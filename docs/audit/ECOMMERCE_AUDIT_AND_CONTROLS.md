# Marketing Automation Audit and Controls

## Overview

The Marketing Automation module implements comprehensive audit logging and control mechanisms to ensure regulatory compliance, security, and operational transparency.

## Audit System Architecture

### Audit Components

```
┌─────────────────────────────────────────────────────────┐
│                    Audit System                          │
├─────────────────────────────────────────────────────────┤
│  Activity Logger                                        │
│  - Marketing changes tracked                             │
│  - User actions recorded                                │
│  - Before/after values captured                         │
├─────────────────────────────────────────────────────────┤
│  Approval Workflow                                       │
│  - Campaign approval                                    │
│  - Budget approval                                     │
│  - Content approval                                    │
│  - Multi-level authorization                           │
├─────────────────────────────────────────────────────────┤
│  SLA Monitoring                                         │
│  - Response time tracking                               │
│  - Breach detection                                     │
│  - Escalation management                                │
├─────────────────────────────────────────────────────────┤
│  Notification System                                    │
│  - Alerts for key events                               │
│  - Approval notifications                               │
│  - SLA warnings                                        │
└─────────────────────────────────────────────────────────┘
```

## Audit Logging

### Activity Log Table (`marketing_activity_log`)

Records all significant marketing activities:

| Field | Description |
|-------|-------------|
| activity_type | Type of activity (create, update, delete, export, approve, reject) |
| entity_type | Marketing entity type |
| entity_id | ID of affected entity |
| entity_name | Human-readable name |
| action | Specific action performed |
| actor_user_id | User who performed action |
| old_value | Previous state (JSON) |
| new_value | New state (JSON) |
| ip_address | User's IP address |
| user_agent | Browser/client info |
| created_at | Timestamp |

### Logged Activities

#### Campaign Changes
- Campaign created
- Campaign updated (with field changes)
- Campaign deleted
- Campaign status changed
- Budget modified
- Campaign approved/rejected

#### Lead Changes
- Lead created
- Lead updated
- Lead status changed
- Lead assigned
- Lead converted
- Lead score changed

#### Journey Changes
- Journey created
- Journey published
- Journey paused
- Journey step added/removed
- Participant enrolled
- Participant completed/dropped

#### A/B Test Changes
- Test created
- Test started/stopped
- Winner declared
- Variants modified

#### Content Changes
- Content created
- Content submitted for approval
- Content approved/rejected
- Content published

#### Budget Changes
- Budget created
- Budget modified
- Budget approved/rejected

### Audit Query Examples

#### Recent Changes by User
```sql
SELECT * FROM marketing_activity_log
WHERE actor_user_id = ?
ORDER BY created_at DESC
LIMIT 50;
```

#### Campaign History
```sql
SELECT * FROM marketing_activity_log
WHERE entity_type = 'campaign' AND entity_id = ?
ORDER BY created_at DESC;
```

#### Export Activity
```sql
SELECT * FROM marketing_activity_log
WHERE activity_type = 'export'
ORDER BY created_at DESC;
```

## Approval Workflow

### Campaign Approval Flow

```
┌──────────┐    ┌─────────────┐    ┌──────────┐    ┌──────────┐
│  Draft   │───▶│ Under Review │───▶│ Approved │───▶│Scheduled │
└──────────┘    └─────────────┘    └──────────┘    └──────────┘
                      │                 │
                      ▼                 ▼
                ┌──────────┐      ┌──────────┐
                │ Rejected │      │  Active  │
                └──────────┘      └──────────┘
```

### Approval States
- `Draft` - Initial creation
- `Pending` - Awaiting approval
- `Approved` - Approved for launch
- `Rejected` - Returned with feedback
- `Scheduled` - Approved and scheduled
- `Active` - Live campaign
- `Paused` - Temporarily stopped
- `Completed` - Finished execution
- `Cancelled` - Terminated

### Approval Triggers

| Entity | Trigger | Approvers |
|--------|---------|-----------|
| Campaign | Budget > threshold | Marketing Admin |
| Campaign | New campaign type | Marketing Manager |
| Budget | Amount > threshold | Finance Admin |
| Content | Certain categories | Content Reviewer |
| Offer | Discount > threshold | Marketing Manager |

## SLA Monitoring

### SLA Policy Types

| Policy | Target | Priority |
|--------|--------|----------|
| Lead Response | 4 hours | Critical |
| Campaign Approval | 24 hours | High |
| Content Approval | 48 hours | Medium |
| Offer Response | 8 hours | High |

### SLA Instance States
- `Active` - Within SLA window
- `At Risk` - 80% of time elapsed
- `Breached` - SLA deadline passed
- `Resolved` - Completed within SLA
- `Escalated` - Escalated to higher authority

### SLA Metrics

