# Quality Management Audit and Controls Guide

## Overview

The Quality Management module includes comprehensive audit trails, controls, and compliance mechanisms to ensure regulatory compliance, traceability, and operational integrity.

## Audit Trail Architecture

### What is Audited

The Quality module maintains detailed audit trails for all critical operations:

| Category | Audited Events |
|----------|---------------|
| **Inspections** | Create, Update, Delete, Pass, Fail, Hold, Release, Re-inspect, Disposition |
| **NCRs** | Create, Update, Status Change, Root Cause Entry, Disposition, Closure, Cancel |
| **CAPAs** | Create, Update, Action Added, Action Completed, Effectiveness Review, Closure |
| **Audits** | Plan Create, Schedule, Execute, Findings Added, Follow-up, Closure |
| **Quality Holds** | Hold Created, Review, Release Decision, Disposition Applied |
| **Suppliers** | Status Change, Scorecard Recalculation, Block/Unblock |
| **Settings** | Configuration Changes, User Permission Changes |
| **Documents** | Upload, Version Change, Approval, Expiry |

### Audit Log Fields

Each audit entry captures:

```json
{
  "audit_id": "unique identifier",
  "entity_type": "INSPECTION|NCR|CAPA|AUDIT|HOLD|SUPPLIER|SETTING",
  "entity_id": "reference ID (e.g., NCR-2026-0001)",
  "action": "CREATE|UPDATE|DELETE|STATUS_CHANGE|DISPOSITION|CLOSE",
  "field_changed": "specific field name if applicable",
  "old_value": "previous value",
  "new_value": "new value",
  "user_id": "user performing action",
  "user_name": "display name",
  "user_role": "role at time of action",
  "timestamp": "ISO 8601 datetime",
  "ip_address": "client IP",
  "session_id": "session identifier",
  "additional_context": "JSON for extra info (branch, entity, etc.)"
}
```

## Access Control Mechanisms

### Role-Based Access Control (RBAC)

Quality module permissions are defined in `permissions.py` with the following structure:

```
quality (resource)
├── dashboard
│   ├── view (own branch)
│   ├── view_all (all branches)
│   └── export
├── inspection_plans
│   ├── view
│   ├── create
│   ├── edit
│   ├── delete
│   └── approve
├── inspections
│   ├── view
│   ├── create
│   ├── edit
│   ├── delete
│   ├── approve
│   └── disposition
├── ncr
│   ├── view
│   ├── create
│   ├── edit
│   ├── delete
│   ├── approve
│   ├── close
│   └── cancel
├── capa
│   ├── view
│   ├── create
│   ├── edit
│   ├── delete
│   ├── approve
│   ├── close
│   └── effectiveness_review
├── audits
│   ├── view
│   ├── create
│   ├── edit
│   ├── execute
│   ├── findings_add
│   ├── findings_close
│   └── reports
├── supplier_quality
│   ├── view
│   ├── approve
│   └── block_supplier
├── quality_holds
│   ├── view
│   ├── create
│   ├── release
│   └── dispose
├── defects
│   ├── view
│   ├── create
│   └── analyze
├── spc
│   ├── view
│   └── configure
├── quality_documents
│   ├── view
│   ├── create
│   ├── edit
│   ├── approve
│   └── obsolete
├── compliance
│   ├── view
│   ├── manage
│   └── approve_exceptions
├── approvals
│   ├── view_pending
│   ├── approve
│   └── reject
├── reports
│   ├── view_own
│   ├── view_branch
│   ├── view_all
│   └── export
├── settings
│   ├── view
│   └── edit
└── audit_log
    ├── view_own
    └── view_all
```

### Pre-Defined Quality Roles

| Role | Primary Permissions |
|------|-------------------|
| **Quality Admin** | Full access to all quality functions across all branches |
| **QA Manager** | Full quality management, approval authority, settings |
| **QC Inspector** | Inspections, NCR creation, holds, defect recording |
| **NCR Coordinator** | NCR management, root cause, disposition |
| **CAPA Owner** | CAPA creation, tracking, effectiveness review |
| **Audit Manager** | Audit program, scheduling, findings management |
| **Supplier Quality Reviewer** | Supplier scorecards, audits, quality agreements |
| **Compliance Reviewer** | Compliance obligations, risk management |
| **Operations Viewer** | Read-only access to quality dashboards and reports |
| **Executive Viewer** | Executive dashboards, aggregate reports |

