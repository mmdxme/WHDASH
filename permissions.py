"""
Unified Permission / RBAC System
================================
Centralized Role-Based Access Control (RBAC) for the entire MMDx platform.

This module provides:
- Single source of truth for all permissions
- Role hierarchy with inheritance
- Permission categories for different modules
- Helper decorators for route protection
- User/Role permission cache for performance

PERMISSION STRUCTURE:
- Permissions are grouped by MODULE (e.g., HR, WMS, CRM, etc.)
- Each module has RESOURCE types (e.g., employees, leave, inventory)
- Each resource has ACTION permissions (view, create, edit, delete, approve)

BACKWARD COMPATIBILITY:
- This module works with both the legacy roles table (with permission flags)
- And the new role_permissions table for granular permissions
- The new system is used when available, falls back to legacy

USAGE:
    from permissions import (
        require_permission, check_permission,
        get_user_permissions, get_role_permissions,
        add_role, assign_role_to_user
    )

    # In routes:
    @app.route('/hr/employees')
    @require_login
    @require_permission('hr', 'employees', 'view')
    def hr_employees():
        ...
"""

from functools import wraps
from typing import List, Optional, Set, Dict, Any

# Import database functions - use lazy import to avoid circular imports
def _get_db():
    from database import get_db_context
    return get_db_context()

# Expose lazy import for use by other functions
def get_db_context():
    from database import get_db_context as _gdb
    return _gdb()

# ============================================================================
# PERMISSION HIERARCHY
# ============================================================================

