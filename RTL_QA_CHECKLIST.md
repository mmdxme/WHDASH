# RTL QA Checklist

Use this checklist to verify RTL/LTR behavior across the WHDASH application. Test all major modules and components.

## Pre-Testing Setup

### Environment Check
- [ ] Verify browser is set to Persian (fa) or Arabic (ar) language
- [ ] User preference set to RTL direction
- [ ] Check browser developer tools: `<html dir="rtl" lang="fa">` is present
- [ ] Confirm CSS files are loaded in correct order

### CSS File Loading Order
1. [ ] `enterprise-design-system.css` loaded
2. [ ] `wms-rtl.css` loaded
3. [ ] `sidebar-rtl.css` loaded
4. [ ] Base template `<style>` block loaded last

---

## 1. Base Layout / App Shell

### Sidebar
- [ ] Sidebar appears on RIGHT side of screen
- [ ] Sidebar toggle button is on the RIGHT
- [ ] Toggle hamburger icon is mirrored (scaleX(-1))
- [ ] Sidebar slides IN from the RIGHT
- [ ] Sidebar expanded state pushes content from right
- [ ] Sidebar collapse works correctly
- [ ] Sidebar overlay covers full height

### Topbar
- [ ] Topbar actions are reversed (RTL order)
- [ ] Language selector shows correct flag
- [ ] User menu aligns correctly
- [ ] Search bar placeholder direction matches language

### Main Content Area
- [ ] Content area starts from the right edge
- [ ] No unexpected left-side overflow
- [ ] Page transitions feel natural

---

## 2. Navigation / Menu

### Main Navigation
- [ ] Nav items are reversed (RTL order)
- [ ] Icons appear on right side of text in nav items
- [ ] Active state indicator is on the correct side
- [ ] Hover effects work correctly

### Submenu
- [ ] Submenu indent is from the right edge
- [ ] Submenu border is on the right side
- [ ] Chevron/arrow icons are mirrored
- [ ] Pin button position is correct

### Breadcrumbs
- [ ] Breadcrumb order is reversed
- [ ] Separator arrows are mirrored (← instead of →)
- [ ] Current page appears on the right

---

## 3. Page Headers / Tabs

### Page Headers
- [ ] Page title aligns right
- [ ] Action buttons align left
- [ ] Header actions are in RTL order

### Tabs
- [ ] Tab order is reversed (right to left)
- [ ] Active tab indicator is on correct side
- [ ] Tab icons flip correctly
- [ ] Tab hover effects work

---

## 4. Cards / Stat Widgets / Dashboards

### KPI Cards
- [ ] Card icon/indicator moves to left side
- [ ] Card content is reversed (icon | value | label)
- [ ] Trend badge and value stack correctly
- [ ] Card body aligns to right

### Stat Cards
- [ ] Stat card content is RTL-reversed
- [ ] Numbers align left within RTL card
- [ ] Trend indicators (↑/↓) render correctly

### Dashboard
- [ ] Dashboard hero section is RTL-flipped
- [ ] Insight cards are RTL-flipped
- [ ] Part cell info is RTL-flipped
- [ ] Shortcut grid uses RTL direction

---

## 5. Tables / Grids

### Table Headers
- [ ] Headers align right
- [ ] Header icons (sort, filter) are on correct side

### Table Body
- [ ] Body cells align right
- [ ] **Numeric columns (qty, amount) align LEFT**
- [ ] **Code columns (item_code, SKU) align LEFT**
- [ ] Row hover effects work

### Table Actions
- [ ] Action buttons column is RTL-reversed
- [ ] Edit/delete icons align correctly

### Filter Bar
- [ ] Filter controls are RTL-reversed
- [ ] Search input direction is correct
- [ ] Date pickers render correctly

### Pagination
- [ ] Pagination order is reversed
- [ ] Prev/Next arrows are mirrored
- [ ] Page numbers display correctly

---

## 6. Forms / Inputs

