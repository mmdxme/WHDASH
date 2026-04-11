"""
Maintenance Management Module - Data Models
===========================================
Enterprise-grade Maintenance Management for the MMDx platform.

This module extends the existing asset maintenance infrastructure with:
- Facility Management (buildings, sites, rooms, areas)
- Maintenance Teams and Team Members
- Technician Skills and Certifications
- Maintenance Checklists and Templates
- Work Order Tasks and Sub-tasks
- Downtime Tracking and Logging
- Spare Parts/Material Usage from Inventory
- Labor/Time Logging
- Maintenance Notifications and Alerts
- SLA/Response Tracking
- Escalation Rules
- Approval Workflows
- Audit Trail

Tables:
- maintenance_facilities: Facility/Building/Site master records
- maintenance_facility_requests: Facility maintenance requests
- maintenance_teams: Maintenance team definitions
- maintenance_team_members: Team member assignments
- maintenance_technician_skills: Technician skill/certification tracking
- maintenance_checklist_templates: Reusable inspection checklists
- maintenance_checklist_items: Items within checklists
- maintenance_work_order_tasks: Work order task lines
- maintenance_downtime_logs: Equipment/facility downtime records
- maintenance_parts_usage: Spare parts/material consumption
- maintenance_labor_logs: Labor/time tracking entries
- maintenance_sla_rules: SLA configuration rules
- maintenance_escalation_rules: Escalation definitions
- maintenance_notifications: Maintenance-specific notifications
- maintenance_approvals: Approval workflow records

Usage:
    from maintenance_models import (
        init_maintenance_tables,
        get_facility_stats,
        get_technician_workload,
        generate_pm_work_orders
    )
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'warehouse.db'))


def get_db():
    """Get database connection with Row factory for dict-like access."""
    conn = sqlite3.connect(DATABASE, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


# =============================================================================
# MAINTENANCE MANAGEMENT TABLE DEFINITIONS
# =============================================================================

MAINTENANCE_TABLES = [
    # -------------------------------------------------------------------------
    # 1. Maintenance Facilities - Facility/Building/Site Master Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_facilities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        facility_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        facility_type TEXT DEFAULT 'Building',
        category TEXT,
        address TEXT,
        city TEXT,
        country TEXT,
        postal_code TEXT,
        contact_person TEXT,
        contact_phone TEXT,
        contact_email TEXT,
        company_id INTEGER,
        branch_id INTEGER,
        parent_facility_id INTEGER,
        is_active INTEGER DEFAULT 1,
        is_critical INTEGER DEFAULT 0,
        operating_hours TEXT,
        notes TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL,
        FOREIGN KEY (branch_id) REFERENCES company_branches(id) ON DELETE SET NULL,
        FOREIGN KEY (parent_facility_id) REFERENCES maintenance_facilities(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 2. Maintenance Facility Requests - Facility Maintenance Requests
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_facility_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_number TEXT UNIQUE NOT NULL,
        facility_id INTEGER NOT NULL,
        request_type TEXT DEFAULT 'Corrective',
        category TEXT,
        priority TEXT DEFAULT 'Medium',
        severity TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'Open',
        reported_by INTEGER,
        reported_date DATE NOT NULL,
        required_by_date DATE,
        description TEXT NOT NULL,
        assigned_team_id INTEGER,
        assigned_technician_id INTEGER,
        scheduled_date DATE,
        completed_date DATE,
        resolution_notes TEXT,
        requester_feedback TEXT,
        attachment_urls TEXT,
        is_emergency INTEGER DEFAULT 0,
        downtime_hours DECIMAL(6,2) DEFAULT 0,
        estimated_cost DECIMAL(12,2) DEFAULT 0,
        actual_cost DECIMAL(12,2) DEFAULT 0,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (facility_id) REFERENCES maintenance_facilities(id) ON DELETE CASCADE,
        FOREIGN KEY (reported_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (assigned_team_id) REFERENCES maintenance_teams(id) ON DELETE SET NULL,
        FOREIGN KEY (assigned_technician_id) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 3. Maintenance Teams - Team Definitions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_code TEXT UNIQUE NOT NULL,
        team_name TEXT NOT NULL,
        description TEXT,
        team_lead_id INTEGER,
        department_id INTEGER,
        company_id INTEGER,
        is_active INTEGER DEFAULT 1,
        max_concurrent_work_orders INTEGER DEFAULT 5,
        skill_specializations TEXT,
        working_hours TEXT,
        notes TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (team_lead_id) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (department_id) REFERENCES hr_departments(id) ON DELETE SET NULL,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 4. Maintenance Team Members - Team Member Assignments
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_team_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_id INTEGER NOT NULL,
        employee_id INTEGER NOT NULL,
        role TEXT DEFAULT 'Technician',
        is_active INTEGER DEFAULT 1,
        joined_date DATE,
        left_date DATE,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (team_id) REFERENCES maintenance_teams(id) ON DELETE CASCADE,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 5. Maintenance Technician Skills - Skill/Certification Tracking
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_technician_skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
        skill_name TEXT NOT NULL,
        certification_name TEXT,
        certification_number TEXT,
        certification_expiry DATE,
        proficiency_level TEXT DEFAULT 'Intermediate',
        years_experience DECIMAL(4,1) DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES hr_employees(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 6. Maintenance Checklist Templates - Reusable Inspection Checklists
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_checklist_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_code TEXT UNIQUE NOT NULL,
        template_name TEXT NOT NULL,
        description TEXT,
        checklist_type TEXT DEFAULT 'Inspection',
        applicable_to TEXT,
        is_active INTEGER DEFAULT 1,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 7. Maintenance Checklist Items - Items Within Checklists
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_checklist_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_id INTEGER NOT NULL,
        item_sequence INTEGER DEFAULT 1,
        item_description TEXT NOT NULL,
        item_type TEXT DEFAULT 'Pass/Fail',
        is_required INTEGER DEFAULT 1,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (template_id) REFERENCES maintenance_checklist_templates(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 8. Work Order Tasks - Work Order Task Lines
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_work_order_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_order_id INTEGER NOT NULL,
        task_sequence INTEGER DEFAULT 1,
        task_description TEXT NOT NULL,
        task_type TEXT DEFAULT 'Maintenance',
        assigned_technician_id INTEGER,
        status TEXT DEFAULT 'Pending',
        is_completed INTEGER DEFAULT 0,
        completed_by INTEGER,
        completed_at DATETIME,
        notes TEXT,
        attachment_urls TEXT,
        estimated_hours DECIMAL(6,2) DEFAULT 0,
        actual_hours DECIMAL(6,2) DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (work_order_id) REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,
        FOREIGN KEY (assigned_technician_id) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (completed_by) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 9. Downtime Logs - Equipment/Facility Downtime Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_downtime_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_number TEXT UNIQUE NOT NULL,
        asset_id INTEGER,
        facility_id INTEGER,
        work_order_id INTEGER,
        downtime_reason TEXT,
        downtime_start DATETIME NOT NULL,
        downtime_end DATETIME,
        planned_downtime INTEGER DEFAULT 0,
        total_hours DECIMAL(8,2) DEFAULT 0,
        impact_level TEXT DEFAULT 'Medium',
        lost_production_value DECIMAL(12,2) DEFAULT 0,
        repair_category TEXT,
        root_cause TEXT,
        corrective_action TEXT,
        is_resolved INTEGER DEFAULT 0,
        resolved_by INTEGER,
        resolved_at DATETIME,
        notes TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
        FOREIGN KEY (facility_id) REFERENCES maintenance_facilities(id) ON DELETE CASCADE,
        FOREIGN KEY (work_order_id) REFERENCES maintenance_work_orders(id) ON DELETE SET NULL,
        FOREIGN KEY (resolved_by) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 10. Spare Parts/Material Usage - Inventory Consumption Tracking
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_parts_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usage_number TEXT UNIQUE NOT NULL,
        work_order_id INTEGER,
        work_log_id INTEGER,
        part_id INTEGER,
        part_number TEXT,
        part_name TEXT NOT NULL,
        quantity_requested DECIMAL(10,2) DEFAULT 0,
        quantity_issued DECIMAL(10,2) DEFAULT 0,
        quantity_used DECIMAL(10,2) DEFAULT 0,
        quantity_returned DECIMAL(10,2) DEFAULT 0,
        unit_of_measure TEXT DEFAULT 'Unit',
        warehouse_id INTEGER,
        issue_date DATE,
        return_date DATE,
        unit_cost DECIMAL(12,2) DEFAULT 0,
        total_cost DECIMAL(12,2) DEFAULT 0,
        status TEXT DEFAULT 'Issued',
        notes TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (work_order_id) REFERENCES maintenance_work_orders(id) ON DELETE SET NULL,
        FOREIGN KEY (work_log_id) REFERENCES maintenance_work_logs(id) ON DELETE SET NULL,
        FOREIGN KEY (warehouse_id) REFERENCES wms_warehouses(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 11. Labor/Time Logs - Labor Time Tracking Entries
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_labor_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_number TEXT UNIQUE NOT NULL,
        work_order_id INTEGER NOT NULL,
        technician_id INTEGER NOT NULL,
        work_date DATE NOT NULL,
        start_time TEXT,
        end_time TEXT,
        total_hours DECIMAL(6,2) DEFAULT 0,
        regular_hours DECIMAL(6,2) DEFAULT 0,
        overtime_hours DECIMAL(6,2) DEFAULT 0,
        hourly_rate DECIMAL(10,2) DEFAULT 0,
        labor_cost DECIMAL(12,2) DEFAULT 0,
        work_description TEXT,
        is_billable INTEGER DEFAULT 0,
        approval_status TEXT DEFAULT 'Approved',
        approved_by INTEGER,
        approved_at DATETIME,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (work_order_id) REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,
        FOREIGN KEY (technician_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (approved_by) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 12. SLA Rules - SLA Configuration Rules
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_sla_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_code TEXT UNIQUE NOT NULL,
        rule_name TEXT NOT NULL,
        priority TEXT NOT NULL,
        response_time_hours INTEGER DEFAULT 4,
        resolution_time_hours INTEGER DEFAULT 24,
        escalation_1_hours INTEGER DEFAULT 2,
        escalation_2_hours INTEGER DEFAULT 4,
        is_active INTEGER DEFAULT 1,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 13. Escalation Rules - Escalation Definitions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_escalation_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_name TEXT NOT NULL,
        trigger_type TEXT NOT NULL,
        trigger_value TEXT NOT NULL,
        escalation_level INTEGER DEFAULT 1,
        escalate_to_role TEXT,
        escalate_to_employee_id INTEGER,
        action_type TEXT DEFAULT 'Notify',
        notification_template TEXT,
        is_active INTEGER DEFAULT 1,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (escalate_to_employee_id) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 14. Work Order Approvals - Approval Workflow Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        approval_number TEXT UNIQUE NOT NULL,
        work_order_id INTEGER,
        request_id INTEGER,
        approval_type TEXT NOT NULL,
        status TEXT DEFAULT 'Pending',
        requested_by INTEGER,
        requested_at DATETIME,
        reviewed_by INTEGER,
        reviewed_at DATETIME,
        decision_notes TEXT,
        rejection_reason TEXT,
        is_escalated INTEGER DEFAULT 0,
        parent_approval_id INTEGER,
        sequence_order INTEGER DEFAULT 1,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (work_order_id) REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,
        FOREIGN KEY (requested_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (parent_approval_id) REFERENCES maintenance_approvals(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 15. Checklist Results - Completed Checklist Results
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_checklist_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_order_id INTEGER,
        checklist_template_id INTEGER,
        asset_id INTEGER,
        facility_id INTEGER,
        inspector_id INTEGER NOT NULL,
        inspection_date DATE NOT NULL,
        findings TEXT,
        overall_status TEXT DEFAULT 'Pass',
        action_required INTEGER DEFAULT 0,
        next_inspection_date DATE,
        attachment_urls TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (work_order_id) REFERENCES maintenance_work_orders(id) ON DELETE SET NULL,
        FOREIGN KEY (checklist_template_id) REFERENCES maintenance_checklist_templates(id) ON DELETE SET NULL,
        FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE SET NULL,
        FOREIGN KEY (facility_id) REFERENCES maintenance_facilities(id) ON DELETE SET NULL,
        FOREIGN KEY (inspector_id) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 16. Checklist Item Results - Individual Item Results
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_checklist_item_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        checklist_result_id INTEGER NOT NULL,
        checklist_item_id INTEGER NOT NULL,
        result_value TEXT,
        result_status TEXT DEFAULT 'Pass',
        remarks TEXT,
        photo_urls TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (checklist_result_id) REFERENCES maintenance_checklist_results(id) ON DELETE CASCADE,
        FOREIGN KEY (checklist_item_id) REFERENCES maintenance_checklist_items(id) ON DELETE CASCADE
    )""",
]

