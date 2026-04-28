"""
Maintenance Management Routes
=============================
Comprehensive Flask routes for the Maintenance Management module.

Provides endpoints for:
- Maintenance Dashboard
- Equipment Maintenance
- Facility Management
- Preventive Maintenance (PM) Plans & Schedules
- Corrective Maintenance Requests
- Breakdown/Emergency Maintenance
- Work Orders Management
- Work Order Tasks & Checklists
- Technician & Team Assignment
- Vendor Assignment
- Spare Parts/Material Usage
- Labor/Time Logging
- Downtime Tracking
- Maintenance Cost Tracking
- Inspection & Checklists
- Maintenance Calendar/Planner
- SLA/Escalation Management
- Maintenance Reports
- Maintenance Settings
- Audit Logs

Route Pattern: /maintenance/*
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session, send_file
from functools import wraps
import sqlite3
import os
import json
from datetime import datetime, timedelta
from io import BytesIO

from database import get_db, get_db_context, get_one, get_all, log_audit, create_notification
from permissions import user_has_permission, require_permission
from maintenance_models import (
    init_maintenance_tables,
    get_next_facility_code, get_next_request_number, get_next_team_code,
    get_next_downtime_log_number, get_next_parts_usage_number,
    get_next_labor_log_number, get_next_approval_number,
    get_facility_stats, get_technician_workload, get_pm_compliance_rate,
    generate_pm_work_orders, get_maintenance_dashboard_stats,
    MAINTENANCE_WORK_ORDER_STATUSES, MAINTENANCE_PRIORITIES,
    MAINTENANCE_SEVERITIES, MAINTENANCE_REQUEST_TYPES,
    MAINTENANCE_FREQUENCIES, FACILITY_TYPES, DOWNTIME_IMPACT_LEVELS,
    APPROVAL_STATUSES
)

# Create blueprint
maintenance_bp = Blueprint('maintenance', __name__, url_prefix='/maintenance')


# =============================================================================
# ROUTE REGISTRATION
# =============================================================================

def register_maintenance_routes(app):
    """Register maintenance management routes with the Flask app."""
    init_maintenance_tables()
    app.register_blueprint(maintenance_bp)


# =============================================================================
# AUTHENTICATION AND PERMISSION HELPERS
# =============================================================================

def require_login(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def require_maintenance_permission(action):
    """Decorator factory for maintenance-specific permissions."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please login to access this page.', 'error')
                return redirect(url_for('login'))

            user_id = session['user_id']
            if not user_has_permission(user_id, 'maintenance', 'maintenance', action):
                if request.is_json:
                    return jsonify({'error': 'Permission denied'}), 403
                flash(f"You don't have permission to {action} maintenance records.", 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# =============================================================================
# MAINTENANCE DASHBOARD
# =============================================================================

@maintenance_bp.route('/')
@maintenance_bp.route('/dashboard')
@require_login
def dashboard():
    """Maintenance Management Dashboard."""
    user_id = session.get('user_id')
    user_role = session.get('role_name', '')

    db = get_db()
    try:
        stats = get_maintenance_dashboard_stats()

        # Get recent work orders
        recent_work_orders = db.execute("""
            SELECT mwo.*, a.asset_code, a.name as asset_name,
                   mt.name as maintenance_type,
                   e.first_name || ' ' || e.last_name as technician_name
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            JOIN maintenance_types mt ON mwo.maintenance_type_id = mt.id
            LEFT JOIN hr_employees e ON mwo.assigned_technician_id = e.id
            WHERE mwo.status NOT IN ('Completed', 'Closed', 'Canceled')
            ORDER BY
                CASE mwo.priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,
                mwo.issue_date DESC
            LIMIT 10
        """).fetchall()

        # Get overdue PM schedules
        overdue_pm = db.execute("""
            SELECT ms.*, a.asset_code, a.name as asset_name,
                   mt.name as maintenance_type
            FROM maintenance_schedules ms
            JOIN assets a ON ms.asset_id = a.id
            JOIN maintenance_types mt ON ms.maintenance_type_id = mt.id
            WHERE ms.is_active = 1
            AND ms.next_due_date < date('now')
            ORDER BY ms.next_due_date ASC
            LIMIT 10
        """).fetchall()

        # Get upcoming PM schedules
        upcoming_pm = db.execute("""
            SELECT ms.*, a.asset_code, a.name as asset_name,
                   mt.name as maintenance_type
            FROM maintenance_schedules ms
            JOIN assets a ON ms.asset_id = a.id
            JOIN maintenance_types mt ON ms.maintenance_type_id = mt.id
            WHERE ms.is_active = 1
            AND ms.next_due_date >= date('now')
            AND ms.next_due_date <= date('now', '+14 days')
            ORDER BY ms.next_due_date ASC
            LIMIT 10
        """).fetchall()

        # Get open facility requests
        facility_requests = db.execute("""
            SELECT mfr.*, mf.name as facility_name, mf.facility_code
            FROM maintenance_facility_requests mfr
            JOIN maintenance_facilities mf ON mfr.facility_id = mf.id
            WHERE mfr.status NOT IN ('Completed', 'Closed')
            ORDER BY mfr.is_emergency DESC, mfr.priority ASC
            LIMIT 10
        """).fetchall()

        # Get technician workload
        tech_workload = get_technician_workload()

        return render_template('maintenance/dashboard.html',
                             stats=stats,
                             recent_work_orders=recent_work_orders,
                             overdue_pm=overdue_pm,
                             upcoming_pm=upcoming_pm,
                             facility_requests=facility_requests,
                             tech_workload=tech_workload)
    finally:
        db.close()


# =============================================================================
# EQUIPMENT MAINTENANCE
# =============================================================================

@maintenance_bp.route('/equipment')
@require_login
def equipment_list():
    """Equipment Maintenance List - all assets with maintenance tracking."""
    db = get_db()
    try:
        # Get filter parameters
        status_filter = request.args.get('status', '')
        search = request.args.get('search', '')

        query = """
            SELECT a.*,
                   c.name as category_name,
                   ac.name as condition_rating,
                   (SELECT COUNT(*) FROM maintenance_work_orders mwo WHERE mwo.asset_id = a.id) as total_work_orders,
                   (SELECT COUNT(*) FROM maintenance_work_orders mwo WHERE mwo.asset_id = a.id AND mwo.status NOT IN ('Completed', 'Closed', 'Canceled')) as open_work_orders,
                   (SELECT SUM(mwo.downtime_hours) FROM maintenance_work_orders mwo WHERE mwo.asset_id = a.id) as total_downtime,
                   (SELECT SUM(mwo.actual_cost) FROM maintenance_work_orders mwo WHERE mwo.asset_id = a.id) as total_maintenance_cost
            FROM assets a
            LEFT JOIN asset_categories c ON a.category_id = c.id
            WHERE a.status NOT IN ('Disposed', 'Retired')
        """
        params = []

        if status_filter:
            query += " AND a.status = ?"
            params.append(status_filter)

        if search:
            query += " AND (a.asset_code LIKE ? OR a.name LIKE ? OR a.serial_number LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])

        query += " ORDER BY a.asset_code"

        assets = db.execute(query, params).fetchall()

        # Get status summary
        status_summary = db.execute("""
            SELECT status, COUNT(*) as cnt FROM assets
            WHERE status NOT IN ('Disposed', 'Retired')
            GROUP BY status
        """).fetchall()

        return render_template('maintenance/equipment_list.html',
                             assets=assets,
                             status_filter=status_filter,
                             search=search,
                             status_summary=status_summary)
    finally:
        db.close()


@maintenance_bp.route('/equipment/<int:asset_id>')
@require_login
def equipment_detail(asset_id):
    """Equipment Maintenance Detail - service history, schedules, downtime."""
    db = get_db()
    try:
        # Get asset details
        asset = db.execute("""
            SELECT a.*, c.name as category_name
            FROM assets a
            LEFT JOIN asset_categories c ON a.category_id = c.id
            WHERE a.id = ?
        """, (asset_id,)).fetchone()

        if not asset:
            flash('Asset not found.', 'error')
            return redirect(url_for('maintenance.equipment_list'))

        # Get maintenance history
        maint_history = db.execute("""
            SELECT mwl.*, mt.name as maintenance_type_name,
                   e.first_name || ' ' || e.last_name as technician_name
            FROM maintenance_work_logs mwl
            JOIN maintenance_types mt ON mwl.maintenance_type_id = mt.id
            LEFT JOIN hr_employees e ON mwl.technician_id = e.id
            WHERE mwl.asset_id = ?
            ORDER BY mwl.work_date DESC
            LIMIT 50
        """, (asset_id,)).fetchall()

        # Get maintenance schedules
        schedules = db.execute("""
            SELECT ms.*, mt.name as maintenance_type_name
            FROM maintenance_schedules ms
            JOIN maintenance_types mt ON ms.maintenance_type_id = mt.id
            WHERE ms.asset_id = ? AND ms.is_active = 1
            ORDER BY ms.next_due_date ASC
        """, (asset_id,)).fetchall()

        # Get open work orders
        work_orders = db.execute("""
            SELECT mwo.*, mt.name as maintenance_type
            FROM maintenance_work_orders mwo
            JOIN maintenance_types mt ON mwo.maintenance_type_id = mt.id
            WHERE mwo.asset_id = ? AND mwo.status NOT IN ('Completed', 'Closed', 'Canceled')
            ORDER BY mwo.issue_date DESC
        """, (asset_id,)).fetchall()

        # Get downtime summary
        downtime_summary = db.execute("""
            SELECT
                SUM(downtime_hours) as total_hours,
                COUNT(*) as incident_count,
                AVG(downtime_hours) as avg_hours
            FROM maintenance_work_orders
            WHERE asset_id = ? AND downtime_hours > 0
        """, (asset_id,)).fetchone()

        # Get cost summary
        cost_summary = db.execute("""
            SELECT
                SUM(actual_cost) as total_cost,
                COUNT(*) as order_count,
                AVG(actual_cost) as avg_cost
            FROM maintenance_work_orders
            WHERE asset_id = ? AND actual_cost > 0
        """, (asset_id,)).fetchone()

        return render_template('maintenance/equipment_detail.html',
                             asset=asset,
                             maint_history=maint_history,
                             schedules=schedules,
                             work_orders=work_orders,
                             downtime_summary=downtime_summary,
                             cost_summary=cost_summary)
    finally:
        db.close()


@maintenance_bp.route('/equipment/<int:asset_id>/downtime')
@require_login
def equipment_downtime(asset_id):
    """Equipment Downtime History."""
    db = get_db()
    try:
        asset = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not asset:
            flash('Asset not found.', 'error')
            return redirect(url_for('maintenance.equipment_list'))

        downtime_logs = db.execute("""
            SELECT mdl.*, e.first_name || ' ' || e.last_name as resolved_by_name
            FROM maintenance_downtime_logs mdl
            LEFT JOIN hr_employees e ON mdl.resolved_by = e.id
            WHERE mdl.asset_id = ?
            ORDER BY mdl.downtime_start DESC
        """, (asset_id,)).fetchall()

        # Summary stats
        summary = db.execute("""
            SELECT
                SUM(total_hours) as total_downtime,
                SUM(CASE WHEN planned_downtime = 1 THEN total_hours ELSE 0 END) as planned,
                SUM(CASE WHEN planned_downtime = 0 THEN total_hours ELSE 0 END) as unplanned,
                COUNT(*) as incident_count,
                AVG(total_hours) as avg_duration
            FROM maintenance_downtime_logs
            WHERE asset_id = ?
        """, (asset_id,)).fetchone()

        return render_template('maintenance/equipment_downtime.html',
                             asset=asset,
                             downtime_logs=downtime_logs,
                             summary=summary)
    finally:
        db.close()


# =============================================================================
# FACILITY MANAGEMENT
# =============================================================================

@maintenance_bp.route('/facilities')
@require_login
def facilities_list():
    """Facility Management List."""
    db = get_db()
    try:
        search = request.args.get('search', '')
        type_filter = request.args.get('type', '')

        query = """
            SELECT mf.*,
                   (SELECT COUNT(*) FROM maintenance_facility_requests mfr WHERE mfr.facility_id = mf.id) as total_requests,
                   (SELECT COUNT(*) FROM maintenance_facility_requests mfr WHERE mfr.facility_id = mf.id AND mfr.status NOT IN ('Completed', 'Closed')) as open_requests
            FROM maintenance_facilities mf
            WHERE mf.is_active = 1
        """
        params = []

        if search:
            query += " AND (mf.facility_code LIKE ? OR mf.name LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])

        if type_filter:
            query += " AND mf.facility_type = ?"
            params.append(type_filter)

        query += " ORDER BY mf.name"

        facilities = db.execute(query, params).fetchall()

        return render_template('maintenance/facilities_list.html',
                             facilities=facilities,
                             search=search,
                             type_filter=type_filter,
                             facility_types=FACILITY_TYPES)
    finally:
        db.close()


@maintenance_bp.route('/facilities/new', methods=['GET', 'POST'])
@require_login
def facility_new():
    """Create New Facility."""
    user_id = session.get('user_id')
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.form
            facility_code = get_next_facility_code()

            cursor = db.execute("""
                INSERT INTO maintenance_facilities
                (facility_code, name, description, facility_type, category, address,
                 city, country, postal_code, contact_person, contact_phone, contact_email,
                 company_id, is_critical, operating_hours, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                facility_code,
                data.get('name'),
                data.get('description'),
                data.get('facility_type', 'Building'),
                data.get('category'),
                data.get('address'),
                data.get('city'),
                data.get('country'),
                data.get('postal_code'),
                data.get('contact_person'),
                data.get('contact_phone'),
                data.get('contact_email'),
                data.get('company_id') or None,
                1 if data.get('is_critical') else 0,
                data.get('operating_hours'),
                data.get('notes'),
                user_id
            ))
            db.commit()
            facility_id = cursor.lastrowid

            log_audit('maintenance_facility', facility_id, 'CREATE', user_id)
            flash(f'Facility {facility_code} created successfully.', 'success')
            return redirect(url_for('maintenance.facility_detail', facility_id=facility_id))

        companies = db.execute("SELECT id, name FROM companies ORDER BY name").fetchall()
        return render_template('maintenance/facility_form.html',
                             facility=None,
                             companies=companies)
    finally:
        db.close()


@maintenance_bp.route('/facilities/<int:facility_id>')
@require_login
def facility_detail(facility_id):
    """Facility Detail View."""
    db = get_db()
    try:
        facility = db.execute("SELECT * FROM maintenance_facilities WHERE id = ?",
                            (facility_id,)).fetchone()
        if not facility:
            flash('Facility not found.', 'error')
            return redirect(url_for('maintenance.facilities_list'))

        # Get requests
        requests = db.execute("""
            SELECT mfr.*,
                   e.first_name || ' ' || e.last_name as assigned_technician_name
            FROM maintenance_facility_requests mfr
            LEFT JOIN hr_employees e ON mfr.assigned_technician_id = e.id
            WHERE mfr.facility_id = ?
            ORDER BY mfr.reported_date DESC
            LIMIT 50
        """, (facility_id,)).fetchall()

        # Get stats
        stats = get_facility_stats(facility_id)

        return render_template('maintenance/facility_detail.html',
                             facility=facility,
                             requests=requests,
                             stats=stats)
    finally:
        db.close()


@maintenance_bp.route('/facilities/<int:facility_id>/edit', methods=['GET', 'POST'])
@require_login
def facility_edit(facility_id):
    """Edit Facility."""
    user_id = session.get('user_id')
    db = get_db()
    try:
        facility = db.execute("SELECT * FROM maintenance_facilities WHERE id = ?",
                            (facility_id,)).fetchone()
        if not facility:
            flash('Facility not found.', 'error')
            return redirect(url_for('maintenance.facilities_list'))

        if request.method == 'POST':
            data = request.form

            db.execute("""
                UPDATE maintenance_facilities SET
                    name = ?, description = ?, facility_type = ?, category = ?,
                    address = ?, city = ?, country = ?, postal_code = ?,
                    contact_person = ?, contact_phone = ?, contact_email = ?,
                    is_critical = ?, operating_hours = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                data.get('name'),
                data.get('description'),
                data.get('facility_type'),
                data.get('category'),
                data.get('address'),
                data.get('city'),
                data.get('country'),
                data.get('postal_code'),
                data.get('contact_person'),
                data.get('contact_phone'),
                data.get('contact_email'),
                1 if data.get('is_critical') else 0,
                data.get('operating_hours'),
                data.get('notes'),
                facility_id
            ))
            db.commit()

            log_audit('maintenance_facility', facility_id, 'UPDATE', user_id)
            flash('Facility updated successfully.', 'success')
            return redirect(url_for('maintenance.facility_detail', facility_id=facility_id))

        companies = db.execute("SELECT id, name FROM companies ORDER BY name").fetchall()
        return render_template('maintenance/facility_form.html',
                             facility=facility,
                             companies=companies)
    finally:
        db.close()


# =============================================================================
# FACILITY REQUESTS
# =============================================================================

@maintenance_bp.route('/facility-requests')
@require_login
def facility_requests_list():
    """Facility Maintenance Requests List."""
    db = get_db()
    try:
        status_filter = request.args.get('status', '')
        priority_filter = request.args.get('priority', '')
        search = request.args.get('search', '')

        query = """
            SELECT mfr.*, mf.name as facility_name, mf.facility_code,
                   e.first_name || ' ' || e.last_name as assigned_technician_name
            FROM maintenance_facility_requests mfr
            JOIN maintenance_facilities mf ON mfr.facility_id = mf.id
            LEFT JOIN hr_employees e ON mfr.assigned_technician_id = e.id
            WHERE 1=1
        """
        params = []

        if status_filter:
            query += " AND mfr.status = ?"
            params.append(status_filter)

        if priority_filter:
            query += " AND mfr.priority = ?"
            params.append(priority_filter)

        if search:
            query += " AND (mfr.request_number LIKE ? OR mf.name LIKE ? OR mfr.description LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])

        query += " ORDER BY mfr.is_emergency DESC, mfr.priority ASC, mfr.reported_date DESC"

        requests = db.execute(query, params).fetchall()

        return render_template('maintenance/facility_requests_list.html',
                             requests=requests,
                             status_filter=status_filter,
                             priority_filter=priority_filter,
                             search=search,
                             priorities=MAINTENANCE_PRIORITIES,
                             statuses=['Open', 'In Progress', 'On Hold', 'Completed', 'Closed'])
    finally:
        db.close()


