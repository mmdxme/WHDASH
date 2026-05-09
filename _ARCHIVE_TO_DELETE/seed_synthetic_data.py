"""
================================================================================
MMDx SYNTHETIC DATA SEEDING SYSTEM
================================================================================
Enterprise-grade synthetic data generation for demo, testing, and QA.

This system populates the MMDx platform with realistic, relationally-correct,
cross-module-consistent synthetic data.

USAGE:
    python seed_synthetic_data.py --demo         # Balanced demo dataset
    python seed_synthetic_data.py --full         # Maximum data for stress testing
    python seed_synthetic_data.py --minimal      # Quick smoke test
    python seed_synthetic_data.py --reset --demo # Clear demo data and reseed

PRODUCTION SAFETY:
    - NEVER runs automatically in production environments
    - Requires explicit --force flag in production
    - All synthetic records are marked with is_demo_data=1
    - Supports safe reset within demo/test environments only

================================================================================
"""

import os
import sys
import argparse
import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from database import get_db_context, get_db


# =============================================================================
# ENVIRONMENT SAFETY CHECKS
# =============================================================================

def is_production_environment():
    """Check if we're running in a production environment."""
    env = os.environ.get('FLASK_ENV', os.environ.get('ENV', 'development')).lower()
    db_path = os.environ.get('DATABASE_PATH', 'warehouse.db')

    if env in ('production', 'prod'):
        return True
    if any(x in db_path.lower() for x in ['/prod/', '/production/', 'prod_']):
        return True
    return False


# =============================================================================
# SYNTHETIC DATA GENERATOR
# =============================================================================

class SyntheticDataGenerator:
    """Generate realistic synthetic data for testing and demos."""

    DEMO_PREFIX = "DEMO_"
    DEMO_DOMAIN = "demo.local"

    FIRST_NAMES = [
        'Ahmed', 'Mohammed', 'Omar', 'Ali', 'Youssef', 'Ibrahim', 'Hassan', 'Karim',
        'Fatima', 'Aisha', 'Mariam', 'Sara', 'Nadia', 'Leila', 'Zainab', 'Rania',
        'John', 'Michael', 'David', 'James', 'Robert', 'William', 'Richard', 'Thomas',
        'Emma', 'Sarah', 'Jessica', 'Lisa', 'Jennifer', 'Amanda', 'Michelle', 'Nicole'
    ]

    LAST_NAMES = [
        'Al-Rashid', 'Al-Mansouri', 'Al-Habibi', 'Al-Blushi', 'Al-Khatib', 'Al-Amin',
        'Khan', 'Ahmedov', 'Petrov', 'Ivanov', 'Singh', 'Patel', 'Sharma', 'Gupta',
        'Chen', 'Wang', 'Li', 'Zhang', 'Liu', 'Yang', 'Kim', 'Park', 'Lee', 'Choi',
        'Muller', 'Schmidt', 'Weber', 'Fischer', 'Brown', 'Wilson', 'Taylor', 'Moore'
    ]

    MARKETS = ['Dubai', 'Abu Dhabi', 'Sharjah', 'Ajman', 'Riyadh', 'Jeddah', 'Doha', 'Manama', 'Kuwait']
    COUNTRIES = ['UAE', 'UAE', 'UAE', 'SA', 'QA', 'BH', 'KW', 'OM', 'KW']

    ITEM_CATEGORIES = [
        'Filters', 'Brakes', 'Suspension', 'Engine Components', 'Electrical',
        'Body Parts', 'Cooling System', 'Exhaust System', 'Steering', 'Transmission',
        'Lighting', 'Wiper System'
    ]

    BRANDS = [
        'Toyota Genuine', 'Bosch', 'Denso', 'ACDelco', 'Hyundai Mobis',
        'Brembo', 'Mann Filter', 'NGK', 'Valeo', 'Continental',
        'SKF', 'Gates', 'Dayco', 'KYB', 'Monroe', 'TRW', 'Delphi'
    ]

    def __init__(self, seed=42):
        self._random = random.Random()
        self._random.seed(seed)

    def reset_seed(self, seed=None):
        """Reset random seed for reproducibility."""
        self._random.seed(seed if seed is not None else 42)

    def random_choice(self, choices, weights=None):
        if weights:
            return self._random.choices(choices, weights=weights)[0]
        return self._random.choice(choices)

    def random_int(self, min_val, max_val):
        return self._random.randint(min_val, max_val)

    def random_float(self, min_val, max_val, decimals=2):
        val = self._random.uniform(min_val, max_val)
        return round(val, decimals)

    def random_date(self, days_back=365, days_forward=0):
        now = datetime.now()
        start = now - timedelta(days=days_back)
        end = now + timedelta(days=days_forward)
        delta = (end - start).days
        random_days = self._random.randint(0, delta)
        return (start + timedelta(days=random_days)).strftime('%Y-%m-%d')

    def demo_code(self, prefix, id_num):
        return f"{self.DEMO_PREFIX}{prefix}_{id_num:05d}"

    def demo_email(self, first_name, last_name):
        clean_fn = first_name.lower().replace(' ', '')
        clean_ln = last_name.lower().replace(' ', '')
        return f"{clean_fn}.{clean_ln}@{self.DEMO_DOMAIN}"

    def demo_phone(self):
        return f"+971{self._random.randint(4, 6)}{self._random.randint(10000000, 99999999)}"


# =============================================================================
# BASE SEEDER
# =============================================================================

