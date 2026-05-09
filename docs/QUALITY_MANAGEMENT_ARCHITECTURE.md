# Quality Management (QA/QC) Module Architecture

## Overview

The Quality Management module in WHDASH is a comprehensive enterprise-grade quality operating platform that provides end-to-end quality control across the supply chain, manufacturing, and operations. It surpasses traditional SAP QM implementations in usability, operational clarity, and integration capabilities.

## Module Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    QUALITY MANAGEMENT MODULE                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Quality    │  │  Quality     │  │   Flow       │         │
│  │   Dashboard  │  │  Analytics   │  │   Integration│         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐   │
│  │               INSPECTION MANAGEMENT                      │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │   │
│  │  │Incoming │ │In-Process│ │ Final  │ │Re-Inspec│    │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘    │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              NCR / NON-CONFORMANCE                       │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │   │
│  │  │Contain- │ │ Root    │ │Disposi- │ │Linked   │    │   │
│  │  │ment     │ │Cause    │ │tion     │ │CAPA     │    │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘    │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              CAPA MANAGEMENT                             │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │   │
│  │  │Correct- │ │Prevent- │ │Effective│ │Action  │    │   │
│  │  │ive      │ │ive      │ │ness     │ │Tracker  │    │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘    │   │
│  └──────────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              AUDIT MANAGEMENT                            │   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐    │   │
│  │  │Programs │ │ Check-  │ │Findings │ │Follow-  │    │   │
│  │  │         │ │lists    │ │         │ │up       │    │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘    │   │
│  └──────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Supplier    │  │   SPC /      │  │   Quality   │         │
│  │  Quality     │  │   Analytics  │  │   Documents  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Holds &     │  │  Risk &      │  │  Workflow & │         │
│  │  Disposition │  │  Compliance  │  │  Approvals  │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## Data Models

### Database Tables

#### 1. Quality Inspection Tables
- `quality_inspection_types` - Master inspection categories (Incoming, In-Process, Final, etc.)
- `quality_inspection_templates` - Reusable inspection checklists
- `quality_inspection_template_lines` - Template checklist items
- `quality_inspection_plans` - Scheduled/planned inspections
- `quality_inspections` - Actual inspection records
- `quality_inspection_lines` - Line-by-line checklist results
- `quality_inspection_findings` - Defects found during inspection

#### 2. NCR Tables
- `quality_non_conformances` - NCR master records
- `quality_containment_actions` - Immediate containment actions

#### 3. CAPA Tables
- `quality_capa_categories` - CAPA classification
- `quality_capa_records` - CAPA master records
- `quality_capa_actions` - Individual CAPA action items
- `quality_effectiveness_reviews` - CAPA effectiveness verification

#### 4. Audit Tables
- `quality_audit_programs` - Annual/scheduled audit programs
- `quality_audit_plans` - Individual audit plans
- `quality_audit_checklist_templates` - Reusable audit checklists
- `quality_audit_checklists` - Completed checklists
- `quality_audit_findings` - Audit findings/non-conformities

#### 5. Supporting Tables
- `quality_defect_categories` - Defect classification
- `quality_root_cause_categories` - Root cause classification
- `quality_settings` - Quality module configuration
- `quality_approval_records` - Approval workflow records
- `quality_audit_log` - Audit trail for all quality changes

## Route Structure

### Main Routes (`/quality/*`)

```
/quality/
├── /dashboard                     - Quality Dashboard
├── /inspections                   - Inspection List
│   ├── /create                    - Create Inspection
│   ├── /view/<id>                - View Inspection
│   ├── /edit/<id>                - Edit Inspection
│   ├── /by-type/<type>           - Filter by Type
│   └── /failed                    - Failed Inspections
├── /ncr                           - NCR List
│   ├── /create                   - Create NCR
│   ├── /view/<id>                - View NCR
│   ├── /edit/<id>                - Edit NCR
│   ├── /open                     - Open NCRs
│   ├── /overdue                   - Overdue NCRs
│   └── /pending-review           - Pending Review NCRs
├── /capa                          - CAPA List
│   ├── /create                   - Create CAPA
│   ├── /create/<ncr_id>          - Create from NCR
│   ├── /view/<id>                - View CAPA
│   ├── /edit/<id>                - Edit CAPA
│   ├── /<id>/effectiveness-review - Effectiveness Review
│   ├── /open                     - Open CAPAs
│   ├── /overdue                   - Overdue CAPAs
│   └── /effectiveness-review      - Pending Effectiveness
├── /audits                        - Audit List
│   ├── /create                   - Create Audit
│   ├── /view/<id>                - View Audit
│   ├── /edit/<id>                - Edit Audit
│   ├── /<id>/add-finding         - Add Finding
│   ├── /findings                 - All Findings
│   ├── /findings/<id>            - View Finding
│   ├── /findings/<id>/edit       - Edit Finding
│   ├── /active                   - Active Audits
│   └── /scheduled                 - Scheduled Audits
├── /reports/                      - Reports
│   ├── /inspection               - Inspection Report
│   ├── /ncr                      - NCR Report
│   ├── /capa                    - CAPA Report
│   ├── /supplier-quality         - Supplier Quality Report
│   └── /audit-findings           - Audit Findings Report
├── /settings                      - Quality Settings
└── /audit-log                    - Quality Audit Log
```

