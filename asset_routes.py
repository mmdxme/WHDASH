"""
Asset Management Routes
=======================
Comprehensive Flask routes for the Asset Management module.

Provides endpoints for:
- Asset Dashboard
- Asset Register (CRUD)
- Asset Categories
- Asset Acquisition/Capitalization
- Asset Transfer/Relocation
- Depreciation Management
- Maintenance Scheduling
- Maintenance Work Orders/Logs
- Asset Disposal
- Asset Reports
- Asset Settings
- Asset Audit Logs

Route Pattern: /assets/*
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session, send_file
from functools import wraps
import sqlite3
import os
import json
from datetime import datetime, timedelta
from openpyxl import Workbook
from io import BytesIO

from database import get_db, get_db_context, get_one, get_all, log_audit, create_notification
from permissions import user_has_permission, require_permission
from asset_models import (
    init_asset_tables, get_asset_setting, set_asset_setting,
    get_next_asset_code, get_next_work_order_number, get_next_disposal_number,
    get_next_depreciation_run_number, calculate_depreciation_for_asset,
    can_transition_status, ASSET_STATUSES, ASSET_STATUS_TRANSITIONS,
    calculate_straight_line_monthly
)

# Create blueprint
assets_bp = Blueprint('assets', __name__, url_prefix='/assets')


# =============================================================================
# ROUTE REGISTRATION
# =============================================================================

def register_asset_routes(app):
    """Register asset management routes with the Flask app."""
    init_asset_tables()
    app.register_blueprint(assets_bp)


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


def require_asset_permission(action):
    """Decorator factory for asset-specific permissions."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please login to access this page.', 'error')
                return redirect(url_for('login'))

            user_id = session['user_id']
            if not user_has_permission(user_id, 'assets', 'assets', action):
                if request.is_json:
                    return jsonify({'error': 'Permission denied'}), 403
                flash(f"You don't have permission to {action} assets.", 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# =============================================================================
# ASSET DASHBOARD
# =============================================================================

@assets_bp.route('/')
@assets_bp.route('/dashboard')
@require_login
@require_asset_permission('view')
def dashboard():
    """Asset Management Dashboard."""
    user_id = session.get('user_id')
    user_role = session.get('role_name', '')

    db = get_db()
    try:
        # Get dashboard statistics
        stats = {
            'total_assets': 0,
            'total_cost': 0,
            'total_accumulated_depr': 0,
            'total_net_book_value': 0,
            'active_assets': 0,
            'under_maintenance': 0,
            'pending_disposal': 0,
            'disposed_assets': 0,
        }

        # Total assets and values
        result = db.execute("""
            SELECT
                COUNT(*) as total,
                SUM(acquisition_cost) as total_cost,
                SUM(accumulated_depreciation) as total_accum,
                SUM(net_book_value) as total_nbv
            FROM assets
            WHERE status NOT IN ('Disposed', 'Retired')
        """).fetchone()
        if result:
            stats['total_assets'] = result['total'] or 0
            stats['total_cost'] = result['total_cost'] or 0
            stats['total_accumulated_depr'] = result['total_accum'] or 0
            stats['total_net_book_value'] = result['total_nbv'] or 0

        # By status
        status_counts = db.execute("""
            SELECT status, COUNT(*) as cnt
            FROM assets
            GROUP BY status
        """).fetchall()
        for row in status_counts:
            if row['status'] == 'Active':
                stats['active_assets'] = row['cnt']
            elif row['status'] == 'Under Maintenance':
                stats['under_maintenance'] = row['cnt']
            elif row['status'] == 'Pending Disposal':
                stats['pending_disposal'] = row['cnt']
            elif row['status'] == 'Disposed':
                stats['disposed_assets'] = row['cnt']

        # Assets by category
        by_category = db.execute("""
            SELECT
                COALESCE(ac.name, 'Uncategorized') as category_name,
                COUNT(a.id) as asset_count,
                SUM(a.acquisition_cost) as total_cost
            FROM assets a
            LEFT JOIN asset_categories ac ON a.category_id = ac.id
            WHERE a.status NOT IN ('Disposed', 'Retired')
            GROUP BY ac.name
            ORDER BY total_cost DESC
            LIMIT 10
        """).fetchall()

        # Recent acquisitions
        recent_acquisitions = db.execute("""
            SELECT a.*, ac.name as category_name
            FROM assets a
            LEFT JOIN asset_categories ac ON a.category_id = ac.id
            WHERE a.status NOT IN ('Disposed', 'Retired')
            ORDER BY a.created_at DESC
            LIMIT 10
        """).fetchall()

        # Upcoming maintenance
        upcoming_maintenance = db.execute("""
            SELECT
                ms.id,
                ms.next_due_date,
                ms.schedule_name,
                ms.priority,
                a.asset_code,
                a.name as asset_name,
                mt.name as maintenance_type
            FROM maintenance_schedules ms
            JOIN assets a ON ms.asset_id = a.id
            JOIN maintenance_types mt ON ms.maintenance_type_id = mt.id
            WHERE ms.is_active = 1 AND ms.next_due_date <= date('now', '+30 days')
            ORDER BY ms.next_due_date ASC
            LIMIT 10
        """).fetchall()

        # Overdue maintenance
        overdue_maintenance = db.execute("""
            SELECT
                ms.id,
                ms.next_due_date,
                ms.schedule_name,
                ms.priority,
                a.asset_code,
                a.name as asset_name,
                mt.name as maintenance_type
            FROM maintenance_schedules ms
            JOIN assets a ON ms.asset_id = a.id
            JOIN maintenance_types mt ON ms.maintenance_type_id = mt.id
            WHERE ms.is_active = 1 AND ms.next_due_date < date('now')
            ORDER BY ms.next_due_date ASC
            LIMIT 10
        """).fetchall()

        # Maintenance costs this month
        maint_costs = db.execute("""
            SELECT
                SUM(mc.amount) as total_cost
            FROM maintenance_cost_entries mc
            WHERE strftime('%Y-%m', mc.cost_date) = strftime('%Y-%m', 'now')
        """).fetchone()
        stats['maintenance_cost_month'] = maint_costs['total_cost'] or 0

        # Pending disposal requests
        pending_disposals = db.execute("""
            SELECT COUNT(*) as cnt
            FROM disposal_requests
            WHERE status = 'Pending Approval'
        """).fetchone()
        stats['pending_disposal_requests'] = pending_disposals['cnt'] or 0

        return render_template('assets/dashboard.html',
                             stats=stats,
                             by_category=by_category,
                             recent_acquisitions=recent_acquisitions,
                             upcoming_maintenance=upcoming_maintenance,
                             overdue_maintenance=overdue_maintenance)

    finally:
        db.close()


# =============================================================================
# ASSET REGISTER - LIST VIEW
# =============================================================================

@assets_bp.route('/register')
@require_login
@require_asset_permission('view')
def register():
    """Asset Register - List all assets."""
    user_id = session.get('user_id')

    # Get filter parameters
    search = request.args.get('search', '')
    status_filter = request.args.get('status', '')
    category_filter = request.args.get('category', '')
    company_filter = request.args.get('company', '')
    department_filter = request.args.get('department', '')
    page = int(request.args.get('page', 1))
    per_page = 50

    db = get_db()
    try:
        # Build query with filters
        query = """
            SELECT a.*,
                   ac.name as category_name,
                   c.name as company_name,
                   d.name as department_name,
                   e.first_name || ' ' || e.last_name as custodian_name
            FROM assets a
            LEFT JOIN asset_categories ac ON a.category_id = ac.id
            LEFT JOIN companies c ON a.company_id = c.id
            LEFT JOIN hr_departments d ON a.department_id = d.id
            LEFT JOIN hr_employees e ON a.custodian_id = e.id
            WHERE 1=1
        """
        params = []

        if search:
            query += " AND (a.asset_code LIKE ? OR a.name LIKE ? OR a.serial_number LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])

        if status_filter:
            query += " AND a.status = ?"
            params.append(status_filter)

        if category_filter:
            query += " AND a.category_id = ?"
            params.append(category_filter)

        if company_filter:
            query += " AND a.company_id = ?"
            params.append(company_filter)

        if department_filter:
            query += " AND a.department_id = ?"
            params.append(department_filter)

        query += " ORDER BY a.created_at DESC"

        # Count total
        count_query = query.replace('a.*,', 'COUNT(*) as cnt ')
        count_result = db.execute(count_query, params).fetchone()
        total_count = count_result['cnt'] if count_result else 0

        # Add pagination
        offset = (page - 1) * per_page
        query += f" LIMIT {per_page} OFFSET {offset}"

        assets = db.execute(query, params).fetchall()

        # Get filter options for dropdowns
        categories = db.execute("SELECT id, name, code FROM asset_categories WHERE is_active = 1 ORDER BY name").fetchall()
        companies = db.execute("SELECT id, name FROM companies ORDER BY name").fetchall()
        departments = db.execute("SELECT id, name FROM hr_departments ORDER BY name").fetchall()

        return render_template('assets/register.html',
                             assets=assets,
                             categories=categories,
                             companies=companies,
                             departments=departments,
                             statuses=ASSET_STATUSES,
                             total_count=total_count,
                             page=page,
                             per_page=per_page,
                             search=search,
                             status_filter=status_filter,
                             category_filter=category_filter,
                             company_filter=company_filter,
                             department_filter=department_filter)

    finally:
        db.close()


# =============================================================================
# ASSET REGISTER - CRUD OPERATIONS
# =============================================================================

@assets_bp.route('/new', methods=['GET', 'POST'])
@require_login
@require_asset_permission('create')
def asset_new():
    """Create new asset."""
    user_id = session.get('user_id')
    db = get_db()

    try:
        if request.method == 'POST':
            # Get form data
            data = request.form

            # Generate asset code
            asset_code = get_next_asset_code()

            # Parse dates
            acquisition_date = data.get('acquisition_date') or None
            capitalization_date = data.get('capitalization_date') or None
            in_service_date = data.get('in_service_date') or None
            depreciation_start_date = data.get('depreciation_start_date') or in_service_date
            warranty_expiry = data.get('warranty_expiry_date') or None

            # Calculate salvage
            salvage_percent = float(data.get('salvage_percent', 0))
            acquisition_cost = float(data.get('acquisition_cost', 0))
            salvage_value = acquisition_cost * (salvage_percent / 100)

            # Insert asset
            cursor = db.execute("""
                INSERT INTO assets (
                    asset_code, name, description, category_id, asset_type,
                    serial_number, brand, model, manufacturer, tag_number,
                    acquisition_date, capitalization_date, in_service_date,
                    acquisition_cost, additional_capitalization, supplier_id,
                    purchase_order_number, invoice_number, warranty_expiry_date,
                    depreciation_method_id, useful_life_years, salvage_value, salvage_percent,
                    depreciation_start_date, company_id, branch_id, warehouse_id,
                    location, department_id, cost_center, custodian_id,
                    status, condition_rating, notes, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                asset_code,
                data.get('name'),
                data.get('description'),
                data.get('category_id') or None,
                data.get('asset_type', 'Tangible'),
                data.get('serial_number'),
                data.get('brand'),
                data.get('model'),
                data.get('manufacturer'),
                data.get('tag_number'),
                acquisition_date,
                capitalization_date,
                in_service_date,
                acquisition_cost,
                float(data.get('additional_capitalization', 0)),
                data.get('supplier_id') or None,
                data.get('purchase_order_number'),
                data.get('invoice_number'),
                warranty_expiry,
                data.get('depreciation_method_id') or None,
                data.get('useful_life_years') or None,
                salvage_value,
                salvage_percent,
                depreciation_start_date,
                data.get('company_id') or None,
                data.get('branch_id') or None,
                data.get('warehouse_id') or None,
                data.get('location'),
                data.get('department_id') or None,
                data.get('cost_center'),
                data.get('custodian_id') or None,
                'Draft',
                data.get('condition_rating', 'Good'),
                data.get('notes'),
                user_id
            ))
            db.commit()
            asset_id = cursor.lastrowid

            # Log audit
            log_audit('asset', asset_id, 'CREATE', user_id, notes=f'Asset {asset_code} created')

            # Create acquisition record if cost > 0
            if acquisition_cost > 0:
                db.execute("""
                    INSERT INTO asset_acquisitions (
                        asset_id, acquisition_type, acquisition_date, capitalization_date,
                        supplier_id, invoice_number, invoice_amount, total_capitalized_cost,
                        approval_status, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    asset_id,
                    'Purchase',
                    acquisition_date,
                    capitalization_date,
                    data.get('supplier_id') or None,
                    data.get('invoice_number'),
                    acquisition_cost,
                    acquisition_cost,
                    'Pending',
                    user_id
                ))
                db.commit()

            flash(f'Asset {asset_code} created successfully.', 'success')
            return redirect(url_for('assets.asset_detail', asset_id=asset_id))

        # GET request - show form
        categories = db.execute("SELECT id, name, code FROM asset_categories WHERE is_active = 1 ORDER BY name").fetchall()
        companies = db.execute("SELECT id, name FROM companies ORDER BY name").fetchall()
        departments = db.execute("SELECT id, name FROM hr_departments ORDER BY name").fetchall()
        suppliers = db.execute("SELECT id, name FROM suppliers ORDER BY name").fetchall()
        depreciation_methods = db.execute("SELECT id, name, code FROM depreciation_methods WHERE is_active = 1").fetchall()

        # Get category defaults for useful life
        category_defaults = {}
        for cat in categories:
            defaults = db.execute("""
                SELECT dm.code, ac.default_useful_life_years, ac.default_salvage_percent
                FROM asset_categories ac
                JOIN depreciation_methods dm ON ac.depreciation_method_id = dm.id
                WHERE ac.id = ?
            """, (cat['id'],)).fetchone()
            if defaults:
                category_defaults[cat['id']] = dict(defaults)

        return render_template('assets/asset_form.html',
                             asset=None,
                             categories=categories,
                             companies=companies,
                             departments=departments,
                             suppliers=suppliers,
                             depreciation_methods=depreciation_methods,
                             category_defaults=category_defaults,
                             statuses=ASSET_STATUSES,
                             page_title='New Asset')

    finally:
        db.close()


@assets_bp.route('/<int:asset_id>')
@require_login
@require_asset_permission('view')
def asset_detail(asset_id):
    """View asset details."""
    user_id = session.get('user_id')
    db = get_db()

    try:
        # Get asset with joins
        asset = db.execute("""
            SELECT a.*,
                   ac.name as category_name, ac.code as category_code,
                   c.name as company_name,
                   d.name as department_name,
                   e.first_name || ' ' || e.last_name as custodian_name,
                   e.employee_code as custodian_code,
                   dm.name as depreciation_method_name,
                   dm.code as depreciation_method_code,
                   sup.name as supplier_name,
                   u.username as created_by_name
            FROM assets a
            LEFT JOIN asset_categories ac ON a.category_id = ac.id
            LEFT JOIN companies c ON a.company_id = c.id
            LEFT JOIN hr_departments d ON a.department_id = d.id
            LEFT JOIN hr_employees e ON a.custodian_id = e.id
            LEFT JOIN depreciation_methods dm ON a.depreciation_method_id = dm.id
            LEFT JOIN suppliers sup ON a.supplier_id = sup.id
            LEFT JOIN users u ON a.created_by = u.id
            WHERE a.id = ?
        """, (asset_id,)).fetchone()

        if not asset:
            flash('Asset not found.', 'error')
            return redirect(url_for('assets.register'))

        # Get depreciation profile
        depr_profile = db.execute("""
            SELECT * FROM asset_depreciation_profiles WHERE asset_id = ?
        """, (asset_id,)).fetchone()

        # Get depreciation history
        depr_history = db.execute("""
            SELECT de.*, u.username as posted_by_name
            FROM depreciation_entries de
            LEFT JOIN depreciation_runs dr ON de.run_id = dr.id
            LEFT JOIN users u ON dr.processed_by = u.id
            WHERE de.asset_id = ?
            ORDER BY de.period_year DESC, de.period_month DESC
            LIMIT 24
        """, (asset_id,)).fetchall()

        # Get transfer history
        transfer_history = db.execute("""
            SELECT * FROM asset_transfer_history
            WHERE asset_id = ?
            ORDER BY transfer_date DESC
        """, (asset_id,)).fetchall()

        # Get assignment history
        assignments = db.execute("""
            SELECT aa.*,
                   e.first_name || ' ' || e.last_name as assigned_to_name,
                   d.name as department_name
            FROM asset_assignments aa
            LEFT JOIN hr_employees e ON aa.assigned_to_id = e.id
            LEFT JOIN hr_departments d ON aa.department_id = d.id
            WHERE aa.asset_id = ?
            ORDER BY aa.effective_date DESC
        """, (asset_id,)).fetchall()

        # Get maintenance history
        maintenance_logs = db.execute("""
            SELECT mwl.*, mt.name as maintenance_type_name,
                   u.username as created_by_name
            FROM maintenance_work_logs mwl
            JOIN maintenance_types mt ON mwl.maintenance_type_id = mt.id
            LEFT JOIN users u ON mwl.created_by = u.id
            WHERE mwl.asset_id = ?
            ORDER BY mwl.work_date DESC
        """, (asset_id,)).fetchall()

        # Get maintenance schedules
        maint_schedules = db.execute("""
            SELECT ms.*, mt.name as maintenance_type_name
            FROM maintenance_schedules ms
            JOIN maintenance_types mt ON ms.maintenance_type_id = mt.id
            WHERE ms.asset_id = ? AND ms.is_active = 1
            ORDER BY ms.next_due_date ASC
        """, (asset_id,)).fetchall()

        # Get disposal history
        disposals = db.execute("""
            SELECT ad.*, u.username as created_by_name
            FROM asset_disposals ad
            LEFT JOIN users u ON ad.created_by = u.id
            WHERE ad.asset_id = ?
            ORDER BY ad.disposal_date DESC
        """, (asset_id,)).fetchall()

        # Get disposal requests
        disposal_requests = db.execute("""
            SELECT dr.*, u.username as created_by_name
            FROM disposal_requests dr
            LEFT JOIN users u ON dr.created_by = u.id
            WHERE dr.asset_id = ?
            ORDER BY dr.request_date DESC
        """, (asset_id,)).fetchall()

        # Get audit log
        audit_log = db.execute("""
            SELECT * FROM asset_audit_log
            WHERE asset_id = ?
            ORDER BY created_at DESC
            LIMIT 50
        """, (asset_id,)).fetchall()

        return render_template('assets/asset_detail.html',
                             asset=asset,
                             depr_profile=depr_profile,
                             depr_history=depr_history,
                             transfer_history=transfer_history,
                             assignments=assignments,
                             maintenance_logs=maintenance_logs,
                             maint_schedules=maint_schedules,
                             disposals=disposals,
                             disposal_requests=disposal_requests,
                             audit_log=audit_log)

    finally:
        db.close()


@assets_bp.route('/<int:asset_id>/edit', methods=['GET', 'POST'])
@require_login
@require_asset_permission('edit')
def asset_edit(asset_id):
    """Edit asset."""
    user_id = session.get('user_id')
    db = get_db()

    try:
        asset = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not asset:
            flash('Asset not found.', 'error')
            return redirect(url_for('assets.register'))

        if request.method == 'POST':
            data = request.form

            # Track changes for audit
            changes = []
            for key in ['name', 'description', 'category_id', 'serial_number', 'brand',
                       'model', 'location', 'department_id', 'cost_center', 'custodian_id',
                       'condition_rating', 'notes']:
                old_val = asset.get(key)
                new_val = data.get(key)
                if str(old_val) != str(new_val):
                    changes.append((key, old_val, new_val))

            # Parse dates
            depreciation_start_date = data.get('depreciation_start_date') or \
                                      asset['depreciation_start_date']
            salvage_percent = float(data.get('salvage_percent', 0))
            acquisition_cost = float(data.get('acquisition_cost', 0))
            salvage_value = acquisition_cost * (salvage_percent / 100)

            # Update asset
            db.execute("""
                UPDATE assets SET
                    name = ?,
                    description = ?,
                    category_id = ?,
                    serial_number = ?,
                    brand = ?,
                    model = ?,
                    tag_number = ?,
                    depreciation_method_id = ?,
                    useful_life_years = ?,
                    salvage_value = ?,
                    salvage_percent = ?,
                    depreciation_start_date = ?,
                    company_id = ?,
                    branch_id = ?,
                    warehouse_id = ?,
                    location = ?,
                    department_id = ?,
                    cost_center = ?,
                    custodian_id = ?,
                    condition_rating = ?,
                    notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                data.get('name'),
                data.get('description'),
                data.get('category_id') or None,
                data.get('serial_number'),
                data.get('brand'),
                data.get('model'),
                data.get('tag_number'),
                data.get('depreciation_method_id') or None,
                data.get('useful_life_years') or None,
                salvage_value,
                salvage_percent,
                depreciation_start_date,
                data.get('company_id') or None,
                data.get('branch_id') or None,
                data.get('warehouse_id') or None,
                data.get('location'),
                data.get('department_id') or None,
                data.get('cost_center'),
                data.get('custodian_id') or None,
                data.get('condition_rating'),
                data.get('notes'),
                asset_id
            ))
            db.commit()

            # Log changes
            for field, old_val, new_val in changes:
                log_audit('asset', asset_id, 'UPDATE', user_id, field, old_val, new_val)

            flash(f'Asset {asset["asset_code"]} updated successfully.', 'success')
            return redirect(url_for('assets.asset_detail', asset_id=asset_id))

        # GET request
        categories = db.execute("SELECT id, name, code FROM asset_categories WHERE is_active = 1 ORDER BY name").fetchall()
        companies = db.execute("SELECT id, name FROM companies ORDER BY name").fetchall()
        departments = db.execute("SELECT id, name FROM hr_departments ORDER BY name").fetchall()
        suppliers = db.execute("SELECT id, name FROM suppliers ORDER BY name").fetchall()
        depreciation_methods = db.execute("SELECT id, name, code FROM depreciation_methods WHERE is_active = 1").fetchall()

        return render_template('assets/asset_form.html',
                             asset=asset,
                             categories=categories,
                             companies=companies,
                             departments=departments,
                             suppliers=suppliers,
                             depreciation_methods=depreciation_methods,
                             statuses=ASSET_STATUSES,
                             page_title=f'Edit Asset {asset["asset_code"]}')

    finally:
        db.close()


@assets_bp.route('/<int:asset_id>/delete', methods=['POST'])
@require_login
@require_asset_permission('delete')
def asset_delete(asset_id):
    """Delete asset (soft delete - only allowed for Draft status)."""
    user_id = session.get('user_id')
    db = get_db()

    try:
        asset = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not asset:
            return jsonify({'error': 'Asset not found'}), 404

        if asset['status'] not in ['Draft', 'Inactive']:
            return jsonify({'error': 'Can only delete assets with Draft or Inactive status'}), 400

        # Delete related records
        db.execute("DELETE FROM asset_acquisitions WHERE asset_id = ?", (asset_id,))
        db.execute("DELETE FROM asset_assignments WHERE asset_id = ?", (asset_id,))
        db.execute("DELETE FROM asset_transfer_history WHERE asset_id = ?", (asset_id,))
        db.execute("DELETE FROM asset_depreciation_profiles WHERE asset_id = ?", (asset_id,))
        db.execute("DELETE FROM maintenance_schedules WHERE asset_id = ?", (asset_id,))
        db.execute("DELETE FROM maintenance_work_orders WHERE asset_id = ?", (asset_id,))
        db.execute("DELETE FROM maintenance_work_logs WHERE asset_id = ?", (asset_id,))
        db.execute("DELETE FROM disposal_requests WHERE asset_id = ?", (asset_id,))
        db.execute("DELETE FROM asset_disposals WHERE asset_id = ?", (asset_id,))
        db.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
        db.commit()

        log_audit('asset', asset_id, 'DELETE', user_id, notes=f'Asset {asset["asset_code"]} deleted')
        flash(f'Asset deleted successfully.', 'success')

        return jsonify({'success': True})

    finally:
        db.close()


# =============================================================================
# ASSET STATUS MANAGEMENT
# =============================================================================

@assets_bp.route('/<int:asset_id>/activate', methods=['POST'])
@require_login
@require_asset_permission('edit')
def asset_activate(asset_id):
    """Activate/Capitalize an asset."""
    user_id = session.get('user_id')
    db = get_db()

    try:
        asset = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not asset:
            return jsonify({'error': 'Asset not found'}), 404

        old_status = asset['status']
        if old_status not in ['Draft', 'Pending Approval']:
            return jsonify({'error': 'Can only activate Draft or Pending Approval assets'}), 400

        db.execute("""
            UPDATE assets SET
                status = 'Active',
                approved_by = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, asset_id))
        db.commit()

        log_audit('asset', asset_id, 'STATUS_CHANGE', user_id, 'status', old_status, 'Active')
        flash(f'Asset {asset["asset_code"]} activated successfully.', 'success')

        return jsonify({'success': True, 'new_status': 'Active'})

    finally:
        db.close()