# Indexes for performance
MAINTENANCE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_maint_facilities_code ON maintenance_facilities(facility_code)",
    "CREATE INDEX IF NOT EXISTS idx_maint_facilities_company ON maintenance_facilities(company_id)",
    "CREATE INDEX IF NOT EXISTS idx_maint_facility_requests_facility ON maintenance_facility_requests(facility_id)",
    "CREATE INDEX IF NOT EXISTS idx_maint_facility_requests_status ON maintenance_facility_requests(status)",
    "CREATE INDEX IF NOT EXISTS idx_maint_teams_code ON maintenance_teams(team_code)",
    "CREATE INDEX IF NOT EXISTS idx_maint_team_members_team ON maintenance_team_members(team_id)",
    "CREATE INDEX IF NOT EXISTS idx_maint_team_members_employee ON maintenance_team_members(employee_id)",
    "CREATE INDEX IF NOT EXISTS idx_maint_technician_skills_employee ON maintenance_technician_skills(employee_id)",
    "CREATE INDEX IF NOT EXISTS idx_maint_checklist_template_code ON maintenance_checklist_templates(template_code)",
    "CREATE INDEX IF NOT EXISTS idx_maint_work_order_tasks_wo ON maintenance_work_order_tasks(work_order_id)",
    "CREATE INDEX IF NOT EXISTS idx_maint_downtime_logs_asset ON maintenance_downtime_logs(asset_id)",
    "CREATE INDEX IF NOT EXISTS idx_maint_downtime_logs_facility ON maintenance_downtime_logs(facility_id)",
    "CREATE INDEX IF NOT EXISTS idx_maint_parts_usage_wo ON maintenance_parts_usage(work_order_id)",
    "CREATE INDEX IF NOT EXISTS idx_maint_labor_logs_wo ON maintenance_labor_logs(work_order_id)",
    "CREATE INDEX IF NOT EXISTS idx_maint_labor_logs_tech ON maintenance_labor_logs(technician_id)",
    "CREATE INDEX IF NOT EXISTS idx_maint_approvals_wo ON maintenance_approvals(work_order_id)",
    "CREATE INDEX IF NOT EXISTS idx_maint_checklist_results_wo ON maintenance_checklist_results(work_order_id)",
]

