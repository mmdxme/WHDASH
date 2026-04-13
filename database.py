"""
Shared Database Connection Module
================================
Centralized database connection management for the unified MMDx platform.
This module provides a single source of truth for all database connections,
ensuring consistent connection settings, transaction management, and cursor factory.

KEY PRINCIPLES:
- Single source of truth for database connections
- Consistent PRAGMA settings across all connections
- Centralized transaction management
- Support for multiple database files if needed
- Connection pooling readiness

Usage:
    from database import get_db, get_dashboard_stats
    
    # Standard read operation
    db = get_db()
    users = db.execute("SELECT * FROM users").fetchall()
    db.close()
    
    # Using context manager (preferred)
    with get_db() as db:
        db.execute("INSERT INTO users (...) VALUES (...)", ...)
        db.commit()
"""

import sqlite3
import os
from contextlib import contextmanager
from functools import wraps

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'warehouse.db'))

# Ensure database directory exists
_db_dir = os.path.dirname(DATABASE_PATH)
if _db_dir:
    os.makedirs(_db_dir, exist_ok=True)


# ============================================================================
# PRAGMA SETTINGS
# ============================================================================

# Connection PRAGMAs applied to every new connection for consistency and performance
STANDARD_PRAGMAS = [
    ("PRAGMA journal_mode=WAL", "Write-Ahead Logging for better concurrency"),
    ("PRAGMA synchronous=NORMAL", "Balanced durability/performance"),
    ("PRAGMA cache_size=10000", "10K pages cache (~40MB)"),
    ("PRAGMA temp_store=MEMORY", "Temp tables in memory"),
    ("PRAGMA foreign_keys=ON", "Enforce foreign key constraints"),
    ("PRAGMA busy_timeout=5000", "5 second busy wait"),
]


# ============================================================================
# CORE DATABASE CONNECTION FACTORY
# ============================================================================

def get_db():
    """
    Get a database connection with standardized settings.
    
    Returns:
        sqlite3.Connection: A SQLite connection with Row factory and optimized PRAGMAs.
    
    Example:
        db = get_db()
        try:
            result = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            return dict(result) if result else None
        finally:
            db.close()
    
    Note:
        Always close the connection when done, or use the context manager:
        `with get_db() as db: ...`
    """
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    
    # Apply all standard PRAGMAs
    for pragma_sql, _ in STANDARD_PRAGMAS:
        conn.execute(pragma_sql)
    
    return conn


@contextmanager
def get_db_context():
    """
    Context manager for database operations.
    Automatically handles connection close, even on exceptions.
    
    Usage:
        with get_db_context() as db:
            db.execute("INSERT INTO ... VALUES (?)", (value,))
            db.commit()
    """
    db = get_db()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ============================================================================
# TRANSACTION HELPERS
# ============================================================================

def execute_with_retry(sql, params=None, max_retries=3):
    """
    Execute a SQL statement with automatic retry on database lock.
    
    Args:
        sql: SQL statement to execute
        params: Parameters for the SQL statement
        max_retries: Maximum retry attempts on lock error
    
    Returns:
        sqlite3.Cursor object
    """
    for attempt in range(max_retries):
        try:
            db = get_db()
            try:
                if params:
                    result = db.execute(sql, params)
                else:
                    result = db.execute(sql)
                db.commit()
                return result
            finally:
                db.close()
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < max_retries - 1:
                import time
                time.sleep(0.1 * (attempt + 1))
                continue
            raise


# ============================================================================
# DICTIONARY HELPERS
# ============================================================================

def row_to_dict(row):
    """Convert a sqlite3.Row to a regular dictionary."""
    return dict(row) if row else None


def rows_to_list(rows):
    """Convert a list of sqlite3.Row objects to a list of dictionaries."""
    return [dict(row) for row in rows] if rows else []


# ============================================================================
# COMMON QUERY HELPERS
# ============================================================================

def get_one(sql, params=None):
    """Execute a query and return a single row as dictionary."""
    with get_db_context() as db:
        cursor = db.execute(sql, params) if params else db.execute(sql)
        row = cursor.fetchone()
        return row_to_dict(row)


