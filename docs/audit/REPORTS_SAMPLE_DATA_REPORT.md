# Reports Sample Data Report

## Overview

This document details the sample data available across all report types in the WHDASH (MMDx) enterprise platform.

## Finance Reports

### General Ledger Report
- **Source Tables**: `finance_journals`, `finance_journal_lines`
- **Data**: 61 journal entries, 160 journal lines
- **Filters**: Date range, account, period

### Accounts Receivable Aging
- **Source Tables**: `finance_customer_invoices`, `finance_customer_receipts`
- **Data**: 18 invoices with various statuses
- **Aging Buckets**: Current, 30/60/90/120+ days

### Accounts Payable Aging
- **Source Tables**: `finance_supplier_bills`, `finance_supplier_payments`
- **Data**: 18 bills with various statuses
- **Aging Buckets**: Current, 30/60/90/120+ days

### Trial Balance
- **Source Tables**: `finance_accounts`, `finance_fiscal_periods`
- **Data**: 86 accounts across all categories

### Budget vs Actual
- **Source Tables**: `finance_budgets`, `finance_budget_lines`
- **Data**: 4 budgets with line items

### Cost Center Report
- **Source Tables**: `finance_cost_centers`, `finance_journals`
- **Data**: 8 cost centers

### Tax Report (VAT)
- **Source Tables**: `finance_tax_codes`, `finance_tax_rules`
- **Data**: 5 tax codes

## Treasury Reports

### Cash Position Report
- **Source Tables**: `treasury_cash_position_snapshots`
- **Data**: 360 daily snapshots across 4 banks

### Cash Flow Forecast
- **Source Tables**: `treasury_forecasts`, `treasury_forecast_items`
- **Data**: 3 forecast scenarios (base/best/worst)

### Collections Report
- **Source Tables**: `treasury_collections`
- **Data**: 5 active collection records

### Payments Report
- **Source Tables**: `treasury_payments_plan`
- **Data**: 5 payment plans

### Bank Reconciliation
- **Source Tables**: `treasury_bank_statements`
- **Data**: 3 bank statements (March 2026)

## WMS Reports

### Inventory Status
- **Source Tables**: `inventory`, `parts`, `warehouses`
- **Data**: 3,983 inventory locations, 322 parts

### Stock Valuation
- **Source Tables**: `inventory`, `wms_inventory_balances`
- **Data**: 54 balance records

### Warehouse Utilization
- **Source Tables**: `wms_zones`, `wms_locations`, `wms_warehouses`
- **Data**: 28 zones, 720 locations, 4 warehouses

### Putaway Performance
- **Source Tables**: `wms_putaway_tasks`
- **Data**: Task performance metrics

### Pick Performance
- **Source Tables**: `wms_pick_tasks`
- **Data**: 1 pick task record

### Wave Summary
- **Source Tables**: `wms_waves`, `wms_wave_templates`
- **Data**: 10 waves, 5 templates

### Returns Report
- **Source Tables**: `wms_returns`
- **Data**: 12 return records

### QC Inspection Report
- **Source Tables**: `wms_qc_inspections`
- **Data**: 15 inspection records

## HR Reports

### Headcount Report
- **Source Tables**: `hr_employees`, `hr_departments`
- **Data**: 94 employees, 8 departments

### Attendance Summary
- **Source Tables**: `hr_attendance_records`
- **Data**: 139 attendance records

### Leave Balance Report
- **Source Tables**: `hr_leave_balances`, `hr_leave_requests`
- **Data**: Leave balances and requests

### Payroll Summary
- **Source Tables**: `hr_payroll_records`, `hr_payroll_components`
- **Data**: Payroll components

## Sales Reports

### Sales Order Report
- **Source Tables**: `sales_orders`, `sales_order_lines`
- **Data**: 134 orders, 45 order lines

### Sales Invoice Report
- **Source Tables**: `sales_invoices`, `sales_invoice_lines`
- **Data**: 20 invoices

### Customer Sales Summary
- **Source Tables**: `sales_customers`, `sales_orders`
- **Data**: 58 customers

### Quotations Conversion
- **Source Tables**: `sales_quotations`, `sales_quotation_lines`
- **Data**: 68 quotations

### Sales Pipeline
- **Source Tables**: `sales_opportunities`, `sales_inquiries`
- **Data**: 71 inquiries

## Procurement Reports

### Purchase Order Report
- **Source Tables**: `procurement_purchase_orders`, `procurement_po_lines`
- **Data**: 1 PO (demo data)

### Supplier Performance
- **Source Tables**: `suppliers`, `procurement_supplier_metrics`
- **Data**: 40 suppliers

### RFQ Analysis
- **Source Tables**: `procurement_rfqs`, `procurement_rfq_lines`
- **Data**: 15 RFQs

### Receipts Report
- **Source Tables**: `procurement_receiving`
- **Data**: 1 receiving record

## Quality Reports

### Inspection Summary
- **Source Tables**: `quality_inspections`
- **Data**: 20 inspections

### NCR Report
- **Source Tables**: `quality_non_conformances`
- **Data**: 10 NCRs

### CAPA Report
- **Source Tables**: `quality_capa_records`, `quality_capa_actions`
- **Data**: 8 CAPAs

### Defect Analysis
- **Source Tables**: `quality_defect_categories`, `quality_inspections`
- **Data**: 8 defect categories

## Workflow Reports

### Pending Approvals
- **Source Tables**: `workflow_instances`, `workflow_instance_steps`
- **Data**: 3 active instances

### SLA Compliance
- **Source Tables**: `workflow_instances`
- **Data**: Instance timestamps

### Process Metrics
- **Source Tables**: `workflow_definitions`, `workflow_versions`
- **Data**: 4 definitions

## Document Reports

### Document Inventory
- **Source Tables**: `documents`, `document_versions`
- **Data**: 12 documents, 12 versions

### Access Audit
- **Source Tables**: `document_access_logs`
- **Data**: 28 access log entries

### Retention Status
- **Source Tables**: `document_retention_policies`, `document_retention_schedules`
- **Data**: Retention policy rules

## Validation Status

| Report Category | Status | Record Count |
|-----------------|--------|--------------|
| Finance | OK | 300+ rows |
| Treasury | OK | 400+ rows |
| WMS | OK | 4,500+ rows |
| HR | OK | 250+ rows |
| Sales | OK | 350+ rows |
| Procurement | OK | 60+ rows |
| Quality | OK | 40+ rows |
| Workflow | OK | 10+ rows |
| Documents | OK | 50+ rows |