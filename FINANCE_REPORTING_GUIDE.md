# Finance Reporting Guide

## Overview

This guide describes all financial reports available in the WHDASH Financial Management module, including how to run them, what data they use, interpretation guidance, and export options.

---

## 1. Financial Statements

### 1.1 Trial Balance

**Description**: Shows all account balances at a point in time with debit/credit columns.

**How to Run**:
1. Navigate to **Finance → Reports → Trial Balance**
2. Select "As of Date"
3. Choose fiscal period or custom date
4. Optionally filter by:
   - Account category
   - Cost center
   - Account code range
5. Click "Generate Report"

**Data Sources**:
- `finance_journal_lines` (posted journals only)
- `finance_accounts` (account definitions)
- `finance_fiscal_periods` (date filtering)

**Output Columns**:
| Column | Description |
|--------|-------------|
| Account Code | Chart of accounts code |
| Account Name | Account description |
| Debit | Sum of all debit transactions |
| Credit | Sum of all credit transactions |
| Net | Debit minus Credit |

**Filters**:
- Date range (period or custom)
- Account type filter
- Cost center filter
- Show only accounts with activity (Y/N)
- Include budget figures (Y/N)

**Interpretation**:
- Total Debits MUST equal Total Credits
- Use to verify books balance before financial statements
- Accounts with zero balances may be hidden

**Export Options**: PDF, Excel, CSV

---

### 1.2 Balance Sheet

**Description**: Snapshot of assets, liabilities, and equity at a specific date.

**How to Run**:
1. Navigate to **Finance → Reports → Balance Sheet**
2. Select "As of Date"
3. Choose company (for multi-entity)
4. Select comparison period (optional)
5. Click "Generate Report"

**Data Sources**:
- `finance_accounts` (account classification)
- `finance_journal_lines` (balances by account)
- `finance_fiscal_periods` (date filtering)
- `finance_account_categories` (grouping)

**Standard Layout**:

```
ASSETS
  Current Assets
    Cash and Cash Equivalents
    Accounts Receivable
    Inventory
    Prepaid Expenses
    Total Current Assets

  Non-Current Assets
    Fixed Assets (net)
    Intangible Assets
    Total Non-Current Assets

  TOTAL ASSETS

LIABILITIES
  Current Liabilities
    Accounts Payable
    Accrued Expenses
    Taxes Payable
    Total Current Liabilities

  Non-Current Liabilities
    Long-term Debt
    Total Non-Current Liabilities

  TOTAL LIABILITIES

EQUITY
  Capital Stock
  Retained Earnings
  Current Year Earnings
  TOTAL EQUITY

TOTAL LIABILITIES + EQUITY
```

**Interpretation**:
- Assets = Liabilities + Equity (must balance)
- Compare to prior period to identify changes
- Drill down on any line to see account detail

**Export Options**: PDF, Excel

---

### 1.3 Income Statement (Profit & Loss)

**Description**: Shows revenue, expenses, and net profit over a period.

**How to Run**:
1. Navigate to **Finance → Reports → Income Statement**
2. Select date range (period or custom)
3. Choose comparison period (previous year recommended)
4. Select cost center (optional)
5. Click "Generate Report"

**Data Sources**:
- `finance_journal_lines` (revenue and expense accounts)
- `finance_account_categories` (account classification)
- `finance_fiscal_periods` (date filtering)

**Standard Layout**:

```
REVENUE
  Sales Revenue
    Product Sales
    Service Revenue
    Wholesale Sales
  Other Revenue
  Total Revenue

EXPENSES
  Cost of Goods Sold
  Gross Profit (Revenue - COGS)

  Operating Expenses
    Selling Expenses
    General & Administrative
  Total Operating Expenses

  Other Expenses
    Interest Expense
  Total Other Expenses

NET PROFIT BEFORE TAX

Income Tax Expense
NET PROFIT
```

**Key Metrics**:
| Metric | Formula | Target |
|--------|---------|--------|
| Gross Margin | Gross Profit / Revenue | > 30% |
| Operating Margin | Operating Profit / Revenue | > 15% |
| Net Profit Margin | Net Profit / Revenue | > 10% |

**Interpretation**:
- Compare periods to identify trends
- Expense ratios (Expense / Revenue) should be stable
- Investigate unusual variances > 10%

**Export Options**: PDF, Excel

---

### 1.4 Cash Flow Statement

**Description**: Tracks cash inflows and outflows by activity type.

