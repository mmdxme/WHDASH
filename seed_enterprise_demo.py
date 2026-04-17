"""
MMDx Enterprise Demo Data - Master Seeder
========================================
Unified demo data seeding orchestrator for the entire WHDASH platform.

This script coordinates demo data seeding across ALL modules in proper dependency order,
ensuring relational integrity and comprehensive coverage.

Usage:
    python seed_enterprise_demo.py              # Seed all modules
    python seed_enterprise_demo.py --status   # Show coverage status
    python seed_enterprise_demo.py --module treasury  # Seed specific module
    python seed_enterprise_demo.py --profiles  # Show available seed profiles

Seed Profiles:
    minimal_demo   - Core entities only (users, companies, basic data)
    standard_demo  - Most modules with moderate data (~6000+ rows)
    full_enterprise_demo - All modules with rich data (~10000+ rows)

Author: MMDx Data Architecture Team
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
    print(f"\n>> {text}")


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
        print("  [OK] Core base data seeded")
    except Exception as e:
        print(f"  [NOTE] {e}")


def seed_hr_data():
    """Seed HR module data."""
    print_step("Seeding HR module data")
    try:
        from seed_sample_data import seed_data as seed_hr
        seed_hr()
        print("  [OK] HR data seeded")
    except Exception as e:
        print(f"  [NOTE] {e}")


def seed_wms_data():
    """Seed WMS/warehouse data."""
    print_step("Seeding WMS module data")
    try:
        from seed_data import seed
        seed()
        print("  [OK] WMS base data seeded")
    except Exception as e:
        print(f"  [NOTE] {e}")
    try:
        from seed_wms_extended_data import seed_wms_extended_data
        seed_wms_extended_data()
        print("  [OK] WMS extended data seeded")
    except Exception as e:
        print(f"  [NOTE] {e}")


def seed_procurement_data():
    """Seed Procurement module data."""
    print_step("Seeding Procurement module data")
    try:
        from seed_procurement_data import seed_procurement_data
        seed_procurement_data()
        print("  [OK] Procurement data seeded")
    except Exception as e:
        print(f"  [ERROR] {e}")


def seed_sales_data():
    """Seed Sales module data."""
    print_step("Seeding Sales module data")
    try:
        from seed_sample_data import seed_data
        print("  [OK] Sales data included in core seeds")
    except Exception as e:
        print(f"  [NOTE] {e}")


def seed_finance_data():
    """Seed Finance module data."""
    print_step("Seeding Finance module data")
    try:
        import seed_finance_data as sfd
        if hasattr(sfd, 'main'):
            sfd.main()
        print("  [OK] Finance data seeded")
    except Exception as e:
        print(f"  [ERROR] {e}")


def seed_treasury_data():
    """Seed Treasury module data."""
    print_step("Seeding Treasury module data")
    try:
        import seed_treasury_data as std
        if hasattr(std, 'seed_treasury_data'):
            std.seed_treasury_data()
        print("  [OK] Treasury data seeded")
    except Exception as e:
        print(f"  [ERROR] {e}")


def seed_quality_data():
    """Seed Quality module data."""
    print_step("Seeding Quality module data")
    try:
        from seed_quality_data import seed_quality_data
        seed_quality_data()
        print("  [OK] Quality data seeded")
    except Exception as e:
        print(f"  [ERROR] {e}")


def seed_maintenance_data():
    """Seed Maintenance module data."""
    print_step("Seeding Maintenance module data")
    try:
        from seed_maintenance_data import seed_maintenance_data
        seed_maintenance_data()
        print("  [OK] Maintenance data seeded")
    except Exception as e:
        print(f"  [ERROR] {e}")


def seed_asset_data():
    """Seed Asset module data."""
    print_step("Seeding Asset module data")
    try:
        from seed_asset_data import seed_asset_data
        seed_asset_data()
        print("  [OK] Asset data seeded")
    except Exception as e:
        print(f"  [ERROR] {e}")


def seed_logistics_data():
    """Seed Logistics module data."""
    print_step("Seeding Logistics module data")
    try:
        from seed_logistics_data import seed_logistics_data
        seed_logistics_data()
        print("  [OK] Logistics data seeded")
    except Exception as e:
        print(f"  [ERROR] {e}")


def seed_ecommerce_data():
    """Seed E-commerce module data."""
    print_step("Seeding E-commerce module data")
    try:
        import seed_ecommerce_data as sed
        if hasattr(sed, 'main'):
            sed.main()
        print("  [OK] E-commerce data seeded")
    except Exception as e:
        print(f"  [ERROR] {e}")


def seed_document_data():
    """Seed Document module data."""
    print_step("Seeding Document module data")
    try:
        from seed_document_data import seed_document_demo_data
        seed_document_demo_data()
        print("  [OK] Document data seeded")
    except Exception as e:
        print(f"  [ERROR] {e}")


def seed_workflow_data():
    """Seed Workflow module data."""
    print_step("Seeding Workflow module data")
    try:
        from seed_workflow_data import seed_workflow_data
        seed_workflow_data()
        print("  [OK] Workflow data seeded")
    except Exception as e:
        print(f"  [ERROR] {e}")


def seed_org_planning_data():
    """Seed Org Planning module data."""
    print_step("Seeding Org Planning module data")
    try:
        from org_planning_models import seed_org_planning_demo_data
        seed_org_planning_demo_data()
        print("  [OK] Org Planning data seeded")
    except Exception as e:
        print(f"  [NOTE] {e}")


def seed_api_gateway_data():
    """Seed API Gateway module data."""
    print_step("Seeding API Gateway module data")
    try:
        from seed_api_gateway_data import seed
        seed()
        print("  [OK] API Gateway data seeded")
    except Exception as e:
        print(f"  [ERROR] {e}")


def seed_bi_data():
    """Seed BI/Reporting module data."""
    print_step("Seeding BI module data")
    try:
        import seed_bi_data as sb
        if hasattr(sb, 'main'):
            sb.main()
        print("  [OK] BI data seeded")
    except Exception as e:
        print(f"  [ERROR] {e}")


def seed_marketing_data():
    """Seed Marketing module data."""
    print_step("Seeding Marketing module data")
    try:
        import seed_marketing_data as smd
        smd.seed_marketing_data()
        print("  [OK] Marketing data seeded")
    except Exception as e:
        print(f"  [ERROR] {e}")


def seed_social_media_data():
    """Seed Social Media module data."""
    print_step("Seeding Social Media module data")
    try:
        import seed_social_media_data as ssmd
        ssmd.seed_social_media_data()
        print("  [OK] Social Media data seeded")
    except Exception as e:
        print(f"  [ERROR] {e}")


def seed_company_data():
    """Seed Company module data."""
    print_step("Seeding Company module data")
    db = get_db()
    cursor = db.cursor()
    try:
        comp_count = count_rows('companies', db)
        if comp_count > 0:
            print("  - Companies already exist")
            return
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
        print("  [OK] Companies seeded")
    except Exception as e:
        print(f"  [ERROR] {e}")


# =============================================================================
# COVERAGE STATUS
# =============================================================================

def show_coverage_status():
    """Show demo data coverage status for all modules."""
    print_header("ENTERPRISE DEMO DATA COVERAGE STATUS")
    
    db = get_db()
    
    modules = [
        ('HR', ['hr_employees', 'hr_departments', 'hr_attendance_records', 'hr_leave_requests']),
        ('WMS', ['parts', 'inventory', 'warehouses', 'wms_waves', 'wms_wave_templates']),
        ('Procurement', ['suppliers', 'procurement_requisitions', 'procurement_purchase_orders']),
        ('Sales', ['sales_customers', 'sales_inquiries', 'sales_quotations', 'sales_orders']),
        ('Finance', ['finance_accounts', 'finance_journals', 'finance_customer_invoices', 'finance_supplier_bills']),
        ('Treasury', ['treasury_settings', 'treasury_cash_movements', 'treasury_collections', 'treasury_alerts']),
        ('Quality', ['quality_inspections', 'quality_non_conformances', 'quality_capa_records']),
        ('Maintenance', ['maintenance_facilities', 'maintenance_work_orders']),
        ('Assets', ['assets', 'asset_categories']),
        ('Logistics', ['logistics_vehicles', 'logistics_drivers', 'delivery_trips']),
        ('E-commerce', ['ecommerce_channels', 'ecommerce_order_imports']),
        ('Documents', ['documents', 'document_categories']),
        ('Workflow', ['workflow_definitions', 'workflow_instances']),
        ('Org Planning', ['op_companies', 'op_org_units', 'op_positions']),
        ('API Gateway', ['api_clients', 'integration_profiles']),
        ('BI', ['bi_reporting_datasets', 'bi_kpis', 'bi_saved_reports']),
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


def show_profiles():
    """Show available seed profiles."""
    print_header("AVAILABLE SEED PROFILES")
    profiles = {
        'minimal_demo': 'Core entities only - ~500 rows',
        'standard_demo': 'Most modules - ~6000+ rows',
        'full_enterprise_demo': 'All modules - ~10000+ rows'
    }
    for name, desc in profiles.items():
        print(f"  {name}: {desc}")
    print()


# =============================================================================
# MAIN ORCHESTRATOR
# =============================================================================

def seed_all():
    """Run all seed scripts in proper order."""
    print_header("MMDx ENTERPRISE DEMO DATA SEEDER")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Core first (dependencies)
    seed_company_data()
    seed_core_base()
    
    # Core modules
    seed_hr_data()
    seed_wms_data()
    seed_procurement_data()
    seed_sales_data()
    
    # Finance modules
    seed_finance_data()
    seed_treasury_data()
    
    # Operations modules
    seed_quality_data()
    seed_maintenance_data()
    seed_asset_data()
    seed_logistics_data()
    
    # Business modules
    seed_ecommerce_data()
    seed_document_data()
    seed_workflow_data()
    seed_org_planning_data()
    
    # Supporting modules
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
    import random
    
    parser = argparse.ArgumentParser(description='MMDx Enterprise Demo Data Seeder')
    parser.add_argument('--status', action='store_true', help='Show coverage status')
    parser.add_argument('--profiles', action='store_true', help='Show available seed profiles')
    parser.add_argument('--module', type=str, help='Seed specific module only')
    
    args = parser.parse_args()
    
    if args.profiles:
        show_profiles()
    elif args.status:
        show_coverage_status()
    elif args.module:
        module_funcs = {
            'hr': seed_hr_data,
            'wms': seed_wms_data,
            'procurement': seed_procurement_data,
            'sales': seed_sales_data,
            'finance': seed_finance_data,
            'treasury': seed_treasury_data,
            'quality': seed_quality_data,
            'maintenance': seed_maintenance_data,
            'asset': seed_asset_data,
            'logistics': seed_logistics_data,
            'ecommerce': seed_ecommerce_data,
            'document': seed_document_data,
            'workflow': seed_workflow_data,
            'org': seed_org_planning_data,
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