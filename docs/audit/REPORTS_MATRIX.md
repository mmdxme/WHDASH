# MMDx Reports Matrix
**Date:** Wednesday April 8, 2026  
**Project:** MMDx - Flask-based ERP Platform  

---

## Overview

This document lists all report routes and templates across the MMDx modules.

---

## Reports by Module

### planning - Planning (3+ reports)

| Report | Route | Template |
|--------|-------|----------|
| Forecast Accuracy | /planning/reports | templates/planning/ |
| Inventory Turnover | /planning/reports | templates/planning/ |
| Demand Analysis | /planning/demand-analysis | templates/planning/demand_analysis.html |
| Purchase Suggestions | /planning/purchase-suggestions | templates/planning/purchase_suggestions.html |
| Inventory Health | /planning/inventory-health | templates/planning/inventory_health.html |
| Safety Stock Rules | /planning/safety-stock-rules | templates/planning/safety_stock_rules.html |

### quality - Quality Management (5+ reports)

| Report | Route | Template |
|--------|-------|----------|
| Inspection Report | /quality/inspections | templates/quality/inspections/list.html |
| NCR Report | /quality/ncr | templates/quality/ncr/ |
| CAPA Report | /quality/capa | templates/quality/capa/ |
| Supplier Quality Report | /quality/supplier-quality | templates/quality/ |
| Audit Findings Report | /quality/audit-findings | templates/quality/audit_findings.html |

### assets - Asset Management (5+ reports)

| Report | Route | Template |
|--------|-------|----------|
| Asset Register Report | /assets/reports | templates/assets/reports.html |
| Depreciation Report | /assets/depreciation-report | templates/assets/ |
| Maintenance Report | /assets/maintenance-report | templates/assets/ |
| Disposal Report | /assets/disposal-report | templates/assets/ |
| Asset Summary | /assets/summary | templates/assets/ |

### wms - Warehouse Management (5+ reports)

| Report | Route | Template |
|--------|-------|----------|
| Inventory Summary | /wms/reports/inventory-summary | templates/wms/report_inventory_summary.html |
| Expiry Report | /wms/reports/expiry | templates/wms/report_expiry.html |
| Stock Valuation | /reports/valuation_details | templates/stock_summary_report.html |
| Stock Movement | /wms/movements | templates/wms/ |
| Location Utilization | /wms/locations | templates/wms/locations.html |

### maintenance - Maintenance Management (7+ reports)

| Report | Route | Template |
|--------|-------|----------|
| Equipment List | /maintenance/equipment | templates/maintenance/equipment_list.html |
| Work Orders Report | /maintenance/work-orders-report | templates/maintenance/ |
| PM Schedule Report | /maintenance/pm-schedules | templates/maintenance/pm_schedules.html |
| Downtime Analysis | /maintenance/downtime-list | templates/maintenance/downtime_list.html |
| Parts Usage Report | /maintenance/parts-usage | templates/maintenance/ |
| Labor Report | /maintenance/labor-logs | templates/maintenance/ |
| Facility Status | /maintenance/facilities | templates/maintenance/ |

### ecommerce - E-commerce Integration (4 reports)

| Report | Route | Template |
|--------|-------|----------|
| Channel Sales Report | /ecommerce/reports/channel-sales | templates/ecommerce/ |
| Sync Status Report | /ecommerce/reports/sync-status | templates/ecommerce/ |
| Exception Report | /ecommerce/reports/exceptions | templates/ecommerce/ |
| Orders Report | /ecommerce/orders | templates/ecommerce/orders/ |

### logistics - Logistics & Delivery (1+ reports)

| Report | Route | Template |
|--------|-------|----------|
| Delivery Performance | /delivery_report | templates/delivery_report.html |
| Trip Summary | /delivery | templates/delivery.html |
| Customer Delivery Table | /delivery/customer_table | templates/delivery.html |

### documents - Document Management (6+ reports)

| Report | Route | Template |
|--------|-------|----------|
| Activity Report | /documents/reports/activity | templates/documents/report_activity.html |
| Version History Report | /documents/reports/version-history | templates/documents/report_version_history.html |
| Signature Status Report | /documents/reports/signature-status | templates/documents/report_signature_status.html |
| Access Log Report | /documents/reports/access-log | templates/documents/report_access_log.html |
| Expiring Documents | /documents/reports/expiring | templates/documents/report_expiring.html |
| Activity Logs | /documents/audit_logs | templates/documents/audit_logs.html |

### sales - Sales & Orders (4+ reports)

