# Demand Planning Translation Keys

## Overview

The WHDASH Demand Planning module supports 8 languages with full RTL/LTR support. This document lists all translation keys and their translations.

## Supported Languages

| Code | Language | Direction | Status |
|------|----------|-----------|--------|
| en | English | LTR | Primary |
| ar | Arabic | RTL | Full |
| fa | Persian/Farsi | RTL | Full |
| ru | Russian | LTR | Partial |
| zh | Chinese | LTR | Partial |
| es | Spanish | LTR | Partial |
| hi | Hindi | LTR | Partial |
| de | German | LTR | Partial |

## Translation Key Structure

Keys follow hierarchical naming:
```
category_subcategory_key_name
```

Example: `forecast_center`, `demand_planning`, `mape_wape_error`

## All Translation Keys

### Core Demand Planning

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| demand_planning | Demand Planning | تخطيط الطلب | برنامه‌ریزی تقاضا |
| demand_overview | Demand Overview | نظرة عامة على الطلب | نمای کلی تقاضا |
| forecast_center | Forecast Center | مركز التوقعات | مرکز پیش‌بینی |
| forecast_control_tower | Forecast Control Tower | برج التحكم | برج کنترل پیش‌بینی |
| statistical_forecasting | Statistical Forecasting | التوقع الإحصائي | پیش‌بینی آماری |
| baseline_forecast | Baseline Forecast | التوقع الأساسي | پیش‌بینی پایه |
| forecast_by_item | Forecast by Item | التوقع حسب الصنف | پیش‌بینی بر اساس کالا |
| forecast_by_warehouse | Forecast by Warehouse | التوقع حسب المستودع | پیش‌بینی بر اساس انبار |
| forecast_by_brand | Forecast by Brand | التوقع حسب العلامة | پیش‌بینی بر اساس برند |
| forecast_by_customer_segment | Forecast by Customer Segment | التوقع حسب شريحة العملاء | پیش‌بینی بر اساس بخش مشتری |

### Forecasting Methods

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| moving_average | Moving Average | المتوسط المتحرك | میانگین متحرک |
| weighted_moving_average | Weighted Moving Average | المتوسط المتحرك المرجح | میانگین متحرک وزنی |
| exponential_smoothing | Exponential Smoothing | التمهيد الأسي | هموارسازی نمایی |
| double_exponential | Double Exponential (Holt) | الأسي المزدوج (هولت) | نمایی دوگانه (هولت) |
| holt_winters | Holt-Winters Seasonal | هولت-وينترز الموسمي | هولت-وينترز فصلی |
| trend_analysis | Trend Analysis | تحليل الاتجاه | تحلیل روند |
| seasonality_analysis | Seasonality Analysis | تحليل الموسمية | تحلیل فصلی |
| model_comparison | Model Comparison | مقارنة النماذج | مقایسه مدل‌ها |
| forecast_model_selection | Forecast Model Selection | اختيار نموذج التوقع | انتخاب مدل پیش‌بینی |
| forecast_regeneration | Forecast Regeneration | إعادة توليد التوقع | بازتولید پیش‌بینی |
| statistical_reports | Statistical Reports | التقارير الإحصائية | گزارشات آماری |
| auto_select | Auto (Best Fit) | تلقائي (أفضل ملاءمة) | خودکار (بهترین تناسب) |

### Forecast Versions

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| forecast_versions | Forecast Versions | إصدارات التوقع | نسخه‌های پیش‌بینی |
| draft_versions | Draft Versions | مسودات | پیش‌نویس‌ها |
| approved_versions | Approved Versions | الإصدارات المعتمدة | نسخه‌های تأیید شده |
| frozen_versions | Frozen Versions | الإصدارات المجمدة | نسخه‌های ثابت |
| historical_snapshots | Historical Snapshots | لقطات تاريخية | تصاویر تاریخی |
| compare_versions | Compare Versions | مقارنة الإصدارات | مقایسه نسخه‌ها |
| publish_version | Publish Version | نشر الإصدار | انتشار نسخه |
| clone_version | Clone Version | استنساخ الإصدار | کپی نسخه |
| version_audit_log | Version Audit Log | سجل تدقيق الإصدار | سابقه حسابرسی نسخه |
| version_name | Version Name | اسم الإصدار | نام نسخه |
| version_number | Version Number | رقم الإصدار | شماره نسخه |
| is_baseline | Is Baseline | هل هو أساسي | آیا پایه است |
| is_frozen | Is Frozen | مجمد | ثابت شده |
| published_at | Published At | نشر في | منتشر شده در |
| published_by | Published By | نشر بواسطة | منتشر شده توسط |

