# Quality Management Reporting Guide

## Overview

The Quality Management module provides comprehensive reporting and analytics capabilities across all quality functions. Reports can be filtered, exported, and customized to meet operational and executive needs.

## Report Types

### 1. Inspection Reports

#### Inspection Summary Report
- **Purpose**: Overview of all inspections with pass/fail rates and trends
- **Filters**: Date range, Branch, Warehouse, Inspection Type, Status, Result, Supplier
- **Metrics**: Total inspections, Pass rate, Fail rate, Pass by type chart
- **Export**: PDF, Excel, CSV

#### Incoming Inspection Report
- **Purpose**: Detailed analysis of incoming goods inspections by supplier
- **Filters**: Date range, Supplier, Item Category, Inspection Result
- **Metrics**: Inspection counts, Pass rates, Reject rates, Top defect categories
- **Export**: PDF, Excel, CSV

#### In-Process Inspection Report
- **Purpose**: Quality control during manufacturing or processing
- **Filters**: Date range, Production Line, Process, Shift
- **Metrics**: Pass rates by process, First-pass yield, Defect distribution
- **Export**: PDF, Excel, CSV

#### Final Inspection Report
- **Purpose**: Outgoing quality verification and release
- **Filters**: Date range, Customer, Order, Inspector
- **Metrics**: Final pass rates, Hold rates, Release authorization status
- **Export**: PDF, Excel, CSV

### 2. NCR Reports

#### NCR Summary Report
- **Purpose**: Overview of non-conformances by status, severity, and category
- **Filters**: Date range, Branch, Warehouse, Severity, Status, Category, Owner
- **Metrics**: NCR counts by status/severity/category, Average resolution time
- **Charts**: Status pie chart, Severity bar chart, Category distribution
- **Export**: PDF, Excel, CSV

#### Critical NCR Report
- **Purpose**: Analysis of critical and major NCRs requiring immediate attention
- **Filters**: Date range, Severity (CRITICAL, MAJOR), Status
- **Metrics**: Critical NCR count, Overdue critical NCRs, NCR with open CAPAs
- **Export**: PDF, Excel, CSV

#### Overdue NCR Report
- **Purpose**: NCRs past target closure date requiring escalation
- **Filters**: Days overdue threshold, Owner, Branch
- **Metrics**: Overdue count, Days overdue distribution, Escalation status
- **Export**: PDF, Excel, CSV

#### NCR Trend Analysis
- **Purpose**: Historical trends and patterns in non-conformances
- **Filters**: Date range, Monthly/Quarterly/Yearly grouping
- **Metrics**: NCR trend line, Category shifts, Resolution time trends
- **Charts**: Line chart, Stacked area chart
- **Export**: PDF, Excel, CSV

### 3. CAPA Reports

#### CAPA Summary Report
- **Purpose**: Overview of corrective and preventive actions
- **Filters**: Date range, Type, Status, Category, Owner, Department
- **Metrics**: CAPA counts, Open/Closed, By type pie chart
- **Export**: PDF, Excel, CSV

#### Effectiveness Review Report
- **Purpose**: CAPA effectiveness verification and closure analysis
- **Filters**: Review date range, Effectiveness result
- **Metrics**: Effective rate, Recurrence rate, Average time to effectiveness
- **Charts**: Effectiveness by type, Recurrence scatter
- **Export**: PDF, Excel, CSV

#### Overdue CAPA Report
- **Purpose**: CAPAs past target date requiring management attention
- **Filters**: Days overdue threshold, Owner
- **Metrics**: Overdue count, Average days overdue
- **Export**: PDF, Excel, CSV

#### Recurring Issues Report
- **Purpose**: CAPAs linked to repeat non-conformances
- **Filters**: Date range, Recurrence count threshold
- **Metrics**: Repeat CAPA count, Issues by root cause category
- **Export**: PDF, Excel, CSV

### 4. Audit Reports

#### Audit Summary Report
- **Purpose**: Overview of all audits by type, status, and results
- **Filters**: Date range, Audit type, Status, Lead Auditor, Branch
- **Metrics**: Audit counts by type/status, Completion rate, Finding rate
- **Export**: PDF, Excel, CSV

#### Audit Findings Report
- **Purpose**: Detailed analysis of audit findings by severity
- **Filters**: Date range, Severity, Status, Finding category, Auditor
- **Metrics**: Finding counts by severity/status, Average closure time
- **Charts**: Severity distribution, Status pie chart, Monthly trend
- **Export**: PDF, Excel, CSV