@assets_bp.route('/<int:asset_id>/status', methods=['POST'])
@require_login
@require_asset_permission('edit')
def asset_change_status(asset_id):
    """Change asset status with validation."""
    user_id = session.get('user_id')
    data = request.get_json()

    new_status = data.get('status')
    if not new_status:
        return jsonify({'error': 'Status is required'}), 400

    db = get_db()
    try:
        asset = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not asset:
            return jsonify({'error': 'Asset not found'}), 404

        old_status = asset['status']

        if not can_transition_status(old_status, new_status):
            return jsonify({
                'error': f'Cannot transition from {old_status} to {new_status}',
                'allowed': ASSET_STATUS_TRANSITIONS.get(old_status, [])
            }), 400

        db.execute("UPDATE assets SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                   (new_status, asset_id))
        db.commit()

        log_audit('asset', asset_id, 'STATUS_CHANGE', user_id, 'status', old_status, new_status)
        flash(f'Asset status changed to {new_status}.', 'success')

        return jsonify({'success': True, 'old_status': old_status, 'new_status': new_status})

    finally:
        db.close()


# =============================================================================
# ASSET CATEGORIES
# =============================================================================

@assets_bp.route('/categories')
@require_login
@require_asset_permission('view')
def categories():
    """Asset Categories list."""
    db = get_db()
    try:
        categories = db.execute("""
            SELECT ac.*,
                   dm.name as depreciation_method_name,
                   pc.name as parent_name,
                   (SELECT COUNT(*) FROM assets WHERE category_id = ac.id) as asset_count
            FROM asset_categories ac
            LEFT JOIN depreciation_methods dm ON ac.depreciation_method_id = dm.id
            LEFT JOIN asset_categories pc ON ac.parent_id = pc.id
            ORDER BY ac.name
        """).fetchall()

        depreciation_methods = db.execute("SELECT id, name, code FROM depreciation_methods WHERE is_active = 1").fetchall()

        return render_template('assets/categories.html',
                             categories=categories,
                             depreciation_methods=depreciation_methods)

    finally:
        db.close()


@assets_bp.route('/categories/save', methods=['POST'])
@require_login
@require_asset_permission('edit')
def category_save():
    """Save asset category (create or update)."""
    user_id = session.get('user_id')
    data = request.get_json()

    db = get_db()
    try:
        category_id = data.get('id')
        name = data.get('name')
        code = data.get('code')
        parent_id = data.get('parent_id') or None
        depreciation_method_id = data.get('depreciation_method_id') or None
        useful_life = data.get('default_useful_life_years') or 5
        salvage_percent = data.get('default_salvage_percent') or 0
        description = data.get('description')

        if category_id:
            # Update existing
            db.execute("""
                UPDATE asset_categories SET
                    name = ?, code = ?, parent_id = ?,
                    depreciation_method_id = ?, default_useful_life_years = ?,
                    default_salvage_percent = ?, description = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (name, code, parent_id, depreciation_method_id, useful_life,
                  salvage_percent, description, category_id))
            db.commit()
            log_audit('asset_category', category_id, 'UPDATE', user_id)
            flash('Category updated successfully.', 'success')
        else:
            # Create new
            cursor = db.execute("""
                INSERT INTO asset_categories
                (name, code, parent_id, depreciation_method_id, default_useful_life_years,
                 default_salvage_percent, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, code, parent_id, depreciation_method_id, useful_life,
                  salvage_percent, description))
            db.commit()
            category_id = cursor.lastrowid
            log_audit('asset_category', category_id, 'CREATE', user_id)
            flash('Category created successfully.', 'success')

        return jsonify({'success': True, 'id': category_id})

    finally:
        db.close()


@assets_bp.route('/categories/delete/<int:category_id>', methods=['POST'])
@require_login
@require_asset_permission('delete')
def category_delete(category_id):
    """Delete asset category."""
    user_id = session.get('user_id')
    db = get_db()

    try:
        # Check for linked assets
        asset_count = db.execute(
            "SELECT COUNT(*) as cnt FROM assets WHERE category_id = ?",
            (category_id,)
        ).fetchone()['cnt']

        if asset_count > 0:
            return jsonify({'error': f'Cannot delete category with {asset_count} linked assets'}), 400

        # Check for child categories
        child_count = db.execute(
            "SELECT COUNT(*) as cnt FROM asset_categories WHERE parent_id = ?",
            (category_id,)
        ).fetchone()['cnt']

        if child_count > 0:
            return jsonify({'error': 'Cannot delete category with subcategories'}), 400

        db.execute("DELETE FROM asset_categories WHERE id = ?", (category_id,))
        db.commit()

        log_audit('asset_category', category_id, 'DELETE', user_id)
        flash('Category deleted successfully.', 'success')

        return jsonify({'success': True})

    finally:
        db.close()


# =============================================================================
# ASSET TRANSFERS
# =============================================================================

@assets_bp.route('/transfers')
@require_login
@require_asset_permission('view')
def transfers():
    """Asset Transfers list."""
    db = get_db()
    try:
        transfers = db.execute("""
            SELECT ath.*, a.asset_code, a.name as asset_name,
                   fc.name as from_company, tc.name as to_company,
                   fd.name as from_department, td.name as to_department,
                   fe.first_name || ' ' || fe.last_name as from_custodian,
                   te.first_name || ' ' || te.last_name as to_custodian
            FROM asset_transfer_history ath
            JOIN assets a ON ath.asset_id = a.id
            LEFT JOIN companies fc ON ath.from_company_id = fc.id
            LEFT JOIN companies tc ON ath.to_company_id = tc.id
            LEFT JOIN hr_departments fd ON ath.from_department_id = fd.id
            LEFT JOIN hr_departments td ON ath.to_department_id = td.id
            LEFT JOIN hr_employees fe ON ath.from_custodian_id = fe.id
            LEFT JOIN hr_employees te ON ath.to_custodian_id = te.id
            ORDER BY ath.transfer_date DESC
            LIMIT 100
        """).fetchall()

        return render_template('assets/transfers.html', transfers=transfers)

    finally:
        db.close()


@assets_bp.route('/<int:asset_id>/transfer', methods=['GET', 'POST'])
@require_login
@require_asset_permission('transfer')
def asset_transfer(asset_id):
    """Transfer asset to new location/department/custodian."""
    user_id = session.get('user_id')
    db = get_db()

    try:
        asset = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not asset:
            flash('Asset not found.', 'error')
            return redirect(url_for('assets.register'))

        if asset['status'] in ['Disposed', 'Pending Disposal']:
            flash('Cannot transfer disposed or pending disposal assets.', 'error')
            return redirect(url_for('assets.asset_detail', asset_id=asset_id))

        if request.method == 'POST':
            data = request.form

            # Parse transfer date
            transfer_date = data.get('transfer_date') or datetime.now().strftime('%Y-%m-%d')

            # Record transfer history
            db.execute("""
                INSERT INTO asset_transfer_history (
                    asset_id, transfer_type,
                    from_company_id, from_branch_id, from_warehouse_id, from_location,
                    from_department_id, from_custodian_id,
                    to_company_id, to_branch_id, to_warehouse_id, to_location,
                    to_department_id, to_custodian_id,
                    transfer_date, reason, notes, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                asset_id,
                data.get('transfer_type', 'Relocation'),
                asset['company_id'],
                asset['branch_id'],
                asset['warehouse_id'],
                asset['location'],
                asset['department_id'],
                asset['custodian_id'],
                data.get('to_company_id') or None,
                data.get('to_branch_id') or None,
                data.get('to_warehouse_id') or None,
                data.get('to_location'),
                data.get('to_department_id') or None,
                data.get('to_custodian_id') or None,
                transfer_date,
                data.get('reason'),
                data.get('notes'),
                user_id
            ))

            # Update asset current location
            db.execute("""
                UPDATE assets SET
                    company_id = ?,
                    branch_id = ?,
                    warehouse_id = ?,
                    location = ?,
                    department_id = ?,
                    custodian_id = ?,
                    status = 'Transferred',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                data.get('to_company_id') or asset['company_id'],
                data.get('to_branch_id') or asset['branch_id'],
                data.get('to_warehouse_id') or asset['warehouse_id'],
                data.get('to_location') or asset['location'],
                data.get('to_department_id') or asset['department_id'],
                data.get('to_custodian_id') or asset['custodian_id'],
                asset_id
            ))
            db.commit()

            log_audit('asset', asset_id, 'TRANSFER', user_id, notes=f'Transferred to {data.get("to_location")}')
            flash(f'Asset {asset["asset_code"]} transferred successfully.', 'success')

            return redirect(url_for('assets.asset_detail', asset_id=asset_id))

        # GET
        companies = db.execute("SELECT id, name FROM companies ORDER BY name").fetchall()
        departments = db.execute("SELECT id, name FROM hr_departments ORDER BY name").fetchall()
        employees = db.execute("""
            SELECT id, first_name, last_name, employee_code
            FROM hr_employees WHERE status = 'Active'
            ORDER BY first_name
        """).fetchall()

        return render_template('assets/transfer_form.html',
                             asset=asset,
                             companies=companies,
                             departments=departments,
                             employees=employees)

    finally:
        db.close()


