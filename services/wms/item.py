"""WMS Item Service - Item master CRUD and validation."""
from services.base import BaseService


class ItemService(BaseService):
    """Service for item master management."""

    def search_items(self, search='', category='', brand='', status='', page=1, per_page=50):
        """Search items with filters."""
        db = self.get_db()
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
            sp = f'%{search}%'
            params.extend([sp, sp, sp, sp, sp])

        if category:
            query += " AND i.category_id = ?"
            params.append(category)

        if brand:
            query += " AND i.brand_id = ?"
            params.append(brand)

        if status:
            query += " AND i.selling_status = ?"
            params.append(status)

        total = len(db.execute(query, params).fetchall())
        query += " ORDER BY i.name LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])
        items = db.execute(query, params).fetchall()

        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page
        }

    def get_item_by_id(self, item_id):
        """Get item detail with joins."""
        db = self.get_db()
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
        return item

    def get_item_by_code(self, item_code):
        """Get item by item_code."""
        db = self.get_db()
        return db.execute('SELECT * FROM wms_items WHERE item_code = ?', (item_code,)).fetchone()

    def create_item(self, data, user_id=None):
        """Create new item with all fields."""
        db = self.get_db()
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
            user_id
        ))
        db.commit()
        return db.execute('SELECT last_insert_rowid()').fetchone()[0]

    def update_item(self, item_id, data, user_id=None):
        """Update existing item."""
        db = self.get_db()
        db.execute('''
            UPDATE wms_items SET
                item_code=?, sku=?, barcode=?, qr_code=?, part_number=?, oem_number=?,
                alternate_part_numbers=?, supplier_code=?, name=?, name_local=?,
                short_name=?, long_description=?, brand_id=?, category_id=?, group_id=?,
                item_type=?, unit_of_measure=?, secondary_uom=?, conversion_rate=?,
                weight_kg=?, volume_m3=?, length_cm=?, width_cm=?, height_cm=?,
                color=?, size=?, material=?, country_of_origin=?, hazard_class=?,
                temperature_requirement=?, shelf_life_days=?, expiry_tracking=?,
                batch_tracking=?, lot_tracking=?, serial_tracking=?,
                quality_inspection_required=?, min_stock_level=?, max_stock_level=?,
                reorder_point=?, reorder_quantity=?, safety_stock=?,
                economic_order_quantity=?, preferred_warehouse_id=?,
                preferred_location_id=?, rotation_policy=?, picking_strategy=?,
                packing_instruction=?, handling_instruction=?, selling_status=?,
                procurement_status=?, abc_class=?, is_kit=?, is_bundle=?,
                kit_components=?, is_active=?, updated_by=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
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
            user_id,
            item_id
        ))
        db.commit()

    def delete_item(self, item_id):
        """Soft delete item - set is_active=0."""
        db = self.get_db()
        db.execute('UPDATE wms_items SET is_active=0, updated_at=CURRENT_TIMESTAMP WHERE id=?', (item_id,))
        db.commit()

    def get_stock_by_warehouse(self, item_id):
        """Get stock levels grouped by warehouse."""
        db = self.get_db()
        return db.execute('''
            SELECT w.name as warehouse_name,
                   COALESCE(SUM(b.quantity), 0) as quantity,
                   COALESCE(SUM(b.reserved_quantity), 0) as reserved,
                   COALESCE(SUM(b.allocated_quantity), 0) as allocated
            FROM wms_inventory_balances b
            JOIN wms_warehouses w ON w.id = b.warehouse_id
            WHERE b.item_id = ?
            GROUP BY w.id
        ''', (item_id,)).fetchall()

    def validate_item_code_unique(self, item_code, exclude_id=None):
        """Check if item_code is unique."""
        db = self.get_db()
        if exclude_id:
            result = db.execute(
                'SELECT id FROM wms_items WHERE item_code = ? AND id != ?',
                (item_code, exclude_id)
            ).fetchone()
        else:
            result = db.execute(
                'SELECT id FROM wms_items WHERE item_code = ?',
                (item_code,)
            ).fetchone()
        return result is None