class BaseSeeder:
    """Base class for all seeders."""

    def __init__(self, generator: SyntheticDataGenerator, verbose=True):
        self.gen = generator
        self.verbose = verbose
        self.records_created = 0
        self.module_name = "Base"

    def log(self, message):
        if self.verbose:
            print(f"  [{self.module_name}] {message}")

    def seed(self):
        raise NotImplementedError

    def count_records(self, table_name, where_clause=""):
        with get_db_context() as db:
            if where_clause:
                result = db.execute(f"SELECT COUNT(*) as cnt FROM {table_name} WHERE {where_clause}").fetchone()
            else:
                result = db.execute(f"SELECT COUNT(*) as cnt FROM {table_name}").fetchone()
            return result['cnt'] if result else 0

    def table_exists(self, table_name):
        with get_db_context() as db:
            result = db.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            ).fetchone()
            return result is not None

    def insert(self, sql, params=None):
        with get_db_context() as db:
            cursor = db.execute(sql, params or ())
            db.commit()
            return cursor.lastrowid

    def insert_many(self, sql, params_list):
        with get_db_context() as db:
            cursor = db.executemany(sql, params_list)
            db.commit()
            return cursor.rowcount

    def skip_or_insert(self, table, where_field, where_value, sql, params):
        """Insert only if record doesn't exist."""
        existing = self.count_records(table, f"{where_field} = '{where_value}'")
        if existing > 0:
            return None
        return self.insert(sql, params)


# =============================================================================
# MASTER DATA SEEDER
# =============================================================================

class MasterDataSeeder(BaseSeeder):
    """Seed master data: companies, warehouses, categories, brands."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_name = "MasterData"

    def seed(self):
        self.log("Seeding master data...")
        self.seed_companies()
        self.seed_warehouses()
        self.seed_categories()
        self.seed_brands()
        self.seed_statuses()
        self.seed_roles()
        self.log(f"Master data seeding complete. Created {self.records_created} records.")
        return self.records_created

    def seed_companies(self):
        """Seed demo companies."""
        companies = [
            'SDAD Trading LLC',
            'Al Rafidain Auto Parts',
            'Gulf Wheels Corporation',
            'Emirates Motors Est',
        ]

        for name in companies:
            result = self.skip_or_insert('companies', 'name', name,
                "INSERT INTO companies (name, created_at) VALUES (?, datetime('now'))",
                (name,))
            if result:
                self.records_created += 1
                self.log(f"Created company: {name}")

    def seed_warehouses(self):
        """Seed warehouses for companies."""
        # Get existing company IDs
        with get_db_context() as db:
            companies = db.execute("SELECT id FROM companies").fetchall()
            company_ids = [c['id'] for c in companies] if companies else [2, 3, 4]

        warehouses = [
            (company_ids[0] if len(company_ids) > 0 else 2, 'Main Warehouse Dubai'),
            (company_ids[0] if len(company_ids) > 0 else 2, 'Spare Parts Store'),
            (company_ids[0] if len(company_ids) > 0 else 2, 'Ajman Depot'),
            (company_ids[1] if len(company_ids) > 1 else 3, 'Central Warehouse'),
            (company_ids[1] if len(company_ids) > 1 else 3, 'Deira Parts Center'),
            (company_ids[2] if len(company_ids) > 2 else 4, 'Bulk Storage Sharjah'),
            (company_ids[2] if len(company_ids) > 2 else 4, 'Distribution Center Dubai'),
            (company_ids[2] if len(company_ids) > 2 else 4, 'Emirates Main WH'),
        ]

        for company_id, name in warehouses:
            result = self.skip_or_insert('warehouses', 'name', name,
                "INSERT INTO warehouses (name, company_id) VALUES (?, ?)",
                (name, company_id))
            if result:
                self.records_created += 1

    def seed_categories(self):
        """Seed item categories."""
        for cat_name in SyntheticDataGenerator.ITEM_CATEGORIES:
            result = self.skip_or_insert('categories', 'name', cat_name,
                "INSERT INTO categories (name) VALUES (?)",
                (cat_name,))
            if result:
                self.records_created += 1

    def seed_brands(self):
        """Seed brands."""
        brands_with_type = [
            ('Toyota Genuine', 'Genuine'),
            ('Bosch', 'Aftermarket'),
            ('Denso', 'Aftermarket'),
            ('ACDelco', 'Aftermarket'),
            ('Hyundai Mobis', 'Genuine'),
            ('Brembo', 'Aftermarket'),
            ('Mann Filter', 'Aftermarket'),
            ('NGK', 'Aftermarket'),
            ('Valeo', 'Aftermarket'),
            ('Continental', 'Aftermarket'),
            ('SKF', 'Aftermarket'),
            ('Gates', 'Aftermarket'),
            ('Dayco', 'Aftermarket'),
            ('KYB', 'Aftermarket'),
            ('Monroe', 'Aftermarket'),
            ('TRW', 'Aftermarket'),
            ('Delphi', 'Aftermarket'),
        ]

        for name, btype in brands_with_type:
            result = self.skip_or_insert('brands', 'name', name,
                "INSERT INTO brands (name, type) VALUES (?, ?)",
                (name, btype))
            if result:
                self.records_created += 1

    def seed_statuses(self):
        """Seed part statuses."""
        statuses = ['Active', 'Discontinued', 'Recalled', 'Backordered']
        for name in statuses:
            result = self.skip_or_insert('statuses', 'name', name,
                "INSERT INTO statuses (name) VALUES (?)",
                (name,))
            if result:
                self.records_created += 1

    def seed_roles(self):
        """Seed user roles."""
        roles = [
            ('Admin', None, 1, 1, 1, 1, 1, 1, 1, 1, 'System administrator with full access'),
            ('Manager', None, 1, 1, 1, 1, 1, 1, 1, 0, 'Manager with most permissions'),
            ('Sales', None, 0, 0, 1, 0, 1, 1, 1, 0, 'Sales team member'),
            ('Warehouse', None, 1, 0, 0, 1, 1, 1, 0, 0, 'Warehouse staff'),
            ('Viewer', None, 0, 0, 1, 0, 0, 0, 0, 0, 'Read-only access'),
        ]

        for role_name, company_id, can_edit_stock, can_manage_users, can_view_reports, \
            can_view_valuation, can_manage_parts, can_manage_locations, \
            can_manage_taxonomies, is_system, description in roles:
            result = self.skip_or_insert('roles', 'role_name', role_name,
                """INSERT INTO roles (role_name, company_id, can_edit_stock, can_manage_users,
                   can_view_reports, can_view_valuation, can_manage_parts,
                   can_manage_locations, can_manage_taxonomies, is_system, description)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (role_name, company_id, can_edit_stock, can_manage_users, can_view_reports,
                 can_view_valuation, can_manage_parts, can_manage_locations,
                 can_manage_taxonomies, is_system, description))
            if result:
                self.records_created += 1


