# File Management Reporting Guide

## Overview

The File Management module includes a comprehensive reporting center with various reports for document analytics, access auditing, retention monitoring, and operational insights.

## Reports Center

Access the Reports Center via: **Documents → Reports Center**

### Available Reports

1. **File Inventory Report** - Complete list of all documents with metadata
2. **Folder Utilization Report** - Storage and usage statistics by folder
3. **Access Audit Report** - Document access and download history
4. **Retention Status Report** - Documents approaching or past retention dates
5. **Version History Report** - Document versioning activity
6. **Signature Status Report** - Pending and completed signatures
7. **Activity Report** - User activity across documents and folders
8. **Custom Reports** - User-defined report configurations

## Report Details

### File Inventory Report

**Route**: `/documents/report/file-inventory`

**Description**: Complete inventory of all documents with full metadata.

**Columns**:
- Document Code
- Title
- Type
- Category
- Folder
- Owner
- Size
- Status
- Visibility
- Confidentiality
- Created Date
- Updated Date
- Expiry Date
- Version Count

**Filters**:
- Document Type
- Category
- Folder
- Owner
- Status
- Visibility
- Date Range

**Export**: CSV, Excel

### Folder Utilization Report

**Route**: `/documents/report/folder-utilization`

**Description**: Storage usage and document distribution by folder.

**Metrics**:
- Total folders
- Documents per folder
- Total size per folder
- Subfolder count
- Most active folders
- Largest folders
- Empty folders

**Visualizations**:
- Bar chart: Documents by folder
- Pie chart: Size distribution
- Trend: Growth over time

### Access Audit Report

**Route**: `/documents/report/access-audit`

**Description**: Complete audit trail of document access.

**Columns**:
- Timestamp
- User
- Document
- Action (View, Download, Edit, Share)
- IP Address
- User Agent

**Filters**:
- User
- Document
- Action Type
- Date Range
- Folder

**Export**: CSV, Excel

### Retention Status Report

**Route**: `/documents/report/retention-status`

**Description**: Documents approaching expiration or past retention date.

**Columns**:
- Document
- Folder
- Owner
- Expiry Date
- Days Until Expiry
- Status
- Action Required

**Status Values**:
- Active
- Expiring Soon (< 30 days)
- Expired
- Under Review

**Filters**:
- Status
- Date Range
- Owner
- Folder

**Export**: CSV, Excel

### Version History Report

**Route**: `/documents/report/version-history`

**Description**: Document versioning activity and history.

**Columns**:
- Document
- Version Number
- Uploaded By
- Upload Date
- Notes
- Size
- Current Version

**Filters**:
- Document
- User
- Date Range

**Export**: CSV, Excel

### Signature Status Report

**Route**: `/documents/report/signature-status`

**Description**: E-signature workflow status across documents.

**Columns**:
- Document
- Requested By
- Signers
- Request Date
- Due Date
- Status
- Completed Date

**Status Values**:
- Pending
- Partially Signed
- Completed
- Rejected
- Cancelled

**Export**: CSV, Excel

### Activity Report

**Route**: `/documents/report/activity`

**Description**: Overall user activity summary.

**Metrics**:
- Total uploads
- Total downloads
- Total views
- Total shares
- Active users
- Most active users
- Most accessed documents
- Most shared documents

**Visualizations**:
- Line chart: Activity over time
- Bar chart: By action type
- Table: Top users

**Filters**:
- Date Range
- User
- Action Type

## Dashboard Widgets

### File Management Dashboard (`/documents/`)

**Widgets**:
1. Total Documents (stat card)
2. Total Folders (stat card)
3. Storage Used (stat card)
4. Recent Documents (table)
5. Documents by Status (donut chart)
6. Documents by Type (bar chart)
7. Recent Activity (timeline)

### Executive Dashboard (`/documents/executive-dashboard`)

**Widgets**:
1. Total Documents (large stat)
2. Total Storage (large stat)
3. Documents by Department (horizontal bar)
4. Top 10 Most Active Documents (table)
5. Documents Expiring This Month (table)
6. Recent Uploads (table)
7. Activity Trend (line chart)
8. Storage Growth (area chart)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/documents/report/file-inventory` | GET | File inventory data |
| `/documents/report/folder-utilization` | GET | Folder utilization data |
| `/documents/report/access-audit` | GET | Access audit data |
| `/documents/report/retention-status` | GET | Retention status data |
| `/documents/report/export/<type>` | GET | Export report (CSV/Excel) |

## Export Formats

### CSV Export
- UTF-8 encoding with BOM
- Comma-separated values
- Double-quote enclosure for fields with commas

### Excel Export
- .xlsx format
- Sheet named after report
- Auto-sized columns
- Header row formatting

## Scheduled Reports

### Weekly Reports
- Storage usage summary (sent to admins)
- Expiring documents alert
- Checked-out files reminder

### Monthly Reports
- Executive summary
- Department activity
- Retention status

### Quarterly Reports
- Compliance audit
- Archive status
- Growth analysis

## Best Practices

1. **Run reports regularly** to monitor document health
2. **Review retention status** weekly to prevent data loss
3. **Audit access logs** monthly for security compliance
4. **Monitor storage usage** to plan capacity
5. **Track version history** for compliance requirements

## Troubleshooting

### Report Not Loading
- Check filters for invalid date ranges
- Verify user has report permission
- Clear browser cache

### Export Fails
- Ensure sufficient disk space
- Check file size limits
- Verify write permissions for export directory

### Data Missing
- Check if documents have expired
- Verify archive status
- Confirm user permissions
