import sqlite3
conn = sqlite3.connect('warehouse.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Get all peyvast_products sorted by current_stock desc
cur.execute('SELECT * FROM peyvast_products ORDER BY current_stock DESC')
rows = cur.fetchall()

print(f'Total: {len(rows)} items')
print()
for i, row in enumerate(rows, 1):
    pn = row['part_number']
    desc = row['description'][:40] if row['description'] else 'N/A'
    stock = row['current_stock']
    brand = row['brand'] or 'N/A'
    warehouse = row['warehouse_name'] or 'N/A'
    print(f'[{i}] {pn} | {desc} | Stock: {stock} | Brand: {brand} | WH: {warehouse}')

conn.close()
