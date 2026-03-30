import sqlite3
import os

DATABASE = 'warehouse.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if os.path.exists(DATABASE):
        print(f"Database '{DATABASE}' already exists. Skipping initialization.")
        return
        
    print(f"Creating database '{DATABASE}' from schema...")
    with get_db() as db:
        with open('sqlite_schema.sql', 'r') as f:
            # Execute multiple statements
            script = f.read()
            db.executescript(script)
        db.commit()
    print("Database built successfully!")

if __name__ == '__main__':
    init_db()
