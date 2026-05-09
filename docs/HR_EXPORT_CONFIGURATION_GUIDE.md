# HR Module - Export Configuration Guide
## WHDASH Enterprise HR Platform

---

## 1. Overview

The HR module provides comprehensive export capabilities with user-controlled column selection, filtering, and format options. This guide explains how to configure and use all export features.

---

## 2. Export Types

### 2.1 Supported Formats

| Format | Description | Best For |
|--------|-------------|----------|
| PDF | Formatted document with headers and styling | Printing, Official reports, Archival |
| Excel (.xlsx) | Spreadsheet with multiple sheets option | Data analysis, Manipulation, Charts |
| CSV | Plain comma-separated values | Data import, Integration, Legacy systems |
| Print View | Optimized for direct printing | Physical printing, Simple reports |

### 2.2 Export Action Locations

All HR pages with data tables have export controls:

| Section | Export Location |
|---------|----------------|
| Employee List | `/hr/employees` - Export button in header |
| Attendance Reports | `/hr/reports/attendance-*` - Export dropdown |
| Leave Reports | `/hr/reports/leave-*` - Export dropdown |
| Payroll Reports | `/hr/reports/payroll-*` - Export dropdown |
| Recruitment | `/hr/reports/recruitment-*` - Export dropdown |
| Performance | `/hr/reports/performance-*` - Export dropdown |
| Reports Menu | `/hr/reports` - Central export center |

---

## 3. Column Selection Configuration

### 3.1 How Column Selection Works

On each report page with a data table:

1. Click the **"Export"** button (gear icon or dropdown)
2. A modal/panel appears with:
   - Available columns (left)
   - Selected columns (right)
   - Up/Down arrows to reorder
3. Check/uncheck columns to include/exclude
4. Drag to reorder columns
5. Click **"Apply"** to confirm
6. Choose format (PDF/Excel/CSV)
7. Click **"Download"**

### 3.2 Column Selection Modal

```
┌─────────────────────────────────────────────────────────┐
│ Export Configuration                                    │
├─────────────────────────────────────────────────────────┤
│ Format: [PDF ▼]  Date Range: [01/01/2024] to [31/12/2024]│
├───────────────────────┬─────────────────────────────────┤
│ AVAILABLE COLUMNS     │  SELECTED COLUMNS (in order)    │
│                       │                                  │
│ ☑ Employee Code      │  1. Employee Name              │
│ ☑ First Name          │  2. Department                  │
│ ☐ Middle Name         │  3. Position                    │
│ ☑ Last Name           │  4. Employee Code               │
│ ☐ Arabic Name         │  5. Hire Date                   │
│ ☑ Department          │  6. Status                      │
│ ☑ Position            │  7. Mobile                     │
│ ☐ Employment Type     │                                 │
│ ☑ Hire Date           │     [Move Up] [Move Down]      │
│ ☐ Confirmation Date   │                                 │
│ ☐ Termination Date    │                                 │
│ ☐ Nationality         │                                 │
│ ☐ Gender              │                                 │
│ ☐ Date of Birth       │                                 │
│ ☐ Mobile              │                                 │
│ ☐ Email               │                                 │
│ ☐ Bank Account        │                                 │
│ ☐ Manager             │                                 │
│                       │                                 │
│ [Select All] [Clear]  │                                 │
├───────────────────────┴─────────────────────────────────┤
│                        [Cancel] [Apply & Download]       │
└─────────────────────────────────────────────────────────┘
```

### 3.3 Default Column Sets

Each report type has preset columns:

**Employee Export Default:**
- Employee Code
- Full Name
- Department
- Position
- Status
- Hire Date
- Email
- Mobile

**Attendance Export Default:**
- Date
- Employee Code
- Employee Name
- Department
- Check In
- Check Out
- Work Hours
- Overtime Hours
- Status

**Leave Export Default:**
- Request ID
- Employee Name
- Department
- Leave Type
- Start Date
- End Date
- Total Days
- Status

---

## 4. Filter Configuration

### 4.1 Standard Filters

All exports respect the current page filters:

