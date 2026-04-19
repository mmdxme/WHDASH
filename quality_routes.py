"""
Quality Management Routes
========================
Flask routes for the Quality Management module.

Provides endpoints for:
- Quality Dashboard
- Inspections (Incoming, In-Process, Outgoing, Warehouse)
- Non-Conformance Records (NCR)
- CAPA (Corrective/Preventive Actions)
- Audit Management
- Quality Reports
- Quality Settings

Route Pattern: /quality/*
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session, send_file
from functools import wraps
import sqlite3
import os
import json
from datetime import datetime, timedelta
from io import BytesIO

from database import get_db, get_db_context, get_one, get_all, log_audit, create_notification
from permissions import user_has_permission, require_permission, get_user_permissions_cached
from quality_models import (
    initialize_quality_tables,
    get_quality_dashboard_stats,
    create_inspection, get_inspections, get_inspection_by_id, update_inspection,
    get_inspection_lines, add_inspection_line,
    create_ncr, get_ncrs, get_ncr_by_id, update_ncr,
    get_containment_actions, create_containment_action, update_containment_action,
    create_capa, get_capas, get_capa_by_id, update_capa,
    get_capa_actions, create_capa_action, update_capa_action,
    create_effectiveness_review,
    create_audit_plan, get_audit_plans, get_audit_plan_by_id, update_audit_plan,
    get_audit_findings, get_finding_by_id, create_audit_finding, update_audit_finding,
    get_quality_audit_log,
    get_inspection_types, get_defect_categories, get_capa_categories,
    get_root_cause_categories, get_inspection_templates,
    get_audit_checklist_templates, get_audit_programs,
    get_quality_setting,
    get_inspection_report_data, get_ncr_summary_report, get_capa_summary_report,
    get_supplier_quality_report
)

# Create blueprint
quality_bp = Blueprint('quality', __name__, url_prefix='/quality')


# =============================================================================
# QUALITY FLOW INTEGRATION HELPERS
# =============================================================================

def send_quality_notification(notification_type, title, message, user_ids=None, severity='MEDIUM', related_id=None, related_type=None):
    """
    Send quality notifications via Flow integration.
    
    Args:
        notification_type: Type of notification (e.g., 'INSPECTION_FAILED', 'NCR_CREATED')
        title: Notification title
        message: Notification message
        user_ids: List of user IDs to notify, or None for quality team
        severity: Notification severity (LOW, MEDIUM, HIGH, CRITICAL)
        related_id: Related record ID
        related_type: Related record type (inspection, ncr, capa, audit)
    """
    try:
        # Get quality team users if not specified
        if user_ids is None:
            user_ids = get_quality_team_users()
        
        # Create notification for each user
        for user_id in user_ids:
            create_notification(
                title=f"[Quality] {title}",
                message=message,
                notification_type=notification_type,
                user_id=user_id,
                severity=severity,
                module='quality',
                related_id=related_id,
                related_type=related_type
            )
        
        return True
    except Exception as e:
        print(f"Error sending quality notification: {e}")
        return False


def get_quality_team_users():
    """Get list of quality team user IDs for notifications."""
    try:
        from permissions import get_users_with_permission
        # Get users with quality.view permission
        quality_users = get_users_with_permission('quality', 'quality', 'view')
        return quality_users if quality_users else []
    except:
        return []


def notify_inspection_failed(inspection_id, inspection_number, item_name, result):
    """Send notification when inspection fails."""
    send_quality_notification(
        notification_type='INSPECTION_FAILED',
        title=f'Inspection Failed: {inspection_number}',
        message=f'Inspection {inspection_number} for item {item_name} has failed with result: {result}',
        severity='HIGH',
        related_id=inspection_id,
        related_type='inspection'
    )


def notify_ncr_created(ncr_id, ncr_number, severity, item_name):
    """Send notification when NCR is created."""
    sev = 'CRITICAL' if severity == 'CRITICAL' else 'HIGH' if severity == 'MAJOR' else 'MEDIUM'
    send_quality_notification(
        notification_type='NCR_CREATED',
        title=f'NCR Created: {ncr_number}',
        message=f'New NCR {ncr_number} created for {item_name} with severity {severity}',
        severity=sev,
        related_id=ncr_id,
        related_type='ncr'
    )


def notify_ncr_overdue(ncr_id, ncr_number, days_overdue):
    """Send notification when NCR is overdue."""
    send_quality_notification(
        notification_type='NCR_OVERDUE',
        title=f'NCR Overdue: {ncr_number}',
        message=f'NCR {ncr_number} is {days_overdue} days overdue and requires immediate attention',
        severity='CRITICAL',
        related_id=ncr_id,
        related_type='ncr'
    )


def notify_capa_created(capa_id, capa_number, title, severity):
    """Send notification when CAPA is created."""
    sev = 'CRITICAL' if severity == 'CRITICAL' else 'HIGH' if severity == 'MAJOR' else 'MEDIUM'
    send_quality_notification(
        notification_type='CAPA_CREATED',
        title=f'CAPA Created: {capa_number}',
        message=f'New CAPA {capa_number} created: {title[:100]}',
        severity=sev,
        related_id=capa_id,
        related_type='capa'
    )


def notify_capa_overdue(capa_id, capa_number, days_overdue):
    """Send notification when CAPA is overdue."""
    send_quality_notification(
        notification_type='CAPA_OVERDUE',
        title=f'CAPA Overdue: {capa_number}',
        message=f'CAPA {capa_number} is {days_overdue} days overdue and requires immediate attention',
        severity='CRITICAL',
        related_id=capa_id,
        related_type='capa'
    )


def notify_audit_finding_created(finding_id, finding_number, severity, audit_title):
    """Send notification when audit finding is created."""
    sev = 'CRITICAL' if severity == 'CRITICAL' else 'HIGH' if severity == 'MAJOR' else 'MEDIUM'
    send_quality_notification(
        notification_type='AUDIT_FINDING_CREATED',
        title=f'Audit Finding: {finding_number}',
        message=f'New {severity} finding {finding_number} in audit: {audit_title[:80]}',
        severity=sev,
        related_id=finding_id,
        related_type='audit_finding'
    )


def notify_quality_hold(item_name, lot_number, reason):
    """Send notification when item is placed on quality hold."""
    send_quality_notification(
        notification_type='QUALITY_HOLD',
        title=f'Quality Hold: {item_name}',
        message=f'Item {item_name} (Lot: {lot_number}) has been placed on quality hold. Reason: {reason}',
        severity='HIGH',
        related_type='hold'
    )


def notify_disposition_required(item_name, lot_number, ncr_number):
    """Send notification when disposition decision is required."""
    send_quality_notification(
        notification_type='DISPOSITION_REQUIRED',
        title=f'Disposition Required: {item_name}',
        message=f'Disposition decision required for {item_name} (Lot: {lot_number}) from NCR {ncr_number}',
        severity='HIGH',
        related_type='disposition'
    )


# =============================================================================
# ROUTE REGISTRATION
# =============================================================================

def register_quality_routes(app):
    """Register quality management routes with the Flask app."""
    initialize_quality_tables()
    app.register_blueprint(quality_bp)


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


def require_quality_permission(action):
    """Decorator factory for quality-specific permissions."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please login to access this page.', 'error')
                return redirect(url_for('login'))

            user_id = session['user_id']
            if not user_has_permission(user_id, 'quality', 'quality', action):
                if request.is_json:
                    return jsonify({'error': 'Permission denied'}), 403
                flash(f"You don't have permission to {action} quality records.", "error")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def check_quality_scope(user_id, company_id=None, branch_id=None, warehouse_id=None):
    """Check if user has access to the specified scope."""
    # Super admin and Global Admin have full access
    permissions = get_user_permissions_cached(user_id)
    if 'quality.*.*' in permissions or 'platform.*.*' in permissions:
        return True
    
    # For now, allow access if user has quality permissions
    if 'quality.quality.view' in permissions:
        return True
    
    return False