# =============================================================================
# DEPRECIATION MANAGEMENT
# =============================================================================

@assets_bp.route('/depreciation')
@require_login
@require_asset_permission('view')
def depreciation():
    """Depreciation management dashboard."""
    db = get_db()
    try:
        # Get depreciation run summary
        runs = db.execute("""
            SELECT dr.*,
                   u.username as processed_by_name,
                   a.username as approved_by_name
            FROM depreciation_runs dr
            LEFT JOIN users u ON dr.processed_by = u.id
            LEFT JOIN users a ON dr.approved_by = a.id
            ORDER BY dr.run_date DESC
            LIMIT 24
        """).fetchall()

        # Get pending depreciation runs
        pending_runs = db.execute("""
            SELECT COUNT(*) as cnt FROM depreciation_runs WHERE status = 'Draft'
        """).fetchone()['cnt']

        # Summary stats
        summary = db.execute("""
            SELECT
                SUM(accumulated_depreciation) as total_accumulated,
                SUM(net_book_value) as total_nbv
            FROM assets
            WHERE status NOT IN ('Disposed', 'Retired')
        """).fetchone()

        return render_template('assets/depreciation.html',
                             runs=runs,
                             pending_runs=pending_runs,
                             summary=summary)

    finally:
        db.close()


@assets_bp.route('/depreciation/run', methods=['GET', 'POST'])
@require_login
@require_asset_permission('depreciation')
def depreciation_run():
    """Run depreciation for a period."""
    user_id = session.get('user_id')
    db = get_db()

    try:
        if request.method == 'POST':
            data = request.get_json()
            period_month = int(data.get('period_month', datetime.now().month))
            period_year = int(data.get('period_year', datetime.now().year))

            # Check if run already exists for this period
            existing = db.execute("""
                SELECT id FROM depreciation_runs
                WHERE period_month = ? AND period_year = ? AND status != 'Reversed'
            """, (period_month, period_year)).fetchone()

            if existing:
                return jsonify({'error': 'Depreciation already run for this period'}), 400

            # Generate run number
            run_number = get_next_depreciation_run_number()

            # Get all active assets with depreciation setup
            assets = db.execute("""
                SELECT a.*,
                       adp.monthly_depreciation, adp.accumulated_depreciation,
                       adp.net_book_value, adp.salvage_value,
                       adp.depreciation_start_date
                FROM assets a
                JOIN asset_depreciation_profiles adp ON a.id = adp.asset_id
                WHERE a.status IN ('Active', 'Under Maintenance')
                AND a.depreciation_status != 'Disposed'
                AND adp.is_active = 1
            """).fetchall()

            if not assets:
                return jsonify({'error': 'No assets to depreciate'}), 400

            total_depreciation = 0
            entries = []

            for asset in assets:
                # Calculate depreciation
                calc = calculate_depreciation_for_asset(asset['id'], period_month, period_year)

                if not calc.get('can_depreciate', False):
                    continue

                depr_amount = calc['period_depreciation']

                # Don't depreciate below salvage value
                new_nbv = calc['current_net_book_value'] - depr_amount
                if new_nbv < asset['salvage_value']:
                    depr_amount = calc['current_net_book_value'] - asset['salvage_value']

                if depr_amount <= 0:
                    continue

                new_accumulated = asset['accumulated_depreciation'] + depr_amount
                new_nbv = asset['acquisition_cost'] - new_accumulated

                entries.append({
                    'asset_id': asset['id'],
                    'asset_code': asset['asset_code'],
                    'asset_name': asset['name'],
                    'depreciation': depr_amount,
                    'accumulated': new_accumulated,
                    'nbv': new_nbv
                })

                total_depreciation += depr_amount

            if not entries:
                return jsonify({'error': 'No depreciation calculated'}), 400

            # Create run header
            cursor = db.execute("""
                INSERT INTO depreciation_runs
                (run_number, run_date, period_month, period_year, description,
                 status, total_assets, total_depreciation, total_accumulated,
                 total_net_book_value, processed_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_number,
                datetime.now().strftime('%Y-%m-%d'),
                period_month,
                period_year,
                f'Depreciation run for {period_month:02d}/{period_year}',
                'Draft',
                len(entries),
                total_depreciation,
                sum(e['accumulated'] for e in entries),
                sum(e['nbv'] for e in entries),
                user_id
            ))
            run_id = cursor.lastrowid

            # Create entries
            for entry in entries:
                db.execute("""
                    INSERT INTO depreciation_entries
                    (run_id, asset_id, asset_code, asset_name, period_month, period_year,
                     depreciation_amount, accumulated_depreciation, net_book_value)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    run_id,
                    entry['asset_id'],
                    entry['asset_code'],
                    entry['asset_name'],
                    period_month,
                    period_year,
                    entry['depreciation'],
                    entry['accumulated'],
                    entry['nbv']
                ))

                # Update asset depreciation
                db.execute("""
                    UPDATE assets SET
                        accumulated_depreciation = ?,
                        net_book_value = ?,
                        last_depreciation_date = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    entry['accumulated'],
                    entry['nbv'],
                    f'{period_year}-{period_month:02d}-01',
                    entry['asset_id']
                ))

                # Update depreciation profile
                db.execute("""
                    UPDATE asset_depreciation_profiles SET
                        accumulated_depreciation = ?,
                        net_book_value = ?,
                        last_depreciation_date = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE asset_id = ?
                """, (
                    entry['accumulated'],
                    entry['nbv'],
                    f'{period_year}-{period_month:02d}-01',
                    entry['asset_id']
                ))

            db.commit()

            log_audit('depreciation_run', run_id, 'CREATE', user_id,
                     notes=f'Depreciation run {run_number} for {period_month:02d}/{period_year}')

            return jsonify({
                'success': True,
                'run_id': run_id,
                'run_number': run_number,
                'total_assets': len(entries),
                'total_depreciation': total_depreciation
            })

        # GET - show depreciation run form
        return render_template('assets/depreciation_run.html')

    finally:
        db.close()


@assets_bp.route('/depreciation/run/<int:run_id>')
@require_login
@require_asset_permission('view')
def depreciation_run_detail(run_id):
    """View depreciation run details."""
    db = get_db()
    try:
        run = db.execute("""
            SELECT dr.*,
                   u.username as processed_by_name,
                   a.username as approved_by_name
            FROM depreciation_runs dr
            LEFT JOIN users u ON dr.processed_by = u.id
            LEFT JOIN users a ON dr.approved_by = a.id
            WHERE dr.id = ?
        """, (run_id,)).fetchone()

        if not run:
            flash('Depreciation run not found.', 'error')
            return redirect(url_for('assets.depreciation'))

        entries = db.execute("""
            SELECT de.*, a.name as asset_name, a.category_id,
                   ac.name as category_name
            FROM depreciation_entries de
            JOIN assets a ON de.asset_id = a.id
            LEFT JOIN asset_categories ac ON a.category_id = ac.id
            WHERE de.run_id = ?
            ORDER BY de.asset_code
        """, (run_id,)).fetchall()

        return render_template('assets/depreciation_run_detail.html',
                             run=run,
                             entries=entries)

    finally:
        db.close()


@assets_bp.route('/depreciation/run/<int:run_id>/post', methods=['POST'])
@require_login
@require_asset_permission('depreciation')
def depreciation_run_post(run_id):
    """Post/Approve a depreciation run."""
    user_id = session.get('user_id')
    db = get_db()

    try:
        run = db.execute("SELECT * FROM depreciation_runs WHERE id = ?", (run_id,)).fetchone()
        if not run:
            return jsonify({'error': 'Depreciation run not found'}), 404

        if run['status'] != 'Draft':
            return jsonify({'error': 'Can only post Draft runs'}), 400

        db.execute("""
            UPDATE depreciation_runs SET
                status = 'Posted',
                approved_by = ?,
                approved_at = CURRENT_TIMESTAMP,
                posted_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, run_id))
        db.commit()

        log_audit('depreciation_run', run_id, 'POST', user_id,
                 notes=f'Depreciation run {run["run_number"]} posted')

        return jsonify({'success': True})

    finally:
        db.close()


