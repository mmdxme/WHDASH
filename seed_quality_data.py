"""Seed Quality Management demo data."""
import sqlite3
import random
from datetime import datetime, timedelta

DATABASE = 'warehouse.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def seed_quality_data():
    """Seed comprehensive quality management demo data."""
    conn = get_db()
    c = conn.cursor()

    print("Seeding Quality Management demo data...")

    # Get some existing data for references
    item_ids = [row[0] for row in c.execute("SELECT id FROM parts LIMIT 10").fetchall()]
    supplier_ids = [row[0] for row in c.execute("SELECT id FROM suppliers LIMIT 10").fetchall()]
    customer_ids = [row[0] for row in c.execute("SELECT id FROM customers LIMIT 10").fetchall()]
    employee_ids = [row[0] for row in c.execute("SELECT id FROM hr_employees LIMIT 10").fetchall()]
    company_ids = [row[0] for row in c.execute("SELECT id FROM companies").fetchall()]
    warehouse_ids = [row[0] for row in c.execute("SELECT id FROM warehouses").fetchall()]

    if not item_ids:
        item_ids = [1]
    if not supplier_ids:
        supplier_ids = [1]
    if not customer_ids:
        customer_ids = [1]
    if not employee_ids:
        employee_ids = [1]
    if not company_ids:
        company_ids = [1]
    if not warehouse_ids:
        warehouse_ids = [1]

    # =========================================================================
    # 1. QUALITY SETTINGS
    # =========================================================================
    settings = [
        ('QUALITY_AUTO_NCR_ON_FAIL', '1', 'Auto-create NCR when inspection fails', 'inspection'),
        ('QUALITY_INSPECTION_NUMBERING_PREFIX', 'INS', 'Inspection number prefix', 'numbering'),
        ('QUALITY_NCR_NUMBERING_PREFIX', 'NCR', 'NCR number prefix', 'numbering'),
        ('QUALITY_CAPA_NUMBERING_PREFIX', 'CAPA', 'CAPA number prefix', 'numbering'),
        ('QUALITY_AUDIT_NUMBERING_PREFIX', 'AUD', 'Audit number prefix', 'numbering'),
        ('QUALITY_DEFAULT_SEVERITY', 'MINOR', 'Default severity for NCRs', 'ncr'),
        ('QUALITY_OVERDUE_DAYS_WARNING', '7', 'Days before due to send warning', 'ncr'),
        ('QUALITY_REQUIRE_CONTAINMENT', '1', 'Require containment action for NCRs', 'ncr'),
        ('QUALITY_REQUIRE_RCA', '1', 'Require root cause analysis', 'ncr'),
        ('QUALITY_REQUIRE_EFFECTIVENESS', '1', 'Require CAPA effectiveness review', 'capa'),
        ('QUALITY_NCR_CLOSURE_DAYS', '30', 'Target NCR closure days', 'ncr'),
        ('QUALITY_CAPA_CLOSURE_DAYS', '60', 'Target CAPA closure days', 'capa'),
        ('QUALITY_EFFECTIVENESS_REVIEW_DAYS', '90', 'Days after closure for effectiveness review', 'capa'),
        ('QUALITY_FINDING_DUE_DAYS', '30', 'Default audit finding due days', 'audit'),
        ('QUALITY_PASS_RATE_THRESHOLD', '95', 'Minimum pass rate threshold (%)', 'inspection'),
        ('QUALITY_EMAIL_NOTIFICATIONS', '1', 'Enable email notifications', 'notification'),
        ('QUALITY_FLOW_INTEGRATION', '1', 'Enable Flow integration', 'notification'),
    ]

    for key, value, desc, cat in settings:
        c.execute("""
            INSERT OR IGNORE INTO quality_settings (setting_key, setting_value, description, category, updated_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (key, value, desc, cat))

    conn.commit()
    print("Created quality settings")

    # =========================================================================
    # 2. QUALITY INSPECTION TYPES
    # =========================================================================
    inspection_types = [
        ('INI', 'Incoming Inspection', 'Inspection of received materials and goods', 'INCOMING', 'ALL', None, 1, 1, 5, 'AQL 2.5', 'PASS_FAIL'),
        ('INP', 'In-Process Inspection', 'Inspection during manufacturing or processing', 'IN_PROCESS', 'ALL', None, 1, 3, None, 'Process specifications', 'PASS_FAIL'),
        ('FIN', 'Final Inspection', 'End-of-line or pre-dispatch inspection', 'FINAL', 'ALL', None, 1, 5, None, 'Final product specs', 'PASS_FAIL'),
        ('WHS', 'Warehouse Inspection', 'Storage condition and handling inspection', 'WAREHOUSE', 'ALL', None, 1, 1, None, 'Warehouse standards', 'PASS_FAIL'),
        ('SUP', 'Supplier Audit', 'Supplier facility and process audit', 'SUPPLIER', 'ALL', None, 1, 0, None, 'Supplier requirements', 'PASS_FAIL'),
        ('CUS', 'Customer Inspection', 'Pre-delivery or customer site inspection', 'CUSTOMER', 'ALL', None, 1, 2, None, 'Customer requirements', 'PASS_FAIL'),
    ]

    for code, name, desc, cat, source, entities, active, checklist, sample, criteria, result_type in inspection_types:
        c.execute("""
            INSERT OR IGNORE INTO quality_inspection_types 
            (code, name, description, category, applicable_source, is_active, requires_checklist, min_sample_size, acceptance_criteria, result_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (code, name, desc, cat, source, active, checklist, sample, criteria, result_type))

    conn.commit()
    print("Created inspection types")

    # =========================================================================
    # 3. DEFECT CATEGORIES
    # =========================================================================
    defect_categories = [
        ('DIM', 'Dimensional', 'Physical dimension out of tolerance', 'CRITICAL,MAJOR,MINOR', 1),
        ('SUR', 'Surface Defect', 'Scratches, dents, marks on surface', 'MAJOR,MINOR', 1),
        ('MAT', 'Material Issue', 'Wrong or substandard material', 'CRITICAL,MAJOR', 1),
        ('FUNC', 'Functional', 'Product does not function as expected', 'CRITICAL,MAJOR', 1),
        ('PKG', 'Packaging', 'Damaged or missing packaging', 'MINOR', 1),
        ('DOC', 'Documentation', 'Missing or incorrect documentation', 'MINOR', 1),
        ('Safety', 'Safety Issue', 'Potential safety hazard', 'CRITICAL', 1),
    ]

    for code, name, desc, severities, active in defect_categories:
        c.execute("""
            INSERT OR IGNORE INTO quality_defect_categories (code, name, description, severity_levels, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, (code, name, desc, severities, active))

    conn.commit()
    print("Created defect categories")

    # =========================================================================
    # 4. CAPA CATEGORIES
    # =========================================================================
    capa_categories = [
        ('CORR', 'Corrective Action', 'Action to eliminate cause of non-conformance', 'CORRECTIVE', 1),
        ('PREV', 'Preventive Action', 'Action to eliminate cause of potential non-conformance', 'PREVENTIVE', 1),
        ('BOTH', 'Both', 'Actions address both corrective and preventive', 'BOTH', 1),
    ]

    for code, name, desc, ctype, active in capa_categories:
        c.execute("""
            INSERT OR IGNORE INTO quality_capa_categories (code, name, description, type, is_active)
            VALUES (?, ?, ?, ?, ?)
        """, (code, name, desc, ctype, active))

    conn.commit()
    print("Created CAPA categories")

    # =========================================================================
    # 5. ROOT CAUSE CATEGORIES
    # =========================================================================
    root_cause_categories = [
        ('MAN', 'Man/Material', 'Human error or material issue'),
        ('MAC', 'Machine', 'Equipment or machinery issue'),
        ('MET', 'Method', 'Process or procedure issue'),
        ('MAT', 'Material', 'Raw material or component issue'),
        ('MEA', 'Measurement', 'Inspection or testing issue'),
        ('ENV', 'Environment', 'Environmental conditions'),
        ('DES', 'Design', 'Product or process design issue'),
        ('SUP', 'Supplier', 'Supplier-related issue'),
    ]

    for code, name, desc in root_cause_categories:
        c.execute("""
            INSERT OR IGNORE INTO quality_root_cause_categories (code, name, description, is_active)
            VALUES (?, ?, ?, 1)
        """, (code, name, desc))

    conn.commit()
    print("Created root cause categories")

    # =========================================================================
    # 6. SAMPLE INSPECTIONS
    # =========================================================================
    inspection_statuses = ['PENDING', 'IN_PROGRESS', 'COMPLETED', 'APPROVED']
    result_statuses = ['PASS', 'FAIL', 'CONDITIONAL']

    for i in range(15):
        status = random.choice(inspection_statuses)
        insp_date = datetime.now() - timedelta(days=random.randint(1, 90))
        qty_received = random.randint(100, 1000)
        qty_inspected = min(qty_received, random.randint(50, 200))
        qty_accepted = int(qty_inspected * random.uniform(0.85, 0.99))
        qty_rejected = qty_inspected - qty_accepted

        insp_type = random.choice(['INI', 'INP', 'FIN'])

        c.execute("""
            INSERT INTO quality_inspections (
                inspection_number, inspection_type_id, source_type, source_reference,
                company_id, warehouse_id, supplier_id, customer_id, item_id, item_code, item_name,
                quantity_received, quantity_inspected, quantity_accepted, quantity_rejected, quantity_held,
                result, status, inspector_id, inspector_name, inspection_date,
                notes, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
        """, (
            f'INS-2026-{1000 + i}',
            random.randint(1, 6),
            random.choice(['PURCHASE_ORDER', 'WORK_ORDER', 'SALES_ORDER', 'TRANSFER', 'RETURN']),
            f'REF-{random.randint(10000, 99999)}',
            random.choice(company_ids),
            random.choice(warehouse_ids),
            random.choice(supplier_ids),
            random.choice(customer_ids),
            random.choice(item_ids),
            f'ITEM-{random.randint(1000, 9999)}',
            f'Sample Product {random.randint(1, 20)}',
            qty_received,
            qty_inspected,
            qty_accepted,
            qty_rejected,
            random.randint(0, 10) if status == 'IN_PROGRESS' else 0,
            random.choice(result_statuses) if status == 'COMPLETED' else None,
            status,
            random.choice(employee_ids),
            f'Inspector {random.randint(1, 10)}',
            insp_date.strftime('%Y-%m-%d'),
            f'Inspection notes for sample {i+1}',
            random.choice(employee_ids)
        ))

    conn.commit()
    print("Created 15 sample inspections")

    # =========================================================================
    # 7. SAMPLE NCRs
    # =========================================================================
    ncr_statuses = ['OPEN', 'UNDER_REVIEW', 'AWAITING_DISPOSITION', 'IN_PROGRESS', 'CLOSED', 'CANCELLED']
    severities = ['CRITICAL', 'MAJOR', 'MINOR']
    ncr_sources = ['INSPECTION', 'PRODUCTION', 'CUSTOMER', 'SUPPLIER', 'INTERNAL', 'MAINTENANCE']

    for i in range(8):
        ncr_date = datetime.now() - timedelta(days=random.randint(1, 60))
        status = random.choice(ncr_statuses)
        severity = random.choice(severities)

        c.execute("""
            INSERT INTO quality_non_conformances (
                ncr_number, source_type, source_reference, source_reference_id,
                company_id, branch_id, warehouse_id, item_id, item_code, item_name,
                lot_number, batch_number, supplier_id, supplier_name,
                ncr_category, defect_category_id, defect_type, severity, impact, priority,
                description, detected_by, detected_by_name, detected_date,
                owner_id, owner_name, status,
                containment_required, containment_status,
                root_cause_required, root_cause_status,
                hold_quantity, return_quantity, scrap_quantity,
                target_close_date, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
        """, (
            f'NCR-2026-{100 + i}',
            random.choice(ncr_sources),
            f'SRC-{random.randint(1000, 9999)}',
            random.randint(1, 50),
            random.choice(company_ids),
            1,
            random.choice(warehouse_ids),
            random.choice(item_ids),
            f'ITEM-{random.randint(1000, 9999)}',
            f'Defective Product {i+1}',
            f'LOT-{random.randint(10000, 99999)}',
            f'BATCH-{random.randint(1000, 9999)}',
            random.choice(supplier_ids),
            f'Supplier {random.randint(1, 10)}',
            random.choice(['MATERIAL', 'PROCESS', 'DESIGN', 'DOCUMENTATION', 'SAFETY']),
            random.randint(1, 7),
            random.choice(['VISUAL', 'DIMENSIONAL', 'FUNCTIONAL', 'MATERIAL']),
            severity,
            random.choice(['LOW', 'MEDIUM', 'HIGH']),
            random.choice(['LOW', 'MEDIUM', 'HIGH']),
            f'Description of non-conformance {i+1}: Visual defect detected on inspection.',
            random.choice(employee_ids),
            f'Employee {random.randint(1, 10)}',
            ncr_date.strftime('%Y-%m-%d'),
            random.choice(employee_ids),
            f'QA Manager {random.randint(1, 5)}',
            status,
            1 if severity in ['CRITICAL', 'MAJOR'] else 0,
            random.choice(['PENDING', 'IN_PROGRESS', 'COMPLETED', 'NOT_REQUIRED']) if severity in ['CRITICAL', 'MAJOR'] else 'NOT_REQUIRED',
            1 if status in ['UNDER_REVIEW', 'AWAITING_DISPOSITION'] else 0,
            random.choice(['PENDING', 'IN_PROGRESS', 'COMPLETED']) if status in ['UNDER_REVIEW', 'AWAITING_DISPOSITION'] else 'NOT_REQUIRED',
            random.randint(10, 100),
            random.randint(0, 20),
            random.randint(0, 15),
            (ncr_date + timedelta(days=30)).strftime('%Y-%m-%d'),
            random.choice(employee_ids)
        ))

    conn.commit()
    print("Created 8 sample NCRs")

    # =========================================================================
    # 8. SAMPLE CAPAs
    # =========================================================================
    capa_types = ['CORRECTIVE', 'PREVENTIVE']
    capa_statuses = ['OPEN', 'IN_PROGRESS', 'PENDING_EFFECTIVENESS', 'CLOSED']

    for i in range(6):
        capa_date = datetime.now() - timedelta(days=random.randint(1, 90))
        status = random.choice(capa_statuses)

        c.execute("""
            INSERT INTO quality_capa_records (
                capa_number, triggering_source, source_type, source_reference_id,
                ncr_id, company_id, branch_id, department,
                category_id, capa_type, severity, priority,
                title, description, root_cause_summary,
                root_cause_category_id, root_cause_description,
                owner_id, owner_name, target_date, status,
                effectiveness_verification_required, effectiveness_review_status,
                created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
        """, (
            f'CAPA-2026-{100 + i}',
            random.choice(['NCR', 'AUDIT', 'INSPECTION', 'CUSTOMER_COMPLAINT', 'INTERNAL']),
            random.choice(['NCR', 'AUDIT_FINDING', 'INSPECTION', 'COMPLAINT']),
            random.randint(1, 10),
            random.randint(1, 8) if i < 5 else None,
            random.choice(company_ids),
            1,
            random.choice(['PRODUCTION', 'WAREHOUSE', 'QUALITY', 'ENGINEERING', 'PROCUREMENT']),
            random.randint(1, 3),
            random.choice(capa_types),
            random.choice(['CRITICAL', 'MAJOR', 'MINOR']),
            random.choice(['HIGH', 'MEDIUM', 'LOW']),
            f'CAPA Title: Address {random.choice(["material defect", "process variation", "documentation gap", "training deficiency"])}',
            f'CAPA description {i+1}',
            f'Root cause identified through 5-why analysis',
            random.randint(1, 8),
            f'Specific root cause description for CAPA {i+1}',
            random.choice(employee_ids),
            f'CAPA Owner {random.randint(1, 5)}',
            (capa_date + timedelta(days=60)).strftime('%Y-%m-%d'),
            status,
            1,
            'PENDING' if status == 'PENDING_EFFECTIVENESS' else None,
            random.choice(employee_ids)
        ))

    conn.commit()
    print("Created 6 sample CAPAs")

    # =========================================================================
    # 9. SAMPLE AUDIT PLANS
    # =========================================================================
    audit_types = ['INTERNAL', 'SUPPLIER', 'COMPLIANCE', 'PROCESS', 'SYSTEM']
    audit_statuses = ['PLANNED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED']

    for i in range(5):
        planned_date = datetime.now() + timedelta(days=random.randint(-15, 45))
        status = random.choice(audit_statuses)

        c.execute("""
            INSERT INTO quality_audit_plans (
                plan_number, audit_title, audit_type, scope, objectives,
                company_id, branch_id, warehouse_id, site_location, department,
                scheduled_start_date, scheduled_end_date,
                lead_auditor_id, lead_auditor_name, auditor_ids, auditor_names,
                auditee_id, auditee_name, auditee_department,
                checklist_template_id, status, preparation_status,
                notification_sent, opening_meeting_held, closing_meeting_held,
                notes, created_at, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
        """, (
            f'AUD-2026-{100 + i}',
            f'{random.choice(["Annual", "Quarterly", "Surveillance", "Certification"])} {random.choice(audit_types)} Audit',
            random.choice(audit_types),
            'Audit scope covering quality management system processes and controls',
            'Objective: Verify compliance with QMS requirements and identify improvement opportunities',
            random.choice(company_ids),
            1,
            random.choice(warehouse_ids),
            f'Site {random.randint(1, 5)}',
            random.choice(['QUALITY', 'PRODUCTION', 'WAREHOUSE', 'ENGINEERING']),
            planned_date.strftime('%Y-%m-%d'),
            (planned_date + timedelta(days=random.randint(1, 5))).strftime('%Y-%m-%d'),
            random.choice(employee_ids),
            f'Lead Auditor {random.randint(1, 3)}',
            ','.join([str(random.choice(employee_ids)) for _ in range(2)]),
            f'Auditor {random.randint(1, 5)}, Auditor {random.randint(1, 5)}',
            random.choice(employee_ids),
            f'Auditee {random.randint(1, 5)}',
            random.choice(['QUALITY', 'PRODUCTION', 'WAREHOUSE']),
            None,
            status,
            random.choice(['NOT_STARTED', 'IN_PROGRESS', 'COMPLETED']),
            1 if status != 'PLANNED' else 0,
            1 if status in ['IN_PROGRESS', 'COMPLETED'] else 0,
            1 if status == 'COMPLETED' else 0,
            f'Audit notes and observations for sample audit {i+1}',
            random.choice(employee_ids)
        ))

    conn.commit()
    print("Created 5 sample audit plans")

    # =========================================================================
    # 10. SAMPLE AUDIT FINDINGS
    # =========================================================================
    finding_categories = ['NON_CONFORMITY', 'OBSERVATION', 'OFI', 'COMPLIANCE']
    finding_severities = ['CRITICAL', 'MAJOR', 'MINOR', 'INFORMATIONAL']
    finding_statuses = ['OPEN', 'IN_PROGRESS', 'CLOSED']

    for i in range(10):
        due_date = datetime.now() + timedelta(days=random.randint(-10, 30))
        status = random.choice(finding_statuses)

        c.execute("""
            INSERT INTO quality_audit_findings (
                audit_plan_id, finding_number, category, severity, title, description,
                root_cause, suggested_corrective_action, due_date, status,
                owner_id, owner_name, verified_by, verified_at,
                closure_date, closure_notes, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            random.randint(1, 5),
            f'FND-{random.randint(1000, 9999)}',
            random.choice(finding_categories),
            random.choice(finding_severities),
            f'Audit Finding: {random.choice(["Non-conforming process control", "Missing documentation", "Training gap identified", "Equipment calibration issue"])}',
            f'Detailed description of finding {i+1}',
            f'Root cause analysis for finding {i+1}',
            f'Suggested corrective action for finding {i+1}',
            due_date.strftime('%Y-%m-%d'),
            status,
            random.choice(employee_ids),
            f'Owner {random.randint(1, 5)}',
            random.choice(employee_ids) if status == 'CLOSED' else None,
            datetime.now().strftime('%Y-%m-%d') if status == 'CLOSED' else None,
            (datetime.now() - timedelta(days=random.randint(1, 10))).strftime('%Y-%m-%d') if status == 'CLOSED' else None,
            f'Closure notes for finding {i+1}' if status == 'CLOSED' else None,
            random.choice(company_ids),
            random.choice(employee_ids)
        ))

    conn.commit()
    print("Created 10 sample audit findings")

    # =========================================================================
    # 11. SAMPLE QUALITY SETTINGS
    # =========================================================================
    c.execute("SELECT COUNT(*) FROM quality_settings")
    if c.fetchone()[0] < 5:
        additional_settings = [
            ('QUALITY_AUTO_ESCALATE_NCR', '1', 'Auto-escalate overdue NCRs', 'ncr'),
            ('QUALITY_AUTO_NCR_ON_FAIL', '1', 'Auto-create NCR when inspection fails', 'inspection'),
            ('QUALITY_CALC_SCRAP_COST', '1', 'Calculate scrap cost automatically', 'financial'),
            ('QUALITY_SCRAP_COST_UNIT', '10.00', 'Default scrap cost per unit', 'financial'),
            ('QUALITY_CURRENCY', 'USD', 'Financial impact currency', 'financial'),
            ('QUALITY_REQUIRE_CAPA_APPROVAL', '1', 'Require approval for CAPA closure', 'capa'),
            ('QUALITY_CAPA_APPROVER_ROLE', 'QA_MANAGER', 'Default CAPA approver role', 'capa'),
            ('QUALITY_REQUIRE_AUDIT_CHECKLIST', '1', 'Require audit checklist', 'audit'),
            ('QUALITY_AUTO_CLOSE_FINDINGS', '0', 'Auto-close resolved findings', 'audit'),
        ]

        for key, value, desc, cat in additional_settings:
            c.execute("""
                INSERT OR IGNORE INTO quality_settings (setting_key, setting_value, description, category, updated_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (key, value, desc, cat))

        conn.commit()
        print("Created additional quality settings")

    conn.close()
    print("Quality Management demo data seeded successfully!")

if __name__ == '__main__':
    seed_quality_data()
