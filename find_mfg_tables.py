import sqlite3
conn = sqlite3.connect('warehouse.db')
cur = conn.cursor()

# Find manufacturing-related tables
tables_to_check = ['mfg_production_orders', 'mfg_work_centers', 'mfg_bom', 'mfg_schedule', 'mfg_downtime', 'mfg_quality_inspections']
for t in tables_to_check:
    cur.execute(f"PRAGMA table_info({t})")
    cols = [col[1] for col in cur.fetchall()]
    print(f"{t}: {cols}")

print()

# Find all mfg_ tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'mfg%'")
print("All mfg_ tables:")
for r in cur.fetchall():
    print(f"  {r[0]}")

print()

# Check for product-like table
print("Looking for product table references in manufacturing_routes...")
with open('manufacturing_routes.py', 'r') as f:
    content = f.read()

# Find all table references (JOINs and FROMs)
import re
joins = re.findall(r'(?:LEFT JOIN|RIGHT JOIN|INNER JOIN|FROM)\s+(\w+)', content, re.IGNORECASE)
unique_joins = sorted(set(joins))
print("All table references:")
for j in unique_joins:
    print(f"  {j}")

conn.close()