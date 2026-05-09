# RTL Mixed Content Strategy

## Overview

Mixed RTL/LTR content appears throughout WHDASH when Persian/Arabic text contains English words, codes, numbers, or when data fields contain mixed-language values. This document defines the strategy for handling such mixed content correctly.

## The Problem

In RTL languages, the text flows from right to left. However, when the content contains:
- English words/names
- Codes (item codes, order numbers)
- Numbers (quantities, prices)
- Dates and times
- Email addresses, URLs

These elements must be displayed LTR to remain readable, but they must also visually fit within the RTL flow of the surrounding text.

## Solution Architecture

### 1. Unicode Bidirectional Algorithm

The browser's built-in Unicode Bidirectional Algorithm (UBA) handles most cases automatically. However, for guaranteed correct rendering, we use explicit direction control.

### 2. CSS Classes for LTR Content

Apply these classes to force LTR rendering in RTL context:

```css
.ltr-content     /* General LTR text */
.item-code       /* SKU, item codes */
.barcode         /* Barcode strings */
.sku             /* Stock keeping unit */
.lot-number      /* Batch/lot numbers */
.serial-number   /* Serial numbers */
.invoice-number  /* Invoice numbers */
.order-number    /* Order reference */
.phone-number    /* Phone numbers */
.email-address   /* Email addresses */
.url-text        /* URLs */
```

### 3. HTML `dir` Attribute

For form inputs with mixed content, use `dir="auto"` to let the browser decide direction based on the first strong character:

```html
<input type="text" dir="auto" placeholder="کد محصول: SKU-12345">
```

## Common Patterns and Solutions

### Pattern 1: Persian Text with English Word

**Problem:**
```html
<p>سفارش شما با موفقیت ثبت شد - Order #ORD-12345</p>
```

**Solution:**
```html
<p>سفارش شما با موفقیت ثبت شد - Order <span class="ltr-content">#ORD-12345</span></p>
```

**CSS:**
```css
.ltr-content {
    direction: ltr;
    unicode-bidi: embed;
}
```

### Pattern 2: Arabic Text with Item Code

**Problem:**
```html
<td>کد کالا: WH-2024-001</td>
```

**Solution:**
```html
<td>کد کالا: <span class="item-code ltr-content">WH-2024-001</span></td>
```

### Pattern 3: Phone Number in RTL Context

**Problem:**
```html
<td>تلفن: +98-21-8865-1234</td>
```

**Solution:**
```html
<td>تلفن: <span class="phone-number ltr-content">+98-21-8865-1234</span></td>
```

### Pattern 4: Date in RTL Text

**Dates should generally stay LTR** for readability, but if they're embedded in RTL text:

```html
<p class="bidi-auto">تاریخ سفارش: 2024-01-15</p>
```

Or explicitly:
```html
<p>تاریخ سفارش: <span class="ltr-content">2024-01-15</span></p>
```

### Pattern 5: Email Address

**Always LTR:**
```html
<td>ایمیل: <span class="email-address ltr-content">user@example.com</span></td>
```

### Pattern 6: Mixed Form Input

For inputs where user might type Persian with English codes:

```html
<input type="text" class="auto-input" dir="auto"
       placeholder="مثال: SKU-2024-001">
```

```css
.auto-input {
    direction: auto;
    unicode-bidi: plaintext;
}
```

### Pattern 7: Table Cell with Multiple Data Types

```html
<td>
    <span class="text-rtl">کد محصول:</span>
    <span class="item-code ltr-content">SKU-12345</span>
</td>
```

### Pattern 8: URL in RTL Text

**Solution:**
```html
<p class="bidi-auto">
    برای اطلاعات بیشتر به
    <a href="..." class="url-text ltr-content">https://example.com/docs</a>
    مراجعه کنید.
</p>
```

```css
.url-text {
    direction: ltr;
    unicode-bidi: embed;
}
```

## Code Display Classes

### Semantic Code Classes

For semantic clarity and consistent RTL handling:

| Class | Use For | Example |
|-------|---------|---------|
| `.item-code` | Item/SKU codes | `SKU-2024-001` |
| `.barcode` | Barcode strings | `5901234123457` |
| `.sku` | Stock keeping unit | `WH-ABC-123` |
| `.lot-number` | Lot/batch numbers | `LOT-2024-001` |
| `.serial-number` | Serial numbers | `SN-123456789` |
| `.invoice-number` | Invoice numbers | `INV-2024-001` |
| `.order-number` | Order references | `ORD-12345` |

### Applying Code Classes

In Jinja templates:
```html
<td>
    <span class="item-code ltr-content">
        {{ item.item_code }}
    </span>
</td>
```

For dynamic content:
```html
<td>
    <span class="{{ code_class }} ltr-content">
        {{ code_value }}
    </span>
</td>
```

## Numeric Display

### Quantity and Amount Display

```html
<td class="quantity ltr-content">{{ quantity }}</td>
```

```css
.quantity {
    direction: ltr;
    text-align: left;
    font-variant-numeric: tabular-nums;
}
```

### Currency Display

```html
<td>
    <span class="amount ltr-content">{{ "%.2f"|format(amount) }}</span>
    <span class="currency-code ltr-content">USD</span>
</td>
```

### Percentage Display

```html
<td>
    <span class="percentage ltr-content">{{ value }}%</span>
</td>
```

## Form Field Strategy

### Text Input (Persian/Arabic)
```html
<input type="text" class="rtl-input" dir="rtl" placeholder="نام محصول">
```
Or rely on automatic RTL for `type="text"` in RTL pages.

### Text Input (English)
```html
<input type="text" class="ltr-input" dir="ltr" placeholder="Product name">
```

