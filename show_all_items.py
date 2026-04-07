import sqlite3
import json

conn = sqlite3.connect('warehouse.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute('SELECT * FROM peyvast_products ORDER BY current_stock DESC')
rows = cur.fetchall()

items = []
for row in rows:
    items.append({
        'part_number': row['part_number'],
        'description': row['description'],
        'brand': row['brand'],
        'category': row['category'],
        'warehouse_name': row['warehouse_name'],
        'stock_location': row['stock_location'],
        'current_stock': row['current_stock'],
        'min_stock': row['min_stock'],
        'max_stock': row['max_stock'],
        'initial_stock': row['initial_stock'],
        'last_purchase_price': row['last_purchase_price'],
        'last_purchase_qty': row['last_purchase_qty'],
        'last_purchase_date': row['last_purchase_date'],
        'avg_unit_cost': row['avg_unit_cost'],
        'seller_invoice_details': row['seller_invoice_details'],
    })

# Save to JSON
with open('all_items_sorted_by_stock.json', 'w', encoding='utf-8') as f:
    json.dump(items, f, ensure_ascii=False, indent=2)

print(f"Saved {len(items)} items to all_items_sorted_by_stock.json")

# Also print summary
print()
print("="*80)
print("ALL 102 ITEMS SORTED BY HIGHEST STOCK QUANTITY")
print("="*80)
print()

for i, item in enumerate(items, 1):
    print(f"{i}. {item['part_number']}")
    print(f"   Description: {item['description']}")
    print(f"   Brand: {item['brand'] or 'N/A'}")
    print(f"   Category: {item['category'] or 'N/A'}")
    print(f"   Warehouse: {item['warehouse_name'] or 'N/A'}")
    print(f"   Location: {item['stock_location'] or 'N/A'}")
    print(f"   CURRENT STOCK: {item['current_stock']}")
    print(f"   Min/Max: {item['min_stock']}/{item['max_stock']}")
    print(f"   Initial: {item['initial_stock']}")
    print(f"   Last Purchase: {item['last_purchase_qty']} x ${item['last_purchase_price']} on {item['last_purchase_date'] or 'N/A'}")
    print(f"   Avg Cost: ${item['avg_unit_cost']}")
    print(f"   Seller/Invoice: {item['seller_invoice_details'] or 'N/A'}")
    print()

conn.close()
