"""
WMS Shared Helpers
==================
Extracted from wms_routes.py — shared utility functions used across all
WMS sub-services and controllers.

These were previously nested inside register_wms_routes() making them
impossible to reuse. They are now standalone functions.
"""

import json
import re
import secrets
from datetime import datetime
from flask import session

from permissions import user_has_permission


# ---------------------------------------------------------------------------
# Permission Helpers
# ---------------------------------------------------------------------------

def get_wms_permissions(user_id=None, *, get_db=None):
    """Get WMS permissions for a user."""
    from database import get_db as _get_db
    db_func = get_db or _get_db
    db = db_func()
    if user_id is None:
        user_id = session.get('user_id')

    # Super admin check
    role = db.execute(
        'SELECT can_manage_users FROM roles WHERE id = ?',
        (session.get('role_id'),)
    ).fetchone()
    if role and role['can_manage_users']:
        return ['all']

    if session.get('role_name') == 'Global Admin':
        return ['all']

    perms = db.execute(
        'SELECT permission_key FROM wms_user_permissions WHERE user_id = ?',
        (user_id,)
    ).fetchall()
    return [p['permission_key'] for p in perms]


def scoped_warehouse_ids(user_id=None, *, get_db=None):
    """Return list of warehouse IDs the user is allowed to access."""
    from database import get_db as _get_db
    db_func = get_db or _get_db
    db = db_func()
    if user_id is None:
        user_id = session.get('user_id')
    perms = get_wms_permissions(user_id, get_db=db_func)
    if 'all' in perms or 'view_all_warehouses' in perms:
        rows = db.execute('SELECT id FROM wms_warehouses WHERE is_active = 1').fetchall()
        return [r['id'] for r in rows]
    rows = db.execute(
        'SELECT warehouse_id FROM wms_user_warehouses WHERE user_id = ?',
        (user_id,)
    ).fetchall()
    return [r['warehouse_id'] for r in rows]


def ensure_warehouse_allowed(warehouse_id, user_id=None, *, get_db=None):
    """Check if the user is allowed to access a given warehouse."""
    if warehouse_id is None:
        return False
    allowed = scoped_warehouse_ids(user_id, get_db=get_db)
    return int(warehouse_id) in allowed


def get_warehouse_filter(user_id=None, *, get_db=None):
    """Return a SQL fragment to filter by allowed warehouses."""
    from database import get_db as _get_db
    db_func = get_db or _get_db
    db = db_func()
    if user_id is None:
        user_id = session.get('user_id')
    perms = get_wms_permissions(user_id, get_db=db_func)
    if 'all' in perms or 'view_all_warehouses' in perms:
        return ""
    user_warehouses = db.execute(
        'SELECT warehouse_id FROM wms_user_warehouses WHERE user_id = ?',
        (user_id,)
    ).fetchall()
    if not user_warehouses:
        return " AND 1=0"
    wh_ids = [str(w['warehouse_id']) for w in user_warehouses]
    return f" AND warehouse_id IN ({','.join(wh_ids)})"


def get_company_filter(user_id=None, *, get_db=None):
    """Return a SQL fragment to filter by allowed companies."""
    from database import get_db as _get_db
    db_func = get_db or _get_db
    db = db_func()
    if user_id is None:
        user_id = session.get('user_id')
    perms = get_wms_permissions(user_id, get_db=db_func)
    if 'all' in perms or 'view_all_companies' in perms:
        return ""
    user_companies = db.execute(
        'SELECT company_id FROM wms_user_companies WHERE user_id = ?',
        (user_id,)
    ).fetchall()
    if not user_companies:
        return " AND 1=0"
    company_ids = [str(c['company_id']) for c in user_companies]
    return f" AND company_id IN ({','.join(company_ids)})"


# ---------------------------------------------------------------------------
# Code Generation
# ---------------------------------------------------------------------------