```
SLA Compliance Rate = (Resolved On Time / Total Instances) × 100%
Average Response Time = Sum(Response Times) / Count
```

## Notification System

### Notification Types

| Type | Trigger | Priority |
|------|---------|----------|
| approval | Approval needed | Medium |
| alert | Threshold exceeded | High/Critical |
| reminder | Scheduled event approaching | Low |
| milestone | Journey/campaign milestone | Medium |
| sla | SLA warning/breach | High |
| test | A/B test complete | Medium |

### Notification Delivery
- In-app notification center
- Dashboard alerts
- Flow integration (future)
- Email integration (future)

## Security Controls

### Access Control

#### Authentication
- Session-based authentication
- User login required for all marketing functions
- Session timeout after inactivity

#### Authorization
- Role-based permissions
- Permission checks on all routes
- Branch/entity scope restrictions

### Permission Levels

| Level | Description |
|-------|-------------|
| All Marketing | Global Admin bypass |
| Module Level | Access to entire module |
| Menu Level | Access to specific menu items |
| Page Level | Access to specific pages |
| Action Level | Execute specific actions |

### Sensitive Operations

Operations requiring elevated privileges:
- Delete campaign
- Approve budget > threshold
- Modify attribution model
- Change SLA policies
- Manage user roles
- Export sensitive data

## Compliance Controls

### Data Retention

| Data Type | Retention Period | Legal Basis |
|-----------|-----------------|-------------|
| Audit Logs | 7 years | Financial compliance |
| Campaign Data | 5 years | Business records |
| Lead Data | 3 years | Marketing best practice |
| Communication Logs | 2 years | Communication records |
| Export Logs | 3 years | Audit trail |

### Data Privacy

- PII handling compliant
- Lead data minimization
- Communication consent tracking
- Unsubscribe management
- Do-not-contact lists

### Change Control

All marketing changes follow:
1. User authentication
2. Permission verification
3. Business rule validation
4. Audit logging
5. Approval workflow (if required)

## Control Reports

### Audit Trail Report
- User activity summary
- Entity change history
- Export activity
- Approval cycle times

### Compliance Report
- SLA compliance metrics
- Approval cycle statistics
- Budget variance analysis
- Policy exception summary

### Security Report
- Access attempts (failed)
- Permission escalation events
- Export activity by user
- Session anomalies

## Control Implementation

### Database Controls
```python
# Before update - capture old value
old_record = db.execute("SELECT * FROM campaigns WHERE id = ?", id).fetchone()

# Perform update
db.execute("UPDATE campaigns SET ... WHERE id = ?", id)

# Log the change
log_marketing_audit(db, 'campaign', id, 'UPDATE',
                   old_value=json.dumps(dict(old_record)),
                   new_value=json.dumps(new_data),
                   actor_user_id=user_id)
```

### Route-Level Controls
```python
@mkt_bp.route('/campaigns/approve/<int:id>', methods=['POST'])
@mkt_login_required
@mkt_permission_required('approve_campaigns')
def approve_campaign(id):
    # Verify approval permission
    # Check budget thresholds
    # Update status
    # Log approval
    # Send notifications
```

## Alerts and Monitoring

### Real-Time Alerts
- SLA breach warnings
- Budget threshold exceeded
- Campaign performance anomalies
- Lead score spikes

### Dashboard Monitoring
- Active campaigns status
- Pending approvals count
- SLA compliance gauge
- Recent activity feed

## Audit Retention and Archival

### Short-Term (1 year)
- Recent audit logs
- Active campaign data
- Current year reports

### Long-Term (7 years)
- Financial-related audits
- Budget approvals
- Compliance records

### Archival Process
- Annual archival of old records
- Compressed storage
- Secure access controls
- Retrieval procedures documented

## Best Practices

### For Administrators
1. Review audit logs weekly
2. Monitor SLA compliance daily
3. Track approval cycle times
4. Validate permission assignments quarterly

### For Compliance
1. Generate monthly compliance reports
2. Audit user role assignments
3. Review export activity
4. Monitor data retention compliance

### For Security
1. Review failed access attempts
2. Audit permission escalations
3. Monitor export volumes
4. Validate session timeouts

## Incident Response

### Audit Investigation Process
1. Identify incident scope
2. Query audit logs for timeline
3. Review affected records
4. Document findings
5. Implement corrective action

### Key Queries for Investigation
```sql
-- Find all changes to a specific record
SELECT * FROM marketing_activity_log
WHERE entity_type = ? AND entity_id = ?
ORDER BY created_at;

-- Find all actions by user in date range
SELECT * FROM marketing_activity_log
WHERE actor_user_id = ? AND created_at BETWEEN ? AND ?
ORDER BY created_at DESC;

-- Find all exports in date range
SELECT * FROM marketing_activity_log
WHERE activity_type = 'export'
AND created_at BETWEEN ? AND ?;
```
