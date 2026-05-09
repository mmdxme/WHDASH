import sqlite3

def migrate():
    conn = sqlite3.connect('warehouse.db')
    c = conn.cursor()
    
    # Update parts table with detailed dimensions
    # SQLite doesn't support 'IF NOT EXISTS' for columns in ALTER TABLE directly through SQL in all versions
    # but we can check if they exist first.
    
    c.execute("PRAGMA table_info(parts)")
    columns = [row[1] for row in c.fetchall()]
    
    if 'length' not in columns:
        c.execute("ALTER TABLE parts ADD COLUMN length REAL DEFAULT 0.0")
    if 'width' not in columns:
        c.execute("ALTER TABLE parts ADD COLUMN width REAL DEFAULT 0.0")
    if 'height' not in columns:
        c.execute("ALTER TABLE parts ADD COLUMN height REAL DEFAULT 0.0")
        
    # Create locations table
    c.execute("""
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_code TEXT NOT NULL UNIQUE,
        charge_rate REAL DEFAULT 0.0,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Seed some default locations if empty using the 5-tier format
    c.execute("SELECT COUNT(*) FROM locations")
    if c.fetchone()[0] == 0:
        default_locations = [
            ("01-01-01-01-A", 10.50),
            ("01-01-01-02-B", 12.00),
            ("02-10-05-22-C", 15.75)
        ]
        c.executemany("INSERT INTO locations (location_code, charge_rate) VALUES (?, ?)", default_locations)
    
    conn.commit()
    conn.close()
    print("Migration successful.")

if __name__ == "__main__":
    migrate()
