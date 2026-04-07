import sqlite3
conn = sqlite3.connect('warehouse.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get hr_employees schema
cur.execute("PRAGMA table_info(hr_employees)")
columns = cur.fetchall()
print("hr_employees columns:")
for col in columns:
    print(f"  {col['name']}: {col['type']}")

# Get hr_employee_employment schema
cur.execute("PRAGMA table_info(hr_employee_employment)")
columns = cur.fetchall()
print("\nhr_employee_employment columns:")
for col in columns:
    print(f"  {col['name']}: {col['type']}")

conn.close()
