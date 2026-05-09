"""
WMS Picking Service
===================
Business logic for picking, packing, dispatch, and wave management
— extracted from wms_routes.py.
"""

from datetime import datetime
from services.wms.helpers import (
    get_warehouse_filter, log_wms_audit, generate_wms_code,
    create_wms_notification
)


class WMSPickingService:
    """Handles all picking/packing/dispatch business logic."""

    def __init__(self, get_db):
        self.get_db = get_db

    def get_pick_tasks(self, user_id, filters=None):
        """Get pick tasks with filters."""
        db = self.get_db()
        filters = filters or {}
        wh_filter = get_warehouse_filter(user_id, get_db=self.get_db)

        query = '''
            SELECT p.*, i.item_code, i.name as item_name,
                   sl.code as source_location, u.username as picker_name
            FROM wms_pick_tasks p
            JOIN wms_items i ON i.id = p.item_id
            JOIN wms_locations sl ON sl.id = p.source_location_id
            LEFT JOIN users u ON u.id = p.assigned_to
            WHERE 1=1
        '''
        params = []
        if filters.get('status'):
            query += " AND p.status = ?"
            params.append(filters['status'])

        query += wh_filter.replace('warehouse_id', 'sl.warehouse_id')
        query += " ORDER BY p.priority DESC, p.created_at"

        return [dict(r) for r in db.execute(query, params).fetchall()]

    def get_pack_tasks(self, user_id, filters=None):
        """Get pack tasks with filters."""
        db = self.get_db()
        filters = filters or {}
        wh_filter = get_warehouse_filter(user_id, get_db=self.get_db)

        query = '''
            SELECT p.*, o.order_number, o.customer_name,
                   u.username as packer_name
            FROM wms_pack_tasks p
            JOIN wms_outbound_orders o ON o.id = p.order_id
            LEFT JOIN users u ON u.id = p.assigned_to
            WHERE 1=1
        '''
        params = []
        if filters.get('status'):
            query += " AND p.status = ?"
            params.append(filters['status'])

        query += wh_filter.replace('warehouse_id', 'o.warehouse_id')
        query += " ORDER BY p.priority DESC, p.created_at"

        return [dict(r) for r in db.execute(query, params).fetchall()]

    def complete_pick(self, user_id, task_id, picked_quantity):
        """Mark a pick task as completed with actual picked quantity."""
        db = self.get_db()
        now = datetime.now().isoformat()

        task = db.execute('SELECT * FROM wms_pick_tasks WHERE id = ?', (task_id,)).fetchone()
        if not task:
            raise ValueError('Pick task not found.')

        # Update task
        db.execute('''
            UPDATE wms_pick_tasks
            SET status = 'COMPLETED', picked_quantity = ?,
                completed_at = ?, completed_by = ?, updated_at = ?
            WHERE id = ?
        ''', (picked_quantity, now, user_id, now, task_id))

        # Deduct from inventory
        db.execute('''
            UPDATE wms_inventory_balances
            SET quantity = quantity - ?, updated_at = ?
            WHERE item_id = ? AND location_id = ? AND status = 'AVAILABLE'
        ''', (picked_quantity, now, task['item_id'], task['source_location_id']))

        # Record ledger
        db.execute('''
            INSERT INTO wms_inventory_ledger
            (item_id, warehouse_id, location_id, transaction_type,
             quantity_moved, user_id, created_at)
            VALUES (?, ?, ?, 'PICK', ?, ?, ?)
        ''', (task['item_id'], task.get('warehouse_id', 0),
              task['source_location_id'],
              -picked_quantity, user_id, now))

        db.commit()
        log_wms_audit('PICK_COMPLETE', 'pick_task', task_id,
                      {'qty': picked_quantity}, user_id, get_db=self.get_db)

    # ------------------------------------------------------------------
    # Wave Management
    # ------------------------------------------------------------------

    def get_waves(self, user_id, filters=None):
        """Get wave picking sessions."""
        db = self.get_db()
        filters = filters or {}
        wh_filter = get_warehouse_filter(user_id, get_db=self.get_db)

        query = '''
            SELECT wv.*, w.name as warehouse_name,
                   u.username as created_by_name,
                   COUNT(DISTINCT wvo.order_id) as order_count
            FROM wms_waves wv
            JOIN wms_warehouses w ON w.id = wv.warehouse_id
            LEFT JOIN users u ON u.id = wv.created_by
            LEFT JOIN wms_wave_orders wvo ON wvo.wave_id = wv.id
            WHERE 1=1
        '''
        params = []
        if filters.get('status'):
            query += " AND wv.status = ?"
            params.append(filters['status'])

        query += wh_filter.replace('warehouse_id', 'wv.warehouse_id')
        query += " GROUP BY wv.id ORDER BY wv.created_at DESC"

        return [dict(r) for r in db.execute(query, params).fetchall()]
