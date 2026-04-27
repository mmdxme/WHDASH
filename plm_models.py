"""
R&D / PLM Module Database Models
=================================
Comprehensive database models for Research & Development and 
Product Lifecycle Management (PLM) capabilities.

This module provides:
- Idea management and innovation pipeline
- R&D project management with stage-gates
- Product concepts and specifications
- Product master and revision control
- Development BOM / product structure
- Prototype and sample management
- Test plans and validation
- Engineering change control (ECO/ECN)
- Release readiness tracking
- Risk, issue, and action management
- Cost and supplier links
- Scorecards and reporting
- Full audit trail

Tables:
- rnd_ideas: Idea/intake management
- rnd_projects: R&D project master data
- rnd_project_stage_history: Stage gate history
- rnd_product_masters: Product master records
- rnd_product_revisions: Revision tracking
- rnd_specifications: Product specifications
- rnd_specification_sections: Structured spec sections
- rnd_boms: Bill of Materials
- rnd_bom_lines: BOM line items
- rnd_prototypes: Prototype records
- rnd_samples: Sample records
- rnd_test_plans: Test plan master
- rnd_test_results: Test results
- rnd_change_requests: Engineering changes
- rnd_change_impacts: Change impact areas
- rnd_release_readiness: Release readiness tracking
- rnd_release_checklist_items: Readiness checklist
- rnd_risks: Risk register
- rnd_issues: Issue register
- rnd_action_items: Action items
- rnd_cost_estimates: Cost hooks
- rnd_supplier_links: Supplier relationships
- rnd_scorecards: Scorecard definitions
- rnd_score_details: Scorecard metrics
- rnd_export_presets: Saved export configurations
- rnd_dashboard_preferences: Dashboard settings
- rnd_audit_records: Audit trail
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'warehouse.db'))


def get_db():
    """Get database connection with Row factory for dict-like access."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


# =============================================================================
# PLM TABLE DEFINITIONS
# =============================================================================

