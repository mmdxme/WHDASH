"""
Workflow/BPM Data Model Layer
=============================
Comprehensive database models and helper functions for a complete Workflow/BPM system.

This module provides:
- Full workflow definition with versioning and scoping
- Step-based workflow execution with state management
- Conditional routing and transition rules
- Automation engine for event-driven actions
- Notification templates and delivery tracking
- SLA and escalation management
- Delegation/substitution rules
- Reusable workflow templates

Usage:
    from workflow_models import (
        initialize_workflow_schema,
        get_workflow_definition, create_workflow_definition,
        get_workflow_instance, create_workflow_instance,
        get_pending_approvals, seed_workflow_demo_data
    )

Required Tables (22):
    1. workflow_definitions    - Full workflow definition with versioning
    2. workflow_versions       - Version tracking
    3. workflow_steps          - Full step definition (extends existing)
    4. workflow_transitions    - State transitions
    5. workflow_conditions     - Conditional routing rules
    6. workflow_instances      - Runtime workflow executions
    7. workflow_instance_steps - Step execution history
    8. workflow_actions        - All actions on instances
    9. workflow_assignments    - Assignment rules
    10. workflow_comments       - Comments/notes on instances
    11. automation_rules        - Automation engine
    12. automation_rule_conditions - Rule conditions
    13. automation_rule_actions    - Rule actions
    14. automation_logs         - Execution logging
    15. notification_templates   - Notification templates
    16. notification_rules       - Notification delivery rules (extends existing)
    17. notification_logs         - Delivery tracking
    18. sla_rules                 - SLA configuration
    19. escalation_rules          - Escalation chains
    20. delegation_rules          - Delegation/substitution
    21. workflow_templates        - Reusable templates
    22. workflow_settings         - Configurable settings
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from database import get_db_context, get_one, get_all, table_exists, log_audit

# ============================================================================
# WORKFLOW STATES AND TYPES
# ============================================================================

WORKFLOW_STATES = {
    'draft': 'Draft',
    'submitted': 'Submitted',
    'pending': 'Pending',
    'under_review': 'Under Review',
    'returned': 'Returned',
    'rejected': 'Rejected',
    'approved': 'Approved',
    'escalated': 'Escalated',
    'completed': 'Completed',
    'cancelled': 'Cancelled'
}

STEP_TYPES = {
    'approval': 'Approval',
    'review': 'Review',
    'verification': 'Verification',
    'notification': 'Notification',
    'automated': 'Automated',
    'finalization': 'Finalization'
}

ASSIGNEE_TYPES = {
    'user': 'User',
    'role': 'Role',
    'department_manager': 'Department Manager',
    'supervisor': 'Supervisor',
    'requester_manager': 'Requester Manager',
    'branch_manager': 'Branch Manager',
    'dynamic': 'Dynamic'
}

ACTION_TYPES = {
    'submit': 'Submit',
    'approve': 'Approve',
    'reject': 'Reject',
    'return': 'Return',
    'reassign': 'Reassign',
    'escalate': 'Escalate',
    'cancel': 'Cancel',
    'complete': 'Complete',
    'skip': 'Skip'
}

PRIORITY_LEVELS = {
    'low': 'Low',
    'medium': 'Medium',
    'high': 'High',
    'critical': 'Critical'
}

WORKFLOW_STATUS_COLORS = {
    'draft': 'gray',
    'submitted': 'blue',
    'pending': 'yellow',
    'under_review': 'purple',
    'returned': 'orange',
    'rejected': 'red',
    'approved': 'green',
    'escalated': 'orange',
    'completed': 'green',
    'cancelled': 'gray'
}

AUTOMATION_TRIGGERS = {
    'on_create': 'On Create',
    'on_update': 'On Update',
    'on_status_change': 'On Status Change',
    'on_approval': 'On Approval',
    'on_rejection': 'On Rejection',
    'on_schedule': 'On Schedule',
    'on_overdue': 'On Overdue',
    'on_webhook': 'On Webhook'
}

AUTOMATION_ACTIONS = {
    'change_status': 'Change Status',
    'assign_user': 'Assign User',
    'create_task': 'Create Task',
    'send_notification': 'Send Notification',
    'escalate': 'Escalate',
    'auto_approve': 'Auto Approve',
    'auto_reject': 'Auto Reject',
    'create_record': 'Create Record',
    'lock_document': 'Lock Document',
    'call_webhook': 'Call Webhook'
}

NOTIFICATION_CHANNELS = {
    'in_app': 'In-App',
    'email': 'Email',
    'sms': 'SMS',
    'webhook': 'Webhook'
}

# ============================================================================
# WORKFLOW DEFINITIONS CRUD
# ============================================================================

def get_workflow_definition(workflow_type: str, version: int = None) -> Optional[Dict]:
    """Get a workflow definition by type, optionally for a specific version."""
    if version:
        return get_one("""
            SELECT wd.*, wv.version_number, wv.version_label, wv.status as version_status
            FROM workflow_definitions wd
            LEFT JOIN workflow_versions wv ON wv.workflow_definition_id = wd.id
            WHERE wd.workflow_type = ? AND wv.version_number = ?
        """, (workflow_type, version))
    return get_one("""
        SELECT wd.*, wv.version_number, wv.version_label, wv.status as version_status
        FROM workflow_definitions wd
        LEFT JOIN workflow_versions wv ON wv.workflow_definition_id = wd.id
        WHERE wd.workflow_type = ? AND wd.is_active = 1
        ORDER BY wv.version_number DESC LIMIT 1
    """, (workflow_type,))


def get_all_workflow_definitions(active_only: bool = True) -> List[Dict]:
    """Get all workflow definitions."""
    if active_only:
        return get_all("""
            SELECT wd.*, wv.version_number, wv.status as version_status
            FROM workflow_definitions wd
            LEFT JOIN workflow_versions wv ON wv.workflow_definition_id = wd.id
            WHERE wd.is_active = 1
            ORDER BY wd.module, wd.workflow_type
        """)
    return get_all("""
        SELECT wd.*, wv.version_number, wv.status as version_status
        FROM workflow_definitions wd
        LEFT JOIN workflow_versions wv ON wv.workflow_definition_id = wd.id
        ORDER BY wd.module, wd.workflow_type
    """)


def create_workflow_definition(
    workflow_type: str,
    name: str,
    module: str,
    entity_type: str,
    description: str = None,
    version: int = 1,
    requires_approval: bool = True,
    company_scope: int = None,
    branch_scope: int = None,
    department_scope: int = None,
    warehouse_scope: int = None,
    created_by: int = None
) -> int:
    """Create a new workflow definition with initial version."""
    with get_db_context() as db:
        # Check if workflow type already exists
        existing = db.execute(
            "SELECT id FROM workflow_definitions WHERE workflow_type = ?",
            (workflow_type,)
        ).fetchone()

        if existing:
            # Update existing
            workflow_def_id = existing['id']
            db.execute("""
                UPDATE workflow_definitions SET
                    name = ?, description = ?, module = ?, entity_type = ?,
                    requires_approval = ?, company_scope = ?, branch_scope = ?,
                    department_scope = ?, warehouse_scope = ?,
                    updated_at = CURRENT_TIMESTAMP, updated_by = ?
                WHERE id = ?
            """, (name, description, module, entity_type,
                  1 if requires_approval else 0, company_scope, branch_scope,
                  department_scope, warehouse_scope, created_by, workflow_def_id))
        else:
            # Create new
            cursor = db.execute("""
                INSERT INTO workflow_definitions
                (workflow_type, name, description, module, entity_type, version,
                 requires_approval, company_scope, branch_scope, department_scope,
                 warehouse_scope, created_by, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (workflow_type, name, description, module, entity_type, version,
                  1 if requires_approval else 0, company_scope, branch_scope,
                  department_scope, warehouse_scope, created_by, created_by))
            workflow_def_id = cursor.lastrowid

        # Create initial version
        db.execute("""
            INSERT INTO workflow_versions
            (workflow_definition_id, version_number, version_label, status, created_by)
            VALUES (?, ?, ?, 'draft', ?)
        """, (workflow_def_id, version, f"v{version}", created_by))

        db.commit()

        log_audit('workflow_definition', workflow_def_id, 'CREATE',
                  user_id=created_by, notes=f"Created workflow: {workflow_type}")

        return workflow_def_id


def update_workflow_definition(
    workflow_def_id: int,
    data: Dict,
    updated_by: int = None
) -> bool:
    """Update a workflow definition."""
    allowed_fields = ['name', 'description', 'requires_approval', 'is_active',
                      'company_scope', 'branch_scope', 'department_scope',
                      'warehouse_scope', 'approved_by', 'approved_at',
                      'activation_date', 'deactivation_date']

    fields = []
    values = []
    for key, value in data.items():
        if key in allowed_fields and key != 'updated_by':
            fields.append(f"{key} = ?")
            values.append(value)

    if not fields:
        return False

    fields.append("updated_at = CURRENT_TIMESTAMP")
    if updated_by:
        fields.append("updated_by = ?")
        values.append(updated_by)
    values.append(workflow_def_id)

    with get_db_context() as db:
        db.execute(
            f"UPDATE workflow_definitions SET {', '.join(fields)} WHERE id = ?",
            values
        )
        db.commit()

    log_audit('workflow_definition', workflow_def_id, 'UPDATE', user_id=updated_by)
    return True


# ============================================================================
# WORKFLOW VERSIONS CRUD
# ============================================================================

def get_workflow_versions(workflow_definition_id: int) -> List[Dict]:
    """Get all versions for a workflow definition."""
    return get_all("""
        SELECT * FROM workflow_versions
        WHERE workflow_definition_id = ?
        ORDER BY version_number DESC
    """, (workflow_definition_id,))


def create_workflow_version(
    workflow_definition_id: int,
    version_number: int,
    version_label: str = None,
    created_by: int = None
) -> int:
    """Create a new version for a workflow."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO workflow_versions
            (workflow_definition_id, version_number, version_label, status, created_by)
            VALUES (?, ?, ?, 'draft', ?)
        """, (workflow_definition_id, version_number,
              version_label or f"v{version_number}", created_by))
        db.commit()
        return cursor.lastrowid


def update_version_status(version_id: int, status: str, user_id: int = None) -> bool:
    """Update workflow version status (draft -> active -> archived)."""
    with get_db_context() as db:
        db.execute("""
            UPDATE workflow_versions SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, version_id))
        db.commit()
    log_audit('workflow_version', version_id, f'STATUS_{status.upper()}', user_id=user_id)
    return True


# ============================================================================
# WORKFLOW STEPS CRUD
# ============================================================================

def get_workflow_steps(version_id: int = None, workflow_definition_id: int = None) -> List[Dict]:
    """Get workflow steps for a version or definition."""
    if version_id:
        return get_all("""
            SELECT * FROM workflow_steps
            WHERE version_id = ?
            ORDER BY step_order
        """, (version_id,))
    elif workflow_definition_id:
        return get_all("""
            SELECT ws.* FROM workflow_steps ws
            JOIN workflow_versions wv ON wv.workflow_definition_id = ws.workflow_definition_id
            WHERE ws.workflow_definition_id = ?
            AND wv.status = 'active'
            ORDER BY ws.step_order
        """, (workflow_definition_id,))
    return []


def create_workflow_step(
    workflow_definition_id: int,
    version_id: int,
    step_code: str,
    step_name: str,
    step_order: int,
    step_type: str = 'approval',
    assignee_type: str = 'role',
    assignee_id: int = None,
    assignee_rule: Dict = None,
    due_duration_hours: int = 24,
    due_duration_type: str = 'hours',
    escalation_enabled: bool = False,
    escalation_level: int = 1,
    escalation_hours: int = None,
    allow_approve: bool = True,
    allow_reject: bool = True,
    allow_return: bool = True,
    allow_skip: bool = False,
    require_comments: bool = False,
    require_attachment: bool = False
) -> int:
    """Create a workflow step."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO workflow_steps (
                workflow_definition_id, version_id, step_code, step_name, step_order,
                step_type, assignee_type, assignee_id, assignee_rule,
                due_duration_hours, due_duration_type, escalation_enabled,
                escalation_level, escalation_hours, allow_approve, allow_reject,
                allow_return, allow_skip, require_comments, require_attachment
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (workflow_definition_id, version_id, step_code, step_name, step_order,
              step_type, assignee_type, assignee_id,
              json.dumps(assignee_rule) if assignee_rule else None,
              due_duration_hours, due_duration_type,
              1 if escalation_enabled else 0, escalation_level, escalation_hours,
              1 if allow_approve else 0, 1 if allow_reject else 0,
              1 if allow_return else 0, 1 if allow_skip else 0,
              1 if require_comments else 0, 1 if require_attachment else 0))
        db.commit()
        return cursor.lastrowid


