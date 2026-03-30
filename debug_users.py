import sqlite3
db = sqlite3.connect('warehouse.db')
cur = db.cursor()
cur.execute("PRAGMA table_info(users)")
print(cur.fetchall())
