import sqlite3
conn = sqlite3.connect('warehouse.db')
cur = conn.cursor()

# Check for orphan warehouses (warehouses with company_id not in companies)
cur.execute('''
    SELECT w.id, w.name, w.company_id, c.name
    FROM warehouses w
    LEFT JOIN companies c ON w.company_id = c.id
''')
print('All warehouses:')
for row in cur.fetchall():
    print(' ', row)

# Check companies
cur.execute('SELECT id, name FROM companies')
print('\nCompanies:')
for row in cur.fetchall():
    print(' ', row)

# Check the exact query used in admin_warehouses
print('\nJOIN query result:')
cur.execute('''
    SELECT w.*, c.name as company_name
    FROM warehouses w
    JOIN companies c ON w.company_id = c.id
    ORDER BY c.name, w.name
''')
for row in cur.fetchall():
    print(' ', row)
conn.close()
