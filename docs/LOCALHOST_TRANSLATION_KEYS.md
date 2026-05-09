# MMDx Localhost Translation Keys

## Translation System Overview

The MMDx platform supports **8 languages** with full RTL (right-to-left) support for Arabic and Persian.

---

## 1. Supported Languages

| Code | Language | Native Name | Direction | Status |
|------|----------|-------------|-----------|--------|
| `en` | English | English | LTR | Primary |
| `ar` | Arabic | العربية | RTL | Full |
| `fa` | Persian/Farsi | فارسی | RTL | Full |
| `ru` | Russian | Русский | LTR | Full |
| `hi` | Hindi | हिन्दी | LTR | Full |
| `es` | Spanish | Español | LTR | Full |
| `zh` | Chinese | 中文 | LTR | Full |
| `de` | German | Deutsch | LTR | Full |

---

## 2. Translation File Location

**File:** `translations.py`

**Structure:**

```python
TRANSLATIONS = {
    'en': {
        'key': 'English text',
        ...
    },
    'ar': {
        'key': 'النص العربي',
        ...
    },
    'fa': {
        'key': 'متن فارسی',
        ...
    }
}
```

---

## 3. Translation Usage

### 3.1 In Python (Routes)

```python
from translations import get_translation

# Simple usage
title = get_translation(lang, 'dashboard_title', 'Dashboard')

# Using the t() shortcut in route functions
def t(key, default=None):
    lang = session.get('language', 'en')
    return get_translation(lang, key, default)

# Usage
page_title = t('shipments_list', 'Shipments')
```

### 3.2 In Templates

```jinja2
{# Simple translation #}
{{ t('app_name', 'MMDx') }}

{# With explicit key #}
{{ t('dashboard', 'Dashboard') }}

{# In base.html (available globally) #}
<title>{{ t('app_name', 'Enterprise') }} - {{ title }}</title>
```

---

## 4. Core Translation Keys

### 4.1 Navigation

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| `app_name` | MMDx | MMDx | MMDx |
| `app_subtitle` | Enterprise Hub | لوحة القيادة | داشبورد |
| `dashboard` | Dashboard | لوحة القيادة | داشبورد |
| `search_placeholder` | Search... | بحث... | جستجو... |
| `profile` | Profile | الملف الشخصي | پروفایل |
| `settings` | Settings | الإعدادات | تنظیمات |
| `logout` | Logout | تسجيل الخروج | خروج |
| `login` | Login | تسجيل الدخول | ورود |

### 4.2 Common Actions

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| `save` | Save | حفظ | ذخیره |
| `cancel` | Cancel | إلغاء | لغو |
| `delete` | Delete | حذف | حذف |
| `edit` | Edit | تعديل | ویرایش |
| `create` | Create | إنشاء | ایجاد |
| `view` | View | عرض | مشاهده |
| `search` | Search | بحث | جستجو |
| `filter` | Filter | تصفية | فیلتر |
| `reset` | Reset | إعادة تعيين | بازنشانی |
| `export` | Export | تصدير | صادرات |
| `import` | Import | استيراد | واردات |
| `submit` | Submit | إرسال | ارسال |
| `close` | Close | إغلاق | بستن |
| `back` | Back | رجوع | بازگشت |
| `next` | Next | التالى | بعدی |
| `previous` | Previous | السابق | قبلی |
| `confirm` | Confirm | تأكيد | تأیید |
| `refresh` | Refresh | تحديث | بروزرسانی |

### 4.3 Status Labels

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| `status_active` | Active | نشط | فعال |
| `status_inactive` | Inactive | غير نشط | غیرفعال |
| `status_pending` | Pending | قيد الانتظار | در انتظار |
| `status_approved` | Approved | تمت الموافقة | تأیید شده |
| `status_rejected` | Rejected | مرفوض | رد شده |
| `status_completed` | Completed | مكتمل | تکمیل شده |
| `status_cancelled` | Cancelled | ملغى | لغو شده |
| `status_draft` | Draft | مسودة | پیش‌نویس |

### 4.4 Logistics

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| `shipments` | Shipments | الشحنات | محموله‌ها |
| `trips` | Trips | الرحلات | سفرها |
| `drivers` | Drivers | السائقين | رانندگان |
| `vehicles` | Vehicles | المركبات | وسایل نقلیه |
| `deliveries` | Deliveries | عمليات التسليم | تحویل‌ها |
| `routes` | Routes | المسارات | مسیرها |
| `pod` | POD | إثبات التسليم | رسید تحویل |
| `in_transit` | In Transit | في الطريق | در مسیر |
| `delivered` | Delivered | تم التسليم | تحویل داده شده |
| `failed` | Failed | فشل | ناموفق |

### 4.5 Maintenance

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| `work_orders` | Work Orders | أوامر العمل | درخواست‌های کار |
| `equipment` | Equipment | المعدات | تجهیزات |
| `preventive` | Preventive | وقائي | پیشگیرانه |
| `corrective` | Corrective | تصحيحي | اصلاحی |
| `breakdown` | Breakdown | عطل | خرابی |
| `pm_schedule` | PM Schedule | جدول الصيانة | برنامه تعمیرات |
| `technicians` | Technicians | الفنيين | تکنسین‌ها |

