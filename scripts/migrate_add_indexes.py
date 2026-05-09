"""
Database Indexes Migration
==========================
Adds missing indexes to improve query performance across the platform.

This migration:
- Adds indexes on foreign key columns
- Adds indexes on frequently queried columns
- Adds composite indexes for common query patterns
- Does NOT remove any data
- Is safe to run multiple times (uses CREATE INDEX IF NOT EXISTS)

Run this script after updates to improve performance:
    python migrate_add_indexes.py
"""

import sqlite3
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import get_db_context, table_exists


# =============================================================================
# INDEX DEFINITIONS
# =============================================================================

# Format: (index_name, table_name, columns, description)
# columns can be a string or list of column specifications

INDEXES_TO_CREATE = [
    # Users table indexes
    ('idx_users_username', 'users', 'username', 'For username lookups during login'),
    ('idx_users_email', 'users', 'email', 'For email lookups during login'),
    ('idx_users_role_id', 'users', 'role_id', 'For role-based queries'),

    # Roles table indexes
    ('idx_roles_company_id', 'roles', 'company_id', 'For company-scoped role queries'),

    # Customers table indexes (if exists)
    ('idx_customers_country', 'sdad_customers', 'country', 'For country-based filtering'),
    ('idx_customers_salesperson', 'sdad_customers', 'salesperson_name', 'For salesperson reports'),
    ('idx_customers_location', 'sdad_customers', 'location', 'For location-based filtering'),
    ('idx_customers_active', 'sdad_customers', 'active', 'For active customer filtering'),

    # Inventory table indexes
    ('idx_inventory_company', 'inventory', 'company_id', 'For company-scoped inventory'),
    ('idx_inventory_part', 'inventory', 'part_id', 'For part lookups'),
    ('idx_inventory_company_part', 'inventory', 'company_id,part_id', 'Composite for unique constraint'),

    # Movements table indexes (high-volume table)
    ('idx_movements_part', 'movements', 'part_id', 'For part movement history'),
    ('idx_movements_company', 'movements', 'company_id', 'For company movement history'),
    ('idx_movements_user', 'movements', 'user_id', 'For user action audit'),
    ('idx_movements_date', 'movements', 'movement_date', 'For date range queries'),
    ('idx_movements_type', 'movements', 'movement_type', 'For movement type filtering'),

    # Parts table indexes
    ('idx_parts_category', 'parts', 'category_id', 'For category filtering'),
    ('idx_parts_brand', 'parts', 'brand_id', 'For brand filtering'),
    ('idx_parts_status', 'parts', 'status_id', 'For status filtering'),
    ('idx_parts_part_number', 'parts', 'part_number', 'For part number lookups'),

    # Platform notifications indexes
    ('idx_notifications_user', 'platform_notifications', 'user_id', 'For user notification lookup'),
    ('idx_notifications_role', 'platform_notifications', 'role_id', 'For role-based notifications'),
    ('idx_notifications_created', 'platform_notifications', 'created_at', 'For notification ordering'),
    ('idx_notifications_read', 'platform_notifications', 'user_id,is_read', 'For unread notification count'),

    # Platform audit log indexes
    ('idx_audit_entity', 'platform_audit_log', 'entity_type,entity_id', 'For entity history lookup'),
    ('idx_audit_user', 'platform_audit_log', 'user_id,created_at', 'For user activity audit'),
    ('idx_audit_action', 'platform_audit_log', 'action,created_at', 'For action type queries'),
    ('idx_audit_company', 'platform_audit_log', 'company_id,created_at', 'For company audit reports'),

    # Platform settings indexes
    ('idx_settings_key', 'platform_settings', 'setting_key', 'For setting lookups'),
    ('idx_settings_category', 'platform_settings', 'category', 'For category-based settings'),

    # Session tracking indexes
    ('idx_sessions_user', 'user_sessions', 'user_id', 'For user session lookup'),
    ('idx_sessions_token', 'user_sessions', 'session_token', 'For session validation'),

    # Role permissions indexes
    ('idx_role_perms_role', 'role_permissions', 'role_id', 'For role permission lookup'),
    ('idx_role_perms_perm', 'role_permissions', 'module,resource,action', 'For permission check queries'),

    # User access control indexes
    ('idx_user_company', 'user_company_access', 'user_id', 'For company access lookup'),
    ('idx_user_warehouse', 'user_warehouse_access', 'user_id', 'For warehouse access lookup'),

    # HR module indexes (if tables exist)
    ('idx_hr_employee_user', 'hr_employees', 'user_id', 'For employee-user linking'),
    ('idx_hr_employee_dept', 'hr_employees', 'department_id', 'For department queries'),

    # WMS indexes (if tables exist)
    ('idx_wms_locations_warehouse', 'wms_locations', 'warehouse_id', 'For warehouse location lookup'),
    ('idx_wms_stock_part', 'wms_stock', 'part_id', 'For stock level queries'),
    ('idx_wms_stock_warehouse', 'wms_stock', 'warehouse_id', 'For warehouse stock view'),

    # Sales module indexes (if tables exist)
    ('idx_sales_orders_customer', 'sales_orders', 'customer_id', 'For customer order history'),
    ('idx_sales_orders_status', 'sales_orders', 'status', 'For order status filtering'),
    ('idx_sales_order_items_order', 'sales_order_items', 'order_id', 'For order items lookup'),

    # Finance indexes (if tables exist)
    ('idx_finance_journals_date', 'finance_journals', 'entry_date', 'For journal date queries'),
    ('idx_finance_ar_customer', 'finance_ar_invoices', 'customer_id', 'For AR by customer'),

    # Quality indexes (if tables exist)
    ('idx_quality_ncr_status', 'quality_ncr', 'status', 'For NCR status filtering'),
    ('idx_quality_inspection_date', 'quality_inspections', 'inspection_date', 'For inspection date range'),

    # Logistics indexes (if tables exist)
    ('idx_logistics_trips_status', 'logistics_trips', 'status', 'For trip status filtering'),
    ('idx_logistics_trips_driver', 'logistics_trips', 'driver_id', 'For driver assignment queries'),
    ('idx_logistics_stops_trip', 'logistics_stops', 'trip_id', 'For stops by trip'),
]