# =============================================================================
# QUALITY DASHBOARD
# =============================================================================

@quality_bp.route('/')
@quality_bp.route('/dashboard')
@require_login
@require_quality_permission('view')
def dashboard():
    """Quality Management Dashboard."""
    user_id = session.get('user_id')
    company_id = session.get('company_id')
    branch_id = session.get('branch_id')
    
    stats = get_quality_dashboard_stats(company_id=company_id, branch_id=branch_id)
    
    return render_template('quality/dashboard.html',
        page_title='Quality Dashboard',
        stats=stats,
        user_id=user_id
    )


# =============================================================================
# INSPECTIONS ROUTES
# =============================================================================

@quality_bp.route('/inspections')
@require_login
@require_quality_permission('view')
def inspections_list():
    """List all inspections."""
    user_id = session.get('user_id')
    
    # Get filter parameters
    filters = {
        'company_id': request.args.get('company_id'),
        'branch_id': request.args.get('branch_id'),
        'warehouse_id': request.args.get('warehouse_id'),
        'inspection_type_id': request.args.get('inspection_type_id'),
        'status': request.args.get('status'),
        'result': request.args.get('result'),
        'supplier_id': request.args.get('supplier_id'),
        'from_date': request.args.get('from_date'),
        'to_date': request.args.get('to_date'),
        'search': request.args.get('search'),
    }
    
    inspections = get_inspections(filters)
    inspection_types = get_inspection_types()
    
    return render_template('quality/inspections/list.html',
        page_title='Quality Inspections',
        inspections=inspections,
        inspection_types=inspection_types,
        filters=filters,
        user_id=user_id
    )


@quality_bp.route('/inspections/view/<int:inspection_id>')
@require_login
@require_quality_permission('view')
def inspections_view(inspection_id):
    """View inspection details."""
    inspection = get_inspection_by_id(inspection_id)
    if not inspection:
        flash('Inspection not found.', 'error')
        return redirect(url_for('quality.inspections_list'))
    
    lines = get_inspection_lines(inspection_id)
    
    # Get findings
    with get_db() as db:
        findings = db.execute("""
            SELECT * FROM quality_inspection_findings
            WHERE inspection_id = ?
        """, (inspection_id,)).fetchall()
    
    return render_template('quality/inspections/view.html',
        page_title=f'Inspection {inspection["inspection_number"]}',
        inspection=inspection,
        lines=lines,
        findings=findings,
        user_id=session.get('user_id')
    )


@quality_bp.route('/inspections/create', methods=['GET', 'POST'])
@require_login
@require_quality_permission('create')
def inspections_create():
    """Create new inspection."""
    if request.method == 'GET':
        inspection_types = get_inspection_types()
        templates = get_inspection_templates()
        
        return render_template('quality/inspections/create.html',
            page_title='Create Inspection',
            inspection_types=inspection_types,
            templates=templates,
            user_id=session.get('user_id')
        )
    
    # POST - Create inspection
    data = {
        'inspection_type_id': request.form.get('inspection_type_id'),
        'template_id': request.form.get('template_id'),
        'source_type': request.form.get('source_type'),
        'source_reference': request.form.get('source_reference'),
        'company_id': request.form.get('company_id') or session.get('company_id'),
        'branch_id': request.form.get('branch_id') or session.get('branch_id'),
        'warehouse_id': request.form.get('warehouse_id'),
        'supplier_id': request.form.get('supplier_id'),
        'customer_id': request.form.get('customer_id'),
        'item_id': request.form.get('item_id'),
        'item_code': request.form.get('item_code'),
        'item_name': request.form.get('item_name'),
        'lot_number': request.form.get('lot_number'),
        'batch_number': request.form.get('batch_number'),
        'quantity_received': request.form.get('quantity_received', 0),
        'quantity_inspected': request.form.get('quantity_inspected', 0),
        'sample_size': request.form.get('sample_size', 0),
        'inspection_date': request.form.get('inspection_date'),
        'inspection_time': request.form.get('inspection_time'),
        'inspector_id': session.get('user_id'),
        'inspector_name': session.get('user_name', 'Unknown'),
        'notes': request.form.get('notes'),
        'status': 'IN_PROGRESS',
        'created_by': session.get('user_id')
    }
    
    try:
        inspection_id, inspection_number = create_inspection(data)
        flash(f'Inspection {inspection_number} created successfully.', 'success')
        return redirect(url_for('quality.inspections_view', inspection_id=inspection_id))
    except Exception as e:
        flash(f'Error creating inspection: {str(e)}', 'error')
        return redirect(url_for('quality.inspections_list'))