@assets_bp.route('/depreciation/run/<int:run_id>/reverse', methods=['POST'])
@require_login
@require_asset_permission('depreciation')
def depreciation_run_reverse(run_id):
    """Reverse a posted depreciation run."""
    user_id = session.get('user_id')
    db = get_db()

    try:
        run = db.execute("SELECT * FROM depreciation_runs WHERE id = ?", (run_id,)).fetchone()
        if not run:
            return jsonify({'error': 'Depreciation run not found'}), 404

        if run['status'] != 'Posted':
            return jsonify({'error': 'Can only reverse Posted runs'}), 400

        # Get entries
        entries = db.execute("SELECT * FROM depreciation_entries WHERE run_id = ?",
                           (run_id,)).fetchall()

        # Reverse each entry
        for entry in entries:
            # Get previous accumulated (before this entry)
            prev_accum = entry['accumulated_depreciation'] - entry['depreciation_amount']
            prev_nbv = entry['net_book_value'] + entry['depreciation_amount']

            # Update asset
            db.execute("""
                UPDATE assets SET
                    accumulated_depreciation = ?,
                    net_book_value = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (prev_accum, prev_nbv, entry['asset_id']))

            # Update profile
            db.execute("""
                UPDATE asset_depreciation_profiles SET
                    accumulated_depreciation = ?,
                    net_book_value = ?
                WHERE asset_id = ?
            """, (prev_accum, prev_nbv, entry['asset_id']))

        # Mark run as reversed
        db.execute("""
            UPDATE depreciation_runs SET status = 'Reversed' WHERE id = ?
        """, (run_id,))
        db.commit()

        log_audit('depreciation_run', run_id, 'REVERSE', user_id,
                 notes=f'Depreciation run {run["run_number"]} reversed')

        return jsonify({'success': True})

    finally:
        db.close()


# =============================================================================
# MAINTENANCE MANAGEMENT
# =============================================================================

@assets_bp.route('/maintenance')
@require_login
@require_asset_permission('view')
def maintenance():
    """Maintenance management dashboard."""
    db = get_db()
    try:
        # Get upcoming schedules
        upcoming = db.execute("""
            SELECT ms.*, a.asset_code, a.name as asset_name,
                   mt.name as maintenance_type,
                   e.first_name || ' ' || e.last_name as technician_name
            FROM maintenance_schedules ms
            JOIN assets a ON ms.asset_id = a.id
            JOIN maintenance_types mt ON ms.maintenance_type_id = mt.id
            LEFT JOIN hr_employees e ON ms.assigned_technician_id = e.id
            WHERE ms.is_active = 1
            AND ms.next_due_date <= date('now', '+30 days')
            ORDER BY ms.next_due_date ASC
        """).fetchall()

        # Get overdue
        overdue = db.execute("""
            SELECT ms.*, a.asset_code, a.name as asset_name,
                   mt.name as maintenance_type
            FROM maintenance_schedules ms
            JOIN assets a ON ms.asset_id = a.id
            JOIN maintenance_types mt ON ms.maintenance_type_id = mt.id
            WHERE ms.is_active = 1 AND ms.next_due_date < date('now')
            ORDER BY ms.next_due_date ASC
        """).fetchall()

        # Get open work orders
        work_orders = db.execute("""
            SELECT mwo.*, a.asset_code, a.name as asset_name,
                   mt.name as maintenance_type,
                   e.first_name || ' ' || e.last_name as technician_name
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            JOIN maintenance_types mt ON mwo.maintenance_type_id = mt.id
            LEFT JOIN hr_employees e ON mwo.assigned_technician_id = e.id
            WHERE mwo.status NOT IN ('Completed', 'Canceled', 'Closed')
            ORDER BY mwo.issue_date DESC
        """).fetchall()

        # Cost summary
        cost_summary = db.execute("""
            SELECT
                SUM(CASE WHEN strftime('%Y-%m', cost_date) = strftime('%Y-%m', 'now')
                    THEN amount ELSE 0 END) as month_cost,
                SUM(CASE WHEN strftime('%Y', cost_date) = strftime('%Y', 'now')
                    THEN amount ELSE 0 END) as year_cost
            FROM maintenance_cost_entries
        """).fetchone()

        return render_template('assets/maintenance.html',
                             upcoming=upcoming,
                             overdue=overdue,
                             work_orders=work_orders,
                             cost_summary=cost_summary)

    finally:
        db.close()


@assets_bp.route('/maintenance/schedules')
@require_login
@require_asset_permission('view')
def maintenance_schedules():
    """Maintenance schedules list."""
    db = get_db()
    try:
        schedules = db.execute("""
            SELECT ms.*, a.asset_code, a.name as asset_name,
                   mt.name as maintenance_type, mt.category,
                   e.first_name || ' ' || e.last_name as technician_name
            FROM maintenance_schedules ms
            JOIN assets a ON ms.asset_id = a.id
            JOIN maintenance_types mt ON ms.maintenance_type_id = mt.id
            LEFT JOIN hr_employees e ON ms.assigned_technician_id = e.id
            WHERE ms.is_active = 1
            ORDER BY ms.next_due_date ASC
        """).fetchall()

        assets = db.execute("""
            SELECT id, asset_code, name FROM assets
            WHERE status NOT IN ('Disposed', 'Retired')
            ORDER BY asset_code
        """).fetchall()

        maintenance_types = db.execute("SELECT * FROM maintenance_types WHERE is_active = 1").fetchall()

        return render_template('assets/maintenance_schedules.html',
                             schedules=schedules,
                             assets=assets,
                             maintenance_types=maintenance_types)

    finally:
        db.close()


@assets_bp.route('/maintenance/schedules/save', methods=['POST'])
@require_login
@require_asset_permission('edit')
def maintenance_schedule_save():
    """Save maintenance schedule."""
    user_id = session.get('user_id')
    data = request.get_json()

    db = get_db()
    try:
        schedule_id = data.get('id')
        asset_id = data.get('asset_id')
        maintenance_type_id = data.get('maintenance_type_id')
        frequency = data.get('frequency', 'Monthly')
        interval_days = int(data.get('interval_days', 30))
        next_due_date = data.get('next_due_date')
        priority = data.get('priority', 'Medium')
        notes = data.get('notes')

        if schedule_id:
            # Update
            db.execute("""
                UPDATE maintenance_schedules SET
                    maintenance_type_id = ?, frequency = ?, interval_days = ?,
                    next_due_date = ?, priority = ?, notes = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (maintenance_type_id, frequency, interval_days,
                  next_due_date, priority, notes, schedule_id))
            db.commit()
            log_audit('maintenance_schedule', schedule_id, 'UPDATE', user_id)
        else:
            # Create
            cursor = db.execute("""
                INSERT INTO maintenance_schedules
                (asset_id, maintenance_type_id, frequency, interval_days,
                 next_due_date, priority, notes, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (asset_id, maintenance_type_id, frequency, interval_days,
                  next_due_date, priority, notes, user_id))
            db.commit()
            schedule_id = cursor.lastrowid
            log_audit('maintenance_schedule', schedule_id, 'CREATE', user_id)

        return jsonify({'success': True, 'id': schedule_id})

    finally:
        db.close()


@assets_bp.route('/maintenance/schedules/<int:schedule_id>/delete', methods=['POST'])
@require_login
@require_asset_permission('delete')
def maintenance_schedule_delete(schedule_id):
    """Delete maintenance schedule."""
    user_id = session.get('user_id')
    db = get_db()

    try:
        db.execute("""
            UPDATE maintenance_schedules SET is_active = 0 WHERE id = ?
        """, (schedule_id,))
        db.commit()

        log_audit('maintenance_schedule', schedule_id, 'DELETE', user_id)
        return jsonify({'success': True})

    finally:
        db.close()


@assets_bp.route('/maintenance/work-orders')
@require_login
@require_asset_permission('view')
def maintenance_work_orders():
    """Maintenance work orders list."""
    db = get_db()
    try:
        work_orders = db.execute("""
            SELECT mwo.*, a.asset_code, a.name as asset_name,
                   mt.name as maintenance_type,
                   e.first_name || ' ' || e.last_name as technician_name,
                   v.name as vendor_name
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            JOIN maintenance_types mt ON mwo.maintenance_type_id = mt.id
            LEFT JOIN hr_employees e ON mwo.assigned_technician_id = e.id
            LEFT JOIN suppliers v ON mwo.assigned_vendor_id = v.id
            ORDER BY mwo.issue_date DESC
        """).fetchall()

        return render_template('assets/maintenance_work_orders.html',
                             work_orders=work_orders)

    finally:
        db.close()


@assets_bp.route('/maintenance/work-orders/new', methods=['GET', 'POST'])
@require_login
@require_asset_permission('create')
def maintenance_work_order_new():
    """Create new maintenance work order."""
    user_id = session.get('user_id')
    db = get_db()

    try:
        if request.method == 'POST':
            data = request.form
            wo_number = get_next_work_order_number()

            cursor = db.execute("""
                INSERT INTO maintenance_work_orders
                (work_order_number, asset_id, maintenance_type_id, work_order_type,
                 priority, status, issue_date, issue_description,
                 assigned_technician_id, assigned_vendor_id,
                 estimated_cost, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                wo_number,
                data.get('asset_id'),
                data.get('maintenance_type_id'),
                data.get('work_order_type', 'Corrective'),
                data.get('priority', 'Medium'),
                'Open',
                data.get('issue_date') or datetime.now().strftime('%Y-%m-%d'),
                data.get('issue_description'),
                data.get('assigned_technician_id') or None,
                data.get('assigned_vendor_id') or None,
                data.get('estimated_cost', 0),
                user_id
            ))
            db.commit()
            wo_id = cursor.lastrowid

            log_audit('maintenance_work_order', wo_id, 'CREATE', user_id,
                     notes=f'Work order {wo_number} created')
            flash(f'Work order {wo_number} created.', 'success')

            return redirect(url_for('assets.maintenance_work_order_detail', wo_id=wo_id))

        # GET
        assets = db.execute("""
            SELECT id, asset_code, name FROM assets
            WHERE status NOT IN ('Disposed', 'Retired')
            ORDER BY asset_code
        """).fetchall()
        maintenance_types = db.execute("SELECT * FROM maintenance_types WHERE is_active = 1").fetchall()
        employees = db.execute("SELECT id, first_name, last_name FROM hr_employees WHERE status = 'Active'").fetchall()
        vendors = db.execute("SELECT id, name FROM suppliers ORDER BY name").fetchall()

        return render_template('assets/work_order_form.html',
                             work_order=None,
                             assets=assets,
                             maintenance_types=maintenance_types,
                             employees=employees,
                             vendors=vendors)

    finally:
        db.close()


