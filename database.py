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
- Query result caching for performance

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

    # Cached query (for frequently accessed data)
    from database import cached_query
    users = cached_query('all_users', 300, lambda: get_all("SELECT * FROM users"))
"""

import sqlite3
import os
import time
import hashlib
import json
import re
import threading
from contextlib import contextmanager
from functools import wraps
from collections import OrderedDict
from typing import Optional, List, Dict, Any, Tuple, Union, Generator, Callable
import queue

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
# QUERY TIMING AND LOGGING (7.1)
# ============================================================================

import logging as _logging
import time as _time

# Configure slow query logging
_query_logger = _logging.getLogger('db_queries')
_query_logger.setLevel(_logging.INFO)

# Query timing threshold (seconds) - queries slower than this are logged as warnings
SLOW_QUERY_THRESHOLD = float(os.environ.get('SLOW_QUERY_THRESHOLD', '0.5'))

# Query stats tracking
_query_stats = {
    'total_queries': 0,
    'slow_queries': 0,
    'total_time': 0.0,
}


def log_query(query, duration, params=None):
    """
    Log a database query with timing information.

    Args:
        query: SQL query string
        duration: Query execution time in seconds
        params: Query parameters (optional)
    """
    global _query_stats
    _query_stats['total_queries'] += 1
    _query_stats['total_time'] += duration

    if duration > SLOW_QUERY_THRESHOLD:
        _query_stats['slow_queries'] += 1
        _query_logger.warning(
            f'Slow query ({duration:.3f}s): {query[:100]}...'
            f' params={params[:3] if params else None}'
        )
    else:
        _query_logger.debug(
            f'Query ({duration:.3f}s): {query[:100]}...'
        )


def get_query_stats():
    """Return query statistics."""
    total = _query_stats['total_queries']
    slow = _query_stats['slow_queries']
    return {
        'total_queries': total,
        'slow_queries': slow,
        'slow_query_rate': f"{(slow / total * 100) if total > 0 else 0:.1f}%",
        'total_time': f"{_query_stats['total_time']:.3f}s",
        'avg_time': f"{(_query_stats['total_time'] / total) if total > 0 else 0:.4f}s"
    }


def reset_query_stats():
    """Reset query statistics."""
    global _query_stats
    _query_stats = {
        'total_queries': 0,
        'slow_queries': 0,
        'total_time': 0.0,
    }


class QueryLogger:
    """
    Context manager for timing and logging database queries.

    Usage:
        with QueryLogger('SELECT * FROM users'):
            db.execute('SELECT * FROM users')
    """

    def __init__(self, query_name='', query=None, params=None):
        self.query_name = query_name
        self.query = query
        self.params = params
        self.duration = 0
        self.error = None

    def __enter__(self):
        self.start_time = _time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.duration = _time.time() - self.start_time
        if exc_type is None:
            log_query(self.query or self.query_name, self.duration, self.params)
        else:
            self.error = str(exc_val)
            _query_logger.error(f'Query error: {self.query_name} - {self.error}')
        return False  # Don't suppress exceptions


def timed_query(query, params=None):
    """
    Execute a query and time it, logging if slow.

    Args:
        query: SQL query string
        params: Query parameters

    Returns:
        tuple: (results, duration)
    """
    start = _time.time()
    try:
        with get_db_context() as db:
            cursor = db.execute(query, params) if params else db.execute(query)
            results = cursor.fetchall()
        duration = _time.time() - start
        log_query(query, duration, params)
        return results, duration
    except Exception as e:
        duration = _time.time() - start
        _query_logger.error(f'Query failed ({duration:.3f}s): {query[:50]}... - {e}')
        raise


# ============================================================================
# CORE DATABASE CONNECTION FACTORY
# ============================================================================

# Global flag to enable connection pooling via environment variable
_DB_POOLING_ENABLED = os.environ.get('DB_POOLING_ENABLED', '0') == '1'


def get_db() -> sqlite3.Connection:
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

    Connection Pooling:
        When DB_POOLING_ENABLED=1, uses the connection pool for better
        concurrency. Connections must be returned via return_connection()
        or by using get_db_context() which handles this automatically.
    """
    if _DB_POOLING_ENABLED:
        return get_pool().get_connection()

    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row

    # Apply all standard PRAGMAs
    for pragma_sql, _ in STANDARD_PRAGMAS:
        conn.execute(pragma_sql)

    return conn


