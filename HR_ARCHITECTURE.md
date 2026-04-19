# Human Resources (HR) Module - Architecture Guide
## WHDASH Enterprise HR Platform

---

## 1. Module Vision & Design Philosophy

The HR module is designed as an **enterprise-grade Human Resources Operating Platform** that integrates deeply with the entire WHDASH ecosystem. It is built to surpass SAP SuccessFactors in usability, operational clarity, HR visibility, and workflow practicality.

### Design Principles
- **Employee-Lifecycle Driven**: From recruitment to offboarding, every HR event is tracked
- **Compliance-Aware**: Document expiry, visa tracking, audit trails built-in
- **Manager-Friendly**: Department managers can see their team, approve requests, view reports
- **Employee-Self-Service**: Employees can view their own data, request leave, update info
- **Audit-Safe**: Every change is logged with before/after values
- **Branch/Entity Aware**: Supports multi-entity, multi-branch organizations
- **Multilingual**: Full support for 8 languages (EN, AR, FA, RU, HI, ES, ZH, DE)
- **RTL-Ready**: Full RTL support for Arabic and Persian interfaces

---

## 2. Database Architecture

### 2.1 Core HR Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `hr_departments` | Organizational structure | id, name, parent_id, code, head_id, cost_center, budget |
| `hr_positions` | Job titles and positions | id, title, department_id, salary_band_min/max, grade, is_critical |
| `hr_employees` | Employee master data | id, employee_code, personal info, status, hire_date, termination_date |
| `hr_employee_employment` | Employment details per employee | employee_id, department_id, position_id, shift_id, reporting_to_id, contract_type |
| `hr_shifts` | Work shift templates | id, name, code, start_time, end_time, grace_minutes, working_hours |
| `hr_attendance_records` | Daily attendance data | employee_id, date, check_in/out, work_hours, late_minutes, status |
| `hr_leave_types` | Types of leave | id, name, code, default_days, is_paid, requires_approval, can_carry_forward |
| `hr_leave_requests` | Leave request records | employee_id, leave_type_id, start_date, end_date, status, approved_by_id |
| `hr_leave_balances` | Employee leave balances | employee_id, leave_type_id, year, total_days, used_days, pending_days |
| `hr_payroll_periods` | Monthly payroll periods | id, name, month, year, status, total_employees, totals |
| `hr_payroll_records` | Per employee payroll | period_id, employee_id, basic_salary, allowances, deductions, net |
| `hr_payroll_components` | Salary component definitions | id, name, code, component_type (Earning/Deduction/Bonus), is_taxable |
| `hr_employee_salary` | Employee salary details | employee_id, component_id, amount, effective_from |
| `hr_overtime_requests` | Overtime requests | employee_id, date, hours, status, rate_multiplier, calculated_amount |
| `hr_bonus_records` | Bonuses and rewards | employee_id, bonus_type, amount, effective_month/year, status |
| `hr_deduction_records` | Deductions and penalties | employee_id, deduction_type, amount, is_recurring |
| `hr_loans` | Employee loans/advances | employee_id, principal_amount, tenure_months, monthly_installment, status |
| `hr_loan_installments` | Loan installment schedule | loan_id, due_date, installment_amount, status, included_in_payroll_id |
| `hr_training_programs` | Training program definitions | id, title, category, training_type, provider, duration_hours, is_mandatory |
| `hr_training_sessions` | Scheduled training sessions | program_id, trainer_name, location, start_date, end_date, status |
| `hr_training_enrollments` | Employee training enrollments | session_id, employee_id, enrollment_date, status, attendance_status, score |
| `hr_employee_documents` | Employee document management | employee_id, document_type, document_name, file_path, expiry_date, is_verified |
| `hr_announcements` | HR announcements/notices | id, title, content, announcement_type, priority, is_active |
| `hr_candidates` | Recruitment candidates | id, requisition_id, first_name, last_name, email, current_stage, status |
| `hr_job_requisitions` | Job requisitions/vacancies | id, title, department_id, vacancy_count, status, salary_min/max |
| `hr_approvals` | Approval workflow records | approval_type, reference_id, employee_id, approver_id, status |
| `hr_performance_reviews` | Performance review records | employee_id, review_period, reviewer_id, overall_score, status |
| `hr_successors` | Successor/deputy planning | employee_id, successor_id, deputy_id, readiness_level, status |
| `hr_tasks` | Employee tasks | employee_id, task_title, due_date, status, assigned_by_id |
| `hr_audit_logs` | Audit trail for HR changes | entity_type, entity_id, action, field_name, old_value, new_value, user_id |
| `hr_notification_templates` | Notification templates | template_key, template_name, subject, body, is_active |
| `hr_employee_history` | Employment history | employee_id, history_type, field_name, old_value, new_value, effective_from |
| `hr_settings` | Configurable HR settings | setting_key, setting_value, setting_type, category |

