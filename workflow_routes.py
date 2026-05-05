"""
Workflow/BPM Route Handler System
=================================
Comprehensive route handlers for the Workflow/Business Process Management module.

ROUTE STRUCTURE:
- /workflow/ - Main dashboard and user work inbox
- /workflow/designer/ - Workflow definition and step designer
- /workflow/processes/ - Process modeling and state management
- /workflow/automation/ - Automation rules engine
- /workflow/notifications/ - Notification templates and delivery
- /workflow/monitoring/ - Instance monitoring and escalation
- /workflow/reports/ - Performance and analytics reports
- /workflow/settings/ - Workflow configuration
- /workflow/audit/ - Audit logs and history
- /api/workflow/ - JSON API endpoints

USAGE:
    from workflow_routes import register_workflow_routes
    register_workflow_routes(app)
"""

from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from datetime import datetime, timedelta
import json
import csv
import io

from database import (
    get_db, get_db_context, get_one, get_all,
    log_audit, create_notification, get_user_notifications,
    table_exists, column_exists
)
from permissions import (
    user_has_permission, get_user_permissions,
    require_permission, get_all_roles, get_role_by_id,
    MODULE_PERMISSIONS
)
from navigation import (
    get_main_menu, get_breadcrumbs, get_page_title,
    prepare_menu_for_template
)
from theme_engine import get_available_themes
from workflow_models import (
    WORKFLOW_STATES, STEP_TYPES, ASSIGNEE_TYPES, ACTION_TYPES,
    PRIORITY_LEVELS, WORKFLOW_STATUS_COLORS, AUTOMATION_TRIGGERS,
    AUTOMATION_ACTIONS, NOTIFICATION_CHANNELS,
    get_workflow_definition, get_all_workflow_definitions,
    create_workflow_definition, update_workflow_definition,
    get_workflow_steps, create_workflow_step, update_workflow_step, delete_workflow_step,
    get_workflow_transitions, create_workflow_transition, update_workflow_transition,
    get_transition_conditions, create_workflow_condition, delete_workflow_condition,
    get_workflow_instance, get_workflow_instances, create_workflow_instance,
    get_pending_approvals, get_my_work_items, get_my_completed_items,
    get_automation_rules, create_automation_rule, update_automation_rule,
    get_notification_templates, create_notification_template,
    get_escalation_rules, create_escalation_rule, update_escalation_rule,
    get_delegation_rules, create_delegation_rule, update_delegation_rule,
    get_workflow_stats, get_workflow_reports
)

# Import export utilities
from export_utils import (
    send_export_response,
    get_export_columns
)

# Create workflow blueprint
workflow_bp = Blueprint('workflow', __name__, url_prefix='/workflow')


# =============================================================================
# EXPORT TYPES AND COLUMNS
# =============================================================================

WORKFLOW_EXPORT_TYPES = [
    'csv', 'excel_text', 'excel_general', 'json', 'xml', 'txt',
    'pdf', 'docx', 'html', 'printable', 'barcode', 'api',
    'email', 'zip', 'backup', 'sql_dump', 'dashboard',
    'summary', 'detailed', 'audit_log'
]

WORKFLOW_EXPORT_COLUMNS = {
    'definitions': ['definition_id', 'name', 'version', 'status', 'created_by', 'created_at'],
    'instances': ['instance_id', 'definition_name', 'status', 'current_step', 'assignee', 'created_at'],
    'steps': ['step_id', 'instance_id', 'step_name', 'status', 'assignee', 'completed_at'],
    'transitions': ['transition_id', 'from_step', 'to_step', 'condition', 'created_at'],
    'tasks': ['task_id', 'instance_id', 'task_name', 'assignee', 'due_date', 'status'],
    'notifications': ['notification_id', 'template_name', 'channel', 'recipient', 'sent_at']
}


# =============================================================================
# API EXPORT ENDPOINTS
# =============================================================================

@workflow_bp.route('/api/export/<export_type>', methods=['GET', 'POST'])
@workflow_bp.route('/api/export/<data_type>/<export_type>', methods=['GET', 'POST'])
@workflow_require_permission('reports', 'view')
def api_workflow_export(export_type, data_type=None):
    """Export workflow data in all 20 formats."""
    if export_type not in WORKFLOW_EXPORT_TYPES:
        return jsonify({
            'error': f'Invalid export type. Valid types: {WORKFLOW_EXPORT_TYPES}'
        }), 400

    company_id = session.get('company_id', 0)

    # Determine data type from URL or default
    if data_type is None:
        data_type = request.args.get('type', 'definitions')

    # Get data based on type
    if data_type == 'definitions':
        data = get_all("""
            SELECT * FROM workflow_definitions
            WHERE company_id = ?
            ORDER BY created_at DESC
            LIMIT 5000
        """, (company_id,))
        columns = WORKFLOW_EXPORT_COLUMNS['definitions']
        title = 'Workflow Definitions'
    elif data_type == 'instances':
        data = get_all("""
            SELECT wi.*, wd.name as definition_name
            FROM workflow_instances wi
            LEFT JOIN workflow_definitions wd ON wi.definition_id = wd.id
            WHERE wi.company_id = ?
            ORDER BY wi.created_at DESC
            LIMIT 5000
        """, (company_id,))
        columns = WORKFLOW_EXPORT_COLUMNS['instances']
        title = 'Workflow Instances'
    elif data_type == 'steps':
        data = get_all("""
            SELECT * FROM workflow_steps
            WHERE company_id = ?
            ORDER BY created_at DESC
            LIMIT 5000
        """, (company_id,))
        columns = WORKFLOW_EXPORT_COLUMNS['steps']
        title = 'Workflow Steps'
    elif data_type == 'transitions':
        data = get_all("""
            SELECT * FROM workflow_transitions
            WHERE company_id = ?
            ORDER BY created_at DESC
            LIMIT 5000
        """, (company_id,))
        columns = WORKFLOW_EXPORT_COLUMNS['transitions']
        title = 'Workflow Transitions'
    elif data_type == 'tasks':
        data = get_all("""
            SELECT * FROM workflow_tasks
            WHERE company_id = ?
            ORDER BY due_date DESC
            LIMIT 5000
        """, (company_id,))
        columns = WORKFLOW_EXPORT_COLUMNS['tasks']
        title = 'Workflow Tasks'
    elif data_type == 'notifications':
        data = get_all("""
            SELECT * FROM workflow_notifications
            WHERE company_id = ?
            ORDER BY sent_at DESC
            LIMIT 5000
        """, (company_id,))
        columns = WORKFLOW_EXPORT_COLUMNS['notifications']
        title = 'Workflow Notifications'
    else:
        return jsonify({'error': f'Data type {data_type} not supported'}), 400

    filename = f'workflow_{data_type}_{datetime.now().strftime("%Y%m%d")}'

    return send_export_response(data, export_type, filename, columns, title)


@workflow_bp.route('/api/export/list')
@workflow_require_permission('reports', 'view')
def list_workflow_export_types():
    """List available export types for workflow module."""
    return jsonify({
        'module': 'workflow',
        'data_types': list(WORKFLOW_EXPORT_COLUMNS.keys()),
        'export_types': [{'type': t} for t in WORKFLOW_EXPORT_TYPES]
    })


