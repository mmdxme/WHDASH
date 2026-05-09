# HR Module - Reporting Guide
## WHDASH Enterprise HR Platform

---

## 1. Overview

The HR module provides comprehensive reporting and analytics capabilities across all HR functions. Reports are available in PDF, Excel, and CSV formats with full multilingual support.

---

## 2. Report Categories

### 2.1 Employee Reports

#### 2.1.1 Employee Master Report
**Route:** `/hr/reports/employee-master`
**Description:** Complete employee listing with all personal and employment details

| Column | Description |
|--------|-------------|
| Employee Code | Unique identifier |
| Full Name | Employee full name |
| Department | Current department |
| Position | Current position |
| Employment Type | Full-time/Part-time/Contractor |
| Hire Date | Date of joining |
| Status | Active/On Leave/Probation/Terminated |
| Nationality | Employee nationality |
| Mobile | Contact number |
| Email | Email address |
| Manager | Direct manager name |
| Salary (Basic) | Basic salary amount |

**Filters:**
- Status (Active, Inactive, All)
- Department (Multi-select)
- Employment Type
- Hire Date Range
- Nationality

#### 2.1.2 Employment History Report
**Route:** `/hr/reports/employment-history`
**Description:** Employment changes and history for selected employees

| Column | Description |
|--------|-------------|
| Employee Code | Unique identifier |
| Employee Name | Full name |
| History Type | Hire, Promotion, Transfer, Salary Change |
| Field Changed | Specific field modified |
| Old Value | Previous value |
| New Value | New value |
| Effective Date | Date of change |
| Approved By | Who approved |

#### 2.1.3 Headcount Report
**Route:** `/hr/reports/headcount`
**Description:** Employee count analysis by various dimensions

| Column | Description |
|--------|-------------|
| Department | Department name |
| Position | Position title |
| Headcount | Number of employees |
| Active | Active count |
| On Leave | Currently on leave |
| Probation | In probation |
| Vacant Positions | Open positions |
| Total Capacity | Headcount + Vacant |

**Drill-down:** Department → Position → Employee

---

### 2.2 Attendance Reports

#### 2.2.1 Daily Attendance Report
**Route:** `/hr/reports/attendance-daily`
**Description:** Day-wise attendance summary

| Column | Description |
|--------|-------------|
| Date | Attendance date |
| Total Employees | Expected headcount |
| Present | Count present |
| Absent | Count absent |
| Late | Count late arrivals |
| Early Leave | Count early departures |
| Attendance Rate | % present |
| Late Rate | % late |

**Filters:**
- Date Range
- Department
- Shift

#### 2.2.2 Monthly Attendance Summary
**Route:** `/hr/reports/attendance-monthly`
**Description:** Monthly attendance aggregation

| Column | Description |
|--------|-------------|
| Employee | Employee name and code |
| Department | Department |
| Total Days | Working days in month |
| Present | Days present |
| Absent | Days absent |
| Late | Days with late arrival |
| Work Hours | Total hours worked |
| Overtime Hours | Extra hours worked |
| Late Minutes | Total minutes late |

#### 2.2.3 Missing Punch Report
**Route:** `/hr/reports/missing-punch`
**Description:** Attendance records with missing check-in or check-out

| Column | Description |
|--------|-------------|
| Employee | Employee name |
| Date | Date of missing punch |
| Shift | Expected shift |
| Missing | Check-in / Check-out / Both |
| Status | Pending / Approved / Rejected |
| Reviewed By | Who reviewed |
| Action Taken | Correction made |

#### 2.2.4 Overtime Report
**Route:** `/hr/reports/overtime`
**Description:** Overtime hours and costs analysis

| Column | Description |
|--------|-------------|
| Employee | Name and code |
| Department | Department |
| Overtime Date | Date of OT |
| Hours | OT hours worked |
| Type | Regular / Weekend / Holiday |
| Rate | Rate multiplier applied |
| Amount | Calculated OT pay |
| Status | Approved / Pending / Rejected |
| Included in Payroll | Yes / No |

---

### 2.3 Leave Reports

#### 2.3.1 Leave Request Report
**Route:** `/hr/reports/leave-requests`
**Description:** All leave requests with status

| Column | Description |
|--------|-------------|
| Request ID | Unique identifier |
| Employee | Name and code |
| Department | Department |
| Leave Type | Type of leave |
| Start Date | Leave start |
| End Date | Leave end |
| Total Days | Days requested |
| Reason | Leave reason |
| Status | Pending / Approved / Rejected |
| Approved By | Approver name |
| Approved Date | Date of approval |

**Filters:**
- Status
- Leave Type
- Department
- Date Range