# Extended work order status constants
MAINTENANCE_WORK_ORDER_STATUSES = [
    'Draft',
    'Open',
    'Approved',
    'Assigned',
    'In Progress',
    'On Hold',
    'Waiting Parts',
    'Waiting Vendor',
    'Completed',
    'Verified',
    'Closed',
    'Canceled',
    'Rejected'
]

MAINTENANCE_PRIORITIES = ['Low', 'Medium', 'High', 'Critical']
MAINTENANCE_SEVERITIES = ['Low', 'Medium', 'High', 'Critical', 'Emergency']
MAINTENANCE_REQUEST_TYPES = ['Preventive', 'Corrective', 'Emergency', 'Inspection', 'Calibration']
MAINTENANCE_FREQUENCIES = ['Daily', 'Weekly', 'Bi-Weekly', 'Monthly', 'Quarterly', 'Semi-Annual', 'Annual', 'Custom']
FACILITY_TYPES = ['Building', 'Warehouse', 'Office', 'Factory', 'Data Center', 'Retail', 'Site', 'Area', 'Floor', 'Room']
DOWNTIME_IMPACT_LEVELS = ['Negligible', 'Low', 'Medium', 'High', 'Critical', 'Catastrophic']
APPROVAL_STATUSES = ['Pending', 'Approved', 'Rejected', 'Returned', 'Escalated']


