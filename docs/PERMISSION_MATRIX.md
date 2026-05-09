# MMDx Permission Matrix
## Enterprise Multi-Layer Permission Structure

---

## Permission Naming Convention

```
module.resource.action
```

**Examples:**
- `wms.inventory.view` - View warehouse inventory
- `finance.journals.post` - Post journal entries
- `hr.employees.create` - Create employee records
- `admin.roles.manage` - Manage roles and permissions

**Action Types:**
- `view` - Read access, see records
- `create` - Create new records
- `edit` - Modify existing records
- `delete` - Delete records
- `approve` - Approve/reject workflows
- `execute` - Execute processes (post, run, etc.)
- `import` - Import data from external sources
- `export` - Export data to external formats
- `upload` - Upload attachments/files
- `download` - Download attachments/reports
- `manage` - Full administrative control

---

## Module: Dashboard

| Resource | view | create | edit | delete | export |
|----------|------|--------|------|--------|--------|
| dashboard | Yes | - | - | - | Yes |
| dashboard.widgets | Yes | Yes | Yes | - | Yes |

---

## Module: WMS (Warehouse Management)

| Resource | view | create | edit | delete | approve | execute | import | export |
|----------|------|--------|------|--------|---------|---------|--------|--------|
| dashboard | Yes | - | - | - | - | - | - | - |
| inventory | Yes | Yes | Yes | Yes | - | Yes | - | Yes |
| items | Yes | Yes | Yes | Yes | - | - | Yes | Yes |
| locations | Yes | Yes | Yes | Yes | - | - | - | - |
| warehouses | Yes | Yes | Yes | Yes | - | - | - | - |
| stock_movements | Yes | Yes | - | - | - | Yes | - | Yes |
| stock_count | Yes | Yes | Yes | - | Yes | - | - | - |
| receipts | Yes | Yes | Yes | - | Yes | Yes | - | - |
| shipments | Yes | Yes | Yes | Yes | Yes | Yes | - | - |
| returns | Yes | Yes | Yes | - | Yes | - | - | - |
| transfers | Yes | Yes | Yes | - | Yes | Yes | - | - |
| adjustments | Yes | Yes | Yes | - | Yes | - | - | - |
| reports | Yes | - | - | - | - | - | - | Yes |
| settings | Yes | - | Yes | - | - | - | - | - |

---

## Module: Logistics

| Resource | view | create | edit | delete | approve | execute | export |
|----------|------|--------|------|--------|---------|---------|--------|
| dashboard | Yes | - | - | - | - | - | - |
| trips | Yes | Yes | Yes | Yes | - | Yes | Yes |
| routes | Yes | Yes | Yes | Yes | - | Yes | - |
| dispatch | Yes | Yes | Yes | - | - | Yes | - |
| vehicles | Yes | Yes | Yes | Yes | - | - | - |
| drivers | Yes | Yes | Yes | Yes | - | - | - |
| stops | Yes | Yes | Yes | Yes | - | Yes | - |
| delivery_reports | Yes | - | - | - | - | - | Yes |
| alerts | Yes | Yes | Yes | Yes | - | Yes | - |
| settings | Yes | - | Yes | - | - | - | - |

---

## Module: Procurement

| Resource | view | create | edit | delete | approve | execute | import | export |
|----------|------|--------|------|--------|---------|---------|--------|--------|
| dashboard | Yes | - | - | - | - | - | - | - |
| suppliers | Yes | Yes | Yes | Yes | - | - | - | Yes |
| requisitions | Yes | Yes | Yes | Yes | Yes | - | - | - |
| rfqs | Yes | Yes | Yes | Yes | - | Yes | - | Yes |
| quotations | Yes | Yes | Yes | Yes | Yes | - | - | - |
| orders | Yes | Yes | Yes | Yes | Yes | Yes | - | Yes |
| shipments | Yes | Yes | Yes | - | - | Yes | - | - |
| receiving | Yes | Yes | Yes | - | - | Yes | - | - |
| local | Yes | Yes | Yes | - | - | - | - | - |
| import_proc | Yes | Yes | Yes | - | - | - | Yes | - |
| claims | Yes | Yes | Yes | Yes | - | Yes | - | - |
| returns | Yes | Yes | Yes | Yes | - | - | - | - |
| contracts | Yes | Yes | Yes | Yes | - | - | - | - |
| performance | Yes | - | - | - | - | - | - | Yes |
| reports | Yes | - | - | - | - | - | - | Yes |
| settings | Yes | - | Yes | - | - | - | - | - |

