"""WMS Inventory Service - Dashboard KPIs and inventory queries."""
from services.base import BaseService


class InventoryService(BaseService):
    """Service for inventory dashboard, KPIs, and stock queries."""

    def get_inventory_metrics(self, warehouse_ids=None, user_id=None):
        """Get inventory dashboard metrics summary."""
        db = self.get_db()
        params = []
        wh_filter = ''
        if warehouse_ids:
            placeholders = ','.join(['?'] * len(warehouse_ids))
            wh_filter = f' AND b.warehouse_id IN ({placeholders})'
            params.extend(warehouse_ids)

        summary = db.execute(f'''
            SELECT
                COALESCE(SUM(quantity), 0) as total_qty,
                COALESCE(SUM(reserved_quantity), 0) as total_reserved,
                COALESCE(SUM(allocated_quantity), 0) as total_allocated,
                COALESCE(SUM(CASE WHEN status = 'AVAILABLE' THEN quantity ELSE 0 END), 0) as available,
                COALESCE(SUM(CASE WHEN status IN ('BLOCKED','QUARANTINE') THEN quantity ELSE 0 END), 0) as blocked,
                COALESCE(SUM(CASE WHEN status = 'DAMAGED' THEN quantity ELSE 0 END), 0) as damaged,
                COALESCE(SUM(CASE WHEN status = 'RESERVED' THEN quantity ELSE 0 END), 0) as reserved,
                COUNT(DISTINCT item_id) as sku_count,
                COUNT(DISTINCT warehouse_id) as warehouse_count
            FROM wms_inventory_balances b
            JOIN wms_items i ON i.id = b.item_id
            WHERE 1=1 {wh_filter}
        ''', params).fetchone()
        return summary

    def get_stock_health_summary(self, warehouse_ids=None):
        """Get stock health: zero stock, below safety, below ROP."""
        db = self.get_db()
        params = []
        wh_filter = ''
        if warehouse_ids:
            placeholders = ','.join(['?'] * len(warehouse_ids))
            wh_filter = f' AND b.warehouse_id IN ({placeholders})'
            params.extend(warehouse_ids)

        zero_stock = db.execute(f'''
            SELECT COUNT(DISTINCT b.item_id) as count
            FROM wms_inventory_balances b
            JOIN wms_items i ON i.id = b.item_id
            WHERE b.quantity = 0 {wh_filter}
        ''', params).fetchone()['count']

        below_min = db.execute(f'''
            SELECT COUNT(DISTINCT b.item_id) as count
            FROM wms_inventory_balances b
            JOIN wms_items i ON i.id = b.item_id
            WHERE i.min_stock_level > 0 AND b.quantity < i.min_stock_level {wh_filter}
        ''', params).fetchone()['count']

        below_reorder = db.execute(f'''
            SELECT COUNT(DISTINCT b.item_id) as count
            FROM wms_inventory_balances b
            JOIN wms_items i ON i.id = b.item_id
            WHERE i.reorder_point > 0 AND b.quantity < i.reorder_point {wh_filter}
        ''', params).fetchone()['count']

        negative_stock = db.execute(f'''
            SELECT COUNT(*) as count
            FROM wms_inventory_balances
            WHERE quantity < 0 {wh_filter}
        ''', params).fetchone()['count']

        return {
            'zero_stock_count': zero_stock,
            'below_min_count': below_min,
            'below_reorder_count': below_reorder,
            'negative_stock_count': negative_stock
        }

    def search_inventory_items(self, search='', warehouse_ids=None, location_id=None,
                               category_ids=None, brand_id=None, statuses=None,
                               stock_filters=None, page=1, per_page=100):
        """Search inventory with filters and pagination."""
        db = self.get_db()

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

        return {
            'items': inventory,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page if total > 0 else 1
        }

    def validate_inventory_operation(self, item_id, warehouse_id, location_id=None, quantity=None):
        """Validate inventory operation before execution."""
        db = self.get_db()
        errors = []

        item = db.execute('SELECT id FROM wms_items WHERE id = ? AND is_active = 1', (item_id,)).fetchone()
        if not item:
            errors.append('Item not found or inactive.')

        warehouse = db.execute('SELECT id FROM wms_warehouses WHERE id = ? AND is_active = 1', (warehouse_id,)).fetchone()
        if not warehouse:
            errors.append('Warehouse not found or inactive.')

        if location_id:
            loc = db.execute('SELECT id FROM wms_locations WHERE id = ? AND is_active = 1', (location_id,)).fetchone()
            if not loc:
                errors.append('Location not found or inactive.')

        if quantity is not None and quantity < 0:
            errors.append('Quantity cannot be negative.')

        return errors