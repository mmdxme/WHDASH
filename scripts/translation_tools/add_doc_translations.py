"""
Script to add comprehensive document management translation keys for all 8 languages.
Run this script to add missing translations.
"""

translations_to_add = {
    # English - added already, but just in case
    'en': {},
    # Persian/Farsi
    'fa': {
        'pending_review': 'در انتظار بررسی',
        'pending_reviews': 'بررسی‌های معوق',
        'doc_pending_review': 'در انتظار بررسی',
        'doc_pending_approval': 'در انتظار تأیید',
        'review_document': 'بررسی سند',
        'approve_document': 'تأیید سند',
        'reject_document': 'رد سند',
        'review_completed': 'بررسی تکمیل شد',
        'approval_recorded': 'تأیید ثبت شد',
        'review_status': 'وضعیت بررسی',
        'review_comments': 'نظرات بررسی',
        'review_score': 'امتیاز بررسی',
        'review_due_date': 'مهلت بررسی',
        'review_requested_at': 'درخواست بررسی',
        'review_completed_at': 'تکمیل بررسی',
        'approval_status': 'وضعیت تأیید',
        'approval_comments': 'نظرات تأیید',
        'rejection_reason': 'دلیل رد',
        'approval_due_date': 'مهلت تأیید',
        'approval_requested_at': 'درخواست تأیید',
        'approval_completed_at': 'تکمیل تأیید',
        'approval_sequence': 'ترتیب تأیید',
        'no_pending_reviews': 'هیچ بررسی معوقی وجود ندارد',
        'no_pending_approvals': 'هیچ تأیید معوقی وجود ندارد',
        'all_caught_up': 'همه کارها انجام شده است!',
        'access_control': 'کنترل دسترسی',
        'doc_access_control': 'کنترل دسترسی',
        'acl_entries': 'ورودی‌های ACL',
        'permission_type': 'نوع مجوز',
        'permission_level': 'سطح مجوز',
        'granted_by': 'اعطا شده توسط',
        'is_inherited': 'ارث‌بری شده',
        'expires_at': 'منقضی می‌شود',
        'add_acl_entry': 'افزودن ورودی ACL',
        'acl_entry_added': 'ورودی ACL اضافه شد',
        'acl_entry_deleted': 'ورودی ACL حذف شد',
        'retention_policies': 'خط مشی‌های نگهداری',
        'doc_retention_policies': 'خط مشی‌های نگهداری',
        'retention_policy': 'خط مشی نگهداری',
        'policy_name': 'نام خط مشی',
        'policy_code': 'کد خط مشی',
        'retention_period_days': 'دوره نگهداری (روز)',
        'retention_basis': 'مبنای نگهداری',
        'archive_before_delete': 'بایگانی قبل از حذف',
        'review_required': 'نیاز به بررسی',
        'review_frequency_days': 'فرکانس بررسی (روز)',
        'document_count': 'اسناد',
        'retention_schedules': 'زمان‌بندی‌های نگهداری',
        'schedule_expires': 'منقضی می‌شود',
        'schedule_status': 'وضعیت',
        'action_taken': 'اقدام انجام شده',
        'policy_created': 'خط مشی ایجاد شد',
        'policy_updated': 'خط مشی به‌روز شد',
        'legal_holds': 'حفظ قانونی',
        'doc_legal_holds': 'حفظ قانونی',
        'legal_hold': 'حفظ قانونی',
        'hold_reference': 'مرجع نگهداری',
        'hold_name': 'نام نگهداری',
        'hold_type': 'نوع نگهداری',
        'legal_case_ref': 'مرجع پرونده حقوقی',
        'hold_status': 'وضعیت نگهداری',
        'hold_active': 'فعال',
        'hold_released': 'آزاد شده',
        'is_permanent': 'دائمی',
        'add_document_to_hold': 'افزودن سند به نگهداری',
        'document_added_to_hold': 'سند به نگهداری قانونی اضافه شد',
        'hold_released_msg': 'نگهداری قانونی آزاد شد',
        'create_legal_hold': 'ایجاد نگهداری قانونی',
        'export_center': 'مرکز صادرات',
        'doc_export_center': 'مرکز صادرات',
        'export_documents': 'صادرات اسناد',
        'export_format': 'فرمت صادرات',
        'export_preset': 'پیش‌تنظیم صادرات',
        'export_presets': 'پیش‌تنظیمات صادرات',
        'preset_name': 'نام پیش‌تنظیم',
        'preset_code': 'کد پیش‌تنظیم',
        'include_columns': 'شامل ستون‌ها',
        'date_range': 'محدوده تاریخ',
        'date_range_start': 'تاریخ شروع',
        'date_range_end': 'تاریخ پایان',
        'export_csv': 'صادرات CSV',
        'export_excel': 'صادرات Excel',
        'export_pdf': 'صادرات PDF',
        'export_json': 'صادرات JSON',
        'text_excel': 'Excel متنی',
        'general_excel': 'Excel عمومی',
        'preset_created': 'پیش‌تنظیم ایجاد شد',
        'usage_count': 'تعداد استفاده',
        'last_used_at': 'آخرین استفاده',
        'categories_metadata': 'فراداده دسته‌ها',
        'doc_categories_metadata': 'فراداده دسته‌ها',
        'metadata_definitions': 'تعریف‌های فراداده',
        'metadata_field': 'فیلد فراداده',
        'field_code': 'کد فیلد',
        'field_name': 'نام فیلد',
        'field_type': 'نوع فیلد',
        'is_required': 'الزامی',
        'is_searchable': 'قابل جستجو',
        'is_exportable': 'قابل صادرات',
        'default_value': 'مقدار پیش‌فرض',
        'options_json': 'گزینه‌ها (JSON)',
        'help_text': 'متن راهنما',
        'display_order': 'ترتیب نمایش',
        'field_created': 'فیلد فراداده ایجاد شد',
        'field_updated': 'فیلد فراداده به‌روز شد',
        'document_metadata': 'فراداده سند',
        'metadata_updated': 'فراداده به‌روز شد',
        'comments': 'نظرات',
        'doc_comments': 'نظرات سند',
        'add_comment': 'افزودن نظر',
        'post_comment': 'ارسال نظر',
        'comment_text': 'متن نظر',
        'reply': 'پاسخ',
        'resolve': 'حل شده',
        'resolved': 'حل شده',
        'comment_resolved': 'نظر حل شد',
        'comment_deleted': 'نظر حذف شد',
        'reply_count': 'پاسخ‌ها',
        'no_comments': 'هنوز نظری وجود ندارد',
        'be_first_comment': 'اولین نفری باشید که نظر می‌دهید',
        'print_document': 'چاپ سند',
        'print': 'چاپ',
        'link_document': 'پیوند سند',
        'unlink_document': 'لغو پیوند سند',
        'link_added': 'پیوند اضافه شد',
        'link_removed': 'پیوند حذف شد',
        'dispose_document': 'مستندسازی سند',
        'dispose': 'مستندسازی',
        'disposal_method': 'روش مستندسازی',
        'disposal_approval': 'تأیید مستندسازی',
        'document_disposed': 'سند مستندسازی شد',
        'force_checkin': 'تأیید اجباری',
        'force_check_in': 'تأیید اجباری',
        'force_checkin_reason': 'دلیل تأیید اجباری',
        'force_checkin_success': 'تأیید اجباری سند با موفقیت انجام شد',
    },
    # Arabic
    'ar': {
        'pending_review': 'في انتظار المراجعة',
        'doc_pending_review': 'في انتظار المراجعة',
        'doc_pending_approval': 'في انتظار الموافقة',
        'access_control': 'التحكم في الوصول',
        'doc_access_control': 'التحكم في الوصول',
        'retention_policies': 'سياسات الاستبقاء',
        'doc_retention_policies': 'سياسات الاستبقاء',
        'legal_holds': 'الحجز القانوني',
        'doc_legal_holds': 'الحجز القانوني',
        'export_center': 'مركز التصدير',
        'doc_export_center': 'مركز التصدير',
        'categories_metadata': 'بيانات الفئات',
        'doc_categories_metadata': 'بيانات الفئات',
        'comments': 'تعليقات',
        'doc_comments': 'تعليقات المستند',
        'print': 'طباعة',
    },
    # Russian
    'ru': {
        'pending_review': 'Ожидание проверки',
        'doc_pending_review': 'Ожидание проверки',
        'doc_pending_approval': 'Ожидание утверждения',
        'access_control': 'Контроль доступа',
        'doc_access_control': 'Контроль доступа',
        'retention_policies': 'Политики хранения',
        'doc_retention_policies': 'Политики хранения',
        'legal_holds': 'Юридические задержания',
        'doc_legal_holds': 'Юридические задержания',
        'export_center': 'Центр экспорта',
        'doc_export_center': 'Центр экспорта',
        'categories_metadata': 'Метаданные категорий',
        'doc_categories_metadata': 'Метаданные категорий',
        'comments': 'Комментарии',
        'doc_comments': 'Комментарии документа',
        'print': 'Печать',
    },
    # Chinese
    'zh': {
        'pending_review': '待审核',
        'doc_pending_review': '待审核',
        'doc_pending_approval': '待审批',
        'access_control': '访问控制',
        'doc_access_control': '访问控制',
        'retention_policies': '保留策略',
        'doc_retention_policies': '保留策略',
        'legal_holds': '法律保留',
        'doc_legal_holds': '法律保留',
        'export_center': '导出中心',
        'doc_export_center': '导出中心',
        'categories_metadata': '分类元数据',
        'doc_categories_metadata': '分类元数据',
        'comments': '评论',
        'doc_comments': '文档评论',
        'print': '打印',
    },
    # Spanish
    'es': {
        'pending_review': 'Revisión pendiente',
        'doc_pending_review': 'Revisión pendiente',
        'doc_pending_approval': 'Aprobación pendiente',
        'access_control': 'Control de acceso',
        'doc_access_control': 'Control de acceso',
        'retention_policies': 'Políticas de retención',
        'doc_retention_policies': 'Políticas de retención',
        'legal_holds': 'Retenciones legales',
        'doc_legal_holds': 'Retenciones legales',
        'export_center': 'Centro de exportación',
        'doc_export_center': 'Centro de exportación',
        'categories_metadata': 'Metadatos de categorías',
        'doc_categories_metadata': 'Metadatos de categorías',
        'comments': 'Comentarios',
        'doc_comments': 'Comentarios del documento',
        'print': 'Imprimir',
    },
    # Hindi
    'hi': {
        'pending_review': 'समीक्षा लंबित',
        'doc_pending_review': 'समीक्षा लंबित',
        'doc_pending_approval': 'स्वीकृति लंबित',
        'access_control': 'पहुंच नियंत्रण',
        'doc_access_control': 'पहुंच नियंत्रण',
        'retention_policies': 'प्रतिधारण नीतियां',
        'doc_retention_policies': 'प्रतिधारण नीतियां',
        'legal_holds': 'कानूनी प्रतिरोध',
        'doc_legal_holds': 'कानूनी प्रतिरोध',
        'export_center': 'निर्यात केंद्र',
        'doc_export_center': 'निर्यात केंद्र',
        'categories_metadata': 'श्रेणी मेटाडेटा',
        'doc_categories_metadata': 'श्रेणी मेटाडेटा',
        'comments': 'टिप्पणियां',
        'doc_comments': 'दस्तावेज़ टिप्पणियां',
        'print': 'प्रिंट',
    },
    # German
    'de': {
        'pending_review': 'Ausstehende Überprüfung',
        'doc_pending_review': 'Ausstehende Überprüfung',
        'doc_pending_approval': 'Ausstehende Genehmigung',
        'access_control': 'Zugriffskontrolle',
        'doc_access_control': 'Zugriffskontrolle',
        'retention_policies': 'Aufbewahrungsrichtlinien',
        'doc_retention_policies': 'Aufbewahrungsrichtlinien',
        'legal_holds': 'Rechtliche Rückbehaltung',
        'doc_legal_holds': 'Rechtliche Rückbehaltung',
        'export_center': 'Exportzentrum',
        'doc_export_center': 'Exportzentrum',
        'categories_metadata': 'Kategorien-Metadaten',
        'doc_categories_metadata': 'Kategorien-Metadaten',
        'comments': 'Kommentare',
        'doc_comments': 'Dokumentenkommentare',
        'print': 'Drucken',
    },
}