---

## Module: Finance

| Resource | view | create | edit | delete | approve | execute | export |
|----------|------|--------|------|--------|---------|---------|--------|
| dashboard | Yes | - | - | - | - | - | - |
| accounts | Yes | Yes | Yes | Yes | - | - | - |
| journals | Yes | Yes | Yes | Yes | - | Yes | - |
| fiscal_years | Yes | Yes | Yes | - | Yes | Yes | - |
| ar_invoices | Yes | Yes | Yes | Yes | - | Yes | - |
| ar_receipts | Yes | Yes | Yes | Yes | - | Yes | - |
| ar_credit_notes | Yes | Yes | Yes | Yes | - | Yes | - |
| ar | Yes | - | Yes | - | - | - | - |
| ap_bills | Yes | Yes | Yes | Yes | - | Yes | - |
| ap_payments | Yes | Yes | Yes | Yes | - | Yes | - |
| ap_debit_notes | Yes | Yes | Yes | Yes | - | Yes | - |
| ap | Yes | - | Yes | - | - | - | - |
| assets | Yes | Yes | Yes | Yes | - | - | - |
| depreciation | Yes | Yes | - | - | Yes | Yes | - |
| cost_centers | Yes | Yes | Yes | Yes | - | - | - |
| budgets | Yes | Yes | Yes | Yes | Yes | - | - |
| tax | Yes | Yes | Yes | - | - | - | - |
| reports | Yes | - | - | - | - | - | Yes |
| settings | Yes | - | Yes | - | - | - | - |

---

## Module: HR

| Resource | view | create | edit | delete | approve | execute | export |
|----------|------|--------|------|--------|---------|---------|--------|
| dashboard | Yes | - | - | - | - | - | - |
| employees | Yes | Yes | Yes | Yes | - | - | Yes |
| departments | Yes | Yes | Yes | Yes | - | - | - |
| positions | Yes | Yes | Yes | Yes | - | - | - |
| attendance | Yes | Yes | Yes | Yes | Yes | - | - |
| leave | Yes | Yes | Yes | Yes | Yes | - | - |
| payroll | Yes | Yes | Yes | Yes | Yes | Yes | - |
| overtime | Yes | Yes | Yes | Yes | Yes | - | - |
| loans | Yes | Yes | Yes | Yes | Yes | - | - |
| documents | Yes | - | - | - | - | Yes | - |
| announcements | Yes | Yes | Yes | Yes | - | - | - |
| recruitment | Yes | Yes | Yes | Yes | Yes | - | - |
| performance | Yes | Yes | Yes | Yes | - | - | - |
| reports | Yes | - | - | - | - | - | Yes |
| settings | Yes | - | Yes | - | - | - | - |

---

## Module: Assets

| Resource | view | create | edit | delete | approve | execute | export |
|----------|------|--------|------|--------|---------|---------|--------|
| dashboard | Yes | - | - | - | - | - | - |
| assets | Yes | Yes | Yes | Yes | - | - | Yes |
| categories | Yes | Yes | Yes | Yes | - | - | - |
| acquisitions | Yes | Yes | Yes | - | Yes | - | - |
| depreciation | Yes | Yes | Yes | - | Yes | Yes | - |
| depreciation_profiles | Yes | Yes | Yes | - | - | - | - |
| maintenance | Yes | Yes | Yes | - | - | Yes | - |
| maintenance_schedules | Yes | Yes | Yes | Yes | - | - | - |
| maintenance_work_orders | Yes | Yes | Yes | - | - | Yes | - |
| maintenance_work_logs | Yes | Yes | Yes | - | - | - | - |
| maintenance_costs | Yes | Yes | - | - | - | - | - |
| transfers | Yes | Yes | - | - | Yes | Yes | - |
| assignments | Yes | Yes | Yes | - | - | - | - |
| disposal | Yes | Yes | - | - | Yes | Yes | - |
| disposal_requests | Yes | Yes | Yes | - | Yes | - | - |
| audit_log | Yes | - | - | - | - | - | Yes |
| reports | Yes | - | - | - | - | - | Yes |
| settings | Yes | - | Yes | - | - | - | - |

