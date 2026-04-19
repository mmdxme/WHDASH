# UI Component System

## MMDx Enterprise Component Library

This document describes the reusable UI component system for the MMDx Enterprise Platform.

---

## 1. Overview

The component system is built on a foundation of:
- **CSS Design Tokens** — Enterprise design system variables
- **Jinja2 Templates** — Reusable HTML partials with context passing
- **CSS Utility Classes** — Tailwind utilities + custom component styles
- **Vanilla JavaScript** — Minimal, targeted interactivity

---

## 2. Component Categories

### 2.1 Display Components

| Component | Purpose | File |
|-----------|---------|------|
| Stat Card | KPI display with icon, value, trend indicator | `_stat_card.html` |
| Badge | Status pills, labels, category tags | `_badge.html` |
| Progress | Linear and circular progress indicators | `_progress.html` |
| Empty State | No-data placeholder with optional action | `_empty_state.html` |
| Skeleton | Loading placeholder with animation | `_skeleton.html` |

### 2.2 Navigation Components

| Component | Purpose | File |
|-----------|---------|------|
| Page Header | Title, subtitle, breadcrumbs, actions | `_page_header.html` |
| Breadcrumb | Navigation trail with links | `_breadcrumb.html` |
| Tabs | Horizontal tab navigation | `_tabs.html` |
| Pagination | Page number controls | (inline in `_table.html`) |

### 2.3 Data Components

| Component | Purpose | File |
|-----------|---------|------|
| Table | Sortable table with actions | `_table.html` |
| Filter Panel | Search and filter form | `_filter_panel.html` |

### 2.4 Feedback Components

| Component | Purpose | File |
|-----------|---------|------|
| Alert | Success/warning/error/info messages | `_alert.html` |
| Modal | Dialog with header, body, footer | `_modal.html` |
| Toast | Temporary notification | (inline JS) |

### 2.5 Layout Components

| Component | Purpose | File |
|-----------|---------|------|
| Card | Container with header, body, footer | `.card` class |
| Glass Panel | Frosted glass background panel | `.glass-panel` class |
| Accordion | Collapsible content sections | `.accordion` class |

---

## 3. Component Details

### 3.1 Stat Card

**Purpose:** Display a single KPI with icon, value, trend, and label.

**Variables:**

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `card_icon` | string | `'fa-chart-line'` | Font Awesome icon class |
| `card_icon_bg` | string | `'bg-brand-500/10'` | Icon background class |
| `card_icon_color` | string | `'text-brand-400'` | Icon color class |
| `card_value` | string | `'0'` | The KPI value |
| `card_label` | string | `''` | Label text |
| `card_trend` | string | `''` | Trend indicator (e.g., '+12.5%') |
| `card_trend_type` | string | `'up'` | `'up'` or `'down'` |
| `card_subtitle` | string | `''` | Additional context |
| `card_extra` | string | `''` | Extra content slot |

**Example:**

```jinja2
{% include 'components/_stat_card.html' with context %}
{% set card_icon = 'fa-truck' %}
{% set card_icon_bg = 'bg-emerald-500/10' %}
{% set card_icon_color = 'text-emerald-400' %}
{% set card_value = '1,234' %}
{% set card_label = 'Total Shipments' %}
{% set card_trend = '+12.5%' %}
{% set card_trend_type = 'up' %}
{% set card_subtitle = 'vs last month' %}
```

**Output:**

```html
<div class="stat-card group">
    <div class="flex items-start justify-between mb-4">
        <div class="stat-card-icon bg-emerald-500/10">
            <i class="fa-solid fa-truck text-emerald-400 text-xl"></i>
        </div>
        <span class="stat-card-trend up">
            <i class="fa-solid fa-arrow-up text-[10px]"></i>
            +12.5%
        </span>
    </div>
    <div class="space-y-1">
        <div class="text-3xl font-extrabold text-white tracking-tight">1,234</div>
        <div class="text-sm font-semibold text-slate-300">Total Shipments</div>
        <div class="text-xs text-slate-500">vs last month</div>
    </div>
</div>
```

---

### 3.2 Badge

**Purpose:** Display status pills with semantic colors.

**Variables:**

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `badge_text` | string | `''` | Badge label |
| `badge_type` | string | `'neutral'` | Color type |
| `badge_icon` | string | `''` | Optional icon class |
| `badge_size` | string | `'md'` | `'sm'` or `'md'` |

