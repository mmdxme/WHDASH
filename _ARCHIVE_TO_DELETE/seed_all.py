"""
Unified Demo Data Seeder for MMDx
===================================
This is the master seeding script that orchestrates all module-specific
seed scripts to ensure comprehensive demo data coverage across the entire platform.

This script:
- Runs all seed scripts in proper dependency order
- Provides idempotent seeding (safe to run multiple times)
- Reports progress and coverage status
- Can be used for initial setup or reseeding

Usage:
    python seed_all.py              # Run all seeds
    python seed_all.py --status    # Check coverage status
    python seed_all.py --module hr # Seed only HR module
    python seed_all.py --reset     # Reset and reseed everything

Author: MMDx Data Seeding System
"""

import os
import sys
import sqlite3
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Database path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'warehouse.db')

# Fix UTF-8 encoding on Windows for emoji support
try:
    import sys
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')
except:
    pass


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{'=' * 60}")
    print(f"  {text}")
    print(f"{'=' * 60}")


def print_step(text: str):
    """Print a formatted step."""
    print(f"\n>> {text}...")


def count_rows(table: str, db=None) -> int:
    """Count rows in a table."""
    if db is None:
        db = get_db()
    try:
        result = db.execute(f"SELECT COUNT(*) as cnt FROM {table}").fetchone()
        return result['cnt'] if result else 0
    except:
        return 0


def table_exists(table: str, db=None) -> bool:
    """Check if a table exists."""
    if db is None:
        db = get_db()
    result = db.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    ).fetchone()
    return result is not None


# =============================================================================
# MODULE SEED FUNCTIONS
# =============================================================================

def seed_core_base():
    """Seed core base data (users, companies, roles)."""
    print_step("Seeding core base data")
    
    try:
        from seed_sample_data import seed_data as seed_core
        seed_core()
        print("  ✓ Core base data seeded")
    except Exception as e:
        print(f"  ✗ Core base seed error: {e}")
        # Fallback: ensure basic users exist
        _seed_fallback_users()


