"""
Workflow / BPM Demo Data Seeder
================================
This script seeds the Workflow module with realistic demo data for testing and demonstration.

Run this script after the database is initialized to populate workflow definitions,
instances, automation rules, notification templates, SLA rules, and more.

Usage:
    python seed_workflow_data.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from database import get_db_context, get_one, get_all, log_audit

def seed_workflow_data():
    """Seed comprehensive demo data for the Workflow/BPM module."""
    
    print("Seeding Workflow/BPM demo data...")
    
    with get_db_context() as db:
        # Check if workflow_definitions table exists
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t['name'] for t in tables]
        
        if 'workflow_definitions' not in table_names:
            print("Error: workflow_definitions table not found. Run initialize_workflow_schema() first.")
            return False
        
        # Check if already seeded
        existing = db.execute("SELECT COUNT(*) as cnt FROM workflow_definitions").fetchone()
        if existing['cnt'] > 0:
            print("Workflow data already exists. Skipping...")
            return True
        
        # =====================================================================
        # SEED WORKFLOW DEFINITIONS
        # =====================================================================
        print("Creating workflow definitions...")
        
        workflows = [
            {
                'workflow_type': 'sales_order_approval',
                'name': 'Sales Order Approval',
                'description': 'Multi-step approval workflow for sales orders based on amount thresholds',
                'module': 'SALES',
                'entity_type': 'sales_order',
                'version': 1,
                'is_active': 1,
                'requires_approval': 1,
                'company_scope': None,
                'branch_scope': None,
                'department_scope': None,
                'warehouse_scope': None,
                'created_by': 1,
                'updated_by': 1,
                'approved_by': 1,
                'approved_at': datetime.now().isoformat()
            },
            {
                'workflow_type': 'purchase_order_approval',
                'name': 'Purchase Order Approval',
                'description': 'Approval workflow for purchase orders with cost center routing',
                'module': 'PROCUREMENT',
                'entity_type': 'purchase_order',
                'version': 1,
                'is_active': 1,
                'requires_approval': 1,
                'company_scope': None,
                'branch_scope': None,
                'department_scope': None,
                'warehouse_scope': None,
                'created_by': 1,
                'updated_by': 1,
                'approved_by': 1,
                'approved_at': datetime.now().isoformat()
            },
            {
                'workflow_type': 'leave_request_approval',
                'name': 'Leave Request Approval',
                'description': 'Employee leave request approval with manager hierarchy',
                'module': 'HR',
                'entity_type': 'leave_request',
                'version': 1,
                'is_active': 1,
                'requires_approval': 1,
                'company_scope': None,
                'branch_scope': None,
                'department_scope': None,
                'warehouse_scope': None,
                'created_by': 1,
                'updated_by': 1,
                'approved_by': 1,
                'approved_at': datetime.now().isoformat()
            },
            {
                'workflow_type': 'expense_approval',
                'name': 'Expense Report Approval',
                'description': 'Approval workflow for employee expense reports',
                'module': 'FINANCE',
                'entity_type': 'expense_report',
                'version': 1,
                'is_active': 1,
                'requires_approval': 1,
                'company_scope': None,
                'branch_scope': None,
                'department_scope': None,
                'warehouse_scope': None,
                'created_by': 1,
                'updated_by': 1,
                'approved_by': 1,
                'approved_at': datetime.now().isoformat()
            },
            {
                'workflow_type': 'asset_disposal_approval',
                'name': 'Asset Disposal Approval',
                'description': 'Approval workflow for fixed asset disposal requests',
                'module': 'ASSETS',
                'entity_type': 'disposal_request',
                'version': 1,
                'is_active': 1,
                'requires_approval': 1,
                'company_scope': None,
                'branch_scope': None,
                'department_scope': None,
                'warehouse_scope': None,
                'created_by': 1,
                'updated_by': 1,
                'approved_by': 1,
                'approved_at': datetime.now().isoformat()
            },
            {
                'workflow_type': 'quote_discount_approval',
                'name': 'Quote Discount Approval',
                'description': 'Special discount approval for sales quotations',
                'module': 'SALES',
                'entity_type': 'quotation',
                'version': 1,
                'is_active': 1,
                'requires_approval': 1,
                'company_scope': None,
                'branch_scope': None,
                'department_scope': None,
                'warehouse_scope': None,
                'created_by': 1,
                'updated_by': 1,
                'approved_by': 1,
                'approved_at': datetime.now().isoformat()
            }
        ]
        
        workflow_ids = {}
        for wf in workflows:
            cursor = db.execute("""
                INSERT INTO workflow_definitions 
                (workflow_type, name, description, module, entity_type, version, is_active, 
                 requires_approval, company_scope, branch_scope, department_scope, warehouse_scope,
                 created_by, created_at, updated_by, approved_by, approved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                wf['workflow_type'], wf['name'], wf['description'], wf['module'],
                wf['entity_type'], wf['version'], wf['is_active'], wf['requires_approval'],
                wf['company_scope'], wf['branch_scope'], wf['department_scope'], wf['warehouse_scope'],
                wf['created_by'], datetime.now().isoformat(), wf['updated_by'],
                wf['approved_by'], wf['approved_at']
            ))
            workflow_ids[wf['workflow_type']] = cursor.lastrowid
            print(f"  Created: {wf['name']}")
        
        # =====================================================================
        # SEED WORKFLOW STEPS
        # =====================================================================
        print("Creating workflow steps...")
        
        steps_data = [
            # Sales Order Approval Steps
            ('sales_order_approval', [
                {'step_code': 'SA_SALES_MGR', 'step_name': 'Sales Manager Review', 'step_order': 1, 
                 'step_type': 'approval', 'assignee_type': 'role', 'assignee_id': 6, 
                 'due_duration_hours': 24, 'allow_approve': 1, 'allow_reject': 1, 'allow_return': 1},
                {'step_code': 'SA_FINANCE', 'step_name': 'Finance Review', 'step_order': 2,
                 'step_type': 'approval', 'assignee_type': 'role', 'assignee_id': 7,
                 'due_duration_hours': 48, 'allow_approve': 1, 'allow_reject': 1, 'allow_return': 1},
                {'step_code': 'SA_NOTIFY', 'step_name': 'Send Notification', 'step_order': 3,
                 'step_type': 'notification', 'assignee_type': 'dynamic', 'assignee_id': None,
                 'due_duration_hours': 1, 'allow_approve': 0, 'allow_reject': 0, 'allow_return': 0},
            ]),
            # Purchase Order Approval Steps
            ('purchase_order_approval', [
                {'step_code': 'PA_PURCH_MGR', 'step_name': 'Purchasing Manager Review', 'step_order': 1,
                 'step_type': 'approval', 'assignee_type': 'role', 'assignee_id': 9,
                 'due_duration_hours': 24, 'allow_approve': 1, 'allow_reject': 1, 'allow_return': 1},
                {'step_code': 'PA_FINANCE', 'step_name': 'Finance Approval', 'step_order': 2,
                 'step_type': 'approval', 'assignee_type': 'role', 'assignee_id': 7,
                 'due_duration_hours': 48, 'allow_approve': 1, 'allow_reject': 1, 'allow_return': 1},
            ]),
            # Leave Request Approval Steps
            ('leave_request_approval', [
                {'step_code': 'LR_MGR', 'step_name': 'Manager Approval', 'step_order': 1,
                 'step_type': 'approval', 'assignee_type': 'supervisor', 'assignee_id': None,
                 'due_duration_hours': 48, 'allow_approve': 1, 'allow_reject': 1, 'allow_return': 1},
                {'step_code': 'LR_HR', 'step_name': 'HR Review', 'step_order': 2,
                 'step_type': 'approval', 'assignee_type': 'role', 'assignee_id': 8,
                 'due_duration_hours': 24, 'allow_approve': 1, 'allow_reject': 1, 'allow_return': 1},
            ]),
            # Expense Approval Steps
            ('expense_approval', [
                {'step_code': 'EX_MGR', 'step_name': 'Manager Approval', 'step_order': 1,
                 'step_type': 'approval', 'assignee_type': 'supervisor', 'assignee_id': None,
                 'due_duration_hours': 24, 'allow_approve': 1, 'allow_reject': 1, 'allow_return': 1},
                {'step_code': 'EX_FINANCE', 'step_name': 'Finance Review', 'step_order': 2,
                 'step_type': 'approval', 'assignee_type': 'role', 'assignee_id': 7,
                 'due_duration_hours': 72, 'allow_approve': 1, 'allow_reject': 1, 'allow_return': 1},
            ]),
            # Asset Disposal Steps
            ('asset_disposal_approval', [
                {'step_code': 'AD_ASSET_MGR', 'step_name': 'Asset Manager Review', 'step_order': 1,
                 'step_type': 'approval', 'assignee_type': 'role', 'assignee_id': 5,
                 'due_duration_hours': 24, 'allow_approve': 1, 'allow_reject': 1, 'allow_return': 1},
                {'step_code': 'AD_FINANCE', 'step_name': 'Finance Approval', 'step_order': 2,
                 'step_type': 'approval', 'assignee_type': 'role', 'assignee_id': 7,
                 'due_duration_hours': 48, 'allow_approve': 1, 'allow_reject': 1, 'allow_return': 1},
                {'step_code': 'AD_GM', 'step_name': 'General Manager Approval', 'step_order': 3,
                 'step_type': 'approval', 'assignee_type': 'role', 'assignee_id': 1,
                 'due_duration_hours': 72, 'allow_approve': 1, 'allow_reject': 1, 'allow_return': 1},
            ]),
            # Quote Discount Steps
            ('quote_discount_approval', [
                {'step_code': 'QD_SALES_MGR', 'step_name': 'Sales Manager Discount Approval', 'step_order': 1,
                 'step_type': 'approval', 'assignee_type': 'role', 'assignee_id': 6,
                 'due_duration_hours': 12, 'allow_approve': 1, 'allow_reject': 1, 'allow_return': 1},
            ]),
        ]
        
        step_ids = {}
        for wf_type, steps in steps_data:
            wf_id = workflow_ids.get(wf_type)
            if not wf_id:
                continue
            step_ids[wf_type] = []
            for step in steps:
                cursor = db.execute("""
                    INSERT INTO workflow_steps 
                    (workflow_definition_id, step_code, step_name, step_order, step_type,
                     assignee_type, assignee_id, due_duration_hours, allow_approve, allow_reject, allow_return,
                     escalation_enabled, require_comments, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    wf_id, step['step_code'], step['step_name'], step['step_order'], step['step_type'],
                    step['assignee_type'], step['assignee_id'], step['due_duration_hours'],
                    step['allow_approve'], step['allow_reject'], step['allow_return'],
                    1 if step['step_type'] == 'approval' else 0,
                    1 if step['allow_reject'] else 0,
                    datetime.now().isoformat()
                ))
                step_ids[wf_type].append(cursor.lastrowid)
                print(f"    Step: {step['step_name']} for {wf_type}")
        
        # =====================================================================
        # SEED WORKFLOW INSTANCES
        # =====================================================================
        print("Creating workflow instances...")
        
        instances = [
            {'workflow_type': 'sales_order_approval', 'instance_code': 'WF-SO-00001', 
             'source_entity_type': 'Sales Order', 'source_entity_id': 101,
             'current_state': 'pending', 'current_step_order': 1,
             'requester_id': 3, 'requester_name': 'John Smith',
             'assigned_to_id': 6, 'assigned_to_type': 'role', 'assigned_to_name': 'Sales Manager',
             'due_date': (datetime.now() + timedelta(hours=20)).isoformat(),
             'priority': 'high', 'context_json': '{"amount": 45000, "customer": "ABC Corp"}'},
            {'workflow_type': 'sales_order_approval', 'instance_code': 'WF-SO-00002',
             'source_entity_type': 'Sales Order', 'source_entity_id': 102,
             'current_state': 'pending', 'current_step_order': 2,
             'requester_id': 4, 'requester_name': 'Sarah Johnson',
             'assigned_to_id': 7, 'assigned_to_type': 'role', 'assigned_to_name': 'Finance Manager',
             'due_date': (datetime.now() + timedelta(hours=40)).isoformat(),
             'priority': 'medium', 'context_json': '{"amount": 120000, "customer": "XYZ Ltd"}'},
            {'workflow_type': 'purchase_order_approval', 'instance_code': 'WF-PO-00001',
             'source_entity_type': 'Purchase Order', 'source_entity_id': 201,
             'current_state': 'pending', 'current_step_order': 1,
             'requester_id': 5, 'requester_name': 'Mike Wilson',
             'assigned_to_id': 9, 'assigned_to_type': 'role', 'assigned_to_name': 'Purchasing Manager',
             'due_date': (datetime.now() + timedelta(hours=18)).isoformat(),
             'priority': 'high', 'context_json': '{"amount": 75000, "supplier": "Tech Supplies Co"}'},
            {'workflow_type': 'purchase_order_approval', 'instance_code': 'WF-PO-00002',
             'source_entity_type': 'Purchase Order', 'source_entity_id': 202,
             'current_state': 'approved', 'current_step_order': 2,
             'requester_id': 3, 'requester_name': 'John Smith',
             'assigned_to_id': 7, 'assigned_to_type': 'role', 'assigned_to_name': 'Finance Manager',
             'due_date': (datetime.now() - timedelta(hours=12)).isoformat(),
             'priority': 'medium', 'context_json': '{"amount": 25000, "supplier": "Office Essentials"}'},
            {'workflow_type': 'leave_request_approval', 'instance_code': 'WF-LV-00001',
             'source_entity_type': 'Leave Request', 'source_entity_id': 301,
             'current_state': 'pending', 'current_step_order': 1,
             'requester_id': 6, 'requester_name': 'Emily Brown',
             'assigned_to_id': 2, 'assigned_to_type': 'user', 'assigned_to_name': 'Department Manager',
             'due_date': (datetime.now() + timedelta(hours=36)).isoformat(),
             'priority': 'low', 'context_json': '{"leave_type": "Annual Leave", "days": 5}'},
            {'workflow_type': 'expense_approval', 'instance_code': 'WF-EX-00001',
             'source_entity_type': 'Expense Report', 'source_entity_id': 401,
             'current_state': 'escalated', 'current_step_order': 1,
             'requester_id': 4, 'requester_name': 'Sarah Johnson',
             'assigned_to_id': 2, 'assigned_to_type': 'user', 'assigned_to_name': 'Department Manager',
             'due_date': (datetime.now() - timedelta(hours=48)).isoformat(),
             'escalation_level': 2, 'escalation_count': 2,
             'priority': 'high', 'context_json': '{"total_amount": 3500, "expense_type": "Travel"}'},
            {'workflow_type': 'quote_discount_approval', 'instance_code': 'WF-QD-00001',
             'source_entity_type': 'Quotation', 'source_entity_id': 501,
             'current_state': 'pending', 'current_step_order': 1,
             'requester_id': 3, 'requester_name': 'John Smith',
             'assigned_to_id': 6, 'assigned_to_type': 'role', 'assigned_to_name': 'Sales Manager',
             'due_date': (datetime.now() + timedelta(hours=8)).isoformat(),
             'priority': 'critical', 'context_json': '{"discount_percent": 25, "original_total": 80000}'},
            {'workflow_type': 'asset_disposal_approval', 'instance_code': 'WF-AD-00001',
             'source_entity_type': 'Disposal Request', 'source_entity_id': 601,
             'current_state': 'under_review', 'current_step_order': 2,
             'requester_id': 5, 'requester_name': 'Mike Wilson',
             'assigned_to_id': 7, 'assigned_to_type': 'role', 'assigned_to_name': 'Finance Manager',
             'due_date': (datetime.now() + timedelta(hours=30)).isoformat(),
             'priority': 'medium', 'context_json': '{"asset_name": "Forklift 2019", "book_value": 15000}'},
            {'workflow_type': 'sales_order_approval', 'instance_code': 'WF-SO-00003',
             'source_entity_type': 'Sales Order', 'source_entity_id': 103,
             'current_state': 'completed', 'current_step_order': 3,
             'requester_id': 4, 'requester_name': 'Sarah Johnson',
             'assigned_to_id': 7, 'assigned_to_type': 'role', 'assigned_to_name': 'Finance Manager',
             'due_date': (datetime.now() - timedelta(days=2)).isoformat(),
             'completed_at': (datetime.now() - timedelta(days=1)).isoformat(),
             'priority': 'medium', 'context_json': '{"amount": 35000, "customer": "Global Traders"}'},
            {'workflow_type': 'purchase_order_approval', 'instance_code': 'WF-PO-00003',
             'source_entity_type': 'Purchase Order', 'source_entity_id': 203,
             'current_state': 'rejected', 'current_step_order': 1,
             'requester_id': 6, 'requester_name': 'Emily Brown',
             'assigned_to_id': 9, 'assigned_to_type': 'role', 'assigned_to_name': 'Purchasing Manager',
             'due_date': (datetime.now() - timedelta(days=1)).isoformat(),
             'priority': 'medium', 'context_json': '{"amount": 200000, "supplier": "Industrial Parts Ltd"}'},
            {'workflow_type': 'leave_request_approval', 'instance_code': 'WF-LV-00002',
             'source_entity_type': 'Leave Request', 'source_entity_id': 302,
             'current_state': 'returned', 'current_step_order': 1,
             'requester_id': 3, 'requester_name': 'John Smith',
             'assigned_to_id': 2, 'assigned_to_type': 'user', 'assigned_to_name': 'Department Manager',
             'due_date': (datetime.now() + timedelta(hours=12)).isoformat(),
             'priority': 'low', 'context_json': '{"leave_type": "Sick Leave", "days": 2}'},
        ]
        
        instance_ids = {}
        for idx, inst in enumerate(instances):
            wf_id = workflow_ids.get(inst['workflow_type'])
            if not wf_id:
                continue
            cursor = db.execute("""
                INSERT INTO workflow_instances 
                (workflow_definition_id, instance_code, source_module, source_entity_type, source_entity_id,
                 current_state, requester_id, requester_name, assigned_to_id, assigned_to_type, assigned_to_name,
                 due_date, due_duration_hours, escalation_level, escalation_count, priority, company_id,
                 context_json, submitted_at, completed_at, created_at, created_by, updated_at, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                wf_id, inst['instance_code'], 'SALES', inst['source_entity_type'], inst['source_entity_id'],
                inst['current_state'], inst['requester_id'], inst['requester_name'],
                inst['assigned_to_id'], inst['assigned_to_type'], inst['assigned_to_name'],
                inst['due_date'], 48, inst.get('escalation_level', 0), inst.get('escalation_count', 0),
                inst['priority'], 1,
                inst['context_json'],
                (datetime.now() - timedelta(hours=12)).isoformat() if inst['current_state'] != 'draft' else None,
                inst.get('completed_at'),
                datetime.now().isoformat(), inst['requester_id'],
                datetime.now().isoformat(), inst['requester_id']
            ))
            instance_ids[inst['instance_code']] = cursor.lastrowid
            print(f"  Instance: {inst['instance_code']} - {inst['current_state']}")
            
            # Create instance steps for each instance
            steps_for_wf = step_ids.get(inst['workflow_type'], [])
            for step_idx, step_id in enumerate(steps_for_wf):
                # Get step info
                step_info = db.execute("SELECT * FROM workflow_steps WHERE id = ?", (step_id,)).fetchone()
                if not step_info:
                    continue
                    
                # Determine if step is completed based on instance state
                step_completed = step_idx < (inst['current_step_order'] - 1)
                action_taken = None
                if step_completed:
                    action_taken = 'approved' if inst['current_state'] not in ['rejected', 'returned'] else 'rejected'
                
                cursor = db.execute("""
                    INSERT INTO workflow_instance_steps
                    (workflow_instance_id, workflow_step_id, step_code, step_name, step_order,
                     executor_id, executor_name, executor_type, action_taken, comments,
                     started_at, completed_at, due_date, was_escalated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cursor.lastrowid, step_id, step_info['step_code'], step_info['step_name'],
                    step_info['step_order'],
                    inst['requester_id'] if step_completed else None,
                    inst['requester_name'] if step_completed else None,
                    'user' if step_completed else None,
                    action_taken,
                    'Auto-approved by system' if action_taken == 'approved' else None,
                    (datetime.now() - timedelta(hours=12)).isoformat() if step_completed else None,
                    (datetime.now() - timedelta(hours=6)).isoformat() if step_completed else None,
                    inst['due_date'],
                    0
                ))
        
        # =====================================================================
        # SEED AUTOMATION RULES
        # =====================================================================
        print("Creating automation rules...")
        
        automations = [
            {
                'rule_code': 'AUTO_ESCALATE_OVERDUE',
                'rule_name': 'Auto-Escalate Overdue Items',
                'description': 'Automatically escalate workflow items that exceed their SLA',
                'module': 'WORKFLOW',
                'entity_type': 'workflow_instance',
                'trigger_type': 'on_overdue',
                'condition_json': json.dumps({'overdue_hours': {'operator': 'gt', 'value': 24}}),
                'action_json': json.dumps({'action_type': 'escalate', 'escalation_level': 1}),
                'priority': 1,
                'is_active': 1
            },
            {
                'rule_code': 'AUTO_APPROVE_LOW_VALUE',
                'rule_name': 'Auto-Approve Low Value Orders',
                'description': 'Automatically approve orders under $1,000',
                'module': 'SALES',
                'entity_type': 'sales_order',
                'trigger_type': 'on_create',
                'condition_json': json.dumps({'amount': {'operator': 'lt', 'value': 1000}}),
                'action_json': json.dumps({'action_type': 'auto_approve'}),
                'priority': 2,
                'is_active': 1
            },
            {
                'rule_code': 'NOTIFY_ASSIGNEE',
                'rule_name': 'Notify Assignee on New Task',
                'description': 'Send notification when a new task is assigned',
                'module': 'WORKFLOW',
                'entity_type': 'workflow_instance',
                'trigger_type': 'on_create',
                'condition_json': json.dumps({}),
                'action_json': json.dumps({'action_type': 'send_notification', 'template': 'new_assignment'}),
                'priority': 3,
                'is_active': 1
            },
            {
                'rule_code': 'AUTO_CLOSE_COMPLETED',
                'rule_name': 'Auto-Close Completed Instances',
                'description': 'Automatically close workflow instances after final approval',
                'module': 'WORKFLOW',
                'entity_type': 'workflow_instance',
                'trigger_type': 'on_status_change',
                'condition_json': json.dumps({'new_status': 'approved'}),
                'action_json': json.dumps({'action_type': 'change_status', 'new_status': 'completed'}),
                'priority': 5,
                'is_active': 1
            },
            {
                'rule_code': 'REMINDER_BEFORE_DUE',
                'rule_name': 'Reminder Before Due Date',
                'description': 'Send reminders for items due within 4 hours',
                'module': 'WORKFLOW',
                'entity_type': 'workflow_instance',
                'trigger_type': 'on_schedule',
                'condition_json': json.dumps({'due_within_hours': {'operator': 'lte', 'value': 4}}),
                'action_json': json.dumps({'action_type': 'send_notification', 'template': 'due_soon_reminder'}),
                'priority': 4,
                'is_active': 1
            }
        ]
        
        for auto in automations:
            db.execute("""
                INSERT INTO automation_rules
                (rule_code, rule_name, description, module, entity_type, trigger_type,
                 condition_json, action_json, priority, is_active, execution_count,
                 created_at, updated_at, created_by, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                auto['rule_code'], auto['rule_name'], auto['description'], auto['module'],
                auto['entity_type'], auto['trigger_type'],
                auto['condition_json'], auto['action_json'], auto['priority'], auto['is_active'],
                0, datetime.now().isoformat(), datetime.now().isoformat(), 1, 1
            ))
            print(f"  Automation: {auto['rule_name']}")
        
        # =====================================================================
        # SEED NOTIFICATION TEMPLATES
        # =====================================================================
        print("Creating notification templates...")
        
        templates = [
            {
                'template_code': 'NEW_ASSIGNMENT',
                'template_name': 'New Assignment Notification',
                'event_type': 'on_assign',
                'channel': 'in_app',
                'subject_template': 'New Workflow Task Assigned',
                'body_template': 'You have been assigned a new task: {{instance_code}} for {{workflow_name}}. The item is due on {{due_date}}.',
                'is_html': 0,
                'is_active': 1
            },
            {
                'template_code': 'APPROVAL_COMPLETED',
                'template_name': 'Approval Completed Notification',
                'event_type': 'on_approve',
                'channel': 'in_app',
                'subject_template': 'Your {{workflow_name}} Request Was Approved',
                'body_template': 'Great news! Your {{instance_code}} has been approved by {{approver_name}}.',
                'is_html': 0,
                'is_active': 1
            },
            {
                'template_code': 'ITEM_REJECTED',
                'template_name': 'Item Rejected Notification',
                'event_type': 'on_reject',
                'channel': 'in_app',
                'subject_template': 'Your {{workflow_name}} Request Was Rejected',
                'body_template': 'Your request {{instance_code}} was rejected by {{approver_name}}. Reason: {{rejection_reason}}',
                'is_html': 0,
                'is_active': 1
            },
            {
                'template_code': 'ESCALATION_WARNING',
                'template_name': 'Escalation Warning',
                'event_type': 'on_escalate',
                'channel': 'in_app',
                'subject_template': 'Urgent: {{instance_code}} Has Been Escalated',
                'body_template': 'Your workflow item {{instance_code}} has been escalated to {{escalated_to}} due to SLA breach.',
                'is_html': 0,
                'is_active': 1
            },
            {
                'template_code': 'DUE_SOON_REMINDER',
                'template_name': 'Due Soon Reminder',
                'event_type': 'on_schedule',
                'channel': 'in_app',
                'subject_template': 'Reminder: {{instance_code}} Due Soon',
                'body_template': 'This is a reminder that {{instance_code}} is due in {{hours_remaining}} hours.',
                'is_html': 0,
                'is_active': 1
            }
        ]
        
        for tmpl in templates:
            db.execute("""
                INSERT INTO notification_templates
                (template_code, template_name, event_type, channel, subject_template,
                 body_template, is_html, is_active, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tmpl['template_code'], tmpl['template_name'], tmpl['event_type'],
                tmpl['channel'], tmpl['subject_template'], tmpl['body_template'],
                tmpl['is_html'], tmpl['is_active'],
                datetime.now().isoformat(), datetime.now().isoformat()
            ))
            print(f"  Template: {tmpl['template_name']}")
        
        # =====================================================================
        # SEED SLA RULES
        # =====================================================================
        print("Creating SLA rules...")
        
        sla_rules = [
            {'rule_code': 'SLA_SALES_ORDER', 'rule_name': 'Sales Order Approval SLA', 'workflow_type': 'sales_order_approval', 'step_type': 'approval', 'duration_hours': 24, 'duration_type': 'hours'},
            {'rule_code': 'SLA_PO_APPROVAL', 'rule_name': 'Purchase Order Approval SLA', 'workflow_type': 'purchase_order_approval', 'step_type': 'approval', 'duration_hours': 48, 'duration_type': 'hours'},
            {'rule_code': 'SLA_LEAVE_REQUEST', 'rule_name': 'Leave Request Approval SLA', 'workflow_type': 'leave_request_approval', 'step_type': 'approval', 'duration_hours': 72, 'duration_type': 'hours'},
            {'rule_code': 'SLA_EXPENSE', 'rule_name': 'Expense Approval SLA', 'workflow_type': 'expense_approval', 'step_type': 'approval', 'duration_hours': 48, 'duration_type': 'hours'},
            {'rule_code': 'SLA_ASSET_DISPOSAL', 'rule_name': 'Asset Disposal Approval SLA', 'workflow_type': 'asset_disposal_approval', 'step_type': 'approval', 'duration_hours': 120, 'duration_type': 'hours'},
        ]
        
        for sla in sla_rules:
            db.execute("""
                INSERT INTO sla_rules
                (rule_code, rule_name, workflow_type, step_type, duration_hours, duration_type, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sla['rule_code'], sla['rule_name'], sla['workflow_type'], sla['step_type'],
                sla['duration_hours'], sla['duration_type'], 1, datetime.now().isoformat()
            ))
            print(f"  SLA: {sla['rule_name']}")
        
        # =====================================================================
        # SEED ESCALATION RULES
        # =====================================================================
        print("Creating escalation rules...")
        
        escalation_rules = [
            {'rule_code': 'ESC_LEVEL1', 'rule_name': 'First Level Escalation', 'workflow_type': 'sales_order_approval', 'step_type': 'approval', 'escalation_level': 1, 'escalation_hours': 24, 'escalation_action': 'notify', 'escalation_target_type': 'role', 'escalation_target_id': 6},
            {'rule_code': 'ESC_LEVEL2', 'rule_name': 'Second Level Escalation', 'workflow_type': 'sales_order_approval', 'step_type': 'approval', 'escalation_level': 2, 'escalation_hours': 48, 'escalation_action': 'reassign', 'escalation_target_type': 'role', 'escalation_target_id': 7},
            {'rule_code': 'ESC_MANAGER', 'rule_name': 'Manager Escalation', 'workflow_type': 'leave_request_approval', 'step_type': 'approval', 'escalation_level': 1, 'escalation_hours': 48, 'escalation_action': 'escalate_to_role', 'escalation_target_type': 'role', 'escalation_target_id': 8},
        ]
        
        for esc in escalation_rules:
            db.execute("""
                INSERT INTO escalation_rules
                (rule_code, rule_name, workflow_type, step_type, escalation_level, escalation_hours,
                 escalation_action, escalation_target_type, escalation_target_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                esc['rule_code'], esc['rule_name'], esc['workflow_type'], esc['step_type'],
                esc['escalation_level'], esc['escalation_hours'], esc['escalation_action'],
                esc['escalation_target_type'], esc['escalation_target_id'],
                datetime.now().isoformat()
            ))
            print(f"  Escalation: {esc['rule_name']}")
        
        db.commit()
    
    print("\nWorkflow/BPM demo data seeded successfully!")
    return True


if __name__ == '__main__':
    seed_workflow_data()