**Color Types:**
- `primary` — Brand blue
- `success` — Green
- `warning` — Amber
- `danger` — Red
- `info` — Cyan
- `neutral` — Gray

**Example:**

```jinja2
{% include 'components/_badge.html' with context %}
{% set badge_text = 'Active' %}
{% set badge_type = 'success' %}
{% set badge_icon = 'fa-check' %}
```

---

### 3.3 Table

**Purpose:** Display tabular data with sorting, selection, and pagination.

**Variables:**

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `table_id` | string | `'enterpriseTable'` | Unique table ID |
| `table_headers` | array | `[]` | Column definitions |
| `table_rows` | array | `[]` | Row data |
| `table_sort_key` | string | `''` | Currently sorted column |
| `table_sort_dir` | string | `'asc'` | Sort direction |
| `table_actions` | array | `[]` | Row action buttons |
| `table_empty_message` | string | `'No records found'` | Empty state text |
| `table_pagination` | dict | `''` | Pagination data |

**Header Definition:**

```jinja2
{% set table_headers = [
    {'key': 'name', 'label': 'Name', 'sortable': true},
    {'key': 'status', 'label': 'Status'},
    {'key': 'created', 'label': 'Created', 'class': 'text-right'}
] %}
```

**Row Action Definition:**

```jinja2
{% set table_actions = [
    {'icon': 'fa-eye', 'url': '/view/{id}', 'label': 'View'},
    {'icon': 'fa-edit', 'url': '/edit/{id}', 'label': 'Edit'}
] %}
```

**Example:**

```jinja2
{% include 'components/_table.html' with context %}
{% set table_id = 'shipmentsTable' %}
{% set table_headers = table_headers %}
{% set table_rows = shipments %}
{% set table_actions = actions %}
```

---

### 3.4 Empty State

**Purpose:** Display when no data is available.

**Variables:**

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `empty_icon` | string | `'fa-inbox'` | Icon class |
| `empty_title` | string | `'No data available'` | Title text |
| `empty_description` | string | `''` | Description text |
| `empty_action_label` | string | `''` | CTA button label |
| `empty_action_url` | string | `'#'` | CTA button URL |
| `empty_action_icon` | string | `'fa-plus'` | CTA button icon |

**Example:**

```jinja2
{% include 'components/_empty_state.html' with context %}
{% set empty_icon = 'fa-truck' %}
{% set empty_title = 'No shipments yet' %}
{% set empty_description = 'Create your first shipment to start tracking deliveries' %}
{% set empty_action_label = 'Create Shipment' %}
{% set empty_action_url = '/shipments/new' %}
```

---

### 3.5 Page Header

**Purpose:** Consistent page headers with navigation.

**Variables:**

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `page_title` | string | `''` | Main title |
| `page_subtitle` | string | `''` | Subtitle/description |
| `page_icon` | string | `''` | Icon class |
| `breadcrumbs` | array | `[]` | Navigation path |
| `page_actions` | string | `''` | HTML for action buttons |

**Breadcrumb Definition:**

```jinja2
{% set breadcrumbs = [
    {'label': 'Home', 'url': '/'},
    {'label': 'Logistics', 'url': '/logistics'},
    {'label': 'Shipments'}
] %}
```

**Example:**

```jinja2
{% include 'components/_page_header.html' with context %}
{% set page_title = 'Shipments' %}
{% set page_subtitle = 'Manage delivery shipments across all branches' %}
{% set page_icon = 'fa-truck' %}
{% set breadcrumbs = crumbs %}
{% set page_actions = '<a href="/shipments/new" class="btn btn-primary"><i class="fa-solid fa-plus"></i> New Shipment</a>' %}
```

---

### 3.6 Filter Panel

**Purpose:** Consistent search and filter forms for list pages.

**Variables:**

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `filter_action` | string | `'#'` | Form action URL |
| `filter_method` | string | `'GET'` | Form method |
| `filter_fields` | array | `[]` | Field definitions |
| `filter_show_reset` | bool | `true` | Show reset button |
| `filter_reset_url` | string | `'#'` | Reset URL |

**Field Definition:**

```jinja2
{% set filter_fields = [
    {'name': 'q', 'label': 'Search', 'type': 'text', 'placeholder': 'Search...', 'icon': 'fa-search'},
    {'name': 'status', 'label': 'Status', 'type': 'select', 'options': status_options},
    {'name': 'date_range', 'label': 'Date Range', 'type': 'daterange'}
] %}
```

