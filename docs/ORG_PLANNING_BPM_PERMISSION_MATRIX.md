# Organizational Planning & BPM Permission Matrix

## Overview

This document defines the complete permission matrix for the Organizational Planning & BPM module.

## Role Definitions

| Role | Description |
|------|-------------|
| Global Admin | Full system access |
| Org Admin | Organization structure management |
| HR Planning Manager | Headcount and position planning |
| Department Manager | Department-level permissions |
| BPM Admin | Workflow and automation management |
| Approver | Approval workflow participation |
| Supervisor | Team oversight |
| Auditor | Read-only audit access |

## Permission Matrix

### Module: org_planning

| Resource | View | Create | Edit | Delete | Approve | Manage | Other |
|----------|-------|--------|------|--------|---------|--------|-------|
| **dashboard** | ✓ | - | - | - | - | - | - |
| **structure** | ✓ | ✓ | ✓ | ✓ | - | ✓ | - |
| **companies** | ✓ | ✓ | ✓ | ✓ | - | - | - |
| **positions** | ✓ | ✓ | ✓ | ✓ | - | ✓ | assign |
| **headcount** | ✓ | ✓ | ✓ | ✓ | ✓ | - | - |
| **delegations** | ✓ | ✓ | ✓ | ✓ | ✓ | - | - |
| **approval_matrix** | ✓ | ✓ | ✓ | ✓ | ✓ | - | - |
| **workflows** | ✓ | ✓ | ✓ | ✓ | - | - | activate, publish |
| **processes** | ✓ | ✓ | ✓ | ✓ | - | - | cancel, reassign |
| **instances** | ✓ | ✓ | - | - | ✓ | - | approve, reject |
| **sla** | ✓ | ✓ | ✓ | ✓ | - | ✓ | - |
| **escalations** | ✓ | ✓ | ✓ | ✓ | - | ✓ | - |
| **automation** | ✓ | ✓ | ✓ | ✓ | - | - | activate, test |
| **simulations** | ✓ | ✓ | ✓ | ✓ | ✓ | - | publish |
| **monitoring** | ✓ | - | - | - | - | ✓ | - |
| **reports** | ✓ | - | - | - | - | - | export, generate |
| **settings** | ✓ | ✓ | ✓ | ✓ | - | ✓ | - |
| **audit** | ✓ | - | - | - | - | - | export |

## Resource Descriptions

### dashboard
Access to the main Organizational Planning dashboard.

### structure
- **View**: See org units
- **Create**: Add new org units
- **Edit**: Modify existing units
- **Delete**: Remove units
- **Manage**: Move units in hierarchy

### companies
- **View**: See company list
- **Create**: Add new companies
- **Edit**: Modify company details
- **Delete**: Remove companies (if empty)

### positions
- **View**: See positions
- **Create**: Add new positions
- **Edit**: Modify position details
- **Delete**: Remove positions
- **Manage**: Configure reporting lines
- **assign**: Assign incumbents to positions

### headcount
- **View**: See headcount plans
- **Create**: Create new plans
- **Edit**: Modify plans
- **Delete**: Remove plans
- **Approve**: Approve headcount changes

### delegations
- **View**: See delegations
- **Create**: Create delegations
- **Edit**: Modify delegations
- **Delete**: Remove delegations
- **Approve**: Approve delegation requests

### approval_matrix
- **View**: See approval routes
- **Create**: Add approval matrices
- **Edit**: Modify matrices
- **Delete**: Remove matrices
- **Approve**: Activate/deactivate matrices

### workflows
- **View**: See workflow definitions
- **Create**: Create workflows
- **Edit**: Modify workflows
- **Delete**: Remove workflows
- **activate**: Activate workflows
- **publish**: Publish for production

### processes
- **View**: See process instances
- **Create**: Start new instances
- **Edit**: Modify instance details
- **Delete**: Cancel instances
- **cancel**: Cancel running instances
- **reassign**: Assign to different user

### instances
- **View**: See assigned tasks
- **Create**: Create new instances
- **Approve**: Approve items
- **reject**: Reject items

### sla
- **View**: See SLA policies
- **Create**: Add SLA policies
- **Edit**: Modify SLAs
- **Delete**: Remove SLAs
- **Manage**: Configure escalation

### escalations
- **View**: See escalation logs
- **Create**: Add escalation rules
- **Edit**: Modify rules
- **Delete**: Remove rules
- **Manage**: Override escalations

### automation
- **View**: See automation rules
- **Create**: Create rules
- **Edit**: Modify rules
- **Delete**: Remove rules
- **activate**: Enable/disable rules
- **test**: Test rule execution
- **manage**: Full rule management

### simulations
- **View**: See simulations
- **Create**: Create simulations
- **Edit**: Modify simulations
- **Delete**: Remove simulations
- **Approve**: Approve for publishing
- **publish**: Publish changes

### monitoring
- **View**: See process metrics
- **Manage**: Configure alerts

### reports
- **View**: See reports
- **export**: Export to Excel/PDF
- **generate**: Generate new reports

### settings
- **View**: See settings
- **Create**: Add settings
- **Edit**: Modify settings
- **Delete**: Remove settings
- **manage**: Full settings management

### audit
- **View**: See audit logs
- **export**: Export audit data

## Permission Inheritance

1. **Global Admin** has all permissions
2. **Org Admin** has all org_planning permissions except instances approve/reject
3. **BPM Admin** has workflow, process, automation, monitoring permissions
4. **Auditor** has view-only permissions on all resources

## Default Role Assignments

| Role | Resources |
|------|-----------|
| Global Admin | All |
| Org Admin | structure, companies, positions, headcount, delegations, approval_matrix, simulations, reports, settings, audit |
| BPM Admin | workflows, processes, instances, sla, escalations, automation, monitoring |
| HR Planning Manager | positions, headcount, delegations, reports |
| Department Manager | structure (department level), headcount (department), delegations (department), instances |
| Approver | instances (approve, reject) |
| Supervisor | instances (view, complete) |
| Auditor | All (view only) |
| Read-only Executive | dashboard, reports, monitoring (view only) |