@maintenance_bp.route('/facility-requests/new', methods=['GET', 'POST'])
@require_login
def facility_request_new():
    """Create New Facility Maintenance Request."""
    user_id = session.get('user_id')
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.form
            request_number = get_next_request_number()

            cursor = db.execute("""
                INSERT INTO maintenance_facility_requests
                (request_number, facility_id, request_type, category, priority, severity,
                 status, reported_by, reported_date, required_by_date, description,
                 is_emergency, estimated_cost, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request_number,
                data.get('facility_id'),
                data.get('request_type', 'Corrective'),
                data.get('category'),
                data.get('priority', 'Medium'),
                data.get('severity', 'Medium'),
                'Open',
                user_id,
                data.get('reported_date', datetime.now().strftime('%Y-%m-%d')),
                data.get('required_by_date') or None,
                data.get('description'),
                1 if data.get('is_emergency') else 0,
                data.get('estimated_cost', 0),
                user_id
            ))
            db.commit()
            request_id = cursor.lastrowid

            log_audit('facility_request', request_id, 'CREATE', user_id)

            # Create notification for maintenance team
            create_notification(
                title='New Facility Request',
                message=f'Facility request {request_number} requires attention.',
                notification_type='INFO',
                severity='HIGH' if data.get('priority') == 'Critical' else 'MEDIUM',
                related_entity_type='facility_request',
                related_entity_id=request_id,
                link_url=f'/maintenance/facility-requests/{request_id}'
            )

            flash(f'Request {request_number} created successfully.', 'success')
            return redirect(url_for('maintenance.facility_request_detail', request_id=request_id))

        facilities = db.execute("""
            SELECT mf.id, mf.facility_code, mf.name, mf.facility_type
            FROM maintenance_facilities mf
            WHERE mf.is_active = 1
            ORDER BY mf.name
        """).fetchall()

        return render_template('maintenance/facility_request_form.html',
                             request=None,
                             facilities=facilities,
                             priorities=MAINTENANCE_PRIORITIES,
                             severities=MAINTENANCE_SEVERITIES,
                             request_types=MAINTENANCE_REQUEST_TYPES)
    finally:
        db.close()


@maintenance_bp.route('/facility-requests/<int:request_id>')
@require_login
def facility_request_detail(request_id):
    """Facility Request Detail View."""
    db = get_db()
    try:
        req = db.execute("""
            SELECT mfr.*, mf.name as facility_name, mf.facility_code,
                   u.username as reported_by_name,
                   e.first_name || ' ' || e.last_name as assigned_technician_name
            FROM maintenance_facility_requests mfr
            JOIN maintenance_facilities mf ON mfr.facility_id = mf.id
            LEFT JOIN users u ON mfr.reported_by = u.id
            LEFT JOIN hr_employees e ON mfr.assigned_technician_id = e.id
            WHERE mfr.id = ?
        """, (request_id,)).fetchone()

        if not req:
            flash('Request not found.', 'error')
            return redirect(url_for('maintenance.facility_requests_list'))

        return render_template('maintenance/facility_request_detail.html', request=req)
    finally:
        db.close()


# =============================================================================
# PREVENTIVE MAINTENANCE
# =============================================================================

@maintenance_bp.route('/pm-plans')
@require_login
def pm_plans():
    """Preventive Maintenance Plans List."""
    db = get_db()
    try:
        search = request.args.get('search', '')

        query = """
            SELECT ms.*, a.asset_code, a.name as asset_name,
                   mt.name as maintenance_type,
                   e.first_name || ' ' || e.last_name as technician_name
            FROM maintenance_schedules ms
            JOIN assets a ON ms.asset_id = a.id
            JOIN maintenance_types mt ON ms.maintenance_type_id = mt.id
            LEFT JOIN hr_employees e ON ms.assigned_technician_id = e.id
            WHERE ms.is_active = 1
        """
        params = []

        if search:
            query += " AND (a.asset_code LIKE ? OR a.name LIKE ? OR ms.schedule_name LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])

        query += " ORDER BY ms.next_due_date ASC"

        schedules = db.execute(query, params).fetchall()

        return render_template('maintenance/pm_plans.html',
                             schedules=schedules,
                             search=search)
    finally:
        db.close()


@maintenance_bp.route('/pm-plans/new', methods=['GET', 'POST'])
@require_login
def pm_plan_new():
    """Create New PM Plan."""
    user_id = session.get('user_id')
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.form

            cursor = db.execute("""
                INSERT INTO maintenance_schedules
                (asset_id, maintenance_type_id, schedule_name, frequency,
                 interval_days, next_due_date, priority, assigned_technician_id,
                 estimated_duration_hours, estimated_cost, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('asset_id'),
                data.get('maintenance_type_id'),
                data.get('schedule_name'),
                data.get('frequency', 'Monthly'),
                data.get('interval_days', 30),
                data.get('next_due_date'),
                data.get('priority', 'Medium'),
                data.get('assigned_technician_id') or None,
                data.get('estimated_duration_hours', 0),
                data.get('estimated_cost', 0),
                data.get('notes'),
                user_id
            ))
            db.commit()
            schedule_id = cursor.lastrowid

            log_audit('pm_schedule', schedule_id, 'CREATE', user_id)
            flash('PM Plan created successfully.', 'success')
            return redirect(url_for('maintenance.pm_plans'))

        assets = db.execute("""
            SELECT id, asset_code, name FROM assets
            WHERE status NOT IN ('Disposed', 'Retired')
            ORDER BY asset_code
        """).fetchall()

        maintenance_types = db.execute("""
            SELECT * FROM maintenance_types WHERE is_active = 1
        """).fetchall()

        employees = db.execute("""
            SELECT id, first_name, last_name FROM hr_employees
            WHERE status = 'Active'
            ORDER BY first_name
        """).fetchall()

        return render_template('maintenance/pm_plan_form.html',
                             schedule=None,
                             assets=assets,
                             maintenance_types=maintenance_types,
                             employees=employees,
                             frequencies=MAINTENANCE_FREQUENCIES,
                             priorities=MAINTENANCE_PRIORITIES)
    finally:
        db.close()


@maintenance_bp.route('/pm-schedules')
@require_login
def pm_schedules():
    """PM Schedules Calendar/Due View."""
    db = get_db()
    try:
        view = request.args.get('view', 'list')
        filter_status = request.args.get('filter', 'all')

        query = """
            SELECT ms.*, a.asset_code, a.name as asset_name,
                   mt.name as maintenance_type,
                   e.first_name || ' ' || e.last_name as technician_name
            FROM maintenance_schedules ms
            JOIN assets a ON ms.asset_id = a.id
            JOIN maintenance_types mt ON ms.maintenance_type_id = mt.id
            LEFT JOIN hr_employees e ON ms.assigned_technician_id = e.id
            WHERE ms.is_active = 1
        """
        params = []

        if filter_status == 'overdue':
            query += " AND ms.next_due_date < date('now')"
        elif filter_status == 'due_soon':
            query += " AND ms.next_due_date >= date('now') AND ms.next_due_date <= date('now', '+7 days')"
        elif filter_status == 'due_this_month':
            query += " AND ms.next_due_date >= date('now') AND ms.next_due_date <= date('now', '+30 days')"

        query += " ORDER BY ms.next_due_date ASC"

        schedules = db.execute(query, params).fetchall()

        # Get compliance stats
        compliance = get_pm_compliance_rate()

        return render_template('maintenance/pm_schedules.html',
                             schedules=schedules,
                             view=view,
                             filter_status=filter_status,
                             compliance=compliance)
    finally:
        db.close()


@maintenance_bp.route('/pm-schedules/generate-wo', methods=['POST'])
@require_login
def pm_generate_work_orders():
    """Generate Work Orders for Due PM Schedules."""
    user_id = session.get('user_id')

    try:
        created_ids = generate_pm_work_orders()

        if created_ids:
            log_audit('pm_schedule', 0, 'BULK_WORK_ORDER_CREATE', user_id,
                     notes=f'Generated {len(created_ids)} work orders from PM schedules')
            flash(f'{len(created_ids)} work order(s) generated from PM schedules.', 'success')
        else:
            flash('No PM schedules are currently due for work order generation.', 'info')

        return redirect(url_for('maintenance.work_orders'))
    except Exception as e:
        flash(f'Error generating work orders: {str(e)}', 'error')
        return redirect(url_for('maintenance.pm_schedules'))


# =============================================================================
# CORRECTIVE / BREAKDOWN MAINTENANCE
# =============================================================================

@maintenance_bp.route('/requests')
@maintenance_bp.route('/corrective')
@require_login
def corrective_requests():
    """Corrective Maintenance Requests List."""
    db = get_db()
    try:
        status_filter = request.args.get('status', '')
        priority_filter = request.args.get('priority', '')
        search = request.args.get('search', '')

        query = """
            SELECT mfr.*, a.asset_code, a.name as asset_name,
                   mt.name as maintenance_type,
                   e.first_name || ' ' || e.last_name as technician_name
            FROM maintenance_facility_requests mfr
            LEFT JOIN assets a ON mfr.facility_id = a.id
            LEFT JOIN maintenance_types mt ON mfr.request_type = mt.name
            LEFT JOIN hr_employees e ON mfr.assigned_technician_id = e.id
            WHERE mfr.request_type IN ('Corrective', 'Emergency')
        """
        params = []

        if status_filter:
            query += " AND mfr.status = ?"
            params.append(status_filter)

        if priority_filter:
            query += " AND mfr.priority = ?"
            params.append(priority_filter)

        if search:
            query += " AND (mfr.request_number LIKE ? OR a.name LIKE ? OR mfr.description LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])

        query += " ORDER BY mfr.is_emergency DESC, mfr.priority ASC, mfr.reported_date DESC"

        requests = db.execute(query, params).fetchall()

        return render_template('maintenance/corrective_requests.html',
                             requests=requests,
                             status_filter=status_filter,
                             priority_filter=priority_filter,
                             search=search)
    finally:
        db.close()


# =============================================================================
# WORK ORDERS
# =============================================================================

@maintenance_bp.route('/work-orders')
@require_login
def work_orders():
    """Work Orders List."""
    db = get_db()
    try:
        status_filter = request.args.get('status', '')
        priority_filter = request.args.get('priority', '')
        type_filter = request.args.get('type', '')
        search = request.args.get('search', '')
        assignee = request.args.get('assignee', '')

        query = """
            SELECT mwo.*, a.asset_code, a.name as asset_name,
                   mt.name as maintenance_type,
                   e.first_name || ' ' || e.last_name as technician_name,
                   v.name as vendor_name
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            JOIN maintenance_types mt ON mwo.maintenance_type_id = mt.id
            LEFT JOIN hr_employees e ON mwo.assigned_technician_id = e.id
            LEFT JOIN suppliers v ON mwo.assigned_vendor_id = v.id
            WHERE 1=1
        """
        params = []

        if status_filter:
            query += " AND mwo.status = ?"
            params.append(status_filter)

        if priority_filter:
            query += " AND mwo.priority = ?"
            params.append(priority_filter)

        if type_filter:
            query += " AND mwo.work_order_type = ?"
            params.append(type_filter)

        if search:
            query += " AND (mwo.work_order_number LIKE ? OR a.name LIKE ? OR mwo.issue_description LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])

        if assignee:
            query += " AND mwo.assigned_technician_id = ?"
            params.append(assignee)

        query += " ORDER BY mwo.priority DESC, mwo.issue_date DESC"

        work_orders = db.execute(query, params).fetchall()

        # For dropdowns
        assets = db.execute("SELECT id, asset_code, name FROM assets WHERE status NOT IN ('Disposed', 'Retired') ORDER BY asset_code").fetchall()
        technicians = db.execute("SELECT id, first_name, last_name FROM hr_employees WHERE status = 'Active' ORDER BY first_name").fetchall()
        vendors = db.execute("SELECT id, name FROM suppliers ORDER BY name").fetchall()
        maintenance_types = db.execute("SELECT * FROM maintenance_types WHERE is_active = 1").fetchall()

        return render_template('maintenance/work_orders_list.html',
                             work_orders=work_orders,
                             assets=assets,
                             technicians=technicians,
                             vendors=vendors,
                             maintenance_types=maintenance_types,
                             status_filter=status_filter,
                             priority_filter=priority_filter,
                             type_filter=type_filter,
                             search=search,
                             assignee=assignee,
                             statuses=MAINTENANCE_WORK_ORDER_STATUSES,
                             priorities=MAINTENANCE_PRIORITIES,
                             work_order_types=MAINTENANCE_REQUEST_TYPES)
    finally:
        db.close()


@maintenance_bp.route('/work-orders/new', methods=['GET', 'POST'])
@require_login
def work_order_new():
    """Create New Work Order."""
    user_id = session.get('user_id')
    db = get_db()
    try:
        if request.method == 'POST':
            from asset_models import get_next_work_order_number
            data = request.form

            wo_number = get_next_work_order_number()

            cursor = db.execute("""
                INSERT INTO maintenance_work_orders
                (work_order_number, asset_id, maintenance_type_id, work_order_type,
                 priority, status, issue_date, issue_description,
                 assigned_technician_id, assigned_vendor_id,
                 scheduled_start_date, scheduled_end_date,
                 estimated_cost, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                wo_number,
                data.get('asset_id'),
                data.get('maintenance_type_id'),
                data.get('work_order_type', 'Corrective'),
                data.get('priority', 'Medium'),
                'Open',
                data.get('issue_date', datetime.now().strftime('%Y-%m-%d')),
                data.get('issue_description'),
                data.get('assigned_technician_id') or None,
                data.get('assigned_vendor_id') or None,
                data.get('scheduled_start_date') or None,
                data.get('scheduled_end_date') or None,
                data.get('estimated_cost', 0),
                user_id
            ))
            db.commit()
            wo_id = cursor.lastrowid

            # Update asset status
            db.execute("""
                UPDATE assets SET status = 'Under Maintenance', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (data.get('asset_id'),))

            log_audit('maintenance_work_order', wo_id, 'CREATE', user_id,
                     notes=f'Work order {wo_number} created')

            create_notification(
                title='New Work Order',
                message=f'Work order {wo_number} requires attention.',
                notification_type='INFO',
                severity='HIGH' if data.get('priority') in ('Critical', 'High') else 'MEDIUM',
                related_entity_type='work_order',
                related_entity_id=wo_id,
                link_url=f'/maintenance/work-orders/{wo_id}'
            )

            flash(f'Work order {wo_number} created successfully.', 'success')
            return redirect(url_for('maintenance.work_order_detail', wo_id=wo_id))

        # Get assets
        assets = db.execute("""
            SELECT id, asset_code, name, status FROM assets
            WHERE status NOT IN ('Disposed', 'Retired')
            ORDER BY asset_code
        """).fetchall()

        maintenance_types = db.execute("SELECT * FROM maintenance_types WHERE is_active = 1").fetchall()
        technicians = db.execute("SELECT id, first_name, last_name FROM hr_employees WHERE status = 'Active' ORDER BY first_name").fetchall()
        vendors = db.execute("SELECT id, name FROM suppliers ORDER BY name").fetchall()
        teams = db.execute("SELECT id, team_name FROM maintenance_teams WHERE is_active = 1").fetchall()
        checklists = db.execute("SELECT id, template_name FROM maintenance_checklist_templates WHERE is_active = 1").fetchall()

        return render_template('maintenance/work_order_form.html',
                             work_order=None,
                             assets=assets,
                             maintenance_types=maintenance_types,
                             technicians=technicians,
                             vendors=vendors,
                             teams=teams,
                             checklists=checklists,
                             statuses=MAINTENANCE_WORK_ORDER_STATUSES,
                             priorities=MAINTENANCE_PRIORITIES,
                             work_order_types=MAINTENANCE_REQUEST_TYPES)
    finally:
        db.close()


@maintenance_bp.route('/work-orders/<int:wo_id>')
@require_login
def work_order_detail(wo_id):
    """Work Order Detail View."""
    db = get_db()
    try:
        wo = db.execute("""
            SELECT mwo.*, a.asset_code, a.name as asset_name, a.serial_number, a.location as asset_location,
                   mt.name as maintenance_type,
                   e.first_name || ' ' || e.last_name as technician_name,
                   v.name as vendor_name,
                   u.username as created_by_name,
                   c.username as completed_by_name
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            JOIN maintenance_types mt ON mwo.maintenance_type_id = mt.id
            LEFT JOIN hr_employees e ON mwo.assigned_technician_id = e.id
            LEFT JOIN suppliers v ON mwo.assigned_vendor_id = v.id
            LEFT JOIN users u ON mwo.created_by = u.id
            LEFT JOIN users c ON mwo.completed_by = c.id
            WHERE mwo.id = ?
        """, (wo_id,)).fetchone()

        if not wo:
            flash('Work order not found.', 'error')
            return redirect(url_for('maintenance.work_orders'))

        # Get work logs
        logs = db.execute("""
            SELECT mwl.*, e.first_name || ' ' || e.last_name as technician_name
            FROM maintenance_work_logs mwl
            LEFT JOIN hr_employees e ON mwl.technician_id = e.id
            WHERE mwl.work_order_id = ?
            ORDER BY mwl.work_date DESC
        """, (wo_id,)).fetchall()

        # Get tasks
        tasks = db.execute("""
            SELECT mwot.*, e.first_name || ' ' || e.last_name as assigned_name
            FROM maintenance_work_order_tasks mwot
            LEFT JOIN hr_employees e ON mwot.assigned_technician_id = e.id
            WHERE mwot.work_order_id = ?
            ORDER BY mwot.task_sequence
        """, (wo_id,)).fetchall()

        # Get parts usage
        parts = db.execute("""
            SELECT mpu.*
            FROM maintenance_parts_usage mpu
            WHERE mpu.work_order_id = ?
            ORDER BY mpu.issue_date DESC
        """, (wo_id,)).fetchall()

        # Get labor logs
        labor_logs = db.execute("""
            SELECT mll.*, e.first_name || ' ' || e.last_name as technician_name
            FROM maintenance_labor_logs mll
            JOIN hr_employees e ON mll.technician_id = e.id
            WHERE mll.work_order_id = ?
            ORDER BY mll.work_date DESC
        """, (wo_id,)).fetchall()

        # Get downtime logs
        downtime = db.execute("""
            SELECT *
            FROM maintenance_downtime_logs
            WHERE work_order_id = ?
            ORDER BY downtime_start DESC
        """, (wo_id,)).fetchall()

        # Get checklist results
        checklist_results = db.execute("""
            SELECT mcr.*, e.first_name || ' ' || e.last_name as inspector_name
            FROM maintenance_checklist_results mcr
            LEFT JOIN hr_employees e ON mcr.inspector_id = e.id
            WHERE mcr.work_order_id = ?
            ORDER BY mcr.inspection_date DESC
        """, (wo_id,)).fetchall()

        technicians = db.execute("SELECT id, first_name, last_name FROM hr_employees WHERE status = 'Active' ORDER BY first_name").fetchall()

        return render_template('maintenance/work_order_detail.html',
                             wo=wo,
                             logs=logs,
                             tasks=tasks,
                             parts=parts,
                             labor_logs=labor_logs,
                             downtime=downtime,
                             checklist_results=checklist_results,
                             technicians=technicians)
    finally:
        db.close()


