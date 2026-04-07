"""
Sales Management Suite - Comprehensive Seed Data
=============================================
Seeds the database with realistic demo data for the Sales Management Suite.

This creates:
- Companies (3)
- Warehouses (5)
- Brands and Product Groups
- Parts/Items (200+)
- Customers (80+)
- Sales Users (11)
- Inquiries (80+)
- Quotations (60+)
- Pro Forma Invoices (25+)
- Sales Confirmations (20+)
- Customer POs (18+)
- Sales Orders (30+)
- Reservations (20+)
- Deliveries (18+)
- Sales Invoices (15+)
- Returns/Complaints (8+)
- Sales Activities (200+)
- Targets (12+)
- Contracts (8+)
- Alerts (various)

Usage:
    python seed_sales_suite.py
"""

import sqlite3
import os
import random
from datetime import datetime, timedelta
import hashlib

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'warehouse.db')

# =============================================================================
# REFERENCE DATA
# =============================================================================

COUNTRIES = ['UAE', 'Saudi Arabia', 'Qatar', 'Oman', 'Bahrain', 'Kuwait', 'Egypt', 'Jordan', 'Lebanon', 'Iraq', 'India', 'Pakistan']
CITIES = {
    'UAE': ['Dubai', 'Abu Dhabi', 'Sharjah', 'Ajman', 'Ras Al Khaimah', 'Fujairah'],
    'Saudi Arabia': ['Riyadh', 'Jeddah', 'Dammam', 'Mecca', 'Medina'],
    'Qatar': ['Doha', 'Al Rayyan'],
    'Oman': ['Muscat', 'Salalah'],
    'Bahrain': ['Manama'],
    'Kuwait': ['Kuwait City'],
    'Egypt': ['Cairo', 'Alexandria'],
    'Jordan': ['Amman'],
    'India': ['Mumbai', 'Delhi', 'Chennai', 'Kolkata'],
    'Pakistan': ['Karachi', 'Lahore', 'Islamabad'],
}

BRANDS = [
    'Toyota Genuine', 'Nissan Genuine', 'Mazda Genuine', 'Renault Genuine',
    'Denso', 'Aisin', 'NGK', 'Bosch', 'Valeo', 'KYB', 'GKN', 'Brembo',
    'Hitachi', 'Mitsubishi Genuine', 'Honda Genuine', 'Hyundai Genuine',
    'Aftermarket Premium', 'Economy Line', 'Performance Plus', 'Heavy Duty'
]

PRODUCT_GROUPS = [
    'Engine Parts', 'Electrical Parts', 'Body Parts', 'Suspension Parts',
    'Filters', 'Cooling System', 'Brake Parts', 'Belts & Hoses',
    'Lubricants & Fluids', 'Fast Moving Consumables', 'Steering Parts',
    'Transmission Parts', 'Exhaust System', 'Ignition System', 'Fuel System'
]

CUSTOMER_TYPES = ['Retail', 'Wholesale', 'Key Account', 'Export Distributor', 'Workshop', 'Trader', 'Fleet / Contract', 'Project']
MARKETS = ['Local', 'Export']
SALES_CHANNELS = ['Walk-in', 'Phone', 'WhatsApp', 'Email', 'Website', 'Social Media', 'Field Sales', 'Agent / Referral', 'Exhibition']
PAYMENT_TERMS = ['Net 30', 'Net 45', 'Net 60', 'Net 90', 'Cash', 'Credit Card', 'Bank Transfer', 'Letter of Credit']
INCOTERMS = ['EXW', 'FOB', 'CIF', 'CFR', 'DAP', 'DDP', 'FCA', 'CPT']
CURRENCIES = ['AED', 'USD', 'EUR', 'SAR', 'OMR']

# Sample part numbers by brand
PART_PREFIXES = {
    'Toyota Genuine': 'TYT',
    'Nissan Genuine': 'NIS',
    'Mazda Genuine': 'MZD',
    'Renault Genuine': 'REN',
    'Denso': 'DNS',
    'Aisin': 'ASN',
    'NGK': 'NGK',
    'Bosch': 'BSH',
    'Valeo': 'VLO',
    'KYB': 'KYB',
    'GKN': 'GKN',
    'Brembo': 'BRB',
    'Hitachi': 'HTC',
    'Mitsubishi Genuine': 'MTS',
    'Honda Genuine': 'HON',
    'Hyundai Genuine': 'HYU',
    'Aftermarket Premium': 'AFP',
    'Economy Line': 'ECN',
    'Performance Plus': 'PRF',
    'Heavy Duty': 'HVY',
}

ITEM_CATEGORIES = {
    'Engine Parts': ['Piston', 'Piston Ring', 'Cylinder Head Gasket', 'Timing Belt', 'Oil Pump', 'Water Pump', 'Camshaft', 'Valve', 'Engine Mount'],
    'Electrical Parts': ['Alternator', 'Starter Motor', 'Spark Plug', 'Ignition Coil', 'Battery', 'Sensor', 'Relay', 'Fuse', 'Wiring Harness'],
    'Body Parts': ['Bumper', 'Grille', 'Headlight', 'Taillight', 'Mirror', 'Door Handle', 'Fender', 'Hood', 'Trunk Lid'],
    'Suspension Parts': ['Shock Absorber', 'Strut Assembly', 'Control Arm', 'Ball Joint', 'Tie Rod End', 'Sway Bar Link', 'Coil Spring', 'Leaf Spring'],
    'Filters': ['Air Filter', 'Oil Filter', 'Fuel Filter', 'Cabin Filter', 'Transmission Filter', 'Hydraulic Filter'],
    'Cooling System': ['Radiator', 'Thermostat', 'Cooling Fan', 'Water Outlet', 'Radiator Hose', 'Coolant Reservoir'],
    'Brake Parts': ['Brake Pad', 'Brake Shoe', 'Brake Disc', 'Brake Drum', 'Brake Caliper', 'Master Cylinder', 'Wheel Cylinder', 'Brake Hose'],
    'Belts & Hoses': ['Serpentine Belt', 'Timing Belt', 'V-Belt', 'Radiator Hose', 'Heater Hose', 'Fuel Hose', 'Vacuum Hose'],
    'Lubricants & Fluids': ['Engine Oil', 'Transmission Fluid', 'Brake Fluid', 'Coolant', 'Power Steering Fluid', 'Hydraulic Fluid'],
    'Fast Moving Consumables': ['Wiper Blade', 'Light Bulb', 'Fuse', 'Belt', 'Filter', 'Spark Plug', 'Brake Pad'],
}

COMPANIES = [
    {'code': 'SDAD', 'name': 'SDAD Auto Spare Parts Trading LLC', 'type': 'Trading', 'country': 'UAE', 'city': 'Dubai'},
    {'code': 'AFRA', 'name': 'AFRA Auto Spare Parts Trading FZCO', 'type': 'Trading', 'country': 'UAE', 'city': 'Dubai'},
    {'code': 'CARM', 'name': 'Carmania General Trading LLC', 'type': 'Trading', 'country': 'UAE', 'city': 'Dubai'},
]

BRANCHES = [
    {'code': 'DEIRA', 'name': 'Deira Sales Office', 'company': 'SDAD', 'type': 'Office'},
    {'code': 'RAK_WH', 'name': 'Ras Al Khor Warehouse & Sales Support', 'company': 'SDAD', 'type': 'Warehouse'},
    {'code': 'JAFZA_OFC', 'name': 'JAFZA Office', 'company': 'AFRA', 'type': 'Office'},
    {'code': 'JAFZA_WH', 'name': 'JAFZA Warehouse', 'company': 'AFRA', 'type': 'Warehouse'},
    {'code': 'EXPORT', 'name': 'Export Desk', 'company': 'SDAD', 'type': 'Office'},
    {'code': 'COUNTER', 'name': 'Counter Sales Desk', 'company': 'SDAD', 'type': 'Counter'},
]

