# Project Management Export Configuration Guide

This guide explains how to configure and execute exports for all Project Management reports and data in PDF, Excel, and CSV formats.

## Export Overview

The Project Management module supports exporting data in three primary formats:

| Format | Best Use Case | File Extension |
|--------|---------------|----------------|
| PDF | Executive reports, printable documents, presentations | .pdf |
| Excel | Data analysis, pivot tables, charts, formulas | .xlsx |
| CSV | Data import/export, external systems integration | .csv |

---

## PDF Export Configuration

### General Settings

PDF exports are generated with the following default settings:

- **Page Size**: A4 (210mm × 297mm)
- **Orientation**: Portrait (landscape available for wide tables)
- **Margins**: 20mm all sides
- **Font**: Helvetica (body), Helvetica-Bold (headers)
- **Font Size**: 10pt body, 12pt headers, 8pt footnotes
- **Colors**: Standard business colors with status indicators

### Header Configuration

Each PDF export includes a header section with:

- Report title
- Generation date and time
- Company logo (if configured)
- Report filters applied
- Page numbers

**Customizing the Header:**

1. Go to Reports → Export Center
2. Select "Configure PDF Header"
3. Choose elements to include/exclude
4. Upload company logo (recommended size: 200×60px)
5. Set header position (left, center, right)
6. Preview and save

### Column Configuration for PDF

PDF exports use a simplified column model due to fixed page width:

1. Navigate to the report you want to export
2. Click the export icon (⤴️)
3. Select "PDF"
4. Click "Configure Columns"
5. Available columns appear in two lists:

   **Included Columns** (shown in export):
   - Checkbox to include/exclude
   - Drag to reorder

   **Available Columns** (hidden in export):
   - Drag to "Included" to add

6. Column width is automatically calculated based on content
7. Long column headers wrap to multiple lines
8. Maximum recommended columns: 6-8 for readability

### Data Truncation Settings

For wide reports, configure how to handle overflow:

| Setting | Behavior |
|---------|----------|
| Wrap Text | Wrap header and data to multiple lines |
| Truncate | Cut off text that exceeds column width |
| Abbreviate | Use shortened text (e.g., "Project Manager" → "PM") |
| Rotate Header | Rotate header text 90° to save width |

### Table Formatting

PDF tables support the following formatting options:

- **Zebra Striping**: Alternate row backgrounds (white/light gray)
- **Borders**: Full grid, horizontal only, or none
- **Header Style**: Bold, shaded background, colored text
- **Alignment**: Left, center, or right align per column
- **Number Formatting**: Decimal places, thousand separator, currency symbol
- **Date Formatting**: Locale-aware date formats

### PDF Security Options

Configure security settings for sensitive exports:

| Option | Description |
|--------|-------------|
| Password Protection | Require password to open |
| Encryption | 128-bit AES encryption |
| Print Permission | Allow/disallow printing |
| Copy Permission | Allow/disallow copying content |
| Modify Permission | Allow/disallow modifications |
| Extract Permission | Allow/disallow text extraction |

### PDF Charts and Graphs

When exporting reports with charts:

1. Charts are rendered as high-resolution images
2. Chart image format: PNG at 300dpi
3. Chart colors follow company theme (if configured)
4. Interactive charts (hover for values) are flattened
5. Legends and data labels included

### Multi-Sheet PDF

For complex exports, generate multi-sheet PDFs:

- Sheet 1: Executive Summary
- Sheet 2: Detailed Data
- Sheet 3: Charts and Graphs
- Sheet 4: Appendix/Supporting Data

---

## Excel Export Configuration

### General Settings

Excel exports preserve data for maximum flexibility:

- **Format**: XLSX (Excel 2007+)
- **Compatibility**: Excel 2010, 2013, 2016, 2019, Office 365
- **Sheet Names**: Auto-generated, configurable per sheet
- **Maximum Rows**: Limited by Excel (1,048,576 rows)
- **Maximum Columns**: 16,384 columns (XFD)

### Column Configuration