@maintenance_bp.route('/work-orders/<int:wo_id>/edit', methods=['GET', 'POST'])
@require_login
def work_order_edit(wo_id):
    """Edit Work Order."""
    user_id = session.get('user_id')
    db = get_db()
    try:
        wo = db.execute("SELECT * FROM maintenance_work_orders WHERE id = ?", (wo_id,)).fetchone()
        if not wo:
            flash('Work order not found.', 'error')
            return redirect(url_for('maintenance.work_orders'))

        if request.method == 'POST':
            data = request.form

            db.execute("""
                UPDATE maintenance_work_orders SET
                    priority = ?, status = ?,
                    assigned_technician_id = ?, assigned_vendor_id = ?,
                    scheduled_start_date = ?, scheduled_end_date = ?,
                    issue_description = ?,
                    estimated_cost = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                data.get('priority'),
                data.get('status'),
                data.get('assigned_technician_id') or None,
                data.get('assigned_vendor_id') or None,
                data.get('scheduled_start_date') or None,
                data.get('scheduled_end_date') or None,
                data.get('issue_description'),
                data.get('estimated_cost', 0),
                wo_id
            ))
            db.commit()

            log_audit('maintenance_work_order', wo_id, 'UPDATE', user_id)
            flash('Work order updated successfully.', 'success')
            return redirect(url_for('maintenance.work_order_detail', wo_id=wo_id))

        assets = db.execute("SELECT id, asset_code, name FROM assets WHERE status NOT IN ('Disposed', 'Retired') ORDER BY asset_code").fetchall()
        maintenance_types = db.execute("SELECT * FROM maintenance_types WHERE is_active = 1").fetchall()
        technicians = db.execute("SELECT id, first_name, last_name FROM hr_employees WHERE status = 'Active' ORDER BY first_name").fetchall()
        vendors = db.execute("SELECT id, name FROM suppliers ORDER BY name").fetchall()
        teams = db.execute("SELECT id, team_name FROM maintenance_teams WHERE is_active = 1").fetchall()

        return render_template('maintenance/work_order_form.html',
                             work_order=wo,
                             assets=assets,
                             maintenance_types=maintenance_types,
                             technicians=technicians,
                             vendors=vendors,
                             teams=teams,
                             statuses=MAINTENANCE_WORK_ORDER_STATUSES,
                             priorities=MAINTENANCE_PRIORITIES,
                             work_order_types=MAINTENANCE_REQUEST_TYPES)
    finally:
        db.close()


@maintenance_bp.route('/work-orders/<int:wo_id>/complete', methods=['POST'])
@require_login
def work_order_complete(wo_id):
    """Complete a Work Order."""
    user_id = session.get('user_id')
    db = get_db()
    try:
        wo = db.execute("SELECT * FROM maintenance_work_orders WHERE id = ?", (wo_id,)).fetchone()
        if not wo:
            return jsonify({'error': 'Work order not found'}), 404

        data = request.get_json() if request.is_json else request.form

        actual_cost = float(data.get('actual_cost', wo['estimated_cost'] or 0))
        resolution = data.get('resolution_notes', '')
        downtime = float(data.get('downtime_hours', 0))

        # Update work order
        db.execute("""
            UPDATE maintenance_work_orders SET
                status = 'Completed',
                actual_end_date = CURRENT_TIMESTAMP,
                actual_cost = ?,
                downtime_hours = COALESCE(downtime_hours, 0) + ?,
                resolution_notes = ?,
                completed_by = ?,
                completed_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (actual_cost, downtime, resolution, user_id, wo_id))

        # Create work log
        db.execute("""
            INSERT INTO maintenance_work_logs
            (work_order_id, asset_id, maintenance_type_id, work_date,
             technician_id, work_performed, action_taken,
             total_cost, downtime_hours, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            wo_id,
            wo['asset_id'],
            wo['maintenance_type_id'],
            datetime.now().strftime('%Y-%m-%d'),
            wo['assigned_technician_id'],
            resolution,
            resolution,
            actual_cost,
            downtime,
            'Work order completed',
            user_id
        ))

        # Create cost entry
        if actual_cost > 0:
            db.execute("""
                INSERT INTO maintenance_cost_entries
                (asset_id, work_order_id, cost_type, cost_date, description, amount, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                wo['asset_id'],
                wo_id,
                'Maintenance',
                datetime.now().strftime('%Y-%m-%d'),
                f'Work order {wo["work_order_number"]} completion',
                actual_cost,
                user_id
            ))

        # Update asset status
        db.execute("""
            UPDATE assets SET status = 'Active', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (wo['asset_id'],))

        # Update PM schedule if linked
        if wo['schedule_id']:
            schedule = db.execute("SELECT * FROM maintenance_schedules WHERE id = ?",
                                 (wo['schedule_id'],)).fetchone()
            if schedule:
                next_date = datetime.strptime(schedule['next_due_date'], '%Y-%m-%d')
                freq = schedule['frequency']
                interval = schedule['interval_days']

                if freq == 'Daily':
                    next_date += timedelta(days=1)
                elif freq == 'Weekly':
                    next_date += timedelta(weeks=1)
                elif freq == 'Bi-Weekly':
                    next_date += timedelta(weeks=2)
                elif freq == 'Monthly':
                    next_date += timedelta(days=30)
                elif freq == 'Quarterly':
                    next_date += timedelta(days=90)
                elif freq == 'Semi-Annual':
                    next_date += timedelta(days=180)
                elif freq == 'Annual':
                    next_date += timedelta(days=365)
                else:
                    next_date += timedelta(days=interval)

                db.execute("""
                    UPDATE maintenance_schedules SET
                        last_performed_date = ?,
                        last_work_order_id = ?,
                        next_due_date = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (datetime.now().strftime('%Y-%m-%d'), wo_id,
                      next_date.strftime('%Y-%m-%d'), wo['schedule_id']))

        db.commit()

        log_audit('maintenance_work_order', wo_id, 'COMPLETE', user_id,
                  notes=f'Work order {wo["work_order_number"]} completed')
        flash('Work order completed successfully.', 'success')

        if request.is_json:
            return jsonify({'success': True})
        return redirect(url_for('maintenance.work_order_detail', wo_id=wo_id))

    except Exception as e:
        db.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f'Error completing work order: {str(e)}', 'error')
        return redirect(url_for('maintenance.work_order_detail', wo_id=wo_id))
    finally:
        db.close()


@maintenance_bp.route('/work-orders/<int:wo_id>/status', methods=['POST'])
@require_login
def work_order_update_status(wo_id):
    """Update Work Order Status."""
    user_id = session.get('user_id')
    db = get_db()
    try:
        data = request.get_json()
        new_status = data.get('status')

        if new_status not in MAINTENANCE_WORK_ORDER_STATUSES:
            return jsonify({'error': 'Invalid status'}), 400

        db.execute("""
            UPDATE maintenance_work_orders SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_status, wo_id))
        db.commit()

        wo = db.execute("SELECT work_order_number FROM maintenance_work_orders WHERE id = ?", (wo_id,)).fetchone()
        log_audit('maintenance_work_order', wo_id, 'STATUS_CHANGE', user_id,
                 notes=f'Status changed to {new_status}')

        flash(f'Work order status updated to {new_status}.', 'success')
        return jsonify({'success': True})

    finally:
        db.close()


@maintenance_bp.route('/work-orders/<int:wo_id>/tasks/add', methods=['POST'])
@require_login
def work_order_add_task(wo_id):
    """Add Task to Work Order."""
    user_id = session.get('user_id')
    db = get_db()
    try:
        data = request.get_json()

        cursor = db.execute("""
            INSERT INTO maintenance_work_order_tasks
            (work_order_id, task_description, task_type, assigned_technician_id,
             estimated_hours, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            wo_id,
            data.get('task_description'),
            data.get('task_type', 'Maintenance'),
            data.get('assigned_technician_id') or None,
            data.get('estimated_hours', 0),
            data.get('notes')
        ))
        db.commit()

        log_audit('work_order_task', cursor.lastrowid, 'CREATE', user_id)
        return jsonify({'success': True, 'task_id': cursor.lastrowid})

    finally:
        db.close()


@maintenance_bp.route('/work-orders/<int:wo_id>/tasks/<int:task_id>/complete', methods=['POST'])
@require_login
def work_order_task_complete(wo_id, task_id):
    """Complete a Work Order Task."""
    user_id = session.get('user_id')
    db = get_db()
    try:
        data = request.get_json()

        db.execute("""
            UPDATE maintenance_work_order_tasks SET
                status = 'Completed',
                is_completed = 1,
                completed_by = ?,
                completed_at = CURRENT_TIMESTAMP,
                actual_hours = ?,
                notes = COALESCE(notes, '') || ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            user_id,
            data.get('actual_hours', 0),
            f" - {data.get('completion_notes', '')}",
            task_id
        ))
        db.commit()

        return jsonify({'success': True})

    finally:
        db.close()


# =============================================================================
# SPARE PARTS / MATERIAL USAGE
# =============================================================================

@maintenance_bp.route('/parts-usage')
@require_login
def parts_usage():
    """Spare Parts/Material Usage List."""
    db = get_db()
    try:
        search = request.args.get('search', '')
        status_filter = request.args.get('status', '')

        query = """
            SELECT mpu.*, mwo.work_order_number,
                   a.asset_code || ' - ' || a.name as asset_name
            FROM maintenance_parts_usage mpu
            LEFT JOIN maintenance_work_orders mwo ON mpu.work_order_id = mwo.id
            LEFT JOIN assets a ON mwo.asset_id = a.id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (mpu.part_name LIKE ? OR mpu.part_number LIKE ? OR mwo.work_order_number LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])

        if status_filter:
            query += " AND mpu.status = ?"
            params.append(status_filter)

        query += " ORDER BY mpu.issue_date DESC"

        parts = db.execute(query, params).fetchall()

        return render_template('maintenance/parts_usage_list.html',
                             parts=parts,
                             search=search,
                             status_filter=status_filter)
    finally:
        db.close()


@maintenance_bp.route('/parts-usage/new', methods=['GET', 'POST'])
@require_login
def parts_usage_new():
    """Add New Parts Usage Entry."""
    user_id = session.get('user_id')
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.form
            usage_number = get_next_parts_usage_number()

            cursor = db.execute("""
                INSERT INTO maintenance_parts_usage
                (usage_number, work_order_id, part_id, part_number, part_name,
                 quantity_requested, quantity_issued, unit_of_measure,
                 warehouse_id, issue_date, unit_cost, total_cost, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                usage_number,
                data.get('work_order_id') or None,
                data.get('part_id') or None,
                data.get('part_number'),
                data.get('part_name'),
                data.get('quantity_requested', 1),
                data.get('quantity_issued', 1),
                data.get('unit_of_measure', 'Unit'),
                data.get('warehouse_id') or None,
                data.get('issue_date', datetime.now().strftime('%Y-%m-%d')),
                data.get('unit_cost', 0),
                data.get('quantity_issued', 1) * float(data.get('unit_cost', 0)),
                data.get('notes'),
                user_id
            ))
            db.commit()

            log_audit('parts_usage', cursor.lastrowid, 'CREATE', user_id)
            flash(f'Parts usage {usage_number} recorded successfully.', 'success')
            return redirect(url_for('maintenance.parts_usage'))

        work_orders = db.execute("""
            SELECT mwo.id, mwo.work_order_number, a.name as asset_name
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            WHERE mwo.status NOT IN ('Completed', 'Closed', 'Canceled')
            ORDER BY mwo.work_order_number DESC
        """).fetchall()

        return render_template('maintenance/parts_usage_form.html',
                             usage=None,
                             work_orders=work_orders)
    finally:
        db.close()


# =============================================================================
# LABOR / TIME LOGGING
# =============================================================================

@maintenance_bp.route('/labor-logs')
@require_login
def labor_logs():
    """Labor/Time Logs List."""
    db = get_db()
    try:
        search = request.args.get('search', '')
        technician = request.args.get('technician', '')

        query = """
            SELECT mll.*, mwo.work_order_number, a.name as asset_name,
                   e.first_name || ' ' || e.last_name as technician_name
            FROM maintenance_labor_logs mll
            JOIN maintenance_work_orders mwo ON mll.work_order_id = mwo.id
            JOIN assets a ON mwo.asset_id = a.id
            JOIN hr_employees e ON mll.technician_id = e.id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (mwo.work_order_number LIKE ? OR a.name LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])

        if technician:
            query += " AND mll.technician_id = ?"
            params.append(technician)

        query += " ORDER BY mll.work_date DESC"

        logs = db.execute(query, params).fetchall()

        technicians = db.execute("""
            SELECT id, first_name, last_name FROM hr_employees
            WHERE status = 'Active'
            ORDER BY first_name
        """).fetchall()

        return render_template('maintenance/labor_logs_list.html',
                             logs=logs,
                             search=search,
                             technician=technician,
                             technicians=technicians)
    finally:
        db.close()


@maintenance_bp.route('/labor-logs/new', methods=['GET', 'POST'])
@require_login
def labor_log_new():
    """Add New Labor/Time Log Entry."""
    user_id = session.get('user_id')
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.form
            log_number = get_next_labor_log_number()

            total_hours = float(data.get('total_hours', 0))
            hourly_rate = float(data.get('hourly_rate', 0))
            labor_cost = total_hours * hourly_rate

            cursor = db.execute("""
                INSERT INTO maintenance_labor_logs
                (log_number, work_order_id, technician_id, work_date,
                 start_time, end_time, total_hours, regular_hours, overtime_hours,
                 hourly_rate, labor_cost, work_description, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_number,
                data.get('work_order_id'),
                data.get('technician_id'),
                data.get('work_date', datetime.now().strftime('%Y-%m-%d')),
                data.get('start_time'),
                data.get('end_time'),
                total_hours,
                data.get('regular_hours', total_hours),
                data.get('overtime_hours', 0),
                hourly_rate,
                labor_cost,
                data.get('work_description'),
                data.get('notes'),
                user_id
            ))
            db.commit()
            log_id = cursor.lastrowid

            # Update work order actual hours if linked
            if data.get('work_order_id'):
                db.execute("""
                    UPDATE maintenance_work_orders SET
                        actual_cost = actual_cost + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (labor_cost, data.get('work_order_id')))

                # Also create cost entry
                wo = db.execute("SELECT asset_id FROM maintenance_work_orders WHERE id = ?",
                               (data.get('work_order_id'),)).fetchone()
                if wo:
                    db.execute("""
                        INSERT INTO maintenance_cost_entries
                        (asset_id, work_order_id, cost_type, cost_date, description, amount, created_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        wo['asset_id'],
                        data.get('work_order_id'),
                        'Labor',
                        data.get('work_date', datetime.now().strftime('%Y-%m-%d')),
                        f'Labor: {data.get("work_description", "Work performed")}',
                        labor_cost,
                        user_id
                    ))
                db.commit()

            log_audit('labor_log', log_id, 'CREATE', user_id)
            flash(f'Labor log {log_number} recorded successfully.', 'success')
            return redirect(url_for('maintenance.labor_logs'))

        work_orders = db.execute("""
            SELECT mwo.id, mwo.work_order_number, a.name as asset_name
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            WHERE mwo.status NOT IN ('Closed', 'Canceled')
            ORDER BY mwo.work_order_number DESC
        """).fetchall()

        technicians = db.execute("""
            SELECT id, first_name, last_name, employee_code FROM hr_employees
            WHERE status = 'Active'
            ORDER BY first_name
        """).fetchall()

        return render_template('maintenance/labor_log_form.html',
                             log=None,
                             work_orders=work_orders,
                             technicians=technicians)
    finally:
        db.close()


# =============================================================================
# DOWNTIME TRACKING
# =============================================================================

@maintenance_bp.route('/downtime')
@require_login
def downtime_list():
    """Downtime Logs List."""
    db = get_db()
    try:
        search = request.args.get('search', '')
        impact_filter = request.args.get('impact', '')

        query = """
            SELECT mdl.*, a.asset_code, a.name as asset_name, mwo.work_order_number,
                   e.first_name || ' ' || e.last_name as resolved_by_name
            FROM maintenance_downtime_logs mdl
            LEFT JOIN assets a ON mdl.asset_id = a.id
            LEFT JOIN maintenance_work_orders mwo ON mdl.work_order_id = mwo.id
            LEFT JOIN hr_employees e ON mdl.resolved_by = e.id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (a.asset_code LIKE ? OR a.name LIKE ? OR mdl.log_number LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])

        if impact_filter:
            query += " AND mdl.impact_level = ?"
            params.append(impact_filter)

        query += " ORDER BY mdl.downtime_start DESC"

        logs = db.execute(query, params).fetchall()

        # Summary stats
        summary = db.execute("""
            SELECT
                SUM(total_hours) as total_downtime,
                COUNT(*) as incident_count,
                SUM(CASE WHEN planned_downtime = 0 THEN total_hours ELSE 0 END) as unplanned,
                SUM(CASE WHEN planned_downtime = 1 THEN total_hours ELSE 0 END) as planned
            FROM maintenance_downtime_logs
        """).fetchone()

        return render_template('maintenance/downtime_list.html',
                             logs=logs,
                             search=search,
                             impact_filter=impact_filter,
                             summary=summary,
                             impact_levels=DOWNTIME_IMPACT_LEVELS)
    finally:
        db.close()


@maintenance_bp.route('/downtime/new', methods=['GET', 'POST'])
@require_login
def downtime_new():
    """Add New Downtime Log Entry."""
    user_id = session.get('user_id')
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.form
            log_number = get_next_downtime_log_number()

            start_dt = data.get('downtime_start')
            end_dt = data.get('downtime_end')
            total_hours = 0

            if start_dt and end_dt:
                start = datetime.strptime(start_dt, '%Y-%m-%dT%H:%M')
                end = datetime.strptime(end_dt, '%Y-%m-%dT%H:%M')
                total_hours = (end - start).total_seconds() / 3600

            cursor = db.execute("""
                INSERT INTO maintenance_downtime_logs
                (log_number, asset_id, work_order_id, downtime_reason,
                 downtime_start, downtime_end, planned_downtime, total_hours,
                 impact_level, root_cause, corrective_action, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_number,
                data.get('asset_id') or None,
                data.get('work_order_id') or None,
                data.get('downtime_reason'),
                start_dt,
                end_dt,
                1 if data.get('planned_downtime') else 0,
                total_hours,
                data.get('impact_level', 'Medium'),
                data.get('root_cause'),
                data.get('corrective_action'),
                data.get('notes'),
                user_id
            ))
            db.commit()
            log_id = cursor.lastrowid

            # Update work order downtime if linked
            if data.get('work_order_id') and total_hours > 0:
                db.execute("""
                    UPDATE maintenance_work_orders SET
                        downtime_hours = COALESCE(downtime_hours, 0) + ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (total_hours, data.get('work_order_id')))
                db.commit()

            log_audit('downtime_log', log_id, 'CREATE', user_id)
            flash(f'Downtime log {log_number} recorded successfully.', 'success')
            return redirect(url_for('maintenance.downtime_list'))

        assets = db.execute("""
            SELECT id, asset_code, name FROM assets
            WHERE status NOT IN ('Disposed', 'Retired')
            ORDER BY asset_code
        """).fetchall()

        work_orders = db.execute("""
            SELECT id, work_order_number FROM maintenance_work_orders
            WHERE status NOT IN ('Closed', 'Canceled')
            ORDER BY work_order_number DESC
        """).fetchall()

        return render_template('maintenance/downtime_form.html',
                             log=None,
                             assets=assets,
                             work_orders=work_orders,
                             impact_levels=DOWNTIME_IMPACT_LEVELS)
    finally:
        db.close()


# =============================================================================
# INSPECTIONS / CHECKLISTS
# =============================================================================

