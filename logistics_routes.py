"""
Logistics Management System - Routes and API Endpoints
=====================================================
This file contains all Logistics/TMS-related Flask routes and API endpoints.

Routes are organized by module:
1. Logistics Dashboard
2. Shipments
3. Delivery Orders
4. Pickup Orders
5. Dispatch Planning
6. Trip Planning
7. Route Planning
8. Fleet Management (Vehicles)
9. Driver Management
10. Carrier Management
11. Cost Management
12. Proof of Delivery (POD)
13. Incidents/Exceptions
14. Documents
15. Reports & Analytics
16. Settings
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file, Response
from functools import wraps
from datetime import datetime, timedelta, date
import sqlite3
import json
import csv
import io
import re
from logistics_models import (
    get_db, run_logistics_migrations, get_logistics_setting, update_logistics_setting,
    log_logistics_audit, get_next_shipment_code, get_next_do_number,
    get_next_pickup_number, get_next_incident_number, get_next_trip_code,
    get_next_route_code, get_trip_stats, get_route_stats, get_stop_stats,
    get_shipment_stats, get_driver_availability_stats, get_vehicle_availability_stats,
    get_active_shipments_for_dispatch, get_open_incidents_count, get_pod_pending_count,
    LOGISTICS_TABLES
)
from flow_models import send_channel_message, get_flow_profile

# Import export utilities
from export_utils import (
    send_export_response,
    get_export_columns
)

logistics_bp = Blueprint('logistics', __name__, url_prefix='/logistics')


# =============================================================================
# EXPORT TYPES AND COLUMNS
# =============================================================================

LOGISTICS_EXPORT_TYPES = [
    'csv', 'excel_text', 'excel_general', 'json', 'xml', 'txt',
    'pdf', 'docx', 'html', 'printable', 'barcode', 'api',
    'email', 'zip', 'backup', 'sql_dump', 'dashboard',
    'summary', 'detailed', 'audit_log'
]

LOGISTICS_EXPORT_COLUMNS = {
    'shipments': ['shipment_id', 'origin', 'destination', 'status', 'carrier', 'cost'],
    'delivery_orders': ['do_number', 'shipment_id', 'customer', 'address', 'status', 'delivery_date'],
    'pickup_orders': ['pickup_number', 'customer', 'address', 'status', 'pickup_date'],
    'trips': ['trip_id', 'vehicle', 'driver', 'route', 'status', 'start_time'],
    'routes': ['route_id', 'route_name', 'stops', 'distance', 'estimated_time'],
    'vehicles': ['vehicle_id', 'plate_number', 'type', 'status', 'capacity'],
    'drivers': ['driver_id', 'name', 'license', 'phone', 'status', 'vehicle_assigned'],
    'incidents': ['incident_id', 'shipment_id', 'type', 'severity', 'status', 'reported_at'],
    'costs': ['cost_id', 'trip_id', 'type', 'amount', 'invoice_number', 'date']
}


# =============================================================================
# DECORATORS AND HELPERS
# =============================================================================

def logistics_login_required(f):
    """Decorator to require logistics login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please log in first.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def logistics_permission_required(permission: str):
    """Decorator to check logistics-specific permissions."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'error')
                return redirect(url_for('login'))

            # SECURITY: Global Admin bypass is handled internally via wildcard permissions
            # in user_has_permission(). Do NOT add custom role checks here.

            # Check specific logistics permissions
            logistics_permissions = session.get('logistics_permissions', [])
            if 'all_logistics' in logistics_permissions or permission in logistics_permissions:
                return f(*args, **kwargs)

            flash('You do not have permission to access this logistics module.', 'error')
            return redirect(url_for('index'))
        return decorated_function
    return decorator


def get_current_user():
    """Get current logged-in user info."""
    if 'user_id' not in session:
        return None
    return {
        'id': session.get('user_id'),
        'username': session.get('username'),
        'role_id': session.get('role_id'),
        'role_name': session.get('role_name'),
        'company_id': session.get('company_id'),
        'logistics_permissions': session.get('logistics_permissions', [])
    }


def parse_date(date_str):
    """Safely parse date string to date object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        try:
            return datetime.strptime(date_str, '%d/%m/%Y').date()
        except ValueError:
            return None


def format_date(date_obj, fmt='%d/%m/%Y'):
    """Format date object to string."""
    if not date_obj:
        return ''
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime(fmt)


def error_response(message, status=400):
    """Return JSON error response."""
    if request.is_json:
        return jsonify({'error': message}), status
    flash(message, 'error')
    return None


# =============================================================================
# 1. LOGISTICS DASHBOARD
# =============================================================================

@logistics_bp.route('/')
@logistics_bp.route('/dashboard')
@logistics_login_required
def logistics_dashboard():
    """Logistics Dashboard - Main overview page."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()

        # Get shipment stats
        shipment_stats = get_shipment_stats(
            company_id=user.get('company_id'),
            date_from=request.args.get('date_from', today.strftime('%Y-%m-01')),
            date_to=request.args.get('date_to', today.strftime('%Y-%m-%d'))
        )

        # Get driver stats
        driver_stats = get_driver_availability_stats()

        # Get vehicle stats
        vehicle_stats = get_vehicle_availability_stats()

        # Get open incidents
        open_incidents = get_open_incidents_count()

        # Get POD pending
        pod_pending = get_pod_pending_count()

        # Recent shipments
        recent_shipments = db.execute("""
            SELECT s.*, c.name as customer_name,
                   d.full_name as driver_name, v.plate_number
            FROM logistics_shipments s
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            LEFT JOIN logistics_drivers d ON s.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            ORDER BY s.created_at DESC
            LIMIT 10
        """).fetchall()

        # Trips today
        trips_today = db.execute("""
            SELECT COUNT(*) as cnt FROM delivery_trips WHERE date = ?
        """, (today.strftime('%Y-%m-%d'),)).fetchone()['cnt']

        # Completed deliveries today
        deliveries_today = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_shipments
            WHERE status = 'delivered' AND date(actual_delivery) = ?
        """, (today.strftime('%Y-%m-%d'),)).fetchone()['cnt']

        # Active trips
        active_trips = db.execute("""
            SELECT t.*, d.full_name as driver_name, v.plate_number
            FROM delivery_trips t
            LEFT JOIN logistics_drivers d ON t.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON t.vehicle_id = v.id
            WHERE t.status IN ('Loading', 'Active')
            ORDER BY t.date DESC, t.id DESC
            LIMIT 10
        """).fetchall()

        # Shipments by type
        by_type = db.execute("""
            SELECT shipment_type, COUNT(*) as cnt
            FROM logistics_shipments
            WHERE date(created_at) BETWEEN ? AND ?
            GROUP BY shipment_type
        """, (today.strftime('%Y-%m-01'), today.strftime('%Y-%m-%d'))).fetchall()

        # Shipments by priority
        by_priority = db.execute("""
            SELECT priority, COUNT(*) as cnt
            FROM logistics_shipments
            WHERE date(created_at) BETWEEN ? AND ?
            GROUP BY priority
        """, (today.strftime('%Y-%m-01'), today.strftime('%Y-%m-%d'))).fetchall()

        # High priority shipments
        urgent_shipments = db.execute("""
            SELECT s.*, c.name as customer_name
            FROM logistics_shipments s
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            WHERE s.priority IN ('High', 'Urgent') AND s.status NOT IN ('delivered', 'cancelled', 'returned')
            ORDER BY s.priority DESC, s.planned_date ASC
            LIMIT 10
        """).fetchall()

        # Failed deliveries
        failed_deliveries = db.execute("""
            SELECT s.*, c.name as customer_name
            FROM logistics_shipments s
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            WHERE s.status = 'failed_delivery'
            ORDER BY s.updated_at DESC
            LIMIT 10
        """).fetchall()

        # Open incidents
        incidents = db.execute("""
            SELECT i.*, s.shipment_code
            FROM logistics_incidents i
            LEFT JOIN logistics_shipments s ON i.shipment_id = s.id
            WHERE i.status = 'open'
            ORDER BY i.created_at DESC
            LIMIT 10
        """).fetchall()

        # Expiring driver documents (next 30 days)
        expiring_driver_docs = db.execute("""
            SELECT dd.*, d.full_name, dd.document_type, dd.expiry_date
            FROM logistics_driver_documents dd
            JOIN logistics_drivers d ON dd.driver_id = d.id
            WHERE dd.expiry_date IS NOT NULL
            AND dd.expiry_date BETWEEN ? AND ?
            ORDER BY dd.expiry_date
            LIMIT 10
        """, (today.strftime('%Y-%m-%d'), (today + timedelta(days=30)).strftime('%Y-%m-%d'))).fetchall()

        # Expiring vehicle documents (next 30 days)
        expiring_vehicle_docs = db.execute("""
            SELECT vd.*, v.plate_number, v.vehicle_code, vd.document_type, vd.expiry_date
            FROM logistics_vehicle_documents vd
            JOIN logistics_vehicles v ON vd.vehicle_id = v.id
            WHERE vd.expiry_date IS NOT NULL
            AND vd.expiry_date BETWEEN ? AND ?
            ORDER BY vd.expiry_date
            LIMIT 10
        """, (today.strftime('%Y-%m-%d'), (today + timedelta(days=30)).strftime('%Y-%m-%d'))).fetchall()

        # Vehicle maintenance due
        maintenance_due = db.execute("""
            SELECT vm.*, v.plate_number, v.vehicle_code
            FROM logistics_vehicle_maintenance vm
            JOIN logistics_vehicles v ON vm.vehicle_id = v.id
            WHERE vm.status = 'pending' AND vm.scheduled_date <= ?
            ORDER BY vm.scheduled_date
            LIMIT 10
        """, (today.strftime('%Y-%m-%d'),)).fetchall()

        return render_template('logistics/dashboard.html',
                             title='Logistics Dashboard',
                             today=today,
                             shipment_stats=shipment_stats,
                             driver_stats=driver_stats,
                             vehicle_stats=vehicle_stats,
                             open_incidents=open_incidents,
                             pod_pending=pod_pending,
                             recent_shipments=[dict(r) for r in recent_shipments],
                             trips_today=trips_today,
                             deliveries_today=deliveries_today,
                             active_trips=[dict(r) for r in active_trips],
                             by_type=[dict(r) for r in by_type],
                             by_priority=[dict(r) for r in by_priority],
                             urgent_shipments=[dict(r) for r in urgent_shipments],
                             failed_deliveries=[dict(r) for r in failed_deliveries],
                             incidents=[dict(r) for r in incidents],
                             expiring_driver_docs=[dict(r) for r in expiring_driver_docs],
                             expiring_vehicle_docs=[dict(r) for r in expiring_vehicle_docs],
                             maintenance_due=[dict(r) for r in maintenance_due])
    finally:
        db.close()


# =============================================================================
# 1b. TMS EXECUTIVE DASHBOARD
# =============================================================================

@logistics_bp.route('/tms-dashboard')
@logistics_login_required
def tms_dashboard():
    """TMS Executive Transport Dashboard - Real-time operations overview."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()

        # Get filter parameters
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        branch_id = request.args.get('branch_id', '')
        vehicle_type = request.args.get('vehicle_type', '')

        # Build base WHERE clause for shipments
        ship_where = ["date(s.created_at) BETWEEN ? AND ?"]
        ship_params = [date_from, date_to]
        if branch_id:
            ship_where.append("s.branch_id = ?")
            ship_params.append(branch_id)
        if vehicle_type:
            ship_where.append("v.vehicle_type = ?")
            ship_params.append(vehicle_type)
        ship_where_clause = " AND ".join(ship_where)

        # KPI: Open Trips (not delivered/cancelled)
        open_trips = db.execute(f"""
            SELECT COUNT(*) as cnt FROM logistics_shipments s
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            WHERE s.status NOT IN ('delivered', 'cancelled', 'returned', 'closed')
            AND {ship_where_clause}
        """, ship_params).fetchone()['cnt']

        # KPI: In Transit
        in_transit = db.execute(f"""
            SELECT COUNT(*) as cnt FROM logistics_shipments s
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            WHERE s.status = 'in_transit'
            AND {ship_where_clause}
        """, ship_params).fetchone()['cnt']

        # KPI: Delayed (past SLA or in exception status)
        delayed = db.execute(f"""
            SELECT COUNT(*) as cnt FROM logistics_shipments s
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            WHERE s.status IN ('failed_delivery', 'delivery_attempted', 'rescheduled')
            AND date(s.created_at) BETWEEN ? AND ?
        """, [date_from, date_to]).fetchone()['cnt']

        # KPI: On-Time % (delivered on or before estimated_delivery)
        total_delivered = db.execute(f"""
            SELECT COUNT(*) as cnt FROM logistics_shipments s
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            WHERE s.status = 'delivered'
            AND {ship_where_clause}
        """, ship_params).fetchone()['cnt']

        on_time_delivered = db.execute(f"""
            SELECT COUNT(*) as cnt FROM logistics_shipments s
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            WHERE s.status = 'delivered'
            AND s.actual_delivery <= s.estimated_delivery
            AND {ship_where_clause}
        """, ship_params).fetchone()['cnt']

        on_time_pct = round((on_time_delivered / total_delivered * 100) if total_delivered > 0 else 0, 1)

        # KPI: Failed Deliveries
        failed_deliveries = db.execute(f"""
            SELECT COUNT(*) as cnt FROM logistics_shipments s
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            WHERE s.status = 'failed_delivery'
            AND {ship_where_clause}
        """, ship_params).fetchone()['cnt']

        # KPI: Available Vehicles
        available_vehicles = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_vehicles
            WHERE status = 'active' AND availability = 'available'
        """).fetchone()['cnt']

        # Active Trips table
        active_trips = db.execute("""
            SELECT s.*, d.full_name as driver_name, v.plate_number, v.vehicle_type,
                   c.name as customer_name,
                   CASE
                       WHEN s.status = 'in_transit' THEN 'In Transit'
                       WHEN s.status = 'assigned' THEN 'Assigned'
                       WHEN s.status = 'loaded' THEN 'Loaded'
                       WHEN s.status = 'departed' THEN 'Departed'
                       ELSE s.status
                   END as trip_status,
                   ROUND((julianday('now') - julianday(s.created_at)) * 24, 1) as hours_elapsed
            FROM logistics_shipments s
            LEFT JOIN logistics_drivers d ON s.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            WHERE s.status IN ('assigned', 'loaded', 'departed', 'in_transit')
            ORDER BY s.priority DESC, s.created_at ASC
            LIMIT 20
        """).fetchall()

        # Dispatch Board Summary
        pending_dispatches = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_shipments
            WHERE status IN ('ready_dispatch', 'scheduled')
        """).fetchone()['cnt']

        completed_today = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_shipments
            WHERE status = 'delivered' AND date(actual_delivery) = ?
        """, (today.strftime('%Y-%m-%d'),)).fetchone()['cnt']

        dispatch_exceptions = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_incidents
            WHERE status = 'open' AND date(created_at) = ?
        """, (today.strftime('%Y-%m-%d'),)).fetchone()['cnt']

        # Fleet Status breakdown
        fleet_status = {
            'available': db.execute("SELECT COUNT(*) as cnt FROM logistics_vehicles WHERE status = 'active' AND availability = 'available'").fetchone()['cnt'],
            'on_trip': db.execute("SELECT COUNT(*) as cnt FROM logistics_vehicles WHERE status = 'active' AND availability = 'on_trip'").fetchone()['cnt'],
            'maintenance': db.execute("SELECT COUNT(*) as cnt FROM logistics_vehicles WHERE status = 'active' AND availability = 'maintenance'").fetchone()['cnt'],
            'unavailable': db.execute("SELECT COUNT(*) as cnt FROM logistics_vehicles WHERE status = 'active' AND availability = 'unavailable'").fetchone()['cnt'],
        }

        # Driver Status breakdown
        driver_status = {
            'available': db.execute("SELECT COUNT(*) as cnt FROM logistics_drivers WHERE status = 'active' AND availability = 'available'").fetchone()['cnt'],
            'on_trip': db.execute("SELECT COUNT(*) as cnt FROM logistics_drivers WHERE status = 'active' AND availability = 'on_trip'").fetchone()['cnt'],
            'off_duty': db.execute("SELECT COUNT(*) as cnt FROM logistics_drivers WHERE status = 'active' AND availability IN ('on_leave', 'unavailable')").fetchone()['cnt'],
        }

        # Alerts/Exceptions panel
        alerts = db.execute("""
            SELECT i.*, s.shipment_code, d.full_name as driver_name, v.plate_number
            FROM logistics_incidents i
            LEFT JOIN logistics_shipments s ON i.shipment_id = s.id
            LEFT JOIN logistics_drivers d ON i.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON i.vehicle_id = v.id
            WHERE i.status = 'open'
            ORDER BY i.severity DESC, i.created_at DESC
            LIMIT 10
        """).fetchall()

        # Shipment Status Distribution
        status_dist = db.execute("""
            SELECT status, COUNT(*) as cnt
            FROM logistics_shipments
            WHERE date(created_at) BETWEEN ? AND ?
            GROUP BY status
            ORDER BY cnt DESC
        """, (date_from, date_to)).fetchall()

        # Delivery Performance (on-time vs late)
        delivery_perf = {
            'on_time': on_time_delivered,
            'late': total_delivered - on_time_delivered,
            'total': total_delivered
        }

        # Top Routes by Volume
        top_routes = db.execute("""
            SELECT r.route_name, r.route_code, COUNT(s.id) as shipment_count,
                   SUM(sl.weight) as total_weight
            FROM logistics_route_masters r
            LEFT JOIN logistics_shipments s ON s.route_id = r.id
            LEFT JOIN logistics_shipment_lines sl ON s.id = sl.shipment_id
            WHERE date(s.created_at) BETWEEN ? AND ?
            GROUP BY r.id
            HAVING shipment_count > 0
            ORDER BY shipment_count DESC
            LIMIT 10
        """, (date_from, date_to)).fetchall()

        # Cost Summary (if cost entries exist)
        cost_summary = db.execute("""
            SELECT SUM(amount) as total_cost, cost_type
            FROM logistics_cost_entries
            WHERE date(created_at) BETWEEN ? AND ?
            GROUP BY cost_type
            ORDER BY total_cost DESC
            LIMIT 10
        """, (date_from, date_to)).fetchall()

        total_cost = sum([c['total_cost'] or 0 for c in cost_summary])

        # Branches for filter dropdown
        branches = db.execute("SELECT id, name FROM branches WHERE is_active = 1 ORDER BY name").fetchall()

        # Vehicle types for filter dropdown
        vehicle_types = db.execute("SELECT DISTINCT vehicle_type FROM logistics_vehicles WHERE vehicle_type IS NOT NULL ORDER BY vehicle_type").fetchall()

        return render_template('logistics/tms_dashboard.html',
                             title='TMS Dashboard',
                             today=today,
                             date_from=date_from,
                             date_to=date_to,
                             branch_id=branch_id,
                             vehicle_type=vehicle_type,
                             branches=branches,
                             vehicle_types=vehicle_types,
                             kpis={
                                 'open_trips': open_trips,
                                 'in_transit': in_transit,
                                 'delayed': delayed,
                                 'on_time_pct': on_time_pct,
                                 'failed_deliveries': failed_deliveries,
                                 'available_vehicles': available_vehicles,
                             },
                             active_trips=[dict(r) for r in active_trips],
                             dispatch_summary={
                                 'pending': pending_dispatches,
                                 'completed_today': completed_today,
                                 'exceptions': dispatch_exceptions
                             },
                             fleet_status=fleet_status,
                             driver_status=driver_status,
                             alerts=[dict(r) for r in alerts],
                             status_dist=[dict(r) for r in status_dist],
                             delivery_perf=delivery_perf,
                             top_routes=[dict(r) for r in top_routes],
                             cost_summary=[dict(r) for r in cost_summary],
                             total_cost=total_cost)
    finally:
        db.close()


# =============================================================================
# 1c. LIVE DISPATCH BOARD
# =============================================================================

@logistics_bp.route('/dispatch-board')
@logistics_login_required
def dispatch_board():
    """Live Dispatch Board - Real-time dispatch operations."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()

        # Get filter parameters
        date_filter = request.args.get('date', today.strftime('%Y-%m-%d'))
        branch_id = request.args.get('branch_id', '')
        zone = request.args.get('zone', '')
        vehicle_id = request.args.get('vehicle_id', '')
        driver_id = request.args.get('driver_id', '')

        # Build filters
        filter_conditions = []
        filter_params = []

        if date_filter:
            filter_conditions.append("date(s.created_at) = ?")
            filter_params.append(date_filter)
        if branch_id:
            filter_conditions.append("s.branch_id = ?")
            filter_params.append(branch_id)
        if zone:
            filter_conditions.append("s.pickup_address LIKE ?")
            filter_params.append(f'%{zone}%')
        if vehicle_id:
            filter_conditions.append("s.vehicle_id = ?")
            filter_params.append(vehicle_id)
        if driver_id:
            filter_conditions.append("s.driver_id = ?")
            filter_params.append(driver_id)

        where_clause = " AND ".join(filter_conditions) if filter_conditions else "1=1"

        # Unassigned Loads panel (ready for dispatch)
        unassigned_loads = db.execute(f"""
            SELECT s.*, c.name as customer_name,
                   sl.total_weight, sl.total_volume,
                   p.pickup_address, p.scheduled_date as pickup_date
            FROM logistics_shipments s
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            LEFT JOIN (
                SELECT shipment_id, SUM(weight) as total_weight, SUM(volume) as total_volume
                FROM logistics_shipment_lines GROUP BY shipment_id
            ) sl ON s.id = sl.shipment_id
            LEFT JOIN logistics_pickup_orders p ON s.id = p.shipment_id
            WHERE s.status IN ('ready_dispatch', 'scheduled')
            AND s.driver_id IS NULL AND s.vehicle_id IS NULL
            ORDER BY s.priority DESC, s.planned_date ASC
            LIMIT 50
        """).fetchall()

        # Available Drivers panel
        available_drivers = db.execute("""
            SELECT d.*,
                   v.plate_number, v.vehicle_type, v.load_capacity_kg,
                   w.name as warehouse_name
            FROM logistics_drivers d
            LEFT JOIN logistics_vehicles v ON d.assigned_vehicle_id = v.id
            LEFT JOIN warehouses w ON d.branch_id = w.id
            WHERE d.status = 'active' AND d.availability = 'available'
            ORDER BY d.full_name
        """).fetchall()

        # Available Vehicles panel
        available_vehicles = db.execute("""
            SELECT v.*, d.full_name as driver_name,
                   vm.next_service_date, vm.status as maintenance_status
            FROM logistics_vehicles v
            LEFT JOIN logistics_drivers d ON v.assigned_driver_id = d.id
            LEFT JOIN logistics_vehicle_maintenance vm ON v.id = vm.vehicle_id AND vm.status = 'pending'
            WHERE v.status = 'active' AND v.availability = 'available'
            ORDER BY v.plate_number
        """).fetchall()

        # Today's Dispatches list
        todays_dispatches = db.execute("""
            SELECT s.*, d.full_name as driver_name, v.plate_number,
                   c.name as customer_name
            FROM logistics_shipments s
            LEFT JOIN logistics_drivers d ON s.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            WHERE date(s.dispatch_date) = ? AND s.driver_id IS NOT NULL
            ORDER BY s.dispatch_date, s.priority DESC
        """, (date_filter,)).fetchall()

        # Delayed Trips list
        delayed_trips = db.execute("""
            SELECT s.*, d.full_name as driver_name, v.plate_number,
                   c.name as customer_name,
                   CASE
                       WHEN s.estimated_delivery < datetime('now') THEN 'Overdue'
                       ELSE 'At Risk'
                   END as delay_status,
                   ROUND((julianday('now') - julianday(s.estimated_delivery)) * 24, 1) as hours_overdue
            FROM logistics_shipments s
            LEFT JOIN logistics_drivers d ON s.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            WHERE s.status IN ('in_transit', 'assigned', 'loaded', 'departed')
            AND (s.estimated_delivery < datetime('now') OR s.status = 'delivery_attempted')
            ORDER BY hours_overdue DESC, s.priority DESC
            LIMIT 20
        """).fetchall()

        # Dispatch Exceptions list
        dispatch_exceptions = db.execute("""
            SELECT i.*, s.shipment_code, s.priority, d.full_name as driver_name,
                   v.plate_number, i.severity
            FROM logistics_incidents i
            LEFT JOIN logistics_shipments s ON i.shipment_id = s.id
            LEFT JOIN logistics_drivers d ON i.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON i.vehicle_id = v.id
            WHERE i.status = 'open'
            ORDER BY i.severity DESC, i.created_at DESC
            LIMIT 20
        """).fetchall()

        # Dispatcher Queue (prioritized unassigned shipments)
        dispatcher_queue = db.execute("""
            SELECT s.*, c.name as customer_name,
                   sl.total_weight, sl.total_volume,
                   r.route_name, r.distance_km
            FROM logistics_shipments s
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            LEFT JOIN (
                SELECT shipment_id, SUM(weight) as total_weight, SUM(volume) as total_volume
                FROM logistics_shipment_lines GROUP BY shipment_id
            ) sl ON s.id = sl.shipment_id
            LEFT JOIN logistics_route_masters r ON s.route_id = r.id
            WHERE s.status IN ('ready_dispatch', 'scheduled')
            ORDER BY s.priority DESC, s.planned_date ASC
        """).fetchall()

        # Branches for filter
        branches = db.execute("SELECT id, name FROM branches WHERE is_active = 1 ORDER BY name").fetchall()

        # All vehicles for filter
        all_vehicles = db.execute("""
            SELECT id, plate_number, vehicle_type FROM logistics_vehicles
            WHERE status = 'active' ORDER BY plate_number
        """).fetchall()

        # All drivers for filter
        all_drivers = db.execute("""
            SELECT id, full_name, mobile FROM logistics_drivers
            WHERE status = 'active' ORDER BY full_name
        """).fetchall()

        return render_template('logistics/dispatch/board.html',
                             title='Live Dispatch Board',
                             today=today,
                             date_filter=date_filter,
                             branch_id=branch_id,
                             zone=zone,
                             vehicle_id=vehicle_id,
                             driver_id=driver_id,
                             branches=branches,
                             all_vehicles=all_vehicles,
                             all_drivers=all_drivers,
                             unassigned_loads=[dict(r) for r in unassigned_loads],
                             available_drivers=[dict(r) for r in available_drivers],
                             available_vehicles=[dict(r) for r in available_vehicles],
                             todays_dispatches=[dict(r) for r in todays_dispatches],
                             delayed_trips=[dict(r) for r in delayed_trips],
                             dispatch_exceptions=[dict(r) for r in dispatch_exceptions],
                             dispatcher_queue=[dict(r) for r in dispatcher_queue])
    finally:
        db.close()


@logistics_bp.route('/dispatch-board/assign', methods=['POST'])
@logistics_login_required
def dispatch_board_assign():
    """API endpoint to assign driver/vehicle to shipment."""
    if not request.is_json:
        return jsonify({'error': 'JSON required'}), 400

    data = request.get_json()
    shipment_id = data.get('shipment_id')
    driver_id = data.get('driver_id')
    vehicle_id = data.get('vehicle_id')
    notes = data.get('notes', '')

    if not shipment_id:
        return jsonify({'error': 'Shipment ID required'}), 400

    db = get_db()
    try:
        # Update shipment
        db.execute("""
            UPDATE logistics_shipments
            SET driver_id = ?, vehicle_id = ?,
                status = CASE WHEN status = 'ready_dispatch' THEN 'assigned' ELSE status END,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (driver_id, vehicle_id, shipment_id))

        # Update driver availability
        if driver_id:
            db.execute("""
                UPDATE logistics_drivers SET availability = 'on_trip' WHERE id = ?
            """, (driver_id,))

        # Update vehicle availability
        if vehicle_id:
            db.execute("""
                UPDATE logistics_vehicles SET availability = 'on_trip' WHERE id = ?
            """, (vehicle_id,))

        # Log audit
        log_logistics_audit(
            entity_type='shipment',
            entity_id=shipment_id,
            action='dispatch_assigned',
            user_id=session.get('user_id'),
            new_value=f'driver:{driver_id}, vehicle:{vehicle_id}',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )

        db.commit()
        return jsonify({'success': True, 'message': 'Assignment successful'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@logistics_bp.route('/dispatch-board/driver-availability', methods=['GET'])
@logistics_login_required
def dispatch_driver_availability():
    """Get driver availability hours for a specific date."""
    driver_id = request.args.get('driver_id')
    date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))

    db = get_db()
    try:
        # Get driver's assigned vehicle capacity
        driver = db.execute("""
            SELECT d.*, v.load_capacity_kg, v.vehicle_type
            FROM logistics_drivers d
            LEFT JOIN logistics_vehicles v ON d.assigned_vehicle_id = v.id
            WHERE d.id = ?
        """, (driver_id,)).fetchone()

        if not driver:
            return jsonify({'error': 'Driver not found'}), 404

        # Count current assignments for the date
        current_loads = db.execute("""
            SELECT COUNT(*) as cnt, SUM(sl.weight) as total_weight
            FROM logistics_shipments s
            LEFT JOIN logistics_shipment_lines sl ON s.id = sl.shipment_id
            WHERE s.driver_id = ? AND date(s.dispatch_date) = ?
        """, (driver_id, date_str)).fetchone()

        available_capacity = (driver['load_capacity_kg'] or 0) - (current_loads['total_weight'] or 0)

        return jsonify({
            'driver': dict(driver),
            'current_loads': current_loads['cnt'],
            'available_capacity': max(0, available_capacity),
            'vehicle_type': driver['vehicle_type']
        })
    finally:
        db.close()


# =============================================================================
# 2. SHIPMENTS MODULE
# =============================================================================

@logistics_bp.route('/shipments')
@logistics_login_required
def shipments_list():
    """Shipment list page with filtering and search."""
    user = get_current_user()
    db = get_db()

    try:
        # Get query parameters
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '')
        shipment_type = request.args.get('shipment_type', '')
        priority = request.args.get('priority', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        page = int(request.args.get('page', 1))
        per_page = 20

        # Build query
        query = """
            SELECT s.*, c.name as customer_name,
                   d.full_name as driver_name, v.plate_number,
                   w.name as warehouse_name
            FROM logistics_shipments s
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            LEFT JOIN logistics_drivers d ON s.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            LEFT JOIN warehouses w ON s.warehouse_id = w.id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (s.shipment_code LIKE ? OR s.consignee_name LIKE ? OR s.delivery_address LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])

        if status:
            query += " AND s.status = ?"
            params.append(status)

        if shipment_type:
            query += " AND s.shipment_type = ?"
            params.append(shipment_type)

        if priority:
            query += " AND s.priority = ?"
            params.append(priority)

        if date_from:
            query += " AND date(s.created_at) >= ?"
            params.append(date_from)

        if date_to:
            query += " AND date(s.created_at) <= ?"
            params.append(date_to)

        query += " ORDER BY s.priority DESC, s.created_at DESC"

        # Count total - build a separate count query
        count_params = list(params)
        count_query = "SELECT COUNT(*) as cnt FROM logistics_shipments s"
        count_query += " LEFT JOIN sdad_customers c ON s.customer_id = c.id"
        count_query += " LEFT JOIN logistics_drivers d ON s.driver_id = d.id"
        count_query += " LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id"
        count_query += " LEFT JOIN warehouses w ON s.warehouse_id = w.id"
        count_query += " WHERE 1=1"

        if search:
            count_query += " AND (s.shipment_code LIKE ? OR s.consignee_name LIKE ? OR s.delivery_address LIKE ?)"
        if status:
            count_query += " AND s.status = ?"
        if shipment_type:
            count_query += " AND s.shipment_type = ?"
        if priority:
            count_query += " AND s.priority = ?"
        if date_from:
            count_query += " AND date(s.created_at) >= ?"
        if date_to:
            count_query += " AND date(s.created_at) <= ?"

        total = db.execute(count_query, count_params).fetchone()['cnt']

        # Paginate
        offset = (page - 1) * per_page
        query += f" LIMIT {per_page} OFFSET {offset}"

        shipments = db.execute(query, params).fetchall()

        # Get lookups
        statuses = db.execute("SELECT DISTINCT setting_value FROM logistics_settings WHERE category = 'Shipment Status' AND is_active = 1").fetchall()
        types = db.execute("SELECT DISTINCT setting_value FROM logistics_settings WHERE category = 'Shipment Types' AND is_active = 1").fetchall()
        priorities = db.execute("SELECT DISTINCT setting_value FROM logistics_settings WHERE category = 'Priority' AND is_active = 1").fetchall()

        return render_template('logistics/shipments/list.html',
                             title='Shipments',
                             shipments=[dict(s) for s in shipments],
                             search=search,
                             status=status,
                             shipment_type=shipment_type,
                             priority=priority,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             total_pages=(total + per_page - 1) // per_page,
                             total=total,
                             statuses=[s['setting_value'] for s in statuses],
                             types=[t['setting_value'] for t in types],
                             priorities=[p['setting_value'] for p in priorities])
    finally:
        db.close()


@logistics_bp.route('/shipments/new', methods=['GET', 'POST'])
@logistics_login_required
def shipments_new():
    """Create new shipment."""
    user = get_current_user()
    db = get_db()

    if request.method == 'POST':
        try:
            data = request.form

            # Generate shipment code
            shipment_code = get_next_shipment_code()

            # Parse dates
            requested_date = parse_date(data.get('requested_date'))
            planned_date = parse_date(data.get('planned_date'))
            dispatch_date = parse_date(data.get('dispatch_date'))
            estimated_delivery = parse_date(data.get('estimated_delivery'))
            sla_target = parse_date(data.get('sla_target'))

            cursor = db.execute("""
                INSERT INTO logistics_shipments (
                    shipment_code, shipment_type, status, priority, company_id,
                    warehouse_id, customer_id, consignee_name, consignee_phone,
                    consignee_address, pickup_address, delivery_address, billing_party,
                    transport_mode, requested_date, planned_date, dispatch_date,
                    estimated_delivery, sla_target, carrier_id, driver_id, vehicle_id,
                    route_id, shipment_reference, notes, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                shipment_code,
                data.get('shipment_type', 'outbound'),
                data.get('status', 'draft'),
                data.get('priority', 'Normal'),
                data.get('company_id') or user.get('company_id'),
                data.get('warehouse_id'),
                data.get('customer_id'),
                data.get('consignee_name'),
                data.get('consignee_phone'),
                data.get('consignee_address'),
                data.get('pickup_address'),
                data.get('delivery_address'),
                data.get('billing_party'),
                data.get('transport_mode'),
                requested_date,
                planned_date,
                dispatch_date,
                estimated_delivery,
                sla_target,
                data.get('carrier_id'),
                data.get('driver_id'),
                data.get('vehicle_id'),
                data.get('route_id'),
                data.get('shipment_reference'),
                data.get('notes'),
                user['id']
            ))

            shipment_id = cursor.lastrowid

            # Add shipment lines if provided
            line_descriptions = data.getlist('line_description[]')
            line_quantities = data.getlist('line_quantity[]')
            line_units = data.getlist('line_unit[]')
            line_weights = data.getlist('line_weight[]')
            line_volumes = data.getlist('line_volume[]')
            line_cartons = data.getlist('line_cartons[]')

            for i in range(len(line_descriptions)):
                if line_descriptions[i]:
                    db.execute("""
                        INSERT INTO logistics_shipment_lines
                        (shipment_id, description, quantity, unit, weight, volume, cartons)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        shipment_id,
                        line_descriptions[i],
                        int(line_quantities[i]) if line_quantities[i] else 1,
                        line_units[i] if i < len(line_units) else 'pcs',
                        float(line_weights[i]) if i < len(line_weights) and line_weights[i] else 0,
                        float(line_volumes[i]) if i < len(line_volumes) and line_volumes[i] else 0,
                        int(line_cartons[i]) if i < len(line_cartons) and line_cartons[i] else 0
                    ))

            # Log status history
            db.execute("""
                INSERT INTO logistics_shipment_status_history (shipment_id, from_status, to_status, changed_by, reason)
                VALUES (?, ?, ?, ?, ?)
            """, (shipment_id, None, 'draft', user['id'], 'Shipment created'))

            db.commit()

            # Audit log
            log_logistics_audit('logistics_shipments', shipment_id, 'CREATE', user['id'],
                               new_value=f"Shipment {shipment_code} created")

            flash(f'Shipment {shipment_code} created successfully!', 'success')
            return redirect(url_for('logistics.shipments_view', id=shipment_id))

        except Exception as e:
            db.rollback()
            flash(f'Error creating shipment: {str(e)}', 'error')

    # GET request - show form
    try:
        warehouses = db.execute("SELECT * FROM warehouses ORDER BY name").fetchall()
        customers = db.execute("SELECT id, name, phone, address FROM sdad_customers ORDER BY name LIMIT 500").fetchall()
        drivers = db.execute("SELECT * FROM logistics_drivers WHERE status = 'active' ORDER BY full_name").fetchall()
        vehicles = db.execute("SELECT * FROM logistics_vehicles WHERE status = 'active' ORDER BY plate_number").fetchall()
        carriers = db.execute("SELECT * FROM logistics_carriers WHERE status = 'active' ORDER BY carrier_name").fetchall()
        routes = db.execute("SELECT * FROM logistics_route_masters WHERE is_active = 1 ORDER BY route_name").fetchall()

        # Get lookup values from settings
        statuses = db.execute("SELECT setting_value FROM logistics_settings WHERE category = 'Shipment Status' AND is_active = 1").fetchall()
        types = db.execute("SELECT setting_value FROM logistics_settings WHERE category = 'Shipment Types' AND is_active = 1").fetchall()
        priorities = db.execute("SELECT setting_value FROM logistics_settings WHERE category = 'Priority' AND is_active = 1").fetchall()
        transport_modes = db.execute("SELECT setting_value FROM logistics_settings WHERE category = 'Transport Mode' AND is_active = 1").fetchall()

        return render_template('logistics/shipments/new.html',
                             title='New Shipment',
                             shipment=None,
                             warehouses=[dict(w) for w in warehouses],
                             customers=[dict(c) for c in customers],
                             drivers=[dict(d) for d in drivers],
                             vehicles=[dict(v) for v in vehicles],
                             carriers=[dict(c) for c in carriers],
                             routes=[dict(r) for r in routes],
                             statuses=[s['setting_value'] for s in statuses],
                             types=[t['setting_value'] for t in types],
                             priorities=[p['setting_value'] for p in priorities],
                             transport_modes=[t['setting_value'] for t in transport_modes])
    finally:
        db.close()


@logistics_bp.route('/shipments/view/<int:id>')
@logistics_login_required
def shipments_view(id):
    """View shipment detail page."""
    user = get_current_user()
    db = get_db()

    try:
        shipment = db.execute("""
            SELECT s.*, c.name as customer_name, c.phone as customer_phone, c.address as customer_address,
                   d.full_name as driver_name, d.mobile as driver_mobile,
                   v.plate_number, v.vehicle_type,
                   cr.carrier_name,
                   r.route_name,
                   w.name as warehouse_name,
                   u.username as created_by_name
            FROM logistics_shipments s
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            LEFT JOIN logistics_drivers d ON s.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            LEFT JOIN logistics_carriers cr ON s.carrier_id = cr.id
            LEFT JOIN logistics_route_masters r ON s.route_id = r.id
            LEFT JOIN warehouses w ON s.warehouse_id = w.id
            LEFT JOIN users u ON s.created_by = u.id
            WHERE s.id = ?
        """, (id,)).fetchone()

        if not shipment:
            flash('Shipment not found.', 'error')
            return redirect(url_for('logistics.shipments_list'))

        # Get shipment lines
        lines = db.execute("SELECT * FROM logistics_shipment_lines WHERE shipment_id = ?", (id,)).fetchall()

        # Get status history
        history = db.execute("""
            SELECT h.*, u.username as changed_by_name
            FROM logistics_shipment_status_history h
            LEFT JOIN users u ON h.changed_by = u.id
            WHERE h.shipment_id = ?
            ORDER BY h.changed_at DESC
        """, (id,)).fetchall()

        # Get cost entries
        costs = db.execute("""
            SELECT c.*, u.username as created_by_name
            FROM logistics_cost_entries c
            LEFT JOIN users u ON c.created_by = u.id
            WHERE c.shipment_id = ?
            ORDER BY c.created_at DESC
        """, (id,)).fetchall()

        # Get POD record
        pod = db.execute("SELECT * FROM logistics_pod_records WHERE shipment_id = ?", (id,)).fetchone()

        # Get incidents
        incidents = db.execute("""
            SELECT * FROM logistics_incidents WHERE shipment_id = ? ORDER BY created_at DESC
        """, (id,)).fetchall()

        # Get related delivery orders
        delivery_orders = db.execute("""
            SELECT * FROM logistics_delivery_orders WHERE shipment_id = ?
        """, (id,)).fetchall()

        return render_template('logistics/shipments/view.html',
                             title=f"Shipment {shipment['shipment_code']}",
                             shipment=dict(shipment),
                             lines=[dict(l) for l in lines],
                             history=[dict(h) for h in history],
                             costs=[dict(c) for c in costs],
                             pod=dict(pod) if pod else None,
                             incidents=[dict(i) for i in incidents],
                             delivery_orders=[dict(d) for d in delivery_orders])
    finally:
        db.close()


@logistics_bp.route('/shipments/edit/<int:id>', methods=['GET', 'POST'])
@logistics_login_required
def shipments_edit(id):
    """Edit shipment details."""
    user = get_current_user()
    db = get_db()

    try:
        shipment = db.execute("SELECT * FROM logistics_shipments WHERE id = ?", (id,)).fetchone()
        if not shipment:
            flash('Shipment not found.', 'error')
            return redirect(url_for('logistics.shipments_list'))

        if request.method == 'POST':
            try:
                data = request.form
                old_status = shipment['status']

                # Parse dates
                requested_date = parse_date(data.get('requested_date'))
                planned_date = parse_date(data.get('planned_date'))
                dispatch_date = parse_date(data.get('dispatch_date'))
                estimated_delivery = parse_date(data.get('estimated_delivery'))
                sla_target = parse_date(data.get('sla_target'))

                # Update shipment
                db.execute("""
                    UPDATE logistics_shipments SET
                        shipment_type = ?, status = ?, priority = ?,
                        warehouse_id = ?, customer_id = ?, consignee_name = ?,
                        consignee_phone = ?, consignee_address = ?, pickup_address = ?,
                        delivery_address = ?, billing_party = ?, transport_mode = ?,
                        requested_date = ?, planned_date = ?, dispatch_date = ?,
                        estimated_delivery = ?, sla_target = ?, carrier_id = ?,
                        driver_id = ?, vehicle_id = ?, route_id = ?,
                        shipment_reference = ?, notes = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    data.get('shipment_type'),
                    data.get('status'),
                    data.get('priority'),
                    data.get('warehouse_id'),
                    data.get('customer_id'),
                    data.get('consignee_name'),
                    data.get('consignee_phone'),
                    data.get('consignee_address'),
                    data.get('pickup_address'),
                    data.get('delivery_address'),
                    data.get('billing_party'),
                    data.get('transport_mode'),
                    requested_date,
                    planned_date,
                    dispatch_date,
                    estimated_delivery,
                    sla_target,
                    data.get('carrier_id'),
                    data.get('driver_id'),
                    data.get('vehicle_id'),
                    data.get('route_id'),
                    data.get('shipment_reference'),
                    data.get('notes'),
                    id
                ))

                # Log status change
                new_status = data.get('status')
                if old_status != new_status:
                    db.execute("""
                        INSERT INTO logistics_shipment_status_history (shipment_id, from_status, to_status, changed_by, reason)
                        VALUES (?, ?, ?, ?, ?)
                    """, (id, old_status, new_status, user['id'], data.get('status_change_reason')))

                db.commit()

                # Audit log
                log_logistics_audit('logistics_shipments', id, 'UPDATE', user['id'],
                                   new_value=f"Shipment {shipment['shipment_code']} updated")

                flash('Shipment updated successfully!', 'success')
                return redirect(url_for('logistics.shipments_view', id=id))

            except Exception as e:
                db.rollback()
                flash(f'Error updating shipment: {str(e)}', 'error')

        # GET request
        warehouses = db.execute("SELECT * FROM warehouses ORDER BY name").fetchall()
        customers = db.execute("SELECT id, name, phone, address FROM sdad_customers ORDER BY name LIMIT 500").fetchall()
        drivers = db.execute("SELECT * FROM logistics_drivers WHERE status = 'active' ORDER BY full_name").fetchall()
        vehicles = db.execute("SELECT * FROM logistics_vehicles WHERE status = 'active' ORDER BY plate_number").fetchall()
        carriers = db.execute("SELECT * FROM logistics_carriers WHERE status = 'active' ORDER BY carrier_name").fetchall()
        routes = db.execute("SELECT * FROM logistics_route_masters WHERE is_active = 1 ORDER BY route_name").fetchall()
        lines = db.execute("SELECT * FROM logistics_shipment_lines WHERE shipment_id = ?", (id,)).fetchall()

        statuses = db.execute("SELECT setting_value FROM logistics_settings WHERE category = 'Shipment Status' AND is_active = 1").fetchall()
        types = db.execute("SELECT setting_value FROM logistics_settings WHERE category = 'Shipment Types' AND is_active = 1").fetchall()
        priorities = db.execute("SELECT setting_value FROM logistics_settings WHERE category = 'Priority' AND is_active = 1").fetchall()
        transport_modes = db.execute("SELECT setting_value FROM logistics_settings WHERE category = 'Transport Mode' AND is_active = 1").fetchall()

        return render_template('logistics/shipments/edit.html',
                             title=f"Edit Shipment {shipment['shipment_code']}",
                             shipment=dict(shipment),
                             lines=[dict(l) for l in lines],
                             warehouses=[dict(w) for w in warehouses],
                             customers=[dict(c) for c in customers],
                             drivers=[dict(d) for d in drivers],
                             vehicles=[dict(v) for v in vehicles],
                             carriers=[dict(c) for c in carriers],
                             routes=[dict(r) for r in routes],
                             statuses=[s['setting_value'] for s in statuses],
                             types=[t['setting_value'] for t in types],
                             priorities=[p['setting_value'] for p in priorities],
                             transport_modes=[t['setting_value'] for t in transport_modes])
    finally:
        db.close()


@logistics_bp.route('/shipments/delete/<int:id>', methods=['POST'])
@logistics_login_required
def shipments_delete(id):
    """Delete/archive shipment."""
    user = get_current_user()
    db = get_db()

    try:
        shipment = db.execute("SELECT * FROM logistics_shipments WHERE id = ?", (id,)).fetchone()
        if not shipment:
            return jsonify({'error': 'Shipment not found'}), 404

        # Only allow deletion of draft shipments
        if shipment['status'] not in ('draft', 'cancelled'):
            return jsonify({'error': 'Only draft or cancelled shipments can be deleted'}), 400

        db.execute("DELETE FROM logistics_shipments WHERE id = ?", (id,))
        db.commit()

        log_logistics_audit('logistics_shipments', id, 'DELETE', user['id'],
                           new_value=f"Shipment {shipment['shipment_code']} deleted")

        return jsonify({'success': True, 'message': 'Shipment deleted successfully'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@logistics_bp.route('/shipments/status/<int:id>', methods=['POST'])
@logistics_login_required
def shipments_update_status(id):
    """Update shipment status."""
    user = get_current_user()
    db = get_db()

    try:
        data = request.get_json() if request.is_json else request.form
        new_status = data.get('status')
        reason = data.get('reason', '')

        if not new_status:
            return jsonify({'error': 'Status is required'}), 400

        shipment = db.execute("SELECT * FROM logistics_shipments WHERE id = ?", (id,)).fetchone()
        if not shipment:
            return jsonify({'error': 'Shipment not found'}), 404

        old_status = shipment['status']

        db.execute("""
            UPDATE logistics_shipments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (new_status, id))

        # Log status change
        db.execute("""
            INSERT INTO logistics_shipment_status_history (shipment_id, from_status, to_status, changed_by, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (id, old_status, new_status, user['id'], reason))

        # Set actual delivery timestamp if delivered
        if new_status == 'delivered':
            db.execute("""
                UPDATE logistics_shipments SET actual_delivery = CURRENT_TIMESTAMP WHERE id = ?
            """, (id,))

        db.commit()

        log_logistics_audit('logistics_shipments', id, 'STATUS_CHANGE', user['id'],
                           field_name='status', old_value=old_status, new_value=new_status)

        return jsonify({'success': True, 'message': f'Status updated to {new_status}'})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


# =============================================================================
# 3. DELIVERY ORDERS
# =============================================================================

@logistics_bp.route('/delivery-orders')
@logistics_login_required
def delivery_orders_list():
    """Delivery orders list page."""
    user = get_current_user()
    db = get_db()

    try:
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        page = int(request.args.get('page', 1))
        per_page = 20

        query = """
            SELECT do.*, s.shipment_code, c.name as customer_name
            FROM logistics_delivery_orders do
            LEFT JOIN logistics_shipments s ON do.shipment_id = s.id
            LEFT JOIN sdad_customers c ON do.customer_id = c.id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (do.do_number LIKE ? OR c.name LIKE ? OR do.contact_person LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])

        if status:
            query += " AND do.status = ?"
            params.append(status)

        if date_from:
            query += " AND date(do.created_at) >= ?"
            params.append(date_from)

        if date_to:
            query += " AND date(do.created_at) <= ?"
            params.append(date_to)

        query += " ORDER BY do.created_at DESC"

        count_query = query.replace("SELECT do.*, s.shipment_code, c.name as customer_name", "SELECT COUNT(*) as cnt")
        total = db.execute(count_query, params).fetchone()['cnt']

        offset = (page - 1) * per_page
        query += f" LIMIT {per_page} OFFSET {offset}"

        orders = db.execute(query, params).fetchall()

        statuses = ['pending', 'confirmed', 'in_transit', 'delivered', 'partial', 'failed', 'cancelled']

        return render_template('logistics/delivery_orders/list.html',
                             title='Delivery Orders',
                             orders=[dict(o) for o in orders],
                             search=search,
                             status=status,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             total_pages=(total + per_page - 1) // per_page,
                             total=total,
                             statuses=statuses)
    finally:
        db.close()


@logistics_bp.route('/delivery-orders/new', methods=['GET', 'POST'])
@logistics_login_required
def delivery_orders_new():
    """Create new delivery order."""
    user = get_current_user()
    db = get_db()

    if request.method == 'POST':
        try:
            data = request.form
            do_number = get_next_do_number()

            cursor = db.execute("""
                INSERT INTO logistics_delivery_orders (
                    do_number, shipment_id, customer_id, contact_person, contact_phone,
                    shipping_address, billing_address, scheduled_date, promised_date,
                    priority, required_vehicle_type, required_handling, temperature_control,
                    notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                do_number,
                data.get('shipment_id'),
                data.get('customer_id'),
                data.get('contact_person'),
                data.get('contact_phone'),
                data.get('shipping_address'),
                data.get('billing_address'),
                parse_date(data.get('scheduled_date')),
                parse_date(data.get('promised_date')),
                data.get('priority', 'Normal'),
                data.get('required_vehicle_type'),
                data.get('required_handling'),
                1 if data.get('temperature_control') else 0,
                data.get('notes')
            ))

            db.commit()
            flash(f'Delivery Order {do_number} created!', 'success')
            return redirect(url_for('logistics.delivery_orders_list'))

        except Exception as e:
            db.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            db.close()

    # GET
    try:
        customers = db.execute("SELECT id, name FROM sdad_customers ORDER BY name LIMIT 500").fetchall()
        shipments = db.execute("""
            SELECT id, shipment_code FROM logistics_shipments
            WHERE status NOT IN ('delivered', 'cancelled', 'returned')
            ORDER BY created_at DESC
        """).fetchall()
        vehicle_types = db.execute("SELECT setting_value FROM logistics_settings WHERE category = 'Vehicle Types' AND is_active = 1").fetchall()

        return render_template('logistics/delivery_orders/new.html',
                             title='New Delivery Order',
                             order=None,
                             customers=[dict(c) for c in customers],
                             shipments=[dict(s) for s in shipments],
                             vehicle_types=[v['setting_value'] for v in vehicle_types])
    finally:
        db.close()


@logistics_bp.route('/delivery-orders/view/<int:id>')
@logistics_login_required
def delivery_orders_view(id):
    """View delivery order detail."""
    user = get_current_user()
    db = get_db()

    try:
        order = db.execute("""
            SELECT do.*, s.shipment_code, c.name as customer_name, c.phone as customer_phone
            FROM logistics_delivery_orders do
            LEFT JOIN logistics_shipments s ON do.shipment_id = s.id
            LEFT JOIN sdad_customers c ON do.customer_id = c.id
            WHERE do.id = ?
        """, (id,)).fetchone()

        if not order:
            flash('Delivery order not found.', 'error')
            return redirect(url_for('logistics.delivery_orders_list'))

        return render_template('logistics/delivery_orders/view.html',
                             title=f"Delivery Order {order['do_number']}",
                             order=dict(order))
    finally:
        db.close()


# =============================================================================
# 3a. TRIP MANAGEMENT - Full Lifecycle
# =============================================================================

TRIP_STATUSES = ['draft', 'planned', 'ready_for_dispatch', 'dispatched', 'en_route', 'arrived', 'completed', 'partially_completed', 'failed', 'cancelled', 'closed']

@logistics_bp.route('/trips/new', methods=['GET', 'POST'])
@logistics_login_required
def trips_new():
    """Create new trip with full form."""
    user = get_current_user()
    db = get_db()

    if request.method == 'POST':
        try:
            data = request.form
            trip_code = get_next_trip_code()

            cursor = db.execute("""
                INSERT INTO logistics_trips (
                    trip_code, trip_name, status, priority, route_id,
                    vehicle_id, driver_id, helper_id,
                    planned_departure, planned_arrival,
                    origin_location, destination_location,
                    distance_km, notes, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trip_code,
                data.get('trip_name'),
                'planned',
                data.get('priority', 'Normal'),
                data.get('route_id') or None,
                data.get('vehicle_id') or None,
                data.get('driver_id') or None,
                data.get('helper_id') or None,
                data.get('planned_departure') or None,
                data.get('planned_arrival') or None,
                data.get('origin_location'),
                data.get('destination_location'),
                float(data.get('distance_km', 0)),
                data.get('notes'),
                user['id']
            ))

            trip_id = cursor.lastrowid

            # If route is selected, copy stops from route
            route_id = data.get('route_id')
            if route_id:
                route_stops = db.execute("""
                    SELECT * FROM logistics_route_stops
                    WHERE route_id = ? AND is_active = 1
                    ORDER BY stop_order
                """, (route_id,)).fetchall()

                for rs in route_stops:
                    db.execute("""
                        INSERT INTO logistics_trip_stops (
                            trip_id, stop_sequence, route_stop_id,
                            stop_name, address, latitude, longitude,
                            planned_arrival, service_time_minutes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        trip_id, rs['stop_order'], rs['id'],
                        rs['stop_name'], rs['address'], rs['latitude'], rs['longitude'],
                        rs['estimated_arrival'], rs['service_time_minutes']
                    ))

            db.commit()
            flash(f'Trip {trip_code} created successfully!', 'success')
            return redirect(url_for('logistics.trips_view', id=trip_id))

        except Exception as e:
            db.rollback()
            flash(f'Error creating trip: {str(e)}', 'error')

    try:
        vehicles = db.execute("""
            SELECT id, vehicle_code, plate_number, vehicle_type
            FROM logistics_vehicles
            WHERE status = 'active' AND availability = 'available'
            ORDER BY vehicle_code
        """).fetchall()

        drivers = db.execute("""
            SELECT id, driver_code, full_name, mobile
            FROM logistics_drivers
            WHERE status = 'active' AND availability = 'available'
            ORDER BY full_name
        """).fetchall()

        routes = db.execute("""
            SELECT id, route_code, route_name, route_type, distance_km,
                   (SELECT COUNT(*) FROM logistics_route_stops WHERE route_id = r.id) as stop_count
            FROM logistics_route_masters r
            WHERE is_active = 1
            ORDER BY route_name
        """).fetchall()

        return render_template('logistics/trips/new.html',
                             title='New Trip',
                             vehicles=[dict(v) for v in vehicles],
                             drivers=[dict(d) for d in drivers],
                             routes=[dict(r) for r in routes])
    finally:
        db.close()


@logistics_bp.route('/trips/<int:id>/edit', methods=['GET', 'POST'])
@logistics_login_required
def trips_edit(id):
    """Edit trip."""
    user = get_current_user()
    db = get_db()

    try:
        trip = db.execute("SELECT * FROM logistics_trips WHERE id = ?", (id,)).fetchone()
        if not trip:
            flash('Trip not found.', 'error')
            return redirect(url_for('logistics.trips_list'))

        if request.method == 'POST':
            try:
                data = request.form

                db.execute("""
                    UPDATE logistics_trips SET
                        trip_name = ?, priority = ?, route_id = ?,
                        vehicle_id = ?, driver_id = ?, helper_id = ?,
                        planned_departure = ?, planned_arrival = ?,
                        origin_location = ?, destination_location = ?,
                        distance_km = ?, notes = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    data.get('trip_name'),
                    data.get('priority', 'Normal'),
                    data.get('route_id') or None,
                    data.get('vehicle_id') or None,
                    data.get('driver_id') or None,
                    data.get('helper_id') or None,
                    data.get('planned_departure') or None,
                    data.get('planned_arrival') or None,
                    data.get('origin_location'),
                    data.get('destination_location'),
                    float(data.get('distance_km', 0)),
                    data.get('notes'),
                    id
                ))

                db.commit()
                flash('Trip updated successfully!', 'success')
                return redirect(url_for('logistics.trips_view', id=id))

            except Exception as e:
                db.rollback()
                flash(f'Error updating trip: {str(e)}', 'error')

        vehicles = db.execute("""
            SELECT id, vehicle_code, plate_number, vehicle_type
            FROM logistics_vehicles WHERE status = 'active'
            ORDER BY vehicle_code
        """).fetchall()

        drivers = db.execute("""
            SELECT id, driver_code, full_name, mobile
            FROM logistics_drivers WHERE status = 'active'
            ORDER BY full_name
        """).fetchall()

        routes = db.execute("""
            SELECT id, route_code, route_name, route_type, distance_km
            FROM logistics_route_masters WHERE is_active = 1
            ORDER BY route_name
        """).fetchall()

        return render_template('logistics/trips/edit.html',
                             title=f'Edit Trip {trip["trip_code"]}',
                             trip=dict(trip),
                             vehicles=[dict(v) for v in vehicles],
                             drivers=[dict(d) for d in drivers],
                             routes=[dict(r) for r in routes])
    finally:
        db.close()


@logistics_bp.route('/trips/<int:id>/assign', methods=['GET', 'POST'])
@logistics_login_required
def trips_assign(id):
    """Assign/reassign driver and vehicle to trip."""
    user = get_current_user()
    db = get_db()

    try:
        trip = db.execute("SELECT * FROM logistics_trips WHERE id = ?", (id,)).fetchone()
        if not trip:
            flash('Trip not found.', 'error')
            return redirect(url_for('logistics.trips_list'))

        if request.method == 'POST':
            try:
                data = request.form
                old_driver = trip['driver_id']
                old_vehicle = trip['vehicle_id']
                new_driver = data.get('driver_id') or None
                new_vehicle = data.get('vehicle_id') or None

                db.execute("""
                    UPDATE logistics_trips SET
                        driver_id = ?, vehicle_id = ?,
                        status = CASE WHEN driver_id IS NOT NULL AND vehicle_id IS NOT NULL
                                     THEN 'ready_for_dispatch' ELSE status END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_driver, new_vehicle, id))

                # Update driver availability
                if old_driver and str(old_driver) != str(new_driver):
                    db.execute("UPDATE logistics_drivers SET availability = 'available' WHERE id = ?", (old_driver,))
                if new_driver:
                    db.execute("UPDATE logistics_drivers SET availability = 'on_trip' WHERE id = ?", (new_driver,))

                # Update vehicle availability
                if old_vehicle and str(old_vehicle) != str(new_vehicle):
                    db.execute("UPDATE logistics_vehicles SET availability = 'available' WHERE id = ?", (old_vehicle,))
                if new_vehicle:
                    db.execute("UPDATE logistics_vehicles SET availability = 'on_trip' WHERE id = ?", (new_vehicle,))

                db.commit()
                log_logistics_audit('trip', id, 'assign', user['id'],
                                   old_value=f"driver:{old_driver},vehicle:{old_vehicle}",
                                   new_value=f"driver:{new_driver},vehicle:{new_vehicle}")
                flash('Driver and vehicle assigned successfully!', 'success')
                return redirect(url_for('logistics.trips_view', id=id))

            except Exception as e:
                db.rollback()
                flash(f'Error assigning: {str(e)}', 'error')

        vehicles = db.execute("""
            SELECT id, vehicle_code, plate_number, vehicle_type
            FROM logistics_vehicles
            WHERE status = 'active' AND availability IN ('available', 'on_trip')
            ORDER BY vehicle_code
        """).fetchall()

        drivers = db.execute("""
            SELECT id, driver_code, full_name, mobile
            FROM logistics_drivers
            WHERE status = 'active' AND availability IN ('available', 'on_trip')
            ORDER BY full_name
        """).fetchall()

        return render_template('logistics/trips/assign.html',
                             title=f'Assign to Trip {trip["trip_code"]}',
                             trip=dict(trip),
                             vehicles=[dict(v) for v in vehicles],
                             drivers=[dict(d) for d in drivers])
    finally:
        db.close()


@logistics_bp.route('/trips/<int:id>/start', methods=['POST'])
@logistics_login_required
def trips_start(id):
    """Mark trip as dispatched/en route."""
    user = get_current_user()
    db = get_db()

    try:
        trip = db.execute("SELECT * FROM logistics_trips WHERE id = ?", (id,)).fetchone()
        if not trip:
            return jsonify({'error': 'Trip not found'}), 404

        if trip['status'] not in ['planned', 'ready_for_dispatch']:
            return jsonify({'error': f'Cannot start trip in {trip["status"]} status'}), 400

        db.execute("""
            UPDATE logistics_trips SET
                status = 'dispatched',
                actual_departure = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (id,))

        db.commit()
        log_logistics_audit('trip', id, 'start', user['id'], old_value=trip['status'], new_value='dispatched')
        return jsonify({'success': True, 'message': 'Trip dispatched successfully'})

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@logistics_bp.route('/trips/<int:id>/complete', methods=['POST'])
@logistics_login_required
def trips_complete(id):
    """Mark trip as completed."""
    user = get_current_user()
    db = get_db()

    try:
        trip = db.execute("SELECT * FROM logistics_trips WHERE id = ?", (id,)).fetchone()
        if not trip:
            return jsonify({'error': 'Trip not found'}), 404

        data = request.json if request.is_json else request.form

        # Check if all stops are done
        pending_stops = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_trip_stops
            WHERE trip_id = ? AND status NOT IN ('completed', 'failed', 'skipped')
        """, (id,)).fetchone()['cnt']

        if pending_stops > 0:
            return jsonify({'error': f'{pending_stops} stops still pending'}), 400

        failed_stops = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_trip_stops
            WHERE trip_id = ? AND status = 'failed'
        """, (id,)).fetchone()['cnt']

        new_status = 'completed' if failed_stops == 0 else 'partially_completed'

        db.execute("""
            UPDATE logistics_trips SET
                status = ?, actual_arrival = CURRENT_TIMESTAMP,
                completed_stops = (SELECT COUNT(*) FROM logistics_trip_stops WHERE trip_id = ? AND status = 'completed'),
                failed_stops = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_status, id, failed_stops, id))

        # Free up driver and vehicle
        if trip['driver_id']:
            db.execute("UPDATE logistics_drivers SET availability = 'available' WHERE id = ?", (trip['driver_id'],))
        if trip['vehicle_id']:
            db.execute("UPDATE logistics_vehicles SET availability = 'available' WHERE id = ?", (trip['vehicle_id'],))

        db.commit()
        log_logistics_audit('trip', id, 'complete', user['id'], old_value=trip['status'], new_value=new_status)
        return jsonify({'success': True, 'message': f'Trip marked as {new_status}'})

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@logistics_bp.route('/trips/<int:id>/cancel', methods=['POST'])
@logistics_login_required
def trips_cancel(id):
    """Cancel trip."""
    user = get_current_user()
    db = get_db()

    try:
        trip = db.execute("SELECT * FROM logistics_trips WHERE id = ?", (id,)).fetchone()
        if not trip:
            return jsonify({'error': 'Trip not found'}), 404

        if trip['status'] in ['completed', 'cancelled', 'closed']:
            return jsonify({'error': f'Cannot cancel trip in {trip["status"]} status'}), 400

        data = request.json if request.is_json else request.form
        reason = data.get('reason', 'No reason provided') if isinstance(data, dict) else request.form.get('reason', 'No reason provided')

        db.execute("""
            UPDATE logistics_trips SET
                status = 'cancelled',
                cancellation_reason = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (reason, id))

        # Free up driver and vehicle
        if trip['driver_id']:
            db.execute("UPDATE logistics_drivers SET availability = 'available' WHERE id = ?", (trip['driver_id'],))
        if trip['vehicle_id']:
            db.execute("UPDATE logistics_vehicles SET availability = 'available' WHERE id = ?", (trip['vehicle_id'],))

        db.commit()
        log_logistics_audit('trip', id, 'cancel', user['id'], old_value=trip['status'], new_value='cancelled')
        return jsonify({'success': True, 'message': 'Trip cancelled successfully'})

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@logistics_bp.route('/trips/<int:id>/timeline')
@logistics_login_required
def trips_timeline(id):
    """Trip timeline view with all stop progress."""
    user = get_current_user()
    db = get_db()

    try:
        trip = db.execute("""
            SELECT t.*, d.full_name as driver_name, d.mobile as driver_mobile,
                   v.plate_number, v.vehicle_type, v.model,
                   r.route_name, r.route_code
            FROM logistics_trips t
            LEFT JOIN logistics_drivers d ON t.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON t.vehicle_id = v.id
            LEFT JOIN logistics_route_masters r ON t.route_id = r.id
            WHERE t.id = ?
        """, (id,)).fetchone()

        if not trip:
            flash('Trip not found.', 'error')
            return redirect(url_for('logistics.trips_list'))

        stops = db.execute("""
            SELECT ts.*, c.name as customer_name
            FROM logistics_trip_stops ts
            LEFT JOIN sdad_customers c ON ts.customer_id = c.id
            WHERE ts.trip_id = ?
            ORDER BY ts.sequence_order
        """, (id,)).fetchall()

        # Calculate progress
        total_stops = len(stops)
        completed_stops = len([s for s in stops if s['status'] == 'completed'])
        failed_stops = len([s for s in stops if s['status'] == 'failed'])
        pending_stops = len([s for s in stops if s['status'] == 'pending'])
        progress = round((completed_stops / total_stops * 100) if total_stops > 0 else 0, 1)

        return render_template('logistics/trips/timeline.html',
                             title=f'Trip {trip["trip_code"]} Timeline',
                             trip=dict(trip),
                             stops=[dict(s) for s in stops],
                             progress=progress,
                             total_stops=total_stops,
                             completed_stops=completed_stops,
                             failed_stops=failed_stops,
                             pending_stops=pending_stops)
    finally:
        db.close()


@logistics_bp.route('/trips/<int:id>/cost')
@logistics_login_required
def trips_cost(id):
    """Trip costing view."""
    user = get_current_user()
    db = get_db()

    try:
        trip = db.execute("""
            SELECT t.*, d.full_name as driver_name,
                   v.plate_number, v.vehicle_type
            FROM logistics_trips t
            LEFT JOIN logistics_drivers d ON t.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON t.vehicle_id = v.id
            WHERE t.id = ?
        """, (id,)).fetchone()

        if not trip:
            flash('Trip not found.', 'error')
            return redirect(url_for('logistics.trips_list'))

        # Get cost entries
        costs = db.execute("""
            SELECT ce.*, u.username as created_by_name
            FROM logistics_cost_entries ce
            LEFT JOIN users u ON ce.created_by = u.id
            WHERE ce.trip_id = ?
            ORDER BY ce.created_at DESC
        """, (id,)).fetchall()

        # Get expense entries
        expenses = db.execute("""
            SELECT te.*, u.username as created_by_name
            FROM logistics_trip_expenses te
            LEFT JOIN users u ON te.created_by = u.id
            WHERE te.trip_id = ?
            ORDER BY te.created_at DESC
        """, (id,)).fetchall()

        # Calculate totals
        total_cost = sum([c['amount'] for c in costs])
        total_expense = sum([e['amount'] for e in expenses])
        estimated_cost = trip['estimated_cost'] or 0
        actual_cost = trip['actual_cost'] or 0
        fuel_cost = trip['fuel_cost'] or 0
        tolls_cost = trip['tolls_cost'] or 0
        driver_allowance = trip['driver_allowance'] or 0

        return render_template('logistics/trips/cost.html',
                             title=f'Trip {trip["trip_code"]} Costing',
                             trip=dict(trip),
                             costs=[dict(c) for c in costs],
                             expenses=[dict(e) for e in expenses],
                             total_cost=total_cost,
                             total_expense=total_expense,
                             estimated_cost=estimated_cost,
                             actual_cost=actual_cost,
                             fuel_cost=fuel_cost,
                             tolls_cost=tolls_cost,
                             driver_allowance=driver_allowance)
    finally:
        db.close()


@logistics_bp.route('/api/trips/<int:id>/status', methods=['POST'])
@logistics_login_required
def api_trips_status(id):
    """JSON API to update trip status."""
    user = get_current_user()
    db = get_db()

    try:
        trip = db.execute("SELECT * FROM logistics_trips WHERE id = ?", (id,)).fetchone()
        if not trip:
            return jsonify({'error': 'Trip not found'}), 404

        data = request.json
        new_status = data.get('status')
        reason = data.get('reason', '')

        if new_status not in TRIP_STATUSES:
            return jsonify({'error': f'Invalid status. Must be one of: {", ".join(TRIP_STATUSES)}'}), 400

        old_status = trip['status']

        db.execute("""
            UPDATE logistics_trips SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (new_status, id))

        db.commit()
        log_logistics_audit('trip', id, 'status_change', user['id'],
                           old_value=old_status, new_value=new_status)
        return jsonify({
            'success': True,
            'old_status': old_status,
            'new_status': new_status,
            'message': f'Status updated to {new_status}'
        })

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


# =============================================================================
# 4. PICKUP ORDERS
# =============================================================================

@logistics_bp.route('/pickup-orders')
@logistics_login_required
def pickup_orders_list():
    """Pickup orders list page."""
    user = get_current_user()
    db = get_db()

    try:
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        per_page = 20

        query = """
            SELECT po.*, c.name as customer_name, s.shipment_code
            FROM logistics_pickup_orders po
            LEFT JOIN sdad_customers c ON po.customer_id = c.id
            LEFT JOIN logistics_shipments s ON po.shipment_id = s.id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (po.pickup_number LIKE ? OR po.supplier_name LIKE ? OR po.contact_person LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])

        if status:
            query += " AND po.status = ?"
            params.append(status)

        query += " ORDER BY po.created_at DESC"

        count_query = query.replace("SELECT po.*, c.name as customer_name, s.shipment_code", "SELECT COUNT(*) as cnt")
        total = db.execute(count_query, params).fetchone()['cnt']

        offset = (page - 1) * per_page
        query += f" LIMIT {per_page} OFFSET {offset}"

        orders = db.execute(query, params).fetchall()

        return render_template('logistics/pickup_orders/list.html',
                             title='Pickup Orders',
                             orders=[dict(o) for o in orders],
                             search=search,
                             status=status,
                             page=page,
                             total_pages=(total + per_page - 1) // per_page,
                             total=total)
    finally:
        db.close()


@logistics_bp.route('/pickup-orders/new', methods=['GET', 'POST'])
@logistics_login_required
def pickup_orders_new():
    """Create new pickup order."""
    user = get_current_user()
    db = get_db()

    if request.method == 'POST':
        try:
            data = request.form
            pickup_number = get_next_pickup_number()

            cursor = db.execute("""
                INSERT INTO logistics_pickup_orders (
                    pickup_number, shipment_id, pickup_type, customer_id, supplier_name,
                    contact_person, contact_phone, pickup_address, scheduled_date,
                    priority, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pickup_number,
                data.get('shipment_id'),
                data.get('pickup_type', 'supplier'),
                data.get('customer_id'),
                data.get('supplier_name'),
                data.get('contact_person'),
                data.get('contact_phone'),
                data.get('pickup_address'),
                parse_date(data.get('scheduled_date')),
                data.get('priority', 'Normal'),
                data.get('notes')
            ))

            db.commit()
            flash(f'Pickup Order {pickup_number} created!', 'success')
            return redirect(url_for('logistics.pickup_orders_list'))

        except Exception as e:
            db.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            db.close()

    try:
        customers = db.execute("SELECT id, name FROM sdad_customers ORDER BY name LIMIT 500").fetchall()
        shipments = db.execute("SELECT id, shipment_code FROM logistics_shipments ORDER BY created_at DESC").fetchall()
        pickup_types = ['supplier', 'customer', 'return', 'internal', 'branch']

        return render_template('logistics/pickup_orders/new.html',
                             title='New Pickup Order',
                             order=None,
                             customers=[dict(c) for c in customers],
                             shipments=[dict(s) for s in shipments],
                             pickup_types=pickup_types)
    finally:
        db.close()


# =============================================================================
# 5. DISPATCH PLANNING
# =============================================================================

@logistics_bp.route('/dispatch')
@logistics_login_required
def dispatch_list():
    """Dispatch planning list page."""
    user = get_current_user()
    db = get_db()

    try:
        status = request.args.get('status', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')

        query = """
            SELECT dp.*, w.name as warehouse_name, u.username as approved_by_name
            FROM logistics_dispatch_plans dp
            LEFT JOIN warehouses w ON dp.warehouse_id = w.id
            LEFT JOIN users u ON dp.approved_by = u.id
            WHERE 1=1
        """
        params = []

        if status:
            query += " AND dp.status = ?"
            params.append(status)

        if date_from:
            query += " AND date(dp.plan_date) >= ?"
            params.append(date_from)

        if date_to:
            query += " AND date(dp.plan_date) <= ?"
            params.append(date_to)

        query += " ORDER BY dp.plan_date DESC"

        plans = db.execute(query, params).fetchall()

        return render_template('logistics/dispatch/list.html',
                             title='Dispatch Planning',
                             plans=[dict(p) for p in plans],
                             status=status,
                             date_from=date_from,
                             date_to=date_to)
    finally:
        db.close()


@logistics_bp.route('/dispatch/new', methods=['GET', 'POST'])
@logistics_login_required
def dispatch_new():
    """Create new dispatch plan."""
    user = get_current_user()
    db = get_db()

    if request.method == 'POST':
        try:
            data = request.form
            today = datetime.now().strftime('%Y%m%d')
            plan_code = f"DISP{today}001"

            # Check for existing plans today
            existing = db.execute(
                "SELECT plan_code FROM logistics_dispatch_plans WHERE plan_code LIKE ? ORDER BY id DESC LIMIT 1",
                (f'DISP{today}%',)
            ).fetchone()
            if existing:
                last_num = int(existing['plan_code'].replace(f'DISP{today}', ''))
                plan_code = f"DISP{today}{(last_num + 1):04d}"

            cursor = db.execute("""
                INSERT INTO logistics_dispatch_plans (
                    plan_code, plan_date, branch_id, warehouse_id, status, notes, created_at
                ) VALUES (?, ?, ?, ?, 'planned', ?, CURRENT_TIMESTAMP)
            """, (
                plan_code,
                parse_date(data.get('plan_date')) or datetime.now().date(),
                data.get('branch_id'),
                data.get('warehouse_id'),
                data.get('notes')
            ))

            db.commit()
            flash(f'Dispatch Plan {plan_code} created!', 'success')
            return redirect(url_for('logistics.dispatch_view', id=cursor.lastrowid))

        except Exception as e:
            db.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            db.close()

    try:
        warehouses = db.execute("SELECT * FROM warehouses ORDER BY name").fetchall()
        return render_template('logistics/dispatch/new.html',
                             title='New Dispatch Plan',
                             plan=None,
                             warehouses=[dict(w) for w in warehouses])
    finally:
        db.close()


@logistics_bp.route('/dispatch/view/<int:id>')
@logistics_login_required
def dispatch_view(id):
    """View dispatch plan detail."""
    user = get_current_user()
    db = get_db()

    try:
        plan = db.execute("""
            SELECT dp.*, w.name as warehouse_name
            FROM logistics_dispatch_plans dp
            LEFT JOIN warehouses w ON dp.warehouse_id = w.id
            WHERE dp.id = ?
        """, (id,)).fetchone()

        if not plan:
            flash('Dispatch plan not found.', 'error')
            return redirect(url_for('logistics.dispatch_list'))

        # Get wave details
        waves = db.execute("""
            SELECT wd.*, s.shipment_code, c.name as customer_name,
                   v.plate_number, d.full_name as driver_name
            FROM logistics_dispatch_wave_details wd
            JOIN logistics_shipments s ON wd.shipment_id = s.id
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            LEFT JOIN logistics_vehicles v ON wd.vehicle_id = v.id
            LEFT JOIN logistics_drivers d ON wd.driver_id = d.id
            WHERE wd.dispatch_plan_id = ?
            ORDER BY wd.sequence_order
        """, (id,)).fetchall()

        # Get available shipments for adding
        available = get_active_shipments_for_dispatch(warehouse_id=plan['warehouse_id'])

        return render_template('logistics/dispatch/view.html',
                             title=f"Dispatch Plan {plan['plan_code']}",
                             plan=dict(plan),
                             waves=[dict(w) for w in waves],
                             available_shipments=available)
    finally:
        db.close()


# =============================================================================
# 6. TRIP PLANNING
# =============================================================================

@logistics_bp.route('/trips')
@logistics_login_required
def trips_list():
    """Trips list page."""
    user = get_current_user()
    db = get_db()

    try:
        status = request.args.get('status', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        page = int(request.args.get('page', 1))
        per_page = 20

        query = """
            SELECT t.*, d.full_name as driver_name, v.plate_number, v.vehicle_type
            FROM delivery_trips t
            LEFT JOIN logistics_drivers d ON t.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON t.vehicle_id = v.id
            WHERE 1=1
        """
        params = []

        if status:
            query += " AND t.status = ?"
            params.append(status)

        if date_from:
            query += " AND date(t.date) >= ?"
            params.append(date_from)

        if date_to:
            query += " AND date(t.date) <= ?"
            params.append(date_to)

        query += " ORDER BY t.date DESC, t.id DESC"

        count_query = query.replace("SELECT t.*, d.full_name as driver_name, v.plate_number, v.vehicle_type", "SELECT COUNT(*) as cnt")
        total = db.execute(count_query, params).fetchone()['cnt']

        offset = (page - 1) * per_page
        query += f" LIMIT {per_page} OFFSET {offset}"

        trips = db.execute(query, params).fetchall()

        return render_template('logistics/trips/list.html',
                             title='Trips',
                             trips=[dict(t) for t in trips],
                             status=status,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             total_pages=(total + per_page - 1) // per_page,
                             total=total)
    finally:
        db.close()


@logistics_bp.route('/trips/view/<int:id>')
@logistics_login_required
def trips_view(id):
    """View trip detail."""
    user = get_current_user()
    db = get_db()

    try:
        trip = db.execute("""
            SELECT t.*, d.full_name as driver_name, d.mobile as driver_mobile,
                   v.plate_number, v.vehicle_type, v.model
            FROM delivery_trips t
            LEFT JOIN logistics_drivers d ON t.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON t.vehicle_id = v.id
            WHERE t.id = ?
        """, (id,)).fetchone()

        if not trip:
            flash('Trip not found.', 'error')
            return redirect(url_for('logistics.trips_list'))

        # Get stops
        stops = db.execute("""
            SELECT ds.*, c.name as customer_name, c.address as customer_address
            FROM delivery_stops ds
            LEFT JOIN sdad_customers c ON ds.customer_id = c.id
            WHERE ds.trip_id = ?
            ORDER BY ds.sequence_order
        """, (id,)).fetchall()

        # Get activity logs
        logs = db.execute("""
            SELECT l.*, c.name as customer_name, a.name as activity_name
            FROM delivery_activity_logs l
            LEFT JOIN sdad_customers c ON l.customer_id = c.id
            LEFT JOIN delivery_activities a ON l.activity_type = a.name
            WHERE l.trip_id = ?
            ORDER BY l.timestamp ASC
        """, (id,)).fetchall()

        return render_template('logistics/trips/view.html',
                             title=f"Trip #{trip['id']}",
                             trip=dict(trip),
                             stops=[dict(s) for s in stops],
                             logs=[dict(l) for l in logs])
    finally:
        db.close()


# =============================================================================
# 7. ROUTE PLANNING
# =============================================================================

@logistics_bp.route('/routes')
@logistics_login_required
def routes_list():
    """Routes list page."""
    user = get_current_user()
    db = get_db()

    try:
        routes = db.execute("""
            SELECT r.*,
                   (SELECT COUNT(*) FROM logistics_route_stops WHERE route_id = r.id) as stop_count
            FROM logistics_route_masters r
            WHERE r.is_active = 1
            ORDER BY r.route_name
        """).fetchall()

        return render_template('logistics/routes/list.html',
                             title='Route Planning',
                             routes=[dict(r) for r in routes])
    finally:
        db.close()


@logistics_bp.route('/routes/new', methods=['GET', 'POST'])
@logistics_login_required
def routes_new():
    """Create new route."""
    user = get_current_user()
    db = get_db()

    if request.method == 'POST':
        try:
            data = request.form
            today = datetime.now().strftime('%Y%m%d')
            route_code = f"RTE{today}001"

            existing = db.execute(
                "SELECT route_code FROM logistics_route_masters WHERE route_code LIKE ? ORDER BY id DESC LIMIT 1",
                (f'RTE{today}%',)
            ).fetchone()
            if existing:
                last_num = int(existing['route_code'].replace(f'RTE{today}', ''))
                route_code = f"RTE{today}{(last_num + 1):04d}"

            cursor = db.execute("""
                INSERT INTO logistics_route_masters (
                    route_code, route_name, description, distance_km,
                    estimated_time_minutes, cost_per_km
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                route_code,
                data.get('route_name'),
                data.get('description'),
                float(data.get('distance_km', 0)),
                int(data.get('estimated_time_minutes', 0)),
                float(data.get('cost_per_km', 0))
            ))

            route_id = cursor.lastrowid

            # Add stops
            stop_names = data.getlist('stop_name[]')
            stop_addresses = data.getlist('stop_address[]')
            stop_orders = data.getlist('stop_order[]')
            service_times = data.getlist('service_time[]')

            for i in range(len(stop_names)):
                if stop_names[i]:
                    db.execute("""
                        INSERT INTO logistics_route_stops
                        (route_id, stop_order, stop_name, address, service_time_minutes)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        route_id,
                        int(stop_orders[i]) if i < len(stop_orders) and stop_orders[i] else i + 1,
                        stop_names[i],
                        stop_addresses[i] if i < len(stop_addresses) else '',
                        int(service_times[i]) if i < len(service_times) and service_times[i] else 15
                    ))

            db.commit()
            flash(f'Route {route_code} created!', 'success')
            return redirect(url_for('logistics.routes_list'))

        except Exception as e:
            db.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            db.close()

    try:
        return render_template('logistics/routes/new.html',
                             title='New Route',
                             route=None)
    finally:
        db.close()


@logistics_bp.route('/routes/view/<int:id>')
@logistics_login_required
def routes_view(id):
    """View route detail."""
    user = get_current_user()
    db = get_db()

    try:
        route = db.execute("SELECT * FROM logistics_route_masters WHERE id = ?", (id,)).fetchone()
        if not route:
            flash('Route not found.', 'error')
            return redirect(url_for('logistics.routes_list'))

        stops = db.execute("""
            SELECT * FROM logistics_route_stops WHERE route_id = ? ORDER BY stop_order
        """, (id,)).fetchall()

        return render_template('logistics/routes/view.html',
                             title=f"Route {route['route_code']}",
                             route=dict(route),
                             stops=[dict(s) for s in stops])
    finally:
        db.close()


@logistics_bp.route('/routes/<int:id>/edit', methods=['GET', 'POST'])
@logistics_login_required
def routes_edit(id):
    """Edit route."""
    user = get_current_user()
    db = get_db()

    try:
        route = db.execute("SELECT * FROM logistics_route_masters WHERE id = ?", (id,)).fetchone()
        if not route:
            flash('Route not found.', 'error')
            return redirect(url_for('logistics.routes_list'))

        if request.method == 'POST':
            try:
                data = request.form

                db.execute("""
                    UPDATE logistics_route_masters SET
                        route_name = ?, description = ?,
                        route_type = ?, service_zone = ?,
                        vehicle_type_compatible = ?,
                        distance_km = ?, estimated_time_minutes = ?,
                        cost_per_km = ?, restriction_notes = ?,
                        is_active = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    data.get('route_name'),
                    data.get('description'),
                    data.get('route_type', 'delivery'),
                    data.get('service_zone'),
                    data.get('vehicle_type_compatible'),
                    float(data.get('distance_km', 0)),
                    int(data.get('estimated_time_minutes', 0)),
                    float(data.get('cost_per_km', 0)),
                    data.get('restriction_notes'),
                    1 if data.get('is_active') else 0,
                    id
                ))

                db.commit()
                flash('Route updated successfully!', 'success')
                return redirect(url_for('logistics.routes_view', id=id))

            except Exception as e:
                db.rollback()
                flash(f'Error updating route: {str(e)}', 'error')

        return render_template('logistics/routes/edit.html',
                             title=f'Edit Route {route["route_code"]}',
                             route=dict(route))
    finally:
        db.close()


@logistics_bp.route('/routes/<int:id>/stops', methods=['GET', 'POST'])
@logistics_login_required
def routes_stops(id):
    """Manage route stops."""
    user = get_current_user()
    db = get_db()

    try:
        route = db.execute("SELECT * FROM logistics_route_masters WHERE id = ?", (id,)).fetchone()
        if not route:
            flash('Route not found.', 'error')
            return redirect(url_for('logistics.routes_list'))

        if request.method == 'POST':
            try:
                data = request.form
                action = data.get('action')

                if action == 'add_stop':
                    max_order = db.execute(
                        "SELECT MAX(stop_order) as max_order FROM logistics_route_stops WHERE route_id = ?",
                        (id,)
                    ).fetchone()['max_order'] or 0

                    db.execute("""
                        INSERT INTO logistics_route_stops
                        (route_id, stop_order, stop_name, address, latitude, longitude,
                         estimated_arrival, estimated_departure, service_time_minutes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        id,
                        max_order + 1,
                        data.get('stop_name'),
                        data.get('address'),
                        float(data.get('latitude', 0)) or None,
                        float(data.get('longitude', 0)) or None,
                        data.get('estimated_arrival'),
                        data.get('estimated_departure'),
                        int(data.get('service_time_minutes', 15))
                    ))
                    db.commit()
                    flash('Stop added successfully!', 'success')

                elif action == 'update_stops':
                    stop_ids = data.getlist('stop_id[]')
                    stop_names = data.getlist('stop_name[]')
                    stop_addresses = data.getlist('stop_address[]')
                    stop_orders = data.getlist('stop_order[]')
                    service_times = data.getlist('service_time[]')

                    for i, stop_id in enumerate(stop_ids):
                        db.execute("""
                            UPDATE logistics_route_stops SET
                                stop_name = ?, address = ?,
                                stop_order = ?, service_time_minutes = ?
                            WHERE id = ? AND route_id = ?
                        """, (
                            stop_names[i] if i < len(stop_names) else '',
                            stop_addresses[i] if i < len(stop_addresses) else '',
                            int(stop_orders[i]) if i < len(stop_orders) and stop_orders[i] else i + 1,
                            int(service_times[i]) if i < len(service_times) and service_times[i] else 15,
                            stop_id, id
                        ))
                    db.commit()
                    flash('Stops updated successfully!', 'success')

                elif action == 'delete_stop':
                    stop_id = data.get('stop_id')
                    db.execute("DELETE FROM logistics_route_stops WHERE id = ? AND route_id = ?", (stop_id, id))
                    db.commit()
                    flash('Stop deleted successfully!', 'success')

                return redirect(url_for('logistics.routes_stops', id=id))

            except Exception as e:
                db.rollback()
                flash(f'Error managing stops: {str(e)}', 'error')

        stops = db.execute("""
            SELECT * FROM logistics_route_stops
            WHERE route_id = ?
            ORDER BY stop_order
        """, (id,)).fetchall()

        return render_template('logistics/routes/stops.html',
                             title=f'Route {route["route_code"]} - Stops',
                             route=dict(route),
                             stops=[dict(s) for s in stops])
    finally:
        db.close()


@logistics_bp.route('/routes/<int:id>/duplicate', methods=['POST'])
@logistics_login_required
def routes_duplicate(id):
    """Duplicate route as template."""
    user = get_current_user()
    db = get_db()

    try:
        route = db.execute("SELECT * FROM logistics_route_masters WHERE id = ?", (id,)).fetchone()
        if not route:
            flash('Route not found.', 'error')
            return redirect(url_for('logistics.routes_list'))

        new_route_code = get_next_route_code()

        cursor = db.execute("""
            INSERT INTO logistics_route_masters
            (route_code, route_name, description, route_type, service_zone,
             vehicle_type_compatible, distance_km, estimated_time_minutes,
             cost_per_km, restriction_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            new_route_code,
            f"{route['route_name']} (Copy)",
            route['description'],
            route['route_type'],
            route.get('service_zone'),
            route.get('vehicle_type_compatible'),
            route['distance_km'],
            route['estimated_time_minutes'],
            route['cost_per_km'],
            route.get('restriction_notes')
        ))

        new_route_id = cursor.lastrowid

        # Copy stops
        stops = db.execute("SELECT * FROM logistics_route_stops WHERE route_id = ?", (id,)).fetchall()
        for stop in stops:
            db.execute("""
                INSERT INTO logistics_route_stops
                (route_id, stop_order, stop_name, address, latitude, longitude,
                 estimated_arrival, estimated_departure, service_time_minutes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                new_route_id, stop['stop_order'], stop['stop_name'],
                stop['address'], stop['latitude'], stop['longitude'],
                stop['estimated_arrival'], stop['estimated_departure'],
                stop['service_time_minutes']
            ))

        db.commit()
        flash(f'Route duplicated as {new_route_code}!', 'success')
        return redirect(url_for('logistics.routes_view', id=new_route_id))

    except Exception as e:
        db.rollback()
        flash(f'Error duplicating route: {str(e)}', 'error')
        return redirect(url_for('logistics.routes_list'))
    finally:
        db.close()


@logistics_bp.route('/routes/library')
@logistics_login_required
def routes_library():
    """Route library view with all routes."""
    user = get_current_user()
    db = get_db()

    try:
        search = request.args.get('search', '').strip()
        route_type = request.args.get('route_type', '')
        service_zone = request.args.get('service_zone', '')

        query = """
            SELECT r.*,
                   (SELECT COUNT(*) FROM logistics_route_stops WHERE route_id = r.id) as stop_count,
                   (SELECT COUNT(*) FROM logistics_trips WHERE route_id = r.id AND status IN ('completed', 'partially_completed')) as trip_count
            FROM logistics_route_masters r
            WHERE r.is_active = 1
        """
        params = []

        if search:
            query += " AND (r.route_code LIKE ? OR r.route_name LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param])

        if route_type:
            query += " AND r.route_type = ?"
            params.append(route_type)

        if service_zone:
            query += " AND r.service_zone = ?"
            params.append(service_zone)

        query += " ORDER BY r.route_name"

        routes = db.execute(query, params).fetchall()

        # Get unique service zones
        zones = db.execute("SELECT DISTINCT service_zone FROM logistics_route_masters WHERE service_zone IS NOT NULL AND service_zone != ''").fetchall()

        return render_template('logistics/routes/library.html',
                             title='Route Library',
                             routes=[dict(r) for r in routes],
                             zones=[z['service_zone'] for z in zones],
                             search=search,
                             route_type=route_type,
                             service_zone=service_zone)
    finally:
        db.close()


@logistics_bp.route('/routes/templates')
@logistics_login_required
def routes_templates():
    """Route templates view."""
    user = get_current_user()
    db = get_db()

    try:
        templates = db.execute("""
            SELECT rt.*, u.username as created_by_name
            FROM logistics_route_templates rt
            LEFT JOIN users u ON rt.created_by = u.id
            WHERE rt.is_active = 1
            ORDER BY rt.template_name
        """).fetchall()

        return render_template('logistics/routes/templates.html',
                             title='Route Templates',
                             templates=[dict(t) for t in templates])
    finally:
        db.close()


@logistics_bp.route('/routes/optimization')
@logistics_login_required
def routes_optimization():
    """Route optimization rules."""
    user = get_current_user()
    db = get_db()

    try:
        rules = db.execute("""
            SELECT * FROM logistics_route_optimization_rules
            WHERE is_active = 1
            ORDER BY priority DESC, rule_name
        """).fetchall()

        return render_template('logistics/routes/optimization.html',
                             title='Route Optimization Rules',
                             rules=[dict(r) for r in rules])
    finally:
        db.close()


@logistics_bp.route('/routes/zones', methods=['GET', 'POST'])
@logistics_login_required
def routes_zones():
    """Service zones management."""
    user = get_current_user()
    db = get_db()

    try:
        if request.method == 'POST':
            try:
                data = request.form
                action = data.get('action')

                if action == 'add_zone':
                    zone_code = f"ZONE{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    db.execute("""
                        INSERT INTO logistics_service_zones
                        (zone_code, zone_name, zone_type, description, city, state, country, postal_code)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        zone_code,
                        data.get('zone_name'),
                        data.get('zone_type', 'service'),
                        data.get('description'),
                        data.get('city'),
                        data.get('state'),
                        data.get('country'),
                        data.get('postal_code')
                    ))
                    db.commit()
                    flash('Service zone added successfully!', 'success')

                elif action == 'update_zone':
                    zone_id = data.get('zone_id')
                    db.execute("""
                        UPDATE logistics_service_zones SET
                            zone_name = ?, zone_type = ?, description = ?,
                            city = ?, state = ?, country = ?, postal_code = ?
                        WHERE id = ?
                    """, (
                        data.get('zone_name'),
                        data.get('zone_type', 'service'),
                        data.get('description'),
                        data.get('city'),
                        data.get('state'),
                        data.get('country'),
                        data.get('postal_code'),
                        zone_id
                    ))
                    db.commit()
                    flash('Service zone updated successfully!', 'success')

                elif action == 'delete_zone':
                    zone_id = data.get('zone_id')
                    db.execute("DELETE FROM logistics_service_zones WHERE id = ?", (zone_id,))
                    db.commit()
                    flash('Service zone deleted successfully!', 'success')

                return redirect(url_for('logistics.routes_zones'))

            except Exception as e:
                db.rollback()
                flash(f'Error managing zone: {str(e)}', 'error')

        zones = db.execute("SELECT * FROM logistics_service_zones WHERE is_active = 1 ORDER BY zone_name").fetchall()

        return render_template('logistics/routes/zones.html',
                             title='Service Zones',
                             zones=[dict(z) for z in zones])
    finally:
        db.close()


@logistics_bp.route('/routes/performance')
@logistics_login_required
def routes_performance():
    """Route performance dashboard."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        # Get route performance metrics
        route_stats = db.execute("""
            SELECT
                r.id, r.route_code, r.route_name, r.route_type,
                COUNT(DISTINCT t.id) as total_trips,
                SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_trips,
                SUM(CASE WHEN t.status = 'partially_completed' THEN 1 ELSE 0 END) as partially_completed,
                SUM(CASE WHEN t.status = 'failed' THEN 1 ELSE 0 END) as failed_trips,
                SUM(ts.actual_arrival IS NOT NULL) as stops_completed,
                AVG(t.distance_km) as avg_distance,
                AVG(t.actual_cost) as avg_cost
            FROM logistics_route_masters r
            LEFT JOIN logistics_trips t ON r.id = t.route_id
                AND date(t.planned_departure) BETWEEN ? AND ?
            LEFT JOIN logistics_trip_stops ts ON t.id = ts.trip_id AND ts.status = 'completed'
            WHERE r.is_active = 1
            GROUP BY r.id
            ORDER BY total_trips DESC
        """, (date_from, date_to)).fetchall()

        # Get overall stats
        total_trips = sum([r['total_trips'] for r in route_stats])
        total_completed = sum([r['completed_trips'] for r in route_stats])
        completion_rate = round((total_completed / total_trips * 100) if total_trips > 0 else 0, 1)

        return render_template('logistics/routes/performance.html',
                             title='Route Performance',
                             route_stats=[dict(r) for r in route_stats],
                             total_trips=total_trips,
                             total_completed=total_completed,
                             completion_rate=completion_rate,
                             date_from=date_from,
                             date_to=date_to)
    finally:
        db.close()


@logistics_bp.route('/api/routes/<int:id>/stops', methods=['GET'])
@logistics_login_required
def api_routes_stops(id):
    """JSON API for route stops."""
    user = get_current_user()
    db = get_db()

    try:
        stops = db.execute("""
            SELECT * FROM logistics_route_stops
            WHERE route_id = ? AND is_active = 1
            ORDER BY stop_order
        """, (id,)).fetchall()

        return jsonify({
            'success': True,
            'stops': [dict(s) for s in stops],
            'count': len(stops)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


# =============================================================================
# 8a. STOP MANAGEMENT
# =============================================================================

@logistics_bp.route('/stops')
@logistics_login_required
def stops_list():
    """All delivery stops across trips."""
    user = get_current_user()
    db = get_db()

    try:
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        page = int(request.args.get('page', 1))
        per_page = 25

        query = """
            SELECT ts.*, t.trip_code, t.status as trip_status,
                   c.name as customer_name
            FROM logistics_trip_stops ts
            LEFT JOIN logistics_trips t ON ts.trip_id = t.id
            LEFT JOIN sdad_customers c ON ts.customer_id = c.id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (ts.stop_name LIKE ? OR ts.address LIKE ? OR c.name LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])

        if status:
            query += " AND ts.status = ?"
            params.append(status)

        if date_from:
            query += " AND date(ts.planned_arrival) >= ?"
            params.append(date_from)

        if date_to:
            query += " AND date(ts.planned_arrival) <= ?"
            params.append(date_to)

        query += " ORDER BY ts.planned_arrival DESC"

        count_query = query.replace("SELECT ts.*, t.trip_code, t.status as trip_status,\n                   c.name as customer_name", "SELECT COUNT(*) as cnt")
        total = db.execute(count_query, params).fetchone()['cnt']

        offset = (page - 1) * per_page
        query += f" LIMIT {per_page} OFFSET {offset}"

        stops = db.execute(query, params).fetchall()

        return render_template('logistics/stops/list.html',
                             title='All Stops',
                             stops=[dict(s) for s in stops],
                             status=status,
                             search=search,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             total_pages=(total + per_page - 1) // per_page if per_page > 0 else 1,
                             total=total)
    finally:
        db.close()


@logistics_bp.route('/stops/<int:id>/checkin', methods=['GET', 'POST'])
@logistics_login_required
def stops_checkin(id):
    """Mark stop as arrived/checked-in."""
    user = get_current_user()
    db = get_db()

    try:
        stop = db.execute("SELECT * FROM logistics_trip_stops WHERE id = ?", (id,)).fetchone()
        if not stop:
            flash('Stop not found.', 'error')
            return redirect(url_for('logistics.stops_list'))

        if request.method == 'POST':
            try:
                data = request.form

                db.execute("""
                    UPDATE logistics_trip_stops SET
                        actual_arrival = CURRENT_TIMESTAMP,
                        status = 'arrived',
                        notes = COALESCE(notes, '') || ? || ?
                        WHERE id = ?
                """, (f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Checked in by {user['username']}: ",
                      data.get('notes', ''), id))

                db.commit()
                log_logistics_audit('stop', id, 'checkin', user['id'])
                flash('Stop checked in successfully!', 'success')
                return redirect(url_for('logistics.trips_timeline', id=stop['trip_id']))

            except Exception as e:
                db.rollback()
                flash(f'Error checking in: {str(e)}', 'error')

        return render_template('logistics/stops/checkin.html',
                             title='Check In',
                             stop=dict(stop))
    finally:
        db.close()


@logistics_bp.route('/stops/<int:id>/checkout', methods=['POST'])
@logistics_login_required
def stops_checkout(id):
    """Mark stop as departed."""
    user = get_current_user()
    db = get_db()

    try:
        stop = db.execute("SELECT * FROM logistics_trip_stops WHERE id = ?", (id,)).fetchone()
        if not stop:
            return jsonify({'error': 'Stop not found'}), 404

        db.execute("""
            UPDATE logistics_trip_stops SET
                actual_departure = CURRENT_TIMESTAMP,
                status = 'completed'
            WHERE id = ?
        """, (id,))

        db.commit()
        log_logistics_audit('stop', id, 'checkout', user['id'])
        return jsonify({'success': True, 'message': 'Stop checked out successfully'})

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@logistics_bp.route('/stops/<int:id>/complete', methods=['POST'])
@logistics_login_required
def stops_complete(id):
    """Mark stop delivered."""
    user = get_current_user()
    db = get_db()

    try:
        stop = db.execute("SELECT * FROM logistics_trip_stops WHERE id = ?", (id,)).fetchone()
        if not stop:
            return jsonify({'error': 'Stop not found'}), 404

        data = request.json if request.is_json else request.form

        db.execute("""
            UPDATE logistics_trip_stops SET
                actual_arrival = COALESCE(actual_arrival, CURRENT_TIMESTAMP),
                actual_departure = CURRENT_TIMESTAMP,
                status = 'completed',
                receiver_name = ?,
                receiver_signature = ?,
                proof_of_delivery = ?,
                notes = COALESCE(notes, '') || ? || ?
            WHERE id = ?
        """, (
            data.get('receiver_name'),
            data.get('receiver_signature'),
            data.get('proof_of_delivery'),
            f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Completed by {user['username']}: ",
            data.get('notes', ''),
            id
        ))

        db.commit()
        log_logistics_audit('stop', id, 'complete', user['id'])
        return jsonify({'success': True, 'message': 'Stop marked as delivered'})

    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        db.close()


@logistics_bp.route('/stops/<int:id>/fail', methods=['GET', 'POST'])
@logistics_login_required
def stops_fail(id):
    """Mark stop as failed with reason."""
    user = get_current_user()
    db = get_db()

    try:
        stop = db.execute("SELECT * FROM logistics_trip_stops WHERE id = ?", (id,)).fetchone()
        if not stop:
            flash('Stop not found.', 'error')
            return redirect(url_for('logistics.stops_list'))

        if request.method == 'POST':
            try:
                data = request.form

                db.execute("""
                    UPDATE logistics_trip_stops SET
                        status = 'failed',
                        failure_reason = ?,
                        notes = COALESCE(notes, '') || ? || ?
                    WHERE id = ?
                """, (
                    data.get('failure_reason'),
                    f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Failed by {user['username']}: ",
                    data.get('notes', ''),
                    id
                ))

                db.commit()
                log_logistics_audit('stop', id, 'fail', user['id'], new_value=data.get('failure_reason'))
                flash('Stop marked as failed.', 'warning')
                return redirect(url_for('logistics.trips_timeline', id=stop['trip_id']))

            except Exception as e:
                db.rollback()
                flash(f'Error marking stop as failed: {str(e)}', 'error')

        return render_template('logistics/stops/fail.html',
                             title='Mark Stop Failed',
                             stop=dict(stop))
    finally:
        db.close()


@logistics_bp.route('/stops/sequence')
@logistics_login_required
def stops_sequence():
    """Stop sequence management."""
    user = get_current_user()
    db = get_db()

    try:
        trip_id = request.args.get('trip_id', '')

        if trip_id:
            trip = db.execute("SELECT * FROM logistics_trips WHERE id = ?", (trip_id,)).fetchone()
            if trip:
                stops = db.execute("""
                    SELECT * FROM logistics_trip_stops
                    WHERE trip_id = ?
                    ORDER BY sequence_order
                """, (trip_id,)).fetchall()
            else:
                stops = []
        else:
            stops = []
            trip = None

        return render_template('logistics/stops/sequence.html',
                             title='Stop Sequence',
                             stops=[dict(s) for s in stops] if stops else [],
                             trip=dict(trip) if trip else None,
                             trip_id=trip_id)
    finally:
        db.close()


@logistics_bp.route('/stops/checkpoints')
@logistics_login_required
def stops_checkpoints():
    """Arrival/departure logs."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        checkpoints = db.execute("""
            SELECT
                ts.id, ts.stop_name, ts.actual_arrival, ts.actual_departure,
                ts.status, t.trip_code, t.id as trip_id,
                ts.failure_reason
            FROM logistics_trip_stops ts
            JOIN logistics_trips t ON ts.trip_id = t.id
            WHERE date(ts.actual_arrival) BETWEEN ? AND ?
               OR date(ts.actual_departure) BETWEEN ? AND ?
            ORDER BY ts.actual_arrival DESC
        """, (date_from, date_to, date_from, date_to)).fetchall()

        return render_template('logistics/stops/checkpoints.html',
                             title='Stop Checkpoints',
                             checkpoints=[dict(c) for c in checkpoints],
                             date_from=date_from,
                             date_to=date_to)
    finally:
        db.close()


@logistics_bp.route('/stops/<int:id>/view')
@logistics_login_required
def stops_view(id):
    """View stop detail."""
    user = get_current_user()
    db = get_db()

    try:
        stop = db.execute("""
            SELECT ts.*, t.trip_code, t.status as trip_status,
                   c.name as customer_name, c.address as customer_address
            FROM logistics_trip_stops ts
            LEFT JOIN logistics_trips t ON ts.trip_id = t.id
            LEFT JOIN sdad_customers c ON ts.customer_id = c.id
            WHERE ts.id = ?
        """, (id,)).fetchone()

        if not stop:
            flash('Stop not found.', 'error')
            return redirect(url_for('logistics.stops_list'))

        return render_template('logistics/stops/view.html',
                             title=f'Stop: {stop["stop_name"]}',
                             stop=dict(stop))
    finally:
        db.close()


# =============================================================================
# 8. FLEET MANAGEMENT (VEHICLES) - EXTENDED
# =============================================================================

@logistics_bp.route('/vehicles/<int:id>/documents')
@logistics_login_required
def vehicles_documents(id):
    """Vehicle document management."""
    user = get_current_user()
    db = get_db()

    try:
        vehicle = db.execute("SELECT * FROM logistics_vehicles WHERE id = ?", (id,)).fetchone()
        if not vehicle:
            flash('Vehicle not found.', 'error')
            return redirect(url_for('logistics.vehicles_list'))

        docs = db.execute("""
            SELECT * FROM logistics_vehicle_documents
            WHERE vehicle_id = ? ORDER BY expiry_date
        """, (id,)).fetchall()

        if request.method == 'POST':
            try:
                data = request.form
                db.execute("""
                    INSERT INTO logistics_vehicle_documents (
                        vehicle_id, document_type, document_number,
                        issue_date, expiry_date, file_path, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    id,
                    data.get('document_type'),
                    data.get('document_number'),
                    parse_date(data.get('issue_date')),
                    parse_date(data.get('expiry_date')),
                    data.get('file_path'),
                    data.get('notes')
                ))
                db.commit()
                flash('Document added successfully!', 'success')
                return redirect(url_for('logistics.vehicles_documents', id=id))
            except Exception as e:
                db.rollback()
                flash(f'Error: {str(e)}', 'error')

        doc_types = ['Registration', 'Insurance', 'Permit', 'Fitness Certificate',
                      'Pollution Certificate', 'Road Tax', 'Other']

        return render_template('logistics/vehicles/documents.html',
                             title=f"Vehicle Documents - {vehicle['plate_number']}",
                             vehicle=dict(vehicle),
                             docs=[dict(d) for d in docs],
                             doc_types=doc_types)
    finally:
        db.close()


@logistics_bp.route('/vehicles/<int:id>/service-history', methods=['GET', 'POST'])
@logistics_login_required
def vehicles_service_history(id):
    """Vehicle service history."""
    user = get_current_user()
    db = get_db()

    try:
        vehicle = db.execute("SELECT * FROM logistics_vehicles WHERE id = ?", (id,)).fetchone()
        if not vehicle:
            flash('Vehicle not found.', 'error')
            return redirect(url_for('logistics.vehicles_list'))

        maintenance = db.execute("""
            SELECT * FROM logistics_vehicle_maintenance
            WHERE vehicle_id = ? ORDER BY scheduled_date DESC
        """, (id,)).fetchall()

        if request.method == 'POST':
            try:
                data = request.form
                db.execute("""
                    INSERT INTO logistics_vehicle_maintenance (
                        vehicle_id, maintenance_type, description,
                        scheduled_date, completed_date, odometer_reading,
                        cost, service_provider, next_service_date,
                        next_service_km, status, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    id,
                    data.get('maintenance_type'),
                    data.get('description'),
                    parse_date(data.get('scheduled_date')),
                    parse_date(data.get('completed_date')),
                    float(data.get('odometer_reading', 0)),
                    float(data.get('cost', 0)),
                    data.get('service_provider'),
                    parse_date(data.get('next_service_date')),
                    float(data.get('next_service_km', 0)),
                    data.get('status', 'pending'),
                    data.get('notes')
                ))
                db.commit()
                flash('Service record added!', 'success')
                return redirect(url_for('logistics.vehicles_service_history', id=id))
            except Exception as e:
                db.rollback()
                flash(f'Error: {str(e)}', 'error')

        maint_types = ['Routine Service', 'Oil Change', 'Tire Replacement',
                        'Brake Service', 'Engine Repair', 'Transmission',
                        'Electrical', 'Body Work', 'Annual Inspection', 'Other']

        return render_template('logistics/vehicles/service_history.html',
                             title=f"Service History - {vehicle['plate_number']}",
                             vehicle=dict(vehicle),
                             maintenance=[dict(m) for m in maintenance],
                             maint_types=maint_types)
    finally:
        db.close()


@logistics_bp.route('/vehicles/<int:id>/utilization')
@logistics_login_required
def vehicles_utilization(id):
    """Vehicle utilization metrics."""
    user = get_current_user()
    db = get_db()

    try:
        vehicle = db.execute("SELECT * FROM logistics_vehicles WHERE id = ?", (id,)).fetchone()
        if not vehicle:
            flash('Vehicle not found.', 'error')
            return redirect(url_for('logistics.vehicles_list'))

        date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        # Trip count and distance
        trip_stats = db.execute("""
            SELECT COUNT(*) as total_trips,
                   SUM(distance_km) as total_distance,
                   AVG(distance_km) as avg_distance
            FROM delivery_trips
            WHERE vehicle_id = ? AND date(date) BETWEEN ? AND ?
        """, (id, date_from, date_to)).fetchone()

        # Shipment stats
        shipment_stats = db.execute("""
            SELECT COUNT(*) as total_deliveries,
                   SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as successful,
                   SUM(CASE WHEN status = 'failed_delivery' THEN 1 ELSE 0 END) as failed
            FROM logistics_shipments
            WHERE vehicle_id = ? AND date(created_at) BETWEEN ? AND ?
        """, (id, date_from, date_to)).fetchone()

        # Fuel consumption estimate
        fuel_stats = db.execute("""
            SELECT SUM(c.amount) as total_fuel_cost
            FROM logistics_cost_entries c
            WHERE c.trip_id IN (SELECT id FROM delivery_trips WHERE vehicle_id = ?)
            AND c.cost_type = 'Fuel'
            AND date(c.created_at) BETWEEN ? AND ?
        """, (id, date_from, date_to)).fetchone()

        # Recent trips
        recent_trips = db.execute("""
            SELECT t.*, d.full_name as driver_name
            FROM delivery_trips t
            LEFT JOIN logistics_drivers d ON t.driver_id = d.id
            WHERE t.vehicle_id = ?
            ORDER BY t.date DESC LIMIT 20
        """, (id,)).fetchall()

        return render_template('logistics/vehicles/utilization.html',
                             title=f"Utilization - {vehicle['plate_number']}",
                             vehicle=dict(vehicle),
                             date_from=date_from,
                             date_to=date_to,
                             trip_stats=dict(trip_stats) if trip_stats else {},
                             shipment_stats=dict(shipment_stats) if shipment_stats else {},
                             fuel_stats=dict(fuel_stats) if fuel_stats else {},
                             recent_trips=[dict(t) for t in recent_trips])
    finally:
        db.close()


@logistics_bp.route('/vehicles/categories')
@logistics_login_required
def vehicles_categories():
    """Vehicle categories management."""
    db = get_db()

    try:
        categories = db.execute("""
            SELECT v.vehicle_category, v.vehicle_type, COUNT(*) as count
            FROM logistics_vehicles v
            WHERE v.vehicle_category IS NOT NULL
            GROUP BY v.vehicle_category, v.vehicle_type
            ORDER BY v.vehicle_category
        """).fetchall()

        return render_template('logistics/vehicles/categories.html',
                             title='Vehicle Categories',
                             categories=[dict(c) for c in categories])
    finally:
        db.close()


@logistics_bp.route('/vehicles/fuel-tracking')
@logistics_login_required
def vehicles_fuel_tracking():
    """Fuel tracking for all vehicles."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        fuel_entries = db.execute("""
            SELECT c.*, v.plate_number, v.vehicle_code,
                   t.trip_code, u.username
            FROM logistics_cost_entries c
            LEFT JOIN logistics_shipments s ON c.shipment_id = s.id
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            LEFT JOIN delivery_trips t ON c.trip_id = t.id
            LEFT JOIN users u ON c.created_by = u.id
            WHERE c.cost_type = 'Fuel'
            AND date(c.created_at) BETWEEN ? AND ?
            ORDER BY c.created_at DESC
        """, (date_from, date_to)).fetchall()

        total_fuel = db.execute("""
            SELECT SUM(c.amount) as total
            FROM logistics_cost_entries c
            WHERE c.cost_type = 'Fuel'
            AND date(c.created_at) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['total'] or 0

        return render_template('logistics/vehicles/fuel_tracking.html',
                             title='Fuel Tracking',
                             fuel_entries=[dict(f) for f in fuel_entries],
                             date_from=date_from,
                             date_to=date_to,
                             total_fuel=total_fuel)
    finally:
        db.close()


@logistics_bp.route('/vehicles/<int:id>/telematics')
@logistics_login_required
def vehicles_telematics(id):
    """Telematics data scaffold."""
    user = get_current_user()
    db = get_db()

    try:
        vehicle = db.execute("SELECT * FROM logistics_vehicles WHERE id = ?", (id,)).fetchone()
        if not vehicle:
            flash('Vehicle not found.', 'error')
            return redirect(url_for('logistics.vehicles_list'))

        # Get last known location from recent POD
        last_location = db.execute("""
            SELECT latitude, longitude, delivery_timestamp
            FROM logistics_pod_records
            WHERE latitude IS NOT NULL AND longitude IS NOT NULL
            ORDER BY delivery_timestamp DESC LIMIT 1
        """).fetchone()

        return render_template('logistics/vehicles/telematics.html',
                             title=f"Telematics - {vehicle['plate_number']}",
                             vehicle=dict(vehicle),
                             last_location=dict(last_location) if last_location else None)
    finally:
        db.close()


@logistics_bp.route('/vehicles/<int:id>/maintenance/new', methods=['GET', 'POST'])
@logistics_login_required
def vehicles_maintenance_new(id):
    """Add new maintenance record for vehicle."""
    user = get_current_user()
    db = get_db()

    try:
        vehicle = db.execute("SELECT * FROM logistics_vehicles WHERE id = ?", (id,)).fetchone()
        if not vehicle:
            flash('Vehicle not found.', 'error')
            return redirect(url_for('logistics.vehicles_list'))

        if request.method == 'POST':
            try:
                data = request.form
                db.execute("""
                    INSERT INTO logistics_vehicle_maintenance (
                        vehicle_id, maintenance_type, description,
                        scheduled_date, cost, service_provider,
                        next_service_date, status, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    id,
                    data.get('maintenance_type'),
                    data.get('description'),
                    parse_date(data.get('scheduled_date')),
                    float(data.get('cost', 0)),
                    data.get('service_provider'),
                    parse_date(data.get('next_service_date')),
                    data.get('status', 'pending'),
                    data.get('notes')
                ))
                db.commit()
                flash('Maintenance record added!', 'success')
                return redirect(url_for('logistics.vehicles_service_history', id=id))
            except Exception as e:
                db.rollback()
                flash(f'Error: {str(e)}', 'error')

        maint_types = ['Routine Service', 'Oil Change', 'Tire Replacement',
                        'Brake Service', 'Engine Repair', 'Other']
        return redirect(url_for('logistics.vehicles_service_history', id=id))
    finally:
        db.close()


# =============================================================================
# 8. FLEET MANAGEMENT (VEHICLES)
# =============================================================================

@logistics_bp.route('/vehicles')
@logistics_login_required
def vehicles_list():
    """Vehicles list page."""
    user = get_current_user()
    db = get_db()

    try:
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '')
        vehicle_type = request.args.get('vehicle_type', '')

        query = """
            SELECT v.*, d.full_name as assigned_driver_name
            FROM logistics_vehicles v
            LEFT JOIN logistics_drivers d ON v.assigned_driver_id = d.id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (v.plate_number LIKE ? OR v.vehicle_code LIKE ? OR v.fleet_number LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])

        if status:
            query += " AND v.status = ?"
            params.append(status)

        if vehicle_type:
            query += " AND v.vehicle_type = ?"
            params.append(vehicle_type)

        query += " ORDER BY v.plate_number"

        vehicles = db.execute(query, params).fetchall()
        vehicle_types = db.execute("SELECT setting_value FROM logistics_settings WHERE category = 'Vehicle Types' AND is_active = 1").fetchall()

        return render_template('logistics/vehicles/list.html',
                             title='Fleet Management',
                             vehicles=[dict(v) for v in vehicles],
                             search=search,
                             status=status,
                             vehicle_type=vehicle_type,
                             vehicle_types=[vt['setting_value'] for vt in vehicle_types])
    finally:
        db.close()


@logistics_bp.route('/vehicles/new', methods=['GET', 'POST'])
@logistics_login_required
def vehicles_new():
    """Create new vehicle."""
    user = get_current_user()
    db = get_db()

    if request.method == 'POST':
        try:
            data = request.form
            today = datetime.now().strftime('%Y%m%d')
            vehicle_code = f"VEH{today}001"

            existing = db.execute(
                "SELECT vehicle_code FROM logistics_vehicles WHERE vehicle_code LIKE ? ORDER BY id DESC LIMIT 1",
                (f'VEH{today}%',)
            ).fetchone()
            if existing:
                last_num = int(existing['vehicle_code'].replace(f'VEH{today}', ''))
                vehicle_code = f"VEH{today}{(last_num + 1):04d}"

            cursor = db.execute("""
                INSERT INTO logistics_vehicles (
                    vehicle_code, plate_number, fleet_number, vehicle_type, vehicle_category,
                    company_id, branch_id, brand, model, year, vin_number, fuel_type,
                    load_capacity_kg, load_capacity_volume, pallet_capacity, carton_capacity,
                    status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                vehicle_code,
                data.get('plate_number'),
                data.get('fleet_number'),
                data.get('vehicle_type'),
                data.get('vehicle_category'),
                data.get('company_id') or user.get('company_id'),
                data.get('branch_id'),
                data.get('brand'),
                data.get('model'),
                data.get('year'),
                data.get('vin_number'),
                data.get('fuel_type', 'diesel'),
                float(data.get('load_capacity_kg', 0)),
                float(data.get('load_capacity_volume', 0)),
                int(data.get('pallet_capacity', 0)),
                int(data.get('carton_capacity', 0)),
                data.get('status', 'active'),
                data.get('notes')
            ))

            db.commit()
            flash(f'Vehicle {vehicle_code} created!', 'success')
            return redirect(url_for('logistics.vehicles_view', id=cursor.lastrowid))

        except Exception as e:
            db.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            db.close()

    try:
        vehicle_types = db.execute("SELECT setting_value FROM logistics_settings WHERE category = 'Vehicle Types' AND is_active = 1").fetchall()
        fuel_types = ['diesel', 'petrol', 'electric', 'hybrid', 'gas', 'lpg']

        return render_template('logistics/vehicles/new.html',
                             title='New Vehicle',
                             vehicle=None,
                             vehicle_types=[vt['setting_value'] for vt in vehicle_types],
                             fuel_types=fuel_types)
    finally:
        db.close()


@logistics_bp.route('/vehicles/view/<int:id>')
@logistics_login_required
def vehicles_view(id):
    """View vehicle detail."""
    user = get_current_user()
    db = get_db()

    try:
        vehicle = db.execute("""
            SELECT v.*, d.full_name as assigned_driver_name
            FROM logistics_vehicles v
            LEFT JOIN logistics_drivers d ON v.assigned_driver_id = d.id
            WHERE v.id = ?
        """, (id,)).fetchone()

        if not vehicle:
            flash('Vehicle not found.', 'error')
            return redirect(url_for('logistics.vehicles_list'))

        # Get documents
        docs = db.execute("""
            SELECT * FROM logistics_vehicle_documents WHERE vehicle_id = ? ORDER BY expiry_date
        """, (id,)).fetchall()

        # Get maintenance records
        maintenance = db.execute("""
            SELECT * FROM logistics_vehicle_maintenance WHERE vehicle_id = ?
            ORDER BY scheduled_date DESC LIMIT 20
        """, (id,)).fetchall()

        # Get recent trips
        trips = db.execute("""
            SELECT * FROM delivery_trips WHERE vehicle_id = ?
            ORDER BY date DESC LIMIT 10
        """, (id,)).fetchall()

        return render_template('logistics/vehicles/view.html',
                             title=f"Vehicle {vehicle['plate_number']}",
                             vehicle=dict(vehicle),
                             docs=[dict(d) for d in docs],
                             maintenance=[dict(m) for m in maintenance],
                             trips=[dict(t) for t in trips])
    finally:
        db.close()


@logistics_bp.route('/vehicles/edit/<int:id>', methods=['GET', 'POST'])
@logistics_login_required
def vehicles_edit(id):
    """Edit vehicle."""
    user = get_current_user()
    db = get_db()

    try:
        vehicle = db.execute("SELECT * FROM logistics_vehicles WHERE id = ?", (id,)).fetchone()
        if not vehicle:
            flash('Vehicle not found.', 'error')
            return redirect(url_for('logistics.vehicles_list'))

        if request.method == 'POST':
            try:
                data = request.form

                db.execute("""
                    UPDATE logistics_vehicles SET
                        plate_number = ?, fleet_number = ?, vehicle_type = ?,
                        vehicle_category = ?, brand = ?, model = ?, year = ?,
                        vin_number = ?, fuel_type = ?, load_capacity_kg = ?,
                        load_capacity_volume = ?, pallet_capacity = ?, carton_capacity = ?,
                        status = ?, assigned_driver_id = ?, notes = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    data.get('plate_number'),
                    data.get('fleet_number'),
                    data.get('vehicle_type'),
                    data.get('vehicle_category'),
                    data.get('brand'),
                    data.get('model'),
                    data.get('year'),
                    data.get('vin_number'),
                    data.get('fuel_type'),
                    float(data.get('load_capacity_kg', 0)),
                    float(data.get('load_capacity_volume', 0)),
                    int(data.get('pallet_capacity', 0)),
                    int(data.get('carton_capacity', 0)),
                    data.get('status'),
                    data.get('assigned_driver_id'),
                    data.get('notes'),
                    id
                ))

                db.commit()
                flash('Vehicle updated!', 'success')
                return redirect(url_for('logistics.vehicles_view', id=id))

            except Exception as e:
                db.rollback()
                flash(f'Error: {str(e)}', 'error')

        drivers = db.execute("SELECT id, full_name FROM logistics_drivers WHERE status = 'active' ORDER BY full_name").fetchall()
        vehicle_types = db.execute("SELECT setting_value FROM logistics_settings WHERE category = 'Vehicle Types' AND is_active = 1").fetchall()
        fuel_types = ['diesel', 'petrol', 'electric', 'hybrid', 'gas', 'lpg']

        return render_template('logistics/vehicles/edit.html',
                             title=f"Edit Vehicle {vehicle['plate_number']}",
                             vehicle=dict(vehicle),
                             drivers=[dict(d) for d in drivers],
                             vehicle_types=[vt['setting_value'] for vt in vehicle_types],
                             fuel_types=fuel_types)
    finally:
        db.close()


# =============================================================================
# 9. DRIVER MANAGEMENT
# =============================================================================

@logistics_bp.route('/drivers')
@logistics_login_required
def drivers_list():
    """Drivers list page."""
    user = get_current_user()
    db = get_db()

    try:
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '')
        availability = request.args.get('availability', '')

        query = """
            SELECT d.*, v.plate_number as assigned_vehicle
            FROM logistics_drivers d
            LEFT JOIN logistics_vehicles v ON d.assigned_vehicle_id = v.id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (d.full_name LIKE ? OR d.driver_code LIKE ? OR d.mobile LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])

        if status:
            query += " AND d.status = ?"
            params.append(status)

        if availability:
            query += " AND d.availability = ?"
            params.append(availability)

        query += " ORDER BY d.full_name"

        drivers = db.execute(query, params).fetchall()

        return render_template('logistics/drivers/list.html',
                             title='Driver Management',
                             drivers=[dict(d) for d in drivers],
                             search=search,
                             status=status,
                             availability=availability)
    finally:
        db.close()


@logistics_bp.route('/drivers/new', methods=['GET', 'POST'])
@logistics_login_required
def drivers_new():
    """Create new driver."""
    user = get_current_user()
    db = get_db()

    if request.method == 'POST':
        try:
            data = request.form
            today = datetime.now().strftime('%Y%m%d')
            driver_code = f"DRV{today}001"

            existing = db.execute(
                "SELECT driver_code FROM logistics_drivers WHERE driver_code LIKE ? ORDER BY id DESC LIMIT 1",
                (f'DRV{today}%',)
            ).fetchone()
            if existing:
                last_num = int(existing['driver_code'].replace(f'DRV{today}', ''))
                driver_code = f"DRV{today}{(last_num + 1):04d}"

            cursor = db.execute("""
                INSERT INTO logistics_drivers (
                    employee_id, driver_code, full_name, employee_type, company_id,
                    mobile, emergency_contact, license_number, license_class,
                    license_expiry, nationality, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('employee_id'),
                driver_code,
                data.get('full_name'),
                data.get('employee_type', 'internal'),
                data.get('company_id') or user.get('company_id'),
                data.get('mobile'),
                data.get('emergency_contact'),
                data.get('license_number'),
                data.get('license_class'),
                parse_date(data.get('license_expiry')),
                data.get('nationality'),
                data.get('status', 'active'),
                data.get('notes')
            ))

            db.commit()
            flash(f'Driver {driver_code} created!', 'success')
            return redirect(url_for('logistics.drivers_view', id=cursor.lastrowid))

        except Exception as e:
            db.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            db.close()

    try:
        employees = db.execute("""
            SELECT e.id, e.first_name, e.last_name, e.employee_code
            FROM hr_employees e WHERE e.status = 'Active'
            ORDER BY e.first_name
        """).fetchall()
        vehicles = db.execute("SELECT id, plate_number FROM logistics_vehicles WHERE status = 'active' ORDER BY plate_number").fetchall()

        return render_template('logistics/drivers/new.html',
                             title='New Driver',
                             driver=None,
                             employees=[dict(e) for e in employees],
                             vehicles=[dict(v) for v in vehicles])
    finally:
        db.close()


@logistics_bp.route('/drivers/view/<int:id>')
@logistics_login_required
def drivers_view(id):
    """View driver detail."""
    user = get_current_user()
    db = get_db()

    try:
        driver = db.execute("""
            SELECT d.*, v.plate_number as assigned_vehicle
            FROM logistics_drivers d
            LEFT JOIN logistics_vehicles v ON d.assigned_vehicle_id = v.id
            WHERE d.id = ?
        """, (id,)).fetchone()

        if not driver:
            flash('Driver not found.', 'error')
            return redirect(url_for('logistics.drivers_list'))

        # Get documents
        docs = db.execute("""
            SELECT * FROM logistics_driver_documents WHERE driver_id = ? ORDER BY expiry_date
        """, (id,)).fetchall()

        # Get recent trips
        trips = db.execute("""
            SELECT t.*, v.plate_number
            FROM delivery_trips t
            LEFT JOIN logistics_vehicles v ON t.vehicle_id = v.id
            WHERE t.driver_id = ?
            ORDER BY t.date DESC LIMIT 10
        """, (id,)).fetchall()

        # Get incidents
        incidents = db.execute("""
            SELECT * FROM logistics_incidents WHERE driver_id = ?
            ORDER BY created_at DESC LIMIT 10
        """, (id,)).fetchall()

        return render_template('logistics/drivers/view.html',
                             title=f"Driver {driver['driver_code']}",
                             driver=dict(driver),
                             docs=[dict(d) for d in docs],
                             trips=[dict(t) for t in trips],
                             incidents=[dict(i) for i in incidents])
    finally:
        db.close()


# =============================================================================
# 9. DRIVER MANAGEMENT - EXTENDED
# =============================================================================

@logistics_bp.route('/drivers/<int:id>/documents', methods=['GET', 'POST'])
@logistics_login_required
def drivers_documents(id):
    """Driver document management."""
    user = get_current_user()
    db = get_db()

    try:
        driver = db.execute("SELECT * FROM logistics_drivers WHERE id = ?", (id,)).fetchone()
        if not driver:
            flash('Driver not found.', 'error')
            return redirect(url_for('logistics.drivers_list'))

        docs = db.execute("""
            SELECT * FROM logistics_driver_documents
            WHERE driver_id = ? ORDER BY expiry_date
        """, (id,)).fetchall()

        if request.method == 'POST':
            try:
                data = request.form
                db.execute("""
                    INSERT INTO logistics_driver_documents (
                        driver_id, document_type, document_number,
                        issue_date, expiry_date, file_path, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    id,
                    data.get('document_type'),
                    data.get('document_number'),
                    parse_date(data.get('issue_date')),
                    parse_date(data.get('expiry_date')),
                    data.get('file_path'),
                    data.get('notes')
                ))
                db.commit()
                flash('Document added successfully!', 'success')
                return redirect(url_for('logistics.drivers_documents', id=id))
            except Exception as e:
                db.rollback()
                flash(f'Error: {str(e)}', 'error')

        doc_types = ['License', 'Permit', 'Medical Certificate',
                      'Training Certificate', 'ID Card', 'Other']

        return render_template('logistics/drivers/documents.html',
                             title=f"Driver Documents - {driver['full_name']}",
                             driver=dict(driver),
                             docs=[dict(d) for d in docs],
                             doc_types=doc_types)
    finally:
        db.close()


@logistics_bp.route('/drivers/<int:id>/assignment-history')
@logistics_login_required
def drivers_assignment_history(id):
    """Driver assignment history."""
    user = get_current_user()
    db = get_db()

    try:
        driver = db.execute("SELECT * FROM logistics_drivers WHERE id = ?", (id,)).fetchone()
        if not driver:
            flash('Driver not found.', 'error')
            return redirect(url_for('logistics.drivers_list'))

        date_from = request.args.get('date_from', (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        assignments = db.execute("""
            SELECT s.shipment_code, s.status, s.priority,
                   s.delivery_address, s.created_at,
                   v.plate_number as vehicle
            FROM logistics_shipments s
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            WHERE s.driver_id = ?
            AND date(s.created_at) BETWEEN ? AND ?
            ORDER BY s.created_at DESC
        """, (id, date_from, date_to)).fetchall()

        return render_template('logistics/drivers/assignment_history.html',
                             title=f"Assignment History - {driver['full_name']}",
                             driver=dict(driver),
                             assignments=[dict(a) for a in assignments],
                             date_from=date_from,
                             date_to=date_to)
    finally:
        db.close()


@logistics_bp.route('/drivers/<int:id>/performance')
@logistics_login_required
def drivers_performance(id):
    """Driver performance KPIs."""
    user = get_current_user()
    db = get_db()

    try:
        driver = db.execute("SELECT * FROM logistics_drivers WHERE id = ?", (id,)).fetchone()
        if not driver:
            flash('Driver not found.', 'error')
            return redirect(url_for('logistics.drivers_list'))

        date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        # Delivery stats
        delivery_stats = db.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status = 'delivered' THEN 1 ELSE 0 END) as delivered,
                   SUM(CASE WHEN status = 'failed_delivery' THEN 1 ELSE 0 END) as failed,
                   SUM(CASE WHEN status = 'partially_delivered' THEN 1 ELSE 0 END) as partial
            FROM logistics_shipments
            WHERE driver_id = ? AND date(created_at) BETWEEN ? AND ?
        """, (id, date_from, date_to)).fetchone()

        # On-time delivery rate
        on_time = db.execute("""
            SELECT COUNT(*) as cnt
            FROM logistics_shipments
            WHERE driver_id = ? AND status = 'delivered'
            AND actual_delivery <= sla_target
            AND date(created_at) BETWEEN ? AND ?
        """, (id, date_from, date_to)).fetchone()['cnt']

        delivered_count = delivery_stats['delivered'] if delivery_stats else 0
        on_time_rate = round((on_time / delivered_count * 100) if delivered_count > 0 else 0, 1)

        # Customer ratings (if available)
        avg_rating = db.execute("""
            SELECT AVG(rating) as avg_rating
            FROM logistics_pod_records
            WHERE driver_id = ?
        """, (id,)).fetchone()['avg_rating'] or 0

        # Recent PODs
        recent_pods = db.execute("""
            SELECT pod.*, s.shipment_code
            FROM logistics_pod_records pod
            JOIN logistics_shipments s ON pod.shipment_id = s.id
            WHERE pod.driver_id = ?
            ORDER BY pod.delivery_timestamp DESC LIMIT 10
        """, (id,)).fetchall()

        return render_template('logistics/drivers/performance.html',
                             title=f"Performance - {driver['full_name']}",
                             driver=dict(driver),
                             date_from=date_from,
                             date_to=date_to,
                             delivery_stats=dict(delivery_stats) if delivery_stats else {},
                             on_time_rate=on_time_rate,
                             avg_rating=round(avg_rating, 1) if avg_rating else 0,
                             recent_pods=[dict(p) for p in recent_pods])
    finally:
        db.close()


@logistics_bp.route('/drivers/<int:id>/hours')
@logistics_login_required
def drivers_hours(id):
    """Driver hours/shift tracking scaffold."""
    user = get_current_user()
    db = get_db()

    try:
        driver = db.execute("SELECT * FROM logistics_drivers WHERE id = ?", (id,)).fetchone()
        if not driver:
            flash('Driver not found.', 'error')
            return redirect(url_for('logistics.drivers_list'))

        date_from = request.args.get('date_from', (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        # Get trip durations as proxy for hours worked
        trip_hours = db.execute("""
            SELECT t.date, t.trip_code, t.status,
                   t.start_time, t.end_time,
                   v.plate_number
            FROM delivery_trips t
            LEFT JOIN logistics_vehicles v ON t.vehicle_id = v.id
            WHERE t.driver_id = ?
            AND date(t.date) BETWEEN ? AND ?
            ORDER BY t.date DESC
        """, (id, date_from, date_to)).fetchall()

        return render_template('logistics/drivers/hours.html',
                             title=f"Driver Hours - {driver['full_name']}",
                             driver=dict(driver),
                             date_from=date_from,
                             date_to=date_to,
                             trip_hours=[dict(t) for t in trip_hours])
    finally:
        db.close()


@logistics_bp.route('/drivers/availability')
@logistics_login_required
def drivers_availability():
    """Driver availability calendar."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', datetime.now().strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'))

        drivers = db.execute("""
            SELECT d.*, v.plate_number as assigned_vehicle
            FROM logistics_drivers d
            LEFT JOIN logistics_vehicles v ON d.assigned_vehicle_id = v.id
            WHERE d.status = 'active'
            ORDER BY d.full_name
        """).fetchall()

        # Get driver assignments for the date range
        assignments = db.execute("""
            SELECT s.driver_id, s.vehicle_id, COUNT(*) as count
            FROM logistics_shipments s
            WHERE s.driver_id IS NOT NULL
            AND date(s.planned_date) BETWEEN ? AND ?
            GROUP BY s.driver_id, s.vehicle_id
        """, (date_from, date_to)).fetchall()

        assignments_dict = {(a['driver_id'], a['vehicle_id']): a['count'] for a in assignments}

        return render_template('logistics/drivers/availability.html',
                             title='Driver Availability',
                             drivers=[dict(d) for d in drivers],
                             assignments=assignments_dict,
                             date_from=date_from,
                             date_to=date_to)
    finally:
        db.close()


# =============================================================================
# 10. CARRIER MANAGEMENT
# =============================================================================

@logistics_bp.route('/carriers')
@logistics_login_required
def carriers_list():
    """Carriers list page."""
    user = get_current_user()
    db = get_db()

    try:
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '')

        query = """
            SELECT * FROM logistics_carriers WHERE 1=1
        """
        params = []

        if search:
            query += " AND (carrier_name LIKE ? OR carrier_code LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param])

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY carrier_name"

        carriers = db.execute(query, params).fetchall()

        return render_template('logistics/carriers/list.html',
                             title='Carrier Management',
                             carriers=[dict(c) for c in carriers],
                             search=search,
                             status=status)
    finally:
        db.close()


@logistics_bp.route('/carriers/new', methods=['GET', 'POST'])
@logistics_login_required
def carriers_new():
    """Create new carrier."""
    user = get_current_user()
    db = get_db()

    if request.method == 'POST':
        try:
            data = request.form
            today = datetime.now().strftime('%Y%m%d')
            carrier_code = f"CARR{today}001"

            existing = db.execute(
                "SELECT carrier_code FROM logistics_carriers WHERE carrier_code LIKE ? ORDER BY id DESC LIMIT 1",
                (f'CARR{today}%',)
            ).fetchone()
            if existing:
                last_num = int(existing['carrier_code'].replace(f'CARR{today}', ''))
                carrier_code = f"CARR{today}{(last_num + 1):04d}"

            cursor = db.execute("""
                INSERT INTO logistics_carriers (
                    carrier_code, carrier_name, contact_person, phone, email,
                    address, service_areas, vehicle_types, credit_terms,
                    status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                carrier_code,
                data.get('carrier_name'),
                data.get('contact_person'),
                data.get('phone'),
                data.get('email'),
                data.get('address'),
                data.get('service_areas'),
                data.get('vehicle_types'),
                data.get('credit_terms'),
                data.get('status', 'active'),
                data.get('notes')
            ))

            db.commit()
            flash(f'Carrier {carrier_code} created!', 'success')
            return redirect(url_for('logistics.carriers_list'))

        except Exception as e:
            db.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            db.close()

    try:
        return render_template('logistics/carriers/new.html',
                             title='New Carrier',
                             carrier=None)
    finally:
        db.close()


# =============================================================================
# 10a. LOAD PLANNING
# =============================================================================

@logistics_bp.route('/loads')
@logistics_login_required
def loads_list():
    """List all loads for load planning."""
    user = get_current_user()
    db = get_db()

    try:
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        per_page = 20

        query = """
            SELECT l.*,
                   v.plate_number as vehicle_plate,
                   t.trip_code,
                   u.username as created_by_name,
                   (SELECT COUNT(*) FROM logistics_shipments WHERE trip_id = l.trip_id) as shipment_count
            FROM logistics_loads l
            LEFT JOIN logistics_vehicles v ON l.vehicle_id = v.id
            LEFT JOIN logistics_trips t ON l.trip_id = t.id
            LEFT JOIN users u ON l.created_by = u.id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (l.load_code LIKE ? OR l.consolidation_group LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%'])

        if status_filter:
            query += " AND l.status = ?"
            params.append(status_filter)

        total = db.execute(
            "SELECT COUNT(*) as cnt FROM logistics_loads l WHERE 1=1" +
            (" AND (l.load_code LIKE ? OR l.consolidation_group LIKE ?)" if search else "") +
            (" AND l.status = ?" if status_filter else ""),
            [p for p in params if p]
        ).fetchone()['cnt']

        offset = (page - 1) * per_page
        query += f" ORDER BY l.created_at DESC LIMIT {per_page} OFFSET {offset}"

        loads = db.execute(query, params).fetchall()

        return render_template('logistics/loads/list.html',
                             title='Loads',
                             loads=[dict(l) for l in loads],
                             search=search,
                             status_filter=status_filter,
                             page=page,
                             per_page=per_page,
                             total=total)
    finally:
        db.close()


@logistics_bp.route('/loads/new', methods=['GET', 'POST'])
@logistics_login_required
def loads_new():
    """Create new load."""
    user = get_current_user()
    db = get_db()

    if request.method == 'POST':
        try:
            data = request.form
            load_code = f'LD-{datetime.now().strftime("%Y%m%d%H%M%S")}'

            cursor = db.execute("""
                INSERT INTO logistics_loads (
                    load_code, trip_id, vehicle_id, status, priority,
                    weight_kg, volume_m3, consolidation_group, notes,
                    created_by, branch_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                load_code,
                data.get('trip_id') or None,
                data.get('vehicle_id') or None,
                data.get('status', 'planning'),
                data.get('priority', 'standard'),
                float(data.get('weight_kg') or 0),
                float(data.get('volume_m3') or 0),
                data.get('consolidation_group') or None,
                data.get('notes'),
                user['id'],
                user.get('branch_id', 1)
            ))

            db.commit()
            flash(f'Load {load_code} created!', 'success')
            return redirect(url_for('logistics.loads_list'))

        except Exception as e:
            db.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            db.close()

    trips = db.execute("SELECT id, trip_code FROM logistics_trips WHERE status IN ('scheduled', 'planning') ORDER BY trip_code").fetchall()
    vehicles = db.execute("SELECT id, plate_number, capacity FROM logistics_vehicles WHERE status = 'active' ORDER BY plate_number").fetchall()

    return render_template('logistics/loads/new.html',
                         title='New Load',
                         load=None,
                         trips=[dict(t) for t in trips],
                         vehicles=[dict(v) for v in vehicles])


@logistics_bp.route('/loads/<int:id>')
@logistics_login_required
def loads_view(id):
    """View load detail."""
    user = get_current_user()
    db = get_db()

    try:
        load = db.execute("""
            SELECT l.*, v.plate_number as vehicle_plate, v.vehicle_type,
                   t.trip_code, u.username as created_by_name
            FROM logistics_loads l
            LEFT JOIN logistics_vehicles v ON l.vehicle_id = v.id
            LEFT JOIN logistics_trips t ON l.trip_id = t.id
            LEFT JOIN users u ON l.created_by = u.id
            WHERE l.id = ?
        """, (id,)).fetchone()

        if not load:
            flash('Load not found', 'error')
            return redirect(url_for('logistics.loads_list'))

        shipments = db.execute("""
            SELECT s.*, sh.tracking_number, sh.receiver_name, sh.weight_kg
            FROM logistics_shipments s
            LEFT JOIN logistics_shipments sh ON s.shipment_id = sh.id
            WHERE s.trip_id = ?
            ORDER BY s.created_at DESC
        """, (load['trip_id'],)).fetchall() if load['trip_id'] else []

        return render_template('logistics/loads/view.html',
                             title=f'Load {load["load_code"]}',
                             load=dict(load),
                             shipments=[dict(s) for s in shipments])
    finally:
        db.close()


@logistics_bp.route('/loads/<int:id>/assign', methods=['GET', 'POST'])
@logistics_login_required
def loads_assign(id):
    """Assign shipments to load."""
    user = get_current_user()
    db = get_db()

    try:
        load = db.execute("SELECT * FROM logistics_loads WHERE id = ?", (id,)).fetchone()

        if not load:
            flash('Load not found', 'error')
            return redirect(url_for('logistics.loads_list'))

        if request.method == 'POST':
            shipment_ids = request.form.getlist('shipment_ids')
            try:
                for shipment_id in shipment_ids:
                    db.execute("""
                        INSERT OR REPLACE INTO logistics_load_shipments (load_id, shipment_id)
                        VALUES (?, ?)
                    """, (id, shipment_id))
                db.commit()
                flash(f'Shipments assigned to load {load["load_code"]}', 'success')
                return redirect(url_for('logistics.loads_view', id=id))
            except Exception as e:
                db.rollback()
                flash(f'Error: {str(e)}', 'error')

        unassigned = db.execute("""
            SELECT s.*, c.customer_name, c.weight_kg, c.volume_m3
            FROM logistics_shipments s
            LEFT JOIN logistics_customers c ON s.customer_id = c.id
            WHERE s.trip_id IS NULL AND s.status = 'pending'
            ORDER BY s.priority DESC, s.due_date ASC
        """).fetchall()

        assigned = db.execute("""
            SELECT shipment_id FROM logistics_load_shipments WHERE load_id = ?
        """, (id,)).fetchall()
        assigned_ids = [s['shipment_id'] for s in assigned]

        return render_template('logistics/loads/assign.html',
                             title=f'Assign Shipments to {load["load_code"]}',
                             load=dict(load),
                             unassigned=[dict(s) for s in unassigned],
                             assigned_ids=assigned_ids)
    finally:
        db.close()


@logistics_bp.route('/loads/consolidation')
@logistics_login_required
def loads_consolidation():
    """Load consolidation view."""
    user = get_current_user()
    db = get_db()

    try:
        groups = db.execute("""
            SELECT consolidation_group, COUNT(*) as load_count,
                   SUM(weight_kg) as total_weight, SUM(volume_m3) as total_volume
            FROM logistics_loads
            WHERE consolidation_group IS NOT NULL AND consolidation_group != ''
            GROUP BY consolidation_group
            ORDER BY load_count DESC
        """).fetchall()

        return render_template('logistics/loads/consolidation.html',
                             title='Load Consolidation',
                             groups=[dict(g) for g in groups])
    finally:
        db.close()


@logistics_bp.route('/loads/urgent')
@logistics_login_required
def loads_urgent():
    """Urgent load queue."""
    user = get_current_user()
    db = get_db()

    try:
        urgent_loads = db.execute("""
            SELECT l.*, v.plate_number as vehicle_plate, t.trip_code
            FROM logistics_loads l
            LEFT JOIN logistics_vehicles v ON l.vehicle_id = v.id
            LEFT JOIN logistics_trips t ON l.trip_id = t.id
            WHERE l.priority IN ('urgent', 'high') AND l.status != 'dispatched'
            ORDER BY l.created_at DESC
        """).fetchall()

        return render_template('logistics/loads/urgent.html',
                             title='Urgent Load Queue',
                             loads=[dict(l) for l in urgent_loads])
    finally:
        db.close()


@logistics_bp.route('/api/loads/<int:id>/capacity-check', methods=['GET'])
@logistics_login_required
def api_loads_capacity_check(id):
    """Check vehicle capacity for load."""
    user = get_current_user()
    db = get_db()

    try:
        load = db.execute("SELECT * FROM logistics_loads WHERE id = ?", (id,)).fetchone()

        if not load:
            return jsonify({'error': 'Load not found'}), 404

        if not load['vehicle_id']:
            return jsonify({'error': 'No vehicle assigned'}), 400

        vehicle = db.execute("SELECT * FROM logistics_vehicles WHERE id = ?", (load['vehicle_id'],)).fetchone()

        total_weight = float(load['weight_kg'] or 0)
        total_volume = float(load['volume_m3'] or 0)
        vehicle_capacity = float(vehicle['capacity'] or 0) * 1000

        weight_ok = total_weight <= vehicle_capacity
        volume_ok = total_volume <= (vehicle_capacity * 0.3)

        return jsonify({
            'load_id': id,
            'vehicle_id': vehicle['id'],
            'vehicle_plate': vehicle['plate_number'],
            'vehicle_capacity_kg': vehicle_capacity,
            'load_weight_kg': total_weight,
            'load_volume_m3': total_volume,
            'weight_utilization': round((total_weight / vehicle_capacity) * 100, 2) if vehicle_capacity else 0,
            'volume_utilization': round((total_volume / (vehicle_capacity * 0.3)) * 100, 2) if vehicle_capacity else 0,
            'weight_ok': weight_ok,
            'volume_ok': volume_ok,
            'capacity_ok': weight_ok and volume_ok
        })
    finally:
        db.close()


# =============================================================================
# 11. COST MANAGEMENT
# =============================================================================

@logistics_bp.route('/costs')
@logistics_login_required
def costs_list():
    """Cost entries list page."""
    user = get_current_user()
    db = get_db()

    try:
        search = request.args.get('search', '').strip()
        cost_type = request.args.get('cost_type', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        page = int(request.args.get('page', 1))
        per_page = 20

        query = """
            SELECT c.*, s.shipment_code, u.username as created_by_name
            FROM logistics_cost_entries c
            LEFT JOIN logistics_shipments s ON c.shipment_id = s.id
            LEFT JOIN users u ON c.created_by = u.id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (s.shipment_code LIKE ? OR c.description LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param])

        if cost_type:
            query += " AND c.cost_type = ?"
            params.append(cost_type)

        if date_from:
            query += " AND date(c.created_at) >= ?"
            params.append(date_from)

        if date_to:
            query += " AND date(c.created_at) <= ?"
            params.append(date_to)

        query += " ORDER BY c.created_at DESC"

        count_query = query.replace("SELECT c.*, s.shipment_code, u.username as created_by_name", "SELECT COUNT(*) as cnt")
        total = db.execute(count_query, params).fetchone()['cnt']

        offset = (page - 1) * per_page
        query += f" LIMIT {per_page} OFFSET {offset}"

        costs = db.execute(query, params).fetchall()
        cost_types = db.execute("SELECT setting_value FROM logistics_settings WHERE category = 'Cost Types' AND is_active = 1").fetchall()

        # Calculate totals
        total_amount = db.execute(f"""
            SELECT SUM(c.amount) as total FROM logistics_cost_entries c WHERE 1=1
            {'AND c.cost_type = ?' if cost_type else ''}
            {'AND date(c.created_at) >= ?' if date_from else ''}
            {'AND date(c.created_at) <= ?' if date_to else ''}
        """, [p for p in params if p]).fetchone()['total'] or 0

        return render_template('logistics/costs/list.html',
                             title='Cost Management',
                             costs=[dict(c) for c in costs],
                             search=search,
                             cost_type=cost_type,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             total_pages=(total + per_page - 1) // per_page,
                             total=total,
                             total_amount=total_amount,
                             cost_types=[ct['setting_value'] for ct in cost_types])
    finally:
        db.close()


@logistics_bp.route('/costs/new', methods=['GET', 'POST'])
@logistics_login_required
def costs_new():
    """Create new cost entry."""
    user = get_current_user()
    db = get_db()

    if request.method == 'POST':
        try:
            data = request.form

            cursor = db.execute("""
                INSERT INTO logistics_cost_entries (
                    shipment_id, trip_id, cost_type, description, amount,
                    currency, cost_category, vendor_id, invoice_reference, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('shipment_id'),
                data.get('trip_id'),
                data.get('cost_type'),
                data.get('description'),
                float(data.get('amount', 0)),
                data.get('currency', 'AED'),
                data.get('cost_category'),
                data.get('vendor_id'),
                data.get('invoice_reference'),
                user['id']
            ))

            db.commit()
            flash('Cost entry created!', 'success')
            return redirect(url_for('logistics.costs_list'))

        except Exception as e:
            db.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            db.close()

    try:
        shipments = db.execute("""
            SELECT id, shipment_code FROM logistics_shipments
            WHERE status NOT IN ('cancelled')
            ORDER BY created_at DESC
        """).fetchall()
        cost_types = db.execute("SELECT setting_value FROM logistics_settings WHERE category = 'Cost Types' AND is_active = 1").fetchall()
        cost_categories = ['direct', 'indirect', 'fuel', 'maintenance', 'admin']

        return render_template('logistics/costs/new.html',
                             title='New Cost Entry',
                             cost=None,
                             shipments=[dict(s) for s in shipments],
                             cost_types=[ct['setting_value'] for ct in cost_types],
                             cost_categories=cost_categories)
    finally:
        db.close()


# =============================================================================
# 11. COST MANAGEMENT - EXTENDED
# =============================================================================

@logistics_bp.route('/costs/freight')
@logistics_login_required
def costs_freight():
    """Freight charges listing."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        freight_costs = db.execute("""
            SELECT c.*, s.shipment_code, s.consignee_name,
                   v.plate_number, u.username
            FROM logistics_cost_entries c
            LEFT JOIN logistics_shipments s ON c.shipment_id = s.id
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            LEFT JOIN users u ON c.created_by = u.id
            WHERE c.cost_type = 'Freight'
            AND date(c.created_at) BETWEEN ? AND ?
            ORDER BY c.created_at DESC
        """, (date_from, date_to)).fetchall()

        total_freight = db.execute("""
            SELECT SUM(c.amount) as total
            FROM logistics_cost_entries c
            WHERE c.cost_type = 'Freight'
            AND date(c.created_at) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['total'] or 0

        return render_template('logistics/costs/freight.html',
                             title='Freight Charges',
                             costs=[dict(c) for c in freight_costs],
                             date_from=date_from,
                             date_to=date_to,
                             total_freight=total_freight)
    finally:
        db.close()


@logistics_bp.route('/costs/trip/<int:trip_id>')
@logistics_login_required
def costs_trip_detail(trip_id):
    """Trip cost detail view."""
    user = get_current_user()
    db = get_db()

    try:
        trip = db.execute("""
            SELECT t.*, d.full_name as driver_name, v.plate_number
            FROM delivery_trips t
            LEFT JOIN logistics_drivers d ON t.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON t.vehicle_id = v.id
            WHERE t.id = ?
        """, (trip_id,)).fetchone()

        if not trip:
            flash('Trip not found.', 'error')
            return redirect(url_for('logistics.trips_list'))

        # Get all costs for this trip
        costs = db.execute("""
            SELECT c.*, u.username
            FROM logistics_cost_entries c
            LEFT JOIN users u ON c.created_by = u.id
            WHERE c.trip_id = ?
            ORDER BY c.created_at
        """, (trip_id,)).fetchall()

        # Get trip expenses
        expenses = db.execute("""
            SELECT e.*
            FROM logistics_trip_expenses e
            WHERE e.trip_id = ?
            ORDER BY e.created_at
        """, (trip_id,)).fetchall()

        total_costs = sum(c['amount'] for c in costs) if costs else 0
        total_expenses = sum(e['amount'] for e in expenses) if expenses else 0

        return render_template('logistics/costs/trip_detail.html',
                             title=f"Trip Costs - {trip['trip_code']}",
                             trip=dict(trip),
                             costs=[dict(c) for c in costs],
                             expenses=[dict(e) for e in expenses],
                             total_costs=total_costs,
                             total_expenses=total_expenses)
    finally:
        db.close()


@logistics_bp.route('/costs/route-analysis')
@logistics_login_required
def costs_route_analysis():
    """Route cost analysis."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        route_costs = db.execute("""
            SELECT r.route_name, r.route_code, r.distance_km,
                   COUNT(DISTINCT s.id) as shipment_count,
                   SUM(c.amount) as total_cost,
                   AVG(c.amount) as avg_cost_per_shipment
            FROM logistics_route_masters r
            LEFT JOIN logistics_shipments s ON s.route_id = r.id
            LEFT JOIN logistics_cost_entries c ON c.shipment_id = s.id
            WHERE (date(s.created_at) BETWEEN ? AND ? OR s.created_at IS NULL)
            GROUP BY r.id
            ORDER BY total_cost DESC
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/costs/route_analysis.html',
                             title='Route Cost Analysis',
                             routes=[dict(r) for r in route_costs],
                             date_from=date_from,
                             date_to=date_to)
    finally:
        db.close()


@logistics_bp.route('/costs/carrier')
@logistics_login_required
def costs_carrier():
    """Carrier cost scaffold."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        carriers = db.execute("""
            SELECT ca.*,
                   COUNT(s.id) as shipment_count,
                   SUM(c.amount) as total_cost
            FROM logistics_carriers ca
            LEFT JOIN logistics_shipments s ON s.carrier_id = ca.id
            LEFT JOIN logistics_cost_entries c ON c.shipment_id = s.id AND c.cost_type = 'Carrier Charges'
            WHERE date(s.created_at) BETWEEN ? AND ? OR s.created_at IS NULL
            GROUP BY ca.id
            ORDER BY total_cost DESC
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/costs/carrier.html',
                             title='Carrier Costs',
                             carriers=[dict(c) for c in carriers],
                             date_from=date_from,
                             date_to=date_to)
    finally:
        db.close()


@logistics_bp.route('/costs/dashboard')
@logistics_login_required
def costs_dashboard():
    """Cost dashboard."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        # Cost by type
        cost_by_type = db.execute("""
            SELECT c.cost_type, SUM(c.amount) as total
            FROM logistics_cost_entries c
            WHERE date(c.created_at) BETWEEN ? AND ?
            GROUP BY c.cost_type
            ORDER BY total DESC
        """, (date_from, date_to)).fetchall()

        # Cost by category
        cost_by_category = db.execute("""
            SELECT c.cost_category, SUM(c.amount) as total
            FROM logistics_cost_entries c
            WHERE date(c.created_at) BETWEEN ? AND ?
            AND c.cost_category IS NOT NULL
            GROUP BY c.cost_category
            ORDER BY total DESC
        """, (date_from, date_to)).fetchall()

        # Total cost
        total_cost = db.execute("""
            SELECT SUM(c.amount) as total
            FROM logistics_cost_entries c
            WHERE date(c.created_at) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['total'] or 0

        # Cost trend (daily)
        cost_trend = db.execute("""
            SELECT date(c.created_at) as cost_date, SUM(c.amount) as daily_total
            FROM logistics_cost_entries c
            WHERE date(c.created_at) BETWEEN ? AND ?
            GROUP BY date(c.created_at)
            ORDER BY cost_date
        """, (date_from, date_to)).fetchall()

        # Top cost shipments
        top_shipments = db.execute("""
            SELECT s.shipment_code, SUM(c.amount) as total_cost
            FROM logistics_cost_entries c
            JOIN logistics_shipments s ON c.shipment_id = s.id
            WHERE date(c.created_at) BETWEEN ? AND ?
            GROUP BY s.id
            ORDER BY total_cost DESC
            LIMIT 10
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/costs/cost_dashboard.html',
                             title='Cost Dashboard',
                             date_from=date_from,
                             date_to=date_to,
                             cost_by_type=[dict(c) for c in cost_by_type],
                             cost_by_category=[dict(c) for c in cost_by_category],
                             total_cost=total_cost,
                             cost_trend=[dict(c) for c in cost_trend],
                             top_shipments=[dict(s) for s in top_shipments])
    finally:
        db.close()


@logistics_bp.route('/costs/per-delivery')
@logistics_login_required
def costs_per_delivery():
    """Cost per delivery report."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        delivery_costs = db.execute("""
            SELECT s.shipment_code, s.status, s.priority,
                   s.delivery_address, s.actual_delivery,
                   SUM(c.amount) as total_cost
            FROM logistics_shipments s
            LEFT JOIN logistics_cost_entries c ON c.shipment_id = s.id
            WHERE date(s.created_at) BETWEEN ? AND ?
            GROUP BY s.id
            HAVING total_cost > 0 OR s.status = 'delivered'
            ORDER BY total_cost DESC
        """, (date_from, date_to)).fetchall()

        avg_cost = db.execute("""
            SELECT AVG(c.amount) as avg_cost
            FROM logistics_cost_entries c
            WHERE date(c.created_at) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['avg_cost'] or 0

        return render_template('logistics/costs/per_delivery.html',
                             title='Cost Per Delivery',
                             deliveries=[dict(d) for d in delivery_costs],
                             date_from=date_from,
                             date_to=date_to,
                             avg_cost=round(avg_cost, 2))
    finally:
        db.close()


# =============================================================================
# 12. PROOF OF DELIVERY (POD)
# =============================================================================

@logistics_bp.route('/pod')
@logistics_login_required
def pod_list():
    """POD records list page."""
    user = get_current_user()
    db = get_db()

    try:
        search = request.args.get('search', '').strip()
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')

        query = """
            SELECT pod.*, s.shipment_code, c.name as customer_name, d.full_name as driver_name
            FROM logistics_pod_records pod
            LEFT JOIN logistics_shipments s ON pod.shipment_id = s.id
            LEFT JOIN sdad_customers c ON pod.customer_id = c.id
            LEFT JOIN logistics_drivers d ON pod.driver_id = d.id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (s.shipment_code LIKE ? OR c.name LIKE ? OR pod.receiver_name LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])

        if date_from:
            query += " AND date(pod.delivery_timestamp) >= ?"
            params.append(date_from)

        if date_to:
            query += " AND date(pod.delivery_timestamp) <= ?"
            params.append(date_to)

        query += " ORDER BY pod.delivery_timestamp DESC"

        records = db.execute(query, params).fetchall()

        return render_template('logistics/pod/list.html',
                             title='Proof of Delivery',
                             records=[dict(r) for r in records],
                             search=search,
                             date_from=date_from,
                             date_to=date_to)
    finally:
        db.close()


@logistics_bp.route('/pod/new/<int:shipment_id>', methods=['GET', 'POST'])
@logistics_login_required
def pod_new(shipment_id):
    """Create new POD record."""
    user = get_current_user()
    db = get_db()

    try:
        shipment = db.execute("SELECT * FROM logistics_shipments WHERE id = ?", (shipment_id,)).fetchone()
        if not shipment:
            flash('Shipment not found.', 'error')
            return redirect(url_for('logistics.shipments_list'))

        if request.method == 'POST':
            try:
                data = request.form

                cursor = db.execute("""
                    INSERT INTO logistics_pod_records (
                        shipment_id, trip_id, driver_id, customer_id,
                        receiver_name, receiver_phone, delivery_timestamp,
                        latitude, longitude, notes, delivery_status,
                        shortage_confirmed, damage_confirmed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    shipment_id,
                    data.get('trip_id'),
                    shipment['driver_id'],
                    shipment['customer_id'],
                    data.get('receiver_name'),
                    data.get('receiver_phone'),
                    datetime.now(),
                    data.get('latitude'),
                    data.get('longitude'),
                    data.get('notes'),
                    data.get('delivery_status', 'completed'),
                    1 if data.get('shortage_confirmed') else 0,
                    1 if data.get('damage_confirmed') else 0
                ))

                # Update shipment status if delivered
                if data.get('delivery_status') == 'completed':
                    db.execute("""
                        UPDATE logistics_shipments SET status = 'delivered', actual_delivery = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (shipment_id,))
                    db.execute("""
                        INSERT INTO logistics_shipment_status_history (shipment_id, from_status, to_status, changed_by, reason)
                        VALUES (?, ?, ?, ?, ?)
                    """, (shipment_id, shipment['status'], 'delivered', user['id'], 'POD submitted'))

                db.commit()
                flash('POD recorded successfully!', 'success')
                return redirect(url_for('logistics.pod_list'))

            except Exception as e:
                db.rollback()
                flash(f'Error: {str(e)}', 'error')

        return render_template('logistics/pod/new.html',
                             title='Record POD',
                             shipment=dict(shipment))
    finally:
        db.close()


# =============================================================================
# 12. PROOF OF DELIVERY (POD) - EXTENDED
# =============================================================================

@logistics_bp.route('/pod/<int:id>')
@logistics_login_required
def pod_view(id):
    """View POD detail."""
    user = get_current_user()
    db = get_db()

    try:
        pod = db.execute("""
            SELECT pod.*, s.shipment_code, s.consignee_name, s.consignee_phone,
                   s.delivery_address, c.name as customer_name,
                   d.full_name as driver_name, v.plate_number
            FROM logistics_pod_records pod
            LEFT JOIN logistics_shipments s ON pod.shipment_id = s.id
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            LEFT JOIN logistics_drivers d ON pod.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            WHERE pod.id = ?
        """, (id,)).fetchone()

        if not pod:
            flash('POD not found.', 'error')
            return redirect(url_for('logistics.pod_list'))

        return render_template('logistics/pod/view.html',
                             title=f"POD - {pod['shipment_code']}",
                             pod=dict(pod))
    finally:
        db.close()


@logistics_bp.route('/pod/<int:id>/edit', methods=['GET', 'POST'])
@logistics_login_required
def pod_edit(id):
    """Edit POD record."""
    user = get_current_user()
    db = get_db()

    try:
        pod = db.execute("""
            SELECT pod.*, s.shipment_code
            FROM logistics_pod_records pod
            LEFT JOIN logistics_shipments s ON pod.shipment_id = s.id
            WHERE pod.id = ?
        """, (id,)).fetchone()

        if not pod:
            flash('POD not found.', 'error')
            return redirect(url_for('logistics.pod_list'))

        if request.method == 'POST':
            try:
                data = request.form
                db.execute("""
                    UPDATE logistics_pod_records SET
                        receiver_name = ?, receiver_phone = ?,
                        latitude = ?, longitude = ?, notes = ?,
                        delivery_status = ?,
                        shortage_confirmed = ?, damage_confirmed = ?
                    WHERE id = ?
                """, (
                    data.get('receiver_name'),
                    data.get('receiver_phone'),
                    data.get('latitude'),
                    data.get('longitude'),
                    data.get('notes'),
                    data.get('delivery_status'),
                    1 if data.get('shortage_confirmed') else 0,
                    1 if data.get('damage_confirmed') else 0,
                    id
                ))
                db.commit()
                flash('POD updated successfully!', 'success')
                return redirect(url_for('logistics.pod_view', id=id))
            except Exception as e:
                db.rollback()
                flash(f'Error: {str(e)}', 'error')

        return render_template('logistics/pod/edit.html',
                             title=f"Edit POD - {pod['shipment_code']}",
                             pod=dict(pod))
    finally:
        db.close()


@logistics_bp.route('/pod/<int:id>/signature', methods=['GET', 'POST'])
@logistics_login_required
def pod_signature(id):
    """Capture signature for POD."""
    user = get_current_user()
    db = get_db()

    try:
        pod = db.execute("""
            SELECT pod.*, s.shipment_code
            FROM logistics_pod_records pod
            LEFT JOIN logistics_shipments s ON pod.shipment_id = s.id
            WHERE pod.id = ?
        """, (id,)).fetchone()

        if not pod:
            flash('POD not found.', 'error')
            return redirect(url_for('logistics.pod_list'))

        if request.method == 'POST':
            try:
                data = request.form
                db.execute("""
                    UPDATE logistics_pod_records SET
                        signature_data = ?
                    WHERE id = ?
                """, (data.get('signature_data'), id))
                db.commit()
                flash('Signature captured!', 'success')
                return redirect(url_for('logistics.pod_view', id=id))
            except Exception as e:
                db.rollback()
                flash(f'Error: {str(e)}', 'error')

        return render_template('logistics/pod/signature.html',
                             title=f"Capture Signature - {pod['shipment_code']}",
                             pod=dict(pod))
    finally:
        db.close()


@logistics_bp.route('/pod/<int:id>/photo', methods=['GET', 'POST'])
@logistics_login_required
def pod_photo(id):
    """Upload delivery photo for POD."""
    user = get_current_user()
    db = get_db()

    try:
        pod = db.execute("""
            SELECT pod.*, s.shipment_code
            FROM logistics_pod_records pod
            LEFT JOIN logistics_shipments s ON pod.shipment_id = s.id
            WHERE pod.id = ?
        """, (id,)).fetchone()

        if not pod:
            flash('POD not found.', 'error')
            return redirect(url_for('logistics.pod_list'))

        if request.method == 'POST':
            try:
                photo_path = request.form.get('photo_path', '')
                if photo_path:
                    current_photos = pod['photo_paths'] or ''
                    if current_photos:
                        new_photos = current_photos + ',' + photo_path
                    else:
                        new_photos = photo_path
                    db.execute("""
                        UPDATE logistics_pod_records SET
                            photo_paths = ?
                        WHERE id = ?
                    """, (new_photos, id))
                    db.commit()
                    flash('Photo added!', 'success')
                return redirect(url_for('logistics.pod_view', id=id))
            except Exception as e:
                db.rollback()
                flash(f'Error: {str(e)}', 'error')

        return render_template('logistics/pod/photo_upload.html',
                             title=f"Upload Photo - {pod['shipment_code']}",
                             pod=dict(pod))
    finally:
        db.close()


@logistics_bp.route('/pod/<int:id>/partial', methods=['GET', 'POST'])
@logistics_login_required
def pod_partial(id):
    """Mark POD as partial delivery."""
    user = get_current_user()
    db = get_db()

    try:
        pod = db.execute("""
            SELECT pod.*, s.shipment_code, s.status as shipment_status
            FROM logistics_pod_records pod
            LEFT JOIN logistics_shipments s ON pod.shipment_id = s.id
            WHERE pod.id = ?
        """, (id,)).fetchone()

        if not pod:
            flash('POD not found.', 'error')
            return redirect(url_for('logistics.pod_list'))

        if request.method == 'POST':
            try:
                data = request.form
                db.execute("""
                    UPDATE logistics_pod_records SET
                        delivery_status = 'partial',
                        notes = ?
                    WHERE id = ?
                """, (data.get('notes', ''), id))
                db.execute("""
                    UPDATE logistics_shipments SET status = 'partially_delivered'
                    WHERE id = ?
                """, (pod['shipment_id'],))
                db.commit()
                flash('Marked as partial delivery.', 'success')
                return redirect(url_for('logistics.pod_view', id=id))
            except Exception as e:
                db.rollback()
                flash(f'Error: {str(e)}', 'error')

        return render_template('logistics/pod/partial.html',
                             title=f"Partial Delivery - {pod['shipment_code']}",
                             pod=dict(pod))
    finally:
        db.close()


@logistics_bp.route('/pod/<int:id>/failed', methods=['GET', 'POST'])
@logistics_login_required
def pod_failed(id):
    """Mark POD as failed delivery."""
    user = get_current_user()
    db = get_db()

    try:
        pod = db.execute("""
            SELECT pod.*, s.shipment_code, s.status as shipment_status
            FROM logistics_pod_records pod
            LEFT JOIN logistics_shipments s ON pod.shipment_id = s.id
            WHERE pod.id = ?
        """, (id,)).fetchone()

        if not pod:
            flash('POD not found.', 'error')
            return redirect(url_for('logistics.pod_list'))

        if request.method == 'POST':
            try:
                data = request.form
                db.execute("""
                    UPDATE logistics_pod_records SET
                        delivery_status = 'failed',
                        notes = ?
                    WHERE id = ?
                """, (data.get('failure_reason', ''), id))
                db.execute("""
                    UPDATE logistics_shipments SET status = 'failed_delivery'
                    WHERE id = ?
                """, (pod['shipment_id'],))
                db.commit()
                flash('Marked as failed delivery.', 'success')
                return redirect(url_for('logistics.pod_view', id=id))
            except Exception as e:
                db.rollback()
                flash(f'Error: {str(e)}', 'error')

        return render_template('logistics/pod/failed.html',
                             title=f"Failed Delivery - {pod['shipment_code']}",
                             pod=dict(pod))
    finally:
        db.close()


@logistics_bp.route('/pod/<int:id>/notes', methods=['GET', 'POST'])
@logistics_login_required
def pod_notes(id):
    """Add notes to POD."""
    user = get_current_user()
    db = get_db()

    try:
        pod = db.execute("""
            SELECT pod.*, s.shipment_code
            FROM logistics_pod_records pod
            LEFT JOIN logistics_shipments s ON pod.shipment_id = s.id
            WHERE pod.id = ?
        """, (id,)).fetchone()

        if not pod:
            flash('POD not found.', 'error')
            return redirect(url_for('logistics.pod_list'))

        if request.method == 'POST':
            try:
                data = request.form
                current_notes = pod['notes'] or ''
                new_note = f"{datetime.now().strftime('%Y-%m-%d %H:%M')}: {data.get('note', '')}"
                updated_notes = current_notes + '\n' + new_note if current_notes else new_note
                db.execute("""
                    UPDATE logistics_pod_records SET notes = ? WHERE id = ?
                """, (updated_notes, id))
                db.commit()
                flash('Note added!', 'success')
                return redirect(url_for('logistics.pod_view', id=id))
            except Exception as e:
                db.rollback()
                flash(f'Error: {str(e)}', 'error')

        return redirect(url_for('logistics.pod_view', id=id))
    finally:
        db.close()


@logistics_bp.route('/pod/<int:id>/attachments')
@logistics_login_required
def pod_attachments(id):
    """Manage POD attachments."""
    user = get_current_user()
    db = get_db()

    try:
        pod = db.execute("""
            SELECT pod.*, s.shipment_code
            FROM logistics_pod_records pod
            LEFT JOIN logistics_shipments s ON pod.shipment_id = s.id
            WHERE pod.id = ?
        """, (id,)).fetchone()

        if not pod:
            flash('POD not found.', 'error')
            return redirect(url_for('logistics.pod_list'))

        photo_paths = []
        if pod['photo_paths']:
            photo_paths = pod['photo_paths'].split(',')

        return render_template('logistics/pod/attachments.html',
                             title=f"Attachments - {pod['shipment_code']}",
                             pod=dict(pod),
                             photo_paths=photo_paths)
    finally:
        db.close()


@logistics_bp.route('/pod/<int:id>/approve', methods=['POST'])
@logistics_login_required
def pod_approve(id):
    """Approve POD."""
    user = get_current_user()
    db = get_db()

    try:
        db.execute("""
            UPDATE logistics_pod_records SET
                approved_by = ?, approved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user['id'], id))
        db.commit()
        flash('POD approved!', 'success')
        return redirect(url_for('logistics.pod_view', id=id))
    except Exception as e:
        db.rollback()
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('logistics.pod_view', id=id))
    finally:
        db.close()


@logistics_bp.route('/pod/<int:id>/reject', methods=['GET', 'POST'])
@logistics_login_required
def pod_reject(id):
    """Reject POD with reason."""
    user = get_current_user()
    db = get_db()

    try:
        pod = db.execute("""
            SELECT pod.*, s.shipment_code
            FROM logistics_pod_records pod
            LEFT JOIN logistics_shipments s ON pod.shipment_id = s.id
            WHERE pod.id = ?
        """, (id,)).fetchone()

        if not pod:
            flash('POD not found.', 'error')
            return redirect(url_for('logistics.pod_list'))

        if request.method == 'POST':
            try:
                data = request.form
                rejection_note = f"REJECTED ({datetime.now().strftime('%Y-%m-%d %H:%M')}): {data.get('reason', '')}"
                current_notes = pod['notes'] or ''
                updated_notes = current_notes + '\n' + rejection_note if current_notes else rejection_note
                db.execute("""
                    UPDATE logistics_pod_records SET notes = ? WHERE id = ?
                """, (updated_notes, id))
                db.commit()
                flash('POD rejected.', 'warning')
                return redirect(url_for('logistics.pod_view', id=id))
            except Exception as e:
                db.rollback()
                flash(f'Error: {str(e)}', 'error')

        return render_template('logistics/pod/reject.html',
                             title=f"Reject POD - {pod['shipment_code']}",
                             pod=dict(pod))
    finally:
        db.close()


# =============================================================================
# 13. INCIDENTS/EXCEPTIONS
# =============================================================================

@logistics_bp.route('/incidents')
@logistics_login_required
def incidents_list():
    """Incidents list page."""
    user = get_current_user()
    db = get_db()

    try:
        status = request.args.get('status', '')
        incident_type = request.args.get('incident_type', '')
        severity = request.args.get('severity', '')

        query = """
            SELECT i.*, s.shipment_code, d.full_name as driver_name, v.plate_number
            FROM logistics_incidents i
            LEFT JOIN logistics_shipments s ON i.shipment_id = s.id
            LEFT JOIN logistics_drivers d ON i.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON i.vehicle_id = v.id
            WHERE 1=1
        """
        params = []

        if status:
            query += " AND i.status = ?"
            params.append(status)

        if incident_type:
            query += " AND i.incident_type = ?"
            params.append(incident_type)

        if severity:
            query += " AND i.severity = ?"
            params.append(severity)

        query += " ORDER BY i.created_at DESC"

        incidents = db.execute(query, params).fetchall()
        incident_types = db.execute("SELECT setting_value FROM logistics_settings WHERE category = 'Incident Types' AND is_active = 1").fetchall()
        severities = ['low', 'medium', 'high', 'critical']

        return render_template('logistics/incidents/list.html',
                             title='Incidents',
                             incidents=[dict(i) for i in incidents],
                             status=status,
                             incident_type=incident_type,
                             severity=severity,
                             incident_types=[it['setting_value'] for it in incident_types],
                             severities=severities)
    finally:
        db.close()


@logistics_bp.route('/incidents/new', methods=['GET', 'POST'])
@logistics_login_required
def incidents_new():
    """Create new incident."""
    user = get_current_user()
    db = get_db()

    if request.method == 'POST':
        try:
            data = request.form
            incident_number = get_next_incident_number()

            cursor = db.execute("""
                INSERT INTO logistics_incidents (
                    incident_number, shipment_id, trip_id, driver_id, vehicle_id,
                    customer_id, incident_type, severity, incident_date, description,
                    responsible_party, status, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?)
            """, (
                incident_number,
                data.get('shipment_id'),
                data.get('trip_id'),
                data.get('driver_id'),
                data.get('vehicle_id'),
                data.get('customer_id'),
                data.get('incident_type'),
                data.get('severity', 'medium'),
                datetime.now(),
                data.get('description'),
                data.get('responsible_party'),
                user['id']
            ))

            db.commit()
            flash(f'Incident {incident_number} created!', 'success')
            return redirect(url_for('logistics.incidents_list'))

        except Exception as e:
            db.rollback()
            flash(f'Error: {str(e)}', 'error')
        finally:
            db.close()

    try:
        shipments = db.execute("SELECT id, shipment_code FROM logistics_shipments ORDER BY created_at DESC").fetchall()
        drivers = db.execute("SELECT id, full_name FROM logistics_drivers WHERE status = 'active' ORDER BY full_name").fetchall()
        vehicles = db.execute("SELECT id, plate_number FROM logistics_vehicles WHERE status = 'active' ORDER BY plate_number").fetchall()
        incident_types = db.execute("SELECT setting_value FROM logistics_settings WHERE category = 'Incident Types' AND is_active = 1").fetchall()

        return render_template('logistics/incidents/new.html',
                             title='New Incident',
                             incident=None,
                             shipments=[dict(s) for s in shipments],
                             drivers=[dict(d) for d in drivers],
                             vehicles=[dict(v) for v in vehicles],
                             incident_types=[it['setting_value'] for it in incident_types])
    finally:
        db.close()


@logistics_bp.route('/incidents/view/<int:id>')
@logistics_login_required
def incidents_view(id):
    """View incident detail."""
    user = get_current_user()
    db = get_db()

    try:
        incident = db.execute("""
            SELECT i.*, s.shipment_code, d.full_name as driver_name, v.plate_number,
                   u.username as created_by_name
            FROM logistics_incidents i
            LEFT JOIN logistics_shipments s ON i.shipment_id = s.id
            LEFT JOIN logistics_drivers d ON i.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON i.vehicle_id = v.id
            LEFT JOIN users u ON i.created_by = u.id
            WHERE i.id = ?
        """, (id,)).fetchone()

        if not incident:
            flash('Incident not found.', 'error')
            return redirect(url_for('logistics.incidents_list'))

        return render_template('logistics/incidents/view.html',
                             title=f"Incident {incident['incident_number']}",
                             incident=dict(incident))
    finally:
        db.close()


@logistics_bp.route('/incidents/close/<int:id>', methods=['POST'])
@logistics_login_required
def incidents_close(id):
    """Close an incident."""
    user = get_current_user()
    db = get_db()

    try:
        data = request.form

        db.execute("""
            UPDATE logistics_incidents SET
                status = 'closed', action_taken = ?, cost_impact = ?,
                closed_by = ?, closed_at = CURRENT_TIMESTAMP, closure_notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get('action_taken'),
            float(data.get('cost_impact', 0)),
            user['id'],
            data.get('closure_notes'),
            id
        ))

        db.commit()
        flash('Incident closed!', 'success')
        return redirect(url_for('logistics.incidents_view', id=id))

    except Exception as e:
        db.rollback()
        flash(f'Error: {str(e)}', 'error')
    finally:
        db.close()


# =============================================================================
# 14. REPORTS & ANALYTICS
# =============================================================================

@logistics_bp.route('/reports')
@logistics_login_required
def reports_menu():
    """Logistics reports menu."""
    return render_template('logistics/reports/index.html', title='Logistics Reports')


@logistics_bp.route('/reports/shipment-summary')
@logistics_login_required
def report_shipment_summary():
    """Shipment summary report."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', datetime.now().strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        stats = get_shipment_stats(
            company_id=user.get('company_id'),
            date_from=date_from,
            date_to=date_to
        )

        # By type
        by_type = db.execute("""
            SELECT shipment_type, COUNT(*) as cnt FROM logistics_shipments
            WHERE date(created_at) BETWEEN ? AND ?
            GROUP BY shipment_type
        """, (date_from, date_to)).fetchall()

        # By priority
        by_priority = db.execute("""
            SELECT priority, COUNT(*) as cnt FROM logistics_shipments
            WHERE date(created_at) BETWEEN ? AND ?
            GROUP BY priority
        """, (date_from, date_to)).fetchall()

        # By status
        by_status = db.execute("""
            SELECT status, COUNT(*) as cnt FROM logistics_shipments
            WHERE date(created_at) BETWEEN ? AND ?
            GROUP BY status
        """, (date_from, date_to)).fetchall()

        # Daily trend
        daily = db.execute("""
            SELECT date(created_at) as day, COUNT(*) as cnt
            FROM logistics_shipments
            WHERE date(created_at) BETWEEN ? AND ?
            GROUP BY day ORDER BY day
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/reports/shipment_summary.html',
                             title='Shipment Summary Report',
                             stats=stats,
                             by_type=[dict(r) for r in by_type],
                             by_priority=[dict(r) for r in by_priority],
                             by_status=[dict(r) for r in by_status],
                             daily=[dict(r) for r in daily],
                             date_from=date_from,
                             date_to=date_to)
    finally:
        db.close()


@logistics_bp.route('/reports/delivery-performance')
@logistics_login_required
def report_delivery_performance():
    """Delivery performance report."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', datetime.now().strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        # Delivery stats
        delivered = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_shipments
            WHERE status = 'delivered' AND date(actual_delivery) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['cnt']

        failed = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_shipments
            WHERE status = 'failed_delivery' AND date(updated_at) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['cnt']

        returned = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_shipments
            WHERE status = 'returned' AND date(updated_at) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['cnt']

        # By driver
        by_driver = db.execute("""
            SELECT d.full_name, COUNT(*) as total_deliveries,
                   SUM(CASE WHEN s.status = 'delivered' THEN 1 ELSE 0 END) as successful
            FROM logistics_shipments s
            JOIN logistics_drivers d ON s.driver_id = d.id
            WHERE date(s.actual_delivery) BETWEEN ? AND ?
            GROUP BY d.id
            ORDER BY successful DESC
        """, (date_from, date_to)).fetchall()

        # On-time delivery
        on_time = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_shipments
            WHERE status = 'delivered'
            AND date(actual_delivery) <= date(sla_target)
            AND date(actual_delivery) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['cnt']

        return render_template('logistics/reports/delivery_performance.html',
                             title='Delivery Performance Report',
                             delivered=delivered,
                             failed=failed,
                             returned=returned,
                             on_time=on_time,
                             by_driver=[dict(r) for r in by_driver],
                             date_from=date_from,
                             date_to=date_to)
    finally:
        db.close()


@logistics_bp.route('/reports/fleet-utilization')
@logistics_login_required
def report_fleet_utilization():
    """Fleet utilization report."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', datetime.now().strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        # Vehicle usage
        vehicle_usage = db.execute("""
            SELECT v.plate_number, v.vehicle_type,
                   COUNT(DISTINCT t.id) as total_trips,
                   SUM(t.warehouse_arrival - t.warehouse_departure) as total_hours
            FROM logistics_vehicles v
            LEFT JOIN delivery_trips t ON v.id = t.vehicle_id
                AND date(t.date) BETWEEN ? AND ?
            WHERE v.status = 'active'
            GROUP BY v.id
            ORDER BY total_trips DESC
        """, (date_from, date_to)).fetchall()

        # Cost by vehicle
        vehicle_costs = db.execute("""
            SELECT v.plate_number, SUM(c.amount) as total_cost
            FROM logistics_vehicles v
            LEFT JOIN logistics_cost_entries c ON c.shipment_id IN
                (SELECT id FROM logistics_shipments WHERE vehicle_id = v.id)
            WHERE date(c.created_at) BETWEEN ? AND ?
            GROUP BY v.id
            ORDER BY total_cost DESC
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/reports/fleet_utilization.html',
                             title='Fleet Utilization Report',
                             vehicle_usage=[dict(r) for r in vehicle_usage],
                             vehicle_costs=[dict(r) for r in vehicle_costs],
                             date_from=date_from,
                             date_to=date_to)
    finally:
        db.close()


@logistics_bp.route('/reports/driver-performance')
@logistics_login_required
def report_driver_performance():
    """Driver performance report."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', datetime.now().strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        driver_perf = db.execute("""
            SELECT d.driver_code, d.full_name, d.mobile,
                   COUNT(DISTINCT s.id) as total_shipments,
                   SUM(CASE WHEN s.status = 'delivered' THEN 1 ELSE 0 END) as delivered,
                   SUM(CASE WHEN s.status = 'failed_delivery' THEN 1 ELSE 0 END) as failed,
                   SUM(CASE WHEN s.status = 'in_transit' THEN 1 ELSE 0 END) as in_transit,
                   COUNT(DISTINCT t.id) as total_trips
            FROM logistics_drivers d
            LEFT JOIN logistics_shipments s ON d.id = s.driver_id
                AND date(s.created_at) BETWEEN ? AND ?
            LEFT JOIN delivery_trips t ON d.id = t.driver_id
                AND date(t.date) BETWEEN ? AND ?
            WHERE d.status = 'active'
            GROUP BY d.id
            ORDER BY delivered DESC
        """, (date_from, date_to, date_from, date_to)).fetchall()

        return render_template('logistics/reports/driver_performance.html',
                             title='Driver Performance Report',
                             drivers=[dict(d) for d in driver_perf],
                             date_from=date_from,
                             date_to=date_to)
    finally:
        db.close()


# =============================================================================
# 14b. TMS REPORTS & ANALYTICS CENTER
# =============================================================================

@logistics_bp.route('/reports/trips')
@logistics_login_required
def report_trips():
    """Trip Report - Complete trip details, status, and performance."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', today.strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        status_filter = request.args.get('status', '')
        branch_id = request.args.get('branch_id', '')
        page = int(request.args.get('page', 1))
        per_page = 25

        # Build WHERE clause
        conditions = ["date(t.planned_departure) BETWEEN ? AND ?"]
        params = [date_from, date_to]

        if status_filter:
            conditions.append("t.status = ?")
            params.append(status_filter)
        if branch_id:
            conditions.append("v.branch_id = ?")
            params.append(branch_id)

        where_clause = " AND ".join(conditions)

        # Get total count
        total_count = db.execute(f"""
            SELECT COUNT(*) as cnt FROM logistics_trips t
            LEFT JOIN logistics_drivers d ON t.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON t.vehicle_id = v.id
            LEFT JOIN logistics_route_masters r ON t.route_id = r.id
            WHERE {where_clause}
        """, params).fetchone()['cnt']

        # Get paginated trips
        offset = (page - 1) * per_page
        trips = db.execute(f"""
            SELECT t.*, d.full_name as driver_name, v.plate_number, v.vehicle_type,
                   r.route_name, r.route_code,
                   (t.completed_stops * 1.0 / NULLIF(t.total_stops, 0) * 100) as completion_rate
            FROM logistics_trips t
            LEFT JOIN logistics_drivers d ON t.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON t.vehicle_id = v.id
            LEFT JOIN logistics_route_masters r ON t.route_id = r.id
            WHERE {where_clause}
            ORDER BY t.planned_departure DESC
            LIMIT ? OFFSET ?
        """, params + [per_page, offset]).fetchall()

        # Summary stats
        summary = {
            'total_trips': total_count,
            'total_distance': db.execute(f"""
                SELECT COALESCE(SUM(distance_km), 0) as km FROM logistics_trips t
                LEFT JOIN logistics_vehicles v ON t.vehicle_id = v.id
                WHERE {where_clause}
            """, params).fetchone()['km'],
            'total_cost': db.execute(f"""
                SELECT COALESCE(SUM(actual_cost), 0) as cost FROM logistics_trips t
                LEFT JOIN logistics_vehicles v ON t.vehicle_id = v.id
                WHERE {where_clause}
            """, params).fetchone()['cost'],
            'total_stops': db.execute(f"""
                SELECT COALESCE(SUM(t.completed_stops), 0) as stops FROM logistics_trips t
                LEFT JOIN logistics_vehicles v ON t.vehicle_id = v.id
                WHERE {where_clause}
            """, params).fetchone()['stops'],
        }

        # Branches for filter
        branches = db.execute("SELECT id, name FROM branches WHERE is_active = 1 ORDER BY name").fetchall()

        return render_template('logistics/reports/trips.html',
                             title='Trip Report',
                             trips=[dict(t) for t in trips],
                             summary=summary,
                             date_from=date_from,
                             date_to=date_to,
                             status_filter=status_filter,
                             branch_id=branch_id,
                             branches=branches,
                             page=page,
                             per_page=per_page,
                             total_count=total_count,
                             total_pages=(total_count + per_page - 1) // per_page)
    finally:
        db.close()


@logistics_bp.route('/reports/dispatch')
@logistics_login_required
def report_dispatch():
    """Dispatch Report - Dispatch waves, vehicle assignments, departures."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', today.strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        status_filter = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        per_page = 25

        # Build WHERE clause
        conditions = ["date(dp.plan_date) BETWEEN ? AND ?"]
        params = [date_from, date_to]

        if status_filter:
            conditions.append("dp.status = ?")
            params.append(status_filter)

        where_clause = " AND ".join(conditions)

        # Get total count
        total_count = db.execute(f"""
            SELECT COUNT(*) as cnt FROM logistics_dispatch_plans dp
            WHERE {where_clause}
        """, params).fetchone()['cnt']

        # Get paginated dispatch plans
        offset = (page - 1) * per_page
        dispatches = db.execute(f"""
            SELECT dp.*, b.name as branch_name,
                   (SELECT COUNT(*) FROM logistics_dispatch_wave_details dwd
                    WHERE dwd.dispatch_plan_id = dp.id) as shipment_count,
                   (SELECT COUNT(*) FROM logistics_dispatch_wave_details dwd
                    WHERE dwd.dispatch_plan_id = dp.id AND dwd.status = 'completed') as completed_count
            FROM logistics_dispatch_plans dp
            LEFT JOIN branches b ON dp.branch_id = b.id
            WHERE {where_clause}
            ORDER BY dp.plan_date DESC, dp.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [per_page, offset]).fetchall()

        # Summary
        summary = {
            'total_dispatches': total_count,
            'total_shipments': db.execute(f"""
                SELECT COUNT(*) as cnt FROM logistics_dispatch_plans dp
                LEFT JOIN logistics_dispatch_wave_details dwd ON dp.id = dwd.dispatch_plan_id
                WHERE {where_clause}
            """, params).fetchone()['cnt'],
            'planned': db.execute(f"SELECT COUNT(*) as cnt FROM logistics_dispatch_plans dp WHERE {where_clause} AND dp.status = 'planned'", params).fetchone()['cnt'],
            'in_progress': db.execute(f"SELECT COUNT(*) as cnt FROM logistics_dispatch_plans dp WHERE {where_clause} AND dp.status = 'in_progress'", params).fetchone()['cnt'],
            'completed': db.execute(f"SELECT COUNT(*) as cnt FROM logistics_dispatch_plans dp WHERE {where_clause} AND dp.status = 'completed'", params).fetchone()['cnt'],
        }

        return render_template('logistics/reports/dispatch.html',
                             title='Dispatch Report',
                             dispatches=[dict(d) for d in dispatches],
                             summary=summary,
                             date_from=date_from,
                             date_to=date_to,
                             status_filter=status_filter,
                             page=page,
                             per_page=per_page,
                             total_count=total_count,
                             total_pages=(total_count + per_page - 1) // per_page)
    finally:
        db.close()


@logistics_bp.route('/reports/route-performance')
@logistics_login_required
def report_route_performance():
    """Route Performance Report - Route efficiency and cost analysis."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', today.strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        page = int(request.args.get('page', 1))
        per_page = 25

        # Get total count
        total_count = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_route_masters
            WHERE is_active = 1
        """).fetchone()['cnt']

        # Get paginated routes
        offset = (page - 1) * per_page
        routes = db.execute("""
            SELECT r.*,
                   COUNT(DISTINCT t.id) as total_trips,
                   SUM(t.distance_km) as total_distance,
                   AVG(t.actual_cost) as avg_trip_cost,
                   SUM(t.completed_stops) as total_deliveries,
                   SUM(CASE WHEN t.status = 'completed' THEN 1 ELSE 0 END) as completed_trips
            FROM logistics_route_masters r
            LEFT JOIN logistics_trips t ON r.id = t.route_id
                AND date(t.planned_departure) BETWEEN ? AND ?
            WHERE r.is_active = 1
            GROUP BY r.id
            ORDER BY total_trips DESC
            LIMIT ? OFFSET ?
        """, (date_from, date_to, per_page, offset)).fetchall()

        # Summary
        summary = {
            'total_routes': total_count,
            'active_routes': db.execute("SELECT COUNT(*) as cnt FROM logistics_route_masters WHERE is_active = 1").fetchone()['cnt'],
            'total_trips': db.execute("""
                SELECT COUNT(*) as cnt FROM logistics_trips t
                LEFT JOIN logistics_route_masters r ON t.route_id = r.id
                WHERE r.is_active = 1 AND date(t.planned_departure) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['cnt'],
            'total_distance': db.execute("""
                SELECT COALESCE(SUM(t.distance_km), 0) as km FROM logistics_trips t
                LEFT JOIN logistics_route_masters r ON t.route_id = r.id
                WHERE r.is_active = 1 AND date(t.planned_departure) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['km'],
        }

        return render_template('logistics/reports/route_performance.html',
                             title='Route Performance Report',
                             routes=[dict(r) for r in routes],
                             summary=summary,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             per_page=per_page,
                             total_count=total_count,
                             total_pages=(total_count + per_page - 1) // per_page)
    finally:
        db.close()


@logistics_bp.route('/reports/on-time-delivery')
@logistics_login_required
def report_on_time_delivery():
    """On-Time Delivery Report - Delivery punctuality metrics."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', today.strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        page = int(request.args.get('page', 1))
        per_page = 25

        # Build WHERE clause
        conditions = ["date(s.actual_delivery) BETWEEN ? AND ?", "s.status = 'delivered'"]
        params = [date_from, date_to]
        where_clause = " AND ".join(conditions)

        # Get totals
        total_delivered = db.execute(f"""
            SELECT COUNT(*) as cnt FROM logistics_shipments s
            WHERE {where_clause}
        """, params).fetchone()['cnt']

        on_time = db.execute(f"""
            SELECT COUNT(*) as cnt FROM logistics_shipments s
            WHERE {where_clause} AND s.actual_delivery <= s.sla_target
        """, params).fetchone()['cnt']

        late = total_delivered - on_time
        on_time_rate = round((on_time / total_delivered * 100) if total_delivered > 0 else 0, 1)

        # Get paginated deliveries
        offset = (page - 1) * per_page
        deliveries = db.execute(f"""
            SELECT s.*, d.full_name as driver_name, v.plate_number,
                   c.name as customer_name,
                   ROUND((julianday(s.actual_delivery) - julianday(s.sla_target)) * 24 * 60) as delay_minutes
            FROM logistics_shipments s
            LEFT JOIN logistics_drivers d ON s.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            WHERE {where_clause}
            ORDER BY s.actual_delivery DESC
            LIMIT ? OFFSET ?
        """, params + [per_page, offset]).fetchall()

        # Summary
        summary = {
            'total_delivered': total_delivered,
            'on_time': on_time,
            'late': late,
            'on_time_rate': on_time_rate,
            'avg_delay_minutes': db.execute(f"""
                SELECT AVG((julianday(s.actual_delivery) - julianday(s.sla_target)) * 24 * 60) as avg_delay
                FROM logistics_shipments s
                WHERE {where_clause} AND s.actual_delivery > s.sla_target
            """, params).fetchone()['avg_delay'] or 0,
        }

        return render_template('logistics/reports/on_time_delivery.html',
                             title='On-Time Delivery Report',
                             deliveries=[dict(d) for d in deliveries],
                             summary=summary,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             per_page=per_page,
                             total_count=total_delivered,
                             total_pages=(total_delivered + per_page - 1) // per_page)
    finally:
        db.close()


@logistics_bp.route('/reports/delay-analysis')
@logistics_login_required
def report_delay_analysis():
    """Delay Analysis Report - Delay reasons and trends."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', today.strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        page = int(request.args.get('page', 1))
        per_page = 25

        # Delay breakdown by reason
        delay_reasons = db.execute("""
            SELECT failure_reason as reason, COUNT(*) as count
            FROM logistics_trip_stops
            WHERE status = 'failed' AND failure_reason IS NOT NULL
                AND date(created_at) BETWEEN ? AND ?
            GROUP BY failure_reason
            ORDER BY count DESC
        """, (date_from, date_to)).fetchall()

        # Avg delay by route
        delay_by_route = db.execute("""
            SELECT r.route_name, r.route_code,
                   AVG((julianday(s.actual_delivery) - julianday(s.sla_target)) * 24 * 60) as avg_delay_minutes,
                   COUNT(*) as total_delays
            FROM logistics_shipments s
            LEFT JOIN logistics_route_masters r ON s.route_id = r.id
            WHERE s.status = 'delivered' AND s.actual_delivery > s.sla_target
                AND date(s.actual_delivery) BETWEEN ? AND ?
            GROUP BY r.id
            HAVING total_delays > 0
            ORDER BY avg_delay_minutes DESC
        """, (date_from, date_to)).fetchall()

        # Avg delay by driver
        delay_by_driver = db.execute("""
            SELECT d.full_name, d.driver_code,
                   AVG((julianday(s.actual_delivery) - julianday(s.sla_target)) * 24 * 60) as avg_delay_minutes,
                   COUNT(*) as total_delays
            FROM logistics_shipments s
            LEFT JOIN logistics_drivers d ON s.driver_id = d.id
            WHERE s.status = 'delivered' AND s.actual_delivery > s.sla_target
                AND date(s.actual_delivery) BETWEEN ? AND ?
            GROUP BY d.id
            HAVING total_delays > 0
            ORDER BY avg_delay_minutes DESC
        """, (date_from, date_to)).fetchall()

        # Daily trend
        daily_trend = db.execute("""
            SELECT date(s.actual_delivery) as day,
                   COUNT(*) as total_deliveries,
                   SUM(CASE WHEN s.actual_delivery > s.sla_target THEN 1 ELSE 0 END) as late_count,
                   AVG(CASE WHEN s.actual_delivery > s.sla_target
                       THEN (julianday(s.actual_delivery) - julianday(s.sla_target)) * 24 * 60
                       ELSE 0 END) as avg_delay
            FROM logistics_shipments s
            WHERE s.status = 'delivered' AND date(s.actual_delivery) BETWEEN ? AND ?
            GROUP BY day
            ORDER BY day
        """, (date_from, date_to)).fetchall()

        # Summary
        summary = {
            'total_delays': sum([r['count'] for r in delay_reasons]),
            'total_late_deliveries': db.execute("""
                SELECT COUNT(*) as cnt FROM logistics_shipments s
                WHERE status = 'delivered' AND actual_delivery > sla_target
                AND date(actual_delivery) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['cnt'],
            'unique_reasons': len(delay_reasons),
        }

        return render_template('logistics/reports/delay_analysis.html',
                             title='Delay Analysis Report',
                             delay_reasons=[dict(r) for r in delay_reasons],
                             delay_by_route=[dict(r) for r in delay_by_route],
                             delay_by_driver=[dict(r) for r in delay_by_driver],
                             daily_trend=[dict(r) for r in daily_trend],
                             summary=summary,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             per_page=per_page)
    finally:
        db.close()


@logistics_bp.route('/reports/vehicle-utilization')
@logistics_login_required
def report_vehicle_utilization():
    """Vehicle Utilization Report - Fleet usage and capacity."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', today.strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        page = int(request.args.get('page', 1))
        per_page = 25

        # Get total count
        total_count = db.execute("SELECT COUNT(*) as cnt FROM logistics_vehicles WHERE status = 'active'").fetchone()['cnt']

        # Get paginated vehicle utilization
        offset = (page - 1) * per_page
        vehicles = db.execute("""
            SELECT v.*,
                   COUNT(DISTINCT t.id) as total_trips,
                   SUM(t.distance_km) as total_km,
                   SUM(t.fuel_cost) as total_fuel_cost,
                   COUNT(DISTINCT m.id) as maintenance_events,
                   AVG(t.distance_km) as avg_km_per_trip
            FROM logistics_vehicles v
            LEFT JOIN logistics_trips t ON v.id = t.vehicle_id
                AND date(t.planned_departure) BETWEEN ? AND ?
            LEFT JOIN logistics_vehicle_maintenance m ON v.id = m.vehicle_id
                AND date(m.scheduled_date) BETWEEN ? AND ?
            WHERE v.status = 'active'
            GROUP BY v.id
            ORDER BY total_km DESC
            LIMIT ? OFFSET ?
        """, (date_from, date_to, date_from, date_to, per_page, offset)).fetchall()

        # Summary
        summary = {
            'total_vehicles': total_count,
            'active_vehicles': db.execute("""
                SELECT COUNT(*) as cnt FROM logistics_vehicles
                WHERE status = 'active' AND availability = 'available'
            """).fetchone()['cnt'],
            'total_km': db.execute("""
                SELECT COALESCE(SUM(distance_km), 0) as km FROM logistics_trips
                WHERE date(planned_departure) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['km'],
            'avg_utilization': db.execute("""
                SELECT AVG( CASE
                    WHEN v.load_capacity_kg > 0
                    THEN (SELECT SUM(sl.weight) FROM logistics_shipments s2
                          LEFT JOIN logistics_shipment_lines sl ON s2.id = sl.shipment_id
                          WHERE s2.vehicle_id = v.id AND date(s2.created_at) BETWEEN ? AND ?)
                          / (COUNT(DISTINCT t.id) * v.load_capacity_kg) * 100
                    ELSE 0 END ) as util
                FROM logistics_vehicles v
                LEFT JOIN logistics_trips t ON v.id = t.vehicle_id
                WHERE v.status = 'active'
            """, (date_from, date_to)).fetchone()['util'] or 0,
        }

        return render_template('logistics/reports/vehicle_utilization.html',
                             title='Vehicle Utilization Report',
                             vehicles=[dict(v) for v in vehicles],
                             summary=summary,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             per_page=per_page,
                             total_count=total_count,
                             total_pages=(total_count + per_page - 1) // per_page)
    finally:
        db.close()


@logistics_bp.route('/reports/fuel-cost')
@logistics_login_required
def report_fuel_cost():
    """Fuel/Cost Report - Fuel consumption, tolls, and misc costs."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', today.strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        page = int(request.args.get('page', 1))
        per_page = 25

        # Get trip expenses with fuel, tolls, etc.
        offset = (page - 1) * per_page
        expenses = db.execute("""
            SELECT t.id, t.trip_code, t.trip_name, t.planned_departure,
                   d.full_name as driver_name, v.plate_number,
                   te.expense_category, te.expense_type, te.amount,
                   te.created_at
            FROM logistics_trip_expenses te
            JOIN logistics_trips t ON te.trip_id = t.id
            LEFT JOIN logistics_drivers d ON t.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON t.vehicle_id = v.id
            WHERE date(t.planned_departure) BETWEEN ? AND ?
            ORDER BY te.created_at DESC
            LIMIT ? OFFSET ?
        """, (date_from, date_to, per_page, offset)).fetchall()

        # Total count
        total_count = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_trip_expenses te
            JOIN logistics_trips t ON te.trip_id = t.id
            WHERE date(t.planned_departure) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['cnt']

        # Summary by category
        summary = {
            'fuel_cost': db.execute("""
                SELECT COALESCE(SUM(te.amount), 0) as total
                FROM logistics_trip_expenses te
                JOIN logistics_trips t ON te.trip_id = t.id
                WHERE te.expense_category = 'fuel'
                AND date(t.planned_departure) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['total'],
            'tolls_cost': db.execute("""
                SELECT COALESCE(SUM(te.amount), 0) as total
                FROM logistics_trip_expenses te
                JOIN logistics_trips t ON te.trip_id = t.id
                WHERE te.expense_type = 'Tolls'
                AND date(t.planned_departure) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['total'],
            'parking_cost': db.execute("""
                SELECT COALESCE(SUM(te.amount), 0) as total
                FROM logistics_trip_expenses te
                JOIN logistics_trips t ON te.trip_id = t.id
                WHERE te.expense_type = 'Parking'
                AND date(t.planned_departure) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['total'],
            'total_cost': db.execute("""
                SELECT COALESCE(SUM(te.amount), 0) as total
                FROM logistics_trip_expenses te
                JOIN logistics_trips t ON te.trip_id = t.id
                WHERE date(t.planned_departure) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['total'],
        }

        return render_template('logistics/reports/fuel_cost.html',
                             title='Fuel / Cost Report',
                             expenses=[dict(e) for e in expenses],
                             summary=summary,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             per_page=per_page,
                             total_count=total_count,
                             total_pages=(total_count + per_page - 1) // per_page)
    finally:
        db.close()


@logistics_bp.route('/reports/pod-completion')
@logistics_login_required
def report_pod_completion():
    """POD Completion Report - Proof of delivery status."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', today.strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        page = int(request.args.get('page', 1))
        per_page = 25

        # Total delivered shipments
        total_delivered = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_shipments
            WHERE status IN ('delivered', 'partially_delivered')
            AND date(actual_delivery) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['cnt']

        # POD completed
        pod_completed = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_pod_records
            WHERE date(delivery_timestamp) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['cnt']

        # POD pending
        pod_pending = total_delivered - pod_completed

        # Paginated POD records
        offset = (page - 1) * per_page
        pods = db.execute("""
            SELECT p.*, s.shipment_code, d.full_name as driver_name,
                   c.name as customer_name
            FROM logistics_pod_records p
            LEFT JOIN logistics_shipments s ON p.shipment_id = s.id
            LEFT JOIN logistics_drivers d ON p.driver_id = d.id
            LEFT JOIN sdad_customers c ON p.customer_id = c.id
            WHERE date(p.delivery_timestamp) BETWEEN ? AND ?
            ORDER BY p.delivery_timestamp DESC
            LIMIT ? OFFSET ?
        """, (date_from, date_to, per_page, offset)).fetchall()

        # Summary
        summary = {
            'total_delivered': total_delivered,
            'pod_complete': pod_completed,
            'pod_pending': pod_pending,
            'completion_rate': round((pod_completed / total_delivered * 100) if total_delivered > 0 else 0, 1),
        }

        return render_template('logistics/reports/pod_completion.html',
                             title='POD Completion Report',
                             pods=[dict(p) for p in pods],
                             summary=summary,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             per_page=per_page,
                             total_count=total_delivered,
                             total_pages=(total_delivered + per_page - 1) // per_page)
    finally:
        db.close()


@logistics_bp.route('/reports/failed-delivery')
@logistics_login_required
def report_failed_delivery():
    """Failed Delivery Report - Failed delivery analysis."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', today.strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        page = int(request.args.get('page', 1))
        per_page = 25

        # Failed deliveries count
        total_failed = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_shipments
            WHERE status = 'failed_delivery'
            AND date(updated_at) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['cnt']

        # Failed by reason
        by_reason = db.execute("""
            SELECT failure_reason as reason, COUNT(*) as count
            FROM logistics_trip_stops
            WHERE status = 'failed' AND failure_reason IS NOT NULL
            AND date(created_at) BETWEEN ? AND ?
            GROUP BY failure_reason
            ORDER BY count DESC
        """, (date_from, date_to)).fetchall()

        # Paginated failed deliveries
        offset = (page - 1) * per_page
        failed = db.execute("""
            SELECT s.*, d.full_name as driver_name, v.plate_number,
                   c.name as customer_name, r.route_name
            FROM logistics_shipments s
            LEFT JOIN logistics_drivers d ON s.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            LEFT JOIN logistics_route_masters r ON s.route_id = r.id
            WHERE s.status = 'failed_delivery'
            AND date(s.updated_at) BETWEEN ? AND ?
            ORDER BY s.updated_at DESC
            LIMIT ? OFFSET ?
        """, (date_from, date_to, per_page, offset)).fetchall()

        # Summary
        summary = {
            'total_failed': total_failed,
            'unique_reasons': len(by_reason),
            'rerouted': db.execute("""
                SELECT COUNT(*) as cnt FROM logistics_shipments
                WHERE status IN ('scheduled', 'assigned') AND is_rescheduled = 1
                AND date(updated_at) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['cnt'],
        }

        return render_template('logistics/reports/failed_delivery.html',
                             title='Failed Delivery Report',
                             failed=[dict(f) for f in failed],
                             by_reason=[dict(r) for r in by_reason],
                             summary=summary,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             per_page=per_page,
                             total_count=total_failed,
                             total_pages=(total_failed + per_page - 1) // per_page)
    finally:
        db.close()


@logistics_bp.route('/reports/stop-activity')
@logistics_login_required
def report_stop_activity():
    """Stop Activity Report - Stop completion and arrival times."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', today.strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        page = int(request.args.get('page', 1))
        per_page = 25

        # Total stops
        total_stops = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_trip_stops ts
            JOIN logistics_trips t ON ts.trip_id = t.id
            WHERE date(t.planned_departure) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['cnt']

        # Paginated stops
        offset = (page - 1) * per_page
        stops = db.execute("""
            SELECT ts.*, t.trip_code, t.planned_departure,
                   s.shipment_code, c.name as customer_name,
                   d.full_name as driver_name
            FROM logistics_trip_stops ts
            JOIN logistics_trips t ON ts.trip_id = t.id
            LEFT JOIN logistics_shipments s ON ts.shipment_id = s.id
            LEFT JOIN sdad_customers c ON ts.customer_id = c.id
            LEFT JOIN logistics_drivers d ON t.driver_id = d.id
            WHERE date(t.planned_departure) BETWEEN ? AND ?
            ORDER BY t.planned_departure DESC, ts.stop_sequence
            LIMIT ? OFFSET ?
        """, (date_from, date_to, per_page, offset)).fetchall()

        # Summary by status
        summary = {
            'total_stops': total_stops,
            'completed': db.execute("""
                SELECT COUNT(*) as cnt FROM logistics_trip_stops ts
                JOIN logistics_trips t ON ts.trip_id = t.id
                WHERE ts.status = 'completed'
                AND date(t.planned_departure) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['cnt'],
            'failed': db.execute("""
                SELECT COUNT(*) as cnt FROM logistics_trip_stops ts
                JOIN logistics_trips t ON ts.trip_id = t.id
                WHERE ts.status = 'failed'
                AND date(t.planned_departure) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['cnt'],
            'pending': db.execute("""
                SELECT COUNT(*) as cnt FROM logistics_trip_stops ts
                JOIN logistics_trips t ON ts.trip_id = t.id
                WHERE ts.status = 'pending'
                AND date(t.planned_departure) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['cnt'],
        }

        return render_template('logistics/reports/stop_activity.html',
                             title='Stop Activity Report',
                             stops=[dict(s) for s in stops],
                             summary=summary,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             per_page=per_page,
                             total_count=total_stops,
                             total_pages=(total_stops + per_page - 1) // per_page)
    finally:
        db.close()


@logistics_bp.route('/reports/delivery-scheduling')
@logistics_login_required
def report_delivery_scheduling():
    """Delivery Scheduling Report - Slot utilization and adherence."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', today.strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        page = int(request.args.get('page', 1))
        per_page = 25

        # Get schedules
        total_schedules = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_delivery_schedules
            WHERE date(scheduled_date) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['cnt']

        # Paginated schedules
        offset = (page - 1) * per_page
        schedules = db.execute("""
            SELECT ds.*, s.shipment_code, c.name as customer_name,
                   v.plate_number, d.full_name as driver_name,
                   dd.dock_name
            FROM logistics_delivery_schedules ds
            LEFT JOIN logistics_shipments s ON ds.shipment_id = s.id
            LEFT JOIN sdad_customers c ON ds.customer_id = c.id
            LEFT JOIN logistics_vehicles v ON ds.vehicle_id = v.id
            LEFT JOIN logistics_drivers d ON ds.driver_id = d.id
            LEFT JOIN logistics_dock_doors dd ON ds.dock_door_id = dd.id
            WHERE date(ds.scheduled_date) BETWEEN ? AND ?
            ORDER BY ds.scheduled_date, ds.scheduled_time_from
            LIMIT ? OFFSET ?
        """, (date_from, date_to, per_page, offset)).fetchall()

        # Summary
        summary = {
            'total_schedules': total_schedules,
            'scheduled': db.execute("""
                SELECT COUNT(*) as cnt FROM logistics_delivery_schedules
                WHERE status = 'scheduled' AND date(scheduled_date) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['cnt'],
            'completed': db.execute("""
                SELECT COUNT(*) as cnt FROM logistics_delivery_schedules
                WHERE status = 'completed' AND date(scheduled_date) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['cnt'],
            'rescheduled': db.execute("""
                SELECT COUNT(*) as cnt FROM logistics_delivery_schedules
                WHERE is_rescheduled = 1 AND date(scheduled_date) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['cnt'],
        }

        return render_template('logistics/reports/delivery_scheduling.html',
                             title='Delivery Scheduling Report',
                             schedules=[dict(s) for s in schedules],
                             summary=summary,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             per_page=per_page,
                             total_count=total_schedules,
                             total_pages=(total_schedules + per_page - 1) // per_page)
    finally:
        db.close()


@logistics_bp.route('/reports/dock-appointment')
@logistics_login_required
def report_dock_appointment():
    """Dock Appointment Report - Dock door utilization."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', today.strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        page = int(request.args.get('page', 1))
        per_page = 25

        # Get dock doors
        total_doors = db.execute("SELECT COUNT(*) as cnt FROM logistics_dock_doors WHERE is_active = 1").fetchone()['cnt']

        # Get appointments per dock
        offset = (page - 1) * per_page
        docks = db.execute("""
            SELECT dd.*,
                   COUNT(ds.id) as scheduled_appointments,
                   SUM(CASE WHEN ds.status = 'completed' THEN 1 ELSE 0 END) as completed_appointments,
                   SUM(CASE WHEN ds.status = 'cancelled' THEN 1 ELSE 0 END) as missed_appointments
            FROM logistics_dock_doors dd
            LEFT JOIN logistics_delivery_schedules ds ON dd.id = ds.dock_door_id
                AND date(ds.scheduled_date) BETWEEN ? AND ?
            WHERE dd.is_active = 1
            GROUP BY dd.id
            ORDER BY scheduled_appointments DESC
            LIMIT ? OFFSET ?
        """, (date_from, date_to, per_page, offset)).fetchall()

        # Summary
        summary = {
            'total_doors': total_doors,
            'total_appointments': db.execute("""
                SELECT COUNT(*) as cnt FROM logistics_delivery_schedules
                WHERE date(scheduled_date) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['cnt'],
            'completed': db.execute("""
                SELECT COUNT(*) as cnt FROM logistics_delivery_schedules
                WHERE status = 'completed' AND date(scheduled_date) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['cnt'],
        }

        return render_template('logistics/reports/dock_appointment.html',
                             title='Dock Appointment Report',
                             docks=[dict(d) for d in docks],
                             summary=summary,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             per_page=per_page,
                             total_count=total_doors,
                             total_pages=(total_doors + per_page - 1) // per_page)
    finally:
        db.close()


@logistics_bp.route('/reports/trip-cost')
@logistics_login_required
def report_trip_cost():
    """Trip Cost Report - Per-trip cost breakdown."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', today.strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        page = int(request.args.get('page', 1))
        per_page = 25

        # Total trips
        total_trips = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_trips
            WHERE date(planned_departure) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['cnt']

        # Paginated trips with costs
        offset = (page - 1) * per_page
        trips = db.execute("""
            SELECT t.*, d.full_name as driver_name, v.plate_number, r.route_name,
                   (t.fuel_cost + t.tolls_cost + t.driver_allowance) as total_trip_cost,
                   CASE WHEN t.distance_km > 0
                        THEN (t.fuel_cost + t.tolls_cost + t.driver_allowance) / t.distance_km
                        ELSE 0 END as cost_per_km
            FROM logistics_trips t
            LEFT JOIN logistics_drivers d ON t.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON t.vehicle_id = v.id
            LEFT JOIN logistics_route_masters r ON t.route_id = r.id
            WHERE date(t.planned_departure) BETWEEN ? AND ?
            ORDER BY t.actual_cost DESC
            LIMIT ? OFFSET ?
        """, (date_from, date_to, per_page, offset)).fetchall()

        # Summary
        summary = {
            'total_trips': total_trips,
            'total_cost': db.execute("""
                SELECT COALESCE(SUM(fuel_cost + tolls_cost + driver_allowance), 0) as total
                FROM logistics_trips
                WHERE date(planned_departure) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['total'],
            'total_distance': db.execute("""
                SELECT COALESCE(SUM(distance_km), 0) as km
                FROM logistics_trips
                WHERE date(planned_departure) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['km'],
            'avg_cost_per_trip': db.execute("""
                SELECT COALESCE(AVG(fuel_cost + tolls_cost + driver_allowance), 0) as avg
                FROM logistics_trips
                WHERE date(planned_departure) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['avg'],
        }

        return render_template('logistics/reports/trip_cost.html',
                             title='Trip Cost Report',
                             trips=[dict(t) for t in trips],
                             summary=summary,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             per_page=per_page,
                             total_count=total_trips,
                             total_pages=(total_trips + per_page - 1) // per_page)
    finally:
        db.close()


@logistics_bp.route('/reports/cost-per-delivery')
@logistics_login_required
def report_cost_per_delivery():
    """Cost per Delivery Report - Delivery zone cost analysis."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', today.strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        page = int(request.args.get('page', 1))
        per_page = 25

        # Get cost per zone
        total_zones = db.execute("SELECT COUNT(*) as cnt FROM logistics_service_zones WHERE is_active = 1").fetchone()['cnt']

        offset = (page - 1) * per_page
        zones = db.execute("""
            SELECT sz.zone_name, sz.zone_code, sz.city,
                   COUNT(DISTINCT s.id) as total_deliveries,
                   COALESCE(SUM(c.amount), 0) as total_cost,
                   CASE WHEN COUNT(DISTINCT s.id) > 0
                        THEN COALESCE(SUM(c.amount), 0) / COUNT(DISTINCT s.id)
                        ELSE 0 END as avg_cost_per_delivery
            FROM logistics_service_zones sz
            LEFT JOIN logistics_shipments s ON s.delivery_address LIKE '%' || sz.zone_code || '%'
                AND s.status = 'delivered'
                AND date(s.actual_delivery) BETWEEN ? AND ?
            LEFT JOIN logistics_cost_entries c ON s.id = c.shipment_id
            WHERE sz.is_active = 1
            GROUP BY sz.id
            ORDER BY avg_cost_per_delivery DESC
            LIMIT ? OFFSET ?
        """, (date_from, date_to, per_page, offset)).fetchall()

        # Summary
        summary = {
            'total_zones': total_zones,
            'total_deliveries': db.execute("""
                SELECT COUNT(*) as cnt FROM logistics_shipments
                WHERE status = 'delivered'
                AND date(actual_delivery) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['cnt'],
            'total_cost': db.execute("""
                SELECT COALESCE(SUM(c.amount), 0) as total
                FROM logistics_cost_entries c
                JOIN logistics_shipments s ON c.shipment_id = s.id
                WHERE s.status = 'delivered'
                AND date(s.actual_delivery) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['total'],
        }

        return render_template('logistics/reports/cost_per_delivery.html',
                             title='Cost per Delivery Report',
                             zones=[dict(z) for z in zones],
                             summary=summary,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             per_page=per_page,
                             total_count=total_zones,
                             total_pages=(total_zones + per_page - 1) // per_page)
    finally:
        db.close()


@logistics_bp.route('/reports/exception')
@logistics_login_required
def report_exception():
    """Exception Report - Incidents and exceptions."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', today.strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        page = int(request.args.get('page', 1))
        per_page = 25

        # Total incidents
        total_incidents = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_incidents
            WHERE date(incident_date) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['cnt']

        # By type
        by_type = db.execute("""
            SELECT incident_type, COUNT(*) as count,
                   SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_count,
                   SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved_count
            FROM logistics_incidents
            WHERE date(incident_date) BETWEEN ? AND ?
            GROUP BY incident_type
            ORDER BY count DESC
        """, (date_from, date_to)).fetchall()

        # Paginated incidents
        offset = (page - 1) * per_page
        incidents = db.execute("""
            SELECT i.*, s.shipment_code, d.full_name as driver_name,
                   v.plate_number
            FROM logistics_incidents i
            LEFT JOIN logistics_shipments s ON i.shipment_id = s.id
            LEFT JOIN logistics_drivers d ON i.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON i.vehicle_id = v.id
            WHERE date(i.incident_date) BETWEEN ? AND ?
            ORDER BY i.incident_date DESC
            LIMIT ? OFFSET ?
        """, (date_from, date_to, per_page, offset)).fetchall()

        # Summary
        summary = {
            'total_incidents': total_incidents,
            'open': db.execute("""
                SELECT COUNT(*) as cnt FROM logistics_incidents
                WHERE status = 'open' AND date(incident_date) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['cnt'],
            'resolved': db.execute("""
                SELECT COUNT(*) as cnt FROM logistics_incidents
                WHERE status = 'resolved' AND date(incident_date) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['cnt'],
        }

        return render_template('logistics/reports/exception.html',
                             title='Exception Report',
                             incidents=[dict(i) for i in incidents],
                             by_type=[dict(t) for t in by_type],
                             summary=summary,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             per_page=per_page,
                             total_count=total_incidents,
                             total_pages=(total_incidents + per_page - 1) // per_page)
    finally:
        db.close()


@logistics_bp.route('/reports/branch-tms')
@logistics_login_required
def report_branch_tms():
    """Branch TMS Report - Branch-level TMS metrics."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', today.strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        page = int(request.args.get('page', 1))
        per_page = 25

        # Get branches
        total_branches = db.execute("SELECT COUNT(*) as cnt FROM branches WHERE is_active = 1").fetchone()['cnt']

        offset = (page - 1) * per_page
        branches_data = db.execute("""
            SELECT b.*,
                   COUNT(DISTINCT t.id) as total_trips,
                   COUNT(DISTINCT s.id) as total_deliveries,
                   SUM(CASE WHEN s.status = 'delivered' AND s.actual_delivery <= s.sla_target THEN 1 ELSE 0 END) as on_time_deliveries,
                   COALESCE(SUM(c.amount), 0) as total_cost,
                   COUNT(DISTINCT v.id) as active_vehicles,
                   COUNT(DISTINCT d.id) as active_drivers
            FROM branches b
            LEFT JOIN logistics_trips t ON b.id = t.route_id
                AND date(t.planned_departure) BETWEEN ? AND ?
            LEFT JOIN logistics_shipments s ON b.id = s.branch_id
                AND date(s.created_at) BETWEEN ? AND ?
            LEFT JOIN logistics_cost_entries c ON s.id = c.shipment_id
            LEFT JOIN logistics_vehicles v ON b.id = v.branch_id AND v.status = 'active'
            LEFT JOIN logistics_drivers d ON b.id = d.branch_id AND d.status = 'active'
            WHERE b.is_active = 1
            GROUP BY b.id
            ORDER BY total_deliveries DESC
            LIMIT ? OFFSET ?
        """, (date_from, date_to, date_from, date_to, per_page, offset)).fetchall()

        # Summary
        summary = {
            'total_branches': total_branches,
            'total_trips': db.execute("""
                SELECT COUNT(*) as cnt FROM logistics_trips
                WHERE date(planned_departure) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['cnt'],
            'total_deliveries': db.execute("""
                SELECT COUNT(*) as cnt FROM logistics_shipments
                WHERE date(created_at) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['cnt'],
        }

        return render_template('logistics/reports/branch_tms.html',
                             title='Branch TMS Report',
                             branches=[dict(b) for b in branches_data],
                             summary=summary,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             per_page=per_page,
                             total_count=total_branches,
                             total_pages=(total_branches + per_page - 1) // per_page)
    finally:
        db.close()


@logistics_bp.route('/reports/entity-tms')
@logistics_login_required
def report_entity_tms():
    """Entity TMS Report - Company/entity aggregate metrics."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', today.strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))

        # Get company-level aggregates
        company_id = user.get('company_id')

        # Shipments
        total_shipments = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_shipments
            WHERE date(created_at) BETWEEN ? AND ?
            AND (company_id = ? OR ? IS NULL)
        """, (date_from, date_to, company_id, company_id)).fetchone()['cnt']

        delivered = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_shipments
            WHERE status = 'delivered' AND date(actual_delivery) BETWEEN ? AND ?
            AND (company_id = ? OR ? IS NULL)
        """, (date_from, date_to, company_id, company_id)).fetchone()['cnt']

        on_time = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_shipments
            WHERE status = 'delivered' AND actual_delivery <= sla_target
            AND date(actual_delivery) BETWEEN ? AND ?
            AND (company_id = ? OR ? IS NULL)
        """, (date_from, date_to, company_id, company_id)).fetchone()['cnt']

        # Trips
        total_trips = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_trips
            WHERE date(planned_departure) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['cnt']

        # Costs
        total_cost = db.execute("""
            SELECT COALESCE(SUM(c.amount), 0) as total
            FROM logistics_cost_entries c
            JOIN logistics_shipments s ON c.shipment_id = s.id
            WHERE date(s.created_at) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['total']

        # Vehicles & Drivers
        active_vehicles = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_vehicles WHERE status = 'active'
        """).fetchone()['cnt']

        active_drivers = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_drivers WHERE status = 'active'
        """).fetchone()['cnt']

        # Branch breakdown
        branch_breakdown = db.execute("""
            SELECT b.name as branch_name,
                   COUNT(DISTINCT s.id) as total_deliveries,
                   SUM(CASE WHEN s.status = 'delivered' THEN 1 ELSE 0 END) as delivered,
                   COALESCE(SUM(c.amount), 0) as total_cost
            FROM branches b
            LEFT JOIN logistics_shipments s ON b.id = s.branch_id
                AND date(s.created_at) BETWEEN ? AND ?
            LEFT JOIN logistics_cost_entries c ON s.id = c.shipment_id
            WHERE b.is_active = 1
            GROUP BY b.id
            ORDER BY total_deliveries DESC
        """, (date_from, date_to)).fetchall()

        summary = {
            'total_shipments': total_shipments,
            'delivered': delivered,
            'on_time': on_time,
            'on_time_rate': round((on_time / delivered * 100) if delivered > 0 else 0, 1),
            'total_trips': total_trips,
            'total_cost': total_cost,
            'active_vehicles': active_vehicles,
            'active_drivers': active_drivers,
        }

        return render_template('logistics/reports/entity_tms.html',
                             title='Entity TMS Report',
                             summary=summary,
                             branch_breakdown=[dict(b) for b in branch_breakdown],
                             date_from=date_from,
                             date_to=date_to)
    finally:
        db.close()


@logistics_bp.route('/reports/carbon-emission')
@logistics_login_required
def report_carbon_emission():
    """Carbon Emission Report - CO2 emissions and environmental impact."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', today.strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        page = int(request.args.get('page', 1))
        per_page = 25

        # Emission factor: diesel ~2.68 kg CO2/liter, petrol ~2.31 kg CO2/liter
        # For trucks, average ~0.25 kg CO2/km

        # Get vehicle emissions
        total_count = db.execute("SELECT COUNT(*) as cnt FROM logistics_vehicles WHERE status = 'active'").fetchone()['cnt']

        offset = (page - 1) * per_page
        vehicles = db.execute("""
            SELECT v.*,
                   COUNT(t.id) as total_trips,
                   SUM(t.distance_km) as total_km,
                   SUM(t.fuel_cost) as fuel_cost,
                   ROUND(SUM(t.distance_km) * 0.25, 2) as estimated_co2_kg
            FROM logistics_vehicles v
            LEFT JOIN logistics_trips t ON v.id = t.vehicle_id
                AND date(t.planned_departure) BETWEEN ? AND ?
            WHERE v.status = 'active'
            GROUP BY v.id
            ORDER BY total_km DESC
            LIMIT ? OFFSET ?
        """, (date_from, date_to, per_page, offset)).fetchall()

        # Summary
        summary = {
            'total_vehicles': total_count,
            'total_km': db.execute("""
                SELECT COALESCE(SUM(distance_km), 0) as km FROM logistics_trips
                WHERE date(planned_departure) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['km'],
            'total_co2_kg': db.execute("""
                SELECT ROUND(COALESCE(SUM(distance_km), 0) * 0.25, 2) as co2 FROM logistics_trips
                WHERE date(planned_departure) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()['co2'],
            'avg_co2_per_km': 0.25,
        }

        return render_template('logistics/reports/carbon_emission.html',
                             title='Carbon Emission Report',
                             vehicles=[dict(v) for v in vehicles],
                             summary=summary,
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             per_page=per_page,
                             total_count=total_count,
                             total_pages=(total_count + per_page - 1) // per_page)
    finally:
        db.close()


@logistics_bp.route('/reports/custom')
@logistics_login_required
def report_custom():
    """Custom Report Builder."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', today.strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        report_type = request.args.get('report_type', 'shipments')
        columns = request.args.get('columns', '')
        page = int(request.args.get('page', 1))
        per_page = 50

        # Available tables and columns
        available_reports = {
            'shipments': {
                'table': 'logistics_shipments',
                'columns': ['shipment_code', 'status', 'priority', 'shipment_type', 'customer_id', 'created_at', 'planned_date', 'dispatch_date', 'actual_delivery', 'sla_target', 'driver_id', 'vehicle_id', 'route_id'],
                'display_names': ['Code', 'Status', 'Priority', 'Type', 'Customer', 'Created', 'Planned', 'Dispatched', 'Delivered', 'SLA', 'Driver', 'Vehicle', 'Route']
            },
            'trips': {
                'table': 'logistics_trips',
                'columns': ['trip_code', 'status', 'planned_departure', 'actual_departure', 'distance_km', 'total_stops', 'completed_stops', 'fuel_cost', 'tolls_cost', 'driver_id', 'vehicle_id'],
                'display_names': ['Trip Code', 'Status', 'Planned', 'Actual Departure', 'Distance', 'Total Stops', 'Completed', 'Fuel Cost', 'Tolls', 'Driver', 'Vehicle']
            },
            'incidents': {
                'table': 'logistics_incidents',
                'columns': ['incident_number', 'incident_type', 'severity', 'status', 'incident_date', 'driver_id', 'vehicle_id', 'cost_impact'],
                'display_names': ['Number', 'Type', 'Severity', 'Status', 'Date', 'Driver', 'Vehicle', 'Cost Impact']
            }
        }

        report_config = available_reports.get(report_type, available_reports['shipments'])
        selected_columns = columns.split(',') if columns else report_config['columns']

        # Build query
        offset = (page - 1) * per_page
        col_list = ', '.join(selected_columns) if selected_columns else '*'

        rows = db.execute(f"""
            SELECT {col_list}
            FROM {report_config['table']}
            WHERE date(created_at) BETWEEN ? AND ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, (date_from, date_to, per_page, offset)).fetchall()

        total_count = db.execute(f"""
            SELECT COUNT(*) as cnt FROM {report_config['table']}
            WHERE date(created_at) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['cnt']

        return render_template('logistics/reports/custom.html',
                             title='Custom Report Builder',
                             report_config=report_config,
                             report_type=report_type,
                             available_reports=available_reports,
                             selected_columns=selected_columns,
                             rows=[dict(r) for r in rows],
                             date_from=date_from,
                             date_to=date_to,
                             page=page,
                             per_page=per_page,
                             total_count=total_count,
                             total_pages=(total_count + per_page - 1) // per_page)
    finally:
        db.close()


@logistics_bp.route('/reports/export-center')
@logistics_login_required
def report_export_center():
    """Export Center - Export reports to CSV/Excel/PDF."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', today.strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        export_type = request.args.get('type', 'shipments')
        format = request.args.get('format', 'csv')

        # Build data based on export type
        if export_type == 'shipments':
            data = db.execute("""
                SELECT s.shipment_code, s.status, s.priority, s.shipment_type,
                       s.created_at, s.planned_date, s.actual_delivery,
                       c.name as customer_name, d.full_name as driver_name,
                       v.plate_number
                FROM logistics_shipments s
                LEFT JOIN sdad_customers c ON s.customer_id = c.id
                LEFT JOIN logistics_drivers d ON s.driver_id = d.id
                LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
                WHERE date(s.created_at) BETWEEN ? AND ?
                ORDER BY s.created_at DESC
            """, (date_from, date_to)).fetchall()
            filename = f'shipments_export_{today}.{format}'

        elif export_type == 'trips':
            data = db.execute("""
                SELECT t.trip_code, t.status, t.planned_departure, t.actual_departure,
                       t.distance_km, t.total_stops, t.completed_stops,
                       t.fuel_cost, t.tolls_cost, t.actual_cost,
                       d.full_name as driver_name, v.plate_number
                FROM logistics_trips t
                LEFT JOIN logistics_drivers d ON t.driver_id = d.id
                LEFT JOIN logistics_vehicles v ON t.vehicle_id = v.id
                WHERE date(t.planned_departure) BETWEEN ? AND ?
                ORDER BY t.planned_departure DESC
            """, (date_from, date_to)).fetchall()
            filename = f'trips_export_{today}.{format}'

        elif export_type == 'incidents':
            data = db.execute("""
                SELECT i.incident_number, i.incident_type, i.severity, i.status,
                       i.incident_date, i.description, i.cost_impact,
                       d.full_name as driver_name, v.plate_number
                FROM logistics_incidents i
                LEFT JOIN logistics_drivers d ON i.driver_id = d.id
                LEFT JOIN logistics_vehicles v ON i.vehicle_id = v.id
                WHERE date(i.incident_date) BETWEEN ? AND ?
                ORDER BY i.incident_date DESC
            """, (date_from, date_to)).fetchall()
            filename = f'incidents_export_{today}.{format}'

        else:
            data = []
            filename = f'export_{today}.{format}'

        # Generate export
        if format == 'csv':
            output = io.StringIO()
            if data:
                writer = csv.writer(output)
                writer.writerow(data[0].keys())
                for row in data:
                    writer.writerow(row.values())
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename={filename}'}
            )
        else:
            # Excel format
            output = io.BytesIO()
            if data:
                import openpyxl
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = export_type.capitalize()
                ws.append(list(data[0].keys()))
                for row in data:
                    ws.append(list(row.values()))
                wb.save(output)
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': f'attachment; filename={filename}'}
            )

    finally:
        db.close()


# =============================================================================
# 15. SETTINGS
# =============================================================================

@logistics_bp.route('/settings')
@logistics_login_required
def settings_menu():
    """Logistics settings menu."""
    db = get_db()

    try:
        settings = db.execute("""
            SELECT * FROM logistics_settings
            WHERE is_active = 1
            ORDER BY category, setting_key
        """).fetchall()

        # Group by category
        settings_by_cat = {}
        for s in settings:
            cat = s['category']
            if cat not in settings_by_cat:
                settings_by_cat[cat] = []
            settings_by_cat[cat].append(dict(s))

        return render_template('logistics/settings/menu.html',
                             title='Logistics Settings',
                             settings_by_cat=settings_by_cat)
    finally:
        db.close()


@logistics_bp.route('/settings/update', methods=['POST'])
@logistics_login_required
def settings_update():
    """Update logistics settings."""
    user = get_current_user()
    db = get_db()

    try:
        data = request.form

        for key, value in data.items():
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                update_logistics_setting(setting_key, value)

        log_logistics_audit('logistics_settings', 0, 'BULK_UPDATE', user['id'],
                           new_value='Logistics settings updated')

        flash('Settings updated successfully!', 'success')
        return redirect(url_for('logistics.settings_menu'))
    finally:
        db.close()


# =============================================================================
# TMS SETTINGS ROUTES
# =============================================================================

@logistics_bp.route('/settings/index')
@logistics_login_required
def settings_index():
    """TMS Settings index page."""
    return render_template('logistics/settings/index.html', title='TMS Settings')


@logistics_bp.route('/settings/tms')
@logistics_login_required
def settings_tms():
    """TMS Core Settings page."""
    user = get_current_user()
    db = get_db()
    try:
        settings = db.execute("""
            SELECT * FROM logistics_settings
            WHERE category IN ('TMS Core', 'General')
            AND is_active = 1
            ORDER BY setting_key
        """).fetchall()
        tms_settings = {s['setting_key']: dict(s) for s in settings}
        return render_template('logistics/settings/tms.html',
                             title='TMS Core Settings',
                             tms_settings=tms_settings)
    finally:
        db.close()


@logistics_bp.route('/settings/routes')
@logistics_login_required
def settings_routes():
    """Route Rules Settings page."""
    db = get_db()
    try:
        settings = db.execute("""
            SELECT * FROM logistics_settings
            WHERE category IN ('Route Rules', 'Routes')
            AND is_active = 1
            ORDER BY setting_key
        """).fetchall()
        routes_settings = {s['setting_key']: dict(s) for s in settings}
        return render_template('logistics/settings/routes.html',
                             title='Route Rules Settings',
                             routes_settings=routes_settings)
    finally:
        db.close()


@logistics_bp.route('/settings/dispatch')
@logistics_login_required
def settings_dispatch():
    """Dispatch Rules Settings page."""
    db = get_db()
    try:
        settings = db.execute("""
            SELECT * FROM logistics_settings
            WHERE category IN ('Dispatch Rules', 'Dispatch')
            AND is_active = 1
            ORDER BY setting_key
        """).fetchall()
        dispatch_settings = {s['setting_key']: dict(s) for s in settings}
        return render_template('logistics/settings/dispatch.html',
                             title='Dispatch Rules Settings',
                             dispatch_settings=dispatch_settings)
    finally:
        db.close()


@logistics_bp.route('/settings/pod')
@logistics_login_required
def settings_pod():
    """POD Rules Settings page."""
    db = get_db()
    try:
        settings = db.execute("""
            SELECT * FROM logistics_settings
            WHERE category IN ('POD Rules', 'POD')
            AND is_active = 1
            ORDER BY setting_key
        """).fetchall()
        pod_settings = {s['setting_key']: dict(s) for s in settings}
        return render_template('logistics/settings/pod.html',
                             title='POD Rules Settings',
                             pod_settings=pod_settings)
    finally:
        db.close()


@logistics_bp.route('/settings/costing')
@logistics_login_required
def settings_costing():
    """Costing Rules Settings page."""
    db = get_db()
    try:
        settings = db.execute("""
            SELECT * FROM logistics_settings
            WHERE category IN ('Costing Rules', 'Costing')
            AND is_active = 1
            ORDER BY setting_key
        """).fetchall()
        costing_settings = {s['setting_key']: dict(s) for s in settings}
        return render_template('logistics/settings/costing.html',
                             title='Costing Rules Settings',
                             costing_settings=costing_settings)
    finally:
        db.close()


@logistics_bp.route('/settings/notifications')
@logistics_login_required
def settings_notifications():
    """Notification Settings page."""
    db = get_db()
    try:
        settings = db.execute("""
            SELECT * FROM logistics_settings
            WHERE category IN ('Notifications', 'Notification Rules')
            AND is_active = 1
            ORDER BY setting_key
        """).fetchall()
        notification_settings = {s['setting_key']: dict(s) for s in settings}

        channels = db.execute("""
            SELECT * FROM flow_channels ORDER BY name
        """).fetchall() if 'flow_channels' in dir() else []

        return render_template('logistics/settings/notifications.html',
                             title='Notification Settings',
                             notification_settings=notification_settings,
                             channels=channels)
    finally:
        db.close()


@logistics_bp.route('/settings/export')
@logistics_login_required
def settings_export():
    """Export Settings page."""
    db = get_db()
    try:
        settings = db.execute("""
            SELECT * FROM logistics_settings
            WHERE category IN ('Export Settings', 'Export')
            AND is_active = 1
            ORDER BY setting_key
        """).fetchall()
        export_settings = {s['setting_key']: dict(s) for s in settings}
        return render_template('logistics/settings/export.html',
                             title='Export Settings',
                             export_settings=export_settings)
    finally:
        db.close()


@logistics_bp.route('/settings/branch-entity')
@logistics_login_required
def settings_branch_entity():
    """Branch/Entity Settings page."""
    db = get_db()
    try:
        settings = db.execute("""
            SELECT * FROM logistics_settings
            WHERE category IN ('Branch Settings', 'Entity Settings', 'Branch')
            AND is_active = 1
            ORDER BY setting_key
        """).fetchall()
        branch_settings = {s['setting_key']: dict(s) for s in settings}

        branches = db.execute("""
            SELECT * FROM logistics_branches WHERE is_active = 1 ORDER BY name
        """).fetchall() if hasattr(db, 'execute') else []

        return render_template('logistics/settings/branch_entity.html',
                             title='Branch/Entity Settings',
                             branch_settings=branch_settings,
                             branches=branches)
    finally:
        db.close()


@logistics_bp.route('/settings/labels')
@logistics_login_required
def settings_labels():
    """Label/Terminology Translation Settings page."""
    db = get_db()
    try:
        settings = db.execute("""
            SELECT * FROM logistics_settings
            WHERE category IN ('Labels', 'Terminology', 'Translation')
            AND is_active = 1
            ORDER BY setting_key
        """).fetchall()
        label_settings = {s['setting_key']: dict(s) for s in settings}
        return render_template('logistics/settings/labels.html',
                             title='Label/Terminology Settings',
                             label_settings=label_settings)
    finally:
        db.close()


@logistics_bp.route('/settings/save', methods=['POST'])
@logistics_login_required
def settings_save():
    """Save TMS settings."""
    user = get_current_user()
    db = get_db()
    try:
        data = request.form
        for key, value in data.items():
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                conn = get_db()
                conn.execute("""
                    UPDATE logistics_settings
                    SET setting_value = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE setting_key = ?
                """, (value, setting_key))
                conn.commit()
                conn.close()

        log_logistics_audit('tms_settings', 0, 'UPDATE', user['id'],
                           new_value='TMS settings updated')

        flash('Settings saved successfully!', 'success')
        return redirect(url_for('logistics.settings_menu'))
    finally:
        db.close()


# =============================================================================
# AUDIT TRAIL ROUTES
# =============================================================================

@logistics_bp.route('/audit/tms')
@logistics_login_required
def audit_tms():
    """TMS Audit Log page."""
    user = get_current_user()
    db = get_db()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page

        entity_type = request.args.get('entity_type', '')
        action = request.args.get('action', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')

        query = """
            SELECT al.*, u.username, u.full_name as user_full_name
            FROM logistics_audit_logs al
            LEFT JOIN users u ON al.user_id = u.id
            WHERE 1=1
        """
        count_query = "SELECT COUNT(*) as total FROM logistics_audit_logs al WHERE 1=1"
        params = []

        if entity_type:
            query += " AND al.entity_type = ?"
            count_query += " AND al.entity_type = ?"
            params.append(entity_type)
        if action:
            query += " AND al.action = ?"
            count_query += " AND al.action = ?"
            params.append(action)
        if date_from:
            query += " AND DATE(al.created_at) >= ?"
            count_query += " AND DATE(al.created_at) >= ?"
            params.append(date_from)
        if date_to:
            query += " AND DATE(al.created_at) <= ?"
            count_query += " AND DATE(al.created_at) <= ?"
            params.append(date_to)

        query += " ORDER BY al.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        logs = db.execute(query, params).fetchall()
        total = db.execute(count_query, params[:len(params)-2]).fetchone()['total']

        entity_types = db.execute("""
            SELECT DISTINCT entity_type FROM logistics_audit_logs
        """).fetchall()

        return render_template('logistics/audit/tms.html',
                             title='TMS Audit Log',
                             logs=[dict(l) for l in logs],
                             entity_types=[e['entity_type'] for e in entity_types],
                             page=page,
                             total_pages=(total + per_page - 1) // per_page,
                             filters={'entity_type': entity_type, 'action': action,
                                    'date_from': date_from, 'date_to': date_to})
    finally:
        db.close()


@logistics_bp.route('/audit/dispatch-changes')
@logistics_login_required
def audit_dispatch_changes():
    """Dispatch Change History page."""
    db = get_db()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page

        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')

        query = """
            SELECT al.*, u.username, u.full_name as user_full_name
            FROM logistics_audit_logs al
            LEFT JOIN users u ON al.user_id = u.id
            WHERE al.entity_type IN ('dispatch', 'dispatch_assignment', 'dispatch_change')
        """
        count_query = """
            SELECT COUNT(*) as total FROM logistics_audit_logs al
            WHERE al.entity_type IN ('dispatch', 'dispatch_assignment', 'dispatch_change')
        """
        params = []

        if date_from:
            query += " AND DATE(al.created_at) >= ?"
            count_query += " AND DATE(al.created_at) >= ?"
            params.append(date_from)
        if date_to:
            query += " AND DATE(al.created_at) <= ?"
            count_query += " AND DATE(al.created_at) <= ?"
            params.append(date_to)

        query += " ORDER BY al.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        logs = db.execute(query, params).fetchall()
        total = db.execute(count_query, params[:len(params)-2]).fetchone()['total']

        return render_template('logistics/audit/dispatch_changes.html',
                             title='Dispatch Change History',
                             logs=[dict(l) for l in logs],
                             page=page,
                             total_pages=(total + per_page - 1) // per_page,
                             filters={'date_from': date_from, 'date_to': date_to})
    finally:
        db.close()


@logistics_bp.route('/audit/trip-changes')
@logistics_login_required
def audit_trip_changes():
    """Trip Change History page."""
    db = get_db()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page

        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')

        query = """
            SELECT al.*, u.username, u.full_name as user_full_name
            FROM logistics_audit_logs al
            LEFT JOIN users u ON al.user_id = u.id
            WHERE al.entity_type IN ('trip', 'trip_assignment', 'trip_change')
        """
        count_query = """
            SELECT COUNT(*) as total FROM logistics_audit_logs al
            WHERE al.entity_type IN ('trip', 'trip_assignment', 'trip_change')
        """
        params = []

        if date_from:
            query += " AND DATE(al.created_at) >= ?"
            count_query += " AND DATE(al.created_at) >= ?"
            params.append(date_from)
        if date_to:
            query += " AND DATE(al.created_at) <= ?"
            count_query += " AND DATE(al.created_at) <= ?"
            params.append(date_to)

        query += " ORDER BY al.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        logs = db.execute(query, params).fetchall()
        total = db.execute(count_query, params[:len(params)-2]).fetchone()['total']

        return render_template('logistics/audit/trip_changes.html',
                             title='Trip Change History',
                             logs=[dict(l) for l in logs],
                             page=page,
                             total_pages=(total + per_page - 1) // per_page,
                             filters={'date_from': date_from, 'date_to': date_to})
    finally:
        db.close()


@logistics_bp.route('/audit/pod-actions')
@logistics_login_required
def audit_pod_actions():
    """POD Action Log page."""
    db = get_db()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page

        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')

        query = """
            SELECT al.*, u.username, u.full_name as user_full_name
            FROM logistics_audit_logs al
            LEFT JOIN users u ON al.user_id = u.id
            WHERE al.entity_type IN ('pod', 'pod_action', 'proof_of_delivery')
        """
        count_query = """
            SELECT COUNT(*) as total FROM logistics_audit_logs al
            WHERE al.entity_type IN ('pod', 'pod_action', 'proof_of_delivery')
        """
        params = []

        if date_from:
            query += " AND DATE(al.created_at) >= ?"
            count_query += " AND DATE(al.created_at) >= ?"
            params.append(date_from)
        if date_to:
            query += " AND DATE(al.created_at) <= ?"
            count_query += " AND DATE(al.created_at) <= ?"
            params.append(date_to)

        query += " ORDER BY al.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        logs = db.execute(query, params).fetchall()
        total = db.execute(count_query, params[:len(params)-2]).fetchone()['total']

        return render_template('logistics/audit/pod_actions.html',
                             title='POD Action Log',
                             logs=[dict(l) for l in logs],
                             page=page,
                             total_pages=(total + per_page - 1) // per_page,
                             filters={'date_from': date_from, 'date_to': date_to})
    finally:
        db.close()


@logistics_bp.route('/audit/route-changes')
@logistics_login_required
def audit_route_changes():
    """Route Change History page."""
    db = get_db()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page

        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')

        query = """
            SELECT al.*, u.username, u.full_name as user_full_name
            FROM logistics_audit_logs al
            LEFT JOIN users u ON al.user_id = u.id
            WHERE al.entity_type IN ('route', 'route_change', 'route_stop')
        """
        count_query = """
            SELECT COUNT(*) as total FROM logistics_audit_logs al
            WHERE al.entity_type IN ('route', 'route_change', 'route_stop')
        """
        params = []

        if date_from:
            query += " AND DATE(al.created_at) >= ?"
            count_query += " AND DATE(al.created_at) >= ?"
            params.append(date_from)
        if date_to:
            query += " AND DATE(al.created_at) <= ?"
            count_query += " AND DATE(al.created_at) <= ?"
            params.append(date_to)

        query += " ORDER BY al.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        logs = db.execute(query, params).fetchall()
        total = db.execute(count_query, params[:len(params)-2]).fetchone()['total']

        return render_template('logistics/audit/route_changes.html',
                             title='Route Change History',
                             logs=[dict(l) for l in logs],
                             page=page,
                             total_pages=(total + per_page - 1) // per_page,
                             filters={'date_from': date_from, 'date_to': date_to})
    finally:
        db.close()


# =============================================================================
# FLOW INTEGRATION FOR TMS
# =============================================================================

def publish_tms_to_flow(channel: str, event_type: str, data: dict, user_id: int = None) -> bool:
    """
    Publish TMS event to Flow channel.

    Args:
        channel: Flow channel identifier (e.g., 'logistics-trips', 'logistics-alerts')
        event_type: Type of event (e.g., 'trip_status_change', 'delay_alert')
        data: Event data dictionary
        user_id: User who triggered the event

    Returns:
        True if successful, False otherwise
    """
    try:
        from flow_models import send_channel_message, get_db as flow_get_db

        user = user_id or 1

        message_content = format_tms_flow_message(event_type, data)
        if not message_content:
            return False

        result = send_channel_message(channel, user, message_content, 'text')
        if result:
            log_tms_notification(channel, event_type, data, user)
        return result is not None
    except Exception as e:
        print(f"Flow publish error: {e}")
        return False


def format_tms_flow_message(event_type: str, data: dict) -> str:
    """Format TMS event data into a Flow message."""
    timestamp = datetime.now().strftime('%d/%m/%Y %H:%M')

    templates = {
        'trip_status_change': "🚚 *Trip Status Update*\nTrip: {trip_code}\nStatus: {old_status} → {new_status}\nTime: {time}",
        'delay_alert': "⚠️ *Delay Alert*\nTrip: {trip_code}\nRoute: {route}\nDelay: {delay_hours} hours\nExpected: {expected_time}",
        'failed_delivery': "❌ *Failed Delivery*\nTrip: {trip_code}\nReason: {failure_reason}\nCustomer: {customer}",
        'missing_pod': "📋 *Missing POD Alert*\nTrip: {trip_code}\nSLA Breach: {sla_hours} hours without POD",
        'vehicle_expiry': "🔔 *Vehicle Document Expiry*\nVehicle: {plate_number}\nDocument: {document_type}\nExpires: {expiry_date}",
        'driver_expiry': "🔔 *Driver Document Expiry*\nDriver: {driver_name}\nDocument: {document_type}\nExpires: {expiry_date}",
        'exception_created': "🚨 *New Exception*\nTrip: {trip_code}\nType: {exception_type}\nSeverity: {severity}",
        'high_cost_trip': "💰 *High-Cost Trip*\nTrip: {trip_code}\nCost: {total_cost} {currency}\nApproval Required",
        'pod_captured': "✅ *POD Captured*\nTrip: {trip_code}\nCustomer: {customer}\nSigned: {signed_by}",
        'pod_approved': "✅ *POD Approved*\nTrip: {trip_code}\nApproved By: {approved_by}",
        'dispatch_created': "📦 *New Dispatch*\nTrip: {trip_code}\nDriver: {driver}\nVehicle: {vehicle}",
        'dispatch_changed': "🔄 *Dispatch Changed*\nTrip: {trip_code}\nChange: {change_details}",
        'route_modified': "🗺️ *Route Modified*\nRoute: {route_name}\nChange: {change_details}",
    }

    template = templates.get(event_type, "📢 *TMS Update*\n{content}")
    if event_type == 'generic':
        template = template.format(content=data.get('content', ''))

    try:
        return template.format(**data, time=timestamp)
    except KeyError:
        return f"📢 *TMS {event_type}*\n{json.dumps(data, default=str)}"


def log_tms_notification(channel: str, event_type: str, data: dict, user_id: int):
    """Log TMS notification sent to Flow."""
    try:
        conn = get_db()
        conn.execute("""
            INSERT INTO logistics_alerts
            (alert_type, title, message, entity_type, entity_id,
             severity, status, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            'flow_notification',
            f'TMS {event_type}',
            f'Published to {channel}: {event_type}',
            event_type,
            data.get('trip_id') or data.get('entity_id', 0),
            data.get('severity', 'info'),
            'sent',
            user_id
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging TMS notification: {e}")


@logistics_bp.route('/flow/tms-notifications')
@logistics_login_required
def flow_tms_notifications():
    """TMS Flow Notifications setup page."""
    user = get_current_user()
    db = get_db()
    try:
        notifications_config = db.execute("""
            SELECT * FROM logistics_settings
            WHERE category = 'Flow Notifications'
            AND is_active = 1
            ORDER BY setting_key
        """).fetchall()

        channels = []
        try:
            from flow_models import get_all as flow_get_all
            channels = flow_get_all("SELECT * FROM flow_channels ORDER BY name")
        except:
            pass

        recent_notifications = db.execute("""
            SELECT * FROM logistics_alerts
            WHERE alert_type = 'flow_notification'
            ORDER BY created_at DESC
            LIMIT 50
        """).fetchall() if hasattr(db, 'execute') else []

        return render_template('logistics/flow/tms_notifications.html',
                             title='TMS Flow Notifications',
                             notifications_config=[dict(n) for n in notifications_config],
                             channels=channels,
                             recent_notifications=[dict(n) for n in recent_notifications])
    finally:
        db.close()


@logistics_bp.route('/flow/publish-alert', methods=['POST'])
@logistics_login_required
def flow_publish_alert():
    """Publish alert to Flow channel."""
    user = get_current_user()
    try:
        data = request.get_json() or request.form
        channel = data.get('channel', 'logistics-alerts')
        event_type = data.get('event_type', 'generic')
        alert_data = data.get('data', {})

        success = publish_tms_to_flow(channel, event_type, alert_data, user['id'])

        if success:
            flash('Alert published to Flow successfully!', 'success')
            return jsonify({'success': True, 'message': 'Alert published'})
        else:
            flash('Failed to publish alert to Flow', 'error')
            return jsonify({'success': False, 'error': 'Failed to publish'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@logistics_bp.route('/flow/subscribe', methods=['POST'])
@logistics_login_required
def flow_subscribe():
    """Subscribe to TMS events in Flow."""
    user = get_current_user()
    try:
        data = request.get_json() or request.form
        channel = data.get('channel', 'logistics-trips')
        events = data.get('events', [])

        conn = get_db()
        for event in events:
            conn.execute("""
                INSERT OR REPLACE INTO logistics_settings
                (setting_key, setting_value, setting_type, category, description, is_active)
                VALUES (?, ?, 'Text', 'Flow Subscriptions', ?, 1)
            """, (
                f'flow_sub_{event}_{channel}',
                channel,
                f'Subscribe to {event} events in {channel}'
            ))
        conn.commit()
        conn.close()

        log_logistics_audit('flow_subscription', 0, 'SUBSCRIBE', user['id'],
                           new_value=f'Subscribed to {len(events)} events in {channel}')

        flash(f'Subscribed to {len(events)} event types in {channel}!', 'success')
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@logistics_bp.route('/flow/test-publish', methods=['POST'])
@logistics_login_required
def flow_test_publish():
    """Test Flow publishing with sample data."""
    user = get_current_user()
    try:
        data = request.get_json() or request.form
        channel = data.get('channel', 'logistics-alerts')

        test_data = {
            'trip_code': 'TEST-001',
            'trip_id': 0,
            'status': 'In Transit',
            'route': 'Dubai - Abu Dhabi',
            'driver_name': 'Test Driver',
            'vehicle_plate': 'XXX-0000',
            'customer': 'Test Customer',
            'content': 'This is a test message from TMS Flow integration'
        }

        success = publish_tms_to_flow(channel, 'generic', test_data, user['id'])

        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# 15b. FLEET PERFORMANCE SYSTEM
# =============================================================================

@logistics_bp.route('/fleet/performance')
@logistics_login_required
def fleet_performance():
    """Main Fleet Performance Dashboard."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        branch_id = request.args.get('branch_id', '')

        # Get fleet KPIs aggregated
        kpi_query = """
            SELECT AVG(on_time_rate) as avg_on_time_rate,
                   AVG(idle_time_minutes) as avg_idle_minutes,
                   AVG(fuel_liters) as avg_fuel,
                   SUM(carbon_kg) as total_carbon,
                   SUM(deliveries_completed) as total_deliveries,
                   SUM(trips_completed) as total_trips,
                   SUM(total_km) as total_km
            FROM logistics_fleet_kpis
            WHERE date(kpi_date) BETWEEN ? AND ?
        """
        kpi_params = [date_from, date_to]
        if branch_id:
            kpi_query += " AND vehicle_id IN (SELECT id FROM logistics_vehicles WHERE branch_id = ?)"
            kpi_params.append(branch_id)

        kpis = db.execute(kpi_query, kpi_params).fetchone()

        # Vehicle utilization
        vehicle_util = db.execute("""
            SELECT v.id, v.vehicle_code, v.plate_number, v.vehicle_type,
                   COUNT(DISTINCT t.id) as trip_count,
                   COALESCE(SUM(t.distance_km), 0) as total_km,
                   COALESCE(SUM(t.actual_cost), 0) as total_cost
            FROM logistics_vehicles v
            LEFT JOIN logistics_trips t ON v.id = t.vehicle_id
                AND date(t.planned_departure) BETWEEN ? AND ?
            WHERE v.status = 'active'
            GROUP BY v.id
            ORDER BY total_km DESC
        """, (date_from, date_to)).fetchall()

        # Driver productivity
        driver_prod = db.execute("""
            SELECT d.id, d.driver_code, d.full_name,
                   COUNT(DISTINCT t.id) as trip_count,
                   COALESCE(SUM(sl.quantity), 0) as deliveries
            FROM logistics_drivers d
            LEFT JOIN logistics_trips t ON d.id = t.driver_id
                AND date(t.planned_departure) BETWEEN ? AND ?
            LEFT JOIN logistics_shipments s ON s.trip_id = t.id
            LEFT JOIN logistics_shipment_lines sl ON s.id = sl.shipment_id
            WHERE d.status = 'active'
            GROUP BY d.id
            ORDER BY deliveries DESC
        """, (date_from, date_to)).fetchall()

        # Cost per km
        cost_per_km = db.execute("""
            SELECT SUM(actual_cost) / NULLIF(SUM(distance_km), 0) as cost_km
            FROM logistics_trips
            WHERE status = 'completed'
            AND distance_km > 0
            AND date(planned_departure) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['cost_km'] or 0

        branches = db.execute("SELECT id, name FROM branches WHERE is_active = 1 ORDER BY name").fetchall()

        return render_template('logistics/fleet/performance.html',
                             title='Fleet Performance',
                             date_from=date_from,
                             date_to=date_to,
                             kpis=dict(kpis) if kpis else {},
                             vehicles=[dict(v) for v in vehicle_util],
                             drivers=[dict(d) for d in driver_prod],
                             cost_per_km=round(cost_per_km, 2),
                             branches=branches,
                             branch_id=branch_id)
    finally:
        db.close()


@logistics_bp.route('/fleet/utilization')
@logistics_login_required
def fleet_utilization():
    """Vehicle Utilization Metrics."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))

        # Calculate utilization per vehicle
        utilization = db.execute("""
            SELECT v.id, v.vehicle_code, v.plate_number, v.vehicle_type,
                   v.load_capacity_kg, v.pallet_capacity,
                   COUNT(t.id) as trips_count,
                   COALESCE(SUM(t.distance_km), 0) as total_km,
                   COALESCE(SUM(t.total_weight_kg), 0) as total_weight,
                   COALESCE(SUM(t.total_stops), 0) as total_stops,
                   COALESCE(SUM(t.completed_stops), 0) as completed_stops
            FROM logistics_vehicles v
            LEFT JOIN logistics_trips t ON v.id = t.vehicle_id
                AND date(t.planned_departure) BETWEEN ? AND ?
                AND t.status IN ('completed', 'closed')
            WHERE v.status = 'active'
            GROUP BY v.id
            ORDER BY total_km DESC
        """, (date_from, date_to)).fetchall()

        # Utilization by type
        by_type = db.execute("""
            SELECT v.vehicle_type,
                   COUNT(DISTINCT v.id) as vehicle_count,
                   COUNT(t.id) as total_trips,
                   COALESCE(SUM(t.distance_km), 0) as total_km
            FROM logistics_vehicles v
            LEFT JOIN logistics_trips t ON v.id = t.vehicle_id
                AND date(t.planned_departure) BETWEEN ? AND ?
            WHERE v.status = 'active'
            GROUP BY v.vehicle_type
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/fleet/utilization.html',
                             title='Vehicle Utilization',
                             date_from=date_from,
                             date_to=date_to,
                             utilization=[dict(u) for u in utilization],
                             by_type=[dict(t) for t in by_type])
    finally:
        db.close()


@logistics_bp.route('/fleet/driver-productivity')
@logistics_login_required
def fleet_driver_productivity():
    """Driver Productivity Reports."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))

        drivers = db.execute("""
            SELECT d.id, d.driver_code, d.full_name, d.mobile, d.license_class,
                   COUNT(DISTINCT t.id) as trips_count,
                   COUNT(DISTINCT s.id) as shipments_handled,
                   COALESCE(SUM(t.distance_km), 0) as total_km,
                   COALESCE(SUM(t.completed_stops), 0) as stops_completed,
                   COALESCE(SUM(t.failed_stops), 0) as stops_failed,
                   COALESCE(SUM(t.driver_allowance), 0) as total_allowance,
                   CASE WHEN COUNT(DISTINCT t.id) > 0
                        THEN COALESCE(SUM(t.distance_km), 0) / COUNT(DISTINCT t.id)
                        ELSE 0 END as avg_km_per_trip
            FROM logistics_drivers d
            LEFT JOIN logistics_trips t ON d.id = t.driver_id
                AND date(t.planned_departure) BETWEEN ? AND ?
                AND t.status IN ('completed', 'closed')
            LEFT JOIN logistics_shipments s ON s.driver_id = d.id
                AND date(s.created_at) BETWEEN ? AND ?
            WHERE d.status = 'active'
            GROUP BY d.id
            ORDER BY trips_count DESC
        """, (date_from, date_to, date_from, date_to)).fetchall()

        return render_template('logistics/fleet/driver_productivity.html',
                             title='Driver Productivity',
                             date_from=date_from,
                             date_to=date_to,
                             drivers=[dict(d) for d in drivers])
    finally:
        db.close()


@logistics_bp.route('/fleet/on-time-delivery')
@logistics_login_required
def fleet_on_time_delivery():
    """On-Time Delivery KPIs."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))

        # On-time stats
        stats = db.execute("""
            SELECT COUNT(*) as total_delivered,
                   SUM(CASE WHEN s.actual_delivery <= s.estimated_delivery THEN 1 ELSE 0 END) as on_time,
                   SUM(CASE WHEN s.actual_delivery > s.estimated_delivery THEN 1 ELSE 0 END) as late
            FROM logistics_shipments s
            WHERE s.status = 'delivered'
            AND date(s.actual_delivery) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()

        # By customer
        by_customer = db.execute("""
            SELECT c.name as customer_name,
                   COUNT(*) as total,
                   SUM(CASE WHEN s.actual_delivery <= s.estimated_delivery THEN 1 ELSE 0 END) as on_time
            FROM logistics_shipments s
            JOIN sdad_customers c ON s.customer_id = c.id
            WHERE s.status = 'delivered'
            AND date(s.actual_delivery) BETWEEN ? AND ?
            GROUP BY c.id
            HAVING total >= 3
            ORDER BY on_time DESC
        """, (date_from, date_to)).fetchall()

        # By route
        by_route = db.execute("""
            SELECT r.route_name,
                   COUNT(*) as total,
                   SUM(CASE WHEN s.actual_delivery <= s.estimated_delivery THEN 1 ELSE 0 END) as on_time
            FROM logistics_shipments s
            JOIN logistics_route_masters r ON s.route_id = r.id
            WHERE s.status = 'delivered'
            AND date(s.actual_delivery) BETWEEN ? AND ?
            GROUP BY r.id
            HAVING total >= 3
            ORDER BY on_time DESC
        """, (date_from, date_to)).fetchall()

        # Recent late deliveries
        late_deliveries = db.execute("""
            SELECT s.*, c.name as customer_name
            FROM logistics_shipments s
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            WHERE s.status = 'delivered'
            AND s.actual_delivery > s.estimated_delivery
            AND date(s.actual_delivery) BETWEEN ? AND ?
            ORDER BY s.actual_delivery DESC
            LIMIT 20
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/fleet/on_time_delivery.html',
                             title='On-Time Delivery',
                             date_from=date_from,
                             date_to=date_to,
                             stats=dict(stats) if stats else {},
                             by_customer=[dict(c) for c in by_customer],
                             by_route=[dict(r) for r in by_route],
                             late_deliveries=[dict(l) for l in late_deliveries])
    finally:
        db.close()


@logistics_bp.route('/fleet/trip-turnaround')
@logistics_login_required
def fleet_trip_turnaround():
    """Trip Turnaround Time Analysis."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))

        # Average turnaround
        turnaround = db.execute("""
            SELECT AVG(
                (julianday(t.actual_arrival) - julianday(t.actual_departure)) * 24
            ) as avg_hours
            FROM logistics_trips t
            WHERE t.status IN ('completed', 'closed')
            AND t.actual_arrival IS NOT NULL
            AND t.actual_departure IS NOT NULL
            AND date(t.planned_departure) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()['avg_hours'] or 0

        # By vehicle
        by_vehicle = db.execute("""
            SELECT v.vehicle_code, v.plate_number,
                   COUNT(t.id) as trip_count,
                   AVG((julianday(t.actual_arrival) - julianday(t.actual_departure)) * 24) as avg_hours,
                   MIN((julianday(t.actual_arrival) - julianday(t.actual_departure)) * 24) as min_hours,
                   MAX((julianday(t.actual_arrival) - julianday(t.actual_departure)) * 24) as max_hours
            FROM logistics_trips t
            JOIN logistics_vehicles v ON t.vehicle_id = v.id
            WHERE t.status IN ('completed', 'closed')
            AND t.actual_arrival IS NOT NULL
            AND date(t.planned_departure) BETWEEN ? AND ?
            GROUP BY v.id
            ORDER BY avg_hours ASC
        """, (date_from, date_to)).fetchall()

        # Recent trips
        recent = db.execute("""
            SELECT t.*, v.plate_number, d.full_name as driver_name,
                   (julianday(t.actual_arrival) - julianday(t.actual_departure)) * 24 as turnaround_hours
            FROM logistics_trips t
            LEFT JOIN logistics_vehicles v ON t.vehicle_id = v.id
            LEFT JOIN logistics_drivers d ON t.driver_id = d.id
            WHERE t.status IN ('completed', 'closed')
            AND t.actual_arrival IS NOT NULL
            AND date(t.planned_departure) BETWEEN ? AND ?
            ORDER BY t.actual_arrival DESC
            LIMIT 30
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/fleet/trip_turnaround.html',
                             title='Trip Turnaround',
                             date_from=date_from,
                             date_to=date_to,
                             avg_hours=round(turnaround, 1),
                             by_vehicle=[dict(v) for v in by_vehicle],
                             recent=[dict(r) for r in recent])
    finally:
        db.close()


@logistics_bp.route('/fleet/fuel-efficiency')
@logistics_login_required
def fleet_fuel_efficiency():
    """Fuel Efficiency Reports."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))

        # Fuel KPIs
        fuel_stats = db.execute("""
            SELECT SUM(t.fuel_cost) as total_fuel_cost,
                   SUM(t.distance_km) as total_distance,
                   SUM(t.fuel_cost) / NULLIF(SUM(t.distance_km), 0) as cost_per_km,
                   SUM(t.distance_km) / NULLIF(SUM(
                       SELECT COALESCE(SUM(fc.fuel_liters), 0)
                       FROM logistics_fleet_kpis fc
                       WHERE date(fc.kpi_date) BETWEEN ? AND ?
                   ), 0) as km_per_liter
            FROM logistics_trips t
            WHERE t.status IN ('completed', 'closed')
            AND t.distance_km > 0
            AND date(t.planned_departure) BETWEEN ? AND ?
        """, (date_from, date_to, date_from, date_to)).fetchone()

        # By vehicle
        by_vehicle = db.execute("""
            SELECT v.id, v.vehicle_code, v.plate_number, v.fuel_type,
                   COALESCE(SUM(t.distance_km), 0) as total_km,
                   COALESCE(SUM(t.fuel_cost), 0) as total_fuel,
                   COALESCE(SUM(fk.fuel_liters), 0) as total_liters,
                   CASE WHEN COALESCE(SUM(fk.fuel_liters), 0) > 0
                        THEN COALESCE(SUM(t.distance_km), 0) / COALESCE(SUM(fk.fuel_liters), 0)
                        ELSE 0 END as km_per_liter,
                   CASE WHEN COALESCE(SUM(t.distance_km), 0) > 0
                        THEN COALESCE(SUM(t.fuel_cost), 0) / COALESCE(SUM(t.distance_km), 0)
                        ELSE 0 END as cost_per_km
            FROM logistics_vehicles v
            LEFT JOIN logistics_trips t ON v.id = t.vehicle_id
                AND t.status IN ('completed', 'closed')
                AND date(t.planned_departure) BETWEEN ? AND ?
            LEFT JOIN logistics_fleet_kpis fk ON v.id = fk.vehicle_id
                AND date(fk.kpi_date) BETWEEN ? AND ?
            WHERE v.status = 'active'
            GROUP BY v.id
            HAVING total_km > 0
            ORDER BY km_per_liter DESC
        """, (date_from, date_to, date_from, date_to)).fetchall()

        # Fuel cost trends
        trends = db.execute("""
            SELECT date(t.planned_departure) as fuel_date,
                   SUM(t.fuel_cost) as daily_cost,
                   SUM(t.distance_km) as daily_km
            FROM logistics_trips t
            WHERE t.status IN ('completed', 'closed')
            AND date(t.planned_departure) BETWEEN ? AND ?
            GROUP BY date(t.planned_departure)
            ORDER BY fuel_date
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/fleet/fuel_efficiency.html',
                             title='Fuel Efficiency',
                             date_from=date_from,
                             date_to=date_to,
                             fuel_stats=dict(fuel_stats) if fuel_stats else {},
                             by_vehicle=[dict(v) for v in by_vehicle],
                             trends=[dict(t) for t in trends])
    finally:
        db.close()


@logistics_bp.route('/fleet/idle-time')
@logistics_login_required
def fleet_idle_time():
    """Idle Time Analysis."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))

        # Idle time stats
        idle_stats = db.execute("""
            SELECT AVG(idle_time_minutes) as avg_idle,
                   SUM(idle_time_minutes) as total_idle,
                   SUM(driving_time_minutes) as total_driving,
                   SUM(idle_time_minutes) * 100.0 / NULLIF(SUM(idle_time_minutes + driving_time_minutes), 0) as idle_pct
            FROM logistics_fleet_kpis
            WHERE date(kpi_date) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()

        # By vehicle
        by_vehicle = db.execute("""
            SELECT v.vehicle_code, v.plate_number, v.vehicle_type,
                   COALESCE(AVG(fk.idle_time_minutes), 0) as avg_idle,
                   COALESCE(AVG(fk.driving_time_minutes), 0) as avg_driving,
                   COALESCE(SUM(fk.idle_time_minutes), 0) as total_idle,
                   COALESCE(SUM(fk.driving_time_minutes), 0) as total_driving
            FROM logistics_vehicles v
            LEFT JOIN logistics_fleet_kpis fk ON v.id = fk.vehicle_id
                AND date(fk.kpi_date) BETWEEN ? AND ?
            WHERE v.status = 'active'
            GROUP BY v.id
            HAVING total_idle > 0 OR total_driving > 0
            ORDER BY avg_idle DESC
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/fleet/idle_time.html',
                             title='Idle Time Analysis',
                             date_from=date_from,
                             date_to=date_to,
                             idle_stats=dict(idle_stats) if idle_stats else {},
                             by_vehicle=[dict(v) for v in by_vehicle])
    finally:
        db.close()


@logistics_bp.route('/fleet/exception-rate')
@logistics_login_required
def fleet_exception_rate():
    """Exception Rate Tracking."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))

        # Exception rate stats
        exc_stats = db.execute("""
            SELECT COUNT(*) as total_deliveries,
                   SUM(i.exception_count) as total_exceptions,
                   SUM(i.exception_count) * 100.0 / NULLIF(COUNT(*), 0) as exception_rate
            FROM logistics_shipments s
            LEFT JOIN logistics_fleet_kpis i ON s.vehicle_id = i.vehicle_id
                AND date(i.kpi_date) = date(s.created_at)
            WHERE s.status IN ('delivered', 'failed_delivery')
            AND date(s.created_at) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()

        # By vehicle
        by_vehicle = db.execute("""
            SELECT v.vehicle_code, v.plate_number,
                   COUNT(s.id) as total_shipments,
                   COALESCE(SUM(fk.exception_count), 0) as exceptions,
                   COALESCE(SUM(fk.exception_count), 0) * 100.0 / NULLIF(COUNT(s.id), 0) as exception_rate
            FROM logistics_vehicles v
            LEFT JOIN logistics_shipments s ON v.id = s.vehicle_id
                AND s.status IN ('delivered', 'failed_delivery')
                AND date(s.created_at) BETWEEN ? AND ?
            LEFT JOIN logistics_fleet_kpis fk ON v.id = fk.vehicle_id
                AND date(fk.kpi_date) BETWEEN ? AND ?
            WHERE v.status = 'active'
            GROUP BY v.id
            HAVING total_shipments >= 3
            ORDER BY exception_rate DESC
        """, (date_from, date_to, date_from, date_to)).fetchall()

        # By driver
        by_driver = db.execute("""
            SELECT d.full_name, d.driver_code,
                   COUNT(s.id) as total_shipments,
                   COALESCE(SUM(fk.exception_count), 0) as exceptions,
                   COALESCE(SUM(fk.exception_count), 0) * 100.0 / NULLIF(COUNT(s.id), 0) as exception_rate
            FROM logistics_drivers d
            LEFT JOIN logistics_shipments s ON d.id = s.driver_id
                AND s.status IN ('delivered', 'failed_delivery')
                AND date(s.created_at) BETWEEN ? AND ?
            LEFT JOIN logistics_fleet_kpis fk ON d.id = fk.driver_id
                AND date(fk.kpi_date) BETWEEN ? AND ?
            WHERE d.status = 'active'
            GROUP BY d.id
            HAVING total_shipments >= 3
            ORDER BY exception_rate DESC
        """, (date_from, date_to, date_from, date_to)).fetchall()

        return render_template('logistics/fleet/exception_rate.html',
                             title='Exception Rate',
                             date_from=date_from,
                             date_to=date_to,
                             exc_stats=dict(exc_stats) if exc_stats else {},
                             by_vehicle=[dict(v) for v in by_vehicle],
                             by_driver=[dict(d) for d in by_driver])
    finally:
        db.close()


@logistics_bp.route('/fleet/carbon')
@logistics_login_required
def fleet_carbon():
    """Carbon/Emission Summary Scaffold."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))

        # Carbon stats from fleet KPIs
        carbon_stats = db.execute("""
            SELECT SUM(carbon_kg) as total_carbon,
                   SUM(total_km) as total_distance,
                   SUM(carbon_kg) / NULLIF(SUM(total_km), 0) * 1000 as carbon_per_km,
                   AVG(carbon_kg) as avg_carbon_per_day
            FROM logistics_fleet_kpis
            WHERE date(kpi_date) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()

        # Calculate from trips if no KPIs
        if not carbon_stats or carbon_stats['total_carbon'] == 0:
            # Estimate: diesel ~2.68 kg CO2 per liter, petrol ~2.31 kg CO2 per liter
            carbon_stats = db.execute("""
                SELECT COALESCE(SUM(t.fuel_cost / 2.0), 0) * 2.68 as total_carbon,
                       COALESCE(SUM(t.distance_km), 0) as total_distance,
                       COALESCE(SUM(t.fuel_cost / 2.0), 0) * 2.68 / NULLIF(COALESCE(SUM(t.distance_km), 0), 0) * 1000 as carbon_per_km
                FROM logistics_trips t
                WHERE t.status IN ('completed', 'closed')
                AND date(t.planned_departure) BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()

        # By vehicle type
        by_type = db.execute("""
            SELECT v.vehicle_type,
                   COUNT(DISTINCT v.id) as vehicle_count,
                   COALESCE(SUM(fk.carbon_kg), 0) as total_carbon,
                   COALESCE(SUM(fk.total_km), 0) as total_km
            FROM logistics_vehicles v
            LEFT JOIN logistics_fleet_kpis fk ON v.id = fk.vehicle_id
                AND date(fk.kpi_date) BETWEEN ? AND ?
            WHERE v.status = 'active'
            GROUP BY v.vehicle_type
        """, (date_from, date_to)).fetchall()

        # Daily carbon trend
        daily = db.execute("""
            SELECT date(kpi_date) as carbon_date,
                   SUM(carbon_kg) as daily_carbon,
                   SUM(total_km) as daily_km
            FROM logistics_fleet_kpis
            WHERE date(kpi_date) BETWEEN ? AND ?
            GROUP BY date(kpi_date)
            ORDER BY carbon_date
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/fleet/carbon.html',
                             title='Carbon Emissions',
                             date_from=date_from,
                             date_to=date_to,
                             carbon_stats=dict(carbon_stats) if carbon_stats else {},
                             by_type=[dict(t) for t in by_type],
                             daily=[dict(d) for d in daily])
    finally:
        db.close()


@logistics_bp.route('/fleet/reports')
@logistics_login_required
def fleet_reports():
    """Fleet Performance Reports - Combined View."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        report_type = request.args.get('type', 'summary')

        # Summary KPIs
        summary = db.execute("""
            SELECT
                COUNT(DISTINCT v.id) as active_vehicles,
                COUNT(DISTINCT t.id) as total_trips,
                COALESCE(SUM(t.distance_km), 0) as total_km,
                COALESCE(SUM(t.actual_cost), 0) as total_cost,
                COALESCE(SUM(fk.carbon_kg), 0) as total_carbon,
                AVG(fk.on_time_rate) as avg_on_time,
                AVG(fk.idle_time_minutes) as avg_idle
            FROM logistics_vehicles v
            CROSS JOIN logistics_trips t ON v.id = t.vehicle_id
                AND date(t.planned_departure) BETWEEN ? AND ?
            LEFT JOIN logistics_fleet_kpis fk ON v.id = fk.vehicle_id
                AND date(fk.kpi_date) BETWEEN ? AND ?
            WHERE v.status = 'active'
        """, (date_from, date_to, date_from, date_to)).fetchone()

        # Vehicle performance ranking
        rankings = db.execute("""
            SELECT v.vehicle_code, v.plate_number, v.vehicle_type,
                   COUNT(t.id) as trips,
                   COALESCE(SUM(t.distance_km), 0) as total_km,
                   COALESCE(SUM(t.actual_cost), 0) as total_cost,
                   AVG(fk.on_time_rate) as on_time_rate,
                   AVG(fk.fuel_liters) as avg_fuel
            FROM logistics_vehicles v
            LEFT JOIN logistics_trips t ON v.id = t.vehicle_id
                AND date(t.planned_departure) BETWEEN ? AND ?
                AND t.status IN ('completed', 'closed')
            LEFT JOIN logistics_fleet_kpis fk ON v.id = fk.vehicle_id
                AND date(fk.kpi_date) BETWEEN ? AND ?
            WHERE v.status = 'active'
            GROUP BY v.id
            ORDER BY trips DESC
            LIMIT 50
        """, (date_from, date_to, date_from, date_to)).fetchall()

        return render_template('logistics/fleet/reports.html',
                             title='Fleet Reports',
                             date_from=date_from,
                             date_to=date_to,
                             report_type=report_type,
                             summary=dict(summary) if summary else {},
                             rankings=[dict(r) for r in rankings])
    finally:
        db.close()


# =============================================================================
# 15c. EXCEPTIONS/ALERTS SYSTEM
# =============================================================================

@logistics_bp.route('/exceptions')
@logistics_login_required
def exceptions_index():
    """Main Exceptions Dashboard."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))
        severity = request.args.get('severity', '')
        status = request.args.get('status', '')

        # Get exceptions with enhanced data
        query = """
            SELECT i.*, s.shipment_code, d.full_name as driver_name,
                   v.plate_number, c.name as customer_name
            FROM logistics_incidents i
            LEFT JOIN logistics_shipments s ON i.shipment_id = s.id
            LEFT JOIN logistics_drivers d ON i.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON i.vehicle_id = v.id
            LEFT JOIN sdad_customers c ON i.customer_id = c.id
            WHERE date(i.created_at) BETWEEN ? AND ?
        """
        params = [date_from, date_to]

        if severity:
            query += " AND i.severity = ?"
            params.append(severity)
        if status:
            query += " AND i.status = ?"
            params.append(status)

        query += " ORDER BY CASE i.severity WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 ELSE 4 END, i.created_at DESC"

        exceptions = db.execute(query, params).fetchall()

        # Stats by type
        by_type = db.execute("""
            SELECT incident_type, COUNT(*) as count,
                   SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_count
            FROM logistics_incidents
            WHERE date(created_at) BETWEEN ? AND ?
            GROUP BY incident_type
        """, (date_from, date_to)).fetchall()

        # Stats by severity
        by_severity = db.execute("""
            SELECT severity, COUNT(*) as count,
                   SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open_count
            FROM logistics_incidents
            WHERE date(created_at) BETWEEN ? AND ?
            GROUP BY severity
        """, (date_from, date_to)).fetchall()

        # Critical alerts count
        critical_count = db.execute("""
            SELECT COUNT(*) as cnt FROM logistics_incidents
            WHERE severity = 'critical' AND status = 'open'
        """).fetchone()['cnt']

        return render_template('logistics/exceptions/index.html',
                             title='Exceptions Dashboard',
                             date_from=date_from,
                             date_to=date_to,
                             exceptions=[dict(e) for e in exceptions],
                             by_type=[dict(t) for t in by_type],
                             by_severity=[dict(s) for s in by_severity],
                             critical_count=critical_count,
                             severity=severity,
                             status_filter=status)
    finally:
        db.close()


@logistics_bp.route('/exceptions/late-deliveries')
@logistics_login_required
def exceptions_late_deliveries():
    """Late Delivery Exceptions."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))

        late_deliveries = db.execute("""
            SELECT s.*, c.name as customer_name, d.full_name as driver_name,
                   v.plate_number,
                   CASE WHEN s.actual_delivery > s.estimated_delivery
                        THEN ROUND((julianday(s.actual_delivery) - julianday(s.estimated_delivery)) * 24, 1)
                        ELSE 0 END as delay_hours
            FROM logistics_shipments s
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            LEFT JOIN logistics_drivers d ON s.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            WHERE s.status = 'delivered'
            AND s.actual_delivery > s.estimated_delivery
            AND date(s.actual_delivery) BETWEEN ? AND ?
            ORDER BY delay_hours DESC
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/exceptions/late_deliveries.html',
                             title='Late Deliveries',
                             date_from=date_from,
                             date_to=date_to,
                             late_deliveries=[dict(l) for l in late_deliveries])
    finally:
        db.close()


@logistics_bp.route('/exceptions/missed-deliveries')
@logistics_login_required
def exceptions_missed_deliveries():
    """Missed Delivery Exceptions."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))

        missed = db.execute("""
            SELECT s.*, c.name as customer_name, d.full_name as driver_name,
                   v.plate_number, i.incident_number, i.description as exception_reason
            FROM logistics_shipments s
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            LEFT JOIN logistics_drivers d ON s.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            LEFT JOIN logistics_incidents i ON s.id = i.shipment_id
                AND i.incident_type LIKE '%missed%'
            WHERE s.status IN ('failed_delivery', 'delivery_attempted')
            AND date(s.updated_at) BETWEEN ? AND ?
            ORDER BY s.updated_at DESC
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/exceptions/missed_deliveries.html',
                             title='Missed Deliveries',
                             date_from=date_from,
                             date_to=date_to,
                             missed=[dict(m) for m in missed])
    finally:
        db.close()


@logistics_bp.route('/exceptions/vehicle-breakdown')
@logistics_login_required
def exceptions_vehicle_breakdown():
    """Vehicle Breakdown Exceptions."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))

        breakdowns = db.execute("""
            SELECT i.*, v.vehicle_code, v.plate_number, v.vehicle_type,
                   d.full_name as driver_name, s.shipment_code
            FROM logistics_incidents i
            LEFT JOIN logistics_vehicles v ON i.vehicle_id = v.id
            LEFT JOIN logistics_drivers d ON i.driver_id = d.id
            LEFT JOIN logistics_shipments s ON i.shipment_id = s.id
            WHERE i.incident_type IN ('vehicle_breakdown', 'Breakdown', 'Vehicle Breakdown')
            AND date(i.incident_date) BETWEEN ? AND ?
            ORDER BY i.severity DESC, i.incident_date DESC
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/exceptions/vehicle_breakdown.html',
                             title='Vehicle Breakdowns',
                             date_from=date_from,
                             date_to=date_to,
                             breakdowns=[dict(b) for b in breakdowns])
    finally:
        db.close()


@logistics_bp.route('/exceptions/pod-missing')
@logistics_bp.route('/exceptions/pod-missing')
@logistics_login_required
def exceptions_pod_missing():
    """Missing POD Exceptions."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))

        missing_pod = db.execute("""
            SELECT s.*, c.name as customer_name, d.full_name as driver_name,
                   v.plate_number
            FROM logistics_shipments s
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            LEFT JOIN logistics_drivers d ON s.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            WHERE s.status = 'delivered'
            AND s.id NOT IN (
                SELECT shipment_id FROM logistics_pod_records WHERE shipment_id IS NOT NULL
            )
            AND date(s.actual_delivery) BETWEEN ? AND ?
            ORDER BY s.actual_delivery DESC
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/exceptions/pod_missing.html',
                             title='Missing POD',
                             date_from=date_from,
                             date_to=date_to,
                             missing_pod=[dict(m) for m in missing_pod])
    finally:
        db.close()


@logistics_bp.route('/exceptions/route-deviations')
@logistics_login_required
def exceptions_route_deviations():
    """Route Deviation Exceptions."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))

        deviations = db.execute("""
            SELECT i.*, v.vehicle_code, v.plate_number,
                   d.full_name as driver_name, s.shipment_code
            FROM logistics_incidents i
            LEFT JOIN logistics_vehicles v ON i.vehicle_id = v.id
            LEFT JOIN logistics_drivers d ON i.driver_id = d.id
            LEFT JOIN logistics_shipments s ON i.shipment_id = s.id
            WHERE i.incident_type IN ('route_deviation', 'Route Deviation')
            AND date(i.incident_date) BETWEEN ? AND ?
            ORDER BY i.severity DESC, i.incident_date DESC
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/exceptions/route_deviations.html',
                             title='Route Deviations',
                             date_from=date_from,
                             date_to=date_to,
                             deviations=[dict(d) for d in deviations])
    finally:
        db.close()


@logistics_bp.route('/exceptions/driver-issues')
@logistics_login_required
def exceptions_driver_issues():
    """Driver Issue Exceptions."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))

        issues = db.execute("""
            SELECT i.*, d.full_name as driver_name, d.mobile, d.license_number,
                   v.vehicle_code, v.plate_number, s.shipment_code
            FROM logistics_incidents i
            LEFT JOIN logistics_drivers d ON i.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON i.vehicle_id = v.id
            LEFT JOIN logistics_shipments s ON i.shipment_id = s.id
            WHERE i.incident_type IN ('driver_issue', 'driver_absence', 'Driver Absence',
                                      'Driver Issue', 'driver_unavailable')
            AND date(i.incident_date) BETWEEN ? AND ?
            ORDER BY i.severity DESC, i.incident_date DESC
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/exceptions/driver_issues.html',
                             title='Driver Issues',
                             date_from=date_from,
                             date_to=date_to,
                             issues=[dict(i) for i in issues])
    finally:
        db.close()


@logistics_bp.route('/exceptions/fuel-cost-anomalies')
@logistics_login_required
def exceptions_fuel_anomalies():
    """Fuel/Cost Anomaly Exceptions."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', today.strftime('%Y-%m-%d'))

        # Find anomalies: fuel cost > 2x average for same distance
        anomalies = db.execute("""
            SELECT t.*, v.vehicle_code, v.plate_number,
                   d.full_name as driver_name,
                   t.fuel_cost / NULLIF(t.distance_km, 0) * 100 as cost_per_100km,
                   (SELECT AVG(fuel_cost / NULLIF(distance_km, 0) * 100)
                    FROM logistics_trips
                    WHERE status IN ('completed', 'closed')
                    AND distance_km > 0
                    AND date(planned_departure) BETWEEN ? AND ?) as avg_cost_per_100km
            FROM logistics_trips t
            LEFT JOIN logistics_vehicles v ON t.vehicle_id = v.id
            LEFT JOIN logistics_drivers d ON t.driver_id = d.id
            WHERE t.status IN ('completed', 'closed')
            AND t.distance_km > 50
            AND t.fuel_cost / NULLIF(t.distance_km, 0) * 100 >
                (SELECT AVG(fuel_cost / NULLIF(distance_km, 0) * 100) * 1.5
                 FROM logistics_trips
                 WHERE status IN ('completed', 'closed')
                 AND distance_km > 0
                 AND date(planned_departure) BETWEEN ? AND ?)
            AND date(t.planned_departure) BETWEEN ? AND ?
            ORDER BY cost_per_100km DESC
        """, (date_from, date_to, date_from, date_to, date_from, date_to)).fetchall()

        return render_template('logistics/exceptions/fuel_anomalies.html',
                             title='Fuel Cost Anomalies',
                             date_from=date_from,
                             date_to=date_to,
                             anomalies=[dict(a) for a in anomalies])
    finally:
        db.close()


@logistics_bp.route('/exceptions/critical-alerts')
@logistics_login_required
def exceptions_critical_alerts():
    """Critical Alerts."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=7)).strftime('%Y-%m-%d'))
        date_to = today.strftime('%Y-%m-%d')

        critical = db.execute("""
            SELECT i.*, s.shipment_code, d.full_name as driver_name,
                   v.plate_number, c.name as customer_name
            FROM logistics_incidents i
            LEFT JOIN logistics_shipments s ON i.shipment_id = s.id
            LEFT JOIN logistics_drivers d ON i.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON i.vehicle_id = v.id
            LEFT JOIN sdad_customers c ON i.customer_id = c.id
            WHERE i.severity = 'critical'
            AND i.status = 'open'
            ORDER BY i.created_at DESC
        """).fetchall()

        return render_template('logistics/exceptions/critical_alerts.html',
                             title='Critical Alerts',
                             date_from=date_from,
                             date_to=date_to,
                             critical=[dict(c) for c in critical])
    finally:
        db.close()


@logistics_bp.route('/exceptions/<int:id>/resolve', methods=['GET', 'POST'])
@logistics_login_required
def exceptions_resolve(id):
    """Resolve Exception."""
    user = get_current_user()
    db = get_db()

    try:
        exception = db.execute("""
            SELECT i.*, s.shipment_code, d.full_name as driver_name,
                   v.plate_number
            FROM logistics_incidents i
            LEFT JOIN logistics_shipments s ON i.shipment_id = s.id
            LEFT JOIN logistics_drivers d ON i.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON i.vehicle_id = v.id
            WHERE i.id = ?
        """, (id,)).fetchone()

        if not exception:
            flash('Exception not found.', 'error')
            return redirect(url_for('logistics.exceptions_index'))

        if request.method == 'POST':
            data = request.form
            db.execute("""
                UPDATE logistics_incidents SET
                    status = 'resolved',
                    action_taken = ?,
                    cost_impact = ?,
                    closed_by = ?,
                    closed_at = CURRENT_TIMESTAMP,
                    closure_notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                data.get('action_taken'),
                float(data.get('cost_impact', 0)),
                user['id'],
                data.get('closure_notes'),
                id
            ))
            db.commit()
            flash('Exception resolved!', 'success')
            return redirect(url_for('logistics.exceptions_index'))

        return render_template('logistics/exceptions/resolve.html',
                             title=f"Resolve Exception {exception['incident_number']}",
                             exception=dict(exception))
    finally:
        db.close()


@logistics_bp.route('/exceptions/<int:id>/escalate', methods=['POST'])
@logistics_login_required
def exceptions_escalate(id):
    """Escalate Exception."""
    user = get_current_user()
    db = get_db()

    try:
        data = request.form
        db.execute("""
            UPDATE logistics_incidents SET
                severity = CASE severity
                    WHEN 'low' THEN 'medium'
                    WHEN 'medium' THEN 'high'
                    WHEN 'high' THEN 'critical'
                    ELSE 'critical'
                END,
                notes = COALESCE(notes, '') || ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (f"\n[ESCALATED {datetime.now().strftime('%Y-%m-%d %H:%M')}] {data.get('escalation_reason', '')}", id))
        db.commit()
        flash('Exception escalated!', 'warning')
        return redirect(url_for('logistics.exceptions_index'))
    finally:
        db.close()


@logistics_bp.route('/exceptions/reports')
@logistics_login_required
def exceptions_reports():
    """Exception Reports."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = today.strftime('%Y-%m-%d')

        # Summary
        summary = db.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open,
                SUM(CASE WHEN status = 'resolved' THEN 1 ELSE 0 END) as resolved,
                SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed,
                SUM(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) as critical,
                SUM(CASE WHEN severity = 'high' THEN 1 ELSE 0 END) as high,
                SUM(CASE WHEN severity = 'medium' THEN 1 ELSE 0 END) as medium,
                SUM(CASE WHEN severity = 'low' THEN 1 ELSE 0 END) as low,
                SUM(cost_impact) as total_cost
            FROM logistics_incidents
            WHERE date(created_at) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()

        # By type
        by_type = db.execute("""
            SELECT incident_type,
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'open' THEN 1 ELSE 0 END) as open,
                   SUM(cost_impact) as cost
            FROM logistics_incidents
            WHERE date(created_at) BETWEEN ? AND ?
            GROUP BY incident_type
            ORDER BY total DESC
        """, (date_from, date_to)).fetchall()

        # By driver
        by_driver = db.execute("""
            SELECT d.full_name, d.driver_code,
                   COUNT(i.id) as exception_count,
                   SUM(CASE WHEN i.severity IN ('critical', 'high') THEN 1 ELSE 0 END) as severe_count
            FROM logistics_drivers d
            LEFT JOIN logistics_incidents i ON d.id = i.driver_id
                AND date(i.created_at) BETWEEN ? AND ?
            WHERE d.status = 'active'
            GROUP BY d.id
            HAVING exception_count > 0
            ORDER BY severe_count DESC, exception_count DESC
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/exceptions/reports.html',
                             title='Exception Reports',
                             date_from=date_from,
                             date_to=date_to,
                             summary=dict(summary) if summary else {},
                             by_type=[dict(t) for t in by_type],
                             by_driver=[dict(d) for d in by_driver])
    finally:
        db.close()


# =============================================================================
# 15d. DOCUMENTS/EXPORT CENTER
# =============================================================================

@logistics_bp.route('/documents/delivery')
@logistics_login_required
def documents_delivery():
    """Delivery Documents."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = today.strftime('%Y-%m-%d')

        documents = db.execute("""
            SELECT td.*, s.shipment_code, t.trip_code
            FROM logistics_transport_documents td
            LEFT JOIN logistics_shipments s ON td.shipment_id = s.id
            LEFT JOIN logistics_trips t ON td.trip_id = t.id
            WHERE td.doc_type = 'delivery'
            AND date(td.created_at) BETWEEN ? AND ?
            ORDER BY td.created_at DESC
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/documents/delivery.html',
                             title='Delivery Documents',
                             date_from=date_from,
                             date_to=date_to,
                             documents=[dict(d) for d in documents])
    finally:
        db.close()


@logistics_bp.route('/documents/trip')
@logistics_login_required
def documents_trip():
    """Trip Documents."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = today.strftime('%Y-%m-%d')

        documents = db.execute("""
            SELECT td.*, t.trip_code, v.plate_number, d.full_name as driver_name
            FROM logistics_transport_documents td
            LEFT JOIN logistics_trips t ON td.trip_id = t.id
            LEFT JOIN logistics_vehicles v ON td.vehicle_id = v.id
            LEFT JOIN logistics_drivers d ON td.driver_id = d.id
            WHERE td.doc_type = 'trip'
            AND date(td.created_at) BETWEEN ? AND ?
            ORDER BY td.created_at DESC
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/documents/trip.html',
                             title='Trip Documents',
                             date_from=date_from,
                             date_to=date_to,
                             documents=[dict(d) for d in documents])
    finally:
        db.close()


@logistics_bp.route('/documents/pod')
@logistics_login_required
def documents_pod():
    """POD Documents."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = today.strftime('%Y-%m-%d')

        pod_records = db.execute("""
            SELECT p.*, s.shipment_code, d.full_name as driver_name
            FROM logistics_pod_records p
            LEFT JOIN logistics_shipments s ON p.shipment_id = s.id
            LEFT JOIN logistics_drivers d ON p.driver_id = d.id
            WHERE date(p.delivery_timestamp) BETWEEN ? AND ?
            ORDER BY p.delivery_timestamp DESC
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/documents/pod.html',
                             title='POD Documents',
                             date_from=date_from,
                             date_to=date_to,
                             pod_records=[dict(p) for p in pod_records])
    finally:
        db.close()


@logistics_bp.route('/documents/vehicle')
@logistics_login_required
def documents_vehicle():
    """Vehicle Documents."""
    user = get_current_user()
    db = get_db()

    try:
        documents = db.execute("""
            SELECT vd.*, v.vehicle_code, v.plate_number, v.vehicle_type,
                   vd.document_type
            FROM logistics_vehicle_documents vd
            JOIN logistics_vehicles v ON vd.vehicle_id = v.id
            ORDER BY v.plate_number, vd.expiry_date
        """).fetchall()

        # Expiring soon
        expiring = db.execute("""
            SELECT vd.*, v.vehicle_code, v.plate_number
            FROM logistics_vehicle_documents vd
            JOIN logistics_vehicles v ON vd.vehicle_id = v.id
            WHERE vd.expiry_date BETWEEN ? AND ?
            ORDER BY vd.expiry_date
        """, (today.strftime('%Y-%m-%d'), (today + timedelta(days=30)).strftime('%Y-%m-%d'))).fetchall()

        return render_template('logistics/documents/vehicle.html',
                             title='Vehicle Documents',
                             documents=[dict(d) for d in documents],
                             expiring=[dict(e) for e in expiring])
    finally:
        db.close()


@logistics_bp.route('/documents/driver')
@logistics_login_required
def documents_driver():
    """Driver Documents."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        documents = db.execute("""
            SELECT dd.*, d.driver_code, d.full_name, d.license_number,
                   dd.document_type
            FROM logistics_driver_documents dd
            JOIN logistics_drivers d ON dd.driver_id = d.id
            ORDER BY d.full_name, dd.expiry_date
        """).fetchall()

        # Expiring soon
        expiring = db.execute("""
            SELECT dd.*, d.driver_code, d.full_name
            FROM logistics_driver_documents dd
            JOIN logistics_drivers d ON dd.driver_id = d.id
            WHERE dd.expiry_date BETWEEN ? AND ?
            ORDER BY dd.expiry_date
        """, (today.strftime('%Y-%m-%d'), (today + timedelta(days=30)).strftime('%Y-%m-%d'))).fetchall()

        return render_template('logistics/documents/driver.html',
                             title='Driver Documents',
                             documents=[dict(d) for d in documents],
                             expiring=[dict(e) for e in expiring])
    finally:
        db.close()


@logistics_bp.route('/export/center')
@logistics_login_required
def export_center():
    """Export Center with Column Selection."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = today.strftime('%Y-%m-%d')
        export_type = request.args.get('type', 'trips')

        return render_template('logistics/export/center.html',
                             title='Export Center',
                             date_from=date_from,
                             date_to=date_to,
                             export_type=export_type)
    finally:
        db.close()


@logistics_bp.route('/export/trips')
@logistics_login_required
def export_trips():
    """Export Trips Data."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', datetime.now().strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
        format_type = request.args.get('format', 'csv')
        columns = request.args.getlist('columns') or ['trip_code', 'status', 'driver_name', 'vehicle', 'origin', 'destination', 'distance_km', 'actual_cost']

        # Get trip data
        trips = db.execute("""
            SELECT t.trip_code, t.trip_name, t.status, t.priority,
                   d.full_name as driver_name, v.plate_number as vehicle,
                   t.origin_location as origin, t.destination_location as destination,
                   t.distance_km, t.estimated_cost, t.actual_cost,
                   t.planned_departure, t.actual_departure,
                   t.planned_arrival, t.actual_arrival,
                   t.total_stops, t.completed_stops, t.failed_stops,
                   t.fuel_cost, t.tolls_cost, t.driver_allowance,
                   t.notes, t.created_at
            FROM logistics_trips t
            LEFT JOIN logistics_drivers d ON t.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON t.vehicle_id = v.id
            WHERE date(t.created_at) BETWEEN ? AND ?
            ORDER BY t.created_at DESC
        """, (date_from, date_to)).fetchall()

        if format_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for trip in trips:
                writer.writerow([trip.get(col, '') for col in columns])
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=trips_export_{date_from}_{date_to}.csv'}
            )
        elif format_type == 'excel':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for trip in trips:
                writer.writerow([trip.get(col, '') for col in columns])
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='application/vnd.ms-excel',
                headers={'Content-Disposition': f'attachment; filename=trips_export_{date_from}_{date_to}.xls'}
            )
        else:
            return jsonify({'data': [dict(t) for t in trips], 'columns': columns})
    finally:
        db.close()


@logistics_bp.route('/export/dispatches')
@logistics_login_required
def export_dispatches():
    """Export Dispatches Data."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', datetime.now().strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
        format_type = request.args.get('format', 'csv')
        columns = request.args.getlist('columns') or ['shipment_code', 'status', 'customer', 'driver', 'vehicle', 'priority', 'planned_date']

        dispatches = db.execute("""
            SELECT s.shipment_code, s.status, s.priority, s.shipment_type,
                   c.name as customer, d.full_name as driver,
                   v.plate_number as vehicle, s.planned_date,
                   s.dispatched_date, s.delivery_address,
                   sl.quantity as total_items,
                   s.notes, s.created_at
            FROM logistics_shipments s
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            LEFT JOIN logistics_drivers d ON s.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            LEFT JOIN logistics_shipment_lines sl ON s.id = sl.shipment_id
            WHERE s.status NOT IN ('draft', 'cancelled')
            AND date(s.created_at) BETWEEN ? AND ?
            GROUP BY s.id
            ORDER BY s.created_at DESC
        """, (date_from, date_to)).fetchall()

        if format_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for d in dispatches:
                writer.writerow([d.get(col, '') for col in columns])
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=dispatches_export_{date_from}_{date_to}.csv'}
            )
        elif format_type == 'excel':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for d in dispatches:
                writer.writerow([d.get(col, '') for col in columns])
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='application/vnd.ms-excel',
                headers={'Content-Disposition': f'attachment; filename=dispatches_export_{date_from}_{date_to}.xls'}
            )
        else:
            return jsonify({'data': [dict(d) for d in dispatches], 'columns': columns})
    finally:
        db.close()


@logistics_bp.route('/export/routes')
@logistics_login_required
def export_routes():
    """Export Routes Data."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', datetime.now().strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
        format_type = request.args.get('format', 'csv')
        columns = request.args.getlist('columns') or ['route_code', 'route_name', 'origin', 'destination', 'distance_km', 'estimated_time']

        routes = db.execute("""
            SELECT r.route_code, r.route_name,
                   r.origin_id, r.destination_id,
                   r.distance_km, r.estimated_time_minutes,
                   r.cost_per_km, r.is_active,
                   (SELECT COUNT(*) FROM logistics_shipments s WHERE s.route_id = r.id) as shipment_count,
                   r.created_at
            FROM logistics_route_masters r
            WHERE r.is_active = 1
            ORDER BY r.route_name
        """).fetchall()

        if format_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for r in routes:
                writer.writerow([r.get(col, '') for col in columns])
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=routes_export_{date_from}_{date_to}.csv'}
            )
        elif format_type == 'excel':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for r in routes:
                writer.writerow([r.get(col, '') for col in columns])
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='application/vnd.ms-excel',
                headers={'Content-Disposition': f'attachment; filename=routes_export_{date_from}_{date_to}.xls'}
            )
        else:
            return jsonify({'data': [dict(r) for r in routes], 'columns': columns})
    finally:
        db.close()


@logistics_bp.route('/export/vehicle-performance')
@logistics_login_required
def export_vehicle_performance():
    """Export Vehicle Performance Data."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', datetime.now().strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
        format_type = request.args.get('format', 'csv')
        columns = request.args.getlist('columns') or ['vehicle_code', 'plate_number', 'trips', 'total_km', 'fuel_cost', 'utilization']

        performance = db.execute("""
            SELECT v.vehicle_code, v.plate_number, v.vehicle_type,
                   COUNT(DISTINCT t.id) as trips,
                   COALESCE(SUM(t.distance_km), 0) as total_km,
                   COALESCE(SUM(t.actual_cost), 0) as total_cost,
                   COALESCE(SUM(t.fuel_cost), 0) as fuel_cost,
                   COALESCE(SUM(t.tolls_cost), 0) as tolls_cost,
                   COALESCE(AVG(fk.on_time_rate), 0) as on_time_rate,
                   COALESCE(AVG(fk.fuel_liters), 0) as avg_fuel_liters
            FROM logistics_vehicles v
            LEFT JOIN logistics_trips t ON v.id = t.vehicle_id
                AND t.status IN ('completed', 'closed')
                AND date(t.planned_departure) BETWEEN ? AND ?
            LEFT JOIN logistics_fleet_kpis fk ON v.id = fk.vehicle_id
                AND date(fk.kpi_date) BETWEEN ? AND ?
            WHERE v.status = 'active'
            GROUP BY v.id
            ORDER BY total_km DESC
        """, (date_from, date_to, date_from, date_to)).fetchall()

        if format_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for p in performance:
                writer.writerow([p.get(col, '') for col in columns])
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=vehicle_performance_{date_from}_{date_to}.csv'}
            )
        elif format_type == 'excel':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for p in performance:
                writer.writerow([p.get(col, '') for col in columns])
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='application/vnd.ms-excel',
                headers={'Content-Disposition': f'attachment; filename=vehicle_performance_{date_from}_{date_to}.xls'}
            )
        else:
            return jsonify({'data': [dict(p) for p in performance], 'columns': columns})
    finally:
        db.close()


@logistics_bp.route('/export/driver-performance')
@logistics_login_required
def export_driver_performance():
    """Export Driver Performance Data."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', datetime.now().strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
        format_type = request.args.get('format', 'csv')
        columns = request.args.getlist('columns') or ['driver_code', 'full_name', 'trips', 'deliveries', 'total_km']

        performance = db.execute("""
            SELECT d.driver_code, d.full_name, d.mobile,
                   COUNT(DISTINCT t.id) as trips,
                   COUNT(DISTINCT s.id) as deliveries,
                   COALESCE(SUM(t.distance_km), 0) as total_km,
                   COALESCE(SUM(t.completed_stops), 0) as stops_completed,
                   COALESCE(SUM(t.failed_stops), 0) as stops_failed,
                   COALESCE(AVG(fk.on_time_rate), 0) as on_time_rate
            FROM logistics_drivers d
            LEFT JOIN logistics_trips t ON d.id = t.driver_id
                AND t.status IN ('completed', 'closed')
                AND date(t.planned_departure) BETWEEN ? AND ?
            LEFT JOIN logistics_shipments s ON d.id = s.driver_id
                AND date(s.created_at) BETWEEN ? AND ?
            LEFT JOIN logistics_fleet_kpis fk ON d.id = fk.driver_id
                AND date(fk.kpi_date) BETWEEN ? AND ?
            WHERE d.status = 'active'
            GROUP BY d.id
            ORDER BY trips DESC
        """, (date_from, date_to, date_from, date_to, date_from, date_to)).fetchall()

        if format_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for p in performance:
                writer.writerow([p.get(col, '') for col in columns])
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=driver_performance_{date_from}_{date_to}.csv'}
            )
        elif format_type == 'excel':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for p in performance:
                writer.writerow([p.get(col, '') for col in columns])
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='application/vnd.ms-excel',
                headers={'Content-Disposition': f'attachment; filename=driver_performance_{date_from}_{date_to}.xls'}
            )
        else:
            return jsonify({'data': [dict(p) for p in performance], 'columns': columns})
    finally:
        db.close()


@logistics_bp.route('/export/costs')
@logistics_login_required
def export_costs():
    """Export Cost Reports."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', datetime.now().strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
        format_type = request.args.get('format', 'csv')
        columns = request.args.getlist('columns') or ['shipment_code', 'cost_type', 'amount', 'cost_category']

        costs = db.execute("""
            SELECT s.shipment_code, c.cost_type, c.amount, c.currency,
                   c.cost_category, c.description, c.invoice_reference,
                   c.is_approved, c.created_at
            FROM logistics_cost_entries c
            LEFT JOIN logistics_shipments s ON c.shipment_id = s.id
            WHERE date(c.created_at) BETWEEN ? AND ?
            ORDER BY c.created_at DESC
        """, (date_from, date_to)).fetchall()

        if format_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for c in costs:
                writer.writerow([c.get(col, '') for col in columns])
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=costs_export_{date_from}_{date_to}.csv'}
            )
        elif format_type == 'excel':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for c in costs:
                writer.writerow([c.get(col, '') for col in columns])
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='application/vnd.ms-excel',
                headers={'Content-Disposition': f'attachment; filename=costs_export_{date_from}_{date_to}.xls'}
            )
        else:
            return jsonify({'data': [dict(c) for c in costs], 'columns': columns})
    finally:
        db.close()


@logistics_bp.route('/export/pod')
@logistics_login_required
def export_pod():
    """Export POD Records."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', datetime.now().strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
        format_type = request.args.get('format', 'csv')
        columns = request.args.getlist('columns') or ['shipment_code', 'receiver_name', 'delivery_timestamp', 'delivery_status']

        pod_records = db.execute("""
            SELECT p.id, s.shipment_code, p.receiver_name, p.receiver_phone,
                   p.delivery_timestamp, p.delivery_status,
                   p.shortage_confirmed, p.damage_confirmed,
                   p.notes, p.created_at
            FROM logistics_pod_records p
            LEFT JOIN logistics_shipments s ON p.shipment_id = s.id
            WHERE date(p.delivery_timestamp) BETWEEN ? AND ?
            ORDER BY p.delivery_timestamp DESC
        """, (date_from, date_to)).fetchall()

        if format_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for p in pod_records:
                writer.writerow([p.get(col, '') for col in columns])
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=pod_export_{date_from}_{date_to}.csv'}
            )
        elif format_type == 'excel':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for p in pod_records:
                writer.writerow([p.get(col, '') for col in columns])
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='application/vnd.ms-excel',
                headers={'Content-Disposition': f'attachment; filename=pod_export_{date_from}_{date_to}.xls'}
            )
        else:
            return jsonify({'data': [dict(p) for p in pod_records], 'columns': columns})
    finally:
        db.close()


@logistics_bp.route('/export/exceptions')
@logistics_login_required
def export_exceptions():
    """Export Exceptions Data."""
    user = get_current_user()
    db = get_db()

    try:
        date_from = request.args.get('date_from', datetime.now().strftime('%Y-%m-01'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
        format_type = request.args.get('format', 'csv')
        columns = request.args.getlist('columns') or ['incident_number', 'incident_type', 'severity', 'status', 'driver']

        exceptions = db.execute("""
            SELECT i.incident_number, i.incident_type, i.severity, i.status,
                   d.full_name as driver, v.plate_number as vehicle,
                   s.shipment_code, i.cost_impact, i.incident_date,
                   i.description, i.action_taken, i.created_at
            FROM logistics_incidents i
            LEFT JOIN logistics_drivers d ON i.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON i.vehicle_id = v.id
            LEFT JOIN logistics_shipments s ON i.shipment_id = s.id
            WHERE date(i.created_at) BETWEEN ? AND ?
            ORDER BY i.created_at DESC
        """, (date_from, date_to)).fetchall()

        if format_type == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for e in exceptions:
                writer.writerow([e.get(col, '') for col in columns])
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='text/caml',
                headers={'Content-Disposition': f'attachment; filename=exceptions_export_{date_from}_{date_to}.csv'}
            )
        elif format_type == 'excel':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(columns)
            for e in exceptions:
                writer.writerow([e.get(col, '') for col in columns])
            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='application/vnd.ms-excel',
                headers={'Content-Disposition': f'attachment; filename=exceptions_export_{date_from}_{date_to}.xls'}
            )
        else:
            return jsonify({'data': [dict(e) for e in exceptions], 'columns': columns})
    finally:
        db.close()


@logistics_bp.route('/documents/print-template')
@logistics_login_required
def documents_print_template():
    """Print Templates."""
    user = get_current_user()
    db = get_db()

    try:
        templates = db.execute("""
            SELECT * FROM logistics_document_templates
            WHERE is_active = 1
            ORDER BY document_type, template_name
        """).fetchall()

        return render_template('logistics/documents/print_templates.html',
                             title='Print Templates',
                             templates=[dict(t) for t in templates])
    finally:
        db.close()


@logistics_bp.route('/documents/output-history')
@logistics_login_required
def documents_output_history():
    """Output History - Previously Generated Documents."""
    user = get_current_user()
    db = get_db()

    try:
        today = datetime.now().date()
        date_from = request.args.get('date_from', (today - timedelta(days=30)).strftime('%Y-%m-%d'))
        date_to = today.strftime('%Y-%m-%d')

        history = db.execute("""
            SELECT gd.*, s.shipment_code, t.trip_code,
                   u.username as generated_by_name
            FROM logistics_generated_documents gd
            LEFT JOIN logistics_shipments s ON gd.shipment_id = s.id
            LEFT JOIN logistics_trips t ON gd.trip_id = t.id
            LEFT JOIN users u ON gd.generated_by = u.id
            WHERE date(gd.generated_at) BETWEEN ? AND ?
            ORDER BY gd.generated_at DESC
            LIMIT 100
        """, (date_from, date_to)).fetchall()

        return render_template('logistics/documents/output_history.html',
                             title='Output History',
                             date_from=date_from,
                             date_to=date_to,
                             history=[dict(h) for h in history])
    finally:
        db.close()


# =============================================================================
# API ENDPOINTS
# =============================================================================

@logistics_bp.route('/api/stats')
@logistics_login_required
def api_stats():
    """Get logistics dashboard stats as JSON."""
    user = get_current_user()

    try:
        stats = {
            'shipment_stats': get_shipment_stats(company_id=user.get('company_id')),
            'driver_stats': get_driver_availability_stats(),
            'vehicle_stats': get_vehicle_availability_stats(),
            'open_incidents': get_open_incidents_count(),
            'pod_pending': get_pod_pending_count(),
        }
        return jsonify(stats)
    finally:
        pass


@logistics_bp.route('/api/shipment/<int:id>')
@logistics_login_required
def api_shipment(id):
    """Get shipment details as JSON."""
    db = get_db()

    try:
        shipment = db.execute("""
            SELECT s.*, c.name as customer_name,
                   d.full_name as driver_name,
                   v.plate_number
            FROM logistics_shipments s
            LEFT JOIN sdad_customers c ON s.customer_id = c.id
            LEFT JOIN logistics_drivers d ON s.driver_id = d.id
            LEFT JOIN logistics_vehicles v ON s.vehicle_id = v.id
            WHERE s.id = ?
        """, (id,)).fetchone()

        if not shipment:
            return jsonify({'error': 'Shipment not found'}), 404

        lines = db.execute("SELECT * FROM logistics_shipment_lines WHERE shipment_id = ?", (id,)).fetchall()

        result = dict(shipment)
        result['lines'] = [dict(l) for l in lines]
        return jsonify(result)
    finally:
        db.close()


@logistics_bp.route('/api/drivers/available')
@logistics_login_required
def api_drivers_available():
    """Get available drivers as JSON."""
    db = get_db()

    try:
        drivers = db.execute("""
            SELECT * FROM logistics_drivers
            WHERE status = 'active' AND availability = 'available'
            ORDER BY full_name
        """).fetchall()
        return jsonify([dict(d) for d in drivers])
    finally:
        db.close()


@logistics_bp.route('/api/vehicles/available')
@logistics_login_required
def api_vehicles_available():
    """Get available vehicles as JSON."""
    db = get_db()

    try:
        vehicles = db.execute("""
            SELECT * FROM logistics_vehicles
            WHERE status = 'active' AND availability = 'available'
            ORDER BY plate_number
        """).fetchall()
        return jsonify([dict(v) for v in vehicles])
    finally:
        db.close()


# =============================================================================
# API EXPORT ENDPOINTS
# =============================================================================

@logistics_bp.route('/api/export/<export_type>', methods=['GET', 'POST'])
@logistics_bp.route('/api/export/<data_type>/<export_type>', methods=['GET', 'POST'])
@logistics_login_required
def api_logistics_export(export_type, data_type=None):
    """Export logistics data in all 20 formats."""
    if export_type not in LOGISTICS_EXPORT_TYPES:
        return jsonify({
            'error': f'Invalid export type. Valid types: {LOGISTICS_EXPORT_TYPES}'
        }), 400

    db = get_db()
    try:
        company_id = session.get('company_id', 0)

        # Determine data type from URL or default
        if data_type is None:
            data_type = request.args.get('type', 'shipments')

        # Get data based on type
        if data_type == 'shipments':
            data = db.execute("""
                SELECT * FROM logistics_shipments
                WHERE company_id = ?
                ORDER BY created_at DESC
                LIMIT 5000
            """, (company_id,)).fetchall()
            data = [dict(row) for row in data]
            columns = LOGISTICS_EXPORT_COLUMNS['shipments']
            title = 'Logistics Shipments'
        elif data_type == 'delivery_orders':
            data = db.execute("""
                SELECT * FROM logistics_delivery_orders
                WHERE company_id = ?
                ORDER BY created_at DESC
                LIMIT 5000
            """, (company_id,)).fetchall()
            data = [dict(row) for row in data]
            columns = LOGISTICS_EXPORT_COLUMNS['delivery_orders']
            title = 'Delivery Orders'
        elif data_type == 'pickup_orders':
            data = db.execute("""
                SELECT * FROM logistics_pickup_orders
                WHERE company_id = ?
                ORDER BY created_at DESC
                LIMIT 5000
            """, (company_id,)).fetchall()
            data = [dict(row) for row in data]
            columns = LOGISTICS_EXPORT_COLUMNS['pickup_orders']
            title = 'Pickup Orders'
        elif data_type == 'trips':
            data = db.execute("""
                SELECT * FROM logistics_trips
                WHERE company_id = ?
                ORDER BY created_at DESC
                LIMIT 5000
            """, (company_id,)).fetchall()
            data = [dict(row) for row in data]
            columns = LOGISTICS_EXPORT_COLUMNS['trips']
            title = 'Logistics Trips'
        elif data_type == 'routes':
            data = db.execute("""
                SELECT * FROM logistics_routes
                WHERE company_id = ?
                ORDER BY route_name
                LIMIT 5000
            """, (company_id,)).fetchall()
            data = [dict(row) for row in data]
            columns = LOGISTICS_EXPORT_COLUMNS['routes']
            title = 'Logistics Routes'
        elif data_type == 'vehicles':
            data = db.execute("""
                SELECT * FROM logistics_vehicles
                WHERE company_id = ?
                ORDER BY plate_number
                LIMIT 5000
            """, (company_id,)).fetchall()
            data = [dict(row) for row in data]
            columns = LOGISTICS_EXPORT_COLUMNS['vehicles']
            title = 'Fleet Vehicles'
        elif data_type == 'drivers':
            data = db.execute("""
                SELECT * FROM logistics_drivers
                WHERE company_id = ?
                ORDER BY driver_name
                LIMIT 5000
            """, (company_id,)).fetchall()
            data = [dict(row) for row in data]
            columns = LOGISTICS_EXPORT_COLUMNS['drivers']
            title = 'Drivers'
        elif data_type == 'incidents':
            data = db.execute("""
                SELECT * FROM logistics_incidents
                WHERE company_id = ?
                ORDER BY created_at DESC
                LIMIT 5000
            """, (company_id,)).fetchall()
            data = [dict(row) for row in data]
            columns = LOGISTICS_EXPORT_COLUMNS['incidents']
            title = 'Logistics Incidents'
        elif data_type == 'costs':
            data = db.execute("""
                SELECT * FROM logistics_trip_costs
                WHERE company_id = ?
                ORDER BY cost_date DESC
                LIMIT 5000
            """, (company_id,)).fetchall()
            data = [dict(row) for row in data]
            columns = LOGISTICS_EXPORT_COLUMNS['costs']
            title = 'Trip Costs'
        else:
            return jsonify({'error': f'Data type {data_type} not supported'}), 400

        filename = f'logistics_{data_type}_{datetime.now().strftime("%Y%m%d")}'

        return send_export_response(data, export_type, filename, columns, title)
    finally:
        db.close()


@logistics_bp.route('/api/export/list')
@logistics_login_required
def list_logistics_export_types():
    """List available export types for logistics module."""
    return jsonify({
        'module': 'logistics',
        'data_types': list(LOGISTICS_EXPORT_COLUMNS.keys()),
        'export_types': [{'type': t} for t in LOGISTICS_EXPORT_TYPES]
    })


def register_logistics_routes(app):
    """Register logistics blueprint with the Flask app."""
    app.register_blueprint(logistics_bp)

    # Run logistics migrations on startup
    with app.app_context():
        try:
            run_logistics_migrations()
            print("Logistics Module initialized successfully")
        except Exception as e:
            print(f"Logistics Module initialization error: {e}")