#### 2.3.2 Leave Balance Report
**Route:** `/hr/reports/leave-balances`
**Description:** Current leave balances for all employees

| Column | Description |
|--------|-------------|
| Employee | Name and code |
| Department | Department |
| Leave Type | Type |
| Total Days | Annual entitlement |
| Used | Days used |
| Pending | Days in approval |
| Available | Balance remaining |
| Carry Forward | Days carried from previous year |
| Expiry | Carry forward expiry date |

#### 2.3.3 Leave Calendar
**Route:** `/hr/leave/calendar`
**Description:** Visual calendar showing who's on leave

**Views:**
- Month view (default)
- Week view
- Department filter
- Team filter

**Features:**
- Color-coded by leave type
- Hover for employee details
- Click to view leave request
- Conflict warnings

---

### 2.4 Payroll Reports

#### 2.4.1 Payroll Summary Report
**Route:** `/hr/reports/payroll-summary`
**Description:** Period-wise payroll totals

| Column | Description |
|--------|-------------|
| Period | Month/Year |
| Total Employees | Employees processed |
| Total Basic | Sum of basic salaries |
| Total Allowances | Sum of allowances |
| Total Overtime | Sum of OT payments |
| Total Bonuses | Sum of bonuses |
| Total Deductions | Sum of deductions |
| Gross Payroll | Total earnings |
| Net Payroll | Total net payable |
| Status | Draft / Approved / Locked |

#### 2.4.2 Payroll Detail Report
**Route:** `/hr/reports/payroll-detail`
**Description:** Employee-wise payroll breakdown

| Column | Description |
|--------|-------------|
| Employee Code | EMP ID |
| Employee Name | Full name |
| Department | Department |
| Basic Salary | Base pay |
| Housing Allowance | HRA component |
| Transport Allowance | TA component |
| Other Allowances | Other allowances |
| Overtime | OT amount |
| Bonuses | Bonus amount |
| Gross Earnings | Total earnings |
| Loan Deduction | Loan installments |
| Absence Deduction | Leave deductions |
| Other Deductions | Other deductions |
| Total Deductions | Sum of deductions |
| Net Salary | Payable amount |
| Status | Paid / Pending |

#### 2.4.3 Loan Report
**Route:** `/hr/reports/loans`
**Description:** Employee loan status and repayment tracking

| Column | Description |
|--------|-------------|
| Loan ID | Unique identifier |
| Employee | Name and code |
| Department | Department |
| Loan Type | Personal / Education / etc. |
| Principal Amount | Original loan amount |
| Interest Rate | Annual interest |
| Tenure | Months |
| Monthly Installment | EMI amount |
| Amount Paid | Total paid to date |
| Amount Remaining | Outstanding balance |
| Start Date | Loan start date |
| End Date | Loan end date |
| Status | Active / Closed / Defaulted |
| Next Installment | Due date and amount |

#### 2.4.4 Bonus & Deduction Report
**Route:** `/hr/reports/bonuses-deductions`
**Description:** All bonus and deduction transactions

| Column | Description |
|--------|-------------|
| Transaction ID | Unique identifier |
| Employee | Name and code |
| Type | Bonus / Deduction |
| Category | Specific type |
| Amount | Transaction amount |
| Effective Period | Month/Year |
| Reason | Description |
| Status | Approved / Pending |
| Included in Payroll | Yes / No |

---

### 2.5 Recruitment Reports

#### 2.5.1 Recruitment Pipeline Report
**Route:** `/hr/reports/recruitment-pipeline`
**Description:** Candidates by stage and requisition

| Column | Description |
|--------|-------------|
| Requisition | Position title |
| Department | Department |
| Stage | Pipeline stage |
| Candidates | Count in stage |
| Avg Time in Stage | Days in stage |
| Conversion Rate | % moving to next stage |

**Stages:** Applied → Screening → Interview → Offer → Hired/Rejected

#### 2.5.2 Time to Hire Report
**Route:** `/hr/reports/time-to-hire`
**Description:** Recruitment cycle time analysis

| Column | Description |
|--------|-------------|
| Position | Job title |
| Department | Department |
| Requisition Date | When opened |
| Hire Date | When filled |
| Days Open | Time to fill |
| Screening Days | Days in screening |
| Interview Days | Days in interview |
| Offer Days | Days to offer |
| Source | Candidate source |

#### 2.5.3 Source Effectiveness Report
**Route:** `/hr/reports/source-effectiveness`
**Description:** Recruitment source performance

