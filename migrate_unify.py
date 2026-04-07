"""
Data Deduplication and Migration Script
====================================
This script helps unify duplicate data across the WHDASH platform.

It performs:
1. Customer deduplication and canonical mapping
2. Item/product deduplication
3. Employee-User identity mapping
4. Warehouse canonical unification
5. Cross-table reference fixes

Run this script once during migration to clean up duplicate data.

Usage:
    python migrate_unify.py --dry-run    # Preview changes
    python migrate_unify.py --execute    # Apply changes
    python migrate_unify.py --report     # Generate deduplication report
"""

import sqlite3
import argparse
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

DATABASE_PATH = 'warehouse.db'


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# ============================================================================
# CUSTOMER DEDUPLICATION
# ============================================================================

def find_duplicate_customers() -> List[Dict]:
    """Find customers with the same name (potential duplicates)."""
    db = get_db()
    duplicates = []
    
    # Find customers with same name
    rows = db.execute("""
        SELECT name, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
        FROM customers
        WHERE name IS NOT NULL AND name != '' AND name != 'N/A'
        GROUP BY LOWER(TRIM(name))
        HAVING COUNT(*) > 1
    """).fetchall()
    
    for row in rows:
        ids = [int(x) for x in row['ids'].split(',')]
        duplicates.append({
            'type': 'name',
            'value': row['name'],
            'count': row['cnt'],
            'ids': ids
        })
    
    # Find customers with same phone
    phone_dups = db.execute("""
        SELECT phone, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
        FROM customers
        WHERE phone IS NOT NULL AND phone != '' AND phone != 'N/A'
        GROUP BY LOWER(TRIM(phone))
        HAVING COUNT(*) > 1
    """).fetchall()
    
    for row in phone_dups:
        ids = [int(x) for x in row['ids'].split(',')]
        duplicates.append({
            'type': 'phone',
            'value': row['phone'],
            'count': row['cnt'],
            'ids': ids
        })
    
    db.close()
    return duplicates


def merge_duplicate_customers(primary_id: int, secondary_ids: List[int], dry_run: bool = True) -> Dict:
    """Merge multiple customer records into one."""
    result = {
        'action': 'merge_customers',
        'primary_id': primary_id,
        'secondary_ids': secondary_ids,
        'dry_run': dry_run,
        'updates': [],
        'errors': []
    }
    
    db = get_db()
    
    try:
        # Get primary customer info
        primary = db.execute("SELECT * FROM customers WHERE id = ?", (primary_id,)).fetchone()
        if not primary:
            result['errors'].append(f"Primary customer {primary_id} not found")
            return result
        
        result['updates'].append(f"Primary: {primary['name']} (ID: {primary_id})")
        
        for sec_id in secondary_ids:
            secondary = db.execute("SELECT * FROM customers WHERE id = ?", (sec_id,)).fetchone()
            if not secondary:
                result['errors'].append(f"Secondary customer {sec_id} not found")
                continue
            
            result['updates'].append(f"  Merging: {secondary['name']} (ID: {sec_id})")
            
            if not dry_run:
                # Update references in other tables
                tables_to_update = [
                    ('customer_transactions', 'customer_id'),
                    ('delivery_stops', 'customer_id'),
                ]
                
                for table, field in tables_to_update:
                    try:
                        # Get count of references
                        count = db.execute(
                            f"SELECT COUNT(*) FROM {table} WHERE {field} = ?",
                            (sec_id,)
                        ).fetchone()[0]
                        
                        if count > 0:
                            # Update to primary
                            db.execute(
                                f"UPDATE {table} SET {field} = ? WHERE {field} = ?",
                                (primary_id, sec_id)
                            )
                            result['updates'].append(f"    Updated {count} rows in {table}.{field}")
                    except Exception as e:
                        result['errors'].append(f"    Error updating {table}: {e}")
                
                # Update CI profiles
                ci_profiles = db.execute(
                    "SELECT id FROM ci_customer_profiles WHERE customer_id = ?",
                    (sec_id,)
                ).fetchall()
                for ci in ci_profiles:
                    db.execute(
                        "UPDATE ci_customer_profiles SET customer_id = ? WHERE id = ?",
                        (primary_id, ci['id'])
                    )
                
                # Archive secondary customer
                db.execute(
                    "UPDATE customers SET name = ?, status = 'Merged' WHERE id = ?",
                    (f"{secondary['name']} [MERGED:{sec_id}]", sec_id)
                )
                
                result['updates'].append(f"    Archived customer {sec_id}")
        
        if not dry_run:
            db.commit()
            result['success'] = True
        else:
            result['success'] = True
            result['note'] = "Dry run - no changes made"
            
    except Exception as e:
        result['errors'].append(str(e))
        result['success'] = False
        db.rollback()
    finally:
        db.close()
    
    return result


