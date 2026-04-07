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
    get_next_pickup_number, get_next_incident_number, get_shipment_stats,
    get_driver_availability_stats, get_vehicle_availability_stats,
    get_active_shipments_for_dispatch, get_open_incidents_count, get_pod_pending_count,
    LOGISTICS_TABLES
)

logistics_bp = Blueprint('logistics', __name__, url_prefix='/logistics')


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

            # Super admin bypass
            if session.get('role_name') == 'Global Admin':
                return f(*args, **kwargs)

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

        # Count total
        count_query = query.replace("SELECT s.*, c.name as customer_name, d.full_name as driver_name, v.plate_number, w.name as warehouse_name", "SELECT COUNT(*) as cnt")
        total = db.execute(count_query, params).fetchone()['cnt']

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
    return render_template('logistics/reports/menu.html', title='Logistics Reports')


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