### Text Input (Mixed)
```html
<input type="text" class="auto-input" dir="auto" placeholder="Mixed content allowed">
```

### Email Input
```html
<input type="email" dir="ltr" class="email-input">
```
Email inputs automatically get `direction: ltr` in RTL pages via CSS.

### Number Input
```html
<input type="number" dir="ltr">
```
Number inputs automatically get `direction: ltr` in RTL pages via CSS.

### Phone Input
```html
<input type="tel" dir="ltr" class="phone-input">
```
Phone inputs automatically get `direction: ltr` in RTL pages via CSS.

### Date/Time Inputs
```html
<input type="date" dir="ltr">
<input type="time" dir="ltr">
```
Date and time inputs automatically get `direction: ltr` in RTL pages via CSS.

## Table Column Strategy

### Text Columns
- Align: right (in RTL context)
- Direction: RTL
```html
<th>نام محصول</th>
```

### Numeric Columns
- Align: left (in RTL context)
- Direction: LTR
- Class: `numeric-col`
```html
<th class="numeric-col">تعداد</th>
```

### Code Columns
- Align: left (in RTL context)
- Direction: LTR
- Class: `code-col`
```html
<th class="code-col">کد کالا</th>
```

### Action Columns
- Flex direction: row-reverse
- Class: `action-col`
```html
<td class="action-col">
    <button>Edit</button>
</td>
```

## JavaScript Handling

### Dynamic Message Addition (Flow/Chat)

When adding user-generated content via JavaScript:

```javascript
function addMessage(content, code) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message-bubble bidi-auto';
    msgDiv.textContent = content;

    const codeSpan = document.createElement('span');
    codeSpan.className = 'item-code ltr-content';
    codeSpan.textContent = code;

    msgDiv.appendChild(codeSpan);
    return msgDiv;
}
```

### Input Direction Detection

```javascript
const rtlChars = /[\u0591-\u07FF\u200F\u202B\u202E\uFB1D-\uFDFD\uFE70-\uFEFC]/;

function detectDirection(text) {
    return rtlChars.test(text) ? 'rtl' : 'ltr';
}
```

### Timestamps

Timestamps should stay LTR for readability:

```html
<span class="message-meta ltr-content">{{ timestamp }}</span>
```

```css
.message-meta {
    direction: ltr;
    unicode-bidi: embed;
}
```

## Print/Export Considerations

### Print Templates

In print templates for RTL languages:

1. Set `dir="rtl"` on `<html>`
2. Use `.ltr-content` on all codes, numbers, barcodes
3. Use `unicode-bidi: embed` for inline LTR content

```html
<table>
    <tr>
        <th>شرح</th>
        <th class="ltr-col">کد</th>
        <th class="ltr-col">تعداد</th>
    </tr>
    <tr>
        <td>{{ description }}</td>
        <td class="ltr-content" style="direction:ltr;">{{ code }}</td>
        <td class="ltr-content" style="direction:ltr;">{{ qty }}</td>
    </tr>
</table>
```

### CSV/Excel Export

When exporting data that will be opened in spreadsheet applications:
- Keep numeric/code columns as-is (spreadsheets handle direction)
- If exporting to a locale-specific format, ensure encoding is correct

## Validation and Edge Cases

### Edge Case: Empty Code Display
```html
<td>
    <span class="item-code ltr-content">{{ item.code or '—' }}</span>
</td>
```

### Edge Case: Long Code in Table
```html
<td class="code-col">
    <span class="item-code ltr-content" style="max-width:150px;overflow:hidden;text-overflow:ellipsis;">
        {{ long_code }}
    </span>
</td>
```

### Edge Case: Inline RTL/LTR Paragraph
```html
<p class="bidi-auto">
    این سفارش با کد
    <span class="order-number ltr-content">ORD-12345</span>
    ثبت شد و
    <span class="ltr-content">John Smith</span>
    تأیید کرد.
</p>
```

### Edge Case: Punctuation Adjacent to LTR Content

**Problem:** Period/comma may appear on wrong side.

**Solution:** Use `unicode-bidi: embed` to isolate direction:

```css
.ltr-content {
    unicode-bidi: embed;
}
```

## Testing Checklist

### Mixed Content Test Cases

- [ ] Persian text + English word in paragraph
- [ ] Arabic text + item code in table cell
- [ ] Persian text + phone number
- [ ] Arabic text + email address
- [ ] Persian text + URL
- [ ] Persian text + date
- [ ] Persian text + percentage
- [ ] Persian text + currency amount
- [ ] Mixed text in form input
- [ ] Mixed text in chat message
- [ ] Table with text, code, and numeric columns

### Print/Export Test Cases

- [ ] Print preview in RTL language
- [ ] PDF export in RTL language
- [ ] Codes visible in printed document
- [ ] Numbers aligned correctly in print

## CSS Quick Reference

```css
/* LTR content in RTL context */
.ltr-content {
    direction: ltr !important;
    text-align: left !important;
    unicode-bidi: embed;
}

/* Auto-detection */
.bidi-auto {
    direction: auto;
    unicode-bidi: plaintext;
}

/* Code-specific */
.item-code, .sku, .barcode, .lot-number {
    direction: ltr !important;
    text-align: left !important;
    unicode-bidi: embed;
}

/* Numeric values */
.numeric-col, .quantity, .amount, .percentage {
    direction: ltr !important;
    text-align: left !important;
    font-variant-numeric: tabular-nums;
}

/* Email and URL */
.email-address, .url-text, .phone-number {
    direction: ltr !important;
    text-align: left !important;
    unicode-bidi: embed;
}
```