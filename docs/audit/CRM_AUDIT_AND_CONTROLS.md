# CRM Audit and Controls

## Overview

The CRM module implements comprehensive audit trail and control mechanisms to ensure data integrity, compliance, and traceability.

## Audit Trail

### Logged Events

#### Lead Management
- Lead creation with full details
- Lead updates with before/after values
- Lead conversion (to customer or opportunity)
- Lead status changes
- Lead assignment changes
- Lead score recalculations

#### Activity Tracking
- Activity creation
- Activity updates
- Activity outcomes recorded

#### Complaint Management
- Complaint creation
- Complaint status changes
- Complaint timeline entries
- Complaint assignment changes
- Complaint resolution

#### Key Account Management
- Account creation
- Account tier changes
- Account manager reassignment
- Objective creation/completion
- Review documentation

### Audit Log Schema

```sql
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    module TEXT NOT NULL,          -- 'crm', 'sales', etc.
    entity_type TEXT NOT NULL,     -- 'lead', 'complaint', etc.
    entity_id INTEGER NOT NULL,
    action TEXT NOT NULL,         -- 'CREATE', 'UPDATE', 'DELETE'
    user_id INTEGER,
    changes TEXT,                 -- JSON of before/after values
    ip_address TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Audit Log Retention
- Default retention: 7 years
- Archival policy: Yearly archive to cold storage
- Deletion requires Auditor role + approval

## Data Validation Controls

### Lead Data Quality
- Required fields: company_name, source, status
- Email format validation
- Phone number format hints
- Duplicate detection based on email/phone

### Lead Scoring
- Score range: 0-100
- Automatic recalculation on relevant field changes
- Manual override disabled (configurable)

### Complaint Handling
- Required fields: subject, category, priority
- Priority escalation rules configurable
- SLA breach notifications

## Access Controls

### Row-Level Security

All CRM queries respect:

1. **User Role Permissions**
   - As defined in permission matrix
   - Checked at route level

2. **Scope-Based Filtering**
   - Salespersons see own records only
   - Managers see team records
   - Admins see all records

3. **Customer Access**
   - Based on customer assignment in Sales
   - Key accounts restricted to assigned managers

### Action-Level Permissions

| Action | Required Permission |
|--------|-------------------|
| View CRM Dashboard | `crm.dashboard.view` |
| View Leads | `crm.leads.view` |
| Create Lead | `crm.leads.create` |
| Edit Lead | `crm.leads.edit` |
| Delete Lead | `crm.leads.delete` |
| Convert Lead | `crm.leads.edit` |
| View Opportunities | `crm.opportunities.view` |
| Create Opportunity | `crm.opportunities.create` |
| Edit Opportunity | `crm.opportunities.edit` |
| View Activities | `crm.activities.view` |
| Log Activity | `crm.activities.create` |
| View Complaints | `crm.complaints.view` |
| Create Complaint | `crm.complaints.create` |
| Update Complaint | `crm.complaints.edit` |
| View Key Accounts | `crm.key_accounts.view` |
| Edit Key Accounts | `crm.key_accounts.edit` |
| View Forecasts | `crm.forecasts.view` |
| View Reports | `crm.reports.view` |
| View Customer 360 | `crm.customer_360.view` |
| Configure Settings | `crm.settings.edit` |

## Compliance Controls

### SOX Compliance (Future)
- Segregation of duties for approval workflows
- Dual authorization for high-value discounts
- Audit log tamper detection

### GDPR Compliance (Future)
- Customer data access logging
- Right to deletion workflow
- Data portability exports

### Data Retention
- Active records: Indefinite
- Deleted records: 7-year retention before purge
- Audit logs: 10-year retention

## Approval Workflows

### Special Pricing Approval
- Threshold-based routing
- Manager approval required above threshold
- Documentation of business justification

### Discount Override Approval
- Configurable discount limits by role
- Escalation to manager beyond limit
- Audit trail of all overrides

### Contract Approval
- Multi-level approval based on value
- Legal review integration (future)
- Digital signature support (future)

## Monitoring and Alerts

### Real-Time Alerts
- Hot lead notifications to assigned salesperson
- SLA breach warnings
- High-value opportunity alerts
- Critical complaint escalation

### Dashboard Metrics
- Lead response time
- Average time to qualification
- Pipeline velocity by stage
- Complaint resolution time
- Customer satisfaction trends

### Scheduled Reports
- Weekly pipeline summary to managers
- Monthly conversion analysis to leadership
- Quarterly account review reminders

## Risk Mitigation

### Data Quality Risks
- Mandatory fields prevent incomplete records
- Duplicate detection reduces redundancy
- Score validation ensures consistency

### Process Risks
- Approval workflows prevent unauthorized discounts
- SLA monitoring ensures service levels
- Escalation rules handle overflow

### Security Risks
- RBAC prevents unauthorized access
- Scope filtering limits data exposure
- Audit logging enables forensic analysis

## Control Testing

### Monthly Tests
- Sample lead conversion to verify audit trail
- Permission assignment review
- Duplicate detection validation

### Quarterly Tests
- Full permission matrix audit
- Report accuracy verification
- SLA compliance review

### Annual Tests
- Disaster recovery verification
- Data retention policy compliance
- Access recertification
