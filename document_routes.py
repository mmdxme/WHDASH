"""
Document Management Module Routes
=================================
Enterprise-grade Document Management System for the MMDx platform.

This module provides:
- Document Dashboard with statistics and recent activity
- Document CRUD operations with metadata management
- Version control with check-in/check-out
- Document templates with placeholder support
- E-signature workflows with multi-signer support
- Document linking to business records
- Access control and sharing
- Search and filtering
- Reports and audit logs

Usage:
    from document_routes import register_document_routes
    register_document_routes(app)
"""

import os
import sqlite3
import json
import uuid
import hashlib
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, redirect, url_for, flash, session, render_template, send_file, jsonify, Response
from werkzeug.utils import secure_filename
from database import get_db, get_db_context, get_one, get_all, log_audit, create_notification, table_exists, column_exists, add_column_if_not_exists

# =============================================================================
# CONSTANTS
# =============================================================================

DOCUMENT_UPLOAD_FOLDER = os.environ.get(
    'DOCUMENT_UPLOAD_FOLDER',
    os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads', 'documents')
)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'png', 'jpg', 'jpeg', 'gif', 'txt', 'csv', 'zip', 'rar'}
MAX_FILE_SIZE_MB = 50

# Ensure upload directory exists
os.makedirs(DOCUMENT_UPLOAD_FOLDER, exist_ok=True)

# Document types mapping
DOCUMENT_TYPES = {
    'file': 'File Upload',
    'template': 'Generated from Template',
    'linked': 'External Link',
    'scanned': 'Scanned Document',
}

# Document status values
DOCUMENT_STATUSES = ['Draft', 'Under Review', 'Approved', 'Published', 'Obsolete', 'Archived']

# Signature status values
SIGNATURE_STATUSES = ['Pending', 'Signed', 'Rejected', 'Expired', 'Canceled']

# Visibility levels
VISIBILITY_LEVELS = ['Private', 'Department', 'Branch', 'Company', 'Public']