**How to Run**:
1. Navigate to **Finance → Reports → Cash Flow Statement**
2. Select date range
3. Choose cash account(s)
4. Click "Generate Report"

**Data Sources**:
- `finance_journal_lines` (cash accounts only)
- `finance_accounts` (classification for indirect method)
- Bank statement data (direct method, if available)

**Sections**:

```
CASH FLOWS FROM OPERATING ACTIVITIES
  Cash received from customers
  Cash paid to suppliers
  Cash paid to employees
  Cash paid for taxes
  Other operating cash flows
  Net Cash from Operations

CASH FLOWS FROM INVESTING ACTIVITIES
  Purchase of fixed assets
  Proceeds from asset disposal
  Other investing activities
  Net Cash from Investing

CASH FLOWS FROM FINANCING ACTIVITIES
  Proceeds from loans
  Repayment of loans
  Dividends paid
  Net Cash from Financing

NET CHANGE IN CASH
BEGINNING CASH BALANCE
ENDING CASH BALANCE
```

**Interpretation**:
- Operating cash flow should be positive
- Investing activities usually negative (asset purchases)
- Financing shows debt/equity changes

**Export Options**: PDF, Excel

---

## 2. Accounts Receivable Reports

### 2.1 AR Aging Report

**Description**: Shows outstanding customer invoices grouped by age (Current, 1-30, 31-60, 61-90, 90+ days).

**How to Run**:
1. Navigate to **Finance → Reports → AR Aging**
2. Select "As of Date"
3. Choose customer filter (all or specific)
4. Select aging buckets
5. Click "Generate Report"

**Data Sources**:
- `finance_customer_invoices` (invoice headers)
- `finance_customer_receipts` (payment applied)
- `customers` (customer details)

**Output Format**:
| Customer | Current | 1-30 Days | 31-60 Days | 61-90 Days | 90+ Days | Total |
|---------|---------|-----------|------------|------------|---------|-------|
| Al Fardan | 50,000 | 25,000 | 0 | 0 | 0 | 75,000 |
| Gulf Solutions | 0 | 30,000 | 45,000 | 0 | 0 | 75,000 |
| Dubai Retail | 0 | 0 | 0 | 100,000 | 0 | 100,000 |
| **TOTAL** | **50,000** | **55,000** | **45,000** | **100,000** | **0** | **250,000** |

**Key Metrics**:
- Days Sales Outstanding (DSO) = (AR Balance / Credit Sales) × Days
- Collection Efficiency = Collections / Beginning AR + Credit Sales

**Interpretation**:
- > 60 days = collection concern
- > 90 days = likely write-off risk
- Compare to payment terms (Net 30, Net 60)

**Export Options**: PDF, Excel, CSV

---

### 2.2 AR Detail Report

**Description**: Lists all open invoices with full details.

**How to Run**:
1. Navigate to **Finance → Reports → AR Detail**
2. Select date range or status filter
3. Choose customer(s)
4. Click "Generate Report"

**Output Columns**:
| Column | Description |
|--------|-------------|
| Invoice # | Unique invoice number |
| Date | Invoice date |
| Due Date | Payment due date |
| Customer | Customer name |
| Amount | Invoice total |
| Paid | Amount paid |
| Outstanding | Amount due |
| Days Outstanding | Days since due date |
| Status | Posted/Paid/Overdue |

**Export Options**: PDF, Excel

---

### 2.3 Customer Statement

**Description**: Account statement for a single customer showing all activity.

**How to Run**:
1. Navigate to **Finance → Reports → Customer Statement**
2. Select customer
3. Select date range
4. Click "Generate Report"

**Output**:
```
CUSTOMER STATEMENT
Al Fardan Trading
Period: January 1, 2026 - April 15, 2026

DATE       | DESCRIPTION           | DEBIT      | CREDIT     | BALANCE
-----------|-----------------------|------------|------------|----------
Jan 15     | Invoice INV-2026-001  | 57,500     |            | 57,500
Jan 20     | Payment RCT-2026-001  |            | 57,500    | 0
Feb 10     | Invoice INV-2026-003  | 34,500     |            | 34,500
Mar 5      | Payment RCT-2026-003  |            | 34,500    | 0
Apr 10     | Invoice INV-2026-008  | 69,000     |            | 69,000

                                      BALANCE DUE: | 69,000
```

**Export Options**: PDF

---

## 3. Accounts Payable Reports

### 3.1 AP Aging Report

**Description**: Shows outstanding supplier bills grouped by age.

