# Dashboard Role Visibility Matrix

## Overview

This document defines which dashboard zones, widgets, KPIs, and modules are visible to each role in the WHDASH Enterprise Dashboard.

---

## Role Definitions

| Role | Description | Dashboard Focus |
|------|-------------|-----------------|
| Admin | Full system access | All zones (full) |
| CEO | Chief Executive Officer | Executive view |
| CFO | Chief Financial Officer | Finance-focused |
| COO | Chief Operating Officer | Operations-focused |
| Finance Manager | Finance department head | Finance zone |
| Treasury Manager | Treasury department head | Treasury zone |
| HR Manager | HR department head | HR zone |
| Warehouse Manager | Warehouse operations | WMS zone |
| Logistics Manager | Logistics operations | Logistics zone |
| Quality Manager | Quality control | Quality zone |
| Maintenance Manager | Maintenance operations | Maintenance zone |
| Auditor | Internal/External auditor | Audit-focused |
| Standard User | Default user | Personal zone only |

---

## Zone Visibility by Role

| Zone | Admin | CEO | CFO | COO | Fin Mgr | Treas Mgr | HR Mgr | Whse Mgr | Log Mgr | Qual Mgr | Maint Mgr | Auditor | User |
|------|-------|-----|-----|-----|---------|-----------|--------|----------|---------|----------|----------|---------|------|
| Z1: Header | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Z2: KPIs | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Limited | ✓ |
| Z3: Modules | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Limited | ✓ |
| Z4: Alerts | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Z5: Operations | ✓ | ✓ | ✓ | ✓ | - | - | - | ✓ | ✓ | ✓ | ✓ | - | - |
| Z6: Financial | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - | - | - | Limited | - |
| Z7: Workflow | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Limited | ✓ |
| Z8: Flow | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Z9: Personal | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Z10: Reports | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Z11: AI Insights | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - | - |
| Z12: Timeline | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - |

Legend: ✓ = Full visibility, - = Hidden, Limited = Partial visibility

---

## KPI Visibility by Role

### Universal KPIs (All Roles)
- Pending Approvals
- Critical Alerts
- Overdue Tasks
- Open Issues

### Finance KPIs
| KPI | CFO | Finance Mgr | Treas Mgr | Admin |
|-----|-----|-------------|-----------|-------|
| Cash Position | ✓ | ✓ | ✓ | ✓ |
| Today's Collections | ✓ | ✓ | ✓ | ✓ |
| Due Payments | ✓ | ✓ | ✓ | ✓ |
| Active Workflows | ✓ | ✓ | ✓ | ✓ |

### Operations KPIs
| KPI | COO | Whse Mgr | Log Mgr | Maint Mgr | Admin |
|-----|-----|----------|---------|----------|-------|
| Stock Health | ✓ | ✓ | - | - | ✓ |
| Late Deliveries | ✓ | - | ✓ | - | ✓ |
| Open Work Orders | ✓ | - | - | ✓ | ✓ |
| Quality Exceptions | ✓ | - | - | ✓ | ✓ |

### HR KPIs
| KPI | HR Mgr | Admin |
|-----|--------|-------|
| Headcount | ✓ | ✓ |
| Attendance Rate | ✓ | ✓ |

### Executive KPIs
| KPI | CEO | CFO | COO | Admin |
|-----|-----|-----|-----|-------|
| Revenue Snapshot | ✓ | ✓ | ✓ | ✓ |
| Budget Variance | ✓ | ✓ | - | ✓ |

---

## Module Visibility by Role

### Module Categories

| Category | Modules |
|----------|---------|
| Core Operations | org_planning, finance, treasury, assets, controlling, inventory, logistics, supply_chain, demand_planning, manufacturing, quality, maintenance |
| People & Org | hr, payroll, talent, expense |
| Customers & Commerce | crm, marketing, ecommerce, project |
| Technology & Governance | investment, bi, ai, btp, integration, security, compliance, documents, legal, multi_company |
| Services | service, supplier, contingent, sustainability, rd |

### Role Module Access Matrix

| Role | Core Ops | Finance | Treasury | Assets | WMS | Logistics | HR | CRM | Admin | Others |
|------|----------|---------|----------|--------|-----|-----------|----|----|-------|--------|
| Admin | ✓ (all) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (all) |
| CEO | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - | View |
| CFO | ✓ | ✓ | ✓ | ✓ | - | - | - | - | - | Finance |
| COO | ✓ | - | - | - | ✓ | ✓ | - | - | - | Operations |
| Finance Mgr | ✓ | ✓ | ✓ | - | - | - | - | - | - | Finance |
| Treas Mgr | ✓ | ✓ | ✓ | - | - | - | - | - | - | Treasury |
| HR Mgr | - | - | - | - | - | - | ✓ | - | - | HR |
| Warehouse Mgr | - | - | - | - | ✓ | ✓ | - | - | - | WMS |
| Log Mgr | - | - | - | - | - | ✓ | - | - | - | Logistics |
| Quality Mgr | - | - | - | - | - | - | - | - | - | Quality |
| Maint Mgr | - | - | - | - | - | - | - | - | - | Maintenance |
| Auditor | Read-only where permitted | | | | | | | | | | Read-only |
| Standard User | Based on assignment | | | | | | | | | | Limited |

---

## Permission Requirements

### Dashboard Access
```
module: dashboard
resource: dashboard
action: view
```

### Module Access
```
module: {module_name}
resource: dashboard
action: view
```

### Alert Management
```
module: dashboard
resource: alerts
action: view, dismiss, acknowledge
```

### Workflow Actions
```
module: workflow
resource: approvals
action: approve, reject
```

### Report Access
```
module: reports
resource: {report_name}
action: view, export
```

---

## Data Scope by Role

### Company/Entity Scope
| Role | Scope |
|------|-------|
| Admin | All companies |
| CEO | All companies (consolidated) |
| CFO | All companies (finance) |
| Department Manager | Assigned company/entity |
| Standard User | Assigned company/entity |

### Branch Scope
| Role | Scope |
|------|-------|
| Admin | All branches |
| Manager | Assigned branches |
| Standard User | Assigned branch |

---

## Widget Visibility Rules

### Personal Productivity Zone
- Only shows tasks/issues assigned to the current user
- Other users' data is never visible

### Approval Items
- Shows only items pending approval by current user
- Does not show items assigned to other approvers

### Flow/Communication
- Shows announcements visible to user's department/company
- Mentions are user-specific

---

## Dashboard Preference Persistence

User preferences are stored in `user_preferences` table:

```json
{
  "dashboard_layout": {
    "hidden_zones": ["zone_11"],
    "kpi_order": ["cash_position", "pending_approvals", ...],
    "favorite_modules": ["finance", "treasury", "crm"],
    "compact_view": false
  }
}
```

---

*Document Version: 1.0*
*Last Updated: 2026-04-16*
