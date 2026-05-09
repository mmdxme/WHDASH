import sqlite3
conn = sqlite3.connect('warehouse.db')
cur = conn.cursor()
cur.execute("SELECT id, username, email, role_id FROM users LIMIT 5")
rows = cur.fetchall()
for r in rows:
    print('User:', r)
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='marketing_user_roles'")
print('marketing_user_roles exists:', cur.fetchone() is not None)
conn.close()