@quality_bp.route('/inspections/<int:inspection_id>/edit', methods=['GET', 'POST'])
@require_login
@require_quality_permission('edit')
def inspections_edit(inspection_id):
    """Edit inspection."""
    inspection = get_inspection_by_id(inspection_id)
    if not inspection:
        flash('Inspection not found.', 'error')
        return redirect(url_for('quality.inspections_list'))
    
    if request.method == 'GET':
        inspection_types = get_inspection_types()
        templates = get_inspection_templates()
        lines = get_inspection_lines(inspection_id)
        
        return render_template('quality/inspections/edit.html',
            page_title=f'Edit Inspection {inspection["inspection_number"]}',
            inspection=inspection,
            inspection_types=inspection_types,
            templates=templates,
            lines=lines,
            user_id=session.get('user_id')
        )
    
    # POST - Update inspection
    data = {
        'inspection_type_id': request.form.get('inspection_type_id'),
        'template_id': request.form.get('template_id'),
        'quantity_inspected': request.form.get('quantity_inspected', 0),
        'sample_size': request.form.get('sample_size', 0),
        'quantity_accepted': request.form.get('quantity_accepted', 0),
        'quantity_rejected': request.form.get('quantity_rejected', 0),
        'quantity_held': request.form.get('quantity_held', 0),
        'quantity_conditionally_accepted': request.form.get('quantity_conditionally_accepted', 0),
        'result': request.form.get('result'),
        'status': request.form.get('status'),
        'disposition': request.form.get('disposition'),
        'disposition_notes': request.form.get('disposition_notes'),
        'notes': request.form.get('notes'),
        'attachments': request.form.get('attachments'),
        'completed_by': session.get('user_id'),
        'updated_by': session.get('user_id')
    }
    
    if request.form.get('status') == 'COMPLETED':
        data['completed_at'] = datetime.now().isoformat()
    
    try:
        update_inspection(inspection_id, data)
        flash('Inspection updated successfully.', 'success')
        return redirect(url_for('quality.inspections_view', inspection_id=inspection_id))
    except Exception as e:
        flash(f'Error updating inspection: {str(e)}', 'error')
        return redirect(url_for('quality.inspections_edit', inspection_id=inspection_id))


@quality_bp.route('/inspections/<int:inspection_id>/add-line', methods=['POST'])
@require_login
@require_quality_permission('edit')
def inspections_add_line(inspection_id):
    """Add a checklist line to inspection."""
    data = {
        'template_line_id': request.form.get('template_line_id'),
        'line_number': request.form.get('line_number'),
        'criterion': request.form.get('criterion'),
        'description': request.form.get('description'),
        'inspection_method': request.form.get('inspection_method'),
        'acceptance_criteria': request.form.get('acceptance_criteria'),
        'result_type': request.form.get('result_type', 'PASS_FAIL'),
        'result': request.form.get('result'),
        'measurement_value': request.form.get('measurement_value'),
        'measurement_unit': request.form.get('measurement_unit'),
        'is_conforming': 1 if request.form.get('is_conforming') == '1' else 0,
        'findings': request.form.get('findings'),
        'severity': request.form.get('severity'),
        'is_mandatory': 1 if request.form.get('is_mandatory') == '1' else 0,
        'weight': request.form.get('weight', 1.0),
        'notes': request.form.get('notes'),
        'attachments': request.form.get('attachments')
    }
    
    try:
        line_id = add_inspection_line(inspection_id, data)
        flash('Checklist line added successfully.', 'success')
    except Exception as e:
        flash(f'Error adding line: {str(e)}', 'error')
    
    return redirect(url_for('quality.inspections_edit', inspection_id=inspection_id))


@quality_bp.route('/inspections/by-type/<inspection_type>')
@require_login
@require_quality_permission('view')
def inspections_by_type(inspection_type):
    """List inspections by type."""
    filters = {'inspection_type_id': inspection_type}
    inspections = get_inspections(filters)
    inspection_types = get_inspection_types()
    
    return render_template('quality/inspections/list.html',
        page_title=f'{inspection_type} Inspections',
        inspections=inspections,
        inspection_types=inspection_types,
        filters=filters,
        user_id=session.get('user_id')
    )


@quality_bp.route('/inspections/failed')
@require_login
@require_quality_permission('view')
def inspections_failed():
    """List failed inspections."""
    filters = {'result': 'FAIL'}
    inspections = get_inspections(filters)
    inspection_types = get_inspection_types()
    
    return render_template('quality/inspections/list.html',
        page_title='Failed Inspections',
        inspections=inspections,
        inspection_types=inspection_types,
        filters=filters,
        user_id=session.get('user_id')
    )


# =============================================================================
# NCR ROUTES
# =============================================================================

@quality_bp.route('/ncr')
@require_login
@require_quality_permission('view')
def ncr_list():
    """List all NCRs."""
    user_id = session.get('user_id')
    
    filters = {
        'company_id': request.args.get('company_id'),
        'branch_id': request.args.get('branch_id'),
        'status': request.args.get('status'),
        'severity': request.args.get('severity'),
        'ncr_category': request.args.get('ncr_category'),
        'supplier_id': request.args.get('supplier_id'),
        'owner_id': request.args.get('owner_id'),
        'from_date': request.args.get('from_date'),
        'to_date': request.args.get('to_date'),
        'search': request.args.get('search'),
        'is_overdue': request.args.get('is_overdue'),
    }
    
    ncrs = get_ncrs(filters)
    defect_categories = get_defect_categories()
    
    return render_template('quality/ncr/list.html',
        page_title='Non-Conformance Records',
        ncrs=ncrs,
        defect_categories=defect_categories,
        filters=filters,
        user_id=user_id
    )


@quality_bp.route('/ncr/view/<int:ncr_id>')
@require_login
@require_quality_permission('view')
def ncr_view(ncr_id):
    """View NCR details."""
    ncr = get_ncr_by_id(ncr_id)
    if not ncr:
        flash('NCR not found.', 'error')
        return redirect(url_for('quality.ncr_list'))
    
    containment_actions = get_containment_actions(ncr_id)
    
    return render_template('quality/ncr/view.html',
        page_title=f'NCR {ncr["ncr_number"]}',
        ncr=ncr,
        containment_actions=containment_actions,
        user_id=session.get('user_id')
    )


