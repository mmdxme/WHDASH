# Talent Management Export Configuration Guide

## Overview

The Talent Management Export Center provides flexible data export capabilities with configurable columns, formats, and filtering options.

---

## Export Center Location

**Route**: `/hr/talent/export`

Access the Export Center from the Talent Management menu under "Export Center".

---

## Supported Export Formats

### 1. CSV (Comma-Separated Values)
- **Best for**: Data analysis, database imports
- **File extension**: `.csv`
- **Encoding**: UTF-8 with BOM for Excel compatibility
- **Delimiter**: Comma
- **Character limit**: No limit

### 2. Excel (XLSX)
- **Best for**: Reporting, pivot tables, charts
- **File extension**: `.xlsx`
- **Compatibility**: Excel 2007+
- **Max rows**: 1,000,000 per sheet

### 3. PDF (Print-Ready)
- **Best for**: Printing, sharing with stakeholders
- **File extension**: `.pdf`
- **Layout**: Landscape, A4/Letter
- **Includes**: Headers, formatting, pagination

### 4. Print View
- **Best for**: Quick printing from browser
- **Format**: Optimized HTML for print
- **Features**: Print-specific styling

---

## Export Configuration Options

### Column Selection

Users can select which columns to include in exports:

#### Talent Profiles Export
| Column | Description | Default |
|--------|-------------|---------|
| employee_code | Unique employee identifier | ✓ |
| first_name | Employee first name | ✓ |
| last_name | Employee last name | ✓ |
| department | Department name | ✓ |
| position | Job title | ✓ |
| manager | Direct manager name | ✓ |
| potential_rating | Potential assessment | ✓ |
| performance_rating | Performance rating | ✓ |
| readiness_level | Readiness for next role | ✓ |
| hi_po | High Potential flag | ✓ |
| succession_candidate | Succession candidate flag | ✓ |
| flight_risk | Flight risk indicator | ✓ |
| career_interests | Career aspiration notes | - |
| mobility_preference | Mobility preference | - |
| hire_date | Original hire date | - |
| last_reviewed | Last talent review date | - |
| profile_completeness | Profile completion % | - |

#### Succession Coverage Export
| Column | Description | Default |
|--------|-------------|---------|
| position_title | Job title | ✓ |
| department | Department name | ✓ |
| incumbent_name | Current job holder | ✓ |
| incumbent_code | Incumbent employee code | ✓ |
| criticality_level | Role criticality | ✓ |
| successor_name | Primary successor name | ✓ |
| successor_code | Successor employee code | ✓ |
| readiness_level | Successor readiness | ✓ |
| development_needs | Training requirements | - |
| backup_name | Backup successor name | - |
| coverage_status | Covered/At Risk | ✓ |

### Column Ordering
- Drag and drop to reorder columns
- Changes apply to current export only
- Can save column order as default

### Filter Scope

Exports respect the same filters as reports:
- **Department filter**: Export only selected departments
- **Position filter**: Export only selected positions
- **Status filter**: Export only selected statuses
- **Date range**: Export within date range
- **Entity/Branch**: Export for specific entity

---

## Per-Report Export Configuration

### Talent Profile Report
```
URL: POST /hr/talent/export/profiles
Format Options: CSV, Excel
Columns: Selectable (see column list)
Filters: Department, Readiness, Potential, Hi-Po status
```

### Succession Coverage Report
```
URL: POST /hr/talent/export/succession
Format Options: CSV, Excel, PDF
Columns: Position, Department, Incumbent, Successor, Readiness
Filters: Department, Criticality, Coverage Status
```

### Hi-Po Report
```
URL: POST /hr/talent/export/hipo
Format Options: CSV, Excel, PDF
Columns: Employee, Department, Potential, Performance, Readiness
Filters: Department, Readiness, Development Status
```

### Competency Gap Report
```
URL: POST /hr/talent/export/gaps
Format Options: CSV, Excel
Columns: Employee, Competency, Category, Current, Required, Gap
Filters: Department, Category, Gap Direction
```

### Development Plan Report
```
URL: POST /hr/talent/export/development
Format Options: CSV, Excel
Columns: Employee, Year, Manager, Status, Goals, Completion
Filters: Status, Department, Year
```

---

## Export Settings

### System-Level Settings (Admin Only)

| Setting | Default | Description |
|---------|---------|-------------|
| export_max_rows | 10,000 | Maximum rows per export |
| export_timeout | 300 | Timeout in seconds |
| default_format | CSV | Default export format |
| compression_enabled | false | Enable ZIP compression for large exports |
| audit_exports | true | Log all export actions |

### User-Level Settings

| Setting | Default | Description |
|---------|---------|-------------|
| preferred_format | CSV | Preferred export format |
| include_headers | true | Include column headers |
| date_format | YYYY-MM-DD | Date format in exports |
| column_order | System Default | Saved column order |

---

## Scheduled Exports

### Configuration Options

1. **Frequency**
   - Daily (midnight)
   - Weekly (Sunday midnight)
   - Monthly (1st of month)
   - Quarterly

2. **Delivery Method**
   - Email attachment
   - Download link
   - Save to folder (network path)

3. **Recipients**
   - Single user
   - Multiple users
   - User groups

4. **Filters**
   - Use current view filters
   - Custom filter set
   - Include all data

---

## Export Audit

### Logged Events

All exports are logged with:
- User ID
- Export type/report
- Timestamp
- Row count
- Format used
- Columns included
- IP address
- Download completion status

### Audit Query
```
Location: System Audit Logs > Talent Management > Exports
Retention: 7 years (configurable)
```

---

## Bulk Export

### Multi-Report Bundle

Users can create export bundles containing:
- Talent Profile Report
- Succession Coverage Report
- Hi-Po Report
- Development Plan Report
- Competency Gap Report

### Bundle Configuration
1. Select reports to include
2. Apply consistent filters across all
3. Choose single or mixed format output
4. Set compression options
5. Schedule or immediate download

---

## API Export Endpoints

### REST API

```
GET /api/talent/export/profiles
GET /api/talent/export/succession
GET /api/talent/export/hipo
GET /api/talent/export/development
GET /api/talent/export/gaps
```

**Query Parameters**:
- `format`: csv, excel, pdf
- `columns`: comma-separated column list
- `department_id`: filter by department
- `status`: filter by status
- `from_date`: start date
- `to_date`: end date

**Response**:
- Content-Type: application/octet-stream
- Content-Disposition: attachment; filename="export.{format}"

---

## Troubleshooting

### Export Fails
1. Check file size limits
2. Verify database connection
3. Reduce filter scope
4. Try smaller date range

### Large Export Times
1. Increase timeout setting
2. Use background processing
3. Split into smaller exports

### Missing Columns
1. Verify column selection
2. Check permissions for restricted columns
3. Confirm data exists in filtered scope

### Encoding Issues
1. Use Excel format for special characters
2. Enable UTF-8 BOM in CSV
3. Open in compatible text editor

---

## Security Considerations

### Sensitive Data
- Potential ratings: May require elevated permissions
- Flight risk flags: Restricted export
- Salary/compensation data: Not included in talent exports

### Access Control
- Users can only export data they can view
- Admin can export all data
- Audit log for all exports

### Data Privacy
- Exports respect user data permissions
- Personal data handling compliant with GDPR
- Export retention policy enforced
