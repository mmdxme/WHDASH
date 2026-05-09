"""
Sales Management Database Migration
===================================
Creates all tables needed for the Sales Management System.
Run this script once to set up the database schema.

Usage:
    python migrate_sales_tables.py
"""

import sqlite3
import os
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'warehouse.db')


def get_connection():
    """Get a database connection with WAL mode."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def migrate():
    """Run all sales management migrations."""
    print("Starting Sales Management migration...")
    
    conn = get_connection()
    
    try:
        # =============================================================================
        # SALES CUSTOMERS TABLE
        # =============================================================================
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_code TEXT UNIQUE,
                name TEXT NOT NULL,
                trade_name TEXT,
                customer_type TEXT DEFAULT 'Retail',
                market TEXT DEFAULT 'Local',
                country TEXT,
                city TEXT,
                address TEXT,
                phone TEXT,
                whatsapp TEXT,
                email TEXT,
                website TEXT,
                buyer_name TEXT,
                buyer_phone TEXT,
                buyer_email TEXT,
                trade_type TEXT,
                assigned_salesperson_id INTEGER,
                payment_terms TEXT,
                credit_limit REAL DEFAULT 0,
                currency TEXT DEFAULT 'AED',
                default_discount REAL DEFAULT 0,
                price_list_id INTEGER,
                status TEXT DEFAULT 'Active',
                priority TEXT DEFAULT 'Medium',
                total_orders INTEGER DEFAULT 0,
                total_revenue REAL DEFAULT 0,
                outstanding_balance REAL DEFAULT 0,
                last_purchase_date DATE,
                notes TEXT,
                is_active INTEGER DEFAULT 1,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assigned_salesperson_id) REFERENCES users(id),
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        """)
        print("  - Created sales_customers table")

        # Customer transactions table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_customer_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                transaction_date DATE NOT NULL,
                amount REAL NOT NULL,
                reference_type TEXT,
                reference_id INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id)
            )
        """)
        print("  - Created sales_customer_transactions table")

        # =============================================================================
        # SALES INQUIRIES TABLE
        # =============================================================================
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_inquiries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inquiry_number TEXT UNIQUE NOT NULL,
                inquiry_date DATE NOT NULL,
                inquiry_time TEXT,
                customer_id INTEGER,
                customer_name TEXT,
                customer_type TEXT,
                market TEXT,
                country TEXT,
                city TEXT,
                inquiry_source TEXT,
                priority TEXT DEFAULT 'Medium',
                assigned_salesperson_id INTEGER,
                status TEXT DEFAULT 'New',
                urgency TEXT,
                immediate_delivery INTEGER DEFAULT 0,
                specific_brand_required INTEGER DEFAULT 0,
                target_customer_price REAL,
                reason_for_no_response TEXT,
                final_outcome TEXT,
                notes TEXT,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id),
                FOREIGN KEY (assigned_salesperson_id) REFERENCES users(id)
            )
        """)
        print("  - Created sales_inquiries table")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_inquiry_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inquiry_id INTEGER NOT NULL,
                part_number TEXT,
                brand TEXT,
                description TEXT,
                requested_quantity INTEGER DEFAULT 0,
                target_price REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (inquiry_id) REFERENCES sales_inquiries(id)
            )
        """)
        print("  - Created sales_inquiry_lines table")

        # =============================================================================
        # SALES OPPORTUNITIES TABLE
        # =============================================================================
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_opportunities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                opportunity_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                customer_name TEXT,
                assigned_salesperson_id INTEGER,
                source TEXT,
                sales_type TEXT,
                market TEXT,
                customer_type TEXT,
                brand TEXT,
                product_group TEXT,
                estimated_value REAL DEFAULT 0,
                success_probability INTEGER DEFAULT 0,
                expected_close_date DATE,
                stage TEXT DEFAULT 'Identified',
                possible_competitors TEXT,
                deal_risks TEXT,
                customer_requirements TEXT,
                last_activity_date DATE,
                next_step TEXT,
                next_follow_up DATE,
                notes TEXT,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id),
                FOREIGN KEY (assigned_salesperson_id) REFERENCES users(id)
            )
        """)
        print("  - Created sales_opportunities table")

        # =============================================================================
        # SALES QUOTATIONS TABLE
        # =============================================================================
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_quotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quotation_number TEXT UNIQUE NOT NULL,
                quotation_date DATE NOT NULL,
                valid_until DATE,
                customer_id INTEGER,
                customer_name TEXT,
                customer_type TEXT,
                market TEXT,
                assigned_salesperson_id INTEGER,
                currency TEXT DEFAULT 'AED',
                payment_terms TEXT,
                delivery_terms TEXT,
                delivery_location TEXT,
                subtotal REAL DEFAULT 0,
                discount_percent REAL DEFAULT 0,
                discount_amount REAL DEFAULT 0,
                tax_percent REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,
                total_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'Draft',
                source TEXT,
                supply_lead_time TEXT,
                stock_status TEXT,
                attachment_path TEXT,
                notes TEXT,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id),
                FOREIGN KEY (assigned_salesperson_id) REFERENCES users(id)
            )
        """)
        print("  - Created sales_quotations table")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_quotation_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quotation_id INTEGER NOT NULL,
                line_number INTEGER,
                part_number TEXT,
                brand TEXT,
                description TEXT,
                requested_quantity INTEGER DEFAULT 0,
                unit_price REAL DEFAULT 0,
                discount_percent REAL DEFAULT 0,
                discount_amount REAL DEFAULT 0,
                final_price REAL DEFAULT 0,
                supply_lead_time TEXT,
                stock_status TEXT,
                origin TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quotation_id) REFERENCES sales_quotations(id)
            )
        """)
        print("  - Created sales_quotation_lines table")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_quotation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quotation_id INTEGER NOT NULL,
                modified_by INTEGER,
                modification_type TEXT,
                old_values TEXT,
                new_values TEXT,
                notes TEXT,
                modified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quotation_id) REFERENCES sales_quotations(id),
                FOREIGN KEY (modified_by) REFERENCES users(id)
            )
        """)
        print("  - Created sales_quotation_history table")

        # =============================================================================
        # SALES ORDERS TABLE
        # =============================================================================
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL,
                order_date DATE NOT NULL,
                customer_id INTEGER,
                customer_name TEXT,
                customer_type TEXT,
                market TEXT,
                is_export INTEGER DEFAULT 0,
                export_country TEXT,
                incoterm TEXT,
                transport_mode TEXT,
                quotation_id INTEGER,
                assigned_salesperson_id INTEGER,
                currency TEXT DEFAULT 'AED',
                payment_terms TEXT,
                delivery_terms TEXT,
                delivery_address TEXT,
                shipment_type TEXT,
                subtotal REAL DEFAULT 0,
                discount_percent REAL DEFAULT 0,
                discount_amount REAL DEFAULT 0,
                tax_percent REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,
                total_amount REAL DEFAULT 0,
                status TEXT DEFAULT 'Registered',
                priority TEXT DEFAULT 'Medium',
                promised_delivery_date DATE,
                actual_delivery_date DATE,
                notes TEXT,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id),
                FOREIGN KEY (quotation_id) REFERENCES sales_quotations(id),
                FOREIGN KEY (assigned_salesperson_id) REFERENCES users(id)
            )
        """)
        print("  - Created sales_orders table")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_order_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                line_number INTEGER,
                part_number TEXT,
                brand TEXT,
                description TEXT,
                ordered_quantity INTEGER DEFAULT 0,
                available_quantity INTEGER DEFAULT 0,
                shortage_quantity INTEGER DEFAULT 0,
                unit_price REAL DEFAULT 0,
                discount_percent REAL DEFAULT 0,
                discount_amount REAL DEFAULT 0,
                final_price REAL DEFAULT 0,
                tax_percent REAL DEFAULT 0,
                tax_amount REAL DEFAULT 0,
                line_total REAL DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES sales_orders(id)
            )
        """)
        print("  - Created sales_order_lines table")

        # =============================================================================
        # SALES RESERVATIONS TABLE
        # =============================================================================
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reservation_number TEXT UNIQUE NOT NULL,
                reservation_date DATE NOT NULL,
                customer_id INTEGER,
                reference_type TEXT,
                reference_id INTEGER,
                order_id INTEGER,
                quotation_id INTEGER,
                part_number TEXT,
                brand TEXT,
                warehouse_id INTEGER,
                reserved_quantity INTEGER NOT NULL,
                available_quantity_at_reservation INTEGER,
                expiry_date DATE,
                reservation_reason TEXT,
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'Active',
                assigned_salesperson_id INTEGER,
                approver_id INTEGER,
                released_at TIMESTAMP,
                release_reason TEXT,
                notes TEXT,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id),
                FOREIGN KEY (order_id) REFERENCES sales_orders(id),
                FOREIGN KEY (quotation_id) REFERENCES sales_quotations(id),
                FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
                FOREIGN KEY (assigned_salesperson_id) REFERENCES users(id),
                FOREIGN KEY (approver_id) REFERENCES users(id)
            )
        """)
        print("  - Created sales_reservations table")

        # =============================================================================
        # SALES DELIVERIES TABLE
        # =============================================================================
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_deliveries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                delivery_number TEXT UNIQUE NOT NULL,
                order_id INTEGER,
                customer_id INTEGER,
                delivery_type TEXT DEFAULT 'Delivery',
                delivery_location TEXT,
                requested_date DATE,
                requested_time TEXT,
                coordinator_id INTEGER,
                vehicle_id INTEGER,
                driver_id INTEGER,
                status TEXT DEFAULT 'Pending',
                preparation_status TEXT DEFAULT 'Waiting for Packing',
                transport_status TEXT DEFAULT 'Pending',
                actual_departure_time TIMESTAMP,
                actual_arrival_time TIMESTAMP,
                notes TEXT,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES sales_orders(id),
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id),
                FOREIGN KEY (coordinator_id) REFERENCES users(id),
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id),
                FOREIGN KEY (driver_id) REFERENCES drivers(id)
            )
        """)
        print("  - Created sales_deliveries table")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_delivery_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                delivery_id INTEGER NOT NULL,
                order_id INTEGER,
                order_line_id INTEGER,
                part_number TEXT,
                brand TEXT,
                description TEXT,
                quantity INTEGER DEFAULT 0,
                weight REAL,
                volume REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (delivery_id) REFERENCES sales_deliveries(id),
                FOREIGN KEY (order_id) REFERENCES sales_orders(id),
                FOREIGN KEY (order_line_id) REFERENCES sales_order_lines(id)
            )
        """)
        print("  - Created sales_delivery_lines table")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_delivery_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                delivery_id INTEGER NOT NULL,
                document_type TEXT,
                document_number TEXT,
                document_path TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (delivery_id) REFERENCES sales_deliveries(id)
            )
        """)
        print("  - Created sales_delivery_documents table")

        # =============================================================================
        # SALES RETURNS TABLE
        # =============================================================================
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_number TEXT UNIQUE NOT NULL,
                return_date DATE NOT NULL,
                customer_id INTEGER,
                order_id INTEGER,
                invoice_id INTEGER,
                part_number TEXT,
                brand TEXT,
                returned_quantity INTEGER DEFAULT 0,
                item_condition TEXT,
                return_reason TEXT,
                inspection_required INTEGER DEFAULT 0,
                reviewer_id INTEGER,
                review_result TEXT,
                final_decision TEXT,
                financial_impact REAL DEFAULT 0,
                status TEXT DEFAULT 'New',
                closure_status TEXT DEFAULT 'Open',
                notes TEXT,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id),
                FOREIGN KEY (order_id) REFERENCES sales_orders(id),
                FOREIGN KEY (reviewer_id) REFERENCES users(id)
            )
        """)
        print("  - Created sales_returns table")

        # =============================================================================
        # SALES TARGETS TABLE
        # =============================================================================
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_targets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                salesperson_id INTEGER NOT NULL,
                period TEXT DEFAULT 'Monthly',
                year INTEGER,
                quarter INTEGER,
                month INTEGER,
                target_amount REAL DEFAULT 0,
                target_quantity INTEGER DEFAULT 0,
                new_customer_target INTEGER DEFAULT 0,
                reactivation_target INTEGER DEFAULT 0,
                brand_target TEXT,
                product_group_target TEXT,
                local_target REAL DEFAULT 0,
                export_target REAL DEFAULT 0,
                weight_amount REAL DEFAULT 100,
                weight_quantity REAL DEFAULT 0,
                weight_new_customers REAL DEFAULT 0,
                weight_reactivation REAL DEFAULT 0,
                status TEXT DEFAULT 'Active',
                notes TEXT,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (salesperson_id) REFERENCES users(id)
            )
        """)
        print("  - Created sales_targets table")

        # =============================================================================
        # SALES CONTRACTS TABLE
        # =============================================================================
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contract_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                start_date DATE,
                end_date DATE,
                contract_type TEXT,
                product_group TEXT,
                brand TEXT,
                pricing_terms TEXT,
                payment_terms TEXT,
                delivery_terms TEXT,
                volume_commitment TEXT,
                agreed_discounts TEXT,
                sla_terms TEXT,
                attachment_path TEXT,
                contract_owner_id INTEGER,
                status TEXT DEFAULT 'Active',
                notes TEXT,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id),
                FOREIGN KEY (contract_owner_id) REFERENCES users(id)
            )
        """)
        print("  - Created sales_contracts table")

        # =============================================================================
        # SALES ACTIVITIES TABLE
        # =============================================================================
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                activity_type TEXT NOT NULL,
                activity_date DATE NOT NULL,
                activity_time TEXT,
                customer_id INTEGER,
                owner_id INTEGER NOT NULL,
                subject TEXT,
                result TEXT,
                next_action TEXT,
                next_follow_up_date DATE,
                status TEXT DEFAULT 'Completed',
                notes TEXT,
                reference_type TEXT,
                reference_id INTEGER,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id),
                FOREIGN KEY (owner_id) REFERENCES users(id)
            )
        """)
        print("  - Created sales_activities table")

        # =============================================================================
        # PRICE LISTS TABLE
        # =============================================================================
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_price_lists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price_list_type TEXT DEFAULT 'Standard',
                currency TEXT DEFAULT 'AED',
                discount_percent REAL DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                valid_from DATE,
                valid_until DATE,
                notes TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        print("  - Created sales_price_lists table")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_price_list_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                price_list_id INTEGER NOT NULL,
                part_number TEXT NOT NULL,
                brand TEXT,
                unit_price REAL NOT NULL,
                discount_percent REAL DEFAULT 0,
                final_price REAL,
                valid_from DATE,
                valid_until DATE,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (price_list_id) REFERENCES sales_price_lists(id)
            )
        """)
        print("  - Created sales_price_list_items table")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_special_prices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                part_number TEXT NOT NULL,
                brand TEXT,
                quantity INTEGER DEFAULT 1,
                price REAL NOT NULL,
                discount_percent REAL DEFAULT 0,
                valid_from DATE,
                valid_until DATE,
                is_active INTEGER DEFAULT 1,
                approved INTEGER DEFAULT 0,
                approved_by INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id),
                FOREIGN KEY (approved_by) REFERENCES users(id)
            )
        """)
        print("  - Created sales_special_prices table")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS sales_special_price_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                salesperson_id INTEGER,
                part_number TEXT,
                brand TEXT,
                quantity INTEGER DEFAULT 1,
                standard_price REAL,
                proposed_price REAL,
                requested_discount REAL,
                reason TEXT,
                urgency TEXT DEFAULT 'Normal',
                status TEXT DEFAULT 'Pending',
                approved_price REAL,
                approved_by INTEGER,
                approval_date DATE,
                notes TEXT,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id),
                FOREIGN KEY (salesperson_id) REFERENCES users(id),
                FOREIGN KEY (approved_by) REFERENCES users(id)
            )
        """)
        print("  - Created sales_special_price_requests table")

        # =============================================================================
        # SALES SETTINGS TABLE
        # =============================================================================
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

        # Insert default settings
        default_settings = [
            ('default_currency', 'AED', 'Default currency for sales'),
            ('tax_percent', '5', 'Default tax/VAT percentage'),
            ('max_discount_percent', '20', 'Maximum allowed discount percentage'),
            ('quotation_validity_days', '30', 'Default quotation validity in days'),
            ('reservation_validity_days', '7', 'Default reservation validity in days'),
            ('min_margin_percent', '10', 'Minimum acceptable margin percentage'),
            ('credit_check_threshold', '80', 'Credit utilization threshold for alerts (%)'),
            ('auto_convert_inquiry_hours', '24', 'Hours before auto-converting inquiry to opportunity'),
            ('require_approval_above_amount', '50000', 'Order amount requiring approval'),
            ('enable_credit_limit_check', '1', 'Enable customer credit limit check'),
            ('default_payment_terms', 'Net 30', 'Default payment terms'),
        ]

        for key, value, desc in default_settings:
            conn.execute("""
                INSERT OR IGNORE INTO sales_settings (setting_key, setting_value, description)
                VALUES (?, ?, ?)
            """, (key, value, desc))
        print("  - Inserted default sales settings")

        # =============================================================================
        # CREATE INDEXES
        # =============================================================================
        indexes = [
            ('idx_sales_customers_code', 'sales_customers', 'customer_code'),
            ('idx_sales_customers_name', 'sales_customers', 'name'),
            ('idx_sales_customers_status', 'sales_customers', 'status'),
            ('idx_sales_inquiries_number', 'sales_inquiries', 'inquiry_number'),
            ('idx_sales_inquiries_status', 'sales_inquiries', 'status'),
            ('idx_sales_inquiries_date', 'sales_inquiries', 'inquiry_date'),
            ('idx_sales_opportunities_number', 'sales_opportunities', 'opportunity_number'),
            ('idx_sales_opportunities_stage', 'sales_opportunities', 'stage'),
            ('idx_sales_quotations_number', 'sales_quotations', 'quotation_number'),
            ('idx_sales_quotations_status', 'sales_quotations', 'status'),
            ('idx_sales_orders_number', 'sales_orders', 'order_number'),
            ('idx_sales_orders_status', 'sales_orders', 'status'),
            ('idx_sales_orders_date', 'sales_orders', 'order_date'),
            ('idx_sales_reservations_number', 'sales_reservations', 'reservation_number'),
            ('idx_sales_reservations_status', 'sales_reservations', 'status'),
            ('idx_sales_deliveries_number', 'sales_deliveries', 'delivery_number'),
            ('idx_sales_returns_number', 'sales_returns', 'return_number'),
            ('idx_sales_activities_date', 'sales_activities', 'activity_date'),
            ('idx_sales_customer_transactions', 'sales_customer_transactions', 'customer_id'),
        ]

        for idx_name, table, column in indexes:
            try:
                conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})")
            except:
                pass
        print("  - Created indexes")

        # =============================================================================
        # ADD SALES PERMISSIONS
        # =============================================================================
        try:
            from permissions import add_permission_to_role, _role_exists, get_role_by_id

            # Add sales permissions to Sales Manager role
            if _role_exists('Sales Manager'):
                role = get_role_by_id(None)
                # We need to get the role id first
                role_row = conn.execute("SELECT id FROM roles WHERE role_name = 'Sales Manager'").fetchone()
                if role_row:
                    role_id = role_row['id']

                    sales_permissions = [
                        ('sales', 'dashboard', 'view'),
                        ('sales', 'customers', 'view'),
                        ('sales', 'customers', 'create'),
                        ('sales', 'customers', 'edit'),
                        ('sales', 'inquiries', 'view'),
                        ('sales', 'inquiries', 'create'),
                        ('sales', 'inquiries', 'edit'),
                        ('sales', 'opportunities', 'view'),
                        ('sales', 'opportunities', 'create'),
                        ('sales', 'opportunities', 'edit'),
                        ('sales', 'quotations', 'view'),
                        ('sales', 'quotations', 'create'),
                        ('sales', 'quotations', 'edit'),
                        ('sales', 'quotations', 'approve'),
                        ('sales', 'quotations', 'send'),
                        ('sales', 'orders', 'view'),
                        ('sales', 'orders', 'create'),
                        ('sales', 'orders', 'edit'),
                        ('sales', 'orders', 'approve'),
                        ('sales', 'orders', 'fulfill'),
                        ('sales', 'reservations', 'view'),
                        ('sales', 'reservations', 'create'),
                        ('sales', 'reservations', 'edit'),
                        ('sales', 'reservations', 'approve'),
                        ('sales', 'deliveries', 'view'),
                        ('sales', 'deliveries', 'create'),
                        ('sales', 'deliveries', 'edit'),
                        ('sales', 'returns', 'view'),
                        ('sales', 'returns', 'create'),
                        ('sales', 'returns', 'edit'),
                        ('sales', 'targets', 'view'),
                        ('sales', 'targets', 'create'),
                        ('sales', 'targets', 'edit'),
                        ('sales', 'contracts', 'view'),
                        ('sales', 'contracts', 'create'),
                        ('sales', 'contracts', 'edit'),
                        ('sales', 'activities', 'view'),
                        ('sales', 'activities', 'create'),
                        ('sales', 'activities', 'edit'),
                        ('sales', 'pricing', 'view'),
                        ('sales', 'pricing', 'create'),
                        ('sales', 'pricing', 'edit'),
                        ('sales', 'sales_reports', 'view'),
                        ('sales', 'sales_reports', 'export'),
                        ('sales', 'settings', 'view'),
                        ('sales', 'settings', 'edit'),
                    ]

                    for module, resource, action in sales_permissions:
                        conn.execute("""
                            INSERT OR IGNORE INTO role_permissions (role_id, module, resource, action)
                            VALUES (?, ?, ?, ?)
                        """, (role_id, module, resource, action))
            print("  - Added sales permissions to Sales Manager role")
        except Exception as e:
            print(f"  - Note: Could not add permissions (permissions module may not be loaded): {e}")

        conn.commit()
        print("\nSales Management migration completed successfully!")
        return True

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
        return False

    finally:
        conn.close()


if __name__ == '__main__':
    migrate()
