# HR Module - Permission Matrix
## WHDASH Enterprise HR Platform

---

## 1. Permission Overview

The HR module uses a granular permission system following the pattern:
```
hr.{resource}.{action}
```

### 1.1 Permission Categories

| Category | Resources | Description |
|----------|-----------|-------------|
| Dashboard | `hr.hr.*` | HR dashboard access |
| Employees | `hr.employees.*` | Employee CRUD operations |
| Organization | `hr.departments.*`, `hr.positions.*` | Org structure management |
| Attendance | `hr.attendance.*` | Attendance management |
| Leave | `hr.leave.*` | Leave management |
| Payroll | `hr.payroll.*` | Payroll processing |
| Overtime | `hr.overtime.*` | Overtime management |
| Rewards | `hr.bonuses.*`, `hr.deductions.*` | Compensation adjustments |
| Loans | `hr.loans.*` | Loan management |
| Training | `hr.training.*` | Training and learning |
| Documents | `hr.documents.*` | HR document management |
| Announcements | `hr.announcements.*` | Company announcements |
| Recruitment | `hr.recruitment.*` | Hiring pipeline |
| Performance | `hr.performance.*` | Performance reviews |
| Successors | `hr.successors.*` | Talent succession |
| Reports | `hr.reports.*` | Reporting and exports |
| Settings | `hr.settings.*` | System configuration |
| Onboarding | `hr.onboarding.*` | Onboarding workflows |
| Offboarding | `hr.offboarding.*` | Offboarding workflows |
| Cases | `hr.cases.*` | HR service cases |

---

## 2. Detailed Permission Matrix

### 2.1 Dashboard Permissions

| Permission | View | Edit | Delete | Approve | Export |
|------------|------|------|--------|---------|--------|
| HR Dashboard | hr.hr.view | - | - | - | hr.hr.export |
| Executive Dashboard | hr.hr.executive_view | - | - | - | hr.hr.export |

### 2.2 Employee Administration Permissions

| Permission | View | Create | Edit | Delete | Approve | Export |
|------------|------|--------|------|--------|---------|--------|
| View Employees | ✓ | - | - | - | - | - |
| Create Employee | - | ✓ | - | - | - | - |
| Edit Employee | - | - | ✓ | - | - | - |
| Delete Employee | - | - | - | ✓ | - | - |
| View Employee Profile | ✓ | - | - | - | - | - |
| Edit Employee Profile | - | - | ✓ | - | - | - |
| View Employment History | ✓ | - | - | - | - | - |
| Add Employment History | - | ✓ | - | - | - | - |
| View Contracts | ✓ | - | - | - | - | - |
| Manage Contracts | - | ✓ | ✓ | - | ✓ | - |
| View Salary Info | ✓ | - | - | - | - | - |
| Edit Salary Info | - | - | ✓ | - | - | - |

### 2.3 Organization Management Permissions

| Permission | View | Create | Edit | Delete | Approve | Export |
|------------|------|--------|------|--------|---------|--------|
| View Departments | ✓ | - | - | - | - | - |
| Create Department | - | ✓ | - | - | - | - |
| Edit Department | - | - | ✓ | - | - | - |
| Delete Department | - | - | - | ✓ | - | - |
| View Positions | ✓ | - | - | - | - | - |
| Create Position | - | ✓ | - | - | - | - |
| Edit Position | - | - | ✓ | - | - | - |
| Delete Position | - | - | - | ✓ | - | - |
| View Org Chart | ✓ | - | - | - | - | - |
| View Headcount | ✓ | - | - | - | - | ✓ |

### 2.4 Attendance & Time Permissions

| Permission | View | Create | Edit | Delete | Approve | Export |
|------------|------|--------|------|--------|---------|--------|
| View Attendance | ✓ | - | - | - | - | ✓ |
| Mark Attendance | - | ✓ | - | - | - | - |
| Edit Attendance | - | - | ✓ | - | - | - |
| Approve Attendance | - | - | - | - | ✓ | - |
| View Shifts | ✓ | - | - | - | - | - |
| Manage Shifts | - | ✓ | ✓ | ✓ | - | - |
| View Missing Punch | ✓ | - | - | - | - | - |
| Review Missing Punch | - | - | ✓ | - | ✓ | - |

### 2.5 Leave Management Permissions

| Permission | View | Create | Edit | Delete | Approve | Export |
|------------|------|--------|------|--------|---------|--------|
| View Leave Requests | ✓ | - | - | - | - | ✓ |
| Create Leave Request | - | ✓ | - | - | - | - |
| Edit Leave Request | - | - | ✓ | - | - | - |
| Cancel Leave Request | - | - | ✓ | - | - | - |
| Approve Leave | - | - | - | - | ✓ | - |
| View Leave Calendar | ✓ | - | - | - | - | - |
| Manage Leave Balances | - | ✓ | ✓ | - | - | - |
| Configure Leave Types | - | ✓ | ✓ | ✓ | - | - |

