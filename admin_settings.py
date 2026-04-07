"""
Centralized Settings and Administration Data Model
=================================================
This module defines the comprehensive unified settings architecture for the entire WHDASH platform.

SCOPING LEVELS:
- Global (platform-wide defaults)
- Company (company-specific overrides)
- Branch (branch-specific overrides)
- Warehouse (warehouse-specific overrides)
- Role (role-specific settings)
- User (user-specific preferences)

CATEGORIES:
1. GENERAL - System name, branding, defaults
2. ORGANIZATION - Companies, branches, departments, teams
3. MASTER_DATA - All centralized reference data
4. USERS - User management and access
5. ROLES - RBAC and permissions
6. APPEARANCE - Theme, language, localization
7. NUMBERING - Code generation rules
8. WORKFLOW - Approval and workflow settings
9. NOTIFICATIONS - Alerts and notification rules
10. SALES - Sales module configuration
11. CRM - Customer management settings
12. WAREHOUSE - Inventory and WMS settings
13. LOGISTICS - Delivery and transport settings
14. PURCHASING - Procurement settings
15. PLANNING - Forecasting and replenishment
16. HR - Human resources settings
17. MARKETING - Marketing configuration
18. SOCIAL_MEDIA - Social media settings
19. DOCUMENTS - Document management settings
20. DASHBOARD - KPI and dashboard settings
21. INTEGRATIONS - Third-party integrations
22. AUDIT - Security and audit settings

USAGE:
    from admin_settings import (
        get_setting, set_setting, get_setting_scoped,
        ADMIN_CATEGORIES, NUMBERING_RULES, WORKFLOW_TEMPLATES,
        initialize_admin_schema
    )
"""

from typing import Any, Optional, Dict, List
from database import get_db_context, get_one, get_all, table_exists, log_audit

# ============================================================================
# CATEGORY DEFINITIONS
# ============================================================================

ADMIN_CATEGORIES = {
    'GENERAL': {
        'label': 'General Settings',
        'label_ar': 'الإعدادات العامة',
        'label_fa': 'تنظیمات عمومی',
        'icon': 'fa-sliders-h',
        'description': 'Basic platform configuration and system defaults',
        'order': 1,
        'subcategories': ['platform_info', 'company_defaults', 'business_defaults']
    },
    'ORGANIZATION': {
        'label': 'Organization Structure',
        'label_ar': 'الهيكل التنظيمي',
        'label_fa': 'ساختار سازمانی',
        'icon': 'fa-sitemap',
        'description': 'Companies, branches, divisions, departments, teams',
        'order': 2,
        'subcategories': ['companies', 'branches', 'divisions', 'departments', 'teams', 'warehouses']
    },
    'MASTER_DATA': {
        'label': 'Master Data',
        'label_ar': 'البيانات الرئيسية',
        'label_fa': 'داده‌های اصلی',
        'icon': 'fa-database',
        'description': 'Centralized reference data for the entire platform',
        'order': 3,
        'subcategories': ['countries', 'currencies', 'regions', 'markets', 'units', 'categories', 'statuses']
    },
    'USERS': {
        'label': 'Users',
        'label_ar': 'المستخدمين',
        'label_fa': 'کاربران',
        'icon': 'fa-user-cog',
        'description': 'User accounts, profiles, and access management',
        'order': 4,
        'subcategories': ['user_list', 'user_profile', 'user_access', 'user_activity']
    },
    'ROLES': {
        'label': 'Roles & Permissions',
        'label_ar': 'الأدوار والصلاحيات',
        'label_fa': 'نقش‌ها و مجوزها',
        'icon': 'fa-shield-alt',
        'description': 'Role definitions and permission matrix',
        'order': 5,
        'subcategories': ['role_list', 'permissions', 'role_hierarchy']
    },
    'APPEARANCE': {
        'label': 'Appearance & Localization',
        'label_ar': 'المظهر والترجمة',
        'label_fa': 'ظاهر و محلی‌سازی',
        'icon': 'fa-palette',
        'description': 'Theme, language, date/time, and display settings',
        'order': 6,
        'subcategories': ['themes', 'languages', 'date_time', 'number_format']
    },
    'NUMBERING': {
        'label': 'Numbering & Codes',
        'label_ar': 'الترقيم والأكواد',
        'label_fa': 'شماره‌گذاری و کدها',
        'icon': 'fa-hashtag',
        'description': 'Document and record numbering rules',
        'order': 7,
        'subcategories': ['customer_codes', 'item_codes', 'document_codes']
    },
    'WORKFLOW': {
        'label': 'Workflow & Approvals',
        'label_ar': 'سير العمل والموافقات',
        'label_fa': 'گردش‌کار و تأییدها',
        'icon': 'fa-project-diagram',
        'description': 'Approval chains and workflow configuration',
        'order': 8,
        'subcategories': ['approval_chains', 'discount_approvals', 'credit_approvals']
    },
    'NOTIFICATIONS': {
        'label': 'Notifications & Alerts',
        'label_ar': 'الإشعارات والتنبيهات',
        'label_fa': 'اعلان‌ها و هشدارها',
        'icon': 'fa-bell',
        'description': 'Alert thresholds, recipients, and delivery rules',
        'order': 9,
        'subcategories': ['stock_alerts', 'sla_alerts', 'finance_alerts', 'hr_alerts']
    },
    'SALES': {
        'label': 'Sales Settings',
        'label_ar': 'إعدادات المبيعات',
        'label_fa': 'تنظیمات فروش',
        'icon': 'fa-chart-line',
        'description': 'Sales module configuration and business rules',
        'order': 10,
        'subcategories': ['pricing', 'discounts', 'quotations', 'orders', 'returns']
    },
    'CRM': {
        'label': 'CRM & Customer Settings',
        'label_ar': 'إعدادات العملاء',
        'label_fa': 'تنظیمات CRM',
        'icon': 'fa-users',
        'description': 'Customer management and CRM behavior',
        'order': 11,
        'subcategories': ['customer_types', 'segments', 'follow_up', 'credit']
    },
    'WAREHOUSE': {
        'label': 'Warehouse & Inventory',
        'label_ar': 'المستودع والمخزون',
        'label_fa': 'انبار و موجودی',
        'icon': 'fa-warehouse',
        'description': 'WMS, inventory policies, and stock rules',
        'order': 12,
        'subcategories': ['inventory_policy', 'stock_rules', 'locations', 'transfers']
    },
    'LOGISTICS': {
        'label': 'Logistics Settings',
        'label_ar': 'إعدادات اللوجستيات',
        'label_fa': 'تنظیمات لجستیک',
        'icon': 'fa-truck',
        'description': 'Delivery, transport, and route configuration',
        'order': 13,
        'subcategories': ['delivery_types', 'routes', 'vehicles', 'drivers', 'sla']
    },
    'PURCHASING': {
        'label': 'Purchasing & Procurement',
        'label_ar': 'المشتريات والتوريد',
        'label_fa': 'خرید و تدارکات',
        'icon': 'fa-shopping-cart',
        'description': 'Supplier management and purchasing rules',
        'order': 14,
        'subcategories': ['suppliers', 'po_rules', 'approval_thresholds']
    },
    'PLANNING': {
        'label': 'Planning & Forecasting',
        'label_ar': 'التخطيط والتوقعات',
        'label_fa': 'برنامه‌ریزی و پیش‌بینی',
        'icon': 'fa-chart-area',
        'description': 'Demand planning, forecasting, and replenishment',
        'order': 15,
        'subcategories': ['forecast_methods', 'replenishment', 'safety_stock']
    },
    'HR': {
        'label': 'HR & Payroll',
        'label_ar': 'الموارد البشرية والرواتب',
        'label_fa': 'منابع انسانی و حقوق',
        'icon': 'fa-user-tie',
        'description': 'Human resources, attendance, leave, and payroll',
        'order': 16,
        'subcategories': ['leave_types', 'attendance', 'payroll_rules', 'overtime']
    },
    'MARKETING': {
        'label': 'Marketing',
        'label_ar': 'التسويق',
        'label_fa': 'بازاریابی',
        'icon': 'fa-bullhorn',
        'description': 'Campaigns, leads, budgets, and marketing KPIs',
        'order': 17,
        'subcategories': ['campaign_types', 'lead_sources', 'budgets', 'attribution']
    },
    'SOCIAL_MEDIA': {
        'label': 'Social Media',
        'label_ar': 'وسائل التواصل',
        'label_fa': 'شبکه‌های اجتماعی',
        'icon': 'fa-share-alt',
        'description': 'Social accounts, publishing, and engagement rules',
        'order': 18,
        'subcategories': ['platforms', 'publishing_rules', 'response_sla']
    },
    'DOCUMENTS': {
        'label': 'Documents & Attachments',
        'label_ar': 'المستندات والمرفقات',
        'label_fa': 'اسناد و پیوست‌ها',
        'icon': 'fa-file-alt',
        'description': 'Document types, file limits, and retention rules',
        'order': 19,
        'subcategories': ['doc_types', 'file_rules', 'retention']
    },
    'DASHBOARD': {
        'label': 'Dashboard & KPIs',
        'label_ar': 'لوحات والمؤشرات',
        'label_fa': 'داشبورد و KPIها',
        'icon': 'fa-chart-pie',
        'description': 'Dashboard widgets, KPI definitions, and targets',
        'order': 20,
        'subcategories': ['kpi_definitions', 'widget_config', 'targets']
    },
    'INTEGRATIONS': {
        'label': 'Integrations',
        'label_ar': 'التكاملات',
        'label_fa': 'یکپارچه‌سازی‌ها',
        'icon': 'fa-plug',
        'description': 'Third-party integrations and API connections',
        'order': 21,
        'subcategories': ['api_keys', 'webhooks', 'external_services']
    },
    'AUDIT': {
        'label': 'Audit & Security',
        'label_ar': 'التدقيق والأمان',
        'label_fa': 'حسابرسی و امنیت',
        'icon': 'fa-lock',
        'description': 'Security policies, audit logs, and access controls',
        'order': 22,
        'subcategories': ['password_policy', 'session_policy', 'audit_log', 'data_retention']
    },
    'DATA_TOOLS': {
        'label': 'Data Tools & Maintenance',
        'label_ar': 'أدوات البيانات والصيانة',
        'label_fa': 'ابزارهای داده و نگهداری',
        'icon': 'fa-tools',
        'description': 'Import/export, data validation, and maintenance tools',
        'order': 23,
        'subcategories': ['import_export', 'data_validation', 'cache_refresh']
    },
    'ACTIVITY_LOG': {
        'label': 'Activity Logs',
        'label_ar': 'سجلات النشاط',
        'label_fa': 'گزارشات فعالیت',
        'icon': 'fa-history',
        'description': 'Settings change history and activity tracking',
        'order': 24,
        'subcategories': ['settings_changes', 'user_activity', 'system_events']
    }
}