### Forecast Overrides

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| forecast_overrides | Forecast Overrides | تجاوزات التوقع | اصلاحات پیش‌بینی |
| manual_overrides | Manual Overrides | التجاوزات اليدوية | اصلاحات دستی |
| bulk_overrides | Bulk Overrides | التجاوزات بالجملة | اصلاحات عمده |
| planner_notes | Planner Notes | ملاحظات المخطط | یادداشت‌های برنامه‌ریز |
| sales_input | Sales Input | إدخال المبيعات | ورودی فروش |
| marketing_input | Marketing Input | إدخال التسويق | ورودی بازاریابی |
| override_approval_queue | Override Approval Queue | قائمة موافقة التجاوز | صف تأیید اصلاحات |
| override_history | Override History | سجل التجاوز | سابقه اصلاحات |
| override_reports | Override Reports | تقارير التجاوز | گزارشات اصلاحات |
| override_reason | Override Reason | سبب التجاوز | دلیل اصلاح |
| override_type | Override Type | نوع التجاوز | نوع اصلاح |
| override_quantity | Override Quantity | الكمية المتجاوزة | مقدار اصلاحی |
| original_quantity | Original Quantity | الكمية الأصلية | مقدار اصلی |
| final_quantity | Final Quantity | الكمية النهائية | مقدار نهایی |

### Demand Drivers

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| demand_drivers | Demand Drivers | محددات الطلب | عوامل تقاضا |
| promotions_impact | Promotions Impact | تأثير العروض | تأثیر تبلیغات |
| marketing_campaign_impact | Marketing Campaign Impact | تأثير الحملة التسويقية | تأثیر کمپین بازاریابی |
| seasonality_calendar | Seasonality Calendar | تقويم الموسمية | تقویم فصلی |
| holidays_events | Holidays & Events | العطلات والأحداث | تعطیلات و رویدادها |
| price_change_impact | Price Change Impact | تأثير تغير السعر | تأثیر تغییر قیمت |
| customer_demand_patterns | Customer Demand Patterns | أنماط طلب العملاء | الگوهای تقاضای مشتری |
| external_factor_notes | External Factor Notes | ملاحظات العوامل الخارجية | یادداشت‌های عوامل خارجی |
| driver_reports | Driver Reports | تقارير المحددات | گزارشات عوامل |
| driver_name | Driver Name | اسم المحدد | نام عامل |
| driver_type | Driver Type | نوع المحدد | نوع عامل |
| impact_factor | Impact Factor | عامل التأثير | ضریب تأثیر |
| promotion_name | Promotion Name | اسم العرض | نام تبلیغ |
| promotion_type | Promotion Type | نوع العرض | نوع تبلیغ |
| expected_uplift | Expected Uplift | الرفع المتوقع | افزایش مورد انتظار |
| actual_uplift | Actual Uplift | الرفع الفعلي | افزایش واقعی |
| budget_allocated | Budget Allocated | الميزانية المخصصة | بودجه تخصیص یافته |
| budget_spent | Budget Spent | الميزانية المنفقة | بودجه صرف شده |
| holiday_name | Holiday Name | اسم العطلة | نام تعطیل |
| holiday_date | Holiday Date | تاريخ العطلة | تاریخ تعطیل |
| holiday_type | Holiday Type | نوع العطلة | نوع تعطیل |
| region | Region | المنطقة | منطقه |
| affected_days | Affected Days | الأيام المتأثرة | روزهای متاثر |