def update_workflow_step(step_id: int, data: Dict) -> bool:
    """Update a workflow step."""
    allowed_fields = ['step_name', 'step_order', 'step_type', 'assignee_type',
                      'assignee_id', 'assignee_rule', 'due_duration_hours',
                      'due_duration_type', 'escalation_enabled', 'escalation_level',
                      'escalation_hours', 'allow_approve', 'allow_reject',
                      'allow_return', 'allow_skip', 'require_comments',
                      'require_attachment', 'completion_status']

    fields = []
    values = []
    for key, value in data.items():
        if key in allowed_fields:
            if key == 'assignee_rule' and isinstance(value, dict):
                value = json.dumps(value)
            elif key in ['escalation_enabled', 'allow_approve', 'allow_reject',
                         'allow_return', 'allow_skip', 'require_comments',
                         'require_attachment']:
                value = 1 if value else 0
            fields.append(f"{key} = ?")
            values.append(value)

    if not fields:
        return False

    values.append(step_id)

    with get_db_context() as db:
        db.execute(
            f"UPDATE workflow_steps SET {', '.join(fields)} WHERE id = ?",
            values
        )
        db.commit()
    return True


def delete_workflow_step(step_id: int) -> bool:
    """Delete a workflow step."""
    with get_db_context() as db:
        db.execute("DELETE FROM workflow_steps WHERE id = ?", (step_id,))
        db.commit()
    return True


# ============================================================================
# WORKFLOW TRANSITIONS CRUD
# ============================================================================

def get_workflow_transitions(workflow_definition_id: int) -> List[Dict]:
    """Get all transitions for a workflow."""
    return get_all("""
        SELECT wt.*,
               fs.step_name as from_step_name, ts.step_name as to_step_name
        FROM workflow_transitions wt
        LEFT JOIN workflow_steps fs ON wt.from_step_id = fs.id
        LEFT JOIN workflow_steps ts ON wt.to_step_id = ts.id
        WHERE wt.workflow_definition_id = ?
        ORDER BY fs.step_order, ts.step_order
    """, (workflow_definition_id,))


def create_workflow_transition(
    workflow_definition_id: int,
    from_step_id: int,
    to_step_id: int,
    transition_type: str = 'sequential',
    condition_expression: str = None,
    condition_json: Dict = None
) -> int:
    """Create a workflow transition."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO workflow_transitions
            (workflow_definition_id, from_step_id, to_step_id, transition_type,
             condition_expression, condition_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (workflow_definition_id, from_step_id, to_step_id, transition_type,
              condition_expression, json.dumps(condition_json) if condition_json else None))
        db.commit()
        return cursor.lastrowid


def update_workflow_transition(transition_id: int, data: Dict) -> bool:
    """Update a workflow transition."""
    allowed_fields = ['transition_type', 'condition_expression', 'condition_json']

    fields = []
    values = []
    for key, value in data.items():
        if key in allowed_fields:
            if key == 'condition_json' and isinstance(value, dict):
                value = json.dumps(value)
            fields.append(f"{key} = ?")
            values.append(value)

    if not fields:
        return False

    values.append(transition_id)

    with get_db_context() as db:
        db.execute(
            f"UPDATE workflow_transitions SET {', '.join(fields)} WHERE id = ?",
            values
        )
        db.commit()
    return True


# ============================================================================
# WORKFLOW CONDITIONS CRUD
# ============================================================================

def get_transition_conditions(transition_id: int) -> List[Dict]:
    """Get conditions for a transition."""
    return get_all("""
        SELECT * FROM workflow_conditions
        WHERE workflow_transition_id = ?
    """, (transition_id,))


def create_workflow_condition(
    workflow_transition_id: int,
    condition_type: str,
    field_name: str = None,
    operator: str = None,
    field_value: str = None,
    value_json: Dict = None
) -> int:
    """Create a workflow condition."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO workflow_conditions
            (workflow_transition_id, condition_type, field_name, operator,
             field_value, value_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (workflow_transition_id, condition_type, field_name, operator,
              field_value, json.dumps(value_json) if value_json else None))
        db.commit()
        return cursor.lastrowid


def delete_workflow_condition(condition_id: int) -> bool:
    """Delete a workflow condition."""
    with get_db_context() as db:
        db.execute("DELETE FROM workflow_conditions WHERE id = ?", (condition_id,))
        db.commit()
    return True


# ============================================================================
# WORKFLOW INSTANCES CRUD
# ============================================================================

def get_workflow_instance(instance_id: int = None, instance_code: str = None) -> Optional[Dict]:
    """Get a workflow instance by ID or code."""
    if instance_id:
        return get_one("SELECT * FROM workflow_instances WHERE id = ?", (instance_id,))
    elif instance_code:
        return get_one("SELECT * FROM workflow_instances WHERE instance_code = ?", (instance_code,))
    return None


def get_workflow_instances(
    workflow_definition_id: int = None,
    current_state: str = None,
    assigned_to_id: int = None,
    requester_id: int = None,
    company_id: int = None,
    branch_id: int = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict]:
    """Get workflow instances with filters."""
    sql = "SELECT * FROM workflow_instances WHERE 1=1"
    params = []

    if workflow_definition_id:
        sql += " AND workflow_definition_id = ?"
        params.append(workflow_definition_id)
    if current_state:
        sql += " AND current_state = ?"
        params.append(current_state)
    if assigned_to_id:
        sql += " AND assigned_to_id = ?"
        params.append(assigned_to_id)
    if requester_id:
        sql += " AND requester_id = ?"
        params.append(requester_id)
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    if branch_id:
        sql += " AND branch_id = ?"
        params.append(branch_id)

    sql += f" ORDER BY created_at DESC LIMIT {limit} OFFSET {offset}"

    return get_all(sql, params)


def create_workflow_instance(
    workflow_definition_id: int,
    version_id: int,
    source_module: str,
    source_entity_type: str,
    source_entity_id: int,
    requester_id: int,
    requester_name: str,
    priority: str = 'medium',
    company_id: int = None,
    branch_id: int = None,
    department_id: int = None,
    warehouse_id: int = None,
    context_json: Dict = None,
    initial_step_id: int = None
) -> str:
    """Create a new workflow instance."""
    instance_code = f"WFI-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO workflow_instances (
                workflow_definition_id, version_id, instance_code, source_module,
                source_entity_type, source_entity_id, current_step_id,
                current_state, requester_id, requester_name, priority,
                company_id, branch_id, department_id, warehouse_id,
                context_json, submitted_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'submitted', ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (workflow_definition_id, version_id, instance_code, source_module,
              source_entity_type, source_entity_id, initial_step_id,
              requester_id, requester_name, priority, company_id, branch_id,
              department_id, warehouse_id,
              json.dumps(context_json) if context_json else None))
        db.commit()
        instance_id = cursor.lastrowid

    log_audit('workflow_instance', instance_id, 'CREATE',
              user_id=requester_id, notes=f"Instance: {instance_code}")

    return instance_code


def update_workflow_instance(
    instance_id: int,
    data: Dict,
    updated_by: int = None
) -> bool:
    """Update a workflow instance."""
    allowed_fields = ['current_step_id', 'current_state', 'assigned_to_id',
                      'assigned_to_type', 'assigned_to_name', 'due_date',
                      'due_duration_hours', 'escalation_level', 'escalation_count',
                      'last_escalated_at', 'priority', 'context_json',
                      'completed_at', 'cancelled_at']

    fields = []
    values = []
    for key, value in data.items():
        if key in allowed_fields:
            if key == 'context_json' and isinstance(value, dict):
                value = json.dumps(value)
            fields.append(f"{key} = ?")
            values.append(value)

    if not fields:
        return False

    fields.append("updated_at = CURRENT_TIMESTAMP")
    if updated_by:
        fields.append("updated_by = ?")
        values.append(updated_by)
    values.append(instance_id)

    with get_db_context() as db:
        db.execute(
            f"UPDATE workflow_instances SET {', '.join(fields)} WHERE id = ?",
            values
        )
        db.commit()
    return True


def advance_workflow_instance(
    instance_id: int,
    to_step_id: int,
    new_state: str,
    action_taken: str,
    action_comments: str = None,
    user_id: int = None,
    user_name: str = None
) -> bool:
    """Advance a workflow instance to the next step."""
    instance = get_workflow_instance(instance_id)
    if not instance:
        return False

    step = get_one("SELECT * FROM workflow_steps WHERE id = ?", (to_step_id))
    if not step:
        return False

    # Calculate due date
    due_date = None
    if step['due_duration_hours']:
        hours = step['due_duration_hours']
        if step['due_duration_type'] == 'days':
            hours = hours * 24
        due_date = datetime.now() + timedelta(hours=hours)

    # Update instance
    update_workflow_instance(instance_id, {
        'current_step_id': to_step_id,
        'current_state': new_state,
        'assigned_to_id': step['assignee_id'],
        'assigned_to_type': step['assignee_type'],
        'assigned_to_name': None,  # Would resolve based on assignee_type
        'due_date': due_date,
        'due_duration_hours': step['due_duration_hours']
    }, updated_by=user_id)

    # Record action
    create_workflow_action(
        workflow_instance_id=instance_id,
        workflow_step_id=to_step_id,
        user_id=user_id,
        action_type=action_taken,
        comments=action_comments,
        previous_state=instance['current_state'],
        new_state=new_state
    )

    log_audit('workflow_instance', instance_id, action_taken.upper(),
              user_id=user_id, notes=f"State: {instance['current_state']} -> {new_state}")

    return True


# ============================================================================
# WORKFLOW INSTANCE STEPS CRUD
# ============================================================================

def get_instance_steps(instance_id: int) -> List[Dict]:
    """Get all steps executed for an instance."""
    return get_all("""
        SELECT wis.*, ws.step_type, ws.assignee_type
        FROM workflow_instance_steps wis
        LEFT JOIN workflow_steps ws ON wis.workflow_step_id = ws.id
        WHERE wis.workflow_instance_id = ?
        ORDER BY wis.step_order
    """, (instance_id,))


def create_instance_step(
    workflow_instance_id: int,
    workflow_step_id: int,
    executor_id: int = None,
    executor_name: str = None,
    executor_type: str = 'user',
    started_at: datetime = None
) -> int:
    """Create a new instance step record."""
    step = get_one("SELECT * FROM workflow_steps WHERE id = ?", (workflow_step_id))
    if not step:
        return None

    due_date = None
    if step['due_duration_hours']:
        hours = step['due_duration_hours']
        if step['due_duration_type'] == 'days':
            hours = hours * 24
        due_date = datetime.now() + timedelta(hours=hours)

    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO workflow_instance_steps (
                workflow_instance_id, workflow_step_id, step_code, step_name,
                step_order, executor_id, executor_name, executor_type,
                started_at, due_date, was_escalated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        """, (workflow_instance_id, workflow_step_id, step['step_code'],
              step['step_name'], step['step_order'], executor_id,
              executor_name, executor_type, started_at or datetime.now(), due_date))
        db.commit()
        return cursor.lastrowid


def complete_instance_step(
    instance_step_id: int,
    action_taken: str,
    comments: str = None,
    attachments_json: List = None
) -> bool:
    """Complete a workflow instance step."""
    with get_db_context() as db:
        db.execute("""
            UPDATE workflow_instance_steps SET
                action_taken = ?, comments = ?,
                attachments_json = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (action_taken, comments,
              json.dumps(attachments_json) if attachments_json else None,
              instance_step_id))
        db.commit()
    return True


