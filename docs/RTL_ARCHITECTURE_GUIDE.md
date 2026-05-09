# RTL Architecture Guide

## Overview

This document describes the Right-to-Left (RTL) / Left-to-Right (LTR) bidirectional architecture for the WHDASH enterprise application. The system supports multiple languages including Persian (fa), Arabic (ar), and English (en) with proper layout flipping and mixed-content handling.

## Direction Resolution

### How Direction is Determined

1. **User Preferences**: The `direction_resolved` value comes from user preferences, resolved in `app.py`:
   - Resolved from `interface_language` direction when explicit
   - Falls back to `interface_direction` preference
   - Default: `ltr` for English, `rtl` for Persian/Arabic

2. **Base Template**: `templates/base.html` line 2 sets direction on `<html>`:
   ```html
   <html lang="{{ 'fa' if user_preferences.direction_resolved == 'rtl' else 'en' }}"
         dir="{{ user_preferences.direction_resolved }}"
         data-theme="{{ user_preferences.theme }}" ...>
   ```

3. **Body Class**: Direction is also available as a CSS class on `<body>`:
   ```html
   <body ... class="dir-{{ user_preferences.direction_resolved }}" ...>
   ```

### Supported Languages and Directions

| Language | Code | Direction | Font Stack |
|----------|------|-----------|------------|
| English | en | LTR | Outfit |
| Persian | fa | RTL | Vazirmatn, Outfit |
| Arabic | ar | RTL | Tajawal, Outfit |
| Urdu | ur | RTL | Noto Sans Arabic |
| Hebrew | he | RTL | Noto Sans Hebrew |

## CSS Architecture

### Three-Layer RTL System

The RTL support is implemented across three CSS files with decreasing specificity:

#### Layer 1: `static/css/enterprise-design-system.css`
- **Purpose**: Base RTL reset and foundational rules
- **Specificity**: Low - `[dir="rtl"]` selectors
- **Scope**: Basic direction flips, text alignment, flex direction basics
- **Loading**: Loaded early via `<link>` in `<head>`

#### Layer 2: `static/css/wms-rtl.css`
- **Purpose**: Comprehensive component-level RTL rules and semantic classes
- **Specificity**: Medium - `[dir="rtl"] .class-name` selectors
- **Scope**:
  - All UI components (cards, tables, forms, modals, dropdowns)
  - Semantic LTR content classes (.item-code, .ltr-content, .email-address)
  - Form input type handling
  - Print/export styles
- **Loading**: After enterprise-design-system.css

#### Layer 3: `templates/base.html` `<style>` block (inline)
- **Purpose**: Application-specific overrides and WMS dashboard rules
- **Specificity**: High - `html[dir="rtl"]` with `!important` to override Tailwind CDN
- **Scope**:
  - Dashboard component flips (kpi-card, filter-panel-header)
  - Sidebar behavior in RTL
  - Quick tools panel RTL
- **Loading**: Last in `<head>` to override everything

### CSS Class System for Mixed Content

#### LTR Content in RTL Context
Use these classes on elements that must remain LTR within RTL pages:

```css
.ltr-content          /* Generic LTR text */
.item-code           /* SKU, item codes, part numbers */
.barcode             /* Barcode strings */
.sku                 /* Stock keeping unit codes */
.lot-number          /* Lot/batch numbers */
.serial-number       /* Serial numbers */
.invoice-number      /* Invoice numbers */
.order-number        /* Order reference numbers */
.phone-number        /* Phone numbers */
.email-address       /* Email addresses */
.url-text            /* URLs */
```

#### Bidirectional Control
```css
.bidi-auto           /* Let browser auto-detect based on first strong character */
.bidi-embed          /* Force embedding of direction */
```

#### Form Input Direction Control
```css
input.ltr-input       /* Force LTR on specific input */
input.rtl-input       /* Force RTL on specific input */
input.auto-input      /* Browser auto-detection */
```

#### Table Column Direction
```css
th.numeric-col, td.numeric-col    /* Numbers stay LTR */
th.code-col, td.code-col          /* Codes stay LTR */
```

