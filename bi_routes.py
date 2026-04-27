"""Business Intelligence Routes - Management Dashboard Endpoints
====================================================
Flask routes for all executive dashboard and management reporting endpoints.

This module provides:
- Executive dashboard routes
- Holding/group dashboard routes
- Company performance comparison routes
- Operational module dashboards (sales, inventory, logistics, procurement, HR, marketing, finance)
- Alert and exception routes
- Consolidated and comparative report routes
- Drill-down API endpoints
- Export functionality (20 export types)

All routes require authentication and respect permission controls.

Usage:
    from bi_routes import register_bi_routes
    register_bi_routes(app)
"""

from flask import Flask, Blueprint, render_template, request, jsonify, session, Response
from functools import wraps
import json
import csv
import io
from datetime import datetime
from openpyxl import Workbook

# Import export utilities
from export_utils import (
    send_export_response,
    export_to_csv,
    export_to_excel_text,
    export_to_excel_general,
    export_to_json,
    export_to_xml,
    export_to_txt,
    export_to_pdf,
    export_to_docx,
    export_to_html,
    export_to_printable_html,
    export_to_barcode_labels,
    export_to_api_json,
    export_to_email_html,
    export_to_zip,
    export_to_backup,
    export_to_sql_dump,
    export_dashboard_state,
    export_summary_report,
    export_detailed_report,
    export_audit_log,
    get_export_columns
)

# Import BI models
from bi_models import (
    get_executive_dashboard_data,
    get_sales_kpis,
    get_inventory_kpis,
    get_logistics_kpis,
    get_procurement_kpis,
    get_hr_kpis,
    get_marketing_kpis,
    get_financial_kpis,
    get_alerts_and_exceptions,
    get_consolidated_holding_view,
    get_company_comparison,
    get_customer_metrics,
    get_inquiry_to_order_funnel,
    get_inventory_turnover,
    get_date_range,
    get_all_companies_for_bi,
    get_all_warehouses_for_bi,
    drill_down_sales_by_company,
    drill_down_sales_by_item,
    drill_down_inventory_by_warehouse
)

# Import database utilities
from database import get_db_context, get_one, get_all


# =============================================================================
# BLUEPRINT AND AUTH HELPERS
# =============================================================================

