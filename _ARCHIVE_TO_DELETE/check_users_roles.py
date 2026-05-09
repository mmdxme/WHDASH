import sqlite3
conn = sqlite3.connect('warehouse.db')
cur = conn.cursor()

# Check users
cur.execute("SELECT id, username, role_id FROM users LIMIT 5")
users = cur.fetchall()
print('Users:', users)

# Check role_permissions for finance
cur.execute("SELECT * FROM role_permissions WHERE permission LIKE '%finance%dashboard%' LIMIT 10")
perms = cur.fetchall()
print('Finance dashboard permissions:', perms)

# Check roles
cur.execute("SELECT * FROM roles LIMIT 5")
roles = cur.fetchall()
print('Roles:', roles)

conn.close()