# Finance Sample Data Guide

## Overview

This document describes the comprehensive seed data for the WHDASH Financial Management module, explaining what data is seeded, sample values, test scenarios, and how to reset the data.

---

## 1. Seed Data Overview

The seed data script (`seed_finance_data.py`) creates a realistic demo company called **"WHDASH Trading LLC"** - a diversified trading company based in Dubai, UAE with operations across the GCC region.

### Company Profile

| Field | Value |
|-------|-------|
| Company Name | WHDASH Trading LLC |
| Industry | Wholesale/Retail Trading |
| Location | Dubai, UAE |
| Fiscal Year | January 1 - December 31 |
| Base Currency | AED (UAE Dirham) |
| VAT Rate | 15% Standard |
| Tax Registration | VAT-REG-XXXX |

---

## 2. Seed Data Components

### 2.1 Account Categories

| Code | Name | Financial Statement |
|------|------|---------------------|
| ASSET | Assets | Balance Sheet |
| LIABILITY | Liabilities | Balance Sheet |
| EQUITY | Equity | Balance Sheet |
| REVENUE | Revenue | Income Statement |
| COGS | Cost of Goods Sold | Income Statement |
| EXPENSE | Expenses | Income Statement |
| OTHER_INCOME | Other Income | Income Statement |
| OTHER_EXPENSE | Other Expenses | Income Statement |

**Total**: 8 categories

---

### 2.2 Chart of Accounts (70+ Accounts)

#### Assets (1000-1999)
| Code | Name | Type | Control Account |
|------|------|------|-----------------|
| 1000 | Cash and Cash Equivalents | ASSET | No |
| 1010 | Cash on Hand | ASSET | No |
| 1020 | Cash at Bank - Current Account | ASSET | Yes |
| 1030 | Cash at Bank - Savings Account | ASSET | No |
| 1100 | Accounts Receivable | ASSET | Yes |
| 1110 | AR - Trade Customers | ASSET | Yes |
| 1120 | AR - Related Parties | ASSET | No |
| 1130 | AR - Employees | ASSET | No |
| 1200 | Inventory | ASSET | No |
| 1210 | Finished Goods | ASSET | No |
| 1220 | Work in Progress | ASSET | No |
| 1230 | Raw Materials | ASSET | No |
| 1300 | Prepaid Expenses | ASSET | No |
| 1400 | Fixed Assets | ASSET | No |
| 1410 | Land and Buildings | ASSET | No |
| 1420 | Office Equipment | ASSET | No |
| 1430 | Vehicles | ASSET | No |
| 1440 | Computer Equipment | ASSET | No |
| 1500 | Accumulated Depreciation | ASSET | No |
| 1600 | Intangible Assets | ASSET | No |
| 1700 | Deposits | ASSET | No |
| 1800 | VAT Receivable | ASSET | No |

#### Liabilities (2000-2999)
| Code | Name | Type | Control Account |
|------|------|------|-----------------|
| 2000 | Current Liabilities | LIABILITY | No |
| 2100 | Accounts Payable | LIABILITY | Yes |
| 2110 | AP - Trade Suppliers | LIABILITY | Yes |
| 2120 | AP - Related Parties | LIABILITY | No |
| 2200 | Accrued Expenses | LIABILITY | No |
| 2210 | Salaries Payable | LIABILITY | No |
| 2220 | Interest Payable | LIABILITY | No |
| 2230 | Utilities Payable | LIABILITY | No |
| 2300 | Taxes Payable | LIABILITY | No |
| 2310 | VAT Payable | LIABILITY | No |
| 2320 | Income Tax Payable | LIABILITY | No |
| 2330 | Withholding Tax Payable | LIABILITY | No |
| 2400 | Deferred Revenue | LIABILITY | No |
| 2500 | Long-term Liabilities | LIABILITY | No |
| 2510 | Bank Loans | LIABILITY | No |
| 2600 | Customer Deposits | LIABILITY | No |

#### Equity (3000-3999)
| Code | Name |
|------|------|
| 3000 | Equity |
| 3100 | Capital Stock |
| 3200 | Retained Earnings |
| 3300 | Current Year Earnings |
| 3400 | Owner Drawings |

