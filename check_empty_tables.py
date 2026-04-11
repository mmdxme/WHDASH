"""Check all tables and find empty ones"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'warehouse.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
tables = cursor.fetchall()

empty_tables = []
all_tables = []

for (table,) in tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
        count = cursor.fetchone()[0]
        all_tables.append((table, count))
        if count == 0:
            empty_tables.append(table)
    except Exception as e:
        all_tables.append((table, f"ERROR: {e}"))

print(f"Total tables: {len(all_tables)}")
print(f"Empty tables: {len(empty_tables)}")
print()
print("=" * 60)
print("ALL TABLES WITH ROW COUNTS:")
print("=" * 60)
for table, count in all_tables:
    if count == 0:
        print(f"  {table:45} | EMPTY")
    else:
        print(f"  {table:45} | {count} rows")

print()
print("=" * 60)
print("EMPTY TABLES LIST:")
print("=" * 60)
for t in empty_tables:
    print(f"  - {t}")

conn.close()
