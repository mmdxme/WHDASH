import sqlite3
conn = sqlite3.connect('warehouse.db')
cur = conn.cursor()
cur.execute("SELECT username, password FROM users")
for row in cur.fetchall():
    print(f"User: {row[0]}, Hash: {row[1][:50]}...")