# ============================================================================
# ITEM/PRODUCT DEDUPLICATION
# ============================================================================

def find_duplicate_items() -> List[Dict]:
    """Find items with the same code or name (potential duplicates)."""
    db = get_db()
    duplicates = []
    
    # Find parts with same item_code
    rows = db.execute("""
        SELECT item_code, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
        FROM parts
        WHERE item_code IS NOT NULL AND item_code != ''
        GROUP BY LOWER(TRIM(item_code))
        HAVING COUNT(*) > 1
    """).fetchall()
    
    for row in rows:
        ids = [int(x) for x in row['ids'].split(',')]
        duplicates.append({
            'type': 'item_code',
            'value': row['item_code'],
            'count': row['cnt'],
            'ids': ids
        })
    
    # Find items with same name
    name_dups = db.execute("""
        SELECT name, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
        FROM parts
        WHERE name IS NOT NULL AND name != ''
        GROUP BY LOWER(TRIM(name))
        HAVING COUNT(*) > 1
    """).fetchall()
    
    for row in name_dups:
        ids = [int(x) for x in row['ids'].split(',')]
        duplicates.append({
            'type': 'name',
            'value': row['name'],
            'count': row['cnt'],
            'ids': ids
        })
    
    db.close()
    return duplicates


def merge_duplicate_items(primary_id: int, secondary_ids: List[int], dry_run: bool = True) -> Dict:
    """Merge multiple item records into one."""
    result = {
        'action': 'merge_items',
        'primary_id': primary_id,
        'secondary_ids': secondary_ids,
        'dry_run': dry_run,
        'updates': [],
        'errors': []
    }
    
    db = get_db()
    
    try:
        primary = db.execute("SELECT * FROM parts WHERE id = ?", (primary_id,)).fetchone()
        if not primary:
            result['errors'].append(f"Primary item {primary_id} not found")
            return result
        
        result['updates'].append(f"Primary: {primary['name']} (ID: {primary_id})")
        
        for sec_id in secondary_ids:
            secondary = db.execute("SELECT * FROM parts WHERE id = ?", (sec_id,)).fetchone()
            if not secondary:
                result['errors'].append(f"Secondary item {sec_id} not found")
                continue
            
            result['updates'].append(f"  Merging: {secondary['name']} (ID: {sec_id})")
            
            if not dry_run:
                # Update WMS items references
                tables_to_update = [
                    ('wms_items', 'id'),
                    ('wms_inventory_balances', 'item_id'),
                    ('planning_item_profiles', 'item_id'),
                ]
                
                for table, field in tables_to_update:
                    try:
                        count = db.execute(
                            f"SELECT COUNT(*) FROM {table} WHERE {field} = ?",
                            (sec_id,)
                        ).fetchone()[0]
                        
                        if count > 0:
                            # Check if primary already has record
                            primary_exists = db.execute(
                                f"SELECT 1 FROM {table} WHERE {field} = ?",
                                (primary_id,)
                            ).fetchone()
                            
                            if primary_exists:
                                # Merge quantities/values
                                if table == 'wms_inventory_balances':
                                    db.execute("""
                                        UPDATE wms_inventory_balances 
                                        SET quantity = quantity + COALESCE(
                                            (SELECT quantity FROM wms_inventory_balances WHERE item_id = ?), 0
                                        )
                                        WHERE item_id = ?
                                    """, (sec_id, primary_id))
                                    db.execute(
                                        "DELETE FROM wms_inventory_balances WHERE item_id = ?",
                                        (sec_id,)
                                    )
                                else:
                                    db.execute(
                                        f"DELETE FROM {table} WHERE {field} = ?",
                                        (sec_id,)
                                    )
                            else:
                                db.execute(
                                    f"UPDATE {table} SET {field} = ? WHERE {field} = ?",
                                    (primary_id, sec_id)
                                )
                            
                            result['updates'].append(f"    Updated {count} rows in {table}")
                    except Exception as e:
                        result['errors'].append(f"    Error updating {table}: {e}")
                
                # Archive secondary item
                db.execute(
                    "UPDATE parts SET name = ?, item_code = ?, status = 'Merged' WHERE id = ?",
                    (f"{secondary['name']} [MERGED:{sec_id}]", f"MERGED-{sec_id}", sec_id)
                )
                
                result['updates'].append(f"    Archived item {sec_id}")
        
        if not dry_run:
            db.commit()
            result['success'] = True
        else:
            result['success'] = True
            result['note'] = "Dry run - no changes made"
            
    except Exception as e:
        result['errors'].append(str(e))
        result['success'] = False
        db.rollback()
    finally:
        db.close()
    
    return result


# ============================================================================
# EMPLOYEE-USER IDENTITY MAPPING
# ============================================================================