# ============================================================================
# MASTER DATA DEFINITIONS
# ============================================================================

MASTER_DATA_TYPES = {
    'country': {
        'label': 'Countries',
        'label_plural': 'Countries',
        'icon': 'fa-globe',
        'fields': ['code', 'name', 'name_ar', 'name_fa', 'phone_code', 'currency_code', 'is_active']
    },
    'region': {
        'label': 'Regions',
        'label_plural': 'Regions',
        'icon': 'fa-map',
        'fields': ['code', 'name', 'country_code', 'is_active']
    },
    'market': {
        'label': 'Markets',
        'label_plural': 'Markets',
        'icon': 'fa-store',
        'fields': ['code', 'name', 'region_codes', 'is_active']
    },
    'currency': {
        'label': 'Currencies',
        'label_plural': 'Currencies',
        'icon': 'fa-coins',
        'fields': ['code', 'name', 'symbol', 'decimal_places', 'exchange_rate', 'is_active']
    },
    'unit_of_measure': {
        'label': 'Unit of Measure',
        'label_plural': 'Units of Measure',
        'icon': 'fa-ruler',
        'fields': ['code', 'name', 'abbreviation', 'type', 'conversion_factor', 'is_active']
    },
    'customer_type': {
        'label': 'Customer Type',
        'label_plural': 'Customer Types',
        'icon': 'fa-user-tag',
        'fields': ['code', 'name', 'description', 'is_active']
    },
    'supplier_type': {
        'label': 'Supplier Type',
        'label_plural': 'Supplier Types',
        'icon': 'fa-industry',
        'fields': ['code', 'name', 'description', 'is_active']
    },
    'lead_source': {
        'label': 'Lead Source',
        'label_plural': 'Lead Sources',
        'icon': 'fa-bullseye',
        'fields': ['code', 'name', 'channel', 'is_active']
    },
    'sales_channel': {
        'label': 'Sales Channel',
        'label_plural': 'Sales Channels',
        'icon': 'fa-broadcast-tower',
        'fields': ['code', 'name', 'description', 'is_active']
    },
    'incoterm': {
        'label': 'Incoterm',
        'label_plural': 'Incoterms',
        'icon': 'fa-file-contract',
        'fields': ['code', 'name', 'description', 'is_active']
    },
    'payment_term': {
        'label': 'Payment Term',
        'label_plural': 'Payment Terms',
        'icon': 'fa-calendar-alt',
        'fields': ['code', 'name', 'days', 'description', 'is_active']
    },
    'tax_rule': {
        'label': 'Tax Rule',
        'label_plural': 'Tax Rules',
        'icon': 'fa-percentage',
        'fields': ['code', 'name', 'rate', 'description', 'is_active']
    },
    'document_type': {
        'label': 'Document Type',
        'label_plural': 'Document Types',
        'icon': 'fa-file',
        'fields': ['code', 'name', 'category', 'requires_approval', 'numbering_rule', 'is_active']
    },
    'alert_type': {
        'label': 'Alert Type',
        'label_plural': 'Alert Types',
        'icon': 'fa-exclamation-triangle',
        'fields': ['code', 'name', 'severity', 'module', 'is_active']
    },
    'complaint_type': {
        'label': 'Complaint Type',
        'label_plural': 'Complaint Types',
        'icon': 'fa-flag',
        'fields': ['code', 'name', 'department', 'is_active']
    },
    'return_reason': {
        'label': 'Return Reason',
        'label_plural': 'Return Reasons',
        'icon': 'fa-undo',
        'fields': ['code', 'name', 'requires_investigation', 'is_active']
    },
    'opportunity_stage': {
        'label': 'Opportunity Stage',
        'label_plural': 'Opportunity Stages',
        'icon': 'fa-flag',
        'fields': ['code', 'name', 'probability', 'stage_order', 'is_active']
    },
    'inquiry_stage': {
        'label': 'Inquiry Stage',
        'label_plural': 'Inquiry Stages',
        'icon': 'fa-question-circle',
        'fields': ['code', 'name', 'stage_order', 'is_active']
    },
    'quotation_status': {
        'label': 'Quotation Status',
        'label_plural': 'Quotation Statuses',
        'icon': 'fa-file-invoice',
        'fields': ['code', 'name', 'color', 'is_active']
    },
    'order_status': {
        'label': 'Order Status',
        'label_plural': 'Order Statuses',
        'icon': 'fa-shopping-cart',
        'fields': ['code', 'name', 'color', 'is_active']
    },
    'shipment_status': {
        'label': 'Shipment Status',
        'label_plural': 'Shipment Statuses',
        'icon': 'fa-shipping-fast',
        'fields': ['code', 'name', 'color', 'is_active']
    },
    'leave_type': {
        'label': 'Leave Type',
        'label_plural': 'Leave Types',
        'icon': 'fa-calendar-minus',
        'fields': ['code', 'name', 'paid_unpaid', 'accrual_rate', 'is_active']
    },
    'campaign_type': {
        'label': 'Campaign Type',
        'label_plural': 'Campaign Types',
        'icon': 'fa-flag',
        'fields': ['code', 'name', 'budget_type', 'is_active']
    },
    'content_type': {
        'label': 'Content Type',
        'label_plural': 'Content Types',
        'icon': 'fa-edit',
        'fields': ['code', 'name', 'platform', 'is_active']
    },
    'social_platform': {
        'label': 'Social Platform',
        'label_plural': 'Social Platforms',
        'icon': 'fa-share-alt',
        'fields': ['code', 'name', 'icon', 'is_active']
    },
    'priority_level': {
        'label': 'Priority Level',
        'label_plural': 'Priority Levels',
        'icon': 'fa-exclamation',
        'fields': ['code', 'name', 'color', 'level', 'is_active']
    },
    'kpi_definition': {
        'label': 'KPI Definition',
        'label_plural': 'KPI Definitions',
        'icon': 'fa-chart-line',
        'fields': ['code', 'name', 'formula', 'module', 'is_active']
    }
}

