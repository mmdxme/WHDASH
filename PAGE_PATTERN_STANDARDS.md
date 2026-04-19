# MMDx Page Pattern Standards

## Standards for Building Consistent Module Pages

This document defines the standard patterns for building pages across all MMDx modules to ensure consistency and cohesion.

---

## 1. Page Type Templates

### 1.1 Dashboard Page

**Purpose:** Module overview with KPIs and quick stats

**URL Pattern:** `/<module>/dashboard` or `/<module>`

**Template Location:** `templates/<module>/dashboard.html`

**Structure:**

```jinja2
{% extends "base.html" %}

{% block content %}
<div class="page-content fade-in">
    
    {# === PAGE HEADER === #}
    {% include 'components/_page_header.html' with context %}
    {% set page_title = module.name %}
    {% set page_subtitle = module.description %}
    {% set page_icon = module.icon %}
    {% set breadcrumbs = module.breadcrumbs %}
    
    {# === DATE RANGE (if applicable) === #}
    <div class="flex justify-end mb-6">
        <div class="flex items-center gap-3">
            <input type="date" class="form-input" value="{{ start_date }}">
            <span class="text-slate-500">—</span>
            <input type="date" class="form-input" value="{{ end_date }}">
            <button class="btn btn-primary btn-sm">
                <i class="fa-solid fa-refresh mr-2"></i>Refresh
            </button>
        </div>
    </div>
    
    {# === KPI CARDS === #}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {% for kpi in kpis %}
        {% include 'components/_stat_card.html' with context %}
        {% set card_icon = kpi.icon %}
        {% set card_value = kpi.value %}
        {% set card_label = kpi.label %}
        {% set card_trend = kpi.trend %}
        {% set card_trend_type = kpi.trend_type %}
        {% endinclude %}
        {% endfor %}
    </div>
    
    {# === RECENT ACTIVITY / CHARTS === #}
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Chart panels -->
        <!-- Activity feed -->
    </div>
    
</div>
{% endblock %}
```

---

### 1.2 List Page

**Purpose:** Paginated list with filtering and actions

**URL Pattern:** `/<module>/list` or `/<module>`

**Template Location:** `templates/<module>/list.html`

**Structure:**

```jinja2
{% extends "base.html" %}

{% block content %}
<div class="page-content fade-in">
    
    {# === PAGE HEADER === #}
    {% include 'components/_page_header.html' with context %}
    {% set page_actions = '
        <a href="/' + module_slug + '/new" class="btn btn-primary">
            <i class="fa-solid fa-plus mr-2"></i>New ' + module.name + '
        </a>
    ' %}
    
    {# === FILTER PANEL === #}
    {% include 'components/_filter_panel.html' with context %}
    {% set filter_action = url_for("' + module_slug + '_list") %}
    {% set filter_fields = filter_definition %}
    
    {# === TABLE === #}
    {% include 'components/_table.html' with context %}
    {% set table_id = module_slug + 'Table' %}
    {% set table_headers = column_definitions %}
    {% set table_rows = records %}
    {% set table_actions = action_buttons %}
    {% set table_pagination = pagination %}
    
</div>
{% endblock %}
```

---

### 1.3 Detail Page

**Purpose:** Show single record with full details

**URL Pattern:** `/<module>/detail/<id>`

**Template Location:** `templates/<module>/detail.html`

**Structure:**

```jinja2
{% extends "base.html" %}

{% block content %}
<div class="page-content fade-in">
    
    {# === BACK BUTTON & HEADER === #}
    <div class="flex items-center gap-4 mb-6">
        <a href="{{ url_for("' + module_slug + '_list') }}" class="btn btn-secondary btn-icon">
            <i class="fa-solid fa-arrow-left"></i>
        </a>
        {% include 'components/_page_header.html' with context %}
        {% set page_title = record.name %}
        {% set page_actions = '
            <a href="/' + module_slug + '/edit/' + record.id + '" class="btn btn-secondary">
                <i class="fa-solid fa-edit mr-2"></i>Edit
            </a>
        ' %}
    </div>
    
    {# === TABS === #}
    {% include 'components/_tabs.html' with context %}
    {% set tabs = [
        {'id': 'overview', 'label': 'Overview', 'active': true},
        {'id': 'details', 'label': 'Details'},
        {'id': 'history', 'label': 'History'},
        {'id': 'documents', 'label': 'Documents'}
    ] %}
    
    {# === TAB CONTENT === #}
    <div class="mt-6">
        
        <div data-tab-content="overview">
            {# === OVERVIEW GRID === #}
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <!-- Info cards -->
            </div>
        </div>
        
        <div data-tab-content="details" class="hidden">
            <!-- Detailed fields -->
        </div>
        
    </div>
    
</div>
{% endblock %}
```

