"""
Admin Demo Data Management Utilities
====================================
Provides utilities for managing demo data loading from the admin interface.

This module provides:
- Loading demo data programmatically
- Checking data coverage status
- Resetting demo data
- Coverage verification

Usage:
    from admin_demo_data import load_all_demo_data, check_coverage, reset_demo_data
"""

import os
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

DATABASE = os.path.join(os.path.dirname(__file__), 'warehouse.db')


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


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


def check_module_coverage(module_name: str, tables: List[str]) -> Dict:
    """Check coverage for a module."""
    db = get_db()
    results = {'module': module_name, 'tables': [], 'total': 0, 'status': 'empty'}
    
    for table in tables:
        count = count_rows(table, db)
        results['tables'].append({
            'table': table,
            'count': count,
            'status': 'ok' if count > 0 else 'missing'
        })
        results['total'] += count
        if count > 0 and results['status'] == 'empty':
            results['status'] = 'partial'
    
    if results['total'] > 10:
        results['status'] = 'populated'
    
    return results


def get_full_coverage_report() -> Dict:
    """Get complete coverage report for all modules."""
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
    
    report = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'modules': [],
        'total_rows': 0,
        'overall_status': 'unknown'
    }
    
    for module_name, tables in modules:
        mod_report = check_module_coverage(module_name, tables)
        report['modules'].append(mod_report)
        report['total_rows'] += mod_report['total']
    
    # Determine overall status
    populated_count = sum(1 for m in report['modules'] if m['status'] == 'populated')
    if populated_count >= len(modules) * 0.8:
        report['overall_status'] = 'excellent'
    elif populated_count >= len(modules) * 0.5:
        report['overall_status'] = 'good'
    elif populated_count >= len(modules) * 0.3:
        report['overall_status'] = 'partial'
    else:
        report['overall_status'] = 'needs_seeding'
    
    return report


def ensure_demo_users() -> bool:
    """Ensure demo users exist in the database."""
    db = get_db()
    cursor = db.cursor()
    
    try:
        # Check if users exist
        user_count = count_rows('users', db)
        if user_count >= 3:
            return True
        
        # Create demo users
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
        return True
    except Exception as e:
        print(f"Error creating demo users: {e}")
        return False


