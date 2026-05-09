# Finance Audit and Controls

## Overview

This document outlines the comprehensive internal controls, audit procedures, and compliance measures implemented in the WHDASH Financial Management module to ensure data integrity, regulatory compliance, and fraud prevention.

---

## 1. Segregation of Duties Policy

### Principle

No single individual should have control over all phases of a financial transaction. This prevents errors and fraud by requiring multiple approvals and oversight.

### Key Segregation Matrix

| Transaction Type | Initiator | Approver | Executor | Reviewer |
|------------------|-----------|----------|----------|----------|
| Journal Entry | Accountant | Controller | Accountant | Auditor |
| AR Invoice | AR Clerk | AR Manager | AR Clerk | Controller |
| AR Receipt | AR Clerk | AR Manager | AR Clerk | Controller |
| AP Bill | AP Clerk | AP Manager | AP Clerk | Controller |
| AP Payment | AP Clerk | FIN Manager | Treasury | Controller |
| Asset Disposal | Asset Mgr | CFO | Controller | Auditor |
| Budget Revision | Budget Owner | CFO | Controller | Auditor |
| Period Close | Accountant | Controller | Controller | CFO |

### Implementation

```
┌─────────────────────────────────────────────────────────────────┐
│                    SEGREGATION ENFORCEMENT                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  User Role: ACCOUNTANT                                           │
│  ─────────────────────                                          │
│  ✓ Can CREATE journal entries                                   │
│  ✓ Can EDIT draft journal entries                               │
│  ✓ Can POST journal entries                                     │
│  ✗ CANNOT DELETE any journal entries                            │
│  ✗ CANNOT approve journal entries (requires Controller)         │
│  ✗ CANNOT access AP functions                                  │
│  ✗ CANNOT access Asset disposal                                │
│                                                                  │
│  User Role: CONTROLLER                                          │
│  ───────────────────────                                        │
│  ✓ Can CREATE/EDIT/POST/DELETE journals                       │
│  ✓ Can approve journal entries                                  │
│  ✓ Can close fiscal periods                                    │
│  ✓ Can view all reports                                         │
│  ✗ CANNOT process payments (Treasury only)                      │
│  ✗ CANNOT approve asset disposals (CFO only)                   │
│                                                                  │
│  User Role: CFO                                                 │
│  ─────────────────                                              │
│  ✓ Full access to all finance functions                        │
│  ✓ Can approve high-value transactions                          │
│  ✓ Can override controls in emergencies                         │
│  ✓ Final sign-off on financial statements                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Posting Controls and Validation Rules

### 2.1 Journal Entry Validation

Every journal entry MUST pass all validation checks before posting:

#### Balance Validation
```python
def validate_balance(journal_lines):
    """
    CRITICAL: Total Debits MUST equal Total Credits
    """
    total_debit = sum(line.debit for line in journal_lines)
    total_credit = sum(line.credit for line in journal_lines)
    
    if total_debit != total_credit:
        raise ValidationError(
            f"Journal is not balanced: "
            f"Debits {total_debit:,.2f} != Credits {total_credit:,.2f}"
        )
```

#### Account Validation
```python
def validate_accounts(journal_lines):
    """
    All accounts must:
    1. Exist in chart of accounts
    2. Be marked as active
    3. Have posting allowed = True
    """
    for line in journal_lines:
        account = get_account(line.account_id)
        
        if not account:
            raise ValidationError(f"Account ID {line.account_id} does not exist")
        
        if not account.is_active:
            raise ValidationError(f"Account {account.code} is inactive")
        
        if not account.is_posting_allowed:
            raise ValidationError(f"Posting not allowed to account {account.code}")
```

#### Period Validation
```python
def validate_period(journal_date, period_id):
    """
    Journal date must fall within an open fiscal period
    """
    period = get_period(period_id)
    
    if not period:
        raise ValidationError(f"Period {period_id} does not exist")
    
    if period.status == 'Closed':
        raise ValidationError(f"Period {period.name} is closed")
    
    if period.status == 'Locked':
        raise ValidationError(f"Period {period.name} is locked")
    
    if journal_date < period.start_date or journal_date > period.end_date:
        raise ValidationError(f"Journal date must be within period dates")
