# Demand Planning Reporting Guide

## Overview

The WHDASH Demand Planning module provides comprehensive reporting and analytics capabilities across all aspects of the forecasting and planning process. This guide details all available reports, their parameters, and usage.

## Report Categories

### 1. Forecast Reports

#### Forecast Summary Report
**Route:** `/scm/demand/reports` (forecast_dashboard)
**Description:** Executive summary of forecast status across all items
**Parameters:**
- Date range: 30/60/90/180/365 days
- Warehouse filter
- Category filter
- Brand filter
- Status filter

**Metrics:**
- Total forecasted quantity
- Items with forecast
- Forecast coverage
- Frozen vs draft breakdown

#### Forecast by Item Report
**Route:** `/scm/demand/by-item/<item_id>`
**Description:** Detailed forecast for a specific item
**Parameters:**
- Item selection (required)
- Period range
- Include actuals toggle
- Include overrides toggle

**Metrics:**
- Historical demand
- Forecast quantity
- Override quantity
- Variance
- Accuracy metrics

#### Forecast by Warehouse Report
**Route:** `/scm/demand/by-warehouse`
**Description:** Forecast aggregation by warehouse
**Parameters:**
- Warehouse filter (multi-select)
- Date range
- Include subcategories toggle

#### Forecast by Brand Report
**Route:** `/scm/demand/by-brand`
**Description:** Brand-level forecast aggregation
**Parameters:**
- Brand filter
- Date range
- Top N brands

#### Forecast by Customer Segment Report
**Route:** `/scm/demand/by-customer-segment`
**Description:** Demand segmentation analysis
**Parameters:**
- Segment filter
- Date range
- Include trends toggle

---

### 2. Forecast Version Reports

#### Version Comparison Report
**Route:** `/scm/demand/versions/compare`
**Description:** Side-by-side comparison of two forecast versions
**Parameters:**
- Version 1 selection (required)
- Version 2 selection (required)
- Include all items toggle
- Difference threshold filter

**Output:**
| Item | Version 1 Qty | Version 2 Qty | Difference | % Change |
|------|---------------|---------------|------------|----------|
| SKU001 | 1,000 | 1,200 | +200 | +20% |

#### Version Audit Report
**Route:** `/scm/demand/versions/<id>/audit`
**Description:** Complete audit trail of version changes
**Parameters:**
- Version selection (required)

**Output:**
- Version metadata
- Creation timestamp
- Approval history
- Change log

---

### 3. Forecast Accuracy Reports

#### Accuracy Dashboard
**Route:** `/scm/demand/accuracy/dashboard`
**Description:** Portfolio-level accuracy metrics
**Parameters:**
- Date range (rolling 30/60/90 days)
- Planner filter
- Item category filter

**Metrics Displayed:**
- Average MAPE
- Items measured count
- Over-forecast count
- Under-forecast count
- Accuracy trend chart

#### Accuracy by Item Report
**Route:** `/scm/demand/accuracy/by-item/<item_id>`
**Description:** Detailed accuracy for specific item
**Parameters:**
- Item selection
- Period range

**Metrics:**
- Per-period MAPE
- Cumulative bias
- Tracking signal
- Forecast vs actual table

#### Bias Analysis Report
**Route:** `/scm/demand/accuracy/bias`
**Description:** Planner and item bias analysis
**Parameters:**
- Planner filter
- Branch filter
- Bias threshold

**Metrics:**
- Average bias by planner
- Bias trend over time
- High-bias items list
- Over/under forecast ratio

#### High Error Items Report
**Route:** `/scm/demand/accuracy/high-error`
**Description:** Items with MAPE > threshold
**Parameters:**
- MAPE threshold (default: 20%)
- Category filter
- Sort by: MAPE/Value/Item

---

### 4. Override Reports

#### Override History Report
**Route:** `/scm/demand/overrides/list`
**Description:** Complete override audit trail
**Parameters:**
- Date range
- Status filter (Pending/Approved/Rejected)
- Override type filter
- Item filter
- Requester filter

**Output Columns:**
- Date
- Item
- Period
- Original Qty
- Override Qty
- Change %
- Reason
- Status
- Requester
- Reviewer