def generate_wms_code(code_type, company_id=None, *, get_db=None):
    """Generate a unique WMS document number (GRN, TRF, PCK, etc.)."""
    from database import get_db as _get_db
    db_func = get_db or _get_db
    db = db_func()
    year = datetime.now().year
    prefix_map = {
        'RECEIPT': 'GRN', 'TRANSFER': 'TRF', 'PICK': 'PCK',
        'PACK': 'PKG', 'DISPATCH': 'DSP', 'RETURN': 'RTN',
        'COUNT': 'CNT', 'ADJ': 'ADJ', 'PUTAWAY': 'PUT', 'INSPECT': 'INS',
    }
    prefix = prefix_map.get(code_type, 'WMS')
    seq_row = db.execute('''
        SELECT last_seq FROM wms_code_sequences
        WHERE code_type = ? AND year = ? AND (company_id = ? OR ? IS NULL)
        ORDER BY company_id DESC LIMIT 1
    ''', (code_type, year, company_id, company_id)).fetchone()
    if seq_row:
        new_seq = seq_row['last_seq'] + 1
        db.execute('''
            UPDATE wms_code_sequences SET last_seq = ?
            WHERE code_type = ? AND year = ? AND company_id IS ?
        ''', (new_seq, code_type, year, company_id))
    else:
        new_seq = 1
        db.execute('''
            INSERT INTO wms_code_sequences (code_type, year, company_id, last_seq)
            VALUES (?, ?, ?, ?)
        ''', (code_type, year, company_id, new_seq))
    db.commit()
    company_suffix = f"-C{company_id}" if company_id else ""
    return f"{prefix}-{year}-{new_seq:06d}{company_suffix}"


# ---------------------------------------------------------------------------
# Audit / Notifications
# ---------------------------------------------------------------------------

