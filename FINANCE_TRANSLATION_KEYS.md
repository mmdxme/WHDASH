# Finance Translation Keys Guide

## Overview

This document provides a comprehensive list of all translation keys used in the WHDASH Financial Management module. All keys follow the naming convention `finance_<category>_<concept>`.

## Translation Structure

The system supports 8 languages:
- **English (en)** - Default
- **Persian/Farsi (fa)**
- **Arabic (ar)**
- **Russian (ru)**
- **Hindi (hi)**
- **Spanish (es)**
- **Chinese (zh)**
- **German (de)**

---

## 1. Navigation Keys

| Key | English | Arabic | Description |
|-----|---------|--------|-------------|
| `finance_nav_dashboard` | Finance Dashboard | لوحة القيادة المالية | Main finance dashboard |
| `finance_nav_chart_of_accounts` | Chart of Accounts | دليل الحسابات | COA navigation |
| `finance_nav_journal_entries` | Journal Entries | قيود اليومية | Journal entries nav |
| `finance_nav_ar_invoices` | AR Invoices | فواتير الذمم المدينة | Receivables nav |
| `finance_nav_ar_receipts` | AR Receipts | سندات القبض | Customer receipts nav |
| `finance_nav_ap_bills` | AP Bills | فواتير الذمم الدائنة | Payables nav |
| `finance_nav_ap_payments` | AP Payments | مدفوعات الموردين | Supplier payments nav |
| `finance_nav_fixed_assets` | Fixed Assets | الأصول الثابتة | Asset management nav |
| `finance_nav_depreciation` | Depreciation | الإهلاك | Depreciation nav |
| `finance_nav_budgets` | Budgets | الميزانيات | Budget management nav |
| `finance_nav_bank_recon` | Bank Reconciliation | التسوية المصرفية | Bank rec nav |
| `finance_nav_tax` | Tax | الضريبة | Tax reports nav |
| `finance_nav_reports` | Reports | التقارير | All reports nav |
| `finance_nav_settings` | Finance Settings | إعدادات المالية | Module settings |

---

## 2. Module Labels

### 2.1 General Module Terms

| Key | English | Arabic | Russian | Hindi |
|-----|---------|--------|---------|-------|
| `finance_module_name` | Financial Management | الإدارة المالية | Управление финансами | वित्तीय प्रबंधन |
| `finance_module_description` | Comprehensive accounting and financial control | المحاسبة والتحكم المالي الشامل | Комплексный учет и финансовый контроль | व्यापक लेखा और वित्तीय नियंत्रण |
| `finance_general_ledger` | General Ledger | دفتر الأستاذ العام | Главная книга | खाता बही |
| `finance_subledger` | Subledger | دفتر فرعي | Субкнига | उप-खाता बही |
| `finance_trial_balance` | Trial Balance | ميزان المراجعة | Оборотная ведомость | परीक्षण शेष |
| `finance_balance_sheet` | Balance Sheet | الميزانية العمومية | Бухгалтерский баланс | तुला पत्र |
| `finance_income_statement` | Income Statement | قائمة الدخل | Отчет о прибылях и убытках | आय विवरण |
| `finance_cash_flow` | Cash Flow Statement | قائمة التدفقات النقدية | Отчет о движении денежных средств | नकदी प्रवाह विवरण |

### 2.2 Account Types

| Key | English | Arabic |
|-----|---------|--------|
| `finance_account_type_asset` | Asset | أصل |
| `finance_account_type_liability` | Liability | مسؤولية |
| `finance_account_type_equity` | Equity | حقوق الملكية |
| `finance_account_type_revenue` | Revenue | الإيرادات |
| `finance_account_type_cogs` | Cost of Goods Sold | تكلفة البضاعة المباعة |
| `finance_account_type_expense` | Expense | مصروف |
| `finance_account_type_other_income` | Other Income | دخل آخر |
| `finance_account_type_other_expense` | Other Expense | مصروف آخر |

---

## 3. Chart of Accounts