## Compliance Controls

### Separation of Duties

| Function | Incompatible With |
|----------|------------------|
| NCR Close | NCR Create, NCR Edit |
| CAPA Close | CAPA Create, CAPA Edit |
| Audit Finding Close | Audit Finding Create |
| Hold Release | Hold Create |
| Supplier Block | Supplier Approval |
| Settings Edit | Audit Log View (own changes) |

### Approval Matrix

| Action | Required Approver | Escalation |
|--------|------------------|------------|
| NCR Closure | NCR Coordinator or QA Manager | Auto-escalate if > 7 days |
| CAPA Closure | QA Manager | Auto-escalate if effectiveness not verified |
| Hold Release | QC Inspector + QA Manager | No release without QA Manager |
| Supplier Block | QA Manager | Immediate notification to Procurement |
| Audit Finding Closure | Audit Manager | Lead Auditor verification |
| Settings Change | Quality Admin | Audit log mandatory |

### Critical Control Points

1. **Inspection Result Verification**
   - Two-inspector verification for critical characteristics
   - Mandatory re-inspection after failed inspection
   - Automatic hold on failed lots

2. **NCR Containment**
   - Immediate notification to affected parties
   - Quarantine of suspected materials
   - Customer notification within 24 hours for critical issues

3. **CAPA Effectiveness**
   - Mandatory effectiveness review before closure
   - Verification of corrective action implementation
   - Trend analysis for recurrence detection

4. **Audit Integrity**
   - Independent auditors (auditor cannot audit own department)
   - Documented evidence requirements
   - Management review of findings

## Data Integrity Controls

### Validation Rules

| Entity | Validation |
|--------|------------|
| Inspection | Sample size ≤ quantity received, inspector must be qualified |
| NCR | Severity must match defect category rules, quantity ≤ shipped |
| CAPA | At least one corrective action required before closure |
| Audit Finding | Severity requires evidence, owner must be assigned |
| Hold Release | Requires documented justification |

### Referential Integrity

- Inspections link to: Suppliers, Items, Purchase Orders, Work Orders, Lots
- NCRs link to: Inspections, Suppliers, Items, Customers, Production Orders
- CAPAs link to: NCRs, Audit Findings, Inspections, Complaints
- Audit Findings link to: Audit Plans, NCRs, CAPAs

### Data Retention

| Record Type | Retention Period |
|-------------|-----------------|
| Inspection Records | 10 years (or product lifecycle + 2 years) |
| NCR Records | 10 years |
| CAPA Records | 10 years |
| Audit Reports | 10 years |
| Controlled Documents | Document lifecycle + 5 years |
| Calibration Records | 10 years |
| Audit Logs | 7 years |

## Workflow Controls

### SLA Policies

| Process | Target Time | Escalation Time |
|---------|-------------|-----------------|
| Inspection Completion | 24 hours from receipt | 48 hours |
| NCR Initial Response | 24 hours | 48 hours |
| NCR Disposition | 5 days | 7 days |
| CAPA Root Cause | 10 days | 14 days |
| CAPA Closure | 30 days | 45 days |
| Audit Finding Closure | 30 days | 45 days |
| Hold Release Decision | 3 days | 5 days |

### Escalation Rules

1. **Automatic Escalation**
   - Overdue items escalate to manager after SLA breach
   - Critical severity items escalate immediately
   - Repeated failures trigger management review

2. **Notification Triggers**
   - NCR created → Quality Manager, NCR Coordinator
   - NCR overdue → Quality Manager, Department Manager
   - CAPA overdue → QA Manager
   - Critical audit finding → Audit Manager, Executive
   - Supplier blocked → Procurement, Quality Director

### Delegation

- Users may delegate approvals during absence
- Delegation must be pre-approved by manager
- Delegation log is audited
- Maximum delegation period: 30 days

## Security Controls

### Authentication

- All quality module access requires authentication
- Session timeout: 30 minutes of inactivity
- Concurrent session limit: 3 per user

### Authorization

- Pre-defined roles with explicit permissions
- Branch-level access restrictions where applicable
- Supplier scope restrictions for quality reviewers

### Audit Logging

All quality-related actions are logged with:
- User identification
- Timestamp (server time, UTC)
- Action type and details
- Before/after values for changes
- Source IP address
- Session information

### Sensitive Data Handling