### Consensus Planning

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| consensus_planning | Consensus Planning | التخطيط التوافقي | برنامه‌ریزی اجماعی |
| sales_forecast_input | Sales Forecast Input | إدخال توقع المبيعات | ورودی پیش‌بینی فروش |
| planner_consensus_view | Planner Consensus View | عرض توافق المخطط | نمای اجماع برنامه‌ریز |
| management_review | Management Review | مراجعة الإدارة | بازنگری مدیریت |
| approved_consensus_forecast | Approved Consensus Forecast | توقع التوافق المعتمد | پیش‌بینی اجماعی تأیید شده |
| forecast_review_meetings | Forecast Review Meetings | اجتماعات مراجعة التوقع | جلسات بازنگری پیش‌بینی |
| disagreement_review | Disagreement Review | مراجعة الخلاف | بازنگری اختلاف |
| collaboration_notes | Collaboration Notes | ملاحظات التعاون | یادداشت‌های همکاری |
| consensus_reports | Consensus Reports | تقارير التوافق | گزارشات اجماع |
| consensus_value | Consensus Value | قيمة التوافق | مقدار اجماع |
| disagreement_level | Disagreement Level | مستوى الخلاف | سطح اختلاف |
| sales_confidence | Sales Confidence | ثقة المبيعات | اطمینان فروش |
| planner_confidence | Planner Confidence | ثقة المخطط | اطمینان برنامه‌ریز |
| marketing_confidence | Marketing Confidence | ثقة التسويق | اطمینان بازاریابی |
| meeting_title | Meeting Title | عنوان الاجتماع | عنوان جلسه |
| meeting_date | Meeting Date | تاريخ الاجتماع | تاریخ جلسه |
| attendees | Attendees | الحاضرون | شرکت‌کنندگان |
| decisions | Decisions | القرارات | تصمیمات |
| action_items | Action Items | عناصر الإجراء | اقدامات |

### Accuracy & Analytics

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| forecast_accuracy | Forecast Accuracy | دقة التوقع | دقت پیش‌بینی |
| bias_analysis | Bias Analysis | تحليل التحيز | تحلیل سوگیری |
| mape_wape_error | MAPE / WAPE / Error Metrics | مقاييس MAPE / WAPE / الخطأ | معیارهای MAPE / WAPE / خطا |
| forecast_vs_actual | Forecast vs Actual | التوقع مقابل الفعلي | پیش‌بینی در برابر واقعی |
| accuracy_by_item | Accuracy by Item | الدقة حسب الصنف | دقت بر اساس کالا |
| accuracy_by_planner | Accuracy by Planner | الدقة حسب المخطط | دقت بر اساس برنامه‌ریز |
| accuracy_by_warehouse | Accuracy by Warehouse | الدقة حسب المستودع | دقت بر اساس انبار |
| exception_heatmap | Exception Heatmap | خريطة استثناءات الحرارة | نقشه حرارتی استثناها |
| accuracy_reports | Accuracy Reports | تقارير الدقة | گزارشات دقت |
| mape | MAPE | MAPE | MAPE |
| wape | WAPE | WAPE | WAPE |
| mae | MAE | MAE | MAE |
| rmse | RMSE | RMSE | RMSE |
| bias | Bias | التحيز | سوگیری |
| tracking_signal | Tracking Signal | إشارة التتبع | سیگنال پیگیری |
| theil_u | Theil's U | U ثيل | Theil's U |
| over_forecast | Over Forecast | فوق التوقع | پیش‌بینی اضافی |
| under_forecast | Under Forecast | تحت التوقع | پیش‌بینی کمتر |
| forecast_health_score | Forecast Health Score | درجة صحة التوقع | امتیاز سلامت پیش‌بینی |

### Demand Sensing

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| demand_sensing | Demand Sensing | استشعار الطلب | حس تقاضا |
| recent_demand_signal | Recent Demand Signal View | عرض إشارة الطلب الأخيرة | نمای سیگنال تقاضای اخیر |
| short_term_demand | Short-Term Demand Adjustments | تعديلات الطلب قصيرة المدى | تنظیمات تقاضای کوتاه‌مدت |
| demand_volatility_alerts | Demand Volatility Alerts | تنبيهات تقلب الطلب | هشدارهای نوسان تقاضا |
| fast_moving_items | Fast-Moving Items Review | مراجعة الأصناف سريعة الحركة | بررسی کالاهای پرسرعت |
| sudden_drop_spike | Sudden Drop / Spike Detection | اكتشاف الانخفاض / الارتفاع المفاجئ | تشخیص سقوط / جهش ناگهانی |
| short_horizon_board | Short-Horizon Planner Board | لوحة المخطط للأفق القصير | تابلوی برنامه‌ریز کوتاه‌مدت |
| demand_signal_reports | Demand Signal Reports | تقارير إشارة الطلب | گزارشات سیگنال تقاضا |
| demand_signal | Demand Signal | إشارة الطلب | سیگنال تقاضا |
| signal_direction | Signal Direction | اتجاه الإشارة | جهت سیگنال |
| volatility_score | Volatility Score | درجة التقلب | امتیاز نوسان |
| anomaly_score | Anomaly Score | درجة الشذوذ | امتیاز ناهنجاری |
| z_score | Z-Score | Z-Score | Z-Score |
| coefficient_variation | Coefficient of Variation | معامل التغير | ضریب تغییر |

