# SCM Permission Matrix

## Overview

The SCM module implements a comprehensive Role-Based Access Control (RBAC) system that ensures proper separation of duties and least-privilege access to supply chain management functions.

## Permission Definitions

### Module-Level Permissions

| Permission | Description |
|------------|-------------|
| `scm:dashboard:view` | View SCM dashboards and control tower |
| `scm:demand:view` | View demand planning pages |
| `scm:demand:create` | Create demand forecasts |
| `scm:demand:edit` | Edit existing forecasts |
| `scm:demand:approve` | Approve forecast versions |
| `scm:demand:override` | Override forecast values |
| `scm:supply:view` | View supply planning pages |
| `scm:supply:create` | Create supply plans |
| `scm:supply:edit` | Edit supply plans |
| `scm:replenishment:view` | View replenishment pages |
| `scm:replenishment:create` | Generate replenishment recommendations |
| `scm:replenishment:edit` | Edit replenishment settings |
| `scm:replenishment:approve` | Approve replenishment actions |
| `scm:replenishment:execute` | Execute approved replenishments |
| `scm:mrp:view` | View MRP pages |
| `scm:mrp:create` | Run MRP calculations |
| `scm:mrp:edit` | Edit MRP parameters |
| `scm:mrp:approve` | Approve purchase suggestions |
| `scm:mrp:execute` | Execute approved purchases |
| `scm:inventory:view` | View inventory optimization |
| `scm:inventory:edit` | Edit inventory parameters |
| `scm:network:view` | View multi-echelon planning |
| `scm:network:edit` | Edit network settings |
| `scm:service:view` | View service level pages |
| `scm:service:edit` | Edit service level targets |
| `scm:scenarios:view` | View scenarios |
| `scm:scenarios:create` | Create new scenarios |
| `scm:scenarios:edit` | Edit scenarios |
| `scm:scenarios:approve` | Approve scenarios |
| `scm:scenarios:run` | Run scenario simulations |
| `scm:alerts:view` | View alerts |
| `scm:alerts:create` | Create alerts manually |
| `scm:alerts:edit` | Edit alert thresholds |
| `scm:alerts:resolve` | Resolve alerts |
| `scm:alerts:acknowledge` | Acknowledge alerts |
| `scm:supplier:view` | View supplier linkage |
| `scm:supplier:edit` | Edit supplier data |
| `scm:warehouse:view` | View warehouse linkage |
| `scm:warehouse:edit` | Edit warehouse data |
| `scm:workflow:view` | View workflow pages |
| `scm:workflow:create` | Create workflows |
| `scm:workflow:edit` | Edit workflows |
| `scm:workflow:approve` | Approve via workflow |
| `scm:reports:view` | View reports |
| `scm:reports:export` | Export report data |
| `scm:reports:create` | Create custom reports |
| `scm:reports:edit` | Edit reports |
| `scm:settings:view` | View settings |
| `scm:settings:edit` | Modify settings |

## Role Definitions

### SCM Administrator
```python
{
    'permissions': ['*:*:*'],  # Full access
    'scope': 'global'
}
```

### Supply Chain Manager
```python
{
    'permissions': [
        'scm:dashboard:view',
        'scm:demand:*',
        'scm:supply:*',
        'scm:replenishment:*',
        'scm:mrp:*',
        'scm:inventory:*',
        'scm:network:*',
        'scm:service:*',
        'scm:scenarios:*',
        'scm:alerts:*',
        'scm:supplier:view',
        'scm:warehouse:view',
        'scm:workflow:*',
        'scm:reports:*',
        'scm:settings:view'
    ],
    'scope': 'global'
}
```

### Demand Planner
```python
{
    'permissions': [
        'scm:dashboard:view',
        'scm:demand:*',
        'scm:scenarios:view',
        'scm:alerts:view',
        'scm:reports:view'
    ],
    'scope': 'assigned_branches'
}
```

### Supply Planner
```python
{
    'permissions': [
        'scm:dashboard:view',
        'scm:supply:*',
        'scm:replenishment:view',
        'scm:mrp:view',
        'scm:alerts:view',
        'scm:supplier:view',
        'scm:warehouse:view',
        'scm:reports:view'
    ],
    'scope': 'assigned_branches'
}
```

### Replenishment Planner
```python
{
    'permissions': [
        'scm:dashboard:view',
        'scm:replenishment:*',
        'scm:inventory:view',
        'scm:alerts:view',
        'scm:warehouse:view',
        'scm:reports:view'
    ],
    'scope': 'assigned_branches'
}
```

### Branch Planner
```python
{
    'permissions': [
        'scm:dashboard:view',
        'scm:demand:view',
        'scm:supply:view',
        'scm:replenishment:view',
        'scm:alerts:view',
        'scm:reports:view'
    ],
    'scope': 'single_branch'
}
```

### Executive Viewer
```python
{
    'permissions': [
        'scm:dashboard:view',
        'scm:executive:view',
        'scm:reports:view',
        'scm:reports:export'
    ],
    'scope': 'global_readonly'
}
```

### Auditor
```python
{
    'permissions': [
        'scm:dashboard:view',
        'scm:reports:view',
        'scm:audit:view'
    ],
    'scope': 'global_readonly',
    'restrictions': ['no_edit', 'no_delete']
}
```

## Branch/Entity Access Control

### Branch Assignment
- Users can be assigned to specific branches
- Branch-level planners only see data for their assigned branches
- Global planners can see all branches

### Data Filtering
```python
def get_branch_filter(user_id):
    # Returns SQL filter clause for branch access
    
    user_branches = db.execute("""
        SELECT branch_id FROM user_branch_assignments
        WHERE user_id = ?
    """, (user_id,)).fetchall()
    
    if is_global_planner(user_id):
        return "1=1"  # No filter
    
    branch_ids = [b['branch_id'] for b in user_branches]
    return f"company_id IN ({','.join(branch_ids)})"
```

## Approval Workflow Permissions

### Approval Matrix

| Action | Threshold | Approver Role |
|--------|-----------|---------------|
| Forecast Approval | >10% variance | Demand Planner Manager |
| Replenishment >$10K | >$10,000 | Supply Chain Manager |
| Safety Stock Change | Any change | SCM Admin |
| Scenario Approval | Critical items | SCM Director |
| Emergency Purchase | >$50,000 | VP Supply Chain |
| Transfer Approval | >$5,000 | Branch Manager |

## Audit Trail

### Tracked Actions
- All forecast overrides (before/after values)
- Replenishment approvals/dismissals
- MRP parameter changes
- Alert acknowledgments
- Scenario modifications
- Settings changes
- Export actions

### Audit Log Format
```python
{
    'action_type': 'FORECAST_OVERRIDE',
    'entity_type': 'forecast_line',
    'entity_id': 123,
    'user_id': 45,
    'changes': {
        'before': {'quantity': 100},
        'after': {'quantity': 120}
    },
    'timestamp': '2026-04-17T10:30:00Z',
    'ip_address': '192.168.1.1'
}
```

## Compliance

### SOX Compliance
- All planning overrides require reason codes
- Approval chain documented
- Before/after audit trail
- Role separation enforced

### GDPR Compliance
- Branch-level data isolation
- User access logging
- Export action tracking
