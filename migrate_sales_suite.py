"""
Sales Management Suite - Extended Migration
==========================================
Adds missing tables for complete Sales Management Suite:
- Pro forma Invoices
- Customer Purchase Orders (incoming from customers)
- Sales Confirmation Orders
- Sales Invoices
- Sales Alerts
- Document flow linking tables

Run this AFTER migrate_sales_tables.py

Usage:
    python migrate_sales_suite.py
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'warehouse.db')


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


def column_exists(conn, table, column):
    """Check if a column exists in a table."""
    result = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(col[1] == column for col in result)


def migrate():
    """Run all sales suite migrations."""
    print("Starting Sales Management Suite Extended Migration...")
    
    conn = get_connection()
    
    try:
        # =============================================================================
        # PRO FORMA INVOICES TABLE
        # =============================================================================
        if not table_exists(conn, 'sales_proforma_invoices'):
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sales_proforma_invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proforma_number TEXT UNIQUE NOT NULL,
                    reference_quotation_id INTEGER,
                    reference_confirmation_id INTEGER,
                    proforma_date DATE NOT NULL,
                    valid_until DATE,
                    customer_id INTEGER,
                    customer_name TEXT,
                    customer_type TEXT,
                    market TEXT DEFAULT 'Local',
                    assigned_salesperson_id INTEGER,
                    currency TEXT DEFAULT 'AED',
                    payment_terms TEXT,
                    delivery_terms TEXT,
                    incoterm TEXT,
                    subtotal REAL DEFAULT 0,
                    discount_percent REAL DEFAULT 0,
                    discount_amount REAL DEFAULT 0,
                    tax_percent REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    total_amount REAL DEFAULT 0,
                    advance_payment_percent REAL DEFAULT 0,
                    advance_payment_required REAL DEFAULT 0,
                    bank_details TEXT,
                    status TEXT DEFAULT 'Draft',
                    source TEXT,
                    notes TEXT,
                    attachment_path TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES sales_customers(id),
                    FOREIGN KEY (reference_quotation_id) REFERENCES sales_quotations(id),
                    FOREIGN KEY (assigned_salesperson_id) REFERENCES users(id)
                )
            """)
            print("  - Created sales_proforma_invoices table")
        else:
            print("  - sales_proforma_invoices already exists")

        # Pro forma lines
        if not table_exists(conn, 'sales_proforma_lines'):
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sales_proforma_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proforma_id INTEGER NOT NULL,
                    line_number INTEGER,
                    part_number TEXT,
                    brand TEXT,
                    description TEXT,
                    requested_quantity INTEGER DEFAULT 0,
                    unit_price REAL DEFAULT 0,
                    discount_percent REAL DEFAULT 0,
                    discount_amount REAL DEFAULT 0,
                    final_price REAL DEFAULT 0,
                    tax_percent REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    line_total REAL DEFAULT 0,
                    supply_lead_time TEXT,
                    stock_status TEXT,
                    origin TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (proforma_id) REFERENCES sales_proforma_invoices(id)
                )
            """)
            print("  - Created sales_proforma_lines table")
        else:
            print("  - sales_proforma_lines already exists")

        # =============================================================================
        # CUSTOMER PURCHASE ORDERS TABLE (Incoming from customers)
        # =============================================================================
        if not table_exists(conn, 'sales_customer_purchase_orders'):
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sales_customer_purchase_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_po_number TEXT UNIQUE NOT NULL,
                    customer_id INTEGER,
                    customer_name TEXT,
                    po_date DATE NOT NULL,
                    received_date DATE DEFAULT CURRENT_DATE,
                    reference_quotation_id INTEGER,
                    reference_proforma_id INTEGER,
                    reference_confirmation_id INTEGER,
                    currency TEXT DEFAULT 'AED',
                    payment_terms TEXT,
                    incoterm TEXT,
                    destination_country TEXT,
                    destination_port TEXT,
                    subtotal REAL DEFAULT 0,
                    discount_percent REAL DEFAULT 0,
                    discount_amount REAL DEFAULT 0,
                    tax_percent REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    total_amount REAL DEFAULT 0,
                    requested_delivery_date DATE,
                    assigned_salesperson_id INTEGER,
                    status TEXT DEFAULT 'Received',
                    review_status TEXT DEFAULT 'Pending',
                    discrepancy_notes TEXT,
                    mapping_notes TEXT,
                    converted_to_order_id INTEGER,
                    converted_at TIMESTAMP,
                    notes TEXT,
                    attachment_path TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES sales_customers(id),
                    FOREIGN KEY (reference_quotation_id) REFERENCES sales_quotations(id),
                    FOREIGN KEY (reference_proforma_id) REFERENCES sales_proforma_invoices(id),
                    FOREIGN KEY (assigned_salesperson_id) REFERENCES users(id)
                )
            """)
            print("  - Created sales_customer_purchase_orders table")
        else:
            print("  - sales_customer_purchase_orders already exists")

        # Customer PO lines
        if not table_exists(conn, 'sales_customer_po_lines'):
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sales_customer_po_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_po_id INTEGER NOT NULL,
                    line_number INTEGER,
                    part_number TEXT,
                    brand TEXT,
                    description TEXT,
                    ordered_quantity INTEGER DEFAULT 0,
                    unit_price REAL DEFAULT 0,
                    total_price REAL DEFAULT 0,
                    requested_delivery_date DATE,
                    mapping_status TEXT DEFAULT 'Pending',
                    mapped_order_line_id INTEGER,
                    discrepancy_type TEXT,
                    discrepancy_notes TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_po_id) REFERENCES sales_customer_purchase_orders(id)
                )
            """)
            print("  - Created sales_customer_po_lines table")
        else:
            print("  - sales_customer_po_lines already exists")

        # =============================================================================
        # SALES CONFIRMATION ORDERS TABLE
        # =============================================================================
        if not table_exists(conn, 'sales_confirmations'):
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sales_confirmations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    confirmation_number TEXT UNIQUE NOT NULL,
                    confirmation_date DATE NOT NULL,
                    reference_quotation_id INTEGER,
                    reference_proforma_id INTEGER,
                    reference_customer_po_id INTEGER,
                    customer_id INTEGER,
                    customer_name TEXT,
                    customer_type TEXT,
                    market TEXT DEFAULT 'Local',
                    assigned_salesperson_id INTEGER,
                    currency TEXT DEFAULT 'AED',
                    payment_terms TEXT,
                    delivery_terms TEXT,
                    incoterm TEXT,
                    lead_time_days INTEGER,
                    subtotal REAL DEFAULT 0,
                    discount_percent REAL DEFAULT 0,
                    discount_amount REAL DEFAULT 0,
                    tax_percent REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    total_amount REAL DEFAULT 0,
                    customer_acceptance_status TEXT DEFAULT 'Pending',
                    customer_acceptance_date DATE,
                    acceptance_notes TEXT,
                    status TEXT DEFAULT 'Draft',
                    notes TEXT,
                    attachment_path TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES sales_customers(id),
                    FOREIGN KEY (reference_quotation_id) REFERENCES sales_quotations(id),
                    FOREIGN KEY (reference_proforma_id) REFERENCES sales_proforma_invoices(id),
                    FOREIGN KEY (reference_customer_po_id) REFERENCES sales_customer_purchase_orders(id),
                    FOREIGN KEY (assigned_salesperson_id) REFERENCES users(id)
                )
            """)
            print("  - Created sales_confirmations table")
        else:
            print("  - sales_confirmations already exists")

        # Confirmation lines
        if not table_exists(conn, 'sales_confirmation_lines'):
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sales_confirmation_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    confirmation_id INTEGER NOT NULL,
                    line_number INTEGER,
                    part_number TEXT,
                    brand TEXT,
                    description TEXT,
                    confirmed_quantity INTEGER DEFAULT 0,
                    unit_price REAL DEFAULT 0,
                    discount_percent REAL DEFAULT 0,
                    discount_amount REAL DEFAULT 0,
                    final_price REAL DEFAULT 0,
                    tax_percent REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    line_total REAL DEFAULT 0,
                    delivery_date DATE,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (confirmation_id) REFERENCES sales_confirmations(id)
                )
            """)
            print("  - Created sales_confirmation_lines table")
        else:
            print("  - sales_confirmation_lines already exists")

        # =============================================================================
        # SALES INVOICES TABLE
        # =============================================================================
        if not table_exists(conn, 'sales_invoices'):
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sales_invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_number TEXT UNIQUE NOT NULL,
                    invoice_date DATE NOT NULL,
                    due_date DATE,
                    order_id INTEGER,
                    delivery_id INTEGER,
                    customer_id INTEGER,
                    customer_name TEXT,
                    customer_type TEXT,
                    market TEXT DEFAULT 'Local',
                    billing_address TEXT,
                    assigned_salesperson_id INTEGER,
                    currency TEXT DEFAULT 'AED',
                    payment_terms TEXT,
                    incoterm TEXT,
                    subtotal REAL DEFAULT 0,
                    discount_percent REAL DEFAULT 0,
                    discount_amount REAL DEFAULT 0,
                    tax_percent REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    total_amount REAL DEFAULT 0,
                    amount_paid REAL DEFAULT 0,
                    amount_due REAL DEFAULT 0,
                    payment_status TEXT DEFAULT 'Unpaid',
                    status TEXT DEFAULT 'Draft',
                    eor_invoice_number TEXT,
                    eor_status TEXT,
                    notes TEXT,
                    attachment_path TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (order_id) REFERENCES sales_orders(id),
                    FOREIGN KEY (delivery_id) REFERENCES sales_deliveries(id),
                    FOREIGN KEY (customer_id) REFERENCES sales_customers(id),
                    FOREIGN KEY (assigned_salesperson_id) REFERENCES users(id)
                )
            """)
            print("  - Created sales_invoices table")
        else:
            print("  - sales_invoices already exists")

        # Invoice lines
        if not table_exists(conn, 'sales_invoice_lines'):
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sales_invoice_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    line_number INTEGER,
                    part_number TEXT,
                    brand TEXT,
                    description TEXT,
                    quantity INTEGER DEFAULT 0,
                    unit_price REAL DEFAULT 0,
                    discount_percent REAL DEFAULT 0,
                    discount_amount REAL DEFAULT 0,
                    final_price REAL DEFAULT 0,
                    tax_percent REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    line_total REAL DEFAULT 0,
                    delivery_line_id INTEGER,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (invoice_id) REFERENCES sales_invoices(id)
                )
            """)
            print("  - Created sales_invoice_lines table")
        else:
            print("  - sales_invoice_lines already exists")

        # =============================================================================
        # SALES ALERTS TABLE
        # =============================================================================
        if not table_exists(conn, 'sales_alerts'):
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sales_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL,
                    alert_code TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT,
                    reference_type TEXT,
                    reference_id INTEGER,
                    customer_id INTEGER,
                    salesperson_id INTEGER,
                    priority TEXT DEFAULT 'Medium',
                    status TEXT DEFAULT 'Open',
                    acknowledged_at TIMESTAMP,
                    acknowledged_by INTEGER,
                    resolved_at TIMESTAMP,
                    resolved_by INTEGER,
                    resolution_notes TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES sales_customers(id),
                    FOREIGN KEY (salesperson_id) REFERENCES users(id),
                    FOREIGN KEY (acknowledged_by) REFERENCES users(id),
                    FOREIGN KEY (resolved_by) REFERENCES users(id)
                )
            """)
            print("  - Created sales_alerts table")
        else:
            print("  - sales_alerts already exists")

        # =============================================================================
        # SALES COMMISSION RULES TABLE
        # =============================================================================
        if not table_exists(conn, 'sales_commission_rules'):
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sales_commission_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name TEXT NOT NULL,
                    rule_type TEXT DEFAULT 'Standard',
                    salesperson_role TEXT,
                    customer_type TEXT,
                    market TEXT,
                    brand TEXT,
                    min_margin_percent REAL DEFAULT 0,
                    max_discount_percent REAL DEFAULT 0,
                    commission_percent REAL DEFAULT 0,
                    tier_from REAL DEFAULT 0,
                    tier_to REAL,
                    effective_from DATE,
                    effective_until DATE,
                    is_active INTEGER DEFAULT 1,
                    notes TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("  - Created sales_commission_rules table")
        else:
            print("  - sales_commission_rules already exists")

        # =============================================================================
        # SALES COMMISSION RECORDS TABLE
        # =============================================================================
        if not table_exists(conn, 'sales_commissions'):
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sales_commissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER,
                    order_id INTEGER,
                    salesperson_id INTEGER NOT NULL,
                    commission_amount REAL DEFAULT 0,
                    commission_percent REAL DEFAULT 0,
                    base_amount REAL DEFAULT 0,
                    margin_percent REAL DEFAULT 0,
                    status TEXT DEFAULT 'Pending',
                    paid_at TIMESTAMP,
                    paid_by INTEGER,
                    notes TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (invoice_id) REFERENCES sales_invoices(id),
                    FOREIGN KEY (order_id) REFERENCES sales_orders(id),
                    FOREIGN KEY (salesperson_id) REFERENCES users(id),
                    FOREIGN KEY (paid_by) REFERENCES users(id)
                )
            """)
            print("  - Created sales_commissions table")
        else:
            print("  - sales_commissions already exists")

        # =============================================================================
        # ENHANCED SALES CUSTOMER CATEGORIES TABLE
        # =============================================================================
        if not table_exists(conn, 'sales_customer_segments'):
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sales_customer_segments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    segment_code TEXT UNIQUE NOT NULL,
                    segment_name TEXT NOT NULL,
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("  - Created sales_customer_segments table")
            
            # Insert default segments
            default_segments = [
                ('ACTIVE', 'Active Customer', 'Customers who purchase regularly'),
                ('INACTIVE', 'Inactive Customer', 'Customers with no recent purchases'),
                ('KEY', 'Key Account', 'High-value strategic customers'),
                ('HIGH_VOLUME', 'High Volume', 'Customers with high order volumes'),
                ('HIGH_MARGIN', 'High Margin', 'Customers with premium pricing acceptance'),
                ('PRICE_SENSITIVE', 'Price Sensitive', 'Customers who negotiate heavily'),
                ('SPEED_SENSITIVE', 'Speed Sensitive', 'Customers prioritizing fast delivery'),
                ('BRAND_SENSITIVE', 'Brand Sensitive', 'Customers focused on original brands'),
                ('CREDIT_RISK', 'Credit Risk', 'Customers with payment issues'),
                ('EXPORT', 'Export Customer', 'International customers'),
                ('LOCAL', 'Local Customer', 'Domestic customers'),
                ('WHOLESALE', 'Wholesale', 'Wholesale traders'),
                ('RETAIL', 'Retail', 'Retail customers'),
                ('SEASONAL', 'Seasonal Buyer', 'Customers with seasonal patterns'),
                ('DECLINING', 'Declining Buyer', 'Customers with reducing purchases'),
                ('GROWING', 'Growing Buyer', 'Customers with increasing purchases'),
            ]
            conn.executemany("""
                INSERT OR IGNORE INTO sales_customer_segments (segment_code, segment_name, description)
                VALUES (?, ?, ?)
            """, default_segments)
            print("  - Inserted default customer segments")
        else:
            print("  - sales_customer_segments already exists")

        # Customer segment assignment
        if not table_exists(conn, 'sales_customer_segment_assignments'):
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sales_customer_segment_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    segment_id INTEGER NOT NULL,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES sales_customers(id),
                    FOREIGN KEY (segment_id) REFERENCES sales_customer_segments(id),
                    UNIQUE(customer_id, segment_id)
                )
            """)
            print("  - Created sales_customer_segment_assignments table")
        else:
            print("  - sales_customer_segment_assignments already exists")

        # =============================================================================
        # ENHANCED SALES SETTINGS
        # =============================================================================
        if not table_exists(conn, 'sales_settings'):
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sales_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            print("  - Created sales_settings table")
        
        # Insert enhanced settings
        enhanced_settings = [
            ('default_currency', 'AED', 'Default currency for sales'),
            ('tax_percent', '5', 'Default tax/VAT percentage'),
            ('max_discount_percent', '20', 'Maximum allowed discount percentage'),
            ('max_discount_sales_executive', '3', 'Maximum discount for Sales Executive'),
            ('max_discount_senior_sales', '5', 'Maximum discount for Senior Sales'),
            ('discount_above_approval_required', '5', 'Discount above this % requires manager approval'),
            ('quotation_validity_days', '30', 'Default quotation validity in days'),
            ('proforma_validity_days', '14', 'Default proforma validity in days'),
            ('confirmation_validity_days', '7', 'Default confirmation validity in days'),
            ('reservation_validity_days', '7', 'Default reservation validity in days'),
            ('min_margin_percent', '10', 'Minimum acceptable margin percentage'),
            ('margin_below_approval_required', '10', 'Margin below this % requires approval'),
            ('credit_check_threshold', '80', 'Credit utilization threshold for alerts (%)'),
            ('auto_convert_inquiry_hours', '24', 'Hours before auto-converting inquiry to opportunity'),
            ('require_approval_above_amount', '50000', 'Order amount requiring approval'),
            ('enable_credit_limit_check', '1', 'Enable customer credit limit check'),
            ('default_payment_terms', 'Net 30', 'Default payment terms'),
            ('enable_alerts', '1', 'Enable sales alerts system'),
            ('alert_inquiry_response_sla_hours', '4', 'Inquiry response SLA in hours'),
            ('alert_quotation_expiry_days', '3', 'Days before quotation expiry to alert'),
            ('alert_proforma_expiry_days', '3', 'Days before proforma expiry to alert'),
            ('alert_reservation_expiry_days', '1', 'Days before reservation expiry to alert'),
            ('alert_customer_debt_threshold', '80', 'Customer debt percentage of credit limit to alert'),
            ('require_customer_po_for_order', '0', 'Require customer PO before creating order'),
            ('require_confirmation_for_order', '0', 'Require confirmation before creating order'),
            ('auto_release_expired_reservations', '1', 'Auto-release reservations past expiry'),
            ('enable_commission_calculation', '0', 'Enable automatic commission calculation'),
            ('default_commission_percent', '2', 'Default commission percentage'),
            ('require_export_documents', '1', 'Require export document checklist for export orders'),
            ('require_incoterrms', '1', 'Require incoterms for export orders'),
        ]
        
        for key, value, desc in enhanced_settings:
            conn.execute("""
                INSERT OR IGNORE INTO sales_settings (setting_key, setting_value, description)
                VALUES (?, ?, ?)
            """, (key, value, desc))
        print("  - Inserted enhanced sales settings")

        # =============================================================================
        # ENHANCED COMPANIES TABLE FOR SALES
        # =============================================================================
        if not column_exists(conn, 'companies', 'sales_enabled'):
            conn.execute("""
                ALTER TABLE companies ADD COLUMN sales_enabled INTEGER DEFAULT 1
            """)
            print("  - Added sales_enabled column to companies table")

        if not column_exists(conn, 'companies', 'default_currency'):
            conn.execute("""
                ALTER TABLE companies ADD COLUMN default_currency TEXT DEFAULT 'AED'
            """)
            print("  - Added default_currency column to companies table")

        # =============================================================================
        # ENHANCED WAREHOUSES TABLE
        # =============================================================================
        if not column_exists(conn, 'warehouses', 'warehouse_type'):
            conn.execute("""
                ALTER TABLE warehouses ADD COLUMN warehouse_type TEXT DEFAULT 'Main'
            """)
            print("  - Added warehouse_type column to warehouses table")

        if not column_exists(conn, 'warehouses', 'supports_sales_allocation'):
            conn.execute("""
                ALTER TABLE warehouses ADD COLUMN supports_sales_allocation INTEGER DEFAULT 1
            """)
            print("  - Added supports_sales_allocation column to warehouses table")

        # =============================================================================
        # CREATE INDEXES FOR NEW TABLES
        # =============================================================================
        new_indexes = [
            ('idx_proforma_number', 'sales_proforma_invoices', 'proforma_number'),
            ('idx_proforma_status', 'sales_proforma_invoices', 'status'),
            ('idx_proforma_customer', 'sales_proforma_invoices', 'customer_id'),
            ('idx_proforma_date', 'sales_proforma_invoices', 'proforma_date'),
            ('idx_cpo_number', 'sales_customer_purchase_orders', 'customer_po_number'),
            ('idx_cpo_status', 'sales_customer_purchase_orders', 'status'),
            ('idx_cpo_customer', 'sales_customer_purchase_orders', 'customer_id'),
            ('idx_cpo_date', 'sales_customer_purchase_orders', 'po_date'),
            ('idx_confirmation_number', 'sales_confirmations', 'confirmation_number'),
            ('idx_confirmation_status', 'sales_confirmations', 'status'),
            ('idx_confirmation_customer', 'sales_confirmations', 'customer_id'),
            ('idx_invoice_number', 'sales_invoices', 'invoice_number'),
            ('idx_invoice_status', 'sales_invoices', 'status'),
            ('idx_invoice_customer', 'sales_invoices', 'customer_id'),
            ('idx_invoice_date', 'sales_invoices', 'invoice_date'),
            ('idx_invoice_payment_status', 'sales_invoices', 'payment_status'),
            ('idx_alerts_type', 'sales_alerts', 'alert_type'),
            ('idx_alerts_status', 'sales_alerts', 'status'),
            ('idx_alerts_priority', 'sales_alerts', 'priority'),
            ('idx_commissions_salesperson', 'sales_commissions', 'salesperson_id'),
            ('idx_commissions_status', 'sales_commissions', 'status'),
        ]

        for idx_name, table, column in new_indexes:
            try:
                conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})")
            except:
                pass
        print("  - Created indexes for new tables")

        # =============================================================================
        # UPDATE SALES_PERMISSIONS FOR NEW MODULES
        # =============================================================================
        try:
            # Add new permission modules
            new_permission_resources = [
                ('sales', 'proforma', ['view', 'create', 'edit', 'delete', 'send', 'convert']),
                ('sales', 'customer_po', ['view', 'create', 'edit', 'review', 'approve', 'convert']),
                ('sales', 'confirmations', ['view', 'create', 'edit', 'send', 'accept', 'convert']),
                ('sales', 'invoices', ['view', 'create', 'edit', 'post', 'cancel', 'print']),
                ('sales', 'alerts', ['view', 'acknowledge', 'resolve']),
                ('sales', 'commissions', ['view', 'calculate', 'approve', 'pay']),
            ]
            
            # Check if role_permissions table exists and has the structure we expect
            if table_exists(conn, 'role_permissions'):
                # Get Sales Manager role
                role_row = conn.execute(
                    "SELECT id FROM roles WHERE role_name = 'Sales Manager'"
                ).fetchone()
                
                if role_row:
                    role_id = role_row['id']
                    
                    for module, resource, actions in new_permission_resources:
                        for action in actions:
                            try:
                                conn.execute("""
                                    INSERT OR IGNORE INTO role_permissions (role_id, module, resource, action)
                                    VALUES (?, ?, ?, ?)
                                """, (role_id, module, resource, action))
                            except:
                                pass
                    print("  - Added new permission resources")
        except Exception as e:
            print(f"  - Note: Could not update permissions: {e}")

        conn.commit()
        print("\nSales Management Suite Extended Migration completed successfully!")
        return True

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == '__main__':
    migrate()
