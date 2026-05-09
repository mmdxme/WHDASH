"""
User Seeds for MMDx
====================
Creates demo/test users for all roles in the multi-layer RBAC system.

Run this script after initialize_permissions() has been called.

USAGE:
    from seed_users import seed_all_demo_users
    seed_all_demo_users()
"""

from werkzeug.security import generate_password_hash
from database import get_db_context

DEFAULT_PASSWORD = 'Welcome123!'

def _user_exists(username):
    """Check if user already exists."""
    with get_db_context() as db:
        result = db.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        return result is not None


def _get_role_id(role_name):
    """Get role ID by name."""
    with get_db_context() as db:
        result = db.execute(
            "SELECT id FROM roles WHERE role_name = ?", (role_name,)
        ).fetchone()
        return result['id'] if result else None


def _get_company_id(company_name='Main Company'):
    """Get company ID by name."""
    with get_db_context() as db:
        result = db.execute(
            "SELECT id FROM companies WHERE name = ?", (company_name,)
        ).fetchone()
        return result['id'] if result else None


def _get_warehouse_id(warehouse_name='Main Warehouse'):
    """Get warehouse ID by name."""
    with get_db_context() as db:
        result = db.execute(
            "SELECT id FROM warehouses WHERE name = ?", (warehouse_name,)
        ).fetchone()
        return result['id'] if result else None


