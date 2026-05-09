"""
Seed Procurement Demo Data
===========================
Seeds realistic procurement data for testing and demonstration.
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


def seed_procurement_data():
    """Seed comprehensive procurement demo data."""
    conn = get_db()
    cursor = conn.cursor()

    print("Seeding procurement demo data...")

    # Check if already seeded
    cursor.execute("SELECT COUNT(*) as cnt FROM procurement_requisitions")
    if cursor.fetchone()['cnt'] > 0:
        print("Procurement data already exists, skipping...")
        conn.close()
        return

    # Ensure suppliers table exists and has data
    cursor.execute("SELECT COUNT(*) as cnt FROM suppliers")
    if cursor.fetchone()['cnt'] == 0:
        print("No suppliers found - skipping procurement seed...")
        conn.close()
        return

    # Get supplier IDs
    cursor.execute("SELECT id, name FROM suppliers LIMIT 10")
    suppliers = list(cursor.fetchall())

    # Get user IDs for requesters and buyers
    cursor.execute("SELECT id, username FROM users LIMIT 5")
    users = list(cursor.fetchall())

    # Get parts for item lookup
    cursor.execute("SELECT id, part_number, description FROM parts LIMIT 20")
    parts = list(cursor.fetchall())

    # Get companies
    cursor.execute("SELECT id FROM companies")
    companies = [r['id'] for r in cursor.fetchall()]

    # Seed Requisitions
    print("  Creating purchase requisitions...")
    requisition_statuses = ['DRAFT', 'PENDING', 'APPROVED', 'CONVERTED']
    
    for i in range(1, 16):
        req_date = (datetime.now() - timedelta(days=random.randint(1, 60))).strftime('%Y-%m-%d')
        status = random.choice(requisition_statuses)
        requester = random.choice(users) if users else None
        company = random.choice(companies) if companies else 1
        
        cursor.execute(
            """INSERT INTO procurement_requisitions 
                (requisition_number, requisition_date, requester_id, requester_name, 
                department, company_id, priority, urgency, status, total_estimated_amount, 
                currency, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (f'PR-{i:04d}', req_date, 
             requester['id'] if requester else 1,
             requester['username'] if requester else 'System',
             random.choice(['Operations', 'Warehouse', 'Maintenance', 'IT', 'Admin']),
             company,
             random.choice(['LOW', 'MEDIUM', 'HIGH', 'URGENT']),
             random.choice(['NORMAL', 'RUSH', 'CRITICAL']),
             status,
             round(random.uniform(500, 50000), 2),
             random.choice(['AED', 'USD', 'EUR']),
             f'Requisition for {random.choice(["regular purchase", "emergency stock", "project material", "maintenance parts"])}',
             requester['id'] if requester else 1)
        )
        req_id = cursor.lastrowid

        # Add requisition lines
        num_lines = random.randint(2, 6)
        for j in range(num_lines):
            part = random.choice(parts) if parts else None
            qty = random.randint(1, 100)
            unit_price = round(random.uniform(10, 1000), 2) if part else round(random.uniform(50, 5000), 2)
            
            cursor.execute(
                """INSERT INTO procurement_requisition_lines 
                    (requisition_id, line_number, item_code, item_name, requested_qty, 
                    unit_of_measure, required_date, estimated_unit_price, estimated_total_price, 
                    purpose, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (req_id, j + 1,
                 part['part_number'] if part else f'ITEM-{random.randint(1000, 9999)}',
                 part['description'] if part else f'Procurement Item {j+1}',
                 qty, 'PCS',
                 (datetime.now() + timedelta(days=random.randint(7, 60))).strftime('%Y-%m-%d'),
                 unit_price, qty * unit_price,
                 random.choice(['Operational', 'Project', 'Stock Replenishment', 'Maintenance']),
                 'PENDING' if status == 'PENDING' else ('APPROVED' if status == 'APPROVED' else 'PENDING'))
            )

    # Seed RFQs
    print("  Creating RFQs...")
    rfq_statuses = ['DRAFT', 'SENT', 'RECEIVED', 'AWARDED', 'CANCELLED']
    
    for i in range(1, 11):
        rfq_date = (datetime.now() - timedelta(days=random.randint(1, 45))).strftime('%Y-%m-%d')
        status = random.choice(rfq_statuses)
        buyer = random.choice(users) if users else None
        supplier = random.choice(suppliers) if suppliers else None
        
        cursor.execute(
            """INSERT INTO procurement_rfqs 
                (rfq_number, rfq_date, buyer_id, buyer_name, company_id, status, 
                response_due_date, incoterm, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (f'RFQ-{i:04d}', rfq_date,
             buyer['id'] if buyer else 1,
             buyer['username'] if buyer else 'System',
             random.choice(companies) if companies else 1,
             status,
             (datetime.now() + timedelta(days=random.randint(7, 30))).strftime('%Y-%m-%d'),
             random.choice(['EXW', 'FOB', 'CIF', 'DDP', 'DAP']),
             f'Request for quotation - {random.choice(["supply of parts", "service contract", "equipment purchase"])}',
             buyer['id'] if buyer else 1)
        )
        rfq_id = cursor.lastrowid

        # Add RFQ lines
        num_lines = random.randint(2, 5)
        for j in range(num_lines):
            part = random.choice(parts) if parts else None
            qty = random.randint(10, 200)
            
            cursor.execute(
                """INSERT INTO procurement_rfq_lines 
                    (rfq_id, line_number, item_code, item_name, description, 
                    requested_qty, unit_of_measure, required_date, target_price)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (rfq_id, j + 1,
                 part['part_number'] if part else f'ITEM-{random.randint(1000, 9999)}',
                 part['description'] if part else f'RFQ Item {j+1}',
                 f'Description for line {j+1}',
                 qty, 'PCS',
                 (datetime.now() + timedelta(days=random.randint(14, 60))).strftime('%Y-%m-%d'),
                 round(random.uniform(20, 2000), 2))
            )

    # Seed Purchase Orders
    print("  Creating purchase orders...")
    po_statuses = ['DRAFT', 'SENT', 'ACKNOWLEDGED', 'PARTIAL', 'RECEIVED', 'CLOSED', 'CANCELLED']
    
    for i in range(1, 13):
        po_date = (datetime.now() - timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d')
        status = random.choice(po_statuses)
        supplier = random.choice(suppliers) if suppliers else None
        buyer = random.choice(users) if users else None
        
        cursor.execute(
            """INSERT INTO procurement_orders 
                (po_number, po_date, supplier_id, supplier_name, buyer_id, buyer_name, 
                company_id, warehouse_id, status, payment_terms, currency, 
                total_amount, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (f'PO-{i:04d}', po_date,
             supplier['id'] if supplier else 1,
             supplier['name'] if supplier else 'Default Supplier',
             buyer['id'] if buyer else 1,
             buyer['username'] if buyer else 'System',
             random.choice(companies) if companies else 1,
             1,  # warehouse_id
             status,
             random.choice(['Net 30', 'Net 45', 'Net 60', 'Cash', '2/10 Net 30']),
             random.choice(['AED', 'USD', 'EUR']),
             round(random.uniform(1000, 100000), 2),
             f'Purchase order for {random.choice(["stock replenishment", "project materials", "service parts", "equipment"])}',
             buyer['id'] if buyer else 1)
        )
        po_id = cursor.lastrowid

        # Add PO lines
        num_lines = random.randint(2, 8)
        for j in range(num_lines):
            part = random.choice(parts) if parts else None
            qty = random.randint(5, 100)
            unit_price = round(random.uniform(15, 3000), 2) if part else round(random.uniform(100, 10000), 2)
            received_qty = qty if status in ['RECEIVED', 'CLOSED'] else (random.randint(0, qty) if status == 'PARTIAL' else 0)
            
            cursor.execute(
                """INSERT INTO procurement_order_lines 
                    (po_id, line_number, item_code, item_name, description, 
                    ordered_qty, received_qty, unit_of_measure, unit_price, 
                    total_price, delivery_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (po_id, j + 1,
                 part['part_number'] if part else f'ITEM-{random.randint(1000, 9999)}',
                 part['description'] if part else f'PO Item {j+1}',
                 f'PO line description {j+1}',
                 qty, received_qty, 'PCS',
                 unit_price, qty * unit_price,
                 (datetime.now() + timedelta(days=random.randint(7, 45))).strftime('%Y-%m-%d'),
                 'RECEIVED' if received_qty >= qty else ('PARTIAL' if received_qty > 0 else 'PENDING'))
            )

    # Seed Supplier Performance
    print("  Creating supplier performance records...")
    for supplier in suppliers:
        for month_offset in range(6):
            metric_date = (datetime.now() - timedelta(days=30 * month_offset)).strftime('%Y-%m-%d')
            on_time = random.uniform(75, 100)
            fill_rate = random.uniform(80, 100)
            quality = random.uniform(85, 100)
            
            cursor.execute(
                """INSERT INTO procurement_supplier_metrics 
                    (supplier_id, metric_date, on_time_delivery_rate, avg_lead_time_days,
                    fill_rate, quantity_accuracy, quality_acceptance_rate, 
                    overall_score, total_orders, total_receipts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (supplier['id'], metric_date,
                 on_time, random.uniform(5, 30),
                 fill_rate, random.uniform(85, 100),
                 quality, (on_time + fill_rate + quality) / 3,
                 random.randint(5, 50), random.randint(5, 50))
            )

    conn.commit()
    print(f"Successfully seeded procurement data: 15 requisitions, 10 RFQs, 12 purchase orders, {len(suppliers)} supplier metrics")
    conn.close()


if __name__ == '__main__':
    seed_procurement_data()