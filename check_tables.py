import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='suppliers';")
print('suppliers:', c.fetchone())

c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vehicles';")
print('vehicles:', c.fetchone())