```

#### Date Sequence Validation
```python
def validate_date_sequence(journal_date):
    """
    Journal date cannot be:
    1. In the future (except first day)
    2. Before company founding date
    3. More than 30 days in the past (requires special approval)
    """
    today = datetime.now().date()
    
    if journal_date > today + timedelta(days=1):
        raise ValidationError("Journal date cannot be in the future")
    
    if journal_date < company.founding_date:
        raise ValidationError("Journal date before company founding")
```

### 2.2 Invoice Validation

#### AR Invoice Controls
```
┌─────────────────────────────────────────────────────────────────┐
│                    AR INVOICE VALIDATION                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✓ Customer exists and is active                                │
│  ✓ Customer credit limit not exceeded                           │
│  ✓ Invoice date is valid (not future)                           │
│  ✓ Due date is after invoice date                               │
│  ✓ Payment terms are valid                                      │
│  ✓ Tax code exists and is active                                │
│  ✓ At least one line item                                       │
│  ✓ Line amounts are positive                                    │
│  ✓ Tax calculation is correct                                   │
│  ✓ Total = Sum of lines + Tax                                   │
│  ✓ Revenue account is valid                                      │
│  ✓ Receivable account is valid                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Credit Limit Check
```python
def check_credit_limit(customer_id, new_invoice_amount):
    """
    Prevent invoices that would exceed customer credit limit
    """
    customer = get_customer(customer_id)
    current_balance = get_ar_balance(customer_id)
    
    new_balance = current_balance + new_invoice_amount
    
    if new_balance > customer.credit_limit:
        raise CreditLimitExceeded(
            f"Credit limit exceeded: "
            f"Current {current_balance:,.2f} + "
            f"New {new_invoice_amount:,.2f} = "
            f"New Balance {new_balance:,.2f} > "
            f"Limit {customer.credit_limit:,.2f}"
        )
```

#### AP Bill Validation
```
✓ Supplier exists and is active
✓ Bill date is valid (not future)
✓ Due date is after bill date
✓ Tax code is valid
✓ Line amounts are positive
✓ Tax calculation is correct
✓ Expense account is valid
✓ 3-way match required (PO, GRN, Invoice)
```

### 2.3 Payment Validation

```
┌─────────────────────────────────────────────────────────────────┐
│                    PAYMENT VALIDATION                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ✓ Payment amount does not exceed invoice amount                 │
│  ✓ Payment not duplicate (check reference number)                │
│  ✓ Bank account exists and is active                             │
✓ Sufficient funds available in bank account                       │
│  ✓ Payment method is valid                                       │
│  ✓ Approval obtained per matrix                                   │
│  ✓ Segregation: Initiator ≠ Approver                            │
│                                                                  │
│  Amount-Based Approval:                                          │
│  ≤ 10,000: AP Manager approval                                  │
│  10,001 - 50,000: Finance Manager approval                       │
│  > 50,000: CFO approval                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Period Lock Policies

### 3.1 Period Status Workflow

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│   OPEN   │────▶│ CLOSED   │────▶│ LOCKED   │────▶│ARCHIVED  │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                │                 │                │
     │                │                 │                │
     │ Can post       │ Cannot post     │ No changes     │ Historical
     │ Can adjust     │ adjustments     │ Audit trail    │ reference
     │ Full editing   │ Limited edit    │ view only      │ only
     │                │                 │                │
     ▼                ▼                 ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PERIOD STATUS RULES                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  OPEN → CLOSED:                                                 │
│  ─────────────────                                               │
│  1. All transactions for period posted                            │
│  2. All reconciliations completed                                │
│  3. Controller approval obtained                                 │
│  4. Click "Close Period" button                                  │
│                                                                  │
│  CLOSED → LOCKED:                                               │
│  ───────────────────                                             │
│  1. Month-end reports generated                                 │
│  2. Financial statements reviewed                               │
│  3. CFO approval obtained                                       │
│  4. Click "Lock Period" button                                   │
│                                                                  │
│  LOCKED → ARCHIVED:                                             │
│  ─────────────────────                                           │
│  1. Year fully closed                                            │
│  2. External audit completed                                    │
│  3. Click "Archive Year" button                                 │
│                                                                  │
│  REVERSING RESTRICTIONS:                                        │
│  ────────────────────────                                        │
│  CLOSED → OPEN: Controller approval + reason                    │
│  LOCKED → CLOSED: CFO approval + reason                         │
│  ARCHIVED: Cannot reverse (permanent)                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Lock Date Configuration

| Period Type | Auto-Lock Date | Manual Override |
|-------------|----------------|-----------------|
| Monthly | 5th of following month | Controller |
| Quarterly | 15th of following month | CFO |
| Annual | 60 days after year end | CFO + Audit |

### 3.3 Period Close Checklist

```markdown
## Monthly Close Checklist