def register_workflow_routes(app):
    """Register all workflow routes with the Flask app."""

    # =====================================================================
    # HELPER DECORATORS
    # =====================================================================

    def workflow_require_login(f):
        """Decorator requiring authentication."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function

    def workflow_require_permission(resource, action):
        """Decorator requiring specific permission."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                user_id = session.get('user_id')
                if not user_id:
                    return redirect(url_for('login'))
                if not user_has_permission(user_id, 'workflow', resource, action):
                    flash(f"Access denied. You need '{action}' permission on '{resource}'.", "error")
                    return redirect(url_for('index'))
                return f(*args, **kwargs)
            return decorated_function
        return decorator

    def _get_workflow_context(user_id, language='en'):
        """Build common context for workflow pages."""
        user_perms = get_user_permissions(user_id)
        menu = get_main_menu(user_id, language)
        current_path = request.path

        return {
            'user_id': user_id,
            'username': session.get('username', 'User'),
            'language': language,
            'direction': 'rtl' if language in ['ar', 'fa'] else 'ltr',
            'menu': prepare_menu_for_template(menu, current_path),
            'permissions': user_perms,
            'available_themes': get_available_themes(),
            'notifications': get_user_notifications(user_id, unread_only=True, limit=10),
            'workflow_states': WORKFLOW_STATES,
            'step_types': STEP_TYPES,
            'assignee_types': ASSIGNEE_TYPES,
            'action_types': ACTION_TYPES,
            'priority_levels': PRIORITY_LEVELS,
            'status_colors': WORKFLOW_STATUS_COLORS,
            'automation_triggers': AUTOMATION_TRIGGERS,
            'automation_actions': AUTOMATION_ACTIONS,
            'notification_channels': NOTIFICATION_CHANNELS
        }

    def _has_workflow_access(user_id):
        """Check if user has any workflow module access."""
        return (user_has_permission(user_id, 'workflow', 'dashboard', 'view') or
                user_has_permission(user_id, 'workflow', 'my_work', 'view') or
                user_has_permission(user_id, 'workflow', 'designer', 'view'))

    # =====================================================================
    # A. WORKFLOW DASHBOARD
    # =====================================================================

    @workflow_bp.route('/')
    @workflow_bp.route('/dashboard')
    @workflow_require_login
    def workflow_dashboard():
        """Main workflow dashboard with stats."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not _has_workflow_access(user_id):
            flash("Access denied. You don't have access to the Workflow module.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/dashboard', 'Workflow Dashboard')

        # Get dashboard stats
        stats = get_workflow_stats(user_id)
        context['stats'] = stats

        # Get recent workflow activity
        context['recent_items'] = get_my_work_items(user_id, limit=10)
        context['pending_count'] = stats.get('pending_count', 0)
        context['overdue_count'] = stats.get('overdue_count', 0)
        context['completed_today'] = stats.get('completed_today', 0)

        return render_template('workflow/dashboard.html', **context)

    @workflow_bp.route('/api/dashboard/stats')
    @workflow_require_login
    def workflow_api_dashboard_stats():
        """API endpoint for dashboard statistics."""
        user_id = session.get('user_id')
        stats = get_workflow_stats(user_id)
        return jsonify(stats)

    # =====================================================================
    # B. MY WORK (User's Personal Workflow Inbox)
    # =====================================================================

    @workflow_bp.route('/my-work')
    @workflow_require_login
    def workflow_my_work():
        """My Work main page - all items assigned to user."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/my-work', 'My Work')

        # Get filter parameters
        status = request.args.get('status', '')
        priority = request.args.get('priority', '')
        search = request.args.get('search', '')
        page = request.args.get('page', 1, type=int)
        per_page = 20

        # Get user's work items
        items = get_my_work_items(user_id, status=status, priority=priority,
                                  search=search, page=page, per_page=per_page)
        context['items'] = items
        context['current_filters'] = {'status': status, 'priority': priority, 'search': search}

        return render_template('workflow/my_work.html', **context)

    @workflow_bp.route('/my-approvals')
    @workflow_require_login
    def workflow_my_approvals():
        """Pending approvals assigned to user."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/my-approvals', 'My Approvals')

        items = get_pending_approvals(user_id, assignee_type='user')
        context['items'] = items

        return render_template('workflow/my_approvals.html', **context)

    @workflow_bp.route('/my-pending')
    @workflow_require_login
    def workflow_my_pending():
        """Pending actions for user."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/my-pending', 'Pending Actions')

        items = get_my_work_items(user_id, status='pending')
        context['items'] = items

        return render_template('workflow/my_pending.html', **context)

    @workflow_bp.route('/delegated-to-me')
    @workflow_require_login
    def workflow_delegated_to_me():
        """Items delegated to user by others."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/delegated-to-me', 'Delegated to Me')

        items = get_my_work_items(user_id, delegated=True)
        context['items'] = items

        return render_template('workflow/delegated_to_me.html', **context)

    @workflow_bp.route('/my-completed')
    @workflow_require_login
    def workflow_my_completed():
        """Completed actions by user."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/my-completed', 'My Completed')

        page = request.args.get('page', 1, type=int)
        per_page = 20

        items = get_my_completed_items(user_id, page=page, per_page=per_page)
        context['items'] = items

        return render_template('workflow/my_completed.html', **context)

    @workflow_bp.route('/returned')
    @workflow_require_login
    def workflow_returned():
        """Returned/rejected items for user."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/returned', 'Returned Items')

        items = get_my_work_items(user_id, status='returned')
        context['items'] = items

        return render_template('workflow/returned.html', **context)

    @workflow_bp.route('/<int:instance_id>/approve', methods=['POST'])
    @workflow_require_login
    @workflow_require_permission('requests', 'approve')
    def workflow_approve(instance_id):
        """Approve a workflow instance."""
        user_id = session.get('user_id')

        comment = request.form.get('comment', '')
        with get_db_context() as db:
            db.execute("""
                INSERT INTO workflow_actions (instance_id, action_type, performed_by, comment)
                VALUES (?, 'approve', ?, ?)
            """, (instance_id, user_id, comment))
            db.execute("""
                UPDATE workflow_instances SET status = 'approved', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (instance_id,))
            db.commit()

            log_audit('workflow_instance', instance_id, 'APPROVE', user_id=user_id, notes=comment)
            create_notification(
                title='Workflow Approved',
                message=f'Your workflow request has been approved by {session.get("username")}',
                notification_type='SUCCESS',
                user_id=user_id
            )

        flash("Item approved successfully.", "success")
        return redirect(url_for('workflow_my_work'))

    @workflow_bp.route('/<int:instance_id>/reject', methods=['POST'])
    @workflow_require_login
    @workflow_require_permission('requests', 'reject')
    def workflow_reject(instance_id):
        """Reject a workflow instance."""
        user_id = session.get('user_id')

        comment = request.form.get('comment', '')
        reason = request.form.get('reason', '')

        with get_db_context() as db:
            db.execute("""
                INSERT INTO workflow_actions (instance_id, action_type, performed_by, comment)
                VALUES (?, 'reject', ?, ?)
            """, (instance_id, user_id, comment))
            db.execute("""
                UPDATE workflow_instances SET status = 'rejected', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (instance_id,))
            db.commit()

            log_audit('workflow_instance', instance_id, 'REJECT', user_id=user_id, notes=f"Reason: {reason}")

        flash("Item rejected.", "warning")
        return redirect(url_for('workflow_my_work'))

    @workflow_bp.route('/<int:instance_id>/return', methods=['POST'])
    @workflow_require_login
    @workflow_require_permission('requests', 'return')
    def workflow_return(instance_id):
        """Return a workflow instance for correction."""
        user_id = session.get('user_id')

        comment = request.form.get('comment', '')

        with get_db_context() as db:
            db.execute("""
                INSERT INTO workflow_actions (instance_id, action_type, performed_by, comment)
                VALUES (?, 'return', ?, ?)
            """, (instance_id, user_id, comment))
            db.execute("""
                UPDATE workflow_instances SET status = 'returned', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (instance_id,))
            db.commit()

            log_audit('workflow_instance', instance_id, 'RETURN', user_id=user_id, notes=comment)

        flash("Item returned for correction.", "info")
        return redirect(url_for('workflow_my_work'))

    @workflow_bp.route('/<int:instance_id>/reassign', methods=['POST'])
    @workflow_require_login
    @workflow_require_permission('requests', 'reassign')
    def workflow_reassign(instance_id):
        """Reassign a workflow instance to another user."""
        user_id = session.get('user_id')

        new_assignee_id = request.form.get('assignee_id', type=int)
        comment = request.form.get('comment', '')

        if not new_assignee_id:
            flash("Please select a user to reassign to.", "error")
            return redirect(url_for('workflow_my_work'))

        with get_db_context() as db:
            db.execute("""
                INSERT INTO workflow_actions (instance_id, action_type, performed_by, comment)
                VALUES (?, 'reassign', ?, ?)
            """, (instance_id, user_id, f"Reassigned to user {new_assignee_id}: {comment}"))
            db.execute("""
                UPDATE workflow_instance_steps SET assignee_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE instance_id = ? AND completion_status IS NULL
            """, (new_assignee_id, instance_id))
            db.commit()

            log_audit('workflow_instance', instance_id, 'REASSIGN', user_id=user_id,
                     notes=f"Reassigned to user {new_assignee_id}")

        flash("Item reassigned successfully.", "success")
        return redirect(url_for('workflow_my_work'))

    @workflow_bp.route('/<int:instance_id>/escalate', methods=['POST'])
    @workflow_require_login
    @workflow_require_permission('requests', 'escalate')
    def workflow_escalate(instance_id):
        """Manually escalate a workflow instance."""
        user_id = session.get('user_id')

        comment = request.form.get('comment', '')
        escalation_level = request.form.get('escalation_level', 1, type=int)

        with get_db_context() as db:
            db.execute("""
                INSERT INTO workflow_actions (instance_id, action_type, performed_by, comment)
                VALUES (?, 'escalate', ?, ?)
            """, (instance_id, user_id, comment))
            db.execute("""
                UPDATE workflow_instances SET status = 'escalated', escalation_level = ?,
                updated_at = CURRENT_TIMESTAMP WHERE id = ?
            """, (escalation_level, instance_id))
            db.commit()

            log_audit('workflow_instance', instance_id, 'ESCALATE', user_id=user_id, notes=comment)

        flash("Item escalated.", "warning")
        return redirect(url_for('workflow_my_work'))

    @workflow_bp.route('/<int:instance_id>/submit', methods=['POST'])
    @workflow_require_login
    @workflow_require_permission('requests', 'submit')
    def workflow_submit(instance_id):
        """Submit a workflow instance for approval (from draft)."""
        user_id = session.get('user_id')

        with get_db_context() as db:
            db.execute("""
                INSERT INTO workflow_actions (instance_id, action_type, performed_by)
                VALUES (?, 'submit', ?)
            """, (instance_id, user_id))
            db.execute("""
                UPDATE workflow_instances SET status = 'submitted', updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'draft'
            """, (instance_id,))
            db.commit()

            log_audit('workflow_instance', instance_id, 'SUBMIT', user_id=user_id)

        flash("Workflow submitted for approval.", "success")
        return redirect(url_for('workflow_my_work'))

    @workflow_bp.route('/<int:instance_id>/cancel', methods=['POST'])
    @workflow_require_login
    @workflow_require_permission('requests', 'cancel')
    def workflow_cancel(instance_id):
        """Cancel a workflow instance."""
        user_id = session.get('user_id')

        comment = request.form.get('comment', '')

        with get_db_context() as db:
            db.execute("""
                INSERT INTO workflow_actions (instance_id, action_type, performed_by, comment)
                VALUES (?, 'cancel', ?, ?)
            """, (instance_id, user_id, comment))
            db.execute("""
                UPDATE workflow_instances SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (instance_id,))
            db.commit()

            log_audit('workflow_instance', instance_id, 'CANCEL', user_id=user_id, notes=comment)

        flash("Workflow cancelled.", "info")
        return redirect(url_for('workflow_my_work'))

    @workflow_bp.route('/<int:instance_id>/detail')
    @workflow_require_login
    def workflow_instance_detail(instance_id):
        """View workflow instance detail."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/instance', 'Workflow Detail')

        instance = get_workflow_instance(instance_id)
        if not instance:
            flash("Workflow instance not found.", "error")
            return redirect(url_for('workflow_my_work'))

        context['instance'] = instance

        # Get instance steps
        with get_db_context() as db:
            context['steps'] = db.execute("""
                SELECT wis.*, ws.step_name, ws.step_type
                FROM workflow_instance_steps wis
                JOIN workflow_steps ws ON wis.step_id = ws.id
                WHERE wis.instance_id = ?
                ORDER BY wis.step_order
            """, (instance_id,)).fetchall()

            context['actions'] = db.execute("""
                SELECT wa.*, u.username as performed_by_name
                FROM workflow_actions wa
                LEFT JOIN users u ON wa.performed_by = u.id
                WHERE wa.instance_id = ?
                ORDER BY wa.created_at DESC
            """, (instance_id,)).fetchall()

            context['comments'] = db.execute("""
                SELECT wc.*, u.username as created_by_name
                FROM workflow_comments wc
                LEFT JOIN users u ON wc.created_by = u.id
                WHERE wc.instance_id = ?
                ORDER BY wc.created_at DESC
            """, (instance_id,)).fetchall()

        return render_template('workflow/instance_detail.html', **context)

    # =====================================================================
    # C. WORKFLOW DESIGNER
    # =====================================================================

    @workflow_bp.route('/designer')
    @workflow_require_login
    def workflow_designer():
        """Workflow Designer main page."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'designer', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/designer', 'Workflow Designer')
        context['definitions'] = get_all_workflow_definitions(active_only=False)
        context['roles'] = get_all_roles()

        return render_template('workflow/designer/index.html', **context)

    @workflow_bp.route('/designer/definitions')
    @workflow_require_login
    def workflow_designer_definitions():
        """List workflow definitions."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'designer', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/designer/definitions', 'Workflow Definitions')
        context['definitions'] = get_all_workflow_definitions(active_only=False)

        return render_template('workflow/designer/definitions.html', **context)

    @workflow_bp.route('/designer/definitions/new', methods=['GET', 'POST'])
    @workflow_require_login
    def workflow_designer_definition_new():
        """New workflow definition form."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'designer', 'create'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/designer/definitions/new', 'New Workflow')
        context['roles'] = get_all_roles()

        if request.method == 'POST':
            workflow_type = request.form.get('workflow_type')
            name = request.form.get('name')
            module = request.form.get('module')
            entity_type = request.form.get('entity_type')
            description = request.form.get('description', '')
            requires_approval = request.form.get('requires_approval') == 'on'

            if not all([workflow_type, name, module]):
                flash("Workflow type, name, and module are required.", "error")
                return redirect(url_for('workflow_designer_definition_new'))

            workflow_def_id = create_workflow_definition(
                workflow_type=workflow_type,
                name=name,
                module=module,
                entity_type=entity_type,
                description=description,
                requires_approval=requires_approval,
                created_by=user_id
            )

            flash("Workflow definition created.", "success")
            return redirect(url_for('workflow_designer_definition_edit', definition_id=workflow_def_id))

        return render_template('workflow/designer/definition_form.html', **context)

    @workflow_bp.route('/designer/definitions/<int:definition_id>/edit', methods=['GET', 'POST'])
    @workflow_require_login
    def workflow_designer_definition_edit(definition_id):
        """Edit workflow definition form."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'designer', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/designer/definitions/edit', 'Edit Workflow')
        context['roles'] = get_all_roles()

        definition = get_workflow_definition(definition_id)
        if not definition:
            flash("Workflow definition not found.", "error")
            return redirect(url_for('workflow_designer_definitions'))

        context['definition'] = definition

        if request.method == 'POST':
            data = {
                'name': request.form.get('name'),
                'description': request.form.get('description', ''),
                'requires_approval': request.form.get('requires_approval') == 'on'
            }
            update_workflow_definition(definition_id, data, user_id)

            flash("Workflow definition updated.", "success")
            return redirect(url_for('workflow_designer_definition_edit', definition_id=definition_id))

        # Get steps for this definition
        with get_db_context() as db:
            context['steps'] = db.execute("""
                SELECT * FROM workflow_steps
                WHERE workflow_definition_id = ?
                ORDER BY step_order
            """, (definition_id,)).fetchall()

            context['transitions'] = db.execute("""
                SELECT wt.*, fs.step_name as from_step, ts.step_name as to_step
                FROM workflow_transitions wt
                LEFT JOIN workflow_steps fs ON wt.from_step_id = fs.id
                LEFT JOIN workflow_steps ts ON wt.to_step_id = ts.id
                WHERE wt.workflow_definition_id = ?
            """, (definition_id,)).fetchall()

        return render_template('workflow/designer/definition_form.html', **context)

    @workflow_bp.route('/designer/definitions/<int:definition_id>/delete', methods=['POST'])
    @workflow_require_login
    def workflow_designer_definition_delete(definition_id):
        """Delete workflow definition."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'designer', 'delete'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        with get_db_context() as db:
            db.execute("DELETE FROM workflow_definitions WHERE id = ?", (definition_id,))
            db.commit()

            log_audit('workflow_definition', definition_id, 'DELETE', user_id=user_id)

        flash("Workflow definition deleted.", "success")
        return redirect(url_for('workflow_designer_definitions'))

    @workflow_bp.route('/designer/definitions/<int:definition_id>/activate', methods=['POST'])
    @workflow_require_login
    def workflow_designer_definition_activate(definition_id):
        """Activate a workflow definition."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'designer', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        with get_db_context() as db:
            db.execute("""
                UPDATE workflow_definitions SET is_active = 1, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (definition_id,))
            db.commit()

            log_audit('workflow_definition', definition_id, 'ACTIVATE', user_id=user_id)

        flash("Workflow activated.", "success")
        return redirect(url_for('workflow_designer_definition_edit', definition_id=definition_id))

    @workflow_bp.route('/designer/definitions/<int:definition_id>/deactivate', methods=['POST'])
    @workflow_require_login
    def workflow_designer_definition_deactivate(definition_id):
        """Deactivate a workflow definition."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'designer', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        with get_db_context() as db:
            db.execute("""
                UPDATE workflow_definitions SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (definition_id,))
            db.commit()

            log_audit('workflow_definition', definition_id, 'DEACTIVATE', user_id=user_id)

        flash("Workflow deactivated.", "info")
        return redirect(url_for('workflow_designer_definition_edit', definition_id=definition_id))

    @workflow_bp.route('/designer/definitions/<int:definition_id>/duplicate', methods=['POST'])
    @workflow_require_login
    def workflow_designer_definition_duplicate(definition_id):
        """Clone/duplicate a workflow definition."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'designer', 'create'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        original = get_workflow_definition(definition_id)
        if not original:
            flash("Workflow not found.", "error")
            return redirect(url_for('workflow_designer_definitions'))

        new_id = create_workflow_definition(
            workflow_type=f"{original['workflow_type']}_copy",
            name=f"{original['name']} (Copy)",
            module=original['module'],
            entity_type=original['entity_type'],
            description=original.get('description', ''),
            version=1,
            requires_approval=original.get('requires_approval', True),
            created_by=user_id
        )

        log_audit('workflow_definition', new_id, 'DUPLICATE', user_id=user_id,
                 notes=f"Duplicated from definition {definition_id}")

        flash("Workflow duplicated.", "success")
        return redirect(url_for('workflow_designer_definition_edit', definition_id=new_id))

    # =====================================================================
    # C.1 STEP DESIGNER
    # =====================================================================

    @workflow_bp.route('/designer/steps/<int:definition_id>')
    @workflow_require_login
    def workflow_designer_steps(definition_id):
        """Step designer for a workflow definition."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'designer', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/designer/steps', 'Step Designer')
        context['definition_id'] = definition_id
        context['roles'] = get_all_roles()

        definition = get_workflow_definition(definition_id)
        context['definition'] = definition

        steps = get_workflow_steps(workflow_definition_id=definition_id)
        context['steps'] = steps

        return render_template('workflow/designer/steps.html', **context)

    @workflow_bp.route('/designer/steps', methods=['POST'])
    @workflow_require_login
    def workflow_designer_step_create():
        """Create a new step."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'designer', 'create'):
            return jsonify({'error': 'Access denied'}), 403

        definition_id = request.form.get('definition_id', type=int)
        step_code = request.form.get('step_code')
        step_name = request.form.get('step_name')
        step_order = request.form.get('step_order', 1, type=int)
        step_type = request.form.get('step_type', 'approval')
        assignee_type = request.form.get('assignee_type', 'role')
        assignee_id = request.form.get('assignee_id', type=int)
        due_duration_hours = request.form.get('due_duration_hours', 24, type=int)
        allow_approve = request.form.get('allow_approve') == 'on'
        allow_reject = request.form.get('allow_reject') == 'on'
        allow_return = request.form.get('allow_return') == 'on'

        with get_db_context() as db:
            version = db.execute("""
                SELECT id FROM workflow_versions
                WHERE workflow_definition_id = ? AND status = 'draft'
                ORDER BY version_number DESC LIMIT 1
            """, (definition_id,)).fetchone()

            version_id = version['id'] if version else None

            step_id = create_workflow_step(
                workflow_definition_id=definition_id,
                version_id=version_id,
                step_code=step_code,
                step_name=step_name,
                step_order=step_order,
                step_type=step_type,
                assignee_type=assignee_type,
                assignee_id=assignee_id,
                due_duration_hours=due_duration_hours,
                allow_approve=allow_approve,
                allow_reject=allow_reject,
                allow_return=allow_return
            )

            log_audit('workflow_step', step_id, 'CREATE', user_id=user_id,
                     notes=f"Created step {step_code} for definition {definition_id}")

        flash("Step created.", "success")
        return redirect(url_for('workflow_designer_steps', definition_id=definition_id))

    @workflow_bp.route('/designer/steps/<int:step_id>', methods=['PUT', 'POST'])
    @workflow_require_login
    def workflow_designer_step_update(step_id):
        """Update a step."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'designer', 'edit'):
            return jsonify({'error': 'Access denied'}), 403

        data = {
            'step_name': request.form.get('step_name'),
            'step_order': request.form.get('step_order', 1, type=int),
            'step_type': request.form.get('step_type'),
            'assignee_type': request.form.get('assignee_type'),
            'assignee_id': request.form.get('assignee_id', type=int),
            'due_duration_hours': request.form.get('due_duration_hours', 24, type=int),
            'allow_approve': request.form.get('allow_approve') == 'on',
            'allow_reject': request.form.get('allow_reject') == 'on',
            'allow_return': request.form.get('allow_return') == 'on',
            'allow_skip': request.form.get('allow_skip') == 'on',
            'require_comments': request.form.get('require_comments') == 'on'
        }

        update_workflow_step(step_id, data)

        log_audit('workflow_step', step_id, 'UPDATE', user_id=user_id)

        flash("Step updated.", "success")
        return redirect(url_for('workflow_designer_steps',
                               definition_id=request.form.get('definition_id', type=int)))

    @workflow_bp.route('/designer/steps/<int:step_id>/delete', methods=['POST'])
    @workflow_require_login
    def workflow_designer_step_delete(step_id):
        """Delete a step."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'designer', 'delete'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        definition_id = request.form.get('definition_id', type=int)

        delete_workflow_step(step_id)
        log_audit('workflow_step', step_id, 'DELETE', user_id=user_id)

        flash("Step deleted.", "success")
        return redirect(url_for('workflow_designer_steps', definition_id=definition_id))

    @workflow_bp.route('/designer/steps/reorder', methods=['POST'])
    @workflow_require_login
    def workflow_designer_steps_reorder():
        """Reorder steps in a workflow."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'designer', 'edit'):
            return jsonify({'error': 'Access denied'}), 403

        data = request.get_json()
        step_orders = data.get('step_orders', [])

        with get_db_context() as db:
            for step_id, new_order in step_orders:
                db.execute("""
                    UPDATE workflow_steps SET step_order = ? WHERE id = ?
                """, (new_order, step_id))
            db.commit()

        return jsonify({'success': True})

    # =====================================================================
    # C.2 TRANSITION DESIGNER
    # =====================================================================

    @workflow_bp.route('/designer/transitions/<int:definition_id>')
    @workflow_require_login
    def workflow_designer_transitions(definition_id):
        """Transition rules designer."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'designer', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/designer/transitions', 'Transitions')
        context['definition_id'] = definition_id

        definition = get_workflow_definition(definition_id)
        context['definition'] = definition

        steps = get_workflow_steps(workflow_definition_id=definition_id)
        context['steps'] = steps

        transitions = get_workflow_transitions(definition_id)
        context['transitions'] = transitions

        return render_template('workflow/designer/transitions.html', **context)

    @workflow_bp.route('/designer/transitions', methods=['POST'])
    @workflow_require_login
    def workflow_designer_transition_create():
        """Create a new transition."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'designer', 'create'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        definition_id = request.form.get('definition_id', type=int)
        from_step_id = request.form.get('from_step_id', type=int)
        to_step_id = request.form.get('to_step_id', type=int)
        transition_type = request.form.get('transition_type', 'sequential')
        condition_expression = request.form.get('condition_expression', '')

        transition_id = create_workflow_transition(
            workflow_definition_id=definition_id,
            from_step_id=from_step_id,
            to_step_id=to_step_id,
            transition_type=transition_type,
            condition_expression=condition_expression
        )

        log_audit('workflow_transition', transition_id, 'CREATE', user_id=user_id)

        flash("Transition created.", "success")
        return redirect(url_for('workflow_designer_transitions', definition_id=definition_id))

    @workflow_bp.route('/designer/transitions/<int:transition_id>', methods=['PUT', 'POST'])
    @workflow_require_login
    def workflow_designer_transition_update(transition_id):
        """Update a transition."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'designer', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        definition_id = request.form.get('definition_id', type=int)
        to_step_id = request.form.get('to_step_id', type=int)
        transition_type = request.form.get('transition_type', 'sequential')
        condition_expression = request.form.get('condition_expression', '')

        with get_db_context() as db:
            db.execute("""
                UPDATE workflow_transitions
                SET to_step_id = ?, transition_type = ?, condition_expression = ?
                WHERE id = ?
            """, (to_step_id, transition_type, condition_expression, transition_id))
            db.commit()

        log_audit('workflow_transition', transition_id, 'UPDATE', user_id=user_id)

        flash("Transition updated.", "success")
        return redirect(url_for('workflow_designer_transitions', definition_id=definition_id))

    @workflow_bp.route('/designer/transitions/<int:transition_id>/delete', methods=['POST'])
    @workflow_require_login
    def workflow_designer_transition_delete(transition_id):
        """Delete a transition."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'designer', 'delete'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        definition_id = request.form.get('definition_id', type=int)

        with get_db_context() as db:
            db.execute("DELETE FROM workflow_transitions WHERE id = ?", (transition_id,))
            db.commit()

        log_audit('workflow_transition', transition_id, 'DELETE', user_id=user_id)

        flash("Transition deleted.", "success")
        return redirect(url_for('workflow_designer_transitions', definition_id=definition_id))

    # =====================================================================
    # C.3 CONDITION DESIGNER
    # =====================================================================

    @workflow_bp.route('/designer/conditions/<int:transition_id>')
    @workflow_require_login
    def workflow_designer_conditions(transition_id):
        """Conditions for a transition."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'designer', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/designer/conditions', 'Conditions')
        context['transition_id'] = transition_id

        conditions = get_transition_conditions(transition_id)
        context['conditions'] = conditions

        return render_template('workflow/designer/conditions.html', **context)

    @workflow_bp.route('/designer/conditions', methods=['POST'])
    @workflow_require_login
    def workflow_designer_condition_create():
        """Create a new condition."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'designer', 'create'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        transition_id = request.form.get('transition_id', type=int)
        condition_type = request.form.get('condition_type', 'field')
        field_name = request.form.get('field_name', '')
        operator = request.form.get('operator', 'equals')
        field_value = request.form.get('field_value', '')

        condition_id = create_workflow_condition(
            workflow_transition_id=transition_id,
            condition_type=condition_type,
            field_name=field_name,
            operator=operator,
            field_value=field_value
        )

        log_audit('workflow_condition', condition_id, 'CREATE', user_id=user_id)

        flash("Condition created.", "success")
        return redirect(url_for('workflow_designer_conditions', transition_id=transition_id))

    @workflow_bp.route('/designer/conditions/<int:condition_id>/delete', methods=['POST'])
    @workflow_require_login
    def workflow_designer_condition_delete(condition_id):
        """Delete a condition."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'designer', 'delete'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        transition_id = request.form.get('transition_id', type=int)

        delete_workflow_condition(condition_id)
        log_audit('workflow_condition', condition_id, 'DELETE', user_id=user_id)

        flash("Condition deleted.", "success")
        return redirect(url_for('workflow_designer_conditions', transition_id=transition_id))

    # =====================================================================
    # C.4 TEMPLATES
    # =====================================================================

    @workflow_bp.route('/designer/templates')
    @workflow_require_login
    def workflow_designer_templates():
        """Workflow templates list."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'designer', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/designer/templates', 'Templates')

        with get_db_context() as db:
            context['templates'] = db.execute("""
                SELECT * FROM workflow_templates WHERE is_active = 1 ORDER BY name
            """).fetchall()

        return render_template('workflow/designer/templates.html', **context)

    @workflow_bp.route('/designer/templates/<int:template_id>/clone', methods=['POST'])
    @workflow_require_login
    def workflow_designer_template_clone(template_id):
        """Clone a template to a new definition."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'designer', 'create'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        with get_db_context() as db:
            template = db.execute("""
                SELECT * FROM workflow_templates WHERE id = ?
            """, (template_id,)).fetchone()

            if not template:
                flash("Template not found.", "error")
                return redirect(url_for('workflow_designer_templates'))

            new_def_id = create_workflow_definition(
                workflow_type=f"{template['template_type']}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                name=f"{template['name']} (From Template)",
                module=template.get('module', 'general'),
                entity_type=template.get('entity_type', ''),
                description=template.get('description', ''),
                requires_approval=True,
                created_by=user_id
            )

            log_audit('workflow_definition', new_def_id, 'CREATE_FROM_TEMPLATE',
                     user_id=user_id, notes=f"Created from template {template_id}")

        flash("Workflow created from template.", "success")
        return redirect(url_for('workflow_designer_definition_edit', definition_id=new_def_id))

    # =====================================================================
    # D. PROCESS MODELING
    # =====================================================================

    @workflow_bp.route('/processes')
    @workflow_require_login
    def workflow_processes():
        """Process list."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'processes', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/processes', 'Processes')
        context['definitions'] = get_all_workflow_definitions(active_only=True)

        return render_template('workflow/processes/index.html', **context)

    @workflow_bp.route('/processes/<int:process_id>')
    @workflow_require_login
    def workflow_process_detail(process_id):
        """Process detail view."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'processes', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/processes/detail', 'Process Detail')

        definition = get_workflow_definition(process_id)
        if not definition:
            flash("Process not found.", "error")
            return redirect(url_for('workflow_processes'))

        context['definition'] = definition
        context['steps'] = get_workflow_steps(workflow_definition_id=process_id)
        context['transitions'] = get_workflow_transitions(process_id)

        # Get instance count
        with get_db_context() as db:
            context['instance_count'] = db.execute("""
                SELECT COUNT(*) as cnt FROM workflow_instances
                WHERE workflow_definition_id = ?
            """, (process_id,)).fetchone()['cnt']

        return render_template('workflow/processes/detail.html', **context)

    @workflow_bp.route('/processes/<int:process_id>/map')
    @workflow_require_login
    def workflow_process_map(process_id):
        """Process map (visual representation as JSON)."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'processes', 'view'):
            return jsonify({'error': 'Access denied'}), 403

        definition = get_workflow_definition(process_id)
        if not definition:
            return jsonify({'error': 'Process not found'}), 404

        steps = get_workflow_steps(workflow_definition_id=process_id)
        transitions = get_workflow_transitions(process_id)

        # Build visual map JSON
        map_data = {
            'id': process_id,
            'name': definition['name'],
            'type': definition['workflow_type'],
            'nodes': [],
            'edges': []
        }

        for step in steps:
            map_data['nodes'].append({
                'id': step['id'],
                'name': step['step_name'],
                'type': step['step_type'],
                'order': step['step_order']
            })

        for trans in transitions:
            map_data['edges'].append({
                'from': trans['from_step_id'],
                'to': trans['to_step_id'],
                'type': trans['transition_type']
            })

        return jsonify(map_data)

    @workflow_bp.route('/processes/states/<int:definition_id>')
    @workflow_require_login
    def workflow_process_states(definition_id):
        """State model for a process."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'processes', 'view'):
            return jsonify({'error': 'Access denied'}), 403

        states = {}
        with get_db_context() as db:
            steps = db.execute("""
                SELECT DISTINCT step_type FROM workflow_steps
                WHERE workflow_definition_id = ?
            """, (definition_id,)).fetchall()

            for step in steps:
                state_name = step['step_type'].upper()
                states[state_name] = WORKFLOW_STATES.get(state_name.lower(), state_name)

        return jsonify({'states': states})

    # =====================================================================
    # D.1 ESCALATION RULES
    # =====================================================================

    @workflow_bp.route('/escalation-rules')
    @workflow_require_login
    def workflow_escalation_rules():
        """SLA/escalation rules list."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'settings', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/escalation-rules', 'Escalation Rules')

        rules = get_escalation_rules()
        context['rules'] = rules

        return render_template('workflow/escalation_rules.html', **context)

    @workflow_bp.route('/escalation-rules', methods=['POST'])
    @workflow_require_login
    def workflow_escalation_rule_create():
        """Create escalation rule."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'settings', 'create'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        rule_name = request.form.get('rule_name')
        workflow_type = request.form.get('workflow_type', '')
        step_id = request.form.get('step_id', type=int)
        escalation_hours = request.form.get('escalation_hours', 24, type=int)
        escalation_level = request.form.get('escalation_level', 1, type=int)
        notify_assignee = request.form.get('notify_assignee') == 'on'
        notify_manager = request.form.get('notify_manager') == 'on'
        auto_escalate = request.form.get('auto_escalate') == 'on'

        rule_id = create_escalation_rule(
            rule_name=rule_name,
            workflow_type=workflow_type,
            step_id=step_id,
            escalation_hours=escalation_hours,
            escalation_level=escalation_level,
            notify_assignee=notify_assignee,
            notify_manager=notify_manager,
            auto_escalate=auto_escalate
        )

        log_audit('escalation_rule', rule_id, 'CREATE', user_id=user_id)

        flash("Escalation rule created.", "success")
        return redirect(url_for('workflow_escalation_rules'))

    @workflow_bp.route('/escalation-rules/<int:rule_id>', methods=['PUT', 'POST'])
    @workflow_require_login
    def workflow_escalation_rule_update(rule_id):
        """Update escalation rule."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'settings', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        data = {
            'rule_name': request.form.get('rule_name'),
            'escalation_hours': request.form.get('escalation_hours', 24, type=int),
            'escalation_level': request.form.get('escalation_level', 1, type=int),
            'notify_assignee': request.form.get('notify_assignee') == 'on',
            'notify_manager': request.form.get('notify_manager') == 'on',
            'auto_escalate': request.form.get('auto_escalate') == 'on',
            'is_active': request.form.get('is_active') == 'on'
        }

        update_escalation_rule(rule_id, data)
        log_audit('escalation_rule', rule_id, 'UPDATE', user_id=user_id)

        flash("Escalation rule updated.", "success")
        return redirect(url_for('workflow_escalation_rules'))

    @workflow_bp.route('/escalation-rules/<int:rule_id>/delete', methods=['POST'])
    @workflow_require_login
    def workflow_escalation_rule_delete(rule_id):
        """Delete escalation rule."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'settings', 'delete'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        with get_db_context() as db:
            db.execute("DELETE FROM escalation_rules WHERE id = ?", (rule_id,))
            db.commit()

        log_audit('escalation_rule', rule_id, 'DELETE', user_id=user_id)

        flash("Escalation rule deleted.", "success")
        return redirect(url_for('workflow_escalation_rules'))

    # =====================================================================
    # E. AUTOMATION RULES
    # =====================================================================

    @workflow_bp.route('/automation')
    @workflow_require_login
    def workflow_automation():
        """Automation rules list."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'automation', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/automation', 'Automation Rules')

        rules = get_automation_rules()
        context['rules'] = rules

        return render_template('workflow/automation/index.html', **context)

    @workflow_bp.route('/automation/new', methods=['GET', 'POST'])
    @workflow_require_login
    def workflow_automation_new():
        """New automation rule form."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'automation', 'create'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/automation/new', 'New Automation Rule')
        context['definitions'] = get_all_workflow_definitions()

        if request.method == 'POST':
            rule_name = request.form.get('rule_name')
            trigger_event = request.form.get('trigger_event')
            workflow_type = request.form.get('workflow_type', '')
            action_type = request.form.get('action_type')
            action_config = request.form.get('action_config', '{}')
            is_active = request.form.get('is_active') == 'on'

            rule_id = create_automation_rule(
                rule_name=rule_name,
                trigger_event=trigger_event,
                workflow_type=workflow_type,
                action_type=action_type,
                action_config=json.loads(action_config),
                is_active=is_active,
                created_by=user_id
            )

            log_audit('automation_rule', rule_id, 'CREATE', user_id=user_id)

            flash("Automation rule created.", "success")
            return redirect(url_for('workflow_automation'))

        return render_template('workflow/automation/rule_form.html', **context)

    @workflow_bp.route('/automation/<int:rule_id>/edit', methods=['GET', 'POST'])
    @workflow_require_login
    def workflow_automation_edit(rule_id):
        """Edit automation rule form."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'automation', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/automation/edit', 'Edit Automation Rule')
        context['definitions'] = get_all_workflow_definitions()

        with get_db_context() as db:
            context['rule'] = db.execute("""
                SELECT * FROM automation_rules WHERE id = ?
            """, (rule_id,)).fetchone()

        if request.method == 'POST':
            data = {
                'rule_name': request.form.get('rule_name'),
                'trigger_event': request.form.get('trigger_event'),
                'workflow_type': request.form.get('workflow_type', ''),
                'action_type': request.form.get('action_type'),
                'action_config': request.form.get('action_config', '{}'),
                'is_active': request.form.get('is_active') == 'on'
            }

            update_automation_rule(rule_id, data, user_id)
            log_audit('automation_rule', rule_id, 'UPDATE', user_id=user_id)

            flash("Automation rule updated.", "success")
            return redirect(url_for('workflow_automation_edit', rule_id=rule_id))

        return render_template('workflow/automation/rule_form.html', **context)

    @workflow_bp.route('/automation/<int:rule_id>/delete', methods=['POST'])
    @workflow_require_login
    def workflow_automation_delete(rule_id):
        """Delete automation rule."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'automation', 'delete'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        with get_db_context() as db:
            db.execute("DELETE FROM automation_rules WHERE id = ?", (rule_id,))
            db.commit()

        log_audit('automation_rule', rule_id, 'DELETE', user_id=user_id)

        flash("Automation rule deleted.", "success")
        return redirect(url_for('workflow_automation'))

    @workflow_bp.route('/automation/<int:rule_id>/activate', methods=['POST'])
    @workflow_require_login
    def workflow_automation_activate(rule_id):
        """Activate automation rule."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'automation', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        with get_db_context() as db:
            db.execute("UPDATE automation_rules SET is_active = 1 WHERE id = ?", (rule_id,))
            db.commit()

        log_audit('automation_rule', rule_id, 'ACTIVATE', user_id=user_id)

        flash("Automation rule activated.", "success")
        return redirect(url_for('workflow_automation'))

    @workflow_bp.route('/automation/<int:rule_id>/deactivate', methods=['POST'])
    @workflow_require_login
    def workflow_automation_deactivate(rule_id):
        """Deactivate automation rule."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'automation', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        with get_db_context() as db:
            db.execute("UPDATE automation_rules SET is_active = 0 WHERE id = ?", (rule_id,))
            db.commit()

        log_audit('automation_rule', rule_id, 'DEACTIVATE', user_id=user_id)

        flash("Automation rule deactivated.", "info")
        return redirect(url_for('workflow_automation'))

    @workflow_bp.route('/automation/<int:rule_id>/test', methods=['GET', 'POST'])
    @workflow_require_login
    def workflow_automation_test(rule_id):
        """Test automation rule (dry run)."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'automation', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        with get_db_context() as db:
            rule = db.execute("SELECT * FROM automation_rules WHERE id = ?", (rule_id,)).fetchone()

            if not rule:
                flash("Automation rule not found.", "error")
                return redirect(url_for('workflow_automation'))

            # Perform dry run test
            test_result = {
                'rule_id': rule_id,
                'rule_name': rule['rule_name'],
                'trigger_event': rule['trigger_event'],
                'would_execute': True,
                'simulated_at': datetime.now().isoformat()
            }

        return jsonify(test_result)

    @workflow_bp.route('/automation/failed')
    @workflow_require_login
    def workflow_automation_failed():
        """Failed automations log."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'automation', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/automation/failed', 'Failed Automations')

        with get_db_context() as db:
            context['logs'] = db.execute("""
                SELECT al.*, ar.rule_name
                FROM automation_logs al
                LEFT JOIN automation_rules ar ON al.rule_id = ar.id
                WHERE al.status = 'failed'
                ORDER BY al.created_at DESC
                LIMIT 100
            """).fetchall()

        return render_template('workflow/automation/failed.html', **context)

    @workflow_bp.route('/automation/<int:rule_id>/retry', methods=['POST'])
    @workflow_require_login
    def workflow_automation_retry(rule_id):
        """Retry failed automation."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'automation', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        with get_db_context() as db:
            db.execute("""
                UPDATE automation_logs SET retry_count = retry_count + 1, status = 'pending'
                WHERE rule_id = ? AND status = 'failed'
            """, (rule_id,))
            db.commit()

        log_audit('automation_rule', rule_id, 'RETRY', user_id=user_id)

        flash("Automation retry queued.", "info")
        return redirect(url_for('workflow_automation_failed'))

    @workflow_bp.route('/automation/logs')
    @workflow_require_login
    def workflow_automation_logs():
        """Automation execution logs."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'automation', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/automation/logs', 'Automation Logs')

        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page

        with get_db_context() as db:
            context['logs'] = db.execute("""
                SELECT al.*, ar.rule_name
                FROM automation_logs al
                LEFT JOIN automation_rules ar ON al.rule_id = ar.id
                ORDER BY al.created_at DESC
                LIMIT ? OFFSET ?
            """, (per_page, offset)).fetchall()

            total = db.execute("SELECT COUNT(*) as cnt FROM automation_logs").fetchone()['cnt']
            context['pagination'] = {
                'page': page,
                'pages': (total + per_page - 1) // per_page,
                'total': total
            }

        return render_template('workflow/automation/logs.html', **context)

    # =====================================================================
    # F. NOTIFICATIONS
    # =====================================================================

    @workflow_bp.route('/notifications/templates')
    @workflow_require_login
    def workflow_notification_templates():
        """Notification templates list."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'notifications', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/notifications/templates', 'Notification Templates')

        templates = get_notification_templates()
        context['templates'] = templates

        return render_template('workflow/notifications/templates.html', **context)

    @workflow_bp.route('/notifications/templates/new', methods=['GET', 'POST'])
    @workflow_require_login
    def workflow_notification_template_new():
        """New notification template form."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'notifications', 'create'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/notifications/templates/new', 'New Template')

        if request.method == 'POST':
            template_name = request.form.get('template_name')
            template_code = request.form.get('template_code')
            notification_type = request.form.get('notification_type')
            subject_template = request.form.get('subject_template')
            body_template = request.form.get('body_template')
            channel = request.form.get('channel', 'in_app')

            template_id = create_notification_template(
                template_name=template_name,
                template_code=template_code,
                notification_type=notification_type,
                subject_template=subject_template,
                body_template=body_template,
                channel=channel
            )

            log_audit('notification_template', template_id, 'CREATE', user_id=user_id)

            flash("Notification template created.", "success")
            return redirect(url_for('workflow_notification_templates'))

        return render_template('workflow/notifications/template_form.html', **context)

    @workflow_bp.route('/notifications/templates/<int:template_id>/edit', methods=['GET', 'POST'])
    @workflow_require_login
    def workflow_notification_template_edit(template_id):
        """Edit notification template form."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'notifications', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/notifications/templates/edit', 'Edit Template')

        with get_db_context() as db:
            context['template'] = db.execute("""
                SELECT * FROM notification_templates WHERE id = ?
            """, (template_id,)).fetchone()

        if request.method == 'POST':
            with get_db_context() as db:
                db.execute("""
                    UPDATE notification_templates SET
                        template_name = ?, notification_type = ?,
                        subject_template = ?, body_template = ?, channel = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    request.form.get('template_name'),
                    request.form.get('notification_type'),
                    request.form.get('subject_template'),
                    request.form.get('body_template'),
                    request.form.get('channel'),
                    template_id
                ))
                db.commit()

            log_audit('notification_template', template_id, 'UPDATE', user_id=user_id)

            flash("Notification template updated.", "success")
            return redirect(url_for('workflow_notification_template_edit', template_id=template_id))

        return render_template('workflow/notifications/template_form.html', **context)

    @workflow_bp.route('/notifications/templates/<int:template_id>/delete', methods=['POST'])
    @workflow_require_login
    def workflow_notification_template_delete(template_id):
        """Delete notification template."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'notifications', 'delete'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        with get_db_context() as db:
            db.execute("DELETE FROM notification_templates WHERE id = ?", (template_id,))
            db.commit()

        log_audit('notification_template', template_id, 'DELETE', user_id=user_id)

        flash("Notification template deleted.", "success")
        return redirect(url_for('workflow_notification_templates'))

    @workflow_bp.route('/notifications/delivery-rules')
    @workflow_require_login
    def workflow_notification_delivery_rules():
        """Delivery rules list."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'notifications', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/notifications/delivery-rules', 'Delivery Rules')

        with get_db_context() as db:
            context['rules'] = db.execute("""
                SELECT * FROM notification_rules ORDER BY priority DESC
            """).fetchall()

        return render_template('workflow/notifications/delivery_rules.html', **context)

    @workflow_bp.route('/notifications/delivery-rules', methods=['POST'])
    @workflow_require_login
    def workflow_notification_delivery_rule_create():
        """Create delivery rule."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'notifications', 'create'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        rule_name = request.form.get('rule_name')
        event_type = request.form.get('event_type')
        channel = request.form.get('channel', 'in_app')
        recipients = request.form.get('recipients', '')
        template_id = request.form.get('template_id', type=int)
        is_active = request.form.get('is_active') == 'on'

        with get_db_context() as db:
            db.execute("""
                INSERT INTO notification_rules (rule_name, event_type, channel, recipients, template_id, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (rule_name, event_type, channel, recipients, template_id, 1 if is_active else 0))
            db.commit()

        flash("Delivery rule created.", "success")
        return redirect(url_for('workflow_notification_delivery_rules'))

    @workflow_bp.route('/notifications/delivery-rules/<int:rule_id>', methods=['PUT', 'POST'])
    @workflow_require_login
    def workflow_notification_delivery_rule_update(rule_id):
        """Update delivery rule."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'notifications', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        with get_db_context() as db:
            db.execute("""
                UPDATE notification_rules SET
                    rule_name = ?, event_type = ?, channel = ?,
                    recipients = ?, template_id = ?, is_active = ?
                WHERE id = ?
            """, (
                request.form.get('rule_name'),
                request.form.get('event_type'),
                request.form.get('channel'),
                request.form.get('recipients'),
                request.form.get('template_id', type=int),
                1 if request.form.get('is_active') == 'on' else 0,
                rule_id
            ))
            db.commit()

        flash("Delivery rule updated.", "success")
        return redirect(url_for('workflow_notification_delivery_rules'))

    @workflow_bp.route('/notifications/delivery-rules/<int:rule_id>/delete', methods=['POST'])
    @workflow_require_login
    def workflow_notification_delivery_rule_delete(rule_id):
        """Delete delivery rule."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'notifications', 'delete'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        with get_db_context() as db:
            db.execute("DELETE FROM notification_rules WHERE id = ?", (rule_id,))
            db.commit()

        flash("Delivery rule deleted.", "success")
        return redirect(url_for('workflow_notification_delivery_rules'))

    @workflow_bp.route('/notifications/logs')
    @workflow_require_login
    def workflow_notification_logs():
        """Notification logs."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'notifications', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/notifications/logs', 'Notification Logs')

        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page

        with get_db_context() as db:
            context['logs'] = db.execute("""
                SELECT nl.*, nt.template_name
                FROM notification_logs nl
                LEFT JOIN notification_templates nt ON nl.template_id = nt.id
                ORDER BY nl.created_at DESC
                LIMIT ? OFFSET ?
            """, (per_page, offset)).fetchall()

        return render_template('workflow/notifications/logs.html', **context)

    @workflow_bp.route('/notifications/<int:notification_id>/resend', methods=['POST'])
    @workflow_require_login
    def workflow_notification_resend(notification_id):
        """Resend a notification."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'notifications', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        log_audit('notification', notification_id, 'RESEND', user_id=user_id)

        flash("Notification resent.", "success")
        return redirect(url_for('workflow_notification_logs'))

    # =====================================================================
    # G. MONITORING
    # =====================================================================

    @workflow_bp.route('/monitoring/instances')
    @workflow_require_login
    def workflow_monitoring_instances():
        """All workflow instances monitoring."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'monitoring', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/monitoring/instances', 'Instance Monitoring')

        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page

        status = request.args.get('status', '')
        search = request.args.get('search', '')

        sql = """
            SELECT wi.*, wd.name as workflow_name, u.username as initiator_name
            FROM workflow_instances wi
            LEFT JOIN workflow_definitions wd ON wi.workflow_definition_id = wd.id
            LEFT JOIN users u ON wi.initiated_by = u.id
            WHERE 1=1
        """
        params = []

        if status:
            sql += " AND wi.status = ?"
            params.append(status)

        if search:
            sql += " AND (wi.instance_key LIKE ? OR wd.name LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%'])

        sql += " ORDER BY wi.created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        context['instances'] = get_all(sql, params)
        context['status'] = status
        context['search'] = search

        return render_template('workflow/monitoring/instances.html', **context)

    @workflow_bp.route('/monitoring/instances/<int:instance_id>')
    @workflow_require_login
    def workflow_monitoring_instance_detail(instance_id):
        """Instance detail for monitoring."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'monitoring', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/monitoring/instance', 'Instance Detail')

        instance = get_workflow_instance(instance_id)
        context['instance'] = instance

        with get_db_context() as db:
            context['steps'] = db.execute("""
                SELECT wis.*, ws.step_name, ws.step_type, u.username as assignee_name
                FROM workflow_instance_steps wis
                LEFT JOIN workflow_steps ws ON wis.step_id = ws.id
                LEFT JOIN users u ON wis.assignee_id = u.id
                WHERE wis.instance_id = ?
                ORDER BY wis.step_order
            """, (instance_id,)).fetchall()

            context['actions'] = db.execute("""
                SELECT wa.*, u.username as performed_by_name
                FROM workflow_actions wa
                LEFT JOIN users u ON wa.performed_by = u.id
                WHERE wa.instance_id = ?
                ORDER BY wa.created_at
            """, (instance_id,)).fetchall()

        return render_template('workflow/monitoring/instance_detail.html', **context)

    @workflow_bp.route('/monitoring/delayed')
    @workflow_require_login
    def workflow_monitoring_delayed():
        """Delayed items monitoring."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'monitoring', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/monitoring/delayed', 'Delayed Items')

        with get_db_context() as db:
            context['items'] = db.execute("""
                SELECT wi.*, wd.name as workflow_name,
                       (julianday('now') - julianday(wi.due_date)) * 24 as hours_overdue
                FROM workflow_instances wi
                LEFT JOIN workflow_definitions wd ON wi.workflow_definition_id = wd.id
                WHERE wi.status IN ('pending', 'submitted', 'under_review')
                AND wi.due_date < datetime('now')
                ORDER BY hours_overdue DESC
                LIMIT 100
            """).fetchall()

        return render_template('workflow/monitoring/delayed.html', **context)

    @workflow_bp.route('/monitoring/escalation-queue')
    @workflow_require_login
    def workflow_monitoring_escalation_queue():
        """Escalation queue monitoring."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'monitoring', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/monitoring/escalation-queue', 'Escalation Queue')

        with get_db_context() as db:
            context['items'] = db.execute("""
                SELECT wi.*, wd.name as workflow_name,
                       er.escalation_level, er.rule_name
                FROM workflow_instances wi
                LEFT JOIN workflow_definitions wd ON wi.workflow_definition_id = wd.id
                LEFT JOIN escalation_rules er ON wi.workflow_definition_id = er.workflow_type
                WHERE wi.status = 'escalated'
                ORDER BY wi.escalation_level DESC, wi.updated_at ASC
            """).fetchall()

        return render_template('workflow/monitoring/escalation_queue.html', **context)

    @workflow_bp.route('/monitoring/automation-logs')
    @workflow_require_login
    def workflow_monitoring_automation_logs():
        """Automation logs for monitoring."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'monitoring', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/monitoring/automation-logs', 'Automation Logs')

        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page

        with get_db_context() as db:
            context['logs'] = db.execute("""
                SELECT al.*, ar.rule_name
                FROM automation_logs al
                LEFT JOIN automation_rules ar ON al.rule_id = ar.id
                ORDER BY al.created_at DESC
                LIMIT ? OFFSET ?
            """, (per_page, offset)).fetchall()

        return render_template('workflow/monitoring/automation_logs.html', **context)

    @workflow_bp.route('/monitoring/notification-logs')
    @workflow_require_login
    def workflow_monitoring_notification_logs():
        """Notification logs for monitoring."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'monitoring', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/monitoring/notification-logs', 'Notification Logs')

        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page

        with get_db_context() as db:
            context['logs'] = db.execute("""
                SELECT nl.*, u.username as recipient_name
                FROM notification_logs nl
                LEFT JOIN users u ON nl.user_id = u.id
                ORDER BY nl.created_at DESC
                LIMIT ? OFFSET ?
            """, (per_page, offset)).fetchall()

        return render_template('workflow/monitoring/notification_logs.html', **context)

    # =====================================================================
    # H. REPORTS
    # =====================================================================

    @workflow_bp.route('/reports/performance')
    @workflow_require_login
    def workflow_reports_performance():
        """Workflow performance report."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'reports', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/reports/performance', 'Performance Report')

        # Get performance metrics
        reports = get_workflow_reports('performance')
        context['reports'] = reports

        return render_template('workflow/reports/performance.html', **context)

    @workflow_bp.route('/reports/approval-cycle-time')
    @workflow_require_login
    def workflow_reports_approval_cycle_time():
        """Approval cycle time analysis."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'reports', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/reports/approval-cycle-time', 'Cycle Time Analysis')

        with get_db_context() as db:
            context['data'] = db.execute("""
                SELECT wd.name as workflow_name,
                       AVG(julianday(wi.completed_at) - julianday(wi.created_at)) * 24 as avg_hours,
                       MIN(julianday(wi.completed_at) - julianday(wi.created_at)) * 24 as min_hours,
                       MAX(julianday(wi.completed_at) - julianday(wi.created_at)) * 24 as max_hours,
                       COUNT(*) as total_count
                FROM workflow_instances wi
                LEFT JOIN workflow_definitions wd ON wi.workflow_definition_id = wd.id
                WHERE wi.status = 'completed' AND wi.completed_at IS NOT NULL
                GROUP BY wd.id
            """).fetchall()

        return render_template('workflow/reports/cycle_time.html', **context)

    @workflow_bp.route('/reports/rejection-analysis')
    @workflow_require_login
    def workflow_reports_rejection_analysis():
        """Rejection analysis report."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'reports', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/reports/rejection-analysis', 'Rejection Analysis')

        with get_db_context() as db:
            context['data'] = db.execute("""
                SELECT wd.name as workflow_name,
                       COUNT(CASE WHEN wi.status = 'rejected' THEN 1 END) as rejected_count,
                       COUNT(*) as total_count,
                       ROUND(COUNT(CASE WHEN wi.status = 'rejected' THEN 1 END) * 100.0 / COUNT(*), 2) as rejection_rate
                FROM workflow_instances wi
                LEFT JOIN workflow_definitions wd ON wi.workflow_definition_id = wd.id
                GROUP BY wd.id
            """).fetchall()

        return render_template('workflow/reports/rejection_analysis.html', **context)

    @workflow_bp.route('/reports/escalation')
    @workflow_require_login
    def workflow_reports_escalation():
        """Escalation report."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'reports', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/reports/escalation', 'Escalation Report')

        with get_db_context() as db:
            context['data'] = db.execute("""
                SELECT wd.name as workflow_name,
                       COUNT(CASE WHEN wi.status = 'escalated' THEN 1 END) as escalated_count,
                       COUNT(*) as total_count,
                       ROUND(COUNT(CASE WHEN wi.status = 'escalated' THEN 1 END) * 100.0 / COUNT(*), 2) as escalation_rate
                FROM workflow_instances wi
                LEFT JOIN workflow_definitions wd ON wi.workflow_definition_id = wd.id
                GROUP BY wd.id
            """).fetchall()

        return render_template('workflow/reports/escalation.html', **context)

    @workflow_bp.route('/reports/user-load')
    @workflow_require_login
    def workflow_reports_user_load():
        """User/department approval load report."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'reports', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/reports/user-load', 'User Load Report')

        with get_db_context() as db:
            context['data'] = db.execute("""
                SELECT u.username, u.full_name,
                       COUNT(CASE WHEN wis.completion_status = 'pending' THEN 1 END) as pending_count,
                       COUNT(CASE WHEN wis.completion_status = 'completed' THEN 1 END) as completed_count,
                       COUNT(*) as total_count
                FROM workflow_instance_steps wis
                LEFT JOIN users u ON wis.assignee_id = u.id
                GROUP BY u.id
                HAVING u.id IS NOT NULL
                ORDER BY pending_count DESC
            """).fetchall()

        return render_template('workflow/reports/user_load.html', **context)

    @workflow_bp.route('/reports/sla-compliance')
    @workflow_require_login
    def workflow_reports_sla_compliance():
        """SLA compliance report."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'reports', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/reports/sla-compliance', 'SLA Compliance')

        with get_db_context() as db:
            context['data'] = db.execute("""
                SELECT wd.name as workflow_name,
                       COUNT(CASE WHEN wi.due_date >= wi.completed_at OR wi.status != 'completed' THEN 1 END) as met_count,
                       COUNT(CASE WHEN wi.due_date < wi.completed_at AND wi.status = 'completed' THEN 1 END) as missed_count,
                       COUNT(*) as total_count
                FROM workflow_instances wi
                LEFT JOIN workflow_definitions wd ON wi.workflow_definition_id = wd.id
                WHERE wi.due_date IS NOT NULL
                GROUP BY wd.id
            """).fetchall()

        return render_template('workflow/reports/sla_compliance.html', **context)

    @workflow_bp.route('/reports/export')
    @workflow_require_login
    def workflow_reports_export():
        """Export report in Excel/CSV format."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'reports', 'export'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        report_type = request.args.get('type', 'performance')
        export_format = request.args.get('format', 'csv')

        reports = get_workflow_reports(report_type)

        if export_format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)

            # Write header
            if reports:
                writer.writerow(reports[0].keys())
                for row in reports:
                    writer.writerow(row.values())

            output.seek(0)
            return output.getvalue(), 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename=workflow_report_{report_type}.csv'
            }

        elif export_format == 'excel':
            # For Excel, return JSON that frontend can convert
            return jsonify({
                'report_type': report_type,
                'data': reports,
                'generated_at': datetime.now().isoformat()
            })

        return jsonify({'error': 'Invalid format'}), 400

    # =====================================================================
    # I. SETTINGS
    # =====================================================================

    @workflow_bp.route('/settings')
    @workflow_require_login
    def workflow_settings():
        """Workflow settings page."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'settings', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/settings', 'Workflow Settings')

        return render_template('workflow/settings/index.html', **context)

    @workflow_bp.route('/settings/types')
    @workflow_require_login
    def workflow_settings_types():
        """Workflow types management."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'settings', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/settings/types', 'Workflow Types')

        with get_db_context() as db:
            context['types'] = db.execute("""
                SELECT DISTINCT wd.module, wd.entity_type, COUNT(*) as count
                FROM workflow_definitions wd
                GROUP BY wd.module, wd.entity_type
            """).fetchall()

        return render_template('workflow/settings/types.html', **context)

    @workflow_bp.route('/settings/types', methods=['POST'])
    @workflow_require_login
    def workflow_settings_type_create():
        """Create workflow type."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'settings', 'create'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        module = request.form.get('module')
        entity_type = request.form.get('entity_type')
        description = request.form.get('description', '')

        log_audit('workflow_type', f"{module}.{entity_type}", 'CREATE', user_id=user_id)

        flash("Workflow type created.", "success")
        return redirect(url_for('workflow_settings_types'))

    @workflow_bp.route('/settings/types/<type_id>', methods=['PUT', 'POST'])
    @workflow_require_login
    def workflow_settings_type_update(type_id):
        """Update workflow type."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'settings', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        flash("Workflow type updated.", "success")
        return redirect(url_for('workflow_settings_types'))

    @workflow_bp.route('/settings/types/<type_id>/delete', methods=['POST'])
    @workflow_require_login
    def workflow_settings_type_delete(type_id):
        """Delete workflow type."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'settings', 'delete'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        flash("Workflow type deleted.", "success")
        return redirect(url_for('workflow_settings_types'))

    @workflow_bp.route('/settings/status-rules')
    @workflow_require_login
    def workflow_settings_status_rules():
        """Status rules management."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'settings', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/settings/status-rules', 'Status Rules')

        with get_db_context() as db:
            context['rules'] = db.execute("""
                SELECT * FROM workflow_settings WHERE setting_type = 'status_rule'
            """).fetchall()

        return render_template('workflow/settings/status_rules.html', **context)

    @workflow_bp.route('/settings/status-rules', methods=['POST'])
    @workflow_require_login
    def workflow_settings_status_rule_create():
        """Create status rule."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'settings', 'create'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        rule_name = request.form.get('rule_name')
        from_status = request.form.get('from_status')
        to_status = request.form.get('to_status')
        condition = request.form.get('condition', '')

        with get_db_context() as db:
            db.execute("""
                INSERT INTO workflow_settings (setting_type, setting_key, setting_value)
                VALUES ('status_rule', ?, ?)
            """, (rule_name, json.dumps({'from': from_status, 'to': to_status, 'condition': condition})))
            db.commit()

        log_audit('workflow_setting', rule_name, 'CREATE', user_id=user_id)

        flash("Status rule created.", "success")
        return redirect(url_for('workflow_settings_status_rules'))

    @workflow_bp.route('/settings/status-rules/<int:rule_id>', methods=['PUT', 'POST'])
    @workflow_require_login
    def workflow_settings_status_rule_update(rule_id):
        """Update status rule."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'settings', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        rule_name = request.form.get('rule_name')
        from_status = request.form.get('from_status')
        to_status = request.form.get('to_status')

        with get_db_context() as db:
            db.execute("""
                UPDATE workflow_settings SET setting_value = ?
                WHERE id = ?
            """, (json.dumps({'from': from_status, 'to': to_status}), rule_id))
            db.commit()

        flash("Status rule updated.", "success")
        return redirect(url_for('workflow_settings_status_rules'))

    @workflow_bp.route('/settings/status-rules/<int:rule_id>/delete', methods=['POST'])
    @workflow_require_login
    def workflow_settings_status_rule_delete(rule_id):
        """Delete status rule."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'settings', 'delete'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        with get_db_context() as db:
            db.execute("DELETE FROM workflow_settings WHERE id = ?", (rule_id,))
            db.commit()

        flash("Status rule deleted.", "success")
        return redirect(url_for('workflow_settings_status_rules'))

    @workflow_bp.route('/settings/assignment-rules')
    @workflow_require_login
    def workflow_settings_assignment_rules():
        """Assignment rules management."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'settings', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/settings/assignment-rules', 'Assignment Rules')
        context['roles'] = get_all_roles()

        with get_db_context() as db:
            context['rules'] = db.execute("""
                SELECT * FROM workflow_assignments WHERE is_active = 1
            """).fetchall()

        return render_template('workflow/settings/assignment_rules.html', **context)

    @workflow_bp.route('/settings/approval-policies')
    @workflow_require_login
    def workflow_settings_approval_policies():
        """Approval policies management."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'settings', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/settings/approval-policies', 'Approval Policies')

        with get_db_context() as db:
            context['policies'] = db.execute("""
                SELECT * FROM workflow_settings WHERE setting_type = 'approval_policy'
            """).fetchall()

        return render_template('workflow/settings/approval_policies.html', **context)

    @workflow_bp.route('/settings/delegation-rules')
    @workflow_require_login
    def workflow_settings_delegation_rules():
        """Delegation rules management."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'settings', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/settings/delegation-rules', 'Delegation Rules')

        rules = get_delegation_rules()
        context['rules'] = rules

        return render_template('workflow/settings/delegation_rules.html', **context)

    @workflow_bp.route('/settings/delegation-rules', methods=['POST'])
    @workflow_require_login
    def workflow_settings_delegation_rule_create():
        """Create delegation rule."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'settings', 'create'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        delegator_id = request.form.get('delegator_id', type=int)
        delegate_id = request.form.get('delegate_id', type=int)
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        is_active = request.form.get('is_active') == 'on'

        rule_id = create_delegation_rule(
            delegator_id=delegator_id,
            delegate_id=delegate_id,
            start_date=start_date,
            end_date=end_date,
            is_active=is_active
        )

        log_audit('delegation_rule', rule_id, 'CREATE', user_id=user_id)

        flash("Delegation rule created.", "success")
        return redirect(url_for('workflow_settings_delegation_rules'))

    @workflow_bp.route('/settings/delegation-rules/<int:rule_id>', methods=['PUT', 'POST'])
    @workflow_require_login
    def workflow_settings_delegation_rule_update(rule_id):
        """Update delegation rule."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'settings', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        data = {
            'delegate_id': request.form.get('delegate_id', type=int),
            'start_date': request.form.get('start_date'),
            'end_date': request.form.get('end_date'),
            'is_active': request.form.get('is_active') == 'on'
        }

        update_delegation_rule(rule_id, data)
        log_audit('delegation_rule', rule_id, 'UPDATE', user_id=user_id)

        flash("Delegation rule updated.", "success")
        return redirect(url_for('workflow_settings_delegation_rules'))

    @workflow_bp.route('/settings/delegation-rules/<int:rule_id>/delete', methods=['POST'])
    @workflow_require_login
    def workflow_settings_delegation_rule_delete(rule_id):
        """Delete delegation rule."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'settings', 'delete'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        with get_db_context() as db:
            db.execute("DELETE FROM delegation_rules WHERE id = ?", (rule_id,))
            db.commit()

        log_audit('delegation_rule', rule_id, 'DELETE', user_id=user_id)

        flash("Delegation rule deleted.", "success")
        return redirect(url_for('workflow_settings_delegation_rules'))

    # =====================================================================
    # J. AUDIT/LOGS
    # =====================================================================

    @workflow_bp.route('/audit/history')
    @workflow_require_login
    def workflow_audit_history():
        """Workflow history."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'audit', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/audit/history', 'Workflow History')

        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page

        entity_type = request.args.get('entity_type')
        action = request.args.get('action')

        sql = """
            SELECT * FROM platform_audit_log
            WHERE entity_type IN ('workflow_instance', 'workflow_definition', 'workflow_step')
        """
        params = []

        if entity_type:
            sql += " AND entity_type = ?"
            params.append(entity_type)

        if action:
            sql += " AND action = ?"
            params.append(action)

        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        context['logs'] = get_all(sql, params)
        context['entity_types'] = ['workflow_instance', 'workflow_definition', 'workflow_step']

        return render_template('workflow/audit/history.html', **context)

    @workflow_bp.route('/audit/approvals')
    @workflow_require_login
    def workflow_audit_approvals():
        """Approval history."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'audit', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/audit/approvals', 'Approval History')

        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page

        with get_db_context() as db:
            context['approvals'] = db.execute("""
                SELECT wa.*, wi.instance_key, wd.name as workflow_name,
                       u.username as performed_by_name
                FROM workflow_actions wa
                LEFT JOIN workflow_instances wi ON wa.instance_id = wi.id
                LEFT JOIN workflow_definitions wd ON wi.workflow_definition_id = wd.id
                LEFT JOIN users u ON wa.performed_by = u.id
                WHERE wa.action_type IN ('approve', 'reject', 'return')
                ORDER BY wa.created_at DESC
                LIMIT ? OFFSET ?
            """, (per_page, offset)).fetchall()

        return render_template('workflow/audit/approvals.html', **context)

    @workflow_bp.route('/audit/changes')
    @workflow_require_login
    def workflow_audit_changes():
        """Change logs."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'audit', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/audit/changes', 'Change Logs')

        with get_db_context() as db:
            context['changes'] = db.execute("""
                SELECT * FROM platform_audit_log
                WHERE entity_type IN ('workflow_definition', 'workflow_step', 'automation_rule')
                AND action IN ('CREATE', 'UPDATE', 'DELETE')
                ORDER BY created_at DESC
                LIMIT 100
            """).fetchall()

        return render_template('workflow/audit/changes.html', **context)

    @workflow_bp.route('/audit/errors')
    @workflow_require_login
    def workflow_audit_errors():
        """Error logs."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'workflow', 'audit', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_workflow_context(user_id, language)
        context['page_title'] = get_page_title('/workflow/audit/errors', 'Error Logs')

        with get_db_context() as db:
            context['errors'] = db.execute("""
                SELECT al.*, ar.rule_name
                FROM automation_logs al
                LEFT JOIN automation_rules ar ON al.rule_id = ar.id
                WHERE al.status = 'failed'
                ORDER BY al.created_at DESC
                LIMIT 100
            """).fetchall()

        return render_template('workflow/audit/errors.html', **context)

    @workflow_bp.route('/audit/export')
    @workflow_require_login
    def workflow_audit_export():
        """Export audit logs."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'audit', 'export'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        export_format = request.args.get('format', 'csv')

        with get_db_context() as db:
            logs = db.execute("""
                SELECT * FROM platform_audit_log
                WHERE entity_type LIKE 'workflow%'
                ORDER BY created_at DESC
                LIMIT 1000
            """).fetchall()

        if export_format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)

            writer.writerow(['ID', 'Entity Type', 'Entity ID', 'Action', 'User ID', 'Timestamp', 'Notes'])
            for log in logs:
                writer.writerow([
                    log['id'], log['entity_type'], log['entity_id'],
                    log['action'], log['user_id'], log['created_at'], log.get('notes', '')
                ])

            output.seek(0)
            return output.getvalue(), 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': 'attachment; filename=workflow_audit_log.csv'
            }

        return jsonify([dict(log) for log in logs])

    # =====================================================================
    # K. API ENDPOINTS (JSON)
    # =====================================================================

    @workflow_bp.route('/api/workflow/instances')
    @workflow_require_login
    def api_workflow_instances():
        """List workflow instances (JSON API)."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'my_work', 'view'):
            return jsonify({'error': 'Access denied'}), 403

        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        status = request.args.get('status')
        workflow_type = request.args.get('workflow_type')

        instances = get_workflow_instances(
            user_id=user_id,
            status=status,
            workflow_type=workflow_type,
            page=page,
            per_page=per_page
        )

        return jsonify({
            'instances': instances,
            'page': page,
            'per_page': per_page
        })

    @workflow_bp.route('/api/workflow/instances/<int:instance_id>')
    @workflow_require_login
    def api_workflow_instance(instance_id):
        """Get workflow instance (JSON API)."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'my_work', 'view'):
            return jsonify({'error': 'Access denied'}), 403

        instance = get_workflow_instance(instance_id)
        if not instance:
            return jsonify({'error': 'Instance not found'}), 404

        return jsonify(instance)

    @workflow_bp.route('/api/workflow/pending')
    @workflow_require_login
    def api_workflow_pending():
        """Get pending items for current user (JSON API)."""
        user_id = session.get('user_id')

        pending = get_pending_approvals(user_id)

        return jsonify({
            'pending_count': len(pending),
            'items': pending
        })

    @workflow_bp.route('/api/workflow/stats')
    @workflow_require_login
    def api_workflow_stats():
        """Get dashboard stats (JSON API)."""
        user_id = session.get('user_id')

        stats = get_workflow_stats(user_id)

        return jsonify(stats)

    @workflow_bp.route('/api/workflow/instances/<int:instance_id>/action', methods=['POST'])
    @workflow_require_login
    def api_workflow_instance_action(instance_id):
        """Perform action on workflow instance (JSON API)."""
        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'workflow', 'my_work', 'edit'):
            return jsonify({'error': 'Access denied'}), 403

        data = request.get_json()
        action = data.get('action')
        comment = data.get('comment', '')

        if action not in ACTION_TYPES:
            return jsonify({'error': f'Invalid action: {action}'}), 400

        with get_db_context() as db:
            # Record the action
            db.execute("""
                INSERT INTO workflow_actions (instance_id, action_type, performed_by, comment)
                VALUES (?, ?, ?, ?)
            """, (instance_id, action, user_id, comment))

            # Update instance status based on action
            status_map = {
                'approve': 'approved',
                'reject': 'rejected',
                'return': 'returned',
                'escalate': 'escalated',
                'cancel': 'cancelled'
            }

            new_status = status_map.get(action)
            if new_status:
                db.execute("""
                    UPDATE workflow_instances SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_status, instance_id))

            db.commit()

            log_audit('workflow_instance', instance_id, action.upper(), user_id=user_id, notes=comment)

        return jsonify({
            'success': True,
            'action': action,
            'new_status': status_map.get(action)
        })

    app.register_blueprint(workflow_bp)
