# Treasury Audit and Controls

## Overview

The Treasury module implements comprehensive audit logging and control mechanisms to ensure financial integrity and regulatory compliance.

## Audit Trail

### Treasury Audit Log Table

```sql
CREATE TABLE treasury_audit_log (
    id INTEGER PRIMARY KEY,
    audit_number TEXT UNIQUE,        -- AUD-2026-00001
    action TEXT,                      -- CREATE, UPDATE, DELETE, APPROVE, REJECT
    entity_type TEXT,                 -- petty_cash_account, transfer_request, etc.
    entity_id INTEGER,
    entity_name TEXT,
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,
    change_reason TEXT,
    ip_address TEXT,
    user_agent TEXT,
    user_id INTEGER,
    user_name TEXT,
    user_role TEXT,
    company_id INTEGER,
    branch_id INTEGER,
    entity_id INTEGER,
    created_at TIMESTAMP
);
```

### Audited Operations

| Operation | Actions Logged |
|-----------|----------------|
| Bank Account Changes | Create, Update, Delete, Status Change |
| Petty Cash | Create, Top Up, Withdraw, Adjust |
| Cash Boxes | Create, Movement, Count Adjustment |
| Transfers | Create, Approve, Reject, Execute |
| Forecasts | Create, Update, Approve |
| Controls | Create, Update, Delete, Activate/Deactivate |
| Alerts | Create, Read, Resolve |
| Settings | Any Change |

### Audit Log Fields

| Field | Description |
|-------|-------------|
| audit_number | Unique sequential identifier |
| action | Type of operation |
| entity_type | What was affected |
| entity_id | ID of affected record |
| entity_name | Name/description of affected |
| field_name | Specific field changed |
| old_value | Previous value |
| new_value | New value |
| change_reason | User-provided reason |
| user_id | Who performed action |
| user_name | Display name |
| user_role | Role at time of action |
| timestamp | When it happened |
| IP address | Source of request |

## Treasury Controls

### Control Types

#### 1. Transfer Limits
```json
{
    "control_name": "high_value_transfer",
    "control_type": "transfer_limit",
    "threshold_value": 500000,
    "threshold_operator": "greater_equal",
    "affected_operations": "bank_transfer",
    "severity": "high"
}
```

**Behavior:** Transfers above threshold require additional approval

#### 2. Transaction Limits
```json
{
    "control_name": "petty_cash_limit",
    "control_type": "transaction_limit",
    "threshold_value": 1000,
    "threshold_operator": "greater_than",
    "affected_operations": "petty_cash_withdrawal",
    "severity": "medium"
}
```

**Behavior:** Single transactions above limit blocked

#### 3. Balance Thresholds
```json
{
    "control_name": "minimum_cash_balance",
    "control_type": "balance_threshold",
    "threshold_value": 500000,
    "threshold_operator": "less_than",
    "affected_operations": "all",
    "severity": "critical"
}
```

**Behavior:** Alerts when cash falls below minimum

### Control Categories

| Category | Description |
|----------|-------------|
| approval | Approval workflow controls |
| petty_cash | Petty cash operation limits |
| liquidity | Liquidity threshold controls |
| reconciliation | Reconciliation controls |

### Severity Levels

| Level | Color | Description |
|-------|-------|-------------|
| critical | Red | Immediate action required |
| high | Orange | Requires attention within 24h |
| medium | Blue | Routine monitoring |
| low | Green | Informational |

## Dual Control

### Dual Authorization Rules

- High-value transfers require two authorized signers
- Petty cash above threshold requires manager approval
- Bank account modifications require dual approval
- Reconciliation adjustments need reviewer approval

### Signatory Management

```sql
CREATE TABLE treasury_bank_signatories (
    id INTEGER PRIMARY KEY,
    bank_account_id INTEGER,
    signatory_name TEXT,
    signatory_title TEXT,
    authorization_limit REAL,
    requires_dual_signature INTEGER,
    is_active INTEGER
);
```

## Alert System

### Alert Types

| Type | Category | Description |
|------|----------|-------------|
| low_balance | liquidity | Account balance below threshold |
| large_outflow | cash_flow | Unusual payment detected |
| overdue_collection | collections | AR invoice overdue |
| reconciliation | reconciliation | Bank-book mismatch |
| threshold_breach | control | Control threshold exceeded |

### Alert Lifecycle

```
Created → Unread → Read → Resolved
   ↓
Escalation (if critical and unresolved)
```

### Alert Severity Actions

| Severity | Notification | Auto-Action |
|----------|--------------|-------------|
| critical | Immediate Flow push + Email | Flag for review |
| high | Flow notification | None |
| medium | In-app only | None |
| low | In-app only | None |

## Workflow Rules

### Approval Routing

```sql
CREATE TABLE treasury_workflow_rules (
    id INTEGER PRIMARY KEY,
    rule_name TEXT,
    operation_type TEXT,
    approval_levels INTEGER,
    level_1_approver_role TEXT,
    level_1_min_amount REAL,
    level_1_max_amount REAL,
    level_2_approver_role TEXT,
    escalation_days INTEGER
);
```

### Approval Levels

1. **Level 1:** Direct manager (amount < threshold)
2. **Level 2:** Treasury Manager (amount >= threshold)
3. **Escalation:** Auto-escalate after SLA days

## Compliance Features

### Segregation of Duties

| Role | Can Create | Can Approve | Can View |
|------|------------|--------------|----------|
| Treasury Analyst | Yes | No | Yes |
| Branch Treasury Officer | Yes (own branch) | No | Branch only |
| Treasury Manager | Yes | Yes | All |
| Treasury Controller | No | Yes | All |
| Auditor | No | No | Yes (read-only) |

### Audit Retention

- Audit logs retained for 7 years (configurable)
- Archived to cold storage after 1 year
- Immutable - no deletions allowed

### Key Controls Checklist

- [ ] All transfers have dual authorization above threshold
- [ ] Petty cash counts performed weekly
- [ ] Bank reconciliations completed within 3 days
- [ ] Liquidity thresholds reviewed monthly
- [ ] Alert resolution tracked weekly
- [ ] Control effectiveness reviewed quarterly

## Reporting

### Control Effectiveness Report
- Controls triggered vs. actual issues
- False positive rates
- Average resolution time

### Audit Summary Report
- Activity by user
- Activity by entity type
- Changes to sensitive fields
- Failed access attempts

## Best Practices

1. **Daily:** Review critical alerts
2. **Weekly:** Audit log review, reconciliation status
3. **Monthly:** Control effectiveness assessment
4. **Quarterly:** Full control review, policy updates
5. **Annually:** External audit preparation

## Integration with Flow

- Critical alerts push to Flow immediately
- Approval requests create Flow tasks
- Escalation notifications via Flow
- Audit summaries scheduled via Flow