### Text Inputs (RTL content)
- [ ] Direction is RTL
- [ ] Text aligns right
- [ ] Placeholder text direction matches

### Text Inputs (LTR content - English words, codes)
- [ ] `dir="auto"` or `.ltr-input` class applied
- [ ] Direction is LTR
- [ ] Text aligns left

### Email/Phone/Number Inputs
- [ ] Direction is automatically LTR (no override needed)
- [ ] Input direction is LTR
- [ ] Values display correctly

### Select Dropdowns
- [ ] Dropdown arrow is on the left side
- [ ] Dropdown menu aligns to the right
- [ ] Selected value displays correctly

### Form Labels
- [ ] Labels align right
- [ ] Labels are above input in RTL context

### Form Validation
- [ ] Error messages align right
- [ ] Error icons are on correct side
- [ ] Success messages align right

### Input Groups (with prepend/append)
- [ ] Prepend/append positions are flipped
- [ ] Border radii are correct (rightmost has left radius)

---

## 7. Buttons / Button Groups

### Single Buttons
- [ ] Icon + text order is reversed in RTL
- [ ] Button text aligns correctly

### Button Groups
- [ ] Button order is reversed
- [ ] Border radii are correct (outer buttons swap)

### Floating Action Button (FAB)
- [ ] FAB is on the LEFT side in RTL
- [ ] FAB menu opens to the left

---

## 8. Modals / Drawers / Popovers

### Modal Header
- [ ] Header content is RTL-reversed
- [ ] Close button is on the LEFT side

### Modal Body
- [ ] Body content aligns right
- [ ] Form elements work correctly

### Modal Footer
- [ ] Button order is reversed
- [ ] Primary button position is correct

### Drawer (Slide-in Panel)
- [ ] Drawer slides from the LEFT side
- [ ] Drawer header aligns correctly

### Popovers/Tooltips
- [ ] Arrow points in correct direction
- [ ] Content aligns correctly

---

## 9. Notifications / Alerts / Toasts

### Alert
- [ ] Icon is on the right side
- [ ] Content aligns right
- [ ] Dismiss button is on correct side

### Toast Notification
- [ ] Toast appears on the LEFT side
- [ ] Icon + content is RTL-reversed
- [ ] Close button is on correct side

### Empty State
- [ ] Icon + text aligns correctly
- [ ] Action button placement is correct

---

## 10. Dropdowns / Context Menus

### Dropdown Menu
- [ ] Menu aligns to the right edge of trigger
- [ ] Menu items are RTL-reversed
- [ ] Icons appear on right side of item text

### Context Menu (Right-click)
- [ ] Menu appears on the left side of cursor
- [ ] Menu items align right

---

## 11. Reports / Charts / Analytics

### Report Tables
- [ ] Headers align right
- [ ] Numeric columns align left
- [ ] Code columns align left

### Charts
- [ ] Chart container stays LTR (correct for data viz)
- [ ] Chart title aligns right
- [ ] Legend aligns right
- [ ] Axis labels are readable

### KPI Dashboard Widgets
- [ ] Widgets flip correctly
- [ ] Number alignment is correct
- [ ] Trend labels are readable

---

## 12. Print Layouts / PDF Exports

### Print Preview
- [ ] Page direction is correct
- [ ] Text aligns correctly
- [ ] Table columns are correct (text right, numbers left)

### PDF Export
- [ ] Generated PDF has correct direction
- [ ] Codes/numbers are readable in PDF
- [ ] Tables don't break

### Standalone Print Template (`print_grn.html`, etc.)
- [ ] `<html dir="rtl">` when `rtl=True`
- [ ] Labels are in correct language
- [ ] Codes are LTR (`class="ltr-content"`)
- [ ] Numbers are LTR (`class="numeric-col"`)

---

## 13. Flow / Chat / Messaging

### Message Bubbles
- [ ] Sent messages align to the left
- [ ] Received messages align to the right
- [ ] Message text direction is correct per content

