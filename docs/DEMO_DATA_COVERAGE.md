# MMDx Demo Data Coverage Report

## Overview

This document tracks the demo/sample data coverage across all MMDx modules. The goal is to ensure every meaningful page, dashboard, table, and report has realistic, relational sample data for demonstration and testing purposes.

---

## Coverage Status Summary

| Module | Status | Seed File(s) | Tables Seeded |
|--------|--------|--------------|---------------|
| **HR** | ✅ Complete | `seed_sample_data.py`, `seed_all.py` | employees, departments, positions, attendance, leave, loans, bonuses, deductions |
| **WMS** | ✅ Complete | `seed_data.py`, `seed_wms_extended_data.py` | parts, inventory, warehouses, locations, zones |
| **Procurement** | ✅ Complete | `seed_procurement_data.py` | requisitions, RFQs, quotations, purchase orders, shipments |
| **Sales** | ✅ Complete | `seed_sample_data.py`, `seed_all.py` | customers, inquiries, opportunities, quotations, orders |
| **Finance** | ✅ Complete | `seed_finance_data.py` | accounts, invoices, receipts, bills, payments, budgets |
| **Quality** | ✅ Complete | `seed_quality_data.py` | inspections, NCRs, CAPAs, audit plans |
| **Maintenance** | ✅ Complete | `seed_maintenance_data.py` | facilities, teams, work orders, schedules |
| **Assets** | ✅ Complete | `seed_asset_data.py` | assets, categories, acquisitions, assignments |
| **Logistics** | ✅ Complete | `seed_logistics_data.py` | vehicles, drivers, routes, delivery trips |
| **E-commerce** | ✅ Complete | `seed_ecommerce_data.py` | channels, products, orders, sync logs |
| **Documents** | ✅ Complete | `seed_document_data.py` | documents, versions, categories, signatures |
| **Workflow** | ✅ Complete | `seed_workflow_data.py` | definitions, instances, steps, rules |
| **API Gateway** | ✅ Complete | `seed_api_gateway_data.py` | clients, credentials, profiles, logs |
| **BI/Reporting** | ✅ Complete | `seed_bi_data.py` | datasets, KPIs, reports, schedules |
| **Marketing** | ✅ Complete | `seed_marketing_data.py` | brands, campaigns, leads, segments, channels |
| **Social Media** | ✅ Complete | `seed_social_media_data.py` | accounts, content, campaigns, ads, leads |
| **Company** | ✅ Complete | `seed_all.py` | companies, branches |

---

## Module-by-Module Coverage Details

### HR Module ✅

**Tables Seeded:**
- `hr_departments` - 8 departments (Executive, Sales, HR, Finance, Operations, Procurement, IT, QA)
- `hr_positions` - 15 positions across all departments
- `hr_employees` - 15 employees with employment records
- `hr_leave_types` - 5 leave types (Annual, Sick, Emergency, Maternity, Paternity)
- `hr_leave_requests` - Multiple leave requests with varied statuses
- `hr_attendance_records` - 30 days of attendance for all employees
- `hr_leave_balances` - Leave balances for current year
- `hr_loans` - 4 loans (Active and Closed)
- `hr_bonus_records` - Multiple bonus records per employee
- `hr_deduction_records` - Multiple deduction records per employee

**Dashboard KPIs:**
- Total employees count
- Attendance rate
- Leave requests pending
- Active loans

---

### WMS Module ✅

**Tables Seeded:**
- `parts` - 40 parts with OEM numbers
- `categories` - 6 categories (Filters, Brakes, Suspension, etc.)
- `brands` - 6 brands (Toyota Genuine, Bosch, Denso, etc.)
- `statuses` - 4 statuses (Active, Discontinued, Recalled, Backordered)
- `inventory` - Inventory across multiple companies/locations
- `warehouses` - 4 warehouses
- `wms_zones` - Zones per warehouse (Receiving, Storage, Picking, Shipping, etc.)
- `wms_locations` - Location codes (Zone-Aisle-Rack-Level)
- `wms_inventory_balances` - Current stock by location
- `wms_inventory_movements` - Stock movements

