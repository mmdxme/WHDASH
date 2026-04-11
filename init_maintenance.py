"""
Initialize Maintenance Management Tables
========================================
Creates all maintenance management tables in the database.
"""

import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from maintenance_models import init_maintenance_tables, get_db

def initialize_tables():
    """Initialize all maintenance tables."""
    print("Initializing maintenance management tables...")
    conn = get_db()
    cursor = conn.cursor()

    # Check existing tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'maintenance_%'")
    existing = [row['name'] for row in cursor.fetchall()]
    print(f"Existing maintenance tables: {existing}")

    conn.close()

    # Initialize tables
    init_maintenance_tables()

    # Verify
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'maintenance_%'")
    tables = [row['name'] for row in cursor.fetchall()]
    print(f"Created maintenance tables: {tables}")
    conn.close()

    print("Maintenance tables initialized successfully!")

if __name__ == '__main__':
    initialize_tables()
