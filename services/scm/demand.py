"""SCM Demand Service - Forecasting and demand analysis."""
from services.base import BaseService


class DemandService(BaseService):
    """Service for demand forecasting and analysis."""

    def get_demand_forecast(self, item_id=None, warehouse_id=None, periods=12):
        """Get demand forecast data."""
        db = self.get_db()
        query = '''
            SELECT * FROM scm_demand_forecasts
            WHERE 1=1
        '''
        params = []
        if item_id:
            query += " AND item_id = ?"
            params.append(item_id)
        if warehouse_id:
            query += " AND warehouse_id = ?"
            params.append(warehouse_id)
        query += " ORDER BY period_start LIMIT ?"
        params.append(periods)
        return db.execute(query, params).fetchall()

    def calculate_safety_stock(self, item_id, warehouse_id=None):
        """Calculate safety stock for an item."""
        db = self.get_db()
        query = '''
            SELECT * FROM scm_demand_history
            WHERE item_id = ?
        '''
        params = [item_id]
        if warehouse_id:
            query += " AND warehouse_id = ?"
            params.append(warehouse_id)
        query += " ORDER BY period_start DESC LIMIT 30"

        history = db.execute(query, params).fetchall()
        if not history:
            return 0

        import statistics
        demands = [h['quantity'] for h in history]
        avg_demand = statistics.mean(demands)
        stdev_demand = statistics.stdev(demands) if len(demands) > 1 else 0
        safety_stock = avg_demand + (2 * stdev_demand)
        return round(safety_stock, 2)

    def get_demand_history(self, item_id=None, warehouse_id=None, limit=30):
        """Get historical demand data."""
        db = self.get_db()
        query = '''
            SELECT dh.*, i.item_code, i.name as item_name
            FROM scm_demand_history dh
            JOIN wms_items i ON i.id = dh.item_id
            WHERE 1=1
        '''
        params = []
        if item_id:
            query += " AND dh.item_id = ?"
            params.append(item_id)
        if warehouse_id:
            query += " AND dh.warehouse_id = ?"
            params.append(warehouse_id)
        query += " ORDER BY dh.period_start DESC LIMIT ?"
        params.append(limit)
        return db.execute(query, params).fetchall()