@assets_bp.route('/maintenance/work-orders/<int:wo_id>')
@require_login
@require_asset_permission('view')
def maintenance_work_order_detail(wo_id):
    """View maintenance work order detail."""
    db = get_db()
    try:
        work_order = db.execute("""
            SELECT mwo.*, a.asset_code, a.name as asset_name, a.serial_number,
                   mt.name as maintenance_type,
                   e.first_name || ' ' || e.last_name as technician_name,
                   v.name as vendor_name
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            JOIN maintenance_types mt ON mwo.maintenance_type_id = mt.id
            LEFT JOIN hr_employees e ON mwo.assigned_technician_id = e.id
            LEFT JOIN suppliers v ON mwo.assigned_vendor_id = v.id
            WHERE mwo.id = ?
        """, (wo_id,)).fetchone()

        if not work_order:
            flash('Work order not found.', 'error')
            return redirect(url_for('assets.maintenance_work_orders'))

        # Get work logs
        logs = db.execute("""
            SELECT mwl.*, e.first_name || ' ' || e.last_name as technician_name
            FROM maintenance_work_logs mwl
            LEFT JOIN hr_employees e ON mwl.technician_id = e.id
            WHERE mwl.work_order_id = ?
            ORDER BY mwl.work_date DESC
        """, (wo_id,)).fetchall()

        return render_template('assets/work_order_detail.html',
                             work_order=work_order,
                             logs=logs)

    finally:
        db.close()


