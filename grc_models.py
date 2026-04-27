"""
Governance, Risk & Compliance (GRC) Module - Database Models
=============================================================
Enterprise-grade GRC models for the MMDx platform covering:
- Governance Structures
- Risk Register & Assessments
- Control Library & Testing
- Compliance Obligations & Regulations
- Policy Management & Acknowledgements
- Segregation of Duties (SoD)
- Access Reviews
- Violations, Exceptions & Findings
- Remediation & CAPA Plans
- Evidence Repository
- Audit Readiness
- Incidents & Breaches
- Certifications & Renewals
- Alert Rules & Events
- High-Risk Activity Monitoring
- Approval Matrix Governance
- Framework Templates

Author: Enterprise Architecture Team
Version: 1.0.0
"""

import sqlite3
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else ''
DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'warehouse.db'))


def get_db():
    """Get database connection with Row factory for dict-like access."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db_context():
    """Context manager for database operations with automatic commit/rollback."""
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row) -> Dict:
    """Convert sqlite3.Row to dict."""
    return dict(row) if row else None


def rows_to_list(rows: List[sqlite3.Row]) -> List[Dict]:
    """Convert list of sqlite3.Row to list of dicts."""
    return [dict(row) for row in rows] if rows else []


# =============================================================================
# GRC TABLE DEFINITIONS
# =============================================================================

GRC_TABLES = [
    # -------------------------------------------------------------------------
    # 1. Governance Entities
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_governance_entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_code TEXT UNIQUE NOT NULL,
        entity_name TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        description TEXT,
        company_id INTEGER,
        branch_id INTEGER,
        department_id INTEGER,
        process_area TEXT,
        scope TEXT,
        owner_user_id INTEGER,
        reviewer_user_id INTEGER,
        approver_user_id INTEGER,
        compliance_officer_id INTEGER,
        risk_owner_id INTEGER,
        control_owner_id INTEGER,
        evidence_custodian_id INTEGER,
        audit_coordinator_id INTEGER,
        escalation_contact_id INTEGER,
        parent_entity_id INTEGER,
        is_active INTEGER DEFAULT 1,
        status TEXT DEFAULT 'active',
        effective_from DATE,
        effective_to DATE,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_by INTEGER
    )""",

    # -------------------------------------------------------------------------
    # 2. Risk Categories
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_risk_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_code TEXT UNIQUE NOT NULL,
        category_name TEXT NOT NULL,
        category_type TEXT,
        description TEXT,
        parent_id INTEGER,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 3. Risks
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_risks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        risk_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        category_id INTEGER,
        risk_type TEXT NOT NULL,
        entity_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        department_id INTEGER,
        business_unit TEXT,
        process_area TEXT,
        risk_owner_id INTEGER,
        reviewer_user_id INTEGER,
        impact_score INTEGER DEFAULT 3,
        likelihood_score INTEGER DEFAULT 3,
        inherent_risk_score INTEGER DEFAULT 9,
        control_effectiveness_score INTEGER DEFAULT 3,
        residual_risk_score INTEGER DEFAULT 3,
        status TEXT DEFAULT 'active',
        risk_status TEXT DEFAULT 'open',
        trigger_conditions TEXT,
        leading_indicators TEXT,
        due_date DATE,
        last_review_date DATE,
        next_review_date DATE,
        treatment_plan TEXT,
        risk_level TEXT DEFAULT 'medium',
        key_risk_indicator TEXT,
        is_critical INTEGER DEFAULT 0,
        is_watchlist INTEGER DEFAULT 0,
        related_party TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_by INTEGER,
        approved_at DATETIME,
        approved_by INTEGER,
        closed_at DATETIME,
        closed_by INTEGER
    )""",

    # -------------------------------------------------------------------------
    # 4. Risk Assessments
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_risk_assessments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        risk_id INTEGER NOT NULL,
        assessment_date DATE NOT NULL,
        assessor_user_id INTEGER NOT NULL,
        impact_score INTEGER,
        likelihood_score INTEGER,
        inherent_risk_score INTEGER,
        control_effectiveness_score INTEGER,
        residual_risk_score INTEGER,
        assessment_method TEXT,
        findings TEXT,
        recommendations TEXT,
        evidence_ref TEXT,
        status TEXT DEFAULT 'draft',
        approved_at DATETIME,
        approved_by INTEGER,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER
    )""",

    # -------------------------------------------------------------------------
    # 5. Risk Treatments
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_risk_treatments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        risk_id INTEGER NOT NULL,
        treatment_type TEXT NOT NULL,
        treatment_description TEXT,
        owner_user_id INTEGER,
        due_date DATE,
        status TEXT DEFAULT 'pending',
        completion_date DATE,
        effectiveness_rating INTEGER,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 6. Control Categories
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_control_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_code TEXT UNIQUE NOT NULL,
        category_name TEXT NOT NULL,
        category_type TEXT,
        description TEXT,
        parent_id INTEGER,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 7. Controls
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_controls (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        control_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        objective TEXT,
        description TEXT,
        control_type TEXT NOT NULL,
        nature TEXT DEFAULT 'manual',
        frequency TEXT DEFAULT 'quarterly',
        category_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        department_id INTEGER,
        owner_user_id INTEGER,
        reviewer_user_id INTEGER,
        approver_user_id INTEGER,
        evidence_requirement TEXT,
        operating_procedure_link TEXT,
        test_method TEXT,
        status TEXT DEFAULT 'active',
        key_control INTEGER DEFAULT 0,
        financial_control INTEGER DEFAULT 0,
        access_control INTEGER DEFAULT 0,
        inventory_control INTEGER DEFAULT 0,
        customs_compliance INTEGER DEFAULT 0,
        effectiveness_rating INTEGER,
        design_effectiveness INTEGER,
        operating_effectiveness INTEGER,
        last_test_date DATE,
        next_test_due_date DATE,
        version INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_by INTEGER
    )""",

    # -------------------------------------------------------------------------
    # 8. Control Assignments (Risk to Control Mapping)
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_control_assignments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        control_id INTEGER NOT NULL,
        risk_id INTEGER,
        regulation_id INTEGER,
        effective_from DATE,
        effective_to DATE,
        owner_user_id INTEGER,
        status TEXT DEFAULT 'active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER
    )""",

    # -------------------------------------------------------------------------
    # 9. Control Tests
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_control_tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_code TEXT UNIQUE NOT NULL,
        control_id INTEGER NOT NULL,
        test_date DATE NOT NULL,
        tester_user_id INTEGER NOT NULL,
        reviewer_user_id INTEGER,
        sample_size INTEGER,
        sample_selection_method TEXT,
        test_procedure TEXT,
        test_result TEXT,
        pass_count INTEGER,
        fail_count INTEGER,
        na_count INTEGER,
        effectiveness_rating INTEGER,
        observation_notes TEXT,
        evidence_ids TEXT,
        status TEXT DEFAULT 'in_progress',
        approval_status TEXT DEFAULT 'pending',
        approved_at DATETIME,
        approved_by INTEGER,
        next_test_date DATE,
        findings TEXT,
        recommendations TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 10. Control Test Results
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_control_test_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_id INTEGER NOT NULL,
        item_description TEXT,
        result TEXT NOT NULL,
        result_notes TEXT,
        evidence_ref TEXT,
        exception_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER
    )""",

    # -------------------------------------------------------------------------
    # 11. Compliance Obligations
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_compliance_obligations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        obligation_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        source_regulation_id INTEGER,
        jurisdiction TEXT,
        category TEXT,
        company_id INTEGER,
        branch_id INTEGER,
        department_id INTEGER,
        process_area TEXT,
        owner_user_id INTEGER,
        reviewer_user_id INTEGER,
        renewal_review_cycle TEXT,
        evidence_requirement TEXT,
        last_compliance_check DATE,
        next_compliance_review DATE,
        noncompliance_impact TEXT,
        status TEXT DEFAULT 'active',
        compliance_status TEXT DEFAULT 'compliant',
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_by INTEGER
    )""",

    # -------------------------------------------------------------------------
    # 12. Regulations
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_regulations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        regulation_code TEXT UNIQUE NOT NULL,
        regulation_name TEXT NOT NULL,
        authority TEXT,
        jurisdiction TEXT,
        effective_date DATE,
        review_date DATE,
        status TEXT DEFAULT 'active',
        summary TEXT,
        document_links TEXT,
        internal_owner_id INTEGER,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_by INTEGER
    )""",

    # -------------------------------------------------------------------------
    # 13. Policy Documents
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_policy_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT,
        owner_user_id INTEGER,
        approver_user_id INTEGER,
        category_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        department_id INTEGER,
        applicability TEXT,
        acknowledgement_required INTEGER DEFAULT 0,
        version INTEGER DEFAULT 1,
        status TEXT DEFAULT 'draft',
        effective_date DATE,
        next_review_date DATE,
        review_cycle TEXT,
        superseded_by_id INTEGER,
        document_url TEXT,
        related_regulation_ids TEXT,
        related_control_ids TEXT,
        related_risk_ids TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_by INTEGER
    )""",

    # -------------------------------------------------------------------------
    # 14. Policy Versions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_policy_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_id INTEGER NOT NULL,
        version_number INTEGER NOT NULL,
        document_url TEXT,
        changelog TEXT,
        status TEXT DEFAULT 'draft',
        approved_at DATETIME,
        approved_by INTEGER,
        effective_date DATE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER
    )""",

    # -------------------------------------------------------------------------
    # 15. Policy Acknowledgements
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_policy_acknowledgements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        policy_id INTEGER NOT NULL,
        policy_version_id INTEGER,
        user_id INTEGER NOT NULL,
        acknowledged_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        due_date DATE,
        status TEXT DEFAULT 'pending',
        comments TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 16. SoD Rules
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_sod_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_code TEXT UNIQUE NOT NULL,
        rule_name TEXT NOT NULL,
        description TEXT,
        conflict_pair_module_a TEXT,
        conflict_pair_action_a TEXT,
        conflict_pair_module_b TEXT,
        conflict_pair_action_b TEXT,
        risk_severity TEXT DEFAULT 'high',
        mitigation_options TEXT,
        is_active INTEGER DEFAULT 1,
        exception_requires_approval INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 17. SoD Conflicts
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_sod_conflicts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_id INTEGER NOT NULL,
        user_id INTEGER,
        role_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        department_id INTEGER,
        detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'open',
        resolution TEXT,
        resolution_notes TEXT,
        exception_id INTEGER,
        approved_at DATETIME,
        approved_by INTEGER,
        expiry_date DATE,
        Mitigating_control_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER
    )""",

    # -------------------------------------------------------------------------
    # 18. Access Reviews
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_access_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        review_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        review_cycle TEXT,
        scope_company_ids TEXT,
        scope_branch_ids TEXT,
        scope_department_ids TEXT,
        scope_module TEXT,
        scope_role_ids TEXT,
        scope_privileged_only INTEGER DEFAULT 0,
        reviewer_user_id INTEGER,
        due_date DATE,
        status TEXT DEFAULT 'planned',
        completion_date DATE,
        total_users INTEGER DEFAULT 0,
        reviewed_users INTEGER DEFAULT 0,
        approved_users INTEGER DEFAULT 0,
        revoked_users INTEGER DEFAULT 0,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 19. Access Review Items
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_access_review_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        review_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        role_id INTEGER,
        permission TEXT,
        resource TEXT,
        module TEXT,
        decision TEXT,
        decision_notes TEXT,
        decision_by INTEGER,
        decided_at DATETIME,
        status TEXT DEFAULT 'pending',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 20. Exceptions
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_exceptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exception_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        exception_type TEXT NOT NULL,
        severity TEXT DEFAULT 'medium',
        source TEXT,
        owner_user_id INTEGER,
        approver_user_id INTEGER,
        status TEXT DEFAULT 'open',
        business_justification TEXT,
        compensating_controls TEXT,
        start_date DATE,
        expiry_date DATE,
        close_date DATE,
        closed_by INTEGER,
        evidence_ids TEXT,
        risk_id INTEGER,
        control_id INTEGER,
        policy_id INTEGER,
        user_id INTEGER,
        transaction_ref TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_by INTEGER
    )""",

    # -------------------------------------------------------------------------
    # 21. Findings
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_findings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        finding_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        source TEXT,
        source_id INTEGER,
        severity TEXT DEFAULT 'medium',
        root_cause TEXT,
        impact TEXT,
        recommendation TEXT,
        owner_user_id INTEGER,
        reviewer_user_id INTEGER,
        status TEXT DEFAULT 'open',
        target_closure_date DATE,
        actual_closure_date DATE,
        validation_result TEXT,
        validation_notes TEXT,
        validated_by INTEGER,
        validated_at DATETIME,
        reopened INTEGER DEFAULT 0,
        reopen_reason TEXT,
        related_risk_ids TEXT,
        related_control_ids TEXT,
        related_incident_ids TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        closed_by INTEGER,
        closed_at DATETIME
    )""",

    # -------------------------------------------------------------------------
    # 22. Remediation Plans
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_remediation_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        finding_id INTEGER,
        exception_id INTEGER,
        owner_user_id INTEGER,
        reviewer_user_id INTEGER,
        status TEXT DEFAULT 'draft',
        priority TEXT DEFAULT 'medium',
        progress_percent INTEGER DEFAULT 0,
        start_date DATE,
        target_date DATE,
        completion_date DATE,
        blocking_issues TEXT,
        verification_step TEXT,
        closure_approval TEXT,
        closure_notes TEXT,
        approved_at DATETIME,
        approved_by INTEGER,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_by INTEGER
    )""",

    # -------------------------------------------------------------------------
    # 23. Remediation Tasks
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_remediation_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        plan_id INTEGER NOT NULL,
        task_description TEXT NOT NULL,
        owner_user_id INTEGER,
        milestone TEXT,
        due_date DATE,
        completion_date DATE,
        status TEXT DEFAULT 'pending',
        progress_percent INTEGER DEFAULT 0,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 24. Evidence Items
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_evidence_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        evidence_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        evidence_type TEXT,
        linked_entity_type TEXT,
        linked_entity_id INTEGER,
        file_url TEXT,
        file_name TEXT,
        file_size INTEGER,
        uploader_user_id INTEGER,
        reviewer_user_id INTEGER,
        review_status TEXT DEFAULT 'pending',
        validity_period_from DATE,
        validity_period_to DATE,
        tags TEXT,
        version INTEGER DEFAULT 1,
        is_expired INTEGER DEFAULT 0,
        expiry_alert_sent INTEGER DEFAULT 0,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 25. Audit Preparedness Checks
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_audit_preparedness_checks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        check_code TEXT UNIQUE NOT NULL,
        audit_type TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        template_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        owner_user_id INTEGER,
        due_date DATE,
        status TEXT DEFAULT 'pending',
        completeness_score INTEGER DEFAULT 0,
        checked_items INTEGER DEFAULT 0,
        passed_items INTEGER DEFAULT 0,
        failed_items INTEGER DEFAULT 0,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 26. Incidents
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_incidents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        incident_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        category TEXT NOT NULL,
        source TEXT,
        incident_datetime DATETIME,
        discovered_by INTEGER,
        affected_entity_type TEXT,
        affected_entity_id INTEGER,
        affected_module TEXT,
        severity TEXT DEFAULT 'medium',
        impact_summary TEXT,
        root_cause TEXT,
        related_user_id INTEGER,
        related_role_id INTEGER,
        related_transaction_ref TEXT,
        related_api_ref TEXT,
        related_session_id TEXT,
        related_document_id INTEGER,
        related_integration_id INTEGER,
        evidence_ids TEXT,
        response_owner_id INTEGER,
        status TEXT DEFAULT 'open',
        resolution TEXT,
        closure_datetime DATETIME,
        closed_by INTEGER,
        remediation_plan_id INTEGER,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_by INTEGER
    )""",

    # -------------------------------------------------------------------------
    # 27. Certifications
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_certifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        certification_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        authority TEXT,
        scope TEXT,
        owner_user_id INTEGER,
        issue_date DATE,
        expiry_date DATE,
        reminder_window_days INTEGER DEFAULT 30,
        renewal_status TEXT DEFAULT 'valid',
        document_url TEXT,
        compliance_impact TEXT,
        related_obligation_ids TEXT,
        status TEXT DEFAULT 'active',
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_by INTEGER
    )""",

    # -------------------------------------------------------------------------
    # 28. Deadlines
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_deadlines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deadline_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        deadline_type TEXT NOT NULL,
        linked_entity_type TEXT,
        linked_entity_id INTEGER,
        owner_user_id INTEGER,
        due_date DATETIME NOT NULL,
        status TEXT DEFAULT 'open',
        reminder_sent INTEGER DEFAULT 0,
        last_reminder_at DATETIME,
        completion_date DATETIME,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER
    )""",

    # -------------------------------------------------------------------------
    # 29. Alert Rules
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_alert_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_code TEXT UNIQUE NOT NULL,
        rule_name TEXT NOT NULL,
        description TEXT,
        alert_type TEXT NOT NULL,
        condition_expression TEXT,
        severity TEXT DEFAULT 'medium',
        owner_user_id INTEGER,
        notification_channel TEXT,
        notification_recipients TEXT,
        is_active INTEGER DEFAULT 1,
        check_frequency TEXT DEFAULT 'daily',
        last_check_at DATETIME,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 30. Alert Events
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_alert_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_id INTEGER NOT NULL,
        triggered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        severity TEXT,
        title TEXT NOT NULL,
        message TEXT,
        entity_type TEXT,
        entity_id INTEGER,
        acknowledged INTEGER DEFAULT 0,
        acknowledged_at DATETIME,
        acknowledged_by INTEGER,
        resolved INTEGER DEFAULT 0,
        resolved_at DATETIME,
        resolved_by INTEGER,
        notes TEXT
    )""",

    # -------------------------------------------------------------------------
    # 31. High Risk Events
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_high_risk_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_code TEXT UNIQUE NOT NULL,
        event_type TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        detected_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        detected_by INTEGER,
        severity TEXT DEFAULT 'medium',
        user_id INTEGER,
        role_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        department_id INTEGER,
        module TEXT,
        activity TEXT,
        ip_address TEXT,
        session_id TEXT,
        transaction_ref TEXT,
        risk_indicators TEXT,
        status TEXT DEFAULT 'detected',
        review_status TEXT DEFAULT 'pending',
        reviewed_by INTEGER,
        reviewed_at DATETIME,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 32. Approval Matrix Rules
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_approval_matrix_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_code TEXT UNIQUE NOT NULL,
        module TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        description TEXT,
        company_id INTEGER,
        branch_id INTEGER,
        department_id INTEGER,
        amount_threshold_min REAL,
        amount_threshold_max REAL,
        risk_level TEXT,
        requester_role_id INTEGER,
        approver_role_id INTEGER,
        approval_sequence INTEGER DEFAULT 1,
        fallback_approver_ids TEXT,
        escalation_path TEXT,
        is_active INTEGER DEFAULT 1,
        effective_from DATE,
        effective_to DATE,
        version INTEGER DEFAULT 1,
        bypass_logging_required INTEGER DEFAULT 1,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 33. Framework Templates
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_framework_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_code TEXT UNIQUE NOT NULL,
        template_name TEXT NOT NULL,
        framework_type TEXT NOT NULL,
        description TEXT,
        content TEXT,
        version INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER
    )""",

    # -------------------------------------------------------------------------
    # 34. Entity Links
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_entity_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_entity_type TEXT NOT NULL,
        source_entity_id INTEGER NOT NULL,
        target_entity_type TEXT NOT NULL,
        target_entity_id INTEGER NOT NULL,
        link_type TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER
    )""",

    # -------------------------------------------------------------------------
    # 35. Status History
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_status_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        entity_id INTEGER NOT NULL,
        old_status TEXT,
        new_status TEXT,
        changed_by INTEGER,
        changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        notes TEXT
    )""",

    # -------------------------------------------------------------------------
    # 36. Notes
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        entity_id INTEGER NOT NULL,
        note_text TEXT NOT NULL,
        is_internal INTEGER DEFAULT 1,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 37. Watchlists
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_watchlists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_type TEXT NOT NULL,
        entity_id INTEGER NOT NULL,
        watchlist_type TEXT,
        user_id INTEGER NOT NULL,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 38. Report Presets
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_report_presets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        preset_code TEXT UNIQUE NOT NULL,
        report_type TEXT NOT NULL,
        title TEXT NOT NULL,
        filters TEXT,
        columns TEXT,
        sort_by TEXT,
        group_by TEXT,
        is_default INTEGER DEFAULT 0,
        user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",

    # -------------------------------------------------------------------------
    # 39. Export Jobs
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_export_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_code TEXT UNIQUE NOT NULL,
        export_type TEXT NOT NULL,
        report_type TEXT,
        filters TEXT,
        columns TEXT,
        file_format TEXT,
        file_url TEXT,
        status TEXT DEFAULT 'pending',
        requested_by INTEGER,
        requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME,
        record_count INTEGER,
        file_size INTEGER,
        notes TEXT
    )""",

    # -------------------------------------------------------------------------
    # 40. Review Cycles
    # -------------------------------------------------------------------------
    """CREATE TABLE IF NOT EXISTS grc_review_cycles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cycle_code TEXT UNIQUE NOT NULL,
        cycle_name TEXT NOT NULL,
        cycle_type TEXT NOT NULL,
        description TEXT,
        frequency TEXT,
        start_date DATE,
        end_date DATE,
        status TEXT DEFAULT 'planned',
        owner_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_by INTEGER
    )""",
]


# =============================================================================
# TABLE INITIALIZATION
# =============================================================================

def init_grc_tables():
    """Initialize all GRC tables."""
    conn = get_db()
    cursor = conn.cursor()
    for table_sql in GRC_TABLES:
        cursor.execute(table_sql)

    # Migrate: add category_type column if missing (for existing tables)
    try:
        cursor.execute("ALTER TABLE grc_control_categories ADD COLUMN category_type TEXT")
    except Exception:
        pass  # column already exists

    conn.commit()
    conn.close()


# =============================================================================
# SEED DATA FUNCTIONS
# =============================================================================

def seed_grc_initial_data():
    """Seed initial GRC lookup data."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Seed Risk Categories
    risk_categories = [
        ('RISK_OPS', 'Operational Risk', 'operational'),
        ('RISK_FIN', 'Financial Risk', 'financial'),
        ('RISK_COMP', 'Compliance Risk', 'compliance'),
        ('RISK_IT', 'IT / Cyber Risk', 'it'),
        ('RISK_HR', 'HR / Personnel Risk', 'hr'),
        ('RISK_LGL', 'Legal / Regulatory Risk', 'legal'),
        ('RISK_LOG', 'Logistics / Supply Chain Risk', 'logistics'),
        ('RISK_SUPP', 'Supplier / Vendor Risk', 'supplier'),
        ('RISK_INV', 'Inventory / Asset Risk', 'inventory'),
        ('RISK_CUS', 'Customs / Trade Compliance Risk', 'customs'),
        ('RISK_DATA', 'Data Privacy Risk', 'data_privacy'),
        ('RISK_FRAUD', 'Fraud Risk', 'fraud'),
        ('RISK_ACC', 'Access / Security Risk', 'access'),
        ('RISK_SAFETY', 'Safety / Environment Risk', 'safety'),
    ]
    
    for code, name, cat_type in risk_categories:
        cursor.execute("""
            INSERT OR IGNORE INTO grc_risk_categories (category_code, category_name, category_type, is_active)
            VALUES (?, ?, ?, 1)
        """, (code, name, cat_type))
    
    # Seed Control Categories
    control_categories = [
        ('CTRL_PRE', 'Preventive Controls', 'preventive'),
        ('CTRL_DET', 'Detective Controls', 'detective'),
        ('CTRL_COR', 'Corrective Controls', 'corrective'),
        ('CTRL_MAN', 'Manual Controls', 'manual'),
        ('CTRL_AUTO', 'Automated Controls', 'automated'),
        ('CTRL_HYB', 'Hybrid Controls', 'hybrid'),
    ]
    
    for code, name, cat_type in control_categories:
        cursor.execute("""
            INSERT OR IGNORE INTO grc_control_categories (category_code, category_name, category_type, is_active)
            VALUES (?, ?, ?, 1)
        """, (code, name, cat_type))
    
    # Seed Framework Templates
    templates = [
        ('TPL_SOX', 'SOX Compliance Framework', 'financial', 'Standard Sarbanes-Oxley control framework for financial reporting.'),
        ('TPL_ISO27001', 'ISO 27001 ISMS Framework', 'security', 'Information Security Management System based on ISO 27001.'),
        ('TPL_PCI_DSS', 'PCI DSS Compliance', 'payment', 'Payment Card Industry Data Security Standard controls.'),
        ('TPL GDPR', 'GDPR Data Privacy Framework', 'privacy', 'General Data Protection Regulation compliance controls.'),
        ('TPL_HIPAA', 'HIPAA Healthcare Framework', 'healthcare', 'Health Insurance Portability and Accountability Act controls.'),
        ('TPL_CUSTOMS', 'Customs Compliance Framework', 'customs', 'International trade and customs compliance controls.'),
    ]
    
    for code, name, ftype, desc in templates:
        cursor.execute("""
            INSERT OR IGNORE INTO grc_framework_templates (template_code, template_name, framework_type, description, is_active)
            VALUES (?, ?, ?, ?, 1)
        """, (code, name, ftype, desc))
    
    conn.commit()
    conn.close()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_grc_next_code(entity_prefix: str) -> str:
    """Generate next GRC entity code."""
    conn = get_db()
    cursor = conn.cursor()
    year = datetime.now().strftime('%Y')
    prefix = f"GRC-{entity_prefix}-{year}"
    cursor.execute(f"""
        SELECT COUNT(*) + 1 as next_num FROM grc_* 
        WHERE entity_code LIKE ?
    """, (f"{prefix}%",))
    result = cursor.fetchone()
    conn.close()
    return f"{prefix}-{result['next_num']:04d}" if result else f"{prefix}-0001"


