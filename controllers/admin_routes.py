"""
Centralized Administration Routes
================================
This module provides all routes for the Settings and Administration module.

ROUTE STRUCTURE:
- /admin/ - Main administration dashboard
- /admin/settings/ - Settings management
- /admin/master-data/ - Master data management
- /admin/users/ - User management
- /admin/roles/ - Role and permission management
- /admin/numbering/ - Numbering rules
- /admin/workflows/ - Workflow and approval management
- /admin/notifications/ - Notification rules
- /admin/audit/ - Audit logs

USAGE:
    from admin_routes import register_admin_routes
    register_admin_routes(app)
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
import json

from database import (
    get_db, get_db_context, get_one, get_all,
    log_audit, get_user_notifications
)
from permissions import (
    user_has_permission, get_user_permissions, get_role_permissions,
    require_permission, get_all_roles, get_role_by_id,
    MODULE_PERMISSIONS
)
from admin_settings import (
    ADMIN_CATEGORIES, MASTER_DATA_TYPES, NUMBERING_RULES,
    WORKFLOW_TEMPLATES, SCOPE_LEVELS,
    get_setting, set_setting, get_settings_by_category,
    get_settings_scoped, get_master_data, get_master_data_record,
    create_master_data, update_master_data, delete_master_data,
    get_numbering_rule, get_all_numbering_rules, save_numbering_rule,
    generate_next_number,
    get_workflow, get_all_workflows, get_workflow_steps, save_workflow,
    get_settings_history
)
from navigation import (
    get_main_menu, get_breadcrumbs, get_page_title,
    prepare_menu_for_template
)
from theme_engine import get_available_themes

# Note: CSRF protection is applied inline within route handlers where needed
# to avoid circular import issues with app.py


def register_admin_routes(app):
    """Register all admin routes with the Flask app."""

    # Ensure date filter is registered (may already be registered in app.py,
    # but we add it here as a safety measure for when admin_routes is used
    # with a different app factory that doesn't register it)
    import datetime
    if 'date' not in app.jinja_env.filters:
        @app.template_filter('date')
        def _date_filter(value, format='%Y-%m-%d'):
            """Format date - handles 'now' string, datetime objects, and ISO date strings."""
            if value == 'now' or value is None:
                return datetime.datetime.now().strftime(format)
            if isinstance(value, str):
                try:
                    value = datetime.datetime.fromisoformat(value)
                except ValueError:
                    try:
                        value = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                    except ValueError:
                        return value
            if isinstance(value, (datetime.datetime, datetime.date)):
                return value.strftime(format)
            return value

    # =====================================================================
    # HELPER DECORATORS
    # =====================================================================
    
    def admin_require_login(f):
        """Decorator requiring authentication."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    
    def admin_require_permission(module, resource, action):
        """Decorator requiring specific permission."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                user_id = session.get('user_id')
                if not user_id:
                    return redirect(url_for('login'))
                if not user_has_permission(user_id, module, resource, action):
                    flash(f"Access denied. You need '{action}' permission on '{resource}'.", "error")
                    return redirect(url_for('index'))
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    # =====================================================================
    # MAIN ADMIN DASHBOARD
    # =====================================================================
    
    @app.route('/admin')
    @app.route('/admin/dashboard')
    @admin_require_login
    def admin_dashboard():
        """Main administration dashboard."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')
        
        context = _get_admin_context(user_id, language)
        context['page_title'] = get_page_title('/admin/dashboard', 'Administration')
        
        # Add dashboard stats
        context['stats'] = _get_admin_stats()
        
        return render_template('admin/dashboard.html', **context)
    
    # =====================================================================
    # GENERAL SETTINGS
    # =====================================================================
    
    @app.route('/admin/settings')
    @app.route('/admin/settings/')
    @admin_require_login
    def admin_settings():
        """Main settings page with category overview."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')
        
        if not user_has_permission(user_id, 'platform', 'settings', 'view'):
            flash("Access denied to settings.", "error")
            return redirect(url_for('index'))
        
        context = _get_admin_context(user_id, language)
        context['page_title'] = 'System Settings'
        context['categories'] = ADMIN_CATEGORIES
        
        return render_template('admin/settings/index.html', **context)
    
    # Safe table names for admin routes - used to prevent SQL injection
    _ALLOWED_TABLE_NAMES = {
        'companies', 'branches', 'departments', 'divisions', 'teams', 'warehouses',
        'users', 'roles', 'permissions', 'settings', 'notifications',
        'documents', 'document_categories', 'workflows', 'approvals'
    }

    # Helper functions for safe DB access
    def _safe_count(table_name):
        """Safe row count that handles missing tables with table name validation."""
        import logging
        _logger = logging.getLogger('admin_routes')

        # Validate table name against allowlist to prevent SQL injection
        if table_name not in _ALLOWED_TABLE_NAMES:
            _logger.warning(f"Table '{table_name}' is not in the allowed list - rejecting")
            return 0

        try:
            result = get_one(f"SELECT COUNT(*) as cnt FROM {table_name} WHERE is_active = 1")
            return result['cnt'] if result else 0
        except Exception as e:
            _logger.warning(f"Table '{table_name}' does not exist or query failed: {e}")
            return 0

    def _get_all_safe(sql, params=None):
        """Safe get_all that handles table not existing."""
        import logging
        _logger = logging.getLogger('admin_routes')
        try:
            return get_all(sql, params) if params else get_all(sql)
        except Exception as e:
            _logger.warning(f"Query failed: {e}")
            return []

    @app.route('/admin/settings/<category>')
    @admin_require_login
    def admin_settings_category(category):
        """Settings page for a specific category."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        # Super admin bypass
        if session.get('role_name') == 'Global Admin':
            pass  # Continue to settings
        elif not user_has_permission(user_id, 'platform', 'settings', 'view'):
            flash("Access denied to settings.", "error")
            return redirect(url_for('index'))

        context = _get_admin_context(user_id, language)
        context['page_title'] = ADMIN_CATEGORIES.get(category.upper(), {}).get('label', category)
        context['category_key'] = category.upper()
        context['category_info'] = ADMIN_CATEGORIES.get(category.upper(), {})
        
        # Load settings for this category
        context['settings'] = get_settings_by_category(category.upper())
        context['default_settings'] = _get_default_settings_for_category(category.upper())
        # Always provide stats to avoid undefined errors in template
        context['stats'] = {}

        # Add sample data for AUDIT category dashboard
        if category.upper() == 'AUDIT':
            context['sample_data'] = {
                'security_events': '247',
                'logs_today': '1,847',
                'failed_logins': '23',
                'compliance_score': '94%'
            }

        # Add ORGANIZATION data — companies, branches, departments, divisions, teams, warehouses
        if category.upper() == 'ORGANIZATION':
            context['stats'] = {
                'companies': _safe_count('companies'),
                'branches': _safe_count('branches'),
                'departments': _safe_count('departments'),
                'divisions': _safe_count('divisions'),
                'teams': _safe_count('teams'),
                'warehouses': _safe_count('warehouses'),
            }
            context['org_companies'] = _get_all_safe("""
                SELECT c.*,
                    (SELECT COUNT(*) FROM branches WHERE company_id = c.id) as branch_count
                FROM companies c ORDER BY c.name
            """)
            context['org_branches'] = _get_all_safe("""
                SELECT b.*, c.name as company_name
                FROM branches b
                LEFT JOIN companies c ON b.company_id = c.id
                ORDER BY b.name
            """)
            context['org_departments'] = _get_all_safe("""
                SELECT d.*,
                    (SELECT COUNT(*) FROM departments d2 WHERE d2.parent_department_id = d.id) as sub_count,
                    c.name as company_name
                FROM departments d
                LEFT JOIN companies c ON d.company_id = c.id
                ORDER BY d.name
            """)
            context['org_divisions'] = _get_all_safe("""
                SELECT d.*, c.name as company_name
                FROM divisions d
                LEFT JOIN companies c ON d.company_id = c.id
                WHERE d.is_active = 1 ORDER BY d.name
            """)
            context['org_warehouses'] = _get_all_safe("""
                SELECT w.*, c.name as company_name
                FROM warehouses w
                LEFT JOIN companies c ON w.company_id = c.id
                ORDER BY w.name
            """)
            context['org_teams'] = _get_all_safe("""
                SELECT t.*, d.name as department_name
                FROM teams t
                LEFT JOIN departments d ON t.department_id = d.id
                ORDER BY t.name
            """)

        # Handle form submission
        if request.method == 'POST':
            _handle_settings_save(category.upper(), user_id)
            flash("Settings saved successfully.", "success")
            return redirect(url_for('admin_settings_category', category=category))
        
        return render_template('admin/settings/category.html', **context)

    @app.route('/admin/settings/ROLES')
    @admin_require_login
    def admin_settings_roles():
        """Dedicated Roles & Permissions management page with full SAP-style UI."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if session.get('role_name') != 'Global Admin':
            if not user_has_permission(user_id, 'platform', 'roles', 'view'):
                flash("Access denied.", "error")
                return redirect(url_for('index'))

        context = _get_admin_context(user_id, language)
        context['page_title'] = 'Roles & Permissions'
        context['category_key'] = 'ROLES'
        context['category_info'] = ADMIN_CATEGORIES.get('ROLES', {})

        # Get all roles with counts
        all_roles = get_all("""
            SELECT r.*,
                   (SELECT COUNT(*) FROM users WHERE role_id = r.id AND is_active = 1) as user_count,
                   (SELECT COUNT(*) FROM role_permissions WHERE role_id = r.id) as permission_count,
                   c.name as company_name
            FROM roles r
            LEFT JOIN companies c ON r.company_id = c.id
            WHERE r.is_active = 1
            ORDER BY r.role_group, r.role_name
        """)

        context['all_roles'] = all_roles

        # Get role summary stats
        context['roles_summary'] = {
            'total': len(all_roles),
            'active': len([r for r in all_roles if r.get('is_active')]),
            'system': len([r for r in all_roles if r.get('is_system')]),
            'custom': len([r for r in all_roles if not r.get('is_system')]),
            'users_assigned': sum(r.get('user_count', 0) for r in all_roles)
        }

        context['companies'] = get_all("SELECT * FROM companies WHERE is_active = 1 ORDER BY name")
        context['modules'] = MODULE_PERMISSIONS

        # Get selected role from query param or default to first
        selected_role_id = request.args.get('role', type=int)
        selected_role = None
        if selected_role_id:
            selected_role = get_one("""
                SELECT r.*, c.name as company_name
                FROM roles r
                LEFT JOIN companies c ON r.company_id = c.id
                WHERE r.id = ? AND r.is_active = 1
            """, (selected_role_id,))
        elif all_roles:
            selected_role = all_roles[0]
            selected_role_id = selected_role['id']

        context['selected_role'] = selected_role

        # Get users assigned to selected role
        role_users = []
        if selected_role_id:
            role_users = get_all("""
                SELECT u.id, u.user_name, u.login_name, u.department, u.is_active
                FROM users u
                WHERE u.role_id = ?
                ORDER BY u.user_name
            """, (selected_role_id,))
        context['role_users'] = role_users

        # Get permissions for selected role
        role_permissions = []
        if selected_role_id:
            perms = get_all("""
                SELECT module, resource, GROUP_CONCAT(action) as actions
                FROM role_permissions
                WHERE role_id = ?
                GROUP BY module, resource
            """, (selected_role_id,))
            role_permissions = [{'module': p['module'], 'resource': p['resource'], 'actions': p['actions'].split(',') if p['actions'] else []} for p in perms]
        context['role_permissions'] = role_permissions

        # Get audit log for selected role
        role_audit_log = []
        if selected_role_id:
            role_audit_log = get_all("""
                SELECT pal.*, u.user_name
                FROM platform_audit_log pal
                LEFT JOIN users u ON pal.user_id = u.id
                WHERE pal.entity_type = 'role' AND pal.entity_id = ?
                ORDER BY pal.created_at DESC
                LIMIT 50
            """, (str(selected_role_id),))
        context['role_audit_log'] = role_audit_log

        return render_template('admin/settings/roles.html', **context)

    @app.route('/admin/api/settings', methods=['GET', 'POST'])
    @admin_require_login
    def admin_api_settings():
        """API endpoint for settings operations."""
        user_id = session.get('user_id')

        if request.method == 'POST':
            # Validate CSRF for POST requests
            from app import validate_csrf_token
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
            if not validate_csrf_token(token):
                return jsonify({'error': 'CSRF token required'}), 403

            if not user_has_permission(user_id, 'platform', 'settings', 'edit'):
                return jsonify({'error': 'Access denied'}), 403

            data = request.get_json()
            key = data.get('key')
            value = data.get('value')
            category = data.get('category', 'GENERAL')

            if not key:
                return jsonify({'error': 'Key is required'}), 400

            success = set_setting(key, value, category, 'GLOBAL', None, None, user_id)

            if success:
                return jsonify({'success': True})
            else:
                return jsonify({'error': 'Failed to save setting'}), 500

        # GET - return all settings
        settings = get_settings_by_category(request.args.get('category', 'GENERAL'))
        return jsonify(settings)
    
    @app.route('/admin/api/settings/bulk', methods=['POST'])
    @admin_require_login
    def admin_api_settings_bulk():
        """Bulk save multiple settings."""
        # Validate CSRF for POST requests
        from app import validate_csrf_token
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        if not validate_csrf_token(token):
            return jsonify({'error': 'CSRF token required'}), 403

        user_id = session.get('user_id')
        
        if not user_has_permission(user_id, 'platform', 'settings', 'edit'):
            return jsonify({'error': 'Access denied'}), 403
        
        data = request.get_json()
        settings_dict = data.get('settings', {})
        category = data.get('category', 'GENERAL')
        
        results = {}
        for key, value in settings_dict.items():
            results[key] = set_setting(key, value, category, 'GLOBAL', None, None, user_id)
        
        return jsonify({'success': all(results.values()), 'results': results})
    
    # =====================================================================
    # MASTER DATA MANAGEMENT
    # =====================================================================
    
    @app.route('/admin/master-data')
    @admin_require_login
    def admin_master_data():
        """Master data management overview."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')
        
        if not user_has_permission(user_id, 'platform', 'settings', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))
        
        context = _get_admin_context(user_id, language)
        context['page_title'] = 'Master Data'
        context['master_data_types'] = MASTER_DATA_TYPES
        
        return render_template('admin/master_data/index.html', **context)
    
    @app.route('/admin/master-data/<md_type>')
    @admin_require_login
    def admin_master_data_type(md_type):
        """List records for a specific master data type."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')
        
        if not user_has_permission(user_id, 'platform', 'settings', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))
        
        if md_type not in MASTER_DATA_TYPES:
            flash("Invalid master data type.", "error")
            return redirect(url_for('admin_master_data'))
        
        context = _get_admin_context(user_id, language)
        context['page_title'] = MASTER_DATA_TYPES[md_type]['label_plural']
        context['md_type'] = md_type
        context['md_info'] = MASTER_DATA_TYPES[md_type]
        context['records'] = get_master_data(md_type, is_active=True)
        
        # Handle form submission for create/edit
        if request.method == 'POST':
            action = request.form.get('action')
            
            if action == 'create':
                _handle_master_data_create(md_type, user_id)
                flash("Record created successfully.", "success")
            elif action == 'edit':
                record_id = request.form.get('id')
                _handle_master_data_update(md_type, record_id, user_id)
                flash("Record updated successfully.", "success")
            elif action == 'delete':
                record_id = request.form.get('id')
                delete_master_data(md_type, record_id)
                flash("Record deleted.", "success")
            
            return redirect(url_for('admin_master_data_type', md_type=md_type))
        
        return render_template('admin/master_data/type.html', **context)
    
    @app.route('/admin/api/master-data/<md_type>', methods=['GET', 'POST', 'PUT', 'DELETE'])
    @admin_require_login
    def admin_api_master_data(md_type):
        """API for master data CRUD operations."""
        user_id = session.get('user_id')

        if request.method in ('POST', 'PUT', 'DELETE'):
            # Validate CSRF for mutating requests
            from app import validate_csrf_token
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
            if not validate_csrf_token(token):
                return jsonify({'error': 'CSRF token required'}), 403

            if not user_has_permission(user_id, 'platform', 'settings', 'edit'):
                return jsonify({'error': 'Access denied'}), 403

        if request.method == 'GET':
            record_id = request.args.get('id')
            if record_id:
                record = get_master_data_record(md_type, record_id)
                return jsonify(record) if record else jsonify({'error': 'Not found'}), 404
            else:
                records = get_master_data(md_type, is_active=True)
                return jsonify(records)

        data = request.get_json()

        if request.method == 'POST':
            record_id, error = create_master_data(md_type, data, user_id)
            if error:
                return jsonify({'error': error}), 400
            return jsonify({'success': True, 'id': record_id})

        elif request.method == 'PUT':
            record_id = data.get('id')
            if not record_id:
                return jsonify({'error': 'ID is required'}), 400
            success, error = update_master_data(md_type, record_id, data, user_id)
            if error:
                return jsonify({'error': error}), 400
            return jsonify({'success': True})

        elif request.method == 'DELETE':
            record_id = data.get('id')
            if not record_id:
                return jsonify({'error': 'ID is required'}), 400
            success, error = delete_master_data(md_type, record_id)
            if error:
                return jsonify({'error': error}), 400
            return jsonify({'success': True})
    
    # =====================================================================
    # NUMBERING RULES
    # =====================================================================
    
    @app.route('/admin/numbering')
    @admin_require_login
    def admin_numbering():
        """Numbering rules management."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')
        
        if not user_has_permission(user_id, 'platform', 'settings', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))
        
        context = _get_admin_context(user_id, language)
        context['page_title'] = 'Numbering & Code Rules'
        context['rules'] = get_all_numbering_rules()
        context['rule_definitions'] = NUMBERING_RULES
        context['settings'] = get_settings_by_category('NUMBERING')
        
        if request.method == 'POST':
            rule_type = request.form.get('rule_type')
            prefix = request.form.get('prefix')
            padding = request.form.get('padding', 5)
            suffix = request.form.get('suffix', '')
            use_company = request.form.get('use_company_prefix') == 'on'
            use_branch = request.form.get('use_branch_prefix') == 'on'
            
            save_numbering_rule(
                rule_type, prefix, int(padding), 'YEARLY',
                use_company, use_branch, suffix, user_id
            )
            flash("Numbering rule saved.", "success")
            return redirect(url_for('admin_numbering'))
        
        return render_template('admin/numbering.html', **context)
    
    @app.route('/admin/api/numbering/<rule_type>/preview')
    @admin_require_login
    def admin_api_numbering_preview(rule_type):
        """Preview what the next number would look like."""
        rule = get_numbering_rule(rule_type)
        if not rule:
            return jsonify({'error': 'Rule not found'}), 404
        
        # Generate preview (not actual increment)
        preview = f"{rule['prefix']}{'0'.zfill(rule['padding'])}{rule['suffix']}"
        
        return jsonify({
            'rule_type': rule_type,
            'preview': preview,
            'prefix': rule['prefix'],
            'padding': rule['padding'],
            'suffix': rule['suffix']
        })
    
    # =====================================================================
    # WORKFLOWS & APPROVALS
    # =====================================================================
    
    @app.route('/admin/workflows')
    @admin_require_login
    def admin_workflows():
        """Workflow and approval management."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')
        
        if not user_has_permission(user_id, 'platform', 'settings', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))
        
        context = _get_admin_context(user_id, language)
        context['page_title'] = 'Workflow & Approvals'
        context['workflows'] = get_all_workflows()
        context['workflow_templates'] = WORKFLOW_TEMPLATES
        context['roles'] = get_all_roles()
        
        if request.method == 'POST':
            wf_type = request.form.get('workflow_type')
            module = request.form.get('module')
            label = request.form.get('label')
            requires_approval = request.form.get('requires_approval') == 'on'
            
            # Parse steps from form
            steps = []
            step_orders = request.form.getlist('step_order')
            for i, order in enumerate(step_orders):
                role_id = request.form.get(f'approver_role_{i}')
                sla = request.form.get(f'sla_hours_{i}')
                if role_id:
                    steps.append({
                        'step_order': int(order),
                        'approver_role_id': int(role_id),
                        'sla_hours': int(sla) if sla else 24
                    })
            
            save_workflow(wf_type, module, label, '', requires_approval, steps, user_id)
            flash("Workflow saved.", "success")
            return redirect(url_for('admin_workflows'))
        
        return render_template('admin/workflows.html', **context)
    
    @app.route('/admin/api/workflows/<wf_type>/steps')
    @admin_require_login
    def admin_api_workflow_steps(wf_type):
        """Get steps for a workflow."""
        workflow = get_workflow(wf_type)
        if not workflow:
            return jsonify({'error': 'Workflow not found'}), 404
        
        steps = get_workflow_steps(workflow['id'])
        return jsonify(steps)
    
    # =====================================================================
    # NOTIFICATIONS & ALERTS
    # =====================================================================
    
    @app.route('/admin/notifications')
    @admin_require_login
    def admin_notifications():
        """Notification rules management."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')
        
        if not user_has_permission(user_id, 'platform', 'settings', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))
        
        context = _get_admin_context(user_id, language)
        context['page_title'] = 'Notifications & Alerts'

        # Get relevant settings from different categories for display
        # Use dict() to ensure we always have a dict, even if the function returns None
        wms_settings = dict(get_settings_by_category('WMS') or {})
        general_settings = dict(get_settings_by_category('GENERAL') or {})
        crm_settings = dict(get_settings_by_category('CRM') or {})
        marketing_settings = dict(get_settings_by_category('MARKETING') or {})

        context['settings'] = {
            **wms_settings,
            **general_settings,
            **crm_settings,
            **marketing_settings,
        }

        # Get notification rules from database
        with get_db_context() as db:
            context['rules'] = db.execute(
                "SELECT * FROM notification_rules WHERE is_active = 1 ORDER BY module, alert_type"
            ).fetchall()

        return render_template('admin/notifications.html', **context)
    
    @app.route('/admin/api/notifications/rules', methods=['GET', 'POST'])
    @admin_require_login
    def admin_api_notification_rules():
        """API for notification rules."""
        user_id = session.get('user_id')

        if request.method == 'POST':
            # Validate CSRF for POST requests
            from app import validate_csrf_token
            token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
            if not validate_csrf_token(token):
                return jsonify({'error': 'CSRF token required'}), 403

            if not user_has_permission(user_id, 'platform', 'settings', 'edit'):
                return jsonify({'error': 'Access denied'}), 403

            data = request.get_json()

            with get_db_context() as db:
                existing = db.execute(
                    "SELECT id FROM notification_rules WHERE rule_code = ?",
                    (data['rule_code'],)
                ).fetchone()
                
                if existing:
                    db.execute("""
                        UPDATE notification_rules 
                        SET rule_name = ?, module = ?, alert_type = ?,
                            threshold_value = ?, severity = ?, recipients = ?,
                            delivery_method = ?, escalation_hours = ?,
                            repeat_interval_hours = ?, is_active = ?,
                            updated_at = CURRENT_TIMESTAMP, updated_by = ?
                        WHERE rule_code = ?
                    """, (
                        data['rule_name'], data['module'], data['alert_type'],
                        data.get('threshold_value', ''), data.get('severity', 'MEDIUM'),
                        json.dumps(data.get('recipients', [])),
                        data.get('delivery_method', 'IN_APP'),
                        data.get('escalation_hours', 24),
                        data.get('repeat_interval_hours', 0),
                        1 if data.get('is_active', True) else 0,
                        user_id, data['rule_code']
                    ))
                else:
                    db.execute("""
                        INSERT INTO notification_rules 
                        (rule_code, rule_name, module, alert_type, threshold_value,
                         severity, recipients, delivery_method, escalation_hours,
                         repeat_interval_hours, is_active, created_by, updated_by)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        data['rule_code'], data['rule_name'], data['module'], data['alert_type'],
                        data.get('threshold_value', ''), data.get('severity', 'MEDIUM'),
                        json.dumps(data.get('recipients', [])),
                        data.get('delivery_method', 'IN_APP'),
                        data.get('escalation_hours', 24),
                        data.get('repeat_interval_hours', 0),
                        1 if data.get('is_active', True) else 0,
                        user_id, user_id
                    ))
                
                db.commit()
            
            return jsonify({'success': True})
        
        # GET
        with get_db_context() as db:
            rules = db.execute(
                "SELECT * FROM notification_rules WHERE is_active = 1"
            ).fetchall()
        
        return jsonify([dict(r) for r in rules])
    
    # =====================================================================
    # AUDIT LOG
    # =====================================================================
    
    @app.route('/admin/audit')
    @admin_require_login
    def admin_audit():
        """Audit log viewer."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')
        
        if not user_has_permission(user_id, 'platform', 'audit_log', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))
        
        context = _get_admin_context(user_id, language)
        context['page_title'] = 'Audit Log'
        
        # Get audit logs with pagination
        page = request.args.get('page', 1, type=int)
        per_page = 50
        offset = (page - 1) * per_page
        
        entity_type = request.args.get('entity_type')
        user_filter = request.args.get('user_id', type=int)
        action = request.args.get('action')
        
        # Build query
        sql = "SELECT * FROM platform_audit_log WHERE 1=1"
        params = []
        
        if entity_type:
            sql += " AND entity_type = ?"
            params.append(entity_type)
        
        if user_filter:
            sql += " AND user_id = ?"
            params.append(user_filter)
        
        if action:
            sql += " AND action = ?"
            params.append(action)
        
        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])
        
        context['logs'] = get_all(sql, params)
        context['entity_types'] = ['setting', 'user', 'customer', 'employee', 'order', 'workflow', 'numbering_rule']
        context['current_filters'] = {
            'entity_type': entity_type,
            'user_id': user_filter,
            'action': action,
            'page': page
        }
        
        return render_template('admin/audit.html', **context)
    
    @app.route('/admin/audit/settings')
    @admin_require_login
    def admin_audit_settings():
        """Settings change history."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')
        
        if not user_has_permission(user_id, 'platform', 'audit_log', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))
        
        context = _get_admin_context(user_id, language)
        context['page_title'] = 'Settings Change History'
        
        # Get settings-specific audit logs
        context['history'] = get_settings_history(
            setting_key=request.args.get('key'),
            user_id=request.args.get('user_id', type=int),
            limit=100
        )
        
        return render_template('admin/audit_settings.html', **context)
    
    # =====================================================================
    # HELPER FUNCTIONS
    # =====================================================================
    
    def _get_admin_context(user_id, language='en'):
        """Build common context for admin pages."""
        user_perms = get_user_permissions(user_id)
        menu = get_main_menu(user_id, language)
        current_path = request.path
        
        return {
            'user_id': user_id,
            'username': session.get('username', 'Admin'),
            'language': language,
            'direction': 'rtl' if language in ['ar', 'fa'] else 'ltr',
            'menu': prepare_menu_for_template(menu, current_path),
            'permissions': sorted(user_perms) if user_perms else [],
            'available_themes': get_available_themes(),
            'notifications': get_user_notifications(user_id, unread_only=True, limit=10),
            'categories': ADMIN_CATEGORIES,
            'scope_levels': SCOPE_LEVELS
        }
    
    def _get_admin_stats():
        """Get comprehensive dashboard statistics."""
        import logging
        _logger = logging.getLogger('admin_routes')

        def safe_get_cnt(sql):
            """Safely execute count query and return 0 on failure."""
            try:
                result = get_one(sql)
                return result['cnt'] if result and 'cnt' in result else 0
            except Exception as e:
                _logger.warning(f"Count query failed: {e}")
                return 0

        stats = {
            'total_settings': safe_get_cnt("SELECT COUNT(*) as cnt FROM admin_settings WHERE is_active = 1"),
            'total_users': safe_get_cnt("SELECT COUNT(*) as cnt FROM users"),
            'total_roles': safe_get_cnt("SELECT COUNT(*) as cnt FROM roles"),
            'total_workflows': safe_get_cnt("SELECT COUNT(*) as cnt FROM workflows WHERE is_active = 1"),
            'total_numbering_rules': safe_get_cnt("SELECT COUNT(*) as cnt FROM numbering_rules WHERE is_active = 1"),
        }

        # Organization counts
        stats['companies'] = safe_get_cnt("SELECT COUNT(*) as cnt FROM companies WHERE is_active = 1")
        stats['branches'] = safe_get_cnt("SELECT COUNT(*) as cnt FROM branches WHERE is_active = 1")
        stats['warehouses'] = safe_get_cnt("SELECT COUNT(*) as cnt FROM warehouses WHERE is_active = 1")

        # Business entity counts
        stats['categories'] = safe_get_cnt("SELECT COUNT(*) as cnt FROM categories")
        stats['brands'] = safe_get_cnt("SELECT COUNT(*) as cnt FROM brands")
        stats['suppliers'] = safe_get_cnt("SELECT COUNT(*) as cnt FROM suppliers WHERE status = 'Active'")
        stats['customers'] = safe_get_cnt("SELECT COUNT(*) as cnt FROM customers WHERE is_active = 1")
        stats['vehicles'] = safe_get_cnt("SELECT COUNT(*) as cnt FROM vehicles WHERE status = 'Active'")
        stats['locations'] = safe_get_cnt("SELECT COUNT(*) as cnt FROM locations WHERE is_active = 1")

        # Count master data records
        md_counts = {}
        md_types_list = []
        # Validate table name prefix to prevent SQL injection
        valid_md_prefixes = set()
        for key in MASTER_DATA_TYPES.keys():
            # Only allow alphanumeric + underscore, max 20 chars
            if key and isinstance(key, str) and len(key) <= 20 and key.replace('_', '').isalnum():
                valid_md_prefixes.add(key)

        for md_type in valid_md_prefixes:
            table_name = f"md_{md_type}"
            try:
                count = get_one(f"SELECT COUNT(*) as cnt FROM {table_name} WHERE is_active = 1")
                md_counts[md_type] = count['cnt'] if count and 'cnt' in count else 0
                if count and count['cnt'] > 0:
                    md_types_list.append(md_type)
            except Exception as e:
                _logger.warning(f"Master data table '{table_name}' query failed: {e}")
                md_counts[md_type] = 0

        stats['master_data_counts'] = md_counts
        stats['master_data_types'] = md_types_list

        # Additional stats
        stats['notification_rules'] = safe_get_cnt("SELECT COUNT(*) as cnt FROM notification_rules WHERE is_active = 1")
        stats['numbering_sequences'] = safe_get_cnt("SELECT COUNT(*) as cnt FROM numbering_sequences")

        return stats
    
    def _get_default_settings_for_category(category):
        """Get default settings metadata for a category."""
        from admin_settings import (
            DEFAULT_GENERAL_SETTINGS, DEFAULT_LOCALIZATION_SETTINGS,
            DEFAULT_SECURITY_SETTINGS, DEFAULT_UI_SETTINGS,
            DEFAULT_SALES_SETTINGS, DEFAULT_CRM_SETTINGS,
            DEFAULT_WMS_SETTINGS, DEFAULT_LOGISTICS_SETTINGS,
            DEFAULT_HR_SETTINGS, DEFAULT_MARKETING_SETTINGS,
            DEFAULT_PLANNING_SETTINGS
        )
        
        all_defaults = {}
        all_defaults.update(DEFAULT_GENERAL_SETTINGS)
        all_defaults.update(DEFAULT_LOCALIZATION_SETTINGS)
        all_defaults.update(DEFAULT_SECURITY_SETTINGS)
        all_defaults.update(DEFAULT_UI_SETTINGS)
        all_defaults.update(DEFAULT_SALES_SETTINGS)
        all_defaults.update(DEFAULT_CRM_SETTINGS)
        all_defaults.update(DEFAULT_WMS_SETTINGS)
        all_defaults.update(DEFAULT_LOGISTICS_SETTINGS)
        all_defaults.update(DEFAULT_HR_SETTINGS)
        all_defaults.update(DEFAULT_MARKETING_SETTINGS)
        all_defaults.update(DEFAULT_PLANNING_SETTINGS)
        
        # Filter by prefix based on category
        prefix_map = {
            'GENERAL': ['platform_', 'company_', 'default_warehouse', 'default_company', 'default_branch'],
            'LOCALIZATION': ['default_language', 'available_languages', 'default_timezone', 'date_format',
                           'time_format', 'number_format', 'decimal_precision', 'currency_format',
                           'default_currency', 'week_start_day', 'business_days', 'enable_rtl'],
            'SECURITY': ['session_timeout', 'max_login', 'password_min', 'require_', 'enable_2fa',
                       'allowed_file', 'max_file_size', 'ip_whitelist'],
            'UI': ['default_theme', 'items_per_page', 'show_welcome', 'compact_sidebar', 
                  'default_font_size', 'table_density'],
            'SALES': ['sales_', 'quotation_', 'max_discount', 'discount_approval', 'min_margin',
                     'inquiry_response', 'lost_reason', 'source_tracking', 'auto_confirm'],
            'CRM': ['crm_'],
            'WAREHOUSE': ['wms_'],
            'LOGISTICS': ['logistics_'],
            'HR': ['hr_'],
            'MARKETING': ['marketing_'],
            'PLANNING': ['planning_'],
        }
        
        prefixes = prefix_map.get(category, [])
        
        return {k: v for k, v in all_defaults.items() 
                if any(k.startswith(p) for p in prefixes)}
    
    def _handle_settings_save(category, user_id):
        """Handle settings form submission."""
        for key in request.form.keys():
            if key.startswith('_'):
                continue
            
            value = request.form.get(key)
            description = request.form.get(f'_desc_{key}', '')
            
            set_setting(key, value, category, 'GLOBAL', None, description, user_id)
    
    def _handle_master_data_create(md_type, user_id):
        """Handle master data create form submission."""
        md_info = MASTER_DATA_TYPES.get(md_type, {})
        fields = md_info.get('fields', [])

        data = {}
        for field in fields:
            if field in ['is_active']:
                data[field] = 1 if request.form.get(field) == 'on' else 0
            elif field in ['category', 'channel']:
                # These go into extra_data for lead_source
                pass
            else:
                data[field] = request.form.get(field, '')

        # Handle extra_data for priority_level
        if md_type == 'priority_level':
            extra_data = {}
            level = request.form.get('level', '')
            response_hours = request.form.get('response_hours', '')
            resolution_hours = request.form.get('resolution_hours', '')
            color = request.form.get('color', '')
            escalation_level = request.form.get('escalation_level', '')
            if level:
                extra_data['level'] = int(level)
            if response_hours:
                extra_data['response_hours'] = int(response_hours)
            if resolution_hours:
                extra_data['resolution_hours'] = int(resolution_hours)
            if color:
                extra_data['color'] = color
            if escalation_level:
                extra_data['escalation_level'] = escalation_level
            if extra_data:
                import json
                data['extra_data'] = json.dumps(extra_data)

        create_master_data(md_type, data, user_id)
    
    def _handle_master_data_update(md_type, record_id, user_id):
        """Handle master data update form submission."""
        md_info = MASTER_DATA_TYPES.get(md_type, {})
        fields = md_info.get('fields', [])

        data = {}
        for field in fields:
            if field in ['is_active']:
                data[field] = 1 if request.form.get(field) == 'on' else 0
            elif field in ['category', 'channel']:
                pass
            else:
                data[field] = request.form.get(field, '')

        # Handle extra_data for priority_level
        if md_type == 'priority_level':
            extra_data = {}
            level = request.form.get('level', '')
            response_hours = request.form.get('response_hours', '')
            resolution_hours = request.form.get('resolution_hours', '')
            color = request.form.get('color', '')
            escalation_level = request.form.get('escalation_level', '')
            if level:
                extra_data['level'] = int(level)
            if response_hours:
                extra_data['response_hours'] = int(response_hours)
            if resolution_hours:
                extra_data['resolution_hours'] = int(resolution_hours)
            if color:
                extra_data['color'] = color
            if escalation_level:
                extra_data['escalation_level'] = escalation_level
            if extra_data:
                import json
                data['extra_data'] = json.dumps(extra_data)

        update_master_data(md_type, record_id, data, user_id)

    # =====================================================================
    # USERS MANAGEMENT
    # =====================================================================

    @app.route('/admin/users')
    @admin_require_login
    def admin_users():
        """User management page."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'platform', 'users', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_admin_context(user_id, language)
        context['page_title'] = 'Users'

        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = 20
        offset = (page - 1) * per_page

        # Filters
        filters = {
            'search': request.args.get('search', ''),
            'role': request.args.get('role', ''),
            'status': request.args.get('status', ''),
            'company': request.args.get('company', '')
        }

        # Build query
        sql = """
            SELECT u.*, r.role_name, c.name as company_name,
                   (SELECT COUNT(*) FROM users GROUP BY role_id HAVING role_id = u.role_id) as role_user_count
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            LEFT JOIN companies c ON u.company_id = c.id
            WHERE 1=1
        """
        params = []

        if filters['search']:
            sql += " AND (u.full_name LIKE ? OR u.email LIKE ? OR u.username LIKE ?)"
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term, search_term])

        if filters['role']:
            sql += " AND u.role_id = ?"
            params.append(filters['role'])

        if filters['status']:
            if filters['status'] == 'active':
                sql += " AND u.is_active = 1"
            else:
                sql += " AND u.is_active = 0"

        if filters['company']:
            sql += " AND u.company_id = ?"
            params.append(filters['company'])

        # Count total
        count_sql = sql.replace("SELECT u.*, r.role_name, c.name as company_name,\n                   (SELECT COUNT(*) FROM users GROUP BY role_id HAVING role_id = u.role_id) as role_user_count", "SELECT COUNT(*) as total")
        total = get_one(count_sql, params)['total']

        # Get paginated results
        sql += f" ORDER BY u.created_at DESC LIMIT {per_page} OFFSET {offset}"
        users = get_all(sql, params)

        # Get roles and companies for dropdowns
        context['roles'] = get_all_roles()
        context['companies'] = get_all("SELECT * FROM companies WHERE is_active = 1 ORDER BY name")
        context['warehouses'] = get_all("SELECT * FROM warehouses WHERE is_active = 1 ORDER BY name")
        context['users'] = users
        context['filters'] = filters
        context['pagination'] = {
            'page': page,
            'pages': (total + per_page - 1) // per_page,
            'total': total,
            'start': offset + 1,
            'end': min(offset + per_page, total)
        }

        return render_template('admin/users.html', **context)

    @app.route('/admin/users/create', methods=['POST'])
    @admin_require_login
    def admin_create_user():
        """Create a new user."""
        # Validate CSRF for POST requests
        from app import validate_csrf_token
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        if not validate_csrf_token(token):
            flash("CSRF validation failed. Please refresh and try again.", "error")
            return redirect(url_for('admin_users'))

        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'platform', 'users', 'create'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        full_name = request.form.get('full_name')
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone', '')
        role_id = request.form.get('role_id', type=int)
        company_id = request.form.get('company_id', type=int) or None
        department = request.form.get('department', '')
        job_title = request.form.get('job_title', '')
        password = request.form.get('password')
        is_active = 1 if request.form.get('is_active') else 0

        if not all([full_name, username, email, password, role_id]):
            flash("Required fields missing.", "error")
            return redirect(url_for('admin_users'))

        from werkzeug.security import generate_password_hash

        with get_db_context() as db:
            # Check if username or email already exists
            existing = db.execute(
                "SELECT id FROM users WHERE username = ? OR email = ?",
                (username, email)
            ).fetchone()

            if existing:
                flash("Username or email already exists.", "error")
                return redirect(url_for('admin_users'))

            db.execute("""
                INSERT INTO users (username, email, password_hash, full_name, phone,
                                 role_id, company_id, department, job_title, is_active,
                                 created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (username, email, generate_password_hash(password), full_name, phone,
                  role_id, company_id, department, job_title, is_active))
            db.commit()

            log_audit(entity_type='user', entity_id=username, action='CREATE',
                     user_id=user_id, notes=f"Created user: {username}")

        flash("User created successfully.", "success")
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/edit', methods=['POST'])
    @admin_require_login
    def admin_edit_user():
        """Update an existing user."""
        # Validate CSRF for POST requests
        from app import validate_csrf_token
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        if not validate_csrf_token(token):
            flash("CSRF validation failed. Please refresh and try again.", "error")
            return redirect(url_for('admin_users'))

        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'platform', 'users', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        user_id_to_edit = request.form.get('user_id', type=int)
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone', '')
        role_id = request.form.get('role_id', type=int)
        company_id = request.form.get('company_id', type=int) or None
        department = request.form.get('department', '')
        job_title = request.form.get('job_title', '')
        password = request.form.get('password')
        is_active = 1 if request.form.get('is_active') else 0

        if not all([user_id_to_edit, full_name, email, role_id]):
            flash("Required fields missing.", "error")
            return redirect(url_for('admin_users'))

        with get_db_context() as db:
            # Check if username or email already exists for other users
            existing = db.execute(
                "SELECT id FROM users WHERE (username = ? OR email = ?) AND id != ?",
                (request.form.get('username'), email, user_id_to_edit)
            ).fetchone()

            if existing:
                flash("Username or email already exists.", "error")
                return redirect(url_for('admin_users'))

            if password:
                from werkzeug.security import generate_password_hash
                db.execute("""
                    UPDATE users SET full_name = ?, email = ?, phone = ?, role_id = ?,
                                   company_id = ?, department = ?, job_title = ?,
                                   password_hash = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (full_name, email, phone, role_id, company_id, department,
                      job_title, generate_password_hash(password), is_active, user_id_to_edit))
            else:
                db.execute("""
                    UPDATE users SET full_name = ?, email = ?, phone = ?, role_id = ?,
                                   company_id = ?, department = ?, job_title = ?,
                                   is_active = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (full_name, email, phone, role_id, company_id, department,
                      job_title, is_active, user_id_to_edit))
            db.commit()

            log_audit(entity_type='user', entity_id=str(user_id_to_edit), action='UPDATE',
                     user_id=user_id, notes=f"Updated user ID: {user_id_to_edit}")

        flash("User updated successfully.", "success")
        return redirect(url_for('admin_users'))

    @app.route('/admin/users/toggle/<int:user_id>', methods=['POST'])
    @admin_require_login
    def admin_toggle_user(user_id):
        """Toggle user active status."""
        # Validate CSRF for POST requests
        from app import validate_csrf_token
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        if not validate_csrf_token(token):
            flash("CSRF validation failed. Please refresh and try again.", "error")
            return redirect(url_for('admin_users'))

        current_user_id = session.get('user_id')

        if not user_has_permission(current_user_id, 'platform', 'users', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        action = request.form.get('action')

        with get_db_context() as db:
            if action == 'activate':
                db.execute("UPDATE users SET is_active = 1 WHERE id = ?", (user_id,))
                flash("User activated.", "success")
            elif action == 'deactivate':
                db.execute("UPDATE users SET is_active = 0 WHERE id = ?", (user_id,))
                flash("User deactivated.", "success")
            db.commit()

            log_audit(entity_type='user', entity_id=str(user_id), action=action.upper(),
                     user_id=current_user_id)

        return redirect(url_for('admin_users'))

    @app.route('/admin/api/users/<int:user_id>')
    @admin_require_login
    def admin_api_get_user(user_id):
        """API endpoint to get user data."""
        if not user_has_permission(session.get('user_id'), 'platform', 'users', 'view'):
            return jsonify({'error': 'Access denied'}), 403

        user = get_one("SELECT * FROM users WHERE id = ?", (user_id,))
        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify(dict(user))

    @app.route('/admin/api/users/<int:user_id>/permissions')
    @admin_require_login
    def admin_api_get_user_permissions(user_id):
        """API endpoint to get user permissions."""
        if not user_has_permission(session.get('user_id'), 'platform', 'users', 'view'):
            return jsonify({'error': 'Access denied'}), 403

        user = get_one("SELECT role_id FROM users WHERE id = ?", (user_id,))
        if not user or not user['role_id']:
            return jsonify({'permissions': []})

        permissions = get_role_permissions(user['role_id'])
        return jsonify({'permissions': list(permissions)})

    @app.route('/admin/api/users/<int:user_id>/access')
    @admin_require_login
    def admin_api_get_user_access(user_id):
        """API endpoint to get user access scopes."""
        if not user_has_permission(session.get('user_id'), 'platform', 'users', 'view'):
            return jsonify({'error': 'Access denied'}), 403

        companies = get_all("""
            SELECT company_id FROM user_company_access WHERE user_id = ?
        """, (user_id,))
        warehouses = get_all("""
            SELECT warehouse_id FROM user_warehouse_access WHERE user_id = ?
        """, (user_id,))

        return jsonify({
            'companies': [c['company_id'] for c in companies],
            'warehouses': [w['warehouse_id'] for w in warehouses]
        })

    @app.route('/admin/users/access', methods=['POST'])
    @admin_require_login
    def admin_update_user_access():
        """Update user access scopes."""
        # Validate CSRF for POST requests
        from app import validate_csrf_token
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        if not validate_csrf_token(token):
            flash("CSRF validation failed. Please refresh and try again.", "error")
            return redirect(url_for('admin_users'))

        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'platform', 'users', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        target_user_id = request.form.get('user_id', type=int)
        company_ids = request.form.getlist('company_ids')
        warehouse_ids = request.form.getlist('warehouse_ids')

        with get_db_context() as db:
            # Clear existing access
            db.execute("DELETE FROM user_company_access WHERE user_id = ?", (target_user_id,))
            db.execute("DELETE FROM user_warehouse_access WHERE user_id = ?", (target_user_id,))

            # Add company access
            for cid in company_ids:
                db.execute(
                    "INSERT INTO user_company_access (user_id, company_id) VALUES (?, ?)",
                    (target_user_id, int(cid))
                )

            # Add warehouse access
            for wid in warehouse_ids:
                db.execute(
                    "INSERT INTO user_warehouse_access (user_id, warehouse_id) VALUES (?, ?)",
                    (target_user_id, int(wid))
                )

            db.commit()

            log_audit(entity_type='user_access', entity_id=str(target_user_id), action='UPDATE',
                     user_id=user_id, notes=f"Updated access scopes for user ID: {target_user_id}")

        flash("Access scopes updated.", "success")
        return redirect(url_for('admin_users'))

    # =====================================================================
    # ROLES MANAGEMENT
    # =====================================================================

    @app.route('/admin/roles')
    @admin_require_login
    def admin_roles():
        """Roles management page."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'platform', 'roles', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_admin_context(user_id, language)
        context['page_title'] = 'Roles & Permissions'

        # Get all roles with user and permission counts
        roles = get_all("""
            SELECT r.*,
                   (SELECT COUNT(*) FROM users WHERE role_id = r.id) as user_count,
                   (SELECT COUNT(*) FROM role_permissions WHERE role_id = r.id) as permission_count
            FROM roles r
            ORDER BY r.role_name
        """)

        context['roles'] = roles
        context['companies'] = get_all("SELECT * FROM companies WHERE is_active = 1 ORDER BY name")
        context['modules'] = MODULE_PERMISSIONS

        return render_template('admin/roles.html', **context)

    @app.route('/admin/roles/create', methods=['POST'])
    @admin_require_login
    def admin_create_role():
        """Create a new role."""
        # Validate CSRF for POST requests
        from app import validate_csrf_token
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        if not validate_csrf_token(token):
            flash("CSRF validation failed. Please refresh and try again.", "error")
            return redirect(url_for('admin_roles'))

        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'platform', 'roles', 'create'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        role_name = request.form.get('role_name')
        description = request.form.get('description', '')
        company_id = request.form.get('company_id', type=int) or None

        if not role_name:
            flash("Role name is required.", "error")
            return redirect(url_for('admin_roles'))

        with get_db_context() as db:
            existing = db.execute(
                "SELECT id FROM roles WHERE role_name = ?", (role_name,)
            ).fetchone()

            if existing:
                flash("Role name already exists.", "error")
                return redirect(url_for('admin_roles'))

            db.execute("""
                INSERT INTO roles (role_name, description, company_id, is_system,
                                   role_group, role_class, valid_from, valid_to)
                VALUES (?, ?, ?, 0, ?, ?, ?, ?)
            """, (role_name, description, company_id,
                  request.form.get('role_group', 'GENERAL'),
                  request.form.get('role_class', 'General'),
                  request.form.get('valid_from', '2020-01-01'),
                  request.form.get('valid_to', '9999-12-31')))
            db.commit()

            log_audit(entity_type='role', entity_id=role_name, action='CREATE',
                     user_id=user_id, notes=f"Created role: {role_name}")

        flash("Role created successfully.", "success")
        return redirect(url_for('admin_roles'))

    @app.route('/admin/roles/edit', methods=['POST'])
    @admin_require_login
    def admin_edit_role():
        """Update an existing role."""
        # Validate CSRF for POST requests
        from app import validate_csrf_token
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        if not validate_csrf_token(token):
            flash("CSRF validation failed. Please refresh and try again.", "error")
            return redirect(url_for('admin_roles'))

        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'platform', 'roles', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        role_id = request.form.get('role_id', type=int)
        role_name = request.form.get('role_name')
        description = request.form.get('description', '')
        company_id = request.form.get('company_id', type=int) or None

        if not role_id or not role_name:
            flash("Role ID and name are required.", "error")
            return redirect(url_for('admin_roles'))

        # Check if system role
        role = get_one("SELECT is_system FROM roles WHERE id = ?", (role_id,))
        if role and role['is_system']:
            flash("Cannot edit system role.", "error")
            return redirect(url_for('admin_roles'))

        with get_db_context() as db:
            db.execute("""
                UPDATE roles SET role_name = ?, description = ?, company_id = ?,
                                role_group = ?, role_class = ?,
                                valid_from = ?, valid_to = ?
                WHERE id = ? AND is_system = 0
            """, (role_name, description, company_id,
                  request.form.get('role_group', 'GENERAL'),
                  request.form.get('role_class', 'General'),
                  request.form.get('valid_from', '2020-01-01'),
                  request.form.get('valid_to', '9999-12-31'),
                  role_id))
            db.commit()

            log_audit(entity_type='role', entity_id=str(role_id), action='UPDATE',
                     user_id=user_id, notes=f"Updated role ID: {role_id}")

        flash("Role updated successfully.", "success")
        return redirect(url_for('admin_roles'))

    @app.route('/admin/api/roles/<int:role_id>')
    @admin_require_login
    def admin_api_get_role(role_id):
        """API endpoint to get role data."""
        if not user_has_permission(session.get('user_id'), 'platform', 'roles', 'view'):
            return jsonify({'error': 'Access denied'}), 403

        role = get_one("SELECT * FROM roles WHERE id = ?", (role_id,))
        if not role:
            return jsonify({'error': 'Role not found'}), 404

        return jsonify(dict(role))

    @app.route('/admin/api/roles/<int:role_id>/permissions')
    @admin_require_login
    def admin_api_get_role_permissions(role_id):
        """API endpoint to get role permissions."""
        if not user_has_permission(session.get('user_id'), 'platform', 'roles', 'view'):
            return jsonify({'error': 'Access denied'}), 403

        permissions = get_role_permissions(role_id)
        return jsonify({'permissions': list(permissions)})

    @app.route('/admin/api/roles/update-permissions', methods=['POST'])
    @admin_require_login
    def admin_api_update_role_permissions():
        """API endpoint to update role permissions."""
        # Validate CSRF for POST requests
        from app import validate_csrf_token
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        if not validate_csrf_token(token):
            return jsonify({'error': 'CSRF token required'}), 403

        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'platform', 'roles', 'edit'):
            return jsonify({'error': 'Access denied'}), 403

        data = request.get_json()
        role_id = data.get('role_id')
        permissions = data.get('permissions', [])

        if not role_id:
            return jsonify({'error': 'Role ID is required'}), 400

        # Check if system role
        role = get_one("SELECT is_system FROM roles WHERE id = ?", (role_id,))
        if role and role['is_system']:
            return jsonify({'error': 'Cannot modify system role'}), 403

        with get_db_context() as db:
            # Clear existing permissions
            db.execute("DELETE FROM role_permissions WHERE role_id = ?", (role_id,))

            # Add new permissions
            for perm in permissions:
                parts = perm.split('.')
                if len(parts) == 3:
                    module, resource, action = parts
                    db.execute("""
                        INSERT INTO role_permissions (role_id, module, resource, action)
                        VALUES (?, ?, ?, ?)
                    """, (role_id, module, resource, action))

            db.commit()

            log_audit(entity_type='role_permissions', entity_id=str(role_id), action='UPDATE',
                     user_id=user_id, notes=f"Updated permissions for role ID: {role_id}")

        return jsonify({'success': True})

    @app.route('/admin/roles/delete/<int:role_id>', methods=['POST'])
    @admin_require_login
    def admin_delete_role(role_id):
        """Delete a role."""
        # Validate CSRF for POST requests
        from app import validate_csrf_token
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        if not validate_csrf_token(token):
            return jsonify({'error': 'CSRF token required'}), 403

        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'platform', 'roles', 'delete'):
            return jsonify({'error': 'Access denied'}), 403

        role = get_one("SELECT * FROM roles WHERE id = ?", (role_id,))
        if not role:
            return jsonify({'error': 'Role not found'}), 404

        if role['is_system']:
            return jsonify({'error': 'Cannot delete system role'}), 403

        # Check if role has users
        user_count = get_one("SELECT COUNT(*) as cnt FROM users WHERE role_id = ?", (role_id,))
        if user_count and user_count['cnt'] > 0:
            return jsonify({'error': f'Cannot delete role: {user_count["cnt"]} users are assigned to this role'}), 400

        with get_db_context() as db:
            db.execute("DELETE FROM role_permissions WHERE role_id = ?", (role_id,))
            db.execute("DELETE FROM roles WHERE id = ? AND is_system = 0", (role_id,))
            db.commit()

            log_audit(entity_type='role', entity_id=str(role_id), action='DELETE',
                     user_id=user_id, notes=f"Deleted role ID: {role_id}")

        return jsonify({'success': True})

    # =====================================================================
    # ACCESS SCOPES MANAGEMENT
    # =====================================================================

    @app.route('/admin/access-scopes')
    @admin_require_login
    def admin_access_scopes():
        """Access scopes management page."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'platform', 'settings', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_admin_context(user_id, language)
        context['page_title'] = 'Access Scopes & Visibility'

        # Get companies
        context['companies'] = get_all("""
            SELECT c.*,
                   (SELECT COUNT(*) FROM branches WHERE company_id = c.id) as branch_count
            FROM companies c
            WHERE c.is_active = 1
            ORDER BY c.name
        """)

        # Get branches
        context['branches'] = get_all("""
            SELECT b.*, c.name as company_name
            FROM branches b
            LEFT JOIN companies c ON b.company_id = c.id
            WHERE b.is_active = 1
            ORDER BY b.name
        """)

        # Get warehouses
        context['warehouses'] = get_all("""
            SELECT w.*, c.name as company_name
            FROM warehouses w
            LEFT JOIN companies c ON w.company_id = c.id
            WHERE w.is_active = 1
            ORDER BY w.name
        """)

        # Get visibility rules from settings
        visibility_rules = {}
        for key in ['customer_default', 'order_default', 'show_costs', 'show_salaries', 'restrict_pricing']:
            setting_key = f'visibility_{key}'
            value = get_setting(setting_key)
            if value is None:
                if key in ['show_costs', 'show_salaries', 'restrict_pricing']:
                    value = False
                else:
                    value = 'all'
            elif value in ('1', 'true', 'True'):
                value = True
            visibility_rules[key] = value

        context['visibility_rules'] = visibility_rules

        return render_template('admin/access_scopes.html', **context)

    @app.route('/admin/access-scopes/save', methods=['POST'])
    @admin_require_login
    def admin_save_visibility_rules():
        """Save visibility rules."""
        # Validate CSRF for POST requests
        from app import validate_csrf_token
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        if not validate_csrf_token(token):
            flash("CSRF validation failed. Please refresh and try again.", "error")
            return redirect(url_for('admin_access_scopes'))

        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'platform', 'settings', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        rules = {
            'visibility_customer_default': request.form.get('visibility_customer_default', 'all'),
            'visibility_order_default': request.form.get('visibility_order_default', 'all'),
            'visibility_show_costs': '1' if request.form.get('visibility_show_costs') else '0',
            'visibility_show_salaries': '1' if request.form.get('visibility_show_salaries') else '0',
            'visibility_restrict_pricing': '1' if request.form.get('visibility_restrict_pricing') else '0',
        }

        for key, value in rules.items():
            set_setting(key, value, 'SECURITY', 'GLOBAL', None, f'Visibility rule: {key}', user_id)

        flash("Visibility rules saved.", "success")
        return redirect(url_for('admin_access_scopes'))

    @app.route('/admin/api/companies/<int:company_id>')
    @admin_require_login
    def admin_api_get_company(company_id):
        """API endpoint to get company data."""
        if not user_has_permission(session.get('user_id'), 'platform', 'settings', 'view'):
            return jsonify({'error': 'Access denied'}), 403

        company = get_one("SELECT * FROM companies WHERE id = ?", (company_id,))
        if not company:
            return jsonify({'error': 'Company not found'}), 404

        return jsonify(dict(company))

    @app.route('/admin/api/branches/<int:branch_id>')
    @admin_require_login
    def admin_api_get_branch(branch_id):
        """API endpoint to get branch data."""
        if not user_has_permission(session.get('user_id'), 'platform', 'settings', 'view'):
            return jsonify({'error': 'Access denied'}), 403

        branch = get_one("SELECT * FROM branches WHERE id = ?", (branch_id,))
        if not branch:
            return jsonify({'error': 'Branch not found'}), 404

        return jsonify(dict(branch))

    @app.route('/admin/api/warehouses/<int:warehouse_id>')
    @admin_require_login
    def admin_api_get_warehouse(warehouse_id):
        """API endpoint to get warehouse data."""
        if not user_has_permission(session.get('user_id'), 'platform', 'settings', 'view'):
            return jsonify({'error': 'Access denied'}), 403

        warehouse = get_one("SELECT * FROM warehouses WHERE id = ?", (warehouse_id,))
        if not warehouse:
            return jsonify({'error': 'Warehouse not found'}), 404

        return jsonify(dict(warehouse))

    # =====================================================================
    # ORGANIZATION MANAGEMENT
    # =====================================================================

    @app.route('/admin/organization')
    @admin_require_login
    def admin_organization():
        """Organization structure management page."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'platform', 'settings', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_admin_context(user_id, language)
        context['page_title'] = 'Organization Structure'

        # Get stats
        stats = {
            'companies': get_one("SELECT COUNT(*) as cnt FROM companies WHERE is_active = 1")['cnt'],
            'branches': get_one("SELECT COUNT(*) as cnt FROM branches WHERE is_active = 1")['cnt'],
            'warehouses': get_one("SELECT COUNT(*) as cnt FROM warehouses WHERE is_active = 1")['cnt'],
            'departments': get_one("SELECT COUNT(*) as cnt FROM departments WHERE is_active = 1")['cnt'] if _table_exists('departments') else 0,
        }

        # Get companies with branch counts
        context['companies'] = get_all("""
            SELECT c.*,
                   (SELECT COUNT(*) FROM branches WHERE company_id = c.id) as branch_count
            FROM companies c
            WHERE c.is_active = 1
            ORDER BY c.name
        """)

        # Get branches
        context['branches'] = get_all("""
            SELECT b.*, c.name as company_name
            FROM branches b
            LEFT JOIN companies c ON b.company_id = c.id
            WHERE b.is_active = 1
            ORDER BY b.name
        """)

        # Get departments
        context['departments'] = get_all("""
            SELECT d.*, c.name as company_name
            FROM departments d
            LEFT JOIN companies c ON d.company_id = c.id
            WHERE d.is_active = 1
            ORDER BY d.name
        """) if _table_exists('departments') else []

        context['stats'] = stats

        return render_template('admin/organization.html', **context)

    @app.route('/admin/organization/save', methods=['POST'])
    @admin_require_login
    def admin_save_organization():
        """Handle organization entity CRUD."""
        # Validate CSRF for POST requests
        from app import validate_csrf_token
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        if not validate_csrf_token(token):
            flash("CSRF validation failed. Please refresh and try again.", "error")
            return redirect(url_for('admin_settings_category', category='ORGANIZATION'))

        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'platform', 'settings', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        action = request.form.get('action')
        entity_id = request.form.get('entity_id')
        code = request.form.get('code')
        name = request.form.get('name')
        parent_id = request.form.get('parent_id') or None
        entity_type = request.form.get('entity_type', '')
        description = request.form.get('description', '')
        is_active = 1 if request.form.get('is_active') else 0

        if not code or not name:
            flash("Code and name are required.", "error")
            return redirect(url_for('admin_organization'))

        def _table_exists(name):
            result = get_one(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (name,)
            )
            return result is not None

        with get_db_context() as db:
            # Parse all form fields
            company_id = request.form.get('company_id') or None
            branch_type = request.form.get('branch_type') or ''
            department_type = request.form.get('department_type') or ''
            cost_center = request.form.get('cost_center') or ''
            city = request.form.get('city') or ''
            country = request.form.get('country') or 'UAE'
            email = request.form.get('email') or ''
            phone = request.form.get('phone') or ''
            address = request.form.get('address') or ''
            manager_name = request.form.get('manager_name') or ''
            manager_phone = request.form.get('manager_phone') or ''
            industry = request.form.get('industry') or ''
            division_type = request.form.get('division_type') or ''
            team_type = request.form.get('team_type') or ''

            if action in ('create_company', 'edit_company'):
                if action == 'create_company':
                    db.execute("""
                        INSERT INTO companies (code, name, company_type, industry, description, address, city, country, phone, email, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (code, name, entity_type, industry, description, address, city, country, phone, email, is_active))
                    flash("Company created successfully.", "success")
                else:
                    db.execute("""
                        UPDATE companies SET code = ?, name = ?, company_type = ?, industry = ?, description = ?,
                                       address = ?, city = ?, country = ?, phone = ?, email = ?,
                                       is_active = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (code, name, entity_type, industry, description, address, city, country, phone, email, is_active, entity_id))
                    flash("Company updated successfully.", "success")

            elif action in ('create_branch', 'edit_branch'):
                if action == 'create_branch':
                    db.execute("""
                        INSERT INTO branches (code, name, company_id, branch_type, description, address, city, country, phone, manager_name, manager_phone, is_active, is_operational, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                    """, (code, name, company_id, branch_type, description, address, city, country, phone, manager_name, manager_phone, is_active))
                    flash("Branch created successfully.", "success")
                else:
                    db.execute("""
                        UPDATE branches SET code = ?, name = ?, company_id = ?, branch_type = ?,
                                       description = ?, address = ?, city = ?, country = ?,
                                       phone = ?, manager_name = ?, manager_phone = ?,
                                       is_active = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (code, name, company_id, branch_type, description, address, city, country, phone, manager_name, manager_phone, is_active, entity_id))
                    flash("Branch updated successfully.", "success")

            elif action in ('create_department', 'edit_department'):
                if action == 'create_department':
                    db.execute("""
                        INSERT INTO departments (code, name, company_id, department_type, description, cost_center, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (code, name, company_id, department_type, description, cost_center, is_active))
                    flash("Department created successfully.", "success")
                else:
                    db.execute("""
                        UPDATE departments SET code = ?, name = ?, company_id = ?, department_type = ?,
                                       description = ?, cost_center = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (code, name, company_id, department_type, description, cost_center, is_active, entity_id))
                    flash("Department updated successfully.", "success")

            elif action in ('create_division', 'edit_division'):
                if action == 'create_division':
                    db.execute("""
                        INSERT INTO divisions (code, name, company_id, division_type, description, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (code, name, company_id, division_type, description, is_active))
                    flash("Division created successfully.", "success")
                else:
                    db.execute("""
                        UPDATE divisions SET code = ?, name = ?, company_id = ?, division_type = ?,
                                       description = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (code, name, company_id, division_type, description, is_active, entity_id))
                    flash("Division updated successfully.", "success")

            elif action in ('create_team', 'edit_team'):
                dept_id = request.form.get('department_id') or None
                if action == 'create_team':
                    db.execute("""
                        INSERT INTO teams (code, name, company_id, department_id, team_type, description, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (code, name, company_id, dept_id, team_type, description, is_active))
                    flash("Team created successfully.", "success")
                else:
                    db.execute("""
                        UPDATE teams SET code = ?, name = ?, company_id = ?, department_id = ?,
                                       team_type = ?, description = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (code, name, company_id, dept_id, team_type, description, is_active, entity_id))
                    flash("Team updated successfully.", "success")

            elif action in ('create_warehouse', 'edit_warehouse'):
                warehouse_type = request.form.get('warehouse_type') or ''
                if action == 'create_warehouse':
                    db.execute("""
                        INSERT INTO warehouses (code, name, company_id, type, address, city, country, phone, email, is_active, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (code, name, company_id, warehouse_type, address, city, country, phone, email, is_active))
                    flash("Warehouse created successfully.", "success")
                else:
                    db.execute("""
                        UPDATE warehouses SET code = ?, name = ?, company_id = ?, type = ?,
                                       address = ?, city = ?, country = ?, phone = ?, email = ?,
                                       is_active = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (code, name, company_id, warehouse_type, address, city, country, phone, email, is_active, entity_id))
                    flash("Warehouse updated successfully.", "success")

            db.commit()

            log_audit(entity_type='organization', entity_id=action,
                     action=action.split('_')[0].upper(),
                     user_id=user_id, notes=f"Action: {action}, Code: {code}")

        # Return to ORGANIZATION settings page
        return redirect(url_for('admin_settings_category', category='ORGANIZATION'))

    @app.route('/admin/api/departments/<int:dept_id>')
    @admin_require_login
    def admin_api_get_department(dept_id):
        """API endpoint to get department data."""
        if not user_has_permission(session.get('user_id'), 'platform', 'settings', 'view'):
            return jsonify({'error': 'Access denied'}), 403

        dept = get_one("SELECT * FROM departments WHERE id = ?", (dept_id,))
        if not dept:
            return jsonify({'error': 'Department not found'}), 404

        return jsonify(dict(dept))

    @app.route('/admin/api/companies/<int:company_id>')
    @admin_require_login
    def admin_api_company_detail(company_id):
        if not user_has_permission(session.get('user_id'), 'platform', 'settings', 'view'):
            return jsonify({'error': 'Access denied'}), 403
        company = get_one("SELECT * FROM companies WHERE id = ?", (company_id,))
        if not company:
            return jsonify({'error': 'Company not found'}), 404
        return jsonify(dict(company))

    @app.route('/admin/api/branches/<int:branch_id>')
    @admin_require_login
    def admin_api_branch_detail(branch_id):
        if not user_has_permission(session.get('user_id'), 'platform', 'settings', 'view'):
            return jsonify({'error': 'Access denied'}), 403
        branch = get_one("SELECT * FROM branches WHERE id = ?", (branch_id,))
        if not branch:
            return jsonify({'error': 'Branch not found'}), 404
        return jsonify(dict(branch))

    @app.route('/admin/api/divisions/<int:division_id>')
    @admin_require_login
    def admin_api_get_division(division_id):
        if not user_has_permission(session.get('user_id'), 'platform', 'settings', 'view'):
            return jsonify({'error': 'Access denied'}), 403
        division = get_one("SELECT * FROM divisions WHERE id = ?", (division_id,))
        if not division:
            return jsonify({'error': 'Division not found'}), 404
        return jsonify(dict(division))

    @app.route('/admin/api/teams/<int:team_id>')
    @admin_require_login
    def admin_api_get_team(team_id):
        if not user_has_permission(session.get('user_id'), 'platform', 'settings', 'view'):
            return jsonify({'error': 'Access denied'}), 403
        team = get_one("SELECT * FROM teams WHERE id = ?", (team_id,))
        if not team:
            return jsonify({'error': 'Team not found'}), 404
        return jsonify(dict(team))

    # =====================================================================
    # PERSONALIZATION & PREFERENCES
    # =====================================================================

    @app.route('/admin/personalization')
    @admin_require_login
    def admin_personalization():
        """Personalization and default preferences management."""
        user_id = session.get('user_id')
        language = session.get('language', 'en')

        if not user_has_permission(user_id, 'platform', 'settings', 'view'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        context = _get_admin_context(user_id, language)
        context['page_title'] = 'Personalization & Preferences'

        # Load preferences from settings
        pref_keys = [
            'default_theme', 'allow_theme_override', 'default_font_family', 'default_font_size',
            'default_language', 'available_languages', 'enable_rtl', 'allow_language_override',
            'default_timezone', 'date_format', 'time_format', 'number_format', 'decimal_precision', 'default_currency',
            'default_sidebar_collapsed', 'compact_sidebar_default', 'table_density_default',
            'items_per_page_default', 'reduced_motion_default', 'default_dashboard', 'allow_dashboard_override',
            'default_company_id', 'default_warehouse_id', 'default_view_mode'
        ]

        preferences = {}
        for key in pref_keys:
            val = get_setting(f'pref_{key}')
            if val is None:
                # Set defaults
                if 'override' in key:
                    preferences[key] = True
                elif key == 'available_languages':
                    preferences[key] = ['en', 'ar', 'fa']
                elif key == 'default_theme':
                    preferences[key] = 'dark'
                elif key == 'default_language':
                    preferences[key] = 'en'
                elif key == 'enable_rtl':
                    preferences[key] = True
                elif key == 'date_format':
                    preferences[key] = 'DD/MM/YYYY'
                elif key == 'time_format':
                    preferences[key] = '24h'
                elif key == 'number_format':
                    preferences[key] = '1,234.56'
                elif key == 'decimal_precision':
                    preferences[key] = '2'
                elif key == 'default_currency':
                    preferences[key] = 'AED'
                elif key == 'default_timezone':
                    preferences[key] = 'Asia/Dubai'
                elif key == 'items_per_page_default':
                    preferences[key] = '50'
                elif key == 'table_density_default':
                    preferences[key] = 'comfortable'
                elif key == 'default_sidebar_collapsed':
                    preferences[key] = '0'
                else:
                    preferences[key] = val
            else:
                if key == 'available_languages' and val:
                    preferences[key] = val.split(',')
                else:
                    preferences[key] = val

        context['preferences'] = preferences
        context['companies'] = get_all("SELECT * FROM companies WHERE is_active = 1 ORDER BY name")
        context['warehouses'] = get_all("SELECT * FROM warehouses WHERE is_active = 1 ORDER BY name")

        return render_template('admin/personalization.html', **context)

    @app.route('/admin/personalization/save', methods=['POST'])
    @admin_require_login
    def admin_save_personalization():
        """Save personalization settings."""
        # Validate CSRF for POST requests
        from app import validate_csrf_token
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        if not validate_csrf_token(token):
            flash("CSRF validation failed. Please refresh and try again.", "error")
            return redirect(url_for('admin_personalization'))

        user_id = session.get('user_id')

        if not user_has_permission(user_id, 'platform', 'settings', 'edit'):
            flash("Access denied.", "error")
            return redirect(url_for('index'))

        action = request.form.get('action')

        def save_pref(key, value, category='UI'):
            set_setting(f'pref_{key}', str(value), category, 'GLOBAL', None, f'Preference: {key}', user_id)

        if action == 'update_theme_defaults':
            save_pref('default_theme', request.form.get('default_theme', 'dark'))
            save_pref('allow_theme_override', request.form.get('allow_theme_override', '1'))
            save_pref('default_font_family', request.form.get('default_font_family', 'Outfit'))
            save_pref('default_font_size', request.form.get('default_font_size', 'medium'))
            flash("Theme settings saved.", "success")

        elif action == 'update_locale_defaults':
            save_pref('default_language', request.form.get('default_language', 'en'))
            langs = ','.join(request.form.getlist('available_languages'))
            save_pref('available_languages', langs)
            save_pref('enable_rtl', request.form.get('enable_rtl', '1'))
            save_pref('allow_language_override', request.form.get('allow_language_override', '1'))
            save_pref('default_timezone', request.form.get('default_timezone', 'Asia/Dubai'))
            save_pref('date_format', request.form.get('date_format', 'DD/MM/YYYY'))
            save_pref('time_format', request.form.get('time_format', '24h'))
            save_pref('number_format', request.form.get('number_format', '1,234.56'))
            save_pref('decimal_precision', request.form.get('decimal_precision', '2'))
            save_pref('default_currency', request.form.get('default_currency', 'AED'))
            flash("Locale settings saved.", "success")

        elif action == 'update_layout_defaults':
            save_pref('default_sidebar_collapsed', request.form.get('default_sidebar_collapsed', '0'))
            save_pref('compact_sidebar_default', request.form.get('compact_sidebar_default', '0'))
            save_pref('table_density_default', request.form.get('table_density_default', 'comfortable'))
            save_pref('items_per_page_default', request.form.get('items_per_page_default', '50'))
            save_pref('reduced_motion_default', request.form.get('reduced_motion_default', '0'))
            flash("Layout settings saved.", "success")

        elif action == 'update_module_defaults':
            save_pref('default_dashboard', request.form.get('default_dashboard', '/'))
            save_pref('allow_dashboard_override', request.form.get('allow_dashboard_override', '1'))
            save_pref('default_company_id', request.form.get('default_company_id', ''))
            save_pref('default_warehouse_id', request.form.get('default_warehouse_id', ''))
            save_pref('default_view_mode', request.form.get('default_view_mode', 'list'))
            flash("Module defaults saved.", "success")

        return redirect(url_for('admin_personalization'))
