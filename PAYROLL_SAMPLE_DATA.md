# WHDASH Payroll Module - Sample Data Guide

## Overview

This document describes the sample data provided with the WHDASH Payroll Module for demonstration and testing purposes.

## Sample Data Overview

The seed data includes:
- 10+ sample employees with payroll profiles
- 12 monthly payroll periods
- Sample payroll runs with calculated records
- Loan and advance examples
- Retro adjustment samples
- Compliance rule results
- Finance posting samples
- Audit log entries

## Sample Employees

### Employee Records

| Code | Name | Department | Position | Basic Salary |
|------|------|------------|----------|--------------|
| EMP001 | Ahmed Al Mansouri | Executive | CEO | 60,000 |
| EMP002 | Fatima Al Zahra | Finance | CFO | 45,000 |
| EMP003 | Mohammed Hassan | IT | Manager | 35,000 |
| EMP004 | Sara Khalid | HR | HR Manager | 30,000 |
| EMP005 | Omar Ibrahim | Operations | Supervisor | 25,000 |
| EMP006 | Layla Mohammed | Sales | Sales Lead | 25,000 |
| EMP007 | Yusuf Ahmed | Finance | Accountant | 20,000 |
| EMP008 | Noor Hassan | IT | Developer | 20,000 |
| EMP009 | Ali Omar | Operations | Technician | 15,000 |
| EMP010 | Mariam Khalid | HR | HR Officer | 15,000 |

## Sample Components

### Earnings
| Code | Name | Type | Default Amount |
|------|------|------|---------------|
| BASIC | Basic Salary | Earning | - |
| HRA | House Rent Allowance | Allowance | 25% of Basic |
| TRANSPORT | Transport Allowance | Allowance | 1,500 |
| MEDICAL | Medical Allowance | Allowance | 800 |
| OT_REG | Overtime - Regular | Earning | Hourly Rate |
| OT_Wknd | Overtime - Weekend | Earning | 2x Hourly |
| BONUS | Bonus | Earning | Variable |

### Deductions
| Code | Name | Type | Rate |
|------|------|------|------|
| TAX | Income Tax | Tax | Calculated |
| PF_EE | Provident Fund - Employee | Contribution | 5% |
| LOAN_RECV | Loan Recovery | Deduction | Per Schedule |
| ADV_RECV | Advance Recovery | Deduction | Per Schedule |
| ABSENT | Absent Deduction | Deduction | 1 Day Pay |

## Sample Payroll Periods

### Current Year Periods

| Period | Status | Employees | Total Net |
|--------|--------|----------|-----------|
| January 2026 | Closed | 10 | 450,000 |
| February 2026 | Closed | 10 | 455,000 |
| March 2026 | Closed | 10 | 452,000 |
| April 2026 | Processing | 10 | - |
| May 2026 | Open | - | - |

### Closed Period Summary

- **Total Payroll Processed**: 1,357,000 AED
- **Total Deductions**: 203,550 AED
- **Total Tax Withheld**: 67,850 AED

## Sample Loans

### Active Loans

| Loan Number | Employee | Type | Principal | Monthly | Balance |
|-------------|---------|------|-----------|---------|---------|
| LN2026001 | Ahmed Al Mansouri | Housing | 200,000 | 11,111 | 177,776 |
| LN2026002 | Fatima Al Zahra | Personal | 50,000 | 4,167 | 41,670 |
| LN2026003 | Mohammed Hassan | Car | 80,000 | 6,667 | 73,337 |

### Loan Status Distribution

- Active Loans: 8
- Completed Loans: 2
- Suspended Loans: 0
- Total Outstanding: 892,450 AED

## Sample Retro Adjustments

### Pending Adjustments

| Retro Number | Employee | Type | Amount | Reason |
|--------------|----------|------|--------|--------|
| RETRO2026001 | Sara Khalid | Salary Correction | 2,000 | Missed increase |
| RETRO2026002 | Yusuf Ahmed | Bonus Correction | 1,500 | Calculation error |

