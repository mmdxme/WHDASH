import sqlite3
conn = sqlite3.connect('warehouse.db')
cursor = conn.cursor()

# Add role_name column if not exists
try:
    cursor.execute("ALTER TABLE hr_employees ADD COLUMN role_name TEXT")
    print("Added role_name column")
except Exception as e:
    print(f"role_name column: {e}")

# Add source_system column if not exists
try:
    cursor.execute("ALTER TABLE hr_employees ADD COLUMN source_system TEXT DEFAULT 'manual'")
    print("Added source_system column")
except Exception as e:
    print(f"source_system column: {e}")

# Add last_synced_at column if not exists
try:
    cursor.execute("ALTER TABLE hr_employees ADD COLUMN last_synced_at TEXT")
    print("Added last_synced_at column")
except Exception as e:
    print(f"last_synced_at column: {e}")

conn.commit()
conn.close()
print("Done!")
