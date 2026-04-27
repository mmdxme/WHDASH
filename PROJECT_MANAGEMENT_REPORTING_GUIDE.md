# Project Management Reporting Guide

This guide describes all reports available in the Project Management module, their configuration options, and how to use scheduling features.

## Available Reports Overview

| Report | Category | Description |
|--------|----------|-------------|
| Project Status Report | Status | Current health and progress of projects |
| WBS Report | Schedule | Work Breakdown Structure breakdown |
| Milestone Report | Schedule | Milestone tracking and completion |
| Resource Utilization Report | Resource | Team member allocation and usage |
| Budget vs Actual Report | Financial | Budget consumption analysis |
| Risk Register Report | Risk | Active risks and mitigation status |
| Issue Log Report | Risk | Open issues and resolution tracking |
| Change Request Report | Risk | Change request analysis |
| Deliverables Report | Status | Project deliverables tracking |
| Project Health Report | Status | Health metrics and indicators |
| Portfolio Summary Report | Portfolio | Portfolio-level overview |
| PMO Dashboard Report | PMO | PMO performance metrics |

---

## Project Status Report

### Description
The Project Status Report provides a comprehensive overview of project health, including current status, progress percentage, schedule performance, and key metrics for all active projects in the portfolio.

### Data Included
- Project code and name
- Project manager and sponsor
- Current status (Draft, Active, On Hold, Completed, Cancelled)
- Progress percentage (0-100%)
- Planned vs actual start and end dates
- Days remaining or overdue
- Schedule variance calculation
- Status trend (improving, stable, declining)
- Last status update date and author

### Available Filters
| Filter | Type | Description |
|--------|------|-------------|
| Status | Multi-select | Filter by project status values |
| Priority | Multi-select | Filter by priority (Critical, High, Medium, Low) |
| Project Manager | Multi-select | Filter by assigned PM |
| Date Range | Date range | Filter by planned end date window |
| Portfolio | Multi-select | Filter by portfolio assignment |
| Project Type | Multi-select | Filter by project type |
| Tags | Multi-select | Filter by project tags |
| Show Archived | Boolean | Include/exclude archived projects |

### Export Formats
- **PDF**: Formatted report with charts and status indicators
- **Excel (.xlsx)**: Full data with formatting preserved
- **CSV**: Raw data export for analysis
- **HTML**: Web-viewable format

### Scheduling Options
- **One-time**: Run immediately or at specified date/time
- **Recurring**: Daily, Weekly (specify day), Monthly (specify date)
- **Trigger-based**: Run when status changes, when milestone due, when budget threshold exceeded

---

## WBS Report

### Description
The WBS (Work Breakdown Structure) Report shows the complete hierarchical structure of project deliverables, organized by WBS codes with associated tasks, resources, and completion status.

### Data Included
- WBS code and name hierarchy
- WBS level (1-5 levels deep)
- Associated tasks count
- Task completion percentage per WBS node
- Planned hours vs actual hours per WBS node
- Resource assignments per WBS node
- Cost allocation per WBS node
- Critical path indicator

### Available Filters
| Filter | Type | Description |
|--------|------|-------------|
| Project | Required | Select single or multiple projects |
| WBS Level | Range | Filter by level depth |
| WBS Code | Pattern | Filter by code prefix pattern |
| Show Tasks | Boolean | Include/exclude task details |
| Show Resources | Boolean | Include/exclude resource details |
| Cost Filter | Range | Filter by cost threshold |
| Completion % | Range | Filter by completion percentage |

### Export Formats
- **PDF**: Hierarchical tree view with expandable sections
- **Excel**: Outline view with indentation preserved
- **CSV**: Flattened structure with level indicators

### Scheduling Options
- Schedule with project reports or run standalone
- Include only changed WBS nodes in delta reports

---

## Milestone Report

### Description
The Milestone Report tracks all project milestones, their planned dates, actual completion dates, approval status, and overdue analysis.

### Data Included
- Milestone code and name
- Associated project
- Milestone type (Phase End, Deliverable, External, Decision)
- Owner
- Planned date
- Target date
- Actual completion date (if completed)
- Days variance (planned vs actual)
- Status (Pending, In Progress, Completed, Overdue, Cancelled)
- Approval required flag
- Approver and approval date
- Tasks linked to milestone

### Available Filters
| Filter | Type | Description |
|--------|------|-------------|
| Project | Multi-select | Filter by project |
| Status | Multi-select | Filter by status |
| Milestone Type | Multi-select | Filter by type |
| Date Range | Date range | Filter by planned/target date |
| Overdue Only | Boolean | Show only overdue milestones |
| Due Within | Number | Filter milestones due within N days |
| Owner | Multi-select | Filter by owner |
| Show Approved | Boolean | Include/exclude approved milestones |