@maintenance_bp.route('/inspections')
@require_login
def inspections_list():
    """Inspection/Checklist Results List."""
    db = get_db()
    try:
        search = request.args.get('search', '')

        query = """
            SELECT mcr.*, mwo.work_order_number, a.name as asset_name,
                   e.first_name || ' ' || e.last_name as inspector_name,
                   mct.template_name
            FROM maintenance_checklist_results mcr
            LEFT JOIN maintenance_work_orders mwo ON mcr.work_order_id = mwo.id
            LEFT JOIN assets a ON mcr.asset_id = a.id
            LEFT JOIN hr_employees e ON mcr.inspector_id = e.id
            LEFT JOIN maintenance_checklist_templates mct ON mcr.checklist_template_id = mct.id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (mwo.work_order_number LIKE ? OR a.name LIKE ?)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term])

        query += " ORDER BY mcr.inspection_date DESC"

        results = db.execute(query, params).fetchall()

        return render_template('maintenance/inspections_list.html',
                             results=results,
                             search=search)
    finally:
        db.close()


@maintenance_bp.route('/checklist-templates')
@require_login
def checklist_templates():
    """Checklist Templates List."""
    db = get_db()
    try:
        templates = db.execute("""
            SELECT mct.*,
                   (SELECT COUNT(*) FROM maintenance_checklist_items mci WHERE mci.template_id = mct.id) as item_count
            FROM maintenance_checklist_templates mct
            WHERE mct.is_active = 1
            ORDER BY mct.template_name
        """).fetchall()

        return render_template('maintenance/checklist_templates.html',
                             templates=templates)
    finally:
        db.close()


# =============================================================================
# TECHNICIANS & TEAMS
# =============================================================================

@maintenance_bp.route('/technicians')
@require_login
def technicians_list():
    """Technicians and Teams List."""
    db = get_db()
    try:
        teams = db.execute("""
            SELECT mt.*,
                   e.first_name || ' ' || e.last_name as team_lead_name,
                   (SELECT COUNT(*) FROM maintenance_team_members mtm WHERE mtm.team_id = mt.id AND mtm.is_active = 1) as member_count
            FROM maintenance_teams mt
            LEFT JOIN hr_employees e ON mt.team_lead_id = e.id
            WHERE mt.is_active = 1
            ORDER BY mt.team_name
        """).fetchall()

        # Get all technicians with workload
        tech_workload = get_technician_workload()

        return render_template('maintenance/technicians_list.html',
                             teams=teams,
                             tech_workload=tech_workload)
    finally:
        db.close()


@maintenance_bp.route('/technicians/new', methods=['GET', 'POST'])
@require_login
def team_new():
    """Create New Maintenance Team."""
    user_id = session.get('user_id')
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.form
            team_code = get_next_team_code()

            cursor = db.execute("""
                INSERT INTO maintenance_teams
                (team_code, team_name, description, team_lead_id,
                 department_id, skill_specializations, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                team_code,
                data.get('team_name'),
                data.get('description'),
                data.get('team_lead_id') or None,
                data.get('department_id') or None,
                data.get('skill_specializations'),
                data.get('notes'),
                user_id
            ))
            db.commit()
            team_id = cursor.lastrowid

            log_audit('maintenance_team', team_id, 'CREATE', user_id)
            flash(f'Team {team_code} created successfully.', 'success')
            return redirect(url_for('maintenance.technicians_list'))

        employees = db.execute("""
            SELECT id, first_name, last_name, employee_code FROM hr_employees
            WHERE status = 'Active'
            ORDER BY first_name
        """).fetchall()

        departments = db.execute("SELECT id, name FROM hr_departments ORDER BY name").fetchall()

        return render_template('maintenance/team_form.html',
                             team=None,
                             employees=employees,
                             departments=departments)
    finally:
        db.close()


# =============================================================================
# REPORTS
# =============================================================================

@maintenance_bp.route('/reports')
@require_login
def reports():
    """Maintenance Reports Hub."""
    return render_template('maintenance/reports.html')