### 2.2 Entity Relationships

```
hr_departments (1) ──────< hr_positions
      │                        │
      │                        │
      └────────────────────────┤
                               │
hr_employees (1) ──────── hr_employee_employment >────── (1) hr_departments
      │                                                      │
      │                                                      │
      ├──< hr_attendance_records                         hr_positions
      ├──< hr_leave_requests                              │
      ├──< hr_leave_balances                               │
      ├──< hr_payroll_records                             
      ├──< hr_overtime_requests                     
      ├──< hr_bonus_records                        
      ├──< hr_deduction_records                    
      ├──< hr_loans >──────< hr_loan_installments        
      ├──< hr_training_enrollments >────── (1) hr_training_sessions >──── (1) hr_training_programs
      ├──< hr_employee_documents                   
      ├──< hr_candidates                           
      ├──< hr_performance_reviews                  
      ├──< hr_successors                           
      ├──< hr_tasks                                
      └──< hr_employee_history
```

---

## 3. Module Structure

### 3.1 HR Menu / Navigation

```
HR (Human Resources)
├─ HR Dashboard               → /hr/dashboard
├─ Employee Administration
│  ├─ Employee List          → /hr/employees
│  ├─ Add Employee           → /hr/employees/new
│  ├─ Employee Profile       → /hr/employees/view/<id>
│  ├─ Employee Directory     → /hr/employees/directory
│  └─ Employment History      → /hr/employees/history/<id>
├─ Organization Management
│  ├─ Departments             → /hr/departments
│  ├─ Positions               → /hr/positions
│  ├─ Org Chart              → /hr/org-chart
│  └─ Headcount Report       → /hr/reports/headcount
├─ Attendance & Time
│  ├─ Attendance Records      → /hr/attendance
│  ├─ Shift Schedules        → /hr/shifts
│  ├─ Overtime               → /hr/overtime
│  ├─ Missing Punch Review   → /hr/attendance/missing-punch
│  └─ Attendance Reports     → /hr/reports/attendance
├─ Leave Management
│  ├─ Leave Requests         → /hr/leave
│  ├─ Leave Calendar         → /hr/leave/calendar
│  ├─ Leave Balances         → /hr/leave/balances
│  ├─ Leave Approvals        → /hr/leave/approvals
│  └─ Leave Reports          → /hr/reports/leave
├─ Payroll & Compensation
│  ├─ Payroll Periods        → /hr/payroll
│  ├─ Payroll Processing     → /hr/payroll/process/<id>
│  ├─ Components             → /hr/payroll/components
│  ├─ Loans & Advances       → /hr/loans
│  └─ Payroll Reports        → /hr/reports/payroll
├─ Recruitment
│  ├─ Job Requisitions       → /hr/recruitment
│  ├─ Candidates             → /hr/recruitment/candidates
│  ├─ Interview Pipeline     → /hr/recruitment/pipeline
│  └─ Recruitment Reports    → /hr/reports/recruitment
├─ Onboarding/Offboarding
│  ├─ Onboarding Plans       → /hr/onboarding
│  ├─ Offboarding Requests   → /hr/offboarding
│  ├─ Probation Tracking     → /hr/probation
│  └─ Clearance Workflow     → /hr/clearance
├─ Performance Management
│  ├─ Goals                  → /hr/goals
│  ├─ Appraisals             → /hr/performance
│  ├─ Review Cycles          → /hr/performance/cycles
│  └─ Performance Reports    → /hr/reports/performance
├─ Talent & Succession
│  ├─ Talent Profiles        → /hr/talent
│  ├─ Hi-Po Watchlist       → /hr/talent/hipo
│  ├─ Succession Plans      → /hr/successors
│  └─ Talent Reports        → /hr/reports/talent
├─ Training & Learning
│  ├─ Training Programs      → /hr/training
│  ├─ Certifications         → /hr/certifications
│  ├─ Mandatory Training     → /hr/training/mandatory
│  └─ Learning Reports       → /hr/reports/training
├─ Employee Experience
│  ├─ Announcements          → /hr/announcements
│  ├─ HR Cases              → /hr/cases
│  └─ Experience Reports    → /hr/reports/experience
├─ HR Documents & Compliance
│  ├─ Employee Documents     → /hr/documents
│  ├─ Document Expiry       → /hr/documents/expiry
│  └─ Compliance Reports    → /hr/reports/compliance
├─ Workforce Planning
│  ├─ Headcount Plan        → /hr/workforce/headcount
│  ├─ Hiring Plan           → /hr/workforce/hiring
│  └─ Workforce Reports     → /hr/reports/workforce
├─ Reports & Analytics
│  ├─ HR Dashboard          → /hr/reports/dashboard
│  ├─ Custom Reports        → /hr/reports/custom
│  └─ Export Center        → /hr/export
├─ Workflow & Approvals
│  ├─ Pending Approvals     → /hr/approvals
│  └─ Approval History      → /hr/approvals/history
└─ Settings
   ├─ HR Settings           → /hr/settings
   ├─ Leave Settings        → /hr/settings/leave
   ├─ Attendance Settings   → /hr/settings/attendance
   └─ Payroll Settings      → /hr/settings/payroll
```

