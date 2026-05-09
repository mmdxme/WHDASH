"""
WMS Extended Demo Data Seeder
============================
Seeds additional WMS demo data including waves and templates.

Usage:
    python seed_wms_extended_data.py
"""

import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db_context, get_one, get_all, table_exists


def seed_wms_extended_data():
    """Seed extended WMS demo data."""
    print("Seeding WMS extended demo data...")
    
    with get_db_context() as db:
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t['name'] for t in tables]
        
        # Seed WMS Wave Templates
        if 'wms_wave_templates' in table_names:
            _seed_wave_templates(db)
        
        # Seed WMS Waves
        if 'wms_waves' in table_names:
            _seed_waves(db)
        
        # Seed WMS Dock Doors
        if 'wms_dock_doors' in table_names:
            _seed_dock_doors(db)
        
        # Seed WMS QC Inspections
        if 'wms_qc_inspections' in table_names:
            _seed_qc_inspections(db)
        
        # Seed WMS Stock Counts
        if 'wms_stock_counts' in table_names:
            _seed_stock_counts(db)
        
        # Seed WMS Returns
        if 'wms_returns' in table_names:
            _seed_returns(db)
        
        # Seed WMS Shipments
        if 'wms_shipments' in table_names:
            _seed_shipments(db)
        
        db.commit()
    
    print("WMS extended demo data seeded successfully!")


def _seed_wave_templates(db):
    """Seed wave templates."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM wms_wave_templates").fetchone()
    if existing['cnt'] > 0:
        print("  - Wave templates already exist")
        return
    
    templates = [
        ('Standard Pick Wave', 'Standard wave for regular orders', 'Single', 'Batch', 50, True, 'Automatic'),
        ('Bulk Order Wave', 'Wave for large bulk orders', 'Single', 'Batch', 200, True, 'Automatic'),
        ('Priority Express', 'High priority expedited picks', 'Single', 'Single', 20, False, 'Manual'),
        ('Cold Storage Wave', 'Temperature-controlled picking', 'Zone', 'Batch', 30, True, 'Automatic'),
        ('Fragile Items Wave', 'Careful handling required', 'Single', 'Single', 15, False, 'Manual'),
    ]
    
    for name, desc, strategy, rule, max_picks, auto, release in templates:
        cursor.execute("""
            INSERT INTO wms_wave_templates (template_name, description, picking_strategy,
                allocation_rule, max_picks_per_operator, auto_assign_tasks, release_type,
                is_active, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1, ?)
        """, (name, desc, strategy, rule, max_picks, 1 if auto else 0, release, datetime.now().isoformat()))
    
    print("  [OK] Wave templates seeded")


def _seed_waves(db):
    """Seed waves."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM wms_waves").fetchone()
    if existing['cnt'] > 0:
        print("  - Waves already exist")
        return
    
    statuses = ['Draft', 'Released', 'In Progress', 'Completed', 'Canceled']
    
    for i in range(10):
        status = random.choice(statuses)
        created = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
        
        cursor.execute("""
            INSERT INTO wms_waves (wave_number, warehouse_id, company_id, status,
                picking_strategy, allocation_rule, order_count, total_lines, total_picks,
                picks_completed, priority, created_by, created_at)
            VALUES (?, 1, 1, ?, 'Single', 'Batch', ?, ?, ?, ?, ?, 1, ?)
        """, (
            f'WAVE-2026-{i+1:04d}',
            status,
            random.randint(5, 50),
            random.randint(10, 100),
            random.randint(50, 500),
            random.randint(0, 500),
            random.choice(['Low', 'Normal', 'High', 'Urgent']),
            datetime.now().isoformat()
        ))
    
    print("  [OK] Waves seeded")