| Column | Description |
|--------|-------------|
| Source | Where candidates came from |
| Total Candidates | Candidates applied |
| In Pipeline | Currently in process |
| Hired | Successfully hired |
| Hire Rate | % converted |
| Avg Time to Hire | Days from apply to hire |
| Cost per Hire | Cost effectiveness |

---

### 2.6 Performance Reports

#### 2.6.1 Performance Review Report
**Route:** `/hr/reports/performance-reviews`
**Description:** Review cycle completion and scores

| Column | Description |
|--------|-------------|
| Employee | Name and code |
| Department | Department |
| Review Cycle | Year/Period |
| Review Date | Date of review |
| Reviewer | Manager name |
| Overall Score | Rating (1-5) |
| Status | Draft / Submitted / Acknowledged |
| Completion Date | When acknowledged |

#### 2.6.2 Goal Achievement Report
**Route:** `/hr/reports/goal-achievement`
**Description:** Goal tracking and completion

| Column | Description |
|--------|-------------|
| Employee | Name and code |
| Goal Title | Goal description |
| Due Date | Target date |
| Status | Pending / In Progress / Completed / Overdue |
| Progress | % complete |
| Achieved | Yes / No |
| Rating | Goal rating |

#### 2.6.3 Rating Distribution Report
**Route:** `/hr/reports/rating-distribution`
**Description:** Performance rating distribution analysis

| Column | Description |
|--------|-------------|
| Rating | 1 to 5 scale |
| Count | Employees at this rating |
| Percentage | % of total |
| Department | Breakdown by department |

---

### 2.7 Talent & Succession Reports

#### 2.7.1 Hi-Po Watchlist Report
**Route:** `/hr/reports/hipo-watchlist`
**Description:** High potential employee tracking

| Column | Description |
|--------|-------------|
| Employee | Name and code |
| Current Position | Title |
| Department | Department |
| Readiness Level | Ready Now / 1 Year / 2 Years |
| Target Role | Succession target |
| Development Plan | Has plan / Needs plan |
| Last Review | Date of last review |
| Risk Level | High / Medium / Low |

#### 2.7.2 Succession Plan Report
**Route:** `/hr/reports/succession-plans`
**Description:** Succession planning status

| Column | Description |
|--------|-------------|
| Current Role | Position |
| Department | Department |
| Incumbent | Current holder |
| Successor | Identified successor |
| Deputy | Backup successor |
| Readiness | Readiness level |
| Handover Date | Planned transition |
| Status | Active / Pending / Urgent |
| Training Needed | Required development |

---

### 2.8 Training Reports

#### 2.8.1 Training Completion Report
**Route:** `/hr/reports/training-completion`
**Description:** Training program completion tracking

| Column | Description |
|--------|-------------|
| Program | Training program name |
| Category | Training category |
| Sessions | Total sessions |
| Enrolled | Employees enrolled |
| Attended | Employees completed |
| Completion Rate | % completed |
| Avg Score | Average score |
| Passed | Count passed |

#### 2.8.2 Certification Expiry Report
**Route:** `/hr/reports/certification-expiry`
**Description:** Certifications approaching expiry

| Column | Description |
|--------|-------------|
| Employee | Name and code |
| Department | Department |
| Certification | Certificate name |
| Valid Until | Expiry date |
| Days Remaining | Days until expiry |
| Status | Valid / Expiring / Expired |
| Renewal Required | Yes / No |

#### 2.8.3 Mandatory Training Matrix
**Route:** `/hr/reports/mandatory-training`
**Description:** Mandatory training compliance by employee

| Column | Description |
|--------|-------------|
| Employee | Name and code |
| Department | Department |
| Training | Required program |
| Status | Completed / Pending / Overdue |
| Completion Date | When completed |
| Next Due | Renewal date |

---

### 2.9 Document & Compliance Reports

#### 2.9.1 Document Expiry Report
**Route:** `/hr/reports/document-expiry`
**Description:** Documents approaching expiry

| Column | Description |
|--------|-------------|
| Employee | Name and code |
| Department | Department |
| Document Type | Type of document |
| Document Number | ID number |
| Issue Date | Date issued |
| Expiry Date | Date expires |
| Days Remaining | Days until expiry |
| Status | Valid / Expiring / Expired |
| Alert Level | Normal / Warning / Critical |

#### 2.9.2 Compliance Status Report
**Route:** `/hr/reports/compliance-status`
**Description:** Overall compliance by category

| Category | Total | Valid | Expiring | Expired | Compliance Rate |
|----------|-------|-------|----------|---------|-----------------|
| Passport | 150 | 140 | 8 | 2 | 93.3% |
| Emirates ID | 150 | 145 | 4 | 1 | 96.7% |
| Visa | 150 | 142 | 6 | 2 | 94.7% |
| Medical Insurance | 150 | 138 | 10 | 2 | 92.0% |

