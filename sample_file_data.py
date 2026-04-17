"""
Sample Data Generator for File Management Module
Creates realistic folders, documents, and metadata for demo purposes.
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

DATABASE_PATH = 'warehouse.db'
UPLOAD_FOLDER = 'uploads/documents'

def get_db():
    """Get database connection."""
    return sqlite3.connect(DATABASE_PATH)

def create_sample_folders():
    """Create sample folder structure."""
    db = get_db()
    try:
        cursor = db.cursor()

        # Check if folders already exist
        cursor.execute("SELECT COUNT(*) FROM document_folders")
        if cursor.fetchone()[0] > 0:
            print("Sample folders already exist, skipping...")
            return

        now = datetime.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        # Root folders
        root_folders = [
            ('FLD-HR-001', 'Human Resources', None, 'hr', None, 1, 'Active', 0, None, None, '#4F46E5', 'fa-folder', 1, now, now),
            ('FLD-FIN-001', 'Finance & Accounting', None, 'finance', None, 1, 'Active', 0, None, None, '#10B981', 'fa-folder', 1, now, now),
            ('FLD-LEGAL-001', 'Legal & Compliance', None, 'legal', None, 1, 'Active', 0, None, None, '#EF4444', 'fa-folder', 1, now, now),
            ('FLD-PROC-001', 'Procurement', None, 'procurement', None, 1, 'Active', 0, None, None, '#F59E0B', 'fa-folder', 1, now, now),
            ('FLD-SALES-001', 'Sales & Marketing', None, 'sales', None, 1, 'Active', 0, None, None, '#3B82F6', 'fa-folder', 1, now, now),
            ('FLD-OPS-001', 'Operations', None, 'operations', None, 1, 'Active', 0, None, None, '#8B5CF6', 'fa-folder', 1, now, now),
            ('FLD-IT-001', 'IT & Systems', None, 'it', None, 1, 'Active', 0, None, None, '#06B6D4', 'fa-folder', 1, now, now),
            ('FLD-PROJ-001', 'Projects', None, 'projects', None, 1, 'Active', 0, None, None, '#EC4899', 'fa-folder', 1, now, now),
        ]

        cursor.executemany("""
            INSERT INTO document_folders (folder_code, name, description, folder_type, parent_id, owner_user_id,
                status, is_archived, archived_by_user_id, archived_at, color, icon, created_by_user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, root_folders)

        db.commit()

        # Get inserted folder IDs
        cursor.execute("SELECT id, folder_code FROM document_folders ORDER BY id")
        folder_map = {code: fid for fid, code in cursor.fetchall()}

        # Subfolders
        subfolders_data = [
            ('FLD-HR-002', 'Employee Records', None, 'hr', folder_map['FLD-HR-001'], 1, 'Active', 0, None, None, '#4F46E5', 'fa-folder', 1, month_ago, month_ago),
            ('FLD-HR-003', 'Policies & Procedures', None, 'hr', folder_map['FLD-HR-001'], 1, 'Active', 0, None, None, '#4F46E5', 'fa-folder', 1, month_ago, month_ago),
            ('FLD-HR-004', 'Training Materials', None, 'hr', folder_map['FLD-HR-001'], 1, 'Active', 0, None, None, '#4F46E5', 'fa-folder', 1, month_ago, month_ago),
            ('FLD-HR-005', 'Benefits & Payroll', None, 'hr', folder_map['FLD-HR-001'], 1, 'Active', 0, None, None, '#4F46E5', 'fa-folder', 1, month_ago, month_ago),
            ('FLD-FIN-002', 'Invoices', None, 'finance', folder_map['FLD-FIN-001'], 1, 'Active', 0, None, None, '#10B981', 'fa-folder', 1, month_ago, month_ago),
            ('FLD-FIN-003', 'Tax Documents', None, 'finance', folder_map['FLD-FIN-001'], 1, 'Active', 0, None, None, '#10B981', 'fa-folder', 1, month_ago, month_ago),
            ('FLD-FIN-004', 'Bank Statements', None, 'finance', folder_map['FLD-FIN-001'], 1, 'Active', 0, None, None, '#10B981', 'fa-folder', 1, month_ago, month_ago),
            ('FLD-FIN-005', 'Budgets', None, 'finance', folder_map['FLD-FIN-001'], 1, 'Active', 0, None, None, '#10B981', 'fa-folder', 1, month_ago, month_ago),
            ('FLD-LEGAL-002', 'Contracts', None, 'legal', folder_map['FLD-LEGAL-001'], 1, 'Active', 0, None, None, '#EF4444', 'fa-folder', 1, month_ago, month_ago),
            ('FLD-LEGAL-003', 'Compliance Reports', None, 'legal', folder_map['FLD-LEGAL-001'], 1, 'Active', 0, None, None, '#EF4444', 'fa-folder', 1, month_ago, month_ago),
            ('FLD-PROC-002', 'Purchase Orders', None, 'procurement', folder_map['FLD-PROC-001'], 1, 'Active', 0, None, None, '#F59E0B', 'fa-folder', 1, month_ago, month_ago),
            ('FLD-PROC-003', 'Vendor Contracts', None, 'procurement', folder_map['FLD-PROC-001'], 1, 'Active', 0, None, None, '#F59E0B', 'fa-folder', 1, month_ago, month_ago),
            ('FLD-SALES-002', 'Customer Contracts', None, 'sales', folder_map['FLD-SALES-001'], 1, 'Active', 0, None, None, '#3B82F6', 'fa-folder', 1, month_ago, month_ago),
            ('FLD-SALES-003', 'Proposals', None, 'sales', folder_map['FLD-SALES-001'], 1, 'Active', 0, None, None, '#3B82F6', 'fa-folder', 1, month_ago, month_ago),
            ('FLD-SALES-004', 'Marketing Materials', None, 'sales', folder_map['FLD-SALES-001'], 1, 'Active', 0, None, None, '#3B82F6', 'fa-folder', 1, month_ago, month_ago),
            ('FLD-OPS-002', 'Work Orders', None, 'operations', folder_map['FLD-OPS-001'], 1, 'Active', 0, None, None, '#8B5CF6', 'fa-folder', 1, month_ago, month_ago),
            ('FLD-OPS-003', 'Quality Records', None, 'operations', folder_map['FLD-OPS-001'], 1, 'Active', 0, None, None, '#8B5CF6', 'fa-folder', 1, month_ago, month_ago),
            ('FLD-IT-002', 'System Documentation', None, 'it', folder_map['FLD-IT-001'], 1, 'Active', 0, None, None, '#06B6D4', 'fa-folder', 1, month_ago, month_ago),
            ('FLD-IT-003', 'Software Licenses', None, 'it', folder_map['FLD-IT-001'], 1, 'Active', 0, None, None, '#06B6D4', 'fa-folder', 1, month_ago, month_ago),
            ('FLD-PROJ-002', '2024 Initiatives', None, 'projects', folder_map['FLD-PROJ-001'], 1, 'Active', 0, None, None, '#EC4899', 'fa-folder', 1, month_ago, month_ago),
            ('FLD-PROJ-003', 'Completed Projects', None, 'projects', folder_map['FLD-PROJ-001'], 1, 'Active', 0, None, None, '#EC4899', 'fa-folder', 1, month_ago, month_ago),
        ]

        cursor.executemany("""
            INSERT INTO document_folders (folder_code, name, description, folder_type, parent_id, owner_user_id,
                status, is_archived, archived_by_user_id, archived_at, color, icon, created_by_user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, subfolders_data)

        db.commit()
        print(f"Created {len(root_folders)} root folders and {len(subfolders_data)} subfolders")

    except Exception as e:
        print(f"Error creating sample folders: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_documents():
    """Create sample documents."""
    db = get_db()
    try:
        cursor = db.cursor()

        # Check if documents already exist
        cursor.execute("SELECT COUNT(*) FROM documents")
        if cursor.fetchone()[0] > 0:
            print("Sample documents already exist, skipping...")
            return

        now = datetime.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        year_ago = now - timedelta(days=365)

        # Get folder IDs
        cursor.execute("SELECT id, folder_code FROM document_folders")
        folder_map = {code: fid for fid, code in cursor.fetchall()}

        # Sample documents
        documents_data = [
            # HR Documents
            ('DOC-HR-001', 'Employee Handbook 2024', 'policy', folder_map.get('FLD-HR-003'), 1,
             'Active', 'HR', 'confidential', now - timedelta(days=30), None, None, None, 'pdf', 2457600, now, now),
            ('DOC-HR-002', 'Vacation Request Form', 'form', folder_map.get('FLD-HR-003'), 1,
             'Active', 'HR', 'internal', now - timedelta(days=15), None, None, None, 'docx', 156000, now, now),
            ('DOC-HR-003', 'Performance Review Template', 'template', folder_map.get('FLD-HR-003'), 1,
             'Active', 'HR', 'internal', now - timedelta(days=60), None, None, None, 'xlsx', 89000, now, now),
            ('DOC-HR-004', 'New Hire Checklist', 'checklist', folder_map.get('FLD-HR-002'), 1,
             'Active', 'HR', 'internal', now - timedelta(days=45), None, None, None, 'pdf', 340000, now, now),
            ('DOC-HR-005', 'Benefits Enrollment Guide', 'guide', folder_map.get('FLD-HR-005'), 1,
             'Active', 'HR', 'confidential', now - timedelta(days=90), None, None, None, 'pdf', 1200000, now, now),

            # Finance Documents
            ('DOC-FIN-001', 'Q4 2024 Financial Statement', 'report', folder_map.get('FLD-FIN-002'), 1,
             'Active', 'Finance', 'confidential', now - timedelta(days=10), None, None, None, 'pdf', 4500000, now, now),
            ('DOC-FIN-002', 'Invoice INV-2024-001', 'invoice', folder_map.get('FLD-FIN-002'), 1,
             'Active', 'Finance', 'confidential', now - timedelta(days=5), None, None, None, 'pdf', 340000, now, now),
            ('DOC-FIN-003', 'Tax Return 2023', 'tax', folder_map.get('FLD-FIN-003'), 1,
             'Active', 'Finance', 'confidential', year_ago, None, None, None, 'pdf', 5600000, now, now),
            ('DOC-FIN-004', 'Bank Reconciliation Oct', 'statement', folder_map.get('FLD-FIN-004'), 1,
             'Active', 'Finance', 'confidential', now - timedelta(days=20), None, None, None, 'xlsx', 780000, now, now),
            ('DOC-FIN-005', 'Budget Forecast 2025', 'budget', folder_map.get('FLD-FIN-005'), 1,
             'Active', 'Finance', 'restricted', now - timedelta(days=7), None, None, None, 'xlsx', 1200000, now, now),

            # Legal Documents
            ('DOC-LEG-001', 'Service Agreement Template', 'contract', folder_map.get('FLD-LEGAL-002'), 1,
             'Active', 'Legal', 'confidential', now - timedelta(days=60), None, None, None, 'docx', 890000, now, now),
            ('DOC-LEG-002', 'NDA Standard Template', 'contract', folder_map.get('FLD-LEGAL-002'), 1,
             'Active', 'Legal', 'confidential', now - timedelta(days=120), None, None, None, 'docx', 450000, now, now),
            ('DOC-LEG-003', 'Annual Compliance Report 2023', 'report', folder_map.get('FLD-LEGAL-003'), 1,
             'Active', 'Legal', 'confidential', year_ago, None, None, None, 'pdf', 3400000, now, now),

            # Procurement Documents
            ('DOC-PROC-001', 'PO-2024-001', 'purchase_order', folder_map.get('FLD-PROC-002'), 1,
             'Active', 'Procurement', 'internal', now - timedelta(days=3), None, None, None, 'pdf', 230000, now, now),
            ('DOC-PROC-002', 'Vendor Registration Form', 'form', folder_map.get('FLD-PROC-003'), 1,
             'Active', 'Procurement', 'internal', now - timedelta(days=45), None, None, None, 'docx', 180000, now, now),
            ('DOC-PROC-003', 'Supplier Agreement Acme Corp', 'contract', folder_map.get('FLD-PROC-003'), 1,
             'Active', 'Procurement', 'confidential', now - timedelta(days=30), None, None, None, 'pdf', 1200000, now, now),

            # Sales Documents
            ('DOC-SALES-001', 'Contract - BigCorp Inc', 'contract', folder_map.get('FLD-SALES-002'), 1,
             'Active', 'Sales', 'confidential', now - timedelta(days=14), None, None, None, 'pdf', 2300000, now, now),
            ('DOC-SALES-002', 'Proposal - TechStart Solutions', 'proposal', folder_map.get('FLD-SALES-003'), 1,
             'Active', 'Sales', 'internal', now - timedelta(days=7), None, None, None, 'pdf', 1800000, now, now),
            ('DOC-SALES-003', 'Product Brochure 2024', 'marketing', folder_map.get('FLD-SALES-004'), 1,
             'Active', 'Sales', 'public', now - timedelta(days=60), None, None, None, 'pdf', 5600000, now, now),
            ('DOC-SALES-004', 'Price List 2024', 'price_list', folder_map.get('FLD-SALES-004'), 1,
             'Active', 'Sales', 'internal', now - timedelta(days=30), None, None, None, 'xlsx', 340000, now, now),

            # Operations Documents
            ('DOC-OPS-001', 'Work Order WO-2024-001', 'work_order', folder_map.get('FLD-OPS-002'), 1,
             'Active', 'Operations', 'internal', now - timedelta(days=2), None, None, None, 'pdf', 450000, now, now),
            ('DOC-OPS-002', 'Quality Control Procedure', 'procedure', folder_map.get('FLD-OPS-003'), 1,
             'Active', 'Operations', 'internal', now - timedelta(days=90), None, None, None, 'pdf', 1200000, now, now),
            ('DOC-OPS-003', 'Inspection Report Q3', 'report', folder_map.get('FLD-OPS-003'), 1,
             'Active', 'Operations', 'internal', now - timedelta(days=20), None, None, None, 'pdf', 2300000, now, now),

            # IT Documents
            ('DOC-IT-001', 'Network Architecture Diagram', 'diagram', folder_map.get('FLD-IT-002'), 1,
             'Active', 'IT', 'confidential', now - timedelta(days=45), None, None, None, 'pdf', 890000, now, now),
            ('DOC-IT-002', 'Software License Inventory', 'inventory', folder_map.get('FLD-IT-003'), 1,
             'Active', 'IT', 'internal', now - timedelta(days=30), None, None, None, 'xlsx', 560000, now, now),
            ('DOC-IT-003', 'IT Security Policy', 'policy', folder_map.get('FLD-IT-002'), 1,
             'Active', 'IT', 'confidential', now - timedelta(days=180), None, None, None, 'pdf', 1800000, now, now),

            # Project Documents
            ('DOC-PROJ-001', 'Project Charter - ERP Upgrade', 'charter', folder_map.get('FLD-PROJ-002'), 1,
             'Active', 'Projects', 'internal', now - timedelta(days=60), None, None, None, 'pdf', 3400000, now, now),
            ('DOC-PROJ-002', 'Status Report - ERP Upgrade', 'report', folder_map.get('FLD-PROJ-002'), 1,
             'Active', 'Projects', 'internal', now - timedelta(days=7), None, None, None, 'pdf', 1200000, now, now),
            ('DOC-PROJ-003', 'Lessons Learned - Warehouse Project', 'report', folder_map.get('FLD-PROJ-003'), 1,
             'Active', 'Projects', 'internal', year_ago, None, None, None, 'pdf', 2300000, now, now),
        ]

        cursor.executemany("""
            INSERT INTO documents (document_code, title, document_type, folder_id, owner_user_id,
                visibility, department, confidentiality, created_at, signed_at, signature_status,
                signature_type, file_type, file_size, updated_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, documents_data)

        db.commit()
        print(f"Created {len(documents_data)} sample documents")

    except Exception as e:
        print(f"Error creating sample documents: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_versions():
    """Create sample document versions."""
    db = get_db()
    try:
        cursor = db.cursor()

        # Check if versions exist
        cursor.execute("SELECT COUNT(*) FROM document_versions")
        if cursor.fetchone()[0] > 0:
            print("Sample versions already exist, skipping...")
            return

        now = datetime.now()

        # Get document IDs
        cursor.execute("SELECT id, document_code FROM documents")
        doc_map = {code: did for did, code in cursor.fetchall()}

        versions_data = [
            # Financial statement has multiple versions
            (doc_map.get('DOC-FIN-001'), 1, 'Initial draft', 1, now - timedelta(days=20), 'v1_initial.pdf'),
            (doc_map.get('DOC-FIN-001'), 2, 'Added executive summary', 1, now - timedelta(days=15), 'v2_summary.pdf'),
            (doc_map.get('DOC-FIN-001'), 3, 'Final version approved', 1, now - timedelta(days=10), 'v3_final.pdf'),
            # Employee handbook updates
            (doc_map.get('DOC-HR-001'), 1, 'Initial version', 1, now - timedelta(days=90), 'handbook_v1.pdf'),
            (doc_map.get('DOC-HR-001'), 2, 'Policy updates Q2', 1, now - timedelta(days=30), 'handbook_v2.pdf'),
            # Contract revisions
            (doc_map.get('DOC-LEG-001'), 1, 'Original template', 1, now - timedelta(days=120), 'contract_v1.docx'),
            (doc_map.get('DOC-LEG-001'), 2, 'Legal review changes', 1, now - timedelta(days=90), 'contract_v2.docx'),
            (doc_map.get('DOC-LEG-001'), 3, 'Final approved version', 1, now - timedelta(days=60), 'contract_v3.docx'),
        ]

        cursor.executemany("""
            INSERT INTO document_versions (document_id, version_number, notes, uploaded_by_user_id,
                uploaded_at, file_name)
            VALUES (?, ?, ?, ?, ?, ?)
        """, versions_data)

        # Update documents with current version
        for doc_code, version_num in [('DOC-FIN-001', 3), ('DOC-HR-001', 2), ('DOC-LEG-001', 3)]:
            doc_id = doc_map.get(doc_code)
            if doc_id:
                cursor.execute("""
                    UPDATE documents SET current_version_id = (
                        SELECT id FROM document_versions
                        WHERE document_id = ? AND version_number = ?
                    )
                    WHERE id = ?
                """, (doc_id, version_num, doc_id))

        db.commit()
        print(f"Created {len(versions_data)} sample versions")

    except Exception as e:
        print(f"Error creating sample versions: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_tags():
    """Create sample tags."""
    db = get_db()
    try:
        cursor = db.cursor()

        # Check if tags exist
        cursor.execute("SELECT COUNT(*) FROM document_tags")
        if cursor.fetchone()[0] > 0:
            print("Sample tags already exist, skipping...")
            return

        now = datetime.now()

        # Tags
        tags_data = [
            ('urgent', 'Urgent', '#EF4444'),
            ('review', 'Needs Review', '#F59E0B'),
            ('approved', 'Approved', '#10B981'),
            ('confidential', 'Confidential', '#7C3AED'),
            ('archived', 'Archived', '#6B7280'),
            ('contract', 'Contract', '#3B82F6'),
            ('report', 'Report', '#06B6D4'),
            ('template', 'Template', '#8B5CF6'),
        ]

        cursor.executemany("""
            INSERT INTO document_tags (tag_name, display_name, color, created_at)
            VALUES (?, ?, ?, ?)
        """, [(t[0], t[1], t[2], now) for t in tags_data])

        db.commit()
        print(f"Created {len(tags_data)} sample tags")

    except Exception as e:
        print(f"Error creating sample tags: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_categories():
    """Create sample document categories."""
    db = get_db()
    try:
        cursor = db.cursor()

        # Check if categories exist
        cursor.execute("SELECT COUNT(*) FROM document_categories")
        if cursor.fetchone()[0] > 0:
            print("Sample categories already exist, skipping...")
            return

        now = datetime.now()

        categories_data = [
            ('contract', 'Contracts', 'fa-file-contract', '#3B82F6'),
            ('invoice', 'Invoices', 'fa-file-invoice', '#10B981'),
            ('report', 'Reports', 'fa-file-alt', '#F59E0B'),
            ('policy', 'Policies', 'fa-file-shield', '#7C3AED'),
            ('form', 'Forms', 'fa-file-lines', '#06B6D4'),
            ('template', 'Templates', 'fa-file-code', '#8B5CF6'),
            ('procedure', 'Procedures', 'fa-file-lines', '#EC4899'),
            ('certificate', 'Certificates', 'fa-file-certificate', '#14B8A6'),
        ]

        cursor.executemany("""
            INSERT INTO document_categories (category_name, display_name, icon, color, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, [(c[0], c[1], c[2], c[3], now) for c in categories_data])

        db.commit()
        print(f"Created {len(categories_data)} sample categories")

    except Exception as e:
        print(f"Error creating sample categories: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_favorites():
    """Create sample favorites for user 1."""
    db = get_db()
    try:
        cursor = db.cursor()

        # Check if favorites exist
        cursor.execute("SELECT COUNT(*) FROM document_favorites")
        if cursor.fetchone()[0] > 0:
            print("Sample favorites already exist, skipping...")
            return

        now = datetime.now()

        # Get some document IDs
        cursor.execute("SELECT id FROM documents LIMIT 5")
        doc_ids = [row[0] for row in cursor.fetchall()]

        favorites_data = [(doc_id, 1, now) for doc_id in doc_ids]

        cursor.executemany("""
            INSERT INTO document_favorites (document_id, user_id, created_at)
            VALUES (?, ?, ?)
        """, favorites_data)

        db.commit()
        print(f"Created {len(favorites_data)} sample favorites")

    except Exception as e:
        print(f"Error creating sample favorites: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_folder_permissions():
    """Create sample folder permissions."""
    db = get_db()
    try:
        cursor = db.cursor()

        # Check if permissions exist
        cursor.execute("SELECT COUNT(*) FROM folder_permissions")
        if cursor.fetchone()[0] > 0:
            print("Sample folder permissions already exist, skipping...")
            return

        now = datetime.now()

        # Get folder IDs
        cursor.execute("SELECT id FROM document_folders LIMIT 5")
        folder_ids = [row[0] for row in cursor.fetchall()]

        # Create permissions for different roles
        permissions_data = []
        for i, folder_id in enumerate(folder_ids):
            permissions_data.append((folder_id, 1, None, 'full_control', None, now, now, now))  # Admin full access
            if i < 3:
                permissions_data.append((folder_id, 2, None, 'read', None, now, now, now))  # User 2 read access
                permissions_data.append((folder_id, 3, None, 'read_write', None, now, now, now))  # User 3 read/write

        cursor.executemany("""
            INSERT INTO folder_permissions (folder_id, user_id, role_id, permission_level, granted_by_user_id, expires_at, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, permissions_data)

        db.commit()
        print(f"Created {len(permissions_data)} sample folder permissions")

    except Exception as e:
        print(f"Error creating sample folder permissions: {e}")
        db.rollback()
    finally:
        db.close()

def init_sample_data():
    """Initialize all sample data."""
    print("Initializing sample data for File Management module...")

    # Ensure tables exist
    from document_models import initialize_document_tables
    initialize_document_tables()

    # Create sample data
    create_sample_categories()
    create_sample_tags()
    create_sample_folders()
    create_sample_documents()
    create_sample_versions()
    create_sample_favorites()
    create_sample_folder_permissions()

    print("Sample data initialization complete!")

if __name__ == '__main__':
    init_sample_data()