@maintenance_bp.route('/reports/work-orders')
@require_login
def report_work_orders():
    """Work Order Report."""
    db = get_db()
    try:
        status_filter = request.args.get('status', '')
        priority_filter = request.args.get('priority', '')
        type_filter = request.args.get('type', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')

        query = """
            SELECT mwo.*, a.asset_code, a.name as asset_name,
                   mt.name as maintenance_type,
                   e.first_name || ' ' || e.last_name as technician_name
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            JOIN maintenance_types mt ON mwo.maintenance_type_id = mt.id
            LEFT JOIN hr_employees e ON mwo.assigned_technician_id = e.id
            WHERE 1=1
        """
        params = []

        if status_filter:
            query += " AND mwo.status = ?"
            params.append(status_filter)

        if priority_filter:
            query += " AND mwo.priority = ?"
            params.append(priority_filter)

        if type_filter:
            query += " AND mwo.work_order_type = ?"
            params.append(type_filter)

        if date_from:
            query += " AND mwo.issue_date >= ?"
            params.append(date_from)

        if date_to:
            query += " AND mwo.issue_date <= ?"
            params.append(date_to)

        query += " ORDER BY mwo.issue_date DESC"

        work_orders = db.execute(query, params).fetchall()

        # Summary stats
        summary = db.execute(f"""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed,
                SUM(actual_cost) as total_cost,
                SUM(downtime_hours) as total_downtime,
                AVG(actual_cost) as avg_cost
            FROM maintenance_work_orders
            WHERE 1=1
            {"AND status = ?" if status_filter else ""}
            {"AND priority = ?" if priority_filter else ""}
            {"AND work_order_type = ?" if type_filter else ""}
        """, [p for p in params if p]).fetchone() if not any([date_from, date_to]) else None

        return render_template('maintenance/report_work_orders.html',
                             work_orders=work_orders,
                             summary=summary,
                             status_filter=status_filter,
                             priority_filter=priority_filter,
                             type_filter=type_filter,
                             date_from=date_from,
                             date_to=date_to,
                             statuses=MAINTENANCE_WORK_ORDER_STATUSES,
                             priorities=MAINTENANCE_PRIORITIES,
                             work_order_types=MAINTENANCE_REQUEST_TYPES)
    finally:
        db.close()


@maintenance_bp.route('/reports/pm-compliance')
@require_login
def report_pm_compliance():
    """PM Compliance Report."""
    db = get_db()
    try:
        compliance = get_pm_compliance_rate()

        # Get overdue by priority
        overdue_by_priority = db.execute("""
            SELECT
                ms.priority,
                COUNT(*) as count
            FROM maintenance_schedules ms
            WHERE ms.is_active = 1
            AND ms.next_due_date < date('now')
            GROUP BY ms.priority
        """).fetchall()

        # Get due soon
        due_by_month = db.execute("""
            SELECT
                strftime('%Y-%m', ms.next_due_date) as month,
                COUNT(*) as count
            FROM maintenance_schedules ms
            WHERE ms.is_active = 1
            AND ms.next_due_date >= date('now')
            AND ms.next_due_date <= date('now', '+90 days')
            GROUP BY strftime('%Y-%m', ms.next_due_date)
            ORDER BY month
        """).fetchall()

        return render_template('maintenance/report_pm_compliance.html',
                             compliance=compliance,
                             overdue_by_priority=overdue_by_priority,
                             due_by_month=due_by_month)
    finally:
        db.close()


@maintenance_bp.route('/reports/costs')
@require_login
def report_costs():
    """Maintenance Cost Report."""
    db = get_db()
    try:
        date_from = request.args.get('date_from', (datetime.now().replace(day=1)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        # Cost by month
        by_month = db.execute("""
            SELECT
                strftime('%Y-%m', mce.cost_date) as month,
                SUM(mce.amount) as total
            FROM maintenance_cost_entries mce
            WHERE mce.cost_date BETWEEN ? AND ?
            GROUP BY strftime('%Y-%m', mce.cost_date)
            ORDER BY month DESC
        """, (date_from, date_to)).fetchall()

        # Cost by type
        by_type = db.execute("""
            SELECT
                mce.cost_type,
                SUM(mce.amount) as total
            FROM maintenance_cost_entries mce
            WHERE mce.cost_date BETWEEN ? AND ?
            GROUP BY mce.cost_type
            ORDER BY total DESC
        """, (date_from, date_to)).fetchall()

        # Cost by asset
        by_asset = db.execute("""
            SELECT
                a.asset_code,
                a.name,
                SUM(mce.amount) as total
            FROM maintenance_cost_entries mce
            JOIN assets a ON mce.asset_id = a.id
            WHERE mce.cost_date BETWEEN ? AND ?
            GROUP BY a.id
            ORDER BY total DESC
            LIMIT 20
        """, (date_from, date_to)).fetchall()

        # Total
        total = db.execute("""
            SELECT SUM(amount) as total FROM maintenance_cost_entries
            WHERE cost_date BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()

        return render_template('maintenance/report_costs.html',
                             by_month=by_month,
                             by_type=by_type,
                             by_asset=by_asset,
                             total=total,
                             date_from=date_from,
                             date_to=date_to)
    finally:
        db.close()


@maintenance_bp.route('/reports/downtime')
@require_login
def report_downtime():
    """Downtime Report."""
    db = get_db()
    try:
        date_from = request.args.get('date_from', (datetime.now().replace(day=1)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        # Downtime by asset
        by_asset = db.execute("""
            SELECT
                a.asset_code,
                a.name,
                SUM(mdl.total_hours) as total_hours,
                COUNT(*) as incident_count
            FROM maintenance_downtime_logs mdl
            JOIN assets a ON mdl.asset_id = a.id
            WHERE date(mdl.downtime_start) BETWEEN ? AND ?
            GROUP BY a.id
            ORDER BY total_hours DESC
        """, (date_from, date_to)).fetchall()

        # Downtime by reason
        by_reason = db.execute("""
            SELECT
                mdl.downtime_reason,
                SUM(mdl.total_hours) as total_hours,
                COUNT(*) as count
            FROM maintenance_downtime_logs mdl
            WHERE date(mdl.downtime_start) BETWEEN ? AND ?
            GROUP BY mdl.downtime_reason
            ORDER BY total_hours DESC
        """, (date_from, date_to)).fetchall()

        # Summary
        summary = db.execute("""
            SELECT
                SUM(total_hours) as total_hours,
                COUNT(*) as incident_count,
                AVG(total_hours) as avg_hours,
                SUM(CASE WHEN planned_downtime = 0 THEN total_hours ELSE 0 END) as unplanned
            FROM maintenance_downtime_logs
            WHERE date(downtime_start) BETWEEN ? AND ?
        """, (date_from, date_to)).fetchone()

        return render_template('maintenance/report_downtime.html',
                             by_asset=by_asset,
                             by_reason=by_reason,
                             summary=summary,
                             date_from=date_from,
                             date_to=date_to)
    finally:
        db.close()


@maintenance_bp.route('/reports/technician-performance')
@require_login
def report_technician_performance():
    """Technician Performance Report."""
    db = get_db()
    try:
        date_from = request.args.get('date_from', (datetime.now().replace(day=1)).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        performance = db.execute("""
            SELECT
                e.id,
                e.first_name || ' ' || e.last_name as technician_name,
                e.employee_code,
                COUNT(mwo.id) as work_orders_completed,
                SUM(CASE WHEN mwo.status = 'Completed' THEN 1 ELSE 0 END) as completed,
                SUM(mwo.actual_cost) as total_cost,
                SUM(mwo.downtime_hours) as total_downtime,
                AVG(mwo.actual_cost) as avg_cost_per_wo
            FROM hr_employees e
            LEFT JOIN maintenance_work_orders mwo ON e.id = mwo.assigned_technician_id
                AND mwo.status = 'Completed'
                AND date(mwo.completed_at) BETWEEN ? AND ?
            WHERE e.status = 'Active'
            GROUP BY e.id
            ORDER BY completed DESC
        """, (date_from, date_to)).fetchall()

        return render_template('maintenance/report_technician_performance.html',
                             performance=performance,
                             date_from=date_from,
                             date_to=date_to)
    finally:
        db.close()


@maintenance_bp.route('/reports/asset-history/<int:asset_id>')
@require_login
def report_asset_history(asset_id):
    """Asset Maintenance History Report."""
    db = get_db()
    try:
        asset = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not asset:
            flash('Asset not found.', 'error')
            return redirect(url_for('maintenance.reports'))

        history = db.execute("""
            SELECT mwo.*, mt.name as maintenance_type
            FROM maintenance_work_orders mwo
            JOIN maintenance_types mt ON mwo.maintenance_type_id = mt.id
            WHERE mwo.asset_id = ?
            ORDER BY mwo.issue_date DESC
        """, (asset_id,)).fetchall()

        cost_summary = db.execute("""
            SELECT
                SUM(actual_cost) as total_cost,
                AVG(actual_cost) as avg_cost,
                SUM(downtime_hours) as total_downtime,
                COUNT(*) as total_orders
            FROM maintenance_work_orders
            WHERE asset_id = ?
        """, (asset_id,)).fetchone()

        return render_template('maintenance/report_asset_history.html',
                             asset=asset,
                             history=history,
                             cost_summary=cost_summary)
    finally:
        db.close()


# =============================================================================
# SETTINGS
# =============================================================================

@maintenance_bp.route('/settings')
@maintenance_bp.route('/settings/maintenance')
@require_login
def settings():
    """Maintenance Settings."""
    db = get_db()
    try:
        # Get maintenance types
        maint_types = db.execute("SELECT * FROM maintenance_types ORDER BY name").fetchall()

        # Get SLA rules
        sla_rules = db.execute("SELECT * FROM maintenance_sla_rules ORDER BY priority").fetchall()

        # Get checklist templates
        checklists = db.execute("""
            SELECT mct.*,
                   (SELECT COUNT(*) FROM maintenance_checklist_items mci WHERE mci.template_id = mct.id) as item_count
            FROM maintenance_checklist_templates mct
            WHERE mct.is_active = 1
        """).fetchall()

        # Get teams
        teams = db.execute("SELECT * FROM maintenance_teams WHERE is_active = 1 ORDER BY team_name").fetchall()

        return render_template('maintenance/settings.html',
                             maint_types=maint_types,
                             sla_rules=sla_rules,
                             checklists=checklists,
                             teams=teams,
                             priorities=MAINTENANCE_PRIORITIES)
    finally:
        db.close()


@maintenance_bp.route('/settings/maintenance-types/save', methods=['POST'])
@require_login
def save_maintenance_type():
    """Save Maintenance Type."""
    user_id = session.get('user_id')
    db = get_db()
    try:
        data = request.get_json()
        type_id = data.get('id')

        if type_id:
            db.execute("""
                UPDATE maintenance_types SET
                    name = ?, description = ?, category = ?,
                    default_priority = ?, estimated_duration_hours = ?,
                    estimated_cost = ?, requires_downtime = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                data.get('name'),
                data.get('description'),
                data.get('category'),
                data.get('default_priority', 'Medium'),
                data.get('estimated_duration_hours', 0),
                data.get('estimated_cost', 0),
                1 if data.get('requires_downtime') else 0,
                type_id
            ))
            log_audit('maintenance_type', type_id, 'UPDATE', user_id)
        else:
            cursor = db.execute("""
                INSERT INTO maintenance_types
                (name, code, category, description, default_priority,
                 estimated_duration_hours, estimated_cost, requires_downtime, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('name'),
                data.get('code'),
                data.get('category', 'Preventive'),
                data.get('description'),
                data.get('default_priority', 'Medium'),
                data.get('estimated_duration_hours', 0),
                data.get('estimated_cost', 0),
                1 if data.get('requires_downtime') else 0,
                user_id
            ))
            type_id = cursor.lastrowid
            log_audit('maintenance_type', type_id, 'CREATE', user_id)

        db.commit()
        return jsonify({'success': True, 'id': type_id})

    finally:
        db.close()


@maintenance_bp.route('/settings/sla-rules/save', methods=['POST'])
@require_login
def save_sla_rule():
    """Save SLA Rule."""
    user_id = session.get('user_id')
    db = get_db()
    try:
        data = request.get_json()
        rule_id = data.get('id')

        if rule_id:
            db.execute("""
                UPDATE maintenance_sla_rules SET
                    rule_name = ?, response_time_hours = ?, resolution_time_hours = ?,
                    escalation_1_hours = ?, escalation_2_hours = ?,
                    is_active = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                data.get('rule_name'),
                data.get('response_time_hours', 4),
                data.get('resolution_time_hours', 24),
                data.get('escalation_1_hours', 2),
                data.get('escalation_2_hours', 4),
                1 if data.get('is_active') else 0,
                data.get('notes'),
                rule_id
            ))
            log_audit('sla_rule', rule_id, 'UPDATE', user_id)
        else:
            cursor = db.execute("""
                INSERT INTO maintenance_sla_rules
                (rule_code, rule_name, priority, response_time_hours, resolution_time_hours,
                 escalation_1_hours, escalation_2_hours, is_active, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('rule_code'),
                data.get('rule_name'),
                data.get('priority', 'Medium'),
                data.get('response_time_hours', 4),
                data.get('resolution_time_hours', 24),
                data.get('escalation_1_hours', 2),
                data.get('escalation_2_hours', 4),
                1 if data.get('is_active') else 0,
                data.get('notes')
            ))
            rule_id = cursor.lastrowid
            log_audit('sla_rule', rule_id, 'CREATE', user_id)

        db.commit()
        return jsonify({'success': True, 'id': rule_id})

    finally:
        db.close()


# =============================================================================
# CALENDAR VIEW
# =============================================================================

@maintenance_bp.route('/calendar')
@require_login
def calendar():
    """Maintenance Calendar View."""
    db = get_db()
    try:
        view = request.args.get('view', 'month')
        date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))

        # Get all work orders and PM schedules for the view period
        start_date = datetime.strptime(date, '%Y-%m-%d')
        if view == 'month':
            start = start_date.replace(day=1)
            end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        elif view == 'week':
            start = start_date - timedelta(days=start_date.weekday())
            end = start + timedelta(days=6)
        else:
            start = start_date
            end = start_date

        # Get scheduled items
        work_orders = db.execute("""
            SELECT mwo.id, mwo.work_order_number as title,
                   mwo.scheduled_start_date as start,
                   mwo.scheduled_end_date as end,
                   mwo.priority,
                   mwo.status,
                   'work_order' as type,
                   a.name as asset_name
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            WHERE mwo.status NOT IN ('Completed', 'Closed', 'Canceled')
            AND (mwo.scheduled_start_date BETWEEN ? AND ? OR mwo.scheduled_end_date BETWEEN ? AND ?)
        """, (start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'),
              start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))).fetchall()

        pm_schedules = db.execute("""
            SELECT ms.id, COALESCE(ms.schedule_name, mt.name) as title,
                   ms.next_due_date as start,
                   ms.next_due_date as end,
                   ms.priority,
                   'PM' as status,
                   'pm' as type,
                   a.name as asset_name
            FROM maintenance_schedules ms
            JOIN assets a ON ms.asset_id = a.id
            JOIN maintenance_types mt ON ms.maintenance_type_id = mt.id
            WHERE ms.is_active = 1
            AND ms.next_due_date BETWEEN ? AND ?
        """, (start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))).fetchall()

        events = []
        for wo in work_orders:
            events.append({
                'id': wo['id'],
                'title': f"{wo['title']} - {wo['asset_name']}",
                'start': wo['start'],
                'end': wo['end'],
                'priority': wo['priority'],
                'status': wo['status'],
                'type': 'work_order',
                'color': 'blue' if wo['status'] == 'In Progress' else 'yellow'
            })

        for pm in pm_schedules:
            events.append({
                'id': pm['id'],
                'title': f"[PM] {pm['title']} - {pm['asset_name']}",
                'start': pm['start'],
                'end': pm['end'],
                'priority': pm['priority'],
                'status': pm['status'],
                'type': 'pm',
                'color': 'green'
            })

        return render_template('maintenance/calendar.html',
                             events=events,
                             view=view,
                             date=date,
                             start_date=start.strftime('%Y-%m-%d'),
                             end_date=end.strftime('%Y-%m-%d'))
    finally:
        db.close()


# =============================================================================
# AUDIT LOGS
# =============================================================================

@maintenance_bp.route('/audit-logs')
@require_login
def audit_logs():
    """Maintenance Audit Logs."""
    db = get_db()
    try:
        entity_filter = request.args.get('entity', '')
        action_filter = request.args.get('action', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')

        query = """
            SELECT pal.*, u.username
            FROM platform_audit_log pal
            LEFT JOIN users u ON pal.user_id = u.id
            WHERE pal.entity_type LIKE 'maintenance%'
                OR pal.entity_type LIKE '%work_order%'
                OR pal.entity_type LIKE '%pm_%'
                OR pal.entity_type LIKE '%facility%'
        """
        params = []

        if entity_filter:
            query += " AND pal.entity_type = ?"
            params.append(entity_filter)

        if action_filter:
            query += " AND pal.action = ?"
            params.append(action_filter)

        if date_from:
            query += " AND date(pal.created_at) >= ?"
            params.append(date_from)

        if date_to:
            query += " AND date(pal.created_at) <= ?"
            params.append(date_to)

        query += " ORDER BY pal.created_at DESC LIMIT 100"

        logs = db.execute(query, params).fetchall()

        return render_template('maintenance/audit_logs.html',
                             logs=logs,
                             entity_filter=entity_filter,
                             action_filter=action_filter,
                             date_from=date_from,
                             date_to=date_to)
    finally:
        db.close()


# =============================================================================
# MY WORK ORDERS (Technician View)
# =============================================================================

@maintenance_bp.route('/my-work-orders')
@require_login
def my_work_orders():
    """Current User's Assigned Work Orders."""
    user_id = session.get('user_id')
    db = get_db()
    try:
        # Get employee_id for current user
        employee = db.execute("SELECT id FROM hr_employees WHERE user_id = ?", (user_id,)).fetchone()

        if not employee:
            flash('No employee record found for your account.', 'warning')
            return redirect(url_for('maintenance.dashboard'))

        work_orders = db.execute("""
            SELECT mwo.*, a.asset_code, a.name as asset_name,
                   mt.name as maintenance_type
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            JOIN maintenance_types mt ON mwo.maintenance_type_id = mt.id
            WHERE mwo.assigned_technician_id = ?
            AND mwo.status NOT IN ('Completed', 'Closed', 'Canceled')
            ORDER BY mwo.priority DESC, mwo.due_date ASC
        """, (employee['id'],)).fetchall()

        return render_template('maintenance/my_work_orders.html',
                             work_orders=work_orders)
    finally:
        db.close()


# =============================================================================
# EXECUTIVE DASHBOARD
# =============================================================================

@maintenance_bp.route('/executive-dashboard')
@require_login
def executive_dashboard():
    """Maintenance Executive Dashboard with KPIs and metrics."""
    db = get_db()
    try:
        # Get overall stats
        open_wos = db.execute("""
            SELECT COUNT(*) as cnt FROM maintenance_work_orders
            WHERE status NOT IN ('Completed', 'Closed', 'Canceled')
        """).fetchone()['cnt']

        overdue_wos = db.execute("""
            SELECT COUNT(*) as cnt FROM maintenance_work_orders
            WHERE status NOT IN ('Completed', 'Closed', 'Canceled')
            AND (due_date < date('now') OR (scheduled_end_date < date('now') AND status = 'In Progress'))
        """).fetchone()['cnt']

        in_progress = db.execute("""
            SELECT COUNT(*) as cnt FROM maintenance_work_orders WHERE status = 'In Progress'
        """).fetchone()['cnt']

        # PM Compliance
        compliance = get_pm_compliance_rate()
        pm_compliance_rate = compliance.get('compliance_rate', 0) if compliance else 0

        # MTBF and MTTR - calculated from actual downtime records
        total_downtime = db.execute("""
            SELECT COALESCE(SUM(total_hours), 0) as total FROM maintenance_downtime_logs
            WHERE date(downtime_start) >= date('now', '-30 days')
        """).fetchone()['total']

        incident_count = db.execute("""
            SELECT COUNT(*) as cnt FROM maintenance_downtime_logs
            WHERE date(downtime_start) >= date('now', '-30 days')
        """).fetchone()['cnt']

        # Real MTBF calculation: total operating time / number of failures
        # Operating time = 30 days * 24 hours = 720 hours, minus downtime
        operating_time = (30 * 24) - total_downtime if total_downtime < 720 else 1
        mtbf = operating_time / incident_count if incident_count > 0 else operating_time
        mttr = total_downtime / incident_count if incident_count > 0 else 0
        availability = (mtbf / (mtbf + mttr) * 100) if mttr > 0 or incident_count > 0 else 100

        # Cost stats
        total_cost = db.execute("""
            SELECT COALESCE(SUM(amount), 0) as total FROM maintenance_cost_entries
            WHERE cost_date >= date('now', '-30 days')
        """).fetchone()['total']

        labor_cost = db.execute("""
            SELECT COALESCE(SUM(labor_cost), 0) as total FROM maintenance_labor_logs
            WHERE work_date >= date('now', '-30 days')
        """).fetchone()['total']

        parts_cost = db.execute("""
            SELECT COALESCE(SUM(total_cost), 0) as total FROM maintenance_parts_usage
            WHERE issue_date >= date('now', '-30 days')
        """).fetchone()['total']

        # Active technicians
        active_techs = db.execute("""
            SELECT COUNT(DISTINCT assigned_technician_id) as cnt FROM maintenance_work_orders
            WHERE status IN ('Assigned', 'In Progress')
            AND assigned_technician_id IS NOT NULL
        """).fetchone()['cnt']

        # Work order status distribution
        wo_status_dist = db.execute("""
            SELECT status, COUNT(*) as count FROM maintenance_work_orders
            GROUP BY status
        """).fetchall()

        total_wos = db.execute("SELECT COUNT(*) as cnt FROM maintenance_work_orders").fetchone()['cnt']

        # Top failing equipment
        top_failing_equipment = db.execute("""
            SELECT a.name as asset_name, a.asset_code, COUNT(*) as failure_count
            FROM maintenance_downtime_logs mdl
            JOIN assets a ON mdl.asset_id = a.id
            WHERE date(mdl.downtime_start) >= date('now', '-90 days')
            GROUP BY a.id
            ORDER BY failure_count DESC
            LIMIT 5
        """).fetchall()

        # Technician utilization
        tech_utilization = db.execute("""
            SELECT e.first_name || ' ' || e.last_name as technician_name,
                   COUNT(mwo.id) as assigned_count,
                   SUM(CASE WHEN mwo.status = 'In Progress' THEN 1 ELSE 0 END) as in_progress_count,
                   CASE WHEN e.max_weekly_hours > 0
                        THEN (COUNT(mwo.id) * 40.0 / e.max_weekly_hours * 100)
                        ELSE 50 END as utilization
            FROM hr_employees e
            LEFT JOIN maintenance_work_orders mwo ON e.id = mwo.assigned_technician_id
                AND mwo.status NOT IN ('Completed', 'Closed', 'Canceled')
            WHERE e.status = 'Active'
            GROUP BY e.id
            LIMIT 10
        """).fetchall()

        # Downtime by reason
        downtime_by_reason = db.execute("""
            SELECT downtime_reason, SUM(total_hours) as total_hours, COUNT(*) as count
            FROM maintenance_downtime_logs
            WHERE date(downtime_start) >= date('now', '-30 days')
            GROUP BY downtime_reason
            ORDER BY total_hours DESC
            LIMIT 5
        """).fetchall()

        # Critical alerts (overdue WOs and missed PMs)
        critical_alerts = []
        for wo in db.execute("""
            SELECT work_order_number as title, issue_description as message, created_at
            FROM maintenance_work_orders
            WHERE priority = 'Critical' AND status NOT IN ('Completed', 'Closed', 'Canceled')
            LIMIT 5
        """).fetchall():
            critical_alerts.append({
                'title': f"Critical WO: {wo['title']}",
                'message': wo['message'][:100] if wo['message'] else 'No description',
                'created_at': wo['created_at']
            })

        stats = {
            'open_work_orders': open_wos,
            'overdue_work_orders': overdue_wos,
            'in_progress': in_progress,
            'total_wos': total_wos,
            'pm_compliance_rate': pm_compliance_rate,
            'missed_pm': db.execute("SELECT COUNT(*) as cnt FROM maintenance_schedules WHERE is_active = 1 AND next_due_date < date('now')").fetchone()['cnt'],
            'mtbf': mtbf,
            'mttr': mttr,
            'availability': availability,
            'total_cost': total_cost,
            'labor_cost': labor_cost,
            'parts_cost': parts_cost,
            'active_technicians': active_techs,
            'pm_cost_pct': (total_cost - labor_cost - parts_cost) / total_cost * 100 if total_cost > 0 else 0,
            'cm_cost_pct': labor_cost / total_cost * 100 if total_cost > 0 else 0,
            'cost_trend': 'stable',
        }

        return render_template('maintenance/executive_dashboard.html',
                             stats=stats,
                             wo_status_dist=wo_status_dist,
                             top_failing_equipment=top_failing_equipment,
                             tech_utilization=tech_utilization,
                             downtime_by_reason=downtime_by_reason,
                             critical_alerts=critical_alerts)
    finally:
        db.close()


# =============================================================================
# PLANNER BOARD
# =============================================================================

@maintenance_bp.route('/planner-board')
@require_login
def planner_board():
    """Maintenance Planner Board for scheduling and assignment."""
    db = get_db()
    try:
        # Get work orders grouped by status
        unscheduled = db.execute("""
            SELECT mwo.*, a.name as asset_name, a.asset_code,
                   e.first_name || ' ' || e.last_name as technician_name
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            LEFT JOIN hr_employees e ON mwo.assigned_technician_id = e.id
            WHERE mwo.status NOT IN ('Completed', 'Closed', 'Canceled')
            AND mwo.scheduled_start_date IS NULL
            ORDER BY mwo.priority DESC, mwo.issue_date ASC
        """).fetchall()

        scheduled = db.execute("""
            SELECT mwo.*, a.name as asset_name, a.asset_code,
                   e.first_name || ' ' || e.last_name as technician_name
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            LEFT JOIN hr_employees e ON mwo.assigned_technician_id = e.id
            WHERE mwo.status = 'Scheduled'
            ORDER BY mwo.scheduled_start_date ASC
        """).fetchall()

        in_progress = db.execute("""
            SELECT mwo.*, a.name as asset_name, a.asset_code,
                   e.first_name || ' ' || e.last_name as technician_name,
                   (SELECT COUNT(*) FROM maintenance_work_order_tasks WHERE work_order_id = mwo.id AND is_completed = 1) * 100.0 /
                   NULLIF((SELECT COUNT(*) FROM maintenance_work_order_tasks WHERE work_order_id = mwo.id), 0) as progress_pct
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            LEFT JOIN hr_employees e ON mwo.assigned_technician_id = e.id
            WHERE mwo.status = 'In Progress'
            ORDER BY mwo.scheduled_start_date ASC
        """).fetchall()

        on_hold = db.execute("""
            SELECT mwo.*, a.name as asset_name, a.asset_code,
                   e.first_name || ' ' || e.last_name as technician_name
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            LEFT JOIN hr_employees e ON mwo.assigned_technician_id = e.id
            WHERE mwo.status = 'On Hold'
            ORDER BY mwo.priority DESC
        """).fetchall()

        completed_today = db.execute("""
            SELECT mwo.*, a.name as asset_name, a.asset_code,
                   e.first_name || ' ' || e.last_name as technician_name
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            LEFT JOIN hr_employees e ON mwo.assigned_technician_id = e.id
            WHERE mwo.status = 'Completed'
            AND date(mwo.completed_at) = date('now')
            ORDER BY mwo.completed_at DESC
        """).fetchall()

        # Stats
        stats = {
            'total': unscheduled|length + scheduled|length + in_progress|length + on_hold|length,
            'scheduled': scheduled|length,
            'unscheduled': unscheduled|length,
            'in_progress': in_progress|length,
            'overdue': db.execute("SELECT COUNT(*) as cnt FROM maintenance_work_orders WHERE status = 'In Progress' AND scheduled_end_date < date('now')").fetchone()['cnt'],
            'capacity_used': 75,  # Placeholder
        }

        # Technician workload
        technician_workload = db.execute("""
            SELECT e.id, e.first_name || ' ' || e.last_name as technician_name,
                   COUNT(mwo.id) as assigned,
                   SUM(CASE WHEN mwo.status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
                   SUM(CASE WHEN mwo.status = 'Completed' AND date(mwo.completed_at) >= date('now', 'start of month') THEN 1 ELSE 0 END) as completed_mtd,
                   CASE WHEN e.max_weekly_hours > 0
                        THEN (COUNT(mwo.id) * 40.0 / e.max_weekly_hours * 100)
                        ELSE 50 END as capacity_pct
            FROM hr_employees e
            LEFT JOIN maintenance_work_orders mwo ON e.id = mwo.assigned_technician_id
                AND mwo.status NOT IN ('Closed', 'Canceled')
            WHERE e.status = 'Active'
            GROUP BY e.id
        """).fetchall()

        technicians = db.execute("SELECT id, first_name, last_name FROM hr_employees WHERE status = 'Active' ORDER BY first_name").fetchall()

        return render_template('maintenance/planner_board.html',
                             unscheduled=unscheduled,
                             scheduled=scheduled,
                             in_progress=in_progress,
                             on_hold=on_hold,
                             completed_today=completed_today,
                             stats=stats,
                             technician_workload=technician_workload,
                             technicians=technicians)
    finally:
        db.close()


@maintenance_bp.route('/work-orders/<int:wo_id>/schedule', methods=['POST'])
@require_login
def schedule_work_order(wo_id):
    """Schedule a work order."""
    user_id = session.get('user_id')
    db = get_db()
    try:
        data = request.get_json()

        db.execute("""
            UPDATE maintenance_work_orders SET
                status = 'Scheduled',
                scheduled_start_date = ?,
                assigned_technician_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get('scheduled_date'),
            data.get('technician_id') or None,
            wo_id
        ))
        db.commit()

        log_audit('maintenance_work_order', wo_id, 'SCHEDULE', user_id)
        return jsonify({'success': True})

    finally:
        db.close()


# =============================================================================
# DOWNTIME & RELIABILITY CENTER
# =============================================================================

@maintenance_bp.route('/reliability-dashboard')
@maintenance_bp.route('/downtime-reliability')
@require_login
def reliability_dashboard():
    """Downtime and Reliability Center."""
    db = get_db()
    try:
        # Key metrics
        total_downtime = db.execute("""
            SELECT COALESCE(SUM(total_hours), 0) as total FROM maintenance_downtime_logs
            WHERE date(downtime_start) >= date('now', '-30 days')
        """).fetchone()['total']

        incident_count = db.execute("""
            SELECT COUNT(*) as cnt FROM maintenance_downtime_logs
            WHERE date(downtime_start) >= date('now', '-30 days')
        """).fetchone()['cnt']

        planned = db.execute("""
            SELECT COALESCE(SUM(total_hours), 0) as total FROM maintenance_downtime_logs
            WHERE date(downtime_start) >= date('now', '-30 days') AND planned_downtime = 1
        """).fetchone()['total']

        unplanned = total_downtime - planned

        # Real MTBF/MTTR calculation
        operating_time = (30 * 24) - total_downtime if total_downtime < 720 else 1
        mtbf = operating_time / incident_count if incident_count > 0 else operating_time
        mttr = total_downtime / incident_count if incident_count > 0 else 0
        availability = (mtbf / (mtbf + mttr) * 100) if mttr > 0 or incident_count > 0 else 100

        # Cost metrics
        repair_cost = db.execute("""
            SELECT COALESCE(SUM(actual_cost), 0) as total FROM maintenance_work_orders
            WHERE status = 'Completed' AND date(completed_at) >= date('now', '-30 days')
        """).fetchone()['total']

        stats = {
            'total_downtime': total_downtime,
            'incident_count': incident_count,
            'planned_downtime': planned,
            'unplanned_downtime': unplanned,
            'planned_pct': (planned / total_downtime * 100) if total_downtime > 0 else 0,
            'unplanned_pct': (unplanned / total_downtime * 100) if total_downtime > 0 else 0,
            'mtbf': mtbf,
            'mttr': mttr,
            'availability': availability,
            'production_loss': total_downtime * 1000,  # Placeholder calculation
            'repair_cost': repair_cost,
            'total_cost': total_downtime * 1000 + repair_cost,
        }

        # Recent incidents
        recent_incidents = db.execute("""
            SELECT mdl.*, a.name as asset_name,
                   CASE WHEN mdl.downtime_end IS NULL THEN 1 ELSE 0 END as is_ongoing
            FROM maintenance_downtime_logs mdl
            LEFT JOIN assets a ON mdl.asset_id = a.id
            ORDER BY mdl.downtime_start DESC
            LIMIT 10
        """).fetchall()

        # Top failure reasons
        top_failure_reasons = db.execute("""
            SELECT downtime_reason as reason, COUNT(*) as count, SUM(total_hours) as total_hours
            FROM maintenance_downtime_logs
            WHERE date(downtime_start) >= date('now', '-90 days')
            GROUP BY downtime_reason
            ORDER BY count DESC
            LIMIT 5
        """).fetchall()

        # Reliability heatmap (equipment scores)
        reliability_heatmap = db.execute("""
            SELECT a.id, a.asset_code, a.name as asset_name,
                   CASE WHEN COUNT(mdl.id) = 0 THEN 100
                        ELSE MAX(0, 100 - COUNT(mdl.id) * 10) END as reliability_score,
                   COUNT(mdl.id) as incident_count,
                   CASE WHEN COUNT(mdl.id) >= 5 THEN '#ef4444'
                        WHEN COUNT(mdl.id) >= 3 THEN '#f97316'
                        WHEN COUNT(mdl.id) >= 1 THEN '#eab308'
                        ELSE '#22c55e' END as color
            FROM assets a
            LEFT JOIN maintenance_downtime_logs mdl ON a.id = mdl.asset_id
                AND date(mdl.downtime_start) >= date('now', '-90 days')
            WHERE a.status NOT IN ('Disposed', 'Retired')
            GROUP BY a.id
            ORDER BY incident_count DESC
            LIMIT 12
        """).fetchall()

        # Recurring failure patterns
        recurring_patterns = db.execute("""
            SELECT a.name as asset_name, COUNT(*) as failure_count,
                   SUM(mdl.total_hours) as total_downtime,
                   AVG(mdl.total_hours) as avg_mttr,
                   mdl.root_cause,
                   'Open' as status
            FROM maintenance_downtime_logs mdl
            JOIN assets a ON mdl.asset_id = a.id
            WHERE date(mdl.downtime_start) >= date('now', '-180 days')
            GROUP BY a.id, mdl.root_cause
            HAVING COUNT(*) > 1
            ORDER BY failure_count DESC
            LIMIT 10
        """).fetchall()

        return render_template('maintenance/reliability_dashboard.html',
                             stats=stats,
                             recent_incidents=recent_incidents,
                             top_failure_reasons=top_failure_reasons,
                             reliability_heatmap=reliability_heatmap,
                             recurring_patterns=recurring_patterns)
    finally:
        db.close()


# =============================================================================
# BREAKDOWN & EMERGENCY CENTER
# =============================================================================

@maintenance_bp.route('/breakdown-center')
@maintenance_bp.route('/breakdown')
@require_login
def breakdown_center():
    """Breakdown and Emergency Maintenance Center."""
    db = get_db()
    try:
        # Active emergencies (work orders with Emergency type)
        active_emergencies = db.execute("""
            SELECT mwo.*, a.name as asset_name, a.asset_code
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            WHERE mwo.work_order_type = 'Emergency'
            AND mwo.status NOT IN ('Completed', 'Closed', 'Canceled')
            ORDER BY mwo.created_at DESC
        """).fetchall()

        # Active breakdowns
        active_breakdowns = db.execute("""
            SELECT mdl.*, a.name as asset_name, mwo.id as work_order_id, mwo.work_order_number
            FROM maintenance_downtime_logs mdl
            LEFT JOIN assets a ON mdl.asset_id = a.id
            LEFT JOIN maintenance_work_orders mwo ON mdl.work_order_id = mwo.id
            WHERE mdl.is_resolved = 0
            ORDER BY mdl.downtime_start DESC
        """).fetchall()

        # Stats
        stats = {
            'active_emergencies': len(active_emergencies),
            'active_breakdowns': len(active_breakdowns),
            'avg_response_time': 45,  # Placeholder
            'avg_recovery_time': db.execute("""
                SELECT AVG(total_hours) as avg FROM maintenance_downtime_logs
                WHERE date(downtime_start) >= date('now', '-30 days') AND is_resolved = 1
            """).fetchone()['avg'] or 0,
            'resolved_today': db.execute("""
                SELECT COUNT(*) as cnt FROM maintenance_downtime_logs
                WHERE date(downtime_end) = date('now') AND is_resolved = 1
            """).fetchone()['cnt'],
        }

        # Combined incident log
        incident_log = []

        for em in db.execute("""
            SELECT 'Emergency' as type, mwo.work_order_number as reference,
                   a.name as asset_name, mwo.issue_description as description,
                   mwo.downtime_hours as duration, mwo.priority as impact_level,
                   mwo.status, mwo.id as work_order_id, mwo.created_at
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            WHERE mwo.work_order_type = 'Emergency'
            ORDER BY mwo.created_at DESC
            LIMIT 20
        """).fetchall():
            incident_log.append({
                'type': 'Emergency',
                'reference': em['reference'],
                'asset_name': em['asset_name'],
                'description': em['description'],
                'duration': em['duration'] or 0,
                'impact_level': 'Critical',
                'status': 'Resolved' if em['status'] in ('Completed', 'Closed') else 'Active',
                'work_order_id': em['work_order_id']
            })

        return render_template('maintenance/breakdown_center.html',
                             active_emergencies=active_emergencies,
                             active_breakdowns=active_breakdowns,
                             stats=stats,
                             incident_log=incident_log)
    finally:
        db.close()


@maintenance_bp.route('/emergency/new', methods=['GET', 'POST'])
@require_login
def emergency_new():
    """Create Emergency Work Order."""
    user_id = session.get('user_id')
    db = get_db()
    try:
        if request.method == 'POST':
            from asset_models import get_next_work_order_number
            data = request.form
            wo_number = get_next_work_order_number()

            cursor = db.execute("""
                INSERT INTO maintenance_work_orders
                (work_order_number, asset_id, maintenance_type_id, work_order_type,
                 priority, status, issue_date, issue_description,
                 assigned_technician_id, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                wo_number,
                data.get('asset_id'),
                data.get('maintenance_type_id'),
                'Emergency',
                'Critical',
                'In Progress',
                datetime.now().strftime('%Y-%m-%d'),
                data.get('issue_description'),
                data.get('assigned_technician_id') or None,
                user_id
            ))
            db.commit()

            # Create downtime log
            db.execute("""
                INSERT INTO maintenance_downtime_logs
                (log_number, asset_id, work_order_id, downtime_reason, downtime_start,
                 impact_level, is_resolved, created_by)
                VALUES (?, ?, ?, ?, ?, ?, 0, ?)
            """, (
                get_next_downtime_log_number(),
                data.get('asset_id'),
                cursor.lastrowid,
                'Emergency breakdown',
                datetime.now().strftime('%Y-%m-%d %H:%M'),
                'Critical',
                user_id
            ))
            db.commit()

            log_audit('maintenance_work_order', cursor.lastrowid, 'CREATE_EMERGENCY', user_id)
            flash(f'Emergency work order {wo_number} created.', 'success')
            return redirect(url_for('maintenance.breakdown_center'))

        assets = db.execute("SELECT id, asset_code, name FROM assets WHERE status NOT IN ('Disposed', 'Retired') ORDER BY asset_code").fetchall()
        maintenance_types = db.execute("SELECT * FROM maintenance_types WHERE is_active = 1").fetchall()
        technicians = db.execute("SELECT id, first_name, last_name FROM hr_employees WHERE status = 'Active' ORDER BY first_name").fetchall()

        return render_template('maintenance/emergency_form.html',
                             assets=assets,
                             maintenance_types=maintenance_types,
                             technicians=technicians)
    finally:
        db.close()


# =============================================================================
# PM COMPLIANCE DASHBOARD
# =============================================================================

@maintenance_bp.route('/pm-compliance-dashboard')
@maintenance_bp.route('/pm-compliance')
@require_login
def pm_compliance_dashboard():
    """PM Compliance Dashboard."""
    db = get_db()
    try:
        compliance = get_pm_compliance_rate()

        # Due this week
        due_this_week = db.execute("""
            SELECT COUNT(*) as cnt FROM maintenance_schedules
            WHERE is_active = 1
            AND next_due_date >= date('now')
            AND next_due_date <= date('now', '+7 days')
        """).fetchone()['cnt']

        on_track = db.execute("""
            SELECT COUNT(*) as cnt FROM maintenance_schedules
            WHERE is_active = 1
            AND next_due_date >= date('now')
            AND next_due_date <= date('now', '+7 days')
        """).fetchone()['cnt']

        at_risk = db.execute("""
            SELECT COUNT(*) as cnt FROM maintenance_schedules
            WHERE is_active = 1
            AND next_due_date < date('now', '+3 days')
            AND next_due_date >= date('now')
        """).fetchone()['cnt']

        overdue = db.execute("""
            SELECT COUNT(*) as cnt FROM maintenance_schedules
            WHERE is_active = 1 AND next_due_date < date('now')
        """).fetchone()['cnt']

        overdue_by_priority = db.execute("""
            SELECT priority, COUNT(*) as count FROM maintenance_schedules
            WHERE is_active = 1 AND next_due_date < date('now')
            GROUP BY priority
        """).fetchall()

        stats = {
            'due_this_week': due_this_week,
            'on_track': on_track,
            'at_risk': at_risk,
            'overdue': overdue,
            'overdue_by_priority': overdue_by_priority,
            'generated_wos': db.execute("""
                SELECT COUNT(*) as cnt FROM maintenance_work_orders
                WHERE work_order_type = 'Preventive'
                AND date(created_at) >= date('now', 'start of month')
            """).fetchone()['cnt'],
            'completed_wos': db.execute("""
                SELECT COUNT(*) as cnt FROM maintenance_work_orders
                WHERE work_order_type = 'Preventive' AND status = 'Completed'
                AND date(completed_at) >= date('now', 'start of month')
            """).fetchone()['cnt'],
        }

        # Compliance by priority
        compliance_by_priority = db.execute("""
            SELECT priority,
                   SUM(CASE WHEN next_due_date >= date('now') THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as compliance_rate
            FROM maintenance_schedules
            WHERE is_active = 1
            GROUP BY priority
        """).fetchall()

        # PM by type
        pm_by_type = db.execute("""
            SELECT mt.name as maintenance_type, COUNT(*) as count
            FROM maintenance_schedules ms
            JOIN maintenance_types mt ON ms.maintenance_type_id = mt.id
            WHERE ms.is_active = 1
            GROUP BY mt.name
        """).fetchall()

        # Upcoming PM
        upcoming_pm = db.execute("""
            SELECT ms.*, a.name as asset_name
            FROM maintenance_schedules ms
            JOIN assets a ON ms.asset_id = a.id
            WHERE ms.is_active = 1
            AND ms.next_due_date >= date('now')
            AND ms.next_due_date <= date('now', '+14 days')
            ORDER BY ms.next_due_date ASC
        """).fetchall()

        # Overdue PM
        overdue_pm = db.execute("""
            SELECT ms.*, a.name as asset_name, a.asset_code, mt.name as maintenance_type,
                   julianday('now') - julianday(ms.next_due_date) as days_overdue
            FROM maintenance_schedules ms
            JOIN assets a ON ms.asset_id = a.id
            JOIN maintenance_types mt ON ms.maintenance_type_id = mt.id
            WHERE ms.is_active = 1 AND ms.next_due_date < date('now')
            ORDER BY days_overdue DESC
        """).fetchall()

        # Forecast
        forecast = db.execute("""
            SELECT strftime('%Y-%m', next_due_date) as month, COUNT(*) as count
            FROM maintenance_schedules
            WHERE is_active = 1 AND next_due_date >= date('now')
            GROUP BY strftime('%Y-%m', next_due_date)
            ORDER BY month
            LIMIT 12
        """).fetchall()

        return render_template('maintenance/pm_compliance_dashboard.html',
                             compliance=compliance,
                             stats=stats,
                             compliance_by_priority=compliance_by_priority,
                             pm_by_type=pm_by_type,
                             upcoming_pm=upcoming_pm,
                             overdue_pm=overdue_pm,
                             forecast=forecast)
    finally:
        db.close()


# =============================================================================
# ENHANCED EAM/PM ROUTES - FUNCTIONAL LOCATIONS
# =============================================================================

@maintenance_bp.route('/functional-locations')
@require_login
def functional_locations_list():
    """List all functional locations."""
    db = get_db()
    try:
        locations = db.execute("""
            SELECT fl.*,
                   pfl.location_code as parent_code, pfl.name as parent_name,
                   c.name as company_name
            FROM functional_locations fl
            LEFT JOIN functional_locations pfl ON fl.parent_location_id = pfl.id
            LEFT JOIN companies c ON fl.company_id = c.id
            ORDER BY fl.hierarchy_path
        """).fetchall()

        return render_template('maintenance/functional_locations_list.html',
                             locations=locations)
    finally:
        db.close()


@maintenance_bp.route('/functional-locations/<int:loc_id>')
@require_login
def functional_location_detail(loc_id):
    """View functional location details."""
    db = get_db()
    try:
        loc = db.execute("""
            SELECT fl.*,
                   pfl.location_code as parent_code, pfl.name as parent_name,
                   c.name as company_name, cb.name as branch_name
            FROM functional_locations fl
            LEFT JOIN functional_locations pfl ON fl.parent_location_id = pfl.id
            LEFT JOIN companies c ON fl.company_id = c.id
            LEFT JOIN company_branches cb ON fl.branch_id = cb.id
            WHERE fl.id = ?
        """, (loc_id,)).fetchone()

        # Get child locations
        children = db.execute("""
            SELECT * FROM functional_locations WHERE parent_location_id = ?
            ORDER BY location_code
        """, (loc_id,)).fetchall()

        # Get equipment at this location
        equipment = db.execute("""
            SELECT id, asset_code, name, status FROM assets
            WHERE functional_location_id = ?
            ORDER BY asset_code
        """, (loc_id,)).fetchall()

        # Get hierarchy path
        hierarchy = []
        current_id = loc['parent_location_id']
        while current_id:
            parent = db.execute("SELECT id, location_code, name, parent_location_id FROM functional_locations WHERE id = ?",
                              (current_id,)).fetchone()
            if parent:
                hierarchy.insert(0, dict(parent))
                current_id = parent['parent_location_id']
            else:
                break

        return render_template('maintenance/functional_location_detail.html',
                             location=loc,
                             children=children,
                             equipment=equipment,
                             hierarchy=hierarchy)
    finally:
        db.close()


@maintenance_bp.route('/functional-locations/new', methods=['GET', 'POST'])
@require_login
def functional_location_new():
    """Create new functional location."""
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.form
            loc_code = data.get('location_code') or None

            if not loc_code:
                seq = db.execute("SELECT COUNT(*) as cnt FROM functional_locations").fetchone()['cnt'] + 1
                loc_code = f"FLOC-{seq:05d}"

            parent_id = data.get('parent_location_id')
            parent_path = ""
            hierarchy_level = 0
            if parent_id:
                parent = db.execute("SELECT hierarchy_path, hierarchy_level FROM functional_locations WHERE id = ?",
                                   (parent_id,)).fetchone()
                if parent:
                    parent_path = parent['hierarchy_path'] or ""
                    hierarchy_level = parent['hierarchy_level'] + 1

            cursor = db.execute("""
                INSERT INTO functional_locations
                (location_code, name, description, location_type, parent_location_id,
                 address, cost_center, company_id, branch_id, is_active, is_critical,
                 operating_hours, hierarchy_path, hierarchy_level, latitude, longitude,
                 qr_code, bar_code, specifications, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                loc_code, data.get('name'), data.get('description'),
                data.get('location_type', 'Area'), parent_id or None,
                data.get('address'), data.get('cost_center'),
                data.get('company_id') or None, data.get('branch_id') or None,
                1 if data.get('is_active') else 0,
                1 if data.get('is_critical') else 0,
                data.get('operating_hours'),
                f"{parent_path}/{loc_code}" if parent_path else f"/{loc_code}",
                hierarchy_level,
                data.get('latitude'), data.get('longitude'),
                data.get('qr_code'), data.get('bar_code'),
                data.get('specifications'), session.get('user_id')
            ))
            db.commit()

            log_audit('functional_location', cursor.lastrowid, 'CREATE', session.get('user_id'))
            flash(f'Functional location {loc_code} created successfully.', 'success')
            return redirect(url_for('maintenance.functional_locations_list'))

        parent_locations = db.execute("""
            SELECT id, location_code, name, location_type, hierarchy_level
            FROM functional_locations ORDER BY hierarchy_path
        """).fetchall()
        companies = db.execute("SELECT id, name FROM companies ORDER BY name").fetchall()
        branches = db.execute("SELECT id, name FROM company_branches ORDER BY name").fetchall()

        return render_template('maintenance/functional_location_form.html',
                             location=None,
                             parent_locations=parent_locations,
                             companies=companies,
                             branches=branches)
    finally:
        db.close()


@maintenance_bp.route('/functional-locations/<int:loc_id>/edit', methods=['GET', 'POST'])
@require_login
def functional_location_edit(loc_id):
    """Edit functional location."""
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.form
            parent_id = data.get('parent_location_id') or None

            parent_path = ""
            hierarchy_level = 0
            if parent_id:
                parent = db.execute("SELECT hierarchy_path, hierarchy_level FROM functional_locations WHERE id = ?",
                                   (parent_id,)).fetchone()
                if parent:
                    parent_path = parent['hierarchy_path'] or ""
                    hierarchy_level = parent['hierarchy_level'] + 1

            db.execute("""
                UPDATE functional_locations SET
                name = ?, description = ?, location_type = ?, parent_location_id = ?,
                address = ?, cost_center = ?, company_id = ?, branch_id = ?,
                is_active = ?, is_critical = ?, operating_hours = ?,
                hierarchy_path = ?, hierarchy_level = ?,
                latitude = ?, longitude = ?, qr_code = ?, bar_code = ?,
                specifications = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                data.get('name'), data.get('description'),
                data.get('location_type', 'Area'), parent_id,
                data.get('address'), data.get('cost_center'),
                data.get('company_id') or None, data.get('branch_id') or None,
                1 if data.get('is_active') else 0,
                1 if data.get('is_critical') else 0,
                data.get('operating_hours'),
                f"{parent_path}/{data.get('location_code')}" if parent_path else f"/{data.get('location_code')}",
                hierarchy_level,
                data.get('latitude'), data.get('longitude'),
                data.get('qr_code'), data.get('bar_code'),
                data.get('specifications'), loc_id
            ))
            db.commit()

            log_audit('functional_location', loc_id, 'UPDATE', session.get('user_id'))
            flash('Functional location updated successfully.', 'success')
            return redirect(url_for('maintenance.functional_location_detail', loc_id=loc_id))

        loc = db.execute("SELECT * FROM functional_locations WHERE id = ?", (loc_id,)).fetchone()
        parent_locations = db.execute("""
            SELECT id, location_code, name, location_type, hierarchy_level
            FROM functional_locations WHERE id != ? ORDER BY hierarchy_path
        """, (loc_id,)).fetchall()
        companies = db.execute("SELECT id, name FROM companies ORDER BY name").fetchall()
        branches = db.execute("SELECT id, name FROM company_branches ORDER BY name").fetchall()

        return render_template('maintenance/functional_location_form.html',
                             location=loc,
                             parent_locations=parent_locations,
                             companies=companies,
                             branches=branches)
    finally:
        db.close()


# =============================================================================
# ENHANCED EAM/PM ROUTES - EQUIPMENT BOMS
# =============================================================================

@maintenance_bp.route('/equipment-boms')
@require_login
def equipment_boms_list():
    """List all equipment BOMs."""
    db = get_db()
    try:
        boms = db.execute("""
            SELECT eb.*, a.asset_code, a.name as equipment_name,
                   u.username as created_by_name
            FROM equipment_boms eb
            JOIN assets a ON eb.equipment_id = a.id
            LEFT JOIN users u ON eb.created_by = u.id
            ORDER BY eb.bom_code
        """).fetchall()

        return render_template('maintenance/equipment_boms_list.html', boms=boms)
    finally:
        db.close()


@maintenance_bp.route('/equipment-boms/<int:bom_id>')
@require_login
def equipment_bom_detail(bom_id):
    """View equipment BOM details."""
    db = get_db()
    try:
        bom = db.execute("""
            SELECT eb.*, a.asset_code, a.name as equipment_name
            FROM equipment_boms eb
            JOIN assets a ON eb.equipment_id = a.id
            WHERE eb.id = ?
        """, (bom_id,)).fetchone()

        items = db.execute("""
            SELECT ebi.*, ii.item_code, ii.description as material_name,
                   wc.work_center_code, wc.work_center_name
            FROM equipment_bom_items ebi
            LEFT JOIN inventory_items ii ON ebi.material_id = ii.id
            LEFT JOIN work_centers wc ON ebi.work_center_id = wc.id
            WHERE ebi.bom_id = ?
            ORDER BY ebi.item_sequence
        """, (bom_id,)).fetchall()

        return render_template('maintenance/equipment_bom_detail.html', bom=bom, items=items)
    finally:
        db.close()


@maintenance_bp.route('/equipment-boms/new', methods=['GET', 'POST'])
@require_login
def equipment_bom_new():
    """Create new equipment BOM."""
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.form
            bom_code = data.get('bom_code')
            if not bom_code:
                seq = db.execute("SELECT COUNT(*) as cnt FROM equipment_boms").fetchone()['cnt'] + 1
                bom_code = f"BOM-{datetime.now().strftime('%Y%m')}-{seq:04d}"

            cursor = db.execute("""
                INSERT INTO equipment_boms
                (bom_code, equipment_id, bom_type, version, is_active, is_template,
                 valid_from, valid_to, description, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bom_code, data.get('equipment_id'),
                data.get('bom_type', 'SpareParts'),
                data.get('version', 1),
                1 if data.get('is_active') else 0,
                1 if data.get('is_template') else 0,
                data.get('valid_from'), data.get('valid_to'),
                data.get('description'), session.get('user_id')
            ))
            db.commit()

            log_audit('equipment_bom', cursor.lastrowid, 'CREATE', session.get('user_id'))
            flash(f'BOM {bom_code} created successfully.', 'success')
            return redirect(url_for('maintenance.equipment_bom_detail', bom_id=cursor.lastrowid))

        equipment = db.execute("SELECT id, asset_code, name FROM assets ORDER BY asset_code").fetchall()
        return render_template('maintenance/equipment_bom_form.html', bom=None, equipment=equipment)
    finally:
        db.close()


@maintenance_bp.route('/equipment-boms/<int:bom_id>/items/new', methods=['POST'])
@require_login
def equipment_bom_item_add(bom_id):
    """Add item to BOM."""
    db = get_db()
    try:
        data = request.form
        cursor = db.execute("""
            INSERT INTO equipment_bom_items
            (bom_id, item_sequence, material_id, part_number, part_name,
             quantity, unit_of_measure, is_optional, is_substitute_allowed,
             substitute_group, work_center_id, storage_location_id, bom_position,
             lead_time_days, cost_estimate, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bom_id, data.get('item_sequence', 1), data.get('material_id') or None,
            data.get('part_number'), data.get('part_name'),
            data.get('quantity', 1), data.get('unit_of_measure', 'EA'),
            1 if data.get('is_optional') else 0,
            1 if data.get('is_substitute_allowed') else 0,
            data.get('substitute_group'), data.get('work_center_id') or None,
            data.get('storage_location_id'), data.get('bom_position'),
            data.get('lead_time_days', 0), data.get('cost_estimate', 0),
            data.get('notes')
        ))
        db.commit()

        log_audit('equipment_bom_item', cursor.lastrowid, 'CREATE', session.get('user_id'))
        flash('BOM item added successfully.', 'success')
        return redirect(url_for('maintenance.equipment_bom_detail', bom_id=bom_id))
    finally:
        db.close()


# =============================================================================
# ENHANCED EAM/PM ROUTES - WORK CENTERS
# =============================================================================

@maintenance_bp.route('/work-centers')
@require_login
def work_centers_list():
    """List all work centers."""
    db = get_db()
    try:
        work_centers = db.execute("""
            SELECT wc.*, e.first_name || ' ' || e.last_name as supervisor_name,
                   fl.location_code, fl.name as location_name
            FROM work_centers wc
            LEFT JOIN hr_employees e ON wc.supervisor_id = e.id
            LEFT JOIN functional_locations fl ON wc.location_id = fl.id
            ORDER BY wc.work_center_code
        """).fetchall()

        return render_template('maintenance/work_centers_list.html', work_centers=work_centers)
    finally:
        db.close()


@maintenance_bp.route('/work-centers/<int:wc_id>')
@require_login
def work_center_detail(wc_id):
    """View work center details."""
    db = get_db()
    try:
        wc = db.execute("""
            SELECT wc.*, e.first_name || ' ' || e.last_name as supervisor_name,
                   fl.location_code, fl.name as location_name,
                   cb.name as plant_name
            FROM work_centers wc
            LEFT JOIN hr_employees e ON wc.supervisor_id = e.id
            LEFT JOIN functional_locations fl ON wc.location_id = fl.id
            LEFT JOIN company_branches cb ON wc.plant_id = cb.id
            WHERE wc.id = ?
        """, (wc_id,)).fetchone()

        shifts = db.execute("SELECT * FROM work_center_shifts WHERE work_center_id = ? ORDER BY shift_code",
                          (wc_id,)).fetchall()

        return render_template('maintenance/work_center_detail.html', work_center=wc, shifts=shifts)
    finally:
        db.close()


@maintenance_bp.route('/work-centers/new', methods=['GET', 'POST'])
@require_login
def work_center_new():
    """Create new work center."""
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.form
            wc_code = data.get('work_center_code')
            if not wc_code:
                seq = db.execute("SELECT COUNT(*) as cnt FROM work_centers").fetchone()['cnt'] + 1
                wc_code = f"WC-{seq:04d}"

            cursor = db.execute("""
                INSERT INTO work_centers
                (work_center_code, work_center_name, plant_id, description,
                 work_center_category, location_id, cost_center, standard_wrk_dir,
                 factory_calendar, currency, available_capacity, capacity_unit,
                 utilization_target, supervisor_id, shift_pattern, capabilities,
                 skilled_workers, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                wc_code, data.get('work_center_name'), data.get('plant_id') or None,
                data.get('description'), data.get('work_center_category'),
                data.get('location_id') or None, data.get('cost_center'),
                data.get('standard_wrk_dir'), data.get('factory_calendar'),
                data.get('currency', 'USD'), data.get('available_capacity', 8.0),
                data.get('capacity_unit', 'HOUR'), data.get('utilization_target', 100.0),
                data.get('supervisor_id') or None, data.get('shift_pattern'),
                data.get('capabilities'), data.get('skilled_workers', 0),
                1 if data.get('is_active') else 0
            ))
            db.commit()

            log_audit('work_center', cursor.lastrowid, 'CREATE', session.get('user_id'))
            flash(f'Work Center {wc_code} created successfully.', 'success')
            return redirect(url_for('maintenance.work_center_detail', wc_id=cursor.lastrowid))

        functional_locs = db.execute("SELECT id, location_code, name FROM functional_locations ORDER BY location_code").fetchall()
        branches = db.execute("SELECT id, name FROM company_branches ORDER BY name").fetchall()
        supervisors = db.execute("SELECT id, first_name, last_name FROM hr_employees WHERE status = 'Active' ORDER BY first_name").fetchall()

        return render_template('maintenance/work_center_form.html',
                             work_center=None,
                             functional_locs=functional_locs,
                             branches=branches,
                             supervisors=supervisors)
    finally:
        db.close()


# =============================================================================
# ENHANCED EAM/PM ROUTES - CAPACITY PLANNING
# =============================================================================

@maintenance_bp.route('/capacity-planning')
@require_login
def capacity_planning():
    """Capacity planning view."""
    db = get_db()
    try:
        work_centers = db.execute("SELECT id, work_center_code, work_center_name FROM work_centers WHERE is_active = 1 ORDER BY work_center_code").fetchall()

        start_date = request.args.get('start_date', datetime.now().strftime('%Y-%m-%d'))
        end_date = request.args.get('end_date', (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'))
        wc_id = request.args.get('work_center_id', type=int)

        capacity_data = []
        if wc_id:
            capacity_data = db.execute("""
                SELECT wcc.*, wc.work_center_code, wc.work_center_name
                FROM work_center_capacity wcc
                JOIN work_centers wc ON wcc.work_center_id = wc.id
                WHERE wcc.work_center_id = ? AND wcc.work_date BETWEEN ? AND ?
                ORDER BY wcc.work_date
            """, (wc_id, start_date, end_date)).fetchall()
        else:
            capacity_data = db.execute("""
                SELECT wcc.*, wc.work_center_code, wc.work_center_name
                FROM work_center_capacity wcc
                JOIN work_centers wc ON wcc.work_center_id = wc.id
                WHERE wcc.work_date BETWEEN ? AND ?
                ORDER BY wc.work_center_code, wcc.work_date
            """, (start_date, end_date)).fetchall()

        return render_template('maintenance/capacity_planning.html',
                             work_centers=work_centers,
                             capacity_data=capacity_data,
                             start_date=start_date,
                             end_date=end_date,
                             selected_wc_id=wc_id)
    finally:
        db.close()


# =============================================================================
# ENHANCED EAM/PM ROUTES - MAINTENANCE STRATEGIES
# =============================================================================

@maintenance_bp.route('/strategies')
@require_login
def maintenance_strategies_list():
    """List all maintenance strategies."""
    db = get_db()
    try:
        strategies = db.execute("SELECT * FROM maintenance_strategies ORDER BY strategy_code").fetchall()
        return render_template('maintenance/strategies_list.html', strategies=strategies)
    finally:
        db.close()


@maintenance_bp.route('/strategies/new', methods=['GET', 'POST'])
@require_login
def maintenance_strategy_new():
    """Create new maintenance strategy."""
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.form
            strategy_code = data.get('strategy_code')
            if not strategy_code:
                seq = db.execute("SELECT COUNT(*) as cnt FROM maintenance_strategies").fetchone()['cnt'] + 1
                strategy_code = f"STRAT-{seq:04d}"

            cursor = db.execute("""
                INSERT INTO maintenance_strategies
                (strategy_code, strategy_name, strategy_type, description, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, (
                strategy_code, data.get('strategy_name'),
                data.get('strategy_type', 'TIME-BASED'),
                data.get('description'), 1 if data.get('is_active') else 0
            ))
            db.commit()

            log_audit('maintenance_strategy', cursor.lastrowid, 'CREATE', session.get('user_id'))
            flash(f'Strategy {strategy_code} created successfully.', 'success')
            return redirect(url_for('maintenance.maintenance_strategies_list'))

        return render_template('maintenance/strategy_form.html', strategy=None)
    finally:
        db.close()


# =============================================================================
# ENHANCED EAM/PM ROUTES - EQUIPMENT COUNTERS
# =============================================================================

@maintenance_bp.route('/counters')
@require_login
def equipment_counters_list():
    """List all equipment counters."""
    db = get_db()
    try:
        counters = db.execute("""
            SELECT mc.*, a.asset_code, a.name as equipment_name
            FROM maintenance_counters mc
            JOIN assets a ON mc.equipment_id = a.id
            ORDER BY mc.counter_code
        """).fetchall()

        return render_template('maintenance/counters_list.html', counters=counters)
    finally:
        db.close()


@maintenance_bp.route('/counters/<int:counter_id>')
@require_login
def counter_detail(counter_id):
    """View counter details and readings."""
    db = get_db()
    try:
        counter = db.execute("""
            SELECT mc.*, a.asset_code, a.name as equipment_name
            FROM maintenance_counters mc
            JOIN assets a ON mc.equipment_id = a.id
            WHERE mc.id = ?
        """, (counter_id,)).fetchone()

        readings = db.execute("""
            SELECT * FROM counter_readings
            WHERE counter_id = ?
            ORDER BY reading_date DESC
            LIMIT 100
        """, (counter_id,)).fetchall()

        return render_template('maintenance/counter_detail.html', counter=counter, readings=readings)
    finally:
        db.close()


@maintenance_bp.route('/counters/new', methods=['GET', 'POST'])
@require_login
def counter_new():
    """Create new equipment counter."""
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.form
            counter_code = data.get('counter_code')
            if not counter_code:
                seq = db.execute("SELECT COUNT(*) as cnt FROM maintenance_counters").fetchone()['cnt'] + 1
                counter_code = f"CNTR-{seq:05d}"

            cursor = db.execute("""
                INSERT INTO maintenance_counters
                (counter_code, equipment_id, counter_type, unit_of_measure,
                 min_warning_threshold, max_warning_threshold,
                 min_critical_threshold, max_critical_threshold,
                 reading_source, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                counter_code, data.get('equipment_id'),
                data.get('counter_type', 'OPERATING_HOURS'),
                data.get('unit_of_measure', 'HOUR'),
                data.get('min_warning_threshold'), data.get('max_warning_threshold'),
                data.get('min_critical_threshold'), data.get('max_critical_threshold'),
                data.get('reading_source', 'MANUAL'),
                1 if data.get('is_active') else 0
            ))
            db.commit()

            log_audit('maintenance_counter', cursor.lastrowid, 'CREATE', session.get('user_id'))
            flash(f'Counter {counter_code} created successfully.', 'success')
            return redirect(url_for('maintenance.equipment_counters_list'))

        equipment = db.execute("SELECT id, asset_code, name FROM assets ORDER BY asset_code").fetchall()
        return render_template('maintenance/counter_form.html', counter=None, equipment=equipment)
    finally:
        db.close()


@maintenance_bp.route('/counters/<int:counter_id>/reading', methods=['POST'])
@require_login
def counter_reading_add(counter_id):
    """Add counter reading."""
    db = get_db()
    try:
        data = request.form
        cursor = db.execute("""
            INSERT INTO counter_readings (counter_id, reading_value, reading_date, reading_type)
            VALUES (?, ?, ?, ?)
        """, (counter_id, data.get('reading_value'), data.get('reading_date'), data.get('reading_type', 'MANUAL')))
        db.commit()

        # Update current value on counter
        db.execute("""
            UPDATE maintenance_counters SET
            current_value = ?, counter_reading_date = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (data.get('reading_value'), data.get('reading_date'), counter_id))
        db.commit()

        log_audit('counter_reading', cursor.lastrowid, 'CREATE', session.get('user_id'))
        flash('Counter reading recorded.', 'success')
        return redirect(url_for('maintenance.counter_detail', counter_id=counter_id))
    finally:
        db.close()


# =============================================================================
# ENHANCED EAM/PM ROUTES - CONDITION INDICATORS
# =============================================================================

@maintenance_bp.route('/condition-indicators')
@require_login
def condition_indicators_list():
    """List all condition indicators."""
    db = get_db()
    try:
        indicators = db.execute("""
            SELECT ci.*, a.asset_code, a.name as equipment_name
            FROM condition_indicators ci
            JOIN assets a ON ci.equipment_id = a.id
            ORDER BY ci.indicator_code
        """).fetchall()

        return render_template('maintenance/condition_indicators_list.html', indicators=indicators)
    finally:
        db.close()


@maintenance_bp.route('/condition-indicators/new', methods=['GET', 'POST'])
@require_login
def condition_indicator_new():
    """Create new condition indicator."""
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.form
            indicator_code = data.get('indicator_code')
            if not indicator_code:
                seq = db.execute("SELECT COUNT(*) as cnt FROM condition_indicators").fetchone()['cnt'] + 1
                indicator_code = f"IND-{seq:05d}"

            cursor = db.execute("""
                INSERT INTO condition_indicators
                (indicator_code, equipment_id, indicator_name, indicator_type, unit,
                 normal_min, normal_max, warning_min, warning_max,
                 critical_min, critical_max, calculation_method,
                 reading_interval_minutes, data_retention_days, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                indicator_code, data.get('equipment_id'),
                data.get('indicator_name'), data.get('indicator_type', 'VIBRATION'),
                data.get('unit'), data.get('normal_min'), data.get('normal_max'),
                data.get('warning_min'), data.get('warning_max'),
                data.get('critical_min'), data.get('critical_max'),
                data.get('calculation_method'),
                data.get('reading_interval_minutes', 60),
                data.get('data_retention_days', 365),
                1 if data.get('is_active') else 0
            ))
            db.commit()

            log_audit('condition_indicator', cursor.lastrowid, 'CREATE', session.get('user_id'))
            flash(f'Condition indicator {indicator_code} created successfully.', 'success')
            return redirect(url_for('maintenance.condition_indicators_list'))

        equipment = db.execute("SELECT id, asset_code, name FROM assets ORDER BY asset_code").fetchall()
        return render_template('maintenance/condition_indicator_form.html', indicator=None, equipment=equipment)
    finally:
        db.close()


# =============================================================================
# ENHANCED EAM/PM ROUTES - SKILL CATALOG
# =============================================================================

@maintenance_bp.route('/skill-catalog')
@require_login
def skill_catalog_list():
    """List all skills in catalog."""
    db = get_db()
    try:
        skills = db.execute("SELECT * FROM skill_catalog ORDER BY skill_code").fetchall()
        return render_template('maintenance/skill_catalog_list.html', skills=skills)
    finally:
        db.close()


@maintenance_bp.route('/skill-catalog/new', methods=['GET', 'POST'])
@require_login
def skill_catalog_new():
    """Add new skill to catalog."""
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.form
            skill_code = data.get('skill_code')
            if not skill_code:
                seq = db.execute("SELECT COUNT(*) as cnt FROM skill_catalog").fetchone()['cnt'] + 1
                skill_code = f"SKILL-{seq:04d}"

            cursor = db.execute("""
                INSERT INTO skill_catalog
                (skill_code, skill_name, skill_category, description,
                 certification_required, validity_months, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                skill_code, data.get('skill_name'), data.get('skill_category'),
                data.get('description'),
                1 if data.get('certification_required') else 0,
                data.get('validity_months'), 1 if data.get('is_active') else 0
            ))
            db.commit()

            flash(f'Skill {skill_code} added to catalog.', 'success')
            return redirect(url_for('maintenance.skill_catalog_list'))

        return render_template('maintenance/skill_form.html', skill=None)
    finally:
        db.close()


# =============================================================================
# ENHANCED EAM/PM ROUTES - SHIFT PLANNING
# =============================================================================

@maintenance_bp.route('/shift-planning')
@require_login
def shift_planning():
    """Shift planning view."""
    db = get_db()
    try:
        work_centers = db.execute("SELECT id, work_center_code, work_center_name FROM work_centers WHERE is_active = 1 ORDER BY work_center_code").fetchall()

        start_date = request.args.get('start_date', datetime.now().strftime('%Y-%m-%d'))
        end_date = request.args.get('end_date', (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'))
        wc_id = request.args.get('work_center_id', type=int)

        shift_assignments = []
        if wc_id:
            shift_assignments = db.execute("""
                SELECT ts.*, e.first_name || ' ' || e.last_name as technician_name,
                       e.employee_code, wcs.shift_name, wcs.start_time, wcs.end_time
                FROM technician_shifts ts
                JOIN hr_employees e ON ts.technician_id = e.id
                LEFT JOIN work_center_shifts wcs ON ts.shift_definition_id = wcs.id
                WHERE ts.work_center_id = ? AND ts.shift_date BETWEEN ? AND ?
                ORDER BY ts.shift_date, e.first_name
            """, (wc_id, start_date, end_date)).fetchall()
        else:
            shift_assignments = db.execute("""
                SELECT ts.*, e.first_name || ' ' || e.last_name as technician_name,
                       e.employee_code, wcs.shift_name, wcs.start_time, wcs.end_time,
                       wc.work_center_name
                FROM technician_shifts ts
                JOIN hr_employees e ON ts.technician_id = e.id
                LEFT JOIN work_center_shifts wcs ON ts.shift_definition_id = wcs.id
                JOIN work_centers wc ON ts.work_center_id = wc.id
                WHERE ts.shift_date BETWEEN ? AND ?
                ORDER BY ts.shift_date, wc.work_center_code, e.first_name
            """, (start_date, end_date)).fetchall()

        return render_template('maintenance/shift_planning.html',
                             work_centers=work_centers,
                             shifts=shift_assignments,
                             start_date=start_date,
                             end_date=end_date,
                             selected_wc_id=wc_id)
    finally:
        db.close()


# =============================================================================
# ENHANCED EAM/PM ROUTES - SERVICE AGREEMENTS
# =============================================================================

@maintenance_bp.route('/service-agreements')
@require_login
def service_agreements_list():
    """List all service agreements."""
    db = get_db()
    try:
        agreements = db.execute("""
            SELECT sa.*, c.name as customer_name
            FROM service_agreements sa
            LEFT JOIN customers c ON sa.customer_id = c.id
            ORDER BY sa.agreement_number
        """).fetchall()

        return render_template('maintenance/service_agreements_list.html', agreements=agreements)
    finally:
        db.close()


@maintenance_bp.route('/service-agreements/<int:ag_id>')
@require_login
def service_agreement_detail(ag_id):
    """View service agreement details."""
    db = get_db()
    try:
        agreement = db.execute("""
            SELECT sa.*, c.name as customer_name, c.contact_person, c.email
            FROM service_agreements sa
            LEFT JOIN customers c ON sa.customer_id = c.id
            WHERE sa.id = ?
        """, (ag_id,)).fetchone()

        line_items = db.execute("""
            SELECT ali.*, a.asset_code, a.name as equipment_name
            FROM agreement_line_items ali
            LEFT JOIN assets a ON ali.equipment_id = a.id
            WHERE ali.agreement_id = ?
            ORDER BY ali.id
        """, (ag_id,)).fetchall()

        return render_template('maintenance/service_agreement_detail.html',
                             agreement=agreement,
                             line_items=line_items)
    finally:
        db.close()


@maintenance_bp.route('/service-agreements/new', methods=['GET', 'POST'])
@require_login
def service_agreement_new():
    """Create new service agreement."""
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.form
            agreement_number = data.get('agreement_number')
            if not agreement_number:
                seq = db.execute("SELECT COUNT(*) as cnt FROM service_agreements").fetchone()['cnt'] + 1
                agreement_number = f"SVC-{datetime.now().strftime('%Y')}-{seq:05d}"

            cursor = db.execute("""
                INSERT INTO service_agreements
                (agreement_number, customer_id, agreement_type, start_date, end_date,
                 response_time_hours, resolution_time_hours, availability_target,
                 contract_value, billing_frequency, payment_terms,
                 status, auto_renewal, contract_document_url, terms_conditions, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agreement_number, data.get('customer_id'),
                data.get('agreement_type', 'MAINTENANCE'),
                data.get('start_date'), data.get('end_date'),
                data.get('response_time_hours', 4),
                data.get('resolution_time_hours', 24),
                data.get('availability_target'),
                data.get('contract_value', 0),
                data.get('billing_frequency', 'MONTHLY'),
                data.get('payment_terms'),
                data.get('status', 'ACTIVE'),
                1 if data.get('auto_renewal') else 0,
                data.get('contract_document_url'),
                data.get('terms_conditions'), session.get('user_id')
            ))
            db.commit()

            log_audit('service_agreement', cursor.lastrowid, 'CREATE', session.get('user_id'))
            flash(f'Service agreement {agreement_number} created.', 'success')
            return redirect(url_for('maintenance.service_agreement_detail', ag_id=cursor.lastrowid))

        customers = db.execute("SELECT id, name FROM customers ORDER BY name").fetchall()
        return render_template('maintenance/service_agreement_form.html',
                             agreement=None, customers=customers)
    finally:
        db.close()


# =============================================================================
# ENHANCED EAM/PM ROUTES - WARRANTY MANAGEMENT
# =============================================================================

@maintenance_bp.route('/warranty')
@require_login
def warranty_list():
    """List all warranty records."""
    db = get_db()
    try:
        warranties = db.execute("""
            SELECT wr.*, a.asset_code, a.name as equipment_name
            FROM warranty_records wr
            JOIN assets a ON wr.equipment_id = a.id
            ORDER BY wr.warranty_number
        """).fetchall()

        return render_template('maintenance/warranty_list.html', warranties=warranties)
    finally:
        db.close()


@maintenance_bp.route('/warranty/<int:wr_id>')
@require_login
def warranty_detail(wr_id):
    """View warranty details."""
    db = get_db()
    try:
        warranty = db.execute("""
            SELECT wr.*, a.asset_code, a.name as equipment_name
            FROM warranty_records wr
            JOIN assets a ON wr.equipment_id = a.id
            WHERE wr.id = ?
        """, (wr_id,)).fetchone()

        claims = db.execute("""
            SELECT wc.*, mwo.work_order_number
            FROM warranty_claims wc
            LEFT JOIN maintenance_work_orders mwo ON wc.work_order_id = mwo.id
            WHERE wc.warranty_id = ?
            ORDER BY wc.claim_date DESC
        """, (wr_id,)).fetchall()

        return render_template('maintenance/warranty_detail.html', warranty=warranty, claims=claims)
    finally:
        db.close()


@maintenance_bp.route('/warranty/new', methods=['GET', 'POST'])
@require_login
def warranty_new():
    """Create new warranty record."""
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.form
            cursor = db.execute("""
                INSERT INTO warranty_records
                (equipment_id, warranty_type, start_date, end_date, warranty_provider,
                 warranty_number, coverage_scope, coverage_details,
                 maximum_claims, maximum_value, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('equipment_id'), data.get('warranty_type', 'MANUFACTURER'),
                data.get('start_date'), data.get('end_date'),
                data.get('warranty_provider'), data.get('warranty_number'),
                data.get('coverage_scope', 'FULL'), data.get('coverage_details'),
                data.get('maximum_claims'), data.get('maximum_value'),
                1 if data.get('is_active') else 0
            ))
            db.commit()

            log_audit('warranty_record', cursor.lastrowid, 'CREATE', session.get('user_id'))
            flash('Warranty record created.', 'success')
            return redirect(url_for('maintenance.warranty_list'))

        equipment = db.execute("SELECT id, asset_code, name FROM assets ORDER BY asset_code").fetchall()
        return render_template('maintenance/warranty_form.html', warranty=None, equipment=equipment)
    finally:
        db.close()


# =============================================================================
# ENHANCED EAM/PM ROUTES - NOTIFICATIONS & PROBLEMS
# =============================================================================

@maintenance_bp.route('/notifications')
@require_login
def notifications_list():
    """List all maintenance notifications."""
    db = get_db()
    try:
        notifications = db.execute("""
            SELECT mn.*, a.asset_code, a.name as equipment_name,
                   fl.location_code, fl.name as location_name
            FROM maintenance_notifications mn
            LEFT JOIN assets a ON mn.equipment_id = a.id
            LEFT JOIN functional_locations fl ON mn.functional_location_id = fl.id
            ORDER BY mn.notification_number DESC
            LIMIT 100
        """).fetchall()

        return render_template('maintenance/notifications_list.html', notifications=notifications)
    finally:
        db.close()


@maintenance_bp.route('/notifications/new', methods=['GET', 'POST'])
@require_login
def notification_new():
    """Create new maintenance notification."""
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.form
            notif_number = data.get('notification_number')
            if not notif_number:
                seq = db.execute("SELECT COUNT(*) as cnt FROM maintenance_notifications").fetchone()['cnt'] + 1
                notif_number = f"NOTIF-{datetime.now().strftime('%Y%m')}-{seq:05d}"

            cursor = db.execute("""
                INSERT INTO maintenance_notifications
                (notification_number, notification_type, priority, short_text, long_text,
                 equipment_id, functional_location_id, status,
                 damage_group, damage_code, cause_group, cause_code,
                 reported_by, reported_date, required_start_date, required_end_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                notif_number, data.get('notification_type', 'MALFUNCTION'),
                data.get('priority', 'MEDIUM'), data.get('short_text'),
                data.get('long_text'), data.get('equipment_id') or None,
                data.get('functional_location_id') or None,
                data.get('status', 'OPEN'),
                data.get('damage_group'), data.get('damage_code'),
                data.get('cause_group'), data.get('cause_code'),
                session.get('user_id'), datetime.now().strftime('%Y-%m-%d %H:%M'),
                data.get('required_start_date'), data.get('required_end_date')
            ))
            db.commit()

            log_audit('maintenance_notification', cursor.lastrowid, 'CREATE', session.get('user_id'))
            flash(f'Notification {notif_number} created.', 'success')
            return redirect(url_for('maintenance.notifications_list'))

        equipment = db.execute("SELECT id, asset_code, name FROM assets ORDER BY asset_code").fetchall()
        locations = db.execute("SELECT id, location_code, name FROM functional_locations ORDER BY location_code").fetchall()
        return render_template('maintenance/notification_form.html',
                             notification=None, equipment=equipment, locations=locations)
    finally:
        db.close()


@maintenance_bp.route('/problems')
@require_login
def problems_list():
    """List all problem records."""
    db = get_db()
    try:
        problems = db.execute("""
            SELECT pr.*, e.first_name || ' ' || e.last_name as assigned_to_name
            FROM problem_records pr
            LEFT JOIN hr_employees e ON pr.assigned_to = e.id
            ORDER BY pr.problem_number DESC
        """).fetchall()

        return render_template('maintenance/problems_list.html', problems=problems)
    finally:
        db.close()


@maintenance_bp.route('/problems/new', methods=['GET', 'POST'])
@require_login
def problem_new():
    """Create new problem record."""
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.form
            problem_number = data.get('problem_number')
            if not problem_number:
                seq = db.execute("SELECT COUNT(*) as cnt FROM problem_records").fetchone()['cnt'] + 1
                problem_number = f"PRB-{datetime.now().strftime('%Y')}-{seq:05d}"

            cursor = db.execute("""
                INSERT INTO problem_records
                (problem_number, title, description, priority, status,
                 problem_category, problem_type, root_cause_analysis,
                 corrective_action, preventive_action, assigned_to)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                problem_number, data.get('title'), data.get('description'),
                data.get('priority', 'MEDIUM'), data.get('status', 'OPEN'),
                data.get('problem_category'), data.get('problem_type'),
                data.get('root_cause_analysis'), data.get('corrective_action'),
                data.get('preventive_action'), data.get('assigned_to') or None
            ))
            db.commit()

            log_audit('problem_record', cursor.lastrowid, 'CREATE', session.get('user_id'))
            flash(f'Problem record {problem_number} created.', 'success')
            return redirect(url_for('maintenance.problems_list'))

        employees = db.execute("SELECT id, first_name, last_name FROM hr_employees ORDER BY first_name").fetchall()
        return render_template('maintenance/problem_form.html', problem=None, employees=employees)
    finally:
        db.close()


# =============================================================================
# ENHANCED EAM/PM ROUTES - IOT DEVICES & ALERTS
# =============================================================================

@maintenance_bp.route('/iot-devices')
@require_login
def iot_devices_list():
    """List all IoT devices."""
    db = get_db()
    try:
        devices = db.execute("""
            SELECT iot.*, a.asset_code, a.name as equipment_name,
                   fl.location_code, fl.name as location_name
            FROM iot_devices iot
            LEFT JOIN assets a ON iot.equipment_id = a.id
            LEFT JOIN functional_locations fl ON iot.location_id = fl.id
            ORDER BY iot.device_code
        """).fetchall()

        return render_template('maintenance/iot_devices_list.html', devices=devices)
    finally:
        db.close()


@maintenance_bp.route('/iot-devices/<int:device_id>')
@require_login
def iot_device_detail(device_id):
    """View IoT device details and telemetry."""
    db = get_db()
    try:
        device = db.execute("""
            SELECT iot.*, a.asset_code, a.name as equipment_name
            FROM iot_devices iot
            LEFT JOIN assets a ON iot.equipment_id = a.id
            WHERE iot.id = ?
        """, (device_id,)).fetchone()

        streams = db.execute("""
            SELECT * FROM iot_data_streams WHERE device_id = ? ORDER BY stream_name
        """, (device_id,)).fetchall()

        recent_data = db.execute("""
            SELECT idp.*, ids.stream_name, ids.data_type, ids.unit
            FROM iot_data_points idp
            JOIN iot_data_streams ids ON idp.stream_id = ids.id
            WHERE ids.device_id = ?
            ORDER BY idp.timestamp DESC LIMIT 100
        """, (device_id,)).fetchall()

        return render_template('maintenance/iot_device_detail.html',
                             device=device, streams=streams, recent_data=recent_data)
    finally:
        db.close()


@maintenance_bp.route('/iot-devices/new', methods=['GET', 'POST'])
@require_login
def iot_device_new():
    """Register new IoT device."""
    db = get_db()
    try:
        if request.method == 'POST':
            data = request.form
            device_code = data.get('device_code')
            if not device_code:
                seq = db.execute("SELECT COUNT(*) as cnt FROM iot_devices").fetchone()['cnt'] + 1
                device_code = f"IOT-{seq:06d}"

            cursor = db.execute("""
                INSERT INTO iot_devices
                (device_code, device_type, manufacturer, model, serial_number,
                 protocol, endpoint_url, auth_type, sampling_interval_seconds,
                 data_format, is_active, equipment_id, location_id,
                 latitude, longitude, installed_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                device_code, data.get('device_type', 'SENSOR'),
                data.get('manufacturer'), data.get('model'), data.get('serial_number'),
                data.get('protocol', 'MQTT'), data.get('endpoint_url'),
                data.get('auth_type'), data.get('sampling_interval_seconds', 60),
                data.get('data_format', 'JSON'),
                1 if data.get('is_active') else 0,
                data.get('equipment_id') or None, data.get('location_id') or None,
                data.get('latitude'), data.get('longitude'),
                data.get('installed_date')
            ))
            db.commit()

            log_audit('iot_device', cursor.lastrowid, 'CREATE', session.get('user_id'))
            flash(f'IoT device {device_code} registered.', 'success')
            return redirect(url_for('maintenance.iot_devices_list'))

        equipment = db.execute("SELECT id, asset_code, name FROM assets ORDER BY asset_code").fetchall()
        locations = db.execute("SELECT id, location_code, name FROM functional_locations ORDER BY location_code").fetchall()
        return render_template('maintenance/iot_device_form.html', device=None, equipment=equipment, locations=locations)
    finally:
        db.close()


@maintenance_bp.route('/iot-alerts')
@require_login
def iot_alerts_list():
    """List all IoT alerts."""
    db = get_db()
    try:
        alerts = db.execute("""
            SELECT ia.*, iar.rule_name, ids.stream_name, ids.data_type,
                   iot.device_code
            FROM iot_alerts ia
            JOIN iot_alert_rules iar ON ia.rule_id = iar.id
            JOIN iot_data_streams ids ON ia.stream_id = ids.id
            JOIN iot_devices iot ON ids.device_id = iot.id
            ORDER BY ia.triggered_at DESC
            LIMIT 100
        """).fetchall()

        return render_template('maintenance/iot_alerts_list.html', alerts=alerts)
    finally:
        db.close()


# =============================================================================
# ENHANCED EAM/PM ROUTES - COST PLANNING & SETTLEMENTS
# =============================================================================

@maintenance_bp.route('/cost-planning')
@require_login
def cost_planning():
    """Cost planning view for work orders."""
    db = get_db()
    try:
        work_orders = db.execute("""
            SELECT mwo.*, a.asset_code, a.name as equipment_name,
                   wocp.total_planned_cost, wocp.total_actual_cost
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            LEFT JOIN (
                SELECT work_order_id,
                       SUM(planned_total_cost) as total_planned_cost,
                       SUM(actual_total_cost) as total_actual_cost
                FROM work_order_cost_plan GROUP BY work_order_id
            ) wocp ON mwo.id = wocp.work_order_id
            WHERE mwo.status NOT IN ('Closed', 'Canceled')
            ORDER BY mwo.work_order_number
        """).fetchall()

        return render_template('maintenance/cost_planning.html', work_orders=work_orders)
    finally:
        db.close()


@maintenance_bp.route('/settlements')
@require_login
def settlements_list():
    """List all maintenance settlements."""
    db = get_db()
    try:
        settlements = db.execute("""
            SELECT ms.*, mwo.work_order_number, sr.rule_name
            FROM maintenance_settlements ms
            JOIN maintenance_work_orders mwo ON ms.work_order_id = mwo.id
            LEFT JOIN settlement_rules sr ON ms.settlement_rule_id = sr.id
            ORDER BY ms.settlement_date DESC
            LIMIT 100
        """).fetchall()

        return render_template('maintenance/settlements_list.html', settlements=settlements)
    finally:
        db.close()


@maintenance_bp.route('/wip')
@require_login
def wip_view():
    """Work in Progress view."""
    db = get_db()
    try:
        wip_data = db.execute("""
            SELECT mw.*, mwo.work_order_number, mwo.work_order_type,
                   mce.element_name as cost_element_name
            FROM maintenance_wip mw
            JOIN maintenance_work_orders mwo ON mw.work_order_id = mwo.id
            LEFT JOIN maintenance_cost_elements mce ON mw.cost_element_id = mce.id
            ORDER BY mw.work_order_id
        """).fetchall()

        return render_template('maintenance/wip_view.html', wip_data=wip_data)
    finally:
        db.close()


# =============================================================================
# API HELPERS
# =============================================================================

@maintenance_bp.route('/api/technicians')
@require_login
def api_technicians():
    """Get technicians list (JSON API)."""
    db = get_db()
    try:
        technicians = db.execute("""
            SELECT id, first_name || ' ' || last_name as name, employee_code
            FROM hr_employees
            WHERE status = 'Active'
            ORDER BY first_name
        """).fetchall()

        return jsonify([dict(t) for t in technicians])
    finally:
        db.close()


@maintenance_bp.route('/api/assets/<int:asset_id>/maintenance-summary')
@require_login
def api_asset_maintenance_summary(asset_id):
    """Get maintenance summary for an asset (JSON API)."""
    db = get_db()
    try:
        total_orders = db.execute("SELECT COUNT(*) as cnt FROM maintenance_work_orders WHERE asset_id = ?",
                                 (asset_id,)).fetchone()['cnt']
        open_orders = db.execute("SELECT COUNT(*) as cnt FROM maintenance_work_orders WHERE asset_id = ? AND status NOT IN ('Completed', 'Closed', 'Canceled')",
                                 (asset_id,)).fetchone()['cnt']
        total_cost = db.execute("SELECT COALESCE(SUM(actual_cost), 0) as total FROM maintenance_work_orders WHERE asset_id = ?",
                                 (asset_id,)).fetchone()['total']
        total_downtime = db.execute("SELECT COALESCE(SUM(downtime_hours), 0) as total FROM maintenance_work_orders WHERE asset_id = ?",
                                   (asset_id,)).fetchone()['total']

        return jsonify({
            'total_work_orders': total_orders,
            'open_work_orders': open_orders,
            'total_maintenance_cost': float(total_cost),
            'total_downtime_hours': float(total_downtime)
        })
    finally:
        db.close()


@maintenance_bp.route('/api/dashboard-stats')
@require_login
def api_dashboard_stats():
    """Get dashboard statistics (JSON API)."""
    stats = get_maintenance_dashboard_stats()
    return jsonify(stats)