| Key | English | Arabic | Description |
|-----|---------|--------|-------------|
| `finance_coa_title` | Chart of Accounts | دليل الحسابات | Page title |
| `finance_coa_account_code` | Account Code | رقم الحساب | Column header |
| `finance_coa_account_name` | Account Name | اسم الحساب | Column header |
| `finance_coa_account_type` | Account Type | نوع الحساب | Column header |
| `finance_coa_parent_account` | Parent Account | الحساب الأب | Column header |
| `finance_coa_is_control_account` | Control Account | حساب контрол | Checkbox label |
| `finance_coa_is_posting_allowed` | Allow Posting | السماح بالترحيل | Checkbox label |
| `finance_coa_is_cost_center_allowed` | Cost Center Allowed | مركز التكلفة مسموح | Checkbox label |
| `finance_coa_add_account` | Add Account | إضافة حساب | Button |
| `finance_coa_edit_account` | Edit Account | تعديل الحساب | Button |
| `finance_coa_delete_account` | Delete Account | حذف الحساب | Button |
| `finance_coa_view_account` | View Account | عرض الحساب | Button |
| `finance_coa_account_moved` | Account moved successfully | تم نقل الحساب | Success message |
| `finance_coa_account_created` | Account created successfully | تم إنشاء الحساب | Success message |
| `finance_coa_account_updated` | Account updated successfully | تم تحديث الحساب | Success message |
| `finance_coa_account_deleted` | Account deleted successfully | تم حذف الحساب | Success message |
| `finance_coa_cannot_delete_account` | Cannot delete account with transactions | لا يمكن حذف حساب لديه حركات | Error message |
| `finance_coa_confirm_delete` | Are you sure you want to delete this account? | هل أنت متأكد من حذف هذا الحساب؟ | Confirmation |

---

## 4. Journal Entries

| Key | English | Arabic |
|-----|---------|--------|
| `finance_je_title` | Journal Entries | قيود اليومية |
| `finance_je_new` | New Journal Entry | قيود يومية جديدة |
| `finance_je_edit` | Edit Journal Entry | تعديل القيد اليومي |
| `finance_je_view` | View Journal Entry | عرض القيد اليومي |
| `finance_je_journal_number` | Journal Number | رقم القيد |
| `finance_je_journal_type` | Journal Type | نوع القيد |
| `finance_je_journal_date` | Journal Date | تاريخ القيد |
| `finance_je_description` | Description | الوصف |
| `finance_je_reference` | Reference | المرجع |
| `finance_je_source_module` | Source Module | الوحدة المصدر |
| `finance_je_status` | Status | الحالة |
| `finance_je_period` | Period | الفترة |
| `finance_je_total_debit` | Total Debit | إجمالي مدين |
| `finance_je_total_credit` | Total Credit | إجمالي دائن |
| `finance_je_balance` | Balance | الرصيد |
| `finance_je_unbalanced` | Journal is not balanced | القيد غير متوازن | Error |
| `finance_je_must_have_lines` | Journal must have at least 2 lines | القيد يجب أن يحتوي سطرين على الأقل | Error |
| `finance_je_posted` | Posted | مرحلة | Status |
| `finance_je_draft` | Draft | مسودة | Status |
| `finance_je_pending` | Pending Approval | قيد الانتظار | Status |
| `finance_je_post` | Post Journal | ترحيل القيد | Button |
| `finance_je_unpost` | Unpost Journal | إلغاء ترحيل | Button |
| `finance_je_approve` | Approve | موافقة | Button |
| `finance_je_reverse` | Reverse | عكس | Button |
| `finance_je_copy` | Copy Journal | نسخ القيد | Button |
| `finance_je_line_number` | Line # | السطر | Column |
| `finance_je_account` | Account | الحساب | Column |
| `finance_je_debit` | Debit | مدين | Column |
| `finance_je_credit` | Credit | دائن | Column |
| `finance_je_cost_center` | Cost Center | مركز التكلفة | Column |
| `finance_je_add_line` | Add Line | إضافة سطر | Button |
| `finance_je_remove_line` | Remove Line | حذف سطر | Button |

### 4.1 Journal Types

| Key | English | Arabic |
|-----|---------|--------|
| `finance_jtype_sales` | Sales | مبيعات |
| `finance_jtype_payment` | Payment | دفع |
| `finance_jtype_purchase` | Purchase | مشتريات |
| `finance_jtype_receipt` | Receipt | سند قبض |
| `finance_jtype_utility` | Utility | مرافق |
| `finance_jtype_payroll` | Payroll | كشوف المرتبات |
| `finance_jtype_bank_charge` | Bank Charge | رسوم بنكية |
| `finance_jtype_depreciation` | Depreciation | إهلاك |
| `finance_jtype_year_end` | Year End | نهاية السنة |
| `finance_jtype_adjustment` | Adjustment | تسوية |
| `finance_jtype_tax` | Tax | ضريبة |
| `finance_jtype_transfer` | Transfer | تحويل |