### 4.6 Quality

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| `inspections` | Inspections | عمليات التفتيش | بازرسی‌ها |
| `audits` | Audits | المراجعات | حسابرسی‌ها |
| `non_conformance` | Non-Conformance | عدم المطابقة | عدم انطباق |
| `corrective_action` | Corrective Action | إجراء تصحيحي | اقدام اصلاحی |
| `defects` | Defects | العيوب | نقص‌ها |

### 4.7 Finance

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| `invoices` | Invoices | الفواتير | فاکتورها |
| `payments` | Payments | المدفوعات | پرداخت‌ها |
| `collections` | Collections | التحصيلات | وصولی‌ها |
| `cash_position` | Cash Position | مركز النقد | موجودی نقد |
| `expenses` | Expenses | المصروفات | هزینه‌ها |

### 4.8 Time & Date

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| `today` | Today | اليوم | امروز |
| `yesterday` | Yesterday | أمس | دیروز |
| `this_week` | This Week | هذا الأسبوع | این هفته |
| `this_month` | This Month | هذا الشهر | این ماه |
| `last_month` | Last Month | الشهر الماضي | ماه گذشته |
| `last_7_days` | Last 7 Days | آخر 7 أيام | 7 روز گذشته |
| `last_30_days` | Last 30 Days | آخر 30 يومًا | 30 روز گذشته |
| `custom_range` | Custom Range | نطاق مخصص | بازه سفارشی |

### 4.9 Greetings

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| `good_morning` | Good Morning | صباح الخير | صبح بخیر |
| `good_afternoon` | Good Afternoon | مس الخير | بعدازظهر بخیر |
| `good_evening` | Good Evening | مساء الخير | عصر بخیر |

---

## 5. RTL Considerations

### 5.1 Text Direction

```jinja2
<html dir="{{ 'rtl' if direction == 'rtl' else 'ltr' }}" lang="{{ language }}">
```

### 5.2 CSS Class Helpers

```css
[dir="rtl"] .text-left { text-align: right !important; }
[dir="rtl"] .text-right { text-align: left !important; }
[dir="rtl"] .mr-2 { margin-right: 0; margin-left: 0.5rem; }
[dir="rtl"] .ml-2 { margin-left: 0; margin-right: 0.5rem; }
```

### 5.3 Icon Margins

```css
/* LTR: Icon on left */
/* RTL: Icon on right */
.nav-item {
    flex-direction: row;
}
[dir="rtl"] .nav-item {
    flex-direction: row-reverse;
}
```

### 5.4 Number Formatting

```python
def format_number(value, lang='en'):
    """Format numbers according to locale."""
    if lang == 'ar':
        return value  # Arabic numerals (٠١٢٣٤٥٦٧٨٩)
    elif lang == 'fa':
        return value  # Persian numerals (۰۱۲۳۴۵۶۷۸۹)
    else:
        return f"{value:,}"  # Western numerals with comma
```

### 5.5 Date Formatting

```python
DATE_FORMATS = {
    'en': '%B %d, %Y',      # April 18, 2026
    'ar': '%d %B %Y',       # 18 أبريل 2026
    'fa': '%Y/%m/%d',       # 1405/01/29 (Solar Hijri)
    'zh': '%Y年%m月%d日',   # 2026年04月18日
}
```

---

## 6. Adding New Translations

### 6.1 Add to All Languages

```python
# In translations.py
TRANSLATIONS = {
    'en': {
        'new_key': 'English text',
    },
    'ar': {
        'new_key': 'النص العربي',
    },
    'fa': {
        'new_key': 'متن فارسی',
    },
    # ... all 8 languages
}
```

### 6.2 Use in Template

```jinja2
{{ t('new_key', 'Default fallback text') }}
```

---

## 7. Missing Translation Handling

If a key is missing, the system falls back to English:

```python
def get_translation(lang, key, default=None):
    if lang not in TRANSLATIONS:
        lang = 'en'
    return TRANSLATIONS.get(lang, {}).get(key, default or key)
```

---

## 8. RTL-Specific Patterns

### 8.1 Sidebar Navigation

```css
html[dir="rtl"] .sidebar {
    left: auto;
    right: 0;
    border-right: none;
    border-left: 1px solid var(--border-default);
}
```

### 8.2 Breadcrumb Separator

```jinja2
<i class="fa-solid fa-chevron-right"></i>
<!-- In RTL, use: -->
<i class="fa-solid fa-chevron-left"></i>
```

Or use CSS to handle both:

```css
[dir="rtl"] .breadcrumb-separator i {
    transform: scaleX(-1);
}
```

### 8.3 Progress Bar Direction

```css
/* Keep progress bar direction LTR (left to right) */
.progress-bar {
    direction: ltr;
}
```

---

## 9. Font Selection

| Language | Font | Google Font |
|----------|------|-------------|
| English | Outfit | Yes |
| Arabic | Tajawal | Yes |
| Persian | Vazirmatn | Yes |
| Russian | Noto Sans | Yes |
| Hindi | Noto Sans | Yes |
| Spanish | Outfit | Yes |
| Chinese | Noto Sans SC | Yes |
| German | Outfit | Yes |

---

## 10. Translation Quality Checklist

- [ ] All visible UI text uses translation keys
- [ ] No hardcoded English text visible to users
- [ ] RTL languages render correctly
- [ ] Numbers format correctly per locale
- [ ] Dates format correctly per locale
- [ ] Font selection matches language
- [ ] Icons don't contain text
- [ ] Empty states have translated text
- [ ] Error messages have translated text
- [ ] Tooltips have translated text

---

*Document Version: 1.0*
*Last Updated: April 18, 2026*