| Report | Route | Template |
|--------|-------|----------|
| Sales Summary | /sales/reports/sales-summary/ | templates/sales/reports/sales_summary.html |
| Sales by Item | /sales/reports/sales-by-item/ | templates/sales/reports/sales_by_item.html |
| Inquiry Conversion | /sales/reports/inquiry-conversion/ | templates/sales/reports/inquiry_conversion.html |
| Customer Report | /sales/reports/customer/ | templates/sales/reports/ |
| Performance | /sales/reports/ | templates/sales/reports/index.html |

### hr - Human Resources (4+ reports)

| Report | Route | Template |
|--------|-------|----------|
| Headcount Report | /hr/reports/headcount | templates/hr/reports/headcount.html |
| Attendance Report | /hr/reports/attendance | templates/hr/reports/ |
| Leave Balance | /hr/reports/leave | templates/hr/reports/ |
| Payroll Summary | /hr/reports/payroll | templates/hr/reports/ |

### marketing - Marketing (4+ reports)

| Report | Route | Template |
|--------|-------|----------|
| Campaign Performance | /marketing/reports/campaign | templates/marketing/report_channel.html |
| Lead Report | /marketing/reports/lead | templates/marketing/report_lead.html |
| Channel Analysis | /marketing/reports/channel | templates/marketing/report_channel.html |
| Budget vs Actual | /marketing/reports/budget | templates/marketing/ |

### social_media - Social Media (2+ reports)

| Report | Route | Template |
|--------|-------|----------|
| Engagement Report | /social-media/reports | templates/social_media/ |
| Content Performance | /social-media/reports/content | templates/social_media/ |

### bi - Business Intelligence (2+ reports)

| Report | Route | Template |
|--------|-------|----------|
| Executive Dashboard | /executive-dashboard | templates/bi/executive_dashboard.html |
| Holding Dashboard | /holding-dashboard | templates/bi/ |
| Company Comparison | /bi/company-comparison | templates/bi/ |

### bi_advanced - Advanced Analytics (3+ reports)

| Report | Route | Template |
|--------|-------|----------|
| BI Dashboard | /bi/dashboard | templates/bi_advanced/dashboard.html |
| Dataset Reports | /bi/datasets | templates/bi_advanced/datasets/ |
| Scheduled Reports | /bi/reports | templates/bi_advanced/reports/ |
| KPI Reports | /bi/kpis | templates/bi_advanced/kpis/ |

### finance - Finance & Accounting (4+ reports)

| Report | Route | Template |
|--------|-------|----------|
| AR Aging | /finance/ar-aging | templates/finance/ |
| AP Aging | /finance/ap-aging | templates/finance/ |
| Trial Balance | /finance/trial-balance | templates/finance/ |
| GL Summary | /finance/reports/general-ledger | templates/finance/ |
| Budget Report | /finance/budgets | templates/finance/ |

### procurement - Procurement (3+ reports)

| Report | Route | Template |
|--------|-------|----------|
| Spend Analysis | /procurement/reports/spend-analysis | templates/procurement/reports/spend_analysis.html |
| Supplier Performance | /procurement/performance | templates/procurement/ |
| PO Status | /procurement/orders | templates/procurement/orders/ |

### sales_suite - Sales Suite (3+ reports)

| Report | Route | Template |
|--------|-------|----------|
| Sales Suite Dashboard | /sales-suite/dashboard | templates/sales/sales_suite_dashboard.html |
| Overview Reports | /sales-suite/reports | templates/sales/ |

### workflow - Workflow & BPM (1+ reports)

| Report | Route | Template |
|--------|-------|----------|
| Performance Report | /workflow/reports/performance | templates/workflow/reports/ |
| Cycle Time Analysis | /workflow/reports/cycle-time | templates/workflow/reports/ |

---

## Modules Without Dedicated Reports

| Module | Notes |
|--------|-------|
| company | Cross-company reporting exists via BI module |
| admin | Settings-focused, reports less relevant |
| profile | User-specific data, no separate reports |
| api_gateway | Monitoring pages serve as reports (usage, errors, rate limits) |

---

## Report Features Checklist

| Feature | Modules Supporting |
|---------|-------------------|
| CSV Export | logistics, documents, sales, api_gateway |
| Excel Export | wms, finance, procurement |
| Date Filters | all modules |
| Status Filters | most modules |
| Search | most modules |
| Pagination | all list views |
| Charts/Visualizations | bi, bi_advanced, finance, logistics |
| Drill-down | bi, bi_advanced, wms, finance |

---

*Reports Matrix Generated: Wednesday April 8, 2026*