---

## 5. Accounts Receivable (AR)

### 5.1 AR Invoices

| Key | English | Arabic |
|-----|---------|--------|
| `finance_ar_invoices_title` | AR Invoices | فواتير الذمم المدينة |
| `finance_ar_invoice_new` | New Invoice | فاتورة جديدة |
| `finance_ar_invoice_edit` | Edit Invoice | تعديل الفاتورة |
| `finance_ar_invoice_view` | View Invoice | عرض الفاتورة |
| `finance_ar_invoice_number` | Invoice Number | رقم الفاتورة |
| `finance_ar_invoice_date` | Invoice Date | تاريخ الفاتورة |
| `finance_ar_invoice_due_date` | Due Date | تاريخ الاستحقاق |
| `finance_ar_invoice_customer` | Customer | العميل |
| `finance_ar_invoice_subtotal` | Subtotal | المجموع الفرعي |
| `finance_ar_invoice_tax` | Tax Amount | مبلغ الضريبة |
| `finance_ar_invoice_total` | Total Amount | المبلغ الإجمالي |
| `finance_ar_invoice_amount_paid` | Amount Paid | المبلغ المدفوع |
| `finance_ar_invoice_amount_due` | Amount Due | المبلغ المستحق |
| `finance_ar_invoice_currency` | Currency | العملة |
| `finance_ar_invoice_status` | Status | الحالة |
| `finance_ar_invoice_post` | Post Invoice | ترحيل الفاتورة |
| `finance_ar_invoice_void` | Void Invoice | إبطال الفاتورة |
| `finance_ar_invoice_print` | Print Invoice | طباعة الفاتورة |
| `finance_ar_invoice_email` | Email Invoice | إرسال الفاتورة |
| `finance_ar_invoice_add_payment` | Add Payment | إضافة دفعة |
| `finance_ar_invoice_credit_note` | Credit Note | إشعار دائن |
| `finance_ar_invoice_status_posted` | Posted | مرحلة |
| `finance_ar_invoice_status_paid` | Paid | مدفوعة |
| `finance_ar_invoice_status_overdue` | Overdue | متأخرة |
| `finance_ar_invoice_status_partial` | Partially Paid | مدفوعة جزئياً |
| `finance_ar_invoice_status_void` | Voided | ملغاة |

### 5.2 AR Receipts

| Key | English | Arabic |
|-----|---------|--------|
| `finance_ar_receipts_title` | Customer Receipts | سندات القبض |
| `finance_ar_receipt_new` | New Receipt | سند قبض جديد |
| `finance_ar_receipt_number` | Receipt Number | رقم السند |
| `finance_ar_receipt_date` | Receipt Date | تاريخ السند |
| `finance_ar_receipt_amount` | Amount Received | المبلغ المستلم |
| `finance_ar_receipt_payment_method` | Payment Method | طريقة الدفع |
| `finance_ar_receipt_reference` | Reference Number | رقم المرجع |
| `finance_ar_receipt_bank` | Bank Account | الحساب البنكي |
| `finance_ar_receipt_apply` | Apply to Invoice | تطبيق على فاتورة |
| `finance_ar_receipt_discount` | Discount Allowed | الخصم المسموح |
| `finance_ar_receipt_unapplied` | Unapplied Amount | المبلغ غير المطبق |

### 5.3 AR Aging

| Key | English | Arabic |
|-----|---------|--------|
| `finance_ar_aging_title` | AR Aging Report | تقرير أعمار الذمم المدينة |
| `finance_ar_aging_current` | Current | الحالي |
| `finance_ar_aging_1_30` | 1-30 Days | 1-30 يوم |
| `finance_ar_aging_31_60` | 31-60 Days | 31-60 يوم |
| `finance_ar_aging_61_90` | 61-90 Days | 61-90 يوم |
| `finance_ar_aging_90_plus` | 90+ Days | أكثر من 90 يوم |
| `finance_ar_aging_total` | Total Outstanding | إجمالي المستحق |
| `finance_ar_aging_customer` | Customer | العميل |

---

## 6. Accounts Payable (AP)

### 6.1 AP Bills

