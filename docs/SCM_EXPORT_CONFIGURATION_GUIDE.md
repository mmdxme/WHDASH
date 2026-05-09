# SCM Export Configuration Guide

## Overview

The SCM Export Center provides comprehensive data export capabilities across all supply chain planning modules. This guide explains how to configure and use export functionality.

## Export Categories

### 1. Demand Export
- **Data**: Demand history, forecasts, overrides
- **Formats**: CSV, Excel, PDF
- **Filters**: Date range, item, warehouse, branch

### 2. Supply Export
- **Data**: Inventory levels, in-transit, open POs
- **Formats**: CSV, Excel, PDF
- **Filters**: Date range, supplier, warehouse

### 3. Replenishment Export
- **Data**: Recommendations, approvals, history
- **Formats**: CSV, Excel, PDF
- **Filters**: Status, priority, date range

### 4. Inventory Export
- **Data**: Stock balances, ABC/XYZ classification
- **Formats**: CSV, Excel, PDF
- **Filters**: Branch, warehouse, category

## Column Configuration

### Available Columns for Demand Export

| Column | Description | Default |
|--------|-------------|---------|
| item_code | Item identifier | ✓ |
| item_name | Item description | ✓ |
| warehouse | Warehouse name | ✓ |
| period_start | Period start date | ✓ |
| sales_quantity | Sales quantity | ✓ |
| consumption_quantity | Consumption quantity | ✓ |
| total_demand | Total demand | ✓ |
| forecast_quantity | Forecast value | ✓ |
| variance | Forecast variance | ✓ |
| variance_percent | Variance percentage | - |

### Available Columns for Supply Export

| Column | Description | Default |
|--------|-------------|---------|
| item_code | Item identifier | ✓ |
| item_name | Item description | ✓ |
| warehouse | Warehouse name | ✓ |
| current_stock | Current inventory | ✓ |
| in_transit | In-transit quantity | ✓ |
| open_po | Open purchase orders | ✓ |
| days_of_supply | Calculated days | ✓ |
| reorder_point | Reorder point | - |

## Export Formats

### CSV Export
- UTF-8 encoding
- Comma delimiter
- Quote character: "
- Date format: YYYY-MM-DD
- Number format: 1000.00

### Excel Export
- .xlsx format
- Header row formatting
- Auto column width
- Date formatting
- Number formatting
- Multiple sheets supported

### PDF Export
- A4 page size
- Portrait orientation
- Header with date/logo
- Page numbers
- Grouped data support

## Filter Configuration

### Date Range Filters
- Predefined ranges: Today, This Week, This Month, This Quarter, This Year
- Custom range selection
- Relative date support (e.g., Last 30 Days)

### Multi-Select Filters
- Items (with search)
- Warehouses
- Branches/Entities
- Suppliers
- Categories

### Quick Filters
- Active items only
- Items with exceptions
- High priority items
- Recently modified

## Scheduled Exports

### Configuration Options
- **Frequency**: Daily, Weekly, Monthly
- **Time**: Specific hour/minute
- **Recipients**: Email distribution list
- **Format**: Preferred export format
- **Filters**: Saved filter configurations

### Example Schedule
```yaml
scheduled_exports:
  daily_demand:
    enabled: true
    frequency: daily
    time: "06:00"
    format: csv
    recipients:
      - demand_planner@company.com
    filters:
      date_range: previous_day
      branches: all
      
  weekly_inventory:
    enabled: true
    frequency: weekly
    day: monday
    time: "07:00"
    format: excel
    recipients:
      - inventory_manager@company.com
    filters:
      date_range: previous_week
```

## Export Templates

### Template Types
1. **Standard**: All default columns
2. **Summary**: Aggregated data only
3. **Detailed**: All available columns
4. **Custom**: User-defined columns

### Creating Custom Templates
1. Navigate to Export Center
2. Select report type
3. Click "Create Template"
4. Choose columns
5. Set default filters
6. Name and save template

## API Export

### REST Endpoints
```
GET /scm/export/demand?format=csv&date_from=2026-01-01
GET /scm/export/supply?format=excel&warehouse_id=1
POST /scm/export/configure
```

### Response Formats
- **JSON**: Structured data response
- **File Download**: Direct file download
- **Email**: Sent as attachment

## Best Practices

1. **Use appropriate date ranges** - Avoid exporting entire history at once
2. **Apply filters** - Reduce data volume for faster exports
3. **Save templates** - Reuse configurations for recurring reports
4. **Schedule off-peak** - Schedule heavy exports for off-hours
5. **Compress large files** - Use ZIP for multiple file exports

## Troubleshooting

### Common Issues

#### Slow Export
- **Cause**: Large dataset
- **Solution**: Apply date filter or reduce columns

#### Missing Data
- **Cause**: Filter excludes data
- **Solution**: Review filter settings

#### Wrong Format
- **Cause**: Incorrect template selection
- **Solution**: Verify template configuration

## Security

### Access Control
- Export permissions required
- Audit trail for all exports
- Sensitive data masking option

### Data Protection
- Encrypted file transfer
- Temporary storage cleanup
- Access logging
