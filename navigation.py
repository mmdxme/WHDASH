"""
Unified Navigation/Menu System
============================
Centralized navigation structure for the WHDASH platform.

This module provides:
- Single source of truth for all navigation menus
- Hierarchical menu structure (top-level → sections → items)
- Permission-based menu visibility
- Multi-language support for menu labels
- Breadcrumb and page title helpers

MENU STRUCTURE:
- Modules (top-level) → Sections → Menu Items
- Each item has: label, icon, route, permission, badge, children

USAGE:
    from navigation import (
        get_main_menu, get_breadcrumbs,
        get_page_title, MENU_STRUCTURE
    )

    # In templates:
    {{ render_menu(get_main_menu(current_user.id)) }}
"""

from typing import List, Dict, Optional, Any

# ============================================================================
# MENU DEFINITIONS
# ============================================================================

# Each module has a key, label, icon, route prefix, and items
# Items can have: label, route, icon, permission (module, resource, action), badge

MENU_STRUCTURE = {
    'profile': {
        'label': 'My Profile',
        'label_ar': 'ملفي',
        'label_fa': 'پروفایل من',
        'icon': 'fa-user-circle',
        'icon_type': 'fas',
        'route': '/profile',
        'permission': None,
        'order': -1,  # Show near top, before other modules
        'items': {
            'profile_overview': {
                'label': 'Profile Overview',
                'label_ar': 'نظرة عامة',
                'label_fa': 'دید کلی',
                'icon': 'fa-home',
                'route': '/profile',
                'permission': None,
            },
            'profile_personal': {
                'label': 'Personal Information',
                'label_ar': 'المعلومات الشخصية',
                'label_fa': 'اطلاعات شخصی',
                'icon': 'fa-user',
                'route': '/profile/personal',
                'permission': None,
            },
            'profile_username': {
                'label': 'Username & Identity',
                'label_ar': 'اسم المستخدم والهوية',
                'label_fa': 'نام کاربری و هویت',
                'icon': 'fa-id-card',
                'route': '/profile/username',
                'permission': None,
            },
            'profile_avatar': {
                'label': 'Profile Photo',
                'label_ar': 'صورة الملف',
                'label_fa': 'عکس پروفایل',
                'icon': 'fa-camera',
                'route': '/profile/avatar',
                'permission': None,
            },
            'profile_contact': {
                'label': 'Contact Information',
                'label_ar': 'معلومات الاتصال',
                'label_fa': 'اطلاعات تماس',
                'icon': 'fa-envelope',
                'route': '/profile/contact',
                'permission': None,
            },
            'profile_work': {
                'label': 'Work Information',
                'label_ar': 'معلومات العمل',
                'label_fa': 'اطلاعات کاری',
                'icon': 'fa-briefcase',
                'route': '/profile/work',
                'permission': None,
            },
            'divider_profile_settings': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'profile_preferences': {
                'label': 'Preferences',
                'label_ar': 'التفضيلات',
                'label_fa': 'ترجیحات',
                'icon': 'fa-sliders-h',
                'route': '/profile/preferences',
                'permission': None,
            },
            'profile_appearance': {
                'label': 'Appearance',
                'label_ar': 'المظهر',
                'label_fa': 'ظاهر',
                'icon': 'fa-palette',
                'route': '/profile/appearance',
                'permission': None,
            },
            'profile_notifications': {
                'label': 'Notifications',
                'label_ar': 'الإشعارات',
                'label_fa': 'اعلان‌ها',
                'icon': 'fa-bell',
                'route': '/profile/notifications',
                'permission': None,
            },
            'divider_profile_security': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'profile_security': {
                'label': 'Security',
                'label_ar': 'الأمان',
                'label_fa': 'امنیت',
                'icon': 'fa-shield-alt',
                'route': '/profile/security',
                'permission': None,
            },
            'profile_sessions': {
                'label': 'Sessions',
                'label_ar': 'الجلسات',
                'label_fa': 'نشست‌ها',
                'icon': 'fa-laptop',
                'route': '/profile/sessions',
                'permission': None,
            },
            'profile_privacy': {
                'label': 'Privacy',
                'label_ar': 'الخصوصية',
                'label_fa': 'حریم خصوصی',
                'icon': 'fa-lock',
                'route': '/profile/privacy',
                'permission': None,
            },
            'profile_activity': {
                'label': 'Activity Log',
                'label_ar': 'سجل النشاط',
                'label_fa': 'گزارش فعالیت',
                'icon': 'fa-history',
                'route': '/profile/activity',
                'permission': None,
            },
            'profile_linked': {
                'label': 'Linked Accounts',
                'label_ar': 'الحسابات المرتبطة',
                'label_fa': 'حساب‌های مرتبط',
                'icon': 'fa-link',
                'route': '/profile/linked-accounts',
                'permission': None,
            },
        }
    },
    'dashboard': {
        'label': 'Dashboard',
        'label_ar': 'لوحة القيادة',
        'label_fa': 'داشبورد',
        'icon': 'fa-th-large',
        'icon_type': 'fas',
        'route': '/',
        'permission': None,  # Available to all authenticated users
        'order': 0,
        'items': None,  # No sub-items, this IS the item
    },
    'sales': {
        'label': 'Sales',
        'label_ar': 'المبيعات',
        'label_fa': 'فروش',
        'icon': 'fa-chart-line',
        'icon_type': 'fas',
        'route': '/sales/dashboard',
        'permission': ('sales', 'dashboard', 'view'),
        'order': 1,
        'items': {
            'sales_dashboard': {
                'label': 'Sales Dashboard',
                'label_ar': 'لوحة المبيعات',
                'label_fa': 'داشبورد فروش',
                'icon': 'fa-th-large',
                'route': '/sales/dashboard',
                'permission': ('sales', 'dashboard', 'view'),
            },
            'sales_suite_dashboard': {
                'label': 'Suite Dashboard',
                'label_ar': 'لوحة متكاملة',
                'label_fa': 'داشبورد جامع',
                'icon': 'fa-chart-pie',
                'route': '/sales/dashboard/suite',
                'permission': ('sales', 'dashboard', 'view'),
            },
            'divider_sales_main': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'sales_customers': {
                'label': 'Customers & Accounts',
                'label_ar': 'العملاء والحسابات',
                'label_fa': 'مشتریان و حساب‌ها',
                'icon': 'fa-users',
                'route': '/sales/customers/',
                'permission': ('sales', 'customers', 'view'),
            },
            'sales_inquiries': {
                'label': 'Leads & Inquiries',
                'label_ar': 'العملاء المحتملين والاستفسارات',
                'label_fa': 'سرنخ‌ها و سوالات',
                'icon': 'fa-question-circle',
                'route': '/sales/inquiries/',
                'permission': ('sales', 'inquiries', 'view'),
            },
            'sales_opportunities': {
                'label': 'Sales Opportunities',
                'label_ar': 'الفرص البيعية',
                'label_fa': 'فرص فروش',
                'icon': 'fa-bullseye',
                'route': '/sales/opportunities/',
                'permission': ('sales', 'opportunities', 'view'),
            },
            'divider_sales_quoting': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'sales_pricing': {
                'label': 'Pricing & Conditions',
                'label_ar': 'التسعير والشروط',
                'label_fa': 'قیمت‌گذاری و شرایط',
                'icon': 'fa-tag',
                'route': '/sales/pricing/',
                'permission': ('sales', 'pricing', 'view'),
            },
            'sales_quotations': {
                'label': 'Quotations',
                'label_ar': 'عروض الأسعار',
                'label_fa': 'پیش‌فاکتورها',
                'icon': 'fa-file-invoice',
                'route': '/sales/quotations/',
                'permission': ('sales', 'quotations', 'view'),
            },
            'sales_proforma': {
                'label': 'Proforma Invoices',
                'label_ar': 'فواتير Proforma',
                'label_fa': 'فاکتورهای Proforma',
                'icon': 'fa-file-invoice-dollar',
                'route': '/sales/proforma/invoices/',
                'permission': ('sales', 'proforma', 'view'),
            },
            'sales_customer_pos': {
                'label': 'Customer POs',
                'label_ar': 'طلبات الشراء',
                'label_fa': 'سفارشات خرید مشتری',
                'icon': 'fa-file-signature',
                'route': '/sales/customer-pos/',
                'permission': ('sales', 'customer_po', 'view'),
            },
            'sales_confirmations': {
                'label': 'Sales Confirmations',
                'label_ar': 'تأكيدات المبيعات',
                'label_fa': 'تأییدیات فروش',
                'icon': 'fa-file-contract',
                'route': '/sales/confirmations/',
                'permission': ('sales', 'confirmations', 'view'),
            },
            'sales_orders': {
                'label': 'Sales Orders',
                'label_ar': 'طلبات البيع',
                'label_fa': 'سفارشات فروش',
                'icon': 'fa-shopping-cart',
                'route': '/sales/orders/',
                'permission': ('sales', 'orders', 'view'),
            },
            'divider_sales_fulfillment': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'sales_reservations': {
                'label': 'Reservations & Allocation',
                'label_ar': 'الحجوزات والتخصيص',
                'label_fa': 'رزرو و تخصیص',
                'icon': 'fa-lock',
                'route': '/sales/reservations/',
                'permission': ('sales', 'reservations', 'view'),
            },
            'sales_deliveries': {
                'label': 'Delivery & Dispatch',
                'label_ar': 'التوصيل والشحن',
                'label_fa': 'تحویل و اعزام',
                'icon': 'fa-truck',
                'route': '/sales/deliveries/',
                'permission': ('sales', 'deliveries', 'view'),
            },
            'sales_invoices': {
                'label': 'Sales Invoices',
                'label_ar': 'فواتير المبيعات',
                'label_fa': 'فاکتورهای فروش',
                'icon': 'fa-file-invoice',
                'route': '/sales/invoices/',
                'permission': ('sales', 'invoices', 'view'),
            },
            'divider_sales_workflows': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'sales_local': {
                'label': 'Local Sales',
                'label_ar': 'المبيعات المحلية',
                'label_fa': 'فروش محلی',
                'icon': 'fa-store',
                'route': '/sales/local-sales/',
                'permission': ('sales', 'orders', 'view'),
            },
            'sales_export': {
                'label': 'Export Sales',
                'label_ar': 'المبيعات التصديرية',
                'label_fa': 'فروش صادراتی',
                'icon': 'fa-plane',
                'route': '/sales/export-sales/',
                'permission': ('sales', 'orders', 'view'),
            },
            'sales_returns': {
                'label': 'Returns & Complaints',
                'label_ar': 'المرتجعات والشكاوى',
                'label_fa': 'بازگشت‌ها و شکایات',
                'icon': 'fa-undo',
                'route': '/sales/returns/',
                'permission': ('sales', 'returns', 'view'),
            },
            'divider_sales_performance': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'sales_targets': {
                'label': 'Targets & Performance',
                'label_ar': 'الأهداف والأداء',
                'label_fa': 'اهداف و عملکرد',
                'icon': 'fa-trophy',
                'route': '/sales/targets/',
                'permission': ('sales', 'targets', 'view'),
            },
            'sales_contracts': {
                'label': 'Contracts & Documents',
                'label_ar': 'العقود والمستندات',
                'label_fa': 'قراردادها و اسناد',
                'icon': 'fa-file-contract',
                'route': '/sales/contracts/',
                'permission': ('sales', 'contracts', 'view'),
            },
            'sales_activities': {
                'label': 'Activities & CRM',
                'label_ar': 'الأنشطة و CRM',
                'label_fa': 'فعالیت‌ها و CRM',
                'icon': 'fa-tasks',
                'route': '/sales/activities/',
                'permission': ('sales', 'activities', 'view'),
            },
            'sales_alerts': {
                'label': 'Sales Alerts',
                'label_ar': 'تنبيهات المبيعات',
                'label_fa': 'هشدارهای فروش',
                'icon': 'fa-bell',
                'route': '/sales/alerts/',
                'permission': ('sales', 'alerts', 'view'),
            },
            'sales_commissions': {
                'label': 'Commissions',
                'label_ar': 'العمولات',
                'label_fa': 'کارمزدها',
                'icon': 'fa-percentage',
                'route': '/sales/commissions/',
                'permission': ('sales', 'commissions', 'view'),
            },
            'divider_sales_reports': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'sales_reports': {
                'label': 'Reports & Analytics',
                'label_ar': 'التقارير والتحليلات',
                'label_fa': 'گزارشات و تحلیل‌ها',
                'icon': 'fa-chart-bar',
                'route': '/sales/reports/',
                'permission': ('sales', 'sales_reports', 'view'),
            },
            'divider_sales_settings': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'sales_settings': {
                'label': 'Settings',
                'label_ar': 'الإعدادات',
                'label_fa': 'تنظیمات',
                'icon': 'fa-cog',
                'route': '/sales/settings/',
                'permission': ('sales', 'settings', 'view'),
            },
        }
    },
    'crm': {
        'label': 'Customers',
        'label_ar': 'العملاء',
        'label_fa': 'مشتریان',
        'icon': 'fa-users',
        'icon_type': 'fas',
        'route': '/customers',
        'permission': ('crm', 'dashboard', 'view'),
        'order': 2,
        'items': {
            'customer_list': {
                'label': 'Customer List',
                'label_ar': 'قائمة العملاء',
                'label_fa': 'لیست مشتریان',
                'icon': 'fa-list',
                'route': '/customers',
                'permission': ('crm', 'customers', 'view'),
            },
            'customer_segments': {
                'label': 'Segments',
                'label_ar': 'الشرائح',
                'label_fa': 'بخش‌ها',
                'icon': 'fa-layer-group',
                'route': '/customers/segments',
                'permission': ('crm', 'segments', 'view'),
            },
            'customer_activities': {
                'label': 'Activities',
                'label_ar': 'الأنشطة',
                'label_fa': 'فعالیت‌ها',
                'icon': 'fa-tasks',
                'route': '/customers/activities',
                'permission': ('crm', 'activities', 'view'),
            },
            'customer_reports': {
                'label': 'Customer Reports',
                'label_ar': 'تقارير العملاء',
                'label_fa': 'گزارشات مشتریان',
                'icon': 'fa-chart-pie',
                'route': '/customers/reports',
                'permission': ('crm', 'reports', 'view'),
            },
        }
    },
    'warehouse': {
        'label': 'Warehouse',
        'label_ar': 'المستودع',
        'label_fa': 'انبار',
        'icon': 'fa-warehouse',
        'icon_type': 'fas',
        'route': None,
        'permission': ('wms', 'dashboard', 'view'),
        'order': 3,
        'items': {
            'inventory': {
                'label': 'Inventory',
                'label_ar': 'المخزون',
                'label_fa': 'موجودی',
                'icon': 'fa-boxes',
                'route': '/api/inventory',
                'permission': ('wms', 'inventory', 'view'),
            },
            'stock_movements': {
                'label': 'Stock Movements',
                'label_ar': 'حركات المخزون',
                'label_fa': 'حرکات موجودی',
                'icon': 'fa-arrows-alt-h',
                'route': '/stock-sync',
                'permission': ('wms', 'stock_movements', 'view'),
            },
            'items': {
                'label': 'Items / Parts',
                'label_ar': 'السلع / القطع',
                'label_fa': 'کالاها / قطعات',
                'icon': 'fa-cube',
                'route': '/settings',
                'permission': ('wms', 'items', 'view'),
            },
            'locations': {
                'label': 'Locations',
                'label_ar': 'المواقع',
                'label_fa': 'مکان‌ها',
                'icon': 'fa-map-marker-alt',
                'route': '/location_settings',
                'permission': ('wms', 'locations', 'view'),
            },
            'stock_count': {
                'label': 'Stock Count',
                'label_ar': 'جرد المخزون',
                'label_fa': 'شمارش موجودی',
                'icon': 'fa-clipboard-list',
                'route': '/wms/stock-counts',
                'permission': ('wms', 'stock_count', 'view'),
            },
            'receipts': {
                'label': 'Receipts',
                'label_ar': 'الاستلامات',
                'label_fa': 'رسیدها',
                'icon': 'fa-truck-loading',
                'route': '/wms/receipts',
                'permission': ('wms', 'receipts', 'view'),
            },
            'shipments': {
                'label': 'Shipments',
                'label_ar': 'الشحنات',
                'label_fa': 'حمل‌ونقل',
                'icon': 'fa-shipping-fast',
                'route': '/wms/shipments',
                'permission': ('wms', 'shipments', 'view'),
            },
            'returns': {
                'label': 'Returns',
                'label_ar': 'المرتجعات',
                'label_fa': 'بازگشت‌ها',
                'icon': 'fa-undo',
                'route': '/wms/returns',
                'permission': ('wms', 'returns', 'view'),
            },
            'transfers': {
                'label': 'Transfers',
                'label_ar': 'التحويلات',
                'label_fa': 'انتقال‌ها',
                'icon': 'fa-exchange-alt',
                'route': '/wms/transfers',
                'permission': ('wms', 'transfers', 'view'),
            },
            'wms_reports': {
                'label': 'WMS Reports',
                'label_ar': 'تقارير المستودع',
                'label_fa': 'گزارشات انبار',
                'icon': 'fa-chart-bar',
                'route': '/wms/reports',
                'permission': ('wms', 'reports', 'view'),
            },
        }
    },
    'logistics': {
        'label': 'Logistics',
        'label_ar': 'الخدمات اللوجستية',
        'label_fa': 'لجستیک',
        'icon': 'fa-truck',
        'icon_type': 'fas',
        'route': None,
        'permission': ('logistics', 'dashboard', 'view'),
        'order': 4,
        'items': {
            'delivery': {
                'label': 'Delivery Management',
                'label_ar': 'إدارة التوصيل',
                'label_fa': 'مدیریت تحویل',
                'icon': 'fa-truck',
                'route': '/delivery',
                'permission': ('logistics', 'trips', 'view'),
            },
            'routes': {
                'label': 'Routes',
                'label_ar': 'المسارات',
                'label_fa': 'مسیرها',
                'icon': 'fa-route',
                'route': '/logistics/routes',
                'permission': ('logistics', 'routes', 'view'),
            },
            'dispatch': {
                'label': 'Dispatch',
                'label_ar': 'الإرسال',
                'label_fa': 'ارسال',
                'icon': 'fa-clipboard-check',
                'route': '/logistics/dispatch',
                'permission': ('logistics', 'dispatch', 'view'),
            },
            'vehicles': {
                'label': 'Vehicles',
                'label_ar': 'المركبات',
                'label_fa': 'وسایل نقلیه',
                'icon': 'fa-shuttle-van',
                'route': '/logistics/vehicles',
                'permission': ('logistics', 'vehicles', 'view'),
            },
            'drivers': {
                'label': 'Drivers',
                'label_ar': 'السائقين',
                'label_fa': 'رانندگان',
                'icon': 'fa-id-card',
                'route': '/logistics/drivers',
                'permission': ('logistics', 'drivers', 'view'),
            },
            'delivery_reports': {
                'label': 'Delivery Reports',
                'label_ar': 'تقارير التوصيل',
                'label_fa': 'گزارشات تحویل',
                'icon': 'fa-chart-line',
                'route': '/delivery_report',
                'permission': ('logistics', 'delivery_reports', 'view'),
            },
            'logistics_settings': {
                'label': 'Logistics Settings',
                'label_ar': 'إعدادات الخدمات',
                'label_fa': 'تنظیمات لجستیک',
                'icon': 'fa-cog',
                'route': '/delivery_settings',
                'permission': ('logistics', 'settings', 'view'),
            },
        }
    },
    'procurement': {
        'label': 'Procurement',
        'label_ar': 'المشتريات',
        'label_fa': 'خرید',
        'icon': 'fa-shopping-basket',
        'icon_type': 'fas',
        'route': '/procurement/dashboard',
        'permission': ('procurement', 'dashboard', 'view'),
        'order': 5,
        'items': {
            'proc_dashboard': {
                'label': 'Procurement Dashboard',
                'label_ar': 'لوحة المشتريات',
                'label_fa': 'داشبورد خرید',
                'icon': 'fa-th-large',
                'route': '/procurement/dashboard',
                'permission': ('procurement', 'dashboard', 'view'),
            },
            'divider_proc_main': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'proc_suppliers': {
                'label': 'Suppliers',
                'label_ar': 'الموردين',
                'label_fa': 'تأمین‌دهندگان',
                'icon': 'fa-boxes',
                'route': '/procurement/suppliers',
                'permission': ('procurement', 'suppliers', 'view'),
            },
            'proc_requisitions': {
                'label': 'Purchase Requisitions',
                'label_ar': 'طلبات الشراء',
                'label_fa': 'درخواست‌های خرید',
                'icon': 'fa-file-alt',
                'route': '/procurement/requisitions',
                'permission': ('procurement', 'requisitions', 'view'),
            },
            'proc_rfqs': {
                'label': 'RFQ / Inquiries',
                'label_ar': 'استفسارات الموردين',
                'label_fa': 'RFQ / استعلام‌ها',
                'icon': 'fa-paper-plane',
                'route': '/procurement/rfqs',
                'permission': ('procurement', 'rfqs', 'view'),
            },
            'proc_quotations': {
                'label': 'Quotations',
                'label_ar': 'عروض الأسعار',
                'label_fa': 'پیشنهادات قیمت',
                'icon': 'fa-file-invoice-dollar',
                'route': '/procurement/quotations',
                'permission': ('procurement', 'quotations', 'view'),
            },
            'proc_orders': {
                'label': 'Purchase Orders',
                'label_ar': 'أوامر الشراء',
                'label_fa': 'سفارشات خرید',
                'icon': 'fa-shopping-cart',
                'route': '/procurement/orders',
                'permission': ('procurement', 'orders', 'view'),
            },
            'divider_proc_logistics': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'proc_shipments': {
                'label': 'Shipment Tracking',
                'label_ar': 'تتبع الشحن',
                'label_fa': 'پیگیری محموله',
                'icon': 'fa-ship',
                'route': '/procurement/shipments',
                'permission': ('procurement', 'shipments', 'view'),
            },
            'proc_receiving': {
                'label': 'Receiving',
                'label_ar': 'الاستلام',
                'label_fa': 'دریافت',
                'icon': 'fa-truck-loading',
                'route': '/procurement/receiving',
                'permission': ('procurement', 'receiving', 'view'),
            },
            'proc_local': {
                'label': 'Local Purchasing',
                'label_ar': 'المشتريات المحلية',
                'label_fa': 'خرید محلی',
                'icon': 'fa-store',
                'route': '/procurement/local',
                'permission': ('procurement', 'local', 'view'),
            },
            'proc_import': {
                'label': 'Import Purchasing',
                'label_ar': 'المشتريات الاستيرادية',
                'label_fa': 'خرید وارداتی',
                'icon': 'fa-plane',
                'route': '/procurement/import',
                'permission': ('procurement', 'import', 'view'),
            },
            'divider_proc_claims': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'proc_claims': {
                'label': 'Claims & Returns',
                'label_ar': 'المطالبات والمرتجعات',
                'label_fa': 'ادعاها و بازگشت‌ها',
                'icon': 'fa-exclamation-triangle',
                'route': '/procurement/claims',
                'permission': ('procurement', 'claims', 'view'),
            },
            'proc_contracts': {
                'label': 'Contracts & Agreements',
                'label_ar': 'العقود والاتفاقيات',
                'label_fa': 'قراردادها',
                'icon': 'fa-file-contract',
                'route': '/procurement/contracts',
                'permission': ('procurement', 'contracts', 'view'),
            },
            'divider_proc_performance': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'proc_performance': {
                'label': 'Supplier Performance',
                'label_ar': 'أداء الموردين',
                'label_fa': 'عملکرد تأمین‌دهندگان',
                'icon': 'fa-chart-line',
                'route': '/procurement/performance',
                'permission': ('procurement', 'performance', 'view'),
            },
            'proc_reports': {
                'label': 'Reports & Analytics',
                'label_ar': 'التقارير والتحليلات',
                'label_fa': 'گزارشات و تحلیل‌ها',
                'icon': 'fa-chart-bar',
                'route': '/procurement/reports',
                'permission': ('procurement', 'reports', 'view'),
            },
            'divider_proc_settings': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'proc_settings': {
                'label': 'Settings',
                'label_ar': 'الإعدادات',
                'label_fa': 'تنظیمات',
                'icon': 'fa-cog',
                'route': '/procurement/settings',
                'permission': ('procurement', 'settings', 'view'),
            },
        }
    },
    'planning': {
        'label': 'Planning',
        'label_ar': 'التخطيط',
        'label_fa': 'برنامه‌ریزی',
        'icon': 'fa-chart-line',
        'icon_type': 'fas',
        'route': None,
        'permission': ('planning', 'dashboard', 'view'),
        'order': 6,
        'items': {
            'forecast_center': {
                'label': 'Forecast Center',
                'label_ar': 'مركز التوقعات',
                'label_fa': 'مرکز پیش‌بینی',
                'icon': 'fa-chart-area',
                'route': '/planning/forecast',
                'permission': ('planning', 'forecasts', 'view'),
            },
            'demand_analysis': {
                'label': 'Demand Analysis',
                'label_ar': 'تحليل الطلب',
                'label_fa': 'تحلیل تقاضا',
                'icon': 'fa-chart-bar',
                'route': '/planning/demand-analysis',
                'permission': ('planning', 'demand', 'view'),
            },
            'inventory_health': {
                'label': 'Inventory Health',
                'label_ar': 'صحة المخزون',
                'label_fa': 'سلامت موجودی',
                'icon': 'fa-heartbeat',
                'route': '/planning/inventory-health',
                'permission': ('planning', 'dashboard', 'view'),
            },
            'replenishment': {
                'label': 'Replenishment',
                'label_ar': 'إعادة التعبئة',
                'label_fa': 'تکمیل موجودی',
                'icon': 'fa-sync',
                'route': '/planning/replenishment',
                'permission': ('planning', 'replenishment', 'view'),
            },
            'purchase_suggestions': {
                'label': 'Purchase Suggestions',
                'label_ar': 'اقتراحات الشراء',
                'label_fa': 'پیشنهادات خرید',
                'icon': 'fa-lightbulb',
                'route': '/planning/purchase-suggestions',
                'permission': ('planning', 'replenishment', 'view'),
            },
            'scenarios': {
                'label': 'Scenarios',
                'label_ar': 'السيناريوهات',
                'label_fa': 'سناریوها',
                'icon': 'fa-magic',
                'route': '/planning/scenarios',
                'permission': ('planning', 'scenarios', 'view'),
            },
            'alerts': {
                'label': 'Alerts',
                'label_ar': 'التنبيهات',
                'label_fa': 'هشدارها',
                'icon': 'fa-bell',
                'route': '/planning/alerts',
                'permission': ('planning', 'alerts', 'view'),
            },
            'planning_reports': {
                'label': 'Planning Reports',
                'label_ar': 'تقارير التخطيط',
                'label_fa': 'گزارشات برنامه‌ریزی',
                'icon': 'fa-chart-pie',
                'route': '/planning/reports',
                'permission': ('planning', 'reports', 'view'),
            },
            'planning_settings': {
                'label': 'Settings',
                'label_ar': 'الإعدادات',
                'label_fa': 'تنظیمات',
                'icon': 'fa-cog',
                'route': '/planning/settings',
                'permission': ('planning', 'settings', 'view'),
            },
        }
    },
    'hr': {
        'label': 'HR',
        'label_ar': 'الموارد البشرية',
        'label_fa': 'منابع انسانی',
        'icon': 'fa-user-tie',
        'icon_type': 'fas',
        'route': None,
        'permission': ('hr', 'dashboard', 'view'),
        'order': 7,
        'items': {
            'hr_dashboard': {
                'label': 'HR Dashboard',
                'label_ar': 'لوحة HR',
                'label_fa': 'داشبورد HR',
                'icon': 'fa-th-large',
                'route': '/hr/dashboard',
                'permission': ('hr', 'dashboard', 'view'),
            },
            'employees': {
                'label': 'Employees',
                'label_ar': 'الموظفين',
                'label_fa': 'کارکنان',
                'icon': 'fa-users',
                'route': '/hr/employees',
                'permission': ('hr', 'employees', 'view'),
            },
            'departments': {
                'label': 'Departments',
                'label_ar': 'الأقسام',
                'label_fa': 'دپارتمان‌ها',
                'icon': 'fa-building',
                'route': '/hr/departments',
                'permission': ('hr', 'departments', 'view'),
            },
            'positions': {
                'label': 'Positions',
                'label_ar': 'المناصب',
                'label_fa': 'سمت‌ها',
                'icon': 'fa-user-tag',
                'route': '/hr/positions',
                'permission': ('hr', 'positions', 'view'),
            },
            'attendance': {
                'label': 'Attendance',
                'label_ar': 'الحضور',
                'label_fa': 'حضور',
                'icon': 'fa-clock',
                'route': '/hr/attendance',
                'permission': ('hr', 'attendance', 'view'),
            },
            'leave': {
                'label': 'Leave',
                'label_ar': 'الإجازات',
                'label_fa': 'مرخصی',
                'icon': 'fa-calendar-alt',
                'route': '/hr/leave',
                'permission': ('hr', 'leave', 'view'),
            },
            'payroll': {
                'label': 'Payroll',
                'label_ar': 'الرواتب',
                'label_fa': 'حقوق',
                'icon': 'fa-money-check-alt',
                'route': '/hr/payroll',
                'permission': ('hr', 'payroll', 'view'),
            },
            'overtime': {
                'label': 'Overtime',
                'label_ar': 'العمل الإضافي',
                'label_fa': 'اضافه‌کاری',
                'icon': 'fa-hourglass-half',
                'route': '/hr/overtime',
                'permission': ('hr', 'overtime', 'view'),
            },
            'loans': {
                'label': 'Loans',
                'label_ar': 'السلف',
                'label_fa': 'وام',
                'icon': 'fa-hand-holding-usd',
                'route': '/hr/loans',
                'permission': ('hr', 'loans', 'view'),
            },
            'documents': {
                'label': 'Documents',
                'label_ar': 'المستندات',
                'label_fa': 'اسناد',
                'icon': 'fa-file-alt',
                'route': '/hr/documents',
                'permission': ('hr', 'documents', 'view'),
            },
            'announcements': {
                'label': 'Announcements',
                'label_ar': 'الإعلانات',
                'label_fa': 'اطلاعیه‌ها',
                'icon': 'fa-bullhorn',
                'route': '/hr/announcements',
                'permission': ('hr', 'announcements', 'view'),
            },
            'recruitment': {
                'label': 'Recruitment',
                'label_ar': 'التوظيف',
                'label_fa': 'استخدام',
                'icon': 'fa-user-plus',
                'route': '/hr/recruitment',
                'permission': ('hr', 'recruitment', 'view'),
            },
            'performance': {
                'label': 'Performance',
                'label_ar': 'الأداء',
                'label_fa': 'عملکرد',
                'icon': 'fa-chart-line',
                'route': '/hr/performance',
                'permission': ('hr', 'performance', 'view'),
            },
            'hr_reports': {
                'label': 'HR Reports',
                'label_ar': 'تقارير HR',
                'label_fa': 'گزارشات HR',
                'icon': 'fa-chart-bar',
                'route': '/hr/reports',
                'permission': ('hr', 'reports', 'view'),
            },
            'hr_settings': {
                'label': 'Settings',
                'label_ar': 'الإعدادات',
                'label_fa': 'تنظیمات',
                'icon': 'fa-cog',
                'route': '/hr/settings',
                'permission': ('hr', 'settings', 'view'),
            },
        }
    },
    'marketing': {
        'label': 'Marketing',
        'label_ar': 'التسويق',
        'label_fa': 'بازاریابی',
        'icon': 'fa-bullhorn',
        'icon_type': 'fas',
        'route': None,
        'permission': ('marketing', 'dashboard', 'view'),
        'order': 8,
        'items': {
            'marketing_dashboard': {
                'label': 'Marketing Dashboard',
                'label_ar': 'لوحة التسويق',
                'label_fa': 'داشبورد بازاریابی',
                'icon': 'fa-th-large',
                'route': '/marketing/dashboard',
                'permission': ('marketing', 'dashboard', 'view'),
            },
            'campaigns': {
                'label': 'Campaigns',
                'label_ar': 'الحملات',
                'label_fa': 'کمپین‌ها',
                'icon': 'fa-flag',
                'route': '/marketing/campaigns',
                'permission': ('marketing', 'campaigns', 'view'),
            },
            'leads': {
                'label': 'Leads',
                'label_ar': 'العملاء المحتملين',
                'label_fa': 'سرنخ‌ها',
                'icon': 'fa-user-clock',
                'route': '/marketing/leads',
                'permission': ('marketing', 'leads', 'view'),
            },
            'channels': {
                'label': 'Channels',
                'label_ar': 'القنوات',
                'label_fa': 'کانال‌ها',
                'icon': 'fa-broadcast-tower',
                'route': '/marketing/channels',
                'permission': ('marketing', 'channels', 'view'),
            },
            'content': {
                'label': 'Content',
                'label_ar': 'المحتوى',
                'label_fa': 'محتوا',
                'icon': 'fa-edit',
                'route': '/marketing/content',
                'permission': ('marketing', 'content', 'view'),
            },
            'advertisements': {
                'label': 'Advertisements',
                'label_ar': 'الإعلانات',
                'label_fa': 'تبلیغات',
                'icon': 'fa-ad',
                'route': '/marketing/advertisements',
                'permission': ('marketing', 'advertisements', 'view'),
            },
            'offers': {
                'label': 'Offers',
                'label_ar': 'العروض',
                'label_fa': 'پیشنهادات',
                'icon': 'fa-gift',
                'route': '/marketing/offers',
                'permission': ('marketing', 'offers', 'view'),
            },
            'budgets': {
                'label': 'Budgets',
                'label_ar': 'الميزانيات',
                'label_fa': 'بودجه‌ها',
                'icon': 'fa-calculator',
                'route': '/marketing/budgets',
                'permission': ('marketing', 'budgets', 'view'),
            },
            'marketing_reports': {
                'label': 'Marketing Reports',
                'label_ar': 'تقارير التسويق',
                'label_fa': 'گزارشات بازاریابی',
                'icon': 'fa-chart-pie',
                'route': '/marketing/reports',
                'permission': ('marketing', 'reports', 'view'),
            },
            'marketing_settings': {
                'label': 'Settings',
                'label_ar': 'الإعدادات',
                'label_fa': 'تنظیمات',
                'icon': 'fa-cog',
                'route': '/marketing/settings',
                'permission': ('marketing', 'settings', 'view'),
            },
        }
    },
    'customer_intelligence': {
        'label': 'Customer Intel',
        'label_ar': 'ذكاء العملاء',
        'label_fa': 'هوش مشتری',
        'icon': 'fa-brain',
        'icon_type': 'fas',
        'route': None,
        'permission': ('customer_intelligence', 'dashboard', 'view'),
        'order': 9,
        'items': {
            'ci_dashboard': {
                'label': 'CI Dashboard',
                'label_ar': 'لوحة CI',
                'label_fa': 'داشبورد CI',
                'icon': 'fa-th-large',
                'route': '/customer-intelligence/dashboard',
                'permission': ('customer_intelligence', 'dashboard', 'view'),
            },
            'customer_profiles': {
                'label': 'Customer Profiles',
                'label_ar': 'ملفات العملاء',
                'label_fa': 'پروفایل مشتریان',
                'icon': 'fa-user-circle',
                'route': '/customer-intelligence/profiles',
                'permission': ('customer_intelligence', 'profiles', 'view'),
            },
            'ci_segments': {
                'label': 'Segments',
                'label_ar': 'الشرائح',
                'label_fa': 'بخش‌ها',
                'icon': 'fa-layer-group',
                'route': '/customer-intelligence/segments',
                'permission': ('customer_intelligence', 'segments', 'view'),
            },
            'ci_forecasts': {
                'label': 'Forecasts',
                'label_ar': 'التوقعات',
                'label_fa': 'پیش‌بینی‌ها',
                'icon': 'fa-chart-area',
                'route': '/customer-intelligence/forecasts',
                'permission': ('customer_intelligence', 'forecasts', 'view'),
            },
            'ci_alerts': {
                'label': 'Risk Alerts',
                'label_ar': 'تنبيهات المخاطر',
                'label_fa': 'هشدارهای ریسک',
                'icon': 'fa-exclamation-triangle',
                'route': '/customer-intelligence/alerts',
                'permission': ('customer_intelligence', 'alerts', 'view'),
            },
            'ci_recommendations': {
                'label': 'Recommendations',
                'label_ar': 'التوصيات',
                'label_fa': 'توصیه‌ها',
                'icon': 'fa-lightbulb',
                'route': '/customer-intelligence/recommendations',
                'permission': ('customer_intelligence', 'recommendations', 'view'),
            },
            'ci_reports': {
                'label': 'CI Reports',
                'label_ar': 'تقارير CI',
                'label_fa': 'گزارشات CI',
                'icon': 'fa-chart-pie',
                'route': '/customer-intelligence/reports',
                'permission': ('customer_intelligence', 'reports', 'view'),
            },
        }
    },
    'tasks': {
        'label': 'Tasks',
        'label_ar': 'المهام',
        'label_fa': 'وظایف',
        'icon': 'fa-tasks',
        'icon_type': 'fas',
        'route': '/tasks',
        'permission': ('tasks', 'dashboard', 'view'),
        'order': 10,
        'items': None,
    },
    'issues': {
        'label': 'Issues',
        'label_ar': 'المشكلات',
        'label_fa': 'مشکلات',
        'icon': 'fa-exclamation-circle',
        'icon_type': 'fas',
        'route': '/issues',
        'permission': ('tasks', 'tasks', 'view'),
        'order': 11,
        'items': None,
    },
    'reports': {
        'label': 'Reports',
        'label_ar': 'التقارير',
        'label_fa': 'گزارشات',
        'icon': 'fa-chart-bar',
        'icon_type': 'fas',
        'route': None,
        'permission': ('reports', 'executive', 'view'),
        'order': 12,
        'items': {
            'executive_dashboard': {
                'label': 'Executive Dashboard',
                'label_ar': 'لوحة تنفيذية',
                'label_fa': 'داشبورد اجرایی',
                'icon': 'fa-chart-pie',
                'route': '/executive-dashboard',
                'permission': ('reports', 'executive', 'view'),
            },
            'operational_reports': {
                'label': 'Operational Reports',
                'label_ar': 'التقارير التشغيلية',
                'label_fa': 'گزارشات عملیاتی',
                'icon': 'fa-chart-line',
                'route': '/reports',
                'permission': ('reports', 'operational', 'view'),
            },
            'stock_summary': {
                'label': 'Stock Summary',
                'label_ar': 'ملخص المخزون',
                'label_fa': 'خلاصه موجودی',
                'icon': 'fa-boxes',
                'route': '/stock-summary-report',
                'permission': ('wms', 'reports', 'view'),
            },
            'low_stock': {
                'label': 'Low Stock Alerts',
                'label_ar': 'تنبيهات انخفاض المخزون',
                'label_fa': 'هشدار موجودی کم',
                'icon': 'fa-exclamation-triangle',
                'route': '/low-stock-alerts',
                'permission': ('wms', 'reports', 'view'),
            },
            'out_of_stock': {
                'label': 'Out of Stock',
                'label_ar': 'نفاد المخزون',
                'label_fa': 'ناموجود',
                'icon': 'fa-times-circle',
                'route': '/out-of-stock',
                'permission': ('wms', 'reports', 'view'),
            },
            'category_report': {
                'label': 'Category Report',
                'label_ar': 'تقرير الفئة',
                'label_fa': 'گزارش دسته',
                'icon': 'fa-tags',
                'route': '/category-report',
                'permission': ('wms', 'reports', 'view'),
            },
        }
    },
    'management_dashboard': {
        'label': 'Management Dashboard',
        'label_ar': 'لوحة الإدارة',
        'label_fa': 'داشبورد مدیریت',
        'icon': 'fa-chart-line',
        'icon_type': 'fas',
        'route': '/executive-dashboard',
        'permission': ('reports', 'executive', 'view'),
        'order': 13,
        'items': {
            'bi_executive': {
                'label': 'Executive Dashboard',
                'label_ar': 'اللوحة التنفيذية',
                'label_fa': 'داشبورد اجرایی',
                'icon': 'fa-chart-pie',
                'route': '/executive-dashboard',
                'permission': ('reports', 'executive', 'view'),
            },
            'bi_holding': {
                'label': 'Holding Dashboard',
                'label_ar': 'لوحة الشركة القابضة',
                'label_fa': 'داشبورد هولدینگ',
                'icon': 'fa-building',
                'route': '/holding-dashboard',
                'permission': ('reports', 'executive', 'view'),
            },
            'bi_sales': {
                'label': 'Sales Performance',
                'label_ar': 'أداء المبيعات',
                'label_fa': 'عملکرد فروش',
                'icon': 'fa-chart-line',
                'route': '/sales-performance',
                'permission': ('reports', 'sales', 'view'),
            },
            'bi_inventory': {
                'label': 'Inventory Performance',
                'label_ar': 'أداء المخزون',
                'label_fa': 'عملکرد موجودی',
                'icon': 'fa-boxes',
                'route': '/inventory-performance',
                'permission': ('reports', 'inventory', 'view'),
            },
            'bi_logistics': {
                'label': 'Logistics Performance',
                'label_ar': 'أداء الخدمات اللوجستية',
                'label_fa': 'عملکرد لجستیک',
                'icon': 'fa-truck',
                'route': '/logistics-performance',
                'permission': ('reports', 'logistics', 'view'),
            },
            'bi_procurement': {
                'label': 'Procurement Performance',
                'label_ar': 'أداء المشتريات',
                'label_fa': 'عملکرد خرید',
                'icon': 'fa-shopping-basket',
                'route': '/procurement-performance',
                'permission': ('reports', 'procurement', 'view'),
            },
            'bi_hr': {
                'label': 'HR & Workforce',
                'label_ar': 'الموارد البشرية',
                'label_fa': 'منابع انسانی',
                'icon': 'fa-user-tie',
                'route': '/hr-performance',
                'permission': ('reports', 'hr', 'view'),
            },
            'bi_finance': {
                'label': 'Finance & Collections',
                'label_ar': 'المالية والتحصيل',
                'label_fa': 'مالی و وصولی',
                'icon': 'fa-coins',
                'route': '/finance-performance',
                'permission': ('reports', 'finance', 'view'),
            },
            'bi_marketing': {
                'label': 'Marketing Performance',
                'label_ar': 'أداء التسويق',
                'label_fa': 'عملکرد بازاریابی',
                'icon': 'fa-bullhorn',
                'route': '/marketing-performance',
                'permission': ('reports', 'marketing', 'view'),
            },
            'divider_bi_alerts': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'bi_risk_alerts': {
                'label': 'Risk Alerts & Exceptions',
                'label_ar': 'تنبيهات المخاطر والاستثناءات',
                'label_fa': 'هشدارهای ریسک و استثناها',
                'icon': 'fa-exclamation-triangle',
                'route': '/risk-alerts',
                'permission': ('reports', 'executive', 'view'),
            },
            'bi_reports': {
                'label': 'Consolidated Reports',
                'label_ar': 'التقارير الموحدة',
                'label_fa': 'گزارشات تلفیقی',
                'icon': 'fa-file-alt',
                'route': '/reports/consolidated',
                'permission': ('reports', 'executive', 'view'),
            },
            'divider_bi_settings': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'bi_settings': {
                'label': 'BI Settings',
                'label_ar': 'إعدادات BI',
                'label_fa': 'تنظیمات BI',
                'icon': 'fa-cog',
                'route': '/bi/settings',
                'permission': ('reports', 'executive', 'view'),
            },
        }
    },
    'admin': {
        'label': 'Admin',
        'label_ar': 'الإدارة',
        'label_fa': 'مدیریت',
        'icon': 'fa-cog',
        'icon_type': 'fas',
        'route': None,
        'permission': ('platform', 'settings', 'view'),
        'order': 98,
        'items': {
            'company_dashboard': {
                'label': 'Company Dashboard',
                'label_ar': 'لوحة الشركة',
                'label_fa': 'داشبورد شرکت',
                'icon': 'fa-building',
                'route': '/company/dashboard',
                'permission': ('platform', 'settings', 'view'),
            },
            'divider_company_main': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'company_list': {
                'label': 'Companies',
                'label_ar': 'الشركات',
                'label_fa': 'شرکت‌ها',
                'icon': 'fa-building',
                'route': '/company/list',
                'permission': ('platform', 'settings', 'view'),
            },
            'company_branches': {
                'label': 'Branches & Facilities',
                'label_ar': 'الفروع والمرافق',
                'label_fa': 'شعب و تاسیسات',
                'icon': 'fa-code-branch',
                'route': '/company/list',
                'permission': ('platform', 'settings', 'view'),
            },
            'company_users': {
                'label': 'User & Access',
                'label_ar': 'المستخدمين والوصول',
                'label_fa': 'کاربران و دسترسی',
                'icon': 'fa-user-shield',
                'route': '/company/list',
                'permission': ('platform', 'settings', 'view'),
            },
            'divider_company_inter': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'intercompany_workflows': {
                'label': 'Intercompany Workflows',
                'label_ar': 'سير العمل بين الشركات',
                'label_fa': 'گردش‌کار بین شرکتی',
                'icon': 'fa-exchange-alt',
                'route': '/company/intercompany/workflows',
                'permission': ('platform', 'settings', 'view'),
            },
            'intercompany_transactions': {
                'label': 'Intercompany Transactions',
                'label_ar': 'المعاملات بين الشركات',
                'label_fa': 'تراکنش‌های بین شرکتی',
                'icon': 'fa-random',
                'route': '/company/intercompany/transactions',
                'permission': ('platform', 'settings', 'view'),
            },
            'divider_company_gov': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'shared_data_rules': {
                'label': 'Data Governance',
                'label_ar': 'حوكمة البيانات',
                'label_fa': 'حاکمه داده',
                'icon': 'fa-database',
                'route': '/company/shared-data/rules',
                'permission': ('platform', 'settings', 'view'),
            },
            'company_hierarchy': {
                'label': 'Company Hierarchy',
                'label_ar': 'تسلسل الشركات',
                'label_fa': 'سلسله مراتب شرکت',
                'icon': 'fa-sitemap',
                'route': '/company/hierarchy',
                'permission': ('platform', 'settings', 'view'),
            },
        },
    },
    'administration': {
        'label': 'Administration',
        'label_ar': 'الإدارة',
        'label_fa': 'مدیریت',
        'icon': 'fa-cog',
        'icon_type': 'fas',
        'route': '/admin/dashboard',
        'permission': ('platform', 'settings', 'view'),
        'order': 99,
        'items': {
            'admin_dashboard': {
                'label': 'Admin Dashboard',
                'label_ar': 'لوحة التحكم',
                'label_fa': 'داشبورد مدیریت',
                'icon': 'fa-th-large',
                'route': '/admin/dashboard',
                'permission': ('platform', 'settings', 'view'),
            },
            'system_settings': {
                'label': 'System Settings',
                'label_ar': 'إعدادات النظام',
                'label_fa': 'تنظیمات سیستم',
                'icon': 'fa-sliders-h',
                'route': '/admin/settings',
                'permission': ('platform', 'settings', 'view'),
            },
            'divider_settings_main': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'master_data': {
                'label': 'Master Data',
                'label_ar': 'البيانات الرئيسية',
                'label_fa': 'داده‌های اصلی',
                'icon': 'fa-database',
                'route': '/admin/master-data',
                'permission': ('platform', 'settings', 'view'),
            },
            'numbering_rules': {
                'label': 'Numbering Rules',
                'label_ar': 'قواعد الترقيم',
                'label_fa': 'قوانین شماره‌گذاری',
                'icon': 'fa-hashtag',
                'route': '/admin/numbering',
                'permission': ('platform', 'settings', 'view'),
            },
            'workflows': {
                'label': 'Workflows',
                'label_ar': 'سير العمل',
                'label_fa': 'گردش‌کارها',
                'icon': 'fa-project-diagram',
                'route': '/admin/workflows',
                'permission': ('platform', 'settings', 'view'),
            },
            'notifications': {
                'label': 'Notifications',
                'label_ar': 'الإشعارات',
                'label_fa': 'اعلان‌ها',
                'icon': 'fa-bell',
                'route': '/admin/notifications',
                'permission': ('platform', 'settings', 'view'),
            },
            'divider_users': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'user_management': {
                'label': 'Users',
                'label_ar': 'المستخدمين',
                'label_fa': 'کاربران',
                'icon': 'fa-user-cog',
                'route': '/admin/users',
                'permission': ('platform', 'users', 'view'),
            },
            'roles_permissions': {
                'label': 'Roles & Permissions',
                'label_ar': 'الأدوار والصلاحيات',
                'label_fa': 'نقش‌ها و مجوزها',
                'icon': 'fa-shield-alt',
                'route': '/admin/roles',
                'permission': ('platform', 'permissions', 'view'),
            },
            'access_scopes': {
                'label': 'Access Scopes',
                'label_ar': 'نطاقات الوصول',
                'label_fa': 'دسترسی‌ها',
                'icon': 'fa-shield-virus',
                'route': '/admin/access-scopes',
                'permission': ('platform', 'settings', 'view'),
            },
            'organization': {
                'label': 'Organization',
                'label_ar': 'المنظمة',
                'label_fa': 'سازمان',
                'icon': 'fa-sitemap',
                'route': '/admin/organization',
                'permission': ('platform', 'settings', 'view'),
            },
            'personalization': {
                'label': 'Personalization',
                'label_ar': 'الإضفاء الشخصي',
                'label_fa': 'شخصی‌سازی',
                'icon': 'fa-palette',
                'route': '/admin/personalization',
                'permission': ('platform', 'settings', 'view'),
            },
            'divider_audit': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'audit_log': {
                'label': 'Audit Log',
                'label_ar': 'سجل التدقيق',
                'label_fa': 'گزارش حسابرسی',
                'icon': 'fa-history',
                'route': '/admin/audit',
                'permission': ('platform', 'audit_log', 'view'),
            },
            'settings_history': {
                'label': 'Settings History',
                'label_ar': 'سجل الإعدادات',
                'label_fa': 'تاریخچه تنظیمات',
                'icon': 'fa-clipboard-list',
                'route': '/admin/audit/settings',
                'permission': ('platform', 'audit_log', 'view'),
            },
            'divider_org': {
                'label': '---',
                'icon': None,
                'route': None,
                'permission': None,
                'divider': True,
            },
            'organization': {
                'label': 'Organization',
                'label_ar': 'الهيكل التنظيمي',
                'label_fa': 'ساختار سازمانی',
                'icon': 'fa-sitemap',
                'route': '/admin/settings/ORGANIZATION',
                'permission': ('platform', 'settings', 'view'),
            },
            'email_settings': {
                'label': 'Email Settings',
                'label_ar': 'إعدادات البريد',
                'label_fa': 'تنظیمات ایمیل',
                'icon': 'fa-envelope',
                'route': '/email/settings',
                'permission': ('platform', 'settings', 'view'),
            },
            'preferences': {
                'label': 'My Preferences',
                'label_ar': 'تفضيلاتي',
                'label_fa': 'ترجیحات من',
                'icon': 'fa-user',
                'route': '/preferences',
                'permission': None,  # Available to all
            },
        }
    },
}


