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
from datetime import datetime, timedelta, date
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from collections import Counter
import re


def register_wms_routes(app, get_db):
    """Register all WMS routes with the Flask app."""

    # ============================================================
    # DECORATORS & HELPERS
    # ============================================================

    def wms_permission_required(permission=None):
        """Decorator to check WMS-specific permissions."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if 'user_id' not in session:
                    return redirect(url_for('login'))
                if permission:
                    user_perms = session.get('wms_permissions', {})
                    if permission not in user_perms and not session.get('can_manage_users'):
                        flash(f'You do not have permission: {permission}', 'error')
                        return redirect(url_for('wms_dashboard'))
                return f(*args, **kwargs)
            return decorated_function
        return decorator

    def get_wms_permissions(user_id=None):
        """Get WMS permissions for a user."""
        db = get_db()
        if user_id is None:
            user_id = session.get('user_id')

        # Check if user is super admin
        role = db.execute('SELECT can_manage_users FROM roles WHERE id = ?', (session.get('role_id'),)).fetchone()
        if role and role['can_manage_users']:
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
                temperature Requirement TEXT,
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

    # Initialize tables on first request
    init_wms_tables()

    # ============================================================
    # WMS DASHBOARD
    # ============================================================

    @app.route('/wms')
    @app.route('/wms/dashboard')
    def wms_dashboard():
        """Main WMS Dashboard."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
        near_expiry_days = int(db.execute("SELECT setting_value FROM wms_settings WHERE setting_key = 'near_expiry_days'").fetchone()['setting_value'] or 30)
        near_expiry = db.execute(f'''
            SELECT COALESCE(SUM(l.quantity), 0) as qty FROM wms_lots l
            WHERE l.expiry_date IS NOT NULL
            AND l.expiry_date <= date('now', '+{near_expiry_days} days')
            AND l.expiry_date > date('now')
            AND l.quantity > 0
            {wh_filter.replace('warehouse_id', 'l.warehouse_id')}
        ''').fetchone()['qty']

        # Expired stock
        expired_stock = db.execute(f'''
            SELECT COALESCE(SUM(l.quantity), 0) as qty FROM wms_lots l
            WHERE l.expiry_date IS NOT NULL
            AND l.expiry_date < date('now')
            AND l.quantity > 0
            {wh_filter.replace('warehouse_id', 'l.warehouse_id')}
        ''').fetchone()['qty']

        # Empty locations
        empty_locations = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_locations
            WHERE is_empty = 1 AND is_active = 1 {wh_filter}
        ''').fetchone()['cnt']

        # Total locations
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
            SELECT COUNT(*) as cnt FROM wms_pick_tasks
            WHERE status IN ('PENDING', 'IN_PROGRESS') {wh_filter.replace('warehouse_id', 'wms_pick_tasks.warehouse_id')}
        ''').fetchone()['cnt']

        pending_packing = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_pack_tasks
            WHERE status = 'PENDING' {wh_filter.replace('warehouse_id', 'wms_pack_tasks.warehouse_id')}
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
    def wms_items():
        """Item master list."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_items_new():
        """Create new item."""
        if 'user_id' not in session:
            return redirect(url_for('login'))
        db = get_db()

        if request.method == 'POST':
            data = request.form
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
                flash(f'Error creating item: {e}', 'error')

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
    def wms_item_detail(item_id):
        """Item detail view with tabs."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_items_edit(item_id):
        """Edit item."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        db = get_db()
        item = db.execute('SELECT * FROM wms_items WHERE id = ?', (item_id,)).fetchone()
        if not item:
            flash('Item not found.', 'error')
            return redirect(url_for('wms_items'))

        if request.method == 'POST':
            data = request.form
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
                flash(f'Error updating item: {e}', 'error')

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
    def wms_warehouses():
        """Warehouse list."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_warehouses_new():
        """Create new warehouse."""
        if 'user_id' not in session:
            return redirect(url_for('login'))
        db = get_db()

        if request.method == 'POST':
            data = request.form
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
                flash(f'Error creating warehouse: {e}', 'error')

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
    def wms_warehouse_detail(warehouse_id):
        """Warehouse detail view."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_warehouses_edit(warehouse_id):
        """Edit warehouse."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
                flash(f'Error updating warehouse: {e}', 'error')

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
    def wms_locations():
        """Locations list."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_locations_new():
        """Create new location."""
        if 'user_id' not in session:
            return redirect(url_for('login'))
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
                flash(f'Error creating location: {e}', 'error')

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
    def wms_location_detail(location_id):
        """Location detail."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_locations_edit(location_id):
        """Edit location."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
                flash(f'Error updating location: {e}', 'error')

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
    def wms_inventory():
        """Inventory overview."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        db = get_db()
        search = request.args.get('search', '').strip()
        warehouse_id = request.args.get('warehouse_id', '')
        location_id = request.args.get('location_id', '')
        category_id = request.args.get('category_id', '')
        brand_id = request.args.get('brand_id', '')
        status = request.args.get('status', '')
        stock_filter = request.args.get('stock_filter', '')
        page = int(request.args.get('page', 1))
        per_page = 100

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
        if warehouse_id:
            query += " AND b.warehouse_id = ?"
            params.append(warehouse_id)
        if location_id:
            query += " AND b.location_id = ?"
            params.append(location_id)
        if category_id:
            query += " AND i.category_id = ?"
            params.append(category_id)
        if brand_id:
            query += " AND i.brand_id = ?"
            params.append(brand_id)
        if status:
            query += " AND b.status = ?"
            params.append(status)
        if stock_filter == 'zero':
            query += " AND b.quantity = 0"
        elif stock_filter == 'negative':
            query += " AND b.quantity < 0"
        elif stock_filter == 'low':
            query += " AND i.min_stock_level > 0 AND b.quantity < i.min_stock_level"
        elif stock_filter == 'below_reorder':
            query += " AND i.reorder_point > 0 AND b.quantity < i.reorder_point"
        elif stock_filter == 'available_only':
            query += " AND b.status = 'AVAILABLE' AND b.quantity > 0"
        elif stock_filter == 'reserved':
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
            ''' + ('' if not warehouse_id else ' AND b.warehouse_id = ' + warehouse_id),
            ([] if not warehouse_id else [warehouse_id])
        ).fetchone()

        title = 'Inventory Overview'
        return render_template('wms/inventory.html',
            title=title,
            inventory=inventory,
            warehouses=warehouses,
            categories=categories,
            brands=brands,
            search=search,
            warehouse_id=warehouse_id,
            location_id=location_id,
            category_id=category_id,
            brand_id=brand_id,
            status=status,
            stock_filter=stock_filter,
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
    def wms_receiving():
        """Receiving/Inbound list."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_receiving_new():
        """Create new inbound receipt."""
        if 'user_id' not in session:
            return redirect(url_for('login'))
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
                flash(f'Error creating receipt: {e}', 'error')

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
    def wms_receiving_detail(receipt_id):
        """Receiving detail with lines."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_receiving_receive(receipt_id):
        """Receive items against a receipt."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
            flash(f'Error receiving: {e}', 'error')

        return redirect(url_for('wms_receiving_detail', receipt_id=receipt_id))

    # ============================================================
    # PUTAWAY
    # ============================================================

    @app.route('/wms/putaway')
    def wms_putaway():
        """Putaway tasks list."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
            JOIN wms_warehouses w ON w.id = p.warehouse_id
            LEFT JOIN wms_locations sl ON sl.id = p.source_location_id
            LEFT JOIN wms_locations dl ON dl.id = p.destination_location_id
            LEFT JOIN users u ON u.id = p.assigned_to
            WHERE 1=1
        '''
        params = []
        if status:
            query += " AND p.status = ?"
            params.append(status)
        if warehouse_id:
            query += " AND p.warehouse_id = ?"
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
    def wms_putaway_complete(task_id):
        """Complete a putaway task."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        db = get_db()
        try:
            task = db.execute('SELECT * FROM wms_putaway_tasks WHERE id = ?', (task_id,)).fetchone()
            if not task:
                flash('Task not found.', 'error')
                return redirect(url_for('wms_putaway'))

            db.execute('''
                UPDATE wms_putaway_tasks SET
                    status = 'COMPLETED',
                    destination_location_id = ?,
                    completed_at = datetime('now'),
                    completed_by = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (request.form.get('location_id'), session.get('user_id'), task_id))
            db.commit()
            log_wms_audit('COMPLETE', 'PUTAWAY_TASK', task_id)
            flash('Putaway task completed!', 'success')
        except Exception as e:
            flash(f'Error completing task: {e}', 'error')

        return redirect(url_for('wms_putaway'))

    # ============================================================
    # INTERNAL MOVEMENTS
    # ============================================================

    @app.route('/wms/movements')
    def wms_movements():
        """Internal movements list."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        db = get_db()
        movement_type = request.args.get('movement_type', '')
        warehouse_id = request.args.get('warehouse_id', '')
        search = request.args.get('search', '').strip()
        page = int(request.args.get('page', 1))
        per_page = 50

        query = '''
            SELECT m.*, i.item_code, i.name as item_name,
                   w.name as warehouse_name,
                   sl.code as source_location, dl.code as dest_location,
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
    def wms_movements_new():
        """Create new internal movement."""
        if 'user_id' not in session:
            return redirect(url_for('login'))
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
                flash(f'Error creating movement: {e}', 'error')

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
    def wms_replenishment():
        """Replenishment tasks."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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

    # ============================================================
    # PICKING
    # ============================================================

    @app.route('/wms/picking')
    def wms_picking():
        """Pick tasks."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
            JOIN wms_warehouses w ON w.id = p.warehouse_id
            LEFT JOIN wms_locations l ON l.id = p.source_location_id
            LEFT JOIN users u ON u.id = p.assigned_to
            LEFT JOIN wms_outbound_orders o ON o.id = p.order_id
            WHERE 1=1
        '''
        params = []
        if status:
            query += " AND p.status = ?"
            params.append(status)
        if warehouse_id:
            query += " AND p.warehouse_id = ?"
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

    # ============================================================
    # PACKING
    # ============================================================

    @app.route('/wms/packing')
    def wms_packing():
        """Pack tasks."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
            JOIN wms_warehouses w ON w.id = p.warehouse_id
            LEFT JOIN users u ON u.id = p.assigned_to
            WHERE 1=1
        '''
        params = []
        if status:
            query += " AND p.status = ?"
            params.append(status)
        if warehouse_id:
            query += " AND p.warehouse_id = ?"
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

    # ============================================================
    # DISPATCH / SHIPPING
    # ============================================================

    @app.route('/wms/dispatch')
    def wms_dispatch():
        """Dispatch/Shipping."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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

    # ============================================================
    # TRANSFERS
    # ============================================================

    @app.route('/wms/transfers')
    def wms_transfers():
        """Transfers list."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_transfers_new():
        """Create new transfer."""
        if 'user_id' not in session:
            return redirect(url_for('login'))
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
                flash(f'Error creating transfer: {e}', 'error')

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
    def wms_transfer_detail(transfer_id):
        """Transfer detail."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_returns():
        """Returns list."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_returns_new():
        """Create new return."""
        if 'user_id' not in session:
            return redirect(url_for('login'))
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
                flash(f'Error creating return: {e}', 'error')

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
    def wms_return_detail(return_id):
        """Return detail."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_stock_counts():
        """Stock counts list."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_stock_counts_new():
        """Create new stock count."""
        if 'user_id' not in session:
            return redirect(url_for('login'))
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
                flash(f'Error creating stock count: {e}', 'error')

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
    def wms_stock_count_detail(count_id):
        """Stock count detail."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_adjustments():
        """Stock adjustments."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_adjustments_new():
        """Create new stock adjustment."""
        if 'user_id' not in session:
            return redirect(url_for('login'))
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
                flash(f'Error creating adjustment: {e}', 'error')

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
    def wms_adjustment_detail(adjustment_id):
        """Adjustment detail."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_quality():
        """QC Inspections."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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

    # ============================================================
    # DOCUMENTS / FORMS
    # ============================================================

    @app.route('/wms/documents')
    def wms_documents():
        """WMS Documents."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_reports():
        """WMS Reports index."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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

    # ============================================================
    # WMS SETTINGS
    # ============================================================

    @app.route('/wms/settings')
    def wms_settings():
        """WMS Settings."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_settings_save():
        """Save WMS settings."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
            flash(f'Error saving settings: {e}', 'error')

        return redirect(url_for('wms_settings'))

    # ============================================================
    # ZONES CRUD
    # ============================================================

    @app.route('/wms/zones/new', methods=['GET', 'POST'])
    def wms_zones_new():
        """Create new zone."""
        if 'user_id' not in session:
            return redirect(url_for('login'))
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
                flash(f'Error creating zone: {e}', 'error')

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
    def wms_item_categories():
        """Item categories."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_item_categories_new():
        """Create new item category."""
        if 'user_id' not in session:
            return redirect(url_for('login'))
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
                flash(f'Error creating category: {e}', 'error')

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
    def wms_item_brands():
        """Item brands."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_item_brands_new():
        """Create new brand."""
        if 'user_id' not in session:
            return redirect(url_for('login'))
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
                flash(f'Error creating brand: {e}', 'error')

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
    def wms_lots():
        """Lots/Batches list."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_work_tasks():
        """Work queue / tasks."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_alerts():
        """WMS Alerts."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        db = get_db()
        severity = request.args.get('severity', '')
        is_active = request.args.get('is_active', '1')
        page = int(request.args.get('page', 1))
        per_page = 50

        query = '''
            SELECT a.*, w.name as warehouse_name, i.item_code, i.name as item_name
            FROM wms_alerts a
            LEFT JOIN wms_warehouses w ON w.id = a.warehouse_id
            LEFT JOIN wms_items i ON i.id = a.item_id
            WHERE 1=1
        '''
        params = []
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
    def wms_alerts_acknowledge(alert_id):
        """Acknowledge an alert."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        db = get_db()
        try:
            db.execute('''
                UPDATE wms_alerts SET is_acknowledged = 1, acknowledged_by = ?, acknowledged_at = datetime('now')
                WHERE id = ?
            ''', (session.get('user_id'), alert_id))
            db.commit()
            flash('Alert acknowledged.', 'success')
        except Exception as e:
            flash(f'Error: {e}', 'error')

        return redirect(url_for('wms_alerts'))

    # ============================================================
    # API ENDPOINTS
    # ============================================================

    @app.route('/wms/api/locations/<int:warehouse_id>')
    def wms_api_locations(warehouse_id):
        """API: Get locations for a warehouse."""
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

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
    def wms_api_items_search():
        """API: Search items."""
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

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
    def wms_api_stock(item_id):
        """API: Get stock for an item."""
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

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
    def wms_api_dashboard_stats():
        """API: Dashboard statistics for AJAX refresh."""
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

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
                SELECT COUNT(*) as cnt FROM wms_pick_tasks WHERE status IN ('PENDING', 'IN_PROGRESS') {wh_filter.replace('warehouse_id', 'wms_pick_tasks.warehouse_id')}
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
    def wms_export_inventory():
        """Export inventory to Excel."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        db = get_db()
        warehouse_id = request.args.get('warehouse_id', '')

        query = '''
            SELECT i.item_code, i.name as item_name, i.unit_of_measure,
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
        if warehouse_id:
            query += " AND b.warehouse_id = ?"
            params.append(warehouse_id)

        query += " ORDER BY i.name"
        rows = db.execute(query, params).fetchall()

        wb = Workbook()
        ws = wb.active
        ws.title = "Inventory"

        headers = ['Item Code', 'Item Name', 'UOM', 'Brand', 'Category', 'Warehouse',
                    'Location', 'Lot Number', 'Expiry Date', 'Quantity',
                    'Reserved', 'Allocated', 'Status']
        ws.append(headers)

        for row in rows:
            ws.append([
                row['item_code'], row['item_name'], row['unit_of_measure'],
                row['brand'] or '', row['category'] or '', row['warehouse'] or '',
                row['location'] or '', row['lot_number'] or '', row['expiry_date'] or '',
                row['quantity'], row['reserved_quantity'], row['allocated_quantity'],
                row['status']
            ])

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                         download_name=f'wms_inventory_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')

    @app.route('/wms/export/items')
    def wms_export_items():
        """Export items to Excel."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_print_grn(receipt_id):
        """Print Goods Receipt Note."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
    def wms_print_pick_list(order_id):
        """Print Pick List."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

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
