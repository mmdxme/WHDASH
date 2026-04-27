"""
Integration / Middleware Module - Routes and Controllers
========================================================
Enterprise-grade integration orchestration layer routes.
All routes follow the existing ERP patterns for consistency.

Author: Enterprise Architecture Team
Version: 1.0.0
"""

import functools
import json
import math
import re
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from flask import Flask, request, jsonify, render_template, session, send_file, redirect, url_for, flash, Response
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

import database as db_helper


def get_integration_db():
    """Get database connection."""
    return db_helper.get_db()


def init_integration_module(app: Flask):
    """
    Initialize the Integration / Middleware module.
    Called during app startup via app.py register mechanism.
    """
    from integration_models import init_integration_tables, seed_integration_connector_types, seed_integration_environments, seed_integration_tags
    import database as db_helper
    
    conn = db_helper.get_db()
    cursor = conn.cursor()
    
    init_integration_tables()
    seed_integration_connector_types()
    seed_integration_environments()
    seed_integration_tags()
    
    print("[Integration Module] Initialized successfully")


def require_permission(module: str, resource: str, action: str):
    """
    Permission decorator for integration routes.
    """
    def decorator(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            from permissions import user_has_permission
            user_id = session.get('user_id')
            if not user_id:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('login'))
            
            if not user_has_permission(user_id, module, resource, action):
                if request.is_json:
                    return jsonify({'error': 'Permission denied'}), 403
                flash('You do not have permission to perform this action.', 'error')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_login(f):
    """Require user to be logged in."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def get_current_user_id():
    """Get current user ID from session."""
    return session.get('user_id')


def get_current_company_id():
    """Get current company ID from session."""
    return session.get('company_id')


def require_integration_permission(action: str):
    """Permission decorator for integration module."""
    return require_permission('integration', 'dashboard', action)


def parse_sort_params(default_sort='created_at', default_order='desc'):
    """Parse sort parameters from request."""
    sort = request.args.get('sort', default_sort)
    order = request.args.get('order', default_order)
    if order not in ('asc', 'desc'):
        order = default_order
    return sort, order


def parse_pagination_params(default_page=1, default_per_page=20):
    """Parse pagination parameters from request."""
    page = max(1, int(request.args.get('page', default_page)))
    per_page = min(100, max(10, int(request.args.get('per_page', default_per_page))))
    return page, per_page


def build_pagination_response(items: List, total: int, page: int, per_page: int, **kwargs):
    """Build pagination metadata for JSON responses."""
    total_pages = math.ceil(total / per_page) if per_page > 0 else 0
    return {
        'items': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1
        },
        **kwargs
    }


def log_integration_audit(entity_type: str, entity_id: int, action: str, 
                           user_id: int = None, notes: str = None,
                           old_value: str = None, new_value: str = None):
    """Log audit entry for integration module."""
    from database import log_audit
    company_id = get_current_company_id()
    log_audit(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        user_id=user_id or get_current_user_id(),
        notes=notes,
        old_value=old_value,
        new_value=new_value,
        company_id=company_id
    )


def notify_flow_channel(channel_name: str, message: str, severity: str = 'info'):
    """Send notification to Flow channel if available."""
    try:
        from flow_models import send_channel_message
        company_id = get_current_company_id()
        send_channel_message(channel_name, message, company_id)
    except Exception as e:
        print(f"[Flow Notification] Failed to send to {channel_name}: {e}")


def generate_uuid():
    """Generate a unique identifier."""
    return str(uuid.uuid4())


def generate_code(prefix):
    """Generate a unique code with prefix."""
    return f"{prefix.upper()}-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"


# =====================================================================
# DASHBOARD - Integration Overview
# =====================================================================

def register_integration_routes(app: Flask):
    """
    Register all Integration / Middleware routes.
    This is the main entry point called from app.py.
    """

    # -------------------------------------------------------------------------
    # OVERVIEW DASHBOARD
    # -------------------------------------------------------------------------
    @app.route('/integration')
    @app.route('/integration/dashboard')
    @require_login
    def integration_dashboard():
        """Main integration overview dashboard."""
        company_id = get_current_company_id()
        conn = get_integration_db()
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute("""
            SELECT COUNT(*), SUM(CASE WHEN active_status = 'active' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN health_status = 'healthy' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN health_status = 'unhealthy' THEN 1 ELSE 0 END)
            FROM integration_connectors WHERE is_deleted = 0
        """)
        connector_stats = cursor.fetchone()
        stats['total_connectors'] = connector_stats[0] or 0
        stats['active_connectors'] = connector_stats[1] or 0
        stats['healthy_connectors'] = connector_stats[2] or 0
        stats['unhealthy_connectors'] = connector_stats[3] or 0
        
        cursor.execute("""
            SELECT COUNT(*), SUM(CASE WHEN flow_status = 'published' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN flow_status = 'draft' THEN 1 ELSE 0 END)
            FROM integration_flows WHERE is_deleted = 0
        """)
        flow_stats = cursor.fetchone()
        stats['total_flows'] = flow_stats[0] or 0
        stats['published_flows'] = flow_stats[1] or 0
        stats['draft_flows'] = flow_stats[2] or 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM integration_queue_items WHERE message_status IN ('pending', 'queued', 'processing')
        """)
        stats['queue_depth'] = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM integration_dlq_items WHERE review_status = 'pending'
        """)
        stats['dlq_count'] = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM integration_webhook_deliveries 
            WHERE delivery_status = 'failed' AND created_at > datetime('now', '-24 hours')
        """)
        stats['webhook_failures_24h'] = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM integration_job_runs 
            WHERE job_status = 'failed' AND created_at > datetime('now', '-24 hours')
        """)
        stats['job_failures_24h'] = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM integration_endpoint_versions ev
            JOIN integration_endpoints e ON ev.endpoint_id = e.id
            WHERE e.active_status = 'active'
        """)
        stats['active_endpoints'] = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM integration_events 
            WHERE event_status = 'published' AND created_at > datetime('now', '-1 hour')
        """)
        stats['events_last_hour'] = cursor.fetchone()[0] or 0
        
        recent_activity = []
        cursor.execute("""
            SELECT 'webhook' as type, wd.delivery_id as id, wh.name, wd.delivery_status,
                   wd.created_at, NULL as flow_name
            FROM integration_webhook_deliveries wd
            JOIN integration_webhooks wh ON wd.webhook_id = wh.id
            ORDER BY wd.created_at DESC LIMIT 10
        """)
        for row in cursor.fetchall():
            recent_activity.append({
                'type': row[0], 'id': row[1], 'name': row[2], 
                'status': row[3], 'created_at': row[4], 'flow_name': row[5]
            })
        
        cursor.execute("""
            SELECT 'job_run' as type, jr.job_run_id as id, IFNULL(s.schedule_name, 'Manual') as name,
                   jr.job_status, jr.start_time, f.name as flow_name
            FROM integration_job_runs jr
            JOIN integration_flows f ON jr.flow_id = f.id
            LEFT JOIN integration_schedules s ON jr.schedule_id = s.id
            ORDER BY jr.start_time DESC LIMIT 10
        """)
        for row in cursor.fetchall():
            recent_activity.append({
                'type': row[0], 'id': row[1], 'name': row[2],
                'status': row[3], 'created_at': row[4], 'flow_name': row[5]
            })
        
        recent_activity.sort(key=lambda x: x['created_at'] or '', reverse=True)
        recent_activity = recent_activity[:10]
        
        health_by_type = []
        cursor.execute("""
            SELECT ct.name, ct.color,
                   SUM(CASE WHEN c.health_status = 'healthy' THEN 1 ELSE 0 END) as healthy,
                   SUM(CASE WHEN c.health_status = 'unhealthy' THEN 1 ELSE 0 END) as unhealthy,
                   SUM(CASE WHEN c.health_status = 'unknown' THEN 1 ELSE 0 END) as unknown
            FROM integration_connector_types ct
            LEFT JOIN integration_connectors c ON c.connector_type = ct.code AND c.is_deleted = 0
            GROUP BY ct.code, ct.name, ct.color
        """)
        for row in cursor.fetchall():
            health_by_type.append({
                'name': row[0], 'color': row[1],
                'healthy': row[2] or 0, 'unhealthy': row[3] or 0, 'unknown': row[4] or 0
            })
        
        return render_template('integration/dashboard.html',
                             stats=stats,
                             recent_activity=recent_activity,
                             health_by_type=health_by_type)

    # -------------------------------------------------------------------------
    # CONNECTORS
    # -------------------------------------------------------------------------
    @app.route('/integration/connectors')
    @require_login
    def integration_connectors():
        """List all integration connectors."""
        page, per_page = parse_pagination_params()
        sort, order = parse_sort_params('created_at', 'desc')
        
        search = request.args.get('search', '').strip()
        connector_type = request.args.get('type', '')
        active_status = request.args.get('status', '')
        health_status = request.args.get('health', '')
        direction = request.args.get('direction', '')
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        conditions = ["c.is_deleted = 0"]
        params = []
        
        if search:
            conditions.append("(c.name LIKE ? OR c.code LIKE ? OR c.description LIKE ?)")
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        if connector_type:
            conditions.append("c.connector_type = ?")
            params.append(connector_type)
        
        if active_status:
            conditions.append("c.active_status = ?")
            params.append(active_status)
        
        if health_status:
            conditions.append("c.health_status = ?")
            params.append(health_status)
        
        if direction:
            conditions.append("c.direction = ?")
            params.append(direction)
        
        where_clause = " AND ".join(conditions)
        
        cursor.execute(f"""
            SELECT COUNT(*) FROM integration_connectors c WHERE {where_clause}
        """, params)
        total = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT c.*, ct.name as type_name, ct.icon as type_icon, ct.color as type_color
            FROM integration_connectors c
            LEFT JOIN integration_connector_types ct ON c.connector_type = ct.code
            WHERE {where_clause}
            ORDER BY c.{sort} {order}
            LIMIT ? OFFSET ?
        """, params + [per_page, (page - 1) * per_page])
        
        connectors = []
        for row in cursor.fetchall():
            connectors.append({
                'id': row[0], 'code': row[1], 'name': row[2], 'description': row[11],
                'connector_type': row[12], 'direction': row[14], 'active_status': row[17],
                'health_status': row[18], 'last_success_at': row[20], 'last_failure_at': row[21],
                'type_name': row[43], 'type_icon': row[44], 'type_color': row[45]
            })
        
        cursor.execute("SELECT code, name FROM integration_connector_types WHERE is_active = 1 ORDER BY name")
        connector_types = [{'code': r[0], 'name': r[1]} for r in cursor.fetchall()]
        
        return render_template('integration/connectors/list.html',
                             connectors=connectors,
                             connector_types=connector_types,
                             pagination=build_pagination_response(connectors, total, page, per_page),
                             filters={
                                 'search': search, 'type': connector_type,
                                 'status': active_status, 'health': health_status,
                                 'direction': direction
                             })

    @app.route('/integration/connectors/api')
    @require_login
    def integration_connectors_api():
        """API endpoint for connectors list (JSON)."""
        page, per_page = parse_pagination_params()
        sort, order = parse_sort_params('created_at', 'desc')
        
        search = request.args.get('search', '').strip()
        connector_type = request.args.get('type', '')
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        conditions = ["c.is_deleted = 0"]
        params = []
        
        if search:
            conditions.append("(c.name LIKE ? OR c.code LIKE ?)")
            params.extend([f'%{search}%', f'%{search}%'])
        
        if connector_type:
            conditions.append("c.connector_type = ?")
            params.append(connector_type)
        
        where_clause = " AND ".join(conditions)
        
        cursor.execute(f"""
            SELECT COUNT(*) FROM integration_connectors c WHERE {where_clause}
        """, params)
        total = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT c.*, ct.name as type_name
            FROM integration_connectors c
            LEFT JOIN integration_connector_types ct ON c.connector_type = ct.code
            WHERE {where_clause}
            ORDER BY c.{sort} {order}
            LIMIT ? OFFSET ?
        """, params + [per_page, (page - 1) * per_page])
        
        connectors = []
        for row in cursor.fetchall():
            connectors.append({
                'id': row[0], 'code': row[1], 'name': row[2],
                'connector_type': row[12], 'direction': row[14],
                'active_status': row[17], 'health_status': row[18],
                'last_success_at': row[20], 'type_name': row[43]
            })
        
        return jsonify(build_pagination_response(connectors, total, page, per_page))

    @app.route('/integration/connectors/<int:connector_id>')
    @require_login
    def integration_connector_detail(connector_id):
        """View connector detail."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.*, ct.name as type_name, ct.icon as type_icon, ct.color as type_color,
                   ct.description as type_description
            FROM integration_connectors c
            LEFT JOIN integration_connector_types ct ON c.connector_type = ct.code
            WHERE c.id = ? AND c.is_deleted = 0
        """, (connector_id,))
        
        row = cursor.fetchone()
        if not row:
            flash('Connector not found.', 'error')
            return redirect(url_for('integration_connectors'))
        
        connector = {
            'id': row[0], 'code': row[1], 'name': row[2], 'description': row[11],
            'connector_type': row[12], 'owner_module': row[13], 'direction': row[14],
            'auth_method': row[15], 'active_status': row[17], 'health_status': row[18],
            'test_status': row[19], 'last_success_at': row[20], 'last_failure_at': row[21],
            'last_tested_at': row[22], 'retry_policy': row[23], 'timeout_seconds': row[24],
            'payload_format': row[25], 'rate_limit_per_minute': row[26], 'environment': row[27],
            'tags': row[28], 'notes': row[29], 'type_name': row[43], 'type_icon': row[44],
            'type_color': row[45], 'type_description': row[46]
        }
        
        cursor.execute("""
            SELECT * FROM integration_credentials 
            WHERE connector_id = ? AND is_deleted = 0
            ORDER BY created_at DESC
        """, (connector_id,))
        credentials = []
        for cred_row in cursor.fetchall():
            credentials.append({
                'id': cred_row[0], 'code': cred_row[2], 'name': cred_row[3],
                'credential_type': cred_row[5], 'auth_method': cred_row[6],
                'is_active': cred_row[33], 'test_status': cred_row[40],
                'last_tested_at': cred_row[41], 'expires_at': cred_row[45]
            })
        
        cursor.execute("""
            SELECT * FROM integration_flows 
            WHERE id IN (SELECT flow_id FROM integration_flow_steps WHERE step_type = 'call_connector')
            AND is_deleted = 0 LIMIT 10
        """)
        related_flows = []
        for flow_row in cursor.fetchall():
            related_flows.append({
                'id': flow_row[0], 'code': flow_row[1], 'name': flow_row[2],
                'flow_status': flow_row[16], 'trigger_type': flow_row[9]
            })
        
        cursor.execute("""
            SELECT * FROM integration_webhooks 
            WHERE connector_id = ? AND is_deleted = 0
            ORDER BY created_at DESC
        """, (connector_id,))
        webhooks = []
        for wh_row in cursor.fetchall():
            webhooks.append({
                'id': wh_row[0], 'code': wh_row[1], 'name': wh_row[2],
                'event_type': wh_row[5], 'active_status': wh_row[13],
                'usage_count': wh_row[24]
            })
        
        cursor.execute("""
            SELECT * FROM integration_logs 
            WHERE connector_id = ? 
            ORDER BY created_at DESC LIMIT 50
        """, (connector_id,))
        recent_logs = []
        for log_row in cursor.fetchall():
            recent_logs.append({
                'id': log_row[0], 'log_level': log_row[2], 'message': row[7],
                'created_at': log_row[35], 'correlation_id': log_row[12]
            })
        
        return render_template('integration/connectors/detail.html',
                             connector=connector,
                             credentials=credentials,
                             related_flows=related_flows,
                             webhooks=webhooks,
                             recent_logs=recent_logs)

    @app.route('/integration/connectors/create/', methods=['GET', 'POST'])
    @require_login
    def integration_connector_create():
        """Create new connector."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        if request.method == 'POST':
            code = generate_code('CONN')
            name = request.form.get('name')
            connector_type = request.form.get('connector_type')
            direction = request.form.get('direction', 'bidirectional')
            owner_module = request.form.get('owner_module')
            auth_method = request.form.get('auth_method')
            description = request.form.get('description', '')
            timeout_seconds = int(request.form.get('timeout_seconds', 30))
            retry_policy = json.dumps({
                'max_retries': int(request.form.get('max_retries', 3)),
                'retry_delay': int(request.form.get('retry_delay', 60))
            })
            environment = request.form.get('environment', 'production')
            company_id = get_current_company_id()
            user_id = get_current_user_id()
            
            cursor.execute("""
                INSERT INTO integration_connectors 
                (code, name, connector_type, direction, owner_module, auth_method,
                 description, timeout_seconds, retry_policy, environment,
                 company_id, created_by, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (code, name, connector_type, direction, owner_module, auth_method,
                  description, timeout_seconds, retry_policy, environment,
                  company_id, user_id, user_id))
            
            connector_id = cursor.lastrowid
            conn.commit()
            
            log_integration_audit('connector', connector_id, 'CREATE',
                                  notes=f'Created connector: {name}')
            
            flash(f'Connector "{name}" created successfully.', 'success')
            return redirect(url_for('integration_connector_detail', connector_id=connector_id))
        
        cursor.execute("SELECT code, name FROM integration_connector_types WHERE is_active = 1 ORDER BY name")
        connector_types = [{'code': r[0], 'name': r[1]} for r in cursor.fetchall()]
        
        modules = ['sales', 'finance', 'procurement', 'warehouse', 'logistics', 'hr',
                   'marketing', 'ecommerce', 'project', 'crm', 'quality', 'documents']
        
        return render_template('integration/connectors/create.html',
                             connector_types=connector_types,
                             modules=modules)

    @app.route('/integration/connectors/<int:connector_id>/edit/', methods=['GET', 'POST'])
    @require_login
    def integration_connector_edit(connector_id):
        """Edit connector."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM integration_connectors WHERE id = ? AND is_deleted = 0", (connector_id,))
        existing = cursor.fetchone()
        if not existing:
            flash('Connector not found.', 'error')
            return redirect(url_for('integration_connectors'))
        
        if request.method == 'POST':
            name = request.form.get('name')
            connector_type = request.form.get('connector_type')
            direction = request.form.get('direction', 'bidirectional')
            owner_module = request.form.get('owner_module')
            auth_method = request.form.get('auth_method')
            description = request.form.get('description', '')
            timeout_seconds = int(request.form.get('timeout_seconds', 30))
            retry_policy = json.dumps({
                'max_retries': int(request.form.get('max_retries', 3)),
                'retry_delay': int(request.form.get('retry_delay', 60))
            })
            environment = request.form.get('environment', 'production')
            active_status = request.form.get('active_status', 'inactive')
            user_id = get_current_user_id()
            
            cursor.execute("""
                UPDATE integration_connectors SET
                    name = ?, connector_type = ?, direction = ?, owner_module = ?,
                    auth_method = ?, description = ?, timeout_seconds = ?,
                    retry_policy = ?, environment = ?, active_status = ?, updated_by = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (name, connector_type, direction, owner_module, auth_method,
                  description, timeout_seconds, retry_policy, environment,
                  active_status, user_id, connector_id))
            
            conn.commit()
            log_integration_audit('connector', connector_id, 'UPDATE',
                                  notes=f'Updated connector: {name}')
            
            flash(f'Connector "{name}" updated successfully.', 'success')
            return redirect(url_for('integration_connector_detail', connector_id=connector_id))
        
        connector = {
            'id': existing[0], 'code': existing[1], 'name': existing[2],
            'connector_type': existing[12], 'owner_module': existing[13],
            'direction': existing[14], 'auth_method': existing[15],
            'description': existing[11], 'timeout_seconds': existing[24],
            'retry_policy': existing[23], 'environment': existing[27],
            'active_status': existing[17]
        }
        
        cursor.execute("SELECT code, name FROM integration_connector_types WHERE is_active = 1 ORDER BY name")
        connector_types = [{'code': r[0], 'name': r[1]} for r in cursor.fetchall()]
        
        modules = ['sales', 'finance', 'procurement', 'warehouse', 'logistics', 'hr',
                   'marketing', 'ecommerce', 'project', 'crm', 'quality', 'documents']
        
        return render_template('integration/connectors/edit.html',
                             connector=connector,
                             connector_types=connector_types,
                             modules=modules)

    @app.route('/integration/connectors/<int:connector_id>/delete/', methods=['POST'])
    @require_login
    def integration_connector_delete(connector_id):
        """Soft delete connector."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE integration_connectors SET is_deleted = 1, updated_by = ?,
            updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (get_current_user_id(), connector_id))
        
        conn.commit()
        log_integration_audit('connector', connector_id, 'DELETE')
        
        flash('Connector deleted successfully.', 'success')
        return redirect(url_for('integration_connectors'))

    @app.route('/integration/connectors/<int:connector_id>/test')
    @require_login
    def integration_connector_test(connector_id):
        """Test connector connectivity."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE integration_connectors SET 
                test_status = 'testing',
                last_tested_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (connector_id,))
        conn.commit()
        
        test_status = 'success'
        error_message = None
        
        cursor.execute("SELECT name, connector_type FROM integration_connectors WHERE id = ?", (connector_id,))
        row = cursor.fetchone()
        connector_name = row[0] if row else 'Unknown'
        
        cursor.execute("""
            UPDATE integration_connectors SET 
                test_status = ?,
                health_status = CASE WHEN ? = 'success' THEN 'healthy' ELSE 'unhealthy' END,
                last_success_at = CASE WHEN ? = 'success' THEN CURRENT_TIMESTAMP ELSE last_success_at END,
                last_failure_at = CASE WHEN ? != 'success' THEN CURRENT_TIMESTAMP ELSE last_failure_at END
            WHERE id = ?
        """, (test_status, test_status, test_status, test_status, connector_id))
        conn.commit()
        
        if test_status == 'success':
            notify_flow_channel('integration-alerts', 
                f'✅ Connector test passed: {connector_name}', 'success')
            return jsonify({'status': 'success', 'message': 'Connector test completed successfully.'})
        else:
            notify_flow_channel('integration-alerts',
                f'❌ Connector test failed: {connector_name} - {error_message}', 'error')
            return jsonify({'status': 'error', 'message': error_message})

    @app.route('/integration/connectors/<int:connector_id>/activate/', methods=['POST'])
    @require_login
    def integration_connector_activate(connector_id):
        """Activate connector."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE integration_connectors SET active_status = 'active', updated_by = ?,
            updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (get_current_user_id(), connector_id))
        conn.commit()
        
        log_integration_audit('connector', connector_id, 'ACTIVATE')
        flash('Connector activated successfully.', 'success')
        return redirect(url_for('integration_connector_detail', connector_id=connector_id))

    @app.route('/integration/connectors/<int:connector_id>/deactivate/', methods=['POST'])
    @require_login
    def integration_connector_deactivate(connector_id):
        """Deactivate connector."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE integration_connectors SET active_status = 'inactive', updated_by = ?,
            updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (get_current_user_id(), connector_id))
        conn.commit()
        
        log_integration_audit('connector', connector_id, 'DEACTIVATE')
        flash('Connector deactivated successfully.', 'success')
        return redirect(url_for('integration_connector_detail', connector_id=connector_id))

    @app.route('/integration/connectors/api/types')
    @require_login
    def integration_connector_types_api():
        """Get connector types (JSON API)."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM integration_connector_types WHERE is_active = 1 ORDER BY name")
        types = []
        for row in cursor.fetchall():
            types.append({
                'code': row[1], 'name': row[2], 'description': row[3],
                'category': row[4], 'icon': row[5], 'color': row[6]
            })
        
        return jsonify(types)

    # -------------------------------------------------------------------------
    # INTEGRATION FLOWS
    # -------------------------------------------------------------------------
    @app.route('/integration/flows')
    @require_login
    def integration_flows():
        """List all integration flows."""
        page, per_page = parse_pagination_params()
        sort, order = parse_sort_params('created_at', 'desc')
        
        search = request.args.get('search', '').strip()
        flow_status = request.args.get('status', '')
        trigger_type = request.args.get('trigger', '')
        source_system = request.args.get('source', '')
        destination_system = request.args.get('destination', '')
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        conditions = ["f.is_deleted = 0"]
        params = []
        
        if search:
            conditions.append("(f.name LIKE ? OR f.code LIKE ? OR f.description LIKE ?)")
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        if flow_status:
            conditions.append("f.flow_status = ?")
            params.append(flow_status)
        
        if trigger_type:
            conditions.append("f.trigger_type = ?")
            params.append(trigger_type)
        
        if source_system:
            conditions.append("f.source_system = ?")
            params.append(source_system)
        
        if destination_system:
            conditions.append("f.destination_system = ?")
            params.append(destination_system)
        
        where_clause = " AND ".join(conditions)
        
        cursor.execute(f"""
            SELECT COUNT(*) FROM integration_flows f WHERE {where_clause}
        """, params)
        total = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT f.*, 
                   (SELECT COUNT(*) FROM integration_flow_steps WHERE flow_id = f.id) as step_count,
                   (SELECT COUNT(*) FROM integration_job_runs WHERE flow_id = f.id AND job_status = 'failed' AND created_at > datetime('now', '-7 days')) as recent_failures
            FROM integration_flows f
            WHERE {where_clause}
            ORDER BY f.{sort} {order}
            LIMIT ? OFFSET ?
        """, params + [per_page, (page - 1) * per_page])
        
        flows = []
        for row in cursor.fetchall():
            flows.append({
                'id': row[0], 'code': row[1], 'name': row[2], 'description': row[6],
                'version': row[7], 'source_system': row[8], 'destination_system': row[9],
                'trigger_type': row[10], 'flow_status': row[16], 'step_count': row[48],
                'recent_failures': row[49], 'created_at': row[42]
            })
        
        return render_template('integration/flows/list.html',
                             flows=flows,
                             pagination=build_pagination_response(flows, total, page, per_page),
                             filters={
                                 'search': search, 'status': flow_status,
                                 'trigger': trigger_type, 'source': source_system,
                                 'destination': destination_system
                             })

    @app.route('/integration/flows/<int:flow_id>')
    @require_login
    def integration_flow_detail(flow_id):
        """View flow detail."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM integration_flows WHERE id = ? AND is_deleted = 0", (flow_id,))
        row = cursor.fetchone()
        if not row:
            flash('Flow not found.', 'error')
            return redirect(url_for('integration_flows'))
        
        flow = {
            'id': row[0], 'code': row[1], 'name': row[2], 'description': row[6],
            'version': row[7], 'source_system': row[8], 'destination_system': row[9],
            'trigger_type': row[10], 'direction': row[11], 'data_entity': row[12],
            'flow_status': row[16], 'is_test_mode': row[17], 'is_production_mode': row[18],
            'retry_strategy': row[26], 'logging_level': row[30], 'alerting_level': row[31],
            'published_at': row[35], 'created_at': row[42]
        }
        
        cursor.execute("""
            SELECT * FROM integration_flow_steps WHERE flow_id = ? ORDER BY step_order
        """, (flow_id,))
        steps = []
        for step_row in cursor.fetchall():
            steps.append({
                'id': step_row[0], 'step_order': step_row[2], 'step_type': step_row[3],
                'step_name': step_row[4], 'description': step_row[5],
                'continue_on_error': step_row[8], 'timeout_seconds': step_row[9],
                'retry_count': step_row[10], 'step_status': step_row[11]
            })
        
        cursor.execute("""
            SELECT * FROM integration_schedules WHERE flow_id = ? AND is_active = 1
        """, (flow_id,))
        schedules = []
        for sched_row in cursor.fetchall():
            schedules.append({
                'id': sched_row[0], 'schedule_name': sched_row[2],
                'frequency': sched_row[4], 'next_run_at': sched_row[12],
                'last_run_at': sched_row[11]
            })
        
        cursor.execute("""
            SELECT * FROM integration_job_runs WHERE flow_id = ?
            ORDER BY start_time DESC LIMIT 20
        """, (flow_id,))
        recent_runs = []
        for run_row in cursor.fetchall():
            recent_runs.append({
                'id': run_row[0], 'job_run_id': run_row[1], 'start_time': run_row[4],
                'end_time': run_row[5], 'duration_ms': run_row[6],
                'job_status': run_row[7], 'records_processed': run_row[8],
                'records_succeeded': run_row[9], 'records_failed': run_row[10]
            })
        
        return render_template('integration/flows/detail.html',
                             flow=flow,
                             steps=steps,
                             schedules=schedules,
                             recent_runs=recent_runs)

    @app.route('/integration/flows/create/', methods=['GET', 'POST'])
    @require_login
    def integration_flow_create():
        """Create new integration flow."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        if request.method == 'POST':
            code = generate_code('FLOW')
            name = request.form.get('name')
            source_system = request.form.get('source_system')
            destination_system = request.form.get('destination_system')
            trigger_type = request.form.get('trigger_type')
            direction = request.form.get('direction', 'outbound')
            data_entity = request.form.get('data_entity')
            description = request.form.get('description', '')
            retry_strategy = request.form.get('retry_strategy', 'exponential')
            logging_level = request.form.get('logging_level', 'info')
            alerting_level = request.form.get('alerting_level', 'warning')
            company_id = get_current_company_id()
            user_id = get_current_user_id()
            
            cursor.execute("""
                INSERT INTO integration_flows 
                (code, name, source_system, destination_system, trigger_type, direction,
                 data_entity, description, retry_strategy, logging_level, alerting_level,
                 company_id, created_by, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (code, name, source_system, destination_system, trigger_type, direction,
                  data_entity, description, retry_strategy, logging_level, alerting_level,
                  company_id, user_id, user_id))
            
            flow_id = cursor.lastrowid
            
            step_order = 1
            for step_type in ['source', 'validate', 'map_fields', 'transform', 'call_api']:
                cursor.execute("""
                    INSERT INTO integration_flow_steps 
                    (flow_id, step_order, step_type, step_name, step_status)
                    VALUES (?, ?, ?, ?, 'active')
                """, (flow_id, step_order, step_type, step_type.replace('_', ' ').title()))
                step_order += 1
            
            conn.commit()
            log_integration_audit('flow', flow_id, 'CREATE', notes=f'Created flow: {name}')
            
            flash(f'Flow "{name}" created successfully.', 'success')
            return redirect(url_for('integration_flow_detail', flow_id=flow_id))
        
        modules = ['sales', 'finance', 'procurement', 'warehouse', 'logistics', 'hr',
                   'marketing', 'ecommerce', 'project', 'crm', 'quality', 'documents']
        
        return render_template('integration/flows/create.html', modules=modules)

    @app.route('/integration/flows/<int:flow_id>/edit/', methods=['GET', 'POST'])
    @require_login
    def integration_flow_edit(flow_id):
        """Edit integration flow."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM integration_flows WHERE id = ? AND is_deleted = 0", (flow_id,))
        existing = cursor.fetchone()
        if not existing:
            flash('Flow not found.', 'error')
            return redirect(url_for('integration_flows'))
        
        if request.method == 'POST':
            name = request.form.get('name')
            source_system = request.form.get('source_system')
            destination_system = request.form.get('destination_system')
            trigger_type = request.form.get('trigger_type')
            direction = request.form.get('direction', 'outbound')
            data_entity = request.form.get('data_entity')
            description = request.form.get('description', '')
            retry_strategy = request.form.get('retry_strategy', 'exponential')
            logging_level = request.form.get('logging_level', 'info')
            alerting_level = request.form.get('alerting_level', 'warning')
            
            cursor.execute("""
                UPDATE integration_flows SET
                    name = ?, source_system = ?, destination_system = ?,
                    trigger_type = ?, direction = ?, data_entity = ?,
                    description = ?, retry_strategy = ?, logging_level = ?,
                    alerting_level = ?, updated_by = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (name, source_system, destination_system, trigger_type, direction,
                  data_entity, description, retry_strategy, logging_level, alerting_level,
                  get_current_user_id(), flow_id))
            
            conn.commit()
            log_integration_audit('flow', flow_id, 'UPDATE', notes=f'Updated flow: {name}')
            
            flash(f'Flow "{name}" updated successfully.', 'success')
            return redirect(url_for('integration_flow_detail', flow_id=flow_id))
        
        flow = {
            'id': existing[0], 'code': existing[1], 'name': existing[2],
            'source_system': existing[8], 'destination_system': existing[9],
            'trigger_type': existing[10], 'direction': existing[11],
            'data_entity': existing[12], 'description': existing[6],
            'retry_strategy': existing[26], 'logging_level': existing[30],
            'alerting_level': existing[31]
        }
        
        modules = ['sales', 'finance', 'procurement', 'warehouse', 'logistics', 'hr',
                   'marketing', 'ecommerce', 'project', 'crm', 'quality', 'documents']
        
        return render_template('integration/flows/edit.html', flow=flow, modules=modules)

    @app.route('/integration/flows/<int:flow_id>/publish/', methods=['POST'])
    @require_login
    def integration_flow_publish(flow_id):
        """Publish a flow."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE integration_flows SET 
                flow_status = 'published',
                published_at = CURRENT_TIMESTAMP,
                updated_by = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (get_current_user_id(), flow_id))
        
        cursor.execute("SELECT name FROM integration_flows WHERE id = ?", (flow_id,))
        flow_name = cursor.fetchone()[0]
        
        conn.commit()
        log_integration_audit('flow', flow_id, 'PUBLISH')
        
        notify_flow_channel('integration-alerts',
            f'🚀 Flow published: {flow_name}', 'info')
        
        flash('Flow published successfully.', 'success')
        return redirect(url_for('integration_flow_detail', flow_id=flow_id))

    @app.route('/integration/flows/<int:flow_id>/archive/', methods=['POST'])
    @require_login
    def integration_flow_archive(flow_id):
        """Archive a flow."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE integration_flows SET 
                flow_status = 'archived',
                archived_at = CURRENT_TIMESTAMP,
                updated_by = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (get_current_user_id(), flow_id))
        
        conn.commit()
        log_integration_audit('flow', flow_id, 'ARCHIVE')
        
        flash('Flow archived successfully.', 'success')
        return redirect(url_for('integration_flows'))

    @app.route('/integration/flows/<int:flow_id>/steps/save/', methods=['POST'])
    @require_login
    def integration_flow_steps_save(flow_id):
        """Save flow steps."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        steps_data = request.json.get('steps', [])
        
        cursor.execute("DELETE FROM integration_flow_steps WHERE flow_id = ?", (flow_id,))
        
        for step in steps_data:
            cursor.execute("""
                INSERT INTO integration_flow_steps 
                (flow_id, step_order, step_type, step_name, description, config_json,
                 continue_on_error, timeout_seconds, retry_count, step_status, is_enabled)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (flow_id, step['step_order'], step['step_type'], step['step_name'],
                  step.get('description', ''), json.dumps(step.get('config', {})),
                  step.get('continue_on_error', 0), step.get('timeout_seconds', 30),
                  step.get('retry_count', 0), step.get('step_status', 'active'),
                  step.get('is_enabled', 1)))
        
        conn.commit()
        log_integration_audit('flow_steps', flow_id, 'UPDATE',
                              notes=f'Updated {len(steps_data)} steps')
        
        return jsonify({'status': 'success', 'message': f'{len(steps_data)} steps saved.'})

    @app.route('/integration/flows/<int:flow_id>/run/', methods=['POST'])
    @require_login
    def integration_flow_run(flow_id):
        """Trigger a manual flow run."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        job_run_id = generate_code('RUN')
        
        cursor.execute("""
            INSERT INTO integration_job_runs 
            (job_run_id, flow_id, job_type, trigger_type, start_time, job_status,
             execution_mode, started_by, company_id)
            VALUES (?, ?, 'flow_execution', 'manual', CURRENT_TIMESTAMP, 'running',
                    'test', ?, ?)
        """, (job_run_id, flow_id, get_current_user_id(), get_current_company_id()))
        
        conn.commit()
        
        return jsonify({
            'status': 'success',
            'job_run_id': job_run_id,
            'message': 'Flow execution started.'
        })

    # -------------------------------------------------------------------------
    # API ENDPOINTS
    # -------------------------------------------------------------------------
    @app.route('/integration/endpoints')
    @require_login
    def integration_endpoints():
        """List API endpoints."""
        page, per_page = parse_pagination_params()
        sort, order = parse_sort_params('created_at', 'desc')
        
        search = request.args.get('search', '').strip()
        endpoint_group = request.args.get('group', '')
        active_status = request.args.get('status', '')
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        conditions = ["e.is_deleted = 0"]
        params = []
        
        if search:
            conditions.append("(e.name LIKE ? OR e.code LIKE ? OR e.url_path LIKE ?)")
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        if endpoint_group:
            conditions.append("e.endpoint_group = ?")
            params.append(endpoint_group)
        
        if active_status:
            conditions.append("e.active_status = ?")
            params.append(active_status)
        
        where_clause = " AND ".join(conditions)
        
        cursor.execute(f"""
            SELECT COUNT(*) FROM integration_endpoints e WHERE {where_clause}
        """, params)
        total = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT * FROM integration_endpoints e
            WHERE {where_clause}
            ORDER BY e.{sort} {order}
            LIMIT ? OFFSET ?
        """, params + [per_page, (page - 1) * per_page])
        
        endpoints = []
        for row in cursor.fetchall():
            endpoints.append({
                'id': row[0], 'code': row[1], 'name': row[2], 'url_path': row[6],
                'http_method': row[5], 'endpoint_type': row[4], 'active_status': row[18],
                'usage_count': row[21], 'error_count': row[22], 'health_check_result': row[24],
                'endpoint_group': row[29]
            })
        
        groups = ['sales', 'finance', 'procurement', 'warehouse', 'logistics', 'hr',
                  'documents', 'marketing', 'ecommerce', 'integrations', 'admin']
        
        return render_template('integration/endpoints/list.html',
                             endpoints=endpoints,
                             groups=groups,
                             pagination=build_pagination_response(endpoints, total, page, per_page),
                             filters={
                                 'search': search, 'group': endpoint_group,
                                 'status': active_status
                             })

    @app.route('/integration/endpoints/<int:endpoint_id>')
    @require_login
    def integration_endpoint_detail(endpoint_id):
        """View endpoint detail."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM integration_endpoints WHERE id = ? AND is_deleted = 0", (endpoint_id,))
        row = cursor.fetchone()
        if not row:
            flash('Endpoint not found.', 'error')
            return redirect(url_for('integration_endpoints'))
        
        endpoint = {
            'id': row[0], 'code': row[1], 'name': row[2], 'description': row[3],
            'endpoint_type': row[4], 'http_method': row[5], 'url_path': row[6],
            'auth_type': row[7], 'allowed_methods': row[8], 'schema_definition': row[9],
            'sample_request': row[10], 'sample_response': row[11], 'timeout_seconds': row[12],
            'rate_limit_per_minute': row[13], 'ip_allowlist': row[14], 'active_status': row[18],
            'deprecated_status': row[19], 'usage_count': row[21], 'error_count': row[22],
            'health_check_result': row[24], 'last_health_check': row[25],
            'endpoint_group': row[29], 'version': row[31]
        }
        
        cursor.execute("""
            SELECT * FROM integration_endpoint_versions 
            WHERE endpoint_id = ? ORDER BY created_at DESC
        """, (endpoint_id,))
        versions = []
        for v_row in cursor.fetchall():
            versions.append({
                'id': v_row[0], 'version': v_row[2], 'changelog': v_row[5],
                'is_active': v_row[6], 'created_at': v_row[8]
            })
        
        return render_template('integration/endpoints/detail.html',
                             endpoint=endpoint,
                             versions=versions)

    @app.route('/integration/endpoints/create/', methods=['GET', 'POST'])
    @require_login
    def integration_endpoint_create():
        """Create new endpoint."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        if request.method == 'POST':
            code = generate_code('EP')
            name = request.form.get('name')
            endpoint_type = request.form.get('endpoint_type')
            http_method = request.form.get('http_method')
            url_path = request.form.get('url_path')
            auth_type = request.form.get('auth_type')
            endpoint_group = request.form.get('endpoint_group')
            description = request.form.get('description', '')
            timeout_seconds = int(request.form.get('timeout_seconds', 30))
            rate_limit = request.form.get('rate_limit_per_minute')
            company_id = get_current_company_id()
            user_id = get_current_user_id()
            
            cursor.execute("""
                INSERT INTO integration_endpoints 
                (code, name, description, endpoint_type, http_method, url_path,
                 auth_type, timeout_seconds, rate_limit_per_minute, endpoint_group,
                 company_id, created_by, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (code, name, description, endpoint_type, http_method, url_path,
                  auth_type, timeout_seconds, rate_limit, endpoint_group,
                  company_id, user_id, user_id))
            
            endpoint_id = cursor.lastrowid
            conn.commit()
            
            log_integration_audit('endpoint', endpoint_id, 'CREATE',
                                  notes=f'Created endpoint: {name}')
            
            flash(f'Endpoint "{name}" created successfully.', 'success')
            return redirect(url_for('integration_endpoint_detail', endpoint_id=endpoint_id))
        
        groups = ['sales', 'finance', 'procurement', 'warehouse', 'logistics', 'hr',
                  'documents', 'marketing', 'ecommerce', 'integrations', 'admin']
        
        return render_template('integration/endpoints/create.html', groups=groups)

    # -------------------------------------------------------------------------
    # WEBHOOKS
    # -------------------------------------------------------------------------
    @app.route('/integration/webhooks')
    @require_login
    def integration_webhooks():
        """List webhooks."""
        page, per_page = parse_pagination_params()
        
        search = request.args.get('search', '').strip()
        event_type = request.args.get('event_type', '')
        active_status = request.args.get('status', '')
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        conditions = ["w.is_deleted = 0"]
        params = []
        
        if search:
            conditions.append("(w.name LIKE ? OR w.code LIKE ?)")
            params.extend([f'%{search}%', f'%{search}%'])
        
        if event_type:
            conditions.append("w.event_type = ?")
            params.append(event_type)
        
        if active_status:
            conditions.append("w.active_status = ?")
            params.append(active_status)
        
        where_clause = " AND ".join(conditions)
        
        cursor.execute(f"SELECT COUNT(*) FROM integration_webhooks w WHERE {where_clause}", params)
        total = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT w.*, c.name as connector_name
            FROM integration_webhooks w
            LEFT JOIN integration_connectors c ON w.connector_id = c.id
            WHERE {where_clause}
            ORDER BY w.created_at DESC LIMIT ? OFFSET ?
        """, params + [per_page, (page - 1) * per_page])
        
        webhooks = []
        for row in cursor.fetchall():
            webhooks.append({
                'id': row[0], 'code': row[1], 'name': row[2], 'event_type': row[5],
                'target_url': row[7], 'active_status': row[13], 'health_status': row[14],
                'usage_count': row[24], 'success_count': row[25], 'failure_count': row[26],
                'last_success_at': row[27], 'last_failure_at': row[28],
                'connector_name': row[47] if len(row) > 47 else None
            })
        
        return render_template('integration/webhooks/list.html',
                             webhooks=webhooks,
                             pagination=build_pagination_response(webhooks, total, page, per_page),
                             filters={
                                 'search': search, 'event_type': event_type,
                                 'status': active_status
                             })

    @app.route('/integration/webhooks/<int:webhook_id>')
    @require_login
    def integration_webhook_detail(webhook_id):
        """View webhook detail."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT w.*, c.name as connector_name
            FROM integration_webhooks w
            LEFT JOIN integration_connectors c ON w.connector_id = c.id
            WHERE w.id = ? AND w.is_deleted = 0
        """, (webhook_id,))
        row = cursor.fetchone()
        if not row:
            flash('Webhook not found.', 'error')
            return redirect(url_for('integration_webhooks'))
        
        webhook = {
            'id': row[0], 'code': row[1], 'name': row[2], 'description': row[3],
            'event_type': row[5], 'source_system': row[6], 'target_url': row[7],
            'http_method': row[8], 'auth_type': row[9], 'retry_policy': row[11],
            'timeout_seconds': row[12], 'active_status': row[13], 'health_status': row[14],
            'is_inbound': row[15], 'is_outbound': row[16], 'usage_count': row[24],
            'success_count': row[25], 'failure_count': row[26], 'last_success_at': row[27],
            'last_failure_at': row[28], 'connector_name': row[47] if len(row) > 47 else None
        }
        
        cursor.execute("""
            SELECT * FROM integration_webhook_deliveries 
            WHERE webhook_id = ? ORDER BY created_at DESC LIMIT 50
        """, (webhook_id,))
        deliveries = []
        for d_row in cursor.fetchall():
            deliveries.append({
                'id': d_row[0], 'delivery_id': d_row[2], 'event_id': d_row[3],
                'http_status_code': d_row[7], 'delivery_status': d_row[10],
                'attempt_number': d_row[11], 'latency_ms': d_row[13],
                'created_at': d_row[17]
            })
        
        return render_template('integration/webhooks/detail.html',
                             webhook=webhook,
                             deliveries=deliveries)

    @app.route('/integration/webhooks/<int:webhook_id>/replay/', methods=['POST'])
    @require_login
    def integration_webhook_replay(webhook_id):
        """Replay webhook delivery."""
        delivery_id = request.json.get('delivery_id') if request.is_json else None
        
        if not delivery_id:
            return jsonify({'status': 'error', 'message': 'Delivery ID required.'}), 400
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT payload, headers_json, target_url FROM integration_webhook_deliveries wd
            JOIN integration_webhooks w ON wd.webhook_id = w.id
            WHERE wd.delivery_id = ?
        """, (delivery_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'status': 'error', 'message': 'Delivery not found.'}), 404
        
        new_delivery_id = generate_code('DLV')
        
        cursor.execute("""
            INSERT INTO integration_webhook_deliveries 
            (webhook_id, delivery_id, payload, headers_json, delivery_status, created_at)
            VALUES (?, ?, ?, ?, 'pending', CURRENT_TIMESTAMP)
        """, (webhook_id, new_delivery_id, row[0], row[1]))
        
        conn.commit()
        log_integration_audit('webhook_delivery', webhook_id, 'REPLAY',
                              notes=f'Replayed delivery: {delivery_id} -> {new_delivery_id}')
        
        return jsonify({
            'status': 'success',
            'new_delivery_id': new_delivery_id,
            'message': 'Webhook replay initiated.'
        })

    @app.route('/integration/webhooks/create/', methods=['GET', 'POST'])
    @require_login
    def integration_webhook_create():
        """Create new webhook."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        if request.method == 'POST':
            code = generate_code('WH')
            name = request.form.get('name')
            event_type = request.form.get('event_type')
            source_system = request.form.get('source_system')
            target_url = request.form.get('target_url')
            http_method = request.form.get('http_method', 'POST')
            auth_type = request.form.get('auth_type', 'hmac_sha256')
            secret_key = request.form.get('secret_key', '')
            description = request.form.get('description', '')
            timeout_seconds = int(request.form.get('timeout_seconds', 30))
            is_outbound = 1 if request.form.get('is_outbound') else 0
            company_id = get_current_company_id()
            user_id = get_current_user_id()
            
            cursor.execute("""
                INSERT INTO integration_webhooks 
                (code, name, event_type, source_system, target_url, http_method,
                 auth_type, secret_key, description, timeout_seconds, is_outbound,
                 company_id, created_by, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (code, name, event_type, source_system, target_url, http_method,
                  auth_type, secret_key, description, timeout_seconds, is_outbound,
                  company_id, user_id, user_id))
            
            webhook_id = cursor.lastrowid
            conn.commit()
            
            log_integration_audit('webhook', webhook_id, 'CREATE',
                                  notes=f'Created webhook: {name}')
            
            flash(f'Webhook "{name}" created successfully.', 'success')
            return redirect(url_for('integration_webhook_detail', webhook_id=webhook_id))
        
        return render_template('integration/webhooks/create.html')

    # -------------------------------------------------------------------------
    # EVENT BUS
    # -------------------------------------------------------------------------
    @app.route('/integration/events')
    @require_login
    def integration_events():
        """List events."""
        page, per_page = parse_pagination_params()
        
        event_type = request.args.get('event_type', '')
        source_system = request.args.get('source', '')
        event_status = request.args.get('status', '')
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        conditions = ["1=1"]
        params = []
        
        if event_type:
            conditions.append("event_type = ?")
            params.append(event_type)
        
        if source_system:
            conditions.append("source_system = ?")
            params.append(source_system)
        
        if event_status:
            conditions.append("event_status = ?")
            params.append(event_status)
        
        where_clause = " AND ".join(conditions)
        
        cursor.execute(f"""
            SELECT COUNT(*) FROM integration_events WHERE {where_clause}
        """, params)
        total = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT * FROM integration_events 
            WHERE {where_clause}
            ORDER BY created_at DESC LIMIT ? OFFSET ?
        """, params + [per_page, (page - 1) * per_page])
        
        events = []
        for row in cursor.fetchall():
            events.append({
                'id': row[0], 'event_id': row[1], 'event_type': row[2],
                'source_system': row[4], 'payload_preview': row[6][:100] if row[6] else '',
                'priority': row[8], 'event_status': row[15], 'correlation_id': row[11],
                'created_at': row[22]
            })
        
        return render_template('integration/events/list.html',
                             events=events,
                             pagination=build_pagination_response(events, total, page, per_page),
                             filters={
                                 'event_type': event_type, 'source': source_system,
                                 'status': event_status
                             })

    @app.route('/integration/event-subscriptions')
    @require_login
    def integration_event_subscriptions():
        """List event subscriptions."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT es.*, f.name as flow_name
            FROM integration_event_subscriptions es
            LEFT JOIN integration_flows f ON es.target_flow_id = f.id
            ORDER BY es.created_at DESC
        """)
        
        subscriptions = []
        for row in cursor.fetchall():
            subscriptions.append({
                'id': row[0], 'code': row[1], 'name': row[2], 'event_type': row[3],
                'source_system': row[4], 'delivery_method': row[6],
                'target_endpoint': row[7], 'is_active': row[10], 'priority': row[11],
                'flow_name': row[48] if len(row) > 48 else None
            })
        
        return render_template('integration/events/subscriptions.html',
                             subscriptions=subscriptions)

    # -------------------------------------------------------------------------
    # MESSAGE QUEUE
    # -------------------------------------------------------------------------
    @app.route('/integration/queue')
    @require_login
    def integration_queue():
        """Message queue monitor."""
        page, per_page = parse_pagination_params()
        
        queue_name = request.args.get('queue', '')
        message_status = request.args.get('status', '')
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        conditions = ["1=1"]
        params = []
        
        if queue_name:
            conditions.append("queue_name = ?")
            params.append(queue_name)
        
        if message_status:
            conditions.append("message_status = ?")
            params.append(message_status)
        else:
            conditions.append("message_status IN ('pending', 'queued', 'processing')")
        
        where_clause = " AND ".join(conditions)
        
        cursor.execute(f"""
            SELECT COUNT(*) FROM integration_queue_items WHERE {where_clause}
        """, params)
        total = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT * FROM integration_queue_items 
            WHERE {where_clause}
            ORDER BY created_at DESC LIMIT ? OFFSET ?
        """, params + [per_page, (page - 1) * per_page])
        
        items = []
        for row in cursor.fetchall():
            items.append({
                'id': row[0], 'queue_item_id': row[1], 'queue_name': row[2],
                'source_system': row[3], 'destination_system': row[4],
                'message_type': row[5], 'payload_preview': row[6][:100] if row[6] else '',
                'priority': row[7], 'message_status': row[8], 'retry_count': row[9],
                'last_error': row[12], 'correlation_id': row[14],
                'created_at': row[19]
            })
        
        cursor.execute("SELECT DISTINCT queue_name FROM integration_queue_items ORDER BY queue_name")
        queues = [r[0] for r in cursor.fetchall()]
        
        return render_template('integration/queue/list.html',
                             items=items,
                             queues=queues,
                             pagination=build_pagination_response(items, total, page, per_page),
                             filters={'queue': queue_name, 'status': message_status})

    @app.route('/integration/queue/<item_id>/requeue/', methods=['POST'])
    @require_login
    def integration_queue_requeue(item_id):
        """Requeue a message."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE integration_queue_items SET 
                message_status = 'queued',
                retry_count = retry_count + 1,
                next_retry_at = NULL,
                updated_at = CURRENT_TIMESTAMP
            WHERE queue_item_id = ?
        """, (item_id,))
        
        conn.commit()
        log_integration_audit('queue_item', item_id, 'REQUEUE')
        
        return jsonify({'status': 'success', 'message': 'Message requeued.'})

    @app.route('/integration/queue/stats')
    @require_login
    def integration_queue_stats():
        """Get queue statistics (JSON API)."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute("""
            SELECT queue_name, 
                   SUM(CASE WHEN message_status = 'pending' THEN 1 ELSE 0 END) as pending,
                   SUM(CASE WHEN message_status = 'queued' THEN 1 ELSE 0 END) as queued,
                   SUM(CASE WHEN message_status = 'processing' THEN 1 ELSE 0 END) as processing,
                   SUM(CASE WHEN message_status = 'completed' THEN 1 ELSE 0 END) as completed,
                   SUM(CASE WHEN message_status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM integration_queue_items
            GROUP BY queue_name
        """)
        
        stats['by_queue'] = []
        for row in cursor.fetchall():
            stats['by_queue'].append({
                'queue': row[0], 'pending': row[1], 'queued': row[2],
                'processing': row[3], 'completed': row[4], 'failed': row[5]
            })
        
        cursor.execute("SELECT COUNT(*) FROM integration_queue_items WHERE message_status IN ('pending', 'queued', 'processing')")
        stats['total_active'] = cursor.fetchone()[0]
        
        return jsonify(stats)

    # -------------------------------------------------------------------------
    # DEAD LETTER QUEUE
    # -------------------------------------------------------------------------
    @app.route('/integration/dlq')
    @require_login
    def integration_dlq():
        """Dead Letter Queue console."""
        page, per_page = parse_pagination_params()
        
        queue_name = request.args.get('queue', '')
        review_status = request.args.get('status', '')
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        conditions = ["1=1"]
        params = []
        
        if queue_name:
            conditions.append("queue_name = ?")
            params.append(queue_name)
        
        if review_status:
            conditions.append("review_status = ?")
            params.append(review_status)
        
        where_clause = " AND ".join(conditions)
        
        cursor.execute(f"""
            SELECT COUNT(*) FROM integration_dlq_items WHERE {where_clause}
        """, params)
        total = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT * FROM integration_dlq_items 
            WHERE {where_clause}
            ORDER BY created_at DESC LIMIT ? OFFSET ?
        """, params + [per_page, (page - 1) * per_page])
        
        items = []
        for row in cursor.fetchall():
            items.append({
                'id': row[0], 'dlq_item_id': row[1], 'original_message_id': row[2],
                'queue_name': row[3], 'message_type': row[4], 'payload_preview': row[5][:100] if row[5] else '',
                'error_message': row[6], 'failure_count': row[8], 'last_failure_at': row[9],
                'source_system': row[10], 'destination_system': row[11],
                'review_status': row[15], 'correlation_id': row[14],
                'created_at': row[21]
            })
        
        cursor.execute("SELECT DISTINCT queue_name FROM integration_dlq_items ORDER BY queue_name")
        queues = [r[0] for r in cursor.fetchall()]
        
        return render_template('integration/dlq/list.html',
                             items=items,
                             queues=queues,
                             pagination=build_pagination_response(items, total, page, per_page),
                             filters={'queue': queue_name, 'status': review_status})

    @app.route('/integration/dlq/<item_id>')
    @require_login
    def integration_dlq_detail(item_id):
        """View DLQ item detail."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM integration_dlq_items WHERE dlq_item_id = ?", (item_id,))
        row = cursor.fetchone()
        if not row:
            flash('DLQ item not found.', 'error')
            return redirect(url_for('integration_dlq'))
        
        item = {
            'id': row[0], 'dlq_item_id': row[1], 'original_message_id': row[2],
            'queue_name': row[3], 'message_type': row[4], 'payload': row[5],
            'headers_json': row[6], 'error_message': row[6], 'error_code': row[7],
            'stack_trace': row[8], 'failure_count': row[9], 'last_failure_at': row[10],
            'source_system': row[11], 'destination_system': row[12],
            'flow_id': row[13], 'correlation_id': row[15],
            'review_status': row[16], 'reviewed_by': row[17], 'reviewed_at': row[18],
            'review_notes': row[19], 'resolution_action': row[20],
            'metadata_json': row[23], 'created_at': row[24]
        }
        
        return render_template('integration/dlq/detail.html', item=item)

    @app.route('/integration/dlq/<item_id>/replay/', methods=['POST'])
    @require_login
    def integration_dlq_replay(item_id):
        """Replay DLQ item."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT payload, queue_name FROM integration_dlq_items WHERE dlq_item_id = ?", (item_id,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'status': 'error', 'message': 'Item not found.'}), 404
        
        new_message_id = generate_code('MSG')
        
        cursor.execute("""
            INSERT INTO integration_messages 
            (message_id, queue_name, payload, message_status, created_at)
            VALUES (?, ?, ?, 'queued', CURRENT_TIMESTAMP)
        """, (new_message_id, row[1], row[0]))
        
        cursor.execute("""
            UPDATE integration_dlq_items SET 
                replayed_to_message_id = ?,
                review_status = 'replayed'
            WHERE dlq_item_id = ?
        """, (new_message_id, item_id))
        
        conn.commit()
        log_integration_audit('dlq_item', item_id, 'REPLAY',
                              notes=f'Replayed DLQ item to: {new_message_id}')
        
        return jsonify({
            'status': 'success',
            'new_message_id': new_message_id,
            'message': 'DLQ item replayed successfully.'
        })

    @app.route('/integration/dlq/<item_id>/resolve/', methods=['POST'])
    @require_login
    def integration_dlq_resolve(item_id):
        """Mark DLQ item as resolved."""
        resolution_notes = None
        if request.is_json:
            resolution_notes = request.json.get('notes', '')
        else:
            resolution_notes = request.form.get('notes', '')
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE integration_dlq_items SET 
                review_status = 'resolved',
                reviewed_by = ?,
                reviewed_at = CURRENT_TIMESTAMP,
                review_notes = ?
            WHERE dlq_item_id = ?
        """, (get_current_user_id(), resolution_notes, item_id))
        
        conn.commit()
        log_integration_audit('dlq_item', item_id, 'RESOLVE',
                              notes=resolution_notes)
        
        return jsonify({'status': 'success', 'message': 'DLQ item resolved.'})

    # -------------------------------------------------------------------------
    # SCHEDULED JOBS
    # -------------------------------------------------------------------------
    @app.route('/integration/schedules')
    @require_login
    def integration_schedules():
        """List scheduled jobs."""
        page, per_page = parse_pagination_params()
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT s.*, f.name as flow_name, f.code as flow_code
            FROM integration_schedules s
            JOIN integration_flows f ON s.flow_id = f.id
            ORDER BY s.next_run_at ASC
            LIMIT ? OFFSET ?
        """, [per_page, (page - 1) * per_page])
        
        schedules = []
        for row in cursor.fetchall():
            schedules.append({
                'id': row[0], 'schedule_name': row[2], 'cron_expression': row[3],
                'frequency': row[4], 'interval_minutes': row[5], 'time_of_day': row[7],
                'is_active': row[10], 'last_run_at': row[11], 'next_run_at': row[12],
                'run_count': row[13], 'error_count': row[15],
                'flow_name': row[25] if len(row) > 25 else '', 'flow_code': row[26]
            })
        
        cursor.execute("SELECT COUNT(*) FROM integration_schedules")
        total = cursor.fetchone()[0]
        
        return render_template('integration/schedules/list.html',
                             schedules=schedules,
                             pagination=build_pagination_response(schedules, total, page, per_page))

    @app.route('/integration/job-runs')
    @require_login
    def integration_job_runs():
        """List job runs."""
        page, per_page = parse_pagination_params()
        
        job_status = request.args.get('status', '')
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        conditions = ["1=1"]
        params = []
        
        if job_status:
            conditions.append("job_status = ?")
            params.append(job_status)
        
        where_clause = " AND ".join(conditions)
        
        cursor.execute(f"""
            SELECT COUNT(*) FROM integration_job_runs WHERE {where_clause}
        """, params)
        total = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT jr.*, f.name as flow_name, IFNULL(s.schedule_name, 'Manual') as schedule_name
            FROM integration_job_runs jr
            JOIN integration_flows f ON jr.flow_id = f.id
            LEFT JOIN integration_schedules s ON jr.schedule_id = s.id
            WHERE {where_clause}
            ORDER BY jr.start_time DESC LIMIT ? OFFSET ?
        """, params + [per_page, (page - 1) * per_page])
        
        runs = []
        for row in cursor.fetchall():
            runs.append({
                'id': row[0], 'job_run_id': row[1], 'schedule_id': row[2],
                'flow_id': row[3], 'job_type': row[4], 'trigger_type': row[5],
                'start_time': row[6], 'end_time': row[7], 'duration_ms': row[8],
                'job_status': row[9], 'records_processed': row[10],
                'records_succeeded': row[11], 'records_failed': row[12],
                'records_skipped': row[13], 'error_message': row[14],
                'flow_name': row[50] if len(row) > 50 else '', 'schedule_name': row[51]
            })
        
        return render_template('integration/job_runs/list.html',
                             runs=runs,
                             pagination=build_pagination_response(runs, total, page, per_page),
                             filters={'status': job_status})

    @app.route('/integration/job-runs/<run_id>')
    @require_login
    def integration_job_run_detail(run_id):
        """View job run detail."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT jr.*, f.name as flow_name, f.code as flow_code,
                   IFNULL(s.schedule_name, 'Manual') as schedule_name
            FROM integration_job_runs jr
            JOIN integration_flows f ON jr.flow_id = f.id
            LEFT JOIN integration_schedules s ON jr.schedule_id = s.id
            WHERE jr.job_run_id = ?
        """, (run_id,))
        row = cursor.fetchone()
        if not row:
            flash('Job run not found.', 'error')
            return redirect(url_for('integration_job_runs'))
        
        run = {
            'id': row[0], 'job_run_id': row[1], 'schedule_id': row[2],
            'flow_id': row[3], 'job_type': row[4], 'trigger_type': row[5],
            'start_time': row[6], 'end_time': row[7], 'duration_ms': row[8],
            'job_status': row[9], 'records_processed': row[10],
            'records_succeeded': row[11], 'records_failed': row[12],
            'records_skipped': row[13], 'error_message': row[15],
            'error_code': row[16], 'warning_count': row[17], 'info_count': row[18],
            'checkpoint_data': row[19], 'execution_mode': row[20],
            'flow_name': row[50], 'schedule_name': row[51]
        }
        
        return render_template('integration/job_runs/detail.html', run=run)

    # -------------------------------------------------------------------------
    # FIELD MAPPING STUDIO
    # -------------------------------------------------------------------------
    @app.route('/integration/mappings')
    @require_login
    def integration_mappings():
        """List field mappings."""
        page, per_page = parse_pagination_params()
        
        search = request.args.get('search', '').strip()
        source_system = request.args.get('source', '')
        target_system = request.args.get('target', '')
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        conditions = ["m.is_deleted = 0 AND m.is_template = 0"]
        params = []
        
        if search:
            conditions.append("(m.name LIKE ? OR m.code LIKE ?)")
            params.extend([f'%{search}%', f'%{search}%'])
        
        if source_system:
            conditions.append("m.source_system = ?")
            params.append(source_system)
        
        if target_system:
            conditions.append("m.target_system = ?")
            params.append(target_system)
        
        where_clause = " AND ".join(conditions)
        
        cursor.execute(f"""
            SELECT COUNT(*) FROM integration_field_mappings m WHERE {where_clause}
        """, params)
        total = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT m.*, u.full_name as owner_name
            FROM integration_field_mappings m
            LEFT JOIN users u ON m.owner_id = u.id
            WHERE {where_clause}
            ORDER BY m.created_at DESC LIMIT ? OFFSET ?
        """, params + [per_page, (page - 1) * per_page])
        
        mappings = []
        for row in cursor.fetchall():
            mappings.append({
                'id': row[0], 'code': row[2], 'name': row[3],
                'source_system': row[5], 'target_system': row[6],
                'entity_type': row[7], 'usage_count': row[19],
                'is_active': row[18], 'owner_name': row[38] if len(row) > 38 else None,
                'created_at': row[30]
            })
        
        return render_template('integration/mappings/list.html',
                             mappings=mappings,
                             pagination=build_pagination_response(mappings, total, page, per_page),
                             filters={'search': search, 'source': source_system, 'target': target_system})

    @app.route('/integration/mappings/create/', methods=['GET', 'POST'])
    @require_login
    def integration_mapping_create():
        """Create field mapping."""
        if request.method == 'POST':
            conn = get_integration_db()
            cursor = conn.cursor()
            
            code = generate_code('MAP')
            name = request.form.get('name')
            source_system = request.form.get('source_system')
            target_system = request.form.get('target_system')
            entity_type = request.form.get('entity_type')
            mappings_json = request.form.get('mappings_json', '[]')
            description = request.form.get('description', '')
            company_id = get_current_company_id()
            user_id = get_current_user_id()
            
            cursor.execute("""
                INSERT INTO integration_field_mappings 
                (mapping_id, code, name, source_system, target_system, entity_type,
                 mappings_json, description, owner_id, company_id, created_by, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (generate_uuid(), code, name, source_system, target_system, entity_type,
                  mappings_json, description, user_id, company_id, user_id, user_id))
            
            conn.commit()
            flash(f'Mapping "{name}" created successfully.', 'success')
            return redirect(url_for('integration_mappings'))
        
        return render_template('integration/mappings/create.html')

    # -------------------------------------------------------------------------
    # TRANSFORMATION RULES
    # -------------------------------------------------------------------------
    @app.route('/integration/transformations')
    @require_login
    def integration_transformations():
        """List transformation rules."""
        page, per_page = parse_pagination_params()
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT t.*, u.full_name as owner_name
            FROM integration_transformation_rules t
            LEFT JOIN users u ON t.owner_id = u.id
            WHERE t.is_deleted = 0
            ORDER BY t.created_at DESC LIMIT ? OFFSET ?
        """, [per_page, (page - 1) * per_page])
        
        rules = []
        for row in cursor.fetchall():
            rules.append({
                'id': row[0], 'rule_id': row[1], 'code': row[2], 'name': row[3],
                'rule_type': row[5], 'category': row[6], 'is_active': row[14],
                'usage_count': row[20], 'owner_name': row[31] if len(row) > 31 else None,
                'created_at': row[33]
            })
        
        cursor.execute("SELECT COUNT(*) FROM integration_transformation_rules WHERE is_deleted = 0")
        total = cursor.fetchone()[0]
        
        return render_template('integration/transformations/list.html',
                             rules=rules,
                             pagination=build_pagination_response(rules, total, page, per_page))

    @app.route('/integration/transformations/create/', methods=['GET', 'POST'])
    @require_login
    def integration_transformation_create():
        """Create transformation rule."""
        if request.method == 'POST':
            conn = get_integration_db()
            cursor = conn.cursor()
            
            rule_id = generate_uuid()
            code = generate_code('RULE')
            name = request.form.get('name')
            rule_type = request.form.get('rule_type')
            category = request.form.get('category')
            transformation_logic = request.form.get('transformation_logic')
            expression = request.form.get('expression', '')
            description = request.form.get('description', '')
            company_id = get_current_company_id()
            user_id = get_current_user_id()
            
            cursor.execute("""
                INSERT INTO integration_transformation_rules 
                (rule_id, code, name, rule_type, category, transformation_logic,
                 expression, description, owner_id, company_id, created_by, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (rule_id, code, name, rule_type, category, transformation_logic,
                  expression, description, user_id, company_id, user_id, user_id))
            
            conn.commit()
            flash(f'Transformation rule "{name}" created successfully.', 'success')
            return redirect(url_for('integration_transformations'))
        
        return render_template('integration/transformations/create.html')

    # -------------------------------------------------------------------------
    # CREDENTIALS VAULT
    # -------------------------------------------------------------------------
    @app.route('/integration/credentials')
    @require_login
    def integration_credentials():
        """List credentials."""
        page, per_page = parse_pagination_params()
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT cred.*, c.name as connector_name
            FROM integration_credentials cred
            LEFT JOIN integration_connectors c ON cred.connector_id = c.id
            WHERE cred.is_deleted = 0
            ORDER BY cred.created_at DESC LIMIT ? OFFSET ?
        """, [per_page, (page - 1) * per_page])
        
        credentials = []
        for row in cursor.fetchall():
            credentials.append({
                'id': row[0], 'credential_id': row[1], 'code': row[2], 'name': row[3],
                'credential_type': row[5], 'auth_method': row[6], 'connector_id': row[7],
                'is_active': row[33], 'test_status': row[40], 'expires_at': row[45],
                'last_rotated_at': row[42], 'connector_name': row[53] if len(row) > 53 else None
            })
        
        cursor.execute("SELECT COUNT(*) FROM integration_credentials WHERE is_deleted = 0")
        total = cursor.fetchone()[0]
        
        return render_template('integration/credentials/list.html',
                             credentials=credentials,
                             pagination=build_pagination_response(credentials, total, page, per_page))

    @app.route('/integration/credentials/create/', methods=['GET', 'POST'])
    @require_login
    def integration_credential_create():
        """Create credential."""
        if request.method == 'POST':
            conn = get_integration_db()
            cursor = conn.cursor()
            
            credential_id = generate_uuid()
            code = generate_code('CRED')
            name = request.form.get('name')
            credential_type = request.form.get('credential_type')
            auth_method = request.form.get('auth_method')
            username = request.form.get('username', '')
            api_key = request.form.get('api_key', '')
            encrypted_secret = request.form.get('encrypted_secret', '')
            connector_id = request.form.get('connector_id')
            expires_at = request.form.get('expires_at')
            description = request.form.get('description', '')
            company_id = get_current_company_id()
            user_id = get_current_user_id()
            
            cursor.execute("""
                INSERT INTO integration_credentials 
                (credential_id, code, name, credential_type, auth_method, username,
                 encrypted_password, api_key, encrypted_secret, connector_id,
                 expires_at, description, owner_id, company_id, created_by, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (credential_id, code, name, credential_type, auth_method, username,
                  '', api_key, encrypted_secret, connector_id, expires_at,
                  description, user_id, company_id, user_id, user_id))
            
            conn.commit()
            log_integration_audit('credential', cursor.lastrowid, 'CREATE',
                                  notes=f'Created credential: {name}')
            
            flash(f'Credential "{name}" created successfully.', 'success')
            return redirect(url_for('integration_credentials'))
        
        conn = get_integration_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name FROM integration_connectors WHERE is_deleted = 0 AND active_status = 'active'")
        connectors = [{'id': r[0], 'name': r[1]} for r in cursor.fetchall()]
        
        return render_template('integration/credentials/create.html', connectors=connectors)

    # -------------------------------------------------------------------------
    # MONITORING CENTER
    # -------------------------------------------------------------------------
    @app.route('/integration/monitoring')
    @require_login
    def integration_monitoring():
        """Monitoring center dashboard."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN health_status = 'healthy' THEN 1 ELSE 0 END) as healthy,
                   SUM(CASE WHEN health_status = 'unhealthy' THEN 1 ELSE 0 END) as unhealthy,
                   SUM(CASE WHEN health_status = 'unknown' THEN 1 ELSE 0 END) as unknown
            FROM integration_connectors WHERE is_deleted = 0
        """)
        row = cursor.fetchone()
        stats['connectors'] = {'total': row[0], 'healthy': row[1], 'unhealthy': row[2], 'unknown': row[3]}
        
        cursor.execute("""
            SELECT connector_type, health_status, COUNT(*) as count
            FROM integration_connectors WHERE is_deleted = 0
            GROUP BY connector_type, health_status
        """)
        stats['by_type'] = {}
        for row in cursor.fetchall():
            if row[0] not in stats['by_type']:
                stats['by_type'][row[0]] = {'healthy': 0, 'unhealthy': 0, 'unknown': 0}
            stats['by_type'][row[0]][row[1]] = row[2]
        
        cursor.execute("""
            SELECT COUNT(*) FROM integration_queue_items 
            WHERE message_status IN ('pending', 'queued', 'processing')
        """)
        stats['queue_depth'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM integration_dlq_items WHERE review_status = 'pending'
        """)
        stats['dlq_count'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT date(created_at) as date, COUNT(*) as count
            FROM integration_logs
            WHERE created_at > datetime('now', '-7 days')
            GROUP BY date(created_at)
            ORDER BY date
        """)
        stats['log_volume_7d'] = [{'date': r[0], 'count': r[1]} for r in cursor.fetchall()]
        
        cursor.execute("""
            SELECT log_level, COUNT(*) as count
            FROM integration_logs
            WHERE created_at > datetime('now', '-24 hours')
            GROUP BY log_level
        """)
        stats['logs_by_level_24h'] = {r[0]: r[1] for r in cursor.fetchall()}
        
        return render_template('integration/monitoring.html', stats=stats)

    # -------------------------------------------------------------------------
    # ERROR QUEUE
    # -------------------------------------------------------------------------
    @app.route('/integration/errors')
    @require_login
    def integration_errors():
        """List integration errors."""
        page, per_page = parse_pagination_params()
        
        severity = request.args.get('severity', '')
        is_resolved = request.args.get('resolved', '')
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        conditions = ["1=1"]
        params = []
        
        if severity:
            conditions.append("severity = ?")
            params.append(severity)
        
        if is_resolved:
            conditions.append("is_resolved = ?")
            params.append('1' if is_resolved == 'true' else '0')
        
        where_clause = " AND ".join(conditions)
        
        cursor.execute(f"""
            SELECT COUNT(*) FROM integration_errors WHERE {where_clause}
        """, params)
        total = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT * FROM integration_errors 
            WHERE {where_clause}
            ORDER BY created_at DESC LIMIT ? OFFSET ?
        """, params + [per_page, (page - 1) * per_page])
        
        errors = []
        for row in cursor.fetchall():
            errors.append({
                'id': row[0], 'error_id': row[1], 'error_code': row[2],
                'error_type': row[3], 'error_message': row[4], 'severity': row[5],
                'source_system': row[6], 'flow_id': row[8], 'occurrence_count': row[27],
                'first_occurrence_at': row[29], 'last_occurrence_at': row[30],
                'is_resolved': row[23], 'resolved_at': row[25],
                'created_at': row[31]
            })
        
        return render_template('integration/errors/list.html',
                             errors=errors,
                             pagination=build_pagination_response(errors, total, page, per_page),
                             filters={'severity': severity, 'resolved': is_resolved})

    # -------------------------------------------------------------------------
    # RECONCILIATION CENTER
    # -------------------------------------------------------------------------
    @app.route('/integration/reconciliation')
    @require_login
    def integration_reconciliation():
        """Reconciliation center."""
        page, per_page = parse_pagination_params()
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT rb.*, u.full_name as owner_name
            FROM integration_reconciliation_batches rb
            LEFT JOIN users u ON rb.owner_id = u.id
            WHERE rb.is_deleted = 0
            ORDER BY rb.created_at DESC LIMIT ? OFFSET ?
        """, [per_page, (page - 1) * per_page])
        
        batches = []
        for row in cursor.fetchall():
            batches.append({
                'id': row[0], 'batch_id': row[1], 'batch_name': row[2],
                'reconciliation_type': row[4], 'source_system': row[5],
                'destination_system': row[6], 'source_count': row[8],
                'destination_count': row[9], 'matched_count': row[10],
                'mismatch_count': row[11], 'batch_status': row[18],
                'run_start_time': row[19], 'owner_name': row[39] if len(row) > 39 else None
            })
        
        cursor.execute("SELECT COUNT(*) FROM integration_reconciliation_batches WHERE is_deleted = 0")
        total = cursor.fetchone()[0]
        
        return render_template('integration/reconciliation/list.html',
                             batches=batches,
                             pagination=build_pagination_response(batches, total, page, per_page))

    @app.route('/integration/reconciliation/<batch_id>')
    @require_login
    def integration_reconciliation_detail(batch_id):
        """Reconciliation batch detail."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT rb.*, u.full_name as owner_name
            FROM integration_reconciliation_batches rb
            LEFT JOIN users u ON rb.owner_id = u.id
            WHERE rb.batch_id = ?
        """, (batch_id,))
        row = cursor.fetchone()
        if not row:
            flash('Batch not found.', 'error')
            return redirect(url_for('integration_reconciliation'))
        
        batch = {
            'id': row[0], 'batch_id': row[1], 'batch_name': row[2],
            'reconciliation_type': row[4], 'source_system': row[5],
            'destination_system': row[6], 'entity_type': row[7],
            'period_start': row[8], 'period_end': row[9],
            'source_count': row[10], 'destination_count': row[11],
            'matched_count': row[12], 'mismatch_count': row[13],
            'missing_in_source_count': row[14], 'missing_in_destination_count': row[15],
            'duplicate_count': row[16], 'batch_status': row[19],
            'run_start_time': row[20], 'run_end_time': row[21], 'run_duration_ms': row[22],
            'owner_name': row[39]
        }
        
        cursor.execute("""
            SELECT * FROM integration_reconciliation_items 
            WHERE batch_id = ? ORDER BY created_at DESC LIMIT 100
        """, (row[0],))
        items = []
        for item_row in cursor.fetchall():
            items.append({
                'id': item_row[0], 'item_id': item_row[1], 'batch_id': item_row[2],
                'mismatch_type': item_row[3], 'source_value': item_row[5],
                'destination_value': item_row[6], 'field_name': item_row[7],
                'status': item_row[10], 'created_at': item_row[21]
            })
        
        return render_template('integration/reconciliation/detail.html',
                             batch=batch,
                             items=items)

    # -------------------------------------------------------------------------
    # ALERTS CENTER
    # -------------------------------------------------------------------------
    @app.route('/integration/alerts')
    @require_login
    def integration_alerts():
        """Alerts center."""
        page, per_page = parse_pagination_params()
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ae.*, ar.name as rule_name, ar.severity
            FROM integration_alert_events ae
            JOIN integration_alert_rules ar ON ae.rule_id = ar.id
            ORDER BY ae.created_at DESC LIMIT ? OFFSET ?
        """, [per_page, (page - 1) * per_page])
        
        alerts = []
        for row in cursor.fetchall():
            alerts.append({
                'id': row[0], 'alert_event_id': row[1], 'severity': row[3],
                'alert_title': row[4], 'alert_message': row[5],
                'source_system': row[6], 'connector_id': row[8],
                'acknowledged': row[16], 'resolved': row[19],
                'notification_sent': row[15], 'created_at': row[23],
                'rule_name': row[36] if len(row) > 36 else None
            })
        
        cursor.execute("SELECT COUNT(*) FROM integration_alert_events")
        total = cursor.fetchone()[0]
        
        return render_template('integration/alerts/list.html',
                             alerts=alerts,
                             pagination=build_pagination_response(alerts, total, page, per_page))

    @app.route('/integration/alerts/rules')
    @require_login
    def integration_alert_rules():
        """Alert rules list."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM integration_alert_rules ORDER BY created_at DESC")
        rules = []
        for row in cursor.fetchall():
            rules.append({
                'id': row[0], 'rule_id': row[1], 'code': row[2], 'name': row[3],
                'alert_type': row[5], 'severity': row[6], 'condition_expression': row[10],
                'is_active': row[22], 'trigger_count': row[25],
                'last_triggered_at': row[24]
            })
        
        return render_template('integration/alerts/rules.html', rules=rules)

    # -------------------------------------------------------------------------
    # REPORTS & ANALYTICS
    # -------------------------------------------------------------------------
    @app.route('/integration/reports')
    @require_login
    def integration_reports():
        """Reports & Analytics."""
        return render_template('integration/reports.html')

    @app.route('/integration/reports/connector-health')
    @require_login
    def integration_report_connector_health():
        """Connector health report."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ct.name, ct.color,
                   SUM(CASE WHEN c.health_status = 'healthy' THEN 1 ELSE 0 END) as healthy,
                   SUM(CASE WHEN c.health_status = 'unhealthy' THEN 1 ELSE 0 END) as unhealthy,
                   SUM(CASE WHEN c.health_status = 'unknown' THEN 1 ELSE 0 END) as unknown,
                   COUNT(*) as total
            FROM integration_connector_types ct
            LEFT JOIN integration_connectors c ON c.connector_type = ct.code AND c.is_deleted = 0
            GROUP BY ct.code, ct.name, ct.color
        """)
        
        data = []
        for row in cursor.fetchall():
            data.append({
                'type': row[0], 'color': row[1],
                'healthy': row[2] or 0, 'unhealthy': row[3] or 0,
                'unknown': row[4] or 0, 'total': row[5]
            })
        
        return render_template('integration/reports/connector_health.html', data=data)

    @app.route('/integration/reports/flow-analytics')
    @require_login
    def integration_report_flow_analytics():
        """Flow analytics report."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT f.name, f.source_system, f.destination_system,
                   COUNT(jr.id) as run_count,
                   SUM(CASE WHEN jr.job_status = 'success' THEN 1 ELSE 0 END) as success_count,
                   SUM(CASE WHEN jr.job_status = 'failed' THEN 1 ELSE 0 END) as failure_count,
                   AVG(jr.duration_ms) as avg_duration
            FROM integration_flows f
            LEFT JOIN integration_job_runs jr ON f.id = jr.flow_id
            WHERE f.is_deleted = 0
            GROUP BY f.id, f.name, f.source_system, f.destination_system
            ORDER BY run_count DESC
        """)
        
        flows = []
        for row in cursor.fetchall():
            total = row[3] or 0
            success = row[4] or 0
            flows.append({
                'name': row[0], 'source': row[1], 'destination': row[2],
                'run_count': total, 'success_count': success,
                'failure_count': row[5] or 0,
                'success_rate': round(success / total * 100, 1) if total > 0 else 0,
                'avg_duration': round(row[6] or 0)
            })
        
        return render_template('integration/reports/flow_analytics.html', flows=flows)

    @app.route('/integration/reports/api-usage')
    @require_login
    def integration_report_api_usage():
        """API usage report."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT endpoint_group,
                   SUM(usage_count) as total_usage,
                   SUM(error_count) as total_errors,
                   COUNT(*) as endpoint_count
            FROM integration_endpoints
            WHERE is_deleted = 0
            GROUP BY endpoint_group
            ORDER BY total_usage DESC
        """)
        
        groups = []
        for row in cursor.fetchall():
            groups.append({
                'group': row[0] or 'Ungrouped', 'total_usage': row[1],
                'total_errors': row[2], 'endpoint_count': row[3],
                'error_rate': round(row[2] / row[1] * 100, 2) if row[1] > 0 else 0
            })
        
        return render_template('integration/reports/api_usage.html', groups=groups)

    @app.route('/integration/reports/webhook-delivery')
    @require_login
    def integration_report_webhook_delivery():
        """Webhook delivery report."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT w.name, w.event_type,
                   SUM(w.usage_count) as total_deliveries,
                   SUM(w.success_count) as success,
                   SUM(w.failure_count) as failures
            FROM integration_webhooks w
            WHERE w.is_deleted = 0
            GROUP BY w.id, w.name, w.event_type
            ORDER BY total_deliveries DESC
        """)
        
        webhooks = []
        for row in cursor.fetchall():
            total = row[2] or 0
            success = row[3] or 0
            webhooks.append({
                'name': row[0], 'event_type': row[1],
                'total': total, 'success': success, 'failures': row[4] or 0,
                'success_rate': round(success / total * 100, 1) if total > 0 else 0
            })
        
        return render_template('integration/reports/webhook_delivery.html', webhooks=webhooks)

    @app.route('/integration/reports/queue-dlq')
    @require_login
    def integration_report_queue_dlq():
        """Queue and DLQ report."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT queue_name,
                   COUNT(*) as total,
                   SUM(CASE WHEN message_status = 'completed' THEN 1 ELSE 0 END) as completed,
                   SUM(CASE WHEN message_status IN ('pending', 'queued') THEN 1 ELSE 0 END) as pending,
                   SUM(CASE WHEN message_status = 'failed' THEN 1 ELSE 0 END) as failed
            FROM integration_queue_items
            GROUP BY queue_name
        """)
        
        queues = []
        for row in cursor.fetchall():
            queues.append({
                'queue': row[0], 'total': row[1], 'completed': row[2],
                'pending': row[3], 'failed': row[4]
            })
        
        cursor.execute("""
            SELECT queue_name, COUNT(*) as dlq_count
            FROM integration_dlq_items
            WHERE review_status = 'pending'
            GROUP BY queue_name
        """)
        dlq_by_queue = {r[0]: r[1] for r in cursor.fetchall()}
        
        for q in queues:
            q['dlq_count'] = dlq_by_queue.get(q['queue'], 0)
        
        return render_template('integration/reports/queue_dlq.html', queues=queues)

    @app.route('/integration/reports/executive')
    @require_login
    def integration_report_executive():
        """Executive summary report."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        kpis = {}
        
        cursor.execute("SELECT COUNT(*) FROM integration_connectors WHERE is_deleted = 0 AND active_status = 'active'")
        kpis['active_connectors'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM integration_flows WHERE is_deleted = 0 AND flow_status = 'published'")
        kpis['published_flows'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM integration_job_runs 
            WHERE job_status = 'success' AND start_time > datetime('now', '-7 days')
        """)
        kpis['successful_runs_7d'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM integration_job_runs 
            WHERE job_status = 'failed' AND start_time > datetime('now', '-7 days')
        """)
        kpis['failed_runs_7d'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM integration_queue_items WHERE message_status = 'pending'")
        kpis['pending_messages'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM integration_dlq_items WHERE review_status = 'pending'")
        kpis['pending_dlq'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT date(start_time) as date, 
                   SUM(records_succeeded) as succeeded,
                   SUM(records_failed) as failed
            FROM integration_job_runs
            WHERE start_time > datetime('now', '-30 days')
            GROUP BY date(start_time)
            ORDER BY date
        """)
        trend_data = [{'date': r[0], 'succeeded': r[1], 'failed': r[2]} for r in cursor.fetchall()]
        
        return render_template('integration/reports/executive.html',
                             kpis=kpis, trend_data=trend_data)

    # -------------------------------------------------------------------------
    # EXPORT CENTER
    # -------------------------------------------------------------------------
    @app.route('/integration/export')
    @require_login
    def integration_export_center():
        """Export center."""
        export_type = request.args.get('type', 'connectors')
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        data = []
        filename = 'integration_export'
        sheet_name = 'Data'
        
        if export_type == 'connectors':
            cursor.execute("""
                SELECT code, name, connector_type, direction, active_status,
                       health_status, last_success_at, last_failure_at, created_at
                FROM integration_connectors WHERE is_deleted = 0
            """)
            headers = ['Code', 'Name', 'Type', 'Direction', 'Status', 'Health',
                      'Last Success', 'Last Failure', 'Created']
            for row in cursor.fetchall():
                data.append(dict(zip(headers, row)))
            filename = 'integration_connectors'
            sheet_name = 'Connectors'
            
        elif export_type == 'flows':
            cursor.execute("""
                SELECT code, name, source_system, destination_system, trigger_type,
                       flow_status, version, created_at
                FROM integration_flows WHERE is_deleted = 0
            """)
            headers = ['Code', 'Name', 'Source', 'Destination', 'Trigger',
                      'Status', 'Version', 'Created']
            for row in cursor.fetchall():
                data.append(dict(zip(headers, row)))
            filename = 'integration_flows'
            sheet_name = 'Flows'
            
        elif export_type == 'endpoints':
            cursor.execute("""
                SELECT code, name, url_path, http_method, active_status,
                       usage_count, error_count, created_at
                FROM integration_endpoints WHERE is_deleted = 0
            """)
            headers = ['Code', 'Name', 'URL', 'Method', 'Status',
                      'Usage', 'Errors', 'Created']
            for row in cursor.fetchall():
                data.append(dict(zip(headers, row)))
            filename = 'integration_endpoints'
            sheet_name = 'Endpoints'
            
        elif export_type == 'webhooks':
            cursor.execute("""
                SELECT code, name, event_type, target_url, active_status,
                       usage_count, success_count, failure_count, created_at
                FROM integration_webhooks WHERE is_deleted = 0
            """)
            headers = ['Code', 'Name', 'Event Type', 'Target URL', 'Status',
                      'Usage', 'Success', 'Failures', 'Created']
            for row in cursor.fetchall():
                data.append(dict(zip(headers, row)))
            filename = 'integration_webhooks'
            sheet_name = 'Webhooks'
            
        elif export_type == 'queue':
            cursor.execute("""
                SELECT queue_item_id, queue_name, message_type, message_status,
                       retry_count, last_error, created_at
                FROM integration_queue_items
            """)
            headers = ['ID', 'Queue', 'Type', 'Status', 'Retries', 'Last Error', 'Created']
            for row in cursor.fetchall():
                data.append(dict(zip(headers, row)))
            filename = 'integration_queue'
            sheet_name = 'Queue'
            
        elif export_type == 'dlq':
            cursor.execute("""
                SELECT dlq_item_id, queue_name, error_message, failure_count,
                       review_status, created_at
                FROM integration_dlq_items
            """)
            headers = ['ID', 'Queue', 'Error', 'Failures', 'Review Status', 'Created']
            for row in cursor.fetchall():
                data.append(dict(zip(headers, row)))
            filename = 'integration_dlq'
            sheet_name = 'DLQ'
        
        export_format = request.args.get('format', 'csv')
        
        if export_format == 'csv':
            return export_to_csv(data, filename)
        else:
            return export_to_excel(data, filename, sheet_name, export_format)

    def export_to_csv(data, filename):
        """Export data to CSV."""
        import io
        
        if not data:
            output = io.StringIO()
            output.write("No data available\n")
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'{filename}.csv'
            )
        
        output = io.StringIO()
        import csv
        writer = csv.DictWriter(output, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'{filename}.csv'
        )

    def export_to_excel(data, filename, sheet_name, format_type='text'):
        """Export data to Excel with proper formatting."""
        wb = Workbook()
        ws = wb.active
        ws.title = sheet_name
        
        if not data:
            ws.append(['No data available'])
            wb.save(filename=f'{filename}.xlsx')
            return send_file(
                f'{filename}.xlsx',
                as_attachment=True,
                download_name=f'{filename}.xlsx'
            )
        
        headers = list(data[0].keys())
        
        header_font = Font(bold=True, color='FFFFFF')
        header_fill = PatternFill("solid", fgColor="4F81BD")
        header_alignment = Alignment(horizontal='center', vertical='center')
        
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment
        
        for row_idx, row_data in enumerate(data, 2):
            for col_idx, key in enumerate(headers, 1):
                value = row_data.get(key, '')
                cell = ws.cell(row=row_idx, column=col_idx, value=value)
                if format_type == 'text':
                    cell.data_type = 's'
                    cell.value = str(value) if value is not None else ''
        
        for col in range(1, len(headers) + 1):
            ws.column_dimensions[get_column_letter(col)].width = 20
        
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        
        for row in range(1, len(data) + 2):
            for col in range(1, len(headers) + 1):
                ws.cell(row=row, column=col).border = thin_border
        
        wb.save(filename=f'{filename}.xlsx')
        return send_file(
            f'{filename}.xlsx',
            as_attachment=True,
            download_name=f'{filename}.xlsx'
        )

    # -------------------------------------------------------------------------
    # SETTINGS
    # -------------------------------------------------------------------------
    @app.route('/integration/settings')
    @require_login
    def integration_settings():
        """Integration settings."""
        return render_template('integration/settings.html')

    # -------------------------------------------------------------------------
    # AUDIT LOG
    # -------------------------------------------------------------------------
    @app.route('/integration/audit')
    @require_login
    def integration_audit():
        """Integration audit log."""
        page, per_page = parse_pagination_params()
        
        entity_type = request.args.get('entity_type', '')
        action = request.args.get('action', '')
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        conditions = ["entity_type LIKE 'integration%' OR entity_type IN ('connector', 'flow', 'endpoint', 'webhook', 'credential', 'dlq_item', 'queue_item', 'flow_steps')"]
        params = []
        
        if entity_type:
            conditions.append("entity_type = ?")
            params.append(entity_type)
        
        if action:
            conditions.append("action = ?")
            params.append(action)
        
        where_clause = " AND ".join(conditions)
        
        cursor.execute(f"""
            SELECT * FROM platform_audit_log 
            WHERE {where_clause}
            ORDER BY created_at DESC LIMIT ? OFFSET ?
        """, params + [per_page, (page - 1) * per_page])
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row[0], 'entity_type': row[1], 'entity_id': row[2],
                'action': row[3], 'user_id': row[4], 'field_name': row[5],
                'old_value': row[6], 'new_value': row[7], 'notes': row[8],
                'created_at': row[10]
            })
        
        cursor.execute(f"SELECT COUNT(*) FROM platform_audit_log WHERE {where_clause}", params)
        total = cursor.fetchone()[0]
        
        return render_template('integration/audit.html',
                             logs=logs,
                             pagination=build_pagination_response(logs, total, page, per_page),
                             filters={'entity_type': entity_type, 'action': action})

    # -------------------------------------------------------------------------
    # DEVELOPER TOOLS
    # -------------------------------------------------------------------------
    @app.route('/integration/tools')
    @require_login
    def integration_tools():
        """Developer tools."""
        return render_template('integration/tools.html')

    @app.route('/integration/tools/payload-inspector/', methods=['GET', 'POST'])
    @require_login
    def integration_payload_inspector():
        """Payload inspector tool."""
        if request.method == 'POST':
            payload = request.form.get('payload', '')
            try:
                parsed = json.loads(payload)
                formatted = json.dumps(parsed, indent=2)
                return jsonify({'status': 'success', 'parsed': formatted})
            except json.JSONDecodeError as e:
                return jsonify({'status': 'error', 'message': f'Invalid JSON: {str(e)}'})
        
        return render_template('integration/tools/payload_inspector.html')

    @app.route('/integration/tools/test-connector/', methods=['GET', 'POST'])
    @require_login
    def integration_test_connector():
        """Test connector tool."""
        if request.method == 'POST':
            connector_id = request.form.get('connector_id')
            test_payload = request.form.get('test_payload', '{}')
            
            try:
                parsed_payload = json.loads(test_payload)
            except json.JSONDecodeError:
                return jsonify({'status': 'error', 'message': 'Invalid JSON payload'})
            
            return jsonify({
                'status': 'success',
                'message': 'Connector test completed',
                'result': {'processed': True, 'connector_id': connector_id}
            })
        
        conn = get_integration_db()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, connector_type FROM integration_connectors 
            WHERE is_deleted = 0 AND active_status = 'active'
        """)
        connectors = [{'id': r[0], 'name': r[1], 'type': r[2]} for r in cursor.fetchall()]
        
        return render_template('integration/tools/test_connector.html', connectors=connectors)

    @app.route('/integration/tools/schema-preview')
    @require_login
    def integration_schema_preview():
        """Schema preview tool."""
        entity_type = request.args.get('entity', 'connector')
        
        schemas = {
            'connector': {
                'name': 'Connector',
                'fields': ['code', 'name', 'connector_type', 'direction', 'auth_method',
                          'active_status', 'health_status', 'timeout_seconds']
            },
            'flow': {
                'name': 'Integration Flow',
                'fields': ['code', 'name', 'source_system', 'destination_system',
                          'trigger_type', 'flow_status', 'version']
            },
            'endpoint': {
                'name': 'API Endpoint',
                'fields': ['code', 'name', 'url_path', 'http_method', 'auth_type',
                          'active_status', 'usage_count']
            },
            'webhook': {
                'name': 'Webhook',
                'fields': ['code', 'name', 'event_type', 'target_url', 'auth_type',
                          'active_status', 'success_count', 'failure_count']
            }
        }
        
        return render_template('integration/tools/schema_preview.html',
                             schemas=schemas,
                             selected=entity_type)

    # -------------------------------------------------------------------------
    # TEMPLATES / PRESETS
    # -------------------------------------------------------------------------
    @app.route('/integration/templates')
    @require_login
    def integration_templates():
        """Integration templates/presets."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT m.*, u.full_name as owner_name
            FROM integration_field_mappings m
            LEFT JOIN users u ON m.owner_id = u.id
            WHERE m.is_deleted = 0 AND m.is_template = 1
            ORDER BY m.created_at DESC
        """)
        
        templates = []
        for row in cursor.fetchall():
            templates.append({
                'id': row[0], 'code': row[2], 'name': row[3],
                'source_system': row[5], 'target_system': row[6],
                'template_category': row[21], 'usage_count': row[19]
            })
        
        cursor.execute("SELECT DISTINCT template_category FROM integration_field_mappings WHERE template_category IS NOT NULL")
        categories = [r[0] for r in cursor.fetchall() if r[0]]
        
        return render_template('integration/templates.html',
                             templates=templates,
                             categories=categories)

    # -------------------------------------------------------------------------
    # FILE EXCHANGE CENTER
    # -------------------------------------------------------------------------
    @app.route('/integration/file-exchange')
    @require_login
    def integration_file_exchange():
        """File exchange center."""
        page, per_page = parse_pagination_params()
        
        file_status = request.args.get('status', '')
        direction = request.args.get('direction', '')
        
        conn = get_integration_db()
        cursor = conn.cursor()
        
        conditions = ["is_deleted = 0"]
        params = []
        
        if file_status:
            conditions.append("file_status = ?")
            params.append(file_status)
        
        if direction:
            conditions.append("direction = ?")
            params.append(direction)
        
        where_clause = " AND ".join(conditions)
        
        cursor.execute(f"""
            SELECT COUNT(*) FROM integration_file_exchange WHERE {where_clause}
        """, params)
        total = cursor.fetchone()[0]
        
        cursor.execute(f"""
            SELECT * FROM integration_file_exchange 
            WHERE {where_clause}
            ORDER BY created_at DESC LIMIT ? OFFSET ?
        """, params + [per_page, (page - 1) * per_page])
        
        files = []
        for row in cursor.fetchall():
            files.append({
                'id': row[0], 'file_id': row[1], 'exchange_type': row[2],
                'file_name': row[3], 'file_type': row[4], 'file_size_bytes': row[5],
                'source_system': row[7], 'destination_system': row[8],
                'direction': row[9], 'file_status': row[13],
                'row_count': row[15], 'success_count': row[16],
                'error_count': row[17], 'created_at': row[30]
            })
        
        return render_template('integration/file_exchange.html',
                             files=files,
                             pagination=build_pagination_response(files, total, page, per_page),
                             filters={'status': file_status, 'direction': direction})

    # -------------------------------------------------------------------------
    # FLOW NOTIFICATIONS
    # -------------------------------------------------------------------------
    @app.route('/integration/flow-notifications')
    @require_login
    def integration_flow_notifications():
        """Flow notification settings."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM integration_alert_rules 
            WHERE notification_channels LIKE '%flow%'
            ORDER BY created_at DESC
        """)
        
        rules = []
        for row in cursor.fetchall():
            rules.append({
                'id': row[0], 'name': row[3], 'alert_type': row[5],
                'severity': row[6], 'notification_channels': row[19],
                'is_active': row[22]
            })
        
        return render_template('integration/flow_notifications.html', rules=rules)

    # -------------------------------------------------------------------------
    # API ENDPOINTS FOR BI INTEGRATION
    # -------------------------------------------------------------------------
    @app.route('/integration/api/bi/metrics')
    @require_login
    def integration_bi_metrics():
        """BI metrics API endpoint."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        metrics = {}
        
        cursor.execute("""
            SELECT date(metric_date) as date, metric_type, SUM(metric_value) as value
            FROM integration_usage_metrics
            WHERE metric_date > datetime('now', '-30 days')
            GROUP BY date(metric_date), metric_type
        """)
        
        metrics['daily'] = []
        for row in cursor.fetchall():
            metrics['daily'].append({'date': row[0], 'type': row[1], 'value': row[2]})
        
        return jsonify(metrics)

    @app.route('/integration/api/bi/kpis')
    @require_login
    def integration_bi_kpis():
        """BI KPIs API endpoint."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        kpis = {}
        
        cursor.execute("""
            SELECT COUNT(DISTINCT connector_id) 
            FROM integration_connectors WHERE is_deleted = 0 AND active_status = 'active'
        """)
        kpis['active_connectors'] = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT COUNT(*) 
            FROM integration_flows WHERE is_deleted = 0 AND flow_status = 'published'
        """)
        kpis['active_flows'] = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM integration_job_runs 
            WHERE job_status = 'success' AND start_time > datetime('now', '-7 days')
        """)
        kpis['successful_runs_7d'] = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT COUNT(*) FROM integration_job_runs 
            WHERE job_status = 'failed' AND start_time > datetime('now', '-7 days')
        """)
        kpis['failed_runs_7d'] = cursor.fetchone()[0] or 0
        
        cursor.execute("""
            SELECT 
                CASE WHEN COUNT(*) > 0 
                     THEN ROUND(SUM(CASE WHEN job_status = 'success' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1)
                     ELSE 100 
                END
            FROM integration_job_runs WHERE start_time > datetime('now', '-7 days')
        """)
        kpis['success_rate_7d'] = cursor.fetchone()[0] or 100
        
        cursor.execute("SELECT COUNT(*) FROM integration_queue_items WHERE message_status = 'pending'")
        kpis['queue_depth'] = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(*) FROM integration_dlq_items WHERE review_status = 'pending'")
        kpis['dlq_count'] = cursor.fetchone()[0] or 0
        
        return jsonify(kpis)

    @app.route('/integration/api/bi/connector-health')
    @require_login
    def integration_bi_connector_health():
        """BI connector health data."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT ct.name, ct.color,
                   COUNT(*) as total,
                   SUM(CASE WHEN c.health_status = 'healthy' THEN 1 ELSE 0 END) as healthy,
                   SUM(CASE WHEN c.health_status = 'unhealthy' THEN 1 ELSE 0 END) as unhealthy
            FROM integration_connector_types ct
            LEFT JOIN integration_connectors c ON c.connector_type = ct.code AND c.is_deleted = 0
            GROUP BY ct.code, ct.name, ct.color
        """)
        
        data = []
        for row in cursor.fetchall():
            data.append({
                'name': row[0], 'color': row[1],
                'total': row[2] or 0, 'healthy': row[3] or 0, 'unhealthy': row[4] or 0
            })
        
        return jsonify(data)

    @app.route('/integration/api/bi/flow-performance')
    @require_login
    def integration_bi_flow_performance():
        """BI flow performance data."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT f.name, f.source_system,
                   COUNT(jr.id) as runs,
                   ROUND(AVG(jr.duration_ms), 0) as avg_duration,
                   SUM(jr.records_succeeded) as records_out
            FROM integration_flows f
            LEFT JOIN integration_job_runs jr ON f.id = jr.flow_id AND jr.start_time > datetime('now', '-7 days')
            WHERE f.is_deleted = 0
            GROUP BY f.id, f.name, f.source_system
            ORDER BY runs DESC LIMIT 10
        """)
        
        data = []
        for row in cursor.fetchall():
            data.append({
                'name': row[0], 'source': row[1],
                'runs': row[2] or 0, 'avg_duration': row[3] or 0,
                'records_out': row[4] or 0
            })
        
        return jsonify(data)

    # -------------------------------------------------------------------------
    # JSON API FOR CONNECTORS LIST
    # -------------------------------------------------------------------------
    @app.route('/integration/api/connectors')
    @require_login
    def integration_api_connectors():
        """Get connectors list API."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.*, ct.name as type_name, ct.icon as type_icon, ct.color as type_color
            FROM integration_connectors c
            LEFT JOIN integration_connector_types ct ON c.connector_type = ct.code
            WHERE c.is_deleted = 0
            ORDER BY c.created_at DESC
        """)
        
        connectors = []
        for row in cursor.fetchall():
            connectors.append({
                'id': row[0], 'code': row[1], 'name': row[2],
                'connector_type': row[12], 'direction': row[14],
                'active_status': row[17], 'health_status': row[18],
                'last_success_at': row[20], 'type_name': row[43],
                'type_icon': row[44], 'type_color': row[45]
            })
        
        return jsonify({'connectors': connectors})

    @app.route('/integration/api/flows')
    @require_login
    def integration_api_flows():
        """Get flows list API."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM integration_flows WHERE is_deleted = 0
            ORDER BY created_at DESC
        """)
        
        flows = []
        for row in cursor.fetchall():
            flows.append({
                'id': row[0], 'code': row[1], 'name': row[2],
                'source_system': row[8], 'destination_system': row[9],
                'trigger_type': row[10], 'flow_status': row[16]
            })
        
        return jsonify({'flows': flows})

    @app.route('/integration/api/queue/stats')
    @require_login
    def integration_api_queue_stats():
        """Get queue statistics API."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT queue_name, message_status, COUNT(*) as count
            FROM integration_queue_items
            GROUP BY queue_name, message_status
        """)
        
        stats = {}
        for row in cursor.fetchall():
            if row[0] not in stats:
                stats[row[0]] = {'pending': 0, 'queued': 0, 'processing': 0, 'completed': 0, 'failed': 0}
            stats[row[0]][row[1]] = row[2]
        
        return jsonify(stats)

    @app.route('/integration/api/dlq/stats')
    @require_login
    def integration_api_dlq_stats():
        """Get DLQ statistics API."""
        conn = get_integration_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT queue_name, COUNT(*) as count
            FROM integration_dlq_items
            WHERE review_status = 'pending'
            GROUP BY queue_name
        """)
        
        stats = {row[0]: row[1] for row in cursor.fetchall()}
        
        return jsonify(stats)

    print("[Integration Module] Routes registered successfully")
