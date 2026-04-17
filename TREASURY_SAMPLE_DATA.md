# Treasury Sample Data

## Overview

The Treasury module includes a comprehensive sample data generator to demonstrate functionality with realistic enterprise scenarios.

## Sample Data Generator

**Function:** `generate_sample_treasury_data(company_id)`

### Sample Bank Accounts

| Bank | Account | Number | Currency | Balance |
|------|---------|--------|----------|---------|
| Emirates NBD | Main Operating | 0521-7845-3021 | AED | 2,450,000 |
| Emirates NBD | Payroll | 0521-7845-3022 | AED | 450,000 |
| Abu Dhabi Commercial Bank | Main Operating | 0712-3456-7890 | AED | 1,820,000 |
| Standard Chartered | USD Operations | 0891-2345-6789 | USD | 890,000 |
| HSBC | EUR Account | 0456-7890-1234 | EUR | 340,000 |
| First Abu Dhabi Bank | Reserve | 0345-6789-0123 | AED | 5,000,000 |

### Sample Petty Cash Accounts

| Code | Name | Location | Float | Balance |
|------|------|----------|-------|---------|
| PC-001 | Main Office Petty Cash | Main Office | 5,000 | 3,850 |
| PC-002 | Warehouse Petty Cash | Warehouse | 2,000 | 1,540 |
| PC-003 | Branch Petty Cash | Dubai Branch | 3,000 | 2,750 |

### Sample Cash Boxes

| Code | Name | Location | Balance |
|------|------|----------|---------|
| CB-001 | Main Reception | Main Reception | 850 |
| CB-002 | Cafeteria | Cafeteria | 320 |

### Sample Treasury Alerts

| Type | Severity | Title | Amount |
|------|----------|-------|--------|
| low_balance | high | Low Balance Alert - Payroll Account | 450,000 AED |
| large_outflow | medium | Large Outflow Detected | 750,000 AED |
| overdue_collection | high | Overdue Collection Alert | 125,000 AED |
| reconciliation | medium | Reconciliation Gap | 15,420 AED |

### Sample Treasury Controls

| Control | Type | Threshold | Severity |
|---------|------|----------|----------|
| high_value_transfer | transfer_limit | >= 500,000 | high |
| petty_cash_limit | transaction_limit | > 1,000 | medium |
| minimum_cash_balance | balance_threshold | < 500,000 | critical |

### Sample Liquidity Thresholds

| Name | Type | Value | Currency | Urgency |
|------|------|-------|----------|---------|
| Minimum AED Operating Balance | minimum_balance | 500,000 | AED | critical |
| Warning AED Balance | minimum_balance | 1,000,000 | AED | high |
| Minimum USD Balance | minimum_balance | 100,000 | USD | high |

## Sample Collections (AR Sync)

### Expected Receipts

| Customer | Invoice | Due Date | Amount | Risk |
|----------|---------|----------|--------|------|
| Al Mahara Restaurant | INV-2026-0045 | 2026-04-20 | 125,000 | normal |
| Grand Hotel LLC | INV-2026-0051 | 2026-04-22 | 89,000 | normal |
| Beach Resort | INV-2026-0048 | 2026-04-25 | 67,000 | medium |
| City Restaurant | INV-2026-0055 | 2026-04-28 | 45,000 | normal |
| Marina Mall | INV-2026-0058 | 2026-04-30 | 38,000 | high |

## Sample Payments (AP Sync)

### Due Payments

| Supplier | Bill | Due Date | Amount | Priority |
|----------|------|----------|--------|----------|
| Steel Works LLC | BILL-2026-0125 | 2026-04-20 | 156,000 | critical |
| Aluminum Supplies Co | BILL-2026-0132 | 2026-04-22 | 98,000 | high |
| Gulf Electronics | BILL-2026-0138 | 2026-04-25 | 75,000 | normal |
| Premium Packaging | BILL-2026-0141 | 2026-04-28 | 52,000 | normal |
| Office Supplies Inc | BILL-2026-0145 | 2026-04-30 | 38,000 | normal |

## Sample Transfers

### Recent Transfers

| Number | Date | From | To | Amount | Status |
|--------|------|------|----|--------|--------|
| TRF-2026-00001 | 2026-04-10 | Emirates NBD | ADCB | 500,000 | Completed |
| TRF-2026-00002 | 2026-04-12 | FAB | Emirates NBD | 1,200,000 | Completed |
| TRF-2026-00003 | 2026-04-14 | Emirates NBD | Petty Cash | 5,000 | Completed |

## Sample Petty Cash Movements

### Movement Types
- `top_up` - Replenishment
- `withdrawal` - Payment
- `transfer_in` - Internal transfer
- `transfer_out` - Internal transfer
- `adjustment` - Count adjustment

## Sample Cash Forecast Data

### 7-Day Forecast Pattern

| Day | Expected Inflow | Expected Outflow | Net |
|-----|-----------------|------------------|-----|
| Day 1 | 150,000 | 80,000 | +70,000 |
| Day 2 | 200,000 | 120,000 | +80,000 |
| Day 3 | 50,000 | 90,000 | -40,000 |
| Day 4 | 180,000 | 60,000 | +120,000 |
| Day 5 | 100,000 | 150,000 | -50,000 |
| Day 6 | 0 | 30,000 | -30,000 |
| Day 7 | 220,000 | 100,000 | +120,000 |

## Usage

### Generate Sample Data
```python
from treasury_models import generate_sample_treasury_data

# Generate for company 1
generate_sample_treasury_data(company_id=1)
```

### Reset Sample Data
Delete and regenerate the treasury tables.

## Notes

- Sample data is for demonstration only
- Amounts are realistic but fictional
- Data can be modified for testing
- Use in development/demo environments