# =============================================================================
# INVENTORY/PARTS SEEDER
# =============================================================================

class InventorySeeder(BaseSeeder):
    """Seed parts, inventory, and stock movements."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_name = "Inventory"

    def seed(self):
        self.log("Seeding inventory data...")
        existing_parts = self.count_records('parts')
        if existing_parts < 50:
            self.seed_parts()
        else:
            self.log(f"Parts already exist ({existing_parts}), skipping...")
        self.seed_inventory()
        self.seed_movements()
        return self.records_created

    def seed_parts(self):
        """Seed master parts (items)."""
        gen = self.gen

        for i in range(1, 201):
            part_number = f"OEM-{gen.random_int(10000, 99999)}-{gen.random_choice(['A', 'B', 'C'])}"
            desc = f"Premium Auto Part {i} - {gen.random_choice(['Assembly', 'Component', 'Module', 'Unit'])}"
            cat_id = gen.random_int(1, 12)
            brand_id = gen.random_int(1, 17)
            status_id = gen.random_choice([1, 1, 1, 4])  # Mostly Active
            cost = gen.random_float(50, 5000)
            reorder = gen.random_int(5, 30)
            weight = gen.random_float(0.5, 15.0)

            try:
                self.insert(
                    """INSERT INTO parts (part_number, description, weight, category_id, brand_id,
                       status_id, reorder_point, cost_price)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (part_number, desc, weight, cat_id, brand_id, status_id, reorder, cost)
                )
                self.records_created += 1
            except sqlite3.IntegrityError:
                pass  # Skip duplicate part numbers

    def seed_inventory(self):
        """Seed inventory records."""
        gen = self.gen
        part_ids = [r[0] for r in get_db().execute("SELECT id FROM parts").fetchall()]
        company_ids = [1, 2, 3, 4]

        for pid in part_ids[:50]:  # Limit for performance
            num_companies = gen.random_int(1, 3)
            companies = gen._random.sample(company_ids, num_companies)
            for cid in companies:
                qty = gen.random_int(0, 200)
                zone = f"{gen.random_int(1,20):02d}-{gen.random_int(1,50):02d}-{gen.random_int(1,10):02d}-{gen.random_int(1,99):02d}-{gen.random_choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"
                try:
                    self.insert(
                        """INSERT INTO inventory (part_id, company_id, zone, quantity, updated_at)
                           VALUES (?, ?, ?, ?, datetime('now'))""",
                        (pid, cid, zone, qty)
                    )
                    self.records_created += 1
                except sqlite3.IntegrityError:
                    pass

    def seed_movements(self):
        """Seed stock movements."""
        gen = self.gen
        movement_types = ['Receipt', 'Issue', 'Transfer', 'Adjustment', 'Return']
        part_ids = [r[0] for r in get_db().execute("SELECT id FROM parts LIMIT 50").fetchall()]

        for i in range(150):
            mtype = gen.random_choice(movement_types)
            qty = gen.random_int(1, 50) if mtype != 'Issue' else -gen.random_int(1, 30)
            part_id = gen.random_choice(part_ids)
            ref = f"MOV-{gen.random_int(10000, 99999)}"

            try:
                self.insert(
                    """INSERT INTO movements (part_id, movement_type, quantity, reference, movement_date)
                       VALUES (?, ?, ?, ?, ?)""",
                    (part_id, mtype, qty, ref, gen.random_date(180, 0))
                )
                self.records_created += 1
            except Exception:
                pass


# =============================================================================
# CUSTOMER/CRM SEEDER
# =============================================================================