# Module definitions with their resources and actions
MODULE_PERMISSIONS = {
    'assets': {
        'label': 'Asset Management',
        'resources': {
            'dashboard': ['view'],
            'assets': ['view', 'create', 'edit', 'delete', 'activate', 'transfer', 'dispose'],
            'categories': ['view', 'create', 'edit', 'delete'],
            'acquisitions': ['view', 'create', 'edit', 'approve'],
            'depreciation': ['view', 'create', 'run', 'post', 'reverse', 'approve'],
            'depreciation_profiles': ['view', 'create', 'edit'],
            'maintenance': ['view', 'create', 'edit', 'complete'],
            'maintenance_schedules': ['view', 'create', 'edit', 'delete'],
            'maintenance_work_orders': ['view', 'create', 'edit', 'complete'],
            'maintenance_work_logs': ['view', 'create', 'edit'],
            'maintenance_costs': ['view', 'create'],
            'transfers': ['view', 'create', 'approve'],
            'assignments': ['view', 'create', 'edit'],
            'disposal': ['view', 'create', 'approve', 'execute'],
            'disposal_requests': ['view', 'create', 'edit', 'approve', 'reject'],
            'audit_log': ['view', 'export'],
            'reports': ['view', 'export'],
            'settings': ['view', 'edit'],
        }
    },
    'maintenance': {
        'label': 'Maintenance Management (EAM/PM)',
        'resources': {
            # Dashboards
            'dashboard': ['view'],
            'executive_dashboard': ['view'],
            'workspace': ['view'],

            # Equipment & Technical Objects
            'equipment': ['view', 'create', 'edit'],
            'equipment_detail': ['view'],
            'equipment_downtime': ['view'],
            'facilities': ['view', 'create', 'edit', 'delete'],
            'facility_requests': ['view', 'create', 'edit', 'complete', 'delete'],

            # Preventive Maintenance
            'pm_plans': ['view', 'create', 'edit', 'delete'],
            'pm_schedules': ['view', 'create', 'edit', 'delete'],
            'pm_calendar': ['view'],
            'pm_forecast': ['view'],
            'pm_compliance': ['view'],
            'pm_missed': ['view'],
            'pm_templates': ['view', 'create', 'edit', 'delete'],

            # Corrective & Breakdown
            'corrective': ['view', 'create', 'edit'],
            'breakdown': ['view', 'create', 'edit'],
            'emergency': ['view', 'create', 'edit'],
            'incident': ['view', 'create', 'edit'],
            'root_cause': ['view', 'create', 'edit'],
            'recurring_failure': ['view', 'create', 'edit'],

            # Work Orders
            'work_orders': ['view', 'create', 'edit', 'complete', 'assign', 'delete'],
            'work_order_tasks': ['view', 'create', 'edit', 'complete'],
            'my_work_orders': ['view', 'edit', 'complete'],

            # Planning & Scheduling
            'planner_board': ['view', 'edit'],
            'backlog': ['view', 'edit'],
            'labor_capacity': ['view'],
            'shift_scheduling': ['view', 'create', 'edit'],
            'overdue_queue': ['view', 'edit'],
            'reschedule': ['view', 'edit'],

            # Resources & Labor
            'technicians': ['view', 'create', 'edit'],
            'teams': ['view', 'create', 'edit'],
            'skills': ['view', 'create', 'edit'],
            'availability': ['view', 'edit'],
            'utilization': ['view'],
            'productivity': ['view'],
            'labor_logs': ['view', 'create', 'edit'],

            # Parts & Materials
            'parts_usage': ['view', 'create', 'edit'],
            'parts_reserved': ['view', 'create', 'edit'],
            'parts_shortage': ['view', 'edit'],
            'spare_watchlist': ['view', 'create', 'edit'],
            'maintenance_bom': ['view', 'create', 'edit'],

            # Downtime & Reliability
            'downtime': ['view', 'create', 'edit'],
            'failure_modes': ['view', 'create', 'edit'],
            'mtbf': ['view'],
            'availability_trends': ['view'],
            'reliability_heatmap': ['view'],
            'reliability_reports': ['view', 'export'],

            # Shutdown & Turnaround
            'shutdown': ['view', 'create', 'edit'],
            'major_maintenance': ['view', 'create', 'edit'],
            'shutdown_risk': ['view', 'create', 'edit'],
            'milestones': ['view', 'create', 'edit'],
            'resource_bundles': ['view', 'create', 'edit'],

            # Inspections & Checklists
            'inspections': ['view', 'create', 'edit'],
            'checklists': ['view', 'create', 'edit', 'delete'],
            'defect_findings': ['view', 'create', 'edit'],
            'inspection_history': ['view'],

            # Predictive Maintenance
            'predictive': ['view'],
            'condition_indicators': ['view', 'create', 'edit'],
            'early_warning': ['view', 'edit'],
            'failure_risk': ['view'],
            'sensor_telemetry': ['view', 'create', 'edit'],
            'predictive_rules': ['view', 'create', 'edit'],

            # Documents & Technical Records
            'documents': ['view', 'create', 'edit', 'delete'],
            'attachments': ['view', 'create', 'edit', 'delete'],
            'service_history': ['view'],

            # Costing & Performance
            'cost_view': ['view'],
            'pm_cm_cost': ['view'],
            'cost_variance': ['view'],
            'labor_cost': ['view'],
            'parts_cost': ['view'],
            'downtime_cost': ['view'],
            'kpis': ['view'],

            # Workflow & Approvals
            'approvals': ['view', 'approve', 'reject'],
            'sla_policies': ['view', 'create', 'edit'],
            'escalations': ['view', 'edit'],
            'delegations': ['view', 'create', 'edit'],
            'approval_history': ['view'],

            # Reports & Analytics
            'reports': ['view', 'export'],
            'report_work_orders': ['view', 'export'],
            'report_pm': ['view', 'export'],
            'report_breakdown': ['view', 'export'],
            'report_downtime': ['view', 'export'],
            'report_reliability': ['view', 'export'],
            'report_technician': ['view', 'export'],
            'report_parts': ['view', 'export'],
            'report_costs': ['view', 'export'],
            'report_asset_history': ['view', 'export'],
            'report_inspection': ['view', 'export'],
            'report_shutdown': ['view', 'export'],
            'export': ['view', 'export'],

            # Calendar
            'calendar': ['view'],

            # Settings
            'settings': ['view', 'edit'],
            'work_order_settings': ['view', 'edit'],
            'pm_settings': ['view', 'edit'],
            'scheduling_rules': ['view', 'create', 'edit'],
            'reliability_settings': ['view', 'edit'],
            'branch_settings': ['view', 'edit'],
            'notification_settings': ['view', 'edit'],
            'audit_logs': ['view', 'export'],

            # Output Files
            'output_files': ['view', 'create', 'download'],

            # === ENHANCED EAM/PM PERMISSIONS ===
            # Functional Locations & Technical Objects
            'functional_locations': ['view', 'create', 'edit', 'delete'],
            'equipment_boms': ['view', 'create', 'edit', 'delete'],
            'equipment_structures': ['view', 'create', 'edit', 'delete'],

            # Work Centers & Capacity
            'work_centers': ['view', 'create', 'edit', 'delete'],
            'capacity_planning': ['view', 'create', 'edit'],

            # Maintenance Strategies & Counters
            'maintenance_strategies': ['view', 'create', 'edit', 'delete'],
            'counters': ['view', 'create', 'edit', 'delete'],
            'measurement_points': ['view', 'create', 'edit', 'delete'],

            # Shift & Skills Planning
            'shift_planning': ['view', 'create', 'edit'],
            'skill_catalog': ['view', 'create', 'edit', 'delete'],
            'skill_matching': ['view', 'create', 'edit'],

            # Costing & Settlement
            'cost_planning': ['view', 'create', 'edit'],
            'wip': ['view', 'create', 'edit'],
            'settlements': ['view', 'create', 'edit'],

            # Service Management
            'service_agreements': ['view', 'create', 'edit', 'delete'],
            'warranty_management': ['view', 'create', 'edit', 'delete'],

            # Notifications & Problem Management
            'notifications': ['view', 'create', 'edit', 'delete'],
            'problem_management': ['view', 'create', 'edit', 'delete'],

            # IoT & Predictive Maintenance
            'iot_devices': ['view', 'create', 'edit', 'delete'],
            'iot_alerts': ['view', 'create', 'edit', 'delete'],

            # Work Order Operations & Components
            'work_order_operations': ['view', 'create', 'edit', 'delete'],
            'work_order_components': ['view', 'create', 'edit', 'delete'],
            'work_order_confirmations': ['view', 'create', 'edit', 'delete'],
            'work_order_tools': ['view', 'create', 'edit', 'delete'],

            # Field Authorization & Data Scopes
            'field_authorization': ['view', 'create', 'edit', 'delete'],
            'data_scopes': ['view', 'create', 'edit', 'delete'],
        }
    },
    'finance': {
        'label': 'Finance & Accounting',
        'resources': {
            'dashboard': ['view'],
            'accounts': ['view', 'create', 'edit', 'delete'],
            'journals': ['view', 'create', 'edit', 'delete', 'post', 'reverse'],
            'fiscal_years': ['view', 'create', 'edit', 'close', 'reopen'],
            'ar_invoices': ['view', 'create', 'edit', 'delete', 'post'],
            'ar_receipts': ['view', 'create', 'edit', 'delete', 'post'],
            'ar_credit_notes': ['view', 'create', 'edit', 'delete', 'post'],
            'ar': ['view', 'manage'],
            'ap_bills': ['view', 'create', 'edit', 'delete', 'post'],
            'ap_payments': ['view', 'create', 'edit', 'delete', 'post'],
            'ap_debit_notes': ['view', 'create', 'edit', 'delete', 'post'],
            'ap': ['view', 'manage'],
            'assets': ['view', 'create', 'edit', 'delete', 'transfer', 'dispose'],
            'depreciation': ['view', 'create', 'post', 'reverse'],
            'cost_centers': ['view', 'create', 'edit', 'delete'],
            'profit_centers': ['view', 'create', 'edit', 'delete'],
            'cost_allocation': ['view', 'create', 'edit', 'delete'],
            'budgets': ['view', 'create', 'edit', 'delete', 'approve'],
            'tax': ['view', 'create', 'edit'],
            'tax_rules': ['view', 'create', 'edit', 'delete'],
            'bank_accounts': ['view', 'create', 'edit', 'delete'],
            'transfers': ['view', 'create', 'edit', 'delete'],
            'reconciliation': ['view', 'create', 'edit'],
            'treasury': ['view', 'manage'],
            'close': ['view', 'manage', 'close', 'reopen'],
            'audit': ['view', 'export'],
            'flow': ['view', 'send', 'manage'],
            'intercompany': ['view', 'create', 'edit', 'delete'],
            'journal_templates': ['view', 'create', 'edit', 'delete'],
            'journal_batches': ['view', 'create', 'edit', 'delete', 'post'],
            'approvals': ['view', 'approve', 'reject'],
            'reports': ['view', 'export'],
            'settings': ['view', 'edit'],
        }
    },
    'platform': {
        'label': 'Platform Administration',
        'resources': {
            'users': ['view', 'create', 'edit', 'delete', 'reset_password'],
            'roles': ['view', 'create', 'edit', 'delete'],
            'permissions': ['view', 'manage'],
            'audit_log': ['view', 'export'],
            'settings': ['view', 'edit'],
            'notifications': ['view', 'create', 'edit', 'delete', 'manage'],
        }
    },
    'hr': {
        'label': 'Human Resources',
        'resources': {
            'dashboard': ['view'],
            'employees': ['view', 'create', 'edit', 'delete'],
            'departments': ['view', 'create', 'edit', 'delete'],
            'positions': ['view', 'create', 'edit', 'delete'],
            'attendance': ['view', 'create', 'edit', 'delete', 'approve'],
            'leave': ['view', 'create', 'edit', 'delete', 'approve'],
            'payroll': ['view', 'create', 'edit', 'delete', 'approve'],
            'overtime': ['view', 'create', 'edit', 'delete', 'approve'],
            'loans': ['view', 'create', 'edit', 'delete', 'approve'],
            'documents': ['view', 'upload', 'download', 'delete'],
            'announcements': ['view', 'create', 'edit', 'delete'],
            'recruitment': ['view', 'create', 'edit', 'delete', 'approve'],
            'performance': ['view', 'create', 'edit', 'delete'],
            'reports': ['view', 'export'],
            'settings': ['view', 'edit'],
        }
    },
    'payroll': {
        'label': 'Enterprise Payroll',
        'resources': {
            # Dashboard & Overview
            'dashboard': ['view'],
            'executive_dashboard': ['view'],
            'processing_dashboard': ['view'],
            'variance_dashboard': ['view'],
            'overtime_dashboard': ['view'],
            'loan_dashboard': ['view'],
            'compliance_dashboard': ['view'],
            # Setup
            'setup': ['view', 'edit'],
            'components': ['view', 'create', 'edit', 'delete'],
            'groups': ['view', 'create', 'edit', 'delete'],
            'profiles': ['view', 'create', 'edit', 'delete'],
            'calendar': ['view', 'create', 'edit', 'delete'],
            # Periods
            'periods': ['view', 'create', 'edit', 'delete', 'lock', 'unlock', 'close'],
            # Processing
            'processing': ['view', 'create', 'calculate', 'validate'],
            'runs': ['view', 'create', 'edit', 'delete'],
            'add_employees': ['add_employees'],
            # Review & Approval
            'review': ['view', 'approve', 'reject', 'return'],
            'approval': ['view', 'approve', 'reject'],
            # Payslips
            'payslips': ['view', 'generate', 'approve', 'release'],
            'payslip_download': ['download'],
            'payslip_email': ['email'],
            # Loans & Advances
            'loans': ['view', 'create', 'edit', 'delete', 'approve', 'suspend'],
            'advances': ['view', 'create', 'edit', 'delete', 'approve'],
            # Retro & Arrears
            'retro': ['view', 'create', 'edit', 'delete', 'approve'],
            'arrears': ['view', 'create', 'edit', 'delete', 'approve'],
            # Compliance & Controls
            'compliance': ['view', 'create', 'edit', 'delete', 'audit'],
            'exceptions': ['view', 'resolve', 'ignore', 'escalate'],
            'audit': ['view', 'export'],
            'controls': ['view', 'create', 'edit', 'delete'],
            # Finance Integration
            'finance': ['view', 'create', 'post', 'approve', 'reject'],
            'posting': ['view', 'create', 'post'],
            # HR Integration
            'hr_integration': ['view', 'manage'],
            # Reports
            'reports': ['view', 'export', 'create', 'edit', 'delete'],
            'summary_report': ['view', 'export'],
            'earnings_report': ['view', 'export'],
            'deductions_report': ['view', 'export'],
            'overtime_report': ['view', 'export'],
            'loan_report': ['view', 'export'],
            'variance_report': ['view', 'export'],
            'compliance_report': ['view', 'export'],
            'audit_report': ['view', 'export'],
            'export': ['view', 'export', 'configure', 'delete'],
            # Workflow
            'approvals': ['view', 'approve', 'reject', 'delegate'],
            'approval_rules': ['view', 'create', 'edit', 'delete'],
            'delegations': ['view', 'create', 'edit', 'delete'],
            'sla': ['view', 'create', 'edit', 'delete'],
            'escalations': ['view', 'manage'],
            # Settings
            'settings': ['view', 'edit'],
            'notification_settings': ['view', 'edit'],
            'integration_settings': ['view', 'edit'],
            # Special permissions
            'lock': ['lock'],
            'unlock': ['unlock'],
            'close': ['close'],
            'recalculate': ['recalculate'],
            'bulk_approve': ['bulk_approve'],
            'sensitive_data': ['view'],  # For salary totals, bank details
            'export_bank_file': ['export'],
            'view_audit_trail': ['view'],
        }
    },
    'wms': {
        'label': 'Warehouse Management',
        'resources': {
            'dashboard': ['view'],
            'inventory': ['view', 'create', 'edit', 'delete', 'adjust'],
            'items': ['view', 'create', 'edit', 'delete', 'import', 'export'],
            'locations': ['view', 'create', 'edit', 'delete'],
            'warehouses': ['view', 'create', 'edit', 'delete'],
            'stock_movements': ['view', 'create', 'transfer'],
            'stock_count': ['view', 'create', 'edit', 'approve'],
            'receipts': ['view', 'create', 'edit', 'receive', 'approve'],
            'shipments': ['view', 'create', 'edit', 'pick', 'pack', 'ship', 'approve'],
            'returns': ['view', 'create', 'edit', 'approve'],
            'transfers': ['view', 'create', 'edit', 'approve', 'execute'],
            'adjustments': ['view', 'create', 'edit', 'approve'],
            'reports': ['view', 'export'],
            'settings': ['view', 'edit'],
        }
    },
    'logistics': {
        'label': 'Logistics & Delivery',
        'resources': {
            'dashboard': ['view'],
            'trips': ['view', 'create', 'edit', 'delete', 'start', 'complete', 'cancel', 'assign'],
            'routes': ['view', 'create', 'edit', 'delete', 'optimize'],
            'dispatch': ['view', 'create', 'edit', 'assign', 'execute', 'reassign'],
            'vehicles': ['view', 'create', 'edit', 'delete', 'assign', 'maintenance'],
            'drivers': ['view', 'create', 'edit', 'delete', 'assign', 'availability'],
            'stops': ['view', 'create', 'edit', 'delete', 'checkin', 'complete'],
            'delivery_reports': ['view', 'export'],
            'alerts': ['view', 'create', 'edit', 'delete', 'resolve'],
            'settings': ['view', 'edit'],
            'audit_logs': ['view', 'export'],
            'costs': ['view', 'create', 'edit', 'approve'],
            'pod': ['view', 'create', 'edit', 'approve', 'reject'],
            'flow_integration': ['view', 'create', 'edit', 'delete', 'publish'],
            'tms_admin': ['view', 'create', 'edit', 'delete'],
        }
    },
    'tms': {
        'label': 'TMS - Transport Management',
        'resources': {
            'dashboard': ['view'],
            'trips': ['view', 'create', 'edit', 'delete', 'start', 'complete', 'cancel', 'assign'],
            'routes': ['view', 'create', 'edit', 'delete', 'optimize'],
            'dispatch_board': ['view', 'create', 'edit', 'assign', 'execute', 'reassign'],
            'vehicles': ['view', 'create', 'edit', 'delete', 'assign', 'maintenance'],
            'drivers': ['view', 'create', 'edit', 'delete', 'assign', 'availability'],
            'stops': ['view', 'create', 'edit', 'delete', 'checkin', 'complete'],
            'shipments': ['view', 'create', 'edit', 'delete'],
            'pod': ['view', 'create', 'edit', 'approve', 'reject'],
            'incidents': ['view', 'create', 'edit', 'resolve'],
            'costs': ['view', 'create', 'edit', 'approve', 'view_sensitive'],
            'reports': ['view', 'export'],
            'settings': ['view', 'edit'],
            'audit_logs': ['view', 'export'],
            'notifications': ['view', 'create', 'edit', 'delete', 'manage'],
            'flow_integration': ['view', 'create', 'edit', 'delete', 'publish'],
        }
    },
    'scm': {
        'label': 'Supply Chain Management',
        'resources': {
            'dashboard': ['view'],
            'demand': ['view', 'create', 'edit', 'delete', 'approve', 'override'],
            'supply': ['view', 'create', 'edit', 'delete'],
            'replenishment': ['view', 'create', 'edit', 'delete', 'approve', 'execute'],
            'mrp': ['view', 'create', 'edit', 'delete', 'approve', 'execute'],
            'inventory': ['view', 'create', 'edit', 'delete'],
            'network': ['view', 'create', 'edit', 'delete'],
            'service': ['view', 'create', 'edit', 'delete'],
            'scenarios': ['view', 'create', 'edit', 'delete', 'approve', 'run'],
            'alerts': ['view', 'create', 'edit', 'delete', 'resolve', 'acknowledge'],
            'supplier': ['view', 'create', 'edit', 'delete'],
            'warehouse': ['view', 'create', 'edit', 'delete'],
            'workflow': ['view', 'create', 'edit', 'delete', 'approve'],
            'reports': ['view', 'export', 'create', 'edit', 'delete'],
            'settings': ['view', 'edit'],
        }
    },
    'planning': {
        'label': 'Demand & Inventory Planning',
        'resources': {
            'dashboard': ['view'],
            'forecasts': ['view', 'create', 'edit', 'delete', 'approve', 'override'],
            'demand': ['view', 'create', 'edit', 'delete'],
            'replenishment': ['view', 'create', 'edit', 'delete', 'approve', 'execute'],
            'policies': ['view', 'create', 'edit', 'delete'],
            'scenarios': ['view', 'create', 'edit', 'delete', 'approve', 'run'],
            'alerts': ['view', 'create', 'edit', 'delete', 'resolve', 'acknowledge', 'escalate'],
            'reports': ['view', 'export', 'create', 'edit', 'delete'],
            'settings': ['view', 'edit'],
            # Enterprise Demand Planning
            'control_tower': ['view'],
            'statistical_forecasting': ['view', 'create', 'edit', 'delete', 'run'],
            'forecast_versions': ['view', 'create', 'edit', 'delete', 'freeze', 'publish', 'clone', 'compare'],
            'forecast_overrides': ['view', 'create', 'edit', 'delete', 'approve', 'reject', 'bulk_override'],
            'demand_drivers': ['view', 'create', 'edit', 'delete'],
            'promotions': ['view', 'create', 'edit', 'delete'],
            'seasonality': ['view', 'create', 'edit', 'delete'],
            'consensus': ['view', 'create', 'edit', 'delete', 'approve', 'input'],
            'forecast_accuracy': ['view', 'create', 'calculate'],
            'demand_sensing': ['view', 'create', 'detect', 'acknowledge'],
            'scenario_planning': ['view', 'create', 'edit', 'delete', 'run', 'compare'],
            'workflow': ['view', 'create', 'edit', 'delete', 'approve', 'reject'],
            'supply_linkage': ['view'],
            'sales_linkage': ['view'],
            'branch_entity': ['view', 'create', 'edit', 'delete'],
            'export': ['view', 'export', 'configure'],
        }
    },
    'crm': {
        'label': 'Customer Relationship',
        'resources': {
            'dashboard': ['view'],
            'customers': ['view', 'create', 'edit', 'delete', 'merge', 'export'],
            'contacts': ['view', 'create', 'edit', 'delete'],
            'activities': ['view', 'create', 'edit', 'delete'],
            'tasks': ['view', 'create', 'edit', 'delete'],
            'opportunities': ['view', 'create', 'edit', 'delete', 'win', 'lose'],
            'reports': ['view', 'export'],
            'settings': ['view', 'edit'],
        }
    },
    'sales': {
        'label': 'Sales & Orders',
        'resources': {
            'dashboard': ['view'],
            'customers': ['view', 'create', 'edit', 'delete', 'export'],
            'inquiries': ['view', 'create', 'edit', 'delete', 'convert'],
            'opportunities': ['view', 'create', 'edit', 'delete', 'win', 'lose'],
            'pricing': ['view', 'create', 'edit', 'approve'],
            'quotations': ['view', 'create', 'edit', 'delete', 'approve', 'send'],
            'orders': ['view', 'create', 'edit', 'delete', 'approve', 'fulfill'],
            'reservations': ['view', 'create', 'edit', 'delete', 'approve', 'release'],
            'deliveries': ['view', 'create', 'edit', 'delete', 'dispatch'],
            'returns': ['view', 'create', 'edit', 'delete', 'approve'],
            'targets': ['view', 'create', 'edit', 'delete'],
            'contracts': ['view', 'create', 'edit', 'delete'],
            'activities': ['view', 'create', 'edit', 'delete'],
            'invoices': ['view', 'create', 'edit', 'delete', 'approve', 'send'],
            'sales_reports': ['view', 'export'],
            'settings': ['view', 'edit'],
        }
    },
    'marketing': {
        'label': 'Marketing',
        'resources': {
            'dashboard': ['view'],
            'campaigns': ['view', 'create', 'edit', 'delete', 'approve', 'launch'],
            'leads': ['view', 'create', 'edit', 'delete', 'convert', 'assign'],
            'channels': ['view', 'create', 'edit', 'delete'],
            'content': ['view', 'create', 'edit', 'delete', 'approve', 'publish'],
            'advertisements': ['view', 'create', 'edit', 'delete', 'approve'],
            'offers': ['view', 'create', 'edit', 'delete', 'approve', 'send'],
            'budgets': ['view', 'create', 'edit', 'delete', 'approve'],
            'reports': ['view', 'export'],
            'settings': ['view', 'edit'],
        }
    },
    'customer_intelligence': {
        'label': 'Customer Intelligence',
        'resources': {
            'dashboard': ['view'],
            'profiles': ['view', 'create', 'edit', 'delete', 'merge'],
            'segments': ['view', 'create', 'edit', 'delete', 'assign'],
            'forecasts': ['view', 'create', 'edit', 'delete', 'approve'],
            'alerts': ['view', 'create', 'edit', 'delete', 'resolve'],
            'recommendations': ['view', 'create', 'edit', 'delete', 'approve', 'execute'],
            'reports': ['view', 'export'],
            'settings': ['view', 'edit'],
        }
    },
    'tasks': {
        'label': 'Task Management',
        'resources': {
            'dashboard': ['view'],
            'tasks': ['view', 'create', 'edit', 'delete', 'assign', 'complete'],
            'subtasks': ['view', 'create', 'edit', 'delete', 'complete'],
            'transactions': ['view', 'create', 'edit', 'delete'],
            'reports': ['view', 'export'],
            'settings': ['view', 'edit'],
        }
    },
    'quicktools': {
        'label': 'Quick Tools',
        'resources': {
            'tools': ['view', 'use'],
            'notes': ['view', 'create', 'edit', 'delete'],
            'reminders': ['view', 'create', 'edit', 'delete'],
            'favorites': ['view', 'create', 'edit', 'delete'],
            'calculator': ['view', 'use'],
            'settings': ['view', 'edit'],
        }
    },
    'procurement': {
        'label': 'Procurement & Purchasing',
        'resources': {
            'dashboard': ['view'],
            'suppliers': ['view', 'create', 'edit', 'delete'],
            'requisitions': ['view', 'create', 'edit', 'delete', 'approve', 'convert'],
            'rfqs': ['view', 'create', 'edit', 'delete', 'send'],
            'quotations': ['view', 'create', 'edit', 'delete', 'compare', 'approve'],
            'orders': ['view', 'create', 'edit', 'delete', 'approve', 'close', 'cancel'],
            'shipments': ['view', 'create', 'edit', 'track'],
            'receiving': ['view', 'create', 'edit', 'receive'],
            'local': ['view', 'create', 'edit'],
            'import': ['view', 'create', 'edit'],
            'claims': ['view', 'create', 'edit', 'delete', 'resolve'],
            'returns': ['view', 'create', 'edit', 'delete'],
            'contracts': ['view', 'create', 'edit', 'delete'],
            'performance': ['view', 'export'],
            'reports': ['view', 'export'],
            'settings': ['view', 'edit'],
        }
    },
    'reports': {
        'label': 'Reporting & BI',
        'resources': {
            'dashboard': ['view', 'export'],
            'executive': ['view', 'export'],
            'operational': ['view', 'export'],
            'financial': ['view', 'export'],
            'sales': ['view', 'export'],
            'inventory': ['view', 'export'],
            'logistics': ['view', 'export'],
            'procurement': ['view', 'export'],
            'hr': ['view', 'export'],
            'marketing': ['view', 'export'],
            'custom': ['view', 'create', 'edit', 'delete', 'export'],
            'scheduled': ['view', 'create', 'edit', 'delete', 'execute'],
            'adhoc': ['view', 'create', 'edit', 'delete', 'execute'],
            'datasets': ['view', 'create', 'edit', 'delete'],
            'kpis': ['view', 'create', 'edit', 'delete', 'approve'],
            'drilldown': ['view', 'execute'],
            'settings': ['view', 'edit'],
            'audit_logs': ['view', 'export'],
        }
    },
    'ecommerce': {
        'label': 'E-commerce Integration',
        'resources': {
            'dashboard': ['view'],
            'channels': ['view', 'create', 'edit', 'delete', 'connect', 'disconnect'],
            'orders': ['view', 'create', 'edit', 'delete', 'import', 'export', 'retry', 'approve'],
            'inventory': ['view', 'create', 'edit', 'delete', 'sync', 'export'],
            'customers': ['view', 'create', 'edit', 'delete', 'sync', 'merge', 'export'],
            'mappings': ['view', 'create', 'edit', 'delete'],
            'exceptions': ['view', 'create', 'edit', 'delete', 'resolve', 'approve', 'export'],
            'reports': ['view', 'export'],
            'settings': ['view', 'edit'],
            'audit_logs': ['view', 'export'],
            'sync': ['view', 'create', 'edit', 'delete', 'execute', 'cancel'],
        }
    },
    'documents': {
        'label': 'Document Management',
        'resources': {
            'dashboard': ['view'],
            'files': ['view', 'upload', 'download', 'edit', 'delete', 'share', 'archive'],
            'versions': ['view', 'create', 'edit', 'delete', 'publish', 'restore'],
            'templates': ['view', 'create', 'edit', 'delete', 'generate', 'preview'],
            'signatures': ['view', 'create', 'sign', 'reject', 'cancel', 'request'],
            'categories': ['view', 'create', 'edit', 'delete', 'manage'],
            'tags': ['view', 'create', 'edit', 'delete', 'manage'],
            'links': ['view', 'create', 'edit', 'delete', 'manage'],
            'shares': ['view', 'create', 'edit', 'delete', 'revoke', 'manage'],
            'reports': ['view', 'export', 'generate'],
            'settings': ['view', 'edit', 'manage'],
            'audit_logs': ['view', 'export'],
            'retention': ['view', 'create', 'edit', 'delete', 'manage'],
            'access_control': ['view', 'create', 'edit', 'delete', 'manage'],
            'checkin_checkout': ['view', 'create', 'edit', 'delete', 'manage'],
            'linked_records': ['view', 'create', 'edit', 'delete', 'manage'],
        }
    },
    'quality': {
        'label': 'Quality Management',
        'resources': {
            # Main areas
            'dashboard': ['view'],
            'executive_dashboard': ['view'],
            'workspace': ['view'],
            # Inspections
            'inspections': ['view', 'create', 'edit', 'delete', 'approve', 'execute', 'hold_release'],
            'inspection_plans': ['view', 'create', 'edit', 'delete', 'approve', 'execute'],
            'inspection_templates': ['view', 'create', 'edit', 'delete', 'manage'],
            'inspection_results': ['view', 'create', 'edit', 'delete'],
            're_inspection': ['view', 'create', 'execute'],
            # NCR / Non-Conformance
            'ncr': ['view', 'create', 'edit', 'delete', 'approve', 'resolve', 'close', 'escalate'],
            'ncr_containment': ['view', 'create', 'edit', 'delete', 'verify'],
            'ncr_disposition': ['view', 'create', 'edit', 'approve', 'execute'],
            # CAPA
            'capa': ['view', 'create', 'edit', 'delete', 'approve', 'verify', 'close', 'reopen'],
            'capa_actions': ['view', 'create', 'edit', 'delete', 'complete', 'verify'],
            'capa_effectiveness': ['view', 'create', 'edit', 'approve', 'close'],
            # Audits
            'audits': ['view', 'create', 'edit', 'delete', 'approve', 'execute', 'close', 'cancel'],
            'audit_programs': ['view', 'create', 'edit', 'delete', 'manage'],
            'audit_checklists': ['view', 'create', 'edit', 'delete', 'manage'],
            'audit_findings': ['view', 'create', 'edit', 'delete', 'verify', 'close'],
            'audit_finding_actions': ['view', 'create', 'edit', 'delete', 'complete'],
            # Supplier Quality
            'supplier_quality': ['view', 'create', 'edit', 'approve', 'block', 'unblock'],
            'supplier_scorecards': ['view', 'create', 'edit', 'delete', 'export'],
            'supplier_ncr': ['view', 'create', 'edit', 'resolve'],
            'supplier_capa': ['view', 'create', 'edit', 'resolve'],
            # Quality Holds & Disposition
            'quality_holds': ['view', 'create', 'release', 'reject', 'rework', 'scrap'],
            'disposition': ['view', 'create', 'edit', 'approve', 'execute'],
            'quarantine': ['view', 'create', 'edit', 'release', 'approve'],
            # Defects & Scrap
            'defects': ['view', 'create', 'edit', 'analyze', 'export'],
            'scrap': ['view', 'create', 'edit', 'approve', 'export'],
            'rework': ['view', 'create', 'edit', 'approve', 'complete'],
            'cost_of_quality': ['view', 'export', 'analyze'],
            # SPC & Analytics
            'spc': ['view', 'create', 'edit', 'configure', 'export'],
            'control_charts': ['view', 'create', 'edit', 'delete', 'configure'],
            'quality_trends': ['view', 'export', 'analyze'],
            'anomaly_review': ['view', 'create', 'edit', 'resolve', 'export'],
            # Documents & Compliance
            'quality_documents': ['view', 'create', 'edit', 'delete', 'approve', 'publish'],
            'controlled_docs': ['view', 'create', 'edit', 'delete', 'approve', 'release'],
            'compliance': ['view', 'create', 'edit', 'approve', 'export', 'manage'],
            'certifications': ['view', 'create', 'edit', 'delete', 'approve', 'manage'],
            # Risk Management
            'quality_risks': ['view', 'create', 'edit', 'mitigate', 'close', 'manage'],
            'risk_assessment': ['view', 'create', 'edit', 'approve', 'manage'],
            'critical_control_points': ['view', 'create', 'edit', 'delete', 'manage'],
            'escalation_rules': ['view', 'create', 'edit', 'delete', 'manage'],
            # Workflow & Approvals
            'approvals': ['view', 'approve', 'reject', 'delegate', 'escalate'],
            'approval_matrix': ['view', 'create', 'edit', 'delete', 'manage'],
            'sla_policies': ['view', 'create', 'edit', 'delete', 'manage'],
            # Settings & Configuration
            'settings': ['view', 'edit', 'manage'],
            'inspection_settings': ['view', 'edit', 'manage'],
            'ncr_settings': ['view', 'edit', 'manage'],
            'capa_settings': ['view', 'edit', 'manage'],
            'audit_settings': ['view', 'edit', 'manage'],
            'supplier_quality_settings': ['view', 'edit', 'manage'],
            'compliance_settings': ['view', 'edit', 'manage'],
            'notification_settings': ['view', 'edit', 'manage'],
            # Reports & Analytics
            'reports': ['view', 'export', 'generate', 'schedule'],
            'inspection_reports': ['view', 'export'],
            'ncr_reports': ['view', 'export'],
            'capa_reports': ['view', 'export'],
            'audit_reports': ['view', 'export'],
            'supplier_quality_reports': ['view', 'export'],
            'defect_reports': ['view', 'export'],
            'compliance_reports': ['view', 'export'],
            'custom_reports': ['view', 'create', 'edit', 'delete', 'export', 'generate'],
            'export_center': ['view', 'create', 'edit', 'delete', 'export', 'manage'],
            # Audit Trail
            'audit_log': ['view', 'export'],
            # Quality Planning
            'quality_plans': ['view', 'create', 'edit', 'delete', 'approve', 'execute'],
            'sampling_rules': ['view', 'create', 'edit', 'delete', 'manage'],
            'test_methods': ['view', 'create', 'edit', 'delete', 'manage'],
            'specifications': ['view', 'create', 'edit', 'delete', 'manage', 'approve'],
            # Generic fallback
            'quality': ['view', 'create', 'edit', 'delete', 'approve', 'execute', 'verify', 'export', 'manage'],
        }
    },
    'spc': {
        'label': 'SPC / Quality Analytics',
        'resources': {
            # SPC Core
            'dashboard': ['view'],
            'charts': ['view', 'create', 'edit', 'delete', 'manage'],
            'measurements': ['view', 'create', 'edit', 'delete'],
            'capability': ['view', 'create', 'edit', 'delete', 'analyze'],
            'sampling': ['view', 'create', 'edit', 'delete', 'manage'],
            'alerts': ['view', 'create', 'edit', 'delete', 'acknowledge', 'resolve'],
            # Equipment
            'equipment': ['view', 'create', 'edit', 'delete', 'manage'],
            'calibration': ['view', 'create', 'edit', 'delete', 'manage'],
            'gage_rr': ['view', 'create', 'edit', 'delete', 'manage'],
            # Analytics
            'analytics': ['view', 'export', 'analyze'],
            'reports': ['view', 'export'],
            # Settings
            'settings': ['view', 'edit', 'manage'],
            # Generic fallback
            'spc': ['view', 'create', 'edit', 'delete', 'manage', 'export', 'analyze'],
        }
    },
    'workflow': {
        'label': 'Workflow & BPM',
        'resources': {
            'dashboard': ['view'],
            'my_work': ['view', 'edit', 'complete'],
            'approvals': ['view', 'approve', 'reject', 'return', 'escalate'],
            'delegation': ['view', 'create', 'edit', 'delete', 'manage'],
            'designer': ['view', 'create', 'edit', 'delete', 'activate', 'deactivate'],
            'processes': ['view', 'create', 'edit', 'delete'],
            'instances': ['view', 'create', 'edit', 'delete', 'cancel', 'reassign'],
            'automation': ['view', 'create', 'edit', 'delete', 'activate', 'deactivate', 'manage', 'test'],
            'notifications': ['view', 'create', 'edit', 'delete', 'manage'],
            'monitoring': ['view', 'manage'],
            'reports': ['view', 'export', 'generate'],
            'settings': ['view', 'create', 'edit', 'delete', 'manage'],
            'audit': ['view', 'export'],
            'templates': ['view', 'create', 'edit', 'delete', 'clone'],
            'escalation': ['view', 'create', 'edit', 'delete', 'manage'],
        }
    },
    'org_planning': {
        'label': 'Organizational Planning & BPM',
        'resources': {
            'dashboard': ['view'],
            'structure': ['view', 'create', 'edit', 'delete', 'manage'],
            'companies': ['view', 'create', 'edit', 'delete'],
            'positions': ['view', 'create', 'edit', 'delete', 'assign'],
            'headcount': ['view', 'create', 'edit', 'delete', 'approve'],
            'delegations': ['view', 'create', 'edit', 'delete', 'approve'],
            'approval_matrix': ['view', 'create', 'edit', 'delete', 'approve'],
            'workflows': ['view', 'create', 'edit', 'delete', 'activate', 'publish'],
            'processes': ['view', 'create', 'edit', 'delete', 'cancel', 'reassign'],
            'instances': ['view', 'create', 'edit', 'delete', 'approve', 'reject'],
            'sla': ['view', 'create', 'edit', 'delete', 'manage'],
            'escalations': ['view', 'create', 'edit', 'delete', 'manage'],
            'automation': ['view', 'create', 'edit', 'delete', 'activate', 'test', 'manage'],
            'simulations': ['view', 'create', 'edit', 'delete', 'approve', 'publish'],
            'monitoring': ['view', 'manage'],
            'reports': ['view', 'export', 'generate'],
            'settings': ['view', 'create', 'edit', 'delete', 'manage'],
            'audit': ['view', 'export'],
        }
    },
    'forms': {
        'label': 'Form Builder',
        'resources': {
            'templates': ['view', 'create', 'edit', 'delete', 'publish', 'archive', 'duplicate'],
            'submissions': ['view', 'create', 'edit', 'delete', 'submit', 'approve', 'reject', 'return', 'cancel'],
            'drafts': ['view', 'edit', 'delete'],
            'approvals': ['view', 'approve', 'reject', 'return'],
            'workflows': ['view', 'create', 'edit', 'delete', 'activate', 'deactivate'],
            'reports': ['view', 'export'],
            'settings': ['view', 'edit'],
            'signatures': ['view', 'create', 'sign'],
            'attachments': ['view', 'upload', 'download', 'delete'],
            'comments': ['view', 'create', 'edit', 'delete'],
            'audit': ['view', 'export'],
        }
    },
    'feedback': {
        'label': 'Feedback & Reporting',
        'resources': {
            'dashboard': ['view'],
            'reports': ['view', 'create', 'edit', 'delete', 'manage', 'assign'],
            'my_reports': ['view', 'create', 'edit'],
            'assigned_reports': ['view', 'edit'],
            'attachments': ['view', 'upload', 'download', 'delete'],
            'comments': ['view', 'create', 'edit', 'delete'],
            'view_internal': ['view'],
            'analytics': ['view', 'export'],
            'settings': ['view', 'edit'],
            'categories': ['view', 'create', 'edit', 'delete'],
            'audit': ['view', 'export'],
        }
    },
    'flow': {
        'label': 'Flow - Communication',
        'resources': {
            'dashboard': ['view'],
            'chats': ['view', 'send', 'edit', 'delete'],
            'channels': ['view', 'create', 'join', 'leave', 'manage', 'admin'],
            'groups': ['view', 'create', 'join', 'leave', 'manage', 'admin'],
            'messages': ['view', 'send', 'edit', 'delete', 'pin'],
            'files': ['upload', 'download', 'delete'],
            'calls': ['initiate', 'join', 'manage'],
            'meetings': ['create', 'join', 'host', 'manage'],
            'notifications': ['view', 'manage'],
            'reminders': ['view', 'create', 'complete', 'dismiss'],
            'saved_messages': ['view', 'save', 'unsave'],
            'settings': ['view', 'edit'],
            'users': ['view', 'block', 'unblock'],
            'profile': ['view', 'edit'],
            'status': ['view', 'set'],
            'search': ['view'],
            'shared_media': ['view', 'upload'],
        }
    },
    'api_gateway': {
        'label': 'API Gateway',
        'resources': {
            'dashboard': ['view'],
            'clients': ['view', 'create', 'edit', 'delete', 'approve'],
            'scopes': ['view', 'create', 'edit', 'delete'],
            'policies': ['view', 'create', 'edit', 'delete'],
            'routes': ['view', 'create', 'edit', 'delete'],
            'api_versions': ['view', 'create', 'edit', 'delete'],
            'request_logs': ['view', 'export'],
            'webhooks': ['view', 'create', 'edit', 'delete', 'subscribe'],
            'subscriptions': ['view', 'create', 'edit', 'delete'],
            'integrations': ['view', 'create', 'edit', 'delete', 'sync'],
            'sync_jobs': ['view', 'create', 'edit', 'delete', 'execute'],
            'monitoring': ['view', 'manage'],
            'rate_limits': ['view', 'create', 'edit', 'delete'],
            'health_status': ['view'],
            'reports': ['view', 'export'],
            'documentation': ['view'],
            'audit_logs': ['view', 'export'],
            'settings': ['view', 'edit'],
        }
    },
    'bi': {
        'label': 'Business Intelligence',
        'resources': {
            'dashboard': ['view'],
            'executive': ['view', 'export'],
            'holding_view': ['view', 'export'],
            'company_comparison': ['view', 'export'],
            'operational': ['view', 'export'],
            'kpis': ['view', 'create', 'edit', 'delete'],
            'drilldown': ['view', 'execute'],
            'alerts': ['view', 'create', 'edit', 'delete', 'resolve'],
            'reports': ['view', 'export', 'generate'],
            'settings': ['view', 'edit'],
        }
    },
    'bi_advanced': {
        'label': 'Advanced Analytics',
        'resources': {
            'dashboard': ['view'],
            'datasets': ['view', 'create', 'edit', 'delete', 'import', 'export'],
            'adhoc_queries': ['view', 'create', 'edit', 'delete', 'execute'],
            'reports': ['view', 'create', 'edit', 'delete', 'export'],
            'scheduled_reports': ['view', 'create', 'edit', 'delete', 'execute'],
            'kpis': ['view', 'create', 'edit', 'delete', 'approve'],
            'drilldown': ['view', 'execute'],
            'monitoring': ['view', 'manage'],
            'access_logs': ['view', 'export'],
            'performance_logs': ['view', 'export'],
            'delivery_logs': ['view', 'export'],
            'settings': ['view', 'edit'],
        }
    },
    'social_media': {
        'label': 'Social Media',
        'resources': {
            'dashboard': ['view'],
            'accounts': ['view', 'create', 'edit', 'delete', 'connect', 'disconnect'],
            'content': ['view', 'create', 'edit', 'delete', 'publish', 'archive'],
            'calendar': ['view', 'create', 'edit', 'delete'],
            'publishing': ['view', 'create', 'edit', 'delete', 'publish', 'schedule'],
            'queue': ['view', 'create', 'edit', 'delete'],
            'engagement': ['view', 'manage'],
            'messages': ['view', 'create', 'edit', 'delete'],
            'saved_replies': ['view', 'create', 'edit', 'delete'],
            'leads': ['view', 'create', 'edit', 'delete', 'convert'],
            'campaigns': ['view', 'create', 'edit', 'delete', 'approve', 'launch'],
            'advertisements': ['view', 'create', 'edit', 'delete', 'approve'],
            'monitoring': ['view', 'manage'],
            'reports': ['view', 'export'],
            'settings': ['view', 'edit'],
        }
    },
}