### Scenario Planning

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| scenario_planning | Scenario Planning | تخطيط السيناريو | برنامه‌ریزی سناریو |
| what_if_scenarios | What-if Scenarios | سيناريوهات ماذا لو | سناریوهای what-if |
| promotion_scenario | Promotion Scenario | سيناريو العرض | سناریو تبلیغ |
| demand_spike_scenario | Demand Spike Scenario | سيناريو ارتفاع الطلب | سناریو جهش تقاضا |
| demand_drop_scenario | Demand Drop Scenario | سيناريو انخفاض الطلب | سناریو سقوط تقاضا |
| stock_constraint_scenario | Stock Constraint Scenario | سيناريو قيود المخزون | سناریو محدودیت موجودی |
| supplier_delay_impact | Supplier Delay Impact | تأثير تأخير المورد | تأثیر تاخیر تامین‌کننده |
| budget_constrained_plan | Budget-Constrained Demand Plan | خطة الطلب المقيدة بالميزانية | برنامه تقاضای محدود به بودجه |
| scenario_comparison | Scenario Comparison | مقارنة السيناريوهات | مقایسه سناریوها |
| scenario_reports | Scenario Reports | تقارير السيناريو | گزارشات سناریو |
| scenario_type | Scenario Type | نوع السيناريو | نوع سناریو |
| scenario_assumptions | Scenario Assumptions | افتراضات السيناريو | فرضیات سناریو |
| scenario_impact | Scenario Impact | تأثير السيناريو | تأثیر سناریو |
| base_value | Base Value | القيمة الأساسية | مقدار پایه |
| scenario_value | Scenario Value | قيمة السيناريو | مقدار سناریو |
| impact_value | Impact Value | قيمة التأثير | مقدار تأثیر |
| impact_percent | Impact % | نسبة التأثير | درصد تأثیر |

### Exceptions & Alerts

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| exceptions_alerts | Exceptions & Alerts | الاستثناءات والتنبيهات | استثناها و هشدارها |
| forecast_deviation_alerts | Forecast Deviation Alerts | تنبيهات انحراف التوقع | هشدارهای انحراف پیش‌بینی |
| accuracy_breach_alerts | Accuracy Breach Alerts | تنبيهات اختراق الدقة | هشدارهای نقض دقت |
| high_volatility_items | High Volatility Items | الأصناف عالية التقلب | کالاهای نوسان بالا |
| high_bias_items | High Bias Items | الأصناف عالية التحيز | کالاهای سوگیری بالا |
| critical_demand_watchlist | Critical Demand Watchlist | قائمة مراقبة الطلب الحرجة | لیست مراقبت تقاضای بحرانی |
| planner_exception_queue | Planner Exception Queue | قائمة استثناءات المخطط | صف استثناهای برنامه‌ریز |
| escalation_queue | Escalation Queue | قائمة التصعيد | صف تصعید |
| alert_rules | Alert Rules | قواعد التنبيه | قوانین هشدار |
| exception_reports | Exception Reports | تقارير الاستثناء | گزارشات استثنا |

### SCM Linkage

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| scm_linkage | SCM Linkage | ربط سلسلة التوريد | پیوند SCM |
| forecast_replenishment_view | Forecast-to-Replenishment View | عرض التوقع إلى التعبئة | نمای پیش‌بینی به تامین |
| purchase_suggestions_impact | Forecast Impact on Purchase Suggestions | تأثير التوقع على اقتراحات الشراء | تأثیر پیش‌بینی بر پیشنهادات خرید |
| coverage_impact | Coverage Impact | تأثير التغطية | تأثیر پوشش |
| branch_refill_risk | Branch Refill Risk | خطر إعادة تعبئة الفرع | خطر شارژ مجدد شعبه |
| warehouse_stock_stress | Warehouse Stock Stress View | عرض ضغط مخزون المستودع | نمای فشار موجودی انبار |
| supply_risk_forecast | Supply Risk from Forecast | خطر التوريد من التوقع | ریسک تامین از پیش‌بینی |
| linked_scm_reports | Linked SCM Reports | تقارير SCM المرتبطة | گزارشات SCM مرتبط |

