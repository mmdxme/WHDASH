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
        'label': 'Maintenance Management',
        'resources': {
            'dashboard': ['view'],
            'equipment': ['view', 'create', 'edit'],
            'equipment_detail': ['view'],
            'equipment_downtime': ['view'],
            'facilities': ['view', 'create', 'edit', 'delete'],
            'facility_requests': ['view', 'create', 'edit', 'complete'],
            'pm_plans': ['view', 'create', 'edit', 'delete'],
            'pm_schedules': ['view', 'create', 'edit', 'delete'],
            'corrective': ['view', 'create', 'edit'],
            'breakdown': ['view', 'create', 'edit'],
            'work_orders': ['view', 'create', 'edit', 'complete', 'assign'],
            'work_order_tasks': ['view', 'create', 'edit', 'complete'],
            'technicians': ['view', 'create', 'edit'],
            'teams': ['view', 'create', 'edit'],
            'parts_usage': ['view', 'create', 'edit'],
            'labor_logs': ['view', 'create', 'edit'],
            'downtime': ['view', 'create', 'edit'],
            'inspections': ['view', 'create', 'edit'],
            'checklists': ['view', 'create', 'edit'],
            'calendar': ['view'],
            'reports': ['view', 'export'],
            'settings': ['view', 'edit'],
            'audit_logs': ['view', 'export'],
            'my_work_orders': ['view', 'edit', 'complete'],
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
            'budgets': ['view', 'create', 'edit', 'delete', 'approve'],
            'tax': ['view', 'create', 'edit'],
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
            'trips': ['view', 'create', 'edit', 'delete', 'start', 'complete'],
            'routes': ['view', 'create', 'edit', 'delete', 'optimize'],
            'dispatch': ['view', 'create', 'edit', 'assign', 'execute'],
            'vehicles': ['view', 'create', 'edit', 'delete', 'assign'],
            'drivers': ['view', 'create', 'edit', 'delete', 'assign'],
            'stops': ['view', 'create', 'edit', 'delete', 'checkin', 'complete'],
            'delivery_reports': ['view', 'export'],
            'alerts': ['view', 'create', 'edit', 'delete', 'resolve'],
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
            'scenarios': ['view', 'create', 'edit', 'delete', 'approve'],
            'alerts': ['view', 'create', 'edit', 'delete', 'resolve'],
            'reports': ['view', 'export'],
            'settings': ['view', 'edit'],
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
            'dashboard': ['view'],
            'inspections': ['view', 'create', 'edit', 'delete', 'approve', 'execute'],
            'ncr': ['view', 'create', 'edit', 'delete', 'approve', 'resolve', 'close'],
            'capa': ['view', 'create', 'edit', 'delete', 'approve', 'verify', 'close'],
            'audits': ['view', 'create', 'edit', 'delete', 'approve', 'execute', 'close'],
            'reports': ['view', 'export'],
            'settings': ['view', 'edit'],
            'audit_log': ['view', 'export'],
            'quality': ['view', 'create', 'edit', 'delete', 'approve', 'execute', 'verify', 'export', 'manage'],
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
                ('wms', 'shipments', 'view'),
                ('wms', 'shipments', 'ship'),
                ('wms', 'returns', 'view'),
                ('tasks', 'tasks', 'view'),
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
                else:
                    add_permission_to_role(role_id, module, resource, action)


# Initialize permissions when module is imported
initialize_permissions()
