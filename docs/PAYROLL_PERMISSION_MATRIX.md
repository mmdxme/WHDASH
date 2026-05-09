# WHDASH Payroll Module - Permission Matrix

## Overview

This document defines the complete permission matrix for the WHDASH Payroll Module. The system implements Role-Based Access Control (RBAC) with granular permissions at the resource and action level.

## Permission Structure

```
payroll.<resource>.<action>

Examples:
- payroll.dashboard.view
- payroll.processing.create
- payroll.payslips.generate
```

## Resource-Action Matrix

### Dashboard & Overview

| Resource | View | Executive | Processing | Variance | Overtime | Loan | Compliance |
|----------|------|-----------|------------|----------|----------|------|-----------|
| dashboard | ✓ | | | | | | |
| executive_dashboard | ✓ | ✓ | | | | | |
| processing_dashboard | ✓ | | ✓ | | | | |
| variance_dashboard | ✓ | | | ✓ | | | |
| overtime_dashboard | ✓ | | | | ✓ | | |
| loan_dashboard | ✓ | | | | | ✓ | |
| compliance_dashboard | ✓ | | | | | | ✓ |

### Setup

| Resource | View | Create | Edit | Delete |
|----------|------|--------|------|--------|
| setup | ✓ | | ✓ | |
| components | ✓ | ✓ | ✓ | ✓ |
| groups | ✓ | ✓ | ✓ | ✓ |
| profiles | ✓ | ✓ | ✓ | ✓ |
| calendar | ✓ | ✓ | ✓ | ✓ |

### Periods

| Resource | View | Create | Edit | Delete | Lock | Unlock | Close |
|----------|------|--------|------|--------|------|--------|-------|
| periods | ✓ | ✓ | | | | | |
| periods.lock | | | | | ✓ | | |
| periods.unlock | | | | | | ✓ | |
| periods.close | | | | | | | ✓ |

### Processing

| Resource | View | Create | Calculate | Validate | Add Employees |
|----------|------|--------|----------|---------|--------------|
| processing | ✓ | | | | |
| runs | ✓ | ✓ | | | |
| processing.calculate | | | ✓ | | |
| processing.validate | | | | ✓ | |
| add_employees | | | | | ✓ |

### Review & Approval

| Resource | View | Approve | Reject | Return |
|----------|------|---------|--------|--------|
| review | ✓ | | | |
| approval | ✓ | ✓ | ✓ | |
| review.approve | | ✓ | | |
| review.reject | | | ✓ | |
| review.return | | | | ✓ |

### Payslips

| Resource | View | Generate | Approve | Release | Download | Email |
|----------|------|----------|---------|---------|----------|-------|
| payslips | ✓ | | | | | |
| payslips.generate | | ✓ | | | | |
| payslips.approve | | | ✓ | | | |
| payslips.release | | | | ✓ | | |
| payslips.download | | | | | ✓ | |
| payslips.email | | | | | | ✓ |

### Loans & Advances

| Resource | View | Create | Edit | Delete | Approve | Suspend |
|----------|------|--------|------|--------|---------|----------|
| loans | ✓ | | | | | |
| loans.create | | ✓ | | | | |
| loans.edit | | | ✓ | | | |
| loans.delete | | | | ✓ | | |
| loans.approve | | | | | ✓ | |
| loans.suspend | | | | | | ✓ |
| advances | ✓ | | | | | |
| advances.create | | ✓ | | | | |
| advances.edit | | | ✓ | | | |
| advances.delete | | | | ✓ | | |

### Retro & Arrears

| Resource | View | Create | Edit | Delete | Approve |
|----------|------|--------|------|--------|---------|
| retro | ✓ | | | | |
| retro.create | | ✓ | | | |
| retro.edit | | | ✓ | | |
| retro.delete | | | | ✓ | |
| retro.approve | | | | | ✓ |
| arrears | ✓ | | | | |
| arrears.create | | ✓ | | | |
| arrears.edit | | | ✓ | | |
| arrears.delete | | | | ✓ | |

### Compliance & Controls

| Resource | View | Create | Edit | Delete | Audit | Resolve | Ignore | Escalate |
|----------|------|--------|------|--------|-------|--------|--------|----------|
| compliance | ✓ | | | | | | | |
| compliance.create | | ✓ | | | | | | |
| compliance.edit | | | ✓ | | | | | |
| compliance.delete | | | | ✓ | | | | |
| compliance.audit | | | | | ✓ | | | |
| exceptions | ✓ | | | | | | | |
| exceptions.resolve | | | | | | ✓ | | |
| exceptions.ignore | | | | | | | ✓ | |
| exceptions.escalate | | | | | | | | ✓ |
| audit | ✓ | | | | ✓ | | | |
| controls | ✓ | | | | | | | |

