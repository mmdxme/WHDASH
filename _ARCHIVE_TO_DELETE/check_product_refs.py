import sqlite3
conn = sqlite3.connect('warehouse.db')
cur = conn.cursor()

# Check foreign keys on mfg_production_orders.product_id
cur.execute("PRAGMA foreign_key_list(mfg_production_orders)")
print("mfg_production_orders foreign keys:")
for r in cur.fetchall():
    print(f"  {r}")

print()
# Check foreign keys on mfg_bom.product_id
cur.execute("PRAGMA foreign_key_list(mfg_bom)")
print("mfg_bom foreign keys:")
for r in cur.fetchall():
    print(f"  {r}")

print()
# Check foreign keys on mfg_routings.product_id
cur.execute("PRAGMA foreign_key_list(mfg_routings)")
print("mfg_routings foreign keys:")
for r in cur.fetchall():
    print(f"  {r}")

print()
# Check if sdad_products has data
cur.execute("SELECT COUNT(*) FROM sdad_products")
print(f"sdad_products rows: {cur.fetchone()[0]}")
cur.execute("SELECT * FROM sdad_products LIMIT 3")
for r in cur.fetchall():
    print(f"  {r}")

print()
# Check wms_items has data
cur.execute("SELECT COUNT(*) FROM wms_items")
print(f"wms_items rows: {cur.fetchone()[0]}")
cur.execute("SELECT id, item_code, name FROM wms_items LIMIT 3")
for r in cur.fetchall():
    print(f"  {r}")

conn.close()