### Pre-Close Tasks (Days 1-3)
- [ ] All departments submit journal entries for prior month
- [ ] AR department confirms all invoices posted
- [ ] AP department confirms all bills posted
- [ ] Bank reconciliations completed

### Close Tasks (Days 3-5)
- [ ] Run trial balance - verify debits = credits
- [ ] Review AR aging - follow up on collections
- [ ] Review AP aging - schedule payments
- [ ] Run depreciation
- [ ] Calculate VAT liability
- [ ] Review account reconciliations

### Approval (Days 5-7)
- [ ] Controller reviews trial balance
- [ ] Controller approves period close
- [ ] Period status changed to Closed

### Post-Close (Day 7+)
- [ ] Generate financial statements
- [ ] CFO review
- [ ] Lock period for audit
```

---

## 4. Approval Workflow Controls

### 4.1 Multi-Level Approval Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│                    APPROVAL WORKFLOW                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  JOURNAL ENTRY APPROVAL:                                        │
│  ──────────────────────────                                     │
│                                                                  │
│  Amount ≤ 50,000:                                               │
│  [ACCOUNTANT] ──▶ [CONTROLLER] ──▶ POSTED                      │
│                                                                  │
│  Amount 50,001 - 200,000:                                       │
│  [ACCOUNTANT] ──▶ [FIN MANAGER] ──▶ [CONTROLLER] ──▶ POSTED   │
│                                                                  │
│  Amount > 200,000:                                               │
│  [ACCOUNTANT] ──▶ [FIN MANAGER] ──▶ [CFO] ──▶ POSTED         │
│                                                                  │
│  ───────────────────────────────────────────────────────────     │
│                                                                  │
│  PAYMENT APPROVAL:                                               │
│  ─────────────────                                               │
│                                                                  │
│  Amount ≤ 10,000:                                               │
│  [AP CLERK] ──▶ [AP MANAGER] ──▶ [TREASURY]                   │
│                                                                  │
│  Amount 10,001 - 50,000:                                        │
│  [AP CLERK] ──▶ [AP MANAGER] ──▶ [FIN MANAGER] ──▶ [TREASURY]│
│                                                                  │
│  Amount > 50,000:                                               │
│  [AP CLERK] ──▶ [AP MANAGER] ──▶ [FIN MANAGER] ──▶ [CFO]     │
│  ──▶ [TREASURY]                                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Workflow Enforcement

```python
class ApprovalWorkflow:
    """
    Enforce multi-level approval based on transaction type and amount
    """
    
    APPROVAL_CHAINS = {
        'journal': {
            'tier1': ('ACCOUNTANT', '≤50000'),
            'tier2': ('FIN_MANAGER', '50001-200000'),
            'tier3': ('CFO', '>200000'),
        },
        'payment': {
            'tier1': ('AP_MANAGER', '≤10000'),
            'tier2': ('FIN_MANAGER', '10001-50000'),
            'tier3': ('CFO', '>50000'),
        },
        'asset_disposal': {
            'all': ('CFO', '>0'),  # All disposals require CFO
        },
        'budget_revision': {
            'increase': ('CFO', '>0'),
            'decrease': ('FIN_MANAGER', '>0'),
        },
    }
    
    def require_approval(self, transaction_type, amount, user_role):
        chain = self.get_approval_chain(transaction_type, amount)
        
        if user_role not in chain:
            raise InsufficientPermission(
                f"User role {user_role} cannot approve this transaction. "
                f"Required: {chain}"
            )
        
        # Log approval attempt
        self.log_approval(
            transaction_type=transaction_type,
            amount=amount,
            approver_role=user_role,
            status='APPROVED'
        )