| Key | English | Arabic |
|-----|---------|--------|
| `finance_ap_bills_title` | AP Bills | فواتير الموردين |
| `finance_ap_bill_new` | New Bill | فاتورة جديدة |
| `finance_ap_bill_edit` | Edit Bill | تعديل الفاتورة |
| `finance_ap_bill_view` | View Bill | عرض الفاتورة |
| `finance_ap_bill_number` | Bill Number | رقم الفاتورة |
| `finance_ap_bill_date` | Bill Date | تاريخ الفاتورة |
| `finance_ap_bill_due_date` | Due Date | تاريخ الاستحقاق |
| `finance_ap_bill_supplier` | Supplier | المورد |
| `finance_ap_bill_subtotal` | Subtotal | المجموع الفرعي |
| `finance_ap_bill_tax` | Tax Amount | مبلغ الضريبة |
| `finance_ap_bill_total` | Total Amount | المبلغ الإجمالي |
| `finance_ap_bill_amount_paid` | Amount Paid | المبلغ المدفوع |
| `finance_ap_bill_amount_due` | Amount Due | المبلغ المستحق |
| `finance_ap_bill_status` | Status | الحالة |
| `finance_ap_bill_post` | Post Bill | ترحيل الفاتورة |
| `finance_ap_bill_void` | Void Bill | إبطال الفاتورة |
| `finance_ap_bill_payment` | Record Payment | تسجيل الدفع |
| `finance_ap_bill_debit_note` | Debit Note | إشعار مدين |
| `finance_ap_bill_status_posted` | Posted | مرحلة |
| `finance_ap_bill_status_paid` | Paid | مدفوعة |
| `finance_ap_bill_status_overdue` | Overdue | متأخرة |
| `finance_ap_bill_status_partial` | Partially Paid | مدفوعة جزئياً |

### 6.2 AP Payments

| Key | English | Arabic |
|-----|---------|--------|
| `finance_ap_payments_title` | Supplier Payments | مدفوعات الموردين |
| `finance_ap_payment_new` | New Payment | دفعة جديدة |
| `finance_ap_payment_number` | Payment Number | رقم الدفع |
| `finance_ap_payment_date` | Payment Date | تاريخ الدفع |
| `finance_ap_payment_amount` | Amount Paid | المبلغ المدفوع |
| `finance_ap_payment_method` | Payment Method | طريقة الدفع |
| `finance_ap_payment_reference` | Reference | المرجع |
| `finance_ap_payment_bank` | Bank Account | الحساب البنكي |
| `finance_ap_payment_apply` | Apply to Bill | تطبيق على فاتورة |
| `finance_ap_payment_discount` | Discount Received | الخصم المستلم |

### 6.3 AP Aging

| Key | English | Arabic |
|-----|---------|--------|
| `finance_ap_aging_title` | AP Aging Report | تقرير أعمار الذمم الدائنة |
| `finance_ap_aging_current` | Current | الحالي |
| `finance_ap_aging_1_30` | 1-30 Days | 1-30 يوم |
| `finance_ap_aging_31_60` | 31-60 Days | 31-60 يوم |
| `finance_ap_aging_61_90` | 61-90 Days | 61-90 يوم |
| `finance_ap_aging_90_plus` | 90+ Days | أكثر من 90 يوم |
| `finance_ap_aging_total` | Total Outstanding | إجمالي المستحق |
| `finance_ap_aging_supplier` | Supplier | المورد |

---

## 7. Fixed Assets

