# Finance Permission Matrix
=========================

## Role-Based Access Control for Finance Module

This document defines the complete RBAC model for the WHDASH Financial Management module.

---

## Finance Roles

| Role | Description | Access Level |
|------|-------------|---------------|
| Global Admin | Full system access | All |
| Finance Admin | Full finance access | All finance |
| CFO | Executive finance view + approval | All finance + approval |
| Finance Controller | Financial control + close | All finance + control |
| Chief Accountant | Day-to-day accounting | All accounting |
| AR Manager | Receivables management | AR focus |
| AP Manager | Payables management | AP focus |
| Treasury Manager | Cash + banking | Treasury focus |
| Tax Manager | Tax compliance | Tax focus |
| Asset Accountant | Asset management | Assets focus |
| Budget Manager | Budget management | Budget focus |
| Branch Finance Manager | Branch-level finance | Branch scope |
| Financial Auditor | Audit access | Read-only |
| Read-only Executive | Dashboard viewing | View dashboards |

---

## Permission Matrix

### Chart of Accounts

| Permission | Admin | CFO | Controller | Accountant | Auditor |
|------------|-------|-----|------------|------------|---------|
| accounts.view | ✓ | ✓ | ✓ | ✓ | ✓ |
| accounts.create | ✓ | ✓ | ✓ | ✓ | ✗ |
| accounts.edit | ✓ | ✓ | ✓ | ✓ | ✗ |
| accounts.delete | ✓ | ✗ | ✓ | ✗ | ✗ |

### Journal Entries

| Permission | Admin | CFO | Controller | Accountant | Auditor |
|------------|-------|-----|------------|------------|---------|
| journals.view | ✓ | ✓ | ✓ | ✓ | ✓ |
| journals.create | ✓ | ✓ | ✓ | ✓ | ✗ |
| journals.edit | ✓ | ✓ | ✓ | ✓ (own draft) | ✗ |
| journals.post | ✓ | ✓ | ✓ | ✓ | ✗ |
| journals.reverse | ✓ | ✓ | ✓ | ✗ | ✗ |
| journals.approve | ✓ | ✓ | ✓ | ✗ | ✗ |

### Accounts Receivable

| Permission | Admin | CFO | Controller | AR Manager | Accountant | Auditor |
|------------|-------|-----|------------|------------|------------|---------|
| ar_invoices.view | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| ar_invoices.create | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| ar_invoices.post | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| ar_invoices.approve | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| ar_receipts.view | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| ar_receipts.create | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| ar_receipts.post | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |

### Accounts Payable

| Permission | Admin | CFO | Controller | AP Manager | Accountant | Auditor |
|------------|-------|-----|------------|------------|------------|---------|
| ap_bills.view | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| ap_bills.create | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| ap_bills.post | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| ap_payments.view | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| ap_payments.create | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| ap_payments.post | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| ap_payments.approve | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |

### Fixed Assets

| Permission | Admin | CFO | Controller | Asset Accountant | Auditor |
|------------|-------|-----|------------|------------------|---------|
| assets.view | ✓ | ✓ | ✓ | ✓ | ✓ |
| assets.create | ✓ | ✓ | ✓ | ✓ | ✗ |
| assets.edit | ✓ | ✓ | ✓ | ✓ | ✗ |
| assets.post | ✓ | ✓ | ✓ | ✓ | ✗ |
| assets.transfer | ✓ | ✓ | ✓ | ✓ | ✗ |
| assets.dispose | ✓ | ✓ | ✓ | ✓ | ✗ |
| depreciation.view | ✓ | ✓ | ✓ | ✓ | ✓ |
| depreciation.run | ✓ | ✓ | ✓ | ✓ | ✗ |
| depreciation.post | ✓ | ✓ | ✓ | ✓ | ✗ |

### Cash & Bank

| Permission | Admin | CFO | Controller | Treasury | Accountant | Auditor |
|------------|-------|-----|------------|----------|------------|---------|
| bank_accounts.view | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| bank_accounts.create | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| bank_accounts.edit | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |
| transfers.view | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| transfers.create | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| reconciliation.view | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| reconciliation.create | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |

### Cost & Profit Centers

| Permission | Admin | CFO | Controller | Accountant | Auditor |
|------------|-------|-----|------------|------------|---------|
| cost_centers.view | ✓ | ✓ | ✓ | ✓ | ✓ |
| cost_centers.create | ✓ | ✓ | ✓ | ✓ | ✗ |
| cost_centers.edit | ✓ | ✓ | ✓ | ✓ | ✗ |
| profit_centers.view | ✓ | ✓ | ✓ | ✓ | ✓ |
| profit_centers.create | ✓ | ✓ | ✓ | ✓ | ✗ |

### Budgeting