```

### 4.3 Approval Audit Trail

Every approval action is logged:

```python
class ApprovalLog:
    """
    Immutable log of all approval actions
    """
    fields = [
        'approval_id',           # Unique identifier
        'transaction_type',       # Journal/Payment/Invoice etc
        'transaction_id',         # Reference to transaction
        'transaction_amount',     # Amount for approval matrix
        'approver_user_id',       # Who approved
        'approver_role',          # Role at time of approval
        'approval_level',         # Which tier in chain
        'action',                 # APPROVED/REJECTED
        'comments',               # Approver comments
        'timestamp',              # Exact time
        'ip_address',             # User's IP
        'user_agent',             # Browser/client info
    ]
```

---

## 5. Audit Trail Coverage

### 5.1 Tracked Events

| Event Category | Events Tracked |
|----------------|----------------|
| Journal Entries | Create, Edit, Post, Unpost, Delete, Reverse |
| Invoices | Create, Edit, Post, Void, Payment Applied, Credit Note |
| Payments | Create, Edit, Post, Cancel, Stop Payment |
| Master Data | Create, Edit, Delete, Status Change |
| User Management | Login, Logout, Role Change, Permission Change |
| System | Config Changes, Period Changes, Archive |

### 5.2 Audit Log Schema

```sql
CREATE TABLE finance_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    event_type TEXT NOT NULL,
    event_category TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    username TEXT NOT NULL,
    user_role TEXT NOT NULL,
    old_values TEXT,           -- JSON of previous state
    new_values TEXT,           -- JSON of new state
    ip_address TEXT,
    user_agent TEXT,
    workstation TEXT,
    comments TEXT,
    approval_id INTEGER,       -- Link to approval if applicable
    session_id TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_audit_entity ON finance_audit_log(entity_type, entity_id);
CREATE INDEX idx_audit_user ON finance_audit_log(user_id);
CREATE INDEX idx_audit_timestamp ON finance_audit_log(event_timestamp);
CREATE INDEX idx_audit_event_type ON finance_audit_log(event_type);
```

### 5.3 Sample Audit Entries

```json
{
  "event_type": "JOURNAL_POSTED",
  "entity_type": "finance_journals",
  "entity_id": 123,
  "user_id": 5,
  "username": "accountant",
  "user_role": "ACCOUNTANT",
  "old_values": {"status": "Draft"},
  "new_values": {"status": "Posted"},
  "transaction_details": {
    "journal_number": "JE-2026-015",
    "total_amount": 25000.00,
    "line_count": 2
  },
  "timestamp": "2026-04-15T14:32:15.123Z",
  "ip_address": "192.168.1.100"
}