# All possible action types
ALL_ACTIONS = ['view', 'create', 'edit', 'delete', 'approve', 'execute',
                'upload', 'download', 'import', 'export', 'assign',
                'reset_password', 'merge', 'send', 'publish', 'launch',
                'receive', 'pick', 'pack', 'ship', 'transfer', 'adjust',
                'resolve', 'start', 'complete', 'optimize', 'override',
                'convert', 'win', 'lose', 'manage', 'set_password']


# ============================================================================
# ROLE MANAGEMENT
# ============================================================================

def get_all_roles():
    """Get all roles with their permissions."""
    roles = get_all("SELECT * FROM roles ORDER BY role_name")
    for role in roles:
        role['permissions'] = get_role_permissions(role['id'])
    return roles


def get_role_by_id(role_id):
    """Get a single role by ID."""
    role = get_one("SELECT * FROM roles WHERE id = ?", (role_id,))
    if role:
        role['permissions'] = get_role_permissions(role_id)
    return role


def get_role_permissions(role_id: int) -> Set[str]:
    """
    Get all permission strings for a role.
    
    Returns a set of strings like 'hr.employees.view', 'wms.inventory.edit'
    """
    permissions = set()
    
    with get_db_context() as db:
        rows = db.execute("""
            SELECT module, resource, action FROM role_permissions
            WHERE role_id = ?
        """, (role_id,)).fetchall()
        
        for row in rows:
            permissions.add(f"{row['module']}.{row['resource']}.{row['action']}")
        
        # Check for wildcard permissions (module-level or resource-level)
        wildcards = db.execute("""
            SELECT module, resource FROM role_permissions
            WHERE role_id = ? AND action = '*'
        """, (role_id,)).fetchall()
        
        for wc in wildcards:
            mod = wc['module']
            res = wc['resource']
            if res == '*':
                # Full module access
                if mod in MODULE_PERMISSIONS:
                    for resource, actions in MODULE_PERMISSIONS[mod]['resources'].items():
                        for action in actions:
                            permissions.add(f"{mod}.{resource}.{action}")
            elif mod == '*':
                # Wildcard module - should not happen normally
                pass
            else:
                # Specific resource, all actions
                if mod in MODULE_PERMISSIONS and res in MODULE_PERMISSIONS[mod]['resources']:
                    for action in MODULE_PERMISSIONS[mod]['resources'][res]:
                        permissions.add(f"{mod}.{res}.{action}")
    
    return permissions