---

### 1.4 Form Page (Create/Edit)

**Purpose:** Create new or edit existing records

**URL Pattern:** 
- Create: `/<module>/new`
- Edit: `/<module>/edit/<id>`

**Template Location:** `templates/<module>/form.html`

**Structure:**

```jinja2
{% extends "base.html" %}

{% block content %}
<div class="page-content fade-in max-w-4xl mx-auto">
    
    {# === PAGE HEADER === #}
    {% include 'components/_page_header.html' with context %}
    {% set page_title = 'Edit ' + record.name if is_edit else 'Create New ' + module.name %}
    {% set page_subtitle = form_description %}
    
    {# === ALERTS === #}
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            <div class="mb-6 space-y-3">
                {% for category, message in messages %}
                {% include 'components/_alert.html' with context %}
                {% set alert_type = category %}
                {% set alert_message = message %}
                {% endinclude %}
                {% endfor %}
            </div>
        {% endif %}
    {% endwith %}
    
    {# === FORM === #}
    <form method="POST" action="{{ form_action }}" class="glass-panel p-6">
        
        {# === FORM SECTIONS === #}
        <div class="space-y-8">
            
            {# --- Section 1: Basic Info --- #}
            <div class="form-section">
                <h3 class="text-lg font-bold text-white mb-4">Basic Information</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                    
                    <div class="form-group">
                        <label class="form-label">Name *</label>
                        <input type="text" name="name" class="form-input" value="{{ record.name }}" required>
                    </div>
                    
                    <div class="form-group">
                        <label class="form-label">Status</label>
                        <select name="status" class="form-input form-select">
                            <option value="active" {% if record.status == 'active' %}selected{% endif %}>Active</option>
                            <option value="inactive" {% if record.status == 'inactive' %}selected{% endif %}>Inactive</option>
                        </select>
                    </div>
                    
                </div>
            </div>
            
            {# --- Section 2: Additional Info --- #}
            <div class="form-section">
                <h3 class="text-lg font-bold text-white mb-4">Additional Details</h3>
                <div class="space-y-4">
                    <!-- Fields -->
                </div>
            </div>
            
        </div>
        
        {# === FORM ACTIONS === #}
        <div class="flex items-center justify-end gap-3 mt-8 pt-6 border-t border-white/10">
            <a href="{{ cancel_url }}" class="btn btn-secondary">Cancel</a>
            <button type="submit" class="btn btn-primary">
                <i class="fa-solid fa-check mr-2"></i>{{ 'Update' if is_edit else 'Create' }}
            </button>
        </div>
        
    </form>
    
</div>
{% endblock %}
```

---

### 1.5 Reports Page

**Purpose:** Index page for module reports

**URL Pattern:** `/<module>/reports`

**Template Location:** `templates/<module>/reports.html`

**Structure:**

```jinja2
{% extends "base.html" %}

{% block content %}
<div class="page-content fade-in">
    
    {% include 'components/_page_header.html' with context %}
    {% set page_title = 'Reports' %}
    {% set page_subtitle = module.name + ' analytics and exports' %}
    
    {# === REPORT CARDS GRID === #}
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
        {% for report in reports %}
        <a href="{{ report.url }}" class="card hover:border-brand-500/30 transition-all group">
            <div class="card-body">
                <div class="w-12 h-12 rounded-xl bg-brand-500/10 flex items-center justify-center mb-4">
                    <i class="fa-solid {{ report.icon }} text-brand-400 text-xl"></i>
                </div>
                <h3 class="font-bold text-white mb-2">{{ report.title }}</h3>
                <p class="text-sm text-slate-400">{{ report.description }}</p>
            </div>
            <div class="card-footer flex items-center justify-between">
                <span class="text-xs text-slate-500">{{ report.type }}</span>
                <i class="fa-solid fa-arrow-right text-slate-500 group-hover:text-brand-400 transition-colors"></i>
            </div>
        </a>
        {% endfor %}
        
    </div>
    
</div>
{% endblock %}
```