def _seed_fallback_users():
    """Fallback for basic user seeding if seed_sample_data fails."""
    db = get_db()
    cursor = db.cursor()
    
    user_count = count_rows('users', db)
    if user_count < 3:
        print("  Seeding fallback users...")
        import hashlib
        
        users = [
            ('admin', 'admin@warehouse.local', 'Administrator', 'admin123', 1),
            ('demo', 'demo@warehouse.local', 'Demo User', 'demo123', 2),
            ('manager', 'manager@warehouse.local', 'Manager User', 'manager123', 3),
        ]
        
        for username, email, name, password, role_id in users:
            try:
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                cursor.execute("""
                    INSERT OR IGNORE INTO users (username, email, full_name, password, role_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username, email, name, password_hash, role_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            except:
                pass
        
        db.commit()
        print("  ✓ Fallback users created")


def seed_hr_data():
    """Seed HR module data."""
    print_step("Seeding HR module data")
    
    try:
        from seed_sample_data import seed_data as seed_hr
        seed_hr()
        print("  ✓ HR data seeded (from seed_sample_data)")
    except Exception as e:
        print(f"  Note: {e}")
    
    # Seed additional HR data (loans, bonuses, deductions)
    _seed_hr_extended()


def _seed_hr_extended():
    """Seed extended HR data (loans, bonuses, deductions, payroll)."""
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Check if hr_loans table exists
        if not table_exists('hr_loans', db):
            print("  - hr_loans table not found, skipping loans")
            return
            
        # Check if already seeded
        loan_count = count_rows('hr_loans', db)
        if loan_count > 5:
            print("  - HR loans already exist")
            return
            
        print("  Seeding HR loans...")
        
        # Get employees
        cursor.execute("SELECT id FROM hr_employees LIMIT 10")
        emp_ids = [r['id'] for r in cursor.fetchall()]
        
        if not emp_ids:
            print("  - No employees found, skipping loans")
            return
        
        loan_data = [
            (emp_ids[0], 15000, 'Personal Loan', 'Active', 12, 1250),
            (emp_ids[1], 8000, 'Emergency Loan', 'Active', 6, 1333),
            (emp_ids[2], 25000, 'Home Loan', 'Active', 36, 694),
            (emp_ids[3], 5000, 'Education Loan', 'Closed', 12, 417),
        ]
        
        for emp_id, amount, ltype, status, months, monthly_payment in loan_data:
            start_date = (datetime.now() - timedelta(days=random.randint(30, 300))).strftime('%Y-%m-%d')
            cursor.execute("""
                INSERT INTO hr_loans (employee_id, loan_type, principal_amount, approved_amount,
                    interest_rate, tenure_months, monthly_payment, status, application_date,
                    approval_date, start_date, end_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                emp_id, ltype, amount, amount, 0.05, months, monthly_payment, status,
                start_date, start_date, start_date,
                (datetime.now() + timedelta(days=months * 30)).strftime('%Y-%m-%d'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
        
        db.commit()
        print("  ✓ HR loans seeded")
        
        # Seed HR bonuses
        bonus_count = count_rows('hr_bonus_records', db)
        if bonus_count < 5:
            print("  Seeding HR bonuses...")
            
            bonus_types = ['Performance Bonus', 'Year-End Bonus', 'Project Bonus', 'Retention Bonus']
            
            for emp_id in emp_ids[:5]:
                for i, btype in enumerate(bonus_types[:2]):
                    cursor.execute("""
                        INSERT INTO hr_bonus_records (employee_id, bonus_type, amount, 
                            bonus_date, reason, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        emp_id, btype, random.uniform(500, 5000),
                        (datetime.now() - timedelta(days=random.randint(30, 300))).strftime('%Y-%m-%d'),
                        f'Bonus for {datetime.now().year}', 'Approved',
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ))
            
            db.commit()
            print("  ✓ HR bonuses seeded")
        
        # Seed HR deductions
        ded_count = count_rows('hr_deduction_records', db)
        if ded_count < 5:
            print("  Seeding HR deductions...")
            
            ded_types = ['Late Attendance', 'Absence', 'Loan Repayment', 'Equipment Damage']
            
            for emp_id in emp_ids[:5]:
                for i, dtype in enumerate(ded_types[:2]):
                    cursor.execute("""
                        INSERT INTO hr_deduction_records (employee_id, deduction_type, amount,
                            deduction_date, reason, status, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        emp_id, dtype, random.uniform(50, 500),
                        (datetime.now() - timedelta(days=random.randint(1, 60))).strftime('%Y-%m-%d'),
                        f'Deduction reason {i+1}', 'Approved',
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ))
            
            db.commit()
            print("  ✓ HR deductions seeded")
            
    except Exception as e:
        print(f"  Note on HR extended data: {e}")


def seed_wms_data():
    """Seed WMS/warehouse data."""
    print_step("Seeding WMS module data")
    
    try:
        from seed_data import seed
        seed()
        print("  ✓ WMS base data seeded")
    except Exception as e:
        print(f"  Note: {e}")
    
    try:
        from seed_wms_extended_data import seed_wms_extended_data
        seed_wms_extended_data()
        print("  ✓ WMS extended data seeded")
    except Exception as e:
        print(f"  Note: {e}")


def seed_procurement_data():
    """Seed Procurement module data."""
    print_step("Seeding Procurement module data")
    
    try:
        from seed_procurement_data import seed_procurement_data
        seed_procurement_data()
        print("  ✓ Procurement data seeded")
    except Exception as e:
        print(f"  ✗ Procurement seed error: {e}")


def seed_sales_data():
    """Seed Sales module data."""
    print_step("Seeding Sales module data")
    
    try:
        from seed_sample_data import seed_data
        # Sales data is part of seed_sample_data
        print("  - Sales data included in core seeds")
    except Exception as e:
        print(f"  Note: {e}")
    
    # Seed additional sales data if table exists
    _seed_sales_extended()


def _seed_sales_extended():
    """Seed extended sales data (inquiries, opportunities, quotations, orders)."""
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Check if sales tables exist
        if not table_exists('sales_customers', db):
            print("  - Sales tables not found")
            return
        
        # Seed customers if empty
        cust_count = count_rows('sales_customers', db)
        if cust_count < 5:
            print("  Seeding sales customers...")
            
            customers = [
                ('Al Futtaim Group', 'AFG-001', 'Enterprise', 'Active'),
                ('Emirates Trading LLC', 'ETL-001', 'Corporate', 'Active'),
                ('Al Shirawi Group', 'ASG-001', 'Enterprise', 'Active'),
                ('Al Ghurair Foods', 'AGF-001', 'Corporate', 'Active'),
                ('Dubai Customs', 'DC-001', 'Government', 'Active'),
                ('Shawka Engineering', 'SE-001', 'SMB', 'Active'),
                ('Gulf Medical University', 'GMU-001', 'Education', 'Active'),
                ('Al Ain Dairy', 'AAD-001', 'Corporate', 'Active'),
            ]
            
            for name, code, cust_type, status in customers:
                cursor.execute("""
                    INSERT INTO sales_customers (customer_code, customer_name, customer_type,
                        industry, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (code, name, cust_type, 'General', status, 
                      datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            db.commit()
            print("  ✓ Sales customers seeded")
        
        # Seed inquiries
        inq_count = count_rows('sales_inquiries', db)
        if inq_count < 10:
            print("  Seeding sales inquiries...")
            
            subjects = [
                'Request for industrial filters quotation',
                'Brake pads for fleet maintenance',
                'Suspension parts inquiry for Toyota models',
                'Electrical components bulk order',
                'Engine oil supply contract',
                'Regular maintenance parts supply',
                'Custom parts fabrication request',
                'Emergency parts procurement',
            ]
            
            statuses = ['New', 'Contacted', 'Quoted', 'Negotiating', 'Closed Won', 'Closed Lost']
            
            for i, subject in enumerate(subjects):
                cursor.execute("""
                    INSERT INTO sales_inquiries (inquiry_number, customer_id, subject,
                        description, priority, status, inquiry_date, created_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f'INQ-2026-{i+1:04d}',
                    random.randint(1, cust_count) if cust_count > 0 else 1,
                    subject,
                    f'Description for {subject}',
                    random.choice(['Low', 'Medium', 'High', 'Urgent']),
                    random.choice(statuses),
                    (datetime.now() - timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d'),
                    1,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
            
            db.commit()
            print("  ✓ Sales inquiries seeded")
        
        # Seed quotations
        quo_count = count_rows('sales_quotations', db)
        if quo_count < 5:
            print("  Seeding sales quotations...")
            
            for i in range(8):
                quo_date = (datetime.now() - timedelta(days=random.randint(1, 60))).strftime('%Y-%m-%d')
                expiry = (datetime.strptime(quo_date, '%Y-%m-%d') + timedelta(days=30)).strftime('%Y-%m-%d')
                
                cursor.execute("""
                    INSERT INTO sales_quotations (quotation_number, customer_id, quotation_date,
                        expiry_date, status, total_amount, currency, created_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f'QT-2026-{i+1:04d}',
                    random.randint(1, cust_count) if cust_count > 0 else 1,
                    quo_date,
                    expiry,
                    random.choice(['Draft', 'Sent', 'Reviewed', 'Accepted', 'Rejected']),
                    random.uniform(5000, 150000),
                    'AED',
                    1,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
            
            db.commit()
            print("  ✓ Sales quotations seeded")
            
    except Exception as e:
        print(f"  Note on sales extended data: {e}")


def seed_finance_data():
    """Seed Finance module data."""
    print_step("Seeding Finance module data")

    try:
        # seed_finance_data.py has a main() function, not seed_finance_data()
        import seed_finance_data as sfd
        if hasattr(sfd, 'main'):
            sfd.main()
        else:
            # Fallback: directly seed using the functions
            from seed_finance_data import seed_account_categories, seed_chart_of_accounts, seed_fiscal_years
            from seed_finance_data import seed_tax_codes, seed_cost_centers, seed_journal_entries
            from seed_finance_data import seed_ar_invoices, seed_ap_bills, seed_fixed_assets, seed_budgets
            from seed_finance_data import get_connection, initialize_finance_schema

            conn = get_connection()
            seed_account_categories(conn)
            seed_chart_of_accounts(conn)
            seed_fiscal_years(conn)
            seed_tax_codes(conn)
            seed_cost_centers(conn)
            seed_journal_entries(conn)
            seed_ar_invoices(conn)
            seed_ap_bills(conn)
            seed_fixed_assets(conn)
            seed_budgets(conn)
            conn.close()
        print("  ✓ Finance data seeded")
    except Exception as e:
        print(f"  ✗ Finance seed error: {e}")


def seed_quality_data():
    """Seed Quality module data."""
    print_step("Seeding Quality module data")
    
    try:
        from seed_quality_data import seed_quality_data
        seed_quality_data()
        print("  ✓ Quality data seeded")
    except Exception as e:
        print(f"  ✗ Quality seed error: {e}")


def seed_maintenance_data():
    """Seed Maintenance module data."""
    print_step("Seeding Maintenance module data")
    
    try:
        from seed_maintenance_data import seed_maintenance_data
        seed_maintenance_data()
        print("  ✓ Maintenance data seeded")
    except Exception as e:
        print(f"  ✗ Maintenance seed error: {e}")


def seed_asset_data():
    """Seed Asset module data."""
    print_step("Seeding Asset module data")
    
    try:
        from seed_asset_data import seed_asset_data
        seed_asset_data()
        print("  ✓ Asset data seeded")
    except Exception as e:
        print(f"  ✗ Asset seed error: {e}")


def seed_logistics_data():
    """Seed Logistics module data."""
    print_step("Seeding Logistics module data")
    
    try:
        from seed_logistics_data import seed_logistics_data
        seed_logistics_data()
        print("  ✓ Logistics data seeded")
    except Exception as e:
        print(f"  ✗ Logistics seed error: {e}")


def seed_ecommerce_data():
    """Seed E-commerce module data."""
    print_step("Seeding E-commerce module data")

    try:
        import seed_ecommerce_data as sed
        if hasattr(sed, 'main'):
            sed.main()
        else:
            # Call individual functions that exist
            from seed_ecommerce_data import seed_channels, seed_customers, seed_orders
            from seed_ecommerce_data import seed_exceptions, seed_inventory_syncs, seed_product_mappings
            from seed_ecommerce_data import seed_sync_jobs, seed_audit_logs, seed_settings

            seed_channels()
            seed_customers()
            seed_orders()
            seed_exceptions()
            seed_inventory_syncs()
            seed_product_mappings()
            seed_sync_jobs()
            seed_audit_logs()
            seed_settings()
        print("  ✓ E-commerce data seeded")
    except Exception as e:
        print(f"  ✗ E-commerce seed error: {e}")


def seed_document_data():
    """Seed Document module data."""
    print_step("Seeding Document module data")
    
    try:
        from seed_document_data import seed_document_demo_data
        seed_document_demo_data()
        print("  ✓ Document data seeded")
    except Exception as e:
        print(f"  ✗ Document seed error: {e}")


def seed_workflow_data():
    """Seed Workflow module data."""
    print_step("Seeding Workflow module data")
    
    try:
        from seed_workflow_data import seed_workflow_data
        seed_workflow_data()
        print("  ✓ Workflow data seeded")
    except Exception as e:
        print(f"  ✗ Workflow seed error: {e}")


def seed_api_gateway_data():
    """Seed API Gateway module data."""
    print_step("Seeding API Gateway module data")
    
    try:
        from seed_api_gateway_data import seed
        seed()
        print("  ✓ API Gateway data seeded")
    except Exception as e:
        print(f"  ✗ API Gateway seed error: {e}")


def seed_bi_data():
    """Seed BI/Reporting module data."""
    print_step("Seeding BI module data")

    try:
        import seed_bi_data as sb
        if hasattr(sb, 'main'):
            sb.main()
        else:
            # Call individual functions that exist
            from seed_bi_data import seed_datasets, seed_dataset_fields, seed_kpis
            from seed_bi_data import seed_sample_reports, seed_sample_queries, seed_sample_schedules
            from seed_bi_data import seed_sample_logs

            seed_datasets()
            seed_dataset_fields(None)  # datasets parameter optional or mocked
            seed_kpis()
            seed_sample_reports(None)
            seed_sample_queries(None)
            seed_sample_schedules(None)
            seed_sample_logs()
        print("  ✓ BI data seeded")
    except Exception as e:
        print(f"  ✗ BI seed error: {e}")


def seed_marketing_data():
    """Seed Marketing module data."""
    print_step("Seeding Marketing module data")

    try:
        import seed_marketing_data as smd
        smd.seed_marketing_data()
        print("  ✓ Marketing data seeded")
    except Exception as e:
        print(f"  ✗ Marketing seed error: {e}")


def seed_social_media_data():
    """Seed Social Media module data."""
    print_step("Seeding Social Media module data")

    try:
        import seed_social_media_data as ssmd
        ssmd.seed_social_media_data()
        print("  ✓ Social Media data seeded")
    except Exception as e:
        print(f"  ✗ Social media seed error: {e}")


def seed_company_data():
    """Seed Company module data."""
    print_step("Seeding Company module data")
    
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Check if companies exist
        comp_count = count_rows('companies', db)
        if comp_count > 0:
            print("  - Companies already exist")
            return
        
        print("  Seeding companies...")
        companies = [
            ('MMDx Holding', 'WH', 'Parent holding company', 'Active'),
            ('MMDx SDAD', 'SDAD', 'SDAD subsidiary', 'Active'),
            ('MMDx AFRA', 'AFRA', 'AFRA subsidiary', 'Active'),
            ('MMDx Carmania', 'CRM', 'Carmania subsidiary', 'Active'),
        ]
        
        for name, code, desc, status in companies:
            cursor.execute("""
                INSERT INTO companies (name, code, description, status, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (name, code, desc, status, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        db.commit()
        print("  ✓ Companies seeded")
        
    except Exception as e:
        print(f"  ✗ Company seed error: {e}")


# =============================================================================
# COVERAGE STATUS
# =============================================================================

def show_coverage_status():
    """Show demo data coverage status for all modules."""
    print_header("DEMO DATA COVERAGE STATUS")
    
    db = get_db()
    
    modules = [
        ('HR', ['hr_employees', 'hr_departments', 'hr_attendance_records', 'hr_leave_requests']),
        ('WMS', ['parts', 'inventory', 'warehouses']),
        ('Procurement', ['suppliers', 'procurement_requisitions', 'purchase_orders']),
        ('Sales', ['sales_customers', 'sales_inquiries', 'sales_quotations', 'sales_orders']),
        ('Finance', ['finance_accounts', 'customer_invoices', 'supplier_bills']),
        ('Quality', ['quality_inspections', 'quality_non_conformances', 'quality_capa_records']),
        ('Maintenance', ['maintenance_facilities', 'maintenance_work_orders']),
        ('Assets', ['assets', 'asset_categories']),
        ('Logistics', ['logistics_vehicles', 'logistics_drivers', 'delivery_trips']),
        ('E-commerce', ['ecommerce_channels', 'ecommerce_orders']),
        ('Documents', ['documents', 'document_categories']),
        ('Workflow', ['workflow_definitions', 'workflow_instances']),
        ('API Gateway', ['api_clients', 'integration_profiles']),
        ('BI', ['reporting_datasets', 'reporting_kpis']),
        ('Marketing', ['marketing_brands', 'marketing_campaigns', 'marketing_leads']),
        ('Social Media', ['social_accounts', 'social_campaigns', 'social_leads']),
    ]
    
    total_checks = 0
    total_rows = 0
    
    for module_name, tables in modules:
        print(f"\n{module_name}:")
        module_total = 0
        for table in tables:
            count = count_rows(table, db)
            status = "[OK]" if count > 0 else "[MISSING]"
            print(f"  {status} {table}: {count} rows")
            module_total += count
        
        total_rows += module_total
    
    print(f"\n{'=' * 60}")
    print(f"Total data coverage: {total_rows} rows across all modules")
    print(f"{'=' * 60}")


# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================

def seed_all():
    """Run all seed scripts in proper order."""
    print_header("MMDx UNIFIED DEMO DATA SEEDER")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Core first (dependencies)
    seed_company_data()
    seed_core_base()
    
    # Then modules
    seed_hr_data()
    seed_wms_data()
    seed_procurement_data()
    seed_sales_data()
    seed_finance_data()
    seed_quality_data()
    seed_maintenance_data()
    seed_asset_data()
    seed_logistics_data()
    seed_ecommerce_data()
    seed_document_data()
    seed_workflow_data()
    seed_api_gateway_data()
    seed_bi_data()
    seed_marketing_data()
    seed_social_media_data()
    
    print_header("SEEDING COMPLETE")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nRun with --status to check coverage.")


# =============================================================================
# CLI
# =============================================================================

if __name__ == '__main__':
    import random  # For random data generation
    
    parser = argparse.ArgumentParser(description='MMDx Demo Data Seeder')
    parser.add_argument('--status', action='store_true', help='Show coverage status')
    parser.add_argument('--module', type=str, help='Seed specific module only')
    parser.add_argument('--reset', action='store_true', help='Reset database and reseed')
    
    args = parser.parse_args()
    
    if args.status:
        show_coverage_status()
    elif args.module:
        module_funcs = {
            'hr': seed_hr_data,
            'wms': seed_wms_data,
            'procurement': seed_procurement_data,
            'sales': seed_sales_data,
            'finance': seed_finance_data,
            'quality': seed_quality_data,
            'maintenance': seed_maintenance_data,
            'asset': seed_asset_data,
            'logistics': seed_logistics_data,
            'ecommerce': seed_ecommerce_data,
            'document': seed_document_data,
            'workflow': seed_workflow_data,
            'api': seed_api_gateway_data,
            'bi': seed_bi_data,
            'marketing': seed_marketing_data,
            'social': seed_social_media_data,
        }
        
        if args.module.lower() in module_funcs:
            print_header(f"Seeding {args.module.upper()} module")
            module_funcs[args.module.lower()]()
        else:
            print(f"Unknown module: {args.module}")
            print(f"Available modules: {', '.join(module_funcs.keys())}")
    else:
        seed_all()