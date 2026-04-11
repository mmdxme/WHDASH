"""
Comprehensive Demo Data Seeder - Fills ALL Empty Tables
========================================================
This script fills all 383 empty tables with sample demo data.
It is idempotent - safe to run multiple times.

Usage:
    python seed_comprehensive.py

Author: MMDx Data Seeding System
"""

import os
import sys
import sqlite3
import random
from datetime import datetime, timedelta
import hashlib

# Database path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'warehouse.db')

# Fix UTF-8 encoding on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except:
    pass


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def table_exists(table, db):
    """Check if table exists."""
    result = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    ).fetchone()
    return result is not None


def get_count(table, db):
    """Get row count for a table."""
    try:
        return db.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
    except:
        return 0


def get_columns(table, db):
    """Get column names for a table."""
    try:
        cursor = db.execute(f"PRAGMA table_info([{table}])")
        return [row[1] for row in cursor.fetchall()]
    except:
        return []


def seed_safe(table, db, data_fn, id_field='id'):
    """Safely seed a table if it's empty."""
    count = get_count(table, db)
    if count > 0:
        return False
    
    cols = get_columns(table, db)
    if not cols:
        return False
    
    try:
        data_fn(db, cols)
        return True
    except Exception as e:
        print(f"      Error seeding {table}: {e}")
        return False


def get_any_id(table, db, limit=1):
    """Get any ID from a table."""
    try:
        result = db.execute(f"SELECT id FROM [{table}] LIMIT {limit}").fetchall()
        return [r['id'] for r in result]
    except:
        return []


def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime('%Y-%m-%d')


# =============================================================================
# MASTER DATA (md_ tables)
# =============================================================================

def seed_md_tables(db, cols):
    """Seed all md_ (master data) tables."""
    
    # md_country
    if table_exists('md_country', db) and get_count('md_country', db) == 0:
        countries = [
            ('UAE', 'United Arab Emirates', 'AE', '+971'),
            ('SA', 'Saudi Arabia', 'SA', '+966'),
            ('QA', 'Qatar', 'QA', '+974'),
            ('KW', 'Kuwait', 'KW', '+965'),
            ('BH', 'Bahrain', 'BH', '+973'),
            ('OM', 'Oman', 'OM', '+968'),
            ('EG', 'Egypt', 'EG', '+20'),
            ('JO', 'Jordan', 'JO', '+962'),
            ('LB', 'Lebanon', 'LB', '+961'),
            ('IQ', 'Iraq', 'IQ', '+964'),
            ('IR', 'Iran', 'IR', '+98'),
            ('US', 'United States', 'US', '+1'),
            ('UK', 'United Kingdom', 'GB', '+44'),
            ('DE', 'Germany', 'DE', '+49'),
            ('FR', 'France', 'FR', '+33'),
            ('CN', 'China', 'CN', '+86'),
            ('IN', 'India', 'IN', '+91'),
            ('JP', 'Japan', 'JP', '+81'),
            ('SG', 'Singapore', 'SG', '+65'),
        ]
        for code, name, iso, phone in countries:
            db.execute("INSERT INTO md_country (code, name, iso_code, phone_code) VALUES (?, ?, ?, ?)",
                      (code, name, iso, phone))
        print("      + md_country: 19 countries")
    
    # md_currency
    if table_exists('md_currency', db) and get_count('md_currency', db) == 0:
        currencies = [
            ('AED', 'UAE Dirham', 'د.إ', 2),
            ('SAR', 'Saudi Riyal', 'ر.س', 2),
            ('USD', 'US Dollar', '$', 2),
            ('EUR', 'Euro', '€', 2),
            ('GBP', 'British Pound', '£', 2),
            ('JPY', 'Japanese Yen', '¥', 0),
            ('CNY', 'Chinese Yuan', '¥', 2),
            ('INR', 'Indian Rupee', '₹', 2),
            ('AUD', 'Australian Dollar', 'A$', 2),
            ('CHF', 'Swiss Franc', 'CHF', 2),
        ]
        for code, name, symbol, decimals in currencies:
            db.execute("INSERT INTO md_currency (code, name, symbol, decimal_places) VALUES (?, ?, ?, ?)",
                      (code, name, symbol, decimals))
        print("      + md_currency: 10 currencies")
    
    # md_payment_term
    if table_exists('md_payment_term', db) and get_count('md_payment_term', db) == 0:
        terms = [
            ('NET 30', 'Net 30 Days', 30),
            ('NET 60', 'Net 60 Days', 60),
            ('NET 90', 'Net 90 Days', 90),
            ('CIA', 'Cash in Advance', 0),
            ('COD', 'Cash on Delivery', 0),
            ('2/10 NET 30', '2% Discount 10 Days Net 30', 30),
            ('IMMEDIATE', 'Immediate Payment', 0),
        ]
        for code, name, days in terms:
            db.execute("INSERT INTO md_payment_term (code, name, days) VALUES (?, ?, ?)",
                      (code, name, days))
        print("      + md_payment_term: 7 payment terms")
    
    # md_unit_of_measure
    if table_exists('md_unit_of_measure', db) and get_count('md_unit_of_measure', db) == 0:
        units = [
            ('PCS', 'Pieces', 'pcs', 1),
            ('KG', 'Kilograms', 'kg', 1000),
            ('LB', 'Pounds', 'lb', 453.592),
            ('L', 'Liters', 'L', 1),
            ('GAL', 'Gallons', 'gal', 3.785),
            ('M', 'Meters', 'm', 1),
            ('FT', 'Feet', 'ft', 0.3048),
            ('IN', 'Inches', 'in', 0.0254),
            ('BOX', 'Boxes', 'box', 1),
            ('CTN', 'Cartons', 'ctn', 1),
            ('PAL', 'Pallets', 'pal', 1),
        ]
        for code, name, abbrev, conversion in units:
            db.execute("INSERT INTO md_unit_of_measure (code, name, abbreviation, conversion_factor) VALUES (?, ?, ?, ?)",
                      (code, name, abbrev, conversion))
        print("      + md_unit_of_measure: 11 units")
    
    # Other md_ tables
    md_tables_data = {
        'md_region': [('DXB', 'Dubai', 'UAE'), ('AUH', 'Abu Dhabi', 'UAE'), ('SHJ', 'Sharjah', 'UAE'),
                      ('JED', 'Jeddah', 'SA'), ('RUH', 'Riyadh', 'SA'), ('DOH', 'Doha', 'QA')],
        'md_customer_type': [('Enterprise', 'Large Enterprise'), ('Corporate', 'Corporate Business'),
                            ('SMB', 'Small Medium Business'), ('Individual', 'Individual Customer'),
                            ('Government', 'Government Entity'), ('Education', 'Educational Institution')],
        'md_supplier_type': [('Manufacturer', 'Original Manufacturer'), ('Distributor', 'Authorized Distributor'),
                            ('Wholesaler', 'Wholesale Supplier'), ('Import', 'Import/Export'), ('Local', 'Local Supplier')],
        'md_lead_source': [('Website', 'Website Inquiry'), ('Referral', 'Referral'), ('Trade Show', 'Trade Show'),
                          ('Cold Call', 'Cold Calling'), ('Social Media', 'Social Media'), ('Partner', 'Partner Channel')],
        'md_leave_type': [('Annual', 'Annual Leave'), ('Sick', 'Sick Leave'), ('Emergency', 'Emergency Leave'),
                         ('Maternity', 'Maternity Leave'), ('Paternity', 'Paternity Leave')],
        'md_priority_level': [('Low', 'Low Priority'), ('Medium', 'Medium Priority'), ('High', 'High Priority'), ('Urgent', 'Urgent/Critical')],
        'md_order_status': [('Draft', 'Draft'), ('Submitted', 'Submitted'), ('Confirmed', 'Confirmed'),
                            ('Processing', 'Processing'), ('Shipped', 'Shipped'), ('Delivered', 'Delivered'), ('Cancelled', 'Cancelled')],
        'md_quotation_status': [('Draft', 'Draft'), ('Sent', 'Sent to Customer'), ('Reviewed', 'Under Review'),
                               ('Accepted', 'Accepted'), ('Rejected', 'Rejected'), ('Expired', 'Expired')],
        'md_shipment_status': [('Pending', 'Pending'), ('Picked', 'Picked Up'), ('In Transit', 'In Transit'),
                              ('Out for Delivery', 'Out for Delivery'), ('Delivered', 'Delivered'), ('Returned', 'Returned')],
        'md_incoterm': [('EXW', 'Ex Works'), ('FCA', 'Free Carrier'), ('CPT', 'Carriage Paid To'),
                       ('CIP', 'Carriage Insurance Paid To'), ('DAP', 'Delivered at Place'), ('DDP', 'Delivered Duty Paid')],
        'md_tax_rule': [('VAT5', 'VAT 5%', 5), ('VAT0', 'Zero Rated', 0), ('EXEMPT', 'Exempt', 0)],
        'md_document_type': [('Contract', 'Contract'), ('Invoice', 'Invoice'), ('Receipt', 'Receipt'),
                            ('Certificate', 'Certificate'), ('License', 'License'), ('Report', 'Report')],
        'md_alert_type': [('Low Stock', 'Low Stock Alert'), ('Overdue', 'Overdue Alert'), ('Budget', 'Budget Alert')],
        'md_campaign_type': [('Email', 'Email Campaign'), ('Social', 'Social Media Campaign'),
                            ('Display', 'Display Ads'), ('Search', 'Search Engine Marketing')],
        'md_content_type': [('Blog', 'Blog Post'), ('Video', 'Video'), ('Infographic', 'Infographic'),
                          ('Whitepaper', 'Whitepaper'), ('Webinar', 'Webinar')],
        'md_complaint_type': [('Product', 'Product Complaint'), ('Service', 'Service Complaint'),
                             ('Delivery', 'Delivery Complaint'), ('Billing', 'Billing Complaint')],
        'md_social_platform': [('Instagram', 'Instagram'), ('LinkedIn', 'LinkedIn'), ('Twitter', 'Twitter/X'),
                              ('Facebook', 'Facebook'), ('YouTube', 'YouTube'), ('TikTok', 'TikTok')],
        'md_inquiry_stage': [('New', 'New'), ('Contacted', 'Contacted'), ('Qualified', 'Qualified'),
                            ('Proposal', 'Proposal Sent'), ('Negotiation', 'Negotiation'), ('Won', 'Won'), ('Lost', 'Lost')],
        'md_opportunity_stage': [('Qualification', 'Qualification'), ('Needs Analysis', 'Needs Analysis'),
                                ('Value Proposition', 'Value Proposition'), ('Decision', 'Decision'),
                                ('Negotiation', 'Negotiation'), ('Closed Won', 'Closed Won'), ('Closed Lost', 'Closed Lost')],
        'md_sales_channel': [('Direct', 'Direct Sales'), ('Retail', 'Retail'), ('Wholesale', 'Wholesale'),
                            ('E-commerce', 'E-commerce'), ('Distributor', 'Distributor')],
        'md_return_reason': [('Defective', 'Defective Product'), ('Wrong Item', 'Wrong Item Shipped'),
                            ('Changed Mind', 'Changed Mind'), ('Damaged', 'Damaged in Shipping'),
                            ('Not as Described', 'Not as Described')],
    }
    
    for table, data in md_tables_data.items():
        if table_exists(table, db) and get_count(table, db) == 0:
            try:
                for row in data:
                    placeholders = ','.join(['?'] * len(row))
                    db.execute(f"INSERT INTO {table} (name, description) VALUES ({placeholders})" if len(row) == 2 
                              else f"INSERT INTO {table} (code, name) VALUES ({placeholders})", row)
                print(f"      + {table}: {len(data)} records")
            except Exception as e:
                # Try simpler insert
                try:
                    for row in data:
                        db.execute(f"INSERT INTO {table} (name) VALUES (?)", (row[0],))
                    print(f"      + {table}: {len(data)} records")
                except:
                    pass
    
    db.commit()


# =============================================================================
# SALES MODULE
# =============================================================================

