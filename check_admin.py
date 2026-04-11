import sqlite3
conn = sqlite3.connect('C:/Users/sdads/MMDx/warehouse.db')
row = conn.execute("SELECT id, username, email, role_id FROM users WHERE username='admin' LIMIT 1").fetchone()
print("Admin user:", row)

# Also check what password hash looks like
pw_row = conn.execute("SELECT password FROM users WHERE username='admin' LIMIT 1").fetchone()
if pw_row:
    print("Password hash:", pw_row[0][:60] if pw_row[0] else "None")
conn.close()