**Dashboard KPIs:**
- Total parts count
- Inventory value
- Low stock alerts
- Recent movements

---

### Procurement Module ✅

**Tables Seeded:**
- `suppliers` - Multiple suppliers with contacts
- `procurement_requisitions` - 15 requisitions with lines
- `procurement_rfqs` - 10 RFQs with lines
- `procurement_quotations` - Quoted items from RFQs
- `purchase_orders` - 12 POs with varied statuses
- `purchase_order_lines` - Multiple line items per PO
- `procurement_shipments` - Shipment tracking
- `procurement_receiving` - Receipt records

**Dashboard KPIs:**
- Pending requisitions
- Active RFQs
- Open POs value
- Recent receipts

---

### Sales Module ✅

**Tables Seeded:**
- `sales_customers` - 8 customers (Enterprise, Corporate, Government, SMB)
- `sales_inquiries` - 8 inquiries with varied statuses
- `sales_opportunities` - Opportunities from converted inquiries
- `sales_quotations` - 8 quotations with amounts
- `sales_orders` - Orders from quotations
- `sales_order_lines` - Line items
- `sales_deliveries` - Delivery records
- `sales_returns` - Return records

**Dashboard KPIs:**
- Today's inquiries
- Today's quotations
- Open orders
- Monthly revenue

---

### Finance Module ✅

**Tables Seeded:**
- `finance_account_categories` - 8 categories (Assets, Liabilities, Equity, etc.)
- `finance_accounts` - 50+ accounts in chart of accounts
- `fiscal_years` - Current and past fiscal years
- `fiscal_periods` - Monthly periods
- `journals` - Journal entries
- `journal_entries` - Detailed journal lines
- `customer_invoices` - 10+ AR invoices
- `customer_receipts` - Payment receipts
- `supplier_bills` - 10+ AP bills
- `supplier_payments` - Payment records
- `finance_assets` - Fixed assets records
- `depreciation_methods` - Depreciation methods
- `cost_centers` - Cost center tracking
- `budgets` - Budget allocations
- `tax_codes` - VAT and tax codes

**Dashboard KPIs:**
- Total receivables
- Total payables
- Cash position
- This month revenue

---

### Quality Module ✅

**Tables Seeded:**
- `quality_inspection_types` - Incoming, in-process, outgoing inspections
- `quality_inspections` - 10 inspections with varied results
- `quality_non_conformances` - 5 NCRs (critical, major, minor)
- `quality_capa_records` - 4 CAPAs (corrective, preventive)
- `quality_audit_plans` - 3 audit plans

**Dashboard KPIs:**
- Open NCRs
- Pending CAPAs
- Inspection pass rate
- Upcoming audits

---

### Maintenance Module ✅

**Tables Seeded:**
- `maintenance_facilities` - 5 facilities
- `maintenance_teams` - 5 teams with specializations
- `maintenance_team_members` - Team assignments
- `maintenance_types` - PM schedule types
- `maintenance_schedules` - 12 preventive maintenance schedules
- `maintenance_work_orders` - Work orders with varied statuses
- `maintenance_work_logs` - Labor and parts usage

**Dashboard KPIs:**
- Open work orders
- Scheduled PMs
- Active facilities
- Overdue maintenance

---

### Assets Module ✅

**Tables Seeded:**
- `asset_categories` - IT Equipment, Office Furniture, Vehicles, etc.
- `assets` - 20+ assets (laptops, monitors, furniture, vehicles)
- `asset_acquisitions` - Acquisition records
- `asset_assignments` - Asset assignments to employees
- `depreciation_methods` - Straight-line, declining balance
- `asset_depreciation_profiles` - Depreciation settings
- `depreciation_runs` - Depreciation calculation runs
- `maintenance_types` - Maintenance types
- `maintenance_schedules` - PM schedules for assets
- `maintenance_work_orders` - Work orders
- `disposal_requests` - Disposal requests

**Dashboard KPIs:**
- Total asset value
- Assets by category
- Upcoming depreciation
- Pending disposals

---

### Logistics Module ✅