# ============================================================================
# NUMBERING RULES DEFINITIONS
# ============================================================================

NUMBERING_RULES = {
    'customer': {
        'label': 'Customer Code',
        'prefix': 'CUST',
        'padding': 5,
        'example': 'CUST00001'
    },
    'supplier': {
        'label': 'Supplier Code',
        'prefix': 'SUP',
        'padding': 5,
        'example': 'SUP00001'
    },
    'item': {
        'label': 'Item/Product Code',
        'prefix': 'ITEM',
        'padding': 6,
        'example': 'ITEM000001'
    },
    'inquiry': {
        'label': 'Inquiry Number',
        'prefix': 'INQ',
        'padding': 5,
        'example': 'INQ00001'
    },
    'opportunity': {
        'label': 'Opportunity Number',
        'prefix': 'OPP',
        'padding': 5,
        'example': 'OPP00001'
    },
    'quotation': {
        'label': 'Quotation Number',
        'prefix': 'QUO',
        'padding': 5,
        'example': 'QUO00001'
    },
    'sales_order': {
        'label': 'Sales Order Number',
        'prefix': 'SO',
        'padding': 5,
        'example': 'SO00001'
    },
    'reservation': {
        'label': 'Reservation Number',
        'prefix': 'RES',
        'padding': 5,
        'example': 'RES00001'
    },
    'delivery': {
        'label': 'Delivery Note Number',
        'prefix': 'DN',
        'padding': 5,
        'example': 'DN00001'
    },
    'return': {
        'label': 'Return Number',
        'prefix': 'RET',
        'padding': 5,
        'example': 'RET00001'
    },
    'purchase_order': {
        'label': 'Purchase Order Number',
        'prefix': 'PO',
        'padding': 5,
        'example': 'PO00001'
    },
    'transfer': {
        'label': 'Transfer Number',
        'prefix': 'TRF',
        'padding': 5,
        'example': 'TRF00001'
    },
    'stock_adjustment': {
        'label': 'Stock Adjustment Number',
        'prefix': 'ADJ',
        'padding': 5,
        'example': 'ADJ00001'
    },
    'shipment': {
        'label': 'Shipment Number',
        'prefix': 'SHIP',
        'padding': 5,
        'example': 'SHIP00001'
    },
    'lead': {
        'label': 'Lead Number',
        'prefix': 'LEAD',
        'padding': 5,
        'example': 'LEAD00001'
    },
    'campaign': {
        'label': 'Campaign Number',
        'prefix': 'CAMP',
        'padding': 5,
        'example': 'CAMP00001'
    },
    'employee': {
        'label': 'Employee Number',
        'prefix': 'EMP',
        'padding': 5,
        'example': 'EMP00001'
    },
    'leave_request': {
        'label': 'Leave Request Number',
        'prefix': 'LV',
        'padding': 5,
        'example': 'LV00001'
    },
    'document': {
        'label': 'Document Number',
        'prefix': 'DOC',
        'padding': 5,
        'example': 'DOC00001'
    },
    'contract': {
        'label': 'Contract Number',
        'prefix': 'CON',
        'padding': 5,
        'example': 'CON00001'
    }
}

# ============================================================================
# WORKFLOW/APPROVAL TEMPLATES
# ============================================================================

WORKFLOW_TEMPLATES = {
    'discount_request': {
        'label': 'Discount Request Approval',
        'module': 'SALES',
        'actions': ['create', 'approve', 'reject'],
        'default_approvers': ['Sales Manager']
    },
    'special_pricing': {
        'label': 'Special Pricing Approval',
        'module': 'SALES',
        'actions': ['create', 'approve', 'reject'],
        'default_approvers': ['Sales Manager']
    },
    'credit_limit_override': {
        'label': 'Credit Limit Override',
        'module': 'CRM',
        'actions': ['request', 'approve', 'reject'],
        'default_approvers': ['Finance Manager']
    },
    'sales_order_approval': {
        'label': 'Sales Order Approval',
        'module': 'SALES',
        'actions': ['submit', 'approve', 'reject'],
        'default_approvers': ['Sales Manager']
    },
    'stock_reservation_override': {
        'label': 'Stock Reservation Override',
        'module': 'WMS',
        'actions': ['request', 'approve', 'reject'],
        'default_approvers': ['Warehouse Manager']
    },
    'transfer_approval': {
        'label': 'Stock Transfer Approval',
        'module': 'WMS',
        'actions': ['submit', 'approve', 'reject'],
        'default_approvers': ['Warehouse Manager']
    },
    'stock_adjustment_approval': {
        'label': 'Stock Adjustment Approval',
        'module': 'WMS',
        'actions': ['submit', 'approve', 'reject'],
        'default_approvers': ['Warehouse Manager']
    },
    'purchase_approval': {
        'label': 'Purchase Order Approval',
        'module': 'PURCHASING',
        'actions': ['submit', 'approve', 'reject'],
        'default_approvers': ['Purchasing Manager']
    },
    'forecast_override': {
        'label': 'Forecast Override Approval',
        'module': 'PLANNING',
        'actions': ['submit', 'approve', 'reject'],
        'default_approvers': ['Planner']
    },
    'leave_approval': {
        'label': 'Leave Request Approval',
        'module': 'HR',
        'actions': ['submit', 'approve', 'reject'],
        'default_approvers': ['HR Manager']
    },
    'overtime_approval': {
        'label': 'Overtime Request Approval',
        'module': 'HR',
        'actions': ['submit', 'approve', 'reject'],
        'default_approvers': ['HR Manager']
    },
    'campaign_approval': {
        'label': 'Marketing Campaign Approval',
        'module': 'MARKETING',
        'actions': ['submit', 'approve', 'reject'],
        'default_approvers': ['Marketing Manager']
    },
    'content_approval': {
        'label': 'Content Approval',
        'module': 'SOCIAL_MEDIA',
        'actions': ['submit', 'approve', 'reject'],
        'default_approvers': ['Social Media Manager']
    },
    'budget_approval': {
        'label': 'Budget Approval',
        'module': 'MARKETING',
        'actions': ['submit', 'approve', 'reject'],
        'default_approvers': ['COO']
    },
    'return_approval': {
        'label': 'Return Request Approval',
        'module': 'SALES',
        'actions': ['submit', 'approve', 'reject'],
        'default_approvers': ['Sales Manager']
    },
    'complaint_closure': {
        'label': 'Complaint Closure Approval',
        'module': 'SALES',
        'actions': ['submit', 'approve', 'reject'],
        'default_approvers': ['Customer Service Manager']
    }
}