| Permission | Admin | CFO | Controller | Budget Manager | Accountant | Auditor |
|------------|-------|-----|------------|----------------|------------|---------|
| budgets.view | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| budgets.create | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| budgets.edit | ✓ | ✓ | ✓ | ✓ (own draft) | ✓ (own draft) | ✗ |
| budgets.approve | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |

### Tax Management

| Permission | Admin | CFO | Controller | Tax Manager | Accountant | Auditor |
|------------|-------|-----|------------|-------------|------------|---------|
| tax.view | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| tax.create | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| tax.edit | ✓ | ✓ | ✓ | ✓ | ✓ | ✗ |
| tax.approve | ✓ | ✓ | ✓ | ✓ | ✗ | ✗ |

### Fiscal Management

| Permission | Admin | CFO | Controller | Accountant | Auditor |
|------------|-------|-----|------------|------------|---------|
| fiscal_years.view | ✓ | ✓ | ✓ | ✓ | ✓ |
| fiscal_years.create | ✓ | ✓ | ✓ | ✓ | ✗ |
| fiscal_years.close | ✓ | ✓ | ✓ | ✗ | ✗ |
| fiscal_years.reopen | ✓ | ✗ | ✓ | ✗ | ✗ |

### Financial Close

| Permission | Admin | CFO | Controller | Auditor |
|------------|-------|-----|------------|---------|
| close.view | ✓ | ✓ | ✓ | ✓ |
| close.manage | ✓ | ✓ | ✓ | ✗ |
| close.close | ✓ | ✓ | ✓ | ✗ |
| close.reopen | ✓ | ✗ | ✓ | ✗ |

### Audit

| Permission | Admin | CFO | Controller | Auditor |
|------------|-------|-----|------------|---------|
| audit.view | ✓ | ✓ | ✓ | ✓ |
| audit.export | ✓ | ✓ | ✓ | ✓ |
| audit.view_financial | ✓ | ✓ | ✓ | ✓ |

### Reports & Dashboards

| Permission | Admin | CFO | Controller | Executive | Auditor |
|------------|-------|-----|------------|----------|---------|
| reports.view | ✓ | ✓ | ✓ | ✓ | ✓ |
| reports.export | ✓ | ✓ | ✓ | ✓ | ✓ |
| dashboard.view | ✓ | ✓ | ✓ | ✓ | ✓ |
| dashboard.cfo | ✓ | ✓ | ✓ | ✗ | ✗ |
| dashboard.ar | ✓ | ✓ | ✓ | ✗ | ✗ |
| dashboard.ap | ✓ | ✓ | ✓ | ✗ | ✗ |

---

## Scope-Based Restrictions

### Branch-Level Access
- Users can be restricted to specific branches
- Transactions can only be created for user's assigned branches
- Reports can be filtered by branch scope

### Company-Level Access
- Multi-entity users can access multiple companies
- Company switcher available for multi-company users

### Period-Based Restrictions
- Users cannot post to closed periods
- Only authorized users can reopen periods
- Audit logs visible for all accessible periods

---

## Approval Thresholds

| Transaction Type | Amount Range | Requires Approval |
|-----------------|--------------|------------------|
| Journal Entry | < 10,000 | No |
| Journal Entry | 10,000 - 50,000 | AR Manager |
| Journal Entry | > 50,000 | CFO |
| Customer Invoice | < 25,000 | No |
| Customer Invoice | 25,000 - 100,000 | AR Manager |
| Customer Invoice | > 100,000 | CFO |
| Supplier Payment | < 25,000 | No |
| Supplier Payment | 25,000 - 100,000 | AP Manager |
| Supplier Payment | > 100,000 | CFO |
| Journal Reversal | Any | Controller |
| Period Reopen | Any | Controller |
| Budget Revision | > 10% change | CFO |

---

## Segregation of Duties Matrix

| Role 1 | Role 2 | Can Be Same Person? |
|---------|--------|-------------------|
| Journal Creator | Journal Approver | No |
| AR Creator | AR Approver | No |
| AP Creator | AP Approver | No |
| Payment Creator | Payment Approver | No |
| Bank Account Editor | Reconciliation Approver | No |
| Period Close | Period Reopen | No |
| Tax Creator | Tax Approver | No |
| Budget Creator | Budget Approver | No |

---

## Data Field Restrictions

| Field | Visible To | Editable By |
|-------|------------|--------------|
| Account Balance | All Finance | System Only |
| Journal Posted Lines | All Finance | No One |
| Bank Account Number | Treasury, Admin | Treasury |
| Tax Rate | Tax Manager, Admin | Tax Manager |
| Customer Credit Limit | AR Manager, Admin | AR Manager |
| Supplier Bank Details | Treasury, Admin | Treasury |
| Budget Locked Flag | Budget Manager, Admin | Controller |
| Period Status | All Finance | Controller |
