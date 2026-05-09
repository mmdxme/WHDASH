"""
Logistics Cost Service
======================
Business logic for logistics cost management, fuel, and maintenance expenses
— extracted from logistics_routes.py section 11.
"""

from datetime import datetime

class LogisticsCostService:
    """Handles cost-related operations."""

    def __init__(self, get_db):
        self.get_db = get_db

    def get_costs(self, filters=None):
        """Get cost entries with filters."""
        db = self.get_db()
        filters = filters or {}
        
        query = """
            SELECT ce.*, s.shipment_code, v.plate_number
            FROM logistics_cost_entries ce
            LEFT JOIN logistics_shipments s ON ce.shipment_id = s.id
            LEFT JOIN logistics_vehicles v ON ce.vehicle_id = v.id
            WHERE 1=1
        """
        params = []
        if filters.get('cost_type'):
            query += " AND ce.cost_type = ?"
            params.append(filters['cost_type'])
        if filters.get('date_from') and filters.get('date_to'):
            query += " AND date(ce.created_at) BETWEEN ? AND ?"
            params.extend([filters['date_from'], filters['date_to']])
            
        query += " ORDER BY ce.created_at DESC"
        return [dict(r) for r in db.execute(query, params).fetchall()]

    def add_cost_entry(self, data, user_id=None):
        """Add a new cost entry."""
        db = self.get_db()
        
        db.execute("""
            INSERT INTO logistics_cost_entries
            (shipment_id, vehicle_id, driver_id, cost_type, amount, currency,
             description, reference_number, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
        """, (
            data.get('shipment_id'), data.get('vehicle_id'),
            data.get('driver_id'), data.get('cost_type'),
            data.get('amount'), data.get('currency', 'AED'),
            data.get('description'), data.get('reference_number')
        ))
        
        db.commit()
        return True
