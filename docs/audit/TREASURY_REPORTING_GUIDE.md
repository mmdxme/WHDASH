# Treasury Reporting Guide

## Overview

The Treasury module provides comprehensive reporting and analytics capabilities for cash management, liquidity planning, and treasury operations.

## Available Reports

### 1. Cash Position Report
**Route:** `/finance/treasury/reports/cash-position`

**Description:** Provides a snapshot of the organization's total cash position across all bank accounts, petty cash, and cash boxes.

**Content:**
- Total cash position summary
- Bank account balances with details
- Petty cash account balances
- Cash box balances
- Breakdown by currency

**Filters:**
- Date range
- Currency
- Account type

**Use Case:** Daily cash visibility for treasury operations

---

### 2. Cash Flow Report
**Route:** `/finance/treasury/reports/cash-flow`

**Description:** Detailed analysis of expected cash inflows and outflows over a specified period.

**Content:**
- 30-day cash flow forecast
- 90-day cash flow forecast
- Daily/weekly/monthly aggregation
- Inflow vs outflow comparison

**Filters:**
- Period (7/30/90 days)
- Currency
- Account type

**Use Case:** Planning cash requirements and investment decisions

---

### 3. Collections Report
**Route:** `/finance/treasury/reports/collections`

**Description:** Analysis of expected cash collections from customers based on AR invoices.

**Content:**
- Total collections amount
- High-risk collections
- Collections by likelihood
- Aging analysis
- Customer-wise breakdown

**Filters:**
- Date range
- Risk level
- Likelihood
- Customer

**Use Case:** Managing incoming cash from receivables

---

### 4. Payments Report
**Route:** `/finance/treasury/reports/payments`

**Description:** Analysis of planned payments to suppliers based on AP bills.

**Content:**
- Total payments due
- Critical priority payments
- High priority payments
- Payment scheduling
- Supplier-wise breakdown

**Filters:**
- Date range
- Priority level
- Status
- Supplier

**Use Case:** Managing outgoing cash and supplier relationships

---

### 5. Liquidity Report
**Route:** `/finance/treasury/reports/liquidity`

**Description:** Comprehensive liquidity position analysis including thresholds and gaps.

**Content:**
- Current cash position
- Minimum required liquidity
- 7-day and 30-day projections
- Liquidity thresholds
- Gap analysis

**Filters:**
- Threshold type
- Urgency level

**Use Case:** Ensuring adequate liquidity buffers

---

### 6. Forecast vs Actual Report
**Route:** `/finance/treasury/reports/forecast-vs-actual`

**Description:** Comparison of forecasted cash flows against actual results.

**Content:**
- Variance analysis by period
- Inflow variance (volume and timing)
- Outflow variance
- Cumulative variance

**Filters:**
- Date range
- Forecast version
- Scenario

**Use Case:** Improving forecast accuracy

---

### 7. Treasury Alerts Report
**Route:** `/finance/treasury/reports/alerts`

**Description:** Historical record of all treasury alerts and their resolution.

**Content:**
- Alert history by type
- Severity distribution
- Resolution status
- Response time analysis

**Filters:**
- Date range
- Alert type
- Severity
- Resolution status

**Use Case:** Monitoring treasury risk events

---

### 8. Treasury Audit Report
**Route:** `/finance/treasury/reports/audit`

**Description:** Complete audit trail of all treasury operations.

**Content:**
- All treasury transactions
- User actions
- Before/after values
- Approval status changes

**Filters:**
- Date range
- Entity type
- User
- Action type

**Use Case:** Compliance and internal audit

---

## Dashboard Views

### Treasury Operations Dashboard
**Route:** `/finance/treasury/dashboard`

**KPIs:**
- Total cash position
- 7-day net cash flow
- 30-day projection
- Collections at risk
- Pending payments
- Pending approvals

**Charts:**
- 7-day cash flow forecast
- Currency distribution
- Liquidity status

---

### Executive Liquidity Dashboard
**Route:** `/finance/treasury/executive-dashboard`

**KPIs:**
- Total cash position
- 30-day net cash flow
- Collections at risk
- Liquidity health status

**Charts:**
- Currency breakdown
- 14-day forecast
- Collections vs Payments

---

## Report Features

### Common Features
- **Export:** Excel, PDF, CSV
- **Print:** Formatted for printing
- **Filter:** Multiple filter options
- **Date Range:** Flexible date selection
- **Sort:** Multiple sort options
- **Drill-down:** Navigate to detail views

### Multilingual Support
- All reports support 8 languages
- RTL layout support
- Localized date/number formats

---

## Using Reports in Workflows

### Daily Treasury Report Routine
1. Review Cash Position Report (morning)
2. Check Collections Report for expected receipts
3. Review Payments Report for due payments
4. Update liquidity if needed

### Weekly Treasury Review
1. Review Executive Dashboard (CFO)
2. Analyze Forecast vs Actual
3. Check Alerts Report
4. Review pending Approvals

### Monthly Treasury Close
1. Generate all reports for month
2. Audit Trail Report for compliance
3. Variance analysis
4. Forecast accuracy assessment

---

## Best Practices

1. **Daily Reviews:** Cash position and alerts
2. **Weekly Analysis:** Forecast accuracy, collections
3. **Monthly Assessment:** Full treasury reporting
4. **Quarterly Review:** Strategy and forecast assumptions

---

## Report Access

Access reports via:
- Treasury menu → Reports
- Executive Dashboard → Report links
- Direct URL navigation
- API endpoints for integration
