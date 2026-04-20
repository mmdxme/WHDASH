# CRM Reporting Guide

## Overview

The CRM module provides comprehensive reporting and analytics capabilities for sales and customer relationship management.

## Available Reports

### 1. CRM Dashboard
**Route:** `/crm/dashboard/`

Real-time KPIs including:
- Total Leads (New, Qualified, Hot)
- Open Opportunities by stage
- Pipeline Value
- Won/Lost Opportunities
- Activities (Calls, Meetings, Visits)
- Open Complaints
- Critical Complaints

**Filters:** Date range, Salesperson

---

### 2. Lead Conversion Report
**Route:** `/crm/reports/lead-conversion/`

Analyzes lead-to-customer conversion effectiveness.

**Metrics:**
- Total Leads
- Converted Leads
- Conversion Rate (%)
- Average Days to Conversion

**Breakdowns:**
- By Source (Website, Phone, Referral, etc.)
- By Month (trend analysis)

**Filters:** Date range

---

### 3. Pipeline Report
**Route:** `/crm/reports/pipeline/`

Detailed pipeline analysis by stage.

**Metrics per Stage:**
- Opportunity Count
- Total Value (sum of estimated_value)
- Average Probability (%)
- Weighted Value (value × probability)
- Min/Max/Avg Deal Size

**Won/Lost Analysis:**
- Won Value
- Lost Value
- Win Rate (%)
- Average Deal Size (Won)

**Pipeline Velocity:**
- Average days in each stage

**Filters:** Date range, Salesperson

---

### 4. Customer Analysis Report
**Route:** `/crm/reports/customer-analysis/`

Customer base analysis and segmentation.

**Metrics:**
- Customer count by tier
- Total/average revenue by tier
- Top 50 customers by revenue
- Churn risk distribution
- Engagement level distribution

---

### 5. Activity Report
**Route:** `/crm/activities/`

Complete activity log with filtering.

**Columns:**
- Date
- Type (Call, Meeting, Visit, Email)
- Subject
- Customer
- Owner
- Duration
- Outcome

**Filters:**
- Type
- Owner
- Customer
- Date range

---

## Export Capabilities

All CRM lists and reports support export functionality:

### Lead Export
**Route:** `/crm/export/leads/`

**Columns:**
- Lead Number
- Company Name
- Contact Name
- Phone
- Email
- Source
- Status
- Priority
- Score
- Estimated Value
- Assigned To
- Created Date

**Filters:** Status, Source, Priority, Assigned To

**Format:** Excel (.xlsx)

---

### Opportunity Export
**Route:** `/crm/export/opportunities/`

**Columns:**
- Opportunity Number
- Customer
- Stage
- Value
- Probability
- Weighted Value
- Expected Close
- Salesperson
- Created Date

**Filters:** Stage, Salesperson

**Format:** Excel (.xlsx)

---

### Activity Export
**Route:** `/crm/export/activities/`

**Columns:**
- Date
- Type
- Subject
- Customer
- Owner
- Duration
- Outcome
- Notes

**Filters:** Type, Owner, Date range

**Format:** CSV

---

## Using Filters Effectively

### Date Range Filters
Most reports support date filtering:
- **Specific dates:** Select exact From/To dates
- **Relative:** Use date pickers or presets (This Month, Last Quarter, etc.)
- **Default:** Most reports show last 30-90 days by default

### Multi-Select Filters
- Use Ctrl/Cmd+Click to select multiple values
- Empty selection means "All"

### Best Practices
1. Always set a date range for large datasets
2. Filter by Salesperson when analyzing individual performance
3. Export filtered data for offline analysis in Excel
4. Use Customer filter when investigating specific issues

---

## Dashboard Widgets

### KPI Cards
Quick-glance metrics at the top of pages:
- Color-coded by performance (green/yellow/red)
- Click to drill down to related list/report

### Pipeline Funnel
Visual funnel showing:
- Leads → Qualified → Proposal → Negotiation → Won
- Drop-off rates between stages

### Conversion Charts
Trend lines showing:
- Lead conversion over time
- Win rate trends
- Average deal size trends

---

## Custom Report Building (Future)

Planned enhancements:
- Drag-and-drop report builder
- Saved report configurations
- Scheduled report delivery via email
- White-label report templates