**Tables Seeded:**
- `logistics_vehicles` - 8 vehicles (vans, trucks)
- `logistics_drivers` - 8 drivers with licenses
- `logistics_route_masters` - 8 routes with distances
- `delivery_trips` - 48 trips (last 7 days + today)
- `logistics_shipments` - Shipment records
- `logistics_pickup_orders` - Pickup requests
- `logistics_cost_entries` - Trip costs

**Dashboard KPIs:**
- Active vehicles
- Today's deliveries
- On-time rate
- Fleet mileage

---

### E-commerce Module ✅

**Tables Seeded:**
- `ecommerce_channels` - 5 channels (Shopify, Amazon, WooCommerce, Etsy)
- `ecommerce_channel_profiles` - Channel-specific settings
- `ecommerce_product_mappings` - Product-sync mappings
- `ecommerce_category_mappings` - Category mappings
- `ecommerce_order_imports` - 20 imported orders
- `ecommerce_order_lines` - Order line items
- `ecommerce_sync_logs` - Sync history
- `ecommerce_exceptions` - Exception records

**Dashboard KPIs:**
- Total orders
- Sync status
- Pending imports
- Exception count

---

### Documents Module ✅

**Tables Seeded:**
- `document_categories` - Contract, Quotation, Report, Manual categories
- `documents` - 15+ documents with tags
- `document_versions` - Version history
- `document_templates` - Template placeholders
- `document_links` - Linked records
- `signature_requests` - Pending signatures
- `document_shares` - Share records
- `document_access_logs` - Access audit trail

**Dashboard KPIs:**
- Total documents
- Pending signatures
- Recent uploads
- Expiring documents

---

### Workflow Module ✅

**Tables Seeded:**
- `workflow_definitions` - 5 workflow types (Sales Order, PO, Leave, NCR, Requisition)
- `workflow_versions` - Version history
- `workflow_steps` - Step definitions
- `workflow_instances` - 10+ active instances
- `workflow_instance_steps` - Current step status
- `workflow_actions` - Action logs
- `automation_rules` - Auto-approval rules
- `notification_templates` - Notification templates
- `sla_rules` - SLA definitions

**Dashboard KPIs:**
- Active workflows
- Pending approvals
- Overdue items
- Average resolution time

---

### API Gateway Module ✅

**Tables Seeded:**
- `api_versions` - API version management
- `api_route_registry` - Endpoint registry
- `api_clients` - 5 API clients
- `api_client_credentials` - Client credentials
- `api_scopes` - Permission scopes
- `api_access_policies` - Access policies
- `integration_profiles` - 3 profiles (E-commerce, Accounting, Shipping)
- `integration_runs` - Integration run history
- `integration_exceptions` - Exception logs
- `webhook_events` - Webhook event types
- `webhook_subscriptions` - Subscriptions
- `webhook_deliveries` - Delivery attempts

**Dashboard KPIs:**
- Total API calls
- Error rate
- Active integrations
- Webhook deliveries

---

### BI/Reporting Module ✅

**Tables Seeded:**
- `reporting_datasets` - 10 datasets across domains
- `dataset_fields` - Field definitions with metadata
- `reporting_kpis` - 20+ KPIs (Financial, Sales, HR, Operations)
- `saved_reports` - Pre-built reports
- `report_schedules` - Scheduled deliveries
- `adhoc_queries` - Saved query definitions
- `query_logs` - Query execution logs
- `report_access_logs` - Access tracking
- `export_logs` - Export history
- `approval_requests` - BI approval workflows

**Dashboard KPIs:**
- Total datasets
- Active KPIs
- Recent reports
- Scheduled deliveries

---

### Marketing Module ✅

**Tables Seeded:**
- `marketing_brands` - 4 brands (Premium, Economy, Professional, Classic)
- `marketing_market_intelligence` - 8 intelligence reports
- `marketing_customer_segments` - 5 segments
- `marketing_channels` - 6 channels (Website, Social, Email, etc.)
- `marketing_campaigns` - 6 campaigns (Seasonal, B2B, Brand)
- `marketing_leads` - 20 leads with varied statuses
- `marketing_funnel_stages` - 6 stages (Awareness to Retention)
- `marketing_offers` - 4 active offers
- `marketing_budgets` - 5 budget items
- `marketing_performance_metrics` - KPI tracking