@quality_bp.route('/ncr/create', methods=['GET', 'POST'])
@require_login
@require_quality_permission('create')
def ncr_create():
    """Create new NCR."""
    if request.method == 'GET':
        defect_categories = get_defect_categories()
        
        # Pre-fill from inspection if provided
        inspection_id = request.args.get('inspection_id')
        inspection = None
        if inspection_id:
            inspection = get_inspection_by_id(inspection_id)
        
        return render_template('quality/ncr/create.html',
            page_title='Create NCR',
            defect_categories=defect_categories,
            inspection=inspection,
            user_id=session.get('user_id')
        )
    
    # POST - Create NCR
    data = {
        'source_type': request.form.get('source_type'),
        'source_reference': request.form.get('source_reference'),
        'source_reference_id': request.form.get('source_reference_id'),
        'company_id': request.form.get('company_id') or session.get('company_id'),
        'branch_id': request.form.get('branch_id') or session.get('branch_id'),
        'warehouse_id': request.form.get('warehouse_id'),
        'department': request.form.get('department'),
        'item_id': request.form.get('item_id'),
        'item_code': request.form.get('item_code'),
        'item_name': request.form.get('item_name'),
        'lot_number': request.form.get('lot_number'),
        'batch_number': request.form.get('batch_number'),
        'supplier_id': request.form.get('supplier_id'),
        'supplier_name': request.form.get('supplier_name'),
        'customer_id': request.form.get('customer_id'),
        'customer_name': request.form.get('customer_name'),
        'ncr_category': request.form.get('ncr_category'),
        'defect_category_id': request.form.get('defect_category_id'),
        'defect_type': request.form.get('defect_type'),
        'severity': request.form.get('severity', 'MEDIUM'),
        'impact': request.form.get('impact'),
        'priority': request.form.get('priority', 'MEDIUM'),
        'description': request.form.get('description'),
        'detected_by': session.get('user_id'),
        'detected_by_name': session.get('user_name', 'Unknown'),
        'detected_date': request.form.get('detected_date') or datetime.now().strftime('%Y-%m-%d'),
        'owner_id': request.form.get('owner_id'),
        'owner_name': request.form.get('owner_name'),
        'assigned_to_id': request.form.get('assigned_to_id'),
        'assigned_to_name': request.form.get('assigned_to_name'),
        'status': 'OPEN',
        'containment_required': 1 if request.form.get('containment_required') == '1' else 0,
        'root_cause_required': 1 if request.form.get('root_cause_required') == '1' else 0,
        'capa_required': 1 if request.form.get('capa_required') == '1' else 0,
        'immediate_action': request.form.get('immediate_action'),
        'disposition': request.form.get('disposition'),
        'hold_quantity': request.form.get('hold_quantity', 0),
        'financial_impact': request.form.get('financial_impact', 0),
        'target_close_date': request.form.get('target_close_date'),
        'notes': request.form.get('notes'),
        'attachments': request.form.get('attachments'),
        'created_by': session.get('user_id')
    }
    
    try:
        ncr_id, ncr_number = create_ncr(data)
        flash(f'NCR {ncr_number} created successfully.', 'success')
        return redirect(url_for('quality.ncr_view', ncr_id=ncr_id))
    except Exception as e:
        flash(f'Error creating NCR: {str(e)}', 'error')
        return redirect(url_for('quality.ncr_list'))


@quality_bp.route('/ncr/<int:ncr_id>/edit', methods=['GET', 'POST'])
@require_login
@require_quality_permission('edit')
def ncr_edit(ncr_id):
    """Edit NCR."""
    ncr = get_ncr_by_id(ncr_id)
    if not ncr:
        flash('NCR not found.', 'error')
        return redirect(url_for('quality.ncr_list'))
    
    if request.method == 'GET':
        defect_categories = get_defect_categories()
        containment_actions = get_containment_actions(ncr_id)
        
        return render_template('quality/ncr/edit.html',
            page_title=f'Edit NCR {ncr["ncr_number"]}',
            ncr=ncr,
            defect_categories=defect_categories,
            containment_actions=containment_actions,
            user_id=session.get('user_id')
        )
    
    # POST - Update NCR
    data = dict(request.form)
    data['updated_by'] = session.get('user_id')
    
    # Handle numeric fields
    for field in ['hold_quantity', 'return_quantity', 'rework_quantity', 'scrap_quantity', 
                  'use_as_is_quantity', 'financial_impact']:
        if field in data and data[field]:
            data[field] = float(data[field])
    
    try:
        update_ncr(ncr_id, data)
        flash('NCR updated successfully.', 'success')
        return redirect(url_for('quality.ncr_view', ncr_id=ncr_id))
    except Exception as e:
        flash(f'Error updating NCR: {str(e)}', 'error')
        return redirect(url_for('quality.ncr_edit', ncr_id=ncr_id))


@quality_bp.route('/ncr/<int:ncr_id>/add-containment', methods=['POST'])
@require_login
@require_quality_permission('edit')
def ncr_add_containment(ncr_id):
    """Add containment action to NCR."""
    data = {
        'action_type': request.form.get('action_type'),
        'description': request.form.get('description'),
        'responsible_id': request.form.get('responsible_id'),
        'responsible_name': request.form.get('responsible_name'),
        'due_date': request.form.get('due_date'),
        'status': request.form.get('status', 'PENDING'),
        'evidence': request.form.get('evidence'),
        'notes': request.form.get('notes'),
        'created_by': session.get('user_id')
    }
    
    try:
        action_id, action_number = create_containment_action(ncr_id, data)
        flash(f'Containment action {action_number} created.', 'success')
    except Exception as e:
        flash(f'Error adding containment action: {str(e)}', 'error')
    
    return redirect(url_for('quality.ncr_edit', ncr_id=ncr_id))


@quality_bp.route('/ncr/open')
@require_login
@require_quality_permission('view')
def ncr_open():
    """List open NCRs."""
    filters = {'status': 'OPEN'}
    ncrs = get_ncrs(filters)
    defect_categories = get_defect_categories()
    
    return render_template('quality/ncr/list.html',
        page_title='Open NCRs',
        ncrs=ncrs,
        defect_categories=defect_categories,
        filters=filters,
        user_id=session.get('user_id')
    )


@quality_bp.route('/ncr/overdue')
@require_login
@require_quality_permission('view')
def ncr_overdue():
    """List overdue NCRs."""
    filters = {'is_overdue': True}
    ncrs = get_ncrs(filters)
    defect_categories = get_defect_categories()
    
    return render_template('quality/ncr/list.html',
        page_title='Overdue NCRs',
        ncrs=ncrs,
        defect_categories=defect_categories,
        filters=filters,
        user_id=session.get('user_id')
    )


@quality_bp.route('/ncr/pending-review')
@require_login
@require_quality_permission('view')
def ncr_pending_review():
    """List NCRs pending review."""
    filters = {'status': 'UNDER_REVIEW'}
    ncrs = get_ncrs(filters)
    defect_categories = get_defect_categories()
    
    return render_template('quality/ncr/list.html',
        page_title='NCRs Pending Review',
        ncrs=ncrs,
        defect_categories=defect_categories,
        filters=filters,
        user_id=session.get('user_id')
    )


# =============================================================================
# CAPA ROUTES
# =============================================================================

@quality_bp.route('/capa')
@require_login
@require_quality_permission('view')
def capa_list():
    """List all CAPAs."""
    user_id = session.get('user_id')
    
    filters = {
        'company_id': request.args.get('company_id'),
        'branch_id': request.args.get('branch_id'),
        'status': request.args.get('status'),
        'capa_type': request.args.get('capa_type'),
        'severity': request.args.get('severity'),
        'priority': request.args.get('priority'),
        'owner_id': request.args.get('owner_id'),
        'ncr_id': request.args.get('ncr_id'),
        'is_overdue': request.args.get('is_overdue'),
        'pending_effectiveness': request.args.get('pending_effectiveness'),
        'search': request.args.get('search'),
    }
    
    capas = get_capas(filters)
    capa_categories = get_capa_categories()
    
    return render_template('quality/capa/list.html',
        page_title='CAPA Register',
        capas=capas,
        capa_categories=capa_categories,
        filters=filters,
        user_id=user_id
    )