#### Revenue (4000-4999)
| Code | Name |
|------|------|
| 4000 | Revenue |
| 4100 | Sales Revenue |
| 4110 | Product Sales |
| 4120 | Service Revenue |
| 4130 | Wholesale Sales |
| 4200 | Other Revenue |
| 4210 | Interest Income |
| 4220 | Commission Income |
| 4300 | Sales Returns |
| 4400 | Sales Discounts |

#### Cost of Goods Sold (5000-5999)
| Code | Name |
|------|------|
| 5000 | Cost of Goods Sold |
| 5100 | Cost of Products Sold |
| 5110 | Direct Material Cost |
| 5120 | Direct Labor Cost |
| 5130 | Manufacturing Overhead |
| 5200 | Inventory Adjustment |

#### Expenses (6000-6999)
| Code | Name |
|------|------|
| 6000 | Operating Expenses |
| 6100 | Selling Expenses |
| 6110 | Advertising |
| 6120 | Sales Commissions |
| 6130 | Travel and Entertainment |
| 6200 | General and Administrative |
| 6210 | Salaries and Wages |
| 6220 | Rent Expense |
| 6230 | Utilities Expense |
| 6240 | Insurance Expense |
| 6250 | Office Supplies |
| 6260 | Professional Fees |
| 6300 | Depreciation Expense |
| 6400 | Bank Charges |
| 6500 | Communication Expense |
| 6600 | IT Expenses |
| 6700 | Maintenance and Repairs |
| 6800 | Training and Development |

#### Other Income (7000-7999)
| Code | Name |
|------|------|
| 7000 | Other Income |
| 7100 | Interest Income |
| 7200 | Gain on Asset Disposal |
| 7300 | Rental Income |

#### Other Expenses (8000-8999)
| Code | Name |
|------|------|
| 8000 | Other Expenses |
| 8100 | Interest Expense |
| 8200 | Loss on Asset Disposal |
| 8300 | Charitable Contributions |
| 8400 | Penalties and Fines |

**Total**: 70+ accounts

---

### 2.3 Fiscal Years and Periods

| Year | Status | Periods |
|------|--------|---------|
| FY 2024 | Closed | 12 periods (Jan-Dec) |
| FY 2025 | Closed | 12 periods (Jan-Dec) |
| FY 2026 | Open | 12 periods (Jan-Dec) |

**Current Period**: April 2026

---

### 2.4 Tax Codes

| Code | Name | Rate | Type |
|------|------|------|------|
| VAT-STD | Standard VAT 15% | 15% | Output |
| VAT-ZERO | Zero Rated VAT 0% | 0% | Output |
| VAT-EX | Exempt VAT 0% | 0% | Exempt |
| TAX-5 | Sales Tax 5% | 5% | Output |
| TAX-10 | Service Tax 10% | 10% | Output |
| CUST-5 | Customs Duty 5% | 5% | Input |
| CUST-10 | Customs Duty 10% | 10% | Input |
| NO-TX | No Tax | 0% | Exempt |

---

### 2.5 Cost Centers

| Code | Name | Department | Manager |
|------|------|------------|---------|
| CC-001 | Executive Office | Executive | Ahmed Hassan |
| CC-002 | Finance Department | Finance | Fatima Ali |
| CC-003 | Sales and Marketing | Sales | Omar Khalid |
| CC-004 | Operations | Operations | Sara Mohammed |
| CC-005 | Human Resources | HR | Youssef Ibrahim |
| CC-006 | IT Department | IT | Layla Ahmed |
| CC-007 | Warehouse | Warehouse | Karim Nasser |
| CC-008 | Procurement | Procurement | Noor Hassan |

---

### 2.6 Profit Centers

| Code | Name | Business Segment | Manager |
|------|------|------------------|---------|
| PC-001 | Corporate Office | Corporate | Ahmed Hassan (CEO) |
| PC-002 | Retail Division | Retail | Omar Khalid (Retail Director) |
| PC-003 | Wholesale Division | Wholesale | Sara Mohammed (Wholesale Director) |
| PC-004 | Export Division | Export | Youssef Ibrahim (Export Director) |
| PC-005 | E-Commerce Division | E-Commerce | Layla Ahmed (E-Commerce Director) |