---

## Module: Maintenance

| Resource | view | create | edit | delete | approve | execute | export |
|----------|------|--------|------|--------|---------|---------|--------|
| dashboard | Yes | - | - | - | - | - | - |
| equipment | Yes | Yes | Yes | - | - | - | - |
| equipment_detail | Yes | - | - | - | - | - | - |
| equipment_downtime | Yes | Yes | Yes | - | - | - | - |
| facilities | Yes | Yes | Yes | Yes | - | - | - |
| facility_requests | Yes | Yes | Yes | - | - | Yes | - |
| pm_plans | Yes | Yes | Yes | Yes | - | - | - |
| pm_schedules | Yes | Yes | Yes | Yes | - | - | - |
| corrective | Yes | Yes | Yes | - | - | - | - |
| breakdown | Yes | Yes | Yes | - | - | - | - |
| work_orders | Yes | Yes | Yes | - | - | Yes | - |
| work_order_tasks | Yes | Yes | Yes | - | - | Yes | - |
| technicians | Yes | Yes | Yes | - | - | - | - |
| teams | Yes | Yes | Yes | - | - | - | - |
| parts_usage | Yes | Yes | Yes | - | - | - | - |
| labor_logs | Yes | Yes | Yes | - | - | - | - |
| downtime | Yes | Yes | Yes | - | - | - | - |
| inspections | Yes | Yes | Yes | - | - | - | - |
| checklists | Yes | Yes | Yes | - | - | - | - |
| calendar | Yes | - | - | - | - | - | - |
| reports | Yes | - | - | - | - | - | Yes |
| settings | Yes | - | Yes | - | - | - | - |
| audit_logs | Yes | - | - | - | - | - | Yes |
| my_work_orders | Yes | - | Yes | - | - | Yes | - |

---

## Module: Quality

| Resource | view | create | edit | delete | approve | execute | export |
|----------|------|--------|------|--------|---------|---------|--------|
| dashboard | Yes | - | - | - | - | - | - |
| inspections | Yes | Yes | Yes | Yes | - | Yes | - |
| ncr | Yes | Yes | Yes | Yes | Yes | - | - |
| capa | Yes | Yes | Yes | Yes | Yes | - | - |
| audits | Yes | Yes | Yes | Yes | - | Yes | - |
| reports | Yes | - | - | - | - | - | Yes |
| settings | Yes | - | Yes | - | - | - | - |
| audit_log | Yes | - | - | - | - | - | Yes |
| quality | Yes | Yes | Yes | Yes | Yes | Yes | Yes |

---

## Module: Sales

| Resource | view | create | edit | delete | approve | execute | export |
|----------|------|--------|------|--------|---------|---------|--------|
| dashboard | Yes | - | - | - | - | - | - |
| customers | Yes | Yes | Yes | Yes | - | - | Yes |
| inquiries | Yes | Yes | Yes | Yes | - | - | - |
| opportunities | Yes | Yes | Yes | Yes | - | - | - |
| pricing | Yes | Yes | Yes | - | Yes | - | - |
| quotations | Yes | Yes | Yes | Yes | Yes | - | - |
| orders | Yes | Yes | Yes | Yes | Yes | - | - |
| reservations | Yes | Yes | Yes | Yes | Yes | - | - |
| deliveries | Yes | Yes | Yes | Yes | - | Yes | - |
| returns | Yes | Yes | Yes | Yes | Yes | - | - |
| targets | Yes | Yes | Yes | Yes | - | - | - |
| contracts | Yes | Yes | Yes | Yes | - | - | - |
| activities | Yes | Yes | Yes | Yes | - | - | - |
| invoices | Yes | Yes | Yes | Yes | Yes | - | - |
| sales_reports | Yes | - | - | - | - | - | Yes |
| settings | Yes | - | Yes | - | - | - | - |

---

## Module: Marketing