def require_login(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            return {'error': 'Authentication required'}, 401
        return f(*args, **kwargs)
    return decorated_function


def require_permission(permission_string):
    """Decorator to require specific permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                return {'error': 'Authentication required'}, 401
            
            # For now, check if user has reports.executive permission
            from permissions import user_has_permission
            user_id = session.get('user_id')
            
            # Extract module and action from permission string
            parts = permission_string.split('.')
            if len(parts) >= 2:
                module = parts[0]
                action = parts[-1]
            else:
                module = 'reports'
                action = permission_string
            
            if not user_has_permission(user_id, 'reports', 'executive', action):
                if request.is_json:
                    return jsonify({'error': 'Permission denied'}), 403
                return {'error': 'Permission denied'}, 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_user_company_access():
    """Get the companies accessible to the current user."""
    if 'user_id' not in session:
        return None
    
    user_id = session['user_id']
    with get_db_context() as db:
        access = db.execute("""
            SELECT company_id FROM user_company_access
            WHERE user_id = ?
        """, (user_id,)).fetchall()
        
        if not access:
            return None
        
        return [r['company_id'] for r in access]


def get_user_default_company():
    """Get the user's default company."""
    if 'user_id' not in session:
        return None
    
    user_id = session['user_id']
    with get_db_context() as db:
        # Just get the first accessible company as default
        access = db.execute("""
            SELECT company_id FROM user_company_access
            WHERE user_id = ?
            LIMIT 1
        """, (user_id,)).fetchone()
        
        return access['company_id'] if access else None


def parse_date_params():
    """Parse date range parameters from request."""
    period = request.args.get('period', 'this_month')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    if not date_from or not date_to:
        date_from, date_to = get_date_range(period)
    
    return date_from, date_to


def parse_company_filter():
    """Parse company filter from request."""
    company_id = request.args.get('company_id', type=int)
    
    # If user has limited access, restrict to their companies
    user_companies = get_user_company_access()
    if user_companies is not None:
        if company_id is None:
            company_id = get_user_default_company()
        elif company_id not in user_companies:
            company_id = user_companies[0] if user_companies else None
    
    return company_id


# =============================================================================
# TEMPLATE RENDERING ROUTES
# =============================================================================

def register_bi_routes(app: Flask):
    """
    Register all Business Intelligence routes with the Flask app.
    Call this function after app creation to register all BI routes.
    """

    # ==========================================================================
    # EXECUTIVE DASHBOARD
    # ==========================================================================

    @app.route('/executive-dashboard')
    @require_login
    def bi_executive_dashboard():
        """Main Executive Dashboard - the top-level management view."""
        date_from, date_to = parse_date_params()
        company_id = parse_company_filter()
        
        # Check if request wants JSON API or HTML page
        if request.args.get('format') == 'json':
            data = get_executive_dashboard_data(
                user_id=session.get('user_id'),
                company_id=company_id,
                date_from=date_from,
                date_to=date_to
            )
            return jsonify(data)
        
        # Get available companies for filter
        companies = get_all_companies_for_bi()
        
        return render_template(
            'bi/executive_dashboard.html',
            page_title='Executive Dashboard',
            date_from=date_from,
            date_to=date_to,
            period=request.args.get('period', 'this_month'),
            companies=companies,
            selected_company=company_id
        )

    # ==========================================================================
    # HOLDING DASHBOARD
    # ==========================================================================

    @app.route('/holding-dashboard')
    @require_login
    def bi_holding_dashboard():
        """Holding/Group Dashboard - consolidated view across all companies."""
        date_from, date_to = parse_date_params()
        eliminate = request.args.get('eliminate_intercompany', 'false').lower() == 'true'
        
        if request.args.get('format') == 'json':
            data = get_consolidated_holding_view(
                date_from=date_from,
                date_to=date_to,
                eliminate_intercompany=eliminate
            )
            return jsonify(data)
        
        companies = get_all_companies_for_bi()
        
        return render_template(
            'bi/holding_dashboard.html',
            page_title='Holding Dashboard',
            date_from=date_from,
            date_to=date_to,
            period=request.args.get('period', 'this_month'),
            companies=companies,
            eliminate_intercompany=eliminate
        )

    # ==========================================================================
    # COMPANY PERFORMANCE DASHBOARD
    # ==========================================================================

    @app.route('/company-performance')
    @require_login
    def bi_company_performance():
        """Company Performance Comparison Dashboard."""
        date_from, date_to = parse_date_params()
        company_ids = request.args.getlist('company_ids', type=int)
        
        if request.args.get('format') == 'json':
            data = get_company_comparison(
                company_ids=company_ids if company_ids else None,
                date_from=date_from,
                date_to=date_to
            )
            return jsonify(data)
        
        companies = get_all_companies_for_bi()
        
        return render_template(
            'bi/company_performance.html',
            page_title='Company Performance',
            date_from=date_from,
            date_to=date_to,
            period=request.args.get('period', 'this_month'),
            companies=companies,
            selected_companies=company_ids
        )

    # ==========================================================================
    # SALES PERFORMANCE DASHBOARD
    # ==========================================================================

    @app.route('/sales-performance')
    @require_login
    def bi_sales_performance():
        """Sales Performance Management Dashboard."""
        date_from, date_to = parse_date_params()
        company_id = parse_company_filter()
        
        if request.args.get('format') == 'json':
            data = {
                'sales': get_sales_kpis(company_id, date_from, date_to),
                'customers': get_customer_metrics(date_from, date_to, company_id),
                'funnel': get_inquiry_to_order_funnel(date_from, date_to, company_id)
            }
            return jsonify(data)
        
        companies = get_all_companies_for_bi()
        
        return render_template(
            'bi/sales_performance.html',
            page_title='Sales Performance',
            date_from=date_from,
            date_to=date_to,
            period=request.args.get('period', 'this_month'),
            companies=companies,
            selected_company=company_id
        )

    # ==========================================================================
    # INVENTORY & WAREHOUSE DASHBOARD
    # ==========================================================================

    @app.route('/inventory-performance')
    @require_login
    def bi_inventory_performance():
        """Inventory & Warehouse Management Dashboard."""
        company_id = parse_company_filter()
        warehouse_id = request.args.get('warehouse_id', type=int)
        
        if request.args.get('format') == 'json':
            data = {
                'inventory': get_inventory_kpis(company_id, warehouse_id),
                'turnover': get_inventory_turnover(days=90)
            }
            return jsonify(data)
        
        companies = get_all_companies_for_bi()
        warehouses = get_all_warehouses_for_bi(company_id)
        
        return render_template(
            'bi/inventory_performance.html',
            page_title='Inventory & Warehouse',
            companies=companies,
            warehouses=warehouses,
            selected_company=company_id,
            selected_warehouse=warehouse_id
        )

    # ==========================================================================
    # LOGISTICS & DELIVERY DASHBOARD
    # ==========================================================================

    @app.route('/logistics-performance')
    @require_login
    def bi_logistics_performance():
        """Logistics & Delivery Management Dashboard."""
        date_from, date_to = parse_date_params()
        company_id = parse_company_filter()
        
        if request.args.get('format') == 'json':
            data = get_logistics_kpis(date_from, date_to, company_id)
            return jsonify(data)
        
        companies = get_all_companies_for_bi()
        
        return render_template(
            'bi/logistics_performance.html',
            page_title='Logistics & Delivery',
            date_from=date_from,
            date_to=date_to,
            period=request.args.get('period', 'this_month'),
            companies=companies,
            selected_company=company_id
        )

    # ==========================================================================
    # PROCUREMENT & SUPPLIER DASHBOARD
    # ==========================================================================

    @app.route('/procurement-performance')
    @require_login
    def bi_procurement_performance():
        """Procurement & Supplier Management Dashboard."""
        date_from, date_to = parse_date_params()
        company_id = parse_company_filter()
        
        if request.args.get('format') == 'json':
            data = get_procurement_kpis(date_from, date_to, company_id)
            return jsonify(data)
        
        companies = get_all_companies_for_bi()
        
        return render_template(
            'bi/procurement_performance.html',
            page_title='Procurement & Supplier',
            date_from=date_from,
            date_to=date_to,
            period=request.args.get('period', 'this_month'),
            companies=companies,
            selected_company=company_id
        )

    # ==========================================================================
    # HR & WORKFORCE DASHBOARD
    # ==========================================================================

    @app.route('/hr-performance')
    @require_login
    def hr_performance():
        """HR & Workforce Management Dashboard."""
        date_from, date_to = parse_date_params()
        company_id = parse_company_filter()
        
        if request.args.get('format') == 'json':
            data = get_hr_kpis(date_from, date_to, company_id)
            return jsonify(data)
        
        companies = get_all_companies_for_bi()
        
        return render_template(
            'bi/hr_performance.html',
            page_title='HR & Workforce',
            date_from=date_from,
            date_to=date_to,
            period=request.args.get('period', 'this_month'),
            companies=companies,
            selected_company=company_id
        )

    # ==========================================================================
    # FINANCE & COLLECTIONS DASHBOARD
    # ==========================================================================

    @app.route('/finance-performance')
    @require_login
    def finance_performance():
        """Finance & Collections Management Dashboard."""
        date_from, date_to = parse_date_params()
        company_id = parse_company_filter()
        
        if request.args.get('format') == 'json':
            data = get_financial_kpis(date_from, date_to, company_id)
            return jsonify(data)
        
        companies = get_all_companies_for_bi()
        
        return render_template(
            'bi/finance_performance.html',
            page_title='Finance & Collections',
            date_from=date_from,
            date_to=date_to,
            period=request.args.get('period', 'this_month'),
            companies=companies,
            selected_company=company_id
        )

    # ==========================================================================
    # MARKETING & LEAD DASHBOARD
    # ==========================================================================

    @app.route('/marketing-performance')
    @require_login
    def marketing_performance():
        """Marketing & Lead Management Dashboard."""
        date_from, date_to = parse_date_params()
        company_id = parse_company_filter()
        
        if request.args.get('format') == 'json':
            data = get_marketing_kpis(date_from, date_to, company_id)
            return jsonify(data)
        
        companies = get_all_companies_for_bi()
        
        return render_template(
            'bi/marketing_performance.html',
            page_title='Marketing & Leads',
            date_from=date_from,
            date_to=date_to,
            period=request.args.get('period', 'this_month'),
            companies=companies,
            selected_company=company_id
        )

    # ==========================================================================
    # RISK ALERTS & EXCEPTION CENTER
    # ==========================================================================

    @app.route('/risk-alerts')
    @require_login
    def risk_alerts():
        """Risk Alerts & Exception Center."""
        company_id = parse_company_filter()
        severity = request.args.get('severity', 'MEDIUM')
        
        if request.args.get('format') == 'json':
            data = get_alerts_and_exceptions(company_id, severity)
            return jsonify({
                'alerts': data,
                'summary': {
                    'total': len(data),
                    'critical': len([a for a in data if a['severity'] == 'CRITICAL']),
                    'high': len([a for a in data if a['severity'] == 'HIGH']),
                    'medium': len([a for a in data if a['severity'] == 'MEDIUM'])
                }
            })
        
        companies = get_all_companies_for_bi()
        
        return render_template(
            'bi/risk_alerts.html',
            page_title='Risk Alerts & Exceptions',
            companies=companies,
            selected_company=company_id,
            severity_threshold=severity
        )

    # ==========================================================================
    # CONSOLIDATED REPORTS
    # ==========================================================================

    @app.route('/reports/consolidated')
    @require_login
    def consolidated_reports():
        """Consolidated Management Reports."""
        date_from, date_to = parse_date_params()
        eliminate = request.args.get('eliminate_intercompany', 'false').lower() == 'true'
        report_type = request.args.get('type', 'sales')
        
        if request.args.get('format') == 'json':
            if report_type == 'sales':
                data = get_sales_kpis(None, date_from, date_to)
            elif report_type == 'inventory':
                data = get_inventory_kpis(None)
            elif report_type == 'logistics':
                data = get_logistics_kpis(date_from, date_to)
            elif report_type == 'procurement':
                data = get_procurement_kpis(date_from, date_to)
            elif report_type == 'hr':
                data = get_hr_kpis(date_from, date_to)
            elif report_type == 'financial':
                data = get_financial_kpis(date_from, date_to)
            else:
                data = get_executive_dashboard_data(session.get('user_id'), None, date_from, date_to)
            
            data['consolidated_view'] = get_consolidated_holding_view(date_from, date_to, eliminate)
            return jsonify(data)
        
        companies = get_all_companies_for_bi()
        
        return render_template(
            'bi/consolidated_reports.html',
            page_title='Consolidated Reports',
            date_from=date_from,
            date_to=date_to,
            period=request.args.get('period', 'this_month'),
            companies=companies,
            eliminate_intercompany=eliminate,
            report_type=report_type
        )

    # ==========================================================================
    # COMPARATIVE REPORTS
    # ==========================================================================

    @app.route('/reports/comparative')
    @require_login
    def comparative_reports():
        """Comparative Reports - Company/Branch/Warehouse comparison."""
        date_from, date_to = parse_date_params()
        compare_type = request.args.get('compare', 'company')
        
        if request.args.get('format') == 'json':
            if compare_type == 'company':
                data = get_company_comparison(None, date_from, date_to)
            else:
                data = {'error': f'Compare type {compare_type} not implemented'}
            return jsonify(data)
        
        companies = get_all_companies_for_bi()
        
        return render_template(
            'bi/comparative_reports.html',
            page_title='Comparative Reports',
            date_from=date_from,
            date_to=date_to,
            period=request.args.get('period', 'this_month'),
            companies=companies,
            compare_type=compare_type
        )

    # ==========================================================================
    # DRILL-DOWN API ENDPOINTS
    # ==========================================================================

    @app.route('/api/bi/drilldown/sales/by-company')
    @require_login
    def api_drilldown_sales_by_company():
        """Drill-down: Sales breakdown by company."""
        date_from, date_to = parse_date_params()
        company_id = parse_company_filter()
        
        data = drill_down_sales_by_company(date_from, date_to, company_id)
        return jsonify({
            'period': {'from': date_from, 'to': date_to},
            'data': data
        })

    @app.route('/api/bi/drilldown/sales/by-item')
    @require_login
    def api_drilldown_sales_by_item():
        """Drill-down: Sales breakdown by item."""
        date_from, date_to = parse_date_params()
        company_id = parse_company_filter()
        limit = request.args.get('limit', 50, type=int)
        
        data = drill_down_sales_by_item(date_from, date_to, company_id, limit)
        return jsonify({
            'period': {'from': date_from, 'to': date_to},
            'data': data
        })

    @app.route('/api/bi/drilldown/inventory/by-warehouse')
    @require_login
    def api_drilldown_inventory_by_warehouse():
        """Drill-down: Inventory breakdown by warehouse."""
        company_id = parse_company_filter()
        
        data = drill_down_inventory_by_warehouse(company_id)
        return jsonify({
            'data': data
        })

    @app.route('/api/bi/kpis/<kpi_type>')
    @require_login
    def api_kpi_type(kpi_type):
        """API endpoint for specific KPI types."""
        date_from, date_to = parse_date_params()
        company_id = parse_company_filter()
        
        if kpi_type == 'sales':
            data = get_sales_kpis(company_id, date_from, date_to)
        elif kpi_type == 'inventory':
            data = get_inventory_kpis(company_id)
        elif kpi_type == 'logistics':
            data = get_logistics_kpis(date_from, date_to, company_id)
        elif kpi_type == 'procurement':
            data = get_procurement_kpis(date_from, date_to, company_id)
        elif kpi_type == 'hr':
            data = get_hr_kpis(date_from, date_to, company_id)
        elif kpi_type == 'marketing':
            data = get_marketing_kpis(date_from, date_to, company_id)
        elif kpi_type == 'financial':
            data = get_financial_kpis(date_from, date_to, company_id)
        elif kpi_type == 'customers':
            data = get_customer_metrics(date_from, date_to, company_id)
        elif kpi_type == 'funnel':
            data = get_inquiry_to_order_funnel(date_from, date_to, company_id)
        elif kpi_type == 'turnover':
            days = request.args.get('days', 90, type=int)
            data = get_inventory_turnover(days)
        else:
            return jsonify({'error': f'Unknown KPI type: {kpi_type}'}), 400
        
        return jsonify(data)

    @app.route('/api/bi/alerts')
    @require_login
    def api_alerts():
        """API endpoint for alerts and exceptions."""
        company_id = parse_company_filter()
        severity = request.args.get('severity', 'MEDIUM')
        
        data = get_alerts_and_exceptions(company_id, severity)
        return jsonify({
            'alerts': data,
            'count': len(data),
            'severity_filter': severity
        })

    @app.route('/api/bi/holding')
    @require_login
    def api_holding():
        """API endpoint for holding consolidated view."""
        date_from, date_to = parse_date_params()
        eliminate = request.args.get('eliminate_intercompany', 'false').lower() == 'true'
        
        data = get_consolidated_holding_view(date_from, date_to, eliminate)
        return jsonify(data)

    @app.route('/api/bi/company-comparison')
    @require_login
    def api_company_comparison():
        """API endpoint for company comparison."""
        date_from, date_to = parse_date_params()
        company_ids = request.args.getlist('company_ids', type=int)
        
        data = get_company_comparison(
            company_ids=company_ids if company_ids else None,
            date_from=date_from,
            date_to=date_to
        )
        return jsonify(data)

    # =============================================================================
# EXPORT ENDPOINTS - ALL 20 EXPORT TYPES
# ==============================================================================

    VALID_EXPORT_TYPES = [
        'csv', 'excel_text', 'excel_general', 'json', 'xml', 'txt',
        'pdf', 'docx', 'html', 'printable', 'barcode', 'api',
        'email', 'zip', 'backup', 'sql_dump', 'dashboard',
        'summary', 'detailed', 'audit_log'
    ]

    EXPORT_COLUMNS = {
        'sales': ['order_number', 'customer', 'date', 'amount', 'status'],
        'inventory': ['item_code', 'item_name', 'quantity', 'value'],
        'alerts': ['severity', 'type', 'title', 'description'],
        'holding': ['company_name', 'total_sales', 'order_count', 'customer_count'],
        'customers': ['customer_id', 'name', 'email', 'total_orders', 'total_value'],
        'logistics': ['shipment_id', 'origin', 'destination', 'status', 'delivery_date'],
        'procurement': ['po_number', 'supplier', 'amount', 'status', 'expected_date'],
        'hr': ['employee_id', 'name', 'department', 'position', 'status'],
        'marketing': ['campaign_id', 'name', 'channel', 'budget', 'roi'],
        'financial': ['invoice_id', 'customer', 'amount', 'due_date', 'status']
    }


    @app.route('/api/bi/export/<export_type>', methods=['GET', 'POST'])
    @app.route('/api/bi/export/<report_type>/<export_type>', methods=['GET', 'POST'])
    @require_login
    def api_export_report(report_type=None, export_type=None):
        """Export report data in all 20 formats."""
        # Handle combined path like /api/bi/export/sales/csv
        if export_type is None:
            export_type = report_type
            report_type = request.args.get('report', 'sales')

        if export_type not in VALID_EXPORT_TYPES:
            return jsonify({
                'error': f'Invalid export type. Valid types: {VALID_EXPORT_TYPES}'
            }), 400

        date_from, date_to = parse_date_params()
        company_id = parse_company_filter()

        # Get data based on report type
        report_type = report_type or 'sales'
        if report_type == 'sales':
            data = get_sales_kpis(company_id, date_from, date_to)
            columns = EXPORT_COLUMNS['sales']
            title = f'Sales Report: {date_from} to {date_to}'
        elif report_type == 'inventory':
            data = get_inventory_kpis(company_id)
            columns = EXPORT_COLUMNS['inventory']
            title = 'Inventory Report'
        elif report_type == 'alerts':
            data = get_alerts_and_exceptions(company_id)
            columns = EXPORT_COLUMNS['alerts']
            title = 'Risk Alerts Report'
        elif report_type == 'holding':
            data = get_consolidated_holding_view(date_from, date_to)
            columns = EXPORT_COLUMNS['holding']
            title = f'Holding Consolidated: {date_from} to {date_to}'
        elif report_type == 'customers':
            data = get_customer_metrics(date_from, date_to, company_id)
            columns = EXPORT_COLUMNS['customers']
            title = 'Customer Metrics Report'
        elif report_type == 'logistics':
            data = get_logistics_kpis(date_from, date_to, company_id)
            columns = EXPORT_COLUMNS['logistics']
            title = f'Logistics Report: {date_from} to {date_to}'
        elif report_type == 'procurement':
            data = get_procurement_kpis(date_from, date_to, company_id)
            columns = EXPORT_COLUMNS['procurement']
            title = f'Procurement Report: {date_from} to {date_to}'
        elif report_type == 'hr':
            data = get_hr_kpis(date_from, date_to, company_id)
            columns = EXPORT_COLUMNS['hr']
            title = f'HR Report: {date_from} to {date_to}'
        elif report_type == 'marketing':
            data = get_marketing_kpis(date_from, date_to, company_id)
            columns = EXPORT_COLUMNS['marketing']
            title = f'Marketing Report: {date_from} to {date_to}'
        elif report_type == 'financial':
            data = get_financial_kpis(date_from, date_to, company_id)
            columns = EXPORT_COLUMNS['financial']
            title = f'Financial Report: {date_from} to {date_to}'
        else:
            # Default to executive dashboard data
            data = get_executive_dashboard_data(session.get('user_id'), company_id, date_from, date_to)
            columns = get_export_columns(data)
            title = f'Executive Dashboard: {date_from} to {date_to}'

        filename = f'{report_type}_report_{date_from}_{date_to}'

        # Handle POST with filters
        if request.method == 'POST':
            filters = request.json or {}
            # Apply filters to data
            data = _apply_export_filters(data, filters)

        return send_export_response(data, export_type, filename, columns, title)


    def _apply_export_filters(data, filters):
        """Apply filters to exported data."""
        if not filters:
            return data

        filtered = []
        for record in data:
            include = True
            for key, value in filters.items():
                if key in record and str(record[key]) != str(value):
                    include = False
                    break
            if include:
                filtered.append(record)
        return filtered


    @app.route('/api/bi/export/list')
    @require_login
    def list_bi_export_types():
        """List available export types for BI module."""
        return jsonify({
            'module': 'bi',
            'report_types': list(EXPORT_COLUMNS.keys()),
            'export_types': [{'type': t} for t in VALID_EXPORT_TYPES]
        })


# =============================================================================
# EXPORT HELPERS (Legacy - kept for backward compatibility)
# =============================================================================

def export_to_csv_response(data, columns, filename):
    """Generate CSV export response (legacy wrapper)."""
    content = export_to_csv(data, filename, columns)
    return Response(
        content,
        mimetype='text/csv; charset=utf-8-sig',
        headers={'Content-Disposition': f'attachment; filename={filename}.csv'}
    )


# =============================================================================
# SETTINGS / KPI DEFINITIONS
# =============================================================================

    @app.route('/bi/settings')
    @require_login
    def bi_settings():
        """BI Settings - KPI definitions and thresholds."""
        return render_template(
            'bi/settings.html',
            page_title='BI Settings & KPI Definitions'
        )

    @app.route('/bi/settings')
    @require_login
    def bi_settings():
        """BI Settings - KPI definitions and thresholds."""
        return render_template(
            'bi/settings.html',
            page_title='BI Settings & KPI Definitions'
        )

    @app.route('/bi/kpi-definitions')
    @require_login
    def kpi_definitions():
        """KPI Definitions page."""
        # Return standard KPI definitions
        kpi_defs = [
            {
                'id': 'sales.total_revenue',
                'name': 'Total Revenue',
                'category': 'Sales',
                'description': 'Sum of all order amounts in period',
                'formula': 'SUM(sales_orders.total_amount)',
                'target_label': 'Monthly Target',
                'warning_threshold': 0.9,
                'critical_threshold': 0.8
            },
            {
                'id': 'sales.orders_count',
                'name': 'Order Count',
                'category': 'Sales',
                'description': 'Total number of orders in period',
                'formula': 'COUNT(sales_orders.id)',
                'target_label': 'Monthly Order Target',
                'warning_threshold': 0.85,
                'critical_threshold': 0.7
            },
            {
                'id': 'inventory.stock_value',
                'name': 'Inventory Stock Value',
                'category': 'Inventory',
                'description': 'Total value of inventory on hand',
                'formula': 'SUM(inventory.quantity * items.unit_cost)',
                'target_label': 'Target Stock Value',
                'warning_threshold': 1.1,
                'critical_threshold': 1.2
            },
            {
                'id': 'inventory.stockout_count',
                'name': 'Stockout Items',
                'category': 'Inventory',
                'description': 'Number of items with zero stock',
                'formula': 'COUNT(items WHERE quantity <= 0)',
                'target_label': 'Max Stockouts',
                'warning_threshold': 5,
                'critical_threshold': 10
            },
            {
                'id': 'logistics.on_time_rate',
                'name': 'On-Time Delivery Rate',
                'category': 'Logistics',
                'description': 'Percentage of deliveries on time',
                'formula': 'COUNT(deliveries WHERE arrival <= scheduled) / COUNT(deliveries) * 100',
                'target_label': 'Target OT Rate',
                'warning_threshold': 0.95,
                'critical_threshold': 0.9
            },
            {
                'id': 'hr.attendance_rate',
                'name': 'Attendance Rate',
                'category': 'HR',
                'description': 'Percentage of employees present',
                'formula': 'SUM(present) / COUNT(employees) * 100',
                'target_label': 'Target Attendance',
                'warning_threshold': 0.95,
                'critical_threshold': 0.9
            },
            {
                'id': 'finance.receivables',
                'name': 'Total Receivables',
                'category': 'Finance',
                'description': 'Outstanding customer balances',
                'formula': 'SUM(customers.outstanding_balance)',
                'target_label': 'Max Receivables',
                'warning_threshold': 1.0,
                'critical_threshold': 1.2
            },
            {
                'id': 'marketing.conversion_rate',
                'name': 'Lead Conversion Rate',
                'category': 'Marketing',
                'description': 'Percentage of leads converted to customers',
                'formula': 'COUNT(converted_leads) / COUNT(total_leads) * 100',
                'target_label': 'Target Conversion',
                'warning_threshold': 0.85,
                'critical_threshold': 0.7
            }
        ]
        
        return jsonify({'kpi_definitions': kpi_defs})

    # ==========================================================================
    # CATCH-ALL FOR MISSING BI ROUTES
    # ==========================================================================

    @app.route('/bi/<path:subpath>')
    @require_login
    def bi_catchall(subpath):
        """Catch-all route for BI pages."""
        return render_template(
            'bi/base_bi.html',
            page_title=f'BI: {subpath}',
            error=f'Page {subpath} not found'
        )


# =============================================================================
# EXPORT HELPERS
# =============================================================================

def export_to_csv_response(data, columns, filename):
    """Generate CSV export response."""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    
    if isinstance(data, list):
        for row in data:
            writer.writerow({col: row.get(col, '') for col in columns})
    elif isinstance(data, dict) and 'by_company' in data:
        for row in data['by_company']:
            writer.writerow({col: row.get(col, '') for col in columns})
    
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}.csv'}
    )


