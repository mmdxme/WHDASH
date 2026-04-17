# File Management Sample Data Guide

## Overview

This document describes the sample data created for the File Management module. The sample data provides a realistic demonstration environment with folders, documents, versions, tags, categories, and user interactions.

## Running Sample Data

To initialize sample data, run:

```bash
python sample_file_data.py
```

This will create sample data only if the database tables are empty.

## Sample Folder Structure

### Root Folders

| Code | Name | Type | Description |
|------|------|------|-------------|
| FLD-HR-001 | Human Resources | hr | HR department documents |
| FLD-FIN-001 | Finance & Accounting | finance | Financial documents |
| FLD-LEGAL-001 | Legal & Compliance | legal | Legal documents |
| FLD-PROC-001 | Procurement | procurement | Procurement documents |
| FLD-SALES-001 | Sales & Marketing | sales | Sales documents |
| FLD-OPS-001 | Operations | operations | Operational documents |
| FLD-IT-001 | IT & Systems | it | IT documentation |
| FLD-PROJ-001 | Projects | projects | Project documentation |

### Subfolders

| Code | Name | Parent | Description |
|------|------|--------|-------------|
| FLD-HR-002 | Employee Records | Human Resources | Personal files |
| FLD-HR-003 | Policies & Procedures | Human Resources | Company policies |
| FLD-HR-004 | Training Materials | Human Resources | Training docs |
| FLD-HR-005 | Benefits & Payroll | Human Resources | Benefits info |
| FLD-FIN-002 | Invoices | Finance | Invoice records |
| FLD-FIN-003 | Tax Documents | Finance | Tax filings |
| FLD-FIN-004 | Bank Statements | Finance | Bank records |
| FLD-FIN-005 | Budgets | Finance | Budget docs |
| FLD-LEGAL-002 | Contracts | Legal | Legal contracts |
| FLD-LEGAL-003 | Compliance Reports | Legal | Compliance docs |
| FLD-PROC-002 | Purchase Orders | Procurement | PO records |
| FLD-PROC-003 | Vendor Contracts | Procurement | Vendor agreements |
| FLD-SALES-002 | Customer Contracts | Sales | Customer agreements |
| FLD-SALES-003 | Proposals | Sales | Sales proposals |
| FLD-SALES-004 | Marketing Materials | Sales | Marketing content |
| FLD-OPS-002 | Work Orders | Operations | Work orders |
| FLD-OPS-003 | Quality Records | Operations | QC records |
| FLD-IT-002 | System Documentation | IT | IT systems |
| FLD-IT-003 | Software Licenses | IT | License records |
| FLD-PROJ-002 | 2024 Initiatives | Projects | Current projects |
| FLD-PROJ-003 | Completed Projects | Projects | Archived projects |

## Sample Documents

### HR Documents

| Code | Title | Type | Folder | Size |
|------|-------|------|--------|------|
| DOC-HR-001 | Employee Handbook 2024 | policy | Policies | 2.4 MB |
| DOC-HR-002 | Vacation Request Form | form | Policies | 156 KB |
| DOC-HR-003 | Performance Review Template | template | Policies | 89 KB |
| DOC-HR-004 | New Hire Checklist | checklist | Employee Records | 340 KB |
| DOC-HR-005 | Benefits Enrollment Guide | guide | Benefits | 1.2 MB |

### Finance Documents

| Code | Title | Type | Folder | Size |
|------|-------|------|--------|------|
| DOC-FIN-001 | Q4 2024 Financial Statement | report | Invoices | 4.5 MB |
| DOC-FIN-002 | Invoice INV-2024-001 | invoice | Invoices | 340 KB |
| DOC-FIN-003 | Tax Return 2023 | tax | Tax Documents | 5.6 MB |
| DOC-FIN-004 | Bank Reconciliation Oct | statement | Bank Statements | 780 KB |
| DOC-FIN-005 | Budget Forecast 2025 | budget | Budgets | 1.2 MB |

### Legal Documents

| Code | Title | Type | Folder | Size |
|------|-------|------|--------|------|
| DOC-LEG-001 | Service Agreement Template | contract | Contracts | 890 KB |
| DOC-LEG-002 | NDA Standard Template | contract | Contracts | 450 KB |
| DOC-LEG-003 | Annual Compliance Report 2023 | report | Compliance | 3.4 MB |

### Procurement Documents

| Code | Title | Type | Folder | Size |
|------|-------|------|--------|------|
| DOC-PROC-001 | PO-2024-001 | purchase_order | Purchase Orders | 230 KB |
| DOC-PROC-002 | Vendor Registration Form | form | Vendor Contracts | 180 KB |
| DOC-PROC-003 | Supplier Agreement Acme Corp | contract | Vendor Contracts | 1.2 MB |

### Sales Documents

