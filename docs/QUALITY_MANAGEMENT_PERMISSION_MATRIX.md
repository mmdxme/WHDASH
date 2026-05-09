# Quality Management Permission Matrix

## Overview

The Quality Management module implements a comprehensive Role-Based Access Control (RBAC) system that ensures appropriate access at module, menu, page, and action levels. This document details all permissions, roles, and access control mechanisms.

## Permission Structure

### Permission Format

Permissions follow the format: `('module', 'resource', 'action')`

Examples:
- `('quality', 'inspections', 'view')` - View inspections
- `('quality', 'ncr', 'approve')` - Approve NCRs
- `('quality', '*', '*')` - Full access to all quality resources

## Quality Module Permission Resources

### Main Areas

| Resource | Permissions | Description |
|----------|-------------|-------------|
| `dashboard` | view | Quality Dashboard access |
| `executive_dashboard` | view | Executive Quality Dashboard |
| `workspace` | view | Quality Workspace |

### Inspections

| Resource | Permissions | Description |
|----------|-------------|-------------|
| `inspections` | view, create, edit, delete, approve, execute, hold_release | Main inspection operations |
| `inspection_plans` | view, create, edit, delete, approve, execute | Inspection planning |
| `inspection_templates` | view, create, edit, delete, manage | Checklist templates |
| `inspection_results` | view, create, edit, delete | Result entry and management |
| `re_inspection` | view, create, execute | Re-inspection workflows |

### NCR / Non-Conformance

| Resource | Permissions | Description |
|----------|-------------|-------------|
| `ncr` | view, create, edit, delete, approve, resolve, close, escalate | NCR management |
| `ncr_containment` | view, create, edit, delete, verify | Containment actions |
| `ncr_disposition` | view, create, edit, approve, execute | Disposition decisions |

### CAPA

| Resource | Permissions | Description |
|----------|-------------|-------------|
| `capa` | view, create, edit, delete, approve, verify, close, reopen | CAPA management |
| `capa_actions` | view, create, edit, delete, complete, verify | CAPA action items |
| `capa_effectiveness` | view, create, edit, approve, close | Effectiveness reviews |

### Audits

| Resource | Permissions | Description |
|----------|-------------|-------------|
| `audits` | view, create, edit, delete, approve, execute, close, cancel | Audit management |
| `audit_programs` | view, create, edit, delete, manage | Annual audit programs |
| `audit_checklists` | view, create, edit, delete, manage | Checklist templates |
| `audit_findings` | view, create, edit, delete, verify, close | Finding management |
| `audit_finding_actions` | view, create, edit, delete, complete | Finding action items |

### Supplier Quality

| Resource | Permissions | Description |
|----------|-------------|-------------|
| `supplier_quality` | view, create, edit, approve, block, unblock | Supplier quality status |
| `supplier_scorecards` | view, create, edit, delete, export | Scorecard management |
| `supplier_ncr` | view, create, edit, resolve | Supplier NCRs |
| `supplier_capa` | view, create, edit, resolve | Supplier CAPAs |

### Quality Holds & Disposition

| Resource | Permissions | Description |
|----------|-------------|-------------|
| `quality_holds` | view, create, release, reject, rework, scrap | Hold management |
| `disposition` | view, create, edit, approve, execute | Disposition workflow |
| `quarantine` | view, create, edit, release, approve | Quarantine management |

### Defects & Scrap

| Resource | Permissions | Description |
|----------|-------------|-------------|
| `defects` | view, create, edit, analyze, export | Defect register |
| `scrap` | view, create, edit, approve, export | Scrap management |
| `rework` | view, create, edit, approve, complete | Rework orders |
| `cost_of_quality` | view, export, analyze | COPQ analysis |

### SPC & Analytics

| Resource | Permissions | Description |
|----------|-------------|-------------|
| `spc` | view, create, edit, configure, export | SPC configuration |
| `control_charts` | view, create, edit, delete, configure | Control chart setup |
| `quality_trends` | view, export, analyze | Trend analysis |
| `anomaly_review` | view, create, edit, resolve, export | Anomaly handling |

### Documents & Compliance