# ============================================================================
# LANGUAGE HELPER
# ============================================================================

def get_menu_label(item: Dict, language: str = 'en') -> str:
    """
    Get the localized label for a menu item.
    
    Args:
        item: Menu item dict
        language: Language code (en, ar, fa)
    
    Returns:
        Localized label or default English
    """
    if language == 'ar' and item.get('label_ar'):
        return item['label_ar']
    elif language == 'fa' and item.get('label_fa'):
        return item['label_fa']
    return item.get('label', item.get('label_en', 'Untitled'))


# ============================================================================
# MENU FILTERING BY PERMISSION
# ============================================================================

def filter_menu_by_permission(menu: Dict, user_permissions: set) -> bool:
    """
    Check if a menu item should be visible based on user permissions.
    
    Args:
        menu: Menu item dict
        user_permissions: Set of permission strings the user has
    
    Returns:
        True if visible, False otherwise
    """
    # No permission required = visible to all authenticated users
    if menu.get('permission') is None:
        return True
    
    module, resource, action = menu['permission']
    
    # Check direct permission
    perm_string = f"{module}.{resource}.{action}"
    if perm_string in user_permissions:
        return True
    
    # Check wildcard permissions
    resource_wildcard = f"{module}.{resource}.*"
    if resource_wildcard in user_permissions:
        return True
    
    module_wildcard = f"{module}.*"
    if module_wildcard in user_permissions:
        return True
    
    return False


