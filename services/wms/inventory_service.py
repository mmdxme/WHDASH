"""
WMS Inventory Service
=====================
Business logic for inventory management, stock movements, adjustments,
replenishment, and stock counting — extracted from wms_routes.py.
"""

from datetime import datetime
from services.wms.helpers import (
    get_warehouse_filter, log_wms_audit,
    create_wms_notification, generate_wms_code
)


class WMSInventoryService:
    """Handles all inventory-related business logic."""

    def __init__(self, get_db):
        self.get_db = get_db

    # ------------------------------------------------------------------
    # Inventory Overview
    # ------------------------------------------------------------------

    def get_inventory_overview(self, user_id, filters=None):
        """Get paginated inventory balances with filters."""
        db = self.get_db()
        filters = filters or {}
        wh_filter = get_warehouse_filter(user_id, get_db=self.get_db)

        query = '''
            SELECT b.*, i.item_code, i.name as item_name, i.uom,
                   w.name as warehouse_name, l.code as location_code,
                   lt.lot_number, lt.expiry_date
            FROM wms_inventory_balances b
            JOIN wms_items i ON i.id = b.item_id
            JOIN wms_warehouses w ON w.id = b.warehouse_id
            LEFT JOIN wms_locations l ON l.id = b.location_id
            LEFT JOIN wms_lots lt ON lt.id = b.lot_id
            WHERE 1=1
        '''
        params = []

        if filters.get('search'):
            query += " AND (i.item_code LIKE ? OR i.name LIKE ?)"
            s = f"%{filters['search']}%"
            params.extend([s, s])

        if filters.get('warehouse_id'):
            query += " AND b.warehouse_id = ?"
            params.append(filters['warehouse_id'])

        if filters.get('status'):
            query += " AND b.status = ?"
            params.append(filters['status'])

        query += wh_filter
        query += " ORDER BY i.name"

        page = int(filters.get('page', 1))
        per_page = int(filters.get('per_page', 50))
        offset = (page - 1) * per_page

        total = len(db.execute(query, params).fetchall())
        query += f" LIMIT {per_page} OFFSET {offset}"
        items = db.execute(query, params).fetchall()

        return {
            'items': [dict(r) for r in items],
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page,
        }

    # ------------------------------------------------------------------
    # Internal Movements
    # ------------------------------------------------------------------

    def move_stock(self, user_id, item_id, from_location_id, to_location_id,
                   quantity, reason=None):
        """Move stock between locations within the same warehouse."""
        db = self.get_db()

        # Validate source balance
        source = db.execute('''
            SELECT * FROM wms_inventory_balances
            WHERE item_id = ? AND location_id = ? AND status = 'AVAILABLE'
        ''', (item_id, from_location_id)).fetchone()

        if not source or source['quantity'] < quantity:
            raise ValueError('Insufficient stock at source location.')

        # Deduct from source
        db.execute('''
            UPDATE wms_inventory_balances
            SET quantity = quantity - ?, updated_at = ?
            WHERE item_id = ? AND location_id = ? AND status = 'AVAILABLE'
        ''', (quantity, datetime.now().isoformat(), item_id, from_location_id))

        # Add to destination (upsert)
        existing = db.execute('''
            SELECT id FROM wms_inventory_balances
            WHERE item_id = ? AND location_id = ? AND status = 'AVAILABLE'
        ''', (item_id, to_location_id)).fetchone()

        if existing:
            db.execute('''
                UPDATE wms_inventory_balances
                SET quantity = quantity + ?, updated_at = ?
                WHERE id = ?
            ''', (quantity, datetime.now().isoformat(), existing['id']))
        else:
            # Determine warehouse from location
            loc = db.execute(
                'SELECT warehouse_id FROM wms_locations WHERE id = ?',
                (to_location_id,)
            ).fetchone()
            db.execute('''
                INSERT INTO wms_inventory_balances
                (item_id, warehouse_id, location_id, quantity, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'AVAILABLE', ?, ?)
            ''', (item_id, loc['warehouse_id'], to_location_id, quantity,
                  datetime.now().isoformat(), datetime.now().isoformat()))

        db.commit()

        log_wms_audit('MOVE', 'inventory', item_id,
                      {'from': from_location_id, 'to': to_location_id,
                       'qty': quantity, 'reason': reason},
                      user_id, get_db=self.get_db)

        return True

    # ------------------------------------------------------------------
    # Stock Adjustments
    # ------------------------------------------------------------------

    def create_adjustment(self, user_id, data):
        """Create an inventory adjustment record."""
        db = self.get_db()
        adj_number = generate_wms_code('ADJ', get_db=self.get_db)
        now = datetime.now().isoformat()

        db.execute('''
            INSERT INTO wms_stock_adjustments
            (adjustment_number, warehouse_id, adjustment_type,
             reason, status, created_by, created_at)
            VALUES (?, ?, ?, ?, 'DRAFT', ?, ?)
        ''', (adj_number, data['warehouse_id'], data.get('adjustment_type', 'MANUAL'),
              data.get('reason', ''), user_id, now))
        adj_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        db.commit()

        log_wms_audit('CREATE', 'adjustment', adj_id,
                      {'number': adj_number}, user_id, get_db=self.get_db)
        return adj_id, adj_number

    # ------------------------------------------------------------------
    # Replenishment
    # ------------------------------------------------------------------

    def get_replenishment_tasks(self, user_id, filters=None):
        """Get replenishment tasks with filters."""
        db = self.get_db()
        filters = filters or {}
        wh_filter = get_warehouse_filter(user_id, get_db=self.get_db)

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
        if filters.get('status'):
            query += " AND r.status = ?"
            params.append(filters['status'])
        if filters.get('warehouse_id'):
            query += " AND r.warehouse_id = ?"
            params.append(filters['warehouse_id'])

        query += wh_filter.replace('warehouse_id', 'r.warehouse_id')
        query += " ORDER BY r.priority DESC, r.created_at DESC"

        items = db.execute(query, params).fetchall()
        return [dict(r) for r in items]

    # ------------------------------------------------------------------
    # Stock Counting
    # ------------------------------------------------------------------

    def get_stock_counts(self, user_id, filters=None):
        """Get stock count sessions with filters."""
        db = self.get_db()
        filters = filters or {}
        wh_filter = get_warehouse_filter(user_id, get_db=self.get_db)

        query = '''
            SELECT sc.*, w.name as warehouse_name, u.username as created_by_name
            FROM wms_stock_counts sc
            JOIN wms_warehouses w ON w.id = sc.warehouse_id
            LEFT JOIN users u ON u.id = sc.created_by
            WHERE 1=1
        '''
        params = []
        if filters.get('status'):
            query += " AND sc.status = ?"
            params.append(filters['status'])
        if filters.get('warehouse_id'):
            query += " AND sc.warehouse_id = ?"
            params.append(filters['warehouse_id'])

        query += wh_filter.replace('warehouse_id', 'sc.warehouse_id')
        query += " ORDER BY sc.created_at DESC"

        items = db.execute(query, params).fetchall()
        return [dict(r) for r in items]
