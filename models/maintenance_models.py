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

    # =========================================================================
    # ENHANCED EAM/PM TABLES - Phase 1: Technical Objects & Structures
    # =========================================================================

    # -------------------------------------------------------------------------
    # 17. Functional Locations - Multi-level Location Hierarchy
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS functional_locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location_code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        location_type TEXT DEFAULT 'Area',
        parent_location_id INTEGER,
        address TEXT,
        cost_center TEXT,
        company_id INTEGER,
        branch_id INTEGER,
        is_active INTEGER DEFAULT 1,
        is_critical INTEGER DEFAULT 0,
        operating_hours TEXT,
        hierarchy_path TEXT,
        hierarchy_level INTEGER DEFAULT 0,
        latitude DECIMAL(10,8),
        longitude DECIMAL(11,8),
        qr_code TEXT,
        bar_code TEXT,
        specifications TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_location_id) REFERENCES functional_locations(id) ON DELETE SET NULL,
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL,
        FOREIGN KEY (branch_id) REFERENCES company_branches(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 18. Equipment BOMs - Bills of Materials for Equipment
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS equipment_boms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bom_code TEXT UNIQUE NOT NULL,
        equipment_id INTEGER NOT NULL,
        bom_type TEXT DEFAULT 'SpareParts',
        version INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1,
        is_template INTEGER DEFAULT 0,
        valid_from DATE,
        valid_to DATE,
        description TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (equipment_id) REFERENCES assets(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 19. Equipment BOM Items - Items within BOMs
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS equipment_bom_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bom_id INTEGER NOT NULL,
        item_sequence INTEGER DEFAULT 1,
        material_id INTEGER,
        part_number TEXT,
        part_name TEXT NOT NULL,
        quantity DECIMAL(10,3) NOT NULL,
        unit_of_measure TEXT DEFAULT 'EA',
        is_optional INTEGER DEFAULT 0,
        is_substitute_allowed INTEGER DEFAULT 0,
        substitute_group TEXT,
        work_center_id INTEGER,
        storage_location_id INTEGER,
        bom_position TEXT,
        lead_time_days INTEGER DEFAULT 0,
        cost_estimate DECIMAL(12,2) DEFAULT 0,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (bom_id) REFERENCES equipment_boms(id) ON DELETE CASCADE,
        FOREIGN KEY (material_id) REFERENCES inventory_items(id) ON DELETE SET NULL,
        FOREIGN KEY (work_center_id) REFERENCES work_centers(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 20. BOM Substitutes - Alternative Materials
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS bom_substitutes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bom_item_id INTEGER NOT NULL,
        substitute_material_id INTEGER,
        substitute_part_number TEXT,
        substitute_name TEXT,
        priority INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (bom_item_id) REFERENCES equipment_bom_items(id) ON DELETE CASCADE,
        FOREIGN KEY (substitute_material_id) REFERENCES inventory_items(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 21. Equipment Structures - Parent-Child Equipment Relationships
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS equipment_structures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_equipment_id INTEGER NOT NULL,
        child_equipment_id INTEGER NOT NULL,
        position TEXT NOT NULL,
        quantity DECIMAL(10,3) DEFAULT 1,
        is_mounted INTEGER DEFAULT 1,
        installed_date DATE,
        warranty_expires DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (parent_equipment_id) REFERENCES assets(id) ON DELETE CASCADE,
        FOREIGN KEY (child_equipment_id) REFERENCES assets(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 22. Work Centers - Work Center Definitions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS work_centers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_center_code TEXT UNIQUE NOT NULL,
        work_center_name TEXT NOT NULL,
        plant_id INTEGER,
        description TEXT,
        work_center_category TEXT,
        location_id INTEGER,
        cost_center TEXT,
        standard_wrk_dir TEXT,
        factory_calendar TEXT,
        currency TEXT DEFAULT 'USD',
        available_capacity DECIMAL(10,2) DEFAULT 8.0,
        capacity_unit TEXT DEFAULT 'HOUR',
        utilization_target DECIMAL(5,2) DEFAULT 100.0,
        supervisor_id INTEGER,
        shift_pattern TEXT,
        capabilities TEXT,
        skilled_workers INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (plant_id) REFERENCES company_branches(id) ON DELETE SET NULL,
        FOREIGN KEY (location_id) REFERENCES functional_locations(id) ON DELETE SET NULL,
        FOREIGN KEY (supervisor_id) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 23. Work Center Capacity - Capacity Planning
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS work_center_capacity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_center_id INTEGER NOT NULL,
        work_date DATE NOT NULL,
        available_hours DECIMAL(10,2) DEFAULT 8.0,
        booked_hours DECIMAL(10,2) DEFAULT 0,
        overtime_hours DECIMAL(10,2) DEFAULT 0,
        maintenance_type TEXT,
        notes TEXT,
        FOREIGN KEY (work_center_id) REFERENCES work_centers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 24. Work Center Shifts - Shift Definitions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS work_center_shifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_center_id INTEGER NOT NULL,
        shift_code TEXT NOT NULL,
        shift_name TEXT,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        break_duration INTEGER DEFAULT 60,
        is_night_shift INTEGER DEFAULT 0,
        capacity_factor DECIMAL(5,2) DEFAULT 100.0,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (work_center_id) REFERENCES work_centers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 25. Work Order Operations - Operations within Work Orders
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS work_order_operations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_order_id INTEGER NOT NULL,
        operation_sequence INTEGER DEFAULT 1,
        operation_id INTEGER,
        work_center_id INTEGER,
        description TEXT NOT NULL,
        plant_id INTEGER,
        work_unit TEXT DEFAULT 'HR',
        duration DECIMAL(10,2) DEFAULT 0,
        duration_unit TEXT DEFAULT 'HOUR',
        setup_time DECIMAL(10,2) DEFAULT 0,
        teardown_time DECIMAL(10,2) DEFAULT 0,
        external_work_duration DECIMAL(10,2) DEFAULT 0,
        cost_element TEXT,
        plant_sewing_time DECIMAL(10,2) DEFAULT 0,
        is_suboperation INTEGER DEFAULT 0,
        parent_operation_id INTEGER,
        is_final_operation INTEGER DEFAULT 0,
        status TEXT DEFAULT 'Pending',
        actual_start_date DATETIME,
        actual_end_date DATETIME,
        actual_duration DECIMAL(10,2),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (work_order_id) REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,
        FOREIGN KEY (work_center_id) REFERENCES work_centers(id) ON DELETE SET NULL,
        FOREIGN KEY (operation_id) REFERENCES work_order_operation_codes(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 26. Work Order Operation Codes - Operation Catalog
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS work_order_operation_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        operation_code TEXT UNIQUE NOT NULL,
        description TEXT,
        work_center_id INTEGER,
        default_duration DECIMAL(10,2),
        default_cost_element TEXT,
        skills_required TEXT,
        tools_required TEXT,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (work_center_id) REFERENCES work_centers(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 27. Work Order Components - Materials/Parts on Work Orders
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS work_order_components (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_order_id INTEGER NOT NULL,
        operation_id INTEGER,
        material_id INTEGER,
        part_number TEXT,
        part_name TEXT NOT NULL,
        quantity_required DECIMAL(10,3) NOT NULL,
        unit_of_measure TEXT DEFAULT 'EA',
        quantity_withdrawn DECIMAL(10,3) DEFAULT 0,
        warehouse_id INTEGER,
        storage_location TEXT,
        reservation_date DATE,
        requirement_date DATE,
        is_optional INTEGER DEFAULT 0,
        is_serialized INTEGER DEFAULT 0,
        bom_item_id INTEGER,
        is_withdrawn INTEGER DEFAULT 0,
        withdrawn_by INTEGER,
        withdrawn_at DATETIME,
        cost_estimate DECIMAL(12,2) DEFAULT 0,
        FOREIGN KEY (work_order_id) REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,
        FOREIGN KEY (material_id) REFERENCES inventory_items(id) ON DELETE SET NULL,
        FOREIGN KEY (bom_item_id) REFERENCES equipment_bom_items(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 28. Work Order Tools - Tools/Resources for Work Orders
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS work_order_tools (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_order_id INTEGER NOT NULL,
        operation_id INTEGER,
        tool_id INTEGER,
        tool_name TEXT NOT NULL,
        quantity_required DECIMAL(10,3) DEFAULT 1,
        quantity_allocated DECIMAL(10,3) DEFAULT 0,
        unit_of_measure TEXT DEFAULT 'EA',
        reservation_start DATETIME,
        reservation_end DATETIME,
        is_returnable INTEGER DEFAULT 1,
        is_withdrawn INTEGER DEFAULT 0,
        FOREIGN KEY (work_order_id) REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,
        FOREIGN KEY (tool_id) REFERENCES inventory_items(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 29. Work Order Confirmations - Technical/Final Confirmations
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS work_order_confirmations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_order_id INTEGER NOT NULL,
        confirmation_type TEXT DEFAULT 'FINAL',
        confirmation_date DATE NOT NULL,
        technician_id INTEGER NOT NULL,
        work_center_id INTEGER,
        operation_id INTEGER,
        yield_time DECIMAL(10,2) DEFAULT 0,
        labor_time DECIMAL(10,2) DEFAULT 0,
        setup_time DECIMAL(10,2) DEFAULT 0,
        tear_time DECIMAL(10,2) DEFAULT 0,
        quantity_completed DECIMAL(10,3) DEFAULT 0,
        quantity_rejected DECIMAL(10,3) DEFAULT 0,
        rejection_reason TEXT,
        labor_cost DECIMAL(12,2) DEFAULT 0,
        external_service_cost DECIMAL(12,2) DEFAULT 0,
        is_reversed INTEGER DEFAULT 0,
        reversed_by INTEGER,
        reversed_at DATETIME,
        reversal_reason TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (work_order_id) REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,
        FOREIGN KEY (technician_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (work_center_id) REFERENCES work_centers(id) ON DELETE SET NULL
    )""",

    # =========================================================================
    # ENHANCED EAM/PM TABLES - Phase 2: Preventive Maintenance
    # =========================================================================

    # -------------------------------------------------------------------------
    # 30. Maintenance Strategies - PM Strategy Definitions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_strategies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        strategy_code TEXT UNIQUE NOT NULL,
        strategy_name TEXT NOT NULL,
        strategy_type TEXT NOT NULL,
        description TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 31. Maintenance Counters - Equipment Counters for PM
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_counters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        counter_code TEXT UNIQUE NOT NULL,
        equipment_id INTEGER NOT NULL,
        counter_type TEXT DEFAULT 'OPERATING_HOURS',
        unit_of_measure TEXT DEFAULT 'HOUR',
        current_value DECIMAL(15,3) DEFAULT 0,
        last_reset_value DECIMAL(15,3) DEFAULT 0,
        last_reset_date DATE,
        counter_reading_date DATETIME,
        min_warning_threshold DECIMAL(15,3),
        max_warning_threshold DECIMAL(15,3),
        min_critical_threshold DECIMAL(15,3),
        max_critical_threshold DECIMAL(15,3),
        is_active INTEGER DEFAULT 1,
        reading_source TEXT DEFAULT 'MANUAL',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (equipment_id) REFERENCES assets(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 32. Counter Readings - Counter Reading History
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS counter_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        counter_id INTEGER NOT NULL,
        reading_value DECIMAL(15,3) NOT NULL,
        reading_date DATETIME NOT NULL,
        reading_type TEXT DEFAULT 'MANUAL',
        iot_device_id TEXT,
        is_forecasted INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (counter_id) REFERENCES maintenance_counters(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 33. Condition Indicators - Condition Monitoring Indicators
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS condition_indicators (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        indicator_code TEXT UNIQUE NOT NULL,
        equipment_id INTEGER NOT NULL,
        indicator_name TEXT NOT NULL,
        indicator_type TEXT DEFAULT 'VIBRATION',
        unit TEXT NOT NULL,
        sensor_id TEXT,
        sensor_location TEXT,
        normal_min DECIMAL(15,4),
        normal_max DECIMAL(15,4),
        warning_min DECIMAL(15,4),
        warning_max DECIMAL(15,4),
        critical_min DECIMAL(15,4),
        critical_max DECIMAL(15,4),
        calculation_method TEXT,
        reading_interval_minutes INTEGER DEFAULT 60,
        data_retention_days INTEGER DEFAULT 365,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (equipment_id) REFERENCES assets(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 34. Condition Readings - Condition Reading History
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS condition_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        indicator_id INTEGER NOT NULL,
        reading_value DECIMAL(15,4) NOT NULL,
        reading_timestamp DATETIME NOT NULL,
        status TEXT DEFAULT 'NORMAL',
        anomaly_score DECIMAL(5,2),
        iot_message_id TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (indicator_id) REFERENCES condition_indicators(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 35. Measurement Points - Physical Measurement Points on Equipment
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS measurement_points (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        point_code TEXT UNIQUE NOT NULL,
        equipment_id INTEGER NOT NULL,
        point_name TEXT NOT NULL,
        measurement_type TEXT DEFAULT 'READING',
        catalog_id INTEGER,
        location_description TEXT,
        location_lat DECIMAL(10,8),
        location_lng DECIMAL(11,8),
        unit_of_measure TEXT NOT NULL,
        decimal_places INTEGER DEFAULT 2,
        lower_limit DECIMAL(15,4),
        upper_limit DECIMAL(15,4),
        target_value DECIMAL(15,4),
        tolerance_minus DECIMAL(15,4),
        tolerance_plus DECIMAL(15,4),
        measurement_frequency TEXT,
        measurement_method TEXT,
        equipment_required TEXT,
        skills_required TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (equipment_id) REFERENCES assets(id) ON DELETE CASCADE
    )""",

    # =========================================================================
    # ENHANCED EAM/PM TABLES - Phase 3: Resource Planning
    # =========================================================================

    # -------------------------------------------------------------------------
    # 36. Shift Patterns - Shift Pattern Definitions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS shift_patterns (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pattern_code TEXT UNIQUE NOT NULL,
        pattern_name TEXT NOT NULL,
        plant_id INTEGER,
        start_date DATE NOT NULL,
        end_date DATE,
        pattern_type TEXT DEFAULT 'WEEKLY',
        is_rolling INTEGER DEFAULT 0,
        notes TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (plant_id) REFERENCES company_branches(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 37. Shift Definitions - Daily Shift Assignments
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS shift_definitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pattern_id INTEGER NOT NULL,
        day_of_week INTEGER NOT NULL,
        shift_code TEXT NOT NULL,
        shift_name TEXT,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        break_minutes INTEGER DEFAULT 60,
        effective_hours DECIMAL(5,2),
        capacity_hours DECIMAL(5,2),
        is_working_day INTEGER DEFAULT 1,
        FOREIGN KEY (pattern_id) REFERENCES shift_patterns(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 38. Technician Shifts - Technician Shift Assignments
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS technician_shifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        technician_id INTEGER NOT NULL,
        work_center_id INTEGER,
        shift_date DATE NOT NULL,
        shift_definition_id INTEGER,
        attendance_status TEXT DEFAULT 'PRESENT',
        overtime_hours DECIMAL(5,2) DEFAULT 0,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (technician_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (work_center_id) REFERENCES work_centers(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 39. Capacity Requirements - Work Order Capacity Requirements
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS capacity_requirements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_order_id INTEGER NOT NULL,
        operation_id INTEGER,
        work_center_id INTEGER NOT NULL,
        required_date DATE NOT NULL,
        required_capacity DECIMAL(10,2) NOT NULL,
        allocated_capacity DECIMAL(10,2) DEFAULT 0,
        capacity_unit TEXT DEFAULT 'HOUR',
        status TEXT DEFAULT 'PENDING',
        priority INTEGER DEFAULT 50,
        FOREIGN KEY (work_order_id) REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,
        FOREIGN KEY (work_center_id) REFERENCES work_centers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 40. Capacity Planning Views - Capacity Planning Snapshots
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS capacity_planning_views (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_center_id INTEGER NOT NULL,
        planning_date DATE NOT NULL,
        shift_id INTEGER,
        available_capacity DECIMAL(10,2) NOT NULL,
        scheduled_capacity DECIMAL(10,2) DEFAULT 0,
        available_seconds INTEGER,
        FOREIGN KEY (work_center_id) REFERENCES work_centers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 41. Skill Catalog - Skills and Certifications Catalog
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS skill_catalog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skill_code TEXT UNIQUE NOT NULL,
        skill_name TEXT NOT NULL,
        skill_category TEXT,
        description TEXT,
        certification_required INTEGER DEFAULT 0,
        validity_months INTEGER,
        is_active INTEGER DEFAULT 1
    )""",

    # -------------------------------------------------------------------------
    # 42. Work Order Skill Requirements - Skills Required for WO
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS work_order_skill_requirements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_order_id INTEGER NOT NULL,
        skill_id INTEGER NOT NULL,
        skill_level_required TEXT DEFAULT 'BASIC',
        priority INTEGER DEFAULT 1,
        FOREIGN KEY (work_order_id) REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,
        FOREIGN KEY (skill_id) REFERENCES skill_catalog(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 43. Technician Skill Levels - Technician Skill Profiles
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS technician_skill_levels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        technician_id INTEGER NOT NULL,
        skill_id INTEGER NOT NULL,
        skill_level TEXT DEFAULT 'BASIC',
        years_experience DECIMAL(4,1) DEFAULT 0,
        certification_number TEXT,
        certification_valid_until DATE,
        last_assessed DATE,
        proficiency_score DECIMAL(5,2),
        is_primary INTEGER DEFAULT 0,
        FOREIGN KEY (technician_id) REFERENCES hr_employees(id) ON DELETE CASCADE,
        FOREIGN KEY (skill_id) REFERENCES skill_catalog(id) ON DELETE CASCADE
    )""",

    # =========================================================================
    # ENHANCED EAM/PM TABLES - Phase 4: Costing & Settlement
    # =========================================================================

    # -------------------------------------------------------------------------
    # 44. Maintenance Cost Elements - Cost Element Definitions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_cost_elements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        element_code TEXT UNIQUE NOT NULL,
        element_name TEXT NOT NULL,
        cost_category TEXT DEFAULT 'LABOR',
        posting_key TEXT,
        gl_account TEXT,
        cost_center_required INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1
    )""",

    # -------------------------------------------------------------------------
    # 45. Work Order Cost Plan - Planned vs Actual Cost Tracking
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS work_order_cost_plan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_order_id INTEGER NOT NULL,
        cost_element_id INTEGER,
        planned_quantity DECIMAL(10,3) DEFAULT 0,
        planned_unit_cost DECIMAL(12,2) DEFAULT 0,
        planned_total_cost DECIMAL(12,2) DEFAULT 0,
        planned_hours DECIMAL(10,2) DEFAULT 0,
        actual_quantity DECIMAL(10,3) DEFAULT 0,
        actual_unit_cost DECIMAL(12,2) DEFAULT 0,
        actual_total_cost DECIMAL(12,2) DEFAULT 0,
        actual_hours DECIMAL(10,2) DEFAULT 0,
        variance_percent DECIMAL(8,2),
        FOREIGN KEY (work_order_id) REFERENCES maintenance_work_orders(id) ON DELETE CASCADE,
        FOREIGN KEY (cost_element_id) REFERENCES maintenance_cost_elements(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 46. Maintenance WIP - Work in Progress Tracking
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_wip (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_order_id INTEGER NOT NULL,
        period_id INTEGER NOT NULL,
        cost_element_id INTEGER,
        opening_quantity DECIMAL(10,3) DEFAULT 0,
        opening_value DECIMAL(12,2) DEFAULT 0,
        opening_hours DECIMAL(10,2) DEFAULT 0,
        additions_quantity DECIMAL(10,3) DEFAULT 0,
        additions_value DECIMAL(12,2) DEFAULT 0,
        additions_hours DECIMAL(10,2) DEFAULT 0,
        closing_quantity DECIMAL(10,3) DEFAULT 0,
        closing_value DECIMAL(12,2) DEFAULT 0,
        closing_hours DECIMAL(10,2) DEFAULT 0,
        settleable_quantity DECIMAL(10,3) DEFAULT 0,
        settled_quantity DECIMAL(10,3) DEFAULT 0,
        settled_value DECIMAL(12,2) DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (work_order_id) REFERENCES maintenance_work_orders(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 47. Settlement Rules - Settlement Configuration
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS settlement_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_code TEXT UNIQUE NOT NULL,
        rule_name TEXT NOT NULL,
        settlement_target_type TEXT,
        target_id INTEGER,
        settlement_percentage DECIMAL(5,2) DEFAULT 100.0,
        cost_categories TEXT,
        is_active INTEGER DEFAULT 1,
        valid_from DATE,
        valid_to DATE
    )""",

    # -------------------------------------------------------------------------
    # 48. Maintenance Settlements - Settlement Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_settlements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        work_order_id INTEGER NOT NULL,
        settlement_rule_id INTEGER,
        settlement_target_type TEXT NOT NULL,
        settlement_target_id INTEGER,
        settlement_date DATE NOT NULL,
        quantity_settled DECIMAL(10,3),
        value_settled DECIMAL(12,2) NOT NULL,
        cost_element_id INTEGER,
        reference_document TEXT,
        fiscal_period INTEGER,
        year INTEGER,
        posted_by INTEGER,
        posted_at DATETIME,
        reversal_document_id INTEGER,
        is_reversed INTEGER DEFAULT 0,
        FOREIGN KEY (work_order_id) REFERENCES maintenance_work_orders(id) ON DELETE CASCADE
    )""",

    # =========================================================================
    # ENHANCED EAM/PM TABLES - Phase 5: Service Management
    # =========================================================================

    # -------------------------------------------------------------------------
    # 49. Service Agreements - Service Contract Management
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS service_agreements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agreement_number TEXT UNIQUE NOT NULL,
        customer_id INTEGER NOT NULL,
        agreement_type TEXT DEFAULT 'MAINTENANCE',
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        response_time_hours INTEGER DEFAULT 4,
        resolution_time_hours INTEGER DEFAULT 24,
        availability_target DECIMAL(5,2),
        contract_value DECIMAL(15,2) DEFAULT 0,
        billing_frequency TEXT DEFAULT 'MONTHLY',
        payment_terms TEXT,
        status TEXT DEFAULT 'ACTIVE',
        auto_renewal INTEGER DEFAULT 0,
        contract_document_url TEXT,
        terms_conditions TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 50. Agreement Line Items - Service Agreement Details
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS agreement_line_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agreement_id INTEGER NOT NULL,
        line_type TEXT DEFAULT 'SERVICE',
        description TEXT NOT NULL,
        quantity DECIMAL(10,3),
        unit_price DECIMAL(12,2),
        total_price DECIMAL(12,2),
        service_type_id INTEGER,
        equipment_id INTEGER,
        coverage_details TEXT,
        FOREIGN KEY (agreement_id) REFERENCES service_agreements(id) ON DELETE CASCADE,
        FOREIGN KEY (equipment_id) REFERENCES assets(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 51. Service Order Types - Service Order Type Definitions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS service_order_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_type_code TEXT UNIQUE NOT NULL,
        order_type_name TEXT NOT NULL,
        notification_type TEXT,
        priority_default TEXT DEFAULT 'MEDIUM',
        work_order_type TEXT,
        auto_create_wo INTEGER DEFAULT 0,
        sla_rule_id INTEGER,
        FOREIGN KEY (sla_rule_id) REFERENCES maintenance_sla_rules(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 52. Warranty Records - Equipment Warranty Tracking
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS warranty_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_id INTEGER NOT NULL,
        warranty_type TEXT DEFAULT 'MANUFACTURER',
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        warranty_provider TEXT,
        warranty_number TEXT,
        coverage_scope TEXT DEFAULT 'FULL',
        coverage_details TEXT,
        maximum_claims INTEGER,
        claims_made INTEGER DEFAULT 0,
        maximum_value DECIMAL(15,2),
        value_used DECIMAL(15,2) DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (equipment_id) REFERENCES assets(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 53. Warranty Claims - Warranty Claim Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS warranty_claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        warranty_id INTEGER NOT NULL,
        claim_number TEXT UNIQUE NOT NULL,
        claim_date DATE NOT NULL,
        work_order_id INTEGER,
        description TEXT NOT NULL,
        claim_cost DECIMAL(12,2) DEFAULT 0,
        claim_status TEXT DEFAULT 'SUBMITTED',
        provider_response_date DATE,
        provider_reference TEXT,
        settled_amount DECIMAL(12,2) DEFAULT 0,
        settlement_date DATE,
        notes TEXT,
        FOREIGN KEY (warranty_id) REFERENCES warranty_records(id) ON DELETE CASCADE,
        FOREIGN KEY (work_order_id) REFERENCES maintenance_work_orders(id) ON DELETE SET NULL
    )""",

    # =========================================================================
    # ENHANCED EAM/PM TABLES - Phase 6: Notifications & Problem Management
    # =========================================================================

    # -------------------------------------------------------------------------
    # 54. Maintenance Notifications - Detailed Notifications
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        notification_number TEXT UNIQUE NOT NULL,
        notification_type TEXT NOT NULL,
        priority TEXT DEFAULT 'MEDIUM',
        short_text TEXT NOT NULL,
        long_text TEXT,
        equipment_id INTEGER,
        functional_location_id INTEGER,
        status TEXT DEFAULT 'OPEN',
        priority_calculated TEXT,
        damage_group TEXT,
        damage_code TEXT,
        cause_group TEXT,
        cause_code TEXT,
        object_part_group TEXT,
        object_part_code TEXT,
        reported_by INTEGER,
        responsible_person_id INTEGER,
        planner_group_id INTEGER,
        reported_date DATETIME NOT NULL,
        required_start_date DATE,
        required_end_date DATE,
        actual_start_date DATETIME,
        actual_end_date DATETIME,
        history TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        closed_at DATETIME,
        FOREIGN KEY (equipment_id) REFERENCES assets(id) ON DELETE SET NULL,
        FOREIGN KEY (functional_location_id) REFERENCES functional_locations(id) ON DELETE SET NULL,
        FOREIGN KEY (reported_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (responsible_person_id) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 55. Notification Items - Notification Line Items
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS notification_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        notification_id INTEGER NOT NULL,
        item_sequence INTEGER DEFAULT 1,
        item_text TEXT NOT NULL,
        item_status TEXT DEFAULT 'OPEN',
        completed_by INTEGER,
        completed_at DATETIME,
        FOREIGN KEY (notification_id) REFERENCES maintenance_notifications(id) ON DELETE CASCADE,
        FOREIGN KEY (completed_by) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 56. Notification Causes - Notification Cause Codes
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS notification_causes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        notification_id INTEGER NOT NULL,
        cause_sequence INTEGER DEFAULT 1,
        cause_group TEXT NOT NULL,
        cause_code TEXT NOT NULL,
        cause_text TEXT,
        is_root_cause INTEGER DEFAULT 0,
        responsibility_group TEXT,
        responsibility_code TEXT,
        FOREIGN KEY (notification_id) REFERENCES maintenance_notifications(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 57. Problem Records - Structured Problem Management
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS problem_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        problem_number TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        priority TEXT DEFAULT 'MEDIUM',
        status TEXT DEFAULT 'OPEN',
        problem_category TEXT,
        problem_type TEXT,
        related_notifications TEXT,
        related_work_orders TEXT,
        related_assets TEXT,
        root_cause_analysis TEXT,
        corrective_action TEXT,
        preventive_action TEXT,
        total_downtime_hours DECIMAL(10,2) DEFAULT 0,
        total_cost DECIMAL(15,2) DEFAULT 0,
        assigned_to INTEGER,
        approved_by INTEGER,
        closed_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        closed_at DATETIME,
        FOREIGN KEY (assigned_to) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (approved_by) REFERENCES hr_employees(id) ON DELETE SET NULL,
        FOREIGN KEY (closed_by) REFERENCES hr_employees(id) ON DELETE SET NULL
    )""",

    # =========================================================================
    # ENHANCED EAM/PM TABLES - Phase 7: IoT & Predictive Maintenance
    # =========================================================================

    # -------------------------------------------------------------------------
    # 58. IoT Devices - IoT Device Management
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS iot_devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_code TEXT UNIQUE NOT NULL,
        device_type TEXT NOT NULL,
        manufacturer TEXT,
        model TEXT,
        serial_number TEXT,
        protocol TEXT DEFAULT 'MQTT',
        endpoint_url TEXT,
        auth_type TEXT,
        credentials TEXT,
        sampling_interval_seconds INTEGER DEFAULT 60,
        data_format TEXT DEFAULT 'JSON',
        is_active INTEGER DEFAULT 1,
        installed_date DATE,
        installed_by INTEGER,
        location_id INTEGER,
        equipment_id INTEGER,
        latitude DECIMAL(10,8),
        longitude DECIMAL(11,8),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (equipment_id) REFERENCES assets(id) ON DELETE SET NULL,
        FOREIGN KEY (location_id) REFERENCES functional_locations(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 59. IoT Data Streams - IoT Data Stream Definitions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS iot_data_streams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER NOT NULL,
        stream_name TEXT NOT NULL,
        data_type TEXT,
        unit TEXT,
        precision INTEGER DEFAULT 2,
        retention_days INTEGER DEFAULT 90,
        is_active INTEGER DEFAULT 1,
        FOREIGN KEY (device_id) REFERENCES iot_devices(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 60. IoT Data Points - Individual IoT Data Points
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS iot_data_points (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        stream_id INTEGER NOT NULL,
        timestamp DATETIME NOT NULL,
        value DECIMAL(15,6) NOT NULL,
        quality TEXT DEFAULT 'GOOD',
        raw_payload TEXT,
        FOREIGN KEY (stream_id) REFERENCES iot_data_streams(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 61. IoT Alert Rules - Alert Rule Definitions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS iot_alert_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_code TEXT UNIQUE NOT NULL,
        rule_name TEXT NOT NULL,
        stream_id INTEGER NOT NULL,
        condition_type TEXT DEFAULT 'THRESHOLD',
        operator TEXT DEFAULT 'GT',
        threshold_value DECIMAL(15,6),
        threshold_value_max DECIMAL(15,6),
        severity TEXT DEFAULT 'WARNING',
        auto_create_notification INTEGER DEFAULT 1,
        auto_create_wo INTEGER DEFAULT 0,
        wo_template_id INTEGER,
        notify_technicians TEXT,
        notify_roles TEXT,
        email_recipients TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (stream_id) REFERENCES iot_data_streams(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 62. IoT Alerts - Triggered IoT Alerts
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS iot_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_id INTEGER NOT NULL,
        stream_id INTEGER NOT NULL,
        triggered_at DATETIME NOT NULL,
        trigger_value DECIMAL(15,6),
        severity TEXT,
        status TEXT DEFAULT 'TRIGGERED',
        notification_id INTEGER,
        work_order_id INTEGER,
        acknowledged_by INTEGER,
        acknowledged_at DATETIME,
        resolved_by INTEGER,
        resolved_at DATETIME,
        resolution_notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (rule_id) REFERENCES iot_alert_rules(id) ON DELETE CASCADE,
        FOREIGN KEY (notification_id) REFERENCES maintenance_notifications(id) ON DELETE SET NULL,
        FOREIGN KEY (work_order_id) REFERENCES maintenance_work_orders(id) ON DELETE SET NULL
    )""",

    # =========================================================================
    # ENHANCED EAM/PM TABLES - Phase 8: Security & Compliance
    # =========================================================================

    # -------------------------------------------------------------------------
    # 63. Maintenance Field Authorization - Field-level Access Control
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_field_authorization (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_id INTEGER NOT NULL,
        object_type TEXT NOT NULL,
        field_name TEXT NOT NULL,
        access_level TEXT DEFAULT 'READ',
        condition_expression TEXT,
        FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 64. Maintenance Data Scopes - Data Isolation Rules
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS maintenance_data_scopes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        scope_type TEXT NOT NULL,
        scope_value TEXT NOT NULL,
        access_level TEXT DEFAULT 'READ',
        is_default INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )""",
]

# Indexes for performance
MAINTENANCE_INDEXES = [
    # Original indexes
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

    # Enhanced EAM/PM indexes - Functional Locations
    "CREATE INDEX IF NOT EXISTS idx_func_loc_code ON functional_locations(location_code)",
    "CREATE INDEX IF NOT EXISTS idx_func_loc_parent ON functional_locations(parent_location_id)",
    "CREATE INDEX IF NOT EXISTS idx_func_loc_hierarchy ON functional_locations(hierarchy_path)",
    "CREATE INDEX IF NOT EXISTS idx_func_loc_company ON functional_locations(company_id)",

    # Equipment BOMs
    "CREATE INDEX IF NOT EXISTS idx_equip_bom_code ON equipment_boms(bom_code)",
    "CREATE INDEX IF NOT EXISTS idx_equip_bom_equipment ON equipment_boms(equipment_id)",
    "CREATE INDEX IF NOT EXISTS idx_equip_bom_items_bom ON equipment_bom_items(bom_id)",
    "CREATE INDEX IF NOT EXISTS idx_equip_bom_items_material ON equipment_bom_items(material_id)",
    "CREATE INDEX IF NOT EXISTS idx_bom_substitutes_item ON bom_substitutes(bom_item_id)",

    # Equipment Structures
    "CREATE INDEX IF NOT EXISTS idx_equip_struct_parent ON equipment_structures(parent_equipment_id)",
    "CREATE INDEX IF NOT EXISTS idx_equip_struct_child ON equipment_structures(child_equipment_id)",

    # Work Centers
    "CREATE INDEX IF NOT EXISTS idx_work_centers_code ON work_centers(work_center_code)",
    "CREATE INDEX IF NOT EXISTS idx_work_centers_plant ON work_centers(plant_id)",
    "CREATE INDEX IF NOT EXISTS idx_work_center_capacity_wc ON work_center_capacity(work_center_id)",
    "CREATE INDEX IF NOT EXISTS idx_work_center_capacity_date ON work_center_capacity(work_date)",
    "CREATE INDEX IF NOT EXISTS idx_work_center_shifts_wc ON work_center_shifts(work_center_id)",

    # Work Order Operations
    "CREATE INDEX IF NOT EXISTS idx_mwo_op_wo ON work_order_operations(work_order_id)",
    "CREATE INDEX IF NOT EXISTS idx_mwo_op_wc ON work_order_operations(work_center_id)",
    "CREATE INDEX IF NOT EXISTS idx_mwo_op_date ON work_order_operations(actual_start_date)",
    "CREATE INDEX IF NOT EXISTS idx_mwo_op_status ON work_order_operations(status)",

    # Work Order Components
    "CREATE INDEX IF NOT EXISTS idx_mwoc_wo ON work_order_components(work_order_id)",
    "CREATE INDEX IF NOT EXISTS idx_mwoc_material ON work_order_components(material_id)",
    "CREATE INDEX IF NOT EXISTS idx_mwoc_operation ON work_order_components(operation_id)",

    # Work Order Tools
    "CREATE INDEX IF NOT EXISTS idx_mwot_wo ON work_order_tools(work_order_id)",

    # Work Order Confirmations
    "CREATE INDEX IF NOT EXISTS idx_mwoc_conf_wo ON work_order_confirmations(work_order_id)",
    "CREATE INDEX IF NOT EXISTS idx_mwoc_conf_tech ON work_order_confirmations(technician_id)",
    "CREATE INDEX IF NOT EXISTS idx_mwoc_conf_date ON work_order_confirmations(confirmation_date)",

    # Maintenance Counters
    "CREATE INDEX IF NOT EXISTS idx_mc_counter_code ON maintenance_counters(counter_code)",
    "CREATE INDEX IF NOT EXISTS idx_mc_equipment ON maintenance_counters(equipment_id)",
    "CREATE INDEX IF NOT EXISTS idx_mcr_counter ON counter_readings(counter_id)",
    "CREATE INDEX IF NOT EXISTS idx_mcr_date ON counter_readings(reading_date)",

    # Condition Indicators
    "CREATE INDEX IF NOT EXISTS idx_mci_indicator_code ON condition_indicators(indicator_code)",
    "CREATE INDEX IF NOT EXISTS idx_mci_equipment ON condition_indicators(equipment_id)",
    "CREATE INDEX IF NOT EXISTS idx_mcir_indicator ON condition_readings(indicator_id)",
    "CREATE INDEX IF NOT EXISTS idx_mcir_timestamp ON condition_readings(reading_timestamp)",

    # Measurement Points
    "CREATE INDEX IF NOT EXISTS idx_mp_point_code ON measurement_points(point_code)",
    "CREATE INDEX IF NOT EXISTS idx_mp_equipment ON measurement_points(equipment_id)",

    # Shift Planning
    "CREATE INDEX IF NOT EXISTS idx_shift_patterns_code ON shift_patterns(pattern_code)",
    "CREATE INDEX IF NOT EXISTS idx_shift_defs_pattern ON shift_definitions(pattern_id)",
    "CREATE INDEX IF NOT EXISTS idx_tech_shifts_tech ON technician_shifts(technician_id)",
    "CREATE INDEX IF NOT EXISTS idx_tech_shifts_date ON technician_shifts(shift_date)",
    "CREATE INDEX IF NOT EXISTS idx_tech_shifts_wc ON technician_shifts(work_center_id)",

    # Capacity Planning
    "CREATE INDEX IF NOT EXISTS idx_cap_req_wo ON capacity_requirements(work_order_id)",
    "CREATE INDEX IF NOT EXISTS idx_cap_req_wc ON capacity_requirements(work_center_id)",
    "CREATE INDEX IF NOT EXISTS idx_cap_req_date ON capacity_requirements(required_date)",
    "CREATE INDEX IF NOT EXISTS idx_cap_views_wc ON capacity_planning_views(work_center_id)",
    "CREATE INDEX IF NOT EXISTS idx_cap_views_date ON capacity_planning_views(planning_date)",

    # Skills
    "CREATE INDEX IF NOT EXISTS idx_skill_catalog_code ON skill_catalog(skill_code)",
    "CREATE INDEX IF NOT EXISTS idx_skill_catalog_category ON skill_catalog(skill_category)",
    "CREATE INDEX IF NOT EXISTS idx_wo_skill_req_wo ON work_order_skill_requirements(work_order_id)",
    "CREATE INDEX IF NOT EXISTS idx_wo_skill_req_skill ON work_order_skill_requirements(skill_id)",
    "CREATE INDEX IF NOT EXISTS idx_tech_skill_tech ON technician_skill_levels(technician_id)",
    "CREATE INDEX IF NOT EXISTS idx_tech_skill_skill ON technician_skill_levels(skill_id)",

    # Costing & Settlement
    "CREATE INDEX IF NOT EXISTS idx_cost_elements_code ON maintenance_cost_elements(element_code)",
    "CREATE INDEX IF NOT EXISTS idx_cost_elements_category ON maintenance_cost_elements(cost_category)",
    "CREATE INDEX IF NOT EXISTS idx_wocp_wo ON work_order_cost_plan(work_order_id)",
    "CREATE INDEX IF NOT EXISTS idx_wip_wo ON maintenance_wip(work_order_id)",
    "CREATE INDEX IF NOT EXISTS idx_wip_period ON maintenance_wip(period_id)",
    "CREATE INDEX IF NOT EXISTS idx_settlement_rules_code ON settlement_rules(rule_code)",
    "CREATE INDEX IF NOT EXISTS idx_settlements_wo ON maintenance_settlements(work_order_id)",
    "CREATE INDEX IF NOT EXISTS idx_settlements_date ON maintenance_settlements(settlement_date)",

    # Service Management
    "CREATE INDEX IF NOT EXISTS idx_svc_agreements_number ON service_agreements(agreement_number)",
    "CREATE INDEX IF NOT EXISTS idx_svc_agreements_customer ON service_agreements(customer_id)",
    "CREATE INDEX IF NOT EXISTS idx_svc_agreements_status ON service_agreements(status)",
    "CREATE INDEX IF NOT EXISTS idx_agreement_lines_agreement ON agreement_line_items(agreement_id)",
    "CREATE INDEX IF NOT EXISTS idx_agreement_lines_equipment ON agreement_line_items(equipment_id)",
    "CREATE INDEX IF NOT EXISTS idx_warranty_records_equipment ON warranty_records(equipment_id)",
    "CREATE INDEX IF NOT EXISTS idx_warranty_claims_warranty ON warranty_claims(warranty_id)",
    "CREATE INDEX IF NOT EXISTS idx_warranty_claims_wo ON warranty_claims(work_order_id)",

    # Notifications & Problem Management
    "CREATE INDEX IF NOT EXISTS idx_maint_notif_number ON maintenance_notifications(notification_number)",
    "CREATE INDEX IF NOT EXISTS idx_maint_notif_equipment ON maintenance_notifications(equipment_id)",
    "CREATE INDEX IF NOT EXISTS idx_maint_notif_loc ON maintenance_notifications(functional_location_id)",
    "CREATE INDEX IF NOT EXISTS idx_maint_notif_status ON maintenance_notifications(status)",
    "CREATE INDEX IF NOT EXISTS idx_maint_notif_priority ON maintenance_notifications(priority)",
    "CREATE INDEX IF NOT EXISTS idx_notif_items_notification ON notification_items(notification_id)",
    "CREATE INDEX IF NOT EXISTS idx_notif_causes_notification ON notification_causes(notification_id)",
    "CREATE INDEX IF NOT EXISTS idx_problem_records_number ON problem_records(problem_number)",
    "CREATE INDEX IF NOT EXISTS idx_problem_records_status ON problem_records(status)",

    # IoT & Predictive Maintenance
    "CREATE INDEX IF NOT EXISTS idx_iot_devices_code ON iot_devices(device_code)",
    "CREATE INDEX IF NOT EXISTS idx_iot_devices_equipment ON iot_devices(equipment_id)",
    "CREATE INDEX IF NOT EXISTS idx_iot_streams_device ON iot_data_streams(device_id)",
    "CREATE INDEX IF NOT EXISTS idx_iot_data_points_stream ON iot_data_points(stream_id)",
    "CREATE INDEX IF NOT EXISTS idx_iot_data_points_timestamp ON iot_data_points(timestamp)",
    "CREATE INDEX IF NOT EXISTS idx_iot_alert_rules_stream ON iot_alert_rules(stream_id)",
    "CREATE INDEX IF NOT EXISTS idx_iot_alerts_rule ON iot_alerts(rule_id)",
    "CREATE INDEX IF NOT EXISTS idx_iot_alerts_triggered ON iot_alerts(triggered_at)",
    "CREATE INDEX IF NOT EXISTS idx_iot_alerts_status ON iot_alerts(status)",

    # Security & Compliance
    "CREATE INDEX IF NOT EXISTS idx_field_auth_role ON maintenance_field_authorization(role_id)",
    "CREATE INDEX IF NOT EXISTS idx_field_auth_object ON maintenance_field_authorization(object_type)",
    "CREATE INDEX IF NOT EXISTS idx_data_scopes_user ON maintenance_data_scopes(user_id)",
]

# Extended work order status constants (SAP-style)
MAINTENANCE_WORK_ORDER_STATUSES = [
    'Draft',           # ایجاد اولیه
    'Open',            # باز
    'Approved',        # تأیید شده
    'Assigned',        # تخصیص شده
    'Released',        # منتشر شده (آزاد برای اجرا)
    'Released Hold',   # منتشر شده اما متوقف
    'Tech Prep',       # آماده‌سازی فنی
    'In Progress',     # در حال اجرا
    'On Hold',         # متوقف
    'On Hold Parts',   # منتظر قطعات
    'On Hold Vendor',  # منتظر تأمین‌کننده
    'On Hold Engineering', # منتظر مهندسی
    'Tech Complete',   # تکمیل فنی (TECO)
    'Doc Complete',    # تکمیل مستندات
    'Close Prep',      # آماده برای بستن
    'Completed',       # تکمیل شده
    'Verified',        # تأیید شده
    'Closed',          # بسته شده
    'Canceled',        # لغو شده
    'Rejected'         # رد شده
]

# Extended work order statuses for SAP PM compatibility
EXTENDED_WORK_ORDER_STATUSES = {
    'CREATED': 'Created',
    'RELEASED': 'Released',
    'REL_HOLD': 'Released Hold',
    'TECH_PREP': 'Technical Preparation',
    'IN_PROCESS': 'In Process',
    'ON_HOLD': 'On Hold',
    'ON_HOLD_PARTS': 'On Hold - Parts',
    'ON_HOLD_VENDOR': 'On Hold - Vendor',
    'ON_HOLD_ENG': 'On Hold - Engineering',
    'TECH_COMPLETE': 'Technically Complete (TECO)',
    'DOC_COMPLETE': 'Documentation Complete',
    'CLOSE_PREP': 'Close Preparation',
    'COMPLETED': 'Completed',
    'VERIFIED': 'Verified',
    'CLOSED': 'Closed',
    'CANCELLED': 'Cancelled',
    'REJECTED': 'Rejected'
}

# Work Order Types
WORK_ORDER_TYPES = [
    'Preventive',      # نگهداری پیشگیرانه
    'Corrective',      # نگهداری اصلاحی
    'Emergency',       # اضطراری
    'Inspection',      # بازرسی
    'Calibration',     # کالیبراسیون
    'Installation',    # نصب
    'Breakdown',       # خرابی
    'Project',         # پروژه
    'Shutdown',        # توقف/تعمیرات اساسی
    'Condition-Based', # مبتنی بر شرایط
    'Time-Based',      # مبتنی بر زمان
    'Counter-Based'    # مبتنی بر شمارنده
]

# Maintenance Strategy Types
MAINTENANCE_STRATEGY_TYPES = [
    'TIME-BASED',      # مبتنی بر زمان (تقویمی)
    'COUNTER-BASED',   # مبتنی بر شمارنده
    'CONDITION-BASED' # مبتنی بر شرایط
]

# Counter Types
COUNTER_TYPES = [
    'OPERATING_HOURS',     # ساعت کارکرد
    'PRODUCTION_QTY',      # تعداد تولید
    'CYCLE_COUNT',        # تعداد سیکل
    'DISTANCE',            # مسافت
    'CUSTOM'              # سفارشی
]

# Condition Indicator Types
CONDITION_INDICATOR_TYPES = [
    'VIBRATION',       # ارتعاش
    'TEMPERATURE',     # دما
    'PRESSURE',        # فشار
    'FLOW',            # جریان
    'LEVEL',           # سطح
    'CURRENT',         # جریان الکتریکی
    'VOLTAGE',         # ولتاژ
    'HUMIDITY',        # رطوبت
    'CUSTOM'           # سفارشی
]

# Notification Types (SAP-style)
NOTIFICATION_TYPES = [
    'MALFUNCTION',         # خرابی/اختلال
    'MAINTENANCE_REQUEST', # درخواست نگهداری
    'DAMAGE',              # آسیب/خرابی
    'ACTIVITY',            # فعالیت
    'INFORMATION',         # اطلاعات
    'WARNING'              # هشدار
]

# Confirmation Types
CONFIRMATION_TYPES = [
    'PRELIMINARY',     # مقدماتی
    'FINAL',           # نهایی
    'TECH_COMPLETE',   # تکمیل فنی
    'PARTIAL'          # جزئی
]

# Settlement Target Types
SETTLEMENT_TARGET_TYPES = [
    'ASSET',           # دارایی
    'COST_CENTER',     # مرکز هزینه
    'PROJECT',         # پروژه
    'ORDER',           # سفارش
    'SALES_ORDER'      # سفارش فروش
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
# ENHANCED EAM/PM HELPER FUNCTIONS
# =============================================================================

def get_next_functional_location_code() -> str:
    """Generate the next functional location code."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM functional_locations")
        result = cursor.fetchone()
        seq = (result['cnt'] if result else 0) + 1
        return f"FLOC-{seq:05d}"
    finally:
        conn.close()


def get_functional_location_hierarchy(location_id: int) -> List[Dict]:
    """Get the full hierarchy path for a functional location."""
    conn = get_db()
    try:
        hierarchy = []
        current_id = location_id
        while current_id:
            loc = conn.execute(
                "SELECT id, location_code, name, parent_location_id FROM functional_locations WHERE id = ?",
                (current_id,)
            ).fetchone()
            if loc:
                hierarchy.insert(0, dict(loc))
                current_id = loc['parent_location_id']
            else:
                break
        return hierarchy
    finally:
        conn.close()


def get_next_bom_code() -> str:
    """Generate the next BOM code."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM equipment_boms")
        result = cursor.fetchone()
        seq = (result['cnt'] if result else 0) + 1
        return f"BOM-{datetime.now().strftime('%Y%m')}-{seq:04d}"
    finally:
        conn.close()


def get_bom_explosion(bom_id: int) -> List[Dict]:
    """Get multi-level BOM explosion for an equipment."""
    conn = get_db()
    try:
        items = conn.execute("""
            SELECT ebi.*, ebi.part_name, ebi.quantity,
                   ii.item_code, ii.description as item_description
            FROM equipment_bom_items ebi
            LEFT JOIN inventory_items ii ON ebi.material_id = ii.id
            WHERE ebi.bom_id = ?
            ORDER BY ebi.item_sequence
        """, (bom_id,)).fetchall()
        return [dict(row) for row in items]
    finally:
        conn.close()


def get_next_work_center_code() -> str:
    """Generate the next work center code."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM work_centers")
        result = cursor.fetchone()
        seq = (result['cnt'] if result else 0) + 1
        return f"WC-{seq:04d}"
    finally:
        conn.close()


def get_work_center_capacity_summary(work_center_id: int, start_date: str, end_date: str) -> List[Dict]:
    """Get capacity summary for a work center in date range."""
    conn = get_db()
    try:
        query = """
            SELECT work_date, available_hours, booked_hours, overtime_hours,
                   (available_hours - booked_hours) as free_hours,
                   ROUND((booked_hours / available_hours) * 100, 2) as utilization_pct
            FROM work_center_capacity
            WHERE work_center_id = ? AND work_date BETWEEN ? AND ?
            ORDER BY work_date
        """
        return [dict(row) for row in conn.execute(query, (work_center_id, start_date, end_date)).fetchall()]
    finally:
        conn.close()


def get_work_order_operations(work_order_id: int) -> List[Dict]:
    """Get all operations for a work order."""
    conn = get_db()
    try:
        query = """
            SELECT woo.*, wc.work_center_code, wc.work_center_name,
                   wco.operation_code, wco.description as op_code_desc
            FROM work_order_operations woo
            LEFT JOIN work_centers wc ON woo.work_center_id = wc.id
            LEFT JOIN work_order_operation_codes wco ON woo.operation_id = wco.id
            WHERE woo.work_order_id = ?
            ORDER BY woo.operation_sequence
        """
        return [dict(row) for row in conn.execute(query, (work_order_id,)).fetchall()]
    finally:
        conn.close()


def get_work_order_components(work_order_id: int) -> List[Dict]:
    """Get all components/materials for a work order."""
    conn = get_db()
    try:
        query = """
            SELECT woc.*, ii.item_code, ii.description as material_desc,
                   wwh.warehouse_name, wwh.location as storage_location_name
            FROM work_order_components woc
            LEFT JOIN inventory_items ii ON woc.material_id = ii.id
            LEFT JOIN wms_warehouses wwh ON woc.warehouse_id = wwh.id
            WHERE woc.work_order_id = ?
            ORDER BY woc.requirement_date
        """
        return [dict(row) for row in conn.execute(query, (work_order_id,)).fetchall()]
    finally:
        conn.close()


def get_work_order_cost_summary(work_order_id: int) -> Dict[str, Any]:
    """Get cost summary for a work order including plan vs actual."""
    conn = get_db()
    try:
        query = """
            SELECT
                SUM(wocp.planned_total_cost) as total_planned_cost,
                SUM(wocp.actual_total_cost) as total_actual_cost,
                SUM(wocp.planned_hours) as total_planned_hours,
                SUM(wocp.actual_hours) as total_actual_hours,
                SUM(wocp.actual_total_cost - wocp.planned_total_cost) as cost_variance,
                SUM(wocp.actual_hours - wocp.planned_hours) as hours_variance
            FROM work_order_cost_plan wocp
            WHERE wocp.work_order_id = ?
        """
        result = conn.execute(query, (work_order_id,)).fetchone()
        return dict(result) if result else {}
    finally:
        conn.close()


def get_next_counter_code() -> str:
    """Generate the next maintenance counter code."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM maintenance_counters")
        result = cursor.fetchone()
        seq = (result['cnt'] if result else 0) + 1
        return f"CNTR-{seq:05d}"
    finally:
        conn.close()


def get_next_indicator_code() -> str:
    """Generate the next condition indicator code."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM condition_indicators")
        result = cursor.fetchone()
        seq = (result['cnt'] if result else 0) + 1
        return f"IND-{seq:05d}"
    finally:
        conn.close()


def get_equipment_condition_status(equipment_id: int) -> Dict[str, Any]:
    """Get overall condition status for equipment based on indicators."""
    conn = get_db()
    try:
        query = """
            SELECT
                COUNT(DISTINCT ci.id) as total_indicators,
                SUM(CASE WHEN cr.status = 'NORMAL' THEN 1 ELSE 0 END) as normal_count,
                SUM(CASE WHEN cr.status = 'WARNING' THEN 1 ELSE 0 END) as warning_count,
                SUM(CASE WHEN cr.status = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count
            FROM condition_indicators ci
            LEFT JOIN (
                SELECT indicator_id, status,
                       ROW_NUMBER() OVER (PARTITION BY indicator_id ORDER BY reading_timestamp DESC) as rn
                FROM condition_readings
            ) cr ON ci.id = cr.indicator_id AND cr.rn = 1
            WHERE ci.equipment_id = ? AND ci.is_active = 1
        """
        result = conn.execute(query, (equipment_id,)).fetchone()
        return dict(result) if result else {}
    finally:
        conn.close()


def get_next_skill_code() -> str:
    """Generate the next skill code."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM skill_catalog")
        result = cursor.fetchone()
        seq = (result['cnt'] if result else 0) + 1
        return f"SKILL-{seq:04d}"
    finally:
        conn.close()


def get_technician_skill_match(work_order_id: int, technician_id: int) -> Dict[str, Any]:
    """Check if technician has required skills for work order."""
    conn = get_db()
    try:
        required_skills = conn.execute("""
            SELECT skill_id, skill_level_required
            FROM work_order_skill_requirements
            WHERE work_order_id = ?
        """, (work_order_id,)).fetchall()

        tech_skills = conn.execute("""
            SELECT skill_id, skill_level
            FROM technician_skill_levels
            WHERE technician_id = ?
        """, (technician_id,)).fetchall()

        tech_skill_map = {ts['skill_id']: ts['skill_level'] for ts in tech_skills}

        matched = 0
        missing = []
        for req in required_skills:
            if req['skill_id'] in tech_skill_map:
                matched += 1
            else:
                missing.append(req['skill_id'])

        return {
            'total_required': len(required_skills),
            'matched': matched,
            'match_percentage': (matched / len(required_skills) * 100) if required_skills else 100,
            'missing_skills': missing
        }
    finally:
        conn.close()


def get_next_agreement_number() -> str:
    """Generate the next service agreement number."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM service_agreements")
        result = cursor.fetchone()
        seq = (result['cnt'] if result else 0) + 1
        return f"SVC-{datetime.now().strftime('%Y')}-{seq:05d}"
    finally:
        conn.close()


def get_next_notification_number() -> str:
    """Generate the next maintenance notification number."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM maintenance_notifications")
        result = cursor.fetchone()
        seq = (result['cnt'] if result else 0) + 1
        return f"NOTIF-{datetime.now().strftime('%Y%m')}-{seq:05d}"
    finally:
        conn.close()


def get_next_problem_number() -> str:
    """Generate the next problem record number."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM problem_records")
        result = cursor.fetchone()
        seq = (result['cnt'] if result else 0) + 1
        return f"PRB-{datetime.now().strftime('%Y')}-{seq:05d}"
    finally:
        conn.close()


def get_next_claim_number() -> str:
    """Generate the next warranty claim number."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM warranty_claims")
        result = cursor.fetchone()
        seq = (result['cnt'] if result else 0) + 1
        return f"WC-{datetime.now().strftime('%Y%m')}-{seq:04d}"
    finally:
        conn.close()


def get_next_iot_device_code() -> str:
    """Generate the next IoT device code."""
    conn = get_db()
    try:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM iot_devices")
        result = cursor.fetchone()
        seq = (result['cnt'] if result else 0) + 1
        return f"IOT-{seq:06d}"
    finally:
        conn.close()


def get_iot_device_telemetry(device_id: int, stream_id: int = None, limit: int = 100) -> List[Dict]:
    """Get recent telemetry data for an IoT device."""
    conn = get_db()
    try:
        query = """
            SELECT idp.*, ids.stream_name, ids.data_type, ids.unit
            FROM iot_data_points idp
            JOIN iot_data_streams ids ON idp.stream_id = ids.id
            WHERE ids.device_id = ?
        """
        params = [device_id]

        if stream_id:
            query += " AND idp.stream_id = ?"
            params.append(stream_id)

        query += " ORDER BY idp.timestamp DESC LIMIT ?"
        params.append(limit)

        return [dict(row) for row in conn.execute(query, params).fetchall()]
    finally:
        conn.close()


def get_mtbf_mttr(equipment_id: int = None, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
    """Calculate MTBF and MTTR for equipment."""
    conn = get_db()
    try:
        query = """
            SELECT
                COUNT(DISTINCT md.downs
                SUM(md.total_hours) as total_downtime,
                SUM(CASE WHEN md.downtime_end IS NOT NULL THEN 1 ELSE 0 END) as repair_count,
                AVG(md.total_hours) as mttr
            FROM maintenance_downtime_logs md
            WHERE 1=1
        """
        params = []

        if equipment_id:
            query += " AND md.asset_id = ?"
            params.append(equipment_id)
        if start_date:
            query += " AND md.downtime_start >= ?"
            params.append(start_date)
        if end_date:
            query += " AND md.downtime_end <= ?"
            params.append(end_date)

        result = conn.execute(query, params).fetchone()

        total_wo = conn.execute("""
            SELECT COUNT(*) as total FROM maintenance_work_orders
            WHERE completed_date IS NOT NULL
        """).fetchone()

        mtbf = 0
        if result['total_downtime'] and total_wo['total']:
            mtbf = result['total_downtime'] / total_wo['total']

        return {
            'mtbf_hours': round(mtbf, 2),
            'mttr_hours': round(result['mttr'] or 0, 2),
            'total_downtime_hours': round(result['total_downtime'] or 0, 2),
            'repair_count': result['repair_count'] or 0
        }
    finally:
        conn.close()


def get_capacity_planning_data(work_center_id: int, start_date: str, end_date: str) -> List[Dict]:
    """Get capacity planning data for work center."""
    conn = get_db()
    try:
        query = """
            SELECT
                wcc.work_date,
                wcc.available_hours,
                wcc.booked_hours,
                wcc.overtime_hours,
                (wcc.available_hours - wcc.booked_hours) as free_hours,
                COUNT(DISTINCT cr.work_order_id) as scheduled_wo_count
            FROM work_center_capacity wcc
            LEFT JOIN capacity_requirements cr ON wcc.work_center_id = cr.work_center_id
                AND cr.required_date = wcc.work_date AND cr.status != 'COMPLETED'
            WHERE wcc.work_center_id = ? AND wcc.work_date BETWEEN ? AND ?
            GROUP BY wcc.work_date
            ORDER BY wcc.work_date
        """
        return [dict(row) for row in conn.execute(query, (work_center_id, start_date, end_date)).fetchall()]
    finally:
        conn.close()


def get_wip_summary(period_id: int) -> Dict[str, Any]:
    """Get WIP summary for a financial period."""
    conn = get_db()
    try:
        query = """
            SELECT
                SUM(opening_value) as total_opening,
                SUM(additions_value) as total_additions,
                SUM(closing_value) as total_closing,
                SUM(settled_value) as total_settled,
                SUM(closing_value - settled_value) as total_wip_value
            FROM maintenance_wip
            WHERE period_id = ?
        """
        result = conn.execute(query, (period_id,)).fetchone()
        return dict(result) if result else {}
    finally:
        conn.close()


# =============================================================================
# RUN INITIALIZATION
# =============================================================================

if __name__ == '__main__' or True:
    init_maintenance_tables()