## Integration Architecture

### Cross-Module Integration

#### WMS Integration
- Quality holds affect inventory state
- Inspection triggers from receipts
- Lot/batch tracking linkage
- Warehouse location awareness

#### Procurement Integration
- Supplier quality scorecards
- Incoming inspection from purchase receipts
- Supplier NCR tracking
- Supplier CAPA management

#### Manufacturing Integration
- In-process inspection from production orders
- First-pass yield tracking
- Process capability data
- Rework order linkage

#### Flow Integration
- Failed inspection alerts
- Critical NCR notifications
- Overdue CAPA notices
- Audit follow-up alerts
- Supplier quality escalations

#### Documents Integration
- Controlled quality documents
- SOPs and work instructions
- Test certificates
- Inspection evidence attachments

#### Workflow Integration
- Approval routing for dispositions
- CAPA closure approvals
- Audit finding verification
- Document approval workflows

## Permission Structure

### Quality Roles

| Role | Inspections | NCR | CAPA | Audits | Reports | Settings |
|------|-------------|-----|------|--------|---------|----------|
| Quality Admin | Full | Full | Full | Full | Full | Full |
| QA Manager | Full | Full | Full | Full | Full | View |
| QC Inspector | Execute | Create | - | - | View | - |
| NCR Coordinator | View | Full | View | View | View | - |
| CAPA Owner | View | View | Full | - | View | - |
| Audit Manager | View | View | View | Full | Full | View |
| Supplier Quality | View | View | View | View | Full | View |
| Compliance Reviewer | View | View | View | View | Full | Full |
| Operations Viewer | View | View | View | View | View | - |

## Feature Highlights

### 1. Inspection Management
- Multi-type inspections (Incoming, In-Process, Final, Warehouse, Supplier, Customer)
- Configurable checklists and acceptance criteria
- Pass/Fail/Conditional results
- Automatic NCR creation on failure
- Sample size calculations
- Re-inspection workflows
- Hold/Release decisions

### 2. NCR Management
- Full lifecycle tracking (Open → Under Review → Disposition → Closure)
- Severity and priority classification
- Containment actions
- Root cause analysis (5-Why, Fishbone)
- Linked CAPA creation
- Financial impact tracking
- Automated escalation

### 3. CAPA Management
- CAPA from NCR, Audit, Inspection, Complaint
- Corrective and Preventive action tracking
- Task assignment and due date management
- Effectiveness review workflow
- Recurrence detection
- Management approval routing

### 4. Audit Management
- Annual program planning
- Audit calendar
- Configurable checklists
- Finding classification
- Corrective action tracking
- Auditor assignment
- Opening/Closing meeting tracking

### 5. Supplier Quality
- Supplier scorecards
- Incoming quality tracking
- Supplier NCR and CAPA linkage
- Approved/Conditional/Blocked status
- Trend analysis
- Performance history

### 6. SPC & Analytics
- Control chart scaffold
- Process capability indices (Cp, Cpk)
- Defect rate trends
- Yield analysis
- Anomaly detection
- Exception thresholds

### 7. Quality Documents
- Controlled document management
- Revision history
- Approval workflows
- Effective/review dates
- Document linking to inspections/NCR/CAPA

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with WAL mode
- **Frontend**: Bootstrap 5, Font Awesome 6
- **Charts**: Chart.js integration ready
- **Icons**: Font Awesome 6
- **JavaScript**: Vanilla JS with Bootstrap 5

## Performance Considerations

- Database indexes on frequently queried columns
- WAL mode for concurrent access
- Lazy loading for large datasets
- Pagination for list views
- Caching for dashboard statistics

## Security

- RBAC permission system
- Field-level access control potential
- Full audit logging
- Session-based authentication
- CSRF protection on forms

## Extensibility

The module architecture supports future expansion:
- Additional inspection types
- Custom defect categories
- Industry-specific compliance requirements
- Integration with external quality systems
- Advanced statistical quality modules