**How to Run**:
1. Navigate to **Finance → Reports → AP Aging**
2. Select "As of Date"
3. Choose supplier filter
4. Click "Generate Report"

**Data Sources**:
- `finance_supplier_bills` (bill headers)
- `finance_supplier_payments` (payments applied)
- `suppliers` (supplier details)

**Output Format**:
| Supplier | Current | 1-30 Days | 31-60 Days | 61-90 Days | 90+ Days | Total |
|----------|---------|-----------|------------|------------|---------|-------|
| Emirates Supplies | 35,000 | 0 | 0 | 0 | 0 | 35,000 |
| Gulf Materials | 0 | 50,000 | 0 | 0 | 0 | 50,000 |
| Office Depot | 0 | 0 | 0 | 95,000 | 0 | 95,000 |
| **TOTAL** | **35,000** | **50,000** | **0** | **95,000** | **0** | **180,000** |

**Key Metrics**:
- Days Payable Outstanding (DPO) = (AP Balance / Purchases) × Days
- AP Turnover = Purchases / Average AP

**Interpretation**:
- Monitor for overdue payments (affects credit rating)
- Optimize payment timing for cash flow

**Export Options**: PDF, Excel, CSV

---

### 3.2 AP Detail Report

**Description**: Lists all open bills with full details.

**How to Run**:
1. Navigate to **Finance → Reports → AP Detail**
2. Select date range or status filter
3. Choose supplier(s)
4. Click "Generate Report"

**Output Columns**:
| Column | Description |
|--------|-------------|
| Bill # | Bill reference |
| Date | Bill date |
| Due Date | Payment due date |
| Supplier | Supplier name |
| Amount | Bill total |
| Paid | Amount paid |
| Outstanding | Amount due |
| Days Outstanding | Days since due date |
| Status | Posted/Paid/Overdue |

**Export Options**: PDF, Excel

---

### 3.3 Supplier Statement

**Description**: Account statement for a single supplier.

**How to Run**:
1. Navigate to **Finance → Reports → Supplier Statement**
2. Select supplier
3. Select date range
4. Click "Generate Report"

**Export Options**: PDF

---

## 4. Tax Reports

### 4.1 VAT Report

**Description**: Summary of VAT collected and paid for VAT filing.

**How to Run**:
1. Navigate to **Finance → Reports → Tax → VAT Report**
2. Select tax period (month/quarter)
3. Choose VAT type (All, Output, Input)
4. Click "Generate Report"

**Data Sources**:
- `finance_journals` with tax references
- `finance_tax_codes` (VAT rate determination)
- `finance_customer_invoices` (output VAT)
- `finance_supplier_bills` (input VAT)

**Output Format**:

```
VAT REPORT
Period: January 1, 2026 - January 31, 2026

OUTPUT VAT
  Standard Rate 15%
    Sales (AED)                    1,500,000
    VAT Collected (AED)               225,000

  Zero Rated 0%
    Exports                            500,000
    VAT Collected                         0

Total Output VAT                                   225,000

INPUT VAT
  Standard Rate 15%
    Purchases (AED)                    800,000
    VAT Paid (AED)                     120,000

  Recoverable Input VAT                             120,000

NET VAT PAYABLE                                   105,000
```

**Interpretation**:
- Output VAT > Input VAT = Payable to Tax Authority
- Input VAT > Output VAT = Receivable (carry forward)
- File VAT return before deadline (typically 28th of following month)

**Export Options**: PDF, Excel

---

### 4.2 Withholding Tax Report

**Description**: Summary of withholding tax deductions.

**How to Run**:
1. Navigate to **Finance → Reports → Tax → Withholding Tax**
2. Select date range
3. Click "Generate Report"

**Export Options**: PDF, Excel

---

## 5. Fixed Asset Reports

### 5.1 Fixed Asset Register

**Description**: Complete listing of all fixed assets with values.

**How to Run**:
1. Navigate to **Finance → Reports → Fixed Assets → Asset Register**
2. Select as-of date
3. Filter by category, status, cost center
4. Click "Generate Report"

**Data Sources**:
- `finance_assets` (asset master)
- `finance_asset_categories` (classification)
- `finance_depreciation_entries` (accumulated depreciation)
- `finance_cost_centers` (assignment)