def _seed_dock_doors(db):
    """Seed dock doors."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM wms_dock_doors").fetchone()
    if existing['cnt'] > 0:
        print("  - Dock doors already exist")
        return
    
    doors = []
    for i in range(12):
        doors.append((f'DOCK-{i+1:02d}', random.choice(['Inbound', 'Outbound']), 'Active'))
    
    for code, dtype, status in doors:
        cursor.execute("""
            INSERT INTO wms_dock_doors (door_number, warehouse_id, door_type, status, is_active, created_at)
            VALUES (?, 1, ?, ?, 1, ?)
        """, (code, dtype, status, datetime.now().isoformat()))
    
    print("  [OK] Dock doors seeded")


def _seed_qc_inspections(db):
    """Seed QC inspections."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM wms_qc_inspections").fetchone()
    if existing['cnt'] > 0:
        print("  - QC inspections already exist")
        return
    
    results = ['Pending', 'In Progress', 'Passed', 'Failed', 'On Hold']
    
    for i in range(15):
        result = random.choice(results)
        date = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
        
        cursor.execute("""
            INSERT INTO wms_qc_inspections (inspection_number, inspection_type, warehouse_id,
                item_id, lot_id, location_id, sample_size, inspected_quantity,
                passed_quantity, failed_quantity, result, inspected_by, inspection_date, created_at)
            VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f'QC-{i+1:04d}',
            random.choice(['Full', 'Partial', 'Spot']),
            random.randint(1, 25),
            random.randint(1, 30),
            random.randint(1, 100),
            random.randint(5, 50),
            random.randint(5, 50),
            random.randint(0, 10),
            random.randint(0, 5),
            result,
            random.randint(1, 5),
            date,
            datetime.now().isoformat()
        ))
    
    print("  [OK] QC inspections seeded")


def _seed_stock_counts(db):
    """Seed stock counts."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM wms_stock_counts").fetchone()
    if existing['cnt'] > 0:
        print("  - Stock counts already exist")
        return
    
    statuses = ['Planned', 'In Progress', 'Completed', 'Variance']
    
    for i in range(8):
        status = random.choice(statuses)
        date = (datetime.now() - timedelta(days=random.randint(0, 60))).strftime('%Y-%m-%d')
        
        cursor.execute("""
            INSERT INTO wms_stock_counts (count_number, count_type, warehouse_id, company_id,
                location_id, status, count_method, is_blind_count, scheduled_date,
                completed_date, total_lines, counted_lines, variance_lines,
                created_by, created_at)
            VALUES (?, ?, 1, 1, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (
            f'SC-{i+1:04d}',
            random.choice(['Full', 'Cycle', 'Spot']),
            random.randint(1, 50),
            status,
            random.choice(['Manual', 'RF Scanner']),
            date,
            date if status in ['Completed', 'Variance'] else None,
            random.randint(20, 100),
            random.randint(0, 100),
            random.randint(0, 5),
            datetime.now().isoformat()
        ))
    
    print("  [OK] Stock counts seeded")


def _seed_returns(db):
    """Seed returns."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM wms_returns").fetchone()
    if existing['cnt'] > 0:
        print("  - Returns already exist")
        return
    
    statuses = ['Pending', 'Received', 'Inspected', 'Approved', 'Rejected']
    
    for i in range(12):
        status = random.choice(statuses)
        date = (datetime.now() - timedelta(days=random.randint(0, 45))).strftime('%Y-%m-%d')
        
        cursor.execute("""
            INSERT INTO wms_returns (return_number, return_type, warehouse_id, company_id,
                customer_id, original_order_number, rma_number, reason_code, status,
                authorization_status, notes, created_by, created_at)
            VALUES (?, ?, 1, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f'RET-2026-{i+1:04d}',
            random.choice(['Customer Return', 'Supplier Return', 'Damaged']),
            random.randint(1, 20),
            f'SO-2026-{random.randint(1,100):04d}',
            f'RMA-{random.randint(1000,9999)}',
            random.choice(['Defective', 'Wrong Item', 'Changed Mind', 'Damaged in Transit']),
            status,
            'Approved',
            f'Return processing for {status}',
            1,
            datetime.now().isoformat()
        ))
    
    print("  [OK] Returns seeded")


def _seed_shipments(db):
    """Seed shipments."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM wms_shipments").fetchone()
    if existing['cnt'] > 0:
        print("  - Shipments already exist")
        return
    
    statuses = ['Pending', 'Packed', 'Shipped', 'In Transit', 'Delivered']
    carriers = ['Aramex', 'DHL', 'FedEx', 'UPS', ' Emirates Post']
    
    for i in range(15):
        status = random.choice(statuses)
        date = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
        
        cursor.execute("""
            INSERT INTO wms_shipments (shipment_number, order_id, warehouse_id, company_id,
                carrier_id, carrier_name, tracking_number, departure_date, arrival_date,
                status, created_by, created_at)
            VALUES (?, ?, 1, 1, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (
            f'SHP-2026-{i+1:04d}',
            random.randint(1, 50),
            random.randint(1, 5),
            random.choice(carriers),
            f'TRK{random.randint(100000, 999999)}',
            date,
            date if status in ['In Transit', 'Delivered'] else None,
            status,
            datetime.now().isoformat()
        ))
    
    print("  [OK] Shipments seeded")


def main():
    """Main entry point."""
    print("=" * 60)
    print("WMS Extended Demo Data Seeder")
    print("=" * 60)
    print()
    seed_wms_extended_data()
    print()
    print("=" * 60)
    print("WMS extended demo data seeding completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()