def _create_user(username, email, full_name, role_name, company_name=None,
                department=None, job_title=None, warehouse_name=None,
                password=None, is_active=True):
    """Create a user if not exists."""
    if _user_exists(username):
        print(f"  [SKIP] User '{username}' already exists")
        return None

    role_id = _get_role_id(role_name)
    if not role_id:
        print(f"  [WARN] Role '{role_name}' not found for user '{username}'")
        return None

    company_id = _get_company_id(company_name) if company_name else None
    warehouse_id = _get_warehouse_id(warehouse_name) if warehouse_name else None

    password_hash = generate_password_hash(password or DEFAULT_PASSWORD)

    with get_db_context() as db:
        try:
            cursor = db.execute("""
                INSERT INTO users (username, email, password_hash, full_name,
                                 role_id, company_id, department, job_title,
                                 is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (username, email, password_hash, full_name, role_id, company_id,
                  department or '', job_title or '', 1 if is_active else 0))
            db.commit()
            user_id = cursor.lastrowid

            # Assign company access
            if company_id:
                db.execute("""
                    INSERT OR IGNORE INTO user_company_access (user_id, company_id, access_level)
                    VALUES (?, ?, 'read')
                """, (user_id, company_id))

            # Assign warehouse access
            if warehouse_id:
                db.execute("""
                    INSERT OR IGNORE INTO user_warehouse_access (user_id, warehouse_id, access_level)
                    VALUES (?, ?, 'read')
                """, (user_id, warehouse_id))

            db.commit()
            print(f"  [CREATED] User '{username}' with role '{role_name}'")
            return user_id
        except Exception as e:
            print(f"  [ERROR] Failed to create user '{username}': {e}")
            return None


def seed_all_demo_users():
    """Seed all demo users for all role layers."""
    print("\n" + "="*60)
    print("SEEDING MMDx DEMO USERS")
    print("="*60)

    # =========================================================================
    # GLOBAL / CROSS-SYSTEM USERS
    # =========================================================================
    print("\n[GLOBAL / CROSS-SYSTEM]")
    _create_user('super.admin', 'super@warehouse.local', 'Super Administrator', 'Super Admin')
    _create_user('global.admin', 'admin@warehouse.local', 'Global Administrator', 'Global Admin',
                 company_name='Main Company')
    _create_user('executive.viewer', 'exec@warehouse.local', 'Executive Viewer', 'Executive Viewer',
                 company_name='Main Company')
    _create_user('auditor.internal', 'auditor@warehouse.local', 'Internal Auditor', 'Internal Auditor',
                 company_name='Main Company')
    _create_user('compliance.viewer', 'compliance@warehouse.local', 'Compliance Reviewer',
                 'Compliance Reviewer', company_name='Main Company')

    # =========================================================================
    # WAREHOUSE / WMS USERS
    # =========================================================================
    print("\n[WAREHOUSE / WMS]")
    _create_user('warehouse.manager', 'warehouse.mgr@warehouse.local', 'Warehouse Manager',
                 'Warehouse Manager', warehouse_name='Main Warehouse')
    _create_user('warehouse.supervisor', 'warehouse.sv@warehouse.local', 'Warehouse Supervisor',
                 'Warehouse Supervisor', warehouse_name='Main Warehouse')
    _create_user('warehouse.assistant', 'warehouse.asst@warehouse.local', 'Warehouse Assistant',
                 'Warehouse Assistant', warehouse_name='Main Warehouse')
    _create_user('warehouse.operator', 'warehouse.op@warehouse.local', 'Warehouse Operator',
                 'Warehouse Operator', warehouse_name='Main Warehouse')
    _create_user('warehouse.viewer', 'warehouse.view@warehouse.local', 'Warehouse Viewer',
                 'Warehouse Viewer', warehouse_name='Main Warehouse')

    # =========================================================================
    # LOGISTICS / DELIVERY USERS
    # =========================================================================
    print("\n[LOGISTICS / DELIVERY]")
    _create_user('logistics.manager', 'logistics.mgr@warehouse.local', 'Logistics Manager',
                 'Logistics Manager', company_name='Main Company')
    _create_user('logistics.supervisor', 'logistics.sv@warehouse.local', 'Logistics Supervisor',
                 'Logistics Supervisor', company_name='Main Company')
    _create_user('logistics.assistant', 'logistics.asst@warehouse.local', 'Logistics Assistant',
                 'Logistics Assistant', company_name='Main Company')
    _create_user('logistics.coordinator', 'logistics.coord@warehouse.local', 'Logistics Coordinator',
                 'Logistics Coordinator', company_name='Main Company')
    _create_user('logistics.driver', 'logistics.driver@warehouse.local', 'Logistics Driver',
                 'Logistics Driver', company_name='Main Company')
    _create_user('logistics.viewer', 'logistics.view@warehouse.local', 'Logistics Viewer',
                 'Logistics Viewer', company_name='Main Company')

    # =========================================================================
    # PROCUREMENT / PURCHASING USERS
    # =========================================================================
    print("\n[PROCUREMENT / PURCHASING]")
    _create_user('procurement.manager', 'procurement.mgr@warehouse.local', 'Procurement Manager',
                 'Procurement Manager', company_name='Main Company')
    _create_user('procurement.supervisor', 'procurement.sv@warehouse.local', 'Procurement Supervisor',
                 'Procurement Supervisor', company_name='Main Company')
    _create_user('procurement.assistant', 'procurement.asst@warehouse.local', 'Procurement Assistant',
                 'Procurement Assistant', company_name='Main Company')
    _create_user('procurement.buyer', 'procurement.buyer@warehouse.local', 'Procurement Buyer',
                 'Procurement Buyer', company_name='Main Company')
    _create_user('procurement.viewer', 'procurement.view@warehouse.local', 'Procurement Viewer',
                 'Procurement Viewer', company_name='Main Company')

    # =========================================================================
    # FINANCE / ACCOUNTING USERS
    # =========================================================================
    print("\n[FINANCE / ACCOUNTING]")
    _create_user('finance.manager', 'finance.mgr@warehouse.local', 'Finance Manager',
                 'Finance Manager', company_name='Main Company')
    _create_user('finance.supervisor', 'finance.sv@warehouse.local', 'Finance Supervisor',
                 'Finance Supervisor', company_name='Main Company')
    _create_user('finance.assistant', 'finance.asst@warehouse.local', 'Finance Assistant',
                 'Finance Assistant', company_name='Main Company')
    _create_user('finance.accountant', 'finance.acct@warehouse.local', 'Finance Accountant',
                 'Finance Accountant', company_name='Main Company')
    _create_user('finance.ap.clerk', 'finance.ap@warehouse.local', 'Finance AP Clerk',
                 'Finance AP Clerk', company_name='Main Company')
    _create_user('finance.ar.clerk', 'finance.ar@warehouse.local', 'Finance AR Clerk',
                 'Finance AR Clerk', company_name='Main Company')
    _create_user('finance.viewer', 'finance.view@warehouse.local', 'Finance Viewer',
                 'Finance Viewer', company_name='Main Company')
    _create_user('finance.auditor', 'finance.auditor@warehouse.local', 'Finance Auditor',
                 'Finance Auditor', company_name='Main Company')

    # =========================================================================
    # HR / HUMAN RESOURCES USERS
    # =========================================================================
    print("\n[HR / HUMAN RESOURCES]")
    _create_user('hr.manager', 'hr.mgr@warehouse.local', 'HR Manager',
                 'HR Manager', company_name='Main Company', department='HR')
    _create_user('hr.supervisor', 'hr.sv@warehouse.local', 'HR Supervisor',
                 'HR Supervisor', company_name='Main Company', department='HR')
    _create_user('hr.assistant', 'hr.asst@warehouse.local', 'HR Assistant',
                 'HR Assistant', company_name='Main Company', department='HR')
    _create_user('hr.officer', 'hr.officer@warehouse.local', 'HR Officer',
                 'HR Officer', company_name='Main Company', department='HR')
    _create_user('payroll.manager', 'payroll.mgr@warehouse.local', 'Payroll Manager',
                 'Payroll Manager', company_name='Main Company', department='HR')
    _create_user('payroll.officer', 'payroll.officer@warehouse.local', 'Payroll Officer',
                 'Payroll Officer', company_name='Main Company', department='HR')
    _create_user('hr.viewer', 'hr.view@warehouse.local', 'HR Viewer',
                 'HR Viewer', company_name='Main Company', department='HR')
    _create_user('employee.demo', 'employee@warehouse.local', 'Demo Employee',
                 'Employee Self-Service', company_name='Main Company', department='Sales')

    # =========================================================================
    # ASSET MANAGEMENT USERS
    # =========================================================================
    print("\n[ASSET MANAGEMENT]")
    _create_user('asset.manager', 'asset.mgr@warehouse.local', 'Asset Manager',
                 'Asset Manager', company_name='Main Company')
    _create_user('asset.supervisor', 'asset.sv@warehouse.local', 'Asset Supervisor',
                 'Asset Supervisor', company_name='Main Company')
    _create_user('asset.accountant', 'asset.acct@warehouse.local', 'Asset Accountant',
                 'Asset Accountant', company_name='Main Company')
    _create_user('asset.assistant', 'asset.asst@warehouse.local', 'Asset Assistant',
                 'Asset Assistant', company_name='Main Company')
    _create_user('asset.operator', 'asset.op@warehouse.local', 'Asset Operator',
                 'Asset Operator', company_name='Main Company')
    _create_user('asset.viewer', 'asset.view@warehouse.local', 'Asset Viewer',
                 'Asset Viewer', company_name='Main Company')

    # =========================================================================
    # MAINTENANCE MANAGEMENT USERS
    # =========================================================================
    print("\n[MAINTENANCE MANAGEMENT]")
    _create_user('maintenance.manager', 'maint.mgr@warehouse.local', 'Maintenance Manager',
                 'Maintenance Manager', company_name='Main Company')
    _create_user('maintenance.supervisor', 'maint.sv@warehouse.local', 'Maintenance Supervisor',
                 'Maintenance Supervisor', company_name='Main Company')
    _create_user('maintenance.technician', 'maint.tech@warehouse.local', 'Maintenance Technician',
                 'Maintenance Technician', company_name='Main Company')
    _create_user('maintenance.planner', 'maint.planner@warehouse.local', 'Maintenance Planner',
                 'Maintenance Planner', company_name='Main Company')
    _create_user('maintenance.viewer', 'maint.view@warehouse.local', 'Maintenance Viewer',
                 'Maintenance Viewer', company_name='Main Company')

    # =========================================================================
    # QUALITY MANAGEMENT USERS
    # =========================================================================
    print("\n[QUALITY MANAGEMENT]")
    _create_user('quality.manager', 'quality.mgr@warehouse.local', 'Quality Manager',
                 'Quality Manager', company_name='Main Company')
    _create_user('quality.supervisor', 'quality.sv@warehouse.local', 'Quality Supervisor',
                 'Quality Supervisor', company_name='Main Company')
    _create_user('quality.inspector', 'quality.insp@warehouse.local', 'Quality Inspector',
                 'Quality Inspector', company_name='Main Company')
    _create_user('quality.auditor', 'quality.auditor@warehouse.local', 'Quality Auditor',
                 'Quality Auditor', company_name='Main Company')
    _create_user('quality.assistant', 'quality.asst@warehouse.local', 'Quality Assistant',
                 'Quality Assistant', company_name='Main Company')
    _create_user('quality.viewer', 'quality.view@warehouse.local', 'Quality Viewer',
                 'Quality Viewer', company_name='Main Company')

    # =========================================================================
    # SALES / CRM USERS
    # =========================================================================
    print("\n[SALES / CRM]")
    _create_user('sales.manager', 'sales.mgr@warehouse.local', 'Sales Manager',
                 'Sales Manager', company_name='Main Company', department='Sales')
    _create_user('sales.supervisor', 'sales.sv@warehouse.local', 'Sales Supervisor',
                 'Sales Supervisor', company_name='Main Company', department='Sales')
    _create_user('sales.assistant', 'sales.asst@warehouse.local', 'Sales Assistant',
                 'Sales Assistant', company_name='Main Company', department='Sales')
    _create_user('sales.executive', 'sales.exec@warehouse.local', 'Sales Executive',
                 'Sales Executive', company_name='Main Company', department='Sales')
    _create_user('crm.manager', 'crm.mgr@warehouse.local', 'CRM Manager',
                 'CRM Manager', company_name='Main Company', department='Sales')
    _create_user('crm.specialist', 'crm.spec@warehouse.local', 'CRM Specialist',
                 'CRM Specialist', company_name='Main Company', department='Sales')
    _create_user('sales.viewer', 'sales.view@warehouse.local', 'Sales Viewer',
                 'Sales Viewer', company_name='Main Company', department='Sales')

    # =========================================================================
    # MARKETING USERS
    # =========================================================================
    print("\n[MARKETING]")
    _create_user('marketing.manager', 'marketing.mgr@warehouse.local', 'Marketing Manager',
                 'Marketing Manager', company_name='Main Company', department='Marketing')
    _create_user('marketing.supervisor', 'marketing.sv@warehouse.local', 'Marketing Supervisor',
                 'Marketing Supervisor', company_name='Main Company', department='Marketing')
    _create_user('marketing.assistant', 'marketing.asst@warehouse.local', 'Marketing Assistant',
                 'Marketing Assistant', company_name='Main Company', department='Marketing')
    _create_user('marketing.specialist', 'marketing.spec@warehouse.local', 'Marketing Specialist',
                 'Marketing Specialist', company_name='Main Company', department='Marketing')
    _create_user('content.manager', 'content.mgr@warehouse.local', 'Content Manager',
                 'Content Manager', company_name='Main Company', department='Marketing')
    _create_user('marketing.viewer', 'marketing.view@warehouse.local', 'Marketing Viewer',
                 'Marketing Viewer', company_name='Main Company', department='Marketing')

    # =========================================================================
    # PLANNING / DEMAND PLANNING USERS
    # =========================================================================
    print("\n[PLANNING / DEMAND PLANNING]")
    _create_user('planning.manager', 'planning.mgr@warehouse.local', 'Planning Manager',
                 'Planning Manager', company_name='Main Company')
    _create_user('planning.analyst', 'planning.analyst@warehouse.local', 'Planning Analyst',
                 'Planning Analyst', company_name='Main Company')
    _create_user('planning.assistant', 'planning.asst@warehouse.local', 'Planning Assistant',
                 'Planning Assistant', company_name='Main Company')
    _create_user('planning.viewer', 'planning.view@warehouse.local', 'Planning Viewer',
                 'Planning Viewer', company_name='Main Company')

    # =========================================================================
    # WORKFLOW / BPM USERS
    # =========================================================================
    print("\n[WORKFLOW / BPM]")
    _create_user('workflow.admin', 'workflow.admin@warehouse.local', 'Workflow Administrator',
                 'Workflow Admin', company_name='Main Company')
    _create_user('workflow.supervisor', 'workflow.sv@warehouse.local', 'Workflow Supervisor',
                 'Workflow Supervisor', company_name='Main Company')
    _create_user('workflow.user', 'workflow.user@warehouse.local', 'Workflow User',
                 'Workflow User', company_name='Main Company')
    _create_user('workflow.viewer', 'workflow.view@warehouse.local', 'Workflow Viewer',
                 'Workflow Viewer', company_name='Main Company')

    # =========================================================================
    # DOCUMENTS / DMS USERS
    # =========================================================================
    print("\n[DOCUMENTS / DMS]")
    _create_user('documents.manager', 'docs.mgr@warehouse.local', 'Documents Manager',
                 'Documents Manager', company_name='Main Company')
    _create_user('documents.controller', 'docs.ctrl@warehouse.local', 'Documents Controller',
                 'Documents Controller', company_name='Main Company')
    _create_user('documents.assistant', 'docs.asst@warehouse.local', 'Documents Assistant',
                 'Documents Assistant', company_name='Main Company')
    _create_user('documents.user', 'docs.user@warehouse.local', 'Documents User',
                 'Documents User', company_name='Main Company')
    _create_user('documents.viewer', 'docs.view@warehouse.local', 'Documents Viewer',
                 'Documents Viewer', company_name='Main Company')

    # =========================================================================
    # E-COMMERCE USERS
    # =========================================================================
    print("\n[E-COMMERCE]")
    _create_user('ecommerce.manager', 'ecommerce.mgr@warehouse.local', 'E-commerce Manager',
                 'E-commerce Manager', company_name='Main Company')
    _create_user('ecommerce.coordinator', 'ecommerce.coord@warehouse.local', 'E-commerce Coordinator',
                 'E-commerce Coordinator', company_name='Main Company')
    _create_user('ecommerce.assistant', 'ecommerce.asst@warehouse.local', 'E-commerce Assistant',
                 'E-commerce Assistant', company_name='Main Company')
    _create_user('ecommerce.viewer', 'ecommerce.view@warehouse.local', 'E-commerce Viewer',
                 'E-commerce Viewer', company_name='Main Company')

    # =========================================================================
    # API GATEWAY USERS
    # =========================================================================
    print("\n[API GATEWAY]")
    _create_user('api.admin', 'api.admin@warehouse.local', 'API Gateway Admin',
                 'API Gateway Admin')
    _create_user('api.manager', 'api.mgr@warehouse.local', 'API Manager',
                 'API Manager')
    _create_user('api.support', 'api.support@warehouse.local', 'API Support User',
                 'API Support User')
    _create_user('api.viewer', 'api.view@warehouse.local', 'API Viewer',
                 'API Viewer')

    # =========================================================================
    # BI / REPORTS USERS
    # =========================================================================
    print("\n[BI / REPORTS]")
    _create_user('bi.manager', 'bi.mgr@warehouse.local', 'BI Manager',
                 'BI Manager', company_name='Main Company')
    _create_user('bi.analyst', 'bi.analyst@warehouse.local', 'BI Analyst',
                 'BI Analyst', company_name='Main Company')
    _create_user('bi.viewer', 'bi.view@warehouse.local', 'BI Viewer',
                 'BI Viewer', company_name='Main Company')
    _create_user('bi.steward', 'bi.steward@warehouse.local', 'BI Data Steward',
                 'BI Data Steward', company_name='Main Company')

    # =========================================================================
    # SOCIAL MEDIA USERS
    # =========================================================================
    print("\n[SOCIAL MEDIA]")
    _create_user('social.manager', 'social.mgr@warehouse.local', 'Social Media Manager',
                 'Social Media Manager', company_name='Main Company')
    _create_user('social.specialist', 'social.spec@warehouse.local', 'Social Media Specialist',
                 'Social Media Specialist', company_name='Main Company')
    _create_user('social.viewer', 'social.view@warehouse.local', 'Social Media Viewer',
                 'Social Media Viewer', company_name='Main Company')

    # =========================================================================
    # ADMIN / PLATFORM USERS
    # =========================================================================
    print("\n[ADMIN / PLATFORM]")
    _create_user('platform.admin', 'platform.admin@warehouse.local', 'Platform Administrator',
                 'Platform Admin')
    _create_user('user.admin', 'user.admin@warehouse.local', 'User & Role Administrator',
                 'User & Role Admin')
    _create_user('audit.viewer', 'audit.view@warehouse.local', 'Audit Viewer',
                 'Audit Viewer')

    print("\n" + "="*60)
    print("DEMO USERS SEEDING COMPLETE")
    print("="*60)
    print("\nDefault password for all demo users: Welcome123!")
    print("Please change passwords after first login.\n")


if __name__ == '__main__':
    seed_all_demo_users()
