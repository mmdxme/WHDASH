import sqlite3
conn = sqlite3.connect('warehouse.db')
cur = conn.cursor()

# Drop and recreate the view with proper column aliases
cur.execute("DROP VIEW IF EXISTS products")
cur.execute("""
CREATE VIEW products AS
SELECT
    id,
    product_code as code,
    name,
    sku,
    category,
    brand,
    warehouse_name,
    stock_location,
    quantity,
    initial_stock,
    min_stock,
    max_stock,
    unit,
    local_part_id,
    last_synced_at,
    created_at,
    updated_at
FROM sdad_products
""")
print("View 'products' recreated with 'code' column alias")

# Verify
cur.execute("PRAGMA table_info(products)")
cols = [col[1] for col in cur.fetchall()]
print(f"products view columns: {cols}")

# Test query
products = cur.execute('SELECT id, name, code FROM products ORDER BY name').fetchall()
print(f"Got {len(products)} products from products view:")
for p in products[:5]:
    print(f"  id={p[0]}, name={p[1]}, code={p[2]}")

conn.commit()
conn.close()
print("\nAll queries work!")