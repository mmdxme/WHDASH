"""
WMS Routes - Warehouse Management System
Enterprise-grade warehouse management covering:
- Warehouse structure (companies, warehouses, zones, locations)
- Item master / SKU management
- Inventory tracking (batches, serials, expiry)
- Receiving / Inbound workflows
- Putaway operations
- Internal warehouse operations
- Replenishment
- Picking / Packing / Dispatch
- Transfers (inter-warehouse, inter-company)
- Returns / Reverse logistics
- Stock counting / cycle counts
- Quality control / inspection
- Space & capacity management
- Task / work queue management
- Documents / forms
- Reports & analytics
- Settings
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, Response
from functools import wraps
import sqlite3
import os
import json
import csv
import io
import hmac
import secrets
import random
from datetime import datetime, timedelta, date
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from collections import Counter
import re

from permissions import user_has_permission

# Import export utilities
from export_utils import (
    send_export_response,
    get_export_columns
)

# Module-level flag to track WMS schema initialization
# This persists across database connections unlike connection-attribute flags
_wms_schema_initialized = False


# =============================================================================
# EXPORT TYPES AND COLUMNS
# =============================================================================

WMS_EXPORT_TYPES = [
    'csv', 'excel_text', 'excel_general', 'json', 'xml', 'txt',
    'pdf', 'docx', 'html', 'printable', 'barcode', 'api',
    'email', 'zip', 'backup', 'sql_dump', 'dashboard',
    'summary', 'detailed', 'audit_log'
]

WMS_EXPORT_COLUMNS = {
    'warehouses': ['warehouse_id', 'name', 'location', 'type', 'capacity', 'status'],
    'items': ['item_id', 'sku', 'name', 'category', 'unit', 'reorder_level'],
    'inventory': ['item_id', 'warehouse', 'location', 'quantity', 'reserved', 'available'],
    'receiving': ['receiving_id', 'po_number', 'supplier', 'received_date', 'status'],
    'putaway': ['putaway_id', 'receiving_id', 'item_id', 'location', 'quantity', 'status'],
    'transfers': ['transfer_id', 'from_warehouse', 'to_warehouse', 'item', 'quantity', 'status'],
    'picking': ['picking_id', 'order_number', 'item', 'quantity', 'picker', 'status'],
    'returns': ['return_id', 'return_number', 'item', 'quantity', 'reason', 'status']
}


def register_wms_routes(app, get_db):
    """Register all WMS routes with the Flask app."""

    # ============================================================
    # DECORATORS & HELPERS
    # ============================================================

    def wms_permission_required(resource, action):
        """Decorator to check WMS permissions using central permissions system."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                wants_json = request.is_json or request.accept_mimetypes.best == 'application/json' or request.path.startswith('/api/')
                if 'user_id' not in session:
                    if wants_json:
                        return jsonify({'success': False, 'error': 'Authentication required'}), 401
                    return redirect(url_for('login'))
                user_id = session.get('user_id')
                if session.get('role_name') == 'Global Admin':
                    return f(*args, **kwargs)
                if not user_has_permission(user_id, 'wms', resource, action):
                    if wants_json:
                        return jsonify({'success': False, 'error': 'Permission denied'}), 403
                    flash(f"Access denied. You need '{action}' permission on '{resource}'.", "error")
                    return redirect(url_for('wms_dashboard'))
                return f(*args, **kwargs)
            return decorated_function
        return decorator

    def validate_wms_csrf():
        """Validate mutating WMS requests against the session CSRF token."""
        token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
        stored = session.get('csrf_token')
        return bool(token and stored and hmac.compare_digest(str(token), str(stored)))

    def wms_csrf_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method in ('POST', 'PUT', 'PATCH', 'DELETE') and not validate_wms_csrf():
                if request.is_json:
                    return jsonify({'success': False, 'error': 'CSRF validation failed'}), 403
                flash('CSRF validation failed. Please refresh the page and try again.', 'error')
                return redirect(request.referrer or url_for('wms_dashboard'))
            return f(*args, **kwargs)
        return decorated_function

    def parse_positive_int(value):
        try:
            value = int(value)
            return value if value > 0 else None
        except (TypeError, ValueError):
            return None

    def parse_non_negative_float(value, field_label, errors, required=False):
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

    def validate_item_payload(data, item_id=None):
        """Validate item master relationships and dangerous numeric fields."""
        db = get_db()
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
            ('weight_kg', 'Weight'),
            ('volume_m3', 'Volume'),
            ('length_cm', 'Length'),
            ('width_cm', 'Width'),
            ('height_cm', 'Height'),
            ('shelf_life_days', 'Shelf life'),
            ('min_stock_level', 'Minimum stock'),
            ('max_stock_level', 'Maximum stock'),
            ('reorder_point', 'Reorder point'),
            ('reorder_quantity', 'Reorder quantity'),
            ('safety_stock', 'Safety stock'),
            ('economic_order_quantity', 'Economic order quantity'),
        ):
            parse_non_negative_float(data.get(field), label, errors)

        min_stock = parse_non_negative_float(data.get('min_stock_level'), 'Minimum stock', [], False) or 0
        max_stock = parse_non_negative_float(data.get('max_stock_level'), 'Maximum stock', [], False)
        if max_stock is not None and max_stock < min_stock:
            errors.append('Maximum stock cannot be lower than minimum stock.')

        preferred_warehouse_id = parse_positive_int(data.get('preferred_warehouse_id'))
        preferred_location_id = parse_positive_int(data.get('preferred_location_id'))
        if preferred_warehouse_id:
            wh = db.execute('SELECT id FROM wms_warehouses WHERE id = ? AND is_active = 1', (preferred_warehouse_id,)).fetchone()
            if not wh or not ensure_warehouse_allowed(preferred_warehouse_id):
                errors.append('Preferred warehouse is invalid or outside your access.')
        if preferred_location_id:
            loc = db.execute('SELECT id, warehouse_id FROM wms_locations WHERE id = ? AND is_active = 1', (preferred_location_id,)).fetchone()
            if not loc:
                errors.append('Preferred location is invalid.')
            elif preferred_warehouse_id and loc['warehouse_id'] != preferred_warehouse_id:
                errors.append('Preferred location must belong to the preferred warehouse.')
            elif not ensure_warehouse_allowed(loc['warehouse_id']):
                errors.append('Preferred location is outside your warehouse access.')

        for field, table, label in (
            ('category_id', 'wms_item_categories', 'Category'),
            ('brand_id', 'wms_item_brands', 'Brand'),
            ('group_id', 'wms_item_groups', 'Item group'),
        ):
            value = parse_positive_int(data.get(field))
            if value and not db.execute(f'SELECT id FROM {table} WHERE id = ? AND is_active = 1', (value,)).fetchone():
                errors.append(f'{label} is invalid.')
        return errors

    def scoped_warehouse_ids(user_id=None):
        db = get_db()
        if user_id is None:
            user_id = session.get('user_id')
        perms = get_wms_permissions(user_id)
        if 'all' in perms or 'view_all_warehouses' in perms:
            rows = db.execute('SELECT id FROM wms_warehouses WHERE is_active = 1').fetchall()
            return [r['id'] for r in rows]
        rows = db.execute('SELECT warehouse_id FROM wms_user_warehouses WHERE user_id = ?', (user_id,)).fetchall()
        return [r['warehouse_id'] for r in rows]

    def ensure_warehouse_allowed(warehouse_id, user_id=None):
        if warehouse_id is None:
            return False
        allowed = scoped_warehouse_ids(user_id)
        return int(warehouse_id) in allowed

    def ensure_quality_hold_tables():
        db = get_db()
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_quality_holds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hold_number TEXT UNIQUE NOT NULL,
                warehouse_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                lot_id INTEGER,
                serial_number_id INTEGER,
                location_id INTEGER,
                quantity_held REAL DEFAULT 0,
                hold_reason TEXT NOT NULL,
                hold_type TEXT DEFAULT 'INSPECTION',
                source_receipt_line_id INTEGER,
                source_return_line_id INTEGER,
                source_inspection_id INTEGER,
                status TEXT DEFAULT 'ACTIVE',
                hold_notes TEXT,
                held_by INTEGER,
                held_at TEXT DEFAULT CURRENT_TIMESTAMP,
                released_by INTEGER,
                released_at TEXT,
                release_reason TEXT,
                expected_clear_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        db.execute('CREATE INDEX IF NOT EXISTS idx_wms_quality_holds_status_wh ON wms_quality_holds(status, warehouse_id)')
        db.execute('CREATE INDEX IF NOT EXISTS idx_wms_quality_holds_item_lot ON wms_quality_holds(item_id, lot_id, location_id)')
        db.commit()

    def get_wms_permissions(user_id=None):
        """Get WMS permissions for a user."""
        db = get_db()
        if user_id is None:
            user_id = session.get('user_id')

        # Check if user is super admin
        role = db.execute('SELECT can_manage_users FROM roles WHERE id = ?', (session.get('role_id'),)).fetchone()
        if role and role['can_manage_users']:
            return ['all']

        # Also check Global Admin role_name for consistency
        if session.get('role_name') == 'Global Admin':
            return ['all']

        # Get WMS-specific permissions
        perms = db.execute('''
            SELECT permission_key FROM wms_user_permissions WHERE user_id = ?
        ''', (user_id,)).fetchall()
        return [p['permission_key'] for p in perms]

    def log_wms_audit(action_type, entity_type, entity_id, details=None, user_id=None):
        """Log a WMS audit entry."""
        db = get_db()
        if user_id is None:
            user_id = session.get('user_id')
        details_json = json.dumps(details) if details else None
        try:
            db.execute('''
                INSERT INTO wms_audit_log
                (action_type, entity_type, entity_id, details, user_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (action_type, entity_type, entity_id, details_json, user_id, datetime.now().isoformat()))
            db.commit()
        except Exception as e:
            print(f"Audit log error: {e}")

    def create_wms_notification(user_id, title, message, notification_type='info', related_entity_type=None, related_entity_id=None):
        """Create a WMS notification."""
        db = get_db()
        try:
            db.execute('''
                INSERT INTO wms_notifications
                (user_id, title, message, notification_type, related_entity_type, related_entity_id, is_read, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?)
            ''', (user_id, title, message, notification_type, related_entity_type, related_entity_id, datetime.now().isoformat()))
            db.commit()
        except Exception as e:
            print(f"Notification error: {e}")

    def get_company_filter(user_id=None):
        """Get company filter based on user permissions."""
        db = get_db()
        if user_id is None:
            user_id = session.get('user_id')
        # Check if user can view all companies
        perms = get_wms_permissions(user_id)
        if 'all' in perms or 'view_all_companies' in perms:
            return ""
        # Get user's assigned companies
        user_companies = db.execute('''
            SELECT company_id FROM wms_user_companies WHERE user_id = ?
        ''', (user_id,)).fetchall()
        if not user_companies:
            return " AND 1=0"
        company_ids = [str(c['company_id']) for c in user_companies]
        return f" AND company_id IN ({','.join(company_ids)})"

    def get_warehouse_filter(user_id=None):
        """Get warehouse filter based on user permissions."""
        db = get_db()
        if user_id is None:
            user_id = session.get('user_id')
        perms = get_wms_permissions(user_id)
        if 'all' in perms or 'view_all_warehouses' in perms:
            return ""
        user_warehouses = db.execute('''
            SELECT warehouse_id FROM wms_user_warehouses WHERE user_id = ?
        ''', (user_id,)).fetchall()
        if not user_warehouses:
            return " AND 1=0"
        wh_ids = [str(w['warehouse_id']) for w in user_warehouses]
        return f" AND warehouse_id IN ({','.join(wh_ids)})"

    def generate_wms_code(code_type, company_id=None):
        """Generate a unique WMS document/code."""
        db = get_db()
        year = datetime.now().year
        prefix_map = {
            'RECEIPT': 'GRN',
            'TRANSFER': 'TRF',
            'PICK': 'PCK',
            'PACK': 'PKG',
            'DISPATCH': 'DSP',
            'RETURN': 'RTN',
            'COUNT': 'CNT',
            'ADJ': 'ADJ',
            'PUTAWAY': 'PUT',
            'INSPECT': 'INS',
        }
        prefix = prefix_map.get(code_type, 'WMS')
        # Get next sequence
        seq_row = db.execute('''
            SELECT last_seq FROM wms_code_sequences
            WHERE code_type = ? AND year = ? AND (company_id = ? OR ? IS NULL)
            ORDER BY company_id DESC LIMIT 1
        ''', (code_type, year, company_id, company_id)).fetchone()
        if seq_row:
            new_seq = seq_row['last_seq'] + 1
            db.execute('''
                UPDATE wms_code_sequences SET last_seq = ? WHERE code_type = ? AND year = ? AND company_id IS ?
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

    def validate_location_code(code, warehouse_id=None):
        """Validate location code format."""
        if not code:
            return False, "Location code is required"
        code = code.strip().upper()
        # Support multiple formats:
        # 1. 5-tier: 01-12-03-05-A (Rack-Bay-Level-Position-Bin)
        # 2. Barcode: BLK-XXXXXX
        # 3. Free text: up to 50 chars
        if re.match(r'^\d{2}-\d{2}-\d{2}-\d{2}-[a-zA-Z0-9]{1,2}$', code):
            return True, code
        if len(code) <= 50:
            return True, code
        return False, "Invalid location code format"

    def get_stock_status_name(status_code):
        """Get human-readable stock status name."""
        statuses = {
            'AVAILABLE': 'Available',
            'RESERVED': 'Reserved',
            'ALLOCATED': 'Allocated',
            'PICKED': 'Picked',
            'PACKED': 'Packed',
            'SHIPPED': 'Shipped',
            'IN_TRANSIT': 'In Transit',
            'RECEIVED': 'Received',
            'QUARANTINE': 'Quarantine',
            'BLOCKED': 'Blocked',
            'DAMAGED': 'Damaged',
            'EXPIRED': 'Expired',
            'RETURNED': 'Returned',
            'INSPECTION': 'Inspection Pending',
            'HOLD': 'On Hold',
            'NON_SALEABLE': 'Non-Saleable',
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

    # ============================================================
    # DATABASE INITIALIZATION - WMS TABLES
    # ============================================================

    def init_wms_tables():
        """Initialize all WMS database tables."""
        global _wms_schema_initialized
        if _wms_schema_initialized:
            return
        db = get_db()

        # WMS Settings
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                setting_key TEXT UNIQUE NOT NULL,
                setting_value TEXT,
                setting_type TEXT DEFAULT 'string',
                category TEXT DEFAULT 'general',
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Companies (extending existing companies table with WMS fields)
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                name_local TEXT,
                country TEXT,
                currency TEXT DEFAULT 'USD',
                language TEXT DEFAULT 'en',
                timezone TEXT DEFAULT 'UTC',
                address TEXT,
                phone TEXT,
                email TEXT,
                tax_id TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        ''')

        # Warehouses
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_warehouses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                name_local TEXT,
                type TEXT DEFAULT 'main',
                address TEXT,
                city TEXT,
                country TEXT,
                phone TEXT,
                email TEXT,
                manager_id INTEGER,
                is_active INTEGER DEFAULT 1,
                allow_receiving INTEGER DEFAULT 1,
                allow_shipping INTEGER DEFAULT 1,
                allow_storage INTEGER DEFAULT 1,
                default_rotation_policy TEXT DEFAULT 'FIFO',
                min_temp REAL,
                max_temp REAL,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES wms_companies(id)
            )
        ''')

        # Warehouse Zones
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_zones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                warehouse_id INTEGER NOT NULL,
                code TEXT NOT NULL,
                name TEXT NOT NULL,
                zone_type TEXT NOT NULL,
                description TEXT,
                picking_enabled INTEGER DEFAULT 1,
                putaway_enabled INTEGER DEFAULT 1,
                replenishment_enabled INTEGER DEFAULT 1,
                is_active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                UNIQUE(warehouse_id, code)
            )
        ''')

        # Warehouse Locations (Bins)
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                warehouse_id INTEGER NOT NULL,
                zone_id INTEGER,
                parent_location_id INTEGER,
                code TEXT NOT NULL,
                barcode TEXT,
                name TEXT,
                location_type TEXT NOT NULL,
                level INTEGER DEFAULT 0,
                coordinates_rack TEXT,
                coordinates_bay TEXT,
                coordinates_level TEXT,
                coordinates_position TEXT,
                coordinates_bin TEXT,
                capacity_pallets INTEGER,
                capacity_weight_kg REAL,
                capacity_volume_m3 REAL,
                capacity_cartons INTEGER,
                current_pallets INTEGER DEFAULT 0,
                current_weight_kg REAL DEFAULT 0,
                current_volume_m3 REAL DEFAULT 0,
                current_cartons INTEGER DEFAULT 0,
                picking_enabled INTEGER DEFAULT 1,
                putaway_enabled INTEGER DEFAULT 1,
                replenishment_enabled INTEGER DEFAULT 1,
                is_locked INTEGER DEFAULT 0,
                lock_reason TEXT,
                is_active INTEGER DEFAULT 1,
                is_empty INTEGER DEFAULT 1,
                temperature_min REAL,
                temperature_max REAL,
                humidity_min REAL,
                humidity_max REAL,
                preferred_item_class TEXT,
                cycle_count_class TEXT,
                last_count_date TEXT,
                last_count_by INTEGER,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (zone_id) REFERENCES wms_zones(id),
                FOREIGN KEY (parent_location_id) REFERENCES wms_locations(id),
                UNIQUE(warehouse_id, code)
            )
        ''')

        # Item Categories
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_item_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                name_local TEXT,
                description TEXT,
                level INTEGER DEFAULT 0,
                path TEXT,
                is_active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES wms_item_categories(id)
            )
        ''')

        # Item Brands
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_item_brands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                name_local TEXT,
                manufacturer TEXT,
                country TEXT,
                website TEXT,
                logo_url TEXT,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Item Groups
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_item_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                name_local TEXT,
                description TEXT,
                is_active INTEGER DEFAULT 1,
                sort_order INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Items (Master / SKU)
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_code TEXT UNIQUE NOT NULL,
                sku TEXT,
                barcode TEXT,
                qr_code TEXT,
                part_number TEXT,
                oem_number TEXT,
                alternate_part_numbers TEXT,
                supplier_code TEXT,
                name TEXT NOT NULL,
                name_local TEXT,
                short_name TEXT,
                long_description TEXT,
                brand_id INTEGER,
                category_id INTEGER,
                group_id INTEGER,
                item_type TEXT DEFAULT 'finished_goods',
                unit_of_measure TEXT DEFAULT 'PCS',
                secondary_uom TEXT,
                conversion_rate REAL DEFAULT 1.0,
                weight_kg REAL,
                volume_m3 REAL,
                length_cm REAL,
                width_cm REAL,
                height_cm REAL,
                color TEXT,
                size TEXT,
                material TEXT,
                country_of_origin TEXT,
                hazard_class TEXT,
                temperature_requirement TEXT,
                shelf_life_days INTEGER,
                expiry_tracking INTEGER DEFAULT 0,
                batch_tracking INTEGER DEFAULT 0,
                lot_tracking INTEGER DEFAULT 0,
                serial_tracking INTEGER DEFAULT 0,
                quality_inspection_required INTEGER DEFAULT 0,
                min_stock_level REAL DEFAULT 0,
                max_stock_level REAL,
                reorder_point REAL DEFAULT 0,
                reorder_quantity REAL,
                safety_stock REAL DEFAULT 0,
                economic_order_quantity REAL,
                preferred_warehouse_id INTEGER,
                preferred_location_id INTEGER,
                rotation_policy TEXT DEFAULT 'FIFO',
                picking_strategy TEXT,
                packing_instruction TEXT,
                handling_instruction TEXT,
                selling_status TEXT DEFAULT 'active',
                procurement_status TEXT DEFAULT 'active',
                abc_class TEXT,
                image_url TEXT,
                is_active INTEGER DEFAULT 1,
                is_kit INTEGER DEFAULT 0,
                is_bundle INTEGER DEFAULT 0,
                kit_components TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (brand_id) REFERENCES wms_item_brands(id),
                FOREIGN KEY (category_id) REFERENCES wms_item_categories(id),
                FOREIGN KEY (group_id) REFERENCES wms_item_groups(id),
                FOREIGN KEY (preferred_warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (preferred_location_id) REFERENCES wms_locations(id)
            )
        ''')
        item_columns = {row['name'] for row in db.execute("PRAGMA table_info(wms_items)").fetchall()}
        if 'temperature_requirement' not in item_columns:
            db.execute('ALTER TABLE wms_items ADD COLUMN temperature_requirement TEXT')

        # Item Suppliers
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_item_suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                supplier_id INTEGER NOT NULL,
                supplier_code TEXT,
                supplier_part_number TEXT,
                lead_time_days INTEGER,
                moq REAL DEFAULT 1,
                unit_cost REAL,
                currency TEXT DEFAULT 'USD',
                is_preferred INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        ''')

        # Item Relations (Substitutes, Equivalents, etc.)
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_item_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                related_item_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                is_bidirectional INTEGER DEFAULT 0,
                is_approved INTEGER DEFAULT 1,
                priority INTEGER DEFAULT 0,
                notes TEXT,
                valid_from TEXT,
                valid_to TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (related_item_id) REFERENCES wms_items(id)
            )
        ''')

        # Inventory Lots / Batches
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_lots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lot_number TEXT UNIQUE NOT NULL,
                item_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL,
                location_id INTEGER,
                quantity REAL DEFAULT 0,
                reserved_quantity REAL DEFAULT 0,
                blocked_quantity REAL DEFAULT 0,
                manufacturing_date TEXT,
                expiry_date TEXT,
                received_date TEXT,
                supplier_batch_number TEXT,
                production_line TEXT,
                status TEXT DEFAULT 'ACTIVE',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (location_id) REFERENCES wms_locations(id)
            )
        ''')

        # Serial Numbers
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_serial_numbers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                serial_number TEXT UNIQUE NOT NULL,
                item_id INTEGER NOT NULL,
                lot_id INTEGER,
                warehouse_id INTEGER NOT NULL,
                location_id INTEGER,
                status TEXT DEFAULT 'AVAILABLE',
                assigned_to TEXT,
                assigned_date TEXT,
                warranty_expiry_date TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (lot_id) REFERENCES wms_lots(id),
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (location_id) REFERENCES wms_locations(id)
            )
        ''')

        # Inventory Balances (current stock by item/lot/location)
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_inventory_balances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                lot_id INTEGER,
                serial_number_id INTEGER,
                warehouse_id INTEGER NOT NULL,
                location_id INTEGER,
                company_id INTEGER,
                quantity REAL DEFAULT 0,
                reserved_quantity REAL DEFAULT 0,
                allocated_quantity REAL DEFAULT 0,
                blocked_quantity REAL DEFAULT 0,
                status TEXT DEFAULT 'AVAILABLE',
                last_movement_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (lot_id) REFERENCES wms_lots(id),
                FOREIGN KEY (serial_number_id) REFERENCES wms_serial_numbers(id),
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (location_id) REFERENCES wms_locations(id),
                FOREIGN KEY (company_id) REFERENCES wms_companies(id),
                UNIQUE(item_id, lot_id, serial_number_id, warehouse_id, location_id, company_id, status)
            )
        ''')

        # Inventory Ledger (movement history)
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_inventory_ledger (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_type TEXT NOT NULL,
                transaction_number TEXT,
                reference_type TEXT,
                reference_number TEXT,
                item_id INTEGER NOT NULL,
                lot_id INTEGER,
                serial_number_id INTEGER,
                warehouse_id INTEGER NOT NULL,
                location_id INTEGER,
                company_id INTEGER,
                quantity_before REAL,
                quantity_moved REAL,
                quantity_after REAL,
                status_before TEXT,
                status_after TEXT,
                reason_code TEXT,
                notes TEXT,
                user_id INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (lot_id) REFERENCES wms_lots(id),
                FOREIGN KEY (serial_number_id) REFERENCES wms_serial_numbers(id),
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (location_id) REFERENCES wms_locations(id),
                FOREIGN KEY (company_id) REFERENCES wms_companies(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Inbound Receipts
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_inbound_receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_number TEXT UNIQUE NOT NULL,
                receipt_type TEXT NOT NULL,
                warehouse_id INTEGER NOT NULL,
                company_id INTEGER,
                supplier_id INTEGER,
                po_reference TEXT,
                asn_reference TEXT,
                expected_date TEXT,
                actual_arrival_date TEXT,
                received_by INTEGER,
                quality_status TEXT DEFAULT 'PENDING',
                status TEXT DEFAULT 'EXPECTED',
                notes TEXT,
                attachments TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (company_id) REFERENCES wms_companies(id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (received_by) REFERENCES users(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        # Inbound Receipt Lines
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_inbound_receipt_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                receipt_id INTEGER NOT NULL,
                line_number INTEGER,
                item_id INTEGER NOT NULL,
                expected_quantity REAL,
                received_quantity REAL DEFAULT 0,
                accepted_quantity REAL DEFAULT 0,
                rejected_quantity REAL DEFAULT 0,
                damaged_quantity REAL DEFAULT 0,
                short_quantity REAL DEFAULT 0,
                over_quantity REAL DEFAULT 0,
                lot_number TEXT,
                expiry_date TEXT,
                serial_numbers TEXT,
                location_id INTEGER,
                unit_cost REAL,
                currency TEXT DEFAULT 'USD',
                quality_status TEXT DEFAULT 'PENDING',
                status TEXT DEFAULT 'PENDING',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (receipt_id) REFERENCES wms_inbound_receipts(id),
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (location_id) REFERENCES wms_locations(id)
            )
        ''')

        # ASN (Advanced Shipping Notice)
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_asn (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asn_number TEXT UNIQUE NOT NULL,
                partner_id INTEGER,
                warehouse_id INTEGER,
                expected_date TEXT,
                actual_date TEXT,
                status TEXT DEFAULT 'EXPECTED',
                po_number TEXT,
                notes TEXT,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES wms_edi_partners(id),
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id)
            )
        ''')

        # ASN Lines
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_asn_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asn_id INTEGER NOT NULL,
                line_number INTEGER,
                item_id INTEGER NOT NULL,
                expected_quantity REAL NOT NULL,
                received_quantity REAL DEFAULT 0,
                unit_cost REAL,
                lot_number TEXT,
                expiry_date TEXT,
                status TEXT DEFAULT 'PENDING',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (asn_id) REFERENCES wms_asn(id),
                FOREIGN KEY (item_id) REFERENCES wms_items(id)
            )
        ''')

        # Cross-Dock
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_cross_dock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cross_dock_number TEXT UNIQUE NOT NULL,
                receipt_id INTEGER,
                warehouse_id INTEGER,
                dock_door_id INTEGER,
                status TEXT DEFAULT 'PENDING',
                priority INTEGER DEFAULT 5,
                scheduled_arrival TEXT,
                actual_arrival TEXT,
                scheduled_departure TEXT,
                actual_departure TEXT,
                notes TEXT,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (receipt_id) REFERENCES wms_inbound_receipts(id),
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (dock_door_id) REFERENCES wms_dock_doors(id)
            )
        ''')

        # Putaway Tasks
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_putaway_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_number TEXT UNIQUE NOT NULL,
                receipt_line_id INTEGER,
                item_id INTEGER NOT NULL,
                lot_id INTEGER,
                source_location_id INTEGER,
                destination_location_id INTEGER,
                suggested_location_id INTEGER,
                quantity REAL NOT NULL,
                priority INTEGER DEFAULT 5,
                status TEXT DEFAULT 'PENDING',
                assigned_to INTEGER,
                started_at TEXT,
                completed_at TEXT,
                completed_by INTEGER,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (receipt_line_id) REFERENCES wms_inbound_receipt_lines(id),
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (lot_id) REFERENCES wms_lots(id),
                FOREIGN KEY (source_location_id) REFERENCES wms_locations(id),
                FOREIGN KEY (destination_location_id) REFERENCES wms_locations(id),
                FOREIGN KEY (suggested_location_id) REFERENCES wms_locations(id),
                FOREIGN KEY (assigned_to) REFERENCES users(id),
                FOREIGN KEY (completed_by) REFERENCES users(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        # Putaway Rules Engine
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_putaway_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL,
                rule_type TEXT NOT NULL,
                description TEXT,
                priority INTEGER DEFAULT 5,
                is_active INTEGER DEFAULT 1,
                conditions_json TEXT,
                action_type TEXT NOT NULL,
                target_zone_id INTEGER,
                target_location_type TEXT,
                target_warehouse_id INTEGER,
                min_capacity_weight REAL,
                max_capacity_weight REAL,
                min_capacity_volume REAL,
                max_capacity_volume REAL,
                velocity_class TEXT,
                hazmat_class TEXT,
                temperature_required INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (target_zone_id) REFERENCES wms_zones(id),
                FOREIGN KEY (target_warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        # Putaway Rule Audit Log
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_putaway_rule_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id INTEGER,
                receipt_line_id INTEGER,
                item_id INTEGER,
                suggested_location_id INTEGER,
                actual_location_id INTEGER,
                is_accepted INTEGER DEFAULT 0,
                is_overridden INTEGER DEFAULT 0,
                override_reason TEXT,
                decision_time_ms INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (rule_id) REFERENCES wms_putaway_rules(id),
                FOREIGN KEY (receipt_line_id) REFERENCES wms_inbound_receipt_lines(id),
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (suggested_location_id) REFERENCES wms_locations(id),
                FOREIGN KEY (actual_location_id) REFERENCES wms_locations(id)
            )
        ''')

        # Internal Movements
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_internal_movements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                movement_number TEXT UNIQUE NOT NULL,
                movement_type TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                lot_id INTEGER,
                serial_number_id INTEGER,
                source_location_id INTEGER,
                destination_location_id INTEGER,
                quantity REAL NOT NULL,
                reason_code TEXT,
                status TEXT DEFAULT 'COMPLETED',
                reference_type TEXT,
                reference_number TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (lot_id) REFERENCES wms_lots(id),
                FOREIGN KEY (serial_number_id) REFERENCES wms_serial_numbers(id),
                FOREIGN KEY (source_location_id) REFERENCES wms_locations(id),
                FOREIGN KEY (destination_location_id) REFERENCES wms_locations(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        # Replenishment Tasks
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_replenishment_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_number TEXT UNIQUE NOT NULL,
                item_id INTEGER NOT NULL,
                lot_id INTEGER,
                source_location_id INTEGER,
                destination_location_id INTEGER,
                quantity REAL NOT NULL,
                priority INTEGER DEFAULT 5,
                replenishment_type TEXT DEFAULT 'PICKING_AREA',
                status TEXT DEFAULT 'PENDING',
                assigned_to INTEGER,
                started_at TEXT,
                completed_at TEXT,
                completed_by INTEGER,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (lot_id) REFERENCES wms_lots(id),
                FOREIGN KEY (source_location_id) REFERENCES wms_locations(id),
                FOREIGN KEY (destination_location_id) REFERENCES wms_locations(id),
                FOREIGN KEY (assigned_to) REFERENCES users(id),
                FOREIGN KEY (completed_by) REFERENCES users(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        # Replenishment Min/Max Configuration
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_replenishment_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL,
                min_quantity REAL DEFAULT 0,
                max_quantity REAL DEFAULT 0,
                reorder_point REAL DEFAULT 0,
                reorder_quantity REAL DEFAULT 0,
                safety_stock REAL DEFAULT 0,
                lead_time_days INTEGER DEFAULT 7,
                abc_class TEXT,
                velocity_class TEXT,
                replenishment_method TEXT DEFAULT 'MIN_MAX',
                is_active INTEGER DEFAULT 1,
                last_calculated_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id)
            )
        ''')

        # Demand Forecasting Data
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_demand_forecast (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                forecast_date DATE NOT NULL,
                predicted_quantity REAL NOT NULL,
                confidence_level REAL DEFAULT 0.95,
                forecast_method TEXT DEFAULT 'MOVING_AVG',
                actual_quantity REAL,
                variance REAL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                UNIQUE(item_id, forecast_date)
            )
        ''')

        # Kanban Configuration
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_kanban_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                source_location_id INTEGER NOT NULL,
                destination_location_id INTEGER NOT NULL,
                kanban_size INTEGER DEFAULT 1,
                current_cards INTEGER DEFAULT 0,
                max_cards INTEGER DEFAULT 5,
                signal_point INTEGER DEFAULT 2,
                is_active INTEGER DEFAULT 1,
                last_refill_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (source_location_id) REFERENCES wms_locations(id),
                FOREIGN KEY (destination_location_id) REFERENCES wms_locations(id)
            )
        ''')

        # Replenishment Suggestion Log
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_replenishment_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL,
                suggested_quantity REAL NOT NULL,
                reason_code TEXT,
                urgency TEXT DEFAULT 'NORMAL',
                status TEXT DEFAULT 'PENDING',
                reviewed_by INTEGER,
                reviewed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (reviewed_by) REFERENCES users(id)
            )
        ''')

        # Outbound Orders
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_outbound_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number TEXT UNIQUE NOT NULL,
                order_type TEXT NOT NULL,
                warehouse_id INTEGER NOT NULL,
                company_id INTEGER,
                customer_id INTEGER,
                so_reference TEXT,
                order_date TEXT,
                required_date TEXT,
                shipped_date TEXT,
                status TEXT DEFAULT 'DRAFT',
                priority INTEGER DEFAULT 5,
                picking_strategy TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (company_id) REFERENCES wms_companies(id),
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        # Outbound Order Lines
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_outbound_order_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                line_number INTEGER,
                item_id INTEGER NOT NULL,
                ordered_quantity REAL,
                allocated_quantity REAL DEFAULT 0,
                picked_quantity REAL DEFAULT 0,
                packed_quantity REAL DEFAULT 0,
                shipped_quantity REAL DEFAULT 0,
                reserved_lot_id INTEGER,
                reserved_serial_numbers TEXT,
                status TEXT DEFAULT 'PENDING',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES wms_outbound_orders(id),
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (reserved_lot_id) REFERENCES wms_lots(id)
            )
        ''')

        # Pick Tasks
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_pick_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_number TEXT UNIQUE NOT NULL,
                order_line_id INTEGER,
                order_id INTEGER,
                item_id INTEGER NOT NULL,
                lot_id INTEGER,
                serial_number_id INTEGER,
                source_location_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                picked_quantity REAL DEFAULT 0,
                priority INTEGER DEFAULT 5,
                pick_sequence INTEGER,
                status TEXT DEFAULT 'PENDING',
                assigned_to INTEGER,
                started_at TEXT,
                completed_at TEXT,
                completed_by INTEGER,
                short_pick_reason TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (order_line_id) REFERENCES wms_outbound_order_lines(id),
                FOREIGN KEY (order_id) REFERENCES wms_outbound_orders(id),
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (lot_id) REFERENCES wms_lots(id),
                FOREIGN KEY (serial_number_id) REFERENCES wms_serial_numbers(id),
                FOREIGN KEY (source_location_id) REFERENCES wms_locations(id),
                FOREIGN KEY (assigned_to) REFERENCES users(id),
                FOREIGN KEY (completed_by) REFERENCES users(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        # Pack Tasks
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_pack_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_number TEXT UNIQUE NOT NULL,
                order_id INTEGER NOT NULL,
                pack_station TEXT,
                carton_count INTEGER DEFAULT 1,
                packed_weight_kg REAL,
                packed_dimensions_l REAL,
                packed_dimensions_w REAL,
                packed_dimensions_h REAL,
                packing_material TEXT,
                status TEXT DEFAULT 'PENDING',
                assigned_to INTEGER,
                started_at TEXT,
                completed_at TEXT,
                completed_by INTEGER,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (order_id) REFERENCES wms_outbound_orders(id),
                FOREIGN KEY (assigned_to) REFERENCES users(id),
                FOREIGN KEY (completed_by) REFERENCES users(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        # Shipments / Dispatch
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_shipments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shipment_number TEXT UNIQUE NOT NULL,
                order_id INTEGER,
                warehouse_id INTEGER NOT NULL,
                company_id INTEGER,
                carrier_id INTEGER,
                carrier_name TEXT,
                tracking_number TEXT,
                vehicle_id INTEGER,
                driver_name TEXT,
                departure_date TEXT,
                arrival_date TEXT,
                status TEXT DEFAULT 'PREPARING',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (order_id) REFERENCES wms_outbound_orders(id),
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (company_id) REFERENCES wms_companies(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        # Transfers
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_transfers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transfer_number TEXT UNIQUE NOT NULL,
                transfer_type TEXT NOT NULL,
                source_warehouse_id INTEGER NOT NULL,
                destination_warehouse_id INTEGER NOT NULL,
                source_company_id INTEGER,
                destination_company_id INTEGER,
                status TEXT DEFAULT 'DRAFT',
                priority INTEGER DEFAULT 5,
                requested_by INTEGER,
                approved_by INTEGER,
                picked_by INTEGER,
                shipped_by INTEGER,
                received_by INTEGER,
                shipped_date TEXT,
                received_date TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (source_warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (destination_warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (source_company_id) REFERENCES wms_companies(id),
                FOREIGN KEY (destination_company_id) REFERENCES wms_companies(id),
                FOREIGN KEY (requested_by) REFERENCES users(id),
                FOREIGN KEY (approved_by) REFERENCES users(id),
                FOREIGN KEY (picked_by) REFERENCES users(id),
                FOREIGN KEY (shipped_by) REFERENCES users(id),
                FOREIGN KEY (received_by) REFERENCES users(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        # Transfer Lines
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_transfer_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transfer_id INTEGER NOT NULL,
                line_number INTEGER,
                item_id INTEGER NOT NULL,
                requested_quantity REAL,
                picked_quantity REAL DEFAULT 0,
                shipped_quantity REAL DEFAULT 0,
                received_quantity REAL DEFAULT 0,
                discrepancy_quantity REAL DEFAULT 0,
                lot_id INTEGER,
                source_location_id INTEGER,
                destination_location_id INTEGER,
                status TEXT DEFAULT 'PENDING',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (transfer_id) REFERENCES wms_transfers(id),
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (lot_id) REFERENCES wms_lots(id),
                FOREIGN KEY (source_location_id) REFERENCES wms_locations(id),
                FOREIGN KEY (destination_location_id) REFERENCES wms_locations(id)
            )
        ''')

        # Returns
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_number TEXT UNIQUE NOT NULL,
                return_type TEXT NOT NULL,
                warehouse_id INTEGER NOT NULL,
                company_id INTEGER,
                customer_id INTEGER,
                supplier_id INTEGER,
                original_order_number TEXT,
                rma_number TEXT,
                reason_code TEXT,
                status TEXT DEFAULT 'REQUESTED',
                authorization_status TEXT DEFAULT 'PENDING',
                inspected_by INTEGER,
                inspected_date TEXT,
                disposition TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (company_id) REFERENCES wms_companies(id),
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                FOREIGN KEY (inspected_by) REFERENCES users(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        # Return Lines
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_return_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                return_id INTEGER NOT NULL,
                line_number INTEGER,
                item_id INTEGER NOT NULL,
                original_order_line_id INTEGER,
                quantity_returned REAL,
                quantity_received REAL DEFAULT 0,
                quantity_accepted REAL DEFAULT 0,
                quantity_rejected REAL DEFAULT 0,
                quantity_damaged REAL DEFAULT 0,
                lot_id INTEGER,
                serial_number_id INTEGER,
                condition_grade TEXT,
                restock_decision TEXT,
                restock_location_id INTEGER,
                inspection_status TEXT DEFAULT 'PENDING',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (return_id) REFERENCES wms_returns(id),
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (original_order_line_id) REFERENCES wms_outbound_order_lines(id),
                FOREIGN KEY (lot_id) REFERENCES wms_lots(id),
                FOREIGN KEY (serial_number_id) REFERENCES wms_serial_numbers(id),
                FOREIGN KEY (restock_location_id) REFERENCES wms_locations(id)
            )
        ''')

        # Stock Counts
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_stock_counts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                count_number TEXT UNIQUE NOT NULL,
                count_type TEXT NOT NULL,
                warehouse_id INTEGER NOT NULL,
                company_id INTEGER,
                location_id INTEGER,
                category_id INTEGER,
                status TEXT DEFAULT 'DRAFT',
                count_method TEXT DEFAULT 'MANUAL',
                is_blind_count INTEGER DEFAULT 0,
                scheduled_date TEXT,
                started_date TEXT,
                completed_date TEXT,
                approved_by INTEGER,
                approved_date TEXT,
                total_lines INTEGER DEFAULT 0,
                counted_lines INTEGER DEFAULT 0,
                variance_lines INTEGER DEFAULT 0,
                freeze_stock INTEGER DEFAULT 0,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (company_id) REFERENCES wms_companies(id),
                FOREIGN KEY (location_id) REFERENCES wms_locations(id),
                FOREIGN KEY (category_id) REFERENCES wms_item_categories(id),
                FOREIGN KEY (approved_by) REFERENCES users(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        # Stock Count Lines
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_stock_count_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                count_id INTEGER NOT NULL,
                line_number INTEGER,
                item_id INTEGER NOT NULL,
                location_id INTEGER,
                lot_id INTEGER,
                serial_number_id INTEGER,
                system_quantity REAL,
                counted_quantity REAL,
                variance_quantity REAL,
                variance_value REAL,
                status TEXT DEFAULT 'PENDING',
                reason_code TEXT,
                investigation_notes TEXT,
                counted_by INTEGER,
                counted_at TEXT,
                verified_by INTEGER,
                verified_at TEXT,
                approved_by INTEGER,
                approved_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (count_id) REFERENCES wms_stock_counts(id),
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (location_id) REFERENCES wms_locations(id),
                FOREIGN KEY (lot_id) REFERENCES wms_lots(id),
                FOREIGN KEY (serial_number_id) REFERENCES wms_serial_numbers(id),
                FOREIGN KEY (counted_by) REFERENCES users(id),
                FOREIGN KEY (verified_by) REFERENCES users(id),
                FOREIGN KEY (approved_by) REFERENCES users(id)
            )
        ''')

        # Stock Adjustments
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_stock_adjustments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                adjustment_number TEXT UNIQUE NOT NULL,
                warehouse_id INTEGER NOT NULL,
                company_id INTEGER,
                adjustment_type TEXT NOT NULL,
                reason_code TEXT NOT NULL,
                status TEXT DEFAULT 'DRAFT',
                approved_by INTEGER,
                approved_date TEXT,
                applied_by INTEGER,
                applied_date TEXT,
                total_lines INTEGER DEFAULT 0,
                total_variance_value REAL DEFAULT 0,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (company_id) REFERENCES wms_companies(id),
                FOREIGN KEY (approved_by) REFERENCES users(id),
                FOREIGN KEY (applied_by) REFERENCES users(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        # Stock Adjustment Lines
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_stock_adjustment_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                adjustment_id INTEGER NOT NULL,
                line_number INTEGER,
                item_id INTEGER NOT NULL,
                location_id INTEGER,
                lot_id INTEGER,
                serial_number_id INTEGER,
                system_quantity REAL,
                counted_quantity REAL,
                adjusted_quantity REAL,
                unit_cost REAL,
                variance_value REAL,
                reason_code TEXT,
                notes TEXT,
                status TEXT DEFAULT 'PENDING',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (adjustment_id) REFERENCES wms_stock_adjustments(id),
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (location_id) REFERENCES wms_locations(id),
                FOREIGN KEY (lot_id) REFERENCES wms_lots(id),
                FOREIGN KEY (serial_number_id) REFERENCES wms_serial_numbers(id)
            )
        ''')

        # Wave Management
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_wave_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                template_name TEXT UNIQUE NOT NULL,
                description TEXT,
                picking_strategy TEXT DEFAULT 'WAVE',
                allocation_rule TEXT DEFAULT 'FIFO',
                max_picks_per_operator INTEGER DEFAULT 50,
                auto_assign_tasks INTEGER DEFAULT 1,
                release_type TEXT DEFAULT 'IMMEDIATE',
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_waves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wave_number TEXT UNIQUE NOT NULL,
                template_id INTEGER,
                warehouse_id INTEGER NOT NULL,
                company_id INTEGER,
                description TEXT,
                picking_strategy TEXT DEFAULT 'WAVE',
                allocation_rule TEXT DEFAULT 'FIFO',
                max_picks_per_operator INTEGER DEFAULT 50,
                auto_assign_tasks INTEGER DEFAULT 1,
                release_type TEXT DEFAULT 'IMMEDIATE',
                scheduled_release_time TEXT,
                status TEXT DEFAULT 'PLANNED',
                priority INTEGER DEFAULT 5,
                order_count INTEGER DEFAULT 0,
                total_lines INTEGER DEFAULT 0,
                total_picks INTEGER DEFAULT 0,
                picks_completed INTEGER DEFAULT 0,
                released_by INTEGER,
                released_at TEXT,
                completed_by INTEGER,
                completed_at TEXT,
                cancelled_by INTEGER,
                cancelled_at TEXT,
                cancel_reason TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (template_id) REFERENCES wms_wave_templates(id),
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (company_id) REFERENCES wms_companies(id),
                FOREIGN KEY (released_by) REFERENCES users(id),
                FOREIGN KEY (completed_by) REFERENCES users(id),
                FOREIGN KEY (cancelled_by) REFERENCES users(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_wave_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wave_id INTEGER NOT NULL,
                order_id INTEGER NOT NULL,
                added_by INTEGER,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (wave_id) REFERENCES wms_waves(id),
                FOREIGN KEY (order_id) REFERENCES wms_outbound_orders(id),
                FOREIGN KEY (added_by) REFERENCES users(id)
            )
        ''')

        # QC Inspections
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_qc_inspections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inspection_number TEXT UNIQUE NOT NULL,
                inspection_type TEXT NOT NULL,
                warehouse_id INTEGER NOT NULL,
                source_receipt_line_id INTEGER,
                source_return_line_id INTEGER,
                item_id INTEGER NOT NULL,
                lot_id INTEGER,
                location_id INTEGER,
                sample_size INTEGER,
                inspected_quantity REAL,
                passed_quantity REAL DEFAULT 0,
                failed_quantity REAL DEFAULT 0,
                result TEXT DEFAULT 'PENDING',
                defect_codes TEXT,
                notes TEXT,
                inspected_by INTEGER,
                inspection_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (source_receipt_line_id) REFERENCES wms_inbound_receipt_lines(id),
                FOREIGN KEY (source_return_line_id) REFERENCES wms_return_lines(id),
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (lot_id) REFERENCES wms_lots(id),
                FOREIGN KEY (location_id) REFERENCES wms_locations(id),
                FOREIGN KEY (inspected_by) REFERENCES users(id)
            )
        ''')

        # QC Usage Decisions
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_usage_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                decision_number TEXT UNIQUE NOT NULL,
                inspection_id INTEGER,
                item_id INTEGER NOT NULL,
                lot_id INTEGER,
                decision_code TEXT NOT NULL,
                decision_text TEXT,
                quantity REAL NOT NULL,
                disposition TEXT,
                notes TEXT,
                decided_by INTEGER,
                decided_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (inspection_id) REFERENCES wms_qc_inspections(id),
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (lot_id) REFERENCES wms_lots(id),
                FOREIGN KEY (decided_by) REFERENCES users(id)
            )
        ''')

        # QC Defect Codes
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_defect_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                description TEXT,
                severity TEXT DEFAULT 'MINOR',
                disposition TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # QC Certificates of Analysis
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_quality_certificates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                certificate_number TEXT UNIQUE NOT NULL,
                inspection_id INTEGER,
                lot_id INTEGER,
                item_id INTEGER NOT NULL,
                supplier_name TEXT,
                manufacture_date TEXT,
                expiry_date TEXT,
                parameters_json TEXT,
                result_summary TEXT,
                is_passed INTEGER DEFAULT 1,
                issued_by INTEGER,
                issued_at TEXT,
                pdf_path TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (inspection_id) REFERENCES wms_qc_inspections(id),
                FOREIGN KEY (lot_id) REFERENCES wms_lots(id),
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (issued_by) REFERENCES users(id)
            )
        ''')

        # QC AQL Sampling Rules
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_aql_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL,
                inspection_level TEXT DEFAULT 'II',
                aql_level REAL DEFAULT 1.5,
                lot_size_min INTEGER DEFAULT 1,
                lot_size_max INTEGER DEFAULT 50000,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # QC CAPA (Corrective/Preventive Action)
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_quality_capa (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capa_number TEXT UNIQUE NOT NULL,
                defect_id INTEGER,
                root_cause TEXT,
                corrective_action TEXT,
                preventive_action TEXT,
                responsible_id INTEGER,
                status TEXT DEFAULT 'OPEN',
                priority TEXT DEFAULT 'MEDIUM',
                due_date TEXT,
                completed_at TEXT,
                effectiveness_check TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (defect_id) REFERENCES wms_defect_codes(id),
                FOREIGN KEY (responsible_id) REFERENCES users(id)
            )
        ''')

        # Quality Holds - formal inventory quarantine
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_quality_holds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hold_number TEXT UNIQUE NOT NULL,
                warehouse_id INTEGER NOT NULL,
                item_id INTEGER NOT NULL,
                lot_id INTEGER,
                serial_number_id INTEGER,
                location_id INTEGER,
                quantity_held REAL DEFAULT 0,
                hold_reason TEXT NOT NULL,
                hold_type TEXT DEFAULT 'INSPECTION',
                source_receipt_line_id INTEGER,
                source_return_line_id INTEGER,
                source_inspection_id INTEGER,
                status TEXT DEFAULT 'ACTIVE',
                hold_notes TEXT,
                held_by INTEGER,
                held_at TEXT DEFAULT CURRENT_TIMESTAMP,
                released_by INTEGER,
                released_at TEXT,
                release_reason TEXT,
                expected_clear_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (lot_id) REFERENCES wms_lots(id),
                FOREIGN KEY (serial_number_id) REFERENCES wms_serial_numbers(id),
                FOREIGN KEY (location_id) REFERENCES wms_locations(id),
                FOREIGN KEY (source_receipt_line_id) REFERENCES wms_inbound_receipt_lines(id),
                FOREIGN KEY (source_return_line_id) REFERENCES wms_return_lines(id),
                FOREIGN KEY (source_inspection_id) REFERENCES wms_qc_inspections(id),
                FOREIGN KEY (held_by) REFERENCES users(id),
                FOREIGN KEY (released_by) REFERENCES users(id)
            )
        ''')

        # Saved Reports
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_saved_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_name TEXT NOT NULL,
                fields_json TEXT,
                filters_json TEXT,
                sort_json TEXT,
                created_by INTEGER,
                is_shared INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Warehouse Documents
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                document_number TEXT UNIQUE NOT NULL,
                document_type TEXT NOT NULL,
                warehouse_id INTEGER,
                related_entity_type TEXT,
                related_entity_id INTEGER,
                reference_number TEXT,
                issue_date TEXT,
                status TEXT DEFAULT 'DRAFT',
                prepared_by INTEGER,
                checked_by INTEGER,
                approved_by INTEGER,
                content_json TEXT,
                file_path TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (prepared_by) REFERENCES users(id),
                FOREIGN KEY (checked_by) REFERENCES users(id),
                FOREIGN KEY (approved_by) REFERENCES users(id)
            )
        ''')

        # RF Scan Log
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_rf_scan_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operator_id INTEGER,
                scan_type TEXT NOT NULL,
                barcode TEXT,
                item_id INTEGER,
                quantity REAL,
                location_id INTEGER,
                operation_status TEXT DEFAULT 'SUCCESS',
                error_message TEXT,
                response_time_ms INTEGER,
                scan_time TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (operator_id) REFERENCES users(id),
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (location_id) REFERENCES wms_locations(id)
            )
        ''')

        # Voice Picking Configuration
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_voice_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key TEXT UNIQUE NOT NULL,
                config_value TEXT,
                config_type TEXT DEFAULT 'string',
                language TEXT DEFAULT 'en',
                description TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Voice Pick Log
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_voice_pick_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                operator_id INTEGER,
                instruction_text TEXT,
                recognized_command TEXT,
                is_correct INTEGER DEFAULT 0,
                response_time_ms INTEGER,
                error_type TEXT,
                retry_count INTEGER DEFAULT 0,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES wms_pick_tasks(id),
                FOREIGN KEY (operator_id) REFERENCES users(id)
            )
        ''')

        # Yard Vehicles
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_yard_vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                plate_number TEXT NOT NULL,
                driver_name TEXT,
                driver_phone TEXT,
                carrier_name TEXT,
                vehicle_type TEXT DEFAULT 'INBOUND',
                warehouse_id INTEGER NOT NULL,
                dock_id INTEGER,
                status TEXT DEFAULT 'WAITING',
                arrival_time TEXT,
                departure_time TEXT,
                expected_duration_minutes INTEGER DEFAULT 60,
                is_active INTEGER DEFAULT 1,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (dock_id) REFERENCES wms_dock_doors(id)
            )
        ''')

        # Dock Doors
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_dock_doors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                door_number TEXT NOT NULL,
                warehouse_id INTEGER NOT NULL,
                door_type TEXT DEFAULT 'BOTH',
                status TEXT DEFAULT 'AVAILABLE',
                current_vehicle_id INTEGER,
                height_limit_cm INTEGER,
                width_limit_cm INTEGER,
                weight_limit_kg INTEGER,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (current_vehicle_id) REFERENCES wms_yard_vehicles(id)
            )
        ''')

        # Dock Schedule
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_dock_schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scheduled_date TEXT NOT NULL,
                scheduled_time TEXT,
                warehouse_id INTEGER NOT NULL,
                dock_id INTEGER,
                vehicle_type TEXT,
                carrier_name TEXT,
                plate_number TEXT,
                driver_name TEXT,
                driver_phone TEXT,
                reference_number TEXT,
                estimated_duration_minutes INTEGER,
                status TEXT DEFAULT 'SCHEDULED',
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (dock_id) REFERENCES wms_dock_doors(id)
            )
        ''')

        # Yard Activity Log
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_yard_activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER,
                event TEXT NOT NULL,
                plate_number TEXT,
                driver_name TEXT,
                dock_number TEXT,
                user_id INTEGER,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vehicle_id) REFERENCES wms_yard_vehicles(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # WMS Tasks / Work Queue
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_work_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_number TEXT UNIQUE NOT NULL,
                task_type TEXT NOT NULL,
                warehouse_id INTEGER NOT NULL,
                location_id INTEGER,
                priority INTEGER DEFAULT 5,
                status TEXT DEFAULT 'PENDING',
                assigned_to INTEGER,
                estimated_minutes INTEGER,
                actual_minutes INTEGER,
                started_at TEXT,
                completed_at TEXT,
                completed_by INTEGER,
                reference_type TEXT,
                reference_number TEXT,
                notes TEXT,
                exceptions TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (location_id) REFERENCES wms_locations(id),
                FOREIGN KEY (assigned_to) REFERENCES users(id),
                FOREIGN KEY (completed_by) REFERENCES users(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        # Alerts
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                alert_code TEXT,
                warehouse_id INTEGER,
                item_id INTEGER,
                location_id INTEGER,
                severity TEXT DEFAULT 'MEDIUM',
                title TEXT NOT NULL,
                message TEXT,
                is_active INTEGER DEFAULT 1,
                is_acknowledged INTEGER DEFAULT 0,
                acknowledged_by INTEGER,
                acknowledged_at TEXT,
                resolved_at TEXT,
                resolved_by INTEGER,
                action_url TEXT,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (location_id) REFERENCES wms_locations(id),
                FOREIGN KEY (acknowledged_by) REFERENCES users(id),
                FOREIGN KEY (resolved_by) REFERENCES users(id)
            )
        ''')

        # EDI Partners
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_edi_partners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_name TEXT NOT NULL,
                partner_type TEXT NOT NULL,
                edi_protocol TEXT DEFAULT 'AS2',
                endpoint_url TEXT,
                username TEXT,
                password_encrypted TEXT,
                certificate_blob TEXT,
                is_active INTEGER DEFAULT 1,
                is_test_mode INTEGER DEFAULT 1,
                partner_code TEXT UNIQUE,
                contact_email TEXT,
                contact_phone TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # EDI Outbound IDocs
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_outbound_idocs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idoc_number TEXT UNIQUE NOT NULL,
                message_type TEXT NOT NULL,
                partner_id INTEGER NOT NULL,
                status TEXT DEFAULT 'PENDING',
                content_xml TEXT,
                content_json TEXT,
                sent_at TEXT,
                acknowledged_at TEXT,
                error_message TEXT,
                retry_count INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (partner_id) REFERENCES wms_edi_partners(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        # EDI Inbound IDocs
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_inbound_idocs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idoc_number TEXT UNIQUE NOT NULL,
                message_type TEXT NOT NULL,
                partner_id INTEGER NOT NULL,
                status TEXT DEFAULT 'RECEIVED',
                content_xml TEXT,
                content_json TEXT,
                processed_at TEXT,
                error_message TEXT,
                reference_number TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partner_id) REFERENCES wms_edi_partners(id)
            )
        ''')

        # EDI Mapping Rules
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_edi_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mapping_name TEXT NOT NULL,
                message_type TEXT NOT NULL,
                direction TEXT NOT NULL,
                field_mappings_json TEXT,
                transformation_rules_json TEXT,
                validation_rules_json TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        # EDI Audit Log
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_edi_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                idoc_id INTEGER,
                action_type TEXT NOT NULL,
                old_status TEXT,
                new_status TEXT,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                created_by INTEGER,
                FOREIGN KEY (idoc_id) REFERENCES wms_outbound_idocs(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        # Notifications
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                message TEXT,
                notification_type TEXT DEFAULT 'info',
                related_entity_type TEXT,
                related_entity_id INTEGER,
                is_read INTEGER DEFAULT 0,
                read_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Audit Log
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id INTEGER,
                details TEXT,
                user_id INTEGER,
                ip_address TEXT,
                user_agent TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # User Permissions
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_user_permissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                permission_key TEXT NOT NULL,
                granted_by INTEGER,
                granted_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (granted_by) REFERENCES users(id),
                UNIQUE(user_id, permission_key)
            )
        ''')

        # User Companies
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_user_companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                company_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (company_id) REFERENCES wms_companies(id),
                UNIQUE(user_id, company_id)
            )
        ''')

        # User Warehouses
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_user_warehouses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                warehouse_id INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                UNIQUE(user_id, warehouse_id)
            )
        ''')

        # Code Sequences
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_code_sequences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code_type TEXT NOT NULL,
                year INTEGER NOT NULL,
                company_id INTEGER,
                last_seq INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (company_id) REFERENCES wms_companies(id),
                UNIQUE(code_type, year, company_id)
            )
        ''')

        # Stock Status History
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_stock_status_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER NOT NULL,
                lot_id INTEGER,
                serial_number_id INTEGER,
                warehouse_id INTEGER NOT NULL,
                location_id INTEGER,
                old_status TEXT,
                new_status TEXT NOT NULL,
                reason_code TEXT,
                reference_type TEXT,
                reference_number TEXT,
                changed_by INTEGER,
                changed_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES wms_items(id),
                FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id),
                FOREIGN KEY (changed_by) REFERENCES users(id)
            )
        ''')

        # Location Types
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_location_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                name_local TEXT,
                description TEXT,
                is_picking INTEGER DEFAULT 1,
                is_putaway INTEGER DEFAULT 1,
                is_storage INTEGER DEFAULT 1,
                is_staging INTEGER DEFAULT 0,
                is_receiving INTEGER DEFAULT 0,
                is_dispatch INTEGER DEFAULT 0,
                is_quarantine INTEGER DEFAULT 0,
                is_damaged INTEGER DEFAULT 0,
                is_return INTEGER DEFAULT 0,
                is_inspection INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Reason Codes
        db.execute('''
            CREATE TABLE IF NOT EXISTS wms_reason_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                description TEXT NOT NULL,
                reason_type TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                requires_approval INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Seed default location types
        default_location_types = [
            ('STORAGE', 'Storage Bin', None, 'Standard storage location', 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0),
            ('PICKING', 'Picking Face', None, 'Primary picking location', 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
            ('BULK', 'Bulk Storage', None, 'Bulk pallet storage', 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0),
            ('STAGING', 'Staging Area', None, 'Outbound staging', 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0),
            ('RECEIVING', 'Receiving Dock', None, 'Inbound receiving', 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0),
            ('INSPECT', 'Inspection Area', None, 'Quality inspection', 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0),
            ('QUARANTINE', 'Quarantine Area', None, 'Quarantine/Hold', 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0),
            ('DAMAGED', 'Damaged Goods', None, 'Damaged item storage', 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0),
            ('RETURN', 'Returns Area', None, 'Returns processing', 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0),
            ('DISPATCH', 'Dispatch Dock', None, 'Outbound dispatch', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1),
        ]
        for lt in default_location_types:
            db.execute('''
                INSERT OR IGNORE INTO wms_location_types
                (code, name, name_local, description, is_picking, is_putaway, is_storage, is_staging,
                 is_receiving, is_dispatch, is_quarantine, is_damaged, is_return, is_inspection, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', lt)

        # Seed default reason codes
        default_reason_codes = [
            ('COUNT_VAR', 'Cycle Count Variance', 'count', 1, 0),
            ('DAMAGE', 'Damaged Goods', 'adjustment', 1, 1),
            ('EXPIRED', 'Expired Items', 'adjustment', 1, 1),
            ('SHRINKAGE', 'Shrinkage/Theft', 'adjustment', 1, 1),
            ('FOUND', 'Found Items', 'adjustment', 0, 0),
            ('SAMPLE', 'Sample/Demo Use', 'adjustment', 0, 0),
            ('REWORK', 'Rework/Repair', 'adjustment', 1, 1),
            ('SCRAP', 'Scrapped Items', 'adjustment', 1, 1),
            ('RECV_DISC', 'Receiving Discrepancy', 'receiving', 1, 1),
            ('SHIP_DISC', 'Shipping Discrepancy', 'shipping', 1, 1),
            ('XFER_DISC', 'Transfer Discrepancy', 'transfer', 1, 1),
            ('RTN_DAMAGE', 'Return Damage', 'return', 1, 1),
            ('RTN_DEFECT', 'Return Defect', 'return', 1, 1),
            ('CORRECTION', 'Data Correction', 'adjustment', 1, 1),
            ('RECEIVED', 'Received Stock', 'receiving', 0, 0),
            ('PRODUCED', 'Produced/Manufactured', 'production', 0, 0),
            ('ISSUE', 'Issue/Consumption', 'issue', 0, 0),
            ('TRANSFER', 'Transfer', 'transfer', 0, 0),
        ]
        for rc in default_reason_codes:
            db.execute('''
                INSERT OR IGNORE INTO wms_reason_codes (code, description, reason_type, is_active, requires_approval)
                VALUES (?, ?, ?, ?, ?)
            ''', rc)

        # Seed default WMS settings
        default_settings = [
            ('default_rotation_policy', 'FIFO', 'string', 'inventory', 'Default inventory rotation policy'),
            ('default_warehouse', '', 'string', 'general', 'Default warehouse for operations'),
            ('allow_negative_stock', '0', 'boolean', 'inventory', 'Allow negative stock levels'),
            ('auto_create_lot', '1', 'boolean', 'inventory', 'Auto-create lot on receipt'),
            ('require_inspection', '0', 'boolean', 'quality', 'Require QC inspection on receipt'),
            ('count_variance_tolerance', '0.01', 'number', 'count', 'Allowed variance % for counts'),
            ('low_stock_alert_threshold', '10', 'number', 'alerts', 'Low stock alert percentage'),
            ('near_expiry_days', '30', 'number', 'alerts', 'Days before expiry to trigger alert'),
            ('auto_allocate_pick', '1', 'boolean', 'picking', 'Auto-allocate stock on pick creation'),
            ('default_pick_strategy', 'FIFO', 'string', 'picking', 'Default picking strategy'),
            ('require_lot_on_receipt', '0', 'boolean', 'receiving', 'Require lot number on receipt'),
            ('require_serial_on_receipt', '0', 'boolean', 'receiving', 'Require serial number on receipt'),
            ('transfer_requires_approval', '1', 'boolean', 'transfer', 'Require approval for transfers'),
            ('adjustment_requires_approval', '1', 'boolean', 'adjustment', 'Require approval for adjustments'),
            ('return_requires_approval', '1', 'boolean', 'return', 'Require approval for returns'),
            ('enable_barcode_scan', '0', 'boolean', 'general', 'Enable barcode scanning mode'),
            ('enable_xyz_classification', '1', 'boolean', 'general', 'Enable XYZ velocity classification'),
            ('dead_stock_days', '90', 'number', 'alerts', 'Days of no movement to mark dead stock'),
            ('slow_moving_days', '30', 'number', 'alerts', 'Days of no movement to mark slow moving'),
            ('decimal_precision', '2', 'number', 'general', 'Decimal precision for quantities'),
            ('date_format', 'DD/MM/YYYY', 'string', 'general', 'Date format for displays'),
            ('time_format', '24h', 'string', 'general', 'Time format (24h or 12h)'),
        ]
        for s in default_settings:
            db.execute('''
                INSERT OR IGNORE INTO wms_settings (setting_key, setting_value, setting_type, category, description)
                VALUES (?, ?, ?, ?, ?)
            ''', s)

        # Seed default item categories
        default_categories = [
            (None, 'RAW_MAT', 'Raw Materials', 0, '0'),
            (None, 'COMP', 'Components', 0, '1'),
            (None, 'WIP', 'Work in Progress', 0, '2'),
            (None, 'FIN_GOODS', 'Finished Goods', 0, '3'),
            (None, 'SPARE', 'Spare Parts', 0, '4'),
            (None, 'CONSUM', 'Consumables', 0, '5'),
            (None, 'PACK', 'Packaging Materials', 0, '6'),
            (None, 'HAZMAT', 'Hazardous Materials', 0, '7'),
        ]
        for cat in default_categories:
            db.execute('''
                INSERT OR IGNORE INTO wms_item_categories (parent_id, code, name, level, sort_order)
                VALUES (?, ?, ?, ?, ?)
            ''', cat)

        db.commit()

        _wms_schema_initialized = True

    # ============================================================
    # WMS DASHBOARD
    # ============================================================

    init_wms_tables()

    @app.route('/wms')
    @app.route('/wms/dashboard')
    @wms_permission_required('dashboard', 'view')
    def wms_dashboard():
        """Main WMS Dashboard."""
        db = get_db()
        user_id = session.get('user_id')
        wh_filter = get_warehouse_filter(user_id)
        company_filter = get_company_filter(user_id)

        # Total active SKUs
        total_skus = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_items WHERE is_active = 1
        ''').fetchone()['cnt']

        # Stock totals by status
        stock_by_status = db.execute(f'''
            SELECT status, SUM(quantity) as total_qty, COUNT(*) as locations
            FROM wms_inventory_balances
            WHERE 1=1 {wh_filter.replace('warehouse_id', 'warehouse_id')}
            GROUP BY status
        ''').fetchall()

        # Available stock
        available_stock = db.execute(f'''
            SELECT COALESCE(SUM(quantity), 0) as qty FROM wms_inventory_balances
            WHERE status = 'AVAILABLE' {wh_filter}
        ''').fetchone()['qty']

        # Reserved stock
        reserved_stock = db.execute(f'''
            SELECT COALESCE(SUM(reserved_quantity), 0) as qty FROM wms_inventory_balances
            WHERE 1=1 {wh_filter}
        ''').fetchone()['qty']

        # Blocked stock
        blocked_stock = db.execute(f'''
            SELECT COALESCE(SUM(blocked_quantity), 0) as qty FROM wms_inventory_balances
            WHERE status IN ('BLOCKED', 'QUARANTINE', 'DAMAGED') {wh_filter}
        ''').fetchone()['qty']

        # Near expiry stock
        try:
            near_expiry_days = int(db.execute("SELECT setting_value FROM wms_settings WHERE setting_key = 'near_expiry_days'").fetchone()['setting_value'] or 30)
        except (ValueError, TypeError):
            near_expiry_days = 30
        near_expiry = db.execute('''
            SELECT COALESCE(SUM(l.quantity), 0) as qty FROM wms_lots l
            WHERE l.expiry_date IS NOT NULL
            AND l.expiry_date <= date('now', '+' || ? || ' days')
            AND l.expiry_date > date('now')
            AND l.quantity > 0
        ''', (str(near_expiry_days),)).fetchone()['qty']

        # Expired stock
        expired_stock_qry = '''
            SELECT COALESCE(SUM(l.quantity), 0) as qty FROM wms_lots l
            WHERE l.expiry_date IS NOT NULL
            AND l.expiry_date < date('now')
            AND l.quantity > 0
        '''
        if wh_filter:
            expired_stock_qry += ' AND ' + wh_filter.replace('warehouse_id', 'l.warehouse_id')
        expired_stock = db.execute(expired_stock_qry).fetchone()['qty']

        # Empty locations
        if wh_filter:
            empty_locations = db.execute(f'''
                SELECT COUNT(*) as cnt FROM wms_locations
                WHERE is_empty = 1 AND is_active = 1 {wh_filter}
            ''').fetchone()['cnt']
        else:
            empty_locations = db.execute('''
                SELECT COUNT(*) as cnt FROM wms_locations
                WHERE is_empty = 1 AND is_active = 1
            ''').fetchone()['cnt']

        # Total locations
        if wh_filter:
            total_locations = db.execute(f'''
                SELECT COUNT(*) as cnt FROM wms_locations
            WHERE is_active = 1 {wh_filter}
        ''').fetchone()['cnt']

        # Active alerts
        active_alerts = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_alerts
            WHERE is_active = 1 AND is_acknowledged = 0
            {wh_filter.replace('warehouse_id', 'warehouse_id')}
        ''').fetchone()['cnt']

        # Pending tasks by type
        pending_receiving = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_inbound_receipts
            WHERE status IN ('EXPECTED', 'ARRIVED', 'PARTIAL') {wh_filter.replace('warehouse_id', 'warehouse_id')}
        ''').fetchone()['cnt']

        pending_putaway = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_putaway_tasks
            WHERE status = 'PENDING' {wh_filter.replace('warehouse_id', 'wms_putaway_tasks.warehouse_id')}
        ''').fetchone()['cnt']

        pending_picking = db.execute(f'''
            SELECT COUNT(*) as cnt
            FROM wms_pick_tasks p
            JOIN wms_locations l ON l.id = p.source_location_id
            WHERE p.status IN ('PENDING', 'IN_PROGRESS') {wh_filter.replace('warehouse_id', 'l.warehouse_id')}
        ''').fetchone()['cnt']

        pending_packing = db.execute(f'''
            SELECT COUNT(*) as cnt
            FROM wms_pack_tasks p
            JOIN wms_outbound_orders o ON o.id = p.order_id
            WHERE p.status = 'PENDING' {wh_filter.replace('warehouse_id', 'o.warehouse_id')}
        ''').fetchone()['cnt']

        pending_transfers = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_transfers
            WHERE status IN ('REQUESTED', 'APPROVED', 'PICKING', 'DISPATCHED') {wh_filter.replace('source_warehouse_id', 'source_warehouse_id')}
        ''').fetchone()['cnt']

        pending_returns = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_returns
            WHERE status IN ('REQUESTED', 'AUTHORIZED', 'RECEIVED') {wh_filter.replace('warehouse_id', 'warehouse_id')}
        ''').fetchone()['cnt']

        pending_counts = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_stock_counts
            WHERE status IN ('DRAFT', 'IN_PROGRESS') {wh_filter.replace('warehouse_id', 'warehouse_id')}
        ''').fetchone()['cnt']

        pending_replenishment = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_replenishment_tasks
            WHERE status = 'PENDING' {wh_filter.replace('warehouse_id', 'wms_replenishment_tasks.warehouse_id')}
        ''').fetchone()['cnt']

        # Zero stock items
        zero_stock = db.execute(f'''
            SELECT COUNT(DISTINCT item_id) as cnt FROM wms_inventory_balances
            WHERE quantity <= 0 {wh_filter}
        ''').fetchone()['cnt']

        # Negative stock count
        negative_stock = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_inventory_balances
            WHERE quantity < 0 {wh_filter}
        ''').fetchone()['cnt']

        # Count discrepancies
        count_discrepancies = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_stock_count_lines
            WHERE variance_quantity != 0 AND status = 'APPROVED'
        ''').fetchone()['cnt']

        # Space utilization
        warehouse_stats = db.execute(f'''
            SELECT
                w.id, w.name,
                COUNT(DISTINCT l.id) as total_locations,
                SUM(CASE WHEN l.is_empty = 1 THEN 1 ELSE 0 END) as empty_locations,
                COALESCE(SUM(l.current_volume_m3), 0) as used_volume,
                COALESCE(SUM(l.capacity_volume_m3), 0) as total_capacity
            FROM wms_warehouses w
            LEFT JOIN wms_locations l ON l.warehouse_id = w.id
            WHERE w.is_active = 1 {wh_filter}
            GROUP BY w.id
        ''').fetchall()

        # Recent movements
        recent_movements = db.execute(f'''
            SELECT
                l.id, l.transaction_type, l.transaction_number,
                l.quantity_moved, l.created_at,
                i.item_code, i.name as item_name,
                w.name as warehouse_name,
                u.username
            FROM wms_inventory_ledger l
            JOIN wms_items i ON i.id = l.item_id
            JOIN wms_warehouses w ON w.id = l.warehouse_id
            LEFT JOIN users u ON u.id = l.user_id
            WHERE 1=1 {wh_filter}
            ORDER BY l.created_at DESC LIMIT 10
        ''').fetchall()

        # Top alerts
        top_alerts = db.execute(f'''
            SELECT * FROM wms_alerts
            WHERE is_active = 1
            ORDER BY
                CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END,
                created_at DESC
            LIMIT 10
        ''').fetchall()

        # Warehouses summary
        warehouses = db.execute(f'''
            SELECT w.*,
                COALESCE(SUM(b.quantity), 0) as total_stock,
                COUNT(DISTINCT l.id) as location_count
            FROM wms_warehouses w
            LEFT JOIN wms_inventory_balances b ON b.warehouse_id = w.id
            LEFT JOIN wms_locations l ON l.warehouse_id = w.id
            WHERE w.is_active = 1 {wh_filter}
            GROUP BY w.id
        ''').fetchall()

        title = 'WMS Dashboard'
        return render_template('wms/dashboard.html',
            title=title,
            total_skus=total_skus,
            available_stock=available_stock,
            reserved_stock=reserved_stock,
            blocked_stock=blocked_stock,
            near_expiry=near_expiry,
            expired_stock=expired_stock,
            empty_locations=empty_locations,
            total_locations=total_locations,
            active_alerts=active_alerts,
            pending_receiving=pending_receiving,
            pending_putaway=pending_putaway,
            pending_picking=pending_picking,
            pending_packing=pending_packing,
            pending_transfers=pending_transfers,
            pending_returns=pending_returns,
            pending_counts=pending_counts,
            pending_replenishment=pending_replenishment,
            zero_stock=zero_stock,
            negative_stock=negative_stock,
            count_discrepancies=count_discrepancies,
            warehouse_stats=warehouse_stats,
            recent_movements=recent_movements,
            top_alerts=top_alerts,
            warehouses=warehouses,
            stock_by_status=stock_by_status
        )

    # ============================================================
    # ITEM MASTER
    # ============================================================

    @app.route('/wms/items')
    @wms_permission_required('items', 'view')
    def wms_items():
        """Item master list."""
        db = get_db()
        search = request.args.get('search', '').strip()
        category = request.args.get('category', '')
        brand = request.args.get('brand', '')
        status = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        per_page = 50

        query = '''
            SELECT i.*, b.name as brand_name, c.name as category_name
            FROM wms_items i
            LEFT JOIN wms_item_brands b ON b.id = i.brand_id
            LEFT JOIN wms_item_categories c ON c.id = i.category_id
            WHERE 1=1
        '''
        params = []

        if search:
            query += " AND (i.item_code LIKE ? OR i.name LIKE ? OR i.sku LIKE ? OR i.barcode LIKE ? OR i.part_number LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param, search_param, search_param])

        if category:
            query += " AND i.category_id = ?"
            params.append(category)

        if brand:
            query += " AND i.brand_id = ?"
            params.append(brand)

        if status:
            query += " AND i.selling_status = ?"
            params.append(status)

        total = db.execute(query, params).fetchall()
        total_count = len(total)

        query += " ORDER BY i.name LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        items = db.execute(query, params).fetchall()

        categories = db.execute('SELECT * FROM wms_item_categories WHERE is_active = 1 ORDER BY name').fetchall()
        brands = db.execute('SELECT * FROM wms_item_brands WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'Item Master'
        return render_template('wms/items.html',
            title=title,
            items=items,
            categories=categories,
            brands=brands,
            search=search,
            category=category,
            brand=brand,
            status=status,
            page=page,
            per_page=per_page,
            total_count=total_count,
            total_pages=(total_count + per_page - 1) // per_page
        )

    @app.route('/wms/items/new', methods=['GET', 'POST'])
    @wms_permission_required('items', 'create')
    def wms_items_new():
        """Create new item."""
        db = get_db()

        if request.method == 'POST':
            data = request.form
            validation_errors = validate_item_payload(data)
            if validation_errors:
                for error in validation_errors:
                    flash(error, 'error')
                categories = db.execute('SELECT * FROM wms_item_categories WHERE is_active = 1 ORDER BY name').fetchall()
                brands = db.execute('SELECT * FROM wms_item_brands WHERE is_active = 1 ORDER BY name').fetchall()
                groups = db.execute('SELECT * FROM wms_item_groups WHERE is_active = 1 ORDER BY name').fetchall()
                warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
                return render_template('wms/item_form.html', title='New Item', item=data,
                    categories=categories, brands=brands, groups=groups, warehouses=warehouses,
                    form_action=url_for('wms_items_new'))
            try:
                db.execute('''
                    INSERT INTO wms_items (
                        item_code, sku, barcode, qr_code, part_number, oem_number,
                        alternate_part_numbers, supplier_code, name, name_local,
                        short_name, long_description, brand_id, category_id, group_id,
                        item_type, unit_of_measure, secondary_uom, conversion_rate,
                        weight_kg, volume_m3, length_cm, width_cm, height_cm,
                        color, size, material, country_of_origin, hazard_class,
                        temperature_requirement, shelf_life_days, expiry_tracking,
                        batch_tracking, lot_tracking, serial_tracking,
                        quality_inspection_required, min_stock_level, max_stock_level,
                        reorder_point, reorder_quantity, safety_stock,
                        economic_order_quantity, preferred_warehouse_id,
                        preferred_location_id, rotation_policy, picking_strategy,
                        packing_instruction, handling_instruction, selling_status,
                        procurement_status, abc_class, is_kit, is_bundle,
                        kit_components, is_active, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('item_code'), data.get('sku'), data.get('barcode'),
                    data.get('qr_code'), data.get('part_number'), data.get('oem_number'),
                    data.get('alternate_part_numbers'), data.get('supplier_code'),
                    data.get('name'), data.get('name_local'),
                    data.get('short_name'), data.get('long_description'),
                    data.get('brand_id') or None, data.get('category_id') or None,
                    data.get('group_id') or None, data.get('item_type', 'finished_goods'),
                    data.get('unit_of_measure', 'PCS'), data.get('secondary_uom'),
                    data.get('conversion_rate', 1.0), data.get('weight_kg'),
                    data.get('volume_m3'), data.get('length_cm'),
                    data.get('width_cm'), data.get('height_cm'),
                    data.get('color'), data.get('size'), data.get('material'),
                    data.get('country_of_origin'), data.get('hazard_class'),
                    data.get('temperature_requirement'), data.get('shelf_life_days'),
                    1 if data.get('expiry_tracking') else 0,
                    1 if data.get('batch_tracking') else 0,
                    1 if data.get('lot_tracking') else 0,
                    1 if data.get('serial_tracking') else 0,
                    1 if data.get('quality_inspection_required') else 0,
                    data.get('min_stock_level', 0), data.get('max_stock_level'),
                    data.get('reorder_point', 0), data.get('reorder_quantity'),
                    data.get('safety_stock'), data.get('economic_order_quantity'),
                    data.get('preferred_warehouse_id') or None,
                    data.get('preferred_location_id') or None,
                    data.get('rotation_policy', 'FIFO'),
                    data.get('picking_strategy'), data.get('packing_instruction'),
                    data.get('handling_instruction'),
                    data.get('selling_status', 'active'),
                    data.get('procurement_status', 'active'),
                    data.get('abc_class'), 1 if data.get('is_kit') else 0,
                    1 if data.get('is_bundle') else 0,
                    data.get('kit_components'),
                    1 if data.get('is_active') else 0,
                    session.get('user_id')
                ))
                db.commit()
                item_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
                log_wms_audit('CREATE', 'ITEM', item_id, {'item_code': data.get('item_code')})
                flash('Item created successfully!', 'success')
                return redirect(url_for('wms_item_detail', item_id=item_id))
            except Exception as e:
                import traceback
                print(f"WMS item create error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error creating item. Please try again.', 'error')

        categories = db.execute('SELECT * FROM wms_item_categories WHERE is_active = 1 ORDER BY name').fetchall()
        brands = db.execute('SELECT * FROM wms_item_brands WHERE is_active = 1 ORDER BY name').fetchall()
        groups = db.execute('SELECT * FROM wms_item_groups WHERE is_active = 1 ORDER BY name').fetchall()
        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'New Item'
        return render_template('wms/item_form.html',
            title=title,
            item=None,
            categories=categories,
            brands=brands,
            groups=groups,
            warehouses=warehouses,
            form_action=url_for('wms_items_new')
        )

    @app.route('/wms/items/<int:item_id>')
    @wms_permission_required('items', 'view')
    def wms_item_detail(item_id):
        """Item detail view with tabs."""
        db = get_db()
        item = db.execute('''
            SELECT i.*, b.name as brand_name, c.name as category_name,
                   g.name as group_name,
                   w.name as preferred_warehouse_name,
                   l.code as preferred_location_code
            FROM wms_items i
            LEFT JOIN wms_item_brands b ON b.id = i.brand_id
            LEFT JOIN wms_item_categories c ON c.id = i.category_id
            LEFT JOIN wms_item_groups g ON g.id = i.group_id
            LEFT JOIN wms_warehouses w ON w.id = i.preferred_warehouse_id
            LEFT JOIN wms_locations l ON l.id = i.preferred_location_id
            WHERE i.id = ?
        ''', (item_id,)).fetchone()

        if not item:
            flash('Item not found.', 'error')
            return redirect(url_for('wms_items'))

        tab = request.args.get('tab', 'overview')

        # Stock by warehouse
        stock_by_wh = db.execute('''
            SELECT w.name as warehouse_name,
                   SUM(b.quantity) as quantity,
                   SUM(b.reserved_quantity) as reserved,
                   SUM(b.allocated_quantity) as allocated
            FROM wms_inventory_balances b
            JOIN wms_warehouses w ON w.id = b.warehouse_id
            WHERE b.item_id = ?
            GROUP BY b.warehouse_id
        ''', (item_id,)).fetchall()

        # Stock by lot
        lots = db.execute('''
            SELECT l.*, w.name as warehouse_name, loc.code as location_code
            FROM wms_lots l
            JOIN wms_warehouses w ON w.id = l.warehouse_id
            LEFT JOIN wms_locations loc ON loc.id = l.location_id
            WHERE l.item_id = ? AND l.quantity > 0
            ORDER BY l.expiry_date ASC
        ''', (item_id,)).fetchall()

        # Movement history
        movements = db.execute('''
            SELECT l.*, u.username, w.name as warehouse_name
            FROM wms_inventory_ledger l
            LEFT JOIN users u ON u.id = l.user_id
            JOIN wms_warehouses w ON w.id = l.warehouse_id
            WHERE l.item_id = ?
            ORDER BY l.created_at DESC LIMIT 100
        ''', (item_id,)).fetchall()

        # Related items
        related = db.execute('''
            SELECT ir.*, i.item_code, i.name as item_name
            FROM wms_item_relations ir
            JOIN wms_items i ON i.id = ir.related_item_id
            WHERE ir.item_id = ?
        ''', (item_id,)).fetchall()

        # Suppliers
        suppliers = db.execute('''
            SELECT s.*, i.unit_cost, i.supplier_code as item_supplier_code
            FROM wms_item_suppliers i
            JOIN suppliers s ON s.id = i.supplier_id
            WHERE i.item_id = ?
        ''', (item_id,)).fetchall()

        # Alerts for this item
        alerts = db.execute('''
            SELECT * FROM wms_alerts
            WHERE item_id = ? AND is_active = 1
            ORDER BY created_at DESC LIMIT 20
        ''', (item_id,)).fetchall()

        title = f'Item: {item["name"]}'
        return render_template('wms/item_detail.html',
            title=title,
            item=item,
            tab=tab,
            stock_by_wh=stock_by_wh,
            lots=lots,
            movements=movements,
            related=related,
            suppliers=suppliers,
            alerts=alerts
        )

    @app.route('/wms/items/<int:item_id>/edit', methods=['GET', 'POST'])
    @wms_permission_required('items', 'edit')
    def wms_items_edit(item_id):
        """Edit item."""
        db = get_db()
        item = db.execute('SELECT * FROM wms_items WHERE id = ?', (item_id,)).fetchone()
        if not item:
            flash('Item not found.', 'error')
            return redirect(url_for('wms_items'))

        if request.method == 'POST':
            data = request.form
            validation_errors = validate_item_payload(data, item_id=item_id)
            if validation_errors:
                for error in validation_errors:
                    flash(error, 'error')
                categories = db.execute('SELECT * FROM wms_item_categories WHERE is_active = 1 ORDER BY name').fetchall()
                brands = db.execute('SELECT * FROM wms_item_brands WHERE is_active = 1 ORDER BY name').fetchall()
                groups = db.execute('SELECT * FROM wms_item_groups WHERE is_active = 1 ORDER BY name').fetchall()
                warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
                return render_template('wms/item_form.html',
                    title=f'Edit Item: {item["name"]}',
                    item=data,
                    categories=categories,
                    brands=brands,
                    groups=groups,
                    warehouses=warehouses,
                    form_action=url_for('wms_items_edit', item_id=item_id))
            try:
                db.execute('''
                    UPDATE wms_items SET
                        item_code = ?, sku = ?, barcode = ?, qr_code = ?,
                        part_number = ?, oem_number = ?, alternate_part_numbers = ?,
                        supplier_code = ?, name = ?, name_local = ?, short_name = ?,
                        long_description = ?, brand_id = ?, category_id = ?, group_id = ?,
                        item_type = ?, unit_of_measure = ?, secondary_uom = ?,
                        conversion_rate = ?, weight_kg = ?, volume_m3 = ?,
                        length_cm = ?, width_cm = ?, height_cm = ?, color = ?,
                        size = ?, material = ?, country_of_origin = ?,
                        hazard_class = ?, temperature_requirement = ?,
                        shelf_life_days = ?, expiry_tracking = ?, batch_tracking = ?,
                        lot_tracking = ?, serial_tracking = ?,
                        quality_inspection_required = ?, min_stock_level = ?,
                        max_stock_level = ?, reorder_point = ?, reorder_quantity = ?,
                        safety_stock = ?, economic_order_quantity = ?,
                        preferred_warehouse_id = ?, preferred_location_id = ?,
                        rotation_policy = ?, picking_strategy = ?,
                        packing_instruction = ?, handling_instruction = ?,
                        selling_status = ?, procurement_status = ?, abc_class = ?,
                        is_kit = ?, is_bundle = ?, kit_components = ?,
                        is_active = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    data.get('item_code'), data.get('sku'), data.get('barcode'),
                    data.get('qr_code'), data.get('part_number'), data.get('oem_number'),
                    data.get('alternate_part_numbers'), data.get('supplier_code'),
                    data.get('name'), data.get('name_local'),
                    data.get('short_name'), data.get('long_description'),
                    data.get('brand_id') or None, data.get('category_id') or None,
                    data.get('group_id') or None, data.get('item_type', 'finished_goods'),
                    data.get('unit_of_measure', 'PCS'), data.get('secondary_uom'),
                    data.get('conversion_rate', 1.0), data.get('weight_kg'),
                    data.get('volume_m3'), data.get('length_cm'),
                    data.get('width_cm'), data.get('height_cm'),
                    data.get('color'), data.get('size'), data.get('material'),
                    data.get('country_of_origin'), data.get('hazard_class'),
                    data.get('temperature_requirement'), data.get('shelf_life_days'),
                    1 if data.get('expiry_tracking') else 0,
                    1 if data.get('batch_tracking') else 0,
                    1 if data.get('lot_tracking') else 0,
                    1 if data.get('serial_tracking') else 0,
                    1 if data.get('quality_inspection_required') else 0,
                    data.get('min_stock_level', 0), data.get('max_stock_level'),
                    data.get('reorder_point', 0), data.get('reorder_quantity'),
                    data.get('safety_stock'), data.get('economic_order_quantity'),
                    data.get('preferred_warehouse_id') or None,
                    data.get('preferred_location_id') or None,
                    data.get('rotation_policy', 'FIFO'),
                    data.get('picking_strategy'), data.get('packing_instruction'),
                    data.get('handling_instruction'),
                    data.get('selling_status', 'active'),
                    data.get('procurement_status', 'active'),
                    data.get('abc_class'), 1 if data.get('is_kit') else 0,
                    1 if data.get('is_bundle') else 0,
                    data.get('kit_components'),
                    1 if data.get('is_active') else 0,
                    item_id
                ))
                db.commit()
                log_wms_audit('UPDATE', 'ITEM', item_id, {'item_code': data.get('item_code')})
                flash('Item updated successfully!', 'success')
                return redirect(url_for('wms_item_detail', item_id=item_id))
            except Exception as e:
                import traceback
                print(f"WMS item update error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error updating item. Please try again.', 'error')

        categories = db.execute('SELECT * FROM wms_item_categories WHERE is_active = 1 ORDER BY name').fetchall()
        brands = db.execute('SELECT * FROM wms_item_brands WHERE is_active = 1 ORDER BY name').fetchall()
        groups = db.execute('SELECT * FROM wms_item_groups WHERE is_active = 1 ORDER BY name').fetchall()
        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()

        title = f'Edit Item: {item["name"]}'
        return render_template('wms/item_form.html',
            title=title,
            item=item,
            categories=categories,
            brands=brands,
            groups=groups,
            warehouses=warehouses,
            form_action=url_for('wms_items_edit', item_id=item_id)
        )

    # ============================================================
    # WAREHOUSES
    # ============================================================

    @app.route('/wms/warehouses')
    @wms_permission_required('warehouses', 'view')
    def wms_warehouses():
        """Warehouse list."""
        db = get_db()
        warehouses = db.execute('''
            SELECT w.*, c.name as company_name,
                (SELECT COUNT(*) FROM wms_locations l WHERE l.warehouse_id = w.id AND l.is_active = 1) as location_count,
                (SELECT COALESCE(SUM(quantity), 0) FROM wms_inventory_balances b WHERE b.warehouse_id = w.id) as total_stock,
                (SELECT COUNT(*) FROM wms_alerts a WHERE a.warehouse_id = w.id AND a.is_active = 1) as alert_count
            FROM wms_warehouses w
            JOIN wms_companies c ON c.id = w.company_id
            WHERE w.is_active = 1
            ORDER BY c.name, w.name
        ''').fetchall()

        title = 'Warehouses'
        return render_template('wms/warehouses.html',
            title=title,
            warehouses=warehouses
        )

    @app.route('/wms/warehouses/new', methods=['GET', 'POST'])
    @wms_permission_required('warehouses', 'create')
    def wms_warehouses_new():
        """Create new warehouse."""
        db = get_db()

        if request.method == 'POST':
            data = request.form
            # Validate required fields
            code = (data.get('code') or '').strip()
            name = (data.get('name') or '').strip()
            if not code or not name:
                if not code:
                    flash('Warehouse code is required.', 'error')
                if not name:
                    flash('Warehouse name is required.', 'error')
                companies = db.execute('SELECT * FROM wms_companies WHERE is_active = 1 ORDER BY name').fetchall()
                if not companies:
                    companies = db.execute('SELECT id, name FROM companies ORDER BY name').fetchall()
                users = db.execute('SELECT id, username FROM users ORDER BY username').fetchall()
                return render_template('wms/warehouse_form.html', title='New Warehouse', warehouse=None,
                    companies=companies, users=users, form_action=url_for('wms_warehouses_new'))
            try:
                db.execute('''
                    INSERT INTO wms_warehouses (
                        company_id, code, name, name_local, type, address, city, country,
                        phone, email, manager_id, allow_receiving, allow_shipping, allow_storage,
                        default_rotation_policy, min_temp, max_temp, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('company_id'), data.get('code'), data.get('name'),
                    data.get('name_local'), data.get('type', 'main'),
                    data.get('address'), data.get('city'), data.get('country'),
                    data.get('phone'), data.get('email'), data.get('manager_id') or None,
                    1 if data.get('allow_receiving') else 0,
                    1 if data.get('allow_shipping') else 0,
                    1 if data.get('allow_storage') else 0,
                    data.get('default_rotation_policy', 'FIFO'),
                    data.get('min_temp'), data.get('max_temp'),
                    data.get('notes')
                ))
                db.commit()
                wh_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
                log_wms_audit('CREATE', 'WAREHOUSE', wh_id, {'code': data.get('code')})
                flash('Warehouse created successfully!', 'success')
                return redirect(url_for('wms_warehouse_detail', warehouse_id=wh_id))
            except Exception as e:
                import traceback
                print(f"WMS warehouse create error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error creating warehouse. Please try again.', 'error')

        companies = db.execute('SELECT * FROM wms_companies WHERE is_active = 1 ORDER BY name').fetchall()
        if not companies:
            companies = db.execute('SELECT id, name FROM companies ORDER BY name').fetchall()
        users = db.execute('SELECT id, username FROM users ORDER BY username').fetchall()

        title = 'New Warehouse'
        return render_template('wms/warehouse_form.html',
            title=title,
            warehouse=None,
            companies=companies,
            users=users,
            form_action=url_for('wms_warehouses_new')
        )

    @app.route('/wms/warehouses/<int:warehouse_id>')
    @wms_permission_required('warehouses', 'view')
    def wms_warehouse_detail(warehouse_id):
        """Warehouse detail view."""
        db = get_db()
        warehouse = db.execute('''
            SELECT w.*, c.name as company_name, u.username as manager_name
            FROM wms_warehouses w
            LEFT JOIN wms_companies c ON c.id = w.company_id
            LEFT JOIN users u ON u.id = w.manager_id
            WHERE w.id = ?
        ''', (warehouse_id,)).fetchone()

        if not warehouse:
            flash('Warehouse not found.', 'error')
            return redirect(url_for('wms_warehouses'))

        # Zones
        zones = db.execute('''
            SELECT z.*,
                (SELECT COUNT(*) FROM wms_locations l WHERE l.zone_id = z.id AND l.is_active = 1) as location_count,
                (SELECT COALESCE(SUM(b.quantity), 0) FROM wms_inventory_balances b
                 JOIN wms_locations l ON l.id = b.location_id WHERE l.zone_id = z.id) as total_stock
            FROM wms_zones z WHERE z.warehouse_id = ? ORDER BY z.sort_order, z.name
        ''', (warehouse_id,)).fetchall()

        # Locations summary
        locations = db.execute('''
            SELECT l.*, z.name as zone_name
            FROM wms_locations l
            LEFT JOIN wms_zones z ON z.id = l.zone_id
            WHERE l.warehouse_id = ? AND l.is_active = 1
            ORDER BY l.code LIMIT 100
        ''', (warehouse_id,)).fetchall()

        # Stock summary
        stock_summary = db.execute('''
            SELECT
                SUM(quantity) as total_qty,
                SUM(reserved_quantity) as reserved,
                SUM(allocated_quantity) as allocated,
                SUM(CASE WHEN status = 'AVAILABLE' THEN quantity ELSE 0 END) as available,
                SUM(CASE WHEN status IN ('BLOCKED','QUARANTINE','DAMAGED') THEN quantity ELSE 0 END) as blocked,
                COUNT(DISTINCT item_id) as sku_count
            FROM wms_inventory_balances
            WHERE warehouse_id = ?
        ''', (warehouse_id,)).fetchone()

        title = f'Warehouse: {warehouse["name"]}'
        return render_template('wms/warehouse_detail.html',
            title=title,
            warehouse=warehouse,
            zones=zones,
            locations=locations,
            stock_summary=stock_summary
        )

    @app.route('/wms/warehouses/<int:warehouse_id>/edit', methods=['GET', 'POST'])
    @wms_permission_required('warehouses', 'edit')
    def wms_warehouses_edit(warehouse_id):
        """Edit warehouse."""
        db = get_db()
        warehouse = db.execute('SELECT * FROM wms_warehouses WHERE id = ?', (warehouse_id,)).fetchone()
        if not warehouse:
            flash('Warehouse not found.', 'error')
            return redirect(url_for('wms_warehouses'))

        if request.method == 'POST':
            data = request.form
            try:
                db.execute('''
                    UPDATE wms_warehouses SET
                        company_id = ?, code = ?, name = ?, name_local = ?,
                        type = ?, address = ?, city = ?, country = ?,
                        phone = ?, email = ?, manager_id = ?,
                        allow_receiving = ?, allow_shipping = ?, allow_storage = ?,
                        default_rotation_policy = ?, min_temp = ?, max_temp = ?,
                        notes = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    data.get('company_id'), data.get('code'), data.get('name'),
                    data.get('name_local'), data.get('type', 'main'),
                    data.get('address'), data.get('city'), data.get('country'),
                    data.get('phone'), data.get('email'), data.get('manager_id') or None,
                    1 if data.get('allow_receiving') else 0,
                    1 if data.get('allow_shipping') else 0,
                    1 if data.get('allow_storage') else 0,
                    data.get('default_rotation_policy', 'FIFO'),
                    data.get('min_temp'), data.get('max_temp'),
                    data.get('notes'),
                    1 if data.get('is_active') else 0,
                    warehouse_id
                ))
                db.commit()
                log_wms_audit('UPDATE', 'WAREHOUSE', warehouse_id, {'code': data.get('code')})
                flash('Warehouse updated successfully!', 'success')
                return redirect(url_for('wms_warehouse_detail', warehouse_id=warehouse_id))
            except Exception as e:
                import traceback
                print(f"WMS warehouse update error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error updating warehouse. Please try again.', 'error')

        companies = db.execute('SELECT * FROM wms_companies WHERE is_active = 1 ORDER BY name').fetchall()
        if not companies:
            companies = db.execute('SELECT id, name FROM companies ORDER BY name').fetchall()
        users = db.execute('SELECT id, username FROM users ORDER BY username').fetchall()

        title = f'Edit Warehouse: {warehouse["name"]}'
        return render_template('wms/warehouse_form.html',
            title=title,
            warehouse=warehouse,
            companies=companies,
            users=users,
            form_action=url_for('wms_warehouses_edit', warehouse_id=warehouse_id)
        )

    # ============================================================
    # LOCATIONS
    # ============================================================

    @app.route('/wms/locations')
    @wms_permission_required('locations', 'view')
    def wms_locations():
        """Locations list."""

        db = get_db()
        warehouse_id = request.args.get('warehouse_id', '')
        zone_id = request.args.get('zone_id', '')
        location_type = request.args.get('location_type', '')
        search = request.args.get('search', '').strip()
        page = int(request.args.get('page', 1))
        per_page = 50

        query = '''
            SELECT l.*, w.name as warehouse_name, z.name as zone_name,
                   i.item_code, i.name as item_name,
                   (SELECT SUM(quantity) FROM wms_inventory_balances WHERE location_id = l.id) as current_stock
            FROM wms_locations l
            JOIN wms_warehouses w ON w.id = l.warehouse_id
            LEFT JOIN wms_zones z ON z.id = l.zone_id
            LEFT JOIN wms_inventory_balances b ON b.location_id = l.id
            LEFT JOIN wms_items i ON i.id = b.item_id
            WHERE l.is_active = 1
        '''
        params = []

        if warehouse_id:
            query += " AND l.warehouse_id = ?"
            params.append(warehouse_id)
        if zone_id:
            query += " AND l.zone_id = ?"
            params.append(zone_id)
        if location_type:
            query += " AND l.location_type = ?"
            params.append(location_type)
        if search:
            query += " AND (l.code LIKE ? OR l.name LIKE ? OR l.barcode LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY l.code LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        locations = db.execute(query, params).fetchall()

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        zones = db.execute('SELECT * FROM wms_zones WHERE is_active = 1 ORDER BY name').fetchall() if warehouse_id else []
        location_types = db.execute('SELECT DISTINCT location_type FROM wms_locations WHERE is_active = 1').fetchall()

        title = 'Locations'
        return render_template('wms/locations.html',
            title=title,
            locations=locations,
            warehouses=warehouses,
            zones=zones,
            location_types=location_types,
            warehouse_id=warehouse_id,
            zone_id=zone_id,
            location_type=location_type,
            search=search,
            page=page,
            per_page=per_page,
            total_count=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1
        )

    @app.route('/wms/locations/new', methods=['GET', 'POST'])
    @wms_permission_required('locations', 'create')
    def wms_locations_new():
        """Create new location."""
        db = get_db()

        if request.method == 'POST':
            data = request.form
            is_valid, code = validate_location_code(data.get('code'))
            if not is_valid:
                flash(code, 'error')
                return redirect(url_for('wms_locations_new'))

            try:
                db.execute('''
                    INSERT INTO wms_locations (
                        warehouse_id, zone_id, code, barcode, name, location_type,
                        coordinates_rack, coordinates_bay, coordinates_level,
                        coordinates_position, coordinates_bin,
                        capacity_pallets, capacity_weight_kg, capacity_volume_m3, capacity_cartons,
                        picking_enabled, putaway_enabled, replenishment_enabled,
                        temperature_min, temperature_max, preferred_item_class,
                        cycle_count_class, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('warehouse_id'), data.get('zone_id') or None,
                    code, data.get('barcode'), data.get('name'),
                    data.get('location_type', 'STORAGE'),
                    data.get('coordinates_rack'), data.get('coordinates_bay'),
                    data.get('coordinates_level'), data.get('coordinates_position'),
                    data.get('coordinates_bin'),
                    data.get('capacity_pallets'), data.get('capacity_weight_kg'),
                    data.get('capacity_volume_m3'), data.get('capacity_cartons'),
                    1 if data.get('picking_enabled') else 0,
                    1 if data.get('putaway_enabled') else 0,
                    1 if data.get('replenishment_enabled') else 0,
                    data.get('temperature_min'), data.get('temperature_max'),
                    data.get('preferred_item_class'), data.get('cycle_count_class'),
                    data.get('notes')
                ))
                db.commit()
                loc_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
                log_wms_audit('CREATE', 'LOCATION', loc_id, {'code': code})
                flash('Location created successfully!', 'success')
                return redirect(url_for('wms_locations'))
            except Exception as e:
                import traceback
                print(f"WMS location create error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error creating location. Please try again.', 'error')

        warehouse_id = request.args.get('warehouse_id')
        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        zones = db.execute('SELECT * FROM wms_zones WHERE is_active = 1 ORDER BY name').fetchall()
        location_types = db.execute('SELECT * FROM wms_location_types WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'New Location'
        return render_template('wms/location_form.html',
            title=title,
            location=None,
            warehouses=warehouses,
            zones=zones,
            location_types=location_types,
            selected_warehouse=warehouse_id,
            form_action=url_for('wms_locations_new')
        )

    @app.route('/wms/locations/<int:location_id>')
    @wms_permission_required('locations', 'view')
    def wms_location_detail(location_id):
        """Location detail."""

        db = get_db()
        location = db.execute('''
            SELECT l.*, w.name as warehouse_name, z.name as zone_name
            FROM wms_locations l
            JOIN wms_warehouses w ON w.id = l.warehouse_id
            LEFT JOIN wms_zones z ON z.id = l.zone_id
            WHERE l.id = ?
        ''', (location_id,)).fetchone()

        if not location:
            flash('Location not found.', 'error')
            return redirect(url_for('wms_locations'))

        # Stock at this location
        stock = db.execute('''
            SELECT b.*, i.item_code, i.name as item_name, i.unit_of_measure,
                   l.lot_number, l.expiry_date
            FROM wms_inventory_balances b
            JOIN wms_items i ON i.id = b.item_id
            LEFT JOIN wms_lots l ON l.id = b.lot_id
            WHERE b.location_id = ? AND b.quantity > 0
            ORDER BY i.name
        ''', (location_id,)).fetchall()

        # Recent movements
        movements = db.execute('''
            SELECT l.*, u.username, i.item_code, i.name as item_name
            FROM wms_inventory_ledger l
            LEFT JOIN users u ON u.id = l.user_id
            JOIN wms_items i ON i.id = l.item_id
            WHERE l.location_id = ?
            ORDER BY l.created_at DESC LIMIT 50
        ''', (location_id,)).fetchall()

        title = f'Location: {location["code"]}'
        return render_template('wms/location_detail.html',
            title=title,
            location=location,
            stock=stock,
            movements=movements
        )

    @app.route('/wms/locations/<int:location_id>/edit', methods=['GET', 'POST'])
    @wms_permission_required('locations', 'edit')
    def wms_locations_edit(location_id):
        """Edit location."""

        db = get_db()
        location = db.execute('SELECT * FROM wms_locations WHERE id = ?', (location_id,)).fetchone()
        if not location:
            flash('Location not found.', 'error')
            return redirect(url_for('wms_locations'))

        if request.method == 'POST':
            data = request.form
            is_valid, code = validate_location_code(data.get('code'))
            if not is_valid:
                flash(code, 'error')
                return redirect(url_for('wms_locations_edit', location_id=location_id))

            try:
                db.execute('''
                    UPDATE wms_locations SET
                        zone_id = ?, code = ?, barcode = ?, name = ?,
                        location_type = ?,
                        coordinates_rack = ?, coordinates_bay = ?,
                        coordinates_level = ?, coordinates_position = ?,
                        coordinates_bin = ?,
                        capacity_pallets = ?, capacity_weight_kg = ?,
                        capacity_volume_m3 = ?, capacity_cartons = ?,
                        picking_enabled = ?, putaway_enabled = ?,
                        replenishment_enabled = ?, is_locked = ?,
                        lock_reason = ?,
                        temperature_min = ?, temperature_max = ?,
                        preferred_item_class = ?, cycle_count_class = ?,
                        notes = ?, is_active = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (
                    data.get('zone_id') or None, code, data.get('barcode'),
                    data.get('name'), data.get('location_type', 'STORAGE'),
                    data.get('coordinates_rack'), data.get('coordinates_bay'),
                    data.get('coordinates_level'), data.get('coordinates_position'),
                    data.get('coordinates_bin'),
                    data.get('capacity_pallets'), data.get('capacity_weight_kg'),
                    data.get('capacity_volume_m3'), data.get('capacity_cartons'),
                    1 if data.get('picking_enabled') else 0,
                    1 if data.get('putaway_enabled') else 0,
                    1 if data.get('replenishment_enabled') else 0,
                    1 if data.get('is_locked') else 0,
                    data.get('lock_reason'),
                    data.get('temperature_min'), data.get('temperature_max'),
                    data.get('preferred_item_class'), data.get('cycle_count_class'),
                    data.get('notes'),
                    1 if data.get('is_active') else 0,
                    location_id
                ))
                db.commit()
                log_wms_audit('UPDATE', 'LOCATION', location_id, {'code': code})
                flash('Location updated successfully!', 'success')
                return redirect(url_for('wms_location_detail', location_id=location_id))
            except Exception as e:
                import traceback
                print(f"WMS location update error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error updating location. Please try again.', 'error')

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        zones = db.execute('SELECT * FROM wms_zones WHERE warehouse_id = ? AND is_active = 1 ORDER BY name', (location['warehouse_id'],)).fetchall()
        location_types = db.execute('SELECT * FROM wms_location_types WHERE is_active = 1 ORDER BY name').fetchall()

        title = f'Edit Location: {location["code"]}'
        return render_template('wms/location_form.html',
            title=title,
            location=location,
            warehouses=warehouses,
            zones=zones,
            location_types=location_types,
            selected_warehouse=location['warehouse_id'],
            form_action=url_for('wms_locations_edit', location_id=location_id)
        )

    # ============================================================
    # INVENTORY OVERVIEW
    # ============================================================

    @app.route('/wms/inventory')
    @wms_permission_required('inventory', 'view')
    def wms_inventory():
        """Inventory overview."""

        db = get_db()
        search = request.args.get('search', '').strip()
        warehouse_ids = request.args.getlist('warehouse_id')
        location_id = request.args.get('location_id', '')
        category_ids = request.args.getlist('category_id')
        brand_id = request.args.get('brand_id', '')
        statuses = request.args.getlist('status')
        stock_filters = request.args.getlist('stock_filter')
        page = int(request.args.get('page', 1))
        per_page = 100

        # Build warehouse_id / category_id / status for display (use first if multiple)
        warehouse_id = warehouse_ids[0] if warehouse_ids else ''
        category_id = category_ids[0] if category_ids else ''
        status = statuses[0] if statuses else ''
        stock_filter = stock_filters[0] if stock_filters else ''

        query = '''
            SELECT b.*, i.item_code, i.name as item_name, i.unit_of_measure,
                   i.part_number, i.barcode as item_barcode,
                   w.name as warehouse_name, l.code as location_code,
                   l.zone_id,
                   cat.name as category_name,
                   br.name as brand_name,
                   lot.lot_number, lot.expiry_date
            FROM wms_inventory_balances b
            JOIN wms_items i ON i.id = b.item_id
            JOIN wms_warehouses w ON w.id = b.warehouse_id
            LEFT JOIN wms_locations l ON l.id = b.location_id
            LEFT JOIN wms_item_categories cat ON cat.id = i.category_id
            LEFT JOIN wms_item_brands br ON br.id = i.brand_id
            LEFT JOIN wms_lots lot ON lot.id = b.lot_id
            WHERE b.quantity != 0 OR b.reserved_quantity != 0 OR b.allocated_quantity != 0
        '''
        params = []

        if search:
            query += " AND (i.item_code LIKE ? OR i.name LIKE ? OR i.barcode LIKE ? OR i.part_number LIKE ?)"
            sp = f'%{search}%'
            params.extend([sp, sp, sp, sp])
        if warehouse_ids:
            placeholders = ','.join(['?'] * len(warehouse_ids))
            query += f" AND b.warehouse_id IN ({placeholders})"
            params.extend(warehouse_ids)
        if location_id:
            query += " AND b.location_id = ?"
            params.append(location_id)
        if category_ids:
            placeholders = ','.join(['?'] * len(category_ids))
            query += f" AND i.category_id IN ({placeholders})"
            params.extend(category_ids)
        if brand_id:
            query += " AND i.brand_id = ?"
            params.append(brand_id)
        if statuses:
            placeholders = ','.join(['?'] * len(statuses))
            query += f" AND b.status IN ({placeholders})"
            params.extend(statuses)
        if stock_filters:
            for sf in stock_filters:
                if sf == 'zero':
                    query += " AND b.quantity = 0"
                elif sf == 'negative':
                    query += " AND b.quantity < 0"
                elif sf == 'low':
                    query += " AND i.min_stock_level > 0 AND b.quantity < i.min_stock_level"
                elif sf == 'below_reorder':
                    query += " AND i.reorder_point > 0 AND b.quantity < i.reorder_point"
                elif sf == 'available_only':
                    query += " AND b.status = 'AVAILABLE' AND b.quantity > 0"
                elif sf == 'reserved':
                    query += " AND b.reserved_quantity > 0"

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY i.name LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        inventory = db.execute(query, params).fetchall()

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        categories = db.execute('SELECT * FROM wms_item_categories WHERE is_active = 1 ORDER BY name').fetchall()
        brands = db.execute('SELECT * FROM wms_item_brands WHERE is_active = 1 ORDER BY name').fetchall()

        # Summary stats
        summary = db.execute('''
            SELECT
                SUM(quantity) as total_qty,
                SUM(reserved_quantity) as total_reserved,
                SUM(allocated_quantity) as total_allocated,
                SUM(CASE WHEN status = 'AVAILABLE' THEN quantity ELSE 0 END) as available,
                SUM(CASE WHEN status IN ('BLOCKED','QUARANTINE') THEN quantity ELSE 0 END) as blocked,
                SUM(CASE WHEN status = 'DAMAGED' THEN quantity ELSE 0 END) as damaged,
                SUM(CASE WHEN status = 'RESERVED' THEN quantity ELSE 0 END) as reserved,
                COUNT(DISTINCT item_id) as sku_count,
                COUNT(DISTINCT warehouse_id) as warehouse_count
            FROM wms_inventory_balances b
            JOIN wms_items i ON i.id = b.item_id
            WHERE 1=1
            ''' + ('' if not warehouse_ids else ' AND b.warehouse_id IN (' + ','.join(['?'] * len(warehouse_ids)) + ')'),
            ([] if not warehouse_ids else warehouse_ids)
        ).fetchone()

        title = 'Inventory Overview'
        return render_template('wms/inventory.html',
            title=title,
            inventory=inventory,
            warehouses=warehouses,
            categories=categories,
            brands=brands,
            search=search,
            warehouse_ids=warehouse_ids,
            location_id=location_id,
            category_ids=category_ids,
            brand_id=brand_id,
            statuses=statuses,
            stock_filters=stock_filters,
            page=page,
            per_page=per_page,
            total_count=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1,
            summary=summary
        )

    # ============================================================
    # RECEIVING / INBOUND
    # ============================================================

    @app.route('/wms/receiving')
    @wms_permission_required('receiving', 'view')
    def wms_receiving():
        """Receiving/Inbound list."""

        db = get_db()
        status = request.args.get('status', '')
        warehouse_id = request.args.get('warehouse_id', '')
        search = request.args.get('search', '').strip()
        page = int(request.args.get('page', 1))
        per_page = 50

        query = '''
            SELECT r.*, w.name as warehouse_name, s.name as supplier_name,
                   u.username as received_by_name
            FROM wms_inbound_receipts r
            JOIN wms_warehouses w ON w.id = r.warehouse_id
            LEFT JOIN suppliers s ON s.id = r.supplier_id
            LEFT JOIN users u ON u.id = r.received_by
            WHERE 1=1
        '''
        params = []

        if status:
            query += " AND r.status = ?"
            params.append(status)
        if warehouse_id:
            query += " AND r.warehouse_id = ?"
            params.append(warehouse_id)
        if search:
            query += " AND (r.receipt_number LIKE ? OR r.po_reference LIKE ?)"
            params.append(f'%{search}%')

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY r.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        receipts = db.execute(query, params).fetchall()

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'Receiving / Inbound'
        return render_template('wms/receiving.html',
            title=title,
            receipts=receipts,
            warehouses=warehouses,
            status=status,
            warehouse_id=warehouse_id,
            search=search,
            page=page,
            per_page=per_page,
            total_count=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1
        )

    @app.route('/wms/receiving/new', methods=['GET', 'POST'])
    @wms_permission_required('receiving', 'create')
    def wms_receiving_new():
        """Create new inbound receipt."""
        db = get_db()

        if request.method == 'POST':
            data = request.form
            try:
                receipt_number = generate_wms_code('RECEIPT')
                db.execute('''
                    INSERT INTO wms_inbound_receipts (
                        receipt_number, receipt_type, warehouse_id, company_id,
                        supplier_id, po_reference, asn_reference, expected_date,
                        status, notes, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    receipt_number,
                    data.get('receipt_type', 'PO_RECEIPT'),
                    data.get('warehouse_id'),
                    data.get('company_id') or None,
                    data.get('supplier_id') or None,
                    data.get('po_reference'),
                    data.get('asn_reference'),
                    data.get('expected_date'),
                    'EXPECTED',
                    data.get('notes'),
                    session.get('user_id')
                ))
                db.commit()
                receipt_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
                log_wms_audit('CREATE', 'INBOUND_RECEIPT', receipt_id, {'receipt_number': receipt_number})
                flash(f'Receipt {receipt_number} created! Add line items next.', 'success')
                return redirect(url_for('wms_receiving_detail', receipt_id=receipt_id))
            except Exception as e:
                import traceback
                print(f"WMS receipt create error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error creating receipt. Please try again.', 'error')

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        suppliers = db.execute('SELECT * FROM suppliers ORDER BY name').fetchall()
        companies = db.execute('SELECT * FROM wms_companies WHERE is_active = 1 ORDER BY name').fetchall()
        if not companies:
            companies = db.execute('SELECT id, name FROM companies ORDER BY name').fetchall()

        title = 'New Inbound Receipt'
        return render_template('wms/receiving_form.html',
            title=title,
            receipt=None,
            warehouses=warehouses,
            suppliers=suppliers,
            companies=companies,
            form_action=url_for('wms_receiving_new')
        )

    @app.route('/wms/receiving/<int:receipt_id>')
    @wms_permission_required('receiving', 'view')
    def wms_receiving_detail(receipt_id):
        """Receiving detail with lines."""

        db = get_db()
        receipt = db.execute('''
            SELECT r.*, w.name as warehouse_name, s.name as supplier_name,
                   u.username as received_by_name, c.name as company_name
            FROM wms_inbound_receipts r
            JOIN wms_warehouses w ON w.id = r.warehouse_id
            LEFT JOIN suppliers s ON s.id = r.supplier_id
            LEFT JOIN users u ON u.id = r.received_by
            LEFT JOIN wms_companies c ON c.id = r.company_id
            WHERE r.id = ?
        ''', (receipt_id,)).fetchone()

        if not receipt:
            flash('Receipt not found.', 'error')
            return redirect(url_for('wms_receiving'))

        lines = db.execute('''
            SELECT rl.*, i.item_code, i.name as item_name, i.unit_of_measure,
                   l.code as location_code
            FROM wms_inbound_receipt_lines rl
            JOIN wms_items i ON i.id = rl.item_id
            LEFT JOIN wms_locations l ON l.id = rl.location_id
            WHERE rl.receipt_id = ?
            ORDER BY rl.line_number
        ''', (receipt_id,)).fetchall()

        title = f'Receipt: {receipt["receipt_number"]}'
        return render_template('wms/receiving_detail.html',
            title=title,
            receipt=receipt,
            lines=lines
        )

    @app.route('/wms/receiving/<int:receipt_id>/receive', methods=['POST'])
    @wms_permission_required('receiving', 'edit')
    def wms_receiving_receive(receipt_id):
        """Receive items against a receipt."""

        db = get_db()
        data = request.form
        try:
            # Update receipt status
            db.execute('''
                UPDATE wms_inbound_receipts SET
                    actual_arrival_date = COALESCE(?, datetime('now')),
                    received_by = ?,
                    status = 'PARTIAL',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (data.get('actual_arrival_date'), session.get('user_id'), receipt_id))

            # Update or create receipt line
            line_id = data.get('line_id')
            received_qty = float(data.get('received_quantity', 0))
            accepted_qty = float(data.get('accepted_quantity', received_qty))
            rejected_qty = float(data.get('rejected_quantity', 0))
            lot_number = data.get('lot_number')
            expiry_date = data.get('expiry_date')
            location_id = data.get('location_id')

            if line_id:
                db.execute('''
                    UPDATE wms_inbound_receipt_lines SET
                        received_quantity = received_quantity + ?,
                        accepted_quantity = accepted_quantity + ?,
                        rejected_quantity = rejected_quantity + ?,
                        lot_number = COALESCE(?, lot_number),
                        expiry_date = COALESCE(?, expiry_date),
                        location_id = COALESCE(?, location_id),
                        status = CASE WHEN (received_quantity + ?) >= expected_quantity THEN 'COMPLETED' ELSE 'PARTIAL' END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND receipt_id = ?
                ''', (received_qty, accepted_qty, rejected_qty, lot_number, expiry_date, location_id,
                      received_qty, line_id, receipt_id))
            else:
                # Add new line
                item_id = data.get('item_id')
                if not item_id:
                    flash('Item is required.', 'error')
                    return redirect(url_for('wms_receiving_detail', receipt_id=receipt_id))

                line_num = db.execute('SELECT MAX(line_number) as max_line FROM wms_inbound_receipt_lines WHERE receipt_id = ?', (receipt_id,)).fetchone()['max_line'] or 0
                db.execute('''
                    INSERT INTO wms_inbound_receipt_lines (
                        receipt_id, line_number, item_id, expected_quantity,
                        received_quantity, accepted_quantity, rejected_quantity,
                        lot_number, expiry_date, location_id, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (receipt_id, line_num + 1, item_id, data.get('expected_quantity', received_qty),
                      received_qty, accepted_qty, rejected_qty, lot_number, expiry_date, location_id, 'PARTIAL'))

            # Create or update lot
            if lot_number and accepted_qty > 0:
                item_id = data.get('item_id') or db.execute(
                    'SELECT item_id FROM wms_inbound_receipt_lines WHERE id = ?', (line_id,)).fetchone()['item_id']
                receipt = db.execute('SELECT warehouse_id FROM wms_inbound_receipts WHERE id = ?', (receipt_id,)).fetchone()
                existing_lot = db.execute(
                    'SELECT id, quantity FROM wms_lots WHERE lot_number = ? AND item_id = ? AND warehouse_id = ?',
                    (lot_number, item_id, receipt['warehouse_id'])).fetchone()
                if existing_lot:
                    db.execute('UPDATE wms_lots SET quantity = quantity + ? WHERE id = ?', (accepted_qty, existing_lot['id']))
                    lot_id = existing_lot['id']
                else:
                    db.execute('''
                        INSERT INTO wms_lots (lot_number, item_id, warehouse_id, location_id, quantity, expiry_date, manufacturing_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (lot_number, item_id, receipt['warehouse_id'], location_id, accepted_qty,
                          expiry_date, data.get('manufacturing_date')))
                    lot_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
            else:
                lot_id = None

            # Update inventory balance
            if accepted_qty > 0:
                item_id = data.get('item_id') or db.execute(
                    'SELECT item_id FROM wms_inbound_receipt_lines WHERE id = ?', (line_id,)).fetchone()['item_id']
                receipt = db.execute('SELECT warehouse_id, company_id FROM wms_inbound_receipts WHERE id = ?', (receipt_id,)).fetchone()
                existing = db.execute('''
                    SELECT id FROM wms_inventory_balances
                    WHERE item_id = ? AND warehouse_id = ? AND location_id = ? AND status = 'AVAILABLE'
                ''', (item_id, receipt['warehouse_id'], location_id)).fetchone()
                if existing:
                    db.execute('''
                        UPDATE wms_inventory_balances SET
                            quantity = quantity + ?,
                            last_movement_date = datetime('now'),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (accepted_qty, existing['id']))
                else:
                    db.execute('''
                        INSERT INTO wms_inventory_balances (
                            item_id, lot_id, warehouse_id, location_id, company_id,
                            quantity, status, last_movement_date
                        ) VALUES (?, ?, ?, ?, ?, ?, 'AVAILABLE', datetime('now'))
                    ''', (item_id, lot_id, receipt['warehouse_id'], location_id, receipt['company_id'], accepted_qty))

                # Record ledger
                db.execute('''
                    INSERT INTO wms_inventory_ledger (
                        transaction_type, transaction_number, reference_type, reference_number,
                        item_id, lot_id, warehouse_id, location_id, company_id,
                        quantity_before, quantity_moved, quantity_after, status_after,
                        user_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', ('RECEIVE', db.execute('SELECT receipt_number FROM wms_inbound_receipts WHERE id = ?', (receipt_id,)).fetchone()['receipt_number'],
                      'INBOUND_RECEIPT', receipt_id, item_id, lot_id, receipt['warehouse_id'], location_id, receipt['company_id'],
                      0, accepted_qty, accepted_qty, 'AVAILABLE', session.get('user_id')))

            # Check if receipt is complete
            pending = db.execute('''
                SELECT COUNT(*) as cnt FROM wms_inbound_receipt_lines
                WHERE receipt_id = ? AND status != 'COMPLETED'
            ''', (receipt_id,)).fetchone()['cnt']
            if pending == 0:
                db.execute('UPDATE wms_inbound_receipts SET status = ? WHERE id = ?', ('COMPLETED', receipt_id))

            db.commit()
            log_wms_audit('RECEIVE', 'INBOUND_RECEIPT', receipt_id, {'received_qty': accepted_qty})
            flash(f'Received {accepted_qty} units successfully!', 'success')
        except Exception as e:
            import traceback
            print(f"WMS receive action error: {e}")
            traceback.print_exc()
            db.rollback()
            flash('Error receiving. Please try again.', 'error')

        return redirect(url_for('wms_receiving_detail', receipt_id=receipt_id))

    # ============================================================
    # PUTAWAY
    # ============================================================

    @app.route('/wms/putaway')
    @wms_permission_required('putaway', 'view')
    def wms_putaway():
        """Putaway tasks list."""

        db = get_db()
        status = request.args.get('status', '')
        warehouse_id = request.args.get('warehouse_id', '')
        page = int(request.args.get('page', 1))
        per_page = 50

        query = '''
            SELECT p.*, i.item_code, i.name as item_name,
                   w.name as warehouse_name,
                   sl.code as source_location,
                   dl.code as destination_location,
                   u.username as assigned_to_name
            FROM wms_putaway_tasks p
            JOIN wms_items i ON i.id = p.item_id
            LEFT JOIN wms_locations sl ON sl.id = p.source_location_id
            LEFT JOIN wms_locations dl ON dl.id = p.destination_location_id
            LEFT JOIN wms_inbound_receipt_lines rl ON rl.id = p.receipt_line_id
            LEFT JOIN wms_inbound_receipts r ON r.id = rl.receipt_id
            JOIN wms_warehouses w ON w.id = COALESCE(dl.warehouse_id, sl.warehouse_id, r.warehouse_id)
            LEFT JOIN users u ON u.id = p.assigned_to
            WHERE 1=1
        '''
        params = []
        if status:
            query += " AND p.status = ?"
            params.append(status)
        if warehouse_id:
            query += " AND COALESCE(dl.warehouse_id, sl.warehouse_id, r.warehouse_id) = ?"
            params.append(warehouse_id)

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY p.priority DESC, p.created_at LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        tasks = db.execute(query, params).fetchall()

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'Putaway'
        return render_template('wms/putaway.html',
            title=title,
            tasks=tasks,
            warehouses=warehouses,
            status=status,
            warehouse_id=warehouse_id,
            page=page,
            per_page=per_page,
            total_count=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1
        )

    @app.route('/wms/putaway/<int:task_id>/complete', methods=['POST'])
    @wms_permission_required('putaway', 'edit')
    @wms_csrf_required
    def wms_putaway_complete(task_id):
        """Complete a putaway task."""

        db = get_db()
        try:
            task = db.execute('''
                SELECT p.*, COALESCE(dl.warehouse_id, sl.warehouse_id, r.warehouse_id) as warehouse_id,
                       r.company_id
                FROM wms_putaway_tasks p
                LEFT JOIN wms_locations sl ON sl.id = p.source_location_id
                LEFT JOIN wms_locations dl ON dl.id = p.destination_location_id
                LEFT JOIN wms_inbound_receipt_lines rl ON rl.id = p.receipt_line_id
                LEFT JOIN wms_inbound_receipts r ON r.id = rl.receipt_id
                WHERE p.id = ?
            ''', (task_id,)).fetchone()
            if not task:
                flash('Task not found.', 'error')
                return redirect(url_for('wms_putaway'))
            if not ensure_warehouse_allowed(task['warehouse_id']):
                flash('You do not have access to this warehouse.', 'error')
                return redirect(url_for('wms_putaway'))

            destination_location_id = parse_positive_int(request.form.get('location_id'))
            if not destination_location_id:
                flash('A valid destination location is required.', 'error')
                return redirect(url_for('wms_putaway'))

            destination = db.execute('''
                SELECT id, warehouse_id, is_active, is_locked, is_quarantine,
                       capacity_weight_kg, current_weight_kg, capacity_volume_m3, current_volume_m3
                FROM wms_locations
                WHERE id = ?
            ''', (destination_location_id,)).fetchone()
            if not destination or destination['is_active'] != 1:
                flash('Destination location is not active.', 'error')
                return redirect(url_for('wms_putaway'))
            if destination['warehouse_id'] != task['warehouse_id']:
                flash('Destination location must be in the task warehouse.', 'error')
                return redirect(url_for('wms_putaway'))
            if destination['is_locked']:
                flash('Destination location is locked.', 'error')
                return redirect(url_for('wms_putaway'))

            db.execute('''
                UPDATE wms_putaway_tasks SET
                    status = 'COMPLETED',
                    destination_location_id = ?,
                    completed_at = datetime('now'),
                    completed_by = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (destination_location_id, session.get('user_id'), task_id))
            db.execute('''
                UPDATE wms_inventory_balances
                SET location_id = ?, updated_at = CURRENT_TIMESTAMP, last_movement_date = CURRENT_TIMESTAMP
                WHERE item_id = ?
                  AND warehouse_id = ?
                  AND COALESCE(lot_id, 0) = COALESCE(?, 0)
                  AND quantity >= ?
                  AND status IN ('AVAILABLE', 'QUARANTINE')
            ''', (destination_location_id, task['item_id'], task['warehouse_id'], task['lot_id'], task['quantity']))
            db.execute('''
                UPDATE wms_locations
                SET is_empty = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (destination_location_id,))
            db.commit()
            log_wms_audit('COMPLETE', 'PUTAWAY_TASK', task_id, {
                'before_destination_location_id': task['destination_location_id'],
                'after_destination_location_id': destination_location_id,
                'quantity': task['quantity'],
            })
            flash('Putaway task completed!', 'success')
        except Exception as e:
            import traceback
            print(f"WMS putaway task complete error: {e}")
            traceback.print_exc()
            db.rollback()
            flash('Error completing task. Please try again.', 'error')

        return redirect(url_for('wms_putaway'))

    # ============================================================
    # PUTAWAY RULES ENGINE
    # ============================================================

    @app.route('/wms/putaway/rules')
    @wms_permission_required('putaway', 'view')
    def wms_putaway_rules():
        """List all putaway rules."""
        db = get_db()
        warehouse_id = request.args.get('warehouse_id', '')

        query = '''
            SELECT r.*, z.code as zone_code, z.name as zone_name,
                   w.code as warehouse_code, w.name as warehouse_name,
                   u.username as created_by_name
            FROM wms_putaway_rules r
            LEFT JOIN wms_zones z ON z.id = r.target_zone_id
            LEFT JOIN wms_warehouses w ON w.id = r.target_warehouse_id
            LEFT JOIN users u ON u.id = r.created_by
            WHERE 1=1
        '''
        params = []
        if warehouse_id:
            query += " AND r.target_warehouse_id = ?"
            params.append(warehouse_id)

        rules = db.execute(query, params).fetchall()
        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        zones = db.execute('SELECT * FROM wms_zones WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'Putaway Rules'
        return render_template('wms/putaway_rules.html',
            title=title,
            rules=rules,
            warehouses=warehouses,
            zones=zones,
            warehouse_id=warehouse_id
        )

    @app.route('/wms/putaway/rules/new', methods=['GET', 'POST'])
    @wms_permission_required('putaway', 'create')
    def wms_putaway_rules_new():
        """Create a new putaway rule."""
        db = get_db()

        if request.method == 'POST':
            try:
                rule_name = request.form.get('rule_name')
                rule_type = request.form.get('rule_type')
                description = request.form.get('description')
                priority = int(request.form.get('priority', 5))
                is_active = 1 if request.form.get('is_active') else 0
                conditions_json = request.form.get('conditions_json', '{}')
                action_type = request.form.get('action_type')
                target_zone_id = request.form.get('target_zone_id') or None
                target_location_type = request.form.get('target_location_type')
                target_warehouse_id = request.form.get('target_warehouse_id') or None
                velocity_class = request.form.get('velocity_class')
                hazmat_class = request.form.get('hazmat_class')

                db.execute('''
                    INSERT INTO wms_putaway_rules
                    (rule_name, rule_type, description, priority, is_active, conditions_json,
                     action_type, target_zone_id, target_location_type, target_warehouse_id,
                     velocity_class, hazmat_class, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (rule_name, rule_type, description, priority, is_active, conditions_json,
                      action_type, target_zone_id, target_location_type, target_warehouse_id,
                      velocity_class, hazmat_class, session.get('user_id')))
                db.commit()
                log_wms_audit('CREATE', 'PUTAWAY_RULE', db.execute('SELECT last_insert_rowid() as id').fetchone()['id'])
                flash('Putaway rule created successfully!', 'success')
                return redirect(url_for('wms_putaway_rules'))
            except Exception as e:
                import traceback
                print(f"WMS putaway rule create error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error creating rule. Please try again.', 'error')

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        zones = db.execute('SELECT * FROM wms_zones WHERE is_active = 1 ORDER BY name').fetchall()
        title = 'New Putaway Rule'
        return render_template('wms/putaway_rule_form.html',
            title=title,
            rule=None,
            warehouses=warehouses,
            zones=zones
        )

    @app.route('/wms/putaway/rules/<int:rule_id>', methods=['GET', 'POST'])
    @wms_permission_required('putaway', 'edit')
    def wms_putaway_rules_edit(rule_id):
        """Edit an existing putaway rule."""
        db = get_db()
        rule = db.execute('SELECT * FROM wms_putaway_rules WHERE id = ?', (rule_id,)).fetchone()

        if not rule:
            flash('Rule not found.', 'error')
            return redirect(url_for('wms_putaway_rules'))

        if request.method == 'POST':
            try:
                rule_name = request.form.get('rule_name')
                rule_type = request.form.get('rule_type')
                description = request.form.get('description')
                priority = int(request.form.get('priority', 5))
                is_active = 1 if request.form.get('is_active') else 0
                conditions_json = request.form.get('conditions_json', '{}')
                action_type = request.form.get('action_type')
                target_zone_id = request.form.get('target_zone_id') or None
                target_location_type = request.form.get('target_location_type')
                target_warehouse_id = request.form.get('target_warehouse_id') or None
                velocity_class = request.form.get('velocity_class')
                hazmat_class = request.form.get('hazmat_class')

                db.execute('''
                    UPDATE wms_putaway_rules SET
                        rule_name = ?, rule_type = ?, description = ?, priority = ?,
                        is_active = ?, conditions_json = ?, action_type = ?,
                        target_zone_id = ?, target_location_type = ?, target_warehouse_id = ?,
                        velocity_class = ?, hazmat_class = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (rule_name, rule_type, description, priority, is_active, conditions_json,
                      action_type, target_zone_id, target_location_type, target_warehouse_id,
                      velocity_class, hazmat_class, rule_id))
                db.commit()
                log_wms_audit('UPDATE', 'PUTAWAY_RULE', rule_id)
                flash('Putaway rule updated successfully!', 'success')
                return redirect(url_for('wms_putaway_rules'))
            except Exception as e:
                import traceback
                print(f"WMS putaway rule update error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error updating rule. Please try again.', 'error')

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        zones = db.execute('SELECT * FROM wms_zones WHERE is_active = 1 ORDER BY name').fetchall()
        title = 'Edit Putaway Rule'
        return render_template('wms/putaway_rule_form.html',
            title=title,
            rule=rule,
            warehouses=warehouses,
            zones=zones
        )

    @app.route('/wms/putaway/rules/<int:rule_id>/delete', methods=['POST'])
    @wms_permission_required('putaway', 'delete')
    def wms_putaway_rules_delete(rule_id):
        """Delete a putaway rule."""
        db = get_db()
        try:
            db.execute('DELETE FROM wms_putaway_rules WHERE id = ?', (rule_id,))
            db.commit()
            log_wms_audit('DELETE', 'PUTAWAY_RULE', rule_id)
            flash('Putaway rule deleted successfully!', 'success')
        except Exception as e:
            import traceback
            print(f"WMS putaway rule delete error: {e}")
            traceback.print_exc()
            db.rollback()
            flash('Error deleting rule. Please try again.', 'error')
        return redirect(url_for('wms_putaway_rules'))

    @app.route('/wms/putaway/rules/<int:rule_id>/toggle', methods=['POST'])
    @wms_permission_required('putaway', 'edit')
    def wms_putaway_rules_toggle(rule_id):
        """Toggle rule active status."""
        db = get_db()
        try:
            rule = db.execute('SELECT is_active FROM wms_putaway_rules WHERE id = ?', (rule_id,)).fetchone()
            if rule:
                new_status = 0 if rule['is_active'] else 1
                db.execute('UPDATE wms_putaway_rules SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                          (new_status, rule_id))
                db.commit()
                log_wms_audit('TOGGLE', 'PUTAWAY_RULE', rule_id)
                flash(f'Rule {"activated" if new_status else "deactivated"} successfully!', 'success')
        except Exception as e:
            import traceback
            print(f"WMS putaway rule toggle error: {e}")
            traceback.print_exc()
            db.rollback()
            flash('Error toggling rule. Please try again.', 'error')
        return redirect(url_for('wms_putaway_rules'))

    @app.route('/wms/putaway/calculate-suggestion', methods=['POST'])
    @wms_permission_required('putaway', 'view')
    def wms_putaway_calculate_suggestion():
        """Calculate optimal putaway location for an item."""
        db = get_db()
        import time
        start_time = time.time()

        item_id = request.form.get('item_id')
        quantity = float(request.form.get('quantity', 0))
        warehouse_id = request.form.get('warehouse_id')

        if not item_id:
            return jsonify({'success': False, 'error': 'Item is required'})

        item = db.execute('SELECT * FROM wms_items WHERE id = ?', (item_id,)).fetchone()
        if not item:
            return jsonify({'success': False, 'error': 'Item not found'})

        rules = db.execute('''
            SELECT * FROM wms_putaway_rules
            WHERE is_active = 1 AND target_warehouse_id = ?
            ORDER BY priority DESC
        ''', (warehouse_id,)).fetchall()

        suggested_location = None
        rule_applied = None

        for rule in rules:
            conditions = json.loads(rule['conditions_json'] or '{}')

            if rule['action_type'] == 'ZONE':
                if rule['target_zone_id']:
                    zone = db.execute('SELECT * FROM wms_zones WHERE id = ?', (rule['target_zone_id'],)).fetchone()
                    if zone and zone['putaway_enabled']:
                        locations = db.execute('''
                            SELECT * FROM wms_locations
                            WHERE zone_id = ? AND is_active = 1 AND is_empty = 0
                            ORDER BY code LIMIT 10
                        ''', (rule['target_zone_id'],)).fetchall()
                        if locations:
                            suggested_location = locations[0]
                            rule_applied = rule
                            break

            elif rule['action_type'] == 'NEAREST':
                locations = db.execute('''
                    SELECT * FROM wms_locations
                    WHERE warehouse_id = ? AND is_active = 1 AND is_empty = 0
                    ORDER BY code LIMIT 20
                ''', (warehouse_id,)).fetchall()
                if locations:
                    suggested_location = locations[0]
                    rule_applied = rule
                    break

            elif rule['action_type'] == 'CONSOLIDATE':
                locations = db.execute('''
                    SELECT * FROM wms_locations
                    WHERE warehouse_id = ? AND is_active = 1 AND is_empty = 0
                    AND current_item_id = ?
                    ORDER BY code LIMIT 5
                ''', (warehouse_id, item_id)).fetchall()
                if locations:
                    suggested_location = locations[0]
                    rule_applied = rule
                    break

        decision_time_ms = int((time.time() - start_time) * 1000)

        if suggested_location:
            log_wms_audit('SUGGEST', 'PUTAWAY_LOCATION', suggested_location['id'])
            return jsonify({
                'success': True,
                'location_id': suggested_location['id'],
                'location_code': suggested_location['code'],
                'zone_name': db.execute('SELECT name FROM wms_zones WHERE id = ?',
                    (suggested_location['zone_id'],)).fetchone()['name'] if suggested_location['zone_id'] else None,
                'rule_applied': rule_applied['rule_name'] if rule_applied else None,
                'decision_time_ms': decision_time_ms
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No suitable location found',
                'decision_time_ms': decision_time_ms
            })

    # ============================================================
    # INTERNAL MOVEMENTS
    # ============================================================

    @app.route('/wms/movements')
    @wms_permission_required('movements', 'view')
    def wms_movements():
        """Internal movements list."""

        db = get_db()
        movement_type = request.args.get('movement_type', '')
        warehouse_id = request.args.get('warehouse_id', '')
        search = request.args.get('search', '').strip()
        page = int(request.args.get('page', 1))
        per_page = 50

        query = '''
            SELECT m.*, i.item_code, i.name as item_name,
                   w.name as warehouse_name,
                   sl.code as source_location, NULL as dest_location,
                   u.username
            FROM wms_internal_movements m
            JOIN wms_items i ON i.id = m.item_id
            JOIN wms_warehouses w ON w.id = m.warehouse_id
            LEFT JOIN wms_locations sl ON sl.id = m.source_location_id
            LEFT JOIN wms_locations dl ON dl.id = m.destination_location_id
            LEFT JOIN users u ON u.id = m.created_by
            WHERE 1=1
        '''
        params = []
        if movement_type:
            query += " AND m.movement_type = ?"
            params.append(movement_type)
        if warehouse_id:
            query += " AND m.warehouse_id = ?"
            params.append(warehouse_id)
        if search:
            query += " AND (i.item_code LIKE ? OR i.name LIKE ?)"
            params.append(f'%{search}%')

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY m.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        movements = db.execute(query, params).fetchall()

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'Internal Movements'
        return render_template('wms/movements.html',
            title=title,
            movements=movements,
            warehouses=warehouses,
            movement_type=movement_type,
            warehouse_id=warehouse_id,
            search=search,
            page=page,
            per_page=per_page,
            total_count=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1
        )

    @app.route('/wms/movements/new', methods=['GET', 'POST'])
    @wms_permission_required('movements', 'create')
    def wms_movements_new():
        """Create new internal movement."""
        db = get_db()

        if request.method == 'POST':
            data = request.form
            try:
                item_id = data.get('item_id')
                source_location_id = data.get('source_location_id')
                dest_location_id = data.get('destination_location_id')
                quantity = float(data.get('quantity', 0))

                # Check available stock
                available = db.execute('''
                    SELECT COALESCE(SUM(quantity), 0) as qty FROM wms_inventory_balances
                    WHERE item_id = ? AND location_id = ? AND status = 'AVAILABLE'
                ''', (item_id, source_location_id)).fetchone()['qty']

                if available < quantity:
                    flash(f'Insufficient stock. Available: {available}', 'error')
                    return redirect(url_for('wms_movements_new'))

                warehouse_id = db.execute(
                    'SELECT warehouse_id FROM wms_locations WHERE id = ?', (source_location_id,)).fetchone()['warehouse_id']
                movement_number = generate_wms_code('ADJ')

                # Deduct from source
                db.execute('''
                    UPDATE wms_inventory_balances SET
                        quantity = quantity - ?,
                        last_movement_date = datetime('now'),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE item_id = ? AND location_id = ? AND status = 'AVAILABLE'
                ''', (quantity, item_id, source_location_id))

                # Add to destination
                existing = db.execute('''
                    SELECT id FROM wms_inventory_balances
                    WHERE item_id = ? AND location_id = ? AND status = 'AVAILABLE'
                ''', (item_id, dest_location_id)).fetchone()
                if existing:
                    db.execute('''
                        UPDATE wms_inventory_balances SET
                            quantity = quantity + ?,
                            last_movement_date = datetime('now'),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (quantity, existing['id']))
                else:
                    db.execute('''
                        INSERT INTO wms_inventory_balances
                        (item_id, warehouse_id, location_id, quantity, status, last_movement_date)
                        VALUES (?, ?, ?, ?, 'AVAILABLE', datetime('now'))
                    ''', (item_id, warehouse_id, dest_location_id, quantity))

                # Record movement
                db.execute('''
                    INSERT INTO wms_internal_movements (
                        movement_number, movement_type, item_id,
                        source_location_id, destination_location_id,
                        quantity, reason_code, status, notes, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (movement_number, data.get('movement_type', 'TRANSFER'),
                      item_id, source_location_id, dest_location_id,
                      quantity, data.get('reason_code'), 'COMPLETED',
                      data.get('notes'), session.get('user_id')))

                # Record ledger
                db.execute('''
                    INSERT INTO wms_inventory_ledger (
                        transaction_type, transaction_number, reference_type,
                        item_id, warehouse_id, location_id,
                        quantity_before, quantity_moved, quantity_after,
                        status_before, status_after, reason_code, notes, user_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', ('MOVE', movement_number, 'INTERNAL_MOVE',
                      item_id, warehouse_id, source_location_id,
                      available, -quantity, available - quantity,
                      'AVAILABLE', 'AVAILABLE', data.get('reason_code'),
                      data.get('notes'), session.get('user_id')))

                db.execute('''
                    INSERT INTO wms_inventory_ledger (
                        transaction_type, transaction_number, reference_type,
                        item_id, warehouse_id, location_id,
                        quantity_before, quantity_moved, quantity_after,
                        status_before, status_after, reason_code, notes, user_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', ('MOVE', movement_number, 'INTERNAL_MOVE',
                      item_id, warehouse_id, dest_location_id,
                      0, quantity, quantity,
                      None, 'AVAILABLE', data.get('reason_code'),
                      data.get('notes'), session.get('user_id')))

                db.commit()
                log_wms_audit('CREATE', 'INTERNAL_MOVEMENT', None, {'movement_number': movement_number})
                flash(f'Movement {movement_number} created successfully!', 'success')
                return redirect(url_for('wms_movements'))
            except Exception as e:
                import traceback
                print(f"WMS movement create error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error creating movement. Please try again.', 'error')

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        items = db.execute('SELECT * FROM wms_items WHERE is_active = 1 ORDER BY name LIMIT 200').fetchall()
        reason_codes = db.execute("SELECT * FROM wms_reason_codes WHERE reason_type IN ('transfer', 'movement') AND is_active = 1").fetchall()

        title = 'New Internal Movement'
        return render_template('wms/movement_form.html',
            title=title,
            movement=None,
            warehouses=warehouses,
            items=items,
            reason_codes=reason_codes,
            form_action=url_for('wms_movements_new')
        )

    # ============================================================
    # REPLENISHMENT
    # ============================================================

    @app.route('/wms/replenishment')
    @wms_permission_required('replenishment', 'view')
    def wms_replenishment():
        """Replenishment tasks."""

        db = get_db()
        status = request.args.get('status', '')
        warehouse_id = request.args.get('warehouse_id', '')
        page = int(request.args.get('page', 1))
        per_page = 50

        query = '''
            SELECT r.*, i.item_code, i.name as item_name,
                   w.name as warehouse_name,
                   sl.code as source_location, dl.code as dest_location,
                   u.username as assigned_to_name
            FROM wms_replenishment_tasks r
            JOIN wms_items i ON i.id = r.item_id
            JOIN wms_warehouses w ON w.id = r.warehouse_id
            LEFT JOIN wms_locations sl ON sl.id = r.source_location_id
            LEFT JOIN wms_locations dl ON dl.id = r.destination_location_id
            LEFT JOIN users u ON u.id = r.assigned_to
            WHERE 1=1
        '''
        params = []
        if status:
            query += " AND r.status = ?"
            params.append(status)
        if warehouse_id:
            query += " AND r.warehouse_id = ?"
            params.append(warehouse_id)

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY r.priority DESC, r.created_at LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        tasks = db.execute(query, params).fetchall()

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'Replenishment'
        return render_template('wms/replenishment.html',
            title=title,
            tasks=tasks,
            warehouses=warehouses,
            status=status,
            warehouse_id=warehouse_id,
            page=page,
            per_page=per_page,
            total_count=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1
        )

    @app.route('/wms/replenishment/config')
    @wms_permission_required('replenishment', 'view')
    def wms_replenishment_config():
        """Replenishment configuration - min/max settings."""
        db = get_db()
        warehouse_id = request.args.get('warehouse_id', '')

        query = '''
            SELECT c.*, i.item_code, i.name as item_name, w.name as warehouse_name
            FROM wms_replenishment_config c
            JOIN wms_items i ON i.id = c.item_id
            JOIN wms_warehouses w ON w.id = c.warehouse_id
            WHERE 1=1
        '''
        params = []
        if warehouse_id:
            query += " AND c.warehouse_id = ?"
            params.append(warehouse_id)

        configs = db.execute(query, params).fetchall()
        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        items = db.execute('SELECT * FROM wms_items WHERE is_active = 1 ORDER BY item_code LIMIT 100').fetchall()

        title = 'Replenishment Config'
        return render_template('wms/replenishment_config.html',
            title=title,
            configs=configs,
            warehouses=warehouses,
            items=items,
            warehouse_id=warehouse_id
        )

    @app.route('/wms/replenishment/config/new', methods=['GET', 'POST'])
    @wms_permission_required('replenishment', 'create')
    def wms_replenishment_config_new():
        """Create replenishment configuration."""
        db = get_db()

        if request.method == 'POST':
            try:
                item_id = request.form.get('item_id')
                warehouse_id = request.form.get('warehouse_id')
                min_quantity = float(request.form.get('min_quantity', 0))
                max_quantity = float(request.form.get('max_quantity', 0))
                reorder_point = float(request.form.get('reorder_point', 0))
                reorder_quantity = float(request.form.get('reorder_quantity', 0))
                safety_stock = float(request.form.get('safety_stock', 0))
                lead_time_days = int(request.form.get('lead_time_days', 7))
                replenishment_method = request.form.get('replenishment_method', 'MIN_MAX')

                db.execute('''
                    INSERT INTO wms_replenishment_config
                    (item_id, warehouse_id, min_quantity, max_quantity, reorder_point,
                     reorder_quantity, safety_stock, lead_time_days, replenishment_method)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (item_id, warehouse_id, min_quantity, max_quantity, reorder_point,
                      reorder_quantity, safety_stock, lead_time_days, replenishment_method))
                db.commit()
                flash('Replenishment configuration created!', 'success')
                return redirect(url_for('wms_replenishment_config'))
            except Exception as e:
                import traceback
                print(f"WMS replenishment config create error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error creating replenishment config. Please try again.', 'error')

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        items = db.execute('SELECT * FROM wms_items WHERE is_active = 1 ORDER BY item_code').fetchall()
        title = 'New Replenishment Config'
        return render_template('wms/replenishment_config_form.html',
            title=title, config=None, warehouses=warehouses, items=items
        )

    @app.route('/wms/replenishment/calculate-suggestions', methods=['POST'])
    @wms_permission_required('replenishment', 'view')
    def wms_replenishment_calculate_suggestions():
        """Calculate replenishment suggestions based on min/max."""
        db = get_db()

        suggestions = []
        configs = db.execute('''
            SELECT c.*, i.item_code, i.name as item_name,
                   COALESCE((SELECT SUM(quantity) FROM wms_inventory_balances b WHERE b.item_id = c.item_id AND b.warehouse_id = c.warehouse_id), 0) as current_stock
            FROM wms_replenishment_config c
            JOIN wms_items i ON i.id = c.item_id
            WHERE c.is_active = 1
        ''').fetchall()

        for cfg in configs:
            if cfg['current_stock'] <= cfg['reorder_point']:
                suggested_qty = cfg['max_quantity'] - cfg['current_stock']
                if suggested_qty > 0:
                    suggestions.append({
                        'item_id': cfg['item_id'],
                        'item_code': cfg['item_code'],
                        'item_name': cfg['item_name'],
                        'current_stock': cfg['current_stock'],
                        'reorder_point': cfg['reorder_point'],
                        'suggested_quantity': suggested_qty,
                        'urgency': 'HIGH' if cfg['current_stock'] < cfg['safety_stock'] else 'NORMAL'
                    })

                    db.execute('''
                        INSERT INTO wms_replenishment_suggestions
                        (item_id, warehouse_id, suggested_quantity, reason_code, urgency, status)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (cfg['item_id'], cfg['warehouse_id'], suggested_qty, 'BELOW_REORDER', 'HIGH' if cfg['current_stock'] < cfg['safety_stock'] else 'NORMAL', 'PENDING'))

        db.commit()
        return jsonify({'success': True, 'suggestions': suggestions, 'count': len(suggestions)})

    @app.route('/wms/replenishment/suggestions')
    @wms_permission_required('replenishment', 'view')
    def wms_replenishment_suggestions():
        """View replenishment suggestions."""
        db = get_db()
        status = request.args.get('status', 'PENDING')

        suggestions = db.execute('''
            SELECT s.*, i.item_code, i.name as item_name, w.name as warehouse_name
            FROM wms_replenishment_suggestions s
            JOIN wms_items i ON i.id = s.item_id
            JOIN wms_warehouses w ON w.id = s.warehouse_id
            WHERE s.status = ?
            ORDER BY s.urgency DESC, s.created_at DESC
        ''', (status,)).fetchall()

        title = 'Replenishment Suggestions'
        return render_template('wms/replenishment_suggestions.html',
            title=title, suggestions=suggestions, status=status
        )

    @app.route('/wms/replenishment/kanban')
    @wms_permission_required('replenishment', 'view')
    def wms_replenishment_kanban():
        """Kanban board for replenishment."""
        db = get_db()

        kanban_cards = db.execute('''
            SELECT k.*, i.item_code, i.name as item_name,
                   sl.code as source_code, dl.code as dest_code
            FROM wms_kanban_config k
            JOIN wms_items i ON i.id = k.item_id
            JOIN wms_locations sl ON sl.id = k.source_location_id
            JOIN wms_locations dl ON dl.id = k.destination_location_id
            WHERE k.is_active = 1
            ORDER BY k.item_id
        ''').fetchall()

        title = 'Kanban Replenishment'
        return render_template('wms/replenishment_kanban.html',
            title=title, kanban_cards=kanban_cards
        )

    # ============================================================
    # PICKING
    # ============================================================

    @app.route('/wms/picking')
    @wms_permission_required('picking', 'view')
    def wms_picking():
        """Pick tasks."""

        db = get_db()
        status = request.args.get('status', '')
        warehouse_id = request.args.get('warehouse_id', '')
        page = int(request.args.get('page', 1))
        per_page = 50

        query = '''
            SELECT p.*, i.item_code, i.name as item_name,
                   w.name as warehouse_name,
                   l.code as source_location,
                   u.username as assigned_to_name,
                   o.order_number
            FROM wms_pick_tasks p
            JOIN wms_items i ON i.id = p.item_id
            LEFT JOIN wms_locations l ON l.id = p.source_location_id
            JOIN wms_warehouses w ON w.id = l.warehouse_id
            LEFT JOIN users u ON u.id = p.assigned_to
            LEFT JOIN wms_outbound_orders o ON o.id = p.order_id
            WHERE 1=1
        '''
        params = []
        if status:
            query += " AND p.status = ?"
            params.append(status)
        if warehouse_id:
            query += " AND l.warehouse_id = ?"
            params.append(warehouse_id)

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY p.priority DESC, p.created_at LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        tasks = db.execute(query, params).fetchall()

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'Picking'
        return render_template('wms/picking.html',
            title=title,
            tasks=tasks,
            warehouses=warehouses,
            status=status,
            warehouse_id=warehouse_id,
            page=page,
            per_page=per_page,
            total_count=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1
        )

    @app.route('/wms/picking/<int:task_id>/start', methods=['POST'])
    @wms_permission_required('picking', 'edit')
    @wms_csrf_required
    def wms_picking_start(task_id):
        db = get_db()
        task = db.execute('''
            SELECT p.*, l.warehouse_id
            FROM wms_pick_tasks p
            JOIN wms_locations l ON l.id = p.source_location_id
            WHERE p.id = ?
        ''', (task_id,)).fetchone()
        if not task:
            flash('Pick task not found.', 'error')
            return redirect(url_for('wms_picking'))
        if not ensure_warehouse_allowed(task['warehouse_id']):
            flash('You do not have access to this warehouse.', 'error')
            return redirect(url_for('wms_picking'))
        held = db.execute('''
            SELECT COALESCE(SUM(quantity_held), 0) as qty
            FROM wms_quality_holds
            WHERE status = 'ACTIVE' AND item_id = ? AND warehouse_id = ?
              AND (? IS NULL OR location_id = ?)
              AND (? IS NULL OR lot_id = ?)
        ''', (task['item_id'], task['warehouse_id'], task['source_location_id'], task['source_location_id'], task['lot_id'], task['lot_id'])).fetchone()['qty']
        if held and held >= task['quantity']:
            flash('This stock is on active quality hold and cannot be picked.', 'error')
            return redirect(url_for('wms_picking'))
        db.execute('UPDATE wms_pick_tasks SET status = "IN_PROGRESS", assigned_to = COALESCE(assigned_to, ?), started_at = COALESCE(started_at, datetime("now")), updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                   (session.get('user_id'), task_id))
        db.commit()
        log_wms_audit('START', 'PICK_TASK', task_id)
        flash('Pick task started.', 'success')
        return redirect(url_for('wms_picking'))

    @app.route('/wms/picking/<int:task_id>/complete', methods=['POST'])
    @wms_permission_required('picking', 'edit')
    @wms_csrf_required
    def wms_picking_complete(task_id):
        db = get_db()
        task = db.execute('''
            SELECT p.*, l.warehouse_id
            FROM wms_pick_tasks p
            JOIN wms_locations l ON l.id = p.source_location_id
            WHERE p.id = ?
        ''', (task_id,)).fetchone()
        if not task:
            flash('Pick task not found.', 'error')
            return redirect(url_for('wms_picking'))
        picked_qty = request.form.get('picked_quantity', type=float, default=task['quantity'])
        short_reason = request.form.get('short_pick_reason', '').strip()
        if picked_qty < 0 or picked_qty > task['quantity']:
            flash('Picked quantity must be between zero and the task quantity.', 'error')
            return redirect(url_for('wms_picking'))
        status = 'COMPLETED' if picked_qty >= task['quantity'] else 'SHORT_PICK'
        if status == 'SHORT_PICK' and not short_reason:
            flash('Short pick reason is required for partial picks.', 'error')
            return redirect(url_for('wms_picking'))
        db.execute('''
            UPDATE wms_pick_tasks
            SET picked_quantity = ?, status = ?, short_pick_reason = ?, completed_at = datetime('now'),
                completed_by = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (picked_qty, status, short_reason or None, session.get('user_id'), task_id))
        db.commit()
        log_wms_audit('COMPLETE', 'PICK_TASK', task_id, {'picked_quantity': picked_qty, 'short_pick_reason': short_reason})
        flash('Pick task updated.', 'success')
        return redirect(url_for('wms_picking'))

    # ============================================================
    # PACKING
    # ============================================================

    @app.route('/wms/packing')
    @wms_permission_required('packing', 'view')
    def wms_packing():
        """Pack tasks."""

        db = get_db()
        status = request.args.get('status', '')
        warehouse_id = request.args.get('warehouse_id', '')
        page = int(request.args.get('page', 1))
        per_page = 50

        query = '''
            SELECT p.*, o.order_number, o.customer_id,
                   w.name as warehouse_name,
                   u.username as assigned_to_name
            FROM wms_pack_tasks p
            JOIN wms_outbound_orders o ON o.id = p.order_id
            JOIN wms_warehouses w ON w.id = o.warehouse_id
            LEFT JOIN users u ON u.id = p.assigned_to
            WHERE 1=1
        '''
        params = []
        if status:
            query += " AND p.status = ?"
            params.append(status)
        if warehouse_id:
            query += " AND o.warehouse_id = ?"
            params.append(warehouse_id)

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY p.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        tasks = db.execute(query, params).fetchall()

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'Packing'
        return render_template('wms/packing.html',
            title=title,
            tasks=tasks,
            warehouses=warehouses,
            status=status,
            warehouse_id=warehouse_id,
            page=page,
            per_page=per_page,
            total_count=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1
        )

    @app.route('/wms/packing/<int:task_id>/complete', methods=['POST'])
    @wms_permission_required('packing', 'edit')
    @wms_csrf_required
    def wms_packing_complete(task_id):
        db = get_db()
        task = db.execute('SELECT * FROM wms_pack_tasks WHERE id = ?', (task_id,)).fetchone()
        if not task:
            flash('Pack task not found.', 'error')
            return redirect(url_for('wms_packing'))
        carton_count = request.form.get('carton_count', type=int, default=task['carton_count'] or 1)
        if carton_count <= 0:
            flash('Carton count must be positive.', 'error')
            return redirect(url_for('wms_packing'))
        db.execute('''
            UPDATE wms_pack_tasks
            SET carton_count = ?, packed_weight_kg = ?, packing_material = ?,
                status = 'COMPLETED', completed_at = datetime('now'), completed_by = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (carton_count, request.form.get('packed_weight_kg') or None, request.form.get('packing_material') or None, session.get('user_id'), task_id))
        db.commit()
        log_wms_audit('COMPLETE', 'PACK_TASK', task_id, {'carton_count': carton_count})
        flash('Pack task completed.', 'success')
        return redirect(url_for('wms_packing'))

    # ============================================================
    # DISPATCH / SHIPPING
    # ============================================================

    @app.route('/wms/dispatch')
    @wms_permission_required('dispatch', 'view')
    def wms_dispatch():
        """Dispatch/Shipping."""

        db = get_db()
        status = request.args.get('status', '')
        warehouse_id = request.args.get('warehouse_id', '')
        page = int(request.args.get('page', 1))
        per_page = 50

        query = '''
            SELECT s.*, o.order_number, o.customer_id,
                   w.name as warehouse_name
            FROM wms_shipments s
            LEFT JOIN wms_outbound_orders o ON o.id = s.order_id
            JOIN wms_warehouses w ON w.id = s.warehouse_id
            WHERE 1=1
        '''
        params = []
        if status:
            query += " AND s.status = ?"
            params.append(status)
        if warehouse_id:
            query += " AND s.warehouse_id = ?"
            params.append(warehouse_id)

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY s.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        shipments = db.execute(query, params).fetchall()

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'Dispatch / Shipping'
        return render_template('wms/dispatch.html',
            title=title,
            shipments=shipments,
            warehouses=warehouses,
            status=status,
            warehouse_id=warehouse_id,
            page=page,
            per_page=per_page,
            total_count=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1
        )

    @app.route('/wms/dispatch/<int:shipment_id>/gate-out', methods=['POST'])
    @wms_permission_required('dispatch', 'edit')
    @wms_csrf_required
    def wms_dispatch_gate_out(shipment_id):
        db = get_db()
        shipment = db.execute('SELECT * FROM wms_shipments WHERE id = ?', (shipment_id,)).fetchone()
        if not shipment:
            flash('Shipment not found.', 'error')
            return redirect(url_for('wms_dispatch'))
        if not ensure_warehouse_allowed(shipment['warehouse_id']):
            flash('You do not have access to this warehouse.', 'error')
            return redirect(url_for('wms_dispatch'))
        db.execute('''
            UPDATE wms_shipments
            SET status = 'DISPATCHED', departure_date = COALESCE(departure_date, datetime('now')),
                carrier_name = COALESCE(NULLIF(?, ''), carrier_name),
                tracking_number = COALESCE(NULLIF(?, ''), tracking_number),
                driver_name = COALESCE(NULLIF(?, ''), driver_name),
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (request.form.get('carrier_name', ''), request.form.get('tracking_number', ''), request.form.get('driver_name', ''), shipment_id))
        db.commit()
        log_wms_audit('GATE_OUT', 'SHIPMENT', shipment_id)
        flash('Shipment dispatched.', 'success')
        return redirect(url_for('wms_dispatch'))

    # ============================================================
    # TRANSFERS
    # ============================================================

    @app.route('/wms/transfers')
    @wms_permission_required('transfers', 'view')
    def wms_transfers():
        """Transfers list."""

        db = get_db()
        status = request.args.get('status', '')
        transfer_type = request.args.get('transfer_type', '')
        page = int(request.args.get('page', 1))
        per_page = 50

        query = '''
            SELECT t.*,
                   sw.name as source_warehouse_name,
                   dw.name as dest_warehouse_name,
                   u1.username as requested_by_name,
                   u2.username as approved_by_name
            FROM wms_transfers t
            JOIN wms_warehouses sw ON sw.id = t.source_warehouse_id
            JOIN wms_warehouses dw ON dw.id = t.destination_warehouse_id
            LEFT JOIN users u1 ON u1.id = t.requested_by
            LEFT JOIN users u2 ON u2.id = t.approved_by
            WHERE 1=1
        '''
        params = []
        if status:
            query += " AND t.status = ?"
            params.append(status)
        if transfer_type:
            query += " AND t.transfer_type = ?"
            params.append(transfer_type)

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY t.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        transfers = db.execute(query, params).fetchall()

        title = 'Transfers'
        return render_template('wms/transfers.html',
            title=title,
            transfers=transfers,
            status=status,
            transfer_type=transfer_type,
            page=page,
            per_page=per_page,
            total_count=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1
        )

    @app.route('/wms/transfers/new', methods=['GET', 'POST'])
    @wms_permission_required('transfers', 'create')
    def wms_transfers_new():
        """Create new transfer."""
        db = get_db()

        if request.method == 'POST':
            data = request.form
            try:
                transfer_number = generate_wms_code('TRANSFER')
                db.execute('''
                    INSERT INTO wms_transfers (
                        transfer_number, transfer_type,
                        source_warehouse_id, destination_warehouse_id,
                        source_company_id, destination_company_id,
                        status, priority, notes, requested_by, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    transfer_number,
                    data.get('transfer_type', 'WAREHOUSE_TO_WAREHOUSE'),
                    data.get('source_warehouse_id'),
                    data.get('destination_warehouse_id'),
                    data.get('source_company_id') or None,
                    data.get('destination_company_id') or None,
                    'REQUESTED',
                    data.get('priority', 5),
                    data.get('notes'),
                    session.get('user_id'),
                    session.get('user_id')
                ))
                db.commit()
                transfer_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
                log_wms_audit('CREATE', 'TRANSFER', transfer_id, {'transfer_number': transfer_number})
                flash(f'Transfer {transfer_number} created! Add line items.', 'success')
                return redirect(url_for('wms_transfer_detail', transfer_id=transfer_id))
            except Exception as e:
                import traceback
                print(f"WMS transfer create error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error creating transfer. Please try again.', 'error')

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        companies = db.execute('SELECT * FROM wms_companies WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'New Transfer'
        return render_template('wms/transfer_form.html',
            title=title,
            transfer=None,
            warehouses=warehouses,
            companies=companies,
            form_action=url_for('wms_transfers_new')
        )

    @app.route('/wms/transfers/<int:transfer_id>')
    @wms_permission_required('transfers', 'view')
    def wms_transfer_detail(transfer_id):
        """Transfer detail."""

        db = get_db()
        transfer = db.execute('''
            SELECT t.*,
                   sw.name as source_warehouse_name,
                   dw.name as dest_warehouse_name,
                   sc.name as source_company_name,
                   dc.name as dest_company_name
            FROM wms_transfers t
            JOIN wms_warehouses sw ON sw.id = t.source_warehouse_id
            JOIN wms_warehouses dw ON dw.id = t.destination_warehouse_id
            LEFT JOIN wms_companies sc ON sc.id = t.source_company_id
            LEFT JOIN wms_companies dc ON dc.id = t.destination_company_id
            WHERE t.id = ?
        ''', (transfer_id,)).fetchone()

        if not transfer:
            flash('Transfer not found.', 'error')
            return redirect(url_for('wms_transfers'))

        lines = db.execute('''
            SELECT tl.*, i.item_code, i.name as item_name,
                   sl.code as source_location, dl.code as dest_location
            FROM wms_transfer_lines tl
            JOIN wms_items i ON i.id = tl.item_id
            LEFT JOIN wms_locations sl ON sl.id = tl.source_location_id
            LEFT JOIN wms_locations dl ON dl.id = tl.destination_location_id
            WHERE tl.transfer_id = ?
        ''', (transfer_id,)).fetchall()

        title = f'Transfer: {transfer["transfer_number"]}'
        return render_template('wms/transfer_detail.html',
            title=title,
            transfer=transfer,
            lines=lines
        )

    # ============================================================
    # RETURNS
    # ============================================================

    @app.route('/wms/returns')
    @wms_permission_required('returns', 'view')
    def wms_returns():
        """Returns list."""

        db = get_db()
        status = request.args.get('status', '')
        return_type = request.args.get('return_type', '')
        page = int(request.args.get('page', 1))
        per_page = 50

        query = '''
            SELECT r.*, w.name as warehouse_name,
                   c.name as customer_name, s.name as supplier_name
            FROM wms_returns r
            JOIN wms_warehouses w ON w.id = r.warehouse_id
            LEFT JOIN customers c ON c.id = r.customer_id
            LEFT JOIN suppliers s ON s.id = r.supplier_id
            WHERE 1=1
        '''
        params = []
        if status:
            query += " AND r.status = ?"
            params.append(status)
        if return_type:
            query += " AND r.return_type = ?"
            params.append(return_type)

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY r.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        returns = db.execute(query, params).fetchall()

        title = 'Returns / Reverse Logistics'
        return render_template('wms/returns.html',
            title=title,
            returns_list=returns,
            status=status,
            return_type=return_type,
            page=page,
            per_page=per_page,
            total_count=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1
        )

    @app.route('/wms/returns/new', methods=['GET', 'POST'])
    @wms_permission_required('returns', 'create')
    def wms_returns_new():
        """Create new return."""
        db = get_db()

        if request.method == 'POST':
            data = request.form
            try:
                return_number = generate_wms_code('RETURN')
                db.execute('''
                    INSERT INTO wms_returns (
                        return_number, return_type, warehouse_id, company_id,
                        customer_id, supplier_id, original_order_number, rma_number,
                        reason_code, status, notes, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    return_number,
                    data.get('return_type', 'CUSTOMER_RETURN'),
                    data.get('warehouse_id'),
                    data.get('company_id') or None,
                    data.get('customer_id') or None,
                    data.get('supplier_id') or None,
                    data.get('original_order_number'),
                    data.get('rma_number'),
                    data.get('reason_code'),
                    'REQUESTED',
                    data.get('notes'),
                    session.get('user_id')
                ))
                db.commit()
                return_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
                log_wms_audit('CREATE', 'RETURN', return_id, {'return_number': return_number})
                flash(f'Return {return_number} created!', 'success')
                return redirect(url_for('wms_return_detail', return_id=return_id))
            except Exception as e:
                import traceback
                print(f"WMS return create error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error creating return. Please try again.', 'error')

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        customers = db.execute('SELECT * FROM customers ORDER BY name LIMIT 200').fetchall()
        suppliers = db.execute('SELECT * FROM suppliers ORDER BY name LIMIT 200').fetchall()
        companies = db.execute('SELECT * FROM wms_companies WHERE is_active = 1 ORDER BY name').fetchall()
        reason_codes = db.execute("SELECT * FROM wms_reason_codes WHERE reason_type IN ('return', 'return_defect', 'return_damage') AND is_active = 1").fetchall()

        title = 'New Return'
        return render_template('wms/return_form.html',
            title=title,
            return_rec=None,
            warehouses=warehouses,
            customers=customers,
            suppliers=suppliers,
            companies=companies,
            reason_codes=reason_codes,
            form_action=url_for('wms_returns_new')
        )

    @app.route('/wms/returns/<int:return_id>')
    @wms_permission_required('returns', 'view')
    def wms_return_detail(return_id):
        """Return detail."""

        db = get_db()
        return_rec = db.execute('''
            SELECT r.*, w.name as warehouse_name,
                   c.name as customer_name, s.name as supplier_name
            FROM wms_returns r
            JOIN wms_warehouses w ON w.id = r.warehouse_id
            LEFT JOIN customers c ON c.id = r.customer_id
            LEFT JOIN suppliers s ON s.id = r.supplier_id
            WHERE r.id = ?
        ''', (return_id,)).fetchone()

        if not return_rec:
            flash('Return not found.', 'error')
            return redirect(url_for('wms_returns'))

        lines = db.execute('''
            SELECT rl.*, i.item_code, i.name as item_name
            FROM wms_return_lines rl
            JOIN wms_items i ON i.id = rl.item_id
            WHERE rl.return_id = ?
        ''', (return_id,)).fetchall()

        title = f'Return: {return_rec["return_number"]}'
        return render_template('wms/return_detail.html',
            title=title,
            return_rec=return_rec,
            lines=lines
        )

    # ============================================================
    # STOCK COUNTING
    # ============================================================

    @app.route('/wms/stock-counts')
    @wms_permission_required('stock_counts', 'view')
    def wms_stock_counts():
        """Stock counts list."""

        db = get_db()
        status = request.args.get('status', '')
        count_type = request.args.get('count_type', '')
        page = int(request.args.get('page', 1))
        per_page = 50

        query = '''
            SELECT c.*, w.name as warehouse_name, u.username as created_by_name
            FROM wms_stock_counts c
            JOIN wms_warehouses w ON w.id = c.warehouse_id
            LEFT JOIN users u ON u.id = c.created_by
            WHERE 1=1
        '''
        params = []
        if status:
            query += " AND c.status = ?"
            params.append(status)
        if count_type:
            query += " AND c.count_type = ?"
            params.append(count_type)

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY c.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        counts = db.execute(query, params).fetchall()

        title = 'Stock Counting / Inventory Control'
        return render_template('wms/stock_counts.html',
            title=title,
            counts=counts,
            status=status,
            count_type=count_type,
            page=page,
            per_page=per_page,
            total_count=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1
        )

    @app.route('/wms/stock-counts/new', methods=['GET', 'POST'])
    @wms_permission_required('stock_counts', 'create')
    def wms_stock_counts_new():
        """Create new stock count."""
        db = get_db()

        if request.method == 'POST':
            data = request.form
            try:
                count_number = generate_wms_code('COUNT')
                db.execute('''
                    INSERT INTO wms_stock_counts (
                        count_number, count_type, warehouse_id, company_id,
                        location_id, category_id, count_method, is_blind_count,
                        scheduled_date, status, notes, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    count_number,
                    data.get('count_type', 'CYCLE_COUNT'),
                    data.get('warehouse_id'),
                    data.get('company_id') or None,
                    data.get('location_id') or None,
                    data.get('category_id') or None,
                    data.get('count_method', 'MANUAL'),
                    1 if data.get('is_blind_count') else 0,
                    data.get('scheduled_date'),
                    'DRAFT',
                    data.get('notes'),
                    session.get('user_id')
                ))
                db.commit()
                count_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
                log_wms_audit('CREATE', 'STOCK_COUNT', count_id, {'count_number': count_number})
                flash(f'Stock count {count_number} created!', 'success')
                return redirect(url_for('wms_stock_count_detail', count_id=count_id))
            except Exception as e:
                import traceback
                print(f"WMS stock count create error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error creating stock count. Please try again.', 'error')

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        categories = db.execute('SELECT * FROM wms_item_categories WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'New Stock Count'
        return render_template('wms/stock_count_form.html',
            title=title,
            count_rec=None,
            warehouses=warehouses,
            categories=categories,
            form_action=url_for('wms_stock_counts_new')
        )

    @app.route('/wms/stock-counts/<int:count_id>')
    @wms_permission_required('stock_counts', 'view')
    def wms_stock_count_detail(count_id):
        """Stock count detail."""

        db = get_db()
        count_rec = db.execute('''
            SELECT c.*, w.name as warehouse_name, u.username as created_by_name
            FROM wms_stock_counts c
            JOIN wms_warehouses w ON w.id = c.warehouse_id
            LEFT JOIN users u ON u.id = c.created_by
            WHERE c.id = ?
        ''', (count_id,)).fetchone()

        if not count_rec:
            flash('Stock count not found.', 'error')
            return redirect(url_for('wms_stock_counts'))

        lines = db.execute('''
            SELECT cl.*, i.item_code, i.name as item_name,
                   l.code as location_code, lot.lot_number
            FROM wms_stock_count_lines cl
            JOIN wms_items i ON i.id = cl.item_id
            LEFT JOIN wms_locations l ON l.id = cl.location_id
            LEFT JOIN wms_lots lot ON lot.id = cl.lot_id
            WHERE cl.count_id = ?
            ORDER BY cl.line_number
        ''', (count_id,)).fetchall()

        title = f'Stock Count: {count_rec["count_number"]}'
        return render_template('wms/stock_count_detail.html',
            title=title,
            count_rec=count_rec,
            lines=lines
        )

    # ============================================================
    # STOCK ADJUSTMENTS
    # ============================================================

    @app.route('/wms/adjustments')
    @wms_permission_required('adjustments', 'view')
    def wms_adjustments():
        """Stock adjustments."""

        db = get_db()
        status = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        per_page = 50

        query = '''
            SELECT a.*, w.name as warehouse_name, u.username as created_by_name
            FROM wms_stock_adjustments a
            JOIN wms_warehouses w ON w.id = a.warehouse_id
            LEFT JOIN users u ON u.id = a.created_by
            WHERE 1=1
        '''
        params = []
        if status:
            query += " AND a.status = ?"
            params.append(status)

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY a.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        adjustments = db.execute(query, params).fetchall()

        title = 'Stock Adjustments'
        return render_template('wms/adjustments.html',
            title=title,
            adjustments=adjustments,
            status=status,
            page=page,
            per_page=per_page,
            total_count=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1
        )

    @app.route('/wms/adjustments/new', methods=['GET', 'POST'])
    @wms_permission_required('adjustments', 'create')
    def wms_adjustments_new():
        """Create new stock adjustment."""
        db = get_db()

        if request.method == 'POST':
            data = request.form
            try:
                adjustment_number = generate_wms_code('ADJ')
                db.execute('''
                    INSERT INTO wms_stock_adjustments (
                        adjustment_number, warehouse_id, company_id,
                        adjustment_type, reason_code, status, notes, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    adjustment_number,
                    data.get('warehouse_id'),
                    data.get('company_id') or None,
                    data.get('adjustment_type', 'CORRECTION'),
                    data.get('reason_code'),
                    'DRAFT',
                    data.get('notes'),
                    session.get('user_id')
                ))
                db.commit()
                adj_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
                flash(f'Adjustment {adjustment_number} created!', 'success')
                return redirect(url_for('wms_adjustment_detail', adjustment_id=adj_id))
            except Exception as e:
                import traceback
                print(f"WMS adjustment create error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error creating adjustment. Please try again.', 'error')

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        reason_codes = db.execute("SELECT * FROM wms_reason_codes WHERE reason_type IN ('adjustment', 'count_var', 'correction') AND is_active = 1").fetchall()

        title = 'New Stock Adjustment'
        return render_template('wms/adjustment_form.html',
            title=title,
            adjustment=None,
            warehouses=warehouses,
            reason_codes=reason_codes,
            form_action=url_for('wms_adjustments_new')
        )

    @app.route('/wms/adjustments/<int:adjustment_id>')
    @wms_permission_required('adjustments', 'view')
    def wms_adjustment_detail(adjustment_id):
        """Adjustment detail."""

        db = get_db()
        adjustment = db.execute('''
            SELECT a.*, w.name as warehouse_name
            FROM wms_stock_adjustments a
            JOIN wms_warehouses w ON w.id = a.warehouse_id
            WHERE a.id = ?
        ''', (adjustment_id,)).fetchone()

        if not adjustment:
            flash('Adjustment not found.', 'error')
            return redirect(url_for('wms_adjustments'))

        lines = db.execute('''
            SELECT al.*, i.item_code, i.name as item_name, l.code as location_code
            FROM wms_stock_adjustment_lines al
            JOIN wms_items i ON i.id = al.item_id
            LEFT JOIN wms_locations l ON l.id = al.location_id
            WHERE al.adjustment_id = ?
        ''', (adjustment_id,)).fetchall()

        title = f'Adjustment: {adjustment["adjustment_number"]}'
        return render_template('wms/adjustment_detail.html',
            title=title,
            adjustment=adjustment,
            lines=lines
        )

    # ============================================================
    # QUALITY CONTROL / INSPECTIONS
    # ============================================================

    @app.route('/wms/quality')
    @wms_permission_required('quality', 'view')
    def wms_quality():
        """QC Inspections."""

        db = get_db()
        result = request.args.get('result', '')
        page = int(request.args.get('page', 1))
        per_page = 50

        query = '''
            SELECT q.*, w.name as warehouse_name, i.item_code, i.name as item_name,
                   u.username as inspected_by_name
            FROM wms_qc_inspections q
            JOIN wms_warehouses w ON w.id = q.warehouse_id
            JOIN wms_items i ON i.id = q.item_id
            LEFT JOIN users u ON u.id = q.inspected_by
            WHERE 1=1
        '''
        params = []
        if result:
            query += " AND q.result = ?"
            params.append(result)

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY q.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        inspections = db.execute(query, params).fetchall()

        title = 'Quality Control / Inspections'
        return render_template('wms/quality.html',
            title=title,
            inspections=inspections,
            result=result,
            page=page,
            per_page=per_page,
            total_count=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1
        )

    @app.route('/wms/quality/decisions')
    @wms_permission_required('quality', 'view')
    def wms_quality_decisions():
        """QC Usage Decisions."""
        db = get_db()
        decisions = db.execute('''
            SELECT d.*, i.item_code, i.name as item_name, u.username as decided_by_name
            FROM wms_usage_decisions d
            JOIN wms_items i ON i.id = d.item_id
            LEFT JOIN users u ON u.id = d.decided_by
            ORDER BY d.created_at DESC LIMIT 100
        ''').fetchall()
        title = 'Usage Decisions'
        return render_template('wms/quality_decisions.html', title=title, decisions=decisions)

    @app.route('/wms/quality/decisions/new', methods=['GET', 'POST'])
    @wms_permission_required('quality', 'create')
    def wms_quality_decisions_new():
        """Create usage decision."""
        db = get_db()
        if request.method == 'POST':
            decision_code = request.form.get('decision_code')
            item_id = request.form.get('item_id')
            quantity = float(request.form.get('quantity', 0))
            disposition = request.form.get('disposition')
            notes = request.form.get('notes')
            db.execute('''
                INSERT INTO wms_usage_decisions (decision_number, inspection_id, item_id, lot_id, decision_code, quantity, disposition, notes, decided_by, decided_at)
                SELECT ?, NULL, ?, NULL, ?, ?, ?, ?, ?, datetime('now')
            ''', (f'UD-{date.today().strftime("%Y%m%d")}-{random.randint(1000,9999)}', item_id, decision_code, quantity, disposition, notes, session.get('user_id')))
            db.commit()
            flash('Usage decision created!', 'success')
            return redirect(url_for('wms_quality_decisions'))
        items = db.execute('SELECT * FROM wms_items WHERE is_active = 1 ORDER BY item_code').fetchall()
        title = 'New Usage Decision'
        return render_template('wms/quality_decision_form.html', title=title, decision=None, items=items)

    @app.route('/wms/quality/defect-codes')
    @wms_permission_required('quality', 'view')
    def wms_quality_defect_codes():
        """QC Defect codes."""
        db = get_db()
        codes = db.execute('SELECT * FROM wms_defect_codes WHERE is_active = 1 ORDER BY code').fetchall()
        title = 'Defect Codes'
        return render_template('wms/quality_defect_codes.html', title=title, codes=codes)

    @app.route('/wms/quality/defect-codes/new', methods=['GET', 'POST'])
    @wms_permission_required('quality', 'create')
    def wms_quality_defect_codes_new():
        """Create defect code."""
        db = get_db()
        if request.method == 'POST':
            code = request.form.get('code')
            category = request.form.get('category')
            description = request.form.get('description')
            severity = request.form.get('severity')
            disposition = request.form.get('disposition')
            db.execute('INSERT INTO wms_defect_codes (code, category, description, severity, disposition) VALUES (?, ?, ?, ?, ?)',
                       (code, category, description, severity, disposition))
            db.commit()
            flash('Defect code created!', 'success')
            return redirect(url_for('wms_quality_defect_codes'))
        title = 'New Defect Code'
        return render_template('wms/quality_defect_code_form.html', title=title, code=None)

    @app.route('/wms/quality/certificates')
    @wms_permission_required('quality', 'view')
    def wms_quality_certificates():
        """Quality certificates (CoA)."""
        db = get_db()
        certs = db.execute('''
            SELECT c.*, i.item_code, i.name as item_name, u.username as issued_by_name
            FROM wms_quality_certificates c
            JOIN wms_items i ON i.id = c.item_id
            LEFT JOIN users u ON u.id = c.issued_by
            ORDER BY c.created_at DESC LIMIT 100
        ''').fetchall()
        title = 'Certificates of Analysis'
        return render_template('wms/quality_certificates.html', title=title, certificates=certs)

    @app.route('/wms/quality/capa')
    @wms_permission_required('quality', 'view')
    def wms_quality_capa():
        """QC CAPA (Corrective/Preventive Actions)."""
        db = get_db()
        capas = db.execute('''
            SELECT c.*, d.code as defect_code, d.category, u.username as responsible_name
            FROM wms_quality_capa c
            LEFT JOIN wms_defect_codes d ON d.id = c.defect_id
            LEFT JOIN users u ON u.id = c.responsible_id
            ORDER BY c.created_at DESC LIMIT 100
        ''').fetchall()
        title = 'CAPA Management'
        return render_template('wms/quality_capa.html', title=title, capas=capas)

    @app.route('/wms/quality/capa/new', methods=['GET', 'POST'])
    @wms_permission_required('quality', 'create')
    def wms_quality_capa_new():
        """Create CAPA."""
        db = get_db()
        if request.method == 'POST':
            root_cause = request.form.get('root_cause')
            corrective = request.form.get('corrective_action')
            preventive = request.form.get('preventive_action')
            priority = request.form.get('priority')
            db.execute('''
                INSERT INTO wms_quality_capa (capa_number, root_cause, corrective_action, preventive_action, priority, responsible_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (f'CAPA-{date.today().strftime("%Y%m%d")}-{random.randint(100,999)}', root_cause, corrective, preventive, priority, session.get('user_id'), 'OPEN'))
            db.commit()
            flash('CAPA created!', 'success')
            return redirect(url_for('wms_quality_capa'))
        defect_codes = db.execute('SELECT * FROM wms_defect_codes WHERE is_active = 1').fetchall()
        title = 'New CAPA'
        return render_template('wms/quality_capa_form.html', title=title, capa=None, defect_codes=defect_codes)

    @app.route('/wms/quality/aql-rules')
    @wms_permission_required('quality', 'view')
    def wms_quality_aql_rules():
        """AQL Sampling rules."""
        db = get_db()
        rules = db.execute('SELECT * FROM wms_aql_rules WHERE is_active = 1 ORDER BY lot_size_min').fetchall()
        title = 'AQL Sampling Rules'
        return render_template('wms/quality_aql_rules.html', title=title, rules=rules)

    @app.route('/wms/quality/aql-rules/new', methods=['GET', 'POST'])
    @wms_permission_required('quality', 'create')
    def wms_quality_aql_rules_new():
        """Create AQL rule."""
        db = get_db()
        if request.method == 'POST':
            try:
                rule_name = request.form.get('rule_name')
                inspection_level = request.form.get('inspection_level', 'II')
                aql_level = float(request.form.get('aql_level', 1.5))
                lot_size_min = int(request.form.get('lot_size_min', 1))
                lot_size_max = int(request.form.get('lot_size_max', 50000))

                db.execute('''
                    INSERT INTO wms_aql_rules (rule_name, inspection_level, aql_level, lot_size_min, lot_size_max)
                    VALUES (?, ?, ?, ?, ?)
                ''', (rule_name, inspection_level, aql_level, lot_size_min, lot_size_max))
                db.commit()
                flash('AQL Rule created!', 'success')
                return redirect(url_for('wms_quality_aql_rules'))
            except Exception as e:
                import traceback
                print(f"WMS AQL rule create error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error creating AQL rule. Please try again.', 'error')
        title = 'New AQL Rule'
        return render_template('wms/quality_aql_rule_form.html', title=title, rule=None)

    # ============================================================
    # QUALITY HOLDS
    # ============================================================

    @app.route('/wms/quality/holds')
    @wms_permission_required('quality', 'view')
    def wms_quality_holds():
        """Quality holds list."""
        db = get_db()
        ensure_quality_hold_tables()
        status = request.args.get('status', '')
        warehouse_id = request.args.get('warehouse_id', '')
        page = int(request.args.get('page', 1))
        per_page = 50

        query = '''
            SELECT h.*, w.name as warehouse_name,
                   i.item_code, i.name as item_name,
                   l.code as location_code,
                   u1.username as held_by_name,
                   u2.username as released_by_name
            FROM wms_quality_holds h
            JOIN wms_warehouses w ON w.id = h.warehouse_id
            JOIN wms_items i ON i.id = h.item_id
            LEFT JOIN wms_locations l ON l.id = h.location_id
            LEFT JOIN users u1 ON u1.id = h.held_by
            LEFT JOIN users u2 ON u2.id = h.released_by
            WHERE 1=1
        '''
        params = []
        if status:
            query += " AND h.status = ?"
            params.append(status)
        if warehouse_id:
            query += " AND h.warehouse_id = ?"
            params.append(warehouse_id)

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY h.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        holds = db.execute(query, params).fetchall()

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()

        # Stats for summary cards
        active_count = db.execute("SELECT COUNT(*) as cnt FROM wms_quality_holds WHERE status = 'ACTIVE'").fetchone()['cnt']
        released_count = db.execute("SELECT COUNT(*) as cnt FROM wms_quality_holds WHERE status = 'RELEASED'").fetchone()['cnt']
        total_qty = db.execute("SELECT COALESCE(SUM(quantity_held), 0) as qty FROM wms_quality_holds WHERE status = 'ACTIVE'").fetchone()['qty']

        title = 'Quality Holds'
        return render_template('wms/quality_holds.html',
            title=title, holds=holds, warehouses=warehouses,
            status=status, warehouse_id=warehouse_id,
            page=page, per_page=per_page,
            total_count=total, active_count=active_count,
            released_count=released_count, total_qty=total_qty,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1
        )

    @app.route('/wms/quality/holds/new', methods=['GET', 'POST'])
    @wms_permission_required('quality', 'create')
    @wms_csrf_required
    def wms_quality_holds_new():
        """Create quality hold."""
        db = get_db()
        ensure_quality_hold_tables()
        if request.method == 'POST':
            try:
                from secrets import token_hex
                hold_number = f'HOLD-{date.today().strftime("%Y%m%d")}-{token_hex(4).upper()}'
                item_id = request.form.get('item_id', type=int)
                lot_id = request.form.get('lot_id')
                location_id = request.form.get('location_id')
                quantity_held = request.form.get('quantity_held', type=float, default=0)
                hold_reason = request.form.get('hold_reason')
                hold_type = request.form.get('hold_type', 'INSPECTION')
                hold_notes = request.form.get('hold_notes')
                warehouse_id = request.form.get('warehouse_id', type=int)
                source_receipt_line_id = request.form.get('source_receipt_line_id')
                source_return_line_id = request.form.get('source_return_line_id')
                source_inspection_id = request.form.get('source_inspection_id')
                if not item_id or not warehouse_id or quantity_held <= 0 or not hold_reason:
                    flash('Item, warehouse, positive quantity, and hold reason are required.', 'error')
                    return redirect(url_for('wms_quality_holds_new'))
                if not ensure_warehouse_allowed(warehouse_id):
                    flash('You do not have access to this warehouse.', 'error')
                    return redirect(url_for('wms_quality_holds'))
                item = db.execute('SELECT id FROM wms_items WHERE id = ? AND is_active = 1', (item_id,)).fetchone()
                if not item:
                    flash('Selected item is invalid or inactive.', 'error')
                    return redirect(url_for('wms_quality_holds_new'))
                if location_id:
                    loc = db.execute('SELECT id, warehouse_id FROM wms_locations WHERE id = ? AND is_active = 1', (location_id,)).fetchone()
                    if not loc or loc['warehouse_id'] != warehouse_id:
                        flash('Hold location must be active and in the selected warehouse.', 'error')
                        return redirect(url_for('wms_quality_holds_new'))
                available_row = db.execute('''
                    SELECT COALESCE(SUM(quantity - reserved_quantity - allocated_quantity - blocked_quantity), 0) as available_qty
                    FROM wms_inventory_balances
                    WHERE item_id = ?
                      AND warehouse_id = ?
                      AND status = 'AVAILABLE'
                      AND (? IS NULL OR location_id = ?)
                      AND (? IS NULL OR lot_id = ?)
                ''', (item_id, warehouse_id, location_id, location_id, lot_id if lot_id else None, lot_id if lot_id else None)).fetchone()
                if (available_row['available_qty'] or 0) < quantity_held:
                    flash('Insufficient available stock for this quality hold.', 'error')
                    return redirect(url_for('wms_quality_holds_new'))

                db.execute('''
                    INSERT INTO wms_quality_holds
                    (hold_number, warehouse_id, item_id, lot_id, location_id,
                     quantity_held, hold_reason, hold_type, hold_notes,
                     held_by, source_receipt_line_id, source_return_line_id, source_inspection_id,
                     status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE')
                ''', (hold_number, warehouse_id, item_id,
                      lot_id if lot_id else None,
                      location_id if location_id else None,
                      quantity_held, hold_reason, hold_type, hold_notes,
                      session.get('user_id'),
                      source_receipt_line_id if source_receipt_line_id else None,
                      source_return_line_id if source_return_line_id else None,
                      source_inspection_id if source_inspection_id else None))
                db.execute('''
                    UPDATE wms_inventory_balances
                    SET blocked_quantity = blocked_quantity + ?,
                        status = CASE WHEN status = 'AVAILABLE' THEN 'QUARANTINE' ELSE status END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = (
                        SELECT id FROM wms_inventory_balances
                        WHERE item_id = ?
                          AND warehouse_id = ?
                          AND status = 'AVAILABLE'
                          AND (? IS NULL OR location_id = ?)
                          AND (? IS NULL OR lot_id = ?)
                        ORDER BY quantity DESC
                        LIMIT 1
                    )
                ''', (quantity_held, item_id, warehouse_id, location_id, location_id,
                      lot_id if lot_id else None, lot_id if lot_id else None))
                db.commit()

                log_wms_audit('CREATE', 'QUALITY_HOLD', hold_number, {
                    'warehouse_id': warehouse_id,
                    'item_id': item_id,
                    'lot_id': lot_id,
                    'location_id': location_id,
                    'quantity_held': quantity_held,
                    'hold_type': hold_type,
                    'hold_reason': hold_reason,
                })
                flash(f'Quality hold {hold_number} created!', 'success')
                return redirect(url_for('wms_quality_holds'))
            except Exception as e:
                import traceback
                print(f"WMS quality hold create error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error creating quality hold. Please try again.', 'error')

        items = db.execute('SELECT * FROM wms_items WHERE is_active = 1 ORDER BY item_code').fetchall()
        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        inspection_ids = db.execute('SELECT id, inspection_number FROM wms_qc_inspections WHERE result = "PENDING" ORDER BY created_at DESC').fetchall()

        title = 'New Quality Hold'
        return render_template('wms/quality_hold_form.html',
            title=title, hold=None, items=items, warehouses=warehouses,
            inspection_ids=inspection_ids,
            form_action=url_for('wms_quality_holds_new'))

    @app.route('/wms/quality/holds/<int:hold_id>')
    @wms_permission_required('quality', 'view')
    def wms_quality_hold_detail(hold_id):
        """Quality hold detail."""
        db = get_db()
        ensure_quality_hold_tables()
        hold = db.execute('''
            SELECT h.*, w.name as warehouse_name,
                   i.item_code, i.name as item_name,
                   l.code as location_code,
                   u1.username as held_by_name, u1.id as held_by_id,
                   u2.username as released_by_name, u2.id as released_by_id
            FROM wms_quality_holds h
            JOIN wms_warehouses w ON w.id = h.warehouse_id
            JOIN wms_items i ON i.id = h.item_id
            LEFT JOIN wms_locations l ON l.id = h.location_id
            LEFT JOIN users u1 ON u1.id = h.held_by
            LEFT JOIN users u2 ON u2.id = h.released_by
            WHERE h.id = ?
        ''', (hold_id,)).fetchone()

        if not hold:
            flash('Quality hold not found.', 'error')
            return redirect(url_for('wms_quality_holds'))

        audit_log = db.execute('''
            SELECT * FROM wms_audit_log
            WHERE entity_type = 'QUALITY_HOLD' AND entity_id = ?
            ORDER BY created_at DESC
        ''', (hold['hold_number'],)).fetchall()

        title = f'Quality Hold: {hold["hold_number"]}'
        return render_template('wms/quality_hold_detail.html',
            title=title, hold=hold, audit_log=audit_log)

    @app.route('/wms/quality/holds/<int:hold_id>/release', methods=['POST'])
    @wms_permission_required('quality', 'edit')
    @wms_csrf_required
    def wms_quality_hold_release(hold_id):
        """Release a quality hold."""
        db = get_db()
        ensure_quality_hold_tables()
        try:
            hold = db.execute('SELECT * FROM wms_quality_holds WHERE id = ?', (hold_id,)).fetchone()
            if not hold:
                flash('Hold not found.', 'error')
                return redirect(url_for('wms_quality_holds'))
            if not ensure_warehouse_allowed(hold['warehouse_id']):
                flash('You do not have access to this warehouse.', 'error')
                return redirect(url_for('wms_quality_holds'))
            if hold['status'] != 'ACTIVE':
                flash('Only active holds can be released.', 'error')
                return redirect(url_for('wms_quality_hold_detail', hold_id=hold_id))

            release_reason = request.form.get('release_reason', '')
            disposition = request.form.get('disposition', 'RELEASED')
            release_status = 'AVAILABLE' if disposition == 'RELEASED' else 'BLOCKED'

            db.execute('''
                UPDATE wms_quality_holds SET
                    status = 'RELEASED',
                    released_by = ?,
                    released_at = datetime('now'),
                    release_reason = ?,
                    updated_at = datetime('now')
                WHERE id = ?
            ''', (session.get('user_id'), release_reason, hold_id))
            db.execute('''
                UPDATE wms_inventory_balances
                SET blocked_quantity = MAX(blocked_quantity - ?, 0),
                    status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = (
                    SELECT id FROM wms_inventory_balances
                    WHERE item_id = ?
                      AND warehouse_id = ?
                      AND status = 'QUARANTINE'
                      AND (? IS NULL OR location_id = ?)
                      AND (? IS NULL OR lot_id = ?)
                    ORDER BY blocked_quantity DESC, quantity DESC
                    LIMIT 1
                )
            ''', (hold['quantity_held'], release_status, hold['item_id'], hold['warehouse_id'],
                  hold['location_id'], hold['location_id'], hold['lot_id'], hold['lot_id']))
            db.commit()

            log_wms_audit('RELEASE', 'QUALITY_HOLD', hold['hold_number'],
                          {'disposition': disposition, 'release_reason': release_reason})
            flash(f'Hold {hold["hold_number"]} released!', 'success')
        except Exception as e:
            import traceback
            print(f"WMS quality hold release error: {e}")
            traceback.print_exc()
            db.rollback()
            flash('Error releasing hold. Please try again.', 'error')

        return redirect(url_for('wms_quality_hold_detail', hold_id=hold_id))

    @app.route('/wms/quality/holds/<int:hold_id>/delete', methods=['POST'])
    @wms_permission_required('quality', 'delete')
    @wms_csrf_required
    def wms_quality_hold_delete(hold_id):
        """Delete a quality hold."""
        db = get_db()
        ensure_quality_hold_tables()
        try:
            hold = db.execute('SELECT * FROM wms_quality_holds WHERE id = ?', (hold_id,)).fetchone()
            if not hold:
                flash('Hold not found.', 'error')
                return redirect(url_for('wms_quality_holds'))

            db.execute('DELETE FROM wms_quality_holds WHERE id = ?', (hold_id,))
            db.commit()
            log_wms_audit('DELETE', 'QUALITY_HOLD', hold['hold_number'])
            flash(f'Hold {hold["hold_number"]} deleted.', 'success')
        except Exception as e:
            import traceback
            print(f"WMS quality hold delete error: {e}")
            traceback.print_exc()
            db.rollback()
            flash('Error deleting hold.', 'error')

        return redirect(url_for('wms_quality_holds'))

    @app.route('/wms/quality/aql-rules/edit/<int:rule_id>', methods=['GET', 'POST'])
    @wms_permission_required('quality', 'edit')
    def wms_quality_aql_rules_edit(rule_id):
        """Edit AQL rule."""
        db = get_db()
        rule = db.execute('SELECT * FROM wms_aql_rules WHERE id = ?', (rule_id,)).fetchone()
        if not rule:
            flash('Rule not found', 'error')
            return redirect(url_for('wms_quality_aql_rules'))

        if request.method == 'POST':
            try:
                rule_name = request.form.get('rule_name')
                inspection_level = request.form.get('inspection_level', 'II')
                aql_level = float(request.form.get('aql_level', 1.5))
                lot_size_min = int(request.form.get('lot_size_min', 1))
                lot_size_max = int(request.form.get('lot_size_max', 50000))

                db.execute('''
                    UPDATE wms_aql_rules SET
                    rule_name = ?, inspection_level = ?, aql_level = ?, lot_size_min = ?, lot_size_max = ?
                    WHERE id = ?
                ''', (rule_name, inspection_level, aql_level, lot_size_min, lot_size_max, rule_id))
                db.commit()
                flash('AQL Rule updated!', 'success')
                return redirect(url_for('wms_quality_aql_rules'))
            except Exception as e:
                import traceback
                print(f"WMS AQL rule update error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error updating AQL rule. Please try again.', 'error')
        title = 'Edit AQL Rule'
        return render_template('wms/quality_aql_rule_form.html', title=title, rule=rule)

    @app.route('/wms/quality/aql-rules/delete/<int:rule_id>', methods=['POST'])
    @wms_permission_required('quality', 'delete')
    def wms_quality_aql_rules_delete(rule_id):
        """Delete AQL rule."""
        db = get_db()
        try:
            db.execute('UPDATE wms_aql_rules SET is_active = 0 WHERE id = ?', (rule_id,))
            db.commit()
            flash('AQL Rule deleted!', 'success')
        except Exception as e:
            import traceback
            print(f"WMS AQL rule delete error: {e}")
            traceback.print_exc()
            db.rollback()
            flash('Error deleting AQL rule. Please try again.', 'error')
        return redirect(url_for('wms_quality_aql_rules'))

    # ============================================================
    # DOCUMENTS / FORMS
    # ============================================================

    @app.route('/wms/documents')
    @wms_permission_required('documents', 'view')
    def wms_documents():
        """WMS Documents."""

        db = get_db()
        doc_type = request.args.get('document_type', '')
        page = int(request.args.get('page', 1))
        per_page = 50

        query = '''
            SELECT d.*, w.name as warehouse_name,
                   u1.username as prepared_by_name,
                   u2.username as approved_by_name
            FROM wms_documents d
            LEFT JOIN wms_warehouses w ON w.id = d.warehouse_id
            LEFT JOIN users u1 ON u1.id = d.prepared_by
            LEFT JOIN users u2 ON u2.id = d.approved_by
            WHERE 1=1
        '''
        params = []
        if doc_type:
            query += " AND d.document_type = ?"
            params.append(doc_type)

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY d.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        documents = db.execute(query, params).fetchall()

        title = 'Documents / Forms'
        return render_template('wms/documents.html',
            title=title,
            documents=documents,
            doc_type=doc_type,
            page=page,
            per_page=per_page,
            total_count=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1
        )

    # ============================================================
    # REPORTS & ANALYTICS
    # ============================================================

    @app.route('/wms/reports')
    @wms_permission_required('reports', 'view')
    def wms_reports():
        """WMS Reports index."""

        title = 'WMS Reports & Analytics'
        return render_template('wms/reports.html', title=title)

    @app.route('/wms/reports/inventory-summary')
    def wms_report_inventory_summary():
        """Inventory summary report."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        db = get_db()
        warehouse_id = request.args.get('warehouse_id', '')

        query = '''
            SELECT
                i.item_code, i.name as item_name,
                cat.name as category_name,
                br.name as brand_name,
                i.unit_of_measure,
                SUM(b.quantity) as total_qty,
                SUM(b.reserved_quantity) as reserved,
                SUM(b.allocated_quantity) as allocated,
                SUM(CASE WHEN b.status = 'AVAILABLE' THEN b.quantity ELSE 0 END) as available,
                i.min_stock_level, i.reorder_point,
                COALESCE(i.weight_kg, 0) * SUM(b.quantity) as total_weight,
                COALESCE(i.volume_m3, 0) * SUM(b.quantity) as total_volume,
                COUNT(DISTINCT b.warehouse_id) as warehouse_count
            FROM wms_inventory_balances b
            JOIN wms_items i ON i.id = b.item_id
            LEFT JOIN wms_item_categories cat ON cat.id = i.category_id
            LEFT JOIN wms_item_brands br ON br.id = i.brand_id
            WHERE 1=1
        '''
        params = []
        if warehouse_id:
            query += " AND b.warehouse_id = ?"
            params.append(warehouse_id)

        query += " GROUP BY i.id ORDER BY i.name"
        items = db.execute(query, params).fetchall()

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'Inventory Summary Report'
        return render_template('wms/report_inventory_summary.html',
            title=title,
            items=items,
            warehouses=warehouses,
            warehouse_id=warehouse_id
        )

    @app.route('/wms/reports/stock-movement')
    def wms_report_stock_movement():
        """Stock movement report."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        db = get_db()
        from_date = request.args.get('from_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        to_date = request.args.get('to_date', datetime.now().strftime('%Y-%m-%d'))
        transaction_type = request.args.get('transaction_type', '')

        query = '''
            SELECT l.*, i.item_code, i.name as item_name,
                   w.name as warehouse_name,
                   u.username
            FROM wms_inventory_ledger l
            JOIN wms_items i ON i.id = l.item_id
            JOIN wms_warehouses w ON w.id = l.warehouse_id
            LEFT JOIN users u ON u.id = l.user_id
            WHERE l.created_at >= ? AND l.created_at <= ?
        '''
        params = [from_date, to_date + ' 23:59:59']

        if transaction_type:
            query += " AND l.transaction_type = ?"
            params.append(transaction_type)

        query += " ORDER BY l.created_at DESC LIMIT 1000"
        movements = db.execute(query, params).fetchall()

        title = 'Stock Movement Report'
        return render_template('wms/report_stock_movement.html',
            title=title,
            movements=movements,
            from_date=from_date,
            to_date=to_date,
            transaction_type=transaction_type
        )

    @app.route('/wms/reports/expiry-report')
    def wms_report_expiry():
        """Expiry/batch report."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        db = get_db()
        warehouse_id = request.args.get('warehouse_id', '')
        days = int(request.args.get('days', 90))

        query = '''
            SELECT l.*, i.item_code, i.name as item_name,
                   w.name as warehouse_name, loc.code as location_code
            FROM wms_lots l
            JOIN wms_items i ON i.id = l.item_id
            JOIN wms_warehouses w ON w.id = l.warehouse_id
            LEFT JOIN wms_locations loc ON loc.id = l.location_id
            WHERE l.expiry_date IS NOT NULL AND l.quantity > 0
        '''
        params = []
        if warehouse_id:
            query += " AND l.warehouse_id = ?"
            params.append(warehouse_id)

        query += " ORDER BY l.expiry_date ASC"
        lots = db.execute(query, params).fetchall()

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'Expiry / Batch Report'
        return render_template('wms/report_expiry.html',
            title=title,
            lots=lots,
            warehouses=warehouses,
            warehouse_id=warehouse_id,
            days=days
        )

    @app.route('/wms/reports/space-utilization')
    def wms_report_space():
        """Space utilization report."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        db = get_db()
        warehouses_list = db.execute('''
            SELECT w.*,
                (SELECT COUNT(*) FROM wms_locations WHERE warehouse_id = w.id AND is_active = 1) as total_locations,
                (SELECT COUNT(*) FROM wms_locations WHERE warehouse_id = w.id AND is_active = 1 AND is_empty = 1) as empty_locations,
                (SELECT COALESCE(SUM(current_volume_m3), 0) FROM wms_locations WHERE warehouse_id = w.id) as used_volume,
                (SELECT COALESCE(SUM(capacity_volume_m3), 0) FROM wms_locations WHERE warehouse_id = w.id) as total_capacity,
                (SELECT COALESCE(SUM(current_weight_kg), 0) FROM wms_locations WHERE warehouse_id = w.id) as used_weight,
                (SELECT COALESCE(SUM(capacity_weight_kg), 0) FROM wms_locations WHERE warehouse_id = w.id) as total_weight,
                (SELECT COUNT(DISTINCT zone_id) FROM wms_locations WHERE warehouse_id = w.id AND zone_id IS NOT NULL) as zone_count
            FROM wms_warehouses w
            WHERE w.is_active = 1
            ORDER BY w.name
        ''').fetchall()

        title = 'Space Utilization Report'
        return render_template('wms/report_space.html',
            title=title,
            warehouses=warehouses_list
        )

    @app.route('/wms/reports/custom')
    @wms_permission_required('reports', 'view')
    def wms_reports_custom():
        """Custom report builder."""
        db = get_db()
        saved_reports = db.execute('''
            SELECT * FROM wms_saved_reports
            ORDER BY created_at DESC LIMIT 20
        ''').fetchall() if 'wms_saved_reports' in [t[0] for t in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()] else []
        title = 'Custom Report Builder'
        return render_template('wms/report_builder.html', title=title, saved_reports=saved_reports)

    @app.route('/wms/reports/builder/save', methods=['POST'])
    @wms_permission_required('reports', 'create')
    def wms_reports_builder_save():
        """Save custom report."""
        try:
            data = request.get_json()
            report_name = data.get('report_name')
            fields = data.get('fields', [])
            filters = data.get('filters', [])

            db = get_db()
            db.execute('''
                INSERT INTO wms_saved_reports (report_name, fields_json, filters_json, created_by)
                VALUES (?, ?, ?, ?)
            ''', (report_name, json.dumps(fields), json.dumps(filters), session.get('user_id')))
            db.commit()
            return jsonify({'success': True, 'message': 'Report saved'})
        except Exception as e:
            import traceback
            print(f"WMS EDI test send error: {e}")
            traceback.print_exc()
            db.rollback()
            return jsonify({'success': False, 'error': 'Unable to send test IDoc. Please try again.'}), 500

    @app.route('/wms/reports/scheduled')
    @wms_permission_required('reports', 'view')
    def wms_reports_scheduled():
        """Scheduled reports list."""
        db = get_db()
        reports = db.execute('''
            SELECT r.*, u.username as created_by_name
            FROM wms_scheduled_reports r
            LEFT JOIN users u ON u.id = r.created_by
            ORDER BY r.created_at DESC
        ''').fetchall() if 'wms_scheduled_reports' in [t['name'] for t in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()] else []
        title = 'Scheduled Reports'
        return render_template('wms/reports_scheduled.html', title=title, reports=reports)

    @app.route('/wms/reports/abc-analysis')
    @wms_permission_required('reports', 'view')
    def wms_reports_abc_analysis():
        """ABC Analysis report."""
        db = get_db()
        abc_data = db.execute('''
            SELECT
                i.item_code, i.name as item_name,
                0 as total_value,
                CASE
                    WHEN SUM(b.quantity) >= (SELECT SUM(quantity) * 0.8 FROM wms_inventory_balances WHERE quantity > 0) THEN 'A'
                    WHEN SUM(b.quantity) >= (SELECT SUM(quantity) * 0.95 FROM wms_inventory_balances WHERE quantity > 0) THEN 'B'
                    ELSE 'C'
                END as abc_class
            FROM wms_inventory_balances b
            JOIN wms_items i ON i.id = b.item_id
            WHERE b.quantity > 0
            GROUP BY i.id
            HAVING total_value > 0
            ORDER BY total_value DESC
        ''').fetchall()
        title = 'ABC Analysis Report'
        return render_template('wms/report_abc_analysis.html', title=title, abc_data=abc_data)

    @app.route('/wms/reports/pick-efficiency')
    @wms_permission_required('reports', 'view')
    def wms_reports_pick_efficiency():
        """Pick efficiency report."""
        db = get_db()
        efficiency = db.execute('''
            SELECT
                DATE(t.completed_at) as pick_date,
                COUNT(*) as total_picks,
                SUM(CASE WHEN t.status = 'COMPLETED' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN t.short_pick_reason IS NOT NULL THEN 1 ELSE 0 END) as short_picks,
                AVG(t.actual_minutes) as avg_minutes,
                SUM(t.actual_minutes) as total_minutes
            FROM wms_pick_tasks t
            WHERE t.completed_at >= date('now', '-30 days')
            GROUP BY DATE(t.completed_at)
            ORDER BY pick_date DESC
        ''').fetchall()
        title = 'Pick Efficiency Report'
        return render_template('wms/report_pick_efficiency.html', title=title, efficiency=efficiency)

    @app.route('/wms/reports/receiving-accuracy')
    @wms_permission_required('reports', 'view')
    def wms_reports_receiving_accuracy():
        """Receiving accuracy report."""
        db = get_db()
        accuracy = db.execute('''
            SELECT
                r.receipt_number, r.received_at,
                i.item_code,
                rl.expected_quantity, rl.received_quantity,
                rl.received_quantity - rl.expected_quantity as variance,
                ABS(rl.received_quantity - rl.expected_quantity) * 100.0 / NULLIF(rl.expected_quantity, 0) as variance_pct
            FROM wms_inbound_receipt_lines rl
            JOIN wms_inbound_receipts r ON r.id = rl.receipt_id
            JOIN wms_items i ON i.id = rl.item_id
            WHERE r.received_at >= date('now', '-30 days')
            ORDER BY r.received_at DESC
        ''').fetchall()
        title = 'Receiving Accuracy Report'
        return render_template('wms/report_receiving_accuracy.html', title=title, accuracy=accuracy)

    @app.route('/wms/reports/quality-holds')
    @wms_permission_required('reports', 'view')
    def wms_report_quality_holds():
        """Quality hold report with CSV export."""
        db = get_db()
        ensure_quality_hold_tables()
        status = request.args.get('status', '')
        warehouse_id = request.args.get('warehouse_id', '')
        export_format = request.args.get('export', '')
        wh_filter = get_warehouse_filter(session.get('user_id')).replace('warehouse_id', 'h.warehouse_id')

        query = '''
            SELECT h.hold_number, h.status, h.hold_type, h.hold_reason,
                   h.quantity_held, h.held_at, h.released_at, h.release_reason,
                   w.name as warehouse_name, i.item_code, i.name as item_name,
                   l.code as location_code, u1.username as held_by_name, u2.username as released_by_name
            FROM wms_quality_holds h
            JOIN wms_warehouses w ON w.id = h.warehouse_id
            JOIN wms_items i ON i.id = h.item_id
            LEFT JOIN wms_locations l ON l.id = h.location_id
            LEFT JOIN users u1 ON u1.id = h.held_by
            LEFT JOIN users u2 ON u2.id = h.released_by
            WHERE 1=1
        ''' + wh_filter
        params = []
        if status:
            query += ' AND h.status = ?'
            params.append(status)
        if warehouse_id:
            if not ensure_warehouse_allowed(warehouse_id):
                flash('You do not have access to this warehouse.', 'error')
                return redirect(url_for('wms_report_quality_holds'))
            query += ' AND h.warehouse_id = ?'
            params.append(warehouse_id)
        query += ' ORDER BY h.held_at DESC'
        holds = db.execute(query, params).fetchall()

        if export_format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Hold #', 'Status', 'Type', 'Reason', 'Quantity', 'Warehouse', 'Item', 'Location', 'Held By', 'Held At', 'Released By', 'Released At', 'Release Reason'])
            for h in holds:
                writer.writerow([h['hold_number'], h['status'], h['hold_type'], h['hold_reason'], h['quantity_held'], h['warehouse_name'], h['item_code'], h['location_code'], h['held_by_name'], h['held_at'], h['released_by_name'], h['released_at'], h['release_reason']])
            return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=wms_quality_holds.csv'})

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        return render_template('wms/report_quality_holds.html',
            title='Quality Hold Report',
            holds=holds,
            warehouses=warehouses,
            status=status,
            warehouse_id=warehouse_id
        )

    # ============================================================
    # WMS SETTINGS
    # ============================================================

    @app.route('/wms/settings')
    @wms_permission_required('settings', 'view')
    def wms_settings():
        """WMS Settings."""

        db = get_db()
        tab = request.args.get('tab', 'general')

        # Get all settings grouped by category
        settings = db.execute('''
            SELECT * FROM wms_settings WHERE is_active = 1 ORDER BY category, setting_key
        ''').fetchall()

        settings_by_category = {}
        for s in settings:
            cat = s['category']
            if cat not in settings_by_category:
                settings_by_category[cat] = []
            settings_by_category[cat].append(s)

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        companies = db.execute('SELECT * FROM wms_companies WHERE is_active = 1 ORDER BY name').fetchall()
        location_types = db.execute('SELECT * FROM wms_location_types WHERE is_active = 1 ORDER BY name').fetchall()
        reason_codes = db.execute('SELECT * FROM wms_reason_codes WHERE is_active = 1 ORDER BY reason_type, code').fetchall()
        categories = db.execute('SELECT * FROM wms_item_categories WHERE is_active = 1 ORDER BY name').fetchall()
        brands = db.execute('SELECT * FROM wms_item_brands WHERE is_active = 1 ORDER BY name').fetchall()
        groups = db.execute('SELECT * FROM wms_item_groups WHERE is_active = 1 ORDER BY name').fetchall()

        # Get users and their permissions
        users = db.execute('SELECT id, username FROM users ORDER BY username').fetchall()
        user_permissions = {}
        for u in users:
            perms = get_wms_permissions(u['id'])
            user_permissions[u['id']] = perms

        title = 'WMS Settings'
        return render_template('wms/settings.html',
            title=title,
            tab=tab,
            settings_by_category=settings_by_category,
            warehouses=warehouses,
            companies=companies,
            location_types=location_types,
            reason_codes=reason_codes,
            categories=categories,
            brands=brands,
            groups=groups,
            users=users,
            user_permissions=user_permissions,
            all_permissions=[
                'all', 'view_inventory', 'edit_inventory', 'view_stock_count',
                'create_adjustment', 'approve_adjustment',
                'view_reports', 'export_reports',
                'manage_receiving', 'manage_putaway',
                'manage_picking', 'manage_packing', 'manage_dispatch',
                'manage_transfers', 'approve_transfers',
                'manage_returns', 'approve_returns',
                'manage_quality',
                'manage_warehouses', 'manage_locations',
                'manage_items', 'manage_categories',
                'view_all_companies', 'view_all_warehouses',
                'manage_settings', 'manage_users',
                'manage_alerts',
            ]
        )

    @app.route('/wms/settings/save', methods=['POST'])
    @wms_permission_required('settings', 'edit')
    def wms_settings_save():
        """Save WMS settings."""

        db = get_db()
        data = request.form
        try:
            for key, value in data.items():
                if key.startswith('setting_'):
                    setting_key = key.replace('setting_', '')
                    setting_type = db.execute(
                        'SELECT setting_type FROM wms_settings WHERE setting_key = ?', (setting_key,)).fetchone()
                    if setting_type:
                        if setting_type['setting_type'] == 'boolean':
                            value = '1' if value in ('1', 'true', 'on') else '0'
                        db.execute('''
                            UPDATE wms_settings SET setting_value = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE setting_key = ?
                        ''', (value, setting_key))
            db.commit()
            log_wms_audit('UPDATE', 'SETTINGS', None, {'keys': list(data.keys())})
            flash('Settings saved successfully!', 'success')
        except Exception as e:
            import traceback
            print(f"WMS settings save error: {e}")
            traceback.print_exc()
            db.rollback()
            flash('Error saving settings. Please try again.', 'error')

        return redirect(url_for('wms_settings'))

    # ============================================================
    # ZONES CRUD
    # ============================================================

    @app.route('/wms/zones/new', methods=['GET', 'POST'])
    @wms_permission_required('zones', 'create')
    def wms_zones_new():
        """Create new zone."""
        db = get_db()

        if request.method == 'POST':
            data = request.form
            try:
                db.execute('''
                    INSERT INTO wms_zones (warehouse_id, code, name, zone_type, description,
                        picking_enabled, putaway_enabled, replenishment_enabled, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    data.get('warehouse_id'), data.get('code'), data.get('name'),
                    data.get('zone_type'), data.get('description'),
                    1 if data.get('picking_enabled') else 0,
                    1 if data.get('putaway_enabled') else 0,
                    1 if data.get('replenishment_enabled') else 0,
                    data.get('sort_order', 0)
                ))
                db.commit()
                flash('Zone created successfully!', 'success')
                return redirect(url_for('wms_warehouse_detail', warehouse_id=data.get('warehouse_id')))
            except Exception as e:
                import traceback
                print(f"WMS zone create error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error creating zone. Please try again.', 'error')

        warehouse_id = request.args.get('warehouse_id')
        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'New Zone'
        return render_template('wms/zone_form.html',
            title=title,
            zone=None,
            warehouses=warehouses,
            selected_warehouse=warehouse_id,
            form_action=url_for('wms_zones_new')
        )

    # ============================================================
    # ITEM CATEGORIES
    # ============================================================

    @app.route('/wms/item-categories')
    @wms_permission_required('item_categories', 'view')
    def wms_item_categories():
        """Item categories."""

        db = get_db()
        categories = db.execute('''
            SELECT c.*, p.name as parent_name,
                (SELECT COUNT(*) FROM wms_items i WHERE i.category_id = c.id) as item_count
            FROM wms_item_categories c
            LEFT JOIN wms_item_categories p ON p.id = c.parent_id
            WHERE c.is_active = 1
            ORDER BY c.path, c.name
        ''').fetchall()

        title = 'Product Groups / Categories'
        return render_template('wms/item_categories.html',
            title=title,
            categories=categories
        )

    @app.route('/wms/item-categories/new', methods=['GET', 'POST'])
    @wms_permission_required('item_categories', 'create')
    def wms_item_categories_new():
        """Create new item category."""
        db = get_db()

        if request.method == 'POST':
            data = request.form
            try:
                parent_id = data.get('parent_id') or None
                level = 0
                path = data.get('code')
                if parent_id:
                    parent = db.execute('SELECT level, path FROM wms_item_categories WHERE id = ?', (parent_id,)).fetchone()
                    if parent:
                        level = parent['level'] + 1
                        path = parent['path'] + '/' + data.get('code')

                db.execute('''
                    INSERT INTO wms_item_categories (parent_id, code, name, name_local, description, level, path, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (parent_id, data.get('code'), data.get('name'), data.get('name_local'),
                      data.get('description'), level, path, data.get('sort_order', 0)))
                db.commit()
                flash('Category created successfully!', 'success')
                return redirect(url_for('wms_item_categories'))
            except Exception as e:
                import traceback
                print(f"WMS category create error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error creating category. Please try again.', 'error')

        parent_categories = db.execute('SELECT * FROM wms_item_categories WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'New Category'
        return render_template('wms/item_category_form.html',
            title=title,
            category=None,
            parent_categories=parent_categories,
            form_action=url_for('wms_item_categories_new')
        )

    # ============================================================
    # ITEM BRANDS
    # ============================================================

    @app.route('/wms/item-brands')
    @wms_permission_required('item_brands', 'view')
    def wms_item_brands():
        """Item brands."""

        db = get_db()
        brands = db.execute('''
            SELECT b.*,
                (SELECT COUNT(*) FROM wms_items i WHERE i.brand_id = b.id) as item_count
            FROM wms_item_brands b
            WHERE b.is_active = 1
            ORDER BY b.name
        ''').fetchall()

        title = 'Brands'
        return render_template('wms/item_brands.html',
            title=title,
            brands=brands
        )

    @app.route('/wms/item-brands/new', methods=['GET', 'POST'])
    @wms_permission_required('item_brands', 'create')
    def wms_item_brands_new():
        """Create new brand."""
        db = get_db()

        if request.method == 'POST':
            data = request.form
            try:
                db.execute('''
                    INSERT INTO wms_item_brands (code, name, name_local, manufacturer, country, website, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (data.get('code'), data.get('name'), data.get('name_local'),
                      data.get('manufacturer'), data.get('country'),
                      data.get('website'), data.get('description')))
                db.commit()
                flash('Brand created successfully!', 'success')
                return redirect(url_for('wms_item_brands'))
            except Exception as e:
                import traceback
                print(f"WMS brand create error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error creating brand. Please try again.', 'error')

        title = 'New Brand'
        return render_template('wms/item_brand_form.html',
            title=title,
            brand=None,
            form_action=url_for('wms_item_brands_new')
        )

    # ============================================================
    # LOTS / BATCHES
    # ============================================================

    @app.route('/wms/lots')
    @wms_permission_required('lots', 'view')
    def wms_lots():
        """Lots/Batches list."""

        db = get_db()
        search = request.args.get('search', '').strip()
        warehouse_id = request.args.get('warehouse_id', '')
        status = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        per_page = 50

        query = '''
            SELECT l.*, i.item_code, i.name as item_name,
                   w.name as warehouse_name, loc.code as location_code
            FROM wms_lots l
            JOIN wms_items i ON i.id = l.item_id
            JOIN wms_warehouses w ON w.id = l.warehouse_id
            LEFT JOIN wms_locations loc ON loc.id = l.location_id
            WHERE l.quantity > 0
        '''
        params = []
        if search:
            query += " AND (l.lot_number LIKE ? OR i.item_code LIKE ? OR i.name LIKE ?)"
            sp = f'%{search}%'
            params.extend([sp, sp, sp])
        if warehouse_id:
            query += " AND l.warehouse_id = ?"
            params.append(warehouse_id)
        if status:
            query += " AND l.status = ?"
            params.append(status)

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY l.expiry_date ASC NULLS LAST LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        lots = db.execute(query, params).fetchall()

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'Batch / Lot / Serial Control'
        return render_template('wms/lots.html',
            title=title,
            lots=lots,
            warehouses=warehouses,
            search=search,
            warehouse_id=warehouse_id,
            status=status,
            page=page,
            per_page=per_page,
            total_count=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1
        )

    # ============================================================
    # WORK TASKS
    # ============================================================

    @app.route('/wms/work-tasks')
    @wms_permission_required('work_tasks', 'view')
    def wms_work_tasks():
        """Work queue / tasks."""

        db = get_db()
        task_type = request.args.get('task_type', '')
        status = request.args.get('status', '')
        warehouse_id = request.args.get('warehouse_id', '')
        page = int(request.args.get('page', 1))
        per_page = 50

        query = '''
            SELECT t.*, w.name as warehouse_name, l.code as location_code,
                   u.username as assigned_to_name
            FROM wms_work_tasks t
            JOIN wms_warehouses w ON w.id = t.warehouse_id
            LEFT JOIN wms_locations l ON l.id = t.location_id
            LEFT JOIN users u ON u.id = t.assigned_to
            WHERE 1=1
        '''
        params = []
        if task_type:
            query += " AND t.task_type = ?"
            params.append(task_type)
        if status:
            query += " AND t.status = ?"
            params.append(status)
        if warehouse_id:
            query += " AND t.warehouse_id = ?"
            params.append(warehouse_id)

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY t.priority DESC, t.created_at LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        tasks = db.execute(query, params).fetchall()

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'Tasks / Work Queue'
        return render_template('wms/work_tasks.html',
            title=title,
            tasks=tasks,
            warehouses=warehouses,
            task_type=task_type,
            status=status,
            warehouse_id=warehouse_id,
            page=page,
            per_page=per_page,
            total_count=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1
        )

    # ============================================================
    # ALERTS
    # ============================================================

    @app.route('/wms/alerts')
    @wms_permission_required('alerts', 'view')
    def wms_alerts():
        """WMS Alerts."""

        db = get_db()
        severity = request.args.get('severity', '')
        is_active = request.args.get('is_active', '1')
        page = int(request.args.get('page', 1))
        per_page = 50
        wh_filter = get_warehouse_filter(session.get('user_id')).replace('warehouse_id', 'a.warehouse_id')

        query = '''
            SELECT a.*, w.name as warehouse_name, i.item_code, i.name as item_name
            FROM wms_alerts a
            LEFT JOIN wms_warehouses w ON w.id = a.warehouse_id
            LEFT JOIN wms_items i ON i.id = a.item_id
            WHERE 1=1
        '''
        params = []
        query += wh_filter
        if severity:
            query += " AND a.severity = ?"
            params.append(severity)
        if is_active:
            query += " AND a.is_active = ?"
            params.append(is_active)

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY a.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        alerts = db.execute(query, params).fetchall()

        title = 'Alerts & Notifications'
        return render_template('wms/alerts.html',
            title=title,
            alerts=alerts,
            severity=severity,
            is_active=is_active,
            page=page,
            per_page=per_page,
            total_count=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1
        )

    @app.route('/wms/alerts/acknowledge/<int:alert_id>', methods=['POST'])
    @wms_permission_required('alerts', 'edit')
    @wms_csrf_required
    def wms_alerts_acknowledge(alert_id):
        """Acknowledge an alert."""

        db = get_db()
        try:
            alert = db.execute('SELECT warehouse_id FROM wms_alerts WHERE id = ?', (alert_id,)).fetchone()
            if not alert:
                flash('Alert not found.', 'error')
                return redirect(url_for('wms_alerts'))
            if alert['warehouse_id'] and not ensure_warehouse_allowed(alert['warehouse_id']):
                flash('You do not have access to this warehouse alert.', 'error')
                return redirect(url_for('wms_alerts'))
            db.execute('''
                UPDATE wms_alerts SET is_acknowledged = 1, acknowledged_by = ?, acknowledged_at = datetime('now')
                WHERE id = ?
            ''', (session.get('user_id'), alert_id))
            db.commit()
            flash('Alert acknowledged.', 'success')
        except Exception as e:
            import traceback
            print(f"WMS alert acknowledge error: {e}")
            traceback.print_exc()
            db.rollback()
            flash('Error acknowledging alert. Please try again.', 'error')

        return redirect(url_for('wms_alerts'))

    # ============================================================
    # API ENDPOINTS
    # ============================================================

    @app.route('/wms/api/locations/<int:warehouse_id>')
    @wms_permission_required('locations', 'view')
    def wms_api_locations(warehouse_id):
        """API: Get locations for a warehouse."""

        db = get_db()
        locations = db.execute('''
            SELECT l.*, z.name as zone_name
            FROM wms_locations l
            LEFT JOIN wms_zones z ON z.id = l.zone_id
            WHERE l.warehouse_id = ? AND l.is_active = 1
            ORDER BY l.code
        ''', (warehouse_id,)).fetchall()

        return jsonify([dict(row) for row in locations])

    @app.route('/wms/api/items/search')
    @wms_permission_required('items', 'view')
    def wms_api_items_search():
        """API: Search items."""

        db = get_db()
        q = request.args.get('q', '').strip()
        if len(q) < 2:
            return jsonify([])

        items = db.execute('''
            SELECT i.*, b.name as brand_name, c.name as category_name
            FROM wms_items i
            LEFT JOIN wms_item_brands b ON b.id = i.brand_id
            LEFT JOIN wms_item_categories c ON c.id = i.category_id
            WHERE i.is_active = 1 AND (i.item_code LIKE ? OR i.name LIKE ? OR i.barcode LIKE ? OR i.sku LIKE ?)
            ORDER BY i.name LIMIT 20
        ''', (f'%{q}%', f'%{q}%', f'%{q}%', f'%{q}%')).fetchall()

        return jsonify([dict(row) for row in items])

    @app.route('/wms/api/stock/<int:item_id>')
    @wms_permission_required('inventory', 'view')
    def wms_api_stock(item_id):
        """API: Get stock for an item."""

        db = get_db()
        balances = db.execute('''
            SELECT b.*, w.name as warehouse_name, l.code as location_code,
                   lot.lot_number, lot.expiry_date
            FROM wms_inventory_balances b
            JOIN wms_warehouses w ON w.id = b.warehouse_id
            LEFT JOIN wms_locations l ON l.id = b.location_id
            LEFT JOIN wms_lots lot ON lot.id = b.lot_id
            WHERE b.item_id = ?
        ''', (item_id,)).fetchall()

        return jsonify([dict(row) for row in balances])

    @app.route('/wms/api/dashboard/stats')
    @wms_permission_required('dashboard', 'view')
    def wms_api_dashboard_stats():
        """API: Dashboard statistics for AJAX refresh."""

        db = get_db()
        user_id = session.get('user_id')
        wh_filter = get_warehouse_filter(user_id)

        stats = {
            'pending_receiving': db.execute(f'''
                SELECT COUNT(*) as cnt FROM wms_inbound_receipts
                WHERE status IN ('EXPECTED', 'ARRIVED', 'PARTIAL') {wh_filter.replace('warehouse_id', 'warehouse_id')}
            ''').fetchone()['cnt'],
            'pending_putaway': db.execute(f'''
                SELECT COUNT(*) as cnt FROM wms_putaway_tasks WHERE status = 'PENDING' {wh_filter.replace('warehouse_id', 'wms_putaway_tasks.warehouse_id')}
            ''').fetchone()['cnt'],
            'pending_picking': db.execute(f'''
                SELECT COUNT(*) as cnt
                FROM wms_pick_tasks p
                JOIN wms_locations l ON l.id = p.source_location_id
                WHERE p.status IN ('PENDING', 'IN_PROGRESS') {wh_filter.replace('warehouse_id', 'l.warehouse_id')}
            ''').fetchone()['cnt'],
            'pending_transfers': db.execute(f'''
                SELECT COUNT(*) as cnt FROM wms_transfers WHERE status IN ('REQUESTED', 'APPROVED', 'PICKING', 'DISPATCHED') {wh_filter.replace('source_warehouse_id', 'source_warehouse_id')}
            ''').fetchone()['cnt'],
            'active_alerts': db.execute(f'''
                SELECT COUNT(*) as cnt FROM wms_alerts WHERE is_active = 1 {wh_filter.replace('warehouse_id', 'warehouse_id')}
            ''').fetchone()['cnt'],
            'available_stock': db.execute(f'''
                SELECT COALESCE(SUM(quantity), 0) as qty FROM wms_inventory_balances WHERE status = 'AVAILABLE' {wh_filter}
            ''').fetchone()['qty'],
        }
        return jsonify(stats)

    # ============================================================
    # EXPORT ENDPOINTS
    # ============================================================

    @app.route('/wms/export/inventory')
    @wms_permission_required('reports', 'view')
    def wms_export_inventory():
        """Export inventory to Excel."""

        db = get_db()
        selected_ids = request.args.getlist('ids')
        selected_cols = request.args.getlist('cols')

        all_cols = ['item', 'warehouse', 'location', 'lot', 'expiry',
                    'quantity', 'reserved', 'allocated', 'status']
        if selected_cols:
            cols_to_export = [c for c in all_cols if c in selected_cols]
        else:
            cols_to_export = all_cols

        col_header_map = {
            'item': 'Item',
            'warehouse': 'Warehouse',
            'location': 'Location',
            'lot': 'Lot Number',
            'expiry': 'Expiry Date',
            'quantity': 'Available',
            'reserved': 'Reserved',
            'allocated': 'Allocated',
            'status': 'Status',
        }
        headers = [col_header_map[c] for c in cols_to_export]

        query = '''
            SELECT b.id, i.item_code, i.name as item_name, i.unit_of_measure,
                   br.name as brand, cat.name as category,
                   w.name as warehouse, l.code as location,
                   lot.lot_number, lot.expiry_date,
                   b.quantity, b.reserved_quantity, b.allocated_quantity,
                   b.status
            FROM wms_inventory_balances b
            JOIN wms_items i ON i.id = b.item_id
            JOIN wms_warehouses w ON w.id = b.warehouse_id
            LEFT JOIN wms_locations l ON l.id = b.location_id
            LEFT JOIN wms_lots lot ON lot.id = b.lot_id
            LEFT JOIN wms_item_brands br ON br.id = i.brand_id
            LEFT JOIN wms_item_categories cat ON cat.id = i.category_id
            WHERE b.quantity != 0
        '''
        params = []
        if selected_ids:
            placeholders = ','.join(['?'] * len(selected_ids))
            query += f" AND b.id IN ({placeholders})"
            params.extend(selected_ids)

        query += " ORDER BY i.name"
        rows = db.execute(query, params).fetchall()

        wb = Workbook()
        ws = wb.active
        ws.title = "Inventory"
        ws.append(headers)

        col_data_map = {
            'item': lambda r: f"{r['item_code']} - {r['item_name']}",
            'warehouse': lambda r: r['warehouse'] or '',
            'location': lambda r: r['location'] or '',
            'lot': lambda r: r['lot_number'] or '',
            'expiry': lambda r: r['expiry_date'] or '',
            'quantity': lambda r: r['quantity'],
            'reserved': lambda r: r['reserved_quantity'],
            'allocated': lambda r: r['allocated_quantity'],
            'status': lambda r: r['status'],
        }

        for row in rows:
            row_data = [col_data_map[c](row) for c in cols_to_export]
            ws.append(row_data)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         download_name=f'wms_inventory_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')

    @app.route('/wms/export/items')
    @wms_permission_required('reports', 'view')
    def wms_export_items():
        """Export items to Excel."""

        db = get_db()
        items = db.execute('''
            SELECT i.item_code, i.name, i.sku, i.barcode, i.part_number, i.oem_number,
                   b.name as brand, c.name as category, g.name as item_group,
                   i.unit_of_measure, i.weight_kg, i.volume_m3,
                   i.min_stock_level, i.reorder_point, i.safety_stock,
                   i.expiry_tracking, i.batch_tracking, i.lot_tracking, i.serial_tracking,
                   i.rotation_policy, i.selling_status, i.procurement_status,
                   i.is_active
            FROM wms_items i
            LEFT JOIN wms_item_brands b ON b.id = i.brand_id
            LEFT JOIN wms_item_categories c ON c.id = i.category_id
            LEFT JOIN wms_item_groups g ON g.id = i.group_id
            ORDER BY i.name
        ''').fetchall()

        wb = Workbook()
        ws = wb.active
        ws.title = "Items"

        headers = ['Item Code', 'Name', 'SKU', 'Barcode', 'Part Number', 'OEM Number',
                   'Brand', 'Category', 'Group', 'UOM', 'Weight (kg)', 'Volume (m3)',
                   'Min Stock', 'Reorder Point', 'Safety Stock',
                   'Expiry Track', 'Batch Track', 'Lot Track', 'Serial Track',
                   'Rotation Policy', 'Selling Status', 'Procurement Status', 'Active']
        ws.append(headers)

        for row in items:
            ws.append([
                row['item_code'], row['name'], row['sku'], row['barcode'],
                row['part_number'], row['oem_number'],
                row['brand'] or '', row['category'] or '', row['item_group'] or '',
                row['unit_of_measure'], row['weight_kg'], row['volume_m3'],
                row['min_stock_level'], row['reorder_point'], row['safety_stock'],
                'Yes' if row['expiry_tracking'] else 'No',
                'Yes' if row['batch_tracking'] else 'No',
                'Yes' if row['lot_tracking'] else 'No',
                'Yes' if row['serial_tracking'] else 'No',
                row['rotation_policy'], row['selling_status'], row['procurement_status'],
                'Yes' if row['is_active'] else 'No'
            ])

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         download_name=f'wms_items_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')

    # ============================================================
    # PRINT FORM TEMPLATES
    # ============================================================

    @app.route('/wms/print/grn/<int:receipt_id>')
    @wms_permission_required('receiving', 'view')
    def wms_print_grn(receipt_id):
        """Print Goods Receipt Note."""

        db = get_db()
        receipt = db.execute('''
            SELECT r.*, w.name as warehouse_name, s.name as supplier_name
            FROM wms_inbound_receipts r
            JOIN wms_warehouses w ON w.id = r.warehouse_id
            LEFT JOIN suppliers s ON s.id = r.supplier_id
            WHERE r.id = ?
        ''', (receipt_id,)).fetchone()

        lines = db.execute('''
            SELECT rl.*, i.item_code, i.name as item_name
            FROM wms_inbound_receipt_lines rl
            JOIN wms_items i ON i.id = rl.item_id
            WHERE rl.receipt_id = ?
        ''', (receipt_id,)).fetchall()

        title = f'Goods Receipt Note: {receipt["receipt_number"]}'
        return render_template('wms/print_grn.html',
            title=title,
            receipt=receipt,
            lines=lines
        )

    @app.route('/wms/print/pick-list/<int:order_id>')
    @wms_permission_required('picking', 'view')
    def wms_print_pick_list(order_id):
        """Print Pick List."""

        db = get_db()
        order = db.execute('SELECT * FROM wms_outbound_orders WHERE id = ?', (order_id,)).fetchone()
        pick_tasks = db.execute('''
            SELECT p.*, i.item_code, i.name as item_name, l.code as location_code
            FROM wms_pick_tasks p
            JOIN wms_items i ON i.id = p.item_id
            LEFT JOIN wms_locations l ON l.id = p.source_location_id
            WHERE p.order_id = ?
            ORDER BY p.pick_sequence
        ''', (order_id,)).fetchall()

        title = f'Pick List: {order["order_number"] if order else order_id}'
        return render_template('wms/print_pick_list.html',
            title=title,
            order=order,
            pick_tasks=pick_tasks
        )

    @app.route('/wms/outbound/orders/<int:order_id>')
    @wms_permission_required('picking', 'view')
    def wms_outbound_order_detail(order_id):
        """Operational outbound order detail used by waves, picking, packing, and dispatch."""
        db = get_db()
        order = db.execute('''
            SELECT o.*, w.name as warehouse_name, c.name as company_name,
                   cust.name as customer_name, u.username as created_by_name
            FROM wms_outbound_orders o
            JOIN wms_warehouses w ON w.id = o.warehouse_id
            LEFT JOIN wms_companies c ON c.id = o.company_id
            LEFT JOIN customers cust ON cust.id = o.customer_id
            LEFT JOIN users u ON u.id = o.created_by
            WHERE o.id = ?
        ''', (order_id,)).fetchone()
        if not order:
            flash('Outbound order not found', 'error')
            return redirect(url_for('wms_picking'))
        if not ensure_warehouse_allowed(order['warehouse_id']):
            flash('You do not have access to this warehouse order.', 'error')
            return redirect(url_for('wms_picking'))

        lines = db.execute('''
            SELECT l.*, i.item_code, i.name as item_name, lot.lot_number
            FROM wms_outbound_order_lines l
            JOIN wms_items i ON i.id = l.item_id
            LEFT JOIN wms_lots lot ON lot.id = l.reserved_lot_id
            WHERE l.order_id = ?
            ORDER BY COALESCE(l.line_number, l.id)
        ''', (order_id,)).fetchall()
        picks = db.execute('''
            SELECT p.*, i.item_code, i.name as item_name, loc.code as source_location_code,
                   u.username as assigned_to_name
            FROM wms_pick_tasks p
            JOIN wms_items i ON i.id = p.item_id
            LEFT JOIN wms_locations loc ON loc.id = p.source_location_id
            LEFT JOIN users u ON u.id = p.assigned_to
            WHERE p.order_id = ?
            ORDER BY COALESCE(p.pick_sequence, p.id)
        ''', (order_id,)).fetchall()
        packs = db.execute('''
            SELECT pk.*
            FROM wms_pack_tasks pk
            WHERE pk.order_id = ?
            ORDER BY pk.created_at DESC
        ''', (order_id,)).fetchall()
        shipments = db.execute('''
            SELECT s.*
            FROM wms_shipments s
            WHERE s.order_id = ?
            ORDER BY s.created_at DESC
        ''', (order_id,)).fetchall()

        return render_template('wms/outbound_order_detail.html',
            title=f'Outbound Order: {order["order_number"]}',
            order=order,
            lines=lines,
            picks=picks,
            packs=packs,
            shipments=shipments
        )

    @app.route('/wms/pickup/tasks/<int:task_id>')
    @wms_permission_required('picking', 'view')
    def wms_pickup_detail(task_id):
        """Pick task detail for legacy pickup links and zone picking drill-down."""
        db = get_db()
        task = db.execute('''
            SELECT p.*, i.item_code, i.name as item_name, o.order_number,
                   loc.code as source_location_code, loc.warehouse_id,
                   wh.name as warehouse_name, u.username as assigned_to_name,
                   cb.username as completed_by_name
            FROM wms_pick_tasks p
            JOIN wms_items i ON i.id = p.item_id
            LEFT JOIN wms_outbound_orders o ON o.id = p.order_id
            LEFT JOIN wms_locations loc ON loc.id = p.source_location_id
            LEFT JOIN wms_warehouses wh ON wh.id = loc.warehouse_id
            LEFT JOIN users u ON u.id = p.assigned_to
            LEFT JOIN users cb ON cb.id = p.completed_by
            WHERE p.id = ?
        ''', (task_id,)).fetchone()
        if not task:
            flash('Pick task not found', 'error')
            return redirect(url_for('wms_picking'))
        if task['warehouse_id'] and not ensure_warehouse_allowed(task['warehouse_id']):
            flash('You do not have access to this pick task.', 'error')
            return redirect(url_for('wms_picking'))

        return render_template('wms/pickup_detail.html',
            title=f'Pick Task: {task["task_number"]}',
            task=task
        )

    # ============================================================
    # WAVE MANAGEMENT
    # ============================================================

    @app.route('/wms/waves')
    @wms_permission_required('waves', 'view')
    def wms_waves():
        """Wave management - list all waves."""
        db = get_db()
        status = request.args.get('status', '')
        warehouse_id = request.args.get('warehouse_id', '')
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = 30

        query = '''
            SELECT w.*, wt.template_name, wh.name as warehouse_name,
                   u.username as created_by_name,
                   CASE
                       WHEN COALESCE(w.total_picks, 0) > 0
                       THEN (COALESCE(w.picks_completed, 0) * 100.0 / w.total_picks)
                       ELSE 0
                   END as progress
            FROM wms_waves w
            LEFT JOIN wms_wave_templates wt ON wt.id = w.template_id
            JOIN wms_warehouses wh ON wh.id = w.warehouse_id
            LEFT JOIN users u ON u.id = w.created_by
            WHERE 1=1
        '''
        params = []
        if status:
            query += " AND w.status = ?"
            params.append(status)
        if warehouse_id:
            query += " AND w.warehouse_id = ?"
            params.append(warehouse_id)
        if search:
            query += " AND (w.wave_number LIKE ? OR w.description LIKE ?)"
            params.append(f'%{search}%')
            params.append(f'%{search}%')

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY w.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        waves = db.execute(query, params).fetchall()

        # Wave stats
        stats = {}
        for s in ['PLANNED', 'RELEASED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']:
            stats[s.lower()] = db.execute(
                'SELECT COUNT(*) as cnt FROM wms_waves WHERE status = ?', (s,)).fetchone()['cnt']
        stats['total_orders'] = db.execute(
            'SELECT COUNT(*) as cnt FROM wms_wave_orders').fetchone()['cnt']

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        templates = db.execute('SELECT * FROM wms_wave_templates WHERE is_active = 1 ORDER BY template_name').fetchall()

        title = 'Wave Management'
        return render_template('wms/waves.html',
            title=title,
            waves=waves,
            templates=templates,
            stats=stats,
            warehouses=warehouses,
            status=status,
            warehouse_id=warehouse_id,
            search=search,
            page=page,
            per_page=per_page,
            total_count=total,
            total_pages=(total + per_page - 1) // per_page if total > 0 else 1
        )

    @app.route('/wms/waves/new', methods=['GET', 'POST'])
    @wms_permission_required('waves', 'create')
    def wms_waves_new():
        """Create a new wave."""
        db = get_db()

        if request.method == 'POST':
            if not validate_wms_csrf():
                flash('CSRF validation failed. Please refresh the page and try again.', 'error')
                return redirect(url_for('wms_waves_new'))
            warehouse_id = request.form.get('warehouse_id')
            template_id = request.form.get('template_id') or None
            priority = int(request.form.get('priority', 5))
            description = request.form.get('description', '')
            picking_strategy = request.form.get('picking_strategy', 'WAVE')
            allocation_rule = request.form.get('allocation_rule', 'FIFO')
            max_picks = int(request.form.get('max_picks_per_operator', 50))
            auto_assign = 1 if request.form.get('auto_assign') else 0
            release_type = request.form.get('release_type', 'IMMEDIATE')
            scheduled_time = request.form.get('scheduled_release_time') or None

            template = db.execute('SELECT * FROM wms_wave_templates WHERE id = ?', (template_id,)).fetchone() if template_id else None
            if template and not picking_strategy:
                picking_strategy = template['picking_strategy']
            if template and not allocation_rule:
                allocation_rule = template['allocation_rule']
            if template and not max_picks:
                max_picks = template['max_picks_per_operator'] or 50

            wave_number = generate_wms_code('WAVE')

            result = db.execute('''
                INSERT INTO wms_waves (wave_number, template_id, warehouse_id, description,
                    picking_strategy, allocation_rule, max_picks_per_operator, auto_assign_tasks,
                    release_type, scheduled_release_time, status, priority, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PLANNED', ?, ?)
            ''', (wave_number, template_id, warehouse_id, description, picking_strategy,
                  allocation_rule, max_picks, auto_assign, release_type, scheduled_time,
                  priority, session.get('user_id')))
            db.commit()

            flash(f'Wave {wave_number} created successfully', 'success')
            return redirect(url_for('wms_waves'))

        # GET
        template_id = request.args.get('template_id')
        template = db.execute('SELECT * FROM wms_wave_templates WHERE id = ?', (template_id,)).fetchone() if template_id else None
        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        templates = db.execute('SELECT * FROM wms_wave_templates WHERE is_active = 1 ORDER BY template_name').fetchall()
        wave_number = generate_wms_code('WAVE')

        title = 'Create Wave'
        return render_template('wms/wave_form.html',
            title=title,
            templates=templates,
            warehouses=warehouses,
            template=template,
            wave_number=wave_number
        )

    @app.route('/wms/wave/<int:wave_id>')
    @wms_permission_required('waves', 'view')
    def wms_wave_detail(wave_id):
        """View wave details."""
        db = get_db()

        wave = db.execute('''
            SELECT w.*, wt.template_name, wh.name as warehouse_name,
                   u.username as created_by_name
            FROM wms_waves w
            LEFT JOIN wms_wave_templates wt ON wt.id = w.template_id
            JOIN wms_warehouses wh ON wh.id = w.warehouse_id
            LEFT JOIN users u ON u.id = w.created_by
            WHERE w.id = ?
        ''', (wave_id,)).fetchone()

        if not wave:
            flash('Wave not found', 'error')
            return redirect(url_for('wms_waves'))

        orders = db.execute('''
            SELECT o.*, wo.added_at,
                   c.name as customer_name,
                   (SELECT COUNT(*) FROM wms_outbound_order_lines WHERE order_id = o.id) as line_count,
                   (SELECT COUNT(*) FROM wms_pick_tasks WHERE order_id = o.id) as pick_count
            FROM wms_wave_orders wo
            JOIN wms_outbound_orders o ON o.id = wo.order_id
            LEFT JOIN customers c ON c.id = o.customer_id
            WHERE wo.wave_id = ?
        ''', (wave_id,)).fetchall()

        picks = db.execute('''
            SELECT p.*, i.item_code, i.name as item_name,
                   l.code as source_location, u.username as assigned_to_name
            FROM wms_pick_tasks p
            JOIN wms_items i ON i.id = p.item_id
            LEFT JOIN wms_locations l ON l.id = p.source_location_id
            LEFT JOIN users u ON u.id = p.assigned_to
            WHERE p.order_id IN (SELECT order_id FROM wms_wave_orders WHERE wave_id = ?)
            ORDER BY p.created_at
        ''', (wave_id,)).fetchall()

        progress = 0
        if wave['total_picks'] > 0:
            progress = (wave['picks_completed'] / wave['total_picks']) * 100

        title = f'Wave {wave["wave_number"]}'
        return render_template('wms/wave_detail.html',
            title=title,
            wave=wave,
            orders=orders,
            picks=picks,
            progress=progress
        )

    @app.route('/wms/wave/<int:wave_id>/release', methods=['POST'])
    @wms_permission_required('waves', 'release')
    def wms_wave_release(wave_id):
        """Release a wave."""
        db = get_db()
        if not validate_wms_csrf():
            flash('CSRF validation failed. Please refresh the page and try again.', 'error')
            return redirect(url_for('wms_wave_detail', wave_id=wave_id))

        wave = db.execute('SELECT * FROM wms_waves WHERE id = ?', (wave_id,)).fetchone()
        if not wave:
            flash('Wave not found', 'error')
            return redirect(url_for('wms_waves'))

        if wave['status'] not in ['PLANNED']:
            flash(f'Cannot release wave in status {wave["status"]}', 'error')
            return redirect(url_for('wms_wave_detail', wave_id=wave_id))

        # Get orders in wave
        wave_orders = db.execute('SELECT order_id FROM wms_wave_orders WHERE wave_id = ?', (wave_id,)).fetchall()

        for wo in wave_orders:
            # Update order status to PICKING
            db.execute('''
                UPDATE wms_outbound_orders SET status = 'PICKING' WHERE id = ?
            ''', (wo['order_id'],))

        # Update wave status
        db.execute('''
            UPDATE wms_waves SET status = 'RELEASED', released_by = ?, released_at = ?
            WHERE id = ?
        ''', (session.get('user_id'), datetime.now().isoformat(), wave_id))
        db.commit()

        log_wms_audit('WAVE_RELEASED', 'wms_waves', wave_id, {'wave_number': wave['wave_number']})
        create_wms_notification(session.get('user_id'), f'Wave {wave["wave_number"]} Released',
            f'Wave {wave["wave_number"]} has been released with {wave["order_count"]} orders',
            'success', 'wave', wave_id)

        flash(f'Wave {wave["wave_number"]} released successfully', 'success')
        return redirect(url_for('wms_wave_detail', wave_id=wave_id))

    @app.route('/wms/wave/<int:wave_id>/cancel', methods=['POST'])
    @wms_permission_required('waves', 'cancel')
    def wms_wave_cancel(wave_id):
        """Cancel a wave."""
        db = get_db()
        if not validate_wms_csrf():
            flash('CSRF validation failed. Please refresh the page and try again.', 'error')
            return redirect(url_for('wms_wave_detail', wave_id=wave_id))

        wave = db.execute('SELECT * FROM wms_waves WHERE id = ?', (wave_id,)).fetchone()
        if not wave:
            flash('Wave not found', 'error')
            return redirect(url_for('wms_waves'))

        if wave['status'] in ['COMPLETED', 'CANCELLED']:
            flash(f'Cannot cancel wave in status {wave["status"]}', 'error')
            return redirect(url_for('wms_wave_detail', wave_id=wave_id))

        cancel_reason = request.form.get('cancel_reason', 'User cancelled')

        # Revert order statuses
        wave_orders = db.execute('SELECT order_id FROM wms_wave_orders WHERE wave_id = ?', (wave_id,)).fetchall()
        for wo in wave_orders:
            db.execute('''
                UPDATE wms_outbound_orders SET status = 'ALLOCATED' WHERE id = ?
            ''', (wo['order_id'],))

        db.execute('''
            UPDATE wms_waves SET status = 'CANCELLED', cancelled_by = ?, cancelled_at = ?, cancel_reason = ?
            WHERE id = ?
        ''', (session.get('user_id'), datetime.now().isoformat(), cancel_reason, wave_id))
        db.commit()

        log_wms_audit('WAVE_CANCELLED', 'wms_waves', wave_id, {'wave_number': wave['wave_number'], 'reason': cancel_reason})
        flash(f'Wave {wave["wave_number"]} cancelled', 'warning')
        return redirect(url_for('wms_wave_detail', wave_id=wave_id))

    @app.route('/wms/wave/<int:wave_id>/complete', methods=['POST'])
    @wms_permission_required('waves', 'complete')
    def wms_wave_complete(wave_id):
        """Complete a wave."""
        db = get_db()
        if not validate_wms_csrf():
            flash('CSRF validation failed. Please refresh the page and try again.', 'error')
            return redirect(url_for('wms_wave_detail', wave_id=wave_id))

        wave = db.execute('SELECT * FROM wms_waves WHERE id = ?', (wave_id,)).fetchone()
        if not wave:
            flash('Wave not found', 'error')
            return redirect(url_for('wms_waves'))

        if wave['status'] not in ['RELEASED', 'IN_PROGRESS']:
            flash(f'Cannot complete wave in status {wave["status"]}', 'error')
            return redirect(url_for('wms_wave_detail', wave_id=wave_id))

        db.execute('''
            UPDATE wms_waves SET status = 'COMPLETED', completed_by = ?, completed_at = ?
            WHERE id = ?
        ''', (session.get('user_id'), datetime.now().isoformat(), wave_id))
        db.commit()

        log_wms_audit('WAVE_COMPLETED', 'wms_waves', wave_id, {'wave_number': wave['wave_number']})
        flash(f'Wave {wave["wave_number"]} completed', 'success')
        return redirect(url_for('wms_wave_detail', wave_id=wave_id))

    @app.route('/wms/waves/templates')
    @wms_permission_required('waves', 'view')
    def wms_wave_templates():
        """Wave templates management."""
        db = get_db()

        templates = db.execute('SELECT * FROM wms_wave_templates ORDER BY template_name').fetchall()

        title = 'Wave Templates'
        return render_template('wms/wave_templates.html',
            title=title,
            templates=templates
        )

    @app.route('/wms/waves/templates/new', methods=['GET', 'POST'])
    @wms_permission_required('waves', 'create')
    def wms_wave_templates_new():
        """Create wave template."""
        db = get_db()

        if request.method == 'POST':
            if not validate_wms_csrf():
                flash('CSRF validation failed. Please refresh the page and try again.', 'error')
                return redirect(url_for('wms_wave_templates_new'))
            template_name = request.form.get('template_name')
            description = request.form.get('description', '')
            picking_strategy = request.form.get('picking_strategy', 'WAVE')
            allocation_rule = request.form.get('allocation_rule', 'FIFO')
            max_picks = int(request.form.get('max_picks_per_operator', 50))
            auto_assign = 1 if request.form.get('auto_assign') else 0
            release_type = request.form.get('release_type', 'IMMEDIATE')

            db.execute('''
                INSERT INTO wms_wave_templates (template_name, description, picking_strategy,
                    allocation_rule, max_picks_per_operator, auto_assign_tasks, release_type, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (template_name, description, picking_strategy, allocation_rule,
                  max_picks, auto_assign, release_type, session.get('user_id')))
            db.commit()

            flash(f'Template {template_name} created', 'success')
            return redirect(url_for('wms_wave_templates'))

        title = 'Create Wave Template'
        return render_template('wms/wave_template_form.html', title=title, template=None)

    @app.route('/wms/waves/templates/<int:template_id>/edit', methods=['GET', 'POST'])
    @wms_permission_required('waves', 'edit')
    def wms_wave_templates_edit(template_id):
        """Edit an existing wave template."""
        db = get_db()
        template = db.execute('SELECT * FROM wms_wave_templates WHERE id = ?', (template_id,)).fetchone()
        if not template:
            flash('Wave template not found', 'error')
            return redirect(url_for('wms_wave_templates'))

        if request.method == 'POST':
            if not validate_wms_csrf():
                flash('CSRF validation failed. Please refresh the page and try again.', 'error')
                return redirect(url_for('wms_wave_templates_edit', template_id=template_id))
            template_name = request.form.get('template_name')
            description = request.form.get('description', '')
            picking_strategy = request.form.get('picking_strategy', 'WAVE')
            allocation_rule = request.form.get('allocation_rule', 'FIFO')
            max_picks = parse_positive_int(request.form.get('max_picks_per_operator'), 50) or 50
            auto_assign = 1 if request.form.get('auto_assign') else 0
            release_type = request.form.get('release_type', 'IMMEDIATE')
            is_active = 1 if request.form.get('is_active') else 0

            db.execute('''
                UPDATE wms_wave_templates
                SET template_name = ?, description = ?, picking_strategy = ?,
                    allocation_rule = ?, max_picks_per_operator = ?,
                    auto_assign_tasks = ?, release_type = ?, is_active = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (template_name, description, picking_strategy, allocation_rule,
                  max_picks, auto_assign, release_type, is_active, template_id))
            db.commit()

            log_wms_audit('WAVE_TEMPLATE_UPDATED', 'wms_wave_templates', template_id, {
                'template_name': template_name,
                'before': dict(template),
                'after': {
                    'template_name': template_name,
                    'description': description,
                    'picking_strategy': picking_strategy,
                    'allocation_rule': allocation_rule,
                    'max_picks_per_operator': max_picks,
                    'auto_assign_tasks': auto_assign,
                    'release_type': release_type,
                    'is_active': is_active
                }
            })
            flash(f'Template {template_name} updated', 'success')
            return redirect(url_for('wms_wave_templates'))

        title = 'Edit Wave Template'
        return render_template('wms/wave_template_form.html', title=title, template=template)

    # ============================================================
    # RF / BARCODE / SCAN
    # ============================================================

    @app.route('/wms/rf-scan')
    @wms_permission_required('rf_scan', 'view')
    def wms_rf_scan():
        """RF Scan Workbench."""
        db = get_db()
        title = 'RF Scan Workbench'
        return render_template('wms/rf_scan.html',
            title=title,
            connection_status='READY'
        )

    @app.route('/wms/rf/scan-history')
    @wms_permission_required('rf_scan', 'view')
    def wms_rf_scan_history():
        """Scan history log."""
        db = get_db()
        page = int(request.args.get('page', 1))
        per_page = 50

        scans = db.execute('''
            SELECT s.*, u.username as operator_name
            FROM wms_rf_scan_log s
            LEFT JOIN users u ON u.id = s.operator_id
            ORDER BY s.scan_time DESC LIMIT ? OFFSET ?
        ''', (per_page, (page-1)*per_page)).fetchall()

        title = 'Scan History'
        return render_template('wms/rf_scan_history.html',
            title=title,
            scans=scans,
            page=page,
            per_page=per_page
        )

    # ============================================================
    # VOICE PICKING
    # ============================================================

    @app.route('/wms/voice-picking')
    @wms_permission_required('voice_picking', 'view')
    def wms_voice_picking():
        """Voice picking workbench - main interface."""
        db = get_db()
        operator_id = session.get('user_id')

        active_task = db.execute('''
            SELECT t.*, i.item_code, i.name as item_name, i.barcode,
                   sl.code as source_location, NULL as dest_location,
                   w.name as warehouse_name
            FROM wms_pick_tasks t
            JOIN wms_items i ON i.id = t.item_id
            LEFT JOIN wms_locations sl ON sl.id = t.source_location_id
            JOIN wms_warehouses w ON w.id = sl.warehouse_id
            WHERE t.status = 'ASSIGNED' AND t.assigned_to = ?
            ORDER BY t.priority DESC, t.created_at
            LIMIT 1
        ''', (operator_id,)).fetchone()

        config = {}
        configs = db.execute('SELECT config_key, config_value FROM wms_voice_config WHERE is_active = 1').fetchall()
        for c in configs:
            config[c['config_key']] = c['config_value']

        title = 'Voice Picking'
        return render_template('wms/voice_picking.html',
            title=title,
            active_task=active_task,
            config=config,
            operator_id=operator_id
        )

    @app.route('/wms/voice-picking/start/<int:task_id>', methods=['POST'])
    @wms_permission_required('voice_picking', 'edit')
    def wms_voice_picking_start(task_id):
        """Start voice picking for a task."""
        db = get_db()
        import time
        start_time = time.time()

        task = db.execute('SELECT * FROM wms_pick_tasks WHERE id = ?', (task_id,)).fetchone()
        if not task:
            return jsonify({'success': False, 'error': 'Task not found'})

        item = db.execute('SELECT * FROM wms_items WHERE id = ?', (task['item_id'],)).fetchone()
        location = db.execute('SELECT * FROM wms_locations WHERE id = ?', (task['source_location_id'],)).fetchone()

        instruction = f"Go to location {location['code'] if location else 'Unknown'}. Pick {int(task['quantity'])} units of item {item['item_code'] if item else 'Unknown'}."

        decision_time_ms = int((time.time() - start_time) * 1000)

        db.execute('''
            INSERT INTO wms_voice_pick_log (task_id, operator_id, instruction_text, response_time_ms)
            VALUES (?, ?, ?, ?)
        ''', (task_id, session.get('user_id'), instruction, decision_time_ms))
        db.execute('UPDATE wms_pick_tasks SET status = "IN_PROGRESS" WHERE id = ?', (task_id,))
        db.commit()

        return jsonify({
            'success': True,
            'instruction': instruction,
            'task_id': task_id,
            'item_code': item['item_code'] if item else None,
            'quantity': int(task['quantity']),
            'location_code': location['code'] if location else None
        })

    @app.route('/wms/voice-picking/confirm', methods=['POST'])
    @wms_permission_required('voice_picking', 'edit')
    def wms_voice_picking_confirm():
        """Confirm voice pick completion."""
        db = get_db()
        import time
        start_time = time.time()

        data = request.get_json()
        task_id = data.get('task_id')
        recognized_command = data.get('recognized_command', '')
        is_correct = data.get('is_correct', 0)
        error_type = data.get('error_type')

        db.execute('''
            INSERT INTO wms_voice_pick_log (task_id, operator_id, recognized_command, is_correct, error_type, retry_count)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (task_id, session.get('user_id'), recognized_command, is_correct, error_type, 0))

        if is_correct:
            db.execute('UPDATE wms_pick_tasks SET status = "COMPLETED" WHERE id = ?', (task_id,))

        db.commit()

        return jsonify({
            'success': True,
            'response_time_ms': int((time.time() - start_time) * 1000)
        })

    @app.route('/wms/voice-picking/report')
    @wms_permission_required('voice_picking', 'view')
    def wms_voice_picking_report():
        """Voice picking performance report."""
        db = get_db()

        stats = db.execute('''
            SELECT
                COUNT(*) as total_picks,
                SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_picks,
                SUM(CASE WHEN is_correct = 0 THEN 1 ELSE 0 END) as error_picks,
                AVG(response_time_ms) as avg_response_time,
                SUM(retry_count) as total_retries
            FROM wms_voice_pick_log
            WHERE timestamp >= datetime('now', '-7 days')
        ''').fetchone()

        operator_stats = db.execute('''
            SELECT u.username, u.id,
                COUNT(*) as total_picks,
                SUM(CASE WHEN v.is_correct = 1 THEN 1 ELSE 0 END) as correct_picks,
                AVG(v.response_time_ms) as avg_time
            FROM wms_voice_pick_log v
            JOIN users u ON u.id = v.operator_id
            WHERE v.timestamp >= datetime('now', '-7 days')
            GROUP BY u.id
            ORDER BY total_picks DESC
        ''').fetchall()

        trend_rows = db.execute('''
            SELECT date(timestamp) as activity_date,
                   COUNT(*) as total_picks,
                   SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct_picks,
                   AVG(response_time_ms) as avg_response_time
            FROM wms_voice_pick_log
            WHERE timestamp >= datetime('now', '-7 days')
            GROUP BY date(timestamp)
            ORDER BY activity_date
        ''').fetchall()

        title = 'Voice Picking Report'
        return render_template('wms/voice_picking_report.html',
            title=title,
            stats=stats,
            operator_stats=operator_stats,
            trend_rows=trend_rows
        )

    @app.route('/wms/voice-picking/config', methods=['GET', 'POST'])
    @wms_permission_required('voice_picking', 'edit')
    def wms_voice_picking_config():
        """Configure voice picking settings."""
        db = get_db()

        if request.method == 'POST':
            config_key = request.form.get('config_key')
            config_value = request.form.get('config_value')
            language = request.form.get('language', 'en')

            existing = db.execute('SELECT id FROM wms_voice_config WHERE config_key = ?', (config_key,)).fetchone()
            if existing:
                db.execute('UPDATE wms_voice_config SET config_value = ?, language = ?, updated_at = CURRENT_TIMESTAMP WHERE config_key = ?',
                           (config_value, language, config_key))
            else:
                db.execute('INSERT INTO wms_voice_config (config_key, config_value, language) VALUES (?, ?, ?)',
                           (config_key, config_value, language))
            db.commit()
            flash('Configuration updated!', 'success')
            return redirect(url_for('wms_voice_picking_config'))

        configs = db.execute('SELECT * FROM wms_voice_config ORDER BY config_key').fetchall()
        title = 'Voice Picking Config'
        return render_template('wms/voice_picking_config.html',
            title=title,
            configs=configs
        )

    # ============================================================
    # EDI / IDOC INTEGRATION
    # ============================================================

    @app.route('/wms/edi/dashboard')
    @wms_permission_required('edi', 'view')
    def wms_edi_dashboard():
        """EDI Dashboard overview."""
        db = get_db()

        stats = {
            'pending_outbound': db.execute("SELECT COUNT(*) as cnt FROM wms_outbound_idocs WHERE status = 'PENDING'").fetchone()['cnt'],
            'sent_today': db.execute("SELECT COUNT(*) as cnt FROM wms_outbound_idocs WHERE DATE(sent_at) = DATE('now')").fetchone()['cnt'],
            'received_today': db.execute("SELECT COUNT(*) as cnt FROM wms_inbound_idocs WHERE DATE(created_at) = DATE('now')").fetchone()['cnt'],
            'errors': db.execute("SELECT COUNT(*) as cnt FROM wms_outbound_idocs WHERE status = 'ERROR'").fetchone()['cnt'],
            'active_partners': db.execute("SELECT COUNT(*) as cnt FROM wms_edi_partners WHERE is_active = 1").fetchone()['cnt'],
        }

        recent_outbound = db.execute('''
            SELECT o.*, p.partner_name
            FROM wms_outbound_idocs o
            JOIN wms_edi_partners p ON p.id = o.partner_id
            ORDER BY o.created_at DESC LIMIT 10
        ''').fetchall()

        recent_inbound = db.execute('''
            SELECT i.*, p.partner_name
            FROM wms_inbound_idocs i
            JOIN wms_edi_partners p ON p.id = i.partner_id
            ORDER BY i.created_at DESC LIMIT 10
        ''').fetchall()

        title = 'EDI Dashboard'
        return render_template('wms/edi_dashboard.html',
            title=title,
            stats=stats,
            recent_outbound=recent_outbound,
            recent_inbound=recent_inbound
        )

    @app.route('/wms/edi/partners')
    @wms_permission_required('edi', 'view')
    def wms_edi_partners():
        """List EDI partners."""
        db = get_db()
        partners = db.execute('SELECT * FROM wms_edi_partners ORDER BY partner_name').fetchall()
        title = 'EDI Partners'
        return render_template('wms/edi_partners.html',
            title=title,
            partners=partners
        )

    @app.route('/wms/edi/partners/new', methods=['GET', 'POST'])
    @wms_permission_required('edi', 'create')
    def wms_edi_partners_new():
        """Create EDI partner."""
        db = get_db()

        if request.method == 'POST':
            try:
                partner_name = request.form.get('partner_name')
                partner_type = request.form.get('partner_type')
                edi_protocol = request.form.get('edi_protocol')
                endpoint_url = request.form.get('endpoint_url')
                username = request.form.get('username')
                password = request.form.get('password')
                partner_code = request.form.get('partner_code')
                contact_email = request.form.get('contact_email')
                is_active = 1 if request.form.get('is_active') else 0

                if password:
                    import hashlib
                    password_encrypted = hashlib.sha256(password.encode()).hexdigest()
                else:
                    password_encrypted = None

                db.execute('''
                    INSERT INTO wms_edi_partners
                    (partner_name, partner_type, edi_protocol, endpoint_url, username, password_encrypted,
                     partner_code, contact_email, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (partner_name, partner_type, edi_protocol, endpoint_url, username, password_encrypted,
                      partner_code, contact_email, is_active))
                db.commit()
                log_wms_audit('CREATE', 'EDI_PARTNER', db.execute('SELECT last_insert_rowid() as id').fetchone()['id'])
                flash('EDI Partner created successfully!', 'success')
                return redirect(url_for('wms_edi_partners'))
            except Exception as e:
                import traceback
                print(f"WMS EDI partner create error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error creating partner. Please try again.', 'error')

        title = 'New EDI Partner'
        return render_template('wms/edi_partner_form.html',
            title=title,
            partner=None
        )

    @app.route('/wms/edi/partners/<int:partner_id>', methods=['GET', 'POST'])
    @wms_permission_required('edi', 'edit')
    def wms_edi_partners_edit(partner_id):
        """Edit EDI partner."""
        db = get_db()
        partner = db.execute('SELECT * FROM wms_edi_partners WHERE id = ?', (partner_id,)).fetchone()

        if not partner:
            flash('Partner not found.', 'error')
            return redirect(url_for('wms_edi_partners'))

        if request.method == 'POST':
            try:
                partner_name = request.form.get('partner_name')
                partner_type = request.form.get('partner_type')
                edi_protocol = request.form.get('edi_protocol')
                endpoint_url = request.form.get('endpoint_url')
                username = request.form.get('username')
                password = request.form.get('password')
                partner_code = request.form.get('partner_code')
                contact_email = request.form.get('contact_email')
                is_active = 1 if request.form.get('is_active') else 0

                if password:
                    import hashlib
                    password_encrypted = hashlib.sha256(password.encode()).hexdigest()
                    db.execute('''
                        UPDATE wms_edi_partners SET
                            partner_name = ?, partner_type = ?, edi_protocol = ?, endpoint_url = ?,
                            username = ?, password_encrypted = ?, partner_code = ?, contact_email = ?,
                            is_active = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (partner_name, partner_type, edi_protocol, endpoint_url, username, password_encrypted,
                          partner_code, contact_email, is_active, partner_id))
                else:
                    db.execute('''
                        UPDATE wms_edi_partners SET
                            partner_name = ?, partner_type = ?, edi_protocol = ?, endpoint_url = ?,
                            username = ?, partner_code = ?, contact_email = ?,
                            is_active = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    ''', (partner_name, partner_type, edi_protocol, endpoint_url, username,
                          partner_code, contact_email, is_active, partner_id))
                db.commit()
                log_wms_audit('UPDATE', 'EDI_PARTNER', partner_id)
                flash('EDI Partner updated successfully!', 'success')
                return redirect(url_for('wms_edi_partners'))
            except Exception as e:
                import traceback
                print(f"WMS EDI partner update error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error updating partner. Please try again.', 'error')

        title = 'Edit EDI Partner'
        return render_template('wms/edi_partner_form.html',
            title=title,
            partner=partner
        )

    @app.route('/wms/edi/outbound')
    @wms_permission_required('edi', 'view')
    def wms_edi_outbound():
        """List outbound IDocs."""
        db = get_db()
        status = request.args.get('status', '')
        partner_id = request.args.get('partner_id', '')

        query = '''
            SELECT o.*, p.partner_name
            FROM wms_outbound_idocs o
            JOIN wms_edi_partners p ON p.id = o.partner_id
            WHERE 1=1
        '''
        params = []
        if status:
            query += " AND o.status = ?"
            params.append(status)
        if partner_id:
            query += " AND o.partner_id = ?"
            params.append(partner_id)

        idocs = db.execute(query + ' ORDER BY o.created_at DESC LIMIT 100', params).fetchall()
        partners = db.execute('SELECT * FROM wms_edi_partners WHERE is_active = 1 ORDER BY partner_name').fetchall()

        title = 'Outbound IDocs'
        return render_template('wms/edi_outbound.html',
            title=title,
            idocs=idocs,
            partners=partners,
            status=status,
            partner_id=partner_id
        )

    @app.route('/wms/edi/inbound')
    @wms_permission_required('edi', 'view')
    def wms_edi_inbound():
        """List inbound IDocs."""
        db = get_db()
        status = request.args.get('status', '')
        partner_id = request.args.get('partner_id', '')

        query = '''
            SELECT i.*, p.partner_name
            FROM wms_inbound_idocs i
            JOIN wms_edi_partners p ON p.id = i.partner_id
            WHERE 1=1
        '''
        params = []
        if status:
            query += " AND i.status = ?"
            params.append(status)
        if partner_id:
            query += " AND i.partner_id = ?"
            params.append(partner_id)

        idocs = db.execute(query + ' ORDER BY i.created_at DESC LIMIT 100', params).fetchall()
        partners = db.execute('SELECT * FROM wms_edi_partners WHERE is_active = 1 ORDER BY partner_name').fetchall()

        title = 'Inbound IDocs'
        return render_template('wms/edi_inbound.html',
            title=title,
            idocs=idocs,
            partners=partners,
            status=status,
            partner_id=partner_id
        )

    @app.route('/wms/edi/mappings')
    @wms_permission_required('edi', 'view')
    def wms_edi_mappings():
        """List EDI mappings."""
        db = get_db()
        mappings = db.execute('SELECT * FROM wms_edi_mappings ORDER BY message_type').fetchall()
        title = 'EDI Mappings'
        return render_template('wms/edi_mappings.html',
            title=title,
            mappings=mappings
        )

    @app.route('/wms/edi/mappings/new', methods=['GET', 'POST'])
    @wms_permission_required('edi', 'create')
    def wms_edi_mappings_new():
        """Create EDI mapping."""
        db = get_db()

        if request.method == 'POST':
            try:
                mapping_name = request.form.get('mapping_name')
                message_type = request.form.get('message_type')
                direction = request.form.get('direction')
                field_mappings_json = request.form.get('field_mappings_json', '{}')
                transformation_rules_json = request.form.get('transformation_rules_json', '{}')

                db.execute('''
                    INSERT INTO wms_edi_mappings
                    (mapping_name, message_type, direction, field_mappings_json, transformation_rules_json, created_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (mapping_name, message_type, direction, field_mappings_json, transformation_rules_json, session.get('user_id')))
                db.commit()
                flash('EDI Mapping created successfully!', 'success')
                return redirect(url_for('wms_edi_mappings'))
            except Exception as e:
                import traceback
                print(f"WMS EDI mapping create error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error creating mapping. Please try again.', 'error')

        title = 'New EDI Mapping'
        return render_template('wms/edi_mapping_form.html',
            title=title,
            mapping=None
        )

    @app.route('/wms/edi/mappings/edit/<int:mapping_id>', methods=['GET', 'POST'])
    @wms_permission_required('edi', 'edit')
    def wms_edi_mappings_edit(mapping_id):
        """Edit EDI mapping."""
        db = get_db()
        mapping = db.execute('SELECT * FROM wms_edi_mappings WHERE id = ?', (mapping_id,)).fetchone()
        if not mapping:
            flash('Mapping not found', 'error')
            return redirect(url_for('wms_edi_mappings'))

        if request.method == 'POST':
            try:
                mapping_name = request.form.get('mapping_name')
                message_type = request.form.get('message_type')
                direction = request.form.get('direction')
                field_mappings_json = request.form.get('field_mappings_json', '{}')
                transformation_rules_json = request.form.get('transformation_rules_json', '{}')

                db.execute('''
                    UPDATE wms_edi_mappings SET
                    mapping_name = ?, message_type = ?, direction = ?,
                    field_mappings_json = ?, transformation_rules_json = ?
                    WHERE id = ?
                ''', (mapping_name, message_type, direction, field_mappings_json, transformation_rules_json, mapping_id))
                db.commit()
                flash('EDI Mapping updated successfully!', 'success')
                return redirect(url_for('wms_edi_mappings'))
            except Exception as e:
                import traceback
                print(f"WMS EDI mapping update error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error updating mapping. Please try again.', 'error')

        title = 'Edit EDI Mapping'
        return render_template('wms/edi_mapping_form.html',
            title=title,
            mapping=mapping
        )

    @app.route('/wms/edi/mappings/delete/<int:mapping_id>', methods=['POST'])
    @wms_permission_required('edi', 'delete')
    def wms_edi_mappings_delete(mapping_id):
        """Delete EDI mapping."""
        db = get_db()
        try:
            db.execute('DELETE FROM wms_edi_mappings WHERE id = ?', (mapping_id,))
            db.commit()
            flash('EDI Mapping deleted successfully!', 'success')
        except Exception as e:
            import traceback
            print(f"WMS EDI mapping delete error: {e}")
            traceback.print_exc()
            db.rollback()
            flash('Error deleting mapping. Please try again.', 'error')
        return redirect(url_for('wms_edi_mappings'))

    @app.route('/wms/edi/idoc/<int:idoc_id>')
    @wms_permission_required('edi', 'view')
    def wms_edi_idoc_detail(idoc_id):
        """View IDoc detail."""
        db = get_db()
        idoc = db.execute('SELECT * FROM wms_outbound_idocs WHERE id = ?', (idoc_id,)).fetchone()
        if not idoc:
            idoc = db.execute('SELECT * FROM wms_inbound_idocs WHERE id = ?', (idoc_id,)).fetchone()
        if not idoc:
            flash('IDoc not found', 'error')
            return redirect(url_for('wms_edi_dashboard'))

        partner = db.execute('SELECT * FROM wms_edi_partners WHERE id = ?', (idoc['partner_id'],)).fetchone() if idoc.get('partner_id') else None
        is_outbound = 'idoc_number' in dict(idoc.keys())
        title = f'IDoc {idoc.get("idoc_number", idoc.get("id"))}'

        return render_template('wms/edi_idoc_detail.html',
            title=title,
            idoc=idoc,
            partner=partner,
            is_outbound=is_outbound
        )

    @app.route('/wms/edi/resend/<int:idoc_id>', methods=['POST'])
    @wms_permission_required('edi', 'edit')
    def wms_edi_resend(idoc_id):
        """Resend outbound IDoc."""
        db = get_db()
        try:
            idoc = db.execute('SELECT * FROM wms_outbound_idocs WHERE id = ?', (idoc_id,)).fetchone()
            if not idoc:
                return jsonify({'success': False, 'error': 'IDoc not found'})

            partner = db.execute('SELECT * FROM wms_edi_partners WHERE id = ?', (idoc['partner_id'],)).fetchone()

            db.execute('''
                UPDATE wms_outbound_idocs SET status = 'PENDING', sent_at = NULL
                WHERE id = ?
            ''', (idoc_id,))
            db.execute('''
                INSERT INTO wms_edi_audit_log (idoc_id, action_type, old_status, new_status, details, created_by)
                VALUES (?, 'RESEND', ?, 'PENDING', ?, ?)
            ''', (idoc_id, idoc['status'], f'Resend to {partner["partner_name"]}', session.get('user_id')))
            db.commit()

            flash('IDoc queued for resend', 'success')
        except Exception as e:
            import traceback
            print(f"WMS IDoc resend error: {e}")
            traceback.print_exc()
            db.rollback()
            flash('Error resending IDoc. Please try again.', 'error')
        return redirect(url_for('wms_edi_outbound'))

    @app.route('/wms/edi/process/<int:idoc_id>', methods=['POST'])
    @wms_permission_required('edi', 'edit')
    def wms_edi_process(idoc_id):
        """Process inbound IDoc."""
        db = get_db()
        try:
            idoc = db.execute('SELECT * FROM wms_inbound_idocs WHERE id = ?', (idoc_id,)).fetchone()
            if not idoc:
                flash('IDoc not found', 'error')
                return redirect(url_for('wms_edi_inbound'))

            db.execute('''
                UPDATE wms_inbound_idocs SET status = 'PROCESSED', processed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (idoc_id,))
            db.execute('''
                INSERT INTO wms_edi_audit_log (idoc_id, action_type, old_status, new_status, details, created_by)
                VALUES (?, 'PROCESS', ?, 'PROCESSED', ?, ?)
            ''', (idoc_id, idoc['status'], 'Manually processed', session.get('user_id')))
            db.commit()

            flash('IDoc processed successfully!', 'success')
        except Exception as e:
            import traceback
            print(f"WMS IDoc process error: {e}")
            traceback.print_exc()
            db.rollback()
            flash('Error processing IDoc. Please try again.', 'error')
        return redirect(url_for('wms_edi_inbound'))

    @app.route('/wms/edi/send-test/<int:idoc_id>', methods=['POST'])
    @wms_permission_required('edi', 'edit')
    def wms_edi_send_test(idoc_id):
        """Send test IDoc to partner."""
        db = get_db()
        try:
            idoc = db.execute('SELECT * FROM wms_outbound_idocs WHERE id = ?', (idoc_id,)).fetchone()
            if not idoc:
                return jsonify({'success': False, 'error': 'IDoc not found'})

            partner = db.execute('SELECT * FROM wms_edi_partners WHERE id = ?', (idoc['partner_id'],)).fetchone()

            db.execute('''
                UPDATE wms_outbound_idocs SET status = 'SENT', sent_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (idoc_id,))
            db.execute('''
                INSERT INTO wms_edi_audit_log (idoc_id, action_type, old_status, new_status, details, created_by)
                VALUES (?, 'SEND_TEST', ?, 'SENT', ?, ?)
            ''', (idoc_id, idoc['status'], f'Test send to {partner["partner_name"]}', session.get('user_id')))
            db.commit()

            return jsonify({'success': True, 'message': 'Test IDoc sent successfully'})
        except Exception as e:
            import traceback
            print(f"WMS EDI test send error: {e}")
            traceback.print_exc()
            db.rollback()
            return jsonify({'success': False, 'error': 'Unable to send test IDoc. Please try again.'}), 500

    # ============================================================
    # YARD / GATE / DOCK MANAGEMENT
    # ============================================================

    @app.route('/wms/yard')
    @wms_permission_required('yard', 'view')
    def wms_yard():
        """Yard management overview."""
        db = get_db()
        status = request.args.get('status', '')
        warehouse_id = request.args.get('warehouse_id', '')

        vehicles = db.execute('''
            SELECT y.*, w.name as warehouse_name, d.door_number as dock_number
            FROM wms_yard_vehicles y
            JOIN wms_warehouses w ON w.id = y.warehouse_id
            LEFT JOIN wms_dock_doors d ON d.id = y.dock_id
            WHERE y.is_active = 1
            ORDER BY y.arrival_time DESC
        ''').fetchall()

        docks = db.execute('SELECT * FROM wms_dock_doors WHERE is_active = 1 ORDER BY door_number').fetchall()

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()

        stats = {
            'waiting': db.execute("SELECT COUNT(*) as cnt FROM wms_yard_vehicles WHERE status = 'WAITING' AND is_active = 1").fetchone()['cnt'],
            'at_dock': db.execute("SELECT COUNT(*) as cnt FROM wms_yard_vehicles WHERE status = 'AT_DOCK' AND is_active = 1").fetchone()['cnt'],
            'loading': db.execute("SELECT COUNT(*) as cnt FROM wms_yard_vehicles WHERE status IN ('LOADING', 'UNLOADING') AND is_active = 1").fetchone()['cnt'],
            'departed': db.execute("SELECT COUNT(*) as cnt FROM wms_yard_vehicles WHERE status = 'DEPARTED' AND DATE(departure_time) = DATE('now')").fetchone()['cnt'],
        }

        activity = db.execute('''
            SELECT y.*, u.username as user_name
            FROM wms_yard_activity_log y
            LEFT JOIN users u ON u.id = y.user_id
            ORDER BY y.timestamp DESC LIMIT 20
        ''').fetchall()

        title = 'Yard Management'
        return render_template('wms/yard.html',
            title=title,
            vehicles=vehicles,
            docks=docks,
            warehouses=warehouses,
            stats=stats,
            activity=activity
        )

    @app.route('/wms/yard/arrival', methods=['GET', 'POST'])
    @wms_permission_required('yard', 'create')
    def wms_yard_arrival():
        """Register vehicle arrival."""
        db = get_db()

        if request.method == 'POST':
            plate_number = request.form.get('plate_number')
            driver_name = request.form.get('driver_name')
            driver_phone = request.form.get('driver_phone')
            carrier_name = request.form.get('carrier_name')
            vehicle_type = request.form.get('vehicle_type', 'INBOUND')
            warehouse_id = request.form.get('warehouse_id')
            expected_duration = request.form.get('expected_duration', 60)

            db.execute('''
                INSERT INTO wms_yard_vehicles (plate_number, driver_name, driver_phone, carrier_name,
                    vehicle_type, warehouse_id, status, expected_duration_minutes, arrival_time)
                VALUES (?, ?, ?, ?, ?, ?, 'WAITING', ?, ?)
            ''', (plate_number, driver_name, driver_phone, carrier_name, vehicle_type,
                  warehouse_id, expected_duration, datetime.now().isoformat()))
            db.commit()

            # Log activity
            db.execute('''
                INSERT INTO wms_yard_activity_log (vehicle_id, event, plate_number, driver_name, user_id)
                VALUES ((SELECT last_insert_rowid()), 'ARRIVED', ?, ?, ?)
            ''', (plate_number, driver_name, session.get('user_id')))

            flash(f'Vehicle {plate_number} registered', 'success')
            return redirect(url_for('wms_yard'))

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        title = 'Register Arrival'
        return render_template('wms/yard_arrival_form.html', title=title, warehouses=warehouses)

    @app.route('/wms/yard/<int:vehicle_id>/assign-dock', methods=['POST'])
    @wms_permission_required('yard', 'update')
    def wms_yard_assign_dock(vehicle_id):
        """Assign dock to vehicle."""
        db = get_db()
        dock_id = request.form.get('dock_id')

        vehicle = db.execute('SELECT * FROM wms_yard_vehicles WHERE id = ?', (vehicle_id,)).fetchone()
        dock = db.execute('SELECT * FROM wms_dock_doors WHERE id = ?', (dock_id,)).fetchone() if dock_id else None

        db.execute('''
            UPDATE wms_yard_vehicles SET dock_id = ?, status = 'AT_DOCK' WHERE id = ?
        ''', (dock_id, vehicle_id))
        db.commit()

        if dock:
            db.execute('''
                UPDATE wms_dock_doors SET status = 'OCCUPIED', current_vehicle_id = ? WHERE id = ?
            ''', (vehicle_id, dock_id))

        db.execute('''
            INSERT INTO wms_yard_activity_log (vehicle_id, event, plate_number, driver_name, dock_number, user_id)
            VALUES (?, 'ASSIGNED_DOCK', ?, ?, ?, ?)
        ''', (vehicle_id, vehicle['plate_number'], vehicle['driver_name'],
              dock['door_number'] if dock else None, session.get('user_id')))
        db.commit()

        flash(f'Dock {dock["door_number"] if dock else "None"} assigned to {vehicle["plate_number"]}', 'success')
        return redirect(url_for('wms_yard'))

    @app.route('/wms/yard/<int:vehicle_id>/depart', methods=['POST'])
    @wms_permission_required('yard', 'update')
    def wms_yard_depart(vehicle_id):
        """Mark vehicle as departed."""
        db = get_db()

        vehicle = db.execute('SELECT * FROM wms_yard_vehicles WHERE id = ?', (vehicle_id,)).fetchone()

        db.execute('''
            UPDATE wms_yard_vehicles SET status = 'DEPARTED', departure_time = ?, is_active = 0 WHERE id = ?
        ''', (datetime.now().isoformat(), vehicle_id))

        if vehicle['dock_id']:
            db.execute('''
                UPDATE wms_dock_doors SET status = 'AVAILABLE', current_vehicle_id = NULL WHERE id = ?
            ''', (vehicle['dock_id'],))

        db.execute('''
            INSERT INTO wms_yard_activity_log (vehicle_id, event, plate_number, driver_name, user_id)
            VALUES (?, 'DEPARTED', ?, ?, ?)
        ''', (vehicle_id, vehicle['plate_number'], vehicle['driver_name'], session.get('user_id')))
        db.commit()

        flash(f'Vehicle {vehicle["plate_number"]} departed', 'success')
        return redirect(url_for('wms_yard'))

    @app.route('/wms/dock-doors')
    @wms_permission_required('yard', 'view')
    def wms_dock_doors():
        """Dock door management."""
        db = get_db()
        warehouse_id = request.args.get('warehouse_id', '')

        docks = db.execute('''
            SELECT d.*, w.name as warehouse_name
            FROM wms_dock_doors d
            JOIN wms_warehouses w ON w.id = d.warehouse_id
            ORDER BY d.warehouse_id, d.door_number
        ''').fetchall()

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'Dock Doors'
        return render_template('wms/dock_doors.html',
            title=title,
            docks=docks,
            warehouses=warehouses
        )

    @app.route('/wms/dock-schedule')
    @wms_permission_required('yard', 'view')
    def wms_dock_schedule():
        """Dock scheduling calendar."""
        db = get_db()

        scheduled = db.execute('''
            SELECT s.*, w.name as warehouse_name, d.door_number
            FROM wms_dock_schedule s
            JOIN wms_warehouses w ON w.id = s.warehouse_id
            LEFT JOIN wms_dock_doors d ON d.id = s.dock_id
            WHERE s.scheduled_date >= date('now', '-1 day')
            ORDER BY s.scheduled_date, s.scheduled_time
        ''').fetchall()

        title = 'Dock Schedule'
        return render_template('wms/dock_schedule.html',
            title=title,
            scheduled=scheduled
        )

    # ============================================================
    # LABOR / TASK MANAGEMENT
    # ============================================================

    @app.route('/wms/labor')
    @wms_permission_required('labor', 'view')
    def wms_labor():
        """Labor and task management."""
        db = get_db()
        warehouse_id = request.args.get('warehouse_id', '')
        status = request.args.get('status', '')

        tasks = db.execute('''
            SELECT t.*, w.name as warehouse_name, l.code as location_code,
                   u.username as assigned_to_name, u2.username as completed_by_name
            FROM wms_work_tasks t
            JOIN wms_warehouses w ON w.id = t.warehouse_id
            LEFT JOIN wms_locations l ON l.id = t.location_id
            LEFT JOIN users u ON u.id = t.assigned_to
            LEFT JOIN users u2 ON u2.id = t.completed_by
            WHERE 1=1
            ORDER BY t.priority DESC, t.created_at DESC
        ''').fetchall()

        # Productivity stats
        today = date.today().isoformat()
        stats = {
            'total_tasks': db.execute('''
                SELECT COUNT(*) as cnt FROM wms_work_tasks
                WHERE DATE(created_at) = ?
            ''', (today,)).fetchone()['cnt'],
            'completed': db.execute('''
                SELECT COUNT(*) as cnt FROM wms_work_tasks
                WHERE status = 'COMPLETED' AND DATE(completed_at) = ?
            ''', (today,)).fetchone()['cnt'],
            'in_progress': db.execute('''
                SELECT COUNT(*) as cnt FROM wms_work_tasks WHERE status = 'IN_PROGRESS'
            ''').fetchone()['cnt'],
            'pending': db.execute('''
                SELECT COUNT(*) as cnt FROM wms_work_tasks WHERE status = 'PENDING'
            ''').fetchone()['cnt'],
            'avg_completion_minutes': db.execute('''
                SELECT AVG(actual_minutes) as avg FROM wms_work_tasks
                WHERE status = 'COMPLETED' AND DATE(completed_at) = ?
            ''', (today,)).fetchone()['avg'] or 0,
        }

        # Operator workload
        operators = db.execute('''
            SELECT u.id, u.username,
                   COUNT(t.id) as assigned_tasks,
                   SUM(CASE WHEN t.status = 'COMPLETED' THEN 1 ELSE 0 END) as completed_tasks,
                   AVG(CASE WHEN t.completed_at IS NOT NULL AND t.started_at IS NOT NULL
                       THEN (julianday(t.completed_at) - julianday(t.started_at)) * 24 * 60 ELSE NULL END) as avg_minutes
            FROM users u
            LEFT JOIN wms_work_tasks t ON t.assigned_to = u.id AND DATE(t.created_at) = ?
            WHERE 1=1
            GROUP BY u.id
            HAVING assigned_tasks > 0
        ''', (today,)).fetchall()

        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()

        title = 'Labor Management'
        return render_template('wms/labor.html',
            title=title,
            tasks=tasks,
            stats=stats,
            operators=operators,
            warehouses=warehouses
        )

    @app.route('/wms/labor/productivity')
    @wms_permission_required('labor', 'view')
    def wms_labor_productivity():
        """Labor productivity reports."""
        db = get_db()

        # Daily productivity over last 30 days
        daily_stats = db.execute('''
            SELECT DATE(created_at) as day,
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as completed,
                   AVG(CASE WHEN completed_at IS NOT NULL AND started_at IS NOT NULL
                       THEN (julianday(completed_at) - julianday(started_at)) * 24 * 60 ELSE NULL END) as avg_minutes
            FROM wms_work_tasks
            WHERE created_at >= date('now', '-30 days')
            GROUP BY DATE(created_at)
            ORDER BY day DESC
        ''').fetchall()

        title = 'Labor Productivity'
        return render_template('wms/labor_productivity.html',
            title=title,
            daily_stats=daily_stats
        )

    @app.route('/wms/executive-dashboard')
    @wms_permission_required('dashboard', 'view')
    def wms_executive_dashboard():
        """Executive Warehouse Dashboard."""
        db = get_db()
        ensure_quality_hold_tables()
        user_id = session.get('user_id')
        wh_filter = get_warehouse_filter(user_id)

        # KPIs
        kpis = {
            'total_skus': db.execute('SELECT COUNT(*) as cnt FROM wms_items WHERE is_active = 1').fetchone()['cnt'],
            'total_units': db.execute(f'SELECT COALESCE(SUM(quantity), 0) as qty FROM wms_inventory_balances WHERE 1=1 {wh_filter}').fetchone()['qty'],
            'pending_receiving': db.execute(f'SELECT COUNT(*) as cnt FROM wms_inbound_receipts WHERE status IN ("EXPECTED", "ARRIVED", "PARTIAL") {wh_filter.replace("warehouse_id", "warehouse_id")}').fetchone()['cnt'],
            'pending_putaway': db.execute(f'SELECT COUNT(*) as cnt FROM wms_putaway_tasks WHERE status = "PENDING" {wh_filter.replace("warehouse_id", "wms_putaway_tasks.warehouse_id")}').fetchone()['cnt'],
            'active_picks': db.execute(f'''
                SELECT COUNT(*) as cnt
                FROM wms_pick_tasks p
                JOIN wms_locations l ON l.id = p.source_location_id
                WHERE p.status IN ("PENDING", "IN_PROGRESS") {wh_filter.replace("warehouse_id", "l.warehouse_id")}
            ''').fetchone()['cnt'],
            'open_alerts': db.execute(f'SELECT COUNT(*) as cnt FROM wms_alerts WHERE is_active = 1 AND is_acknowledged = 0 {wh_filter.replace("warehouse_id", "warehouse_id")}').fetchone()['cnt'],
            'available': db.execute(f'SELECT COALESCE(SUM(quantity), 0) as qty FROM wms_inventory_balances WHERE status = "AVAILABLE" {wh_filter}').fetchone()['qty'],
            'reserved': db.execute(f'SELECT COALESCE(SUM(quantity), 0) as qty FROM wms_inventory_balances WHERE status = "RESERVED" {wh_filter}').fetchone()['qty'],
            'blocked': db.execute(f'SELECT COALESCE(SUM(quantity), 0) as qty FROM wms_inventory_balances WHERE status = "BLOCKED" {wh_filter}').fetchone()['qty'],
            'quarantine': db.execute(f'SELECT COALESCE(SUM(quantity), 0) as qty FROM wms_inventory_balances WHERE status = "QUARANTINE" {wh_filter}').fetchone()['qty'],
            'sku_growth': 0,
            'utilization_pct': 0,
        }
        sku_recent = db.execute("SELECT COUNT(*) as cnt FROM wms_items WHERE is_active = 1 AND DATE(created_at) >= DATE('now', '-30 days')").fetchone()['cnt']
        sku_previous = db.execute("SELECT COUNT(*) as cnt FROM wms_items WHERE is_active = 1 AND DATE(created_at) BETWEEN DATE('now', '-60 days') AND DATE('now', '-31 days')").fetchone()['cnt']
        kpis['sku_growth'] = round(((sku_recent - sku_previous) * 100.0 / sku_previous), 1) if sku_previous else (100 if sku_recent else 0)

        # Warehouse utilization
        warehouse_util = db.execute(f'''
            SELECT w.name,
                   COUNT(CASE WHEN l.is_empty = 0 THEN 1 END) as used_locations,
                   COUNT(*) as total_locations,
                   (COUNT(CASE WHEN l.is_empty = 0 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0)) as utilization
            FROM wms_warehouses w
            LEFT JOIN wms_locations l ON l.warehouse_id = w.id AND l.is_active = 1
            WHERE w.is_active = 1 {wh_filter}
            GROUP BY w.id
            ORDER BY w.name
        ''').fetchall()
        util_values = [float(row['utilization'] or 0) for row in warehouse_util]
        kpis['utilization_pct'] = round(sum(util_values) / len(util_values), 1) if util_values else 0

        inbound_rows = db.execute(f'''
            SELECT DATE(created_at) as activity_date,
                   COUNT(*) as receipts,
                   SUM(CASE WHEN status IN ('COMPLETED', 'RECEIVED') THEN 1 ELSE 0 END) as received
            FROM wms_inbound_receipts
            WHERE DATE(created_at) >= DATE('now', '-6 days') {wh_filter.replace('warehouse_id', 'warehouse_id')}
            GROUP BY DATE(created_at)
        ''').fetchall()
        inbound_by_day = {row['activity_date']: row for row in inbound_rows}
        inbound_trend = []
        for i in range(6, -1, -1):
            d = date.today() - timedelta(days=i)
            row = inbound_by_day.get(d.isoformat())
            inbound_trend.append({
                'day': d.strftime('%a')[:2],
                'receipts': row['receipts'] if row else 0,
                'received': row['received'] if row else 0
            })

        outbound_rows = db.execute(f'''
            SELECT DATE(created_at) as activity_date,
                   COUNT(*) as orders,
                   SUM(CASE WHEN status IN ('DISPATCHED', 'IN_TRANSIT', 'DELIVERED') THEN 1 ELSE 0 END) as shipped
            FROM wms_shipments
            WHERE DATE(created_at) >= DATE('now', '-6 days') {wh_filter.replace('warehouse_id', 'warehouse_id')}
            GROUP BY DATE(created_at)
        ''').fetchall()
        outbound_by_day = {row['activity_date']: row for row in outbound_rows}
        outbound_trend = []
        for i in range(6, -1, -1):
            d = date.today() - timedelta(days=i)
            row = outbound_by_day.get(d.isoformat())
            outbound_trend.append({
                'day': d.strftime('%a')[:2],
                'orders': row['orders'] if row else 0,
                'shipped': row['shipped'] if row else 0
            })

        inbound_max = max([d['receipts'] for d in inbound_trend]) or 1
        outbound_max = max([d['orders'] for d in outbound_trend]) or 1

        # Top moving items
        top_items = db.execute(f'''
            SELECT i.item_code, i.name, COUNT(m.id) as moves
            FROM wms_items i
            LEFT JOIN wms_inventory_ledger m ON m.item_id = i.id AND m.created_at >= date('now', '-7 days')
            WHERE i.is_active = 1
            GROUP BY i.id
            ORDER BY moves DESC
            LIMIT 8
        ''').fetchall()

        # Exceptions
        exceptions = []
        exc_types = [
            ('Low Stock', db.execute(f'''
                SELECT COUNT(*) as cnt
                FROM wms_replenishment_config c
                WHERE c.is_active = 1
                  AND COALESCE((SELECT SUM(quantity) FROM wms_inventory_balances b WHERE b.item_id = c.item_id AND b.warehouse_id = c.warehouse_id), 0) <= c.reorder_point
                  {wh_filter.replace('warehouse_id', 'c.warehouse_id')}
            ''').fetchone()['cnt']),
            ('Near Expiry', db.execute(f'''
                SELECT COUNT(DISTINCT l.item_id) as cnt
                FROM wms_lots l
                JOIN wms_inventory_balances b ON b.lot_id = l.id
                WHERE l.expiry_date BETWEEN date("now") AND date("now", "+30 days")
                  AND b.quantity > 0 {wh_filter.replace('warehouse_id', 'b.warehouse_id')}
            ''').fetchone()['cnt']),
            ('Negative Stock', db.execute(f'SELECT COUNT(*) as cnt FROM wms_inventory_balances WHERE quantity < 0 {wh_filter}').fetchone()['cnt']),
            ('Pending Count', db.execute(f'SELECT COUNT(*) as cnt FROM wms_stock_count_lines WHERE status = "PENDING"').fetchone()['cnt']),
            ('QC Hold', db.execute(f'SELECT COUNT(*) as cnt FROM wms_quality_holds WHERE status = "ACTIVE" {wh_filter.replace("warehouse_id", "warehouse_id")}').fetchone()['cnt']),
            ('Short Pick', db.execute(f'''
                SELECT COUNT(*) as cnt
                FROM wms_pick_tasks p
                JOIN wms_locations l ON l.id = p.source_location_id
                WHERE p.short_pick_reason IS NOT NULL {wh_filter.replace("warehouse_id", "l.warehouse_id")}
            ''').fetchone()['cnt']),
        ]
        for etype, cnt in exc_types:
            if cnt > 0:
                exceptions.append({'type': etype, 'count': cnt})

        # Top operators
        top_operators = db.execute('''
            SELECT u.username, COUNT(t.id) as tasks, SUM(CASE WHEN t.status = "COMPLETED" THEN 1 ELSE 0 END) as completed
            FROM users u
            LEFT JOIN wms_work_tasks t ON t.assigned_to = u.id AND DATE(t.created_at) = DATE("now")
            WHERE 1=1
            GROUP BY u.id
            HAVING tasks > 0
            ORDER BY completed DESC
            LIMIT 5
        ''').fetchall()

        selected_warehouse = db.execute(f'SELECT name FROM wms_warehouses WHERE is_active = 1 {wh_filter} LIMIT 1').fetchone()
        selected_warehouse = selected_warehouse['name'] if selected_warehouse else 'All Warehouses'

        title = 'Executive Warehouse Dashboard'
        return render_template('wms/executive_dashboard.html',
            title=title,
            kpis=kpis,
            warehouse_util=warehouse_util,
            inbound_trend=inbound_trend,
            outbound_trend=outbound_trend,
            inbound_max=inbound_max,
            outbound_max=outbound_max,
            top_items=top_items,
            exceptions=exceptions,
            top_operators=top_operators,
            selected_warehouse=selected_warehouse
        )

    # ============================================================
    # BI / ANALYTICS INTEGRATION
    # ============================================================

    @app.route('/wms/analytics/dashboard')
    @wms_permission_required('dashboard', 'view')
    def wms_analytics_dashboard():
        """Analytics Dashboard - KPI overview."""
        db = get_db()
        user_id = session.get('user_id')
        wh_filter = get_warehouse_filter(user_id)

        # Inventory KPIs
        inventory_kpis = {
            'total_value': 0,
            'total_units': db.execute(f'SELECT COALESCE(SUM(quantity), 0) as qty FROM wms_inventory_balances WHERE 1=1 {wh_filter}').fetchone()['qty'],
            'sku_count': db.execute(f'SELECT COUNT(DISTINCT item_id) as cnt FROM wms_inventory_balances WHERE 1=1 {wh_filter}').fetchone()['cnt'],
            'location_count': db.execute(f'SELECT COUNT(*) as cnt FROM wms_locations WHERE is_active = 1 {wh_filter.replace("warehouse_id", "warehouse_id")}').fetchone()['cnt'],
            'utilization_pct': db.execute(f'''
                SELECT
                    (COUNT(CASE WHEN is_empty = 0 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0)) as util
                FROM wms_locations WHERE is_active = 1 {wh_filter.replace("warehouse_id", "warehouse_id")}
            ''').fetchone()['util'] or 0,
        }

        # Stock Aging Analysis (ABC classification)
        abc_analysis = db.execute(f'''
            SELECT abc_class, COUNT(*) as item_count, SUM(total_qty) as total_qty, 0 as total_value
            FROM (
                SELECT item_id, SUM(quantity) as total_qty,
                    CASE
                        WHEN SUM(quantity) >= (SELECT COALESCE(SUM(quantity), 0) * 0.8 FROM wms_inventory_balances WHERE 1=1 {wh_filter} AND quantity > 0) THEN 'A'
                        WHEN SUM(quantity) >= (SELECT COALESCE(SUM(quantity), 0) * 0.95 FROM wms_inventory_balances WHERE 1=1 {wh_filter} AND quantity > 0) THEN 'B'
                        ELSE 'C'
                    END as abc_class
                FROM wms_inventory_balances
                WHERE quantity > 0 {wh_filter}
                GROUP BY item_id
            )
            GROUP BY abc_class
        ''').fetchall()

        # Velocity Analysis
        velocity_analysis = db.execute(f'''
            SELECT
                CASE
                    WHEN move_count >= 100 THEN 'A'
                    WHEN move_count >= 20 THEN 'B'
                    ELSE 'C'
                END as velocity_class,
                COUNT(*) as sku_count,
                SUM(move_count) as total_moves
            FROM (
                SELECT i.id, i.item_code,
                       COALESCE((SELECT COUNT(*) FROM wms_inventory_ledger l WHERE l.item_id = i.id AND l.created_at >= date('now', '-30 days')), 0) as move_count
                FROM wms_items i
                WHERE i.is_active = 1
            )
            GROUP BY velocity_class
        ''').fetchall()

        # Daily Trends (last 30 days)
        daily_trends = []
        for i in range(29, -1, -1):
            day = db.execute('''
                SELECT
                    COALESCE(SUM(CASE WHEN transaction_type IN ('RECEIPT', 'RETURN_IN') THEN quantity_moved ELSE 0 END), 0) as inbound,
                    COALESCE(SUM(CASE WHEN transaction_type IN ('PICK', 'SHIPMENT', 'RETURN_OUT') THEN ABS(quantity_moved) ELSE 0 END), 0) as outbound
                FROM wms_inventory_ledger
                WHERE DATE(created_at) = DATE('now', ?)
            ''', (f'-{i} days',)).fetchone()
            daily_trends.append({
                'date': date.today().strftime('%m/%d'),
                'inbound': day['inbound'] or 0,
                'outbound': day['outbound'] or 0
            })

        title = 'Analytics Dashboard'
        return render_template('wms/analytics_dashboard.html',
            title=title,
            inventory_kpis=inventory_kpis,
            abc_analysis=abc_analysis,
            velocity_analysis=velocity_analysis,
            daily_trends=daily_trends
        )

    @app.route('/wms/analytics/api/kpis')
    @wms_permission_required('dashboard', 'view')
    def wms_analytics_api_kpis():
        """API endpoint for KPI data (for BI tools)."""
        db = get_db()
        user_id = session.get('user_id')
        wh_filter = get_warehouse_filter(user_id)

        kpis = {
            'inventory_value': 0,
            'inventory_units': db.execute(f'SELECT COALESCE(SUM(quantity), 0) as qty FROM wms_inventory_balances WHERE 1=1 {wh_filter}').fetchone()['qty'],
            'sku_count': db.execute(f'SELECT COUNT(DISTINCT item_id) as cnt FROM wms_inventory_balances WHERE 1=1 {wh_filter}').fetchone()['cnt'],
            'pending_receiving': db.execute(f'SELECT COUNT(*) as cnt FROM wms_inbound_receipts WHERE status IN ("EXPECTED", "ARRIVED") {wh_filter.replace("warehouse_id", "warehouse_id")}').fetchone()['cnt'],
            'pending_picking': db.execute(f'''
                SELECT COUNT(*) as cnt
                FROM wms_pick_tasks p
                JOIN wms_locations l ON l.id = p.source_location_id
                WHERE p.status IN ("PENDING", "ASSIGNED") {wh_filter.replace("warehouse_id", "l.warehouse_id")}
            ''').fetchone()['cnt'],
            'open_alerts': db.execute(f'SELECT COUNT(*) as cnt FROM wms_alerts WHERE is_active = 1 {wh_filter.replace("warehouse_id", "warehouse_id")}').fetchone()['cnt'],
        }

        return jsonify({'success': True, 'kpis': kpis})

    @app.route('/wms/analytics/api/chart/<chart_type>')
    @wms_permission_required('dashboard', 'view')
    def wms_analytics_api_chart(chart_type):
        """API endpoint for chart data (for BI tools)."""
        db = get_db()
        user_id = session.get('user_id')
        wh_filter = get_warehouse_filter(user_id)

        if chart_type == 'inventory_abc':
            data = db.execute(f'''
                SELECT label, SUM(total_qty) as total_qty, SUM(total_qty) as value
                FROM (
                    SELECT item_id, SUM(quantity) as total_qty,
                        CASE
                            WHEN SUM(quantity) >= (SELECT COALESCE(SUM(quantity), 0) * 0.8 FROM wms_inventory_balances WHERE 1=1 {wh_filter} AND quantity > 0) THEN 'A'
                            WHEN SUM(quantity) >= (SELECT COALESCE(SUM(quantity), 0) * 0.95 FROM wms_inventory_balances WHERE 1=1 {wh_filter} AND quantity > 0) THEN 'B'
                            ELSE 'C'
                        END as label
                    FROM wms_inventory_balances
                    WHERE quantity > 0 {wh_filter}
                    GROUP BY item_id
                )
                GROUP BY label
            ''').fetchall()
        elif chart_type == 'stock_status':
            data = db.execute(f'''
                SELECT status as label, SUM(quantity) as value
                FROM wms_inventory_balances
                WHERE 1=1 {wh_filter}
                GROUP BY status
            ''').fetchall()
        elif chart_type == 'movement_trend':
            data = db.execute('''
                SELECT
                    strftime('%Y-%m-%d', created_at) as label,
                    SUM(CASE WHEN quantity_moved > 0 THEN quantity_moved ELSE 0 END) as inbound,
                    SUM(CASE WHEN quantity_moved < 0 THEN ABS(quantity_moved) ELSE 0 END) as outbound
                FROM wms_inventory_ledger
                WHERE created_at >= date('now', '-30 days')
                GROUP BY label
                ORDER BY label
            ''').fetchall()
        else:
            data = []

        return jsonify({'success': True, 'chart_type': chart_type, 'data': [dict(row) for row in data]})

    @app.route('/wms/analytics/api/export/<format>')
    @wms_permission_required('dashboard', 'view')
    def wms_analytics_export(format):
        """Export analytics data in various formats."""
        db = get_db()
        user_id = session.get('user_id')
        wh_filter = get_warehouse_filter(user_id)

        inventory_data = db.execute(f'''
            SELECT
                i.item_code, i.name as item_name,
                COALESCE(b.quantity, 0) as quantity,
                0 as unit_cost,
                0 as total_value,
                b.status, l.code as location_code,
                w.name as warehouse_name
            FROM wms_items i
            LEFT JOIN wms_inventory_balances b ON b.item_id = i.id
            LEFT JOIN wms_locations l ON l.id = b.location_id
            LEFT JOIN wms_warehouses w ON w.id = b.warehouse_id
            WHERE i.is_active = 1 {wh_filter}
            ORDER BY total_value DESC
        ''').fetchall()

        if format == 'csv':
            import csv
            from io import StringIO
            output = StringIO()
            writer = csv.writer(output)
            writer.writerow(['Item Code', 'Item Name', 'Quantity', 'Unit Cost', 'Total Value', 'Status', 'Location', 'Warehouse'])
            for row in inventory_data:
                writer.writerow([row['item_code'], row['item_name'], row['quantity'], row['unit_cost'], row['total_value'], row['status'], row['location_code'], row['warehouse_name']])
            return output.getvalue(), 200, {'Content-Type': 'text/csv', 'Content-Disposition': 'attachment; filename=inventory_export.csv'}
        elif format == 'json':
            return jsonify({'success': True, 'data': [dict(row) for row in inventory_data]})
        else:
            return jsonify({'success': False, 'error': 'Unsupported format'})

    @app.route('/wms/analytics/inventory-aging')
    @wms_permission_required('reports', 'view')
    def wms_analytics_inventory_aging():
        """Inventory aging analysis report."""
        db = get_db()
        user_id = session.get('user_id')
        wh_filter = get_warehouse_filter(user_id)

        aging_data = db.execute(f'''
            SELECT
                i.item_code, i.name as item_name,
                l.lot_number, l.expiry_date,
                b.quantity, 0 as unit_cost,
                0 as total_value,
                CASE
                    WHEN l.expiry_date < date('now') THEN 'EXPIRED'
                    WHEN l.expiry_date < date('now', '+30 days') THEN 'CRITICAL'
                    WHEN l.expiry_date < date('now', '+90 days') THEN 'WARNING'
                    ELSE 'OK'
                END as aging_status
            FROM wms_items i
            JOIN wms_inventory_balances b ON b.item_id = i.id
            LEFT JOIN wms_lots l ON l.id = b.lot_id
            WHERE i.is_active = 1 AND l.expiry_date IS NOT NULL {wh_filter}
            ORDER BY l.expiry_date
        ''').fetchall()

        title = 'Inventory Aging'
        return render_template('wms/analytics_inventory_aging.html',
            title=title,
            aging_data=aging_data
        )

    @app.route('/wms/analytics/operator-productivity')
    @wms_permission_required('reports', 'view')
    def wms_analytics_operator_productivity():
        """Operator productivity analytics."""
        db = get_db()

        productivity = db.execute('''
            SELECT
                u.username, u.id as user_id,
                COUNT(DISTINCT t.id) as total_tasks,
                SUM(CASE WHEN t.status = 'COMPLETED' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN t.task_type = 'PICK' AND t.status = 'COMPLETED' THEN 1 ELSE 0 END) as picks,
                SUM(CASE WHEN t.task_type = 'PUTAWAY' AND t.status = 'COMPLETED' THEN 1 ELSE 0 END) as putaways,
                AVG(t.actual_minutes) as avg_minutes,
                SUM(t.actual_minutes) as total_minutes
            FROM users u
            LEFT JOIN wms_work_tasks t ON t.assigned_to = u.id AND DATE(t.created_at) >= DATE('now', '-7 days')
            WHERE 1=1
            GROUP BY u.id
            HAVING total_tasks > 0
            ORDER BY completed DESC
        ''').fetchall()

        title = 'Operator Productivity'
        return render_template('wms/analytics_operator_productivity.html',
            title=title,
            productivity=productivity
        )

    # ============================================================
    # INTEGRATION / FLOW / WEBHOOKS
    # ============================================================

    @app.route('/wms/integration/webhooks')
    @wms_permission_required('settings', 'view')
    def wms_integration_webhooks():
        """Webhook configuration."""
        db = get_db()
        webhooks = db.execute('SELECT * FROM wms_webhooks ORDER BY event_type').fetchall() if 'wms_webhooks' in [t[0] for t in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()] else []
        title = 'Webhook Configuration'
        return render_template('wms/integration_webhooks.html', title=title, webhooks=webhooks)

    @app.route('/wms/integration/webhooks/new', methods=['GET', 'POST'])
    @wms_permission_required('settings', 'create')
    def wms_integration_webhooks_new():
        """Create webhook."""
        db = get_db()
        if request.method == 'POST':
            event_type = request.form.get('event_type')
            url = request.form.get('url')
            secret = request.form.get('secret')
            is_active = 1 if request.form.get('is_active') else 0
            try:
                db.execute('''
                    CREATE TABLE IF NOT EXISTS wms_webhooks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_type TEXT NOT NULL,
                        url TEXT NOT NULL,
                        secret TEXT,
                        is_active INTEGER DEFAULT 1,
                        retry_count INTEGER DEFAULT 0,
                        last_triggered TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                db.execute('INSERT INTO wms_webhooks (event_type, url, secret, is_active) VALUES (?, ?, ?, ?)',
                          (event_type, url, secret, is_active))
                db.commit()
                flash('Webhook created!', 'success')
            except Exception as e:
                import traceback
                print(f"WMS webhook create error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error creating webhook. Please try again.', 'error')
            return redirect(url_for('wms_integration_webhooks'))
        title = 'New Webhook'
        return render_template('wms/integration_webhook_form.html', title=title, webhook=None)

    @app.route('/wms/integration/api/status')
    @wms_permission_required('dashboard', 'view')
    def wms_integration_api_status():
        """Check integration status with external systems."""
        db = get_db()
        status = {
            'database': 'CONNECTED',
            'edi_partners': db.execute('SELECT COUNT(*) as cnt FROM wms_edi_partners WHERE is_active = 1').fetchone()['cnt'],
            'pending_webhooks': 0,
            'active_connections': 1
        }
        return jsonify({'success': True, 'status': status})

    @app.route('/wms/integration/logs')
    @wms_permission_required('settings', 'view')
    def wms_integration_logs():
        """Integration logs."""
        db = get_db()
        logs = db.execute('SELECT * FROM wms_integration_logs ORDER BY created_at DESC LIMIT 100').fetchall() if 'wms_integration_logs' in [t[0] for t in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()] else []
        title = 'Integration Logs'
        return render_template('wms/integration_logs.html', title=title, logs=logs)

    @app.route('/wms/integration/trigger-webhook/<event_type>', methods=['POST'])
    @wms_permission_required('settings', 'edit')
    def wms_integration_trigger_webhook(event_type):
        """Manually trigger a webhook for testing."""
        import hashlib, hmac, json
        db = get_db()
        webhooks = db.execute('SELECT * FROM wms_webhooks WHERE event_type = ? AND is_active = 1', (event_type,)).fetchall()
        results = []
        for wh in webhooks:
            payload = json.dumps({'event': event_type, 'timestamp': datetime.now().isoformat(), 'data': {}})
            signature = hmac.new(wh['secret'].encode(), payload.encode(), hashlib.sha256).hexdigest() if wh['secret'] else ''
            results.append({'webhook_id': wh['id'], 'url': wh['url'], 'signature': signature, 'status': 'TRIGGERED'})
            db.execute('UPDATE wms_webhooks SET last_triggered = CURRENT_TIMESTAMP, retry_count = retry_count + 1 WHERE id = ?', (wh['id'],))
        db.commit()
        return jsonify({'success': True, 'results': results})

    # ============================================================
    # ZONE PICKING ENHANCEMENT
    # ============================================================

    @app.route('/wms/zone-picking')
    @wms_permission_required('picking', 'view')
    def wms_zone_picking():
        """Zone picking management."""
        db = get_db()
        zones = db.execute('''
            SELECT z.*, w.name as warehouse_name,
                   (SELECT COUNT(*) FROM wms_pick_tasks p JOIN wms_locations l ON l.id = p.source_location_id WHERE l.zone_id = z.id AND p.status = 'PENDING') as pending_picks,
                   (SELECT COUNT(*) FROM wms_pick_tasks p JOIN wms_locations l ON l.id = p.source_location_id WHERE l.zone_id = z.id AND p.status = 'IN_PROGRESS') as in_progress_picks,
                   (SELECT COUNT(*) FROM wms_pick_tasks p JOIN wms_locations l ON l.id = p.source_location_id WHERE l.zone_id = z.id AND p.status = 'COMPLETED' AND DATE(p.completed_at) = DATE('now')) as completed_today
            FROM wms_zones z
            JOIN wms_warehouses w ON w.id = z.warehouse_id
            WHERE z.picking_enabled = 1 AND z.is_active = 1
        ''').fetchall()

        picks = db.execute('''
            SELECT p.*, l.code as location_code, i.item_code, i.name as item_name, z.code as zone_code
            FROM wms_pick_tasks p
            LEFT JOIN wms_locations l ON l.id = p.source_location_id
            LEFT JOIN wms_items i ON i.id = p.item_id
            LEFT JOIN wms_zones z ON z.id = l.zone_id
            WHERE p.status IN ('PENDING', 'ASSIGNED', 'IN_PROGRESS')
            ORDER BY p.priority DESC, p.created_at ASC LIMIT 50
        ''').fetchall()

        operators = db.execute('''
            SELECT u.id, u.username as name,
                   (SELECT z.code FROM wms_pick_tasks p JOIN wms_locations l ON l.id = p.source_location_id JOIN wms_zones z ON z.id = l.zone_id WHERE p.assigned_to = u.id AND p.status = 'IN_PROGRESS' LIMIT 1) as current_zone,
                   (SELECT COUNT(*) FROM wms_pick_tasks WHERE assigned_to = u.id AND status = 'IN_PROGRESS') as active_picks
            FROM users u
            WHERE 1=1
            ORDER BY u.username
        ''').fetchall() if 'users' in [t[0] for t in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()] else []

        title = 'Zone Picking'
        return render_template('wms/zone_picking.html', title=title, zones=zones, picks=picks, operators=operators)

    @app.route('/wms/zone-picking/quick-assign/<int:pick_id>', methods=['POST'])
    @wms_permission_required('picking', 'edit')
    def wms_zone_picking_quick_assign(pick_id):
        """Quick assign a single pick to current user."""
        db = get_db()
        try:
            pick = db.execute('''
                SELECT p.id, loc.warehouse_id
                FROM wms_pick_tasks p
                LEFT JOIN wms_locations loc ON p.source_location_id = loc.id
                WHERE p.id = ? AND p.status = 'PENDING'
            ''', (pick_id,)).fetchone()
            if not pick:
                return jsonify({'success': False, 'error': 'Pick task not found or not assignable'}), 404
            if pick['warehouse_id'] and not ensure_warehouse_allowed(pick['warehouse_id']):
                return jsonify({'success': False, 'error': 'Permission denied for this warehouse'}), 403
            db.execute("UPDATE wms_pick_tasks SET assigned_to = ?, status = 'ASSIGNED' WHERE id = ?",
                       (session.get('user_id'), pick_id))
            db.commit()
            return jsonify({'success': True})
        except Exception as e:
            import traceback
            print(f"WMS zone quick assign error: {e}")
            traceback.print_exc()
            db.rollback()
            return jsonify({'success': False, 'error': 'Unable to assign pick task. Please try again.'}), 500

    @app.route('/wms/zone-picking/assign', methods=['POST'])
    @wms_permission_required('picking', 'edit')
    def wms_zone_picking_assign():
        """Assign picks to zone based on items location."""
        db = get_db()
        zone_id = parse_positive_int(request.form.get('zone_id'))
        operator_id = parse_positive_int(request.form.get('operator_id'))
        if not zone_id or not operator_id:
            flash('Select a valid zone and operator.', 'error')
            return redirect(url_for('wms_zone_picking'))
        zone = db.execute('SELECT id, warehouse_id FROM wms_zones WHERE id = ?', (zone_id,)).fetchone()
        if not zone or not ensure_warehouse_allowed(zone['warehouse_id']):
            flash('Selected zone is not available for your warehouse access.', 'error')
            return redirect(url_for('wms_zone_picking'))
        operator = db.execute('SELECT id FROM users WHERE id = ?', (operator_id,)).fetchone()
        if not operator:
            flash('Selected operator was not found.', 'error')
            return redirect(url_for('wms_zone_picking'))
        picks_assigned = 0
        picks = db.execute('''
            SELECT p.* FROM wms_pick_tasks p
            JOIN wms_locations l ON l.id = p.source_location_id
            WHERE l.zone_id = ? AND p.status = 'PENDING'
            ORDER BY p.priority DESC LIMIT 20
        ''', (zone_id,)).fetchall()
        for pick in picks:
            db.execute('UPDATE wms_pick_tasks SET assigned_to = ?, status = "ASSIGNED" WHERE id = ?', (operator_id, pick['id']))
            picks_assigned += 1
        db.commit()
        flash(f'Assigned {picks_assigned} picks to operator', 'success')
        return redirect(url_for('wms_zone_picking'))

    # ============================================================
    # PACKING & DISPATCH ENHANCEMENT
    # ============================================================

    @app.route('/wms/packing/specifications')
    @wms_permission_required('packing', 'view')
    def wms_packing_specs():
        """Packing specifications."""
        db = get_db()
        specs = db.execute('SELECT * FROM wms_packing_specs ORDER BY name').fetchall() if 'wms_packing_specs' in [t[0] for t in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()] else []
        title = 'Packing Specifications'
        return render_template('wms/packing_specs.html', title=title, specs=specs)

    @app.route('/wms/packing/container-load')
    @wms_permission_required('packing', 'view')
    def wms_packing_container_load():
        """Container load optimization."""
        title = 'Container Load Optimization'
        return render_template('wms/packing_container_load.html', title=title)

    @app.route('/wms/dispatch/schedule')
    @wms_permission_required('dispatch', 'view')
    def wms_dispatch_schedule():
        """Dispatch scheduling."""
        db = get_db()
        dispatches = db.execute('''
            SELECT s.*, w.name as warehouse_name, v.plate_number
            FROM wms_shipments s
            JOIN wms_warehouses w ON w.id = s.warehouse_id
            LEFT JOIN wms_yard_vehicles v ON v.id = s.vehicle_id
            WHERE s.status IN ('READY', 'IN_TRANSIT')
            ORDER BY s.scheduled_date
        ''').fetchall()
        title = 'Dispatch Schedule'
        return render_template('wms/dispatch_schedule.html', title=title, dispatches=dispatches)

    # ============================================================
    # TRANSFER MANAGEMENT ENHANCEMENT
    # ============================================================

    @app.route('/wms/transfers/cross-company')
    @wms_permission_required('transfers', 'view')
    def wms_transfers_cross_company():
        """Cross-company transfers."""
        db = get_db()
        transfers = db.execute('''
            SELECT t.*, w_src.name as source_warehouse, w_dst.name as dest_warehouse
            FROM wms_transfers t
            JOIN wms_warehouses w_src ON w_src.id = t.source_warehouse_id
            JOIN wms_warehouses w_dst ON w_dst.id = t.destination_warehouse_id
            WHERE t.transfer_type = 'CROSS_COMPANY'
            ORDER BY t.created_at DESC
        ''').fetchall()
        title = 'Cross-Company Transfers'
        return render_template('wms/transfers_cross_company.html', title=title, transfers=transfers)

    @app.route('/wms/transfers/transit')
    @wms_permission_required('transfers', 'view')
    def wms_transfers_in_transit():
        """In-transit stock tracking."""
        db = get_db()
        transit = db.execute('''
            SELECT t.*, w_src.name as source, w_dst.name as destination,
                   DATEDIFF(COALESCE(t.estimated_arrival, datetime('now', '+3 days')), datetime('now')) as days_in_transit
            FROM wms_transfers t
            JOIN wms_warehouses w_src ON w_src.id = t.source_warehouse_id
            JOIN wms_warehouses w_dst ON w_dst.id = t.destination_warehouse_id
            WHERE t.status = 'IN_TRANSIT'
        ''').fetchall()
        title = 'In-Transit Stock'
        return render_template('wms/transfers_transit.html', title=title, transit=transit)

    # ============================================================
    # RECEIVING ENHANCEMENT
    # ============================================================

    @app.route('/wms/receiving/asn')
    @wms_permission_required('receiving', 'view')
    def wms_receiving_asn():
        """ASN (Advanced Shipping Notice) management."""
        db = get_db()
        asns = db.execute('''
            SELECT a.*, p.partner_name
            FROM wms_asn a
            LEFT JOIN wms_edi_partners p ON p.id = a.partner_id
            ORDER BY a.expected_date DESC
        ''').fetchall() if 'wms_asn' in [t[0] for t in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()] else []
        title = 'ASN Management'
        return render_template('wms/receiving_asn.html', title=title, asns=asns)

    @app.route('/wms/receiving/asn/new', methods=['GET', 'POST'])
    @wms_permission_required('receiving', 'create')
    def wms_receiving_asn_new():
        """Create ASN."""
        db = get_db()
        if request.method == 'POST':
            try:
                asn_number = (request.form.get('asn_number') or f'ASN-{date.today().strftime("%Y%m%d")}-{random.randint(1000,9999)}').strip()
                partner_id = parse_positive_int(request.form.get('partner_id'))
                warehouse_id = parse_positive_int(request.form.get('warehouse_id'))
                expected_date = request.form.get('expected_date')
                po_number = (request.form.get('po_number') or '').strip()
                notes = (request.form.get('notes') or '').strip()
                if not asn_number or not warehouse_id:
                    flash('ASN number and warehouse are required.', 'error')
                    raise ValueError('validation_failed')
                if not ensure_warehouse_allowed(warehouse_id):
                    flash('Selected warehouse is not available for your account.', 'error')
                    raise ValueError('validation_failed')
                if partner_id:
                    partner = db.execute('SELECT id FROM wms_edi_partners WHERE id = ? AND is_active = 1', (partner_id,)).fetchone()
                    if not partner:
                        flash('Selected EDI partner was not found.', 'error')
                        raise ValueError('validation_failed')

                cursor = db.execute('''
                    INSERT INTO wms_asn (asn_number, partner_id, warehouse_id, expected_date, po_number, notes, created_by, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'EXPECTED')
                ''', (asn_number, partner_id, warehouse_id, expected_date, po_number, notes, session.get('user_id')))
                asn_id = cursor.lastrowid
                db.commit()
                flash('ASN created successfully!', 'success')
                return redirect(url_for('wms_receiving_asn_detail', asn_id=asn_id))
            except ValueError as e:
                if str(e) != 'validation_failed':
                    flash('Invalid ASN data. Please review the form.', 'error')
                db.rollback()
            except Exception as e:
                import traceback
                print(f"WMS ASN create error: {e}")
                traceback.print_exc()
                db.rollback()
                flash('Error creating ASN. Please try again.', 'error')

        partners = db.execute('SELECT * FROM wms_edi_partners WHERE is_active = 1 ORDER BY partner_name').fetchall()
        warehouses = db.execute('SELECT * FROM wms_warehouses WHERE is_active = 1 ORDER BY name').fetchall()
        title = 'New ASN'
        return render_template('wms/receiving_asn_form.html', title=title, asn=None, partners=partners, warehouses=warehouses)

    @app.route('/wms/receiving/asn/<int:asn_id>')
    @wms_permission_required('receiving', 'view')
    def wms_receiving_asn_detail(asn_id):
        """View ASN detail."""
        db = get_db()
        asn = db.execute('SELECT a.*, p.partner_name, w.name as warehouse_name FROM wms_asn a LEFT JOIN wms_edi_partners p ON p.id = a.partner_id LEFT JOIN wms_warehouses w ON w.id = a.warehouse_id WHERE a.id = ?', (asn_id,)).fetchone()
        if not asn:
            flash('ASN not found', 'error')
            return redirect(url_for('wms_receiving_asn'))

        lines = db.execute('SELECT l.*, i.item_code, i.name as item_name FROM wms_asn_lines l JOIN wms_items i ON i.id = l.item_id WHERE l.asn_id = ?', (asn_id,)).fetchall()
        title = f'ASN {asn.asn_number}'
        return render_template('wms/receiving_asn_detail.html', title=title, asn=asn, lines=lines)

    @app.route('/wms/receiving/asn/<int:asn_id>/delete', methods=['POST'])
    @wms_permission_required('receiving', 'delete')
    def wms_receiving_asn_delete(asn_id):
        """Delete ASN."""
        db = get_db()
        try:
            db.execute('DELETE FROM wms_asn_lines WHERE asn_id = ?', (asn_id,))
            db.execute('DELETE FROM wms_asn WHERE id = ?', (asn_id,))
            db.commit()
            flash('ASN deleted successfully!', 'success')
        except Exception as e:
            import traceback
            print(f"WMS ASN delete error: {e}")
            traceback.print_exc()
            db.rollback()
            flash('Error deleting ASN. Please try again.', 'error')
        return redirect(url_for('wms_receiving_asn'))

    @app.route('/wms/receiving/cross-dock')
    @wms_permission_required('receiving', 'view')
    def wms_receiving_cross_dock():
        """Cross-dock management."""
        db = get_db()
        cross_docks = db.execute('''
            SELECT c.*, r.receipt_number, w.name as warehouse_name
            FROM wms_cross_dock c
            JOIN wms_inbound_receipts r ON r.id = c.receipt_id
            JOIN wms_warehouses w ON w.id = c.warehouse_id
            WHERE c.status IN ('PENDING', 'IN_PROGRESS')
        ''').fetchall() if 'wms_cross_dock' in [t[0] for t in db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()] else []
        title = 'Cross-Dock Management'
        return render_template('wms/receiving_cross_dock.html', title=title, cross_docks=cross_docks)

    # ============================================================
    # NAVIGATION COMPATIBILITY ALIASES
    # ============================================================

    @app.route('/wms/inventory/current')
    @app.route('/wms/inventory/by-warehouse')
    @app.route('/wms/inventory/by-location')
    @app.route('/wms/inventory/reserved')
    @wms_permission_required('inventory', 'view')
    def wms_inventory_aliases():
        return redirect(url_for('wms_inventory', status='RESERVED' if request.path.endswith('/reserved') else ''))

    @app.route('/wms/stock-movements')
    @app.route('/wms/stock-movements/history')
    @app.route('/wms/stock-movements/inbound')
    @app.route('/wms/stock-movements/outbound')
    @app.route('/wms/stock-movements/internal')
    @wms_permission_required('stock_movements', 'view')
    def wms_stock_movement_aliases():
        movement_map = {'/wms/stock-movements/inbound': 'IN', '/wms/stock-movements/outbound': 'OUT', '/wms/stock-movements/internal': 'INTERNAL'}
        return redirect(url_for('wms_movements', movement_type=movement_map.get(request.path, '')))

    @app.route('/wms/items/create')
    @wms_permission_required('items', 'create')
    def wms_items_create_alias():
        return redirect(url_for('wms_items_new'))

    @app.route('/wms/items/categories')
    @wms_permission_required('items', 'view')
    def wms_item_categories_alias():
        return redirect(url_for('wms_item_categories'))

    @app.route('/wms/items/brands')
    @wms_permission_required('items', 'view')
    def wms_item_brands_alias():
        return redirect(url_for('wms_item_brands'))

    @app.route('/wms/items/uom')
    @app.route('/wms/items/barcode')
    @wms_permission_required('items', 'view')
    def wms_item_master_aliases():
        return redirect(url_for('wms_items'))

    @app.route('/wms/locations/zones')
    @app.route('/wms/locations/bins')
    @app.route('/wms/locations/capacity')
    @app.route('/wms/locations/mapping')
    @wms_permission_required('locations', 'view')
    def wms_location_aliases():
        return redirect(url_for('wms_locations'))

    @app.route('/wms/stock-counts/plans')
    @app.route('/wms/stock-counts/open')
    @app.route('/wms/stock-counts/variances')
    @app.route('/wms/stock-counts/history')
    @wms_permission_required('stock_count', 'view')
    def wms_stock_count_aliases():
        status_map = {'/wms/stock-counts/open': 'IN_PROGRESS', '/wms/stock-counts/variances': 'VARIANCE', '/wms/stock-counts/history': 'COMPLETED'}
        return redirect(url_for('wms_stock_counts', status=status_map.get(request.path, '')))

    @app.route('/wms/receipts')
    @app.route('/wms/receipts/history')
    @app.route('/wms/receipts/today')
    @app.route('/wms/receipts/pending-putaway')
    @wms_permission_required('receiving', 'view')
    def wms_receipts_aliases():
        return redirect(url_for('wms_receiving', status='COMPLETED' if request.path.endswith('/history') else ''))

    @app.route('/wms/receipts/new')
    @wms_permission_required('receiving', 'create')
    def wms_receipts_new_alias():
        return redirect(url_for('wms_receiving_new'))

    @app.route('/wms/shipments')
    @app.route('/wms/shipments/history')
    @app.route('/wms/shipments/packed')
    @app.route('/wms/shipments/dispatched')
    @wms_permission_required('dispatch', 'view')
    def wms_shipments_aliases():
        status_map = {'/wms/shipments/packed': 'PACKED', '/wms/shipments/dispatched': 'DISPATCHED', '/wms/shipments/history': 'DELIVERED'}
        return redirect(url_for('wms_dispatch', status=status_map.get(request.path, '')))

    @app.route('/wms/shipments/new')
    @app.route('/wms/shipments/picking')
    @wms_permission_required('picking', 'view')
    def wms_shipments_work_aliases():
        return redirect(url_for('wms_picking'))

    @app.route('/wms/returns/customer')
    @app.route('/wms/returns/supplier')
    @app.route('/wms/returns/pending-inspection')
    @app.route('/wms/returns/closed')
    @wms_permission_required('returns', 'view')
    def wms_returns_aliases():
        return redirect(url_for('wms_returns', status='CLOSED' if request.path.endswith('/closed') else ''))

    @app.route('/wms/transfers/pending')
    @app.route('/wms/transfers/in-transit')
    @app.route('/wms/transfers/completed')
    @wms_permission_required('transfers', 'view')
    def wms_transfer_status_aliases():
        status_map = {'/wms/transfers/pending': 'PENDING', '/wms/transfers/in-transit': 'IN_TRANSIT', '/wms/transfers/completed': 'COMPLETED'}
        return redirect(url_for('wms_transfers', status=status_map.get(request.path, '')))

    @app.route('/wms/adjustments/positive')
    @app.route('/wms/adjustments/negative')
    @app.route('/wms/adjustments/pending')
    @app.route('/wms/adjustments/history')
    @wms_permission_required('adjustments', 'view')
    def wms_adjustment_aliases():
        return redirect(url_for('wms_adjustments', status='PENDING' if request.path.endswith('/pending') else ''))

    @app.route('/wms/putaway/pending')
    @app.route('/wms/putaway/assigned')
    @app.route('/wms/putaway/completed')
    @wms_permission_required('putaway', 'view')
    def wms_putaway_status_aliases():
        status_map = {'/wms/putaway/pending': 'PENDING', '/wms/putaway/assigned': 'ASSIGNED', '/wms/putaway/completed': 'COMPLETED'}
        return redirect(url_for('wms_putaway', status=status_map.get(request.path, '')))

    @app.route('/wms/pickup')
    @app.route('/wms/pickup/queue')
    @app.route('/wms/pickup/assigned')
    @app.route('/wms/pickup/completed')
    @app.route('/wms/pickup/short')
    @wms_permission_required('picking', 'view')
    def wms_pickup_aliases():
        status_map = {'/wms/pickup/queue': 'PENDING', '/wms/pickup/assigned': 'ASSIGNED', '/wms/pickup/completed': 'COMPLETED'}
        return redirect(url_for('wms_picking', short='1' if request.path.endswith('/short') else '', status=status_map.get(request.path, '')))

    # Historical templates and menus still build these endpoint names directly.
    # Keep them live while routing the work into the current picking workspace.
    app.add_url_rule('/wms/pickup', endpoint='wms_pickup', view_func=wms_pickup_aliases)
    app.add_url_rule('/wms/pickup/queue', endpoint='wms_pickup_queue', view_func=wms_pickup_aliases)
    app.add_url_rule('/wms/pickup/assigned', endpoint='wms_pickup_assigned', view_func=wms_pickup_aliases)
    app.add_url_rule('/wms/pickup/completed', endpoint='wms_pickup_completed', view_func=wms_pickup_aliases)
    app.add_url_rule('/wms/pickup/short', endpoint='wms_pickup_short', view_func=wms_pickup_aliases)

    @app.route('/wms/reports/stock-balance')
    @app.route('/wms/reports/movement')
    @app.route('/wms/reports/ageing')
    @app.route('/wms/reports/valuation')
    @app.route('/wms/reports/by-location')
    @wms_permission_required('reports', 'view')
    def wms_report_aliases():
        report_map = {'/wms/reports/stock-balance': 'wms_report_inventory_summary', '/wms/reports/movement': 'wms_report_stock_movement', '/wms/reports/ageing': 'wms_report_expiry', '/wms/reports/valuation': 'wms_report_inventory_summary', '/wms/reports/by-location': 'wms_report_space'}
        return redirect(url_for(report_map.get(request.path, 'wms_reports')))

    @app.route('/wms/settings/warehouse')
    @app.route('/wms/settings/location-rules')
    @app.route('/wms/settings/numbering')
    @app.route('/wms/settings/notifications')
    @wms_permission_required('settings', 'view')
    def wms_settings_aliases():
        return redirect(url_for('wms_settings'))

    # ============================================================
    # API EXPORT ENDPOINTS
    # ============================================================

    @app.route('/api/export/<export_type>', methods=['GET', 'POST'])
    @app.route('/api/export/<data_type>/<export_type>', methods=['GET', 'POST'])
    @wms_permission_required('reports', 'view')
    def api_wms_export(export_type, data_type=None):
        """Export WMS data in all 20 formats."""
        if export_type not in WMS_EXPORT_TYPES:
            return jsonify({
                'error': f'Invalid export type. Valid types: {WMS_EXPORT_TYPES}'
            }), 400

        db = get_db()
        company_id = session.get('company_id', 0)
        wh_filter = get_warehouse_filter(session.get('user_id'))
        try:
            export_limit = min(max(int(request.args.get('limit', 5000)), 1), 50000)
        except (TypeError, ValueError):
            export_limit = 5000

        # Determine data type from URL or default
        if data_type is None:
            data_type = request.args.get('type', 'inventory')

        # Get data based on type
        if data_type == 'warehouses':
            data = db.execute(f"""
                SELECT id as warehouse_id, name, COALESCE(address, '') as location,
                       type, '' as capacity,
                       CASE WHEN is_active = 1 THEN 'Active' ELSE 'Inactive' END as status
                FROM wms_warehouses
                WHERE company_id = ? {wh_filter}
                ORDER BY name
                LIMIT ?
            """, (company_id, export_limit)).fetchall()
            data = [dict(row) for row in data]
            columns = WMS_EXPORT_COLUMNS['warehouses']
            title = 'Warehouses'
        elif data_type == 'items':
            data = db.execute("""
                SELECT id as item_id, item_code as sku, name, category_id as category,
                       unit_of_measure as unit, reorder_point as reorder_level
                FROM wms_items
                ORDER BY name
                LIMIT ?
            """, (export_limit,)).fetchall()
            data = [dict(row) for row in data]
            columns = WMS_EXPORT_COLUMNS['items']
            title = 'WMS Items'
        elif data_type == 'inventory':
            data = db.execute(f"""
                SELECT b.item_id, w.name as warehouse, loc.code as location,
                       b.quantity, b.reserved_quantity as reserved,
                       (COALESCE(b.quantity, 0) - COALESCE(b.reserved_quantity, 0)) as available
                FROM wms_inventory_balances b
                LEFT JOIN wms_warehouses w ON b.warehouse_id = w.id
                LEFT JOIN wms_locations loc ON b.location_id = loc.id
                WHERE b.company_id = ? {wh_filter.replace('warehouse_id', 'b.warehouse_id')}
                ORDER BY b.updated_at DESC
                LIMIT ?
            """, (company_id, export_limit)).fetchall()
            data = [dict(row) for row in data]
            columns = WMS_EXPORT_COLUMNS['inventory']
            title = 'WMS Inventory'
        elif data_type == 'receiving':
            data = db.execute(f"""
                SELECT id as receiving_id, po_reference as po_number, supplier_id as supplier,
                       COALESCE(actual_arrival_date, expected_date, created_at) as received_date, status
                FROM wms_inbound_receipts
                WHERE company_id = ? {wh_filter}
                ORDER BY COALESCE(actual_arrival_date, expected_date, created_at) DESC
                LIMIT ?
            """, (company_id, export_limit)).fetchall()
            data = [dict(row) for row in data]
            columns = WMS_EXPORT_COLUMNS['receiving']
            title = 'Inbound Receipts'
        elif data_type == 'putaway':
            data = db.execute(f"""
                SELECT p.id as putaway_id, p.receipt_line_id as receiving_id,
                       p.item_id, loc.code as location, p.quantity, p.status
                FROM wms_putaway_tasks p
                LEFT JOIN wms_locations loc ON p.destination_location_id = loc.id
                WHERE 1 = 1 {wh_filter.replace('warehouse_id', 'loc.warehouse_id')}
                ORDER BY p.created_at DESC
                LIMIT ?
            """, (export_limit,)).fetchall()
            data = [dict(row) for row in data]
            columns = WMS_EXPORT_COLUMNS['putaway']
            title = 'Putaway Tasks'
        elif data_type == 'transfers':
            data = db.execute(f"""
                SELECT t.id as transfer_id, ws.name as from_warehouse,
                       wd.name as to_warehouse, tl.item_id as item,
                       tl.requested_quantity as quantity, t.status
                FROM wms_transfers t
                LEFT JOIN wms_warehouses ws ON t.source_warehouse_id = ws.id
                LEFT JOIN wms_warehouses wd ON t.destination_warehouse_id = wd.id
                LEFT JOIN wms_transfer_lines tl ON tl.transfer_id = t.id
                WHERE COALESCE(t.source_company_id, t.destination_company_id, ?) = ?
                  {wh_filter.replace('warehouse_id', 't.source_warehouse_id')}
                ORDER BY t.created_at DESC
                LIMIT ?
            """, (company_id, company_id, export_limit)).fetchall()
            data = [dict(row) for row in data]
            columns = WMS_EXPORT_COLUMNS['transfers']
            title = 'Warehouse Transfers'
        elif data_type == 'picking':
            data = db.execute(f"""
                SELECT p.id as picking_id, o.order_number, p.item_id as item,
                       p.quantity, p.assigned_to as picker, p.status
                FROM wms_pick_tasks p
                LEFT JOIN wms_outbound_orders o ON p.order_id = o.id
                LEFT JOIN wms_locations loc ON p.source_location_id = loc.id
                WHERE 1 = 1 {wh_filter.replace('warehouse_id', 'loc.warehouse_id')}
                ORDER BY p.created_at DESC
                LIMIT ?
            """, (export_limit,)).fetchall()
            data = [dict(row) for row in data]
            columns = WMS_EXPORT_COLUMNS['picking']
            title = 'Picking Tasks'
        elif data_type == 'returns':
            data = db.execute(f"""
                SELECT r.id as return_id, r.return_number, rl.item_id as item,
                       rl.quantity_returned as quantity, r.reason_code as reason, r.status
                FROM wms_returns r
                LEFT JOIN wms_return_lines rl ON rl.return_id = r.id
                WHERE r.company_id = ? {wh_filter.replace('warehouse_id', 'r.warehouse_id')}
                ORDER BY r.created_at DESC
                LIMIT ?
            """, (company_id, export_limit)).fetchall()
            data = [dict(row) for row in data]
            columns = WMS_EXPORT_COLUMNS['returns']
            title = 'WMS Returns'
        else:
            return jsonify({'error': f'Data type {data_type} not supported'}), 400

        filename = f'wms_{data_type}_{datetime.now().strftime("%Y%m%d")}'

        return send_export_response(data, export_type, filename, columns, title)

    @app.route('/api/export/list')
    @wms_permission_required('reports', 'view')
    def list_wms_export_types():
        """List available export types for WMS module."""
        return jsonify({
            'module': 'wms',
            'data_types': list(WMS_EXPORT_COLUMNS.keys()),
            'export_types': [{'type': t} for t in WMS_EXPORT_TYPES]
        })
