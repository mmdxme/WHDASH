"""
WMS Item Service
================
Business logic for Item Master CRUD operations
— extracted from wms_routes.py.
"""

from datetime import datetime
from services.wms.helpers import (
    log_wms_audit, validate_item_payload
)


class WMSItemService:
    """Handles all item master business logic."""

    def __init__(self, get_db):
        self.get_db = get_db

    def get_items(self, filters=None):
        """Get paginated item list with filters."""
        db = self.get_db()
        filters = filters or {}

        query = '''
            SELECT i.*, b.name as brand_name, c.name as category_name
            FROM wms_items i
            LEFT JOIN wms_item_brands b ON b.id = i.brand_id
            LEFT JOIN wms_item_categories c ON c.id = i.category_id
            WHERE 1=1
        '''
        params = []

        if filters.get('search'):
            query += (" AND (i.item_code LIKE ? OR i.name LIKE ? "
                      "OR i.sku LIKE ? OR i.barcode LIKE ? OR i.part_number LIKE ?)")
            s = f"%{filters['search']}%"
            params.extend([s, s, s, s, s])
        if filters.get('category'):
            query += " AND i.category_id = ?"
            params.append(filters['category'])
        if filters.get('brand'):
            query += " AND i.brand_id = ?"
            params.append(filters['brand'])
        if filters.get('status'):
            query += " AND i.selling_status = ?"
            params.append(filters['status'])

        total = len(db.execute(query, params).fetchall())
        page = int(filters.get('page', 1))
        per_page = int(filters.get('per_page', 50))

        query += " ORDER BY i.name LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        items = db.execute(query, params).fetchall()

        return {
            'items': [dict(r) for r in items],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
        }

    def get_item_detail(self, item_id):
        """Get full item detail with stock, lots, movements."""
        db = self.get_db()
        item = db.execute('''
            SELECT i.*, b.name as brand_name, c.name as category_name,
                   g.name as group_name
            FROM wms_items i
            LEFT JOIN wms_item_brands b ON b.id = i.brand_id
            LEFT JOIN wms_item_categories c ON c.id = i.category_id
            LEFT JOIN wms_item_groups g ON g.id = i.group_id
            WHERE i.id = ?
        ''', (item_id,)).fetchone()
        if not item:
            return None

        result = dict(item)

        # Stock by warehouse
        result['stock_by_warehouse'] = [dict(r) for r in db.execute('''
            SELECT w.name as warehouse_name,
                   SUM(b.quantity) as total_qty,
                   SUM(b.reserved_quantity) as reserved_qty
            FROM wms_inventory_balances b
            JOIN wms_warehouses w ON w.id = b.warehouse_id
            WHERE b.item_id = ?
            GROUP BY b.warehouse_id
        ''', (item_id,)).fetchall()]

        # Active lots
        result['lots'] = [dict(r) for r in db.execute('''
            SELECT l.*, w.name as warehouse_name
            FROM wms_lots l
            JOIN wms_warehouses w ON w.id = l.warehouse_id
            WHERE l.item_id = ? AND l.quantity > 0
            ORDER BY l.expiry_date
        ''', (item_id,)).fetchall()]

        # Recent movements
        result['movements'] = [dict(r) for r in db.execute('''
            SELECT il.*, w.name as warehouse_name, u.username
            FROM wms_inventory_ledger il
            JOIN wms_warehouses w ON w.id = il.warehouse_id
            LEFT JOIN users u ON u.id = il.user_id
            WHERE il.item_id = ?
            ORDER BY il.created_at DESC LIMIT 20
        ''', (item_id,)).fetchall()]

        return result

    def create_item(self, user_id, data):
        """Create a new item master record."""
        errors = validate_item_payload(data, get_db=self.get_db)
        if errors:
            raise ValueError('; '.join(errors))

        db = self.get_db()
        now = datetime.now().isoformat()

        db.execute('''
            INSERT INTO wms_items
            (item_code, name, sku, barcode, part_number, description,
             category_id, brand_id, group_id, uom, secondary_uom,
             conversion_rate, weight_kg, volume_m3,
             length_cm, width_cm, height_cm,
             shelf_life_days, is_lot_tracked, is_serial_tracked,
             is_batch_tracked, is_hazardous, storage_condition,
             min_stock_level, max_stock_level, reorder_point,
             reorder_quantity, safety_stock, economic_order_quantity,
             preferred_warehouse_id, preferred_location_id,
             selling_status, is_active, created_at, updated_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,1,?,?)
        ''', (
            data.get('item_code', '').strip(),
            data.get('name', '').strip(),
            data.get('sku'), data.get('barcode'), data.get('part_number'),
            data.get('description'),
            data.get('category_id') or None,
            data.get('brand_id') or None,
            data.get('group_id') or None,
            data.get('uom', 'PCS'),
            data.get('secondary_uom'),
            data.get('conversion_rate') or None,
            data.get('weight_kg') or None,
            data.get('volume_m3') or None,
            data.get('length_cm') or None,
            data.get('width_cm') or None,
            data.get('height_cm') or None,
            data.get('shelf_life_days') or None,
            1 if data.get('is_lot_tracked') else 0,
            1 if data.get('is_serial_tracked') else 0,
            1 if data.get('is_batch_tracked') else 0,
            1 if data.get('is_hazardous') else 0,
            data.get('storage_condition'),
            data.get('min_stock_level') or None,
            data.get('max_stock_level') or None,
            data.get('reorder_point') or None,
            data.get('reorder_quantity') or None,
            data.get('safety_stock') or None,
            data.get('economic_order_quantity') or None,
            data.get('preferred_warehouse_id') or None,
            data.get('preferred_location_id') or None,
            data.get('selling_status', 'ACTIVE'),
            now, now
        ))
        item_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        db.commit()

        log_wms_audit('CREATE', 'item', item_id,
                      {'code': data.get('item_code')},
                      user_id, get_db=self.get_db)
        return item_id

    def get_lookups(self):
        """Get categories, brands, groups for dropdowns."""
        db = self.get_db()
        return {
            'categories': [dict(r) for r in db.execute(
                'SELECT * FROM wms_item_categories WHERE is_active = 1 ORDER BY name'
            ).fetchall()],
            'brands': [dict(r) for r in db.execute(
                'SELECT * FROM wms_item_brands WHERE is_active = 1 ORDER BY name'
            ).fetchall()],
            'groups': [dict(r) for r in db.execute(
                'SELECT * FROM wms_item_groups WHERE is_active = 1 ORDER BY name'
            ).fetchall()],
        }
