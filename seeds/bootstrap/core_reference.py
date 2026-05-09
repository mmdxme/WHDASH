"""
Core Reference Data Seeds
==========================
Bootstrap seeds: the minimal set of reference data the application
needs to function correctly.

This file MUST run before any other seeds.
It contains only production-safe, non-demo reference data.

Functions:
  seed_core_reference()      - Categories, brands, statuses, roles
  seed_reference_companies() - Default companies (Holding, SDAD, AFRA, Carmania)
  seed_reference_users()     - Admin user
  seed_reference_warehouses()- Default warehouse per company
"""

import random
from datetime import datetime


def seed_core_reference(db_getter):
    """Seed core lookup tables: categories, brands, statuses."""
    db = db_getter()

    # Categories
    categories = ['Filters', 'Brakes', 'Suspension', 'Electrical', 'Engine Components', 'Body Parts']
    for cat in categories:
        db.execute("INSERT OR IGNORE INTO categories (name) VALUES (?)", (cat,))

    # Brands
    brands = [
        ('Toyota Genuine', 'Genuine'),
        ('Bosch', 'Aftermarket'),
        ('Denso', 'Aftermarket'),
        ('ACDelco', 'Aftermarket'),
        ('Hyundai Mobis', 'Genuine'),
        ('Brembo', 'Aftermarket'),
    ]
    for name, btype in brands:
        db.execute("INSERT OR IGNORE INTO brands (name, type) VALUES (?, ?)", (name, btype))

    # Statuses
    statuses = ['Active', 'Discontinued', 'Recalled', 'Backordered']
    for st in statuses:
        db.execute("INSERT OR IGNORE INTO statuses (name) VALUES (?)", (st,))

    # Default delivery activities
    activities = [
        'Arrival to warehouse', 'Departure from Warehouse',
        'Arrival at Customer', 'Departure from Customer', 'Documents Delivery'
    ]
    for a in activities:
        db.execute("INSERT OR IGNORE INTO delivery_activities (name) VALUES (?)", (a,))

    # Task departments
    departments = [
        ('Administration', 'Cross-functional leadership, governance, and approvals'),
        ('Sales', 'Customer acquisition, key accounts, and commercial follow-up'),
        ('Warehouse', 'Stock handling, shelving, and internal controls'),
        ('Logistics', 'Fleet, dispatch, and route execution'),
        ('Procurement', 'Supplier management and purchasing coordination'),
        ('Accounting', 'Collections, payables, and financial close'),
        ('Operations', 'Execution monitoring and service coordination'),
        ('Human Resources', 'Staffing, onboarding, and compliance'),
    ]
    for name, desc in departments:
        db.execute(
            "INSERT OR IGNORE INTO task_departments (name, description) VALUES (?, ?)",
            (name, desc)
        )

    # Task transaction categories
    categories = [
        ('Labor', 'Employee working hours and wages', '#10b981', 'fa-clock', 1),
        ('Materials', 'Raw materials and supplies consumed', '#f59e0b', 'fa-box', 1),
        ('Equipment', 'Equipment usage and rental costs', '#6366f1', 'fa-truck', 1),
        ('Transportation', 'Travel and transport expenses', '#8b5cf6', 'fa-car', 1),
        ('Outsourcing', 'Third-party services and contractors', '#ec4899', 'fa-users', 1),
        ('Overhead', 'Indirect costs and utilities', '#64748b', 'fa-building', 1),
        ('Revenue', 'Income generated from task completion', '#22c55e', 'fa-dollar-sign', 1),
        ('Miscellaneous', 'Other task-related expenses', '#78716c', 'fa-ellipsis-h', 1),
    ]
    for name, desc, color, icon, system in categories:
        db.execute(
            "INSERT OR IGNORE INTO task_transaction_categories (name, description, color, icon, is_system) VALUES (?, ?, ?, ?, ?)",
            (name, desc, color, icon, system)
        )

    # Issue SLA rules
    sla_rules = [
        ('Critical', 4, 24, 'Critical priority - 4hr response, 24hr resolution'),
        ('High', 8, 48, 'High priority - 8hr response, 48hr resolution'),
        ('Medium', 24, 120, 'Medium priority - 24hr response, 120hr resolution'),
        ('Low', 72, 240, 'Low priority - 72hr response, 240hr resolution'),
    ]
    for priority, resp_hours, res_hours, desc in sla_rules:
        db.execute(
            "INSERT OR IGNORE INTO issue_sla_rules (priority, response_hours, resolution_hours, description) VALUES (?, ?, ?, ?)",
            (priority, resp_hours, res_hours, desc)
        )

    db.commit()
    db.close()
    print("  [OK] Core reference data seeded")


def seed_reference_companies(db_getter):
    """Seed default companies."""
    db = db_getter()

    companies = ['Holding Company', 'SDAD', 'AFRA', 'Carmania']
    for name in companies:
        db.execute("INSERT OR IGNORE INTO companies (name) VALUES (?)", (name,))

    # Seed Global Admin role
    db.execute(
        "INSERT OR IGNORE INTO roles (role_name, company_id, can_edit_stock, can_manage_users) VALUES (?, ?, ?, ?)",
        ('Global Admin', 1, 1, 1)
    )

    db.commit()
    db.close()
    print("  [OK] Reference companies seeded")


def seed_reference_users(db_getter):
    """Seed default admin user."""
    db = db_getter()

    # Check if admin exists
    existing = db.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
    if not existing:
        db.execute("""
            INSERT INTO users (username, email, password, role_id, company_id)
            VALUES (?, ?, ?, ?, ?)
        """, (
            'admin',
            'admin@warehouse.local',
            '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4p2p0lGnyPyEzG8m',  # admin123
            1, None
        ))

    db.commit()
    db.close()
    print("  [OK] Reference users seeded")


def seed_reference_warehouses(db_getter):
    """Seed default Main Warehouse per company."""
    db = db_getter()

    companies = db.execute("SELECT id, name FROM companies").fetchall()
    for comp in companies:
        existing = db.execute(
            "SELECT id FROM warehouses WHERE company_id = ? AND name = ?",
            (comp['id'], 'Main Warehouse')
        ).fetchone()
        if not existing:
            db.execute(
                "INSERT INTO warehouses (name, company_id) VALUES (?, ?)",
                ('Main Warehouse', comp['id'])
            )

    db.commit()
    db.close()
    print("  [OK] Reference warehouses seeded")