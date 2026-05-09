# Project Management Audit and Controls Guide

This document describes the audit events logged by the Project Management module, how to view and analyze audit logs, compliance controls, segregation of duties requirements, and how to generate audit reports.

---

## Audit Logging Overview

The Project Management module maintains a comprehensive audit trail of all significant actions. The audit system captures who did what, when, and from where.

### Audit Log Table Structure

```sql
-- Project Audit Logs Table
CREATE TABLE project_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    task_id INTEGER,
    action_type TEXT NOT NULL,
    field_changed TEXT,
    old_value TEXT,
    new_value TEXT,
    actor_user_id INTEGER,
    ip_address TEXT,
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (task_id) REFERENCES project_tasks(id) ON DELETE SET NULL,
    FOREIGN KEY (actor_user_id) REFERENCES users(id) ON DELETE SET NULL
);
```

### Audit Log Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | INTEGER | Unique audit entry identifier |
| `project_id` | INTEGER | Associated project (NULL for system events) |
| `task_id` | INTEGER | Associated task (if applicable) |
| `action_type` | TEXT | Type of action performed |
| `field_changed` | TEXT | Field that was modified |
| `old_value` | TEXT | Previous value |
| `new_value` | TEXT | New value |
| `actor_user_id` | INTEGER | User who performed the action |
| `ip_address` | TEXT | IP address of the user |
| `user_agent` | TEXT | Browser/client information |
| `created_at` | DATETIME | Timestamp of the action |

---

## Audit Event Types

### Project Lifecycle Events

| Action Type | Description | Fields Tracked |
|-------------|-------------|----------------|
| `PROJECT_CREATED` | New project created | All initial values |
| `PROJECT_UPDATED` | Project data modified | Specific changed fields |
| `PROJECT_DELETED` | Project deleted | All values before deletion |
| `PROJECT_APPROVED` | Project approved | Status, approver, approval date |
| `PROJECT_REJECTED` | Project rejected | Status, rejection reason |
| `PROJECT_ARCHIVED` | Project archived | Status, archive date |
| `PROJECT_RESTORED` | Archived project restored | Status |
| `PROJECT_STATUS_CHANGED` | Status transition | Previous and new status |
| `PROJECT_COMPLETED` | Project marked complete | Status, completion date, final progress |

### Project Field Change Events

| Action Type | Description | Fields Tracked |
|-------------|-------------|----------------|
| `PROJECT_NAME_CHANGED` | Project name updated | Name (old/new) |
| `PROJECT_MANAGER_CHANGED` | PM reassigned | Manager (old/new) |
| `PROJECT_SPONSOR_CHANGED` | Sponsor reassigned | Sponsor (old/new) |
| `PROJECT_DATES_CHANGED` | Start/end dates modified | Dates (old/new) |
| `PROJECT_BUDGET_CHANGED` | Budget modified | Budget amounts |
| `PROJECT_PRIORITY_CHANGED` | Priority changed | Priority (old/new) |
| `PROJECT_PROGRESS_CHANGED` | Progress updated | Progress % |
| `PROJECT_OWNER_CHANGED` | Owner changed | Owner |
| `PROJECT_DESCRIPTION_CHANGED` | Description modified | Description |

### Task Events

| Action Type | Description | Fields Tracked |
|-------------|-------------|----------------|
| `TASK_CREATED` | Task created | All initial values |
| `TASK_UPDATED` | Task data modified | Specific changed fields |
| `TASK_DELETED` | Task deleted | All values before deletion |
| `TASK_COMPLETED` | Task marked complete | Status, completion date |
| `TASK_ASSIGNED` | Task assignee changed | Assignee (old/new) |
| `TASK_REASSIGNED` | Task reassignment | From/to user |
| `TASK_STATUS_CHANGED` | Status transition | Status (old/new) |
| `TASK_PROGRESS_CHANGED` | Progress updated | Progress % |
| `TASK_DATES_CHANGED` | Start/end dates modified | Dates |
| `TASK_BLOCKED` | Task blocked | Blocked status, reason |
| `TASK_UNBLOCKED` | Task unblocked | Resolution |
| `TASK_COMMENT_ADDED` | Comment added | Comment content |
| `TASK_ATTACHMENT_ADDED` | File attached | File name, size |
| `TASK_DEPENDENCY_ADDED` | Dependency created | Predecessor/successor |
| `TASK_DEPENDENCY_REMOVED` | Dependency removed | Predecessor/successor |

