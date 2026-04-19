# WHDASH Payroll Module - Reporting Guide

## Overview

The WHDASH Payroll Module provides a comprehensive suite of reports and analytics designed to meet the needs of payroll managers, HR professionals, finance teams, and executives.

## Report Categories

### 1. Payroll Summary Reports

#### Payroll Summary Report
- **Purpose**: High-level overview of payroll for a period
- **Data Included**:
  - Total employees processed
  - Gross payroll amount
  - Total deductions
  - Net payroll amount
  - Breakdown by department
  - Breakdown by component type
- **Access**: Payroll Manager, HR Reviewer, Finance Reviewer, Executive
- **Export Formats**: PDF, Excel, CSV

#### Period Comparison Report
- **Purpose**: Compare payroll across periods
- **Data Included**:
  - Month-over-month variance
  - Employee count changes
  - Salary structure changes
  - Deduction trend analysis
- **Access**: Payroll Manager, Executive

### 2. Earnings Reports

#### Detailed Earnings Report
- **Purpose**: Itemized view of all earnings
- **Data Included**:
  - Employee details
  - Component breakdown
  - Hours/quantity (for variable pay)
  - Amount
  - YTD totals
- **Filters**:
  - Period
  - Department
  - Component type
  - Employee
- **Export Formats**: Excel, CSV

#### Earnings by Type Report
- **Purpose**: Aggregate earnings by component
- **Data Included**:
  - Basic Salary total
  - Allowances breakdown
  - Overtime total
  - Bonuses total
  - Other earnings
- **Access**: Payroll Manager, Finance Reviewer

### 3. Deductions Reports

#### Detailed Deductions Report
- **Purpose**: Itemized view of all deductions
- **Data Included**:
  - Employee details
  - Deduction type
  - Amount
  - YTD totals
- **Filters**: Period, Department, Deduction type
- **Export Formats**: Excel, CSV

#### Tax Report
- **Purpose**: Tax withholding summary
- **Data Included**:
  - Employee
  - Taxable income
  - Tax withheld
  - Tax brackets applied
- **Access**: Payroll Manager, Finance Reviewer (restricted)

### 4. Overtime Reports

#### Overtime Summary Report
- **Purpose**: Overtime hours and costs
- **Data Included**:
  - Employee
  - Overtime type (Regular, Weekend, Holiday)
  - Hours
  - Rate
  - Amount
- **Filters**: Period, Employee, OT Type
- **Export Formats**: Excel, CSV

#### Overtime Trend Report
- **Purpose**: Track overtime patterns
- **Data Included**:
  - Monthly overtime hours
  - Monthly overtime cost
  - Employee count with OT
  - Average OT per employee
- **Access**: Payroll Manager, HR Reviewer

### 5. Loan & Advance Reports

#### Loan Portfolio Report
- **Purpose**: Overview of all loans
- **Data Included**:
  - Loan details
  - Principal amount
  - Amount recovered
  - Amount outstanding
  - Installment schedule
  - Status
- **Filters**: Status, Loan Type, Employee
- **Export Formats**: Excel, PDF

#### Loan Recovery Report
- **Purpose**: Track loan repayments
- **Data Included**:
  - Employee
  - Loan number
  - Installment amount
  - Amount paid
  - Due date
  - Status (Paid, Overdue, Pending)
- **Filters**: Period, Status
- **Export Formats**: Excel, CSV

#### Advance Status Report
- **Purpose**: Salary advance tracking
- **Data Included**:
  - Employee
  - Advance amount
  - Recovery status
  - Remaining balance
- **Export Formats**: Excel

### 6. Variance Reports

#### Payroll Variance Report
- **Purpose**: Identify unusual payroll changes
- **Data Included**:
  - Employee
  - Prior period amount
  - Current period amount
  - Variance (amount and percentage)
  - Flag for review
- **Threshold Configuration**: Configurable variance threshold
- **Access**: Payroll Manager, HR Reviewer

### 7. Compliance Reports