| Key | English | Arabic |
|-----|---------|--------|
| `finance_asset_title` | Fixed Assets | الأصول الثابتة |
| `finance_asset_register` | Asset Register | سجل الأصول |
| `finance_asset_new` | New Asset | أصل جديد |
| `finance_asset_edit` | Edit Asset | تعديل الأصل |
| `finance_asset_view` | View Asset | عرض الأصل |
| `finance_asset_code` | Asset Code | رمز الأصل |
| `finance_asset_name` | Asset Name | اسم الأصل |
| `finance_asset_category` | Category | الفئة |
| `finance_asset_acquisition_date` | Acquisition Date | تاريخ الاقتناء |
| `finance_asset_capitalization_date` | Capitalization Date | تاريخ رسملة |
| `finance_asset_cost` | Acquisition Cost | تكلفة الاقتناء |
| `finance_asset_useful_life` | Useful Life (Years) | العمر الإنتاجي (سنوات) |
| `finance_asset_salvage_value` | Salvage Value | قيمة الخردة |
| `finance_asset_depreciation_method` | Depreciation Method | طريقة الإهلاك |
| `finance_asset_accumulated_depr` | Accumulated Depreciation | الإهلاك التراكمي |
| `finance_asset_net_book_value` | Net Book Value | القيمة الدفترية الصافية |
| `finance_asset_status` | Status | الحالة |
| `finance_asset_location` | Location | الموقع |
| `finance_asset_custodian` | Custodian | الحارس |
| `finance_asset_serial_number` | Serial Number | الرقم التسلسلي |
| `finance_asset_depreciation` | Depreciation | الإهلاك |
| `finance_asset_disposal` | Disposal | التخلص |
| `finance_asset_transfer` | Transfer | نقل |
| `finance_asset_revaluation` | Revaluation | إعادة تقييم |
| `finance_asset_status_active` | Active | نشط |
| `finance_asset_status_disposed` | Disposed | تم التخلص |
| `finance_asset_status_transferred` | Transferred | منقول |
| `finance_asset_status_suspended` | Suspended | موقوف |

### 7.1 Depreciation

| Key | English | Arabic |
|-----|---------|--------|
| `finance_depreciation_runs` | Depreciation Runs | تشغيلات الإهلاك |
| `finance_depreciation_run_new` | New Depreciation Run | تشغيل إهلاك جديد |
| `finance_depreciation_run_number` | Run Number | رقم التشغيل |
| `finance_depreciation_run_date` | Run Date | تاريخ التشغيل |
| `finance_depreciation_total` | Total Depreciation | إجمالي الإهلاك |
| `finance_depreciation_asset_count` | Asset Count | عدد الأصول |
| `finance_depreciation_post` | Post Depreciation | ترحيل الإهلاك |
| `finance_depreciation_method_straight` | Straight Line | القسط الثابت |
| `finance_depreciation_method_declining` | Declining Balance | الرصيد المتناقص |
| `finance_depreciation_method_units` | Units of Production | وحدات الإنتاج |
| `finance_depreciation_schedule` | Depreciation Schedule | جدول الإهلاك |

---

## 8. Budgets

| Key | English | Arabic |
|-----|---------|--------|
| `finance_budget_title` | Budgets | الميزانيات |
| `finance_budget_list` | Budget List | قائمة الميزانيات |
| `finance_budget_new` | New Budget | ميزانية جديدة |
| `finance_budget_edit` | Edit Budget | تعديل الميزانية |
| `finance_budget_view` | View Budget | عرض الميزانية |
| `finance_budget_number` | Budget Number | رقم الميزانية |
| `finance_budget_name` | Budget Name | اسم الميزانية |
| `finance_budget_fiscal_year` | Fiscal Year | السنة المالية |
| `finance_budget_status` | Status | الحالة |
| `finance_budget_total` | Total Budget | إجمالي الميزانية |
| `finance_budget_approved` | Approved | معتمد |
| `finance_budget_draft` | Draft | مسودة |
| `finance_budget_rejected` | Rejected | مرفوض |
| `finance_budget_approve` | Approve Budget | اعتماد الميزانية |
| `finance_budget_reject` | Reject Budget | رفض الميزانية |
| `finance_budget_revisions` | Budget Revisions | مراجعات الميزانية |
| `finance_budget_vs_actual` | Budget vs Actual | الميزانية مقابل الفعلي |
| `finance_budget_variance` | Variance | التباين |
| `finance_budget_favorable` | Favorable | لصالح |
| `finance_budget_unfavorable` | Unfavorable | ضد |

---

## 9. Bank & Cash

