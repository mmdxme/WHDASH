"""
Technology Platform (BTP) Module - Routes and Controllers
=========================================================
Enterprise-grade Technology Platform module for the MMDx ERP system.

This module provides:
- Platform Overview / Control Tower
- Integration Suite (Connectors, Flows, Mappings)
- API Lifecycle Management
- Event & Webhook Management
- Data Exchange / Transformation
- Sync Jobs / Schedulers / Retry Center
- Extension Studio
- Environment & Configuration Center
- Monitoring & Diagnostics
- AI & External Service Connectors
- Flow-integrated Collaboration
- Reports & Analytics
- Administration

Author: Enterprise Architecture Team
Version: 1.0.0
"""

import functools
import json
import math
import re
import uuid
import csv
import io
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from flask import Flask, request, jsonify, render_template, session, send_file, redirect, url_for, flash, Response
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

import database as db_helper

# Import export utilities
from export_utils import (
    send_export_response,
    get_export_columns
)


def get_btp_db():
    """Get database connection."""
    return db_helper.get_db()


def init_btp_module(app: Flask):
    """
    Initialize the Technology Platform (BTP) module.
    Called during app startup via app.py register mechanism.
    """
    from btp_models import init_btp_tables, seed_btp_sample_data
    import database as db_helper

    conn = db_helper.get_db()
    cursor = conn.cursor()

    init_btp_tables()
    seed_btp_sample_data()

    print("[BTP Module] Technology Platform initialized successfully")


def require_permission(module: str, resource: str, action: str):
    """
    Permission decorator for BTP routes.
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


def get_current_user_name():
    """Get current user name from session."""
    return session.get('user_name', 'System')


def get_current_company_id():
    """Get current company ID from session."""
    return session.get('company_id')


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


def log_btp_audit(entity_type: str, entity_id: int, action: str,
                  user_id: int = None, notes: str = None,
                  old_value: str = None, new_value: str = None):
    """Log audit entry for BTP module."""
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


def export_to_excel_text(data: List[Dict], columns: List[str], title: str) -> Response:
    """Export data to Excel with all cells as Text."""
    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")

    for col_idx, col_key in enumerate(columns, 1):
        cell = ws.cell(row=1, column=col_idx, value=col_key.replace('_', ' ').title())
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment

    for row_idx, row in enumerate(data, 2):
        for col_idx, col_key in enumerate(columns, 1):
            value = row.get(col_key, '')
            if value is None:
                value = ''
            cell = ws.cell(row=row_idx, column=col_idx, value=str(value))
            cell.alignment = Alignment(horizontal="left", vertical="center")

    for col_idx in range(1, len(columns) + 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = 20

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return Response(output.getvalue(), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                   headers={'Content-Disposition': f'attachment; filename={title}.xlsx'})


def export_to_excel_general(data: List[Dict], columns: List[str], title: str) -> Response:
    """Export data to Excel with all cells as General format."""
    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    header_alignment = Alignment(horizontal="center", vertical="center")

    for col_idx, col_key in enumerate(columns, 1):
        cell = ws.cell(row=1, column=col_idx, value=col_key.replace('_', ' ').title())
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_alignment

    for row_idx, row in enumerate(data, 2):
        for col_idx, col_key in enumerate(columns, 1):
            value = row.get(col_key, '')
            if value is None:
                value = ''
            cell = ws.cell(row=row_idx, column=col_idx)
            try:
                if isinstance(value, (int, float)) and str(value).replace('.', '').replace('-', '').isdigit():
                    cell.value = value
                else:
                    cell.value = str(value)
            except:
                cell.value = str(value)
            cell.alignment = Alignment(horizontal="left", vertical="center")

    for col_idx in range(1, len(columns) + 1):
        ws.column_dimensions[get_column_letter(col_idx)].width = 20

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return Response(output.getvalue(), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                   headers={'Content-Disposition': f'attachment; filename={title}_general.xlsx'})


def export_to_csv(data: List[Dict], columns: List[str]) -> Response:
    """Export data to CSV."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    for row in data:
        writer.writerow({k: row.get(k, '') for k in columns})
    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv',
                   headers={'Content-Disposition': 'attachment; filename=export.csv'})


# =============================================================================
# EXPORT ENDPOINTS - ALL 20 EXPORT TYPES
# =============================================================================

BTP_EXPORT_TYPES = [
    'csv', 'excel_text', 'excel_general', 'json', 'xml', 'txt',
    'pdf', 'docx', 'html', 'printable', 'barcode', 'api',
    'email', 'zip', 'backup', 'sql_dump', 'dashboard',
    'summary', 'detailed', 'audit_log'
]

BTP_EXPORT_COLUMNS = {
    'connectors': ['connector_id', 'name', 'type', 'status', 'last_sync', 'config'],
    'flows': ['flow_id', 'name', 'status', 'trigger_type', 'created_at', 'last_run'],
    'api_clients': ['client_id', 'name', 'type', 'status', 'created_at', 'last_used'],
    'mappings': ['mapping_id', 'name', 'source_type', 'target_type', 'status', 'created_at'],
    'jobs': ['job_id', 'name', 'type', 'status', 'started_at', 'completed_at', 'records_processed'],
    'schedules': ['schedule_id', 'name', 'cron_expression', 'status', 'last_run', 'next_run'],
    'events': ['event_id', 'event_type', 'source', 'payload', 'created_at', 'processed'],
    'extensions': ['extension_id', 'name', 'type', 'status', 'version', 'created_at']
}