PLM_TABLES = [
    # -------------------------------------------------------------------------
    # 1. Ideas & Innovation Pipeline
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_ideas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        idea_number TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        submitter_name TEXT,
        submitter_department TEXT,
        category TEXT,
        product_family TEXT,
        market_line TEXT,
        problem_statement TEXT,
        proposed_solution TEXT,
        expected_value TEXT,
        estimated_complexity TEXT DEFAULT 'Medium',
        priority TEXT DEFAULT 'Normal',
        status TEXT DEFAULT 'Draft',
        source_type TEXT,
        linked_customer_id INTEGER,
        linked_supplier_id INTEGER,
        review_owner_id INTEGER,
        attachments TEXT,
        notes TEXT,
        company_id INTEGER,
        branch_id INTEGER,
        is_archived INTEGER DEFAULT 0,
        archived_at DATETIME,
        created_by_user_id INTEGER,
        approved_by_user_id INTEGER,
        approved_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 2. R&D Projects
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_number TEXT UNIQUE NOT NULL,
        project_code TEXT,
        project_name TEXT NOT NULL,
        linked_idea_id INTEGER,
        owner_user_id INTEGER,
        technical_lead_id INTEGER,
        commercial_lead_id INTEGER,
        quality_lead_id INTEGER,
        procurement_lead_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        site_id INTEGER,
        department_id INTEGER,
        product_family TEXT,
        project_type TEXT,
        start_date DATE,
        target_completion_date DATE,
        target_launch_date DATE,
        actual_end_date DATE,
        business_case TEXT,
        budget_reference TEXT,
        stage TEXT DEFAULT 'Discovery',
        previous_stage TEXT,
        status TEXT DEFAULT 'Active',
        risk_level TEXT DEFAULT 'Medium',
        priority TEXT DEFAULT 'Normal',
        progress INTEGER DEFAULT 0,
        stage_completion_date DATE,
        linked_documents TEXT,
        notes TEXT,
        is_archived INTEGER DEFAULT 0,
        archived_at DATETIME,
        created_by_user_id INTEGER,
        approved_by_user_id INTEGER,
        approved_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (linked_idea_id) REFERENCES rnd_ideas(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 3. Project Stage History (for tracking stage gates)
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_project_stage_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        stage TEXT NOT NULL,
        status TEXT DEFAULT 'Completed',
        completion_date DATE,
        duration_days INTEGER,
        notes TEXT,
        completed_by_user_id INTEGER,
        gate_checklist TEXT,
        required_approvals TEXT,
        required_documents TEXT,
        test_requirements TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES rnd_projects(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 4. Product Masters
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_product_masters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_code TEXT UNIQUE NOT NULL,
        part_number TEXT,
        description TEXT,
        brand TEXT,
        series TEXT,
        product_family TEXT,
        category TEXT,
        uom TEXT DEFAULT 'EA',
        application TEXT,
        compatibility TEXT,
        status TEXT DEFAULT 'Draft',
        lifecycle_state TEXT DEFAULT 'Draft',
        current_revision_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        notes TEXT,
        is_archived INTEGER DEFAULT 0,
        archived_at DATETIME,
        created_by_user_id INTEGER,
        released_by_user_id INTEGER,
        released_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 5. Product Revisions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_product_revisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        revision_number TEXT NOT NULL,
        revision_label TEXT,
        change_reason TEXT,
        change_summary TEXT,
        effective_date DATE,
        release_date DATE,
        superseded_by_revision_id INTEGER,
        replaces_revision_id INTEGER,
        status TEXT DEFAULT 'Draft',
        approval_state TEXT DEFAULT 'Pending',
        approved_by_user_id INTEGER,
        approved_at DATETIME,
        rejection_reason TEXT,
        linked_project_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        notes TEXT,
        is_archived INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES rnd_product_masters(id) ON DELETE CASCADE,
        FOREIGN KEY (linked_project_id) REFERENCES rnd_projects(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 6. Specifications
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_specifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        spec_number TEXT UNIQUE NOT NULL,
        product_revision_id INTEGER,
        linked_project_id INTEGER,
        spec_category TEXT,
        title TEXT NOT NULL,
        version TEXT DEFAULT '1.0',
        revision TEXT DEFAULT 'A',
        status TEXT DEFAULT 'Draft',
        approval_state TEXT DEFAULT 'Pending',
        source_of_truth INTEGER DEFAULT 0,
        effective_date DATE,
        superseded_by_spec_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        notes TEXT,
        created_by_user_id INTEGER,
        approved_by_user_id INTEGER,
        approved_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_revision_id) REFERENCES rnd_product_revisions(id) ON DELETE SET NULL,
        FOREIGN KEY (linked_project_id) REFERENCES rnd_projects(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 7. Specification Sections (structured spec data)
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_specification_sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        spec_id INTEGER NOT NULL,
        section_type TEXT NOT NULL,
        section_title TEXT NOT NULL,
        content TEXT,
        sort_order INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (spec_id) REFERENCES rnd_specifications(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 8. Bill of Materials (BOM)
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_boms (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bom_number TEXT UNIQUE NOT NULL,
        product_revision_id INTEGER,
        linked_project_id INTEGER,
        bom_type TEXT DEFAULT 'Production',
        revision TEXT,
        status TEXT DEFAULT 'Draft',
        approval_state TEXT DEFAULT 'Pending',
        total_estimated_cost DECIMAL(12,2),
        currency TEXT DEFAULT 'USD',
        effective_from DATE,
        effective_to DATE,
        change_summary TEXT,
        company_id INTEGER,
        branch_id INTEGER,
        notes TEXT,
        created_by_user_id INTEGER,
        approved_by_user_id INTEGER,
        approved_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_revision_id) REFERENCES rnd_product_revisions(id) ON DELETE SET NULL,
        FOREIGN KEY (linked_project_id) REFERENCES rnd_projects(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 9. BOM Lines
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_bom_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bom_id INTEGER NOT NULL,
        line_number INTEGER NOT NULL,
        component_item_code TEXT,
        component_description TEXT,
        quantity DECIMAL(10,3) NOT NULL,
        uom TEXT DEFAULT 'EA',
        is_required INTEGER DEFAULT 1,
        is_optional INTEGER DEFAULT 0,
        substitute_item_codes TEXT,
        sourcing_status TEXT,
        estimated_unit_cost DECIMAL(10,2),
        estimated_total_cost DECIMAL(12,2),
        supplier_id INTEGER,
        supplier_part_number TEXT,
        lead_time_days INTEGER,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (bom_id) REFERENCES rnd_boms(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 10. Prototypes
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_prototypes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prototype_number TEXT UNIQUE NOT NULL,
        linked_project_id INTEGER,
        linked_product_revision_id INTEGER,
        prototype_type TEXT,
        build_request_date DATE,
        requested_by_user_id INTEGER,
        prepared_by TEXT,
        supplier_id INTEGER,
        quantity INTEGER DEFAULT 1,
        status TEXT DEFAULT 'Requested',
        purpose TEXT,
        destination TEXT,
        feedback_summary TEXT,
        disposition TEXT,
        attachments TEXT,
        photos TEXT,
        company_id INTEGER,
        branch_id INTEGER,
        notes TEXT,
        is_archived INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (linked_project_id) REFERENCES rnd_projects(id) ON DELETE SET NULL,
        FOREIGN KEY (linked_product_revision_id) REFERENCES rnd_product_revisions(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 11. Samples
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_samples (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sample_number TEXT UNIQUE NOT NULL,
        linked_prototype_id INTEGER,
        linked_project_id INTEGER,
        linked_product_revision_id INTEGER,
        sample_type TEXT,
        build_date DATE,
        received_date DATE,
        prepared_by TEXT,
        supplier_id INTEGER,
        quantity INTEGER DEFAULT 1,
        status TEXT DEFAULT 'Requested',
        test_result TEXT,
        approval_state TEXT DEFAULT 'Pending',
        approved_by_user_id INTEGER,
        approved_at DATETIME,
        notes TEXT,
        is_archived INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (linked_prototype_id) REFERENCES rnd_prototypes(id) ON DELETE SET NULL,
        FOREIGN KEY (linked_project_id) REFERENCES rnd_projects(id) ON DELETE SET NULL,
        FOREIGN KEY (linked_product_revision_id) REFERENCES rnd_product_revisions(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 12. Test Plans
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_test_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_plan_number TEXT UNIQUE NOT NULL,
        test_title TEXT NOT NULL,
        linked_project_id INTEGER,
        linked_product_revision_id INTEGER,
        test_type TEXT NOT NULL,
        owner_user_id INTEGER,
        lab_location TEXT,
        site TEXT,
        start_date DATE,
        end_date DATE,
        criteria TEXT,
        expected_results TEXT,
        status TEXT DEFAULT 'Draft',
        notes TEXT,
        company_id INTEGER,
        branch_id INTEGER,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (linked_project_id) REFERENCES rnd_projects(id) ON DELETE SET NULL,
        FOREIGN KEY (linked_product_revision_id) REFERENCES rnd_product_revisions(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 13. Test Results
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_test_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_plan_id INTEGER NOT NULL,
        result_number TEXT UNIQUE NOT NULL,
        test_date DATE,
        tester_name TEXT,
        actual_results TEXT,
        pass_fail TEXT DEFAULT 'Pending',
        findings TEXT,
        attachments TEXT,
        photos TEXT,
        retest_required INTEGER DEFAULT 0,
        issue_linked_ids TEXT,
        approval_state TEXT DEFAULT 'Pending',
        approved_by_user_id INTEGER,
        approved_at DATETIME,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (test_plan_id) REFERENCES rnd_test_plans(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 14. Change Requests / ECO / ECN
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_change_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        change_number TEXT UNIQUE NOT NULL,
        change_type TEXT DEFAULT 'ECR',
        linked_project_id INTEGER,
        linked_product_revision_id INTEGER,
        linked_bom_id INTEGER,
        linked_spec_id INTEGER,
        change_reason TEXT NOT NULL,
        current_state TEXT,
        requested_state TEXT,
        impact_summary TEXT,
        urgency TEXT DEFAULT 'Normal',
        status TEXT DEFAULT 'Draft',
        approval_workflow TEXT,
        effective_date DATE,
        implementation_status TEXT,
        closure_notes TEXT,
        cost_impact TEXT,
        quality_impact TEXT,
        warehouse_impact TEXT,
        sales_impact TEXT,
        company_id INTEGER,
        branch_id INTEGER,
        is_archived INTEGER DEFAULT 0,
        created_by_user_id INTEGER,
        approved_by_user_id INTEGER,
        approved_at DATETIME,
        rejected_by_user_id INTEGER,
        rejected_at DATETIME,
        rejection_reason TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (linked_project_id) REFERENCES rnd_projects(id) ON DELETE SET NULL,
        FOREIGN KEY (linked_product_revision_id) REFERENCES rnd_product_revisions(id) ON DELETE SET NULL,
        FOREIGN KEY (linked_bom_id) REFERENCES rnd_boms(id) ON DELETE SET NULL,
        FOREIGN KEY (linked_spec_id) REFERENCES rnd_specifications(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 15. Change Impacts
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_change_impacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        change_request_id INTEGER NOT NULL,
        impact_area TEXT NOT NULL,
        impact_description TEXT,
        severity TEXT,
        affected_item_codes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (change_request_id) REFERENCES rnd_change_requests(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 16. Release Readiness
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_release_readiness (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_revision_id INTEGER NOT NULL,
        linked_project_id INTEGER,
        readiness_score INTEGER DEFAULT 0,
        status TEXT DEFAULT 'In Progress',
        blocker_count INTEGER DEFAULT 0,
        missing_item_count INTEGER DEFAULT 0,
        release_target_date DATE,
        actual_release_date DATE,
        released_by_user_id INTEGER,
        released_at DATETIME,
        release_notes TEXT,
        company_id INTEGER,
        branch_id INTEGER,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_revision_id) REFERENCES rnd_product_revisions(id) ON DELETE CASCADE,
        FOREIGN KEY (linked_project_id) REFERENCES rnd_projects(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 17. Release Checklist Items
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_release_checklist_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        readiness_id INTEGER NOT NULL,
        checklist_category TEXT NOT NULL,
        checklist_item TEXT NOT NULL,
        is_required INTEGER DEFAULT 1,
        is_checked INTEGER DEFAULT 0,
        checked_by_user_id INTEGER,
        checked_at DATETIME,
        notes TEXT,
        sort_order INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (readiness_id) REFERENCES rnd_release_readiness(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 18. Risks
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_risks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        risk_number TEXT UNIQUE NOT NULL,
        linked_project_id INTEGER,
        linked_product_revision_id INTEGER,
        risk_title TEXT NOT NULL,
        description TEXT,
        severity TEXT DEFAULT 'Medium',
        probability TEXT DEFAULT 'Medium',
        impact TEXT DEFAULT 'Medium',
        risk_score INTEGER,
        owner_user_id INTEGER,
        mitigation_action TEXT,
        contingency_action TEXT,
        due_date DATE,
        status TEXT DEFAULT 'Open',
        escalated INTEGER DEFAULT 0,
        linked_document_ids TEXT,
        closure_notes TEXT,
        closed_by_user_id INTEGER,
        closed_at DATETIME,
        company_id INTEGER,
        branch_id INTEGER,
        is_archived INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (linked_project_id) REFERENCES rnd_projects(id) ON DELETE CASCADE,
        FOREIGN KEY (linked_product_revision_id) REFERENCES rnd_product_revisions(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 19. Issues
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_number TEXT UNIQUE NOT NULL,
        linked_project_id INTEGER,
        linked_product_revision_id INTEGER,
        linked_test_result_id INTEGER,
        issue_title TEXT NOT NULL,
        description TEXT,
        severity TEXT DEFAULT 'Medium',
        issue_type TEXT,
        owner_user_id INTEGER,
        assigned_to_user_id INTEGER,
        due_date DATE,
        status TEXT DEFAULT 'Open',
        resolution TEXT,
        linked_document_ids TEXT,
        linked_change_request_id INTEGER,
        closure_notes TEXT,
        closed_by_user_id INTEGER,
        closed_at DATETIME,
        company_id INTEGER,
        branch_id INTEGER,
        is_archived INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (linked_project_id) REFERENCES rnd_projects(id) ON DELETE CASCADE,
        FOREIGN KEY (linked_product_revision_id) REFERENCES rnd_product_revisions(id) ON DELETE SET NULL,
        FOREIGN KEY (linked_test_result_id) REFERENCES rnd_test_results(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 20. Action Items
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_action_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action_number TEXT UNIQUE NOT NULL,
        linked_project_id INTEGER,
        linked_product_revision_id INTEGER,
        linked_risk_id INTEGER,
        linked_issue_id INTEGER,
        action_title TEXT NOT NULL,
        description TEXT,
        action_type TEXT,
        owner_user_id INTEGER,
        assigned_to_user_id INTEGER,
        due_date DATE,
        priority TEXT DEFAULT 'Normal',
        status TEXT DEFAULT 'Open',
        completion_notes TEXT,
        closed_by_user_id INTEGER,
        closed_at DATETIME,
        company_id INTEGER,
        branch_id INTEGER,
        is_archived INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (linked_project_id) REFERENCES rnd_projects(id) ON DELETE CASCADE,
        FOREIGN KEY (linked_product_revision_id) REFERENCES rnd_product_revisions(id) ON DELETE SET NULL,
        FOREIGN KEY (linked_risk_id) REFERENCES rnd_risks(id) ON DELETE SET NULL,
        FOREIGN KEY (linked_issue_id) REFERENCES rnd_issues(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 21. Cost Estimates
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_cost_estimates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        estimate_number TEXT UNIQUE NOT NULL,
        product_revision_id INTEGER,
        linked_project_id INTEGER,
        linked_bom_id INTEGER,
        estimate_type TEXT DEFAULT 'Development',
        material_cost DECIMAL(12,2),
        labor_cost DECIMAL(12,2),
        overhead_cost DECIMAL(12,2),
        tooling_cost DECIMAL(12,2),
        packaging_cost DECIMAL(12,2),
        total_cost DECIMAL(12,2),
        margin_percentage DECIMAL(6,2),
        selling_price DECIMAL(12,2),
        currency TEXT DEFAULT 'USD',
        supplier_quote_ref TEXT,
        quotation_date DATE,
        commercial_viability_notes TEXT,
        company_id INTEGER,
        branch_id INTEGER,
        notes TEXT,
        created_by_user_id INTEGER,
        approved_by_user_id INTEGER,
        approved_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_revision_id) REFERENCES rnd_product_revisions(id) ON DELETE SET NULL,
        FOREIGN KEY (linked_project_id) REFERENCES rnd_projects(id) ON DELETE SET NULL,
        FOREIGN KEY (linked_bom_id) REFERENCES rnd_boms(id) ON DELETE SET NULL
    )""",

    # -------------------------------------------------------------------------
    # 22. Supplier Links
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_supplier_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_revision_id INTEGER NOT NULL,
        supplier_id INTEGER NOT NULL,
        supplier_part_number TEXT,
        supplier_item_description TEXT,
        primary_supplier INTEGER DEFAULT 0,
        qualification_status TEXT DEFAULT 'Candidate',
        qualification_notes TEXT,
        lead_time_days INTEGER,
        moq INTEGER,
        unit_cost DECIMAL(10,2),
        currency TEXT DEFAULT 'USD',
        last_quote_date DATE,
        rfq_reference TEXT,
        is_preferred INTEGER DEFAULT 0,
        approval_comments TEXT,
        company_id INTEGER,
        branch_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_revision_id) REFERENCES rnd_product_revisions(id) ON DELETE CASCADE,
        FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 23. Scorecards
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_scorecards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scorecard_name TEXT NOT NULL,
        scorecard_type TEXT DEFAULT 'Project',
        description TEXT,
        display_type TEXT DEFAULT 'card',
        refresh_interval INTEGER DEFAULT 60,
        is_default INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        company_id INTEGER,
        branch_id INTEGER,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 24. Score Details
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_score_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        scorecard_id INTEGER NOT NULL,
        metric_name TEXT NOT NULL,
        metric_key TEXT NOT NULL,
        metric_type TEXT DEFAULT 'count',
        aggregation TEXT DEFAULT 'sum',
        display_order INTEGER DEFAULT 0,
        display_format TEXT,
        color_code TEXT,
        threshold_min DECIMAL(10,2),
        threshold_max DECIMAL(10,2),
        icon TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (scorecard_id) REFERENCES rnd_scorecards(id) ON DELETE CASCADE
    )""",

    # -------------------------------------------------------------------------
    # 25. Export Presets
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_export_presets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        preset_name TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        columns_config TEXT,
        filters_config TEXT,
        sort_config TEXT,
        output_format TEXT DEFAULT 'csv',
        include_archived INTEGER DEFAULT 0,
        include_audit_fields INTEGER DEFAULT 0,
        date_range_start DATE,
        date_range_end DATE,
        company_id INTEGER,
        branch_id INTEGER,
        created_by_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 26. Dashboard Preferences
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_dashboard_preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        dashboard_type TEXT DEFAULT 'main',
        layout_config TEXT,
        widget_preferences TEXT,
        filter_defaults TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 27. Audit Records
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS rnd_audit_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        entity_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        field_name TEXT,
        old_value TEXT,
        new_value TEXT,
        user_id INTEGER,
        ip_address TEXT,
        notes TEXT,
        company_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
]


# =============================================================================
# PLM CONSTANTS
# =============================================================================

IDEA_STATUSES = [
    'Draft', 'Submitted', 'Under Review', 'Needs Clarification',
    'Approved for Discovery', 'Rejected', 'Parked', 'Converted to R&D Project'
]

PROJECT_STAGES = [
    'Discovery', 'Feasibility', 'Concept', 'Design',
    'Prototype', 'Validation', 'Pilot', 'Release Preparation',
    'Released', 'Closed', 'Cancelled'
]

PRODUCT_LIFECYCLE_STATES = [
    'Draft', 'In Development', 'Under Review', 'Pending Validation',
    'Pending Release', 'Released', 'Frozen', 'Obsolete', 'Archived'
]

PROTOTYPE_STATUSES = [
    'Requested', 'In Preparation', 'Ready', 'Under Test',
    'Approved', 'Rejected', 'Rework Required', 'Closed'
]

TEST_STATUSES = ['Draft', 'Planned', 'In Progress', 'Completed', 'Cancelled']
TEST_PASS_FAIL = ['Pending', 'Pass', 'Fail', 'Partial', 'Inconclusive']

CHANGE_TYPES = ['ECR', 'ECO', 'ECN']
CHANGE_STATUSES = [
    'Draft', 'Submitted', 'Under Review', 'Pending Approval',
    'Approved', 'Rejected', 'Implementing', 'Effective', 'Closed', 'Cancelled'
]

RISK_SEVERITIES = ['Low', 'Medium', 'High', 'Critical']
ISSUE_SEVERITIES = ['Low', 'Medium', 'High', 'Critical', 'Blocker']

COMPLEXITY_LEVELS = ['Low', 'Medium', 'High', 'Very High']
PRIORITY_LEVELS = ['Low', 'Normal', 'High', 'Very High', 'Critical']


# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_plm_schema():
    """Initialize all PLM tables."""
    db = get_db()
    try:
        for table_sql in PLM_TABLES:
            db.execute(table_sql)
        db.commit()
        
        # Initialize default data
        _seed_plm_defaults(db)
    finally:
        db.close()


def _seed_plm_defaults(db):
    """Seed default configuration data for PLM."""
    cursor = db.cursor()
    
    # Check if default scorecard exists
    cursor.execute("SELECT id FROM rnd_scorecards WHERE is_default = 1")
    if not cursor.fetchone():
        # Create default scorecard
        cursor.execute("""
            INSERT INTO rnd_scorecards (scorecard_name, scorecard_type, description, is_default, display_type)
            VALUES ('R&D Portfolio', 'Project', 'Main R&D Portfolio Scorecard', 1, 'card')
        """)
        scorecard_id = cursor.lastrowid
        
        # Add default metrics
        default_metrics = [
            ('Active Projects', 'active_projects', 'count', 'sum', 1, 'number', '#3B82F6', 'fa-project-diagram'),
            ('Ideas Pipeline', 'ideas_pipeline', 'count', 'sum', 2, 'number', '#8B5CF6', 'fa-lightbulb'),
            ('Prototypes', 'prototypes_count', 'count', 'sum', 3, 'number', '#F59E0B', 'fa-cube'),
            ('Test Pass Rate', 'test_pass_rate', 'percentage', 'avg', 4, 'percentage', '#10B981', 'fa-check-circle'),
            ('Changes Pending', 'changes_pending', 'count', 'sum', 5, 'number', '#EF4444', 'fa-exchange-alt'),
            ('Release Readiness', 'release_readiness', 'percentage', 'avg', 6, 'percentage', '#06B6D4', 'fa-rocket'),
            ('Open Risks', 'open_risks', 'count', 'sum', 7, 'number', '#F97316', 'fa-exclamation-triangle'),
            ('Open Issues', 'open_issues', 'count', 'sum', 8, 'number', '#EC4899', 'fa-bug'),
        ]
        
        for name, key, mtype, agg, order, fmt, color, icon in default_metrics:
            cursor.execute("""
                INSERT INTO rnd_score_details (scorecard_id, metric_name, metric_key, metric_type, aggregation, display_order, display_format, color_code, icon)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (scorecard_id, name, key, mtype, agg, order, fmt, color, icon))
        
        db.commit()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_next_number(entity_type: str, prefix: str = None) -> str:
    """Generate next sequential number for an entity."""
    db = get_db()
    cursor = db.cursor()
    
    # Map entity types to their tables and prefix patterns
    patterns = {
        'idea': ('rnd_ideas', 'IDEA'),
        'project': ('rnd_projects', 'RND'),
        'product': ('rnd_product_masters', 'PROD'),
        'spec': ('rnd_specifications', 'SPEC'),
        'bom': ('rnd_boms', 'BOM'),
        'prototype': ('rnd_prototypes', 'PROT'),
        'sample': ('rnd_samples', 'SAMP'),
        'test_plan': ('rnd_test_plans', 'TEST'),
        'test_result': ('rnd_test_results', 'TRES'),
        'change': ('rnd_change_requests', 'CHG'),
        'risk': ('rnd_risks', 'RSK'),
        'issue': ('rnd_issues', 'ISS'),
        'action': ('rnd_action_items', 'ACT'),
        'cost': ('rnd_cost_estimates', 'COST'),
    }
    
    if entity_type not in patterns:
        return f'{entity_type.upper()}-{datetime.now().strftime("%Y%m%d%H%M%S")}'
    
    table_name, default_prefix = patterns[entity_type]
    prefix = prefix or default_prefix
    
    try:
        cursor.execute(f"""
            SELECT id FROM {table_name} 
            WHERE id = (SELECT MAX(id) FROM {table_name})
        """)
        result = cursor.fetchone()
        next_num = (result[0] + 1) if result else 1
        return f'{prefix}-{next_num:05d}'
    finally:
        db.close()


def log_plm_audit(entity_type: str, entity_id: int, action: str, user_id: int = None,
                   field_name: str = None, old_value: str = None, new_value: str = None,
                   notes: str = None, ip_address: str = None, company_id: int = None):
    """Log audit record for PLM entity changes."""
    db = get_db()
    try:
        db.execute("""
            INSERT INTO rnd_audit_records 
            (entity_type, entity_id, action, field_name, old_value, new_value, user_id, ip_address, notes, company_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (entity_type, entity_id, action, field_name, old_value, new_value, user_id, ip_address, notes, company_id, datetime.now().isoformat()))
        db.commit()
    finally:
        db.close()


# =============================================================================
# QUERY HELPERS
# =============================================================================

def get_one(sql: str, params: tuple = None) -> Optional[Dict]:
    """Fetch a single record."""
    db = get_db()
    try:
        cursor = db.execute(sql, params or ())
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        db.close()


def get_all(sql: str, params: tuple = None) -> List[Dict]:
    """Fetch all records."""
    db = get_db()
    try:
        cursor = db.execute(sql, params or ())
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        db.close()


def get_plm_stats() -> Dict:
    """Get PLM dashboard statistics."""
    db = get_db()
    try:
        cursor = db.cursor()
        
        stats = {}
        
        # Count ideas by status
        cursor.execute("""
            SELECT status, COUNT(*) as count FROM rnd_ideas 
            WHERE is_archived = 0 GROUP BY status
        """)
        stats['ideas_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
        stats['total_ideas'] = sum(stats['ideas_by_status'].values())
        
        # Count projects by stage
        cursor.execute("""
            SELECT stage, COUNT(*) as count FROM rnd_projects 
            WHERE is_archived = 0 AND status = 'Active' GROUP BY stage
        """)
        stats['projects_by_stage'] = {row['stage']: row['count'] for row in cursor.fetchall()}
        stats['active_projects'] = sum(stats['projects_by_stage'].values())
        
        # Count products by lifecycle state
        cursor.execute("""
            SELECT lifecycle_state, COUNT(*) as count FROM rnd_product_masters 
            WHERE is_archived = 0 GROUP BY lifecycle_state
        """)
        stats['products_by_lifecycle'] = {row['lifecycle_state']: row['count'] for row in cursor.fetchall()}
        
        # Count prototypes by status
        cursor.execute("""
            SELECT status, COUNT(*) as count FROM rnd_prototypes 
            WHERE is_archived = 0 GROUP BY status
        """)
        stats['prototypes_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Count tests pass/fail
        cursor.execute("""
            SELECT pass_fail, COUNT(*) as count FROM rnd_test_results GROUP BY pass_fail
        """)
        stats['test_results'] = {row['pass_fail']: row['count'] for row in cursor.fetchall()}
        
        # Count changes by status
        cursor.execute("""
            SELECT status, COUNT(*) as count FROM rnd_change_requests 
            WHERE is_archived = 0 GROUP BY status
        """)
        stats['changes_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Count risks and issues
        cursor.execute("SELECT status, COUNT(*) as count FROM rnd_risks WHERE is_archived = 0 GROUP BY status")
        stats['risks_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
        
        cursor.execute("SELECT status, COUNT(*) as count FROM rnd_issues WHERE is_archived = 0 GROUP BY status")
        stats['issues_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
        
        return stats
    finally:
        db.close()


def get_active_ideas(filter_status: str = None, search: str = None, 
                     company_id: int = None, branch_id: int = None,
                     limit: int = 50, offset: int = 0) -> List[Dict]:
    """Get active ideas with filtering."""
    db = get_db()
    try:
        sql = "SELECT * FROM rnd_ideas WHERE is_archived = 0"
        params = []
        
        if filter_status:
            sql += " AND status = ?"
            params.append(filter_status)
        
        if search:
            sql += " AND (title LIKE ? OR idea_number LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%'])
        
        if company_id:
            sql += " AND company_id = ?"
            params.append(company_id)
        
        if branch_id:
            sql += " AND branch_id = ?"
            params.append(branch_id)
        
        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = db.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        db.close()


def get_active_projects(filter_stage: str = None, filter_status: str = None,
                        search: str = None, company_id: int = None, branch_id: int = None,
                        limit: int = 50, offset: int = 0) -> List[Dict]:
    """Get active R&D projects with filtering."""
    db = get_db()
    try:
        sql = "SELECT * FROM rnd_projects WHERE is_archived = 0"
        params = []
        
        if filter_stage:
            sql += " AND stage = ?"
            params.append(filter_stage)
        
        if filter_status:
            sql += " AND status = ?"
            params.append(filter_status)
        
        if search:
            sql += " AND (project_name LIKE ? OR project_number LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%'])
        
        if company_id:
            sql += " AND company_id = ?"
            params.append(company_id)
        
        if branch_id:
            sql += " AND branch_id = ?"
            params.append(branch_id)
        
        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        cursor = db.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        db.close()


def get_product_revisions(product_id: int) -> List[Dict]:
    """Get all revisions for a product."""
    db = get_db()
    try:
        cursor = db.execute("""
            SELECT * FROM rnd_product_revisions 
            WHERE product_id = ? AND is_archived = 0 
            ORDER BY created_at DESC
        """, (product_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        db.close()


def get_bom_lines(bom_id: int) -> List[Dict]:
    """Get all lines for a BOM."""
    db = get_db()
    try:
        cursor = db.execute("""
            SELECT * FROM rnd_bom_lines 
            WHERE bom_id = ? 
            ORDER BY line_number
        """, (bom_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        db.close()


def get_spec_sections(spec_id: int) -> List[Dict]:
    """Get all sections for a specification."""
    db = get_db()
    try:
        cursor = db.execute("""
            SELECT * FROM rnd_specification_sections 
            WHERE spec_id = ? 
            ORDER BY sort_order
        """, (spec_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        db.close()


def get_project_stage_history(project_id: int) -> List[Dict]:
    """Get stage history for a project."""
    db = get_db()
    try:
        cursor = db.execute("""
            SELECT * FROM rnd_project_stage_history 
            WHERE project_id = ? 
            ORDER BY created_at ASC
        """, (project_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        db.close()


def get_release_checklist(readiness_id: int) -> List[Dict]:
    """Get checklist items for a release readiness record."""
    db = get_db()
    try:
        cursor = db.execute("""
            SELECT * FROM rnd_release_checklist_items 
            WHERE readiness_id = ? 
            ORDER BY sort_order
        """, (readiness_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        db.close()


def get_change_impacts(change_request_id: int) -> List[Dict]:
    """Get impacts for a change request."""
    db = get_db()
    try:
        cursor = db.execute("""
            SELECT * FROM rnd_change_impacts 
            WHERE change_request_id = ? 
            ORDER BY severity DESC
        """, (change_request_id,))
        return [dict(row) for row in cursor.fetchall()]
    finally:
        db.close()


# Run initialization when module is imported
if __name__ != '__main__':
    initialize_plm_schema()
