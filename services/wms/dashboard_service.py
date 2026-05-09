"""
WMS Dashboard Service
=====================
Business logic for the WMS Dashboard, extracted from wms_routes.py.
Handles all dashboard statistics, KPIs and summary data aggregation.
"""

from datetime import datetime
from services.wms.helpers import get_warehouse_filter, get_company_filter


class WMSDashboardService:
    """Aggregates all dashboard metrics for the WMS module."""

    def __init__(self, get_db):
        self.get_db = get_db

    def get_dashboard_data(self, user_id):
        """
        Return a complete dictionary of dashboard metrics.

        This replaces the ~250-line wms_dashboard() view function body,
        separating data aggregation from HTTP response rendering.
        """
        db = self.get_db()
        wh_filter = get_warehouse_filter(user_id, get_db=self.get_db)

        data = {}

        # Total active SKUs
        data['total_skus'] = db.execute(
            'SELECT COUNT(*) as cnt FROM wms_items WHERE is_active = 1'
        ).fetchone()['cnt']

        # Stock totals
        data['available_stock'] = db.execute(f'''
            SELECT COALESCE(SUM(quantity), 0) as qty FROM wms_inventory_balances
            WHERE status = 'AVAILABLE' {wh_filter}
        ''').fetchone()['qty']

        data['reserved_stock'] = db.execute(f'''
            SELECT COALESCE(SUM(reserved_quantity), 0) as qty
            FROM wms_inventory_balances WHERE 1=1 {wh_filter}
        ''').fetchone()['qty']

        data['blocked_stock'] = db.execute(f'''
            SELECT COALESCE(SUM(blocked_quantity), 0) as qty
            FROM wms_inventory_balances
            WHERE status IN ('BLOCKED', 'QUARANTINE', 'DAMAGED') {wh_filter}
        ''').fetchone()['qty']

        # Near expiry
        try:
            near_expiry_days = int(db.execute(
                "SELECT setting_value FROM wms_settings "
                "WHERE setting_key = 'near_expiry_days'"
            ).fetchone()['setting_value'] or 30)
        except (ValueError, TypeError):
            near_expiry_days = 30

        data['near_expiry'] = db.execute('''
            SELECT COALESCE(SUM(l.quantity), 0) as qty FROM wms_lots l
            WHERE l.expiry_date IS NOT NULL
              AND l.expiry_date <= date('now', '+' || ? || ' days')
              AND l.expiry_date > date('now') AND l.quantity > 0
        ''', (str(near_expiry_days),)).fetchone()['qty']

        data['expired_stock'] = db.execute('''
            SELECT COALESCE(SUM(l.quantity), 0) as qty FROM wms_lots l
            WHERE l.expiry_date IS NOT NULL
              AND l.expiry_date < date('now') AND l.quantity > 0
        ''').fetchone()['qty']

        # Locations
        data['empty_locations'] = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_locations
            WHERE is_empty = 1 AND is_active = 1 {wh_filter}
        ''').fetchone()['cnt']

        data['total_locations'] = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_locations
            WHERE is_active = 1 {wh_filter}
        ''').fetchone()['cnt']

        # Pending tasks
        data['active_alerts'] = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_alerts
            WHERE is_active = 1 AND is_acknowledged = 0
            {wh_filter}
        ''').fetchone()['cnt']

        data['pending_receiving'] = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_inbound_receipts
            WHERE status IN ('EXPECTED', 'ARRIVED', 'PARTIAL') {wh_filter}
        ''').fetchone()['cnt']

        data['pending_putaway'] = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_putaway_tasks
            WHERE status = 'PENDING'
            {wh_filter.replace('warehouse_id', 'wms_putaway_tasks.warehouse_id')}
        ''').fetchone()['cnt']

        data['pending_picking'] = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_pick_tasks p
            JOIN wms_locations l ON l.id = p.source_location_id
            WHERE p.status IN ('PENDING', 'IN_PROGRESS')
            {wh_filter.replace('warehouse_id', 'l.warehouse_id')}
        ''').fetchone()['cnt']

        data['pending_packing'] = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_pack_tasks p
            JOIN wms_outbound_orders o ON o.id = p.order_id
            WHERE p.status = 'PENDING'
            {wh_filter.replace('warehouse_id', 'o.warehouse_id')}
        ''').fetchone()['cnt']

        data['pending_transfers'] = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_transfers
            WHERE status IN ('REQUESTED','APPROVED','PICKING','DISPATCHED')
            {wh_filter.replace('warehouse_id', 'source_warehouse_id')}
        ''').fetchone()['cnt']

        data['pending_returns'] = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_returns
            WHERE status IN ('REQUESTED','AUTHORIZED','RECEIVED') {wh_filter}
        ''').fetchone()['cnt']

        data['pending_counts'] = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_stock_counts
            WHERE status IN ('DRAFT', 'IN_PROGRESS') {wh_filter}
        ''').fetchone()['cnt']

        data['pending_replenishment'] = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_replenishment_tasks
            WHERE status = 'PENDING'
            {wh_filter.replace('warehouse_id', 'wms_replenishment_tasks.warehouse_id')}
        ''').fetchone()['cnt']

        # Stock anomalies
        data['zero_stock'] = db.execute(f'''
            SELECT COUNT(DISTINCT item_id) as cnt FROM wms_inventory_balances
            WHERE quantity <= 0 {wh_filter}
        ''').fetchone()['cnt']

        data['negative_stock'] = db.execute(f'''
            SELECT COUNT(*) as cnt FROM wms_inventory_balances
            WHERE quantity < 0 {wh_filter}
        ''').fetchone()['cnt']

        data['count_discrepancies'] = db.execute('''
            SELECT COUNT(*) as cnt FROM wms_stock_count_lines
            WHERE variance_quantity != 0 AND status = 'APPROVED'
        ''').fetchone()['cnt']

        # Warehouse utilization
        data['warehouse_stats'] = [dict(r) for r in db.execute(f'''
            SELECT w.id, w.name,
                COUNT(DISTINCT l.id) as total_locations,
                SUM(CASE WHEN l.is_empty = 1 THEN 1 ELSE 0 END) as empty_locations,
                COALESCE(SUM(l.current_volume_m3), 0) as used_volume,
                COALESCE(SUM(l.capacity_volume_m3), 0) as total_capacity
            FROM wms_warehouses w
            LEFT JOIN wms_locations l ON l.warehouse_id = w.id
            WHERE w.is_active = 1 {wh_filter}
            GROUP BY w.id
        ''').fetchall()]

        # Recent movements
        data['recent_movements'] = [dict(r) for r in db.execute(f'''
            SELECT l.id, l.transaction_type, l.transaction_number,
                l.quantity_moved, l.created_at,
                i.item_code, i.name as item_name,
                w.name as warehouse_name, u.username
            FROM wms_inventory_ledger l
            JOIN wms_items i ON i.id = l.item_id
            JOIN wms_warehouses w ON w.id = l.warehouse_id
            LEFT JOIN users u ON u.id = l.user_id
            WHERE 1=1 {wh_filter}
            ORDER BY l.created_at DESC LIMIT 10
        ''').fetchall()]

        # Top alerts
        data['top_alerts'] = [dict(r) for r in db.execute('''
            SELECT * FROM wms_alerts WHERE is_active = 1
            ORDER BY CASE severity
                WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3 ELSE 4 END,
                created_at DESC
            LIMIT 10
        ''').fetchall()]

        # Warehouses summary
        data['warehouses'] = [dict(r) for r in db.execute(f'''
            SELECT w.*,
                COALESCE(SUM(b.quantity), 0) as total_stock,
                COUNT(DISTINCT l.id) as location_count
            FROM wms_warehouses w
            LEFT JOIN wms_inventory_balances b ON b.warehouse_id = w.id
            LEFT JOIN wms_locations l ON l.warehouse_id = w.id
            WHERE w.is_active = 1 {wh_filter}
            GROUP BY w.id
        ''').fetchall()]

        # Stock by status
        data['stock_by_status'] = [dict(r) for r in db.execute(f'''
            SELECT status, SUM(quantity) as total_qty, COUNT(*) as locations
            FROM wms_inventory_balances
            WHERE 1=1 {wh_filter}
            GROUP BY status
        ''').fetchall()]

        return data
