"""Final check - count empty tables"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'warehouse.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
tables = cursor.fetchall()

total = len(tables)
empty = 0
all_counts = []

for (table,) in tables:
    try:
        count = cursor.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
        all_counts.append((table, count))
        if count == 0:
            empty += 1
    except:
        all_counts.append((table, "ERROR"))

print(f"Total tables: {total}")
print(f"Empty tables: {empty}")
print(f"Non-empty tables: {total - empty}")
print()

# Show all empty tables
if empty > 0:
    print("EMPTY TABLES:")
    for t, c in all_counts:
        if c == 0:
            print(f"  - {t}")

conn.close()
