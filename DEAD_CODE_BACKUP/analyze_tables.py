"""Check all table counts"""
import sqlite3
import os

DATABASE = 'warehouse.db'
conn = sqlite3.connect(DATABASE)
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('PRAGMA foreign_keys=ON')
conn.row_factory = sqlite3.Row

# Get all tables
tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]

# Group by prefix
groups = {}
for t in tables:
    prefix = t.split('_')[0] if '_' in t else t
    if prefix not in groups:
        groups[prefix] = []
    groups[prefix].append(t)

# Print grouped
print("=" * 80)
print("TABLES GROUPED BY PREFIX")
print("=" * 80)
for prefix, tables_list in sorted(groups.items()):
    print(f"\n[{prefix}] ({len(tables_list)} tables)")
    for t in tables_list:
        try:
            count = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
            status = "OK" if count > 0 else "EMPTY"
            print(f"  {t}: {count} rows [{status}]")
        except Exception as e:
            print(f"  {t}: ERROR - {e}")

conn.close()