### Finance Integration

| Resource | View | Create | Post | Approve | Reject |
|----------|------|--------|------|---------|--------|
| finance | ✓ | | | | |
| finance.create | | ✓ | | | |
| finance.post | | | ✓ | | |
| finance.approve | | | | ✓ | |
| finance.reject | | | | | ✓ |
| posting | ✓ | | | | |

### HR Integration

| Resource | View | Manage |
|----------|------|--------|
| hr_integration | ✓ | |
| hr_integration.manage | | ✓ |

### Reports

| Resource | View | Export | Create | Edit | Delete | Configure |
|----------|------|--------|--------|------|--------|-----------|
| reports | ✓ | | | | | |
| reports.export | | ✓ | | | | |
| reports.create | | | ✓ | | | |
| reports.edit | | | | ✓ | | |
| reports.delete | | | | | ✓ | |
| export | ✓ | ✓ | | | | ✓ |
| summary_report | ✓ | ✓ | | | | |
| earnings_report | ✓ | ✓ | | | | |
| deductions_report | ✓ | ✓ | | | | |
| overtime_report | ✓ | ✓ | | | | |
| loan_report | ✓ | ✓ | | | | |
| variance_report | ✓ | ✓ | | | | |
| compliance_report | ✓ | ✓ | | | | |
| audit_report | ✓ | ✓ | | | | |

### Workflow

| Resource | View | Approve | Reject | Delegate |
|----------|------|---------|--------|----------|
| approvals | ✓ | | | |
| approvals.approve | | ✓ | | |
| approvals.reject | | | ✓ | |
| approvals.delegate | | | | ✓ |
| approval_rules | ✓ | | | |
| delegations | ✓ | | | |
| sla | ✓ | | | |
| escalations | ✓ | | | |

### Settings

| Resource | View | Edit |
|----------|------|------|
| settings | ✓ | |
| notification_settings | ✓ | ✓ |
| integration_settings | ✓ | ✓ |

### Special Permissions

| Permission | Description |
|-----------|-------------|
| lock | Lock payroll periods and runs |
| unlock | Unlock payroll periods |
| close | Close payroll periods |
| recalculate | Trigger payroll recalculation |
| bulk_approve | Batch approve records |
| sensitive_data | View salary totals, bank details |
| export_bank_file | Export bank transfer files |
| view_audit_trail | View audit logs |

## Role Definitions

### Global Admin
- Full system access
- All permissions granted
- Cannot be restricted by RBAC

### Payroll Admin
- Full payroll module access
- Can manage all payroll functions
- Cannot override segregation of duties

### Payroll Manager
- Process payroll runs
- Review and approve payroll
- Manage loans and advances
- View all reports
- Cannot access system settings

### Payroll Officer
- Data entry for payroll
- Process payroll runs
- Cannot approve or reject
- Cannot access sensitive data

### HR Reviewer
- View payroll reports
- View compliance dashboards
- Cannot process or approve

### Finance Reviewer
- View payroll summaries
- View finance postings
- Export reports
- Cannot process payroll

### Auditor
- View audit trail
- View compliance results
- Export audit reports
- Cannot modify data

### Employee Self-Service
- View own payslip
- View own leave balance
- Cannot access other employee data
- Cannot process payroll

## Segregation of Duties (SOD) Rules

| Rule ID | Description | Create Permission | Approve Permission |
|---------|-------------|-------------------|-------------------|
| PAY_SOD_001 | Payroll Processing | payroll.processing | payroll.review.approve |
| PAY_SOD_002 | Period Lock/Unlock | payroll.periods.lock | payroll.periods.unlock |
| PAY_SOD_003 | Loan Approval | payroll.loans.create | payroll.loans.approve |
| PAY_SOD_004 | Retro Approval | payroll.retro.create | payroll.retro.approve |

## Multi-Language Support

All permissions and resources support internationalization:

| Language | Code | Direction |
|----------|------|-----------|
| English | en | LTR |
| Arabic | ar | RTL |
| Persian/Farsi | fa | RTL |
| Russian | ru | LTR |
| Hindi | hi | LTR |
| Spanish | es | LTR |
| Chinese | zh | LTR |
| German | de | LTR |

## Implementation Notes

1. Permissions are checked at the route level using decorators
2. Super admin (role_name = 'Global Admin') bypasses all permission checks
3. Permission cache is invalidated on role changes
4. Audit logging occurs for all permission-checks and successful operations
5. Sensitive field access (salary totals, bank details) requires explicit permission