@quality_bp.route('/capa/view/<int:capa_id>')
@require_login
@require_quality_permission('view')
def capa_view(capa_id):
    """View CAPA details."""
    capa = get_capa_by_id(capa_id)
    if not capa:
        flash('CAPA not found.', 'error')
        return redirect(url_for('quality.capa_list'))
    
    actions = get_capa_actions(capa_id)
    
    # Get linked NCR if exists
    linked_ncr = None
    if capa['ncr_id']:
        linked_ncr = get_ncr_by_id(capa['ncr_id'])
    
    return render_template('quality/capa/view.html',
        page_title=f'CAPA {capa["capa_number"]}',
        capa=capa,
        actions=actions,
        linked_ncr=linked_ncr,
        user_id=session.get('user_id')
    )


@quality_bp.route('/capa/create', methods=['GET', 'POST'])
@quality_bp.route('/capa/create/<int:ncr_id>', methods=['GET', 'POST'])
@require_login
@require_quality_permission('create')
def capa_create(ncr_id=None):
    """Create new CAPA."""
    if request.method == 'GET':
        capa_categories = get_capa_categories()
        root_cause_categories = get_root_cause_categories()
        
        # Pre-fill from NCR if provided
        ncr = None
        if ncr_id:
            ncr = get_ncr_by_id(ncr_id)
        
        return render_template('quality/capa/create.html',
            page_title='Create CAPA',
            capa_categories=capa_categories,
            root_cause_categories=root_cause_categories,
            ncr=ncr,
            user_id=session.get('user_id')
        )
    
    # POST - Create CAPA
    data = {
        'triggering_source': request.form.get('triggering_source'),
        'source_type': request.form.get('source_type'),
        'source_reference': request.form.get('source_reference'),
        'source_reference_id': request.form.get('source_reference_id'),
        'ncr_id': request.form.get('ncr_id') or ncr_id,
        'audit_finding_id': request.form.get('audit_finding_id'),
        'company_id': request.form.get('company_id') or session.get('company_id'),
        'branch_id': request.form.get('branch_id') or session.get('branch_id'),
        'department': request.form.get('department'),
        'warehouse_id': request.form.get('warehouse_id'),
        'category_id': request.form.get('category_id'),
        'capa_type': request.form.get('capa_type', 'CORRECTIVE'),
        'severity': request.form.get('severity', 'MEDIUM'),
        'priority': request.form.get('priority', 'MEDIUM'),
        'title': request.form.get('title'),
        'description': request.form.get('description'),
        'root_cause_summary': request.form.get('root_cause_summary'),
        'root_cause_category_id': request.form.get('root_cause_category_id'),
        'root_cause_description': request.form.get('root_cause_description'),
        'contributing_factors': request.form.get('contributing_factors'),
        'is_recurring_issue': 1 if request.form.get('is_recurring_issue') == '1' else 0,
        'owner_id': request.form.get('owner_id'),
        'owner_name': request.form.get('owner_name'),
        'approver_id': request.form.get('approver_id'),
        'approver_name': request.form.get('approver_name'),
        'target_date': request.form.get('target_date'),
        'status': 'OPEN',
        'effectiveness_verification_required': 1 if request.form.get('effectiveness_verification_required') == '1' else 0,
        'notes': request.form.get('notes'),
        'attachments': request.form.get('attachments'),
        'created_by': session.get('user_id')
    }
    
    try:
        capa_id, capa_number = create_capa(data)
        flash(f'CAPA {capa_number} created successfully.', 'success')
        return redirect(url_for('quality.capa_view', capa_id=capa_id))
    except Exception as e:
        flash(f'Error creating CAPA: {str(e)}', 'error')
        return redirect(url_for('quality.capa_list'))


@quality_bp.route('/capa/<int:capa_id>/edit', methods=['GET', 'POST'])
@require_login
@require_quality_permission('edit')
def capa_edit(capa_id):
    """Edit CAPA."""
    capa = get_capa_by_id(capa_id)
    if not capa:
        flash('CAPA not found.', 'error')
        return redirect(url_for('quality.capa_list'))
    
    if request.method == 'GET':
        capa_categories = get_capa_categories()
        root_cause_categories = get_root_cause_categories()
        actions = get_capa_actions(capa_id)
        
        return render_template('quality/capa/edit.html',
            page_title=f'Edit CAPA {capa["capa_number"]}',
            capa=capa,
            capa_categories=capa_categories,
            root_cause_categories=root_cause_categories,
            actions=actions,
            user_id=session.get('user_id')
        )
    
    # POST - Update CAPA
    data = dict(request.form)
    data['updated_by'] = session.get('user_id')
    
    try:
        update_capa(capa_id, data)
        flash('CAPA updated successfully.', 'success')
        return redirect(url_for('quality.capa_view', capa_id=capa_id))
    except Exception as e:
        flash(f'Error updating CAPA: {str(e)}', 'error')
        return redirect(url_for('quality.capa_edit', capa_id=capa_id))


@quality_bp.route('/capa/<int:capa_id>/add-action', methods=['POST'])
@require_login
@require_quality_permission('edit')
def capa_add_action(capa_id):
    """Add action to CAPA."""
    data = {
        'action_description': request.form.get('action_description'),
        'action_type': request.form.get('action_type'),
        'responsible_id': request.form.get('responsible_id'),
        'responsible_name': request.form.get('responsible_name'),
        'due_date': request.form.get('due_date'),
        'status': request.form.get('status', 'PENDING'),
        'evidence': request.form.get('evidence'),
        'completion_notes': request.form.get('completion_notes'),
        'follow_up_date': request.form.get('follow_up_date'),
        'follow_up_required': 1 if request.form.get('follow_up_required') == '1' else 0,
        'created_by': session.get('user_id')
    }
    
    try:
        action_id, action_number = create_capa_action(capa_id, data)
        flash(f'Action {action_number} created.', 'success')
    except Exception as e:
        flash(f'Error adding action: {str(e)}', 'error')
    
    return redirect(url_for('quality.capa_edit', capa_id=capa_id))