@assets_bp.route('/maintenance/work-orders/<int:wo_id>/complete', methods=['POST'])
@require_login
@require_asset_permission('edit')
def maintenance_work_order_complete(wo_id):
    """Complete a maintenance work order."""
    user_id = session.get('user_id')
    data = request.get_json()

    db = get_db()
    try:
        work_order = db.execute("SELECT * FROM maintenance_work_orders WHERE id = ?",
                               (wo_id,)).fetchone()
        if not work_order:
            return jsonify({'error': 'Work order not found'}), 404

        actual_cost = float(data.get('actual_cost', 0))
        resolution = data.get('resolution_notes', '')
        downtime = float(data.get('downtime_hours', 0))

        # Update work order
        db.execute("""
            UPDATE maintenance_work_orders SET
                status = 'Completed',
                actual_end_date = CURRENT_TIMESTAMP,
                actual_cost = ?,
                downtime_hours = ?,
                resolution_notes = ?,
                completed_by = ?,
                completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (actual_cost, downtime, resolution, user_id, wo_id))

        # Create work log
        db.execute("""
            INSERT INTO maintenance_work_logs
            (work_order_id, asset_id, maintenance_type_id, work_date,
             technician_id, work_performed, action_taken,
             actual_cost, downtime_hours, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            wo_id,
            work_order['asset_id'],
            work_order['maintenance_type_id'],
            datetime.now().strftime('%Y-%m-%d'),
            work_order['assigned_technician_id'],
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
                work_order['asset_id'],
                wo_id,
                'Maintenance',
                datetime.now().strftime('%Y-%m-%d'),
                'Work order completion',
                actual_cost,
                user_id
            ))

        # Update asset status back to Active
        db.execute("""
            UPDATE assets SET status = 'Active', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (work_order['asset_id'],))

        # Update schedule if linked
        if work_order['schedule_id']:
            schedule = db.execute("SELECT * FROM maintenance_schedules WHERE id = ?",
                                 (work_order['schedule_id'],)).fetchone()
            if schedule:
                # Calculate next due date
                next_date = datetime.strptime(schedule['next_due_date'], '%Y-%m-%d')
                if schedule['frequency'] == 'Daily':
                    next_date += timedelta(days=1)
                elif schedule['frequency'] == 'Weekly':
                    next_date += timedelta(weeks=1)
                elif schedule['frequency'] == 'Monthly':
                    next_date += timedelta(days=30)
                elif schedule['frequency'] == 'Quarterly':
                    next_date += timedelta(days=90)
                elif schedule['frequency'] == 'Yearly':
                    next_date += timedelta(days=365)
                else:
                    next_date += timedelta(days=schedule['interval_days'])

                db.execute("""
                    UPDATE maintenance_schedules SET
                        last_performed_date = ?,
                        last_work_order_id = ?,
                        next_due_date = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (datetime.now().strftime('%Y-%m-%d'), wo_id,
                      next_date.strftime('%Y-%m-%d'), work_order['schedule_id']))

        db.commit()

        log_audit('maintenance_work_order', wo_id, 'COMPLETE', user_id)
        flash('Work order completed.', 'success')

        return jsonify({'success': True})

    finally:
        db.close()


@assets_bp.route('/maintenance/work-logs')
@require_login
@require_asset_permission('view')
def maintenance_work_logs():
    """Maintenance work logs list."""
    db = get_db()
    try:
        logs = db.execute("""
            SELECT mwl.*, a.asset_code, a.name as asset_name,
                   mt.name as maintenance_type,
                   e.first_name || ' ' || e.last_name as technician_name
            FROM maintenance_work_logs mwl
            JOIN assets a ON mwl.asset_id = a.id
            JOIN maintenance_types mt ON mwl.maintenance_type_id = mt.id
            LEFT JOIN hr_employees e ON mwl.technician_id = e.id
            ORDER BY mwl.work_date DESC
            LIMIT 100
        """).fetchall()

        return render_template('assets/maintenance_work_logs.html', logs=logs)

    finally:
        db.close()