| Code | Title | Type | Folder | Size |
|------|-------|------|--------|------|
| DOC-SALES-001 | Contract - BigCorp Inc | contract | Customer Contracts | 2.3 MB |
| DOC-SALES-002 | Proposal - TechStart Solutions | proposal | Proposals | 1.8 MB |
| DOC-SALES-003 | Product Brochure 2024 | marketing | Marketing | 5.6 MB |
| DOC-SALES-004 | Price List 2024 | price_list | Marketing | 340 KB |

### Operations Documents

| Code | Title | Type | Folder | Size |
|------|-------|------|--------|------|
| DOC-OPS-001 | Work Order WO-2024-001 | work_order | Work Orders | 450 KB |
| DOC-OPS-002 | Quality Control Procedure | procedure | Quality Records | 1.2 MB |
| DOC-OPS-003 | Inspection Report Q3 | report | Quality Records | 2.3 MB |

### IT Documents

| Code | Title | Type | Folder | Size |
|------|-------|------|--------|------|
| DOC-IT-001 | Network Architecture Diagram | diagram | System Docs | 890 KB |
| DOC-IT-002 | Software License Inventory | inventory | Licenses | 560 KB |
| DOC-IT-003 | IT Security Policy | policy | System Docs | 1.8 MB |

### Project Documents

| Code | Title | Type | Folder | Size |
|------|-------|------|--------|------|
| DOC-PROJ-001 | Project Charter - ERP Upgrade | charter | 2024 Initiatives | 3.4 MB |
| DOC-PROJ-002 | Status Report - ERP Upgrade | report | 2024 Initiatives | 1.2 MB |
| DOC-PROJ-003 | Lessons Learned - Warehouse Project | report | Completed | 2.3 MB |

## Sample Tags

| Tag Name | Display Name | Color |
|----------|--------------|-------|
| urgent | Urgent | Red (#EF4444) |
| review | Needs Review | Orange (#F59E0B) |
| approved | Approved | Green (#10B981) |
| confidential | Confidential | Purple (#7C3AED) |
| archived | Archived | Gray (#6B7280) |
| contract | Contract | Blue (#3B82F6) |
| report | Report | Cyan (#06B6D4) |
| template | Template | Violet (#8B5CF6) |

## Sample Categories

| Category Name | Display Name | Icon | Color |
|---------------|--------------|------|-------|
| contract | Contracts | fa-file-contract | Blue |
| invoice | Invoices | fa-file-invoice | Green |
| report | Reports | fa-file-alt | Orange |
| policy | Policies | fa-file-shield | Purple |
| form | Forms | fa-file-lines | Cyan |
| template | Templates | fa-file-code | Violet |
| procedure | Procedures | fa-file-lines | Pink |
| certificate | Certificates | fa-file-certificate | Teal |

## Sample Versions

### Financial Statement (DOC-FIN-001)
- v1: Initial draft (20 days ago)
- v2: Added executive summary (15 days ago)
- v3: Final version approved (10 days ago)

### Employee Handbook (DOC-HR-001)
- v1: Initial version (90 days ago)
- v2: Policy updates Q2 (30 days ago)

### Service Agreement (DOC-LEG-001)
- v1: Original template (120 days ago)
- v2: Legal review changes (90 days ago)
- v3: Final approved version (60 days ago)

## Sample Permissions

| Folder | User | Permission Level |
|--------|------|------------------|
| Human Resources | Admin (1) | full_control |
| Human Resources | User 2 | read |
| Human Resources | User 3 | read_write |
| Finance | Admin (1) | full_control |
| Finance | User 2 | read |
| Finance | User 3 | read_write |
| Legal | Admin (1) | full_control |
| Legal | User 2 | read |

## Sample Favorites

User 1 (Admin) has 5 favorite documents for quick access.

## Sample Activity

The sample data includes:
- Folder creation activities
- Document upload activities
- Folder access logs
- Version upload events

## Customization

To customize sample data:

1. Edit `sample_file_data.py`
2. Modify the data tuples
3. Re-run the script (after clearing existing data)

To clear existing sample data:

```sql
DELETE FROM document_favorites;
DELETE FROM folder_permissions;
DELETE FROM document_versions;
DELETE FROM documents;
DELETE FROM document_folders;
DELETE FROM document_tags;
DELETE FROM document_categories;
```

## Adding More Sample Data

Add more sample data by extending the arrays in `sample_file_data.py`:

```python
# Example: Add more documents
new_docs = [
    ('DOC-XXX-001', 'New Document', 'report', folder_id, 1,
     'Active', 'General', 'internal', now, None, None, None, 'pdf', 500000, now, now),
]
cursor.executemany("""
    INSERT INTO documents (...) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", new_docs)
```

## Performance Notes

Sample data is designed for:
- Testing folder hierarchies (8 root + 21 subfolders)
- Testing document CRUD (30+ documents)
- Testing version control (8 sample versions)
- Testing permissions (multiple users)
- Testing search and filtering

For performance testing with larger datasets, modify the script to generate data in loops.