Excel exports offer full column control:

1. Go to report → Export → Excel
2. Click "Configure Columns"
3. The column configuration panel shows:

   ```
   Column Name        | Include | Width | Format | Sort Order
   -------------------|---------|-------|--------|------------
   Project Code      | ✓       | Auto  | Text   | 1
   Project Name      | ✓       | 30    | Text   | 2
   Status            | ✓       | 15    | Text   | 3
   Budget            | ✓       | 15    | Currency | 4
   Spent             | ✓       | 15    | Currency | 5
   Variance          | ✓       | 12    | Percent | 6
   ```

4. **Include**: Checkbox to show/hide column
5. **Width**: Pixels or "Auto-fit"
6. **Format**: Text, Number, Currency, Percent, Date, DateTime
7. **Sort Order**: Drag to set multi-column sort priority

### Numeric Formatting Options

| Format Type | Options | Example Output |
|-------------|---------|----------------|
| Number | Decimal places (0-10) | 1,234.56 |
| Currency | Symbol, decimal places | $1,234.56 |
| Accounting | Symbol, aligned | $ 1,234.56 |
| Percent | Decimal places | 12.35% |
| Scientific | Standard notation | 1.23E+05 |
| Custom | User-defined pattern | [Red](#,##0.00) |

### Date/Time Formatting

| Format Code | Example Output |
|-------------|----------------|
| YYYY-MM-DD | 2026-04-20 |
| DD/MM/YYYY | 20/04/2026 |
| MM/DD/YYYY | 04/20/2026 |
| YYYY-MMM-DD | 2026-Apr-20 |
| MMM DD, YYYY | Apr 20, 2026 |
| HH:MM:SS | 14:30:00 |
| YYYY-MM-DD HH:MM | 2026-04-20 14:30 |

### Formula Preservation

Excel exports can include calculated formulas:

| Formula Type | Options |
|--------------|---------|
| Variance | `=Budget - Spent` |
| Variance % | `=(Budget - Spent) / Budget` |
| CPI | `=EarnedValue / ActualCost` |
| Health Score | `=IF(SPI>=1,"Green",IF(SPI>=0.9,"Yellow","Red"))` |

Enable "Include Formulas" checkbox to preserve calculated fields.

### Grouping and Outline

Enable hierarchical grouping in Excel:

1. Check "Enable Grouping"
2. Select grouping level columns
3. Choose collapse/expand default
4. Subtotals: None, Sum, Average, Count

### Pivot Table Export

Generate export as Pivot Table:

1. Check "Export as Pivot Table"
2. Select row fields
3. Select column fields
4. Select value fields with aggregation
5. Select report filter fields

### Conditional Formatting

Apply conditional formatting to cells:

- **Color Scales**: Gradient from red (low) to green (high)
- **Data Bars**: Horizontal bars showing relative values
- **Icon Sets**: Traffic light, arrows, shapes
- **Rules**: Highlight cells meeting criteria

Configure in: Export Settings → Conditional Formatting

### Excel Sheet Organization

Multi-sheet Excel workbooks:

| Sheet | Content |
|-------|---------|
| Summary | Aggregated metrics and KPIs |
| Detail | Full transaction-level data |
| Charts | Embedded chart visualizations |
| Metadata | Report parameters, generation info |

### Named Ranges

Create Excel named ranges for external references:

- `ProjectList` → All project codes
- `ActiveProjects` → Filtered active projects
- `BudgetTotal` → Sum of all budgets

---

## CSV Export Configuration

### General Settings

CSV exports provide raw data for maximum compatibility:

- **Encoding**: UTF-8 (default), UTF-8 BOM, UTF-16, ASCII
- **Delimiter**: Comma (default), Tab, Semicolon, Pipe, Custom
- **Quote Character**: Double quote (default) or single quote
- **Line Ending**: CRLF (Windows) or LF (Unix/Mac)
- **Include Header Row**: Yes (default) or No
- **Include Subtotals**: Yes or No

### Column Configuration

CSV exports can include/exclude and reorder columns:

1. Navigate to report → Export → CSV
2. Click "Configure Columns"
3. Drag columns between Available and Included lists
4. Set sort order by numbering
5. Click "Apply"

### Data Transformation

Apply transformations to CSV data:

| Transform | Description | Example |
|-----------|-------------|---------|
| Trim | Remove leading/trailing spaces | " Project " → "Project" |
| Uppercase | Convert to uppercase | "active" → "ACTIVE" |
| Lowercase | Convert to lowercase | "ACTIVE" → "active" |
| Proper Case | Capitalize each word | "project manager" → "Project Manager" |
| Date Format | Standardize date output | 2026-04-20, 04/20/2026 |
| Number Format | Standardize numeric output | 1234.56, 1,234.56 |
| Replace | Find and replace text | Replace "N/A" with blank |
| Concatenate | Combine multiple columns | FirstName + " " + LastName |
| Calculate | Add calculated columns | Budget - Spent = Variance |

### Null/Empty Value Handling

Configure how to represent empty values:

| Setting | Output |
|---------|--------|
| Empty String | (nothing between delimiters) |
| Null | NULL |
| Custom Text | "N/A", "None", "-", etc. |
| Preserve Original | Keep source system value |

### CSV Date Range Options

Date filters apply to CSV exports:

| Option | Behavior |
|--------|----------|
| All Data | No date filtering |
| Specific Range | Start and end date |
| Relative Period | Last N days/weeks/months |
| Current Period | This week/month/quarter/year |
| Custom Period | User-defined period |

### Grouping Options for CSV

CSV does not support Excel grouping, but offers aggregation:

- **No Grouping**: Raw transaction data
- **Group by Single Column**: Summarize by one field
- **Group by Multiple Columns**: Hierarchical summary

Aggregation functions for grouped CSV:

- Sum
- Average
- Count
- Min
- Max
- First
- Last

### Sort Configuration for CSV

Configure multi-level sorting:

1. Click "Configure Sort"
2. Select primary sort column
3. Choose ascending or descending
4. Add secondary sort columns
5. Maximum 5 sort levels

Sort applies before grouping.

### File Naming Configuration

Customize export filename using tokens:

| Token | Description | Example Output |
|-------|-------------|----------------|
| `{ReportType}` | Report name | "Project_Status" |
| `{ProjectCode}` | Single project code | "PRJ00001" |
| `{ProjectName}` | Single project name | "ERP_Implementation" |
| `{Date}` | Generation date | "2026-04-20" |
| `{DateTime}` | Generation datetime | "2026-04-20_1430" |
| `{User}` | Current username | "jsmith" |
| `{Company}` | Company name | "Acme_Corp" |
| `{Status}` | Report filter status | "Active" |
| `{YYYY}` | Year | "2026" |
| `{MM}` | Month | "04" |
| `{DD}` | Day | "20" |

**Default Pattern**: `{ReportType}_{DateTime}.csv`

**Example Filenames**:
- `Project_Status_2026-04-20.csv`
- `Budget_vs_Actual_PRJ00001_2026-Q1.csv`
- `Risk_Register_AllProjects_2026-04-20_1430.csv`

### CSV Character Handling

Special characters in CSV exports:

| Character | Standard Handling | Safe Handling |
|-----------|------------------|----------------|
| Comma (,) | Field delimiter | Quoted: "Value, with comma" |
| Quote (") | Field enclosure | Escaped: "He said ""Hello""" |
| Newline | Row separator | Quoted or replaced with \n |
| Tab | Potential delimiter | Quoted or replaced with space |
| Accented | Preserved in UTF-8 | Transliterated for ASCII |

---

## Filter Configuration for All Formats

### Standard Filters

All exports respect the filters configured on the report:

1. Set filters on the report view
2. Click Export
3. Select format (PDF/Excel/CSV)
4. Check "Apply Current Filters"
5. Optionally save filter preset

### Save Filter Presets

Save frequently used filter combinations:

1. Configure filters on report
2. Click "Save Filter Preset"
3. Enter preset name
4. Select share scope: Personal, Team, All Users
5. Click "Save"

**Using Presets**:
1. Click "Load Preset"
2. Select saved preset
3. Filters applied automatically

### Predefined Filter Presets

| Preset Name | Filters Applied |
|------------|-----------------|
| Active Projects | Status = Active |
| My Projects | Project Manager = Current User |
| Overdue | Status = Active, End Date < Today |
| High Priority | Priority = Critical, High |
| Q1 Projects | Planned Start >= Jan 1, Planned Start <= Mar 31 |
| Budget Review | Budget > 0, Status in (Active, On Hold) |

---

## Scheduling Exports

### Creating a Scheduled Export

1. Configure report and filters
2. Click Export → Schedule
3. Set schedule parameters:

   **Frequency Options**:
   - One-time (specific date/time)
   - Daily (specify time)
   - Weekly (specify day and time)
   - Monthly (specify date and time)
   - Quarterly
   - Custom cron expression

4. Set delivery method
5. Configure notifications
6. Click "Schedule"

### Delivery Methods

| Method | Configuration |
|--------|---------------|
| Download | Automatic browser download |
| Email | SMTP server, recipient list, subject template |
| Shared Link | Expiration date, access permissions |
| SFTP | Server, username, key/password, path |
| Cloud Storage | Google Drive, Dropbox, OneDrive OAuth |

### Notification Settings

Configure notifications for scheduled exports:

- **On Success**: Notify when export generated and delivered
- **On Failure**: Notify when export generation fails
- **Recipients**: Specific users, roles, or email addresses
- **Message Template**: Custom notification message

---

## Advanced Export Options

### Snapshot vs Dynamic Data

| Mode | Description |
|------|-------------|
| Snapshot | Data captured at generation time, static |
| Dynamic | Linked to live data, updates on open (Excel only) |

### Watermarks

Add watermarks to PDF exports:

1. Go to Export Settings → Watermark
2. Enter watermark text
3. Select position (diagonal, header, footer)
4. Set opacity (10-100%)
5. Select color
6. Preview and save

### Automated Export Rules

Configure automated export triggers:

- **Status Change**: Export when project status changes
- **Threshold Exceeded**: Export when budget exceeds % threshold
- **Milestone Due**: Export when milestone approaches
- **Schedule Slippage**: Export when project delays beyond N days
- **Manual Trigger**: Export via API or button click

### Bulk Export

Export multiple reports in one package:

1. Go to Reports → Export Center
2. Select multiple reports (checkbox)
3. Click "Bulk Export"
4. Choose format per report or single format for all
5. Reports packaged as ZIP archive

### Export History

Track all exports:

| Field | Description |
|-------|-------------|
| Export ID | Unique identifier |
| Report Type | Which report was exported |
| Format | PDF/Excel/CSV |
| Generated By | User who triggered export |
| Generated At | Date/time |
| Filters Applied | Which filters were active |
| File Size | Size of export file |
| Download Count | Times downloaded |
| Scheduled | Whether scheduled or on-demand |

---

## Troubleshooting Exports

### Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Excel file won't open | File corruption | Re-export, check encoding |
| Missing columns | Filter excludes all data | Adjust filters, check column config |
| Wrong dates | Timezone difference | Set timezone in user preferences |
| Special characters garbled | Encoding mismatch | Use UTF-8 encoding |
| File too large | Too many rows/columns | Apply filters, reduce columns |
| Charts not rendering | Memory limit | Reduce chart data range |
| Scheduled export failed | System error | Check notification, retry manually |
| Password not working | Wrong password | Reset export password |

### Performance Guidelines

| Export Type | Recommended Limits |
|-------------|-------------------|
| PDF | Max 10,000 rows, 20 pages |
| Excel | Max 100,000 rows per sheet |
| CSV | Max 500,000 rows |

For larger datasets, use incremental exports by filtering date ranges or project subsets.

---

*Document Version: 1.0*
*Last Updated: April 2026*
*Module: Project Management*
