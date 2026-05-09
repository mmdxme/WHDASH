"""
WMS Transfer Service
====================
Business logic for inter-warehouse and inter-company stock transfers
— extracted from wms_routes.py.
"""

from datetime import datetime
from services.wms.helpers import (
    get_warehouse_filter, log_wms_audit, generate_wms_code,
    create_wms_notification, ensure_warehouse_allowed
)


class WMSTransferService:
    """Handles all transfer business logic."""

    def __init__(self, get_db):
        self.get_db = get_db

    def get_transfers(self, user_id, filters=None):
        """Get transfers with filters."""
        db = self.get_db()
        filters = filters or {}
        wh_filter = get_warehouse_filter(user_id, get_db=self.get_db)

        query = '''
            SELECT t.*,
                   sw.name as source_warehouse_name,
                   dw.name as dest_warehouse_name,
                   u.username as requested_by_name
            FROM wms_transfers t
            JOIN wms_warehouses sw ON sw.id = t.source_warehouse_id
            JOIN wms_warehouses dw ON dw.id = t.destination_warehouse_id
            LEFT JOIN users u ON u.id = t.requested_by
            WHERE 1=1
        '''
        params = []
        if filters.get('status'):
            query += " AND t.status = ?"
            params.append(filters['status'])

        query += wh_filter.replace('warehouse_id', 't.source_warehouse_id')
        query += " ORDER BY t.created_at DESC"

        return [dict(r) for r in db.execute(query, params).fetchall()]

    def create_transfer(self, user_id, data):
        """Create a new transfer request."""
        db = self.get_db()
        now = datetime.now().isoformat()
        transfer_number = generate_wms_code('TRANSFER', get_db=self.get_db)

        # Validate warehouses
        src = data['source_warehouse_id']
        dst = data['destination_warehouse_id']
        if not ensure_warehouse_allowed(src, user_id, get_db=self.get_db):
            raise PermissionError('No access to source warehouse.')
        if not ensure_warehouse_allowed(dst, user_id, get_db=self.get_db):
            raise PermissionError('No access to destination warehouse.')
        if str(src) == str(dst):
            raise ValueError('Source and destination warehouses must differ.')

        db.execute('''
            INSERT INTO wms_transfers
            (transfer_number, source_warehouse_id, destination_warehouse_id,
             transfer_type, status, notes, requested_by, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'REQUESTED', ?, ?, ?, ?)
        ''', (transfer_number, src, dst,
              data.get('transfer_type', 'INTER_WAREHOUSE'),
              data.get('notes', ''), user_id, now, now))
        transfer_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        db.commit()

        log_wms_audit('CREATE', 'transfer', transfer_id,
                      {'number': transfer_number, 'src': src, 'dst': dst},
                      user_id, get_db=self.get_db)
        return transfer_id, transfer_number

    def approve_transfer(self, user_id, transfer_id):
        """Approve a pending transfer request."""
        db = self.get_db()
        now = datetime.now().isoformat()
        transfer = db.execute(
            'SELECT * FROM wms_transfers WHERE id = ?', (transfer_id,)
        ).fetchone()
        if not transfer:
            raise ValueError('Transfer not found.')
        if transfer['status'] != 'REQUESTED':
            raise ValueError('Transfer is not in REQUESTED status.')

        db.execute('''
            UPDATE wms_transfers
            SET status = 'APPROVED', approved_by = ?, approved_at = ?, updated_at = ?
            WHERE id = ?
        ''', (user_id, now, now, transfer_id))
        db.commit()

        log_wms_audit('APPROVE', 'transfer', transfer_id,
                      {'number': transfer['transfer_number']},
                      user_id, get_db=self.get_db)

    def get_returns(self, user_id, filters=None):
        """Get return requests with filters."""
        db = self.get_db()
        filters = filters or {}
        wh_filter = get_warehouse_filter(user_id, get_db=self.get_db)

        query = '''
            SELECT r.*, w.name as warehouse_name,
                   u.username as requested_by_name
            FROM wms_returns r
            JOIN wms_warehouses w ON w.id = r.warehouse_id
            LEFT JOIN users u ON u.id = r.requested_by
            WHERE 1=1
        '''
        params = []
        if filters.get('status'):
            query += " AND r.status = ?"
            params.append(filters['status'])

        query += wh_filter.replace('warehouse_id', 'r.warehouse_id')
        query += " ORDER BY r.created_at DESC"

        return [dict(r) for r in db.execute(query, params).fetchall()]
