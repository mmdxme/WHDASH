"""WMS Transfer Service - Atomic transfer operations with transaction safety."""
from services.base import BaseService


class TransferService(BaseService):
    """Service for transfer operations with transaction support."""

    def create_transfer(self, data, user_id=None):
        """Create a new transfer header."""
        db = self.get_db()
        transfer_number = self._generate_transfer_number()

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
            user_id,
            user_id
        ))
        db.commit()
        transfer_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        return transfer_id, transfer_number

    def execute_transfer(self, transfer_id, user_id=None):
        """Execute a transfer: deduct from source, add to destination (atomic)."""
        with self.get_db_context() as ctx:
            transfer = ctx.execute(
                'SELECT * FROM wms_transfers WHERE id = ? AND status = ?',
                (transfer_id, 'APPROVED')
            ).fetchone()

            if not transfer:
                raise ValueError('Transfer not found or not approved.')

            lines = ctx.execute(
                'SELECT * FROM wms_transfer_lines WHERE transfer_id = ?',
                (transfer_id,)
            ).fetchall()

            if not lines:
                raise ValueError('No line items in transfer.')

            for line in lines:
                source_balance = ctx.execute('''
                    SELECT * FROM wms_inventory_balances
                    WHERE item_id = ? AND warehouse_id = ? AND location_id = ?
                ''', (line['item_id'], transfer['source_warehouse_id'], line['source_location_id'])).fetchone()

                if not source_balance or source_balance['quantity'] < line['quantity']:
                    raise ValueError(f'Insufficient stock for item {line["item_id"]} at source location.')

                ctx.execute('''
                    UPDATE wms_inventory_balances
                    SET quantity = quantity - ?
                    WHERE item_id = ? AND warehouse_id = ? AND location_id = ?
                ''', (line['quantity'], line['item_id'], transfer['source_warehouse_id'], line['source_location_id']))

                dest_balance = ctx.execute('''
                    SELECT * FROM wms_inventory_balances
                    WHERE item_id = ? AND warehouse_id = ? AND location_id = ?
                ''', (line['item_id'], transfer['destination_warehouse_id'], line['destination_location_id'])).fetchone()

                if dest_balance:
                    ctx.execute('''
                        UPDATE wms_inventory_balances
                        SET quantity = quantity + ?
                        WHERE item_id = ? AND warehouse_id = ? AND location_id = ?
                    ''', (line['quantity'], line['item_id'], transfer['destination_warehouse_id'], line['destination_location_id']))
                else:
                    ctx.execute('''
                        INSERT INTO wms_inventory_balances
                        (item_id, warehouse_id, location_id, quantity, reserved_quantity, allocated_quantity, status)
                        VALUES (?, ?, ?, ?, 0, 0, 'AVAILABLE')
                    ''', (line['item_id'], transfer['destination_warehouse_id'], line['destination_location_id'], line['quantity']))

            ctx.execute('''
                UPDATE wms_transfers
                SET status = 'COMPLETED', completed_at = CURRENT_TIMESTAMP, completed_by = ?
                WHERE id = ?
            ''', (user_id, transfer_id))
            ctx.commit()

    def search_transfers(self, status='', transfer_type='', page=1, per_page=50):
        """Search transfers with filters."""
        db = self.get_db()
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

        return {
            'transfers': transfers,
            'total': total,
            'page': page,
            'per_page': per_page,
            'total_pages': (total + per_page - 1) // per_page if total > 0 else 1
        }

    def get_transfer_by_id(self, transfer_id):
        """Get transfer with detail."""
        db = self.get_db()
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
        return transfer

    def get_transfer_lines(self, transfer_id):
        """Get transfer line items."""
        db = self.get_db()
        return db.execute('''
            SELECT tl.*, i.item_code, i.name as item_name,
                   sl.code as source_location, dl.code as dest_location
            FROM wms_transfer_lines tl
            JOIN wms_items i ON i.id = tl.item_id
            LEFT JOIN wms_locations sl ON sl.id = tl.source_location_id
            LEFT JOIN wms_locations dl ON dl.id = tl.destination_location_id
            WHERE tl.transfer_id = ?
        ''', (transfer_id,)).fetchall()

    def add_transfer_line(self, transfer_id, item_id, quantity, source_location_id=None,
                          destination_location_id=None, notes=None):
        """Add a line to a transfer."""
        db = self.get_db()
        db.execute('''
            INSERT INTO wms_transfer_lines
            (transfer_id, item_id, quantity, source_location_id, destination_location_id, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (transfer_id, item_id, quantity, source_location_id, destination_location_id, notes))
        db.commit()

    def validate_inventory_available(self, item_id, warehouse_id, location_id, required_qty):
        """Check if required quantity is available at location."""
        db = self.get_db()
        balance = db.execute('''
            SELECT quantity FROM wms_inventory_balances
            WHERE item_id = ? AND warehouse_id = ? AND location_id = ?
        ''', (item_id, warehouse_id, location_id)).fetchone()

        if not balance or balance['quantity'] < required_qty:
            return False
        return True

    def _generate_transfer_number(self):
        """Generate unique transfer number."""
        import random
        from datetime import datetime
        year = datetime.now().year
        random_part = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        return f'TRF-{year}-{random_part}'