# ============================================================================
# MENU BUILDING
# ============================================================================

def get_main_menu(user_id: int, language: str = 'en') -> List[Dict]:
    """
    Build the main menu for a user based on their permissions.
    
    Args:
        user_id: Current user ID
        language: Language code for labels
    
    Returns:
        List of top-level menu items with nested sub-items
    """
    from permissions import get_user_permissions_cached
    
    permissions = get_user_permissions_cached(user_id)
    
    menu = []
    
    # Sort modules by order
    sorted_modules = sorted(
        MENU_STRUCTURE.items(),
        key=lambda x: x[1].get('order', 999)
    )
    
    for module_key, module_data in sorted_modules:
        # Check if user has permission for this module
        if not filter_menu_by_permission(module_data, permissions):
            continue
        
        # Build module entry
        module_entry = {
            'key': module_key,
            'label': get_menu_label(module_data, language),
            'icon': module_data.get('icon', 'fa-circle'),
            'icon_type': module_data.get('icon_type', 'fas'),
            'route': module_data.get('route'),
            'items': []
        }
        
        # Add sub-items if present
        if module_data.get('items'):
            for item_key, item_data in module_data['items'].items():
                if filter_menu_by_permission(item_data, permissions):
                    module_entry['items'].append({
                        'key': item_key,
                        'label': get_menu_label(item_data, language),
                        'icon': item_data.get('icon', 'fa-circle'),
                        'route': item_data.get('route'),
                        'badge': item_data.get('badge'),
                    })
        
        menu.append(module_entry)
    
    return menu