### Milestone Events

| Action Type | Description | Fields Tracked |
|-------------|-------------|----------------|
| `MILESTONE_CREATED` | Milestone created | All initial values |
| `MILESTONE_UPDATED` | Milestone modified | Specific changed fields |
| `MILESTONE_DELETED` | Milestone deleted | All values |
| `MILESTONE_COMPLETED` | Milestone achieved | Completion date, status |
| `MILESTONE_APPROVED` | Milestone approval | Approver, approval date |
| `MILESTONE_SIGN_OFF` | Sign-off recorded | Sign-off date, signer |

### Budget and Financial Events

| Action Type | Description | Fields Tracked |
|-------------|-------------|----------------|
| `BUDGET_CREATED` | Budget item created | Budget details |
| `BUDGET_UPDATED` | Budget modified | Changed amounts |
| `BUDGET_APPROVED` | Budget approved | Approver, date |
| `BUDGET_REJECTED` | Budget rejected | Rejection reason |
| `EXPENSE_ADDED` | Expense recorded | Amount, category, description |
| `EXPENSE_APPROVED` | Expense approved | Approver, amount |
| `EXPENSE_REJECTED` | Expense rejected | Rejection reason |
| `INVOICE_ADDED` | Invoice added | Invoice details |
| `PAYMENT_PROCESSED` | Payment made | Amount, vendor |

### Risk Events

| Action Type | Description | Fields Tracked |
|-------------|-------------|----------------|
| `RISK_IDENTIFIED` | New risk logged | Risk details |
| `RISK_UPDATED` | Risk data modified | Changed fields |
| `RISK_MITIGATED` | Mitigation applied | Mitigation plan |
| `RISK_CLOSED` | Risk resolved/closed | Closure date, notes |
| `RISK_ESCALATED` | Risk escalated | Escalation level |
| `RISK_REVIEWED` | Risk reviewed | Review date, findings |

### Issue Events

| Action Type | Description | Fields Tracked |
|-------------|-------------|----------------|
| `ISSUE_LOGGED` | New issue reported | Issue details |
| `ISSUE_UPDATED` | Issue modified | Changed fields |
| `ISSUE_ASSIGNED` | Issue reassigned | Assignee changes |
| `ISSUE_RESOLVED` | Issue resolved | Resolution date, notes |
| `ISSUE_CLOSED` | Issue closed | Closure date, notes |
| `ISSUE_ESCALATED` | Issue escalated | Escalation level |
| `ISSUE_BLOCKER_SET` | Blocker flag set | Is blocker |

### Change Request Events

| Action Type | Description | Fields Tracked |
|-------------|-------------|----------------|
| `CHANGE_CREATED` | Change request submitted | Change details |
| `CHANGE_UPDATED` | Change modified | Changed fields |
| `CHANGE_APPROVED` | Change approved | Approver, decision |
| `CHANGE_REJECTED` | Change rejected | Rejection reason |
| `CHANGE_IMPLEMENTED` | Change implemented | Implementation date |
| `CHANGE_WITHDRAWN` | Change withdrawn | Withdrawal reason |

### Document Events

| Action Type | Description | Fields Tracked |
|-------------|-------------|----------------|
| `DOCUMENT_UPLOADED` | Document uploaded | File details |
| `DOCUMENT_DOWNLOADED` | Document downloaded | User, timestamp |
| `DOCUMENT_UPDATED` | Document updated | Version, changes |
| `DOCUMENT_DELETED` | Document deleted | File name |
| `DOCUMENT_APPROVED` | Document approved | Approver |
| `DOCUMENT_SHARED` | Document shared | Recipients |

### Governance Events

| Action Type | Description | Fields Tracked |
|-------------|-------------|----------------|
| `STATUS_UPDATE_ADDED` | Status update submitted | Update content |
| `CHARTER_APPROVED` | Charter approved | Approver, date |
| `GOVERNANCE_REVIEW` | Governance review conducted | Review results |
| `STEERING_COMMITTEE` | Steering committee held | Meeting notes |

### System Events

| Action Type | Description | Fields Tracked |
|-------------|-------------|----------------|
| `SETTING_UPDATED` | System setting changed | Setting key, old/new value |
| `WORKFLOW_TRIGGERED` | Workflow initiated | Workflow type, status |
| `NOTIFICATION_SENT` | Notification dispatched | Notification type, recipient |
| `EXPORT_GENERATED` | Report exported | Report type, format |
| `USER_PERMISSION_CHANGED` | User permission modified | Permission changes |