---

## 4. Key Features by Area

### 4.1 Employee Administration
- **Employee Master**: Comprehensive employee profiles with personal, job, and employment info
- **Employee Code Generation**: Sequential EMP{YYYY}{####} format
- **Employment History**: Track all changes (promotions, transfers, status changes)
- **Contract Management**: Track contract types, dates, and renewals
- **Employee Lifecycle Timeline**: Visual timeline of all HR events
- **Employee Directory**: Searchable directory with photos and contact info

### 4.2 Organization Management
- **Department Hierarchy**: Parent-child relationships with cost center linkage
- **Position Management**: Salary bands, grades, critical position flagging
- **Org Chart**: Visual representation of reporting lines
- **Vacant Positions**: Track and manage open positions
- **Headcount by Department**: Real-time headcount visualization

### 4.3 Attendance & Time Management
- **Shift Scheduling**: Multiple shift templates with grace periods
- **Attendance Recording**: Check-in/check-out with work hours calculation
- **Late/Early Detection**: Automatic detection with configurable grace minutes
- **Missing Punch Review**: Workflow for correcting attendance gaps
- **Overtime Management**: Request, approval, and payroll integration

### 4.4 Leave Management
- **Leave Types**: Configurable types with paid/unpaid, approval requirements
- **Leave Balances**: Automatic calculation with carry-forward rules
- **Leave Calendar**: Team calendar showing who's on leave
- **Approval Workflow**: Manager approval with remarks tracking
- **Team Conflict Alerts**: Warn when multiple team members request same leave period

### 4.5 Payroll & Compensation
- **Payroll Periods**: Monthly periods with draft/approved/locked statuses
- **Component-Based Pay**: Earning and deduction components
- **Overtime Integration**: Auto-calculate OT based on rate multipliers
- **Loan Management**: Track loans with installment schedules
- **Payslip Output**: Generate payslip documents (scaffold)

### 4.6 Recruitment
- **Job Requisitions**: Create, approve, and track requisitions
- **Candidate Pipeline**: Track candidates through stages (Applied → Screening → Interview → Offer → Hired)
- **Recruiter Assignment**: Assign recruiters to requisitions
- **Salary Offers**: Track offered salary and negotiation
- **Source Tracking**: Track where candidates came from

### 4.7 Onboarding/Offboarding
- **Onboarding Checklist**: Task list for new joiners
- **Probation Tracking**: Monitor probation progress
- **Document Collection**: Track required documents
- **Offboarding Workflow**: Request clearance, exit interview
- **Asset Return**: Link to asset management for equipment return

### 4.8 Performance Management
- **Goals**: Set and track employee goals
- **Review Cycles**: Annual/semi-annual review periods
- **Multi-Rater Reviews**: Self, manager, and peer reviews
- **Rating Scales**: Configurable rating definitions
- **Improvement Plans**: Track performance improvement actions

### 4.9 Talent & Succession
- **Talent Profiles**: Potential and readiness assessments
- **Succession Plans**: Plan for key role continuity
- **Hi-Po Watchlist**: Identify and track high potentials
- **Development Plans**: Create and track development actions
- **Career Paths**: Visualize potential career trajectories

### 4.10 Training & Learning
- **Training Programs**: Define programs with categories and providers
- **Mandatory Training**: Track required training by role/department
- **Enrollment Management**: Enroll employees in sessions
- **Certification Tracking**: Track certification expiry
- **Training Effectiveness**: Measure training outcomes

---

## 5. Security & Permissions

### 5.1 Permission Structure

Permissions follow the pattern: `hr.{resource}.{action}`

| Permission | Description |
|------------|-------------|
| `hr.hr.view` | View HR dashboard |
| `hr.employees.view` | View employee list |
| `hr.employees.create` | Create new employees |
| `hr.employees.edit` | Edit employee records |
| `hr.employees.delete` | Archive/terminate employees |
| `hr.departments.view` | View departments |
| `hr.departments.create` | Create departments |
| `hr.positions.view` | View positions |
| `hr.attendance.view` | View attendance |
| `hr.attendance.create` | Mark attendance |
| `hr.attendance.approve` | Approve attendance changes |
| `hr.leave.view` | View leave |
| `hr.leave.create` | Create leave requests |
| `hr.leave.approve` | Approve/reject leave |
| `hr.payroll.view` | View payroll |
| `hr.payroll.process` | Process payroll |
| `hr.payroll.approve` | Approve payroll |
| `hr.overtime.view` | View overtime |
| `hr.overtime.create` | Create overtime requests |
| `hr.overtime.approve` | Approve overtime |
| `hr.training.view` | View training |
| `hr.training.create` | Create training programs |
| `hr.documents.view` | View documents |
| `hr.documents.create` | Upload documents |
| `hr.documents.approve` | Verify documents |
| `hr.announcements.view` | View announcements |
| `hr.announcements.create` | Create announcements |
| `hr.recruitment.view` | View recruitment |
| `hr.recruitment.create` | Create requisitions |
| `hr.performance.view` | View performance |
| `hr.performance.create` | Create reviews |
| `hr.reports.view` | View reports |
| `hr.reports.export` | Export reports |
| `hr.settings.view` | View settings |
| `hr.settings.edit` | Modify settings |

### 5.2 Role-Based Access

| Role | Scope |
|------|-------|
| Global Admin | Full access to all HR functions |
| HR Admin | Full HR access except payroll final approval |
| HR Manager | Manage employees, leave, attendance, reports |
| HR Officer | Data entry and viewing |
| Attendance Officer | Attendance marking and reports |
| Payroll Reviewer | View payroll, cannot approve |
| Recruiter | Full recruitment access |
| Department Manager | Team-scoped access |
| Employee (Self-Service) | Own data only |
| Auditor | Read-only access with audit logs |

---

## 6. Integration Points

### 6.1 Flow Integration
- Leave approval notifications → Flow
- Announcement broadcasts → Flow channels
- Document expiry alerts → Flow
- Recruitment updates → Flow for authorized users
- Performance review reminders → Flow

### 6.2 Documents Module
- Employee documents stored via document_routes
- HR-specific folder structure (FLD-HR-001 through FLD-HR-005)
- Version tracking for HR documents
- Access control integration

### 6.3 Finance/Payroll
- Payroll periods linked to finance integration (scaffold)
- Loan installment deductions in payroll
- Bonus and overtime payment tracking

### 6.4 Assets
- Equipment assignment on onboarding
- Equipment return on offboarding
- Asset tracking linked to employee records

---

## 7. Reporting Architecture

### 7.1 Standard Reports

| Report | Route | Description |
|--------|-------|-------------|
| Headcount Report | `/hr/reports/headcount` | Employee count by dept/position/status |
| Leave Report | `/hr/reports/leave` | Leave usage by type and employee |
| Attendance Report | `/hr/reports/attendance` | Daily/monthly attendance summary |
| Overtime Report | `/hr/reports/overtime` | OT hours and costs |
| Payroll Summary | `/hr/reports/payroll` | Payroll totals by period |
| Recruitment Report | `/hr/reports/recruitment` | Pipeline and hiring metrics |
| Performance Report | `/hr/reports/performance` | Review completion and scores |
| Talent Report | `/hr/reports/talent` | Hi-Po and succession status |
| Training Report | `/hr/reports/training` | Completion and certification |
| Compliance Report | `/hr/reports/compliance` | Document expiry and visa status |

### 7.2 Export Capabilities

All reports support:
- PDF export with formatting
- Excel/CSV with column selection
- Configurable columns and filters
- Date range selection
- Branch/entity filtering

---

## 8. Multilingual Support

### 8.1 Supported Languages
- English (en) - Default
- Arabic (ar) - RTL
- Persian/Farsi (fa) - RTL
- Russian (ru)
- Hindi (hi)
- Spanish (es)
- Chinese (zh)
- German (de)

### 8.2 Translation Requirements
- All UI labels translated
- HR terminology standardized
- Date/number formatting per locale
- Mixed RTL/LTR content safe rendering

---

## 9. Technical Implementation

### 9.1 Routes File
- `hr_routes.py` - All Flask routes organized by function
- ~3000+ lines of route handlers

### 9.2 Models File
- `hr_models.py` - All database table definitions
- 31+ HR tables with proper foreign keys
- Helper functions for common operations

### 9.3 Templates
- 52+ HTML templates in `templates/hr/`
- Modern glass-panel design
- Responsive layouts
- Consistent component styling

### 9.4 Navigation
- Defined in `navigation.py` (lines ~5910-6041)
- Menu items with AR/FA translations
- Permission-based visibility

---

## 10. Future Enhancements

### 10.1 Payroll Engine
- Country-specific payroll calculations
- Tax computation integration
- Bank file generation for salary transfers

### 10.2 Self-Service Portal
- Employee self-service for profile updates
- Manager self-service for team management
- Mobile-responsive interface

### 10.3 Advanced Analytics
- Predictive attrition modeling
- Skills gap analysis
- Compensation benchmarking

### 10.4 Integration Expansion
- Biometric device integration
- Government e-services integration (e.g., MOL, TASheel)
- Benefits provider integrations