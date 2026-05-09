"""
WMS Receiving Service
=====================
Business logic for inbound receipts, putaway tasks,
and putaway rules engine — extracted from wms_routes.py.
"""

from datetime import datetime
from services.wms.helpers import (
    get_warehouse_filter, log_wms_audit, generate_wms_code,
    create_wms_notification
)


class WMSReceivingService:
    """Handles all receiving/inbound business logic."""

    def __init__(self, get_db):
        self.get_db = get_db

    def get_receipts(self, user_id, filters=None):
        """Get inbound receipts with filters."""
        db = self.get_db()
        filters = filters or {}
        wh_filter = get_warehouse_filter(user_id, get_db=self.get_db)

        query = '''
            SELECT r.*, w.name as warehouse_name,
                   u.username as received_by_name
            FROM wms_inbound_receipts r
            JOIN wms_warehouses w ON w.id = r.warehouse_id
            LEFT JOIN users u ON u.id = r.received_by
            WHERE 1=1
        '''
        params = []
        if filters.get('status'):
            query += " AND r.status = ?"
            params.append(filters['status'])
        if filters.get('warehouse_id'):
            query += " AND r.warehouse_id = ?"
            params.append(filters['warehouse_id'])
        if filters.get('search'):
            query += " AND (r.receipt_number LIKE ? OR r.po_number LIKE ?)"
            s = f"%{filters['search']}%"
            params.extend([s, s])

        query += wh_filter.replace('warehouse_id', 'r.warehouse_id')
        query += " ORDER BY r.created_at DESC"

        items = db.execute(query, params).fetchall()
        return [dict(r) for r in items]

    def get_receipt_detail(self, receipt_id):
        """Get full receipt with lines."""
        db = self.get_db()
        receipt = db.execute('''
            SELECT r.*, w.name as warehouse_name
            FROM wms_inbound_receipts r
            JOIN wms_warehouses w ON w.id = r.warehouse_id
            WHERE r.id = ?
        ''', (receipt_id,)).fetchone()
        if not receipt:
            return None, None

        lines = db.execute('''
            SELECT rl.*, i.item_code, i.name as item_name, i.uom
            FROM wms_inbound_receipt_lines rl
            JOIN wms_items i ON i.id = rl.item_id
            WHERE rl.receipt_id = ?
            ORDER BY rl.line_number
        ''', (receipt_id,)).fetchall()

        return dict(receipt), [dict(l) for l in lines]

    def receive_line(self, user_id, receipt_id, line_data):
        """Receive a single line item against a receipt."""
        db = self.get_db()
        now = datetime.now().isoformat()

        item_id = line_data['item_id']
        qty = float(line_data['quantity'])
        warehouse_id = line_data['warehouse_id']
        location_id = line_data.get('location_id')
        lot_number = line_data.get('lot_number')

        # Update or create receipt line
        existing = db.execute('''
            SELECT id FROM wms_inbound_receipt_lines
            WHERE receipt_id = ? AND item_id = ?
        ''', (receipt_id, item_id)).fetchone()

        if existing:
            db.execute('''
                UPDATE wms_inbound_receipt_lines
                SET received_quantity = received_quantity + ?,
                    status = 'RECEIVED', updated_at = ?
                WHERE id = ?
            ''', (qty, now, existing['id']))
        else:
            db.execute('''
                INSERT INTO wms_inbound_receipt_lines
                (receipt_id, item_id, expected_quantity, received_quantity,
                 status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'RECEIVED', ?, ?)
            ''', (receipt_id, item_id, qty, qty, now, now))

        # Create or update lot if lot tracking
        lot_id = None
        if lot_number:
            existing_lot = db.execute(
                'SELECT id FROM wms_lots WHERE lot_number = ? AND item_id = ?',
                (lot_number, item_id)
            ).fetchone()
            if existing_lot:
                lot_id = existing_lot['id']
                db.execute('''
                    UPDATE wms_lots SET quantity = quantity + ?, updated_at = ?
                    WHERE id = ?
                ''', (qty, now, lot_id))
            else:
                db.execute('''
                    INSERT INTO wms_lots
                    (lot_number, item_id, warehouse_id, quantity,
                     expiry_date, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (lot_number, item_id, warehouse_id, qty,
                      line_data.get('expiry_date'), now, now))
                lot_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Update inventory balance (upsert)
        existing_bal = db.execute('''
            SELECT id FROM wms_inventory_balances
            WHERE item_id = ? AND warehouse_id = ? AND location_id IS ?
              AND lot_id IS ? AND status = 'AVAILABLE'
        ''', (item_id, warehouse_id, location_id, lot_id)).fetchone()

        if existing_bal:
            db.execute('''
                UPDATE wms_inventory_balances
                SET quantity = quantity + ?, updated_at = ?
                WHERE id = ?
            ''', (qty, now, existing_bal['id']))
        else:
            db.execute('''
                INSERT INTO wms_inventory_balances
                (item_id, warehouse_id, location_id, lot_id,
                 quantity, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, 'AVAILABLE', ?, ?)
            ''', (item_id, warehouse_id, location_id, lot_id, qty, now, now))

        # Record ledger entry
        db.execute('''
            INSERT INTO wms_inventory_ledger
            (item_id, warehouse_id, location_id, lot_id,
             transaction_type, transaction_number, quantity_moved,
             user_id, created_at)
            VALUES (?, ?, ?, ?, 'RECEIPT', ?, ?, ?, ?)
        ''', (item_id, warehouse_id, location_id, lot_id,
              f'RCV-{receipt_id}', qty, user_id, now))

        # Update receipt status
        db.execute('''
            UPDATE wms_inbound_receipts SET status = 'PARTIAL', updated_at = ?
            WHERE id = ? AND status != 'COMPLETED'
        ''', (now, receipt_id))

        db.commit()

        log_wms_audit('RECEIVE', 'receipt_line', receipt_id,
                      {'item_id': item_id, 'qty': qty},
                      user_id, get_db=self.get_db)

    # ------------------------------------------------------------------
    # Putaway
    # ------------------------------------------------------------------

    def get_putaway_tasks(self, user_id, filters=None):
        """Get putaway tasks with filters."""
        db = self.get_db()
        filters = filters or {}
        wh_filter = get_warehouse_filter(user_id, get_db=self.get_db)

        query = '''
            SELECT pt.*, i.item_code, i.name as item_name,
                   w.name as warehouse_name,
                   sl.code as source_location, dl.code as dest_location,
                   u.username as assigned_to_name
            FROM wms_putaway_tasks pt
            JOIN wms_items i ON i.id = pt.item_id
            JOIN wms_warehouses w ON w.id = pt.warehouse_id
            LEFT JOIN wms_locations sl ON sl.id = pt.source_location_id
            LEFT JOIN wms_locations dl ON dl.id = pt.destination_location_id
            LEFT JOIN users u ON u.id = pt.assigned_to
            WHERE 1=1
        '''
        params = []
        if filters.get('status'):
            query += " AND pt.status = ?"
            params.append(filters['status'])

        query += wh_filter.replace('warehouse_id', 'pt.warehouse_id')
        query += " ORDER BY pt.priority DESC, pt.created_at DESC"

        items = db.execute(query, params).fetchall()
        return [dict(r) for r in items]
