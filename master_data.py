"""
Master Data Management System
============================
Unified master data management for the MMDx platform.

This module provides:
- Single source of truth for all master data entities
- Entity mapping between legacy tables
- Data synchronization between duplicate tables
- Deduplication utilities
- Cross-module reference resolution

KEY PRINCIPLES:
- One Customer everywhere
- One Item everywhere
- One Employee everywhere
- One Supplier everywhere
- One Warehouse everywhere

ENTITY CANONICAL FORMS:
- customers: Canonical customer table (id, name, etc.)
- items/parts: Canonical product/item table
- employees: Canonical employee table
- suppliers: Canonical supplier table
- warehouses: Canonical warehouse table
"""

from typing import Dict, List, Optional, Any, Tuple
from database import get_db_context, get_one, get_all, row_to_dict, rows_to_list

# ============================================================================
# ENTITY CANONICAL MAPPING
# ============================================================================

# Maps canonical entity types to their source tables and key fields
ENTITY_SOURCES = {
    'customer': {
        'canonical_table': 'customers',
        'sources': [
            {'table': 'sdad_customers', 'key': 'id', 'label': 'name'},
            {'table': 'ci_customer_profiles', 'key': 'customer_id', 'label': 'customer_name'},
        ],
        'canonical_id_field': 'id',
        'label_field': 'name',
        'merge_fields': ['name', 'phone', 'email', 'address'],
    },
    'item': {
        'canonical_table': 'parts',
        'sources': [
            {'table': 'wms_items', 'key': 'id', 'label': 'name'},
            {'table': 'peyvast_products', 'key': 'id', 'label': 'name'},
        ],
        'canonical_id_field': 'id',
        'label_field': 'name',
        'merge_fields': ['name', 'item_code', 'barcode'],
    },
    'employee': {
        'canonical_table': 'hr_employees',
        'sources': [
            {'table': 'users', 'key': 'id', 'label': 'username'},
        ],
        'canonical_id_field': 'id',
        'label_field': 'first_name',
        'merge_fields': ['first_name', 'last_name', 'email', 'mobile'],
    },
    'supplier': {
        'canonical_table': 'suppliers',
        'sources': [
            {'table': 'wms_item_suppliers', 'key': 'supplier_id', 'label': 'supplier_name'},
        ],
        'canonical_id_field': 'id',
        'label_field': 'name',
        'merge_fields': ['name', 'email', 'phone'],
    },
    'warehouse': {
        'canonical_table': 'warehouses',
        'sources': [
            {'table': 'wms_warehouses', 'key': 'id', 'label': 'name'},
            {'table': 'peyvast_warehouses', 'key': 'id', 'label': 'name'},
        ],
        'canonical_id_field': 'id',
        'label_field': 'name',
        'merge_fields': ['name', 'code', 'address'],
    },
    'company': {
        'canonical_table': 'companies',
        'sources': [
            {'table': 'wms_companies', 'key': 'id', 'label': 'name'},
        ],
        'canonical_id_field': 'id',
        'label_field': 'name',
        'merge_fields': ['name', 'code'],
    },
}


# ============================================================================
# CUSTOMER MASTER DATA
# ============================================================================

def get_canonical_customer(customer_id: int) -> Optional[Dict]:
    """Get a customer from the canonical customers table."""
    return get_one("SELECT * FROM customers WHERE id = ?", (customer_id,))


def get_all_canonical_customers(active_only: bool = True) -> List[Dict]:
    """Get all customers from the canonical table."""
    sql = "SELECT * FROM customers"
    if active_only:
        sql += " WHERE status = 'Active'"
    sql += " ORDER BY name"
    return get_all(sql)