# ============================================================================
# WORKFLOW ACTIONS CRUD
# ============================================================================

def get_instance_actions(instance_id: int) -> List[Dict]:
    """Get all actions for an instance."""
    return get_all("""
        SELECT wa.*, u.username as user_name
        FROM workflow_actions wa
        LEFT JOIN users u ON wa.user_id = u.id
        WHERE wa.workflow_instance_id = ?
        ORDER BY wa.created_at DESC
    """, (instance_id,))


def create_workflow_action(
    workflow_instance_id: int,
    action_type: str,
    workflow_step_id: int = None,
    user_id: int = None,
    comments: str = None,
    attachments_json: List = None,
    previous_state: str = None,
    new_state: str = None
) -> int:
    """Record a workflow action."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO workflow_actions (
                workflow_instance_id, workflow_step_id, user_id, action_type,
                comments, attachments_json, previous_state, new_state
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (workflow_instance_id, workflow_step_id, user_id, action_type,
              comments, json.dumps(attachments_json) if attachments_json else None,
              previous_state, new_state))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# WORKFLOW ASSIGNMENTS CRUD
# ============================================================================

def get_workflow_assignments(workflow_definition_id: int, step_code: str = None) -> List[Dict]:
    """Get assignment rules for a workflow."""
    sql = "SELECT * FROM workflow_assignments WHERE workflow_definition_id = ?"
    params = [workflow_definition_id]

    if step_code:
        sql += " AND step_code = ?"
        params.append(step_code)

    sql += " ORDER BY priority_order"

    return get_all(sql, params)


def create_workflow_assignment(
    workflow_definition_id: int,
    step_code: str,
    assignee_type: str,
    assignee_id: int = None,
    assignee_rule_json: Dict = None,
    priority_order: int = 1,
    is_active: bool = True
) -> int:
    """Create a workflow assignment rule."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO workflow_assignments (
                workflow_definition_id, step_code, assignee_type, assignee_id,
                assignee_rule_json, priority_order, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (workflow_definition_id, step_code, assignee_type, assignee_id,
              json.dumps(assignee_rule_json) if assignee_rule_json else None,
              priority_order, 1 if is_active else 0))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# WORKFLOW COMMENTS CRUD
# ============================================================================

def get_instance_comments(instance_id: int) -> List[Dict]:
    """Get all comments for an instance."""
    return get_all("""
        SELECT * FROM workflow_comments
        WHERE workflow_instance_id = ?
        ORDER BY created_at ASC
    """, (instance_id,))


def create_workflow_comment(
    workflow_instance_id: int,
    user_id: int,
    user_name: str,
    comment: str
) -> int:
    """Add a comment to a workflow instance."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO workflow_comments (workflow_instance_id, user_id, user_name, comment)
            VALUES (?, ?, ?, ?)
        """, (workflow_instance_id, user_id, user_name, comment))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# AUTOMATION RULES CRUD
# ============================================================================

def get_automation_rule(rule_id: int = None, rule_code: str = None) -> Optional[Dict]:
    """Get an automation rule by ID or code."""
    if rule_id:
        return get_one("SELECT * FROM automation_rules WHERE id = ?", (rule_id,))
    elif rule_code:
        return get_one("SELECT * FROM automation_rules WHERE rule_code = ?", (rule_code,))
    return None


def get_automation_rules(
    module: str = None,
    entity_type: str = None,
    trigger_type: str = None,
    is_active: bool = True
) -> List[Dict]:
    """Get automation rules with filters."""
    sql = "SELECT * FROM automation_rules WHERE 1=1"
    params = []

    if module:
        sql += " AND module = ?"
        params.append(module)
    if entity_type:
        sql += " AND entity_type = ?"
        params.append(entity_type)
    if trigger_type:
        sql += " AND trigger_type = ?"
        params.append(trigger_type)
    if is_active:
        sql += " AND is_active = 1"

    sql += " ORDER BY priority DESC, id"

    return get_all(sql, params)


def create_automation_rule(
    rule_code: str,
    rule_name: str,
    module: str,
    entity_type: str,
    trigger_type: str,
    description: str = None,
    condition_json: Dict = None,
    action_json: Dict = None,
    priority: int = 100,
    scope_type: str = None,
    scope_id: int = None,
    created_by: int = None
) -> int:
    """Create an automation rule."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO automation_rules (
                rule_code, rule_name, description, module, entity_type,
                trigger_type, condition_json, action_json, priority, is_active,
                scope_type, scope_id, created_by, updated_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
        """, (rule_code, rule_name, description, module, entity_type,
              trigger_type, json.dumps(condition_json) if condition_json else None,
              json.dumps(action_json) if action_json else None, priority,
              scope_type, scope_id, created_by, created_by))
        db.commit()
        return cursor.lastrowid


def update_automation_rule(rule_id: int, data: Dict, updated_by: int = None) -> bool:
    """Update an automation rule."""
    allowed_fields = ['rule_name', 'description', 'trigger_type', 'condition_json',
                      'action_json', 'priority', 'is_active', 'approved_by',
                      'approved_at', 'last_executed_at', 'last_execution_status',
                      'execution_count']

    fields = []
    values = []
    for key, value in data.items():
        if key in allowed_fields:
            if key in ['condition_json', 'action_json'] and isinstance(value, dict):
                value = json.dumps(value)
            fields.append(f"{key} = ?")
            values.append(value)

    if not fields:
        return False

    fields.append("updated_at = CURRENT_TIMESTAMP")
    if updated_by:
        fields.append("updated_by = ?")
        values.append(updated_by)
    values.append(rule_id)

    with get_db_context() as db:
        db.execute(
            f"UPDATE automation_rules SET {', '.join(fields)} WHERE id = ?",
            values
        )
        db.commit()
    return True


# ============================================================================
# AUTOMATION RULE CONDITIONS CRUD
# ============================================================================

def get_rule_conditions(rule_id: int) -> List[Dict]:
    """Get conditions for an automation rule."""
    return get_all("""
        SELECT * FROM automation_rule_conditions
        WHERE automation_rule_id = ?
        ORDER BY id
    """, (rule_id,))


def create_rule_condition(
    automation_rule_id: int,
    condition_type: str,
    field_name: str = None,
    operator: str = None,
    value: str = None,
    value_json: Dict = None
) -> int:
    """Create a condition for an automation rule."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO automation_rule_conditions
            (automation_rule_id, condition_type, field_name, operator, value, value_json)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (automation_rule_id, condition_type, field_name, operator,
              value, json.dumps(value_json) if value_json else None))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# AUTOMATION RULE ACTIONS CRUD
# ============================================================================

def get_rule_actions(rule_id: int) -> List[Dict]:
    """Get actions for an automation rule."""
    return get_all("""
        SELECT * FROM automation_rule_actions
        WHERE automation_rule_id = ?
        ORDER BY id
    """, (rule_id,))


def create_rule_action(
    automation_rule_id: int,
    action_type: str,
    action_config_json: Dict
) -> int:
    """Create an action for an automation rule."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO automation_rule_actions
            (automation_rule_id, action_type, action_config_json)
            VALUES (?, ?, ?)
        """, (automation_rule_id, action_type, json.dumps(action_config_json)))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# AUTOMATION LOGS CRUD
# ============================================================================

def get_automation_logs(
    automation_rule_id: int = None,
    workflow_instance_id: int = None,
    result: str = None,
    limit: int = 100
) -> List[Dict]:
    """Get automation execution logs."""
    sql = "SELECT * FROM automation_logs WHERE 1=1"
    params = []

    if automation_rule_id:
        sql += " AND automation_rule_id = ?"
        params.append(automation_rule_id)
    if workflow_instance_id:
        sql += " AND workflow_instance_id = ?"
        params.append(workflow_instance_id)
    if result:
        sql += " AND result = ?"
        params.append(result)

    sql += f" ORDER BY created_at DESC LIMIT {limit}"

    return get_all(sql, params)


def create_automation_log(
    automation_rule_id: int,
    workflow_instance_id: int = None,
    trigger_event: str = None,
    action_taken: str = None,
    result: str = 'success',
    error_message: str = None,
    execution_time_ms: int = None
) -> int:
    """Log an automation execution."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO automation_logs (
                automation_rule_id, workflow_instance_id, trigger_event,
                action_taken, result, error_message, execution_time_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (automation_rule_id, workflow_instance_id, trigger_event,
              action_taken, result, error_message, execution_time_ms))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# NOTIFICATION TEMPLATES CRUD
# ============================================================================

def get_notification_template(template_id: int = None, template_code: str = None) -> Optional[Dict]:
    """Get a notification template."""
    if template_id:
        return get_one("SELECT * FROM notification_templates WHERE id = ?", (template_id,))
    elif template_code:
        return get_one("SELECT * FROM notification_templates WHERE template_code = ?", (template_code,))
    return None


def get_notification_templates(event_type: str = None, channel: str = None) -> List[Dict]:
    """Get notification templates with filters."""
    sql = "SELECT * FROM notification_templates WHERE is_active = 1"
    params = []

    if event_type:
        sql += " AND event_type = ?"
        params.append(event_type)
    if channel:
        sql += " AND channel = ?"
        params.append(channel)

    sql += " ORDER BY template_name"

    return get_all(sql, params)


def create_notification_template(
    template_code: str,
    template_name: str,
    event_type: str,
    channel: str = 'in_app',
    subject_template: str = None,
    body_template: str = None,
    is_html: bool = False,
    variables_json: List = None,
    created_by: int = None
) -> int:
    """Create a notification template."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO notification_templates (
                template_code, template_name, event_type, channel,
                subject_template, body_template, is_html, variables_json,
                is_active, created_by, updated_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        """, (template_code, template_name, event_type, channel,
              subject_template, body_template, 1 if is_html else 0,
              json.dumps(variables_json) if variables_json else None,
              created_by, created_by))
        db.commit()
        return cursor.lastrowid


def update_notification_template(template_id: int, data: Dict) -> bool:
    """Update a notification template."""
    allowed_fields = ['template_name', 'event_type', 'channel', 'subject_template',
                      'body_template', 'is_html', 'variables_json', 'is_active']

    fields = []
    values = []
    for key, value in data.items():
        if key in allowed_fields:
            if key in ['variables_json'] and isinstance(value, list):
                value = json.dumps(value)
            elif key == 'is_html':
                value = 1 if value else 0
            fields.append(f"{key} = ?")
            values.append(value)

    if not fields:
        return False

    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(template_id)

    with get_db_context() as db:
        db.execute(
            f"UPDATE notification_templates SET {', '.join(fields)} WHERE id = ?",
            values
        )
        db.commit()
    return True


# ============================================================================
# NOTIFICATION RULES CRUD (Extends existing)
# ============================================================================

def get_notification_rules(module: str = None, event_type: str = None) -> List[Dict]:
    """Get notification delivery rules."""
    sql = "SELECT * FROM notification_rules WHERE 1=1"
    params = []

    if module:
        sql += " AND module = ?"
        params.append(module)
    if event_type:
        sql += " AND event_type = ?"
        params.append(event_type)

    sql += " AND is_active = 1 ORDER BY priority_order"

    return get_all(sql, params)


