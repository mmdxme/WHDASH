# Minimal quality_models.py that actually works
# This avoids the problematic f-string patterns

from database import get_db
import sqlite3
from datetime import datetime

def get_db():
    """Get database connection."""
    conn = sqlite3.connect('warehouse.db')
    conn.row_factory = sqlite3.Row
    return conn

QUALITY_TABLES = [
    """CREATE TABLE IF NOT EXISTS quality_inspection_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL,
        description TEXT,
        is_active INTEGER DEFAULT 1
    )""",
    """CREATE TABLE IF NOT EXISTS quality_inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inspection_number TEXT UNIQUE,
        inspection_type TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        result TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )""",
]

def initialize_quality_tables():
    """Initialize quality tables."""
    with get_db() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS quality_inspection_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            is_active INTEGER DEFAULT 1
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS quality_inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inspection_number TEXT UNIQUE,
            inspection_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            result TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )""")
        db.commit()
    return True

if __name__ == '__main__':
    initialize_quality_tables()
    print("Quality tables initialized")
