import sqlite3
conn = sqlite3.connect('warehouse.db')
cur = conn.cursor()

# Check all tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cur.fetchall()]
print('All tables:')
for t in tables:
    print(f'  {t}')

# Find HR-related tables
emp_tables = [t for t in tables if any(x in t.lower() for x in ['hr', 'employ', 'staff', 'personnel'])]
print('\nHR/Employee-related tables:')
for t in emp_tables:
    try:
        count = cur.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        print(f'  {t}: {count} rows')
    except Exception as e:
        print(f'  {t}: Error - {e}')

# Check what's in hr_employees
print('\n--- hr_employees sample data ---')
try:
    rows = cur.execute('SELECT * FROM hr_employees LIMIT 5').fetchall()
    if rows:
        for r in rows:
            print(dict(r))
    else:
        print('No data in hr_employees')
except Exception as e:
    print(f'Error: {e}')
