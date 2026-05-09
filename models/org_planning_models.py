"""
Organizational Planning & BPM Module - Database Models
======================================================
Comprehensive database models for the Organizational Planning & BPM platform.

This module provides:
- Organizational Structure (company, divisions, departments, units)
- Positions & Roles Management
- Reporting Lines & Chains of Command
- Headcount & Workforce Planning
- Delegation & Substitution Framework
- Approval Matrix
- BPM Process Models
- Process Instances & Running Cases
- SLA & Escalation Center
- Automation Rules
- Process Monitoring & Analytics
- Reorganization & Change Simulation

Required Tables (35+):
    1. op_companies              - Company hierarchy root
    2. op_org_units              - Organizational units (all levels)
    3. op_positions              - Position/job title definitions
    4. op_reporting_lines        - Reporting relationships
    5. op_headcount_plans        - Headcount planning records
    6. op_headcount_actuals      - Actual headcount snapshots
    7. op_delegations            - Delegation rules
    8. op_approval_matrix        - Approval routing rules
    9. op_approval_conditions    - Conditional approval rules
    10. op_workflow_definitions   - BPM process definitions
    11. op_workflow_versions      - Version tracking
    12. op_workflow_steps        - Step definitions
    13. op_workflow_transitions  - State transitions
    14. op_workflow_conditions   - Conditional routing
    15. op_process_instances     - Running workflow instances
    16. op_instance_steps        - Step execution history
    17. op_instance_actions      - Actions on instances
    18. op_instance_comments     - Comments/notes
    19. op_sla_policies          - SLA definitions
    20. op_sla_records           - SLA tracking
    21. op_escalation_rules      - Escalation chains
    22. op_escalation_logs       - Escalation history
    23. op_automation_rules      - Automation rules
    24. op_automation_conditions - Rule conditions
    25. op_automation_actions    - Rule actions
    26. op_automation_logs       - Execution logs
    27. op_simulation_scenarios  - Reorg simulations
    28. op_simulation_impacts    - Impact analysis
    29. op_org_history           - Historical snapshots
    30. op_audit_logs            - Change audit trail
    31. op_dashboard_widgets     - Dashboard configurations
    32. op_notifications         - In-app notifications
    33. op_settings              - Module settings
"""

import json
import uuid
from datetime import datetime, timedelta, date
from typing import Optional, Dict, List, Any
from database import get_db_context, get_one, get_all, table_exists, log_audit

# ============================================================================
# CONSTANTS AND ENUMERATIONS
# ============================================================================

# Org Unit Types
ORG_UNIT_TYPES = {
    'company': 'Company',
    'subsidiary': 'Subsidiary',
    'business_unit': 'Business Unit',
    'division': 'Division',
    'department': 'Department',
    'section': 'Section',
    'team': 'Team',
    'sub_team': 'Sub-Team',
    'branch': 'Branch',
    'facility': 'Facility',
    'warehouse': 'Warehouse',
    'site': 'Site'
}

# Position Levels
POSITION_LEVELS = {
    'executive': 'Executive (C-Level)',
    'vp': 'Vice President',
    'director': 'Director',
    'senior_manager': 'Senior Manager',
    'manager': 'Manager',
    'assistant_manager': 'Assistant Manager',
    'supervisor': 'Supervisor',
    'senior': 'Senior',
    'junior': 'Junior',
    'entry': 'Entry Level',
    'intern': 'Intern'
}

# Employment Types
EMPLOYMENT_TYPES = {
    'full_time': 'Full-Time',
    'part_time': 'Part-Time',
    'contract': 'Contract',
    'temporary': 'Temporary',
    'internship': 'Internship',
    'freelance': 'Freelance'
}

# Headcount Status
HEADCOUNT_STATUS = {
    'approved': 'Approved',
    'planned': 'Planned',
    'vacant': 'Vacant',
    'frozen': 'Frozen',
    'requested': 'Requested'
}

# Delegation Types
DELEGATION_TYPES = {
    'temporary': 'Temporary Delegation',
    'permanent': 'Permanent Delegation',
    'leave_based': 'Leave-Based Substitution',
    'conditional': 'Conditional Delegation',
    'emergency': 'Emergency Fallback'
}

# Workflow/Process States
WORKFLOW_STATES = {
    'draft': 'Draft',
    'published': 'Published',
    'archived': 'Archived',
    'active': 'Active'
}

PROCESS_STATES = {
    'initiated': 'Initiated',
    'in_progress': 'In Progress',
    'pending': 'Pending',
    'approved': 'Approved',
    'rejected': 'Rejected',
    'completed': 'Completed',
    'cancelled': 'Cancelled',
    'on_hold': 'On Hold'
}

STEP_STATES = {
    'pending': 'Pending',
    'in_progress': 'In Progress',
    'approved': 'Approved',
    'rejected': 'Rejected',
    'skipped': 'Skipped',
    'returned': 'Returned'
}

# SLA Priority
SLA_PRIORITIES = {
    'critical': 'Critical',
    'high': 'High',
    'medium': 'Medium',
    'low': 'Low'
}

# Approval Types
APPROVAL_TYPES = {
    'sequential': 'Sequential',
    'parallel': 'Parallel',
    'conditional': 'Conditional',
    'anyone': 'Any Approver (Anyone)'
}

# Automation Trigger Types
AUTOMATION_TRIGGERS = {
    'on_create': 'On Record Create',
    'on_update': 'On Record Update',
    'on_delete': 'On Record Delete',
    'on_status_change': 'On Status Change',
    'on_schedule': 'On Schedule',
    'on_sla_breach': 'On SLA Breach',
    'on_approval': 'On Approval',
    'on_rejection': 'On Rejection',
    'on_date': 'On Specific Date',
    'on_condition': 'When Condition Met'
}

# Automation Action Types
AUTOMATION_ACTIONS = {
    'create_task': 'Create Task',
    'assign_task': 'Assign Task',
    'send_notification': 'Send Notification',
    'send_email': 'Send Email',
    'send_sms': 'Send SMS',
    'update_field': 'Update Field',
    'change_status': 'Change Status',
    'escalate': 'Escalate',
    'delegate': 'Delegate',
    'approve': 'Auto Approve',
    'reject': 'Auto Reject',
    'create_record': 'Create Record',
    'call_webhook': 'Call Webhook',
    'start_workflow': 'Start Workflow',
    'add_comment': 'Add Comment',
    'attach_document': 'Attach Document'
}

# Simulation Status
SIMULATION_STATUS = {
    'draft': 'Draft',
    'published': 'Published',
    'archived': 'Archived'
}

# ============================================================================
# DATABASE CONNECTION
# ============================================================================

def get_db():
    """Get database connection with Row factory for dict-like access."""
    from database import get_db
    return get_db()

# ============================================================================
# ORG PLANNING TABLE DEFINITIONS
# ============================================================================

