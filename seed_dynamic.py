"""
Smart Schema-Aware Demo Data Seeder
===================================
This script reads actual table schemas and inserts appropriate data.
It is completely safe and idempotent.

Usage:
    python seed_dynamic.py
"""

import os
import sys
import sqlite3
import random
from datetime import datetime, timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'warehouse.db')

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except:
    pass


def get_db():
    conn = sqlite3.connect(DATABASE, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def get_columns(db, table):
    """Get actual columns for a table."""
    try:
        cursor = db.execute(f"PRAGMA table_info([{table}])")
        return [row[1] for row in cursor.fetchall()]
    except:
        return []


def get_first_id(db, table):
    """Get first ID from a table."""
    try:
        result = db.execute(f"SELECT id FROM [{table}] LIMIT 1").fetchone()
        return result['id'] if result else 1
    except:
        return 1


def count_rows(db, table):
    """Count rows in table."""
    try:
        return db.execute(f"SELECT COUNT(*) FROM [{table}]").fetchone()[0]
    except:
        return 0


def col_exists(cols, *candidates):
    """Check if any of the candidates exist in columns."""
    for c in candidates:
        if c in cols:
            return c
    return None


def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def days_ago(n):
    return (datetime.now() - timedelta(days=n)).strftime('%Y-%m-%d')


def safe_insert(db, table, data):
    """Insert data dict into table, ignoring extra columns."""
    cols = get_columns(db, table)
    filtered = {k: v for k, v in data.items() if k in cols}
    if not filtered:
        return False
    placeholders = ', '.join(['?'] * len(filtered))
    col_names = ', '.join(filtered.keys())
    try:
        db.execute(f"INSERT INTO [{table}] ({col_names}) VALUES ({placeholders})",
                   list(filtered.values()))
        return True
    except Exception as e:
        return False


def smart_seed_table(db, table, generator_fn):
    """Seed a table using a smart generator function."""
    cols = get_columns(db, table)
    if not cols:
        return 0
    
    if count_rows(db, table) > 0:
        return 0
    
    count = 0
    for data in generator_fn(cols):
        if safe_insert(db, table, data):
            count += 1
    return count


# =============================================================================
# SMART SEED FUNCTIONS (one per table)
# =============================================================================

def seed_md_country(cols):
    data = [
        {'code': 'AE', 'name': 'United Arab Emirates', 'iso_code': 'UAE', 'phone_code': '+971'},
        {'code': 'SA', 'name': 'Saudi Arabia', 'iso_code': 'SA', 'phone_code': '+966'},
        {'code': 'QA', 'name': 'Qatar', 'iso_code': 'QA', 'phone_code': '+974'},
        {'code': 'KW', 'name': 'Kuwait', 'iso_code': 'KW', 'phone_code': '+965'},
        {'code': 'BH', 'name': 'Bahrain', 'iso_code': 'BH', 'phone_code': '+973'},
        {'code': 'OM', 'name': 'Oman', 'iso_code': 'OM', 'phone_code': '+968'},
        {'code': 'EG', 'name': 'Egypt', 'iso_code': 'EG', 'phone_code': '+20'},
        {'code': 'US', 'name': 'United States', 'iso_code': 'US', 'phone_code': '+1'},
        {'code': 'UK', 'name': 'United Kingdom', 'iso_code': 'GB', 'phone_code': '+44'},
        {'code': 'DE', 'name': 'Germany', 'iso_code': 'DE', 'phone_code': '+49'},
    ]
    for d in data:
        yield d


def seed_md_currency(cols):
    data = [
        {'code': 'AED', 'name': 'UAE Dirham', 'symbol': 'د.إ'},
        {'code': 'SAR', 'name': 'Saudi Riyal', 'symbol': 'ر.س'},
        {'code': 'USD', 'name': 'US Dollar', 'symbol': '$'},
        {'code': 'EUR', 'name': 'Euro', 'symbol': '€'},
        {'code': 'GBP', 'name': 'British Pound', 'symbol': '£'},
        {'code': 'JPY', 'name': 'Japanese Yen', 'symbol': '¥'},
    ]
    for d in data:
        yield d


def seed_md_payment_term(cols):
    terms = ['NET 30', 'NET 60', 'NET 90', 'CIA', 'COD', '2/10 NET 30']
    for i, t in enumerate(terms):
        yield {'code': t, 'name': t, 'days': (i+1)*30 if 'NET' in t else 0}


def seed_md_unit_of_measure(cols):
    units = [
        ('PCS', 'Pieces', 'pcs'), ('KG', 'Kilograms', 'kg'),
        ('L', 'Liters', 'L'), ('M', 'Meters', 'm'),
        ('BOX', 'Boxes', 'box'), ('CTN', 'Cartons', 'ctn'),
    ]
    for u in units:
        yield {'code': u[0], 'name': u[1], 'abbreviation': u[2]}


def seed_md_region(cols):
    regions = [
        ('DXB', 'Dubai', 'UAE'), ('AUH', 'Abu Dhabi', 'UAE'),
        ('SHJ', 'Sharjah', 'UAE'), ('JED', 'Jeddah', 'SA'),
    ]
    for r in regions:
        yield {'code': r[0], 'name': r[1], 'country': r[2]}


def seed_md_customer_type(cols):
    types = ['Enterprise', 'Corporate', 'SMB', 'Individual', 'Government']
    for t in types:
        yield {'name': t, 'description': f'{t} customer type'}


def seed_md_supplier_type(cols):
    types = ['Manufacturer', 'Distributor', 'Wholesaler', 'Import', 'Local']
    for t in types:
        yield {'name': t, 'description': f'{t} supplier type'}


def seed_md_lead_source(cols):
    sources = ['Website', 'Referral', 'Trade Show', 'Cold Call', 'Social Media']
    for s in sources:
        yield {'name': s, 'description': f'{s} lead source'}


def seed_md_leave_type(cols):
    types = ['Annual', 'Sick', 'Emergency', 'Maternity', 'Paternity']
    for t in types:
        yield {'name': t, 'description': f'{t} leave type'}


def seed_md_priority_level(cols):
    levels = ['Low', 'Medium', 'High', 'Urgent']
    for l in levels:
        yield {'name': l, 'description': f'{l} priority'}


def seed_md_order_status(cols):
    statuses = ['Draft', 'Submitted', 'Confirmed', 'Processing', 'Shipped', 'Delivered', 'Cancelled']
    for s in statuses:
        yield {'name': s, 'description': s}


def seed_md_shipment_status(cols):
    statuses = ['Pending', 'Picked', 'In Transit', 'Delivered', 'Returned']
    for s in statuses:
        yield {'name': s, 'description': s}


def seed_md_incoterm(cols):
    terms = [('EXW', 'Ex Works'), ('FCA', 'Free Carrier'), ('CPT', 'Carriage Paid To'),
             ('DAP', 'Delivered at Place'), ('DDP', 'Delivered Duty Paid')]
    for t in terms:
        yield {'code': t[0], 'name': t[1]}


def seed_sales_customers(cols):
    names = ['Al Futtaim Group', 'Emirates Trading LLC', 'Al Shirawi Group', 'Al Ghurair Foods',
             'Dubai Customs', 'Shawka Engineering', 'Gulf Medical University', 'Al Ain Dairy']
    for i, n in enumerate(names):
        yield {'customer_code': f'CUST-{i+1:04d}', 'customer_name': n, 'customer_type': 'Corporate',
               'status': 'Active', 'created_at': now()}


def seed_sales_inquiries(cols):
    subjects = ['Request for quotation', 'Bulk order inquiry', 'Parts availability check',
                'Custom parts request', 'Contract negotiation']
    for i in range(15):
        yield {'inquiry_number': f'INQ-2026-{i+1:04d}', 'subject': subjects[i % len(subjects)],
               'status': random.choice(['New', 'Contacted', 'Quoted', 'Closed']),
               'inquiry_date': days_ago(random.randint(1, 90)), 'created_at': now()}


def seed_sales_quotations(cols):
    for i in range(20):
        quo_date = days_ago(random.randint(1, 60))
        yield {'quotation_number': f'QT-2026-{i+1:04d}', 'quotation_date': quo_date,
               'expiry_date': (datetime.strptime(quo_date, '%Y-%m-%d') + timedelta(days=30)).strftime('%Y-%m-%d'),
               'status': random.choice(['Draft', 'Sent', 'Accepted']), 'total_amount': random.uniform(5000, 150000),
               'currency': 'AED', 'created_at': now()}


def seed_sales_orders(cols):
    for i in range(25):
        yield {'order_number': f'SO-2026-{i+1:04d}', 'order_date': days_ago(random.randint(1, 60)),
               'status': random.choice(['Draft', 'Confirmed', 'Processing', 'Shipped']),
               'total_amount': random.uniform(10000, 200000), 'payment_status': random.choice(['Pending', 'Paid']),
               'created_at': now()}


def seed_sales_opportunities(cols):
    for i in range(15):
        yield {'opportunity_name': f'Opportunity {i+1}', 'stage': random.choice(['Qualification', 'Proposal', 'Negotiation']),
               'expected_value': random.uniform(50000, 500000), 'probability': random.randint(20, 80),
               'expected_close_date': days_ago(random.randint(-30, 60)), 'created_at': now()}


def seed_sales_invoices(cols):
    for i in range(20):
        yield {'invoice_number': f'INV-2026-{i+1:04d}', 'invoice_date': days_ago(random.randint(1, 90)),
               'due_date': days_ago(random.randint(-30, 60)), 'status': random.choice(['Draft', 'Sent', 'Paid']),
               'total_amount': random.uniform(5000, 100000), 'tax_amount': random.uniform(250, 5000),
               'paid_amount': random.uniform(0, 50000), 'created_at': now()}


def seed_suppliers(cols):
    names = ['Toyota Parts Distribution', 'Bosch Automotive', 'Denso Corporation', 'ACDelco Parts',
             'Hyundai Mobis', 'Gulf Auto Parts', 'Emirates Filters LLC', 'National Motors Corp']
    for i, n in enumerate(names):
        yield {'supplier_code': f'SUP-{i+1:04d}', 'supplier_name': n, 'supplier_type': 'Distributor',
               'status': 'Active', 'created_at': now()}


def seed_logistics_drivers(cols):
    names = ['Ahmed Ali', 'Mohammed Hassan', 'Khalid Rahman', 'Omar Farouk', 'Tariq Mansour',
             'Faisal Ahmed', 'Bilal Khan', 'Rashid Al Maktoum']
    for n in names:
        yield {'driver_name': n, 'license_number': f'DL-{random.randint(100000, 999999)}',
               'phone': f'+97150{random.randint(1000000, 9999999)}', 'status': 'Active', 'created_at': now()}


def seed_logistics_vehicles(cols):
    for i in range(15):
        yield {'vehicle_number': f'VEH-{i+1:04d}', 'vehicle_type': random.choice(['Van', 'Truck', 'Pickup']),
               'capacity_tons': random.uniform(1, 10), 'status': 'Active', 'created_at': now()}


def seed_procurement_requisitions(cols):
    for i in range(20):
        yield {'requisition_number': f'PR-2026-{i+1:04d}', 'request_date': days_ago(random.randint(1, 45)),
               'department': random.choice(['Sales', 'Operations', 'Warehouse', 'HR']),
               'status': random.choice(['Draft', 'Submitted', 'Approved']),
               'estimated_cost': random.uniform(5000, 100000), 'created_at': now()}


def seed_procurement_rfqs(cols):
    for i in range(15):
        yield {'rfq_number': f'RFQ-2026-{i+1:04d}', 'rfq_date': days_ago(random.randint(1, 30)),
               'valid_until': days_ago(random.randint(-30, 30)),
               'status': random.choice(['Draft', 'Sent', 'Received']),
               'estimated_value': random.uniform(10000, 200000), 'created_at': now()}


def seed_procurement_purchase_orders(cols):
    for i in range(25):
        yield {'po_number': f'PO-2026-{i+1:04d}', 'order_date': days_ago(random.randint(1, 60)),
               'expected_delivery': days_ago(random.randint(-30, 30)),
               'status': random.choice(['Draft', 'Sent', 'Confirmed', 'Received']),
               'total_amount': random.uniform(10000, 300000), 'created_at': now()}


def seed_procurement_quotations(cols):
    for i in range(15):
        yield {'quotation_number': f'SQ-2026-{i+1:04d}', 'quotation_date': days_ago(random.randint(1, 30)),
               'valid_until': days_ago(random.randint(-30, 30)),
               'status': random.choice(['Submitted', 'Under Review', 'Accepted']),
               'total_amount': random.uniform(15000, 250000), 'payment_terms': 'NET 30', 'created_at': now()}


def seed_procurement_contracts(cols):
    for i in range(12):
        yield {'contract_number': f'PC-2026-{i+1:04d}', 'title': f'Framework Agreement {i+1}',
               'contract_value': random.uniform(100000, 1000000),
               'start_date': days_ago(random.randint(30, 180)),
               'end_date': days_ago(random.randint(-180, 0)),
               'status': random.choice(['Draft', 'Active', 'Expired']),
               'payment_terms': 'NET 60', 'created_at': now()}


def seed_logistics_shipments(cols):
    for i in range(20):
        yield {'shipment_number': f'SHP-2026-{i+1:04d}', 'ship_date': days_ago(random.randint(5, 40)),
               'estimated_arrival': days_ago(random.randint(-10, 20)),
               'status': random.choice(['In Transit', 'Customs', 'Delivered']),
               'carrier': random.choice(['DHL', 'FedEx', 'UPS', 'Aramex']),
               'tracking_number': f'TRK{random.randint(10000000, 99999999)}', 'created_at': now()}


def seed_logistics_delivery_orders(cols):
    for i in range(25):
        yield {'order_number': f'DO-2026-{i+1:04d}', 'delivery_date': days_ago(random.randint(-7, 14)),
               'time_slot': f'{9+i}:00-{10+i}:00',
               'status': random.choice(['Pending', 'Assigned', 'In Transit', 'Delivered']),
               'notes': f'Delivery order {i+1}', 'created_at': now()}


def seed_logistics_pickup_orders(cols):
    for i in range(15):
        yield {'order_number': f'PPO-2026-{i+1:04d}', 'pickup_date': days_ago(random.randint(-7, 14)),
               'status': random.choice(['Pending', 'Assigned', 'Completed']),
               'notes': f'Pickup order {i+1}', 'created_at': now()}


def seed_logistics_route_masters(cols):
    routes = [
        ('DXB-AUH', 'Dubai - Abu Dhabi', 150),
        ('DXB-SHJ', 'Dubai - Sharjah', 30),
        ('DXB-AIN', 'Dubai - Al Ain', 180),
    ]
    for code, name, dist in routes:
        yield {'route_code': code, 'route_name': name, 'estimated_distance_km': dist,
               'estimated_time_minutes': dist, 'is_active': 1, 'created_at': now()}


def seed_logistics_carriers(cols):
    carriers = [
        ('DHL Express', '+971420000000', 'dhl@express.com'),
        ('FedEx', '+971420000001', 'fedex@uae.com'),
        ('Aramex', '+971420000002', 'aramex@uae.com'),
        ('SMSA Express', '+971420000003', 'smsa@express.com'),
    ]
    for name, phone, email in carriers:
        yield {'carrier_name': name, 'contact_phone': phone, 'contact_email': email,
               'service_type': 'International', 'is_active': 1, 'created_at': now()}


def seed_finance_customer_receipts(cols):
    for i in range(20):
        yield {'receipt_number': f'RCP-2026-{i+1:04d}', 'receipt_date': days_ago(random.randint(1, 60)),
               'amount': random.uniform(1000, 30000),
               'payment_method': random.choice(['Cash', 'Bank Transfer', 'Check']),
               'reference_number': f'REF-{random.randint(100000, 999999)}',
               'notes': f'Payment received {i+1}', 'created_at': now()}


def seed_finance_supplier_payments(cols):
    for i in range(20):
        yield {'payment_number': f'PAY-2026-{i+1:04d}', 'payment_date': days_ago(random.randint(1, 60)),
               'amount': random.uniform(1000, 30000),
               'payment_method': random.choice(['Cash', 'Bank Transfer', 'Check']),
               'reference_number': f'PAY-REF-{random.randint(100000, 999999)}',
               'notes': f'Payment for invoice {i+1}', 'created_at': now()}


def seed_finance_customer_credit_notes(cols):
    for i in range(10):
        yield {'credit_note_number': f'CN-2026-{i+1:04d}', 'credit_note_date': days_ago(random.randint(1, 45)),
               'amount': random.uniform(500, 5000),
               'reason': random.choice(['Return', 'Discount', 'Adjustment']),
               'status': random.choice(['Draft', 'Issued', 'Applied']),
               'applied_amount': random.uniform(0, 3000), 'created_at': now()}


def seed_finance_supplier_debit_notes(cols):
    for i in range(10):
        yield {'debit_note_number': f'DN-2026-{i+1:04d}', 'debit_note_date': days_ago(random.randint(1, 45)),
               'amount': random.uniform(500, 5000),
               'reason': random.choice(['Price Adjustment', 'Shortage', 'Damaged Goods']),
               'status': random.choice(['Draft', 'Issued', 'Resolved']), 'created_at': now()}


def seed_marketing_campaigns(cols):
    for i in range(30):
        yield {'campaign_name': f'Campaign {i+1}',
               'campaign_type': random.choice(['Email', 'Social', 'Display', 'Search']),
               'start_date': days_ago(random.randint(1, 45)),
               'end_date': days_ago(random.randint(-30, 0)),
               'budget': random.uniform(5000, 50000),
               'spent': random.uniform(2000, 40000),
               'status': random.choice(['Draft', 'Active', 'Paused', 'Completed']),
               'created_at': now()}


def seed_marketing_leads(cols):
    for i in range(100):
        yield {'lead_name': f'Lead {i+1}', 'lead_email': f'lead{i+1}@example.com',
               'lead_phone': f'+97150{random.randint(1000000, 9999999)}',
               'status': random.choice(['New', 'Contacted', 'Qualified', 'Converted']),
               'source': random.choice(['Website', 'Referral', 'Social Media']),
               'created_at': now()}


def seed_marketing_brands(cols):
    brands = ['Toyota', 'Samsung', 'Apple', 'Nike', 'Adidas', 'Sony', 'LG', 'Bosch']
    for b in brands:
        yield {'brand_name': b, 'industry': 'General', 'country_of_origin': 'International',
               'status': 'Active', 'created_at': now()}


def seed_marketing_channels(cols):
    channels = [
        ('Website', 'Owned', 'High'), ('Instagram', 'Social', 'High'),
        ('LinkedIn', 'Social', 'Medium'), ('Email', 'Direct', 'Medium'),
        ('Google Ads', 'Paid', 'High'), ('Facebook', 'Social', 'Medium'),
    ]
    for name, ch_type, eff in channels:
        yield {'channel_name': name, 'channel_type': ch_type, 'effectiveness': eff,
               'status': 'Active', 'created_at': now()}


def seed_social_accounts(cols):
    platforms = [
        ('@whdash_official', 'Instagram', 'Active'),
        ('@whdashLinkedIn', 'LinkedIn', 'Active'),
        ('MMDx_Official', 'Twitter', 'Active'),
        ('MMDx Facebook', 'Facebook', 'Active'),
    ]
    for handle, platform, status in platforms:
        yield {'account_handle': handle, 'platform': platform, 'status': status,
               'followers_count': random.randint(1000, 50000), 'created_at': now()}


def seed_social_leads(cols):
    for i in range(50):
        yield {'lead_name': f'Social Lead {i+1}', 'platform': random.choice(['Instagram', 'LinkedIn', 'Twitter']),
               'status': random.choice(['New', 'Contacted', 'Qualified']),
               'email': f'lead{i+1}@social.com',
               'phone': f'+97150{random.randint(1000000, 9999999)}', 'created_at': now()}


def seed_workflow_definitions(cols):
    workflows = ['Leave Approval', 'Purchase Approval', 'Document Review', 'Quality Approval']
    for i, w in enumerate(workflows):
        yield {'definition_name': w, 'description': f'{w} workflow',
               'version': '1.0', 'is_active': 1, 'created_at': now()}


def seed_workflow_instances(cols):
    for i in range(20):
        yield {'instance_title': f'Workflow Instance {i+1}',
               'status': random.choice(['Running', 'Completed', 'Cancelled']),
               'started_at': days_ago(random.randint(1, 30)),
               'completed_at': days_ago(random.randint(0, 15)) if random.random() > 0.5 else None,
               'created_at': now()}


def seed_notification_templates(cols):
    templates = [
        ('Approval Request', 'Your approval is required', 'Email'),
        ('Task Assigned', 'You have been assigned a task', 'In-App'),
        ('Status Update', 'Status has been updated', 'Both'),
        ('Reminder', 'Reminder for pending action', 'Email'),
    ]
    for name, content, channel in templates:
        yield {'template_name': name, 'content': content, 'channel': channel,
               'is_active': 1, 'created_at': now()}


def seed_api_clients(cols):
    clients = ['Mobile App', 'Web Dashboard', 'Partner API', 'Internal Service']
    for c in clients:
        yield {'client_name': c, 'client_type': 'Confidential',
               'status': 'Active', 'rate_limit_per_hour': random.randint(1000, 10000),
               'created_at': now()}


def seed_webhook_subscriptions(cols):
    events = ['order.created', 'order.updated', 'shipment.delivered', 'customer.added']
    for i, e in enumerate(events):
        yield {'subscription_name': f'Webhook {i+1}',
               'webhook_url': f'https://example.com/webhook/{i+1}',
               'events': e, 'is_active': 1, 'created_at': now()}


def seed_hr_leave_requests(cols):
    for i in range(25):
        yield {'start_date': days_ago(random.randint(-30, 30)),
               'end_date': days_ago(random.randint(-20, 40)),
               'total_days': random.randint(1, 10),
               'reason': f'Leave request {i+1}',
               'status': random.choice(['Pending', 'Approved', 'Rejected']),
               'request_date': days_ago(random.randint(1, 30)), 'created_at': now()}


def seed_hr_loans(cols):
    for i in range(15):
        yield {'loan_type': random.choice(['Personal', 'Home', 'Car', 'Education']),
               'principal_amount': random.uniform(5000, 50000),
               'monthly_payment': random.uniform(200, 2000),
               'tenure_months': random.choice([12, 24, 36, 48]),
               'status': random.choice(['Active', 'Closed', 'Pending']),
               'application_date': days_ago(random.randint(60, 300)),
               'start_date': days_ago(random.randint(20, 200)), 'created_at': now()}


def seed_hr_bonus_records(cols):
    for i in range(20):
        yield {'bonus_type': random.choice(['Performance', 'Year-End', 'Project']),
               'amount': random.uniform(500, 5000),
               'bonus_date': days_ago(random.randint(1, 180)),
               'reason': f'Bonus {i+1}',
               'status': random.choice(['Pending', 'Approved', 'Paid']),
               'created_at': now()}


def seed_hr_deduction_records(cols):
    for i in range(20):
        yield {'deduction_type': random.choice(['Late', 'Absent', 'Equipment']),
               'amount': random.uniform(50, 500),
               'deduction_date': days_ago(random.randint(1, 60)),
               'reason': f'Deduction {i+1}',
               'status': random.choice(['Pending', 'Approved']), 'created_at': now()}


def seed_hr_overtime_requests(cols):
    for i in range(15):
        yield {'overtime_date': days_ago(random.randint(1, 30)),
               'hours': random.uniform(1, 8),
               'overtime_type': random.choice(['Weekday', 'Weekend', 'Holiday']),
               'reason': f'Overtime {i+1}',
               'status': random.choice(['Pending', 'Approved', 'Rejected']),
               'created_at': now()}


def seed_hr_training_programs(cols):
    programs = ['Leadership Training', 'Technical Skills', 'Safety Certification', 'Customer Service', 'IT Workshop']
    for p in programs:
        yield {'program_name': p, 'description': f'{p} program',
               'duration_hours': random.randint(8, 40),
               'program_type': random.choice(['Internal', 'External', 'Online']),
               'status': 'Active', 'created_at': now()}


def seed_hr_performance_reviews(cols):
    for i in range(15):
        yield {'review_period': '2026 Q1',
               'review_date': days_ago(random.randint(1, 60)),
               'overall_rating': random.uniform(3.0, 5.0),
               'strengths': f'Strengths for review {i+1}',
               'improvements': f'Areas for improvement {i+1}',
               'status': random.choice(['Draft', 'Submitted', 'Completed']),
               'created_at': now()}


def seed_wms_transfers(cols):
    for i in range(20):
        yield {'transfer_number': f'TRF-2026-{i+1:04d}',
               'transfer_date': days_ago(random.randint(1, 30)),
               'status': random.choice(['Draft', 'In Transit', 'Received']),
               'notes': f'Transfer {i+1}', 'created_at': now()}


def seed_wms_shipments(cols):
    for i in range(15):
        yield {'shipment_number': f'WMS-SHP-2026-{i+1:04d}',
               'ship_date': days_ago(random.randint(1, 30)),
               'status': random.choice(['Preparing', 'Shipped', 'In Transit']),
               'carrier': random.choice(['DHL', 'FedEx', 'Aramex']),
               'notes': f'Shipment {i+1}', 'created_at': now()}


def seed_wms_returns(cols):
    for i in range(12):
        yield {'return_number': f'RET-2026-{i+1:04d}',
               'return_date': days_ago(random.randint(1, 30)),
               'reason': random.choice(['Defective', 'Wrong Item', 'Changed Mind']),
               'status': random.choice(['Pending', 'Approved', 'Received']),
               'refund_amount': random.uniform(100, 5000),
               'notes': f'Return {i+1}', 'created_at': now()}


def seed_wms_stock_adjustments(cols):
    for i in range(15):
        yield {'adjustment_number': f'ADJ-2026-{i+1:04d}',
               'adjustment_date': days_ago(random.randint(1, 30)),
               'adjustment_type': random.choice(['Count', 'Damage', 'Theft']),
               'reason': f'Adjustment reason {i+1}',
               'status': random.choice(['Draft', 'Approved', 'Applied']),
               'notes': f'Adjustment {i+1}', 'created_at': now()}


def seed_document_categories(cols):
    cats = ['Contracts', 'Invoices', 'Reports', 'Policies', 'Manuals', 'Certifications']
    for c in cats:
        yield {'category_name': c, 'description': f'{c} documents', 'created_at': now()}


def seed_document_tags(cols):
    tags = ['Important', 'Urgent', 'Confidential', 'Draft', 'Final']
    for t in tags:
        yield {'tag_name': t, 'created_at': now()}


def seed_form_submissions(cols):
    for i in range(20):
        yield {'submission_date': days_ago(random.randint(1, 45)),
               'status': random.choice(['Draft', 'Submitted', 'Approved']),
               'notes': f'Submission {i+1}', 'created_at': now()}


def seed_form_comments(cols):
    for i in range(15):
        yield {'comment_text': f'Comment {i+1}',
               'created_at': now()}


def seed_form_approvals(cols):
    for i in range(15):
        yield {'approval_date': days_ago(random.randint(1, 30)),
               'status': random.choice(['Pending', 'Approved', 'Rejected']),
               'comments': f'Approval comments {i+1}',
               'created_at': now()}


def seed_bi_reporting_datasets(cols):
    datasets = [
        ('Sales Dataset', 'Sales data'), ('Inventory Dataset', 'Inventory levels'),
        ('HR Dataset', 'Employee data'), ('Finance Dataset', 'Financial data'),
    ]
    for name, desc in datasets:
        yield {'dataset_name': name, 'description': desc,
               'refresh_schedule': 'Daily',
               'is_active': 1, 'created_at': now()}


def seed_bi_kpis(cols):
    kpis = [
        ('Total Revenue', 'SUM', 'Revenue'), ('Order Count', 'COUNT', 'Orders'),
        ('Inventory Value', 'SUM', 'Inventory'), ('Employee Count', 'COUNT', 'Employees'),
    ]
    for name, agg, desc in kpis:
        yield {'kpi_name': name, 'aggregation': agg, 'description': f'{desc} KPI',
               'target_value': random.uniform(100000, 1000000),
               'created_at': now()}


def seed_bi_saved_reports(cols):
    for i in range(10):
        yield {'report_name': f'Report {i+1}',
               'report_type': random.choice(['Sales', 'Inventory', 'Financial']),
               'is_shared': random.choice([0, 1]),
               'created_at': now()}


def seed_quality_inspection_templates(cols):
    templates = ['Incoming Inspection', 'In-Process Inspection', 'Final Inspection']
    for t in templates:
        yield {'template_name': t, 'description': f'{t} template',
               'is_active': 1, 'created_at': now()}


def seed_quality_capa_actions(cols):
    for i in range(15):
        yield {'action_type': random.choice(['Root Cause', 'Corrective', 'Preventive']),
               'description': f'CAPA action {i+1}',
               'due_date': days_ago(random.randint(-15, 30)),
               'status': random.choice(['Open', 'In Progress', 'Completed']),
               'created_at': now()}


def seed_numbering_sequences(cols):
    seqs = [('SO', 'Sales Order', 'SO-'), ('PO', 'Purchase Order', 'PO-'),
            ('INV', 'Invoice', 'INV-'), ('DO', 'Delivery', 'DO-')]
    for prefix, name, pattern in seqs:
        yield {'sequence_name': name, 'prefix': prefix,
               'current_value': random.randint(100, 999),
               'format_pattern': f'{pattern}YYYY-####',
               'is_active': 1, 'created_at': now()}


def seed_user_sessions(cols):
    for i in range(15):
        yield {'session_token': f'token_{random.randint(10000, 99999)}',
               'ip_address': f'192.168.1.{random.randint(1,255)}',
               'created_at': now()}


def seed_notification_logs(cols):
    for i in range(20):
        yield {'title': f'Notification {i+1}',
               'message': f'Message {i+1}',
               'notification_type': random.choice(['Email', 'SMS', 'In-App']),
               'is_read': random.choice([0, 1]),
               'sent_at': days_ago(random.randint(1, 15)),
               'created_at': now()}


def seed_saved_reports(cols):
    for i in range(12):
        yield {'report_name': f'Saved Report {i+1}',
               'report_type': random.choice(['Sales', 'Inventory', 'Financial']),
               'is_shared': random.choice([0, 1]),
               'created_at': now()}


def seed_sla_rules(cols):
    for i in range(8):
        yield {'rule_name': f'SLA Rule {i+1}',
               'rule_type': random.choice(['Response', 'Resolution']),
               'target_hours': random.randint(4, 72),
               'warning_threshold': random.randint(2, 48),
               'is_active': 1, 'created_at': now()}


def seed_escalation_rules(cols):
    for i in range(10):
        yield {'rule_name': f'Escalation Rule {i+1}',
               'trigger_type': random.choice(['Overdue', 'Priority']),
               'escalation_level': random.randint(1, 3),
               'action': 'Email + SMS', 'is_active': 1, 'created_at': now()}


def seed_automation_rules(cols):
    for i in range(10):
        yield {'rule_name': f'Automation {i+1}',
               'trigger_event': random.choice(['On Create', 'On Update']),
               'is_active': random.choice([0, 1]),
               'created_at': now()}


def seed_social_campaigns(cols):
    for i in range(15):
        yield {'campaign_name': f'Social Campaign {i+1}',
               'platform': random.choice(['Instagram', 'LinkedIn']),
               'campaign_type': random.choice(['Awareness', 'Engagement']),
               'start_date': days_ago(random.randint(1, 45)),
               'end_date': days_ago(random.randint(-30, 0)),
               'budget': random.uniform(5000, 50000),
               'status': random.choice(['Draft', 'Active', 'Completed']),
               'created_at': now()}


def seed_social_content_templates(cols):
    for i in range(10):
        yield {'template_name': f'Content Template {i+1}',
               'platform': random.choice(['Instagram', 'LinkedIn']),
               'created_at': now()}


def seed_social_audiences(cols):
    audiences = [
        ('Tech Enthusiasts', 50000), ('Business Professionals', 30000),
        ('Automotive Fans', 75000), ('Enterprise Buyers', 15000),
    ]
    for name, size in audiences:
        yield {'audience_name': name, 'estimated_size': size,
               'created_at': now()}


def seed_social_publish_queue(cols):
    for i in range(20):
        yield {'scheduled_time': f'2026-04-{random.randint(10, 30):02d} {random.randint(9, 17):02d}:00:00',
               'status': random.choice(['Scheduled', 'Published']),
               'created_at': now()}


def seed_social_automation_logs(cols):
    for i in range(15):
        yield {'automation_name': f'Automation {i+1}',
               'action_taken': 'Auto reply sent',
               'created_at': now()}


# =============================================================================
# TABLE TO SEEDER MAPPING
# =============================================================================

TABLE_SEEDERS = {
    # Master data
    'md_country': seed_md_country,
    'md_currency': seed_md_currency,
    'md_payment_term': seed_md_payment_term,
    'md_unit_of_measure': seed_md_unit_of_measure,
    'md_region': seed_md_region,
    'md_customer_type': seed_md_customer_type,
    'md_supplier_type': seed_md_supplier_type,
    'md_lead_source': seed_md_lead_source,
    'md_leave_type': seed_md_leave_type,
    'md_priority_level': seed_md_priority_level,
    'md_order_status': seed_md_order_status,
    'md_shipment_status': seed_md_shipment_status,
    'md_incoterm': seed_md_incoterm,
    # Sales
    'sales_customers': seed_sales_customers,
    'sales_inquiries': seed_sales_inquiries,
    'sales_quotations': seed_sales_quotations,
    'sales_orders': seed_sales_orders,
    'sales_opportunities': seed_sales_opportunities,
    'sales_invoices': seed_sales_invoices,
    # Procurement
    'suppliers': seed_suppliers,
    'procurement_requisitions': seed_procurement_requisitions,
    'procurement_rfqs': seed_procurement_rfqs,
    'procurement_purchase_orders': seed_procurement_purchase_orders,
    'procurement_quotations': seed_procurement_quotations,
    'procurement_contracts': seed_procurement_contracts,
    # Logistics
    'logistics_drivers': seed_logistics_drivers,
    'logistics_vehicles': seed_logistics_vehicles,
    'logistics_shipments': seed_logistics_shipments,
    'logistics_delivery_orders': seed_logistics_delivery_orders,
    'logistics_pickup_orders': seed_logistics_pickup_orders,
    'logistics_route_masters': seed_logistics_route_masters,
    'logistics_carriers': seed_logistics_carriers,
    # Finance
    'finance_customer_receipts': seed_finance_customer_receipts,
    'finance_supplier_payments': seed_finance_supplier_payments,
    'finance_customer_credit_notes': seed_finance_customer_credit_notes,
    'finance_supplier_debit_notes': seed_finance_supplier_debit_notes,
    # Marketing
    'marketing_campaigns': seed_marketing_campaigns,
    'marketing_leads': seed_marketing_leads,
    'marketing_brands': seed_marketing_brands,
    'marketing_channels': seed_marketing_channels,
    # Social Media
    'social_accounts': seed_social_accounts,
    'social_leads': seed_social_leads,
    'social_campaigns': seed_social_campaigns,
    'social_content_templates': seed_social_content_templates,
    'social_audiences': seed_social_audiences,
    'social_publish_queue': seed_social_publish_queue,
    # Workflow
    'workflow_definitions': seed_workflow_definitions,
    'workflow_instances': seed_workflow_instances,
    'notification_templates': seed_notification_templates,
    # API Gateway
    'api_clients': seed_api_clients,
    'webhook_subscriptions': seed_webhook_subscriptions,
    # HR
    'hr_leave_requests': seed_hr_leave_requests,
    'hr_loans': seed_hr_loans,
    'hr_bonus_records': seed_hr_bonus_records,
    'hr_deduction_records': seed_hr_deduction_records,
    'hr_overtime_requests': seed_hr_overtime_requests,
    'hr_training_programs': seed_hr_training_programs,
    'hr_performance_reviews': seed_hr_performance_reviews,
    # WMS
    'wms_transfers': seed_wms_transfers,
    'wms_shipments': seed_wms_shipments,
    'wms_returns': seed_wms_returns,
    'wms_stock_adjustments': seed_wms_stock_adjustments,
    # Documents
    'document_categories': seed_document_categories,
    'document_tags': seed_document_tags,
    # Forms
    'form_submissions': seed_form_submissions,
    'form_comments': seed_form_comments,
    'form_approvals': seed_form_approvals,
    # BI
    'bi_reporting_datasets': seed_bi_reporting_datasets,
    'bi_kpis': seed_bi_kpis,
    'bi_saved_reports': seed_bi_saved_reports,
    # Quality
    'quality_inspection_templates': seed_quality_inspection_templates,
    'quality_capa_actions': seed_quality_capa_actions,
    # Other
    'numbering_sequences': seed_numbering_sequences,
    'user_sessions': seed_user_sessions,
    'notification_logs': seed_notification_logs,
    'saved_reports': seed_saved_reports,
    'sla_rules': seed_sla_rules,
    'escalation_rules': seed_escalation_rules,
    'automation_rules': seed_automation_rules,
    'social_automation_logs': seed_social_automation_logs,
}


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 70)
    print("  MMDx SMART SCHEMA-AWARE SEEDER")
    print("=" * 70)
    print()
    
    db = get_db()
    
    # Get all tables
    cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    all_tables = [row[0] for row in cursor.fetchall()]
    
    seeded_count = 0
    total_seeded = 0
    
    for table in all_tables:
        if table in TABLE_SEEDERS:
            cols = get_columns(db, table)
            if not cols:
                continue
            
            current_count = count_rows(db, table)
            if current_count > 0:
                continue
            
            seeder_fn = TABLE_SEEDERS[table]
            count = 0
            for data in seeder_fn(cols):
                if safe_insert(db, table, data):
                    count += 1
            
            if count > 0:
                print(f"  + {table}: {count} rows")
                seeded_count += 1
                total_seeded += count
    
    db.commit()
    db.close()
    
    print()
    print("=" * 70)
    print(f"  SEEDED: {seeded_count} tables, {total_seeded} total rows")
    print("=" * 70)


if __name__ == '__main__':
    main()