#### Audit Calendar Report
- **Purpose**: Scheduled and completed audits timeline
- **Filters**: Date range, Audit type, Department
- **Metrics**: Upcoming audits, Completion rate, On-time completion
- **Export**: PDF, Excel, CSV

#### Auditor Performance Report
- **Purpose**: Audit team workload and effectiveness analysis
- **Filters**: Auditor, Date range
- **Metrics**: Findings per auditor, Average audit duration, On-time rate
- **Export**: PDF, Excel, CSV

### 5. Supplier Quality Reports

#### Supplier Scorecard Report
- **Purpose**: Supplier quality performance metrics and ratings
- **Filters**: Supplier, Date range, Qualification status
- **Metrics**: Quality score, Pass rate, NCR count, Reject rate, Trend
- **Charts**: Score distribution, Trend comparison
- **Export**: PDF, Excel, CSV

#### Supplier Defect Rate Report
- **Purpose**: Incoming defect rates by supplier comparison
- **Filters**: Supplier, Date range, Item category
- **Metrics**: PPM defect rate, DPMO, Defect count
- **Charts**: Bar chart comparison, Trend line
- **Export**: PDF, Excel, CSV

#### Supplier NCR Analysis
- **Purpose**: NCR distribution and trends by supplier
- **Filters**: Supplier, Date range, Severity
- **Metrics**: NCR count, Critical NCR rate, Resolution time
- **Export**: PDF, Excel, CSV

#### Supplier Quality Trend Report
- **Purpose**: Historical supplier quality performance trends
- **Filters**: Supplier, Date range, Metric type
- **Charts**: Multi-line trend chart, Rolling average comparison
- **Export**: PDF, Excel, CSV

### 6. Additional Reports

#### Held Inventory Report
- **Purpose**: Items under quality hold and disposition status
- **Filters**: Date range, Hold reason, Item category
- **Metrics**: Hold count, Value at hold, Age distribution
- **Export**: PDF, Excel, CSV

#### Defect Analysis Report
- **Purpose**: Defect categorization and Pareto analysis
- **Filters**: Date range, Defect category, Severity, Production line
- **Metrics**: Defect counts, Pareto distribution, Top contributors
- **Charts**: Pareto chart, Defect category pie
- **Export**: PDF, Excel, CSV

#### Cost of Poor Quality Report
- **Purpose**: Financial impact of scrap, rework, and rejections
- **Filters**: Date range, Cost category, Department
- **Metrics**: Total COPQ, By cost type (scrap/rework/rejection), Trend
- **Charts**: Cost breakdown pie, Monthly trend
- **Export**: PDF, Excel, CSV

#### Compliance Report
- **Purpose**: Regulatory and standard compliance status
- **Filters**: Standard/Regulation, Compliance status
- **Metrics**: Compliance rate, Non-conformances by area
- **Export**: PDF, Excel, CSV

## Export Configuration

### Export Formats
- **PDF**: Print-ready formatted reports
- **Excel**: Native Excel with formatting preserved
- **CSV**: Raw data export for analysis

### Column Selection
Users can select which columns to include in exports:
1. Navigate to report page
2. Click "Configure Columns" or settings icon
3. Check/uncheck columns to include
4. Set column order via drag-and-drop
5. Save preferences for future exports

### Filter Configuration
- Save filter configurations as presets
- Schedule automated report generation
- Share filter presets with team members

## Custom Reports

### Report Builder
The custom report builder allows users to:
- Select data source (inspection, NCR, CAPA, etc.)
- Choose fields to display
- Apply filters and groupings
- Add calculated fields
- Save as custom report template

### Access
- Custom report permissions: `quality.custom_reports`
- Admin can manage all custom reports
- Users can view/edit their own reports

## Report Scheduling

### Automated Reports
- Schedule daily, weekly, monthly reports
- Configure recipients
- Set delivery time
- Enable/disable as needed

### Access Permissions
- `quality.reports`: View own reports
- `quality.reports.generate`: Create scheduled reports
- `quality.export_center`: Manage export configurations

## Dashboard Widgets

### Available Dashboard Reports
- Open NCR count (with severity breakdown)
- Overdue NCR count
- Open CAPA count
- Overdue CAPA count
- Pending inspections
- Failed inspections
- Active audits
- Open audit findings
- Supplier quality score
- Quality pass rate trend

### Widget Configuration
- Drag-and-drop widget arrangement
- Resize widgets
- Set refresh interval
- Configure alert thresholds

## Data Retention

Quality report data is retained according to:
- Company policy settings
- Regulatory requirements
- Database cleanup schedules

## Performance Optimization

- Report data is cached for frequently accessed reports
- Large datasets use pagination
- Export time depends on data volume
- Consider date range limits for large exports
