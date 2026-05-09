# CRM Permission Matrix

## Overview

The CRM module uses role-based access control (RBAC) integrated with the WHDASH permission system. Permissions follow the pattern: `('crm', resource, action)`.

## Permission Hierarchy

```
crm
├── dashboard (view)
├── leads
│   ├── view
│   ├── create
│   ├── edit
│   └── delete
├── opportunities
│   ├── view
│   ├── create
│   ├── edit
│   └── delete
├── activities
│   ├── view
│   ├── create
│   ├── edit
│   └── delete
├── complaints
│   ├── view
│   ├── create
│   ├── edit
│   └── delete
├── key_accounts
│   ├── view
│   ├── create
│   ├── edit
│   └── delete
├── forecasts
│   └── view
├── reports
│   └── view
├── customer_360
│   └── view
├── journey
│   └── view
└── settings
    ├── view
    └── edit
```

## Role Definitions

### Global Admin
- Full access to all CRM features
- Can configure CRM settings
- Can delete any record

### CRM Admin
- Full access to all CRM features
- Can configure CRM settings
- Cannot delete records created by others

### Sales Manager
- View all leads/opportunities/activities in their team
- Create/edit leads and opportunities
- Log activities
- View forecasts and reports
- Cannot access settings

### Salesperson
- View/edit own leads and opportunities
- Log activities
- View own forecasts
- Cannot access team data or reports

### Marketing Reviewer
- View leads (read-only)
- View reports
- Cannot edit or create

### Customer Service Reviewer
- View complaints
- Cannot access leads/opportunities

### Executive Viewer
- View all dashboards and reports
- Cannot edit any records

### Auditor
- View all CRM data
- Access audit logs
- Cannot edit

## Default Permission Assignments

| Role | dashboard | leads | opportunities | activities | complaints | key_accounts | forecasts | reports | customer_360 | settings |
|------|----------|-------|---------------|------------|------------|--------------|----------|---------|--------------|----------|
| Global Admin | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| CRM Admin | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Sales Manager | ✓ | ✓ | ✓ | ✓ | - | ✓ | ✓ | ✓ | - |
| Salesperson | ✓ | Own | Own | Own | - | - | Own | - | Own | - |
| Marketing Reviewer | ✓ | ✓ (R) | - | - | - | - | - | ✓ | - |
| Customer Service Reviewer | ✓ | - | - | - | ✓ (R) | - | - | ✓ | - |
| Executive Viewer | ✓ | ✓ (R) | ✓ (R) | ✓ (R) | ✓ (R) | ✓ (R) | ✓ (R) | ✓ | ✓ | - |
| Auditor | ✓ (R) | ✓ (R) | ✓ (R) | ✓ (R) | ✓ (R) | ✓ (R) | ✓ (R) | ✓ (R) | ✓ (R) | - |

✓ = Full access, ✓ (R) = Read-only, - = No access

## Permission Check Implementation

All CRM routes use the `crm_permission_required` decorator:

```python
@app.route('/crm/leads/')
@crm_permission_required('leads', 'view')
def crm_leads():
    ...
```

The decorator checks:
1. User is logged in
2. User has `('crm', 'leads', 'view')` permission

## Scope-Based Access

Beyond role permissions, CRM also supports scope-based filtering:

### By Salesperson
- Salespersons see only their own data
- Managers see their team's data

### By Customer
- Key Account Managers see assigned accounts only
- Users see customers they have access to in Sales

### By Branch/Entity
- Multi-entity deployments can filter by company_id

## Audit Trail

All CRM changes are logged with:
- User who made the change
- Before/after values for critical fields
- Timestamp
- IP address (if available)

Auditable actions:
- Lead creation, update, conversion
- Complaint creation, status change
- Key account modifications
- Customer engagement score recalculations