**Output Columns**:
| Column | Description |
|--------|-------------|
| Asset Code | Unique identifier |
| Asset Name | Description |
| Category | Asset type |
| Acquisition Date | Date acquired |
| Cost | Original cost |
| Useful Life | Years for depreciation |
| Salvage Value | Expected residual value |
| Accumulated Depreciation | Total depreciation to date |
| Net Book Value | Current value |
| Location | Physical location |
| Cost Center | Department assigned |

**Key Metrics**:
- Asset Turnover = Revenue / Average Net Assets
- Age Analysis = Average Age vs Useful Life

**Export Options**: PDF, Excel

---

### 5.2 Depreciation Schedule

**Description**: Shows depreciation expense by asset and period.

**How to Run**:
1. Navigate to **Finance → Reports → Fixed Assets → Depreciation Schedule**
2. Select fiscal year
3. Choose asset filter
4. Click "Generate Report"

**Output Format**:
| Asset | Jan | Feb | Mar | ... | Dec | Total |
|-------|-----|-----|-----|-----|-----|-------|
| Dell Laptop | 236 | 236 | 236 | ... | 236 | 2,833 |
| Toyota Camry | 2,083 | 2,083 | 2,083 | ... | 2,083 | 25,000 |
| **TOTAL** | **2,319** | **2,319** | **2,319** | ... | **2,319** | **27,833** |

**Export Options**: PDF, Excel

---

### 5.3 Asset Disposal Report

**Description**: Summary of asset disposals in period.

**How to Run**:
1. Navigate to **Finance → Reports → Fixed Assets → Disposals**
2. Select date range
3. Click "Generate Report"

**Export Options**: PDF, Excel

---

## 6. Budget Reports

### 6.1 Budget vs Actual

**Description**: Compares budgeted amounts to actual expenses.

**How to Run**:
1. Navigate to **Finance → Reports → Budget → Budget vs Actual**
2. Select budget and fiscal year
3. Choose cost center filter (optional)
4. Select comparison period
5. Click "Generate Report"

**Data Sources**:
- `finance_budgets` and `finance_budget_lines` (budgets)
- `finance_journal_lines` (actuals)

**Output Format**:
| Account | Cost Center | Budget | Actual | Variance | Variance % |
|---------|-------------|--------|--------|----------|------------|
| 6210 Salaries | Executive | 900,000 | 875,000 | 25,000 | 2.8% Favorable |
| 6220 Rent | Executive | 300,000 | 290,000 | 10,000 | 3.3% Favorable |
| 6230 Utilities | Operations | 150,000 | 162,000 | -12,000 | -8.0% Unfavorable |
| **TOTAL** | | **1,350,000** | **1,327,000** | **23,000** | **1.7% Favorable** |

**Variance Calculation**:
- Variance = Budget - Actual
- Variance % = (Variance / Budget) × 100
- Favorable = Under budget (positive variance for expenses)
- Unfavorable = Over budget (negative variance for expenses)

**Interpretation**:
- Investigate variances > 5%
- Favorable variances may indicate opportunities
- Unfavorable variances require corrective action

**Export Options**: PDF, Excel

---

### 6.2 Budget Summary

**Description**: Overview of all budgets with total amounts.

**How to Run**:
1. Navigate to **Finance → Reports → Budget → Budget Summary**
2. Select fiscal year
3. Click "Generate Report"

**Export Options**: PDF, Excel

---

## 7. Bank Reconciliation Reports

### 7.1 Bank Reconciliation Statement

**Description**: Shows bank balance vs book balance with adjustments.

**How to Run**:
1. Navigate to **Finance → Reports → Bank → Reconciliation**
2. Select bank account
3. Select reconciliation period
4. Click "Generate Report"

**Output Format**:

```
BANK RECONCILIATION
Bank: Emirates NBD - Account XXXXX7890
Date: March 31, 2026

BANK BALANCE PER STATEMENT                    525,000
Add: Deposits in Transit
  Mar 31 deposit                               15,000
  Mar 30 deposit                               25,000
Less: Outstanding Checks
  Check #1234 (Mar 28)                        -20,000
  Check #1235 (Mar 29)                        -18,000

ADJUSTED BANK BALANCE                         527,000

BOOK BALANCE PER GL                           530,000
Add: Bank charges not recorded                 -1,500
Less: Interest earned not recorded              1,500

ADJUSTED BOOK BALANCE                         530,000

DIFFERENCE                                           0
```

**Interpretation**:
- Difference should be zero when reconciled
- Unreconciled items require investigation
- Typical items: timing differences, bank errors

**Export Options**: PDF

---

### 7.2 Outstanding Checks Report

**Description**: Lists checks issued but not yet cleared.

