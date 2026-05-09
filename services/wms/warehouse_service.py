"""
WMS Warehouse Service
=====================
Business logic for warehouse, zone, and location management
— extracted from wms_routes.py.
"""

from datetime import datetime
from services.wms.helpers import (
    log_wms_audit, ensure_warehouse_allowed, get_warehouse_filter,
    validate_location_code
)


class WMSWarehouseService:
    """Handles all warehouse/zone/location business logic."""

    def __init__(self, get_db):
        self.get_db = get_db

    def get_warehouses(self, user_id, filters=None):
        """Get list of warehouses the user can access."""
        db = self.get_db()
        wh_filter = get_warehouse_filter(user_id, get_db=self.get_db)

        query = f'''
            SELECT w.*,
                COUNT(DISTINCT l.id) as location_count,
                COALESCE(SUM(b.quantity), 0) as total_stock
            FROM wms_warehouses w
            LEFT JOIN wms_locations l ON l.warehouse_id = w.id
            LEFT JOIN wms_inventory_balances b ON b.warehouse_id = w.id
            WHERE w.is_active = 1 {wh_filter}
            GROUP BY w.id ORDER BY w.name
        '''
        return [dict(r) for r in db.execute(query).fetchall()]

    def get_warehouse_detail(self, warehouse_id, user_id):
        """Get full warehouse details with zones, locations, stock."""
        db = self.get_db()
        if not ensure_warehouse_allowed(warehouse_id, user_id, get_db=self.get_db):
            raise PermissionError('No access to this warehouse.')

        wh = db.execute(
            'SELECT * FROM wms_warehouses WHERE id = ?', (warehouse_id,)
        ).fetchone()
        if not wh:
            return None

        result = dict(wh)

        result['zones'] = [dict(r) for r in db.execute('''
            SELECT * FROM wms_zones WHERE warehouse_id = ?
            ORDER BY name
        ''', (warehouse_id,)).fetchall()]

        result['location_summary'] = dict(db.execute('''
            SELECT COUNT(*) as total,
                SUM(CASE WHEN is_empty = 1 THEN 1 ELSE 0 END) as empty,
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active
            FROM wms_locations WHERE warehouse_id = ?
        ''', (warehouse_id,)).fetchone())

        result['stock_summary'] = [dict(r) for r in db.execute('''
            SELECT status, SUM(quantity) as total_qty, COUNT(*) as lines
            FROM wms_inventory_balances WHERE warehouse_id = ?
            GROUP BY status
        ''', (warehouse_id,)).fetchall()]

        return result

    def create_warehouse(self, user_id, data):
        """Create a new warehouse."""
        db = self.get_db()
        now = datetime.now().isoformat()

        name = (data.get('name') or '').strip()
        code = (data.get('code') or '').strip()
        if not name:
            raise ValueError('Warehouse name is required.')
        if not code:
            raise ValueError('Warehouse code is required.')

        db.execute('''
            INSERT INTO wms_warehouses
            (code, name, warehouse_type, address, city, country,
             company_id, capacity_sqm, capacity_pallets,
             is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        ''', (code, name, data.get('warehouse_type', 'STANDARD'),
              data.get('address'), data.get('city'), data.get('country'),
              data.get('company_id'), data.get('capacity_sqm'),
              data.get('capacity_pallets'), now, now))
        wh_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        db.commit()

        log_wms_audit('CREATE', 'warehouse', wh_id,
                      {'name': name, 'code': code},
                      user_id, get_db=self.get_db)
        return wh_id

    # ------------------------------------------------------------------
    # Locations
    # ------------------------------------------------------------------

    def get_locations(self, warehouse_id, user_id, filters=None):
        """Get locations for a warehouse."""
        db = self.get_db()
        filters = filters or {}

        if not ensure_warehouse_allowed(warehouse_id, user_id, get_db=self.get_db):
            raise PermissionError('No access to this warehouse.')

        query = '''
            SELECT l.*, z.name as zone_name
            FROM wms_locations l
            LEFT JOIN wms_zones z ON z.id = l.zone_id
            WHERE l.warehouse_id = ?
        '''
        params = [warehouse_id]

        if filters.get('zone_id'):
            query += " AND l.zone_id = ?"
            params.append(filters['zone_id'])
        if filters.get('is_empty') is not None:
            query += " AND l.is_empty = ?"
            params.append(1 if filters['is_empty'] else 0)

        query += " ORDER BY l.code"
        return [dict(r) for r in db.execute(query, params).fetchall()]

    def create_location(self, user_id, warehouse_id, data):
        """Create a new location in a warehouse."""
        db = self.get_db()
        now = datetime.now().isoformat()

        code = (data.get('code') or '').strip()
        valid, result = validate_location_code(code, warehouse_id)
        if not valid:
            raise ValueError(result)

        db.execute('''
            INSERT INTO wms_locations
            (warehouse_id, zone_id, code, name, location_type,
             capacity_volume_m3, capacity_weight_kg,
             is_empty, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?)
        ''', (warehouse_id, data.get('zone_id'), result,
              data.get('name', result), data.get('location_type', 'RACK'),
              data.get('capacity_volume_m3'), data.get('capacity_weight_kg'),
              now, now))
        loc_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]
        db.commit()

        log_wms_audit('CREATE', 'location', loc_id,
                      {'code': result, 'warehouse_id': warehouse_id},
                      user_id, get_db=self.get_db)
        return loc_id
