"""
Document Management Seed Data
============================
Seeds realistic demo/test data for the Document Management module.

Usage:
    from seed_document_data import seed_document_demo_data
    seed_document_demo_data()
"""

import sqlite3
import os
import json
import random
from datetime import datetime, timedelta

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'warehouse.db'))


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def seed_document_demo_data(user_id=1, company_id=1):
    """Seed demo data for document management."""
    # Initialize tables first
    from document_models import initialize_document_tables
    initialize_document_tables()
    
    db = get_db()
    
    # Ensure signature_status column exists
    try:
        db.execute("ALTER TABLE documents ADD COLUMN signature_status TEXT DEFAULT 'Not Applicable'")
        db.execute("ALTER TABLE documents ADD COLUMN signed_at DATETIME")
        db.execute("ALTER TABLE documents ADD COLUMN signed_by_user_id INTEGER")
        db.execute("ALTER TABLE documents ADD COLUMN signature_type TEXT")
        db.commit()
    except Exception as e:
        pass  # Column may already exist
    try:
        # Check if already seeded
        existing = db.execute("SELECT COUNT(*) as cnt FROM documents").fetchone()
        if existing['cnt'] > 0:
            print(f"Document data already exists ({existing['cnt']} documents). Skipping seed.")
            return

        print("Seeding document management demo data...")

        # Get categories
        categories = db.execute("SELECT id, name, code FROM document_categories").fetchall()
        category_ids = [c['id'] for c in categories]

        # Get users
        users = db.execute("SELECT id, username FROM users LIMIT 5").fetchall()
        user_ids = [u['id'] for u in users] if users else [1]
        if not user_ids:
            user_ids = [1]

        # Get branches
        branches = db.execute("SELECT id FROM company_branches LIMIT 3").fetchall()
        branch_ids = [b['id'] for b in branches] if branches else [1]

        # Get departments
        departments = db.execute("SELECT id FROM hr_departments LIMIT 5").fetchall()
        dept_ids = [d['id'] for d in departments] if departments else [1]

        # Seed documents
        documents_data = [
            {
                'title': 'Q1 2026 Sales Quotation - Al Futtaim Group',
                'code': 'DOC-20260115-0001',
                'category': 'QUOTATION',
                'status': 'Published',
                'visibility': 'Company',
                'source_module': 'sales',
                'tags': ['Quotation', 'Sales', '重要客户'],
                'description': 'Annual service quotation for Al Futtaim Group facilities management contract renewal.',
                'file_size': 245760,
                'mime_type': 'application/pdf',
            },
            {
                'title': 'Supplier Agreement - Emirates Industrial LLC',
                'code': 'DOC-20260112-0002',
                'category': 'CONTRACT',
                'status': 'Signed',
                'visibility': 'Private',
                'source_module': 'procurement',
                'tags': ['Contract', 'Supplier', 'Signed'],
                'description': 'Three-year supply agreement with Emirates Industrial for raw materials.',
                'file_size': 524288,
                'mime_type': 'application/pdf',
            },
            {
                'title': 'ISO 9001:2015 Quality Manual',
                'code': 'DOC-20260110-0003',
                'category': 'QUALITY',
                'status': 'Published',
                'visibility': 'Company',
                'source_module': 'quality',
                'tags': ['ISO', 'Quality', 'Certified'],
                'description': 'Company quality management system manual compliant with ISO 9001:2015 standards.',
                'file_size': 1048576,
                'mime_type': 'application/pdf',
            },
            {
                'title': 'Employee Handbook 2026',
                'code': 'DOC-20260108-0004',
                'category': 'HR',
                'status': 'Published',
                'visibility': 'Company',
                'source_module': 'hr',
                'tags': ['HR', 'Policy', 'Employee'],
                'description': 'Updated employee handbook covering policies, procedures, and code of conduct.',
                'file_size': 786432,
                'mime_type': 'application/pdf',
            },
            {
                'title': 'Annual Financial Report FY2025',
                'code': 'DOC-20260105-0005',
                'category': 'FINANCE',
                'status': 'Approved',
                'visibility': 'Company',
                'source_module': 'finance',
                'tags': ['Financial', 'Annual Report', 'Confidential'],
                'description': 'Audited financial statements and management discussion for fiscal year 2025.',
                'file_size': 2097152,
                'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            },
            {
                'title': 'Warehouse Safety Procedures',
                'code': 'DOC-20260103-0006',
                'category': 'QUALITY',
                'status': 'Published',
                'visibility': 'Branch',
                'source_module': 'wms',
                'tags': ['Safety', 'Warehouse', 'Operations'],
                'description': 'Comprehensive safety procedures for warehouse operations including HAZMAT handling.',
                'file_size': 358400,
                'mime_type': 'application/pdf',
            },
            {
                'title': 'Service Level Agreement - Dubai Mall',
                'code': 'DOC-20251228-0007',
                'category': 'CONTRACT',
                'status': 'Pending Signature',
                'visibility': 'Company',
                'source_module': 'sales',
                'tags': ['SLA', 'Service', 'Pending'],
                'description': 'Facilities management SLA for Dubai Mall shopping complex.',
                'file_size': 614400,
                'mime_type': 'application/pdf',
            },
            {
                'title': 'Maintenance Work Order Template',
                'code': 'DOC-20251220-0008',
                'category': 'TECHNICAL',
                'status': 'Published',
                'visibility': 'Department',
                'source_module': 'maintenance',
                'tags': ['Template', 'Maintenance', 'Work Order'],
                'description': 'Standard template for preventive and corrective maintenance work orders.',
                'file_size': 102400,
                'mime_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            },
            {
                'title': 'Customer Invoice #INV-2026-0042',
                'code': 'DOC-20251215-0009',
                'category': 'INVOICE',
                'status': 'Published',
                'visibility': 'Company',
                'source_module': 'finance',
                'tags': ['Invoice', 'Sales', 'Finance'],
                'description': 'Monthly service invoice for January 2026 services rendered.',
                'file_size': 153600,
                'mime_type': 'application/pdf',
            },
            {
                'title': 'Equipment Calibration Certificate - HVAC',
                'code': 'DOC-20251210-0010',
                'category': 'QUALITY',
                'status': 'Approved',
                'visibility': 'Company',
                'source_module': 'maintenance',
                'tags': ['Calibration', 'HVAC', 'Certification'],
                'description': 'Annual calibration certificate for building HVAC monitoring equipment.',
                'file_size': 204800,
                'mime_type': 'application/pdf',
            },
            {
                'title': 'Project Proposal - Abu Dhabi Mall Expansion',
                'code': 'DOC-20251205-0011',
                'category': 'QUOTATION',
                'status': 'Under Review',
                'visibility': 'Company',
                'source_module': 'projects',
                'tags': ['Proposal', 'Project', 'Abu Dhabi'],
                'description': 'Technical and commercial proposal for mall expansion project Phase 2.',
                'file_size': 819200,
                'mime_type': 'application/pdf',
            },
            {
                'title': 'Non-Conformance Report NCR-2026-0012',
                'code': 'DOC-20251201-0012',
                'category': 'QUALITY',
                'status': 'Resolved',
                'visibility': 'Company',
                'source_module': 'quality',
                'tags': ['NCR', 'Quality', 'Resolved'],
                'description': 'NCR for delayed delivery of spare parts from supplier XYZ.',
                'file_size': 128000,
                'mime_type': 'application/pdf',
            },
        ]

        for i, doc_data in enumerate(documents_data):
            doc_id = insert_document(db, doc_data, user_ids, category_ids, branch_ids, dept_ids)
            
            # Add version
            insert_version(db, doc_id, doc_data, user_ids[0])
            
            # Add some links
            if doc_data['source_module'] in ['sales', 'procurement', 'finance', 'quality', 'maintenance', 'hr']:
                insert_link(db, doc_id, doc_data['source_module'], random.randint(1, 100), user_ids[0])
        
        # Seed templates
        templates_data = [
            {
                'name': 'Standard Quotation Template',
                'code': 'TPL-0001',
                'type': 'Sales',
                'output_format': 'DOCX',
                'category': 'QUOTATION',
                'description': 'Professional quotation template for sales quotations',
                'content': '''QUOTATION

Company: {{company_name}}
Date: {{quote_date}}
Quotation No: {{quote_number}}

Customer: {{customer_name}}
Contact: {{customer_contact}}
Address: {{customer_address}}

We are pleased to submit our quotation for the following services:

{{service_details}}

Total Amount: {{total_amount}} {{currency}}
Validity: {{validity_days}} days
Payment Terms: {{payment_terms}}

Terms and Conditions:
{{terms_and_conditions}}

Authorized By: ___________________
Date: ___________________
''',
            },
            {
                'name': 'Service Agreement Template',
                'code': 'TPL-0002',
                'type': 'Legal',
                'output_format': 'DOCX',
                'category': 'CONTRACT',
                'description': 'Master service agreement template for long-term contracts',
                'content': '''SERVICE AGREEMENT

This Agreement is entered into on {{agreement_date}}

BETWEEN:
{{company_name}} ("Service Provider")
AND:
{{client_name}} ("Client")

1. SCOPE OF SERVICES
{{scope_of_services}}

2. TERM
This Agreement shall commence on {{start_date}} and continue for {{term_months}} months.

3. FEES AND PAYMENT
Total Monthly Fee: {{monthly_fee}} {{currency}}
Payment Due: {{payment_due_day}} of each month

4. CONFIDENTIALITY
{{confidentiality_clause}}

5. TERMINATION
{{termination_clause}}

SIGNATURES:

Service Provider: ___________________ Date: ___________________

Client: ___________________ Date: ___________________
''',
            },
            {
                'name': 'Work Order Form',
                'code': 'TPL-0003',
                'type': 'Operations',
                'output_format': 'DOCX',
                'category': 'TECHNICAL',
                'description': 'Standard work order form for maintenance operations',
                'content': '''WORK ORDER

Work Order No: {{work_order_number}}
Date: {{work_order_date}}

Location: {{work_location}}
Priority: {{priority}}

Requester: {{requester_name}}
Contact: {{requester_phone}}

Description of Work:
{{work_description}}

Assigned To: {{assigned_technician}}
Scheduled Date: {{scheduled_date}}
Estimated Hours: {{estimated_hours}}

Materials Required:
{{materials_list}}

Completed By: ___________________
Completion Date: ___________________
Work Notes: {{work_notes}}
''',
            },
            {
                'name': 'Invoice Template',
                'code': 'TPL-0004',
                'type': 'Finance',
                'output_format': 'DOCX',
                'category': 'INVOICE',
                'description': 'Professional invoice template',
                'content': '''INVOICE

Invoice No: {{invoice_number}}
Date: {{invoice_date}}
Due Date: {{due_date}}

Bill To:
{{customer_name}}
{{customer_address}}
{{customer_vat}}

From:
{{company_name}}
{{company_address}}
{{company_vat}}

Description: {{service_description}}
Amount: {{subtotal}} {{currency}}
VAT ({{vat_rate}}%): {{vat_amount}} {{currency}}
Total: {{total_amount}} {{currency}}

Payment Instructions:
{{payment_instructions}}
''',
            },
            {
                'name': 'Quality Inspection Report',
                'code': 'TPL-0005',
                'type': 'Quality',
                'output_format': 'DOCX',
                'category': 'QUALITY',
                'description': 'Template for quality inspection reports',
                'content': '''QUALITY INSPECTION REPORT

Report No: {{report_number}}
Date: {{inspection_date}}
Inspector: {{inspector_name}}

Location: {{inspection_location}}
Reference: {{reference_number}}

ITEMS INSPECTED:
{{inspection_items}}

FINDINGS:
{{inspection_findings}}

RESULT: {{inspection_result}} [PASS/FAIL/CONDITIONAL]

Verified By: ___________________
Date: ___________________

Quality Manager: ___________________
Date: ___________________
''',
            },
        ]

        for tpl_data in templates_data:
            insert_template(db, tpl_data, user_ids[0], category_ids)

        # Seed some signature requests
        signature_requests_data = [
            {
                'title': 'Contract Approval - Emirates Industrial LLC',
                'document_idx': 1,  # Supplier Agreement
                'signers': user_ids[:3] if len(user_ids) >= 3 else user_ids,
                'status': 'Completed',
                'priority': 'High',
            },
            {
                'title': 'SLA Approval - Dubai Mall',
                'document_idx': 6,  # SLA - Dubai Mall
                'signers': user_ids[:2] if len(user_ids) >= 2 else user_ids,
                'status': 'Pending',
                'priority': 'Normal',
            },
        ]

        for sig_data in signature_requests_data:
            insert_signature_request(db, sig_data, user_ids)

        # Seed access logs
        for _ in range(20):
            insert_access_log(db, random.choice([1, 2, 3]), random.choice(['View', 'Download', 'Upload']), user_ids[0])

        db.commit()
        print(f"Successfully seeded document management demo data!")
        print(f"  - {len(documents_data)} documents")
        print(f"  - {len(templates_data)} templates")
        print(f"  - {len(signature_requests_data)} signature requests")
        print(f"  - 20 access logs")

    except Exception as e:
        print(f"Error seeding document data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def insert_document(db, doc_data, user_ids, category_ids, branch_ids, dept_ids):
    """Insert a document record."""
    cursor = db.execute("""
        INSERT INTO documents (
            document_code, title, description, category_id, status, visibility,
            source_module, owner_user_id, created_by_user_id, company_id,
            branch_id, department_id, file_size, mime_type, is_latest,
            signature_status, tags_json, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        doc_data['code'],
        doc_data['title'],
        doc_data['description'],
        random.choice(category_ids) if category_ids else None,
        doc_data['status'],
        doc_data['visibility'],
        doc_data['source_module'],
        random.choice(user_ids),
        random.choice(user_ids),
        1,  # company_id
        random.choice(branch_ids) if branch_ids else None,
        random.choice(dept_ids) if dept_ids else None,
        doc_data['file_size'],
        doc_data['mime_type'],
        1,
        'Signed' if doc_data['status'] == 'Signed' else ('Pending Signature' if doc_data['status'] == 'Pending Signature' else 'Not Applicable'),
        json.dumps(doc_data['tags']),
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    ))
    return cursor.lastrowid


def insert_version(db, document_id, doc_data, user_id):
    """Insert a document version."""
    import uuid
    stored_filename = f"demo_{uuid.uuid4().hex[:8]}.pdf"
    
    cursor = db.execute("""
        INSERT INTO document_versions (
            document_id, version_number, file_name, file_path,
            file_size, mime_type, is_current_version, status,
            created_by_user_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        document_id,
        '1.0',
        f"{doc_data['code']}.pdf",
        f"/static/uploads/documents/{stored_filename}",
        doc_data['file_size'],
        doc_data['mime_type'],
        1,
        'Published',
        user_id,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    ))
    
    version_id = cursor.lastrowid
    
    # Update document with version
    db.execute("UPDATE documents SET current_version_id = ? WHERE id = ?", (version_id, document_id))
    
    return version_id


def insert_link(db, document_id, module, record_id, user_id):
    """Insert a document link."""
    db.execute("""
        INSERT INTO document_links (
            document_id, linked_module, linked_record_id, link_type,
            is_primary, created_by_user_id, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        document_id,
        module,
        record_id,
        'Related',
        1,
        user_id,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    ))


def insert_template(db, tpl_data, user_id, category_ids):
    """Insert a document template."""
    cursor = db.execute("""
        INSERT INTO document_templates (
            template_name, template_code, description, template_type,
            output_format, category_id, content_template,
            is_active, owner_user_id, created_by_user_id,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        tpl_data['name'],
        tpl_data['code'],
        tpl_data['description'],
        tpl_data['type'],
        tpl_data['output_format'],
        random.choice(category_ids) if category_ids else None,
        tpl_data['content'],
        1,
        user_id,
        user_id,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    ))
    
    template_id = cursor.lastrowid
    
    # Extract and insert placeholders
    import re
    placeholders = re.findall(r'\{\{(\w+)\}\}', tpl_data['content'])
    for i, ph in enumerate(set(placeholders)):
        db.execute("""
            INSERT INTO template_placeholders (
                template_id, placeholder_key, placeholder_label,
                is_required, sort_order
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            template_id,
            ph,
            ph.replace('_', ' ').title(),
            0,
            i,
        ))
    
    return template_id


def insert_signature_request(db, sig_data, user_ids):
    """Insert a signature request and participants."""
    # Get a document
    docs = db.execute("SELECT id FROM documents LIMIT ?", (sig_data['document_idx'],)).fetchall()
    if not docs:
        return
    document_id = docs[0]['id']
    
    # Create request
    cursor = db.execute("""
        INSERT INTO signature_requests (
            request_code, document_id, request_title, request_message,
            requestor_user_id, priority, status,
            completed_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        f"SIG-{datetime.now().strftime('%Y%m%d')}-{random.randint(1, 99):04d}",
        document_id,
        sig_data['title'],
        f"Please review and sign this {sig_data['title']}",
        user_ids[0],
        sig_data['priority'],
        sig_data['status'],
        datetime.now().strftime('%Y-%m-%d %H:%M:%S') if sig_data['status'] == 'Completed' else None,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    ))
    request_id = cursor.lastrowid
    
    # Add participants
    for i, signer_id in enumerate(sig_data['signers']):
        signer = db.execute("SELECT username, email FROM users WHERE id = ?", (signer_id,)).fetchone()
        if signer:
            db.execute("""
                INSERT INTO signature_participants (
                    request_id, user_id, participant_name, participant_email,
                    participant_role, signing_order, status,
                    signed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request_id,
                signer_id,
                signer['username'],
                signer['email'],
                'Signer',
                i + 1,
                'Signed' if sig_data['status'] == 'Completed' else 'Pending',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S') if sig_data['status'] == 'Completed' else None,
            ))
    
    # Update document signature status
    if sig_data['status'] == 'Completed':
        db.execute("UPDATE documents SET signature_status = 'Signed' WHERE id = ?", (document_id,))
    elif sig_data['status'] == 'Pending':
        db.execute("UPDATE documents SET signature_status = 'Pending Signature' WHERE id = ?", (document_id,))


def insert_access_log(db, document_id, action, user_id):
    """Insert an access log."""
    db.execute("""
        INSERT INTO document_access_logs (
            document_id, user_id, access_action, access_type,
            ip_address, created_at
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        document_id,
        user_id,
        action,
        'Web',
        '192.168.1.' + str(random.randint(1, 255)),
        (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d %H:%M:%S'),
    ))


if __name__ == '__main__':
    seed_document_demo_data()