def get_sidebar_menu(user_id: int, language: str = 'en') -> List[Dict]:
    """
    Get the sidebar/vertical menu structure.
    Alias for get_main_menu with specific ordering.
    """
    return get_main_menu(user_id, language)


# ============================================================================
# BREADCRUMBS
# ============================================================================

# Route to breadcrumb mapping
ROUTE_BREADCRUMBS = {
    '/': [{'label': 'Home', 'label_ar': 'الرئيسية', 'label_fa': 'خانه'}],
    '/profile': [{'label': 'My Profile', 'label_ar': 'ملفي', 'label_fa': 'پروفایل من'}],
    '/profile/personal': [{'label': 'My Profile', 'label_ar': 'ملفي', 'label_fa': 'پروفایل من'}, {'label': 'Personal Information', 'label_ar': 'معلومات شخصية', 'label_fa': 'اطلاعات شخصی'}],
    '/profile/username': [{'label': 'My Profile', 'label_ar': 'ملفي', 'label_fa': 'پروفایل من'}, {'label': 'Username & Identity', 'label_ar': 'اسم المستخدم', 'label_fa': 'نام کاربری'}],
    '/profile/avatar': [{'label': 'My Profile', 'label_ar': 'ملفي', 'label_fa': 'پروفایل من'}, {'label': 'Profile Photo', 'label_ar': 'صورة الملف', 'label_fa': 'عکس پروفایل'}],
    '/profile/contact': [{'label': 'My Profile', 'label_ar': 'ملفي', 'label_fa': 'پروفایل من'}, {'label': 'Contact', 'label_ar': 'الاتصال', 'label_fa': 'تماس'}],
    '/profile/work': [{'label': 'My Profile', 'label_ar': 'ملفي', 'label_fa': 'پروفایل من'}, {'label': 'Work', 'label_ar': 'العمل', 'label_fa': 'کار'}],
    '/profile/preferences': [{'label': 'My Profile', 'label_ar': 'ملفي', 'label_fa': 'پروفایل من'}, {'label': 'Preferences', 'label_ar': 'التفضيلات', 'label_fa': 'ترجیحات'}],
    '/profile/appearance': [{'label': 'My Profile', 'label_ar': 'ملفي', 'label_fa': 'پروفایل من'}, {'label': 'Appearance', 'label_ar': 'المظهر', 'label_fa': 'ظاهر'}],
    '/profile/notifications': [{'label': 'My Profile', 'label_ar': 'ملفي', 'label_fa': 'پروفایل من'}, {'label': 'Notifications', 'label_ar': 'الإشعارات', 'label_fa': 'اعلان‌ها'}],
    '/profile/security': [{'label': 'My Profile', 'label_ar': 'ملفي', 'label_fa': 'پروفایل من'}, {'label': 'Security', 'label_ar': 'الأمان', 'label_fa': 'امنیت'}],
    '/profile/sessions': [{'label': 'My Profile', 'label_ar': 'ملفي', 'label_fa': 'پروفایل من'}, {'label': 'Sessions', 'label_ar': 'الجلسات', 'label_fa': 'نشست‌ها'}],
    '/profile/privacy': [{'label': 'My Profile', 'label_ar': 'ملفي', 'label_fa': 'پروفایل من'}, {'label': 'Privacy', 'label_ar': 'الخصوصية', 'label_fa': 'حریم خصوصی'}],
    '/profile/activity': [{'label': 'My Profile', 'label_ar': 'ملفي', 'label_fa': 'پروفایل من'}, {'label': 'Activity Log', 'label_ar': 'سجل النشاط', 'label_fa': 'گزارش فعالیت'}],
    '/profile/linked-accounts': [{'label': 'My Profile', 'label_ar': 'ملفي', 'label_fa': 'پروفایل من'}, {'label': 'Linked Accounts', 'label_ar': 'الحسابات المرتبطة', 'label_fa': 'حساب‌های مرتبط'}],
    '/tasks': [{'label': 'Tasks', 'label_ar': 'المهام', 'label_fa': 'وظایف'}],
    '/issues': [{'label': 'Issues', 'label_ar': 'المشكلات', 'label_fa': 'مشکلات'}],
    '/customers': [{'label': 'Customers', 'label_ar': 'العملاء', 'label_fa': 'مشتریان'}],
    '/delivery': [{'label': 'Delivery', 'label_ar': 'التوصيل', 'label_fa': 'تحویل'}],
    '/stock-sync': [{'label': 'Stock Sync', 'label_ar': 'مزامنة المخزون', 'label_fa': 'همگام‌سازی موجودی'}],
    '/reports': [{'label': 'Reports', 'label_ar': 'التقارير', 'label_fa': 'گزارشات'}],
    '/executive-dashboard': [{'label': 'Executive Dashboard', 'label_ar': 'لوحة تنفيذية', 'label_fa': 'داشبورد اجرایی'}],
    '/settings': [{'label': 'Settings', 'label_ar': 'الإعدادات', 'label_fa': 'تنظیمات'}],
    '/preferences': [{'label': 'My Preferences', 'label_ar': 'تفضيلاتي', 'label_fa': 'ترجیحات من'}],
    '/users': [{'label': 'Users', 'label_ar': 'المستخدمين', 'label_fa': 'کاربران'}],
}


