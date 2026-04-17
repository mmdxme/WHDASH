# Treasury Translation Keys Reference

## Overview

Treasury module translations cover all 8 supported languages with complete RTL support for Arabic and Persian.

## Languages Supported

| Code | Language | Direction |
|------|----------|----------|
| en | English | LTR |
| fa | Persian/Farsi | RTL |
| ar | Arabic | RTL |
| ru | Russian | LTR |
| hi | Hindi | LTR |
| es | Spanish | LTR |
| zh | Chinese | LTR |
| de | German | LTR |

## Translation File Location

`treasury_translations.py` - Contains all treasury-specific translation keys

## Key Categories

### Dashboard & Overview
| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| treasury_dashboard | Treasury Dashboard | لوحة الخزينة | داشبورد خزانه |
| executive_dashboard | Executive Liquidity | لوحة السيولة التنفيذية | داشبورد نقدینگی اجرایی |
| cash_position | Cash Position | موقع النقدية | موقعیت نقدی |
| cash_management | Cash Management | إدارة النقدية | مدیریت نقدی |

### Cash Position
| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| total_cash | Total Cash | إجمالي النقدية | کل نقدی |
| opening_balance | Opening Balance | الرصيد الافتتاحي | مانده افتتاحی |
| closing_balance | Closing Balance | الرصيد الختامي | مانده نهایی |
| available_balance | Available Balance | الرصيد المتاح | مانده قابل دسترس |

### Cash Flow Forecast
| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| forecast | Forecast | توقعات | پیش‌بینی |
| inflow_forecast | Inflow Forecast | توقعات الواردات | پیش‌بینی ورودی |
| outflow_forecast | Outflow Forecast | توقعات الصادرات | پیش‌بینی خروجی |
| scenario | Scenario | سيناريو | سناریو |

### Collections
| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| collections | Collections | التحصيلات | وصولی‌ها |
| expected_receipts | Expected Receipts | المستلمات المتوقعة | وصولی‌های مورد انتظار |
| overdue_collections | Overdue Collections | التحصيلات المتأخرة | وصولی‌های معوق |
| collection_risk | Collection Risk | مخاطر التحصيل | ریسک وصولی |

### Payments
| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| payments | Payments | المدفوعات | پرداخت‌ها |
| due_payments | Due Payments | المدفوعات المستحقة | پرداخت‌های سررسید شده |
| payment_calendar | Payment Calendar | تقويم المدفوعات | تقویم پرداخت |
| cash_requirement | Cash Requirement | متطلب النقدية | نیاز نقدی |

### Transfers
| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| transfers | Transfers | التحويلات | انتقال‌ها |
| bank_transfers | Bank Transfers | تحويلات بنكية | انتقال‌های بانکی |
| transfer_request | Transfer Request | طلب تحويل | درخواست انتقال |
| approve_transfer | Approve Transfer | الموافقة على التحويل | تأیید انتقال |

### Petty Cash
| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| petty_cash | Petty Cash | النقدية الصغيرة | تنخواه |
| top_up | Top Up | تعبئة | شارژ |
| withdraw | Withdraw | سحب | برداشت |
| float_amount | Float Amount | مبلغ العائمة | مبلغ شناور |

### Liquidity
| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| liquidity | Liquidity | السيولة | نقدینگی |
| liquidity_gaps | Liquidity Gaps | فجوات السيولة | شکاف‌های نقدینگی |
| minimum_required | Minimum Required | الحد الأدنى المطلوب | حداقل مورد نیاز |
| shortfall | Shortfall | العجز | کسری |

### Alerts & Controls
| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| alerts | Alerts | التنبيهات | هشدارها |
| treasury_controls | Treasury Controls | ضوابط الخزينة | کنترل‌های خزانه |
| severity | Severity | الخطورة | شدت |
| resolve | Resolve | حل | حل |

### Status Terms
| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| pending | Pending | قيد الانتظار | در انتظار |
| approved | Approved | موافق عليه | تأیید شده |
| rejected | Rejected | مرفوض | رد شده |
| completed | Completed | مكتمل | تکمیل شده |
| active | Active | نشط | فعال |
| inactive | Inactive | غير نشط | غیرفعال |

### Action Terms
| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| view | View | عرض | مشاهده |
| edit | Edit | تعديل | ویرایش |
| delete | Delete | حذف | حذف |
| create | Create | إنشاء | ایجاد |
| save | Save | حفظ | ذخیره |
| cancel | Cancel | إلغاء | لغو |
| approve | Approve | موافقة | تأیید |
| reject | Reject | رفض | رد |

## RTL Support

### Layout Considerations
- Tables flip direction in RTL
- Charts maintain orientation
- Amounts remain LTR (numerical)
- Labels flip to right-aligned

### Mixed Content
- Persian/Arabic + English amounts: amounts stay LTR
- Account numbers: always LTR
- Dates: locale-appropriate format

## Usage in Templates

```jinja2
{{ _('treasury_dashboard') }}
{{ _('cash_position') }}
{{ _('collections') }}
```

## Adding New Translations

1. Add key to English ('en') section
2. Add translations to all 8 language sections
3. Test RTL layout
4. Verify date/number formatting

## Notes

- All financial amounts use monospace font
- Dates format per locale
- Currency codes remain unchanged
- Account numbers stay LTR