@assets_bp.route('/maintenance/costs')
@require_login
@require_asset_permission('view')
def maintenance_costs():
    """Maintenance costs report."""
    db = get_db()
    try:
        # Get costs by asset
        by_asset = db.execute("""
            SELECT a.asset_code, a.name as asset_name,
                   SUM(mc.amount) as total_cost,
                   COUNT(*) as transaction_count
            FROM maintenance_cost_entries mc
            JOIN assets a ON mc.asset_id = a.id
            GROUP BY a.id
            ORDER BY total_cost DESC
            LIMIT 50
        """).fetchall()

        # Get costs by month
        by_month = db.execute("""
            SELECT strftime('%Y-%m', cost_date) as month,
                   SUM(amount) as total_cost
            FROM maintenance_cost_entries
            WHERE cost_date >= date('now', '-12 months')
            GROUP BY strftime('%Y-%m', cost_date)
            ORDER BY month DESC
        """).fetchall()

        # Total costs
        totals = db.execute("""
            SELECT
                SUM(CASE WHEN strftime('%Y', cost_date) = strftime('%Y', 'now')
                    THEN amount ELSE 0 END) as year_total,
                SUM(CASE WHEN strftime('%Y-%m', cost_date) = strftime('%Y-%m', 'now')
                    THEN amount ELSE 0 END) as month_total
            FROM maintenance_cost_entries
        """).fetchone()

        return render_template('assets/maintenance_costs.html',
                             by_asset=by_asset,
                             by_month=by_month,
                             totals=totals)

    finally:
        db.close()


# =============================================================================
# ASSET DISPOSAL
# =============================================================================

@assets_bp.route('/disposal')
@require_login
@require_asset_permission('view')
def disposal():
    """Asset disposal dashboard."""
    db = get_db()
    try:
        # Pending requests
        pending_requests = db.execute("""
            SELECT dr.*, a.asset_code, a.name as asset_name
            FROM disposal_requests dr
            JOIN assets a ON dr.asset_id = a.id
            WHERE dr.status = 'Pending Approval'
            ORDER BY dr.request_date DESC
        """).fetchall()

        # Recent disposals
        recent_disposals = db.execute("""
            SELECT ad.*, a.asset_code, a.name as asset_name
            FROM asset_disposals ad
            JOIN assets a ON ad.asset_id = a.id
            ORDER BY ad.disposal_date DESC
            LIMIT 20
        """).fetchall()

        return render_template('assets/disposal.html',
                             pending_requests=pending_requests,
                             recent_disposals=recent_disposals)

    finally:
        db.close()


@assets_bp.route('/disposal/request', methods=['GET', 'POST'])
@require_login
@require_asset_permission('create')
def disposal_request():
    """Create disposal request."""
    user_id = session.get('user_id')
    db = get_db()

    try:
        if request.method == 'POST':
            data = request.form
            asset_id = data.get('asset_id')

            # Get asset details
            asset = db.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
            if not asset:
                flash('Asset not found.', 'error')
                return redirect(url_for('assets.disposal'))

            request_number = get_next_disposal_number()

            cursor = db.execute("""
                INSERT INTO disposal_requests
                (request_number, asset_id, request_date, disposal_type,
                 reason_code, reason_description, estimated_proceeds,
                 net_book_value, gain_loss, status, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request_number,
                asset_id,
                data.get('request_date') or datetime.now().strftime('%Y-%m-%d'),
                data.get('disposal_type'),
                data.get('reason_code'),
                data.get('reason_description'),
                float(data.get('estimated_proceeds', 0)),
                asset['net_book_value'],
                float(data.get('estimated_proceeds', 0)) - asset['net_book_value'],
                'Pending Approval',
                user_id
            ))
            db.commit()
            request_id = cursor.lastrowid

            # Update asset status
            db.execute("""
                UPDATE assets SET status = 'Pending Disposal', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (asset_id,))

            log_audit('disposal_request', request_id, 'CREATE', user_id,
                     notes=f'Disposal request {request_number} for {asset["asset_code"]}')

            flash(f'Disposal request {request_number} created.', 'success')
            return redirect(url_for('assets.disposal_request_detail', request_id=request_id))

        # GET
        assets = db.execute("""
            SELECT id, asset_code, name, net_book_value, status
            FROM assets
            WHERE status IN ('Active', 'Pending Disposal')
            AND depreciation_status != 'Disposed'
            ORDER BY asset_code
        """).fetchall()

        return render_template('assets/disposal_request_form.html',
                             request=None,
                             assets=assets)

    finally:
        db.close()


@assets_bp.route('/disposal/request/<int:request_id>')
@require_login
@require_asset_permission('view')
def disposal_request_detail(request_id):
    """View disposal request detail."""
    db = get_db()
    try:
        disposal_req = db.execute("""
            SELECT dr.*, a.asset_code, a.name as asset_name, a.serial_number,
                   a.acquisition_cost, a.net_book_value,
                   u.username as created_by_name
            FROM disposal_requests dr
            JOIN assets a ON dr.asset_id = a.id
            LEFT JOIN users u ON dr.created_by = u.id
            WHERE dr.id = ?
        """, (request_id,)).fetchone()

        if not disposal_req:
            flash('Disposal request not found.', 'error')
            return redirect(url_for('assets.disposal'))

        return render_template('assets/disposal_request_detail.html',
                             request=disposal_req)

    finally:
        db.close()


