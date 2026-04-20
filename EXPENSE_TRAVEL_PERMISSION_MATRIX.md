# Expense & Travel Management - Permission Matrix

## Role-Based Access Control

### Permission Definitions

| Module | Resource | Actions |
|--------|----------|---------|
| `expense_travel` | `dashboard` | view |
| `expense_travel` | `executive_dashboard` | view |
| `expense_travel` | `workspace` | view |
| `expense_travel` | `claims` | view, create, edit, delete, submit, approve, reject, return |
| `expense_travel` | `claims_view_own` | view_own |
| `expense_travel` | `claims_edit_own` | edit_own |
| `expense_travel` | `travel` | view, create, edit, delete, submit, approve, reject, return |
| `expense_travel` | `travel_view_own` | view_own |
| `expense_travel` | `advances` | view, create, edit, delete, submit, approve, reject, issue, settle |
| `expense_travel` | `receipts` | view, upload, delete, link, unlink |
| `expense_travel` | `reimbursements` | view, create, approve, reject, pay |
| `expense_travel` | `policies` | view, create, edit, delete, approve |
| `expense_travel` | `reports` | view, export |
| `expense_travel` | `settings` | view, edit |
| `expense_travel` | `audit_log` | view, export |

## Role Matrix

| Role | Dashboard | Claims | Travel | Advances | Receipts | Reimburse | Policies | Reports | Settings |
|------|-----------|--------|--------|----------|----------|-----------|----------|---------|----------|
| **Global Admin** | Full | Full | Full | Full | Full | Full | Full | Full | Full |
| **Expense Admin** | Full | Full | Full | Full | Full | Full | Full | Full | Full |
| **Travel Admin** | Full | View | Full | View | View | View | View | Full | Full |
| **Finance Reviewer** | Full | Approve | View | Approve | View | Full | View | Full | View |
| **Manager** | Own/Team | Own/Team | Own/Team | Own/Team | Own | View Own | View | Own/Team | None |
| **Employee** | Own | Own | Own | Own | Own | View Own | None | Own | None |
| **Auditor** | View | View | View | View | View | View | View | Full | None |

## Access Scope Rules

### Scope Levels

1. **Self (Own)**: User can only see their own records
2. **Team**: User can see records of their direct reports
3. **Department**: User can see all records in their department
4. **Branch**: User can see all records in their branch
5. **Company**: User can see all records in their company
6. **Global**: User can see all records across all companies

### Scope by Resource

| Resource | Default Scope | Configurable |
|----------|--------------|-------------|
| Expense Claims | Own | Yes (Team/Dept) |
| Travel Requests | Own | Yes (Team/Dept) |
| Cash Advances | Own | Yes (Team/Dept) |
| Receipts | Own | Yes |
| Reimbursements | Own | Yes |
| Policies | Company | No |
| Reports | Scope-dependent | Yes |
| Settings | Company | No |

## Approval Hierarchy

### Expense Claim Approval Flow

```
Employee submits claim
        ↓
Manager reviews (Level 1)
        ↓ (if amount > threshold)
Finance reviews (Level 2)
        ↓
Approved for payment
        ↓
Reimbursement processed
```

### Travel Request Approval Flow

```
Employee submits request
        ↓
Manager approves
        ↓ (if cost > threshold)
Finance approves budget
        ↓
Travel authorized
        ↓
Booking arranged
        ↓
Post-trip expense claim
```

### Cash Advance Approval Flow

```
Employee requests advance
        ↓
Manager approves
        ↓
Finance approves & issues
        ↓
Employee settles with expense claim
        ↓
Unused balance recovered
```

## Segregation of Duties (SOD)

### Key SOD Rules

| Rule ID | Description | Prevented Roles |
|---------|------------|----------------|
| ET_SOD_001 | Cannot approve own expense | Creator, Submitter |
| ET_SOD_002 | Cannot pay own reimbursement | Finance, Approver |
| ET_SOD_003 | Cannot create advance for self | Finance |
| ET_SOD_004 | Audit cannot modify | Auditor |

## Field-Level Security

### Sensitive Fields

| Field | Visibility | Editable By |
|-------|-----------|-------------|
| `approved_amount` | Finance | Finance |
| `payment_reference` | Finance | Finance |
| `bank_account` | Self, Finance | Self, Finance |
| `rejection_reason` | All | Approver |
| `override_approved_by` | Finance | Finance |
| `internal_notes` | Finance, Admin | Finance, Admin |

## Audit Requirements

### Tracked Actions

| Action | Fields Logged | Always Logged |
|--------|--------------|--------------|
| CREATE | All fields | Yes |
| UPDATE | Changed fields | Yes |
| SUBMIT | Status, submitter | Yes |
| APPROVE | Approver, timestamp | Yes |
| REJECT | Rejecter, reason | Yes |
| DELETE | All fields | Yes |
| VIEW | Viewer, timestamp | Optional |
| EXPORT | Exporter, scope | Yes |

### Audit Retention

- Minimum: 7 years (configurable)
- Archival: After 2 years to cold storage
- Access: Auditors, Compliance, Admin