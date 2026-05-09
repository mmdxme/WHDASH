# RTL Component Rules

This document provides specific rules for RTL behavior of each UI component type in WHDASH.

## Table of Contents
1. [Cards & Panels](#cards--panels)
2. [Tables](#tables)
3. [Forms & Inputs](#forms--inputs)
4. [Buttons & Actions](#buttons--actions)
5. [Navigation](#navigation)
6. [Modals & Drawers](#modals--drawers)
7. [Notifications & Alerts](#notifications--alerts)
8. [Dropdowns & Menus](#dropdowns--menus)
9. [Tabs & Accordions](#tabs--accordions)
10. [Pagination](#pagination)
11. [Breadcrumbs](#breadcrumbs)
12. [Badges & Tags](#badges--tags)
13. [Progress & Loading](#progress--loading)
14. [Charts & KPIs](#charts--kpis)
15. [Empty States](#empty-states)

---

## Cards & Panels

### Glass Panel
```css
[dir="rtl"] .glass-panel {
    text-align: right;
}
[dir="rtl"] .glass-panel .flex.items-center {
    flex-direction: row-reverse;
}
```

**Expected RTL behavior:**
- Content aligns to the right
- Internal flex containers reverse direction
- Icons appear on the right side of text

### KPI / Stat Card
```css
[dir="rtl"] .kpi-card {
    flex-direction: row-reverse;
}
[dir="rtl"] .kpi-card-body {
    align-items: flex-end;
}
[dir="rtl"] .kpi-indicator {
    right: auto;
    left: 1rem;
}
```

**Expected RTL behavior:**
- Indicator moves from right to left side
- Card content flips horizontally
- Trend badge and value stack correctly

### Insight Card
```css
[dir="rtl"] .insight-card {
    flex-direction: row-reverse;
}
```

### Dashboard Hero
```css
[dir="rtl"] .dashboard-hero {
    flex-direction: row-reverse;
}
[dir="rtl"] .dashboard-hero-content {
    flex-direction: row-reverse;
}
```

---

## Tables

### Basic Table Rules
```css
[dir="rtl"] table {
    direction: rtl;
}
[dir="rtl"] th,
[dir="rtl"] td {
    text-align: right;
}
```

**Critical Rule:** Numeric and code columns must NOT follow the default RTL table rule.

### Numeric/Code Columns (Must Stay LTR)
```css
[dir="rtl"] table th.numeric-col,
[dir="rtl"] table td.numeric-col,
[dir="rtl"] table th.code-col,
[dir="rtl"] table td.code-col {
    text-align: left !important;
    direction: ltr !important;
}
```

**When to use `numeric-col`:**
- Quantity columns
- Amount/currency columns
- Weight/dimension columns
- Percentage columns

**When to use `code-col`:**
- Item codes (SKU, part numbers)
- Barcode strings
- Invoice/order numbers
- Reference IDs

### Table Header
```css
[dir="rtl"] thead th {
    text-align: right;
}
```

### Table Actions Column
```css
[dir="rtl"] .table-actions {
    flex-direction: row-reverse;
}
```

### Sort Icon
```css
[dir="rtl"] .sort-icon {
    margin-left: 0.5rem;
    margin-right: 0;
}
```

### Filter Panel in Tables
```css
[dir="rtl"] .data-table-panel-header,
[dir="rtl"] .table-panel-header {
    flex-direction: row-reverse;
}
```

---

## Forms & Inputs

### General Input Rule
```css
[dir="rtl"] input[type="text"],
[dir="rtl"] textarea {
    direction: rtl;
    text-align: right;
}
```

### LTR Input Types (Automatic)
```css
[dir="rtl"] input[type="email"],
[dir="rtl"] input[type="tel"],
[dir="rtl"] input[type="url"],
[dir="rtl"] input[type="number"],
[dir="rtl"] input[type="password"],
[dir="rtl"] input[type="search"],
[dir="rtl"] input[type="date"],
[dir="rtl"] input[type="time"],
[dir="rtl"] input[type="datetime-local"] {
    direction: ltr;
    text-align: left;
}
```

### Input Direction Utility Classes

| Class | Effect | Use When |
|-------|--------|----------|
| `.ltr-input` | Force LTR | Codes, numbers, URLs in text input |
| `.rtl-input` | Force RTL | Arabic text in text input |
| `.auto-input` | Browser decides | Mixed RTL/LTR text |

### Labels
```css
[dir="rtl"] .form-label,
[dir="rtl"] label {
    text-align: right;
}
```

### Form Help and Error Text
```css
[dir="rtl"] .form-help,
[dir="rtl"] .form-hint,
[dir="rtl"] .form-error {
    text-align: right;
    direction: rtl;
}
```

### Input Groups
```css
[dir="rtl"] .input-group-prepend {
    margin-inline-end: -1px;
    border-start-end-radius: 0.5rem;
    border-end-end-radius: 0.5rem;
}
[dir="rtl"] .input-group-append {
    margin-inline-start: -1px;
    border-start-start-radius: 0.5rem;
    border-end-start-radius: 0.5rem;
}
```

### Select Dropdowns
```css
[dir="rtl"] .form-select {
    background-position: left var(--space-3) center;
    padding-inline-end: var(--space-3);
    padding-inline-start: var(--space-10);
}
```

---

## Buttons & Actions

### Button Group
```css
[dir="rtl"] .btn-group {
    flex-direction: row-reverse;
}
```

### Icon + Text Alignment
```css
[dir="rtl"] .btn i.fa-left,
[dir="rtl"] .btn .icon-left {
    margin-right: 0;
    margin-left: 0.5rem;
}
[dir="rtl"] .btn i.fa-right,
[dir="rtl"] .btn .icon-right {
    margin-left: 0;
    margin-right: 0.5rem;
}
```

### Action Buttons in Tables
```css
[dir="rtl"] .action-btns {
    flex-direction: row-reverse;
    justify-content: flex-start;
}
```

### Floating Action Button (FAB)
```css
[dir="rtl"] .fab {
    left: auto;
    right: 1.5rem;
}
[dir="rtl"] #quick-tools-fab {
    left: auto;
    right: 1.5rem;
}
```

### Modal Footer Actions
```css
[dir="rtl"] .modal-footer {
    flex-direction: row-reverse;
}
[dir="rtl"] .modal-footer .btn {
    margin-inline-start: 0.5rem;
    margin-inline-end: 0;
}
```

---

## Navigation

### Sidebar
- Position: RIGHT side of viewport
- Slide direction: from right
- Border: `border-inline-start` instead of `border-inline-end`

```css
html[dir="rtl"] #sidebar {
    left: auto !important;
    right: 0 !important;
    transform: translateX(100%) !important;
}
html[dir="rtl"] #sidebar.expanded {
    transform: translateX(0) !important;
}
```

### Submenu Items
```css
html[dir="rtl"] .sidebar-submenu {
    border-left: none !important;
    border-right: 1px solid var(--theme-border) !important;
}
html[dir="rtl"] .sidebar-submenu-link {
    flex-direction: row-reverse !important;
}
```

### Topbar Actions
```css
html[dir="rtl"] .topbar-actions {
    flex-direction: row-reverse !important;
    margin-left: 0 !important;
    margin-right: auto !important;
}
```

### Nav Items
```css
[dir="rtl"] .nav-list {
    flex-direction: row-reverse;
}
[dir="rtl"] .nav-item {
    flex-direction: row-reverse;
}
```

### Top Navigation
```css
[dir="rtl"] .top-nav {
    flex-direction: row-reverse;
}
```

---

## Modals & Drawers

### Modal Header
```css
[dir="rtl"] .modal-header {
    flex-direction: row-reverse;
}
[dir="rtl"] .modal-title {
    flex-direction: row-reverse;
}
```

### Modal Close Button
```css
[dir="rtl"] .modal .close {
    margin-left: 0;
    margin-right: auto;
    order: 1;
}
```

### Modal Footer
```css
[dir="rtl"] .modal-footer {
    flex-direction: row-reverse;
}
```

### Drawer (Slide-in Panel)
```css
[dir="rtl"] .drawer {
    inset-inline-end: 0;
    inset-inline-start: auto;
    border-inline-start: 1px solid var(--border-default);
    border-inline-end: none;
}
```

---

## Notifications & Alerts

### Alert
```css
[dir="rtl"] .alert {
    flex-direction: row-reverse;
}
[dir="rtl"] .alert-icon {
    margin-left: 0.75rem;
    margin-right: 0;
}
[dir="rtl"] .alert-body {
    text-align: right;
}
```

### Toast Notification
```css
[dir="rtl"] .toast {
    flex-direction: row-reverse;
}
[dir="rtl"] .toast-container {
    inset-inline-end: 1.5rem;
    inset-inline-start: auto;
}
```

---

## Dropdowns & Menus

### Dropdown Menu
```css
[dir="rtl"] .dropdown-menu {
    inset-inline-end: 0;
    inset-inline-start: auto;
    text-align: right;
}
```

### Dropdown Item
```css
[dir="rtl"] .dropdown-item {
    flex-direction: row-reverse;
}
[dir="rtl"] .dropdown-icon {
    margin-left: 0;
    margin-right: 0.5rem;
}
```

### Context Menu
```css
[dir="rtl"] .context-menu {
    inset-inline-end: 0;
    inset-inline-start: auto;
}
```

---

## Tabs & Accordions

### Tab List
```css
[dir="rtl"] .nav-tabs,
[dir="rtl"] .tab-list,
[dir="rtl"] .tabs {
    flex-direction: row-reverse;
}
[dir="rtl"] .nav-tab,
[dir="rtl"] .tab-item {
    flex-direction: row-reverse;
}
```

### Tab Icon
```css
[dir="rtl"] .tab-icon {
    margin-left: 0.5rem;
    margin-right: 0;
}
```

### Tab Active Indicator
```css
[dir="rtl"] .nav-tabs .nav-item.active {
    border-right: none;
    border-left: 2px solid var(--brand-primary);
}
```

---

## Pagination

### Pagination Container
```css
[dir="rtl"] .pagination {
    flex-direction: row-reverse;
}
[dir="rtl"] .pagination-bar {
    flex-direction: row-reverse;
}
[dir="rtl"] .page-item {
    flex-direction: row-reverse;
}
```

### Pagination Arrows
```css
[dir="rtl"] .pagination .page-prev i,
[dir="rtl"] .pagination .page-next i {
    transform: scaleX(-1);
}
```

---

## Breadcrumbs

### Breadcrumb Container
```css
[dir="rtl"] .breadcrumb {
    flex-direction: row-reverse;
}
```

### Breadcrumb Separator
```css
[dir="rtl"] .breadcrumb-separator {
    transform: scaleX(-1);
}
[dir="rtl"] .breadcrumb-item + .breadcrumb-item::before {
    content: "\f104";
    transform: scaleX(-1);
}
```

---

## Badges & Tags

### Badge
```css
[dir="rtl"] .badge {
    margin-left: 0;
    margin-right: 0.5rem;
}
```

### Tag
```css
[dir="rtl"] .tag {
    margin-left: 0;
    margin-right: 0.25rem;
}
```

### Status Badge with Icon
```css
[dir="rtl"] .status-badge {
    flex-direction: row-reverse;
}
```

---

## Progress & Loading

### Progress Bar
**Important:** Progress bars should NOT flip direction. They represent visual quantity and should remain LTR.
```css
[dir="rtl"] .progress-bar {
    direction: ltr;
}
```

### Loading Spinner
No RTL changes needed - spinner is rotationally symmetric.

### Skeleton Loader
No RTL changes needed - skeleton represents text width which follows container direction.

---

## Charts & KPIs

### Chart Container
Charts typically use LTR for data visualization.
```css
[dir="rtl"] .chart-container {
    direction: ltr;
}
```

### Chart Legend
```css
[dir="rtl"] .chart-legend {
    text-align: right;
}
```

### KPI Indicator
```css
[dir="rtl"] .kpi-indicator {
    right: auto;
    left: 1rem;
}
```

---

## Empty States

No RTL-specific rules needed - empty states follow their container's direction context.

---

## Special Cases

### Flow/Chat Messages

Message bubbles in Flow/chat:
```css
[dir="rtl"] .message-bubble {
    direction: rtl;
    text-align: right;
}
[dir="rtl"] .message-bubble.sent {
    margin-inline-start: 0;
    margin-inline-end: auto;
}
[dir="rtl"] .message-bubble.received {
    margin-inline-end: 0;
    margin-inline-start: auto;
}
[dir="rtl"] .message-meta {
    direction: ltr;
    text-align: left;
    unicode-bidi: embed;
}
```

### Timeline

```css
[dir="rtl"] .timeline {
    padding-inline-start: 2rem;
    padding-inline-end: 0;
}
[dir="rtl"] .timeline::before {
    inset-inline-start: 0.5rem;
    inset-inline-end: auto;
}
[dir="rtl"] .timeline-item {
    flex-direction: row-reverse;
}
```

### Calculator Display

```css
[dir="rtl"] .calc-display,
[dir="rtl"] .calc-result {
    direction: ltr;
    text-align: right;
}
```

### Search Input

```css
[dir="rtl"] input[type="search"] {
    direction: ltr;
    text-align: left;
}
[dir="rtl"] .filter-search-input {
    padding: 0.5rem 2.5rem 0.5rem 0.75rem;
}
[dir="rtl"] .filter-search-icon {
    left: auto;
    right: 0.875rem;
}
```

---

## Responsive RTL

```css
@media (max-width: 768px) {
    [dir="rtl"] .flex-mobile {
        flex-direction: column-reverse;
    }
}
```

---

## Print RTL

```css
@media print {
    [dir="rtl"] {
        direction: rtl;
    }
    [dir="rtl"] .no-print {
        display: none !important;
    }
    [dir="rtl"] table th,
    [dir="rtl"] table td {
        text-align: right;
    }
    [dir="rtl"] table th.numeric-col,
    [dir="rtl"] table td.numeric-col {
        text-align: left !important;
    }
}
```