# =============================================================================
# MIGRATION LOGIC
# =============================================================================

def check_index_exists(index_name: str, cursor) -> bool:
    """Check if an index already exists."""
    cursor.execute("""
        SELECT 1 FROM sqlite_master WHERE type='index' AND name=?
    """, (index_name,))
    return cursor.fetchone() is not None


def create_index(conn, index_name: str, table_name: str, columns: str, description: str = '') -> bool:
    """
    Create an index if it doesn't exist.

    Returns:
        True if index was created, False if it already existed
    """
    if check_index_exists(index_name, conn.cursor()):
        print(f"  [SKIP] Index {index_name} already exists")
        return False

    # Validate table exists
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM sqlite_master WHERE type='table' AND name=?
    """, (table_name,))

    if not cursor.fetchone():
        print(f"  [SKIP] Table {table_name} does not exist")
        return False

    # Create the index
    if isinstance(columns, str):
        column_spec = columns
    else:
        column_spec = ', '.join(columns)

    sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({column_spec})"

    try:
        conn.execute(sql)
        print(f"  [CREATE] {index_name} on {table_name}({column_spec})")
        if description:
            print(f"         Purpose: {description}")
        return True
    except sqlite3.Error as e:
        print(f"  [ERROR] Failed to create {index_name}: {e}")
        return False


def run_migration():
    """Run the index creation migration."""
    print("=" * 70)
    print("Database Indexes Migration")
    print("=" * 70)
    print()

    # Get database path from environment or default
    from config import DATABASE_PATH
    db_path = os.environ.get('DATABASE_PATH', DATABASE_PATH)

    print(f"Database: {db_path}")
    print(f"Indexes to create: {len(INDEXES_TO_CREATE)}")
    print()

    # Connect to database
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    try:
        created = 0
        skipped = 0
        errors = 0

        for index_name, table_name, columns, description in INDEXES_TO_CREATE:
            success = create_index(conn, index_name, table_name, columns, description)
            if success:
                created += 1
            elif check_index_exists(index_name, conn.cursor()) or not conn.execute("""
                SELECT 1 FROM sqlite_master WHERE type='table' AND name=?
            """, (table_name,)).fetchone():
                skipped += 1
            else:
                errors += 1

        conn.commit()

        print()
        print("=" * 70)
        print("Migration Complete")
        print("=" * 70)
        print(f"  Created: {created}")
        print(f"  Skipped: {skipped}")
        print(f"  Errors:  {errors}")
        print()

        # Analyze tables for query optimization
        print("Running ANALYZE to update query planner statistics...")
        conn.execute("ANALYZE")
        conn.commit()
        print("  Done.")

    finally:
        conn.close()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    run_migration()