def get_all(sql, params=None):
    """Execute a query and return all rows as list of dictionaries."""
    with get_db_context() as db:
        cursor = db.execute(sql, params) if params else db.execute(sql)
        rows = cursor.fetchall()
        return rows_to_list(rows)


def get_count(table, where_clause="", params=None):
    """Get count of rows in a table with optional WHERE clause."""
    sql = f"SELECT COUNT(*) as cnt FROM {table}"
    if where_clause:
        sql += f" WHERE {where_clause}"
    result = get_one(sql, params)
    return result['cnt'] if result else 0


def exists(table, where_clause, params=None):
    """Check if a record exists in a table."""
    sql = f"SELECT 1 FROM {table} WHERE {where_clause} LIMIT 1"
    result = get_one(sql, params)
    return result is not None


# ============================================================================
# SEED DATA AND MIGRATION HELPERS
# ============================================================================

def table_exists(table_name):
    """Check if a table exists in the database."""
    with get_db_context() as db:
        result = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        ).fetchone()
        return result is not None


def column_exists(table_name, column_name):
    """Check if a column exists in a table."""
    with get_db_context() as db:
        result = db.execute(f"PRAGMA table_info({table_name})").fetchall()
        columns = [row['name'] for row in result]
        return column_name in columns


def add_column_if_not_exists(table_name, column_name, column_definition):
    """
    Add a column to a table if it doesn't exist.
    
    Args:
        table_name: Name of the table
        column_name: Name of the column to add
        column_definition: SQLite column definition (e.g., "INTEGER DEFAULT 0")
    """
    if not column_exists(table_name, column_name):
        with get_db_context() as db:
            db.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
            db.commit()


def seed_simple_lookup(table_name, key_field, value_field, data, extra_fields=None):
    """
    Seed a simple key-value lookup table.
    
    Args:
        table_name: Table to seed
        key_field: Name of the key column
        value_field: Name of the value column
        data: List of tuples [(key, value), ...] or list of values for auto-increment
        extra_fields: Optional dict of {field: value} for all rows
    """
    with get_db_context() as db:
        for item in data:
            if isinstance(item, tuple):
                key, value = item
                values = [key, value]
            else:
                values = [item]
            
            if extra_fields:
                for field, val in extra_fields.items():
                    values.append(val)
            
            placeholders = ','.join(['?' for _ in values])
            fields = key_field
            if value_field:
                fields += f",{value_field}"
            if extra_fields:
                fields += "," + ','.join(extra_fields.keys())
            
            sql = f"INSERT OR IGNORE INTO {table_name} ({fields}) VALUES ({placeholders})"
            db.execute(sql, values)
        db.commit()


# ============================================================================
# PLATFORM AUDIT LOGGING (UNIFIED)
# ============================================================================

