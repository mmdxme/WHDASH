"""
Logistics Trip Service
======================
Business logic for trip planning, scheduling, and shipment management
— extracted from logistics_routes.py.
"""

from datetime import datetime

class LogisticsTripService:
    """Handles trip and shipment planning."""

    def __init__(self, get_db):
        self.get_db = get_db

    def get_shipments(self, filters=None):
        """Get shipments with related info."""
        db = self.get_db()
        filters = filters or {}
        
        query = """
            SELECT s.*, c.name as customer_name,
                   d.full_name as driver_name, v.plate_number
            FROM logistics_shipments s
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            LEFT JOIN logistics_drivers d ON s.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            WHERE 1=1
        """
        params = []
        if filters.get('status'):
            query += " AND s.status = ?"
            params.append(filters['status'])
        if filters.get('date_from') and filters.get('date_to'):
            query += " AND date(s.created_at) BETWEEN ? AND ?"
            params.extend([filters['date_from'], filters['date_to']])
            
        query += " ORDER BY s.created_at DESC"
        return [dict(r) for r in db.execute(query, params).fetchall()]

    def get_trip_detail(self, shipment_id):
        """Get shipment details with lines and incidents."""
        db = self.get_db()
        shipment = db.execute("""
            SELECT s.*, c.name as customer_name,
                   d.full_name as driver_name, v.plate_number,
                   v.vehicle_type, b.name as branch_name
            FROM logistics_shipments s
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            LEFT JOIN logistics_drivers d ON s.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            LEFT JOIN branches b ON s.branch_id = b.id
            WHERE s.id = ?
        """, (shipment_id,)).fetchone()
        
        if not shipment:
            return None
            
        result = dict(shipment)
        result['lines'] = [dict(r) for r in db.execute("""
            SELECT * FROM logistics_shipment_lines WHERE shipment_id = ?
        """, (shipment_id,)).fetchall()]
        
        result['incidents'] = [dict(r) for r in db.execute("""
            SELECT * FROM logistics_incidents WHERE shipment_id = ?
        """, (shipment_id,)).fetchall()]
        
        return result
