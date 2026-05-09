"""
Quality Management Module Database Models
=========================================
Enterprise-grade Quality Management for the MMDx platform.

This module provides comprehensive data models for:
- Quality Inspections (Incoming, In-Process, Outgoing, Warehouse, Supplier, Customer)
- Non-Conformance Records (NCR)
- CAPA (Corrective/Preventive Actions)
- Audit Management (Programs, Checklists, Findings)
- Quality Settings and Configuration
- Quality Dashboard Analytics

Tables:
- quality_inspection_types: Master list of inspection types
- quality_inspection_templates: Reusable inspection checklists/templates
- quality_inspection_plans: Planned inspection schedules
- quality_inspections: Actual inspection records
- quality_inspection_lines: Line-by-line checklist results
- quality_inspection_findings: Defects/issues found during inspection
- quality_defect_categories: Classification of defects
- quality_non_conformances: NCR records
- quality_containment_actions: Immediate containment actions
- quality_capa_categories: CAPA classification
- quality_capa_records: CAPA master records
- quality_capa_actions: Individual CAPA action items
- quality_root_cause_categories: Root cause classification
- quality_effectiveness_reviews: CAPA effectiveness verification
- quality_audit_programs: Annual/scheduled audit programs
- quality_audit_plans: Individual audit plans
- quality_audit_checklist_templates: Reusable audit checklists
- quality_audit_checklists: Completed audit checklists
- quality_audit_findings: Audit findings/non-conformities
- quality_settings: Quality module configuration
- quality_approval_records: Approval workflow records
- quality_audit_log: Audit trail for all quality changes

Usage:
    from quality_models import (
        initialize_quality_tables,
        get_quality_dashboard_stats,
        create_inspection, get_inspections,
        create_ncr, get_ncrs,
        create_capa, get_capas,
        create_audit, get_audits,
        # ... etc
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
# QUALITY MANAGEMENT TABLE DEFINITIONS
# =============================================================================

QUALITY_TABLES = [
    # -------------------------------------------------------------------------
    # 1. Quality Inspection Types - Master list of inspection categories
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_inspection_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        category TEXT DEFAULT 'GENERAL',
        applicable_source TEXT DEFAULT 'ALL',
        applicable_entities TEXT,
        is_active INTEGER DEFAULT 1,
        requires_checklist INTEGER DEFAULT 1,
        min_sample_size INTEGER DEFAULT 1,
        acceptance_criteria TEXT,
        result_type TEXT DEFAULT 'PASS_FAIL',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 2. Quality Inspection Templates - Reusable checklist templates
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_inspection_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_code TEXT UNIQUE NOT NULL,
        template_name TEXT NOT NULL,
        inspection_type_id INTEGER,
        version TEXT DEFAULT '1.0',
        description TEXT,
        company_id INTEGER,
        branch_id INTEGER,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (inspection_type_id) REFERENCES quality_inspection_types(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 3. Quality Inspection Template Lines - Checklist items
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_inspection_template_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_id INTEGER NOT NULL,
        line_number INTEGER NOT NULL,
        criterion TEXT NOT NULL,
        description TEXT,
        inspection_method TEXT,
        acceptance_criteria TEXT,
        result_type TEXT DEFAULT 'PASS_FAIL',
        is_mandatory INTEGER DEFAULT 1,
        weight REAL DEFAULT 1.0,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (template_id) REFERENCES quality_inspection_templates(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 4. Quality Inspection Plans - Scheduled/planned inspections
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_inspection_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_number TEXT UNIQUE NOT NULL,
        plan_name TEXT NOT NULL,
        inspection_type_id INTEGER,
        template_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        warehouse_id INTEGER,
        department TEXT,
        source_type TEXT,
        item_category TEXT,
        supplier_id INTEGER,
        frequency TEXT DEFAULT 'ONCE',
        planned_date DATE,
        planned_end_date DATE,
        inspector_id INTEGER,
        team_members TEXT,
        estimated_duration_hours REAL,
        status TEXT DEFAULT 'PLANNED',
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (inspection_type_id) REFERENCES quality_inspection_types(id) ON DELETE SET NULL,
        FOREIGN KEY (template_id) REFERENCES quality_inspection_templates(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 5. Quality Inspections - Actual inspection records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inspection_number TEXT UNIQUE NOT NULL,
        inspection_type_id INTEGER,
        template_id INTEGER,
        plan_id INTEGER,
        source_type TEXT,
        source_reference TEXT,
        source_reference_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        warehouse_id INTEGER,
        location_id INTEGER,
        department TEXT,
        supplier_id INTEGER,
        customer_id INTEGER,
        item_id INTEGER,
        item_code TEXT,
        item_name TEXT,
        lot_number TEXT,
        serial_number TEXT,
        batch_number TEXT,
        quantity_received REAL DEFAULT 0,
        quantity_inspected REAL DEFAULT 0,
        sample_size INTEGER DEFAULT 0,
        quantity_accepted REAL DEFAULT 0,
        quantity_rejected REAL DEFAULT 0,
        quantity_held REAL DEFAULT 0,
        quantity_conditionally_accepted REAL DEFAULT 0,
        inspection_date DATE,
        inspection_time TEXT,
        inspector_id INTEGER,
        inspector_name TEXT,
        team_members TEXT,
        result TEXT,
        status TEXT DEFAULT 'IN_PROGRESS',
        disposition TEXT,
        disposition_notes TEXT,
        reinspection_required INTEGER DEFAULT 0,
        reinspection_of_id INTEGER,
        ncr_id INTEGER,
        notes TEXT,
        attachments TEXT,
        completed_at DATETIME,
        completed_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        FOREIGN KEY (inspection_type_id) REFERENCES quality_inspection_types(id) ON DELETE SET NULL,
        FOREIGN KEY (template_id) REFERENCES quality_inspection_templates(id) ON DELETE SET NULL,
        FOREIGN KEY (reinspection_of_id) REFERENCES quality_inspections(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 6. Quality Inspection Lines - Line-by-line checklist results
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_inspection_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inspection_id INTEGER NOT NULL,
        template_line_id INTEGER,
        line_number INTEGER NOT NULL,
        criterion TEXT NOT NULL,
        description TEXT,
        inspection_method TEXT,
        acceptance_criteria TEXT,
        result_type TEXT DEFAULT 'PASS_FAIL',
        result TEXT,
        measurement_value REAL,
        measurement_unit TEXT,
        is_conforming INTEGER,
        findings TEXT,
        severity TEXT,
        is_mandatory INTEGER DEFAULT 1,
        weight REAL DEFAULT 1.0,
        notes TEXT,
        attachments TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (inspection_id) REFERENCES quality_inspections(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 7. Quality Inspection Findings - Defects found during inspection
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_inspection_findings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        inspection_id INTEGER NOT NULL,
        line_id INTEGER,
        defect_code TEXT,
        defect_category TEXT,
        defect_type TEXT,
        severity TEXT,
        description TEXT,
        affected_quantity REAL DEFAULT 0,
        lot_number TEXT,
        location_in_item TEXT,
        photos TEXT,
        is_rejected INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (inspection_id) REFERENCES quality_inspections(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 8. Quality Defect Categories - Classification of defects
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_defect_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        severity_levels TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 9. Quality Non-Conformances - NCR records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_non_conformances (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ncr_number TEXT UNIQUE NOT NULL,
        source_type TEXT,
        source_reference TEXT,
        source_reference_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        warehouse_id INTEGER,
        department TEXT,
        location_id INTEGER,
        item_id INTEGER,
        item_code TEXT,
        item_name TEXT,
        lot_number TEXT,
        batch_number TEXT,
        supplier_id INTEGER,
        supplier_name TEXT,
        customer_id INTEGER,
        customer_name TEXT,
        ncr_category TEXT,
        defect_category_id INTEGER,
        defect_type TEXT,
        severity TEXT,
        impact TEXT,
        priority TEXT DEFAULT 'MEDIUM',
        description TEXT,
        detected_by INTEGER,
        detected_by_name TEXT,
        detected_date DATE,
        owner_id INTEGER,
        owner_name TEXT,
        assigned_to_id INTEGER,
        assigned_to_name TEXT,
        status TEXT DEFAULT 'OPEN',
        containment_required INTEGER DEFAULT 0,
        containment_status TEXT,
        root_cause_required INTEGER DEFAULT 0,
        root_cause_status TEXT,
        capa_required INTEGER DEFAULT 0,
        capa_id INTEGER,
        immediate_action TEXT,
        disposition TEXT,
        disposition_approved_by INTEGER,
        disposition_approved_at DATETIME,
        hold_quantity REAL DEFAULT 0,
        return_quantity REAL DEFAULT 0,
        rework_quantity REAL DEFAULT 0,
        scrap_quantity REAL DEFAULT 0,
        use_as_is_quantity REAL DEFAULT 0,
        financial_impact REAL DEFAULT 0,
        target_close_date DATE,
        actual_close_date DATE,
        closure_verified_by INTEGER,
        closure_verified_at DATETIME,
        closure_notes TEXT,
        reopen_count INTEGER DEFAULT 0,
        reopen_reason TEXT,
        notes TEXT,
        attachments TEXT,
        rejection_reason TEXT,
        rejected_by INTEGER,
        rejected_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        closed_by INTEGER,
        FOREIGN KEY (defect_category_id) REFERENCES quality_defect_categories(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 10. Quality Containment Actions - Immediate containment
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_containment_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ncr_id INTEGER NOT NULL,
        action_number TEXT UNIQUE NOT NULL,
        action_type TEXT NOT NULL,
        description TEXT NOT NULL,
        responsible_id INTEGER,
        responsible_name TEXT,
        due_date DATE,
        completed_date DATE,
        status TEXT DEFAULT 'PENDING',
        evidence TEXT,
        notes TEXT,
        verified_by INTEGER,
        verified_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        FOREIGN KEY (ncr_id) REFERENCES quality_non_conformances(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 11. Quality CAPA Categories - CAPA classification
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_capa_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        type TEXT DEFAULT 'BOTH',
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 12. Quality CAPA Records - CAPA master records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_capa_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        capa_number TEXT UNIQUE NOT NULL,
        triggering_source TEXT NOT NULL,
        source_type TEXT,
        source_reference TEXT,
        source_reference_id INTEGER,
        ncr_id INTEGER,
        audit_finding_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        department TEXT,
        warehouse_id INTEGER,
        category_id INTEGER,
        capa_type TEXT DEFAULT 'CORRECTIVE',
        severity TEXT DEFAULT 'MEDIUM',
        priority TEXT DEFAULT 'MEDIUM',
        title TEXT NOT NULL,
        description TEXT,
        root_cause_summary TEXT,
        root_cause_category_id INTEGER,
        root_cause_description TEXT,
        contributing_factors TEXT,
        is_recurring_issue INTEGER DEFAULT 0,
        previous_capa_id INTEGER,
        owner_id INTEGER,
        owner_name TEXT,
        approver_id INTEGER,
        approver_name TEXT,
        target_date DATE,
        actual_completion_date DATE,
        status TEXT DEFAULT 'OPEN',
        effectiveness_verification_required INTEGER DEFAULT 1,
        effectiveness_review_status TEXT,
        effectiveness_review_date DATE,
        effectiveness_reviewer_id INTEGER,
        effectiveness_result TEXT,
        effectiveness_notes TEXT,
        effectiveness_evidence TEXT,
        closed_by INTEGER,
        closed_at DATETIME,
        closure_notes TEXT,
        reopen_count INTEGER DEFAULT 0,
        reopen_reason TEXT,
        reopened_by INTEGER,
        reopened_at DATETIME,
        notes TEXT,
        attachments TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        approved_by INTEGER,
        approved_at DATETIME,
        FOREIGN KEY (ncr_id) REFERENCES quality_non_conformances(id) ON DELETE SET NULL,
        FOREIGN KEY (root_cause_category_id) REFERENCES quality_root_cause_categories(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 13. Quality CAPA Actions - Individual action items within CAPA
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_capa_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        capa_id INTEGER NOT NULL,
        action_number TEXT UNIQUE NOT NULL,
        action_description TEXT NOT NULL,
        action_type TEXT,
        responsible_id INTEGER,
        responsible_name TEXT,
        due_date DATE,
        completed_date DATE,
        status TEXT DEFAULT 'PENDING',
        evidence TEXT,
        completion_notes TEXT,
        follow_up_date DATE,
        follow_up_required INTEGER DEFAULT 0,
        verified_by INTEGER,
        verified_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        FOREIGN KEY (capa_id) REFERENCES quality_capa_records(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 14. Quality Root Cause Categories - Root cause classification
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_root_cause_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        description TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 15. Quality Effectiveness Reviews - CAPA effectiveness verification
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_effectiveness_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        capa_id INTEGER NOT NULL,
        review_number TEXT UNIQUE NOT NULL,
        review_date DATE NOT NULL,
        reviewer_id INTEGER,
        reviewer_name TEXT,
        effectiveness_result TEXT NOT NULL,
        result_meets_criteria INTEGER,
        evidence TEXT,
        findings TEXT,
        recurrence_observed INTEGER DEFAULT 0,
        recurrence_details TEXT,
        further_action_required INTEGER DEFAULT 0,
        further_action_description TEXT,
        next_review_date DATE,
        status TEXT DEFAULT 'PENDING',
        notes TEXT,
        attachments TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        FOREIGN KEY (capa_id) REFERENCES quality_capa_records(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 16. Quality Audit Programs - Annual/scheduled audit programs
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_audit_programs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        program_number TEXT UNIQUE NOT NULL,
        program_name TEXT NOT NULL,
        audit_type TEXT NOT NULL,
        scope TEXT,
        objectives TEXT,
        standard_reference TEXT,
        company_id INTEGER,
        branch_id INTEGER,
        warehouse_id INTEGER,
        department TEXT,
        audit_period_start DATE,
        audit_period_end DATE,
        lead_auditor_id INTEGER,
        lead_auditor_name TEXT,
        team_members TEXT,
        status TEXT DEFAULT 'ACTIVE',
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER
    )""",

    # -------------------------------------------------------------------------
    # 17. Quality Audit Plans - Individual audit plans
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_audit_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_number TEXT UNIQUE NOT NULL,
        program_id INTEGER,
        audit_type TEXT NOT NULL,
        scope TEXT,
        objectives TEXT,
        company_id INTEGER,
        branch_id INTEGER,
        warehouse_id INTEGER,
        site_location TEXT,
        department TEXT,
        process_area TEXT,
        scheduled_start_date DATE,
        scheduled_end_date DATE,
        actual_start_date DATE,
        actual_end_date DATE,
        lead_auditor_id INTEGER,
        lead_auditor_name TEXT,
        auditor_ids TEXT,
        auditor_names TEXT,
        auditee_id INTEGER,
        auditee_name TEXT,
        auditee_department TEXT,
        checklist_template_id INTEGER,
        status TEXT DEFAULT 'PLANNED',
        preparation_status TEXT,
        document_review_notes TEXT,
        notification_sent INTEGER DEFAULT 0,
        opening_meeting_held INTEGER DEFAULT 0,
        closing_meeting_held INTEGER DEFAULT 0,
        findings_count INTEGER DEFAULT 0,
        major_findings_count INTEGER DEFAULT 0,
        minor_findings_count INTEGER DEFAULT 0,
        observations_count INTEGER DEFAULT 0,
        notes TEXT,
        attachments TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        FOREIGN KEY (program_id) REFERENCES quality_audit_programs(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 18. Quality Audit Checklist Templates - Reusable audit checklists
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_audit_checklist_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_code TEXT UNIQUE NOT NULL,
        template_name TEXT NOT NULL,
        audit_type TEXT,
        version TEXT DEFAULT '1.0',
        description TEXT,
        scope TEXT,
        company_id INTEGER,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 19. Quality Audit Checklist Template Lines - Checklist items
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_audit_checklist_template_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_id INTEGER NOT NULL,
        line_number INTEGER NOT NULL,
        clause_reference TEXT,
        requirement TEXT NOT NULL,
        description TEXT,
        checklist_question TEXT,
        evidence_required TEXT,
        result_type TEXT DEFAULT 'CONFORMITY',
        is_mandatory INTEGER DEFAULT 1,
        weight REAL DEFAULT 1.0,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (template_id) REFERENCES quality_audit_checklist_templates(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 20. Quality Audit Checklists - Completed audit checklists
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_audit_checklists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        audit_plan_id INTEGER NOT NULL,
        template_id INTEGER,
        auditor_id INTEGER,
        auditor_name TEXT,
        audit_date DATE,
        area_audited TEXT,
        process_audited TEXT,
        auditor_notes TEXT,
        overall_result TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (audit_plan_id) REFERENCES quality_audit_plans(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 21. Quality Audit Checklist Lines - Line-by-line audit results
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_audit_checklist_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        checklist_id INTEGER NOT NULL,
        template_line_id INTEGER,
        line_number INTEGER NOT NULL,
        clause_reference TEXT,
        requirement TEXT NOT NULL,
        description TEXT,
        checklist_question TEXT,
        result TEXT,
        evidence TEXT,
        findings TEXT,
        non_conformity_id INTEGER,
        is_conforming INTEGER,
        severity TEXT,
        notes TEXT,
        attachments TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (checklist_id) REFERENCES quality_audit_checklists(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 22. Quality Audit Findings - Audit findings/non-conformities
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_audit_findings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        finding_number TEXT UNIQUE NOT NULL,
        audit_plan_id INTEGER,
        checklist_id INTEGER,
        category TEXT DEFAULT 'NON_CONFORMITY',
        severity TEXT DEFAULT 'MINOR',
        clause_reference TEXT,
        requirement TEXT,
        description TEXT NOT NULL,
        evidence TEXT,
        auditee_statement TEXT,
        root_cause TEXT,
        corrective_action TEXT,
        preventive_action TEXT,
        capa_id INTEGER,
        owner_id INTEGER,
        owner_name TEXT,
        due_date DATE,
        actual_close_date DATE,
        status TEXT DEFAULT 'OPEN',
        verified_by INTEGER,
        verified_at DATETIME,
        verification_evidence TEXT,
        notes TEXT,
        attachments TEXT,
        rejected_reason TEXT,
        rejected_by INTEGER,
        rejected_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        FOREIGN KEY (audit_plan_id) REFERENCES quality_audit_plans(id) ON DELETE SET NULL,
        FOREIGN KEY (capa_id) REFERENCES quality_capa_records(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 23. Quality Settings - Module configuration
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT UNIQUE NOT NULL,
        setting_value TEXT,
        category TEXT DEFAULT 'GENERAL',
        description TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 24. Quality Approval Records - Approval workflow
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_approval_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_type TEXT NOT NULL,
        record_id INTEGER NOT NULL,
        record_number TEXT NOT NULL,
        approval_type TEXT NOT NULL,
        step_number INTEGER DEFAULT 1,
        approver_id INTEGER,
        approver_name TEXT,
        status TEXT DEFAULT 'PENDING',
        decision TEXT,
        decision_date DATETIME,
        remarks TEXT,
        rejection_reason TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 25. Quality Audit Log - Complete audit trail
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS quality_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        log_number TEXT UNIQUE NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        entity_type TEXT NOT NULL,
        entity_id INTEGER NOT NULL,
        entity_number TEXT,
        action TEXT NOT NULL,
        field_changed TEXT,
        old_value TEXT,
        new_value TEXT,
        user_id INTEGER,
        user_name TEXT,
        ip_address TEXT,
        notes TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
    )""",
]


# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_quality_tables():
    """Initialize all quality management tables."""
    with get_db() as db:
        for table_sql in QUALITY_TABLES:
            db.execute(table_sql)
        db.commit()
    
    # Seed default configuration data
    _seed_default_quality_config()
    _seed_default_inspection_types()
    _seed_default_defect_categories()
    _seed_default_capa_categories()
    _seed_default_root_cause_categories()


def _seed_default_quality_config():
    """Seed default quality module configuration."""
    defaults = [
        ('QUALITY_AUTO_NCR_ON_FAIL', '1', 'RULES', 'Auto-create NCR when inspection fails'),
        ('QUALITY_AUTO_HOLD_ON_FAIL', '1', 'RULES', 'Auto-hold stock when inspection fails'),
        ('QUALITY_REINSPECTION_REQD', '1', 'RULES', 'Require reinspection after failed inspection'),
        ('QUALITY_REINSPECTION_DAYS', '30', 'RULES', 'Days allowed for reinspection'),
        ('QUALITY_NCR_NUMBERING_PREFIX', 'NCR', 'NUMBERING', 'NCR number prefix'),
        ('QUALITY_INSPECTION_NUMBERING_PREFIX', 'INS', 'NUMBERING', 'Inspection number prefix'),
        ('QUALITY_CAPA_NUMBERING_PREFIX', 'CAPA', 'NUMBERING', 'CAPA number prefix'),
        ('QUALITY_AUDIT_NUMBERING_PREFIX', 'AUD', 'NUMBERING', 'Audit number prefix'),
        ('QUALITY_FINDING_NUMBERING_PREFIX', 'FIND', 'NUMBERING', 'Finding number prefix'),
        ('QUALITY_CONTAINMENT_NUMBERING_PREFIX', 'CA', 'NUMBERING', 'Containment action number prefix'),
        ('QUALITY_DEFAULT_SEVERITY', 'MEDIUM', 'DEFAULTS', 'Default severity for NCRs'),
        ('QUALITY_DEFAULT_PRIORITY', 'MEDIUM', 'DEFAULTS', 'Default priority for NCRs'),
        ('QUALITY_OVERDUE_DAYS_WARNING', '7', 'NOTIFICATIONS', 'Days before due to send warning'),
        ('QUALITY_OVERDUE_DAYS_CRITICAL', '3', 'NOTIFICATIONS', 'Days before due to send critical alert'),
        ('QUALITY_EFFECTIVENESS_REVIEW_DAYS', '90', 'NOTIFICATIONS', 'Days after closure to review effectiveness'),
        ('QUALITY_NCR_AUTO_CLOSE_DAYS', '30', 'RULES', 'Days to auto-close NCR if no activity'),
        ('QUALITY_MIN_INSPECTION_SAMPLE_SIZE', '5', 'RULES', 'Minimum sample size for inspections'),
        ('QUALITY_INSPECTION_RESULT_PASS', 'PASS', 'RESULTS', 'Pass inspection result'),
        ('QUALITY_INSPECTION_RESULT_FAIL', 'FAIL', 'RESULTS', 'Fail inspection result'),
        ('QUALITY_INSPECTION_RESULT_HOLD', 'HOLD', 'RESULTS', 'Hold inspection result'),
        ('QUALITY_INSPECTION_RESULT_COND_PASS', 'CONDITIONAL_PASS', 'RESULTS', 'Conditional pass result'),
        ('QUALITY_INSPECTION_RESULT_REJECT', 'REJECT', 'RESULTS', 'Reject inspection result'),
    ]
    
    for key, value, category, description in defaults:
        try:
            with get_db() as db:
                db.execute("""
                    INSERT OR IGNORE INTO quality_settings (setting_key, setting_value, category, description)
                    VALUES (?, ?, ?, ?)
                """, (key, value, category, description))
                db.commit()
        except:
            pass


def _seed_default_inspection_types():
    """Seed default inspection types."""
    types = [
        ('INC', 'Incoming Inspection', 'Incoming material/received goods inspection', 'INCOMING', 'RECEIPT', 'PASS_FAIL'),
        ('PROC', 'In-Process Inspection', 'Inspection during production/assembly', 'IN_PROCESS', 'PRODUCTION', 'PASS_FAIL'),
        ('OUT', 'Outgoing Inspection', 'Final product before dispatch', 'OUTGOING', 'DELIVERY', 'PASS_FAIL'),
        ('WH', 'Warehouse Inspection', 'Storage condition/handling inspection', 'WAREHOUSE', 'STORAGE', 'PASS_FAIL'),
        ('SUP', 'Supplier Audit', 'Supplier facility/quality system audit', 'SUPPLIER', 'SUPPLIER', 'GRADED'),
        ('CUST', 'Customer Inspection', 'Customer-specific inspection requirements', 'CUSTOMER', 'RETURN', 'PASS_FAIL'),
        ('RET', 'Return Inspection', 'Inspection of returned goods', 'RETURN', 'RETURN', 'PASS_FAIL'),
        ('FIN', 'Final Inspection', 'End-of-line quality check', 'FINAL', 'PRODUCTION', 'PASS_FAIL'),
        ('SAN', 'Sanitation Inspection', 'Hygiene/sanitation check', 'SANITATION', 'FACILITY', 'PASS_FAIL'),
        ('ENV', 'Environmental Inspection', 'Environmental condition check', 'ENVIRONMENTAL', 'STORAGE', 'PASS_FAIL'),
    ]
    
    for code, name, description, category, applicable, result_type in types:
        try:
            with get_db() as db:
                db.execute("""
                    INSERT OR IGNORE INTO quality_inspection_types 
                    (code, name, description, category, applicable_source, result_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (code, name, description, category, applicable, result_type))
                db.commit()
        except:
            pass


def _seed_default_defect_categories():
    """Seed default defect categories."""
    categories = [
        ('DIM', 'Dimensional', 'Parts not within specified dimensions', 'Critical,Major,Minor'),
        ('SUR', 'Surface Defect', 'Scratches, dents, marks, discoloration', 'Critical,Major,Minor'),
        ('MAT', 'Material Defect', 'Wrong material, contamination, impurities', 'Critical,Major,Minor'),
        ('FUNC', 'Functional', 'Part does not perform intended function', 'Critical,Major,Minor'),
        ('PACK', 'Packaging', 'Damaged packaging, missing labels, incorrect packaging', 'Critical,Major,Minor'),
        ('DOC', 'Documentation', 'Missing/m incorrect certificates, documents', 'Critical,Major,Minor'),
        ('QTY', 'Quantity', 'Incorrect quantity received', 'Critical,Major,Minor'),
        ('PERF', 'Performance', 'Does not meet performance specifications', 'Critical,Major,Minor'),
        ('SAFE', 'Safety', 'Safety-critical defects', 'Critical'),
        ('OTHER', 'Other', 'Other defects not classified', 'Critical,Major,Minor'),
    ]
    
    for code, name, description, severity_levels in categories:
        try:
            with get_db() as db:
                db.execute("""
                    INSERT OR IGNORE INTO quality_defect_categories 
                    (code, name, description, severity_levels)
                    VALUES (?, ?, ?, ?)
                """, (code, name, description, severity_levels))
                db.commit()
        except:
            pass


def _seed_default_capa_categories():
    """Seed default CAPA categories."""
    categories = [
        ('PROC', 'Process Issue', 'Manufacturing or process-related cause'),
        ('DES', 'Design Issue', 'Product or process design flaw'),
        ('MAT', 'Material Issue', 'Raw material or component defect'),
        ('EQUIP', 'Equipment Issue', 'Machinery or equipment malfunction'),
        ('HUMAN', 'Human Error', 'Training, procedure, or human factors'),
        ('SUP', 'Supplier Issue', 'Supplier-related quality problem'),
        ('STORAGE', 'Storage/Handling', 'Storage or handling issue'),
        ('INSPEC', 'Inspection Error', 'Quality inspection oversight'),
        ('ENG', 'Engineering', 'Engineering specification issue'),
        ('MGMT', 'Management', 'Management system or procedure gap'),
        ('OTHER', 'Other', 'Other causes not classified'),
    ]
    
    for code, name, description in categories:
        try:
            with get_db() as db:
                db.execute("""
                    INSERT OR IGNORE INTO quality_capa_categories 
                    (code, name, description)
                    VALUES (?, ?, ?)
                """, (code, name, description))
                db.commit()
        except:
            pass


def _seed_default_root_cause_categories():
    """Seed default root cause categories."""
    categories = [
        ('MAN', 'Man/Personnel', 'Human factors, training, procedures'),
        ('MACH', 'Machine/Equipment', 'Equipment failure, wear, malfunction'),
        ('MAT', 'Material', 'Raw material defect, component failure'),
        ('METHOD', 'Method/Process', 'Process design, procedure inadequacy'),
        ('MEAS', 'Measurement', 'Inspection/test method error'),
        ('ENV', 'Environment', 'Temperature, humidity, contamination'),
        ('DESIGN', 'Design', 'Product or process design flaw'),
        ('SUP', 'Supplier', 'Supplier-related causes'),
        ('MGMT', 'Management', 'System, policy, leadership gaps'),
        ('UNKNOWN', 'Unknown', 'Root cause not yet determined'),
    ]
    
    for code, name, description in categories:
        try:
            with get_db() as db:
                db.execute("""
                    INSERT OR IGNORE INTO quality_root_cause_categories 
                    (code, name, description)
                    VALUES (?, ?, ?)
                """, (code, name, description))
                db.commit()
        except:
            pass


# =============================================================================
# NUMBER GENERATION
# =============================================================================

def get_next_inspection_number():
    """Generate next inspection number."""
    with get_db() as db:
        result = db.execute("""
            SELECT COALESCE(MAX(CAST(SUBSTR(inspection_number, 5) AS INTEGER)), 0) + 1 as next_num
            FROM quality_inspections
            WHERE inspection_number LIKE 'INS%'
        """).fetchone()
        next_num = result['next_num'] if result else 1
        return f"INS{next_num:06d}"


def get_next_ncr_number():
    """Generate next NCR number."""
    with get_db() as db:
        result = db.execute("""
            SELECT COALESCE(MAX(CAST(SUBSTR(ncr_number, 4) AS INTEGER)), 0) + 1 as next_num
            FROM quality_non_conformances
            WHERE ncr_number LIKE 'NCR%'
        """).fetchone()
        next_num = result['next_num'] if result else 1
        return f"NCR{next_num:06d}"


def get_next_capa_number():
    """Generate next CAPA number."""
    with get_db() as db:
        result = db.execute("""
            SELECT COALESCE(MAX(CAST(SUBSTR(capa_number, 5) AS INTEGER)), 0) + 1 as next_num
            FROM quality_capa_records
            WHERE capa_number LIKE 'CAPA%'
        """).fetchone()
        next_num = result['next_num'] if result else 1
        return f"CAPA{next_num:06d}"


def get_next_audit_plan_number():
    """Generate next audit plan number."""
    with get_db() as db:
        result = db.execute("""
            SELECT COALESCE(MAX(CAST(SUBSTR(plan_number, 4) AS INTEGER)), 0) + 1 as next_num
            FROM quality_audit_plans
            WHERE plan_number LIKE 'AUD%'
        """).fetchone()
        next_num = result['next_num'] if result else 1
        return f"AUD{next_num:06d}"


def get_next_finding_number():
    """Generate next audit finding number."""
    with get_db() as db:
        result = db.execute("""
            SELECT COALESCE(MAX(CAST(SUBSTR(finding_number, 5) AS INTEGER)), 0) + 1 as next_num
            FROM quality_audit_findings
            WHERE finding_number LIKE 'FIND%'
        """).fetchone()
        next_num = result['next_num'] if result else 1
        return f"FIND{next_num:06d}"


def get_next_containment_action_number():
    """Generate next containment action number."""
    with get_db() as db:
        result = db.execute("""
            SELECT COALESCE(MAX(CAST(SUBSTR(action_number, 3) AS INTEGER)), 0) + 1 as next_num
            FROM quality_containment_actions
            WHERE action_number LIKE 'CA%'
        """).fetchone()
        next_num = result['next_num'] if result else 1
        return f"CA{next_num:06d}"


def get_next_capa_action_number(capa_id):
    """Generate next CAPA action number."""
    with get_db() as db:
        result = db.execute("""
            SELECT COALESCE(MAX(CAST(SUBSTR(action_number, 5) AS INTEGER)), 0) + 1 as next_num
            FROM quality_capa_actions
            WHERE capa_id = ? AND action_number LIKE 'CA%'
        """, (capa_id,)).fetchone()
        next_num = result['next_num'] if result else 1
        return f"CA{next_num:04d}"


def get_next_effectiveness_review_number(capa_id):
    """Generate next effectiveness review number."""
    with get_db() as db:
        result = db.execute("""
            SELECT COALESCE(MAX(CAST(SUBSTR(review_number, 4) AS INTEGER)), 0) + 1 as next_num
            FROM quality_effectiveness_reviews
            WHERE capa_id = ? AND review_number LIKE 'ER%'
        """, (capa_id,)).fetchone()
        next_num = result['next_num'] if result else 1
        return f"ER{next_num:04d}"


def get_next_log_number():
    """Generate next audit log number."""
    with get_db() as db:
        result = db.execute("""
            SELECT COALESCE(MAX(CAST(SUBSTR(log_number, 4) AS INTEGER)), 0) + 1 as next_num
            FROM quality_audit_log
            WHERE log_number LIKE 'QL%'
        """).fetchone()
        next_num = result['next_num'] if result else 1
        return f"QL{next_num:08d}"


# =============================================================================
# QUALITY SETTINGS HELPERS
# =============================================================================

def get_quality_setting(key, default=None):
    """Get a quality module setting value."""
    with get_db() as db:
        result = db.execute(
            "SELECT setting_value FROM quality_settings WHERE setting_key = ? AND is_active = 1",
            (key,)
        ).fetchone()
        return result['setting_value'] if result else default


def set_quality_setting(key, value):
    """Set a quality module setting value."""
    with get_db() as db:
        db.execute("""
            INSERT INTO quality_settings (setting_key, setting_value, category)
            VALUES (?, ?, 'USER')
            ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value
        """, (key, value))
        db.commit()


# =============================================================================
# QUALITY DASHBOARD STATISTICS
# =============================================================================

def get_quality_dashboard_stats(company_id=None, branch_id=None):
    """Get comprehensive quality dashboard statistics."""
    stats = {
        'total_inspections': 0,
        'pending_inspections': 0,
        'completed_inspections': 0,
        'failed_inspections': 0,
        'pass_rate': 0,
        'open_ncrs': 0,
        'pending_ncrs': 0,
        'closed_ncrs': 0,
        'overdue_ncrs': 0,
        'open_capas': 0,
        'pending_effectiveness': 0,
        'closed_capas': 0,
        'overdue_capas': 0,
        'active_audits': 0,
        'scheduled_audits': 0,
        'completed_audits': 0,
        'open_findings': 0,
        'overdue_findings': 0,
        'inspections_by_type': [],
        'ncrs_by_severity': [],
        'ncrs_by_category': [],
        'capa_status_distribution': [],
        'recent_inspections': [],
        'recent_ncrs': [],
        'recent_capas': [],
        'upcoming_audits': [],
        'overdue_actions': [],
    }
    
    with get_db() as db:
        # Build WHERE clause for company/branch filtering
        where_clauses = []
        params = []
        if company_id:
            where_clauses.append("company_id = ?")
            params.append(company_id)
        if branch_id:
            where_clauses.append("branch_id = ?")
            params.append(branch_id)
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        
        # Inspections
        result = db.execute(f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'IN_PROGRESS' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN result = 'FAIL' THEN 1 ELSE 0 END) as failed
            FROM quality_inspections
            WHERE {where_sql}
        """, params).fetchone()
        
        if result:
            stats['total_inspections'] = result['total'] or 0
            stats['pending_inspections'] = result['pending'] or 0
            stats['completed_inspections'] = result['completed'] or 0
            stats['failed_inspections'] = result['failed'] or 0
            total_completed = stats['completed_inspections']
            stats['pass_rate'] = round(((total_completed - stats['failed_inspections']) / total_completed * 100) if total_completed > 0 else 100, 1)
        
        # NCRs
        result = db.execute(f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'OPEN' THEN 1 ELSE 0 END) as open_ncrs,
                SUM(CASE WHEN status IN ('UNDER_REVIEW', 'CONTAINMENT', 'INVESTIGATION') THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'CLOSED' THEN 1 ELSE 0 END) as closed,
                SUM(CASE WHEN target_close_date < date('now') AND status != 'CLOSED' THEN 1 ELSE 0 END) as overdue
            FROM quality_non_conformances
            WHERE {where_sql}
        """, params).fetchone()
        
        if result:
            stats['open_ncrs'] = result['open_ncrs'] or 0
            stats['pending_ncrs'] = result['pending'] or 0
            stats['closed_ncrs'] = result['closed'] or 0
            stats['overdue_ncrs'] = result['overdue'] or 0
        
        # CAPAs
        result = db.execute(f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'OPEN' THEN 1 ELSE 0 END) as open,
                SUM(CASE WHEN status = 'EFFECTIVENESS_REVIEW' THEN 1 ELSE 0 END) as pending_effect,
                SUM(CASE WHEN status = 'CLOSED' THEN 1 ELSE 0 END) as closed,
                SUM(CASE WHEN target_date < date('now') AND status NOT IN ('CLOSED', 'CANCELLED') THEN 1 ELSE 0 END) as overdue
            FROM quality_capa_records
            WHERE {where_sql}
        """, params).fetchone()
        
        if result:
            stats['open_capas'] = result['open'] or 0
            stats['pending_effectiveness'] = result['pending_effect'] or 0
            stats['closed_capas'] = result['closed'] or 0
            stats['overdue_capas'] = result['overdue'] or 0
        
        # Audits
        result = db.execute(f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'IN_PROGRESS' THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN status = 'COMPLETED' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'PLANNED' THEN 1 ELSE 0 END) as scheduled
            FROM quality_audit_plans
            WHERE {where_sql}
        """, params).fetchone()
        
        if result:
            stats['active_audits'] = result['active'] or 0
            stats['scheduled_audits'] = result['scheduled'] or 0
            stats['completed_audits'] = result['completed'] or 0
        
        # Findings
        result = db.execute(f"""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'OPEN' THEN 1 ELSE 0 END) as open_findings,
                SUM(CASE WHEN due_date < date('now') AND status = 'OPEN' THEN 1 ELSE 0 END) as overdue
            FROM quality_audit_findings
            WHERE {where_sql}
        """, params).fetchone()
        
        if result:
            stats['open_findings'] = result['open_findings'] or 0
            stats['overdue_findings'] = result['overdue'] or 0
        
        # Inspections by type
        stats['inspections_by_type'] = db.execute(f"""
            SELECT 
                qit.name as type_name,
                COUNT(qi.id) as count,
                SUM(CASE WHEN qi.result = 'PASS' THEN 1 ELSE 0 END) as passed,
                SUM(CASE WHEN qi.result = 'FAIL' THEN 1 ELSE 0 END) as failed
            FROM quality_inspection_types qit
            LEFT JOIN quality_inspections qi ON qit.id = qi.inspection_type_id AND ({where_sql})
            GROUP BY qit.id, qit.name
            ORDER BY count DESC
            LIMIT 10
        """, params).fetchall()
        
        # NCRs by severity
        stats['ncrs_by_severity'] = db.execute(f"""
            SELECT severity, COUNT(*) as count
            FROM quality_non_conformances
            WHERE {where_sql} AND severity IS NOT NULL
            GROUP BY severity
        """, params).fetchall()
        
        # NCRs by category
        stats['ncrs_by_category'] = db.execute(f"""
            SELECT ncr_category, COUNT(*) as count
            FROM quality_non_conformances
            WHERE {where_sql} AND ncr_category IS NOT NULL
            GROUP BY ncr_category
            ORDER BY count DESC
            LIMIT 10
        """, params).fetchall()
        
        # CAPA status distribution
        stats['capa_status_distribution'] = db.execute(f"""
            SELECT status, COUNT(*) as count
            FROM quality_capa_records
            WHERE {where_sql}
            GROUP BY status
        """, params).fetchall()
        
        # Recent inspections
        stats['recent_inspections'] = db.execute(f"""
            SELECT qi.*, qit.name as type_name
            FROM quality_inspections qi
            LEFT JOIN quality_inspection_types qit ON qi.inspection_type_id = qit.id
            WHERE {where_sql}
            ORDER BY qi.created_at DESC
            LIMIT 10
        """, params).fetchall()
        
        # Recent NCRs
        stats['recent_ncrs'] = db.execute(f"""
            SELECT * FROM quality_non_conformances
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT 10
        """, params).fetchall()
        
        # Recent CAPAs
        stats['recent_capas'] = db.execute(f"""
            SELECT * FROM quality_capa_records
            WHERE {where_sql}
            ORDER BY created_at DESC
            LIMIT 10
        """, params).fetchall()
        
        # Upcoming audits
        stats['upcoming_audits'] = db.execute(f"""
            SELECT * FROM quality_audit_plans
            WHERE {where_sql} AND status = 'PLANNED'
            ORDER BY scheduled_start_date ASC
            LIMIT 10
        """, params).fetchall()
        
        # Overdue actions (CAPA actions and containment)
        stats['overdue_actions'] = db.execute(f"""
            SELECT 
                'CAPA Action' as action_type,
                qca.action_description as description,
                qcr.capa_number,
                qca.due_date,
                qca.responsible_name
            FROM quality_capa_actions qca
            JOIN quality_capa_records qcr ON qca.capa_id = qcr.id
            WHERE qca.due_date < date('now') AND qca.status != 'COMPLETED'
            UNION ALL
            SELECT 
                'Containment' as action_type,
                qca.action_description as description,
                qncr.ncr_number,
                qca.due_date,
                qca.responsible_name
            FROM quality_containment_actions qca
            JOIN quality_non_conformances qncr ON qca.ncr_id = qncr.id
            WHERE qca.due_date < date('now') AND qca.status != 'COMPLETED'
            ORDER BY due_date ASC
            LIMIT 20
        """).fetchall()
    
    return stats


# =============================================================================
# INSPECTION CRUD OPERATIONS
# =============================================================================

def create_inspection(data):
    """Create a new quality inspection."""
    with get_db() as db:
        inspection_number = get_next_inspection_number()
        
        db.execute("""
            INSERT INTO quality_inspections (
                inspection_number, inspection_type_id, template_id, plan_id,
                source_type, source_reference, source_reference_id,
                company_id, branch_id, warehouse_id, location_id, department,
                supplier_id, customer_id, item_id, item_code, item_name,
                lot_number, serial_number, batch_number,
                quantity_received, quantity_inspected, sample_size,
                quantity_accepted, quantity_rejected, quantity_held, quantity_conditionally_accepted,
                inspection_date, inspection_time, inspector_id, inspector_name,
                team_members, result, status, disposition, disposition_notes,
                reinspection_required, reinspection_of_id, ncr_id, notes, attachments,
                completed_at, completed_by, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            inspection_number,
            data.get('inspection_type_id'),
            data.get('template_id'),
            data.get('plan_id'),
            data.get('source_type'),
            data.get('source_reference'),
            data.get('source_reference_id'),
            data.get('company_id'),
            data.get('branch_id'),
            data.get('warehouse_id'),
            data.get('location_id'),
            data.get('department'),
            data.get('supplier_id'),
            data.get('customer_id'),
            data.get('item_id'),
            data.get('item_code'),
            data.get('item_name'),
            data.get('lot_number'),
            data.get('serial_number'),
            data.get('batch_number'),
            data.get('quantity_received', 0),
            data.get('quantity_inspected', 0),
            data.get('sample_size', 0),
            data.get('quantity_accepted', 0),
            data.get('quantity_rejected', 0),
            data.get('quantity_held', 0),
            data.get('quantity_conditionally_accepted', 0),
            data.get('inspection_date'),
            data.get('inspection_time'),
            data.get('inspector_id'),
            data.get('inspector_name'),
            data.get('team_members'),
            data.get('result'),
            data.get('status', 'IN_PROGRESS'),
            data.get('disposition'),
            data.get('disposition_notes'),
            data.get('reinspection_required', 0),
            data.get('reinspection_of_id'),
            data.get('ncr_id'),
            data.get('notes'),
            data.get('attachments'),
            data.get('completed_at'),
            data.get('completed_by'),
            datetime.now().isoformat(),
            data.get('created_by'),
        ))
        db.commit()
        
        inspection_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # Log the creation
        _log_quality_change('INSPECTION', inspection_id, inspection_number, 'CREATED', user_id=data.get('created_by'))
        
        return inspection_id, inspection_number


def get_inspections(filters=None):
    """Get inspections with optional filters."""
    with get_db() as db:
        where_clauses = ["1=1"]
        params = []
        
        if filters:
            if filters.get('company_id'):
                where_clauses.append("qi.company_id = ?")
                params.append(filters['company_id'])
            if filters.get('branch_id'):
                where_clauses.append("qi.branch_id = ?")
                params.append(filters['branch_id'])
            if filters.get('warehouse_id'):
                where_clauses.append("qi.warehouse_id = ?")
                params.append(filters['warehouse_id'])
            if filters.get('inspection_type_id'):
                where_clauses.append("qi.inspection_type_id = ?")
                params.append(filters['inspection_type_id'])
            if filters.get('status'):
                where_clauses.append("qi.status = ?")
                params.append(filters['status'])
            if filters.get('result'):
                where_clauses.append("qi.result = ?")
                params.append(filters['result'])
            if filters.get('supplier_id'):
                where_clauses.append("qi.supplier_id = ?")
                params.append(filters['supplier_id'])
            if filters.get('customer_id'):
                where_clauses.append("qi.customer_id = ?")
                params.append(filters['customer_id'])
            if filters.get('item_id'):
                where_clauses.append("qi.item_id = ?")
                params.append(filters['item_id'])
            if filters.get('inspector_id'):
                where_clauses.append("qi.inspector_id = ?")
                params.append(filters['inspector_id'])
            if filters.get('source_type'):
                where_clauses.append("qi.source_type = ?")
                params.append(filters['source_type'])
            if filters.get('from_date'):
                where_clauses.append("qi.inspection_date >= ?")
                params.append(filters['from_date'])
            if filters.get('to_date'):
                where_clauses.append("qi.inspection_date <= ?")
                params.append(filters['to_date'])
            if filters.get('search'):
                where_clauses.append("(qi.inspection_number LIKE ? OR qi.item_name LIKE ? OR qi.item_code LIKE ?)")
                search = f"%{filters['search']}%"
                params.extend([search, search, search])
        
        where_sql = " AND ".join(where_clauses)
        
        query = f"""
            SELECT qi.*, qit.name as type_name, qit.code as type_code,
                   w.name as warehouse_name, b.name as branch_name,
                   s.name as supplier_name, c.name as customer_name
            FROM quality_inspections qi
            LEFT JOIN quality_inspection_types qit ON qi.inspection_type_id = qit.id
            LEFT JOIN warehouses w ON qi.warehouse_id = w.id
            LEFT JOIN company_branches b ON qi.branch_id = b.id
            LEFT JOIN suppliers s ON qi.supplier_id = s.id
            LEFT JOIN customers c ON qi.customer_id = c.id
            WHERE {where_sql}
            ORDER BY qi.created_at DESC
        """
        
        return db.execute(query, params).fetchall()


def get_inspection_by_id(inspection_id):
    """Get a single inspection by ID."""
    with get_db() as db:
        return db.execute("""
            SELECT qi.*, qit.name as type_name, qit.code as type_code
            FROM quality_inspections qi
            LEFT JOIN quality_inspection_types qit ON qi.inspection_type_id = qit.id
            WHERE qi.id = ?
        """, (inspection_id,)).fetchone()


def update_inspection(inspection_id, data):
    """Update an inspection record."""
    with get_db() as db:
        # Get current state for audit
        current = db.execute("SELECT * FROM quality_inspections WHERE id = ?", (inspection_id,)).fetchone()
        
        # Build update query
        fields = []
        values = []
        for key in ['inspection_type_id', 'template_id', 'quantity_inspected', 'sample_size',
                    'quantity_accepted', 'quantity_rejected', 'quantity_held', 'quantity_conditionally_accepted',
                    'result', 'status', 'disposition', 'disposition_notes', 'notes', 'attachments',
                    'completed_at', 'completed_by', 'ncr_id']:
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])
        
        if fields:
            fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            fields.append("WHERE id = ?")
            values.append(inspection_id)
            
            db.execute(f"UPDATE quality_inspections SET {', '.join(fields[:-1])} {fields[-1]}", values[:-1])
            db.commit()
        
        # Log changes
        if current:
            for key in data:
                if data[key] != current[key]:
                    _log_quality_change('INSPECTION', inspection_id, current['inspection_number'], 
                                       f'FIELD_UPDATE:{key}', 
                                       old_value=str(current.get(key)), 
                                       new_value=str(data[key]),
                                       user_id=data.get('updated_by'))


def get_inspection_lines(inspection_id):
    """Get inspection checklist lines."""
    with get_db() as db:
        return db.execute("""
            SELECT * FROM quality_inspection_lines
            WHERE inspection_id = ?
            ORDER BY line_number
        """, (inspection_id,)).fetchall()


def add_inspection_line(inspection_id, data):
    """Add a checklist line to an inspection."""
    with get_db() as db:
        db.execute("""
            INSERT INTO quality_inspection_lines (
                inspection_id, template_line_id, line_number, criterion, description,
                inspection_method, acceptance_criteria, result_type, result,
                measurement_value, measurement_unit, is_conforming, findings,
                severity, is_mandatory, weight, notes, attachments
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            inspection_id, data.get('template_line_id'), data.get('line_number'),
            data.get('criterion'), data.get('description'), data.get('inspection_method'),
            data.get('acceptance_criteria'), data.get('result_type', 'PASS_FAIL'),
            data.get('result'), data.get('measurement_value'), data.get('measurement_unit'),
            data.get('is_conforming'), data.get('findings'), data.get('severity'),
            data.get('is_mandatory', 1), data.get('weight', 1.0), data.get('notes'),
            data.get('attachments')
        ))
        db.commit()
        return db.execute("SELECT last_insert_rowid()").fetchone()[0]


# =============================================================================
# NCR CRUD OPERATIONS
# =============================================================================

def create_ncr(data):
    """Create a new Non-Conformance Record."""
    with get_db() as db:
        ncr_number = get_next_ncr_number()
        
        db.execute("""
            INSERT INTO quality_non_conformances (
                ncr_number, source_type, source_reference, source_reference_id,
                company_id, branch_id, warehouse_id, department, location_id,
                item_id, item_code, item_name, lot_number, batch_number,
                supplier_id, supplier_name, customer_id, customer_name,
                ncr_category, defect_category_id, defect_type, severity, impact, priority,
                description, detected_by, detected_by_name, detected_date,
                owner_id, owner_name, assigned_to_id, assigned_to_name,
                status, containment_required, containment_status, root_cause_required,
                root_cause_status, capa_required, capa_id,
                immediate_action, disposition, hold_quantity, return_quantity,
                rework_quantity, scrap_quantity, use_as_is_quantity, financial_impact,
                target_close_date, notes, attachments, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ncr_number,
            data.get('source_type'),
            data.get('source_reference'),
            data.get('source_reference_id'),
            data.get('company_id'),
            data.get('branch_id'),
            data.get('warehouse_id'),
            data.get('department'),
            data.get('location_id'),
            data.get('item_id'),
            data.get('item_code'),
            data.get('item_name'),
            data.get('lot_number'),
            data.get('batch_number'),
            data.get('supplier_id'),
            data.get('supplier_name'),
            data.get('customer_id'),
            data.get('customer_name'),
            data.get('ncr_category'),
            data.get('defect_category_id'),
            data.get('defect_type'),
            data.get('severity', 'MEDIUM'),
            data.get('impact'),
            data.get('priority', 'MEDIUM'),
            data.get('description'),
            data.get('detected_by'),
            data.get('detected_by_name'),
            data.get('detected_date'),
            data.get('owner_id'),
            data.get('owner_name'),
            data.get('assigned_to_id'),
            data.get('assigned_to_name'),
            data.get('status', 'OPEN'),
            data.get('containment_required', 0),
            data.get('containment_status', 'PENDING'),
            data.get('root_cause_required', 0),
            data.get('root_cause_status', 'PENDING'),
            data.get('capa_required', 0),
            data.get('capa_id'),
            data.get('immediate_action'),
            data.get('disposition'),
            data.get('hold_quantity', 0),
            data.get('return_quantity', 0),
            data.get('rework_quantity', 0),
            data.get('scrap_quantity', 0),
            data.get('use_as_is_quantity', 0),
            data.get('financial_impact', 0),
            data.get('target_close_date'),
            data.get('notes'),
            data.get('attachments'),
            datetime.now().isoformat(),
            data.get('created_by'),
        ))
        db.commit()
        
        ncr_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        _log_quality_change('NCR', ncr_id, ncr_number, 'CREATED', user_id=data.get('created_by'))
        
        return ncr_id, ncr_number


def get_ncrs(filters=None):
    """Get NCRs with optional filters."""
    with get_db() as db:
        where_clauses = ["1=1"]
        params = []
        
        if filters:
            if filters.get('company_id'):
                where_clauses.append("qnc.company_id = ?")
                params.append(filters['company_id'])
            if filters.get('branch_id'):
                where_clauses.append("qnc.branch_id = ?")
                params.append(filters['branch_id'])
            if filters.get('warehouse_id'):
                where_clauses.append("qnc.warehouse_id = ?")
                params.append(filters['warehouse_id'])
            if filters.get('status'):
                where_clauses.append("qnc.status = ?")
                params.append(filters['status'])
            if filters.get('severity'):
                where_clauses.append("qnc.severity = ?")
                params.append(filters['severity'])
            if filters.get('ncr_category'):
                where_clauses.append("qnc.ncr_category = ?")
                params.append(filters['ncr_category'])
            if filters.get('supplier_id'):
                where_clauses.append("qnc.supplier_id = ?")
                params.append(filters['supplier_id'])
            if filters.get('customer_id'):
                where_clauses.append("qnc.customer_id = ?")
                params.append(filters['customer_id'])
            if filters.get('owner_id'):
                where_clauses.append("qnc.owner_id = ?")
                params.append(filters['owner_id'])
            if filters.get('from_date'):
                where_clauses.append("qnc.detected_date >= ?")
                params.append(filters['from_date'])
            if filters.get('to_date'):
                where_clauses.append("qnc.detected_date <= ?")
                params.append(filters['to_date'])
            if filters.get('search'):
                where_clauses.append("(qnc.ncr_number LIKE ? OR qnc.item_name LIKE ? OR qnc.description LIKE ?)")
                search = f"%{filters['search']}%"
                params.extend([search, search, search])
            if filters.get('is_overdue'):
                where_clauses.append("qnc.target_close_date < date('now') AND qnc.status NOT IN ('CLOSED', 'CANCELLED')")
        
        where_sql = " AND ".join(where_clauses)
        
        return db.execute(f"""
            SELECT qnc.*, qdc.name as defect_category_name,
                   s.name as supplier_name, c.name as customer_name
            FROM quality_non_conformances qnc
            LEFT JOIN quality_defect_categories qdc ON qnc.defect_category_id = qdc.id
            LEFT JOIN suppliers s ON qnc.supplier_id = s.id
            LEFT JOIN customers c ON qnc.customer_id = c.id
            WHERE {where_sql}
            ORDER BY qnc.created_at DESC
        """, params).fetchall()


def get_ncr_by_id(ncr_id):
    """Get a single NCR by ID."""
    with get_db() as db:
        return db.execute("""
            SELECT qnc.*, qdc.name as defect_category_name
            FROM quality_non_conformances qnc
            LEFT JOIN quality_defect_categories qdc ON qnc.defect_category_id = qdc.id
            WHERE qnc.id = ?
        """, (ncr_id,)).fetchone()


def update_ncr(ncr_id, data):
    """Update an NCR record."""
    with get_db() as db:
        current = db.execute("SELECT * FROM quality_non_conformances WHERE id = ?", (ncr_id,)).fetchone()
        
        updatable_fields = [
            'status', 'owner_id', 'owner_name', 'assigned_to_id', 'assigned_to_name',
            'containment_required', 'containment_status', 'root_cause_required', 'root_cause_status',
            'capa_required', 'capa_id', 'immediate_action', 'disposition',
            'disposition_approved_by', 'disposition_approved_at',
            'hold_quantity', 'return_quantity', 'rework_quantity', 'scrap_quantity', 'use_as_is_quantity',
            'financial_impact', 'target_close_date', 'actual_close_date',
            'closure_verified_by', 'closure_verified_at', 'closure_notes',
            'reopen_count', 'reopen_reason', 'notes', 'attachments',
            'rejection_reason', 'rejected_by', 'rejected_at'
        ]
        
        fields = []
        values = []
        for key in updatable_fields:
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])
        
        if fields:
            fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(ncr_id)
            
            db.execute(f"UPDATE quality_non_conformances SET {', '.join(fields[:-1])} WHERE id = ?", values[:-1])
            db.commit()
        
        if current:
            for key in data:
                if data[key] != current[key]:
                    _log_quality_change('NCR', ncr_id, current['ncr_number'], f'FIELD_UPDATE:{key}',
                                       old_value=str(current.get(key)), new_value=str(data[key]),
                                       user_id=data.get('updated_by'))


def get_containment_actions(ncr_id):
    """Get containment actions for an NCR."""
    with get_db() as db:
        return db.execute("""
            SELECT * FROM quality_containment_actions
            WHERE ncr_id = ?
            ORDER BY created_at
        """, (ncr_id,)).fetchall()


def create_containment_action(ncr_id, data):
    """Create a containment action for an NCR."""
    with get_db() as db:
        action_number = get_next_containment_action_number()
        
        db.execute("""
            INSERT INTO quality_containment_actions (
                ncr_id, action_number, action_type, description,
                responsible_id, responsible_name, due_date, completed_date,
                status, evidence, notes, verified_by, verified_at,
                created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ncr_id, action_number, data.get('action_type'), data.get('description'),
            data.get('responsible_id'), data.get('responsible_name'), data.get('due_date'),
            data.get('completed_date'), data.get('status', 'PENDING'),
            data.get('evidence'), data.get('notes'), data.get('verified_by'),
            data.get('verified_at'), datetime.now().isoformat(), data.get('created_by')
        ))
        db.commit()
        
        action_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # Update NCR containment status
        db.execute("""
            UPDATE quality_non_conformances
            SET containment_status = 'IN_PROGRESS'
            WHERE id = ?
        """, (ncr_id,))
        db.commit()
        
        return action_id, action_number


def update_containment_action(action_id, data):
    """Update a containment action."""
    with get_db() as db:
        db.execute("""
            UPDATE quality_containment_actions
            SET action_type = COALESCE(?, action_type),
                description = COALESCE(?, description),
                responsible_id = COALESCE(?, responsible_id),
                responsible_name = COALESCE(?, responsible_name),
                due_date = COALESCE(?, due_date),
                completed_date = COALESCE(?, completed_date),
                status = COALESCE(?, status),
                evidence = COALESCE(?, evidence),
                notes = COALESCE(?, notes),
                verified_by = COALESCE(?, verified_by),
                verified_at = COALESCE(?, verified_at),
                updated_at = ?
            WHERE id = ?
        """, (
            data.get('action_type'), data.get('description'),
            data.get('responsible_id'), data.get('responsible_name'),
            data.get('due_date'), data.get('completed_date'),
            data.get('status'), data.get('evidence'),
            data.get('notes'), data.get('verified_by'),
            data.get('verified_at'), datetime.now().isoformat(),
            action_id
        ))
        db.commit()


# =============================================================================
# CAPA CRUD OPERATIONS
# =============================================================================

def create_capa(data):
    """Create a new CAPA record."""
    with get_db() as db:
        capa_number = get_next_capa_number()
        
        db.execute("""
            INSERT INTO quality_capa_records (
                capa_number, triggering_source, source_type, source_reference, source_reference_id,
                ncr_id, audit_finding_id, company_id, branch_id, department, warehouse_id,
                category_id, capa_type, severity, priority, title, description,
                root_cause_summary, root_cause_category_id, root_cause_description,
                contributing_factors, is_recurring_issue, previous_capa_id,
                owner_id, owner_name, approver_id, approver_name,
                target_date, status, effectiveness_verification_required,
                notes, attachments, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            capa_number, data.get('triggering_source'), data.get('source_type'),
            data.get('source_reference'), data.get('source_reference_id'),
            data.get('ncr_id'), data.get('audit_finding_id'),
            data.get('company_id'), data.get('branch_id'), data.get('department'),
            data.get('warehouse_id'), data.get('category_id'),
            data.get('capa_type', 'CORRECTIVE'), data.get('severity', 'MEDIUM'),
            data.get('priority', 'MEDIUM'), data.get('title'),
            data.get('description'), data.get('root_cause_summary'),
            data.get('root_cause_category_id'), data.get('root_cause_description'),
            data.get('contributing_factors'), data.get('is_recurring_issue', 0),
            data.get('previous_capa_id'), data.get('owner_id'), data.get('owner_name'),
            data.get('approver_id'), data.get('approver_name'),
            data.get('target_date'), data.get('status', 'OPEN'),
            data.get('effectiveness_verification_required', 1),
            data.get('notes'), data.get('attachments'),
            datetime.now().isoformat(), data.get('created_by')
        ))
        db.commit()
        
        capa_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # Update NCR if linked
        if data.get('ncr_id'):
            db.execute("""
                UPDATE quality_non_conformances
                SET capa_required = 1, capa_id = ?, status = 'CAPA_OPEN'
                WHERE id = ?
            """, (capa_id, data.get('ncr_id')))
            db.commit()
        
        _log_quality_change('CAPA', capa_id, capa_number, 'CREATED', user_id=data.get('created_by'))
        
        return capa_id, capa_number


def get_capas(filters=None):
    """Get CAPAs with optional filters."""
    with get_db() as db:
        where_clauses = ["1=1"]
        params = []
        
        if filters:
            if filters.get('company_id'):
                where_clauses.append("qcr.company_id = ?")
                params.append(filters['company_id'])
            if filters.get('branch_id'):
                where_clauses.append("qcr.branch_id = ?")
                params.append(filters['branch_id'])
            if filters.get('status'):
                where_clauses.append("qcr.status = ?")
                params.append(filters['status'])
            if filters.get('capa_type'):
                where_clauses.append("qcr.capa_type = ?")
                params.append(filters['capa_type'])
            if filters.get('severity'):
                where_clauses.append("qcr.severity = ?")
                params.append(filters['severity'])
            if filters.get('priority'):
                where_clauses.append("qcr.priority = ?")
                params.append(filters['priority'])
            if filters.get('owner_id'):
                where_clauses.append("qcr.owner_id = ?")
                params.append(filters['owner_id'])
            if filters.get('ncr_id'):
                where_clauses.append("qcr.ncr_id = ?")
                params.append(filters['ncr_id'])
            if filters.get('from_date'):
                where_clauses.append("qcr.created_at >= ?")
                params.append(filters['from_date'])
            if filters.get('to_date'):
                where_clauses.append("qcr.created_at <= ?")
                params.append(filters['to_date'])
            if filters.get('search'):
                where_clauses.append("(qcr.capa_number LIKE ? OR qcr.title LIKE ?)")
                search = f"%{filters['search']}%"
                params.extend([search, search])
            if filters.get('is_overdue'):
                where_clauses.append("qcr.target_date < date('now') AND qcr.status NOT IN ('CLOSED', 'CANCELLED')")
            if filters.get('pending_effectiveness'):
                where_clauses.append("qcr.status = 'EFFECTIVENESS_REVIEW'")
        
        where_sql = " AND ".join(where_clauses)
        
        return db.execute(f"""
            SELECT qcr.*, qcc.name as category_name, qrc.name as root_cause_category_name,
                   qncr.ncr_number
            FROM quality_capa_records qcr
            LEFT JOIN quality_capa_categories qcc ON qcr.category_id = qcc.id
            LEFT JOIN quality_root_cause_categories qrc ON qcr.root_cause_category_id = qrc.id
            LEFT JOIN quality_non_conformances qncr ON qcr.ncr_id = qncr.id
            WHERE {where_sql}
            ORDER BY qcr.created_at DESC
        """, params).fetchall()


def get_capa_by_id(capa_id):
    """Get a single CAPA by ID."""
    with get_db() as db:
        return db.execute("""
            SELECT qcr.*, qcc.name as category_name, qrc.name as root_cause_category_name
            FROM quality_capa_records qcr
            LEFT JOIN quality_capa_categories qcc ON qcr.category_id = qcc.id
            LEFT JOIN quality_root_cause_categories qrc ON qcr.root_cause_category_id = qrc.id
            WHERE qcr.id = ?
        """, (capa_id,)).fetchone()


def update_capa(capa_id, data):
    """Update a CAPA record."""
    with get_db() as db:
        current = db.execute("SELECT * FROM quality_capa_records WHERE id = ?", (capa_id,)).fetchone()
        
        updatable_fields = [
            'category_id', 'capa_type', 'severity', 'priority', 'title', 'description',
            'root_cause_summary', 'root_cause_category_id', 'root_cause_description',
            'contributing_factors', 'is_recurring_issue', 'previous_capa_id',
            'owner_id', 'owner_name', 'approver_id', 'approver_name',
            'target_date', 'actual_completion_date', 'status',
            'effectiveness_verification_required', 'effectiveness_review_status',
            'effectiveness_review_date', 'effectiveness_reviewer_id', 'effectiveness_result',
            'effectiveness_notes', 'effectiveness_evidence',
            'closed_by', 'closed_at', 'closure_notes',
            'reopen_count', 'reopen_reason', 'reopened_by', 'reopened_at',
            'notes', 'attachments', 'approved_by', 'approved_at'
        ]
        
        fields = []
        values = []
        for key in updatable_fields:
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])
        
        if fields:
            fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(capa_id)
            
            db.execute(f"UPDATE quality_capa_records SET {', '.join(fields[:-1])} WHERE id = ?", values[:-1])
            db.commit()
        
        if current:
            for key in data:
                if data[key] != current[key]:
                    _log_quality_change('CAPA', capa_id, current['capa_number'], f'FIELD_UPDATE:{key}',
                                       old_value=str(current.get(key)), new_value=str(data[key]),
                                       user_id=data.get('updated_by'))


def get_capa_actions(capa_id):
    """Get CAPA actions for a CAPA."""
    with get_db() as db:
        return db.execute("""
            SELECT * FROM quality_capa_actions
            WHERE capa_id = ?
            ORDER BY created_at
        """, (capa_id,)).fetchall()


def create_capa_action(capa_id, data):
    """Create a CAPA action."""
    with get_db() as db:
        action_number = get_next_capa_action_number(capa_id)
        
        db.execute("""
            INSERT INTO quality_capa_actions (
                capa_id, action_number, action_description, action_type,
                responsible_id, responsible_name, due_date, completed_date,
                status, evidence, completion_notes, follow_up_date,
                follow_up_required, verified_by, verified_at,
                created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            capa_id, action_number, data.get('action_description'), data.get('action_type'),
            data.get('responsible_id'), data.get('responsible_name'), data.get('due_date'),
            data.get('completed_date'), data.get('status', 'PENDING'),
            data.get('evidence'), data.get('completion_notes'), data.get('follow_up_date'),
            data.get('follow_up_required', 0), data.get('verified_by'), data.get('verified_at'),
            datetime.now().isoformat(), data.get('created_by')
        ))
        db.commit()
        
        return db.execute("SELECT last_insert_rowid()").fetchone()[0], action_number


def update_capa_action(action_id, data):
    """Update a CAPA action."""
    with get_db() as db:
        db.execute("""
            UPDATE quality_capa_actions
            SET action_description = COALESCE(?, action_description),
                action_type = COALESCE(?, action_type),
                responsible_id = COALESCE(?, responsible_id),
                responsible_name = COALESCE(?, responsible_name),
                due_date = COALESCE(?, due_date),
                completed_date = COALESCE(?, completed_date),
                status = COALESCE(?, status),
                evidence = COALESCE(?, evidence),
                completion_notes = COALESCE(?, completion_notes),
                follow_up_date = COALESCE(?, follow_up_date),
                follow_up_required = COALESCE(?, follow_up_required),
                verified_by = COALESCE(?, verified_by),
                verified_at = COALESCE(?, verified_at),
                updated_at = ?
            WHERE id = ?
        """, (
            data.get('action_description'), data.get('action_type'),
            data.get('responsible_id'), data.get('responsible_name'),
            data.get('due_date'), data.get('completed_date'),
            data.get('status'), data.get('evidence'),
            data.get('completion_notes'), data.get('follow_up_date'),
            data.get('follow_up_required'), data.get('verified_by'),
            data.get('verified_at'), datetime.now().isoformat(),
            action_id
        ))
        db.commit()


def create_effectiveness_review(capa_id, data):
    """Create an effectiveness review for a CAPA."""
    with get_db() as db:
        review_number = get_next_effectiveness_review_number(capa_id)
        
        db.execute("""
            INSERT INTO quality_effectiveness_reviews (
                capa_id, review_number, review_date, reviewer_id, reviewer_name,
                effectiveness_result, result_meets_criteria, evidence, findings,
                recurrence_observed, recurrence_details, further_action_required,
                further_action_description, next_review_date, status,
                notes, attachments, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            capa_id, review_number, data.get('review_date'), data.get('reviewer_id'),
            data.get('reviewer_name'), data.get('effectiveness_result'),
            data.get('result_meets_criteria'), data.get('evidence'), data.get('findings'),
            data.get('recurrence_observed', 0), data.get('recurrence_details'),
            data.get('further_action_required', 0), data.get('further_action_description'),
            data.get('next_review_date'), data.get('status', 'PENDING'),
            data.get('notes'), data.get('attachments'),
            datetime.now().isoformat(), data.get('created_by')
        ))
        db.commit()
        
        review_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # Update CAPA effectiveness review status
        db.execute("""
            UPDATE quality_capa_records
            SET effectiveness_review_status = 'REVIEW_COMPLETED',
                effectiveness_review_date = ?,
                effectiveness_reviewer_id = ?,
                effectiveness_result = ?,
                effectiveness_notes = ?
            WHERE id = ?
        """, (data.get('review_date'), data.get('reviewer_id'),
              data.get('effectiveness_result'), data.get('notes'), capa_id))
        db.commit()
        
        return review_id, review_number


# =============================================================================
# AUDIT CRUD OPERATIONS
# =============================================================================

def create_audit_plan(data):
    """Create a new audit plan."""
    with get_db() as db:
        plan_number = get_next_audit_plan_number()
        
        db.execute("""
            INSERT INTO quality_audit_plans (
                plan_number, program_id, audit_type, scope, objectives,
                company_id, branch_id, warehouse_id, site_location, department, process_area,
                scheduled_start_date, scheduled_end_date,
                lead_auditor_id, lead_auditor_name, auditor_ids, auditor_names,
                auditee_id, auditee_name, auditee_department,
                checklist_template_id, status, preparation_status,
                document_review_notes, notes, attachments, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            plan_number, data.get('program_id'), data.get('audit_type'),
            data.get('scope'), data.get('objectives'),
            data.get('company_id'), data.get('branch_id'), data.get('warehouse_id'),
            data.get('site_location'), data.get('department'), data.get('process_area'),
            data.get('scheduled_start_date'), data.get('scheduled_end_date'),
            data.get('lead_auditor_id'), data.get('lead_auditor_name'),
            data.get('auditor_ids'), data.get('auditor_names'),
            data.get('auditee_id'), data.get('auditee_name'), data.get('auditee_department'),
            data.get('checklist_template_id'), data.get('status', 'PLANNED'),
            data.get('preparation_status', 'NOT_STARTED'),
            data.get('document_review_notes'), data.get('notes'), data.get('attachments'),
            datetime.now().isoformat(), data.get('created_by')
        ))
        db.commit()
        
        plan_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        _log_quality_change('AUDIT_PLAN', plan_id, plan_number, 'CREATED', user_id=data.get('created_by'))
        
        return plan_id, plan_number


def get_audit_plans(filters=None):
    """Get audit plans with optional filters."""
    with get_db() as db:
        where_clauses = ["1=1"]
        params = []
        
        if filters:
            if filters.get('company_id'):
                where_clauses.append("qap.company_id = ?")
                params.append(filters['company_id'])
            if filters.get('branch_id'):
                where_clauses.append("qap.branch_id = ?")
                params.append(filters['branch_id'])
            if filters.get('status'):
                where_clauses.append("qap.status = ?")
                params.append(filters['status'])
            if filters.get('audit_type'):
                where_clauses.append("qap.audit_type = ?")
                params.append(filters['audit_type'])
            if filters.get('lead_auditor_id'):
                where_clauses.append("qap.lead_auditor_id = ?")
                params.append(filters['lead_auditor_id'])
            if filters.get('from_date'):
                where_clauses.append("qap.scheduled_start_date >= ?")
                params.append(filters['from_date'])
            if filters.get('to_date'):
                where_clauses.append("qap.scheduled_start_date <= ?")
                params.append(filters['to_date'])
            if filters.get('search'):
                where_clauses.append("(qap.plan_number LIKE ? OR qap.scope LIKE ?)")
                search = f"%{filters['search']}%"
                params.extend([search, search])
        
        where_sql = " AND ".join(where_clauses)
        
        return db.execute(f"""
            SELECT qap.*, qapg.program_name
            FROM quality_audit_plans qap
            LEFT JOIN quality_audit_programs qapg ON qap.program_id = qapg.id
            WHERE {where_sql}
            ORDER BY qap.created_at DESC
        """, params).fetchall()


def get_audit_plan_by_id(plan_id):
    """Get a single audit plan by ID."""
    with get_db() as db:
        return db.execute("""
            SELECT qap.*, qapg.program_name, qact.template_name as checklist_template_name
            FROM quality_audit_plans qap
            LEFT JOIN quality_audit_programs qapg ON qap.program_id = qapg.id
            LEFT JOIN quality_audit_checklist_templates qact ON qap.checklist_template_id = qact.id
            WHERE qap.id = ?
        """, (plan_id,)).fetchone()


def update_audit_plan(plan_id, data):
    """Update an audit plan."""
    with get_db() as db:
        current = db.execute("SELECT * FROM quality_audit_plans WHERE id = ?", (plan_id,)).fetchone()
        
        updatable_fields = [
            'audit_type', 'scope', 'objectives', 'warehouse_id', 'site_location',
            'department', 'process_area', 'scheduled_start_date', 'scheduled_end_date',
            'actual_start_date', 'actual_end_date', 'lead_auditor_id', 'lead_auditor_name',
            'auditor_ids', 'auditor_names', 'auditee_id', 'auditee_name', 'auditee_department',
            'checklist_template_id', 'status', 'preparation_status', 'document_review_notes',
            'notification_sent', 'opening_meeting_held', 'closing_meeting_held',
            'notes', 'attachments'
        ]
        
        fields = []
        values = []
        for key in updatable_fields:
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])
        
        if fields:
            fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(plan_id)
            
            db.execute(f"UPDATE quality_audit_plans SET {', '.join(fields[:-1])} WHERE id = ?", values[:-1])
            db.commit()
        
        if current:
            for key in data:
                if data[key] != current[key]:
                    _log_quality_change('AUDIT_PLAN', plan_id, current['plan_number'], f'FIELD_UPDATE:{key}',
                                       old_value=str(current.get(key)), new_value=str(data[key]),
                                       user_id=data.get('updated_by'))


