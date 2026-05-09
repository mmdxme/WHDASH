"""
Logistics Driver Service
========================
Business logic for driver management, licensing, and document tracking
— extracted from logistics_routes.py.
"""

from datetime import datetime

class LogisticsDriverService:
    """Handles driver-related operations."""

    def __init__(self, get_db):
        self.get_db = get_db

    def get_drivers(self, filters=None):
        """Get drivers with assigned vehicle and warehouse info."""
        db = self.get_db()
        filters = filters or {}
        
        query = """
            SELECT d.*, v.plate_number, v.vehicle_type,
                   w.name as warehouse_name
            FROM logistics_drivers d
            LEFT JOIN logistics_vehicles v ON d.assigned_vehicle_id = v.id
            LEFT JOIN warehouses w ON d.branch_id = w.id
            WHERE 1=1
        """
        params = []
        if filters.get('status'):
            query += " AND d.status = ?"
            params.append(filters['status'])
        if filters.get('availability'):
            query += " AND d.availability = ?"
            params.append(filters['availability'])
            
        return [dict(r) for r in db.execute(query, params).fetchall()]

    def get_driver_detail(self, driver_id):
        """Get full driver profile including documents and trip history."""
        db = self.get_db()
        driver = db.execute("SELECT * FROM logistics_drivers WHERE id = ?", (driver_id,)).fetchone()
        if not driver:
            return None
            
        result = dict(driver)
        
        # Documents
        result['documents'] = [dict(r) for r in db.execute("""
            SELECT * FROM logistics_driver_documents WHERE driver_id = ?
        """, (driver_id,)).fetchall()]
        
        # Trip history
        result['recent_trips'] = [dict(r) for r in db.execute("""
            SELECT s.*, v.plate_number
            FROM logistics_shipments s
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            WHERE s.driver_id = ?
            ORDER BY s.created_at DESC LIMIT 10
        """, (driver_id,)).fetchall()]
        
        return result
