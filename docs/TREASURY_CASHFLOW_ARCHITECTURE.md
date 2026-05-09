# Treasury / Cash Flow Architecture

## Overview

The Treasury / Cash Flow module in WHDASH is an enterprise-grade treasury management system that provides comprehensive cash position management, liquidity planning, forecasting, and treasury controls.

## Architecture Components

### 1. Models Layer (`treasury_models.py`)

#### Core Tables
- `treasury_settings` - Treasury configuration
- `treasury_cash_position_snapshots` - Historical cash position tracking
- `treasury_petty_cash_accounts` - Petty cash management
- `treasury_cash_boxes` - Cash box tracking
- `treasury_cash_movements` - Movement transactions
- `treasury_forecasts` - Cash flow forecast headers
- `treasury_forecast_scenarios` - Scenario variants
- `treasury_forecast_items` - Individual forecast line items
- `treasury_liquidity_plans` - Liquidity planning
- `treasury_liquidity_thresholds` - Alert thresholds
- `treasury_collections` - AR-Treasury sync
- `treasury_payments_plan` - AP-Treasury sync
- `treasury_transfer_requests` - Transfer workflow
- `treasury_transfer_approvals` - Multi-level approvals
- `treasury_controls` - Control definitions
- `treasury_alerts` - Alert queue
- `treasury_audit_log` - Full audit trail
- `treasury_bank_signatories` - Authorized signatories
- `treasury_account_groups` - Bank account grouping
- `treasury_workflow_rules` - Approval matrices
- `treasury_reconciliation_rules` - Matching rules

### 2. Routes Layer (`treasury_routes.py`)

#### Blueprint
- `treasury_bp = Blueprint('treasury', __name__, url_prefix='/finance/treasury')`

#### Main Routes
| Route | Function |
|-------|----------|
| `/dashboard` | Main treasury dashboard |
| `/executive-dashboard` | CFO-level liquidity view |
| `/cash-position` | Cash position overview |
| `/cash-position/by-currency` | Currency breakdown |
| `/cash-position/by-bank` | Bank breakdown |
| `/cash-position/historical` | Historical snapshots |
| `/forecast` | Cash flow forecast main |
| `/forecast/7-day` | 7-day forecast |
| `/forecast/30-day` | 30-day forecast |
| `/forecast/90-day` | 90-day forecast |
| `/forecast/vs-actual` | Variance analysis |
| `/collections` | Collections planning |
| `/collections/calendar` | Collection calendar |
| `/collections/overdue` | Overdue items |
| `/payments` | Payments planning |
| `/payments/calendar` | Payment calendar |
| `/payments/cash-requirement` | Funding analysis |
| `/transfers` | Transfer requests list |
| `/transfers/create` | New transfer |
| `/transfers/<id>` | Transfer detail |
| `/reconciliation` | Bank reconciliation |
| `/controls` | Treasury controls |
| `/alerts` | Alert management |
| `/liquidity` | Liquidity planning |
| `/liquidity/gaps` | Gap analysis |
| `/reports` | Report menu |
| `/approvals` | Pending approvals |
| `/audit-log` | Audit trail |
| `/settings` | Module settings |

### 3. Templates Layer (`templates/finance/treasury/`)

#### Dashboard Templates
- `dashboard.html` - Operations dashboard
- `executive_dashboard.html` - CFO view

#### Cash Position Templates
- `cash_position.html` - Main cash position
- `cash_position_by_currency.html` - Currency view
- `cash_position_by_bank.html` - Bank view
- `cash_position_historical.html` - Historical

#### Forecast Templates
- `cash_flow_forecast.html` - Main forecast
- `forecast_7day.html` - Short-term
- `forecast_30day.html` - Medium-term
- `forecast_90day.html` - Long-term
- `forecast_detail.html` - Forecast detail
- `forecast_create.html` - New forecast
- `forecast_vs_actual.html` - Variance

#### Collections Templates
- `collections.html` - Main collections
- `collections_calendar.html` - Calendar view
- `collections_overdue.html` - Overdue items

#### Payments Templates
- `payments.html` - Main payments
- `payments_calendar.html` - Calendar view
- `payments_cash_requirement.html` - Funding needs

#### Petty Cash Templates
- `petty_cash_list.html` - Account list
- `petty_cash_view.html` - Account detail
- `petty_cash_create.html` - Create account
- `petty_cash_edit.html` - Edit account

#### Cash Box Templates
- `cash_boxes_list.html` - List
- `cash_box_view.html` - Detail
- `cash_box_create.html` - Create

#### Transfer Templates
- `transfers_list.html` - Request list
- `transfer_detail.html` - Request detail
- `transfer_create.html` - New request

#### Reconciliation Templates
- `reconciliation.html` - Workspace
- `reconciliation_detail.html` - Account detail

#### Controls & Alerts
- `controls.html` - Control management
- `control_create.html` - New control
- `alerts.html` - Alert management

#### Liquidity Templates
- `liquidity.html` - Main liquidity
- `liquidity_gaps.html` - Gap analysis

#### Reports
- `reports.html` - Report menu
- `reports/*.html` - Individual reports

#### Settings & Workflow
- `approvals.html` - Pending items
- `audit_log.html` - Audit trail
- `settings.html` - Configuration

## Data Flow

### Cash Position Calculation
```
1. Bank Account Balances (from GL)
   ↓
2. Petty Cash Account Balances
   ↓
3. Cash Box Balances
   ↓
4. Aggregate by Currency
   ↓
5. Calculate Total Position
   ↓
6. Create Snapshot
```

### Forecast Calculation
```
1. Current Cash Position
   ↓
2. Expected Inflows (AR invoices due)
   ↓
3. Expected Outflows (AP bills due)
   ↓
4. Apply Scenario Multipliers
   ↓
5. Calculate Daily Projections
   ↓
6. Aggregate Weekly/Monthly
```

### Collections Sync (AR → Treasury)
```
1. Get Posted Invoices (AR)
   ↓
2. Calculate Open Amount
   ↓
3. Map to Treasury Collections
   ↓
4. Set Likelihood & Risk
   ↓
5. Update Collections Plan
```

## Integration Points

### Finance Module
- Bank accounts from `finance_bank_accounts`
- GL accounts from `finance_accounts`
- Customer invoices from `finance_customer_invoices`
- Supplier bills from `finance_supplier_bills`
- Journal entries for transfers

### Flow Module
- Alert creation via `create_treasury_alert()`
- Flow notification integration
- Approval workflow triggers

### Permissions
- Treasury-specific roles
- Granular resource permissions
- Branch/entity scoping

## Security Model

### Access Control
- Module-level: `finance.treasury`
- Resource-level: `cash_position`, `forecast`, `collections`, etc.
- Action-level: `view`, `manage`, `approve`, etc.

### Audit Trail
- All state changes logged
- Before/after values
- User, timestamp, IP tracking
- Immutable audit records

## Multilingual Support

### Languages
- English (en)
- Persian (fa)
- Arabic (ar)
- Russian (ru)
- Hindi (hi)
- Spanish (es)
- Chinese (zh)
- German (de)

### Translation File
- `treasury_translations.py` - All treasury-specific terminology
- RTL support for Arabic/Persian
- Safe rendering of mixed scripts

## Future Enhancements
- Real-time bank feed integration
- Automated clearing (ACH)
- FX hedging recommendations
- Counterparty risk scoring
- Treasury workstation integration
- SWIFT message support