def get_audit_findings(filters=None):
    """Get audit findings with optional filters."""
    with get_db() as db:
        where_clauses = ["1=1"]
        params = []
        
        if filters:
            if filters.get('audit_plan_id'):
                where_clauses.append("qaf.audit_plan_id = ?")
                params.append(filters['audit_plan_id'])
            if filters.get('status'):
                where_clauses.append("qaf.status = ?")
                params.append(filters['status'])
            if filters.get('severity'):
                where_clauses.append("qaf.severity = ?")
                params.append(filters['severity'])
            if filters.get('category'):
                where_clauses.append("qaf.category = ?")
                params.append(filters['category'])
            if filters.get('owner_id'):
                where_clauses.append("qaf.owner_id = ?")
                params.append(filters['owner_id'])
            if filters.get('is_overdue'):
                where_clauses.append("qaf.due_date < date('now') AND qaf.status = 'OPEN'")
            if filters.get('search'):
                where_clauses.append("(qaf.finding_number LIKE ? OR qaf.description LIKE ?)")
                search = f"%{filters['search']}%"
                params.extend([search, search])
        
        where_sql = " AND ".join(where_clauses)
        
        return db.execute(f"""
            SELECT qaf.*, qap.plan_number, qcr.capa_number
            FROM quality_audit_findings qaf
            LEFT JOIN quality_audit_plans qap ON qaf.audit_plan_id = qap.id
            LEFT JOIN quality_capa_records qcr ON qaf.capa_id = qcr.id
            WHERE {where_sql}
            ORDER BY qaf.created_at DESC
        """, params).fetchall()


