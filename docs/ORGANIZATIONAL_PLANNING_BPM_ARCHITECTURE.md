# Organizational Planning & BPM Architecture

## Overview

The **Organizational Planning & BPM (Business Process Management)** module is a comprehensive enterprise-grade system for managing organizational structure, workforce planning, workflows, approvals, SLA management, and process automation.

This module is designed to be:
- **Deeply integrated** with the entire WHDASH ERP platform
- **Fully multilingual** across all 8 supported languages
- **RTL-aware** for Persian and Arabic interfaces
- **Role-based** with granular permissions
- **Configurable** to meet enterprise requirements

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    WHDASH Application Layer                      │
├─────────────────────────────────────────────────────────────────┤
│  Flask Routes (org_planning_routes.py)                           │
│  ├── Dashboard Routes                                           │
│  ├── Organizational Structure Routes                            │
│  ├── Positions & Roles Routes                                   │
│  ├── Headcount Planning Routes                                  │
│  ├── Delegation Routes                                          │
│  ├── Approval Matrix Routes                                     │
│  ├── Workflow/BPM Routes                                        │
│  ├── Process Instance Routes                                     │
│  ├── SLA & Escalation Routes                                    │
│  ├── Automation Routes                                          │
│  ├── Simulation Routes                                          │
│  ├── Monitoring Routes                                          │
│  └── Reports Routes                                             │
├─────────────────────────────────────────────────────────────────┤
│  Templates (templates/org_planning/)                             │
│  ├── base.html                  - Base template with RTL       │
│  ├── dashboard.html             - Executive dashboard             │
│  ├── structure/                 - Org structure pages           │
│  ├── companies/                 - Company management           │
│  ├── positions/                - Position management          │
│  ├── headcount/                 - Headcount planning           │
│  ├── delegations/               - Delegation management        │
│  ├── approvals/                 - Approval matrix             │
│  ├── workflows/                 - Workflow definitions         │
│  ├── processes/                 - Process instances            │
│  ├── sla/                       - SLA policies                │
│  ├── escalations/               - Escalation logs             │
│  ├── automation/                 - Automation rules            │
│  ├── simulations/               - Reorg simulations            │
│  ├── monitoring/                - Process monitoring          │
│  ├── reports/                   - Analytics & reports         │
│  └── settings/                   - Module settings             │
├─────────────────────────────────────────────────────────────────┤
│  Models (org_planning_models.py)                                │
│  ├── 35+ Database Tables                                       │
│  ├── CRUD Helper Functions                                      │
│  ├── Business Logic Functions                                   │
│  └── Metrics & Analytics Functions                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Core Tables

#### 1. Company Hierarchy
- `op_companies` - Company definitions with hierarchy support

#### 2. Organizational Units
- `op_org_units` - Full org hierarchy (divisions, departments, teams, etc.)

#### 3. Positions & Roles
- `op_positions` - Position definitions with levels, grades, authority
- `op_position_incumbents` - Employee assignments to positions

#### 4. Reporting Structure
- `op_reporting_lines` - Chain of command definitions

#### 5. Headcount Planning
- `op_headcount_plans` - Annual/quarterly headcount plans
- `op_headcount_actuals` - Monthly headcount snapshots

#### 6. Delegations
- `op_delegations` - Delegation and substitution rules

#### 7. Approval Matrix
- `op_approval_matrix` - Approval routing definitions
- `op_approval_matrix_steps` - Approval sequence steps

#### 8. Workflow/BPM
- `op_workflow_definitions` - BPM process definitions
- `op_workflow_versions` - Version tracking
- `op_workflow_steps` - Step definitions
- `op_workflow_transitions` - State transitions

#### 9. Process Instances
- `op_process_instances` - Running workflow instances
- `op_instance_steps` - Step execution history
- `op_instance_actions` - Actions taken
- `op_instance_comments` - Comments/notes

#### 10. SLA Management
- `op_sla_policies` - SLA definitions
- `op_sla_records` - SLA tracking

#### 11. Escalation
- `op_escalation_rules` - Escalation chains
- `op_escalation_logs` - Escalation history

#### 12. Automation
- `op_automation_rules` - Automation rules
- `op_automation_conditions` - Rule conditions
- `op_automation_actions` - Rule actions
- `op_automation_logs` - Execution logs

#### 13. Simulations
- `op_simulation_scenarios` - Reorg scenarios
- `op_simulation_changes` - Change records
- `op_simulation_impacts` - Impact analysis

#### 14. Supporting
- `op_org_history` - Historical snapshots
- `op_dashboard_widgets` - Custom dashboard configs
- `op_notifications` - In-app notifications
- `op_settings` - Module settings
- `op_org_dependencies` - Cross-module links
- `op_process_metrics` - Analytics snapshots

---

