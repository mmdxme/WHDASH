# Demand Planning Export Configuration Guide

## Overview

The WHDASH Demand Planning module provides comprehensive export capabilities supporting multiple formats with user-configurable column selection, filtering, and formatting options. This guide details all export functionality and configuration options.

## Export Routes

| Route | Description |
|-------|-------------|
| `/scm/demand/export/demand` | Export demand data |
| `/scm/demand/export/forecast` | Export forecast data |
| `/scm/demand/export/accuracy` | Export accuracy metrics |
| `/scm/demand/export/overrides` | Export override history |
| `/scm/demand/export/scenarios` | Export scenario data |

## Supported Formats

### 1. CSV (Comma-Separated Values)
- Default format for data analysis
- UTF-8 encoding
- Configurable delimiter
- Quote character options

### 2. Excel (XLSX)
- Full formatting preserved
- Multiple sheets supported
- Auto-filter enabled
- Column width auto-fit

### 3. PDF
- Formatted report layout
- Charts included
- Headers and footers
- Page numbers

### 4. Print View
- Browser print optimization
- CSS print styles
- Automatic page breaks

## Export Configuration Options

### Common Configuration

```python
{
    'format': 'excel',  # csv, excel, pdf, print
    'filename': 'forecast_export_2026-01-15',
    'encoding': 'utf-8',
    'date_format': '%Y-%m-%d',
    'datetime_format': '%Y-%m-%d %H:%M:%S',
    'number_format': '#,##0.00',
    'include_header': True,
    'include_totals': True,
    'compress': False
}
```

### Column Selection

```python
{
    'columns': [
        {
            'field': 'item_code',
            'header': 'Item Code',
            'width': 15,
            'visible': True,
            'order': 1,
            'format': 'text'
        },
        {
            'field': 'forecast_qty',
            'header': 'Forecast Qty',
            'width': 12,
            'visible': True,
            'order': 2,
            'format': 'number',
            'decimals': 2,
            'totals': 'sum'
        }
    ],
    'show_columns': ['item_code', 'item_name', 'forecast_qty', 'actual_qty', 'variance']
}
```

### Filtering Options

```python
{
    'filters': {
        'date_range': {
            'field': 'period_start',
            'start': '2026-01-01',
            'end': '2026-03-31'
        },
        'warehouse': {
            'field': 'warehouse_id',
            'operator': 'in',
            'values': [1, 2, 3]
        },
        'category': {
            'field': 'category',
            'operator': '=',
            'value': 'Electronics'
        },
        'status': {
            'field': 'status',
            'operator': 'in',
            'values': ['APPROVED', 'PUBLISHED']
        }
    }
}
```

### Sorting Options

```python
{
    'sort': [
        {'field': 'item_code', 'direction': 'asc'},
        {'field': 'period_start', 'direction': 'desc'}
    ],
    'sort_by': 'item_code',
    'sort_order': 'asc'
}
```

### Grouping Options

```python
{
    'group_by': [
        {'field': 'category', 'label': 'Category'},
        {'field': 'warehouse_id', 'label': 'Warehouse'}
    ],
    'include_subtotals': True,
    'include_grand_total': True
}
```

## Export Templates

Users can save and reuse export configurations:

### Template Structure

```python
{
    'name': 'Monthly Forecast Summary',
    'description': 'Standard monthly forecast export for management',
    'report_type': 'forecast_summary',
    'format': 'excel',
    'columns': [...],
    'filters': {...},
    'sort': [...],
    'group_by': [...],
    'created_by': 1,
    'created_at': '2026-01-15 10:30:00'
}
```

### Built-in Templates

| Template Name | Report Type | Description |
|--------------|-------------|-------------|
| Standard Forecast | forecast_summary | Basic forecast export |
| Accuracy Report | accuracy | MAPE and bias metrics |
| Override Log | overrides | Complete override history |
| Version Comparison | version_diff | Two-version comparison |
| Exception Summary | exceptions | Active exceptions |
| Demand Sensing | signals | Demand signals and alerts |

## Demand Data Export

### Export Demand History

**Route:** `GET /scm/demand/export/demand`

**Available Columns:**
- item_code
- item_name
- category
- brand
- warehouse_code
- warehouse_name
- period_start
- period_type
- sales_quantity
- consumption_quantity
- total_demand
- customer_count
- order_count
- returned_quantity
- lost_sales_estimate

**Default Columns:** item_code, item_name, period_start, sales_quantity, consumption_quantity, total_demand

**Example Request:**
```
GET /scm/demand/export/demand?format=excel&date_range=2026-01-01,2026-03-31&columns=item_code,item_name,total_demand
```

