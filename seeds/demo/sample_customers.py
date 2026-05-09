"""
Demo Data Seeds
==============
Sample/demo data for development and demonstration environments.
These seeds are ONLY executed when SEED_MODE=demo.

Functions:
  seed_demo_customers()     - 10 sample customers
  seed_demo_delivery_trips() - 3 sample delivery trips
  seed_demo_tasks()         - 5 sample tasks
  seed_demo_issues()        - 3 sample issues
  seed_demo_inventory()     - 20 sample inventory items
"""

import random
from datetime import datetime, timedelta


def seed_demo_customers(db_getter):
    """Seed sample customers."""
    db = db_getter()

    if db.execute("SELECT COUNT(*) FROM customers").fetchone()[0] > 0:
        print("  [SKIP] Customers already exist")
        db.close()
        return

    names = [
        ('Al Futtaim Auto', 'Dubai', 'Active'),
        ('Al Naboodah Automobiles', 'Sharjah', 'Active'),
        ('Al Futtaim Motors', 'Dubai', 'Active'),
        ('AW Rostamani', 'Dubai', 'Active'),
        ('Tabarak Automotive', 'Abu Dhabi', 'Active'),
        ('National Motor Company', 'Al Ain', 'Active'),
        ('Universal Automotive', 'Dubai', 'Active'),
        ('Premium Auto Services', 'Sharjah', 'Active'),
        ('Fast Track Garage', 'Dubai', 'Active'),
        ('Quick Fix Auto', 'Abu Dhabi', 'Active'),
    ]

    for name, location, status in names:
        db.execute(
            "INSERT OR IGNORE INTO customers (name, location, type, status) VALUES (?, ?, ?, ?)",
            (name, location, 'Retail', status)
        )

    db.commit()
    db.close()
    print("  [OK] Demo customers seeded")


def seed_demo_delivery_trips(db_getter):
    """Seed sample delivery trips."""
    db = db_getter()

    if db.execute("SELECT COUNT(*) FROM delivery_trips").fetchone()[0] > 0:
        print("  [SKIP] Delivery trips already exist")
        db.close()
        return

    drivers = db.execute("SELECT id FROM users WHERE role_id = 1 LIMIT 3").fetchall()
    if not drivers:
        print("  [SKIP] No driver users found")
        db.close()
        return

    for driver in drivers:
        db.execute("""
            INSERT INTO delivery_trips (driver_id, status, date)
            VALUES (?, ?, ?)
        """, (driver['id'], 'At Warehouse', datetime.now().date().isoformat()))

    db.commit()
    db.close()
    print("  [OK] Demo delivery trips seeded")


def seed_demo_tasks(db_getter):
    """Seed sample tasks."""
    db = db_getter()

    if db.execute("SELECT COUNT(*) FROM task_items").fetchone()[0] > 0:
        print("  [SKIP] Tasks already exist")
        db.close()
        return

    task_templates = [
        ('Review Q1 financial statements', 'High', 'Open', 'Accounting'),
        ('Schedule maintenance for forklift #3', 'Medium', 'Open', 'Warehouse'),
        ('Follow up with Al Futtaim on pending order', 'High', 'In Progress', 'Sales'),
        ('Update staff onboarding checklist', 'Low', 'Open', 'Human Resources'),
        ('Approve supplier invoice #INV-2026-0042', 'Medium', 'Open', 'Procurement'),
    ]

    for task_name, priority, status, dept_name in task_templates:
        dept = db.execute(
            "SELECT id FROM task_departments WHERE name = ?", (dept_name,)
        ).fetchone()
        dept_id = dept['id'] if dept else None

        db.execute("""
            INSERT INTO task_items (task_name, priority, status, department_id, due_at)
            VALUES (?, ?, ?, ?, ?)
        """, (
            task_name, priority, status, dept_id,
            (datetime.now() + timedelta(days=7)).date().isoformat()
        ))

    db.commit()
    db.close()
    print("  [OK] Demo tasks seeded")


def seed_demo_issues(db_geteter):
    """Seed sample issues."""
    db = db_getter()

    if db.execute("SELECT COUNT(*) FROM issue_items").fetchone()[0] > 0:
        print("  [SKIP] Issues already exist")
        db.close()
        return

    issues = [
        ('Oil filter batch quality issue', 'High', 'Open', 'Critical batch of filters received'),
        ('Delivery van #12 brake pads worn', 'Medium', 'Open', 'Safety check required'),
        ('Customer complaint: wrong part delivered', 'High', 'In Progress', 'Investigation ongoing'),
    ]

    for issue, priority, status, desc in issues:
        db.execute("""
            INSERT INTO issue_items (issue_date, issue, priority, status, row_id, pareto_law)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            datetime.now().date().isoformat(),
            issue, priority, status,
            random.randint(1000, 9999), 0
        ))

    db.commit()
    db.close()
    print("  [OK] Demo issues seeded")


def seed_demo_inventory(db_getter):
    """Seed sample inventory items."""
    db = db_getter()

    if db.execute("SELECT COUNT(*) FROM inventory").fetchone()[0] > 0:
        print("  [SKIP] Inventory already exists")
        db.close()
        return

    parts = db.execute("SELECT id FROM parts LIMIT 10").fetchall()
    for part in parts:
        for zone_suffix in ['01-01-01-01-A', '01-01-01-02-B', '01-02-01-01-C']:
            qty = random.randint(0, 150)
            try:
                db.execute("""
                    INSERT INTO inventory (part_id, zone, quantity, company_id)
                    VALUES (?, ?, ?, ?)
                """, (part['id'], zone_suffix, qty, 1))
            except Exception:
                pass  # Skip duplicates

    db.commit()
    db.close()
    print("  [OK] Demo inventory seeded")