| Key | English | Arabic |
|-----|---------|--------|
| `finance_bank_accounts` | Bank Accounts | الحسابات البنكية |
| `finance_bank_account_new` | New Bank Account | حساب بنكي جديد |
| `finance_bank_name` | Bank Name | اسم البنك |
| `finance_bank_account_name` | Account Name | اسم الحساب |
| `finance_bank_account_number` | Account Number | رقم الحساب |
| `finance_bank_account_type` | Account Type | نوع الحساب |
| `finance_bank_iban` | IBAN | IBAN |
| `finance_bank_swift` | SWIFT Code | رمز SWIFT |
| `finance_bank_balance` | Current Balance | الرصيد الحالي |
| `finance_bank_opening_balance` | Opening Balance | الرصيد الافتتاحي |
| `finance_cash_account` | Cash Account | حساب النقدية |
| `finance_cash_transfer` | Cash Transfer | تحويل نقدي |
| `finance_reconciliation` | Bank Reconciliation | التسوية المصرفية |
| `finance_recon_new` | New Reconciliation | تسوية جديدة |
| `finance_recon_statement_date` | Statement Date | تاريخ الكشف |
| `finance_recon_bank_balance` | Bank Balance | رصيد البنك |
| `finance_recon_book_balance` | Book Balance | رصيد الدفتر |
| `finance_recon_difference` | Difference | الفرق |
| `finance_recon_matched` | Matched | مطابق |
| `finance_recon_unmatched` | Unmatched | غير مطابق |
| `finance_recon_deposits_transit` | Deposits in Transit | إيداعات قيد الانتظار |
| `finance_recon_outstanding_checks` | Outstanding Checks | شيكات معلقة |

---

## 10. Tax

| Key | English | Arabic |
|-----|---------|--------|
| `finance_tax_codes` | Tax Codes | أكواد الضريبة |
| `finance_tax_code_new` | New Tax Code | كود ضريبي جديد |
| `finance_tax_code` | Tax Code | كود الضريبة |
| `finance_tax_name` | Tax Name | اسم الضريبة |
| `finance_tax_rate` | Tax Rate | معدل الضريبة |
| `finance_tax_type` | Tax Type | نوع الضريبة |
| `finance_tax_vat` | VAT | ضريبة القيمة المضافة |
| `finance_tax_vat_standard` | Standard VAT | VAT قياسي |
| `finance_tax_vat_zero` | Zero Rated | نسبة صفر |
| `finance_tax_vat_exempt` | Exempt | معفى |
| `finance_tax_output` | Output Tax | ضريبة المخرجات |
| `finance_tax_input` | Input Tax | ضريبة المدخلات |
| `finance_tax_payable` | Tax Payable | الضريبة المستحقة |
| `finance_tax_receivable` | Tax Receivable | الضريبة المستحقة对我们 |
| `finance_tax_report` | Tax Report | تقرير الضريبة |
| `finance_vat_return` | VAT Return | إقرار VAT |
| `finance_withholding_tax` | Withholding Tax | ضريبة الاستقطاع |

---

## 11. Cost Centers & Profit Centers

| Key | English | Arabic |
|-----|---------|--------|
| `finance_cost_centers` | Cost Centers | مراكز التكلفة |
| `finance_cost_center_new` | New Cost Center | مركز تكلفة جديد |
| `finance_cost_center_code` | Cost Center Code | رمز مركز التكلفة |
| `finance_cost_center_name` | Cost Center Name | اسم مركز التكلفة |
| `finance_cost_center_manager` | Manager | المدير |
| `finance_cost_center_budget` | Allocated Budget | الميزانية المخصصة |
| `finance_profit_centers` | Profit Centers | مراكز الربح |
| `finance_profit_center_new` | New Profit Center | مركز ربح جديد |
| `finance_profit_center_code` | Profit Center Code | رمز مركز الربح |
| `finance_profit_center_name` | Profit Center Name | اسم مركز الربح |
| `finance_profit_center_segment` | Business Segment | القطاع التجاري |

---

## 12. Fiscal Years & Periods

| Key | English | Arabic |
|-----|---------|--------|
| `finance_fiscal_years` | Fiscal Years | السنوات المالية |
| `finance_fiscal_year_new` | New Fiscal Year | سنة مالية جديدة |
| `finance_fiscal_year_name` | Year Name | اسم السنة |
| `finance_fiscal_year_start` | Start Date | تاريخ البدء |
| `finance_fiscal_year_end` | End Date | تاريخ الانتهاء |
| `finance_fiscal_periods` | Fiscal Periods | الفترات المالية |
| `finance_period_name` | Period Name | اسم الفترة |
| `finance_period_number` | Period Number | رقم الفترة |
| `finance_period_status` | Period Status | حالة الفترة |
| `finance_period_open` | Open | مفتوح |
| `finance_period_closed` | Closed | مغلق |
| `finance_period_locked` | Locked | مقفل |
| `finance_period_close` | Close Period | إغلاق الفترة |
| `finance_period_reopen` | Reopen Period | إعادة فتح الفترة |

---

## 13. Reports