{
  "event_type": "PAYMENT_APPROVED",
  "entity_type": "finance_supplier_payments",
  "entity_id": 89,
  "user_id": 3,
  "username": "fin_manager",
  "user_role": "FIN_MANAGER",
  "approval_level": "tier2",
  "comments": "Approved for payment - verified invoice matches PO",
  "transaction_details": {
    "payment_number": "PMT-2026-045",
    "amount": 45000.00,
    "supplier": "Emirates Supplies LLC"
  }
}
```

### 5.4 Audit Retention Policy

| Retention Period | Justification |
|------------------|----------------|
| 7 years | UAE tax authority requirement |
| 10 years | Audit trail for long-term assets |
| Permanent | Year-end financial statements |
| 3 years | System logs after archive |

---

## 6. Fraud Prevention Measures

### 6.1 Detection Controls

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRAUD DETECTION SYSTEM                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  REAL-TIME MONITORING:                                          │
│  ────────────────────────                                       │
│                                                                  │
│  • Unusual journal entry patterns (after hours, weekends)         │
│  • Large transactions (>100,000 AED) flagged                     │
│  • Round number transactions (suspicious)                        │
│  • Transactions without proper documentation                     │
│  • Rapid consecutive entries (potential collusion)               │
│  • User login from multiple locations                            │
│                                                                  │
│  ───────────────────────────────────────────────────────────     │
│                                                                  │
│  PATTERN ANALYSIS:                                              │
│  ────────────────                                               │
│                                                                  │
│  • Vendorinvoice to payment < 24 hours (bypassing approval)     │
│  • Customer refunds without return goods                         │
│  • Write-offs without proper justification                      │
│  • Journal entries modifying closed periods                     │
│  • Bank reconciling items older than 30 days                    │
│                                                                  │
│  ───────────────────────────────────────────────────────────     │
│                                                                  │
│  RECONCILIATION CONTROLS:                                       │
│  ──────────────────────────                                     │
│                                                                  │
│  • Daily: Bank GL vs Bank Statement                              │
│  • Weekly: Subledger vs GL (AR and AP)                         │
│  • Monthly: Intercompany eliminations                           │
│  • Quarterly: Physical asset verification                       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Preventive Controls

| Control | Description | Implementation |
|---------|-------------|----------------|
| Dual Control | Two people required for sensitive ops | Payment processing, bank transfers |
| Rotation | Periodic rotation of duties | AR/AP clerk swap every 6 months |
| Authentication | Strong password + MFA | Required for all finance access |
| Authorization | Role-based access control | Principle of least privilege |
| Limits | Transaction amount limits | Daily payment limit per user |
| Documentation | Supporting docs required | PO + GRN + Invoice match |
| Segmentation | Separate custody of assets | Different people handle cash vs recording |

### 6.3 Red Flag Alerts

The system monitors for these fraud indicators:

```python
RED_FLAGS = [
    # Journal Entry Red Flags
    {'type': 'je_unusual_time', 'condition': 'je.created_hour < 6 OR je.created_hour > 20'},
    {'type': 'je_weekend', 'condition': 'je.created_date IN (Saturday, Sunday)'},
    {'type': 'je_round_amount', 'condition': 'je.amount MOD 1000 = 0 AND je.amount > 10000'},
    {'type': 'je_backdate', 'condition': 'je.date < today - 7'},
    
    # Payment Red Flags
    {'type': 'pmt_rapid', 'condition': 'payment.created < 24 hours after invoice'},
    {'type': 'pmt_new_vendor', 'condition': 'vendor.created_date > today - 30'},
    {'type': 'pmt_same_as_invoice', 'condition': 'payment.amount = invoice.amount'},
    
    # Receipt Red Flags
    {'type': 'rcpt_cash_large', 'condition': 'receipt.payment_method = "Cash" AND amount > 5000'},
    {'type': 'rcpt_unapplied', 'condition': 'receipt.unapplied_days > 30'},
    
    # User Behavior
    {'type': 'user_multiple_login', 'condition': 'user.logged_in_from > 2 locations today'},
    {'type': 'user_after_hours', 'condition': 'user.last_activity > 22:00'},
]
```

---

## 7. Exception Handling Procedures

### 7.1 Exception Categories

| Category | Description | Response Time |
|----------|-------------|---------------|
| Critical | Data integrity issue, potential fraud | Immediate |
| High | Control violation, policy breach | 24 hours |
| Medium | Minor policy deviation | 5 business days |
| Low | Documentation missing | Next close |

### 7.2 Exception Workflow

```
EXCEPTION DETECTED
        │
        ▼