| Resource | view | create | edit | delete | approve | execute | export |
|----------|------|--------|------|--------|---------|---------|--------|
| dashboard | Yes | - | - | - | - | - | - |
| campaigns | Yes | Yes | Yes | Yes | - | Yes | - |
| leads | Yes | Yes | Yes | Yes | - | - | - |
| channels | Yes | Yes | Yes | Yes | - | - | - |
| content | Yes | Yes | Yes | Yes | - | Yes | - |
| advertisements | Yes | Yes | Yes | Yes | - | - | - |
| offers | Yes | Yes | Yes | Yes | - | - | - |
| budgets | Yes | Yes | Yes | Yes | - | - | - |
| reports | Yes | - | - | - | - | - | Yes |
| settings | Yes | - | Yes | - | - | - | - |

---

## Module: CRM

| Resource | view | create | edit | delete | approve | execute | export |
|----------|------|--------|------|--------|---------|---------|--------|--------|
| dashboard | Yes | - | - | - | - | - | - |
| customers | Yes | Yes | Yes | Yes | - | - | Yes |
| contacts | Yes | Yes | Yes | Yes | - | - | - |
| activities | Yes | Yes | Yes | Yes | - | - | - |
| tasks | Yes | Yes | Yes | Yes | - | - | - |
| opportunities | Yes | Yes | Yes | Yes | - | - | - |
| reports | Yes | - | - | - | - | - | Yes |
| settings | Yes | - | Yes | - | - | - | - |

---

## Module: Planning

| Resource | view | create | edit | delete | approve | execute | export |
|----------|------|--------|------|--------|---------|---------|--------|
| dashboard | Yes | - | - | - | - | - | - |
| forecasts | Yes | Yes | Yes | Yes | - | - | - |
| demand | Yes | Yes | Yes | Yes | - | - | - |
| replenishment | Yes | Yes | Yes | Yes | - | Yes | - |
| policies | Yes | Yes | Yes | Yes | - | - | - |
| scenarios | Yes | Yes | Yes | Yes | - | - | - |
| alerts | Yes | Yes | Yes | Yes | - | Yes | - |
| reports | Yes | - | - | - | - | - | Yes |
| settings | Yes | - | Yes | - | - | - | - |

---

## Module: Workflow

| Resource | view | create | edit | delete | approve | execute | export |
|----------|------|--------|------|--------|---------|---------|--------|
| dashboard | Yes | - | - | - | - | - | - |
| my_work | Yes | - | Yes | - | - | Yes | - |
| approvals | Yes | - | - | - | Yes | - | - |
| delegation | Yes | Yes | Yes | Yes | - | - | - |
| designer | Yes | Yes | Yes | Yes | - | - | - |
| processes | Yes | Yes | Yes | Yes | - | - | - |
| instances | Yes | Yes | Yes | Yes | - | Yes | - |
| automation | Yes | Yes | Yes | Yes | - | - | - |
| notifications | Yes | Yes | Yes | Yes | - | - | - |
| monitoring | Yes | - | - | - | - | Yes | - |
| reports | Yes | - | - | - | - | - | Yes |
| settings | Yes | Yes | Yes | Yes | - | - | - |
| audit | Yes | - | - | - | - | - | Yes |
| templates | Yes | Yes | Yes | Yes | - | - | - |
| escalation | Yes | Yes | Yes | Yes | - | - | - |

---

## Module: Documents

| Resource | view | create | edit | delete | approve | execute | export |
|----------|------|--------|------|--------|---------|---------|--------|
| dashboard | Yes | - | - | - | - | - | - |
| files | Yes | Yes | Yes | Yes | - | - | - |
| versions | Yes | Yes | Yes | Yes | - | - | - |
| templates | Yes | Yes | Yes | Yes | - | - | - |
| signatures | Yes | Yes | - | - | - | Yes | - |
| categories | Yes | Yes | Yes | Yes | - | - | - |
| tags | Yes | Yes | Yes | Yes | - | - | - |
| links | Yes | Yes | Yes | Yes | - | - | - |
| shares | Yes | Yes | Yes | Yes | - | - | - |
| reports | Yes | - | - | - | - | - | Yes |
| settings | Yes | - | Yes | - | - | - | - |
| audit_logs | Yes | - | - | - | - | - | Yes |
| retention | Yes | Yes | Yes | Yes | - | - | - |
| access_control | Yes | Yes | Yes | Yes | - | - | - |
| checkin_checkout | Yes | Yes | Yes | Yes | - | - | - |
| linked_records | Yes | Yes | Yes | Yes | - | - | - |