| Filter | Options | Applied To |
|--------|---------|------------|
| Date Range | Custom start/end dates | Attendance, Leave, Payroll |
| Department | Multi-select from list | All reports |
| Employee | Search and select | All reports |
| Status | Multi-select | Leave, Attendance |
| Position | Multi-select | Headcount, Reports |
| Employment Type | Full-time, Part-time, Contractor | Employee exports |
| Branch/Entity | Multi-select | All reports |

### 4.2 Filter Persistence

- Filters set on the page are automatically applied to export
- Use "Clear Filters" to reset before export
- Export-specific filters (like specific columns) do NOT affect page display

### 4.3 Quick Filter Presets

| Preset Name | Filters Applied |
|-------------|-----------------|
| This Month | Date range: current month |
| This Quarter | Date range: current quarter |
| This Year | Date range: January 1 - December 31 |
| Last Month | Date range: previous month |
| Last Quarter | Date range: previous quarter |
| All Active | Status: Active only |
| All Pending | Status: Pending approval |

---

## 5. Page-Specific Export Configurations

### 5.1 Employee List Export

**Route:** `GET /hr/employees/export`

**Exportable Columns:**

| Column Key | Column Name | Default |
|------------|-------------|---------|
| employee_code | Employee Code | ✓ |
| first_name | First Name | ✓ |
| last_name | Last Name | ✓ |
| full_name | Full Name | ✓ |
| arabic_name | Arabic Name | ✗ |
| email | Email | ✓ |
| mobile | Mobile | ✓ |
| department | Department | ✓ |
| position | Position | ✓ |
| employment_type | Employment Type | ✓ |
| status | Status | ✓ |
| hire_date | Hire Date | ✓ |
| confirmation_date | Confirmation Date | ✗ |
| probation_end_date | Probation End | ✗ |
| nationality | Nationality | ✗ |
| gender | Gender | ✗ |
| date_of_birth | Date of Birth | ✗ |
| manager | Manager Name | ✓ |
| company | Company/Entity | ✗ |

**Special Options:**
- Include former employees (default: active only)
- Include employment history summary
- Include profile photo (PDF only)

### 5.2 Attendance Report Export

**Route:** `GET /hr/reports/attendance/export`

**Exportable Columns:**

| Column Key | Column Name | Default |
|------------|-------------|---------|
| date | Date | ✓ |
| employee_code | Employee Code | ✓ |
| employee_name | Employee Name | ✓ |
| department | Department | ✓ |
| shift | Shift | ✓ |
| check_in | Check In | ✓ |
| check_out | Check Out | ✓ |
| work_hours | Work Hours | ✓ |
| overtime_hours | Overtime Hours | ✓ |
| late_minutes | Late Minutes | ✓ |
| early_leave_minutes | Early Leave | ✗ |
| status | Status | ✓ |
| remarks | Remarks | ✗ |

**Special Options:**
- Include approved overtime only
- Include only late arrivals
- Group by department
- Summary totals row

### 5.3 Leave Report Export

**Route:** `GET /hr/reports/leave/export`

**Exportable Columns:**

| Column Key | Column Name | Default |
|------------|-------------|---------|
| request_id | Request ID | ✓ |
| employee_code | Employee Code | ✓ |
| employee_name | Employee Name | ✓ |
| department | Department | ✓ |
| leave_type | Leave Type | ✓ |
| start_date | Start Date | ✓ |
| end_date | End Date | ✓ |
| total_days | Total Days | ✓ |
| reason | Reason | ✗ |
| status | Status | ✓ |
| approved_by | Approved By | ✗ |
| approved_date | Approved Date | ✗ |

**Special Options:**
- Include balance impact
- Group by leave type
- Include only pending
- Year filter

### 5.4 Payroll Report Export

**Route:** `GET /hr/reports/payroll/export`

**Exportable Columns:**

| Column Key | Column Name | Default |
|------------|-------------|---------|
| employee_code | Employee Code | ✓ |
| employee_name | Employee Name | ✓ |
| department | Department | ✓ |
| basic_salary | Basic Salary | ✓ |
| housing_allowance | Housing | ✓ |
| transport_allowance | Transport | ✓ |
| food_allowance | Food | ✗ |
| communication | Communication | ✗ |
| other_allowances | Other Allowances | ✗ |
| total_earnings | Total Earnings | ✓ |
| loan_deduction | Loan | ✓ |
| absence_deduction | Absence | ✓ |
| late_deduction | Late | ✗ |
| other_deductions | Other Deductions | ✗ |
| total_deductions | Total Deductions | ✓ |
| net_salary | Net Salary | ✓ |
| days_worked | Days Worked | ✓ |
| days_absent | Days Absent | ✗ |