┌─────────────────┐
│  LOG EXCEPTION  │
│  - Who          │
│  - What         │
│  - When         │
│  - Where        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ASSESS SEVERITY│
│  - Critical     │──▶ IMMEDIATE ESCALATION
│  - High        │──▶ 24-HOUR RESPONSE
│  - Medium      │──▶ 5-DAY RESPONSE
│  - Low         │──▶ NEXT CLOSE
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  INVESTIGATE    │
│  - Gather facts │
│  - Interview    │
│  - Review docs  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  RESOLVE        │
│  - Correct      │
│  - Document     │
│  - Prevent      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  CLOSE & REPORT │
│  - Approval     │
│  - Archive      │
│  - Update controls│
└─────────────────┘
```

### 7.3 Emergency Access Procedure

For urgent situations requiring control override:

```markdown
## Emergency Access Procedure

### When to Use
- System down affecting financial close
- Payment needed for critical vendor
- Security incident requiring immediate action

### Procedure

1. **Request** - User calls CFO (or backup if unavailable)
2. **Verbal Approval** - CFO provides verbal approval with reason
3. **Document** - User documents:
   - Date/Time of request
   - CFO name providing approval
   - Reason for emergency
   - Specific action taken
4. **Implement** - User performs necessary action
5. **Follow-up** - Written approval submitted within 24 hours
6. **Review** - CFO reviews action within 48 hours
7. **Close** - Document added to audit file

### Limitations
- Emergency access expires in 24 hours
- Must be followed by proper approval workflow
- Cannot exceed amount limits without CFO + Controller
```

---

## 8. Control Testing Schedule

### 8.1 Testing Frequency

| Control | Test Frequency | Tester | Reviewer |
|---------|---------------|--------|----------|
| Journal posting validation | Per transaction | System | N/A |
| Period close procedures | Monthly | Accountant | Controller |
| Segregation of duties | Quarterly | Audit | Controller |
| Bank reconciliation | Weekly | Treasury | Controller |
| AR aging review | Monthly | AR Manager | Controller |
| AP aging review | Monthly | AP Manager | Controller |
| User access review | Quarterly | IT | Controller |
| Password policy compliance | Monthly | IT | Controller |
| Backup restore test | Quarterly | IT | CFO |
| Disaster recovery test | Annually | IT | CFO |

### 8.2 Control Self-Assessment

```markdown
## Quarterly Control Self-Assessment

### Responsible Party: Controller

#### 1. Journal Entry Controls
- [ ] All journals balanced before posting
- [ ] Period validation enforced
- [ ] Approval workflow followed
- [ ] Audit trail complete

#### 2. Invoice Controls
- [ ] Credit limits enforced
- [ ] Approval workflow followed
- [ ] Tax calculations correct
- [ ] AR aging reviewed weekly

#### 3. Payment Controls
- [ ] Segregation maintained
- [ ] Approval matrix followed
- [ ] Bank reconciliations current
- [ ] Outstanding items investigated

#### 4. Access Controls
- [ ] User access reviewed
- [ ] Inactive accounts disabled
- [ ] Password policy enforced
- [ ] MFA enabled for sensitive roles

