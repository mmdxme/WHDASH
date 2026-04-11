import sqlite3
import random

conn = sqlite3.connect('warehouse.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("Updating WMS data for dashboard display...")

# Update some locations to have inventory (is_empty = 0)
cur.execute("SELECT id FROM wms_locations LIMIT 200")
loc_ids = [r['id'] for r in cur.fetchall()]

# Mark about 30% of locations as non-empty
for loc_id in random.sample(loc_ids, min(200, len(loc_ids) // 3)):
    cur.execute('''
        UPDATE wms_locations SET is_empty = 0, current_volume_m3 = ?
        WHERE id = ?
    ''', (random.uniform(0.5, 8), loc_id))

conn.commit()
print(f"  Updated {min(200, len(loc_ids) // 3)} locations to non-empty")

# Check wms_internal_movements
cur.execute("SELECT COUNT(*) as cnt FROM wms_internal_movements")
mov_count = cur.fetchone()['cnt']
print(f"  Internal movements: {mov_count}")

# Add some internal movements if none exist
if mov_count == 0:
    print("  Creating internal movements...")
    cur.execute("SELECT id FROM wms_items LIMIT 10")
    item_ids = [r['id'] for r in cur.fetchall()]
    cur.execute("SELECT id FROM wms_warehouses")
    wh_ids = [r['id'] for r in cur.fetchall()]
    
    for i in range(50):
        cur.execute('''
            INSERT INTO wms_internal_movements 
            (movement_number, movement_type, item_id, source_location_id, destination_location_id, 
             quantity, reference_type, reference_number, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, date('now', ?))
        ''', (
            f"MOV-{i+10000:05d}",
            random.choice(['RECEIPT', 'TRANSFER', 'ISSUE', 'ADJUSTMENT']),
            random.choice(item_ids) if item_ids else 1,
            random.choice(loc_ids),
            random.choice(loc_ids),
            random.randint(1, 50),
            random.choice(['PO', 'SO', 'WO', 'Manual']),
            f"REF-{random.randint(10000, 99999)}",
            f"-{random.randint(1, 30)} days"
        ))
    conn.commit()
    print(f"  Created 50 internal movements")

# Verify near_expiry_days setting exists
cur.execute("SELECT * FROM wms_settings WHERE setting_key = 'near_expiry_days'")
if not cur.fetchone():
    cur.execute("INSERT INTO wms_settings (setting_key, setting_value) VALUES ('near_expiry_days', '30')")
    conn.commit()
    print("  Added near_expiry_days setting")

# Verify lots with expiry for near_expiry/expired counts
cur.execute("SELECT COUNT(*) as cnt FROM wms_lots")
lot_count = cur.fetchone()['cnt']
print(f"  Current lots: {lot_count}")

if lot_count == 0:
    print("  Creating lots with expiry dates...")
    cur.execute("SELECT id FROM wms_items LIMIT 15")
    item_ids = [r['id'] for r in cur.fetchall()]
    
    for i in range(30):
        from datetime import datetime, timedelta
        days_offset = random.randint(-10, 60)
        expiry = (datetime.now() + timedelta(days=days_offset)).strftime('%Y-%m-%d')
        cur.execute('''
            INSERT INTO wms_lots (item_id, lot_number, quantity, expiry_date, warehouse_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            random.choice(item_ids) if item_ids else 1,
            f"LOT-{random.randint(10000, 99999)}",
            random.randint(10, 100),
            expiry,
            random.choice(wh_ids) if wh_ids else 1
        ))
    conn.commit()
    print("  Created 30 lots with varying expiry dates")

conn.close()
print("Done!")