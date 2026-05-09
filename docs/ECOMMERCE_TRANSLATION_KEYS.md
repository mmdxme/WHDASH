# Marketing Automation Translation Keys

## Overview

The Marketing Automation module is fully multilingual, supporting 8 languages with RTL compatibility. All user-facing strings use the translation function `t()` and are defined in the central `translations.py` file.

## Supported Languages

| Code | Language | Direction | Status |
|------|----------|-----------|--------|
| en | English | LTR | Primary |
| ar | Arabic | RTL | Supported |
| fa | Persian/Farsi | RTL | Supported |
| de | German | LTR | Supported |
| es | Spanish | LTR | Supported |
| fr | French | LTR | Supported |
| ru | Russian | LTR | Supported |
| zh | Chinese | LTR | Supported |
| tr | Turkish | LTR | Supported |

## Translation Key Categories

### Core Marketing Terms

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| marketing | Marketing | التسويق | بازاریابی |
| marketing_dashboard | Marketing Dashboard | لوحة التسويق | داشبورد بازاریابی |
| campaigns | Campaigns | الحملات | کمپین‌ها |
| leads | Leads | العملاء المحتملين | سرنخ‌ها |
| channels | Channels | القنوات | کانال‌ها |
| content | Content | المحتوى | محتوا |
| offers | Offers | العروض | پیشنهادات |
| budgets | Budgets | الميزانيات | بودجه‌ها |

### Lead Scoring Keys

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| lead_scoring | Lead Scoring | نقاط العملاء | امتیاز سرنخ |
| scoring_rules | Scoring Rules | قواعد النقاط | قوانین امتیاز |
| demographic | Demographic | ديموغرافي | جمعیت‌شناختی |
| behavioral | Behavioral | السلوكي | رفتاری |
| engagement | Engagement | التفاعل | مشارکت |
| score_grade | Score Grade | درجة النقاط | درجه امتیاز |
| mql_count | MQLs | مؤهلات التسويق | سرنخ‌های واجد شرایط |
| sql_count | SQLs | مؤهلات المبيعات | سرنخ‌های آماده فروش |

### Journey Keys

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| nurture_journeys | Nurture Journeys | رحلات العملاء | مسیرهای پرورش |
| journey_builder | Journey Builder | بناء الرحلة | سازنده مسیر |
| entry_trigger | Entry Trigger | محفز الدخول | محرک ورود |
| step_actions | Step Actions | إجراءات الخطوة | اقدامات مرحله |
| wait_delay | Wait/Delay | الانتظار/التأخير | انتظار/تأخیر |
| branching_logic | Branching Logic | منطق التفرع | منطق شاخه‌ای |
| journey_performance | Journey Performance | أداء الرحلة | عملکرد مسیر |

### A/B Testing Keys

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| ab_tests | A/B Tests | اختبارات A/B | تست A/B |
| subject_line | Subject Line | سطر الموضوع | عنوان موضوع |
| cta | Call to Action | دعوة للعمل | دعوت به اقدام |
| variant | Variant | المتغير | متغیر |
| control | Control | الضبط | کنترل |
| challenger | Challenger | المتحدي | چالش‌برانگیز |
| uplift | Uplift | التحسن | بهبود |
| confidence | Confidence | الثقة | اطمینان |

### Channel Keys

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| email | Email | البريد الإلكتروني | ایمیل |
| sms | SMS | الرسائل | پیامک |
| whatsapp | WhatsApp | واتساب | واتساپ |
| push | Push Notification | الإشعار | نوتیفیکیشن |
| delivered | Delivered | تم التسليم | تحویل داده شده |
| opened | Opened | تم الفتح | باز شده |
| clicked | Clicked | تم النقر | کلیک شده |
| bounced | Bounced | مرتجع | برگشتی |
| unsubscribed | Unsubscribed | إلغاء الاشتراك | لغو اشتراک |

### Funnel & Attribution Keys

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| funnel | Funnel | القمع | قیف |
| attribution | Attribution | الانتساب | انتساب |
| first_touch | First Touch | اللمسة الأولى | اولین لمس |
| last_touch | Last Touch | اللمسة الأخيرة | آخرین لمس |
| linear | Linear | الخطي | خطی |
| time_decay | Time Decay | تناقص الوقت | کاهش زمانی |
| position_based | Position Based | القائم على الموقف | مبتنی بر موقعیت |

### Status Keys

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| draft | Draft | مسودة | پیش‌نویس |
| active | Active | نشط | فعال |
| paused | Paused | متوقف | متوقف |
| completed | Completed | مكتمل | تکمیل شده |
| cancelled | Cancelled | ملغى | لغو شده |
| pending | Pending | قيد الانتظار | در انتظار |
| approved | Approved | موافق عليه | تأیید شده |
| rejected | Rejected | مرفوض | رد شده |

### Action Keys

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| create | Create | إنشاء | ایجاد |
| edit | Edit | تعديل | ویرایش |
| delete | Delete | حذف | حذف |
| save | Save | حفظ | ذخیره |
| cancel | Cancel | إلغاء | لغو |
| approve | Approve | موافقة | تأیید |
| reject | Reject | رفض | رد |
| export | Export | تصدير | صادرات |
| download | Download | تنزيل | دانلود |
| filter | Filter | تصفية | فیلتر |
| search | Search | بحث | جستجو |

## Implementation

### Template Usage
```html
<h1>{{ t('lead_scoring', 'Lead Scoring') }}</h1>
<span>{{ t('active', 'Active') }}</span>
```

### Python Usage
```python
flash(t('campaign_created', 'Campaign created successfully.'), 'success')
```

### RTL Handling
Templates automatically handle RTL:
```html
<html lang="{{ 'fa' if user_preferences.direction_resolved == 'rtl' else 'en' }}"
      dir="{{ user_preferences.direction_resolved }}">
```

## Translation Best Practices

1. **Use Descriptive Keys** - Keys should describe the content, not just `text_001`
2. **Include Fallbacks** - Always provide fallback text in `t(key, fallback)`
3. **RTL Considerations** - Test layouts in RTL mode
4. **Pluralization** - Handle plural forms for different languages
5. **Date/Number Formats** - Respect locale-specific formatting
6. **Length Variations** - Allow for text expansion/contraction

## Adding New Translations

### 1. Python File
Add to the `TRANSLATIONS` dict in `translations.py`:
```python
'new_key': 'English Value',
'new_key_ar': 'Arabic Value',
'new_key_fa': 'Persian Value',
```

### 2. Template Files
Use the translation function:
```html
<span>{{ t('new_key', 'Default English') }}</span>
```

### 3. JavaScript (Future)
For dynamic content, use the JS translation API.

## Character Limits

| Context | Max Characters | Notes |
|---------|---------------|-------|
| Menu Labels | 30 | Short, concise |
| Button Labels | 20 | Action-focused |
| Table Headers | 25 | Abbreviate if needed |
| Form Labels | 40 | Descriptive |
| Status Badges | 15 | Short status |
| Notifications | 100 | Complete message |

## RTL Guidelines

### Layout Mirroring
- Left margins → Right margins
- Right margins → Left margins
- Text alignment flips
- Icons that imply direction flip

### Icons
- Use symmetric icons when possible
- Avoid directional arrows in navigation
- Check all icon placements in RTL

### Tables
- Column order reverses
- Sort indicators flip
- Pagination flips
