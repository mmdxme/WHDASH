"""
Seed WMS/Warehouse Extended Demo Data
======================================
Seeds realistic warehouse management data including locations, receipts, 
shipments, transfers, and stock counts.
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


def seed_wms_extended_data():
    """Seed comprehensive WMS demo data beyond basic parts/inventory."""
    conn = get_db()
    cursor = conn.cursor()

    print("Seeding WMS extended demo data...")

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) as cnt FROM wms_locations")
    if cursor.fetchone()['cnt'] > 0:
        print("WMS extended data already exists, skipping...")
        conn.close()
        return

    # Get existing data
    cursor.execute("SELECT id, name FROM companies")
    companies = list(cursor.fetchall())
    cursor.execute("SELECT id, name FROM warehouses")
    warehouses = list(cursor.fetchall())
    cursor.execute("SELECT id, part_number FROM parts LIMIT 30")
    parts = list(cursor.fetchall())

    if not warehouses:
        print("No warehouses found - creating defaults...")
        for comp in companies[:4]:
            cursor.execute("INSERT INTO warehouses (name, company_id) VALUES (?, ?)",
                         (f"Main Warehouse {comp['name']}", comp['id']))
        conn.commit()
        cursor.execute("SELECT id, name FROM warehouses")
        warehouses = list(cursor.fetchall())

    # Seed Warehouse Zones
    print("  Creating warehouse zones...")
    zone_types = ['Receiving', 'Storage', 'Picking', 'Shipping', 'Returns', 'Quarantine', 'Staging']
    zone_id_map = {}
    
    for wh in warehouses:
        for ztype in zone_types:
            cursor.execute(
                """INSERT INTO wms_zones (warehouse_id, zone_code, zone_name, zone_type, 
                    is_active, description) VALUES (?, ?, ?, ?, ?, ?)""",
                (wh['id'], f"{wh['id']}-{ztype[:3].upper()}", 
                 f"Zone {ztype} - {wh['name']}",
                 ztype, 1, f"{ztype} area for {wh['name']}")
            )
            zone_id_map[(wh['id'], ztype)] = cursor.lastrowid

    # Seed Locations
    print("  Creating locations...")
    location_count = 0
    for wh in warehouses:
        for zone_num in range(1, 4):
            for aisle in range(1, 6):
                for rack in range(1, 4):
                    for level in range(1, 5):
                        loc_code = f"{wh['id']:02d}-{zone_num:02d}-{aisle:02d}-{rack:02d}-{level:02d}"
                        cursor.execute(
                            """INSERT INTO wms_locations (warehouse_id, location_code, location_type,
                                zone, aisle, rack, level, is_active, capacity_sqm, max_weight_kg)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (wh['id'], loc_code, 'Storage', f"Z{zone_num}", 
                             f"A{aisle}", f"R{rack}", f"L{level}",
                             1, random.randint(10, 50), random.randint(500, 2000))
                        )
                        location_count += 1

    # Get location IDs for stock operations
    cursor.execute("SELECT id FROM wms_locations LIMIT 100")
    locations = [r['id'] for r in cursor.fetchall()]

    # Seed Stock Movements
    print("  Creating stock movements...")
    movement_types = ['Receipt', 'Issue', 'Transfer', 'Adjustment', 'Return']
    cursor.execute("SELECT id FROM inventory LIMIT 50")
    inv_items = list(cursor.fetchall())

    for idx, inv in enumerate(inv_items[:30]):
        for m in range(random.randint(3, 10)):
            move_type = random.choice(movement_types)
            qty = random.randint(1, 50)
            loc = random.choice(locations) if locations else None
            
            cursor.execute(
                """INSERT INTO wms_stock_movements (item_id, warehouse_id, from_location, to_location,
                    movement_type, quantity, reference_type, reference_number, 
                    performed_by, movement_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (inv['id'], inv['id'] % len(warehouses) + 1,
                 loc, loc if move_type == 'Transfer' else None,
                 move_type, qty,
                 random.choice(['PO', 'SO', 'WO', 'Manual', 'Cycle Count']),
                 f"REF-{random.randint(10000, 99999)}",
                 1,  # user_id
                 (datetime.now() - timedelta(days=random.randint(0, 90))).strftime('%Y-%m-%d'),
                 f"{move_type} for inventory item {inv['id']}")
            )

    # Seed Receiving Records
    print("  Creating receiving records...")
    for i in range(1, 21):
        status = random.choice(['Pending', 'In Progress', 'Completed', 'Verified'])
        cursor.execute(
            """INSERT INTO wms_receiving (receipt_number, warehouse_id, supplier_name, 
                receipt_date, status, received_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (f"RCV-{i:05d}", 
             random.choice(warehouses)['id'] if warehouses else 1,
             random.choice(['Global Tech Parts', 'EuroAuto Systems', 'Nippon Dynamics', 'American Steelworks']),
             (datetime.now() - timedelta(days=random.randint(1, 60))).strftime('%Y-%m-%d'),
             status, 1,
             f"Receiving record {i}")
        )
        recv_id = cursor.lastrowid

        # Add receiving lines
        for j in range(random.randint(2, 6)):
            part = random.choice(parts) if parts else None
            cursor.execute(
                """INSERT INTO wms_receiving_lines (receiving_id, part_id, expected_qty, 
                    received_qty, condition_status, location_id, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (recv_id, part['id'] if part else None,
                 random.randint(10, 100), random.randint(5, 80),
                 random.choice(['Good', 'Damaged', 'Partial']),
                 random.choice(locations) if locations else None,
                 f"Line {j} notes")
            )

    # Seed Shipping Records
    print("  Creating shipping records...")
    for i in range(1, 16):
        status = random.choice(['Draft', 'Picking', 'Packed', 'Shipped', 'Delivered'])
        cursor.execute(
            """INSERT INTO wms_shipping (shipment_number, warehouse_id, customer_name,
                shipment_date, status, shipped_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (f"SHP-{i:05d}",
             random.choice(warehouses)['id'] if warehouses else 1,
             random.choice(['Al Futtaim Motors', 'Al Tayer Motors', 'AW Rostamani', 'Swiss O']) if i % 2 == 0 else f"Customer {i}",
             (datetime.now() - timedelta(days=random.randint(1, 45))).strftime('%Y-%m-%d'),
             status, 1,
             f"Shipping record {i}")
        )
        ship_id = cursor.lastrowid

        # Add shipping lines
        for j in range(random.randint(1, 5)):
            part = random.choice(parts) if parts else None
            cursor.execute(
                """INSERT INTO wms_shipping_lines (shipping_id, part_id, ordered_qty,
                    shipped_qty, location_id, notes)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (ship_id, part['id'] if part else None,
                 random.randint(5, 50), random.randint(1, 40),
                 random.choice(locations) if locations else None,
                 f"Line {j}")
            )

    # Seed Transfer Orders
    print("  Creating transfer orders...")
    for i in range(1, 13):
        status = random.choice(['Draft', 'In Transit', 'Completed', 'Cancelled'])
        source_wh = random.choice(warehouses)['id'] if warehouses else 1
        dest_wh = random.choice([w for w in warehouses if w['id'] != source_wh])['id'] if len(warehouses) > 1 else source_wh
        
        cursor.execute(
            """INSERT INTO wms_transfer_orders (transfer_number, from_warehouse_id, to_warehouse_id,
                transfer_date, status, requested_by, approved_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (f"TFR-{i:05d}", source_wh, dest_wh,
             (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
             status, 1, 1 if status == 'Completed' else None,
             f"Transfer order {i}")
        )
        trans_id = cursor.lastrowid

        # Add transfer lines
        for j in range(random.randint(2, 6)):
            part = random.choice(parts) if parts else None
            qty = random.randint(5, 30)
            cursor.execute(
                """INSERT INTO wms_transfer_lines (transfer_id, part_id, from_location, to_location,
                    quantity, status)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (trans_id, part['id'] if part else None,
                 random.choice(locations), random.choice(locations),
                 qty, 'COMPLETED' if status == 'Completed' else 'PENDING')
            )

    # Seed Stock Counts
    print("  Creating stock count records...")
    for i in range(1, 8):
        status = random.choice(['Planned', 'In Progress', 'Completed', 'Verified'])
        cursor.execute(
            """INSERT INTO wms_stock_counts (count_number, warehouse_id, count_date, 
                status, count_type, counted_by, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (f"CNT-{i:05d}",
             random.choice(warehouses)['id'] if warehouses else 1,
             (datetime.now() - timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d'),
             status, random.choice(['Full', 'Cycle', 'Spot']),
             1,
             f"Stock count {i}")
        )
        count_id = cursor.lastrowid

        # Add count lines
        for j in range(random.randint(5, 15)):
            part = random.choice(parts) if parts else None
            system_qty = random.randint(0, 100)
            counted_qty = system_qty + random.randint(-5, 5)
            cursor.execute(
                """INSERT INTO wms_stock_count_lines (stock_count_id, part_id, location_id,
                    system_qty, counted_qty, variance, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (count_id, part['id'] if part else None,
                 random.choice(locations) if locations else None,
                 system_qty, counted_qty, counted_qty - system_qty,
                 f"Count line {j}")
            )

    conn.commit()
    print(f"Successfully seeded WMS extended data: {location_count} locations, 20 receipts, 15 shipments, 12 transfers, 7 stock counts")
    conn.close()


if __name__ == '__main__':
    seed_wms_extended_data()