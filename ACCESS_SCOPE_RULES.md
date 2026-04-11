# MMDx Access Scope Rules
## Data Visibility and Record-Level Access Control

---

## Overview

Access scope rules define what data a user can see and manipulate based on their role, organizational assignment, and permission level. These rules complement action-based permissions (`module.resource.action`) with data visibility controls.

---

## Scope Types

| Scope Type | Code | Description |
|------------|------|-------------|
| **Global** | `global` | Access to all records across all companies/branches |
| **Company** | `company` | Access restricted to records within assigned company |
| **Branch** | `branch` | Access restricted to records within assigned branch |
| **Department** | `department` | Access restricted to records within assigned department |
| **Warehouse** | `warehouse` | Access restricted to records within assigned warehouse |
| **Regional** | `region` | Access restricted to records within assigned region |
| **Own Records** | `own` | Access only to records created by or assigned to the user |
| **Team** | `team` | Access to records of user's direct team members |
| **Assigned** | `assigned` | Access only to specifically assigned records |
| **None** | `none` | No direct record access (relies on cross-record visibility) |

---

## Module-Specific Scope Rules

### WMS / Warehouse Module

| Role | Inventory | Receipts | Shipments | Transfers | Adjustments | Reports |
|------|-----------|----------|-----------|-----------|-------------|---------|
| Warehouse Manager | Own Company | Own Company | Own Company | Own Company | Own Company | Own Company |
| Warehouse Supervisor | Own Warehouse | Own Warehouse | Own Warehouse | Own Warehouse | Own Warehouse | Own Warehouse |
| Warehouse Assistant | Own Warehouse | Own Warehouse | - | Own Warehouse | - | Own Warehouse |
| Warehouse Operator | Assigned Location | - | - | - | - | Assigned Location |

**Scope Details:**
- `Own Company` - All warehouses and locations belonging to user's company
- `Own Warehouse` - Only the specific warehouse assigned to the user's profile
- `Assigned Location` - Only warehouse locations explicitly assigned to the user

---

### Logistics Module

| Role | Trips | Routes | Vehicles | Drivers | Dispatch |
|------|-------|--------|----------|---------|----------|
| Logistics Manager | Own Region | Own Region | Own Region | Own Region | Own Region |
| Logistics Supervisor | Own Region | Own Region | Assigned | Assigned | Own Region |
| Logistics Assistant | Own Region | Own Region | - | - | - |
| Logistics Coordinator | Assigned Routes | Assigned Routes | Assigned | Assigned | Assigned |
| Logistics Driver | Assigned Trips | - | Assigned Vehicle | - | - |

**Scope Details:**
- `Own Region` - All operational records within the user's assigned geographical region
- `Assigned Routes` - Trips/routes explicitly assigned to the coordinator
- `Assigned Vehicle` - Vehicle explicitly assigned to the driver

---

### Procurement Module

| Role | Suppliers | Requisitions | RFQs | Quotations | Orders | Contracts |
|------|-----------|--------------|------|------------|--------|-----------|
| Procurement Manager | Own Company | Own Company | Own Company | Own Company | Own Company | Own Company |
| Procurement Supervisor | Own Company | Own Company | Own Company | Own Company | Own Company | Own Company |
| Procurement Assistant | Own Company | Own Company | Own Company | Own Company | - | - |
| Procurement Buyer | Own Company | Assigned/Own | Assigned/Own | Assigned/Own | Assigned/Own | - |
| Procurement Viewer | Own Company | Own Company | Own Company | Own Company | Own Company | Own Company |

**Scope Details:**
- `Own Company` - All procurement records within the user's company
- `Assigned/Own` - Only requisitions/RFQs created by the user or assigned to them

---

### Finance Module