### 2.6 Payroll & Compensation Permissions

| Permission | View | Create | Edit | Delete | Approve | Export |
|------------|------|--------|------|--------|---------|--------|
| View Payroll | ✓ | - | - | - | - | ✓ |
| Process Payroll | - | - | ✓ | - | - | - |
| Approve Payroll | - | - | - | - | ✓ | - |
| Lock Payroll | - | - | ✓ | - | - | - |
| View Payroll Details | ✓ | - | - | - | - | - |
| Edit Payroll Components | - | ✓ | ✓ | ✓ | - | - |
| View Loans | ✓ | - | - | - | - | ✓ |
| Manage Loans | - | ✓ | ✓ | - | ✓ | - |
| View Bonuses | ✓ | - | - | - | - | ✓ |
| Manage Bonuses | - | ✓ | ✓ | - | ✓ | - |
| View Deductions | ✓ | - | - | - | - | ✓ |
| Manage Deductions | - | ✓ | ✓ | - | ✓ | - |

### 2.7 Recruitment Permissions

| Permission | View | Create | Edit | Delete | Approve | Export |
|------------|------|--------|------|--------|---------|--------|
| View Requisitions | ✓ | - | - | - | - | ✓ |
| Create Requisition | - | ✓ | - | - | - | - |
| Edit Requisition | - | - | ✓ | - | - | - |
| Approve Requisition | - | - | - | - | ✓ | - |
| Close Requisition | - | - | ✓ | - | - | - |
| View Candidates | ✓ | - | - | - | - | ✓ |
| Add Candidate | - | ✓ | - | - | - | - |
| Edit Candidate | - | - | ✓ | - | - | - |
| Move Candidate Stage | - | - | ✓ | - | - | - |
| Make Offer | - | - | ✓ | - | ✓ | - |
| Hire Candidate | - | - | - | - | ✓ | - |
| Reject Candidate | - | - | ✓ | - | - | - |

### 2.8 Performance Management Permissions

| Permission | View | Create | Edit | Delete | Approve | Export |
|------------|------|--------|------|--------|---------|--------|
| View Goals | ✓ | - | - | - | - | ✓ |
| Create Goal | - | ✓ | - | - | - | - |
| Edit Goal | - | - | ✓ | - | - | - |
| View Appraisals | ✓ | - | - | - | - | ✓ |
| Create Appraisal | - | ✓ | - | - | - | - |
| Complete Appraisal | - | - | ✓ | - | - | - |
| Approve Appraisal | - | - | - | - | ✓ | - |
| View Review Cycles | ✓ | - | - | - | - | - |
| Manage Review Cycles | - | ✓ | ✓ | ✓ | - | - |

### 2.9 Talent & Succession Permissions

| Permission | View | Create | Edit | Delete | Approve | Export |
|------------|------|--------|------|--------|---------|--------|
| View Talent Profiles | ✓ | - | - | - | - | ✓ |
| Edit Talent Profile | - | - | ✓ | - | - | - |
| View Hi-Po Watchlist | ✓ | - | - | - | - | ✓ |
| Add to Hi-Po | - | - | ✓ | - | - | - |
| Remove from Hi-Po | - | - | ✓ | - | - | - |
| View Succession Plans | ✓ | - | - | - | - | ✓ |
| Create Succession Plan | - | ✓ | - | - | - | - |
| Edit Succession Plan | - | - | ✓ | - | - | - |
| View Development Plans | ✓ | - | - | - | - | ✓ |
| Create Development Plan | - | ✓ | - | - | - | - |

### 2.10 Training & Learning Permissions

| Permission | View | Create | Edit | Delete | Approve | Export |
|------------|------|--------|------|--------|---------|--------|
| View Training Programs | ✓ | - | - | - | - | ✓ |
| Create Program | - | ✓ | - | - | - | - |
| Edit Program | - | - | ✓ | - | - | - |
| Delete Program | - | - | - | ✓ | - | - |
| View Sessions | ✓ | - | - | - | - | - |
| Schedule Session | - | ✓ | - | - | - | - |
| Edit Session | - | - | ✓ | - | - | - |
| Cancel Session | - | - | ✓ | - | - | - |
| Enroll Employee | - | ✓ | - | - | - | - |
| Mark Attendance | - | ✓ | ✓ | - | - | - |
| Issue Certificate | - | - | - | - | ✓ | - |
| View Certifications | ✓ | - | - | - | - | ✓ |
| Manage Mandatory Training | - | ✓ | ✓ | ✓ | - | - |

### 2.11 Employee Documents Permissions