## Form Input Handling

### Type-Based Direction Rules

In RTL context, form inputs automatically receive direction based on input type:

| Input Type | Direction | Rationale |
|------------|-----------|-----------|
| text (general) | RTL | For RTL language content |
| textarea | RTL | For RTL language content |
| email | LTR | Email addresses are always LTR |
| tel | LTR | Phone numbers are LTR |
| url | LTR | URLs are always LTR |
| number | LTR | Numbers are LTR |
| password | LTR | Passwords are LTR |
| search | LTR | Search queries are LTR |
| date | LTR | Dates are LTR |
| time | LTR | Times are LTR |
| datetime-local | LTR | Datetimes are LTR |
| month | LTR | Months are LTR |
| week | LTR | Weeks are LTR |

### Mixed Content Text Inputs

For text inputs that may contain mixed RTL/LTR content (e.g., Persian text with English words), use:

```html
<input type="text" class="auto-input" dir="auto">
```

The `auto-input` CSS class combined with `dir="auto"` attribute allows the browser to determine direction based on the first strong directional character.

### CSS Override Classes

For specific control, these classes override the type-based default:

```html
<!-- Force LTR even in RTL page -->
<input type="text" class="ltr-input" value="SKU-12345">

<!-- Force RTL even in LTR page -->
<input type="text" class="rtl-input" value="متن فارسی">
```

## Sidebar and Navigation RTL

### Sidebar Behavior in RTL

The sidebar:
- Moves to the RIGHT side of the viewport
- Slides in from the RIGHT when expanded
- Uses `border-inline-start` instead of `border-inline-end` for border

CSS selectors for sidebar RTL:
```css
html[dir="rtl"] #sidebar {
    left: auto !important;
    right: 0 !important;
    transform: translateX(100%) !important;
}
```

### Topbar Actions

Topbar action buttons are reversed in RTL:
```css
html[dir="rtl"] .topbar-actions {
    flex-direction: row-reverse !important;
    margin-left: 0 !important;
    margin-right: auto !important;
}
```

### Navigation Menu Items

Menu items in RTL display with icon on the right side of text:
```css
html[dir="rtl"] .sidebar-submenu-link {
    flex-direction: row-reverse !important;
}
```

## Component RTL Rules

### Cards and Panels

```css
[dir="rtl"] .glass-panel { text-align: right; }
[dir="rtl"] .card-header { flex-direction: row-reverse; }
[dir="rtl"] .kpi-card { flex-direction: row-reverse; }
```

### Tables

```css
[dir="rtl"] table { direction: rtl; }
[dir="rtl"] th, [dir="rtl"] td { text-align: right; }

/* BUT numeric/code columns stay LTR */
[dir="rtl"] table th.numeric-col,
[dir="rtl"] table td.numeric-col {
    text-align: left !important;
    direction: ltr !important;
}
```

### Modals

```css
[dir="rtl"] .modal-header { flex-direction: row-reverse; }
[dir="rtl"] .modal-footer { flex-direction: row-reverse; }
[dir="rtl"] .modal .close { margin-right: auto; order: 1; }
```

### Dropdowns

```css
[dir="rtl"] .dropdown-menu {
    inset-inline-end: 0;
    inset-inline-start: auto;
}
[dir="rtl"] .dropdown-item { flex-direction: row-reverse; }
```

### Tabs

```css
[dir="rtl"] .nav-tabs { flex-direction: row-reverse; }
[dir="rtl"] .tab-icon { margin-left: 0.5rem; margin-right: 0; }
```

### Pagination

```css
[dir="rtl"] .pagination { flex-direction: row-reverse; }
[dir="rtl"] .pagination .page-prev i,
[dir="rtl"] .pagination .page-next i { transform: scaleX(-1); }
```

### Breadcrumbs

```css
[dir="rtl"] .breadcrumb { flex-direction: row-reverse; }
[dir="rtl"] .breadcrumb-separator { transform: scaleX(-1); }
```

