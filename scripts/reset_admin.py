import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('warehouse.db')
conn.row_factory = sqlite3.Row

admin = conn.execute("SELECT id, username, password FROM users WHERE username = 'admin'").fetchone()
print('Admin user found:', admin['username'])
print('Current hash:', admin['password'][:60])

new_hash = generate_password_hash('admin123')
conn.execute("UPDATE users SET password = ? WHERE username = 'admin'", (new_hash,))
conn.commit()
print('Password reset to: admin123')

admin2 = conn.execute("SELECT id, username, password FROM users WHERE username = 'admin'").fetchone()
print('New hash:', admin2['password'][:60])