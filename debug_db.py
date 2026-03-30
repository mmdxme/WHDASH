import sqlite3
db = sqlite3.connect('warehouse.db')
cur = db.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print([r[0] for r in cur.fetchall()])