| Permission | View | Create | Edit | Delete | Approve | Export |
|------------|------|--------|------|--------|---------|--------|
| View Documents | ✓ | - | - | - | - | ✓ |
| Upload Document | - | ✓ | - | - | - | - |
| Edit Document | - | - | ✓ | - | - | - |
| Delete Document | - | - | - | ✓ | - | - |
| Verify Document | - | - | ✓ | - | ✓ | - |
| View Expiry Alerts | ✓ | - | - | - | - | ✓ |
| Manage Document Types | - | ✓ | ✓ | ✓ | - | - |

### 2.12 Announcements Permissions

| Permission | View | Create | Edit | Delete | Approve | Export |
|------------|------|--------|------|--------|---------|--------|
| View Announcements | ✓ | - | - | - | - | - |
| Create Announcement | - | ✓ | - | - | - | - |
| Edit Announcement | - | - | ✓ | - | - | - |
| Delete Announcement | - | - | - | ✓ | - | - |
| Pin Announcement | - | - | ✓ | - | - | - |

### 2.13 Onboarding/Offboarding Permissions

| Permission | View | Create | Edit | Delete | Approve | Export |
|------------|------|--------|------|--------|---------|--------|
| View Onboarding | ✓ | - | - | - | - | ✓ |
| Create Onboarding Plan | - | ✓ | - | - | - | - |
| Edit Onboarding Plan | - | - | ✓ | - | - | - |
| View Checklist Items | ✓ | - | - | - | - | - |
| Complete Checklist Item | - | ✓ | - | - | - | - |
| View Probation Status | ✓ | - | - | - | - | - |
| Confirm Probation | - | - | - | - | ✓ | - |
| View Offboarding | ✓ | - | - | - | - | ✓ |
| Create Offboarding | - | ✓ | - | - | - | - |
| Approve Clearance | - | - | - | - | ✓ | - |
| View Exit Interview | ✓ | - | - | - | - | - |
| Conduct Exit Interview | - | ✓ | - | - | - | - |

### 2.14 Reports & Analytics Permissions

| Permission | View | Create | Edit | Delete | Export |
|------------|------|--------|------|--------|--------|
| View HR Dashboard | ✓ | - | - | - | ✓ |
| View Headcount Report | ✓ | - | - | - | ✓ |
| View Attendance Report | ✓ | - | - | - | ✓ |
| View Leave Report | ✓ | - | - | - | ✓ |
| View Payroll Report | ✓ | - | - | - | ✓ |
| View Recruitment Report | ✓ | - | - | - | ✓ |
| View Performance Report | ✓ | - | - | - | ✓ |
| View Talent Report | ✓ | - | - | - | ✓ |
| View Training Report | ✓ | - | - | - | ✓ |
| View Compliance Report | ✓ | - | - | - | ✓ |
| Create Custom Report | - | ✓ | - | - | - |
| Export Data | - | - | - | - | ✓ |

### 2.15 Settings Permissions

| Permission | View | Edit | Delete | Export |
|------------|------|------|--------|--------|
| View HR Settings | ✓ | - | - | - |
| Edit HR Settings | - | ✓ | - | - |
| View Leave Settings | ✓ | - | - | - |
| Edit Leave Settings | - | ✓ | - | - |
| View Attendance Settings | ✓ | - | - | - |
| Edit Attendance Settings | - | ✓ | - | - |
| View Payroll Settings | ✓ | - | - | - |
| Edit Payroll Settings | - | ✓ | - | - |
| View Notification Settings | ✓ | - | - | - |
| Edit Notification Settings | - | ✓ | - | - |

---

## 3. Role Definitions

### 3.1 Global Admin
```
hr.* (full access to all HR permissions)
```
Has unrestricted access to all HR functions and cannot be blocked by any permission check.

### 3.2 HR Admin
```
hr.hr.view, hr.hr.export
hr.employees.view, hr.employees.create, hr.employees.edit, hr.employees.delete
hr.departments.view, hr.departments.create, hr.departments.edit, hr.departments.delete
hr.positions.view, hr.positions.create, hr.positions.edit, hr.positions.delete
hr.attendance.view, hr.attendance.create, hr.attendance.edit
hr.leave.view, hr.leave.create, hr.leave.edit, hr.leave.approve
hr.payroll.view, hr.payroll.process
hr.overtime.view, hr.overtime.create, hr.overtime.edit, hr.overtime.approve
hr.bonuses.view, hr.bonuses.create, hr.bonuses.edit
hr.deductions.view, hr.deductions.create, hr.deductions.edit
hr.loans.view, hr.loans.create, hr.loans.edit
hr.training.view, hr.training.create, hr.training.edit
hr.documents.view, hr.documents.create, hr.documents.edit, hr.documents.approve
hr.announcements.view, hr.announcements.create, hr.announcements.edit
hr.recruitment.view, hr.recruitment.create, hr.recruitment.edit, hr.recruitment.approve
hr.performance.view, hr.performance.create, hr.performance.edit
hr.successors.view, hr.successors.create, hr.successors.edit
hr.reports.view, hr.reports.export
hr.settings.view, hr.settings.edit
hr.onboarding.view, hr.onboarding.create, hr.onboarding.edit
hr.offboarding.view, hr.offboarding.create, hr.offboarding.edit
hr.cases.view, hr.cases.create, hr.cases.edit, hr.cases.approve
```

