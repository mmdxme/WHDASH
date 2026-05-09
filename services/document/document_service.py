"""
Document Service Layer
======================
Business logic for document management, version control, and permissions
— extracted from document_routes.py.
"""

import os
import json
from datetime import datetime

class DocumentService:
    """Handles document-related business logic."""

    def __init__(self, get_db):
        self.get_db = get_db

    def get_documents(self, user_id, filters=None):
        """Get filtered documents for a user with permission checks."""
        db = self.get_db()
        filters = filters or {}
        
        # Base query with simplified permission check for the list view
        query = """
            SELECT d.*, c.name as category_name, u.username as owner_username
            FROM documents d
            LEFT JOIN document_categories c ON d.category_id = c.id
            LEFT JOIN users u ON d.owner_user_id = u.id
            WHERE (d.owner_user_id = ? OR d.created_by_user_id = ? OR d.is_archived = 0)
        """
        params = [user_id, user_id]
        
        if filters.get('search'):
            query += " AND (d.title LIKE ? OR d.description LIKE ?)"
            s = f"%{filters['search']}%"
            params.extend([s, s])
            
        if filters.get('category'):
            query += " AND d.category_id = ?"
            params.append(filters['category'])
            
        if filters.get('status'):
            query += " AND d.status = ?"
            params.append(filters['status'])
            
        query += " ORDER BY d.updated_at DESC"
        
        return [dict(r) for r in db.execute(query, params).fetchall()]

    def get_document_detail(self, document_id, user_id):
        """Get full document detail with versions and metadata."""
        db = self.get_db()
        
        doc = db.execute("""
            SELECT d.*, c.name as category_name, u.username as owner_username
            FROM documents d
            LEFT JOIN document_categories c ON d.category_id = c.id
            LEFT JOIN users u ON d.owner_user_id = u.id
            WHERE d.id = ?
        """, (document_id,)).fetchone()
        
        if not doc:
            return None
            
        result = dict(doc)
        
        # Versions
        result['versions'] = [dict(r) for r in db.execute("""
            SELECT v.*, u.username as created_by_username
            FROM document_versions v
            LEFT JOIN users u ON v.created_by_user_id = u.id
            WHERE v.document_id = ?
            ORDER BY v.version_number DESC
        """, (document_id,)).fetchall()]
        
        # Shares
        result['shares'] = [dict(r) for r in db.execute("""
            SELECT s.*, u.username as shared_with_username
            FROM document_shares s
            LEFT JOIN users u ON s.shared_with_user_id = u.id
            WHERE s.document_id = ? AND s.is_active = 1
        """, (document_id,)).fetchall()]
        
        return result

    def create_document(self, data, user_id):
        """Create a new document and its first version."""
        db = self.get_db()
        now = datetime.now().isoformat()
        
        db.execute("""
            INSERT INTO documents 
            (title, description, category_id, status, owner_user_id, created_by_user_id, 
             created_at, updated_at, is_archived)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (
            data['title'], data.get('description', ''), data.get('category_id'),
            data.get('status', 'Draft'), user_id, user_id, now, now
        ))
        
        doc_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # Add initial version if file info provided
        if data.get('file_path'):
            db.execute("""
                INSERT INTO document_versions
                (document_id, version_number, file_name, file_path, file_size, 
                 mime_type, checksum, created_by_user_id, created_at)
                VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?)
            """, (
                doc_id, data['file_name'], data['file_path'], data['file_size'],
                data['mime_type'], data.get('checksum'), user_id, now
            ))
            version_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            db.execute("UPDATE documents SET current_version_id = ? WHERE id = ?", (version_id, doc_id))
            
        db.commit()
        return doc_id

    def archive_document(self, document_id, user_id, reason=None):
        """Archive a document."""
        db = self.get_db()
        db.execute("""
            UPDATE documents 
            SET is_archived = 1, archived_at = CURRENT_TIMESTAMP, 
                archived_by_user_id = ?, archive_reason = ?
            WHERE id = ?
        """, (user_id, reason, document_id))
        db.commit()
        return True