@quality_bp.route('/capa/<int:capa_id>/effectiveness-review', methods=['GET', 'POST'])
@require_login
@require_quality_permission('edit')
def capa_effectiveness_review(capa_id):
    """Perform CAPA effectiveness review."""
    capa = get_capa_by_id(capa_id)
    if not capa:
        flash('CAPA not found.', 'error')
        return redirect(url_for('quality.capa_list'))
    
    if request.method == 'GET':
        return render_template('quality/capa/effectiveness_review.html',
            page_title=f'Effectiveness Review - {capa["capa_number"]}',
            capa=capa,
            user_id=session.get('user_id')
        )
    
    # POST - Create effectiveness review
    data = {
        'review_date': request.form.get('review_date'),
        'reviewer_id': session.get('user_id'),
        'reviewer_name': session.get('user_name', 'Unknown'),
        'effectiveness_result': request.form.get('effectiveness_result'),
        'result_meets_criteria': 1 if request.form.get('result_meets_criteria') == '1' else 0,
        'evidence': request.form.get('evidence'),
        'findings': request.form.get('findings'),
        'recurrence_observed': 1 if request.form.get('recurrence_observed') == '1' else 0,
        'recurrence_details': request.form.get('recurrence_details'),
        'further_action_required': 1 if request.form.get('further_action_required') == '1' else 0,
        'further_action_description': request.form.get('further_action_description'),
        'next_review_date': request.form.get('next_review_date'),
        'status': 'COMPLETED',
        'notes': request.form.get('notes'),
        'attachments': request.form.get('attachments'),
        'created_by': session.get('user_id')
    }
    
    try:
        review_id, review_number = create_effectiveness_review(capa_id, data)
        
        # Update CAPA status based on result
        result = request.form.get('effectiveness_result')
        new_status = 'CLOSED' if result == 'EFFECTIVE' else 'OPEN'
        update_capa(capa_id, {
            'status': new_status,
            'closed_by': session.get('user_id'),
            'closed_at': datetime.now().isoformat() if new_status == 'CLOSED' else None,
            'updated_by': session.get('user_id')
        })
        
        flash(f'Effectiveness review {review_number} completed.', 'success')
        return redirect(url_for('quality.capa_view', capa_id=capa_id))
    except Exception as e:
        flash(f'Error creating effectiveness review: {str(e)}', 'error')
        return redirect(url_for('quality.capa_effectiveness_review', capa_id=capa_id))


@quality_bp.route('/capa/open')
@require_login
@require_quality_permission('view')
def capa_open():
    """List open CAPAs."""
    filters = {'status': 'OPEN'}
    capas = get_capas(filters)
    capa_categories = get_capa_categories()
    
    return render_template('quality/capa/list.html',
        page_title='Open CAPAs',
        capas=capas,
        capa_categories=capa_categories,
        filters=filters,
        user_id=session.get('user_id')
    )


@quality_bp.route('/capa/overdue')
@require_login
@require_quality_permission('view')
def capa_overdue():
    """List overdue CAPAs."""
    filters = {'is_overdue': True}
    capas = get_capas(filters)
    capa_categories = get_capa_categories()
    
    return render_template('quality/capa/list.html',
        page_title='Overdue CAPAs',
        capas=capas,
        capa_categories=capa_categories,
        filters=filters,
        user_id=session.get('user_id')
    )


@quality_bp.route('/capa/effectiveness-review')
@require_login
@require_quality_permission('view')
def capa_pending_effectiveness():
    """List CAPAs pending effectiveness review."""
    filters = {'pending_effectiveness': True}
    capas = get_capas(filters)
    capa_categories = get_capa_categories()
    
    return render_template('quality/capa/list.html',
        page_title='CAPAs Pending Effectiveness Review',
        capas=capas,
        capa_categories=capa_categories,
        filters=filters,
        user_id=session.get('user_id')
    )


# =============================================================================
# AUDIT ROUTES
# =============================================================================

@quality_bp.route('/audits')
@require_login
@require_quality_permission('view')
def audits_list():
    """List all audit plans."""
    user_id = session.get('user_id')
    
    filters = {
        'company_id': request.args.get('company_id'),
        'branch_id': request.args.get('branch_id'),
        'status': request.args.get('status'),
        'audit_type': request.args.get('audit_type'),
        'lead_auditor_id': request.args.get('lead_auditor_id'),
        'from_date': request.args.get('from_date'),
        'to_date': request.args.get('to_date'),
        'search': request.args.get('search'),
    }
    
    audits = get_audit_plans(filters)
    
    return render_template('quality/audits/list.html',
        page_title='Audit Management',
        audits=audits,
        filters=filters,
        user_id=user_id
    )


@quality_bp.route('/audits/view/<int:plan_id>')
@require_login
@require_quality_permission('view')
def audits_view(plan_id):
    """View audit plan details."""
    audit = get_audit_plan_by_id(plan_id)
    if not audit:
        flash('Audit plan not found.', 'error')
        return redirect(url_for('quality.audits_list'))
    
    # Get findings for this audit
    findings = get_audit_findings({'audit_plan_id': plan_id})
    
    return render_template('quality/audits/view.html',
        page_title=f'Audit {audit["plan_number"]}',
        audit=audit,
        findings=findings,
        user_id=session.get('user_id')
    )


@quality_bp.route('/audits/create', methods=['GET', 'POST'])
@require_login
@require_quality_permission('create')
def audits_create():
    """Create new audit plan."""
    if request.method == 'GET':
        programs = get_audit_programs()
        templates = get_audit_checklist_templates()
        
        return render_template('quality/audits/create.html',
            page_title='Create Audit Plan',
            programs=programs,
            templates=templates,
            user_id=session.get('user_id')
        )
    
    # POST - Create audit
    data = {
        'program_id': request.form.get('program_id'),
        'audit_type': request.form.get('audit_type'),
        'scope': request.form.get('scope'),
        'objectives': request.form.get('objectives'),
        'company_id': request.form.get('company_id') or session.get('company_id'),
        'branch_id': request.form.get('branch_id') or session.get('branch_id'),
        'warehouse_id': request.form.get('warehouse_id'),
        'site_location': request.form.get('site_location'),
        'department': request.form.get('department'),
        'process_area': request.form.get('process_area'),
        'scheduled_start_date': request.form.get('scheduled_start_date'),
        'scheduled_end_date': request.form.get('scheduled_end_date'),
        'lead_auditor_id': session.get('user_id'),
        'lead_auditor_name': session.get('user_name', 'Unknown'),
        'auditor_ids': request.form.get('auditor_ids'),
        'auditor_names': request.form.get('auditor_names'),
        'auditee_id': request.form.get('auditee_id'),
        'auditee_name': request.form.get('auditee_name'),
        'auditee_department': request.form.get('auditee_department'),
        'checklist_template_id': request.form.get('checklist_template_id'),
        'status': 'PLANNED',
        'preparation_status': 'NOT_STARTED',
        'notes': request.form.get('notes'),
        'attachments': request.form.get('attachments'),
        'created_by': session.get('user_id')
    }
    
    try:
        plan_id, plan_number = create_audit_plan(data)
        flash(f'Audit plan {plan_number} created successfully.', 'success')
        return redirect(url_for('quality.audits_view', plan_id=plan_id))
    except Exception as e:
        flash(f'Error creating audit: {str(e)}', 'error')
        return redirect(url_for('quality.audits_list'))


