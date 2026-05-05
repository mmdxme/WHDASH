"""
Quick Tools Models
==================
Database models for the floating quick-tools system.
Handles: user notes, reminders, favorites, and tool preferences.
"""

from database import get_db_context, table_exists, get_one, get_all
import re


# ============================================================================
# QUICK NOTES
# ============================================================================

def ensure_quick_notes_table():
    """Ensure the quick_notes table exists."""
    if not table_exists('quick_notes'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS quick_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT,
                    content TEXT NOT NULL,
                    color TEXT DEFAULT 'blue',
                    is_pinned INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_notes_user ON quick_notes(user_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_notes_pinned ON quick_notes(user_id, is_pinned)")
            db.commit()


def get_user_notes(user_id):
    """Get all notes for a user."""
    ensure_quick_notes_table()
    return get_all(
        "SELECT * FROM quick_notes WHERE user_id = ? ORDER BY is_pinned DESC, updated_at DESC",
        (user_id,)
    )


def create_note(user_id, content, title=None, color='blue'):
    """Create a new quick note."""
    ensure_quick_notes_table()
    with get_db_context() as db:
        db.execute(
            "INSERT INTO quick_notes (user_id, title, content, color) VALUES (?, ?, ?, ?)",
            (user_id, title, content, color)
        )
        note_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    return note_id


def update_note(note_id, user_id, content=None, title=None, color=None, is_pinned=None):
    """Update an existing note."""
    ensure_quick_notes_table()
    fields = []
    params = []
    
    if content is not None:
        fields.append("content = ?")
        params.append(content)
    if title is not None:
        fields.append("title = ?")
        params.append(title)
    if color is not None:
        fields.append("color = ?")
        params.append(color)
    if is_pinned is not None:
        fields.append("is_pinned = ?")
        params.append(is_pinned)
    
    if not fields:
        return False
    
    fields.append("updated_at = CURRENT_TIMESTAMP")
    params.extend([note_id, user_id])
    
    with get_db_context() as db:
        result = db.execute(
            f"UPDATE quick_notes SET {', '.join(fields)} WHERE id = ? AND user_id = ?",
            params
        )
        return result.rowcount > 0


def delete_note(note_id, user_id):
    """Delete a note."""
    ensure_quick_notes_table()
    with get_db_context() as db:
        result = db.execute(
            "DELETE FROM quick_notes WHERE id = ? AND user_id = ?",
            (note_id, user_id)
        )
        return result.rowcount > 0


# ============================================================================
# QUICK REMINDERS
# ============================================================================

def ensure_quick_reminders_table():
    """Ensure the quick_reminders table exists."""
    if not table_exists('quick_reminders'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS quick_reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    remind_at TIMESTAMP NOT NULL,
                    is_done INTEGER DEFAULT 0,
                    done_at TIMESTAMP,
                    link_url TEXT,
                    link_label TEXT,
                    notified_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_reminders_user ON quick_reminders(user_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_reminders_remind_at ON quick_reminders(user_id, remind_at)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_reminders_done ON quick_reminders(user_id, is_done)")
            db.commit()
    else:
        # Migration: Add notified_at column if it doesn't exist
        with get_db_context() as db:
            try:
                db.execute("ALTER TABLE quick_reminders ADD COLUMN notified_at TIMESTAMP")
            except Exception:
                pass  # Column already exists


def get_user_reminders(user_id, include_done=False):
    """Get all reminders for a user."""
    ensure_quick_reminders_table()
    sql = "SELECT * FROM quick_reminders WHERE user_id = ?"
    if not include_done:
        sql += " AND is_done = 0"
    sql += " ORDER BY remind_at ASC"
    return get_all(sql, (user_id,))


def get_due_reminders(user_id):
    """Get reminders that are due now or overdue and haven't been notified."""
    ensure_quick_reminders_table()
    return get_all(
        """SELECT * FROM quick_reminders
           WHERE user_id = ? AND is_done = 0 AND remind_at <= CURRENT_TIMESTAMP
           AND (notified_at IS NULL OR notified_at < remind_at)
           ORDER BY remind_at ASC""",
        (user_id,)
    )


def create_reminder(user_id, title, remind_at, description=None, link_url=None, link_label=None):
    """Create a new reminder."""
    ensure_quick_reminders_table()
    with get_db_context() as db:
        db.execute(
            """INSERT INTO quick_reminders (user_id, title, description, remind_at, link_url, link_label)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, title, description, remind_at, link_url, link_label)
        )
        reminder_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    return reminder_id


def mark_reminder_notified(reminder_id):
    """Mark a reminder as notified to prevent re-notification."""
    ensure_quick_reminders_table()
    with get_db_context() as db:
        db.execute(
            "UPDATE quick_reminders SET notified_at = CURRENT_TIMESTAMP WHERE id = ?",
            (reminder_id,)
        )


def mark_reminder_done(reminder_id, user_id):
    """Mark a reminder as done."""
    ensure_quick_reminders_table()
    with get_db_context() as db:
        result = db.execute(
            """UPDATE quick_reminders SET is_done = 1, done_at = CURRENT_TIMESTAMP
               WHERE id = ? AND user_id = ?""",
            (reminder_id, user_id)
        )
        return result.rowcount > 0


def delete_reminder(reminder_id, user_id):
    """Delete a reminder."""
    ensure_quick_reminders_table()
    with get_db_context() as db:
        result = db.execute(
            "DELETE FROM quick_reminders WHERE id = ? AND user_id = ?",
            (reminder_id, user_id)
        )
        return result.rowcount > 0


def snooze_reminder(reminder_id, user_id, new_remind_at):
    """Snooze a reminder to a new time."""
    ensure_quick_reminders_table()
    with get_db_context() as db:
        result = db.execute(
            "UPDATE quick_reminders SET remind_at = ? WHERE id = ? AND user_id = ?",
            (new_remind_at, reminder_id, user_id)
        )
        return result.rowcount > 0


# ============================================================================
# QUICK FAVORITES / SHORTCUTS
# ============================================================================

def ensure_quick_favorites_table():
    """Ensure the quick_favorites table exists."""
    if not table_exists('quick_favorites'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS quick_favorites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    label TEXT NOT NULL,
                    url TEXT NOT NULL,
                    icon TEXT DEFAULT 'fa-star',
                    color TEXT DEFAULT 'blue',
                    sort_order INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_favorites_user ON quick_favorites(user_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_favorites_order ON quick_favorites(user_id, sort_order)")
            db.commit()


def get_user_favorites(user_id):
    """Get all favorites for a user."""
    ensure_quick_favorites_table()
    return get_all(
        "SELECT * FROM quick_favorites WHERE user_id = ? AND is_active = 1 ORDER BY sort_order ASC",
        (user_id,)
    )


def create_favorite(user_id, label, url, icon='fa-star', color='blue', sort_order=0):
    """Create a new favorite shortcut."""
    ensure_quick_favorites_table()
    with get_db_context() as db:
        db.execute(
            """INSERT INTO quick_favorites (user_id, label, url, icon, color, sort_order)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, label, url, icon, color, sort_order)
        )
        fav_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    return fav_id


def update_favorite(favorite_id, user_id, label=None, url=None, icon=None, color=None, sort_order=None):
    """Update an existing favorite."""
    ensure_quick_favorites_table()
    fields = []
    params = []
    
    if label is not None:
        fields.append("label = ?")
        params.append(label)
    if url is not None:
        fields.append("url = ?")
        params.append(url)
    if icon is not None:
        fields.append("icon = ?")
        params.append(icon)
    if color is not None:
        fields.append("color = ?")
        params.append(color)
    if sort_order is not None:
        fields.append("sort_order = ?")
        params.append(sort_order)
    
    if not fields:
        return False
    
    params.extend([favorite_id, user_id])
    
    with get_db_context() as db:
        result = db.execute(
            f"UPDATE quick_favorites SET {', '.join(fields)} WHERE id = ? AND user_id = ?",
            params
        )
        return result.rowcount > 0


def delete_favorite(favorite_id, user_id):
    """Delete a favorite."""
    ensure_quick_favorites_table()
    with get_db_context() as db:
        result = db.execute(
            "UPDATE quick_favorites SET is_active = 0 WHERE id = ? AND user_id = ?",
            (favorite_id, user_id)
        )
        return result.rowcount > 0


def reorder_favorites(user_id, favorite_orders):
    """
    Reorder favorites. favorite_orders is a list of dicts: [{id: 1, sort_order: 0}, {id: 2, sort_order: 1}, ...]
    """
    ensure_quick_favorites_table()
    with get_db_context() as db:
        for item in favorite_orders:
            db.execute(
                "UPDATE quick_favorites SET sort_order = ? WHERE id = ? AND user_id = ?",
                (item['sort_order'], item['id'], user_id)
            )
        db.commit()
    return True


# ============================================================================
# QUICK TOOL PREFERENCES
# ============================================================================

def ensure_quick_preferences_table():
    """Ensure the quick_tool_preferences table exists."""
    if not table_exists('quick_tool_preferences'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS quick_tool_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    default_tool TEXT DEFAULT 'calculator',
                    panel_size TEXT DEFAULT 'normal',
                    notes_autosave INTEGER DEFAULT 1,
                    show_favorites INTEGER DEFAULT 1,
                    show_calculator INTEGER DEFAULT 1,
                    show_notes INTEGER DEFAULT 1,
                    show_tasks INTEGER DEFAULT 1,
                    show_issues INTEGER DEFAULT 1,
                    show_reminders INTEGER DEFAULT 1,
                    calculator_history INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_qt_prefs_user ON quick_tool_preferences(user_id)")
            db.commit()


def get_quick_preferences(user_id):
    """Get quick tool preferences for a user."""
    ensure_quick_preferences_table()
    prefs = get_one(
        "SELECT * FROM quick_tool_preferences WHERE user_id = ?",
        (user_id,)
    )
    if not prefs:
        # Create default preferences
        with get_db_context() as db:
            db.execute(
                "INSERT INTO quick_tool_preferences (user_id) VALUES (?)",
                (user_id,)
            )
        prefs = get_one(
            "SELECT * FROM quick_tool_preferences WHERE user_id = ?",
            (user_id,)
        )
    return prefs


def update_quick_preferences(user_id, **kwargs):
    """Update quick tool preferences."""
    ensure_quick_preferences_table()
    
    valid_fields = [
        'default_tool', 'panel_size', 'notes_autosave', 'show_favorites',
        'show_calculator', 'show_notes', 'show_tasks', 'show_issues',
        'show_reminders', 'calculator_history'
    ]
    
    fields = []
    params = []
    
    for key, value in kwargs.items():
        if key in valid_fields:
            fields.append(f"{key} = ?")
            params.append(value)
    
    if not fields:
        return False
    
    fields.append("updated_at = CURRENT_TIMESTAMP")
    params.append(user_id)
    
    with get_db_context() as db:
        existing = db.execute(
            "SELECT id FROM quick_tool_preferences WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        
        if existing:
            result = db.execute(
                f"UPDATE quick_tool_preferences SET {', '.join(fields)} WHERE user_id = ?",
                params
            )
        else:
            db.execute(
                f"INSERT INTO quick_tool_preferences (user_id, {', '.join(fields[:-1])}) VALUES (?, {', '.join(['?' for _ in fields])})",
                [user_id] + params[:-1]
            )
            result = db.execute("SELECT 1")  # Fake result
    
    return True


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_quick_tools_schema():
    """Initialize all quick tools tables."""
    ensure_quick_notes_table()
    ensure_quick_reminders_table()
    ensure_quick_favorites_table()
    ensure_quick_preferences_table()
    
    # Seed default favorites for new users
    seed_default_favorites()


def seed_default_favorites():
    """Seed default favorites for users who don't have any."""
    # This will be called when needed, not automatically
    pass


def get_default_favorites_for_user(user_id):
    """Get default favorites to seed for a new user."""
    return [
        {'label': 'Dashboard', 'url': '/dashboard', 'icon': 'fa-home', 'color': 'blue'},
        {'label': 'Task Center', 'url': '/tasks/dashboard', 'icon': 'fa-tasks', 'color': 'green'},
        {'label': 'Issue Tracker', 'url': '/issues', 'icon': 'fa-bug', 'color': 'red'},
    ]


# ============================================================================
# USAGE ANALYTICS & REPORTING
# ============================================================================

def ensure_usage_tracking_table():
    """Ensure the tool_usage_tracking table exists for analytics."""
    if not table_exists('tool_usage_tracking'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS tool_usage_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    tool_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX IF NOT EXISTS idx_usage_user ON tool_usage_tracking(user_id)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_usage_tool ON tool_usage_tracking(tool_name)")
            db.execute("CREATE INDEX IF NOT EXISTS idx_usage_date ON tool_usage_tracking(created_at)")
            db.commit()


def track_tool_usage(user_id, tool_name, action, metadata=None):
    """Track tool usage for analytics."""
    ensure_usage_tracking_table()
    with get_db_context() as db:
        import json
        meta_str = json.dumps(metadata) if metadata else None
        db.execute(
            "INSERT INTO tool_usage_tracking (user_id, tool_name, action, metadata) VALUES (?, ?, ?, ?)",
            (user_id, tool_name, action, meta_str)
        )


def get_usage_analytics(user_id=None, days=30):
    """Get usage analytics - most used tools, frequency, active users."""
    ensure_usage_tracking_table()
    import json

    date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

    # Tool usage counts
    tool_usage = get_all("""
        SELECT tool_name, COUNT(*) as usage_count
        FROM tool_usage_tracking
        WHERE created_at >= ?
        GROUP BY tool_name
        ORDER BY usage_count DESC
    """, (date_from,))

    # Daily usage trend
    daily_usage = get_all("""
        SELECT DATE(created_at) as date, COUNT(*) as count
        FROM tool_usage_tracking
        WHERE created_at >= ?
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        LIMIT 30
    """, (date_from,))

    # Active users count
    active_users = get_one("""
        SELECT COUNT(DISTINCT user_id) as active_users
        FROM tool_usage_tracking
        WHERE created_at >= ?
    """, (date_from,))

    # Peak hours
    peak_hours = get_all("""
        SELECT strftime('%H', created_at) as hour, COUNT(*) as count
        FROM tool_usage_tracking
        WHERE created_at >= ?
        GROUP BY hour
        ORDER BY count DESC
        LIMIT 5
    """, (date_from,))

    # Per-user stats if admin
    user_stats = []
    if user_id is not None:
        user_stats = get_all("""
            SELECT tool_name, action, COUNT(*) as count
            FROM tool_usage_tracking
            WHERE user_id = ? AND created_at >= ?
            GROUP BY tool_name, action
            ORDER BY count DESC
        """, (user_id, date_from,))

    return {
        'tool_usage': tool_usage,
        'daily_usage': daily_usage,
        'active_users': active_users['active_users'] if active_users else 0,
        'peak_hours': peak_hours,
        'user_stats': user_stats,
        'period_days': days
    }


def get_notes_report(user_id=None, days=30):
    """Get notes analytics - by category, recent, shared, archive stats."""
    ensure_quick_notes_table()
    date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

    # Notes by color/category
    by_color = get_all("""
        SELECT color, COUNT(*) as count
        FROM quick_notes
        WHERE created_at >= ?
        GROUP BY color
        ORDER BY count DESC
    """, (date_from,))

    # Recent notes
    recent = get_all("""
        SELECT * FROM quick_notes
        ORDER BY updated_at DESC
        LIMIT 10
    """) if user_id else []

    # Pinned vs unpinned
    pinned_stats = get_one("""
        SELECT
            SUM(CASE WHEN is_pinned = 1 THEN 1 ELSE 0 END) as pinned_count,
            SUM(CASE WHEN is_pinned = 0 THEN 1 ELSE 0 END) as unpinned_count,
            COUNT(*) as total
        FROM quick_notes
        WHERE user_id = ?
    """, (user_id,)) if user_id else {'pinned_count': 0, 'unpinned_count': 0, 'total': 0}

    return {
        'by_color': by_color,
        'recent_notes': recent,
        'pinned_count': pinned_stats['pinned_count'] or 0,
        'unpinned_count': pinned_stats['unpinned_count'] or 0,
        'total_notes': pinned_stats['total'] or 0,
        'period_days': days
    }


def get_tasks_report(user_id=None, days=30):
    """Get task analytics - completion rates, overdue, productivity."""
    date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

    # Task completion stats
    completion_stats = get_one("""
        SELECT
            COUNT(*) as total_created,
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status != 'Completed' AND due_at < CURRENT_TIMESTAMP THEN 1 ELSE 0 END) as overdue,
            SUM(CASE WHEN status != 'Completed' AND due_at >= CURRENT_TIMESTAMP THEN 1 ELSE 0 END) as pending
        FROM task_items
        WHERE created_at >= ?
    """, (date_from,)) if table_exists('task_items') else {'total_created': 0, 'completed': 0, 'overdue': 0, 'pending': 0}

    # Priority distribution
    priority_dist = get_all("""
        SELECT priority, COUNT(*) as count
        FROM task_items
        WHERE created_at >= ?
        GROUP BY priority
        ORDER BY count DESC
    """, (date_from,)) if table_exists('task_items') else []

    # Completion rate
    completion_rate = 0
    if completion_stats['total_created'] > 0:
        completion_rate = round((completion_stats['completed'] / completion_stats['total_created']) * 100, 1)

    return {
        'total_created': completion_stats['total_created'] or 0,
        'completed': completion_stats['completed'] or 0,
        'overdue': completion_stats['overdue'] or 0,
        'pending': completion_stats['pending'] or 0,
        'completion_rate': completion_rate,
        'priority_distribution': priority_dist,
        'period_days': days
    }


def get_reminders_report(user_id=None, days=30):
    """Get reminder analytics - fulfillment, snooze frequency, overdue."""
    ensure_quick_reminders_table()
    date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')

    # Reminder stats
    reminder_stats = get_one("""
        SELECT
            COUNT(*) as total_created,
            SUM(CASE WHEN is_done = 1 THEN 1 ELSE 0 END) as fulfilled,
            SUM(CASE WHEN is_done = 0 AND remind_at < CURRENT_TIMESTAMP THEN 1 ELSE 0 END) as overdue,
            SUM(CASE WHEN is_done = 0 AND remind_at >= CURRENT_TIMESTAMP THEN 1 ELSE 0 END) as upcoming
        FROM quick_reminders
        WHERE created_at >= ?
    """, (date_from,))

    # Snooze frequency (if we had snooze tracking - use as proxy)
    snooze_stats = get_one("""
        SELECT COUNT(*) as snooze_count
        FROM quick_reminders
        WHERE created_at >= ? AND is_done = 0
    """, (date_from,))

    # Fulfillment rate
    fulfillment_rate = 0
    if reminder_stats['total_created'] > 0:
        fulfillment_rate = round((reminder_stats['fulfilled'] / reminder_stats['total_created']) * 100, 1)

    return {
        'total_created': reminder_stats['total_created'] or 0,
        'fulfilled': reminder_stats['fulfilled'] or 0,
        'overdue': reminder_stats['overdue'] or 0,
        'upcoming': reminder_stats['upcoming'] or 0,
        'fulfillment_rate': fulfillment_rate,
        'snooze_count': snooze_stats['snooze_count'] if snooze_stats else 0,
        'period_days': days
    }