def seed_sales_tables(db, cols):
    """Seed all empty sales tables."""
    
    # Get existing data for references
    cust_ids = get_any_id('sales_customers', db, 10)
    emp_ids = get_any_id('hr_employees', db, 5)
    if not cust_ids:
        cust_ids = [1]
    if not emp_ids:
        emp_ids = [1]
    
    # sales_inquiry_lines
    if table_exists('sales_inquiry_lines', db) and get_count('sales_inquiry_lines', db) == 0:
        inq_ids = get_any_id('sales_inquiries', db, 20)
        part_ids = get_any_id('parts', db, 20)
        if inq_ids and part_ids:
            for inq_id in inq_ids[:10]:
                for i in range(random.randint(1, 4)):
                    db.execute("""INSERT INTO sales_inquiry_lines 
                        (inquiry_id, part_id, description, quantity, unit_price, total_price, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (inq_id, random.choice(part_ids), f'Item description {i+1}',
                         random.randint(1, 100), random.uniform(10, 1000), 
                         random.uniform(100, 10000), now()))
            print("      + sales_inquiry_lines: inquiry lines added")
    
    # sales_quotation_lines
    if table_exists('sales_quotation_lines', db) and get_count('sales_quotation_lines', db) == 0:
        quo_ids = get_any_id('sales_quotations', db, 20)
        if quo_ids and part_ids:
            for quo_id in quo_ids[:15]:
                for i in range(random.randint(1, 5)):
                    qty = random.randint(1, 50)
                    price = random.uniform(50, 500)
                    db.execute("""INSERT INTO sales_quotation_lines
                        (quotation_id, part_id, description, quantity, unit_price, discount_percent, total_price, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (quo_id, random.choice(part_ids), f'Product {i+1}', qty, price,
                         random.uniform(0, 10), qty * price, now()))
            print("      + sales_quotation_lines: quotation lines added")
    
    # sales_orders
    if table_exists('sales_orders', db) and get_count('sales_orders', db) < 10:
        statuses = ['Draft', 'Confirmed', 'Processing', 'Shipped', 'Delivered']
        for i in range(20):
            db.execute("""INSERT INTO sales_orders
                (order_number, customer_id, order_date, delivery_date, status, total_amount, 
                 sales_person_id, payment_status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'SO-2026-{i+1:04d}', random.choice(cust_ids),
                 days_ago(random.randint(1, 60)), days_ago(random.randint(-30, 30)),
                 random.choice(statuses), random.uniform(5000, 150000),
                 random.choice(emp_ids), random.choice(['Pending', 'Partial', 'Paid']),
                 now()))
        print("      + sales_orders: 20 orders added")
    
    # sales_order_lines
    if table_exists('sales_order_lines', db) and get_count('sales_order_lines', db) < 20:
        order_ids = get_any_id('sales_orders', db, 50)
        if order_ids and part_ids:
            for order_id in order_ids[:30]:
                for i in range(random.randint(1, 5)):
                    qty = random.randint(1, 20)
                    price = random.uniform(100, 2000)
                    db.execute("""INSERT INTO sales_order_lines
                        (order_id, part_id, description, quantity, unit_price, discount_percent, total_price, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (order_id, random.choice(part_ids), f'Item {i+1}', qty, price,
                         random.uniform(0, 5), qty * price, now()))
            print("      + sales_order_lines: order lines added")
    
    # sales_deliveries
    if table_exists('sales_deliveries', db) and get_count('sales_deliveries', db) == 0:
        order_ids = get_any_id('sales_orders', db, 30)
        for i, order_id in enumerate(order_ids[:15]):
            db.execute("""INSERT INTO sales_deliveries
                (delivery_number, order_id, customer_id, delivery_date, status, 
                 driver_name, vehicle_number, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'DEL-2026-{i+1:04d}', order_id, random.choice(cust_ids),
                 days_ago(random.randint(-15, 15)), random.choice(['Pending', 'In Transit', 'Delivered']),
                 f'Driver {random.randint(1,10)}', f'VEh-{random.randint(100,999)}', now()))
        print("      + sales_deliveries: 15 deliveries added")
    
    # sales_delivery_lines
    if table_exists('sales_delivery_lines', db) and get_count('sales_delivery_lines', db) == 0:
        del_ids = get_any_id('sales_deliveries', db, 20)
        if del_ids and part_ids:
            for del_id in del_ids:
                for i in range(random.randint(1, 3)):
                    db.execute("""INSERT INTO sales_delivery_lines
                        (delivery_id, part_id, quantity, created_at)
                        VALUES (?, ?, ?, ?)""",
                        (del_id, random.choice(part_ids), random.randint(1, 20), now()))
            print("      + sales_delivery_lines: delivery lines added")
    
    # sales_invoices
    if table_exists('sales_invoices', db) and get_count('sales_invoices', db) == 0:
        for i in range(15):
            db.execute("""INSERT INTO sales_invoices
                (invoice_number, customer_id, invoice_date, due_date, status, total_amount,
                 tax_amount, paid_amount, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'INV-2026-{i+1:04d}', random.choice(cust_ids),
                 days_ago(random.randint(1, 90)), days_ago(random.randint(-30, 60)),
                 random.choice(['Draft', 'Sent', 'Paid', 'Overdue']),
                 random.uniform(1000, 50000), random.uniform(50, 2500),
                 random.uniform(0, 10000), now()))
        print("      + sales_invoices: 15 invoices added")
    
    # sales_invoice_lines
    if table_exists('sales_invoice_lines', db) and get_count('sales_invoice_lines', db) == 0:
        inv_ids = get_any_id('sales_invoices', db, 20)
        if inv_ids and part_ids:
            for inv_id in inv_ids:
                for i in range(random.randint(1, 5)):
                    qty = random.randint(1, 10)
                    price = random.uniform(100, 1000)
                    db.execute("""INSERT INTO sales_invoice_lines
                        (invoice_id, part_id, description, quantity, unit_price, total_price, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (inv_id, random.choice(part_ids), f'Item {i+1}', qty, price, qty * price, now()))
            print("      + sales_invoice_lines: invoice lines added")
    
    # sales_opportunities
    if table_exists('sales_opportunities', db) and get_count('sales_opportunities', db) == 0:
        stages = ['Qualification', 'Needs Analysis', 'Value Proposition', 'Decision', 'Negotiation', 'Closed Won']
        for i in range(15):
            db.execute("""INSERT INTO sales_opportunities
                (opportunity_name, customer_id, stage, expected_value, probability,
                 sales_person_id, expected_close_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'Opportunity {i+1}', random.choice(cust_ids),
                 random.choice(stages), random.uniform(10000, 500000),
                 random.randint(10, 90), random.choice(emp_ids),
                 days_ago(random.randint(-60, 60)), now()))
        print("      + sales_opportunities: 15 opportunities added")
    
    # sales_activities
    if table_exists('sales_activities', db) and get_count('sales_activities', db) == 0:
        types = ['Call', 'Email', 'Meeting', 'Demo', 'Follow-up']
        for i in range(25):
            db.execute("""INSERT INTO sales_activities
                (customer_id, activity_type, subject, description, sales_person_id,
                 activity_date, duration_minutes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(cust_ids), random.choice(types),
                 f'Activity subject {i+1}', f'Activity description {i+1}',
                 random.choice(emp_ids), days_ago(random.randint(1, 30)),
                 random.randint(15, 120), now()))
        print("      + sales_activities: 25 activities added")
    
    # sales_targets
    if table_exists('sales_targets', db) and get_count('sales_targets', db) == 0:
        for emp_id in emp_ids[:5]:
            for qtr in range(1, 5):
                db.execute("""INSERT INTO sales_targets
                    (sales_person_id, target_amount, target_type, period_year, period_quarter,
                     achieved_amount, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (emp_id, random.uniform(100000, 500000), 'Quarterly',
                     2026, qtr, random.uniform(50000, 400000), now()))
        print("      + sales_targets: quarterly targets added")
    
    # sales_price_lists
    if table_exists('sales_price_lists', db) and get_count('sales_price_lists', db) == 0:
        names = ['Retail Price List', 'Wholesale Price List', 'VIP Customer List', 'Partner Pricing']
        for name in names:
            db.execute("""INSERT INTO sales_price_lists (name, valid_from, valid_to, status, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (name, days_ago(30), days_ago(-180), 'Active', now()))
        print("      + sales_price_lists: price lists added")
    
    # sales_price_list_items
    if table_exists('sales_price_list_items', db) and get_count('sales_price_list_items', db) == 0:
        pl_ids = get_any_id('sales_price_lists', db, 10)
        if pl_ids and part_ids:
            for pl_id in pl_ids:
                for part_id in part_ids[:20]:
                    db.execute("""INSERT INTO sales_price_list_items
                        (price_list_id, part_id, min_quantity, unit_price, created_at)
                        VALUES (?, ?, ?, ?, ?)""",
                        (pl_id, part_id, 1, random.uniform(50, 500), now()))
            print("      + sales_price_list_items: price list items added")
    
    # sales_contracts
    if table_exists('sales_contracts', db) and get_count('sales_contracts', db) == 0:
        for i in range(10):
            db.execute("""INSERT INTO sales_contracts
                (contract_number, customer_id, title, contract_value, start_date, end_date,
                 status, sales_person_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'CTR-2026-{i+1:04d}', random.choice(cust_ids),
                 f'Contract {i+1}', random.uniform(50000, 500000),
                 days_ago(random.randint(1, 180)), days_ago(random.randint(-180, 0)),
                 random.choice(['Draft', 'Active', 'Expired', 'Terminated']),
                 random.choice(emp_ids), now()))
        print("      + sales_contracts: contracts added")
    
    # sales_returns
    if table_exists('sales_returns', db) and get_count('sales_returns', db) == 0:
        reasons = ['Defective', 'Wrong Item', 'Changed Mind', 'Damaged']
        for i in range(8):
            db.execute("""INSERT INTO sales_returns
                (return_number, invoice_id, customer_id, return_date, reason,
                 status, total_refund, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'RET-2026-{i+1:04d}', random.randint(1, 15), random.choice(cust_ids),
                 days_ago(random.randint(1, 30)), random.choice(reasons),
                 random.choice(['Pending', 'Approved', 'Refunded']),
                 random.uniform(100, 5000), now()))
        print("      + sales_returns: returns added")
    
    # sales_confirmations
    if table_exists('sales_confirmations', db) and get_count('sales_confirmations', db) == 0:
        for i in range(10):
            db.execute("""INSERT INTO sales_confirmations
                (confirmation_number, order_id, customer_id, confirmation_date,
                 status, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f'CF-2026-{i+1:04d}', random.randint(1, 30), random.choice(cust_ids),
                 days_ago(random.randint(1, 30)), random.choice(['Pending', 'Confirmed']),
                 f'Confirmation notes {i+1}', now()))
        print("      + sales_confirmations: confirmations added")
    
    # sales_special_prices
    if table_exists('sales_special_prices', db) and get_count('sales_special_prices', db) == 0:
        for i in range(15):
            db.execute("""INSERT INTO sales_special_prices
                (customer_id, part_id, special_price, min_quantity, valid_from, valid_to, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(cust_ids), random.choice(part_ids) if part_ids else 1,
                 random.uniform(30, 300), random.randint(1, 10),
                 days_ago(30), days_ago(-90), now()))
        print("      + sales_special_prices: special prices added")
    
    # Customer purchase orders
    if table_exists('customer_purchase_orders', db) and get_count('customer_purchase_orders', db) == 0:
        for i in range(12):
            db.execute("""INSERT INTO customer_purchase_orders
                (customer_id, po_number, po_date, status, total_amount, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.choice(cust_ids), f'CPO-{random.randint(1000,9999)}',
                 days_ago(random.randint(1, 60)), random.choice(['Received', 'Processing', 'Filled']),
                 random.uniform(5000, 100000), now()))
        print("      + customer_purchase_orders: customer POs added")
    
    db.commit()


# =============================================================================
# PROCUREMENT MODULE
# =============================================================================

def seed_procurement_tables(db, cols):
    """Seed all empty procurement tables."""
    
    supplier_ids = get_any_id('suppliers', db, 20)
    emp_ids = get_any_id('hr_employees', db, 5)
    part_ids = get_any_id('parts', db, 20)
    
    if not supplier_ids:
        supplier_ids = [1]
    if not emp_ids:
        emp_ids = [1]
    if not part_ids:
        part_ids = [1]
    
    # procurement_requisitions
    if table_exists('procurement_requisitions', db) and get_count('procurement_requisitions', db) == 0:
        for i in range(15):
            db.execute("""INSERT INTO procurement_requisitions
                (requisition_number, requested_by, request_date, department, status,
                 total_estimated_cost, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'PR-2026-{i+1:04d}', random.choice(emp_ids),
                 days_ago(random.randint(1, 45)),
                 random.choice(['Sales', 'Operations', 'Warehouse', 'HR']),
                 random.choice(['Draft', 'Submitted', 'Approved', 'Rejected']),
                 random.uniform(5000, 100000),
                 f'Requisition for {random.choice(["filters", "brakes", "oil", "electrical parts"])}',
                 now()))
            print("      + procurement_requisitions: requisitions added")
    
    # procurement_requisition_lines
    if table_exists('procurement_requisition_lines', db) and get_count('procurement_requisition_lines', db) == 0:
        req_ids = get_any_id('procurement_requisitions', db, 20)
        for req_id in req_ids[:10]:
            for i in range(random.randint(1, 5)):
                db.execute("""INSERT INTO procurement_requisition_lines
                    (requisition_id, part_id, description, quantity, estimated_unit_price,
                     total_price, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (req_id, random.choice(part_ids), f'Item {i+1}',
                     random.randint(5, 50), random.uniform(20, 500),
                     random.uniform(100, 5000), now()))
        print("      + procurement_requisition_lines: lines added")
    
    # procurement_rfqs
    if table_exists('procurement_rfqs', db) and get_count('procurement_rfqs', db) == 0:
        for i in range(12):
            db.execute("""INSERT INTO procurement_rfqs
                (rfq_number, supplier_id, requested_by, rfq_date, valid_until, status,
                 total_estimated_value, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'RFQ-2026-{i+1:04d}', random.choice(supplier_ids),
                 random.choice(emp_ids), days_ago(random.randint(1, 30)),
                 days_ago(random.randint(-30, 30)),
                 random.choice(['Draft', 'Sent', 'Received', 'Evaluated']),
                 random.uniform(10000, 200000),
                 f'RFQ for parts procurement', now()))
            print("      + procurement_rfqs: RFQs added")
    
    # procurement_rfq_lines
    if table_exists('procurement_rfq_lines', db) and get_count('procurement_rfq_lines', db) == 0:
        rfq_ids = get_any_id('procurement_rfqs', db, 20)
        for rfq_id in rfq_ids[:10]:
            for i in range(random.randint(1, 5)):
                db.execute("""INSERT INTO procurement_rfq_lines
                    (rfq_id, part_id, description, quantity, target_price, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (rfq_id, random.choice(part_ids), f'Item {i+1}',
                     random.randint(10, 100), random.uniform(50, 500), now()))
        print("      + procurement_rfq_lines: RFQ lines added")
    
    # procurement_purchase_orders
    if table_exists('procurement_purchase_orders', db) and get_count('procurement_purchase_orders', db) == 0:
        for i in range(20):
            db.execute("""INSERT INTO procurement_purchase_orders
                (po_number, supplier_id, buyer_id, order_date, expected_delivery,
                 status, total_amount, tax_amount, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'PO-2026-{i+1:04d}', random.choice(supplier_ids),
                 random.choice(emp_ids), days_ago(random.randint(1, 60)),
                 days_ago(random.randint(-30, 30)),
                 random.choice(['Draft', 'Sent', 'Confirmed', 'Partial', 'Received']),
                 random.uniform(10000, 300000), random.uniform(500, 15000),
                 f'Purchase order for inventory replenishment', now()))
            print("      + procurement_purchase_orders: POs added")
    
    # procurement_po_lines
    if table_exists('procurement_po_lines', db) and get_count('procurement_po_lines', db) == 0:
        po_ids = get_any_id('procurement_purchase_orders', db, 30)
        for po_id in po_ids[:20]:
            for i in range(random.randint(1, 6)):
                qty = random.randint(10, 100)
                price = random.uniform(20, 300)
                db.execute("""INSERT INTO procurement_po_lines
                    (po_id, part_id, description, quantity, unit_price, total_price, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (po_id, random.choice(part_ids), f'PO Item {i+1}',
                     qty, price, qty * price, now()))
        print("      + procurement_po_lines: PO lines added")
    
    # procurement_quotations
    if table_exists('procurement_quotations', db) and get_count('procurement_quotations', db) == 0:
        for i in range(15):
            db.execute("""INSERT INTO procurement_quotations
                (quotation_number, supplier_id, rfq_id, quotation_date, valid_until,
                 status, total_amount, payment_terms, delivery_terms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'SQ-2026-{i+1:04d}', random.choice(supplier_ids),
                 random.randint(1, 10) if get_count('procurement_rfqs', db) > 0 else None,
                 days_ago(random.randint(1, 30)), days_ago(random.randint(-30, 30)),
                 random.choice(['Submitted', 'Under Review', 'Accepted', 'Rejected']),
                 random.uniform(15000, 250000), 'NET 30', 'FOB', now()))
            print("      + procurement_quotations: quotations added")
    
    # procurement_quotation_lines
    if table_exists('procurement_quotation_lines', db) and get_count('procurement_quotation_lines', db) == 0:
        quo_ids = get_any_id('procurement_quotations', db, 20)
        for quo_id in quo_ids[:12]:
            for i in range(random.randint(1, 5)):
                db.execute("""INSERT INTO procurement_quotation_lines
                    (quotation_id, part_id, description, quantity, unit_price, total_price, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (quo_id, random.choice(part_ids), f'Quoted Item {i+1}',
                     random.randint(20, 200), random.uniform(15, 250),
                     random.uniform(300, 5000), now()))
        print("      + procurement_quotation_lines: quotation lines added")
    
    # procurement_receiving
    if table_exists('procurement_receiving', db) and get_count('procurement_receiving', db) == 0:
        for i in range(15):
            db.execute("""INSERT INTO procurement_receiving
                (receipt_number, po_id, supplier_id, receipt_date, status,
                 receiver_id, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'REC-2026-{i+1:04d}', random.randint(1, 20),
                 random.choice(supplier_ids), days_ago(random.randint(1, 30)),
                 random.choice(['Pending', 'Partial', 'Complete']),
                 random.choice(emp_ids), f'Goods receipt {i+1}', now()))
            print("      + procurement_receiving: receipts added")
    
    # procurement_receiving_lines
    if table_exists('procurement_receiving_lines', db) and get_count('procurement_receiving_lines', db) == 0:
        rec_ids = get_any_id('procurement_receiving', db, 20)
        for rec_id in rec_ids[:12]:
            for i in range(random.randint(1, 4)):
                db.execute("""INSERT INTO procurement_receiving_lines
                    (receiving_id, part_id, ordered_quantity, received_quantity,
                     accepted_quantity, rejected_quantity, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (rec_id, random.choice(part_ids),
                     random.randint(50, 200), random.randint(40, 200),
                     random.randint(35, 190), random.randint(0, 10), now()))
        print("      + procurement_receiving_lines: receiving lines added")
    
    # procurement_contracts
    if table_exists('procurement_contracts', db) and get_count('procurement_contracts', db) == 0:
        for i in range(10):
            db.execute("""INSERT INTO procurement_contracts
                (contract_number, supplier_id, title, contract_value, start_date,
                 end_date, status, payment_terms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'PC-2026-{i+1:04d}', random.choice(supplier_ids),
                 f'Framework Agreement {i+1}', random.uniform(100000, 1000000),
                 days_ago(random.randint(30, 180)), days_ago(random.randint(-180, 0)),
                 random.choice(['Draft', 'Active', 'Expired', 'Terminated']),
                 'NET 60', now()))
            print("      + procurement_contracts: contracts added")
    
    # procurement_shipments
    if table_exists('procurement_shipments', db) and get_count('procurement_shipments', db) == 0:
        for i in range(12):
            db.execute("""INSERT INTO procurement_shipments
                (shipment_number, po_id, supplier_id, ship_date, estimated_arrival,
                 actual_arrival, status, carrier, tracking_number, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'SHP-2026-{i+1:04d}', random.randint(1, 20),
                 random.choice(supplier_ids), days_ago(random.randint(5, 40)),
                 days_ago(random.randint(-10, 20)), days_ago(random.randint(-5, 25)),
                 random.choice(['In Transit', 'Customs', 'Delivered', 'Delayed']),
                 random.choice(['DHL', 'FedEx', 'UPS', 'Aramex']),
                 f'TRK{random.randint(10000000, 99999999)}', now()))
            print("      + procurement_shipments: shipments added")
    
    # procurement_shipment_lines
    if table_exists('procurement_shipment_lines', db) and get_count('procurement_shipment_lines', db) == 0:
        shp_ids = get_any_id('procurement_shipments', db, 15)
        for shp_id in shp_ids[:10]:
            for i in range(random.randint(1, 5)):
                db.execute("""INSERT INTO procurement_shipment_lines
                    (shipment_id, part_id, quantity, created_at)
                    VALUES (?, ?, ?, ?)""",
                    (shp_id, random.choice(part_ids), random.randint(20, 100), now()))
        print("      + procurement_shipment_lines: shipment lines added")
    
    # procurement_supplier_contacts
    if table_exists('procurement_supplier_contacts', db) and get_count('procurement_supplier_contacts', db) == 0:
        titles = ['Procurement Manager', 'Sales Representative', 'Account Manager', 'General Manager']
        for sup_id in supplier_ids[:15]:
            for i, title in enumerate(titles[:2]):
                db.execute("""INSERT INTO procurement_supplier_contacts
                    (supplier_id, name, title, email, phone, is_primary, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (sup_id, f'Contact {i+1} for Supplier {sup_id}', title,
                     f'contact{i+1}@supplier{sup_id}.com',
                     f'+97150{random.randint(1000000, 9999999)}',
                     'Yes' if i == 0 else 'No', now()))
        print("      + procurement_supplier_contacts: contacts added")
    
    # procurement_supplier_brands
    if table_exists('procurement_supplier_brands', db) and get_count('procurement_supplier_brands', db) == 0:
        brands = ['Toyota', 'Bosch', 'Denso', 'Hyundai', 'Kia', 'Nissan', 'Mitsubishi']
        for sup_id in supplier_ids[:10]:
            for brand in random.sample(brands, random.randint(2, 4)):
                db.execute("""INSERT INTO procurement_supplier_brands
                    (supplier_id, brand_name, is_authorized, created_at)
                    VALUES (?, ?, ?, ?)""",
                    (sup_id, brand, random.choice(['Yes', 'No']), now()))
        print("      + procurement_supplier_brands: brands added")
    
    # procurement_supplier_metrics
    if table_exists('procurement_supplier_metrics', db) and get_count('procurement_supplier_metrics', db) == 0:
        for sup_id in supplier_ids[:15]:
            db.execute("""INSERT INTO procurement_supplier_metrics
                (supplier_id, on_time_delivery_rate, quality_score, price_competitiveness,
                 response_time_hours, overall_rating, evaluated_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (sup_id, random.uniform(85, 99), random.uniform(3.5, 5.0),
                 random.uniform(3.0, 5.0), random.uniform(2, 48),
                 random.uniform(3.5, 5.0), days_ago(random.randint(1, 30)), now()))
        print("      + procurement_supplier_metrics: metrics added")
    
    # procurement_claims
    if table_exists('procurement_claims', db) and get_count('procurement_claims', db) == 0:
        for i in range(8):
            db.execute("""INSERT INTO procurement_claims
                (claim_number, supplier_id, po_id, claim_type, description,
                 claim_amount, status, filed_date, resolution_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'CLM-2026-{i+1:04d}', random.choice(supplier_ids),
                 random.randint(1, 20), random.choice(['Quality', 'Shortage', 'Damage', 'Pricing']),
                 f'Claim description {i+1}', random.uniform(500, 10000),
                 random.choice(['Filed', 'Under Review', 'Approved', 'Rejected']),
                 days_ago(random.randint(10, 60)),
                 days_ago(random.randint(-15, 9)) if random.random() > 0.5 else None, now()))
        print("      + procurement_claims: claims added")
    
    # procurement_budgets
    if table_exists('procurement_budgets', db) and get_count('procurement_budgets', db) == 0:
        for i in range(4):
            db.execute("""INSERT INTO procurement_budgets
                (budget_number, department, budget_year, total_budget, spent_amount,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f'PB-2026-{i+1}', random.choice(['Warehouse', 'Operations', 'Sales', 'HR']),
                 2026, random.uniform(500000, 2000000),
                 random.uniform(100000, 1500000),
                 random.choice(['Draft', 'Approved', 'Exceeded']), now()))
            print("      + procurement_budgets: budgets added")
    
    # procurement_budget_lines
    if table_exists('procurement_budget_lines', db) and get_count('procurement_budget_lines', db) == 0:
        budget_ids = get_any_id('procurement_budgets', db, 10)
        for budget_id in budget_ids:
            for month in range(1, 13):
                db.execute("""INSERT INTO procurement_budget_lines
                    (budget_id, month, allocated_amount, spent_amount, created_at)
                    VALUES (?, ?, ?, ?, ?)""",
                    (budget_id, month, random.uniform(30000, 150000),
                     random.uniform(20000, 120000), now()))
        print("      + procurement_budget_lines: budget lines added")
    
    # procurement_vendor_selections
    if table_exists('procurement_vendor_selections', db) and get_count('procurement_vendor_selections', db) == 0:
        for i in range(10):
            db.execute("""INSERT INTO procurement_vendor_selections
                (rfq_id, supplier_id, technical_score, commercial_score, total_score,
                 rank, selected, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 12), random.choice(supplier_ids),
                 random.uniform(60, 100), random.uniform(60, 100),
                 random.uniform(60, 100), random.randint(1, 5),
                 'Yes' if random.random() > 0.3 else 'No',
                 f'Vendor selection notes {i+1}', now()))
        print("      + procurement_vendor_selections: vendor selections added")
    
    db.commit()


# =============================================================================
# FINANCE MODULE
# =============================================================================

def seed_finance_tables(db, cols):
    """Seed all empty finance tables."""
    
    cust_ids = get_any_id('sales_customers', db, 20)
    sup_ids = get_any_id('suppliers', db, 20)
    emp_ids = get_any_id('hr_employees', db, 10)
    acc_ids = get_any_id('finance_accounts', db, 30)
    
    if not cust_ids:
        cust_ids = [1]
    if not sup_ids:
        sup_ids = [1]
    if not emp_ids:
        emp_ids = [1]
    if not acc_ids:
        acc_ids = list(range(1, 31))
    
    # finance_customer_receipts
    if table_exists('finance_customer_receipts', db) and get_count('finance_customer_receipts', db) == 0:
        for i in range(15):
            db.execute("""INSERT INTO finance_customer_receipts
                (receipt_number, customer_id, receipt_date, amount, payment_method,
                 reference_number, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'RCP-2026-{i+1:04d}', random.choice(cust_ids),
                 days_ago(random.randint(1, 60)), random.uniform(1000, 30000),
                 random.choice(['Cash', 'Bank Transfer', 'Check', 'Credit Card']),
                 f'REF-{random.randint(100000, 999999)}',
                 f'Payment received {i+1}', now()))
        print("      + finance_customer_receipts: receipts added")
    
    # finance_customer_receipt_lines
    if table_exists('finance_customer_receipt_lines', db) and get_count('finance_customer_receipt_lines', db) == 0:
        inv_ids = get_any_id('finance_customer_invoices', db, 20)
        for inv_id in inv_ids[:10]:
            db.execute("""INSERT INTO finance_customer_receipt_lines
                (receipt_id, invoice_id, amount_applied, created_at)
                VALUES (?, ?, ?, ?)""",
                (random.randint(1, 15), inv_id, random.uniform(500, 15000), now()))
        print("      + finance_customer_receipt_lines: receipt lines added")
    
    # finance_supplier_payments
    if table_exists('finance_supplier_payments', db) and get_count('finance_supplier_payments', db) == 0:
        for i in range(15):
            db.execute("""INSERT INTO finance_supplier_payments
                (payment_number, supplier_id, payment_date, amount, payment_method,
                 reference_number, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'PAY-2026-{i+1:04d}', random.choice(sup_ids),
                 days_ago(random.randint(1, 60)), random.uniform(1000, 30000),
                 random.choice(['Cash', 'Bank Transfer', 'Check']),
                 f'PAY-REF-{random.randint(100000, 999999)}',
                 f'Payment for invoice {i+1}', now()))
        print("      + finance_supplier_payments: payments added")
    
    # finance_supplier_payment_lines
    if table_exists('finance_supplier_payment_lines', db) and get_count('finance_supplier_payment_lines', db) == 0:
        bill_ids = get_any_id('finance_supplier_bills', db, 20)
        for bill_id in bill_ids[:10]:
            db.execute("""INSERT INTO finance_supplier_payment_lines
                (payment_id, bill_id, amount_applied, created_at)
                VALUES (?, ?, ?, ?)""",
                (random.randint(1, 15), bill_id, random.uniform(500, 15000), now()))
        print("      + finance_supplier_payment_lines: payment lines added")
    
    # finance_customer_credit_notes
    if table_exists('finance_customer_credit_notes', db) and get_count('finance_customer_credit_notes', db) == 0:
        for i in range(8):
            db.execute("""INSERT INTO finance_customer_credit_notes
                (credit_note_number, customer_id, credit_note_date, amount, reason,
                 status, applied_amount, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'CN-2026-{i+1:04d}', random.choice(cust_ids),
                 days_ago(random.randint(1, 45)), random.uniform(500, 5000),
                 random.choice(['Return', 'Discount', 'Adjustment', 'Overcharge']),
                 random.choice(['Draft', 'Issued', 'Applied']),
                 random.uniform(0, 3000), now()))
        print("      + finance_customer_credit_notes: credit notes added")
    
    # finance_supplier_debit_notes
    if table_exists('finance_supplier_debit_notes', db) and get_count('finance_supplier_debit_notes', db) == 0:
        for i in range(8):
            db.execute("""INSERT INTO finance_supplier_debit_notes
                (debit_note_number, supplier_id, debit_note_date, amount, reason,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f'DN-2026-{i+1:04d}', random.choice(sup_ids),
                 days_ago(random.randint(1, 45)), random.uniform(500, 5000),
                 random.choice(['Price Adjustment', 'Shortage', 'Damaged Goods', 'Other']),
                 random.choice(['Draft', 'Issued', 'Resolved']), now()))
        print("      + finance_supplier_debit_notes: debit notes added")
    
    # finance_depreciation_runs
    if table_exists('finance_depreciation_runs', db) and get_count('finance_depreciation_runs', db) == 0:
        for i in range(6):
            db.execute("""INSERT INTO finance_depreciation_runs
                (run_date, description, total_depreciation, status, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (days_ago(random.randint(1, 180)), f'Depreciation run {i+1}',
                 random.uniform(10000, 100000), 'Completed',
                 random.choice(emp_ids), now()))
        print("      + finance_depreciation_runs: depreciation runs added")
    
    # finance_tax_rules
    if table_exists('finance_tax_rules', db) and get_count('finance_tax_rules', db) == 0:
        rules = [
            ('VAT Standard', 'Standard VAT rate', 'VAT', '5', 'Sales,Services', 'Output'),
            ('VAT Zero', 'Zero rated VAT', 'VAT', '0', 'Exports,Essential', 'Output'),
            ('VAT Exempt', 'Exempt from VAT', 'VAT', '0', 'Financial,Real Estate', 'Output'),
            ('Input VAT', 'Input VAT on purchases', 'VAT', '5', 'Purchases', 'Input'),
            ('Customs Duty', 'Customs import duty', 'Customs', '5', 'Imports', 'Customs'),
        ]
        for name, desc, tax_type, rate, applies_to, direction in rules:
            db.execute("""INSERT INTO finance_tax_rules
                (name, description, tax_type, rate, applies_to, direction, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, desc, tax_type, rate, applies_to, direction, 'Active', now()))
        print("      + finance_tax_rules: tax rules added")
    
    db.commit()


# =============================================================================
# LOGISTICS MODULE
# =============================================================================

def seed_logistics_tables(db, cols):
    """Seed all empty logistics tables."""
    
    driver_ids = get_any_id('logistics_drivers', db, 20)
    vehicle_ids = get_any_id('logistics_vehicles', db, 15)
    
    if not driver_ids:
        driver_ids = [1]
    if not vehicle_ids:
        vehicle_ids = [1]
    
    # logistics_carriers
    if table_exists('logistics_carriers', db) and get_count('logistics_carriers', db) == 0:
        carriers = [
            ('DHL Express', 'dhl.com', '+971420000000', 'International'),
            ('FedEx', 'fedex.com', '+971420000001', 'International'),
            ('Aramex', 'aramex.com', '+971420000002', 'Regional'),
            ('SMSA Express', 'smsaexpress.com', '+971420000003', 'Local'),
            ('Amazon Logistics', 'amazon.com', '+971420000004', 'E-commerce'),
        ]
        for name, website, phone, service_type in carriers:
            db.execute("""INSERT INTO logistics_carriers
                (name, contact_email, contact_phone, service_type, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (name, f'info@{website}', phone, service_type, 'Yes', now()))
        print("      + logistics_carriers: carriers added")
    
    # logistics_route_masters
    if table_exists('logistics_route_masters', db) and get_count('logistics_route_masters', db) == 0:
        routes = [
            ('Dubai - Abu Dhabi', 'DXB-AUH', 150, 120),
            ('Dubai - Sharjah', 'DXB-SHJ', 30, 25),
            ('Dubai - Al Ain', 'DXB-AIN', 180, 150),
            ('Abu Dhabi - Al Dhafra', 'AUH-DHF', 200, 180),
            ('Dubai - Northern Emirates', 'DXB-NORTH', 90, 75),
        ]
        for name, code, est_time, est_dist in routes:
            db.execute("""INSERT INTO logistics_route_masters
                (route_name, route_code, estimated_time_minutes, estimated_distance_km,
                 is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (name, code, est_time, est_dist, 'Yes', now()))
        print("      + logistics_route_masters: routes added")
    
    # logistics_route_stops
    if table_exists('logistics_route_stops', db) and get_count('logistics_route_stops', db) == 0:
        route_ids = get_any_id('logistics_route_masters', db, 10)
        for route_id in route_ids[:3]:
            for i in range(random.randint(3, 8)):
                db.execute("""INSERT INTO logistics_route_stops
                    (route_id, stop_sequence, location_name, address, estimated_arrival,
                     actual_arrival, stop_type, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (route_id, i+1, f'Stop {i+1}', f'Address {i+1}, UAE',
                     f'0{i+1}:{random.randint(0,5)}{random.randint(0,9)}',
                     None, random.choice(['Pickup', 'Delivery', 'Both']), now()))
        print("      + logistics_route_stops: route stops added")
    
    # logistics_delivery_orders
    if table_exists('logistics_delivery_orders', db) and get_count('logistics_delivery_orders', db) == 0:
        for i in range(20):
            db.execute("""INSERT INTO logistics_delivery_orders
                (order_number, customer_id, delivery_date, time_slot, status,
                 driver_id, vehicle_id, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'DO-2026-{i+1:04d}', random.randint(1, 50),
                 days_ago(random.randint(-7, 14)), f'{9+i}:00-{10+i}:00',
                 random.choice(['Pending', 'Assigned', 'In Transit', 'Delivered']),
                 random.choice(driver_ids), random.choice(vehicle_ids),
                 f'Delivery order {i+1}', now()))
        print("      + logistics_delivery_orders: delivery orders added")
    
    # logistics_pickup_orders
    if table_exists('logistics_pickup_orders', db) and get_count('logistics_pickup_orders', db) == 0:
        for i in range(12):
            db.execute("""INSERT INTO logistics_pickup_orders
                (order_number, supplier_id, pickup_date, time_slot, status,
                 driver_id, vehicle_id, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'PPO-2026-{i+1:04d}', random.randint(1, 30),
                 days_ago(random.randint(-7, 14)), f'{8+i}:00-{9+i}:00',
                 random.choice(['Pending', 'Assigned', 'Completed']),
                 random.choice(driver_ids), random.choice(vehicle_ids),
                 f'Pickup order {i+1}', now()))
        print("      + logistics_pickup_orders: pickup orders added")
    
    # logistics_cost_entries
    if table_exists('logistics_cost_entries', db) and get_count('logistics_cost_entries', db) == 0:
        cost_types = ['Fuel', 'Toll', 'Parking', 'Maintenance', 'Driver Allowance']
        for i in range(30):
            db.execute("""INSERT INTO logistics_cost_entries
                (trip_id, cost_type, amount, description, receipt_number, 
                 expense_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 10), random.choice(cost_types),
                 random.uniform(20, 500), f'Cost entry {i+1}',
                 f'RCP-{random.randint(1000,9999)}', days_ago(random.randint(1, 30)), now()))
        print("      + logistics_cost_entries: cost entries added")
    
    # logistics_expense_entries
    if table_exists('logistics_expense_entries', db) and get_count('logistics_expense_entries', db) == 0:
        for i in range(25):
            db.execute("""INSERT INTO logistics_expense_entries
                (trip_id, expense_category, amount, description, expense_date, 
                 submitted_by, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 10), random.choice(['Travel', 'Accommodation', 'Meal', 'Communication']),
                 random.uniform(50, 800), f'Expense {i+1}',
                 days_ago(random.randint(1, 30)), 1,
                 random.choice(['Submitted', 'Approved', 'Rejected']), now()))
        print("      + logistics_expense_entries: expense entries added")
    
    # logistics_trip_expenses
    if table_exists('logistics_trip_expenses', db) and get_count('logistics_trip_expenses', db) == 0:
        for i in range(20):
            db.execute("""INSERT INTO logistics_trip_expenses
                (trip_id, expense_type, amount, description, expense_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 10), random.choice(['Fuel', 'Toll', 'Parking', 'Other']),
                 random.uniform(30, 400), f'Trip expense {i+1}',
                 days_ago(random.randint(1, 30)), now()))
        print("      + logistics_trip_expenses: trip expenses added")
    
    # logistics_incidents
    if table_exists('logistics_incidents', db) and get_count('logistics_incidents', db) == 0:
        for i in range(10):
            db.execute("""INSERT INTO logistics_incidents
                (incident_number, trip_id, incident_type, description, severity,
                 reported_date, status, resolution, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'INC-2026-{i+1:04d}', random.randint(1, 10),
                 random.choice(['Accident', 'Breakdown', 'Delay', 'Damage', 'Theft']),
                 f'Incident description {i+1}',
                 random.choice(['Low', 'Medium', 'High', 'Critical']),
                 days_ago(random.randint(1, 30)),
                 random.choice(['Reported', 'Under Investigation', 'Resolved']),
                 f'Resolution for incident {i+1}' if random.random() > 0.5 else None, now()))
        print("      + logistics_incidents: incidents added")
    
    # logistics_alerts
    if table_exists('logistics_alerts', db) and get_count('logistics_alerts', db) == 0:
        for i in range(15):
            db.execute("""INSERT INTO logistics_alerts
                (alert_type, title, message, priority, related_id, is_read, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(['Delay', 'Delivery', 'Vehicle', 'Driver', 'Geofence']),
                 f'Alert {i+1}', f'Alert message {i+1}',
                 random.choice(['Info', 'Warning', 'Critical']),
                 random.randint(1, 20), 'No' if random.random() > 0.5 else 'Yes', now()))
        print("      + logistics_alerts: alerts added")
    
    # logistics_notifications
    if table_exists('logistics_notifications', db) and get_count('logistics_notifications', db) == 0:
        for i in range(20):
            db.execute("""INSERT INTO logistics_notifications
                (title, message, notification_type, recipient_id, is_read, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f'Notification {i+1}', f'Notification message {i+1}',
                 random.choice(['Update', 'Reminder', 'Alert', 'Confirmation']),
                 1, 'No' if random.random() > 0.5 else 'Yes', now()))
        print("      + logistics_notifications: notifications added")
    
    db.commit()


# =============================================================================
# MARKETING MODULE
# =============================================================================

def seed_marketing_tables(db, cols):
    """Seed all empty marketing tables."""
    
    # marketing_brands
    if table_exists('marketing_brands', db) and get_count('marketing_brands', db) == 0:
        brands = [
            ('Toyota', 'Automotive', 'Japan'),
            ('Samsung', 'Electronics', 'South Korea'),
            ('Apple', 'Technology', 'USA'),
            ('Nike', 'Sportswear', 'USA'),
            ('Adidas', 'Sportswear', 'Germany'),
            ('Sony', 'Electronics', 'Japan'),
            ('LG', 'Electronics', 'South Korea'),
            ('Bosch', 'Automotive', 'Germany'),
        ]
        for name, industry, country in brands:
            db.execute("""INSERT INTO marketing_brands
                (brand_name, industry, country_of_origin, status, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (name, industry, country, 'Active', now()))
        print("      + marketing_brands: brands added")
    
    # marketing_channels
    if table_exists('marketing_channels', db) and get_count('marketing_channels', db) == 0:
        channels = [
            ('Website', 'Owned', 'High'),
            ('Instagram', 'Social', 'High'),
            ('LinkedIn', 'Social', 'Medium'),
            ('Email', 'Direct', 'Medium'),
            ('Google Ads', 'Paid', 'High'),
            ('Facebook', 'Social', 'Medium'),
            ('Trade Shows', 'Events', 'Medium'),
            ('Partner Referral', 'Referral', 'Low'),
        ]
        for name, channel_type, effectiveness in channels:
            db.execute("""INSERT INTO marketing_channels
                (channel_name, channel_type, effectiveness, status, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (name, channel_type, effectiveness, 'Active', now()))
        print("      + marketing_channels: channels added")
    
    # marketing_funnel_stages
    if table_exists('marketing_funnel_stages', db) and get_count('marketing_funnel_stages', db) == 0:
        stages = [
            ('Awareness', 'Top of Funnel', 1),
            ('Interest', 'Top of Funnel', 2),
            ('Consideration', 'Middle of Funnel', 3),
            ('Intent', 'Middle of Funnel', 4),
            ('Evaluation', 'Bottom of Funnel', 5),
            ('Purchase', 'Bottom of Funnel', 6),
        ]
        for name, stage_type, sequence in stages:
            db.execute("""INSERT INTO marketing_funnel_stages
                (stage_name, stage_type, sequence_order, created_at)
                VALUES (?, ?, ?, ?)""",
                (name, stage_type, sequence, now()))
        print("      + marketing_funnel_stages: funnel stages added")
    
    # marketing_customer_segments
    if table_exists('marketing_customer_segments', db) and get_count('marketing_customer_segments', db) == 0:
        segments = [
            ('Enterprise Customers', 'High-value enterprise clients', 100, 50),
            ('SMB Businesses', 'Small and medium businesses', 500, 30),
            ('Individual Consumers', 'B2C segment', 2000, 20),
            ('Government Clients', 'Government entities', 50, 80),
            ('Partner Network', 'Channel partners', 100, 40),
        ]
        for name, desc, count, avg_value in segments:
            db.execute("""INSERT INTO marketing_customer_segments
                (segment_name, description, customer_count, avg_customer_value,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (name, desc, count, avg_value, 'Active', now()))
        print("      + marketing_customer_segments: segments added")
    
    # marketing_budgets
    if table_exists('marketing_budgets', db) and get_count('marketing_budgets', db) == 0:
        for i in range(4):
            db.execute("""INSERT INTO marketing_budgets
                (budget_name, campaign_type, budget_amount, spent_amount,
                 period_start, period_end, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'Budget Q{i+1} 2026', 'Quarterly',
                 random.uniform(50000, 200000), random.uniform(20000, 150000),
                 f'2026-0{i*3+1}-01', f'2026-0{i*3+3}-31',
                 random.choice(['Draft', 'Active', 'Exceeded']), now()))
        print("      + marketing_budgets: budgets added")
    
    # marketing_costs
    if table_exists('marketing_costs', db) and get_count('marketing_costs', db) == 0:
        cost_types = ['Ad Spend', 'Content Creation', 'Agency Fee', 'Event Cost', 'Software']
        for i in range(20):
            db.execute("""INSERT INTO marketing_costs
                (campaign_id, cost_type, amount, description, cost_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 20), random.choice(cost_types),
                 random.uniform(500, 10000), f'Cost entry {i+1}',
                 days_ago(random.randint(1, 60)), now()))
        print("      + marketing_costs: costs added")
    
    # marketing_content
    if table_exists('marketing_content', db) and get_count('marketing_content', db) == 0:
        content_types = ['Blog Post', 'Social Post', 'Email', 'Video', 'Infographic']
        for i in range(25):
            db.execute("""INSERT INTO marketing_content
                (content_title, content_type, channel, status, published_date,
                 engagement_score, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f'Marketing Content {i+1}', random.choice(content_types),
                 random.choice(['Website', 'Instagram', 'LinkedIn', 'Email']),
                 random.choice(['Draft', 'Published', 'Archived']),
                 days_ago(random.randint(1, 45)),
                 random.randint(50, 5000), now()))
        print("      + marketing_content: content added")
    
    # marketing_lead_sources
    if table_exists('marketing_lead_sources', db) and get_count('marketing_lead_sources', db) == 0:
        sources = ['Website Form', 'Phone Inquiry', 'Trade Show', 'Referral', 'Social Media', 'Partner']
        for source in sources:
            db.execute("""INSERT INTO marketing_lead_sources
                (source_name, source_type, is_active, created_at)
                VALUES (?, ?, ?, ?)""",
                (source, random.choice(['Inbound', 'Outbound']), 'Yes', now()))
        print("      + marketing_lead_sources: lead sources added")
    
    # marketing_performance_metrics
    if table_exists('marketing_performance_metrics', db) and get_count('marketing_performance_metrics', db) == 0:
        for i in range(30):
            db.execute("""INSERT INTO marketing_performance_metrics
                (campaign_id, metric_date, impressions, clicks, conversions,
                 spend, revenue, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 20), days_ago(random.randint(1, 60)),
                 random.randint(1000, 50000), random.randint(50, 2000),
                 random.randint(5, 200), random.uniform(100, 5000),
                 random.uniform(500, 25000), now()))
        print("      + marketing_performance_metrics: metrics added")
    
    db.commit()


# =============================================================================
# WORKFLOW MODULE
# =============================================================================

def seed_workflow_tables(db, cols):
    """Seed all empty workflow tables."""
    
    # workflow_instances
    if table_exists('workflow_instances', db) and get_count('workflow_instances', db) == 0:
        def_ids = get_any_id('workflow_definitions', db, 10)
        emp_ids = get_any_id('hr_employees', db, 10)
        
        if def_ids:
            for i in range(15):
                db.execute("""INSERT INTO workflow_instances
                    (definition_id, instance_title, status, started_by, current_step_id,
                     started_at, completed_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (random.choice(def_ids), f'Workflow Instance {i+1}',
                     random.choice(['Running', 'Completed', 'Cancelled', 'Suspended']),
                     random.choice(emp_ids) if emp_ids else 1,
                     random.randint(1, 10),
                     days_ago(random.randint(1, 30)),
                     days_ago(random.randint(-10, 0)) if random.random() > 0.5 else None, now()))
            print("      + workflow_instances: instances added")
    
    # workflow_instance_steps
    if table_exists('workflow_instance_steps', db) and get_count('workflow_instance_steps', db) == 0:
        inst_ids = get_any_id('workflow_instances', db, 20)
        for inst_id in inst_ids[:12]:
            for i in range(random.randint(2, 5)):
                db.execute("""INSERT INTO workflow_instance_steps
                    (instance_id, step_id, step_name, status, assigned_to,
                     started_at, completed_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (inst_id, i+1, f'Step {i+1}',
                     random.choice(['Pending', 'In Progress', 'Completed', 'Skipped']),
                     random.randint(1, 10),
                     days_ago(random.randint(1, 20)),
                     days_ago(random.randint(-5, 0)) if random.random() > 0.3 else None, now()))
        print("      + workflow_instance_steps: instance steps added")
    
    # workflow_steps
    if table_exists('workflow_steps', db) and get_count('workflow_steps', db) == 0:
        step_types = ['Approval', 'Review', 'Task', 'Notification', 'Document']
        def_ids = get_any_id('workflow_definitions', db, 10)
        for def_id in def_ids[:4]:
            for i in range(1, 6):
                db.execute("""INSERT INTO workflow_steps
                    (definition_id, step_order, step_name, step_type, assigned_role,
                     is_required, timeout_hours, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (def_id, i, f'Step {i}', random.choice(step_types),
                     random.choice(['Manager', 'Admin', 'User', 'Finance']),
                     'Yes' if random.random() > 0.2 else 'No',
                     random.randint(24, 168), now()))
        print("      + workflow_steps: steps added")
    
    # workflow_transitions
    if table_exists('workflow_transitions', db) and get_count('workflow_transitions', db) == 0:
        for i in range(15):
            db.execute("""INSERT INTO workflow_transitions
                (definition_id, from_step_id, to_step_id, transition_name,
                 condition_expression, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 4), random.randint(1, 5),
                 random.randint(1, 5), f'Transition {i+1}',
                 f'condition == true', now()))
        print("      + workflow_transitions: transitions added")
    
    # workflow_conditions
    if table_exists('workflow_conditions', db) and get_count('workflow_conditions', db) == 0:
        for i in range(12):
            db.execute("""INSERT INTO workflow_conditions
                (step_id, condition_type, field_name, operator, value,
                 created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 15), 'Field',
                 random.choice(['amount', 'status', 'priority', 'department']),
                 random.choice(['equals', 'greater_than', 'less_than', 'contains']),
                 f'value_{i+1}', now()))
        print("      + workflow_conditions: conditions added")
    
    # workflow_actions
    if table_exists('workflow_actions', db) and get_count('workflow_actions', db) == 0:
        action_types = ['Send Email', 'Update Record', 'Create Task', 'Notify User', 'Generate Document']
        for i in range(15):
            db.execute("""INSERT INTO workflow_actions
                (step_id, action_type, action_config, created_at)
                VALUES (?, ?, ?, ?)""",
                (random.randint(1, 15), random.choice(action_types),
                 f'{{"config": "value{i+1}"}}', now()))
        print("      + workflow_actions: actions added")
    
    # workflow_assignments
    if table_exists('workflow_assignments', db) and get_count('workflow_assignments', db) == 0:
        for i in range(20):
            db.execute("""INSERT INTO workflow_assignments
                (instance_id, step_id, assigned_to, assigned_by, assigned_at,
                 completed_at, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 15), random.randint(1, 10),
                 random.randint(1, 15), random.randint(1, 5),
                 days_ago(random.randint(1, 20)),
                 days_ago(random.randint(-5, 0)) if random.random() > 0.4 else None,
                 random.choice(['Pending', 'Completed', 'Rejected']), now()))
        print("      + workflow_assignments: assignments added")
    
    # workflow_comments
    if table_exists('workflow_comments', db) and get_count('workflow_comments', db) == 0:
        for i in range(25):
            db.execute("""INSERT INTO workflow_comments
                (instance_id, step_id, user_id, comment_text, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (random.randint(1, 15), random.randint(1, 10),
                 random.randint(1, 10), f'Comment {i+1}', now()))
        print("      + workflow_comments: comments added")
    
    # sla_rules
    if table_exists('sla_rules', db) and get_count('sla_rules', db) == 0:
        rule_types = ['Response', 'Resolution', 'Escalation']
        for i, rtype in enumerate(rule_types):
            db.execute("""INSERT INTO sla_rules
                (rule_name, rule_type, priority_level, target_hours, 
                 warning_threshold, escalation_action, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'{rtype} SLA Rule {i+1}', rtype,
                 random.choice(['Low', 'Medium', 'High', 'Critical']),
                 random.randint(4, 72), random.randint(2, 48),
                 'Notify Manager', 'Yes', now()))
        print("      + sla_rules: SLA rules added")
    
    # escalation_rules
    if table_exists('escalation_rules', db) and get_count('escalation_rules', db) == 0:
        for i in range(10):
            db.execute("""INSERT INTO escalation_rules
                (rule_name, trigger_type, trigger_value, escalation_level,
                 escalate_to, action, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'Escalation Rule {i+1}', random.choice(['Overdue', 'Priority', 'Budget']),
                 random.randint(1, 5), random.randint(1, 3),
                 random.randint(5, 15), 'Email + SMS', 'Yes', now()))
        print("      + escalation_rules: escalation rules added")
    
    # notification_templates
    if table_exists('notification_templates', db) and get_count('notification_templates', db) == 0:
        templates = [
            ('Approval Request', 'Your approval is required for {{item}}', 'Email'),
            ('Task Assigned', 'You have been assigned a new task: {{task}}', 'Both'),
            ('Status Update', 'The status of {{item}} has been updated to {{status}}', 'In-App'),
            ('Reminder', 'Reminder: {{task}} is due on {{due_date}}', 'Email'),
            ('Escalation', '{{item}} has been escalated to you', 'Both'),
        ]
        for name, content, channel in templates:
            db.execute("""INSERT INTO notification_templates
                (template_name, subject, content, channel, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (name, name, content, channel, 'Yes', now()))
        print("      + notification_templates: templates added")
    
    # automation_rules
    if table_exists('automation_rules', db) and get_count('automation_rules', db) == 0:
        for i in range(10):
            db.execute("""INSERT INTO automation_rules
                (rule_name, trigger_event, conditions, actions, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f'Automation Rule {i+1}',
                 random.choice(['On Create', 'On Update', 'On Status Change']),
                 f'[{{"field": "status", "op": "eq", "value": "Active"}}]',
                 f'[{{"action": "notify", "to": "manager"}}]',
                 'Yes' if random.random() > 0.3 else 'No', now()))
        print("      + automation_rules: automation rules added")
    
    db.commit()


# =============================================================================
# SOCIAL MEDIA MODULE
# =============================================================================

def seed_social_media_tables(db, cols):
    """Seed all empty social media tables."""
    
    acc_ids = get_any_id('social_accounts', db, 20)
    if not acc_ids:
        acc_ids = [1]
    
    # social_campaigns
    if table_exists('social_campaigns', db) and get_count('social_campaigns', db) == 0:
        platforms = ['Instagram', 'LinkedIn', 'Twitter', 'Facebook']
        for i in range(15):
            db.execute("""INSERT INTO social_campaigns
                (campaign_name, platform, campaign_type, start_date, end_date,
                 budget, spent, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'Social Campaign {i+1}', random.choice(platforms),
                 random.choice(['Awareness', 'Engagement', 'Conversion']),
                 days_ago(random.randint(1, 45)), days_ago(random.randint(-30, 0)),
                 random.uniform(5000, 50000), random.uniform(2000, 40000),
                 random.choice(['Draft', 'Active', 'Paused', 'Completed']), now()))
        print("      + social_campaigns: campaigns added")
    
    # social_content_templates
    if table_exists('social_content_templates', db) and get_count('social_content_templates', db) == 0:
        for i in range(10):
            db.execute("""INSERT INTO social_content_templates
                (template_name, platform, content_format, template_content,
                 created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (f'Content Template {i+1}', random.choice(['Instagram', 'LinkedIn']),
                 random.choice(['Image', 'Video', 'Carousel', 'Story']),
                 f'Template content for post {i+1}', now()))
        print("      + social_content_templates: templates added")
    
    # social_caption_bank
    if table_exists('social_caption_bank', db) and get_count('social_caption_bank', db) == 0:
        captions = [
            'Excited to announce our latest innovation!',
            'Join us in celebrating this milestone.',
            'Discover the future of technology with us.',
            'Quality is our top priority. Learn more.',
            'Customer satisfaction at its best!',
        ]
        for caption in captions:
            db.execute("""INSERT INTO social_caption_bank
                (caption_text, category, is_verified, usage_count, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (caption, random.choice(['Product', 'Service', 'Brand', 'Promo']),
                 'Yes' if random.random() > 0.5 else 'No', random.randint(0, 50), now()))
        print("      + social_caption_bank: captions added")
    
    # social_hashtag_bank
    if table_exists('social_hashtag_bank', db) and get_count('social_hashtag_bank', db) == 0:
        hashtags = ['#innovation', '#technology', '#quality', '#uae', '#dubai',
                   '#business', '#growth', '#success', '#automation', '#digital']
        for tag in hashtags:
            db.execute("""INSERT INTO social_hashtag_bank
                (hashtag, category, usage_count, is_trending, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (tag, random.choice(['Industry', 'Brand', 'General', 'Trend']),
                 random.randint(10, 500), 'Yes' if random.random() > 0.7 else 'No', now()))
        print("      + social_hashtag_bank: hashtags added")
    
    # social_cta_bank
    if table_exists('social_cta_bank', db) and get_count('social_cta_bank', db) == 0:
        ctas = ['Shop Now', 'Learn More', 'Contact Us', 'Sign Up', 'Get Quote', 'Call Now']
        for cta in ctas:
            db.execute("""INSERT INTO social_cta_bank
                (cta_text, cta_type, url, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (cta, random.choice(['Shop', 'Info', 'Contact', 'Signup']),
                 f'https://example.com/{cta.lower().replace(" ", "-")}',
                 'Yes', now()))
        print("      + social_cta_bank: CTAs added")
    
    # social_audiences
    if table_exists('social_audiences', db) and get_count('social_audiences', db) == 0:
        audiences = [
            ('Tech Enthusiasts', 'People interested in technology', 50000, 25, 45),
            ('Business Professionals', 'B2B decision makers', 30000, 30, 50),
            ('Automotive Fans', 'Car enthusiasts and owners', 75000, 22, 40),
            ('Enterprise Buyers', 'Large enterprise IT buyers', 15000, 35, 55),
        ]
        for name, desc, size, age_from, age_to in audiences:
            db.execute("""INSERT INTO social_audiences
                (audience_name, description, estimated_size, age_range_from,
                 age_range_to, interests, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (name, desc, size, age_from, age_to,
                 random.choice(['Technology', 'Business', 'Automotive', 'Finance']), now()))
        print("      + social_audiences: audiences added")
    
    # social_lead_followups
    if table_exists('social_lead_followups', db) and get_count('social_lead_followups', db) == 0:
        lead_ids = get_any_id('social_leads', db, 30)
        for lead_id in lead_ids[:20]:
            for i in range(random.randint(1, 3)):
                db.execute("""INSERT INTO social_lead_followups
                    (lead_id, followup_type, notes, followup_date, outcome,
                     created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (lead_id, random.choice(['Call', 'Email', 'Meeting', 'Message']),
                     f'Followup notes {i+1}', days_ago(random.randint(1, 15)),
                     random.choice(['Interested', 'Not Interested', 'No Response', 'Qualified']), now()))
        print("      + social_lead_followups: followups added")
    
    # social_publish_queue
    if table_exists('social_publish_queue', db) and get_count('social_publish_queue', db) == 0:
        for i in range(20):
            db.execute("""INSERT INTO social_publish_queue
                (account_id, content_text, scheduled_time, status,
                 platform_post_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.choice(acc_ids), f'Content to publish {i+1}',
                 f'2026-04-{random.randint(10, 30):02d} {random.randint(9, 17):02d}:00:00',
                 random.choice(['Scheduled', 'Published', 'Failed']),
                 f'POST-{random.randint(100000, 999999)}' if random.random() > 0.5 else None, now()))
        print("      + social_publish_queue: queued posts added")
    
    # social_publish_history
    if table_exists('social_publish_history', db) and get_count('social_publish_history', db) == 0:
        for i in range(30):
            db.execute("""INSERT INTO social_publish_history
                (account_id, content_text, published_time, platform_post_id,
                 likes_count, comments_count, shares_count, reach, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(acc_ids), f'Published content {i+1}',
                 days_ago(random.randint(1, 45)),
                 f'POST-{random.randint(100000, 999999)}',
                 random.randint(10, 500), random.randint(0, 50),
                 random.randint(0, 20), random.randint(100, 5000), now()))
        print("      + social_publish_history: history added")
    
    # social_content_archive
    if table_exists('social_content_archive', db) and get_count('social_content_archive', db) == 0:
        for i in range(25):
            db.execute("""INSERT INTO social_content_archive
                (account_id, content_text, archived_date, archive_reason,
                 engagement_metrics, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.choice(acc_ids), f'Archived content {i+1}',
                 days_ago(random.randint(30, 90)),
                 random.choice(['Campaign End', 'Manual', 'Auto-Archive']),
                 f'{{"likes": {random.randint(50, 300)}}}' if random.random() > 0.3 else None, now()))
        print("      + social_content_archive: archive added")
    
    # social_automations
    if table_exists('social_automations', db) and get_count('social_automations', db) == 0:
        for i in range(10):
            db.execute("""INSERT INTO social_automations
                (automation_name, automation_type, trigger_condition, actions,
                 is_active, last_run, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f'Automation {i+1}', random.choice(['Auto Reply', 'Scheduled Post', 'Lead Capture']),
                 f'trigger == "{random.choice(["new_follower", "mention", "dm"])}"',
                 f'[{{"action": "reply", "message": "Thank you!"}}]',
                 'Yes' if random.random() > 0.3 else 'No',
                 days_ago(random.randint(1, 15)), now()))
        print("      + social_automations: automations added")
    
    # social_ads
    if table_exists('social_ads', db) and get_count('social_ads', db) == 0:
        for i in range(12):
            db.execute("""INSERT INTO social_ads
                (campaign_id, ad_name, ad_format, target_audience_id,
                 daily_budget, total_spent, impressions, clicks,
                 conversions, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 15), f'Ad {i+1}',
                 random.choice(['Single Image', 'Carousel', 'Video']),
                 random.randint(1, 10),
                 random.uniform(50, 500), random.uniform(500, 5000),
                 random.randint(1000, 50000), random.randint(50, 1000),
                 random.randint(5, 100),
                 random.choice(['Active', 'Paused', 'Completed']), now()))
        print("      + social_ads: ads added")
    
    # social_alerts
    if table_exists('social_alerts', db) and get_count('social_alerts', db) == 0:
        for i in range(15):
            db.execute("""INSERT INTO social_alerts
                (alert_type, title, message, platform, is_read, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.choice(['Mention', 'Comment', 'DM', 'Follower', 'Engagement']),
                 f'Alert: {random.choice(["New mention", "Comment received", "New follower"])}',
                 f'Alert message {i+1}',
                 random.choice(['Instagram', 'LinkedIn', 'Twitter']),
                 'No' if random.random() > 0.5 else 'Yes', now()))
        print("      + social_alerts: alerts added")
    
    # social_monitoring
    if table_exists('social_monitoring', db) and get_count('social_monitoring', db) == 0:
        keywords = ['warehouse management', 'inventory', 'logistics', 'supply chain', 'automation']
        for kw in keywords:
            db.execute("""INSERT INTO social_monitoring
                (keyword, platform, mentions_count, sentiment_score,
                 last_monitored, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (kw, random.choice(['All', 'Twitter', 'LinkedIn']),
                 random.randint(10, 500), random.uniform(0.3, 0.9),
                 days_ago(random.randint(1, 7)), now()))
        print("      + social_monitoring: monitoring added")
    
    # social_kpis
    if table_exists('social_kpis', db) and get_count('social_kpis', db) == 0:
        kpis = [
            ('Followers', 'Total followers', 'Count'),
            ('Engagement Rate', 'Posts engagement', 'Percentage'),
            ('Reach', 'Content reach', 'Count'),
            ('Click Rate', 'Link clicks', 'Percentage'),
        ]
        for name, desc, unit in kpis:
            db.execute("""INSERT INTO social_kpis
                (kpi_name, description, target_value, current_value,
                 unit, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (name, desc, random.uniform(1000, 10000),
                 random.uniform(500, 9000), unit, now()))
        print("      + social_kpis: KPIs added")
    
    # social_roles
    if table_exists('social_roles', db) and get_count('social_roles', db) == 0:
        roles = ['Social Media Manager', 'Content Creator', 'Community Manager', 'Analytics']
        for role in roles:
            db.execute("""INSERT INTO social_roles
                (role_name, description, permissions, created_at)
                VALUES (?, ?, ?, ?)""",
                (role, f'{role} role',
                 f'["read", "write", "publish"]', now()))
        print("      + social_roles: roles added")
    
    # social_settings
    if table_exists('social_settings', db) and get_count('social_settings', db) == 0:
        settings = [
            ('auto_post', 'true', 'Auto posting enabled'),
            ('moderation', 'true', 'Content moderation enabled'),
            ('notifications', 'email', 'Email notifications'),
        ]
        for key, value, desc in settings:
            db.execute("""INSERT INTO social_settings
                (setting_key, setting_value, description, created_at)
                VALUES (?, ?, ?, ?)""",
                (key, value, desc, now()))
        print("      + social_settings: settings added")
    
    db.commit()


# =============================================================================
# HR EXTENDED TABLES
# =============================================================================

def seed_hr_extended_tables(db, cols):
    """Seed all empty HR extended tables."""
    
    emp_ids = get_any_id('hr_employees', db, 30)
    if not emp_ids:
        emp_ids = list(range(1, 20))
    
    # hr_leave_requests
    if table_exists('hr_leave_requests', db) and get_count('hr_leave_requests', db) == 0:
        leave_types = get_any_id('hr_leave_types', db, 10)
        if not leave_types:
            leave_types = [1, 2, 3]
        
        for i in range(25):
            db.execute("""INSERT INTO hr_leave_requests
                (employee_id, leave_type_id, start_date, end_date, total_days,
                 reason, status, approved_by, approved_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(emp_ids), random.choice(leave_types),
                 days_ago(random.randint(-30, 30)), days_ago(random.randint(-20, 40)),
                 random.randint(1, 10), f'Leave request {i+1}',
                 random.choice(['Pending', 'Approved', 'Rejected']),
                 random.randint(1, 10) if random.random() > 0.3 else None,
                 days_ago(random.randint(1, 25)) if random.random() > 0.5 else None, now()))
        print("      + hr_leave_requests: leave requests added")
    
    # hr_leave_balances
    if table_exists('hr_leave_balances', db) and get_count('hr_leave_balances', db) == 0:
        leave_type_ids = get_any_id('hr_leave_types', db, 10)
        if not leave_type_ids:
            leave_type_ids = [1, 2, 3]
        
        for emp_id in emp_ids[:20]:
            for lt_id in leave_type_ids:
                db.execute("""INSERT INTO hr_leave_balances
                    (employee_id, leave_type_id, entitled_days, used_days, pending_days,
                     balance_days, year, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (emp_id, lt_id, random.randint(15, 30), random.randint(0, 15),
                     random.randint(0, 5), random.randint(0, 20),
                     2026, now()))
        print("      + hr_leave_balances: leave balances added")
    
    # hr_loans
    if table_exists('hr_loans', db) and get_count('hr_loans', db) == 0:
        for i in range(15):
            db.execute("""INSERT INTO hr_loans
                (employee_id, loan_type, principal_amount, monthly_payment,
                 tenure_months, status, application_date, approval_date,
                 start_date, end_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(emp_ids), random.choice(['Personal', 'Home', 'Car', 'Education']),
                 random.uniform(5000, 50000), random.uniform(200, 2000),
                 random.choice([12, 24, 36, 48]),
                 random.choice(['Active', 'Closed', 'Pending']),
                 days_ago(random.randint(60, 300)),
                 days_ago(random.randint(30, 250)),
                 days_ago(random.randint(20, 200)),
                 days_ago(random.randint(-180, 0)), now()))
        print("      + hr_loans: loans added")
    
    # hr_loan_installments
    if table_exists('hr_loan_installments', db) and get_count('hr_loan_installments', db) == 0:
        loan_ids = get_any_id('hr_loans', db, 20)
        for loan_id in loan_ids[:10]:
            for i in range(1, random.randint(6, 13)):
                db.execute("""INSERT INTO hr_loan_installments
                    (loan_id, installment_number, amount, due_date, paid_date,
                     status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (loan_id, i, random.uniform(200, 2000),
                     days_ago(random.randint(-180, 180)),
                     days_ago(random.randint(-150, 180)) if random.random() > 0.3 else None,
                     random.choice(['Pending', 'Paid', 'Overdue']),
                     now()))
        print("      + hr_loan_installments: installments added")
    
    # hr_bonus_records
    if table_exists('hr_bonus_records', db) and get_count('hr_bonus_records', db) == 0:
        bonus_types = ['Performance', 'Year-End', 'Project', 'Holiday', 'Retention']
        for i in range(20):
            db.execute("""INSERT INTO hr_bonus_records
                (employee_id, bonus_type, amount, bonus_date, reason,
                 status, approved_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(emp_ids), random.choice(bonus_types),
                 random.uniform(500, 5000),
                 days_ago(random.randint(1, 180)),
                 f'Bonus for performance {i+1}',
                 random.choice(['Pending', 'Approved', 'Paid']),
                 random.randint(1, 5), now()))
        print("      + hr_bonus_records: bonus records added")
    
    # hr_deduction_records
    if table_exists('hr_deduction_records', db) and get_count('hr_deduction_records', db) == 0:
        ded_types = ['Late', 'Absent', 'Equipment', 'Advance', 'Loan']
        for i in range(20):
            db.execute("""INSERT INTO hr_deduction_records
                (employee_id, deduction_type, amount, deduction_date,
                 reason, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(emp_ids), random.choice(ded_types),
                 random.uniform(50, 500),
                 days_ago(random.randint(1, 60)),
                 f'Deduction reason {i+1}',
                 random.choice(['Pending', 'Approved', 'Rejected']), now()))
        print("      + hr_deduction_records: deduction records added")
    
    # hr_overtime_requests
    if table_exists('hr_overtime_requests', db) and get_count('hr_overtime_requests', db) == 0:
        for i in range(15):
            db.execute("""INSERT INTO hr_overtime_requests
                (employee_id, overtime_date, hours, overtime_type,
                 reason, status, approved_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(emp_ids),
                 days_ago(random.randint(1, 30)),
                 random.uniform(1, 8),
                 random.choice(['Weekday', 'Weekend', 'Holiday']),
                 f'Overtime request {i+1}',
                 random.choice(['Pending', 'Approved', 'Rejected']),
                 random.randint(1, 5), now()))
        print("      + hr_overtime_requests: overtime requests added")
    
    # hr_payroll_periods
    if table_exists('hr_payroll_periods', db) and get_count('hr_payroll_periods', db) == 0:
        for month in range(1, 4):
            db.execute("""INSERT INTO hr_payroll_periods
                (period_name, period_start, period_end, status,
                 processed_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f'April 2026', f'2026-0{month}-01', f'2026-0{month}-30',
                 'Processed' if month < 4 else 'Draft',
                 days_ago(random.randint(5, 30)), now()))
        print("      + hr_payroll_periods: payroll periods added")
    
    # hr_payroll_records
    if table_exists('hr_payroll_records', db) and get_count('hr_payroll_records', db) == 0:
        period_ids = get_any_id('hr_payroll_periods', db, 10)
        for emp_id in emp_ids[:15]:
            for period_id in (period_ids if period_ids else [1]):
                db.execute("""INSERT INTO hr_payroll_records
                    (employee_id, period_id, basic_salary, allowances,
                     deductions, net_salary, status, processed_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (emp_id, period_id, random.uniform(5000, 15000),
                     random.uniform(500, 3000), random.uniform(200, 2000),
                     random.uniform(5000, 15000), 'Processed',
                     days_ago(random.randint(5, 30)), now()))
        print("      + hr_payroll_records: payroll records added")
    
    # hr_employee_salary
    if table_exists('hr_employee_salary', db) and get_count('hr_employee_salary', db) == 0:
        for emp_id in emp_ids[:20]:
            db.execute("""INSERT INTO hr_employee_salary
                (employee_id, basic_salary, housing_allowance, transport_allowance,
                 other_allowances, effective_from, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (emp_id, random.uniform(5000, 15000),
                 random.uniform(2000, 5000), random.uniform(1000, 2000),
                 random.uniform(500, 1500), days_ago(random.randint(30, 180)), now()))
        print("      + hr_employee_salary: salaries added")
    
    # hr_training_programs
    if table_exists('hr_training_programs', db) and get_count('hr_training_programs', db) == 0:
        programs = ['Leadership', 'Technical Skills', 'Safety', 'Customer Service', 'IT']
        for prog in programs:
            db.execute("""INSERT INTO hr_training_programs
                (program_name, description, duration_hours, program_type,
                 target_audience, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f'{prog} Training', f'{prog} training program',
                 random.randint(8, 40),
                 random.choice(['Internal', 'External', 'Online']),
                 random.choice(['Managers', 'All Employees', 'Technical Staff']),
                 'Active', now()))
        print("      + hr_training_programs: training programs added")
    
    # hr_training_sessions
    if table_exists('hr_training_sessions', db) and get_count('hr_training_sessions', db) == 0:
        prog_ids = get_any_id('hr_training_programs', db, 10)
        for i, prog_id in enumerate(prog_ids[:5] if prog_ids else [1]):
            db.execute("""INSERT INTO hr_training_sessions
                (program_id, session_name, trainer_name, start_date, end_date,
                 location, max_participants, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (prog_id, f'Session {i+1}', f'Trainer {i+1}',
                 days_ago(random.randint(-30, 30)),
                 days_ago(random.randint(-20, 40)),
                 random.choice(['Training Room A', 'Training Room B', 'Online']),
                 random.randint(10, 30),
                 random.choice(['Scheduled', 'In Progress', 'Completed']), now()))
        print("      + hr_training_sessions: training sessions added")
    
    # hr_training_enrollments
    if table_exists('hr_training_enrollments', db) and get_count('hr_training_enrollments', db) == 0:
        sess_ids = get_any_id('hr_training_sessions', db, 10)
        for sess_id in sess_ids[:5] if sess_ids else [1]:
            for emp_id in random.sample(emp_ids, random.randint(5, 10)):
                db.execute("""INSERT INTO hr_training_enrollments
                    (session_id, employee_id, enrollment_date, attendance_status,
                     assessment_score, certificate_issued, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (sess_id, emp_id, days_ago(random.randint(10, 60)),
                     random.choice(['Registered', 'Attended', 'Completed']),
                     random.uniform(60, 100),
                     'Yes' if random.random() > 0.4 else 'No', now()))
        print("      + hr_training_enrollments: enrollments added")
    
    # hr_employee_documents
    if table_exists('hr_employee_documents', db) and get_count('hr_employee_documents', db) == 0:
        doc_types = ['Contract', 'ID', 'Certificate', 'Visa', 'Insurance']
        for emp_id in emp_ids[:15]:
            for doc_type in random.sample(doc_types, 3):
                db.execute("""INSERT INTO hr_employee_documents
                    (employee_id, document_type, document_name, document_number,
                     issue_date, expiry_date, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (emp_id, doc_type, f'{doc_type} Document',
                     f'DOC-{random.randint(10000, 99999)}',
                     days_ago(random.randint(100, 365)),
                     days_ago(random.randint(-180, 0)), now()))
        print("      + hr_employee_documents: documents added")
    
    # hr_performance_reviews
    if table_exists('hr_performance_reviews', db) and get_count('hr_performance_reviews', db) == 0:
        for i in range(15):
            db.execute("""INSERT INTO hr_performance_reviews
                (employee_id, review_period, reviewer_id, review_date,
                 overall_rating, strengths, improvements, comments,
                 status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(emp_ids), '2026 Q1',
                 random.randint(1, 10), days_ago(random.randint(1, 60)),
                 random.uniform(3.0, 5.0),
                 f'Strengths for employee {i+1}',
                 f'Areas for improvement {i+1}',
                 f'Comments {i+1}',
                 random.choice(['Draft', 'Submitted', 'Completed']), now()))
        print("      + hr_performance_reviews: reviews added")
    
    # hr_successors
    if table_exists('hr_successors', db) and get_count('hr_successors', db) == 0:
        for i in range(10):
            db.execute("""INSERT INTO hr_successors
                (current_employee_id, successor_employee_id, position_id,
                 readiness_level, development_plan, target_date, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(emp_ids), random.choice(emp_ids),
                 random.randint(1, 10),
                 random.choice(['Ready Now', '1-2 Years', '2-3 Years']),
                 f'Development plan {i+1}',
                 days_ago(random.randint(-180, 180)),
                 random.choice(['Identified', 'In Progress', 'Completed']), now()))
        print("      + hr_successors: successors added")
    
    # hr_tasks
    if table_exists('hr_tasks', db) and get_count('hr_tasks', db) == 0:
        for i in range(20):
            db.execute("""INSERT INTO hr_tasks
                (task_title, description, assigned_to, assigned_by,
                 due_date, priority, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'HR Task {i+1}', f'Task description {i+1}',
                 random.choice(emp_ids), random.randint(1, 10),
                 days_ago(random.randint(-15, 30)),
                 random.choice(['Low', 'Medium', 'High', 'Urgent']),
                 random.choice(['Pending', 'In Progress', 'Completed']), now()))
        print("      + hr_tasks: tasks added")
    
    # hr_approvals
    if table_exists('hr_approvals', db) and get_count('hr_approvals', db) == 0:
        types = ['Leave', 'Overtime', 'Loan', 'Expense', 'Training']
        for i in range(20):
            db.execute("""INSERT INTO hr_approvals
                (approval_type, reference_id, requested_by, approved_by,
                 request_date, approval_date, status, comments, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(types), random.randint(1, 50),
                 random.choice(emp_ids), random.randint(1, 10),
                 days_ago(random.randint(1, 30)),
                 days_ago(random.randint(0, 20)),
                 random.choice(['Pending', 'Approved', 'Rejected']),
                 f'Approval comments {i+1}', now()))
        print("      + hr_approvals: approvals added")
    
    # hr_notification_templates
    if table_exists('hr_notification_templates', db) and get_count('hr_notification_templates', db) == 0:
        templates = [
            ('Leave Approval', 'Your leave request has been {{status}}'),
            ('Overtime Reminder', 'Please submit your overtime for {{date}}'),
            ('Performance Review', 'Your performance review is scheduled for {{date}}'),
            ('Birthday', 'Happy Birthday! Wishing you a wonderful day!'),
        ]
        for name, content in templates:
            db.execute("""INSERT INTO hr_notification_templates
                (template_name, content, notification_type, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (name, content, 'Email', 'Yes', now()))
        print("      + hr_notification_templates: templates added")
    
    db.commit()


# =============================================================================
# WMS EXTENDED TABLES
# =============================================================================

def seed_wms_extended_tables(db, cols):
    """Seed all empty WMS extended tables."""
    
    # wms_transfers
    if table_exists('wms_transfers', db) and get_count('wms_transfers', db) == 0:
        wh_ids = get_any_id('wms_warehouses', db, 10)
        if not wh_ids:
            wh_ids = [1, 2, 3]
        
        for i in range(20):
            from_wh = random.choice(wh_ids)
            to_wh = random.choice([w for w in wh_ids if w != from_wh])
            db.execute("""INSERT INTO wms_transfers
                (transfer_number, from_warehouse_id, to_warehouse_id, transfer_date,
                 status, initiated_by, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'TRF-2026-{i+1:04d}', from_wh, to_wh,
                 days_ago(random.randint(1, 30)),
                 random.choice(['Draft', 'In Transit', 'Received', 'Completed']),
                 random.randint(1, 10), f'Transfer {i+1}', now()))
        print("      + wms_transfers: transfers added")
    
    # wms_transfer_lines
    if table_exists('wms_transfer_lines', db) and get_count('wms_transfer_lines', db) == 0:
        trf_ids = get_any_id('wms_transfers', db, 30)
        part_ids = get_any_id('parts', db, 50)
        for trf_id in trf_ids[:15]:
            for i in range(random.randint(1, 5)):
                db.execute("""INSERT INTO wms_transfer_lines
                    (transfer_id, part_id, quantity, created_at)
                    VALUES (?, ?, ?, ?)""",
                    (trf_id, random.choice(part_ids) if part_ids else 1,
                     random.randint(5, 50), now()))
        print("      + wms_transfer_lines: transfer lines added")
    
    # wms_shipments
    if table_exists('wms_shipments', db) and get_count('wms_shipments', db) == 0:
        for i in range(15):
            db.execute("""INSERT INTO wms_shipments
                (shipment_number, warehouse_id, shipment_type, ship_date,
                 status, carrier, tracking_number, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'SHP-2026-{i+1:04d}', random.randint(1, 4),
                 random.choice(['Outbound', 'Inbound']),
                 days_ago(random.randint(1, 30)),
                 random.choice(['Preparing', 'Shipped', 'In Transit', 'Delivered']),
                 random.choice(['DHL', 'FedEx', 'Aramex']),
                 f'TRK-{random.randint(100000, 999999)}',
                 f'Shipment {i+1}', now()))
        print("      + wms_shipments: shipments added")
    
    # wms_returns
    if table_exists('wms_returns', db) and get_count('wms_returns', db) == 0:
        reasons = ['Defective', 'Wrong Item', 'Changed Mind', 'Damaged']
        for i in range(12):
            db.execute("""INSERT INTO wms_returns
                (return_number, customer_id, return_date, reason,
                 status, refund_amount, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'RET-2026-{i+1:04d}', random.randint(1, 50),
                 days_ago(random.randint(1, 30)),
                 random.choice(reasons),
                 random.choice(['Pending', 'Approved', 'Received', 'Refunded']),
                 random.uniform(100, 5000), f'Return {i+1}', now()))
        print("      + wms_returns: returns added")
    
    # wms_stock_adjustments
    if table_exists('wms_stock_adjustments', db) and get_count('wms_stock_adjustments', db) == 0:
        for i in range(15):
            db.execute("""INSERT INTO wms_stock_adjustments
                (adjustment_number, warehouse_id, adjustment_date, adjustment_type,
                 reason, status, approved_by, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'ADJ-2026-{i+1:04d}', random.randint(1, 4),
                 days_ago(random.randint(1, 30)),
                 random.choice(['Count', 'Damage', 'Theft', 'Expiry', 'Other']),
                 f'Adjustment reason {i+1}',
                 random.choice(['Draft', 'Approved', 'Applied']),
                 random.randint(1, 10), f'Adjustment {i+1}', now()))
        print("      + wms_stock_adjustments: adjustments added")
    
    # wms_stock_counts
    if table_exists('wms_stock_counts', db) and get_count('wms_stock_counts', db) == 0:
        for i in range(10):
            db.execute("""INSERT INTO wms_stock_counts
                (count_number, warehouse_id, count_date, count_type,
                 status, counted_by, approved_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'CNT-2026-{i+1:04d}', random.randint(1, 4),
                 days_ago(random.randint(1, 45)),
                 random.choice(['Full', 'Partial', 'Cycle']),
                 random.choice(['Draft', 'In Progress', 'Completed']),
                 random.randint(1, 10), random.randint(1, 10), now()))
        print("      + wms_stock_counts: stock counts added")
    
    # wms_inbound_receipts
    if table_exists('wms_inbound_receipts', db) and get_count('wms_inbound_receipts', db) == 0:
        for i in range(15):
            db.execute("""INSERT INTO wms_inbound_receipts
                (receipt_number, po_number, warehouse_id, receipt_date,
                 supplier_name, status, received_by, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'INB-2026-{i+1:04d}', f'PO-2026-{random.randint(1,200):04d}',
                 random.randint(1, 4), days_ago(random.randint(1, 30)),
                 f'Supplier {random.randint(1,30)}',
                 random.choice(['Pending', 'In Progress', 'Completed']),
                 random.randint(1, 10), f'Inbound receipt {i+1}', now()))
        print("      + wms_inbound_receipts: inbound receipts added")
    
    # wms_outbound_orders
    if table_exists('wms_outbound_orders', db) and get_count('wms_outbound_orders', db) == 0:
        for i in range(15):
            db.execute("""INSERT INTO wms_outbound_orders
                (order_number, warehouse_id, order_date, order_type,
                 status, picked_by, shipped_by, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'OBO-2026-{i+1:04d}', random.randint(1, 4),
                 days_ago(random.randint(1, 30)),
                 random.choice(['Sales', 'Transfer', 'Return']),
                 random.choice(['Pending', 'Picked', 'Shipped', 'Delivered']),
                 random.randint(1, 10), random.randint(1, 10),
                 f'Outbound order {i+1}', now()))
        print("      + wms_outbound_orders: outbound orders added")
    
    db.commit()


# =============================================================================
# DOCUMENT TABLES
# =============================================================================

def seed_document_tables(db, cols):
    """Seed all empty document tables."""
    
    # document_categories
    if table_exists('document_categories', db) and get_count('document_categories', db) == 0:
        categories = ['Contracts', 'Invoices', 'Reports', 'Policies', 'Manuals', 'Certifications']
        for cat in categories:
            db.execute("""INSERT INTO document_categories
                (category_name, description, parent_id, created_at)
                VALUES (?, ?, ?, ?)""",
                (cat, f'{cat} category documents', None, now()))
        print("      + document_categories: categories added")
    
    # document_tags
    if table_exists('document_tags', db) and get_count('document_tags', db) == 0:
        tags = ['Important', 'Urgent', 'Confidential', 'Draft', 'Final', 'Archived']
        for tag in tags:
            db.execute("""INSERT INTO document_tags (tag_name, created_at) VALUES (?, ?)""",
                (tag, now()))
        print("      + document_tags: tags added")
    
    # document_shares
    if table_exists('document_shares', db) and get_count('document_shares', db) == 0:
        doc_ids = get_any_id('documents', db, 20)
        for doc_id in doc_ids[:10]:
            for i in range(random.randint(1, 3)):
                db.execute("""INSERT INTO document_shares
                    (document_id, shared_with, permission_level, shared_at, expires_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)""",
                    (doc_id, random.randint(1, 15), random.choice(['Read', 'Write', 'Admin']),
                     days_ago(random.randint(1, 30)),
                     days_ago(random.randint(-30, 0)) if random.random() > 0.7 else None, now()))
        print("      + document_shares: shares added")
    
    db.commit()


# =============================================================================
# FORM TABLES
# =============================================================================

def seed_form_tables(db, cols):
    """Seed all empty form tables."""
    
    # form_submissions
    if table_exists('form_submissions', db) and get_count('form_submissions', db) == 0:
        template_ids = get_any_id('form_templates', db, 10)
        if not template_ids:
            template_ids = [1, 2, 3]
        
        for i in range(20):
            db.execute("""INSERT INTO form_submissions
                (template_id, submitted_by, submission_date, status,
                 approved_by, approved_at, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.choice(template_ids), random.randint(1, 15),
                 days_ago(random.randint(1, 45)),
                 random.choice(['Draft', 'Submitted', 'Approved', 'Rejected']),
                 random.randint(1, 10) if random.random() > 0.4 else None,
                 days_ago(random.randint(1, 30)) if random.random() > 0.5 else None,
                 f'Submission notes {i+1}', now()))
        print("      + form_submissions: submissions added")
    
    # form_submission_values
    if table_exists('form_submission_values', db) and get_count('form_submission_values', db) == 0:
        sub_ids = get_any_id('form_submissions', db, 30)
        field_ids = get_any_id('form_fields', db, 20)
        for sub_id in sub_ids[:15]:
            for field_id in (field_ids if field_ids else [1, 2, 3]):
                db.execute("""INSERT INTO form_submission_values
                    (submission_id, field_id, field_value, created_at)
                    VALUES (?, ?, ?, ?)""",
                    (sub_id, field_id, f'Value for field {field_id}', now()))
        print("      + form_submission_values: submission values added")
    
    # form_comments
    if table_exists('form_comments', db) and get_count('form_comments', db) == 0:
        for i in range(15):
            db.execute("""INSERT INTO form_comments
                (submission_id, user_id, comment_text, created_at)
                VALUES (?, ?, ?, ?)""",
                (random.randint(1, 20), random.randint(1, 15),
                 f'Comment {i+1}', now()))
        print("      + form_comments: comments added")
    
    # form_approvals
    if table_exists('form_approvals', db) and get_count('form_approvals', db) == 0:
        for i in range(15):
            db.execute("""INSERT INTO form_approvals
                (submission_id, approver_id, approval_date, status,
                 comments, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 20), random.randint(1, 10),
                 days_ago(random.randint(1, 30)),
                 random.choice(['Pending', 'Approved', 'Rejected']),
                 f'Approval comments {i+1}', now()))
        print("      + form_approvals: approvals added")
    
    db.commit()


# =============================================================================
# API GATEWAY TABLES
# =============================================================================

def seed_api_gateway_tables(db, cols):
    """Seed all empty API gateway tables."""
    
    # api_clients
    if table_exists('api_clients', db) and get_count('api_clients', db) == 0:
        clients = [
            ('Mobile App', 'Mobile application client'),
            ('Web Dashboard', 'Web dashboard client'),
            ('Partner API', 'Partner integration'),
            ('Internal Service', 'Internal microservice'),
        ]
        for name, desc in clients:
            db.execute("""INSERT INTO api_clients
                (client_name, description, client_type, status,
                 rate_limit_per_hour, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (name, desc, 'Confidential', 'Active',
                 random.randint(1000, 10000), now()))
        print("      + api_clients: API clients added")
    
    # api_access_policies
    if table_exists('api_access_policies', db) and get_count('api_access_policies', db) == 0:
        for i in range(8):
            db.execute("""INSERT INTO api_access_policies
                (policy_name, resource_pattern, http_method, effect,
                 priority, description, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (f'Policy {i+1}', f'/api/v1/*', random.choice(['GET', 'POST', 'PUT', 'DELETE']),
                 random.choice(['Allow', 'Deny']), random.randint(1, 100),
                 f'Access policy {i+1}', 'Yes', now()))
        print("      + api_access_policies: policies added")
    
    # api_request_logs
    if table_exists('api_request_logs', db) and get_count('api_request_logs', db) == 0:
        for i in range(50):
            db.execute("""INSERT INTO api_request_logs
                (client_id, endpoint, http_method, response_code,
                 response_time_ms, request_size, ip_address, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 4), f'/api/v1/resource/{random.randint(1,20)}',
                 random.choice(['GET', 'POST', 'PUT', 'DELETE']),
                 random.choice([200, 200, 200, 400, 401, 404, 500]),
                 random.randint(10, 2000), random.randint(100, 10000),
                 f'192.168.1.{random.randint(1,255)}', now()))
        print("      + api_request_logs: request logs added")
    
    # api_route_registry
    if table_exists('api_route_registry', db) and get_count('api_route_registry', db) == 0:
        routes = [
            ('/api/v1/inventory', 'GET', 'inventory', 'Inventory service'),
            ('/api/v1/orders', 'POST', 'orders', 'Orders service'),
            ('/api/v1/customers', 'GET', 'customers', 'Customer service'),
            ('/api/v1/suppliers', 'GET', 'suppliers', 'Supplier service'),
        ]
        for path, method, service, desc in routes:
            db.execute("""INSERT INTO api_route_registry
                (route_path, http_method, backend_service, description,
                 rate_limit, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (path, method, service, desc, random.randint(100, 1000), 'Yes', now()))
        print("      + api_route_registry: routes added")
    
    # webhook_subscriptions
    if table_exists('webhook_subscriptions', db) and get_count('webhook_subscriptions', db) == 0:
        events = ['order.created', 'order.updated', 'shipment.delivered', 'customer.added']
        for i, event in enumerate(events):
            db.execute("""INSERT INTO webhook_subscriptions
                (subscription_name, webhook_url, secret_key, events,
                 is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f'Webhook {i+1}', f'https://example.com/webhook/{i+1}',
                 f'secret_{random.randint(10000, 99999)}',
                 event, 'Yes', now()))
        print("      + webhook_subscriptions: subscriptions added")
    
    # webhook_deliveries
    if table_exists('webhook_deliveries', db) and get_count('webhook_deliveries', db) == 0:
        sub_ids = get_any_id('webhook_subscriptions', db, 10)
        for sub_id in sub_ids[:4] if sub_ids else [1]:
            for i in range(random.randint(5, 15)):
                db.execute("""INSERT INTO webhook_deliveries
                    (subscription_id, event_type, payload, response_code,
                     response_body, attempt_number, delivered_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (sub_id, f'event.{random.randint(1,4)}',
                     f'{{"id": {i+1}, "data": "sample"}}',
                     random.choice([200, 200, 400, 500]),
                     'OK' if random.random() > 0.2 else 'Error',
                     random.randint(1, 3),
                     days_ago(random.randint(1, 15)), now()))
        print("      + webhook_deliveries: deliveries added")
    
    db.commit()


# =============================================================================
# BI TABLES
# =============================================================================

def seed_bi_tables(db, cols):
    """Seed all empty BI tables."""
    
    # bi_reporting_datasets
    if table_exists('bi_reporting_datasets', db) and get_count('bi_reporting_datasets', db) == 0:
        datasets = [
            ('Sales Dataset', 'Sales transactions data', 'sales_orders,sales_order_lines'),
            ('Inventory Dataset', 'Inventory levels', 'inventory,parts'),
            ('HR Dataset', 'Employee data', 'hr_employees,hr_attendance'),
            ('Finance Dataset', 'Financial transactions', 'finance_journals,finance_accounts'),
        ]
        for name, desc, tables in datasets:
            db.execute("""INSERT INTO bi_reporting_datasets
                (dataset_name, description, source_tables, refresh_schedule,
                 last_refreshed, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (name, desc, tables, 'Daily',
                 days_ago(random.randint(1, 7)), 'Yes', now()))
        print("      + bi_reporting_datasets: datasets added")
    
    # bi_kpis
    if table_exists('bi_kpis', db) and get_count('bi_kpis', db) == 0:
        kpis = [
            ('Total Revenue', 'SUM', 'finance_customer_invoices', 'total_amount'),
            ('Order Count', 'COUNT', 'sales_orders', 'id'),
            ('Inventory Value', 'SUM', 'inventory', 'quantity'),
            ('Employee Count', 'COUNT', 'hr_employees', 'id'),
        ]
        for name, agg, table, field in kpis:
            db.execute("""INSERT INTO bi_kpis
                (kpi_name, description, aggregation, source_table, source_field,
                 target_value, unit, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, f'{name} KPI', agg, table, field,
                 random.uniform(100000, 1000000), 'AED', now()))
        print("      + bi_kpis: KPIs added")
    
    # bi_saved_reports
    if table_exists('bi_saved_reports', db) and get_count('bi_saved_reports', db) == 0:
        for i in range(10):
            db.execute("""INSERT INTO bi_saved_reports
                (report_name, report_type, description, parameters,
                 created_by, is_shared, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (f'Report {i+1}', random.choice(['Sales', 'Inventory', 'Finance', 'HR']),
                 f'Report description {i+1}',
                 f'{{"date_from": "2026-01-01", "date_to": "2026-04-01"}}',
                 random.randint(1, 10), 'Yes' if random.random() > 0.5 else 'No', now()))
        print("      + bi_saved_reports: reports added")
    
    db.commit()


# =============================================================================
# QUALITY EXTENDED TABLES
# =============================================================================

def seed_quality_extended_tables(db, cols):
    """Seed all empty quality tables."""
    
    # quality_inspection_templates
    if table_exists('quality_inspection_templates', db) and get_count('quality_inspection_templates', db) == 0:
        templates = [
            ('Incoming Inspection', 'Incoming goods inspection'),
            ('In-Process Inspection', 'During production inspection'),
            ('Final Inspection', 'Before shipment inspection'),
        ]
        for name, desc in templates:
            db.execute("""INSERT INTO quality_inspection_templates
                (template_name, description, checklist_items,
                 is_active, created_at)
                VALUES (?, ?, ?, ?, ?)""",
                (name, desc, random.randint(10, 30), 'Yes', now()))
        print("      + quality_inspection_templates: templates added")
    
    # quality_capa_actions
    if table_exists('quality_capa_actions', db) and get_count('quality_capa_actions', db) == 0:
        capa_ids = get_any_id('quality_capa_records', db, 10)
        actions = ['Root Cause Analysis', 'Corrective Action', 'Preventive Action', 'Verification']
        for capa_id in capa_ids[:5] if capa_ids else [1]:
            for action in random.sample(actions, 3):
                db.execute("""INSERT INTO quality_capa_actions
                    (capa_id, action_type, description, assigned_to,
                     due_date, status, completed_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (capa_id, action, f'{action} description',
                     random.randint(1, 10), days_ago(random.randint(-15, 30)),
                     random.choice(['Open', 'In Progress', 'Completed']),
                     days_ago(random.randint(-10, 0)) if random.random() > 0.5 else None, now()))
        print("      + quality_capa_actions: actions added")
    
    db.commit()


# =============================================================================
# OTHER EMPTY TABLES
# =============================================================================

def seed_other_tables(db, cols):
    """Seed other empty tables."""
    
    # numbering_sequences
    if table_exists('numbering_sequences', db) and get_count('numbering_sequences', db) == 0:
        sequences = [
            ('SO', 'Sales Order', 'SO-'),
            ('PO', 'Purchase Order', 'PO-'),
            ('INV', 'Invoice', 'INV-'),
            ('DO', 'Delivery', 'DO-'),
        ]
        for prefix, name, pattern in sequences:
            db.execute("""INSERT INTO numbering_sequences
                (sequence_name, prefix, current_value, format_pattern,
                 is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (name, prefix, random.randint(100, 999),
                 f'{pattern}YYYY-####', 'Yes', now()))
        print("      + numbering_sequences: sequences added")
    
    # user_sessions
    if table_exists('user_sessions', db) and get_count('user_sessions', db) == 0:
        for i in range(15):
            db.execute("""INSERT INTO user_sessions
                (user_id, session_token, ip_address, user_agent,
                 created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 13), f'token_{random.randint(10000, 99999)}',
                 f'192.168.1.{random.randint(1,255)}', 'Mozilla/5.0',
                 days_ago(random.randint(1, 30)),
                 days_ago(random.randint(-30, 0)) if random.random() > 0.7 else None, now()))
        print("      + user_sessions: sessions added")
    
    # notification_logs
    if table_exists('notification_logs', db) and get_count('notification_logs', db) == 0:
        for i in range(20):
            db.execute("""INSERT INTO notification_logs
                (user_id, notification_type, title, message, is_read,
                 sent_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (random.randint(1, 13), random.choice(['Email', 'SMS', 'In-App']),
                 f'Notification {i+1}', f'Message {i+1}',
                 'Yes' if random.random() > 0.5 else 'No',
                 days_ago(random.randint(1, 15)), now()))
        print("      + notification_logs: notification logs added")
    
    # saved_reports
    if table_exists('saved_reports', db) and get_count('saved_reports', db) == 0:
        for i in range(12):
            db.execute("""INSERT INTO saved_reports
                (report_name, report_type, parameters, created_by,
                 is_shared, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (f'Saved Report {i+1}', random.choice(['Sales', 'Inventory', 'Financial']),
                 f'{{"date": "2026-04"}}', random.randint(1, 10),
                 'Yes' if random.random() > 0.5 else 'No', now()))
        print("      + saved_reports: saved reports added")
    
    db.commit()


# =============================================================================
# MAIN
# =============================================================================

def seed_all():
    """Seed all empty tables."""
    print("=" * 70)
    print("  MMDx COMPREHENSIVE DEMO DATA SEEDER")
    print("  Filling ALL Empty Tables")
    print("=" * 70)
    print()
    
    db = get_db()
    
    # Seed each category
    categories = [
        ("MASTER DATA (md_ tables)", seed_md_tables),
        ("SALES MODULE", seed_sales_tables),
        ("PROCUREMENT MODULE", seed_procurement_tables),
        ("FINANCE MODULE", seed_finance_tables),
        ("LOGISTICS MODULE", seed_logistics_tables),
        ("MARKETING MODULE", seed_marketing_tables),
        ("WORKFLOW MODULE", seed_workflow_tables),
        ("HR EXTENDED MODULE", seed_hr_extended_tables),
        ("WMS EXTENDED MODULE", seed_wms_extended_tables),
        ("DOCUMENT MODULE", seed_document_tables),
        ("FORM MODULE", seed_form_tables),
        ("API GATEWAY MODULE", seed_api_gateway_tables),
        ("BI MODULE", seed_bi_tables),
        ("QUALITY EXTENDED MODULE", seed_quality_extended_tables),
        ("OTHER TABLES", seed_other_tables),
    ]
    
    for name, seed_fn in categories:
        print(f"\n>> Seeding {name}...")
        try:
            seed_fn(db, [])
        except Exception as e:
            print(f"    Error: {e}")
    
    db.commit()
    db.close()
    
    print()
    print("=" * 70)
    print("  SEEDING COMPLETE!")
    print("=" * 70)
    print()
    print("Run check_empty_tables.py to verify results.")


if __name__ == '__main__':
    seed_all()