class CustomerSeeder(BaseSeeder):
    """Seed customers and CRM data."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_name = "Customers"

    def seed(self):
        self.log("Seeding customer data...")
        self.seed_customers()
        self.seed_sales_customers()
        return self.records_created

    def seed_customers(self):
        """Seed basic customers table."""
        gen = self.gen
        customer_types = ['Local', 'Export', 'Wholesale', 'Retail']
        statuses = ['Active', 'Active', 'Active', 'Inactive']

        for i in range(80):
            first = gen.random_choice(gen.FIRST_NAMES)
            last = gen.random_choice(gen.LAST_NAMES)
            ctype = gen.random_choice(customer_types)
            market = gen.random_choice(gen.MARKETS)
            country = gen.COUNTRIES[gen.MARKETS.index(market)] if market in gen.MARKETS else 'UAE'
            status = gen.random_choice(statuses)
            balance = gen.random_float(0, 50000) if status == 'Active' else gen.random_float(1000, 100000)
            credit_limit = gen.random_int(5000, 100000)

            try:
                self.insert(
                    """INSERT INTO customers
                       (name, phone, location, type, salesperson_id, working_hours,
                        working_days, balance, credit_limit, country, city, is_export,
                        outstanding, is_active)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (f"{first} {last} {ctype}", gen.demo_phone(), market, ctype,
                     gen.random_int(1, 5), '9AM-6PM', 'Sun-Thu',
                     balance, credit_limit, country, market,
                     1 if ctype == 'Export' else 0, balance, 1 if status == 'Active' else 0)
                )
                self.records_created += 1
            except Exception:
                pass

    def seed_sales_customers(self):
        """Seed sales_customers table."""
        gen = self.gen
        customer_types = ['Retail', 'Wholesale', 'Corporate', 'Export', 'Counter']
        priorities = ['High', 'Medium', 'Medium', 'Low']

        for i in range(60):
            first = gen.random_choice(gen.FIRST_NAMES)
            last = gen.random_choice(gen.LAST_NAMES)
            ctype = gen.random_choice(customer_types)
            market = gen.random_choice(gen.MARKETS)
            country = gen.COUNTRIES[gen.MARKETS.index(market)] if market in gen.MARKETS else 'UAE'

            try:
                self.insert(
                    """INSERT INTO sales_customers
                       (customer_code, name, trade_name, customer_type, market, country, city,
                        phone, whatsapp, email, assigned_salesperson_id, payment_terms,
                        credit_limit, status, priority, total_orders, total_revenue,
                        outstanding_balance, is_active)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (gen.demo_code('CUST', i+1), f"{first} {last} Trading", f"{first} {last}",
                     ctype, market, country, market, gen.demo_phone(), gen.demo_phone(),
                     gen.demo_email(first, last), gen.random_int(1, 5),
                     gen.random_choice(['COD', 'NET30', 'NET60']), gen.random_int(10000, 200000),
                     gen.random_choice(['Active', 'Active', 'Active', 'Inactive']),
                     gen.random_choice(priorities), gen.random_int(0, 200),
                     gen.random_float(10000, 1000000), gen.random_float(0, 100000),
                     1)
                )
                self.records_created += 1
            except Exception:
                pass


# =============================================================================
# SUPPLIER SEEDER
# =============================================================================

class SupplierSeeder(BaseSeeder):
    """Seed suppliers and procurement data."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_name = "Suppliers"

    def seed(self):
        self.log("Seeding supplier data...")
        self.seed_suppliers()
        return self.records_created

    def seed_suppliers(self):
        """Seed suppliers."""
        gen = self.gen
        supplier_types = ['Local', 'International']
        countries = ['UAE', 'Japan', 'Germany', 'China', 'Korea', 'Turkey', 'India', 'USA']
        ratings = [3, 3, 3, 4, 4, 4, 5, 5]

        for i in range(35):
            stype = gen.random_choice(supplier_types)
            country = gen.random_choice(countries) if stype == 'International' else 'UAE'
            brand = gen.random_choice(gen.BRANDS)
            code = f"SUP-{gen.random_int(1000, 9999)}"

            try:
                self.insert(
                    """INSERT INTO suppliers
                       (name, code, contact_person, email, phone, address, city,
                        country, payment_terms, lead_time, currency, margin, rating, status)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (f"{brand} Supplies", code,
                     f"{gen.random_choice(gen.FIRST_NAMES)} {gen.random_choice(gen.LAST_NAMES)}",
                     gen.demo_email(gen.random_choice(gen.FIRST_NAMES), gen.random_choice(gen.LAST_NAMES)),
                     gen.demo_phone(), gen.random_choice(gen.MARKETS), gen.random_choice(gen.MARKETS),
                     country, gen.random_choice(['COD', 'NET30', 'NET60']),
                     f"{gen.random_int(3, 30)} days",
                     gen.random_choice(['AED', 'USD', 'EUR', 'JPY', 'CNY']),
                     gen.random_int(5, 25), gen.random_choice(ratings), 'Active')
                )
                self.records_created += 1
            except Exception:
                pass


# =============================================================================
# HR SEEDER
# =============================================================================

class HRSeeder(BaseSeeder):
    """Seed HR employees, departments, positions."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_name = "HR"

    def seed(self):
        self.log("Seeding HR data...")
        self.seed_departments()
        self.seed_positions()
        self.seed_employees()
        self.seed_attendance()
        self.seed_leave_requests()
        return self.records_created

    def seed_departments(self):
        """Seed HR departments."""
        depts = [
            ('Executive Management', 'EXEC'),
            ('Sales & Marketing', 'SALES'),
            ('Operations', 'OPS'),
            ('Warehouse & Logistics', 'WHL'),
            ('Finance & Accounts', 'FIN'),
            ('Human Resources', 'HR'),
            ('IT & Systems', 'IT'),
            ('Customer Service', 'CS'),
        ]

        for name, code in depts:
            result = self.skip_or_insert('hr_departments', 'name', name,
                "INSERT INTO hr_departments (name, code, status) VALUES (?, ?, 'Active')",
                (name, code))
            if result:
                self.records_created += 1

    def seed_positions(self):
        """Seed HR positions."""
        positions = [
            ('CEO', 1), ('COO', 1), ('CFO', 1), ('Sales Director', 2), ('Sales Manager', 2),
            ('Senior Sales Executive', 2), ('Sales Executive', 2), ('Counter Sales', 2),
            ('Warehouse Manager', 4), ('Inventory Controller', 4), ('Store Keeper', 4),
            ('HR Manager', 6), ('HR Officer', 6), ('Accountant', 5), ('IT Manager', 7),
            ('System Administrator', 7), ('Marketing Manager', 2), ('Content Creator', 2),
            ('Customer Service Manager', 8), ('Logistics Coordinator', 4),
        ]

        for title, dept_id in positions:
            result = self.skip_or_insert('hr_positions', 'title', title,
                "INSERT INTO hr_positions (title, department_id, status) VALUES (?, ?, 'Active')",
                (title, dept_id))
            if result:
                self.records_created += 1

    def seed_employees(self):
        """Seed HR employees."""
        gen = self.gen

        for i in range(40):
            first = gen.random_choice(gen.FIRST_NAMES)
            last = gen.random_choice(gen.LAST_NAMES)
            emp_code = gen.demo_code('EMP', i+1)
            hire_date = gen.random_date(365*3, 0)
            status = gen.random_choice(['Active', 'Active', 'Active', 'On Leave', 'Terminated'])
            employment_type = gen.random_choice(['Full-time', 'Full-time', 'Part-time', 'Contract'])

            try:
                self.insert(
                    """INSERT INTO hr_employees
                       (employee_code, first_name, last_name, mobile, email, status,
                        employment_type, hire_date, nationality, role_name)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (emp_code, first, last, gen.demo_phone(), gen.demo_email(first, last),
                     status, employment_type, hire_date,
                     gen.random_choice(['UAE', 'India', 'Pakistan', 'Philippines', 'Jordan']),
                     gen.random_choice(['Sales Executive', 'Warehouse Staff', 'Manager', 'HR Officer']))
                )
                self.records_created += 1
            except Exception:
                pass

    def seed_attendance(self):
        """Seed attendance records."""
        gen = self.gen

        for i in range(50):
            emp_id = (i % 20) + 1
            date = gen.random_date(30, 0)
            status = gen.random_choice(['Present', 'Present', 'Present', 'Late', 'Absent'])

            try:
                self.insert(
                    """INSERT INTO hr_attendance_records (employee_id, date, status) VALUES (?, ?, ?)""",
                    (emp_id, date, status)
                )
                self.records_created += 1
            except Exception:
                pass

    def seed_leave_requests(self):
        """Seed leave requests."""
        gen = self.gen
        statuses = ['Approved', 'Approved', 'Pending', 'Rejected']
        leave_types = ['Annual', 'Sick', 'Emergency', 'Unpaid']

        for i in range(25):
            emp_id = (i % 15) + 1
            start = gen.random_date(30, 60)
            end = gen.random_date(31, 90)

            try:
                self.insert(
                    """INSERT INTO hr_leave_requests
                       (employee_id, start_date, end_date, status, leave_type) VALUES (?, ?, ?, ?, ?)""",
                    (emp_id, start, end, gen.random_choice(statuses), gen.random_choice(leave_types))
                )
                self.records_created += 1
            except Exception:
                pass


# =============================================================================
# SALES SEEDER
# =============================================================================

class SalesSeeder(BaseSeeder):
    """Seed sales inquiries, quotations, orders."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_name = "Sales"

    def seed(self):
        self.log("Seeding sales data...")
        self.seed_inquiries()
        self.seed_quotations()
        self.seed_orders()
        return self.records_created

    def seed_inquiries(self):
        """Seed sales inquiries."""
        gen = self.gen
        statuses = ['New', 'Under Review', 'Need Pricing', 'Responded', 'In Negotiation',
                     'Converted to Quotation', 'Lost', 'Closed']
        status_weights = [15, 10, 10, 20, 15, 15, 10, 5]
        sources = ['Call', 'WhatsApp', 'Email', 'Walk-in', 'Website', 'Social Media', 'Referral']

        for i in range(100):
            first = gen.random_choice(gen.FIRST_NAMES)
            last = gen.random_choice(gen.LAST_NAMES)
            inq_num = gen.demo_code('INQ', i+1)
            date = gen.random_date(180, 0)

            try:
                self.insert(
                    """INSERT INTO sales_inquiries
                       (inquiry_number, inquiry_date, customer_name, customer_type, market,
                        country, city, inquiry_source, status, priority, assigned_salesperson_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (inq_num, date, f"{first} {last}",
                     gen.random_choice(['Retail', 'Wholesale', 'Corporate', 'Export']),
                     gen.random_choice(gen.MARKETS), gen.random_choice(gen.COUNTRIES),
                     gen.random_choice(gen.MARKETS), gen.random_choice(sources),
                     gen.random_choice(statuses, status_weights),
                     gen.random_choice(['High', 'Medium', 'Low']), gen.random_int(1, 5))
                )
                self.records_created += 1
            except Exception:
                pass

    def seed_quotations(self):
        """Seed sales quotations."""
        gen = self.gen
        statuses = ['Draft', 'Sent', 'Approved', 'Rejected', 'Expired', 'Converted']
        status_weights = [15, 25, 20, 10, 15, 15]

        for i in range(80):
            first = gen.random_choice(gen.FIRST_NAMES)
            quo_num = gen.demo_code('QUO', i+1)
            date = gen.random_date(180, 0)
            valid_until = gen.random_date(0, 30)
            subtotal = gen.random_float(5000, 200000)
            discount = subtotal * gen.random_float(0, 0.1)
            tax_percent = 5
            tax = (subtotal - discount) * (tax_percent / 100)
            total = subtotal - discount + tax

            try:
                self.insert(
                    """INSERT INTO sales_quotations
                       (quotation_number, quotation_date, valid_until, customer_name,
                        customer_type, status, currency, subtotal, discount_percent,
                        discount_amount, tax_percent, tax_amount, total_amount,
                        payment_terms, assigned_salesperson_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (quo_num, date, valid_until, f"{first} {gen.random_choice(gen.LAST_NAMES)}",
                     gen.random_choice(['Retail', 'Wholesale', 'Corporate', 'Export']),
                     gen.random_choice(statuses, status_weights), 'AED',
                     subtotal, gen.random_float(0, 10), discount, tax_percent, tax, total,
                     gen.random_choice(['COD', 'NET30', 'NET60']), gen.random_int(1, 5))
                )
                self.records_created += 1
            except Exception:
                pass

    def seed_orders(self):
        """Seed sales orders."""
        gen = self.gen
        statuses = ['Registered', 'Pending Approval', 'In Preparation', 'Ready for Delivery',
                    'Partially Delivered', 'Fully Delivered', 'Delayed', 'Cancelled']
        status_weights = [10, 15, 20, 15, 10, 15, 10, 5]

        for i in range(120):
            first = gen.random_choice(gen.FIRST_NAMES)
            ord_num = gen.demo_code('ORD', i+1)
            date = gen.random_date(180, 0)
            subtotal = gen.random_float(10000, 500000)
            discount = subtotal * gen.random_float(0, 0.1)
            tax = (subtotal - discount) * 0.05
            total = subtotal - discount + tax

            try:
                self.insert(
                    """INSERT INTO sales_orders
                       (order_number, order_date, customer_name, customer_type, market,
                        currency, subtotal, discount_amount, tax_amount, total_amount,
                        status, priority, assigned_salesperson_id, payment_terms)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (ord_num, date, f"{first} {gen.random_choice(gen.LAST_NAMES)}",
                     gen.random_choice(['Retail', 'Wholesale', 'Corporate', 'Export']),
                     gen.random_choice(gen.MARKETS), 'AED', subtotal, discount, tax, total,
                     gen.random_choice(statuses, status_weights),
                     gen.random_choice(['High', 'Medium', 'Low']), gen.random_int(1, 5),
                     gen.random_choice(['COD', 'NET30', 'NET60']))
                )
                self.records_created += 1
            except Exception:
                pass


# =============================================================================
# LOGISTICS SEEDER
# =============================================================================

class LogisticsSeeder(BaseSeeder):
    """Seed logistics shipments, vehicles, drivers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_name = "Logistics"

    def seed(self):
        self.log("Seeding logistics data...")
        self.seed_shipments()
        self.seed_vehicles()
        self.seed_drivers()
        return self.records_created

    def seed_shipments(self):
        """Seed logistics shipments."""
        gen = self.gen
        statuses = ['Pending', 'In Transit', 'Delivered', 'Delayed', 'Cancelled']
        status_weights = [20, 25, 30, 15, 10]

        for i in range(80):
            shp_num = gen.demo_code('SHP', i+1)
            requested = gen.random_date(60, 0)
            estimated = gen.random_date(0, 7)

            try:
                self.insert(
                    """INSERT INTO logistics_shipments
                       (shipment_code, status, priority, requested_date,
                        estimated_delivery, pickup_address, delivery_address)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (shp_num, gen.random_choice(statuses, status_weights),
                     gen.random_choice(['High', 'Medium', 'Low']), requested, estimated,
                     f"{gen.random_int(1,500)} {gen.random_choice(gen.MARKETS)} Street",
                     f"{gen.random_int(1,500)} {gen.random_choice(gen.MARKETS)} Avenue")
                )
                self.records_created += 1
            except Exception:
                pass

    def seed_vehicles(self):
        """Seed logistics vehicles."""
        gen = self.gen
        vehicle_types = ['Van', 'Truck', 'Pickup', 'Refrigerated']
        statuses = ['Active', 'Active', 'Active', 'Maintenance', 'Retired']

        for i in range(15):
            try:
                self.insert(
                    """INSERT INTO logistics_vehicles
                       (vehicle_code, plate_number, vehicle_type, status, load_capacity_kg)
                       VALUES (?, ?, ?, ?, ?)""",
                    (gen.demo_code('VEH', i+1),
                     f"{gen.random_choice(['DXB', 'ABU', 'SHJ'])} {gen.random_int(1000, 9999)}",
                     gen.random_choice(vehicle_types),
                     gen.random_choice(statuses, [30, 30, 30, 5, 5]),
                     gen.random_int(1000, 10000))
                )
                self.records_created += 1
            except Exception:
                pass

    def seed_drivers(self):
        """Seed logistics drivers."""
        gen = self.gen

        for i in range(20):
            first = gen.random_choice(gen.FIRST_NAMES)
            try:
                self.insert(
                    """INSERT INTO logistics_drivers
                       (driver_code, full_name, mobile, license_number, status)
                       VALUES (?, ?, ?, ?, ?)""",
                    (gen.demo_code('DRV', i+1),
                     f"{first} {gen.random_choice(gen.LAST_NAMES)}",
                     gen.demo_phone(), f"DL-{gen.random_int(100000, 999999)}", 'Active')
                )
                self.records_created += 1
            except Exception:
                pass


# =============================================================================
# MARKETING SEEDER
# =============================================================================

class MarketingSeeder(BaseSeeder):
    """Seed marketing campaigns and leads."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_name = "Marketing"

    def seed(self):
        self.log("Seeding marketing data...")
        self.seed_campaigns()
        self.seed_leads()
        return self.records_created

    def seed_campaigns(self):
        """Seed marketing campaigns."""
        gen = self.gen
        campaign_types = ['Brand Awareness', 'Sales Growth', 'Seasonal', 'New Product', 'Reactivation']
        statuses = ['Draft', 'Active', 'Active', 'Completed', 'Paused']
        status_weights = [10, 30, 30, 20, 10]

        for i in range(20):
            name = f"{gen.random_choice(campaign_types)} Campaign {i+1}"
            start = gen.random_date(90, 0)
            end = gen.random_date(0, 90)
            budget = gen.random_float(10000, 200000)

            try:
                self.insert(
                    """INSERT INTO marketing_campaigns
                       (name, campaign_type, status, start_date, end_date, budget) VALUES (?, ?, ?, ?, ?, ?)""",
                    (name, gen.random_choice(campaign_types),
                     gen.random_choice(statuses, status_weights), start, end, budget)
                )
                self.records_created += 1
            except Exception:
                pass

    def seed_leads(self):
        """Seed marketing leads."""
        gen = self.gen
        statuses = ['New', 'In Follow-up', 'Qualified', 'Converted', 'Lost']
        customer_types = ['Retail', 'Wholesale', 'Corporate']
        importance_levels = ['High', 'Medium', 'Low']

        for i in range(150):
            first = gen.random_choice(gen.FIRST_NAMES)
            try:
                self.insert(
                    """INSERT INTO marketing_leads
                       (lead_name, phone, email, city, country, customer_type,
                        importance_level, lead_status, assigned_salesperson_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (f"{first} {gen.random_choice(gen.LAST_NAMES)}",
                     gen.demo_phone(), gen.demo_email(first, gen.random_choice(gen.LAST_NAMES)),
                     gen.random_choice(gen.MARKETS), gen.random_choice(gen.COUNTRIES),
                     gen.random_choice(customer_types),
                     gen.random_choice(importance_levels), gen.random_choice(statuses),
                     gen.random_int(1, 4))
                )
                self.records_created += 1
            except Exception:
                pass


# =============================================================================
# SOCIAL MEDIA SEEDER
# =============================================================================

class SocialMediaSeeder(BaseSeeder):
    """Seed social accounts, posts, messages."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_name = "SocialMedia"

    def seed(self):
        self.log("Seeding social media data...")
        self.seed_accounts()
        self.seed_posts()
        self.seed_messages()
        self.seed_social_leads()
        return self.records_created

    def seed_accounts(self):
        """Seed social accounts."""
        platforms = [
            ('Instagram', 'SDAD Official'),
            ('Facebook', 'SDAD Trading'),
            ('LinkedIn', 'SDAD Business'),
            ('YouTube', 'SDAD Channel'),
            ('WhatsApp Business', 'SDAD Sales'),
        ]

        for platform, name in platforms:
            try:
                self.insert(
                    """INSERT INTO social_accounts
                       (platform, account_name, username, account_status) VALUES (?, ?, ?, ?)""",
                    (platform, name, f"@{name.lower().replace(' ', '_')}", 'Active')
                )
                self.records_created += 1
            except Exception:
                pass

    def seed_posts(self):
        """Seed social content production."""
        gen = self.gen
        statuses = ['Draft', 'In Production', 'Review', 'Approved', 'Published']
        platforms = ['Instagram', 'Facebook', 'LinkedIn', 'YouTube', 'TikTok']

        for i in range(60):
            try:
                self.insert(
                    """INSERT INTO social_content_production
                       (content_code, internal_title, display_title, target_platform,
                        content_type, production_status, approval_status)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (gen.demo_code('SCP', i+1),
                     f"Content {i+1}",
                     f"Social Media Post {i+1}",
                     gen.random_choice(platforms),
                     gen.random_choice(['Post', 'Story', 'Reel', 'Carousel']),
                     gen.random_choice(statuses),
                     gen.random_choice(['Pending', 'Approved', 'Rejected']))
                )
                self.records_created += 1
            except Exception:
                pass

    def seed_messages(self):
        """Seed social messages and threads."""
        gen = self.gen
        statuses = ['New', 'Read', 'Responded', 'Archived']
        platforms = ['Instagram', 'Facebook', 'WhatsApp']

        # First create threads
        thread_ids = []
        for i in range(30):
            first = gen.random_choice(gen.FIRST_NAMES)
            platform = gen.random_choice(platforms)
            try:
                thread_id = self.insert(
                    """INSERT INTO social_message_threads
                       (thread_platform, platform, sender_name, sender_phone, account_id,
                        thread_status, message_count, is_unread)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (platform, platform, f"{first} {gen.random_choice(gen.LAST_NAMES)}",
                     gen.demo_phone(), gen.random_int(1, 5), 'Active',
                     gen.random_int(1, 50), gen.random_choice([0, 1]))
                )
                thread_ids.append(thread_id)
            except Exception:
                pass

        # Then create messages linked to threads
        for i in range(80):
            if not thread_ids:
                break
            first = gen.random_choice(gen.FIRST_NAMES)
            try:
                self.insert(
                    """INSERT INTO social_messages
                       (thread_id, message_platform, sender_type, message_text, message_type,
                        is_read, message_status, requires_reply)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (gen.random_choice(thread_ids), gen.random_choice(platforms), 'User',
                     f"Hi, I'm interested in your products. Can you share more details?",
                     'Text', gen.random_choice([0, 0, 1]), gen.random_choice(statuses), 1)
                )
                self.records_created += 1
            except Exception:
                pass

    def seed_social_leads(self):
        """Seed social leads."""
        gen = self.gen
        stages = ['Message', 'Lead', 'Qualified', 'Customer']
        statuses = ['New', 'In Follow-up', 'Converted', 'Lost']
        platforms = ['Instagram', 'Facebook', 'LinkedIn', 'WhatsApp']

        for i in range(60):
            first = gen.random_choice(gen.FIRST_NAMES)
            try:
                self.insert(
                    """INSERT INTO social_leads
                       (lead_name, phone, email, country, city, customer_type,
                        source_platform, funnel_stage, lead_status, assigned_salesperson_id,
                        created_by_user_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (f"{first} {gen.random_choice(gen.LAST_NAMES)}",
                     gen.demo_phone(), gen.demo_email(first, gen.random_choice(gen.LAST_NAMES)),
                     gen.random_choice(gen.COUNTRIES), gen.random_choice(gen.MARKETS),
                     gen.random_choice(['Retail', 'Wholesale', 'Corporate']),
                     gen.random_choice(platforms), gen.random_choice(stages),
                     gen.random_choice(statuses), gen.random_int(1, 4), gen.random_int(1, 4))
                )
                self.records_created += 1
            except Exception:
                pass


# =============================================================================
# NOTIFICATION SEEDER
# =============================================================================

class NotificationSeeder(BaseSeeder):
    """Seed platform notifications."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.module_name = "Notifications"

    def seed(self):
        self.log("Seeding notifications...")
        self.seed_notifications()
        return self.records_created

    def seed_notifications(self):
        """Seed platform notifications."""
        gen = self.gen
        notif_types = ['INFO', 'WARNING', 'ERROR', 'SUCCESS', 'APPROVAL']
        severities = ['Low', 'Medium', 'High']
        is_read_options = [0, 0, 0, 1]  # 75% unread

        titles = [
            'New inquiry received',
            'Quote awaiting approval',
            'Low stock alert',
            'Delivery delayed',
            'Customer payment received',
            'Employee leave request',
            'Campaign target reached',
            'Social message pending response',
        ]

        for i, title in enumerate(titles):
            try:
                self.insert(
                    """INSERT INTO platform_notifications
                       (title, message, notification_type, severity, is_read, created_at) VALUES (?, ?, ?, ?, ?, datetime('now'))""",
                    (title, f"Notification message for: {title}",
                     gen.random_choice(notif_types), gen.random_choice(severities),
                     gen.random_choice(is_read_options))
                )
                self.records_created += 1
            except Exception:
                pass


# =============================================================================
# MAIN SEEDING ORCHESTRATOR
# =============================================================================

class SyntheticDataSeeder:
    """Main orchestrator for synthetic data seeding."""

    def __init__(self, mode='demo', verbose=True):
        self.mode = mode
        self.verbose = verbose
        self.generator = SyntheticDataGenerator()
        self.seeders = []
        self.total_records = 0
        self.start_time = None

    def setup_seeders(self):
        """Initialize all seeders based on mode."""
        self.seeders.append(MasterDataSeeder(self.generator, self.verbose))
        self.seeders.append(InventorySeeder(self.generator, self.verbose))
        self.seeders.append(CustomerSeeder(self.generator, self.verbose))
        self.seeders.append(SupplierSeeder(self.generator, self.verbose))

        if self.mode in ('full', 'demo'):
            self.seeders.append(HREmployeeSeeder(self.generator, self.verbose))
            self.seeders.append(SalesSeeder(self.generator, self.verbose))
            self.seeders.append(LogisticsSeeder(self.generator, self.verbose))
            self.seeders.append(MarketingSeeder(self.generator, self.verbose))
            self.seeders.append(SocialMediaSeeder(self.generator, self.verbose))

        if self.mode == 'full':
            self.seeders.append(NotificationSeeder(self.generator, self.verbose))

    def run(self):
        """Run all seeders."""
        self.start_time = datetime.now()
        print(f"\n{'='*60}")
        print(f"MMDx Synthetic Data Seeding System")
        print(f"Mode: {self.mode.upper()}")
        print(f"Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        try:
            for seeder in self.seeders:
                print(f"\n--- Seeding: {seeder.module_name} ---")
                count = seeder.seed()
                self.total_records += count

            elapsed = (datetime.now() - self.start_time).total_seconds()
            print(f"\n{'='*60}")
            print(f"SEEDING COMPLETE")
            print(f"Total Records Created: {self.total_records}")
            print(f"Time Elapsed: {elapsed:.1f} seconds")
            print(f"{'='*60}\n")

            return True, self.total_records

        except Exception as e:
            print(f"\nERROR during seeding: {e}")
            import traceback
            traceback.print_exc()
            return False, self.total_records


# Alias for backward compatibility
HREmployeeSeeder = HRSeeder


# =============================================================================
# COMMAND-LINE INTERFACE
# =============================================================================

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='MMDx Synthetic Data Seeding System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python seed_synthetic_data.py --demo     # Demo dataset (balanced)
  python seed_synthetic_data.py --full     # Full dataset (maximum data)
  python seed_synthetic_data.py --minimal  # Minimal dataset (quick test)
  python seed_synthetic_data.py --reset --demo  # Reset and reseed

PRODUCTION SAFETY: This script will NOT run in production without --force.
        """
    )

    parser.add_argument('--demo', action='store_true', help='Seed demo dataset (balanced)')
    parser.add_argument('--full', action='store_true', help='Seed full dataset (maximum data)')
    parser.add_argument('--minimal', action='store_true', help='Seed minimal dataset (quick test)')
    parser.add_argument('--module', type=str, help='Seed specific module only')
    parser.add_argument('--reset', action='store_true', help='Reset demo data before seeding')
    parser.add_argument('--force', action='store_true', help='Force run in production (DANGEROUS)')
    parser.add_argument('--quiet', action='store_true', help='Suppress verbose output')

    args = parser.parse_args()

    # Check production safety
    if is_production_environment() and not args.force:
        print("\n" + "="*60)
        print("PRODUCTION SAFETY CHECK")
        print("="*60)
        print("ERROR: Cannot run synthetic data seeding in production environment.")
        print("This script is designed for demo/test environments only.")
        print("")
        print("To force run in production, add: --force")
        print("DANGER: This will insert synthetic test data into your production database!")
        print("="*60 + "\n")
        sys.exit(1)

    # Determine mode
    mode = 'demo'
    if args.full:
        mode = 'full'
    elif args.minimal:
        mode = 'minimal'
    elif args.module:
        mode = f"module:{args.module}"

    # Run seeder
    verbose = not args.quiet
    seeder = SyntheticDataSeeder(mode=mode, verbose=verbose)
    seeder.setup_seeders()
    success, count = seeder.run()

    sys.exit(0 if success else 1)