### 3.3 HR Manager
```
hr.hr.view
hr.employees.view, hr.employees.create, hr.employees.edit
hr.departments.view
hr.positions.view
hr.attendance.view, hr.attendance.create, hr.attendance.edit, hr.attendance.approve
hr.leave.view, hr.leave.create, hr.leave.approve
hr.payroll.view
hr.overtime.view, hr.overtime.create, hr.overtime.approve
hr.training.view, hr.training.create
hr.documents.view, hr.documents.create
hr.announcements.view, hr.announcements.create
hr.recruitment.view, hr.recruitment.create, hr.recruitment.edit
hr.performance.view, hr.performance.create, hr.performance.edit
hr.successors.view
hr.reports.view, hr.reports.export
hr.onboarding.view, hr.onboarding.create
hr.offboarding.view
hr.cases.view, hr.cases.create
```

### 3.4 HR Officer
```
hr.hr.view
hr.employees.view, hr.employees.create, hr.employees.edit
hr.departments.view
hr.positions.view
hr.attendance.view, hr.attendance.create, hr.attendance.edit
hr.leave.view, hr.leave.create
hr.payroll.view
hr.overtime.view, hr.overtime.create
hr.training.view, hr.training.create
hr.documents.view, hr.documents.create
hr.announcements.view
hr.recruitment.view, hr.recruitment.create
hr.performance.view
hr.reports.view
hr.cases.view, hr.cases.create
```

### 3.5 Attendance Officer
```
hr.hr.view
hr.attendance.view, hr.attendance.create, hr.attendance.edit, hr.attendance.approve
hr.leave.view
hr.reports.view, hr.reports.export
```

### 3.6 Payroll Reviewer
```
hr.hr.view
hr.payroll.view
hr.employees.view
hr.loans.view
hr.bonuses.view
hr.deductions.view
hr.reports.view, hr.reports.export
```

### 3.7 Recruiter
```
hr.hr.view
hr.recruitment.view, hr.recruitment.create, hr.recruitment.edit, hr.recruitment.approve
hr.candidates.view, hr.candidates.create, hr.candidates.edit
hr.employees.view
hr.announcements.view
hr.reports.view
```

### 3.8 Department Manager
```
hr.hr.view
hr.employees.view (team only)
hr.attendance.view (team only), hr.attendance.create (team only)
hr.leave.view (team only), hr.leave.approve (team only)
hr.overtime.view (team only), hr.overtime.approve (team only)
hr.training.view (team only)
hr.performance.view (team only)
hr.reports.view (team only)
```

### 3.9 Employee (Self-Service)
```
hr.hr.view
hr.employees.view (self only)
hr.attendance.view (self only)
hr.leave.view (self only), hr.leave.create (self only)
hr.training.view (self only)
hr.documents.view (self only)
hr.announcements.view
hr.performance.view (self only)
```

### 3.10 Auditor
```
hr.hr.view
hr.employees.view
hr.departments.view
hr.positions.view
hr.attendance.view
hr.leave.view
hr.payroll.view
hr.overtime.view
hr.training.view
hr.documents.view
hr.recruitment.view
hr.performance.view
hr.successors.view
hr.reports.view
hr.audit_logs.view
```

---

## 4. Scope-Based Access Control

### 4.1 Team Scoping
Users with team-scoped permissions can only access data for employees who report to them in the org hierarchy.

**Implementation:**
- `reporting_to_id` in `hr_employee_employment` table defines reporting lines
- Department managers can see all employees in their department
- Managers can only approve requests from their direct reports

### 4.2 Branch/Entity Scoping
Users can be scoped to specific branches or entities.

**Implementation:**
- `company_id` and `branch_id` in `hr_employee_employment`
- Users can only see employees in their assigned branches

### 4.3 Sensitive Data Protection
Certain fields require elevated permissions:
- `bank_account_number`, `iban` - only HR Admin and Payroll Reviewer
- `salary` fields - only HR Admin and Payroll Reviewer
- `passport_number`, `visa_number` - HR Admin and above

---

## 5. Audit Trail

All permission-changed activities are logged in `hr_audit_logs`:
- Who made the change
- What was changed
- Before/after values
- Timestamp
- IP address

---

## 6. Permission Inheritance

Permissions are checked in order:
1. Global Admin bypass
2. Direct user permissions
3. Role-based permissions
4. Deny if no match found