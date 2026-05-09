# CRM Architecture Document

## Overview

The CRM module extends the existing Sales module to provide enterprise-grade customer relationship management capabilities. It is built as an integral part of the WHDASH platform, sharing the same database, authentication, permissions, and translation systems.

## Architecture Principles

### 1. Integration First
- CRM reuses existing Sales tables where possible (`sales_customers`, `sales_opportunities`, `sales_quotations`, `sales_activities`)
- New CRM-specific tables are created for capabilities not covered by Sales
- Routes are registered under `/crm/*` to distinguish from `/sales/*`

### 2. Extensibility
- CRM models (`crm_models.py`) provide a service layer that can be extended
- Lead scoring algorithm is configurable and future-ML-ready
- Journey tracking architecture supports future AI/ML analytics

### 3. Permission-Aware Design
- All CRM routes use the `crm_permission_required` decorator
- Permissions follow the pattern: `('crm', resource, action)`
- Admins can access all CRM features; other roles need explicit grants

## Database Schema

### Core CRM Tables

#### `crm_leads`
Primary lead management table with scoring and lifecycle tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| lead_number | TEXT | Unique identifier (LEAD-YYYY-NNNNN) |
| company_name | TEXT | Company name |
| contact_name | TEXT | Primary contact name |
| contact_title | TEXT | Contact job title |
| phone | TEXT | Phone number |
| whatsapp | TEXT | WhatsApp number |
| email | TEXT | Email address |
| website | TEXT | Company website |
| source | TEXT | Lead source (referral, website, etc.) |
| status | TEXT | Lifecycle status |
| priority | TEXT | Priority level |
| is_hot | INTEGER | Hot lead flag |
| industry | TEXT | Industry classification |
| lead_score | INTEGER | Calculated lead score (0-100) |
| estimated_value | REAL | Estimated deal value |
| assigned_to | INTEGER | FK to users |
| converted_customer_id | INTEGER | FK to sales_customers after conversion |
| converted_opportunity_id | INTEGER | FK to sales_opportunities after conversion |

#### `crm_lead_activities`
Activity log for lead engagement tracking.

#### `crm_lead_qualifications`
BANT qualification criteria scoring.

#### `crm_complaints`
Customer complaint and service case tracking.

#### `crm_key_accounts`
Strategic account management with objectives and reviews.

#### `crm_journey_events`
Customer journey touchpoints across all interactions.

#### `crm_customer_engagement`
Calculated engagement scores per customer.

#### `crm_customer_churn_risk`
Churn risk assessment per customer.

#### `crm_segments` / `crm_customer_segments`
Customer segmentation support.

### Extension Tables (shared with Sales)
- `sales_activities` - Activity log (shared with CRM)
- `sales_customers` - Customer master (shared with CRM)
- `sales_opportunities` - Opportunities (shared with CRM)

## Module Structure

### Routes (`crm_routes.py`)

```
/crm/dashboard/          → CRM Executive Dashboard
/crm/leads/              → Lead list
/crm/leads/new/          → Create lead
/crm/leads/<id>/         → View lead
/crm/leads/<id>/edit/    → Edit lead
/crm/leads/<id>/convert/ → Convert lead to customer/opportunity
/crm/leads/<id>/activity/ → Add lead activity (POST)

/crm/opportunities/      → Opportunities list
/crm/opportunities/pipeline/ → Pipeline Kanban view

/crm/activities/         → Activity log
/crm/activities/new/     → Log activity
/crm/activities/calendar/ → Calendar view

/crm/complaints/          → Complaints list
/crm/complaints/new/      → Create complaint
/crm/complaints/<id>/     → View complaint
/crm/complaints/<id>/update/ → Update complaint (POST)

/crm/key-accounts/       → Key accounts list
/crm/key-accounts/<id>/  → View account

/crm/forecasts/          → Forecasts

/crm/reports/             → Reports center
/crm/reports/lead-conversion/ → Lead conversion report
/crm/reports/pipeline/   → Pipeline analysis
/crm/reports/customer-analysis/ → Customer analysis

/crm/customer-360/<id>/  → Customer 360 view
/crm/journey/<id>/       → Customer journey view

/crm/settings/            → Settings
```

### Models (`crm_models.py`)

**Lead Management**
- `get_leads()` - Paginated lead list with filters
- `get_lead_by_id()` - Lead with activities, contacts, qualifications
- `create_lead()` - Create with auto-numbering
- `update_lead()` - Update with score recalculation
- `calculate_lead_score()` - Configurable scoring algorithm
- `convert_lead_to_customer()` - Convert to Sales customer
- `convert_lead_to_opportunity()` - Convert to Sales opportunity

**Customer 360**
- `get_customer_360()` - Complete customer view
- `calculate_customer_engagement_score()` - Engagement calculation
- `calculate_churn_risk()` - Risk assessment with factors

**Opportunities**
- `get_crm_opportunities()` - Enhanced opportunity list
- `get_opportunity_pipeline_summary()` - Stage totals and weighted values

**Activities**
- `get_crm_activities()` - Activity list with filters
- `create_crm_activity()` - Log new activity

**Complaints**
- `get_complaints()` - Complaint list with filters
- `get_complaint_by_id()` - Complaint with timeline
- `create_complaint()` - Create with auto-numbering
- `update_complaint_status()` - Status update with timeline log

**Forecasting**
- `get_crm_forecasts()` - Pipeline forecast by month
- `get_salesperson_forecast()` - Individual rep forecast vs target

**Reports**
- `get_lead_conversion_report()` - Conversion analysis
- `get_sales_pipeline_report()` - Pipeline analysis
- `get_customer_analysis_report()` - Customer metrics

## Integration Points

### With Sales Module
- Leads can convert to Sales Customers
- Leads can convert to Sales Opportunities
- CRM uses shared `sales_activities` table
- CRM customer 360 shows Sales quotations, orders, deliveries

### With Flow Module
- Future: CRM alerts surface in Flow channels
- Future: Lead notifications via Flow messages
- Architecture ready for Flow webhook integration

### With Workflow Module
- Future: Approval workflows for lead scoring
- Future: Complaint escalation workflows
- Architecture ready for workflow triggers

## Lead Scoring Algorithm

The lead score (0-100) is calculated based on:

| Factor | Points |
|--------|--------|
| Priority (Low/Medium/High/Urgent) | 0/10/20/30 |
| Source (Referral/Partner/Trade Show/Web/Social/Other) | 25/20/15/10/5/0 |
| Estimated Value (>100K/>50K/>10K/>0) | 30/20/10/5 |
| Status adjustment | -50 to +30 |
| Hot lead bonus | +20 |
| Industry presence | +5 |

## Engagement Score Calculation

Customer engagement (0-100) based on last 90 days:

| Activity | Weight |
|----------|--------|
| Order placed | +10 per order |
| Quotation received | +5 per quote |
| Activity logged | +2 per activity |

## Churn Risk Factors

Risk assessment considers:
- Days since last purchase (>180 days: +40, >90 days: +25, >60 days: +10)
- Credit utilization (>90%: +30, >70%: +15)
- Low engagement score (+20)
- Open complaints (>2: +25, >0: +10)

## Future Enhancements

1. **AI Lead Scoring** - Replace rule-based scoring with ML model
2. **Journey Prediction** - Predict next best action
3. **Sentiment Analysis** - Analyze complaint/activity text
4. **Forecast ML** - Pipeline prediction with historical data
5. **Email Integration** - Direct email from CRM
6. **Document Generation** - PDF proposals from templates
