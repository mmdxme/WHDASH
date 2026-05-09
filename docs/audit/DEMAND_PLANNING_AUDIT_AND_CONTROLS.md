# Demand Planning Audit and Controls

## Overview

The WHDASH Demand Planning module implements comprehensive audit trails and controls to ensure data integrity, regulatory compliance, and operational transparency.

## Audit Trail Architecture

### Audit Log Table

```sql
CREATE TABLE planning_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
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

### Key Audit Fields

| Field | Description | Purpose |
|-------|-------------|---------|
| action_type | Type of action performed | Categorization |
| entity_type | Type of entity changed | Filtering |
| entity_id | ID of changed entity | Reference |
| changes_json | Before/after values | Detail |
| user_id | Who performed action | Attribution |
| ip_address | Source of change | Security |
| created_at | When change occurred | Timeline |

## Action Types Logged

### Forecast Actions
- FORECAST_GENERATED
- FORECAST_APPROVED
- FORECAST_REJECTED
- FORECAST_DELETED

### Override Actions
- OVERRIDE_CREATED
- OVERRIDE_APPROVED
- OVERRIDE_REJECTED
- OVERRIDE_BULK_APPLIED
- OVERRIDE_DELETED

### Version Actions
- VERSION_CREATED
- VERSION_FROZEN
- VERSION_PUBLISHED
- VERSION_CLONED
- VERSION_COMPARED

### Scenario Actions
- SCENARIO_CREATED
- SCENARIO_RUN
- SCENARIO_DELETED

### Alert Actions
- ALERT_CREATED
- ALERT_RESOLVED
- ALERT_ESCALATED
- ALERT_ACKNOWLEDGED

### Settings Actions
- SETTINGS_CHANGED
- POLICY_CREATED
- POLICY_UPDATED

## Audit Log Helper Functions

```python
def log_planning_action(db, action_type, entity_type, entity_id=None,
                         item_id=None, warehouse_id=None, company_id=None,
                         user_id=None, changes=None, notes=None):
    """Log a planning action to the audit trail."""
    changes_json = json.dumps(changes) if changes else None
    db.execute("""
        INSERT INTO planning_audit_log
        (action_type, entity_type, entity_id, item_id, warehouse_id, company_id,
         user_id, changes_json, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (action_type, entity_type, entity_id, item_id, warehouse_id, company_id,
          user_id, changes_json, notes))
    db.commit()
```

## Override Audit

### Override Before/After Tracking

```python
override_record = {
    'item_id': 1,
    'period_start': '2026-02-15',
    'original_quantity': 200.0,
    'override_quantity': 250.0,
    'override_reason': 'PROMOTION',
    'override_type': 'MANUAL',
    'status': 'APPROVED'
}

# Logged as:
{
    'action': 'OVERRIDE_CREATED',
    'before': {'final_quantity': 200.0},
    'after': {'final_quantity': 250.0},
    'change_percent': 25.0,
    'user': 'dp_planner1',
    'timestamp': '2026-01-15 10:30:00'
}
```

### Approval Audit Trail

```sql
SELECT 
    o.id,
    o.item_id,
    o.original_quantity,
    o.override_quantity,
    o.override_reason,
    o.status,
    u1.username as requested_by,
    o.created_at,
    u2.username as reviewed_by,
    o.reviewed_at,
    o.review_notes
FROM planning_forecast_overrides o
LEFT JOIN users u1 ON o.created_by = u1.id
LEFT JOIN users u2 ON o.reviewed_by = u2.id
```

## Version Control Audit

### Version Lifecycle Audit

Each version tracks:
- Creation timestamp and user
- Freeze timestamp and user
- Publish timestamp and user
- Clone source
- Parent version relationship
- All line changes

```sql
SELECT
    v.id,
    v.version_name,
    v.version_number,
    v.status,
    v.is_baseline,
    v.is_frozen,
    u1.username as created_by,
    v.created_at,
    u2.username as published_by,
    v.published_at,
    p.version_name as parent_version
FROM planning_forecast_versions v
LEFT JOIN users u1 ON v.created_by = u1.id
LEFT JOIN users u2 ON v.published_by = u2.id
LEFT JOIN planning_forecast_versions p ON v.parent_version_id = p.id
```

## Forecast Accuracy Audit

### Accuracy Calculation Audit

```sql
SELECT
    fa.item_id,
    fa.period_start,
    fa.forecast_quantity,
    fa.actual_quantity,
    fa.error_quantity,
    fa.mape,
    fa.bias,
    fa.calculated_at,
    v.version_name,
    v.version_number
FROM planning_forecast_accuracy fa
LEFT JOIN planning_forecast_versions v ON fa.version_id = v.id
ORDER BY fa.calculated_at DESC
```

### Bias Tracking by Planner

```sql
SELECT
    fb.planner_id,
    u.username,
    fb.period_start,
    fb.total_forecast,
    fb.total_actual,
    fb.bias_amount,
    fb.bias_percent
FROM planning_forecast_bias fb
JOIN users u ON fb.planner_id = u.id
ORDER BY fb.bias_percent DESC
```

## Data Integrity Controls

### Transaction Integrity

All forecast operations wrapped in transactions:

```python
def generate_forecast_with_audit(db, item_id, method, user_id):
    try:
        db.begin()
        
        # Create forecast run
        cursor = db.execute("""
            INSERT INTO planning_forecast_runs 
            (run_name, method, status, created_by)
            VALUES (?, ?, 'DRAFT', ?)
        """, (f"Forecast {datetime.now()}", method, user_id))
        run_id = cursor.lastrowid
        
        # Generate forecast lines
        for period, qty in forecast_data:
            db.execute("""
                INSERT INTO planning_forecast_lines
                (run_id, item_id, period_start, base_quantity, final_quantity)
                VALUES (?, ?, ?, ?, ?)
            """, (run_id, item_id, period, qty, qty))
        
        # Log audit
        log_planning_action(db, 'FORECAST_GENERATED', 'forecast_run', run_id,
                           item_id=item_id, user_id=user_id,
                           changes={'method': method, 'qty': qty})
        
        db.commit()
        return run_id
        
    except Exception as e:
        db.rollback()
        log_planning_action(db, 'FORECAST_GENERATION_FAILED', 'forecast_run', None,
                           item_id=item_id, user_id=user_id,
                           notes=str(e))
        raise
```

### Validation Rules

1. **Forecast Quantity**: Must be >= 0
2. **Period**: Cannot be in the past for overrides
3. **Override Reason**: Required for changes > 10%
4. **Approval**: Required for changes > 25%

### Constraint Checks

```sql
-- Prevent duplicate forecast lines
UNIQUE(run_id, item_id, period_start)

-- Ensure positive quantities
CHECK (quantity >= 0)

-- Validate status transitions
CHECK (
    (status = 'DRAFT') OR
    (status = 'FROZEN' AND frozen_by IS NOT NULL) OR
    (status = 'PUBLISHED' AND published_by IS NOT NULL) OR
    (status = 'APPROVED' AND approved_by IS NOT NULL)
)
```

## RBAC Controls

### Permission Enforcement

```python
def forecast_permission_required(action):
    """Decorator for forecast permission checks."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please login', 'error')
                return redirect(url_for('auth.login'))
            
            user_permissions = get_user_permissions(db, session['user_id'], 'planning')
            
            if action not in user_permissions.get('forecasts', []):
                # Log unauthorized attempt
                log_planning_action(db, 'UNAUTHORIZED_ACCESS_ATTEMPT', 
                                   'forecast', None,
                                   user_id=session['user_id'],
                                   notes=f'Attempted action: {action}')
                flash('Permission denied', 'error')
                return redirect(url_for('scm.demand'))
            
            return f(*args, **kwargs)
        return wrapped
    return decorator
```

### Branch-Level Access Control

```python
@forecast_permission_required('view')
def demand_versions_detail(version_id):
    db = get_db()
    
    version = db.execute("""
        SELECT * FROM planning_forecast_versions WHERE id = ?
    """, (version_id,)).fetchone()
    
    # Check branch access
    user_branches = get_user_branches(session['user_id'])
    if version['branch_id'] not in user_branches and version['branch_id'] is not None:
        log_planning_action(db, 'UNAUTHORIZED_ACCESS', 'forecast_version',
                          version_id, user_id=session['user_id'])
        flash('Access denied to this branch', 'error')
        return redirect(url_for('scm.demand_versions_list'))
    
    # ... rest of function
```

## Compliance Controls

### SOX Compliance

For financial forecasting compliance:

1. **Segregation of Duties**
   - Forecast creators cannot approve their own forecasts
   - Override reviewers must be different from creators
   - Version publishers must be managers

2. **Audit Trail Retention**
   - Minimum 7 years for forecast data
   - All changes logged with before/after values

3. **Approval Thresholds**
   - < 10%: Planners can self-approve
   - 10-25%: Manager approval required
   - > 25%: Director approval required

### Change Management

```python
def require_approval(action, change_percent, user_role):
    """Determine if approval is required."""
    if user_role in ['ADMIN', 'DEMAND_PLANNING_ADMIN']:
        return False
    
    if action == 'override':
        if change_percent < 10:
            return False
        elif change_percent < 25:
            return user_role != 'DEMAND_PLANNER'
        else:
            return True
    
    if action == 'version_publish':
        return user_role == 'DEMAND_PLANNER'
    
    return False
```

## Flow Integration for Audit

### Notification Audit Trail

All Flow notifications are tracked:

```python
def create_flow_notification_audit(db, notification_id, notification_type,
                                   entity_type, entity_id, user_id):
    """Track Flow notification creation."""
    db.execute("""
        INSERT INTO planning_flow_notifications
        (notification_type, entity_type, entity_id, created_by, created_at)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (notification_type, entity_type, entity_id, user_id))
```

### Approval Workflow Audit

```python
# All approval actions logged
log_planning_action(
    db,
    'OVERRIDE_APPROVED',
    'override_approval',
    approval_id,
    user_id=reviewer_id,
    changes={
        'override_id': override_id,
        'override_quantity': 250,
        'review_notes': 'Approved for promotion'
    }
)
```

## Reporting and Analytics

### Audit Reports

| Report | Description | Frequency |
|--------|-------------|----------|
| Override Summary | Override trends and patterns | Weekly |
| Accuracy History | Accuracy metric trends | Monthly |
| Version Changes | Version lifecycle summary | Monthly |
| User Activity | Actions by user | Weekly |
| Compliance Check | SOX compliance status | Monthly |

### Audit Query Examples

```sql
-- All overrides by user in date range
SELECT o.*, u.username, i.item_code
FROM planning_forecast_overrides o
JOIN users u ON o.created_by = u.id
JOIN wms_items i ON o.item_id = i.id
WHERE o.created_at BETWEEN ? AND ?
ORDER BY o.created_at DESC

-- Version lifecycle summary
SELECT 
    v.version_name,
    v.status,
    COUNT(vl.id) as line_count,
    u1.username as created_by,
    v.created_at,
    u2.username as published_by,
    v.published_at
FROM planning_forecast_versions v
LEFT JOIN planning_forecast_version_lines vl ON v.id = vl.version_id
LEFT JOIN users u1 ON v.created_by = u1.id
LEFT JOIN users u2 ON v.published_by = u2.id
GROUP BY v.id

-- Compliance audit - unapproved high overrides
SELECT o.*, u1.username as requested_by, u2.username as reviewed_by
FROM planning_forecast_overrides o
JOIN users u1 ON o.created_by = u1.id
LEFT JOIN users u2 ON o.reviewed_by = u2.id
WHERE o.status = 'PENDING'
AND (o.override_quantity - o.original_quantity) / o.original_quantity > 0.25
```

## Retention and Archival

### Data Retention Policy

| Data Type | Retention Period | Storage |
|-----------|----------------|--------|
| Audit Logs | 7 years | Archive |
| Forecast Runs | 3 years | Active |
| Forecast Versions | 5 years | Archive |
| Accuracy Records | 3 years | Active |
| Override History | 7 years | Archive |
| User Sessions | 90 days | Active |

### Archival Process

```python
def archive_old_forecasts():
    """Archive forecasts older than 3 years."""
    db = get_db()
    
    cutoff_date = (datetime.now() - timedelta(days=3*365)).strftime('%Y-%m-%d')
    
    # Move to archive table
    db.execute("""
        INSERT INTO planning_forecast_runs_archive
        SELECT * FROM planning_forecast_runs
        WHERE created_at < ?
    """, (cutoff_date,))
    
    # Delete from active
    db.execute("""
        DELETE FROM planning_forecast_runs
        WHERE created_at < ?
    """, (cutoff_date,))
    
    db.commit()
```

## Security Controls

### Access Logging

```python
@app.before_request
def log_access():
    """Log all access to planning routes."""
    if request.path.startswith('/scm/demand'):
        log_planning_action(
            db,
            'PAGE_ACCESS',
            'planning_module',
            user_id=session.get('user_id'),
            notes=request.path
        )
```

### IP-based Restrictions

```python
def check_ip_access():
    """Restrict access by IP for sensitive operations."""
    allowed_ips = ['10.0.0.0/8', '192.168.0.0/16']
    
    if request.path.startswith('/scm/demand/settings'):
        if not is_ip_allowed(request.remote_addr, allowed_ips):
            log_planning_action(
                db, 'UNAUTHORIZED_IP_ACCESS',
                'settings', user_id=session.get('user_id')
            )
            flash('Access denied from this location', 'error')
            return redirect(url_for('scm.demand'))
```

## Best Practices

1. **Always log before/after values** for any change
2. **Include user context** in all audit records
3. **Use structured JSON** for changes field
4. **Implement approval workflows** for sensitive changes
5. **Regular audit report generation** for management review
6. **Periodic access review** for compliance
7. **Archive old data** to maintain performance
8. **Test audit trail integrity** regularly