---

## 2. Common Patterns

### 2.1 Breadcrumb Setup

```jinja2
{% set breadcrumbs = [
    {'label': 'Home', 'url': url_for('index')},
    {'label': module.name, 'url': url_for(module.list_route)},
    {'label': 'Detail', 'url': '#'}
] %}
```

### 2.2 Filter Field Definition

```jinja2
{% set filter_fields = [
    {'name': 'q', 'label': 'Search', 'type': 'text', 'placeholder': 'Search by name or ID...', 'icon': 'fa-search'},
    {'name': 'status', 'label': 'Status', 'type': 'select', 'options': status_options},
    {'name': 'date_from', 'label': 'Date From', 'type': 'date'},
    {'name': 'date_to', 'label': 'Date To', 'type': 'date'}
] %}
```

### 2.3 Table Header Definition

```jinja2
{% set table_headers = [
    {'key': 'id', 'label': 'ID', 'sortable': true, 'class': 'w-20'},
    {'key': 'name', 'label': 'Name', 'sortable': true},
    {'key': 'status', 'label': 'Status', 'render': status_badge},
    {'key': 'created_at', 'label': 'Created', 'sortable': true},
    {'key': 'actions', 'label': '', 'class': 'w-24'}
] %}
```

### 2.4 Row Action Buttons

```jinja2
{% set table_actions = [
    {'icon': 'fa-eye', 'url': url_for('module.detail', id='') + '{id}', 'label': 'View'},
    {'icon': 'fa-edit', 'url': url_for('module.edit', id='') + '{id}', 'label': 'Edit'},
    {'icon': 'fa-trash', 'url': url_for('module.delete', id='') + '{id}', 'label': 'Delete'}
] %}
```

### 2.5 Status Badge Renderer

```jinja2
{% macro status_badge(status, record) %}
{% include 'components/_badge.html' with context %}
{% if status == 'active' %}
{% set badge_type = 'success' %}
{% set badge_text = 'Active' %}
{% elif status == 'pending' %}
{% set badge_type = 'warning' %}
{% set badge_text = 'Pending' %}
{% else %}
{% set badge_type = 'neutral' %}
{% set badge_text = 'Inactive' %}
{% endif %}
{% endmacro %}
```

---

## 3. Spacing & Layout Standards

### 3.1 Section Spacing

| Context | Spacing |
|---------|---------|
| Between major sections | `mb-8` or `gap-8` |
| Between cards in grid | `gap-4` or `gap-6` |
| Inside card body | `p-5` or `p-6` |
| Between form fields | `space-y-4` |
| Between page sections | `mb-6` |

### 3.2 Grid Patterns

| Use Case | Grid |
|----------|------|
| KPI cards | `grid-cols-1 md:grid-cols-2 lg:grid-cols-4` |
| Two-column layout | `grid-cols-1 lg:grid-cols-2` |
| Three-column layout | `grid-cols-1 md:grid-cols-2 lg:grid-cols-3` |
| Form fields | `grid-cols-1 md:grid-cols-2` |

### 3.3 Responsive Behavior

```jinja2
{# Mobile: Stack vertically #}
{# Tablet: 2 columns #}
{# Desktop: 3-4 columns or full width #}
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
```

---

## 4. Form Standards

### 4.1 Required Field Indicator

```jinja2
<label class="form-label form-label-required">Field Label</label>
```

### 4.2 Field Help Text

```jinja2
<div class="form-group">
    <label class="form-label">Email Address</label>
    <input type="email" name="email" class="form-input" value="{{ email }}">
    <span class="form-help">We'll never share your email</span>
</div>
```

### 4.3 Field Error Display