def create_notification_rule(
    rule_name: str,
    module: str,
    event_type: str,
    template_id: int = None,
    recipient_type: str = 'user',
    recipient_id: int = None,
    delay_hours: int = 0,
    reminder_interval_hours: int = None,
    max_reminders: int = 3,
    escalation_template_id: int = None,
    created_by: int = None
) -> int:
    """Create a notification rule."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO notification_rules (
                rule_name, module, event_type, template_id, recipient_type,
                recipient_id, delay_hours, reminder_interval_hours, max_reminders,
                escalation_template_id, is_active, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (rule_name, module, event_type, template_id, recipient_type,
              recipient_id, delay_hours, reminder_interval_hours, max_reminders,
              escalation_template_id, created_by))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# NOTIFICATION LOGS CRUD
# ============================================================================

def get_notification_logs(
    notification_template_id: int = None,
    workflow_instance_id: int = None,
    recipient_id: int = None,
    status: str = None,
    limit: int = 100
) -> List[Dict]:
    """Get notification delivery logs."""
    sql = "SELECT * FROM notification_logs WHERE 1=1"
    params = []

    if notification_template_id:
        sql += " AND notification_template_id = ?"
        params.append(notification_template_id)
    if workflow_instance_id:
        sql += " AND workflow_instance_id = ?"
        params.append(workflow_instance_id)
    if recipient_id:
        sql += " AND recipient_id = ?"
        params.append(recipient_id)
    if status:
        sql += " AND status = ?"
        params.append(status)

    sql += f" ORDER BY created_at DESC LIMIT {limit}"

    return get_all(sql, params)


def create_notification_log(
    notification_template_id: int,
    workflow_instance_id: int,
    recipient_type: str,
    recipient_id: int,
    recipient_address: str,
    channel: str,
    subject: str,
    body: str,
    status: str = 'pending'
) -> int:
    """Log a notification delivery."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO notification_logs (
                notification_template_id, workflow_instance_id, recipient_type,
                recipient_id, recipient_address, channel, subject, body, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (notification_template_id, workflow_instance_id, recipient_type,
              recipient_id, recipient_address, channel, subject, body, status))
        db.commit()
        return cursor.lastrowid


def update_notification_log(log_id: int, status: str, error_message: str = None) -> bool:
    """Update notification log status."""
    with get_db_context() as db:
        update_fields = "status = ?"
        params = [status]

        if status == 'sent':
            update_fields += ", sent_at = CURRENT_TIMESTAMP"
        elif status == 'delivered':
            update_fields += ", delivered_at = CURRENT_TIMESTAMP"
        elif status == 'read':
            update_fields += ", read_at = CURRENT_TIMESTAMP"
        elif status == 'failed':
            update_fields += ", error_message = ?"
            params.append(error_message)

        params.append(log_id)

        db.execute(f"UPDATE notification_logs SET {update_fields} WHERE id = ?", params)
        db.commit()
    return True


# ============================================================================
# SLA RULES CRUD
# ============================================================================

def get_sla_rule(rule_id: int = None, rule_code: str = None) -> Optional[Dict]:
    """Get an SLA rule."""
    if rule_id:
        return get_one("SELECT * FROM sla_rules WHERE id = ?", (rule_id,))
    elif rule_code:
        return get_one("SELECT * FROM sla_rules WHERE rule_code = ?", (rule_code,))
    return None


def get_sla_rules(workflow_type: str = None, step_type: str = None) -> List[Dict]:
    """Get SLA rules with filters."""
    sql = "SELECT * FROM sla_rules WHERE is_active = 1"
    params = []

    if workflow_type:
        sql += " AND workflow_type = ?"
        params.append(workflow_type)
    if step_type:
        sql += " AND step_type = ?"
        params.append(step_type)

    sql += " ORDER BY rule_name"

    return get_all(sql, params)


def create_sla_rule(
    rule_code: str,
    rule_name: str,
    workflow_type: str = None,
    step_type: str = None,
    duration_hours: int = 24,
    duration_type: str = 'hours',
    created_by: int = None
) -> int:
    """Create an SLA rule."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO sla_rules (rule_code, rule_name, workflow_type, step_type,
                                    duration_hours, duration_type, is_active, created_by)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """, (rule_code, rule_name, workflow_type, step_type,
              duration_hours, duration_type, created_by))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# ESCALATION RULES CRUD
# ============================================================================

def get_escalation_rule(rule_id: int = None, rule_code: str = None) -> Optional[Dict]:
    """Get an escalation rule."""
    if rule_id:
        return get_one("SELECT * FROM escalation_rules WHERE id = ?", (rule_id,))
    elif rule_code:
        return get_one("SELECT * FROM escalation_rules WHERE rule_code = ?", (rule_code,))
    return None


def get_escalation_rules(workflow_type: str = None, step_type: str = None) -> List[Dict]:
    """Get escalation rules with filters."""
    sql = "SELECT * FROM escalation_rules WHERE 1=1"
    params = []

    if workflow_type:
        sql += " AND workflow_type = ?"
        params.append(workflow_type)
    if step_type:
        sql += " AND step_type = ?"
        params.append(step_type)

    sql += " ORDER BY escalation_level, escalation_hours"

    return get_all(sql, params)


def create_escalation_rule(
    rule_code: str,
    rule_name: str,
    workflow_type: str = None,
    step_type: str = None,
    escalation_level: int = 1,
    escalation_hours: int = 24,
    escalation_action: str = 'reassign',
    escalation_target_type: str = 'role',
    escalation_target_id: int = None,
    created_by: int = None
) -> int:
    """Create an escalation rule."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO escalation_rules (
                rule_code, rule_name, workflow_type, step_type,
                escalation_level, escalation_hours, escalation_action,
                escalation_target_type, escalation_target_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (rule_code, rule_name, workflow_type, step_type,
              escalation_level, escalation_hours, escalation_action,
              escalation_target_type, escalation_target_id, created_by))
        db.commit()
        return cursor.lastrowid


def update_escalation_rule(rule_id: int, data: Dict) -> bool:
    """Update an escalation rule."""
    allowed_fields = ['rule_name', 'workflow_type', 'step_type', 'escalation_level',
                      'escalation_hours', 'escalation_action', 'escalation_target_type',
                      'escalation_target_id', 'is_active']

    fields = []
    values = []
    for key, value in data.items():
        if key in allowed_fields:
            fields.append(f"{key} = ?")
            values.append(value)

    if not fields:
        return False

    values.append(rule_id)

    with get_db_context() as db:
        db.execute(
            f"UPDATE escalation_rules SET {', '.join(fields)} WHERE id = ?",
            values
        )
        db.commit()
    return True


# ============================================================================
# DELEGATION RULES CRUD
# ============================================================================

def get_delegation_rules(delegator_id: int = None, delegate_id: int = None, active_only: bool = True) -> List[Dict]:
    """Get delegation rules."""
    sql = "SELECT * FROM delegation_rules WHERE 1=1"
    params = []

    if delegator_id:
        sql += " AND delegator_id = ?"
        params.append(delegator_id)
    if delegate_id:
        sql += " AND delegate_id = ?"
        params.append(delegate_id)
    if active_only:
        sql += " AND is_active = 1 AND start_date <= CURRENT_DATE AND end_date >= CURRENT_DATE"

    sql += " ORDER BY created_at DESC"

    return get_all(sql, params)


def create_delegation_rule(
    delegator_id: int,
    delegate_id: int,
    workflow_type: str = None,
    module_scope: str = None,
    start_date: str = None,
    end_date: str = None
) -> int:
    """Create a delegation rule."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO delegation_rules (
                delegator_id, delegate_id, workflow_type, module_scope,
                start_date, end_date, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, 1)
        """, (delegator_id, delegate_id, workflow_type, module_scope,
              start_date, end_date))
        db.commit()
        return cursor.lastrowid


def update_delegation_rule(rule_id: int, data: Dict) -> bool:
    """Update a delegation rule."""
    allowed_fields = ['delegate_id', 'workflow_type', 'module_scope', 'start_date', 'end_date', 'is_active']

    fields = []
    values = []
    for key, value in data.items():
        if key in allowed_fields:
            fields.append(f"{key} = ?")
            values.append(value)

    if not fields:
        return False

    values.append(rule_id)

    with get_db_context() as db:
        db.execute(
            f"UPDATE delegation_rules SET {', '.join(fields)} WHERE id = ?",
            values
        )
        db.commit()
    return True


def deactivate_delegation_rule(rule_id: int) -> bool:
    """Deactivate a delegation rule."""
    with get_db_context() as db:
        db.execute("UPDATE delegation_rules SET is_active = 0 WHERE id = ?", (rule_id,))
        db.commit()
    return True


# ============================================================================
# WORKFLOW TEMPLATES CRUD
# ============================================================================

def get_workflow_template(template_id: int = None, template_code: str = None) -> Optional[Dict]:
    """Get a workflow template."""
    if template_id:
        return get_one("SELECT * FROM workflow_templates WHERE id = ?", (template_id,))
    elif template_code:
        return get_one("SELECT * FROM workflow_templates WHERE template_code = ?", (template_code,))
    return None


def get_workflow_templates(is_active: bool = True) -> List[Dict]:
    """Get all workflow templates."""
    sql = "SELECT * FROM workflow_templates"
    if is_active:
        sql += " WHERE is_active = 1"
    sql += " ORDER BY template_name"
    return get_all(sql)


def create_workflow_template(
    template_code: str,
    template_name: str,
    workflow_type: str,
    module: str,
    entity_type: str,
    steps_json: List = None,
    conditions_json: List = None,
    created_by: int = None
) -> int:
    """Create a workflow template."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO workflow_templates (
                template_code, template_name, workflow_type, module, entity_type,
                steps_json, conditions_json, is_active, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (template_code, template_name, workflow_type, module, entity_type,
              json.dumps(steps_json) if steps_json else None,
              json.dumps(conditions_json) if conditions_json else None,
              created_by))
        db.commit()
        return cursor.lastrowid


def instantiate_from_template(template_id: int, created_by: int = None) -> int:
    """Create a workflow definition from a template."""
    template = get_workflow_template(template_id)
    if not template:
        return None

    # Create workflow definition
    workflow_def_id = create_workflow_definition(
        workflow_type=template['workflow_type'] + '_' + template['template_code'],
        name=template['template_name'],
        module=template['module'],
        entity_type=template['entity_type'],
        created_by=created_by
    )

    # Parse and create steps
    if template['steps_json']:
        steps = json.loads(template['steps_json']) if isinstance(template['steps_json'], str) else template['steps_json']
        version = get_one("SELECT MAX(version_number) as v FROM workflow_versions WHERE workflow_definition_id = ?",
                         (workflow_def_id,))
        version_id = get_one("SELECT id FROM workflow_versions WHERE workflow_definition_id = ? AND version_number = ?",
                            (workflow_def_id, version['v'] if version else 1))

        for step in steps:
            create_workflow_step(
                workflow_definition_id=workflow_def_id,
                version_id=version_id['id'] if version_id else 1,
                **step
            )

    return workflow_def_id


# ============================================================================
# WORKFLOW SETTINGS CRUD
# ============================================================================

def get_workflow_setting(setting_key: str, scope_type: str = 'GLOBAL', scope_id: int = None) -> Optional[str]:
    """Get a workflow setting value."""
    result = get_one("""
        SELECT setting_value FROM workflow_settings
        WHERE setting_key = ? AND scope_type = ? AND (scope_id = ? OR scope_id IS NULL)
        AND is_active = 1
    """, (setting_key, scope_type, scope_id))
    return result['setting_value'] if result else None


def get_workflow_settings(category: str = None, scope_type: str = 'GLOBAL', scope_id: int = None) -> Dict:
    """Get workflow settings as a dictionary."""
    sql = "SELECT setting_key, setting_value FROM workflow_settings WHERE is_active = 1"
    params = []

    if category:
        sql += " AND category = ?"
        params.append(category)
    if scope_type:
        sql += " AND scope_type = ?"
        params.append(scope_type)
    if scope_id:
        sql += " AND (scope_id = ? OR scope_id IS NULL)"
        params.append(scope_id)

    rows = get_all(sql, params)
    return {row['setting_key']: row['setting_value'] for row in rows}