def get_db_pooled():
    """
    Get a database connection from the pool.
    Use return_connection() to return to pool when done.

    This is equivalent to get_db() when DB_POOLING_ENABLED=1.
    """
    return get_pool().get_connection()


def is_pooling_enabled() -> bool:
    """Check if connection pooling is enabled."""
    return _DB_POOLING_ENABLED


@contextmanager
def get_db_context() -> Generator[sqlite3.Connection, None, None]:
    """
    Context manager for database operations.
    Automatically handles connection close, even on exceptions.

    Usage:
        with get_db_context() as db:
            db.execute("INSERT INTO ... VALUES (?)", (value,))
            db.commit()

    Returns:
        Generator yielding sqlite3.Connection
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

def row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    """Convert a sqlite3.Row to a regular dictionary."""
    return dict(row) if row else None


def rows_to_list(rows: Optional[List[sqlite3.Row]]) -> List[Dict[str, Any]]:
    """Convert a list of sqlite3.Row objects to a list of dictionaries."""
    return [dict(row) for row in rows] if rows else []


# ============================================================================
# COMMON QUERY HELPERS
# ============================================================================

def get_one(sql: str, params: Optional[Tuple[Any, ...]] = None) -> Optional[Dict[str, Any]]:
    """Execute a query and return a single row as dictionary."""
    with get_db_context() as db:
        cursor = db.execute(sql, params) if params else db.execute(sql)
        row = cursor.fetchone()
        return row_to_dict(row)


def get_all(sql: str, params: Optional[Tuple[Any, ...]] = None) -> List[Dict[str, Any]]:
    """Execute a query and return all rows as list of dictionaries."""
    with get_db_context() as db:
        cursor = db.execute(sql, params) if params else db.execute(sql)
        rows = cursor.fetchall()
        return rows_to_list(rows)


def _validate_identifier(name, type_name="identifier"):
    """
    Validate that a name is safe for use in SQL (tables, columns, indexes).
    Only allows alphanumeric characters and underscores.
    
    Args:
        name: The identifier to validate
        type_name: Name of the type for error messages
    
    Returns:
        The validated name
    
    Raises:
        ValueError: If the name contains unsafe characters
    """
    if not name or not isinstance(name, str):
        raise ValueError(f"{type_name} must be a non-empty string")
    
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
        raise ValueError(f"{type_name} contains invalid characters: {name}")
    
    # Check length
    if len(name) > 64:
        raise ValueError(f"{type_name} is too long (max 64 characters)")
    
    return name


def get_count(table, where_clause="", params=None):
    """Get count of rows in a table with optional WHERE clause."""
    table = _validate_identifier(table, "table name")
    if where_clause:
        # Only validate table name in where_clause, params are parameterized
        # Note: where_clause here is expected to be safe (constructed internally)
        where_clause = _validate_identifier(where_clause.split('=')[0].strip(), "where clause field") if '=' in where_clause else ""
    sql = f"SELECT COUNT(*) as cnt FROM {table}"
    if where_clause:
        sql += f" WHERE {where_clause}"
    result = get_one(sql, params)
    return result['cnt'] if result else 0


def exists(table, where_clause, params=None):
    """Check if a record exists in a table."""
    table = _validate_identifier(table, "table name")
    # where_clause should be parameterized - only use for field names
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
    table_name = _validate_identifier(table_name, "table name")
    column_name = _validate_identifier(column_name, "column name")
    with get_db_context() as db:
        result = db.execute(f"PRAGMA table_info({table_name})").fetchall()
        columns = [row['name'] for row in result]
        return column_name in columns


def add_column_if_not_exists(table_name, column_name, column_definition):
    """
    Add a column to a table if it doesn't exist.

    Args:
        table_name: Name of the table (must be validated identifier)
        column_name: Name of the column to add (must be validated identifier)
        column_definition: SQLite column definition (e.g., "INTEGER DEFAULT 0")
    """
    table_name = _validate_identifier(table_name, "table name")
    column_name = _validate_identifier(column_name, "column name")
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

# In-memory cache for platform settings
_platform_settings_cache = {}
_platform_settings_cache_time = {}
_PLATFORM_SETTINGS_CACHE_TTL = 300  # 5 minutes


def get_platform_setting(key, default=None, category=None):
    """
    Get a platform-wide setting value with caching.

    Args:
        key: Setting key
        default: Default value if not found
        category: Optional category filter

    Returns:
        Setting value as string, or default
    """
    import time

    # Check cache first
    cache_key = f"{key}:{category}"
    now = time.time()
    if cache_key in _platform_settings_cache:
        cached_time, cached_value = _platform_settings_cache[cache_key]
        if now - cached_time < _PLATFORM_SETTINGS_CACHE_TTL:
            return cached_value

    # Cache miss - fetch from database
    _ensure_settings_table()

    sql = "SELECT setting_value FROM platform_settings WHERE setting_key = ?"
    params = [key]

    if category:
        sql += " AND category = ?"
        params.append(category)

    result = get_one(sql, params)
    value = result['setting_value'] if result else default

    # Store in cache
    _platform_settings_cache[cache_key] = (now, value)

    return value


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

    # Invalidate cache for this setting
    cache_key = f"{key}:{category}"
    _platform_settings_cache.pop(cache_key, None)


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
# CONNECTION POOLING (for scalability)
# ============================================================================

class ConnectionPool:
    """
    Thread-safe connection pool for SQLite.
    Maintains a pool of reusable connections to reduce connection overhead.
    """
    def __init__(self, database_path, pool_size=5, max_overflow=10, timeout=30.0):
        self.database_path = database_path
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.timeout = timeout
        self._pool = []
        self._overflow = []
        self._lock = threading.Lock()
        self._pragmas = STANDARD_PRAGMAS.copy()

    def _create_connection(self):
        """Create a new connection with standardized settings."""
        conn = sqlite3.connect(self.database_path, timeout=self.timeout)
        conn.row_factory = sqlite3.Row
        for pragma_sql, _ in self._pragmas:
            conn.execute(pragma_sql)
        return conn

    def get_connection(self):
        """
        Get a connection from the pool.
        Blocks if pool is exhausted until a connection is available or timeout.
        """
        deadline = time.time() + self.timeout

        while True:
            with self._lock:
                # Try pool first
                if self._pool:
                    return self._pool.pop()

                # Try overflow if under limit
                if len(self._overflow) < self.max_overflow:
                    conn = self._create_connection()
                    self._overflow.append(conn)
                    return conn

            # Wait and retry
            remaining = deadline - time.time()
            if remaining <= 0:
                raise RuntimeError("Connection pool timeout - too many concurrent requests")
            time.sleep(0.05)

    def return_connection(self, conn):
        """Return a connection to the pool."""
        with self._lock:
            if len(self._pool) < self.pool_size:
                self._pool.append(conn)
            else:
                conn.close()
                if self._overflow:
                    self._overflow.pop()

    def close_all(self):
        """Close all connections in pool."""
        with self._lock:
            for conn in self._pool + self._overflow:
                try:
                    conn.close()
                except Exception:
                    pass
            self._pool.clear()
            self._overflow.clear()


# Global connection pool instance (initialized lazily)
_pool = None


def get_pool():
    """Get or create the global connection pool."""
    global _pool
    if _pool is None:
        pool_size = int(os.environ.get('DB_POOL_SIZE', '5'))
        max_overflow = int(os.environ.get('DB_MAX_OVERFLOW', '10'))
        _pool = ConnectionPool(DATABASE_PATH, pool_size=pool_size, max_overflow=max_overflow)
    return _pool


# Pool-enabled get_db()
def get_db_pooled():
    """
    Get a database connection from the pool.
    Use return_connection() to return to pool when done.

    Usage:
        pool = get_pool()
        conn = pool.get_connection()
        try:
            result = conn.execute("SELECT * FROM users").fetchall()
        finally:
            pool.return_connection(conn)
    """
    return get_pool().get_connection()


def return_connection(conn):
    """Return a connection to the pool after use."""
    get_pool().return_connection(conn)


# ============================================================================
# QUERY RESULT CACHING (for performance)
# ============================================================================

class QueryCache:
    """
    Thread-safe in-memory query result cache.
    Uses LRU eviction when max_size is reached.
    """
    def __init__(self, max_size=1000, default_ttl=300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    def _make_key(self, prefix, *args, **kwargs):
        """Generate a cache key from prefix and arguments."""
        key_parts = [prefix] + [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_str = ':'.join(key_parts)
        return hashlib.md5(key_str.encode()).hexdigest()

    def get(self, prefix, *args, **kwargs):
        """Get cached result or return None."""
        key = self._make_key(prefix, *args, **kwargs)
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() < entry['expires_at']:
                    self._hits += 1
                    # Move to end (most recently used)
                    self._cache.move_to_end(key)
                    return entry['data']
                else:
                    # Expired - remove
                    del self._cache[key]
            self._misses += 1
        return None

    def set(self, data, prefix, *args, **kwargs):
        """Cache a result with TTL."""
        # Extract TTL before key generation (don't include in cache key)
        ttl = kwargs.pop('_ttl', self.default_ttl)
        # Also extract any other internal params that shouldn't be in key
        internal_keys = ['_ttl']
        filtered_kwargs = {k: v for k, v in kwargs.items() if k not in internal_keys}

        key = self._make_key(prefix, *args, **filtered_kwargs)
        expires_at = time.time() + ttl

        with self._lock:
            # Evict oldest if at capacity
            while len(self._cache) >= self.max_size:
                self._cache.popitem(last=False)

            self._cache[key] = {
                'data': data,
                'expires_at': expires_at
            }

    def invalidate(self, prefix=None, *args, **kwargs):
        """Invalidate cache entries matching pattern."""
        with self._lock:
            if prefix is None:
                self._cache.clear()
                return

            # Invalidate by prefix match
            keys_to_delete = []
            for key in list(self._cache.keys()):
                # Check if key starts with prefix
                if key.startswith(prefix):
                    keys_to_delete.append(key)

            # Delete only matching keys
            for key in keys_to_delete:
                del self._cache[key]

    def get_stats(self):
        """Return cache hit/miss statistics."""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total > 0 else 0
            return {
                'hits': self._hits,
                'misses': self._misses,
                'size': len(self._cache),
                'hit_rate': hit_rate
            }


# ============================================================================
# CIRCUIT BREAKER PATTERN (8.1)
# ============================================================================

class CircuitBreaker:
    """
    Thread-safe circuit breaker for fault tolerance.
    Prevents repeated calls to failing services.

    States:
        - CLOSED: Normal operation, requests pass through
        - OPEN: Service is down, requests fail fast
        - HALF_OPEN: Testing if service recovered
    """
    CLOSED = 'closed'
    OPEN = 'open'
    HALF_OPEN = 'half_open'

    def __init__(self, failure_threshold=5, timeout=60, success_threshold=2):
        """
        Args:
            failure_threshold: Number of failures before opening circuit
            timeout: Seconds to wait before trying again (OPEN -> HALF_OPEN)
            success_threshold: Successes needed to close circuit (HALF_OPEN -> CLOSED)
        """
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.success_threshold = success_threshold
        self._failures = 0
        self._successes = 0
        self._last_failure_time = None
        self._state = self.CLOSED
        self._lock = threading.Lock()

    @property
    def state(self):
        """Get current circuit state."""
        with self._lock:
            if self._state == self.OPEN:
                # Check if timeout expired
                if time.time() - self._last_failure_time >= self.timeout:
                    self._state = self.HALF_OPEN
                    self._successes = 0
            return self._state

    def call(self, func, *args, **kwargs):
        """
        Execute function through circuit breaker.

        Returns:
            Result of func, or raises CircuitBreakerOpen if circuit is OPEN
        """
        state = self.state

        if state == self.OPEN:
            raise CircuitBreakerOpen('Circuit breaker is OPEN')

        try:
            result = func(*args, **kwargs)

            with self._lock:
                if state == self.HALF_OPEN:
                    self._successes += 1
                    if self._successes >= self.success_threshold:
                        self._state = self.CLOSED
                        self._failures = 0

            return result

        except Exception as e:
            with self._lock:
                self._failures += 1
                self._last_failure_time = time.time()

                if self._failures >= self.failure_threshold:
                    self._state = self.OPEN

            raise e

    def reset(self):
        """Manually reset circuit breaker to closed state."""
        with self._lock:
            self._state = self.CLOSED
            self._failures = 0
            self._successes = 0
            self._last_failure_time = None


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""
    pass


# ============================================================================
# FALLBACK RESPONSE HELPERS (8.2)
# ============================================================================

def get_with_fallback(cache_key, fallback_func, ttl=300, cache=None):
    """
    Get from cache with fallback to function on miss/error.

    Args:
        cache_key: Cache key prefix for this data
        fallback_func: Function to call on cache miss
        ttl: Time-to-live for cached result (seconds)
        cache: Cache instance to use (defaults to global cache)

    Returns:
        Cached or freshly computed result
    """
    if cache is None:
        cache = get_cache()

    # Try cache first
    try:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
    except Exception as e:
        _query_logger.warning(f"Cache read error for key '{cache_key}': {e}")

    # Try fallback function
    try:
        result = fallback_func()
        # Cache the result if possible
        try:
            cache.set(result, cache_key, _ttl=ttl)
        except Exception as e:
            _query_logger.warning(f"Cache write error for key '{cache_key}': {e}")
        return result
    except Exception as e:
        # Fallback also failed - return empty but valid response
        return {
            'error': str(e),
            'data': [],
            'cached': False,
            'fallback_failed': True
        }


def batch_get_with_fallback(items, key_func, fallback_func, ttl=300, batch_size=100):
    """
    Get multiple items with fallback, with optional batching.

    Args:
        items: List of item identifiers
        key_func: Function(item) -> cache key
        fallback_func: Function(list of items) -> dict of results
        ttl: TTL for cached results
        batch_size: Number of items per fallback call

    Returns:
        Dict of {item_id: result} for all items
    """
    cache = get_cache()
    results = {}
    missing = []

    # Check cache for each item
    for item in items:
        key = key_func(item)
        cached = cache.get(key)
        if cached is not None:
            results[item] = cached
        else:
            missing.append(item)

    # Batch fetch missing items
    if missing:
        for i in range(0, len(missing), batch_size):
            batch = missing[i:i + batch_size]
            try:
                fetched = fallback_func(batch)
                if isinstance(fetched, dict):
                    for item_id, value in fetched.items():
                        key = key_func(item_id)
                        results[item_id] = value
                        try:
                            cache.set(value, key, _ttl=ttl)
                        except Exception as e:
                            _query_logger.warning(f"Cache batch write error for key '{key}': {e}")
                else:
                    # Non-dict fallback result, assign to all
                    for item_id in batch:
                        results[item_id] = fetched
            except Exception as e:
                # Fallback failed - assign error to missing items
                for item_id in batch:
                    results[item_id] = {
                        'error': str(e),
                        'data': None,
                        'cached': False
                    }

    return results


# ============================================================================
# REDIS CACHE BACKEND (Optional - falls back to in-memory)
# ============================================================================

_redis_client = None


def get_redis_client():
    """
    Get or create Redis client for distributed caching.
    Returns None if Redis is not available.
    """
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    try:
        import redis
        from config import REDIS_URL, REDIS_CACHE_URL

        redis_url = REDIS_CACHE_URL or REDIS_URL
        if not redis_url:
            return None

        _redis_client = redis.from_url(redis_url)
        _redis_client.ping()  # Test connection
        return _redis_client
    except Exception:
        return None


def invalidate_redis_cache(pattern):
    """
    Invalidate Redis cache keys matching pattern.

    Args:
        pattern: Redis key pattern (e.g., 'user_perms:*' or '*')

    Returns:
        Number of keys deleted
    """
    client = get_redis_client()
    if not client:
        return 0

    try:
        deleted = 0
        for key in client.scan_iter(match=pattern):
            client.delete(key)
            deleted += 1
        return deleted
    except Exception:
        return 0


class RedisQueryCache:
    """
    Redis-backed distributed query cache.
    Falls back to in-memory cache if Redis is unavailable.
    """

    def __init__(self, default_ttl=300):
        self.default_ttl = default_ttl
        self._local_cache = QueryCache(max_size=100, default_ttl=60)  # Local L1 cache
        self._hits = 0
        self._misses = 0
        self._local_hits = 0

    def _make_key(self, prefix, *args, **kwargs):
        """Generate a cache key from prefix and arguments."""
        key_parts = [prefix] + [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_str = ':'.join(key_parts)
        return f"mmdx:cache:{hashlib.md5(key_str.encode()).hexdigest()}"

    def get(self, prefix, *args, **kwargs):
        """Get cached result, checking local cache first, then Redis."""
        # Check local L1 cache first (very fast)
        local_result = self._local_cache.get(prefix, *args, **kwargs)
        if local_result is not None:
            self._local_hits += 1
            return local_result

        # Try Redis
        client = get_redis_client()
        if not client:
            self._misses += 1
            return None

        key = self._make_key(prefix, *args, **kwargs)
        try:
            cached = client.get(key)
            if cached is not None:
                import json
                result = json.loads(cached)
                self._hits += 1
                # Also populate local cache
                self._local_cache.set(result, prefix, *args, **kwargs)
                return result
        except Exception:
            pass

        self._misses += 1
        return None

    def set(self, data, prefix, *args, **kwargs):
        """Cache a result in both local and Redis cache."""
        ttl = kwargs.pop('_ttl', self.default_ttl)

        # Always set in local cache
        self._local_cache.set(data, prefix, *args, _ttl=ttl, **kwargs)

        # Try Redis
        client = get_redis_client()
        if not client:
            return

        key = self._make_key(prefix, *args, **kwargs)
        try:
            import json
            client.setex(key, ttl, json.dumps(data))
        except Exception:
            pass

    def invalidate(self, prefix=None):
        """Invalidate cache entries."""
        # Clear local cache
        if prefix is None:
            self._local_cache.invalidate()
        else:
            self._local_cache.invalidate(prefix)

        # Invalidate Redis
        if prefix:
            invalidate_redis_cache(f"mmdx:cache:{prefix}:*")
        else:
            invalidate_redis_cache("mmdx:cache:*")

    def get_stats(self):
        """Return cache hit/miss statistics."""
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        local_hit_rate = (self._local_hits / (self._local_hits + 1)) * 100  # Approximate

        return {
            'hits': self._hits,
            'misses': self._misses,
            'local_hits': self._local_hits,
            'hit_rate': hit_rate,
            'local_cache_size': len(self._local_cache._cache),
            'backend': 'redis' if get_redis_client() else 'memory'
        }


# Global query cache instance
_query_cache = None


def get_cache():
    """Get or create the global query cache (Redis-backed if available)."""
    global _query_cache
    if _query_cache is None:
        default_ttl = int(os.environ.get('QUERY_CACHE_TTL', '300'))
        _query_cache = RedisQueryCache(default_ttl=default_ttl)
    return _query_cache


def cached_query(prefix, ttl, query_func, *args, **kwargs):
    """
    Execute a query with caching (Redis-backed if available).

    Args:
        prefix: Cache key prefix
        ttl: Time-to-live in seconds
        query_func: Function to execute if cache miss
        *args, **kwargs: Arguments passed to both cache key and query_func

    Returns:
        Cached or freshly computed result
    """
    cache = get_cache()

    # Try to get from cache
    result = cache.get(prefix, *args, **kwargs)
    if result is not None:
        return result

    # Execute query
    result = query_func(*args, **kwargs)

    # Cache result
    cache.set(result, prefix, *args, _ttl=ttl, **kwargs)

    return result


# ============================================================================
# CURSOR-BASED PAGINATION
# ============================================================================

def paginate_query(sql, params=None, cursor_after=None, limit=50, order_by_column='id'):
    """
    Cursor-based pagination for efficient scrolling.

    Args:
        sql: Base query (should include ORDER BY for consistent ordering)
        params: Query parameters dictionary
        cursor_after: Row ID to cursor after (exclusive) - fetches rows with id < cursor_after
        limit: Page size (will fetch limit+1 to check if there's more)
        order_by_column: Column name to use for cursor comparison (default: 'id')

    Returns:
        tuple: (results as list of dicts, next_cursor or None)
    """
    if params is None:
        params = {}

    if cursor_after is not None:
        # Add WHERE clause to skip to cursor position
        # The cursor condition assumes ordering by id DESC
        cursor_condition = f"{order_by_column} < :cursor_after"
        if "WHERE" in sql.upper():
            sql = sql.replace("WHERE", f"{cursor_condition} AND (", 1)
        else:
            sql = sql.replace("ORDER BY", f"WHERE {cursor_condition} ORDER BY", 1)

        params['cursor_after'] = cursor_after

    # Add limit + 1 to detect if there are more results
    sql = sql.rstrip(';')
    sql += " LIMIT :limit"
    params['limit'] = limit + 1

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()

    has_more = len(rows) > limit
    if has_more:
        rows = rows[:-1]  # Remove the extra row

    next_cursor = None
    if rows and has_more:
        # Use the last row's order_by_column value as next cursor
        next_cursor = rows[-1][order_by_column]

    return rows_to_list(rows), next_cursor


def paginate_query_with_metadata(sql, params=None, cursor_after=None, limit=50,
                                   order_by_column='id', result_key='items'):
    """
    Cursor-based pagination with standardized response metadata.

    Args:
        sql: Base query (should include ORDER BY for consistent ordering)
        params: Query parameters dictionary
        cursor_after: Row ID to cursor after (exclusive)
        limit: Page size
        order_by_column: Column name to use for cursor comparison
        result_key: Key name for results in response

    Returns:
        dict: {
            result_key: [...list of items...],
            'pagination': {
                'next_cursor': cursor_value or None,
                'has_more': bool,
                'limit': int
            }
        }
    """
    rows, next_cursor = paginate_query(sql, params, cursor_after, limit, order_by_column)

    return {
        result_key: rows,
        'pagination': {
            'next_cursor': next_cursor,
            'has_more': next_cursor is not None,
            'limit': limit
        }
    }


# ============================================================================
# INDEX OPTIMIZATION
# ============================================================================

def ensure_index(table_name, index_name, columns, unique=False):
    """
    Ensure an index exists on a table, creating it if necessary.

    Args:
        table_name: Name of the table
        index_name: Name for the index (use 'idx_' prefix convention)
        columns: List of column names or single column string
        unique: Whether index should be unique

    Example:
        ensure_index('users', 'idx_users_email', ['email'])
        ensure_index('orders', 'idx_orders_customer_date', ['customer_id', 'order_date'])
    """
    # Validate all identifiers
    table_name = _validate_identifier(table_name, "table name")
    index_name = _validate_identifier(index_name, "index name")

    if isinstance(columns, str):
        columns = [columns]

    # Validate column names
    validated_columns = [_validate_identifier(col, "column name") for col in columns]

    # Check if index already exists
    existing = get_one("""
        SELECT 1 FROM sqlite_master
        WHERE type='index' AND name=?
    """, (index_name,))

    if existing:
        return False  # Index already exists

    # Create index
    columns_str = ', '.join(validated_columns)
    unique_str = 'UNIQUE ' if unique else ''

    sql = f"CREATE {unique_str}INDEX IF NOT EXISTS {index_name} ON {table_name} ({columns_str})"

    try:
        with get_db_context() as db:
            db.execute(sql)
        return True  # Index created
    except Exception as e:
        # Log but don't fail - index might be created by table creation
        return False


def ensure_indexes_for_table(table_name, indexes):
    """
    Ensure multiple indexes exist for a table.

    Args:
        table_name: Name of the table
        indexes: List of (index_name, columns, unique) tuples

    Example:
        ensure_indexes_for_table('orders', [
            ('idx_orders_customer', ['customer_id'], False),
            ('idx_orders_status', ['status'], False),
            ('idx_orders_date', ['order_date'], False),
        ])
    """
    created = []
    for index_def in indexes:
        if len(index_def) == 3:
            index_name, columns, unique = index_def
        else:
            index_name, columns = index_def
            unique = False

        if ensure_index(table_name, index_name, columns, unique):
            created.append(index_name)
    return created


# Standard platform indexes for high-traffic queries
PLATFORM_INDEXES = [
    # Users table
    ('users', 'idx_users_email', ['email'], False),
    ('users', 'idx_users_role', ['role_id'], False),
    ('users', 'idx_users_company', ['company_id'], False),
    ('users', 'idx_users_status', ['is_active'], False),

    # Notifications
    ('platform_notifications', 'idx_notif_user_read', ['user_id', 'is_read'], False),
    ('platform_notifications', 'idx_notif_created', ['created_at'], False),

    # Audit logs
    ('platform_audit_log', 'idx_audit_entity', ['entity_type', 'entity_id'], False),
    ('platform_audit_log', 'idx_audit_user', ['user_id', 'created_at'], False),
    ('platform_audit_log', 'idx_audit_action', ['action', 'created_at'], False),

    # Sessions
    ('user_sessions', 'idx_sessions_user', ['user_id'], False),
    ('user_sessions', 'idx_sessions_token', ['session_token'], False),

    # Flow messages (critical for chat performance)
    ('flow_messages', 'idx_flow_messages_conversation_time', ['conversation_id', 'created_at'], False),
    ('flow_messages', 'idx_flow_messages_sender', ['sender_id', 'created_at'], False),

    # Flow conversation members
    ('flow_conversation_members', 'idx_flow_conv_members_user', ['user_id', 'unread_count'], False),

    # WMS inventory (critical for SCM dashboards)
    ('wms_inventory_balances', 'idx_wms_inventory_item_wh', ['item_id', 'warehouse_id'], False),
    ('wms_items', 'idx_wms_items_active_code', ['is_active', 'item_code'], False),

    # Planning demand history
    ('planning_demand_history', 'idx_planning_demand_item_date', ['item_id', 'demand_date'], False),

    # Planning item profiles
    ('planning_item_profiles', 'idx_planning_profiles_item', ['item_id'], False),

    # SCM alerts
    ('planning_alerts', 'idx_planning_alerts_ack', ['is_acknowledged', 'severity', 'created_at'], False),

    # Platform notifications (additional composite index)
    ('platform_notifications', 'idx_platform_notif_user_read', ['user_id', 'is_read', 'created_at'], False),

    # Audit log (additional composite index for entity lookups)
    ('platform_audit_log', 'idx_platform_audit_entity_time', ['entity_type', 'entity_id', 'created_at'], False),
]


def initialize_platform_indexes():
    """Initialize all recommended platform indexes."""
    created = []
    for table, index_name, columns, unique in PLATFORM_INDEXES:
        if ensure_index(table, index_name, columns, unique):
            created.append(index_name)
    return created


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
        # Validate table name before interpolation
        query_or_table = _validate_identifier(query_or_table, "table name")
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


def deactivate_all_user_sessions(user_id, except_current=False):
    """Deactivate all sessions for a user, optionally except current.

    Args:
        user_id: The user ID whose sessions to deactivate
        except_current: If True, keeps the current session active (default: False for proper logout)
    """
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

    # Initialize platform indexes for query optimization
    initialize_platform_indexes()

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