| Key | English | Arabic |
|-----|---------|--------|
| `finance_report_trial_balance` | Trial Balance | ميزان المراجعة |
| `finance_report_balance_sheet` | Balance Sheet | الميزانية العمومية |
| `finance_report_income_statement` | Income Statement | قائمة الدخل |
| `finance_report_cash_flow` | Cash Flow Statement | قائمة التدفقات النقدية |
| `finance_report_ar_aging` | AR Aging | تقرير أعمار الذمم المدينة |
| `finance_report_ap_aging` | AP Aging | تقرير أعمار الذمم الدائنة |
| `finance_report_vat` | VAT Report | تقرير VAT |
| `finance_report_asset_register` | Asset Register | سجل الأصول |
| `finance_report_depreciation` | Depreciation Schedule | جدول الإهلاك |
| `finance_report_budget_vs_actual` | Budget vs Actual | الميزانية مقابل الفعلي |
| `finance_report_bank_recon` | Bank Reconciliation | التسوية المصرفية |
| `finance_report_journal_audit` | Journal Audit Trail | تدقيق قيود اليومية |
| `finance_report_generate` | Generate Report | إنشاء التقرير |
| `finance_report_export_pdf` | Export to PDF | تصدير إلى PDF |
| `finance_report_export_excel` | Export to Excel | تصدير إلى Excel |
| `finance_report_export_csv` | Export to CSV | تصدير إلى CSV |
| `finance_report_schedule` | Schedule Report | جدولة التقرير |
| `finance_report_parameters` | Report Parameters | معاملات التقرير |
| `finance_report_date_range` | Date Range | نطاق التاريخ |
| `finance_report_as_of_date` | As of Date | حتى تاريخ |
| `finance_report_period` | Period | الفترة |

---

## 14. Common Actions & Status

| Key | English | Arabic |
|-----|---------|--------|
| `finance_action_save` | Save | حفظ |
| `finance_action_cancel` | Cancel | إلغاء |
| `finance_action_delete` | Delete | حذف |
| `finance_action_edit` | Edit | تعديل |
| `finance_action_view` | View | عرض |
| `finance_action_add` | Add | إضافة |
| `finance_action_remove` | Remove | إزالة |
| `finance_action_search` | Search | بحث |
| `finance_action_filter` | Filter | تصفية |
| `finance_action_export` | Export | تصدير |
| `finance_action_import` | Import | استيراد |
| `finance_action_print` | Print | طباعة |
| `finance_action_post` | Post | ترحيل |
| `finance_action_unpost` | Unpost | إلغاء الترحيل |
| `finance_action_approve` | Approve | اعتماد |
| `finance_action_reject` | Reject | رفض |
| `finance_action_submit` | Submit | إرسال |
| `finance_action_back` | Back | رجوع |
| `finance_action_next` | Next | التالي |
| `finance_action_previous` | Previous | السابق |
| `finance_action_refresh` | Refresh | تحديث |
| `finance_action_close` | Close | إغلاق |

### 14.1 Status Messages

| Key | English | Arabic |
|-----|---------|--------|
| `finance_status_success` | Operation completed successfully | تمت العملية بنجاح |
| `finance_status_error` | An error occurred | حدث خطأ |
| `finance_status_warning` | Warning | تحذير |
| `finance_status_info` | Information | معلومات |
| `finance_status_loading` | Loading... | جاري التحميل... |
| `finance_status_saving` | Saving... | جاري الحفظ... |
| `finance_status_processing` | Processing... | جاري المعالجة... |
| `finance_status_no_data` | No data available | لا توجد بيانات |
| `finance_status_confirm_delete` | Are you sure you want to delete? | هل أنت متأكد من الحذف؟ |
| `finance_status_unsaved_changes` | You have unsaved changes | لديك تغييرات غير محفوظة |

---

## 15. Accounting Terminology Standards

### 15.1 Arabic Accounting Terms (UAE/GAAP)

