# Project Management Permission Matrix

This document provides a comprehensive permission matrix for all project management roles. Each role has specific capabilities across the resource areas defined in the system.

## Role Summary

| Role | Description |
|------|-------------|
| **Global Admin** | Full system access with all permissions |
| **PMO Admin** | Administrative access to PMO functions and configuration |
| **PMO Manager** | Manages project portfolio, approves major deliverables |
| **Portfolio Manager** | Oversees programs and project groupings |
| **Program Manager** | Manages related projects grouped under a program |
| **Project Manager** | Day-to-day management of individual projects |
| **Project Coordinator** | Administrative support for project managers |
| **Team Member** | Execute tasks, view assigned project content |
| **Finance Reviewer** | Financial oversight and budget analysis |
| **Procurement Reviewer** | Procurement and vendor coordination |
| **Executive Viewer** | Read-only access to project dashboards |
| **Auditor** | Audit trail access and compliance review |

## Resource Areas and Actions

### Resource Area Definitions

| Resource Area | Description |
|--------------|-------------|
| `dashboard` | Main project dashboard and home page |
| `portfolio` | Portfolio management and grouping |
| `intake` | Project intake requests and approval pipeline |
| `projects` | Project master data management |
| `charter` | Project charter documents |
| `wbs` | Work Breakdown Structure |
| `milestones` | Project milestone tracking |
| `tasks` | Task management |
| `resources` | Resource allocation and management |
| `budget` | Budget tracking and financial management |
| `procurement` | Procurement linkages and vendor management |
| `timesheet` | Time tracking and timesheets |
| `risks` | Risk register and mitigation |
| `issues` | Issue log management |
| `changes` | Change request management |
| `documents` | Document upload and management |
| `governance` | Status updates and governance |
| `reports` | Reporting and analytics |
| `workflow` | Workflow approvals and routing |
| `settings` | System configuration |
| `audit_logs` | Audit trail access |

---

## Global Admin

| Resource Area | View | Create | Edit | Delete | Approve | Export | Configure | Other Actions |
|--------------|------|--------|------|--------|---------|--------|-----------|---------------|
| dashboard | ✓ | — | — | — | — | — | — | — |
| portfolio | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Full access |
| intake | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | All |
| projects | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Archive, Restore |
| charter | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | All |
| wbs | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | All |
| milestones | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Sign-off |
| tasks | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Reassign |
| resources | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Allocate |
| budget | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | All |
| procurement | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Link/Unlink |
| timesheet | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Submit/Approve |
| risks | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Mitigate, Close |
| issues | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Resolve, Escalate, Close |
| changes | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Approve, Reject |
| documents | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Upload, Share |
| governance | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Sign-off |
| reports | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Schedule |
| workflow | ✓ | — | — | — | ✓ | — | — | Delegate, Escalate |
| settings | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ | Manage |
| audit_logs | ✓ | — | — | ✓ | — | ✓ | ✓ | View All, Clear |

---

## PMO Admin

| Resource Area | View | Create | Edit | Delete | Approve | Export | Configure | Other Actions |
|--------------|------|--------|------|--------|---------|--------|-----------|---------------|
| dashboard | ✓ | — | — | — | — | — | — | — |
| executive_dashboard | ✓ | — | — | — | — | — | — | — |
| pmo_workspace | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | Configure |
| portfolio | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | All |
| intake | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Approve, Reject |
| projects | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Archive |
| charter | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| wbs | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| milestones | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Sign-off |
| tasks | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Reassign |
| resources | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Allocate |
| budget | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| procurement | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Link/Unlink |
| timesheet | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Submit/Approve |
| risks | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Mitigate, Close |
| issues | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Resolve, Escalate, Close |
| changes | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Approve, Reject |
| documents | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Upload, Share |
| governance | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Sign-off |
| reports | ✓ | ✓ | ✓ | — | — | ✓ | ✓ | Schedule |
| workflow | ✓ | — | — | — | ✓ | — | — | Delegate, Escalate |
| settings | ✓ | ✓ | ✓ | — | — | — | ✓ | Manage |
| audit_logs | ✓ | — | — | — | — | ✓ | ✓ | View |

---

## PMO Manager