def ensure_companies() -> bool:
    """Ensure companies exist."""
    db = get_db()
    cursor = db.cursor()
    
    try:
        comp_count = count_rows('companies', db)
        if comp_count > 0:
            return True
        
        companies = [
            ('MMDx Holding', 'WH', 'Parent holding company', 'Active'),
            ('MMDx SDAD', 'SDAD', 'SDAD subsidiary', 'Active'),
            ('MMDx AFRA', 'AFRA', 'AFRA subsidiary', 'Active'),
            ('MMDx Carmania', 'CRM', 'Carmania subsidiary', 'Active'),
        ]
        
        for name, code, desc, status in companies:
            try:
                cursor.execute("""
                    INSERT INTO companies (name, code, description, status, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, code, desc, status, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            except:
                pass
        
        db.commit()
        return True
    except Exception as e:
        print(f"Error creating companies: {e}")
        return False


def load_all_demo_data() -> Dict:
    """
    Load all demo data by running all seed scripts.
    Returns a status report.
    """
    results = {
        'started_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'modules': [],
        'success': True,
        'errors': []
    }
    
    # First ensure base data
    try:
        ensure_companies()
        ensure_demo_users()
    except Exception as e:
        results['errors'].append(f"Base data error: {e}")
    
    # Import and run seed functions
    seed_modules = [
        ('HR', 'seed_hr_data'),
        ('WMS', 'seed_wms_data'),
        ('Procurement', 'seed_procurement_data'),
        ('Sales', 'seed_sales_data'),
        ('Finance', 'seed_finance_data'),
        ('Quality', 'seed_quality_data'),
        ('Maintenance', 'seed_maintenance_data'),
        ('Asset', 'seed_asset_data'),
        ('Logistics', 'seed_logistics_data'),
        ('E-commerce', 'seed_ecommerce_data'),
        ('Document', 'seed_document_data'),
        ('Workflow', 'seed_workflow_data'),
        ('API Gateway', 'seed_api_gateway_data'),
        ('BI', 'seed_bi_data'),
        ('Marketing', 'seed_marketing_data'),
        ('Social Media', 'seed_social_media_data'),
    ]
    
    for module_name, func_name in seed_modules:
        try:
            # Try to import from seed_all
            from seed_all import seed_hr_data, seed_wms_data, seed_procurement_data, seed_sales_data
            from seed_all import seed_finance_data, seed_quality_data, seed_maintenance_data, seed_asset_data
            from seed_all import seed_logistics_data, seed_ecommerce_data, seed_document_data, seed_workflow_data
            from seed_all import seed_api_gateway_data, seed_bi_data, seed_marketing_data, seed_social_media_data
            
            func_map = {
                'HR': seed_hr_data,
                'WMS': seed_wms_data,
                'Procurement': seed_procurement_data,
                'Sales': seed_sales_data,
                'Finance': seed_finance_data,
                'Quality': seed_quality_data,
                'Maintenance': seed_maintenance_data,
                'Asset': seed_asset_data,
                'Logistics': seed_logistics_data,
                'E-commerce': seed_ecommerce_data,
                'Document': seed_document_data,
                'Workflow': seed_workflow_data,
                'API Gateway': seed_api_gateway_data,
                'BI': seed_bi_data,
                'Marketing': seed_marketing_data,
                'Social Media': seed_social_media_data,
            }
            
            if module_name in func_map:
                func_map[module_name]()
                results['modules'].append({'name': module_name, 'status': 'ok'})
        except Exception as e:
            results['errors'].append(f"{module_name}: {str(e)}")
            results['modules'].append({'name': module_name, 'status': 'error'})
            results['success'] = False
    
    results['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    results['coverage'] = get_full_coverage_report()
    
    return results


def quick_seed() -> Dict:
    """
    Quick seed - minimal demo data for testing.
    Runs only the essential seeds.
    """
    results = {
        'started_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'starting'
    }
    
    try:
        # Ensure base data
        ensure_companies()
        ensure_demo_users()
        
        # Run minimal seeds
        try:
            from seed_sample_data import seed_data
            seed_data()
        except:
            pass
        
        try:
            from seed_data import seed
            seed()
        except:
            pass
        
        results['status'] = 'complete'
        results['message'] = 'Quick seed complete'
    except Exception as e:
        results['status'] = 'error'
        results['message'] = str(e)
    
    results['completed_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return results


def get_recommended_seeds() -> List[Dict]:
    """
    Get list of recommended seeds based on current coverage.
    Returns modules that should be seeded.
    """
    coverage = get_full_coverage_report()
    recommended = []
    
    for mod in coverage['modules']:
        if mod['status'] in ['empty', 'missing', 'partial']:
            recommended.append({
                'module': mod['module'],
                'current_rows': mod['total'],
                'priority': 'high' if mod['total'] == 0 else 'medium',
                'tables': [t['table'] for t in mod['tables'] if t['count'] == 0]
            })
    
    return recommended


# Standalone execution
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Admin Demo Data Utilities')
    parser.add_argument('--status', action='store_true', help='Show coverage status')
    parser.add_argument('--report', action='store_true', help='Generate full coverage report')
    parser.add_argument('--recommended', action='store_true', help='Show recommended seeds')
    parser.add_argument('--quick', action='store_true', help='Quick seed')
    parser.add_argument('--full', action='store_true', help='Full seed')
    
    args = parser.parse_args()
    
    if args.status or args.report:
        report = get_full_coverage_report()
        print(f"\n=== Coverage Report ===")
        print(f"Generated: {report['generated_at']}")
        print(f"Overall Status: {report['overall_status']}")
        print(f"Total Rows: {report['total_rows']}")
        print(f"\nModules:")
        for mod in report['modules']:
            print(f"  {mod['module']}: {mod['total']} rows ({mod['status']})")
    
    elif args.recommended:
        recs = get_recommended_seeds()
        print(f"\n=== Recommended Seeds ===")
        for rec in recs:
            print(f"\n{rec['module']} (Priority: {rec['priority']})")
            print(f"  Current: {rec['current_rows']} rows")
            print(f"  Missing tables: {', '.join(rec['tables'])}")
    
    elif args.quick:
        result = quick_seed()
        print(f"Quick seed: {result['status']}")
        print(f"Message: {result.get('message', 'N/A')}")
    
    elif args.full:
        result = load_all_demo_data()
        print(f"Full seed: {'Success' if result['success'] else 'Errors'}")
        if result['errors']:
            print(f"Errors: {result['errors']}")
    
    else:
        # Default: show coverage
        report = get_full_coverage_report()
        print(f"\n=== MMDx Demo Data Coverage ===")
        print(f"Status: {report['overall_status']}")
        print(f"Total Rows: {report['total_rows']}")
        print(f"\nUse --help for options")