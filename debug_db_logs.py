import sqlite3
db = sqlite3.connect('warehouse.db')
db.row_factory = sqlite3.Row
logs = db.execute('SELECT * FROM delivery_activity_logs LIMIT 10').fetchall()
for log in logs:
    print(dict(log))
