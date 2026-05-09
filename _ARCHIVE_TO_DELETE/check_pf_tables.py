import sqlite3
conn = sqlite3.connect('warehouse.db')
cur = conn.cursor()

# Check pf_ tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'pf_%'")
pf_tables = [t[0] for t in cur.fetchall()]
print('PF tables:', pf_tables)

# Check if users table exists
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
users = cur.fetchone()
print('Users table exists:', users is not None)

conn.close()