---

## Module: E-commerce

| Resource | view | create | edit | delete | approve | execute | import | export |
|----------|------|--------|------|--------|---------|---------|--------|--------|--------|
| dashboard | Yes | - | - | - | - | - | - | - |
| channels | Yes | Yes | Yes | Yes | - | - | - | - |
| orders | Yes | Yes | Yes | Yes | - | Yes | Yes | Yes |
| inventory | Yes | Yes | Yes | Yes | - | Yes | - | Yes |
| customers | Yes | Yes | Yes | Yes | - | - | Yes | Yes |
| mappings | Yes | Yes | Yes | Yes | - | - | - | - |
| exceptions | Yes | Yes | Yes | Yes | - | Yes | - | - |
| reports | Yes | - | - | - | - | - | - | Yes |
| settings | Yes | - | Yes | - | - | - | - | - |
| audit_logs | Yes | - | - | - | - | - | - | Yes |
| sync | Yes | Yes | Yes | Yes | - | Yes | - | - |

---

## Module: API Gateway

| Resource | view | create | edit | delete | approve | execute | export |
|----------|------|--------|------|--------|---------|---------|--------|
| dashboard | Yes | - | - | - | - | - | - |
| clients | Yes | Yes | Yes | Yes | - | - | - |
| scopes | Yes | Yes | Yes | Yes | - | - | - |
| policies | Yes | Yes | Yes | Yes | - | - | - |
| routes | Yes | Yes | Yes | Yes | - | - | - |
| api_versions | Yes | Yes | Yes | Yes | - | - | - |
| request_logs | Yes | - | - | - | - | - | Yes |
| webhooks | Yes | Yes | Yes | Yes | - | - | - |
| subscriptions | Yes | Yes | Yes | Yes | - | - | - |
| integrations | Yes | Yes | Yes | Yes | - | Yes | - |
| sync_jobs | Yes | Yes | Yes | Yes | - | Yes | - | - |
| monitoring | Yes | - | - | - | - | Yes | - |
| rate_limits | Yes | Yes | Yes | Yes | - | - | - |
| health_status | Yes | - | - | - | - | - | - |
| reports | Yes | - | - | - | - | - | Yes |
| documentation | Yes | - | - | - | - | - | - |
| audit_logs | Yes | - | - | - | - | - | Yes |
| settings | Yes | - | Yes | - | - | - | - |

---

## Module: BI / Business Intelligence

| Resource | view | create | edit | delete | approve | execute | export |
|----------|------|--------|------|--------|---------|---------|--------|
| dashboard | Yes | - | - | - | - | - | - |
| executive | Yes | - | - | - | - | - | Yes |
| holding_view | Yes | - | - | - | - | - | Yes |
| company_comparison | Yes | - | - | - | - | - | Yes |
| operational | Yes | - | - | - | - | - | Yes |
| kpis | Yes | Yes | Yes | Yes | - | - | - |
| drilldown | Yes | - | - | - | - | Yes | - |
| alerts | Yes | Yes | Yes | Yes | - | Yes | - |
| reports | Yes | - | - | - | - | - | Yes |
| settings | Yes | - | Yes | - | - | - | - |

---

## Module: BI Advanced

| Resource | view | create | edit | delete | approve | execute | import | export |
|----------|------|--------|------|--------|---------|---------|--------|--------|
| dashboard | Yes | - | - | - | - | - | - | - |
| datasets | Yes | Yes | Yes | Yes | - | - | Yes | Yes |
| adhoc_queries | Yes | Yes | Yes | Yes | - | Yes | - | - |
| reports | Yes | Yes | Yes | Yes | - | - | - | Yes |
| scheduled_reports | Yes | Yes | Yes | Yes | - | Yes | - | - |
| kpis | Yes | Yes | Yes | Yes | - | - | - | - |
| drilldown | Yes | - | - | - | - | Yes | - | - |
| monitoring | Yes | - | - | - | - | Yes | - | - |
| access_logs | Yes | - | - | - | - | - | - | Yes |
| performance_logs | Yes | - | - | - | - | - | - | Yes |
| delivery_logs | Yes | - | - | - | - | - | - | Yes |
| settings | Yes | - | Yes | - | - | - | - | - |