def log_wms_audit(action_type, entity_type, entity_id,
                  details=None, user_id=None, *, get_db=None):
    """Log a WMS audit entry."""
    from database import get_db as _get_db
    db_func = get_db or _get_db
    db = db_func()
    if user_id is None:
        user_id = session.get('user_id')
    details_json = json.dumps(details) if details else None
    try:
        db.execute('''
            INSERT INTO wms_audit_log
            (action_type, entity_type, entity_id, details, user_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (action_type, entity_type, entity_id,
              details_json, user_id, datetime.now().isoformat()))
        db.commit()
    except Exception as e:
        print(f"Audit log error: {e}")


def create_wms_notification(user_id, title, message,
                            notification_type='info',
                            related_entity_type=None,
                            related_entity_id=None, *, get_db=None):
    """Create a WMS notification."""
    from database import get_db as _get_db
    db_func = get_db or _get_db
    db = db_func()
    try:
        db.execute('''
            INSERT INTO wms_notifications
            (user_id, title, message, notification_type,
             related_entity_type, related_entity_id, is_read, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 0, ?)
        ''', (user_id, title, message, notification_type,
              related_entity_type, related_entity_id,
              datetime.now().isoformat()))
        db.commit()
    except Exception as e:
        print(f"Notification error: {e}")


# ---------------------------------------------------------------------------
# Validation Helpers
# ---------------------------------------------------------------------------

def parse_positive_int(value):
    """Parse and validate a positive integer."""
    try:
        value = int(value)
        return value if value > 0 else None
    except (TypeError, ValueError):
        return None


def parse_non_negative_float(value, field_label, errors, required=False):
    """Parse and validate a non-negative float, appending to errors list."""
    if value in (None, ''):
        if required:
            errors.append(f'{field_label} is required.')
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        errors.append(f'{field_label} must be a valid number.')
        return None
    if number < 0:
        errors.append(f'{field_label} cannot be negative.')
    return number


def validate_item_payload(data, item_id=None, *, get_db=None):
    """Validate item master relationships and numeric fields."""
    from database import get_db as _get_db
    db_func = get_db or _get_db
    db = db_func()
    errors = []
    item_code = (data.get('item_code') or '').strip()
    name = (data.get('name') or '').strip()
    if not item_code:
        errors.append('Item code is required.')
    if not name:
        errors.append('Item name is required.')
    if item_code:
        duplicate = db.execute(
            'SELECT id FROM wms_items WHERE item_code = ? AND (? IS NULL OR id != ?)',
            (item_code, item_id, item_id)
        ).fetchone()
        if duplicate:
            errors.append('Item code must be unique.')

    for field, label in (
        ('conversion_rate', 'Conversion rate'),
        ('weight_kg', 'Weight'), ('volume_m3', 'Volume'),
        ('length_cm', 'Length'), ('width_cm', 'Width'), ('height_cm', 'Height'),
        ('shelf_life_days', 'Shelf life'),
        ('min_stock_level', 'Minimum stock'), ('max_stock_level', 'Maximum stock'),
        ('reorder_point', 'Reorder point'), ('reorder_quantity', 'Reorder quantity'),
        ('safety_stock', 'Safety stock'),
        ('economic_order_quantity', 'Economic order quantity'),
    ):
        parse_non_negative_float(data.get(field), label, errors)

    min_stock = parse_non_negative_float(
        data.get('min_stock_level'), 'Minimum stock', [], False) or 0
    max_stock = parse_non_negative_float(
        data.get('max_stock_level'), 'Maximum stock', [], False)
    if max_stock is not None and max_stock < min_stock:
        errors.append('Maximum stock cannot be lower than minimum stock.')

    preferred_warehouse_id = parse_positive_int(data.get('preferred_warehouse_id'))
    preferred_location_id = parse_positive_int(data.get('preferred_location_id'))
    if preferred_warehouse_id:
        wh = db.execute(
            'SELECT id FROM wms_warehouses WHERE id = ? AND is_active = 1',
            (preferred_warehouse_id,)
        ).fetchone()
        if not wh or not ensure_warehouse_allowed(preferred_warehouse_id, get_db=db_func):
            errors.append('Preferred warehouse is invalid or outside your access.')
    if preferred_location_id:
        loc = db.execute(
            'SELECT id, warehouse_id FROM wms_locations WHERE id = ? AND is_active = 1',
            (preferred_location_id,)
        ).fetchone()
        if not loc:
            errors.append('Preferred location is invalid.')
        elif preferred_warehouse_id and loc['warehouse_id'] != preferred_warehouse_id:
            errors.append('Preferred location must belong to the preferred warehouse.')
        elif not ensure_warehouse_allowed(loc['warehouse_id'], get_db=db_func):
            errors.append('Preferred location is outside your warehouse access.')

    for field, table, label in (
        ('category_id', 'wms_item_categories', 'Category'),
        ('brand_id', 'wms_item_brands', 'Brand'),
        ('group_id', 'wms_item_groups', 'Item group'),
    ):
        value = parse_positive_int(data.get(field))
        if value and not db.execute(
            f'SELECT id FROM {table} WHERE id = ? AND is_active = 1', (value,)
        ).fetchone():
            errors.append(f'{label} is invalid.')
    return errors


def validate_location_code(code, warehouse_id=None):
    """Validate location code format."""
    if not code:
        return False, "Location code is required"
    code = code.strip().upper()
    if re.match(r'^\d{2}-\d{2}-\d{2}-\d{2}-[a-zA-Z0-9]{1,2}$', code):
        return True, code
    if len(code) <= 50:
        return True, code
    return False, "Invalid location code format"


# ---------------------------------------------------------------------------
# Display Helpers
# ---------------------------------------------------------------------------

def get_stock_status_name(status_code):
    """Get human-readable stock status name."""
    statuses = {
        'AVAILABLE': 'Available', 'RESERVED': 'Reserved',
        'ALLOCATED': 'Allocated', 'PICKED': 'Picked',
        'PACKED': 'Packed', 'SHIPPED': 'Shipped',
        'IN_TRANSIT': 'In Transit', 'RECEIVED': 'Received',
        'QUARANTINE': 'Quarantine', 'BLOCKED': 'Blocked',
        'DAMAGED': 'Damaged', 'EXPIRED': 'Expired',
        'RETURNED': 'Returned', 'INSPECTION': 'Inspection Pending',
        'HOLD': 'On Hold', 'NON_SALEABLE': 'Non-Saleable',
        'SAMPLE': 'Sample/Demo',
    }
    return statuses.get(status_code, status_code)


def get_rotation_policy_name(policy_code):
    """Get human-readable rotation policy name."""
    policies = {
        'FIFO': 'FIFO - First In, First Out',
        'LIFO': 'LIFO - Last In, First Out',
        'FEFO': 'FEFO - First Expired, First Out',
        'FMFO': 'FMFO - First Manufactured, First Out',
        'CUSTOM': 'Custom Priority',
        'MANUAL': 'Manual Selection',
    }
    return policies.get(policy_code, policy_code)
