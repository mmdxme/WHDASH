import sqlite3
conn = sqlite3.connect('warehouse.db')
cur = conn.cursor()

# Check all tables that have product_id column
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]

product_id_tables = []
for t in tables:
    cur.execute(f"PRAGMA table_info({t})")
    cols = [col[1] for col in cur.fetchall()]
    if 'product_id' in cols:
        product_id_tables.append(t)

print(f"Tables with product_id column ({len(product_id_tables)}):")
for t in sorted(product_id_tables):
    print(f"  {t}")

print()

# For mfg_production_orders, check what values are in product_id
cur.execute("SELECT DISTINCT product_id FROM mfg_production_orders WHERE product_id IS NOT NULL ORDER BY product_id LIMIT 20")
product_ids = [r[0] for r in cur.fetchall()]
print(f"product_id values in mfg_production_orders: {product_ids}")

# Check if those values exist in sdad_products
if product_ids:
    placeholders = ','.join('?' * len(product_ids))
    cur.execute(f"SELECT id, product_code, name FROM sdad_products WHERE id IN ({placeholders})", product_ids)
    print(f"Matching sdad_products: {cur.fetchall()}")

    # Also check wms_items
    cur.execute(f"SELECT id, item_code, name FROM wms_items WHERE id IN ({placeholders})", product_ids)
    print(f"Matching wms_items: {cur.fetchall()}")

conn.close()