| Role | Accounts | Journals | AR/AP | Budgets | Assets | Reports |
|------|----------|----------|-------|---------|--------|---------|
| Finance Manager | Own Company | Own Company | Own Company | Own Company | Own Company | Own Company |
| Finance Supervisor | Own Company | Own Company | Own Company | Own Company | Own Company | Own Company |
| Finance Assistant | Own Company | Own Company | Own Company | Own Company | - | - |
| Finance Accountant | Own Company | Own (by account) | Own (by account) | Own Company | Own Company | Own Company |
| Finance AP Clerk | Own Company | Own Company | AP Only | - | - | - |
| Finance AR Clerk | Own Company | Own Company | AR Only | - | - | - |
| Finance Viewer | Own Company | Own Company | Own Company | Own Company | Own Company | Own Company |
| Finance Auditor | Global | Global | Global | Global | Global | Global |

**Scope Details:**
- `Own Company` - All financial records within the user's company
- `Own (by account)` - Only journals/entries for accounts assigned to the accountant
- `AP Only` - Access only to accounts payable records
- `AR Only` - Access only to accounts receivable records
- `Global` - All financial records across all companies (auditors only)

---

### HR Module

| Role | Employees | Attendance | Leave | Payroll | Recruitment |
|------|-----------|------------|-------|---------|--------------|
| HR Manager | Own Company | Own Company | Own Company | Own Company | Own Company |
| HR Supervisor | Own Company | Own Department | Own Department | - | Own Company |
| HR Assistant | Own Company | Own Department | Own Department | - | Own Company |
| HR Officer | Own Company | Own Company | Own Company | - | - |
| Payroll Manager | Own Company | Own Company | Own Company | Own Company | - |
| Payroll Officer | Own Company | Own Company | Own Company | Own Company | - |
| HR Viewer | Own Company | Own Company | Own Company | - | - |
| Employee Self-Service | Own Record | Own Record | Own Record | - | - |

**Scope Details:**
- `Own Company` - All employee records within the user's company
- `Own Department` - Only employees within the user's department
- `Own Record` - Only the employee's own record (self-service)

**Sensitive Field Restrictions:**
- `Salary/Compensation` - Payroll Manager, HR Manager with payroll rights only
- `Bank Details` - Payroll Manager only
- `Performance Reviews` - Employee's direct manager and HR Manager only
- `Disciplinary Records` - HR Manager, Compliance Reviewer only

---

### Assets Module

| Role | Assets | Depreciation | Transfers | Disposals | Maintenance |
|------|--------|--------------|-----------|-----------|-------------|
| Asset Manager | Own Company | Own Company | Own Company | Own Company | Own Company |
| Asset Supervisor | Own Company | Own Company | Own Company | Own Company | Own Company |
| Asset Accountant | Own Company | Own Company | - | - | - |
| Asset Assistant | Own Company | - | Own Company | - | Own Company |
| Asset Operator | Own Company | - | - | - | Own Company |
| Asset Viewer | Own Company | Own Company | - | - | - |

---

### Maintenance Module

| Role | Equipment | Work Orders | PM Schedules | Technicians | Reports |
|------|-----------|--------------|--------------|-------------|---------|
| Maintenance Manager | Own Facility | Own Facility | Own Facility | Own Facility | Own Facility |
| Maintenance Supervisor | Own Facility | Own Facility | Own Facility | Own Facility | Own Facility |
| Maintenance Technician | Assigned | Assigned | - | - | - |
| Maintenance Planner | Own Facility | Own Facility | Own Facility | - | Own Facility |
| Maintenance Viewer | Own Facility | Own Facility | Own Facility | - | Own Facility |

**Scope Details:**
- `Own Facility` - All equipment and maintenance records for facilities assigned to user's company
- `Assigned` - Only work orders and equipment explicitly assigned to the technician

---

### Quality Module

| Role | Inspections | NCR | CAPA | Audits | Reports |
|------|-------------|-----|------|--------|---------|
| Quality Manager | Own Company | Own Company | Own Company | Own Company | Own Company |
| Quality Supervisor | Own Company | Own Company | Own Company | Own Company | Own Company |
| Quality Inspector | Assigned Area | - | - | - | - |
| Quality Auditor | Own Company | Own Company | Own Company | Own Company | Own Company |
| Quality Assistant | Own Company | Own Company | Own Company | Own Company | Own Company |
| Quality Viewer | Own Company | Own Company | Own Company | Own Company | Own Company |