def calculate_risk_score(impact: int, likelihood: int) -> int:
    """Calculate risk score from impact and likelihood."""
    return impact * likelihood


def get_grc_stats(company_id: int = None) -> Dict:
    """Get GRC dashboard statistics."""
    conn = get_db()
    cursor = conn.cursor()
    
    stats = {}
    
    # Total risks
    cursor.execute("SELECT COUNT(*) as cnt FROM grc_risks WHERE status = 'active'")
    stats['total_risks'] = cursor.fetchone()['cnt']
    
    # High risks
    cursor.execute("SELECT COUNT(*) as cnt FROM grc_risks WHERE status = 'active' AND risk_level = 'high'")
    stats['high_risks'] = cursor.fetchone()['cnt']
    
    # Total controls
    cursor.execute("SELECT COUNT(*) as cnt FROM grc_controls WHERE status = 'active'")
    stats['total_controls'] = cursor.fetchone()['cnt']
    
    # Overdue control tests
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM grc_control_tests 
        WHERE status IN ('in_progress', 'pending') AND next_test_date < date('now')
    """)
    stats['overdue_tests'] = cursor.fetchone()['cnt']
    
    # Open findings
    cursor.execute("SELECT COUNT(*) as cnt FROM grc_findings WHERE status = 'open'")
    stats['open_findings'] = cursor.fetchone()['cnt']
    
    # SoD conflicts
    cursor.execute("SELECT COUNT(*) as cnt FROM grc_sod_conflicts WHERE status = 'open'")
    stats['sod_conflicts'] = cursor.fetchone()['cnt']
    
    # Open exceptions
    cursor.execute("SELECT COUNT(*) as cnt FROM grc_exceptions WHERE status IN ('open', 'approved')")
    stats['open_exceptions'] = cursor.fetchone()['cnt']
    
    # Expiring certifications (within 30 days)
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM grc_certifications 
        WHERE renewal_status = 'valid' AND expiry_date BETWEEN date('now') AND date('now', '+30 days')
    """)
    stats['expiring_certs'] = cursor.fetchone()['cnt']
    
    conn.close()
    return stats