---

## Viewing Audit Logs

### Accessing Audit Logs

**Role Requirements**: Users must have `audit_logs` permission with `view` action to access audit logs.

**Navigation**: Project → Settings → Audit Logs

### Audit Log Interface

The audit log interface provides:

1. **Timeline View**: Chronological list of all audit events
2. **Filter Panel**: Filter by date range, project, action type, user
3. **Detail Panel**: Expandable details for each audit entry
4. **Export Options**: Export filtered results to CSV/PDF

### Filter Options

| Filter | Description | Example |
|--------|-------------|---------|
| Date Range | Filter by timestamp | Last 7 days, custom range |
| Project | Filter by specific project | PRJ00001 - ERP Implementation |
| Action Type | Filter by event type | PROJECT_STATUS_CHANGED |
| User | Filter by actor | All actions by specific user |
| Field | Filter by changed field | BUDGET, STATUS, MANAGER |
| IP Address | Filter by source IP | 192.168.1.100 |
| Severity | Filter by significance | High, Medium, Low |

### Audit Entry Details

Clicking on an audit entry shows:

- **Timestamp**: Exact date and time of the action
- **Actor**: User who performed the action (name, role)
- **Action Type**: Category of the action
- **Affected Record**: Project/task reference
- **Changes**: Field-level before and after values
- **Context**: IP address, user agent, session info

---

## Audit Report Generation

### Standard Audit Reports

| Report Name | Description | Refresh Rate |
|------------|-------------|--------------|
| Project Activity Report | All actions on a project | Real-time |
| User Activity Report | All actions by a specific user | Real-time |
| Field Change Report | History of specific field changes | On-demand |
| Compliance Report | SOX/regulatory compliance events | Daily |
| Security Report | Authentication and permission changes | Daily |
| Budget Audit Report | All budget modifications | Real-time |

### Generating an Audit Report

1. Navigate to Reports → Audit Reports
2. Select report type
3. Configure filters:
   - Date range (required)
   - Projects to include
   - Action types to include
   - Users to include
4. Select output format (PDF/Excel/CSV)
5. Click "Generate Report"
6. Download or schedule for recurring generation

### Scheduled Audit Reports

Configure automated audit report delivery:

1. Click "Schedule Report"
2. Set frequency (Daily/Weekly/Monthly)
3. Set delivery time and recipients
4. Choose format
5. Set retention period
6. Click "Save Schedule"

---

## Compliance Controls

### SOX Compliance Controls

The Project Management module implements the following SOX-relevant controls:

#### 1. Access Controls (ITGC A.1)

| Control | Implementation |
|---------|----------------|
| User Provisioning | Role-based permissions with approval workflow |
| Periodic Review | Quarterly access certification by managers |
| Terminated Users | Automatic access revocation on user deactivation |
| Shared Accounts | Prohibition with monitoring for exceptions |
| Privileged Access | Elevated permissions require additional approval |

#### 2. Change Management (ITGC A.2)

| Control | Implementation |
|---------|----------------|
| Change Request | Formal change request process with approval |
| Change Documentation | All changes logged with business justification |
| Change Testing | Testing evidence required for significant changes |
| Change Approval | Segregation of duties - requester cannot approve |
| Emergency Changes | Post-implementation approval within 24 hours |

#### 3. Computer Operations (ITGC A.3)

| Control | Implementation |
|---------|----------------|
| Backup | Automated backups with verifiable restoration testing |
| Recovery | Business continuity plan tested annually |
| Incident Response | Documented process with escalation procedures |
| Job Scheduling | Automated jobs with monitoring and alerting |

### Project-Specific SOX Controls

#### Budget Controls (SOX Section 302/404)

| Control | Requirement |
|---------|-------------|
| Budget Creation | Project manager creates, PMO approves |
| Budget Modification | Formal change request for variance >10% |
| Budget Approval | Finance reviewer approval for amounts >$50,000 |
| Actual vs Budget | Monthly reconciliation required |
| Unauthorized Commitments | System prevents commitment without approval |
| Period-End Cutoff | Proper period accounting with audit trail |

#### Project Status Controls

| Control | Requirement |
|---------|-------------|
| Status Changes | All status changes require logged justification |
| Progress Updates | Weekly progress required for active projects |
| Completion | Formal completion sign-off by sponsor required |
| Cancellation | Cancellation requires documented business reason |

