import sqlite3
conn = sqlite3.connect('warehouse.db')
cur = conn.cursor()

# Check all users and their roles
cur.execute('''
    SELECT u.id, u.username, u.role_id, r.role_name, r.can_manage_users, r.can_edit_stock
    FROM users u
    LEFT JOIN roles r ON u.role_id = r.id
''')
print('Users and their roles:')
for row in cur.fetchall():
    print(f'  User {row[0]}: {row[1]}, role_id={row[2]}, role={row[3]}, can_manage_users={row[4]}, can_edit_stock={row[5]}')

# Check all roles
print('\nAll roles:')
cur.execute('SELECT id, role_name, can_manage_users, can_edit_stock, is_system FROM roles')
for row in cur.fetchall():
    print(f'  Role {row[0]}: {row[1]}, can_manage_users={row[2]}, can_edit_stock={row[3]}, is_system={row[4]}')

conn.close()