def get_breadcrumbs(request_path: str, language: str = 'en') -> List[Dict]:
    """
    Build breadcrumbs for a given request path.
    
    Args:
        request_path: Current URL path
        language: Language code
    
    Returns:
        List of breadcrumb items with labels and URLs
    """
    breadcrumbs = [{'label': 'Home', 'label_ar': 'الرئيسية', 'label_fa': 'خانه', 'url': '/'}]
    
    # Find matching base path
    for path, crumbs in ROUTE_BREADCRUMBS.items():
        if request_path.startswith(path) and path != '/':
            breadcrumbs.extend(crumbs)
            break
    
    return breadcrumbs


# ============================================================================
# PAGE TITLE
# ============================================================================

PAGE_TITLES = {
    '/': 'Dashboard',
    '/tasks': 'Task Management',
    '/issues': 'Issue Tracker',
    '/customers': 'Customer Management',
    '/delivery': 'Delivery Management',
    '/stock-sync': 'Stock Synchronization',
    '/sync-status': 'Sync Status',
    '/low-stock-alerts': 'Low Stock Alerts',
    '/out-of-stock': 'Out of Stock Items',
    '/stock-summary-report': 'Stock Summary Report',
    '/category-report': 'Category Report',
    '/reports': 'Reports Dashboard',
    '/executive-dashboard': 'Executive Dashboard',
    '/settings': 'System Settings',
    '/users': 'User Management',
    '/preferences': 'My Preferences',
    '/hs-codes': 'HS Codes',
    '/parts_settings': 'Parts & Items Settings',
    '/location_settings': 'Location Settings',
    '/delivery_settings': 'Delivery Settings',
    '/admin/warehouses': 'Warehouse Management',
}


