"""
WMS Quality Service
===================
Business logic for quality holds, inspections
— extracted from wms_routes.py.
"""

from datetime import datetime
from services.wms.helpers import (
    get_warehouse_filter, log_wms_audit, generate_wms_code,
    create_wms_notification
)


class WMSQualityService:
    """Handles all quality hold and inspection business logic."""

    def __init__(self, get_db):
        self.get_db = get_db

    def get_quality_holds(self, user_id, filters=None):
        """Get quality holds with filters."""
        db = self.get_db()
        filters = filters or {}
        wh_filter = get_warehouse_filter(user_id, get_db=self.get_db)

        query = '''
            SELECT qh.*, i.item_code, i.name as item_name,
                   w.name as warehouse_name,
                   l.code as location_code,
                   lt.lot_number,
                   u.username as held_by_name
            FROM wms_quality_holds qh
            JOIN wms_items i ON i.id = qh.item_id
            JOIN wms_warehouses w ON w.id = qh.warehouse_id
            LEFT JOIN wms_locations l ON l.id = qh.location_id
            LEFT JOIN wms_lots lt ON lt.id = qh.lot_id
            LEFT JOIN users u ON u.id = qh.held_by
            WHERE 1=1
        '''
        params = []
        if filters.get('status'):
            query += " AND qh.status = ?"
            params.append(filters['status'])
        if filters.get('warehouse_id'):
            query += " AND qh.warehouse_id = ?"
            params.append(filters['warehouse_id'])

        query += wh_filter.replace('warehouse_id', 'qh.warehouse_id')
        query += " ORDER BY qh.created_at DESC"

        return [dict(r) for r in db.execute(query, params).fetchall()]

    def get_hold_stats(self, user_id):
        """Get summary statistics for quality holds dashboard."""
        db = self.get_db()
        wh_filter = get_warehouse_filter(user_id, get_db=self.get_db)

        stats = {}
        stats['total_active'] = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_quality_holds
            WHERE status = 'ACTIVE' {wh_filter.replace('warehouse_id', 'warehouse_id')}
        ''').fetchone()['cnt']

        stats['total_held_qty'] = db.execute(f'''
            SELECT COALESCE(SUM(quantity_held), 0) as qty FROM wms_quality_holds
            WHERE status = 'ACTIVE' {wh_filter.replace('warehouse_id', 'warehouse_id')}
        ''').fetchone()['qty']

        stats['by_type'] = [dict(r) for r in db.execute(f'''
            SELECT hold_type, COUNT(*) as cnt, SUM(quantity_held) as qty
            FROM wms_quality_holds
            WHERE status = 'ACTIVE' {wh_filter.replace('warehouse_id', 'warehouse_id')}
            GROUP BY hold_type
        ''').fetchall()]

        stats['overdue'] = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_quality_holds
            WHERE status = 'ACTIVE'
              AND expected_clear_date IS NOT NULL
              AND expected_clear_date < date('now')
            {wh_filter.replace('warehouse_id', 'warehouse_id')}
        ''').fetchone()['cnt']

        return stats

    def create_hold(self, user_id, data):
        """Create a quality hold on inventory."""
        db = self.get_db()
        now = datetime.now().isoformat()
        hold_number = generate_wms_code('INSPECT', get_db=self.get_db)

        db.execute('''
            INSERT INTO wms_quality_holds
            (hold_number, warehouse_id, item_id, lot_id,
             location_id, quantity_held, hold_reason, hold_type,
             status, hold_notes, held_by, held_at,
             expected_clear_date, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?, ?, ?, ?)
        ''', (hold_number, data['warehouse_id'], data['item_id'],
              data.get('lot_id'), data.get('location_id'),
              float(data.get('quantity_held', 0)),
              data['hold_reason'], data.get('hold_type', 'INSPECTION'),
              data.get('hold_notes'), user_id, now,
              data.get('expected_clear_date'), now, now))

        hold_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Block inventory
        if data.get('location_id'):
            db.execute('''
                UPDATE wms_inventory_balances
                SET blocked_quantity = blocked_quantity + ?,
                    quantity = quantity - ?, updated_at = ?
                WHERE item_id = ? AND location_id = ? AND status = 'AVAILABLE'
            ''', (float(data.get('quantity_held', 0)),
                  float(data.get('quantity_held', 0)), now,
                  data['item_id'], data['location_id']))

        db.commit()

        log_wms_audit('CREATE', 'quality_hold', hold_id,
                      {'number': hold_number, 'reason': data['hold_reason']},
                      user_id, get_db=self.get_db)
        return hold_id, hold_number

    def release_hold(self, user_id, hold_id, release_reason):
        """Release a quality hold, returning stock to available."""
        db = self.get_db()
        now = datetime.now().isoformat()

        hold = db.execute(
            'SELECT * FROM wms_quality_holds WHERE id = ?', (hold_id,)
        ).fetchone()
        if not hold:
            raise ValueError('Quality hold not found.')
        if hold['status'] != 'ACTIVE':
            raise ValueError('Hold is not active.')

        db.execute('''
            UPDATE wms_quality_holds
            SET status = 'RELEASED', released_by = ?, released_at = ?,
                release_reason = ?, updated_at = ?
            WHERE id = ?
        ''', (user_id, now, release_reason, now, hold_id))

        # Unblock inventory
        if hold['location_id']:
            db.execute('''
                UPDATE wms_inventory_balances
                SET blocked_quantity = MAX(0, blocked_quantity - ?),
                    quantity = quantity + ?, updated_at = ?
                WHERE item_id = ? AND location_id = ?
            ''', (hold['quantity_held'], hold['quantity_held'], now,
                  hold['item_id'], hold['location_id']))

        db.commit()

        log_wms_audit('RELEASE', 'quality_hold', hold_id,
                      {'reason': release_reason},
                      user_id, get_db=self.get_db)
