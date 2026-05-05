"""Check database state"""
import sqlite3
import os

DATABASE = 'warehouse.db'
conn = sqlite3.connect(DATABASE)
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('PRAGMA foreign_keys=ON')
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]
print(f'Total tables: {len(tables)}')
print()
for t in tables:
    try:
        count = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        print(f'{t}: {count} rows')
    except:
        print(f'{t}: ERROR')
conn.close()