def log_audit(entity_type, entity_id, action, user_id=None,
               field_name=None, old_value=None, new_value=None,
               notes=None, ip_address=None, company_id=None):
    """
    Unified platform audit logging function.
    All modules should use this instead of creating their own audit tables.
    
    Args:
        entity_type: Type of entity (e.g., 'customer', 'employee', 'order')
        entity_id: ID of the entity
        action: Action performed (CREATE, UPDATE, DELETE, LOGIN, LOGOUT, APPROVE, etc.)
        user_id: ID of user performing action
        field_name: Name of field changed (for UPDATE actions)
        old_value: Previous value
        new_value: New value
        notes: Additional notes
        ip_address: Client IP address
        company_id: Company/branch context
    """
    # Ensure platform_audit_log table exists
    _ensure_audit_table()
    
    with get_db_context() as db:
        db.execute("""
            INSERT INTO platform_audit_log 
            (entity_type, entity_id, action, user_id, field_name, old_value, new_value, notes, ip_address, company_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (entity_type, entity_id, action, user_id, field_name, old_value, new_value, notes, ip_address, company_id))
        db.commit()


def _ensure_audit_table():
    """Ensure the unified audit log table exists."""
    if not table_exists('platform_audit_log'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE platform_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entity_type TEXT NOT NULL,
                    entity_id INTEGER,
                    action TEXT NOT NULL,
                    user_id INTEGER,
                    field_name TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    notes TEXT,
                    ip_address TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_audit_entity ON platform_audit_log(entity_type, entity_id)")
            db.execute("CREATE INDEX idx_audit_user ON platform_audit_log(user_id, created_at)")
            db.execute("CREATE INDEX idx_audit_action ON platform_audit_log(action, created_at)")
            db.commit()


# ============================================================================
# PLATFORM NOTIFICATIONS (UNIFIED)
# ============================================================================

def create_notification(title, message, notification_type="INFO",
                        user_id=None, role_id=None,
                        severity="MEDIUM", link_url=None,
                        related_entity_type=None, related_entity_id=None,
                        company_id=None, expires_at=None):
    """
    Unified platform notification creation.
    All modules should use this instead of creating their own notification tables.
    
    Args:
        title: Notification title
        message: Notification message body
        notification_type: Type (INFO, WARNING, ERROR, SUCCESS, APPROVAL)
        user_id: Specific user to notify (optional)
        role_id: Role to notify (optional)
        severity: LOW, MEDIUM, HIGH, CRITICAL
        link_url: URL to link to
        related_entity_type: Entity type for linking
        related_entity_id: Entity ID for linking
        company_id: Company context
        expires_at: Expiration datetime (optional)
    """
    _ensure_notification_table()
    
    with get_db_context() as db:
        db.execute("""
            INSERT INTO platform_notifications 
            (title, message, notification_type, user_id, role_id, severity, 
             link_url, related_entity_type, related_entity_id, company_id, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (title, message, notification_type, user_id, role_id, severity,
              link_url, related_entity_type, related_entity_id, company_id, expires_at))
        db.commit()


def _ensure_notification_table():
    """Ensure the unified notifications table exists."""
    if not table_exists('platform_notifications'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE platform_notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    message TEXT,
                    notification_type TEXT DEFAULT 'INFO',
                    user_id INTEGER,
                    role_id INTEGER,
                    severity TEXT DEFAULT 'MEDIUM',
                    is_read INTEGER DEFAULT 0,
                    read_at TIMESTAMP,
                    link_url TEXT,
                    related_entity_type TEXT,
                    related_entity_id INTEGER,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_notif_user ON platform_notifications(user_id, is_read)")
            db.execute("CREATE INDEX idx_notif_role ON platform_notifications(role_id, is_read)")
            db.execute("CREATE INDEX idx_notif_created ON platform_notifications(created_at)")
            db.commit()


def get_user_notifications(user_id, unread_only=False, limit=50):
    """Get notifications for a user."""
    _ensure_notification_table()
    
    sql = """
        SELECT * FROM platform_notifications 
        WHERE (user_id = ? OR user_id IS NULL)
        AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
    """
    params = [user_id]
    
    if unread_only:
        sql += " AND is_read = 0"
    
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    return get_all(sql, params)


# ============================================================================
# PLATFORM SETTINGS (UNIFIED)
# ============================================================================

def get_platform_setting(key, default=None, category=None):
    """
    Get a platform-wide setting value.
    
    Args:
        key: Setting key
        default: Default value if not found
        category: Optional category filter
    
    Returns:
        Setting value as string, or default
    """
    _ensure_settings_table()
    
    sql = "SELECT setting_value FROM platform_settings WHERE setting_key = ?"
    params = [key]
    
    if category:
        sql += " AND category = ?"
        params.append(category)
    
    result = get_one(sql, params)
    return result['setting_value'] if result else default


def set_platform_setting(key, value, category="GENERAL", description=None):
    """
    Set a platform-wide setting value.
    
    Args:
        key: Setting key
        value: Setting value (will be converted to string)
        category: Setting category
        description: Optional description
    """
    _ensure_settings_table()
    
    with get_db_context() as db:
        existing = db.execute(
            "SELECT id FROM platform_settings WHERE setting_key = ?", (key,)
        ).fetchone()
        
        if existing:
            db.execute(
                "UPDATE platform_settings SET setting_value = ?, category = ?, description = ?, updated_at = CURRENT_TIMESTAMP WHERE setting_key = ?",
                (str(value), category, description, key)
            )
        else:
            db.execute(
                "INSERT INTO platform_settings (setting_key, setting_value, category, description) VALUES (?, ?, ?, ?)",
                (key, str(value), category, description)
            )
        db.commit()


def _ensure_settings_table():
    """Ensure the unified settings table exists."""
    if not table_exists('platform_settings'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE platform_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT,
                    category TEXT DEFAULT 'GENERAL',
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.commit()


# ============================================================================
# PLATFORM MASTER DATA LOOKUP
# ============================================================================

def get_master_companies():
    """Get all companies."""
    return get_all("SELECT * FROM companies ORDER BY name")


def get_master_warehouses(company_id=None):
    """Get all warehouses, optionally filtered by company."""
    if company_id:
        return get_all("SELECT * FROM warehouses WHERE company_id = ? ORDER BY name", (company_id,))
    return get_all("SELECT * FROM warehouses ORDER BY name")


def get_master_users(active_only=True):
    """Get all system users."""
    sql = "SELECT id, username, email, role_id, created_at FROM users"
    if active_only:
        sql += " WHERE 1=1"  # Can add active flag when available
    sql += " ORDER BY username"
    return get_all(sql)


def get_master_customers(active_only=True):
    """Get master customer list from canonical customers table."""
    sql = "SELECT * FROM customers"
    if active_only:
        sql += " WHERE status = 'Active'"  # Adjust based on actual column
    sql += " ORDER BY name"
    return get_all(sql)


def get_master_items(active_only=True):
    """Get master item/product list from canonical parts table."""
    sql = "SELECT * FROM parts"
    if active_only:
        sql += " WHERE is_active = 1"  # Adjust based on actual column
    sql += " ORDER BY name"
    return get_all(sql)


def get_master_suppliers(active_only=True):
    """Get master supplier list."""
    sql = "SELECT * FROM suppliers"
    if active_only:
        sql += " WHERE status = 'Active'"
    sql += " ORDER BY name"
    return get_all(sql)


# ============================================================================
# PLATFORM STATUS DEFINITIONS (UNIFIED)
# ============================================================================

# Standard status values used across the platform
STANDARD_STATUSES = {
    'record_status': ['Draft', 'Active', 'Inactive', 'Archived'],
    'task_status': ['Open', 'In Progress', 'Review', 'Completed', 'Canceled'],
    'approval_status': ['Pending', 'Approved', 'Rejected', 'Returned'],
    'priority': ['Low', 'Medium', 'High', 'Critical'],
    'severity': ['Low', 'Medium', 'High', 'Critical'],
    'gender': ['Male', 'Female', 'Other'],
    'marital_status': ['Single', 'Married', 'Divorced', 'Widowed'],
    'employment_type': ['Full-time', 'Part-time', 'Contract', 'Temporary', 'Intern'],
    'contract_type': ['Permanent', 'Fixed-term', 'Project-based'],
    'leave_status': ['Pending', 'Approved', 'Rejected', 'Canceled'],
    'payroll_status': ['Draft', 'Calculated', 'Approved', 'Paid', 'Locked'],
    'attendance_status': ['Present', 'Absent', 'Late', 'On Leave', 'Holiday'],
    'delivery_status': ['Pending', 'Dispatched', 'In Transit', 'Delivered', 'Failed', 'Returned'],
    'order_status': ['Draft', 'Confirmed', 'Processing', 'Shipped', 'Delivered', 'Canceled'],
    'invoice_status': ['Draft', 'Sent', 'Paid', 'Overdue', 'Canceled'],
}

# Status color mapping for consistent UI
STATUS_COLORS = {
    'Draft': 'gray',
    'Open': 'blue',
    'Active': 'green',
    'Pending': 'yellow',
    'In Progress': 'blue',
    'Review': 'purple',
    'Approved': 'green',
    'Completed': 'green',
    'Rejected': 'red',
    'Canceled': 'gray',
    'Inactive': 'gray',
    'Archived': 'gray',
    'Low': 'gray',
    'Medium': 'yellow',
    'High': 'orange',
    'Critical': 'red',
    'Delivered': 'green',
    'In Transit': 'blue',
    'Failed': 'red',
    'Returned': 'yellow',
    'Overdue': 'red',
    'Paid': 'green',
    'Sent': 'blue',
    'Locked': 'gray',
    'Present': 'green',
    'Absent': 'red',
    'Late': 'yellow',
    'On Leave': 'blue',
    'Holiday': 'purple',
}


def get_status_color(status):
    """Get the standard color for a status value."""
    return STATUS_COLORS.get(status, 'gray')


# ============================================================================
# EXPORT HELPERS
# ============================================================================

def export_to_dict_list(query_or_table, params=None):
    """
    Execute a query or table name and return as list of dicts.
    
    Args:
        query_or_table: SQL query string or table name
        params: Query parameters
    
    Returns:
        List of dictionaries
    """
    if query_or_table.strip().upper().startswith("SELECT"):
        return get_all(query_or_table, params)
    else:
        return get_all(f"SELECT * FROM {query_or_table}")


# ============================================================================
# USER PROFILE EXTENSIONS (Extended Profile Data)
# ============================================================================

def _ensure_profile_extensions_table():
    """Ensure the user profile extensions table exists."""
    if not table_exists('user_profile_extensions'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE user_profile_extensions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    -- Personal Info
                    first_name TEXT,
                    last_name TEXT,
                    display_name TEXT,
                    preferred_name TEXT,
                    date_of_birth TEXT,
                    gender TEXT,
                    nationality TEXT,
                    bio TEXT,
                    headline TEXT,
                    spoken_languages TEXT,
                    timezone TEXT,
                    notes TEXT,
                    -- Contact Info
                    secondary_email TEXT,
                    mobile TEXT,
                    secondary_mobile TEXT,
                    whatsapp TEXT,
                    phone_extension TEXT,
                    country TEXT,
                    city TEXT,
                    address TEXT,
                    emergency_contact_name TEXT,
                    emergency_contact_phone TEXT,
                    emergency_contact_relation TEXT,
                    preferred_communication TEXT,
                    -- Work Info
                    department TEXT,
                    position TEXT,
                    job_title TEXT,
                    employee_code TEXT,
                    work_email TEXT,
                    work_phone TEXT,
                    hire_date TEXT,
                    termination_date TEXT,
                    reporting_to TEXT,
                    team TEXT,
                    territory TEXT,
                    work_notes TEXT,
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_profile_user ON user_profile_extensions(user_id)")
            db.commit()


def get_user_profile_extension(user_id):
    """Get extended profile data for a user."""
    return get_one("SELECT * FROM user_profile_extensions WHERE user_id = ?", (user_id,))


def save_user_profile_extension(user_id, data):
    """Save/update extended profile data for a user."""
    _ensure_profile_extensions_table()
    
    fields = []
    values = []
    for key, value in data.items():
        if key not in ('id', 'user_id', 'created_at'):
            fields.append(f"{key} = ?")
            values.append(value)
    
    values.append(user_id)
    
    with get_db_context() as db:
        existing = db.execute("SELECT id FROM user_profile_extensions WHERE user_id = ?", (user_id,)).fetchone()
        
        if existing:
            fields_str = ", ".join(fields) + ", updated_at = CURRENT_TIMESTAMP"
            sql = f"UPDATE user_profile_extensions SET {fields_str} WHERE user_id = ?"
        else:
            set_fields = ", ".join([f.split(" = ")[0] for f in fields])
            placeholders = ",".join(["?" for _ in fields])
            sql = f"INSERT INTO user_profile_extensions (user_id, {set_fields}) VALUES (?, {placeholders})"
        
        db.execute(sql, values)
        db.commit()


# ============================================================================
# USER NOTIFICATION PREFERENCES
# ============================================================================

def _ensure_notification_prefs_table():
    """Ensure the user notification preferences table exists."""
    if not table_exists('user_notification_preferences'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE user_notification_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    -- In-app notifications
                    inapp_tasks TEXT DEFAULT '1',
                    inapp_approvals TEXT DEFAULT '1',
                    inapp_deliveries TEXT DEFAULT '1',
                    inapp_stock TEXT DEFAULT '1',
                    inapp_sales TEXT DEFAULT '1',
                    inapp_hr TEXT DEFAULT '1',
                    inapp_system TEXT DEFAULT '1',
                    -- Email notifications
                    email_tasks TEXT DEFAULT '0',
                    email_approvals TEXT DEFAULT '0',
                    email_deliveries TEXT DEFAULT '0',
                    email_stock TEXT DEFAULT '0',
                    email_sales TEXT DEFAULT '0',
                    email_digest TEXT DEFAULT '0',
                    -- General
                    daily_summary TEXT DEFAULT '0',
                    weekly_summary TEXT DEFAULT '0',
                    urgent_only TEXT DEFAULT '0',
                    sound_enabled TEXT DEFAULT '1',
                    quiet_hours_enabled TEXT DEFAULT '0',
                    quiet_hours_start TEXT DEFAULT '22:00',
                    quiet_hours_end TEXT DEFAULT '08:00',
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_notif_prefs_user ON user_notification_preferences(user_id)")
            db.commit()


def get_user_notification_preferences(user_id):
    """Get notification preferences for a user."""
    return get_one("SELECT * FROM user_notification_preferences WHERE user_id = ?", (user_id,))


# ============================================================================
# USER PRIVACY SETTINGS
# ============================================================================

def _ensure_privacy_settings_table():
    """Ensure the user privacy settings table exists."""
    if not table_exists('user_privacy_settings'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE user_privacy_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    profile_visibility TEXT DEFAULT 'internal',
                    show_email TEXT DEFAULT '0',
                    show_phone TEXT DEFAULT '0',
                    show_mobile TEXT DEFAULT '0',
                    show_department TEXT DEFAULT '1',
                    show_role TEXT DEFAULT '1',
                    show_last_login TEXT DEFAULT '0',
                    allow_directory_search TEXT DEFAULT '1',
                    show_activity_status TEXT DEFAULT '1',
                    show_online_indicator TEXT DEFAULT '1',
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_privacy_user ON user_privacy_settings(user_id)")
            db.commit()


def get_user_privacy_settings(user_id):
    """Get privacy settings for a user."""
    return get_one("SELECT * FROM user_privacy_settings WHERE user_id = ?", (user_id,))


# ============================================================================
# USER LINKED ACCOUNTS
# ============================================================================

def _ensure_linked_accounts_table():
    """Ensure the user linked accounts table exists."""
    if not table_exists('user_linked_accounts'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE user_linked_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    provider TEXT NOT NULL,
                    provider_user_id TEXT,
                    provider_email TEXT,
                    access_token_encrypted TEXT,
                    refresh_token_encrypted TEXT,
                    token_expires_at TIMESTAMP,
                    is_active TEXT DEFAULT '1',
                    -- Timestamps
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, provider)
                )
            """)
            db.execute("CREATE INDEX idx_linked_user ON user_linked_accounts(user_id)")
            db.commit()


def get_user_linked_accounts(user_id):
    """Get linked accounts for a user."""
    return get_all("SELECT * FROM user_linked_accounts WHERE user_id = ? AND is_active = '1'", (user_id,))


# ============================================================================
# USER SESSIONS TRACKING
# ============================================================================

def _ensure_sessions_table():
    """Ensure the user sessions table exists for tracking login sessions."""
    if not table_exists('user_sessions'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    device_info TEXT,
                    location TEXT,
                    is_current INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_sessions_user ON user_sessions(user_id)")
            db.execute("CREATE INDEX idx_sessions_token ON user_sessions(session_token)")
            db.commit()


def create_user_session(user_id, session_token, ip_address, user_agent, device_info=None, location=None):
    """Create a new session record for a user."""
    _ensure_sessions_table()
    
    with get_db_context() as db:
        # Deactivate old sessions for this user (optional - keep only recent)
        db.execute("""
            UPDATE user_sessions SET is_active = 0
            WHERE user_id = ? AND created_at < datetime('now', '-7 days')
        """, (user_id,))
        
        # Create new session
        db.execute("""
            INSERT INTO user_sessions (user_id, session_token, ip_address, user_agent, device_info, location)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, session_token, ip_address, user_agent, device_info, location))
        db.commit()


def get_user_active_sessions(user_id):
    """Get active sessions for a user."""
    return get_all("""
        SELECT * FROM user_sessions
        WHERE user_id = ? AND is_active = 1 AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
        ORDER BY last_activity DESC
    """, (user_id,))


def deactivate_session(session_id):
    """Deactivate a specific session."""
    with get_db_context() as db:
        db.execute("UPDATE user_sessions SET is_active = 0 WHERE id = ?", (session_id,))
        db.commit()


def deactivate_all_user_sessions(user_id, except_current=True):
    """Deactivate all sessions for a user, optionally except current."""
    with get_db_context() as db:
        if except_current:
            db.execute("""
                UPDATE user_sessions SET is_active = 0
                WHERE user_id = ? AND is_current = 0
            """, (user_id,))
        else:
            db.execute("UPDATE user_sessions SET is_active = 0 WHERE user_id = ?", (user_id,))
        db.commit()


# ============================================================================
# PROFILE COMPLETION SCORING
# ============================================================================

def calculate_profile_completion_score(user_id):
    """
    Calculate profile completion percentage for a user.
    Returns 0-100 score.
    """
    score = 0
    total_fields = 10
    
    # Get user data
    user = get_one("SELECT * FROM users WHERE id = ?", (user_id,))
    if not user:
        return 0
    
    # Check basic fields
    if user.get('username'): score += 1
    if user.get('email'): score += 1
    if user.get('profile_pic') and user['profile_pic'] != 'default.png': score += 1
    
    # Get extended profile
    ext = get_user_profile_extension(user_id)
    if ext:
        if ext.get('first_name'): score += 1
        if ext.get('last_name'): score += 1
        if ext.get('phone') or ext.get('mobile'): score += 1
        if ext.get('bio'): score += 1
        if ext.get('date_of_birth'): score += 1
    else:
        # Missing extended profile counts as 5 incomplete fields
        pass
    
    return int((score / total_fields) * 100)


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_platform_schema():
    """
    Initialize the unified platform schema elements.
    Called during app startup to ensure all shared tables exist.
    """
    _ensure_audit_table()
    _ensure_notification_table()
    _ensure_settings_table()
    _ensure_profile_extensions_table()
    _ensure_notification_prefs_table()
    _ensure_privacy_settings_table()
    _ensure_linked_accounts_table()
    _ensure_sessions_table()
    
    # Seed default platform settings if not exist
    default_settings = [
        ('platform_name', 'MMDx', 'GENERAL', 'Platform display name'),
        ('default_language', 'en', 'GENERAL', 'Default system language'),
        ('default_currency', 'AED', 'GENERAL', 'Default currency code'),
        ('date_format', 'DD/MM/YYYY', 'GENERAL', 'Default date format'),
        ('timezone', 'Asia/Dubai', 'GENERAL', 'Default timezone'),
        ('session_timeout_minutes', '120', 'SECURITY', 'Session timeout in minutes'),
        ('max_login_attempts', '5', 'SECURITY', 'Maximum failed login attempts'),
        ('password_min_length', '8', 'SECURITY', 'Minimum password length'),
        ('require_email_verification', '0', 'SECURITY', 'Require email verification'),
        ('default_theme', 'dark', 'UI', 'Default UI theme'),
        ('items_per_page', '50', 'UI', 'Default pagination size'),
        ('enable_rtl', '1', 'UI', 'Enable RTL language support'),
        ('company_name', 'Warehouse Dashboard', 'COMPANY', 'Default company name'),
        ('support_email', 'support@warehouse.local', 'COMPANY', 'Support email address'),
    ]
    
    for key, value, category, description in default_settings:
        existing = get_platform_setting(key)
        if existing is None:
            set_platform_setting(key, value, category, description)


# Run initialization when this module is imported
initialize_platform_schema()
