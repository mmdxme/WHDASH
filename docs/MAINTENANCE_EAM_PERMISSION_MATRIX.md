# Maintenance (EAM/PM) Permission Matrix

## Role Definitions

### Maintenance Administrator
Full system access for maintenance configuration and administration.

| Resource | View | Create | Edit | Delete | Complete | Assign | Export |
|----------|------|--------|------|--------|----------|--------|--------|
| Dashboard | ✓ | - | - | - | - | - | - |
| Equipment | ✓ | ✓ | ✓ | - | - | - | - |
| Work Orders | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| PM Plans | ✓ | ✓ | ✓ | ✓ | - | - | ✓ |
| PM Schedules | ✓ | ✓ | ✓ | ✓ | - | - | ✓ |
| Technicians | ✓ | ✓ | ✓ | - | - | - | - |
| Teams | ✓ | ✓ | ✓ | - | - | - | - |
| Parts Usage | ✓ | ✓ | ✓ | - | - | - | ✓ |
| Labor Logs | ✓ | ✓ | ✓ | - | - | - | ✓ |
| Downtime | ✓ | ✓ | ✓ | - | - | - | ✓ |
| Inspections | ✓ | ✓ | ✓ | - | - | - | ✓ |
| Checklists | ✓ | ✓ | ✓ | ✓ | - | - | - |
| Settings | ✓ | - | ✓ | - | - | - | - |
| Audit Logs | ✓ | - | - | - | - | - | ✓ |

### Maintenance Manager
Operational management of maintenance activities.

| Resource | View | Create | Edit | Delete | Complete | Assign | Export |
|----------|------|--------|------|--------|----------|--------|--------|
| Dashboard | ✓ | - | - | - | - | - | - |
| Equipment | ✓ | ✓ | ✓ | - | - | - | ✓ |
| Work Orders | ✓ | ✓ | ✓ | - | ✓ | ✓ | ✓ |
| PM Plans | ✓ | ✓ | ✓ | - | - | - | ✓ |
| PM Schedules | ✓ | ✓ | ✓ | - | - | - | ✓ |
| Technicians | ✓ | ✓ | ✓ | - | - | - | - |
| Teams | ✓ | ✓ | ✓ | - | - | - | - |
| Parts Usage | ✓ | ✓ | ✓ | - | - | - | ✓ |
| Labor Logs | ✓ | ✓ | ✓ | - | - | - | ✓ |
| Downtime | ✓ | ✓ | ✓ | - | - | - | ✓ |
| Inspections | ✓ | ✓ | ✓ | - | - | - | ✓ |
| Checklists | ✓ | ✓ | ✓ | - | - | - | - |
| Settings | ✓ | - | - | - | - | - | - |
| Audit Logs | ✓ | - | - | - | - | - | ✓ |

### Maintenance Planner
Focus on scheduling and planning work.

| Resource | View | Create | Edit | Delete | Complete | Assign | Export |
|----------|------|--------|------|--------|----------|--------|--------|
| Dashboard | ✓ | - | - | - | - | - | - |
| Planner Board | ✓ | - | ✓ | - | - | ✓ | - |
| Work Orders | ✓ | ✓ | ✓ | - | - | ✓ | ✓ |
| PM Plans | ✓ | ✓ | ✓ | - | - | - | ✓ |
| PM Schedules | ✓ | ✓ | ✓ | - | - | - | ✓ |
| Backlog | ✓ | - | ✓ | - | - | - | - |
| Labor Capacity | ✓ | - | - | - | - | - | - |
| Shift Scheduling | ✓ | ✓ | ✓ | - | - | - | - |
| Overdue Queue | ✓ | - | ✓ | - | - | - | - |

### Technician
Own work orders and time logging.

| Resource | View | Create | Edit | Delete | Complete | Assign | Export |
|----------|------|--------|------|--------|----------|--------|--------|
| My Work Orders | ✓ | - | ✓ | - | ✓ | - | - |
| Work Order Detail | ✓ | - | ✓ | - | ✓ | - | - |
| Tasks | ✓ | - | ✓ | - | ✓ | - | - |
| Labor Logs | ✓ | ✓ | - | - | - | - | - |
| Parts Usage | ✓ | ✓ | - | - | - | - | - |
| Inspections | ✓ | ✓ | - | - | - | - | - |
| Downtime | ✓ | ✓ | - | - | - | - | - |
| Availability | ✓ | - | ✓ | - | - | - | - |

### Supervisor
Team oversight with approval capabilities.