### Export Formats
- **PDF**: Calendar-style layout with color coding
- **Excel**: Gantt-style timeline view
- **CSV**: Full milestone data

### Scheduling Options
- Weekly milestone reminder reports
- Overdue milestone alerts
- Upcoming milestone notifications (configurable lead time: 7, 14, 30 days)

---

## Resource Utilization Report

### Description
The Resource Utilization Report shows how project resources (team members) are allocated across projects, their utilization percentage, and workload analysis.

### Data Included
- Resource name and role
- Project assignment
- Allocation percentage per project
- Total allocated hours
- Total actual hours logged
- Utilization percentage (actual/budgeted)
- Workload status (Under-utilized, Optimal, Over-allocated)
- Available capacity
- Skills/capabilities matching
- Allocation timeline (start/end dates)

### Available Filters
| Filter | Type | Description |
|--------|------|-------------|
| Resource | Multi-select | Filter by specific resources |
| Role | Multi-select | Filter by role type |
| Project | Multi-select | Filter by project |
| Utilization Range | Range | Filter by utilization percentage |
| Date Range | Date range | Filter by allocation period |
| Show Over-allocated | Boolean | Show only over-allocated resources |
| Show Under-allocated | Boolean | Show only under-utilized resources |
| Company | Multi-select | Filter by company |

### Export Formats
- **PDF**: Visual charts and heat maps
- **Excel**: Pivot table ready format
- **CSV**: Time-phased allocation data

### Scheduling Options
- Weekly utilization summary
- Over-allocation alerts
- Monthly capacity planning reports

---

## Budget vs Actual Report

### Description
The Budget vs Actual Report provides detailed financial analysis of project budgets, comparing planned budget, committed costs, actual expenditure, and variance analysis.

### Data Included
- Project code and name
- Budget code and cost center
- Total approved budget
- Budget by cost category (Labor, Materials, Vendors, Travel, Other)
- Committed costs (purchase orders, contracts)
- Actual costs to date
- Remaining budget
- Variance (Budget - Actual)
- Variance percentage
- Cost performance index (CPI)
- Forecasted final cost
- Burn rate analysis
- Budget approval history

### Available Filters
| Filter | Type | Description |
|--------|------|-------------|
| Project | Multi-select | Filter by project |
| Cost Category | Multi-select | Filter by expense type |
| Budget Code | Multi-select | Filter by budget code |
| Date Range | Date range | Filter by cost incurred period |
| Show Over-budget | Boolean | Show only over-budget items |
| Show Under-budget | Boolean | Show only under-budget items |
| Vendor | Multi-select | Filter by vendor charges |
| Include Labor | Boolean | Include/exclude labor costs |
| Threshold | Number | Show items exceeding variance threshold % |

### Export Formats
- **PDF**: Executive summary with charts
- **Excel**: Detailed worksheet with formulas
- **CSV**: Transaction-level detail

### Scheduling Options
- Weekly budget variance alerts
- Monthly financial summaries
- Over-budget warning triggers
- Quarter-end financial reports

---

## Risk Register Report

### Description
The Risk Register Report provides a comprehensive view of all identified project risks, their probability, impact, mitigation strategies, and current status.

### Data Included
- Risk ID and title
- Associated project
- Risk category (Technical, Schedule, Budget, External, Operational)
- Probability assessment (Very Low, Low, Medium, High, Very High)
- Impact assessment (Very Low, Low, Medium, High, Very High)
- Risk score (Probability × Impact)
- Mitigation strategy
- Contingency plan
- Risk owner
- Status (Identified, Monitoring, Mitigating, Resolved, Accepted)
- Trigger date
- Review date
- Date identified
- Date last updated
- Related issues

### Available Filters
| Filter | Type | Description |
|--------|------|-------------|
| Project | Multi-select | Filter by project |
| Status | Multi-select | Filter by risk status |
| Category | Multi-select | Filter by category |
| Probability | Multi-select | Filter by probability level |
| Impact | Multi-select | Filter by impact level |
| Risk Score | Range | Filter by calculated score |
| Owner | Multi-select | Filter by risk owner |
| Date Range | Date range | Filter by identification date |
| Show Resolved | Boolean | Include/exclude resolved risks |
| Top N | Number | Show top N highest risks |

### Export Formats
- **PDF**: Risk matrix heat map format
- **Excel**: Analysis-ready format with formulas
- **CSV**: Register data

### Scheduling Options
- Weekly risk review reports
- High-risk alert notifications
- Monthly trend analysis

---

## Issue Log Report

### Description
The Issue Log Report tracks all project issues and blockers, their severity, status, and resolution progress.

