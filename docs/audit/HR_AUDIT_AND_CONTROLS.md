# HR Module - Audit and Controls Guide
## WHDASH Enterprise HR Platform

---

## 1. Overview

The HR module implements comprehensive audit trails and controls to ensure compliance, traceability, and security of all HR-related data and actions.

---

## 2. Audit Logging

### 2.1 Audit Log Table

```sql
CREATE TABLE hr_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    entity_id INTEGER,
    action TEXT NOT NULL,
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,
    user_id INTEGER,
    ip_address TEXT,
    user_agent TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 Logged Actions

| Entity Type | Actions Logged |
|-------------|----------------|
| `employee` | Create, Update, Delete, Status Change |
| `employment` | Create, Update, Transfer, Promote |
| `leave_request` | Create, Update, Approve, Reject, Cancel |
| `attendance` | Create, Update, Approve |
| `payroll` | Create, Update, Approve, Lock |
| `overtime` | Create, Update, Approve, Reject |
| `document` | Upload, Verify, Expiry Update |
| `announcement` | Create, Update, Delete |
| `candidate` | Create, Stage Change, Offer, Hire, Reject |
| `performance_review` | Create, Submit, Acknowledge |

### 2.3 Log Entry Contents

Each audit log entry captures:
- **Entity Type**: The HR entity being modified
- **Entity ID**: The specific record ID
- **Action**: Create, Update, Delete, Approve, etc.
- **Field Name**: The specific field changed (for updates)
- **Old Value**: Previous value (for updates)
- **New Value**: New value (for updates)
- **User ID**: Who made the change
- **IP Address**: Source IP of the change
- **User Agent**: Browser/client info
- **Timestamp**: When the change occurred

### 2.4 API for Audit Logging

```python
from hr_models import log_hr_audit

# Log a field change
log_hr_audit(
    entity_type='employee',
    entity_id=123,
    action='Update',
    field_name='mobile',
    old_value='0501234567',
    new_value='0509876543',
    user_id=session['user_id'],
    ip_address=request.remote_addr,
    user_agent=request.headers.get('User-Agent')
)

# Log a status change
log_hr_audit(
    entity_type='leave_request',
    entity_id=456,
    action='Approve',
    user_id=session['user_id'],
    ip_address=request.remote_addr
)
```

---

## 3. Employee Lifecycle Audit Trail

### 3.1 Employment History Table

```sql
CREATE TABLE hr_employee_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    history_type TEXT NOT NULL,
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,
    effective_from DATE,
    effective_to DATE,
    reason TEXT,
    created_by_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 3.2 Tracked Lifecycle Events

| History Type | Description |
|--------------|-------------|
| `hire` | New employee hire |
| `promotion` | Position/grade change |
| `transfer` | Department/branch change |
| `salary_change` | Compensation update |
| `status_change` | Active/Inactive/On Leave changes |
| `contract_renewal` | Contract extension |
| `probation_confirmation` | Probation passed |
| `termination` | Employment ended |
| `contact_update` | Personal info change |
| `emergency_contact_update` | Emergency contact change |

### 3.3 Employment History Example

```
Employee: Ahmed Al-Rashid (EMP2024001)

| Date       | Type            | Field      | Old Value        | New Value       |
|------------|-----------------|------------|------------------|-----------------|
| 2020-01-15 | hire            | -          | -                | Joined as CEO   |
| 2020-01-15 | salary_change   | basic      | -                | 75,000 AED      |
| 2021-01-01 | salary_change   | basic      | 75,000           | 80,000 AED      |
| 2022-06-01 | promotion       | position   | CEO              | CEO + Chairman  |
| 2022-06-01 | salary_change   | basic      | 80,000           | 90,000 AED      |
```

---

## 4. Approval Workflow Controls

### 4.1 Approval Table Structure