def set_workflow_setting(
    setting_key: str,
    setting_value: str,
    category: str = 'GENERAL',
    description: str = None,
    scope_type: str = 'GLOBAL',
    scope_id: int = None,
    updated_by: int = None
) -> bool:
    """Set a workflow setting."""
    with get_db_context() as db:
        existing = db.execute("""
            SELECT id FROM workflow_settings
            WHERE setting_key = ? AND scope_type = ? AND (scope_id = ? OR scope_id IS NULL)
        """, (setting_key, scope_type, scope_id)).fetchone()

        if existing:
            db.execute("""
                UPDATE workflow_settings SET setting_value = ?, category = ?,
                    description = ?, updated_at = CURRENT_TIMESTAMP, updated_by = ?
                WHERE id = ?
            """, (setting_value, category, description, updated_by, existing['id']))
        else:
            db.execute("""
                INSERT INTO workflow_settings (setting_key, setting_value, category,
                                               description, scope_type, scope_id,
                                               is_active, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?)
            """, (setting_key, setting_value, category, description,
                  scope_type, scope_id, updated_by))

        db.commit()
    return True


# ============================================================================
# QUERY HELPERS
# ============================================================================

def get_pending_approvals(assigned_to_id: int = None, role_id: int = None,
                          company_id: int = None, limit: int = 100) -> List[Dict]:
    """Get pending approvals for a user (by user_id or role_id)."""
    sql = """
        SELECT wi.*, wd.name as workflow_name, wd.workflow_type,
               wd.module, ws.step_name as current_step_name
        FROM workflow_instances wi
        JOIN workflow_definitions wd ON wi.workflow_definition_id = wd.id
        LEFT JOIN workflow_steps ws ON wi.current_step_id = ws.id
        WHERE wi.current_state IN ('pending', 'under_review', 'submitted')
    """
    params = []

    if assigned_to_id:
        sql += " AND wi.assigned_to_id = ?"
        params.append(assigned_to_id)
    elif role_id:
        sql += " AND wi.assigned_to_type = 'role' AND wi.assigned_to_id = ?"
        params.append(role_id)

    if company_id:
        sql += " AND wi.company_id = ?"
        params.append(company_id)

    sql += f" ORDER BY wi.priority DESC, wi.created_at ASC LIMIT {limit}"

    return get_all(sql, params)


def get_overdue_instances(due_date_before: datetime = None) -> List[Dict]:
    """Get overdue workflow instances."""
    before_date = due_date_before or datetime.now()

    return get_all("""
        SELECT wi.*, wd.name as workflow_name, wd.workflow_type,
               ws.step_name as current_step_name
        FROM workflow_instances wi
        JOIN workflow_definitions wd ON wi.workflow_definition_id = wd.id
        LEFT JOIN workflow_steps ws ON wi.current_step_id = ws.id
        WHERE wi.current_state IN ('pending', 'under_review', 'submitted')
        AND wi.due_date IS NOT NULL AND wi.due_date < ?
        ORDER BY wi.due_date ASC
    """, (before_date,))


def get_workflow_stats(workflow_definition_id: int = None, company_id: int = None) -> Dict:
    """Get workflow statistics."""
    sql = """
        SELECT
            COUNT(*) as total_instances,
            SUM(CASE WHEN current_state = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN current_state = 'pending' OR current_state = 'under_review' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN current_state = 'rejected' THEN 1 ELSE 0 END) as rejected,
            SUM(CASE WHEN current_state = 'escalated' THEN 1 ELSE 0 END) as escalated,
            SUM(CASE WHEN due_date IS NOT NULL AND due_date < CURRENT_TIMESTAMP
                     AND current_state NOT IN ('completed', 'cancelled', 'rejected')
                     THEN 1 ELSE 0 END) as overdue
        FROM workflow_instances wi
        WHERE 1=1
    """
    params = []

    if workflow_definition_id:
        sql += " AND wi.workflow_definition_id = ?"
        params.append(workflow_definition_id)
    if company_id:
        sql += " AND wi.company_id = ?"
        params.append(company_id)

    result = get_one(sql, params)
    if not result:
        return {}
    # Ensure all numeric fields default to 0 instead of None
    for key in ('total_instances', 'completed', 'pending', 'rejected', 'escalated', 'overdue'):
        if key in result and result[key] is None:
            result[key] = 0
    return result


def get_my_work_items(user_id: int, limit: int = 50) -> List[Dict]:
    """Get workflow items assigned to a user."""
    return get_all("""
        SELECT wi.*, wd.name as workflow_name, wd.workflow_type,
               ws.step_name as current_step_name
        FROM workflow_instances wi
        JOIN workflow_definitions wd ON wi.workflow_definition_id = wd.id
        LEFT JOIN workflow_steps ws ON wi.current_step_id = ws.id
        WHERE wi.assigned_to_id = ? AND wi.current_state NOT IN ('completed', 'cancelled')
        ORDER BY wi.priority DESC, wi.created_at DESC LIMIT ?
    """, (user_id, limit))


def get_my_completed_items(user_id: int, limit: int = 50) -> List[Dict]:
    """Get workflow items completed by a user."""
    return get_all("""
        SELECT wi.*, wd.name as workflow_name, wd.workflow_type,
               ws.step_name as current_step_name
        FROM workflow_instances wi
        JOIN workflow_definitions wd ON wi.workflow_definition_id = wd.id
        LEFT JOIN workflow_steps ws ON wi.current_step_id = ws.id
        WHERE wi.assigned_to_id = ? AND wi.current_state = 'completed'
        ORDER BY wi.completed_at DESC LIMIT ?
    """, (user_id, limit))


def get_workflow_reports(workflow_definition_id: int = None, company_id: int = None) -> Dict:
    """Get workflow reports and analytics."""
    return {
        'stats': get_workflow_stats(workflow_definition_id, company_id),
        'by_state': get_all("""
            SELECT current_state as state, COUNT(*) as count
            FROM workflow_instances wi
            WHERE 1=1
            """ + (" AND workflow_definition_id = ?" if workflow_definition_id else "") +
            (" AND company_id = ?" if company_id else "") +
            " GROUP BY current_state",
            [x for x in [workflow_definition_id, company_id] if x])
    }


def get_workflow_history(source_entity_type: str = None, source_entity_id: int = None,
                         limit: int = 50) -> List[Dict]:
    """Get workflow history for an entity."""
    sql = """
        SELECT wa.*, wi.instance_code, wd.name as workflow_name,
               u.username as user_name
        FROM workflow_actions wa
        JOIN workflow_instances wi ON wa.workflow_instance_id = wi.id
        JOIN workflow_definitions wd ON wi.workflow_definition_id = wd.id
        LEFT JOIN users u ON wa.user_id = u.id
        WHERE 1=1
    """
    params = []

    if source_entity_type:
        sql += " AND wi.source_entity_type = ?"
        params.append(source_entity_type)
    if source_entity_id:
        sql += " AND wi.source_entity_id = ?"
        params.append(source_entity_id)

    sql += f" ORDER BY wa.created_at DESC LIMIT {limit}"

    return get_all(sql, params)


def get_user_workload(assigned_to_id: int = None) -> Dict:
    """Get workload summary for a user."""
    sql = """
        SELECT
            COUNT(*) as total_assigned,
            SUM(CASE WHEN current_state = 'pending' THEN 1 ELSE 0 END) as pending_count,
            SUM(CASE WHEN current_state = 'under_review' THEN 1 ELSE 0 END) as under_review_count,
            SUM(CASE WHEN current_state = 'escalated' THEN 1 ELSE 0 END) as escalated_count,
            SUM(CASE WHEN due_date IS NOT NULL AND due_date < CURRENT_TIMESTAMP
                     AND current_state NOT IN ('completed', 'cancelled')
                     THEN 1 ELSE 0 END) as overdue_count
        FROM workflow_instances
        WHERE assigned_to_id = ?
        AND current_state NOT IN ('completed', 'cancelled', 'draft')
    """
    result = get_one(sql, (assigned_to_id,))
    return dict(result) if result else {}


def resolve_assignee(assignee_type: str, assignee_id: int, context: Dict = None) -> Optional[Dict]:
    """Resolve actual user ID based on assignee type and context."""
    if assignee_type == 'user':
        return get_one("SELECT id, username as name FROM users WHERE id = ?", (assignee_id,))

    elif assignee_type == 'role':
        # Get first user with this role
        return get_one("""
            SELECT u.id, u.username as name
            FROM users u
            WHERE u.role_id = ? AND u.is_active = 1
            LIMIT 1
        """, (assignee_id,))

    elif assignee_type == 'department_manager' and context:
        department_id = context.get('department_id')
        if department_id:
            return get_one("""
                SELECT u.id, u.username as name
                FROM users u
                WHERE u.department_id = ? AND u.is_manager = 1
                LIMIT 1
            """, (department_id,))

    elif assignee_type == 'requester_manager' and context:
        requester_id = context.get('requester_id')
        if requester_id:
            requester = get_one("SELECT department_id FROM users WHERE id = ?", (requester_id,))
            if requester:
                return get_one("""
                    SELECT u.id, u.username as name
                    FROM users u
                    WHERE u.department_id = ? AND u.is_manager = 1
                    LIMIT 1
                """, (requester['department_id'],))

    elif assignee_type == 'dynamic' and context:
        # Dynamic assignment based on rules in context
        rule = context.get('assignee_rule', {})
        # Implementation depends on rule structure
        pass

    return None


# ============================================================================
# SCHEMA CREATION
# ============================================================================

