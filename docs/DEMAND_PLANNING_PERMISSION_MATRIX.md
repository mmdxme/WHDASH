# Demand Planning Permission Matrix

## Overview

The WHDASH Demand Planning module implements a comprehensive Role-Based Access Control (RBAC) system with granular permissions at the module, menu, page, and action levels. This document details all roles, permissions, and access controls.

## Permission Structure

```
planning
├── dashboard                    [view]
├── forecasts
│   ├── view                     ✓ All planners and above
│   ├── create                   ✓ Planner and above
│   ├── edit                     ✓ Planner and above
│   ├── delete                   ✗ Planner (read-only own)
│   ├── approve                  ✓ Manager and above
│   └── override                 ✓ Planner and above
├── demand
│   ├── view                     ✓ All
│   ├── create                   ✓ Planner and above
│   ├── edit                     ✓ Planner and above
│   └── delete                   ✓ Manager and above
├── replenishment
│   ├── view                     ✓ All
│   ├── create                   ✓ Planner and above
│   ├── edit                     ✓ Planner and above
│   ├── delete                   ✗ Planner
│   ├── approve                  ✓ Manager and above
│   └── execute                  ✗ Planner
├── policies
│   ├── view                     ✓ Planner and above
│   ├── create                   ✗ Planner
│   ├── edit                     ✗ Planner
│   └── delete                   ✗ Planner
├── scenarios
│   ├── view                     ✓ Planner and above
│   ├── create                   ✓ Planner and above
│   ├── edit                     ✓ Planner and above
│   ├── delete                   ✗ Planner
│   └── run                      ✓ Manager and above
├── alerts
│   ├── view                     ✓ All
│   ├── create                   ✓ Planner and above
│   ├── edit                     ✓ Planner and above
│   ├── delete                   ✗ Planner
│   ├── resolve                  ✓ Planner and above
│   ├── acknowledge               ✓ All
│   └── escalate                 ✗ Planner
├── reports
│   ├── view                     ✓ All
│   ├── export                   ✓ Planner and above
│   ├── create                   ✗ Planner
│   ├── edit                     ✗ Planner
│   └── delete                   ✗ Planner
├── settings
│   ├── view                     ✓ Manager and above
│   └── edit                     ✗ Planner
├── control_tower                [view]              ✓ All
├── statistical_forecasting
│   ├── view                     ✓ Planner and above
│   ├── create                   ✓ Planner and above
│   ├── edit                     ✓ Planner and above
│   ├── delete                   ✗ Planner
│   └── run                      ✓ Planner and above
├── forecast_versions
│   ├── view                     ✓ Planner and above
│   ├── create                   ✓ Planner and above
│   ├── edit                     ✓ Planner and above
│   ├── delete                   ✗ Planner
│   ├── freeze                   ✗ Planner
│   ├── publish                 ✗ Planner
│   ├── clone                    ✓ Planner and above
│   └── compare                  ✓ Planner and above
├── forecast_overrides
│   ├── view                     ✓ Planner and above
│   ├── create                   ✓ Planner and above
│   ├── edit                     ✓ Planner and above
│   ├── delete                   ✗ Planner
│   ├── approve                  ✗ Planner
│   ├── reject                   ✗ Planner
│   └── bulk_override            ✗ Planner
├── demand_drivers
│   ├── view                     ✓ Planner and above
│   ├── create                   ✗ Planner
│   ├── edit                     ✗ Planner
│   └── delete                   ✗ Planner
├── promotions
│   ├── view                     ✓ Planner and above
│   ├── create                   ✗ Planner
│   ├── edit                     ✗ Planner
│   └── delete                   ✗ Planner
├── seasonality
│   ├── view                     ✓ Planner and above
│   ├── create                   ✗ Planner
│   ├── edit                     ✗ Planner
│   └── delete                   ✗ Planner
├── consensus
│   ├── view                     ✓ Planner and above
│   ├── create                   ✓ Planner and above
│   ├── edit                     ✓ Planner and above
│   ├── delete                   ✗ Planner
│   ├── approve                  ✗ Planner
│   └── input                    ✓ Sales/Marketing + Planner
├── forecast_accuracy
│   ├── view                     ✓ Planner and above
│   ├── create                   ✓ Planner and above
│   └── calculate                ✓ Planner and above
├── demand_sensing
│   ├── view                     ✓ Planner and above
│   ├── create                   ✓ Planner and above
│   ├── detect                   ✓ Planner and above
│   └── acknowledge              ✓ Planner and above
├── scenario_planning
│   ├── view                     ✓ Planner and above
│   ├── create                   ✓ Planner and above
│   ├── edit                     ✓ Planner and above
│   ├── delete                   ✗ Planner
│   ├── run                      ✓ Manager and above
│   └── compare                  ✓ Planner and above
├── workflow
│   ├── view                     ✓ Planner and above
│   ├── create                   ✗ Planner
│   ├── edit                     ✗ Planner
│   ├── delete                   ✗ Planner
│   ├── approve                  ✗ Planner
│   └── reject                   ✗ Planner
├── supply_linkage               [view]              ✓ Planner and above
├── sales_linkage               [view]              ✓ Planner and above
├── branch_entity
│   ├── view                     ✓ Branch Planner and above
│   ├── create                   ✗ Planner
│   ├── edit                     ✗ Planner
│   └── delete                   ✗ Planner
└── export
    ├── view                     ✓ Planner and above
    ├── export                   ✓ Planner and above
    └── configure                ✗ Planner
```