### Timestamps
- [ ] Timestamps are LTR (`.message-meta`)
- [ ] Timestamps appear on correct side of bubble

### Input Field
- [ ] Text input has correct direction
- [ ] `dir="auto"` detects mixed content correctly

### Dynamic Message Addition
- [ ] New messages get `.bidi-auto` class
- [ ] Codes in messages have `.ltr-content`
- [ ] Messages appear in correct order

---

## 14. Mixed RTL/LTR Content Tests

### Test Case: Persian text + English word
- [ ] Display: `سفارش شما با موفقیت ثبت شد - Order #ORD-12345`
- [ ] Code/Order number is LTR

### Test Case: Arabic text + Item code
- [ ] Display: `کد محصول: WH-2024-001`
- [ ] Item code is LTR with mono font

### Test Case: Persian text + Phone number
- [ ] Display: `تلفن: +98-21-8865-1234`
- [ ] Phone number is LTR

### Test Case: Arabic text + Email
- [ ] Display: `ایمیل: user@example.com`
- [ ] Email is LTR

### Test Case: Mixed text in form input
- [ ] User can type mixed RTL/LTR text
- [ ] Input direction changes based on content

### Test Case: Table with text, code, numeric columns
- [ ] Text column: right-aligned (RTL)
- [ ] Code column: left-aligned (LTR) with mono font
- [ ] Numeric column: left-aligned (LTR) with tabular-nums

---

## 15. Language Switching

### Switch from English (LTR) to Persian (RTL)
- [ ] Entire layout flips to RTL
- [ ] No visual glitches during transition
- [ ] Sidebar moves to right side
- [ ] All components update correctly

### Switch from Persian (RTL) to English (LTR)
- [ ] Entire layout flips to LTR
- [ ] No residual RTL artifacts
- [ ] Sidebar moves to left side
- [ ] All components update correctly

### Switch from Persian to Arabic
- [ ] Both are RTL - no layout change needed
- [ ] Font changes appropriately (Vazirmatn → Tajawal)

---

## 16. Edge Cases

### Long Text in Narrow Column
- [ ] Text truncation/ellipsis works correctly
- [ ] No overflow in RTL mode

### Numbers with Decimal Points
- [ ] `1,234.56` displays correctly in RTL table
- [ ] Decimal alignment is correct

### Negative Numbers
- [ ] `-100` displays correctly
- [ ] Parentheses format `(100)` displays correctly

### Percentage Values
- [ ] `25%` displays correctly
- [ ] Percentage bar (LTR) fills correctly

### Currency Values
- [ ] Currency symbol + amount displays correctly
- [ ] `USD 1,234.56` displays in LTR order

### Date Formats
- [ ] `2024-01-15` displays correctly
- [ ] `1402/10/25` (Jalali) displays correctly

### Timestamps
- [ ] `12:30:45` displays correctly
- [ ] Full datetime formats display correctly

### URLs
- [ ] `https://example.com` displays in LTR
- [ ] No broken visual display

### Email Addresses
- [ ] `user.name@example.com` displays in LTR
- [ ] @ and . are visually correct

---

## 17. Accessibility

- [ ] Screen reader reads content in correct order
- [ ] Focus order follows RTL flow
- [ ] ARIA labels are correct for RTL context

---

## 18. Performance

- [ ] No layout shift on page load
- [ ] No FOUC (flash of unstyled content) related to RTL
- [ ] CSS transitions are smooth

---

## Issue Reporting

When you find an RTL bug, document:
1. **Page/Component**: Where did you find the bug?
2. **Language**: Which language/direction was active?
3. **Expected**: What should it look like?
4. **Actual**: What did you see instead?
5. **Screenshot**: Attach if possible
6. **Browser/Platform**: Browser and OS details

---

## Sign-Off

Before marking RTL implementation complete, verify:

- [ ] All checklist items pass
- [ ] All major modules tested
- [ ] Mixed content cases verified
- [ ] Print/PDF exports work
- [ ] Language switching works both ways
- [ ] No broken UI elements remain