**Special Options:**
- Hide salary columns (for non-payroll users)
- Include year-to-date totals
- Include employer contributions
- Per period / Year-to-date

**Security:** Salary columns require `hr.payroll.view` permission

### 5.5 Recruitment Report Export

**Route:** `GET /hr/reports/recruitment/export`

**Exportable Columns:**

| Column Key | Column Name | Default |
|------------|-------------|---------|
| requisition_id | Requisition ID | ✓ |
| position_title | Position Title | ✓ |
| department | Department | ✓ |
| candidate_name | Candidate Name | ✓ |
| stage | Pipeline Stage | ✓ |
| source | Source | ✓ |
| applied_date | Applied Date | ✓ |
| interview_score | Interview Score | ✗ |
| status | Status | ✓ |
| offer_salary | Offered Salary | ✗ |
| joining_date | Joining Date | ✗ |

**Special Options:**
- Include candidate CV path
- Include recruiter notes
- Pipeline stage timeline

### 5.6 Performance Report Export

**Route:** `GET /hr/reports/performance/export`

**Exportable Columns:**

| Column Key | Column Name | Default |
|------------|-------------|---------|
| employee_code | Employee Code | ✓ |
| employee_name | Employee Name | ✓ |
| department | Department | ✓ |
| review_cycle | Review Cycle | ✓ |
| review_date | Review Date | ✓ |
| overall_score | Overall Score | ✓ |
| rating | Rating | ✓ |
| strengths | Strengths | ✗ |
| areas_for_improvement | Areas for Improvement | ✗ |
| reviewer | Reviewer | ✓ |
| status | Status | ✓ |

### 5.7 Training Report Export

**Route:** `GET /hr/reports/training/export`

**Exportable Columns:**

| Column Key | Column Name | Default |
|------------|-------------|---------|
| program_name | Program Name | ✓ |
| category | Category | ✓ |
| employee_name | Employee Name | ✓ |
| department | Department | ✓ |
| session_date | Session Date | ✓ |
| attendance_status | Attendance | ✓ |
| score | Score | ✓ |
| grade | Grade | ✗ |
| certificate_number | Certificate # | ✗ |
| completion_date | Completion Date | ✓ |

**Special Options:**
- Include only mandatory training
- Include expired certifications
- Include upcoming renewals

### 5.8 Document Compliance Export

**Route:** `GET /hr/reports/compliance/export`

**Exportable Columns:**

| Column Key | Column Name | Default |
|------------|-------------|---------|
| employee_code | Employee Code | ✓ |
| employee_name | Employee Name | ✓ |
| department | Department | ✓ |
| document_type | Document Type | ✓ |
| document_number | Document Number | ✓ |
| issue_date | Issue Date | ✓ |
| expiry_date | Expiry Date | ✓ |
| days_remaining | Days Remaining | ✓ |
| status | Status | ✓ |
| verified_by | Verified By | ✗ |
| verified_date | Verified Date | ✗ |

**Special Options:**
- Include only expiring within 30/60/90 days
- Include expired only
- Status summary sheet

---

## 6. Export Output Files

### 6.1 File Naming Convention

```
{ReportType}_{Department}_{DateRange}_{ExportDate}
```

**Examples:**
- `Employees_All_2024-01-01_to_2024-12-31_2024-03-15.pdf`
- `Attendance_IT_Department_March_2024_2024-03-31.xlsx`
- `Leave_Requests_2024_2024-01-01_to_2024-03-15.csv`

### 6.2 PDF Export Styling

PDF exports include:
- Company logo (if configured)
- Report title and filters applied
- Generated date and user
- Page numbers
- Column headers with styling
- Alternating row colors
- Group headers

### 6.3 Excel Export Features

