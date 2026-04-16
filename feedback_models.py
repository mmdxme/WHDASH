"""
Feedback & Issue Reporting Models
==================================
Enterprise-grade feedback, bug report, and issue tracking system.

Models:
- FeedbackCategory: Categories and subcategories for reports
- FeedbackReport: Main feedback/bug report entries
- FeedbackAttachment: File attachments (images, videos, documents, audio)
- FeedbackComment: Internal and public comments
- FeedbackStatusHistory: Status change audit trail
- FeedbackAssignment: Assignment tracking
- FeedbackNotification: Notification preferences
- FeedbackTag: Tags/labels for reports
- FeedbackRelated: Related/duplicate report links

Features:
- Rich report types (Bug, UI Issue, Feature Request, Complaint, etc.)
- Status workflow (Draft → Submitted → ... → Closed)
- Priority/Severity/Impact/Urgency fields
- File attachments (images, videos, documents, audio)
- Voice recording support
- Internal comments and reporter-visible updates
- Full activity history
- Assignment to users/teams/departments
- Notifications and reminders
- RBAC permissions
- Multilingual support
"""

import os
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from database import get_db, get_db_context, get_one, get_all

# =============================================================================
# FEEDBACK REPORT TYPES
# =============================================================================

REPORT_TYPES = [
    ('bug', 'Bug Report'),
    ('ui_issue', 'UI/UX Issue'),
    ('performance', 'Performance Issue'),
    ('data_issue', 'Data Issue'),
    ('access_issue', 'Access/Permission Issue'),
    ('integration', 'Integration Issue'),
    ('system_error', 'System Error'),
    ('feature_request', 'Feature Request'),
    ('improvement', 'Improvement Suggestion'),
    ('general_feedback', 'General Feedback'),
    ('complaint', 'Complaint / Service Feedback'),
    ('urgent', 'Urgent Incident / Critical Problem'),
]

REPORT_TYPE_LABELS = {k: v for k, v in REPORT_TYPES}

# =============================================================================
# STATUS WORKFLOW
# =============================================================================

STATUS_DRAFT = 'Draft'
STATUS_SUBMITTED = 'Submitted'
STATUS_NEW = 'New'
STATUS_ACKNOWLEDGED = 'Acknowledged'
STATUS_UNDER_REVIEW = 'Under Review'
STATUS_ASSIGNED = 'Assigned'
STATUS_IN_PROGRESS = 'In Progress'
STATUS_WAITING_USER = 'Waiting for User'
STATUS_WAITING_INTERNAL = 'Waiting for Internal'
STATUS_RESOLVED = 'Resolved'
STATUS_VERIFIED = 'Verified'
STATUS_REOPENED = 'Reopened'
STATUS_CLOSED = 'Closed'
STATUS_REJECTED = 'Rejected'
STATUS_DUPLICATE = 'Duplicate'
STATUS_ESCALATED = 'Escalated'
STATUS_DEFERRED = 'Deferred'

STATUS_CHOICES = [
    STATUS_DRAFT, STATUS_SUBMITTED, STATUS_NEW, STATUS_ACKNOWLEDGED,
    STATUS_UNDER_REVIEW, STATUS_ASSIGNED, STATUS_IN_PROGRESS,
    STATUS_WAITING_USER, STATUS_WAITING_INTERNAL, STATUS_RESOLVED,
    STATUS_VERIFIED, STATUS_REOPENED, STATUS_CLOSED, STATUS_REJECTED,
    STATUS_DUPLICATE, STATUS_ESCALATED, STATUS_DEFERRED
]

