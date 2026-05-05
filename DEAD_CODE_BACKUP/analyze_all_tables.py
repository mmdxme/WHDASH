"""Analyze all tables in the database to find empty/underpopulated tables."""
import sqlite3
import os

DATABASE = 'warehouse.db'

conn = sqlite3.connect(DATABASE)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get all tables
cur.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name')
tables = [r[0] for r in cur.fetchall()]

# Skip sqlite internal tables
tables = [t for t in tables if not t.startswith('sqlite_')]

print(f"Total tables: {len(tables)}")
print("=" * 80)

results = []

for table in tables:
    try:
        cur.execute(f'SELECT COUNT(*) as cnt FROM "{table}"')
        count = cur.fetchone()[0]

        # Get column count
        cur.execute(f'PRAGMA table_info("{table}")')
        cols = cur.fetchall()
        col_count = len(cols)

        results.append((table, count, col_count))
    except Exception as e:
        results.append((table, -1, 0))

conn.close()

# Sort by count ascending (empty first)
results.sort(key=lambda x: x[1])

# Categorize
empty_tables = [r for r in results if r[1] == 0]
tiny_tables = [r for r in results if 0 < r[1] < 10]
small_tables = [r for r in results if 10 <= r[1] < 50]
medium_tables = [r for r in results if 50 <= r[1] < 100]
large_tables = [r for r in results if r[1] >= 100]

print(f"\nEmpty tables (0 records): {len(empty_tables)}")
print(f"Tiny tables (1-9 records): {len(tiny_tables)}")
print(f"Small tables (10-49 records): {len(small_tables)}")
print(f"Medium tables (50-99 records): {len(medium_tables)}")
print(f"Large tables (100+ records): {len(large_tables)}")

print("\n" + "=" * 80)
print("EMPTY TABLES (Need seeding):")
print("=" * 80)
for t, cnt, cols in empty_tables:
    print(f"  {t} ({cols} columns)")

print("\n" + "=" * 80)
print("TINY TABLES (Need more data):")
print("=" * 80)
for t, cnt, cols in tiny_tables[:50]:  # Show first 50
    print(f"  {t}: {cnt} records")

if len(tiny_tables) > 50:
    print(f"  ... and {len(tiny_tables) - 50} more")

print("\n" + "=" * 80)
print("SMALL TABLES (Need more data):")
print("=" * 80)
for t, cnt, cols in small_tables[:50]:  # Show first 50
    print(f"  {t}: {cnt} records")

if len(small_tables) > 50:
    print(f"  ... and {len(small_tables) - 50} more")

# Save detailed report
with open('table_analysis.txt', 'w', encoding='utf-8') as f:
    f.write("MMDx Table Analysis Report\n")
    f.write("=" * 80 + "\n\n")

    f.write(f"Total tables: {len(tables)}\n")
    f.write(f"Empty tables: {len(empty_tables)}\n")
    f.write(f"Tiny tables: {len(tiny_tables)}\n")
    f.write(f"Small tables: {len(small_tables)}\n")
    f.write(f"Medium tables: {len(medium_tables)}\n")
    f.write(f"Large tables: {len(large_tables)}\n\n")

    f.write("EMPTY TABLES:\n")
    for t, cnt, cols in empty_tables:
        f.write(f"  {t} ({cols} columns)\n")

    f.write("\n\nTINY TABLES (1-9 records):\n")
    for t, cnt, cols in tiny_tables:
        f.write(f"  {t}: {cnt} records, {cols} columns\n")

    f.write("\n\nSMALL TABLES (10-49 records):\n")
    for t, cnt, cols in small_tables:
        f.write(f"  {t}: {cnt} records, {cols} columns\n")

    f.write("\n\nMEDIUM TABLES (50-99 records):\n")
    for t, cnt, cols in medium_tables:
        f.write(f"  {t}: {cnt} records, {cols} columns\n")

    f.write("\n\nLARGE TABLES (100+ records):\n")
    for t, cnt, cols in large_tables:
        f.write(f"  {t}: {cnt} records, {cols} columns\n")

print("\nReport saved to table_analysis.txt")