# ============================================================================
# DEFAULT SETTINGS VALUES
# ============================================================================

DEFAULT_GENERAL_SETTINGS = {
    'platform_name': {'value': 'WHDASH', 'type': 'string', 'description': 'Platform display name'},
    'platform_version': {'value': '2.0.0', 'type': 'string', 'description': 'Current platform version'},
    'company_name': {'value': 'My Company', 'type': 'string', 'description': 'Primary company name'},
    'company_address': {'value': '', 'type': 'string', 'description': 'Company address'},
    'company_phone': {'value': '', 'type': 'string', 'description': 'Company phone'},
    'company_email': {'value': '', 'type': 'string', 'description': 'Company email'},
    'company_website': {'value': '', 'type': 'string', 'description': 'Company website'},
    'default_warehouse_id': {'value': '', 'type': 'integer', 'description': 'Default warehouse ID'},
    'default_company_id': {'value': '', 'type': 'integer', 'description': 'Default company ID'},
    'default_branch_id': {'value': '', 'type': 'integer', 'description': 'Default branch ID'},
}

DEFAULT_LOCALIZATION_SETTINGS = {
    'default_language': {'value': 'en', 'type': 'string', 'description': 'Default system language'},
    'available_languages': {'value': 'en,ar,fa', 'type': 'string', 'description': 'Available languages'},
    'default_timezone': {'value': 'Asia/Dubai', 'type': 'string', 'description': 'Default timezone'},
    'date_format': {'value': 'DD/MM/YYYY', 'type': 'string', 'description': 'Date format'},
    'time_format': {'value': '24h', 'type': 'string', 'description': 'Time format (12h or 24h)'},
    'number_format': {'value': '1,234.56', 'type': 'string', 'description': 'Number format pattern'},
    'decimal_precision': {'value': '2', 'type': 'integer', 'description': 'Decimal places'},
    'currency_format': {'value': 'AED 1,234.56', 'type': 'string', 'description': 'Currency display format'},
    'default_currency': {'value': 'AED', 'type': 'string', 'description': 'Default currency code'},
    'week_start_day': {'value': 'Sunday', 'type': 'string', 'description': 'Week start day'},
    'business_days': {'value': '1,2,3,4,5', 'type': 'string', 'description': 'Business days (0=Sun)'},
    'enable_rtl': {'value': '1', 'type': 'boolean', 'description': 'Enable RTL support'},
}

DEFAULT_SECURITY_SETTINGS = {
    'session_timeout_minutes': {'value': '120', 'type': 'integer', 'description': 'Session timeout'},
    'max_login_attempts': {'value': '5', 'type': 'integer', 'description': 'Max login attempts'},
    'password_min_length': {'value': '8', 'type': 'integer', 'description': 'Min password length'},
    'require_special_char_password': {'value': '1', 'type': 'boolean', 'description': 'Require special chars'},
    'require_email_verification': {'value': '0', 'type': 'boolean', 'description': 'Require email verification'},
    'enable_2fa': {'value': '0', 'type': 'boolean', 'description': 'Enable two-factor auth'},
    'allowed_file_extensions': {'value': 'png,jpg,jpeg,gif,pdf,doc,docx,xls,xlsx', 'type': 'string', 'description': 'Allowed file uploads'},
    'max_file_size_mb': {'value': '10', 'type': 'integer', 'description': 'Max file size in MB'},
    'ip_whitelist_enabled': {'value': '0', 'type': 'boolean', 'description': 'Enable IP whitelist'},
    'ip_whitelist': {'value': '', 'type': 'string', 'description': 'Whitelisted IP addresses'},
}

DEFAULT_UI_SETTINGS = {
    'default_theme': {'value': 'dark', 'type': 'string', 'description': 'Default UI theme'},
    'items_per_page': {'value': '50', 'type': 'integer', 'description': 'Default pagination size'},
    'show_welcome_tour': {'value': '1', 'type': 'boolean', 'description': 'Show welcome tour'},
    'compact_sidebar': {'value': '0', 'type': 'boolean', 'description': 'Use compact sidebar'},
    'default_font_size': {'value': 'medium', 'type': 'string', 'description': 'Default font size'},
    'table_density': {'value': 'comfortable', 'type': 'string', 'description': 'Table row density'},
}

DEFAULT_SALES_SETTINGS = {
    'sales_default_currency': {'value': 'AED', 'type': 'string', 'description': 'Default sales currency'},
    'sales_tax_rate': {'value': '5', 'type': 'float', 'description': 'Default tax rate %'},
    'quotation_validity_days': {'value': '30', 'type': 'integer', 'description': 'Quotation validity in days'},
    'max_discount_percent': {'value': '20', 'type': 'float', 'description': 'Max allowed discount %'},
    'discount_approval_threshold': {'value': '10', 'type': 'float', 'description': 'Discount needing approval %'},
    'min_margin_percent': {'value': '5', 'type': 'float', 'description': 'Minimum profit margin %'},
    'inquiry_response_sla_hours': {'value': '24', 'type': 'integer', 'description': 'Inquiry response SLA (hours)'},
    'quotation_turnaround_hours': {'value': '48', 'type': 'integer', 'description': 'Quotation turnaround SLA (hours)'},
    'lost_reason_mandatory': {'value': '1', 'type': 'boolean', 'description': 'Require lost reason'},
    'source_tracking_mandatory': {'value': '1', 'type': 'boolean', 'description': 'Require source tracking'},
    'require_quotation_approval': {'value': '0', 'type': 'boolean', 'description': 'Require quotation approval'},
    'default_payment_terms': {'value': 'NET30', 'type': 'string', 'description': 'Default payment terms'},
    'auto_confirm_orders': {'value': '0', 'type': 'boolean', 'description': 'Auto-confirm orders'},
}