| Resource | Permissions | Description |
|----------|-------------|-------------|
| `quality_documents` | view, create, edit, delete, approve, publish | Quality documents |
| `controlled_docs` | view, create, edit, delete, approve, release | Controlled documents |
| `compliance` | view, create, edit, approve, export, manage | Compliance management |
| `certifications` | view, create, edit, delete, approve, manage | Certifications |

### Risk Management

| Resource | Permissions | Description |
|----------|-------------|-------------|
| `quality_risks` | view, create, edit, mitigate, close, manage | Risk register |
| `risk_assessment` | view, create, edit, approve, manage | Risk assessments |
| `critical_control_points` | view, create, edit, delete, manage | CCP management |
| `escalation_rules` | view, create, edit, delete, manage | Escalation configuration |

### Workflow & Approvals

| Resource | Permissions | Description |
|----------|-------------|-------------|
| `approvals` | view, approve, reject, delegate, escalate | Approval actions |
| `approval_matrix` | view, create, edit, delete, manage | Approval rules |
| `sla_policies` | view, create, edit, delete, manage | SLA configuration |

### Settings

| Resource | Permissions | Description |
|----------|-------------|-------------|
| `settings` | view, edit, manage | General settings |
| `inspection_settings` | view, edit, manage | Inspection configuration |
| `ncr_settings` | view, edit, manage | NCR configuration |
| `capa_settings` | view, edit, manage | CAPA configuration |
| `audit_settings` | view, edit, manage | Audit configuration |
| `supplier_quality_settings` | view, edit, manage | Supplier quality config |
| `compliance_settings` | view, edit, manage | Compliance settings |
| `notification_settings` | view, edit, manage | Notification settings |

### Reports

| Resource | Permissions | Description |
|----------|-------------|-------------|
| `reports` | view, export, generate, schedule | General reporting |
| `inspection_reports` | view, export | Inspection reports |
| `ncr_reports` | view, export | NCR reports |
| `capa_reports` | view, export | CAPA reports |
| `audit_reports` | view, export | Audit reports |
| `supplier_quality_reports` | view, export | Supplier quality reports |
| `defect_reports` | view, export | Defect analysis reports |
| `compliance_reports` | view, export | Compliance reports |
| `custom_reports` | view, create, edit, delete, export, generate | Custom report builder |
| `export_center` | view, create, edit, delete, export, manage | Export management |

### Other

| Resource | Permissions | Description |
|----------|-------------|-------------|
| `audit_log` | view, export | Audit trail access |
| `quality_plans` | view, create, edit, delete, approve, execute | Quality planning |
| `sampling_rules` | view, create, edit, delete, manage | Sampling rules |
| `test_methods` | view, create, edit, delete, manage | Test methods |
| `specifications` | view, create, edit, delete, manage, approve | Quality specifications |

## Pre-Defined Roles

### 1. Quality Admin
Full administrative access to all quality functions.
```
('quality', '*', '*')
```

### 2. QA Manager (Senior)
Senior quality assurance oversight.
```
('quality', '*', '*')
('reports', 'executive', 'view')
('reports', 'operational', 'view')
('tasks', 'tasks', 'view')
```

### 3. QC Inspector
Quality control inspection and testing.
```
('quality', 'dashboard', 'view')
('quality', 'inspections', ['view', 'create', 'edit', 'execute'])
('quality', 'inspection_plans', ['view', 'create', 'edit'])
('quality', 'inspection_templates', 'view')
('quality', 're_inspection', ['view', 'create'])
('quality', 'ncr', ['view', 'create'])
('quality', 'inspection_reports', ['view', 'export'])
```

### 4. NCR Coordinator
NCR management specialist.
```
('quality', 'dashboard', 'view')
('quality', 'ncr', ['view', 'create', 'edit', 'approve', 'resolve', 'close'])
('quality', 'ncr_containment', ['view', 'create', 'edit', 'verify'])
('quality', 'ncr_disposition', ['view', 'create', 'edit', 'approve', 'execute'])
('quality', 'quality_holds', ['view', 'create'])
('quality', 'ncr_reports', ['view', 'export'])
```

