# Expense & Travel Management - Reporting Guide

## Available Reports

### 1. Expense Claims Report
**Route**: `/expense-travel/reports/expense-claims`

**Description**: Comprehensive analysis of all expense claims.

**Filters**:
- Date range (from/to)
- Department
- Status
- Employee
- Category

**Columns**:
- Claim Number
- Claim Date
- Employee Name
- Department
- Business Purpose
- Amount
- Currency
- Status
- Submitted Date
- Approved Date
- Paid Date

**Charts**:
- Claims by status (pie chart)
- Amount by department (bar chart)
- Monthly trend (line chart)

**Export**: Excel, CSV

---

### 2. Travel Requests Report
**Route**: `/expense-travel/reports/travel-requests`

**Description**: Travel patterns and cost analysis.

**Filters**:
- Date range
- Destination country/city
- Status
- Employee

**Columns**:
- Travel Number
- Employee
- Destination
- Trip Purpose
- Start Date
- End Date
- Duration (days)
- Estimated Cost
- Actual Cost (if completed)
- Status

**Charts**:
- Travel by destination (bar chart)
- Cost by month (line chart)
- Trips by status (pie chart)

**Export**: Excel, CSV

---

### 3. Cash Advances Report
**Route**: `/expense-travel/reports/cash-advances`

**Description**: Cash advance requests and settlement status.

**Filters**:
- Date range
- Status
- Employee
- Overdue only

**Columns**:
- Advance Number
- Employee
- Department
- Requested Amount
- Approved Amount
- Outstanding Balance
- Issue Date
- Settlement Date
- Status

**Charts**:
- Advances by status
- Outstanding by department
- Average processing time

**Export**: Excel, CSV

---

### 4. Reimbursement Report
**Route**: `/expense-travel/reports/reimbursements`

**Description**: Reimbursement processing and payment status.

**Filters**:
- Date range
- Payment status
- Employee
- Payment method

**Columns**:
- Reimbursement Number
- Claim Number
- Employee
- Gross Amount
- Advance Deduction
- Net Reimbursement
- Payment Date
- Payment Reference
- Status

**Charts**:
- Reimbursements by month
- Average processing time
- By payment method

**Export**: Excel, CSV

---

### 5. Policy Violations Report
**Route**: `/expense-travel/reports/violations`

**Description**: Policy compliance and violation tracking.

**Filters**:
- Date range
- Severity
- Status
- Category

**Columns**:
- Violation Code
- Claim Number
- Employee
- Category
- Amount
- Threshold
- Severity
- Exception Status
- Resolution

**Charts**:
- Violations by category
- Severity distribution
- Exception approval rate

**Export**: Excel, CSV

---

### 6. Department Expense Summary
**Route**: `/expense-travel/reports/by-department`

**Description**: Expense summary grouped by department.

**Columns**:
- Department
- Total Claims
- Total Amount
- Average Amount
- Min/Max Claims
- Approval Rate

**Charts**:
- Top spending departments
- Department approval rates

**Export**: Excel, CSV

---

### 7. Employee Expense History
**Route**: `/expense-travel/reports/employee-history`

**Description**: Individual employee expense history.

**Filters**:
- Employee
- Date range
- Category

**Columns**:
- Employee
- Claim Number
- Date
- Category
- Amount
- Status
- Processing Time

**Export**: Excel, PDF

---

## Executive Dashboards

### Main Dashboard
**Route**: `/expense-travel/dashboard`

**KPIs Displayed**:
- Total claims
- Pending approvals
- Approved claims
- Paid reimbursements
- Open advances
- Overdue settlements
- Policy violations
- Missing receipts

**Refresh Rate**: Real-time

---

### Executive Dashboard
**Route**: `/expense-travel/executive-dashboard`

**KPIs Displayed**:
- Total spend (MTD/YTD)
- Spend by department
- Spend by category
- Travel cost breakdown
- Advance outstanding
- Reimbursement cycle time
- Policy compliance rate

**Charts**:
- Spend trend (12 months)
- Department comparison
- Category breakdown
- Status distribution

---

## Custom Report Builder

### Available Metrics

| Metric | Description |
|--------|-------------|
| `total_claims` | Count of all claims |
| `total_amount` | Sum of all amounts |
| `avg_amount` | Average claim amount |
| `processing_days` | Days from submit to approve |
| `reimbursement_days` | Days from approve to pay |
| `violation_rate` | % of claims with violations |
| `approval_rate` | % of claims approved |
| `rejection_rate` | % of claims rejected |

### Available Dimensions

| Dimension | Group By |
|-----------|---------|
| `employee` | Employee |
| `department` | Department |
| `branch` | Branch |
| `category` | Expense category |
| `status` | Claim status |
| `date` | Month/Quarter/Year |
| `travel_type` | Travel type |
| `destination` | Country/City |

### Creating Custom Reports

1. Navigate to Reports & Analytics
2. Click "Create Custom Report"
3. Select metrics and dimensions
4. Apply filters
5. Choose visualization
6. Save report template

---

## Export Configuration

### Column Selection
Users can select which columns to include in exports.

### Filter Scope
Define the default filter scope for the report.

### Grouping Options
- By department
- By employee
- By month
- By category
- Custom grouping

### Sort Order
Configure default sort field and direction.

---

## Scheduled Reports

### Available Schedules
- Daily at midnight
- Weekly on Monday
- Monthly on 1st
- Quarterly

### Report Distribution
- Email to specified recipients
- Flow notification
- Download link

### Retention
- Last 12 months of exports stored
- Auto-cleanup of older exports