### Sales & Marketing Linkage

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| sales_marketing | Sales & Marketing | المبيعات والتسويق | فروش و بازاریابی |
| sales_trends | Sales Trends | اتجاهات المبيعات | روندهای فروش |
| campaign_demand_impact | Campaign Demand Impact | تأثير الحملة على الطلب | تأثیر کمپین بر تقاضا |
| lead_opportunity_signals | Lead / Opportunity Demand Signals | إشارات الطلب من العملاء المتوقعين | سیگنال‌های تقاضای سرنخ/فرصت |
| customer_segment_demand | Customer Segment Demand View | عرض طلب شريحة العملاء | نمای تقاضای بخش مشتری |
| promotion_uplift_review | Promotion Uplift Review | مراجعة رفع العرض | بازنگری افزایش تبلیغ |
| demand_collaboration_reports | Demand Collaboration Reports | تقارير تعاون الطلب | گزارشات همکاری تقاضا |

### Workflow & Approvals

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| approvals_workflow | Approvals & Workflow | الموافقات وسير العمل | تأییدات و گردش کار |
| approval_rules | Approval Rules | قواعد الموافقة | قوانین تأیید |
| pending_approvals | Pending Approvals | الموافقات المعلقة | تأییدات معلق |
| delegations | Delegations | التفويضات | تفویض‌ها |
| sla_policies | SLA Policies | سياسات SLA | سیاست‌های SLA |
| approval_history | Approval History | سجل الموافقة | سابقه تأیید |
| approval_level | Approval Level | مستوى الموافقة | سطح تأیید |
| approver_role | Approver Role | دور الموافق | نقش تأییدکننده |
| bypass_role | Bypass Role | دور التجاوز | نقش عبور |
| response_hours | Response Hours | ساعات الاستجابة | ساعات پاسخ |
| resolution_hours | Resolution Hours | ساعات الحل | ساعات رفع |
| escalation_hours | Escalation Hours | ساعات التصعيد | ساعات تصعید |
| threshold_value | Threshold Value | قيمة العتبة | مقدار آستانه |

### Settings

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| settings | Settings | الإعدادات | تنظیمات |
| forecast_settings | Forecast Settings | إعدادات التوقع | تنظیمات پیش‌بینی |
| model_settings | Model Settings | إعدادات النموذج | تنظیمات مدل |
| accuracy_settings | Accuracy Settings | إعدادات الدقة | تنظیمات دقت |
| override_rules | Override Rules | قواعد التجاوز | قوانین اصلاح |
| consensus_workflow_settings | Consensus Workflow Settings | إعدادات سير عمل التوافق | تنظیمات گردش کار اجماع |
| alert_thresholds | Alert Thresholds | عتبات التنبيه | آستانه‌های هشدار |
| export_settings | Export Settings | إعدادات التصدير | تنظیمات صادرات |
| branch_entity_settings | Branch/Entity Settings | إعدادات الفرع / الكيان | تنظیمات شعبه/موجودیت |
| notification_settings | Notification Settings | إعدادات الإشعارات | تنظیمات اعلان‌ها |
| translation_label_settings | Translation / Label Settings | إعدادات الترجمة / التسميات | تنظیمات ترجمه/برچسب |

### Common Terms

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| view | View | عرض | مشاهده |
| edit | Edit | تعديل | ویرایش |
| delete | Delete | حذف | حذف |
| approve | Approve | موافقة | تأیید |
| reject | Reject | رفض | رد |
| submit | Submit | إرسال | ارسال |
| save | Save | حفظ | ذخیره |
| cancel | Cancel | إلغاء | لغو |
| close | Close | إغلاق | بستن |
| search | Search | بحث | جستجو |
| filter | Filter | تصفية | فیلتر |
| export | Export | تصدير | صادرات |
| refresh | Refresh | تحديث | بروزرسانی |
| generate | Generate | توليد | تولید |
| apply | Apply | تطبيق | اعمال |
| resolve | Resolve | حل | حل |
| escalate | Escalate | تصعيد | تصعید |
| acknowledge | Acknowledge | إقرار | تاءیید |
| freeze | Freeze | تجميد | ثابت کردن |
| publish | Publish | نشر | انتشار |
| clone | Clone | استنساخ | کپی |
| compare | Compare | مقارنة | مقایسه |
| select_all | Select All | اختيار الكل | انتخاب همه |
| select_item | Select Item | اختيار الصنف | انتخاب کالا |
| no_data | No Data Available | لا توجد بيانات | داده‌ای موجود نیست |
| loading | Loading... | جاري التحميل... | در حال بارگذاری... |
| error | Error | خطأ | خطا |
| success | Success | نجاح | موفقیت |
| warning | Warning | تحذير | هشدار |
| info | Info | معلومات | اطلاعات |