def get_finding_by_id(finding_id):
    """Get a single finding by ID."""
    with get_db() as db:
        return db.execute("""
            SELECT qaf.*, qap.plan_number, qcr.capa_number
            FROM quality_audit_findings qaf
            LEFT JOIN quality_audit_plans qap ON qaf.audit_plan_id = qap.id
            LEFT JOIN quality_capa_records qcr ON qaf.capa_id = qcr.id
            WHERE qaf.id = ?
        """, (finding_id,)).fetchone()


def create_audit_finding(plan_id, data):
    """Create an audit finding."""
    with get_db() as db:
        finding_number = get_next_finding_number()
        
        db.execute("""
            INSERT INTO quality_audit_findings (
                finding_number, audit_plan_id, checklist_id, category, severity,
                clause_reference, requirement, description, evidence,
                auditee_statement, root_cause, corrective_action, preventive_action,
                capa_id, owner_id, owner_name, due_date, status,
                notes, attachments, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            finding_number, plan_id, data.get('checklist_id'), data.get('category', 'NON_CONFORMITY'),
            data.get('severity', 'MINOR'), data.get('clause_reference'), data.get('requirement'),
            data.get('description'), data.get('evidence'), data.get('auditee_statement'),
            data.get('root_cause'), data.get('corrective_action'), data.get('preventive_action'),
            data.get('capa_id'), data.get('owner_id'), data.get('owner_name'),
            data.get('due_date'), data.get('status', 'OPEN'),
            data.get('notes'), data.get('attachments'),
            datetime.now().isoformat(), data.get('created_by')
        ))
        db.commit()
        
        finding_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # Update audit plan findings count
        db.execute("""
            UPDATE quality_audit_plans
            SET findings_count = findings_count + 1,
                major_findings_count = major_findings_count + CASE WHEN ? = 'MAJOR' THEN 1 ELSE 0 END,
                minor_findings_count = minor_findings_count + CASE WHEN ? = 'MINOR' THEN 1 ELSE 0 END,
                observations_count = observations_count + CASE WHEN ? = 'OBSERVATION' THEN 1 ELSE 0 END
            WHERE id = ?
        """, (data.get('severity'), data.get('severity'), data.get('category'), plan_id))
        db.commit()
        
        _log_quality_change('AUDIT_FINDING', finding_id, finding_number, 'CREATED', user_id=data.get('created_by'))
        
        return finding_id, finding_number


def update_audit_finding(finding_id, data):
    """Update an audit finding."""
    with get_db() as db:
        current = db.execute("SELECT * FROM quality_audit_findings WHERE id = ?", (finding_id,)).fetchone()
        
        updatable_fields = [
            'category', 'severity', 'clause_reference', 'requirement', 'description',
            'evidence', 'auditee_statement', 'root_cause', 'corrective_action',
            'preventive_action', 'capa_id', 'owner_id', 'owner_name', 'due_date',
            'actual_close_date', 'status', 'verified_by', 'verified_at',
            'verification_evidence', 'notes', 'attachments',
            'rejected_reason', 'rejected_by', 'rejected_at'
        ]
        
        fields = []
        values = []
        for key in updatable_fields:
            if key in data:
                fields.append(f"{key} = ?")
                values.append(data[key])
        
        if fields:
            fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(finding_id)
            
            db.execute(f"UPDATE quality_audit_findings SET {', '.join(fields[:-1])} WHERE id = ?", values[:-1])
            db.commit()
        
        if current:
            for key in data:
                if data[key] != current[key]:
                    _log_quality_change('AUDIT_FINDING', finding_id, current['finding_number'], f'FIELD_UPDATE:{key}',
                                       old_value=str(current.get(key)), new_value=str(data[key]),
                                       user_id=data.get('updated_by'))


# =============================================================================
# AUDIT LOG HELPER
# =============================================================================

def _log_quality_change(entity_type, entity_id, entity_number, action, field_changed=None,
                        old_value=None, new_value=None, user_id=None, notes=None, ip_address=None):
    """Log a quality management change to the audit log."""
    try:
        log_number = get_next_log_number()
        
        with get_db() as db:
            db.execute("""
                INSERT INTO quality_audit_log (
                    log_number, entity_type, entity_id, entity_number,
                    action, field_changed, old_value, new_value,
                    user_id, ip_address, notes, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_number, entity_type, entity_id, entity_number,
                action, field_changed, old_value, new_value,
                user_id, ip_address, notes, datetime.now().isoformat()
            ))
            db.commit()
    except Exception as e:
        # Don't fail the main operation if logging fails
        print(f"Warning: Failed to log quality change: {e}")