| Data Type | Protection |
|-----------|------------|
| Customer complaint details | Restricted access |
| Supplier financial info | Restricted access |
| Internal audit findings pre-disclosure | Restricted access |
| Regulatory submission data | Encrypted storage |

## Compliance Monitoring

### Key Metrics Monitored

| Metric | Threshold | Alert |
|--------|-----------|-------|
| NCR Open > 30 days | > 5% of total | Warning |
| CAPA Overdue | > 0 | Immediate |
| Inspection Pass Rate | < 90% | Warning |
| Supplier Defect Rate | > 5% | Warning |
| Audit Finding Recurrence | > 2 same issue | Critical |
| Hold Age > 30 days | > 2 holds | Warning |

### Periodic Reviews

| Review | Frequency | Owner |
|--------|-----------|-------|
| NCR Trend Analysis | Monthly | QA Manager |
| CAPA Effectiveness | Monthly | QA Manager |
| Supplier Quality Scorecard | Quarterly | Supplier Quality |
| Audit Program Effectiveness | Semi-Annual | Audit Manager |
| Compliance Obligation Review | Annual | Compliance |
| Quality System Management Review | Annual | Quality Director |

## Control Effectiveness Monitoring

### Key Performance Indicators

```
Quality Index = (NCR Resolution Rate × 0.25) +
                (CAPA Effectiveness Rate × 0.25) +
                (Inspection Pass Rate × 0.20) +
                (Audit Finding Closure Rate × 0.15) +
                (Supplier Quality Score × 0.15)

Target: Quality Index ≥ 85
```

### Control Testing

| Control | Test Frequency | Sample Size |
|---------|---------------|-------------|
| Inspection Result Accuracy | Quarterly | 25 records |
| NCR Disposition Appropriateness | Quarterly | 20 records |
| CAPA Closure Validity | Quarterly | 15 records |
| Audit Finding Documentation | Semi-Annual | 10 records |
| Hold Release Justification | Quarterly | 20 decisions |

## Exception Handling

### Exception Categories

1. **Minor Deviation**
   - Documented but not escalated
   - Corrective action within normal cycle

2. **Significant Deviation**
   - Escalated to manager
   - Corrective action with extended timeline
   - Follow-up verification required

3. **Critical Deviation**
   - Immediate escalation to director
   - Root cause analysis required
   - Management review before disposition
   - Enhanced monitoring post-resolution

### Exception Report

All deviations are documented with:
- Description of deviation
- Reason for exception
- Impact assessment
- Corrective action taken
- Preventive action taken
- Evidence of resolution
- Approvals obtained

## Regulatory Compliance Scaffold

### Supported Standards

| Standard | Applicable Controls |
|----------|-------------------|
| ISO 9001:2015 | QMS requirements, audit, continual improvement |
| FDA 21 CFR Part 820 | Medical device quality system (if applicable) |
| IATF 16949 | Automotive QMS (if applicable) |
| Industry-specific | Configurable based on requirements |

### Compliance Mapping

Controls are mapped to regulatory requirements:
- Each control has documented regulatory reference
- Evidence of control operation is maintained
- Control effectiveness is periodically reviewed

## Audit Log Query Interface

The quality audit log is accessible via:

1. **Web Interface** (`/quality/audit_log`)
   - Filterable by entity type, date range, user, action
   - Export to Excel/CSV
   - Detail view with before/after comparison

2. **API Access**
   - RESTful endpoints for integration
   - Pagination and filtering
   - JSON format

3. **Report Integration**
   - Audit trail in all quality reports
   - Change history in entity detail views
   - Compliance reports include relevant audit entries

## Control Documentation

| Document | Location | Owner |
|----------|----------|-------|
| Quality Manual | Quality Documents | Quality Director |
| Inspection Procedures | Quality Documents | QA Manager |
| NCR Procedure | Quality Documents | QA Manager |
| CAPA Procedure | Quality Documents | QA Manager |
| Audit Protocol | Quality Documents | Audit Manager |
| Calibration Records | Quality Documents | QC Supervisor |
| Supplier Quality Agreements | Quality Documents | Supplier Quality |

## Continuous Improvement

### Control Review Cycle

1. **Monthly**
   - KPI trend analysis
   - Exception report review
   - Open item aging review

2. **Quarterly**
   - Control effectiveness assessment
   - User feedback collection
   - Procedure update assessment

3. **Annually**
   - Management review
   - Control documentation update
   - Training effectiveness verification
   - Regulatory compliance review