def create_workflow_schema():
    """Create all workflow/BPM tables."""

    # 1. workflow_definitions
    if not table_exists('workflow_definitions'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE workflow_definitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_type TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    module TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    version INTEGER DEFAULT 1,
                    is_active INTEGER DEFAULT 1,
                    requires_approval INTEGER DEFAULT 1,
                    company_scope INTEGER,
                    branch_scope INTEGER,
                    department_scope INTEGER,
                    warehouse_scope INTEGER,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    updated_by INTEGER,
                    approved_by INTEGER,
                    approved_at TIMESTAMP,
                    activation_date TIMESTAMP,
                    deactivation_date TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_wfd_type ON workflow_definitions(workflow_type)")
            db.execute("CREATE INDEX idx_wfd_module ON workflow_definitions(module)")

    # 2. workflow_versions
    if not table_exists('workflow_versions'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE workflow_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_definition_id INTEGER NOT NULL,
                    version_number INTEGER NOT NULL,
                    version_label TEXT,
                    status TEXT DEFAULT 'draft',
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    FOREIGN KEY (workflow_definition_id) REFERENCES workflow_definitions(id)
                )
            """)
            db.execute("CREATE INDEX idx_wv_def ON workflow_versions(workflow_definition_id)")

    # 3. workflow_steps (extend existing)
    if table_exists('workflow_steps'):
        # Add missing columns if they don't exist
        from database import column_exists
        with get_db_context() as db:
            # Check for old column name and add new one if needed
            if column_exists('workflow_steps', 'workflow_id') and not column_exists('workflow_steps', 'workflow_definition_id'):
                db.execute("ALTER TABLE workflow_steps ADD COLUMN workflow_definition_id INTEGER")
                db.execute("UPDATE workflow_steps SET workflow_definition_id = workflow_id")
            if not column_exists('workflow_steps', 'version_id'):
                db.execute("ALTER TABLE workflow_steps ADD COLUMN version_id INTEGER")
            if not column_exists('workflow_steps', 'step_code'):
                db.execute("ALTER TABLE workflow_steps ADD COLUMN step_code TEXT")
            if not column_exists('workflow_steps', 'step_name'):
                db.execute("ALTER TABLE workflow_steps ADD COLUMN step_name TEXT")
            if not column_exists('workflow_steps', 'step_type'):
                db.execute("ALTER TABLE workflow_steps ADD COLUMN step_type TEXT DEFAULT 'approval'")
            if not column_exists('workflow_steps', 'assignee_type'):
                db.execute("ALTER TABLE workflow_steps ADD COLUMN assignee_type TEXT DEFAULT 'role'")
            if not column_exists('workflow_steps', 'assignee_id'):
                db.execute("ALTER TABLE workflow_steps ADD COLUMN assignee_id INTEGER")
            if not column_exists('workflow_steps', 'assignee_rule'):
                db.execute("ALTER TABLE workflow_steps ADD COLUMN assignee_rule TEXT")
            if not column_exists('workflow_steps', 'due_duration_hours'):
                db.execute("ALTER TABLE workflow_steps ADD COLUMN due_duration_hours INTEGER DEFAULT 24")
            if not column_exists('workflow_steps', 'due_duration_type'):
                db.execute("ALTER TABLE workflow_steps ADD COLUMN due_duration_type TEXT DEFAULT 'hours'")
            if not column_exists('workflow_steps', 'escalation_enabled'):
                db.execute("ALTER TABLE workflow_steps ADD COLUMN escalation_enabled INTEGER DEFAULT 0")
            if not column_exists('workflow_steps', 'escalation_level'):
                db.execute("ALTER TABLE workflow_steps ADD COLUMN escalation_level INTEGER DEFAULT 1")
            if not column_exists('workflow_steps', 'escalation_hours'):
                db.execute("ALTER TABLE workflow_steps ADD COLUMN escalation_hours INTEGER")
            if not column_exists('workflow_steps', 'allow_approve'):
                db.execute("ALTER TABLE workflow_steps ADD COLUMN allow_approve INTEGER DEFAULT 1")
            if not column_exists('workflow_steps', 'allow_reject'):
                db.execute("ALTER TABLE workflow_steps ADD COLUMN allow_reject INTEGER DEFAULT 1")
            if not column_exists('workflow_steps', 'allow_return'):
                db.execute("ALTER TABLE workflow_steps ADD COLUMN allow_return INTEGER DEFAULT 1")
            if not column_exists('workflow_steps', 'allow_skip'):
                db.execute("ALTER TABLE workflow_steps ADD COLUMN allow_skip INTEGER DEFAULT 0")
            if not column_exists('workflow_steps', 'require_comments'):
                db.execute("ALTER TABLE workflow_steps ADD COLUMN require_comments INTEGER DEFAULT 0")
            if not column_exists('workflow_steps', 'require_attachment'):
                db.execute("ALTER TABLE workflow_steps ADD COLUMN require_attachment INTEGER DEFAULT 0")
            if not column_exists('workflow_steps', 'completion_status'):
                db.execute("ALTER TABLE workflow_steps ADD COLUMN completion_status TEXT")
            db.commit()
    else:
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE workflow_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_definition_id INTEGER NOT NULL,
                    version_id INTEGER,
                    step_code TEXT,
                    step_name TEXT NOT NULL,
                    step_order INTEGER NOT NULL,
                    step_type TEXT DEFAULT 'approval',
                    assignee_type TEXT DEFAULT 'role',
                    assignee_id INTEGER,
                    assignee_rule TEXT,
                    due_duration_hours INTEGER DEFAULT 24,
                    due_duration_type TEXT DEFAULT 'hours',
                    escalation_enabled INTEGER DEFAULT 0,
                    escalation_level INTEGER DEFAULT 1,
                    escalation_hours INTEGER,
                    allow_approve INTEGER DEFAULT 1,
                    allow_reject INTEGER DEFAULT 1,
                    allow_return INTEGER DEFAULT 1,
                    allow_skip INTEGER DEFAULT 0,
                    require_comments INTEGER DEFAULT 0,
                    require_attachment INTEGER DEFAULT 0,
                    completion_status TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workflow_definition_id) REFERENCES workflow_definitions(id)
                )
            """)
            db.execute("CREATE INDEX idx_ws_def ON workflow_steps(workflow_definition_id)")
            db.execute("CREATE INDEX idx_ws_version ON workflow_steps(version_id)")

    # 4. workflow_transitions
    if not table_exists('workflow_transitions'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE workflow_transitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_definition_id INTEGER NOT NULL,
                    from_step_id INTEGER,
                    to_step_id INTEGER,
                    transition_type TEXT DEFAULT 'sequential',
                    condition_expression TEXT,
                    condition_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workflow_definition_id) REFERENCES workflow_definitions(id)
                )
            """)
            db.execute("CREATE INDEX idx_wt_def ON workflow_transitions(workflow_definition_id)")

    # 5. workflow_conditions
    if not table_exists('workflow_conditions'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE workflow_conditions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_transition_id INTEGER NOT NULL,
                    condition_type TEXT NOT NULL,
                    field_name TEXT,
                    operator TEXT,
                    field_value TEXT,
                    value_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workflow_transition_id) REFERENCES workflow_transitions(id)
                )
            """)

    # 6. workflow_instances
    if not table_exists('workflow_instances'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE workflow_instances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_definition_id INTEGER NOT NULL,
                    version_id INTEGER,
                    instance_code TEXT UNIQUE NOT NULL,
                    source_module TEXT NOT NULL,
                    source_entity_type TEXT NOT NULL,
                    source_entity_id INTEGER NOT NULL,
                    current_step_id INTEGER,
                    current_state TEXT DEFAULT 'draft',
                    requester_id INTEGER NOT NULL,
                    requester_name TEXT,
                    assigned_to_id INTEGER,
                    assigned_to_type TEXT,
                    assigned_to_name TEXT,
                    due_date TIMESTAMP,
                    due_duration_hours INTEGER,
                    escalation_level INTEGER DEFAULT 0,
                    escalation_count INTEGER DEFAULT 0,
                    last_escalated_at TIMESTAMP,
                    priority TEXT DEFAULT 'medium',
                    company_id INTEGER,
                    branch_id INTEGER,
                    department_id INTEGER,
                    warehouse_id INTEGER,
                    context_json TEXT,
                    submitted_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    cancelled_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    updated_at TIMESTAMP,
                    updated_by INTEGER,
                    FOREIGN KEY (workflow_definition_id) REFERENCES workflow_definitions(id)
                )
            """)
            db.execute("CREATE INDEX idx_wi_code ON workflow_instances(instance_code)")
            db.execute("CREATE INDEX idx_wi_state ON workflow_instances(current_state)")
            db.execute("CREATE INDEX idx_wi_requester ON workflow_instances(requester_id)")
            db.execute("CREATE INDEX idx_wi_assignee ON workflow_instances(assigned_to_id)")
            db.execute("CREATE INDEX idx_wi_entity ON workflow_instances(source_entity_type, source_entity_id)")

    # 7. workflow_instance_steps
    if not table_exists('workflow_instance_steps'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE workflow_instance_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_instance_id INTEGER NOT NULL,
                    workflow_step_id INTEGER,
                    step_code TEXT,
                    step_name TEXT,
                    step_order INTEGER,
                    executor_id INTEGER,
                    executor_name TEXT,
                    executor_type TEXT DEFAULT 'user',
                    action_taken TEXT,
                    comments TEXT,
                    attachments_json TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    due_date TIMESTAMP,
                    sla_remaining_hours REAL,
                    was_escalated INTEGER DEFAULT 0,
                    FOREIGN KEY (workflow_instance_id) REFERENCES workflow_instances(id)
                )
            """)
            db.execute("CREATE INDEX idx_wis_instance ON workflow_instance_steps(workflow_instance_id)")

    # 8. workflow_actions
    if not table_exists('workflow_actions'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE workflow_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_instance_id INTEGER NOT NULL,
                    workflow_step_id INTEGER,
                    user_id INTEGER,
                    action_type TEXT NOT NULL,
                    comments TEXT,
                    attachments_json TEXT,
                    previous_state TEXT,
                    new_state TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workflow_instance_id) REFERENCES workflow_instances(id)
                )
            """)
            db.execute("CREATE INDEX idx_wa_instance ON workflow_actions(workflow_instance_id)")

    # 9. workflow_assignments
    if not table_exists('workflow_assignments'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE workflow_assignments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_definition_id INTEGER NOT NULL,
                    step_code TEXT,
                    assignee_type TEXT NOT NULL,
                    assignee_id INTEGER,
                    assignee_rule_json TEXT,
                    priority_order INTEGER DEFAULT 1,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workflow_definition_id) REFERENCES workflow_definitions(id)
                )
            """)

    # 10. workflow_comments
    if not table_exists('workflow_comments'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE workflow_comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_instance_id INTEGER NOT NULL,
                    user_id INTEGER,
                    user_name TEXT,
                    comment TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workflow_instance_id) REFERENCES workflow_instances(id)
                )
            """)
            db.execute("CREATE INDEX idx_wc_instance ON workflow_comments(workflow_instance_id)")

    # 11. automation_rules
    if not table_exists('automation_rules'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE automation_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_code TEXT UNIQUE NOT NULL,
                    rule_name TEXT NOT NULL,
                    description TEXT,
                    module TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    condition_json TEXT,
                    action_json TEXT,
                    priority INTEGER DEFAULT 100,
                    is_active INTEGER DEFAULT 1,
                    scope_type TEXT,
                    scope_id INTEGER,
                    execution_count INTEGER DEFAULT 0,
                    last_executed_at TIMESTAMP,
                    last_execution_status TEXT,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    updated_by INTEGER,
                    approved_by INTEGER,
                    approved_at TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_ar_code ON automation_rules(rule_code)")
            db.execute("CREATE INDEX idx_ar_trigger ON automation_rules(trigger_type)")

    # 12. automation_rule_conditions
    if not table_exists('automation_rule_conditions'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE automation_rule_conditions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    automation_rule_id INTEGER NOT NULL,
                    condition_type TEXT NOT NULL,
                    field_name TEXT,
                    operator TEXT,
                    value TEXT,
                    value_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (automation_rule_id) REFERENCES automation_rules(id)
                )
            """)

    # 13. automation_rule_actions
    if not table_exists('automation_rule_actions'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE automation_rule_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    automation_rule_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    action_config_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (automation_rule_id) REFERENCES automation_rules(id)
                )
            """)

    # 14. automation_logs
    if not table_exists('automation_logs'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE automation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    automation_rule_id INTEGER,
                    workflow_instance_id INTEGER,
                    trigger_event TEXT,
                    action_taken TEXT,
                    result TEXT NOT NULL,
                    error_message TEXT,
                    execution_time_ms INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (automation_rule_id) REFERENCES automation_rules(id)
                )
            """)
            db.execute("CREATE INDEX idx_al_rule ON automation_logs(automation_rule_id)")
            db.execute("CREATE INDEX idx_al_instance ON automation_logs(workflow_instance_id)")

    # 15. notification_templates
    if not table_exists('notification_templates'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE notification_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_code TEXT UNIQUE NOT NULL,
                    template_name TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    channel TEXT DEFAULT 'in_app',
                    subject_template TEXT,
                    body_template TEXT,
                    is_html INTEGER DEFAULT 0,
                    variables_json TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    updated_by INTEGER
                )
            """)
            db.execute("CREATE INDEX idx_nt_code ON notification_templates(template_code)")

    # 16. notification_rules (extend existing)
    if table_exists('notification_rules'):
        from database import column_exists
        with get_db_context() as db:
            if not column_exists('notification_rules', 'template_id'):
                db.execute("ALTER TABLE notification_rules ADD COLUMN template_id INTEGER")
            if not column_exists('notification_rules', 'recipient_type'):
                db.execute("ALTER TABLE notification_rules ADD COLUMN recipient_type TEXT DEFAULT 'user'")
            if not column_exists('notification_rules', 'recipient_id'):
                db.execute("ALTER TABLE notification_rules ADD COLUMN recipient_id INTEGER")
            if not column_exists('notification_rules', 'delay_hours'):
                db.execute("ALTER TABLE notification_rules ADD COLUMN delay_hours INTEGER DEFAULT 0")
            if not column_exists('notification_rules', 'reminder_interval_hours'):
                db.execute("ALTER TABLE notification_rules ADD COLUMN reminder_interval_hours INTEGER")
            if not column_exists('notification_rules', 'max_reminders'):
                db.execute("ALTER TABLE notification_rules ADD COLUMN max_reminders INTEGER DEFAULT 3")
            if not column_exists('notification_rules', 'escalation_template_id'):
                db.execute("ALTER TABLE notification_rules ADD COLUMN escalation_template_id INTEGER")
            db.commit()

    # 17. notification_logs
    if not table_exists('notification_logs'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE notification_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    notification_template_id INTEGER,
                    workflow_instance_id INTEGER,
                    recipient_type TEXT NOT NULL,
                    recipient_id INTEGER,
                    recipient_address TEXT,
                    channel TEXT DEFAULT 'in_app',
                    subject TEXT,
                    body TEXT,
                    status TEXT DEFAULT 'pending',
                    sent_at TIMESTAMP,
                    delivered_at TIMESTAMP,
                    read_at TIMESTAMP,
                    error_message TEXT,
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (notification_template_id) REFERENCES notification_templates(id)
                )
            """)
            db.execute("CREATE INDEX idx_nl_template ON notification_logs(notification_template_id)")
            db.execute("CREATE INDEX idx_nl_instance ON notification_logs(workflow_instance_id)")
            db.execute("CREATE INDEX idx_nl_status ON notification_logs(status)")

    # 18. sla_rules
    if not table_exists('sla_rules'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE sla_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_code TEXT UNIQUE NOT NULL,
                    rule_name TEXT NOT NULL,
                    workflow_type TEXT,
                    step_type TEXT,
                    duration_hours INTEGER DEFAULT 24,
                    duration_type TEXT DEFAULT 'hours',
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)

    # 19. escalation_rules
    if not table_exists('escalation_rules'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE escalation_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_code TEXT UNIQUE NOT NULL,
                    rule_name TEXT NOT NULL,
                    workflow_type TEXT,
                    step_type TEXT,
                    escalation_level INTEGER DEFAULT 1,
                    escalation_hours INTEGER DEFAULT 24,
                    escalation_action TEXT DEFAULT 'reassign',
                    escalation_target_type TEXT,
                    escalation_target_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP
                )
            """)

    # 20. delegation_rules
    if not table_exists('delegation_rules'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE delegation_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    delegator_id INTEGER NOT NULL,
                    delegate_id INTEGER NOT NULL,
                    workflow_type TEXT,
                    module_scope TEXT,
                    start_date DATE,
                    end_date DATE,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_dr_delegator ON delegation_rules(delegator_id)")
            db.execute("CREATE INDEX idx_dr_delegate ON delegation_rules(delegate_id)")

    # 21. workflow_templates
    if not table_exists('workflow_templates'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE workflow_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_code TEXT UNIQUE NOT NULL,
                    template_name TEXT NOT NULL,
                    workflow_type TEXT NOT NULL,
                    module TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    steps_json TEXT,
                    conditions_json TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

    # 22. workflow_settings
    if not table_exists('workflow_settings'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE workflow_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT NOT NULL,
                    setting_value TEXT,
                    category TEXT DEFAULT 'GENERAL',
                    description TEXT,
                    scope_type TEXT DEFAULT 'GLOBAL',
                    scope_id INTEGER,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP,
                    updated_by INTEGER,
                    UNIQUE(setting_key, scope_type, scope_id)
                )
            """)
            db.execute("CREATE INDEX idx_ws_key ON workflow_settings(setting_key)")


