"""
Comprehensive seed data script for Document Management System.
Creates realistic sample data across all document-related tables.
"""

import sqlite3
import os
import random
from datetime import datetime, timedelta

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'warehouse.db'))

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def seed_documents():
    """Seed comprehensive document data."""
    db = get_db()
    try:
        # Get existing data for references
        users = db.execute("SELECT id, username FROM users LIMIT 20").fetchall()

        if not users:
            print("No users found. Please ensure seed data is run first.")
            return

        user_ids = [u['id'] for u in users]

        # Handle optional tables
        try:
            categories = db.execute("SELECT id, code FROM document_categories").fetchall()
            category_ids = [c['id'] for c in categories] if categories else [1]
        except:
            category_ids = [1]

        try:
            companies = db.execute("SELECT id FROM companies LIMIT 5").fetchall()
            company_ids = [c['id'] for c in companies] if companies else [1]
        except:
            company_ids = [1]

        try:
            departments = db.execute("SELECT id FROM departments LIMIT 10").fetchall()
            dept_ids = [d['id'] for d in departments] if departments else [1]
        except:
            dept_ids = [1]

        statuses = ['Draft', 'Under Review', 'Approved', 'Published', 'Obsolete']
        visibility_options = ['Private', 'Department', 'Company', 'Public']

        document_templates = [
            ('Contract Agreement', 'CONTRACT', 'Legal contracts and agreements'),
            ('Invoice Template', 'INVOICE', 'Standard invoice format'),
            ('Purchase Order', 'PO', 'Purchase order documents'),
            ('Quotation Form', 'QUOTATION', 'Sales quotation template'),
            ('Delivery Note', 'DELIVERY', 'Delivery acknowledgment form'),
            ('HR Policy Document', 'HR', 'Human resources policies'),
            ('Quality Report', 'QUALITY', 'Quality assurance reports'),
            ('Financial Statement', 'FINANCE', 'Financial reporting templates'),
            ('Technical Manual', 'TECHNICAL', 'Technical specifications'),
            ('Meeting Minutes', 'CORRESPONDENCE', 'Meeting notes template'),
        ]

        # Create documents
        docs_created = 0
        for i in range(50):
            template = random.choice(document_templates)
            cat_id = random.choice(category_ids)
            owner_id = random.choice(user_ids)
            creator_id = random.choice(user_ids)
            company_id = random.choice(company_ids)
            dept_id = random.choice(dept_ids)

            doc_code = f"DOC-{datetime.now().strftime('%Y%m%d')}-{i+1:04d}"
            title = f"{template[0]} #{i+1}"
            status = random.choice(statuses)
            visibility = random.choice(visibility_options)

            created_date = datetime.now() - timedelta(days=random.randint(1, 365))
            updated_date = created_date + timedelta(days=random.randint(0, 30))

            # Get category retention period
            cat_retention = db.execute(
                "SELECT retention_period_days FROM document_categories WHERE id = ?",
                (cat_id,)
            ).fetchone()
            retention_days = cat_retention['retention_period_days'] if cat_retention else 365

            expiry_date = created_date + timedelta(days=retention_days) if retention_days else None

            try:
                db.execute("""
                    INSERT INTO documents (
                        document_code, title, description, category_id, document_type,
                        mime_type, file_size, original_filename, storage_path,
                        company_id, department_id, owner_user_id, created_by_user_id,
                        source_module, status, visibility, is_latest, is_archived,
                        retention_date, expiry_date, metadata_json, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_code, title, template[2], cat_id, 'file',
                    'application/pdf', random.randint(10000, 5000000),
                    f"{title}.pdf", f"/documents/{doc_code}.pdf",
                    company_id, dept_id, owner_id, creator_id,
                    'Manual', status, visibility, 1, 0,
                    expiry_date, expiry_date,
                    '{"author": "System", "department": "General"}',
                    created_date.strftime('%Y-%m-%d %H:%M:%S'),
                    updated_date.strftime('%Y-%m-%d %H:%M:%S')
                ))
                docs_created += 1
            except sqlite3.IntegrityError:
                pass

        print(f"Created {docs_created} documents")

        # Create document versions for each document
        versions_created = 0
        doc_ids = db.execute("SELECT id FROM documents LIMIT 30").fetchall()
        for doc in doc_ids:
            for v in range(1, random.randint(2, 5)):
                version_date = datetime.now() - timedelta(days=random.randint(1, 180))
                try:
                    db.execute("""
                        INSERT INTO document_versions (
                            document_id, version_number, version_label, file_name,
                            file_path, file_size, mime_type, checksum,
                            is_current_version, is_published, created_by_user_id, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        doc['id'], f"{v}.0", f"Version {v}",
                        f"document_v{v}.pdf", f"/versions/doc{doc['id']}_v{v}.pdf",
                        random.randint(10000, 2000000), 'application/pdf',
                        f"hash_{doc['id']}_{v}",
                        1 if v == 3 else 0, 1 if v > 1 else 0,
                        random.choice(user_ids),
                        version_date.strftime('%Y-%m-%d %H:%M:%S')
                    ))
                    versions_created += 1
                except:
                    pass

        print(f"Created {versions_created} document versions")

        # Create signature requests
        sigs_created = 0
        sig_statuses = ['Pending', 'Completed', 'Canceled']
        for i in range(15):
            doc_id = random.choice([d['id'] for d in doc_ids])
            requestor = random.choice(user_ids)
            sig_status = random.choice(sig_statuses)
            created_date = datetime.now() - timedelta(days=random.randint(1, 90))

            sig_code = f"SIG-{datetime.now().strftime('%Y%m%d')}-{i+1:04d}"

            try:
                db.execute("""
                    INSERT INTO signature_requests (
                        request_code, document_id, request_title, request_message,
                        requestor_user_id, signature_type, sequential_signing,
                        status, priority, due_date, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sig_code, doc_id, f"Signature Request #{i+1}",
                    f"Please sign document {doc_id}", requestor,
                    'electronic', 1, sig_status, 'Normal',
                    created_date + timedelta(days=14),
                    created_date.strftime('%Y-%m-%d %H:%M:%S')
                ))
                sigs_created += 1
            except:
                pass

        print(f"Created {sigs_created} signature requests")

        # Create document reviews
        reviews_created = 0
        for i in range(10):
            doc_id = random.choice([d['id'] for d in doc_ids])
            reviewer = random.choice(user_ids)
            review_status = random.choice(['Pending', 'Completed', 'Overdue'])
            created_date = datetime.now() - timedelta(days=random.randint(1, 60))

            try:
                db.execute("""
                    INSERT INTO dms_document_reviews (
                        document_id, reviewer_user_id, review_status,
                        review_requested_at, due_date, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    doc_id, reviewer, review_status,
                    created_date.strftime('%Y-%m-%d %H:%M:%S'),
                    created_date + timedelta(days=7),
                    created_date.strftime('%Y-%m-%d %H:%M:%S')
                ))
                reviews_created += 1
            except:
                pass

        print(f"Created {reviews_created} document reviews")

        # Create document approvals
        approvals_created = 0
        for i in range(10):
            doc_id = random.choice([d['id'] for d in doc_ids])
            approver = random.choice(user_ids)
            approval_status = random.choice(['Pending', 'Approved', 'Rejected'])
            created_date = datetime.now() - timedelta(days=random.randint(1, 60))

            try:
                db.execute("""
                    INSERT INTO dms_document_approvals (
                        document_id, approver_user_id, approval_status,
                        approval_sequence, approval_requested_at, due_date, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_id, approver, approval_status, i % 3 + 1,
                    created_date.strftime('%Y-%m-%d %H:%M:%S'),
                    created_date + timedelta(days=10),
                    created_date.strftime('%Y-%m-%d %H:%M:%S')
                ))
                approvals_created += 1
            except:
                pass

        print(f"Created {approvals_created} document approvals")

        # Create retention policies
        policies = [
            ('Standard Retention', 'RET-001', 'Standard 7-year retention policy', 2555, 'creation_date', 1),
            ('Tax Documents', 'RET-002', 'Tax-related documents retention', 2555, 'creation_date', 1),
            ('HR Records', 'RET-003', 'Employee records retention', 3650, 'creation_date', 1),
            ('Contracts', 'RET-004', 'Contract and legal documents', 3650, 'creation_date', 1),
            ('Operational', 'RET-005', 'General operational documents', 730, 'creation_date', 0),
        ]

        policies_created = 0
        for name, code, desc, days, basis, archive in policies:
            try:
                db.execute("""
                    INSERT INTO document_retention_policies (
                        policy_name, policy_code, description, retention_period_days,
                        retention_basis, archive_before_delete, is_active, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 1, datetime('now'))
                """, (name, code, desc, days, basis, archive))
                policies_created += 1
            except:
                pass

        print(f"Created {policies_created} retention policies")

        # Create legal holds
        holds = [
            ('HR Investigation 2024', 'LH-2024-001', 'HR investigation hold', 'Legal', 'HR investigation in progress'),
            ('Litigation Hold - Case 123', 'LH-2024-002', 'Litigation preservation', 'Litigation', 'Active lawsuit'),
            ('Regulatory Investigation', 'LH-2024-003', 'Regulatory inquiry hold', 'Regulatory', 'Ongoing investigation'),
        ]

        holds_created = 0
        for name, ref, desc, htype, reason in holds:
            try:
                db.execute("""
                    INSERT INTO dms_legal_holds (
                        hold_name, hold_reference, description, hold_type,
                        reason, status, is_permanent, requested_by_user_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, datetime('now'))
                """, (name, ref, desc, htype, reason, 'Active', random.choice(user_ids)))
                holds_created += 1
            except:
                pass

        print(f"Created {holds_created} legal holds")

        # Create export presets
        presets = [
            ('Monthly Report CSV', 'EXP-CSV-001', 'CSV', 'document_code,title,category,status,created_at'),
            ('Audit Export Excel', 'EXP-XLS-001', 'Excel', 'code,title,owner,date,status'),
            ('Full JSON Export', 'EXP-JSON-001', 'JSON', 'all'),
            ('Compliance Archive', 'EXP-PDF-001', 'PDF', 'document_code,title,metadata'),
        ]

        presets_created = 0
        for name, code, fmt, cols in presets:
            try:
                db.execute("""
                    INSERT INTO dms_export_presets (
                        preset_name, preset_code, export_format, include_columns,
                        created_by_user_id, usage_count, created_at
                    ) VALUES (?, ?, ?, ?, ?, 0, datetime('now'))
                """, (name, code, fmt, cols, random.choice(user_ids)))
                presets_created += 1
            except:
                pass

        print(f"Created {presets_created} export presets")

        # Create metadata definitions
        metadata_fields = [
            ('department_code', 'Department Code', 'text', 1, 1, 1),
            ('confidentiality_level', 'Confidentiality Level', 'select', 1, 1, 1),
            ('project_reference', 'Project Reference', 'text', 0, 1, 1),
            ('cost_center', 'Cost Center', 'text', 0, 0, 1),
            ('expiration_warning', 'Expiration Warning Days', 'number', 0, 0, 0),
        ]

        metadata_created = 0
        for code, name, ftype, req, search, exp in metadata_fields:
            try:
                db.execute("""
                    INSERT INTO dms_metadata_definitions (
                        field_code, field_name, field_type, is_required,
                        is_searchable, is_exportable, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
                """, (code, name, ftype, req, search, exp))
                metadata_created += 1
            except:
                pass

        print(f"Created {metadata_created} metadata definitions")

        # Create document comments
        comments_created = 0
        comment_texts = [
            "Please review this document at your earliest convenience.",
            "Approved - ready for signature.",
            "Needs revision on section 3.",
            "Complies with all requirements.",
            "Please provide additional details.",
            "Confirmed receipt of document.",
            "Document archived as per policy.",
            "Updated version uploaded.",
        ]

        for i in range(20):
            doc_id = random.choice([d['id'] for d in doc_ids])
            user_id = random.choice(user_ids)
            created_date = datetime.now() - timedelta(days=random.randint(1, 90))

            try:
                db.execute("""
                    INSERT INTO dms_document_comments (
                        document_id, user_id, comment_text, created_at
                    ) VALUES (?, ?, ?, ?)
                """, (
                    doc_id, user_id,
                    random.choice(comment_texts),
                    created_date.strftime('%Y-%m-%d %H:%M:%S')
                ))
                comments_created += 1
            except:
                pass

        print(f"Created {comments_created} document comments")

        # Create ACL entries
        acl_created = 0
        permission_types = ['User', 'Role', 'Department']
        permission_levels = ['Read', 'Write', 'Admin', 'Full Control']

        for i in range(15):
            doc_id = random.choice([d['id'] for d in doc_ids])
            perm_type = random.choice(permission_types)
            perm_level = random.choice(permission_levels)
            granted_by = random.choice(user_ids)

            user_id = random.choice(user_ids) if perm_type == 'User' else None
            role_id = random.randint(1, 5) if perm_type == 'Role' else None

            try:
                db.execute("""
                    INSERT INTO dms_document_acl (
                        document_id, user_id, role_id, permission_type,
                        permission_level, granted_by_user_id, is_active, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 1, datetime('now'))
                """, (doc_id, user_id, role_id, perm_type, perm_level, granted_by))
                acl_created += 1
            except:
                pass

        print(f"Created {acl_created} ACL entries")

        # Create access logs
        logs_created = 0
        actions = ['View', 'Download', 'Upload', 'Edit', 'Share', 'Print']

        for i in range(100):
            doc_id = random.choice([d['id'] for d in doc_ids])
            user_id = random.choice(user_ids)
            action = random.choice(actions)
            created_date = datetime.now() - timedelta(days=random.randint(1, 60))

            try:
                db.execute("""
                    INSERT INTO document_access_logs (
                        document_id, user_id, access_action, access_type,
                        ip_address, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    doc_id, user_id, action, 'Web',
                    f"192.168.1.{random.randint(1, 254)}",
                    created_date.strftime('%Y-%m-%d %H:%M:%S')
                ))
                logs_created += 1
            except:
                pass

        print(f"Created {logs_created} access logs")

        db.commit()
        print("\n=== Document Management Seed Data Complete ===")
        print(f"Total documents: {docs_created}")
        print(f"Total versions: {versions_created}")
        print(f"Total signatures: {sigs_created}")
        print(f"Total reviews: {reviews_created}")
        print(f"Total approvals: {approvals_created}")
        print(f"Total policies: {policies_created}")
        print(f"Total legal holds: {holds_created}")
        print(f"Total presets: {presets_created}")
        print(f"Total metadata fields: {metadata_created}")
        print(f"Total comments: {comments_created}")
        print(f"Total ACL entries: {acl_created}")
        print(f"Total access logs: {logs_created}")

    finally:
        db.close()

if __name__ == '__main__':
    print("Seeding document management data...")
    seed_documents()