| English | Arabic | Transliteration |
|---------|--------|-----------------|
| Debit | مدين | Madin |
| Credit | دائن | Dain |
| Journal Entry | قيد يومية | Qaid Yawmiyah |
| Ledger | دفتر |Daftar |
| Chart of Accounts | دليل الحسابات | Dalil Al Hisab |
| Trial Balance | ميزان المراجعة | Mizan Al Murajaha |
| Balance Sheet | الميزانية العمومية | Al Mizanah Al Ammah |
| Income Statement | قائمة الدخل | Qaimah Al Dakhil |
| Asset | أصل | Asl |
| Liability | مسؤولية | Masuliyah |
| Equity | حقوق الملكية | Huquq Al Milkiyah |
| Revenue | إيرادات | Iradat |
| Expense | مصروف | Masroof |
| Accounts Receivable | ذمم مدينة | Dhamim Madinah |
| Accounts Payable | ذمم دائنة | Dhamim Dainah |
| Cost of Goods Sold | تكلفة البضاعة المباعة | Taklif Al Badaya |
| Depreciation | إهلاك | Ihkal |
| Accumulated Depreciation | إهلاك تراكمي | Ihkal Tarakumi |
| Net Book Value | القيمة الدفترية الصافية | Al Qimah Al Dafatariyah Al Safiyah |
| VAT | ضريبة القيمة المضافة | Dharibat Qimat Al Ziadah |

### 15.2 Russian Accounting Terms

| English | Russian | Transliteration |
|---------|---------|-----------------|
| Debit | Дебет | Debet |
| Credit | Кредит | Kredit |
| Journal Entry | Журнал проводок | Zhurnal provodok |
| Balance Sheet | Бухгалтерский баланс | Bukhgalterskiy balans |
| Assets | Активы | Aktiv |
| Liabilities | Обязательства | Obyazatelstva |
| Equity | Капитал | Kapitel |
| Revenue | Доходы | Dokhody |
| Expenses | Расходы | Raskhody |
| Accounts Receivable | Дебиторская задолженность | Debitorskaya zadolzhennost |
| Accounts Payable | Кредиторская задолженность | Kreditorskaya zadolzhennost |

---

## 16. Adding New Translation Keys

When adding new features to the Finance module:

1. Add keys to `translations.py` following the pattern:
   ```python
   'finance_feature_key': 'English text',
   ```

2. Use underscore_case naming:
   - `finance_<module>_<concept>_<detail>`

3. Always provide translations for all 8 languages when possible

4. Keys should be descriptive and follow existing patterns

5. Group related keys together by prefix

---

## 17. Current Translation Coverage

| Language | Coverage | Status |
|----------|----------|--------|
| English (en) | 100% | Complete |
| Arabic (ar) | ~40% | Partial - requires completion |
| Persian/Farsi (fa) | ~25% | Partial |
| Russian (ru) | ~15% | Minimal |
| Hindi (hi) | ~15% | Minimal |
| Spanish (es) | ~10% | Minimal |
| Chinese (zh) | ~10% | Minimal |
| German (de) | ~10% | Minimal |

### Priority Languages for Finance Module

1. **English (en)** - Default
2. **Arabic (ar)** - Primary localization (UAE market)
3. **Russian (ru)** - Growing market
4. **Hindi (hi)** - Large user base

---

## 18. Formatting Standards

### Currency Formatting
```python
# Use locale-aware formatting
# AED: 1,234,567.89
# USD: $1,234,567.89
# EUR: €1,234,567.89
```

### Date Formatting
```python
# Use ISO format for storage: YYYY-MM-DD
# Display format by locale:
# en: 04/15/2026
# ar: 15/04/2026
# de: 15.04.2026
```

### Number Formatting
```python
# Use thousand separators
# 1,000,000.00 (en)
# 1.000.000,00 (de)
# 1 000 000,00 (fr)
```

---

## Appendix: Key Naming Convention

| Prefix | Category | Example |
|--------|----------|---------|
| `finance_nav_` | Navigation | `finance_nav_dashboard` |
| `finance_coa_` | Chart of Accounts | `finance_coa_account_code` |
| `finance_je_` | Journal Entries | `finance_je_journal_number` |
| `finance_ar_` | AR/Invoices | `finance_ar_invoice_total` |
| `finance_ap_` | AP/Bills | `finance_ap_bill_number` |
| `finance_asset_` | Fixed Assets | `finance_asset_code` |
| `finance_depreciation_` | Depreciation | `finance_depreciation_run` |
| `finance_budget_` | Budgets | `finance_budget_total` |
| `finance_bank_` | Bank/Cash | `finance_bank_account` |
| `finance_tax_` | Tax | `finance_tax_rate` |
| `finance_report_` | Reports | `finance_report_generate` |
| `finance_status_` | Status Messages | `finance_status_success` |
| `finance_action_` | Action Buttons | `finance_action_save` |
| `finance_period_` | Period/Fiscal | `finance_period_open` |
