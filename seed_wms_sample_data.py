"""
Seed WMS Sample Data
====================
Seeds WMS/warehouse data including warehouses, zones, locations, items, 
inventory balances, alerts, and stock movements for dashboard display.
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

DATABASE = os.path.join(os.path.dirname(__file__), 'warehouse.db')


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def seed_wms_data():
    """Seed comprehensive WMS demo data."""
    conn = get_db()
    cursor = conn.cursor()

    print("Seeding WMS sample data...")

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) as cnt FROM wms_warehouses")
    if cursor.fetchone()['cnt'] > 0:
        print("WMS data already exists, skipping...")
        conn.close()
        return

    # Get existing data
    cursor.execute("SELECT id, name FROM companies LIMIT 4")
    companies = list(cursor.fetchall())
    cursor.execute("SELECT id, name FROM parts LIMIT 30")
    parts = list(cursor.fetchall())
    cursor.execute("SELECT id FROM inventory LIMIT 50")
    inv_items = list(cursor.fetchall())

    warehouse_ids = []
    
    # Create WMS Warehouses
    print("  Creating warehouses...")
    warehouse_data = [
        ('DH001', 'Dubai Hub Warehouse', 'main', 'Dubai', 'UAE'),
        ('SH001', 'Sharjah Storage Facility', 'main', 'Sharjah', 'UAE'),
        ('AB001', 'Abu Dhabi Distribution', 'main', 'Abu Dhabi', 'UAE'),
        ('RJ001', 'Ras Al Khaimah DC', 'main', 'Ras Al Khaimah', 'UAE'),
    ]
    
    for i, (code, name, wtype, city, country) in enumerate(warehouse_data):
        company_id = companies[i]['id'] if i < len(companies) else 1
        cursor.execute('''
            INSERT INTO wms_warehouses (company_id, code, name, type, city, country, is_active)
            VALUES (?, ?, ?, ?, ?, ?, 1)
        ''', (company_id, code, name, wtype, city, country))
        warehouse_ids.append(cursor.lastrowid)

    conn.commit()

    # Create WMS Zones for each warehouse
    print("  Creating zones...")
    zone_types = ['Receiving', 'Storage', 'Picking', 'Shipping', 'Returns', 'Quarantine', 'Staging']
    zone_ids = []
    
    for wh_id in warehouse_ids:
        for ztype in zone_types:
            cursor.execute('''
                INSERT INTO wms_zones (warehouse_id, code, name, zone_type, description, is_active)
                VALUES (?, ?, ?, ?, ?, 1)
            ''', (wh_id, f"{wh_id}-{ztype[:3].upper()}", f"Zone {ztype}", ztype, f"{ztype} area"))
            zone_ids.append(cursor.lastrowid)

    conn.commit()

    # Create WMS Locations
    print("  Creating locations...")
    location_ids = []
    for wh_id in warehouse_ids:
        for zone_num in range(1, 4):
            for aisle in range(1, 6):
                for rack in range(1, 4):
                    for level in range(1, 5):
                        loc_code = f"{wh_id}-{zone_num:02d}-{aisle:02d}-{rack:02d}-{level:02d}"
                        cursor.execute('''
                            INSERT INTO wms_locations 
                            (warehouse_id, code, location_type, is_active, is_empty, 
                             capacity_volume_m3, current_volume_m3)
                            VALUES (?, ?, 'Storage', 1, 1, ?, 0)
                        ''', (wh_id, loc_code, random.uniform(1, 10)))
                        location_ids.append(cursor.lastrowid)

    conn.commit()
    print(f"    Created {len(location_ids)} locations")

    # Get location IDs for operations
    cursor.execute("SELECT id FROM wms_locations LIMIT 200")
    loc_ids = [r['id'] for r in cursor.fetchall()]

    # Create WMS Items from parts
    print("  Creating WMS items...")
    item_ids = []
    for i, part in enumerate(parts[:25]):
        item_code = f"SKU-{part['id']:05d}"
        cursor.execute('''
            INSERT INTO wms_items (item_code, name, item_type, unit_of_measure, 
                                   is_active, min_stock_level, reorder_point, safety_stock)
            VALUES (?, ?, 'finished_goods', 'PCS', 1, 5, 10, 15)
        ''', (item_code, f"Item {part['id']} - Auto Part {i+1}"))
        item_ids.append(cursor.lastrowid)

    conn.commit()
    print(f"    Created {len(item_ids)} items")

    # Create WMS Inventory Balances
    print("  Creating inventory balances...")
    statuses = ['AVAILABLE', 'RESERVED', 'BLOCKED', 'QUARANTINE']
    balance_count = 0
    for item_id in item_ids:
        for _ in range(random.randint(1, 3)):
            wh_id = random.choice(warehouse_ids)
            loc_id = random.choice(loc_ids) if loc_ids else None
            qty = random.randint(0, 200)
            status = random.choice(statuses)
            
            cursor.execute('''
                INSERT INTO wms_inventory_balances 
                (item_id, warehouse_id, location_id, quantity, reserved_quantity, 
                 blocked_quantity, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (item_id, wh_id, loc_id, qty, random.randint(0, 20) if status == 'RESERVED' else 0,
                  random.randint(0, 10) if status in ['BLOCKED', 'QUARANTINE'] else 0, status))
            balance_count += 1

    conn.commit()
    print(f"    Created {balance_count} inventory balances")

    # Create WMS Alerts
    print("  Creating alerts...")
    alert_data = [
        ('CRITICAL', 'Low Stock Alert', 'SKU-00012 below safety stock level', 'LOW_STOCK'),
        ('HIGH', 'Expiry Warning', 'Batch LOT-2024-045 expiring in 5 days', 'EXPIRY'),
        ('MEDIUM', 'Receiving Delay', 'GRN-2024-123 pending for 3 days', 'RECEIVING'),
        ('LOW', 'Location Locked', 'Location A-05-03-01 locked for inspection', 'LOCK'),
        ('MEDIUM', 'Quantity Discrepancy', 'Cycle count variance detected in Zone A', 'VARIANCE'),
    ]
    
    for severity, title, message, alert_type in alert_data:
        wh_id = random.choice(warehouse_ids)
        cursor.execute('''
            INSERT INTO wms_alerts (warehouse_id, severity, title, message, alert_type, is_active, is_acknowledged)
            VALUES (?, ?, ?, ?, ?, 1, 0)
        ''', (wh_id, severity, title, message, alert_type))

    conn.commit()

    # Create WMS Internal Movements (stock movements)
    print("  Creating stock movements...")
    movement_types = ['RECEIPT', 'ISSUE', 'TRANSFER', 'ADJUSTMENT', 'RETURN']
    movement_count = 0
    for inv in inv_items[:30]:
        for m in range(random.randint(3, 8)):
            move_type = random.choice(movement_types)
            qty = random.randint(1, 50)
            src_loc = random.choice(loc_ids) if loc_ids else None
            dst_loc = random.choice(loc_ids) if loc_ids else None
            
            cursor.execute('''
                INSERT INTO wms_internal_movements 
                (movement_number, movement_type, item_id, source_location_id, destination_location_id, 
                 quantity, reference_type, reference_number, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            ''', (
                f"MOV-{random.randint(10000, 99999)}",
                move_type, 
                inv['id'] % len(item_ids) + 1 if item_ids else 1,
                src_loc, dst_loc if move_type == 'TRANSFER' else None,
                qty,
                random.choice(['PO', 'SO', 'WO', 'Manual', 'Cycle Count']),
                f"REF-{random.randint(10000, 99999)}",
                (datetime.now() - timedelta(days=random.randint(0, 60))).strftime('%Y-%m-%d')
            ))
            movement_count += 1

    conn.commit()
    print(f"    Created {movement_count} stock movements")

    # Create WMS Settings
    print("  Creating settings...")
    settings = [
        ('near_expiry_days', '30'),
        ('low_stock_threshold_percent', '20'),
        ('auto_assign_location', '1'),
        ('enable_serial_tracking', '1'),
        ('enable_batch_tracking', '1'),
    ]
    for key, value in settings:
        cursor.execute('''
            INSERT OR IGNORE INTO wms_settings (setting_key, setting_value)
            VALUES (?, ?)
        ''', (key, value))

    conn.commit()
    conn.close()
    print(f"WMS sample data seeded successfully!")
    print(f"  - {len(warehouse_ids)} warehouses")
    print(f"  - {len(location_ids)} locations")
    print(f"  - {len(item_ids)} items")
    print(f"  - {balance_count} inventory balances")
    print(f"  - {len(alert_data)} alerts")
    print(f"  - {movement_count} movements")


if __name__ == '__main__':
    seed_wms_data()