ORG_PLANNING_TABLES = [
    # -------------------------------------------------------------------------
    # 1. Companies - Root of Org Hierarchy
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name_ar TEXT,
        name_fa TEXT,
        code TEXT UNIQUE,
        registration_number TEXT,
        tax_id TEXT,
        logo TEXT,
        address TEXT,
        city TEXT,
        country TEXT,
        phone TEXT,
        email TEXT,
        website TEXT,
        parent_company_id INTEGER,
        is_active INTEGER DEFAULT 1,
        effective_date DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_company_id) REFERENCES op_companies(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 2. Organizational Units - Full Hierarchy
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_org_units (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_id INTEGER NOT NULL,
        parent_id INTEGER,
        unit_type TEXT NOT NULL,
        name TEXT NOT NULL,
        name_ar TEXT,
        name_fa TEXT,
        code TEXT,
        description TEXT,
        cost_center TEXT,
        budget DECIMAL(15,2) DEFAULT 0,
        head_position_id INTEGER,
        head_employee_id INTEGER,
        location TEXT,
        address TEXT,
        phone TEXT,
        email TEXT,
        employee_count INTEGER DEFAULT 0,
        sort_order INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        effective_date DATE DEFAULT (date('now')),
        end_date DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES op_companies(id) ON DELETE CASCADE,
        FOREIGN KEY (parent_id) REFERENCES op_org_units(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 3. Positions - Position Management
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_unit_id INTEGER,
        position_code TEXT UNIQUE,
        title TEXT NOT NULL,
        title_ar TEXT,
        title_fa TEXT,
        level TEXT DEFAULT 'junior',
        grade TEXT,
        salary_band_min DECIMAL(12,2) DEFAULT 0,
        salary_band_max DECIMAL(12,2) DEFAULT 0,
        employment_type TEXT DEFAULT 'full_time',
        headcount_approved INTEGER DEFAULT 1,
        headcount_budgeted INTEGER DEFAULT 1,
        is_critical INTEGER DEFAULT 0,
        is_supervisor INTEGER DEFAULT 0,
        requires_approval INTEGER DEFAULT 1,
        parent_position_id INTEGER,
        reports_to_position_id INTEGER,
        responsibilities TEXT,
        requirements TEXT,
        skills_required TEXT,
        linked_permission_template TEXT,
        approval_authority_level INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1,
        effective_date DATE DEFAULT (date('now')),
        end_date DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (org_unit_id) REFERENCES op_org_units(id) ON DELETE SET NULL,
        FOREIGN KEY (parent_position_id) REFERENCES op_positions(id) ON DELETE SET NULL,
        FOREIGN KEY (reports_to_position_id) REFERENCES op_positions(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 4. Position Incumbents - Who Holds Which Position
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_position_incumbents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        position_id INTEGER NOT NULL,
        employee_id INTEGER,
        user_id INTEGER,
        incumbent_type TEXT DEFAULT 'primary',
        start_date DATE DEFAULT (date('now')),
        end_date DATE,
        is_active INTEGER DEFAULT 1,
        is_acting INTEGER DEFAULT 0,
        is_interim INTEGER DEFAULT 0,
        is_successor INTEGER DEFAULT 0,
        status TEXT DEFAULT 'Filled',
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (position_id) REFERENCES op_positions(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 5. Reporting Lines - Chain of Command
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_reporting_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        position_id INTEGER NOT NULL,
        reports_to_position_id INTEGER NOT NULL,
        reporting_type TEXT DEFAULT 'direct',
        is_primary INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1,
        effective_date DATE DEFAULT (date('now')),
        end_date DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (position_id) REFERENCES op_positions(id) ON DELETE CASCADE,
        FOREIGN KEY (reports_to_position_id) REFERENCES op_positions(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 6. Headcount Plans - Planning Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_headcount_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_unit_id INTEGER NOT NULL,
        position_id INTEGER,
        plan_year INTEGER NOT NULL,
        plan_period TEXT DEFAULT 'annual',
        headcount_approved INTEGER DEFAULT 0,
        headcount_planned INTEGER DEFAULT 0,
        headcount_current INTEGER DEFAULT 0,
        headcount_vacant INTEGER DEFAULT 0,
        headcount_requested INTEGER DEFAULT 0,
        headcount_frozen INTEGER DEFAULT 0,
        budget_allocated DECIMAL(15,2) DEFAULT 0,
        budget_used DECIMAL(15,2) DEFAULT 0,
        notes TEXT,
        status TEXT DEFAULT 'Draft',
        created_by INTEGER,
        approved_by INTEGER,
        approved_at DATETIME,
        effective_date DATE DEFAULT (date('now')),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (org_unit_id) REFERENCES op_org_units(id) ON DELETE CASCADE,
        FOREIGN KEY (position_id) REFERENCES op_positions(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 7. Headcount Actuals - Monthly Snapshots
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_headcount_actuals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_unit_id INTEGER NOT NULL,
        position_id INTEGER,
        snapshot_date DATE NOT NULL,
        actual_headcount INTEGER DEFAULT 0,
        new_hires INTEGER DEFAULT 0,
        terminations INTEGER DEFAULT 0,
        transfers_in INTEGER DEFAULT 0,
        transfers_out INTEGER DEFAULT 0,
        vacant_positions INTEGER DEFAULT 0,
        contract_workers INTEGER DEFAULT 0,
        overtime_hours DECIMAL(6,2) DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (org_unit_id) REFERENCES op_org_units(id) ON DELETE CASCADE,
        FOREIGN KEY (position_id) REFERENCES op_positions(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 8. Delegations - Substitution Rules
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_delegations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        delegator_id INTEGER NOT NULL,
        delegate_id INTEGER NOT NULL,
        delegation_type TEXT DEFAULT 'temporary',
        scope TEXT,
        modules TEXT,
        transaction_types TEXT,
        limit_amount DECIMAL(15,2) DEFAULT 0,
        currency TEXT DEFAULT 'USD',
        priority INTEGER DEFAULT 1,
        reason TEXT,
        is_active INTEGER DEFAULT 1,
        requires_approval INTEGER DEFAULT 0,
        approved_by INTEGER,
        start_date DATE DEFAULT (date('now')),
        end_date DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (delegator_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (delegate_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 9. Approval Matrix - Routing Rules
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_approval_matrix (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name_ar TEXT,
        name_fa TEXT,
        module TEXT NOT NULL,
        document_type TEXT NOT NULL,
        approval_type TEXT DEFAULT 'sequential',
        min_amount DECIMAL(15,2) DEFAULT 0,
        max_amount DECIMAL(15,2) DEFAULT 0,
        currency TEXT DEFAULT 'USD',
        conditions TEXT,
        is_active INTEGER DEFAULT 1,
        priority INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 10. Approval Matrix Steps
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_approval_matrix_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matrix_id INTEGER NOT NULL,
        step_order INTEGER NOT NULL,
        approver_type TEXT NOT NULL,
        approver_id INTEGER,
        approver_role TEXT,
        approval_level INTEGER DEFAULT 1,
        is_final INTEGER DEFAULT 0,
        skip_if_no_approver INTEGER DEFAULT 0,
        min_quorum INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (matrix_id) REFERENCES op_approval_matrix(id) ON DELETE CASCADE,
        FOREIGN KEY (approver_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 11. Workflow Definitions - BPM Process Definitions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_workflow_definitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name_ar TEXT,
        name_fa TEXT,
        code TEXT UNIQUE,
        description TEXT,
        category TEXT,
        module TEXT,
        entity_type TEXT,
        version INTEGER DEFAULT 1,
        status TEXT DEFAULT 'draft',
        owner_id INTEGER,
        estimated_duration_hours INTEGER,
        risk_level TEXT DEFAULT 'medium',
        is_published INTEGER DEFAULT 0,
        published_at DATETIME,
        published_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (published_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 12. Workflow Versions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_workflow_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workflow_definition_id INTEGER NOT NULL,
        version_number INTEGER NOT NULL,
        version_label TEXT,
        definition_json TEXT,
        change_summary TEXT,
        status TEXT DEFAULT 'draft',
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workflow_definition_id) REFERENCES op_workflow_definitions(id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 13. Workflow Steps
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_workflow_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workflow_definition_id INTEGER NOT NULL,
        step_key TEXT NOT NULL,
        name TEXT NOT NULL,
        name_ar TEXT,
        step_type TEXT NOT NULL,
        description TEXT,
        assignee_type TEXT,
        assignee_id INTEGER,
        assignee_role TEXT,
        form_schema TEXT,
        timeout_hours INTEGER,
        timeout_action TEXT,
        escalation_level INTEGER,
        is_optional INTEGER DEFAULT 0,
        is_enabled INTEGER DEFAULT 1,
        sort_order INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workflow_definition_id) REFERENCES op_workflow_definitions(id) ON DELETE CASCADE,
        FOREIGN KEY (assignee_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 14. Workflow Transitions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_workflow_transitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workflow_definition_id INTEGER NOT NULL,
        from_step_id INTEGER,
        to_step_id INTEGER NOT NULL,
        transition_type TEXT DEFAULT 'sequential',
        condition_json TEXT,
        action_name TEXT,
        is_default INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workflow_definition_id) REFERENCES op_workflow_definitions(id) ON DELETE CASCADE,
        FOREIGN KEY (from_step_id) REFERENCES op_workflow_steps(id) ON DELETE SET NULL,
        FOREIGN KEY (to_step_id) REFERENCES op_workflow_steps(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 15. Process Instances - Running Cases
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_process_instances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workflow_definition_id INTEGER NOT NULL,
        reference_id TEXT,
        reference_type TEXT,
        title TEXT NOT NULL,
        description TEXT,
        priority TEXT DEFAULT 'medium',
        status TEXT DEFAULT 'initiated',
        current_step_id INTEGER,
        requester_id INTEGER,
        requester_name TEXT,
        assigned_to_id INTEGER,
        company_id INTEGER,
        department_id INTEGER,
        due_date DATETIME,
        started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME,
        sla_status TEXT,
        sla_due_at DATETIME,
        sla_breached INTEGER DEFAULT 0,
        metadata_json TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workflow_definition_id) REFERENCES op_workflow_definitions(id) ON DELETE SET NULL,
        FOREIGN KEY (current_step_id) REFERENCES op_workflow_steps(id) ON DELETE SET NULL,
        FOREIGN KEY (requester_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (assigned_to_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 16. Instance Steps - Step Execution History
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_instance_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        instance_id INTEGER NOT NULL,
        step_id INTEGER NOT NULL,
        step_key TEXT,
        step_name TEXT,
        status TEXT DEFAULT 'pending',
        assigned_to_id INTEGER,
        started_at DATETIME,
        completed_at DATETIME,
        due_at DATETIME,
        sla_breached INTEGER DEFAULT 0,
        action_taken TEXT,
        comments TEXT,
        form_data TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (instance_id) REFERENCES op_process_instances(id) ON DELETE CASCADE,
        FOREIGN KEY (step_id) REFERENCES op_workflow_steps(id) ON DELETE SET NULL,
        FOREIGN KEY (assigned_to_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 17. Instance Actions - Actions Taken
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_instance_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        instance_id INTEGER NOT NULL,
        step_id INTEGER,
        action_type TEXT NOT NULL,
        performed_by_id INTEGER NOT NULL,
        performed_by_name TEXT,
        action_data TEXT,
        comments TEXT,
        previous_status TEXT,
        new_status TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (instance_id) REFERENCES op_process_instances(id) ON DELETE CASCADE,
        FOREIGN KEY (step_id) REFERENCES op_workflow_steps(id) ON DELETE SET NULL,
        FOREIGN KEY (performed_by_id) REFERENCES users(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 18. Instance Comments
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_instance_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        instance_id INTEGER NOT NULL,
        step_id INTEGER,
        user_id INTEGER NOT NULL,
        user_name TEXT,
        comment TEXT NOT NULL,
        is_internal INTEGER DEFAULT 1,
        mentioned_users TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (instance_id) REFERENCES op_process_instances(id) ON DELETE CASCADE,
        FOREIGN KEY (step_id) REFERENCES op_workflow_steps(id) ON DELETE SET NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 19. SLA Policies
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_sla_policies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name_ar TEXT,
        name_fa TEXT,
        module TEXT NOT NULL,
        document_type TEXT,
        priority TEXT DEFAULT 'medium',
        response_hours INTEGER DEFAULT 24,
        resolution_hours INTEGER DEFAULT 72,
        warning_threshold_pct INTEGER DEFAULT 75,
        pause_on_holidays INTEGER DEFAULT 1,
        auto_escalate INTEGER DEFAULT 1,
        business_hours_only INTEGER DEFAULT 0,
        working_days TEXT DEFAULT '1,2,3,4,5',
        working_start_time TEXT DEFAULT '09:00',
        working_end_time TEXT DEFAULT '18:00',
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 20. SLA Records - Tracking
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_sla_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        instance_id INTEGER NOT NULL,
        step_id INTEGER,
        policy_id INTEGER NOT NULL,
        status TEXT DEFAULT 'active',
        started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        first_response_at DATETIME,
        resolved_at DATETIME,
        due_at DATETIME,
        sla_breached INTEGER DEFAULT 0,
        pause_started_at DATETIME,
        total_paused_minutes INTEGER DEFAULT 0,
        metadata_json TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (instance_id) REFERENCES op_process_instances(id) ON DELETE CASCADE,
        FOREIGN KEY (step_id) REFERENCES op_workflow_steps(id) ON DELETE SET NULL,
        FOREIGN KEY (policy_id) REFERENCES op_sla_policies(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 21. Escalation Rules
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_escalation_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        module TEXT NOT NULL,
        trigger_type TEXT NOT NULL,
        trigger_condition TEXT,
        escalation_level INTEGER DEFAULT 1,
        escalate_to_user_id INTEGER,
        escalate_to_role TEXT,
        escalate_to_position_id INTEGER,
        delay_minutes INTEGER DEFAULT 0,
        action_type TEXT DEFAULT 'notify',
        action_config TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (escalate_to_user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (escalate_to_position_id) REFERENCES op_positions(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 22. Escalation Logs
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_escalation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        instance_id INTEGER NOT NULL,
        step_id INTEGER,
        rule_id INTEGER NOT NULL,
        escalation_level INTEGER,
        escalated_to_id INTEGER,
        escalated_to_name TEXT,
        reason TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (instance_id) REFERENCES op_process_instances(id) ON DELETE CASCADE,
        FOREIGN KEY (step_id) REFERENCES op_workflow_steps(id) ON DELETE SET NULL,
        FOREIGN KEY (rule_id) REFERENCES op_escalation_rules(id) ON DELETE SET NULL,
        FOREIGN KEY (escalated_to_id) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 23. Automation Rules
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_automation_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name_ar TEXT,
        name_fa TEXT,
        description TEXT,
        module TEXT NOT NULL,
        trigger_type TEXT NOT NULL,
        trigger_condition TEXT,
        schedule_cron TEXT,
        is_active INTEGER DEFAULT 1,
        priority INTEGER DEFAULT 1,
        created_by INTEGER,
        approved_by INTEGER,
        approved_at DATETIME,
        last_run_at DATETIME,
        run_count INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 24. Automation Rule Conditions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_automation_conditions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_id INTEGER NOT NULL,
        field_name TEXT,
        operator TEXT,
        field_value TEXT,
        condition_group TEXT DEFAULT 'all',
        sort_order INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (rule_id) REFERENCES op_automation_rules(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 25. Automation Rule Actions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_automation_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_id INTEGER NOT NULL,
        action_type TEXT NOT NULL,
        action_config TEXT,
        execution_order INTEGER DEFAULT 1,
        continue_on_failure INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (rule_id) REFERENCES op_automation_rules(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 26. Automation Execution Logs
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_automation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_id INTEGER NOT NULL,
        instance_id INTEGER,
        trigger_type TEXT,
        status TEXT DEFAULT 'success',
        action_executed TEXT,
        error_message TEXT,
        execution_time_ms INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (rule_id) REFERENCES op_automation_rules(id) ON DELETE SET NULL,
        FOREIGN KEY (instance_id) REFERENCES op_process_instances(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 27. Simulation Scenarios - Reorg Planning
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_simulation_scenarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        name_ar TEXT,
        description TEXT,
        scenario_type TEXT NOT NULL,
        status TEXT DEFAULT 'draft',
        planned_effective_date DATE,
        created_by INTEGER NOT NULL,
        approved_by INTEGER,
        approved_at DATETIME,
        published_at DATETIME,
        version INTEGER DEFAULT 1,
        metadata_json TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (approved_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 28. Simulation Changes
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_simulation_changes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        simulation_id INTEGER NOT NULL,
        change_type TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id INTEGER NOT NULL,
        field_name TEXT,
        old_value TEXT,
        new_value TEXT,
        impact_analysis TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (simulation_id) REFERENCES op_simulation_scenarios(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 29. Simulation Impacts
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_simulation_impacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        simulation_id INTEGER NOT NULL,
        impact_type TEXT NOT NULL,
        impacted_module TEXT,
        impact_description TEXT,
        severity TEXT DEFAULT 'medium',
        mitigation TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (simulation_id) REFERENCES op_simulation_scenarios(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 30. Organization History - Historical Snapshots
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_org_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        entity_id INTEGER NOT NULL,
        snapshot_date DATE NOT NULL,
        data_json TEXT NOT NULL,
        change_type TEXT,
        changed_by INTEGER,
        change_reason TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 31. Dashboard Widgets - Custom Dashboards
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_dashboard_widgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        widget_key TEXT NOT NULL,
        widget_type TEXT NOT NULL,
        title TEXT,
        title_ar TEXT,
        title_fa TEXT,
        config_json TEXT,
        position_x INTEGER DEFAULT 0,
        position_y INTEGER DEFAULT 0,
        width INTEGER DEFAULT 4,
        height INTEGER DEFAULT 3,
        is_default INTEGER DEFAULT 0,
        is_shared INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 32. Notifications
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        notification_type TEXT NOT NULL,
        title TEXT NOT NULL,
        title_ar TEXT,
        title_fa TEXT,
        message TEXT,
        message_ar TEXT,
        message_fa TEXT,
        link TEXT,
        reference_type TEXT,
        reference_id INTEGER,
        is_read INTEGER DEFAULT 0,
        priority TEXT DEFAULT 'medium',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (reference_id) REFERENCES op_process_instances(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 33. Module Settings
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT UNIQUE NOT NULL,
        setting_value TEXT,
        setting_type TEXT DEFAULT 'string',
        description TEXT,
        category TEXT,
        is_encrypted INTEGER DEFAULT 0,
        updated_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (updated_by) REFERENCES users(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 34. Org Unit Dependencies (cross-module links)
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_org_dependencies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        org_unit_id INTEGER NOT NULL,
        dependent_module TEXT NOT NULL,
        dependent_entity_type TEXT,
        dependent_entity_id INTEGER,
        dependency_type TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (org_unit_id) REFERENCES op_org_units(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 35. Process Metrics - Analytics
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS op_process_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workflow_definition_id INTEGER,
        snapshot_date DATE NOT NULL,
        total_instances INTEGER DEFAULT 0,
        completed_instances INTEGER DEFAULT 0,
        rejected_instances INTEGER DEFAULT 0,
        cancelled_instances INTEGER DEFAULT 0,
        avg_completion_hours DECIMAL(10,2) DEFAULT 0,
        avg_approval_hours DECIMAL(10,2) DEFAULT 0,
        sla_breach_count INTEGER DEFAULT 0,
        sla_compliance_pct DECIMAL(5,2) DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (workflow_definition_id) REFERENCES op_workflow_definitions(id) ON DELETE SET NULL
    )"""
]

# ============================================================================
# MIGRATION RUNNER
# ============================================================================

def run_org_planning_migrations():
    """Run all Organizational Planning table migrations."""
    from database import get_db
    db = get_db()
    cursor = db.cursor()
    
    for table_sql in ORG_PLANNING_TABLES:
        table_name_match = table_sql.split('CREATE TABLE IF NOT EXISTS ')[1]
        table_name = table_name_match.split(' ')[0]
        try:
            cursor.execute(table_sql)
            print(f"[OK] Created/verified table: {table_name}")
        except Exception as e:
            print(f"[ERROR] Error creating {table_name}: {e}")
    
    db.commit()
    db.close()
    print("\n[OK] Organizational Planning migrations completed successfully!")

# ============================================================================
# HELPER FUNCTIONS - COMPANIES
# ============================================================================

def create_company(name, code, **kwargs):
    """Create a new company in the org hierarchy."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_companies (name, code, name_ar, name_fa, registration_number,
                tax_id, address, city, country, phone, email, website, 
                parent_company_id, is_active, effective_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, code,
            kwargs.get('name_ar', name),
            kwargs.get('name_fa', name),
            kwargs.get('registration_number'),
            kwargs.get('tax_id'),
            kwargs.get('address'),
            kwargs.get('city'),
            kwargs.get('country'),
            kwargs.get('phone'),
            kwargs.get('email'),
            kwargs.get('website'),
            kwargs.get('parent_company_id'),
            kwargs.get('is_active', 1),
            kwargs.get('effective_date', date.today().isoformat())
        ))
        return cursor.lastrowid

def get_companies(active_only=True):
    """Get all companies."""
    if active_only:
        return get_all("SELECT * FROM op_companies WHERE is_active = 1 ORDER BY name")
    return get_all("SELECT * FROM op_companies ORDER BY name")

def get_company(company_id):
    """Get a single company by ID."""
    return get_one("SELECT * FROM op_companies WHERE id = ?", (company_id,))

# ============================================================================
# HELPER FUNCTIONS - ORG UNITS
# ============================================================================

def create_org_unit(company_id, unit_type, name, **kwargs):
    """Create a new organizational unit."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_org_units (company_id, parent_id, unit_type, name, name_ar, name_fa,
                code, description, cost_center, budget, head_position_id, head_employee_id,
                location, address, phone, email, sort_order, is_active, effective_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company_id, kwargs.get('parent_id'), unit_type, name,
            kwargs.get('name_ar', name), kwargs.get('name_fa', name),
            kwargs.get('code'), kwargs.get('description'),
            kwargs.get('cost_center'), kwargs.get('budget', 0),
            kwargs.get('head_position_id'), kwargs.get('head_employee_id'),
            kwargs.get('location'), kwargs.get('address'),
            kwargs.get('phone'), kwargs.get('email'),
            kwargs.get('sort_order', 0), kwargs.get('is_active', 1),
            kwargs.get('effective_date', date.today().isoformat())
        ))
        return cursor.lastrowid

def get_org_units(company_id=None, parent_id=None, unit_type=None, active_only=True):
    """Get organizational units with optional filters."""
    query = "SELECT * FROM op_org_units WHERE 1=1"
    params = []
    
    if company_id:
        query += " AND company_id = ?"
        params.append(company_id)
    if parent_id is not None:
        query += " AND parent_id = ?"
        params.append(parent_id)
    if unit_type:
        query += " AND unit_type = ?"
        params.append(unit_type)
    if active_only:
        query += " AND is_active = 1"
    
    query += " ORDER BY sort_order, name"
    return get_all(query, params)

def get_org_unit_tree(company_id=None, parent_id=None, level=0):
    """Get organizational units as a nested tree structure."""
    units = get_org_units(company_id=company_id, parent_id=parent_id)
    tree = []
    for unit in units:
        unit_dict = dict(unit)
        unit_dict['level'] = level
        unit_dict['children'] = get_org_unit_tree(company_id=unit['id'], parent_id=unit['id'], level=level+1)
        tree.append(unit_dict)
    return tree

def get_org_unit(org_unit_id):
    """Get a single org unit by ID."""
    return get_one("SELECT * FROM op_org_units WHERE id = ?", (org_unit_id,))

def update_org_unit(org_unit_id, **kwargs):
    """Update an organizational unit."""
    fields = []
    values = []
    for key, value in kwargs.items():
        if key in ['name', 'name_ar', 'name_fa', 'code', 'description', 'cost_center',
                   'budget', 'head_position_id', 'head_employee_id', 'location', 
                   'address', 'phone', 'email', 'sort_order', 'is_active', 'end_date']:
            fields.append(f"{key} = ?")
            values.append(value)
    
    if fields:
        values.append(org_unit_id)
        with get_db_context() as db:
            db.execute(f"UPDATE op_org_units SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", values)

# ============================================================================
# HELPER FUNCTIONS - POSITIONS
# ============================================================================

def create_position(org_unit_id, title, level, **kwargs):
    """Create a new position."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_positions (org_unit_id, position_code, title, title_ar, title_fa,
                level, grade, salary_band_min, salary_band_max, employment_type,
                headcount_approved, headcount_budgeted, is_critical, is_supervisor,
                requires_approval, parent_position_id, reports_to_position_id,
                responsibilities, requirements, skills_required, approval_authority_level,
                is_active, effective_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            org_unit_id, kwargs.get('position_code'), title,
            kwargs.get('title_ar', title), kwargs.get('title_fa', title),
            level, kwargs.get('grade'), kwargs.get('salary_band_min', 0),
            kwargs.get('salary_band_max', 0), kwargs.get('employment_type', 'full_time'),
            kwargs.get('headcount_approved', 1), kwargs.get('headcount_budgeted', 1),
            kwargs.get('is_critical', 0), kwargs.get('is_supervisor', 0),
            kwargs.get('requires_approval', 1), kwargs.get('parent_position_id'),
            kwargs.get('reports_to_position_id'), kwargs.get('responsibilities'),
            kwargs.get('requirements'), kwargs.get('skills_required'),
            kwargs.get('approval_authority_level', 1), kwargs.get('is_active', 1),
            kwargs.get('effective_date', date.today().isoformat())
        ))
        return cursor.lastrowid

def get_positions(org_unit_id=None, level=None, active_only=True):
    """Get positions with optional filters."""
    query = "SELECT * FROM op_positions WHERE 1=1"
    params = []
    
    if org_unit_id:
        query += " AND org_unit_id = ?"
        params.append(org_unit_id)
    if level:
        query += " AND level = ?"
        params.append(level)
    if active_only:
        query += " AND is_active = 1"
    
    query += " ORDER BY level, title"
    return get_all(query, params)

def get_position(position_id):
    """Get a single position by ID."""
    return get_one("SELECT * FROM op_positions WHERE id = ?", (position_id,))

def get_position_hierarchy(position_id, visited=None):
    """Get the reporting hierarchy above a position."""
    if visited is None:
        visited = []
    
    if position_id in visited:
        return visited
    visited.append(position_id)
    
    position = get_position(position_id)
    if position and position['reports_to_position_id']:
        visited = get_position_hierarchy(position['reports_to_position_id'], visited)
    
    return visited

def assign_incumbent(position_id, employee_id=None, user_id=None, **kwargs):
    """Assign an incumbent to a position."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_position_incumbents (position_id, employee_id, user_id,
                incumbent_type, start_date, end_date, is_active, is_acting, 
                is_interim, is_successor, status, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            position_id, employee_id, user_id,
            kwargs.get('incumbent_type', 'primary'),
            kwargs.get('start_date', date.today().isoformat()),
            kwargs.get('end_date'),
            kwargs.get('is_active', 1),
            kwargs.get('is_acting', 0),
            kwargs.get('is_interim', 0),
            kwargs.get('is_successor', 0),
            kwargs.get('status', 'Filled'),
            kwargs.get('notes')
        ))
        return cursor.lastrowid

# ============================================================================
# HELPER FUNCTIONS - REPORTING LINES
# ============================================================================

def create_reporting_line(position_id, reports_to_position_id, reporting_type='direct', **kwargs):
    """Create a reporting line."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_reporting_lines (position_id, reports_to_position_id, 
                reporting_type, is_primary, is_active, effective_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            position_id, reports_to_position_id, reporting_type,
            kwargs.get('is_primary', 1), kwargs.get('is_active', 1),
            kwargs.get('effective_date', date.today().isoformat())
        ))
        return cursor.lastrowid

def get_reporting_lines(position_id=None, reports_to_position_id=None):
    """Get reporting lines with optional filters."""
    query = "SELECT * FROM op_reporting_lines WHERE is_active = 1"
    params = []
    
    if position_id:
        query += " AND position_id = ?"
        params.append(position_id)
    if reports_to_position_id:
        query += " AND reports_to_position_id = ?"
        params.append(reports_to_position_id)
    
    return get_all(query, params)

def detect_circular_reporting(position_id, target_id, visited=None):
    """Detect circular reporting relationships."""
    if visited is None:
        visited = []
    
    if position_id == target_id:
        return True
    
    if position_id in visited:
        return False
    visited.append(position_id)
    
    lines = get_reporting_lines(position_id=position_id)
    for line in lines:
        if detect_circular_reporting(line['reports_to_position_id'], target_id, visited):
            return True
    
    return False

# ============================================================================
# HELPER FUNCTIONS - HEADCOUNT
# ============================================================================

def create_headcount_plan(org_unit_id, plan_year, **kwargs):
    """Create a headcount plan."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_headcount_plans (org_unit_id, position_id, plan_year,
                plan_period, headcount_approved, headcount_planned, headcount_current,
                headcount_vacant, headcount_requested, headcount_frozen,
                budget_allocated, budget_used, notes, status, created_by,
                approved_by, approved_at, effective_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            org_unit_id, kwargs.get('position_id'), plan_year,
            kwargs.get('plan_period', 'annual'),
            kwargs.get('headcount_approved', 0),
            kwargs.get('headcount_planned', 0),
            kwargs.get('headcount_current', 0),
            kwargs.get('headcount_vacant', 0),
            kwargs.get('headcount_requested', 0),
            kwargs.get('headcount_frozen', 0),
            kwargs.get('budget_allocated', 0),
            kwargs.get('budget_used', 0),
            kwargs.get('notes'),
            kwargs.get('status', 'Draft'),
            kwargs.get('created_by'),
            kwargs.get('approved_by'),
            kwargs.get('approved_at'),
            kwargs.get('effective_date', date.today().isoformat())
        ))
        return cursor.lastrowid

def get_headcount_plans(org_unit_id=None, plan_year=None):
    """Get headcount plans."""
    query = "SELECT * FROM op_headcount_plans WHERE 1=1"
    params = []
    
    if org_unit_id:
        query += " AND org_unit_id = ?"
        params.append(org_unit_id)
    if plan_year:
        query += " AND plan_year = ?"
        params.append(plan_year)
    
    return get_all(query + " ORDER BY plan_year DESC, org_unit_id", params)

def get_headcount_metrics(org_unit_id=None):
    """Get headcount metrics for dashboard."""
    query = """
        SELECT 
            o.name as org_unit_name,
            o.unit_type,
            COALESCE(SUM(hcp.headcount_approved), 0) as total_approved,
            COALESCE(SUM(hcp.headcount_current), 0) as total_current,
            COALESCE(SUM(hcp.headcount_vacant), 0) as total_vacant,
            COALESCE(SUM(hcp.headcount_planned), 0) as total_planned
        FROM op_org_units o
        LEFT JOIN op_headcount_plans hcp ON o.id = hcp.org_unit_id AND hcp.plan_year = ?
        WHERE o.is_active = 1
    """
    params = [date.today().year]
    
    if org_unit_id:
        query += " AND o.id = ?"
        params.append(org_unit_id)
    
    query += " GROUP BY o.id ORDER BY o.name"
    return get_all(query, params)

# ============================================================================
# HELPER FUNCTIONS - DELEGATIONS
# ============================================================================

def create_delegation(delegator_id, delegate_id, delegation_type, **kwargs):
    """Create a delegation."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_delegations (delegator_id, delegate_id, delegation_type,
                scope, modules, transaction_types, limit_amount, currency,
                priority, reason, is_active, requires_approval, approved_by,
                start_date, end_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            delegator_id, delegate_id, delegation_type,
            kwargs.get('scope', 'full'),
            json.dumps(kwargs.get('modules', [])),
            json.dumps(kwargs.get('transaction_types', [])),
            kwargs.get('limit_amount', 0),
            kwargs.get('currency', 'USD'),
            kwargs.get('priority', 1),
            kwargs.get('reason'),
            kwargs.get('is_active', 1),
            kwargs.get('requires_approval', 0),
            kwargs.get('approved_by'),
            kwargs.get('start_date', date.today().isoformat()),
            kwargs.get('end_date')
        ))
        return cursor.lastrowid

def get_delegations(delegator_id=None, delegate_id=None, active_only=True):
    """Get delegations with optional filters."""
    query = "SELECT * FROM op_delegations WHERE 1=1"
    params = []
    
    if delegator_id:
        query += " AND delegator_id = ?"
        params.append(delegator_id)
    if delegate_id:
        query += " AND delegate_id = ?"
        params.append(delegate_id)
    if active_only:
        query += " AND is_active = 1 AND (start_date IS NULL OR start_date <= date('now')) AND (end_date IS NULL OR end_date >= date('now'))"
    
    return get_all(query + " ORDER BY priority DESC, start_date DESC", params)

def check_delegation_conflict(delegator_id, delegate_id):
    """Check for overlapping delegations."""
    return get_one("""
        SELECT * FROM op_delegations 
        WHERE delegator_id = ? AND delegate_id = ? 
        AND is_active = 1 
        AND (start_date IS NULL OR start_date <= date('now')) 
        AND (end_date IS NULL OR end_date >= date('now'))
        LIMIT 1
    """, (delegator_id, delegate_id))

# ============================================================================
# HELPER FUNCTIONS - APPROVAL MATRIX
# ============================================================================

def create_approval_matrix(name, module, document_type, **kwargs):
    """Create an approval matrix."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_approval_matrix (name, name_ar, name_fa, module, document_type,
                approval_type, min_amount, max_amount, currency, conditions, is_active, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, kwargs.get('name_ar', name), kwargs.get('name_fa', name),
            module, document_type,
            kwargs.get('approval_type', 'sequential'),
            kwargs.get('min_amount', 0),
            kwargs.get('max_amount', 999999999),
            kwargs.get('currency', 'USD'),
            json.dumps(kwargs.get('conditions', {})),
            kwargs.get('is_active', 1),
            kwargs.get('priority', 1)
        ))
        return cursor.lastrowid

def add_approval_matrix_step(matrix_id, step_order, approver_type, **kwargs):
    """Add a step to an approval matrix."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_approval_matrix_steps (matrix_id, step_order, approver_type,
                approver_id, approver_role, approval_level, is_final, skip_if_no_approver, min_quorum)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            matrix_id, step_order, approver_type,
            kwargs.get('approver_id'),
            kwargs.get('approver_role'),
            kwargs.get('approval_level', 1),
            kwargs.get('is_final', 0),
            kwargs.get('skip_if_no_approver', 0),
            kwargs.get('min_quorum', 1)
        ))
        return cursor.lastrowid

def get_approval_matrices(module=None, document_type=None):
    """Get approval matrices."""
    query = "SELECT * FROM op_approval_matrix WHERE is_active = 1"
    params = []
    
    if module:
        query += " AND module = ?"
        params.append(module)
    if document_type:
        query += " AND document_type = ?"
        params.append(document_type)
    
    return get_all(query + " ORDER BY priority, name", params)

def get_approval_matrix_steps(matrix_id):
    """Get steps for an approval matrix."""
    return get_all(
        "SELECT * FROM op_approval_matrix_steps WHERE matrix_id = ? ORDER BY step_order",
        (matrix_id,)
    )

def find_approval_route(module, document_type, amount=0, currency='USD'):
    """Find the appropriate approval route for a transaction."""
    matrices = get_approval_matrices(module, document_type)
    
    for matrix in matrices:
        if matrix['min_amount'] <= amount <= matrix['max_amount'] and matrix['currency'] == currency:
            steps = get_approval_matrix_steps(matrix['id'])
            if steps:
                return {'matrix': dict(matrix), 'steps': [dict(s) for s in steps]}
    
    return None

# ============================================================================
# HELPER FUNCTIONS - WORKFLOW DEFINITIONS
# ============================================================================

def create_workflow_definition(name, code, category, module, **kwargs):
    """Create a workflow definition."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_workflow_definitions (name, name_ar, name_fa, code, description,
                category, module, entity_type, version, status, owner_id,
                estimated_duration_hours, risk_level, is_published)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, kwargs.get('name_ar', name), kwargs.get('name_fa', name),
            code, kwargs.get('description'),
            category, module, kwargs.get('entity_type'),
            kwargs.get('version', 1), kwargs.get('status', 'draft'),
            kwargs.get('owner_id'),
            kwargs.get('estimated_duration_hours'),
            kwargs.get('risk_level', 'medium'),
            kwargs.get('is_published', 0)
        ))
        return cursor.lastrowid

def add_workflow_step(workflow_definition_id, step_key, name, step_type, **kwargs):
    """Add a step to a workflow definition."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_workflow_steps (workflow_definition_id, step_key, name, name_ar,
                step_type, description, assignee_type, assignee_id, assignee_role,
                form_schema, timeout_hours, timeout_action, escalation_level,
                is_optional, is_enabled, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            workflow_definition_id, step_key, name,
            kwargs.get('name_ar', name), step_type,
            kwargs.get('description'),
            kwargs.get('assignee_type', 'role'),
            kwargs.get('assignee_id'),
            kwargs.get('assignee_role'),
            json.dumps(kwargs.get('form_schema', {})),
            kwargs.get('timeout_hours', 24),
            kwargs.get('timeout_action', 'escalate'),
            kwargs.get('escalation_level'),
            kwargs.get('is_optional', 0),
            kwargs.get('is_enabled', 1),
            kwargs.get('sort_order', 0)
        ))
        return cursor.lastrowid

def add_workflow_transition(workflow_definition_id, from_step_id, to_step_id, **kwargs):
    """Add a transition between workflow steps."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_workflow_transitions (workflow_definition_id, from_step_id,
                to_step_id, transition_type, condition_json, action_name, is_default)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            workflow_definition_id, from_step_id, to_step_id,
            kwargs.get('transition_type', 'sequential'),
            json.dumps(kwargs.get('condition_json', {})),
            kwargs.get('action_name'),
            kwargs.get('is_default', 0)
        ))
        return cursor.lastrowid

def get_workflow_definitions(category=None, module=None, status=None):
    """Get workflow definitions."""
    query = "SELECT * FROM op_workflow_definitions WHERE 1=1"
    params = []
    
    if category:
        query += " AND category = ?"
        params.append(category)
    if module:
        query += " AND module = ?"
        params.append(module)
    if status:
        query += " AND status = ?"
        params.append(status)
    
    return get_all(query + " ORDER BY category, name", params)

def get_workflow_definition(workflow_id):
    """Get a single workflow definition."""
    return get_one("SELECT * FROM op_workflow_definitions WHERE id = ?", (workflow_id,))

def get_workflow_steps(workflow_definition_id):
    """Get steps for a workflow definition."""
    return get_all(
        "SELECT * FROM op_workflow_steps WHERE workflow_definition_id = ? ORDER BY sort_order",
        (workflow_definition_id,)
    )

# ============================================================================
# HELPER FUNCTIONS - PROCESS INSTANCES
# ============================================================================

def create_process_instance(workflow_definition_id, title, requester_id, **kwargs):
    """Create a new process instance."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_process_instances (workflow_definition_id, reference_id,
                reference_type, title, description, priority, status, current_step_id,
                requester_id, requester_name, assigned_to_id, company_id, department_id,
                due_date, sla_status, sla_due_at, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            workflow_definition_id, kwargs.get('reference_id'),
            kwargs.get('reference_type'), title,
            kwargs.get('description'),
            kwargs.get('priority', 'medium'),
            kwargs.get('status', 'initiated'),
            kwargs.get('current_step_id'),
            requester_id, kwargs.get('requester_name'),
            kwargs.get('assigned_to_id'),
            kwargs.get('company_id'),
            kwargs.get('department_id'),
            kwargs.get('due_date'),
            kwargs.get('sla_status', 'active'),
            kwargs.get('sla_due_at'),
            json.dumps(kwargs.get('metadata_json', {}))
        ))
        return cursor.lastrowid

def get_process_instances(**filters):
    """Get process instances with filters."""
    query = """
        SELECT pi.*, wd.name as workflow_name, wd.category as workflow_category,
               u1.full_name as requester_name_full, u2.full_name as assigned_to_name
        FROM op_process_instances pi
        LEFT JOIN op_workflow_definitions wd ON pi.workflow_definition_id = wd.id
        LEFT JOIN users u1 ON pi.requester_id = u1.id
        LEFT JOIN users u2 ON pi.assigned_to_id = u2.id
        WHERE 1=1
    """
    params = []
    
    if filters.get('status'):
        query += " AND pi.status = ?"
        params.append(filters['status'])
    if filters.get('assigned_to_id'):
        query += " AND pi.assigned_to_id = ?"
        params.append(filters['assigned_to_id'])
    if filters.get('requester_id'):
        query += " AND pi.requester_id = ?"
        params.append(filters['requester_id'])
    if filters.get('workflow_definition_id'):
        query += " AND pi.workflow_definition_id = ?"
        params.append(filters['workflow_definition_id'])
    if filters.get('priority'):
        query += " AND pi.priority = ?"
        params.append(filters['priority'])
    if filters.get('sla_breached'):
        query += " AND pi.sla_breached = 1"
    
    query += " ORDER BY pi.priority DESC, pi.created_at DESC"
    return get_all(query, params)

def get_my_pending_approvals(user_id):
    """Get pending approvals for a specific user."""
    return get_all("""
        SELECT pi.*, wd.name as workflow_name, wd.category,
               ws.name as current_step_name, ws.step_type,
               TIMESTAMPDIFF_HOUR(pi.started_at, NOW()) as age_hours
        FROM op_process_instances pi
        JOIN op_workflow_definitions wd ON pi.workflow_definition_id = wd.id
        LEFT JOIN op_workflow_steps ws ON pi.current_step_id = ws.id
        WHERE pi.assigned_to_id = ?
        AND pi.status IN ('initiated', 'in_progress', 'pending')
        ORDER BY pi.priority DESC, pi.created_at ASC
    """, (user_id,))

def perform_instance_action(instance_id, action_type, performed_by, **kwargs):
    """Perform an action on a process instance."""
    with get_db_context() as db:
        instance = get_one("SELECT * FROM op_process_instances WHERE id = ?", (instance_id,))
        if not instance:
            return None
        
        cursor = db.cursor()
        
        if action_type == 'approve':
            new_status = 'approved'
        elif action_type == 'reject':
            new_status = 'rejected'
        elif action_type == 'return':
            new_status = 'returned'
        elif action_type == 'complete':
            new_status = 'completed'
        elif action_type == 'cancel':
            new_status = 'cancelled'
        else:
            new_status = instance['status']
        
        cursor.execute("""
            INSERT INTO op_instance_actions (instance_id, step_id, action_type,
                performed_by_id, performed_by_name, comments, previous_status, new_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            instance_id,
            kwargs.get('step_id'),
            action_type,
            performed_by,
            kwargs.get('performed_by_name'),
            kwargs.get('comments'),
            instance['status'],
            new_status
        ))
        
        cursor.execute("""
            UPDATE op_process_instances
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (new_status, instance_id))
        
        if new_status in ['completed', 'approved', 'cancelled', 'rejected']:
            cursor.execute("""
                UPDATE op_process_instances SET completed_at = CURRENT_TIMESTAMP WHERE id = ?
            """, (instance_id,))
        
        return new_status

# ============================================================================
# HELPER FUNCTIONS - SLA
# ============================================================================

def create_sla_policy(name, module, **kwargs):
    """Create an SLA policy."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_sla_policies (name, name_ar, name_fa, module, document_type,
                priority, response_hours, resolution_hours, warning_threshold_pct,
                pause_on_holidays, auto_escalate, business_hours_only, working_days,
                working_start_time, working_end_time, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, kwargs.get('name_ar', name), kwargs.get('name_fa', name),
            module, kwargs.get('document_type'),
            kwargs.get('priority', 'medium'),
            kwargs.get('response_hours', 24),
            kwargs.get('resolution_hours', 72),
            kwargs.get('warning_threshold_pct', 75),
            kwargs.get('pause_on_holidays', 1),
            kwargs.get('auto_escalate', 1),
            kwargs.get('business_hours_only', 0),
            kwargs.get('working_days', '1,2,3,4,5'),
            kwargs.get('working_start_time', '09:00'),
            kwargs.get('working_end_time', '18:00'),
            kwargs.get('is_active', 1)
        ))
        return cursor.lastrowid

def get_sla_policies(module=None, priority=None):
    """Get SLA policies."""
    query = "SELECT * FROM op_sla_policies WHERE is_active = 1"
    params = []
    
    if module:
        query += " AND module = ?"
        params.append(module)
    if priority:
        query += " AND priority = ?"
        params.append(priority)
    
    return get_all(query + " ORDER BY priority, name", params)

def calculate_sla_due_date(policy_id, start_time=None):
    """Calculate SLA due date based on policy."""
    policy = get_one("SELECT * FROM op_sla_policies WHERE id = ?", (policy_id,))
    if not policy:
        return None
    
    if start_time is None:
        start_time = datetime.now()
    
    resolution_hours = policy['resolution_hours']
    due_date = start_time + timedelta(hours=resolution_hours)
    
    if policy['business_hours_only']:
        due_date = calculate_business_hours_due_date(
            start_time, resolution_hours,
            policy['working_days'].split(','),
            policy['working_start_time'],
            policy['working_end_time']
        )
    
    return due_date

def calculate_business_hours_due_date(start_time, hours, working_days, start_time_str, end_time_str):
    """Calculate due date considering business hours only."""
    start_hour = int(start_time_str.split(':')[0])
    end_hour = int(end_time_str.split(':')[0])
    
    remaining_hours = hours
    current_time = start_time
    
    while remaining_hours > 0:
        current_day = current_time.strftime('%w')
        
        if current_day not in working_days:
            current_time += timedelta(days=1)
            current_time = current_time.replace(hour=start_hour, minute=0, second=0)
            continue
        
        day_end = current_time.replace(hour=end_hour, minute=0, second=0)
        day_start = current_time.replace(hour=start_hour, minute=0, second=0)
        
        if current_time < day_start:
            current_time = day_start
        
        if current_time >= day_end:
            current_time += timedelta(days=1)
            current_time = current_time.replace(hour=start_hour, minute=0, second=0)
            continue
        
        available_hours = (day_end - current_time).total_seconds() / 3600
        
        if available_hours >= remaining_hours:
            current_time += timedelta(hours=remaining_hours)
            remaining_hours = 0
        else:
            remaining_hours -= available_hours
            current_time += timedelta(days=1)
            current_time = current_time.replace(hour=start_hour, minute=0, second=0)
    
    return current_time

# ============================================================================
# HELPER FUNCTIONS - AUTOMATION
# ============================================================================

def create_automation_rule(name, module, trigger_type, **kwargs):
    """Create an automation rule."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_automation_rules (name, name_ar, name_fa, description,
                module, trigger_type, trigger_condition, schedule_cron,
                is_active, priority, created_by, approved_by, approved_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, kwargs.get('name_ar', name), kwargs.get('name_fa', name),
            kwargs.get('description'),
            module, trigger_type,
            json.dumps(kwargs.get('trigger_condition', {})),
            kwargs.get('schedule_cron'),
            kwargs.get('is_active', 1),
            kwargs.get('priority', 1),
            kwargs.get('created_by'),
            kwargs.get('approved_by'),
            kwargs.get('approved_at')
        ))
        return cursor.lastrowid

def add_automation_condition(rule_id, field_name, operator, field_value, **kwargs):
    """Add a condition to an automation rule."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_automation_conditions (rule_id, field_name, operator,
                field_value, condition_group, sort_order)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            rule_id, field_name, operator, field_value,
            kwargs.get('condition_group', 'all'),
            kwargs.get('sort_order', 0)
        ))
        return cursor.lastrowid

def add_automation_action(rule_id, action_type, **kwargs):
    """Add an action to an automation rule."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_automation_actions (rule_id, action_type, action_config,
                execution_order, continue_on_failure)
            VALUES (?, ?, ?, ?, ?)
        """, (
            rule_id, action_type,
            json.dumps(kwargs.get('action_config', {})),
            kwargs.get('execution_order', 1),
            kwargs.get('continue_on_failure', 0)
        ))
        return cursor.lastrowid

def get_automation_rules(module=None, trigger_type=None, active_only=True):
    """Get automation rules."""
    query = "SELECT * FROM op_automation_rules WHERE 1=1"
    params = []
    
    if module:
        query += " AND module = ?"
        params.append(module)
    if trigger_type:
        query += " AND trigger_type = ?"
        params.append(trigger_type)
    if active_only:
        query += " AND is_active = 1"
    
    return get_all(query + " ORDER BY priority DESC, name", params)

# ============================================================================
# HELPER FUNCTIONS - SIMULATION
# ============================================================================

def create_simulation_scenario(name, scenario_type, created_by, **kwargs):
    """Create a simulation scenario."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_simulation_scenarios (name, name_ar, description,
                scenario_type, status, planned_effective_date, created_by,
                approved_by, approved_at, version, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, kwargs.get('name_ar', name), kwargs.get('description'),
            scenario_type, kwargs.get('status', 'draft'),
            kwargs.get('planned_effective_date'),
            created_by, kwargs.get('approved_by'),
            kwargs.get('approved_at'),
            kwargs.get('version', 1),
            json.dumps(kwargs.get('metadata_json', {}))
        ))
        return cursor.lastrowid

def add_simulation_change(simulation_id, change_type, entity_type, entity_id, **kwargs):
    """Add a change to a simulation."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_simulation_changes (simulation_id, change_type,
                entity_type, entity_id, field_name, old_value, new_value, impact_analysis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            simulation_id, change_type, entity_type, entity_id,
            kwargs.get('field_name'),
            kwargs.get('old_value'),
            kwargs.get('new_value'),
            kwargs.get('impact_analysis')
        ))
        return cursor.lastrowid

def get_simulation_scenarios(status=None, created_by=None):
    """Get simulation scenarios."""
    query = "SELECT * FROM op_simulation_scenarios WHERE 1=1"
    params = []
    
    if status:
        query += " AND status = ?"
        params.append(status)
    if created_by:
        query += " AND created_by = ?"
        params.append(created_by)
    
    return get_all(query + " ORDER BY created_at DESC", params)

def analyze_simulation_impacts(simulation_id):
    """Analyze impacts of a simulation scenario."""
    changes = get_all("""
        SELECT * FROM op_simulation_changes WHERE simulation_id = ?
    """, (simulation_id,))
    
    impacts = []
    
    for change in changes:
        impact = {
            'change': dict(change),
            'impact_type': 'unknown',
            'impacted_modules': [],
            'description': '',
            'severity': 'low'
        }
        
        if change['entity_type'] == 'org_unit':
            impact['impact_type'] = 'org_structure'
            impact['impacted_modules'] = ['workflow', 'hr', 'permissions', 'reports']
            impact['description'] = f"Organization unit change may affect approval routing and access control"
            impact['severity'] = 'high'
        
        elif change['entity_type'] == 'position':
            impact['impact_type'] = 'reporting_line'
            impact['impacted_modules'] = ['workflow', 'hr', 'delegation', 'notifications']
            impact['description'] = f"Position change may affect reporting lines and delegation rules"
            impact['severity'] = 'high'
        
        elif change['entity_type'] == 'headcount':
            impact['impact_type'] = 'headcount'
            impact['impacted_modules'] = ['hr', 'budget', 'reports']
            impact['description'] = f"Headcount change affects staffing and budget planning"
            impact['severity'] = 'medium'
        
        with get_db_context() as db:
            cursor = db.cursor()
            cursor.execute("""
                INSERT INTO op_simulation_impacts (simulation_id, impact_type,
                    impacted_module, impact_description, severity)
                VALUES (?, ?, ?, ?, ?)
            """, (
                simulation_id, impact['impact_type'],
                ','.join(impact['impacted_modules']),
                impact['description'], impact['severity']
            ))
        
        impacts.append(impact)
    
    return impacts

# ============================================================================
# HELPER FUNCTIONS - METRICS & ANALYTICS
# ============================================================================

def get_process_metrics(workflow_definition_id=None, days=30):
    """Get process performance metrics."""
    query = """
        SELECT 
            wd.name as workflow_name,
            wd.category,
            COUNT(pi.id) as total_instances,
            SUM(CASE WHEN pi.status = 'completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN pi.status = 'rejected' THEN 1 ELSE 0 END) as rejected,
            SUM(CASE WHEN pi.status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
            AVG(CASE WHEN pi.completed_at IS NOT NULL 
                THEN (julianday(pi.completed_at) - julianday(pi.started_at)) * 24 
                ELSE NULL END) as avg_hours,
            SUM(pi.sla_breached) as sla_breaches
        FROM op_workflow_definitions wd
        LEFT JOIN op_process_instances pi ON wd.id = pi.workflow_definition_id
            AND pi.created_at >= datetime('now', '-' || ? || ' days')
        WHERE wd.is_published = 1
    """
    params = [days]
    
    if workflow_definition_id:
        query += " AND wd.id = ?"
        params.append(workflow_definition_id)
    
    query += " GROUP BY wd.id ORDER BY total_instances DESC"
    
    return get_all(query, params)

def get_sla_compliance_stats(days=30):
    """Get SLA compliance statistics."""
    return get_all("""
        SELECT 
            sla.name as policy_name,
            sla.priority,
            COUNT(sr.id) as total_records,
            SUM(CASE WHEN sr.sla_breached = 1 THEN 1 ELSE 0 END) as breaches,
            AVG(CASE WHEN sr.sla_breached = 0 AND sr.resolved_at IS NOT NULL
                THEN (julianday(sr.resolved_at) - julianday(sr.started_at)) * 24
                ELSE NULL END) as avg_resolution_hours,
            MIN(sr.due_at) as next_due
        FROM op_sla_policies sla
        LEFT JOIN op_sla_records sr ON sla.id = sr.policy_id
            AND sr.created_at >= datetime('now', '-' || ? || ' days')
        WHERE sla.is_active = 1
        GROUP BY sla.id
        ORDER BY sla.priority, breaches DESC
    """, (days,))

def get_bottleneck_steps(days=30):
    """Identify bottleneck steps in workflows."""
    return get_all("""
        SELECT 
            wd.name as workflow_name,
            ws.name as step_name,
            ws.step_type,
            COUNT(is2.id) as executions,
            AVG(CASE WHEN is2.completed_at IS NOT NULL 
                THEN (julianday(is2.completed_at) - julianday(is2.started_at)) * 24
                ELSE NULL END) as avg_hours,
            SUM(CASE WHEN is2.status = 'pending' THEN 1 ELSE 0 END) as pending_count,
            MAX(CASE WHEN is2.due_at IS NOT NULL AND is2.completed_at IS NULL
                THEN (julianday(is2.due_at) - julianday('now')) * 24
                ELSE NULL END) as hours_overdue
        FROM op_workflow_steps ws
        JOIN op_workflow_definitions wd ON ws.workflow_definition_id = wd.id
        LEFT JOIN op_instance_steps is2 ON ws.id = is2.step_id
            AND is2.created_at >= datetime('now', '-' || ? || ' days')
        WHERE wd.is_published = 1 AND ws.is_enabled = 1
        GROUP BY ws.id
        ORDER BY avg_hours DESC, pending_count DESC
        LIMIT 20
    """, (days,))

# ============================================================================
# HELPER FUNCTIONS - NOTIFICATIONS
# ============================================================================

def create_notification(user_id, notification_type, title, message, **kwargs):
    """Create a notification."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_notifications (user_id, notification_type, title, title_ar,
                title_fa, message, message_ar, message_fa, link, reference_type,
                reference_id, priority)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, notification_type, title,
            kwargs.get('title_ar', title),
            kwargs.get('title_fa', title),
            message, kwargs.get('message_ar', message),
            kwargs.get('message_fa', message),
            kwargs.get('link'),
            kwargs.get('reference_type'),
            kwargs.get('reference_id'),
            kwargs.get('priority', 'medium')
        ))
        return cursor.lastrowid

def get_user_notifications(user_id, unread_only=False, limit=50):
    """Get notifications for a user."""
    query = "SELECT * FROM op_notifications WHERE user_id = ?"
    params = [user_id]
    
    if unread_only:
        query += " AND is_read = 0"
    
    return get_all(query + " ORDER BY created_at DESC LIMIT ?", params + [limit])

def mark_notification_read(notification_id, user_id):
    """Mark a notification as read."""
    with get_db_context() as db:
        db.execute(
            "UPDATE op_notifications SET is_read = 1 WHERE id = ? AND user_id = ?",
            (notification_id, user_id)
        )

# ============================================================================
# HELPER FUNCTIONS - AUDIT LOG
# ============================================================================

def log_org_change(entity_type, entity_id, change_type, changed_by, change_reason=None, data_json=None):
    """Log an organizational change to audit trail."""
    with get_db_context() as db:
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO op_org_history (entity_type, entity_id, snapshot_date,
                change_type, changed_by, change_reason, data_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entity_type, entity_id, date.today().isoformat(),
            change_type, changed_by, change_reason, json.dumps(data_json) if data_json else None
        ))
        
        cursor.execute("""
            INSERT INTO op_audit_logs (entity_type, entity_id, action_type,
                user_id, change_reason, old_value, new_value)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entity_type, entity_id, change_type,
            changed_by, change_reason,
            data_json.get('old_value') if data_json else None,
            data_json.get('new_value') if data_json else None
        ))
        return cursor.lastrowid

# ============================================================================
# SEED DATA
# ============================================================================

def seed_org_planning_demo_data():
    """Seed demo data for the Organizational Planning module."""
    
    # Create demo companies
    company1_id = create_company(
        name="MMDx Global Corporation",
        code="MMDX-GLOBAL",
        registration_number="REG-2024-001",
        tax_id="TAX-12345678",
        address="123 Business Tower, Downtown",
        city="Dubai",
        country="UAE",
        phone="+971-4-123-4567",
        email="info@mmdx.com",
        website="https://mmdx.com"
    )
    
    company2_id = create_company(
        name="MMDx MENA Operations",
        code="MMDX-MENA",
        registration_number="REG-2024-002",
        tax_id="TAX-87654321",
        address="456 Commerce Ave, Business Bay",
        city="Dubai",
        country="UAE",
        phone="+971-4-765-4321",
        email="mena@mmdx.com",
        parent_company_id=company1_id
    )
    
    # Create org units
    divisions = [
        {'name': 'Corporate Operations', 'type': 'division', 'code': 'CORP-OPS'},
        {'name': 'Finance & Accounting', 'type': 'division', 'code': 'FIN'},
        {'name': 'Human Resources', 'type': 'division', 'code': 'HR'},
        {'name': 'Information Technology', 'type': 'division', 'code': 'IT'},
        {'name': 'Sales & Marketing', 'type': 'division', 'code': 'SALES'},
        {'name': 'Operations & Logistics', 'type': 'division', 'code': 'OPS'},
        {'name': 'Procurement & Supply Chain', 'type': 'division', 'code': 'PROC'},
        {'name': 'Quality & Compliance', 'type': 'division', 'code': 'QUAL'},
    ]
    
    div_ids = {}
    for div in divisions:
        div_id = create_org_unit(
            company_id=company1_id,
            unit_type=div['type'],
            name=div['name'],
            code=div['code'],
            description=f"{div['name']} Division"
        )
        div_ids[div['name']] = div_id
    
    # Create departments under each division
    departments_data = {
        'Corporate Operations': [
            {'name': 'Executive Management', 'code': 'EXEC', 'type': 'department'},
            {'name': 'Legal & Compliance', 'code': 'LEGAL', 'type': 'department'},
            {'name': 'Strategy & Planning', 'code': 'STRAT', 'type': 'department'},
        ],
        'Finance & Accounting': [
            {'name': 'Financial Planning & Analysis', 'code': 'FP&A', 'type': 'department'},
            {'name': 'Treasury', 'code': 'TREAS', 'type': 'department'},
            {'name': 'Accounts Payable', 'code': 'AP', 'type': 'department'},
            {'name': 'Accounts Receivable', 'code': 'AR', 'type': 'department'},
            {'name': 'Tax & Regulatory', 'code': 'TAX', 'type': 'department'},
        ],
        'Human Resources': [
            {'name': 'Talent Acquisition', 'code': 'TA', 'type': 'department'},
            {'name': 'Learning & Development', 'code': 'L&D', 'type': 'department'},
            {'name': 'Compensation & Benefits', 'code': 'C&B', 'type': 'department'},
            {'name': 'Employee Relations', 'code': 'ER', 'type': 'department'},
            {'name': 'HR Operations', 'code': 'HR-OPS', 'type': 'department'},
        ],
        'Information Technology': [
            {'name': 'Software Development', 'code': 'DEV', 'type': 'department'},
            {'name': 'Infrastructure & Security', 'code': 'INFRA', 'type': 'department'},
            {'name': 'Business Analysis', 'code': 'BA', 'type': 'department'},
            {'name': 'IT Support', 'code': 'IT-SUPP', 'type': 'department'},
        ],
        'Sales & Marketing': [
            {'name': 'Enterprise Sales', 'code': 'ENT-SALES', 'type': 'department'},
            {'name': 'SMB Sales', 'code': 'SMB-SALES', 'type': 'department'},
            {'name': 'Digital Marketing', 'code': 'DIG-MKT', 'type': 'department'},
            {'name': 'Brand & Communications', 'code': 'BRAND', 'type': 'department'},
            {'name': 'Customer Success', 'code': 'CS', 'type': 'department'},
        ],
        'Operations & Logistics': [
            {'name': 'Warehouse Management', 'code': 'WMS', 'type': 'department'},
            {'name': 'Transportation', 'code': 'TRANS', 'type': 'department'},
            {'name': 'Fleet Management', 'code': 'FLEET', 'type': 'department'},
            {'name': 'Inventory Control', 'code': 'INV', 'type': 'department'},
        ],
        'Procurement & Supply Chain': [
            {'name': 'Strategic Sourcing', 'code': 'SOURCING', 'type': 'department'},
            {'name': 'Supplier Management', 'code': 'SUP-MGR', 'type': 'department'},
            {'name': 'Contract Management', 'code': 'CONTRACTS', 'type': 'department'},
            {'name': 'Procurement Operations', 'code': 'PROC-OPS', 'type': 'department'},
        ],
        'Quality & Compliance': [
            {'name': 'Quality Assurance', 'code': 'QA', 'type': 'department'},
            {'name': 'Food Safety', 'code': 'FS', 'type': 'department'},
            {'name': 'Health & Safety', 'code': 'H&S', 'type': 'department'},
            {'name': 'Environmental Compliance', 'code': 'ENV', 'type': 'department'},
        ],
    }
    
    dept_ids = {}
    for div_name, depts in departments_data.items():
        for dept in depts:
            dept_id = create_org_unit(
                company_id=company1_id,
                parent_id=div_ids.get(div_name),
                unit_type=dept['type'],
                name=dept['name'],
                code=dept['code'],
                description=f"{dept['name']} Department"
            )
            dept_ids[dept['code']] = dept_id
    
    # Create positions
    positions_data = [
        {'title': 'Chief Executive Officer', 'level': 'executive', 'code': 'CEO'},
        {'title': 'Chief Financial Officer', 'level': 'executive', 'code': 'CFO'},
        {'title': 'Chief Human Resources Officer', 'level': 'executive', 'code': 'CHRO'},
        {'title': 'Chief Technology Officer', 'level': 'executive', 'code': 'CTO'},
        {'title': 'Chief Sales Officer', 'level': 'executive', 'code': 'CSO'},
        {'title': 'Chief Operating Officer', 'level': 'executive', 'code': 'COO'},
        {'title': 'Vice President - Finance', 'level': 'vp', 'code': 'VP-FIN'},
        {'title': 'Vice President - HR', 'level': 'vp', 'code': 'VP-HR'},
        {'title': 'Vice President - IT', 'level': 'vp', 'code': 'VP-IT'},
        {'title': 'Vice President - Sales', 'level': 'vp', 'code': 'VP-SALES'},
        {'title': 'Vice President - Operations', 'level': 'vp', 'code': 'VP-OPS'},
        {'title': 'Director - Financial Planning', 'level': 'director', 'code': 'DIR-FP'},
        {'title': 'Director - Talent Acquisition', 'level': 'director', 'code': 'DIR-TA'},
        {'title': 'Director - Software Development', 'level': 'director', 'code': 'DIR-DEV'},
        {'title': 'Director - Enterprise Sales', 'level': 'director', 'code': 'DIR-ENT'},
        {'title': 'Director - Warehouse Operations', 'level': 'director', 'code': 'DIR-WMS'},
        {'title': 'Senior Manager - FP&A', 'level': 'senior_manager', 'code': 'SM-FPA'},
        {'title': 'Senior Manager - Compensation', 'level': 'senior_manager', 'code': 'SM-CB'},
        {'title': 'Senior Manager - Infrastructure', 'level': 'senior_manager', 'code': 'SM-INF'},
        {'title': 'Senior Manager - Digital Marketing', 'level': 'senior_manager', 'code': 'SM-DM'},
        {'title': 'Manager - Accounts Payable', 'level': 'manager', 'code': 'MGR-AP'},
        {'title': 'Manager - Employee Relations', 'level': 'manager', 'code': 'MGR-ER'},
        {'title': 'Manager - Business Analysis', 'level': 'manager', 'code': 'MGR-BA'},
        {'title': 'Manager - Enterprise Sales', 'level': 'manager', 'code': 'MGR-ENT'},
        {'title': 'Manager - Transportation', 'level': 'manager', 'code': 'MGR-TRANS'},
        {'title': 'Supervisor - Software Development', 'level': 'supervisor', 'code': 'SPV-DEV'},
        {'title': 'Supervisor - IT Support', 'level': 'supervisor', 'code': 'SPV-ITS'},
        {'title': 'Senior Developer', 'level': 'senior', 'code': 'DEV-SR'},
        {'title': 'Developer', 'level': 'junior', 'code': 'DEV-JR'},
        {'title': 'Junior Developer', 'level': 'entry', 'code': 'DEV-ENTRY'},
    ]
    
    pos_ids = {}
    for pos in positions_data:
        pos_id = create_position(
            org_unit_id=None,
            title=pos['title'],
            level=pos['level'],
            position_code=pos['code'],
            is_critical=1 if pos['level'] in ['executive', 'vp', 'director'] else 0,
            is_supervisor=1 if pos['level'] in ['supervisor', 'manager', 'senior_manager'] else 0
        )
        pos_ids[pos['code']] = pos_id
    
    # Create headcount plans
    for dept_code, dept_id in dept_ids.items():
        create_headcount_plan(
            org_unit_id=dept_id,
            plan_year=date.today().year,
            headcount_approved=10 + (hash(dept_code) % 20),
            headcount_current=8 + (hash(dept_code) % 15),
            headcount_vacant=2 + (hash(dept_code) % 5),
            headcount_planned=12 + (hash(dept_code) % 20),
            budget_allocated=500000 + (hash(dept_code) % 500000),
            status='Approved'
        )
    
    # Create workflow definitions
    workflows = [
        {
            'name': 'Purchase Request Approval',
            'code': 'WF-PURCHASE',
            'category': 'Finance',
            'module': 'finance',
            'description': 'Standard purchase request workflow for procurement approvals',
            'estimated_hours': 48
        },
        {
            'name': 'Leave Request Workflow',
            'code': 'WF-LEAVE',
            'category': 'HR',
            'module': 'hr',
            'description': 'Employee leave request approval workflow',
            'estimated_hours': 24
        },
        {
            'name': 'New Hire Onboarding',
            'code': 'WF-ONBOARD',
            'category': 'HR',
            'module': 'hr',
            'description': 'Standard onboarding process for new employees',
            'estimated_hours': 120
        },
        {
            'name': 'Invoice Approval',
            'code': 'WF-INVOICE',
            'category': 'Finance',
            'module': 'finance',
            'description': 'Invoice matching and approval workflow',
            'estimated_hours': 72
        },
        {
            'name': 'Access Request',
            'code': 'WF-ACCESS',
            'category': 'IT',
            'module': 'it',
            'description': 'IT system access request workflow',
            'estimated_hours': 24
        },
        {
            'name': 'Document Approval',
            'code': 'WF-DOC',
            'category': 'Quality',
            'module': 'quality',
            'description': 'Standard operating procedure document approval',
            'estimated_hours': 48
        },
        {
            'name': 'Capital Expenditure Request',
            'code': 'WF-CAPEX',
            'category': 'Finance',
            'module': 'finance',
            'description': 'CapEx approval workflow for major investments',
            'estimated_hours': 168
        },
        {
            'name': 'Customer Complaint Resolution',
            'code': 'WF-COMPLAINT',
            'category': 'Operations',
            'module': 'operations',
            'description': 'Customer complaint handling and resolution workflow',
            'estimated_hours': 72
        },
    ]
    
    wf_ids = {}
    for wf in workflows:
        wf_id = create_workflow_definition(
            name=wf['name'],
            code=wf['code'],
            category=wf['category'],
            module=wf['module'],
            description=wf['description'],
            estimated_duration_hours=wf['estimated_hours'],
            status='published',
            is_published=1
        )
        wf_ids[wf['code']] = wf_id
        
        # Add workflow steps
        steps = [
            {'key': 'start', 'name': 'Start', 'type': 'start'},
            {'key': 'submit', 'name': 'Submit Request', 'type': 'manual'},
            {'key': 'review', 'name': 'Manager Review', 'type': 'approval'},
            {'key': 'approve', 'name': 'Final Approval', 'type': 'approval'},
            {'key': 'complete', 'name': 'Complete', 'type': 'end'},
        ]
        
        prev_step_id = None
        for i, step in enumerate(steps):
            step_id = add_workflow_step(
                workflow_definition_id=wf_id,
                step_key=step['key'],
                name=step['name'],
                step_type=step['type'],
                assignee_type='role',
                assignee_role='manager' if 'approval' in step['type'] else None,
                timeout_hours=24,
                sort_order=i
            )
            
            if prev_step_id:
                add_workflow_transition(
                    workflow_definition_id=wf_id,
                    from_step_id=prev_step_id,
                    to_step_id=step_id,
                    transition_type='sequential'
                )
            
            prev_step_id = step_id
    
    # Create SLA policies
    sla_policies = [
        {'name': 'Critical Issue SLA', 'module': 'operations', 'priority': 'critical', 'response_hours': 2, 'resolution_hours': 8},
        {'name': 'High Priority SLA', 'module': 'operations', 'priority': 'high', 'response_hours': 4, 'resolution_hours': 24},
        {'name': 'Medium Priority SLA', 'module': 'operations', 'priority': 'medium', 'response_hours': 8, 'resolution_hours': 48},
        {'name': 'Low Priority SLA', 'module': 'operations', 'priority': 'low', 'response_hours': 24, 'resolution_hours': 120},
        {'name': 'Purchase Approval SLA', 'module': 'finance', 'priority': 'medium', 'response_hours': 8, 'resolution_hours': 24},
        {'name': 'Leave Request SLA', 'module': 'hr', 'priority': 'low', 'response_hours': 24, 'resolution_hours': 48},
        {'name': 'Access Request SLA', 'module': 'it', 'priority': 'medium', 'response_hours': 4, 'resolution_hours': 24},
        {'name': 'Invoice Processing SLA', 'module': 'finance', 'priority': 'high', 'response_hours': 12, 'resolution_hours': 48},
    ]
    
    for sla in sla_policies:
        create_sla_policy(
            name=sla['name'],
            module=sla['module'],
            priority=sla['priority'],
            response_hours=sla['response_hours'],
            resolution_hours=sla['resolution_hours']
        )
    
    # Create approval matrices
    matrices = [
        {'name': 'Purchase Request < 10K', 'module': 'finance', 'doc_type': 'purchase', 'min': 0, 'max': 10000},
        {'name': 'Purchase Request 10K-50K', 'module': 'finance', 'doc_type': 'purchase', 'min': 10000, 'max': 50000},
        {'name': 'Purchase Request > 50K', 'module': 'finance', 'doc_type': 'purchase', 'min': 50000, 'max': 999999999},
        {'name': 'Leave Approval - Annual', 'module': 'hr', 'doc_type': 'leave', 'min': 0, 'max': 999999},
        {'name': 'Overtime Approval', 'module': 'hr', 'doc_type': 'overtime', 'min': 0, 'max': 999999},
        {'name': 'Invoice Approval', 'module': 'finance', 'doc_type': 'invoice', 'min': 0, 'max': 999999999},
        {'name': 'CapEx Approval', 'module': 'finance', 'doc_type': 'capex', 'min': 50000, 'max': 999999999},
    ]
    
    for mat in matrices:
        matrix_id = create_approval_matrix(
            name=mat['name'],
            module=mat['module'],
            document_type=mat['doc_type'],
            min_amount=mat['min'],
            max_amount=mat['max'],
            approval_type='sequential'
        )
        
        # Add approval steps
        add_approval_matrix_step(matrix_id, 1, 'role', approver_role='manager', is_final=False)
        if mat['max'] > 10000:
            add_approval_matrix_step(matrix_id, 2, 'role', approver_role='director', is_final=False)
        if mat['max'] > 50000:
            add_approval_matrix_step(matrix_id, 3, 'role', approver_role='vp', is_final=True)
        elif mat['min'] == 0:
            add_approval_matrix_step(matrix_id, 2, 'role', approver_role='hr_manager', is_final=True)
    
    # Create automation rules
    automations = [
        {'name': 'Auto-assign purchase requests', 'module': 'finance', 'trigger': 'on_create', 'action': 'assign_task'},
        {'name': 'Escalate overdue approvals', 'module': 'workflow', 'trigger': 'on_sla_breach', 'action': 'escalate'},
        {'name': 'Send approval reminders', 'module': 'workflow', 'trigger': 'on_schedule', 'action': 'send_notification'},
        {'name': 'Close completed instances', 'module': 'workflow', 'trigger': 'on_status_change', 'action': 'update_field'},
    ]
    
    for auto in automations:
        rule_id = create_automation_rule(
            name=auto['name'],
            module=auto['module'],
            trigger_type=auto['trigger']
        )
        add_automation_action(rule_id, auto['action'])
    
    print("✓ Demo data seeded successfully!")
    print(f"  - Companies: {2}")
    print(f"  - Divisions: {len(div_ids)}")
    print(f"  - Departments: {len(dept_ids)}")
    print(f"  - Positions: {len(pos_ids)}")
    print(f"  - Headcount Plans: {len(dept_ids)}")
    print(f"  - Workflows: {len(wf_ids)}")
    print(f"  - SLA Policies: {len(sla_policies)}")
    print(f"  - Approval Matrices: {len(matrices)}")
    print(f"  - Automation Rules: {len(automations)}")

if __name__ == '__main__':
    print("Running Organizational Planning migrations...")
    run_org_planning_migrations()
