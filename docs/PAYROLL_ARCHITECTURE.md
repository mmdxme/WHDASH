# WHDASH Enterprise Payroll Module Architecture

## Overview

The WHDASH Enterprise Payroll Module is a comprehensive, integrated payroll system designed to meet the needs of medium-to-large enterprises. It provides end-to-end payroll processing capabilities including configuration, calculation, approval workflows, compliance controls, and financial integration.

## System Architecture

### Core Components

```
┌─────────────────────────────────────────────────────────────────┐
│                      WHDASH Application                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  HR Module   │  │Payroll Module│  │Finance Module│         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│         │                  │                  │                    │
│         └──────────────────┼──────────────────┘                    │
│                            │                                       │
│                    ┌───────▼───────┐                               │
│                    │  Shared DB    │                               │
│                    │  (SQLite)     │                               │
│                    └───────────────┘                               │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with WAL mode
- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **Icons**: FontAwesome 6
- **Fonts**: Inter (Google Fonts)

## Module Structure

### Database Tables

The payroll module uses 40+ database tables organized into functional groups:

#### 1. Configuration Tables
| Table | Purpose |
|-------|---------|
| `payroll_components` | Earnings, deductions, allowances configuration |
| `payroll_groups` | Employee grouping for batch processing |
| `payroll_group_members` | Group membership assignments |
| `payroll_profiles` | Employee payroll settings |
| `payroll_profile_components` | Per-employee component amounts |
| `payroll_calendar` | Payroll cycle definitions |
| `payroll_settings` | System configuration |
| `payroll_tax_brackets` | Tax rate configuration |
| `payroll_insurance_rates` | Insurance contribution rates |

#### 2. Period Management Tables
| Table | Purpose |
|-------|---------|
| `payroll_periods` | Monthly payroll periods |
| `payroll_period_locks` | Period lock/unlock tracking |

#### 3. Processing Tables
| Table | Purpose |
|-------|---------|
| `payroll_runs` | Payroll run instances |
| `payroll_run_validations` | Pre-run validation results |
| `payroll_employee_records` | Per-employee payroll results |
| `payroll_employee_earnings` | Itemized earnings |
| `payroll_employee_deductions` | Itemized deductions |
| `payroll_attendance_inputs` | Attendance data for payroll |
| `payroll_overtime_inputs` | Overtime hours for payroll |
| `payroll_leave_impacts` | Leave effect on payroll |
| `payroll_manual_adjustments` | Manual adjustments |
| `payroll_exceptions` | Processing exceptions |

#### 4. Output Tables
| Table | Purpose |
|-------|---------|
| `payroll_payslips` | Generated payslips |
| `payroll_payslip_details` | Payslip line items |
| `payroll_letters` | Payroll letters scaffold |

#### 5. Loan & Advance Tables
| Table | Purpose |
|-------|---------|
| `payroll_loans` | Employee loans |
| `payroll_loan_installments` | Loan repayment schedule |
| `payroll_advances` | Salary advances |

#### 6. Retro & Arrears Tables
| Table | Purpose |
|-------|---------|
| `payroll_retro_adjustments` | Retroactive adjustments |
| `payroll_arrears` | Arrears register |

#### 7. Compliance & Control Tables
| Table | Purpose |
|-------|---------|
| `payroll_compliance_rules` | Validation rule definitions |
| `payroll_compliance_results` | Compliance check results |

#### 8. Finance Integration Tables
| Table | Purpose |
|-------|---------|
| `payroll_finance_postings` | Journal postings |
| `payroll_finance_lines` | Journal line items |
| `payroll_cost_allocations` | Cost center distribution |

#### 9. Workflow Tables
| Table | Purpose |
|-------|---------|
| `payroll_approval_rules` | Approval workflow definitions |
| `payroll_approval_instances` | Active approval records |
| `payroll_approval_delegations` | User delegations |

#### 10. Audit & Logging
| Table | Purpose |
|-------|---------|
| `payroll_audit_log` | Comprehensive audit trail |
| `payroll_export_configs` | Export configurations |
| `payroll_export_history` | Export audit |
| `payroll_flow_notifications` | Flow integration |

## Payroll Processing Flow

```
┌─────────────┐
│ Open Period │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Create Payroll   │◄──── Validation
│ Run              │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Add Employees   │
│ to Run          │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Pre-Run         │◄──── Validations
│ Validation       │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Calculate       │◄──── Components
│ Payroll         │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Review &        │
│ Approve         │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Lock Payroll    │
│ Run             │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Generate        │
│ Payslips        │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│ Close Period    │
└─────────────────┘
```

## Key Features

### 1. Payroll Configuration
- Flexible component definition (earnings, deductions, allowances)
- Multi-language support for component names
- Taxable/insurable flags
- Percentage-based or fixed amount calculations
- GL account mapping

### 2. Period Management
- Monthly payroll periods with auto-date calculation
- Period status lifecycle (Open → Processing → Approved → Locked → Closed)
- Lock/unlock controls with audit trail
- Cutoff date management

### 3. Payroll Processing
- Multi-step payroll runs with validation
- Bulk employee addition
- Component-based calculation engine
- Exception handling and queue
- Variance detection

### 4. Approval Workflow
- Configurable approval rules
- Multi-level approval support
- Delegation capabilities
- SLA tracking
- Escalation support

### 5. Loan Management
- Multiple loan types
- Interest calculation
- Installment scheduling
- Auto-recovery through payroll
- Suspension support

### 6. Retro Processing
- Retroactive adjustment tracking
- Arrears calculation
- Backdated change impact analysis
- Tax implications handling

### 7. Compliance Controls
- Pre-defined validation rules
- SOD (Segregation of Duties) checks
- Exception monitoring
- Audit trail

### 8. Finance Integration
- Journal entry generation
- Cost center allocation
- Branch/entity splitting
- Posting preview

## Security Model

### Role-Based Access Control

| Role | Permissions |
|------|-------------|
| Global Admin | Full access to all features |
| Payroll Admin | Full payroll management |
| Payroll Manager | Process, review, approve |
| Payroll Officer | Data entry, processing |
| HR Reviewer | View reports |
| Finance Reviewer | View, export |
| Auditor | View audit logs |

### Segregation of Duties

- Payroll processor cannot approve own work
- Separate roles for processing vs. approval
- Audit trail for all sensitive operations

## Integration Points

### HR Module Integration
- Employee data synchronization
- Attendance feed
- Leave impact calculation
- Overtime integration
- Employee status changes

### Finance Module Integration
- Journal posting
- Cost center allocation
- Budget impact

### Flow Integration
- Notification publishing
- Approval routing
- SLA monitoring

### Document Integration
- Payslip storage
- Report archiving

## Performance Considerations

- Database indexes on frequently queried columns
- WAL mode for concurrent access
- Efficient pagination for large datasets
- Cached summary statistics

## Future Enhancements

1. Multi-currency payroll support
2. Country-specific tax engines
3. Advanced analytics dashboards
4. API for third-party integrations
5. Mobile employee self-service
6. Advanced workflow customization
