import sqlite3

def migrate():
    conn = sqlite3.connect('warehouse.db')
    cursor = conn.cursor()
    
    # Create vitalities table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vitalities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) NOT NULL
        )
    ''')
    
    # Check if vitality_id exists in parts
    cursor.execute("PRAGMA table_info(parts)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'vitality_id' not in columns:
        print("Adding vitality_id to parts table...")
        cursor.execute("ALTER TABLE parts ADD COLUMN vitality_id INTEGER REFERENCES vitalities(id) ON DELETE SET NULL")
    
    # Seed some initial vitalities
    cursor.execute("SELECT COUNT(*) FROM vitalities")
    if cursor.fetchone()[0] == 0:
        print("Seeding initial vitalities...")
        for v in ['Fast Moving', 'Slow Moving', 'Dead Stock', 'Critical']:
            cursor.execute("INSERT INTO vitalities (name) VALUES (?)", (v,))
            
    conn.commit()
    conn.close()
    print("Migration complete!")

if __name__ == '__main__':
    migrate()
