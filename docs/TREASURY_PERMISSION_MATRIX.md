# Treasury Permission Matrix

## Overview

The Treasury module implements a comprehensive Role-Based Access Control (RBAC) system that provides granular permissions at the module, menu, page, and action levels.

## Permission Structure

### Finance Module Permissions

```python
'finance': {
    'label': 'Finance & Accounting',
    'resources': {
        # Existing Finance Permissions
        'dashboard': ['view'],
        'accounts': ['view', 'create', 'edit', 'delete'],
        'journals': ['view', 'create', 'edit', 'delete', 'post', 'reverse'],
        'fiscal_years': ['view', 'create', 'edit', 'close', 'reopen'],
        'ar_invoices': ['view', 'create', 'edit', 'delete', 'post'],
        'ar_receipts': ['view', 'create', 'edit', 'delete', 'post'],
        'ap_bills': ['view', 'create', 'edit', 'delete', 'post'],
        'ap_payments': ['view', 'create', 'edit', 'delete', 'post'],
        'bank_accounts': ['view', 'create', 'edit', 'delete'],
        'transfers': ['view', 'create', 'edit', 'delete'],
        'reconciliation': ['view', 'create', 'edit'],
        'treasury': ['view', 'manage'],
        ...
        
        # Treasury Sub-Permissions (NEW)
        'treasury_dashboard': ['view'],
        'cash_position': ['view', 'manage'],
        'cash_forecast': ['view', 'create', 'edit', 'approve'],
        'collections': ['view', 'manage', 'sync'],
        'payments': ['view', 'manage', 'sync'],
        'transfers': ['view', 'create', 'edit', 'approve', 'reject'],
        'petty_cash': ['view', 'create', 'edit', 'top_up', 'withdraw'],
        'cash_boxes': ['view', 'create', 'edit'],
        'liquidity': ['view', 'manage'],
        'treasury_controls': ['view', 'create', 'edit', 'manage'],
        'treasury_alerts': ['view', 'resolve', 'manage'],
        'treasury_reports': ['view', 'export'],
        'treasury_settings': ['view', 'edit', 'manage'],
        'treasury_audit': ['view', 'export'],
    }
}
```

## Role Definitions

### Treasury-Specific Roles

| Role | Description | Permissions |
|------|-------------|------------|
| **Global Admin** | Full system access | All treasury permissions |
| **Finance Admin** | Finance department head | `treasury: manage`, all sub-permissions |
| **CFO** | Chief Financial Officer | `treasury_dashboard: view`, `treasury_reports: view, export`, `treasury_settings: view` |
| **Treasury Manager** | Treasury department head | `treasury: view, manage`, all sub-permissions |
| **Treasury Analyst** | Treasury operations | `treasury_dashboard: view`, `cash_position: view`, `cash_forecast: view`, `collections: view`, `payments: view`, `treasury_reports: view` |
| **Treasury Controller** | Treasury controls | `treasury_controls: view, manage`, `treasury_alerts: view, resolve`, `treasury_audit: view, export` |
| **Branch Treasury Officer** | Branch cash operations | `cash_position: view`, `petty_cash: view, top_up, withdraw`, `cash_boxes: view`, limited `transfers` |
| **Entity Treasury Manager** | Multi-entity treasury | Entity-scoped `treasury: view, manage`, all entity-level permissions |
| **Collections Viewer** | Collections monitoring | `collections: view`, `treasury_reports: view` |
| **Payments Planner** | Payment scheduling | `payments: view, manage`, `transfers: view` |
| **Reconciliation Officer** | Daily reconciliation | `reconciliation: view, create, edit`, `treasury_reports: view` |
| **Reconciliation Reviewer** | Reconciliation approval | Above + approval permissions |
| **Auditor** | Audit access | `treasury_audit: view, export`, read-only across treasury |
| **Read-only Executive Viewer** | Management reporting | `treasury_dashboard: view`, `treasury_reports: view` |

## Permission Details

### Cash Position Permissions