def find_unmapped_employees() -> List[Dict]:
    """Find employees without user accounts."""
    db = get_db()
    
    unmapped = db.execute("""
        SELECT e.*, u.id as user_id, u.username
        FROM hr_employees e
        LEFT JOIN users u ON e.user_id = u.id
        WHERE e.user_id IS NULL AND e.status = 'Active'
    """).fetchall()
    
    result = [dict(row) for row in unmapped]
    db.close()
    return result


def find_users_without_employee() -> List[Dict]:
    """Find users without employee records."""
    db = get_db()
    
    users = db.execute("""
        SELECT u.*
        FROM users u
        LEFT JOIN hr_employees e ON u.id = e.user_id
        WHERE e.id IS NULL AND u.username != 'admin'
    """).fetchall()
    
    result = [dict(row) for row in users]
    db.close()
    return result


def map_employee_to_user(employee_id: int, user_id: int, dry_run: bool = True) -> Dict:
    """Link an employee to a user account."""
    result = {
        'action': 'map_employee_user',
        'employee_id': employee_id,
        'user_id': user_id,
        'dry_run': dry_run,
        'updates': [],
        'errors': []
    }
    
    db = get_db()
    
    try:
        employee = db.execute("SELECT * FROM hr_employees WHERE id = ?", (employee_id,)).fetchone()
        user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        
        if not employee:
            result['errors'].append(f"Employee {employee_id} not found")
            return result
        
        if not user:
            result['errors'].append(f"User {user_id} not found")
            return result
        
        result['updates'].append(f"Employee: {employee['first_name']} {employee['last_name']} -> User: {user['username']}")
        
        if not dry_run:
            db.execute("UPDATE hr_employees SET user_id = ? WHERE id = ?", (user_id, employee_id))
            db.commit()
            result['success'] = True
        else:
            result['success'] = True
            result['note'] = "Dry run - no changes made"
            
    except Exception as e:
        result['errors'].append(str(e))
        result['success'] = False
    finally:
        db.close()
    
    return result


# ============================================================================
# WAREHOUSE UNIFICATION
# ============================================================================

def find_duplicate_warehouses() -> List[Dict]:
    """Find warehouses that might be duplicates."""
    db = get_db()
    
    duplicates = []
    
    # Find warehouses with same name
    rows = db.execute("""
        SELECT name, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
        FROM warehouses
        GROUP BY LOWER(TRIM(name))
        HAVING COUNT(*) > 1
    """).fetchall()
    
    for row in rows:
        ids = [int(x) for x in row['ids'].split(',')]
        duplicates.append({
            'type': 'name',
            'value': row['name'],
            'count': row['cnt'],
            'ids': ids
        })
    
    db.close()
    return duplicates


# ============================================================================
# MASTER DATA HEALTH REPORT
# ============================================================================

def generate_health_report() -> Dict:
    """Generate a comprehensive health report of master data."""
    db = get_db()
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'summary': {},
        'duplicates': {},
        'orphans': {},
        'inconsistencies': []
    }
    
    # Customer stats
    report['summary']['customers'] = {
        'total': db.execute("SELECT COUNT(*) FROM customers").fetchone()[0],
        'active': db.execute("SELECT COUNT(*) FROM customers WHERE status = 'Active'").fetchone()[0],
        'merged': db.execute("SELECT COUNT(*) FROM customers WHERE status = 'Merged'").fetchone()[0],
    }
    
    # Item stats
    report['summary']['items'] = {
        'total': db.execute("SELECT COUNT(*) FROM parts").fetchone()[0],
        'active': db.execute("SELECT COUNT(*) FROM parts WHERE status = 'Active'").fetchone()[0],
        'merged': db.execute("SELECT COUNT(*) FROM parts WHERE status = 'Merged'").fetchone()[0],
    }
    
    # Employee stats
    report['summary']['employees'] = {
        'total': db.execute("SELECT COUNT(*) FROM hr_employees").fetchone()[0],
        'active': db.execute("SELECT COUNT(*) FROM hr_employees WHERE status = 'Active'").fetchone()[0],
        'with_user': db.execute("SELECT COUNT(*) FROM hr_employees WHERE user_id IS NOT NULL").fetchone()[0],
    }
    
    # Warehouse stats
    report['summary']['warehouses'] = {
        'total': db.execute("SELECT COUNT(*) FROM warehouses").fetchone()[0],
    }
    
    # Duplicate counts
    report['duplicates']['customers'] = find_duplicate_customers()
    report['duplicates']['items'] = find_duplicate_items()
    report['duplicates']['warehouses'] = find_duplicate_warehouses()
    
    # Orphan records
    report['orphans']['unmapped_employees'] = find_unmapped_employees()
    report['orphans']['users_without_employee'] = find_users_without_employee()
    
    # Check for inconsistent references
    # Customers in transactions but not in customers table
    orphan_tx = db.execute("""
        SELECT COUNT(*) FROM customer_transactions ct
        LEFT JOIN customers c ON ct.customer_id = c.id
        WHERE c.id IS NULL
    """).fetchone()[0]
    if orphan_tx > 0:
        report['inconsistencies'].append(f"{orphan_tx} customer transactions have invalid customer_id")
    
    # Items in inventory but not in parts table
    orphan_inv = db.execute("""
        SELECT COUNT(DISTINCT item_id) FROM wms_inventory_balances
        WHERE item_id NOT IN (SELECT id FROM parts)
    """).fetchone()[0]
    if orphan_inv > 0:
        report['inconsistencies'].append(f"{orphan_inv} items in inventory have no parts record")
    
    db.close()
    return report