#### Override Summary Report
**Route:** `/scm/demand/overrides/summary`
**Description:** Override statistics and trends
**Parameters:**
- Period (daily/weekly/monthly)
- Date range
- Group by: Item/Reason/Requester

**Metrics:**
- Total overrides
- Override frequency
- Average change magnitude
- Most common reasons
- Approval rate

---

### 5. Demand Sensing Reports

#### Volatility Alert Report
**Route:** `/scm/demand/sensing`
**Description:** High-volatility items requiring attention
**Parameters:**
- Severity filter
- Alert type (Spike/Drop/Volatility)
- Item filter
- Date range

**Output:**
| Item | Alert Type | Severity | Z-Score | CV | Date |
|------|------------|----------|---------|-----|------|
| SKU001 | DEMAND_SPIKE | HIGH | 3.2 | 0.8 | 2026-01-15 |

#### Demand Signal Summary
**Route:** `/scm/demand/sensing/signals`
**Description:** Recent demand signals and anomalies
**Parameters:**
- Signal direction (Up/Down/Stable)
- Confidence threshold
- Item filter

---

### 6. Scenario Planning Reports

#### Scenario Comparison Report
**Route:** `/scm/demand/scenarios/compare`
**Description:** Compare multiple what-if scenarios
**Parameters:**
- Scenario selection (2-5)
- Metrics to compare

**Output:**
| Scenario | Items | Total Base | Total Impact | Avg Impact % |
|----------|-------|------------|--------------|--------------|
| Promotion Uplift | 50 | 100,000 | +15,000 | +15% |
| Demand Drop | 50 | 100,000 | -10,000 | -10% |

#### Scenario Impact Detail
**Route:** `/scm/demand/scenarios/<id>/impact`
**Description:** Item-level scenario impact
**Parameters:**
- Scenario selection
- Sort by: Impact/Item/Category
- Filter by category

---

### 7. Consensus Planning Reports

#### Consensus Status Report
**Route:** `/scm/demand/consensus`
**Description:** Collaborative forecast status
**Parameters:**
- Version filter
- Disagreement level filter
- Item filter

**Output:**
| Item | Sales Input | Planner Input | Marketing Input | Consensus | Disagreement |
|------|-------------|---------------|-----------------|-----------|--------------|
| SKU001 | 1,000 | 1,200 | 1,100 | 1,100 | LOW |

#### Disagreement Report
**Route:** `/scm/demand/consensus/disagreements`
**Description:** Items with high forecast disagreement
**Parameters:**
- Disagreement threshold
- Date range

---

### 8. Exception Reports

#### Exception Queue Report
**Route:** `/scm/demand/exceptions`
**Description:** Active planning exceptions
**Parameters:**
- Exception type
- Severity filter
- Date range
- Item filter

**Output:**
| Type | Item | Severity | Title | Date | Age |
|------|------|----------|-------|------|-----|
| FORECAST_DEVIATION | SKU001 | HIGH | >20% variance | 2026-01-15 | 3 days |

#### Escalation Report
**Route:** `/scm/demand/exceptions/escalations`
**Description:** Escalated issues tracking
**Parameters:**
- Escalation status
- Date range

---

### 9. SCM Linkage Reports

#### Forecast-to-Replenishment Impact
**Route:** `/scm/demand/scm-linkage`
**Description:** How forecasts drive replenishment
**Parameters:**
- Date range
- Warehouse filter
- Item category filter

**Metrics:**
- Forecast-driven replenishment quantity
- Items at coverage risk
- Branch refill alerts

#### Supply Risk from Forecast
**Route:** `/scm/demand/scm-linkage/supply-risk`
**Description:** Supplier risks based on forecasts
**Parameters:**
- Lead time threshold
- Supplier filter

---

### 10. Sales/Marketing Linkage Reports

#### Sales Forecast Input Report
**Route:** `/scm/demand/sales-linkage`
**Description:** Sales vs. planning forecast alignment
**Parameters:**
- Date range
- Salesperson filter
- Item filter