WAREHOUSES = [
    {'code': 'SDAD_RAK_MAIN', 'name': 'SDAD Ras Al Khor Main', 'company': 'SDAD', 'type': 'Main'},
    {'code': 'AFRA_JAFZA_MAIN', 'name': 'AFRA JAFZA Main', 'company': 'AFRA', 'type': 'Main'},
    {'code': 'CARMANIA_VIRTUAL', 'name': 'Carmania Virtual Stock', 'company': 'CARM', 'type': 'Virtual'},
    {'code': 'SDAD_TRANSIT', 'name': 'SDAD Transit Stock', 'company': 'SDAD', 'type': 'Transit'},
    {'code': 'AFRA_EXPORT', 'name': 'AFRA Export Staging', 'company': 'AFRA', 'type': 'Export'},
]

SALES_USERS = [
    {'username': 'sales_mgr', 'full_name': 'Ahmed Al Maktoum', 'role': 'Sales Manager', 'email': 'sales_mgr@sdad.com'},
    {'username': 'senior_sales1', 'full_name': 'Fatima Hassan', 'role': 'Senior Sales', 'email': 'senior_sales1@sdad.com'},
    {'username': 'senior_sales2', 'full_name': 'Mohammed Ali', 'role': 'Senior Sales', 'email': 'senior_sales2@sdad.com'},
    {'username': 'sales_exec1', 'full_name': 'Sara Khan', 'role': 'Sales Executive', 'email': 'sales_exec1@sdad.com'},
    {'username': 'sales_exec2', 'full_name': 'John Wilson', 'role': 'Sales Executive', 'email': 'sales_exec2@sdad.com'},
    {'username': 'sales_exec3', 'full_name': 'Priya Sharma', 'role': 'Sales Executive', 'email': 'sales_exec3@sdad.com'},
    {'username': 'sales_exec4', 'full_name': 'Ali Ahmed', 'role': 'Sales Executive', 'email': 'sales_exec4@sdad.com'},
    {'username': 'counter_sales', 'full_name': 'Rashid Al Badour', 'role': 'Counter Sales', 'email': 'counter@sdad.com'},
    {'username': 'export_sales', 'full_name': 'Layla Mahmoud', 'role': 'Export Sales', 'email': 'export@sdad.com'},
    {'username': 'pricing_officer', 'full_name': 'Tariq Nasser', 'role': 'Pricing Officer', 'email': 'pricing@sdad.com'},
    {'username': 'credit_viewer', 'full_name': 'Nadia Hassan', 'role': 'Credit Control', 'email': 'credit@sdad.com'},
    {'username': 'analyst', 'full_name': 'Omar Farouk', 'role': 'Analyst', 'email': 'analyst@sdad.com'},
]

CUSTOMER_NAMES = [
    'Al Roya Auto Services', 'Gulf Motors Workshop', 'Premium Auto Care', 'Speed Fix Garage',
    'Dubai Auto Parts', 'Sharjah Truck Center', 'Abu Dhabi Fleet Services', 'Northern Emirates Motors',
    'Desert Wheels Trading', 'Oasis Automotive', 'Falcon Workshop', 'Eagle Eye Auto',
    'Emirates Auto Electric', 'Al Ain Garage', 'Khalifa Auto Services', 'Mussafah Auto',
    'Industrial Area Workshop', 'Deira Auto Spare', 'Bur Dubai Motors', 'Karama Auto Care',
    'Jumeirah Auto Services', 'Business Bay Garage', 'Downtown Auto Workshop',
    'Muscat Auto Parts LLC', 'Salalah Vehicle Services', 'Sohar Auto Care',
    'Bahrain Auto Works', 'Manama Fleet Services', 'Doha Automotive',
    'Riyadh Auto Services', 'Jeddah Truck Center', 'Dammam Auto Parts',
    'Kuwait City Motors', 'Cairo Auto Trading', 'Alexandria Fleet Services',
    'Amman Auto Works', 'Beirut Automotive', 'Baghdad Auto Services',
    'Mumbai Auto Parts', 'Delhi Motor Services', 'Karachi Auto Works',
    'Lahore Fleet Services', 'Islamabad Auto Care',
    'Red Sea Trading Co', 'Gulf Star Motors', 'Ocean Auto Services',
    'Desert Fleet Services', 'Mountain Auto Care', 'Valley Motors',
    'Sunrise Auto Works', 'Sunset Automotive', 'Palm Auto Services',
    'Marina Motors', 'Creek Auto Care', 'Harbour Auto Works',
    'Lighthouse Auto', 'Beacon Motors', 'Navigator Auto',
    'Champion Auto Services', 'Victory Auto Works', 'Triumph Motors',
    'Elite Auto Care', 'Prime Auto Services', 'Supreme Motors',
    'Royal Auto Trading', 'Crown Auto Works', 'Empire Auto Care',
]

# Sample part number generator
def generate_part_number(brand):
    """Generate a realistic part number based on brand."""
    prefix = PART_PREFIXES.get(brand, 'GEN')
    category_code = random.choice(['ENG', 'ELC', 'BDY', 'SUS', 'FLT', 'COL', 'BRK', 'BLT', 'LUB', 'FMC'])
    number = random.randint(10000, 99999)
    return f"{prefix}-{category_code}-{number}"

def generate_part_description(category, brand):
    """Generate a realistic part description."""
    items = ITEM_CATEGORIES.get(category, ['Part'])
    item = random.choice(items)
    brand_short = brand.split()[0] if brand else 'Universal'
    return f"{brand_short} {item} - Premium Quality"

# =============================================================================
# DATABASE HELPERS
# =============================================================================

def get_connection():
    """Get a database connection with WAL mode."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def table_exists(conn, table_name):
    """Check if a table exists."""
    result = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
        (table_name,)
    ).fetchone()
    return result is not None


def row_exists(conn, table, where_clause, params):
    """Check if a row exists."""
    result = conn.execute(f"SELECT 1 FROM {table} WHERE {where_clause} LIMIT 1", params).fetchone()
    return result is not None


def get_or_create_company(conn, code, name, company_type, country, city):
    """Get or create a company."""
    existing = conn.execute("SELECT id FROM companies WHERE company_code = ?", (code,)).fetchone()
    if existing:
        return existing['id']
    
    cursor = conn.execute("""
        INSERT INTO companies (company_code, name, company_type, country, city, status, created_at)
        VALUES (?, ?, ?, ?, ?, 'Active', CURRENT_TIMESTAMP)
    """, (code, name, company_type, country, city))
    conn.commit()
    return cursor.lastrowid


def get_or_create_warehouse(conn, code, name, company_id, warehouse_type):
    """Get or create a warehouse."""
    existing = conn.execute("SELECT id FROM warehouses WHERE warehouse_code = ?", (code,)).fetchone()
    if existing:
        return existing['id']
    
    cursor = conn.execute("""
        INSERT INTO warehouses (warehouse_code, name, company_id, location, status, warehouse_type, supports_sales_allocation, created_at)
        VALUES (?, ?, ?, ?, 'Active', ?, 1, CURRENT_TIMESTAMP)
    """, (code, name, company_id, name.split()[0], warehouse_type))
    conn.commit()
    return cursor.lastrowid


def get_or_create_user(conn, username, full_name, role_name, email):
    """Get or create a user with role."""
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        return existing['id']
    
    # Get or create role
    role = conn.execute("SELECT id FROM roles WHERE role_name = ?", (role_name,)).fetchone()
    if not role:
        cursor = conn.execute("INSERT INTO roles (role_name) VALUES (?)", (role_name,))
        conn.commit()
        role_id = cursor.lastrowid
    else:
        role_id = role['id']
    
    # Create user
    password_hash = hashlib.sha256(f"{username}_default".encode()).hexdigest()
    cursor = conn.execute("""
        INSERT INTO users (username, password_hash, email, full_name, role_id, company_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, 1, 'Active', CURRENT_TIMESTAMP)
    """, (username, password_hash, email, full_name, role_id, 1))
    conn.commit()
    return cursor.lastrowid


def get_or_create_customer(conn, customer_data):
    """Get or create a customer."""
    existing = conn.execute("SELECT id FROM sales_customers WHERE customer_code = ?", 
                          (customer_data['customer_code'],)).fetchone()
    if existing:
        return existing['id']
    
    cursor = conn.execute("""
        INSERT INTO sales_customers (
            customer_code, name, trade_name, customer_type, market,
            country, city, address, phone, whatsapp, email,
            buyer_name, buyer_phone, trade_type, assigned_salesperson_id,
            payment_terms, credit_limit, currency, default_discount,
            status, priority, total_orders, total_revenue, outstanding_balance,
            last_purchase_date, company_id, is_active, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        customer_data['customer_code'], customer_data['name'], 
        customer_data.get('trade_name', ''),
        customer_data['customer_type'], customer_data['market'],
        customer_data['country'], customer_data['city'],
        customer_data.get('address', ''), customer_data.get('phone', ''),
        customer_data.get('whatsapp', ''), customer_data.get('email', ''),
        customer_data.get('buyer_name', ''), customer_data.get('buyer_phone', ''),
        customer_data.get('trade_type', ''), customer_data.get('assigned_salesperson_id'),
        customer_data.get('payment_terms', 'Net 30'),
        customer_data.get('credit_limit', random.randint(10000, 200000)),
        customer_data.get('currency', 'AED'),
        customer_data.get('default_discount', 0),
        customer_data.get('status', 'Active'),
        customer_data.get('priority', 'Medium'),
        customer_data.get('total_orders', 0),
        customer_data.get('total_revenue', 0),
        customer_data.get('outstanding_balance', 0),
        customer_data.get('last_purchase_date'),
        customer_data.get('company_id', 1),
        1,
        customer_data.get('created_at', datetime.now().strftime('%Y-%m-%d'))
    ))
    conn.commit()
    return cursor.lastrowid