def add_translations():
    """Add translations to the translations file."""
    import os
    translations_path = os.path.join(os.path.dirname(__file__), 'translations.py')

    with open(translations_path, 'r', encoding='utf-8') as f:
        content = f.read()

    for lang, keys in translations_to_add.items():
        if not keys:
            continue

        # Find the language block
        lang_pattern = f"    '{lang}': {{"
        if lang_pattern not in content:
            print(f"Language '{lang}' not found in translations.py")
            continue

        # Find the end of the language block (next language or end of TRANSLATIONS)
        lang_start = content.find(lang_pattern)
        next_lang_start = content.find("    '", lang_start + 10)
        next_lang_start = content.find("':", next_lang_start) if next_lang_start > 0 else -1

        if next_lang_start < 0:
            # Find the closing brace at the end
            end_idx = content.rfind("    }")
        else:
            end_idx = next_lang_start

        lang_block = content[lang_start:end_idx]

        # Add each key if not present
        for key, value in keys.items():
            if f"'{key}':" not in lang_block:
                # Add the key-value pair
                new_entry = f"        '{key}': '{value}',\n"
                # Find a good place to insert (alphabetically or at the end of relevant section)
                lang_block += new_entry

        # Update the content
        content = content[:lang_start] + lang_block + content[end_idx:]

        print(f"Added translations for {lang}")

    with open(translations_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("Translation updates complete!")


if __name__ == '__main__':
    add_translations()