### 5. CAPA Owner
CAPA management and implementation.
```
('quality', 'dashboard', 'view')
('quality', 'capa', ['view', 'create', 'edit', 'verify', 'close'])
('quality', 'capa_actions', ['view', 'create', 'edit', 'complete'])
('quality', 'capa_effectiveness', ['view', 'create', 'edit', 'approve', 'close'])
('quality', 'capa_reports', ['view', 'export'])
```

### 6. Audit Manager
Audit program and finding management.
```
('quality', 'dashboard', 'view')
('quality', 'audits', ['view', 'create', 'edit', 'approve', 'execute', 'close', 'cancel'])
('quality', 'audit_programs', ['view', 'create', 'edit', 'manage'])
('quality', 'audit_checklists', ['view', 'create', 'edit', 'manage'])
('quality', 'audit_findings', ['view', 'create', 'edit', 'verify', 'close'])
('quality', 'audit_finding_actions', ['view', 'create', 'edit', 'complete'])
('quality', 'audit_reports', ['view', 'export'])
```

### 7. Supplier Quality Reviewer
Supplier quality management.
```
('quality', 'dashboard', 'view')
('quality', 'supplier_quality', ['view', 'create', 'edit', 'approve', 'block', 'unblock'])
('quality', 'supplier_scorecards', ['view', 'create', 'edit', 'export'])
('quality', 'supplier_ncr', ['view', 'create', 'edit', 'resolve'])
('quality', 'supplier_capa', ['view', 'create', 'edit', 'resolve'])
('quality', 'supplier_quality_reports', ['view', 'export'])
```

### 8. Compliance Reviewer
Quality compliance and regulatory.
```
('quality', 'dashboard', 'view')
('quality', 'compliance', ['view', 'create', 'edit', 'approve', 'export', 'manage'])
('quality', 'quality_documents', ['view', 'create', 'edit', 'approve', 'publish'])
('quality', 'controlled_docs', ['view', 'create', 'edit', 'approve', 'release'])
('quality', 'certifications', ['view', 'create', 'edit', 'approve', 'manage'])
('quality', 'quality_risks', ['view', 'create', 'edit', 'mitigate', 'manage'])
('quality', 'risk_assessment', ['view', 'create', 'edit', 'approve', 'manage'])
('quality', 'critical_control_points', ['view', 'create', 'edit', 'manage'])
('quality', 'escalation_rules', ['view', 'create', 'edit', 'manage'])
('quality', 'compliance_reports', ['view', 'export'])
```

### 9. Operations Viewer
Read-only quality operations.
```
('quality', 'dashboard', 'view')
('quality', 'inspections', 'view')
('quality', 'ncr', 'view')
('quality', 'audits', 'view')
('quality', 'audit_findings', 'view')
('quality', 'reports', 'view')
```

### 10. Executive Viewer
Executive quality dashboard access.
```
('quality', 'dashboard', 'view')
('quality', 'executive_dashboard', 'view')
('quality', 'reports', 'view')
('quality', 'inspection_reports', 'view')
('quality', 'ncr_reports', 'view')
('quality', 'capa_reports', 'view')
('quality', 'supplier_quality_reports', 'view')
('quality', 'compliance_reports', 'view')
```

## Branch/Entity Level Access

Quality data supports branch-level access control:
- Users can be scoped to specific branches
- Data filtering by user's assigned branches
- Cross-branch visibility for admin roles

## Audit Trail

All quality changes are logged with:
- User ID who made the change
- Timestamp of change
- Old and new values
- Entity type and ID
- Action type (CREATE, UPDATE, DELETE, STATUS_CHANGE, etc.)

## Permission Enforcement

Permissions are enforced at multiple levels:
1. **Route level** - `@require_quality_permission('action')` decorator
2. **Template level** - `{% if has_permission('quality', 'resource', 'action') %}`
3. **API level** - Permission check before data access
4. **Database level** - Optional row-level filtering by scope

## Flow Integration

Quality notifications respect permission boundaries:
- Notifications sent only to relevant users
- Severity-based routing
- Escalation paths configurable per role
