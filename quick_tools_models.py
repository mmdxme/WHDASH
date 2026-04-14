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