## Forecast Data Export

### Export Forecast Lines

**Route:** `GET /scm/demand/export/forecast`

**Available Columns:**
- item_code
- item_name
- warehouse_name
- period_start
- period_type
- base_quantity
- trend_factor
- seasonal_factor
- override_quantity
- final_quantity
- confidence
- is_frozen
- run_name
- method
- version_name
- version_status

**Default Columns:** item_code, item_name, period_start, final_quantity, confidence, run_name

### Export Forecast Runs

**Route:** `GET /scm/demand/export/forecast/runs`

**Available Columns:**
- run_name
- method
- horizon_days
- period_type
- status
- total_items
- total_demand
- created_by
- created_at
- approved_by
- approved_at

## Accuracy Data Export

### Export Accuracy Metrics

**Route:** `GET /scm/demand/export/accuracy`

**Available Columns:**
- item_code
- item_name
- warehouse_name
- period_start
- forecast_quantity
- actual_quantity
- error_quantity
- mape
- wape
- mae
- bias
- tracking_signal
- theil_u

**Default Columns:** item_code, item_name, period_start, forecast_quantity, actual_quantity, mape, bias

### Export Bias Analysis

**Route:** `GET /scm/demand/export/accuracy/bias`

**Available Columns:**
- item_code
- planner_name
- period_start
- total_forecast
- total_actual
- bias_amount
- bias_percent
- over_forecast_count
- under_forecast_count

## Override Data Export

### Export Override History

**Route:** `GET /scm/demand/export/overrides`

**Available Columns:**
- item_code
- item_name
- period_start
- original_quantity
- override_quantity
- change_percent
- override_reason
- override_type
- status
- requested_by
- requested_at
- reviewed_by
- reviewed_at
- review_notes

**Default Columns:** item_code, period_start, original_quantity, override_quantity, change_percent, override_reason, status

### Export Bulk Override Summary

**Route:** `GET /scm/demand/export/overrides/bulk`

## Version Data Export

### Export Version Comparison

**Route:** `GET /scm/demand/export/versions/compare`

**Available Columns:**
- item_code
- item_name
- version_1_name
- version_1_quantity
- version_2_name
- version_2_quantity
- difference
- percent_difference

## Scenario Data Export

### Export Scenarios

**Route:** `GET /scm/demand/export/scenarios`

**Available Columns:**
- scenario_name
- scenario_type
- item_code
- item_name
- base_value
- scenario_value
- impact_value
- impact_percent
- created_by
- created_at

## Flow Integration

Exports can trigger Flow notifications:

```python
{
    'notify_on_export': True,
    'notify_users': [1, 2, 3],
    'flow_template': 'export_completed',
    'include_summary': True
}
```

## Scheduled Exports

Users can configure scheduled exports:

```python
{
    'schedule': {
        'frequency': 'daily',  # daily, weekly, monthly
        'day_of_week': 1,  # 0-6 for weekly
        'day_of_month': 1,  # 1-28 for monthly
        'time': '08:00',
        'timezone': 'UTC'
    },
    'delivery': {
        'method': 'email',  # email, ftp, s3, internal
        'recipients': ['manager@company.com'],
        'ftp_config': {...}
    }
}
```

## API Export Endpoint

### POST /api/demand/export

**Request Body:**
```json
{
    "report_type": "forecast_summary",
    "format": "excel",
    "columns": ["item_code", "item_name", "forecast_qty"],
    "filters": {
        "date_range": {"start": "2026-01-01", "end": "2026-03-31"},
        "warehouse_id": [1, 2]
    },
    "sort": {"field": "item_code", "direction": "asc"},
    "options": {
        "include_totals": true,
        "compress": true
    }
}
```

**Response:**
```json
{
    "success": true,
    "download_url": "/exports/demand_forecast_2026-01-15.xlsx",
    "expires_at": "2026-01-16T08:00:00Z",
    "file_size": 1024000,
    "record_count": 15000
}
```

## Performance Guidelines

### Large Export Handling
- Exports > 100,000 rows: Automatic chunking
- Maximum export size: 500,000 rows
- Timeout limit: 5 minutes
- Background processing for large exports

### Optimization Tips
1. Use specific date ranges instead of full history
2. Filter by warehouse/category to reduce size
3. Export only needed columns
4. Use CSV for large datasets
5. Schedule off-peak for very large exports

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Empty export | Wrong filters | Check filter criteria |
| Missing columns | Column not in data | Verify column selection |
| File too large | Too much data | Reduce date range/columns |
| Encoding issues | Non-UTF8 characters | Use UTF-8 encoding option |
| Timeout | Very large export | Use background export |