# =============================================================================
# INITIALIZATION FUNCTION
# =============================================================================

def init_maintenance_tables():
    """
    Initialize all maintenance management tables.
    Called during app startup to ensure tables exist.
    """
    conn = get_db()
    try:
        cursor = conn.cursor()

        # Create tables
        for table_sql in MAINTENANCE_TABLES:
            cursor.execute(table_sql)

        # Create indexes
        for index_sql in MAINTENANCE_INDEXES:
            cursor.execute(index_sql)

        conn.commit()

        # Seed default data
        _seed_maintenance_default_data(conn)

    finally:
        conn.close()


def _seed_maintenance_default_data(conn):
    """Seed default reference data for maintenance management."""
    cursor = conn.cursor()

    # Seed SLA Rules
    cursor.execute("SELECT COUNT(*) as cnt FROM maintenance_sla_rules")
    if cursor.fetchone()['cnt'] == 0:
        sla_rules = [
            ('SLA-CRIT', 'Critical Priority SLA', 'Critical', 1, 4, 1, 2, 1),
            ('SLA-HIGH', 'High Priority SLA', 'High', 2, 8, 2, 4, 1),
            ('SLA-MED', 'Medium Priority SLA', 'Medium', 4, 24, 4, 8, 1),
            ('SLA-LOW', 'Low Priority SLA', 'Low', 8, 72, 8, 24, 1),
        ]
        for code, name, priority, resp_hrs, resol_hrs, esc1, esc2, active in sla_rules:
            cursor.execute("""
                INSERT INTO maintenance_sla_rules
                (rule_code, rule_name, priority, response_time_hours, resolution_time_hours,
                 escalation_1_hours, escalation_2_hours, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (code, name, priority, resp_hrs, resol_hrs, esc1, esc2, active))

    # Seed Checklist Templates
    cursor.execute("SELECT COUNT(*) as cnt FROM maintenance_checklist_templates")
    if cursor.fetchone()['cnt'] == 0:
        # Equipment Inspection Template
        cursor.execute("""
            INSERT INTO maintenance_checklist_templates
            (template_code, template_name, description, checklist_type, applicable_to, is_active)
            VALUES ('EQUIP-INSP-001', 'Standard Equipment Inspection',
                    'Complete equipment safety and operational inspection', 'Inspection', 'Equipment', 1)
        """)
        equip_template_id = cursor.lastrowid

        equip_items = [
            (equip_template_id, 1, 'Visual inspection for damage or wear', 'Pass/Fail', 1),
            (equip_template_id, 2, 'Check all safety guards are in place', 'Pass/Fail', 1),
            (equip_template_id, 3, 'Verify emergency stop functionality', 'Pass/Fail', 1),
            (equip_template_id, 4, 'Check fluid levels (oil, hydraulic, coolant)', 'Pass/Fail', 1),
            (equip_template_id, 5, 'Inspect electrical connections', 'Pass/Fail', 1),
            (equip_template_id, 6, 'Test operational controls', 'Pass/Fail', 1),
            (equip_template_id, 7, 'Check for unusual noise or vibration', 'Pass/Fail', 1),
            (equip_template_id, 8, 'Verify warning labels visible', 'Pass/Fail', 1),
        ]
        for template_id, seq, desc, item_type, required in equip_items:
            cursor.execute("""
                INSERT INTO maintenance_checklist_items
                (template_id, item_sequence, item_description, item_type, is_required)
                VALUES (?, ?, ?, ?, ?)
            """, (template_id, seq, desc, item_type, required))

        # HVAC Inspection Template
        cursor.execute("""
            INSERT INTO maintenance_checklist_templates
            (template_code, template_name, description, checklist_type, applicable_to, is_active)
            VALUES ('HVAC-INSP-001', 'HVAC System Inspection',
                    'Comprehensive HVAC maintenance inspection', 'Inspection', 'HVAC', 1)
        """)
        hvac_template_id = cursor.lastrowid

        hvac_items = [
            (hvac_template_id, 1, 'Replace or clean air filters', 'Pass/Fail', 1),
            (hvac_template_id, 2, 'Check thermostat calibration', 'Pass/Fail', 1),
            (hvac_template_id, 3, 'Inspect condensate drain', 'Pass/Fail', 1),
            (hvac_template_id, 4, 'Check refrigerant levels', 'Pass/Fail', 1),
            (hvac_template_id, 5, 'Inspect electrical components', 'Pass/Fail', 1),
            (hvac_template_id, 6, 'Lubricate moving parts', 'Pass/Fail', 1),
            (hvac_template_id, 7, 'Check airflow across coils', 'Pass/Fail', 1),
            (hvac_template_id, 8, 'Verify compressor operation', 'Pass/Fail', 1),
            (hvac_template_id, 9, 'Inspect ductwork for leaks', 'Pass/Fail', 1),
            (hvac_template_id, 10, 'Record temperature readings', 'Reading', 1),
        ]
        for template_id, seq, desc, item_type, required in hvac_items:
            cursor.execute("""
                INSERT INTO maintenance_checklist_items
                (template_id, item_sequence, item_description, item_type, is_required)
                VALUES (?, ?, ?, ?, ?)
            """, (template_id, seq, desc, item_type, required))

        # Facility Safety Inspection Template
        cursor.execute("""
            INSERT INTO maintenance_checklist_templates
            (template_code, template_name, description, checklist_type, applicable_to, is_active)
            VALUES ('SAFE-INSP-001', 'Facility Safety Inspection',
                    'General facility safety and compliance inspection', 'Safety', 'Facility', 1)
        """)
        safe_template_id = cursor.lastrowid

        safe_items = [
            (safe_template_id, 1, 'Check fire extinguisher accessibility', 'Pass/Fail', 1),
            (safe_template_id, 2, 'Verify emergency exits clear', 'Pass/Fail', 1),
            (safe_template_id, 3, 'Inspect floor conditions (hazards)', 'Pass/Fail', 1),
            (safe_template_id, 4, 'Check lighting in all areas', 'Pass/Fail', 1),
            (safe_template_id, 5, 'Verify signage visible', 'Pass/Fail', 1),
            (safe_template_id, 6, 'Inspect stairways and handrails', 'Pass/Fail', 1),
            (safe_template_id, 7, 'Check electrical panel access', 'Pass/Fail', 1),
            (safe_template_id, 8, 'Inspect ventilation', 'Pass/Fail', 1),
        ]
        for template_id, seq, desc, item_type, required in safe_items:
            cursor.execute("""
                INSERT INTO maintenance_checklist_items
                (template_id, item_sequence, item_description, item_type, is_required)
                VALUES (?, ?, ?, ?, ?)
            """, (template_id, seq, desc, item_type, required))

    conn.commit()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_next_facility_code() -> str:
    """Generate the next facility code."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM maintenance_facilities")
        result = cursor.fetchone()
        seq = (result['cnt'] if result else 0) + 1
        return f"FAC-{seq:04d}"
    finally:
        conn.close()


