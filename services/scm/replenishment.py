"""SCM Replenishment Service - Order suggestions and EOQ."""
from services.base import BaseService


class ReplenishmentService(BaseService):
    """Service for replenishment calculations and suggestions."""

    def get_replenishment_suggestions(self, warehouse_id=None):
        """Get replenishment suggestions based on min/max or ROP."""
        db = self.get_db()
        query = '''
            SELECT c.*, i.item_code, i.name as item_name,
                   COALESCE((SELECT SUM(quantity) FROM wms_inventory_balances b
                             WHERE b.item_id = c.item_id AND b.warehouse_id = c.warehouse_id), 0) as current_stock
            FROM wms_replenishment_config c
            JOIN wms_items i ON i.id = c.item_id
            WHERE c.is_active = 1
        '''
        params = []
        if warehouse_id:
            query += " AND c.warehouse_id = ?"
            params.append(warehouse_id)
        return db.execute(query, params).fetchall()

    def calculate_economic_order_quantity(self, item_id, annual_demand=None):
        """Calculate EOQ = sqrt(2 * annual_demand * ordering_cost / holding_cost)."""
        db = self.get_db()

        if annual_demand is None:
            hist = db.execute('''
                SELECT SUM(quantity) as total FROM scm_demand_history WHERE item_id = ?
            ''', (item_id,)).fetchone()
            annual_demand = hist['total'] if hist else 1000

        ordering_cost = db.execute('''
            SELECT AVG(ordering_cost) as cost FROM scm_supply_orders WHERE item_id = ?
        ''', (item_id,)).fetchone()
        ordering_cost = ordering_cost['cost'] if ordering_cost else 50

        holding_cost_pct = db.execute('''
            SELECT holding_cost_pct FROM wms_items WHERE id = ?
        ''', (item_id,)).fetchone()
        holding_cost_pct = holding_cost_pct['holding_cost_pct'] if holding_cost_pct else 0.25

        item_value = db.execute('''
            SELECT unit_cost FROM wms_items WHERE id = ?
        ''', (item_id,)).fetchone()
        item_value = item_value['unit_cost'] if item_value else 100

        holding_cost = item_value * holding_cost_pct
        eoq = ((2 * annual_demand * ordering_cost) / holding_cost) ** 0.5 if holding_cost > 0 else 0
        return round(eoq, 2)