---

## Module: Social Media

| Resource | view | create | edit | delete | approve | execute | export |
|----------|------|--------|------|--------|---------|---------|--------|
| dashboard | Yes | - | - | - | - | - | - |
| accounts | Yes | Yes | Yes | Yes | - | - | - |
| content | Yes | Yes | Yes | Yes | - | Yes | - |
| calendar | Yes | Yes | Yes | Yes | - | - | - |
| publishing | Yes | Yes | Yes | Yes | - | Yes | - |
| queue | Yes | Yes | Yes | Yes | - | - | - |
| engagement | Yes | - | - | - | - | Yes | - |
| messages | Yes | Yes | Yes | Yes | - | - | - |
| saved_replies | Yes | Yes | Yes | Yes | - | - | - |
| leads | Yes | Yes | Yes | Yes | - | - | - |
| campaigns | Yes | Yes | Yes | Yes | - | - | - |
| advertisements | Yes | Yes | Yes | Yes | - | - | - |
| monitoring | Yes | - | - | - | - | Yes | - |
| reports | Yes | - | - | - | - | - | Yes |
| settings | Yes | - | Yes | - | - | - | - |

---

## Module: Customer Intelligence

| Resource | view | create | edit | delete | approve | execute | export |
|----------|------|--------|------|--------|---------|---------|--------|
| dashboard | Yes | - | - | - | - | - | - |
| profiles | Yes | Yes | Yes | Yes | - | - | - |
| segments | Yes | Yes | Yes | Yes | - | - | - |
| forecasts | Yes | Yes | Yes | Yes | - | - | - |
| alerts | Yes | Yes | Yes | Yes | - | Yes | - |
| recommendations | Yes | Yes | Yes | Yes | - | Yes | - |
| reports | Yes | - | - | - | - | - | Yes |
| settings | Yes | - | Yes | - | - | - | - |

---

## Module: Tasks

| Resource | view | create | edit | delete | approve | execute | export |
|----------|------|--------|------|--------|---------|---------|--------|
| dashboard | Yes | - | - | - | - | - | - |
| tasks | Yes | Yes | Yes | Yes | - | - | - |
| subtasks | Yes | Yes | Yes | Yes | - | - | - |
| transactions | Yes | Yes | Yes | Yes | - | - | - |
| reports | Yes | - | - | - | - | - | Yes |
| settings | Yes | - | Yes | - | - | - | - |

---

## Module: Platform / Admin

| Resource | view | create | edit | delete | approve | execute | export |
|----------|------|--------|------|--------|---------|---------|--------|
| users | Yes | Yes | Yes | Yes | - | - | Yes |
| roles | Yes | Yes | Yes | Yes | - | - | - |
| permissions | Yes | - | - | - | - | Yes | - |
| audit_log | Yes | - | - | - | - | - | Yes |
| settings | Yes | - | Yes | - | - | - | - |
| notifications | Yes | Yes | Yes | Yes | - | - | - |

---

## Role-Permission Mapping Summary

### Global Admin (all modules, all actions)
```
*.*.*
```

### Warehouse Manager
```
wms.*.*
logistics.*.*
planning.dashboard.view
planning.reports.view
tasks.tasks.view
reports.operational.view
reports.executive.view
```

### Warehouse Supervisor
```
wms.dashboard.view
wms.inventory.view
wms.inventory.edit
wms.items.view
wms.locations.view
wms.warehouses.view
wms.stock_movements.view
wms.stock_count.view
wms.stock_count.create
wms.receipts.view
wms.receipts.edit
wms.receipts.receive
wms.shipments.view
wms.shipments.edit
wms.returns.view
wms.returns.edit
wms.transfers.view
wms.transfers.create
wms.transfers.edit
wms.transfers.approve
wms.adjustments.view
wms.adjustments.create
wms.adjustments.edit
wms.reports.view
wms.reports.export
logistics.dashboard.view
logistics.trips.view
```

