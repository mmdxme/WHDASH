import sqlite3
conn = sqlite3.connect('warehouse.db')
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM payroll_components")
print("Count:", cur.fetchone()[0])
cur.execute("SELECT * FROM payroll_components LIMIT 5")
for row in cur.fetchall():
    print(row)
conn.close()