## Module Structure

### 1. Organizational Structure
- **Tree View** - Interactive org hierarchy
- **List View** - Card-based unit display
- **Table View** - Dense tabular data
- **Unit Detail** - Full unit information with children

### 2. Positions & Roles
- Position CRUD with level/grade management
- Reporting line configuration
- Authority level assignment
- Succession planning fields

### 3. Headcount Planning
- Annual/quarterly planning by department
- Budget allocation tracking
- Vacancy monitoring
- Utilization metrics

### 4. Delegation Framework
- Temporary/permanent delegations
- Leave-based substitutions
- Scope limiting (modules, amounts)
- Conflict detection

### 5. Approval Matrix
- Amount-based routing
- Sequential/parallel approvals
- Role-based approver assignment
- Quorum rules

### 6. Workflow/BPM
- Visual workflow definitions
- Multiple step types (approval, review, notification, automated)
- Conditional routing
- SLA tracking per step

### 7. Process Instances
- Instance lifecycle management
- Activity timeline
- Comments and attachments
- SLA monitoring

### 8. SLA & Escalation
- Priority-based SLAs
- Business hours support
- Multi-level escalation
- Breach alerts

### 9. Automation Rules
- Trigger-based execution
- Condition evaluation
- Action chains
- Webhook support

### 10. Simulations
- Change scenario planning
- Impact analysis
- Approval workflow previews
- Effective date scheduling

### 11. Monitoring & Analytics
- Process performance metrics
- Bottleneck identification
- SLA compliance tracking
- Trend analysis

---

## Integration Points

### Cross-Module Integration

| Module | Integration |
|--------|-------------|
| HR | Employee positions, headcount, recruitment |
| Finance | Budget allocation, cost centers |
| Procurement | Approval routing for purchase requests |
| Workflow | Extends existing workflow engine |
| Flow | Notifications, messages, approvals |
| Reports | Unified reporting framework |
| Permissions | Shared RBAC system |

### API Endpoints

- `GET /org-planning/api/stats` - Dashboard statistics
- `GET /org-planning/api/org-tree` - Organization tree data
- `GET /org-planning/api/process/<id>` - Process instance details
- `GET /org-planning/api/approval-route` - Find approval route

---

## Permissions Model

The module uses the unified RBAC system with these resources:

- `dashboard` - View dashboard
- `structure` - Manage org units
- `companies` - Manage companies
- `positions` - Manage positions
- `headcount` - Plan headcount
- `delegations` - Manage delegations
- `approval_matrix` - Configure approvals
- `workflows` - Design workflows
- `processes` - Manage instances
- `instances` - Work on tasks
- `sla` - Configure SLAs
- `escalations` - Manage escalations
- `automation` - Configure automation
- `simulations` - Run simulations
- `monitoring` - View analytics
- `reports` - Access reports
- `settings` - Configure settings

---

## Multilingual Support

All 8 languages supported:
- English (en) - Default
- Persian/Farsi (fa) - RTL
- Arabic (ar) - RTL
- Russian (ru)
- Hindi (hi)
- Spanish (es)
- Chinese (zh)
- German (de)

### RTL Implementation
- Base template uses `dir="{{ 'rtl' if is_rtl(lang) else 'ltr' }}"`
- CSS uses `[dir="rtl"]` selectors for mirrored layouts
- Fonts: Vazirmatn for Arabic, system fonts for others

---

## Design System

### UI Framework
- Tailwind CSS via CDN
- Glass-morphism panels
- Custom CSS variables for theming

### Color System
```css
--app-bg: #0f172a
--app-surface: #1e293b
--app-primary: #0ea5e9
--app-success: #10b981
--app-warning: #f59e0b
--app-danger: #ef4444
```

### Components
- Stat cards with gradient accents
- Badge system for statuses
- Table containers with hover states
- Timeline components for activity
- Progress bars for metrics

---

## Future Enhancements

1. **Advanced BPM Designer** - Drag-and-drop workflow builder
2. **Process Mining** - Actual process path analysis
3. **Org Chart Visualization** - Interactive org chart
4. **Mobile App** - Native mobile support
5. **AI Suggestions** - Smart approval routing
6. **Workflow Simulation** - Test before publish
7. **Advanced Analytics** - BI-style dashboards
8. **Document Management** - Integrated DMS

---

## Files Created

| File | Purpose |
|------|---------|
| `org_planning_models.py` | Database models and helpers |
| `org_planning_routes.py` | Flask routes and API |
| `templates/org_planning/*` | 35+ HTML templates |
| `seed_org_planning.py` | Demo data seeder |
| `permissions.py` | Added `org_planning` module |
| `navigation.py` | Added navigation items |
| `translations.py` | Added 200+ translation keys |
| `app.py` | Registered blueprint |