def get_page_title(request_path: str, default: str = 'Dashboard') -> str:
    """
    Get the page title for a given path.
    
    Args:
        request_path: Current URL path
        default: Default title if not found
    
    Returns:
        Page title string
    """
    return PAGE_TITLES.get(request_path, default)


# ============================================================================
# ACTIVE MENU DETECTION
# ============================================================================

def is_menu_item_active(item_route: str, current_path: str) -> bool:
    """
    Check if a menu item is currently active (matches current path).
    
    Args:
        item_route: Menu item route
        current_path: Current request path
    
    Returns:
        True if active
    """
    if not item_route:
        return False
    
    # Exact match
    if item_route == current_path:
        return True
    
    # Prefix match for section headers
    if current_path.startswith(item_route + '/'):
        return True
    
    return False


def get_active_module(current_path: str) -> Optional[str]:
    """
    Get the active top-level module key for the current path.
    
    Args:
        current_path: Current request path
    
    Returns:
        Module key or None
    """
    for module_key, module_data in MENU_STRUCTURE.items():
        route = module_data.get('route')
        if route and current_path.startswith(route):
            return module_key
        
        # Check sub-items
        items = module_data.get('items', {})
        for item_key, item_data in items.items():
            item_route = item_data.get('route')
            if item_route and current_path.startswith(item_route):
                return module_key
    
    # Check dashboard specially
    if current_path == '/':
        return 'dashboard'
    
    return None