```sql
CREATE TABLE hr_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    approval_type TEXT NOT NULL,
    reference_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    approver_id INTEGER NOT NULL,
    sequence INTEGER DEFAULT 1,
    status TEXT DEFAULT 'Pending',
    remarks TEXT,
    actioned_by_id INTEGER,
    actioned_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 4.2 Approval Types

| Type | Description | Required Approvers |
|------|-------------|-------------------|
| `leave` | Leave request approval | Direct Manager → HR |
| `overtime` | Overtime request approval | Direct Manager |
| `attendance` | Attendance correction approval | HR Officer |
| `payroll` | Payroll period approval | HR Director → Finance |
| `requisition` | Job requisition approval | Department Head → HR |
| `onboarding` | Onboarding plan approval | HR Manager |
| `offboarding` | Offboarding clearance | HR + IT + Finance |
| `document_verification` | Document verification | HR Officer |
| `salary_change` | Salary adjustment approval | HR Director → Finance |

### 4.3 Approval Status Flow

```
Pending → Approved → Executed
       ↘ Rejected → Cancelled
```

### 4.4 Approval Rules Engine

```python
# Example approval rules
APPROVAL_RULES = {
    'leave': {
        'threshold_days': 5,  # >5 days requires 2-level approval
        'approvers': ['direct_manager', 'hr_manager'],
    },
    'overtime': {
        'threshold_hours': 8,  # >8 hours/month requires approval
        'approvers': ['direct_manager'],
    },
    'payroll': {
        'threshold_amount': 50000,  # >50k adjustment requires escalation
        'approvers': ['hr_director', 'finance_director'],
    }
}
```

---

## 5. Document Compliance Controls

### 5.1 Document Expiry Tracking

Documents tracked for expiry:
- Passport
- Emirates ID
- Visa
- Labour Card
- Medical Insurance
- Driving License
- Trade License
- Insurance Certificates

### 5.2 Expiry Alert Schedule

| Timeframe | Alert Level | Action |
|-----------|-------------|--------|
| 90 days | Info | Document approaching expiry |
| 60 days | Warning | Expiry in 2 months |
| 30 days | Alert | Expiry in 1 month - action needed |
| 14 days | Critical | Expiry in 2 weeks |
| 7 days | Urgent | Expiry in 1 week |
| Expired | Overdue | Document has expired |

### 5.3 Compliance Dashboard Metrics

- Documents expiring in 30 days
- Expired documents count
- Pending verification count
- Compliance rate by document type
- Compliance rate by employee

---

## 6. Attendance Controls

### 6.1 Shift Configuration Controls

- Grace period per shift type
- Maximum late minutes before penalty
- Early leave threshold
- Overtime eligibility rules

### 6.2 Missing Punch Workflow

```
1. Employee notices missing punch
2. Submits missing punch request
3. Manager reviews and approves/rejects
4. HR Officer verifies and updates attendance
5. Audit log captures the correction
```

### 6.3 Overtime Controls

- Daily OT limit (typically 4 hours max)
- Weekly OT limit (typically 20 hours max)
- Monthly OT cap (typically 40 hours max)
- Weekend/Holiday OT multiplier configuration
- OT approval required before work starts (where possible)

---

## 7. Leave Controls

### 7.1 Leave Balance Rules

- Cannot request leave exceeding available balance
- Cannot request leave for past dates (with exceptions)
- Cannot have overlapping leave requests
- Leave during probation restricted (0 days by default)

### 7.2 Team Conflict Detection

When a leave request is submitted:
1. System checks team members on same dates
2. If >50% of team on leave → Warning
3. Manager must acknowledge warning to approve

### 7.3 Carry Forward Rules

- Annual leave can carry forward up to 5 days
- Carried forward days expire on March 31st each year
- Sick leave does not carry forward
- Unused emergency leave does not carry forward

---

## 8. Payroll Controls

### 8.1 Payroll Period States

| Status | Description | Permitted Actions |
|--------|-------------|-------------------|
| `Draft` | Period created, not processed | Edit employees |
| `Processing` | Payroll being calculated | Add adjustments |
| `Review` | Calculated, pending approval | View, add corrections |
| `Approved` | Approved by HR Director | Lock period |
| `Locked` | Payroll finalized | View only, create adjustment period |
| `Paid` | Bank transfers initiated | View only |

### 8.2 Payroll Validation Rules

- Total earnings >= Total deductions (net should be positive)
- All employees must have basic salary > 0
- Loan deductions must not exceed available balance
- Overtime must be approved before inclusion
- Leave without pay must be deducted

### 8.3 Lock Protection

Once a payroll period is locked:
- Cannot add new employees
- Cannot modify basic salary
- Can only add post-lock adjustments in next period
- Audit trail captures all attempted unauthorized changes

---

## 9. Data Access Controls

### 9.1 Field-Level Security

Sensitive fields require elevated permissions:

| Field | Required Permission |
|-------|---------------------|
| `bank_account_number` | `hr.payroll.approve` or `hr.employees.edit` (HR Admin only) |
| `iban` | `hr.payroll.approve` |
| `salary` fields | `hr.payroll.view` |
| `passport_number` | `hr.documents.approve` |
| `visa_number` | `hr.documents.approve` |

### 9.2 Row-Level Security

Users only see data for:
- Their own employee record (self-service)
- Employees in their department (managers)
- All employees (HR Admin/Auditor)

### 9.3 API-Level Controls

All HR endpoints decorated with:
- `@hr_login_required` - Authentication check
- `@hr_permission_required(action)` - RBAC check

---

## 10. Audit Report Types

### 10.1 Employee Activity Report

Lists all changes to employee records:
- Who changed what
- When changed
- Before/after values
- IP address of change

### 10.2 Approval History Report

Complete approval workflow history:
- All pending approvals
- All completed approvals
- Rejection reasons
- Turnaround time (SLA compliance)

### 10.3 Compliance Status Report

Document compliance overview:
- Expiring documents by category
- Expired documents requiring action
- Compliance rate trends
- Employee compliance summary

### 10.4 Payroll Audit Report

Payroll changes after locking:
- All post-lock adjustments
- Who made adjustments
- Approval for adjustments
- Net impact on payroll

---

## 11. Retention Policies

### 11.1 Data Retention Periods

| Data Type | Retention Period | Reason |
|-----------|-----------------|--------|
| Employee Records | 7 years after termination | Legal compliance |
| Payroll Records | 7 years | Tax compliance |
| Attendance Records | 5 years | Labor law |
| Leave Records | 5 years | Labor law |
| Performance Reviews | 7 years | Legal compliance |
| Training Records | 5 years | Certification requirements |
| Audit Logs | 7 years | Audit requirements |
| HR Documents | 10 years | Legal compliance |

---

## 12. Segregation of Duties

### 12.1 Critical Duty Separations

| Duty | Cannot be combined with |
|------|------------------------|
| Payroll Processor | Payroll Approver |
| Leave Approver | Leave Processor |
| Document Uploader | Document Verifier |
| Employee Creator | Employee Terminator |
| Salary Editor | Payroll Lock Authority |

### 12.2 Review Requirements

- Payroll must be reviewed by someone other than the processor
- Leave approvals should be by the employee's manager, not HR officer
- Document verification should be by someone other than uploader

---

## 13. Real-Time Alerts

### 13.1 Flow Integration Alerts

Alerts sent to Flow for:
- Leave requests (to approver)
- Leave approvals/rejections (to employee)
- Document expiry warnings (to HR admin)
- Payroll processing complete (to HR director)
- Recruitment stage changes (to recruiter)
- Performance review reminders (to manager)
- Probation reviews due (to HR)

### 13.2 Alert Priority Levels

| Priority | Use Case | Channel |
|----------|----------|---------|
| Urgent | Document expired | Flow + Email |
| High | Probation ending | Flow |
| Normal | Leave request | Flow |
| Low | Announcement | Flow |

---

## 14. Controls Self-Assessment

### 14.1 Monthly Control Checklist

- [ ] Review pending approvals (SLA compliance)
- [ ] Check document expiry report
- [ ] Verify payroll period status
- [ ] Confirm audit log integrity
- [ ] Review exception reports
- [ ] Approve/reject pending overtime
- [ ] Update HR settings if needed

### 14.2 Quarterly Control Review

- [ ] Review access rights (remove unnecessary)
- [ ] Audit role assignments
- [ ] Check segregation of duties compliance
- [ ] Review and update approval thresholds
- [ ] Verify backup and recovery procedures
- [ ] Conduct mock data breach drill