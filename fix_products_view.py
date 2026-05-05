import sqlite3
conn = sqlite3.connect('warehouse.db')
cur = conn.cursor()

# Fix 1: Rename sdad_products to products (or create a view)
# Check if there's already a products view
cur.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='products'")
if cur.fetchone():
    print("View 'products' already exists")
else:
    print("Creating VIEW 'products' as alias for sdad_products...")
    cur.execute("CREATE VIEW products AS SELECT id, product_code, name, sku, category, brand, warehouse_name, stock_location, quantity, initial_stock, min_stock, max_stock, unit, local_part_id FROM sdad_products")
    print("Done")

# Verify
cur.execute("SELECT name FROM sqlite_master WHERE type='view' AND name='products'")
print(f"products view exists: {cur.fetchone() is not None}")

conn.commit()
conn.close()
print("Database updated successfully!")