### Segregation of Duties Matrix

| Transaction | Initiates | Authorizes | Records | Reviews |
|------------|-----------|------------|---------|---------|
| Create Project | Project Manager | PMO Manager | System | Auditor |
| Approve Budget | Project Manager | Finance | System | Auditor |
| Create Task | Project Manager | Project Manager | System | PMO |
| Complete Task | Team Member | Project Manager | System | Auditor |
| Log Issue | Team Member | Project Manager | System | PMO |
| Close Risk | Risk Owner | PMO Manager | System | Auditor |
| Change Scope | Project Manager | PMO Manager | System | Sponsor |

### Segregation of Duties Examples

**Example 1: Project Budget Approval**
```
WRONG (Segregation Violation):
  Project Manager creates budget → Project Manager approves budget
  Result: No segregation, control weakness

CORRECT:
  Project Manager creates budget
  → Finance Reviewer reviews and approves
  → PMO Manager provides final approval
  Result: Proper segregation of duties
```

**Example 2: Issue Resolution**
```
WRONG (Segregation Violation):
  Issue Reporter identifies issue → Issue Reporter resolves issue
  Result: Reporter cannot provide independent verification

CORRECT:
  Issue Reporter identifies issue
  → Different team member investigates root cause
  → Project Manager approves resolution
  → Original reporter verifies resolution
  Result: Independent verification achieved
```

**Example 3: Project Completion**
```
WRONG (Segregation Violation):
  Project Manager marks project complete → Project Manager signs off
  Result: No independent verification

CORRECT:
  Project Manager requests completion
  → Sponsor reviews deliverables
  → PMO Manager verifies metrics
  → Auditor performs final review
  Result: Multiple independent checkpoints
```

---

## Regulatory Compliance

### Data Retention Requirements

| Data Type | Retention Period | Legal Justification |
|----------|-----------------|-------------------|
| Project Records | 7 years after completion | Business records |
| Audit Logs | 5 years minimum | SOX requirement |
| Financial Transactions | 7 years | Tax/banking regulations |
| Contracts | 10 years after expiration | Legal |
| Personnel Records | 5 years post-project | Labor law |

### Privacy Considerations

| Requirement | Implementation |
|------------|----------------|
| Personal Data Minimization | Only collect necessary project data |
| Access Logging | All personal data access is logged |
| Consent | Users informed of monitoring scope |
| Right to Access | Users can request their data records |
| Right to Erasure | Anonymization after retention period |

### Industry-Specific Regulations

#### Construction/Engineering Projects

| Regulation | Requirement |
|-----------|-------------|
| AIA Documentation | Standard contract document formats |
| lien waivers | Signed waivers required for payments |
| Building Permits | Permit tracking and expiration alerts |
| Inspection Records | Third-party inspection documentation |

#### Healthcare Projects

| Regulation | Requirement |
|-----------|-------------|
| HIPAA | PHI protection in project documentation |
| FDA 21 CFR Part 11 | Electronic records for regulated systems |
| HITECH | Security breach notification procedures |

#### Financial Services Projects

| Regulation | Requirement |
|-----------|-------------|
| Dodd-Frank | Enhanced controls for financial projects |
| Basel III | Capital adequacy tracking |
| MiFID II | Transaction reporting for trading projects |

---

## Audit Report Templates

### Executive Audit Summary Template

```
PROJECT MANAGEMENT AUDIT SUMMARY
Report Period: [Date Range]
Generated: [Timestamp]
Generated By: [User]

1. OVERALL COMPLIANCE STATUS
   - Total compliance violations: [N]
   - High severity: [N]
   - Medium severity: [N]
   - Low severity: [N]

2. ACTIVITY SUMMARY
   - Total audit events: [N]
   - Project creates: [N]
   - Project updates: [N]
   - Budget modifications: [N]
   - Access changes: [N]

3. HIGH-RISK EVENTS
   [Table of high-risk events requiring attention]

4. TREND ANALYSIS
   [Comparison to previous period]

5. RECOMMENDATIONS
   [List of recommended actions]
```

### Detailed Field Change Report Template