---

### 2.7 Bank Accounts

| Bank | Account Name | Number | Currency | Balance (AED) |
|------|--------------|--------|----------|---------------|
| Emirates NBD | Business Current - AED | 1234567890 | AED | 500,000 |
| Emirates NBD | Business Savings - AED | 1234567891 | AED | 200,000 |
| First Abu Dhabi Bank | Corporate Current - AED | 9876543210 | AED | 750,000 |
| Standard Chartered | USD Business Account | US5432109876 | USD | 100,000 |
| Dubai Islamic Bank | Current Account - AED | DIB123456789 | AED | 300,000 |

---

### 2.8 Journal Entries (30+ Entries)

| Journal | Type | Date | Description | Amount (AED) |
|---------|------|------|-------------|---------------|
| JE-2026-001 | Payment | 2026-01-01 | Rent Payment - January 2026 | 25,000 |
| JE-2026-002 | Utility | 2026-01-05 | DEWA Bill - January 2026 | 4,525 |
| JE-2026-003 | Payroll | 2026-01-15 | Salaries - January 1st half | 85,000 |
| JE-2026-004 | Purchase | 2026-01-10 | Purchase of Laptop - Dell XPS 15 | 8,500 |
| JE-2026-005 | Sales | 2026-01-08 | Invoice #INV-2026-001 - Al Fardan | 34,500 |
| JE-2026-006 | Bank Charge | 2026-01-31 | Bank fees - January 2026 | 850 |
| JE-2026-007 | Payment | 2026-02-01 | Rent Payment - February 2026 | 25,000 |
| JE-2026-008 | Utility | 2026-02-05 | DEWA Bill - February 2026 | 5,175 |
| JE-2026-009 | Payroll | 2026-02-15 | Salaries - February 1st half | 85,000 |
| JE-2026-010 | Sales | 2026-02-10 | Service Revenue - Gulf Solutions | 46,000 |
| JE-2026-011 | Purchase | 2026-02-12 | Office furniture purchase | 28,000 |
| JE-2026-012 | Sales | 2026-02-15 | Wholesale invoice - Marina Wholesale | 115,000 |
| JE-2026-013 | Journal | 2026-02-20 | Prepaid insurance amortization | 5,000 |
| JE-2026-014 | Bank Charge | 2026-02-28 | Bank fees - February 2026 | 920 |
| JE-2026-015 | Payment | 2026-03-01 | Rent Payment - March 2026 | 25,000 |
| JE-2026-016 | Utility | 2026-03-05 | DEWA Bill - March 2026 | 5,850 |
| JE-2026-017 | Payroll | 2026-03-15 | Salaries - March 1st half | 87,500 |
| JE-2026-018 | Sales | 2026-03-08 | Product sales - Dubai Retail | 69,000 |
| JE-2026-019 | Purchase | 2026-03-12 | Raw materials purchase | 57,500 |
| JE-2026-020 | COGS | 2026-03-25 | Cost of goods sold - March | 35,000 |
| JE-2026-021 | Journal | 2026-03-28 | Internet and communication | 4,200 |
| JE-2026-022 | Depreciation | 2026-03-31 | Monthly depreciation | 8,500 |
| JE-2026-023 | Payment | 2026-04-01 | Rent Payment - April 2026 | 25,000 |
| JE-2026-024 | Payroll | 2026-04-15 | Salaries - April 1st half | 90,000 |
| JE-2026-025 | Sales | 2026-04-10 | Product sales - Export | 92,000 |
| JE-2026-026 | Purchase | 2026-04-12 | IT equipment | 15,000 |
| JE-2026-027 | Journal | 2026-04-20 | Maintenance expense | 6,500 |
| JE-2026-028 | Bank Charge | 2026-04-30 | Bank fees - April 2026 | 1,100 |
| JE-2025-001 | Year End | 2025-12-31 | Close revenue accounts | 2,500,000 |
| JE-2025-002 | Year End | 2025-12-31 | Close expense accounts | 2,100,000 |
| JE-2025-003 | Year End | 2025-12-31 | Close income summary | 400,000 |