# ============================================================================
# DEMO DATA SEEDING
# ============================================================================

def seed_workflow_demo_data():
    """Seed demo workflow data for testing."""

    # Check if already seeded
    existing = get_workflow_definition('sales_approval')
    if existing:
        return False

    # Get first user for created_by
    first_user = get_one("SELECT id FROM users LIMIT 1")
    user_id = first_user['id'] if first_user else 1

    # =====================================================================
    # 1. Create Workflow Definitions
    # =====================================================================

    # Sales Approval Workflow
    sales_wf_id = create_workflow_definition(
        workflow_type='sales_approval',
        name='Sales Order Approval',
        module='SALES',
        entity_type='sales_order',
        description='Approval workflow for sales orders exceeding credit limits',
        requires_approval=True,
        created_by=user_id
    )

    # Purchase Approval Workflow
    purchase_wf_id = create_workflow_definition(
        workflow_type='purchase_approval',
        name='Purchase Order Approval',
        module='PURCHASING',
        entity_type='purchase_order',
        description='Approval workflow for purchase orders',
        requires_approval=True,
        created_by=user_id
    )

    # Leave Approval Workflow
    leave_wf_id = create_workflow_definition(
        workflow_type='leave_approval',
        name='Leave Request Approval',
        module='HR',
        entity_type='leave_request',
        description='Approval workflow for employee leave requests',
        requires_approval=True,
        created_by=user_id
    )

    # Expense Approval Workflow
    expense_wf_id = create_workflow_definition(
        workflow_type='expense_approval',
        name='Expense Claim Approval',
        module='FINANCE',
        entity_type='expense_claim',
        description='Approval workflow for expense claims',
        requires_approval=True,
        created_by=user_id
    )

    # =====================================================================
    # 2. Create Workflow Steps for each definition
    # =====================================================================

    # Get version IDs
    sales_version = get_one("""
        SELECT id FROM workflow_versions
        WHERE workflow_definition_id = ? AND version_number = 1
    """, (sales_wf_id,))
    sales_version_id = sales_version['id'] if sales_version else 1

    purchase_version = get_one("""
        SELECT id FROM workflow_versions
        WHERE workflow_definition_id = ? AND version_number = 1
    """, (purchase_wf_id,))
    purchase_version_id = purchase_version['id'] if purchase_version else 2

    leave_version = get_one("""
        SELECT id FROM workflow_versions
        WHERE workflow_definition_id = ? AND version_number = 1
    """, (leave_wf_id,))
    leave_version_id = leave_version['id'] if leave_version else 3

    expense_version = get_one("""
        SELECT id FROM workflow_versions
        WHERE workflow_definition_id = ? AND version_number = 1
    """, (expense_wf_id,))
    expense_version_id = expense_version['id'] if expense_version else 4

    # Sales Workflow Steps
    create_workflow_step(sales_wf_id, sales_version_id, 'sales_submit', 'Initial Submission', 1,
                         step_type='approval', assignee_type='role', assignee_id=2,
                         due_duration_hours=24, allow_approve=True, allow_reject=True)
    create_workflow_step(sales_wf_id, sales_version_id, 'sales_manager', 'Sales Manager Review', 2,
                         step_type='approval', assignee_type='role', assignee_id=3,
                         due_duration_hours=48, allow_approve=True, allow_reject=True, allow_return=True)
    create_workflow_step(sales_wf_id, sales_version_id, 'sales_final', 'Final Approval', 3,
                         step_type='finalization', assignee_type='role', assignee_id=1,
                         due_duration_hours=24, allow_approve=True, allow_reject=True)

    # Purchase Workflow Steps
    create_workflow_step(purchase_wf_id, purchase_version_id, 'purchase_submit', 'Purchase Request', 1,
                         step_type='approval', assignee_type='role', assignee_id=4,
                         due_duration_hours=24, allow_approve=True, allow_reject=True)
    create_workflow_step(purchase_wf_id, purchase_version_id, 'purchase_manager', 'Manager Approval', 2,
                         step_type='approval', assignee_type='role', assignee_id=1,
                         due_duration_hours=48, allow_approve=True, allow_reject=True, allow_return=True)
    create_workflow_step(purchase_wf_id, purchase_version_id, 'purchase_final', 'Finance Approval', 3,
                         step_type='approval', assignee_type='role', assignee_id=5,
                         due_duration_hours=24, allow_approve=True, allow_reject=True)

    # Leave Workflow Steps
    create_workflow_step(leave_wf_id, leave_version_id, 'leave_submit', 'Leave Application', 1,
                         step_type='approval', assignee_type='supervisor', assignee_id=None,
                         due_duration_hours=24, allow_approve=True, allow_reject=True, allow_return=True)
    create_workflow_step(leave_wf_id, leave_version_id, 'leave_hr', 'HR Verification', 2,
                         step_type='verification', assignee_type='role', assignee_id=6,
                         due_duration_hours=12, allow_approve=True, allow_reject=True)
    create_workflow_step(leave_wf_id, leave_version_id, 'leave_final', 'Final Approval', 3,
                         step_type='finalization', assignee_type='department_manager', assignee_id=None,
                         due_duration_hours=24, allow_approve=True, allow_reject=True)

    # Expense Workflow Steps
    create_workflow_step(expense_wf_id, expense_version_id, 'expense_submit', 'Expense Submission', 1,
                         step_type='approval', assignee_type='role', assignee_id=2,
                         due_duration_hours=24, allow_approve=True, allow_reject=True)
    create_workflow_step(expense_wf_id, expense_version_id, 'expense_manager', 'Manager Approval', 2,
                         step_type='approval', assignee_type='role', assignee_id=3,
                         due_duration_hours=48, allow_approve=True, allow_reject=True, allow_return=True)
    create_workflow_step(expense_wf_id, expense_version_id, 'expense_finance', 'Finance Review', 3,
                         step_type='verification', assignee_type='role', assignee_id=5,
                         due_duration_hours=24, allow_approve=True, allow_reject=True)
    create_workflow_step(expense_wf_id, expense_version_id, 'expense_final', 'Final Approval', 4,
                         step_type='finalization', assignee_type='role', assignee_id=1,
                         due_duration_hours=12, allow_approve=True, allow_reject=True)

    # =====================================================================
    # 3. Create Workflow Instances (10-15 instances in various states)
    # =====================================================================

    # Get some step IDs
    step1 = get_one("SELECT id FROM workflow_steps WHERE workflow_definition_id = ? AND step_order = 1",
                   (sales_wf_id,))
    step2 = get_one("SELECT id FROM workflow_steps WHERE workflow_definition_id = ? AND step_order = 2",
                   (sales_wf_id,))
    step3 = get_one("SELECT id FROM workflow_steps WHERE workflow_definition_id = ? AND step_order = 1",
                   (purchase_wf_id,))
    step4 = get_one("SELECT id FROM workflow_steps WHERE workflow_definition_id = ? AND step_order = 1",
                   (leave_wf_id,))
    step5 = get_one("SELECT id FROM workflow_steps WHERE workflow_definition_id = ? AND step_order = 1",
                   (expense_wf_id,))

    context_data = {
        'amount': 50000,
        'customer': 'ABC Corporation',
        'items': ['Item A', 'Item B'],
        'notes': 'Urgent order for monthly supply'
    }

    # Instance 1: Pending at Sales Manager
    code1 = create_workflow_instance(
        sales_wf_id, sales_version_id, 'SALES', 'sales_order', 1001,
        requester_id=2, requester_name='John Smith', priority='high',
        context_json=context_data
    )
    if step1:
        advance_workflow_instance(code1 if isinstance(code1, int) else get_workflow_instance(instance_code=code1)['id'],
                                  step1['id'], 'pending', 'submit', user_id=2, user_name='John Smith')
    if step2:
        inst1 = get_workflow_instance(instance_code=code1)
        update_workflow_instance(inst1['id'], {
            'current_state': 'under_review',
            'current_step_id': step2['id'],
            'assigned_to_id': 3,
            'assigned_to_type': 'role',
            'assigned_to_name': 'Sales Manager'
        })

    # Instance 2: Pending at Initial
    code2 = create_workflow_instance(
        sales_wf_id, sales_version_id, 'SALES', 'sales_order', 1002,
        requester_id=2, requester_name='John Smith', priority='medium',
        context_json={'amount': 25000, 'customer': 'XYZ Ltd'}
    )

    # Instance 3: Completed
    code3 = create_workflow_instance(
        sales_wf_id, sales_version_id, 'SALES', 'sales_order', 1003,
        requester_id=3, requester_name='Jane Doe', priority='low',
        context_json={'amount': 15000, 'customer': 'Small Biz'}
    )

    # Instance 4: Rejected
    code4 = create_workflow_instance(
        purchase_wf_id, purchase_version_id, 'PURCHASING', 'purchase_order', 2001,
        requester_id=4, requester_name='Bob Wilson', priority='high',
        context_json={'amount': 100000, 'items': ['Raw Materials']}
    )
    if step3:
        inst4 = get_workflow_instance(instance_code=code4)
        update_workflow_instance(inst4['id'], {'current_state': 'rejected'})

    # Instance 5: Pending Leave
    code5 = create_workflow_instance(
        leave_wf_id, leave_version_id, 'HR', 'leave_request', 3001,
        requester_id=5, requester_name='Alice Brown', priority='medium',
        context_json={'leave_type': 'Annual', 'days': 5, 'start_date': '2026-04-15'}
    )

    # Instance 6: Pending Leave
    code6 = create_workflow_instance(
        leave_wf_id, leave_version_id, 'HR', 'leave_request', 3002,
        requester_id=6, requester_name='Charlie Green', priority='low',
        context_json={'leave_type': 'Sick', 'days': 2, 'start_date': '2026-04-10'}
    )

    # Instance 7: Pending Expense
    code7 = create_workflow_instance(
        expense_wf_id, expense_version_id, 'FINANCE', 'expense_claim', 4001,
        requester_id=2, requester_name='John Smith', priority='high',
        context_json={'amount': 5000, 'category': 'Travel', 'description': 'Client meeting travel'}
    )

    # Instance 8: Pending Expense
    code8 = create_workflow_instance(
        expense_wf_id, expense_version_id, 'FINANCE', 'expense_claim', 4002,
        requester_id=3, requester_name='Jane Doe', priority='medium',
        context_json={'amount': 2500, 'category': 'Meals', 'description': 'Team dinner'}
    )

    # Instance 9: Under Review - Sales
    code9 = create_workflow_instance(
        sales_wf_id, sales_version_id, 'SALES', 'sales_order', 1004,
        requester_id=4, requester_name='Bob Wilson', priority='critical',
        context_json={'amount': 200000, 'customer': 'Enterprise Co'}
    )
    if step2:
        inst9 = get_workflow_instance(instance_code=code9)
        update_workflow_instance(inst9['id'], {
            'current_state': 'under_review',
            'current_step_id': step2['id'],
            'assigned_to_id': 3,
            'assigned_to_type': 'role'
        })

    # Instance 10: Escalated
    code10 = create_workflow_instance(
        purchase_wf_id, purchase_version_id, 'PURCHASING', 'purchase_order', 2002,
        requester_id=5, requester_name='Alice Brown', priority='high',
        context_json={'amount': 75000, 'items': ['Equipment']}
    )
    inst10 = get_workflow_instance(instance_code=code10)
    update_workflow_instance(inst10['id'], {
        'current_state': 'escalated',
        'escalation_level': 2,
        'escalation_count': 1
    })

    # Instance 11: Pending Purchase
    code11 = create_workflow_instance(
        purchase_wf_id, purchase_version_id, 'PURCHASING', 'purchase_order', 2003,
        requester_id=6, requester_name='Charlie Green', priority='medium',
        context_json={'amount': 45000, 'items': ['Supplies']}
    )

    # Instance 12: Completed Leave
    code12 = create_workflow_instance(
        leave_wf_id, leave_version_id, 'HR', 'leave_request', 3003,
        requester_id=7, requester_name='David Lee', priority='low',
        context_json={'leave_type': 'Annual', 'days': 3, 'start_date': '2026-03-20'}
    )
    inst12 = get_workflow_instance(instance_code=code12)
    update_workflow_instance(inst12['id'], {'current_state': 'completed', 'completed_at': datetime.now()})

    # Instance 13: Returned
    code13 = create_workflow_instance(
        expense_wf_id, expense_version_id, 'FINANCE', 'expense_claim', 4003,
        requester_id=4, requester_name='Bob Wilson', priority='medium',
        context_json={'amount': 8000, 'category': 'Equipment', 'description': 'Office supplies'}
    )
    inst13 = get_workflow_instance(instance_code=code13)
    update_workflow_instance(inst13['id'], {'current_state': 'returned'})

    # Instance 14: Pending Sales
    code14 = create_workflow_instance(
        sales_wf_id, sales_version_id, 'SALES', 'sales_order', 1005,
        requester_id=7, requester_name='David Lee', priority='medium',
        context_json={'amount': 35000, 'customer': 'New Customer LLC'}
    )

    # Instance 15: Cancelled
    code15 = create_workflow_instance(
        sales_wf_id, sales_version_id, 'SALES', 'sales_order', 1006,
        requester_id=2, requester_name='John Smith', priority='low',
        context_json={'amount': 12000, 'customer': 'Old Customer'}
    )
    inst15 = get_workflow_instance(instance_code=code15)
    update_workflow_instance(inst15['id'], {'current_state': 'cancelled', 'cancelled_at': datetime.now()})

    # =====================================================================
    # 4. Create Automation Rules (3-5 rules)
    # =====================================================================

    # Rule 1: Auto-escalate overdue items
    create_automation_rule(
        rule_code='auto_escalate_overdue',
        rule_name='Auto Escalate Overdue Workflows',
        module='WORKFLOW',
        entity_type='workflow_instance',
        trigger_type='on_overdue',
        description='Automatically escalate workflows that exceed SLA',
        priority=100,
        action_json={'action': 'escalate', 'level_increment': 1},
        created_by=user_id
    )

    # Rule 2: Send notification on approval
    create_automation_rule(
        rule_code='notify_on_approval',
        rule_name='Notify on Workflow Approval',
        module='WORKFLOW',
        entity_type='workflow_instance',
        trigger_type='on_approval',
        description='Send notification when a workflow is approved',
        priority=90,
        action_json={'action': 'send_notification', 'template': 'approval_notification'},
        created_by=user_id
    )

    # Rule 3: Auto-assign based on amount
    create_automation_rule(
        rule_code='auto_assign_high_value',
        rule_name='Auto-assign High Value Orders',
        module='SALES',
        entity_type='sales_order',
        trigger_type='on_create',
        description='Auto-assign high value orders to senior manager',
        priority=80,
        condition_json={'field': 'amount', 'operator': 'gt', 'value': 100000},
        action_json={'action': 'assign_user', 'assign_to_role': 1},
        created_by=user_id
    )

    # Rule 4: Reminder for pending approvals
    create_automation_rule(
        rule_code='reminder_pending',
        rule_name='Pending Approval Reminder',
        module='WORKFLOW',
        entity_type='workflow_instance',
        trigger_type='on_schedule',
        description='Send reminders for pending approvals older than 24 hours',
        priority=70,
        condition_json={'field': 'current_state', 'operator': 'in', 'value': ['pending', 'under_review']},
        action_json={'action': 'send_notification', 'template': 'reminder_notification', 'delay_hours': 24},
        created_by=user_id
    )

    # Rule 5: Auto-reject stale requests
    create_automation_rule(
        rule_code='auto_reject_stale',
        rule_name='Auto-reject Stale Requests',
        module='PURCHASING',
        entity_type='purchase_order',
        trigger_type='on_overdue',
        description='Auto-reject purchase requests overdue by more than 72 hours',
        priority=60,
        condition_json={'field': 'overdue_hours', 'operator': 'gt', 'value': 72},
        action_json={'action': 'auto_reject', 'notify_requester': True},
        created_by=user_id
    )

    # =====================================================================
    # 5. Create Notification Templates
    # =====================================================================

    create_notification_template(
        template_code='wf_approval_request',
        template_name='Workflow Approval Request',
        event_type='approval_required',
        channel='in_app',
        subject_template='Approval Required: {{workflow_name}}',
        body_template='You have a new approval request for {{entity_type}} from {{requester_name}}. Amount: {{amount}}. Please review and take action.',
        variables_json=['workflow_name', 'entity_type', 'requester_name', 'amount']
    )

    create_notification_template(
        template_code='wf_approval_complete',
        template_name='Workflow Approval Complete',
        event_type='approval_complete',
        channel='in_app',
        subject_template='{{workflow_name}} - {{action}}',
        body_template='Your {{entity_type}} request has been {{action}} by {{approver_name}}.',
        variables_json=['workflow_name', 'entity_type', 'action', 'approver_name']
    )

    create_notification_template(
        template_code='wf_escalation',
        template_name='Workflow Escalation',
        event_type='escalation',
        channel='in_app',
        subject_template='ESCALATION: {{workflow_name}}',
        body_template='Workflow instance {{instance_code}} has been escalated to level {{escalation_level}} due to overdue.',
        variables_json=['instance_code', 'workflow_name', 'escalation_level']
    )

    create_notification_template(
        template_code='wf_reminder',
        template_name='Workflow Reminder',
        event_type='reminder',
        channel='email',
        subject_template='Reminder: Pending Approval - {{workflow_name}}',
        body_template='This is a reminder that you have a pending approval for {{workflow_name}} that requires your attention.',
        variables_json=['workflow_name', 'days_pending']
    )

    # =====================================================================
    # 6. Create SLA Rules
    # =====================================================================

    create_sla_rule('sales_approval_sla', 'Sales Approval SLA', 'sales_approval', 'approval', 24, 'hours')
    create_sla_rule('purchase_approval_sla', 'Purchase Approval SLA', 'purchase_approval', 'approval', 48, 'hours')
    create_sla_rule('leave_approval_sla', 'Leave Approval SLA', 'leave_approval', 'approval', 12, 'hours')
    create_sla_rule('expense_approval_sla', 'Expense Approval SLA', 'expense_approval', 'approval', 24, 'hours')
    create_sla_rule('critical_sla', 'Critical Priority SLA', None, 'approval', 4, 'hours')

    # =====================================================================
    # 7. Create Escalation Rules
    # =====================================================================

    create_escalation_rule('sales_escalate_1', 'Sales Escalation Level 1', 'sales_approval', 'approval',
                           1, 24, 'notify', 'role', 3)
    create_escalation_rule('sales_escalate_2', 'Sales Escalation Level 2', 'sales_approval', 'approval',
                           2, 48, 'reassign', 'role', 1)
    create_escalation_rule('purchase_escalate_1', 'Purchase Escalation Level 1', 'purchase_approval', 'approval',
                           1, 48, 'notify', 'role', 4)
    create_escalation_rule('purchase_escalate_2', 'Purchase Escalation Level 2', 'purchase_approval', 'approval',
                           2, 72, 'escalate_to_role', 'role', 1)
    create_escalation_rule('leave_escalate_1', 'Leave Escalation Level 1', 'leave_approval', 'approval',
                           1, 24, 'notify', 'role', 6)

    # =====================================================================
    # 8. Create Workflow Settings
    # =====================================================================

    set_workflow_setting('default_priority', 'medium', 'WORKFLOW', 'Default workflow priority')
    set_workflow_setting('enable_escalation', '1', 'WORKFLOW', 'Enable automatic escalation')
    set_workflow_setting('escalation_check_interval', '60', 'WORKFLOW', 'Escalation check interval in minutes')
    set_workflow_setting('max_escalation_level', '3', 'WORKFLOW', 'Maximum escalation level')
    set_workflow_setting('enable_auto_complete', '1', 'WORKFLOW', 'Enable automatic workflow completion')
    set_workflow_setting('require_comments_reject', '1', 'WORKFLOW', 'Require comments on rejection')
    set_workflow_setting('enable_delegation', '1', 'WORKFLOW', 'Enable workflow delegation')

    return True


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_workflow_schema():
    """Initialize all workflow/BPM tables and seed demo data."""
    create_workflow_schema()
    seed_workflow_demo_data()


# NOTE: Auto-initialization on import has been REMOVED.
# Tables are now created through Alembic migrations.
# To initialize manually: initialize_workflow_schema()
