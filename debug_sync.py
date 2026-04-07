from hr_sync import HREmployeeSyncManager
import sqlite3

# Fetch employees
manager = HREmployeeSyncManager()
employees = manager.fetch_all_employees()

print('First 5 employees from API:')
for emp in employees[:5]:
    print('  ID:', emp.get('id'))
    print('  Name:', emp.get('name'))
    print('  Email:', emp.get('email'))
    print('  Active:', emp.get('active'))
    print()

# Now check what our DB has
conn = sqlite3.connect('warehouse.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print('DB employees:')
cur.execute('SELECT id, employee_code, first_name, last_name, email FROM hr_employees')
for r in cur.fetchall():
    print(' ', dict(r))

# Check what the sync would match
print('\nChecking matches:')
for emp in employees[:5]:
    emp_id = emp.get('id', '')
    email = emp.get('email', '')
    cur.execute('SELECT id FROM hr_employees WHERE employee_code = ? OR email = ?', (emp_id, email))
    existing = cur.fetchone()
    if existing:
        print(f'  {emp.get("name")} -> matches existing ID {existing["id"]}')
    else:
        print(f'  {emp.get("name")} -> NO MATCH (will insert)')

conn.close()