| Resource Area | View | Create | Edit | Delete | Approve | Export | Configure | Other Actions |
|--------------|------|--------|------|--------|---------|--------|-----------|---------------|
| dashboard | ✓ | — | — | — | — | — | — | — |
| executive_dashboard | ✓ | — | — | — | — | — | — | — |
| pmo_workspace | ✓ | — | ✓ | — | ✓ | ✓ | — | — |
| portfolio | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — |
| intake | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Approve, Reject |
| projects | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Archive (own) |
| charter | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — |
| wbs | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — |
| milestones | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Sign-off |
| tasks | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Reassign (own projects) |
| resources | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Allocate |
| budget | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — |
| procurement | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Link/Unlink |
| timesheet | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Approve |
| risks | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Mitigate, Close |
| issues | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Resolve, Escalate, Close |
| changes | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Approve, Reject |
| documents | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Upload, Share |
| governance | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Sign-off |
| reports | ✓ | ✓ | — | — | — | ✓ | — | Schedule |
| workflow | ✓ | — | — | — | ✓ | — | — | Delegate |
| settings | ✓ | — | ✓ | — | — | — | — | — |
| audit_logs | ✓ | — | — | — | — | ✓ | — | View (own projects) |

---

## Portfolio Manager

| Resource Area | View | Create | Edit | Delete | Approve | Export | Configure | Other Actions |
|--------------|------|--------|------|--------|---------|--------|-----------|---------------|
| dashboard | ✓ | — | — | — | — | — | — | — |
| executive_dashboard | ✓ | — | — | — | — | — | — | — |
| portfolio | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — |
| intake | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — |
| projects | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — |
| charter | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — |
| wbs | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — |
| milestones | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Sign-off |
| tasks | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Reassign (own) |
| resources | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Allocate |
| budget | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — |
| procurement | ✓ | ✓ | — | — | ✓ | ✓ | — | — |
| timesheet | ✓ | ✓ | — | — | ✓ | ✓ | — | — |
| risks | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Mitigate, Close |
| issues | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Resolve, Escalate |
| changes | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — |
| documents | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Upload, Share |
| governance | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — |
| reports | ✓ | ✓ | — | — | — | ✓ | — | Schedule |
| workflow | ✓ | — | — | — | ✓ | — | — | — |
| settings | ✓ | — | — | — | — | — | — | — |
| audit_logs | ✓ | — | — | — | — | ✓ | — | View (own portfolio) |

---

## Program Manager

| Resource Area | View | Create | Edit | Delete | Approve | Export | Configure | Other Actions |
|--------------|------|--------|------|--------|---------|--------|-----------|---------------|
| dashboard | ✓ | — | — | — | — | — | — | — |
| portfolio | ✓ | — | — | — | — | ✓ | — | — |
| intake | ✓ | ✓ | — | — | — | ✓ | — | — |
| projects | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — |
| charter | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — |
| wbs | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — |
| milestones | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Sign-off |
| tasks | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Reassign |
| resources | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Allocate |
| budget | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — |
| procurement | ✓ | ✓ | — | — | ✓ | ✓ | — | — |
| timesheet | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Submit, Approve |
| risks | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Mitigate, Close |
| issues | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Resolve, Escalate |
| changes | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — |
| documents | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | Upload, Share |
| governance | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — |
| reports | ✓ | ✓ | — | — | — | ✓ | — | Schedule |
| workflow | ✓ | — | — | — | ✓ | — | — | — |
| settings | ✓ | — | — | — | — | — | — | — |
| audit_logs | ✓ | — | — | — | — | ✓ | — | — |

---

## Project Manager

| Resource Area | View | Create | Edit | Delete | Approve | Export | Configure | Other Actions |
|--------------|------|--------|------|--------|---------|--------|-----------|---------------|
| dashboard | ✓ | — | — | — | — | — | — | — |
| portfolio | ✓ | — | — | — | — | ✓ | — | — |
| intake | ✓ | — | — | — | — | ✓ | — | — |
| projects | ✓ | ✓ | ✓ | — | ✓ | ✓ | — | — |
| charter | ✓ | ✓ | ✓ | — | — | ✓ | — | — |
| wbs | ✓ | ✓ | ✓ | — | — | ✓ | — | — |
| milestones | ✓ | ✓ | ✓ | ✓ | — | ✓ | — | Sign-off |
| tasks | ✓ | ✓ | ✓ | ✓ | — | ✓ | — | Reassign |
| resources | ✓ | ✓ | ✓ | ✓ | — | ✓ | — | Allocate |
| budget | ✓ | ✓ | ✓ | — | — | ✓ | — | — |
| procurement | ✓ | ✓ | — | — | — | ✓ | — | — |
| timesheet | ✓ | ✓ | ✓ | — | — | ✓ | — | Submit |
| risks | ✓ | ✓ | ✓ | ✓ | — | ✓ | — | Mitigate, Close |
| issues | ✓ | ✓ | ✓ | ✓ | — | ✓ | — | Resolve, Escalate |
| changes | ✓ | ✓ | ✓ | ✓ | — | ✓ | — | — |
| documents | ✓ | ✓ | ✓ | ✓ | — | ✓ | — | Upload, Share |
| governance | ✓ | ✓ | ✓ | — | — | ✓ | — | — |
| reports | ✓ | — | — | — | — | ✓ | — | — |
| workflow | ✓ | — | — | — | — | — | — | — |
| settings | ✓ | — | — | — | — | — | — | — |
| audit_logs | ✓ | — | — | — | — | ✓ | — | — |