**Total**: 30+ journal entries

---

### 2.9 AR Invoices (18 Invoices)

| Invoice | Customer | Date | Amount | Status |
|---------|----------|------|--------|--------|
| INV-2026-001 | Customer 1 | 45 days ago | 57,500 | Paid |
| INV-2026-002 | Customer 2 | 30 days ago | 34,500 | Paid |
| INV-2026-003 | Customer 3 | 20 days ago | 86,250 | Paid |
| INV-2026-004 | Customer 4 | 15 days ago | 115,000 | Paid |
| INV-2026-005 | Customer 5 | 10 days ago | 46,000 | Paid |
| INV-2026-006 | Customer 6 | 90 days ago | 97,750 | Paid |
| INV-2026-007 | Customer 7 | 75 days ago | 48,250 | Paid |
| INV-2026-008 | Customer 8 | 60 days ago | 156,000 | Paid |
| INV-2026-009 | Customer 1 | 55 days ago | 77,625 | Partially Paid |
| INV-2026-010 | Customer 2 | 50 days ago | 105,800 | Posted |
| INV-2026-011 | Customer 3 | 35 days ago | 34,000 | Paid |
| INV-2026-012 | Customer 4 | 25 days ago | 146,050 | Posted |
| INV-2026-013 | Customer 5 | 20 days ago | 55,200 | Posted |
| INV-2026-014 | Customer 6 | 15 days ago | 215,000 | Posted |
| INV-2026-015 | Customer 7 | 10 days ago | 89,700 | Posted |
| INV-2026-016 | Customer 8 | 95 days ago | 109,250 | Overdue |
| INV-2026-017 | Customer 9 | 120 days ago | 166,750 | Overdue |
| INV-2026-018 | Customer 10 | 85 days ago | 55,000 | Overdue |

**Status Breakdown**:
- Paid: 8 invoices
- Partially Paid: 1 invoice
- Posted (Outstanding): 6 invoices
- Overdue: 3 invoices

---

### 2.10 AR Receipts (10 Receipts)

| Receipt | Customer | Date | Amount | Payment Method |
|---------|----------|------|--------|----------------|
| RCT-2026-001 | Customer 1 | 40 days ago | 57,500 | Bank Transfer |
| RCT-2026-002 | Customer 2 | 25 days ago | 34,500 | Check |
| RCT-2026-003 | Customer 3 | 15 days ago | 86,750 | Bank Transfer |
| RCT-2026-004 | Customer 4 | 10 days ago | 50,000 | Cash |
| RCT-2026-005 | Customer 5 | 5 days ago | 46,000 | Bank Transfer |
| RCT-2026-006 | Customer 6 | 80 days ago | 99,250 | Bank Transfer |
| RCT-2026-007 | Customer 7 | 20 days ago | 48,250 | Check |
| RCT-2026-008 | Customer 8 | 12 days ago | 92,000 | Bank Transfer |
| RCT-2026-009 | Customer 1 | 3 days ago | 35,000 | Bank Transfer |
| RCT-2026-010 | Customer 2 | 1 day ago | 15,000 | Cash |

---

### 2.11 AP Bills (18 Bills)