#### Promotion Impact Report
**Route:** `/scm/demand/sales-linkage/promotion-impact`
**Description:** Promotion effectiveness analysis
**Parameters:**
- Promotion filter
- Date range
- Comparison period

---

## Export Capabilities

### Export Formats
- **PDF:** Formatted report with charts
- **Excel:** Full data with formatting
- **CSV:** Raw data for analysis
- **Print:** Optimized for printing

### Export Configuration Options

For each report, users can configure:

```python
export_options = {
    'columns': [
        'item_code',
        'item_name',
        'forecast_qty',
        'actual_qty',
        'variance',
        'mape'
    ],
    'column_order': ['item_code', 'item_name', 'forecast_qty', 'actual_qty', 'variance', 'mape'],
    'sort_by': 'item_code',
    'sort_order': 'asc',
    'group_by': None,
    'filters': {
        'category': 'Electronics',
        'date_range': ['2026-01-01', '2026-03-31']
    },
    'format': 'excel',
    'include_totals': True,
    'include_charts': True,
    'page_size': 'A4',
    'orientation': 'landscape'
}
```

### Column Selection UI

Each report page includes a column selection panel:
- Checkbox for each available column
- Drag-and-drop reordering
- Save as template option
- Reset to default option

### Scheduled Exports

Users can schedule reports to run automatically:
- Daily/Weekly/Monthly
- Email delivery
- FTP upload
- Internal notification

---

## Report Access by Role

| Report | DEMAND_PLANNER | DEMAND_MANAGER | EXECUTIVE_VIEWER | AUDITOR |
|--------|----------------|-----------------|------------------|---------|
| Forecast Summary | ✓ | ✓ | ✓ | ✓ |
| Forecast by Item | ✓ | ✓ | ✓ | ✓ |
| Forecast by Warehouse | ✓ | ✓ | ✓ | ✓ |
| Forecast by Brand | ✓ | ✓ | ✓ | ✓ |
| Version Comparison | ✓ | ✓ | ✓ | ✓ |
| Accuracy Dashboard | ✓ | ✓ | ✓ | ✓ |
| Accuracy by Item | ✓ | ✓ | ✓ | ✓ |
| Bias Analysis | ✓ | ✓ | ✓ | ✓ |
| High Error Items | ✓ | ✓ | ✓ | ✓ |
| Override History | Own only | ✓ All | ✓ | ✓ |
| Override Summary | ✓ | ✓ | ✓ | ✓ |
| Volatility Alerts | ✓ | ✓ | ✓ | ✓ |
| Scenario Comparison | ✓ | ✓ | ✓ | - |
| Scenario Impact | ✓ | ✓ | ✓ | - |
| Consensus Status | ✓ | ✓ | ✓ | ✓ |
| Exception Queue | ✓ | ✓ | ✓ | ✓ |
| SCM Linkage | ✓ | ✓ | ✓ | - |
| Sales Linkage | ✓ | ✓ | ✓ | - |

---

## Custom Report Builder

**Route:** `/scm/reports/custom`

The custom report builder allows users to:
1. Select data source (demand_history, forecast_lines, overrides, etc.)
2. Choose columns to display
3. Apply filters
4. Set grouping and aggregation
5. Add calculated fields
6. Save as custom report
7. Schedule custom reports

### Available Data Sources

```
demand_history
forecast_runs
forecast_lines
forecast_versions
forecast_overrides
consensus_forecasts
demand_drivers
promotion_impact
demand_signals
volatility_alerts
scenario_lines
alerts
kpi_records
```

### Supported Aggregations

- SUM
- AVG
- COUNT
- MIN
- MAX
- STDDEV
- VARIANCE

---

## Report Rendering

### Charts

All reports support optional charts:
- Line charts for trends
- Bar charts for comparisons
- Pie charts for distributions
- Heatmaps for exception views

### Tables

- Sortable columns
- Filterable
- Pivoting capability
- Row expansion for details
- Export selection

### Dashboards

Pre-built dashboard configurations:
- Executive Summary Dashboard
- Forecast Control Tower
- Accuracy Dashboard
- Exception Dashboard
- Scenario Comparison Dashboard