---

## Project Coordinator

| Resource Area | View | Create | Edit | Delete | Approve | Export | Configure | Other Actions |
|--------------|------|--------|------|--------|---------|--------|-----------|---------------|
| dashboard | ✓ | — | — | — | — | — | — | — |
| portfolio | ✓ | — | — | — | — | ✓ | — | — |
| intake | ✓ | ✓ | ✓ | — | — | ✓ | — | — |
| projects | ✓ | ✓ | ✓ | — | — | ✓ | — | — |
| charter | ✓ | ✓ | ✓ | — | — | ✓ | — | — |
| wbs | ✓ | ✓ | ✓ | — | — | ✓ | — | — |
| milestones | ✓ | ✓ | ✓ | — | — | ✓ | — | — |
| tasks | ✓ | ✓ | ✓ | ✓ | — | ✓ | — | — |
| resources | ✓ | ✓ | ✓ | — | — | ✓ | — | — |
| budget | ✓ | — | — | — | — | ✓ | — | — |
| procurement | ✓ | — | — | — | — | ✓ | — | — |
| timesheet | ✓ | ✓ | ✓ | — | — | ✓ | — | Submit |
| risks | ✓ | ✓ | ✓ | — | — | ✓ | — | — |
| issues | ✓ | ✓ | ✓ | — | — | ✓ | — | — |
| changes | ✓ | ✓ | ✓ | — | — | ✓ | — | — |
| documents | ✓ | ✓ | ✓ | — | — | ✓ | — | Upload |
| governance | ✓ | ✓ | — | — | — | ✓ | — | — |
| reports | ✓ | — | — | — | — | ✓ | — | — |
| workflow | ✓ | — | — | — | — | — | — | — |
| settings | ✓ | — | — | — | — | — | — | — |
| audit_logs | — | — | — | — | — | — | — | — |

---

## Team Member

| Resource Area | View | Create | Edit | Delete | Approve | Export | Configure | Other Actions |
|--------------|------|--------|------|--------|---------|--------|-----------|---------------|
| dashboard | ✓ | — | — | — | — | — | — | — |
| portfolio | ✓ | — | — | — | — | — | — | — |
| intake | — | — | — | — | — | — | — | — |
| projects | ✓ (assigned) | — | — | — | — | — | — | — |
| charter | ✓ (assigned) | — | — | — | — | — | — | — |
| wbs | ✓ (assigned) | — | — | — | — | — | — | — |
| milestones | ✓ (assigned) | — | — | — | — | — | — | — |
| tasks | ✓ (assigned) | ✓ | ✓ | — | — | — | — | Update progress |
| resources | ✓ (assigned) | — | — | — | — | — | — | — |
| budget | — | — | — | — | — | — | — | — |
| procurement | — | — | — | — | — | — | — | — |
| timesheet | ✓ (own) | ✓ | ✓ | — | — | — | — | Submit |
| risks | ✓ (assigned) | ✓ | — | — | — | — | — | — |
| issues | ✓ (assigned) | ✓ | — | — | — | — | — | — |
| changes | ✓ (assigned) | ✓ | — | — | — | — | — | — |
| documents | ✓ (assigned) | — | — | — | — | — | — | Download |
| governance | ✓ (assigned) | — | — | — | — | — | — | — |
| reports | — | — | — | — | — | — | — | — |
| workflow | — | — | — | — | — | — | — | — |
| settings | — | — | — | — | — | — | — | — |
| audit_logs | — | — | — | — | — | — | — | — |

---

## Finance Reviewer