### Data Included
- Issue number and title
- Associated project
- Task linkage (if applicable)
- Category (Technical, Resource, Budget, Scope, Communication)
- Severity (Critical, High, Medium, Low)
- Impact description
- Issue owner
- Reported by
- Reported date
- Due date
- Is blocker flag
- Status (Open, In Progress, Pending Info, Resolved, Closed)
- Root cause analysis
- Mitigation plan
- Resolution date
- Closure notes
- Days open calculation
- Escalation level

### Available Filters
| Filter | Type | Description |
|--------|------|-------------|
| Project | Multi-select | Filter by project |
| Status | Multi-select | Filter by status |
| Severity | Multi-select | Filter by severity |
| Category | Multi-select | Filter by category |
| Is Blocker | Boolean | Show only blockers |
| Owner | Multi-select | Filter by owner |
| Date Range | Date range | Filter by reported date |
| Overdue Only | Boolean | Show issues past due date |
| Show Resolved | Boolean | Include/exclude closed issues |

### Export Formats
- **PDF**: Summary with severity indicators
- **Excel**: Action item tracking format
- **CSV**: Issue register data

### Scheduling Options
- Daily issue summary
- Critical issue alerts
- Weekly resolution metrics

---

## Change Request Report

### Description
The Change Request Report tracks all change requests submitted against projects, their impact analysis, approval status, and implementation tracking.

### Data Included
- Change request number
- Associated project
- Request title and description
- Request type (Scope, Schedule, Budget, Resource)
- Requested by
- Requested date
- Impact analysis (schedule, budget, resource)
- Affected WBS elements
- Estimated cost impact
- Estimated schedule impact
- Approval status (Pending, Approved, Rejected, Withdrawn)
- Approver and decision date
- Rejection reason (if applicable)
- Implementation status
- Implementation date
- Change category

### Available Filters
| Filter | Type | Description |
|--------|------|-------------|
| Project | Multi-select | Filter by project |
| Status | Multi-select | Filter by approval status |
| Type | Multi-select | Filter by change type |
| Requester | Multi-select | Filter by requester |
| Date Range | Date range | Filter by request date |
| Impact | Multi-select | Filter by impact level |
| Show Pending | Boolean | Include/exclude pending requests |
| Show Approved | Boolean | Include/exclude approved requests |

### Export Formats
- **PDF**: Impact summary format
- **Excel**: Analysis format
- **CSV**: Change register

### Scheduling Options
- Weekly change summary
- Pending approval reminders
- Impact trend analysis

---

## Deliverables Report

### Description
The Deliverables Report tracks all project deliverables, their planned completion dates, actual delivery dates, and acceptance status.

### Data Included
- Deliverable name and description
- Associated project
- Associated WBS element
- Milestone linkage
- Planned delivery date
- Actual delivery date
- Delivery status (Pending, In Progress, Delivered, Accepted, Rejected)
- Acceptance criteria
- Review required flag
- Reviewed by
- Reviewed date
- Quality status
- Notes

### Available Filters
| Filter | Type | Description |
|--------|------|-------------|
| Project | Multi-select | Filter by project |
| Status | Multi-select | Filter by delivery status |
| Date Range | Date range | Filter by planned date |
| Show Overdue | Boolean | Show only overdue deliverables |
| Show Pending Acceptance | Boolean | Show deliverables awaiting acceptance |

### Export Formats
- **PDF**: Deliverable checklist format
- **Excel**: Tracking format
- **CSV**: Deliverable data

---

## Project Health Report

### Description
The Project Health Report provides an analytical dashboard assessing overall project health using multiple indicators including schedule performance, cost performance, quality metrics, and risk indicators.

### Data Included
- Health score (0-100) with trend
- Schedule health indicator (On Track, At Risk, Behind)
- Budget health indicator (On Budget, At Risk, Over Budget)
- Scope health indicator
- Resource health indicator
- Quality health indicator
- Risk health indicator
- Overall status determination
- Days until next milestone
- Days until project end
- Critical path status
- Open issues count
- Open risks count
- Blocker count
- Team velocity
- Stakeholder satisfaction score
- Recommendation summary

### Available Filters
| Filter | Type | Description |
|--------|------|-------------|
| Project | Required | Select project(s) |
| Health Categories | Multi-select | Filter by specific health types |
| Score Range | Range | Filter by health score |
| Date Snapshot | Date | Generate report for specific date |
| Include Historical | Boolean | Include trend history |

### Export Formats
- **PDF**: Executive dashboard format with gauges
- **Excel**: Detailed metrics with charts
- **CSV**: Raw health data

### Scheduling Options
- Weekly health snapshots
- Health degradation alerts
- Monthly health trends

---

## Portfolio Summary Report

### Description
The Portfolio Summary Report provides executive-level visibility into all projects within a portfolio, showing aggregated metrics, status distribution, and portfolio health.