**Dashboard KPIs:**
- Active campaigns
- Lead conversion rate
- Budget utilization
- Campaign ROI

---

### Social Media Module ✅

**Tables Seeded:**
- `social_accounts` - 5 accounts (Instagram, LinkedIn, Twitter, Facebook, WhatsApp)
- `social_content_calendar` - 15 scheduled posts
- `social_content_production` - 10 content items
- `social_publish_queue` - 8 queued posts
- `social_campaigns` - 6 campaigns
- `social_ads` - 10 ad creatives
- `social_leads` - 15 social leads
- `social_audiences` - 5 audience segments
- `social_kpis` - 6 performance metrics
- `social_monitoring` - 4 keyword monitors

**Dashboard KPIs:**
- Total followers
- Engagement rate
- Active campaigns
- Lead generation

---

## Data Relationships

All seeded data maintains proper relationships:

- **Purchase Orders** → connect to Suppliers, Employees, and Status
- **Sales Orders** → connect to Customers, Products, and Delivery status
- **Invoices** → connect to Customers, Line Items, and Payment status
- **Assets** → connect to Categories, Employees, and Depreciation profiles
- **Work Orders** → connect to Equipment, Technicians, and Status
- **Inspections** → connect to Items/Suppliers/Locations and Inspector
- **Workflow Instances** → connect to Module records and Approval steps
- **Documents** → connect to Categories, Owners, Tags, and Versions
- **API Logs** → connect to Clients, Endpoints, and Status codes

---

## Seed Scripts Location

All seed scripts are located in the project root:

```
MMDx/
├── seed_all.py                 # Master orchestrator
├── seed_sample_data.py         # Core HR and base data
├── seed_data.py                # Basic WMS parts and inventory
├── seed_wms_extended_data.py   # Extended WMS (locations, zones)
├── seed_procurement_data.py    # Procurement module
├── seed_finance_data.py        # Finance module
├── seed_quality_data.py        # Quality module
├── seed_maintenance_data.py    # Maintenance module
├── seed_asset_data.py          # Asset management
├── seed_logistics_data.py      # Logistics/delivery
├── seed_ecommerce_data.py      # E-commerce
├── seed_document_data.py       # Document management
├── seed_workflow_data.py       # Workflow/BPM
├── seed_api_gateway_data.py    # API Gateway
├── seed_bi_data.py             # BI/Reporting
├── seed_marketing_data.py      # Marketing module
├── seed_social_media_data.py  # Social Media module
```

---

## Running the Seeds

### Run All Seeds
```bash
python seed_all.py
```

### Check Coverage Status
```bash
python seed_all.py --status
```

### Seed Specific Module
```bash
python seed_all.py --module hr
python seed_all.py --module sales
python seed_all.py --module finance
```

### Run Individual Seed
```bash
python seed_hr_data.py
python seed_marketing_data.py
python seed_social_media_data.py
```

---

## Demo Users

After seeding, the following demo users are available:

| Username | Password | Role | Email |
|----------|----------|------|-------|
| admin | admin123 | Global Admin | admin@warehouse.local |
| demo | demo123 | Manager | demo@warehouse.local |
| manager | manager123 | Department Manager | manager@warehouse.local |

---

## Remaining Gaps

The following areas may still need business-specific data that cannot be generically seeded:

1. **Industry-specific part numbers** - Part numbers may need to match actual supplier catalogs
2. **Realistic pricing** - Prices may need to reflect actual market conditions
3. **Localized content** - Arabic/Persian translations for specific terminology
4. **Integration credentials** - Real API keys for external system integrations
5. **Company-specific workflows** - Custom approval rules based on company policy

---

## Adding New Seed Data

When adding new features or modules:

1. Create a `seed_<module>_data.py` file
2. Follow the idempotent pattern: check if data exists before inserting
3. Use realistic, connected data (no "test1", "test2" names)
4. Include varied statuses (Active, Pending, Completed, etc.)
5. Include date spread (not all records from today)
6. Add the seed function to `seed_all.py`
7. Update this document with new module coverage

---

*Last Updated: 2026-04-08*