| Resource Area | View | Create | Edit | Delete | Approve | Export | Configure | Other Actions |
|--------------|------|--------|------|--------|---------|--------|-----------|---------------|
| dashboard | ✓ | — | — | — | — | — | — | — |
| portfolio | ✓ | — | — | — | — | ✓ | — | — |
| intake | ✓ | — | — | — | — | ✓ | — | — |
| projects | ✓ | — | — | — | — | ✓ | — | — |
| charter | ✓ | — | — | — | — | ✓ | — | — |
| wbs | ✓ | — | — | — | — | ✓ | — | — |
| milestones | ✓ | — | — | — | — | ✓ | — | — |
| tasks | ✓ | — | — | — | — | ✓ | — | — |
| resources | ✓ | — | — | — | — | ✓ | — | — |
| budget | ✓ | — | ✓ | — | ✓ | ✓ | — | Forecast, Analyze |
| procurement | ✓ | — | — | — | ✓ | ✓ | — | — |
| timesheet | ✓ | — | — | — | ✓ | ✓ | — | Approve |
| risks | ✓ | — | — | — | — | ✓ | — | — |
| issues | ✓ | — | — | — | — | ✓ | — | — |
| changes | ✓ | — | — | — | ✓ | ✓ | — | — |
| documents | ✓ | — | — | — | — | ✓ | — | — |
| governance | ✓ | — | — | — | — | ✓ | — | — |
| reports | ✓ | — | — | — | — | ✓ | — | — |
| workflow | ✓ | — | — | — | ✓ | — | — | — |
| settings | — | — | — | — | — | — | — | — |
| audit_logs | ✓ | — | — | — | — | ✓ | — | — |

---

## Procurement Reviewer

| Resource Area | View | Create | Edit | Delete | Approve | Export | Configure | Other Actions |
|--------------|------|--------|------|--------|---------|--------|-----------|---------------|
| dashboard | ✓ | — | — | — | — | — | — | — |
| portfolio | ✓ | — | — | — | — | ✓ | — | — |
| intake | ✓ | — | — | — | — | ✓ | — | — |
| projects | ✓ | — | — | — | — | ✓ | — | — |
| charter | ✓ | — | — | — | — | ✓ | — | — |
| wbs | ✓ | — | — | — | — | ✓ | — | — |
| milestones | ✓ | — | — | — | — | ✓ | — | — |
| tasks | ✓ | — | — | — | — | ✓ | — | — |
| resources | ✓ | — | — | — | — | ✓ | — | — |
| budget | ✓ | — | — | — | ✓ | ✓ | — | — |
| procurement | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | Link, Unlink |
| timesheet | ✓ | — | — | — | — | ✓ | — | — |
| risks | ✓ | — | — | — | — | ✓ | — | — |
| issues | ✓ | — | — | — | — | ✓ | — | — |
| changes | ✓ | — | — | — | ✓ | ✓ | — | — |
| documents | ✓ | — | — | — | — | ✓ | — | — |
| governance | ✓ | — | — | — | — | ✓ | — | — |
| reports | ✓ | — | — | — | — | ✓ | — | — |
| workflow | ✓ | — | — | — | ✓ | — | — | — |
| settings | — | — | — | — | — | — | — | — |
| audit_logs | ✓ | — | — | — | — | ✓ | — | — |

---

## Executive Viewer

| Resource Area | View | Create | Edit | Delete | Approve | Export | Configure | Other Actions |
|--------------|------|--------|------|--------|---------|--------|-----------|---------------|
| dashboard | ✓ | — | — | — | — | — | — | — |
| executive_dashboard | ✓ | — | — | — | — | — | — | — |
| portfolio | ✓ | — | — | — | — | ✓ | — | — |
| intake | ✓ | — | — | — | — | ✓ | — | — |
| projects | ✓ | — | — | — | — | ✓ | — | — |
| charter | ✓ | — | — | — | — | ✓ | — | — |
| wbs | ✓ | — | — | — | — | ✓ | — | — |
| milestones | ✓ | — | — | — | — | ✓ | — | — |
| tasks | ✓ | — | — | — | — | ✓ | — | — |
| resources | ✓ | — | — | — | — | ✓ | — | — |
| budget | ✓ | — | — | — | — | ✓ | — | — |
| procurement | ✓ | — | — | — | — | ✓ | — | — |
| timesheet | — | — | — | — | — | — | — | — |
| risks | ✓ | — | — | — | — | ✓ | — | — |
| issues | ✓ | — | — | — | — | ✓ | — | — |
| changes | ✓ | — | — | — | — | ✓ | — | — |
| documents | ✓ | — | — | — | — | ✓ | — | — | Download |
| governance | ✓ | — | — | — | — | ✓ | — | — |
| reports | ✓ | — | — | — | — | ✓ | — | — |
| workflow | ✓ | — | — | — | — | — | — | — |
| settings | — | — | — | — | — | — | — | — |
| audit_logs | — | — | — | — | — | — | — | — |