#### Compliance Dashboard Summary
- **Purpose**: Overview of compliance status
- **Data Included**:
  - Rules checked
  - Pass/Fail counts
  - Critical violations
  - Resolution status
- **Access**: Payroll Manager, Auditor

#### Audit Trail Report
- **Purpose**: Detailed audit log
- **Data Included**:
  - Timestamp
  - User
  - Action
  - Entity type
  - Entity ID
  - Changes made
- **Filters**: Date range, User, Action type, Entity type
- **Access**: Auditor, Compliance Officer

### 8. Finance Integration Reports

#### Journal Posting Report
- **Purpose**: Finance journal entries from payroll
- **Data Included**:
  - Posting number
  - Date
  - Description
  - Debit amounts
  - Credit amounts
  - Status
- **Access**: Finance Reviewer, Payroll Manager

#### Cost Allocation Report
- **Purpose**: Cost center distribution
- **Data Included**:
  - Cost center
  - Department
  - Amount allocated
  - Percentage of total
- **Access**: Finance Reviewer

### 9. Export Center

The Export Center provides flexible data export with the following features:

#### Export Types
- **Summary Export**: Complete payroll summary
- **Detailed Export**: Full employee payroll details
- **Earnings Export**: All earnings data
- **Deductions Export**: All deductions data
- **Custom Export**: User-selected columns

#### Configuration Options
- **Column Selection**: Choose which columns to include
- **Column Order**: Drag-and-drop column ordering
- **Filters**:
  - Period range
  - Department filter
  - Employee filter
  - Status filter
- **Grouping**: Group by department, component type
- **Sorting**: Multi-column sort options

#### Export Formats
| Format | Use Case |
|--------|----------|
| CSV | Data import, further analysis |
| Excel (.xlsx) | Detailed reports, charts |
| PDF | Printing, formal distribution |

## Dashboard Analytics

### Executive Dashboard
- YTD payroll totals
- Monthly trend charts
- Department comparison
- Top deductions breakdown
- Variance to budget

### Processing Dashboard
- Current period status
- Run progress
- Exception summary
- Pending approvals
- Processing queue

### Compliance Dashboard
- Rules compliance status
- SOD violation alerts
- Recent audit entries
- Exception watchlist

## Report Access by Role

| Report | Payroll Admin | Payroll Manager | HR Reviewer | Finance | Auditor | Executive |
|--------|--------------|------------------|-------------|--------|--------|----------|
| Payroll Summary | ✓ | ✓ | ✓ | ✓ | | ✓ |
| Detailed Earnings | ✓ | ✓ | ✓ | | | |
| Deductions | ✓ | ✓ | ✓ | ✓ | | |
| Tax Report | ✓ | ✓ | | ✓ | | |
| Overtime | ✓ | ✓ | ✓ | | | |
| Loan Portfolio | ✓ | ✓ | | | | |
| Variance | ✓ | ✓ | ✓ | | | |
| Compliance | ✓ | ✓ | | | ✓ | |
| Audit Trail | | | | | ✓ | |
| Finance Posting | ✓ | ✓ | | ✓ | | |

## Scheduling & Distribution

### Automated Reports
Reports can be scheduled for automatic generation and distribution:

- **Monthly Payroll Summary**: Generated after period close
- **Compliance Report**: Generated weekly
- **Audit Trail**: Available on-demand

### Distribution Lists
- Configure email distribution for reports
- Role-based automatic routing
- Secure delivery with encryption option

## Best Practices

1. **Regular Review**: Review variance reports before period close
2. **Compliance Monitoring**: Check compliance dashboard daily during processing
3. **Audit Trail**: Review audit logs for any unauthorized access
4. **Data Retention**: Export and archive reports per company policy
5. **Access Control**: Assign report access based on job function

## Troubleshooting

### Report Not Loading
- Check database connection
- Verify report permissions
- Clear cache and retry

### Export Failing
- Check available disk space
- Verify file permissions
- Reduce data scope if timeout

### Missing Data
- Verify period status (must be Processed/Approved)
- Check employee payroll profiles
- Confirm component assignments