@quality_bp.route('/audits/<int:plan_id>/edit', methods=['GET', 'POST'])
@require_login
@require_quality_permission('edit')
def audits_edit(plan_id):
    """Edit audit plan."""
    audit = get_audit_plan_by_id(plan_id)
    if not audit:
        flash('Audit plan not found.', 'error')
        return redirect(url_for('quality.audits_list'))
    
    if request.method == 'GET':
        programs = get_audit_programs()
        templates = get_audit_checklist_templates()
        findings = get_audit_findings({'audit_plan_id': plan_id})
        
        return render_template('quality/audits/edit.html',
            page_title=f'Edit Audit {audit["plan_number"]}',
            audit=audit,
            programs=programs,
            templates=templates,
            findings=findings,
            user_id=session.get('user_id')
        )
    
    # POST - Update audit
    data = dict(request.form)
    data['updated_by'] = session.get('user_id')
    
    try:
        update_audit_plan(plan_id, data)
        flash('Audit plan updated successfully.', 'success')
        return redirect(url_for('quality.audits_view', plan_id=plan_id))
    except Exception as e:
        flash(f'Error updating audit: {str(e)}', 'error')
        return redirect(url_for('quality.audits_edit', plan_id=plan_id))


@quality_bp.route('/audits/<int:plan_id>/add-finding', methods=['POST'])
@require_login
@require_quality_permission('edit')
def audits_add_finding(plan_id):
    """Add finding to audit."""
    data = {
        'checklist_id': request.form.get('checklist_id'),
        'category': request.form.get('category', 'NON_CONFORMITY'),
        'severity': request.form.get('severity', 'MINOR'),
        'clause_reference': request.form.get('clause_reference'),
        'requirement': request.form.get('requirement'),
        'description': request.form.get('description'),
        'evidence': request.form.get('evidence'),
        'auditee_statement': request.form.get('auditee_statement'),
        'corrective_action': request.form.get('corrective_action'),
        'preventive_action': request.form.get('preventive_action'),
        'owner_id': request.form.get('owner_id'),
        'owner_name': request.form.get('owner_name'),
        'due_date': request.form.get('due_date'),
        'status': 'OPEN',
        'notes': request.form.get('notes'),
        'attachments': request.form.get('attachments'),
        'created_by': session.get('user_id')
    }
    
    try:
        finding_id, finding_number = create_audit_finding(plan_id, data)
        flash(f'Finding {finding_number} created.', 'success')
    except Exception as e:
        flash(f'Error creating finding: {str(e)}', 'error')
    
    return redirect(url_for('quality.audits_edit', plan_id=plan_id))


@quality_bp.route('/audits/findings')
@require_login
@require_quality_permission('view')
def audits_findings_list():
    """List all audit findings."""
    filters = {
        'status': request.args.get('status'),
        'severity': request.args.get('severity'),
        'is_overdue': request.args.get('is_overdue'),
        'search': request.args.get('search'),
    }
    
    findings = get_audit_findings(filters)
    
    return render_template('quality/audits/findings_list.html',
        page_title='Audit Findings',
        findings=findings,
        filters=filters,
        user_id=session.get('user_id')
    )


@quality_bp.route('/audits/findings/<int:finding_id>')
@require_login
@require_quality_permission('view')
def audits_findings_view(finding_id):
    """View audit finding details."""
    finding = get_finding_by_id(finding_id)
    if not finding:
        flash('Finding not found.', 'error')
        return redirect(url_for('quality.audits_findings_list'))
    
    return render_template('quality/audits/finding_view.html',
        page_title=f'Finding {finding["finding_number"]}',
        finding=finding,
        user_id=session.get('user_id')
    )


@quality_bp.route('/audits/findings/<int:finding_id>/edit', methods=['GET', 'POST'])
@require_login
@require_quality_permission('edit')
def audits_findings_edit(finding_id):
    """Edit audit finding."""
    finding = get_finding_by_id(finding_id)
    if not finding:
        flash('Finding not found.', 'error')
        return redirect(url_for('quality.audits_findings_list'))
    
    if request.method == 'GET':
        return render_template('quality/audits/finding_edit.html',
            page_title=f'Edit Finding {finding["finding_number"]}',
            finding=finding,
            user_id=session.get('user_id')
        )
    
    # POST - Update finding
    data = dict(request.form)
    data['updated_by'] = session.get('user_id')
    
    try:
        update_audit_finding(finding_id, data)
        flash('Finding updated successfully.', 'success')
        return redirect(url_for('quality.audits_findings_view', finding_id=finding_id))
    except Exception as e:
        flash(f'Error updating finding: {str(e)}', 'error')
        return redirect(url_for('quality.audits_findings_edit', finding_id=finding_id))


@quality_bp.route('/audits/active')
@require_login
@require_quality_permission('view')
def audits_active():
    """List active audits."""
    filters = {'status': 'IN_PROGRESS'}
    audits = get_audit_plans(filters)
    
    return render_template('quality/audits/list.html',
        page_title='Active Audits',
        audits=audits,
        filters=filters,
        user_id=session.get('user_id')
    )


@quality_bp.route('/audits/scheduled')
@require_login
@require_quality_permission('view')
def audits_scheduled():
    """List scheduled audits."""
    filters = {'status': 'PLANNED'}
    audits = get_audit_plans(filters)
    
    return render_template('quality/audits/list.html',
        page_title='Scheduled Audits',
        audits=audits,
        filters=filters,
        user_id=session.get('user_id')
    )


# =============================================================================
# QUALITY REPORTS ROUTES
# =============================================================================

@quality_bp.route('/reports/inspection')
@require_login
@require_quality_permission('view')
def reports_inspection():
    """Inspection report."""
    filters = {
        'company_id': request.args.get('company_id'),
        'branch_id': request.args.get('branch_id'),
        'warehouse_id': request.args.get('warehouse_id'),
        'inspection_type_id': request.args.get('inspection_type_id'),
        'status': request.args.get('status'),
        'result': request.args.get('result'),
        'from_date': request.args.get('from_date'),
        'to_date': request.args.get('to_date'),
    }
    
    report_data = get_inspection_report_data(filters)
    
    return render_template('quality/reports/inspection_report.html',
        page_title='Inspection Report',
        report_data=report_data,
        filters=filters,
        user_id=session.get('user_id')
    )


