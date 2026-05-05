"""
Seed Comprehensive Roles Data
=============================
This script seeds the database with all roles from the MMDx Role Matrix.
It populates the roles table with 20 categories of roles with proper sample data.
Run this after database initialization.

Usage:
    python seed_roles_comprehensive.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db_context, get_one, get_all

# Role Matrix Data - All 20 categories from ROLE_MATRIX.md
ROLE_MATRIX = {
    'GLOBAL': [
        {'name': 'Super Admin', 'code': 'super_admin', 'description': 'Full system control, all modules, all companies. Cannot be edited/deleted.', 'is_system': 1},
        {'name': 'Global Admin', 'code': 'global_admin', 'description': 'Platform administration, user/role management, settings', 'is_system': 1},
        {'name': 'Executive Viewer', 'code': 'executive_viewer', 'description': 'Read-only dashboards, executive summaries, reports', 'is_system': 1},
        {'name': 'Internal Auditor', 'code': 'internal_auditor', 'description': 'Read-only access to audit logs, compliance reports, financial summaries', 'is_system': 1},
        {'name': 'Compliance Reviewer', 'code': 'compliance_reviewer', 'description': 'Read-only access to audit logs, NCR, CAPA, quality records', 'is_system': 1},
    ],
    'WMS': [
        {'name': 'Warehouse Manager', 'code': 'warehouse_manager', 'description': 'Full warehouse visibility, approve transfers/adjustments, export reports, manage team', 'is_system': 0},
        {'name': 'Warehouse Supervisor', 'code': 'warehouse_supervisor', 'description': 'Manage daily operations, assign tasks, validate counts, confirm receipts/shipments', 'is_system': 0},
        {'name': 'Warehouse Assistant', 'code': 'warehouse_assistant', 'description': 'Prepare documents, update statuses, support transactions, upload attachments', 'is_system': 0},
        {'name': 'Warehouse Operator', 'code': 'warehouse_operator', 'description': 'Receive, pick, pack, move, count, update assigned operational records', 'is_system': 0},
        {'name': 'Warehouse Viewer', 'code': 'warehouse_viewer', 'description': 'Read-only access to inventory, reports and logs', 'is_system': 0},
    ],
    'LOGISTICS': [
        {'name': 'Logistics Manager', 'code': 'logistics_manager', 'description': 'Full logistics visibility, approve shipments, driver management, reports', 'is_system': 0},
        {'name': 'Logistics Supervisor', 'code': 'logistics_supervisor', 'description': 'Dispatch operations, trip management, route optimization, driver coordination', 'is_system': 0},
        {'name': 'Logistics Assistant', 'code': 'logistics_assistant', 'description': 'Prepare shipment documents, update follow-ups, documentation support', 'is_system': 0},
        {'name': 'Logistics Coordinator', 'code': 'logistics_coordinator', 'description': 'Coordinate deliveries, track shipments, handle exceptions', 'is_system': 0},
        {'name': 'Logistics Driver', 'code': 'logistics_driver', 'description': 'View assigned trips, update delivery status, check-in at stops', 'is_system': 0},
        {'name': 'Logistics Viewer', 'code': 'logistics_viewer', 'description': 'Read-only access to trips, routes, delivery reports', 'is_system': 0},
    ],
    'PROCUREMENT': [
        {'name': 'Procurement Manager', 'code': 'procurement_manager', 'description': 'Approve PR/RFQ/PO, supplier performance, contracts, final approval', 'is_system': 0},
        {'name': 'Procurement Supervisor', 'code': 'procurement_supervisor', 'description': 'Review drafts, assign buyers, monitor due dates, second-level approval', 'is_system': 0},
        {'name': 'Procurement Assistant', 'code': 'procurement_assistant', 'description': 'Prepare RFQ/PO drafts, upload quotations, update follow-ups', 'is_system': 0},
        {'name': 'Procurement Buyer', 'code': 'procurement_buyer', 'description': 'Create requisitions, request quotes, work assigned purchase orders', 'is_system': 0},
        {'name': 'Procurement Viewer', 'code': 'procurement_viewer', 'description': 'Read-only access to suppliers, contracts, procurement reports', 'is_system': 0},
    ],
    'FINANCE': [
        {'name': 'Finance Manager', 'code': 'finance_manager', 'description': 'Broad visibility, approvals, posting, closing, financial reporting', 'is_system': 0},
        {'name': 'Finance Supervisor', 'code': 'finance_supervisor', 'description': 'Review entries, supervise billing/payment workflow, reconcile', 'is_system': 0},
        {'name': 'Finance Assistant', 'code': 'finance_assistant', 'description': 'Prepare bills/invoices/receipts, reconciliation support, data entry', 'is_system': 0},
        {'name': 'Finance Accountant', 'code': 'finance_accountant', 'description': 'Daily operational accounting by assigned scope, journal entries', 'is_system': 0},
        {'name': 'Finance AP Clerk', 'code': 'finance_ap_clerk', 'description': 'Process payables, payments, vendor invoices', 'is_system': 0},
        {'name': 'Finance AR Clerk', 'code': 'finance_ar_clerk', 'description': 'Process receivables, receipts, customer invoices', 'is_system': 0},
        {'name': 'Finance Viewer', 'code': 'finance_viewer', 'description': 'Read-only financial review, reports, dashboards', 'is_system': 0},
        {'name': 'Finance Auditor', 'code': 'finance_auditor', 'description': 'Read-only access to journals, audit logs, financial records', 'is_system': 0},
    ],
    'HR': [
        {'name': 'HR Manager', 'code': 'hr_manager', 'description': 'Full HR visibility, employee management, leave/attendance approval, payroll final', 'is_system': 0},
        {'name': 'HR Supervisor', 'code': 'hr_supervisor', 'description': 'Attendance/leave review, team administration, recruitment screening', 'is_system': 0},
        {'name': 'HR Assistant', 'code': 'hr_assistant', 'description': 'Employee document updates, onboarding support, leave processing, data entry', 'is_system': 0},
        {'name': 'HR Officer', 'code': 'hr_officer', 'description': 'Day-to-day HR operations, attendance management, leave tracking', 'is_system': 0},
        {'name': 'Payroll Manager', 'code': 'payroll_manager', 'description': 'Full payroll access, salary processing, tax calculations, disbursements', 'is_system': 0},
        {'name': 'Payroll Officer', 'code': 'payroll_officer', 'description': 'Prepare payroll, calculate overtime, benefits administration', 'is_system': 0},
        {'name': 'HR Viewer', 'code': 'hr_viewer', 'description': 'Read-only access to employee lists, leave balances, reports', 'is_system': 0},
        {'name': 'Employee Self-Service', 'code': 'employee_self_service', 'description': 'View own profile, submit leave requests, view own attendance', 'is_system': 0},
    ],
    'ASSETS': [
        {'name': 'Asset Manager', 'code': 'asset_manager', 'description': 'Full asset visibility, acquisitions, disposals, depreciation, team oversight', 'is_system': 0},
        {'name': 'Asset Supervisor', 'code': 'asset_supervisor', 'description': 'Asset maintenance tracking, depreciation run review, transfers approval', 'is_system': 0},
        {'name': 'Asset Accountant', 'code': 'asset_accountant', 'description': 'Depreciation calculations, asset valuations, financial reporting', 'is_system': 0},
        {'name': 'Asset Assistant', 'code': 'asset_assistant', 'description': 'Prepare acquisition documents, update asset records, maintenance logs', 'is_system': 0},
        {'name': 'Asset Operator', 'code': 'asset_operator', 'description': 'Record asset usage, submit maintenance requests, physical counts', 'is_system': 0},
        {'name': 'Asset Viewer', 'code': 'asset_viewer', 'description': 'Read-only access to asset register, depreciation schedules', 'is_system': 0},
    ],
    'MAINTENANCE': [
        {'name': 'Maintenance Manager', 'code': 'maintenance_manager', 'description': 'Full maintenance visibility, approve work orders, PM schedules, costs', 'is_system': 0},
        {'name': 'Maintenance Supervisor', 'code': 'maintenance_supervisor', 'description': 'Manage technicians, assign work orders, review completion', 'is_system': 0},
        {'name': 'Maintenance Technician', 'code': 'maintenance_technician', 'description': 'Execute work orders, update task completion, log parts usage', 'is_system': 0},
        {'name': 'Maintenance Planner', 'code': 'maintenance_planner', 'description': 'Schedule PM plans, create work orders, parts planning', 'is_system': 0},
        {'name': 'Maintenance Viewer', 'code': 'maintenance_viewer', 'description': 'Read-only access to work orders, equipment, maintenance reports', 'is_system': 0},
    ],
    'QUALITY': [
        {'name': 'Quality Manager', 'code': 'quality_manager', 'description': 'Full quality visibility, NCR/CAPA approval, audit scheduling, reports', 'is_system': 0},
        {'name': 'Quality Supervisor', 'code': 'quality_supervisor', 'description': 'Inspections oversight, NCR review, CAPA tracking', 'is_system': 0},
        {'name': 'Quality Inspector', 'code': 'quality_inspector', 'description': 'Execute inspections, create NCRs, verify quality standards', 'is_system': 0},
        {'name': 'Quality Auditor', 'code': 'quality_auditor', 'description': 'Conduct audits, document findings, track CAPA effectiveness', 'is_system': 0},
        {'name': 'Quality Assistant', 'code': 'quality_assistant', 'description': 'Prepare inspection documents, update records, support audits', 'is_system': 0},
        {'name': 'Quality Viewer', 'code': 'quality_viewer', 'description': 'Read-only access to inspections, NCR, CAPA, audit logs', 'is_system': 0},
    ],
    'SALES': [
        {'name': 'Sales Manager', 'code': 'sales_manager', 'description': 'Sales dashboards, customer approvals, quotation oversight, team management', 'is_system': 0},
        {'name': 'Sales Supervisor', 'code': 'sales_supervisor', 'description': 'Team pipeline supervision, quotation review, order follow-up', 'is_system': 0},
        {'name': 'Sales Assistant', 'code': 'sales_assistant', 'description': 'Data entry, quote preparation, documentation, follow-up', 'is_system': 0},
        {'name': 'Sales Executive', 'code': 'sales_executive', 'description': 'Customer operations, quotations, orders within scope', 'is_system': 0},
        {'name': 'CRM Manager', 'code': 'crm_manager', 'description': 'Customer data, segments, customer intelligence oversight', 'is_system': 0},
        {'name': 'CRM Specialist', 'code': 'crm_specialist', 'description': 'Customer profiling, segmentation, activity tracking', 'is_system': 0},
        {'name': 'Sales Viewer', 'code': 'sales_viewer', 'description': 'Read-only access to customers, quotations, orders, reports', 'is_system': 0},
    ],
    'MARKETING': [
        {'name': 'Marketing Manager', 'code': 'marketing_manager', 'description': 'Full marketing visibility, campaign approvals, budget control, team oversight', 'is_system': 0},
        {'name': 'Marketing Supervisor', 'code': 'marketing_supervisor', 'description': 'Campaign coordination, lead management, content approval', 'is_system': 0},
        {'name': 'Marketing Assistant', 'code': 'marketing_assistant', 'description': 'Prepare campaign content, manage leads, social media posts', 'is_system': 0},
        {'name': 'Marketing Specialist', 'code': 'marketing_specialist', 'description': 'Execute campaigns, track leads, manage channels', 'is_system': 0},
        {'name': 'Content Manager', 'code': 'content_manager', 'description': 'Approve/publish content, manage templates, brand consistency', 'is_system': 0},
        {'name': 'Marketing Viewer', 'code': 'marketing_viewer', 'description': 'Read-only access to campaigns, leads, reports, analytics', 'is_system': 0},
    ],
    'PLANNING': [
        {'name': 'Planning Manager', 'code': 'planning_manager', 'description': 'Full planning visibility, forecast approval, replenishment decisions', 'is_system': 0},
        {'name': 'Planning Analyst', 'code': 'planning_analyst', 'description': 'Create forecasts, analyze demand, run replenishment scenarios', 'is_system': 0},
        {'name': 'Planning Assistant', 'code': 'planning_assistant', 'description': 'Prepare planning data, update parameters, support analysis', 'is_system': 0},
        {'name': 'Planning Viewer', 'code': 'planning_viewer', 'description': 'Read-only access to forecasts, demand plans, replenishment', 'is_system': 0},
    ],
    'WORKFLOW': [
        {'name': 'Workflow Admin', 'code': 'workflow_admin', 'description': 'Full workflow visibility, designer access, process modeling', 'is_system': 0},
        {'name': 'Workflow Supervisor', 'code': 'workflow_supervisor', 'description': 'Monitor instances, handle escalations, approve/reject', 'is_system': 0},
        {'name': 'Workflow User', 'code': 'workflow_user', 'description': 'Access assigned work items, complete tasks, submit for approval', 'is_system': 0},
        {'name': 'Workflow Viewer', 'code': 'workflow_viewer', 'description': 'Read-only access to workflow dashboard, monitoring', 'is_system': 0},
    ],
    'DOCUMENTS': [
        {'name': 'Documents Manager', 'code': 'documents_manager', 'description': 'Full document visibility, access control, retention policies', 'is_system': 0},
        {'name': 'Documents Controller', 'code': 'documents_controller', 'description': 'Manage document categories, templates, signature workflows', 'is_system': 0},
        {'name': 'Documents Assistant', 'code': 'documents_assistant', 'description': 'Upload documents, update versions, manage links', 'is_system': 0},
        {'name': 'Documents User', 'code': 'documents_user', 'description': 'View/upload own documents, request signatures', 'is_system': 0},
        {'name': 'Documents Viewer', 'code': 'documents_viewer', 'description': 'Read-only access to documents library', 'is_system': 0},
    ],
    'ECOMMERCE': [
        {'name': 'E-commerce Manager', 'code': 'ecommerce_manager', 'description': 'Full e-commerce visibility, channel management, order approvals', 'is_system': 0},
        {'name': 'E-commerce Coordinator', 'code': 'ecommerce_coordinator', 'description': 'Manage orders, sync inventory, handle exceptions', 'is_system': 0},
        {'name': 'E-commerce Assistant', 'code': 'ecommerce_assistant', 'description': 'Process orders, update status, customer communication', 'is_system': 0},
        {'name': 'E-commerce Viewer', 'code': 'ecommerce_viewer', 'description': 'Read-only access to orders, channels, reports', 'is_system': 0},
    ],
    'API': [
        {'name': 'API Gateway Admin', 'code': 'api_gateway_admin', 'description': 'Full API visibility, client management, rate limits, monitoring', 'is_system': 0},
        {'name': 'API Manager', 'code': 'api_manager', 'description': 'Manage API routes, versions, documentation', 'is_system': 0},
        {'name': 'API Support User', 'code': 'api_support_user', 'description': 'View logs, monitor health, manage webhooks', 'is_system': 0},
        {'name': 'API Viewer', 'code': 'api_viewer', 'description': 'Read-only access to API routes, logs, monitoring', 'is_system': 0},
    ],
    'BI': [
        {'name': 'BI Manager', 'code': 'bi_manager', 'description': 'Full BI visibility, dataset management, scheduled reports', 'is_system': 0},
        {'name': 'BI Analyst', 'code': 'bi_analyst', 'description': 'Create reports, run adhoc queries, manage KPIs', 'is_system': 0},
        {'name': 'BI Viewer', 'code': 'bi_viewer', 'description': 'View dashboards, executive reports, standard reports', 'is_system': 0},
        {'name': 'BI Data Steward', 'code': 'bi_data_steward', 'description': 'Manage datasets, data quality, import/export', 'is_system': 0},
    ],
    'SOCIAL': [
        {'name': 'Social Media Manager', 'code': 'social_media_manager', 'description': 'Full social media visibility, approve content, manage accounts', 'is_system': 0},
        {'name': 'Social Media Specialist', 'code': 'social_media_specialist', 'description': 'Create content, manage calendar, publish posts', 'is_system': 0},
        {'name': 'Social Media Viewer', 'code': 'social_media_viewer', 'description': 'Read-only access to content, engagement reports', 'is_system': 0},
    ],
    'ADMIN': [
        {'name': 'Platform Admin', 'code': 'platform_admin', 'description': 'System settings, localization, numbering, notifications', 'is_system': 0},
        {'name': 'User & Role Admin', 'code': 'user_role_admin', 'description': 'Manage users, roles, permissions, access scopes', 'is_system': 0},
        {'name': 'Audit Viewer', 'code': 'audit_viewer', 'description': 'View audit logs, system logs', 'is_system': 0},
    ],
    'COMPANY': [
        {'name': 'Company Admin', 'code': 'company_admin', 'description': 'Manage company, branches, departments', 'is_system': 0},
        {'name': 'Branch Manager', 'code': 'branch_manager', 'description': 'Full branch visibility, branch operations', 'is_system': 0},
        {'name': 'Department Manager', 'code': 'department_manager', 'description': 'Department oversight, team management', 'is_system': 0},
    ],
}

# Default permissions per role group
DEFAULT_PERMISSIONS = {
    'GLOBAL': [('platform', '*', '*')],
    'WMS': [('wms', '*', '*')],
    'LOGISTICS': [('logistics', '*', '*')],
    'PROCUREMENT': [('procurement', '*', '*')],
    'FINANCE': [('finance', '*', '*')],
    'HR': [('hr', '*', '*')],
    'ASSETS': [('assets', '*', '*')],
    'MAINTENANCE': [('maintenance', '*', '*')],
    'QUALITY': [('quality', '*', '*')],
    'SALES': [('sales', '*', '*'), ('crm', '*', '*')],
    'MARKETING': [('marketing', '*', '*')],
    'PLANNING': [('planning', '*', '*')],
    'WORKFLOW': [('workflow', '*', '*')],
    'DOCUMENTS': [('documents', '*', '*')],
    'ECOMMERCE': [('ecommerce', '*', '*')],
    'API': [('api', '*', '*')],
    'BI': [('bi', '*', '*')],
    'SOCIAL': [('social_media', '*', '*')],
    'ADMIN': [('platform', '*', '*')],
    'COMPANY': [('company', '*', '*')],
}


def seed_roles():
    """Seed all roles from ROLE_MATRIX."""
    print("=" * 60)
    print("Seeding Comprehensive Roles Data")
    print("=" * 60)
    
    total_created = 0
    total_updated = 0
    
    with get_db_context() as db:
        # First ensure the new columns exist
        try:
            db.execute("ALTER TABLE roles ADD COLUMN role_group TEXT DEFAULT 'GENERAL'")
        except:
            pass
        try:
            db.execute("ALTER TABLE roles ADD COLUMN role_class TEXT DEFAULT 'General'")
        except:
            pass
        try:
            db.execute("ALTER TABLE roles ADD COLUMN valid_from TEXT DEFAULT '2020-01-01'")
        except:
            pass
        try:
            db.execute("ALTER TABLE roles ADD COLUMN valid_to TEXT DEFAULT '9999-12-31'")
        except:
            pass
        
        db.commit()
    
    for group, roles in ROLE_MATRIX.items():
        print(f"\n{group}:")
        for role_data in roles:
            # Check if role already exists
            existing = get_one(
                "SELECT id FROM roles WHERE role_name = ?",
                (role_data['name'],)
            )
            
            if existing:
                # Update existing role
                with get_db_context() as db:
                    db.execute("""
                        UPDATE roles SET 
                            description = ?,
                            role_group = ?,
                            is_system = ?
                        WHERE id = ?
                    """, (
                        role_data['description'],
                        group,
                        role_data['is_system'],
                        existing['id']
                    ))
                    db.commit()
                print(f"  [UPDATE] {role_data['name']}")
                total_updated += 1
            else:
                # Create new role
                with get_db_context() as db:
                    cursor = db.execute("""
                        INSERT INTO roles (role_name, description, role_group, role_class, 
                                          valid_from, valid_to, is_system)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        role_data['name'],
                        role_data['description'],
                        group,
                        'General',
                        '2020-01-01',
                        '9999-12-31',
                        role_data['is_system']
                    ))
                    db.commit()
                    role_id = cursor.lastrowid
                    
                    # Add default permissions for this role group
                    if group in DEFAULT_PERMISSIONS:
                        for mod, res, act in DEFAULT_PERMISSIONS[group]:
                            if act == '*':
                                # Add all actions for this module/resource
                                actions = ['view', 'create', 'edit', 'delete', 'approve', 'export']
                                for a in actions:
                                    db.execute("""
                                        INSERT INTO role_permissions (role_id, module, resource, action)
                                        VALUES (?, ?, ?, ?)
                                    """, (role_id, mod, res, a))
                            else:
                                db.execute("""
                                    INSERT INTO role_permissions (role_id, module, resource, action)
                                    VALUES (?, ?, ?, ?)
                                """, (role_id, mod, res, act))
                        db.commit()
                
                print(f"  [CREATE] {role_data['name']} (ID: {role_id})")
                total_created += 1
    
    print(f"\n{'=' * 60}")
    print(f"Summary:")
    print(f"  Total Created: {total_created}")
    print(f"  Total Updated: {total_updated}")
    print(f"  Total Roles: {total_created + total_updated}")
    print("=" * 60)
    
    return total_created, total_updated


if __name__ == '__main__':
    seed_roles()