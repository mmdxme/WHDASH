"""
Document Management Module Database Models
==========================================
Enterprise-grade Document Management System for the MMDx platform.

This module provides:
- Centralized document storage and versioning
- Document templates with placeholder support
- E-signature workflows with multi-signer support
- Document linking to business records across all modules
- Full audit trail and access logging
- Retention and archive management

Tables:
- document_categories: Document type/category definitions
- document_tags: Reusable tags for document classification
- documents: Master document registry
- document_versions: Version history for each document
- document_links: Links between documents and business records
- document_templates: Template definitions for document generation
- template_placeholders: Placeholder definitions for templates
- generated_documents: Records of documents generated from templates
- signature_requests: E-signature request tracking
- signature_participants: Signers and their status
- document_shares: Document sharing/access grants
- document_access_logs: Access audit trail
- document_settings: Document management configuration

Usage:
    from document_models import initialize_document_tables, get_document_categories
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'warehouse.db'))


def get_db():
    """Get database connection with Row factory for dict-like access."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# =============================================================================
# DOCUMENT MANAGEMENT TABLE DEFINITIONS
# =============================================================================

DOCUMENT_TABLES = [
    # -------------------------------------------------------------------------
    # 1. Document Categories
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS document_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        code TEXT UNIQUE,
        parent_id INTEGER,
        icon TEXT,
        color TEXT DEFAULT '#6c757d',
        sort_order INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        requires_approval INTEGER DEFAULT 0,
        retention_period_days INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by_user_id INTEGER,
        FOREIGN KEY (parent_id) REFERENCES document_categories(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 2. Document Tags
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS document_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        color TEXT DEFAULT '#6c757d',
        is_system INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by_user_id INTEGER
    )""",

    # -------------------------------------------------------------------------
    # 3. Documents - Master Registry
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        category_id INTEGER,
        document_type TEXT DEFAULT 'file',
        mime_type TEXT,
        file_size INTEGER,
        stored_filename TEXT,
        original_filename TEXT,
        storage_path TEXT,
        checksum TEXT,
        company_id INTEGER,
        branch_id INTEGER,
        department_id INTEGER,
        owner_user_id INTEGER,
        created_by_user_id INTEGER,
        source_module TEXT,
        source_record_id INTEGER,
        status TEXT DEFAULT 'Draft',
        visibility TEXT DEFAULT 'Private',
        current_version_id INTEGER,
        is_latest INTEGER DEFAULT 1,
        is_archived INTEGER DEFAULT 0,
        archived_at DATETIME,
        archived_by_user_id INTEGER,
        archive_reason TEXT,
        retention_date DATE,
        expiry_date DATE,
        is_template INTEGER DEFAULT 0,
        template_id INTEGER,
        signature_status TEXT DEFAULT 'Not Applicable',
        signed_at DATETIME,
        signed_by_user_id INTEGER,
        metadata_json TEXT,
        tags_json TEXT,
        notes TEXT,
        approved_by_user_id INTEGER,
        approved_at DATETIME,
        rejection_reason TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES document_categories(id) ON DELETE SET NULL,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL,
        FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 4. Document Versions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS document_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        version_number TEXT NOT NULL,
        version_label TEXT,
        file_name TEXT NOT NULL,
        file_path TEXT NOT NULL,
        file_size INTEGER,
        mime_type TEXT,
        checksum TEXT,
        change_summary TEXT,
        is_current_version INTEGER DEFAULT 0,
        is_published INTEGER DEFAULT 0,
        is_obsolete INTEGER DEFAULT 0,
        published_at DATETIME,
        published_by_user_id INTEGER,
        status TEXT DEFAULT 'Draft',
        checked_out_by_user_id INTEGER,
        checked_out_at DATETIME,
        checked_out_until DATETIME,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
        FOREIGN KEY (checked_out_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 5. Document Links - Business Record Associations
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS document_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        document_version_id INTEGER,
        linked_module TEXT NOT NULL,
        linked_record_id INTEGER NOT NULL,
        link_type TEXT DEFAULT 'Related',
        description TEXT,
        is_primary INTEGER DEFAULT 0,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
        FOREIGN KEY (document_version_id) REFERENCES document_versions(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 6. Document Templates
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS document_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_code TEXT UNIQUE NOT NULL,
        template_name TEXT NOT NULL,
        description TEXT,
        template_type TEXT,
        output_format TEXT DEFAULT 'DOCX',
        category_id INTEGER,
        module_domain TEXT,
        content_template TEXT,
        is_active INTEGER DEFAULT 1,
        is_default INTEGER DEFAULT 0,
        requires_signature INTEGER DEFAULT 0,
        signature_type TEXT,
        version INTEGER DEFAULT 1,
        owner_user_id INTEGER,
        created_by_user_id INTEGER,
        approved_by_user_id INTEGER,
        approved_at DATETIME,
        usage_count INTEGER DEFAULT 0,
        last_used_at DATETIME,
        metadata_json TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES document_categories(id) ON DELETE SET NULL,
        FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by_user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 7. Template Placeholders
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS template_placeholders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_id INTEGER NOT NULL,
        placeholder_key TEXT NOT NULL,
        placeholder_label TEXT,
        description TEXT,
        default_value TEXT,
        data_type TEXT DEFAULT 'text',
        is_required INTEGER DEFAULT 0,
        is_system INTEGER DEFAULT 0,
        source_module TEXT,
        source_field TEXT,
        validation_pattern TEXT,
        sort_order INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (template_id) REFERENCES document_templates(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 8. Generated Documents
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS generated_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        generated_code TEXT UNIQUE NOT NULL,
        template_id INTEGER NOT NULL,
        source_document_id INTEGER,
        linked_module TEXT,
        linked_record_id INTEGER,
        title TEXT NOT NULL,
        generated_by_user_id INTEGER NOT NULL,
        file_path TEXT,
        file_size INTEGER,
        mime_type TEXT,
        status TEXT DEFAULT 'Generated',
        generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        parameters_json TEXT,
        notes TEXT,
        FOREIGN KEY (template_id) REFERENCES document_templates(id) ON DELETE SET NULL,
        FOREIGN KEY (generated_by_user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 9. Signature Requests
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS signature_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_code TEXT UNIQUE NOT NULL,
        document_id INTEGER NOT NULL,
        document_version_id INTEGER,
        request_title TEXT NOT NULL,
        request_message TEXT,
        requestor_user_id INTEGER NOT NULL,
        signature_type TEXT DEFAULT 'electronic',
        signing_order INTEGER DEFAULT 1,
        sequential_signing INTEGER DEFAULT 1,
        status TEXT DEFAULT 'Pending',
        priority TEXT DEFAULT 'Normal',
        due_date DATETIME,
        expired_at DATETIME,
        completed_at DATETIME,
        canceled_at DATETIME,
        canceled_by_user_id INTEGER,
        cancellation_reason TEXT,
        company_id INTEGER,
        branch_id INTEGER,
        department_id INTEGER,
        metadata_json TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
        FOREIGN KEY (document_version_id) REFERENCES document_versions(id) ON DELETE SET NULL,
        FOREIGN KEY (requestor_user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (canceled_by_user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 10. Signature Participants
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS signature_participants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER NOT NULL,
        user_id INTEGER,
        participant_name TEXT,
        participant_email TEXT,
        participant_role TEXT DEFAULT 'Signer',
        signing_order INTEGER DEFAULT 1,
        status TEXT DEFAULT 'Pending',
        signed_at DATETIME,
        signed_ip_address TEXT,
        signed_user_agent TEXT,
        rejection_reason TEXT,
        signed_file_path TEXT,
        signature_data TEXT,
        verification_token TEXT,
        reminded_at DATETIME,
        reminders_count INTEGER DEFAULT 0,
        expires_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (request_id) REFERENCES signature_requests(id) ON DELETE CASCADE,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 11. Document Shares
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS document_shares (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        shared_with_user_id INTEGER,
        shared_with_role TEXT,
        shared_with_department_id INTEGER,
        permission_level TEXT DEFAULT 'View',
        share_type TEXT DEFAULT 'Internal',
        shared_by_user_id INTEGER NOT NULL,
        access_level TEXT DEFAULT 'Read',
        expires_at DATETIME,
        is_active INTEGER DEFAULT 1,
        revoked_at DATETIME,
        revoked_by_user_id INTEGER,
        revocation_reason TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
        FOREIGN KEY (shared_with_user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (shared_by_user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (revoked_by_user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 12. Document Access Logs
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS document_access_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        document_version_id INTEGER,
        user_id INTEGER,
        access_action TEXT NOT NULL,
        access_type TEXT,
        ip_address TEXT,
        user_agent TEXT,
        session_id TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
        FOREIGN KEY (document_version_id) REFERENCES document_versions(id) ON DELETE SET NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 13. Document Settings
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS document_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT UNIQUE NOT NULL,
        setting_value TEXT,
        setting_type TEXT DEFAULT 'string',
        category TEXT DEFAULT 'General',
        description TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 14. Retention Rules
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS document_retention_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_name TEXT NOT NULL,
        rule_code TEXT UNIQUE,
        description TEXT,
        category_id INTEGER,
        document_type TEXT,
        source_module TEXT,
        retention_period_days INTEGER,
        retention_action TEXT DEFAULT 'Archive',
        archive_location TEXT,
        requires_approval INTEGER DEFAULT 0,
        approver_role TEXT,
        is_active INTEGER DEFAULT 1,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES document_categories(id) ON DELETE SET NULL
    )""",
]


