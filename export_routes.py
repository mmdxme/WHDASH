"""
Export Routes - Central Export Blueprint
========================================
Provides centralized export functionality that can be used by all modules.
All modules can import and use the export_bp blueprint or individual functions.

Usage:
    from export_routes import register_export_routes
    register_export_routes(app, 'bi', get_bi_data, get_bi_columns)

    Or use the export decorator directly:
    @export_bp.route('/export/<export_type>')
    @require_login
    def export_data(export_type):
        ...
"""

from flask import Blueprint, request, jsonify, session, Response
from functools import wraps
import io
import csv
import json
from datetime import datetime

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

# Valid export types
VALID_EXPORT_TYPES = [
    'csv', 'excel_text', 'excel_general', 'json', 'xml', 'txt',
    'pdf', 'docx', 'html', 'printable', 'barcode', 'api',
    'email', 'zip', 'backup', 'sql_dump', 'dashboard',
    'summary', 'detailed', 'audit_log'
]


# =============================================================================
# EXPORT DECORATOR AND HELPERS
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


def export_required_permission(module_name='reports'):
    """Decorator to require export permission for a module."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from permissions import user_has_permission
            user_id = session.get('user_id')

            if not user_has_permission(user_id, module_name, 'export', 'read'):
                if request.is_json:
                    return jsonify({'error': 'Export permission denied'}), 403
                return {'error': 'Export permission denied'}, 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def create_export_route(module_name, data_getter, columns_getter=None, title_getter=None):
    """
    Factory function to create an export route for a module.

    Args:
        module_name: Name of the module (e.g., 'bi', 'ecommerce')
        data_getter: Function to get data for export
        columns_getter: Function to get column definitions (optional)
        title_getter: Function to get report title (optional)

    Returns:
        Flask route function
    """
    def export_data(export_type):
        if export_type not in VALID_EXPORT_TYPES:
            return jsonify({
                'error': f'Invalid export type. Valid types: {VALID_EXPORT_TYPES}'
            }), 400

        # Get data based on request method
        if request.method == 'POST':
            filters = request.json or {}
            data = data_getter(filters=filters)
        else:
            data = data_getter()

        # Get columns
        if columns_getter:
            columns = columns_getter()
        else:
            columns = get_export_columns(data)

        # Get title
        title = title_getter() if title_getter else f'{module_name}_export'

        return send_export_response(data, export_type, f'{module_name}_{export_type}', columns, title)

    return export_data


# =============================================================================
# STANDALONE EXPORT BLUEPRINT
# =============================================================================

export_bp = Blueprint('export', __name__, url_prefix='/export')


@export_bp.route('/api/<module>/export/<export_type>', methods=['GET', 'POST'])
@require_login
def module_export(module, export_type):
    """
    Generic export endpoint for all modules.
    URL pattern: /export/api/{module}/export/{export_type}

    Query parameters:
        - page: Page number for API pagination
        - per_page: Items per page
    """
    if export_type not in VALID_EXPORT_TYPES:
        return jsonify({
            'error': f'Invalid export type. Valid types: {VALID_EXPORT_TYPES}'
        }), 400

    # Import module data getters on demand
    module_data_funcs = {
        'bi': _get_bi_data,
        'ecommerce': _get_ecommerce_data,
        'marketing': _get_marketing_data,
        'security': _get_security_data,
        'integration': _get_integration_data,
        'btp': _get_btp_data,
        'project': _get_project_data,
        'sales': _get_sales_data,
        'hr': _get_hr_data,
        'logistics': _get_logistics_data,
        'wms': _get_wms_data,
        'scm': _get_scm_data,
        'talent': _get_talent_data,
        'payroll': _get_payroll_data,
        'finance': _get_finance_data,
        'workflow': _get_workflow_data,
        'quality': _get_quality_data,
        'form': _get_form_data,
    }

    if module not in module_data_funcs:
        return jsonify({'error': f'Module {module} not supported for export'}), 400

    try:
        data = module_data_funcs[module]()
        columns = get_export_columns(data)
        return send_export_response(data, export_type, f'{module}_export', columns)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _get_bi_data(filters=None):
    """Get BI module data."""
    from bi_routes import get_executive_dashboard_data
    return get_executive_dashboard_data(session.get('user_id'))


def _get_ecommerce_data(filters=None):
    """Get E-commerce module data."""
    from ecommerce_models import EcommerceOrderImport
    with __import__('database').get_db_context() as db:
        rows = db.execute("SELECT * FROM ecommerce_order_imports LIMIT 1000").fetchall()
        return [dict(r) for r in rows]


def _get_marketing_data(filters=None):
    """Get Marketing module data."""
    from marketing_models import get_db
    conn = get_db()
    cursor = conn.cursor()
    rows = cursor.execute("SELECT * FROM marketing_campaigns LIMIT 1000").fetchall()
    return [dict(r) for r in rows]


def _get_security_data(filters=None):
    """Get Security module data."""
    from security_models import get_security_events
    return get_security_events(limit=1000)


def _get_integration_data(filters=None):
    """Get Integration module data."""
    from integration_models import get_all_connectors
    return get_all_connectors()


def _get_btp_data(filters=None):
    """Get BTP module data."""
    try:
        from btp_models import get_btp_overview
        return get_btp_overview()
    except (ImportError, AttributeError) as e:
        import logging
        logging.getLogger(__name__).warning(f"BTP overview not available: {e}")
        return []


def _get_project_data(filters=None):
    """Get Project module data."""
    from project_models import get_all_projects
    return get_all_projects()


def _get_sales_data(filters=None):
    """Get Sales module data."""
    from sales_models import get_all_sales_orders
    return get_all_sales_orders()


def _get_hr_data(filters=None):
    """Get HR module data."""
    from hr_models import get_all_employees
    return get_all_employees()


def _get_logistics_data(filters=None):
    """Get Logistics module data."""
    from logistics_models import get_all_deliveries
    return get_all_deliveries()


def _get_wms_data(filters=None):
    """Get WMS module data."""
    try:
        from database import get_db_context
        with get_db_context() as db:
            rows = db.execute("""
                SELECT 
                    ib.id,
                    ib.item_id,
                    i.item_code,
                    i.name as item_name,
                    w.name as warehouse_name,
                    l.location_code,
                    l.zone,
                    ib.lot_id,
                    lb.lot_number,
                    lb.expiry_date,
                    ib.quantity as on_hand,
                    ib.reserved,
                    ib.available,
                    ib.quarantine,
                    ib.blocked,
                    ib.status,
                    i.barcode,
                    i.part_number,
                    i.uom_code,
                    i.min_stock_level,
                    i.reorder_point
                FROM wms_inventory_balances ib
                LEFT JOIN wms_items i ON ib.item_id = i.id
                LEFT JOIN wms_warehouses w ON ib.warehouse_id = w.id
                LEFT JOIN wms_locations l ON ib.location_id = l.id
                LEFT JOIN wms_lots lb ON ib.lot_id = lb.id
                ORDER BY i.item_code, w.name, l.location_code
                LIMIT 10000
            """).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"WMS data not available: {e}")
        return []


def _get_scm_data(filters=None):
    """Get SCM module data."""
    try:
        from scm_models import get_scm_data
        return get_scm_data()
    except (ImportError, AttributeError) as e:
        import logging
        logging.getLogger(__name__).warning(f"SCM data not available: {e}")
        return []


def _get_talent_data(filters=None):
    """Get Talent module data."""
    try:
        from talent_models import get_talent_pool_members
        # Get talent pool members if the function exists
        if hasattr(talent_models, 'get_talent_pool'):
            return talent_models.get_talent_pool()
        return []
    except (ImportError, AttributeError) as e:
        import logging
        logging.getLogger(__name__).warning(f"Talent data not available: {e}")
        return []


def _get_payroll_data(filters=None):
    """Get Payroll module data."""
    try:
        from payroll_models import get_payroll_records
        return get_payroll_records()
    except (ImportError, AttributeError) as e:
        import logging
        logging.getLogger(__name__).warning(f"Payroll data not available: {e}")
        return []


def _get_finance_data(filters=None):
    """Get Finance module data."""
    try:
        from finance_models import get_finance_data
        return get_finance_data()
    except (ImportError, AttributeError) as e:
        import logging
        logging.getLogger(__name__).warning(f"Finance data not available: {e}")
        return []


def _get_workflow_data(filters=None):
    """Get Workflow module data."""
    from workflow_models import get_all_workflows
    return get_all_workflows()


def _get_quality_data(filters=None):
    """Get Quality module data."""
    from quality_models import get_quality_records
    return get_quality_records()


def _get_form_data(filters=None):
    """Get Form module data."""
    from form_models import get_all_forms
    return get_all_forms()


# =============================================================================
# REGISTER EXPORT ROUTES
# =============================================================================

def register_export_routes(app, module_name, data_getter, columns_getter=None):
    """
    Register export routes for a specific module.

    Args:
        app: Flask application
        module_name: Name of the module
        data_getter: Function to get data for export
        columns_getter: Optional function to get column definitions
    """
    endpoint_name = f'{module_name}_export'

    @app.route(f'/api/{module_name}/export/<export_type>', methods=['GET', 'POST'])
    @require_login
    def export_endpoint(export_type):
        return create_export_route(module_name, data_getter, columns_getter)(export_type)


# =============================================================================
# EXPORT HISTORY TRACKING
# =============================================================================

def log_export(export_type, module_name, user_id, record_count, file_size):
    """Log an export operation for audit trail."""
    try:
        from database import get_db_context
        with get_db_context() as db:
            db.execute("""
                INSERT INTO export_history (export_type, module_name, user_id, record_count,
                                           file_size, created_at, ip_address)
                VALUES (?, ?, ?, ?, ?, datetime('now'), ?)
            """, (export_type, module_name, user_id, record_count, file_size,
                  request.remote_addr if request else ''))
            db.commit()
    except Exception as e:
        print(f"Failed to log export: {e}")


def get_export_history(module_name=None, limit=100):
    """Get export history for audit purposes."""
    from database import get_db_context
    with get_db_context() as db:
        if module_name:
            rows = db.execute("""
                SELECT * FROM export_history
                WHERE module_name = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (module_name, limit)).fetchall()
        else:
            rows = db.execute("""
                SELECT * FROM export_history
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
        return [dict(r) for r in rows]


# =============================================================================
# EXPORT TYPES LIST
# =============================================================================

@export_bp.route('/export/types')
@require_login
def list_export_types():
    """List all available export types."""
    return jsonify({
        'export_types': [
            {'type': 'csv', 'name': 'CSV Export', 'description': 'Comma-separated values with UTF-8 BOM'},
            {'type': 'excel_text', 'name': 'Excel (Text Cells)', 'description': 'Excel with text-formatted cells'},
            {'type': 'excel_general', 'name': 'Excel (General)', 'description': 'Excel with auto-detected types'},
            {'type': 'json', 'name': 'JSON', 'description': 'Clean JSON with indentation'},
            {'type': 'xml', 'name': 'XML', 'description': 'Valid XML 1.0 with declaration'},
            {'type': 'txt', 'name': 'Text File', 'description': 'Tab-separated plain text'},
            {'type': 'pdf', 'name': 'PDF Report', 'description': 'Formatted PDF with ReportLab'},
            {'type': 'docx', 'name': 'Word Document', 'description': 'DOCX with python-docx'},
            {'type': 'html', 'name': 'HTML', 'description': 'Clean HTML5 with inline CSS'},
            {'type': 'printable', 'name': 'Printable HTML', 'description': 'Print-optimized HTML'},
            {'type': 'barcode', 'name': 'Barcode Labels', 'description': 'QR codes and Code128 labels'},
            {'type': 'api', 'name': 'API JSON', 'description': 'RESTful JSON with pagination'},
            {'type': 'email', 'name': 'Email HTML', 'description': 'Email-ready HTML with inline CSS'},
            {'type': 'zip', 'name': 'ZIP Archive', 'description': 'Compressed archive'},
            {'type': 'backup', 'name': 'Backup File', 'description': 'Database-style backup'},
            {'type': 'sql_dump', 'name': 'SQL Dump', 'description': 'Executable SQL INSERT statements'},
            {'type': 'dashboard', 'name': 'Dashboard State', 'description': 'Complete dashboard export'},
            {'type': 'summary', 'name': 'Summary Report', 'description': 'One-page summary with KPIs'},
            {'type': 'detailed', 'name': 'Detailed Report', 'description': 'Full multi-section report'},
            {'type': 'audit_log', 'name': 'Audit Log', 'description': 'Export with audit trail info'}
        ]
    })