@assets_bp.route('/disposal/request/<int:request_id>/approve', methods=['POST'])
@require_login
@require_asset_permission('edit')
def disposal_request_approve(request_id):
    """Approve disposal request."""
    user_id = session.get('user_id')
    db = get_db()

    try:
        request = db.execute("SELECT * FROM disposal_requests WHERE id = ?",
                            (request_id,)).fetchone()
        if not request:
            return jsonify({'error': 'Request not found'}), 404

        if request['status'] != 'Pending Approval':
            return jsonify({'error': 'Request already processed'}), 400

        # Update request status
        db.execute("""
            UPDATE disposal_requests SET
                status = 'Approved',
                approved_by = ?,
                approved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, request_id))

        log_audit('disposal_request', request_id, 'APPROVE', user_id)
        flash('Disposal request approved.', 'success')

        return jsonify({'success': True})

    finally:
        db.close()


@assets_bp.route('/disposal/request/<int:request_id>/reject', methods=['POST'])
@require_login
@require_asset_permission('edit')
def disposal_request_reject(request_id):
    """Reject disposal request."""
    user_id = session.get('user_id')
    data = request.get_json()
    reason = data.get('reason', '')

    db = get_db()
    try:
        request = db.execute("SELECT * FROM disposal_requests WHERE id = ?",
                            (request_id,)).fetchone()
        if not request:
            return jsonify({'error': 'Request not found'}), 404

        # Update request status
        db.execute("""
            UPDATE disposal_requests SET
                status = 'Rejected',
                rejection_reason = ?,
                approved_by = ?,
                approved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (reason, user_id, request_id))

        # Revert asset status
        db.execute("""
            UPDATE assets SET status = 'Active', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (request['asset_id'],))

        log_audit('disposal_request', request_id, 'REJECT', user_id, notes=reason)
        flash('Disposal request rejected.', 'success')

        return jsonify({'success': True})

    finally:
        db.close()


@assets_bp.route('/disposal/execute', methods=['POST'])
@require_login
@require_asset_permission('edit')
def disposal_execute():
    """Execute asset disposal."""
    user_id = session.get('user_id')
    data = request.get_json()

    request_id = data.get('request_id')
    disposal_date = data.get('disposal_date')
    proceeds = float(data.get('proceeds', 0))
    cost_of_disposal = float(data.get('cost_of_disposal', 0))
    buyer_name = data.get('buyer_name')
    notes = data.get('notes')

    db = get_db()
    try:
        disposal_req = db.execute("SELECT * FROM disposal_requests WHERE id = ?",
                                (request_id,)).fetchone()
        if not disposal_req:
            return jsonify({'error': 'Request not found'}), 404

        if disposal_req['status'] != 'Approved':
            return jsonify({'error': 'Request must be approved first'}), 400

        asset = db.execute("SELECT * FROM assets WHERE id = ?",
                          (disposal_req['asset_id'])).fetchone()

        disposal_number = get_next_disposal_number()
        gain_loss = proceeds - cost_of_disposal - asset['net_book_value']

        # Create disposal record
        cursor = db.execute("""
            INSERT INTO asset_disposals
            (disposal_number, request_id, asset_id, disposal_date, disposal_type,
             reason_code, proceeds, cost_of_disposal, net_proceeds,
             gain_loss, buyer_name, approval_status, approved_by, approved_at,
             notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            disposal_number,
            request_id,
            disposal_req['asset_id'],
            disposal_date,
            disposal_req['disposal_type'],
            disposal_req['reason_code'],
            proceeds,
            cost_of_disposal,
            proceeds - cost_of_disposal,
            gain_loss,
            buyer_name,
            'Approved',
            user_id,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            notes,
            user_id
        ))
        disposal_id = cursor.lastrowid

        # Update asset
        db.execute("""
            UPDATE assets SET
                status = 'Disposed',
                depreciation_status = 'Disposed',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (disposal_req['asset_id'],))

        # Update request
        db.execute("""
            UPDATE disposal_requests SET
                status = 'Completed'
            WHERE id = ?
        """, (request_id,))

        db.commit()

        log_audit('asset_disposal', disposal_id, 'CREATE', user_id,
                 notes=f'Asset {asset["asset_code"]} disposed via {disposal_number}')
        log_audit('asset', disposal_req['asset_id'], 'DISPOSE', user_id,
                 notes=f'Gain/Loss: {gain_loss}')

        flash(f'Asset disposed successfully. Gain/Loss: {gain_loss:,.2f}', 'success')

        return jsonify({
            'success': True,
            'disposal_id': disposal_id,
            'disposal_number': disposal_number,
            'gain_loss': gain_loss
        })

    finally:
        db.close()


# =============================================================================
# ASSET REPORTS
# =============================================================================

@assets_bp.route('/reports')
@require_login
@require_asset_permission('view')
def reports():
    """Asset Reports menu."""
    return render_template('assets/reports.html')


@assets_bp.route('/reports/register')
@require_login
@require_asset_permission('view')
def report_register():
    """Asset Register Report."""
    db = get_db()
    try:
        assets = db.execute("""
            SELECT a.*, ac.name as category_name, c.name as company_name,
                   d.name as department_name
            FROM assets a
            LEFT JOIN asset_categories ac ON a.category_id = ac.id
            LEFT JOIN companies c ON a.company_id = c.id
            LEFT JOIN hr_departments d ON a.department_id = d.id
            WHERE a.status NOT IN ('Disposed', 'Retired')
            ORDER BY a.asset_code
        """).fetchall()

        return render_template('assets/report_register.html', assets=assets)

    finally:
        db.close()


@assets_bp.route('/reports/depreciation')
@require_login
@require_asset_permission('view')
def report_depreciation():
    """Depreciation Report."""
    db = get_db()
    try:
        assets = db.execute("""
            SELECT a.asset_code, a.name, ac.name as category_name,
                   a.acquisition_cost, a.salvage_value,
                   a.useful_life_years, a.accumulated_depreciation,
                   a.net_book_value,
                   dm.name as depreciation_method
            FROM assets a
            LEFT JOIN asset_categories ac ON a.category_id = ac.id
            LEFT JOIN depreciation_methods dm ON a.depreciation_method_id = dm.id
            WHERE a.status NOT IN ('Disposed', 'Retired')
            ORDER BY a.asset_code
        """).fetchall()

        # Summary
        summary = db.execute("""
            SELECT
                SUM(acquisition_cost) as total_cost,
                SUM(accumulated_depreciation) as total_accumulated,
                SUM(net_book_value) as total_nbv
            FROM assets
            WHERE status NOT IN ('Disposed', 'Retired')
        """).fetchone()

        return render_template('assets/report_depreciation.html',
                             assets=assets,
                             summary=summary)

    finally:
        db.close()


@assets_bp.route('/reports/maintenance')
@require_login
@require_asset_permission('view')
def report_maintenance():
    """Maintenance Report."""
    db = get_db()
    try:
        logs = db.execute("""
            SELECT mwl.*, a.asset_code, a.name as asset_name,
                   mt.name as maintenance_type
            FROM maintenance_work_logs mwl
            JOIN assets a ON mwl.asset_id = a.id
            JOIN maintenance_types mt ON mwl.maintenance_type_id = mt.id
            ORDER BY mwl.work_date DESC
            LIMIT 200
        """).fetchall()

        # Summary by type
        by_type = db.execute("""
            SELECT mt.name, COUNT(*) as count, SUM(mwl.total_cost) as total_cost
            FROM maintenance_work_logs mwl
            JOIN maintenance_types mt ON mwl.maintenance_type_id = mt.id
            GROUP BY mt.id
        """).fetchall()

        return render_template('assets/report_maintenance.html',
                             logs=logs,
                             by_type=by_type)

    finally:
        db.close()


@assets_bp.route('/reports/disposal')
@require_login
@require_asset_permission('view')
def report_disposal():
    """Disposal Report."""
    db = get_db()
    try:
        disposals = db.execute("""
            SELECT ad.*, a.asset_code, a.name as asset_name,
                   ad.gain_loss
            FROM asset_disposals ad
            JOIN assets a ON ad.asset_id = a.id
            ORDER BY ad.disposal_date DESC
        """).fetchall()

        # Summary
        summary = db.execute("""
            SELECT
                SUM(proceeds) as total_proceeds,
                SUM(gain_loss) as total_gain_loss
            FROM asset_disposals
        """).fetchone()

        return render_template('assets/report_disposal.html',
                             disposals=disposals,
                             summary=summary)

    finally:
        db.close()


@assets_bp.route('/reports/export/<report_type>')
@require_login
@require_asset_permission('view')
def report_export(report_type):
    """Export asset report to Excel."""
    db = get_db()
    try:
        wb = Workbook()
        ws = wb.active

        if report_type == 'register':
            ws.title = 'Asset Register'
            data = db.execute("""
                SELECT a.asset_code, a.name, ac.name as category,
                       a.acquisition_date, a.acquisition_cost,
                       a.useful_life_years, a.accumulated_depreciation,
                       a.net_book_value, a.status, c.name as company,
                       d.name as department
                FROM assets a
                LEFT JOIN asset_categories ac ON a.category_id = ac.id
                LEFT JOIN companies c ON a.company_id = c.id
                LEFT JOIN hr_departments d ON a.department_id = d.id
                WHERE a.status NOT IN ('Disposed', 'Retired')
                ORDER BY a.asset_code
            """).fetchall()

            headers = ['Asset Code', 'Name', 'Category', 'Acquisition Date',
                      'Acquisition Cost', 'Useful Life (Years)', 'Accumulated Depreciation',
                      'Net Book Value', 'Status', 'Company', 'Department']

        elif report_type == 'depreciation':
            ws.title = 'Depreciation'
            data = db.execute("""
                SELECT a.asset_code, a.name, a.acquisition_cost,
                       a.salvage_value, a.useful_life_years,
                       a.accumulated_depreciation, a.net_book_value,
                       dm.name as method
                FROM assets a
                LEFT JOIN depreciation_methods dm ON a.depreciation_method_id = dm.id
                WHERE a.status NOT IN ('Disposed', 'Retired')
                ORDER BY a.asset_code
            """).fetchall()

            headers = ['Asset Code', 'Name', 'Acquisition Cost', 'Salvage Value',
                      'Useful Life (Years)', 'Accumulated Depreciation',
                      'Net Book Value', 'Depreciation Method']

        elif report_type == 'maintenance':
            ws.title = 'Maintenance'
            data = db.execute("""
                SELECT a.asset_code, a.name, mt.name as type,
                       mwl.work_date, mwl.total_cost, mwl.notes
                FROM maintenance_work_logs mwl
                JOIN assets a ON mwl.asset_id = a.id
                JOIN maintenance_types mt ON mwl.maintenance_type_id = mt.id
                ORDER BY mwl.work_date DESC
            """).fetchall()

            headers = ['Asset Code', 'Asset Name', 'Maintenance Type',
                      'Work Date', 'Cost', 'Notes']

        else:
            return jsonify({'error': 'Invalid report type'}), 400

        # Write headers
        ws.append(headers)

        # Write data
        for row in data:
            ws.append([row[h.lower().replace(' ', '_')] if h.lower().replace(' ', '_') in row.keys()
                      else row.get(h.lower().replace(' ', '_'), '') for h in headers])

        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)

        filename = f'asset_{report_type}_report_{datetime.now().strftime("%Y%m%d")}.xlsx'

        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        as_attachment=True, download_name=filename)

    finally:
        db.close()


# =============================================================================
# ASSET SETTINGS
# =============================================================================

@assets_bp.route('/settings')
@require_login
@require_asset_permission('settings')
def settings():
    """Asset Settings."""
    db = get_db()
    try:
        settings_list = db.execute("""
            SELECT * FROM asset_settings
            WHERE is_active = 1
            ORDER BY category, setting_key
        """).fetchall()

        # Group by category
        settings_by_cat = {}
        for s in settings_list:
            cat = s['category']
            if cat not in settings_by_cat:
                settings_by_cat[cat] = []
            settings_by_cat[cat].append(s)

        return render_template('assets/settings.html', settings_by_cat=settings_by_cat)

    finally:
        db.close()


@assets_bp.route('/settings/save', methods=['POST'])
@require_login
@require_asset_permission('settings')
def settings_save():
    """Save asset settings."""
    user_id = session.get('user_id')
    data = request.get_json()

    db = get_db()
    try:
        for key, value in data.items():
            existing = db.execute(
                "SELECT id FROM asset_settings WHERE setting_key = ?",
                (key,)
            ).fetchone()

            if existing:
                db.execute(
                    "UPDATE asset_settings SET setting_value = ?, updated_at = CURRENT_TIMESTAMP WHERE setting_key = ?",
                    (str(value), key)
                )
            else:
                db.execute(
                    "INSERT INTO asset_settings (setting_key, setting_value) VALUES (?, ?)",
                    (key, str(value))
                )

        db.commit()
        log_audit('asset_settings', 0, 'UPDATE', user_id, notes='Asset settings updated')

        return jsonify({'success': True})

    finally:
        db.close()


# =============================================================================
# API ENDPOINTS FOR FRONTEND
# =============================================================================

@assets_bp.route('/api/stats')
@require_login
@require_asset_permission('view')
def api_stats():
    """Get dashboard statistics as JSON."""
    db = get_db()
    try:
        stats = db.execute("""
            SELECT
                COUNT(*) as total_assets,
                SUM(acquisition_cost) as total_cost,
                SUM(accumulated_depreciation) as total_accumulated,
                SUM(net_book_value) as total_nbv
            FROM assets
            WHERE status NOT IN ('Disposed', 'Retired')
        """).fetchone()

        status_counts = db.execute("""
            SELECT status, COUNT(*) as cnt FROM assets GROUP BY status
        """).fetchall()

        return jsonify({
            'total_assets': stats['total_assets'] or 0,
            'total_cost': stats['total_cost'] or 0,
            'total_accumulated': stats['total_accumulated'] or 0,
            'total_nbv': stats['total_nbv'] or 0,
            'by_status': {r['status']: r['cnt'] for r in status_counts}
        })

    finally:
        db.close()


@assets_bp.route('/api/assets')
@require_login
@require_asset_permission('view')
def api_assets():
    """Get assets list as JSON for dropdowns/selects."""
    db = get_db()
    try:
        assets = db.execute("""
            SELECT id, asset_code, name, status, net_book_value
            FROM assets
            WHERE status NOT IN ('Disposed', 'Retired')
            ORDER BY asset_code
        """).fetchall()

        return jsonify([{
            'id': a['id'],
            'asset_code': a['asset_code'],
            'name': a['name'],
            'status': a['status'],
            'net_book_value': a['net_book_value']
        } for a in assets])

    finally:
        db.close()


@assets_bp.route('/api/categories')
@require_login
@require_asset_permission('view')
def api_categories():
    """Get asset categories as JSON."""
    db = get_db()
    try:
        categories = db.execute("""
            SELECT id, name, code, default_useful_life_years, default_salvage_percent
            FROM asset_categories WHERE is_active = 1
            ORDER BY name
        """).fetchall()

        return jsonify([dict(c) for c in categories])

    finally:
        db.close()