DEFAULT_CRM_SETTINGS = {
    'crm_customer_types': {'value': 'Retail,Wholesale,Corporate,Government', 'type': 'string', 'description': 'Customer type list'},
    'crm_segments': {'value': 'VIP,Regular,New,Inactive', 'type': 'string', 'description': 'Customer segments'},
    'crm_lead_followup_days': {'value': '7', 'type': 'integer', 'description': 'Lead follow-up reminder days'},
    'crm_auto_assignment': {'value': '0', 'type': 'boolean', 'description': 'Enable auto lead assignment'},
    'crm_inactive_days_threshold': {'value': '90', 'type': 'integer', 'description': 'Inactive customer threshold'},
    'crm_credit_limit_default': {'value': '10000', 'type': 'float', 'description': 'Default credit limit'},
    'crm_duplicate_check_fields': {'value': 'name,phone,email', 'type': 'string', 'description': 'Duplicate check fields'},
}

DEFAULT_WMS_SETTINGS = {
    'wms_inventory_method': {'value': 'FIFO', 'type': 'string', 'description': 'Inventory valuation method'},
    'wms_low_stock_threshold_percent': {'value': '20', 'type': 'integer', 'description': 'Low stock alert threshold %'},
    'wms_reorder_threshold_percent': {'value': '30', 'type': 'integer', 'description': 'Reorder threshold %'},
    'wms_auto_assign_location': {'value': '1', 'type': 'boolean', 'description': 'Auto-assign storage location'},
    'wms_enable_serial_tracking': {'value': '1', 'type': 'boolean', 'description': 'Enable serial tracking'},
    'wms_enable_batch_tracking': {'value': '1', 'type': 'boolean', 'description': 'Enable batch tracking'},
    'wms_auto_receive': {'value': '0', 'type': 'boolean', 'description': 'Enable auto receiving'},
    'wms_cycle_count_frequency': {'value': '30', 'type': 'integer', 'description': 'Cycle count frequency (days)'},
    'wms_reservation_expiry_hours': {'value': '48', 'type': 'integer', 'description': 'Reservation expiry (hours)'},
    'wms_auto_reservation': {'value': '1', 'type': 'boolean', 'description': 'Auto-reserve stock on order'},
}

DEFAULT_LOGISTICS_SETTINGS = {
    'logistics_default_delivery_window_hours': {'value': '4', 'type': 'integer', 'description': 'Default delivery window (hours)'},
    'logistics_enable_gps_tracking': {'value': '1', 'type': 'boolean', 'description': 'Enable GPS tracking'},
    'logistics_default_vehicle_id': {'value': '', 'type': 'integer', 'description': 'Default vehicle ID'},
    'logistics_sla_delivery_hours': {'value': '72', 'type': 'integer', 'description': 'Delivery SLA (hours)'},
    'logistics_requires_pod': {'value': '1', 'type': 'boolean', 'description': 'Require proof of delivery'},
    'logistics_auto_dispatch': {'value': '0', 'type': 'boolean', 'description': 'Auto-dispatch deliveries'},
    'logistics_failed_attempts_max': {'value': '3', 'type': 'integer', 'description': 'Max failed delivery attempts'},
}

DEFAULT_HR_SETTINGS = {
    'hr_default_probation_months': {'value': '3', 'type': 'integer', 'description': 'Default probation period (months)'},
    'hr_default_annual_leave_days': {'value': '21', 'type': 'integer', 'description': 'Default annual leave days'},
    'hr_work_week_days': {'value': '5', 'type': 'integer', 'description': 'Working days per week'},
    'hr_overtime_rate_weekday': {'value': '1.5', 'type': 'float', 'description': 'Weekday overtime multiplier'},
    'hr_overtime_rate_weekend': {'value': '2.0', 'type': 'float', 'description': 'Weekend overtime multiplier'},
    'hr_overtime_rate_holiday': {'value': '2.5', 'type': 'float', 'description': 'Holiday overtime multiplier'},
    'hr_lateness_threshold_minutes': {'value': '15', 'type': 'integer', 'description': 'Lateness threshold (minutes)'},
    'hr_leave_carry_forward_days': {'value': '5', 'type': 'integer', 'description': 'Leave carry-forward max days'},
    'hr_payroll_frequency': {'value': 'monthly', 'type': 'string', 'description': 'Payroll frequency'},
}

DEFAULT_MARKETING_SETTINGS = {
    'marketing_default_campaign_budget': {'value': '1000', 'type': 'float', 'description': 'Default campaign budget'},
    'marketing_enable_attribution': {'value': '1', 'type': 'boolean', 'description': 'Enable attribution tracking'},
    'marketing_default_channel': {'value': 'Social Media', 'type': 'string', 'description': 'Default marketing channel'},
    'marketing_lead_convert_sla_days': {'value': '7', 'type': 'integer', 'description': 'Lead conversion SLA (days)'},
    'marketing_budget_alert_threshold': {'value': '80', 'type': 'integer', 'description': 'Budget alert threshold %'},
}

DEFAULT_PLANNING_SETTINGS = {
    'planning_default_forecast_method': {'value': 'MOVING_AVERAGE', 'type': 'string', 'description': 'Default forecast method'},
    'planning_forecast_horizon_days': {'value': '30', 'type': 'integer', 'description': 'Forecast horizon (days)'},
    'planning_demand_history_months': {'value': '12', 'type': 'integer', 'description': 'Demand history (months)'},
    'planning_enable_auto_replenishment': {'value': '0', 'type': 'boolean', 'description': 'Enable auto replenishment'},
    'planning_service_level_target': {'value': '95', 'type': 'integer', 'description': 'Service level target %'},
    'planning_safety_stock_factor': {'value': '1.5', 'type': 'float', 'description': 'Safety stock multiplier'},
}

# ============================================================================
# SCOPING HELPERS
# ============================================================================

SCOPE_LEVELS = {
    'GLOBAL': {'label': 'Global', 'order': 1},
    'COMPANY': {'label': 'Company', 'order': 2},
    'BRANCH': {'label': 'Branch', 'order': 3},
    'WAREHOUSE': {'label': 'Warehouse', 'order': 4},
    'ROLE': {'label': 'Role', 'order': 5},
    'USER': {'label': 'User', 'order': 6},
}

def get_scope_label(scope_type):
    """Get localized label for a scope type."""
    return SCOPE_LEVELS.get(scope_type.upper(), {}).get('label', scope_type)

# ============================================================================
# SETTINGS GET/SET FUNCTIONS
# ============================================================================

def get_setting(setting_key, default=None, scope_type='GLOBAL', scope_id=None):
    """
    Get a setting value with proper scoping.
    
    Args:
        setting_key: The setting key to retrieve
        default: Default value if not found
        scope_type: GLOBAL, COMPANY, BRANCH, WAREHOUSE, ROLE, or USER
        scope_id: ID of the scope entity (company_id, branch_id, etc.)
    
    Returns:
        The setting value or default
    """
    # Try scope-specific first, fall back to global
    if scope_type != 'GLOBAL' and scope_id:
        result = get_one("""
            SELECT setting_value FROM admin_settings 
            WHERE setting_key = ? AND scope_type = ? AND scope_id = ? AND is_active = 1
        """, (setting_key, scope_type.upper(), scope_id))
        
        if result is None:
            # Fall back to global
            result = get_one("""
                SELECT setting_value FROM admin_settings 
                WHERE setting_key = ? AND scope_type = 'GLOBAL' AND is_active = 1
            """, (setting_key,))
    else:
        result = get_one("""
            SELECT setting_value FROM admin_settings 
            WHERE setting_key = ? AND scope_type = 'GLOBAL' AND is_active = 1
        """, (setting_key,))
    
    return result['setting_value'] if result else default


