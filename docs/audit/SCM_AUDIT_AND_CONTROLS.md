# SCM Audit and Controls

## Overview

The SCM module implements comprehensive audit trails and controls to ensure compliance, traceability, and governance of supply chain planning activities.

## Audit Trail

### Tracked Activities

#### Forecast Management
```python
AUDITED_ACTIONS = {
    'FORECAST_GENERATED': {
        'entity': 'forecast_run',
        'fields': ['method', 'horizon_days', 'total_items'],
        'user_required': True
    },
    'FORECAST_APPROVED': {
        'entity': 'forecast_run',
        'fields': ['status', 'approved_by', 'approved_at'],
        'user_required': True,
        'approval_required': True
    },
    'FORECAST_OVERRIDE': {
        'entity': 'forecast_line',
        'fields': ['override_quantity', 'override_reason'],
        'before_after': True,
        'user_required': True
    }
}
```

#### Replenishment
```python
AUDITED_ACTIONS = {
    'REPLENISHMENT_GENERATED': {
        'entity': 'batch',
        'fields': ['item_count', 'total_quantity'],
        'user_required': True
    },
    'REPLENISHMENT_APPROVED': {
        'entity': 'replenishment_rec',
        'fields': ['status', 'approved_by'],
        'user_required': True,
        'approval_required': True
    },
    'REPLENISHMENT_DISMISSED': {
        'entity': 'replenishment_rec',
        'fields': ['status', 'reviewed_by'],
        'user_required': True
    },
    'REPLENISHMENT_EXECUTED': {
        'entity': 'replenishment_rec',
        'fields': ['execution_details'],
        'user_required': True
    }
}
```

#### MRP Operations
```python
AUDITED_ACTIONS = {
    'MRP_RUN': {
        'entity': 'batch',
        'fields': ['horizon_days', 'items_processed'],
        'user_required': True
    },
    'PURCHASE_REC_APPROVED': {
        'entity': 'purchase_rec',
        'fields': ['status', 'approved_by'],
        'approval_required': True
    }
}
```

#### Inventory Changes
```python
AUDITED_ACTIONS = {
    'SAFETY_STOCK_UPDATED': {
        'entity': 'item',
        'fields': ['safety_stock_days'],
        'before_after': True,
        'approval_required': True
    },
    'OVERRIDE_APPLIED': {
        'entity': 'item',
        'fields': ['override_type', 'override_value'],
        'before_after': True,
        'reason_required': True
    }
}
```

## Control Framework

### Preventive Controls

#### 1. Access Control
- Role-based permissions enforced at module, page, and action level
- Branch-level data isolation for branch planners
- Approval thresholds requiring manager sign-off

#### 2. Approval Workflows
```python
APPROVAL_THRESHOLDS = {
    'forecast_override': {
        'threshold': 'any',
        'approver': 'demand_manager',
        'reason_required': True
    },
    'safety_stock_change': {
        'threshold': 'any',
        'approver': 'scm_admin',
        'reason_required': True
    },
    'replenishment_approve': {
        'threshold': 'value > 10000',
        'approver': 'supply_chain_manager',
        'reason_required': True
    },
    'purchase_suggestion': {
        'threshold': 'value > 50000',
        'approver': 'vp_supply_chain',
        'reason_required': True
    }
}
```

#### 3. Data Validation
- Forecast values must be non-negative
- Replenishment quantities must meet MOQ
- Safety stock cannot exceed max stock
- Lead times must be within defined range

### Detective Controls

#### 1. Alert Monitoring
- Automated alerts for stockout conditions
- Forecast deviation alerts
- Supplier delay notifications
- Coverage breach warnings

#### 2. Variance Analysis
- Forecast vs actual comparison
- Planned vs executed replenishment
- Budget vs actual cost tracking

#### 3. Compliance Reporting
- Monthly audit summary
- Approval cycle time metrics
- Override frequency analysis

## Control Activities

### Daily Controls

| Control | Description | Frequency |
|---------|-------------|-----------|
| Alert Review | Review critical alerts | Daily |
| Stockout Check | Verify stockout items | Daily |
| Forecast Monitor | Check forecast accuracy | Daily |

### Weekly Controls

