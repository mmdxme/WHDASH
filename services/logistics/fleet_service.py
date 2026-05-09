"""
Logistics Fleet Service
=======================
Business logic for vehicle management, maintenance, and fuel tracking
— extracted from logistics_routes.py.
"""

from datetime import datetime

class LogisticsFleetService:
    """Handles vehicle-related operations."""

    def __init__(self, get_db):
        self.get_db = get_db

    def get_vehicles(self, filters=None):
        """Get vehicles with status and maintenance info."""
        db = self.get_db()
        filters = filters or {}
        
        query = """
            SELECT v.*, d.full_name as driver_name,
                   vm.next_service_date, vm.status as maintenance_status
            FROM logistics_vehicles v
            LEFT JOIN logistics_drivers d ON v.assigned_driver_id = d.id
            LEFT JOIN logistics_vehicle_maintenance vm ON v.id = vm.vehicle_id AND vm.status = 'pending'
            WHERE 1=1
        """
        params = []
        if filters.get('status'):
            query += " AND v.status = ?"
            params.append(filters['status'])
        if filters.get('availability'):
            query += " AND v.availability = ?"
            params.append(filters['availability'])
            
        return [dict(r) for r in db.execute(query, params).fetchall()]

    def get_vehicle_detail(self, vehicle_id):
        """Get full vehicle details including documents and history."""
        db = self.get_db()
        vehicle = db.execute("SELECT * FROM logistics_vehicles WHERE id = ?", (vehicle_id,)).fetchone()
        if not vehicle:
            return None
            
        result = dict(vehicle)
        
        # Documents
        result['documents'] = [dict(r) for r in db.execute("""
            SELECT * FROM logistics_vehicle_documents WHERE vehicle_id = ?
        """, (vehicle_id,)).fetchall()]
        
        # Maintenance history
        result['maintenance'] = [dict(r) for r in db.execute("""
            SELECT * FROM logistics_vehicle_maintenance WHERE vehicle_id = ?
            ORDER BY scheduled_date DESC
        """, (vehicle_id,)).fetchall()]
        
        # Recent trips
        result['recent_trips'] = [dict(r) for r in db.execute("""
            SELECT s.*, d.full_name as driver_name
            FROM logistics_shipments s
            LEFT JOIN logistics_drivers d ON s.driver_id = d.id
            WHERE s.vehicle_id = ?
            ORDER BY s.created_at DESC LIMIT 10
        """, (vehicle_id,)).fetchall()]
        
        return result

    def update_vehicle_status(self, vehicle_id, status, availability=None):
        """Update vehicle status and/or availability."""
        db = self.get_db()
        updates = ["status = ?", "updated_at = CURRENT_TIMESTAMP"]
        params = [status]
        
        if availability:
            updates.append("availability = ?")
            params.append(availability)
            
        params.append(vehicle_id)
        db.execute(f"UPDATE logistics_vehicles SET {', '.join(updates)} WHERE id = ?", params)
        db.commit()
