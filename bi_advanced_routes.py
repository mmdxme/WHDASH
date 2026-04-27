"""
Advanced Reporting / BI Routes
=============================
Comprehensive Flask routes for the Advanced Reporting and BI module.

This module provides:
- BI Dashboard
- Custom Report Builder
- Ad-hoc Query Builder
- Report Scheduling and Delivery
- Drill-down / Drill-through Analytics
- Saved Reports and Templates
- Dataset Registry and Field Explorer
- KPI / Metric Catalog
- Export Engine
- Permission-controlled Access
- Audit Logging

Usage:
    from bi_advanced_routes import register_advanced_bi_routes
    register_advanced_bi_routes(app)
"""

from flask import Flask, Blueprint, render_template, request, jsonify, session, Response, redirect, url_for, send_file
from functools import wraps
import json
import csv
import io
import re
from datetime import datetime, timedelta
from openpyxl import Workbook
from typing import Dict, List, Optional, Any

# Import BI models
from bi_reporting_models import (
    ReportingDataset, DatasetField, ReportingKPI, SavedReport,
    ReportSchedule, DeliveryLog, AdhocQuery, QueryLog,
    ReportAccessLog, ExportLog, DrillDownConfig, PerformanceLog,
    ApprovalRequest, ReportingSettings,
    initialize_reporting_tables
)

# Import database utilities
from database import get_db_context, get_one, get_all


# =============================================================================
# AUTH AND PERMISSION HELPERS
# =============================================================================

def require_login(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def require_permission(module: str, resource: str, action: str):
    """Decorator to require specific BI permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('login'))
            
            from permissions import user_has_permission
            user_id = session.get('user_id')
            
            if not user_has_permission(user_id, module, resource, action):
                if request.is_json:
                    return jsonify({'error': 'Permission denied'}), 403
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_user_id() -> Optional[int]:
    """Get current user ID from session."""
    return session.get('user_id')


def get_user_role():
    """Get current user's role name."""
    if 'user_id' not in session:
        return None
    with get_db_context() as db:
        row = db.execute(
            "SELECT r.role_name FROM users u JOIN roles r ON u.role_id = r.id WHERE u.id = ?",
            (session['user_id'],)
        ).fetchone()
        return row['role_name'] if row else None


def is_bi_admin() -> bool:
    """Check if current user is a BI admin."""
    role = get_user_role()
    if not role:
        return False
    role_lower = role.lower()
    return 'bi admin' in role_lower or 'global admin' in role_lower or 'super admin' in role_lower


def can_build_reports() -> bool:
    """Check if current user can build custom reports."""
    if is_bi_admin():
        return True
    if 'user_id' not in session:
        return False
    from permissions import user_has_permission
    return user_has_permission(session['user_id'], 'reports', 'custom', 'create')


def can_schedule_reports() -> bool:
    """Check if current user can schedule reports."""
    if is_bi_admin():
        return True
    if 'user_id' not in session:
        return False
    from permissions import user_has_permission
    return user_has_permission(session['user_id'], 'reports', 'scheduled', 'create')


def can_export() -> bool:
    """Check if current user can export data."""
    if is_bi_admin():
        return True
    if 'user_id' not in session:
        return False
    from permissions import user_has_permission
    return user_has_permission(session['user_id'], 'reports', 'custom', 'export')


def can_run_adhoc() -> bool:
    """Check if current user can run ad-hoc queries."""
    if is_bi_admin():
        return True
    if 'user_id' not in session:
        return False
    from permissions import user_has_permission
    return user_has_permission(session['user_id'], 'reports', 'custom', 'view')


def bi_permission_required(action: str = 'view'):
    """Decorator to require BI/report permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                return redirect(url_for('login'))

            from permissions import user_has_permission
            user_id = session.get('user_id')

            if not user_has_permission(user_id, 'reports', 'custom', action):
                if request.is_json:
                    return jsonify({'error': 'Permission denied'}), 403
                return redirect(url_for('index'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator


# =============================================================================
# QUERY BUILDER HELPERS
# =============================================================================

def build_query_from_config(dataset_id: int, fields: List[str],
                           filters: Dict, group_by: List[str],
                           order_by: List[Dict], limit: int = 1000) -> tuple:
    """
    Build SQL query from report configuration.
    
    Returns: (sql_statement, params, result_columns)
    """
    dataset = ReportingDataset.get_by_id(dataset_id)
    if not dataset:
        return None, None, None
    
    dataset_fields = DatasetField.get_by_dataset(dataset_id, include_hidden=True)
    
    selected_fields = []
    result_columns = []
    params = []
    
    for field in fields:
        field_def = next((f for f in dataset_fields if f['field_code'] == field), None)
        if field_def:
            if field_def['source_expression']:
                selected_fields.append(f"{field_def['source_expression']} AS {field}")
            elif field_def['source_column']:
                selected_fields.append(f"{field_def['source_column']} AS {field}")
            else:
                selected_fields.append(field)
            result_columns.append({
                'code': field,
                'name': field_def['field_name'],
                'data_type': field_def['data_type']
            })
    
    if not selected_fields:
        selected_fields = ['*']
    
    base_table = dataset['base_table'] or 'sales_orders'
    
    sql = f"SELECT {', '.join(selected_fields)} FROM {base_table}"
    
    where_clauses = []
    
    for filter_def in filters.get('conditions', []):
        field = filter_def.get('field')
        operator = filter_def.get('operator', '=')
        value = filter_def.get('value')
        
        if field and operator and value is not None:
            field_def = next((f for f in dataset_fields if f['field_code'] == field), None)
            if field_def:
                source = field_def['source_column'] or field
                
                if operator == 'like':
                    where_clauses.append(f"{source} LIKE ?")
                    params.append(f"%{value}%")
                elif operator == 'in':
                    where_clauses.append(f"{source} IN ({','.join(['?' for _ in value])})")
                    params.extend(value)
                elif operator == 'between':
                    where_clauses.append(f"{source} BETWEEN ? AND ?")
                    params.extend(value)
                elif operator == 'is_null':
                    where_clauses.append(f"{source} IS NULL")
                elif operator == 'is_not_null':
                    where_clauses.append(f"{source} IS NOT NULL")
                else:
                    where_clauses.append(f"{source} {operator} ?")
                    params.append(value)
    
    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)
    
    if group_by:
        sql += f" GROUP BY {', '.join(group_by)}"
    
    if order_by:
        order_parts = []
        for ob in order_by:
            field = ob.get('field')
            direction = ob.get('direction', 'ASC').upper()
            if field:
                order_parts.append(f"{field} {direction}")
        if order_parts:
            sql += " ORDER BY " + ", ".join(order_parts)
    
    if limit:
        sql += f" LIMIT {min(limit, 10000)}"
    
    return sql, params, result_columns


def execute_query_with_guardrails(sql: str, params: List, 
                                 timeout_seconds: int = 60,
                                 user_id: int = None) -> Dict:
    """
    Execute a query with performance guardrails.
    
    Returns: {'success': bool, 'data': list, 'columns': list, 'row_count': int, 
              'execution_time_ms': int, 'error': str}
    """
    start_time = datetime.now()
    
    max_rows = ReportingSettings.get('bi.default_row_limit', 1000)
    slow_threshold = ReportingSettings.get('bi.slow_query_threshold_ms', 5000)
    
    try:
        with get_db_context() as db:
            db.execute(f"PRAGMA busy_timeout = {timeout_seconds * 1000}")
            
            cursor = db.execute(sql, params)
            rows = cursor.fetchmany(max_rows + 1)
            
            has_more = len(rows) > max_rows
            if has_more:
                rows = rows[:max_rows]
            
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            end_time = datetime.now()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            is_slow = execution_time_ms > slow_threshold
            
            PerformanceLog.create(
                query_fingerprint=hashlib.md5(sql.encode()).hexdigest()[:16],
                query_type='ad-hoc',
                execution_time_ms=execution_time_ms,
                rows_scanned=len(rows),
                rows_returned=len(rows),
                slow_query=is_slow,
                user_id=user_id
            )
            
            return {
                'success': True,
                'data': [dict(zip(columns, row)) for row in rows],
                'columns': columns,
                'row_count': len(rows),
                'has_more': has_more,
                'execution_time_ms': execution_time_ms,
                'is_slow': is_slow,
                'error': None
            }
    
    except Exception as e:
        end_time = datetime.now()
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return {
            'success': False,
            'data': None,
            'columns': None,
            'row_count': 0,
            'has_more': False,
            'execution_time_ms': execution_time_ms,
            'is_slow': False,
            'error': str(e)
        }


# =============================================================================
# EXPORT HELPERS
# =============================================================================

def export_to_csv(data: List[Dict], columns: List[str], filename: str) -> Response:
    """Generate CSV export response."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, extrasaction='ignore')
    writer.writeheader()
    
    for row in data:
        writer.writerow(row)
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}.csv'}
    )


