"""SCM Supply Service - Supply planning and reorder points."""
from services.base import BaseService


class SupplyService(BaseService):
    """Service for supply planning operations."""

    def get_supply_plan(self, item_id=None, warehouse_id=None):
        """Get supply plan for items."""
        db = self.get_db()
        query = '''
            SELECT sp.*, i.item_code, i.name as item_name, w.name as warehouse_name
            FROM scm_supply_plan sp
            JOIN wms_items i ON i.id = sp.item_id
            JOIN wms_warehouses w ON w.id = sp.warehouse_id
            WHERE 1=1
        '''
        params = []
        if item_id:
            query += " AND sp.item_id = ?"
            params.append(item_id)
        if warehouse_id:
            query += " AND sp.warehouse_id = ?"
            params.append(warehouse_id)
        query += " ORDER BY sp.due_date"
        return db.execute(query, params).fetchall()

    def calculate_reorder_point(self, item_id, warehouse_id=None):
        """Calculate reorder point (ROP) = (demand rate * lead time) + safety stock."""
        db = self.get_db()

        item = db.execute('SELECT reorder_point, safety_stock FROM wms_items WHERE id = ?', (item_id,)).fetchone()
        if not item:
            return 0

        lead_time = db.execute('''
            SELECT AVG(lead_time_days) as avg_lead_time
            FROM scm_supply_orders
            WHERE item_id = ? AND status = 'RECEIVED'
        ''', (item_id,)).fetchone()

        lead_time_days = lead_time['avg_lead_time'] if lead_time else 7

        demand = db.execute('''
            SELECT AVG(daily_demand) as avg_demand
            FROM scm_demand_history
            WHERE item_id = ?
        ''', (item_id,)).fetchone()

        avg_demand = demand['avg_demand'] if demand else 0
        safety_stock = item['safety_stock'] or 0

        rop = (avg_demand * lead_time_days) + safety_stock
        return round(rop, 2)