## Print and Export RTL

### Print Template Requirements

All print templates (standalone HTML for PDF/print) must:

1. Accept `rtl` variable from Flask route
2. Set `<html dir="{{ 'rtl' if rtl else 'ltr' }}" lang="{{ 'fa' if rtl else 'en' }}">`
3. Apply RTL body direction via CSS
4. Use `.ltr-content` class on codes, numbers, barcodes
5. Use `.ltr-col` class on table header/data cells that must be LTR

### Example Print Template Structure

```html
<!DOCTYPE html>
<html lang="{{ 'fa' if rtl else 'en' }}" dir="{{ 'rtl' if rtl else 'ltr' }}">
<head>
    <style>
        body { direction: {{ 'rtl' if rtl else 'ltr' }}; }
        .ltr-content { direction: ltr; unicode-bidi: embed; }
        [dir="rtl"] table { direction: rtl; }
        [dir="rtl"] th, [dir="rtl"] td { text-align: right; }
        [dir="rtl"] th.ltr-col, [dir="rtl"] td.ltr-col {
            text-align: left !important;
            direction: ltr !important;
        }
    </style>
</head>
<body>
    <!-- content with {{ 'RTL labels' if rtl else 'LTR labels' }} -->
</body>
</html>
```

## JavaScript Direction Awareness

### Dynamic Content Addition

When JavaScript adds content dynamically (e.g., chat messages, notifications):

1. Ensure the container has `dir` attribute set appropriately
2. Use `escapeHtml()` for XSS protection (already implemented in chat.html)
3. Apply `.bidi-auto` class to user-generated text content
4. Apply `.ltr-content` to any codes/numbers added

### Direction Detection Function

Used in Flow/chat for dynamic input direction:

```javascript
function updateInputDirection(textarea) {
    const rtlPattern = /[\u0591-\u07FF\u200F\u202B\u202E\uFB1D-\uFDFD\uFE70-\uFEFC]/;
    if (rtlPattern.test(textarea.value)) {
        textarea.dir = 'rtl';
    } else {
        textarea.dir = 'ltr';
    }
}
```

### Chart/Visualization Direction

Charts typically stay LTR even in RTL pages because:
- Data visualization is universally LTR
- Numeric axes make more sense in LTR
- Chart.js and similar libraries default to LTR

Override only if specifically needed:
```css
[dir="rtl"] .chart-container {
    direction: ltr; /* Charts stay LTR */
}
```

## Loading Order

The correct CSS loading order is:

1. `static/css/enterprise-design-system.css` - Foundation
2. `static/css/wms-rtl.css` - Component rules
3. `static/css/sidebar-rtl.css` - Sidebar overrides (loaded in base.html)
4. `<style>` block in `templates/base.html` - App-specific and Tailwind overrides

## Performance Considerations

- RTL rules are scoped to `[dir="rtl"]` selector for minimal DOM traversal cost
- Logical properties (`inset-inline-start`, `margin-inline-start`) used where supported
- CSS variables used for theme tokens to minimize specificity wars
- No JavaScript required for direction switching - pure CSS

## Migration Notes

### Breaking Changes from Previous RTL System

1. **Form inputs**: Previously all inputs were forced `direction: rtl` in RTL pages. Now email/phone/number inputs automatically stay LTR.

2. **Table columns**: Numeric columns now use `numeric-col` class to explicitly stay LTR, rather than being implied.

3. **Sidebar RTL**: Uses `html[dir="rtl"]` selector with `!important` to override Tailwind CDN's implicit `!important` on all utilities.

4. **Base template inline CSS**: Added extensive LTR input type rules to fix the blanket RTL form issue.

## Future Enhancements

- Consider CSS `direction` property via `unicode-bidi: isolate` for more precise mixed-content control
- Add RTL-aware measurement units (kg, meter) display
- Consider `::-webkit-input-placeholder` RTL fixes for older browsers
- Add CSS `writing-mode: horizontal-tb` override where needed for mixed modes