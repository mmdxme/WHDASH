"""
Logistics Dispatch Service
==========================
Business logic for live dispatch board operations and assignments
— extracted from logistics_routes.py.
"""

from datetime import datetime

class LogisticsDispatchService:
    """Handles real-time dispatching and assignments."""

    def __init__(self, get_db):
        self.get_db = get_db

    def get_dispatch_board_data(self, filters=None):
        """Aggregate all data needed for the live dispatch board."""
        db = self.get_db()
        filters = filters or {}
        date_filter = filters.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Unassigned Loads
        unassigned_loads = [dict(r) for r in db.execute("""
            SELECT s.*, c.name as customer_name
            FROM logistics_shipments s
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            WHERE s.status IN ('ready_dispatch', 'scheduled')
            AND s.driver_id IS NULL AND s.vehicle_id IS NULL
            ORDER BY s.priority DESC, s.planned_date ASC
        """).fetchall()]

        # Available Drivers
        available_drivers = [dict(r) for r in db.execute("""
            SELECT d.*, v.plate_number, v.vehicle_type
            FROM logistics_drivers d
            LEFT JOIN logistics_vehicles v ON d.assigned_vehicle_id = v.id
            WHERE d.status = 'active' AND d.availability = 'available'
        """).fetchall()]

        # Available Vehicles
        available_vehicles = [dict(r) for r in db.execute("""
            SELECT v.*, d.full_name as driver_name
            FROM logistics_vehicles v
            LEFT JOIN logistics_drivers d ON v.assigned_driver_id = d.id
            WHERE v.status = 'active' AND v.availability = 'available'
        """).fetchall()]

        # Active Dispatches (today)
        active_dispatches = [dict(r) for r in db.execute("""
            SELECT s.*, d.full_name as driver_name, v.plate_number
            FROM logistics_shipments s
            LEFT JOIN logistics_drivers d ON s.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            WHERE date(s.dispatch_date) = ? OR s.status IN ('assigned', 'loaded', 'departed', 'in_transit')
        """, (date_filter,)).fetchall()]

        return {
            'unassigned_loads': unassigned_loads,
            'available_drivers': available_drivers,
            'available_vehicles': available_vehicles,
            'active_dispatches': active_dispatches
        }

    def assign_trip(self, shipment_id, driver_id, vehicle_id, user_id=None):
        """Assign driver and vehicle to a shipment."""
        db = self.get_db()
        
        db.execute("""
            UPDATE logistics_shipments
            SET driver_id = ?, vehicle_id = ?,
                status = CASE WHEN status = 'ready_dispatch' THEN 'assigned' ELSE status END,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (driver_id, vehicle_id, shipment_id))

        if driver_id:
            db.execute("UPDATE logistics_drivers SET availability = 'on_trip' WHERE id = ?", (driver_id,))
        if vehicle_id:
            db.execute("UPDATE logistics_vehicles SET availability = 'on_trip' WHERE id = ?", (vehicle_id,))

        db.commit()
        return True