```jinja2
<div class="form-group">
    <label class="form-label">Username</label>
    <input type="text" name="username" class="form-input form-input-error" value="{{ username }}">
    <span class="form-error">
        <i class="fa-solid fa-exclamation-circle"></i>
        Username is already taken
    </span>
</div>
```

### 4.4 Sticky Form Actions

```jinja2
<div class="glass-panel p-6">
    <form class="space-y-6">
        <!-- Form fields -->
    </form>
    <div class="sticky bottom-0 bg-slate-900/95 backdrop-blur border-t border-white/10 mt-6 -mx-6 -mb-6 p-6 flex justify-end gap-3">
        <a href="{{ cancel_url }}" class="btn btn-secondary">Cancel</a>
        <button type="submit" class="btn btn-primary">Save Changes</button>
    </div>
</div>
```

---

## 5. Table Standards

### 5.1 Column Width Guidelines

| Column Type | Width | Notes |
|------------|-------|-------|
| ID | 60-80px | Fixed, narrow |
| Actions | 80-100px | Fixed, always rightmost |
| Status | 100-120px | Fixed |
| Dates | 120-150px | Fixed or flexible |
| Name/Title | flex-1 | Takes remaining space |
| Email | 200-250px | Fixed |

### 5.2 Sticky Header Table

```html
<div class="table-container">
    <table class="enterprise-data-table">
        <thead class="sticky top-0 z-10">
            <!-- Headers -->
        </thead>
        <tbody>
            <!-- Rows -->
        </tbody>
    </table>
</div>
```

### 5.3 Row Selection

```jinja2
<td class="w-12">
    <input type="checkbox" class="table-checkbox" data-row-id="{{ row.id }}">
</td>
```

---

## 6. Empty State Standards

### 6.1 List Empty State

```jinja2
{% if records|length == 0 %}
{% include 'components/_empty_state.html' with context %}
{% set empty_icon = 'fa-folder-open' %}
{% set empty_title = 'No ' + module.name + ' found' %}
{% set empty_description = 'Get started by creating your first ' + module.name %}
{% set empty_action_label = 'Create ' + module.name %}
{% set empty_action_url = url_for(module.create_route) %}
{% endif %}
```

### 6.2 Search No Results

```jinja2
{% if filtered and records|length == 0 %}
{% include 'components/_empty_state.html' with context %}
{% set empty_icon = 'fa-search' %}
{% set empty_title = 'No results found' %}
{% set empty_description = 'Try adjusting your search or filter criteria' %}
{% set empty_action_label = 'Clear Filters' %}
{% set empty_action_url = url_for(module.list_route) %}
{% endif %}
```

---

## 7. Error Handling

### 7.1 Form Validation Errors

```jinja2
{% if errors %}
<div class="alert alert-danger mb-6">
    <i class="fa-solid fa-circle-exclamation"></i>
    <div>
        <strong>Please fix the following errors:</strong>
        <ul class="mt-2 list-disc list-inside">
            {% for field, message in errors.items() %}
            <li>{{ field }}: {{ message }}</li>
            {% endfor %}
        </ul>
    </div>
</div>
{% endif %}
```

### 7.2 API Error Display

```jinja2
{% if api_error %}
{% include 'components/_alert.html' with context %}
{% set alert_type = 'danger' %}
{% set alert_title = 'Error' %}
{% set alert_message = api_error %}
{% endif %}
```

---

## 8. Accessibility Standards

### 8.1 Form Labels

Always associate labels with inputs:

```jinja2
<label for="username" class="form-label">Username</label>
<input id="username" type="text" class="form-input" name="username">
```

### 8.2 Button Labels

```jinja2
<button class="btn btn-primary" title="Delete item" aria-label="Delete item">
    <i class="fa-solid fa-trash" aria-hidden="true"></i>
</button>
```

### 8.3 Table Headers

```jinja2
<th scope="col" aria-sort="{{ 'ascending' if sort_dir == 'asc' else 'descending' }}">
    <button onclick="sortTable('column')">Name</button>
</th>
```

---

*Document Version: 1.0*
*Last Updated: April 18, 2026*
