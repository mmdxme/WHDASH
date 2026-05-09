# Maintenance (EAM/PM) Reporting Guide

## Overview

The Maintenance module provides comprehensive reporting capabilities across all maintenance operations. Reports are designed to provide actionable insights for maintenance managers, planners, technicians, and executives.

## Report Categories

### 1. Work Order Reports

#### Work Order Summary Report
Lists all work orders with key details.

**Parameters:**
- Date Range: Start date, End date
- Status: All, Open, In Progress, Completed, etc.
- Priority: All, Critical, High, Medium, Low
- Type: All, Preventive, Corrective, Emergency

**Columns:**
- Work Order Number
- Asset Code
- Asset Name
- Type
- Priority
- Status
- Assigned Technician
- Issue Date
- Due Date
- Completed Date
- Estimated Cost
- Actual Cost
- Downtime Hours

#### Work Order Detail Report
Detailed view of individual work orders including tasks and history.

**Includes:**
- Full work order details
- Task checklist and status
- Labor logs summary
- Parts usage summary
- Downtime records
- Inspection results
- Cost breakdown
- Timeline of all activities

### 2. Preventive Maintenance Reports

#### PM Compliance Report
Tracks compliance with preventive maintenance schedules.

**Metrics:**
- Total PM schedules
- Compliant schedules (on time)
- Non-compliant schedules (overdue)
- Compliance rate percentage

**Breakdown by:**
- Priority level
- Equipment category
- Maintenance type
- Technician/team

#### PM Forecast Report
Projects upcoming preventive maintenance for planning purposes.

**Forecast Period:** 12 months rolling

**Shows:**
- PMs due by month
- Estimated labor hours
- Required parts
- Cost projections

#### Missed PM Analysis
Reviews PMs that were not completed on schedule.

**Details:**
- Equipment affected
- Days overdue
- Root cause of delay
- Impact assessment

### 3. Breakdown & Downtime Reports

#### Downtime Summary Report
Comprehensive downtime analysis.

**Metrics:**
- Total downtime hours
- Planned vs Unplanned breakdown
- Average incident duration
- Total incidents count

**Analysis by:**
- Equipment
- Downtime reason
- Impact level
- Time period

#### Breakdown Report
Equipment failure analysis.

**Includes:**
- Failure frequency per equipment
- MTBF calculations
- MTTR calculations
- Root cause distribution
- Cost of downtime

#### Reliability Report
Equipment reliability metrics and trends.

**KPIs:**
- MTBF (Mean Time Between Failures)
- MTTR (Mean Time to Repair)
- Availability percentage
- Reliability score

**Visualizations:**
- Trend charts
- Equipment ranking
- Failure mode distribution

### 4. Technician & Labor Reports

#### Technician Utilization Report
Tracks technician workload and productivity.

**Metrics:**
- Total hours worked
- Work orders completed
- Average time per work order
- Utilization percentage

**Analysis:**
- By technician
- By team
- By time period
- By work order type

#### Labor Cost Report
Labor cost analysis and allocation.

**Breakdown:**
- Regular hours vs Overtime
- Cost by work order
- Cost by equipment
- Cost by department

#### Productivity Report
Technician productivity comparisons.

**KPIs:**
- Work orders completed per technician
- Average completion time
- Quality of work (rework rate)
- Utilization efficiency

### 5. Parts & Materials Reports

#### Parts Usage Report
Spare parts consumption analysis.

**Details:**
- Parts issued by work order
- Quantity and cost
- Warehouse source
- Usage trend

#### Spare Parts Shortage Report
Identifies critical spare parts shortages.

**Shows:**
- Current stock levels
- Reorder points
- Shortage quantity
- Impact on maintenance

#### Reserved Parts Report
Parts reserved for upcoming maintenance.

**Details:**
- Reservation date
- Expected use date
- Work order reference
- Reserved quantity

### 6. Cost Reports

#### Maintenance Cost Summary
Total maintenance cost analysis.

**Cost Categories:**
- Labor costs
- Parts costs
- Downtime costs
- External service costs

**Breakdown by:**
- Time period
- Equipment
- Work order type
- Department/Cost center

#### PM vs CM Cost Analysis
Compares preventive vs corrective maintenance costs.

**Rationale:** A healthy maintenance program should show higher PM costs and lower CM costs, indicating proactive maintenance.

**Metrics:**
- PM total cost
- CM total cost
- PM/CM ratio
- Trend analysis

#### Cost Variance Report
Compares estimated vs actual costs.

**Analysis:**
- Variance by work order
- Variance by category
- Variance by technician
- Trend analysis

### 7. Equipment Reports

#### Asset History Report
Complete maintenance history for equipment.

**Includes:**
- All work orders
- All downtime events
- All inspections
- All cost transactions
- Timeline view

#### Equipment Reliability Ranking
Ranks equipment by reliability performance.

**Ranking Factors:**
- Failure frequency
- Downtime impact
- Maintenance cost
- MTBF

### 8. Inspection Reports

#### Inspection Summary Report
Inspection activity and findings.

**Details:**
- Inspections completed
- Pass/Fail rates
- Findings by severity
- Follow-up required

#### Defect Findings Report
Analysis of defects identified during inspections.

**Breakdown:**
- By equipment
- By inspection type
- By severity
- By root cause

## Export Formats

### Excel Export
- Full data preservation
- Multiple worksheets
- Formatted headers
- Automatic column width

### PDF Export
- Print-ready formatting
- Professional report headers
- Summary pages
- Charts and graphs

### CSV Export
- Raw data export
- Easy import to other systems
- Customizable columns
- Large dataset support

## Export Configuration

### Column Selection
Users can select which columns to include in exports.

### Filter Scope
- Date range selection
- Multi-select filters
- Save filter configurations

### Grouping Options
- Group by equipment
- Group by technician
- Group by status
- Group by type

### Sort Order
- Ascending/Descending
- Multiple sort keys
- Custom sort sequences

## Scheduled Reports

### Automated Reports
Configure reports to run automatically on schedule.

**Schedule Options:**
- Daily
- Weekly
- Monthly
- Quarterly

**Distribution:**
- Email to recipients
- Save to file server
- Flow notification

## Report Templates

### Custom Report Builder
Create custom reports using available data fields.

**Capabilities:**
- Field selection
- Calculations
- Filters
- Groupings
- Charts

### Saved Templates
Save report configurations for reuse.

**Template Features:**
- Name and description
- Parameter defaults
- Column selection
- Sort preferences

## Access Control

Reports are filtered based on user permissions:
- Technicians see own data only
- Planners see team data
- Managers see department data
- Admins see all data

## Best Practices

### Daily Reviews
- Check overdue work orders
- Review technician workload
- Monitor PM compliance

### Weekly Analysis
- Backlog trending
- Resource utilization
- Cost variance

### Monthly Reports
- MTBF/MTTR trends
- Cost analysis
- PM compliance rate
- Parts consumption

### Quarterly Reviews
- Equipment reliability ranking
- Program effectiveness
- Budget variance
- Improvement plans