# ============================================================================
# REFERENCE INTEGRITY FIXES
# ============================================================================

def fix_orphan_references(dry_run: bool = True) -> Dict:
    """Fix orphan references in the database."""
    result = {
        'action': 'fix_orphan_references',
        'dry_run': dry_run,
        'updates': [],
        'errors': []
    }
    
    db = get_db()
    
    try:
        # Find customer transactions with invalid customer_id
        orphan_tx = db.execute("""
            SELECT ct.id, ct.customer_id, c.name as customer_name
            FROM customer_transactions ct
            LEFT JOIN customers c ON ct.customer_id = c.id
            WHERE c.id IS NULL
        """).fetchall()
        
        if orphan_tx:
            result['updates'].append(f"Found {len(orphan_tx)} orphan customer transactions")
            
            if not dry_run:
                # Get or create a generic "Unknown Customer" record
                unknown = db.execute(
                    "SELECT id FROM customers WHERE name = 'Unknown Customer' LIMIT 1"
                ).fetchone()
                
                if not unknown:
                    cursor = db.execute(
                        "INSERT INTO customers (name, status) VALUES ('Unknown Customer', 'Active')"
                    )
                    unknown_id = cursor.lastrowid
                else:
                    unknown_id = unknown['id']
                
                # Update orphan transactions
                db.execute(
                    "UPDATE customer_transactions SET customer_id = ? WHERE customer_id NOT IN (SELECT id FROM customers)",
                    (unknown_id,)
                )
                result['updates'].append(f"Reassigned {len(orphan_tx)} transactions to Unknown Customer")
        
        # Find inventory records with invalid item_id
        orphan_items = db.execute("""
            SELECT DISTINCT ib.item_id
            FROM wms_inventory_balances ib
            LEFT JOIN parts p ON ib.item_id = p.id
            WHERE p.id IS NULL
        """).fetchall()
        
        if orphan_items:
            result['updates'].append(f"Found {len(orphan_items)} orphan inventory item_ids")
        
        if not dry_run:
            db.commit()
            result['success'] = True
        else:
            result['success'] = True
            result['note'] = "Dry run - no changes made"
            
    except Exception as e:
        result['errors'].append(str(e))
        result['success'] = False
        db.rollback()
    finally:
        db.close()
    
    return result


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Data Deduplication and Migration Tool')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without applying')
    parser.add_argument('--execute', action='store_true', help='Apply changes')
    parser.add_argument('--report', action='store_true', help='Generate health report')
    parser.add_argument('--fix-orphans', action='store_true', help='Fix orphan references')
    parser.add_argument('--customer-dups', action='store_true', help='Find duplicate customers')
    parser.add_argument('--item-dups', action='store_true', help='Find duplicate items')
    parser.add_argument('--health', action='store_true', help='Generate full health report')
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("WHDASH Data Deduplication and Migration Tool")
    print("=" * 70)
    print()
    
    if args.health or args.report:
        print("Generating Master Data Health Report...")
        print("-" * 40)
        report = generate_health_report()
        print(json.dumps(report, indent=2, default=str))
        
    if args.customer_dups:
        print("Finding Duplicate Customers...")
        print("-" * 40)
        dups = find_duplicate_customers()
        print(f"Found {len(dups)} duplicate groups")
        for dup in dups:
            print(f"  {dup['type']}: '{dup['value']}' - {dup['count']} records: {dup['ids']}")
    
    if args.item_dups:
        print("Finding Duplicate Items...")
        print("-" * 40)
        dups = find_duplicate_items()
        print(f"Found {len(dups)} duplicate groups")
        for dup in dups:
            print(f"  {dup['type']}: '{dup['value']}' - {dup['count']} records: {dup['ids']}")
    
    if args.fix_orphans:
        print("Fixing Orphan References...")
        print("-" * 40)
        result = fix_orphan_references(dry_run=not args.execute)
        print(json.dumps(result, indent=2, default=str))
    
    if not any([args.health, args.report, args.customer_dups, args.item_dups, args.fix_orphans, args.execute]):
        parser.print_help()


if __name__ == '__main__':
    main()
