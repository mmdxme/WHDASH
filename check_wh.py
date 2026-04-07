import sqlite3
conn = sqlite3.connect('warehouse.db')
cur = conn.cursor()

cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='warehouses'")
print('warehouses:', cur.fetchone())

cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='companies'")
print('companies:', cur.fetchone())

cur.execute('SELECT COUNT(*) FROM warehouses')
print('wh count:', cur.fetchone()[0])

cur.execute('SELECT COUNT(*) FROM companies')
print('co count:', cur.fetchone()[0])

cur.execute('SELECT * FROM warehouses LIMIT 5')
print('warehouses:', cur.fetchall())

cur.execute("SELECT * FROM companies WHERE name != 'Holding Company' ORDER BY name LIMIT 5")
print('companies:', cur.fetchall())

conn.close()
