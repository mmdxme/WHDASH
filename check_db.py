import sqlite3
import json

db_path = 'warehouse.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()

with open('schema.txt', 'w') as f:
    for t in tables:
        f.write(f"--- Table: {t['name']} ---\n")
        f.write(f"{t['sql']}\n\n")

conn.close()