@quality_bp.route('/reports/ncr')
@require_login
@require_quality_permission('view')
def reports_ncr():
    """NCR summary report."""
    report_data = get_ncr_summary_report(
        company_id=request.args.get('company_id'),
        branch_id=request.args.get('branch_id'),
        from_date=request.args.get('from_date'),
        to_date=request.args.get('to_date')
    )
    
    return render_template('quality/reports/ncr_report.html',
        page_title='NCR Summary Report',
        report_data=report_data,
        filters=request.args,
        user_id=session.get('user_id')
    )


@quality_bp.route('/reports/capa')
@require_login
@require_quality_permission('view')
def reports_capa():
    """CAPA summary report."""
    report_data = get_capa_summary_report(
        company_id=request.args.get('company_id'),
        branch_id=request.args.get('branch_id'),
        from_date=request.args.get('from_date'),
        to_date=request.args.get('to_date')
    )
    
    return render_template('quality/reports/capa_report.html',
        page_title='CAPA Status Report',
        report_data=report_data,
        filters=request.args,
        user_id=session.get('user_id')
    )


@quality_bp.route('/reports/supplier-quality')
@require_login
@require_quality_permission('view')
def reports_supplier_quality():
    """Supplier quality report."""
    report_data = get_supplier_quality_report(
        supplier_id=request.args.get('supplier_id'),
        from_date=request.args.get('from_date'),
        to_date=request.args.get('to_date')
    )
    
    return render_template('quality/reports/supplier_quality_report.html',
        page_title='Supplier Quality Report',
        report_data=report_data,
        filters=request.args,
        user_id=session.get('user_id')
    )


@quality_bp.route('/reports/audit-findings')
@require_login
@require_quality_permission('view')
def reports_audit_findings():
    """Audit findings report."""
    filters = {
        'status': request.args.get('status'),
        'severity': request.args.get('severity'),
        'from_date': request.args.get('from_date'),
        'to_date': request.args.get('to_date'),
    }
    
    findings = get_audit_findings(filters)
    
    return render_template('quality/reports/audit_findings_report.html',
        page_title='Audit Findings Report',
        findings=findings,
        filters=filters,
        user_id=session.get('user_id')
    )


# =============================================================================
# QUALITY SETTINGS ROUTES
# =============================================================================

@quality_bp.route('/settings')
@require_login
@require_quality_permission('settings')
def settings():
    """Quality module settings."""
    from database import get_all
    
    # Get all quality settings
    settings_list = get_all("SELECT * FROM quality_settings ORDER BY category, setting_key")
    
    return render_template('quality/settings.html',
        page_title='Quality Settings',
        settings=settings_list,
        user_id=session.get('user_id')
    )


@quality_bp.route('/settings/update', methods=['POST'])
@require_login
@require_quality_permission('settings')
def settings_update():
    """Update quality settings."""
    for key, value in request.form.items():
        if key.startswith('setting_'):
            setting_key = key.replace('setting_', '')
            with get_db() as db:
                db.execute("""
                    INSERT INTO quality_settings (setting_key, setting_value, category)
                    VALUES (?, ?, 'USER')
                    ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value
                """, (setting_key, value))
                db.commit()
    
    flash('Settings updated successfully.', 'success')
    return redirect(url_for('quality.settings'))


# =============================================================================
# QUALITY AUDIT LOG ROUTES
# =============================================================================

@quality_bp.route('/audit-log')
@require_login
@require_quality_permission('view')
def audit_log():
    """Quality audit log."""
    filters = {
        'entity_type': request.args.get('entity_type'),
        'entity_id': request.args.get('entity_id'),
        'action': request.args.get('action'),
        'user_id': request.args.get('user_id'),
        'from_date': request.args.get('from_date'),
        'to_date': request.args.get('to_date'),
        'search': request.args.get('search'),
    }
    
    log_entries = get_quality_audit_log(filters)
    
    return render_template('quality/audit_log.html',
        page_title='Quality Audit Log',
        log_entries=log_entries,
        filters=filters,
        user_id=session.get('user_id')
    )


# =============================================================================
# API ROUTES (JSON)
# =============================================================================

@quality_bp.route('/api/inspections/<int:inspection_id>')
@require_login
@require_quality_permission('view')
def api_inspection(inspection_id):
    """Get inspection as JSON."""
    inspection = get_inspection_by_id(inspection_id)
    if not inspection:
        return jsonify({'error': 'Inspection not found'}), 404
    
    lines = get_inspection_lines(inspection_id)
    
    return jsonify({
        'inspection': dict(inspection),
        'lines': [dict(l) for l in lines]
    })


@quality_bp.route('/api/ncr/<int:ncr_id>')
@require_login
@require_quality_permission('view')
def api_ncr(ncr_id):
    """Get NCR as JSON."""
    ncr = get_ncr_by_id(ncr_id)
    if not ncr:
        return jsonify({'error': 'NCR not found'}), 404
    
    containment = get_containment_actions(ncr_id)
    
    return jsonify({
        'ncr': dict(ncr),
        'containment_actions': [dict(c) for c in containment]
    })


@quality_bp.route('/api/capa/<int:capa_id>')
@require_login
@require_quality_permission('view')
def api_capa(capa_id):
    """Get CAPA as JSON."""
    capa = get_capa_by_id(capa_id)
    if not capa:
        return jsonify({'error': 'CAPA not found'}), 404
    
    actions = get_capa_actions(capa_id)
    
    return jsonify({
        'capa': dict(capa),
        'actions': [dict(a) for a in actions]
    })


@quality_bp.route('/api/audit/<int:plan_id>')
@require_login
@require_quality_permission('view')
def api_audit(plan_id):
    """Get audit plan as JSON."""
    audit = get_audit_plan_by_id(plan_id)
    if not audit:
        return jsonify({'error': 'Audit not found'}), 404
    
    findings = get_audit_findings({'audit_plan_id': plan_id})
    
    return jsonify({
        'audit': dict(audit),
        'findings': [dict(f) for f in findings]
    })


@quality_bp.route('/api/dashboard-stats')
@require_login
@require_quality_permission('view')
def api_dashboard_stats():
    """Get dashboard stats as JSON."""
    company_id = request.args.get('company_id') or session.get('company_id')
    branch_id = request.args.get('branch_id') or session.get('branch_id')
    
    stats = get_quality_dashboard_stats(company_id=company_id, branch_id=branch_id)
    
    return jsonify(stats)