---

### 2.10 Workforce Reports

#### 2.10.1 Headcount Planning Report
**Route:** `/hr/reports/headcount-planning`
**Description:** Current vs planned headcount

| Column | Description |
|--------|-------------|
| Department | Department name |
| Current Headcount | As of today |
| Planned Headcount | Target headcount |
| Variance | Difference |
| Vacancies | Open positions |
| Budget | Approved budget |
| Status | On Track / At Risk / Over Budget |

#### 2.10.2 Attrition Report
**Route:** `/hr/reports/attrition`
**Description:** Employee turnover analysis

| Column | Description |
|--------|-------------|
| Period | Month/Quarter/Year |
| Total Employees | Average headcount |
| New Hires | Joined |
| Resignations | Left voluntarily |
| Terminations | Dismissed |
| Total Turnover | All departures |
| Turnover Rate | % of average headcount |
| By Department | Breakdown |
| By Tenure | Breakdown by years |
| By Reason | Exit reasons |

#### 2.10.3 Department Staffing Report
**Route:** `/hr/reports/department-staffing`
**Description:** Staffing levels by department

| Column | Description |
|--------|-------------|
| Department | Name |
| Headcount | Current count |
| Approved Headcount | Budgeted |
| Variance | Difference |
| On Leave | Currently absent |
| Probation | In probation |
| Contractors | Headcount type |
| Avg Tenure | Average service years |

---

## 3. Report Features

### 3.1 Filtering Capabilities

All reports support:
- **Date Range:** Custom start/end dates
- **Department:** Multi-select department filter
- **Employee:** Individual or group selection
- **Status:** Various status filters
- **Branch/Entity:** Multi-entity filtering

### 3.2 Export Formats

| Format | Use Case |
|--------|----------|
| PDF | Official reports, printing, archival |
| Excel (.xlsx) | Data analysis, further manipulation |
| CSV | Data import, integration |

### 3.3 Report Schedules

Reports can be scheduled for automatic generation:
- Daily (attendance, overtime)
- Weekly (leave summary, headcount)
- Monthly (payroll, performance)
- Quarterly (attrition analysis, compliance)

### 3.4 Report Access Control

- Reports filtered by user's department scope
- Sensitive reports (payroll) require elevated permissions
- Export actions are logged in audit trail

---

## 4. Dashboard Widgets

### 4.1 HR Executive Dashboard

| Widget | Metrics |
|--------|---------|
| Headcount Summary | Total, Active, New Hires, Turnover |
| On Leave Today | Employee count on leave |
| Pending Approvals | Leave, OT, Payroll pending |
| Attendance Rate | Today's attendance % |
| Open Vacancies | Active job requisitions |
| Expiring Documents | 30-day expiry count |
| Overtime Hours | This month's OT |
| New Candidates | In recruitment pipeline |

### 4.2 Department Manager Dashboard

| Widget | Metrics |
|--------|---------|
| Team Headcount | Direct reports count |
| Team on Leave | Who's on leave |
| Team Attendance | Attendance rate |
| Pending Approvals | OT, Leave requests |
| Probation Ending | Team members in probation |
| Training Compliance | Mandatory training status |
| Performance Reviews | Team review status |

### 4.3 Employee Self-Service Dashboard

| Widget | Metrics |
|--------|---------|
| Leave Balance | Available days by type |
| Upcoming Leave | Scheduled leave |
| Attendance This Month | Days present/absent |
| Training Assigned | Required training |
| Goals Progress | Goal completion % |
| Announcements | Latest HR notices |

---

## 5. Custom Report Builder

### 5.1 Available Fields

Users can build custom reports by selecting:
- Employee fields
- Employment fields
- Attendance fields
- Leave fields
- Payroll fields
- Custom calculated fields

### 5.2 Report Templates

Pre-built templates for common reports:
- Monthly Attendance Summary
- Leave Usage by Department
- Payroll Cost Analysis
- Recruitment Funnel
- Training Effectiveness

---

## 6. Data Visualization

### 6.1 Chart Types

| Report | Recommended Chart |
|--------|-------------------|
| Headcount Trend | Line chart (monthly) |
| Attendance Rate | Area chart |
| Leave by Type | Pie chart |
| Turnover by Department | Bar chart |
| Recruitment Pipeline | Funnel |
| Performance Distribution | Histogram |

### 6.2 Drill-Down Capabilities

- Headcount → Department → Position → Employee
- Attendance → Department → Employee → Day
- Leave → Department → Employee → Request
- Payroll → Period → Employee → Components