import sqlite3
conn = sqlite3.connect('warehouse.db')
cur = conn.cursor()

# Get role_permissions table structure
cur.execute("PRAGMA table_info(role_permissions)")
cols = cur.fetchall()
print('role_permissions columns:', cols)

# Check permissions for role_id=1 (admin)
cur.execute("SELECT * FROM role_permissions WHERE role_id=1 LIMIT 20")
perms = cur.fetchall()
print('\nRole 1 permissions:', perms)

conn.close()