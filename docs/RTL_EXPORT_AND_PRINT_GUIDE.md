# RTL Export and Print Guide

## Overview

This guide covers RTL (Right-to-Left) support for exports and print layouts in WHDASH. It addresses HTML print templates, PDF generation, CSV/Excel exports, and the special considerations for handling mixed RTL/LTR content in exported documents.

## Print Template Architecture

### Standalone Print Templates

Standalone print templates (those that don't extend `base.html`) must implement their own RTL support. They should work both as:
- HTML rendered in browser for print preview
- HTML-to-PDF converted documents

### Print Template File Locations

| Template | Purpose | RTL Status |
|----------|---------|------------|
| `templates/wms/print_grn.html` | Goods Receipt Note | ✅ RTL Updated |
| `templates/wms/print_pick_list.html` | Pick List | ✅ RTL Updated |
| `templates/forms/export/pdf_template.html` | Form submission PDF | ✅ Already RTL-aware |
| `templates/logistics/documents/print_templates.html` | Transport docs | Uses base.html |

### Required RTL Elements in Print Templates

Every standalone print template must include:

```html
<!DOCTYPE html>
<html lang="{{ 'fa' if rtl else 'en' }}"
      dir="{{ 'rtl' if rtl else 'ltr' }}">
<head>
    <meta charset="UTF-8">
    <style>
        /* Body direction */
        body { direction: {{ 'rtl' if rtl else 'ltr' }}; }

        /* LTR content classes */
        .ltr-content {
            direction: ltr;
            unicode-bidi: embed;
        }

        /* Table RTL adjustments */
        [dir="rtl"] table { direction: rtl; }
        [dir="rtl"] th, [dir="rtl"] td { text-align: right; }
        [dir="rtl"] th.ltr-col, [dir="rtl"] td.ltr-col {
            text-align: left !important;
            direction: ltr !important;
        }
    </style>
</head>
<body>
    <!-- Content -->
</body>
</html>
```

## Print Template RTL Checklist

### Structure
- [ ] `<!DOCTYPE html>` present
- [ ] `<html>` has `lang="{{ 'fa' if rtl else 'en' }}"`
- [ ] `<html>` has `dir="{{ 'rtl' if rtl else 'ltr' }}"`
- [ ] `<meta charset="UTF-8">` present
- [ ] `<title>` set appropriately

### CSS
- [ ] `body { direction: ... }` set
- [ ] `.ltr-content` class defined
- [ ] `th.ltr-col, td.ltr-col` classes defined for numeric/code columns
- [ ] Print media query present: `@media print { ... }`
- [ ] No-print elements hidden in print: `.no-print { display: none; }`

### Content
- [ ] Labels change with language (Persian/English)
- [ ] Codes/IDs have `.ltr-content` class
- [ ] Numbers have `.ltr-content` class
- [ ] Dates formatted correctly for locale

## Bilingual Labels in Print Templates

Use Jinja2 conditionals for bilingual labels:

```html
<!-- Static approach -->
{% if rtl %}
    <th>کد کالا</th>
    <th>توضیحات</th>
    <th>تعداد</th>
{% else %}
    <th>Item Code</th>
    <th>Description</th>
    <th>Quantity</th>
{% endif %}

<!-- Reusable macro approach -->
{% macro th(label) %}
    <th>{{ label if rtl else label }}</th>
{% endmacro %}
```

### Common Label Translations

| English | Persian (RTL) |
|---------|--------------|
| Item Code | کد کالا |
| Description | توضیحات |
| Quantity | تعداد |
| Expected | انتظار |
| Received | دریافتی |
| Accepted | پذیرش |
| Rejected | رد |
| Lot Number | شماره بچ |
| Location | موقعیت |
| Order Number | شماره سفارش |
| Receipt Number | شماره رسید |
| Warehouse | انبار |
| Supplier | تأمین‌کننده |
| Status | وضعیت |
| Date | تاریخ |
| Time | زمان |
| Prepared By | تهیه‌کننده |
| Checked By | بازبینی‌کننده |
| Received By | دریافت‌کننده |

## Table Handling in Print

### Standard Table (Text Content)

```html
<table>
    <thead>
        <tr>
            <th>شرح</th>
            <th class="ltr-col">کد</th>
            <th class="ltr-col">تعداد</th>
        </tr>
    </thead>
    <tbody>
        {% for item in items %}
        <tr>
            <td>{{ item.description }}</td>
            <td class="ltr-content" style="direction:ltr;">{{ item.code }}</td>
            <td class="ltr-content" style="direction:ltr;">{{ item.qty }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

### Key Rules for Print Tables

1. **Text columns**: Right-aligned in RTL
2. **Code columns**: Left-aligned with `class="ltr-col"` and inline `style="direction:ltr;"`
3. **Numeric columns**: Left-aligned with `class="ltr-col"` and inline `style="direction:ltr;"`
4. **Always use `unicode-bidi: embed`** for inline LTR content to prevent punctuation issues

### Complete Print Table Example

```html
<table>
    <thead>
        <tr>
            <th>{{ 'شرح' if rtl else 'Description' }}</th>
            <th class="ltr-col">{{ 'کد کالا' if rtl else 'Item Code' }}</th>
            <th class="ltr-col">{{ 'تعداد' if rtl else 'Quantity' }}</th>
            <th class="ltr-col">{{ 'واحد' if rtl else 'Unit' }}</th>
            <th class="ltr-col">{{ 'قیمت' if rtl else 'Price' }}</th>
            <th class="ltr-col">{{ 'مجموع' if rtl else 'Total' }}</th>
        </tr>
    </thead>
    <tbody>
        {% for line in lines %}
        <tr>
            <td>{{ line.description }}</td>
            <td class="ltr-content" style="direction:ltr;text-align:left;">{{ line.item_code }}</td>
            <td class="ltr-content" style="direction:ltr;text-align:left;">{{ line.quantity|int }}</td>
            <td class="ltr-content" style="direction:ltr;text-align:left;">{{ line.unit }}</td>
            <td class="ltr-content" style="direction:ltr;text-align:left;">{{ "%.2f"|format(line.price) }}</td>
            <td class="ltr-content" style="direction:ltr;text-align:left;">{{ "%.2f"|format(line.total) }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
```

## CSS for Print

### Print-Specific CSS Rules

```css
@media print {
    /* Reset direction for print */
    body { direction: {{ 'rtl' if rtl else 'ltr' }}; }

    /* Hide non-print elements */
    .no-print { display: none !important; }

    /* Table adjustments */
    table { direction: {{ 'rtl' if rtl else 'ltr' }}; }
    th, td { text-align: {{ 'right' if rtl else 'left' }}; }

    /* Code/number columns stay LTR */
    th.ltr-col, td.ltr-col {
        text-align: left !important;
        direction: ltr !important;
    }

    /* Reduce margins for printing */
    body { margin: 0; padding: 0; }

    /* Ensure backgrounds print */
    * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
}
```

### Print Styles for LTR Content in RTL Print

```css
/* Print-specific LTR content handling */
@media print {
    [dir="rtl"] .ltr-content {
        direction: ltr !important;
        unicode-bidi: embed;
    }
}
```

## Page Layout for Print

### Page Margins and Size

```css
@page {
    size: A4;
    margin: 20mm;
}
```

### Header Block

```html
<div class="header" style="text-align: center; margin-bottom: 30px; border-bottom: 2px solid #333; padding-bottom: 20px;">
    <h1 style="margin: 0; font-size: 24px;">{{ 'سند دریافت کالا' if rtl else 'Goods Receipt Note' }}</h1>
    <p class="ltr-content" style="direction:ltr;">{{ receipt_number }}</p>
</div>
```

### Info Grid Layout

For document metadata (receipt info, dates, etc.):

```html
<div class="info-grid" style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
    <div class="info-box" style="border: 1px solid #ddd; padding: 10px; border-radius: 4px;">
        <label style="display: block; font-size: 10px; color: #888; text-transform: uppercase;">
            {{ 'شماره رسید' if rtl else 'Receipt Number' }}
        </label>
        <div class="value ltr-content" style="direction:ltr;font-size: 14px; font-weight: bold; margin-top: 2px;">
            {{ receipt_number }}
        </div>
    </div>
    <!-- More info boxes -->
</div>
```

### Footer with Signature Blocks

```html
<div class="footer" style="margin-top: 50px; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px;">
    <div class="signature" style="border-top: 1px solid #333; padding-top: 5px; text-align: center; font-size: 10px;">
        <p>{{ 'تهیه‌کننده' if rtl else 'Prepared By' }}</p>
        <br><br><br>
        ____________________
    </div>
    <div class="signature" style="border-top: 1px solid #333; padding-top: 5px; text-align: center; font-size: 10px;">
        <p>{{ 'بازبینی‌کننده' if rtl else 'Checked By' }}</p>
        <br><br><br>
        ____________________
    </div>
    <div class="signature" style="border-top: 1px solid #333; padding-top: 5px; text-align: center; font-size: 10px;">
        <p>{{ 'دریافت‌کننده' if rtl else 'Received By' }}</p>
        <br><br><br>
        ____________________
    </div>
</div>
```

## Export Routes and RTL Context

### Flask Route Pattern for Print Templates

```python
@app.route('/wms/print/grn/<int:receipt_id>')
def print_grn(receipt_id):
    receipt = get_receipt(receipt_id)

    # Determine RTL from user preferences or query param
    rtl = request.args.get('rtl', 'false').lower() == 'true'
    if not rtl and session.get('user_preferences'):
        rtl = session['user_preferences'].get('direction_resolved') == 'rtl'

    return render_template(
        'wms/print_grn.html',
        title='Print GRN',
        receipt=receipt,
        lines=receipt.lines,
        rtl=rtl  # Pass to template
    )
```

### PDF Generation Considerations

When generating PDFs from HTML:
1. Ensure the HTML has proper `dir` and `lang` attributes
2. Use embedded fonts for RTL scripts (Noto Sans Arabic for Arabic, Vazirmatn for Persian)
3. Test PDF output with actual RTL content

### CSS for Embedded Fonts in Print

```css
@font-face {
    font-family: 'Vazirmatn';
    src: url('/static/fonts/Vazirmatn-Regular.woff2') format('woff2');
    font-weight: normal;
    font-style: normal;
}

body {
    font-family: 'Vazirmatn', Arial, sans-serif;
}
```

## Excel/CSV Export Considerations

### Excel Export Notes

When exporting data to Excel:
- Excel handles RTL/LTR direction internally
- Number formats are preserved regardless of language
- Column headers should be in the appropriate language

### CSV Export Notes

- CSV files are plain text - no direction metadata
- For mixed content, use proper encoding (UTF-8 with BOM for Excel compatibility)
- Consider that CSV viewers may not handle RTL well

### Export UI Panel RTL

For export center pages that use base.html:
- [ ] Export format tabs are RTL-reversed
- [ ] Column selection checkboxes align correctly
- [ ] "Export" button placement follows RTL layout

## Testing Print Templates

### Browser Print Preview Testing

1. Open template in browser
2. Add `?rtl=true` to URL
3. Open browser print preview (Ctrl+P)
4. Verify layout direction
5. Check all codes/numbers are LTR
6. Check labels are in Persian/Arabic

### PDF Conversion Testing

1. Use browser "Save as PDF" feature
2. Open resulting PDF
3. Verify direction is correct
4. Verify all text renders (not missing glyphs)
5. Check codes are readable

### Common Print Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Codes look reversed | Missing `direction:ltr` on code cells | Add `class="ltr-content" style="direction:ltr;"` |
| Text cut off | Column too narrow | Increase column width |
| Missing glyphs | Font not embedded | Embed RTL font in CSS |
| Numbers look wrong | Wrong alignment | Use `class="ltr-col"` for numeric columns |
| Layout breaks in PDF | CSS not supported | Inline critical CSS |

## Quick Reference: Print Template Checklist

- [ ] `<!DOCTYPE html>`
- [ ] `<html lang="{{ 'fa' if rtl else 'en' }}" dir="{{ 'rtl' if rtl else 'ltr' }}">`
- [ ] `<meta charset="UTF-8">`
- [ ] CSS with `.ltr-content` class
- [ ] CSS with `th.ltr-col, td.ltr-col` for numeric/code columns
- [ ] Bilingual labels (Persian/English)
- [ ] Inline `style="direction:ltr;"` on code/number cells
- [ ] `@media print` rules
- [ ] Signature/footer block with RTL labels
- [ ] Font embedding for RTL scripts

## Example: Complete RTL-Ready Print Template

```html
<!DOCTYPE html>
<html lang="{{ 'fa' if rtl else 'en' }}" dir="{{ 'rtl' if rtl else 'ltr' }}">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: Arial, sans-serif;
            font-size: 12px;
            margin: 20px;
            direction: {{ 'rtl' if rtl else 'ltr' }};
        }
        .header { text-align: center; margin-bottom: 30px; border-bottom: 2px solid #333; padding-bottom: 20px; }
        .header h1 { margin: 0; font-size: 24px; }
        .header p { margin: 5px 0; color: #666; }
        .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }
        .info-box { border: 1px solid #ddd; padding: 10px; border-radius: 4px; }
        .info-box label { display: block; font-size: 10px; color: #888; text-transform: uppercase; }
        .info-box .value { font-size: 14px; font-weight: bold; margin-top: 2px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; }
        th { background-color: #f5f5f5; font-size: 10px; text-transform: uppercase; }
        .text-right { text-align: right; }
        .text-center { text-align: center; }

        /* LTR content in RTL print */
        .ltr-content {
            direction: ltr;
            unicode-bidi: embed;
            font-variant-numeric: tabular-nums;
        }

        /* Table RTL adjustments */
        [dir="rtl"] table { direction: rtl; }
        [dir="rtl"] th, [dir="rtl"] td { text-align: right; }
        [dir="rtl"] th.ltr-col, [dir="rtl"] td.ltr-col {
            text-align: left !important;
            direction: ltr !important;
        }

        .footer { margin-top: 50px; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; }
        .signature { border-top: 1px solid #333; padding-top: 5px; text-align: center; font-size: 10px; }
        @media print {
            body { margin: 0; }
            [dir="rtl"] .ltr-content { direction: ltr !important; }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ 'عنوان سند' if rtl else 'Document Title' }}</h1>
        <p class="ltr-content" style="direction:ltr;">{{ doc_number }}</p>
    </div>

    <div class="info-grid">
        <div class="info-box">
            <label>{{ 'شماره' if rtl else 'Number' }}</label>
            <div class="value ltr-content" style="direction:ltr;">{{ doc_number }}</div>
        </div>
        <div class="info-box">
            <label>{{ 'تاریخ' if rtl else 'Date' }}</label>
            <div class="value ltr-content" style="direction:ltr;">{{ doc_date }}</div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>{{ 'شرح' if rtl else 'Description' }}</th>
                <th class="ltr-col">{{ 'کد' if rtl else 'Code' }}</th>
                <th class="ltr-col">{{ 'تعداد' if rtl else 'Qty' }}</th>
            </tr>
        </thead>
        <tbody>
            {% for item in items %}
            <tr>
                <td>{{ item.description }}</td>
                <td class="ltr-content" style="direction:ltr;text-align:left;">{{ item.code }}</td>
                <td class="ltr-content" style="direction:ltr;text-align:left;">{{ item.qty }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    <div class="footer">
        <div class="signature">
            <p>{{ 'امضای اول' if rtl else 'Signature 1' }}</p>
            <br><br><br>
            ____________________
        </div>
        <div class="signature">
            <p>{{ 'امضای دوم' if rtl else 'Signature 2' }}</p>
            <br><br><br>
            ____________________
        </div>
        <div class="signature">
            <p>{{ 'امضای سوم' if rtl else 'Signature 3' }}</p>
            <br><br><br>
            ____________________
        </div>
    </div>
</body>
</html>
```