| Bill | Supplier | Date | Amount | Status |
|------|----------|------|--------|--------|
| BILL-2026-001 | Supplier 1 | 40 days ago | 28,750 | Paid |
| BILL-2026-002 | Supplier 2 | 35 days ago | 34,500 | Paid |
| BILL-2026-003 | Supplier 3 | 25 days ago | 57,500 | Paid |
| BILL-2026-004 | Supplier 4 | 20 days ago | 40,250 | Paid |
| BILL-2026-005 | Supplier 5 | 15 days ago | 17,250 | Paid |
| BILL-2026-006 | Supplier 6 | 85 days ago | 5,175 | Paid |
| BILL-2026-007 | Supplier 7 | 70 days ago | 5,980 | Paid |
| BILL-2026-008 | Supplier 8 | 55 days ago | 5,520 | Partially Paid |
| BILL-2026-009 | Supplier 1 | 45 days ago | 75,000 | Paid |
| BILL-2026-010 | Supplier 1 | 15 days ago | 75,000 | Posted |
| BILL-2026-011 | Supplier 9 | 60 days ago | 143,750 | Paid |
| BILL-2026-012 | Supplier 10 | 40 days ago | 97,750 | Posted |
| BILL-2026-013 | Supplier 6 | 30 days ago | 77,050 | Posted |
| BILL-2026-014 | Supplier 7 | 50 days ago | 28,750 | Partially Paid |
| BILL-2026-015 | Supplier 8 | 25 days ago | 20,700 | Posted |
| BILL-2026-016 | Supplier 9 | 95 days ago | 109,250 | Overdue |
| BILL-2026-017 | Supplier 10 | 120 days ago | 166,750 | Overdue |
| BILL-2026-018 | Supplier 1 | 35 days ago | 17,250 | Posted |

**Status Breakdown**:
- Paid: 8 bills
- Partially Paid: 2 bills
- Posted (Outstanding): 5 bills
- Overdue: 2 bills

---

### 2.12 AP Payments (10 Payments)

| Payment | Supplier | Date | Amount | Payment Method |
|---------|----------|------|--------|----------------|
| PMT-2026-001 | Supplier 1 | 35 days ago | 28,750 | Bank Transfer |
| PMT-2026-002 | Supplier 2 | 30 days ago | 34,500 | Check |
| PMT-2026-003 | Supplier 3 | 20 days ago | 57,500 | Bank Transfer |
| PMT-2026-004 | Supplier 4 | 15 days ago | 40,250 | Bank Transfer |
| PMT-2026-005 | Supplier 5 | 10 days ago | 17,250 | Cash |
| PMT-2026-006 | Supplier 6 | 75 days ago | 51,750 | Bank Transfer |
| PMT-2026-007 | Supplier 7 | 25 days ago | 28,650 | Check |
| PMT-2026-008 | Supplier 8 | 18 days ago | 97,750 | Bank Transfer |
| PMT-2026-009 | Supplier 1 | 5 days ago | 25,000 | Bank Transfer |
| PMT-2026-010 | Supplier 2 | 2 days ago | 15,000 | Cash |

---

### 2.13 Fixed Assets (8 Assets)

| Code | Name | Acquisition | Cost (AED) | NBV (AED) | Status |
|------|------|------------|------------|------------|--------|
| AST-2024-001 | Dell XPS 15 Laptop | 365 days ago | 8,500 | 6,375 | Active |
| AST-2024-002 | HP LaserJet Printer | 320 days ago | 2,200 | 1,100 | Disposed |
| AST-2024-003 | Toyota Camry 2024 | 280 days ago | 125,000 | 100,000 | Active |
| AST-2024-004 | Office Furniture Set | 240 days ago | 35,000 | 29,167 | Active |
| AST-2024-005 | Server Rack System | 180 days ago | 45,000 | 36,000 | Active |
| AST-2025-001 | MacBook Pro 16" | 90 days ago | 12,000 | 10,000 | Active |
| AST-2025-002 | Conference Projector | 60 days ago | 7,500 | 6,500 | Active |
| AST-2026-001 | Forklift - Toyota | 15 days ago | 85,000 | 84,167 | Active |

**Total Cost**: AED 320,200
**Total NBV**: AED 273,309

---

### 2.14 Asset Transactions (6 Transactions)

| Transaction | Asset | Type | Date | Amount (AED) |
|-------------|-------|------|------|---------------|
| ATXN-2026-001 | AST-2024-001 | Acquisition | 365 days ago | 8,500 |
| ATXN-2026-002 | AST-2024-003 | Acquisition | 280 days ago | 125,000 |
| ATXN-2026-003 | AST-2024-005 | Acquisition | 180 days ago | 45,000 |
| ATXN-2026-004 | AST-2025-002 | Acquisition | 60 days ago | 7,500 |
| ATXN-2026-005 | AST-2024-002 | Disposal | 30 days ago | -1,700 (loss) |
| ATXN-2026-006 | AST-2024-004 | Transfer | 45 days ago | 0 |

