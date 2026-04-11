from werkzeug.security import check_password_hash
import sqlite3
conn = sqlite3.connect('warehouse.db')
conn.row_factory = sqlite3.Row
user = conn.execute("SELECT password FROM users WHERE username='admin'").fetchone()
print('Hash:', user['password'][:60])
print('check_password_hash works:', check_password_hash(user['password'], 'admin123'))