# =============================================================================
# TABLE INDEXES
# =============================================================================

DOCUMENT_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_documents_code ON documents(document_code)",
    "CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category_id)",
    "CREATE INDEX IF NOT EXISTS idx_documents_owner ON documents(owner_user_id)",
    "CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)",
    "CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source_module, source_record_id)",
    "CREATE INDEX IF NOT EXISTS idx_documents_archived ON documents(is_archived)",
    "CREATE INDEX IF NOT EXISTS idx_versions_document ON document_versions(document_id)",
    "CREATE INDEX IF NOT EXISTS idx_versions_current ON document_versions(is_current_version)",
    "CREATE INDEX IF NOT EXISTS idx_links_document ON document_links(document_id)",
    "CREATE INDEX IF NOT EXISTS idx_links_module ON document_links(linked_module, linked_record_id)",
    "CREATE INDEX IF NOT EXISTS idx_shares_document ON document_shares(document_id)",
    "CREATE INDEX IF NOT EXISTS idx_access_logs_document ON document_access_logs(document_id)",
    "CREATE INDEX IF NOT EXISTS idx_access_logs_user ON document_access_logs(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_signature_requests_status ON signature_requests(status)",
    "CREATE INDEX IF NOT EXISTS idx_signature_participants_request ON signature_participants(request_id)",
    "CREATE INDEX IF NOT EXISTS idx_signature_participants_status ON signature_participants(status)",
    "CREATE INDEX IF NOT EXISTS idx_templates_category ON document_templates(category_id)",
    "CREATE INDEX IF NOT EXISTS idx_templates_active ON document_templates(is_active)",
]


# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_document_tables():
    """Initialize all document management tables and seed default data."""
    db = get_db()
    try:
        # Create tables
        for table_sql in DOCUMENT_TABLES:
            db.execute(table_sql)
        
        # Create indexes
        for index_sql in DOCUMENT_INDEXES:
            db.execute(index_sql)
        
        db.commit()
        
        # Seed default categories
        seed_default_categories(db)
        
        # Seed default tags
        seed_default_tags(db)
        
        # Seed default settings
        seed_default_settings(db)
        
    finally:
        db.close()


def seed_default_categories(db):
    """Seed default document categories."""
    default_categories = [
        ('Contracts', 'Contract and agreement documents', 'CONTRACT', None, 'fa-file-contract', '#28a745', 1, 1, 90),
        ('Invoices', 'Invoice and billing documents', 'INVOICE', None, 'fa-file-invoice', '#007bff', 2, 1, 2555),
        ('Purchase Orders', 'Purchase order documents', 'PO', None, 'fa-file-pdf', '#6f42c1', 3, 0, 2555),
        ('Quotations', 'Quotation and proposal documents', 'QUOTATION', None, 'fa-file-alt', '#17a2b8', 4, 0, 365),
        ('Delivery Notes', 'Delivery and shipping documents', 'DELIVERY', None, 'fa-truck', '#fd7e14', 5, 0, 1095),
        ('Receipts', 'Payment receipt documents', 'RECEIPT', None, 'fa-receipt', '#20c997', 6, 0, 2555),
        ('HR Documents', 'Human resources documents', 'HR', None, 'fa-user-tie', '#e83e8c', 7, 1, 3650),
        ('Quality Documents', 'Quality assurance and compliance', 'QUALITY', None, 'fa-check-double', '#dc3545', 8, 1, 3650),
        ('Financial Reports', 'Financial statement and reports', 'FINANCE', None, 'fa-chart-bar', '#6c757d', 9, 1, 2555),
        ('Legal Documents', 'Legal and compliance documents', 'LEGAL', None, 'fa-gavel', '#343a40', 10, 1, 3650),
        ('Technical Documents', 'Technical specifications and manuals', 'TECHNICAL', None, 'fa-cogs', '#6610f2', 11, 0, 1825),
        ('Correspondence', 'Letters and communication', 'CORRESPONDENCE', None, 'fa-envelope', '#007bff', 12, 0, 365),
        ('Reports', 'General reports and analysis', 'REPORT', None, 'fa-chart-pie', '#17a2b8', 13, 0, 730),
        ('Archives', 'Archived documents', 'ARCHIVE', None, 'fa-archive', '#6c757d', 14, 0, None),
    ]
    
    for name, desc, code, parent, icon, color, order, approval, retention in default_categories:
        existing = db.execute("SELECT id FROM document_categories WHERE code = ?", (code,)).fetchone()
        if not existing:
            db.execute("""
                INSERT INTO document_categories 
                (name, description, code, parent_id, icon, color, sort_order, requires_approval, retention_period_days)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, desc, code, parent, icon, color, order, approval, retention))


def seed_default_tags(db):
    """Seed default document tags."""
    default_tags = [
        ('Confidential', 'Confidential documents requiring restricted access', '#dc3545', 1),
        ('Internal', 'Internal use only', '#6c757d', 1),
        ('External', 'Can be shared externally', '#28a745', 1),
        ('Urgent', 'Urgent/priority documents', '#fd7e14', 1),
        ('Draft', 'Draft documents not finalized', '#17a2b8', 1),
        ('Final', 'Finalized approved documents', '#28a745', 1),
        ('Review Required', 'Documents pending review', '#ffc107', 1),
        ('Archived', 'Archived documents', '#6c757d', 1),
        ('Original', 'Original source documents', '#007bff', 1),
        ('Copy', 'Copied documents', '#6610f2', 1),
        ('Signed', 'Documents with signatures', '#20c997', 1),
        ('Pending Signature', 'Awaiting signatures', '#ffc107', 1),
    ]
    
    for name, desc, color, is_system in default_tags:
        existing = db.execute("SELECT id FROM document_tags WHERE name = ?", (name,)).fetchone()
        if not existing:
            db.execute("""
                INSERT INTO document_tags (name, description, color, is_system)
                VALUES (?, ?, ?, ?)
            """, (name, desc, color, is_system))


def seed_default_settings(db):
    """Seed default document management settings."""
    default_settings = [
        ('max_file_size_mb', '50', 'integer', 'Storage', 'Maximum file size for uploads in MB'),
        ('allowed_extensions', 'pdf,doc,docx,xls,xlsx,png,jpg,jpeg,gif,txt,csv,zip,rar', 'string', 'Storage', 'Allowed file extensions'),
        ('enable_version_control', '1', 'boolean', 'Versioning', 'Enable automatic version control'),
        ('max_versions_per_document', '50', 'integer', 'Versioning', 'Maximum versions to retain per document'),
        ('require_approval_for_publish', '0', 'boolean', 'Workflow', 'Require approval before publishing'),
        ('default_visibility', 'Private', 'string', 'Security', 'Default document visibility'),
        ('enable_audit_logging', '1', 'boolean', 'Security', 'Enable detailed access logging'),
        ('signature_provider', 'electronic', 'string', 'Signature', 'Signature provider type'),
        ('signature_expiry_days', '30', 'integer', 'Signature', 'Signature request expiry in days'),
        ('require_sequential_signing', '1', 'boolean', 'Signature', 'Require sequential signing order'),
        ('document_code_prefix', 'DOC', 'string', 'Numbering', 'Document code prefix'),
        ('template_code_prefix', 'TPL', 'string', 'Numbering', 'Template code prefix'),
        ('signature_code_prefix', 'SIG', 'string', 'Numbering', 'Signature request code prefix'),
        ('auto_archive_on_expiry', '1', 'boolean', 'Retention', 'Auto-archive documents on expiry'),
        ('retention_check_days', '30', 'integer', 'Retention', 'Days before expiry to send reminders'),
    ]
    
    for key, value, stype, category, desc in default_settings:
        existing = db.execute("SELECT id FROM document_settings WHERE setting_key = ?", (key,)).fetchone()
        if not existing:
            db.execute("""
                INSERT INTO document_settings (setting_key, setting_value, setting_type, category, description)
                VALUES (?, ?, ?, ?, ?)
            """, (key, value, stype, category, desc))


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_document_code(db, prefix='DOC'):
    """Generate a unique document code."""
    today = datetime.now().strftime('%Y%m%d')
    # Get count for today
    result = db.execute("""
        SELECT COUNT(*) as cnt FROM documents 
        WHERE document_code LIKE ?
    """, (f'{prefix}-{today}%',)).fetchone()
    count = (result['cnt'] if result else 0) + 1
    return f"{prefix}-{today}-{count:04d}"


def generate_template_code(db, prefix='TPL'):
    """Generate a unique template code."""
    result = db.execute("""
        SELECT COUNT(*) as cnt FROM document_templates 
        WHERE template_code LIKE ?
    """, (f'{prefix}-%',)).fetchone()
    count = (result['cnt'] if result else 0) + 1
    return f"{prefix}-{count:04d}"


def generate_signature_code(db, prefix='SIG'):
    """Generate a unique signature request code."""
    today = datetime.now().strftime('%Y%m%d')
    result = db.execute("""
        SELECT COUNT(*) as cnt FROM signature_requests 
        WHERE request_code LIKE ?
    """, (f'{prefix}-{today}%',)).fetchone()
    count = (result['cnt'] if result else 0) + 1
    return f"{prefix}-{today}-{count:04d}"


def get_document_by_id(document_id):
    """Get a document by ID with full details."""
    db = get_db()
    try:
        doc = db.execute("""
            SELECT d.*, 
                   c.name as category_name,
                   u.username as owner_username,
                   cu.username as created_by_username,
                   au.username as approved_by_username
            FROM documents d
            LEFT JOIN document_categories c ON d.category_id = c.id
            LEFT JOIN users u ON d.owner_user_id = u.id
            LEFT JOIN users cu ON d.created_by_user_id = cu.id
            LEFT JOIN users au ON d.approved_by_user_id = au.id
            WHERE d.id = ?
        """, (document_id,)).fetchone()
        return dict(doc) if doc else None
    finally:
        db.close()


def get_document_versions(document_id):
    """Get all versions of a document."""
    db = get_db()
    try:
        versions = db.execute("""
            SELECT v.*, u.username as created_by_username
            FROM document_versions v
            LEFT JOIN users u ON v.created_by_user_id = u.id
            WHERE v.document_id = ?
            ORDER BY v.created_at DESC
        """, (document_id,)).fetchall()
        return [dict(v) for v in versions]
    finally:
        db.close()


def get_document_links(document_id):
    """Get all business record links for a document."""
    db = get_db()
    try:
        links = db.execute("""
            SELECT l.*, u.username as created_by_username
            FROM document_links l
            LEFT JOIN users u ON l.created_by_user_id = u.id
            WHERE l.document_id = ?
            ORDER BY l.is_primary DESC, l.created_at DESC
        """, (document_id,)).fetchall()
        return [dict(l) for l in links]
    finally:
        db.close()


def get_linked_documents(linked_module, linked_record_id):
    """Get all documents linked to a business record."""
    db = get_db()
    try:
        docs = db.execute("""
            SELECT d.*, l.link_type, l.is_primary as is_primary_link,
                   c.name as category_name
            FROM document_links l
            JOIN documents d ON l.document_id = d.id
            LEFT JOIN document_categories c ON d.category_id = c.id
            WHERE l.linked_module = ? AND l.linked_record_id = ?
            ORDER BY l.is_primary DESC, d.created_at DESC
        """, (linked_module, linked_record_id)).fetchall()
        return [dict(d) for d in docs]
    finally:
        db.close()


def get_signature_requests_for_document(document_id):
    """Get all signature requests for a document."""
    db = get_db()
    try:
        requests = db.execute("""
            SELECT sr.*, 
                   u.username as requestor_username,
                   (SELECT COUNT(*) FROM signature_participants WHERE request_id = sr.id) as participant_count,
                   (SELECT COUNT(*) FROM signature_participants WHERE request_id = sr.id AND status = 'Signed') as signed_count
            FROM signature_requests sr
            LEFT JOIN users u ON sr.requestor_user_id = u.id
            WHERE sr.document_id = ?
            ORDER BY sr.created_at DESC
        """, (document_id,)).fetchall()
        return [dict(r) for r in requests]
    finally:
        db.close()


def get_pending_signature_requests(user_id):
    """Get pending signature requests for a user."""
    db = get_db()
    try:
        requests = db.execute("""
            SELECT sr.*, 
                   d.title as document_title,
                   d.document_code,
                   u.username as requestor_username,
                   p.status as participant_status,
                   p.participant_name
            FROM signature_requests sr
            JOIN signature_participants p ON sr.id = p.request_id
            JOIN documents d ON sr.document_id = d.id
            LEFT JOIN users u ON sr.requestor_user_id = u.id
            WHERE p.user_id = ? AND p.status = 'Pending' AND sr.status = 'Pending'
            ORDER BY sr.due_date ASC, sr.created_at DESC
        """, (user_id,)).fetchall()
        return [dict(r) for r in requests]
    finally:
        db.close()


def log_document_access(document_id, user_id, action, access_type='View', 
                        ip_address=None, user_agent=None, session_id=None,
                        document_version_id=None):
    """Log a document access event."""
    db = get_db()
    try:
        db.execute("""
            INSERT INTO document_access_logs 
            (document_id, document_version_id, user_id, access_action, access_type,
             ip_address, user_agent, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (document_id, document_version_id, user_id, action, access_type,
              ip_address, user_agent, session_id))
        db.commit()
    finally:
        db.close()


def get_setting_value(key, default=None):
    """Get a document management setting value."""
    db = get_db()
    try:
        result = db.execute(
            "SELECT setting_value FROM document_settings WHERE setting_key = ? AND is_active = 1",
            (key,)
        ).fetchone()
        return result['setting_value'] if result else default
    finally:
        db.close()


def get_document_stats():
    """Get overall document management statistics."""
    db = get_db()
    try:
        stats = {
            'total_documents': 0,
            'total_versions': 0,
            'total_templates': 0,
            'pending_signatures': 0,
            'completed_signatures': 0,
            'archived_documents': 0,
            'by_status': {},
            'by_category': {},
        }
        
        result = db.execute("SELECT COUNT(*) as cnt FROM documents").fetchone()
        stats['total_documents'] = result['cnt'] if result else 0
        
        result = db.execute("SELECT COUNT(*) as cnt FROM document_versions").fetchone()
        stats['total_versions'] = result['cnt'] if result else 0
        
        result = db.execute("SELECT COUNT(*) as cnt FROM document_templates WHERE is_active = 1").fetchone()
        stats['total_templates'] = result['cnt'] if result else 0
        
        result = db.execute("""
            SELECT COUNT(*) as cnt FROM signature_participants 
            WHERE status = 'Pending' AND request_id IN 
            (SELECT id FROM signature_requests WHERE status = 'Pending')
        """).fetchone()
        stats['pending_signatures'] = result['cnt'] if result else 0
        
        result = db.execute("""
            SELECT COUNT(*) as cnt FROM signature_participants WHERE status = 'Signed'
        """).fetchone()
        stats['completed_signatures'] = result['cnt'] if result else 0
        
        result = db.execute("SELECT COUNT(*) as cnt FROM documents WHERE is_archived = 1").fetchone()
        stats['archived_documents'] = result['cnt'] if result else 0
        
        # Count by status
        rows = db.execute("""
            SELECT status, COUNT(*) as cnt FROM documents 
            WHERE status IS NOT NULL 
            GROUP BY status
        """).fetchall()
        stats['by_status'] = {r['status']: r['cnt'] for r in rows}
        
        # Count by category
        rows = db.execute("""
            SELECT c.name, COUNT(d.id) as cnt 
            FROM document_categories c
            LEFT JOIN documents d ON c.id = d.category_id
            GROUP BY c.id, c.name
        """).fetchall()
        stats['by_category'] = {r['name']: r['cnt'] for r in rows if r['name']}
        
        return stats
    finally:
        db.close()


# Initialize tables when module is imported
initialize_document_tables()