# Status colors for UI
STATUS_COLORS = {
    STATUS_DRAFT: ('slate', 'bg-slate-500/10 text-slate-400 border-slate-500/20'),
    STATUS_SUBMITTED: ('sky', 'bg-sky-500/10 text-sky-400 border-sky-500/20'),
    STATUS_NEW: ('blue', 'bg-blue-500/10 text-blue-400 border-blue-500/20'),
    STATUS_ACKNOWLEDGED: ('indigo', 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'),
    STATUS_UNDER_REVIEW: ('violet', 'bg-violet-500/10 text-violet-400 border-violet-500/20'),
    STATUS_ASSIGNED: ('purple', 'bg-purple-500/10 text-purple-400 border-purple-500/20'),
    STATUS_IN_PROGRESS: ('amber', 'bg-amber-500/10 text-amber-400 border-amber-500/20'),
    STATUS_WAITING_USER: ('orange', 'bg-orange-500/10 text-orange-400 border-orange-500/20'),
    STATUS_WAITING_INTERNAL: ('cyan', 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'),
    STATUS_RESOLVED: ('teal', 'bg-teal-500/10 text-teal-400 border-teal-500/20'),
    STATUS_VERIFIED: ('emerald', 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'),
    STATUS_REOPENED: ('rose', 'bg-rose-500/10 text-rose-400 border-rose-500/20'),
    STATUS_CLOSED: ('gray', 'bg-gray-500/10 text-gray-400 border-gray-500/20'),
    STATUS_REJECTED: ('red', 'bg-red-500/10 text-red-400 border-red-500/20'),
    STATUS_DUPLICATE: ('zinc', 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'),
    STATUS_ESCALATED: ('red', 'bg-red-500/10 text-red-400 border-red-500/20'),
    STATUS_DEFERRED: ('neutral', 'bg-neutral-500/10 text-neutral-400 border-neutral-500/20'),
}

# =============================================================================
# PRIORITY / SEVERITY / IMPACT / URGENCY
# =============================================================================

PRIORITY_CHOICES = ['Low', 'Medium', 'High', 'Critical']
PRIORITY_COLORS = {
    'Low': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    'Medium': 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    'High': 'bg-orange-500/10 text-orange-400 border-orange-500/20',
    'Critical': 'bg-rose-500/10 text-rose-400 border-rose-500/20',
}

SEVERITY_CHOICES = ['Minor', 'Major', 'Critical', 'Blocking']
SEVERITY_COLORS = {
    'Minor': 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    'Major': 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    'Critical': 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    'Blocking': 'bg-red-600/10 text-red-400 border-red-600/20',
}

IMPACT_CHOICES = ['Low', 'Team', 'Department', 'Company-wide']
IMPACT_COLORS = {
    'Low': 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    'Team': 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    'Department': 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    'Company-wide': 'bg-rose-500/10 text-rose-400 border-rose-500/20',
}

URGENCY_CHOICES = ['Low', 'Normal', 'Urgent', 'Immediate']
URGENCY_COLORS = {
    'Low': 'bg-slate-500/10 text-slate-400 border-slate-500/20',
    'Normal': 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    'Urgent': 'bg-orange-500/10 text-orange-400 border-orange-500/20',
    'Immediate': 'bg-red-600/10 text-red-400 border-red-600/20',
}

# =============================================================================
# FREQUENCY
# =============================================================================

FREQUENCY_CHOICES = [
    ('once', 'Once'),
    ('sometimes', 'Sometimes'),
    ('often', 'Often'),
    ('always', 'Always'),
    ('unknown', 'Unknown'),
]

# =============================================================================
# VISIBILITY
# =============================================================================

VISIBILITY_CHOICES = [
    ('public', 'Public'),
    ('team', 'Team Only'),
    ('department', 'Department Only'),
    ('confidential', 'Confidential'),
]

# =============================================================================
# DEFAULT CATEGORIES
# =============================================================================

DEFAULT_CATEGORIES = [
    {'name': 'Bug', 'description': 'Software bugs and defects', 'icon': 'fa-bug', 'color': 'rose'},
    {'name': 'UI/UX', 'description': 'User interface and experience issues', 'icon': 'fa-desktop', 'color': 'violet'},
    {'name': 'Performance', 'description': 'Speed, loading, and performance issues', 'icon': 'fa-tachometer-alt', 'color': 'amber'},
    {'name': 'Data', 'description': 'Data accuracy, integrity, and quality issues', 'icon': 'fa-database', 'color': 'blue'},
    {'name': 'Access', 'description': 'Access control and permission issues', 'icon': 'fa-lock', 'color': 'red'},
    {'name': 'Integration', 'description': 'Third-party integrations and APIs', 'icon': 'fa-plug', 'color': 'purple'},
    {'name': 'System', 'description': 'System errors and crashes', 'icon': 'fa-server', 'color': 'slate'},
    {'name': 'Feature', 'description': 'Feature requests and suggestions', 'icon': 'fa-lightbulb', 'color': 'emerald'},
    {'name': 'Documentation', 'description': 'Documentation and help content', 'icon': 'fa-book', 'color': 'cyan'},
    {'name': 'Security', 'description': 'Security vulnerabilities and concerns', 'icon': 'fa-shield-alt', 'color': 'red'},
    {'name': 'Network', 'description': 'Network and connectivity issues', 'icon': 'fa-wifi', 'color': 'sky'},
    {'name': 'Mobile', 'description': 'Mobile app specific issues', 'icon': 'fa-mobile-alt', 'color': 'indigo'},
    {'name': 'API', 'description': 'API and developer issues', 'icon': 'fa-code', 'color': 'teal'},
    {'name': 'Complaint', 'description': 'Customer complaints and service issues', 'icon': 'fa-comment-dots', 'color': 'orange'},
    {'name': 'Other', 'description': 'Other issues and requests', 'icon': 'fa-ellipsis-h', 'color': 'gray'},
]

# =============================================================================
# MODEL INITIALIZATION
# =============================================================================

def init_feedback_tables():
    """Initialize all feedback-related database tables."""
    
    with get_db_context() as db:
        # Feedback categories table
        db.execute("""
            CREATE TABLE IF NOT EXISTS feedback_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                icon TEXT DEFAULT 'fa-tag',
                color TEXT DEFAULT 'blue',
                parent_id INTEGER,
                sort_order INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES feedback_categories(id)
            )
        """)
        
        # Main feedback reports table
        db.execute("""
            CREATE TABLE IF NOT EXISTS feedback_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reference_number TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                report_type TEXT NOT NULL,
                category_id INTEGER,
                subcategory_id INTEGER,
                
                -- Status and workflow
                status TEXT DEFAULT 'Draft',
                previous_status TEXT,
                status_changed_at TIMESTAMP,
                
                -- Priority and severity
                priority TEXT DEFAULT 'Medium',
                severity TEXT DEFAULT 'Minor',
                impact TEXT DEFAULT 'Low',
                urgency TEXT DEFAULT 'Normal',
                
                -- Description fields
                summary TEXT,
                description TEXT,
                expected_behavior TEXT,
                actual_behavior TEXT,
                steps_to_reproduce TEXT,
                
                -- Location information
                page_url TEXT,
                page_route TEXT,
                affected_module TEXT,
                affected_department TEXT,
                browser_info TEXT,
                device_info TEXT,
                operating_system TEXT,
                
                -- Occurrence
                occurrence_date TEXT,
                frequency TEXT DEFAULT 'unknown',
                
                -- Assignment
                assigned_to INTEGER,
                assigned_to_name TEXT,
                assigned_team TEXT,
                assigned_department TEXT,
                assigned_by INTEGER,
                assigned_at TIMESTAMP,
                
                -- Reporter
                reporter_user_id INTEGER,
                reporter_name TEXT,
                reporter_email TEXT,
                reporter_department TEXT,
                
                -- Visibility
                visibility TEXT DEFAULT 'public',
                is_confidential INTEGER DEFAULT 0,
                
                -- Related reports
                related_report_id INTEGER,
                is_duplicate INTEGER DEFAULT 0,
                duplicate_of_id INTEGER,
                
                -- Feedback specific
                satisfaction_rating INTEGER,
                resolution_notes TEXT,
                
                -- Tags as JSON array
                tags TEXT DEFAULT '[]',
                
                -- SLA
                sla_due_date TEXT,
                sla_breached INTEGER DEFAULT 0,
                
                -- Counts
                comment_count INTEGER DEFAULT 0,
                attachment_count INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                
                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                submitted_at TIMESTAMP,
                resolved_at TIMESTAMP,
                closed_at TIMESTAMP,
                
                -- Soft delete
                is_deleted INTEGER DEFAULT 0,
                deleted_at TIMESTAMP,
                
                -- Metadata
                metadata TEXT DEFAULT '{}',
                
                FOREIGN KEY (category_id) REFERENCES feedback_categories(id),
                FOREIGN KEY (assigned_to) REFERENCES users(id),
                FOREIGN KEY (reporter_user_id) REFERENCES users(id),
                FOREIGN KEY (duplicate_of_id) REFERENCES feedback_reports(id)
            )
        """)
        
        # Attachments table
        db.execute("""
            CREATE TABLE IF NOT EXISTS feedback_attachments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                file_name TEXT NOT NULL,
                file_path TEXT NOT NULL,
                file_type TEXT,
                file_size INTEGER,
                mime_type TEXT,
                thumbnail_path TEXT,
                
                -- For audio/voice recordings
                duration_seconds INTEGER,
                
                -- For images/screenshots
                width INTEGER,
                height INTEGER,
                
                -- Description and attribution
                description TEXT,
                uploaded_by INTEGER,
                uploaded_by_name TEXT,
                
                -- Visibility
                is_internal INTEGER DEFAULT 0,
                
                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (report_id) REFERENCES feedback_reports(id),
                FOREIGN KEY (uploaded_by) REFERENCES users(id)
            )
        """)
        
        # Comments table
        db.execute("""
            CREATE TABLE IF NOT EXISTS feedback_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                author_user_id INTEGER,
                author_name TEXT NOT NULL,
                author_role TEXT,
                content TEXT NOT NULL,
                content_html TEXT,
                
                -- Visibility
                is_internal INTEGER DEFAULT 0,
                is_system INTEGER DEFAULT 0,
                
                -- Edit tracking
                is_edited INTEGER DEFAULT 0,
                edited_at TIMESTAMP,
                
                -- Reference
                parent_comment_id INTEGER,
                
                -- Timestamps
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (report_id) REFERENCES feedback_reports(id),
                FOREIGN KEY (author_user_id) REFERENCES users(id),
                FOREIGN KEY (parent_comment_id) REFERENCES feedback_comments(id)
            )
        """)
        
        # Status history table
        db.execute("""
            CREATE TABLE IF NOT EXISTS feedback_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                from_status TEXT,
                to_status TEXT NOT NULL,
                changed_by_user_id INTEGER,
                changed_by_name TEXT,
                change_reason TEXT,
                is_automatic INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (report_id) REFERENCES feedback_reports(id),
                FOREIGN KEY (changed_by_user_id) REFERENCES users(id)
            )
        """)
        
        # Assignment history table
        db.execute("""
            CREATE TABLE IF NOT EXISTS feedback_assignment_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                from_assignee_id INTEGER,
                from_assignee_name TEXT,
                to_assignee_id INTEGER,
                to_assignee_name TEXT,
                to_team TEXT,
                to_department TEXT,
                assigned_by_user_id INTEGER,
                assigned_by_name TEXT,
                assignment_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (report_id) REFERENCES feedback_reports(id),
                FOREIGN KEY (from_assignee_id) REFERENCES users(id),
                FOREIGN KEY (to_assignee_id) REFERENCES users(id),
                FOREIGN KEY (assigned_by_user_id) REFERENCES users(id)
            )
        """)
        
        # Activity history / audit log
        db.execute("""
            CREATE TABLE IF NOT EXISTS feedback_activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                actor_user_id INTEGER,
                actor_name TEXT,
                details TEXT,
                metadata TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (report_id) REFERENCES feedback_reports(id),
                FOREIGN KEY (actor_user_id) REFERENCES users(id)
            )
        """)
        
        # Tags table
        db.execute("""
            CREATE TABLE IF NOT EXISTS feedback_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                color TEXT DEFAULT 'blue',
                description TEXT,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Report-tag relationship
        db.execute("""
            CREATE TABLE IF NOT EXISTS feedback_report_tags (
                report_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (report_id, tag_id),
                FOREIGN KEY (report_id) REFERENCES feedback_reports(id),
                FOREIGN KEY (tag_id) REFERENCES feedback_tags(id)
            )
        """)
        
        # Notification preferences
        db.execute("""
            CREATE TABLE IF NOT EXISTS feedback_notification_prefs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                notify_on_submission INTEGER DEFAULT 1,
                notify_on_assignment INTEGER DEFAULT 1,
                notify_on_status_change INTEGER DEFAULT 1,
                notify_on_comment INTEGER DEFAULT 1,
                notify_on_resolution INTEGER DEFAULT 1,
                notify_on_reopen INTEGER DEFAULT 1,
                notify_sla_breach INTEGER DEFAULT 1,
                email_enabled INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # Settings table
        db.execute("""
            CREATE TABLE IF NOT EXISTS feedback_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT NOT NULL UNIQUE,
                setting_value TEXT,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes
        db.execute("CREATE INDEX IF NOT EXISTS idx_feedback_reports_status ON feedback_reports(status)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_feedback_reports_type ON feedback_reports(report_type)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_feedback_reports_priority ON feedback_reports(priority)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_feedback_reports_reporter ON feedback_reports(reporter_user_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_feedback_reports_assignee ON feedback_reports(assigned_to)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_feedback_reports_category ON feedback_reports(category_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_feedback_reports_created ON feedback_reports(created_at)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_feedback_comments_report ON feedback_comments(report_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_feedback_attachments_report ON feedback_attachments(report_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_feedback_activity_report ON feedback_activity_log(report_id)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_feedback_status_history_report ON feedback_status_history(report_id)")
        
        db.commit()
    
    # Seed default categories if empty
    _seed_categories()
    _seed_default_settings()


def _seed_categories():
    """Seed default categories if none exist."""
    with get_db_context() as db:
        existing = db.execute("SELECT COUNT(*) as cnt FROM feedback_categories").fetchone()
        if existing and existing['cnt'] > 0:
            return
        
        for i, cat in enumerate(DEFAULT_CATEGORIES):
            db.execute("""
                INSERT OR IGNORE INTO feedback_categories (name, description, icon, color, sort_order)
                VALUES (?, ?, ?, ?, ?)
            """, (cat['name'], cat['description'], cat['icon'], cat['color'], i))


def _seed_default_settings():
    """Seed default settings."""
    defaults = [
        ('feedback_reference_prefix', 'FB', 'Reference number prefix'),
        ('feedback_reference_sequence', '1000', 'Last reference number'),
        ('feedback_allow_anonymous', '0', 'Allow anonymous submissions'),
        ('feedback_require_login', '1', 'Require login for submissions'),
        ('feedback_max_attachments', '10', 'Maximum attachments per report'),
        ('feedback_max_file_size_mb', '50', 'Maximum file size in MB'),
        ('feedback_allowed_extensions', 'pdf,doc,docx,xls,xlsx,png,jpg,jpeg,gif,txt,csv,zip,rar,mp4,mov,mp3,wav,ogg,webm', 'Allowed file extensions'),
        ('feedback_default_priority', 'Medium', 'Default priority for new reports'),
        ('feedback_notification_email', '', 'Email for notifications'),
        ('feedback_sla_enabled', '1', 'Enable SLA tracking'),
        ('feedback_auto_assign_enabled', '0', 'Enable auto-assignment'),
        ('feedback_require_evidence', '0', 'Require evidence/attachments'),
        ('feedback_allow_voice', '1', 'Allow voice recordings'),
        ('feedback_allow_screenshot', '1', 'Allow screenshot uploads'),
        ('feedback_retention_days', '365', 'Data retention period in days'),
    ]
    
    with get_db_context() as db:
        for key, value, desc in defaults:
            db.execute("""
                INSERT OR IGNORE INTO feedback_settings (setting_key, setting_value, description)
                VALUES (?, ?, ?)
            """, (key, value, desc))


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_reference_number():
    """Generate a unique reference number for a feedback report."""
    setting_key = 'feedback_reference_sequence'
    current = get_platform_setting(setting_key, '1000')
    new_num = int(current) + 1
    
    # Update sequence
    set_platform_setting(setting_key, str(new_num))
    
    prefix = get_platform_setting('feedback_reference_prefix', 'FB')
    return f"{prefix}-{new_num:06d}"


def get_platform_setting(key, default=None):
    """Get a platform setting value."""
    row = get_one("SELECT setting_value FROM feedback_settings WHERE setting_key = ?", (key,))
    return row['setting_value'] if row else default


def set_platform_setting(key, value):
    """Set a platform setting value."""
    db = get_db()
    db.execute("""
        INSERT INTO feedback_settings (setting_key, setting_value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(setting_key) DO UPDATE SET setting_value = ?, updated_at = CURRENT_TIMESTAMP
    """, (key, value, value))
    db.commit()


def get_categories():
    """Get all active categories."""
    rows = get_all("""
        SELECT c.*, p.name as parent_name 
        FROM feedback_categories c
        LEFT JOIN feedback_categories p ON c.parent_id = p.id
        WHERE c.is_active = 1
        ORDER BY c.sort_order, c.name
    """)
    return [dict(row) for row in rows] if rows else []


def get_category_by_name(name):
    """Get a category by name."""
    row = get_one("SELECT * FROM feedback_categories WHERE name = ? AND is_active = 1", (name,))
    return dict(row) if row else None


def get_reports(filters=None, page=1, per_page=50, order_by='created_at DESC'):
    """
    Get feedback reports with filtering and pagination.
    
    filters: dict with keys like status, type, priority, category, 
             assignee, reporter, search, date_from, date_to
    """
    filters = filters or {}
    
    # Handle deprecated 'id' filter - map to report.id
    if 'id' in filters:
        filters['report_id'] = filters['id']
        del filters['id']
    
    conditions = ["fr.is_deleted = 0"]
    params = []
    
    if filters.get('report_id'):
        conditions.append("fr.id = ?")
        params.append(filters['report_id'])
    
    if filters.get('status'):
        statuses = filters['status'] if isinstance(filters['status'], list) else [filters['status']]
        placeholders = ','.join(['?' for _ in statuses])
        conditions.append(f"fr.status IN ({placeholders})")
        params.extend(statuses)
    
    if filters.get('type') or filters.get('report_type'):
        types = filters.get('type') or filters.get('report_type')
        types = types if isinstance(types, list) else [types]
        placeholders = ','.join(['?' for _ in types])
        conditions.append(f"fr.report_type IN ({placeholders})")
        params.extend(types)
    
    if filters.get('priority'):
        priorities = filters['priority'] if isinstance(filters['priority'], list) else [filters['priority']]
        placeholders = ','.join(['?' for _ in priorities])
        conditions.append(f"fr.priority IN ({placeholders})")
        params.extend(priorities)
    
    if filters.get('severity'):
        severities = filters['severity'] if isinstance(filters['severity'], list) else [filters['severity']]
        placeholders = ','.join(['?' for _ in severities])
        conditions.append(f"fr.severity IN ({placeholders})")
        params.extend(severities)
    
    if filters.get('category'):
        conditions.append("fr.category_id = ?")
        params.append(filters['category'])
    
    if filters.get('assigned_to'):
        conditions.append("fr.assigned_to = ?")
        params.append(filters['assigned_to'])
    
    if filters.get('reporter'):
        conditions.append("fr.reporter_user_id = ?")
        params.append(filters['reporter'])
    
    if filters.get('assigned_team'):
        conditions.append("fr.assigned_team = ?")
        params.append(filters['assigned_team'])
    
    if filters.get('assigned_department'):
        conditions.append("fr.assigned_department = ?")
        params.append(filters['assigned_department'])
    
    if filters.get('visibility'):
        conditions.append("fr.visibility = ?")
        params.append(filters['visibility'])
    
    if filters.get('is_confidential') is not None:
        conditions.append("fr.is_confidential = ?")
        params.append(1 if filters['is_confidential'] else 0)
    
    if filters.get('search'):
        search_term = f"%{filters['search']}%"
        conditions.append("(fr.title LIKE ? OR fr.summary LIKE ? OR fr.description LIKE ? OR fr.reference_number LIKE ?)")
        params.extend([search_term, search_term, search_term, search_term])
    
    if filters.get('date_from'):
        conditions.append("fr.created_at >= ?")
        params.append(filters['date_from'])
    
    if filters.get('date_to'):
        conditions.append("fr.created_at <= ?")
        params.append(filters['date_to'])
    
    # Build query
    where_clause = ' AND '.join(conditions) if conditions else '1=1'
    
    # Get total count
    count_query = f"SELECT COUNT(*) as total FROM feedback_reports fr WHERE {where_clause}"
    total = get_one(count_query, tuple(params))
    total_count = total['total'] if total else 0
    
    # Get paginated results
    offset = (page - 1) * per_page
    query = f"""
        SELECT fr.*, 
               fc.name as category_name, fc.icon as category_icon, fc.color as category_color,
               u.username as assigned_username, u.display_name as assigned_display_name
        FROM feedback_reports fr
        LEFT JOIN feedback_categories fc ON fr.category_id = fc.id
        LEFT JOIN users u ON fr.assigned_to = u.id
        WHERE {where_clause}
        ORDER BY fr.{order_by}
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])
    
    rows = get_all(query, tuple(params))
    reports = [dict(row) for row in rows] if rows else []
    
    return {
        'reports': reports,
        'total': total_count,
        'page': page,
        'per_page': per_page,
        'pages': (total_count + per_page - 1) // per_page if per_page > 0 else 0
    }


def get_report_by_id(report_id):
    """Get a single report by ID with full details."""
    row = get_one("""
        SELECT fr.*,
               fc.name as category_name, fc.icon as category_icon, fc.color as category_color,
               u.username as assigned_username,
               reporter.username as reporter_username,
               reporter.email as reporter_email_addr
        FROM feedback_reports fr
        LEFT JOIN feedback_categories fc ON fr.category_id = fc.id
        LEFT JOIN users u ON fr.assigned_to = u.id
        LEFT JOIN users reporter ON fr.reporter_user_id = reporter.id
        WHERE fr.id = ? AND fr.is_deleted = 0
    """, (report_id,))
    
    if not row:
        return None
    
    report = dict(row)
    
    # Parse tags JSON
    if report.get('tags'):
        try:
            import json
            report['tags_list'] = json.loads(report['tags'])
        except:
            report['tags_list'] = []
    else:
        report['tags_list'] = []
    
    # Parse metadata JSON
    if report.get('metadata'):
        try:
            import json
            report['metadata_dict'] = json.loads(report['metadata'])
        except:
            report['metadata_dict'] = {}
    else:
        report['metadata_dict'] = {}
    
    # Increment view count
    with get_db_context() as db:
        db.execute("UPDATE feedback_reports SET view_count = view_count + 1 WHERE id = ?", (report_id,))
    
    return report


def get_report_attachments(report_id):
    """Get all attachments for a report."""
    rows = get_all("""
        SELECT fa.*, u.username as uploader_username
        FROM feedback_attachments fa
        LEFT JOIN users u ON fa.uploaded_by = u.id
        WHERE fa.report_id = ?
        ORDER BY fa.created_at
    """, (report_id,))
    return [dict(row) for row in rows] if rows else []


def get_report_comments(report_id, include_internal=False):
    """Get all comments for a report."""
    query = """
        SELECT fc.*, u.username as author_username, u.display_name as author_display_name
        FROM feedback_comments fc
        LEFT JOIN users u ON fc.author_user_id = u.id
        WHERE fc.report_id = ?
    """
    if not include_internal:
        query += " AND fc.is_internal = 0"
    query += " ORDER BY fc.created_at ASC"
    
    rows = get_all(query, (report_id,))
    return [dict(row) for row in rows] if rows else []


def get_report_activity(report_id):
    """Get activity log for a report."""
    rows = get_all("""
        SELECT fal.*, u.username as actor_username
        FROM feedback_activity_log fal
        LEFT JOIN users u ON fal.actor_user_id = u.id
        WHERE fal.report_id = ?
        ORDER BY fal.created_at DESC
    """, (report_id,))
    return [dict(row) for row in rows] if rows else []


def get_report_status_history(report_id):
    """Get status history for a report."""
    rows = get_all("""
        SELECT fsh.*, u.username as changer_username
        FROM feedback_status_history fsh
        LEFT JOIN users u ON fsh.changed_by_user_id = u.id
        WHERE fsh.report_id = ?
        ORDER BY fsh.created_at ASC
    """, (report_id,))
    return [dict(row) for row in rows] if rows else []


def create_report(data, user_id=None):
    """Create a new feedback report."""
    import json
    
    reference_number = generate_reference_number()
    now = datetime.now().isoformat()
    
    # Parse tags
    tags = data.get('tags', [])
    if isinstance(tags, list):
        tags = json.dumps(tags)
    
    # Parse metadata
    metadata = data.get('metadata', {})
    if isinstance(metadata, dict):
        metadata = json.dumps(metadata)
    
    db = get_db()
    cursor = db.execute("""
        INSERT INTO feedback_reports (
            reference_number, title, report_type, category_id, subcategory_id,
            status, summary, description, expected_behavior, actual_behavior,
            steps_to_reproduce, page_url, page_route, affected_module, affected_department,
            browser_info, device_info, operating_system, occurrence_date, frequency,
            priority, severity, impact, urgency, visibility, is_confidential,
            reporter_user_id, reporter_name, reporter_email, reporter_department,
            tags, metadata, sla_due_date, created_at, submitted_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        reference_number,
        data.get('title', ''),
        data.get('report_type', 'bug'),
        data.get('category_id'),
        data.get('subcategory_id'),
        data.get('status', STATUS_DRAFT),
        data.get('summary', ''),
        data.get('description', ''),
        data.get('expected_behavior', ''),
        data.get('actual_behavior', ''),
        data.get('steps_to_reproduce', ''),
        data.get('page_url', ''),
        data.get('page_route', ''),
        data.get('affected_module', ''),
        data.get('affected_department', ''),
        data.get('browser_info', ''),
        data.get('device_info', ''),
        data.get('operating_system', ''),
        data.get('occurrence_date', ''),
        data.get('frequency', 'unknown'),
        data.get('priority', 'Medium'),
        data.get('severity', 'Minor'),
        data.get('impact', 'Low'),
        data.get('urgency', 'Normal'),
        data.get('visibility', 'public'),
        1 if data.get('is_confidential') else 0,
        user_id,
        data.get('reporter_name', ''),
        data.get('reporter_email', ''),
        data.get('reporter_department', ''),
        tags,
        metadata,
        data.get('sla_due_date', ''),
        now,
        now if data.get('submit_now') else None
    ))
    
    report_id = cursor.lastrowid
    db.commit()
    
    # Log activity
    log_activity(report_id, 'created', user_id, data.get('reporter_name', 'Anonymous'),
                 f"Report created: {reference_number}")
    
    # Create initial status history
    if data.get('submit_now'):
        db.execute("""
            INSERT INTO feedback_status_history (report_id, from_status, to_status, changed_by_user_id, changed_by_name, is_automatic)
            VALUES (?, NULL, ?, ?, ?, 1)
        """, (report_id, STATUS_SUBMITTED, user_id, data.get('reporter_name', 'Anonymous')))
        db.commit()
    
    return report_id


def update_report(report_id, data, user_id=None, user_name='Unknown'):
    """Update an existing feedback report."""
    import json
    
    # Get current report
    current = get_report_by_id(report_id)
    if not current:
        return False
    
    # Build update query dynamically
    allowed_fields = [
        'title', 'report_type', 'category_id', 'subcategory_id',
        'summary', 'description', 'expected_behavior', 'actual_behavior',
        'steps_to_reproduce', 'page_url', 'page_route', 'affected_module',
        'affected_department', 'browser_info', 'device_info', 'operating_system',
        'occurrence_date', 'frequency', 'priority', 'severity', 'impact', 'urgency',
        'visibility', 'is_confidential', 'tags', 'metadata', 'sla_due_date',
        'resolution_notes', 'satisfaction_rating'
    ]
    
    updates = []
    params = []
    
    for field in allowed_fields:
        if field in data:
            value = data[field]
            if field in ('tags', 'metadata') and isinstance(value, (list, dict)):
                value = json.dumps(value)
            if field == 'is_confidential':
                value = 1 if value else 0
            updates.append(f"{field} = ?")
            params.append(value)
    
    updates.append("updated_at = ?")
    params.append(datetime.now().isoformat())
    params.append(report_id)
    
    db = get_db()
    db.execute(f"UPDATE feedback_reports SET {', '.join(updates)} WHERE id = ?", tuple(params))
    db.commit()
    
    # Log activity
    log_activity(report_id, 'updated', user_id, user_name, "Report updated")
    
    return True


def change_status(report_id, new_status, user_id=None, user_name='Unknown', reason=''):
    """Change the status of a report with history tracking."""
    current = get_report_by_id(report_id)
    if not current:
        return False
    
    old_status = current['status']
    
    now = datetime.now().isoformat()
    
    db = get_db()
    
    # Update status
    db.execute("""
        UPDATE feedback_reports 
        SET status = ?, previous_status = ?, status_changed_at = ?, updated_at = ?,
            resolved_at = CASE WHEN ? = 'Resolved' THEN ? ELSE resolved_at END,
            closed_at = CASE WHEN ? = 'Closed' THEN ? ELSE closed_at END
        WHERE id = ?
    """, (new_status, old_status, now, now, new_status, now, new_status, now, report_id))
    
    # Log status change
    db.execute("""
        INSERT INTO feedback_status_history (report_id, from_status, to_status, changed_by_user_id, changed_by_name, change_reason, is_automatic)
        VALUES (?, ?, ?, ?, ?, ?, 0)
    """, (report_id, old_status, new_status, user_id, user_name, reason))
    
    # Log activity
    db.execute("""
        INSERT INTO feedback_activity_log (report_id, activity_type, actor_user_id, actor_name, details)
        VALUES (?, 'status_changed', ?, ?, ?)
    """, (report_id, user_id, user_name, f"Status changed from {old_status} to {new_status}"))
    
    db.commit()
    
    return True


def assign_report(report_id, assignee_id, assignee_name, team=None, department=None,
                  assigned_by_id=None, assigned_by_name='Unknown', reason=''):
    """Assign a report to a user or team."""
    with get_db_context() as db:
        # Get current assignment info
        current = db.execute(
            "SELECT assigned_to, assigned_to_name FROM feedback_reports WHERE id = ?",
            (report_id,)
        ).fetchone()
        
        if not current:
            return False
        
        now = datetime.now().isoformat()
        
        # Update assignment
        db.execute("""
            UPDATE feedback_reports
            SET assigned_to = ?, assigned_to_name = ?, assigned_team = ?, assigned_department = ?,
                assigned_by = ?, assigned_at = ?, updated_at = ?
            WHERE id = ?
        """, (assignee_id, assignee_name, team, department, assigned_by_id, now, now, report_id))
        
        # Log assignment history
        db.execute("""
            INSERT INTO feedback_assignment_history
            (report_id, from_assignee_id, from_assignee_name, to_assignee_id, to_assignee_name,
             to_team, to_department, assigned_by_user_id, assigned_by_name, assignment_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (report_id, current['assigned_to'], current['assigned_to_name'],
              assignee_id, assignee_name, team, department, assigned_by_id, assigned_by_name, reason))
        
        # Log activity
        db.execute("""
            INSERT INTO feedback_activity_log (report_id, activity_type, actor_user_id, actor_name, details)
            VALUES (?, 'assigned', ?, ?, ?)
        """, (report_id, assigned_by_id, assigned_by_name,
              f"Assigned to {assignee_name}" + (f" ({team})" if team else "")))
    
    db.commit()
    
    return True


def add_comment(report_id, content, user_id=None, user_name='Anonymous', 
                is_internal=False, is_system=False):
    """Add a comment to a report."""
    db = get_db()
    cursor = db.execute("""
        INSERT INTO feedback_comments 
        (report_id, author_user_id, author_name, content, is_internal, is_system)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (report_id, user_id, user_name, content, 1 if is_internal else 0, 1 if is_system else 0))
    
    # Update comment count
    db.execute("UPDATE feedback_reports SET comment_count = comment_count + 1 WHERE id = ?", (report_id,))
    
    # Log activity
    db.execute("""
        INSERT INTO feedback_activity_log (report_id, activity_type, actor_user_id, actor_name, details)
        VALUES (?, 'comment_added', ?, ?, ?)
    """, (report_id, user_id, user_name, "Comment added" if not is_internal else "Internal note added"))
    
    db.commit()
    return cursor.lastrowid


def add_attachment(report_id, file_data, user_id=None, user_name='Anonymous'):
    """Add an attachment to a report."""
    db = get_db()
    cursor = db.execute("""
        INSERT INTO feedback_attachments 
        (report_id, file_name, file_path, file_type, file_size, mime_type,
         thumbnail_path, duration_seconds, width, height, uploaded_by, uploaded_by_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        report_id,
        file_data.get('file_name'),
        file_data.get('file_path'),
        file_data.get('file_type'),
        file_data.get('file_size'),
        file_data.get('mime_type'),
        file_data.get('thumbnail_path'),
        file_data.get('duration_seconds'),
        file_data.get('width'),
        file_data.get('height'),
        user_id,
        user_name
    ))
    
    # Update attachment count
    db.execute("UPDATE feedback_reports SET attachment_count = attachment_count + 1 WHERE id = ?", (report_id,))
    
    db.commit()
    return cursor.lastrowid


def log_activity(report_id, activity_type, user_id=None, user_name='Unknown', details=''):
    """Log an activity for a report."""
    db = get_db()
    db.execute("""
        INSERT INTO feedback_activity_log (report_id, activity_type, actor_user_id, actor_name, details)
        VALUES (?, ?, ?, ?, ?)
    """, (report_id, activity_type, user_id, user_name, details))
    db.commit()


def delete_report(report_id, user_id=None, user_name='Unknown'):
    """Soft delete a report."""
    db = get_db()
    db.execute("""
        UPDATE feedback_reports 
        SET is_deleted = 1, deleted_at = ?, updated_at = ?
        WHERE id = ?
    """, (datetime.now().isoformat(), datetime.now().isoformat(), report_id))
    
    db.execute("""
        INSERT INTO feedback_activity_log (report_id, activity_type, actor_user_id, actor_name, details)
        VALUES (?, 'deleted', ?, ?, ?)
    """, (report_id, user_id, user_name, "Report deleted"))
    
    db.commit()


def get_stats(filters=None):
    """Get aggregated statistics for reports."""
    filters = filters or {}
    
    base_query = "SELECT * FROM feedback_reports WHERE is_deleted = 0"
    params = []
    
    if filters.get('date_from'):
        base_query += " AND created_at >= ?"
        params.append(filters['date_from'])
    if filters.get('date_to'):
        base_query += " AND created_at <= ?"
        params.append(filters['date_to'])
    if filters.get('category'):
        base_query += " AND category_id = ?"
        params.append(filters['category'])
    
    reports = get_all(base_query, tuple(params))
    reports_list = [dict(r) for r in reports] if reports else []
    
    total = len(reports_list)
    
    from collections import Counter
    
    status_counts = Counter(r.get('status', 'Unknown') for r in reports_list)
    type_counts = Counter(r.get('report_type', 'unknown') for r in reports_list)
    priority_counts = Counter(r.get('priority', 'Medium') for r in reports_list)
    severity_counts = Counter(r.get('severity', 'Minor') for r in reports_list)
    
    # Calculate averages
    avg_resolution_hours = 0
    resolved_count = 0
    total_resolution_hours = 0
    
    for r in reports_list:
        if r.get('resolved_at') and r.get('created_at'):
            try:
                created = datetime.fromisoformat(r['created_at'])
                resolved = datetime.fromisoformat(r['resolved_at'])
                hours = (resolved - created).total_seconds() / 3600
                total_resolution_hours += hours
                resolved_count += 1
            except:
                pass
    
    if resolved_count > 0:
        avg_resolution_hours = total_resolution_hours / resolved_count
    
    # Count by assignee
    assignee_counts = {}
    for r in reports_list:
        assignee = r.get('assigned_to_name') or r.get('assigned_username') or 'Unassigned'
        assignee_counts[assignee] = assignee_counts.get(assignee, 0) + 1
    
    # Count by category
    category_counts = {}
    for r in reports_list:
        cat = r.get('category_name') or 'Uncategorized'
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    # Overdue/SLA
    overdue = sum(1 for r in reports_list 
                  if r.get('sla_due_date') and r.get('status') not in (STATUS_CLOSED, STATUS_RESOLVED)
                  and r.get('sla_due_date') < datetime.now().strftime('%Y-%m-%d'))
    
    # Open reports
    open_statuses = [STATUS_NEW, STATUS_ACKNOWLEDGED, STATUS_UNDER_REVIEW, STATUS_ASSIGNED, 
                     STATUS_IN_PROGRESS, STATUS_WAITING_USER, STATUS_WAITING_INTERNAL,
                     STATUS_SUBMITTED, STATUS_REOPENED, STATUS_ESCALATED]
    open_count = sum(1 for r in reports_list if r.get('status') in open_statuses)
    
    return {
        'total': total,
        'open': open_count,
        'resolved': status_counts.get(STATUS_RESOLVED, 0),
        'closed': status_counts.get(STATUS_CLOSED, 0),
        'pending': status_counts.get(STATUS_WAITING_USER, 0) + status_counts.get(STATUS_WAITING_INTERNAL, 0),
        'overdue': overdue,
        'by_status': dict(status_counts),
        'by_type': dict(type_counts),
        'by_priority': dict(priority_counts),
        'by_severity': dict(severity_counts),
        'by_assignee': assignee_counts,
        'by_category': category_counts,
        'avg_resolution_hours': round(avg_resolution_hours, 1),
        'resolved_count': resolved_count,
    }


def search_reports(query, filters=None, limit=50):
    """Search reports by text query."""
    filters = filters or {}
    
    search_term = f"%{query}%"
    conditions = ["fr.is_deleted = 0 AND (fr.title LIKE ? OR fr.summary LIKE ? OR fr.description LIKE ? OR fr.reference_number LIKE ?)"]
    params = [search_term, search_term, search_term, search_term]
    
    if filters.get('status'):
        conditions.append("fr.status = ?")
        params.append(filters['status'])
    if filters.get('priority'):
        conditions.append("fr.priority = ?")
        params.append(filters['priority'])
    
    where_clause = ' AND '.join(conditions)
    
    rows = get_all(f"""
        SELECT fr.*, fc.name as category_name,
               u.username as assigned_username, u.display_name as assigned_display_name
        FROM feedback_reports fr
        LEFT JOIN feedback_categories fc ON fr.category_id = fc.id
        LEFT JOIN users u ON fr.assigned_to = u.id
        WHERE {where_clause}
        ORDER BY fr.created_at DESC
        LIMIT ?
    """, tuple(params + [limit]))
    
    return [dict(row) for row in rows] if rows else []
