# WHDASH Payroll Module - Export Configuration Guide

## Overview

The WHDASH Payroll Module provides a comprehensive export system that allows users to export payroll data in multiple formats with configurable columns, filters, and grouping options.

## Export Capabilities

### Supported Export Formats

| Format | MIME Type | Use Case |
|--------|----------|----------|
| CSV | text/csv | Data import, Excel analysis |
| Excel | application/vnd.openxmlformats | Detailed reports, printing |
| PDF | application/pdf | Formal distribution |

## Export Types

### 1. Payroll Summary Export

**Purpose**: Complete payroll summary for a period

**Default Columns**:
- Employee Code
- Employee Name
- Department
- Basic Salary
- Total Allowances
- Total Earnings
- Total Deductions
- Overtime
- Tax
- Gross Salary
- Net Salary
- Days Worked
- Days Absent

**Configurable Options**:
- Add/remove columns
- Include/exclude overtime details
- Include/exclude deduction breakdown
- Show/hide YTD columns

### 2. Earnings Report Export

**Purpose**: Detailed earnings breakdown

**Default Columns**:
- Employee Code
- Employee Name
- Component Code
- Component Name
- Amount
- Quantity
- Rate
- Taxable (Yes/No)

**Configurable Options**:
- Group by employee or component
- Filter by component type
- Date range selection

### 3. Deductions Report Export

**Purpose**: Detailed deductions breakdown

**Default Columns**:
- Employee Code
- Employee Name
- Deduction Type
- Amount
- Pre-tax (Yes/No)
- Calculation Details

**Configurable Options**:
- Group by type or employee
- Filter by deduction category
- Include/exclude loan recoveries

### 4. Payslip Export

**Purpose**: Individual or batch payslip export

**Default Columns**:
- Payslip Number
- Employee Code
- Employee Name
- Period
- Basic Salary
- Earnings Itemized
- Deductions Itemized
- Net Salary

**Configurable Options**:
- Individual or batch selection
- Include/exclude itemized details
- PDF generation option

### 5. Bank File Export

**Purpose**: Bank transfer file generation

**Default Columns**:
- Employee Code
- Bank Account Number
- IBAN
- Bank Name
- Net Amount
- Payment Description

**Configurable Options**:
- Bank format selection
- Payment reference format
- Date format
- Header/footer customization

## Column Configuration

### Available Columns by Export Type

#### Employee Data Columns
- Employee Code
- Employee Name
- Arabic Name
- Department
- Position
- Join Date
- Employment Type

#### Payroll Data Columns
- Basic Salary
- Total Allowances
- Total Earnings
- Housing Allowance
- Transport Allowance
- Medical Allowance
- Overtime Hours
- Overtime Amount
- Bonus Amount
- Commission Amount
- Total Deductions
- Tax Amount
- Insurance Deduction
- Loan Recovery
- Advance Recovery
- Other Deductions
- Gross Salary
- Net Salary
- Days Worked
- Days Absent

#### Cost Allocation Columns
- Cost Center
- Branch
- Legal Entity

#### Bank Details Columns
- Bank Name
- Account Number
- IBAN
- Account Holder Name

### Column Ordering

Users can:
1. Drag and drop columns to reorder
2. Show/hide specific columns
3. Set default column sets
4. Save column configurations

### Saved Configurations

Users can save column configurations with:
- Configuration name
- Export type association
- Default flag
- Sharing options (personal or shared)

## Filter Configuration

### Available Filters

| Filter | Type | Description |
|--------|------|-------------|
| Period | Single/Multiple | Select one or more periods |
| Date Range | Range | Custom date range |
| Department | Multi-select | Filter by department |
| Branch | Multi-select | Filter by branch |
| Employee | Search | Search by employee name/code |
| Status | Multi-select | Filter by payroll status |
| Component Type | Multi-select | Filter by earnings/deductions |

### Filter Presets

Save commonly used filter combinations:
- "Current Month - All Departments"
- "Q1 2026 - Executive Staff"
- "Pending Approval Only"

## Grouping Options

### Group By
- Department
- Branch
- Cost Center
- Component Type
- Employee

### Subtotals

Enable subtotals when grouping:
- Show subtotal rows
- Calculate subtotal percentages
- Include subtotal in total

### Sorting Options

Multi-column sorting:
- Primary sort column
- Secondary sort column
- Sort direction (ASC/DESC)

## Export Workflow

### Step 1: Select Export Type
1. Navigate to Export Center
2. Select export type from menu
3. View available columns

### Step 2: Configure Columns
1. Check/uncheck columns
2. Drag to reorder
3. Click "Save Configuration" for reuse

### Step 3: Apply Filters
1. Select period(s)
2. Choose departments
3. Search employees if needed
4. Set date range if applicable

### Step 4: Preview
1. Click "Preview" to see sample data
2. Verify column selection
3. Check filter results

### Step 5: Generate Export
1. Select format (CSV/Excel/PDF)
2. Click "Export"
3. Download file or schedule delivery

## Scheduled Exports

### Setup Scheduled Export
1. Create export configuration
2. Click "Schedule Export"
3. Set frequency:
   - Daily
   - Weekly
   - Monthly
   - On period close
4. Configure delivery:
   - Email recipients
   - File naming convention
   - Storage location

### Scheduled Export Reports
- View export history
- Monitor schedule status
- Retry failed exports

## Bank File Configuration

### Bank Format Templates

#### UAE Bank Format (Default)
```
Header: Bank Code, Company Name, Account Number, Date
Detail: Employee Code, Account, Amount, Reference
Footer: Total Records, Total Amount, Hash Total
```

#### Custom Format
- Define field positions
- Set delimiter character
- Configure date format
- Set currency format

### Validation Rules
- Account number format check
- IBAN validation
- Amount precision check
- Duplicate detection

## Security Considerations

### Access Control
- Role-based export permissions
- Sensitive data restrictions
- Audit logging for all exports

### Data Protection
- Encrypted file transfer option
- Secure download links
- Time-limited access

### Audit Trail
- All exports logged with:
  - User ID
  - Timestamp
  - Export type
  - Record count
  - Download IP

## Best Practices

### Performance Optimization
1. Export only needed columns
2. Use date range filters
3. Export during off-peak hours for large datasets

### Data Accuracy
1. Always use finalized period data
2. Verify totals match summary reports
3. Check filter results before export

### Security
1. Limit who can export sensitive data
2. Use encrypted transfer for bank files
3. Regularly review export audit logs

## Troubleshooting

### Export Fails
1. Check disk space
2. Verify database connection
3. Reduce dataset size
4. Check file permissions

### Missing Data
1. Verify filters are correct
2. Check period status (data may not be finalized)
3. Confirm employee profiles are complete

### Large File Size
1. Reduce exported columns
2. Use CSV instead of Excel
3. Split into multiple exports by department

### Bank File Rejected
1. Verify IBAN format
2. Check for special characters
3. Confirm bank code accuracy