def sync_customer_to_sdad(source_customer_id: int) -> bool:
    """
    Sync a canonical customer to the sdad_customers table.
    Used when data needs to be shared with external systems.
    
    Args:
        source_customer_id: ID from customers table
    
    Returns:
        True if successful
    """
    customer = get_canonical_customer(source_customer_id)
    if not customer:
        return False
    
    with get_db_context() as db:
        # Check if exists in sdad_customers
        existing = db.execute(
            "SELECT id FROM sdad_customers WHERE id = ?",
            (source_customer_id,)
        ).fetchone()
        
        if existing:
            # Update
            db.execute("""
                UPDATE sdad_customers SET
                    name = ?, phone = ?, location = ?, type = ?,
                    salesperson_id = ?, working_hours = ?, working_days = ?
                WHERE id = ?
            """, (
                customer.get('name'),
                customer.get('phone'),
                customer.get('location'),
                customer.get('type'),
                customer.get('salesperson_id'),
                customer.get('working_hours'),
                customer.get('working_days'),
                source_customer_id
            ))
        else:
            # Insert
            db.execute("""
                INSERT INTO sdad_customers (id, name, phone, location, type, salesperson_id, working_hours, working_days)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                source_customer_id,
                customer.get('name'),
                customer.get('phone'),
                customer.get('location'),
                customer.get('type'),
                customer.get('salesperson_id'),
                customer.get('working_hours'),
                customer.get('working_days'),
            ))
        
        db.commit()
    return True


def link_customer_to_ci(customer_id: int) -> bool:
    """
    Link canonical customer to Customer Intelligence profile.
    
    Args:
        customer_id: Canonical customer ID
    
    Returns:
        True if successful
    """
    customer = get_canonical_customer(customer_id)
    if not customer:
        return False
    
    with get_db_context() as db:
        # Check if CI profile exists
        existing = db.execute(
            "SELECT id FROM ci_customer_profiles WHERE customer_id = ?",
            (customer_id,)
        ).fetchone()
        
        if not existing:
            # Create CI profile
            db.execute("""
                INSERT INTO ci_customer_profiles (
                    customer_id, customer_name, phone, email, city, country,
                    customer_type, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                customer_id,
                customer.get('name'),
                customer.get('phone'),
                customer.get('email'),
                customer.get('city'),
                customer.get('country'),
                customer.get('type', 'retail'),
                1
            ))
            db.commit()
    
    return True


# ============================================================================
# ITEM MASTER DATA
# ============================================================================

def get_canonical_item(item_id: int) -> Optional[Dict]:
    """Get an item from the canonical parts table."""
    return get_one("SELECT * FROM parts WHERE id = ?", (item_id,))


def get_all_canonical_items(active_only: bool = True) -> List[Dict]:
    """Get all items from the canonical table."""
    sql = "SELECT * FROM parts"
    if active_only:
        sql += " WHERE status = 'Active'"
    sql += " ORDER BY name"
    return get_all(sql)


