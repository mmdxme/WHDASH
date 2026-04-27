# Marketing Automation Export Configuration Guide

## Overview

The Marketing Automation Export Center provides flexible data export capabilities with user-configurable columns, formats, and filtering options. All exports maintain multilingual support and RTL compatibility.

## Export Configuration Structure

### Configuration Fields

| Field | Type | Description |
|-------|------|-------------|
| config_name | string | Human-readable export name |
| config_code | string | Unique identifier |
| export_type | enum | Type: campaign, lead, segment, channel, journey, roi, attribution |
| entity_type | string | Primary entity being exported |
| report_type | string | Specific report variant |
| columns_config | JSON | Column definitions and order |
| output_format | enum | csv, excel, pdf |
| include_headers | boolean | Include column headers |
| include_totals | boolean | Include summary totals |
| filter_config | JSON | Predefined filters |
| is_system_config | boolean | System vs user-created |
| is_active | boolean | Configuration availability |

## Export Types

### Campaign Export
**Code**: `EXP-CAMP-STANDARD`
**Entity**: marketing_campaigns

#### Available Columns
- Campaign Name
- Campaign Code
- Campaign Type
- Status
- Start Date
- End Date
- Budget
- Actual Cost
- Leads Generated
- Sales Generated
- Profit Generated
- ROI %
- Cost per Lead
- Cost per Acquisition
- Owner
- Created Date

#### Filter Options
- Status (Draft, Active, Paused, Completed)
- Campaign Type
- Date Range
- Branch/Entity
- Budget Range

### Lead Export
**Code**: `EXP-LEAD-STANDARD`
**Entity**: marketing_leads

#### Available Columns
- Lead Name
- Email
- Phone
- Company
- Industry
- Source
- Status
- Importance Level
- Estimated Value
- Conversion Probability
- Assigned To
- Score Grade
- MQL Flag
- SQL Flag
- Created Date
- Last Activity

#### Filter Options
- Status
- Lead Source
- Score Grade
- Date Range
- Assigned User
- Segment
- Importance

### Segment Export
**Code**: `EXP-SEG-EXPORT`
**Entity**: marketing_customer_segments

#### Available Columns
- Segment Name
- Segment Code
- Segment Type
- Customer Type
- Status
- Member Count
- Created Date
- Last Updated

#### Filter Options
- Segment Type
- Status
- Customer Type

### Channel Performance Export
**Code**: `EXP-CHAN-PERF`
**Entity**: marketing_channels + performance

#### Available Columns
- Channel Name
- Channel Type
- Status
- Budget
- Actual Spend
- Leads Generated
- Inquiries Generated
- Sales Generated
- Cost per Lead
- ROI %

#### Filter Options
- Channel Type
- Date Range
- Status

### Journey Performance Export
**Code**: `EXP-JOURNEY-PERF`
**Entity**: marketing_nurture_journeys

#### Available Columns
- Journey Name
- Journey Code
- Journey Type
- Status
- Participant Count
- Completed Count
- Active Count
- Dropped Count
- Completion Rate
- Avg Engagement
- Total Revenue

#### Filter Options
- Status
- Journey Type
- Date Range

### ROI Summary Export
**Code**: `EXP-ROI-SUMMARY`
**Entity**: Calculated metrics

#### Available Columns
- Campaign/Channel Name
- Spend
- Revenue
- Profit
- ROI %
- Cost per Lead
- Cost per Acquisition
- Period

### Attribution Export
**Code**: `EXP-ATTR-EXPORT`
**Entity**: marketing_attribution

#### Available Columns
- Campaign Name
- Channel Name
- Attribution Model
- Attributed Customers
- Attributed Revenue
- Attributed Profit
- Conversion Count

## Output Formats

### CSV (Comma-Separated Values)
- UTF-8 encoding with BOM for Excel compatibility
- Configurable delimiter
- Quote handling for special characters
- Header row option

### Excel (XLSX)
- Multiple sheets supported
- Column formatting preserved
- Auto-filter enabled
- Summary totals row

### PDF (Future)
- Formatted report layout
- Charts and graphs
- Header/footer with branding

## Column Configuration

### User Column Selection
Users can select which columns to include:
```json
{
  "columns": [
    {"field": "name", "label": "Campaign Name", "selected": true},
    {"field": "status", "label": "Status", "selected": true},
    {"field": "budget", "label": "Budget", "selected": true}
  ]
}
```

### Column Order
Drag-and-drop column reordering:
```json
{
  "column_order": ["name", "status", "start_date", "budget", "actual_cost", "roi"]
}
```

### Column Settings
- Width (for Excel)
- Format (currency, date, percentage)
- Aggregate function (sum, avg, count)

## Filter Configuration

### Predefined Filters
```json
{
  "filters": {
    "date_range": {"type": "date_range", "default": "last_30_days"},
    "status": {"type": "multi_select", "options": ["Active", "Paused"]},
    "campaign_type": {"type": "single_select"}
  }
}
```

### Dynamic Filters
- Date range picker
- Multi-select dropdowns
- Search text fields
- Numeric ranges

## Export Execution

### API Endpoint
```
POST /marketing/export/run/<config_id>
```

### Request Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| columns | array | Selected column field names |
| filters | object | Applied filter values |
| format | string | csv, excel, pdf |
| sort_by | string | Primary sort field |
| sort_order | string | asc, desc |

### Response
- Content-Type based on format
- Content-Disposition for file download
- Filename: `{entity}_{timestamp}.{format}`

## Audit Logging

All exports are logged:
```python
log_marketing_audit(db, 'export', config_id, 'EXPORT',
                   new_value=json.dumps({'config_name': config_name,
                                        'columns': columns,
                                        'row_count': row_count}),
                   actor_user_id=user_id)
```

## Scheduled Exports (Future)

### Configuration
- Frequency: Daily, Weekly, Monthly
- Recipients: Email list
- Time: Hour selection
- Filters: Preserved from configuration

### Delivery
- Email with attachment
- In-app notification
- Flow integration

## Best Practices

### Data Selection
1. Select only needed columns
2. Apply appropriate filters
3. Use date ranges to limit data
4. Sort by most important field

### Performance
1. Export during off-peak hours for large datasets
2. Use Excel for datasets > 10,000 rows
3. Schedule recurring exports

### Security
1. Verify export permissions before running
2. Review exported data sensitivity
3. Follow data retention policies

## Troubleshooting

### Empty Exports
- Check filter criteria
- Verify data exists in selected date range
- Confirm user has access to data scope

### Large File Size
- Reduce column selection
- Apply date range filters
- Split into multiple exports

### Encoding Issues
- Ensure UTF-8 encoding selected
- Verify Excel version compatibility
- Check for special characters