| Action | Description | Allowed Roles |
|--------|-------------|---------------|
| `view` | View cash position | All treasury roles |
| `manage` | Modify cash settings | Treasury Manager, Finance Admin, Global Admin |

### Cash Forecast Permissions

| Action | Description | Allowed Roles |
|--------|-------------|---------------|
| `view` | View forecasts | Treasury Analyst+, CFO, Executive Viewer |
| `create` | Create new forecast | Treasury Analyst, Treasury Manager |
| `edit` | Modify draft forecast | Treasury Analyst, Treasury Manager |
| `approve` | Approve forecast | Treasury Manager, CFO |

### Collections Permissions

| Action | Description | Allowed Roles |
|--------|-------------|---------------|
| `view` | View collections | Collections Viewer+, Treasury roles |
| `manage` | Modify collections | Treasury Manager, Finance Admin |
| `sync` | Sync from AR | Treasury Analyst, Treasury Manager |

### Payments Permissions

| Action | Description | Allowed Roles |
|--------|-------------|---------------|
| `view` | View payments | Payments Planner+, Treasury roles |
| `manage` | Modify payments | Treasury Manager, Finance Admin |
| `sync` | Sync from AP | Treasury Analyst, Treasury Manager |

### Transfer Permissions

| Action | Description | Allowed Roles |
|--------|-------------|---------------|
| `view` | View transfers | All treasury roles |
| `create` | Create transfer request | Treasury Analyst+ |
| `edit` | Edit draft transfers | Creator, Treasury Manager |
| `approve` | Approve transfers | Treasury Manager, Branch Treasury Officer (within limit) |
| `reject` | Reject transfers | Treasury Manager, Branch Treasury Officer |

### Petty Cash Permissions

| Action | Description | Allowed Roles |
|--------|-------------|---------------|
| `view` | View petty cash | Branch Treasury Officer+ |
| `create` | Create accounts | Treasury Manager |
| `edit` | Edit accounts | Treasury Manager |
| `top_up` | Top up accounts | Branch Treasury Officer, Treasury Manager |
| `withdraw` | Withdraw from accounts | Branch Treasury Officer, Treasury Manager |

### Treasury Controls Permissions

| Action | Description | Allowed Roles |
|--------|-------------|---------------|
| `view` | View controls | Treasury Controller+ |
| `create` | Create controls | Treasury Manager, Finance Admin |
| `edit` | Modify controls | Treasury Manager |
| `manage` | Full control management | Finance Admin |

### Alert Permissions

| Action | Description | Allowed Roles |
|--------|-------------|---------------|
| `view` | View alerts | Treasury Controller+ |
| `resolve` | Resolve alerts | Treasury Controller, Treasury Manager |
| `manage` | Alert administration | Finance Admin |

## Data Scope Restrictions

### Branch-Level Restrictions
- Branch Treasury Officers only see their branch
- Treasury Manager can see all branches (configurable)

### Entity-Level Restrictions
- Entity Treasury Managers only see their entity
- Global roles see all entities

### Currency Restrictions
- Configurable by role
- Some roles see only local currency
- Global roles see multi-currency

## Implementation

### Permission Check Flow
```
1. User requests treasury action
   ↓
2. Check module permission (finance.treasury)
   ↓
3. Check resource permission (e.g., cash_position)
   ↓
4. Check action permission (e.g., view, manage)
   ↓
5. Check scope (branch/entity if applicable)
   ↓
6. Log to audit trail
   ↓
7. Allow or deny
```

### Permission Decorator Usage
```python
@treasury_bp.route('/cash-position')
@require_permission('finance', 'cash_position', 'view')
def cash_position():
    ...

@treasury_bp.route('/petty-cash/<id>/top-up', methods=['POST'])
@require_permission('finance', 'petty_cash', 'top_up')
def petty_cash_topup(account_id):
    ...
```

## Audit Logging

All permission-challenged actions are logged:
- User ID
- Action performed
- Resource affected
- Old/New values
- Timestamp
- IP address

## Future Enhancements
- Dynamic permission rules based on amount thresholds
- Delegation workflows
- SoD (Segregation of Duties) conflict detection
- Risk-based access scoring