def get_next_request_number() -> str:
    """Generate the next facility request number."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM maintenance_facility_requests")
        result = cursor.fetchone()
        seq = (result['cnt'] if result else 0) + 1
        return f"FMR-{datetime.now().strftime('%Y%m')}-{seq:04d}"
    finally:
        conn.close()


def get_next_team_code() -> str:
    """Generate the next team code."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM maintenance_teams")
        result = cursor.fetchone()
        seq = (result['cnt'] if result else 0) + 1
        return f"MT-{seq:03d}"
    finally:
        conn.close()


def get_next_downtime_log_number() -> str:
    """Generate the next downtime log number."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM maintenance_downtime_logs")
        result = cursor.fetchone()
        seq = (result['cnt'] if result else 0) + 1
        return f"DT-{datetime.now().strftime('%Y%m')}-{seq:04d}"
    finally:
        conn.close()


def get_next_parts_usage_number() -> str:
    """Generate the next parts usage number."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM maintenance_parts_usage")
        result = cursor.fetchone()
        seq = (result['cnt'] if result else 0) + 1
        return f"MPU-{datetime.now().strftime('%Y%m')}-{seq:04d}"
    finally:
        conn.close()


def get_next_labor_log_number() -> str:
    """Generate the next labor log number."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM maintenance_labor_logs")
        result = cursor.fetchone()
        seq = (result['cnt'] if result else 0) + 1
        return f"MLL-{datetime.now().strftime('%Y%m')}-{seq:04d}"
    finally:
        conn.close()


def get_next_approval_number() -> str:
    """Generate the next approval number."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM maintenance_approvals")
        result = cursor.fetchone()
        seq = (result['cnt'] if result else 0) + 1
        return f"APR-{datetime.now().strftime('%Y%m')}-{seq:04d}"
    finally:
        conn.close()