**Scope Details:**
- `Assigned Area` - Only inspection records for the inspector's assigned area
- `Own Company` - All quality records within the user's company

---

### Sales Module

| Role | Customers | Quotations | Orders | Deliveries | Reports |
|------|-----------|------------|--------|------------|---------|
| Sales Manager | Own Company | Own Company | Own Company | Own Company | Own Company |
| Sales Supervisor | Own Company | Own Company | Own Company | Own Company | Own Company |
| Sales Assistant | Own Company | Own Company | Own Company | Own Company | Own Company |
| Sales Executive | Own Company | Own (by customer) | Own (by customer) | Own (by customer) | Own (by customer) |
| CRM Manager | Own Company | Own Company | Own Company | Own Company | Own Company |
| Sales Viewer | Own Company | Own Company | Own Company | Own Company | Own Company |

**Scope Details:**
- `Own (by customer)` - Only records for customers assigned to or owned by the executive
- `Own Company` - All sales records within the user's company

---

### Marketing Module

| Role | Campaigns | Leads | Content | Budgets | Reports |
|------|-----------|-------|---------|---------|---------|
| Marketing Manager | Own Company | Own Company | Own Company | Own Company | Own Company |
| Marketing Supervisor | Own Company | Own Company | Own Company | Own Company | Own Company |
| Marketing Assistant | Own Company | Own Company | Own Company | - | Own Company |
| Marketing Specialist | Own Company | Assigned/Own | Own | - | - |
| Content Manager | Own Company | - | Own Company | Own Company | Own Company |
| Marketing Viewer | Own Company | Own Company | Own Company | Own Company | Own Company |

**Scope Details:**
- `Assigned/Own` - Leads assigned to the specialist or created by them
- `Own` - Content created by the user

---

### Planning Module

| Role | Forecasts | Demand | Replenishment | Policies | Reports |
|------|-----------|--------|---------------|---------|---------|
| Planning Manager | Own Company | Own Company | Own Company | Own Company | Own Company |
| Planning Analyst | Own Company | Own Company | Own Company | Own Company | Own Company |
| Planning Assistant | Own Company | - | - | - | Own Company |
| Planning Viewer | Own Company | Own Company | Own Company | Own Company | Own Company |

---

### Workflow Module

| Role | Instances | Tasks | Delegations | Monitoring |
|------|-----------|-------|-------------|------------|
| Workflow Admin | Global | Global | Global | Global |
| Workflow Supervisor | Own Company | Own Company | Own Company | Own Company |
| Workflow User | Assigned | Assigned | - | - |
| Workflow Viewer | Own Company | Own Company | - | Own Company |

**Scope Details:**
- `Assigned` - Only workflow instances/tasks assigned to or created by the user
- `Global` - All workflow instances across all companies

---

### Documents Module

| Role | Files | Templates | Signatures | Access Control |
|------|-------|-----------|------------|----------------|
| Documents Manager | Own Company | Own Company | Own Company | Own Company |
| Documents Controller | Own Company | Own Company | Own Company | Own Company |
| Documents Assistant | Own Company | Own Company | Own Company | - |
| Documents User | Own Records | Own Records | Own Records | - |
| Documents Viewer | Own Company | Own Company | - | - |

**Scope Details:**
- `Own Records` - Only documents uploaded by or shared with the user
- `Own Company` - All documents within the user's company

**Document Classification Access:**
- `Public` - All authenticated users with document.view permission
- `Internal` - Users within the company
- `Confidential` - Explicitly assigned users or roles
- `Restricted` - Only users with explicit document-specific permission

---

### E-commerce Module

| Role | Channels | Orders | Inventory | Customers | Exceptions |
|------|----------|--------|-----------|-----------|------------|
| E-commerce Manager | Global | Global | Global | Global | Global |
| E-commerce Coordinator | Own Company | Own Company | Own Company | Own Company | Own Company |
| E-commerce Assistant | Own Company | Own Company | Own Company | Own Company | - |
| E-commerce Viewer | Own Company | Own Company | Own Company | Own Company | Own Company |

