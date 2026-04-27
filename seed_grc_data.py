"""
GRC Module - Comprehensive Seed Data
====================================
Seeds realistic GRC data for demo/development purposes.
"""

import sqlite3
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else ''
DATABASE_PATH = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'warehouse.db'))


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def seed_grc_comprehensive_data():
    """Seed comprehensive GRC data for demo purposes."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as cnt FROM grc_risks")
    if cursor.fetchone()['cnt'] > 0:
        print("[GRC Seed] Data already exists, skipping...")
        conn.close()
        return

    print("[GRC Seed] Seeding comprehensive GRC data...")

    # =================================================================
    # GOVERNANCE ENTITIES
    # =================================================================
    governance_data = [
        ('GE-001', 'Headquarters', 'company', 'Main headquarters governance entity', 1),
        ('GE-002', 'Warehouse A', 'branch', 'Primary warehouse operations', 1),
        ('GE-003', 'Warehouse B', 'branch', 'Secondary warehouse operations', 1),
        ('GE-004', 'Finance Department', 'department', 'Financial operations and controls', 1),
        ('GE-005', 'Procurement Department', 'department', 'Vendor management and purchasing', 1),
        ('GE-006', 'HR Department', 'department', 'Human resources management', 1),
        ('GE-007', 'IT Department', 'department', 'Technology and systems', 1),
        ('GE-008', 'Operations', 'process', 'Core operational processes', 1),
        ('GE-009', 'Customs & Compliance', 'process', 'Trade compliance and customs', 1),
        ('GE-010', 'Sales & Distribution', 'function', 'Sales operations', 1),
    ]

    for code, name, etype, desc, company_id in governance_data:
        cursor.execute("""
            INSERT INTO grc_governance_entities (
                entity_code, entity_name, entity_type, description, company_id,
                status, owner_user_id, compliance_officer_id, risk_owner_id, control_owner_id, created_at
            ) VALUES (?, ?, ?, ?, ?, 'active', 1, 1, 1, 1, datetime('now'))
        """, (code, name, etype, desc, company_id))

    # =================================================================
    # RISKS
    # =================================================================
    risks_data = [
        ('RSK-2026-001', 'Unauthorized Vendor Creation', 'Financial fraud through fake vendor setup', 'operational', 1, 'high', 5, 4, 20, 6, 'open', 'Users creating vendors without proper approval chain', 'Multiple vendor creation by single user', None, 'Implement SoD between vendor creation and approval'),
        ('RSK-2026-002', 'Customs Documentation Fraud', 'False customs declarations to avoid duties', 'customs', 1, 'high', 5, 3, 15, 6, 'open', 'Undervaluation of imports', 'Repeated undervaluation patterns detected', None, 'Enhanced customs control testing'),
        ('RSK-2026-003', 'Segregation of Duties Violation - Finance', 'User can create and approve own payments', 'access', 1, 'high', 5, 4, 20, 10, 'open', 'Single user with excessive privileges', 'Payment creation and approval by same user', None, 'Restrict payment approval to different role'),
        ('RSK-2026-004', 'Inventory Theft', 'Warehouse stock being diverted', 'inventory', 1, 'high', 4, 5, 20, 6, 'open', 'High-value items missing', 'Stock count discrepancies > 2%', None, 'Implement segregation of receiving and inventory management'),
        ('RSK-2026-005', 'Data Export Abuse', 'Bulk export of sensitive customer data', 'data_privacy', 1, 'high', 5, 2, 10, 5, 'open', 'Unusual data export activity', 'Large exports by users not in data analyst role', None, 'Monitor and restrict data exports'),
        ('RSK-2026-006', 'Policy Non-Compliance', 'Policies not acknowledged by staff', 'compliance', 1, 'medium', 3, 4, 12, 4, 'open', 'Overdue policy acknowledgements', '10+ policies unacknowledged > 30 days', None, 'Send reminders and escalate to management'),
        ('RSK-2026-007', 'Control Testing Backlog', 'Control tests overdue for execution', 'operational', 1, 'medium', 3, 4, 12, 4, 'open', 'Quarterly tests not completed', '15 control tests overdue', None, 'Complete overdue tests and update calendar'),
        ('RSK-2026-008', 'Supplier Compliance Gap', 'Key suppliers not meeting compliance requirements', 'supplier', 1, 'medium', 3, 3, 9, 4, 'open', 'ISO certifications expiring', '3 critical suppliers with expired certs', None, 'Renew certifications or find alternative suppliers'),
        ('RSK-2026-009', 'Access Review Backlog', 'Privileged access not reviewed', 'access', 1, 'medium', 4, 3, 12, 6, 'open', '90+ days since last access review', 'Admin accounts not reviewed in Q1', None, 'Complete quarterly access review cycle'),
        ('RSK-2026-010', 'Approval Bypass - Procurement', 'Large PO approved by single approver', 'operational', 1, 'medium', 4, 3, 12, 4, 'open', 'Amount threshold exceeded', 'PO > $100K with single approval', None, 'Implement dual approval for high-value POs'),
        ('RSK-2026-011', 'Documentation Gap', 'Missing operating procedures', 'operational', 1, 'low', 2, 3, 6, 2, 'open', 'SOPs not updated', '3 departments with outdated documentation', None, 'Update standard operating procedures'),
        ('RSK-2026-012', 'Training Completion', 'Mandatory training not completed', 'hr', 1, 'low', 2, 4, 8, 3, 'open', 'Compliance training overdue', '20% staff missing annual compliance training', None, 'Schedule and track mandatory training completion'),
        ('RSK-2026-013', 'Certifications Renewal', 'Professional certifications expiring', 'legal', 1, 'low', 2, 3, 6, 3, 'open', 'Certification expiry approaching', '2 certifications expiring within 60 days', None, 'Initiate renewal process'),
    ]

    for r in risks_data:
        cursor.execute("""
            INSERT INTO grc_risks (
                risk_code, title, description, risk_type, company_id, risk_level,
                impact_score, likelihood_score, inherent_risk_score, residual_risk_score,
                status, trigger_conditions, leading_indicators, due_date, treatment_plan, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), 1)
        """, r)

    # =================================================================
    # CONTROLS
    # =================================================================
    controls_data = [
        ('CTL-001', 'Vendor Creation Approval', 'All vendor creations must be approved by department head', 'preventive', 'manual', 'event-driven', 1, 'Vendor Master Policy', 'Analytical: Compare new vendors against black list', 3, 1, 1, 0, 0, 0, 1),
        ('CTL-002', 'Payment Approval Segregation', 'Payment creators cannot approve their own payments', 'preventive', 'automated', 'event-driven', 1, 'Payment Control Policy', 'System-enforced: Role-based approval restriction', 3, 1, 1, 0, 1, 0, 1),
        ('CTL-003', 'Inventory Cycle Count', 'Monthly physical inventory count with variance analysis', 'detective', 'hybrid', 'monthly', 1, 'Inventory Control Policy', 'Physical: Full count vs system; Analytical: Variance > 2%', 3, 1, 1, 1, 0, 1, 1),
        ('CTL-004', 'Customs Declaration Review', '100% review of customs documentation by compliance', 'detective', 'manual', 'weekly', 1, 'Customs Compliance Policy', 'Documentary: Check commercial invoices vs customs declarations', 3, 1, 1, 0, 0, 1, 1),
        ('CTL-005', 'Access Review Quarterly', 'Quarterly review of all privileged user access', 'detective', 'manual', 'quarterly', 1, 'Access Control Policy', 'Review user access lists vs business requirements', 3, 1, 1, 1, 1, 0, 1),
        ('CTL-006', 'Data Export Monitoring', 'Monitor and alert on bulk data exports', 'detective', 'automated', 'real-time', 1, 'Data Privacy Policy', 'System: Log and alert exports > 1000 records', 3, 1, 1, 0, 1, 0, 1),
        ('CTL-007', 'PO Approval Threshold', 'POs > $50K require dual approval', 'preventive', 'automated', 'event-driven', 1, 'Procurement Policy', 'System-enforced: Block single approval for high-value POs', 3, 1, 1, 0, 1, 0, 1),
        ('CTL-008', 'Policy Acknowledgement Tracking', 'Track and escalate unacknowledged policies', 'detective', 'manual', 'weekly', 1, 'Policy Management Policy', 'Report: List policies unacknowledged > 30 days', 3, 1, 1, 0, 0, 0, 1),
        ('CTL-009', 'Supplier Certification Verification', 'Annual verification of supplier certifications', 'preventive', 'manual', 'annual', 1, 'Supplier Management Policy', 'Documentary: Collect and verify ISO/compliance certs', 3, 1, 1, 0, 0, 1, 1),
        ('CTL-010', 'Control Test Calendar', 'Annual control testing calendar with reminders', 'detective', 'manual', 'quarterly', 1, 'Testing Policy', 'Review: Monitor test completion vs calendar', 3, 1, 1, 0, 0, 0, 1),
        ('CTL-011', 'Segregation of Duties Matrix', 'Maintain and enforce SoD conflict matrix', 'preventive', 'system', 'real-time', 1, 'SoD Policy', 'System-enforced: Prevent conflicting role combinations', 3, 1, 1, 0, 1, 0, 1),
        ('CTL-012', 'Training Completion Tracking', 'Track mandatory training completion per employee', 'detective', 'manual', 'monthly', 1, 'HR Compliance Policy', 'Report: List staff with overdue mandatory training', 3, 1, 1, 0, 0, 0, 1),
    ]

    for c in controls_data:
        cursor.execute("""
            INSERT INTO grc_controls (
                control_code, title, objective, control_type, nature, frequency,
                key_control, evidence_requirement, test_method, effectiveness_rating,
                design_effectiveness, operating_effectiveness, financial_control,
                access_control, inventory_control, customs_compliance,
                status, is_active, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', 1, datetime('now'), 1)
        """, c)

    # =================================================================
    # CONTROL TESTS
    # =================================================================
    now = datetime.now()
    tests_data = [
        ('TST-2026-001', 1, (now - timedelta(days=5)).strftime('%Y-%m-%d'), 1, 10, 'Review vendor creation logs', 'pass', 10, 0, 0, 5, 'All vendor creations properly approved', None, 'completed', (now + timedelta(days=90)).strftime('%Y-%m-%d')),
        ('TST-2026-002', 2, (now - timedelta(days=10)).strftime('%Y-%m-%d'), 1, 15, 'Sample payments to verify different approver', 'fail', 12, 3, 0, 2, '3 payments approved by creator', 'Exception needed', 'in_progress', (now + timedelta(days=20)).strftime('%Y-%m-%d')),
        ('TST-2026-003', 3, (now - timedelta(days=15)).strftime('%Y-%m-%d'), 1, 8, 'Full inventory count with variance', 'pass', 8, 0, 0, 5, 'Variances within acceptable threshold', None, 'completed', (now + timedelta(days=30)).strftime('%Y-%m-%d')),
        ('TST-2026-004', 4, (now - timedelta(days=7)).strftime('%Y-%m-%d'), 1, 25, 'Review customs documentation', 'partial', 20, 3, 2, 3, '2 declarations with discrepancies', 'Investigation ongoing', 'in_progress', (now + timedelta(days=7)).strftime('%Y-%m-%d')),
        ('TST-2026-005', 5, (now - timedelta(days=60)).strftime('%Y-%m-%d'), 1, 20, 'Review privileged user access', 'fail', 15, 5, 0, 2, '5 accounts with excessive privileges', 'Remediation plan created', 'pending', (now - timedelta(days=5)).strftime('%Y-%m-%d')),
        ('TST-2026-006', 7, (now - timedelta(days=3)).strftime('%Y-%m-%d'), 1, 12, 'Sample high-value POs', 'pass', 12, 0, 0, 5, 'All POs properly dual-approved', None, 'completed', (now + timedelta(days=87)).strftime('%Y-%m-%d')),
    ]

    for t in tests_data:
        cursor.execute("""
            INSERT INTO grc_control_tests (
                test_code, control_id, test_date, tester_user_id, reviewer_user_id, sample_size,
                sample_selection_method, test_procedure, test_result, pass_count, fail_count, na_count,
                effectiveness_rating, observation_notes, evidence_ids, status,
                next_test_date, approval_status, approved_at, approved_by,
                findings, recommendations, notes, created_at, created_by, updated_at
            ) VALUES (?, ?, ?, ?, NULL, ?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', NULL, NULL, NULL, NULL, NULL, datetime('now'), 1, CURRENT_TIMESTAMP)
        """, t)

    # =================================================================
    # COMPLIANCE OBLIGATIONS
    # =================================================================
    obls_data = [
        ('OBL-2026-001', 'SOX Section 404 - Financial Controls', 'Annual assessment of financial reporting controls', 1, 'US', 'Federal', 'financial_reporting', 1, datetime.now().strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'), 'High', 'compliant'),
        ('OBL-2026-002', 'GDPR Article 30 - Records of Processing', 'Maintain records of all data processing activities', 1, 'EU', 'Regulation', 'data_privacy', 1, datetime.now().strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d'), 'Medium', 'compliant'),
        ('OBL-2026-003', 'PCI DSS Requirement 12 - Security Policy', 'Annual review of security policies', 1, 'US', 'Standard', 'payment_security', 1, datetime.now().strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'), 'High', 'in_progress'),
        ('OBL-2026-004', 'Customs Record Keeping', 'Retain customs documentation for 5 years', 1, 'AE', 'Federal', 'trade_compliance', 1, datetime.now().strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'), 'Medium', 'compliant'),
        ('OBL-2026-005', 'ISO 27001 Control Review', 'Annual review of information security controls', 1, 'Global', 'Standard', 'information_security', 1, datetime.now().strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d'), 'High', 'in_progress'),
        ('OBL-2026-006', 'Anti-Money Laundering Compliance', 'KYC and AML monitoring requirements', 1, 'Global', 'Regulation', 'financial_crime', 1, datetime.now().strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'), 'Critical', 'compliant'),
    ]

    for o in obls_data:
        # Map 12-element tuple to 17 columns:
        # [0]obligation_code [1]title [2]desc [3]company_id [4]jurisdiction [5]category
        # [6]process_area [7]owner_user_id [8]last_check [9]next_review [10]impact [11]compliance_status
        row = (
            o[0], o[1], o[2],                                    # obligation_code, title, description
            o[3], o[4], o[5],                                    # company_id, jurisdiction, category
            None, None, o[6], o[7],                              # branch_id, department_id, process_area, owner_user_id
            'annual', None,                                       # renewal_review_cycle, evidence_requirement
            o[8], o[9], o[10], o[11],                            # last_check, next_review, noncompliance_impact, compliance_status
            'active'                                              # status
        )
        cursor.execute("""
            INSERT INTO grc_compliance_obligations (
                obligation_code, title, description, company_id, jurisdiction, category,
                branch_id, department_id, process_area, owner_user_id,
                renewal_review_cycle, evidence_requirement,
                last_compliance_check, next_compliance_review, noncompliance_impact,
                compliance_status, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, row)

    # =================================================================
    # REGULATIONS
    # =================================================================
    regs_data = [
        ('REG-001', 'Sarbanes-Oxley Act (SOX)', 'SEC', 'US', '2002-07-30', 'active', 'Financial reporting internal controls'),
        ('REG-002', 'General Data Protection Regulation (GDPR)', 'EU Parliament', 'EU', '2018-05-25', 'active', 'Data protection and privacy regulation'),
        ('REG-003', 'PCI Data Security Standard', 'PCI SSC', 'US', '2004-01-01', 'active', 'Payment card data security'),
        ('REG-004', 'UAE Customs Federal Law No. 8', 'UAE Customs', 'UAE', '1993-01-01', 'active', 'Customs procedures and record keeping'),
        ('REG-005', 'ISO/IEC 27001:2022', 'ISO', 'International', '2022-10-01', 'active', 'Information security management'),
        ('REG-006', 'FATF Guidelines', 'FATF', 'International', '2012-02-01', 'active', 'Anti-money laundering guidelines'),
    ]

    for r in regs_data:
        cursor.execute("""
            INSERT INTO grc_regulations (
                regulation_code, regulation_name, authority, jurisdiction,
                effective_date, status, summary, review_date, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (*r, (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')))

    # =================================================================
    # POLICIES
    # =================================================================
    pols_data = [
        ('POL-001', 'Vendor Management Policy', 'Policy governing vendor creation', 'vendor_management', 'active', '2026-01-01', 1),
        ('POL-002', 'Payment Approval Policy', 'Requirements for payment approvals', 'payment', 'active', '2026-01-01', 1),
        ('POL-003', 'Data Privacy Policy', 'Handling and protection of personal data', 'data_privacy', 'active', '2026-01-01', 1),
        ('POL-004', 'Access Control Policy', 'User access provisioning requirements', 'access_control', 'active', '2026-01-01', 1),
        ('POL-005', 'Customs Compliance Policy', 'Trade compliance and customs documentation', 'customs', 'active', '2026-01-01', 1),
        ('POL-006', 'Information Security Policy', 'General security requirements', 'security', 'active', '2026-01-01', 1),
    ]

    for p in pols_data:
        # p = (policy_code, title, description, category, status, effective_date, owner_user_id)
        cursor.execute("""
            INSERT INTO grc_policy_documents (
                policy_code, title, description, category, company_id,
                status, effective_date, acknowledgement_required, owner_user_id,
                version, created_at
            ) VALUES (?, ?, ?, ?, 1, ?, ?, 1, ?, 1, datetime('now'))
        """, p)

    # =================================================================
    # SOD RULES
    # =================================================================
    sods_data = [
        ('SOD-001', 'Create Vendor + Approve Vendor', 'Same user cannot create and approve vendor', 'procurement', 'create', 'procurement', 'approve', 'critical', 'Require different users', 1),
        ('SOD-002', 'Create User + Approve Own Access', 'User cannot approve their own access', 'security', 'create', 'security', 'approve', 'critical', 'Require manager approval', 1),
        ('SOD-003', 'Create PO + Approve PO', 'Same user cannot create and approve POs', 'procurement', 'create', 'procurement', 'approve', 'high', 'Implement dual approval', 1),
        ('SOD-004', 'Receive Goods + Approve Invoice', 'Receiving clerk cannot approve invoices', 'procurement', 'receive', 'finance', 'approve', 'high', 'Segregate functions', 1),
        ('SOD-005', 'Create Payment + Approve Payment', 'Payment creator cannot approve own payment', 'finance', 'create', 'finance', 'approve', 'critical', 'Require different approvers', 1),
        ('SOD-006', 'Edit Security Policy + Approve Exception', 'Security admin cannot approve exceptions', 'security', 'edit', 'security', 'approve', 'high', 'Require CISO approval', 1),
        ('SOD-007', 'Control Tester + Approver', 'Same person cannot test and approve controls', 'compliance', 'test', 'compliance', 'approve', 'high', 'Rotate testers quarterly', 1),
        ('SOD-008', 'Create Customer + Approve Credit Note', 'Same user cannot create and approve credit notes', 'finance', 'create', 'finance', 'approve', 'medium', 'Require supervisor approval', 1),
    ]

    for s in sods_data:
        cursor.execute("""
            INSERT INTO grc_sod_rules (
                rule_code, rule_name, description, conflict_pair_module_a,
                conflict_pair_action_a, conflict_pair_module_b, conflict_pair_action_b,
                risk_severity, mitigation_options, exception_requires_approval,
                is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, datetime('now'))
        """, s)

    # =================================================================
    # EXCEPTIONS
    # =================================================================
    exps_data = [
        ('EXP-2026-001', 'Temporary SoD Override - Month-End', 'Temporary override for month-end closing', 'sod_violation', 'high', 'audit_request', datetime.now().strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=5)).strftime('%Y-%m-%d'), 'CFO approved temporary override', 'Additional manual review performed', 1),
        ('EXP-2026-002', 'Emergency Vendor Addition', 'Emergency vendor for critical repair', 'policy_breach', 'medium', 'emergency', (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=80)).strftime('%Y-%m-%d'), 'Emergency due to equipment failure', 'Verified by operations manager', 1),
        ('EXP-2026-003', 'Single Approver for Urgent PO', 'Urgent PO required single approval', 'approval_exception', 'medium', 'time_constraint', (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=27)).strftime('%Y-%m-%d'), 'Production emergency', 'Retrospective dual approval obtained', 1),
    ]

    for e in exps_data:
        cursor.execute("""
            INSERT INTO grc_exceptions (
                exception_code, title, description, exception_type, severity,
                source, start_date, expiry_date, business_justification,
                compensating_controls, owner_user_id, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', datetime('now'))
        """, e)

    # =================================================================
    # FINDINGS
    # =================================================================
    fnds_data = [
        ('FND-2026-001', 'Vendor Creation Without Approval', 'Q1 audit found vendors created without approval', 'audit', 'high', 'Inadequate SoD in vendor creation', 'High financial reporting risk', 'Implement mandatory dual approval', 1, '2026-06-15', 'open'),
        ('FND-2026-002', 'Expired Supplier Certifications', 'Critical suppliers with expired ISO certs', 'supplier_audit', 'medium', 'Supplier monitoring gap', 'Compliance and operational risk', 'Renew or disqualify suppliers', 1, '2026-05-20', 'open'),
        ('FND-2026-003', 'Missing Policy Acknowledgements', '25% staff not acknowledged Data Privacy Policy', 'compliance_review', 'low', 'Inadequate policy communication', 'Regulatory risk', 'Automated reminders and escalation', 1, '2026-04-10', 'in_progress'),
        ('FND-2026-004', 'Control Test Backlog', '8 quarterly control tests overdue', 'internal_audit', 'medium', 'Resource constraints', 'Audit finding risk', 'Prioritize and hire support', 1, '2026-05-01', 'open'),
    ]

    for f in fnds_data:
        cursor.execute("""
            INSERT INTO grc_findings (
                finding_code, title, description, source, severity, root_cause,
                impact, recommendation, owner_user_id, target_closure_date,
                status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, f)

    # =================================================================
    # INCIDENTS
    # =================================================================
    incs_data = [
        ('INC-2026-001', 'Suspicious Access - After Hours', 'Privileged user accessed finance system at 3AM', 'suspicious_access', 'security', (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M'), 1, 'finance', 'high', 'Potential unauthorized access'),
        ('INC-2026-002', 'Bulk Data Export Detected', 'User exported 5000+ customer records', 'data_export_abuse', 'security', (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d %H:%M'), 1, 'crm', 'medium', 'Potential data breach'),
        ('INC-2026-003', 'Warehouse Stock Discrepancy', '50 units missing from Warehouse A', 'inventory_governance', 'operations', (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d %H:%M'), 1, 'warehouse', 'high', 'Possible theft'),
    ]

    for i in incs_data:
        cursor.execute("""
            INSERT INTO grc_incidents (
                incident_code, title, description, category, source,
                incident_datetime, discovered_by, affected_module, severity,
                impact_summary, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', datetime('now'))
        """, i)

    # =================================================================
    # CERTIFICATIONS
    # =================================================================
    certs_data = [
        ('CERT-001', 'ISO 9001:2015 - Quality Management', 'BSI', 'Global', datetime.now().strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d'), 30, 'valid', 'Quality', 'High'),
        ('CERT-002', 'ISO 27001:2022 - Information Security', 'DNV GL', 'Global', datetime.now().strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=45)).strftime('%Y-%m-%d'), 30, 'renewal_pending', 'Information Security', 'High'),
        ('CERT-003', 'PCI DSS Level 1', 'QSA', 'US', datetime.now().strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=90)).strftime('%Y-%m-%d'), 30, 'valid', 'Payment Security', 'Critical'),
        ('CERT-004', 'C-TPAT Certification', 'US Customs', 'US', datetime.now().strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=20)).strftime('%Y-%m-%d'), 30, 'renewal_pending', 'Supply Chain Security', 'High'),
    ]

    for c in certs_data:
        cursor.execute("""
            INSERT INTO grc_certifications (
                certification_code, title, authority, scope, owner_user_id, issue_date,
                expiry_date, reminder_window_days, renewal_status, compliance_impact,
                status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', datetime('now'))
        """, c)

    # =================================================================
    # ALERT RULES
    # =================================================================
    alerts_data = [
        ('ALR-001', 'Overdue Control Test Alert', 'control_test', "next_test_date < date('now')", 'high', 'grc-alerts', 'daily'),
        ('ALR-002', 'High Risk Change Alert', 'risk', "risk_level = 'high'", 'critical', 'grc-alerts', 'realtime'),
        ('ALR-003', 'Certification Expiry Warning', 'certification', "expiry_date BETWEEN date('now') AND date('now', '+30 days')", 'medium', 'grc-alerts', 'daily'),
        ('ALR-004', 'Policy Acknowledgement Overdue', 'policy', "due_date < date('now')", 'medium', 'grc-alerts', 'daily'),
        ('ALR-005', 'SoD Conflict Detected', 'sod', "status = 'open'", 'critical', 'grc-alerts', 'realtime'),
        ('ALR-006', 'Failed Control Test Alert', 'control_test', "test_result = 'fail'", 'high', 'grc-alerts', 'realtime'),
    ]

    for a in alerts_data:
        cursor.execute("""
            INSERT INTO grc_alert_rules (
                rule_code, rule_name, alert_type, condition_expression,
                severity, notification_channel, check_frequency,
                is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, datetime('now'))
        """, a)

    # =================================================================
    # HIGH RISK EVENTS
    # =================================================================
    hres_data = [
        ('HRE-2026-001', 'repeated_login_failure', 'User failed login 10 times in 5 minutes', (now - timedelta(days=1)).strftime('%Y-%m-%d %H:%M'), 1, 'high', 1, 'security', 'login_attempt', '192.168.1.100', 'session-abc'),
        ('HRE-2026-002', 'after_hours_privileged_access', 'Admin accessed system at 3:00 AM', (now - timedelta(days=2)).strftime('%Y-%m-%d %H:%M'), 1, 'medium', 1, 'finance', 'admin_access', '192.168.1.105', 'session-def'),
        ('HRE-2026-003', 'bulk_data_export', 'User exported 5000+ customer records', (now - timedelta(days=3)).strftime('%Y-%m-%d %H:%M'), 1, 'high', 1, 'crm', 'data_export', '192.168.1.110', 'session-ghi'),
        ('HRE-2026-004', 'role_change_privileged', 'Admin role granted to regular user', (now - timedelta(days=4)).strftime('%Y-%m-%d %H:%M'), 1, 'critical', 1, 'security', 'role_change', '192.168.1.115', 'session-jkl'),
    ]

    for h in hres_data:
        cursor.execute("""
            INSERT INTO grc_high_risk_events (
                event_code, event_type, title, detected_at, detected_by,
                severity, user_id, module, activity, ip_address, session_id,
                status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'detected', datetime('now'))
        """, h)

    # =================================================================
    # APPROVAL MATRIX RULES
    # =================================================================
    aprs_data = [
        ('APR-001', 'finance', 'payment', 'Payment approval matrix', 1, 50000, 100000, 'medium', 1, 2, '1', 'CFO', 1),
        ('APR-002', 'finance', 'payment', 'High value payment approval', 1, 100001, None, 'high', 1, 2, '1,2', 'CEO + CFO', 1),
        ('APR-003', 'procurement', 'purchase_order', 'PO approval matrix', 1, 10000, 50000, 'low', 4, 5, '1', 'Procurement Manager', 1),
        ('APR-004', 'procurement', 'purchase_order', 'High value PO approval', 1, 50001, None, 'high', 4, 5, '1,2', 'Director + CFO', 1),
        ('APR-005', 'inventory', 'stock_adjustment', 'Stock adjustment approval', 1, 1000, 10000, 'medium', 6, 7, '1', 'Warehouse Manager', 1),
        ('APR-006', 'security', 'access_request', 'Privileged access approval', 1, 0, None, 'high', 8, 9, '1,2', 'CISO + IT Director', 1),
    ]

    for a in aprs_data:
        cursor.execute("""
            INSERT INTO grc_approval_matrix_rules (
                rule_code, module, entity_type, description, company_id,
                amount_threshold_min, amount_threshold_max, risk_level,
                requester_role_id, approver_role_id, approval_sequence,
                fallback_approver_ids, is_active, effective_from, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
        """, a)

    # =================================================================
    # SOD CONFLICTS
    # =================================================================
    sod_conflicts_data = [
        (1, 1, 1, 1, 'open', 'Active SoD conflict - same user can create and approve vendors', datetime.now().strftime('%Y-%m-%d'), 1),
        (2, 2, 2, 1, 'open', 'Active SoD conflict - same user can create and approve POs', datetime.now().strftime('%Y-%m-%d'), 1),
        (3, 4, 1, 1, 'under_review', 'Temporary override for warehouse manager - exception approved until month-end', datetime.now().strftime('%Y-%m-%d'), 1),
        (5, 5, 3, 1, 'open', 'Critical SoD conflict in payment processing', datetime.now().strftime('%Y-%m-%d'), 1),
    ]
    for sc in sod_conflicts_data:
        cursor.execute("""
            INSERT INTO grc_sod_conflicts (
                rule_id, user_id, role_id, company_id,
                status, resolution_notes, detected_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, sc)

    # =================================================================
    # ACCESS REVIEWS
    # =================================================================
    access_reviews_data = [
        ('AR-2026-Q1', 'Q1 2026 Privileged Access Review', 'Quarterly review of all privileged users', 'quarterly', '1', None, None, 'privileged', '1', 1, (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'), 'in_progress', None, 25, 8, 5, 0, 'Reviewing admin and finance roles', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ('AR-2026-Q1-FIN', 'Q1 2026 Finance Access Review', 'Quarterly review of finance system access', 'quarterly', '1', None, None, None, None, 1, (datetime.now() + timedelta(days=21)).strftime('%Y-%m-%d'), 'planned', None, 15, 0, 0, 0, None, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ('AR-2026-HR', 'HR System Access Review', 'Review of HR system access for compliance', 'annual', '1', None, None, 'hr', '1', 1, (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'), 'planned', None, 10, 0, 0, 0, None, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
    ]
    for ar in access_reviews_data:
        cursor.execute("""
            INSERT INTO grc_access_reviews (
                review_code, title, description, review_cycle, scope_company_ids,
                scope_branch_ids, scope_department_ids, scope_module, scope_role_ids,
                scope_privileged_only, reviewer_user_id, due_date, status,
                completion_date, total_users, reviewed_users, approved_users, revoked_users, notes,
                created_at, created_by, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ar)

    # =================================================================
    # EVIDENCE ITEMS
    # =================================================================
    evidence_data = [
        ('EVD-2026-001', 'Control Test Evidence', 'Vendor approval logs for Q1', 'control_test', 'control', 1, 'uploads/grc/vendor_approval_log.xlsx', 'vendor_approval_log.xlsx', 24576, 1, 1, 'pending', (datetime.now()).strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d'), 'compliance,evidence', 1, 0, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1),
        ('EVD-2026-002', 'Access Review Evidence', 'User access list export', 'access_review', 'user', 1, 'uploads/grc/access_review_q1.xlsx', 'access_review_q1.xlsx', 18432, 1, 1, 'in_review', (datetime.now()).strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=180)).strftime('%Y-%m-%d'), 'access,quarterly', 1, 0, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1),
        ('EVD-2026-003', 'Policy Acknowledgement', 'Signed policy acknowledgement forms', 'policy', 'policy', 1, 'uploads/grc/policy_signed_2026.pdf', 'policy_signed_2026.pdf', 102400, 1, 1, 'approved', (datetime.now()).strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=730)).strftime('%Y-%m-%d'), 'policy,acknowledgement', 1, 0, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1),
        ('EVD-2026-004', 'Compliance Certificate', 'ISO 9001 certificate', 'certification', 'control', 1, 'uploads/grc/iso9001_cert.pdf', 'iso9001_cert.pdf', 51200, 1, 1, 'approved', (datetime.now()).strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=548)).strftime('%Y-%m-%d'), 'iso,certification,quality', 2, 0, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1),
        ('EVD-2026-005', 'Customs Documentation', 'Customs declarations review', 'compliance', 'compliance', 1, 'uploads/grc/customs_review_2026.pdf', 'customs_review_2026.pdf', 153600, 1, 1, 'approved', (datetime.now()).strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=1825)).strftime('%Y-%m-%d'), 'customs,trade,compliance', 1, 0, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1),
    ]
    for ev in evidence_data:
        cursor.execute("""
            INSERT INTO grc_evidence_items (
                evidence_code, title, description, evidence_type, linked_entity_type,
                linked_entity_id, file_url, file_name, file_size, uploader_user_id,
                reviewer_user_id, review_status, validity_period_from, validity_period_to,
                tags, version, is_expired, expiry_alert_sent, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ev)

    # =================================================================
    # ALERT EVENTS
    # =================================================================
    alert_events_data = [
        (1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'high', 'Overdue Control Test', 'Control CTL-002 test is overdue by 5 days', 'control', 2, 0, None, None, 0, None, None, 'Assigned to ops team for immediate action'),
        (1, (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'), 'high', 'SoD Conflict Detected', 'SoD conflict detected for user ID 5 in vendor creation', 'user', 5, 0, None, None, 0, None, None, 'Reviewing with compliance team'),
        (1, (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d %H:%M:%S'), 'low', 'Policy Expiry Warning', 'Policy POL-003 expires in 30 days', 'policy', 3, 1, (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'), 1, 0, None, None, 'Acknowledged, monitoring'),
        (2, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'medium', 'Certification Expiry', 'Certification CERT-002 expires in 45 days', 'certification', 2, 0, None, None, 0, None, None, 'Renewal process initiated'),
    ]
    for ae in alert_events_data:
        cursor.execute("""
            INSERT INTO grc_alert_events (
                rule_id, triggered_at, severity, title, message, entity_type, entity_id,
                acknowledged, acknowledged_at, acknowledged_by, resolved, resolved_at, resolved_by, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ae)

    # =================================================================
    # DEADLINES
    # =================================================================
    deadlines_data = [
        ('DLN-2026-001', 'Q1 Control Testing Deadline', 'control_testing', 'control', 1, 1, '2026-03-31', 'upcoming', 0, None, None, 'Q1 2026 control testing must be completed', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1),
        ('DLN-2026-002', 'Policy Review - POL-001', 'policy_review', 'policy', 3, 1, '2026-06-30', 'upcoming', 0, None, None, 'Vendor Management Policy annual review due', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1),
        ('DLN-2026-003', 'Access Review Completion', 'access_review', 'access_review', 1, 1, (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'), 'upcoming', 0, None, None, 'Q1 access review cycle deadline', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1),
        ('DLN-2026-004', 'Compliance Obligation - SOX', 'compliance_obligation', 'compliance', 1, 1, '2026-12-31', 'open', 0, None, None, 'Annual SOX 404 assessment', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1),
    ]
    for dl in deadlines_data:
        cursor.execute("""
            INSERT INTO grc_deadlines (
                deadline_code, title, deadline_type, linked_entity_type, linked_entity_id,
                owner_user_id, due_date, status, reminder_sent, last_reminder_at,
                completion_date, notes, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, dl)

    # =================================================================
    # REMEDIATION PLANS
    # =================================================================
    remediation_data = [
        ('RMP-2026-001', 'SoD Violation Remediation', 'Address SoD conflict in vendor creation process', 1, None, 1, 1, 'in_progress', 'high', 40, '2026-03-15', '2026-06-30', None, 'Requires dual approval workflow implementation', 'Implement dual approval for vendor creation', 'pending', 'Awaiting security team review', None, None, 'Working with IT to implement compensating controls', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ('RMP-2026-002', 'Control Testing Backlog', 'Clear overdue control tests', 2, None, 1, 1, 'in_progress', 'medium', 65, '2026-02-01', '2026-05-31', None, '10 control tests overdue', 'Complete 10 overdue control tests', 'approved', 'Testing schedule approved by compliance', None, None, 'Weekly status updates to management', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ('RMP-2026-003', 'Access Review Findings', 'Remediate excessive access found in Q1 review', 3, None, 1, 1, 'planned', 'high', 0, '2026-04-01', '2026-04-30', None, '5 accounts with excessive privileges', 'Review and remediate 5 accounts with excessive privileges', 'pending', 'Action plan under review', None, None, 'User access review scheduled', datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
    ]
    for rm in remediation_data:
        cursor.execute("""
            INSERT INTO grc_remediation_plans (
                plan_code, title, description, finding_id, exception_id,
                owner_user_id, reviewer_user_id, status, priority, progress_percent,
                start_date, target_date, completion_date, blocking_issues, verification_step,
                closure_approval, closure_notes, approved_at, approved_by, notes,
                created_at, created_by, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rm)

    # =================================================================
    # FRAMEWORK TEMPLATES
    # =================================================================
    frameworks_data = [
        ('FRM-001', 'COSO 2013 Framework', 'coso', 'Internal Control - Integrated Framework', '{"principles": ["control environment", "risk assessment", "control activities", "information and communication", "monitoring"]}', 1, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1),
        ('FRM-002', 'COBIT 2019', 'cobit', 'Governance and Management of Enterprise IT', '{"domains": ["EDM", "APO", "BAI", "DSS", "MEA"]}', 1, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1),
        ('FRM-003', 'ISO 31000', 'iso', 'Risk Management Guidelines', '{"components": ["scope", "framework", "process"]}', 1, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 1),
    ]
    for fw in frameworks_data:
        cursor.execute("""
            INSERT INTO grc_framework_templates (
                template_code, template_name, framework_type, description, content,
                version, is_active, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, fw)

    # =================================================================
    # NOTES
    # =================================================================
    notes_data = [
        ('risk', 1, 'Initial risk assessment completed with moderate inherent risk rating', 1, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ('control', 1, 'Added additional approval step to vendor creation process', 1, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ('finding', 1, 'Root cause identified - inadequate segregation of duties in procurement', 1, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ('incident', 1, 'Security team investigating unauthorized access attempt', 1, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
    ]
    for nt in notes_data:
        cursor.execute("""
            INSERT INTO grc_notes (
                entity_type, entity_id, note_text, is_internal, created_by, created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, nt)

    conn.commit()
    conn.close()

    print("[GRC Seed] Comprehensive GRC data seeded successfully!")
    print(f"  - Governance Entities: {len(governance_data)}")
    print(f"  - Risks: {len(risks_data)}")
    print(f"  - Controls: {len(controls_data)}")
    print(f"  - Control Tests: {len(tests_data)}")
    print(f"  - Compliance Obligations: {len(obls_data)}")
    print(f"  - Regulations: {len(regs_data)}")
    print(f"  - Policies: {len(pols_data)}")
    print(f"  - SoD Rules: {len(sods_data)}")
    print(f"  - Exceptions: {len(exps_data)}")
    print(f"  - Findings: {len(fnds_data)}")
    print(f"  - Incidents: {len(incs_data)}")
    print(f"  - Certifications: {len(certs_data)}")
    print(f"  - Alert Rules: {len(alerts_data)}")
    print(f"  - High-Risk Events: {len(hres_data)}")
    print(f"  - Approval Matrix Rules: {len(aprs_data)}")
    print(f"  - SoD Conflicts: {len(sod_conflicts_data)}")
    print(f"  - Access Reviews: {len(access_reviews_data)}")
    print(f"  - Evidence Items: {len(evidence_data)}")
    print(f"  - Alert Events: {len(alert_events_data)}")
    print(f"  - Deadlines: {len(deadlines_data)}")
    print(f"  - Remediation Plans: {len(remediation_data)}")
    print(f"  - Framework Templates: {len(frameworks_data)}")
    print(f"  - Notes: {len(notes_data)}")


if __name__ == '__main__':
    seed_grc_comprehensive_data()