### Warehouse Assistant
```
wms.dashboard.view
wms.inventory.view
wms.items.view
wms.locations.view
wms.warehouses.view
wms.stock_movements.view
wms.stock_count.view
wms.stock_count.create
wms.receipts.view
wms.shipments.view
wms.returns.view
wms.transfers.view
wms.transfers.create
wms.adjustments.view
```

### Warehouse Operator
```
wms.dashboard.view
wms.inventory.view
wms.items.view
wms.locations.view
wms.stock_movements.view
wms.stock_count.view
wms.stock_count.create
wms.receipts.view
wms.shipments.view
wms.returns.view
wms.transfers.view
```

### Finance Manager
```
finance.*.*
reports.financial.view
reports.financial.export
reports.executive.view
```

### Finance Supervisor
```
finance.dashboard.view
finance.accounts.view
finance.journals.view
finance.journals.create
finance.journals.edit
finance.fiscal_years.view
finance.ar_invoices.view
finance.ar_invoices.create
finance.ar_invoices.edit
finance.ar_receipts.view
finance.ar_receipts.create
finance.ar_credit_notes.view
finance.ar_credit_notes.create
finance.ar.view
finance.ap_bills.view
finance.ap_bills.create
finance.ap_bills.edit
finance.ap_payments.view
finance.ap_payments.create
finance.ap_debit_notes.view
finance.ap.view
finance.assets.view
finance.depreciation.view
finance.depreciation.create
finance.cost_centers.view
finance.budgets.view
finance.budgets.create
finance.budgets.edit
finance.tax.view
finance.reports.view
finance.reports.export
```

### Finance Assistant / Accountant
```
finance.dashboard.view
finance.accounts.view
finance.journals.view
finance.journals.create
finance.journals.edit
finance.fiscal_years.view
finance.ar_invoices.view
finance.ar_invoices.create
finance.ar_invoices.edit
finance.ar_receipts.view
finance.ar_receipts.create
finance.ar_credit_notes.view
finance.ar_credit_notes.create
finance.ar.view
finance.ap_bills.view
finance.ap_bills.create
finance.ap_bills.edit
finance.ap_payments.view
finance.ap_payments.create
finance.ap_debit_notes.view
finance.ap.view
finance.assets.view
finance.depreciation.view
finance.cost_centers.view
finance.budgets.view
finance.tax.view
finance.reports.view
```

### HR Manager
```
hr.*.*
tasks.tasks.view
tasks.subtasks.view
reports.executive.view
reports.hr.view
reports.hr.export
```

### HR Supervisor
```
hr.dashboard.view
hr.employees.view
hr.employees.create
hr.employees.edit
hr.departments.view
hr.departments.create
hr.departments.edit
hr.positions.view
hr.positions.create
hr.positions.edit
hr.attendance.view
hr.attendance.create
hr.attendance.edit
hr.leave.view
hr.leave.create
hr.leave.edit
hr.loans.view
hr.loans.create
hr.documents.view
hr.announcements.view
hr.announcements.create
hr.announcements.edit
hr.recruitment.view
hr.recruitment.create
hr.recruitment.edit
hr.performance.view
hr.performance.create
hr.performance.edit
hr.reports.view
hr.reports.export
tasks.tasks.view
tasks.subtasks.view
```

### Procurement Manager
```
procurement.*.*
planning.dashboard.view
planning.replenishment.view
wms.receipts.view
logistics.dashboard.view
reports.operational.view
reports.procurement.view
tasks.tasks.view
```

### Sales Manager
```
crm.*.*
sales.*.*
marketing.leads.view
marketing.leads.create
marketing.leads.edit
tasks.tasks.view
tasks.tasks.create
tasks.tasks.edit
```

### Quality Manager
```
quality.*.*
reports.executive.view
reports.operational.view
```

### Maintenance Manager
```
maintenance.*.*
assets.maintenance.view
assets.maintenance.create
assets.maintenance.edit
assets.maintenance_schedules.view
assets.maintenance_schedules.create
assets.maintenance_schedules.edit
assets.maintenance_work_orders.view
assets.maintenance_work_orders.create
assets.maintenance_work_orders.edit
reports.operational.view
```

### Asset Manager
```
assets.*.*
reports.executive.view
reports.operational.view
```