def create_part(conn, part_number, name, brand, category, cost, sell_price, stock_qty, warehouse_id):
    """Create a part/item."""
    existing = conn.execute("SELECT id FROM parts WHERE part_number = ?", (part_number,)).fetchone()
    if existing:
        return existing['id']
    
    cursor = conn.execute("""
        INSERT INTO parts (part_number, name, description, category, brand, 
                          standard_cost, standard_price, quantity, warehouse_id, 
                          is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
    """, (part_number, name, f"{name} - {brand}", category, brand, cost, sell_price, stock_qty, warehouse_id))
    
    # Also add to inventory
    conn.execute("""
        INSERT INTO inventory (part_number, warehouse_id, quantity, reserved_quantity, updated_at)
        VALUES (?, ?, ?, 0, CURRENT_TIMESTAMP)
    """, (part_number, warehouse_id, stock_qty))
    
    conn.commit()
    return cursor.lastrowid


def create_inquiry(conn, inquiry_data):
    """Create an inquiry with lines."""
    year = datetime.now().year
    last_inq = conn.execute("SELECT inquiry_number FROM sales_inquiries WHERE inquiry_number LIKE ? ORDER BY id DESC LIMIT 1",
                           (f'INQ-{year}%',)).fetchone()
    
    if last_inq:
        last_num = int(last_inq['inquiry_number'].split('-')[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    
    inquiry_number = f"INQ-{year}-{new_num:05d}"
    
    cursor = conn.execute("""
        INSERT INTO sales_inquiries (
            inquiry_number, inquiry_date, inquiry_time, customer_id, customer_name,
            customer_type, market, country, city, inquiry_source, priority,
            assigned_salesperson_id, status, urgency, immediate_delivery,
            specific_brand_required, target_customer_price, notes, company_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        inquiry_number,
        inquiry_data['inquiry_date'],
        inquiry_data.get('inquiry_time', '09:00'),
        inquiry_data.get('customer_id'),
        inquiry_data.get('customer_name'),
        inquiry_data.get('customer_type'),
        inquiry_data.get('market', 'Local'),
        inquiry_data.get('country'),
        inquiry_data.get('city'),
        inquiry_data['inquiry_source'],
        inquiry_data.get('priority', 'Medium'),
        inquiry_data.get('assigned_salesperson_id'),
        inquiry_data.get('status', 'New'),
        inquiry_data.get('urgency'),
        inquiry_data.get('immediate_delivery', 0),
        inquiry_data.get('specific_brand_required', 0),
        inquiry_data.get('target_customer_price'),
        inquiry_data.get('notes'),
        inquiry_data.get('company_id', 1)
    ))
    inquiry_id = cursor.lastrowid
    
    # Add lines
    for line in inquiry_data.get('lines', []):
        conn.execute("""
            INSERT INTO sales_inquiry_lines (
                inquiry_id, part_number, brand, description, requested_quantity, target_price, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (inquiry_id, line['part_number'], line['brand'], line['description'], 
              line['quantity'], line.get('target_price'), line.get('notes')))
    
    conn.commit()
    return inquiry_id


def create_quotation(conn, quotation_data):
    """Create a quotation with lines."""
    year = datetime.now().year
    last_quo = conn.execute("SELECT quotation_number FROM sales_quotations WHERE quotation_number LIKE ? ORDER BY id DESC LIMIT 1",
                            (f'QUO-{year}%',)).fetchone()
    
    if last_quo:
        last_num = int(last_quo['quotation_number'].split('-')[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    
    quotation_number = f"QUO-{year}-{new_num:05d}"
    
    subtotal = sum(line['final_price'] * line['quantity'] for line in quotation_data.get('lines', []))
    discount_amount = subtotal * quotation_data.get('discount_percent', 0) / 100
    taxable_amount = subtotal - discount_amount
    tax_amount = taxable_amount * quotation_data.get('tax_percent', 5) / 100
    total_amount = taxable_amount + tax_amount
    
    cursor = conn.execute("""
        INSERT INTO sales_quotations (
            quotation_number, quotation_date, valid_until, customer_id, customer_name,
            customer_type, market, assigned_salesperson_id, currency,
            payment_terms, delivery_terms, delivery_location,
            subtotal, discount_percent, discount_amount, tax_percent, tax_amount,
            total_amount, status, source, supply_lead_time, stock_status, notes, company_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        quotation_number,
        quotation_data['quotation_date'],
        quotation_data.get('valid_until'),
        quotation_data.get('customer_id'),
        quotation_data.get('customer_name'),
        quotation_data.get('customer_type'),
        quotation_data.get('market', 'Local'),
        quotation_data.get('assigned_salesperson_id'),
        quotation_data.get('currency', 'AED'),
        quotation_data.get('payment_terms'),
        quotation_data.get('delivery_terms'),
        quotation_data.get('delivery_location'),
        subtotal,
        quotation_data.get('discount_percent', 0),
        discount_amount,
        quotation_data.get('tax_percent', 5),
        tax_amount,
        total_amount,
        quotation_data.get('status', 'Draft'),
        quotation_data.get('source'),
        quotation_data.get('supply_lead_time'),
        quotation_data.get('stock_status'),
        quotation_data.get('notes'),
        quotation_data.get('company_id', 1)
    ))
    quotation_id = cursor.lastrowid
    
    # Add lines
    for i, line in enumerate(quotation_data.get('lines', []), 1):
        conn.execute("""
            INSERT INTO sales_quotation_lines (
                quotation_id, line_number, part_number, brand, description,
                requested_quantity, unit_price, discount_percent, discount_amount,
                final_price, supply_lead_time, stock_status, origin
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (quotation_id, i, line['part_number'], line['brand'], line['description'],
              line['quantity'], line['unit_price'], line.get('discount_percent', 0),
              line.get('discount_amount', 0), line['final_price'],
              line.get('supply_lead_time'), line.get('stock_status'), line.get('origin')))
    
    conn.commit()
    return quotation_id


def create_proforma(conn, proforma_data):
    """Create a pro forma invoice with lines."""
    year = datetime.now().year
    last_pfi = conn.execute("SELECT proforma_number FROM sales_proforma_invoices WHERE proforma_number LIKE ? ORDER BY id DESC LIMIT 1",
                           (f'PFI-{year}%',)).fetchone()
    
    if last_pfi:
        last_num = int(last_pfi['proforma_number'].split('-')[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    
    proforma_number = f"PFI-{year}-{new_num:05d}"
    
    subtotal = sum(line['final_price'] * line['quantity'] for line in proforma_data.get('lines', []))
    discount_amount = subtotal * proforma_data.get('discount_percent', 0) / 100
    taxable_amount = subtotal - discount_amount
    tax_amount = taxable_amount * proforma_data.get('tax_percent', 5) / 100
    total_amount = taxable_amount + tax_amount
    
    cursor = conn.execute("""
        INSERT INTO sales_proforma_invoices (
            proforma_number, proforma_date, valid_until, customer_id, customer_name,
            customer_type, market, assigned_salesperson_id, currency,
            payment_terms, delivery_terms, incoterm,
            subtotal, discount_percent, discount_amount, tax_percent, tax_amount,
            total_amount, advance_payment_percent, advance_payment_required,
            status, notes, company_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        proforma_number,
        proforma_data['proforma_date'],
        proforma_data.get('valid_until'),
        proforma_data.get('customer_id'),
        proforma_data.get('customer_name'),
        proforma_data.get('customer_type'),
        proforma_data.get('market', 'Local'),
        proforma_data.get('assigned_salesperson_id'),
        proforma_data.get('currency', 'AED'),
        proforma_data.get('payment_terms'),
        proforma_data.get('delivery_terms'),
        proforma_data.get('incoterm'),
        subtotal,
        proforma_data.get('discount_percent', 0),
        discount_amount,
        proforma_data.get('tax_percent', 5),
        tax_amount,
        total_amount,
        proforma_data.get('advance_payment_percent', 0),
        total_amount * proforma_data.get('advance_payment_percent', 0) / 100,
        proforma_data.get('status', 'Draft'),
        proforma_data.get('notes'),
        proforma_data.get('company_id', 1)
    ))
    proforma_id = cursor.lastrowid
    
    # Add lines
    for i, line in enumerate(proforma_data.get('lines', []), 1):
        conn.execute("""
            INSERT INTO sales_proforma_lines (
                proforma_id, line_number, part_number, brand, description,
                requested_quantity, unit_price, discount_percent, discount_amount,
                final_price, tax_percent, tax_amount, line_total,
                supply_lead_time, stock_status, origin
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (proforma_id, i, line['part_number'], line['brand'], line['description'],
              line['quantity'], line['unit_price'], line.get('discount_percent', 0),
              line.get('discount_amount', 0), line['final_price'],
              line.get('tax_percent', 5), line.get('tax_amount', 0), line['final_price'] * line['quantity'],
              line.get('supply_lead_time'), line.get('stock_status'), line.get('origin')))
    
    conn.commit()
    return proforma_id


def create_confirmation(conn, confirmation_data):
    """Create a sales confirmation."""
    year = datetime.now().year
    last_sco = conn.execute("SELECT confirmation_number FROM sales_confirmations WHERE confirmation_number LIKE ? ORDER BY id DESC LIMIT 1",
                           (f'SCO-{year}%',)).fetchone()
    
    if last_sco:
        last_num = int(last_sco['confirmation_number'].split('-')[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    
    confirmation_number = f"SCO-{year}-{new_num:05d}"
    
    subtotal = sum(line['final_price'] * line['quantity'] for line in confirmation_data.get('lines', []))
    discount_amount = subtotal * confirmation_data.get('discount_percent', 0) / 100
    taxable_amount = subtotal - discount_amount
    tax_amount = taxable_amount * confirmation_data.get('tax_percent', 5) / 100
    total_amount = taxable_amount + tax_amount
    
    cursor = conn.execute("""
        INSERT INTO sales_confirmations (
            confirmation_number, confirmation_date,
            reference_quotation_id, reference_proforma_id,
            customer_id, customer_name, customer_type, market,
            assigned_salesperson_id, currency,
            payment_terms, delivery_terms, incoterm, lead_time_days,
            subtotal, discount_percent, discount_amount, tax_percent, tax_amount,
            total_amount, customer_acceptance_status, status, notes, company_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        confirmation_number,
        confirmation_data['confirmation_date'],
        confirmation_data.get('reference_quotation_id'),
        confirmation_data.get('reference_proforma_id'),
        confirmation_data.get('customer_id'),
        confirmation_data.get('customer_name'),
        confirmation_data.get('customer_type'),
        confirmation_data.get('market', 'Local'),
        confirmation_data.get('assigned_salesperson_id'),
        confirmation_data.get('currency', 'AED'),
        confirmation_data.get('payment_terms'),
        confirmation_data.get('delivery_terms'),
        confirmation_data.get('incoterm'),
        confirmation_data.get('lead_time_days'),
        subtotal,
        confirmation_data.get('discount_percent', 0),
        discount_amount,
        confirmation_data.get('tax_percent', 5),
        tax_amount,
        total_amount,
        confirmation_data.get('customer_acceptance_status', 'Pending'),
        confirmation_data.get('status', 'Draft'),
        confirmation_data.get('notes'),
        confirmation_data.get('company_id', 1)
    ))
    confirmation_id = cursor.lastrowid
    
    # Add lines
    for i, line in enumerate(confirmation_data.get('lines', []), 1):
        conn.execute("""
            INSERT INTO sales_confirmation_lines (
                confirmation_id, line_number, part_number, brand, description,
                confirmed_quantity, unit_price, discount_percent, discount_amount,
                final_price, tax_percent, tax_amount, line_total, delivery_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (confirmation_id, i, line['part_number'], line['brand'], line['description'],
              line['quantity'], line['unit_price'], line.get('discount_percent', 0),
              line.get('discount_amount', 0), line['final_price'],
              line.get('tax_percent', 5), line.get('tax_amount', 0), line['final_price'] * line['quantity'],
              line.get('delivery_date')))
    
    conn.commit()
    return confirmation_id


def create_order(conn, order_data):
    """Create a sales order."""
    year = datetime.now().year
    last_ord = conn.execute("SELECT order_number FROM sales_orders WHERE order_number LIKE ? ORDER BY id DESC LIMIT 1",
                           (f'ORD-{year}%',)).fetchone()
    
    if last_ord:
        last_num = int(last_ord['order_number'].split('-')[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    
    order_number = f"ORD-{year}-{new_num:05d}"
    
    subtotal = sum(line['final_price'] * line['quantity'] for line in order_data.get('lines', []))
    discount_amount = subtotal * order_data.get('discount_percent', 0) / 100
    taxable_amount = subtotal - discount_amount
    tax_amount = taxable_amount * order_data.get('tax_percent', 5) / 100
    total_amount = taxable_amount + tax_amount
    
    cursor = conn.execute("""
        INSERT INTO sales_orders (
            order_number, order_date,
            customer_id, customer_name, customer_type, market,
            is_export, export_country, incoterm, transport_mode,
            quotation_id, assigned_salesperson_id, currency,
            payment_terms, delivery_terms, delivery_address, shipment_type,
            subtotal, discount_percent, discount_amount, tax_percent, tax_amount,
            total_amount, status, priority, promised_delivery_date, notes, company_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        order_number,
        order_data['order_date'],
        order_data.get('customer_id'),
        order_data.get('customer_name'),
        order_data.get('customer_type'),
        order_data.get('market', 'Local'),
        order_data.get('is_export', 0),
        order_data.get('export_country'),
        order_data.get('incoterm'),
        order_data.get('transport_mode'),
        order_data.get('quotation_id'),
        order_data.get('assigned_salesperson_id'),
        order_data.get('currency', 'AED'),
        order_data.get('payment_terms'),
        order_data.get('delivery_terms'),
        order_data.get('delivery_address'),
        order_data.get('shipment_type'),
        subtotal,
        order_data.get('discount_percent', 0),
        discount_amount,
        order_data.get('tax_percent', 5),
        tax_amount,
        total_amount,
        order_data.get('status', 'Registered'),
        order_data.get('priority', 'Medium'),
        order_data.get('promised_delivery_date'),
        order_data.get('notes'),
        order_data.get('company_id', 1)
    ))
    order_id = cursor.lastrowid
    
    # Add lines
    for i, line in enumerate(order_data.get('lines', []), 1):
        conn.execute("""
            INSERT INTO sales_order_lines (
                order_id, line_number, part_number, brand, description,
                ordered_quantity, available_quantity, shortage_quantity,
                unit_price, discount_percent, discount_amount, final_price,
                tax_percent, tax_amount, line_total
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (order_id, i, line['part_number'], line['brand'], line['description'],
              line['quantity'], line.get('available_quantity', line['quantity']),
              line.get('shortage_quantity', 0),
              line['unit_price'], line.get('discount_percent', 0),
              line.get('discount_amount', 0), line['final_price'],
              line.get('tax_percent', 5), line.get('tax_amount', 0), line['final_price'] * line['quantity']))
    
    conn.commit()
    return order_id


def create_invoice(conn, invoice_data):
    """Create a sales invoice."""
    year = datetime.now().year
    last_inv = conn.execute("SELECT invoice_number FROM sales_invoices WHERE invoice_number LIKE ? ORDER BY id DESC LIMIT 1",
                           (f'INV-{year}%',)).fetchone()
    
    if last_inv:
        last_num = int(last_inv['invoice_number'].split('-')[-1])
        new_num = last_num + 1
    else:
        new_num = 1
    
    invoice_number = f"INV-{year}-{new_num:05d}"
    
    subtotal = sum(line['final_price'] * line['quantity'] for line in invoice_data.get('lines', []))
    discount_amount = subtotal * invoice_data.get('discount_percent', 0) / 100
    taxable_amount = subtotal - discount_amount
    tax_amount = taxable_amount * invoice_data.get('tax_percent', 5) / 100
    total_amount = taxable_amount + tax_amount
    
    cursor = conn.execute("""
        INSERT INTO sales_invoices (
            invoice_number, invoice_date, due_date,
            order_id, delivery_id,
            customer_id, customer_name, customer_type, market,
            billing_address, assigned_salesperson_id, currency,
            payment_terms, incoterm,
            subtotal, discount_percent, discount_amount, tax_percent, tax_amount,
            total_amount, amount_paid, amount_due,
            payment_status, status, notes, company_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        invoice_number,
        invoice_data['invoice_date'],
        invoice_data.get('due_date'),
        invoice_data.get('order_id'),
        invoice_data.get('delivery_id'),
        invoice_data.get('customer_id'),
        invoice_data.get('customer_name'),
        invoice_data.get('customer_type'),
        invoice_data.get('market', 'Local'),
        invoice_data.get('billing_address'),
        invoice_data.get('assigned_salesperson_id'),
        invoice_data.get('currency', 'AED'),
        invoice_data.get('payment_terms'),
        invoice_data.get('incoterm'),
        subtotal,
        invoice_data.get('discount_percent', 0),
        discount_amount,
        invoice_data.get('tax_percent', 5),
        tax_amount,
        total_amount,
        invoice_data.get('amount_paid', 0),
        total_amount - invoice_data.get('amount_paid', 0),
        invoice_data.get('payment_status', 'Unpaid'),
        invoice_data.get('status', 'Draft'),
        invoice_data.get('notes'),
        invoice_data.get('company_id', 1)
    ))
    invoice_id = cursor.lastrowid
    
    # Add lines
    for i, line in enumerate(invoice_data.get('lines', []), 1):
        conn.execute("""
            INSERT INTO sales_invoice_lines (
                invoice_id, line_number, part_number, brand, description,
                quantity, unit_price, discount_percent, discount_amount,
                final_price, tax_percent, tax_amount, line_total
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (invoice_id, i, line['part_number'], line['brand'], line['description'],
              line['quantity'], line['unit_price'], line.get('discount_percent', 0),
              line.get('discount_amount', 0), line['final_price'],
              line.get('tax_percent', 5), line.get('tax_amount', 0), line['final_price'] * line['quantity']))
    
    conn.commit()
    return invoice_id


def create_activity(conn, activity_data):
    """Create a sales activity."""
    cursor = conn.execute("""
        INSERT INTO sales_activities (
            activity_type, activity_date, activity_time, customer_id, owner_id,
            subject, result, next_action, next_follow_up_date, status, notes,
            reference_type, reference_id, company_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        activity_data['activity_type'],
        activity_data['activity_date'],
        activity_data.get('activity_time', '09:00'),
        activity_data.get('customer_id'),
        activity_data['owner_id'],
        activity_data['subject'],
        activity_data.get('result'),
        activity_data.get('next_action'),
        activity_data.get('next_follow_up_date'),
        activity_data.get('status', 'Completed'),
        activity_data.get('notes'),
        activity_data.get('reference_type'),
        activity_data.get('reference_id'),
        activity_data.get('company_id', 1)
    ))
    conn.commit()
    return cursor.lastrowid


# =============================================================================
# MAIN SEED FUNCTION
# =============================================================================

def seed_database():
    """Execute the complete seed process."""
    print("=" * 60)
    print("SALES MANAGEMENT SUITE - COMPREHENSIVE SEED DATA")
    print("=" * 60)
    
    conn = get_connection()
    
    try:
        # Check if already seeded
        existing_customers = conn.execute("SELECT COUNT(*) as cnt FROM sales_customers").fetchone()
        if existing_customers and existing_customers['cnt'] > 50:
            print(f"\nDatabase already appears to have {existing_customers['cnt']} customers.")
            response = input("Do you want to continue seeding anyway? (y/n): ")
            if response.lower() != 'y':
                print("Seeding cancelled.")
                return
        
        print("\n[1/12] Creating companies...")
        company_ids = {}
        for company in COMPANIES:
            cid = get_or_create_company(conn, company['code'], company['name'], company['type'], company['country'], company['city'])
            company_ids[company['code']] = cid
            print(f"  - {company['name']} (ID: {cid})")
        
        print("\n[2/12] Creating warehouses...")
        warehouse_ids = {}
        for wh in WAREHOUSES:
            wid = get_or_create_warehouse(conn, wh['code'], wh['name'], company_ids.get(wh['company'], 1), wh['type'])
            warehouse_ids[wh['code']] = wid
            print(f"  - {wh['name']} (ID: {wid})")
        
        print("\n[3/12] Creating sales users...")
        user_ids = {}
        for user in SALES_USERS:
            uid = get_or_create_user(conn, user['username'], user['full_name'], user['role'], user['email'])
            user_ids[user['username']] = uid
            print(f"  - {user['full_name']} ({user['role']}) - ID: {uid}")
        
        print("\n[4/12] Creating parts/items...")
        parts_created = 0
        all_parts = []
        
        # Generate 300 parts across all brands and categories
        for brand in BRANDS[:10]:  # First 10 brands
            for category, items in ITEM_CATEGORIES.items():
                for item in items[:4]:  # First 4 items per category
                    part_number = generate_part_number(brand)
                    description = f"{brand.split()[0]} {item}"
                    cost = round(random.uniform(10, 500), 2)
                    sell_price = round(cost * random.uniform(1.3, 2.0), 2)
                    stock_qty = random.randint(0, 100)
                    
                    create_part(conn, part_number, description, brand, category, cost, sell_price, stock_qty, warehouse_ids['SDAD_RAK_MAIN'])
                    all_parts.append({
                        'part_number': part_number,
                        'brand': brand,
                        'description': description,
                        'category': category,
                        'unit_price': sell_price
                    })
                    parts_created += 1
        
        print(f"  - Created {parts_created} parts")
        
        print("\n[5/12] Creating customers...")
        customers_created = 0
        customer_ids = []
        
        # Create 80+ customers
        for i, name in enumerate(CUSTOMER_NAMES[:85]):
            customer_code = f"CUST-{i+1:05d}"
            country = random.choice(COUNTRIES)
            city = random.choice(CITIES.get(country, ['N/A']))
            customer_type = random.choice(CUSTOMER_TYPES)
            market = 'Export' if country != 'UAE' else random.choice(['Local', 'Export'])
            salesperson_username = random.choice(list(user_ids.keys()))
            last_purchase = (datetime.now() - timedelta(days=random.randint(1, 180))).strftime('%Y-%m-%d')
            
            customer_id = get_or_create_customer(conn, {
                'customer_code': customer_code,
                'name': name,
                'trade_name': f"{name} Trading",
                'customer_type': customer_type,
                'market': market,
                'country': country,
                'city': city,
                'address': f"{random.randint(1, 999)} {random.choice(['Main', 'Industrial', 'Commercial'])} Street, {city}",
                'phone': f"+971-{random.randint(50, 59)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                'whatsapp': f"+971-{random.randint(50, 59)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                'email': f"info@{name.lower().replace(' ', '')}.com",
                'buyer_name': random.choice(['Ahmed', 'Mohammed', 'Ali', 'Fatima', 'Sara', 'Omar', 'Layla']) + ' ' + 
                             random.choice(['Khan', 'Ali', 'Hassan', 'Ahmed', 'Malik', 'Nasser']),
                'buyer_phone': f"+971-{random.randint(50, 59)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
                'trade_type': random.choice(['Auto Parts', 'Workshop', 'Fleet', 'Trading', 'Retail']),
                'assigned_salesperson_id': user_ids.get(salesperson_username),
                'payment_terms': random.choice(PAYMENT_TERMS),
                'credit_limit': random.randint(10000, 200000),
                'currency': 'AED' if country == 'UAE' else random.choice(['USD', 'EUR']),
                'default_discount': random.choice([0, 0, 5, 10]),
                'status': 'Active' if random.random() > 0.1 else 'Inactive',
                'priority': random.choice(['Low', 'Medium', 'Medium', 'High']),
                'total_orders': random.randint(0, 100),
                'total_revenue': random.randint(0, 500000),
                'outstanding_balance': random.randint(0, 50000),
                'last_purchase_date': last_purchase,
                'company_id': random.choice([1, 2, 3]),
            })
            customer_ids.append(customer_id)
            customers_created += 1
        
        print(f"  - Created {customers_created} customers")
        
        print("\n[6/12] Creating inquiries (80+)...")
        inquiries_created = 0
        
        # Generate 80 inquiries
        for i in range(80):
            days_ago = random.randint(1, 180)
            inquiry_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            customer_id = random.choice(customer_ids) if random.random() > 0.2 else None
            customer = conn.execute("SELECT name, customer_type, country, city FROM sales_customers WHERE id = ?", 
                                   (customer_id,)).fetchone() if customer_id else None
            
            # Generate 1-5 line items
            num_lines = random.randint(1, 5)
            lines = []
            for _ in range(num_lines):
                part = random.choice(all_parts)
                lines.append({
                    'part_number': part['part_number'],
                    'brand': part['brand'],
                    'description': part['description'],
                    'quantity': random.randint(1, 50),
                    'target_price': round(part['unit_price'] * random.uniform(0.9, 1.1), 2),
                    'notes': random.choice(['', 'Urgent', 'Quality matters', 'Competitive quote needed'])
                })
            
            status = random.choice(['New', 'Under Review', 'Need Pricing', 'Responded', 'In Negotiation', 'Converted to Quotation', 'Closed'])
            
            inquiry_id = create_inquiry(conn, {
                'inquiry_date': inquiry_date,
                'customer_id': customer_id,
                'customer_name': customer['name'] if customer else random.choice(CUSTOMER_NAMES[:30]),
                'customer_type': customer['customer_type'] if customer else random.choice(CUSTOMER_TYPES),
                'market': 'Export' if customer and customer['country'] != 'UAE' else 'Local',
                'country': customer['country'] if customer else 'UAE',
                'city': customer['city'] if customer else 'Dubai',
                'inquiry_source': random.choice(SALES_CHANNELS),
                'priority': random.choice(['Low', 'Medium', 'Medium', 'High']),
                'assigned_salesperson_id': random.choice(list(user_ids.values())),
                'status': status,
                'urgency': random.choice(['Normal', 'Urgent', 'Very Urgent']),
                'immediate_delivery': 1 if random.random() > 0.8 else 0,
                'specific_brand_required': 1 if random.random() > 0.6 else 0,
                'target_customer_price': random.randint(1000, 50000),
                'notes': random.choice(['', 'Regular customer', 'New inquiry', 'Follow up needed']),
                'lines': lines,
                'company_id': random.choice([1, 2, 3])
            })
            inquiries_created += 1
        
        print(f"  - Created {inquiries_created} inquiries")
        
        print("\n[7/12] Creating quotations (60+)...")
        quotations_created = 0
        
        # Generate 60 quotations
        for i in range(60):
            days_ago = random.randint(1, 150)
            quotation_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            valid_until = (datetime.strptime(quotation_date, '%Y-%m-%d') + timedelta(days=30)).strftime('%Y-%m-%d')
            
            customer_id = random.choice(customer_ids)
            customer = conn.execute("SELECT name, customer_type FROM sales_customers WHERE id = ?", (customer_id,)).fetchone()
            
            num_lines = random.randint(2, 8)
            lines = []
            for _ in range(num_lines):
                part = random.choice(all_parts)
                quantity = random.randint(1, 20)
                unit_price = round(part['unit_price'] * random.uniform(0.95, 1.1), 2)
                discount_percent = random.choice([0, 0, 5, 10])
                final_price = round(unit_price * (1 - discount_percent/100), 2)
                lines.append({
                    'part_number': part['part_number'],
                    'brand': part['brand'],
                    'description': part['description'],
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'discount_percent': discount_percent,
                    'final_price': final_price,
                    'supply_lead_time': f"{random.randint(1,14)} days",
                    'stock_status': random.choice(['In Stock', 'In Stock', 'In Stock', 'On Order', 'Limited Stock']),
                    'origin': random.choice(['Local', 'Imported', 'UAE', 'Japan', 'Europe'])
                })
            
            status = random.choice(['Draft', 'Sent', 'Sent', 'Viewed', 'In Negotiation', 'Approved', 'Converted to Order', 'Expired'])
            
            quotation_id = create_quotation(conn, {
                'quotation_date': quotation_date,
                'valid_until': valid_until,
                'customer_id': customer_id,
                'customer_name': customer['name'] if customer else 'Unknown',
                'customer_type': customer['customer_type'] if customer else 'Retail',
                'market': 'Local' if random.random() > 0.3 else 'Export',
                'assigned_salesperson_id': random.choice(list(user_ids.values())),
                'currency': random.choice(['AED', 'USD', 'EUR']),
                'payment_terms': random.choice(PAYMENT_TERMS),
                'delivery_terms': random.choice(['EXW', 'FOB', 'CIF', 'DAP']),
                'delivery_location': random.choice(['Dubai', 'Abu Dhabi', 'Sharjah', 'Doha', 'Riyadh']),
                'discount_percent': random.choice([0, 0, 5]),
                'tax_percent': 5,
                'status': status,
                'source': random.choice(SALES_CHANNELS),
                'supply_lead_time': '7-14 days',
                'stock_status': 'Mixed',
                'notes': random.choice(['', 'Competitive pricing', 'Volume discount applicable', ' Rush order']),
                'lines': lines,
                'company_id': random.choice([1, 2, 3])
            })
            quotations_created += 1
        
        print(f"  - Created {quotations_created} quotations")
        
        print("\n[8/12] Creating pro forma invoices (25+)...")
        proformas_created = 0
        
        for i in range(25):
            days_ago = random.randint(1, 120)
            proforma_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            valid_until = (datetime.strptime(proforma_date, '%Y-%m-%d') + timedelta(days=14)).strftime('%Y-%m-%d')
            
            customer_id = random.choice(customer_ids)
            customer = conn.execute("SELECT name, customer_type FROM sales_customers WHERE id = ?", (customer_id,)).fetchone()
            
            num_lines = random.randint(3, 10)
            lines = []
            for _ in range(num_lines):
                part = random.choice(all_parts)
                quantity = random.randint(2, 30)
                unit_price = round(part['unit_price'] * random.uniform(0.98, 1.05), 2)
                discount_percent = random.choice([0, 5, 10, 15])
                final_price = round(unit_price * (1 - discount_percent/100), 2)
                lines.append({
                    'part_number': part['part_number'],
                    'brand': part['brand'],
                    'description': part['description'],
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'discount_percent': discount_percent,
                    'final_price': final_price,
                    'tax_percent': 5,
                    'supply_lead_time': f"{random.randint(7,21)} days",
                    'stock_status': random.choice(['In Stock', 'On Order', 'Pre-order']),
                    'origin': random.choice(['UAE', 'Japan', 'Korea', 'Europe'])
                })
            
            status = random.choice(['Draft', 'Issued', 'Issued', 'Viewed', 'Under Review', 'Accepted', 'Converted'])
            
            create_proforma(conn, {
                'proforma_date': proforma_date,
                'valid_until': valid_until,
                'customer_id': customer_id,
                'customer_name': customer['name'] if customer else 'Unknown',
                'customer_type': customer['customer_type'] if customer else 'Wholesale',
                'market': 'Local' if random.random() > 0.4 else 'Export',
                'assigned_salesperson_id': random.choice(list(user_ids.values())),
                'currency': random.choice(['AED', 'USD', 'EUR']),
                'payment_terms': random.choice(['Net 30', 'Net 45', 'Cash', 'Letter of Credit']),
                'delivery_terms': random.choice(['DAP', 'DDP', 'FOB', 'CIF']),
                'incoterm': random.choice(['DAP', 'DDP', 'FOB', 'CIF']),
                'discount_percent': random.choice([0, 5, 10]),
                'tax_percent': 5,
                'advance_payment_percent': random.choice([0, 0, 30, 50]),
                'status': status,
                'notes': random.choice(['', 'Export order', 'Requires LC', '50% advance required']),
                'lines': lines,
                'company_id': random.choice([1, 2, 3])
            })
            proformas_created += 1
        
        print(f"  - Created {proformas_created} pro forma invoices")
        
        print("\n[9/12] Creating sales confirmations (20+)...")
        confirmations_created = 0
        
        for i in range(20):
            days_ago = random.randint(1, 100)
            confirmation_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            
            customer_id = random.choice(customer_ids)
            customer = conn.execute("SELECT name, customer_type FROM sales_customers WHERE id = ?", (customer_id,)).fetchone()
            
            num_lines = random.randint(3, 8)
            lines = []
            for _ in range(num_lines):
                part = random.choice(all_parts)
                quantity = random.randint(5, 25)
                unit_price = round(part['unit_price'] * random.uniform(1.0, 1.1), 2)
                discount_percent = random.choice([0, 5, 10])
                final_price = round(unit_price * (1 - discount_percent/100), 2)
                lines.append({
                    'part_number': part['part_number'],
                    'brand': part['brand'],
                    'description': part['description'],
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'discount_percent': discount_percent,
                    'final_price': final_price,
                    'tax_percent': 5,
                    'delivery_date': (datetime.strptime(confirmation_date, '%Y-%m-%d') + timedelta(days=14)).strftime('%Y-%m-%d')
                })
            
            status = random.choice(['Draft', 'Sent', 'Confirmed by Customer', 'Confirmed by Customer', 'Revised', 'Converted to Order'])
            
            create_confirmation(conn, {
                'confirmation_date': confirmation_date,
                'customer_id': customer_id,
                'customer_name': customer['name'] if customer else 'Unknown',
                'customer_type': customer['customer_type'] if customer else 'Key Account',
                'market': 'Local' if random.random() > 0.3 else 'Export',
                'assigned_salesperson_id': random.choice(list(user_ids.values())),
                'currency': random.choice(['AED', 'USD', 'EUR']),
                'payment_terms': random.choice(['Net 30', 'Net 45', 'Net 60']),
                'delivery_terms': random.choice(['DAP', 'DDP', 'FOB', 'CIF']),
                'incoterm': random.choice(['DAP', 'DDP', 'FOB', 'CIF']),
                'lead_time_days': random.randint(7, 21),
                'discount_percent': random.choice([0, 5, 10]),
                'tax_percent': 5,
                'customer_acceptance_status': 'Confirmed' if 'Confirmed' in status else 'Pending',
                'customer_acceptance_date': confirmation_date if 'Confirmed' in status else None,
                'status': status,
                'notes': random.choice(['', 'Customer confirmed via email', 'PO received', 'Terms agreed']),
                'lines': lines,
                'company_id': random.choice([1, 2, 3])
            })
            confirmations_created += 1
        
        print(f"  - Created {confirmations_created} sales confirmations")
        
        print("\n[10/12] Creating sales orders (30+)...")
        orders_created = 0
        
        for i in range(30):
            days_ago = random.randint(1, 90)
            order_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            promised_date = (datetime.strptime(order_date, '%Y-%m-%d') + timedelta(days=random.randint(7, 30))).strftime('%Y-%m-%d')
            
            customer_id = random.choice(customer_ids)
            customer = conn.execute("SELECT name, customer_type FROM sales_customers WHERE id = ?", (customer_id,)).fetchone()
            
            num_lines = random.randint(2, 10)
            lines = []
            for _ in range(num_lines):
                part = random.choice(all_parts)
                quantity = random.randint(3, 30)
                unit_price = round(part['unit_price'] * random.uniform(1.0, 1.15), 2)
                discount_percent = random.choice([0, 5, 10])
                final_price = round(unit_price * (1 - discount_percent/100), 2)
                lines.append({
                    'part_number': part['part_number'],
                    'brand': part['brand'],
                    'description': part['description'],
                    'quantity': quantity,
                    'available_quantity': quantity if random.random() > 0.2 else quantity - random.randint(1, 5),
                    'shortage_quantity': 0 if random.random() > 0.2 else random.randint(1, 5),
                    'unit_price': unit_price,
                    'discount_percent': discount_percent,
                    'final_price': final_price,
                    'tax_percent': 5
                })
            
            status = random.choice(['Registered', 'Pending Approval', 'Pending Reservation', 'In Preparation', 
                                   'Ready for Delivery', 'Partially Delivered', 'Fully Delivered', 'Delayed'])
            
            create_order(conn, {
                'order_date': order_date,
                'customer_id': customer_id,
                'customer_name': customer['name'] if customer else 'Unknown',
                'customer_type': customer['customer_type'] if customer else 'Wholesale',
                'market': 'Local' if random.random() > 0.35 else 'Export',
                'is_export': 1 if random.random() > 0.65 else 0,
                'export_country': random.choice(COUNTRIES) if random.random() > 0.65 else None,
                'incoterm': random.choice(['EXW', 'FOB', 'CIF', 'DAP', 'DDP']) if random.random() > 0.5 else None,
                'transport_mode': random.choice(['Sea', 'Air', 'Land']) if random.random() > 0.6 else None,
                'quotation_id': None,
                'assigned_salesperson_id': random.choice(list(user_ids.values())),
                'currency': random.choice(['AED', 'USD', 'EUR']),
                'payment_terms': random.choice(['Net 30', 'Net 45', 'Net 60', 'Cash']),
                'delivery_terms': random.choice(['EXW', 'FOB', 'DAP', 'DDP']),
                'delivery_address': f"{random.randint(1,999)} Main Street, {random.choice(['Dubai', 'Abu Dhabi', 'Sharjah'])}",
                'shipment_type': random.choice(['Full Container', 'LCL', 'Air Freight', 'Local Delivery']),
                'discount_percent': random.choice([0, 5]),
                'tax_percent': 5,
                'status': status,
                'priority': random.choice(['Low', 'Medium', 'Medium', 'High', 'Urgent']),
                'promised_delivery_date': promised_date,
                'notes': random.choice(['', 'Handle with care', 'Call before delivery', 'Fragile items']),
                'lines': lines,
                'company_id': random.choice([1, 2, 3])
            })
            orders_created += 1
        
        print(f"  - Created {orders_created} sales orders")
        
        print("\n[11/12] Creating sales invoices (15+)...")
        invoices_created = 0
        
        for i in range(15):
            days_ago = random.randint(1, 60)
            invoice_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            due_date = (datetime.strptime(invoice_date, '%Y-%m-%d') + timedelta(days=30)).strftime('%Y-%m-%d')
            
            customer_id = random.choice(customer_ids)
            customer = conn.execute("SELECT name, customer_type FROM sales_customers WHERE id = ?", (customer_id,)).fetchone()
            
            num_lines = random.randint(2, 8)
            lines = []
            for _ in range(num_lines):
                part = random.choice(all_parts)
                quantity = random.randint(2, 20)
                unit_price = round(part['unit_price'] * random.uniform(1.1, 1.3), 2)
                discount_percent = random.choice([0, 5])
                final_price = round(unit_price * (1 - discount_percent/100), 2)
                lines.append({
                    'part_number': part['part_number'],
                    'brand': part['brand'],
                    'description': part['description'],
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'discount_percent': discount_percent,
                    'final_price': final_price,
                    'tax_percent': 5
                })
            
            total = sum(line['final_price'] * line['quantity'] for line in lines)
            amount_paid = 0 if random.random() > 0.5 else total * random.uniform(0, 1)
            
            create_invoice(conn, {
                'invoice_date': invoice_date,
                'due_date': due_date,
                'order_id': None,
                'delivery_id': None,
                'customer_id': customer_id,
                'customer_name': customer['name'] if customer else 'Unknown',
                'customer_type': customer['customer_type'] if customer else 'Wholesale',
                'market': 'Local' if random.random() > 0.4 else 'Export',
                'billing_address': f"{random.randint(1,999)} Business Street, Dubai",
                'assigned_salesperson_id': random.choice(list(user_ids.values())),
                'currency': random.choice(['AED', 'USD', 'EUR']),
                'payment_terms': random.choice(['Net 30', 'Net 45', 'Net 60']),
                'incoterm': random.choice(['DAP', 'DDP', 'FOB']) if random.random() > 0.5 else None,
                'discount_percent': 0,
                'tax_percent': 5,
                'amount_paid': round(amount_paid, 2),
                'payment_status': 'Paid' if amount_paid >= total * 0.95 else ('Partially Paid' if amount_paid > 0 else 'Unpaid'),
                'status': 'Posted',
                'notes': random.choice(['', 'EOR attached', 'Original invoice', 'Customer requested POD']),
                'lines': lines,
                'company_id': random.choice([1, 2, 3])
            })
            invoices_created += 1
        
        print(f"  - Created {invoices_created} sales invoices")
        
        print("\n[12/12] Creating sales activities (200+)...")
        activities_created = 0
        
        for i in range(200):
            days_ago = random.randint(1, 180)
            activity_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            next_follow = (datetime.strptime(activity_date, '%Y-%m-%d') + timedelta(days=random.randint(1, 14))).strftime('%Y-%m-%d')
            
            customer_id = random.choice(customer_ids) if random.random() > 0.3 else None
            
            activity_types = ['Call', 'WhatsApp', 'Email', 'Visit', 'Meeting', 'Follow-up', 'Demo', 'Proposal Sent']
            
            create_activity(conn, {
                'activity_type': random.choice(activity_types),
                'activity_date': activity_date,
                'activity_time': f"{random.randint(8,17):02d}:{random.choice(['00', '15', '30', '45'])}",
                'customer_id': customer_id,
                'owner_id': random.choice(list(user_ids.values())),
                'subject': random.choice([
                    'Follow up on quotation', 'Product inquiry', 'Price negotiation',
                    'Delivery schedule', 'Technical discussion', 'Contract renewal',
                    'New product introduction', 'Stock availability check', 'Payment follow up',
                    'Customer visit', 'Product demo', 'Competitive quote discussion'
                ]),
                'result': random.choice(['Positive', 'Neutral', 'Needs follow up', 'Will order', 'Not interested', 'Called back later']),
                'next_action': random.choice(['Send quotation', 'Call back', 'Send samples', 'Arrange meeting', 'Process order', 'Send price list']),
                'next_follow_up_date': next_follow if random.random() > 0.3 else None,
                'status': 'Completed',
                'notes': random.choice(['', 'Customer interested in premium brand', 'Price is main concern', 'Looking for better payment terms', 'Regular buyer']),
                'reference_type': random.choice(['inquiry', 'quotation', 'order', None]),
                'reference_id': random.randint(1, 20) if random.random() > 0.5 else None,
                'company_id': random.choice([1, 2, 3])
            })
            activities_created += 1
        
        print(f"  - Created {activities_created} sales activities")
        
        # Create targets
        print("\nCreating sales targets...")
        for user_id in list(user_ids.values())[:8]:  # First 8 users
            for month in range(1, 13):
                year = datetime.now().year
                target_date = f"{year}-{month:02d}-01"
                
                conn.execute("""
                    INSERT INTO sales_targets (
                        salesperson_id, period, year, quarter, month,
                        target_amount, target_quantity, new_customer_target,
                        reactivation_target, status, company_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, 'Monthly', year, (month-1)//3 + 1, month,
                    random.randint(50000, 200000),  # target_amount
                    random.randint(10, 50),  # target_quantity
                    random.randint(1, 5),  # new_customer_target
                    random.randint(1, 3),  # reactivation_target
                    'Active', 1
                ))
        conn.commit()
        print(f"  - Created 12 monthly targets per salesperson")
        
        # Create some alerts
        print("\nCreating sample alerts...")
        alert_types = [
            ('quotation_expiry', 'High', 'Quotation expires in 3 days'),
            ('reservation_expiry', 'Medium', 'Reservation expiring soon'),
            ('credit_limit', 'High', 'Customer approaching credit limit'),
            ('inquiry_sla', 'Medium', 'Inquiry pending response'),
            ('order_delay', 'Critical', 'Order delivery delayed'),
        ]
        
        for i in range(15):
            alert_type, priority, title = random.choice(alert_types)
            customer_id = random.choice(customer_ids) if random.random() > 0.3 else None
            
            conn.execute("""
                INSERT INTO sales_alerts (
                    alert_type, alert_code, title, message,
                    customer_id, salesperson_id, priority, status,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                alert_type,
                f"ALT-{datetime.now().year}-{i+1:05d}",
                title,
                f"Auto-generated alert for {customer_id or 'system'}",
                customer_id,
                random.choice(list(user_ids.values())),
                priority,
                random.choice(['Open', 'Open', 'Acknowledged']),
                (datetime.now() - timedelta(days=random.randint(0, 7))).strftime('%Y-%m-%d')
            ))
        conn.commit()
        print(f"  - Created 15 sample alerts")
        
        print("\n" + "=" * 60)
        print("SEED DATA COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"""
Summary:
- {len(COMPANIES)} Companies
- {len(WAREHOUSES)} Warehouses  
- {len(SALES_USERS)} Sales Users
- {parts_created} Parts/Items
- {customers_created} Customers
- {inquiries_created} Inquiries
- {quotations_created} Quotations
- {proformas_created} Pro Forma Invoices
- {confirmations_created} Sales Confirmations
- {orders_created} Sales Orders
- {invoices_created} Sales Invoices
- {activities_created} Sales Activities
- 96 Sales Targets (12 per salesperson)
- 15 Sample Alerts
        """)
        
    except Exception as e:
        print(f"Error during seeding: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    seed_database()
