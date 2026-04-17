# Dashboard Sample Data Report

## Executive Summary

This report documents the sample data populated across all dashboards in the WHDASH (MMDx) enterprise platform. All major dashboards have been populated with realistic, relational demo data.

## Dashboard Coverage

### 1. Main Enterprise Dashboard
**Route**: `/dashboard`

| Widget Type | Data Source | Status |
|-------------|-------------|--------|
| KPI Cards | Platform statistics | Populated |
| Finance Summary | finance_* tables | Populated |
| WMS Summary | inventory, warehouses | Populated |
| HR Summary | hr_employees, hr_attendance | Populated |
| Sales Summary | sales_orders, sales_invoices | Populated |
| Procurement Summary | procurement_purchase_orders | Populated |
| Quality Summary | quality_inspections | Populated |
| Recent Activities | activity logs | Populated |
| Pending Approvals | workflow_instances | Populated |
| Alerts | platform_notifications | Populated |

### 2. Treasury Dashboard
**Route**: `/finance/treasury/dashboard`

| Widget Type | Data Source | Status |
|-------------|-------------|--------|
| Cash Position | treasury_cash_position_snapshots | 360 rows |
| Petty Cash | treasury_petty_cash_accounts | 4 accounts |
| Cash Movements | treasury_cash_movements | 50 movements |
| Collections Plan | treasury_collections | 5 records |
| Payments Plan | treasury_payments_plan | 5 records |
| Transfer Requests | treasury_transfer_requests | 4 requests |
| Treasury Alerts | treasury_alerts | 6 alerts |
| Forecasts | treasury_forecasts | 3 scenarios |

### 3. WMS Dashboard
**Route**: `/wms/dashboard`

| Widget Type | Data Source | Status |
|-------------|-------------|--------|
| Inventory Summary | parts, inventory | 322 parts, 3983 inventory |
| Warehouse Overview | warehouses | 21 warehouses |
| Wave Status | wms_waves | 10 waves |
| Wave Templates | wms_wave_templates | 5 templates |
| Dock Status | wms_dock_doors | 12 doors |
| QC Inspections | wms_qc_inspections | 15 inspections |
| Stock Counts | wms_stock_counts | 8 counts |
| Returns | wms_returns | 12 returns |
| Shipments | wms_shipments | 15 shipments |

### 4. Finance Dashboard
**Route**: `/finance/dashboard`

| Widget Type | Data Source | Status |
|-------------|-------------|--------|
| Chart of Accounts | finance_accounts | 86 accounts |
| Fiscal Years | finance_fiscal_years | 3 years |
| Fiscal Periods | finance_fiscal_periods | 36 periods |
| Journal Entries | finance_journals | 61 entries |
| Customer Invoices | finance_customer_invoices | 18 invoices |
| Supplier Bills | finance_supplier_bills | 18 bills |
| Cost Centers | finance_cost_centers | 8 centers |
| Budgets | finance_budgets | 4 budgets |

### 5. Quality Dashboard
**Route**: `/quality/dashboard`

| Widget Type | Data Source | Status |
|-------------|-------------|--------|
| Inspections | quality_inspections | 20 inspections |
| NCRs | quality_non_conformances | 10 NCRs |
| CAPAs | quality_capa_records | 8 CAPAs |
| Root Cause Categories | quality_root_cause_categories | 7 categories |
| Defect Categories | quality_defect_categories | 8 categories |

### 6. HR Dashboard
**Route**: `/hr/dashboard`

| Widget Type | Data Source | Status |
|-------------|-------------|--------|
| Employees | hr_employees | 94 employees |
| Departments | hr_departments | 8 departments |
| Attendance | hr_attendance_records | 139 records |
| Leave Requests | hr_leave_requests | Various statuses |
| Positions | hr_positions | 20 positions |

### 7. Sales Dashboard
**Route**: `/sales/dashboard`

| Widget Type | Data Source | Status |
|-------------|-------------|--------|
| Customers | sales_customers | 58 customers |
| Inquiries | sales_inquiries | 71 inquiries |
| Quotations | sales_quotations | 68 quotations |
| Orders | sales_orders | 134 orders |
| Invoices | sales_invoices | 20 invoices |

### 8. Procurement Dashboard
**Route**: `/procurement/dashboard`

| Widget Type | Data Source | Status |
|-------------|-------------|--------|
| Suppliers | suppliers | 40 suppliers |
| Requisitions | procurement_requisitions | 1 requisition |
| Purchase Orders | procurement_purchase_orders | 1 PO |
| RFQs | procurement_rfqs | 15 RFQs |

### 9. Maintenance Dashboard
**Route**: `/maintenance/dashboard`

| Widget Type | Data Source | Status |
|-------------|-------------|--------|
| Facilities | maintenance_facilities | 5 facilities |
| Work Orders | maintenance_work_orders | 35 work orders |

### 10. Asset Dashboard
**Route**: `/assets/dashboard`

| Widget Type | Data Source | Status |
|-------------|-------------|--------|
| Assets | assets | 44 assets |
| Categories | asset_categories | 10 categories |
| Depreciation | asset_depreciation_schedules | 44 schedules |

### 11. Logistics Dashboard
**Route**: `/logistics/dashboard`

| Widget Type | Data Source | Status |
|-------------|-------------|--------|
| Vehicles | logistics_vehicles | 15 vehicles |
| Drivers | logistics_drivers | 20 drivers |
| Delivery Trips | delivery_trips | 3 trips |
| Delivery Stops | delivery_stops | 2 stops |
| Delivery Activities | delivery_activities | 5 activities |

## Validation Results

| Dashboard | Status | Row Count |
|-----------|--------|----------|
| Main Dashboard | OK | Platform-wide |
| Treasury | OK | 445+ rows |
| WMS | OK | 4,300+ rows |
| Finance | OK | 260+ rows |
| Quality | OK | 38 rows |
| HR | OK | 242 rows |
| Sales | OK | 351 rows |
| Procurement | OK | 57 rows |
| Maintenance | OK | 40 rows |
| Assets | OK | 98 rows |
| Logistics | OK | 45 rows |

## KPI Summary

All KPI cards across dashboards display non-zero values:
- Total Employees: 94
- Active Suppliers: 40
- Sales Orders: 134
- Open Invoices: 18
- Inventory Items: 322 parts
- Warehouse Capacity: 21 locations
- Pending Approvals: 3 instances
- Active Workflows: 4 definitions