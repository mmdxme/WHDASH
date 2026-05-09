# MMDx Enterprise Sample Data Strategy

## Overview

This document describes the comprehensive sample data strategy for the WHDASH (MMDx) enterprise platform. The goal is to populate the entire system with realistic, relational, cross-linked demo data that makes the platform feel complete, alive, and enterprise-grade.

## Business Context

The demo data is designed for an **auto spare parts trading and warehouse operations company** operating in the **UAE/GCC region** with:

- Multiple companies and branches
- Warehouse operations (receiving, storage, picking, shipping)
- Import/export operations
- Finance, procurement, and sales operations
- HR and maintenance departments
- Quality control and compliance
- Documents and workflow management

## Data Architecture

### Database Type
- **Primary**: SQLite (development/demo)
- **Production-Ready**: PostgreSQL architecture (connection strings configured)

### Relational Integrity
All sample data maintains referential integrity through:
- Foreign key constraints (enforced via PRAGMA foreign_keys=ON)
- Proper parent-child relationships
- Cross-module linking via IDs

## Module Coverage

### 1. Organizational Structure
| Module | Tables Populated | Sample Entities |
|--------|------------------|-----------------|
| Companies | companies | MMDx Holding, SDAD, AFRA, Carmania |
| Branches | company_branches | Dubai HQ, Jebel Ali, Abu Dhabi |
| Departments | hr_departments | Finance, Operations, Sales, HR, IT |

### 2. HR Module
| Table | Sample Data |
|-------|-------------|
| hr_employees | 94 employees across all departments |
| hr_departments | 8 departments with hierarchy |
| hr_attendance_records | 139 attendance entries |
| hr_leave_requests | Leave requests in various statuses |

### 3. WMS Module
| Table | Sample Data |
|-------|-------------|
| parts | 322 auto spare parts with brands |
| inventory | 3983 inventory locations |
| warehouses | 21 warehouses/zones |
| wms_waves | 10 pick waves |
| wms_wave_templates | 5 wave templates |

### 4. Procurement
| Table | Sample Data |
|-------|-------------|
| suppliers | 40 suppliers (Bosch, Michelin, Shell, etc.) |
| procurement_requisitions | Purchase requisitions |
| procurement_purchase_orders | POs in various statuses |

### 5. Sales
| Table | Sample Data |
|-------|-------------|
| sales_customers | 58 customers (Al Futtaim, Emirates Trading, etc.) |
| sales_inquiries | 71 sales inquiries |
| sales_quotations | 68 quotations |
| sales_orders | 134 sales orders |

### 6. Finance
| Table | Sample Data |
|-------|-------------|
| finance_accounts | 86 GL accounts |
| finance_fiscal_years | FY 2024, 2025, 2026 |
| finance_fiscal_periods | 36 monthly periods |
| finance_journals | Journal entries with debit/credit |
| finance_customer_invoices | AR invoices |
| finance_supplier_bills | AP bills |
| finance_budgets | Budget allocations |
| finance_cost_centers | 8 cost centers |

### 7. Treasury
| Table | Sample Data |
|-------|-------------|
| treasury_settings | 10 settings |
| treasury_cash_movements | 50 cash movements |
| treasury_collections | 5 AR collections |
| treasury_alerts | 6 treasury alerts |
| treasury_cash_boxes | 4 cash boxes |
| treasury_petty_cash_accounts | 4 petty cash accounts |
| treasury_forecasts | 3 forecast scenarios |
| treasury_payment_runs | Payment batch records |

### 8. Quality
| Table | Sample Data |
|-------|-------------|
| quality_inspections | 20 inspections |
| quality_non_conformances | 10 NCRs |
| quality_capa_records | 8 CAPAs |

### 9. Maintenance
| Table | Sample Data |
|-------|-------------|
| maintenance_facilities | 5 facilities |
| maintenance_work_orders | 35 work orders |