| Resource | View | Create | Edit | Delete | Complete | Assign | Approve | Export |
|----------|------|--------|------|--------|----------|--------|---------|--------|
| Team Work Orders | ✓ | ✓ | ✓ | - | ✓ | ✓ | ✓ | ✓ |
| Team Technicians | ✓ | - | ✓ | - | - | - | - | - |
| Parts Usage | ✓ | ✓ | ✓ | - | - | - | - | ✓ |
| Labor Logs | ✓ | ✓ | ✓ | - | - | - | ✓ | ✓ |
| Approvals | ✓ | - | - | - | - | - | ✓ | - |

### Auditor
Read-only access for compliance review.

| Resource | View | Create | Edit | Delete | Complete | Assign | Export |
|----------|------|--------|------|--------|----------|--------|--------|
| All Maintenance | ✓ | - | - | - | - | - | ✓ |
| Audit Logs | ✓ | - | - | - | - | - | ✓ |
| Reports | ✓ | - | - | - | - | - | ✓ |
| Settings | ✓ | - | - | - | - | - | - |

### Executive Viewer
Dashboard and KPI visibility only.

| Resource | View | Create | Edit | Delete | Complete | Assign | Export |
|----------|------|--------|------|--------|----------|--------|--------|
| Executive Dashboard | ✓ | - | - | - | - | - | ✓ |
| Reports | ✓ | - | - | - | - | - | ✓ |
| Cost Dashboard | ✓ | - | - | - | - | - | ✓ |
| Reliability Dashboard | ✓ | - | - | - | - | - | ✓ |

## Resource-Specific Permissions

### Equipment & Technical Objects
- `equipment.view` - View equipment list and details
- `equipment.create` - Add new equipment
- `equipment.edit` - Modify equipment records
- `equipment.downtime` - View equipment downtime history
- `facilities.view` - View facilities
- `facilities.create` - Create facilities
- `facilities.edit` - Edit facilities
- `facilities.delete` - Delete facilities

### Work Orders
- `work_orders.view` - View all work orders
- `work_orders.create` - Create new work orders
- `work_orders.edit` - Edit work order details
- `work_orders.complete` - Mark work orders complete
- `work_orders.assign` - Assign technicians/teams
- `work_orders.delete` - Delete work orders
- `work_order_tasks.view` - View tasks
- `work_order_tasks.create` - Add tasks
- `work_order_tasks.edit` - Edit tasks
- `work_order_tasks.complete` - Complete tasks

### Preventive Maintenance
- `pm_plans.view` - View PM plans
- `pm_plans.create` - Create PM plans
- `pm_plans.edit` - Edit PM plans
- `pm_plans.delete` - Delete PM plans
- `pm_schedules.view` - View PM schedules
- `pm_calendar.view` - View PM calendar
- `pm_forecast.view` - View PM forecast
- `pm_compliance.view` - View compliance reports

### Corrective & Breakdown
- `corrective.view` - View corrective requests
- `corrective.create` - Create corrective requests
- `corrective.edit` - Edit corrective requests
- `breakdown.view` - View breakdown logs
- `breakdown.create` - Log breakdowns
- `breakdown.edit` - Edit breakdown records
- `emergency.view` - View emergency orders
- `emergency.create` - Create emergency orders
- `root_cause.view` - View root cause analysis
- `recurring_failure.view` - View recurring failures

### Planning & Scheduling
- `planner_board.view` - View planner board
- `planner_board.edit` - Modify schedule assignments
- `backlog.view` - View backlog
- `backlog.edit` - Manage backlog
- `labor_capacity.view` - View capacity
- `shift_scheduling.view` - View shifts
- `shift_scheduling.create` - Create shifts
- `shift_scheduling.edit` - Edit shifts
- `overdue_queue.view` - View overdue items
- `overdue_queue.edit` - Process overdue items

### Resources & Labor
- `technicians.view` - View technicians
- `technicians.create` - Add technicians
- `technicians.edit` - Edit technician records
- `teams.view` - View teams
- `teams.create` - Create teams
- `teams.edit` - Edit teams
- `skills.view` - View skills/certifications
- `skills.create` - Add skills
- `skills.edit` - Edit skills
- `availability.view` - View availability
- `availability.edit` - Update availability
- `utilization.view` - View utilization
- `productivity.view` - View productivity
- `labor_logs.view` - View labor logs
- `labor_logs.create` - Create labor logs
- `labor_logs.edit` - Edit labor logs

