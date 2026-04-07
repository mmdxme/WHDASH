import sqlite3
conn = sqlite3.connect('warehouse.db')
cur = conn.cursor()

# Check for orphan warehouses (company_id not in companies)
cur.execute('''
    SELECT w.id, w.name, w.company_id
    FROM warehouses w
    WHERE w.company_id NOT IN (SELECT id FROM companies)
''')
orphans = cur.fetchall()
print('Orphan warehouses (company_id not in companies):')
if orphans:
    for o in orphans:
        print(f'  Warehouse id={o[0]}, name={o[1]}, company_id={o[2]}')
else:
    print('  None - all warehouses have valid company_id')

# Check companies without warehouses
cur.execute('''
    SELECT c.id, c.name
    FROM companies c
    WHERE c.id NOT IN (SELECT DISTINCT company_id FROM warehouses)
''')
no_wh = cur.fetchall()
print('\nCompanies without warehouses:')
if no_wh:
    for c in no_wh:
        print(f'  Company id={c[0]}, name={c[1]}')
else:
    print('  None - all companies have at least one warehouse')

# Check the warehouses table structure
cur.execute('PRAGMA table_info(warehouses)')
print('\nWarehouses table structure:')
for col in cur.fetchall():
    print(f'  {col}')

# Check if there's an is_active column
cur.execute('PRAGMA table_info(warehouses)')
cols = [col[1] for col in cur.fetchall()]
print('\nColumns:', cols)

conn.close()