def get_quality_audit_log(filters=None):
    """Get quality audit log with optional filters."""
    with get_db() as db:
        where_clauses = ["1=1"]
        params = []
        
        if filters:
            if filters.get('entity_type'):
                where_clauses.append("qal.entity_type = ?")
                params.append(filters['entity_type'])
            if filters.get('entity_id'):
                where_clauses.append("qal.entity_id = ?")
                params.append(filters['entity_id'])
            if filters.get('action'):
                where_clauses.append("qal.action = ?")
                params.append(filters['action'])
            if filters.get('user_id'):
                where_clauses.append("qal.user_id = ?")
                params.append(filters['user_id'])
            if filters.get('from_date'):
                where_clauses.append("qal.timestamp >= ?")
                params.append(filters['from_date'])
            if filters.get('to_date'):
                where_clauses.append("qal.timestamp <= ?")
                params.append(filters['to_date'])
            if filters.get('search'):
                where_clauses.append("(qal.entity_number LIKE ? OR qal.notes LIKE ?)")
                search = f"%{filters['search']}%"
                params.extend([search, search])
        
        where_sql = " AND ".join(where_clauses)
        
        return db.execute(f"""
            SELECT qal.*, u.username as user_name
            FROM quality_audit_log qal
            LEFT JOIN users u ON qal.user_id = u.id
            WHERE {where_sql}
            ORDER BY qal.timestamp DESC
        """, params).fetchall()