| Control | Description | Frequency |
|---------|-------------|-----------|
| Replenishment Queue | Review pending recommendations | Weekly |
| MRP Exception Review | Analyze MRP exceptions | Weekly |
| Scenario Review | Validate active scenarios | Weekly |

### Monthly Controls

| Control | Description | Frequency |
|---------|-------------|-----------|
| Forecast Accuracy | Analyze forecast performance | Monthly |
| Service Level Review | Evaluate service metrics | Monthly |
| Inventory Audit | Physical vs system stock | Monthly |
| Scenario Comparison | Review scenario outcomes | Monthly |

## Segregation of Duties

### Role Definitions

| Role | Plan | Approve | Execute | View | Audit |
|------|------|---------|---------|------|-------|
| Demand Planner | ✓ | - | - | ✓ | - |
| Supply Planner | ✓ | ✓ | - | ✓ | - |
| Replenishment Executor | - | - | ✓ | ✓ | - |
| SCM Manager | ✓ | ✓ | ✓ | ✓ | ✓ |
| Auditor | - | - | - | ✓ | ✓ |

### Forbidden Combinations
- Creator cannot approve their own changes
- Executor cannot approve their own work
- Auditor cannot have execute permissions

## Compliance Requirements

### SOX Compliance

#### 1. Audit Trail Requirements
- All forecast overrides must be logged
- Approval chain must be documented
- Before/after values must be captured
- User attribution required

#### 2. Access Controls
- System access logging
- Role assignment approval
- Periodic access review

#### 3. Data Integrity
- No direct database modifications without audit
- Change management for configuration
- Version control for planning rules

### GDPR Compliance

#### 1. Data Access
- Branch-level data isolation
- User access logging
- Export action tracking

#### 2. Data Retention
- Demand history retention period
- Forecast archive policy
- Audit log retention

## Risk Controls

### Risk: Incorrect Forecast
**Controls:**
- Multi-method comparison
- Override reason required
- Manager approval for large changes
- Forecast accuracy tracking

### Risk: Stockout
**Controls:**
- Proactive alert system
- Safety stock monitoring
- Coverage analysis
- Priority replenishment

### Risk: Overstock
**Controls:**
- Max stock limits
- Overstock alerts
- Excess analysis
- Liquidation workflow

### Risk: Supplier Delay
**Controls:**
- Lead time monitoring
- Alternative sourcing
- Safety stock buffer
- Delay alerts

## Monitoring and Reporting

### Key Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Alert Response Time | Time to acknowledge alerts | < 4 hours |
| Forecast Accuracy | MAPE of forecasts | > 85% |
| Approval Cycle | Time from create to approve | < 24 hours |
| Override Rate | % of forecasts overridden | < 10% |
| Stockout Duration | Average stockout days | < 2 days |

### Audit Reports

#### 1. Override Report
- Items overridden
- Override reasons
- User responsible
- Impact analysis

#### 2. Approval Report
- Pending approvals
- Cycle time
- Rejection rate
- Approver workload

#### 3. Compliance Report
- Policy violations
- Control failures
- Remediation actions

## Incident Response

### Response Procedures

```python
INCIDENT_RESPONSE = {
    'stockout_critical': {
        'escalation': 'immediate',
        'notification': ['supply_chain_manager', 'branch_planner'],
        'sla': '2 hours',
        'actions': ['emergency_procurement', 'alternative_sourcing']
    },
    'forecast_miss': {
        'escalation': '24 hours',
        'notification': ['demand_planner_manager'],
        'sla': '1 week',
        'actions': ['root_cause_analysis', 'forecast_model_review']
    },
    'supplier_delay': {
        'escalation': 'immediate',
        'notification': ['supply_chain_manager', 'procurement'],
        'sla': '4 hours',
        'actions': ['alternative_sourcing', 'safety_stock_approval']
    }
}
```

## Testing Requirements

### Unit Testing
- Forecast calculation accuracy
- Replenishment logic
- Alert generation
- Permission enforcement

### Integration Testing
- WMS data flow
- Procurement integration
- Finance linkage
- Flow notifications

### User Acceptance Testing
- End-to-end scenarios
- Role-based access
- Approval workflows
- Report generation