# ============================================================================
# BADGE HELPERS
# ============================================================================

def get_notification_badge(user_id: int) -> int:
    """Get count of unread notifications for badge display."""
    from database import get_db_context
    with get_db_context() as db:
        result = db.execute(
            "SELECT COUNT(*) as cnt FROM platform_notifications WHERE user_id = ? AND is_read = 0"
        ).fetchone()
        return result['cnt'] if result else 0


def get_task_badge(user_id: int) -> int:
    """Get count of open tasks assigned to user."""
    from database import get_db_context
    with get_db_context() as db:
        result = db.execute(
            "SELECT COUNT(*) as cnt FROM task_items WHERE assigned_to_user_id = ? AND status NOT IN ('Completed', 'Canceled')",
            (user_id,)
        ).fetchone()
        return result['cnt'] if result else 0


# ============================================================================
# TEMPLATE HELPERS
# ============================================================================

def prepare_menu_for_template(menu: List[Dict], current_path: str) -> List[Dict]:
    """
    Prepare menu for template rendering with active states.
    
    Args:
        menu: Menu from get_main_menu
        current_path: Current request path
    
    Returns:
        Menu with active states calculated
    """
    for module in menu:
        module['is_active'] = get_active_module(current_path) == module['key']
        
        if module.get('items'):
            for item in module['items']:
                item['is_active'] = item.get('route') and is_menu_item_active(item['route'], current_path)
        
        # Mark module as active if any child is active
        if not module['is_active'] and module.get('items'):
            module['is_active'] = any(item.get('is_active', False) for item in module['items'])
    
    return menu