def register_btp_routes(app: Flask):
    """
    Register all Technology Platform (BTP) routes.
    This is the main entry point called from app.py.
    """

    # =========================================================================
    # API EXPORT ENDPOINTS
    # =========================================================================

    @app.route('/btp/api/export/<export_type>', methods=['GET', 'POST'])
    @app.route('/btp/api/export/<data_type>/<export_type>', methods=['GET', 'POST'])
    @require_login
    def api_btp_export(export_type, data_type=None):
        """Export BTP data in all 20 formats."""
        if export_type not in BTP_EXPORT_TYPES:
            return jsonify({
                'error': f'Invalid export type. Valid types: {BTP_EXPORT_TYPES}'
            }), 400

        conn = get_btp_db()
        cursor = conn.cursor()

        # Determine data type from URL or default
        if data_type is None:
            data_type = request.args.get('type', 'connectors')

        # Get data based on type
        if data_type == 'connectors':
            cursor.execute("SELECT * FROM btp_connectors ORDER BY created_at DESC LIMIT 5000")
            data = [dict(row) for row in cursor.fetchall()]
            columns = BTP_EXPORT_COLUMNS['connectors']
            title = 'BTP Connectors'
        elif data_type == 'flows':
            cursor.execute("SELECT * FROM btp_integration_flows ORDER BY created_at DESC LIMIT 5000")
            data = [dict(row) for row in cursor.fetchall()]
            columns = BTP_EXPORT_COLUMNS['flows']
            title = 'Integration Flows'
        elif data_type == 'api_clients':
            cursor.execute("SELECT * FROM btp_api_clients ORDER BY created_at DESC LIMIT 5000")
            data = [dict(row) for row in cursor.fetchall()]
            columns = BTP_EXPORT_COLUMNS['api_clients']
            title = 'API Clients'
        elif data_type == 'mappings':
            cursor.execute("SELECT * FROM btp_mappings ORDER BY created_at DESC LIMIT 5000")
            data = [dict(row) for row in cursor.fetchall()]
            columns = BTP_EXPORT_COLUMNS['mappings']
            title = 'Data Mappings'
        elif data_type == 'jobs':
            cursor.execute("SELECT * FROM btp_jobs ORDER BY created_at DESC LIMIT 5000")
            data = [dict(row) for row in cursor.fetchall()]
            columns = BTP_EXPORT_COLUMNS['jobs']
            title = 'Sync Jobs'
        elif data_type == 'schedules':
            cursor.execute("SELECT * FROM btp_schedules ORDER BY created_at DESC LIMIT 5000")
            data = [dict(row) for row in cursor.fetchall()]
            columns = BTP_EXPORT_COLUMNS['schedules']
            title = 'Schedules'
        elif data_type == 'events':
            cursor.execute("SELECT * FROM btp_events ORDER BY created_at DESC LIMIT 5000")
            data = [dict(row) for row in cursor.fetchall()]
            columns = BTP_EXPORT_COLUMNS['events']
            title = 'Events'
        elif data_type == 'extensions':
            cursor.execute("SELECT * FROM btp_extensions ORDER BY created_at DESC LIMIT 5000")
            data = [dict(row) for row in cursor.fetchall()]
            columns = BTP_EXPORT_COLUMNS['extensions']
            title = 'Extensions'
        else:
            return jsonify({'error': f'Data type {data_type} not supported'}), 400

        filename = f'btp_{data_type}_{datetime.now().strftime("%Y%m%d")}'

        return send_export_response(data, export_type, filename, columns, title)

    @app.route('/btp/api/export/list')
    @require_login
    def list_btp_export_types():
        """List available export types for BTP module."""
        return jsonify({
            'module': 'btp',
            'data_types': list(BTP_EXPORT_COLUMNS.keys()),
            'export_types': [{'type': t} for t in BTP_EXPORT_TYPES]
        })

    # =========================================================================
    # DASHBOARD - BTP Overview
    # =========================================================================

    @app.route('/btp')
    @app.route('/btp/dashboard')
    @require_login
    def btp_dashboard():
        """Main BTP overview dashboard - Platform Control Tower."""
        company_id = get_current_company_id()
        conn = get_btp_db()
        cursor = conn.cursor()

        stats = {}

        cursor.execute("SELECT COUNT(*) FROM btp_connectors WHERE is_active = 1")
        stats['active_connectors'] = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM btp_connectors")
        stats['total_connectors'] = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM btp_connectors WHERE last_failure > datetime('now', '-24 hours')")
        stats['failed_connectors_24h'] = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM btp_integration_flows WHERE status = 'active'")
        stats['active_flows'] = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM btp_integration_flows")
        stats['total_flows'] = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM btp_jobs WHERE DATE(created_at) = DATE('now')")
        stats['jobs_today'] = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM btp_jobs WHERE status = 'failed'")
        stats['failed_jobs'] = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM btp_jobs WHERE status = 'completed'")
        stats['completed_jobs'] = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM btp_retry_queue WHERE status = 'pending'")
        stats['pending_retries'] = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM btp_dead_letters WHERE status = 'failed'")
        stats['dead_letters'] = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM btp_api_catalog WHERE is_active = 1")
        stats['active_apis'] = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM btp_api_clients")
        stats['api_clients'] = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM btp_incidents WHERE status = 'open'")
        stats['open_incidents'] = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM btp_incidents WHERE severity = 'critical' AND status = 'open'")
        stats['critical_incidents'] = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM btp_feature_flags WHERE is_active = 1")
        stats['active_flags'] = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM btp_ai_providers WHERE is_active = 1")
        stats['active_ai_providers'] = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM btp_webhook_deliveries WHERE delivery_status = 'pending'")
        stats['pending_webhooks'] = cursor.fetchone()[0] or 0

        cursor.execute("SELECT COUNT(*) FROM btp_webhook_deliveries WHERE delivery_status = 'failed'")
        stats['failed_webhooks'] = cursor.fetchone()[0] or 0

        success_rate = 0
        if stats['jobs_today'] > 0:
            success_rate = round((stats['completed_jobs'] / stats['jobs_today']) * 100, 1)
        stats['success_rate'] = success_rate

        recent_incidents = []
        cursor.execute("""
            SELECT id, incident_code, title, severity, status, created_at
            FROM btp_incidents ORDER BY created_at DESC LIMIT 5
        """)
        for row in cursor.fetchall():
            recent_incidents.append({
                'id': row[0], 'incident_code': row[1], 'title': row[2],
                'severity': row[3], 'status': row[4], 'created_at': row[5]
            })

        recent_jobs = []
        cursor.execute("""
            SELECT id, job_id, name, job_type, status, created_at
            FROM btp_jobs ORDER BY created_at DESC LIMIT 10
        """)
        for row in cursor.fetchall():
            recent_jobs.append({
                'id': row[0], 'job_id': row[1], 'name': row[2],
                'job_type': row[3], 'status': row[4], 'created_at': row[5]
            })

        top_connectors = []
        cursor.execute("""
            SELECT id, name, code, category, health_score, status
            FROM btp_connectors ORDER BY health_score ASC LIMIT 5
        """)
        for row in cursor.fetchall():
            top_connectors.append({
                'id': row[0], 'name': row[1], 'code': row[2],
                'category': row[3], 'health_score': row[4], 'status': row[5]
            })

        top_apis = []
        cursor.execute("""
            SELECT id, api_name, api_code, owner_team, is_active
            FROM btp_api_catalog LIMIT 5
        """)
        for row in cursor.fetchall():
            top_apis.append({
                'id': row[0], 'api_name': row[1], 'api_code': row[2],
                'owner_team': row[3], 'is_active': row[4]
            })

        return render_template('btp/index.html',
                               stats=stats,
                               recent_incidents=recent_incidents,
                               recent_jobs=recent_jobs,
                               top_connectors=top_connectors,
                               top_apis=top_apis)

    # =========================================================================
    # CONNECTORS
    # =========================================================================

    @app.route('/btp/connectors')
    @require_login
    @require_permission('btp', 'connector', 'view')
    def btp_connectors():
        """List all BTP connectors."""
        conn = get_btp_db()
        cursor = conn.cursor()

        status_filter = request.args.get('status', '')
        category_filter = request.args.get('category', '')
        search = request.args.get('search', '')
        page, per_page = parse_pagination_params()
        sort, order = parse_sort_params()

        query = "SELECT * FROM btp_connectors WHERE 1=1"
        count_query = "SELECT COUNT(*) FROM btp_connectors WHERE 1=1"
        params = []
        count_params = []

        if status_filter:
            query += " AND status = ?"
            count_query += " AND status = ?"
            params.append(status_filter)
            count_params.append(status_filter)

        if category_filter:
            query += " AND category = ?"
            count_query += " AND category = ?"
            params.append(category_filter)
            count_params.append(category_filter)

        if search:
            query += " AND (name LIKE ? OR code LIKE ? OR description LIKE ?)"
            count_query += " AND (name LIKE ? OR code LIKE ? OR description LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])
            count_params.extend([search_param, search_param, search_param])

        total = cursor.execute(count_query, count_params).fetchone()[0]

        query += f" ORDER BY {sort} {order} LIMIT ? OFFSET ?"
        params.extend([per_page, (page - 1) * per_page])

        connectors = []
        for row in cursor.execute(query, params).fetchall():
            connectors.append(dict(row))

        categories = cursor.execute("SELECT DISTINCT category FROM btp_connectors ORDER BY category").fetchall()
        categories = [c[0] for c in categories if c[0]]

        return render_template('btp/connectors/index.html',
                               connectors=connectors,
                               categories=categories,
                               total=total,
                               page=page,
                               per_page=per_page)

    @app.route('/btp/connectors/<int:connector_id>', methods=['GET', 'POST'])
    @require_login
    @require_permission('btp', 'connector', 'view')
    def btp_connector_detail(connector_id):
        """Connector detail page."""
        conn = get_btp_db()
        cursor = conn.cursor()

        connector = cursor.execute("SELECT * FROM btp_connectors WHERE id = ?", (connector_id,)).fetchone()
        if not connector:
            flash('Connector not found.', 'error')
            return redirect(url_for('btp_connectors'))

        connector = dict(connector)

        logs = []
        cursor.execute("""
            SELECT * FROM btp_connector_logs
            WHERE connector_id = ? ORDER BY attempted_at DESC LIMIT 20
        """, (connector_id,))
        for row in cursor.execute("SELECT * FROM btp_connector_logs WHERE connector_id = ? ORDER BY attempted_at DESC LIMIT 20", (connector_id,)).fetchall():
            logs.append(dict(row))

        return render_template('btp/connectors/detail.html',
                               connector=connector,
                               logs=logs)

    @app.route('/btp/connectors/create', methods=['GET', 'POST'])
    @require_login
    @require_permission('btp', 'connector', 'create')
    def btp_connector_create():
        """Create new connector."""
        if request.method == 'POST':
            conn = get_btp_db()
            cursor = conn.cursor()

            name = request.form.get('name')
            code = request.form.get('code')
            category = request.form.get('category')
            direction = request.form.get('direction', 'bidirectional')
            source_system = request.form.get('source_system', '')
            target_system = request.form.get('target_system', '')
            auth_type = request.form.get('auth_type', '')
            base_url = request.form.get('base_url', '')
            file_format = request.form.get('file_format', '')
            owner = request.form.get('owner', '')
            team = request.form.get('team', '')
            environment = request.form.get('environment', 'production')
            timeout = int(request.form.get('timeout', 30))

            try:
                cursor.execute("""
                    INSERT INTO btp_connectors (name, code, category, direction, source_system,
                        target_system, auth_type, base_url, file_format, owner, team,
                        environment, timeout, created_by_user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, code, category, direction, source_system, target_system,
                      auth_type, base_url, file_format, owner, team, environment,
                      timeout, get_current_user_id()))
                conn.commit()

                log_btp_audit('btp_connector', cursor.lastrowid, 'create',
                              notes=f'Created connector: {name} ({code})')
                flash(f'Connector {name} created successfully.', 'success')
                return redirect(url_for('btp_connectors'))
            except Exception as e:
                flash(f'Error creating connector: {str(e)}', 'error')

        return render_template('btp/connectors/create.html')

    @app.route('/btp/connectors/<int:connector_id>/edit', methods=['GET', 'POST'])
    @require_login
    @require_permission('btp', 'connector', 'edit')
    def btp_connector_edit(connector_id):
        """Edit connector."""
        conn = get_btp_db()
        cursor = conn.cursor()

        connector = cursor.execute("SELECT * FROM btp_connectors WHERE id = ?", (connector_id,)).fetchone()
        if not connector:
            flash('Connector not found.', 'error')
            return redirect(url_for('btp_connectors'))

        if request.method == 'POST':
            name = request.form.get('name')
            category = request.form.get('category')
            direction = request.form.get('direction', 'bidirectional')
            source_system = request.form.get('source_system', '')
            target_system = request.form.get('target_system', '')
            auth_type = request.form.get('auth_type', '')
            base_url = request.form.get('base_url', '')
            file_format = request.form.get('file_format', '')
            owner = request.form.get('owner', '')
            team = request.form.get('team', '')
            environment = request.form.get('environment', 'production')
            timeout = int(request.form.get('timeout', 30))
            is_active = 1 if request.form.get('is_active') else 0

            try:
                cursor.execute("""
                    UPDATE btp_connectors SET name = ?, category = ?, direction = ?,
                        source_system = ?, target_system = ?, auth_type = ?, base_url = ?,
                        file_format = ?, owner = ?, team = ?, environment = ?, timeout = ?,
                        is_active = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (name, category, direction, source_system, target_system, auth_type,
                      base_url, file_format, owner, team, environment, timeout,
                      is_active, connector_id))
                conn.commit()

                log_btp_audit('btp_connector', connector_id, 'update',
                              notes=f'Updated connector: {name}')
                flash('Connector updated successfully.', 'success')
                return redirect(url_for('btp_connector_detail', connector_id=connector_id))
            except Exception as e:
                flash(f'Error updating connector: {str(e)}', 'error')

        connector = dict(connector)
        return render_template('btp/connectors/create.html', connector=connector)

    @app.route('/btp/connectors/<int:connector_id>/test')
    @require_login
    @require_permission('btp', 'connector', 'test')
    def btp_connector_test(connector_id):
        """Test connector connection."""
        conn = get_btp_db()
        cursor = conn.cursor()

        connector = cursor.execute("SELECT * FROM btp_connectors WHERE id = ?", (connector_id,)).fetchone()
        if not connector:
            return jsonify({'success': False, 'error': 'Connector not found'})

        cursor.execute("""
            INSERT INTO btp_connector_logs (connector_id, status, direction, attempted_at)
            VALUES (?, 'success', 'outbound', CURRENT_TIMESTAMP)
        """, (connector_id,))
        conn.commit()

        cursor.execute("UPDATE btp_connectors SET last_success = CURRENT_TIMESTAMP WHERE id = ?", (connector_id,))
        conn.commit()

        log_btp_audit('btp_connector', connector_id, 'test', notes='Connection test successful')
        return jsonify({'success': True, 'message': 'Connection test successful'})

    @app.route('/btp/connectors/export')
    @require_login
    @require_permission('btp', 'connector', 'export')
    def btp_connectors_export():
        """Export connectors to Excel/CSV."""
        conn = get_btp_db()
        cursor = conn.cursor()

        export_format = request.args.get('format', 'csv')
        columns = ['name', 'code', 'category', 'direction', 'status', 'health_score', 'owner', 'team', 'environment']

        connectors = []
        for row in cursor.execute("SELECT * FROM btp_connectors ORDER BY name").fetchall():
            connectors.append(dict(row))

        if export_format == 'excel-text':
            return export_to_excel_text(connectors, columns, 'btp_connectors')
        elif export_format == 'excel-general':
            return export_to_excel_general(connectors, columns, 'btp_connectors')
        elif export_format == 'json':
            return jsonify(connectors)
        else:
            return export_to_csv(connectors, columns)

    # =========================================================================
    # INTEGRATION FLOWS
    # =========================================================================

    @app.route('/btp/flows')
    @require_login
    @require_permission('btp', 'flow', 'view')
    def btp_flows():
        """List all integration flows."""
        conn = get_btp_db()
        cursor = conn.cursor()

        status_filter = request.args.get('status', '')
        search = request.args.get('search', '')
        page, per_page = parse_pagination_params()

        query = "SELECT * FROM btp_integration_flows WHERE 1=1"
        params = []

        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)

        if search:
            query += " AND (flow_name LIKE ? OR flow_code LIKE ?)"
            params.append(f'%{search}%')

        total = cursor.execute(f"SELECT COUNT(*) FROM ({query})", params).fetchone()[0]
        query += f" ORDER BY created_at DESC LIMIT {per_page} OFFSET {(page - 1) * per_page}"

        flows = []
        for row in cursor.execute(query, params).fetchall():
            flows.append(dict(row))

        return render_template('btp/flows/index.html',
                               flows=flows,
                               total=total,
                               page=page,
                               per_page=per_page)

    @app.route('/btp/flows/<int:flow_id>')
    @require_login
    @require_permission('btp', 'flow', 'view')
    def btp_flow_detail(flow_id):
        """Flow detail page."""
        conn = get_btp_db()
        cursor = conn.cursor()

        flow = cursor.execute("SELECT * FROM btp_integration_flows WHERE id = ?", (flow_id,)).fetchone()
        if not flow:
            flash('Flow not found.', 'error')
            return redirect(url_for('btp_flows'))

        flow = dict(flow)

        versions = []
        for row in cursor.execute("""
            SELECT * FROM btp_flow_versions WHERE flow_id = ? ORDER BY version_number DESC
        """, (flow_id,)).fetchall():
            versions.append(dict(row))

        return render_template('btp/flows/detail.html', flow=flow, versions=versions)

    @app.route('/btp/flows/create', methods=['GET', 'POST'])
    @require_login
    @require_permission('btp', 'flow', 'create')
    def btp_flow_create():
        """Create new integration flow."""
        if request.method == 'POST':
            conn = get_btp_db()
            cursor = conn.cursor()

            flow_name = request.form.get('flow_name')
            flow_code = request.form.get('flow_code')
            trigger_type = request.form.get('trigger_type', 'manual')
            schedule = request.form.get('schedule', '')
            source_entity = request.form.get('source_entity', '')
            target_entity = request.form.get('target_entity', '')
            owner = request.form.get('owner', '')

            try:
                cursor.execute("""
                    INSERT INTO btp_integration_flows (flow_name, flow_code, trigger_type, schedule,
                        source_entity, target_entity, owner, created_by_user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (flow_name, flow_code, trigger_type, schedule, source_entity, target_entity,
                      owner, get_current_user_id()))
                conn.commit()

                log_btp_audit('btp_flow', cursor.lastrowid, 'create',
                              notes=f'Created flow: {flow_name} ({flow_code})')
                flash(f'Flow {flow_name} created successfully.', 'success')
                return redirect(url_for('btp_flows'))
            except Exception as e:
                flash(f'Error creating flow: {str(e)}', 'error')

        return render_template('btp/flows/create.html')

    @app.route('/btp/flows/<int:flow_id>/run')
    @require_login
    @require_permission('btp', 'flow', 'run')
    def btp_flow_run(flow_id):
        """Run an integration flow."""
        conn = get_btp_db()
        cursor = conn.cursor()

        flow = cursor.execute("SELECT * FROM btp_integration_flows WHERE id = ?", (flow_id,)).fetchone()
        if not flow:
            return jsonify({'success': False, 'error': 'Flow not found'})

        job_id = generate_code('JOB')

        cursor.execute("""
            INSERT INTO btp_jobs (job_id, job_type, name, flow_id, status, run_mode,
                trigger_source, created_by_user_id)
            VALUES (?, 'flow', ?, ?, 'queued', 'manual', 'user_action', ?)
        """, (job_id, flow['flow_name'], flow_id, get_current_user_id()))
        conn.commit()

        log_btp_audit('btp_flow', flow_id, 'run', notes=f'Ran flow manually: {flow["flow_name"]}')
        return jsonify({'success': True, 'job_id': job_id, 'message': 'Flow queued for execution'})

    # =========================================================================
    # DATA MAPPINGS
    # =========================================================================

    @app.route('/btp/mappings')
    @require_login
    @require_permission('btp', 'mapping', 'view')
    def btp_mappings():
        """List all data mappings."""
        conn = get_btp_db()
        cursor = conn.cursor()

        status_filter = request.args.get('status', '')
        search = request.args.get('search', '')

        query = "SELECT * FROM btp_mappings WHERE 1=1"
        params = []

        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)

        if search:
            query += " AND (name LIKE ? OR code LIKE ?)"
            params.append(f'%{search}%')

        mappings = []
        for row in cursor.execute(query + " ORDER BY name", params).fetchall():
            mappings.append(dict(row))

        return render_template('btp/mappings/index.html', mappings=mappings)

    @app.route('/btp/mappings/create', methods=['GET', 'POST'])
    @require_login
    @require_permission('btp', 'mapping', 'create')
    def btp_mapping_create():
        """Create new data mapping."""
        if request.method == 'POST':
            conn = get_btp_db()
            cursor = conn.cursor()

            name = request.form.get('name')
            code = request.form.get('code')
            source_type = request.form.get('source_type', '')
            target_type = request.form.get('target_type', '')
            owner = request.form.get('owner', '')

            try:
                cursor.execute("""
                    INSERT INTO btp_mappings (name, code, source_type, target_type, owner, created_by_user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, code, source_type, target_type, owner, get_current_user_id()))
                conn.commit()

                log_btp_audit('btp_mapping', cursor.lastrowid, 'create',
                              notes=f'Created mapping: {name}')
                flash(f'Mapping {name} created successfully.', 'success')
                return redirect(url_for('btp_mappings'))
            except Exception as e:
                flash(f'Error creating mapping: {str(e)}', 'error')

        return render_template('btp/mappings/create.html')

    # =========================================================================
    # JOBS
    # =========================================================================

    @app.route('/btp/jobs')
    @require_login
    @require_permission('btp', 'job', 'view')
    def btp_jobs():
        """List all BTP jobs."""
        conn = get_btp_db()
        cursor = conn.cursor()

        status_filter = request.args.get('status', '')
        job_type_filter = request.args.get('job_type', '')
        page, per_page = parse_pagination_params()

        query = "SELECT * FROM btp_jobs WHERE 1=1"
        params = []

        if status_filter:
            query += " AND status = ?"
            params.append(status_filter)

        if job_type_filter:
            query += " AND job_type = ?"
            params.append(job_type_filter)

        total = cursor.execute(f"SELECT COUNT(*) FROM ({query})", params).fetchone()[0]
        query += f" ORDER BY created_at DESC LIMIT {per_page} OFFSET {(page - 1) * per_page}"

        jobs = []
        for row in cursor.execute(query, params).fetchall():
            jobs.append(dict(row))

        return render_template('btp/jobs/index.html',
                              jobs=jobs,
                              total=total,
                              page=page,
                              per_page=per_page)

    @app.route('/btp/jobs/<int:job_id>')
    @require_login
    @require_permission('btp', 'job', 'view')
    def btp_job_detail(job_id):
        """Job detail page."""
        conn = get_btp_db()
        cursor = conn.cursor()

        job = cursor.execute("SELECT * FROM btp_jobs WHERE id = ?", (job_id,)).fetchone()
        if not job:
            flash('Job not found.', 'error')
            return redirect(url_for('btp_jobs'))

        job = dict(job)

        attempts = []
        for row in cursor.execute("""
            SELECT * FROM btp_job_attempts WHERE job_id = ? ORDER BY attempt_number DESC
        """, (job_id,)).fetchall():
            attempts.append(dict(row))

        return render_template('btp/jobs/detail.html', job=job, attempts=attempts)

    @app.route('/btp/jobs/<int:job_id>/retry')
    @require_login
    @require_permission('btp', 'job', 'retry')
    def btp_job_retry(job_id):
        """Retry a failed job."""
        conn = get_btp_db()
        cursor = conn.cursor()

        job = cursor.execute("SELECT * FROM btp_jobs WHERE id = ?", (job_id,)).fetchone()
        if not job:
            return jsonify({'success': False, 'error': 'Job not found'})

        cursor.execute("UPDATE btp_jobs SET status = 'queued', attempts = attempts + 1 WHERE id = ?", (job_id,))
        conn.commit()

        log_btp_audit('btp_job', job_id, 'retry', notes=f'Retrying job: {job["job_id"]}')
        return jsonify({'success': True, 'message': 'Job queued for retry'})

    @app.route('/btp/jobs/run-now', methods=['POST'])
    @require_login
    @require_permission('btp', 'job', 'run')
    def btp_job_run_now():
        """Run a job immediately."""
        job_type = request.form.get('job_type', 'manual')
        name = request.form.get('name', 'Manual Job')
        connector_id = request.form.get('connector_id')

        conn = get_btp_db()
        cursor = conn.cursor()

        job_id = generate_code('JOB')

        cursor.execute("""
            INSERT INTO btp_jobs (job_id, job_type, name, connector_id, status, run_mode,
                trigger_source, created_by_user_id)
            VALUES (?, ?, ?, ?, 'queued', 'manual', 'user_action', ?)
        """, (job_id, job_type, name, connector_id, get_current_user_id()))
        conn.commit()

        log_btp_audit('btp_job', cursor.lastrowid, 'run',
                      notes=f'Run job manually: {name}')
        flash('Job queued for execution.', 'success')
        return redirect(url_for('btp_jobs'))

    # =========================================================================
    # RETRY CENTER
    # =========================================================================

    @app.route('/btp/retry-center')
    @require_login
    @require_permission('btp', 'job', 'view')
    def btp_retry_center():
        """Retry queue management."""
        conn = get_btp_db()
        cursor = conn.cursor()

        retries = []
        for row in cursor.execute("""
            SELECT r.*, j.job_id, j.name as job_name
            FROM btp_retry_queue r
            LEFT JOIN btp_jobs j ON r.job_id = j.id
            ORDER BY r.created_at DESC LIMIT 100
        """).fetchall():
            retries.append(dict(row))

        return render_template('btp/retry_center.html', retries=retries)

    @app.route('/btp/retry-center/<int:retry_id>/retry')
    @require_login
    @require_permission('btp', 'job', 'retry')
    def btp_retry(retry_id):
        """Retry a specific item."""
        conn = get_btp_db()
        cursor = conn.cursor()

        retry = cursor.execute("SELECT * FROM btp_retry_queue WHERE id = ?", (retry_id,)).fetchone()
        if not retry:
            return jsonify({'success': False, 'error': 'Retry item not found'})

        cursor.execute("UPDATE btp_retry_queue SET status = 'completed', next_retry_at = NULL WHERE id = ?", (retry_id,))
        conn.commit()

        log_btp_audit('btp_retry', retry_id, 'retry', notes='Retried from retry center')
        return jsonify({'success': True, 'message': 'Retry completed'})

    # =========================================================================
    # DEAD LETTER QUEUE
    # =========================================================================

    @app.route('/btp/dlq')
    @require_login
    @require_permission('btp', 'job', 'view')
    def btp_dlq():
        """Dead letter queue management."""
        conn = get_btp_db()
        cursor = conn.cursor()

        dlq_items = []
        for row in cursor.execute("""
            SELECT d.*, c.name as connector_name, j.job_id, j.name as job_name
            FROM btp_dead_letters d
            LEFT JOIN btp_connectors c ON d.connector_id = c.id
            LEFT JOIN btp_jobs j ON d.job_id = j.id
            ORDER BY d.created_at DESC LIMIT 100
        """).fetchall():
            dlq_items.append(dict(row))

        return render_template('btp/dlq.html', dlq_items=dlq_items)

    @app.route('/btp/dlq/<int:dlq_id>/replay')
    @require_login
    @require_permission('btp', 'job', 'retry')
    def btp_dlq_replay(dlq_id):
        """Replay a dead letter item."""
        conn = get_btp_db()
        cursor = conn.cursor()

        dlq = cursor.execute("SELECT * FROM btp_dead_letters WHERE id = ?", (dlq_id,)).fetchone()
        if not dlq:
            return jsonify({'success': False, 'error': 'DLQ item not found'})

        cursor.execute("UPDATE btp_dead_letters SET status = 'replayed' WHERE id = ?", (dlq_id,))
        conn.commit()

        log_btp_audit('btp_dlq', dlq_id, 'replay', notes='Replayed from DLQ')
        return jsonify({'success': True, 'message': 'Item replayed successfully'})

    # =========================================================================
    # API MANAGEMENT
    # =========================================================================

    @app.route('/btp/api/catalog')
    @require_login
    @require_permission('btp', 'api', 'view')
    def btp_api_catalog():
        """API catalog."""
        conn = get_btp_db()
        cursor = conn.cursor()

        apis = []
        for row in cursor.execute("SELECT * FROM btp_api_catalog ORDER BY api_name").fetchall():
            apis.append(dict(row))

        return render_template('btp/api/index.html', apis=apis)

    @app.route('/btp/api/clients')
    @require_login
    @require_permission('btp', 'api', 'view')
    def btp_api_clients():
        """API clients."""
        conn = get_btp_db()
        cursor = conn.cursor()

        clients = []
        for row in cursor.execute("""
            SELECT c.*, a.api_name
            FROM btp_api_clients c
            LEFT JOIN btp_api_catalog a ON c.api_id = a.id
            ORDER BY c.client_name
        """).fetchall():
            clients.append(dict(row))

        return render_template('btp/api/clients.html', clients=clients)

    @app.route('/btp/api/clients/create', methods=['GET', 'POST'])
    @require_login
    @require_permission('btp', 'api', 'client_manage')
    def btp_api_client_create():
        """Create API client."""
        if request.method == 'POST':
            conn = get_btp_db()
            cursor = conn.cursor()

            client_name = request.form.get('client_name')
            client_code = request.form.get('client_code')
            api_id = request.form.get('api_id')
            scopes = request.form.get('scopes', '')

            try:
                cursor.execute("""
                    INSERT INTO btp_api_clients (client_name, client_code, api_id, scopes,
                        owner_user_id, created_by_user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (client_name, client_code, api_id, scopes,
                      get_current_user_id(), get_current_user_id()))
                conn.commit()

                log_btp_audit('btp_api_client', cursor.lastrowid, 'create',
                              notes=f'Created API client: {client_name}')
                flash(f'API client {client_name} created successfully.', 'success')
                return redirect(url_for('btp_api_clients'))
            except Exception as e:
                flash(f'Error creating API client: {str(e)}', 'error')

        return render_template('btp/api/client_create.html')

    @app.route('/btp/api/keys/generate', methods=['POST'])
    @require_login
    @require_permission('btp', 'api', 'key_manage')
    def btp_api_key_generate():
        """Generate API key."""
        client_id = request.form.get('client_id')

        conn = get_btp_db()
        cursor = conn.cursor()

        key_prefix = f"BTP_{uuid.uuid4().hex[:8].upper()}"
        key_hash = uuid.uuid4().hex

        cursor.execute("""
            UPDATE btp_api_clients SET key_prefix = ?, key_hash = ?,
                updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (key_prefix, key_hash, client_id))
        conn.commit()

        log_btp_audit('btp_api_client', client_id, 'key_generate',
                      notes=f'Generated new API key for client')
        return jsonify({'success': True, 'key_prefix': key_prefix, 'key': f"{key_prefix}-{key_hash}"})

    # =========================================================================
    # EVENTS
    # =========================================================================

    @app.route('/btp/events')
    @require_login
    @require_permission('btp', 'event', 'view')
    def btp_events():
        """Event registry."""
        conn = get_btp_db()
        cursor = conn.cursor()

        events = []
        for row in cursor.execute("SELECT * FROM btp_events ORDER BY event_type").fetchall():
            events.append(dict(row))

        return render_template('btp/events/index.html', events=events)

    @app.route('/btp/events/subscriptions')
    @require_login
    @require_permission('btp', 'event', 'view')
    def btp_event_subscriptions():
        """Event subscriptions."""
        conn = get_btp_db()
        cursor = conn.cursor()

        subscriptions = []
        for row in cursor.execute("""
            SELECT s.*, e.name as event_name
            FROM btp_event_subscriptions s
            LEFT JOIN btp_events e ON s.event_type = e.event_type
            ORDER BY s.created_at DESC
        """).fetchall():
            subscriptions.append(dict(row))

        return render_template('btp/events/subscriptions.html', subscriptions=subscriptions)

    @app.route('/btp/events/replay', methods=['POST'])
    @require_login
    @require_permission('btp', 'event', 'replay')
    def btp_event_replay():
        """Replay an event."""
        event_type = request.form.get('event_type')

        log_btp_audit('btp_event', 0, 'replay', notes=f'Replayed event: {event_type}')
        return jsonify({'success': True, 'message': f'Event {event_type} replayed'})

    # =========================================================================
    # EXTENSIONS
    # =========================================================================

    @app.route('/btp/extensions/fields')
    @require_login
    @require_permission('btp', 'extension', 'view')
    def btp_extension_fields():
        """Custom fields registry."""
        conn = get_btp_db()
        cursor = conn.cursor()

        fields = []
        for row in cursor.execute("SELECT * FROM btp_extension_fields ORDER BY entity_type, display_order").fetchall():
            fields.append(dict(row))

        return render_template('btp/extensions/fields.html', fields=fields)

    @app.route('/btp/extensions/rules')
    @require_login
    @require_permission('btp', 'extension', 'view')
    def btp_extension_rules():
        """Automation rules."""
        conn = get_btp_db()
        cursor = conn.cursor()

        rules = []
        for row in cursor.execute("SELECT * FROM btp_extension_rules ORDER BY priority DESC").fetchall():
            rules.append(dict(row))

        return render_template('btp/extensions/rules.html', rules=rules)

    # =========================================================================
    # AI PROVIDERS
    # =========================================================================

    @app.route('/btp/ai-providers')
    @require_login
    @require_permission('btp', 'ai_provider', 'view')
    def btp_ai_providers():
        """AI providers management."""
        conn = get_btp_db()
        cursor = conn.cursor()

        providers = []
        for row in cursor.execute("SELECT * FROM btp_ai_providers ORDER BY provider_name").fetchall():
            providers.append(dict(row))

        return render_template('btp/ai_providers/index.html', providers=providers)

    @app.route('/btp/ai-providers/create', methods=['GET', 'POST'])
    @require_login
    @require_permission('btp', 'ai_provider', 'manage')
    def btp_ai_provider_create():
        """Create AI provider."""
        if request.method == 'POST':
            conn = get_btp_db()
            cursor = conn.cursor()

            provider_name = request.form.get('provider_name')
            provider_code = request.form.get('provider_code')
            provider_type = request.form.get('provider_type', 'openai')
            api_endpoint = request.form.get('api_endpoint', '')
            model_name = request.form.get('model_name', '')

            try:
                cursor.execute("""
                    INSERT INTO btp_ai_providers (provider_name, provider_code, provider_type,
                        api_endpoint, model_name, owner_team, created_by_user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (provider_name, provider_code, provider_type, api_endpoint, model_name,
                      get_current_user_id(), get_current_user_id()))
                conn.commit()

                log_btp_audit('btp_ai_provider', cursor.lastrowid, 'create',
                              notes=f'Created AI provider: {provider_name}')
                flash(f'AI provider {provider_name} created successfully.', 'success')
                return redirect(url_for('btp_ai_providers'))
            except Exception as e:
                flash(f'Error creating AI provider: {str(e)}', 'error')

        return render_template('btp/ai_providers/create.html')

    @app.route('/ai')
    @require_login
    def ai_copilot():
        """AI Copilot - Intelligent Assistant."""
        conn = get_btp_db()
        cursor = conn.cursor()

        providers = []
        for row in cursor.execute("SELECT * FROM btp_ai_providers WHERE is_active = 1 ORDER BY provider_name").fetchall():
            providers.append(dict(row))

        recent_chats = []
        for row in cursor.execute("""
            SELECT id, title, created_at, message_count
            FROM btp_ai_chats
            WHERE user_id = ? AND is_active = 1
            ORDER BY updated_at DESC LIMIT 10
        """, (get_current_user_id(),)).fetchall():
            recent_chats.append(dict(row))

        return render_template('btp/ai/index.html',
                             providers=providers,
                             recent_chats=recent_chats)

    @app.route('/ai/send', methods=['POST'])
    @require_login
    def ai_send_message():
        """Send a message to AI and get response."""
        import requests

        data = request.get_json()
        message = data.get('message', '').strip()
        provider_id = data.get('provider_id')
        chat_id = data.get('chat_id')

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        conn = get_btp_db()
        cursor = conn.cursor()

        if not provider_id:
            cursor.execute("SELECT * FROM btp_ai_providers WHERE is_active = 1 ORDER BY provider_name LIMIT 1")
            provider = cursor.fetchone()
            if not provider:
                return jsonify({'error': 'No AI provider configured. Please configure an AI provider in BTP > AI Providers.'}), 400
            provider = dict(provider)
        else:
            cursor.execute("SELECT * FROM btp_ai_providers WHERE id = ? AND is_active = 1", (provider_id,))
            provider = cursor.fetchone()
            if not provider:
                return jsonify({'error': 'AI provider not found or inactive'}), 400
            provider = dict(provider)

        api_key = provider.get('api_key') or ''
        model_name = provider.get('model_name', 'gpt-4')
        provider_type = provider.get('provider_type', 'openai')

        try:
            if provider_type == 'openai':
                headers = {
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                }
                payload = {
                    'model': model_name,
                    'messages': [{'role': 'user', 'content': message}],
                    'max_tokens': 1000
                }
                resp = requests.post(
                    f"{provider['api_endpoint'].rstrip('/')}/chat/completions",
                    headers=headers, json=payload, timeout=30
                )
                if resp.status_code == 200:
                    result = resp.json()
                    reply = result['choices'][0]['message']['content']
                else:
                    reply = f"OpenAI API error: {resp.status_code} - {resp.text}"

            elif provider_type == 'azure':
                headers = {
                    'Content-Type': 'application/json',
                    'api-key': api_key
                }
                payload = {
                    'messages': [{'role': 'user', 'content': message}],
                    'max_tokens': 1000
                }
                resp = requests.post(
                    f"{provider['api_endpoint'].rstrip('/')}/chat/completions?api-version=2024-02-01",
                    headers=headers, json=payload, timeout=30
                )
                if resp.status_code == 200:
                    result = resp.json()
                    reply = result['choices'][0]['message']['content']
                else:
                    reply = f"Azure OpenAI error: {resp.status_code} - {resp.text}"

            elif provider_type == 'anthropic':
                headers = {
                    'x-api-key': api_key,
                    'Content-Type': 'application/json',
                    'anthropic-version': '2023-06-01'
                }
                payload = {
                    'model': model_name,
                    'max_tokens': 1000,
                    'messages': [{'role': 'user', 'content': message}]
                }
                resp = requests.post(
                    f"{provider['api_endpoint'].rstrip('/')}/v1/messages",
                    headers=headers, json=payload, timeout=30
                )
                if resp.status_code == 200:
                    result = resp.json()
                    reply = result['content'][0]['text']
                else:
                    reply = f"Anthropic API error: {resp.status_code} - {resp.text}"

            elif provider_type == 'google':
                headers = {
                    'Content-Type': 'application/json'
                }
                payload = {
                    'contents': [{'parts': [{'text': message}]}]
                }
                resp = requests.post(
                    f"{provider['api_endpoint'].rstrip('/')}/v1beta/models/{model_name}:generateContent?key={api_key}",
                    headers=headers, json=payload, timeout=30
                )
                if resp.status_code == 200:
                    result = resp.json()
                    reply = result['candidates'][0]['content']['parts'][0]['text']
                else:
                    reply = f"Google Gemini error: {resp.status_code} - {resp.text}"

            else:
                reply = f"Unsupported provider type: {provider_type}"

        except requests.exceptions.Timeout:
            reply = "Request timed out. Please try again."
        except requests.exceptions.ConnectionError:
            reply = f"Could not connect to {provider_type} endpoint. Please check configuration."
        except Exception as e:
            reply = f"Error: {str(e)}"

        if chat_id:
            cursor.execute("""
                INSERT INTO btp_ai_messages (chat_id, provider_id, role, content, tokens_used)
                VALUES (?, ?, 'user', ?, 0)
            """, (chat_id, provider['id'], message))
            cursor.execute("""
                INSERT INTO btp_ai_messages (chat_id, provider_id, role, content, tokens_used)
                VALUES (?, ?, 'assistant', ?, 0)
            """, (chat_id, provider['id'], reply))
            cursor.execute("UPDATE btp_ai_chats SET updated_at = CURRENT_TIMESTAMP, message_count = message_count + 2 WHERE id = ?", (chat_id,))
        else:
            cursor.execute("""
                INSERT INTO btp_ai_chats (user_id, title, message_count, is_active)
                VALUES (?, ?, 2, 1)
            """, (get_current_user_id(), message[:50]))
            new_chat_id = cursor.lastrowid
            cursor.execute("""
                INSERT INTO btp_ai_messages (chat_id, provider_id, role, content, tokens_used)
                VALUES (?, ?, 'user', ?, 0)
            """, (new_chat_id, provider['id'], message))
            cursor.execute("""
                INSERT INTO btp_ai_messages (chat_id, provider_id, role, content, tokens_used)
                VALUES (?, ?, 'assistant', ?, 0)
            """, (new_chat_id, provider['id'], reply))
            chat_id = new_chat_id

        cursor.execute("""
            INSERT INTO btp_provider_usage_logs (provider_id, endpoint, tokens_used, latency_ms, status, user_id)
            VALUES (?, '/v1/chat/completions', 0, 0, 'success', ?)
        """, (provider['id'], get_current_user_id()))

        conn.commit()

        return jsonify({
            'reply': reply,
            'chat_id': chat_id,
            'provider': provider.get('provider_name')
        })

    @app.route('/ai/history')
    @require_login
    def ai_history():
        """Get chat history."""
        conn = get_btp_db()
        cursor = conn.cursor()

        chats = []
        for row in cursor.execute("""
            SELECT id, title, created_at, message_count
            FROM btp_ai_chats
            WHERE user_id = ? AND is_active = 1
            ORDER BY updated_at DESC LIMIT 50
        """, (get_current_user_id(),)).fetchall():
            chats.append(dict(row))

        return jsonify({'chats': chats})

    @app.route('/ai/chat/<int:chat_id>')
    @require_login
    def ai_get_chat(chat_id):
        """Get messages for a specific chat."""
        conn = get_btp_db()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM btp_ai_chats WHERE id = ? AND user_id = ?", (chat_id, get_current_user_id()))
        chat = cursor.fetchone()
        if not chat:
            return jsonify({'error': 'Chat not found'}), 404

        messages = []
        for row in cursor.execute("""
            SELECT * FROM btp_ai_messages WHERE chat_id = ? ORDER BY created_at ASC
        """, (chat_id,)).fetchall():
            messages.append(dict(row))

        return jsonify({'chat': dict(chat), 'messages': messages})

    # =========================================================================
    # ENVIRONMENT & CONFIG
    # =========================================================================

    @app.route('/btp/environments')
    @require_login
    @require_permission('btp', 'environment', 'view')
    def btp_environments():
        """Environment profiles."""
        conn = get_btp_db()
        cursor = conn.cursor()

        profiles = []
        for row in cursor.execute("SELECT * FROM btp_environment_profiles ORDER BY profile_name").fetchall():
            profiles.append(dict(row))

        return render_template('btp/environments/index.html', profiles=profiles)

    @app.route('/btp/feature-flags')
    @require_login
    @require_permission('btp', 'feature_flag', 'view')
    def btp_feature_flags():
        """Feature flags management."""
        conn = get_btp_db()
        cursor = conn.cursor()

        flags = []
        for row in cursor.execute("SELECT * FROM btp_feature_flags ORDER BY name").fetchall():
            flags.append(dict(row))

        return render_template('btp/feature_flags/index.html', flags=flags)

    @app.route('/btp/feature-flags/create', methods=['GET', 'POST'])
    @require_login
    @require_permission('btp', 'feature_flag', 'manage')
    def btp_feature_flag_create():
        """Create feature flag."""
        if request.method == 'POST':
            conn = get_btp_db()
            cursor = conn.cursor()

            flag_key = request.form.get('flag_key')
            name = request.form.get('name')
            description = request.form.get('description', '')
            flag_type = request.form.get('flag_type', 'boolean')
            default_value = request.form.get('default_value', 'false')

            try:
                cursor.execute("""
                    INSERT INTO btp_feature_flags (flag_key, name, description, flag_type,
                        default_value, current_value, created_by_user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (flag_key, name, description, flag_type, default_value, default_value,
                      get_current_user_id()))
                conn.commit()

                log_btp_audit('btp_feature_flag', cursor.lastrowid, 'create',
                              notes=f'Created feature flag: {flag_key}')
                flash(f'Feature flag {name} created successfully.', 'success')
                return redirect(url_for('btp_feature_flags'))
            except Exception as e:
                flash(f'Error creating feature flag: {str(e)}', 'error')

        return render_template('btp/feature_flags/create.html')

    @app.route('/btp/feature-flags/<int:flag_id>/toggle', methods=['POST'])
    @require_login
    @require_permission('btp', 'feature_flag', 'manage')
    def btp_feature_flag_toggle(flag_id):
        """Toggle feature flag."""
        conn = get_btp_db()
        cursor = conn.cursor()

        flag = cursor.execute("SELECT * FROM btp_feature_flags WHERE id = ?", (flag_id,)).fetchone()
        if not flag:
            return jsonify({'success': False, 'error': 'Flag not found'})

        new_value = 'true' if flag['current_value'] == 'false' else 'false'
        cursor.execute("UPDATE btp_feature_flags SET current_value = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                      (new_value, flag_id))
        conn.commit()

        log_btp_audit('btp_feature_flag', flag_id, 'toggle',
                      notes=f'Toggled flag to {new_value}')
        return jsonify({'success': True, 'current_value': new_value})

    @app.route('/btp/settings')
    @require_login
    @require_permission('btp', 'environment', 'view')
    def btp_settings():
        """Platform settings."""
        conn = get_btp_db()
        cursor = conn.cursor()

        settings = {}
        for row in cursor.execute("SELECT * FROM btp_platform_settings").fetchall():
            settings[row['setting_key']] = row['setting_value']

        return render_template('btp/settings/index.html', settings=settings)

    # =========================================================================
    # MONITORING
    # =========================================================================

    @app.route('/btp/monitoring/health')
    @require_login
    @require_permission('btp', 'monitoring', 'view')
    def btp_monitoring_health():
        """Service health dashboard."""
        conn = get_btp_db()
        cursor = conn.cursor()

        health_data = []

        cursor.execute("""
            SELECT 'connectors' as service, COUNT(*) as total,
                   SUM(CASE WHEN health_score >= 80 THEN 1 ELSE 0 END) as healthy
            FROM btp_connectors
        """)
        row = cursor.fetchone()
        health_data.append({'service': 'Connectors', 'total': row[1], 'healthy': row[2] or 0, 'unhealthy': row[1] - (row[2] or 0)})

        cursor.execute("SELECT COUNT(*) FROM btp_jobs WHERE status = 'failed'")
        health_data.append({'service': 'Failed Jobs', 'total': cursor.fetchone()[0], 'healthy': 0, 'unhealthy': 0})

        cursor.execute("SELECT COUNT(*) FROM btp_webhook_deliveries WHERE delivery_status = 'failed'")
        health_data.append({'service': 'Failed Webhooks', 'total': cursor.fetchone()[0], 'healthy': 0, 'unhealthy': 0})

        cursor.execute("SELECT COUNT(*) FROM btp_dead_letters WHERE status = 'failed'")
        health_data.append({'service': 'Dead Letters', 'total': cursor.fetchone()[0], 'healthy': 0, 'unhealthy': 0})

        return render_template('btp/monitoring/health.html', health_data=health_data)

    @app.route('/btp/monitoring/logs')
    @require_login
    @require_permission('btp', 'monitoring', 'view')
    def btp_monitoring_logs():
        """Platform logs."""
        conn = get_btp_db()
        cursor = conn.cursor()

        logs = []
        for row in cursor.execute("""
            SELECT * FROM btp_audit_logs ORDER BY created_at DESC LIMIT 100
        """).fetchall():
            logs.append(dict(row))

        return render_template('btp/monitoring/logs.html', logs=logs)

    @app.route('/btp/monitoring/incidents')
    @require_login
    @require_permission('btp', 'monitoring', 'view')
    def btp_monitoring_incidents():
        """Platform incidents."""
        conn = get_btp_db()
        cursor = conn.cursor()

        incidents = []
        for row in cursor.execute("""
            SELECT * FROM btp_incidents ORDER BY created_at DESC LIMIT 100
        """).fetchall():
            incidents.append(dict(row))

        return render_template('btp/monitoring/incidents.html', incidents=incidents)

    @app.route('/btp/incidents/create', methods=['POST'])
    @require_login
    @require_permission('btp', 'monitoring', 'manage')
    def btp_incident_create():
        """Create incident."""
        conn = get_btp_db()
        cursor = conn.cursor()

        title = request.form.get('title')
        description = request.form.get('description', '')
        severity = request.form.get('severity', 'medium')
        category = request.form.get('category', 'technical')

        incident_code = generate_code('INC')

        try:
            cursor.execute("""
                INSERT INTO btp_incidents (incident_code, title, description, severity, category,
                    status, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, 'open', ?)
            """, (incident_code, title, description, severity, category, get_current_user_id()))
            conn.commit()

            log_btp_audit('btp_incident', cursor.lastrowid, 'create',
                          notes=f'Created incident: {title}')
            flash(f'Incident {incident_code} created successfully.', 'success')
            return redirect(url_for('btp_monitoring_incidents'))
        except Exception as e:
            flash(f'Error creating incident: {str(e)}', 'error')
            return redirect(url_for('btp_monitoring_incidents'))

    # =========================================================================
    # REPORTS
    # =========================================================================

    @app.route('/btp/reports')
    @require_login
    @require_permission('btp', 'report', 'view')
    def btp_reports():
        """Reports dashboard."""
        return render_template('btp/reports/index.html')

    @app.route('/btp/reports/connector-analytics')
    @require_login
    @require_permission('btp', 'report', 'view')
    def btp_reports_connector_analytics():
        """Connector analytics report."""
        conn = get_btp_db()
        cursor = conn.cursor()

        analytics = []
        cursor.execute("""
            SELECT category, COUNT(*) as total,
                   SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                   AVG(health_score) as avg_health
            FROM btp_connectors GROUP BY category
        """)
        for row in cursor.fetchall():
            analytics.append({
                'category': row[0], 'total': row[1], 'active': row[2], 'avg_health': round(row[3] or 0, 1)
            })

        return render_template('btp/reports/connector_analytics.html', analytics=analytics)

    @app.route('/btp/reports/api-analytics')
    @require_login
    @require_permission('btp', 'report', 'view')
    def btp_reports_api_analytics():
        """API analytics report."""
        conn = get_btp_db()
        cursor = conn.cursor()

        apis = []
        for row in cursor.execute("""
            SELECT a.*, COUNT(c.id) as client_count
            FROM btp_api_catalog a
            LEFT JOIN btp_api_clients c ON c.api_id = a.id
            GROUP BY a.id
        """).fetchall():
            apis.append(dict(row))

        return render_template('btp/reports/api_analytics.html', apis=apis)

    @app.route('/btp/reports/export')
    @require_login
    @require_permission('btp', 'report', 'export')
    def btp_reports_export():
        """Export report data."""
        report_type = request.args.get('type', 'connectors')
        export_format = request.args.get('format', 'csv')

        conn = get_btp_db()
        cursor = conn.cursor()

        if report_type == 'connectors':
            data = []
            for row in cursor.execute("SELECT * FROM btp_connectors").fetchall():
                data.append(dict(row))
            columns = ['name', 'code', 'category', 'status', 'health_score']
        elif report_type == 'jobs':
            data = []
            for row in cursor.execute("SELECT * FROM btp_jobs").fetchall():
                data.append(dict(row))
            columns = ['job_id', 'name', 'job_type', 'status', 'created_at']
        elif report_type == 'apis':
            data = []
            for row in cursor.execute("SELECT * FROM btp_api_catalog").fetchall():
                data.append(dict(row))
            columns = ['api_name', 'api_code', 'version', 'owner_team', 'is_active']
        else:
            data = []
            columns = []

        if export_format == 'excel-text':
            return export_to_excel_text(data, columns, f'btp_{report_type}')
        elif export_format == 'excel-general':
            return export_to_excel_general(data, columns, f'btp_{report_type}')
        elif export_format == 'json':
            return jsonify(data)
        else:
            return export_to_csv(data, columns)

    # =========================================================================
    # COLLABORATION
    # =========================================================================

    @app.route('/btp/collaboration')
    @require_login
    @require_permission('btp', 'flow', 'view')
    def btp_collaboration():
        """Flow collaboration threads."""
        return render_template('btp/collaboration/index.html')

    # =========================================================================
    # ADMINISTRATION
    # =========================================================================

    @app.route('/btp/admin/permissions')
    @require_login
    @require_permission('btp', 'admin', 'access')
    def btp_admin_permissions():
        """Permission management."""
        from permissions import MODULE_PERMISSIONS
        return render_template('btp/admin/permissions.html', permissions=MODULE_PERMISSIONS.get('btp', {}))

    @app.route('/btp/admin/roles')
    @require_login
    @require_permission('btp', 'admin', 'access')
    def btp_admin_roles():
        """Role management."""
        conn = get_btp_db()
        cursor = conn.cursor()

        roles = []
        for row in cursor.execute("SELECT DISTINCT role_name FROM roles ORDER BY role_name").fetchall():
            roles.append(row[0])

        return render_template('btp/admin/roles.html', roles=roles)

    @app.route('/btp/admin/seed-data')
    @require_login
    @require_permission('btp', 'admin', 'access')
    def btp_admin_seed_data():
        """Seed/reset sample data."""
        from btp_models import seed_btp_sample_data
        seed_btp_sample_data()
        log_btp_audit('btp', 0, 'seed_data', notes='Reset BTP sample data')
        flash('Sample data seeded successfully.', 'success')
        return redirect(url_for('btp_dashboard'))

    # =========================================================================
    # FILE TEMPLATES
    # =========================================================================

    @app.route('/btp/templates')
    @require_login
    @require_permission('btp', 'mapping', 'view')
    def btp_file_templates():
        """File templates management."""
        conn = get_btp_db()
        cursor = conn.cursor()

        templates = []
        for row in cursor.execute("SELECT * FROM btp_file_templates ORDER BY name").fetchall():
            templates.append(dict(row))

        return render_template('btp/file_templates/index.html', templates=templates)

    # =========================================================================
    # SCHEDULES
    # =========================================================================

    @app.route('/btp/schedules')
    @require_login
    @require_permission('btp', 'job', 'view')
    def btp_schedules():
        """Scheduled jobs."""
        conn = get_btp_db()
        cursor = conn.cursor()

        schedules = []
        cursor.execute("""
            SELECT j.*, c.name as connector_name
            FROM btp_jobs j
            LEFT JOIN btp_connectors c ON j.connector_id = c.id
            WHERE j.schedule IS NOT NULL AND j.schedule != ''
            ORDER BY j.created_at DESC
        """)
        for row in cursor.fetchall():
            schedules.append(dict(row))

        return render_template('btp/schedules/index.html', schedules=schedules)