Excel exports include:
- Multiple worksheets (Summary, Detail, Filters Applied)
- Column auto-sizing
- Number formatting (dates, currency)
- Header row with filters
- Frozen header row
- Named ranges for data tables

### 6.4 CSV Export Features

CSV exports include:
- UTF-8 encoding (BOM for Excel compatibility)
- Comma delimiter
- Quoted text fields
- Header row included
- No formatting (pure data)

---

## 7. Export Settings

### 7.1 User Preferences

Users can set defaults for:
- Preferred export format
- Default columns per report type
- Email export vs download
- Scheduled export frequency

### 7.2 System Configuration (Admin)

Admin can configure:
- Maximum export rows (for performance)
- Export timeout settings
- Large file handling (chunked downloads)
- Export log retention
- Default filters per role

---

## 8. Scheduled Exports

### 8.1 Setting Up Scheduled Exports

1. Go to Reports menu
2. Select report type
3. Click "Schedule Export"
4. Configure:
   - Name
   - Frequency (Daily/Weekly/Monthly)
   - Format
   - Columns
   - Filters
   - Recipients (email)
5. Save schedule

### 8.2 Scheduled Export Options

| Frequency | Runs On | Best For |
|-----------|---------|----------|
| Daily | Every day at configured time | Attendance, Overtime |
| Weekly | Monday morning | Leave summary, Headcount |
| Monthly | 1st of month | Payroll, Compliance |
| Quarterly | Quarter start | Attrition, Reviews |

### 8.3 Notification

When scheduled export completes:
- Email to configured recipients
- Flow notification to creator
- Export log entry created

---

## 9. Export Log & Audit

### 9.1 Export Log Entry

Each export creates a log entry:

| Field | Value |
|-------|-------|
| Export ID | Auto-generated |
| User ID | Who exported |
| Report Type | Which report |
| Date/Time | When exported |
| Format | PDF/Excel/CSV |
| Row Count | Number of rows |
| Columns Included | List of columns |
| Filters Applied | Filter summary |
| File Size | In KB |

### 9.2 Audit Trail

Export actions are logged in `hr_audit_logs`:
- Logged when: Export action
- User: Who performed export
- Entity: Export configuration used
- IP Address: Source of export

---

## 10. Common Export Scenarios

### 10.1 Monthly Attendance Report for Finance

1. Go to `/hr/reports/attendance-monthly`
2. Filter: Date range = Last month, Department = All
3. Export → Select columns: Employee, Days Present, Days Absent, Overtime Hours, Net Pay
4. Format: Excel
5. Download

### 10.2 Annual Leave Summary for Audit

1. Go to `/hr/reports/leave-balances`
2. Filter: Year = 2024
3. Export → Select columns: Employee, Leave Type, Total, Used, Balance
4. Format: PDF
5. Download

### 10.3 Headcount Report for Board Meeting

1. Go to `/hr/reports/headcount`
2. Filter: Status = All (include inactive)
3. Export → Select columns: Department, Headcount, Active, On Leave, Probation, Vacant
4. Format: PDF
5. Download

### 10.4 Recruitment Pipeline for Weekly Review

1. Go to `/hr/reports/recruitment-pipeline`
2. Filter: Status = Open requisitions
3. Export → Select columns: Position, Stage, Count, Avg Time
4. Format: Excel
5. Download

---

## 11. Troubleshooting

### 11.1 Large Export Fails

**Problem:** Export times out for large datasets

**Solution:**
- Apply department filter to reduce data
- Export in chunks (by month)
- Contact admin to increase timeout

### 11.2 Missing Columns

**Problem:** Some columns not appearing in export

**Solution:**
- Check column selection modal
- Ensure column is checked in "Available" and moved to "Selected"
- Some columns require permissions (e.g., salary fields)

### 11.3 Incorrect Date Format

**Problem:** Dates showing incorrectly

**Solution:**
- Date format follows user's locale setting
- Check browser locale configuration
- Report uses server date format by default

### 11.4 Permission Denied on Export

**Problem:** "You don't have permission to export"

**Solution:**
- User needs `hr.reports.export` permission
- Contact HR Admin to grant permission
- Some exports (payroll) require additional `hr.payroll.view`