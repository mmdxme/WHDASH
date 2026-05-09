# Maintenance (EAM/PM) Module Architecture

## Overview

The Maintenance module is an enterprise-grade Enterprise Asset Management (EAM) and Preventive Maintenance (PM) system that integrates deeply with the WHDASH ERP platform. It provides comprehensive equipment maintenance tracking, work order management, preventive scheduling, resource planning, and reliability analytics.

## Module Structure

### Navigation Hierarchy

```
Maintenance (EAM/PM) [fa-tools icon]
├── Dashboards
│   ├── Maintenance Dashboard
│   ├── Executive Dashboard
│   └── Maintenance Workspace
├── Equipment & Technical Objects
│   ├── Equipment Register
│   ├── Equipment Detail
│   ├── Equipment Downtime
│   ├── Facilities
│   └── Facility Requests
├── Preventive Maintenance
│   ├── PM Plans
│   ├── PM Schedules
│   ├── PM Calendar View
│   ├── PM Forecast
│   ├── PM Compliance
│   └── Missed PM Review
├── Corrective & Breakdown
│   ├── Corrective Requests
│   ├── Breakdown Calls
│   ├── Emergency Orders
│   ├── Incident Logging
│   ├── Root Cause Review
│   └── Recurring Failure Review
├── Work Orders
│   ├── All Work Orders
│   ├── Create Work Order
│   ├── Open Work Orders
│   ├── Planned Work Orders
│   ├── Released Work Orders
│   ├── In Process Work Orders
│   ├── Completed Work Orders
│   ├── Closed Work Orders
│   └── My Work Orders
├── Planning & Scheduling
│   ├── Planner Board
│   ├── Backlog Management
│   ├── Labor Capacity
│   ├── Shift Scheduling
│   └── Overdue Queue
├── Resources & Labor
│   ├── Technicians & Teams
│   ├── Teams
│   ├── Skills & Certifications
│   ├── Availability
│   ├── Utilization
│   └── Productivity
├── Parts & Materials
│   ├── Parts Usage
│   ├── Reserved Parts
│   ├── Shortage Alerts
│   └── Critical Spare Watchlist
├── Downtime & Reliability
│   ├── Downtime Log
│   ├── Failure Modes
│   ├── MTBF / MTTR
│   ├── Availability Trends
│   └── Reliability Heatmap
├── Shutdown Planning
│   ├── Shutdown Plans
│   ├── Major Maintenance Events
│   └── Shutdown Risk Review
├── Inspections & Checklists
│   ├── Inspections
│   ├── Checklist Templates
│   └── Defect Findings
├── Predictive Maintenance
│   ├── Predictive Maintenance
│   ├── Condition Indicators
│   ├── Early Warning Review
│   └── Failure Risk View
├── Documents & Records
│   ├── Documents & SOPs
│   ├── Attachments
│   └── Service History Files
├── Costing & Performance
│   ├── Maintenance Cost View
│   ├── PM vs CM Cost
│   ├── Cost Variance
│   └── Performance KPIs
├── Workflow & Approvals
│   ├── Pending Approvals
│   ├── SLA Policies
│   ├── Escalations
│   ├── Delegations
│   └── Approval History
├── Reports & Analytics
│   ├── Reports Center
│   ├── Work Order Report
│   ├── PM Compliance Report
│   ├── Breakdown Report
│   ├── Downtime Report
│   ├── Reliability Report
│   ├── Technician Utilization
│   ├── Parts Usage Report
│   ├── Cost Report
│   └── Export Center
└── Settings
    ├── Maintenance Settings
    ├── Work Order Settings
    ├── PM Settings
    ├── Scheduling Rules
    ├── Branch/Entity Settings
    ├── Notification Settings
    └── Audit Logs
```

## Database Schema

### Core Tables

#### maintenance_facilities
Facilities, buildings, sites master records.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| facility_code | TEXT | Unique facility code |
| name | TEXT | Facility name |
| facility_type | TEXT | Building, Warehouse, etc. |
| parent_facility_id | INTEGER | Hierarchical location |
| is_critical | INTEGER | Critical facility flag |

#### maintenance_work_orders
Core work order tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| work_order_number | TEXT | Unique WO number |
| asset_id | INTEGER | Linked asset |
| maintenance_type_id | INTEGER | PM, Corrective, etc. |
| work_order_type | TEXT | Type classification |
| priority | TEXT | Low/Medium/High/Critical |
| status | TEXT | Draft/Open/Approved/etc. |
| issue_date | DATE | Date reported |
| scheduled_start_date | DATE | Planned start |
| scheduled_end_date | DATE | Planned end |
| assigned_technician_id | INTEGER | Assigned technician |
| estimated_cost | DECIMAL | Estimated cost |
| actual_cost | DECIMAL | Actual cost |
| downtime_hours | DECIMAL | Production downtime |

#### maintenance_schedules
Preventive maintenance plans and schedules.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| asset_id | INTEGER | Equipment to maintain |
| schedule_name | TEXT | PM plan name |
| frequency | TEXT | Daily/Weekly/Monthly/etc. |
| interval_days | INTEGER | Custom interval |
| next_due_date | DATE | Next due date |
| last_performed_date | DATE | Last completion |
| assigned_technician_id | INTEGER | Default technician |

