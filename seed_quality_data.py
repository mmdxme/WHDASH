"""Seed Quality Management demo data."""
import sqlite3
import random
from datetime import datetime, timedelta

DATABASE = 'warehouse.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def seed_quality_data():
    """Seed quality management demo data."""
    conn = get_db()
    c = conn.cursor()

    print("Seeding Quality Management demo data...")

    # Get some existing data for references
    item_ids = [row[0] for row in c.execute("SELECT id FROM parts LIMIT 10").fetchall()]
    supplier_ids = [row[0] for row in c.execute("SELECT id FROM suppliers LIMIT 10").fetchall()]
    customer_ids = [row[0] for row in c.execute("SELECT id FROM customers LIMIT 10").fetchall()]
    employee_ids = [row[0] for row in c.execute("SELECT id FROM hr_employees LIMIT 10").fetchall()]
    company_ids = [row[0] for row in c.execute("SELECT id FROM companies").fetchall()]
    warehouse_ids = [row[0] for row in c.execute("SELECT id FROM warehouses").fetchall()]

    if not item_ids:
        item_ids = [1]
    if not supplier_ids:
        supplier_ids = [1]
    if not customer_ids:
        customer_ids = [1]
    if not employee_ids:
        employee_ids = [1]
    if not company_ids:
        company_ids = [1]
    if not warehouse_ids:
        warehouse_ids = [1]

    # 1. Create sample inspections
    inspection_statuses = ['pending', 'in_progress', 'completed', 'approved']
    result_statuses = ['pass', 'fail', 'conditional']

    for i in range(10):
        status = random.choice(inspection_statuses)
        insp_date = datetime.now() - timedelta(days=random.randint(1, 90))

        c.execute("""
            INSERT INTO quality_inspections (
                inspection_number, inspection_type, source_type, source_reference,
                company_id, warehouse_id, supplier_id, customer_id, item_id,
                quantity_inspected, quantity_passed, quantity_failed,
                result, status, inspector_id, inspection_date, notes, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f'INS-{random.randint(2024, 2026)}-{random.randint(1000, 9999)}',
            random.choice(['incoming', 'in_process', 'outgoing', 'warehouse']),
            random.choice(['procurement', 'production', 'sales', 'internal']),
            f'REF-{random.randint(100, 999)}',
            random.choice(company_ids),
            random.choice(warehouse_ids),
            random.choice(supplier_ids),
            random.choice(customer_ids),
            random.choice(item_ids),
            random.randint(50, 500),
            random.randint(40, 480),
            random.randint(0, 20),
            random.choice(result_statuses) if status == 'completed' else None,
            status,
            random.choice(employee_ids),
            insp_date.strftime('%Y-%m-%d'),
            f'Sample inspection {i+1}',
            random.choice(employee_ids)
        ))

    conn.commit()
    print("Created 10 sample inspections")

    # 2. Create sample NCRs
    ncr_statuses = ['open', 'investigating', 'closed']
    severities = ['critical', 'major', 'minor']

    for i in range(5):
        ncr_date = datetime.now() - timedelta(days=random.randint(1, 60))

        c.execute("""
            INSERT INTO quality_non_conformances (
                ncr_number, source_type, source_id, severity, description,
                status, item_id, quantity_affected, initiator_id,
                open_date, target_close_date, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f'NCR-{random.randint(2024, 2026)}-{random.randint(100, 999)}',
            random.choice(['inspection', 'production', 'customer', 'supplier']),
            random.randint(1, 50),
            random.choice(severities),
            f'Description of NCR {i+1}',
            random.choice(ncr_statuses),
            random.choice(item_ids),
            random.randint(1, 100),
            random.choice(employee_ids),
            ncr_date.strftime('%Y-%m-%d'),
            (ncr_date + timedelta(days=30)).strftime('%Y-%m-%d'),
            ncr_date.strftime('%Y-%m-%d')
        ))

    conn.commit()
    print("Created 5 sample NCRs")

    # 3. Create sample CAPAs
    for i in range(4):
        capa_date = datetime.now() - timedelta(days=random.randint(1, 60))

        c.execute("""
            INSERT INTO quality_capa_records (
                capa_number, title, capa_type, severity, description,
                root_cause, status, owner_id, open_date, target_date, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f'CAPA-{random.randint(2024, 2026)}-{random.randint(100, 999)}',
            f'CAPA Title for Issue {i+1}',
            random.choice(['corrective', 'preventive']),
            random.choice(severities),
            f'CAPA description {i+1}',
            f'Root cause analysis for CAPA {i+1}',
            random.choice(['open', 'in_progress', 'closed']),
            random.choice(employee_ids),
            capa_date.strftime('%Y-%m-%d'),
            (capa_date + timedelta(days=60)).strftime('%Y-%m-%d'),
            capa_date.strftime('%Y-%m-%d')
        ))

    conn.commit()
    print("Created 4 sample CAPAs")

    # 4. Create sample audit plans
    for i in range(3):
        planned_date = datetime.now() - timedelta(days=random.randint(-15, 45))

        c.execute("""
            INSERT INTO quality_audit_plans (
                plan_number, audit_title, audit_type, auditor_id,
                scheduled_start_date, status, company_id, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f'AUD-{random.randint(2024, 2026)}-{random.randint(100, 999)}',
            f'Audit Title {i+1}',
            random.choice(['internal', 'external', 'supplier']),
            random.choice(employee_ids),
            planned_date.strftime('%Y-%m-%d'),
            random.choice(['scheduled', 'in_progress', 'completed']),
            random.choice(company_ids),
            planned_date.strftime('%Y-%m-%d')
        ))

    conn.commit()
    print("Created 3 sample audit plans")

    conn.close()
    print("Quality Management demo data seeded successfully!")

if __name__ == '__main__':
    seed_quality_data()
