import sqlite3
conn = sqlite3.connect('warehouse.db')
cur = conn.cursor()

# Test the original query that was failing
print("Testing original query:")
result = cur.execute('''
    SELECT o.*, p.name as product_name, w.name as work_center_name
    FROM mfg_production_orders o
    LEFT JOIN products p ON o.product_id = p.id
    LEFT JOIN mfg_work_centers w ON o.work_center_id = w.id
    ORDER BY o.created_at DESC
    LIMIT 5
''').fetchall()
print(f"Got {len(result)} rows")
for r in result:
    print(f"  order: {r[1]}, product: {r[-2]}, work_center: {r[-1]}")

print()

# Test order form query
print("Testing order form query:")
products = cur.execute('SELECT id, name, code FROM products ORDER BY name').fetchall()
print(f"Got {len(products)} products")
for p in products[:3]:
    print(f"  {p}")

conn.close()
print("\nAll queries work!")