---

### 2.15 Depreciation Runs (8 Runs)

| Run | Period | Date | Total (AED) | Assets |
|-----|--------|------|-------------|--------|
| DEP-2025-09 | Sep 2025 | 2025-09-30 | 7,500 | 5 |
| DEP-2025-10 | Oct 2025 | 2025-10-31 | 7,500 | 5 |
| DEP-2025-11 | Nov 2025 | 2025-11-30 | 7,500 | 5 |
| DEP-2025-12 | Dec 2025 | 2025-12-31 | 7,500 | 5 |
| DEP-2026-01 | Jan 2026 | 2026-01-31 | 8,500 | 6 |
| DEP-2026-02 | Feb 2026 | 2026-02-28 | 8,500 | 6 |
| DEP-2026-03 | Mar 2026 | 2026-03-31 | 8,500 | 6 |
| DEP-2026-04 | Apr 2026 | 2026-04-30 | 8,500 | 6 |

---

### 2.16 Budgets (4 Budgets)

| Budget | Name | FY 2026 | Status | Monthly Amount |
|--------|------|---------|--------|----------------|
| BUD-2026-001 | Operating Budget | 2026 | Approved | 30,000 |
| BUD-2026-002 | Marketing Budget | 2026 | Approved | 20,000 |
| BUD-2026-003 | IT Infrastructure | 2026 | Approved | 15,000 |
| BUD-2026-004 | HR Training | 2026 | Draft | 10,000 |

---

### 2.17 Tax Transactions (6 VAT Payments)

| VAT Payment | Period | Date | Amount (AED) |
|-------------|--------|------|--------------|
| VAT-2025-09 | Sep 2025 | 2025-10-20 | 45,000 |
| VAT-2025-10 | Oct 2025 | 2025-11-20 | 52,000 |
| VAT-2025-11 | Nov 2025 | 2025-12-20 | 48,000 |
| VAT-2025-12 | Dec 2025 | 2026-01-20 | 55,000 |
| VAT-2026-01 | Jan 2026 | 2026-02-20 | 62,000 |
| VAT-2026-02 | Feb 2026 | 2026-03-20 | 58,000 |

---

### 2.18 Bank Reconciliations (3 Sets)

| Reconciliation | Bank | Date | Status | Items | Matched |
|----------------|------|------|--------|-------|---------|
| RECON-2026-01 | Emirates NBD | Jan 31, 2026 | Completed | 20 | 20 |
| RECON-2026-02 | Emirates NBD | Feb 28, 2026 | Completed | 18 | 18 |
| RECON-2026-03 | Emirates NBD | Mar 31, 2026 | In Progress | 15 | 12 |

---

## 3. Sample Test Scenarios

### Scenario 1: Monthly Financial Close

**Objective**: Practice month-end close procedures

**Steps**:
1. Review Trial Balance for current period
2. Run AR Aging Report - follow up on overdue invoices
3. Run AP Aging Report - schedule payments
4. Verify bank reconciliation
5. Run depreciation
6. Review VAT liability
7. Lock period

**Expected Data**:
- 8 journal entries in current period
- 6 AR invoices (3 overdue)
- 5 AP bills (2 overdue)
- 1 bank reconciliation in progress

---

### Scenario 2: AR Collection Process

**Objective**: Practice collection procedures

**Steps**:
1. Run AR Aging Report
2. Identify overdue invoices (>30 days)
3. Contact customers (use sample contact info)
4. Record partial payments
5. Issue credit notes if needed
6. Update invoice status

**Overdue Invoices**:
- INV-2026-016: 95 days overdue - 109,250 AED
- INV-2026-017: 120 days overdue - 166,750 AED
- INV-2026-018: 85 days overdue - 55,000 AED

---

### Scenario 3: AP Payment Processing

**Objective**: Practice payment processing

**Steps**:
1. Run AP Aging Report
2. Select bills for payment (due or overdue)
3. Generate payment proposal
4. Obtain approvals per matrix
5. Process payments
6. Update bill status
7. Print checks if needed