### Parts & Materials
- `parts_usage.view` - View parts usage
- `parts_usage.create` - Record parts usage
- `parts_usage.edit` - Edit parts usage
- `parts_reserved.view` - View reservations
- `parts_reserved.create` - Create reservations
- `parts_shortage.view` - View shortage alerts
- `parts_shortage.edit` - Manage shortages
- `spare_watchlist.view` - View watchlist
- `spare_watchlist.create` - Add to watchlist
- `spare_watchlist.edit` - Edit watchlist

### Downtime & Reliability
- `downtime.view` - View downtime logs
- `downtime.create` - Create downtime logs
- `downtime.edit` - Edit downtime logs
- `failure_modes.view` - View failure modes
- `failure_modes.edit` - Manage failure modes
- `mtbf.view` - View MTBF metrics
- `availability_trends.view` - View trends
- `reliability_heatmap.view` - View heatmap
- `reliability_reports.view` - View reports
- `reliability_reports.export` - Export reports

### Shutdown & Turnaround
- `shutdown.view` - View shutdown plans
- `shutdown.create` - Create shutdown plans
- `shutdown.edit` - Edit shutdown plans
- `major_maintenance.view` - View major maintenance
- `major_maintenance.create` - Create events
- `major_maintenance.edit` - Edit events
- `shutdown_risk.view` - View risk review
- `shutdown_risk.edit` - Manage risk review

### Inspections & Checklists
- `inspections.view` - View inspections
- `inspections.create` - Create inspections
- `inspections.edit` - Edit inspections
- `checklists.view` - View checklist templates
- `checklists.create` - Create templates
- `checklists.edit` - Edit templates
- `checklists.delete` - Delete templates
- `defect_findings.view` - View findings
- `defect_findings.create` - Create findings
- `defect_findings.edit` - Edit findings

### Predictive Maintenance
- `predictive.view` - View predictive center
- `condition_indicators.view` - View indicators
- `condition_indicators.create` - Create indicators
- `condition_indicators.edit` - Edit indicators
- `early_warning.view` - View early warnings
- `early_warning.edit` - Manage warnings
- `failure_risk.view` - View failure risk
- `predictive_rules.view` - View rules
- `predictive_rules.create` - Create rules
- `predictive_rules.edit` - Edit rules

### Documents & Technical Records
- `documents.view` - View documents
- `documents.create` - Upload documents
- `documents.edit` - Edit documents
- `documents.delete` - Delete documents
- `attachments.view` - View attachments
- `attachments.create` - Add attachments
- `attachments.edit` - Edit attachments
- `attachments.delete` - Delete attachments
- `service_history.view` - View service history

### Costing & Performance
- `cost_view.view` - View cost dashboard
- `pm_cm_cost.view` - View PM vs CM cost
- `cost_variance.view` - View cost variance
- `labor_cost.view` - View labor cost
- `parts_cost.view` - View parts cost
- `downtime_cost.view` - View downtime cost
- `kpis.view` - View KPIs

### Workflow & Approvals
- `approvals.view` - View approvals
- `approvals.approve` - Approve items
- `approvals.reject` - Reject items
- `sla_policies.view` - View SLA policies
- `sla_policies.create` - Create SLA policies
- `sla_policies.edit` - Edit SLA policies
- `escalations.view` - View escalations
- `escalations.edit` - Manage escalations
- `delegations.view` - View delegations
- `delegations.create` - Create delegations
- `delegations.edit` - Edit delegations
- `approval_history.view` - View approval history

### Reports & Analytics
- `reports.view` - View reports center
- `reports.export` - Export reports
- `report_work_orders.view` - WO report
- `report_pm.view` - PM report
- `report_breakdown.view` - Breakdown report
- `report_downtime.view` - Downtime report
- `report_reliability.view` - Reliability report
- `report_technician.view` - Technician report
- `report_parts.view` - Parts report
- `report_costs.view` - Cost report
- `export.view` - View export center
- `export.export` - Perform exports

### Settings & Administration
- `settings.view` - View settings
- `settings.edit` - Edit settings
- `work_order_settings.view` - View WO settings
- `work_order_settings.edit` - Edit WO settings
- `pm_settings.view` - View PM settings
- `pm_settings.edit` - Edit PM settings
- `scheduling_rules.view` - View scheduling rules
- `scheduling_rules.create` - Create rules
- `scheduling_rules.edit` - Edit rules
- `branch_settings.view` - View branch settings
- `notification_settings.view` - View notifications
- `notification_settings.edit` - Edit notifications
- `audit_logs.view` - View audit logs
- `audit_logs.export` - Export audit logs
