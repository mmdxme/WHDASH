"""Check all tables and find empty ones - PowerShell compatible"""
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
print("EMPTY TABLES LIST:")
print("=" * 60)
for t in empty_tables:
    print(f"  - {t}")

# Also show non-empty tables with low counts
print()
print("=" * 60)
print("TABLES WITH LOW ROW COUNTS (< 10 rows):")
print("=" * 60)
for table, count in all_tables:
    if 0 < count < 10:
        print(f"  {table:45} | {count} rows")

conn.close()