**Overdue Bills**:
- BILL-2026-016: 95 days overdue - 109,250 AED
- BILL-2026-017: 120 days overdue - 166,750 AED

---

### Scenario 4: Fixed Asset Disposal

**Objective**: Practice asset disposal workflow

**Steps**:
1. View Fixed Asset Register
2. Select asset for disposal (HP Printer)
3. Record disposal transaction
4. Generate gain/loss journal entry
5. Update asset status
6. Report on disposal

**Sample Disposal**:
- Asset: HP LaserJet Printer (AST-2024-002)
- Original Cost: 2,200 AED
- Accumulated Depreciation: 1,100 AED
- Net Book Value: 1,100 AED
- Disposal Proceeds: 500 AED
- Loss on Disposal: 600 AED

---

### Scenario 5: Budget vs Actual Analysis

**Objective**: Practice budget monitoring

**Steps**:
1. Review budget allocations for FY 2026
2. Run Budget vs Actual Report
3. Analyze variances (>5%)
4. Investigate unfavorable variances
5. Prepare budget revision if needed

**Sample Variance Analysis**:
- Salaries: Budget 90,000 / Actual 87,500 = 2.8% Favorable
- Rent: Budget 25,000 / Actual 25,000 = 0% On Budget
- Utilities: Budget 15,000 / Actual 16,200 = -8% Unfavorable

---

### Scenario 6: Bank Reconciliation

**Objective**: Practice bank rec completion

**Steps**:
1. Open RECON-2026-03 (March 2026)
2. Review unmatched items
3. Investigate differences
4. Match or adjust items
5. Complete reconciliation
6. Obtain approval

**Outstanding Items**:
- 3 unmatched items totaling 15,000 AED
- Possible causes: timing differences, bank errors

---

## 4. Resetting Seed Data

### Option 1: Full Database Reset

```bash
# Delete the warehouse.db file
rm warehouse.db

# Run seed script
python seed_finance_data.py
```

### Option 2: Selective Reset

To reset only finance data, you can delete specific tables:

```sql
-- Delete in order due to foreign keys
DELETE FROM finance_reconciliation_items;
DELETE FROM finance_reconciliation_sets;
DELETE FROM finance_tax_transactions;
DELETE FROM finance_budget_actuals;
DELETE FROM finance_depreciation_entries;
DELETE FROM finance_depreciation_runs;
DELETE FROM finance_asset_transactions;
DELETE FROM finance_assets;
DELETE FROM finance_supplier_payment_lines;
DELETE FROM finance_supplier_payments;
DELETE FROM finance_customer_receipt_lines;
DELETE FROM finance_customer_receipts;
DELETE FROM finance_supplier_bill_lines;
DELETE FROM finance_supplier_bills;
DELETE FROM finance_customer_invoice_lines;
DELETE FROM finance_customer_invoices;
DELETE FROM finance_journal_lines;
DELETE FROM finance_journals;
DELETE FROM finance_budget_lines;
DELETE FROM finance_budgets;
DELETE FROM finance_bank_accounts;
DELETE FROM finance_profit_centers;
DELETE FROM finance_cost_centers;
DELETE FROM finance_tax_codes;
DELETE FROM finance_fiscal_periods;
DELETE FROM finance_fiscal_years;
DELETE FROM finance_accounts;
DELETE FROM finance_account_categories;

-- Run seed script
python seed_finance_data.py
```

### Option 3: Individual Table Reset

```python
import sqlite3
conn = sqlite3.connect('warehouse.db')
cursor = conn.cursor()

# Reset specific table
cursor.execute("DELETE FROM finance_customer_invoices")
conn.commit()
conn.close()

# Then run specific seed function
```

---

## 5. Adding Custom Seed Data

### Example: Adding a New Customer

```python
def add_sample_customer():
    cursor.execute("""
        INSERT INTO customers (code, name, email, phone, address, tax_id, credit_limit, payment_terms)
        VALUES ('CUST-NEW', 'New Customer LLC', 'contact@newcustomer.ae', '+971-4-123-4567', 
                'Dubai, UAE', 'TAX-REG-NEW', 100000, 'Net 30')
    """)
```