## Role Definitions

| Role | Description | Scope |
|------|-------------|-------|
| DEMAND_PLANNING_ADMIN | Full system administrator | Global |
| DEMAND_PLANNING_MANAGER | Department manager | Global/Branch |
| DEMAND_PLANNER | Forecast analyst | Global/Branch |
| SALES_CONTRIBUTOR | Sales forecast input | Branch |
| MARKETING_CONTRIBUTOR | Marketing forecast input | Global |
| BRANCH_PLANNER | Branch-specific planner | Branch Only |
| EXECUTIVE_VIEWER | Read-only executive | Global |
| AUDITOR | Audit access only | Global |

## Default Role Permissions

### DEMAND_PLANNING_ADMIN
```
planning: *
planning.control_tower: view
planning.statistical_forecasting: *
planning.forecast_versions: *
planning.forecast_overrides: *
planning.demand_drivers: *
planning.promotions: *
planning.seasonality: *
planning.consensus: *
planning.forecast_accuracy: *
planning.demand_sensing: *
planning.scenario_planning: *
planning.alerts: *
planning.workflow: *
planning.supply_linkage: view
planning.sales_linkage: view
planning.branch_entity: *
planning.export: *
planning.reports: *
planning.settings: *
```

### DEMAND_PLANNING_MANAGER
```
planning.dashboard: view
planning.forecasts: [view, create, edit, approve, override]
planning.demand: [view, create, edit]
planning.replenishment: [view, create, edit, approve, execute]
planning.policies: [view, create, edit]
planning.scenarios: [view, create, edit, approve, run]
planning.alerts: [view, create, edit, resolve, escalate]
planning.reports: [view, export]
planning.settings: view
planning.control_tower: view
planning.statistical_forecasting: [view, create, edit, run]
planning.forecast_versions: [view, create, edit, freeze, publish, clone, compare]
planning.forecast_overrides: [view, create, edit, approve, reject, bulk_override]
planning.demand_drivers: [view, create, edit]
planning.promotions: [view, create, edit]
planning.seasonality: [view, create, edit]
planning.consensus: [view, create, edit, approve, input]
planning.forecast_accuracy: [view, create, calculate]
planning.demand_sensing: [view, create, detect, acknowledge]
planning.scenario_planning: [view, create, edit, run, compare]
planning.workflow: [view, create, edit, approve, reject]
planning.supply_linkage: view
planning.sales_linkage: view
planning.export: [view, export, configure]
```