---

## Auditor

| Resource Area | View | Create | Edit | Delete | Approve | Export | Configure | Other Actions |
|--------------|------|--------|------|--------|---------|--------|-----------|---------------|
| dashboard | ✓ | — | — | — | — | — | — | — |
| portfolio | ✓ | — | — | — | — | ✓ | — | — |
| intake | ✓ | — | — | — | — | ✓ | — | — |
| projects | ✓ | — | — | — | — | ✓ | — | — |
| charter | ✓ | — | — | — | — | ✓ | — | — |
| wbs | ✓ | — | — | — | — | ✓ | — | — |
| milestones | ✓ | — | — | — | — | ✓ | — | — |
| tasks | ✓ | — | — | — | — | ✓ | — | — |
| resources | ✓ | — | — | — | — | ✓ | — | — |
| budget | ✓ | — | — | — | — | ✓ | — | — |
| procurement | ✓ | — | — | — | — | ✓ | — | — |
| timesheet | ✓ | — | — | — | — | ✓ | — | — |
| risks | ✓ | — | — | — | — | ✓ | — | — |
| issues | ✓ | — | — | — | — | ✓ | — | — |
| changes | ✓ | — | — | — | — | ✓ | — | — |
| documents | ✓ | — | — | — | — | ✓ | — | — |
| governance | ✓ | — | — | — | — | ✓ | — | — |
| reports | ✓ | — | — | — | — | ✓ | — | — |
| workflow | ✓ | — | — | — | — | — | — | — |
| settings | — | — | — | — | — | — | — | — |
| audit_logs | ✓ | — | — | — | — | ✓ | ✓ | View All, Export All |

---

## Permission Inheritance Rules

1. **Role Hierarchy**: Permissions inherit downward. A PMO Admin has all permissions of a PMO Manager, who has all permissions of a Project Manager, and so on.

2. **Project-Level Overrides**: Individual projects may have custom permission settings that override role-based defaults. These are configured in the Project Settings > Access Control section.

3. **Resource-Based Restrictions**: Some permissions are conditional based on resource assignment. Team Members can only perform actions on tasks or resources explicitly assigned to them.

4. **Company-Level Isolation**: All permission checks are scoped to the user's company. Cross-company access is not permitted unless explicitly granted by a Global Admin.

5. **Temporary Permissions**: Time-limited permissions can be granted for specific projects. These appear with an expiration date in the user's permission list and auto-expire when the duration ends.

## Segregation of Duties Examples

| Duty | Roles Who Can Perform | Roles Who Must NOT Perform |
|------|----------------------|---------------------------|
| Create and approve own project | Project Manager cannot approve their own project | PMO Manager or higher must approve |
| Budget creation and approval | Project Manager creates, Finance Reviewer approves | Creator cannot be approver |
| Issue creation and closure | Reporter creates, different Team Member resolves | Reporter cannot close their own issue |
| Document upload and approval | Project Coordinator uploads, Project Manager approves | Uploader cannot approve |
| User role assignment | PMO Admin assigns roles | Cannot assign roles higher than own |

---

## Quick Reference: Role Comparison

| Capability | PMO Admin | PMO Manager | Portfolio Manager | Program Manager | Project Manager | Team Member |
|-----------|-----------|------------|------------------|----------------|-----------------|-------------|
| Create Project | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Delete Project | ✓ | ✓ | — | — | — | — |
| Approve Project | ✓ | ✓ | ✓ | ✓ | — | — |
| Manage Budget | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Approve Budget | ✓ | ✓ | ✓ | ✓ | — | — |
| View Audit Logs | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Configure Settings | ✓ | — | — | — | — | — |
| Manage Users | ✓ | — | — | — | — | — |
| Export Reports | ✓ | ✓ | ✓ | ✓ | ✓ | — |
| Schedule Reports | ✓ | ✓ | — | — | — | — |
| View All Projects | ✓ | ✓ | Portfolio only | Program only | Assigned only | Assigned only |

---

*Document Version: 1.0*
*Last Updated: April 2026*
*Module: Project Management*