### Example: Adding a New Supplier

```python
def add_sample_supplier():
    cursor.execute("""
        INSERT INTO suppliers (code, name, email, phone, address, tax_id, payment_terms)
        VALUES ('SUPP-NEW', 'New Supplier Co', 'sales@newsupplier.ae', '+971-4-765-4321',
                'Abu Dhabi, UAE', 'TAX-REG-SUPP', 'Net 45')
    """)
```

---

## 6. Database Schema Reference

### Key Finance Tables

| Table | Description | Key Fields |
|-------|-------------|------------|
| finance_account_categories | Account classification | category_code, category_name |
| finance_accounts | Chart of accounts | code, name, account_type |
| finance_fiscal_years | Year definitions | name, start_date, end_date |
| finance_fiscal_periods | Period definitions | fiscal_year_id, name, status |
| finance_journals | Journal headers | journal_number, journal_type, status |
| finance_journal_lines | Journal detail | journal_id, account_id, debit, credit |
| finance_customer_invoices | AR invoices | invoice_number, customer_id, total |
| finance_customer_receipts | AR receipts | receipt_number, customer_id, amount |
| finance_supplier_bills | AP bills | bill_number, supplier_id, total |
| finance_supplier_payments | AP payments | payment_number, supplier_id, amount |
| finance_assets | Asset register | asset_code, asset_name, acquisition_cost |
| finance_depreciation_runs | Depreciation runs | run_number, run_date, total_depreciation |
| finance_budgets | Budget masters | budget_number, fiscal_year_id |
| finance_budget_lines | Budget detail | budget_id, account_id, period, amount |
| finance_bank_accounts | Bank accounts | bank_name, account_number, balance |

---

## 7. Useful Queries

### Current Period Balances

```sql
-- Trial Balance for Current Period
SELECT 
    fa.code,
    fa.name,
    SUM(fjl.debit) as total_debit,
    SUM(fjl.credit) as total_credit
FROM finance_journal_lines fjl
JOIN finance_accounts fa ON fjl.account_id = fa.id
JOIN finance_fiscal_periods ffp ON fjl.period_id = ffp.id
WHERE strftime('%Y', ffp.start_date) = '2026'
GROUP BY fa.code, fa.name
ORDER BY fa.code;
```

### AR Aging Summary

```sql
-- AR Aging by customer
SELECT 
    c.name,
    SUM(fci.amount_due) as total_due,
    CASE 
        WHEN fci.due_date < date('now', '-90 days') THEN '90+ Days'
        WHEN fci.due_date < date('now', '-60 days') THEN '61-90 Days'
        WHEN fci.due_date < date('now', '-30 days') THEN '31-60 Days'
        WHEN fci.due_date < date('now') THEN 'Current'
    END as age_bucket
FROM finance_customer_invoices fci
JOIN customers c ON fci.customer_id = c.id
WHERE fci.status != 'Paid'
GROUP BY c.name, age_bucket;
```

### VAT Liability

```sql
-- VAT Payable calculation
SELECT 
    SUM(CASE WHEN fci.tax_amount > 0 THEN fci.tax_amount ELSE 0 END) as output_vat,
    SUM(CASE WHEN fci.tax_amount > 0 THEN fci.tax_amount * 0.85 ELSE 0 END) as input_vat_recoverable,
    SUM(CASE WHEN fci.tax_amount > 0 THEN fci.tax_amount * 0.15 ELSE 0 END) as net_vat
FROM finance_customer_invoices fci
WHERE fci.status IN ('Posted', 'Partially Paid', 'Overdue');
```

---

## 8. Demo Users

| Username | Password | Role | Access |
|----------|----------|------|--------|
| admin | admin123 | Administrator | Full Access |
| cfo | cfo123 | CFO | Full Finance Access |
| controller | controller123 | Controller | All Accounting |
| ar_manager | armgr123 | AR Manager | AR Only |
| ap_manager | apmgr123 | AP Manager | AP Only |
| accountant | accountant123 | Accountant | Journal Entry |
| viewer | viewer123 | Viewer | Read Only |