def export_to_excel(data: List[Dict], columns: List[str], filename: str) -> Response:
    """Generate Excel export response."""
    wb = Workbook()
    ws = wb.active
    ws.title = filename[:31]
    
    ws.append(columns)
    
    for row in data:
        ws.append([row.get(col, '') for col in columns])
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename={filename}.xlsx'}
    )


def export_to_json(data: List[Dict], filename: str) -> Response:
    """Generate JSON export response."""
    return Response(
        json.dumps(data, indent=2, default=str),
        mimetype='application/json',
        headers={'Content-Disposition': f'attachment; filename={filename}.json'}
    )


def export_to_pdf(data: List[Dict], columns: List[str], filename: str, title: str = None) -> Response:
    """Generate PDF export response using CSV as intermediate."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
    except ImportError:
        return jsonify({'error': 'PDF export requires reportlab library'}), 500
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), 
                           leftMargin=0.5*inch, rightMargin=0.5*inch,
                           topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    if title:
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=1
        )
        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 10))
    
    header_labels = [col.replace('_', ' ').title() for col in columns]
    table_data = [header_labels]
    
    for row in data[:1000]:
        table_data.append([str(row.get(col, ''))[:50] for col in columns])
    
    col_widths = [letter[0] - inch] / len(columns) * len(columns)
    table = Table(table_data, colWidths=col_widths)
    
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563EB')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whiteness),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F3F4F6')]),
    ])
    table.setStyle(table_style)
    elements.append(table)
    
    elements.append(Spacer(1, 20))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=1
    )
    elements.append(Paragraph(
        f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Business Intelligence Module | Total rows: {len(data)}",
        footer_style
    ))
    
    doc.build(elements)
    buffer.seek(0)
    
    return Response(
        buffer.getvalue(),
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename={filename}.pdf'}
    )


# =============================================================================
# ROUTE REGISTRATION
# =============================================================================

def register_advanced_bi_routes(app: Flask):
    """
    Register all Advanced BI routes with the Flask app.
    """

    # =========================================================================
    # BI DASHBOARD
    # =========================================================================

    @app.route('/bi')
    def bi_dashboard():
        """Main BI Dashboard - overview of all reporting activities."""
        return redirect(url_for('bi_advanced_dashboard'))

    @app.route('/bi/dashboard')
    @require_login
    @bi_permission_required('view')
    def bi_advanced_dashboard():
        """Main BI Dashboard - overview of all reporting activities."""
        user_id = get_current_user_id()
        
        recent_reports = SavedReport.get_my_reports(user_id)[:5]
        shared_reports = SavedReport.get_shared_reports()[:5]
        recent_queries = AdhocQuery.get_my_queries(user_id)[:5]
        
        active_schedules = ReportSchedule.get_all()[:5]
        
        dataset_count = len(ReportingDataset.get_all())
        kpi_count = len(ReportingKPI.get_all())
        report_count = len(SavedReport.get_all())
        schedule_count = len(ReportSchedule.get_all())
        
        return render_template(
            'bi_advanced/dashboard.html',
            page_title='Advanced Reporting & BI',
            recent_reports=recent_reports,
            shared_reports=shared_reports,
            recent_queries=recent_queries,
            active_schedules=active_schedules,
            dataset_count=dataset_count,
            kpi_count=kpi_count,
            report_count=report_count,
            schedule_count=schedule_count,
            can_build=can_build_reports(),
            can_schedule=can_schedule_reports(),
            can_export=can_export()
        )

    # =========================================================================
    # DATASET REGISTRY
    # =========================================================================

    @app.route('/bi/datasets')
    @require_login
    @bi_permission_required('view')
    def bi_datasets():
        """Dataset Registry - view all available datasets."""
        datasets = ReportingDataset.get_all()
        
        return render_template(
            'bi_advanced/datasets/list.html',
            page_title='Dataset Registry',
            datasets=datasets
        )

    @app.route('/bi/datasets/<int:dataset_id>')
    @require_login
    @bi_permission_required('view')
    def bi_dataset_detail(dataset_id):
        """Dataset detail with field explorer."""
        dataset = ReportingDataset.get_by_id(dataset_id)
        if not dataset:
            return redirect(url_for('bi_datasets'))
        
        fields = DatasetField.get_by_dataset(dataset_id)
        
        grouped_fields = {}
        for field in fields:
            cat = field['field_category']
            if cat not in grouped_fields:
                grouped_fields[cat] = []
            grouped_fields[cat].append(field)
        
        return render_template(
            'bi_advanced/datasets/detail.html',
            page_title=f'Dataset: {dataset["dataset_name"]}',
            dataset=dataset,
            fields=fields,
            grouped_fields=grouped_fields
        )

    @app.route('/bi/datasets/api/fields/<int:dataset_id>')
    @require_login
    def api_dataset_fields(dataset_id):
        """API to get fields for a dataset (for report builder)."""
        fields = DatasetField.get_by_dataset(dataset_id, include_hidden=True)
        return jsonify({'fields': fields})

    # =========================================================================
    # KPI CATALOG
    # =========================================================================

    @app.route('/bi/kpis')
    @require_login
    @bi_permission_required('view')
    def bi_kpis():
        """KPI Catalog - view all defined KPIs."""
        category = request.args.get('category')
        kpis = ReportingKPI.get_all(category=category)
        categories = ReportingKPI.get_categories()
        
        return render_template(
            'bi_advanced/kpis/list.html',
            page_title='KPI Catalog',
            kpis=kpis,
            categories=categories,
            selected_category=category
        )

    @app.route('/bi/kpis/<int:kpi_id>')
    @require_login
    @bi_permission_required('view')
    def bi_kpi_detail(kpi_id):
        """KPI detail view."""
        kpi = ReportingKPI.get_by_id(kpi_id)
        if not kpi:
            return redirect(url_for('bi_kpis'))
        
        return render_template(
            'bi_advanced/kpis/detail.html',
            page_title=f'KPI: {kpi["kpi_name"]}',
            kpi=kpi
        )

    @app.route('/bi/kpis/api/list')
    @require_login
    def api_kpis():
        """API to get KPIs as JSON."""
        category = request.args.get('category')
        kpis = ReportingKPI.get_all(category=category)
        return jsonify({'kpis': kpis})

    # =========================================================================
    # REPORT BUILDER
    # =========================================================================

    @app.route('/bi/reports/builder')
    @require_login
    @bi_permission_required('create')
    def bi_report_builder():
        """Custom Report Builder - main interface."""
        if not can_build_reports():
            return redirect(url_for('bi_advanced_dashboard'))
        
        datasets = ReportingDataset.get_all()
        kpis = ReportingKPI.get_all()
        
        return render_template(
            'bi_advanced/reports/builder.html',
            page_title='Report Builder',
            datasets=datasets,
            kpis=kpis
        )

    @app.route('/bi/reports/builder/<int:report_id>')
    @require_login
    @bi_permission_required('edit')
    def bi_edit_report(report_id):
        """Edit an existing report."""
        if not can_build_reports():
            return redirect(url_for('bi_advanced_dashboard'))
        
        report = SavedReport.get_by_id(report_id)
        if not report:
            return redirect(url_for('bi_report_builder'))
        
        datasets = ReportingDataset.get_all()
        kpis = ReportingKPI.get_all()
        
        return render_template(
            'bi_advanced/reports/builder.html',
            page_title=f'Edit Report: {report["report_name"]}',
            datasets=datasets,
            kpis=kpis,
            editing_report=report
        )

    @app.route('/bi/reports/api/preview', methods=['POST'])
    @require_login
    def api_preview_report():
        """Preview a report before saving."""
        if not can_build_reports():
            return jsonify({'error': 'Permission denied'}), 403
        
        data = request.get_json()
        
        dataset_id = data.get('dataset_id')
        fields = data.get('fields', [])
        filters = data.get('filters', {})
        group_by = data.get('group_by', [])
        order_by = data.get('order_by', [])
        limit = data.get('limit', 1000)
        
        if not dataset_id:
            return jsonify({'error': 'Dataset is required'}), 400
        
        sql, params, columns = build_query_from_config(
            dataset_id, fields, filters, group_by, order_by, limit
        )
        
        if not sql:
            return jsonify({'error': 'Could not build query'}), 400
        
        result = execute_query_with_guardrails(
            sql, params,
            timeout_seconds=60,
            user_id=get_current_user_id()
        )
        
        return jsonify({
            'sql': sql,
            'columns': columns,
            'data': result['data'][:100],
            'row_count': result['row_count'],
            'has_more': result['has_more'],
            'execution_time_ms': result['execution_time_ms'],
            'is_slow': result['is_slow'],
            'error': result['error']
        })

    @app.route('/bi/reports/api/save', methods=['POST'])
    @require_login
    def api_save_report():
        """Save a report configuration."""
        if not can_build_reports():
            return jsonify({'error': 'Permission denied'}), 403
        
        data = request.get_json()
        
        report_name = data.get('report_name')
        if not report_name:
            return jsonify({'error': 'Report name is required'}), 400
        
        dataset_id = data.get('dataset_id')
        report_type = data.get('report_type', 'tabular')
        description = data.get('description')
        selected_fields = data.get('fields', [])
        selected_kpis = data.get('kpis', [])
        filters_config = data.get('filters', {})
        grouping_config = data.get('group_by', [])
        sorting_config = data.get('order_by', [])
        layout_config = data.get('layout', {})
        chart_type = data.get('chart_type')
        visualization_type = data.get('visualization_type')
        is_shared = data.get('is_shared', False)
        
        user_id = get_current_user_id()
        
        report_id = SavedReport.create(
            report_name=report_name,
            dataset_id=dataset_id,
            report_type=report_type,
            description=description,
            selected_fields=selected_fields,
            selected_kpis=selected_kpis,
            filters_config=filters_config,
            grouping_config=grouping_config,
            sorting_config=sorting_config,
            layout_config=layout_config,
            chart_type=chart_type,
            visualization_type=visualization_type,
            status='active',
            is_shared=is_shared,
            created_by_user_id=user_id
        )
        
        ReportAccessLog.create(
            report_id=report_id,
            report_name=report_name,
            accessed_by_user_id=user_id,
            access_type='create',
            ip_address=request.remote_addr
        )
        
        return jsonify({'success': True, 'report_id': report_id})

    @app.route('/bi/reports/api/update/<int:report_id>', methods=['POST'])
    @require_login
    def api_update_report(report_id):
        """Update a saved report."""
        if not can_build_reports():
            return jsonify({'error': 'Permission denied'}), 403
        
        report = SavedReport.get_by_id(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        user_id = get_current_user_id()
        
        if report['created_by_user_id'] != user_id and not is_bi_admin():
            return jsonify({'error': 'Not authorized to edit this report'}), 403
        
        data = request.get_json()
        
        SavedReport.update(
            report_id,
            report_name=data.get('report_name'),
            description=data.get('description'),
            selected_fields=data.get('fields'),
            selected_kpis=data.get('kpis'),
            filters_config=data.get('filters'),
            grouping_config=data.get('group_by'),
            sorting_config=data.get('order_by'),
            layout_config=data.get('layout'),
            chart_type=data.get('chart_type'),
            visualization_type=data.get('visualization_type'),
            is_shared=data.get('is_shared'),
            updated_by_user_id=user_id
        )
        
        return jsonify({'success': True})

    @app.route('/bi/reports/api/delete/<int:report_id>', methods=['POST'])
    @require_login
    @bi_permission_required('delete')
    def api_delete_report(report_id):
        """Delete a saved report."""
        if not can_build_reports():
            return jsonify({'error': 'Permission denied'}), 403
        
        report = SavedReport.get_by_id(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        user_id = get_current_user_id()
        
        if report['created_by_user_id'] != user_id and not is_bi_admin():
            return jsonify({'error': 'Not authorized to delete this report'}), 403
        
        SavedReport.delete(report_id)
        
        return jsonify({'success': True})

    @app.route('/bi/reports/api/duplicate/<int:report_id>', methods=['POST'])
    @require_login
    @bi_permission_required('create')
    def api_duplicate_report(report_id):
        """Duplicate a report."""
        if not can_build_reports():
            return jsonify({'error': 'Permission denied'}), 403
        
        new_name = request.get_json().get('new_name') if request.get_json() else None
        new_id = SavedReport.duplicate(report_id, new_name, get_current_user_id())
        
        if new_id:
            return jsonify({'success': True, 'report_id': new_id})
        else:
            return jsonify({'error': 'Could not duplicate report'}), 400

    # =========================================================================
    # SAVED REPORTS LIST
    # =========================================================================

    @app.route('/bi/reports')
    @require_login
    @bi_permission_required('view')
    def bi_reports():
        """Saved Reports list."""
        view = request.args.get('view', 'my')
        user_id = get_current_user_id()
        
        if view == 'shared':
            reports = SavedReport.get_shared_reports()
        elif view == 'templates':
            reports = SavedReport.get_templates()
        else:
            reports = SavedReport.get_my_reports(user_id)
        
        return render_template(
            'bi_advanced/reports/list.html',
            page_title='Saved Reports',
            reports=reports,
            current_view=view
        )

    @app.route('/bi/reports/<int:report_id>')
    @require_login
    @bi_permission_required('view')
    def bi_view_report(report_id):
        """View and execute a saved report."""
        report = SavedReport.get_by_id(report_id)
        if not report:
            return redirect(url_for('bi_reports'))
        
        user_id = get_current_user_id()
        
        ReportAccessLog.create(
            report_id=report_id,
            report_name=report['report_name'],
            report_code=report['report_code'],
            accessed_by_user_id=user_id,
            access_type='view',
            ip_address=request.remote_addr
        )
        
        SavedReport.record_run(report_id)
        
        dataset = None
        fields = []
        if report.get('dataset_id'):
            dataset = ReportingDataset.get_by_id(report['dataset_id'])
            fields = DatasetField.get_by_dataset(report['dataset_id'])
        
        return render_template(
            'bi_advanced/reports/view.html',
            page_title=report['report_name'],
            report=report,
            dataset=dataset,
            fields=fields,
            can_export=can_export()
        )

    @app.route('/bi/reports/api/execute/<int:report_id>')
    @require_login
    def api_execute_report(report_id):
        """Execute a saved report and return data."""
        report = SavedReport.get_by_id(report_id)
        if not report:
            return jsonify({'error': 'Report not found'}), 404
        
        user_id = get_current_user_id()
        
        dataset_id = report.get('dataset_id')
        if not dataset_id:
            return jsonify({'error': 'Report has no dataset configured'}), 400
        
        fields = report.get('selected_fields', [])
        filters = report.get('filters_config', {})
        group_by = report.get('grouping_config', [])
        order_by = report.get('sorting_config', [])
        limit = report.get('row_limit', 1000)
        
        sql, params, columns = build_query_from_config(
            dataset_id, fields, filters, group_by, order_by, limit
        )
        
        if not sql:
            return jsonify({'error': 'Could not build query'}), 400
        
        result = execute_query_with_guardrails(
            sql, params,
            timeout_seconds=report.get('timeout_seconds', 300),
            user_id=user_id
        )
        
        ReportAccessLog.create(
            report_id=report_id,
            report_name=report['report_name'],
            report_code=report['report_code'],
            accessed_by_user_id=user_id,
            access_type='execute',
            execution_time_ms=result['execution_time_ms'],
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'report': {
                'id': report['id'],
                'name': report['report_name'],
                'code': report['report_code']
            },
            'columns': columns,
            'data': result['data'],
            'row_count': result['row_count'],
            'has_more': result['has_more'],
            'execution_time_ms': result['execution_time_ms'],
            'is_slow': result['is_slow'],
            'error': result['error']
        })

    # =========================================================================
    # AD-HOC QUERY BUILDER
    # =========================================================================

    @app.route('/bi/adhoc')
    @require_login
    @bi_permission_required('execute')
    def bi_adhoc_query():
        """Ad-hoc Query Builder interface."""
        if not can_run_adhoc():
            return redirect(url_for('bi_advanced_dashboard'))
        
        datasets = ReportingDataset.get_all()
        
        return render_template(
            'bi_advanced/adhoc/query_builder.html',
            page_title='Ad-hoc Query Builder',
            datasets=datasets
        )

    @app.route('/bi/adhoc/queries')
    @require_login
    @bi_permission_required('view')
    def bi_adhoc_queries():
        """Saved Ad-hoc Queries list."""
        user_id = get_current_user_id()
        view = request.args.get('view', 'my')
        
        if view == 'shared':
            queries = AdhocQuery.get_shared_queries()
        else:
            queries = AdhocQuery.get_my_queries(user_id)
        
        return render_template(
            'bi_advanced/adhoc/queries_list.html',
            page_title='Ad-hoc Queries',
            queries=queries,
            current_view=view
        )

    @app.route('/bi/adhoc/api/execute', methods=['POST'])
    @require_login
    def api_execute_adhoc():
        """Execute an ad-hoc query."""
        if not can_run_adhoc():
            return jsonify({'error': 'Permission denied'}), 403
        
        data = request.get_json()
        
        sql = data.get('sql')
        if not sql:
            return jsonify({'error': 'SQL statement is required'}), 400
        
        forbidden_patterns = [
            r'\bDROP\b', r'\bDELETE\b', r'\bTRUNCATE\b',
            r'\bALTER\b', r'\bCREATE\b', r'\bINSERT\b',
            r'\bUPDATE\b', r'\bGRANT\b', r'\bREVOKE\b'
        ]
        
        sql_upper = sql.upper()
        for pattern in forbidden_patterns:
            if re.search(pattern, sql_upper):
                return jsonify({'error': 'Query contains forbidden operations'}), 400
        
        max_rows = ReportingSettings.get('bi.default_row_limit', 1000)
        timeout = ReportingSettings.get('bi.default_timeout_seconds', 300)
        
        user_id = get_current_user_id()
        
        result = execute_query_with_guardrails(sql, [], timeout, user_id)
        
        QueryLog.create(
            query_name=data.get('name', 'Ad-hoc Query'),
            executed_by_user_id=user_id,
            sql_statement=sql,
            result_row_count=result['row_count'],
            execution_time_ms=result['execution_time_ms'],
            status='completed' if result['success'] else 'failed',
            error_message=result['error'],
            client_ip=request.remote_addr
        )
        
        return jsonify({
            'columns': result['columns'],
            'data': result['data'],
            'row_count': result['row_count'],
            'has_more': result['has_more'],
            'execution_time_ms': result['execution_time_ms'],
            'is_slow': result['is_slow'],
            'error': result['error']
        })

    @app.route('/bi/adhoc/api/save', methods=['POST'])
    @require_login
    def api_save_adhoc_query():
        """Save an ad-hoc query configuration."""
        if not can_run_adhoc():
            return jsonify({'error': 'Permission denied'}), 403
        
        data = request.get_json()
        
        query_name = data.get('query_name')
        if not query_name:
            return jsonify({'error': 'Query name is required'}), 400
        
        query_id = AdhocQuery.create(
            query_name=query_name,
            description=data.get('description'),
            dataset_id=data.get('dataset_id'),
            sql_statement=data.get('sql'),
            is_shared=data.get('is_shared', False),
            created_by_user_id=get_current_user_id()
        )
        
        return jsonify({'success': True, 'query_id': query_id})

    # =========================================================================
    # REPORT SCHEDULING
    # =========================================================================

    @app.route('/bi/schedules')
    @require_login
    @bi_permission_required('view')
    def bi_schedules():
        """Report Schedules list."""
        if not can_schedule_reports():
            return redirect(url_for('bi_advanced_dashboard'))
        
        schedules = ReportSchedule.get_all()
        
        return render_template(
            'bi_advanced/scheduling/list.html',
            page_title='Report Schedules',
            schedules=schedules
        )

    @app.route('/bi/schedules/create')
    @require_login
    @bi_permission_required('create')
    def bi_create_schedule():
        """Create new schedule form."""
        if not can_schedule_reports():
            return redirect(url_for('bi_advanced_dashboard'))
        
        reports = SavedReport.get_all(status='active')
        
        return render_template(
            'bi_advanced/scheduling/create.html',
            page_title='Create Schedule',
            reports=reports
        )

    @app.route('/bi/schedules/<int:schedule_id>')
    @require_login
    def bi_view_schedule(schedule_id):
        """View schedule detail."""
        schedule = ReportSchedule.get_by_id(schedule_id)
        if not schedule:
            return redirect(url_for('bi_schedules'))
        
        delivery_logs = DeliveryLog.get_by_schedule(schedule_id)
        
        return render_template(
            'bi_advanced/scheduling/detail.html',
            page_title=f'Schedule: {schedule["schedule_name"]}',
            schedule=schedule,
            delivery_logs=delivery_logs
        )

    @app.route('/bi/schedules/api/create', methods=['POST'])
    @require_login
    def api_create_schedule():
        """Create a new report schedule."""
        if not can_schedule_reports():
            return jsonify({'error': 'Permission denied'}), 403
        
        data = request.get_json()
        
        schedule_name = data.get('schedule_name')
        report_id = data.get('report_id')
        
        if not schedule_name or not report_id:
            return jsonify({'error': 'Name and report are required'}), 400
        
        schedule_id = ReportSchedule.create(
            schedule_name=schedule_name,
            report_id=report_id,
            frequency=data.get('frequency', 'monthly'),
            run_time=data.get('run_time', '09:00'),
            day_of_week=data.get('day_of_week'),
            day_of_month=data.get('day_of_month'),
            output_formats=data.get('output_formats', ['excel']),
            delivery_method=data.get('delivery_method', 'email'),
            recipient_emails=data.get('recipient_emails'),
            recipient_user_ids=data.get('recipient_user_ids'),
            email_subject=data.get('email_subject'),
            created_by_user_id=get_current_user_id()
        )
        
        return jsonify({'success': True, 'schedule_id': schedule_id})

    @app.route('/bi/schedules/api/toggle/<int:schedule_id>', methods=['POST'])
    @require_login
    def api_toggle_schedule(schedule_id):
        """Toggle schedule active status."""
        if not can_schedule_reports():
            return jsonify({'error': 'Permission denied'}), 403
        
        schedule = ReportSchedule.get_by_id(schedule_id)
        if not schedule:
            return jsonify({'error': 'Schedule not found'}), 404
        
        new_status = 'paused' if schedule['is_active'] else 'active'
        ReportSchedule.update(schedule_id, is_active=(new_status == 'active'))
        
        return jsonify({'success': True, 'new_status': new_status})

    @app.route('/bi/schedules/api/delete/<int:schedule_id>', methods=['POST'])
    @require_login
    def api_delete_schedule(schedule_id):
        """Delete a schedule."""
        if not can_schedule_reports():
            return jsonify({'error': 'Permission denied'}), 403
        
        ReportSchedule.delete(schedule_id)
        return jsonify({'success': True})

    @app.route('/bi/delivery/failed')
    @require_login
    def bi_failed_deliveries():
        """View failed deliveries."""
        if not can_schedule_reports():
            return redirect(url_for('bi_advanced_dashboard'))
        
        failed = DeliveryLog.get_failed()
        
        return render_template(
            'bi_advanced/scheduling/failed_deliveries.html',
            page_title='Failed Deliveries',
            deliveries=failed
        )

    # =========================================================================
    # DRILL-DOWN ANALYTICS
    # =========================================================================

    @app.route('/bi/drilldown/<domain>')
    @require_login
    @bi_permission_required('execute')
    def bi_drilldown(domain):
        """Drill-down analytics by domain."""
        valid_domains = ['sales', 'inventory', 'procurement', 'finance', 
                        'customers', 'warehouse', 'branch']
        
        if domain not in valid_domains:
            return redirect(url_for('bi_advanced_dashboard'))
        
        user_id = get_current_user_id()
        company_id = request.args.get('company_id', type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        if not date_from:
            date_from = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        if not date_to:
            date_to = datetime.now().strftime('%Y-%m-%d')
        
        if domain == 'sales':
            return render_template(
                'bi_advanced/drilldown/sales.html',
                page_title='Sales Drill-down',
                date_from=date_from,
                date_to=date_to,
                company_id=company_id
            )
        elif domain == 'inventory':
            return render_template(
                'bi_advanced/drilldown/inventory.html',
                page_title='Inventory Drill-down',
                company_id=company_id
            )
        elif domain == 'customers':
            return render_template(
                'bi_advanced/drilldown/customers.html',
                page_title='Customer Drill-down',
                date_from=date_from,
                date_to=date_to
            )
        
        return render_template(
            'bi_advanced/drilldown/base.html',
            page_title=f'{domain.title()} Drill-down',
            domain=domain,
            date_from=date_from,
            date_to=date_to,
            company_id=company_id
        )

    @app.route('/bi/api/drilldown/sales/by-company')
    @require_login
    def api_drilldown_sales_by_company_advanced():
        """Get sales breakdown by company."""
        from bi_models import drill_down_sales_by_company
        
        date_from = request.args.get('date_from', datetime.now().replace(day=1).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
        company_id = request.args.get('company_id', type=int)
        
        data = drill_down_sales_by_company(date_from, date_to, company_id)
        
        return jsonify({
            'date_range': {'from': date_from, 'to': date_to},
            'data': data
        })

    @app.route('/bi/api/drilldown/sales/by-item')
    @require_login
    def api_drilldown_sales_by_item_advanced():
        """Get sales breakdown by item."""
        from bi_models import drill_down_sales_by_item
        
        date_from = request.args.get('date_from', datetime.now().replace(day=1).strftime('%Y-%m-%d'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
        company_id = request.args.get('company_id', type=int)
        limit = request.args.get('limit', 50, type=int)
        
        data = drill_down_sales_by_item(date_from, date_to, company_id, limit)
        
        return jsonify({
            'date_range': {'from': date_from, 'to': date_to},
            'data': data
        })

    @app.route('/bi/api/drilldown/inventory/by-warehouse')
    @require_login
    def api_drilldown_inventory_by_warehouse_advanced():
        """Get inventory breakdown by warehouse."""
        from bi_models import drill_down_inventory_by_warehouse
        
        company_id = request.args.get('company_id', type=int)
        
        data = drill_down_inventory_by_warehouse(company_id)
        
        return jsonify({'data': data})

    # =========================================================================
    # EXPORT ENGINE
    # =========================================================================

    @app.route('/bi/export/<int:report_id>')
    @require_login
    def bi_export_report(report_id):
        """Export a report."""
        if not can_export():
            return redirect(url_for('bi_view_report', report_id=report_id))
        
        export_format = request.args.get('format', 'excel')
        
        report = SavedReport.get_by_id(report_id)
        if not report:
            return redirect(url_for('bi_reports'))
        
        dataset_id = report.get('dataset_id')
        if not dataset_id:
            return redirect(url_for('bi_view_report', report_id=report_id))
        
        fields = report.get('selected_fields', [])
        filters = report.get('filters_config', {})
        group_by = report.get('grouping_config', [])
        order_by = report.get('sorting_config', [])
        limit = ReportingSettings.get('bi.max_export_rows', 50000)
        
        sql, params, columns = build_query_from_config(
            dataset_id, fields, filters, group_by, order_by, limit
        )
        
        if not sql:
            return redirect(url_for('bi_view_report', report_id=report_id))
        
        result = execute_query_with_guardrails(sql, params, 300, get_current_user_id())
        
        if not result['success']:
            return redirect(url_for('bi_view_report', report_id=report_id))
        
        filename = f"{report['report_name'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}"
        
        user_id = get_current_user_id()
        
        ExportLog.create(
            report_id=report_id,
            report_name=report['report_name'],
            report_code=report['report_code'],
            exported_by_user_id=user_id,
            export_format=export_format,
            row_count=result['row_count'],
            status='completed',
            execution_time_ms=result['execution_time_ms'],
            ip_address=request.remote_addr
        )
        
        ReportAccessLog.create(
            report_id=report_id,
            report_name=report['report_name'],
            report_code=report['report_code'],
            accessed_by_user_id=user_id,
            access_type='export',
            export_format=export_format,
            ip_address=request.remote_addr
        )
        
        if export_format == 'csv':
            return export_to_csv(result['data'], columns, filename)
        elif export_format == 'json':
            return export_to_json(result['data'], filename)
        else:
            return export_to_excel(result['data'], columns, filename)

    @app.route('/bi/api/export', methods=['POST'])
    @require_login
    def api_export_data():
        """Export data from ad-hoc query or report builder."""
        if not can_export():
            return jsonify({'error': 'Permission denied'}), 403
        
        data = request.get_json()
        
        export_format = data.get('format', 'excel')
        report_name = data.get('report_name', 'Export')
        columns = data.get('columns', [])
        export_data = data.get('data', [])
        
        filename = f"{report_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}"
        
        user_id = get_current_user_id()
        
        ExportLog.create(
            exported_by_user_id=user_id,
            export_format=export_format,
            file_name=f"{filename}.{export_format}",
            row_count=len(export_data),
            status='completed',
            ip_address=request.remote_addr
        )
        
        if export_format == 'csv':
            return export_to_csv(export_data, columns, filename)
        elif export_format == 'json':
            return export_to_json(export_data, filename)
        else:
            return export_to_excel(export_data, columns, filename)

    # =========================================================================
    # MONITORING & LOGS
    # =========================================================================

    @app.route('/bi/logs/access')
    @require_login
    @bi_permission_required('view')
    def bi_access_logs():
        """Report access logs."""
        if not is_bi_admin():
            return redirect(url_for('bi_advanced_dashboard'))
        
        user_id = request.args.get('user_id', type=int)
        logs = ReportAccessLog.get_recent_access(user_id=user_id)
        
        return render_template(
            'bi_advanced/monitoring/access_logs.html',
            page_title='Report Access Logs',
            logs=logs
        )

    @app.route('/bi/logs/query')
    @require_login
    def bi_query_logs():
        """Ad-hoc query logs."""
        if not is_bi_admin():
            return redirect(url_for('bi_advanced_dashboard'))
        
        user_id = request.args.get('user_id', type=int)
        if user_id:
            logs = QueryLog.get_by_user(user_id)
        else:
            logs = QueryLog.get_slow_queries(threshold_ms=0)
        
        return render_template(
            'bi_advanced/monitoring/query_logs.html',
            page_title='Query Logs',
            logs=logs
        )

    @app.route('/bi/logs/performance')
    @require_login
    def bi_performance_logs():
        """Performance logs."""
        if not is_bi_admin():
            return redirect(url_for('bi_advanced_dashboard'))
        
        threshold = request.args.get('threshold', 5000, type=int)
        logs = PerformanceLog.get_slow_queries(threshold_ms=threshold)
        
        return render_template(
            'bi_advanced/monitoring/performance_logs.html',
            page_title='Performance Logs',
            logs=logs,
            threshold=threshold
        )

    @app.route('/bi/logs/export')
    @require_login
    def bi_export_logs():
        """Export logs."""
        if not is_bi_admin():
            return redirect(url_for('bi_advanced_dashboard'))
        
        logs = ExportLog.get_recent_exports()
        
        return render_template(
            'bi_advanced/monitoring/export_logs.html',
            page_title='Export Logs',
            logs=logs
        )

    @app.route('/bi/logs/delivery')
    @require_login
    def bi_delivery_logs():
        """Delivery logs."""
        if not is_bi_admin():
            return redirect(url_for('bi_advanced_dashboard'))
        
        failed = DeliveryLog.get_failed()
        
        return render_template(
            'bi_advanced/monitoring/delivery_logs.html',
            page_title='Delivery Logs',
            deliveries=failed
        )

    # =========================================================================
    # SETTINGS
    # =========================================================================

    @app.route('/bi/settings')
    @require_login
    @bi_permission_required('view')
    def bi_settings():
        """BI Settings page."""
        if not is_bi_admin():
            return redirect(url_for('bi_advanced_dashboard'))
        
        return render_template(
            'bi_advanced/settings/index.html',
            page_title='BI Settings'
        )

    @app.route('/bi/settings/api/get')
    @require_login
    def api_get_settings():
        """Get BI settings as JSON."""
        if not is_bi_admin():
            return jsonify({'error': 'Permission denied'}), 403
        
        settings = ReportingSettings.get_all_by_category('bi')
        return jsonify({'settings': settings})

    @app.route('/bi/settings/api/save', methods=['POST'])
    @require_login
    def api_save_settings():
        """Save BI settings."""
        if not is_bi_admin():
            return jsonify({'error': 'Permission denied'}), 403
        
        data = request.get_json()
        
        for key, value in data.items():
            ReportingSettings.set(key, value)
        
        return jsonify({'success': True})

    # =========================================================================
    # KPI CATALOG MANAGEMENT
    # =========================================================================

    @app.route('/bi/kpis/manage')
    @require_login
    @bi_permission_required('create')
    def bi_manage_kpis():
        """Manage KPIs (admin only)."""
        if not is_bi_admin():
            return redirect(url_for('bi_kpis'))
        
        kpis = ReportingKPI.get_all(include_inactive=True)
        categories = ReportingKPI.get_categories()
        
        return render_template(
            'bi_advanced/kpis/manage.html',
            page_title='Manage KPIs',
            kpis=kpis,
            categories=categories
        )

    @app.route('/bi/kpis/api/create', methods=['POST'])
    @require_login
    def api_create_kpi():
        """Create a new KPI."""
        if not is_bi_admin():
            return jsonify({'error': 'Permission denied'}), 403
        
        data = request.get_json()
        
        kpi_code = data.get('kpi_code')
        kpi_name = data.get('kpi_name')
        category = data.get('category')
        
        if not kpi_code or not kpi_name or not category:
            return jsonify({'error': 'Code, name, and category are required'}), 400
        
        kpi_id = ReportingKPI.create(
            kpi_code=kpi_code,
            kpi_name=kpi_name,
            category=category,
            description=data.get('description'),
            business_definition=data.get('business_definition'),
            formula_description=data.get('formula_description'),
            dataset_code=data.get('dataset_code'),
            source_query=data.get('source_query'),
            aggregation_type=data.get('aggregation_type'),
            unit_of_measure=data.get('unit_of_measure', 'number'),
            display_format=data.get('display_format'),
            decimal_places=data.get('decimal_places', 0),
            target_direction=data.get('target_direction', 'higher_is_better'),
            warning_threshold=data.get('warning_threshold'),
            critical_threshold=data.get('critical_threshold'),
            owner_role=data.get('owner_role'),
            tags=data.get('tags', []),
            created_by_user_id=get_current_user_id()
        )
        
        return jsonify({'success': True, 'kpi_id': kpi_id})

    @app.route('/bi/kpis/api/toggle/<int:kpi_id>', methods=['POST'])
    @require_login
    def api_toggle_kpi(kpi_id):
        """Toggle KPI active status."""
        if not is_bi_admin():
            return jsonify({'error': 'Permission denied'}), 403
        
        kpi = ReportingKPI.get_by_id(kpi_id)
        if not kpi:
            return jsonify({'error': 'KPI not found'}), 404
        
        ReportingKPI.update(kpi_id, is_active=not kpi['is_active'])
        
        return jsonify({'success': True, 'new_status': not kpi['is_active']})

    # =========================================================================
    # APPROVALS
    # =========================================================================

    @app.route('/bi/approvals')
    @require_login
    def bi_approvals():
        """Pending approvals."""
        if not is_bi_admin():
            return redirect(url_for('bi_advanced_dashboard'))
        
        pending = ApprovalRequest.get_pending()
        
        return render_template(
            'bi_advanced/approvals/list.html',
            page_title='Pending Approvals',
            approvals=pending
        )

    @app.route('/bi/approvals/api/approve/<int:request_id>', methods=['POST'])
    @require_login
    def api_approve_request(request_id):
        """Approve an approval request."""
        if not is_bi_admin():
            return jsonify({'error': 'Permission denied'}), 403
        
        remarks = request.get_json().get('remarks') if request.get_json() else None
        
        ApprovalRequest.approve(request_id, get_current_user_id(), remarks)
        
        return jsonify({'success': True})

    @app.route('/bi/approvals/api/reject/<int:request_id>', methods=['POST'])
    @require_login
    def api_reject_request(request_id):
        """Reject an approval request."""
        if not is_bi_admin():
            return jsonify({'error': 'Permission denied'}), 403
        
        remarks = request.get_json().get('remarks') if request.get_json() else None
        
        ApprovalRequest.reject(request_id, get_current_user_id(), remarks)
        
        return jsonify({'success': True})

    # =========================================================================
    # API: EXECUTIVE DASHBOARD DATA
    # =========================================================================

    @app.route('/bi/api/executive-summary')
    @require_login
    def api_executive_summary():
        """Get executive dashboard summary data for BI dashboards."""
        from bi_models import get_executive_dashboard_data
        
        company_id = request.args.get('company_id', type=int)
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        
        if not date_from:
            date_from = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        if not date_to:
            date_to = datetime.now().strftime('%Y-%m-%d')
        
        data = get_executive_dashboard_data(
            user_id=get_current_user_id(),
            company_id=company_id,
            date_from=date_from,
            date_to=date_to
        )
        
        return jsonify(data)

    # =========================================================================
    # CATCH-ALL FOR MISSING ROUTES
    # =========================================================================

    @app.route('/bi/<path:subpath>')
    @require_login
    def bi_catchall_advanced(subpath):
        """Catch-all route for BI pages (advanced module)."""
        return render_template(
            'bi_advanced/base.html',
            page_title=f'BI: {subpath}',
            error=f'Page not found: {subpath}'
        )


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == '__main__':
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret'
    
    with app.app_context():
        initialize_reporting_tables()
    
    register_advanced_bi_routes(app)
    
    print("Advanced BI Routes registered. Available endpoints:")
    print("  /bi/dashboard - Main BI Dashboard")
    print("  /bi/datasets - Dataset Registry")
    print("  /bi/kpis - KPI Catalog")
    print("  /bi/reports - Saved Reports")
    print("  /bi/reports/builder - Report Builder")
    print("  /bi/adhoc - Ad-hoc Query Builder")
    print("  /bi/schedules - Report Schedules")
    print("  /bi/drilldown/<domain> - Drill-down Analytics")
    print("  /bi/logs/* - Monitoring Logs")
    print("  /bi/settings - BI Settings")