def sync_item_to_wms(item_id: int) -> bool:
    """
    Sync a canonical item to the WMS items table.
    
    Args:
        item_id: Canonical item ID
    
    Returns:
        True if successful
    """
    item = get_canonical_item(item_id)
    if not item:
        return False
    
    with get_db_context() as db:
        # Check if exists in wms_items
        existing = db.execute(
            "SELECT id FROM wms_items WHERE id = ?",
            (item_id,)
        ).fetchone()
        
        if existing:
            # Update
            db.execute("""
                UPDATE wms_items SET
                    name = ?, item_code = ?, description = ?,
                    category_id = ?, brand_id = ?, unit_of_measure = ?,
                    is_active = ?
                WHERE id = ?
            """, (
                item.get('name'),
                item.get('item_code'),
                item.get('description'),
                item.get('category_id'),
                item.get('brand_id'),
                item.get('unit'),
                1 if item.get('status') == 'Active' else 0,
                item_id
            ))
        else:
            # Insert
            db.execute("""
                INSERT INTO wms_items (id, name, item_code, description, category_id, brand_id, unit_of_measure, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                item_id,
                item.get('name'),
                item.get('item_code'),
                item.get('description'),
                item.get('category_id'),
                item.get('brand_id'),
                item.get('unit'),
                1 if item.get('status') == 'Active' else 0,
            ))
        
        db.commit()
    return True


# ============================================================================
# EMPLOYEE MASTER DATA
# ============================================================================

def get_canonical_employee(employee_id: int) -> Optional[Dict]:
    """Get an employee from the canonical hr_employees table."""
    return get_one("SELECT * FROM hr_employees WHERE id = ?", (employee_id,))


def get_all_canonical_employees(active_only: bool = True) -> List[Dict]:
    """Get all employees from the canonical table."""
    sql = "SELECT * FROM hr_employees"
    if active_only:
        sql += " WHERE status = 'Active'"
    sql += " ORDER BY first_name, last_name"
    return get_all(sql)


def link_employee_to_user(employee_id: int, user_id: int) -> bool:
    """
    Link an employee to their system user account.
    
    Args:
        employee_id: HR employee ID
        user_id: System user ID
    
    Returns:
        True if successful
    """
    with get_db_context() as db:
        db.execute(
            "UPDATE hr_employees SET user_id = ? WHERE id = ?",
            (user_id, employee_id)
        )
        db.commit()
    return True


def get_employee_by_code(employee_code: str) -> Optional[Dict]:
    """Get employee by their employee code."""
    return get_one("SELECT * FROM hr_employees WHERE employee_code = ?", (employee_code,))


# ============================================================================
# SUPPLIER MASTER DATA
# ============================================================================

def get_canonical_supplier(supplier_id: int) -> Optional[Dict]:
    """Get a supplier from the canonical suppliers table."""
    return get_one("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))


def get_all_canonical_suppliers(active_only: bool = True) -> List[Dict]:
    """Get all suppliers from the canonical table."""
    sql = "SELECT * FROM suppliers"
    if active_only:
        sql += " WHERE status = 'Active'"
    sql += " ORDER BY name"
    return get_all(sql)


# ============================================================================
# WAREHOUSE MASTER DATA
# ============================================================================

def get_canonical_warehouse(warehouse_id: int) -> Optional[Dict]:
    """Get a warehouse from the canonical warehouses table."""
    return get_one("SELECT * FROM warehouses WHERE id = ?", (warehouse_id,))


def get_all_canonical_warehouses() -> List[Dict]:
    """Get all warehouses from the canonical table."""
    return get_all("SELECT * FROM warehouses ORDER BY name")


# ============================================================================
# CROSS-MODULE LOOKUP
# ============================================================================

def resolve_customer(customer_id: int) -> Dict[str, Any]:
    """
    Resolve a customer ID to all related data across modules.
    
    Returns a unified view of the customer with data from:
    - Canonical customers table
    - CI customer profiles
    - SDAD customer data
    - Related transactions
    """
    result = {}
    
    # Canonical customer
    canonical = get_canonical_customer(customer_id)
    if canonical:
        result['canonical'] = canonical
    
    # CI profile
    with get_db_context() as db:
        ci_profile = db.execute(
            "SELECT * FROM ci_customer_profiles WHERE customer_id = ?",
            (customer_id,)
        ).fetchone()
        if ci_profile:
            result['ci_profile'] = dict(ci_profile)
    
    # SDAD data
    sdad = get_one("SELECT * FROM sdad_customers WHERE id = ?", (customer_id,))
    if sdad:
        result['sdad'] = sdad
    
    # Order count
    result['order_count'] = get_one(
        "SELECT COUNT(*) as cnt FROM customer_transactions WHERE customer_id = ?",
        (customer_id,)
    )['cnt'] if customer_id else 0
    
    return result


def resolve_item(item_id: int) -> Dict[str, Any]:
    """
    Resolve an item ID to all related data across modules.
    
    Returns a unified view of the item with data from:
    - Canonical parts table
    - WMS items
    - Peyvast products
    - Current stock levels
    """
    result = {}
    
    # Canonical part
    canonical = get_canonical_item(item_id)
    if canonical:
        result['canonical'] = canonical
    
    # WMS data
    with get_db_context() as db:
        wms_item = db.execute(
            "SELECT * FROM wms_items WHERE id = ?",
            (item_id,)
        ).fetchone()
        if wms_item:
            result['wms'] = dict(wms_item)
    
    # Current stock
    stock = db.execute("""
        SELECT SUM(quantity) as total_stock, SUM(reserved) as reserved
        FROM wms_inventory_balances WHERE item_id = ?
    """, (item_id,)).fetchone()
    
    if stock:
        result['stock'] = {
            'total': stock['total_stock'] or 0,
            'reserved': stock['reserved'] or 0,
            'available': (stock['total_stock'] or 0) - (stock['reserved'] or 0)
        }
    
    return result


def resolve_employee(employee_id: int) -> Dict[str, Any]:
    """
    Resolve an employee ID to all related data.
    
    Returns unified employee data including HR records and user account.
    """
    result = {}
    
    # Canonical employee
    canonical = get_canonical_employee(employee_id)
    if canonical:
        result['hr'] = canonical
        
        # Employment details
        with get_db_context() as db:
            employment = db.execute("""
                SELECT ee.*, 
                       d.name as department_name,
                       p.title as position_title,
                       s.name as shift_name
                FROM hr_employee_employment ee
                LEFT JOIN hr_departments d ON ee.department_id = d.id
                LEFT JOIN hr_positions p ON ee.position_id = p.id
                LEFT JOIN hr_shifts s ON ee.shift_id = s.id
                WHERE ee.employee_id = ? AND ee.is_primary = 1
            """, (employee_id,)).fetchone()
            
            if employment:
                result['employment'] = dict(employment)
    
    # User account
    user = get_one(
        "SELECT id, username, email FROM users WHERE id = ?",
        (canonical.get('user_id') if canonical else None,)
    ) if canonical and canonical.get('user_id') else None
    if user:
        result['user'] = user
    
    return result


# ============================================================================
# DEDUPLICATION
# ============================================================================

def find_duplicate_customers(criteria: str = 'name') -> List[Dict]:
    """
    Find potential duplicate customers based on criteria.
    
    Args:
        criteria: 'name', 'phone', 'email'
    
    Returns:
        List of potential duplicate pairs
    """
    duplicates = []
    
    if criteria == 'name':
        with get_db_context() as db:
            rows = db.execute("""
                SELECT name, COUNT(*) as cnt, GROUP_CONCAT(id) as ids
                FROM customers
                WHERE name IS NOT NULL AND name != ''
                GROUP BY LOWER(TRIM(name))
                HAVING cnt > 1
            """).fetchall()
            
            for row in rows:
                ids = [int(x) for x in row['ids'].split(',')]
                duplicates.append({
                    'criteria': 'name',
                    'value': row['name'],
                    'count': row['cnt'],
                    'ids': ids
                })
    
    return duplicates


def merge_customers(primary_id: int, secondary_id: int, archive_secondary: bool = True) -> bool:
    """
    Merge two customer records into one.
    
    Args:
        primary_id: ID to keep
        secondary_id: ID to merge into primary
        archive_secondary: If True, archive the secondary record
    
    Returns:
        True if successful
    """
    with get_db_context() as db:
        # Get secondary record
        secondary = db.execute("SELECT * FROM customers WHERE id = ?", (secondary_id,)).fetchone()
        if not secondary:
            return False
        
        # Update references in other tables
        table_refs = [
            ('customer_transactions', 'customer_id'),
            ('delivery_stops', 'customer_id'),
            ('ci_customer_profiles', 'customer_id'),
            ('task_items', 'assigned_to_user_id'),  # If used as FK
        ]
        
        for table, field in table_refs:
            try:
                db.execute(f"""
                    UPDATE OR IGNORE {table} SET {field} = ?
                    WHERE {field} = ?
                """, (primary_id, secondary_id))
            except Exception:
                pass
        
        # Archive secondary if requested
        if archive_secondary:
            db.execute("""
                UPDATE customers SET 
                    status = 'Merged',
                    name = name || ' [MERGED: ' || ? || ']'
                WHERE id = ?
            """, (secondary_id, secondary_id))
        
        db.commit()
    return True


# ============================================================================
# MASTER DATA VALIDATION
# ============================================================================

def validate_master_references(entity_type: str, entity_id: int) -> Dict[str, Any]:
    """
    Validate that an entity has valid references across all modules.
    
    Returns:
        Dict with 'is_valid' and list of 'issues'
    """
    issues = []
    
    if entity_type == 'customer':
        # Check canonical exists
        customer = get_canonical_customer(entity_id)
        if not customer:
            issues.append('Customer does not exist in canonical table')
            return {'is_valid': len(issues) == 0, 'issues': issues}
        
        # Check for broken references
        with get_db_context() as db:
            # Orphaned in CI
            ci = db.execute(
                "SELECT id FROM ci_customer_profiles WHERE customer_id = ?",
                (entity_id,)
            ).fetchone()
            if not ci:
                issues.append('Customer has no CI profile')
            
            # Count transactions
            tx_count = db.execute(
                "SELECT COUNT(*) as cnt FROM customer_transactions WHERE customer_id = ?",
                (entity_id,)
            ).fetchone()['cnt']
            if tx_count == 0:
                issues.append('Customer has no transactions')
    
    elif entity_type == 'item':
        item = get_canonical_item(entity_id)
        if not item:
            issues.append('Item does not exist in canonical table')
            return {'is_valid': len(issues) == 0, 'issues': issues}
    
    elif entity_type == 'employee':
        emp = get_canonical_employee(entity_id)
        if not emp:
            issues.append('Employee does not exist in HR table')
            return {'is_valid': len(issues) == 0, 'issues': issues}
    
    return {'is_valid': len(issues) == 0, 'issues': issues}


# ============================================================================
# MASTER DATA HEALTH CHECK
# ============================================================================

def run_master_data_health_check() -> Dict[str, Any]:
    """
    Run a comprehensive health check on master data.
    
    Returns:
        Dict with health metrics and issues
    """
    health = {
        'customers': {'total': 0, 'orphaned': 0, 'duplicates': 0, 'issues': []},
        'items': {'total': 0, 'orphaned': 0, 'duplicates': 0, 'issues': []},
        'employees': {'total': 0, 'orphaned': 0, 'issues': []},
        'suppliers': {'total': 0, 'orphaned': 0, 'issues': []},
        'warehouses': {'total': 0, 'orphaned': 0, 'issues': []},
    }
    
    with get_db_context() as db:
        # Customer health
        health['customers']['total'] = db.execute(
            "SELECT COUNT(*) FROM customers"
        ).fetchone()[0]
        
        # Check CI orphaning
        ci_count = db.execute("SELECT COUNT(*) FROM ci_customer_profiles").fetchone()[0]
        if ci_count < health['customers']['total']:
            health['customers']['orphaned'] = health['customers']['total'] - ci_count
        
        # Check duplicates
        dup_count = db.execute("""
            SELECT COUNT(*) FROM (
                SELECT name FROM customers
                WHERE name IS NOT NULL AND name != ''
                GROUP BY LOWER(TRIM(name))
                HAVING COUNT(*) > 1
            )
        """).fetchone()[0]
        health['customers']['duplicates'] = dup_count
        
        # Item health
        health['items']['total'] = db.execute(
            "SELECT COUNT(*) FROM parts"
        ).fetchone()[0]
        
        wms_count = db.execute("SELECT COUNT(*) FROM wms_items").fetchone()[0]
        if wms_count < health['items']['total']:
            health['items']['orphaned'] = health['items']['total'] - wms_count
        
        # Employee health
        health['employees']['total'] = db.execute(
            "SELECT COUNT(*) FROM hr_employees"
        ).fetchone()[0]
        
        user_with_emp = db.execute("""
            SELECT COUNT(*) FROM users u
            JOIN hr_employees e ON u.id = e.user_id
        """).fetchone()[0]
        
        if user_with_emp < health['employees']['total']:
            health['employees']['orphaned'] = health['employees']['total'] - user_with_emp
        
        # Supplier health
        health['suppliers']['total'] = db.execute(
            "SELECT COUNT(*) FROM suppliers"
        ).fetchone()[0]
        
        # Warehouse health
        health['warehouses']['total'] = db.execute(
            "SELECT COUNT(*) FROM warehouses"
        ).fetchone()[0]
        
        wms_wh_count = db.execute("SELECT COUNT(*) FROM wms_warehouses").fetchone()[0]
        if wms_wh_count < health['warehouses']['total']:
            health['warehouses']['orphaned'] = health['warehouses']['total'] - wms_wh_count
    
    return health


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_master_data():
    """
    Initialize master data system.
    Creates any necessary mapping tables and ensures referential integrity.
    """
    # Ensure customer-company mapping table exists
    with get_db_context() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS customer_company_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                company_id INTEGER NOT NULL,
                is_primary INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(customer_id, company_id)
            )
        """)
        
        # Ensure item-company mapping table exists
        db.execute("""
            CREATE TABLE IF NOT EXISTS item_company_mapping (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                company_id INTEGER NOT NULL,
                is_primary INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(item_id, company_id)
            )
        """)
        
        db.commit()