### DEMAND_PLANNER
```
planning.dashboard: view
planning.forecasts: [view, create, edit, override]
planning.demand: [view, create, edit]
planning.replenishment: [view]
planning.scenarios: [view, create, edit]
planning.alerts: [view, resolve]
planning.reports: view
planning.control_tower: view
planning.statistical_forecasting: [view, create, edit, run]
planning.forecast_versions: [view, create, clone, compare]
planning.forecast_overrides: [view, create]
planning.consensus: [view, create, input]
planning.forecast_accuracy: view
planning.demand_sensing: [view, create]
planning.scenario_planning: [view, create]
```

### SALES_CONTRIBUTOR
```
planning.dashboard: view
planning.consensus: [view, input]
planning.control_tower: view
planning.reports: view
```

### MARKETING_CONTRIBUTOR
```
planning.dashboard: view
planning.demand_drivers: [view, create]
planning.promotions: [view, create]
planning.consensus: [view, input]
planning.control_tower: view
planning.reports: view
```

### BRANCH_PLANNER
```
Same as DEMAND_PLANNER but branch_id restricted
planning.forecasts: [view, create, edit, override]
planning.demand: [view, create, edit]
planning.replenishment: [view]
planning.scenarios: [view, create, edit]
planning.alerts: [view, resolve]
planning.reports: view
planning.control_tower: view
planning.forecast_versions: [view, create, clone, compare]
planning.forecast_overrides: [view, create]
planning.consensus: [view, create, input]
```

### EXECUTIVE_VIEWER
```
planning.dashboard: view
planning.control_tower: view
planning.reports: view
planning.forecast_accuracy: view
planning.scenarios: view
planning.supply_linkage: view
planning.sales_linkage: view
```

### AUDITOR
```
planning.dashboard: view
planning.forecasts: view
planning.alerts: view
planning.reports: view
planning.audit_log: view
planning.forecast_versions: view
planning.forecast_overrides: view
```

## Branch/Entity Access Control

Branch-specific access is enforced at the data level:

```sql
-- Branch planners can only see their branch's data
SELECT * FROM planning_forecast_versions
WHERE branch_id = ? OR branch_id IS NULL

-- Items filtered by branch warehouse assignments
SELECT * FROM planning_demand_history dh
JOIN wms_warehouses w ON dh.warehouse_id = w.id
WHERE w.branch_id = ?
```

## Override Approval Thresholds

| Override Change | Threshold | Required Approval |
|-----------------|-----------|-------------------|
| < 10% | No approval | Immediate |
| 10-25% | Level 1 | Planner Manager |
| 25-50% | Level 2 | Demand Planning Manager |
| > 50% | Level 3 | Demand Planning Admin |

## Audit Trail

All planning actions are logged to `planning_audit_log`:

```sql
CREATE TABLE planning_audit_log (
    id INTEGER PRIMARY KEY,
    action_type TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER,
    item_id INTEGER,
    warehouse_id INTEGER,
    company_id INTEGER,
    user_id INTEGER,
    changes_json TEXT,
    notes TEXT,
    ip_address TEXT,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## Action Types Logged

- FORECAST_GENERATED
- FORECAST_APPROVED
- FORECAST_OVERRIDE_CREATED
- FORECAST_OVERRIDE_APPROVED
- FORECAST_OVERRIDE_REJECTED
- VERSION_CREATED
- VERSION_FROZEN
- VERSION_PUBLISHED
- VERSION_CLONED
- SCENARIO_CREATED
- SCENARIO_RUN
- ALERT_CREATED
- ALERT_RESOLVED
- ALERT_ESCALATED
- SETTINGS_CHANGED

## Session Permissions Caching

Permissions are cached in session for performance:

```python
# Check permission
if 'planning' not in session.get('permissions', {}):
    session['permissions']['planning'] = get_user_permissions(db, user_id, 'planning')

# Verify action
if 'override' not in session['permissions']['planning'].get('forecasts', []):
    flash('Permission denied', 'error')
    return redirect(url_for('scm.demand'))
```