**Field Types:**
- `text` — Text input
- `select` — Dropdown select
- `date` — Single date picker
- `daterange` — From/to date range
- `checkbox` — Single checkbox

---

### 3.7 Alert

**Purpose:** Display feedback messages.

**Variables:**

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `alert_type` | string | `'info'` | Alert type |
| `alert_message` | string | `''` | Message content |
| `alert_icon` | string | `''` | Custom icon |
| `alert_dismissible` | bool | `true` | Show dismiss button |
| `alert_title` | string | `''` | Optional title |

**Alert Types:**
- `success` — Green with check icon
- `warning` — Amber with warning icon
- `danger` / `error` — Red with X icon
- `info` — Blue with info icon

---

### 3.8 Skeleton

**Purpose:** Loading placeholder while content loads.

**Variables:**

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `skeleton_type` | string | `'card'` | Skeleton layout |
| `skeleton_count` | int | `1` | Number of items |

**Skeleton Types:**
- `card` — Card-shaped placeholder grid
- `table` — Table row placeholder
- `list` — List item placeholder
- `text` — Text block placeholder

---

## 4. CSS Classes Reference

### 4.1 Display Classes

| Class | Purpose |
|-------|---------|
| `.stat-card` | KPI card container |
| `.stat-card-icon` | Icon wrapper (48x48) |
| `.stat-card-trend` | Trend indicator pill |
| `.badge` | Base badge |
| `.badge-success` | Green badge |
| `.badge-danger` | Red badge |
| `.progress` | Linear progress bar |
| `.progress-bar` | Progress fill |
| `.empty-state` | Empty state container |
| `.empty-state-icon` | Icon circle (80x80) |

### 4.2 Navigation Classes

| Class | Purpose |
|-------|---------|
| `.page-header` | Page header wrapper |
| `.breadcrumb` | Breadcrumb container |
| `.breadcrumb-item` | Individual crumb |
| `.tab-item` | Tab button |

### 4.3 Form Classes

| Class | Purpose |
|-------|---------|
| `.form-group` | Field container |
| `.form-label` | Field label |
| `.form-input` | Text input |
| `.form-input-error` | Error input state |
| `.form-help` | Helper text |
| `.form-error` | Error message |
| `.form-select` | Select dropdown |
| `.form-check` | Checkbox container |

### 4.4 Layout Classes

| Class | Purpose |
|-------|---------|
| `.card` | Card container |
| `.card-header` | Card header section |
| `.card-body` | Card content section |
| `.card-footer` | Card footer section |
| `.glass-panel` | Frosted glass panel |
| `.accordion` | Accordion container |
| `.accordion-item` | Accordion section |

---

## 5. JavaScript Functions

### 5.1 Table Functions

```javascript
// Sort table by column
function sortTable(tableId, columnKey) { ... }

// Navigate to page
function goToPage(pageNum) { ... }

// Select all visible rows
function selectAllVisibleRows() { ... }

// Clear row selection
function clearSelectedRows() { ... }
```

### 5.2 Tab Functions

```javascript
// Switch active tab
function switchTab(tabId) { ... }
```

### 5.3 Modal Functions

```javascript
// Open modal by ID
function openModal{myModal}() { ... }

// Close modal by ID
function closeModal{myModal}() { ... }
```

### 5.4 Alert Functions

```javascript
// Dismiss alert by ID
function dismissAlert(alertId) { ... }
```

---

## 6. Usage Guidelines

### 6.1 Always Include Context

```jinja2
{% include 'components/_stat_card.html' with context %}
```

### 6.2 Set Variables Before Include

```jinja2
{% set card_icon = 'fa-truck' %}
{% set card_value = shipment.count %}
{% include 'components/_stat_card.html' with context %}
```

### 6.3 Use Semantic Colors

Prefer semantic colors over arbitrary ones:
- Success/green for positive states
- Danger/red for errors/critical
- Warning/amber for attention needed
- Info/blue for informational

### 6.4 Provide Empty States

Always include empty states for list views:
- Clear message explaining no data
- Action to create first item (if applicable)

### 6.5 Use Loading Skeletons

Show skeletons while data loads:
- Match the shape of actual content
- Use appropriate count for viewport

---

*Document Version: 1.0*
*Last Updated: April 18, 2026*