def set_setting(setting_key, value, category='GENERAL', scope_type='GLOBAL', 
                scope_id=None, description=None, user_id=None):
    """
    Set a setting value with proper scoping and audit.
    
    Args:
        setting_key: The setting key
        value: The value to set
        category: Setting category
        scope_type: GLOBAL, COMPANY, BRANCH, WAREHOUSE, ROLE, or USER
        scope_id: ID of the scope entity
        description: Setting description
        user_id: User making the change (for audit)
    
    Returns:
        True if successful
    """
    with get_db_context() as db:
        # Check existing
        existing = db.execute("""
            SELECT id, setting_value FROM admin_settings 
            WHERE setting_key = ? AND scope_type = ? AND scope_id = ?
        """, (setting_key, scope_type.upper(), scope_id)).fetchone()
        
        old_value = existing['setting_value'] if existing else None
        
        if existing:
            db.execute("""
                UPDATE admin_settings 
                SET setting_value = ?, category = ?, description = ?, 
                    updated_at = CURRENT_TIMESTAMP, updated_by = ?, is_active = 1
                WHERE id = ?
            """, (str(value), category, description, user_id, existing['id']))
        else:
            db.execute("""
                INSERT INTO admin_settings 
                (setting_key, setting_value, category, scope_type, scope_id, description, created_by, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (setting_key, str(value), category, scope_type.upper(), scope_id, description, user_id, user_id))
        
        db.commit()
        
        # Audit log
        if old_value != str(value):
            log_audit(
                entity_type='setting',
                entity_id=setting_key,
                action='UPDATE' if old_value else 'CREATE',
                user_id=user_id,
                field_name='setting_value',
                old_value=old_value,
                new_value=str(value),
                notes=f"Scope: {scope_type}" + (f":{scope_id}" if scope_id else "")
            )
        
        return True


def get_settings_by_category(category, scope_type='GLOBAL', scope_id=None):
    """Get all settings in a category."""
    if scope_type != 'GLOBAL' and scope_id:
        rows = get_all("""
            SELECT setting_key, setting_value, scope_type, scope_id 
            FROM admin_settings 
            WHERE category = ? AND scope_type IN ('GLOBAL', ?) AND is_active = 1
            ORDER BY scope_type, setting_key
        """, (category, scope_type.upper()))
    else:
        rows = get_all("""
            SELECT setting_key, setting_value 
            FROM admin_settings 
            WHERE category = ? AND scope_type = 'GLOBAL' AND is_active = 1
            ORDER BY setting_key
        """, (category,))
    
    return {row['setting_key']: row['setting_value'] for row in rows}


def get_settings_scoped(category, scope_type='GLOBAL', scope_id=None):
    """
    Get settings with proper scoping hierarchy.
    Returns merged dict where more specific scopes override global.
    """
    settings = {}
    
    # Get global settings first
    global_settings = get_settings_by_category(category, 'GLOBAL', None)
    settings.update(global_settings)
    
    # Override with scope-specific if exists
    if scope_type != 'GLOBAL' and scope_id:
        scoped_settings = get_all("""
            SELECT setting_key, setting_value FROM admin_settings 
            WHERE category = ? AND scope_type = ? AND scope_id = ? AND is_active = 1
        """, (category, scope_type.upper(), scope_id))
        
        for row in scoped_settings:
            settings[row['setting_key']] = row['setting_value']
    
    return settings


def delete_setting(setting_key, scope_type='GLOBAL', scope_id=None):
    """Soft delete a setting."""
    with get_db_context() as db:
        db.execute("""
            UPDATE admin_settings SET is_active = 0, updated_at = CURRENT_TIMESTAMP
            WHERE setting_key = ? AND scope_type = ? AND scope_id = ?
        """, (setting_key, scope_type.upper(), scope_id))
        db.commit()
    return True


def reset_setting_to_default(setting_key, scope_type='GLOBAL', scope_id=None):
    """Reset a setting to its global default by removing scope override."""
    if scope_type == 'GLOBAL':
        return False  # Can't reset global to itself
    
    return delete_setting(setting_key, scope_type, scope_id)


# ============================================================================
# MASTER DATA CRUD
# ============================================================================

def get_master_data(master_type, is_active=None, limit=100, offset=0):
    """Get master data records of a specific type."""
    table_name = f"md_{master_type}"
    
    if not table_exists(table_name):
        return []
    
    sql = f"SELECT * FROM {table_name}"
    params = []
    
    if is_active is not None:
        sql += " WHERE is_active = ?"
        params.append(1 if is_active else 0)
    
    sql += f" ORDER BY name LIMIT {limit} OFFSET {offset}"
    
    return get_all(sql, params)


def get_master_data_record(master_type, record_id):
    """Get a single master data record."""
    table_name = f"md_{master_type}"
    
    if not table_exists(table_name):
        return None
    
    return get_one(f"SELECT * FROM {table_name} WHERE id = ?", (record_id,))


def create_master_data(master_type, data, user_id=None):
    """Create a new master data record."""
    table_name = f"md_{master_type}"
    
    if not table_exists(table_name):
        return None, f"Table {table_name} does not exist"
    
    # Build insert statement
    fields = list(data.keys())
    values = list(data.values())
    placeholders = ','.join(['?' for _ in fields])
    field_str = ','.join(fields)
    
    try:
        with get_db_context() as db:
            cursor = db.execute(
                f"INSERT INTO {table_name} ({field_str}) VALUES ({placeholders})",
                values
            )
            db.commit()
            record_id = cursor.lastrowid
            
            log_audit(
                entity_type=master_type,
                entity_id=record_id,
                action='CREATE',
                user_id=user_id
            )
            
            return record_id, None
    except Exception as e:
        return None, str(e)


def update_master_data(master_type, record_id, data, user_id=None):
    """Update a master data record."""
    table_name = f"md_{master_type}"
    
    if not table_exists(table_name):
        return False, f"Table {table_name} does not exist"
    
    # Build update statement
    fields = list(data.keys())
    values = list(data.values())
    set_str = ','.join([f"{f} = ?" for f in fields])
    
    try:
        with get_db_context() as db:
            db.execute(
                f"UPDATE {table_name} SET {set_str} WHERE id = ?",
                values + [record_id]
            )
            db.commit()
            
            log_audit(
                entity_type=master_type,
                entity_id=record_id,
                action='UPDATE',
                user_id=user_id
            )
            
            return True, None
    except Exception as e:
        return False, str(e)


def delete_master_data(master_type, record_id, hard_delete=False):
    """Delete a master data record (soft delete by default)."""
    table_name = f"md_{master_type}"
    
    if not table_exists(table_name):
        return False, f"Table {table_name} does not exist"
    
    try:
        with get_db_context() as db:
            if hard_delete:
                db.execute(f"DELETE FROM {table_name} WHERE id = ?", (record_id,))
            else:
                db.execute(f"UPDATE {table_name} SET is_active = 0 WHERE id = ?", (record_id,))
            db.commit()
            
            log_audit(
                entity_type=master_type,
                entity_id=record_id,
                action='DELETE' if hard_delete else 'DEACTIVATE',
            )
            
            return True, None
    except Exception as e:
        return False, str(e)


# ============================================================================
# NUMBERING RULE CRUD
# ============================================================================

def get_numbering_rule(rule_type):
    """Get a numbering rule configuration."""
    return get_one("SELECT * FROM numbering_rules WHERE rule_type = ? AND is_active = 1", (rule_type,))


def get_all_numbering_rules():
    """Get all active numbering rules."""
    return get_all("SELECT * FROM numbering_rules WHERE is_active = 1 ORDER BY rule_type")


def save_numbering_rule(rule_type, prefix, padding, reset_frequency='YEARLY',
                        use_company_prefix=False, use_branch_prefix=False,
                        suffix='', user_id=None):
    """Create or update a numbering rule."""
    with get_db_context() as db:
        existing = db.execute(
            "SELECT id FROM numbering_rules WHERE rule_type = ?", (rule_type,)
        ).fetchone()
        
        if existing:
            db.execute("""
                UPDATE numbering_rules 
                SET prefix = ?, padding = ?, reset_frequency = ?, 
                    use_company_prefix = ?, use_branch_prefix = ?, suffix = ?,
                    updated_at = CURRENT_TIMESTAMP, updated_by = ?
                WHERE rule_type = ?
            """, (prefix, padding, reset_frequency, 
                  1 if use_company_prefix else 0,
                  1 if use_branch_prefix else 0,
                  suffix, user_id, rule_type))
        else:
            db.execute("""
                INSERT INTO numbering_rules 
                (rule_type, prefix, padding, reset_frequency, use_company_prefix, 
                 use_branch_prefix, suffix, created_by, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (rule_type, prefix, padding, reset_frequency,
                  1 if use_company_prefix else 0,
                  1 if use_branch_prefix else 0,
                  suffix, user_id, user_id))
        
        db.commit()
        
        log_audit(
            entity_type='numbering_rule',
            entity_id=rule_type,
            action='UPDATE' if existing else 'CREATE',
            user_id=user_id,
            notes=f"Rule: {rule_type}"
        )
        
        return True


def generate_next_number(rule_type, company_id=None, branch_id=None):
    """
    Generate the next number for a given rule type.
    This is thread-safe and handles concurrent access.
    """
    rule = get_numbering_rule(rule_type)
    if not rule:
        return None
    
    prefix = rule['prefix']
    
    # Add company prefix if configured
    if rule['use_company_prefix'] and company_id:
        company = get_one("SELECT code FROM companies WHERE id = ?", (company_id,))
        if company:
            prefix = f"{company['code']}{prefix}"
    
    # Add branch prefix if configured
    if rule['use_branch_prefix'] and branch_id:
        branch = get_one("SELECT code FROM branches WHERE id = ?", (branch_id,))
        if branch:
            prefix = f"{prefix}{branch['code']}"
    
    with get_db_context() as db:
        # Get next sequence
        seq_row = db.execute("""
            SELECT next_value FROM numbering_sequences 
            WHERE rule_type = ? AND company_id = ? AND branch_id = ?
            FOR UPDATE
        """, (rule_type, company_id, branch_id)).fetchone()
        
        if seq_row:
            next_val = seq_row['next_value']
            db.execute("""
                UPDATE numbering_sequences SET next_value = next_value + 1
                WHERE rule_type = ? AND company_id = ? AND branch_id = ?
            """, (rule_type, company_id, branch_id))
        else:
            next_val = 1
            db.execute("""
                INSERT INTO numbering_sequences (rule_type, company_id, branch_id, next_value)
                VALUES (?, ?, ?, 2)
            """, (rule_type, company_id, branch_id))
        
        db.commit()
    
    # Format the number with zero padding
    num_str = str(next_val).zfill(rule['padding'])
    
    return f"{prefix}{num_str}{rule['suffix']}"


# ============================================================================
# WORKFLOW CRUD
# ============================================================================

def get_workflow(workflow_type):
    """Get a workflow configuration."""
    return get_one("SELECT * FROM workflows WHERE workflow_type = ? AND is_active = 1", (workflow_type,))


def get_all_workflows():
    """Get all active workflows."""
    return get_all("SELECT * FROM workflows WHERE is_active = 1 ORDER BY workflow_type")


def get_workflow_steps(workflow_id):
    """Get all approval steps for a workflow."""
    return get_all("""
        SELECT ws.*, r.role_name as approver_role_name
        FROM workflow_steps ws
        LEFT JOIN roles r ON ws.approver_role_id = r.id
        WHERE ws.workflow_id = ?
        ORDER BY ws.step_order
    """, (workflow_id,))


def save_workflow(workflow_type, module, label, description, 
                  requires_approval=True, steps=None, user_id=None):
    """
    Create or update a workflow.
    Steps should be a list of dicts with: approver_role_id, step_order, sla_hours
    """
    with get_db_context() as db:
        existing = db.execute(
            "SELECT id FROM workflows WHERE workflow_type = ?", (workflow_type,)
        ).fetchone()
        
        if existing:
            workflow_id = existing['id']
            db.execute("""
                UPDATE workflows 
                SET module = ?, label = ?, description = ?, requires_approval = ?,
                    updated_at = CURRENT_TIMESTAMP, updated_by = ?
                WHERE id = ?
            """, (module, label, description, 1 if requires_approval else 0,
                  user_id, workflow_id))
            
            # Delete existing steps
            db.execute("DELETE FROM workflow_steps WHERE workflow_id = ?", (workflow_id,))
        else:
            cursor = db.execute("""
                INSERT INTO workflows (workflow_type, module, label, description, 
                                      requires_approval, created_by, updated_by)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (workflow_type, module, label, description,
                  1 if requires_approval else 0, user_id, user_id))
            workflow_id = cursor.lastrowid
        
        # Insert steps
        if steps:
            for step in steps:
                db.execute("""
                    INSERT INTO workflow_steps 
                    (workflow_id, step_order, approver_role_id, sla_hours)
                    VALUES (?, ?, ?, ?)
                """, (workflow_id, step['step_order'], step['approver_role_id'], 
                      step.get('sla_hours', 24)))
        
        db.commit()
        
        log_audit(
            entity_type='workflow',
            entity_id=workflow_type,
            action='UPDATE' if existing else 'CREATE',
            user_id=user_id
        )
        
        return True


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_admin_schema():
    """Initialize all admin/settings tables."""
    
    # admin_settings table - unified settings with scoping
    if not table_exists('admin_settings'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE admin_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT NOT NULL,
                    setting_value TEXT,
                    category TEXT DEFAULT 'GENERAL',
                    description TEXT,
                    scope_type TEXT DEFAULT 'GLOBAL',
                    scope_id INTEGER,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    updated_at TIMESTAMP,
                    updated_by INTEGER,
                    UNIQUE(setting_key, scope_type, scope_id)
                )
            """)
            db.execute("CREATE INDEX idx_settings_key ON admin_settings(setting_key)")
            db.execute("CREATE INDEX idx_settings_scope ON admin_settings(scope_type, scope_id)")
            db.execute("CREATE INDEX idx_settings_category ON admin_settings(category)")
    
    # numbering_rules table
    if not table_exists('numbering_rules'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE numbering_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_type TEXT UNIQUE NOT NULL,
                    prefix TEXT NOT NULL,
                    padding INTEGER DEFAULT 5,
                    reset_frequency TEXT DEFAULT 'YEARLY',
                    use_company_prefix INTEGER DEFAULT 0,
                    use_branch_prefix INTEGER DEFAULT 0,
                    suffix TEXT DEFAULT '',
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    updated_at TIMESTAMP,
                    updated_by INTEGER
                )
            """)
    
    # numbering_sequences table
    if not table_exists('numbering_sequences'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE numbering_sequences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_type TEXT NOT NULL,
                    company_id INTEGER,
                    branch_id INTEGER,
                    next_value INTEGER DEFAULT 1,
                    last_reset_at TIMESTAMP,
                    UNIQUE(rule_type, company_id, branch_id)
                )
            """)
    
    # workflows table
    if not table_exists('workflows'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE workflows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_type TEXT UNIQUE NOT NULL,
                    module TEXT NOT NULL,
                    label TEXT NOT NULL,
                    description TEXT,
                    requires_approval INTEGER DEFAULT 1,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    updated_at TIMESTAMP,
                    updated_by INTEGER
                )
            """)
    
    # workflow_steps table
    if not table_exists('workflow_steps'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE workflow_steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_id INTEGER NOT NULL,
                    step_order INTEGER NOT NULL,
                    approver_role_id INTEGER,
                    sla_hours INTEGER DEFAULT 24,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (workflow_id) REFERENCES workflows(id),
                    FOREIGN KEY (approver_role_id) REFERENCES roles(id)
                )
            """)
    
    # notification_rules table
    if not table_exists('notification_rules'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE notification_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_code TEXT UNIQUE NOT NULL,
                    rule_name TEXT NOT NULL,
                    module TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    threshold_value TEXT,
                    severity TEXT DEFAULT 'MEDIUM',
                    recipients TEXT,
                    delivery_method TEXT DEFAULT 'IN_APP',
                    escalation_hours INTEGER,
                    repeat_interval_hours INTEGER,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_by INTEGER,
                    updated_at TIMESTAMP,
                    updated_by INTEGER
                )
            """)
    
    # master_data_registry table - tracks all master data types
    if not table_exists('master_data_registry'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE master_data_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    master_type TEXT UNIQUE NOT NULL,
                    label TEXT NOT NULL,
                    label_plural TEXT NOT NULL,
                    icon TEXT,
                    table_name TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
    
    # Seed master data registry
    for md_type, md_def in MASTER_DATA_TYPES.items():
        existing = get_one("SELECT id FROM master_data_registry WHERE master_type = ?", (md_type,))
        if not existing:
            with get_db_context() as db:
                db.execute("""
                    INSERT INTO master_data_registry (master_type, label, label_plural, icon, table_name)
                    VALUES (?, ?, ?, ?, ?)
                """, (md_type, md_def['label'], md_def['label_plural'], 
                      md_def.get('icon', 'fa-circle'), f"md_{md_type}"))
                db.commit()
    
    # Create individual master data tables
    _create_master_data_tables()
    
    # Seed default settings
    _seed_default_settings()


def _create_master_data_tables():
    """Create individual master data tables based on registry."""
    registry = get_all("SELECT * FROM master_data_registry WHERE is_active = 1")
    
    for md in registry:
        table_name = md['table_name']
        
        if not table_exists(table_name):
            with get_db_context() as db:
                db.execute(f"""
                    CREATE TABLE {table_name} (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        code TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        name_ar TEXT,
                        name_fa TEXT,
                        description TEXT,
                        extra_data TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP,
                        created_by INTEGER,
                        updated_by INTEGER
                    )
                """)
                db.execute(f"CREATE INDEX idx_{table_name}_code ON {table_name}(code)")
                db.execute(f"CREATE INDEX idx_{table_name}_active ON {table_name}(is_active)")
                db.commit()


def _seed_default_settings():
    """Seed default settings if not already present."""
    
    all_defaults = {}
    all_defaults.update(DEFAULT_GENERAL_SETTINGS)
    all_defaults.update(DEFAULT_LOCALIZATION_SETTINGS)
    all_defaults.update(DEFAULT_SECURITY_SETTINGS)
    all_defaults.update(DEFAULT_UI_SETTINGS)
    all_defaults.update(DEFAULT_SALES_SETTINGS)
    all_defaults.update(DEFAULT_CRM_SETTINGS)
    all_defaults.update(DEFAULT_WMS_SETTINGS)
    all_defaults.update(DEFAULT_LOGISTICS_SETTINGS)
    all_defaults.update(DEFAULT_HR_SETTINGS)
    all_defaults.update(DEFAULT_MARKETING_SETTINGS)
    all_defaults.update(DEFAULT_PLANNING_SETTINGS)
    
    for key, meta in all_defaults.items():
        existing = get_setting(key)
        if existing is None:
            # Determine category
            if key.startswith(('platform', 'company', 'default_')):
                category = 'GENERAL'
            elif key.startswith(('default_')):
                category = 'GENERAL'
            elif key.startswith(('session', 'max_', 'password', 'require_', 'enable_', 'allowed_', 'ip_', 'wms_', 'logistics_', 'hr_', 'planning_', 'crm_', 'marketing_')):
                category = key.split('_')[0].upper()
                if category == 'CRM':
                    category = 'CRM'
                elif category == 'HR':
                    category = 'HR'
                elif category == 'PLANNING':
                    category = 'PLANNING'
                elif category == 'MARKETING':
                    category = 'MARKETING'
                elif category == 'DEFAULT':
                    category = 'GENERAL'
            else:
                category = 'GENERAL'
            
            set_setting(key, meta['value'], category, 'GLOBAL', None, meta['description'])
    
    # Seed numbering rules
    for rule_type, rule_def in NUMBERING_RULES.items():
        existing = get_numbering_rule(rule_type)
        if not existing:
            save_numbering_rule(
                rule_type,
                rule_def['prefix'],
                rule_def['padding'],
                'YEARLY',
                False,
                False,
                ''
            )
    
    # Seed workflows
    for wf_type, wf_def in WORKFLOW_TEMPLATES.items():
        existing = get_workflow(wf_type)
        if not existing:
            save_workflow(
                wf_type,
                wf_def['module'],
                wf_def['label'],
                '',
                True,
                []
            )


# ============================================================================
# SETTINGS CHANGE HISTORY
# ============================================================================

def get_settings_history(setting_key=None, user_id=None, limit=100):
    """
    Get settings change history from audit log.
    Filter by setting_key and/or user_id.
    """
    sql = """
        SELECT * FROM platform_audit_log 
        WHERE entity_type = 'setting'
    """
    params = []
    
    if setting_key:
        sql += " AND entity_id = ?"
        params.append(setting_key)
    
    if user_id:
        sql += " AND user_id = ?"
        params.append(user_id)
    
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    return get_all(sql, params)


# Initialize when module is imported
initialize_admin_schema()