### 10. Fixed Assets
| Table | Sample Data |
|-------|-------------|
| assets | 44 assets |
| asset_categories | 10 categories |
| asset_acquisitions | Asset acquisitions |
| asset_depreciation_schedules | Depreciation tracking |

### 11. Logistics
| Table | Sample Data |
|-------|-------------|
| logistics_vehicles | 15 vehicles |
| logistics_drivers | 20 drivers |
| delivery_trips | 3 delivery trips |

### 12. E-commerce
| Table | Sample Data |
|-------|-------------|
| ecommerce_channels | 5 channels |
| ecommerce_orders | Orders and sync jobs |

### 13. Documents
| Table | Sample Data |
|-------|-------------|
| documents | 12 documents |
| document_categories | Category definitions |
| document_folders | 29 folders |
| document_templates | 5 templates |

### 14. Workflow
| Table | Sample Data |
|-------|-------------|
| workflow_definitions | 4 workflow definitions |
| workflow_instances | 3 running instances |

### 15. Marketing
| Table | Sample Data |
|-------|-------------|
| marketing_brands | Brand definitions |
| marketing_campaigns | 220 campaigns |
| marketing_leads | 900 leads |

### 16. Social Media
| Table | Sample Data |
|-------|-------------|
| social_accounts | 55 accounts |
| social_campaigns | 15 campaigns |
| social_leads | 420 leads |

## Seed Scripts

### Master Scripts
| Script | Purpose |
|--------|---------|
| `seed_enterprise_demo.py` | Unified orchestrator for all modules |
| `seed_all.py` | Legacy comprehensive seeder |
| `seed_treasury_data.py` | Treasury module seeder |
| `seed_wms_extended_data.py` | WMS waves, templates, returns |

### Module Scripts
| Script | Module |
|--------|--------|
| `seed_sample_data.py` | Core base data |
| `seed_finance_data.py` | Finance module |
| `seed_wms_sample_data.py` | WMS base data |
| `seed_procurement_data.py` | Procurement |
| `seed_sales_suite.py` | Sales module |
| `seed_quality_data.py` | Quality module |
| `seed_asset_data.py` | Fixed assets |
| `seed_logistics_data.py` | Logistics |
| `seed_maintenance_data.py` | Maintenance |
| `seed_workflow_data.py` | Workflow |
| `seed_document_data.py` | Documents |
| `seed_org_planning.py` | Org planning |
| `seed_marketing_data.py` | Marketing |
| `seed_social_media_data.py` | Social media |
| `seed_ecommerce_data.py` | E-commerce |

## Usage

### Seed All Modules
```bash
python seed_enterprise_demo.py
```

### Check Coverage Status
```bash
python seed_enterprise_demo.py --status
```

### Seed Specific Module
```bash
python seed_enterprise_demo.py --module treasury
```

### Show Available Profiles
```bash
python seed_enterprise_demo.py --profiles
```

## Data Characteristics

### Realistic Range
- Dates distributed across current year and past 90 days
- Status values distributed: Draft, Active, Pending, Approved, Rejected
- Amounts realistic for UAE/GCC market (AED currency)
- Part numbers as text strings (not auto-incrementing integers)

### Cross-Module Linking
- Customer IDs link sales orders to AR invoices
- Supplier IDs link POs to AP bills
- Employee IDs link to attendance, leave, and payroll
- Warehouse IDs link inventory to WMS operations

### Multilingual Support
- Arabic/Persian translations for key labels
- Part numbers and codes in standard formats
- Date formats DD/MM/YYYY (UAE standard)

## Maintenance

### Idempotency
All seed scripts are idempotent - safe to run multiple times without creating duplicates.

### Reset Strategy
To reset demo data, run the specific module seeder after clearing the target tables.

## Success Metrics

- Total rows seeded: ~7000+ across all modules
- Zero empty critical modules
- All dashboards show real data
- All reports return meaningful results