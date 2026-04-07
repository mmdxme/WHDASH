import sqlite3
import json

conn = sqlite3.connect('warehouse.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Check all tables for any employee/user data
print("=== Checking all tables for employee/user data ===\n")

# Get all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cur.fetchall()]

for table in tables:
    try:
        # Get sample data
        rows = cur.execute(f'SELECT * FROM "{table}" LIMIT 3').fetchall()
        if rows:
            # Check if it has name/employee/user related columns
            columns = rows[0].keys()
            relevant_cols = [c for c in columns if any(x in c.lower() for x in ['name', 'employee', 'user', 'staff', 'first', 'last'])]
            if relevant_cols:
                print(f"Table: {table}")
                print(f"  Relevant columns: {relevant_cols}")
                print(f"  Sample row(s):")
                for row in rows[:2]:
                    sample = {c: row[c] for c in relevant_cols}
                    print(f"    {sample}")
                print()
    except Exception as e:
        pass

# Specifically check users table
print("\n=== Users Table ===")
try:
    users = cur.execute('SELECT * FROM users LIMIT 10').fetchall()
    if users:
        for u in users:
            print(dict(u))
    else:
        print("No users found")
except Exception as e:
    print(f"Error: {e}")

# Check roles
print("\n=== Roles Table ===")
try:
    roles = cur.execute('SELECT * FROM roles LIMIT 10').fetchall()
    if roles:
        for r in roles:
            print(dict(r))
    else:
        print("No roles found")
except Exception as e:
    print(f"Error: {e}")

# Check hr_employees
print("\n=== hr_employees ===")
hr_emp = cur.execute('SELECT * FROM hr_employees LIMIT 10').fetchall()
print(f"Count: {len(hr_emp)}")
if hr_emp:
    for e in hr_emp:
        print(dict(e))
else:
    print("Empty")

conn.close()