### Status Values

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| status | Status | الحالة | وضعیت |
| draft | Draft | مسودة | پیش‌نویس |
| frozen | Frozen | مجمد | ثابت |
| published | Published | منشور | منتشر شده |
| approved | Approved | معتمد | تأیید شده |
| rejected | Rejected | مرفوض | رد شده |
| pending | Pending | معلق | در انتظار |
| open | Open | مفتوح | باز |
| closed | Closed | مغلق | بسته |
| active | Active | نشط | فعال |
| inactive | Inactive | غير نشط | غیرفعال |

### Severity Values

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| critical | Critical | حرج | بحرانی |
| high | High | مرتفع | بالا |
| medium | Medium | متوسط | متوسط |
| low | Low | منخفض | پایین |

### Metrics & KPIs

| Key | English | Arabic | Persian |
|-----|---------|--------|---------|
| total_quantity | Total Quantity | الكمية الإجمالية | مقدار کل |
| total_items | Total Items | إجمالي الأصناف | تعداد کل کالاها |
| items_measured | Items Measured | الأصناف المقاسة | کالاهای اندازه‌گیری شده |
| avg_mape | Avg MAPE | متوسط MAPE | میانگین MAPE |
| over_forecast | Over Forecast | فوق التوقع | پیش‌بینی اضافی |
| under_forecast | Under Forecast | تحت التوقع | پیش‌بینی کمتر |
| items | Items | أصناف | کالاها |
| total_qty | Total Qty | الكمية الإجمالية | مقدار کل |
| created_by | Created By | أنشئ بواسطة | ایجاد شده توسط |
| created | Created | أنشئ | ایجاد شده |
| actions | Actions | إجراءات | اقدامات |

### Navigation Menu

| Key | English |
|-----|---------|
| control_tower | Forecast Control Tower |
| statistical | Statistical |
| versions | Versions |
| overrides | Overrides |
| sensing | Sensing |
| scenarios | Scenarios |
| consensus | Consensus |
| accuracy | Accuracy |
| approvals | Approvals |
| settings | Settings |

## RTL/LTR Considerations

### Layout Direction
- All flex/grid layouts should use `dir="auto"` for mixed content
- Use logical properties (margin-inline-start vs margin-left)
- Icons should not flip for RTL
- Charts maintain left-to-right orientation

### Number Formatting
- Numbers remain LTR even in RTL context
- Item codes, dates use standard format
- Percentages use standard format with RTL label

### Table Handling
```css
[dir="rtl"] .data-table th {
    text-align: right;
}
[dir="rtl"] .data-table td {
    text-align: right;
}
```

### Form Alignment
```css
[dir="rtl"] input, [dir="rtl"] select {
    text-align: right;
}
```

## Translation Implementation

Translations are implemented in `translations.py`:

```python
TRANSLATIONS = {
    'en': {
        'forecast_center': 'Forecast Center',
        'forecast_accuracy': 'Forecast Accuracy',
        # ...
    },
    'ar': {
        'forecast_center': 'مركز التوقعات',
        'forecast_accuracy': 'دقة التوقع',
        # ...
    },
    'fa': {
        'forecast_center': 'مرکز پیش‌بینی',
        'forecast_accuracy': 'دقت پیش‌بینی',
        # ...
    },
}
```

## Usage in Templates

```html
<!-- Standard usage -->
<h1>{{ t.forecast_center }}</h1>

<!-- With default fallback -->
<p>{{ t.no_data|default('No data available') }}</p>

<!-- With translation in JavaScript -->
<script>
const labels = {
    forecastCenter: "{{ t.forecast_center }}",
    accuracy: "{{ t.forecast_accuracy }}"
};
</script>
```