#### maintenance_downtime_logs
Equipment downtime tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| log_number | TEXT | Unique log number |
| asset_id | INTEGER | Equipment |
| work_order_id | INTEGER | Linked WO |
| downtime_start | DATETIME | Start time |
| downtime_end | DATETIME | End time |
| total_hours | DECIMAL | Duration |
| impact_level | TEXT | Negligible to Catastrophic |
| root_cause | TEXT | Root cause |
| corrective_action | TEXT | Action taken |

#### maintenance_teams
Maintenance team definitions.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| team_code | TEXT | Unique code |
| team_name | TEXT | Team name |
| team_lead_id | INTEGER | Team lead employee |
| max_concurrent_work_orders | INTEGER | Capacity limit |

#### maintenance_labor_logs
Technician time tracking.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| log_number | TEXT | Unique log number |
| work_order_id | INTEGER | Linked WO |
| technician_id | INTEGER | Employee |
| work_date | DATE | Date worked |
| total_hours | DECIMAL | Hours worked |
| hourly_rate | DECIMAL | Labor rate |
| labor_cost | DECIMAL | Total labor cost |

#### maintenance_parts_usage
Spare parts consumption.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| usage_number | TEXT | Unique usage number |
| work_order_id | INTEGER | Linked WO |
| part_id | INTEGER | Inventory part |
| quantity_requested | DECIMAL | Requested qty |
| quantity_issued | DECIMAL | Issued qty |
| quantity_used | DECIMAL | Used qty |
| unit_cost | DECIMAL | Cost per unit |
| total_cost | DECIMAL | Total cost |

#### maintenance_checklist_templates
Reusable inspection checklists.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| template_code | TEXT | Unique code |
| template_name | TEXT | Template name |
| checklist_type | TEXT | Inspection/Safety/etc. |
| applicable_to | TEXT | Equipment type |

#### maintenance_sla_rules
SLA configuration by priority.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| priority | TEXT | Priority level |
| response_time_hours | INTEGER | Response SLA |
| resolution_time_hours | INTEGER | Resolution SLA |
| escalation_1_hours | INTEGER | First escalation |
| escalation_2_hours | INTEGER | Second escalation |

## Integration Points

### Assets Module
- Equipment linked to assets table
- Maintenance history on asset detail
- Depreciation impact from downtime

### Warehouse (WMS)
- Parts reservation and issuance
- Stock level visibility
- Shortage alerts to procurement

### Procurement
- Emergency purchase requests
- Spare parts procurement
- Vendor assignment for external work

### Quality
- Defect-triggered maintenance
- Inspection findings
- Compliance documentation

### Finance
- Maintenance cost tracking
- Work order costing
- Budget variance reporting

### Flow
- Critical breakdown alerts
- Overdue work order notifications
- PM due reminders
- Approval routing

## Key Features

### 1. Work Order Lifecycle
Complete status flow:
```
Draft → Open → Approved → Planned → Released → In Progress → Waiting Parts/Vendor → Completed → Verified → Closed
```

### 2. PM Auto-Generation
- System generates work orders from due PM schedules
- Maintains next due dates automatically
- Links completed WOs back to PM plans

### 3. SLA Tracking
- Response time monitoring
- Resolution time tracking
- Automatic escalation triggers

### 4. Cost Tracking
- Labor costs from time logs
- Parts costs from issuance
- Downtime cost estimation
- Variance analysis

### 5. Reliability Metrics
- MTBF calculation
- MTTR tracking
- Availability percentages
- Failure mode analysis

## Routes

| Route | Description |
|-------|-------------|
| /maintenance/dashboard | Main dashboard |
| /maintenance/executive-dashboard | Executive KPIs |
| /maintenance/planner-board | Kanban scheduling |
| /maintenance/equipment | Equipment list |
| /maintenance/work-orders | Work order list |
| /maintenance/pm-plans | PM plan management |
| /maintenance/pm-schedules | PM calendar |
| /maintenance/reliability-dashboard | MTBF/MTTR dashboard |
| /maintenance/breakdown-center | Emergency management |
| /maintenance/export | Export center |

## Permissions

### Roles
- **Maintenance Admin**: Full access
- **Maintenance Manager**: Manager-level access
- **Maintenance Planner**: Scheduling access
- **Technician**: Own work orders only
- **Supervisor**: Team oversight
- **Auditor**: Read-only audit access

### Permission Categories
- dashboard: view
- equipment: view, create, edit
- work_orders: view, create, edit, complete, assign, delete
- pm_plans: view, create, edit, delete
- technicians: view, create, edit
- parts_usage: view, create, edit
- labor_logs: view, create, edit
- downtime: view, create, edit
- inspections: view, create, edit
- reports: view, export
- settings: view, edit
- audit_logs: view, export

## Technical Stack
- Backend: Flask/Python
- Database: SQLite with WAL mode
- Frontend: HTML5/TailwindCSS
- JavaScript: Vanilla JS with Fetch API
- Icons: FontAwesome 6
- Charts: Chart.js integration ready