**How to Run**:
1. Navigate to **Finance → Reports → Bank → Outstanding Checks**
2. Select bank account
3. Select date
4. Click "Generate Report"

**Export Options**: PDF, Excel

---

## 8. Administrative Reports

### 8.1 Journal Entry Audit Trail

**Description**: Shows all journal entries with full audit information.

**How to Run**:
1. Navigate to **Finance → Reports → Audit → Journal Trail**
2. Select date range
3. Optionally filter by:
   - Journal number
   - User who created
   - Status
4. Click "Generate Report"

**Output Columns**:
| Column | Description |
|--------|-------------|
| JE Number | Journal entry reference |
| Date | Transaction date |
| Description | Entry description |
| Created By | User who created |
| Created At | Timestamp |
| Posted By | User who posted |
| Posted At | Timestamp |
| Status | Draft/Pending/Posted |
| Total | Entry amount |

**Export Options**: PDF, Excel, CSV

---

### 8.2 Period Status Report

**Description**: Shows status of all fiscal periods.

**How to Run**:
1. Navigate to **Finance → Reports → Administrative → Period Status**
2. Select fiscal year
3. Click "Generate Report"

**Output**:
| Period | Start Date | End Date | Status | Journals | Total Debits |
|--------|------------|----------|--------|----------|--------------|
| FY 2026 P01 | Jan 1 | Jan 31 | Open | 45 | 2,500,000 |
| FY 2026 P02 | Feb 1 | Feb 28 | Open | 52 | 2,750,000 |
| FY 2026 P03 | Mar 1 | Mar 31 | Open | 48 | 2,600,000 |
| FY 2025 P12 | Dec 1 | Dec 31 | Closed | 78 | 3,200,000 |

**Export Options**: PDF, Excel

---

## 9. Report Scheduling

### Scheduled Reports

Reports can be scheduled to run automatically and be emailed to stakeholders.

**Configuration**:
1. Navigate to **Finance → Reports → Schedule**
2. Click "New Schedule"
3. Configure:
   - Report type
   - Parameters
   - Frequency (Daily/Weekly/Monthly)
   - Recipients
   - Format (PDF/Excel)
4. Save schedule

**Common Scheduled Reports**:
| Report | Frequency | Recipients |
|--------|-----------|------------|
| Trial Balance | Daily | Controller |
| AR Aging | Weekly | AR Manager, CFO |
| AP Aging | Weekly | AP Manager, CFO |
| VAT Report | Monthly | Tax, CFO |
| Budget vs Actual | Monthly | Budget owners |

---

## 10. Custom Report Builder

For ad-hoc analysis, use the Custom Report Builder:

1. Navigate to **Finance → Reports → Custom Builder**
2. Select data source (GL, AR, AP, Assets)
3. Choose fields to include
4. Set filters and sorting
5. Preview results
6. Save as custom report or export

**Available Fields**: All fields from underlying tables are available for selection.

---

## 11. Common Use Cases

### Use Case 1: Month-End Financial Close Checklist

Run these reports in order:
1. Trial Balance - Verify debits = credits
2. AR Aging - Confirm collections on track
3. AP Aging - Verify payments scheduled
4. VAT Report - Calculate VAT payable
5. Journal Trail - Review all entries
6. Period Status - Lock period when complete

### Use Case 2: Cash Flow Analysis

Run:
1. Cash Flow Statement (indirect method)
2. Bank Reconciliation
3. Outstanding Checks
4. AR Aging (predict collections)

### Use Case 3: Budget Review Meeting

Run:
1. Budget vs Actual Summary
2. Detail drill-down by cost center
3. Prior year comparison (if available)

### Use Case 4: Customer Collections Review

Run:
1. AR Aging (current period)
2. AR Detail (all overdue items)
3. Customer Statement (specific customer)

---

## 12. Troubleshooting

### Report Shows No Data
- Verify date range includes transactions
- Check if filters are too restrictive
- Confirm period is open (not locked)
- Verify user has permission to view data

### Report Takes Too Long
- Narrow date range
- Limit to specific cost center
- Run during off-peak hours
- Export to Excel for large datasets

### Numbers Don't Match GL
- Check if comparing posted vs all entries
- Verify currency exchange rates applied
- Confirm period filters are consistent
- Look for unposted transactions

### Export Problems
- Clear browser cache
- Disable popup blocker for downloads
- Try different browser (Chrome recommended)
- Check file size limits (max 10MB for Excel)