# =============================================================================
# LOOKUP HELPERS
# =============================================================================

def get_inspection_types():
    """Get all active inspection types."""
    with get_db() as db:
        return db.execute("""
            SELECT * FROM quality_inspection_types
            WHERE is_active = 1
            ORDER BY name
        """).fetchall()


def get_defect_categories():
    """Get all active defect categories."""
    with get_db() as db:
        return db.execute("""
            SELECT * FROM quality_defect_categories
            WHERE is_active = 1
            ORDER BY name
        """).fetchall()


def get_capa_categories():
    """Get all active CAPA categories."""
    with get_db() as db:
        return db.execute("""
            SELECT * FROM quality_capa_categories
            WHERE is_active = 1
            ORDER BY name
        "").fetchall()


def get_root_cause_categories():
    """Get all active root cause categories."""
    with get_db() as db:
        return db.execute("""
            SELECT * FROM quality_root_cause_categories
            WHERE is_active = 1
            ORDER BY name
        """).fetchall()


def get_inspection_templates():
    """Get all active inspection templates."""
    with get_db() as db:
        return db.execute("""
            SELECT qt.*, qit.name as type_name
            FROM quality_inspection_templates qt
            LEFT JOIN quality_inspection_types qit ON qt.inspection_type_id = qit.id
            WHERE qt.is_active = 1
            ORDER BY qt.template_name
        """).fetchall()


def get_audit_checklist_templates():
    """Get all active audit checklist templates."""
    with get_db() as db:
        return db.execute("""
            SELECT * FROM quality_audit_checklist_templates
            WHERE is_active = 1
            ORDER BY template_name
        """).fetchall()


def get_audit_programs():
    """Get all active audit programs."""
    with get_db() as db:
        return db.execute("""
            SELECT * FROM quality_audit_programs
            WHERE status = 'ACTIVE'
            ORDER BY program_name
        """).fetchall()


# =============================================================================
# EXPORT AND REPORT HELPERS
# =============================================================================

def get_inspection_report_data(filters=None):
    """Get detailed inspection report data."""
    inspections = get_inspections(filters)
    
    report_data = []
    for insp in inspections:
        lines = get_inspection_lines(insp['id'])
        findings = []
        
        with get_db() as db:
            findings = db.execute("""
                SELECT * FROM quality_inspection_findings
                WHERE inspection_id = ?
            """, (insp['id'],)).fetchall()
        
        report_data.append({
            'inspection': insp,
            'lines': [dict(l) for l in lines],
            'findings': [dict(f) for f in findings]
        })
    
    return report_data


def get_ncr_summary_report(company_id=None, branch_id=None, from_date=None, to_date=None):
    """Get NCR summary report."""
    with get_db() as db:
        where_clauses = ["1=1"]
        params = []
        
        if company_id:
            where_clauses.append("company_id = ?")
            params.append(company_id)
        if branch_id:
            where_clauses.append("branch_id = ?")
            params.append(branch_id)
        if from_date:
            where_clauses.append("detected_date >= ?")
            params.append(from_date)
        if to_date:
            where_clauses.append("detected_date <= ?")
            params.append(to_date)
        
        where_sql = " AND ".join(where_clauses)
        
        # Summary by status
        by_status = db.execute(f"""
            SELECT status, COUNT(*) as count
            FROM quality_non_conformances
            WHERE {where_sql}
            GROUP BY status
        """, params).fetchall()
        
        # Summary by severity
        by_severity = db.execute(f"""
            SELECT severity, COUNT(*) as count
            FROM quality_non_conformances
            WHERE {where_sql}
            GROUP BY severity
        """, params).fetchall()
        
        # Summary by category
        by_category = db.execute(f"""
            SELECT ncr_category, COUNT(*) as count
            FROM quality_non_conformances
            WHERE {where_sql}
            GROUP BY ncr_category
            ORDER BY count DESC
        """, params).fetchall()
        
        # Summary by supplier
        by_supplier = db.execute(f"""
            SELECT supplier_name, COUNT(*) as count
            FROM quality_non_conformances
            WHERE {where_sql} AND supplier_name IS NOT NULL
            GROUP BY supplier_name
            ORDER BY count DESC
            LIMIT 20
        """, params).fetchall()
        
        # Monthly trend
        monthly_trend = db.execute(f"""
            SELECT 
                strftime('%Y-%m', detected_date) as month,
                COUNT(*) as total,
                SUM(CASE WHEN status = 'CLOSED' THEN 1 ELSE 0 END) as closed
            FROM quality_non_conformances
            WHERE {where_sql} AND detected_date IS NOT NULL
            GROUP BY strftime('%Y-%m', detected_date)
            ORDER BY month DESC
            LIMIT 12
        """, params).fetchall()
        
        return {
            'by_status': [dict(r) for r in by_status],
            'by_severity': [dict(r) for r in by_severity],
            'by_category': [dict(r) for r in by_category],
            'by_supplier': [dict(r) for r in by_supplier],
            'monthly_trend': [dict(r) for r in monthly_trend],
        }


def get_capa_summary_report(company_id=None, branch_id=None, from_date=None, to_date=None):
    """Get CAPA summary report."""
    with get_db() as db:
        where_clauses = ["1=1"]
        params = []
        
        if company_id:
            where_clauses.append("company_id = ?")
            params.append(company_id)
        if branch_id:
            where_clauses.append("branch_id = ?")
            params.append(branch_id)
        if from_date:
            where_clauses.append("created_at >= ?")
            params.append(from_date)
        if to_date:
            where_clauses.append("created_at <= ?")
            params.append(to_date)
        
        where_sql = " AND ".join(where_clauses)
        
        # Summary by status
        by_status = db.execute(f"""
            SELECT status, COUNT(*) as count
            FROM quality_capa_records
            WHERE {where_sql}
            GROUP BY status
        """, params).fetchall()
        
        # Summary by type
        by_type = db.execute(f"""
            SELECT capa_type, COUNT(*) as count
            FROM quality_capa_records
            WHERE {where_sql}
            GROUP BY capa_type
        """, params).fetchall()
        
        # Summary by category
        by_category = db.execute(f"""
            SELECT qcc.name, COUNT(*) as count
            FROM quality_capa_records qcr
            LEFT JOIN quality_capa_categories qcc ON qcr.category_id = qcc.id
            WHERE {where_sql}
            GROUP BY qcc.name
            ORDER BY count DESC
        """, params).fetchall()
        
        # Effectiveness summary
        effectiveness_summary = db.execute(f"""
            SELECT 
                effectiveness_result, COUNT(*) as count
            FROM quality_capa_records
            WHERE {where_sql} AND effectiveness_result IS NOT NULL
            GROUP BY effectiveness_result
        """, params).fetchall()
        
        # Average closure time
        avg_closure = db.execute(f"""
            SELECT 
                AVG(julianday(actual_completion_date) - julianday(created_at)) as avg_days
            FROM quality_capa_records
            WHERE {where_sql} AND status = 'CLOSED' AND actual_completion_date IS NOT NULL
        """, params).fetchone()
        
        return {
            'by_status': [dict(r) for r in by_status],
            'by_type': [dict(r) for r in by_type],
            'by_category': [dict(r) for r in by_category],
            'effectiveness_summary': [dict(r) for r in effectiveness_summary],
            'avg_closure_days': round(avg_closure['avg_days'], 1) if avg_closure and avg_closure['avg_days'] else 0,
        }


def get_supplier_quality_report(supplier_id=None, from_date=None, to_date=None):
    """Get supplier quality performance report."""
    with get_db() as db:
        where_clauses = ["1=1"]
        params = []

        if supplier_id:
            where_clauses.append("supplier_id = ?")
            params.append(supplier_id)
        if from_date:
            where_clauses.append("detected_date >= ?")
            params.append(from_date)
        if to_date:
            where_clauses.append("detected_date <= ?")
            params.append(to_date)

        where_sql = " AND ".join(where_clauses)

        query = """
            SELECT
                s.id as supplier_id,
                s.name as supplier_name,
                COUNT(qnc.id) as ncr_count,
                SUM(CASE WHEN qnc.status = 'CLOSED' THEN 1 ELSE 0 END) as closed_count,
                SUM(CASE WHEN qnc.severity = 'CRITICAL' THEN 1 ELSE 0 END) as critical_count,
                SUM(CASE WHEN qnc.severity = 'MAJOR' THEN 1 ELSE 0 END) as major_count,
                SUM(qnc.financial_impact) as total_cost
            FROM suppliers s
            LEFT JOIN quality_non_conformances qnc ON s.id = qnc.supplier_id AND (%s)
            WHERE s.id IN (SELECT DISTINCT supplier_id FROM quality_non_conformances WHERE supplier_id IS NOT NULL)
            GROUP BY s.id, s.name
            ORDER BY ncr_count DESC
        """ % where_sql

        ncr_by_supplier = db.execute(query, params).fetchall()

        return {
            'ncr_by_supplier': [dict(r) for r in ncr_by_supplier],
        }