def get_facility_stats(facility_id: int = None) -> Dict[str, Any]:
    """Get statistics for a facility or all facilities."""
    conn = get_db()
    try:
        query = """
            SELECT
                COUNT(*) as total_requests,
                SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) as open_requests,
                SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN priority = 'Critical' AND status NOT IN ('Completed', 'Closed') THEN 1 ELSE 0 END) as critical_pending,
                SUM(downtime_hours) as total_downtime,
                SUM(actual_cost) as total_cost
            FROM maintenance_facility_requests
        """
        params = []
        if facility_id:
            query += " WHERE facility_id = ?"
            params.append(facility_id)

        result = conn.execute(query, params).fetchone()
        return dict(result) if result else {}
    finally:
        conn.close()


def get_technician_workload(technician_id: int = None, as_of_date: str = None) -> List[Dict]:
    """Get workload summary for technicians."""
    conn = get_db()
    try:
        query = """
            SELECT
                e.id as employee_id,
                e.first_name || ' ' || e.last_name as technician_name,
                e.employee_code,
                COUNT(mwo.id) as assigned_orders,
                SUM(CASE WHEN mwo.status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN mwo.status = 'Open' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN mwo.priority = 'Critical' THEN 1 ELSE 0 END) as critical_count
            FROM hr_employees e
            LEFT JOIN maintenance_work_orders mwo ON e.id = mwo.assigned_technician_id
                AND mwo.status NOT IN ('Completed', 'Closed', 'Canceled')
        """
        params = []
        if technician_id:
            query += " WHERE e.id = ?"
            params.append(technician_id)
        query += " GROUP BY e.id ORDER BY e.first_name"
        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def get_pm_compliance_rate(start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """Calculate PM compliance rate for reporting."""
    conn = get_db()
    try:
        query = """
            SELECT
                COUNT(*) as total_scheduled,
                SUM(CASE WHEN last_work_order_id IS NOT NULL THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN next_due_date < date('now') AND last_work_order_id IS NULL THEN 1 ELSE 0 END) as overdue,
                SUM(CASE WHEN next_due_date >= date('now') AND next_due_date <= date('now', '+7 days') AND last_work_order_id IS NULL THEN 1 ELSE 0 END) as due_soon
            FROM maintenance_schedules ms
            WHERE ms.is_active = 1
        """
        params = []
        if start_date:
            query += " AND ms.next_due_date >= ?"
            params.append(start_date)
        if end_date:
            query += " AND ms.next_due_date <= ?"
            params.append(end_date)

        result = conn.execute(query, params).fetchone()
        total = result['total_scheduled'] if result else 0
        completed = result['completed'] if result else 0
        compliance = (completed / total * 100) if total > 0 else 0

        return {
            'total_scheduled': total,
            'completed': completed,
            'overdue': result['overdue'] if result else 0,
            'due_soon': result['due_soon'] if result else 0,
            'compliance_rate': round(compliance, 2)
        }
    finally:
        conn.close()


def generate_pm_work_orders() -> List[int]:
    """
    Generate work orders for PM schedules that are due.
    Returns list of created work order IDs.
    """
    from asset_models import get_next_work_order_number

    conn = get_db()
    created_ids = []
    try:
        cursor = conn.cursor()

        # Find all active schedules that are due
        due_schedules = cursor.execute("""
            SELECT ms.*, a.asset_code, a.name as asset_name
            FROM maintenance_schedules ms
            JOIN assets a ON ms.asset_id = a.id
            WHERE ms.is_active = 1
            AND ms.next_due_date <= date('now')
            AND ms.last_work_order_id IS NULL
            ORDER BY ms.priority DESC, ms.next_due_date ASC
        """).fetchall()

        for schedule in due_schedules:
            wo_number = get_next_work_order_number()

            cursor.execute("""
                INSERT INTO maintenance_work_orders
                (work_order_number, asset_id, schedule_id, maintenance_type_id,
                 work_order_type, priority, status, issue_date,
                 issue_description, assigned_technician_id,
                 estimated_cost, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                wo_number,
                schedule['asset_id'],
                schedule['id'],
                schedule['maintenance_type_id'],
                'Preventive',
                schedule['priority'],
                'Open',
                datetime.now().strftime('%Y-%m-%d'),
                f"PM: {schedule['schedule_name'] or 'Scheduled maintenance'} - Asset: {schedule['asset_name']}",
                schedule['assigned_technician_id'],
                schedule['estimated_cost'],
                1
            ))

            created_ids.append(cursor.lastrowid)

            # Update schedule to prevent duplicate generation
            cursor.execute("""
                UPDATE maintenance_schedules
                SET last_work_order_id = ?
                WHERE id = ?
            """, (cursor.lastrowid, schedule['id']))

        conn.commit()
        return created_ids
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_maintenance_dashboard_stats(company_id: int = None, branch_id: int = None) -> Dict[str, Any]:
    """Get comprehensive dashboard statistics."""
    conn = get_db()
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        start_of_month = datetime.now().replace(day=1).strftime('%Y-%m-%d')

        stats = {}

        # Work order stats
        wo_query = """
            SELECT
                COUNT(*) as total_wo,
                SUM(CASE WHEN mwo.status = 'Open' THEN 1 ELSE 0 END) as open_wo,
                SUM(CASE WHEN mwo.status = 'In Progress' THEN 1 ELSE 0 END) as in_progress_wo,
                SUM(CASE WHEN mwo.status = 'On Hold' THEN 1 ELSE 0 END) as on_hold_wo,
                SUM(CASE WHEN mwo.status = 'Waiting Parts' OR mwo.status = 'Waiting Vendor' THEN 1 ELSE 0 END) as waiting_wo,
                SUM(CASE WHEN mwo.status IN ('Completed', 'Verified', 'Closed') THEN 1 ELSE 0 END) as completed_wo,
                SUM(CASE WHEN mwo.priority = 'Critical' AND mwo.status NOT IN ('Completed', 'Verified', 'Closed', 'Canceled') THEN 1 ELSE 0 END) as critical_wo,
                SUM(mwo.actual_cost) as total_actual_cost,
                SUM(mwo.downtime_hours) as total_downtime_hours
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            WHERE 1=1
        """
        wo_params = []
        if company_id:
            wo_query += " AND a.company_id = ?"
            wo_params.append(company_id)
        if branch_id:
            wo_query += " AND a.branch_id = ?"
            wo_params.append(branch_id)

        wo_stats = conn.execute(wo_query, wo_params).fetchone()
        stats['work_orders'] = dict(wo_stats) if wo_stats else {}

        # PM schedule stats
        pm_query = """
            SELECT
                COUNT(*) as total_pm,
                SUM(CASE WHEN is_active = 1 AND next_due_date < date('now') THEN 1 ELSE 0 END) as overdue_pm,
                SUM(CASE WHEN is_active = 1 AND next_due_date >= date('now') AND next_due_date <= date('now', '+7 days') THEN 1 ELSE 0 END) as due_soon_pm,
                SUM(CASE WHEN is_active = 1 AND next_due_date >= date('now') AND next_due_date <= date('now', '+30 days') THEN 1 ELSE 0 END) as due_this_month_pm
            FROM maintenance_schedules
        """
        pm_stats = conn.execute(pm_query).fetchone()
        stats['preventive_maintenance'] = dict(pm_stats) if pm_stats else {}

        # Facility request stats
        fac_query = """
            SELECT
                COUNT(*) as total_requests,
                SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) as open_requests,
                SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
                SUM(CASE WHEN is_emergency = 1 AND status NOT IN ('Completed', 'Closed') THEN 1 ELSE 0 END) as emergency_requests,
                SUM(actual_cost) as total_cost
            FROM maintenance_facility_requests
        """
        fac_stats = conn.execute(fac_query).fetchone()
        stats['facility_requests'] = dict(fac_stats) if fac_stats else {}

        # Cost stats
        cost_query = """
            SELECT
                SUM(CASE WHEN cost_date >= ? THEN amount ELSE 0 END) as month_cost,
                SUM(CASE WHEN cost_date >= date('now', '-30 days') THEN amount ELSE 0 END) as last_30_days_cost,
                SUM(CASE WHEN cost_date >= date('now', '-90 days') THEN amount ELSE 0 END) as last_90_days_cost
            FROM maintenance_cost_entries
        """
        cost_stats = conn.execute(cost_query, (start_of_month,)).fetchone()
        stats['costs'] = dict(cost_stats) if cost_stats else {}

        # Technician workload
        tech_query = """
            SELECT
                COUNT(DISTINCT assigned_technician_id) as active_technicians,
                SUM(CASE WHEN status IN ('Open', 'Assigned', 'In Progress') THEN 1 ELSE 0 END) as active_assignments
            FROM maintenance_work_orders
            WHERE assigned_technician_id IS NOT NULL
            AND status NOT IN ('Completed', 'Closed', 'Canceled')
        """
        tech_stats = conn.execute(tech_query).fetchone()
        stats['technicians'] = dict(tech_stats) if tech_stats else {}

        return stats
    finally:
        conn.close()


# =============================================================================
# RUN INITIALIZATION
# =============================================================================

if __name__ == '__main__' or True:
    init_maintenance_tables()