def export_to_excel_response(data, columns, filename):
    """Generate Excel export response."""
    wb = Workbook()
    ws = wb.active
    ws.title = filename[:31]
    
    # Header row
    ws.append(columns)
    
    # Data rows
    if isinstance(data, list):
        for row in data:
            ws.append([row.get(col, '') for col in columns])
    elif isinstance(data, dict) and 'by_company' in data:
        for row in data['by_company']:
            ws.append([row.get(col, '') for col in columns])
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return Response(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': f'attachment; filename={filename}.xlsx'}
    )


# =============================================================================
# STANDALONE TEST
# =============================================================================

if __name__ == '__main__':
    # Test the routes by running standalone
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret'
    
    with app.app_context():
        from database import initialize_platform_schema
        initialize_platform_schema()
    
    register_bi_routes(app)
    
    print("BI Routes registered. Available endpoints:")
    print("  /executive-dashboard")
    print("  /holding-dashboard")
    print("  /company-performance")
    print("  /sales-performance")
    print("  /inventory-performance")
    print("  /logistics-performance")
    print("  /procurement-performance")
    print("  /hr-performance")
    print("  /finance-performance")
    print("  /marketing-performance")
    print("  /risk-alerts")
    print("  /reports/consolidated")
    print("  /reports/comparative")
    print("  /api/bi/*")