def get_user_permissions(user_id: int) -> Set[str]:
    """
    Get all effective permissions for a user (from their role).
    """
    with get_db_context() as db:
        user = db.execute("SELECT role_id FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user or not user['role_id']:
            return set()
        return get_role_permissions(user['role_id'])


def user_has_permission(user_id: int, module: str, resource: str, action: str) -> bool:
    """
    Check if a user has a specific permission.
    
    Args:
        user_id: User ID
        module: Module name (e.g., 'hr', 'wms')
        resource: Resource name (e.g., 'employees', 'inventory')
        action: Action name (e.g., 'view', 'edit')
    
    Returns:
        True if user has the permission, False otherwise
    """
    permissions = get_user_permissions(user_id)
    perm_string = f"{module}.{resource}.{action}"
    
    # Direct match
    if perm_string in permissions:
        return True
    
    # Check for resource-level wildcard (e.g., 'hr.employees.*')
    resource_wildcard = f"{module}.{resource}.*"
    if resource_wildcard in permissions:
        return True
    
    # Check for module-level wildcard (e.g., 'hr.*')
    module_wildcard = f"{module}.*"
    if module_wildcard in permissions:
        # Need to verify the action exists in that module's resources
        if module in MODULE_PERMISSIONS:
            if resource in MODULE_PERMISSIONS[module]['resources']:
                if action in MODULE_PERMISSIONS[module]['resources'][resource]:
                    return True
    
    return False


def check_permission(user_id: int, module: str, resource: str, action: str) -> bool:
    """Alias for user_has_permission for clearer usage."""
    return user_has_permission(user_id, module, resource, action)


# ============================================================================
# ROLE & PERMISSION MANAGEMENT
# ============================================================================

def create_role(role_name: str, description: str = None,
                company_id: int = None, is_system: bool = False) -> int:
    """
    Create a new role.

    Returns:
        The ID of the newly created role
    """
    # Ensure description column exists
    _ensure_roles_description_column()

    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO roles (role_name, description, company_id, is_system)
            VALUES (?, ?, ?, ?)
        """, (role_name, description, company_id, 1 if is_system else 0))
        db.commit()
        return cursor.lastrowid


def _ensure_roles_description_column():
    """Add description column to roles table if it doesn't exist."""
    from database import table_exists
    if not table_exists('roles'):
        return

    with get_db_context() as db:
        try:
            db.execute("ALTER TABLE roles ADD COLUMN description TEXT")
            db.commit()
        except:
            pass  # Column already exists


def add_permission_to_role(role_id: int, module: str, resource: str, action: str):
    """Add a specific permission to a role."""
    with get_db_context() as db:
        db.execute("""
            INSERT OR IGNORE INTO role_permissions (role_id, module, resource, action)
            VALUES (?, ?, ?, ?)
        """, (role_id, module, resource, action))
        db.commit()


def add_wildcard_permission(role_id: int, module: str, resource: str):
    """Add a wildcard permission (all actions for a resource) to a role."""
    with get_db_context() as db:
        db.execute("""
            INSERT OR IGNORE INTO role_permissions (role_id, module, resource, action)
            VALUES (?, ?, ?, '*')
        """, (role_id, module, resource))
        db.commit()


def remove_permission_from_role(role_id: int, module: str, resource: str, action: str):
    """Remove a specific permission from a role."""
    with get_db_context() as db:
        db.execute("""
            DELETE FROM role_permissions 
            WHERE role_id = ? AND module = ? AND resource = ? AND action = ?
        """, (role_id, module, resource, action))
        db.commit()


def delete_role(role_id: int):
    """Delete a role and all its permissions."""
    with get_db_context() as db:
        db.execute("DELETE FROM role_permissions WHERE role_id = ?", (role_id,))
        db.execute("DELETE FROM roles WHERE id = ? AND is_system = 0", (role_id,))
        db.commit()


def assign_role_to_user(user_id: int, role_id: int):
    """Assign a role to a user."""
    with get_db_context() as db:
        db.execute("UPDATE users SET role_id = ? WHERE id = ?", (role_id, user_id))
        db.commit()


# ============================================================================
# DECORATORS FOR ROUTE PROTECTION
# ============================================================================

def require_permission(module: str, resource: str, action: str):
    """
    Decorator to require a specific permission for a route.
    
    Usage:
        @app.route('/hr/employees')
        @require_login
        @require_permission('hr', 'employees', 'view')
        def hr_employees():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import session, flash, redirect, url_for
            
            user_id = session.get('user_id')
            if not user_id:
                flash("Please login to access this page.", "error")
                return redirect(url_for('login'))
            
            if not user_has_permission(user_id, module, resource, action):
                flash(f"Access Denied. You don't have permission to {action} {resource}.", "error")
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_any_permission(module: str, resource: str, actions: List[str]):
    """
    Decorator requiring any one of the specified permissions.
    
    Usage:
        @require_any_permission('hr', 'employees', ['view', 'edit'])
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import session, flash, redirect, url_for
            
            user_id = session.get('user_id')
            if not user_id:
                flash("Please login to access this page.", "error")
                return redirect(url_for('login'))
            
            has_any = any(
                user_has_permission(user_id, module, resource, action) 
                for action in actions
            )
            
            if not has_any:
                flash(f"Access Denied. You don't have permission for this action.", "error")
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_all_permissions(module: str, resource: str, actions: List[str]):
    """
    Decorator requiring all specified permissions.
    
    Usage:
        @require_all_permissions('wms', 'inventory', ['view', 'edit', 'adjust'])
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import session, flash, redirect, url_for
            
            user_id = session.get('user_id')
            if not user_id:
                flash("Please login to access this page.", "error")
                return redirect(url_for('login'))
            
            has_all = all(
                user_has_permission(user_id, module, resource, action) 
                for action in actions
            )
            
            if not has_all:
                flash(f"Access Denied. You don't have the required permissions.", "error")
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_module_access(module: str):
    """
    Decorator requiring access to all resources in a module.
    
    Usage:
        @require_module_access('hr')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import session, flash, redirect, url_for
            
            user_id = session.get('user_id')
            if not user_id:
                flash("Please login to access this page.", "error")
                return redirect(url_for('login'))
            
            permissions = get_user_permissions(user_id)
            
            # Check if user has any permission in this module
            has_module_access = any(
                perm.startswith(f"{module}.") for perm in permissions
            )
            
            if not has_module_access:
                flash(f"Access Denied. You don't have access to {module.upper()} module.", "error")
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ============================================================================
# PERMISSION FORMATTING HELPERS
# ============================================================================

def format_permission_string(module: str, resource: str, action: str) -> str:
    """Format a permission tuple into a display string."""
    return f"{module.upper()}.{resource.upper()}.{action.upper()}"


def parse_permission_string(permission: str) -> tuple:
    """Parse a permission string like 'hr.employees.view' into components."""
    parts = permission.split('.')
    if len(parts) == 3:
        return parts[0], parts[1], parts[2]
    return None, None, None


def get_module_resources(module: str) -> List[str]:
    """Get all resource names for a module."""
    if module in MODULE_PERMISSIONS:
        return list(MODULE_PERMISSIONS[module]['resources'].keys())
    return []


def get_resource_actions(module: str, resource: str) -> List[str]:
    """Get all action names for a module/resource combination."""
    if module in MODULE_PERMISSIONS:
        if resource in MODULE_PERMISSIONS[module]['resources']:
            return MODULE_PERMISSIONS[module]['resources'][resource]
    return []


def get_all_permissions_flat() -> List[Dict[str, str]]:
    """Get a flat list of all possible permissions with labels."""
    permissions = []
    for module, module_data in MODULE_PERMISSIONS.items():
        for resource, actions in module_data['resources'].items():
            for action in actions:
                permissions.append({
                    'module': module,
                    'resource': resource,
                    'action': action,
                    'key': f"{module}.{resource}.{action}",
                    'label': f"{module_data['label']} - {resource.title()} - {action.title()}"
                })
    return permissions


# ============================================================================
# SCOPE-BASED PERMISSIONS (Company/Branch/Warehouse)
# ============================================================================

def check_scope_permission(user_id: int, scope_type: str, scope_id: int,
                           require_write: bool = False) -> bool:
    """
    Check if user has access to a specific scope (company/branch/warehouse).
    
    Args:
        user_id: User ID
        scope_type: 'company', 'branch', or 'warehouse'
        scope_id: ID of the scope entity
        require_write: If True, requires write access; if False, read is enough
    
    Returns:
        True if user has scope access, False otherwise
    """
    with get_db_context() as db:
        user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return False
        
        # System users with global admin can access all scopes
        if user.get('is_admin') or (user.get('role_id') and _role_is_global_admin(user['role_id'])):
            return True
        
        # Check scope-specific permissions
        if scope_type == 'company':
            access = db.execute("""
                SELECT 1 FROM user_company_access WHERE user_id = ? AND company_id = ?
            """, (user_id, scope_id)).fetchone()
        elif scope_type == 'warehouse':
            access = db.execute("""
                SELECT 1 FROM user_warehouse_access WHERE user_id = ? AND warehouse_id = ?
            """, (user_id, scope_id)).fetchone()
        else:
            access = None
        
        return access is not None


def _role_is_global_admin(role_id: int) -> bool:
    """Check if a role is a global admin role."""
    role = get_role_by_id(role_id)
    if not role:
        return False
    role_name = role.get('role_name', '').lower()
    return 'global admin' in role_name or 'super admin' in role_name


# ============================================================================
# TMS SCOPE-BASED PERMISSIONS
# ============================================================================

def check_tms_branch_access(user_id: int, branch_id: int, require_write: bool = False) -> bool:
    """
    Check if user has access to a specific TMS branch.

    Args:
        user_id: User ID
        branch_id: Branch ID
        require_write: If True, requires write access

    Returns:
        True if user has branch access, False otherwise
    """
    with get_db_context() as db:
        user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return False

        if user.get('is_admin') or _role_is_global_admin(user.get('role_id', 0)):
            return True

        role = get_role_by_id(user['role_id']) if user.get('role_id') else None
        if role:
            role_name = role.get('role_name', '').lower()
            if 'tms admin' in role_name or 'global admin' in role_name:
                return True

        access = db.execute("""
            SELECT 1 FROM user_branch_access
            WHERE user_id = ? AND branch_id = ?
        """, (user_id, branch_id)).fetchone()

        return access is not None


def check_tms_route_scope(user_id: int, route_id: int) -> bool:
    """
    Check if user can access a specific route.

    Args:
        user_id: User ID
        route_id: Route ID

    Returns:
        True if user has route access, False otherwise
    """
    with get_db_context() as db:
        user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return False

        if user.get('is_admin') or _role_is_global_admin(user.get('role_id', 0)):
            return True

        role = get_role_by_id(user['role_id']) if user.get('role_id') else None
        if role:
            role_name = role.get('role_name', '').lower()
            if role_name in ['dispatcher', 'auditor', 'executive viewer']:
                route = db.execute("SELECT branch_id FROM logistics_routes WHERE id = ?", (route_id,)).fetchone()
                if route:
                    return check_tms_branch_access(user_id, route['branch_id'])
                return False

        return True


def check_tms_vehicle_scope(user_id: int, vehicle_id: int) -> bool:
    """
    Check if user can access a specific vehicle.

    Args:
        user_id: User ID
        vehicle_id: Vehicle ID

    Returns:
        True if user has vehicle access, False otherwise
    """
    with get_db_context() as db:
        user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return False

        if user.get('is_admin') or _role_is_global_admin(user.get('role_id', 0)):
            return True

        role = get_role_by_id(user['role_id']) if user.get('role_id') else None
        if role:
            role_name = role.get('role_name', '').lower()
            if role_name in ['dispatcher', 'auditor', 'executive viewer']:
                vehicle = db.execute("SELECT branch_id FROM logistics_vehicles WHERE id = ?", (vehicle_id,)).fetchone()
                if vehicle:
                    return check_tms_branch_access(user_id, vehicle['branch_id'])
                return False

        return True


def check_tms_driver_scope(user_id: int, driver_id: int) -> bool:
    """
    Check if user can access a specific driver.

    Args:
        user_id: User ID
        driver_id: Driver ID

    Returns:
        True if user has driver access, False otherwise
    """
    with get_db_context() as db:
        user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if not user:
            return False

        if user.get('is_admin') or _role_is_global_admin(user.get('role_id', 0)):
            return True

        role = get_role_by_id(user['role_id']) if user.get('role_id') else None
        if role:
            role_name = role.get('role_name', '').lower()
            if role_name in ['dispatcher', 'auditor', 'executive viewer']:
                driver = db.execute("SELECT branch_id FROM logistics_drivers WHERE id = ?", (driver_id,)).fetchone()
                if driver:
                    return check_tms_branch_access(user_id, driver['branch_id'])
                return False

        return True


def user_can_view_tms_cost(user_id: int, cost_amount: float = None) -> bool:
    """
    Check if a user can view TMS cost information.

    Args:
        user_id: User ID
        cost_amount: Optional cost amount to check against threshold

    Returns:
        True if user can view costs, False otherwise
    """
    perms = get_user_permissions(user_id)

    if 'tms.costs.view_sensitive' in perms or 'tms.*' in perms:
        return True

    if 'tms.costs.view' not in perms and 'logistics.costs.view' not in perms:
        return False

    if cost_amount:
        threshold = 10000
        if cost_amount > threshold:
            return 'tms.costs.approve' in perms or 'logistics.costs.approve' in perms

    return True


def user_can_approve_tms_cost(user_id: int, cost_amount: float, role_id: int = None) -> bool:
    """
    Check if a user can approve a TMS cost.

    Args:
        user_id: User ID
        cost_amount: Cost amount to approve
        role_id: Optional role_id (will fetch from user if not provided)

    Returns:
        True if user can approve, False otherwise
    """
    perms = get_user_permissions(user_id)

    if 'tms.costs.approve' not in perms and 'logistics.costs.approve' not in perms:
        return False

    approval_thresholds = {
        'tms admin': float('inf'),
        'logistics manager': 50000,
        'cost reviewer': 25000,
        'dispatch supervisor': 5000,
    }

    if role_id is None:
        user = get_one("SELECT role_id FROM users WHERE id = ?", (user_id,))
        role_id = user['role_id'] if user else None

    role = get_role_by_id(role_id) if role_id else None
    if role:
        role_name = role.get('role_name', '').lower()
        for key, threshold in approval_thresholds.items():
            if key in role_name:
                return cost_amount <= threshold

    return cost_amount <= 5000


# ============================================================================
# PERMISSION CACHE (for performance)
# ============================================================================

_user_permission_cache: Dict[int, tuple] = {}
_CACHE_TTL = 300  # 5 minutes


def get_user_permissions_cached(user_id: int, use_cache: bool = True) -> Set[str]:
    """
    Get user permissions with caching.
    
    Args:
        user_id: User ID
        use_cache: Whether to use/return cached value
    
    Returns:
        Set of permission strings
    """
    import time
    
    if use_cache and user_id in _user_permission_cache:
        cached_expiry, cached_permissions = _user_permission_cache[user_id]
        if time.time() - cached_expiry < _CACHE_TTL:
            return cached_permissions
    
    permissions = get_user_permissions(user_id)
    
    if use_cache:
        import time
        _user_permission_cache[user_id] = (time.time(), permissions)
    
    return permissions


def invalidate_user_permission_cache(user_id: int):
    """Invalidate the permission cache for a user."""
    if user_id in _user_permission_cache:
        del _user_permission_cache[user_id]


def invalidate_all_permission_caches():
    """Invalidate all cached permissions."""
    _user_permission_cache.clear()


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_permissions():
    """Initialize the permission system - create tables and default roles."""
    
    # Ensure role_permissions table exists
    if not _table_exists('role_permissions'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS role_permissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role_id INTEGER NOT NULL,
                    module TEXT NOT NULL,
                    resource TEXT NOT NULL,
                    action TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(role_id, module, resource, action)
                )
            """)
            db.execute("CREATE INDEX idx_rp_role ON role_permissions(role_id)")
            db.execute("CREATE INDEX idx_rp_perm ON role_permissions(module, resource, action)")
            
            # Ensure roles table has is_system field
            try:
                db.execute("ALTER TABLE roles ADD COLUMN is_system INTEGER DEFAULT 0")
            except:
                pass
            
            db.commit()
    
    # Ensure scope access tables exist
    if not _table_exists('user_company_access'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS user_company_access (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    company_id INTEGER NOT NULL,
                    access_level TEXT DEFAULT 'read',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, company_id)
                )
            """)
    
    if not _table_exists('user_warehouse_access'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS user_warehouse_access (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    warehouse_id INTEGER NOT NULL,
                    access_level TEXT DEFAULT 'read',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, warehouse_id)
                )
            """)
            db.commit()
    
    # Create default roles if they don't exist
    _create_default_roles()


def _table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    with _get_db() as db:
        result = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        ).fetchone()
        return result is not None


def _role_exists(role_name: str) -> bool:
    """Check if a role with this name exists."""
    with get_db_context() as db:
        result = db.execute(
            "SELECT 1 FROM roles WHERE role_name = ?", (role_name,)
        ).fetchone()
        return result is not None


def _create_default_roles():
    """Create default system roles."""
    
    default_roles = [
        {
            'name': 'Global Admin',
            'description': 'Full system access with all permissions',
            'permissions': [('*', '*', '*'), ('flow', '*', '*')]  # Wildcard = all permissions
        },
        {
            'name': 'Asset Admin',
            'description': 'Full Asset Management module access',
            'permissions': [
                ('assets', '*', '*'),
                ('reports', 'executive', 'view'),
                ('reports', 'operational', 'view'),
            ]
        },
        {
            'name': 'Fixed Asset Accountant',
            'description': 'Asset depreciation and financial asset management',
            'permissions': [
                ('assets', 'dashboard', 'view'),
                ('assets', 'assets', 'view'),
                ('assets', 'categories', 'view'),
                ('assets', 'acquisitions', 'view'),
                ('assets', 'depreciation', 'view'),
                ('assets', 'depreciation', 'create'),
                ('assets', 'depreciation', 'run'),
                ('assets', 'depreciation', 'post'),
                ('assets', 'depreciation_profiles', 'view'),
                ('assets', 'depreciation_profiles', 'create'),
                ('assets', 'depreciation_profiles', 'edit'),
                ('assets', 'reports', 'view'),
                ('assets', 'reports', 'export'),
                ('assets', 'audit_log', 'view'),
            ]
        },
        {
            'name': 'Maintenance Coordinator',
            'description': 'Asset maintenance scheduling and tracking',
            'permissions': [
                ('assets', 'dashboard', 'view'),
                ('assets', 'assets', 'view'),
                ('assets', 'maintenance', 'view'),
                ('assets', 'maintenance', 'create'),
                ('assets', 'maintenance', 'edit'),
                ('assets', 'maintenance_schedules', 'view'),
                ('assets', 'maintenance_schedules', 'create'),
                ('assets', 'maintenance_schedules', 'edit'),
                ('assets', 'maintenance_work_orders', 'view'),
                ('assets', 'maintenance_work_orders', 'create'),
                ('assets', 'maintenance_work_orders', 'edit'),
                ('assets', 'maintenance_work_logs', 'view'),
                ('assets', 'maintenance_work_logs', 'create'),
                ('assets', 'maintenance_costs', 'view'),
                ('reports', 'operational', 'view'),
            ]
        },
        {
            'name': 'HR Manager',
            'description': 'Full HR module access',
            'permissions': [
                ('hr', '*', '*'),  # All HR permissions
                ('tasks', 'tasks', 'view'),
                ('tasks', 'subtasks', 'view'),
                ('reports', 'executive', 'view'),
            ]
        },
        {
            'name': 'Warehouse Manager',
            'description': 'Full WMS and inventory access',
            'permissions': [
                ('wms', '*', '*'),
                ('logistics', '*', '*'),
                ('planning', 'dashboard', 'view'),
                ('planning', 'reports', 'view'),
                ('tasks', 'tasks', 'view'),
            ]
        },
        {
            'name': 'Procurement Manager',
            'description': 'Full procurement and purchasing access',
            'permissions': [
                ('procurement', '*', '*'),
                ('planning', 'dashboard', 'view'),
                ('planning', 'replenishment', 'view'),
                ('wms', 'receipts', 'view'),
                ('logistics', 'dashboard', 'view'),
                ('reports', 'operational', 'view'),
                ('tasks', 'tasks', 'view'),
            ]
        },
        {
            'name': 'Quality Manager',
            'description': 'Full Quality Management module access',
            'permissions': [
                ('quality', '*', '*'),
                ('reports', 'executive', 'view'),
                ('reports', 'operational', 'view'),
            ]
        },
        {
            'name': 'Quality Inspector',
            'description': 'Quality inspection and NCR tracking',
            'permissions': [
                ('quality', 'dashboard', 'view'),
                ('quality', 'inspections', ['view', 'create', 'edit', 'execute']),
                ('quality', 'ncr', ['view', 'create', 'edit']),
                ('quality', 'reports', 'view'),
            ]
        },
        {
            'name': 'Quality Auditor',
            'description': 'Quality audit management',
            'permissions': [
                ('quality', 'dashboard', 'view'),
                ('quality', 'audits', ['view', 'create', 'edit', 'execute']),
                ('quality', 'ncr', 'view'),
                ('quality', 'capa', ['view', 'create', 'edit']),
                ('quality', 'reports', 'view'),
            ]
        },
        {
            'name': 'QA Manager',
            'description': 'Senior Quality Assurance Manager with full quality control oversight',
            'permissions': [
                ('quality', '*', '*'),
                ('reports', 'executive', 'view'),
                ('reports', 'operational', 'view'),
                ('tasks', 'tasks', 'view'),
            ]
        },
        {
            'name': 'QC Inspector',
            'description': 'Quality Control Inspector for inspections and testing',
            'permissions': [
                ('quality', 'dashboard', 'view'),
                ('quality', 'inspections', ['view', 'create', 'edit', 'execute']),
                ('quality', 'inspection_plans', ['view', 'create', 'edit']),
                ('quality', 'inspection_templates', 'view'),
                ('quality', 're_inspection', ['view', 'create']),
                ('quality', 'ncr', ['view', 'create']),
                ('quality', 'inspection_reports', ['view', 'export']),
            ]
        },
        {
            'name': 'NCR Coordinator',
            'description': 'Non-Conformance Record management specialist',
            'permissions': [
                ('quality', 'dashboard', 'view'),
                ('quality', 'ncr', ['view', 'create', 'edit', 'approve', 'resolve', 'close']),
                ('quality', 'ncr_containment', ['view', 'create', 'edit', 'verify']),
                ('quality', 'ncr_disposition', ['view', 'create', 'edit', 'approve', 'execute']),
                ('quality', 'quality_holds', ['view', 'create']),
                ('quality', 'ncr_reports', ['view', 'export']),
            ]
        },
        {
            'name': 'CAPA Owner',
            'description': 'CAPA management and implementation',
            'permissions': [
                ('quality', 'dashboard', 'view'),
                ('quality', 'capa', ['view', 'create', 'edit', 'verify', 'close']),
                ('quality', 'capa_actions', ['view', 'create', 'edit', 'complete']),
                ('quality', 'capa_effectiveness', ['view', 'create', 'edit', 'approve', 'close']),
                ('quality', 'capa_reports', ['view', 'export']),
            ]
        },
        {
            'name': 'Audit Manager',
            'description': 'Audit program and finding management',
            'permissions': [
                ('quality', 'dashboard', 'view'),
                ('quality', 'audits', ['view', 'create', 'edit', 'approve', 'execute', 'close', 'cancel']),
                ('quality', 'audit_programs', ['view', 'create', 'edit', 'manage']),
                ('quality', 'audit_checklists', ['view', 'create', 'edit', 'manage']),
                ('quality', 'audit_findings', ['view', 'create', 'edit', 'verify', 'close']),
                ('quality', 'audit_finding_actions', ['view', 'create', 'edit', 'complete']),
                ('quality', 'audit_reports', ['view', 'export']),
            ]
        },
        {
            'name': 'Supplier Quality Reviewer',
            'description': 'Supplier quality management and scorecards',
            'permissions': [
                ('quality', 'dashboard', 'view'),
                ('quality', 'supplier_quality', ['view', 'create', 'edit', 'approve', 'block', 'unblock']),
                ('quality', 'supplier_scorecards', ['view', 'create', 'edit', 'export']),
                ('quality', 'supplier_ncr', ['view', 'create', 'edit', 'resolve']),
                ('quality', 'supplier_capa', ['view', 'create', 'edit', 'resolve']),
                ('quality', 'supplier_quality_reports', ['view', 'export']),
            ]
        },
        {
            'name': 'Compliance Reviewer',
            'description': 'Quality compliance and regulatory management',
            'permissions': [
                ('quality', 'dashboard', 'view'),
                ('quality', 'compliance', ['view', 'create', 'edit', 'approve', 'export', 'manage']),
                ('quality', 'quality_documents', ['view', 'create', 'edit', 'approve', 'publish']),
                ('quality', 'controlled_docs', ['view', 'create', 'edit', 'approve', 'release']),
                ('quality', 'certifications', ['view', 'create', 'edit', 'approve', 'manage']),
                ('quality', 'quality_risks', ['view', 'create', 'edit', 'mitigate', 'manage']),
                ('quality', 'risk_assessment', ['view', 'create', 'edit', 'approve', 'manage']),
                ('quality', 'critical_control_points', ['view', 'create', 'edit', 'manage']),
                ('quality', 'escalation_rules', ['view', 'create', 'edit', 'manage']),
                ('quality', 'compliance_reports', ['view', 'export']),
            ]
        },
        {
            'name': 'Operations Viewer',
            'description': 'Read-only quality operations access',
            'permissions': [
                ('quality', 'dashboard', 'view'),
                ('quality', 'inspections', 'view'),
                ('quality', 'ncr', 'view'),
                ('quality', 'audits', 'view'),
                ('quality', 'audit_findings', 'view'),
                ('quality', 'reports', 'view'),
            ]
        },
        {
            'name': 'Executive Viewer',
            'description': 'Executive quality dashboard and KPI access',
            'permissions': [
                ('quality', 'dashboard', 'view'),
                ('quality', 'executive_dashboard', 'view'),
                ('quality', 'reports', 'view'),
                ('quality', 'inspection_reports', 'view'),
                ('quality', 'ncr_reports', 'view'),
                ('quality', 'capa_reports', 'view'),
                ('quality', 'supplier_quality_reports', 'view'),
                ('quality', 'compliance_reports', 'view'),
            ]
        },
        {
            'name': 'Sales Manager',
            'description': 'Sales, CRM, and customer access',
            'permissions': [
                ('crm', '*', '*'),
                ('sales', '*', '*'),
                ('marketing', 'leads', 'view'),
                ('marketing', 'leads', 'create'),
                ('marketing', 'leads', 'edit'),
                ('tasks', 'tasks', 'view'),
                ('tasks', 'tasks', 'create'),
                ('tasks', 'tasks', 'edit'),
            ]
        },
        {
            'name': 'Logistics Manager',
            'description': 'Logistics and delivery operations',
            'permissions': [
                ('logistics', '*', '*'),
                ('tms', '*', '*'),
                ('wms', 'shipments', 'view'),
                ('wms', 'shipments', 'ship'),
                ('wms', 'returns', 'view'),
                ('tasks', 'tasks', 'view'),
            ]
        },
        {
            'name': 'TMS Admin',
            'description': 'Full TMS administrator access',
            'permissions': [
                ('tms', '*', '*'),
                ('logistics', '*', '*'),
                ('reports', 'logistics', 'view'),
                ('reports', 'logistics', 'export'),
            ]
        },
        {
            'name': 'Dispatch Supervisor',
            'description': 'Manage dispatch board and assignments',
            'permissions': [
                ('tms', 'dashboard', 'view'),
                ('tms', 'dispatch_board', ['view', 'create', 'edit', 'assign', 'execute', 'reassign']),
                ('tms', 'trips', ['view', 'create', 'edit']),
                ('tms', 'routes', 'view'),
                ('tms', 'vehicles', 'view'),
                ('tms', 'drivers', 'view'),
                ('tms', 'stops', ['view', 'create', 'edit', 'complete']),
                ('tms', 'shipments', ['view', 'create', 'edit']),
                ('tms', 'incidents', ['view', 'create']),
                ('tms', 'pod', 'view'),
                ('tms', 'reports', 'view'),
            ]
        },
        {
            'name': 'Dispatcher',
            'description': 'View dispatch and assign loads',
            'permissions': [
                ('tms', 'dashboard', 'view'),
                ('tms', 'dispatch_board', ['view', 'assign']),
                ('tms', 'trips', 'view'),
                ('tms', 'routes', 'view'),
                ('tms', 'vehicles', 'view'),
                ('tms', 'drivers', 'view'),
                ('tms', 'shipments', 'view'),
                ('tms', 'pod', 'view'),
            ]
        },
        {
            'name': 'Fleet Manager',
            'description': 'Manage vehicles and drivers',
            'permissions': [
                ('tms', 'dashboard', 'view'),
                ('tms', 'vehicles', ['view', 'create', 'edit', 'maintenance']),
                ('tms', 'drivers', ['view', 'create', 'edit', 'availability']),
                ('tms', 'trips', 'view'),
                ('tms', 'routes', 'view'),
                ('tms', 'reports', ['view', 'export']),
                ('tms', 'settings', 'view'),
            ]
        },
        {
            'name': 'Driver Coordinator',
            'description': 'Manage driver availability and assignments',
            'permissions': [
                ('tms', 'dashboard', 'view'),
                ('tms', 'drivers', ['view', 'create', 'edit', 'availability', 'assign']),
                ('tms', 'trips', 'view'),
                ('tms', 'dispatch_board', 'view'),
                ('tms', 'vehicles', 'view'),
            ]
        },
        {
            'name': 'POD Reviewer',
            'description': 'Review and approve Proof of Delivery',
            'permissions': [
                ('tms', 'dashboard', 'view'),
                ('tms', 'pod', ['view', 'edit', 'approve', 'reject']),
                ('tms', 'trips', 'view'),
                ('tms', 'reports', 'view'),
            ]
        },
        {
            'name': 'Cost Reviewer',
            'description': 'View cost reports and approve high-cost trips',
            'permissions': [
                ('tms', 'dashboard', 'view'),
                ('tms', 'trips', 'view'),
                ('tms', 'costs', ['view', 'approve']),
                ('tms', 'reports', ['view', 'export']),
                ('tms', 'shipments', 'view'),
            ]
        },
        {
            'name': 'Auditor',
            'description': 'Read-only access with audit log viewing',
            'permissions': [
                ('tms', 'dashboard', 'view'),
                ('tms', 'trips', 'view'),
                ('tms', 'routes', 'view'),
                ('tms', 'dispatch_board', 'view'),
                ('tms', 'vehicles', 'view'),
                ('tms', 'drivers', 'view'),
                ('tms', 'shipments', 'view'),
                ('tms', 'pod', 'view'),
                ('tms', 'incidents', 'view'),
                ('tms', 'costs', 'view'),
                ('tms', 'reports', 'view'),
                ('tms', 'audit_logs', ['view', 'export']),
            ]
        },
        {
            'name': 'Executive Viewer',
            'description': 'Executive dashboards only - read only',
            'permissions': [
                ('tms', 'dashboard', 'view'),
                ('tms', 'reports', 'view'),
                ('reports', 'executive', 'view'),
            ]
        },
        {
            'name': 'Planner',
            'description': 'Demand planning and forecasting',
            'permissions': [
                ('planning', '*', '*'),
                ('wms', 'inventory', 'view'),
                ('wms', 'reports', 'view'),
                ('reports', 'operational', 'view'),
            ]
        },
        {
            'name': 'Marketing Manager',
            'description': 'Marketing and campaigns',
            'permissions': [
                ('marketing', '*', '*'),
                ('customer_intelligence', 'profiles', 'view'),
                ('customer_intelligence', 'segments', 'view'),
                ('reports', 'operational', 'view'),
            ]
        },
        {
            'name': 'Employee',
            'description': 'Basic employee access',
            'permissions': [
                ('hr', 'dashboard', 'view'),
                ('hr', 'attendance', 'view'),
                ('hr', 'leave', 'view'),
                ('hr', 'leave', 'create'),
                ('tasks', 'tasks', 'view'),
                ('tasks', 'subtasks', 'view'),
                ('tasks', 'subtasks', 'create'),
                ('flow', 'dashboard', 'view'),
                ('flow', 'chats', ['view', 'send']),
                ('flow', 'channels', 'view'),
                ('flow', 'groups', 'view'),
                ('flow', 'messages', ['view', 'send']),
                ('flow', 'notifications', 'view'),
                ('flow', 'reminders', ['view', 'create']),
                ('flow', 'saved_messages', 'view'),
                ('flow', 'search', 'view'),
                ('flow', 'settings', 'view'),
            ]
        },
        {
            'name': 'Viewer',
            'description': 'Read-only access to most modules',
            'permissions': [
                ('hr', 'dashboard', 'view'),
                ('wms', 'dashboard', 'view'),
                ('wms', 'inventory', 'view'),
                ('logistics', 'dashboard', 'view'),
                ('logistics', 'trips', 'view'),
                ('planning', 'dashboard', 'view'),
                ('planning', 'forecasts', 'view'),
                ('crm', 'dashboard', 'view'),
                ('crm', 'customers', 'view'),
                ('marketing', 'dashboard', 'view'),
                ('reports', 'executive', 'view'),
                ('reports', 'operational', 'view'),
                ('flow', 'dashboard', 'view'),
                ('flow', 'chats', 'view'),
                ('flow', 'channels', 'view'),
                ('flow', 'groups', 'view'),
                ('flow', 'messages', 'view'),
                ('flow', 'notifications', 'view'),
                ('flow', 'reminders', 'view'),
                ('flow', 'saved_messages', 'view'),
                ('flow', 'search', 'view'),
                ('flow', 'settings', 'view'),
            ]
        },
    ]
    
    for role_def in default_roles:
        if not _role_exists(role_def['name']):
            role_id = create_role(
                role_def['name'], 
                role_def['description'], 
                is_system=True
            )
            
            for module, resource, action in role_def['permissions']:
                if action == '*' and resource == '*':
                    # Module-level wildcard
                    add_wildcard_permission(role_id, module, '*')
                elif action == '*':
                    # Resource-level wildcard
                    add_wildcard_permission(role_id, module, resource)
                elif isinstance(action, list):
                    # Multiple actions for this resource
                    for a in action:
                        add_permission_to_role(role_id, module, resource, a)
                else:
                    add_permission_to_role(role_id, module, resource, action)


# =============================================================================
# FIELD-LEVEL SECURITY (Enterprise Data Protection)
# =============================================================================
# Sensitive fields that require elevated permissions to view or edit.
# Used for: salary, bank account, SSN/tax ID, credit limit, etc.

SENSITIVE_FIELDS = {
    # HR / Employee fields
    'hr': {
        'employees': {
            'salary': {'masked_default': '*****', 'access_level': 'restricted'},
            'bank_account_number': {'masked_default': '****', 'access_level': 'restricted'},
            'tax_id': {'masked_default': '***-**-****', 'access_level': 'restricted'},
            'ssn': {'masked_default': '***-**-****', 'access_level': 'restricted'},
            'date_of_birth': {'masked_default': '**/**/****', 'access_level': 'elevated'},
            'emergency_contact_phone': {'masked_default': '*****', 'access_level': 'elevated'},
            'emergency_contact_name': {'masked_default': '*****', 'access_level': 'elevated'},
        },
        'payroll': {
            'net_pay': {'masked_default': '*****', 'access_level': 'restricted'},
            'gross_pay': {'masked_default': '*****', 'access_level': 'restricted'},
            'tax_withheld': {'masked_default': '*****', 'access_level': 'restricted'},
            'bank_account': {'masked_default': '****', 'access_level': 'restricted'},
        }
    },
    # Finance / Treasury fields
    'finance': {
        'accounts': {
            'bank_account_number': {'masked_default': '****', 'access_level': 'restricted'},
            'iban': {'masked_default': '****', 'access_level': 'restricted'},
            'swift_code': {'masked_default': '*****', 'access_level': 'restricted'},
        },
        'bank_accounts': {
            'account_number': {'masked_default': '****', 'access_level': 'restricted'},
            'iban': {'masked_default': '****', 'access_level': 'restricted'},
            'pin': {'masked_default': '*****', 'access_level': 'restricted'},
            'online_password': {'masked_default': '*****', 'access_level': 'restricted'},
        }
    },
    # Customer Intelligence
    'customer_intelligence': {
        'profiles': {
            'credit_card': {'masked_default': '****', 'access_level': 'restricted'},
            'tax_id': {'masked_default': '***-**-****', 'access_level': 'restricted'},
        }
    },
    # CRM / Sales
    'crm': {
        'customers': {
            'credit_limit': {'masked_default': None, 'access_level': 'elevated'},
            'payment_terms_override': {'masked_default': None, 'access_level': 'elevated'},
        }
    },
    # Treasury
    'treasury': {
        'bank_accounts': {
            'account_number': {'masked_default': '****', 'access_level': 'restricted'},
            'pin': {'masked_default': '*****', 'access_level': 'restricted'},
            'password': {'masked_default': '*****', 'access_level': 'restricted'},
        },
        'counterparties': {
            'bank_account': {'masked_default': '****', 'access_level': 'restricted'},
        }
    }
}


def get_sensitive_fields(module, resource):
    """Get list of sensitive fields for a module/resource."""
    if module not in SENSITIVE_FIELDS:
        return []
    resource_fields = SENSITIVE_FIELDS.get(module, {}).get(resource, {})
    return list(resource_fields.keys())


def is_sensitive_field(module, resource, field):
    """Check if a field is marked as sensitive."""
    if module not in SENSITIVE_FIELDS:
        return False
    return field in SENSITIVE_FIELDS.get(module, {}).get(resource, {})


def get_field_access_level(module, resource, field):
    """Get the access level required for a field: 'restricted', 'elevated', or None."""
    if module not in SENSITIVE_FIELDS:
        return None
    field_info = SENSITIVE_FIELDS.get(module, {}).get(resource, {}).get(field, {})
    return field_info.get('access_level')


def mask_sensitive_value(module, resource, field, value, unmasked=False):
    """
    Mask a sensitive field value based on access level.

    Args:
        module: Module name (e.g., 'hr', 'finance')
        resource: Resource name (e.g., 'employees', 'bank_accounts')
        field: Field name
        value: Original value
        unmasked: If True, return the actual value (caller verified access)

    Returns:
        Masked string or original value if unmasked
    """
    if unmasked or not value:
        return value

    if module not in SENSITIVE_FIELDS:
        return value

    field_info = SENSITIVE_FIELDS.get(module, {}).get(resource, {}).get(field, {})
    return field_info.get('masked_default', '*****')


def filter_sensitive_fields(module, resource, record_dict, unmasked=False):
    """
    Filter a record dictionary to mask sensitive fields.

    Args:
        module: Module name
        resource: Resource name
        record_dict: Dictionary of field:value pairs
        unmasked: If True, don't mask (caller verified access)

    Returns:
        New dictionary with sensitive fields masked
    """
    if module not in SENSITIVE_FIELDS:
        return record_dict

    sensitive = SENSITIVE_FIELDS.get(module, {}).get(resource, {})
    if not sensitive:
        return record_dict

    result = dict(record_dict)
    for field in sensitive:
        if field in result:
            result[field] = mask_sensitive_value(module, resource, field, result[field], unmasked)

    return result


def user_can_view_field(user_id, module, resource, field):
    """
    Check if a user can view a specific sensitive field.
    Returns (can_view, reason).
    """
    access_level = get_field_access_level(module, resource, field)
    if not access_level:
        return True, None  # Not sensitive

    # Get user's role
    user_perms = get_user_permissions(user_id)
    role_perms = user_perms.get(module, {})

    # Admin role can view everything
    if role_perms.get('admin') or '*' in role_perms.get('*', []):
        return True, None

    if access_level == 'restricted':
        # Only roles explicitly granted the restricted field can view
        # Check for field-level override permission
        field_perm_key = f'{resource}.{field}'
        if field_perm_key in role_perms:
            actions = role_perms[field_perm_key]
            if 'view_sensitive' in actions or '*' in actions:
                return True, None

        # Default: deny restricted fields
        return False, f"Access to {field} requires elevated permissions"

    elif access_level == 'elevated':
        # Elevated fields need view permission on the resource at minimum
        resource_perms = role_perms.get(resource, [])
        if 'view' in resource_perms or 'admin' in resource_perms or '*' in resource_perms:
            return True, None
        return False, f"Access to {field} requires view permission on {resource}"

    return True, None


# =============================================================================
# SEGREGATION OF DUTIES (SOD) MATRIX
# =============================================================================

SOD_RULES = [
    # Finance SOD: Creator and approver must be different
    {
        'rule_id': 'FIN_SOD_001',
        'name': 'Finance Transaction Separation',
        'description': 'User who creates a journal entry cannot approve it',
        'entity_type': 'finance_journal',
        'create_permission': ('finance', 'journals', 'create'),
        'approve_permission': ('finance', 'journals', 'approve'),
        'severity': 'HIGH',
    },
    {
        'rule_id': 'FIN_SOD_002',
        'name': 'Payment Approval Separation',
        'description': 'User who creates a payment cannot approve it',
        'entity_type': 'finance_payment',
        'create_permission': ('finance', 'ap_payments', 'create'),
        'approve_permission': ('finance', 'ap_payments', 'approve'),
        'severity': 'HIGH',
    },
    {
        'rule_id': 'TR_SOD_001',
        'name': 'Treasury Transfer Separation',
        'description': 'User who creates a transfer cannot approve it',
        'entity_type': 'treasury_transfer',
        'create_permission': ('finance', 'transfers', 'create'),
        'approve_permission': ('finance', 'transfers', 'approve'),
        'severity': 'HIGH',
    },
    {
        'rule_id': 'TR_SOD_002',
        'name': 'Treasury Payment Run Separation',
        'description': 'User who creates a payment run cannot execute it',
        'entity_type': 'treasury_payment_run',
        'create_permission': ('finance', 'payment_runs', 'create'),
        'approve_permission': ('finance', 'payment_runs', 'approve'),
        'execute_permission': ('finance', 'payment_runs', 'execute'),
        'severity': 'HIGH',
    },
    {
        'rule_id': 'ASSET_SOD_001',
        'name': 'Asset Disposal Separation',
        'description': 'User who creates a disposal request cannot approve it',
        'entity_type': 'asset_disposal',
        'create_permission': ('assets', 'disposal_requests', 'create'),
        'approve_permission': ('assets', 'disposal_requests', 'approve'),
        'severity': 'HIGH',
    },
    {
        'rule_id': 'HR_SOD_001',
        'name': 'Payroll Processing Separation',
        'description': 'User who processes payroll cannot approve it',
        'entity_type': 'hr_payroll',
        'create_permission': ('hr', 'payroll', 'create'),
        'approve_permission': ('hr', 'payroll', 'approve'),
        'severity': 'HIGH',
    },
    {
        'rule_id': 'PROC_SOD_001',
        'name': 'Purchase Order Separation',
        'description': 'User who creates a PO above threshold cannot approve it',
        'entity_type': 'procurement_order',
        'create_permission': ('procurement', 'orders', 'create'),
        'approve_permission': ('procurement', 'orders', 'approve'),
        'severity': 'MEDIUM',
    },
]


def check_sod_violation(user_id, entity_type, action, entity_id=None, entity_data=None):
    """
    Check if performing an action would violate SOD rules.

    Args:
        user_id: ID of user attempting the action
        entity_type: Type of entity (e.g., 'finance_journal')
        action: Action being performed (e.g., 'approve')
        entity_id: ID of specific entity (if known)
        entity_data: Dict with entity data (e.g., {'created_by': user_id})

    Returns:
        (is_violation, violation_details)
        - is_violation: True if SOD would be violated
        - violation_details: Dict with rule details if violated
    """
    # Find applicable SOD rules
    for rule in SOD_RULES:
        if rule['entity_type'] != entity_type:
            continue

        # Check if this is an approval/execute action
        approve_action = None
        if action == 'approve' and 'approve_permission' in rule:
            approve_action = rule['approve_permission']
        elif action == 'execute' and 'execute_permission' in rule:
            approve_action = rule['execute_permission']
        else:
            continue

        # Get the creator of the entity
        creator_id = None
        if entity_data and 'created_by' in entity_data:
            creator_id = entity_data['created_by']
        elif entity_id:
            # Try to look up from database
            creator_id = _get_entity_creator(entity_type, entity_id)

        # Check SOD violation
        if creator_id and creator_id == user_id:
            return True, {
                'rule_id': rule['rule_id'],
                'rule_name': rule['name'],
                'description': rule['description'],
                'severity': rule['severity'],
                'message': f"SOD Violation: You cannot {action} an item you created. "
                          f"Different personnel must create and approve for segregation of duties."
            }

    return False, None


def _get_entity_creator(entity_type, entity_id):
    """Get the creator user_id for an entity."""
    # Generic lookup by entity_type pattern
    creator_field_map = {
        'finance_journal': ('finance_journals', 'created_by_user_id'),
        'finance_payment': ('finance_supplier_payments', 'created_by'),
        'treasury_transfer': ('treasury_transfer_requests', 'requested_by'),
        'treasury_payment_run': ('treasury_payment_runs', 'created_by'),
        'asset_disposal': ('disposal_requests', 'requested_by'),
        'procurement_order': ('procurement_orders', 'created_by'),
    }

    if entity_type not in creator_field_map:
        return None

    table, field = creator_field_map[entity_type]
    result = get_one(f"SELECT {field} FROM {table} WHERE id = ?", (entity_id,))
    return result[field] if result else None


def get_sod_violations_for_user(user_id):
    """
    Get all potential SOD violations for a user's current permissions.
    Returns list of rules that would be violated by this user's permission set.
    """
    user_perms = get_user_permissions(user_id)
    violations = []

    for rule in SOD_RULES:
        mod, res, act = rule.get('approve_permission', rule.get('execute_permission', (None, None, None)))
        if not mod:
            continue

        # Check if user has both create and approve/execute on same rule
        can_create = user_has_permission(user_id, mod, res, 'create')
        can_approve = user_has_permission(user_id, mod, res, act.split('_')[-1] if '_' in act else act)

        if can_create and can_approve:
            violations.append({
                'rule_id': rule['rule_id'],
                'rule_name': rule['name'],
                'description': rule['description'],
                'severity': rule['severity'],
                'create_permission': rule['create_permission'],
                'approve_permission': rule.get('approve_permission') or rule.get('execute_permission'),
            })

    return violations


# =============================================================================
# INITIALIZE PERMISSIONS
# =============================================================================

# Initialize permissions when module is imported
initialize_permissions()