### Data Included
- Portfolio name and description
- Total projects count
- Projects by status distribution
- Budget summary (total, approved, spent)
- Overall portfolio health score
- Project type distribution
- Priority distribution
- Resource utilization summary
- Risk summary (total risks, high risks)
- Issue summary (total issues, blockers)
- Schedule overview (on time, at risk, late)
- Program breakdown (if applicable)
- Strategic alignment scores
- Portfolio value metrics
- ROI summary (if configured)

### Available Filters
| Filter | Type | Description |
|--------|------|-------------|
| Portfolio | Multi-select | Filter by portfolio |
| Status | Multi-select | Filter by status |
| Date Snapshot | Date | Portfolio state at specific date |
| Include Programs | Boolean | Include program rollup |
| Show Historical | Boolean | Include trend data |

### Export Formats
- **PDF**: Executive summary format
- **Excel**: Portfolio analysis format
- **CSV**: Aggregated data

### Scheduling Options
- Weekly portfolio status
- Monthly executive summary
- Quarterly board reports

---

## PMO Dashboard Report

### Description
The PMO Dashboard Report provides metrics on PMO performance, project governance compliance, process adherence, and PMO value delivery.

### Data Included
- Total active projects
- Projects by status
- Average project health score
- On-time delivery rate
- On-budget delivery rate
- First-time quality rate
- Project success rate
- Planned vs actual benefits
- Governance compliance percentage
- Process adherence score
- PMO maturity indicators
- Resource utilization rate
- Active risks across portfolio
- Issues resolution time
- Average project duration
- Projects completed this period
- Pipeline summary
- PMO recommendations

### Available Filters
| Filter | Type | Description |
|--------|------|-------------|
| Time Period | Selection | This week, month, quarter, year |
| PMO Level | Multi-select | Filter by organizational level |
| Show Trends | Boolean | Include historical comparison |
| Include Forecast | Boolean | Include forecasts |

### Export Formats
- **PDF**: Dashboard snapshot format
- **Excel**: Metrics with charts
- **CSV**: Raw data

### Scheduling Options
- Weekly PMO metrics
- Monthly executive summary
- Quarter-end analysis

---

## Export Configuration Guide

### Column Selection

For each report, you can configure which columns to include:

1. Navigate to Reports section
2. Select your report type
3. Click "Configure Columns"
4. Check/uncheck columns to include
5. Drag to reorder columns
6. Click "Apply"

### Filter Configuration

1. Click "Filters" button on report page
2. Select filter fields from dropdown
3. Set operator (equals, contains, greater than, etc.)
4. Enter or select filter values
5. Add multiple filters with AND/OR logic
6. Click "Apply Filters"

### Date Range Options

| Option | Description |
|--------|-------------|
| Today | Current date only |
| This Week | Monday to Sunday |
| This Month | First to last day of month |
| This Quarter | Q1 (Jan-Mar), Q2 (Apr-Jun), Q3 (Jul-Sep), Q4 (Oct-Dec) |
| This Year | January 1 to December 31 |
| Custom Range | User-specified start and end dates |
| Relative | "Last N days/weeks/months" |
| Fiscal Year | Based on company fiscal calendar |

### Grouping Options

Reports can be grouped by:
- Project
- Status
- Priority
- Project Manager
- Department
- Project Type
- Date (day/week/month/quarter)
- Cost Category
- WBS Level

### Sort Options

- Ascending (A-Z, 0-9)
- Descending (Z-A, 9-0)
- Multiple sort levels supported
- Default sort varies by report

### File Naming

Configure export filename patterns:
- `{ReportType}_{ProjectCode}_{Date}.{ext}`
- `{ReportType}_{DateRange}.{ext}`
- Custom prefix option
- Date format: YYYYMMDD, YYYY-MM-DD, DD/MM/YYYY

---

## Report Scheduling

### Schedule Types

| Type | Frequency | Options |
|------|-----------|---------|
| One-time | Once | Specific date and time |
| Daily | Every day | Select time |
| Weekly | Every week | Select day(s) and time |
| Monthly | Every month | Select date and time |
| Quarterly | Every quarter | Select start date and time |
| Yearly | Every year | Select date and time |
| On Event | Triggered | Status change, threshold exceeded |

### Delivery Options

- **Download**: Save to local device
- **Email**: Send to configured email addresses
- **Shared Link**: Generate shareable URL (with optional expiration)
- **Cloud Storage**: Save to Google Drive, Dropbox, OneDrive (configured)

### Notification Settings

- Success notification: Report generated successfully
- Failure notification: Report generation failed
- No data notification: Report ran but returned empty result
- Custom recipients per report

### Retention Settings

- Keep all versions
- Keep last N versions
- Keep versions from last N days
- Delete after download

---

*Document Version: 1.0*
*Last Updated: April 2026*
*Module: Project Management*