## Sample Compliance Results

### Validation Results (Latest Run)

| Rule | Status | Violations |
|------|--------|------------|
| Minimum Salary | Pass | 0 |
| Max OT Hours | Pass | 0 |
| Bank Details | Pass | 0 |
| Tax ID | Warning | 1 |
| SOD Check | Pass | 0 |
| Duplicate Payment | Pass | 0 |

## Sample Finance Postings

### Journal Entries

| Posting Number | Period | Type | Amount | Status |
|---------------|--------|------|--------|--------|
| PP2026001 | January 2026 | Salary | 450,000 | Posted |
| PP2026002 | February 2026 | Salary | 455,000 | Posted |

### Journal Lines (Sample)

**PP2026001 - January 2026**

| Account | Type | Amount |
|---------|------|--------|
| 6100-Salary Expense | Debit | 450,000 |
| 1200-Cash/Bank | Credit | 405,000 |
| 2200-Tax Payable | Credit | 45,000 |

## Sample Audit Entries

### Recent Audit Activity

| Timestamp | User | Action | Entity | Details |
|-----------|------|--------|--------|---------|
| 2026-04-15 09:30 | admin | CREATE | payroll_runs | Created run for April |
| 2026-04-15 10:15 | admin | CALCULATE | payroll_runs | Calculated 10 employees |
| 2026-04-15 11:00 | admin | APPROVE | payroll_runs | Approved run |
| 2026-04-15 11:30 | admin | LOCK | payroll_periods | Locked April period |

## Generating Sample Data

To regenerate sample data:

```bash
python seed_payroll_data.py
```

This will:
1. Create payroll calendars
2. Generate 12 monthly periods
3. Create payroll profiles for employees
4. Populate component assignments
5. Generate sample runs for closed periods
6. Create sample loans and installments
7. Add retro adjustments
8. Populate compliance results
9. Generate audit log entries

## Customization

### Modifying Sample Salaries

Edit the `seed_payroll_data.py` file:

```python
# Change salary ranges
salaries = [8000, 12000, 15000, 20000, 25000, 30000, 35000, 40000, 50000, 60000]
```

### Adding More Employees

Extend the sample_employees list:

```python
sample_employees = [
    ('EMP001', 'Ahmed', 'Al Mansouri', 'Active'),
    # Add more...
]
```

### Changing Period Configuration

Modify the period generation logic:

```python
# Adjust months generated
months = [
    ('January', 1), ('February', 2), # ...
]
```

## Testing Scenarios

### Scenario 1: Process Monthly Payroll

1. Select current open period
2. Create new payroll run
3. Add all employees
4. Run validation
5. Calculate payroll
6. Review and approve
7. Lock period
8. Generate payslips

### Scenario 2: Handle Retro Adjustment

1. Create retroactive adjustment
2. Approve adjustment
3. Include in next payroll run
4. Verify arrears calculation

### Scenario 3: Loan Recovery

1. Create new loan for employee
2. Approve loan
3. Verify installment schedule
4. Process payroll with recovery
5. Track outstanding balance

### Scenario 4: Compliance Exception

1. View exception dashboard
2. Identify open exception
3. Investigate root cause
4. Resolve with notes
5. Verify resolution

## Data Cleanup

To reset payroll data:

```python
# WARNING: This deletes all payroll data!
db.execute("DELETE FROM payroll_audit_log")
db.execute("DELETE FROM payroll_exceptions")
# ... continue for all tables
```

## Production Considerations

When moving to production:

1. **Remove Sample Data**
   - Clear test employees
   - Reset salary amounts
   - Remove demo loans

2. **Configure Real Settings**
   - Set company-specific tax rules
   - Configure actual GL accounts
   - Set bank file formats

3. **Validate Configuration**
   - Test with small employee set
   - Verify calculations
   - Confirm approval workflows