```
FIELD CHANGE AUDIT REPORT
Field: [Field Name]
Period: [Date Range]
Project(s): [Project Filter]

DATE        USER        PROJECT     OLD VALUE     NEW VALUE     JUSTIFICATION
----------- ----------- ----------- ------------ ------------- ------------------
[Timestamp] [Username]  [Code]      [Old]        [New]         [Business Reason]

SUMMARY:
- Total changes: [N]
- Highest frequency user: [Name] ([N] changes)
- Most modified project: [Code] ([N] changes)
```

### User Activity Report Template

```
USER ACTIVITY AUDIT REPORT
User: [Name] ([Username])
Period: [Date Range]
Role: [Role]

ACTIONS SUMMARY:
- Total actions: [N]
- Project creates: [N]
- Project updates: [N]
- Task actions: [N]
- Document actions: [N]
- Other: [N]

ACCESS LOCATIONS:
[IP Address] - [Location] - [Action Count]

ANOMALIES DETECTED:
[N] unusual patterns identified

RECOMMENDATION:
[Access review recommendation]
```

---

## Audit Dashboard

### Key Metrics Tracked

| Metric | Description | Threshold |
|-------|-------------|-----------|
| Event Count | Number of audit events per period | Baseline ± 20% |
| Failed Auth | Failed login attempts | > 5 per day |
| Unauthorized Access | Access denied events | > 0 per day |
| Budget Changes | Budget modification frequency | Baseline |
| Status Changes | Status transition frequency | Baseline |
| Data Exports | Export volume | Baseline ± 50% |

### Alert Configuration

Configure alerts for:

| Alert Type | Trigger Condition | Notification |
|-----------|-------------------|--------------|
| Failed Login | > 3 failures per user per hour | Security team |
| Unauthorized Access | Access denied event | User's manager |
| Budget Anomaly | > 10% variance in 24 hours | Finance team |
| Bulk Export | > 1000 records exported | Compliance team |
| Role Change | Any permission modification | HR/Compliance |

---

## Audit Log Retention and Archival

### Retention Policy

1. **Active Period**: All audit logs retained in primary database
2. **Year 1-3**: Archived to separate database with slower access
3. **Year 3-5**: Archived to compressed storage
4. **Year 5+**: Archived to cold storage (offline)

### Archival Process

| Step | Action |
|------|--------|
| 1 | Identify logs reaching retention threshold |
| 2 | Export to archival format (JSON) |
| 3 | Compress and encrypt archive |
| 4 | Store in compliant archive location |
| 5 | Update archive catalog |
| 6 | Delete from primary database |
| 7 | Verify archive integrity |

### Archive Retrieval

To retrieve archived logs:

1. Submit retrieval request with date range and reason
2. Obtain approval from Compliance Officer
3. Extract from archive location
4. Decrypt and decompress
5. Provide access for specified duration
6. Log retrieval in access register

---

## Audit System Maintenance

### Regular Maintenance Tasks

| Task | Frequency | Owner |
|------|----------|-------|
| Log rotation | Weekly | System |
| Archive verification | Monthly | Compliance |
| Access review | Quarterly | Security |
| Report generation | Monthly | Audit |
| Alert threshold review | Quarterly | Security |
| Retention compliance check | Annually | Legal |

### Performance Optimization

| Optimization | Impact |
|--------------|--------|
| Index on action_type | 10x faster filtering |
| Index on created_at | Faster date range queries |
| Index on project_id | Faster project-level queries |
| Partition by month | Improved maintenance |
| Archive old partitions | Reduced storage |

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|------|-------|----------|
| Missing audit entries | Transaction rollback | Verify atomic operations |
| Duplicate entries | Retry logic | Deduplicate in reports |
| Slow query performance | Missing index | Add missing indexes |
| Large log volume | Excessive logging | Adjust logging level |
| Archive corruption | Storage failure | Restore from backup |

### Audit Log Verification

To verify audit log integrity:

```sql
-- Check for gaps in audit sequence
SELECT id, created_at,
       id - LAG(id) OVER (ORDER BY created_at) as gap
FROM project_audit_logs
WHERE created_at > datetime('now', '-30 days');

-- Verify no deleted records have audit trail
SELECT * FROM project_audit_logs
WHERE action_type LIKE '%DELETED%'
AND project_id NOT IN (SELECT id FROM projects);

-- Check for orphaned entries
SELECT * FROM project_audit_logs
WHERE project_id IS NOT NULL
AND project_id NOT IN (SELECT id FROM projects);
```

---

*Document Version: 1.0*
*Last Updated: April 2026*
*Module: Project Management*