---

### API Gateway Module

| Role | Clients | Routes | Webhooks | Logs | Rate Limits |
|------|---------|--------|----------|------|-------------|
| API Gateway Admin | Global | Global | Global | Global | Global |
| API Manager | Global | Global | Global | Global | Global |
| API Support User | - | - | - | Global | - |
| API Viewer | Global | Global | - | Global | - |

---

### BI / Reports Module

| Role | Executive | Operational | Financial | Custom | Datasets |
|------|-----------|-------------|-----------|--------|----------|
| BI Manager | Own Company | Own Company | Own Company | Own Company | Global |
| BI Analyst | Own Company | Own Company | Own Company | Own Company | Own Company |
| BI Viewer | Own Company | Own Company | Own Company | - | - |
| Executive Viewer | Own Company | Own Company | Own Company | - | - |

---

### Admin / Platform Module

| Role | Users | Roles | Audit Logs | Settings |
|------|-------|-------|------------|----------|
| Super Admin | Global | Global | Global | Global |
| Global Admin | Global | Global | Global | Global |
| User & Role Admin | Global | Global | - | - |
| Audit Viewer | Global | - | Global | - |
| Platform Admin | - | - | - | Global |

---

## Cross-Module Scope Inheritance

Some modules inherit scope from others:

| Primary Module | Inherits Scope From | Notes |
|----------------|---------------------|-------|
| WMS Shipments | Logistics Deliveries | Shipment scope follows delivery region |
| Procurement Receipts | WMS Receipts | Receipt warehouse scope applies |
| Finance Journal | All Modules | Journals inherit scope from source transaction |
| Documents | All Modules | Document scope follows linked entity |

---

## Implementation Rules

### Record Filtering

When querying records, always apply scope filters:

```python
def get_scoped_records(user_id, module, resource):
    user_role = get_user_role(user_id)
    user_scope = get_user_scope(user_id, module)

    if user_scope == 'global':
        return get_all_records(module, resource)

    elif user_scope == 'company':
        company_id = get_user_company_id(user_id)
        return get_records_by_company(module, resource, company_id)

    elif user_scope == 'warehouse':
        warehouse_ids = get_user_warehouse_ids(user_id)
        return get_records_by_warehouses(module, resource, warehouse_ids)

    elif user_scope == 'assigned':
        return get_assigned_records(user_id, module, resource)

    elif user_scope == 'own':
        return get_user_created_records(user_id, module, resource)
```

### Scope Verification

Before allowing record manipulation, verify scope access:

```python
def can_access_record(user_id, module, resource, record_id):
    record = get_record(module, resource, record_id)
    if not record:
        return False

    user_scope = get_user_scope(user_id, module)
    user_role = get_user_role(user_id)

    if user_role.has_permission('*', '*', '*'):  # Global admin
        return True

    if user_scope == 'global':
        return True

    if user_scope == 'company':
        return record.company_id == get_user_company_id(user_id)

    if user_scope == 'warehouse':
        return record.warehouse_id in get_user_warehouse_ids(user_id)

    if user_scope == 'assigned':
        return is_record_assigned_to_user(record_id, user_id)

    if user_scope == 'own':
        return record.created_by == user_id

    return False
```

---

## Menu Visibility by Scope

Menus must be filtered based on user scope:

| Scope | Visible Menus |
|-------|---------------|
| Global | All menus the user has permissions for |
| Company | Company-scoped module menus |
| Warehouse | Warehouse-specific submenus only |
| Assigned | Only personally assigned task/item menus |
| Own | Only user's own records (self-service style) |

---

## Button/Action Visibility by Scope

| Action | Visibility Rule |
|--------|----------------|
| Edit | User has edit permission AND can_access_record for that specific record |
| Delete | User has delete permission AND record scope matches user scope |
| Approve | User has approve permission AND record is in user's approval queue |
| Export | User has export permission AND export scope matches user data scope |
| Assign | User has assign permission AND target user is within user's scope |
