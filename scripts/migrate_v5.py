import sqlite3

def migrate():
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    
    # Check if company_id already exists
    cursor.execute("PRAGMA table_info(locations)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'company_id' not in columns:
        print("Adding company_id column to locations...")
        cursor.execute("ALTER TABLE locations ADD COLUMN company_id INTEGER REFERENCES companies(id)")
        conn.commit()
    else:
        print("company_id column already exists.")

    print("Migration complete.")
    conn.close()

if __name__ == "__main__":
    migrate()