# Access levels
ACCESS_LEVELS = ['Read', 'Write', 'Admin']

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def require_login(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login to access this page.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user_id():
    """Get the current user ID from session."""
    return session.get('user_id')


def get_document_upload_folder():
    """Get the document upload folder path."""
    return DOCUMENT_UPLOAD_FOLDER


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_extension(filename):
    """Get file extension."""
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''


def generate_stored_filename(original_filename):
    """Generate a unique stored filename."""
    ext = get_file_extension(original_filename)
    unique_id = uuid.uuid4().hex[:12]
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    return f"{timestamp}_{unique_id}.{ext}"


def calculate_file_checksum(file_path):
    """Calculate MD5 checksum of a file."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_file_size_bytes(file_path):
    """Get file size in bytes."""
    return os.path.getsize(file_path) if os.path.exists(file_path) else 0


def format_file_size(size_bytes):
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def get_document_setting(key, default=None):
    """Get a document management setting."""
    result = get_one("SELECT setting_value FROM document_settings WHERE setting_key = ? AND is_active = 1", (key,))
    return result['setting_value'] if result else default


def document_has_permission(user_id, document_id, permission='view'):
    """Check if user has permission for a document."""
    doc = get_one("SELECT * FROM documents WHERE id = ?", (document_id,))
    if not doc:
        return False
    
    # Owner always has access
    if doc['owner_user_id'] == user_id or doc['created_by_user_id'] == user_id:
        return True
    
    # Check document shares
    share = get_one("""
        SELECT 1 FROM document_shares 
        WHERE document_id = ? AND shared_with_user_id = ? AND is_active = 1
        AND (expires_at IS NULL OR expires_at > datetime('now'))
    """, (document_id, user_id))
    
    if share:
        return True
    
    # Check if user is a signer on this document
    signer_check = get_one("""
        SELECT 1 FROM signature_participants sp
        JOIN signature_requests sr ON sp.request_id = sr.id
        WHERE sr.document_id = ? AND sp.user_id = ?
    """, (document_id, user_id))
    
    if signer_check:
        return True
    
    # Check if user has document module permissions
    from permissions import user_has_permission
    if user_has_permission(user_id, 'documents', 'files', permission):
        return True
    
    return False


def log_document_access(document_id, user_id, action, access_type='View', notes=None):
    """Log document access."""
    ip_address = request.remote_addr if request else None
    user_agent = request.headers.get('User-Agent') if request else None
    
    with get_db_context() as db:
        db.execute("""
            INSERT INTO document_access_logs 
            (document_id, user_id, access_action, access_type, ip_address, user_agent, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (document_id, user_id, action, access_type, ip_address, user_agent, notes))
        db.commit()


def document_permission_required(action: str = 'view'):
    """Decorator to require document permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please login to access this page.", "error")
                return redirect(url_for('login'))
            
            user_id = session['user_id']
            from permissions import user_has_permission
            if not user_has_permission(user_id, 'documents', 'files', action):
                flash(f"Access Denied. You don't have permission to {action} documents.", "error")
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_document_tables():
    """Initialize document management tables."""
    from document_models import initialize_document_tables as init_doc_tables
    init_doc_tables()

    # Ensure metadata columns exist in documents table
    add_column_if_not_exists('documents', 'signature_status', 'TEXT DEFAULT "Not Applicable"')
    add_column_if_not_exists('documents', 'signed_at', 'DATETIME')
    add_column_if_not_exists('documents', 'signed_by_user_id', 'INTEGER')

    # Ensure signature type column exists
    add_column_if_not_exists('documents', 'signature_type', 'TEXT')

    # Ensure folder_id column exists for documents
    add_column_if_not_exists('documents', 'folder_id', 'INTEGER')

    # Create folder index if needed
    try:
        with get_db_context() as db:
            db.execute("CREATE INDEX IF NOT EXISTS idx_documents_folder ON documents(folder_id)")
            db.commit()
    except:
        pass


# =============================================================================
# ROUTE REGISTRATION
# =============================================================================

def register_document_routes(app):
    """Register all document management routes."""

    # Initialize tables
    initialize_document_tables()

    # Import folder helper functions from document_models
    from document_models import (
        get_folder_by_id, get_folder_tree, get_folder_path, get_folder_children,
        get_folder_documents, get_folder_stats, get_user_root_folders, check_folder_access,
        log_folder_activity, get_user_favorites, get_user_quick_access, update_quick_access,
        add_document_favorite, remove_document_favorite, is_document_favorited,
        get_document_lock, lock_document, unlock_document, get_user_locks, get_overdue_locks,
        search_documents_advanced, get_file_management_stats, generate_folder_code
    )

    # Create blueprint
    documents_bp = app.route
    
    # =========================================================================
    # DOCUMENT DASHBOARD
    # =========================================================================
    
    @app.route('/documents/')
    @app.route('/documents/dashboard')
    @require_login
    @document_permission_required('view')
    def documents_dashboard():
        """Document management dashboard."""
        user_id = get_current_user_id()
        
        stats = get_document_stats_for_user(user_id)
        recent_docs = get_recent_documents(user_id, limit=10)
        pending_sigs = get_pending_signatures_for_user(user_id, limit=5)
        recent_activity = get_recent_document_activity(user_id, limit=10)
        
        return render_template('documents/dashboard.html',
            stats=stats,
            recent_docs=recent_docs,
            pending_sigs=pending_sigs,
            recent_activity=recent_activity,
            page_title='Document Dashboard')
    
    # =========================================================================
    # DOCUMENT LIST VIEWS
    # =========================================================================
    
    @app.route('/documents/all')
    @require_login
    @document_permission_required('view')
    def documents_all():
        """All documents list."""
        user_id = get_current_user_id()
        
        # Get filter parameters
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        status = request.args.get('status', '')
        doc_type = request.args.get('type', '')
        
        page = int(request.args.get('page', 1))
        per_page = 50
        
        documents, total = get_filtered_documents(
            user_id=user_id,
            search=search,
            category=category,
            status=status,
            doc_type=doc_type,
            page=page,
            per_page=per_page
        )
        
        categories = get_all("SELECT * FROM document_categories WHERE is_active = 1 ORDER BY sort_order")
        
        return render_template('documents/all_documents.html',
            documents=documents,
            categories=categories,
            search=search,
            category=category,
            status=status,
            doc_type=doc_type,
            page=page,
            total_pages=(total + per_page - 1) // per_page,
            total=total,
            page_title='All Documents')
    
    @app.route('/documents/my')
    @require_login
    @document_permission_required('view')
    def documents_my():
        """My documents list."""
        user_id = get_current_user_id()
        
        documents = get_my_documents(user_id)
        
        return render_template('documents/my_documents.html',
            documents=documents,
            page_title='My Documents')
    
    @app.route('/documents/shared')
    @require_login
    def documents_shared():
        """Documents shared with me."""
        user_id = get_current_user_id()
        
        documents = get_shared_documents(user_id)
        
        return render_template('documents/shared_documents.html',
            documents=documents,
            page_title='Shared with Me')
    
    @app.route('/documents/recent')
    @require_login
    def documents_recent():
        """Recently accessed documents."""
        user_id = get_current_user_id()
        
        documents = get_recent_documents(user_id, limit=50)
        
        return render_template('documents/recent_documents.html',
            documents=documents,
            page_title='Recent Documents')
    
    @app.route('/documents/archived')
    @require_login
    @document_permission_required('view')
    def documents_archived():
        """Archived documents."""
        user_id = get_current_user_id()
        
        documents = get_archived_documents(user_id)
        
        return render_template('documents/archived_documents.html',
            documents=documents,
            page_title='Archived Documents')
    
    @app.route('/documents/pending-signature')
    @require_login
    def documents_pending_signature():
        """Documents pending signature."""
        user_id = get_current_user_id()
        
        requests = get_pending_signature_requests_list(user_id)
        
        return render_template('documents/pending_signature.html',
            signature_requests=requests,
            page_title='Pending Signature')
    
    @app.route('/documents/signed')
    @require_login
    def documents_signed():
        """Signed/completed documents."""
        user_id = get_current_user_id()
        
        documents = get_signed_documents(user_id)
        
        return render_template('documents/signed_documents.html',
            documents=documents,
            page_title='Signed Documents')
    
    # =========================================================================
    # DOCUMENT CRUD
    # =========================================================================
    
    @app.route('/documents/create', methods=['GET', 'POST'])
    @require_login
    @document_permission_required('create')
    def documents_create():
        """Create a new document."""
        user_id = get_current_user_id()
        
        if request.method == 'POST':
            return handle_document_create(user_id)
        
        categories = get_all("SELECT * FROM document_categories WHERE is_active = 1 ORDER BY sort_order")
        tags = get_all("SELECT * FROM document_tags ORDER BY name")
        
        return render_template('documents/document_form.html',
            document=None,
            categories=categories,
            tags=tags,
            is_edit=False,
            page_title='Upload Document')
    
    @app.route('/documents/<int:document_id>/edit', methods=['GET', 'POST'])
    @require_login
    @document_permission_required('edit')
    def documents_edit(document_id):
        """Edit a document."""
        user_id = get_current_user_id()
        
        doc = get_one("SELECT * FROM documents WHERE id = ?", (document_id,))
        if not doc:
            flash("Document not found.", "error")
            return redirect(url_for('documents_all'))
        
        if not document_has_permission(user_id, document_id, 'edit'):
            flash("You don't have permission to edit this document.", "error")
            return redirect(url_for('documents_detail', document_id=document_id))
        
        if request.method == 'POST':
            return handle_document_update(document_id, user_id)
        
        categories = get_all("SELECT * FROM document_categories WHERE is_active = 1 ORDER BY sort_order")
        tags = get_all("SELECT * FROM document_tags ORDER BY name")
        
        versions = get_all("""
            SELECT * FROM document_versions 
            WHERE document_id = ? 
            ORDER BY created_at DESC
        """, (document_id,))
        
        links = get_all("""
            SELECT * FROM document_links 
            WHERE document_id = ?
            ORDER BY is_primary DESC, created_at DESC
        """, (document_id,))
        
        return render_template('documents/document_form.html',
            document=doc,
            categories=categories,
            tags=tags,
            versions=versions,
            links=links,
            is_edit=True,
            page_title='Edit Document')
    
    @app.route('/documents/<int:document_id>')
    @require_login
    @document_permission_required('view')
    def documents_detail(document_id):
        """View document details."""
        user_id = get_current_user_id()
        
        doc = get_one("""
            SELECT d.*, 
                   c.name as category_name,
                   u.username as owner_username,
                   creator.username as created_by_username
            FROM documents d
            LEFT JOIN document_categories c ON d.category_id = c.id
            LEFT JOIN users u ON d.owner_user_id = u.id
            LEFT JOIN users creator ON d.created_by_user_id = creator.id
            WHERE d.id = ?
        """, (document_id,))
        
        if not doc:
            flash("Document not found.", "error")
            return redirect(url_for('documents_all'))
        
        if not document_has_permission(user_id, document_id, 'view'):
            flash("You don't have permission to view this document.", "error")
            return redirect(url_for('documents_all'))
        
        # Parse JSON fields for template use
        if doc.get('tags_json'):
            try:
                doc['tags'] = json.loads(doc['tags_json'])
            except (json.JSONDecodeError, TypeError):
                doc['tags'] = []
        else:
            doc['tags'] = []
        
        # Log access
        log_document_access(document_id, user_id, 'View')
        
        versions = get_all("""
            SELECT v.*, u.username as created_by_username
            FROM document_versions v
            LEFT JOIN users u ON v.created_by_user_id = u.id
            WHERE v.document_id = ?
            ORDER BY v.created_at DESC
        """, (document_id,))
        
        links = get_all("""
            SELECT l.*, u.username as created_by_username
            FROM document_links l
            LEFT JOIN users u ON l.created_by_user_id = u.id
            WHERE l.document_id = ?
            ORDER BY l.is_primary DESC, l.created_at DESC
        """, (document_id,))
        
        signature_requests = get_all("""
            SELECT sr.*, 
                   u.username as requestor_username,
                   (SELECT COUNT(*) FROM signature_participants WHERE request_id = sr.id) as total_participants,
                   (SELECT COUNT(*) FROM signature_participants WHERE request_id = sr.id AND status = 'Signed') as signed_count
            FROM signature_requests sr
            LEFT JOIN users u ON sr.requestor_user_id = u.id
            WHERE sr.document_id = ?
            ORDER BY sr.created_at DESC
        """, (document_id,))
        
        access_logs = get_all("""
            SELECT al.*, u.username
            FROM document_access_logs al
            LEFT JOIN users u ON al.user_id = u.id
            WHERE al.document_id = ?
            ORDER BY al.created_at DESC
            LIMIT 50
        """, (document_id,))
        
        shares = get_all("""
            SELECT s.*, u.username as shared_with_username
            FROM document_shares s
            LEFT JOIN users u ON s.shared_with_user_id = u.id
            WHERE s.document_id = ? AND s.is_active = 1
            ORDER BY s.created_at DESC
        """, (document_id,))
        
        return render_template('documents/document_detail.html',
            document=doc,
            versions=versions,
            links=links,
            signature_requests=signature_requests,
            access_logs=access_logs,
            shares=shares,
            page_title=doc['title'])
    
    @app.route('/documents/<int:document_id>/delete', methods=['POST'])
    @require_login
    @document_permission_required('delete')
    def documents_delete(document_id):
        """Delete a document."""
        user_id = get_current_user_id()
        
        doc = get_one("SELECT * FROM documents WHERE id = ?", (document_id,))
        if not doc:
            return jsonify({'success': False, 'message': 'Document not found'})
        
        if not document_has_permission(user_id, document_id, 'delete'):
            return jsonify({'success': False, 'message': 'Permission denied'})
        
        # Check if document is locked or has active signatures
        if doc.get('signature_status') == 'Pending':
            return jsonify({'success': False, 'message': 'Cannot delete document with pending signatures'})
        
        # Delete document (cascade will handle versions, links, etc.)
        with get_db_context() as db:
            db.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            db.commit()
        
        # Delete physical file
        if doc.get('storage_path') and os.path.exists(doc['storage_path']):
            try:
                os.remove(doc['storage_path'])
            except:
                pass
        
        log_audit('document', document_id, 'DELETE', user_id=user_id)
        
        return jsonify({'success': True, 'message': 'Document deleted successfully'})
    
    @app.route('/documents/<int:document_id>/archive', methods=['POST'])
    @require_login
    def documents_archive(document_id):
        """Archive a document."""
        user_id = get_current_user_id()
        
        doc = get_one("SELECT * FROM documents WHERE id = ?", (document_id,))
        if not doc:
            return jsonify({'success': False, 'message': 'Document not found'})
        
        if not document_has_permission(user_id, document_id, 'edit'):
            return jsonify({'success': False, 'message': 'Permission denied'})
        
        reason = request.form.get('reason', '')
        
        with get_db_context() as db:
            db.execute("""
                UPDATE documents 
                SET is_archived = 1, archived_at = datetime('now'), 
                    archived_by_user_id = ?, archive_reason = ?
                WHERE id = ?
            """, (user_id, reason, document_id))
            db.commit()
        
        log_audit('document', document_id, 'ARCHIVE', user_id=user_id, notes=reason)
        
        return jsonify({'success': True, 'message': 'Document archived successfully'})
    
    @app.route('/documents/<int:document_id>/unarchive', methods=['POST'])
    @require_login
    def documents_unarchive(document_id):
        """Unarchive a document."""
        user_id = get_current_user_id()
        
        doc = get_one("SELECT * FROM documents WHERE id = ?", (document_id,))
        if not doc:
            return jsonify({'success': False, 'message': 'Document not found'})
        
        if not document_has_permission(user_id, document_id, 'edit'):
            return jsonify({'success': False, 'message': 'Permission denied'})
        
        with get_db_context() as db:
            db.execute("""
                UPDATE documents 
                SET is_archived = 0, archived_at = NULL, archived_by_user_id = NULL, archive_reason = NULL
                WHERE id = ?
            """, (document_id,))
            db.commit()
        
        log_audit('document', document_id, 'UNARCHIVE', user_id=user_id)
        
        return jsonify({'success': True, 'message': 'Document unarchived successfully'})
    
    # =========================================================================
    # FILE UPLOAD AND DOWNLOAD
    # =========================================================================
    
    @app.route('/documents/upload', methods=['POST'])
    @require_login
    def documents_upload():
        """Handle document file upload."""
        user_id = get_current_user_id()
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'No file provided'})
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'})
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'})
        
        # Check file size
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        
        max_size = int(get_document_setting('max_file_size_mb', MAX_FILE_SIZE_MB)) * 1024 * 1024
        if size > max_size:
            return jsonify({'success': False, 'message': f'File too large. Maximum size: {max_size // (1024*1024)}MB'})
        
        # Generate stored filename
        original_filename = secure_filename(file.filename)
        stored_filename = generate_stored_filename(original_filename)
        storage_path = os.path.join(DOCUMENT_UPLOAD_FOLDER, stored_filename)
        
        # Save file
        file.save(storage_path)
        
        # Calculate checksum
        checksum = calculate_file_checksum(storage_path)
        file_size = get_file_size_bytes(storage_path)
        
        return jsonify({
            'success': True,
            'stored_filename': stored_filename,
            'storage_path': storage_path,
            'original_filename': original_filename,
            'checksum': checksum,
            'file_size': file_size,
            'mime_type': file.content_type
        })
    
    @app.route('/documents/<int:document_id>/download')
    @require_login
    def documents_download(document_id):
        """Download a document file."""
        user_id = get_current_user_id()
        
        doc = get_one("""
            SELECT d.*, v.file_path, v.file_name, v.mime_type
            FROM documents d
            LEFT JOIN document_versions v ON d.current_version_id = v.id
            WHERE d.id = ?
        """, (document_id,))
        
        if not doc:
            flash("Document not found.", "error")
            return redirect(url_for('documents_all'))
        
        if not document_has_permission(user_id, document_id, 'download'):
            flash("You don't have permission to download this document.", "error")
            return redirect(url_for('documents_detail', document_id=document_id))
        
        # Try version file path first, then document storage path
        file_path = doc.get('file_path') or doc.get('storage_path')
        
        if not file_path or not os.path.exists(file_path):
            flash("File not found on server.", "error")
            return redirect(url_for('documents_detail', document_id=document_id))
        
        # Log download access
        log_document_access(document_id, user_id, 'Download')
        
        download_name = doc.get('file_name') or doc.get('original_filename') or 'document'
        
        return send_file(file_path, 
                        download_name=download_name,
                        as_attachment=True)
    
    @app.route('/documents/version/<int:version_id>/download')
    @require_login
    def documents_version_download(version_id):
        """Download a specific version of a document."""
        user_id = get_current_user_id()
        
        version = get_one("""
            SELECT v.*, d.id as document_id, d.title
            FROM document_versions v
            JOIN documents d ON v.document_id = d.id
            WHERE v.id = ?
        """, (version_id,))
        
        if not version:
            return jsonify({'success': False, 'message': 'Version not found'})
        
        if not document_has_permission(user_id, version['document_id'], 'download'):
            return jsonify({'success': False, 'message': 'Permission denied'})
        
        if not os.path.exists(version['file_path']):
            return jsonify({'success': False, 'message': 'File not found'})
        
        # Log download
        log_document_access(version['document_id'], user_id, 'Download Version', 
                          notes=f"Version {version['version_number']}")
        
        return send_file(version['file_path'], 
                        download_name=version['file_name'],
                        as_attachment=True)
    
    # =========================================================================
    # VERSION CONTROL
    # =========================================================================
    
    @app.route('/documents/<int:document_id>/versions')
    @require_login
    def documents_versions(document_id):
        """View document version history."""
        user_id = get_current_user_id()
        
        doc = get_one("SELECT * FROM documents WHERE id = ?", (document_id,))
        if not doc:
            flash("Document not found.", "error")
            return redirect(url_for('documents_all'))
        
        if not document_has_permission(user_id, document_id, 'view'):
            flash("You don't have permission to view this document.", "error")
            return redirect(url_for('documents_all'))
        
        versions = get_all("""
            SELECT v.*, u.username as created_by_username,
                   cb.username as checked_out_username
            FROM document_versions v
            LEFT JOIN users u ON v.created_by_user_id = u.id
            LEFT JOIN users cb ON v.checked_out_by_user_id = cb.id
            WHERE v.document_id = ?
            ORDER BY v.created_at DESC
        """, (document_id,))
        
        return render_template('documents/version_history.html',
            document=doc,
            versions=versions,
            page_title=f'Versions - {doc["title"]}')
    
    @app.route('/documents/<int:document_id>/new-version', methods=['GET', 'POST'])
    @require_login
    def documents_new_version(document_id):
        """Upload a new version of a document."""
        user_id = get_current_user_id()
        
        doc = get_one("SELECT * FROM documents WHERE id = ?", (document_id,))
        if not doc:
            flash("Document not found.", "error")
            return redirect(url_for('documents_all'))
        
        if not document_has_permission(user_id, document_id, 'edit'):
            flash("You don't have permission to edit this document.", "error")
            return redirect(url_for('documents_detail', document_id=document_id))
        
        if request.method == 'POST':
            return handle_new_version(document_id, user_id)
        
        current_version = get_one("SELECT * FROM document_versions WHERE id = ?", (doc['current_version_id'],))
        next_version = "1.1"
        if current_version:
            try:
                parts = current_version['version_number'].split('.')
                major = int(parts[0])
                minor = int(parts[1]) + 1 if len(parts) > 1 else 1
                next_version = f"{major}.{minor}"
            except:
                next_version = f"{current_version['version_number']}.1"
        
        return render_template('documents/new_version_form.html',
            document=doc,
            current_version=current_version,
            next_version=next_version,
            page_title=f'New Version - {doc["title"]}')
    
    @app.route('/documents/version/<int:version_id>/set-current', methods=['POST'])
    @require_login
    def documents_set_current_version(version_id):
        """Set a version as the current version."""
        user_id = get_current_user_id()
        
        version = get_one("""
            SELECT v.*, d.id as document_id
            FROM document_versions v
            JOIN documents d ON v.document_id = d.id
            WHERE v.id = ?
        """, (version_id,))
        
        if not version:
            return jsonify({'success': False, 'message': 'Version not found'})
        
        if not document_has_permission(user_id, version['document_id'], 'edit'):
            return jsonify({'success': False, 'message': 'Permission denied'})
        
        with get_db_context() as db:
            # Unmark current version
            db.execute("""
                UPDATE document_versions 
                SET is_current_version = 0 
                WHERE document_id = ?
            """, (version['document_id'],))
            
            # Mark new current version
            db.execute("""
                UPDATE document_versions 
                SET is_current_version = 1 
                WHERE id = ?
            """, (version_id,))
            
            # Update document
            db.execute("""
                UPDATE documents 
                SET current_version_id = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (version_id, version['document_id']))
            
            db.commit()
        
        log_audit('document_version', version_id, 'SET_CURRENT', user_id=user_id)
        
        return jsonify({'success': True, 'message': 'Current version updated'})
    
    @app.route('/documents/version/<int:version_id>/delete', methods=['POST'])
    @require_login
    def documents_delete_version(version_id):
        """Delete a document version."""
        user_id = get_current_user_id()
        
        version = get_one("""
            SELECT v.*, d.id as document_id
            FROM document_versions v
            JOIN documents d ON v.document_id = d.id
            WHERE v.id = ?
        """, (version_id,))
        
        if not version:
            return jsonify({'success': False, 'message': 'Version not found'})
        
        if not document_has_permission(user_id, version['document_id'], 'delete'):
            return jsonify({'success': False, 'message': 'Permission denied'})
        
        if version['is_current_version']:
            return jsonify({'success': False, 'message': 'Cannot delete current version'})
        
        # Delete file
        if os.path.exists(version['file_path']):
            try:
                os.remove(version['file_path'])
            except:
                pass
        
        # Delete version record
        with get_db_context() as db:
            db.execute("DELETE FROM document_versions WHERE id = ?", (version_id,))
            db.commit()
        
        log_audit('document_version', version_id, 'DELETE', user_id=user_id)
        
        return jsonify({'success': True, 'message': 'Version deleted'})
    
    # =========================================================================
    # CHECK-IN / CHECK-OUT
    # =========================================================================
    
    @app.route('/documents/<int:document_id>/checkout', methods=['POST'])
    @require_login
    def documents_checkout(document_id):
        """Check out a document for editing."""
        user_id = get_current_user_id()
        
        doc = get_one("SELECT * FROM documents WHERE id = ?", (document_id,))
        if not doc:
            return jsonify({'success': False, 'message': 'Document not found'})
        
        if not document_has_permission(user_id, document_id, 'edit'):
            return jsonify({'success': False, 'message': 'Permission denied'})
        
        # Check if already checked out
        current_version = get_one("""
            SELECT * FROM document_versions 
            WHERE document_id = ? AND is_current_version = 1
        """, (document_id,))
        
        if current_version and current_version['checked_out_by_user_id']:
            if current_version['checked_out_by_user_id'] != user_id:
                return jsonify({
                    'success': False, 
                    'message': f'Document is already checked out by another user'
                })
        
        checkout_until = request.form.get('checkout_until')
        if checkout_until:
            checkout_until = datetime.strptime(checkout_until, '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')
        
        with get_db_context() as db:
            if current_version:
                db.execute("""
                    UPDATE document_versions 
                    SET checked_out_by_user_id = ?, checked_out_at = datetime('now'),
                        checked_out_until = ?
                    WHERE id = ?
                """, (user_id, checkout_until, current_version['id']))
            db.commit()
        
        log_audit('document', document_id, 'CHECKOUT', user_id=user_id)
        
        return jsonify({'success': True, 'message': 'Document checked out successfully'})
    
    @app.route('/documents/<int:document_id>/checkin', methods=['POST'])
    @require_login
    def documents_checkin(document_id):
        """Check in a document after editing."""
        user_id = get_current_user_id()
        
        doc = get_one("SELECT * FROM documents WHERE id = ?", (document_id,))
        if not doc:
            return jsonify({'success': False, 'message': 'Document not found'})
        
        if not document_has_permission(user_id, document_id, 'edit'):
            return jsonify({'success': False, 'message': 'Permission denied'})
        
        current_version = get_one("""
            SELECT * FROM document_versions 
            WHERE document_id = ? AND is_current_version = 1
        """, (document_id,))
        
        if not current_version or current_version['checked_out_by_user_id'] != user_id:
            return jsonify({'success': False, 'message': 'Document is not checked out by you'})
        
        with get_db_context() as db:
            db.execute("""
                UPDATE document_versions 
                SET checked_out_by_user_id = NULL, checked_out_at = NULL, checked_out_until = NULL
                WHERE id = ?
            """, (current_version['id']))
            db.commit()
        
        log_audit('document', document_id, 'CHECKIN', user_id=user_id)
        
        return jsonify({'success': True, 'message': 'Document checked in successfully'})
    
    # =========================================================================
    # DOCUMENT LINKING
    # =========================================================================
    
    @app.route('/documents/<int:document_id>/links')
    @require_login
    def documents_links(document_id):
        """View and manage document links."""
        user_id = get_current_user_id()
        
        doc = get_one("SELECT * FROM documents WHERE id = ?", (document_id,))
        if not doc:
            flash("Document not found.", "error")
            return redirect(url_for('documents_all'))
        
        if not document_has_permission(user_id, document_id, 'view'):
            flash("You don't have permission to view this document.", "error")
            return redirect(url_for('documents_all'))
        
        links = get_all("""
            SELECT l.*, u.username as created_by_username
            FROM document_links l
            LEFT JOIN users u ON l.created_by_user_id = u.id
            WHERE l.document_id = ?
            ORDER BY l.is_primary DESC, l.created_at DESC
        """, (document_id,))
        
        return render_template('documents/document_links.html',
            document=doc,
            links=links,
            page_title=f'Links - {doc["title"]}')
    
    @app.route('/documents/<int:document_id>/link', methods=['POST'])
    @require_login
    def documents_add_link(document_id):
        """Add a link between document and business record."""
        user_id = get_current_user_id()
        
        doc = get_one("SELECT * FROM documents WHERE id = ?", (document_id,))
        if not doc:
            return jsonify({'success': False, 'message': 'Document not found'})
        
        if not document_has_permission(user_id, document_id, 'edit'):
            return jsonify({'success': False, 'message': 'Permission denied'})
        
        linked_module = request.form.get('linked_module')
        linked_record_id = request.form.get('linked_record_id')
        link_type = request.form.get('link_type', 'Related')
        is_primary = 1 if request.form.get('is_primary') else 0
        description = request.form.get('description', '')
        
        if not linked_module or not linked_record_id:
            return jsonify({'success': False, 'message': 'Module and record ID are required'})
        
        try:
            linked_record_id = int(linked_record_id)
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid record ID'})
        
        with get_db_context() as db:
            # If setting as primary, unset other primaries
            if is_primary:
                db.execute("UPDATE document_links SET is_primary = 0 WHERE document_id = ?", (document_id,))
            
            db.execute("""
                INSERT INTO document_links 
                (document_id, linked_module, linked_record_id, link_type, is_primary, description, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (document_id, linked_module, linked_record_id, link_type, is_primary, description, user_id))
            db.commit()
        
        log_audit('document_link', document_id, 'CREATE', user_id=user_id, 
                 notes=f"Linked to {linked_module}:{linked_record_id}")
        
        return jsonify({'success': True, 'message': 'Link added successfully'})
    
    @app.route('/documents/link/<int:link_id>/delete', methods=['POST'])
    @require_login
    def documents_delete_link(link_id):
        """Delete a document link."""
        user_id = get_current_user_id()
        
        link = get_one("SELECT * FROM document_links WHERE id = ?", (link_id,))
        if not link:
            return jsonify({'success': False, 'message': 'Link not found'})
        
        if not document_has_permission(user_id, link['document_id'], 'edit'):
            return jsonify({'success': False, 'message': 'Permission denied'})
        
        with get_db_context() as db:
            db.execute("DELETE FROM document_links WHERE id = ?", (link_id,))
            db.commit()
        
        log_audit('document_link', link_id, 'DELETE', user_id=user_id)
        
        return jsonify({'success': True, 'message': 'Link deleted successfully'})
    
    # =========================================================================
    # DOCUMENT SHARING
    # =========================================================================
    
    @app.route('/documents/<int:document_id>/shares')
    @require_login
    def documents_shares(document_id):
        """View and manage document shares."""
        user_id = get_current_user_id()
        
        doc = get_one("SELECT * FROM documents WHERE id = ?", (document_id,))
        if not doc:
            flash("Document not found.", "error")
            return redirect(url_for('documents_all'))
        
        if not document_has_permission(user_id, document_id, 'view'):
            flash("You don't have permission to view this document.", "error")
            return redirect(url_for('documents_all'))
        
        shares = get_all("""
            SELECT s.*, u.username as shared_with_username
            FROM document_shares s
            LEFT JOIN users u ON s.shared_with_user_id = u.id
            WHERE s.document_id = ?
            ORDER BY s.created_at DESC
        """, (document_id,))
        
        return render_template('documents/document_shares.html',
            document=doc,
            shares=shares,
            page_title=f'Shares - {doc["title"]}')
    
    @app.route('/documents/<int:document_id>/share', methods=['POST'])
    @require_login
    def documents_add_share(document_id):
        """Share a document with users."""
        user_id = get_current_user_id()
        
        doc = get_one("SELECT * FROM documents WHERE id = ?", (document_id,))
        if not doc:
            return jsonify({'success': False, 'message': 'Document not found'})
        
        if not document_has_permission(user_id, document_id, 'share'):
            return jsonify({'success': False, 'message': 'Permission denied'})
        
        share_with_user_id = request.form.get('share_with_user_id')
        permission_level = request.form.get('permission_level', 'View')
        access_level = request.form.get('access_level', 'Read')
        expires_at = request.form.get('expires_at')
        
        if not share_with_user_id:
            return jsonify({'success': False, 'message': 'User is required'})
        
        try:
            share_with_user_id = int(share_with_user_id)
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid user ID'})
        
        with get_db_context() as db:
            db.execute("""
                INSERT INTO document_shares 
                (document_id, shared_with_user_id, permission_level, access_level, 
                 shared_by_user_id, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (document_id, share_with_user_id, permission_level, access_level,
                  user_id, expires_at))
            db.commit()
        
        log_audit('document_share', document_id, 'CREATE', user_id=user_id,
                 notes=f"Shared with user {share_with_user_id}")
        
        return jsonify({'success': True, 'message': 'Document shared successfully'})
    
    @app.route('/documents/share/<int:share_id>/revoke', methods=['POST'])
    @require_login
    def documents_revoke_share(share_id):
        """Revoke a document share."""
        user_id = get_current_user_id()
        
        share = get_one("SELECT * FROM document_shares WHERE id = ?", (share_id,))
        if not share:
            return jsonify({'success': False, 'message': 'Share not found'})
        
        if not document_has_permission(user_id, share['document_id'], 'share'):
            return jsonify({'success': False, 'message': 'Permission denied'})
        
        with get_db_context() as db:
            db.execute("""
                UPDATE document_shares 
                SET is_active = 0, revoked_at = datetime('now'), revoked_by_user_id = ?
                WHERE id = ?
            """, (user_id, share_id))
            db.commit()
        
        log_audit('document_share', share_id, 'REVOKE', user_id=user_id)
        
        return jsonify({'success': True, 'message': 'Share revoked successfully'})
    
    # =========================================================================
    # DOCUMENT TEMPLATES
    # =========================================================================
    
    @app.route('/documents/templates/')
    @require_login
    def documents_templates():
        """List all document templates."""
        user_id = get_current_user_id()
        
        templates = get_all("""
            SELECT t.*, u.username as owner_username,
                   c.name as category_name,
                   (SELECT COUNT(*) FROM template_placeholders WHERE template_id = t.id) as placeholder_count
            FROM document_templates t
            LEFT JOIN users u ON t.owner_user_id = u.id
            LEFT JOIN document_categories c ON t.category_id = c.id
            WHERE t.is_active = 1
            ORDER BY t.template_name
        """)
        
        categories = get_all("SELECT * FROM document_categories WHERE is_active = 1 ORDER BY sort_order")
        
        return render_template('documents/templates.html',
            templates=templates,
            categories=categories,
            page_title='Document Templates')
    
    @app.route('/documents/templates/create', methods=['GET', 'POST'])
    @require_login
    def documents_create_template():
        """Create a new document template."""
        user_id = get_current_user_id()
        
        if request.method == 'POST':
            return handle_template_create(user_id)
        
        categories = get_all("SELECT * FROM document_categories WHERE is_active = 1 ORDER BY sort_order")
        
        return render_template('documents/template_form.html',
            template=None,
            categories=categories,
            is_edit=False,
            page_title='Create Template')
    
    @app.route('/documents/templates/<int:template_id>/edit', methods=['GET', 'POST'])
    @require_login
    def documents_edit_template(template_id):
        """Edit a document template."""
        user_id = get_current_user_id()
        
        template = get_one("SELECT * FROM document_templates WHERE id = ?", (template_id,))
        if not template:
            flash("Template not found.", "error")
            return redirect(url_for('documents_templates'))
        
        if request.method == 'POST':
            return handle_template_update(template_id, user_id)
        
        categories = get_all("SELECT * FROM document_categories WHERE is_active = 1 ORDER BY sort_order")
        
        placeholders = get_all("""
            SELECT * FROM template_placeholders 
            WHERE template_id = ?
            ORDER BY sort_order
        """, (template_id,))
        
        return render_template('documents/template_form.html',
            template=template,
            categories=categories,
            placeholders=placeholders,
            is_edit=True,
            page_title=f'Edit Template - {template["template_name"]}')
    
    @app.route('/documents/templates/<int:template_id>/delete', methods=['POST'])
    @require_login
    def documents_delete_template(template_id):
        """Delete a document template."""
        user_id = get_current_user_id()
        
        template = get_one("SELECT * FROM document_templates WHERE id = ?", (template_id,))
        if not template:
            return jsonify({'success': False, 'message': 'Template not found'})
        
        # Soft delete
        with get_db_context() as db:
            db.execute("UPDATE document_templates SET is_active = 0 WHERE id = ?", (template_id,))
            db.commit()
        
        log_audit('document_template', template_id, 'DELETE', user_id=user_id)
        
        return jsonify({'success': True, 'message': 'Template deleted successfully'})
    
    @app.route('/documents/templates/<int:template_id>/preview')
    @require_login
    def documents_template_preview(template_id):
        """Preview a template with sample data."""
        user_id = get_current_user_id()
        
        template = get_one("SELECT * FROM document_templates WHERE id = ?", (template_id,))
        if not template:
            return jsonify({'success': False, 'message': 'Template not found'})
        
        placeholders = get_all("""
            SELECT * FROM template_placeholders 
            WHERE template_id = ?
            ORDER BY sort_order
        """, (template_id,))
        
        return render_template('documents/template_preview.html',
            template=template,
            placeholders=placeholders,
            page_title=f'Preview - {template["template_name"]}')
    
    @app.route('/documents/templates/<int:template_id>/generate', methods=['GET', 'POST'])
    @require_login
    def documents_generate_from_template(template_id):
        """Generate a document from a template."""
        user_id = get_current_user_id()
        
        template = get_one("SELECT * FROM document_templates WHERE id = ?", (template_id,))
        if not template:
            flash("Template not found.", "error")
            return redirect(url_for('documents_templates'))
        
        if request.method == 'POST':
            return handle_document_generate(template_id, user_id)
        
        placeholders = get_all("""
            SELECT * FROM template_placeholders 
            WHERE template_id = ?
            ORDER BY sort_order
        """, (template_id,))
        
        categories = get_all("SELECT * FROM document_categories WHERE is_active = 1 ORDER BY sort_order")
        
        return render_template('documents/generate_document.html',
            template=template,
            placeholders=placeholders,
            categories=categories,
            page_title=f'Generate Document - {template["template_name"]}')
    
    # =========================================================================
    # E-SIGNATURE WORKFLOWS
    # =========================================================================
    
    @app.route('/documents/signatures/')
    @require_login
    def documents_signatures():
        """List all signature requests."""
        user_id = get_current_user_id()
        
        # Get requests where user is requestor or participant
        requests = get_all("""
            SELECT sr.*, 
                   d.title as document_title,
                   d.document_code,
                   u.username as requestor_username,
                   (SELECT COUNT(*) FROM signature_participants WHERE request_id = sr.id) as total_participants,
                   (SELECT COUNT(*) FROM signature_participants WHERE request_id = sr.id AND status = 'Signed') as signed_count
            FROM signature_requests sr
            JOIN documents d ON sr.document_id = d.id
            LEFT JOIN users u ON sr.requestor_user_id = u.id
            WHERE sr.requestor_user_id = ? OR sr.id IN (
                SELECT request_id FROM signature_participants WHERE user_id = ?
            )
            ORDER BY sr.created_at DESC
        """, (user_id, user_id))
        
        return render_template('documents/signatures.html',
            signature_requests=requests,
            page_title='Signature Requests')
    
    @app.route('/documents/signatures/create/<int:document_id>', methods=['GET', 'POST'])
    @require_login
    def documents_create_signature_request(document_id):
        """Create a signature request for a document."""
        user_id = get_current_user_id()
        
        doc = get_one("SELECT * FROM documents WHERE id = ?", (document_id,))
        if not doc:
            flash("Document not found.", "error")
            return redirect(url_for('documents_all'))
        
        if not document_has_permission(user_id, document_id, 'sign'):
            flash("You don't have permission to request signatures.", "error")
            return redirect(url_for('documents_detail', document_id=document_id))
        
        if request.method == 'POST':
            return handle_signature_request_create(document_id, user_id)
        
        users = get_all("SELECT id, username, email FROM users WHERE is_active = 1 ORDER BY username")
        
        return render_template('documents/signature_request_form.html',
            document=doc,
            users=users,
            page_title='Request Signatures')
    
    @app.route('/documents/signatures/<int:request_id>')
    @require_login
    def documents_signature_detail(request_id):
        """View signature request details."""
        user_id = get_current_user_id()
        
        sig_request = get_one("""
            SELECT sr.*, 
                   d.title as document_title,
                   d.document_code,
                   u.username as requestor_username,
                   du.username as canceled_by_username
            FROM signature_requests sr
            JOIN documents d ON sr.document_id = d.id
            LEFT JOIN users u ON sr.requestor_user_id = u.id
            LEFT JOIN users du ON sr.canceled_by_user_id = du.id
            WHERE sr.id = ?
        """, (request_id,))
        
        if not sig_request:
            flash("Signature request not found.", "error")
            return redirect(url_for('documents_signatures'))
        
        participants = get_all("""
            SELECT p.*, u.username as participant_username
            FROM signature_participants p
            LEFT JOIN users u ON p.user_id = u.id
            WHERE p.request_id = ?
            ORDER BY p.signing_order
        """, (request_id,))
        
        return render_template('documents/signature_detail.html',
            signature_request=sig_request,
            participants=participants,
            page_title=f'Signature Request - {sig_request["request_title"]}')
    
    @app.route('/documents/signatures/<int:request_id>/sign', methods=['POST'])
    @require_login
    def documents_sign(request_id):
        """Sign a document."""
        user_id = get_current_user_id()
        
        sig_request = get_one("SELECT * FROM signature_requests WHERE id = ?", (request_id,))
        if not sig_request:
            return jsonify({'success': False, 'message': 'Signature request not found'})
        
        if sig_request['status'] != 'Pending':
            return jsonify({'success': False, 'message': 'Request is not pending'})
        
        # Check if user is a participant
        participant = get_one("""
            SELECT * FROM signature_participants 
            WHERE request_id = ? AND user_id = ? AND status = 'Pending'
        """, (request_id, user_id))
        
        if not participant:
            return jsonify({'success': False, 'message': 'You are not a participant or already signed'})
        
        action = request.form.get('action', 'sign')
        rejection_reason = request.form.get('rejection_reason', '')
        
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get('User-Agent') if request else None
        
        with get_db_context() as db:
            if action == 'sign':
                status = 'Signed'
                signed_file_path = sig_request.get('document_id')  # Reference to document
                
                db.execute("""
                    UPDATE signature_participants 
                    SET status = ?, signed_at = datetime('now'), 
                        signed_ip_address = ?, signed_user_agent = ?,
                        signature_data = ?
                    WHERE id = ?
                """, (status, ip_address, user_agent, f"SIG-{participant['id']}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                      participant['id']))
            else:
                status = 'Rejected'
                db.execute("""
                    UPDATE signature_participants 
                    SET status = ?, rejection_reason = ?
                    WHERE id = ?
                """, (status, rejection_reason, participant['id']))
            
            # Check if all participants have signed
            pending = db.execute("""
                SELECT COUNT(*) as cnt FROM signature_participants 
                WHERE request_id = ? AND status = 'Pending'
            """, (request_id,)).fetchone()['cnt']
            
            if pending == 0:
                # All signed - complete the request
                db.execute("""
                    UPDATE signature_requests 
                    SET status = 'Completed', completed_at = datetime('now')
                    WHERE id = ?
                """, (request_id,))
                
                # Update document signature status
                db.execute("""
                    UPDATE documents 
                    SET signature_status = 'Signed', signed_at = datetime('now'), signed_by_user_id = ?
                    WHERE id = ?
                """, (user_id, sig_request['document_id']))
            elif action == 'reject':
                # Someone rejected - cancel the request
                db.execute("""
                    UPDATE signature_requests 
                    SET status = 'Rejected', canceled_at = datetime('now'), canceled_by_user_id = ?
                    WHERE id = ?
                """, (user_id, request_id))
                
                # Update document
                db.execute("""
                    UPDATE documents 
                    SET signature_status = 'Rejected'
                    WHERE id = ?
                """, (sig_request['document_id'],))
            
            db.commit()
        
        log_audit('signature', request_id, status.upper(), user_id=user_id)
        
        return jsonify({
            'success': True, 
            'message': f'Document {"signed" if action == "sign" else "rejected"} successfully'
        })
    
    @app.route('/documents/signatures/<int:request_id>/cancel', methods=['POST'])
    @require_login
    def documents_cancel_signature_request(request_id):
        """Cancel a signature request."""
        user_id = get_current_user_id()
        
        sig_request = get_one("SELECT * FROM signature_requests WHERE id = ?", (request_id,))
        if not sig_request:
            return jsonify({'success': False, 'message': 'Signature request not found'})
        
        if sig_request['requestor_user_id'] != user_id:
            return jsonify({'success': False, 'message': 'Only requestor can cancel'})
        
        if sig_request['status'] != 'Pending':
            return jsonify({'success': False, 'message': 'Request is not pending'})
        
        reason = request.form.get('reason', '')
        
        with get_db_context() as db:
            db.execute("""
                UPDATE signature_requests 
                SET status = 'Canceled', canceled_at = datetime('now'), 
                    canceled_by_user_id = ?, cancellation_reason = ?
                WHERE id = ?
            """, (user_id, reason, request_id))
            
            # Update document signature status
            db.execute("""
                UPDATE documents 
                SET signature_status = 'Canceled'
                WHERE id = ?
            """, (sig_request['document_id'],))
            
            db.commit()
        
        log_audit('signature', request_id, 'CANCEL', user_id=user_id)
        
        return jsonify({'success': True, 'message': 'Signature request canceled'})
    
    @app.route('/documents/signatures/pending')
    @require_login
    def documents_pending_signatures():
        """List pending signatures for current user."""
        user_id = get_current_user_id()
        
        requests = get_all("""
            SELECT sr.*, 
                   d.title as document_title,
                   d.document_code,
                   u.username as requestor_username,
                   p.status as my_status
            FROM signature_requests sr
            JOIN signature_participants p ON sr.id = p.request_id
            JOIN documents d ON sr.document_id = d.id
            LEFT JOIN users u ON sr.requestor_user_id = u.id
            WHERE p.user_id = ? AND p.status = 'Pending' AND sr.status = 'Pending'
            ORDER BY sr.due_date ASC, sr.created_at DESC
        """, (user_id,))
        
        return render_template('documents/pending_signatures.html',
            signature_requests=requests,
            page_title='Pending Signatures')
    
    # =========================================================================
    # SEARCH AND FILTERING
    # =========================================================================
    
    @app.route('/documents/search')
    @require_login
    @document_permission_required('view')
    def documents_search():
        """Advanced document search."""
        user_id = get_current_user_id()
        
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        doc_type = request.args.get('type', '')
        status = request.args.get('status', '')
        visibility = request.args.get('visibility', '')
        source_module = request.args.get('source_module', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        page = int(request.args.get('page', 1))
        per_page = 50
        
        documents, total = search_documents(
            user_id=user_id,
            search=search,
            category=category,
            doc_type=doc_type,
            status=status,
            visibility=visibility,
            source_module=source_module,
            date_from=date_from,
            date_to=date_to,
            page=page,
            per_page=per_page
        )
        
        categories = get_all("SELECT * FROM document_categories WHERE is_active = 1 ORDER BY sort_order")
        
        return render_template('documents/search.html',
            documents=documents,
            categories=categories,
            search=search,
            category=category,
            doc_type=doc_type,
            status=status,
            visibility=visibility,
            source_module=source_module,
            date_from=date_from,
            date_to=date_to,
            page=page,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 0,
            total=total,
            page_title='Search Documents')
    
    @app.route('/documents/api/search')
    @require_login
    def documents_api_search():
        """API endpoint for document search (JSON)."""
        user_id = get_current_user_id()
        
        search = request.args.get('search', '')
        category = request.args.get('category', '')
        limit = min(int(request.args.get('limit', 20)), 100)
        
        documents = search_documents_simple(user_id, search, category, limit)
        
        return jsonify({'success': True, 'documents': documents})
    
    # =========================================================================
    # REPORTS
    # =========================================================================
    
    @app.route('/documents/reports/')
    @require_login
    def documents_reports():
        """Document management reports."""
        user_id = get_current_user_id()
        
        return render_template('documents/reports.html',
            page_title='Document Reports')
    
    @app.route('/documents/reports/activity')
    @require_login
    def documents_report_activity():
        """Document activity report."""
        user_id = get_current_user_id()
        
        date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
        
        activities = get_all("""
            SELECT al.*, d.title as document_title, d.document_code,
                   u.username
            FROM document_access_logs al
            JOIN documents d ON al.document_id = d.id
            LEFT JOIN users u ON al.user_id = u.id
            WHERE date(al.created_at) BETWEEN ? AND ?
            ORDER BY al.created_at DESC
            LIMIT 500
        """, (date_from, date_to))
        
        return render_template('documents/report_activity.html',
            activities=activities,
            date_from=date_from,
            date_to=date_to,
            page_title='Document Activity Report')
    
    @app.route('/documents/reports/version-history')
    @require_login
    def documents_report_version_history():
        """Version history report."""
        user_id = get_current_user_id()
        
        documents_list = get_all("""
            SELECT d.*, 
                   (SELECT COUNT(*) FROM document_versions WHERE document_id = d.id) as version_count
            FROM documents d
            ORDER BY version_count DESC
            LIMIT 100
        """)
        
        return render_template('documents/report_version_history.html',
            documents=documents_list,
            page_title='Version History Report')
    
    @app.route('/documents/reports/signature-status')
    @require_login
    def documents_report_signature_status():
        """Signature status report."""
        user_id = get_current_user_id()
        
        requests = get_all("""
            SELECT sr.*, d.title as document_title, d.document_code,
                   u.username as requestor_username,
                   (SELECT COUNT(*) FROM signature_participants WHERE request_id = sr.id) as total,
                   (SELECT COUNT(*) FROM signature_participants WHERE request_id = sr.id AND status = 'Signed') as signed,
                   (SELECT COUNT(*) FROM signature_participants WHERE request_id = sr.id AND status = 'Rejected') as rejected,
                   (SELECT COUNT(*) FROM signature_participants WHERE request_id = sr.id AND status = 'Pending') as pending
            FROM signature_requests sr
            JOIN documents d ON sr.document_id = d.id
            LEFT JOIN users u ON sr.requestor_user_id = u.id
            ORDER BY sr.created_at DESC
        """)
        
        return render_template('documents/report_signature_status.html',
            signature_requests=requests,
            page_title='Signature Status Report')
    
    @app.route('/documents/reports/access-log')
    @require_login
    def documents_report_access_log():
        """Access log report."""
        user_id = get_current_user_id()
        
        date_from = request.args.get('date_from', (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
        document_id = request.args.get('document_id')
        
        if document_id:
            logs = get_all("""
                SELECT al.*, d.title as document_title, d.document_code, u.username
                FROM document_access_logs al
                JOIN documents d ON al.document_id = d.id
                LEFT JOIN users u ON al.user_id = u.id
                WHERE al.document_id = ? AND date(al.created_at) BETWEEN ? AND ?
                ORDER BY al.created_at DESC
            """, (document_id, date_from, date_to))
        else:
            logs = get_all("""
                SELECT al.*, d.title as document_title, d.document_code, u.username
                FROM document_access_logs al
                JOIN documents d ON al.document_id = d.id
                LEFT JOIN users u ON al.user_id = u.id
                WHERE date(al.created_at) BETWEEN ? AND ?
                ORDER BY al.created_at DESC
                LIMIT 500
            """, (date_from, date_to))
        
        return render_template('documents/report_access_log.html',
            logs=logs,
            date_from=date_from,
            date_to=date_to,
            document_id=document_id,
            page_title='Access Log Report')
    
    @app.route('/documents/reports/expiring')
    @require_login
    def documents_report_expiring():
        """Expiring/pending documents report."""
        user_id = get_current_user_id()
        
        days = int(request.args.get('days', 30))
        cutoff_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        
        documents_list = get_all("""
            SELECT d.*, c.name as category_name, u.username as owner_username
            FROM documents d
            LEFT JOIN document_categories c ON d.category_id = c.id
            LEFT JOIN users u ON d.owner_user_id = u.id
            WHERE d.is_archived = 0 
            AND d.expiry_date IS NOT NULL 
            AND d.expiry_date <= ?
            ORDER BY d.expiry_date ASC
        """, (cutoff_date,))
        
        return render_template('documents/report_expiring.html',
            documents=documents_list,
            days=days,
            cutoff_date=cutoff_date,
            page_title='Expiring Documents Report')
    
    # =========================================================================
    # CATEGORIES AND TAGS MANAGEMENT
    # =========================================================================
    
    @app.route('/documents/categories/')
    @require_login
    @document_permission_required('view')
    def documents_categories():
        """Manage document categories."""
        user_id = get_current_user_id()
        
        categories = get_all("""
            SELECT c.*, 
                   (SELECT COUNT(*) FROM documents WHERE category_id = c.id) as document_count,
                   pc.name as parent_name
            FROM document_categories c
            LEFT JOIN document_categories pc ON c.parent_id = pc.id
            ORDER BY c.sort_order
        """)
        
        return render_template('documents/categories.html',
            categories=categories,
            page_title='Document Categories')
    
    @app.route('/documents/categories/create', methods=['POST'])
    @require_login
    def documents_create_category():
        """Create a new category."""
        user_id = get_current_user_id()
        
        name = request.form.get('name')
        code = request.form.get('code')
        description = request.form.get('description', '')
        parent_id = request.form.get('parent_id')
        icon = request.form.get('icon', 'fa-file-alt')
        color = request.form.get('color', '#6c757d')
        retention_period = request.form.get('retention_period_days')
        
        if not name or not code:
            return jsonify({'success': False, 'message': 'Name and code are required'})
        
        if parent_id:
            try:
                parent_id = int(parent_id)
            except ValueError:
                parent_id = None
        
        if retention_period:
            try:
                retention_period = int(retention_period)
            except ValueError:
                retention_period = None
        
        with get_db_context() as db:
            db.execute("""
                INSERT INTO document_categories 
                (name, code, description, parent_id, icon, color, retention_period_days, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, code, description, parent_id, icon, color, retention_period, user_id))
            db.commit()
        
        log_audit('document_category', 'new', 'CREATE', user_id=user_id, notes=f"Created category: {name}")
        
        return jsonify({'success': True, 'message': 'Category created successfully'})
    
    @app.route('/documents/categories/<int:category_id>/edit', methods=['POST'])
    @require_login
    def documents_edit_category(category_id):
        """Update a category."""
        user_id = get_current_user_id()
        
        name = request.form.get('name')
        description = request.form.get('description', '')
        icon = request.form.get('icon', 'fa-file-alt')
        color = request.form.get('color', '#6c757d')
        retention_period = request.form.get('retention_period_days')
        
        if retention_period:
            try:
                retention_period = int(retention_period)
            except ValueError:
                retention_period = None
        
        with get_db_context() as db:
            db.execute("""
                UPDATE document_categories 
                SET name = ?, description = ?, icon = ?, color = ?, retention_period_days = ?,
                    updated_at = datetime('now')
                WHERE id = ?
            """, (name, description, icon, color, retention_period, category_id))
            db.commit()
        
        log_audit('document_category', category_id, 'UPDATE', user_id=user_id)
        
        return jsonify({'success': True, 'message': 'Category updated successfully'})
    
    @app.route('/documents/categories/<int:category_id>/delete', methods=['POST'])
    @require_login
    def documents_delete_category(category_id):
        """Delete a category."""
        user_id = get_current_user_id()
        
        # Check if category has documents
        doc_count = get_one("SELECT COUNT(*) as cnt FROM documents WHERE category_id = ?", (category_id,))
        if doc_count and doc_count['cnt'] > 0:
            return jsonify({'success': False, 'message': f'Category has {doc_count["cnt"]} documents. Move or delete them first.'})
        
        with get_db_context() as db:
            db.execute("DELETE FROM document_categories WHERE id = ?", (category_id,))
            db.commit()
        
        log_audit('document_category', category_id, 'DELETE', user_id=user_id)
        
        return jsonify({'success': True, 'message': 'Category deleted successfully'})
    
    @app.route('/documents/tags/')
    @require_login
    @document_permission_required('view')
    def documents_tags():
        """Manage document tags."""
        user_id = get_current_user_id()
        
        tags = get_all("""
            SELECT t.*,
                   (SELECT COUNT(*) FROM documents WHERE tags_json LIKE '%"' || t.name || '"%') as document_count
            FROM document_tags t
            ORDER BY t.name
        """)
        
        return render_template('documents/tags.html',
            tags=tags,
            page_title='Document Tags')
    
    @app.route('/documents/tags/create', methods=['POST'])
    @require_login
    def documents_create_tag():
        """Create a new tag."""
        user_id = get_current_user_id()
        
        name = request.form.get('name')
        description = request.form.get('description', '')
        color = request.form.get('color', '#6c757d')
        
        if not name:
            return jsonify({'success': False, 'message': 'Name is required'})
        
        with get_db_context() as db:
            db.execute("""
                INSERT INTO document_tags (name, description, color, created_by_user_id)
                VALUES (?, ?, ?, ?)
            """, (name, description, color, user_id))
            db.commit()
        
        return jsonify({'success': True, 'message': 'Tag created successfully'})
    
    @app.route('/documents/tags/<int:tag_id>/delete', methods=['POST'])
    @require_login
    def documents_delete_tag(tag_id):
        """Delete a tag."""
        user_id = get_current_user_id()
        
        with get_db_context() as db:
            db.execute("DELETE FROM document_tags WHERE id = ?", (tag_id,))
            db.commit()
        
        return jsonify({'success': True, 'message': 'Tag deleted successfully'})
    
    # =========================================================================
    # SETTINGS
    # =========================================================================
    
    @app.route('/documents/settings/')
    @require_login
    def documents_settings():
        """Document management settings."""
        user_id = get_current_user_id()
        
        settings = get_all("SELECT * FROM document_settings ORDER BY category, setting_key")
        
        settings_by_category = {}
        for s in settings:
            cat = s['category']
            if cat not in settings_by_category:
                settings_by_category[cat] = []
            settings_by_category[cat].append(s)
        
        return render_template('documents/settings.html',
            settings_by_category=settings_by_category,
            page_title='Document Settings')
    
    @app.route('/documents/settings/save', methods=['POST'])
    @require_login
    def documents_save_settings():
        """Save document settings."""
        user_id = get_current_user_id()
        
        for key, value in request.form.items():
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                
                with get_db_context() as db:
                    db.execute("""
                        UPDATE document_settings 
                        SET setting_value = ?, updated_at = datetime('now')
                        WHERE setting_key = ?
                    """, (value, setting_key))
                    db.commit()
        
        flash("Settings saved successfully.", "success")
        return redirect(url_for('documents_settings'))
    
    # =========================================================================
    # AUDIT LOGS
    # =========================================================================
    
    @app.route('/documents/audit-logs/')
    @require_login
    @document_permission_required('view')
    def documents_audit_logs():
        """View document audit logs."""
        user_id = get_current_user_id()
        
        date_from = request.args.get('date_from', (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
        
        logs = get_all("""
            SELECT * FROM document_access_logs
            WHERE date(created_at) BETWEEN ? AND ?
            ORDER BY created_at DESC
            LIMIT 500
        """, (date_from, date_to))
        
        return render_template('documents/audit_logs.html',
            logs=logs,
            date_from=date_from,
            date_to=date_to,
            page_title='Document Audit Logs')
    
    # =========================================================================
    # LINKED RECORDS VIEW
    # =========================================================================
    
    @app.route('/documents/linked-records/')
    @require_login
    def documents_linked_records():
        """View documents linked to business records."""
        user_id = get_current_user_id()
        
        # Get unique linked modules
        modules = get_all("""
            SELECT DISTINCT linked_module FROM document_links ORDER BY linked_module
        """)
        
        return render_template('documents/linked_records.html',
            modules=[m['linked_module'] for m in modules],
            page_title='Linked Records')
    
    @app.route('/documents/linked-records/<module_name>/<int:record_id>')
    @require_login
    def documents_view_linked_record(module_name, record_id):
        """View documents linked to a specific business record."""
        user_id = get_current_user_id()
        
        documents_list = get_all("""
            SELECT d.*, l.link_type, l.is_primary, l.created_at as linked_at,
                   c.name as category_name
            FROM document_links l
            JOIN documents d ON l.document_id = d.id
            LEFT JOIN document_categories c ON d.category_id = c.id
            WHERE l.linked_module = ? AND l.linked_record_id = ?
            ORDER BY l.is_primary DESC, d.created_at DESC
        """, (module_name, record_id))
        
        return render_template('documents/linked_record_detail.html',
            documents=documents_list,
            module_name=module_name,
            record_id=record_id,
            page_title=f'Documents - {module_name} #{record_id}')


# =============================================================================
# HELPER FUNCTIONS - DATA ACCESS
# =============================================================================

def get_document_stats_for_user(user_id):
    """Get document statistics for a user."""
    stats = {
        'total_documents': 0,
        'my_documents': 0,
        'shared_with_me': 0,
        'pending_signatures': 0,
        'draft_documents': 0,
        'published_documents': 0,
        'archived_documents': 0,
        'recent_activity_count': 0,
    }
    
    # Total documents accessible by user
    result = get_one("""
        SELECT COUNT(*) as cnt FROM documents 
        WHERE is_archived = 0
        AND (owner_user_id = ? OR created_by_user_id = ?
             OR id IN (SELECT document_id FROM document_shares WHERE shared_with_user_id = ? AND is_active = 1))
    """, (user_id, user_id, user_id))
    stats['total_documents'] = result['cnt'] if result else 0
    
    # My documents
    result = get_one("""
        SELECT COUNT(*) as cnt FROM documents 
        WHERE created_by_user_id = ? OR owner_user_id = ?
    """, (user_id, user_id))
    stats['my_documents'] = result['cnt'] if result else 0
    
    # Shared with me
    result = get_one("""
        SELECT COUNT(*) as cnt FROM document_shares 
        WHERE shared_with_user_id = ? AND is_active = 1
    """, (user_id,))
    stats['shared_with_me'] = result['cnt'] if result else 0
    
    # Pending signatures
    result = get_one("""
        SELECT COUNT(*) as cnt FROM signature_participants 
        WHERE user_id = ? AND status = 'Pending'
        AND request_id IN (SELECT id FROM signature_requests WHERE status = 'Pending')
    """, (user_id,))
    stats['pending_signatures'] = result['cnt'] if result else 0
    
    # Draft documents
    result = get_one("""
        SELECT COUNT(*) as cnt FROM documents 
        WHERE status = 'Draft' AND (created_by_user_id = ? OR owner_user_id = ?)
    """, (user_id, user_id))
    stats['draft_documents'] = result['cnt'] if result else 0
    
    # Published documents
    result = get_one("""
        SELECT COUNT(*) as cnt FROM documents 
        WHERE status = 'Published' AND is_archived = 0
    """)
    stats['published_documents'] = result['cnt'] if result else 0
    
    # Archived
    result = get_one("""
        SELECT COUNT(*) as cnt FROM documents 
        WHERE is_archived = 1 AND (created_by_user_id = ? OR owner_user_id = ?)
    """, (user_id, user_id))
    stats['archived_documents'] = result['cnt'] if result else 0
    
    # Recent activity
    result = get_one("""
        SELECT COUNT(*) as cnt FROM document_access_logs 
        WHERE user_id = ? AND created_at > datetime('now', '-7 days')
    """, (user_id,))
    stats['recent_activity_count'] = result['cnt'] if result else 0
    
    return stats


def get_recent_documents(user_id, limit=10):
    """Get recently accessed documents for a user."""
    # Get from access logs
    docs = get_all("""
        SELECT DISTINCT d.*, al.created_at as accessed_at,
               c.name as category_name
        FROM document_access_logs al
        JOIN documents d ON al.document_id = d.id
        LEFT JOIN document_categories c ON d.category_id = c.id
        WHERE al.user_id = ?
        ORDER BY al.created_at DESC
        LIMIT ?
    """, (user_id, limit))
    
    return docs


def get_pending_signatures_for_user(user_id, limit=5):
    """Get pending signatures for a user."""
    return get_all("""
        SELECT sr.*, d.title as document_title, d.document_code,
               p.status as participant_status
        FROM signature_requests sr
        JOIN signature_participants p ON sr.id = p.request_id
        JOIN documents d ON sr.document_id = d.id
        WHERE p.user_id = ? AND p.status = 'Pending' AND sr.status = 'Pending'
        ORDER BY sr.due_date ASC, sr.created_at DESC
        LIMIT ?
    """, (user_id, limit))


def get_recent_document_activity(user_id, limit=10):
    """Get recent document activity for a user."""
    return get_all("""
        SELECT al.*, d.title as document_title, d.document_code,
               u.username
        FROM document_access_logs al
        JOIN documents d ON al.document_id = d.id
        LEFT JOIN users u ON al.user_id = u.id
        ORDER BY al.created_at DESC
        LIMIT ?
    """, (limit,))


def get_filtered_documents(user_id, search='', category='', status='', doc_type='', page=1, per_page=50):
    """Get filtered list of documents."""
    conditions = []
    params = []
    
    # Access conditions - user must own, have created, or have shared access
    access_condition = """
        (d.owner_user_id = ? OR d.created_by_user_id = ? 
         OR d.id IN (SELECT document_id FROM document_shares WHERE shared_with_user_id = ? AND is_active = 1))
    """
    conditions.append(access_condition)
    params.extend([user_id, user_id, user_id])
    
    if search:
        conditions.append("(d.title LIKE ? OR d.document_code LIKE ? OR d.description LIKE ?)")
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])
    
    if category:
        conditions.append("d.category_id = ?")
        params.append(category)
    
    if status:
        conditions.append("d.status = ?")
        params.append(status)
    
    if doc_type:
        conditions.append("d.document_type = ?")
        params.append(doc_type)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    # Get total count
    total_result = get_one(f"""
        SELECT COUNT(*) as cnt FROM documents d
        WHERE {where_clause}
    """, params)
    total = total_result['cnt'] if total_result else 0
    
    # Get paginated results
    offset = (page - 1) * per_page
    docs = get_all(f"""
        SELECT d.*, c.name as category_name,
               u.username as owner_username,
               creator.username as created_by_username
        FROM documents d
        LEFT JOIN document_categories c ON d.category_id = c.id
        LEFT JOIN users u ON d.owner_user_id = u.id
        LEFT JOIN users creator ON d.created_by_user_id = creator.id
        WHERE {where_clause}
        ORDER BY d.created_at DESC
        LIMIT ? OFFSET ?
    """, params + [per_page, offset])
    
    return docs, total


def get_my_documents(user_id):
    """Get documents owned or created by user."""
    return get_all("""
        SELECT d.*, c.name as category_name
        FROM documents d
        LEFT JOIN document_categories c ON d.category_id = c.id
        WHERE d.created_by_user_id = ? OR d.owner_user_id = ?
        ORDER BY d.created_at DESC
    """, (user_id, user_id))


def get_shared_documents(user_id):
    """Get documents shared with user."""
    return get_all("""
        SELECT DISTINCT d.*, c.name as category_name,
               s.permission_level, s.access_level, s.shared_at
        FROM document_shares s
        JOIN documents d ON s.document_id = d.id
        LEFT JOIN document_categories c ON d.category_id = c.id
        WHERE s.shared_with_user_id = ? AND s.is_active = 1
        AND (s.expires_at IS NULL OR s.expires_at > datetime('now'))
        ORDER BY s.created_at DESC
    """, (user_id,))


def get_archived_documents(user_id):
    """Get archived documents accessible by user."""
    return get_all("""
        SELECT d.*, c.name as category_name,
               u.username as archived_by_username
        FROM documents d
        LEFT JOIN document_categories c ON d.category_id = c.id
        LEFT JOIN users u ON d.archived_by_user_id = u.id
        WHERE d.is_archived = 1
        AND (d.owner_user_id = ? OR d.created_by_user_id = ?)
        ORDER BY d.archived_at DESC
    """, (user_id, user_id))


def get_signed_documents(user_id):
    """Get documents that have been signed."""
    return get_all("""
        SELECT DISTINCT d.*, c.name as category_name,
               sr.status as signature_status,
               sr.completed_at as signed_at
        FROM signature_requests sr
        JOIN signature_participants sp ON sr.id = sp.request_id
        JOIN documents d ON sr.document_id = d.id
        LEFT JOIN document_categories c ON d.category_id = c.id
        WHERE sp.user_id = ? AND sp.status = 'Signed'
        ORDER BY sp.signed_at DESC
    """, (user_id,))


def get_pending_signature_requests_list(user_id):
    """Get pending signature requests list."""
    return get_all("""
        SELECT sr.*, d.title as document_title, d.document_code,
               p.status as my_status
        FROM signature_requests sr
        JOIN signature_participants p ON sr.id = p.request_id
        JOIN documents d ON sr.document_id = d.id
        WHERE p.user_id = ? AND p.status = 'Pending' AND sr.status = 'Pending'
        ORDER BY sr.due_date ASC, sr.created_at DESC
    """, (user_id,))


def search_documents(user_id, search='', category='', doc_type='', status='',
                     visibility='', source_module='', date_from='', date_to='',
                     page=1, per_page=50):
    """Search documents with advanced filters."""
    conditions = []
    params = []
    
    # Access conditions
    conditions.append("""
        (d.owner_user_id = ? OR d.created_by_user_id = ? 
         OR d.id IN (SELECT document_id FROM document_shares WHERE shared_with_user_id = ? AND is_active = 1))
    """)
    params.extend([user_id, user_id, user_id])
    
    if search:
        conditions.append("(d.title LIKE ? OR d.document_code LIKE ? OR d.description LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
    
    if category:
        conditions.append("d.category_id = ?")
        params.append(category)
    
    if status:
        conditions.append("d.status = ?")
        params.append(status)
    
    if visibility:
        conditions.append("d.visibility = ?")
        params.append(visibility)
    
    if source_module:
        conditions.append("d.source_module = ?")
        params.append(source_module)
    
    if date_from:
        conditions.append("date(d.created_at) >= ?")
        params.append(date_from)
    
    if date_to:
        conditions.append("date(d.created_at) <= ?")
        params.append(date_to)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    # Count
    total_result = get_one(f"SELECT COUNT(*) as cnt FROM documents d WHERE {where_clause}", params)
    total = total_result['cnt'] if total_result else 0
    
    # Results
    offset = (page - 1) * per_page
    docs = get_all(f"""
        SELECT d.*, c.name as category_name
        FROM documents d
        LEFT JOIN document_categories c ON d.category_id = c.id
        WHERE {where_clause}
        ORDER BY d.created_at DESC
        LIMIT ? OFFSET ?
    """, params + [per_page, offset])
    
    return docs, total


def search_documents_simple(user_id, search='', category='', limit=20):
    """Simple document search for autocomplete."""
    conditions = []
    params = []
    
    conditions.append("""
        (d.owner_user_id = ? OR d.created_by_user_id = ? 
         OR d.id IN (SELECT document_id FROM document_shares WHERE shared_with_user_id = ? AND is_active = 1))
    """)
    params.extend([user_id, user_id, user_id])
    
    if search:
        conditions.append("(d.title LIKE ? OR d.document_code LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    
    if category:
        conditions.append("d.category_id = ?")
        params.append(category)
    
    where_clause = " AND ".join(conditions)
    
    return get_all(f"""
        SELECT d.id, d.title, d.document_code, d.status, c.name as category_name
        FROM documents d
        LEFT JOIN document_categories c ON d.category_id = c.id
        WHERE {where_clause}
        ORDER BY d.title
        LIMIT ?
    """, params + [limit])


# =============================================================================
# FORM HANDLERS
# =============================================================================

def handle_document_create(user_id):
    """Handle document creation form submission."""
    try:
        title = request.form.get('title')
        description = request.form.get('description', '')
        category_id = request.form.get('category_id')
        tags = request.form.getlist('tags')
        visibility = request.form.get('visibility', 'Private')
        source_module = request.form.get('source_module', '')
        source_record_id = request.form.get('source_record_id')
        notes = request.form.get('notes', '')
        
        # Get uploaded file info
        stored_filename = request.form.get('stored_filename')
        original_filename = request.form.get('original_filename')
        storage_path = request.form.get('storage_path')
        checksum = request.form.get('checksum')
        file_size = request.form.get('file_size')
        mime_type = request.form.get('mime_type')
        
        if not title:
            return jsonify({'success': False, 'message': 'Title is required'})
        
        if not storage_path or not os.path.exists(storage_path):
            return jsonify({'success': False, 'message': 'File upload failed'})
        
        # Generate document code
        db = get_db()
        try:
            result = db.execute("SELECT COUNT(*) as cnt FROM documents").fetchone()
            count = result['cnt'] + 1
            document_code = f"DOC-{datetime.now().strftime('%Y%m%d')}-{count:04d}"
            
            # Insert document
            cursor = db.execute("""
                INSERT INTO documents (
                    document_code, title, description, category_id, 
                    visibility, source_module, source_record_id, notes,
                    stored_filename, original_filename, storage_path, checksum,
                    file_size, mime_type, owner_user_id, created_by_user_id,
                    status, is_latest, tags_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document_code, title, description, category_id,
                visibility, source_module, source_record_id, notes,
                stored_filename, original_filename, storage_path, checksum,
                file_size, mime_type, user_id, user_id,
                'Draft', 1, json.dumps(tags)
            ))
            document_id = cursor.lastrowid
            
            # Create first version
            db.execute("""
                INSERT INTO document_versions (
                    document_id, version_number, file_name, file_path, 
                    file_size, mime_type, checksum, is_current_version,
                    status, created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document_id, '1.0', original_filename, storage_path,
                file_size, mime_type, checksum, 1,
                'Published', user_id
            ))
            
            version_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            
            # Update document with current version
            db.execute("UPDATE documents SET current_version_id = ? WHERE id = ?", (version_id, document_id))
            
            db.commit()
        finally:
            db.close()
        
        log_audit('document', document_id, 'CREATE', user_id=user_id)
        
        return jsonify({'success': True, 'message': 'Document created successfully', 'document_id': document_id})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


def handle_document_update(document_id, user_id):
    """Handle document update form submission."""
    try:
        title = request.form.get('title')
        description = request.form.get('description', '')
        category_id = request.form.get('category_id')
        tags = request.form.getlist('tags')
        visibility = request.form.get('visibility', 'Private')
        notes = request.form.get('notes', '')
        
        if not title:
            return jsonify({'success': False, 'message': 'Title is required'})
        
        with get_db_context() as db:
            db.execute("""
                UPDATE documents SET
                    title = ?, description = ?, category_id = ?,
                    visibility = ?, notes = ?, tags_json = ?,
                    updated_at = datetime('now')
                WHERE id = ?
            """, (title, description, category_id, visibility, notes, json.dumps(tags), document_id))
            db.commit()
        
        log_audit('document', document_id, 'UPDATE', user_id=user_id)
        
        return jsonify({'success': True, 'message': 'Document updated successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


def handle_new_version(document_id, user_id):
    """Handle new version upload."""
    try:
        version_number = request.form.get('version_number')
        change_summary = request.form.get('change_summary', '')
        
        stored_filename = request.form.get('stored_filename')
        original_filename = request.form.get('original_filename')
        storage_path = request.form.get('storage_path')
        checksum = request.form.get('checksum')
        file_size = request.form.get('file_size')
        mime_type = request.form.get('mime_type')
        
        if not version_number:
            return jsonify({'success': False, 'message': 'Version number is required'})
        
        if not storage_path or not os.path.exists(storage_path):
            return jsonify({'success': False, 'message': 'File upload failed'})
        
        with get_db_context() as db:
            # Mark current version as not current
            db.execute("""
                UPDATE document_versions 
                SET is_current_version = 0 
                WHERE document_id = ?
            """, (document_id,))
            
            # Insert new version
            cursor = db.execute("""
                INSERT INTO document_versions (
                    document_id, version_number, file_name, file_path,
                    file_size, mime_type, checksum, change_summary,
                    is_current_version, status, created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document_id, version_number, original_filename, storage_path,
                file_size, mime_type, checksum, change_summary,
                1, 'Published', user_id
            ))
            version_id = cursor.lastrowid
            
            # Update document
            db.execute("""
                UPDATE documents SET
                    current_version_id = ?,
                    stored_filename = ?, original_filename = ?, storage_path = ?,
                    checksum = ?, file_size = ?, mime_type = ?,
                    is_latest = 1, updated_at = datetime('now')
                WHERE id = ?
            """, (version_id, stored_filename, original_filename, storage_path,
                  checksum, file_size, mime_type, document_id))
            
            db.commit()
        
        log_audit('document_version', version_id, 'CREATE', user_id=user_id, 
                 notes=f"New version {version_number} for document {document_id}")
        
        return jsonify({'success': True, 'message': 'New version created successfully', 'version_id': version_id})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


def handle_template_create(user_id):
    """Handle template creation."""
    try:
        template_name = request.form.get('template_name')
        template_code = request.form.get('template_code')
        description = request.form.get('description', '')
        template_type = request.form.get('template_type', 'General')
        output_format = request.form.get('output_format', 'DOCX')
        category_id = request.form.get('category_id')
        module_domain = request.form.get('module_domain', '')
        content_template = request.form.get('content_template', '')
        notes = request.form.get('notes', '')
        
        if not template_name or not template_code:
            return jsonify({'success': False, 'message': 'Name and code are required'})
        
        # Generate code if not provided
        if not template_code:
            result = get_one("SELECT COUNT(*) as cnt FROM document_templates")
            count = result['cnt'] + 1 if result else 1
            template_code = f"TPL-{count:04d}"
        
        with get_db_context() as db:
            cursor = db.execute("""
                INSERT INTO document_templates (
                    template_name, template_code, description, template_type,
                    output_format, category_id, module_domain, content_template,
                    notes, owner_user_id, created_by_user_id, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                template_name, template_code, description, template_type,
                output_format, category_id, module_domain, content_template,
                notes, user_id, user_id, 1
            ))
            template_id = cursor.lastrowid
            db.commit()
        
        log_audit('document_template', template_id, 'CREATE', user_id=user_id)
        
        return jsonify({'success': True, 'message': 'Template created successfully', 'template_id': template_id})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


def handle_template_update(template_id, user_id):
    """Handle template update."""
    try:
        template_name = request.form.get('template_name')
        description = request.form.get('description', '')
        template_type = request.form.get('template_type', 'General')
        output_format = request.form.get('output_format', 'DOCX')
        category_id = request.form.get('category_id')
        module_domain = request.form.get('module_domain', '')
        content_template = request.form.get('content_template', '')
        notes = request.form.get('notes', '')
        
        if not template_name:
            return jsonify({'success': False, 'message': 'Name is required'})
        
        # Update placeholders if provided
        placeholder_keys = request.form.getlist('placeholder_key')
        placeholder_labels = request.form.getlist('placeholder_label')
        
        with get_db_context() as db:
            db.execute("""
                UPDATE document_templates SET
                    template_name = ?, description = ?, template_type = ?,
                    output_format = ?, category_id = ?, module_domain = ?,
                    content_template = ?, notes = ?,
                    updated_at = datetime('now')
                WHERE id = ?
            """, (
                template_name, description, template_type,
                output_format, category_id, module_domain,
                content_template, notes, template_id
            ))
            
            # Delete existing placeholders and recreate
            db.execute("DELETE FROM template_placeholders WHERE template_id = ?", (template_id,))
            
            for i, (key, label) in enumerate(zip(placeholder_keys, placeholder_labels)):
                if key:
                    db.execute("""
                        INSERT INTO template_placeholders 
                        (template_id, placeholder_key, placeholder_label, sort_order)
                        VALUES (?, ?, ?, ?)
                    """, (template_id, key, label, i))
            
            db.commit()
        
        log_audit('document_template', template_id, 'UPDATE', user_id=user_id)
        
        return jsonify({'success': True, 'message': 'Template updated successfully'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


def handle_document_generate(template_id, user_id):
    """Handle document generation from template."""
    try:
        title = request.form.get('title')
        linked_module = request.form.get('linked_module')
        linked_record_id = request.form.get('linked_record_id')
        notes = request.form.get('notes', '')
        
        if not title:
            return jsonify({'success': False, 'message': 'Title is required'})
        
        template = get_one("SELECT * FROM document_templates WHERE id = ?", (template_id,))
        if not template:
            return jsonify({'success': False, 'message': 'Template not found'})
        
        # Get placeholder values from form
        placeholder_keys = request.form.getlist('placeholder_key')
        placeholder_values = request.form.getlist('placeholder_value')
        
        parameters = dict(zip(placeholder_keys, placeholder_values))
        
        # Generate document code
        result = get_one("SELECT COUNT(*) as cnt FROM documents")
        count = result['cnt'] + 1 if result else 1
        document_code = f"DOC-{datetime.now().strftime('%Y%m%d')}-{count:04d}"
        
        # For now, create a placeholder file indicating the document would be generated
        # In a full implementation, this would use a document generation library
        content = f"Generated from template: {template['template_name']}\n"
        content += f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += f"Generated by: User {user_id}\n\n"
        content += "Parameters:\n"
        for key, value in parameters.items():
            content += f"  {key}: {value}\n"
        
        # Save generated content as a file
        generated_filename = f"generated_{document_code}.txt"
        generated_path = os.path.join(DOCUMENT_UPLOAD_FOLDER, generated_filename)
        
        with open(generated_path, 'w') as f:
            f.write(content)
        
        with get_db_context() as db:
            # Create document
            cursor = db.execute("""
                INSERT INTO documents (
                    document_code, title, description, category_id,
                    stored_filename, original_filename, storage_path,
                    file_size, mime_type, owner_user_id, created_by_user_id,
                    status, is_latest, is_template, template_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document_code, title, f"Generated from {template['template_name']}",
                template['category_id'], generated_filename,
                generated_filename, generated_path, len(content),
                'text/plain', user_id, user_id, 'Draft', 1, 0, template_id
            ))
            document_id = cursor.lastrowid
            
            # Create version
            cursor = db.execute("""
                INSERT INTO document_versions (
                    document_id, version_number, file_name, file_path,
                    file_size, mime_type, is_current_version, status,
                    created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (document_id, '1.0', generated_filename, generated_path,
                  len(content), 'text/plain', 1, 'Draft', user_id))
            version_id = cursor.lastrowid
            
            # Update document
            db.execute("UPDATE documents SET current_version_id = ? WHERE id = ?", (version_id, document_id))
            
            # Record in generated_documents
            db.execute("""
                INSERT INTO generated_documents (
                    generated_code, template_id, source_document_id,
                    linked_module, linked_record_id, title,
                    generated_by_user_id, file_path, file_size,
                    mime_type, status, parameters_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"GEN-{count:04d}", template_id, None,
                linked_module, linked_record_id, title,
                user_id, generated_path, len(content),
                'text/plain', 'Generated', json.dumps(parameters)
            ))
            
            # Update template usage count
            db.execute("""
                UPDATE document_templates 
                SET usage_count = usage_count + 1, last_used_at = datetime('now')
                WHERE id = ?
            """, (template_id,))
            
            db.commit()
        
        log_audit('document', document_id, 'GENERATE', user_id=user_id, 
                 notes=f"Generated from template {template_id}")
        
        return jsonify({
            'success': True, 
            'message': 'Document generated successfully',
            'document_id': document_id
        })
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


def handle_signature_request_create(document_id, user_id):
    """Handle signature request creation."""
    try:
        request_title = request.form.get('request_title')
        request_message = request.form.get('request_message', '')
        signer_ids = request.form.getlist('signer_ids')
        due_date = request.form.get('due_date')
        priority = request.form.get('priority', 'Normal')
        sequential = 1 if request.form.get('sequential_signing') else 0
        
        if not request_title:
            return jsonify({'success': False, 'message': 'Title is required'})
        
        if not signer_ids:
            return jsonify({'success': False, 'message': 'At least one signer is required'})
        
        # Generate request code
        result = get_one("SELECT COUNT(*) as cnt FROM signature_requests")
        count = result['cnt'] + 1 if result else 1
        request_code = f"SIG-{datetime.now().strftime('%Y%m%d')}-{count:04d}"
        
        with get_db_context() as db:
            cursor = db.execute("""
                INSERT INTO signature_requests (
                    request_code, document_id, request_title, request_message,
                    requestor_user_id, priority, due_date, sequential_signing,
                    signing_order, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request_code, document_id, request_title, request_message,
                user_id, priority, due_date, sequential, 1, 'Pending'
            ))
            request_id = cursor.lastrowid
            
            # Add participants
            for i, signer_id in enumerate(signer_ids):
                signer_id = int(signer_id)
                signer = get_one("SELECT username, email FROM users WHERE id = ?", (signer_id))
                
                db.execute("""
                    INSERT INTO signature_participants (
                        request_id, user_id, participant_name, participant_email,
                        participant_role, signing_order, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    request_id, signer_id, signer['username'] if signer else '',
                    signer['email'] if signer else '',
                    'Signer', i + 1, 'Pending'
                ))
            
            # Update document signature status
            db.execute("""
                UPDATE documents SET signature_status = 'Pending Signature'
                WHERE id = ?
            """, (document_id,))
            
            db.commit()
        
        log_audit('signature_request', request_id, 'CREATE', user_id=user_id)
        
        # Create notifications for signers
        for signer_id in signer_ids:
            create_notification(
                title=f"Signature Request: {request_title}",
                message=f"You have been requested to sign a document: {request_title}",
                notification_type="APPROVAL",
                user_id=int(signer_id),
                severity="MEDIUM",
                link_url=f"/documents/signatures/{request_id}",
                related_entity_type="signature_request",
                related_entity_id=request_id
            )
        
        return jsonify({
            'success': True, 
            'message': 'Signature request created successfully',
            'request_id': request_id
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


    # =============================================================================
    # FILE MANAGEMENT - FOLDER SYSTEM ROUTES
    # =============================================================================

    @app.route('/documents/file-manager')
    @require_login
    @document_permission_required('view')
    def documents_file_manager():
        """Main file manager with folder tree view."""
        user_id = get_current_user_id()
        root_folders = get_user_root_folders(user_id)
        quick_access = get_user_quick_access(user_id, limit=10)
        favorites = get_user_favorites(user_id, limit=10)
        stats = get_file_management_stats(user_id)
        return render_template('documents/file_manager.html',
            root_folders=root_folders,
            quick_access=quick_access,
            favorites=favorites,
            stats=stats,
            page_title='File Manager')

    @app.route('/documents/folders')
    @require_login
    @document_permission_required('view')
    def documents_folders():
        """Folder tree view."""
        user_id = get_current_user_id()
        folders = get_folder_tree(user_id=user_id)
        return render_template('documents/folders.html',
            folders=folders,
            page_title='Folders')

    @app.route('/documents/folder/<int:folder_id>')
    @require_login
    @document_permission_required('view')
    def documents_folder_detail(folder_id):
        """Folder detail page."""
        user_id = get_current_user_id()
        folder = get_folder_by_id(folder_id)
        if not folder:
            flash("Folder not found.", "error")
            return redirect(url_for('documents_folders'))
        if not check_folder_access(user_id, folder_id, 'read'):
            flash("You don't have permission to access this folder.", "error")
            return redirect(url_for('documents_folders'))
        subfolders = get_folder_children(folder_id)
        documents = get_folder_documents(folder_id, user_id)
        stats = get_folder_stats(folder_id)
        path = get_folder_path(folder_id)
        log_folder_activity(folder_id, user_id, 'view')
        return render_template('documents/folder_detail.html',
            folder=folder,
            subfolders=subfolders,
            documents=documents,
            stats=stats,
            path=path,
            page_title=folder['name'])

    @app.route('/documents/folder/create', methods=['POST'])
    @require_login
    @document_permission_required('write')
    def documents_folder_create():
        """Create a new folder."""
        user_id = get_current_user_id()
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        parent_id = request.form.get('parent_id')
        folder_type = request.form.get('folder_type', 'general')
        if not name:
            return jsonify({'success': False, 'message': 'Folder name is required'})
        if parent_id:
            parent_id = int(parent_id)
            if not check_folder_access(user_id, parent_id, 'write'):
                return jsonify({'success': False, 'message': 'Permission denied'})
        try:
            with get_db_context() as db:
                folder_code = generate_folder_code(db)
                cursor = db.execute("""
                    INSERT INTO document_folders (folder_code, name, description, folder_type, parent_id, owner_user_id, created_by_user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (folder_code, name, description, folder_type, parent_id, user_id, user_id))
                folder_id = cursor.lastrowid
                db.commit()
            log_folder_activity(folder_id, user_id, 'create', f"Created folder: {name}")
            return jsonify({'success': True, 'message': 'Folder created', 'folder_id': folder_id})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

    @app.route('/documents/folder/<int:folder_id>/edit', methods=['POST'])
    @require_login
    @document_permission_required('write')
    def documents_folder_edit(folder_id):
        """Edit folder details."""
        user_id = get_current_user_id()
        if not check_folder_access(user_id, folder_id, 'write'):
            return jsonify({'success': False, 'message': 'Permission denied'})
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        if not name:
            return jsonify({'success': False, 'message': 'Folder name is required'})
        try:
            with get_db_context() as db:
                db.execute("""
                    UPDATE document_folders SET name = ?, description = ?, updated_at = datetime('now')
                    WHERE id = ?
                """, (name, description, folder_id))
                db.commit()
            log_folder_activity(folder_id, user_id, 'edit', f"Updated folder: {name}")
            return jsonify({'success': True, 'message': 'Folder updated'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

    @app.route('/documents/folder/<int:folder_id>/delete', methods=['POST'])
    @require_login
    @document_permission_required('admin')
    def documents_folder_delete(folder_id):
        """Archive a folder."""
        user_id = get_current_user_id()
        if not check_folder_access(user_id, folder_id, 'admin'):
            return jsonify({'success': False, 'message': 'Permission denied'})
        try:
            with get_db_context() as db:
                db.execute("""
                    UPDATE document_folders SET is_archived = 1, archived_by_user_id = ?, archived_at = datetime('now'), updated_at = datetime('now')
                    WHERE id = ?
                """, (user_id, folder_id))
                db.commit()
            log_folder_activity(folder_id, user_id, 'archive', "Folder archived")
            return jsonify({'success': True, 'message': 'Folder archived'})
        except Exception as e:
            return jsonify({'success': False, 'message': str(e)})

    @app.route('/documents/folder/<int:folder_id>/permissions')
    @require_login
    @document_permission_required('admin')
    def documents_folder_permissions(folder_id):
        """Manage folder permissions."""
        user_id = get_current_user_id()
        folder = get_folder_by_id(folder_id)
        if not folder:
            flash("Folder not found.", "error")
            return redirect(url_for('documents_folders'))
        if not check_folder_access(user_id, folder_id, 'admin'):
            flash("Permission denied.", "error")
            return redirect(url_for('documents_folder_detail', folder_id=folder_id))
        with get_db_context() as db:
            perms = db.execute("""
                SELECT fp.*, u.username
                FROM folder_permissions fp
                LEFT JOIN users u ON fp.user_id = u.id
                WHERE fp.folder_id = ?
            """, (folder_id,)).fetchall()
        return render_template('documents/folder_permissions.html',
            folder=folder,
            permissions=[dict(p) for p in perms],
            page_title=f'Permissions - {folder["name"]}')

    @app.route('/documents/folder/<int:folder_id>/activity')
    @require_login
    @document_permission_required('read')
    def documents_folder_activity(folder_id):
        """View folder activity log."""
        user_id = get_current_user_id()
        folder = get_folder_by_id(folder_id)
        if not folder:
            flash("Folder not found.", "error")
            return redirect(url_for('documents_folders'))
        if not check_folder_access(user_id, folder_id, 'read'):
            flash("Permission denied.", "error")
            return redirect(url_for('documents_folders'))
        with get_db_context() as db:
            activities = db.execute("""
                SELECT fa.*, u.username
                FROM folder_activity_log fa
                LEFT JOIN users u ON fa.user_id = u.id
                WHERE fa.folder_id = ?
                ORDER BY fa.created_at DESC
                LIMIT 100
            """, (folder_id,)).fetchall()
        return render_template('documents/folder_activity.html',
            folder=folder,
            activities=[dict(a) for a in activities],
            page_title=f'Activity - {folder["name"]}')

    @app.route('/documents/folder/api/tree')
    @require_login
    def documents_folder_tree_api():
        """API endpoint for folder tree AJAX."""
        user_id = get_current_user_id()
        parent_id = request.args.get('parent_id')
        parent_id = int(parent_id) if parent_id and parent_id != 'null' else None
        if parent_id:
            folders = get_folder_children(parent_id)
        else:
            folders = get_user_root_folders(user_id)
        return jsonify({'success': True, 'folders': folders})

    @app.route('/documents/favorites')
    @require_login
    @document_permission_required('view')
    def documents_favorites():
        """User's favorite documents."""
        user_id = get_current_user_id()
        favorites = get_user_favorites(user_id, limit=50)
        return render_template('documents/favorites.html',
            favorites=favorites,
            page_title='My Favorites')

    @app.route('/documents/favorite/<int:document_id>/toggle', methods=['POST'])
    @require_login
    def documents_favorite_toggle(document_id):
        """Toggle favorite status."""
        user_id = get_current_user_id()
        if is_document_favorited(document_id, user_id):
            remove_document_favorite(document_id, user_id)
            return jsonify({'success': True, 'status': 'removed'})
        else:
            add_document_favorite(document_id, user_id)
            return jsonify({'success': True, 'status': 'added'})

    @app.route('/documents/quick-access')
    @require_login
    @document_permission_required('view')
    def documents_quick_access():
        """User's quick access items."""
        user_id = get_current_user_id()
        items = get_user_quick_access(user_id, limit=20)
        return render_template('documents/quick_access.html',
            items=items,
            page_title='Quick Access')

    @app.route('/documents/advanced-search')
    @require_login
    @document_permission_required('view')
    def documents_advanced_search():
        """Advanced search page."""
        return render_template('documents/advanced_search.html',
            page_title='Advanced Search')

    @app.route('/documents/search/api', methods=['POST'])
    @require_login
    def documents_search_api():
        """API endpoint for advanced search."""
        criteria = {
            'keyword': request.form.get('keyword', ''),
            'folder_id': request.form.get('folder_id'),
            'document_type': request.form.get('document_type'),
            'owner_user_id': request.form.get('owner_user_id'),
            'visibility': request.form.get('visibility'),
        }
        if criteria['folder_id']:
            criteria['folder_id'] = int(criteria['folder_id'])
        results = search_documents_advanced(criteria)
        return jsonify({'success': True, 'results': results, 'count': len(results)})

    @app.route('/documents/checkouts')
    @require_login
    @document_permission_required('view')
    def documents_checkouts():
        """Show checked out documents."""
        user_id = get_current_user_id()
        my_locks = get_user_locks(user_id)
        from permissions import user_has_permission
        if user_has_permission(user_id, 'documents', 'checkin_checkout', 'manage'):
            overdue = get_overdue_locks()
        else:
            overdue = []
        return render_template('documents/checkouts.html',
            my_locks=my_locks,
            overdue_locks=overdue,
            page_title='Checked Out Files')

    @app.route('/documents/<int:document_id>/lock', methods=['POST'])
    @require_login
    def documents_lock(document_id):
        """Lock a document for checkout."""
        user_id = get_current_user_id()
        lock_type = request.form.get('lock_type', 'checkout')
        reason = request.form.get('reason', '')
        result, error = lock_document(document_id, user_id, lock_type, reason)
        if error:
            return jsonify({'success': False, 'message': error})
        return jsonify({'success': True, 'message': 'Document locked', 'lock': result})

    @app.route('/documents/<int:document_id>/unlock', methods=['POST'])
    @require_login
    def documents_unlock(document_id):
        """Unlock a document."""
        user_id = get_current_user_id()
        force = request.form.get('force', 'false').lower() == 'true'
        from permissions import user_has_permission
        if force and not user_has_permission(user_id, 'documents', 'checkin_checkout', 'manage'):
            return jsonify({'success': False, 'message': 'Only managers can force unlock'})
        result, error = unlock_document(document_id, user_id, force)
        if error:
            return jsonify({'success': False, 'message': error})
        return jsonify({'success': True, 'message': 'Document unlocked'})

    @app.route('/documents/workspace')
    @require_login
    @document_permission_required('view')
    def documents_workspace():
        """Personal workspace."""
        user_id = get_current_user_id()
        stats = get_file_management_stats(user_id)
        recent_locks = get_user_locks(user_id)[:5]
        favorites = get_user_favorites(user_id, limit=6)
        return render_template('documents/workspace.html',
            stats=stats,
            recent_locks=recent_locks,
            favorites=favorites,
            page_title='My Workspace')

    @app.route('/documents/executive-dashboard')
    @require_login
    @document_permission_required('view')
    def documents_executive_dashboard():
        """Executive dashboard for documents."""
        stats = get_file_management_stats()
        return render_template('documents/executive_dashboard.html',
            stats=stats,
            page_title='Documents Executive Dashboard')

    @app.route('/documents/reports-center')
    @require_login
    @document_permission_required('view')
    def documents_reports_center():
        """Reports center."""
        return render_template('documents/reports_center.html',
            page_title='Reports Center')

    @app.route('/documents/report/file-inventory')
    @require_login
    @document_permission_required('view')
    def documents_report_file_inventory():
        """File inventory report."""
        with get_db_context() as db:
            docs = db.execute("""
                SELECT d.*, f.name as folder_name, u.username as owner_name,
                       v.version_number, v.uploaded_at as last_version_date
                FROM documents d
                LEFT JOIN document_folders f ON d.folder_id = f.id
                LEFT JOIN users u ON d.owner_user_id = u.id
                LEFT JOIN document_versions v ON d.current_version_id = v.id
                WHERE d.archived = 0
                ORDER BY d.updated_at DESC
            """).fetchall()
        return render_template('documents/report_file_inventory.html',
            documents=[dict(d) for d in docs],
            page_title='File Inventory Report')

    @app.route('/documents/report/folder-utilization')
    @require_login
    @document_permission_required('view')
    def documents_report_folder_utilization():
        """Folder utilization report."""
        with get_db_context() as db:
            folders = db.execute("""
                SELECT f.*,
                       (SELECT COUNT(*) FROM document_folders WHERE parent_id = f.id) as subfolder_count,
                       (SELECT COUNT(*) FROM documents WHERE folder_id = f.id) as document_count
                FROM document_folders f
                WHERE f.is_archived = 0
                ORDER BY f.name
            """).fetchall()
        return render_template('documents/report_folder_utilization.html',
            folders=[dict(f) for f in folders],
            page_title='Folder Utilization Report')

    @app.route('/documents/report/access-audit')
    @require_login
    @document_permission_required('view')
    def documents_report_access_audit():
        """Access audit report."""
        with get_db_context() as db:
            logs = db.execute("""
                SELECT dal.*, d.title as document_title, u.username
                FROM document_access_logs dal
                LEFT JOIN documents d ON dal.document_id = d.id
                LEFT JOIN users u ON dal.user_id = u.id
                ORDER BY dal.accessed_at DESC
                LIMIT 500
            """).fetchall()
        return render_template('documents/report_access_audit.html',
            logs=[dict(l) for l in logs],
            page_title='Access Audit Report')

    @app.route('/documents/report/retention-status')
    @require_login
    @document_permission_required('view')
    def documents_report_retention_status():
        """Retention status report."""
        with get_db_context() as db:
            docs = db.execute("""
                SELECT d.*, f.name as folder_name, u.username as owner_name
                FROM documents d
                LEFT JOIN document_folders f ON d.folder_id = f.id
                LEFT JOIN users u ON d.owner_user_id = u.id
                WHERE d.archived = 0 AND d.expiry_date IS NOT NULL
                ORDER BY d.expiry_date ASC
            """).fetchall()
        return render_template('documents/report_retention_status.html',
            documents=[dict(d) for d in docs],
            page_title='Retention Status Report')

    @app.route('/documents/<int:document_id>/preview')
    @require_login
    def documents_preview(document_id):
        """Preview a document."""
        user_id = get_current_user_id()
        doc = get_one("""
            SELECT d.*, v.file_path, v.file_name, v.mime_type
            FROM documents d
            LEFT JOIN document_versions v ON d.current_version_id = v.id
            WHERE d.id = ?
        """, (document_id,))
        if not doc:
            flash("Document not found.", "error")
            return redirect(url_for('documents_all'))
        file_path = doc.get('file_path') or doc.get('storage_path')
        if not file_path or not os.path.exists(file_path):
            flash("File not found on server.", "error")
            return redirect(url_for('documents_detail', document_id=document_id))
        can_download = document_has_permission(user_id, document_id, 'download')
        mime_type = doc.get('mime_type', '')
        file_ext = doc.get('file_type', '').lower()
        is_pdf = file_ext == 'pdf' or mime_type == 'application/pdf'
        is_image = mime_type.startswith('image/')
        is_video = mime_type.startswith('video/')
        is_audio = mime_type.startswith('audio/')
        is_office = file_ext in ['doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']
        file_icon_map = {
            'pdf': 'file-pdf', 'doc': 'file-word', 'docx': 'file-word',
            'xls': 'file-excel', 'xlsx': 'file-excel', 'ppt': 'file-powerpoint', 'pptx': 'file-powerpoint',
            'jpg': 'file-image', 'jpeg': 'file-image', 'png': 'file-image', 'gif': 'file-image',
        }
        file_icon = file_icon_map.get(file_ext, 'file-alt')
        return render_template('documents/preview.html',
            document=doc, can_download=can_download,
            is_pdf=is_pdf, is_image=is_image, is_video=is_video,
            is_audio=is_audio, is_office=is_office,
            mime_type=mime_type, file_icon=file_icon)

    @app.route('/documents/flow/notify', methods=['POST'])
    @require_login
    def documents_flow_notify():
        """Flow notification endpoint for document events."""
        event_type = request.form.get('event_type')
        document_id = request.form.get('document_id')
        user_id = get_current_user_id()
        message = request.form.get('message', '')
        if event_type == 'share':
            create_notification(
                user_id=user_id,
                title='Document Shared',
                message=message,
                module='documents',
                related_id=document_id
            )
        return jsonify({'success': True})