### Sign-off
Controller: _______________ Date: ___________
CFO: _______________ Date: ___________
```

---

## 9. Compliance Framework

### 9.1 Regulatory Requirements

| Regulation | Requirement | Implementation |
|------------|-------------|----------------|
| UAE VAT | 15% VAT filing | Tax engine with VAT-STD |
| UAE Corporate Tax | 9% on profits > 375K | Tax calculation (future) |
| IFRS | Financial reporting | Chart of accounts alignment |
| UAE Anti-Money Laundering | KYC for customers | Customer verification |
| Data Protection | Personal data security | Access controls, encryption |

### 9.2 Internal Policies

| Policy | Description | Frequency |
|--------|-------------|-----------|
| Expense Policy | Allowed expense types | Annual review |
| Authorization Matrix | Approval limits | Quarterly review |
| Segregation Policy | Duty separation rules | Annual review |
| Data Retention | How long to keep records | Annual review |
| Incident Response | How to handle breaches | Annual test |

---

## 10. Reporting and Monitoring

### 10.1 Daily Monitoring Reports

```python
DAILY_REPORTS = [
    {
        'name': 'Exception Report',
        'description': 'Transactions requiring review',
        'recipients': ['controller'],
        'schedule': 'Daily 8:00 AM'
    },
    {
        'name': 'Bank Balance Report',
        'description': 'Current cash positions',
        'recipients': ['treasury', 'controller'],
        'schedule': 'Daily 7:00 AM'
    },
    {
        'name': 'Unreconciled Items',
        'description': 'Bank rec exceptions',
        'recipients': ['treasury'],
        'schedule': 'Daily 9:00 AM'
    }
]
```

### 10.2 Weekly Monitoring Reports

```python
WEEKLY_REPORTS = [
    {
        'name': 'AR Aging Report',
        'description': 'Collections status',
        'recipients': ['ar_manager', 'controller'],
        'schedule': 'Monday 8:00 AM'
    },
    {
        'name': 'AP Aging Report',
        'description': 'Payment scheduling',
        'recipients': ['ap_manager', 'controller'],
        'schedule': 'Monday 8:00 AM'
    },
    {
        'name': 'Journal Entry Summary',
        'description': 'All JEs posted',
        'recipients': ['controller'],
        'schedule': 'Monday 9:00 AM'
    }
]
```

### 10.3 Monthly Monitoring Reports

```python
MONTHLY_REPORTS = [
    {
        'name': 'Trial Balance',
        'description': 'Pre-close verification',
        'recipients': ['controller', 'cfo'],
        'schedule': 'Last day of month'
    },
    {
        'name': 'Financial Statements',
        'description': 'P&L, Balance Sheet',
        'recipients': ['cfo', 'board'],
        'schedule': '5th of following month'
    },
    {
        'name': 'VAT Return',
        'description': 'VAT liability',
        'recipients': ['controller', 'cfo', 'tax_authority'],
        'schedule': '28th of following month'
    },
    {
        'name': 'Control Self-Assessment',
        'description': 'Control effectiveness',
        'recipients': ['controller', 'cfo'],
        'schedule': 'End of quarter'
    }
]
```

---

## 11. Incident Response

### 11.1 Incident Classification

| Level | Description | Examples | Response |
|-------|-------------|-----------|----------|
| 1 | Minor | Missing documentation, minor delay | Normal process |
| 2 | Moderate | Policy breach, control gap | 24-hour fix |
| 3 | Major | Data error, unauthorized access | Immediate action |
| 4 | Critical | Fraud, system breach, data loss | Crisis response |

### 11.2 Incident Response Team

```python
INCIDENT_RESPONSE_TEAM = {
    'level_1': ['department_manager'],
    'level_2': ['controller', 'department_manager'],
    'level_3': ['cfo', 'controller', 'it_security'],
    'level_4': ['cfo', 'ceo', 'legal', 'external_auditor']
}
```

### 11.3 Communication Protocol

```markdown
## Incident Communication Protocol

### Level 3+ Incidents

1. **Within 1 hour**: Notify CFO and Controller
2. **Within 4 hours**: Document initial findings
3. **Within 24 hours**: Notify CEO if fraud/serious breach
4. **Within 48 hours**: Notify external auditor if material
5. **Within 72 hours**: File regulatory reports if required

### Communication Template

```
SUBJECT: Finance Incident - [Brief Description]

DATE: [Date/Time]
INCIDENT LEVEL: [1/2/3/4]

SUMMARY:
[What happened]

IMPACT:
[Financial/Operational/Reputational]

ACTIONS TAKEN:
[Immediate response]

NEXT STEPS:
[Investigation plan]

REVIEWED BY: [Name/Date]
APPROVED BY: [Name/Date]
```
