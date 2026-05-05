import sqlite3
conn = sqlite3.connect('warehouse.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name')
for r in cur.fetchall():
    print(r[0])
conn.close()