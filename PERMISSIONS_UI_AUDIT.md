# Permissions UI Audit Report - WHDASH

**Date:** Tuesday April 14, 2026  
**Application:** WHDASH Enterprise Application  
**Scope:** RBAC system and UI permission enforcement

---

## Permission System Architecture

### Files
- **Main:** `permissions.py` (~1300 lines)
- **Database:** `role_permissions` table
- **Legacy:** `roles` table with flags (`can_edit_stock`, `can_manage_users`)

### Permission Structure
```
Format: module.resource.action
Example: hr.employees.view

Modules: 28 modules
Resources per module: 5-20 resources
Actions per resource: view, create, edit, delete, approve, etc.
```

---

## Permission Modules

| Module | Key | Permissions Count |
|--------|-----|-----------------|
| HR | hr | 16 resources |
| WMS | wms | 16 resources |
| Finance | finance | 16 resources |
| Sales | sales | 16 resources |
| CRM | crm | 10 resources |
| Marketing | marketing | 12 resources |
| Procurement | procurement | 16 resources |
| Quality | quality | 10 resources |
| Maintenance | maintenance | 16 resources |
| Assets | assets | 16 resources |
| Workflow | workflow | 16 resources |
| Documents | documents | 20 resources |
| Reports | reports | 16 resources |
| E-commerce | ecommerce | 14 resources |
| API Gateway | api_gateway | 20 resources |
| BI | bi | 10 resources |
| Forms | forms | 12 resources |
| Tasks | tasks | 6 resources |
| Quick Tools | quicktools | 8 resources |
| Platform | platform | 8 resources |
| Flow | flow | 20 resources |

---

## Role Definitions

| Role | Description | Access Level |
|------|-------------|--------------|
| Global Admin | Full system access | All modules |
| HR Manager | HR department head | HR + basic |
| Warehouse Manager | Inventory/WMS lead | WMS + basic |
| Procurement Manager | Purchasing lead | Procurement + basic |
| Quality Manager | QA department head | Quality + basic |
| Sales Manager | Sales department head | Sales + basic |
| Logistics Manager | Fleet/dispatch lead | Logistics + basic |
| Planner | Demand planning | Planning + basic |
| Marketing Manager | Marketing lead | Marketing + basic |
| Employee | Basic staff | Limited access |
| Viewer | Read-only | All views, no edit |

---

## Permission Decorators

### In Routes
```python
@require_login          # Requires authentication
@require_permission    # Requires specific permission
admin_required         # Admin-only pages
stock_admin_required    # Stock management access
```

### In Templates
```html
{% if user_has_permission('hr', 'employees', 'view') %}
    <!-- Show HR section -->
{% endif %}
```

---

## UI Permission Enforcement

### Menu Visibility
- Menus filtered by `get_main_menu()` based on user permissions
- Only visible items are those user has at least `view` permission

### Button Visibility
| Pattern | Example |
|---------|---------|
| `{% if user_has_permission(...) %}` | Shows/hides buttons |
| `{% if can_edit %}` | Legacy pattern check |

### Page Access
- Routes use `@require_permission` decorator
- Unauthorized access → redirect to index with flash message

---

## Issues Found

### 1. Legacy Permission Flags
The system still uses legacy flags alongside RBAC:
```python
session['can_edit_stock'] = bool(role['can_edit_stock'])
session['can_manage_users'] = bool(role['can_manage_users'])
```

These are session-based and not module-specific.

### 2. Permission Check Patterns
Mixed patterns found:
```python
# Legacy (still in use)
if not session.get('can_manage_users'):
    flash("Access Denied")
    return redirect(url_for('index'))

# Modern RBAC
if not user_has_permission(user_id, 'module', 'resource', 'action'):
    flash("Access Denied")
    return redirect(url_for('index'))
```

### 3. UI Visibility vs Enforcement
- Menu items hidden based on permissions ✅
- Page routes protected ✅
- Action buttons need verification ⚠️

---

## Recommended Permission UI Patterns

### Correct Template Pattern
```html
{% if user_has_permission('hr', 'employees', 'view') %}
    <a href="{{ url_for('hr.employees') }}">Employees</a>
{% endif %}

{% if user_has_permission('hr', 'employees', 'create') %}
    <a href="{{ url_for('hr.employees_new') }}">Add Employee</a>
{% endif %}

{% if user_has_permission('hr', 'employees', 'delete') %}
    <button onclick="deleteEmployee()">Delete</button>
{% endif %}
```

### Correct Route Pattern
```python
@app.route('/hr/employees/delete/<int:id>', methods=['POST'])
@require_login
def hr_employees_delete(id):
    if not user_has_permission(session['user_id'], 'hr', 'employees', 'delete'):
        flash("You don't have permission to delete employees.")
        return redirect(url_for('hr.employees'))
    # Proceed with deletion
```

---

## Testing Checklist

### Admin User
- [ ] Can access all pages
- [ ] Can see all menus
- [ ] Can perform all actions
- [ ] Can view all reports

### Module Manager (e.g., HR Manager)
- [ ] Can access HR module
- [ ] Can see HR menu items
- [ ] Cannot access other module admin pages
- [ ] Cannot modify users/settings (specific admin functions)

### Employee
- [ ] Can access dashboard
- [ ] Can view assigned tasks
- [ ] Cannot access admin functions
- [ ] Cannot view sensitive reports

### Viewer
- [ ] Can view all pages
- [ ] Cannot see create/edit/delete buttons
- [ ] Cannot perform actions
- [ ] Cannot export sensitive data

---

## Files Reviewed

| File | Permissions | Status |
|------|-------------|--------|
| app.py | @admin_required, @stock_admin_required | ✅ Working |
| hr_routes.py | Permission decorators | ✅ Working |
| wms_routes.py | Permission decorators | ✅ Working |
| workflow_routes.py | Permission decorators | ✅ Working |
| quality_routes.py | Permission decorators | ✅ Working |
| navigation.py | Menu filtering | ✅ Working |
| templates/ | user_has_permission() calls | ⚠️ Mixed |

---

## Recommendations

### Immediate
1. Audit all template permission checks for consistency
2. Ensure all destructive actions have server-side permission checks
3. Add permission comments to complex routes

### Long-term
1. Migrate all legacy permission checks to RBAC
2. Add permission audit logging
3. Create permission test suite
4. Document permission requirements per role

---

**Report Date:** 2026-04-14  
**Status:** Permission system operational, UI enforcement needs verification
