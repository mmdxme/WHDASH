"""
Enterprise Dashboard Routes
==========================
Comprehensive enterprise dashboard providing a unified command center
for the WHDASH platform.

Routes:
- GET /                       → Main Enterprise Dashboard
- GET /dashboard/api/kpis     → KPI data API
- GET /dashboard/api/alerts  → Alerts data API
- POST /dashboard/api/dismiss → Dismiss alert
- POST /dashboard/api/modules/favorite → Toggle module favorite
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from datetime import datetime, timedelta
import random

# Import translations
try:
    from translations import get_translation, TRANSLATIONS
except ImportError:
    # Fallback if translations not available
    def get_translation(lang, key, default=None):
        return default or key
    TRANSLATIONS = {'en': {}}

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

def get_company_id():
    """Get company ID from session."""
    return session.get('company_id', 1)

def get_current_user_id():
    """Get current user ID from session."""
    return session.get('user_id', 1)

def get_user_role():
    """Get current user role."""
    return session.get('user_role', 'Standard User')

def get_user_language():
    """Get user's preferred language."""
    return session.get('language', 'en')

def check_permission(module, resource, action='view'):
    """Check if user has permission for a module/resource."""
    permissions = session.get('permissions', {})
    mod_perms = permissions.get(module, {})
    resource_perms = mod_perms.get(resource, [])
    return action in resource_perms or 'admin' in resource_perms

def t(key, default=None):
    """Shortcut for getting translations."""
    lang = get_user_language()
    return get_translation(lang, key, default)

def get_translated_modules(modules, lang='en'):
    """Translate module labels based on language."""
    translations = {
        'en': {
            'org_planning': 'Org Planning',
            'finance': 'Finance',
            'treasury': 'Treasury',
            'assets': 'Fixed Assets',
            'controlling': 'Controlling',
            'inventory': 'Inventory',
            'logistics': 'Logistics',
            'supply_chain': 'Supply Chain',
            'demand_planning': 'Demand Planning',
            'manufacturing': 'Manufacturing',
            'quality': 'Quality',
            'maintenance': 'Maintenance',
            'hr': 'Human Resources',
            'payroll': 'Payroll',
            'talent': 'Talent',
            'expense': 'Expense',
            'crm': 'CRM',
            'marketing': 'Marketing',
            'ecommerce': 'E-commerce',
            'project': 'Project',
            'investment': 'Investment',
            'bi': 'Business Intelligence',
            'ai': 'AI Copilot',
            'btp': 'BTP',
            'integration': 'Integration',
            'security': 'Security',
            'compliance': 'Compliance',
            'documents': 'Documents',
            'legal': 'Legal',
            'multi_company': 'Multi-company',
            'service': 'Service',
            'supplier': 'Supplier',
            'contingent': 'Contingent Workforce',
            'sustainability': 'Sustainability',
            'rd': 'R&D'
        },
        'fa': {
            'org_planning': 'برنامه‌ریزی سازمانی',
            'finance': 'مالی',
            'treasury': 'خزانه‌داری',
            'assets': 'دارایی‌های ثابت',
            'controlling': 'کنترل',
            'inventory': 'انبار',
            'logistics': 'لجستیک',
            'supply_chain': 'زنجیره تأمین',
            'demand_planning': 'برنامه‌ریزی تقاضا',
            'manufacturing': 'تولید',
            'quality': 'کیفیت',
            'maintenance': 'نگهداری',
            'hr': 'منابع انسانی',
            'payroll': 'حقوق',
            'talent': 'استعداد',
            'expense': 'هزینه',
            'crm': 'مدیریت مشتری',
            'marketing': 'بازاریابی',
            'ecommerce': 'تجارت الکترونیک',
            'project': 'پروژه',
            'investment': 'سرمایه‌گذاری',
            'bi': 'هوش تجاری',
            'ai': 'دستیار هوشمند',
            'btp': 'پلتفرم فناوری',
            'integration': 'یکپارچگی',
            'security': 'امنیت',
            'compliance': 'انطباق',
            'documents': 'اسناد',
            'legal': 'حقوقی',
            'multi_company': 'چندشرکتی',
            'service': 'خدمات',
            'supplier': 'تأمین‌کننده',
            'contingent': 'نیروی کار',
            'sustainability': 'پایداری',
            'rd': 'تحقیق و توسعه'
        },
        'ar': {
            'org_planning': 'التخطيط التنظيمي',
            'finance': 'المالية',
            'treasury': 'الخزينة',
            'assets': 'الأصول الثابتة',
            'controlling': 'الرقابة',
            'inventory': 'المخزون',
            'logistics': 'الخدمات اللوجستية',
            'supply_chain': 'سلسلة التوريد',
            'demand_planning': 'تخطيط الطلب',
            'manufacturing': 'التصنيع',
            'quality': 'الجودة',
            'maintenance': 'الصيانة',
            'hr': 'الموارد البشرية',
            'payroll': 'الرواتب',
            'talent': 'المواهب',
            'expense': 'المصروفات',
            'crm': 'إدارة العملاء',
            'marketing': 'التسويق',
            'ecommerce': 'التجارة الإلكترونية',
            'project': 'المشروع',
            'investment': 'الاستثمار',
            'bi': 'الذكاء التجاري',
            'ai': 'المساعد الذكي',
            'btp': 'منصة التقنية',
            'integration': 'التكامل',
            'security': 'الأمان',
            'compliance': 'الامتثال',
            'documents': 'المستندات',
            'legal': 'القانونية',
            'multi_company': 'متعدد الشركات',
            'service': 'الخدمات',
            'supplier': 'المورد',
            'contingent': 'القوى العاملة',
            'sustainability': 'الاستدامة',
            'rd': 'البحث والتطوير'
        }
    }
    
    return translations.get(lang, translations['en']).get(modules, modules)

# ============================================================================
# MAIN DASHBOARD ROUTE
# ============================================================================

@dashboard_bp.route('/')
def enterprise_dashboard():
    """Main Enterprise Dashboard - The command center of WHDASH."""
    
    lang = session.get('language', 'en')
    user_id = get_current_user_id()
    user_role = get_user_role()
    company_id = get_company_id()
    
    # Build greeting based on time of day using translations
    hour = datetime.now().hour
    if hour < 12:
        time_greeting = t('good_morning', 'Good Morning')
    elif hour < 17:
        time_greeting = t('good_afternoon', 'Good Afternoon')
    else:
        time_greeting = t('good_evening', 'Good Evening')
    
    username = session.get('username', 'User')
    
    # Get localized greeting with username
    greeting_template = t('welcome_greeting', 'Good {time}, {name}')
    greeting = greeting_template.replace('{time}', time_greeting).replace('{name}', username)
    
    # Format current date using translations
    date_formats = {
        'en': '%A, %B %d, %Y',
        'fa': '%Y/%m/%d',
        'ar': '%d %B %Y',
        'ru': '%d.%m.%Y',
        'hi': '%d %B %Y',
        'es': '%d de %B de %Y',
        'zh': '%Y年%m月%d日',
        'de': '%d. %B %Y'
    }
    current_date = datetime.now().strftime(date_formats.get(lang, date_formats['en']))
    
    # Build dashboard data
    dashboard_data = {
        'greeting': greeting,
        'current_date': current_date,
        
        # Notifications
        'notifications': {
            'unread': 5,
            'items': []
        },
        
        # Quick Actions
        'quick_actions': [
            {'label': 'Create Invoice', 'icon': 'file-invoice', 'url': '/finance/ar/create'},
            {'label': 'New Task', 'icon': 'tasks', 'url': '/tasks/create'},
            {'label': 'Upload Document', 'icon': 'upload', 'url': '/documents/upload'},
            {'label': 'Submit Expense', 'icon': 'receipt', 'url': '/expenses/create'},
            {'label': 'Start Workflow', 'icon': 'project-diagram', 'url': '/workflow/start'},
            {'label': 'Schedule Report', 'icon': 'calendar', 'url': '/reports/schedule'},
        ],
        
        # KPIs - Role-based
        'kpis': build_kpis(user_role, company_id),
        
        # Module Categories
        'module_categories': build_module_categories(user_role, lang),
        
        # Recent & Favorite Modules
        'recent_modules': build_recent_modules(user_role),
        'favorite_modules': build_favorite_modules(user_role),
        
        # Alerts
        'alerts': build_alerts(user_role),
        
        # Operational Widgets
        'operational_widgets': build_operational_widgets(user_role),
        
        # Financial Widgets
        'financial_widgets': build_financial_widgets(user_role),
        
        # Workflow Data
        'workflow': build_workflow_data(user_role),
        
        # Flow Data
        'flow': build_flow_data(),
        
        # Personal Productivity
        'personal': build_personal_data(user_id),
        
        # Reports
        'reports': build_reports(user_role),
        
        # AI Insights
        'insights': build_insights(),
        
        # Activity Timeline
        'timeline': build_timeline()
    }
    
    return render_template('dashboard/index.html', 
                         title="Enterprise Dashboard",
                         dashboard=dashboard_data)

# ============================================================================
# KPI BUILDERS
# ============================================================================

def build_kpis(user_role, company_id):
    """Build role-appropriate KPI cards."""
    
    base_kpis = [
        {
            'id': 'pending_approvals',
            'label': 'Pending Approvals',
            'value': 12,
            'formatted_value': '12',
            'icon': 'clipboard-check',
            'severity': 'warning',
            'trend': '+3 today',
            'trend_direction': 'up',
            'subtext': 'Requires attention',
            'link': '/workflow/my-approvals'
        },
        {
            'id': 'critical_alerts',
            'label': 'Critical Alerts',
            'value': 3,
            'formatted_value': '3',
            'icon': 'exclamation-triangle',
            'severity': 'critical',
            'trend': 'Same as yesterday',
            'trend_direction': 'neutral',
            'subtext': 'Immediate action required',
            'link': '/alerts?severity=critical'
        },
        {
            'id': 'overdue_tasks',
            'label': 'Overdue Tasks',
            'value': 7,
            'formatted_value': '7',
            'icon': 'clock',
            'severity': 'warning',
            'trend': '-2 from last week',
            'trend_direction': 'down',
            'subtext': 'Past due date',
            'link': '/tasks?filter=overdue'
        },
        {
            'id': 'open_issues',
            'label': 'Open Issues',
            'value': 15,
            'formatted_value': '15',
            'icon': 'exclamation-circle',
            'severity': 'info',
            'trend': '+5 new today',
            'trend_direction': 'up',
            'subtext': 'Active tracking',
            'link': '/issues'
        }
    ]
    
    # Finance-specific KPIs
    if user_role in ['CFO', 'Finance Manager', 'Treasury Manager', 'Admin']:
        base_kpis.extend([
            {
                'id': 'cash_position',
                'label': 'Cash Position',
                'value': 2450000,
                'formatted_value': 'AED 2.45M',
                'icon': 'wallet',
                'severity': 'success',
                'trend': '+2.3%',
                'trend_direction': 'up',
                'subtext': 'Total available',
                'link': '/finance/treasury/cash-position'
            },
            {
                'id': 'todays_collections',
                'label': "Today's Collections",
                'value': 185000,
                'formatted_value': 'AED 185K',
                'icon': 'hand-holding-dollar',
                'severity': 'info',
                'trend': '85% of target',
                'trend_direction': 'up',
                'subtext': 'vs AED 218K target',
                'link': '/finance/treasury/collections'
            },
            {
                'id': 'due_payments',
                'label': 'Due Payments',
                'value': 425000,
                'formatted_value': 'AED 425K',
                'icon': 'credit-card',
                'severity': 'warning',
                'trend': 'Due in 5 days',
                'trend_direction': 'neutral',
                'subtext': '32 invoices',
                'link': '/finance/treasury/payments'
            },
            {
                'id': 'active_workflows',
                'label': 'Active Workflows',
                'value': 24,
                'formatted_value': '24',
                'icon': 'project-diagram',
                'severity': 'info',
                'trend': '+8 new today',
                'trend_direction': 'up',
                'subtext': 'Running instances',
                'link': '/workflow/dashboard'
            }
        ])
    
    # Operations KPIs
    if user_role in ['COO', 'Warehouse Manager', 'Operations Manager', 'Admin']:
        base_kpis.extend([
            {
                'id': 'stock_health',
                'label': 'Stock Health',
                'value': 94,
                'formatted_value': '94%',
                'icon': 'boxes-stacked',
                'severity': 'success',
                'trend': '+1.2%',
                'trend_direction': 'up',
                'subtext': 'Items in healthy range',
                'link': '/inventory/dashboard'
            },
            {
                'id': 'late_deliveries',
                'label': 'Late Deliveries',
                'value': 4,
                'formatted_value': '4',
                'icon': 'truck-fast',
                'severity': 'critical',
                'trend': '+2 new',
                'trend_direction': 'up',
                'subtext': 'On-time rate: 94%',
                'link': '/logistics/deliveries?status=delayed'
            }
        ])
    
    # HR KPIs
    if user_role in ['HR Manager', 'Admin']:
        base_kpis.extend([
            {
                'id': 'headcount',
                'label': 'Total Headcount',
                'value': 248,
                'formatted_value': '248',
                'icon': 'users',
                'severity': 'info',
                'trend': '+12 this month',
                'trend_direction': 'up',
                'subtext': 'vs 236 last month',
                'link': '/hr/employees'
            }
        ])
    
    # Executive KPIs
    if user_role in ['CEO', 'COO', 'CFO', 'Admin']:
        base_kpis.extend([
            {
                'id': 'revenue_snapshot',
                'label': 'Revenue MTD',
                'value': 8750000,
                'formatted_value': 'AED 8.75M',
                'icon': 'chart-line',
                'severity': 'success',
                'trend': '+18% vs LY',
                'trend_direction': 'up',
                'subtext': 'vs AED 7.4M last year',
                'link': '/reports/revenue'
            },
            {
                'id': 'budget_variance',
                'label': 'Budget Variance',
                'value': -3.2,
                'formatted_value': '-3.2%',
                'icon': 'chart-column',
                'severity': 'warning',
                'trend': 'Under budget',
                'trend_direction': 'down',
                'subtext': 'Favorable variance',
                'link': '/reports/budget'
            }
        ])
    
    return base_kpis

# ============================================================================
# MODULE LAUNCHER BUILDERS
# ============================================================================

def build_module_categories(user_role, lang='en'):
    """Build all 35 module categories with shortcuts."""
    
    categories = [
        {
            'id': 'core_operations',
            'label': 'Core Operations',
            'icon': 'cogs',
            'modules': [
                {'id': 'org_planning', 'label': 'Org Planning', 'icon': 'sitemap', 'url': '/org-planning', 'description': 'BPM & org structure', 'permission': 'org_planning'},
                {'id': 'finance', 'label': 'Finance', 'icon': 'calculator', 'url': '/finance', 'description': 'Accounting & GL', 'permission': 'finance'},
                {'id': 'treasury', 'label': 'Treasury', 'icon': 'wallet', 'url': '/finance/treasury/dashboard', 'description': 'Cash & liquidity', 'permission': 'finance.treasury'},
                {'id': 'assets', 'label': 'Fixed Assets', 'icon': 'building', 'url': '/assets', 'description': 'Asset management', 'permission': 'assets'},
                {'id': 'controlling', 'label': 'Controlling', 'icon': 'chart-pie', 'url': '/finance/reports', 'description': 'Cost accounting', 'permission': 'finance'},
                {'id': 'inventory', 'label': 'Inventory', 'icon': 'boxes', 'url': '/wms/dashboard', 'description': 'Warehouse management', 'permission': 'wms'},
                {'id': 'logistics', 'label': 'Logistics', 'icon': 'truck', 'url': '/logistics', 'description': 'Transportation', 'permission': 'logistics'},
                {'id': 'supply_chain', 'label': 'Supply Chain', 'icon': 'chain', 'url': '/scm', 'description': 'SCM module', 'permission': 'scm'},
                {'id': 'demand_planning', 'label': 'Demand Planning', 'icon': 'chart-line', 'url': '/scm/demand', 'description': 'Forecasting', 'permission': 'planning'},
                {'id': 'manufacturing', 'label': 'Manufacturing', 'icon': 'industry', 'url': '/manufacturing', 'description': 'MES/PP', 'permission': 'manufacturing'},
                {'id': 'quality', 'label': 'Quality', 'icon': 'check-double', 'url': '/quality', 'description': 'QA/QC', 'permission': 'quality'},
                {'id': 'maintenance', 'label': 'Maintenance', 'icon': 'wrench', 'url': '/maintenance', 'description': 'EAM/PM', 'permission': 'maintenance'},
            ]
        },
        {
            'id': 'people_organization',
            'label': 'People & Organization',
            'icon': 'users',
            'modules': [
                {'id': 'hr', 'label': 'Human Resources', 'icon': 'user-tie', 'url': '/hr', 'description': 'Employee management', 'permission': 'hr'},
                {'id': 'payroll', 'label': 'Payroll', 'icon': 'money-check', 'url': '/payroll', 'description': 'Salary processing', 'permission': 'hr.payroll'},
                {'id': 'talent', 'label': 'Talent', 'icon': 'graduation-cap', 'url': '/talent', 'description': 'Talent management', 'permission': 'hr'},
                {'id': 'expense', 'label': 'Expense', 'icon': 'receipt', 'url': '/expense-travel', 'description': 'Travel & expense', 'permission': 'expense_travel'},
            ]
        },
        {
            'id': 'customers_commerce',
            'label': 'Customers & Commerce',
            'icon': 'handshake',
            'modules': [
                {'id': 'crm', 'label': 'CRM', 'icon': 'address-book', 'url': '/crm', 'description': 'Customer relationships', 'permission': 'crm'},
                {'id': 'marketing', 'label': 'Marketing', 'icon': 'megaphone', 'url': '/marketing', 'description': 'Marketing automation', 'permission': 'marketing'},
                {'id': 'ecommerce', 'label': 'E-commerce', 'icon': 'shopping-cart', 'url': '/ecommerce', 'description': 'Online store', 'permission': 'ecommerce'},
                {'id': 'project', 'label': 'Project', 'icon': 'tasks', 'url': '/project', 'description': 'Project management', 'permission': 'project'},
            ]
        },
        {
            'id': 'technology_governance',
            'label': 'Technology & Governance',
            'icon': 'server',
            'modules': [
                {'id': 'investment', 'label': 'Investment', 'icon': 'chart-line', 'url': '/finance/investments', 'description': 'Investment tracking', 'permission': 'finance'},
                {'id': 'bi', 'label': 'BI Dashboard', 'icon': 'chart-bar', 'url': '/bi', 'description': 'Analytics', 'permission': 'bi'},
                {'id': 'ai', 'label': 'AI Copilot', 'icon': 'robot', 'url': '/ai', 'description': 'Intelligent assistant', 'permission': 'ai'},
                {'id': 'btp', 'label': 'BTP', 'icon': 'cloud', 'url': '/btp', 'description': 'Business Technology', 'permission': 'platform'},
                {'id': 'integration', 'label': 'Integration', 'icon': 'plug', 'url': '/integration', 'description': 'Middleware', 'permission': 'platform'},
                {'id': 'security', 'label': 'Security', 'icon': 'shield-alt', 'url': '/security', 'description': 'SSO/MFA', 'permission': 'platform.security'},
                {'id': 'compliance', 'label': 'Compliance', 'icon': 'gavel', 'url': '/grc', 'description': 'GRC', 'permission': 'compliance'},
                {'id': 'documents', 'label': 'Documents', 'icon': 'file-alt', 'url': '/documents', 'description': 'DMS', 'permission': 'documents'},
                {'id': 'legal', 'label': 'Legal', 'icon': 'balance-scale', 'url': '/legal-tax', 'description': 'Tax & legal', 'permission': 'finance'},
                {'id': 'multi_company', 'label': 'Multi-company', 'icon': 'building', 'url': '/multi-entity', 'description': 'Intercompany', 'permission': 'platform'},
            ]
        },
            {
            'id': 'services',
            'label': 'Services',
            'icon': 'headset',
            'modules': [
                {'id': 'service', 'label': 'Service', 'icon': 'bell', 'url': '/scm/service-level', 'description': 'Field service', 'permission': 'scm'},
                {'id': 'supplier', 'label': 'Supplier', 'icon': 'user-tag', 'url': '/procurement/suppliers', 'description': 'Supplier portal', 'permission': 'procurement'},
                {'id': 'contingent', 'label': 'Contingent', 'icon': 'user-clock', 'url': '/hr/employees', 'description': 'Workforce management', 'permission': 'hr'},
                {'id': 'sustainability', 'label': 'Sustainability', 'icon': 'leaf', 'url': '/scm/reports', 'description': 'ESG tracking', 'permission': 'compliance'},
                {'id': 'rd', 'label': 'R&D', 'icon': 'flask', 'url': '/project', 'description': 'Research & development', 'permission': 'project'},
            ]
        }
    ]
    
    # Check permissions and mark favorites
    permissions = session.get('permissions', {})
    for category in categories:
        for module in category['modules']:
            mod_perms = permissions.get(module['permission'].split('.')[0], {})
            has_access = bool(mod_perms)
            module['has_access'] = has_access
            # Simulate some favorites
            module['is_favorite'] = module['id'] in ['finance', 'treasury', 'inventory', 'hr', 'crm', 'projects']
    
    return categories

def build_recent_modules(user_role):
    """Build recently used modules (simulated)."""
    return [
        {'id': 'treasury', 'label': 'Treasury', 'icon': 'wallet', 'url': '/finance/treasury/dashboard'},
        {'id': 'finance', 'label': 'Finance', 'icon': 'calculator', 'url': '/finance'},
        {'id': 'inventory', 'label': 'Inventory', 'icon': 'boxes', 'url': '/'},
    ]

def build_favorite_modules(user_role):
    """Build favorite modules."""
    return [
        {'id': 'treasury', 'label': 'Treasury', 'icon': 'wallet', 'url': '/finance/treasury/dashboard'},
        {'id': 'finance', 'label': 'Finance', 'icon': 'calculator', 'url': '/finance'},
        {'id': 'crm', 'label': 'CRM', 'icon': 'address-book', 'url': '/crm'},
        {'id': 'hr', 'label': 'HR', 'icon': 'user-tie', 'url': '/hr'},
    ]

# ============================================================================
# ALERT BUILDERS
# ============================================================================

def build_alerts(user_role):
    """Build dashboard alerts."""
    
    alerts = {
        'total_count': 6,
        'unread_count': 3,
        'items': [
            {
                'id': 'alert_001',
                'type': 'sla_breach',
                'severity': 'critical',
                'icon': 'exclamation-circle',
                'title': 'Invoice Approval SLA Breached',
                'message': 'INV-2026-0890 is 3 days past the SLA deadline. Immediate approval required.',
                'time_ago': '2 hours ago',
                'action_label': 'Review',
                'action_url': '/finance/ar/invoices/890',
                'dismissible': False
            },
            {
                'id': 'alert_002',
                'type': 'payment_overdue',
                'severity': 'critical',
                'icon': 'credit-card',
                'title': 'Payment Overdue',
                'message': 'AED 45,000 payment to Al-Futtaim Motors is 15 days overdue.',
                'time_ago': '4 hours ago',
                'action_label': 'View',
                'action_url': '/finance/ap/payments/456',
                'dismissible': True
            },
            {
                'id': 'alert_003',
                'type': 'stock_low',
                'severity': 'warning',
                'icon': 'boxes-stacked',
                'title': 'Low Stock Alert',
                'message': 'Spare parts category "Brake Pads" is below reorder point in Dubai warehouse.',
                'time_ago': '5 hours ago',
                'action_label': 'Reorder',
                'action_url': '/inventory/reorder',
                'dismissible': True
            },
            {
                'id': 'alert_004',
                'type': 'transfer_pending',
                'severity': 'warning',
                'icon': 'exchange-alt',
                'title': 'Transfer Approval Pending',
                'message': 'AED 250,000 internal transfer awaiting CFO approval.',
                'time_ago': '1 day ago',
                'action_label': 'Approve',
                'action_url': '/finance/treasury/transfers/789',
                'dismissible': False
            },
            {
                'id': 'alert_005',
                'type': 'document_expired',
                'severity': 'warning',
                'icon': 'file-circle-exclamation',
                'title': 'Document Expiring',
                'message': 'Insurance policy for fleet vehicle VF-123 expires in 30 days.',
                'time_ago': '1 day ago',
                'action_label': 'Renew',
                'action_url': '/documents/renew/123',
                'dismissible': True
            }
        ]
    }
    
    return alerts

# ============================================================================
# OPERATIONAL WIDGET BUILDERS
# ============================================================================

def build_operational_widgets(user_role):
    """Build operational overview widgets."""
    
    return [
        {
            'type': 'kpi',
            'title': 'WMS Health',
            'icon': 'boxes',
            'value': '94%',
            'subtitle': '+1.2% vs last week',
            'badge': '3 Critical',
            'badge_type': 'danger',
            'link': '/inventory/dashboard'
        },
        {
            'type': 'kpi',
            'title': 'Active Shipments',
            'icon': 'truck',
            'value': '24',
            'subtitle': '18 on-time, 4 delayed',
            'badge': '4 Delayed',
            'badge_type': 'warning',
            'link': '/logistics/shipments'
        },
        {
            'type': 'kpi',
            'title': 'Quality Holds',
            'icon': 'check-double',
            'value': '7',
            'subtitle': 'Items pending QC',
            'badge': '2 Urgent',
            'badge_type': 'warning',
            'link': '/quality/holds'
        },
        {
            'type': 'kpi',
            'title': 'Open Work Orders',
            'icon': 'wrench',
            'value': '31',
            'subtitle': '12 preventive, 19 corrective',
            'badge': '5 Overdue',
            'badge_type': 'danger',
            'link': '/maintenance/work-orders'
        }
    ]

# ============================================================================
# FINANCIAL WIDGET BUILDERS
# ============================================================================

def build_financial_widgets(user_role):
    """Build financial snapshot widgets."""
    
    return [
        {
            'title': 'Revenue MTD',
            'icon': 'chart-line',
            'value': 'AED 8.75M',
            'comparison': {'label': 'vs Budget', 'value': '+12.3%', 'direction': 'up'}
        },
        {
            'title': 'Expenses MTD',
            'icon': 'credit-card',
            'value': 'AED 5.2M',
            'comparison': {'label': 'vs Budget', 'value': '-3.1%', 'direction': 'down'}
        },
        {
            'title': 'AR Outstanding',
            'icon': 'file-invoice-dollar',
            'value': 'AED 12.4M',
            'comparison': {'label': 'vs Last Month', 'value': '+8.5%', 'direction': 'up'}
        },
        {
            'title': 'AP Outstanding',
            'icon': 'money-check-alt',
            'value': 'AED 4.8M',
            'comparison': {'label': 'Due This Week', 'value': 'AED 1.2M', 'direction': 'neutral'}
        }
    ]

# ============================================================================
# WORKFLOW BUILDERS
# ============================================================================

def build_workflow_data(user_role):
    """Build workflow and approval data."""
    
    return {
        'pending_count': 12,
        'pending_approvals': [
            {
                'id': 'wf_001',
                'icon': 'file-invoice',
                'title': 'Invoice Approval - AED 85,000',
                'requester': 'Sarah Johnson',
                'time_ago': '2 hours ago'
            },
            {
                'id': 'wf_002',
                'icon': 'shopping-cart',
                'title': 'Purchase Order - AED 125,000',
                'requester': 'Ahmed Al-Maktoum',
                'time_ago': '5 hours ago'
            },
            {
                'id': 'wf_003',
                'icon': 'user-plus',
                'title': 'New Employee Onboarding',
                'requester': 'HR Department',
                'time_ago': '1 day ago'
            },
            {
                'id': 'wf_004',
                'icon': 'wrench',
                'title': 'Equipment Repair - AED 45,000',
                'requester': 'Operations',
                'time_ago': '1 day ago'
            }
        ],
        'sla': {
            'compliance': 87,
            'compliance_color': 'yellow',
            'breaches': 3
        }
    }

# ============================================================================
# FLOW BUILDERS
# ============================================================================

def build_flow_data():
    """Build Flow communication data."""
    
    return {
        'unread_count': 5,
        'announcements': [
            {
                'id': 'ann_001',
                'author': 'CEO Office',
                'author_avatar': None,
                'message': 'Q1 Town Hall meeting scheduled for April 25th at 2:00 PM. All employees are encouraged to attend.',
                'time_ago': '3 hours ago',
                'pinned': True
            },
            {
                'id': 'ann_002',
                'author': 'IT Department',
                'author_avatar': None,
                'message': 'Scheduled maintenance window this Saturday from 2:00 AM to 6:00 AM. Some services may be temporarily unavailable.',
                'time_ago': '1 day ago',
                'pinned': False
            },
            {
                'id': 'ann_003',
                'author': 'HR',
                'author_avatar': None,
                'message': 'Open enrollment for health insurance benefits closes April 30th. Please review your options.',
                'time_ago': '2 days ago',
                'pinned': False
            }
        ],
        'mentions': [
            {
                'id': 'men_001',
                'message': '@you Please review the Q1 financial report when you have a moment.',
                'context': 'In #finance-team channel'
            }
        ]
    }

# ============================================================================
# PERSONAL PRODUCTIVITY BUILDERS
# ============================================================================

def build_personal_data(user_id):
    """Build personal productivity widgets."""
    
    return {
        'tasks': {
            'total': 18,
            'overdue': 3,
            'today': 5,
            'upcoming': 10,
            'items': [
                {'id': 'task_001', 'title': 'Review Q1 financial report', 'due_date': 'Today', 'completed': False},
                {'id': 'task_002', 'title': 'Approve vendor invoices', 'due_date': 'Today', 'completed': False},
                {'id': 'task_003', 'title': 'Team meeting preparation', 'due_date': 'Today', 'completed': False},
                {'id': 'task_004', 'title': 'Update budget forecasts', 'due_date': 'Tomorrow', 'completed': False},
                {'id': 'task_005', 'title': 'Review expense reports', 'due_date': 'Tomorrow', 'completed': False},
            ]
        },
        'issues': {
            'total': 7,
            'by_priority': [
                {'level': 'critical', 'count': 1, 'label': 'Critical'},
                {'level': 'high', 'count': 2, 'label': 'High'},
                {'level': 'medium', 'count': 3, 'label': 'Medium'},
                {'level': 'low', 'count': 1, 'label': 'Low'},
            ]
        }
    }

# ============================================================================
# REPORTS BUILDERS
# ============================================================================

def build_reports(user_role):
    """Build reports and analytics shortcuts."""
    
    return [
        {
            'title': 'CFO Executive Report',
            'description': 'Comprehensive financial overview for leadership',
            'icon': 'file-invoice-dollar',
            'url': '/reports/cfo',
            'last_run': '2 hours ago',
            'frequency': 'Daily'
        },
        {
            'title': 'Operations Dashboard',
            'description': 'Real-time operational metrics and KPIs',
            'icon': 'chart-pie',
            'url': '/reports/operations',
            'last_run': '1 hour ago',
            'frequency': 'Real-time'
        },
        {
            'title': 'HR Analytics',
            'description': 'Workforce metrics and attendance analysis',
            'icon': 'users',
            'url': '/hr/reports',
            'last_run': '1 day ago',
            'frequency': 'Weekly'
        },
        {
            'title': 'Treasury Report',
            'description': 'Cash flow and liquidity analysis',
            'icon': 'wallet',
            'url': '/finance/treasury/reports',
            'last_run': '4 hours ago',
            'frequency': 'Daily'
        },
        {
            'title': 'Inventory Status',
            'description': 'Stock levels and movement analysis',
            'icon': 'boxes',
            'url': '/reports/inventory',
            'last_run': '3 hours ago',
            'frequency': 'Daily'
        },
        {
            'title': 'Sales Performance',
            'description': 'Revenue analysis and pipeline metrics',
            'icon': 'chart-line',
            'url': '/reports/sales',
            'last_run': '1 day ago',
            'frequency': 'Weekly'
        }
    ]

# ============================================================================
# AI INSIGHTS BUILDERS
# ============================================================================

def build_insights():
    """Build AI-generated insights and recommendations."""
    
    return [
        {
            'id': 'ins_001',
            'type': 'attention',
            'type_label': 'Attention Needed',
            'icon': 'exclamation-circle',
            'confidence': 92,
            'title': 'Cash Flow Risk Detected',
            'description': 'Based on current payables and receivables patterns, there is a 78% probability of cash flow shortfall in the next 15 days. Consider accelerating collections or adjusting payment terms.',
            'affected_items': 'AED 2.4M in receivables overdue >30 days',
            'source_module': 'Treasury',
            'time_ago': '1 hour ago',
            'actions': [
                {'label': 'View Details', 'icon': 'eye', 'type': 'secondary', 'url': '/finance/treasury/cash-flow-risk'},
                {'label': 'Take Action', 'icon': 'bolt', 'type': 'primary', 'url': '/finance/treasury/actions#collections'}
            ]
        },
        {
            'id': 'ins_002',
            'type': 'recommendation',
            'type_label': 'Recommendation',
            'icon': 'lightbulb',
            'confidence': 85,
            'title': 'Reorder Point Adjustment',
            'description': 'Based on demand patterns and lead times, consider increasing reorder points for 12 high-velocity items in the Dubai warehouse to reduce stockout risk.',
            'affected_items': '12 SKUs in Automotive Parts category',
            'source_module': 'Inventory',
            'time_ago': '3 hours ago',
            'actions': [
                {'label': 'View SKUs', 'icon': 'list', 'type': 'secondary', 'url': '/inventory/reorder-suggestions'},
                {'label': 'Apply Recommendation', 'icon': 'check', 'type': 'primary', 'url': '/inventory/reorder-suggestions/apply'}
            ]
        },
        {
            'id': 'ins_003',
            'type': 'prediction',
            'type_label': 'Prediction',
            'icon': 'crystal-ball',
            'confidence': 76,
            'title': 'SLA Breach Risk',
            'description': '3 approval workflows are at risk of missing SLA deadlines within the next 24 hours based on current processing times and queue depth.',
            'affected_items': '3 workflow instances',
            'source_module': 'Workflow',
            'time_ago': '5 hours ago',
            'actions': [
                {'label': 'Review Workflows', 'icon': 'project-diagram', 'type': 'primary', 'url': '/workflow/at-risk'}
            ]
        },
        {
            'id': 'ins_004',
            'type': 'attention',
            'type_label': 'Attention Needed',
            'icon': 'chart-line',
            'confidence': 88,
            'title': 'Expense Variance Alert',
            'description': 'Travel expenses in March exceeded budget by 23%. Primary drivers: increased client visits and unplanned conference attendance.',
            'affected_items': 'Marketing and Sales departments',
            'source_module': 'Finance',
            'time_ago': '1 day ago',
            'actions': [
                {'label': 'View Analysis', 'icon': 'chart-bar', 'type': 'secondary', 'url': '/reports/expense-variance'},
                {'label': 'Set Controls', 'icon': 'sliders-h', 'type': 'primary', 'url': '/finance/expense-controls'}
            ]
        }
    ]

# ============================================================================
# TIMELINE BUILDERS
# ============================================================================

def build_timeline():
    """Build activity timeline."""
    
    return [
        {
            'category': 'approvals',
            'event': 'Invoice Approved',
            'details': 'INV-2026-0891 for AED 45,000 approved by CFO',
            'user': 'Mohammed Hassan',
            'time_ago': '15 minutes ago'
        },
        {
            'category': 'documents',
            'event': 'Contract Uploaded',
            'details': 'Service agreement with TechCorp LLC uploaded to DMS',
            'user': 'Legal Team',
            'time_ago': '1 hour ago'
        },
        {
            'category': 'system',
            'event': 'Period Closed',
            'details': 'February 2026 accounting period successfully closed',
            'user': 'System',
            'time_ago': '2 hours ago'
        },
        {
            'category': 'approvals',
            'event': 'Budget Approved',
            'details': 'Q2 2026 department budgets approved for Marketing',
            'user': 'CFO',
            'time_ago': '3 hours ago'
        },
        {
            'category': 'critical',
            'event': 'SLA Breach Alert',
            'details': 'Invoice approval for Emirates Trading Co. breached SLA',
            'user': 'System',
            'time_ago': '4 hours ago'
        },
        {
            'category': 'documents',
            'event': 'Report Generated',
            'details': 'Monthly treasury report generated and distributed',
            'user': 'Treasury Team',
            'time_ago': '5 hours ago'
        },
        {
            'category': 'system',
            'event': 'User Login',
            'details': 'Sarah Johnson logged in from Dubai, UAE',
            'user': 'System',
            'time_ago': '6 hours ago'
        }
    ]

# ============================================================================
# API ROUTES
# ============================================================================

@dashboard_bp.route('/api/kpis')
def api_kpis():
    """Return KPI data as JSON."""
    user_role = get_user_role()
    company_id = get_company_id()
    return jsonify({
        'kpis': build_kpis(user_role, company_id),
        'generated_at': datetime.now().isoformat()
    })

@dashboard_bp.route('/api/alerts')
def api_alerts():
    """Return alerts data as JSON."""
    user_role = get_user_role()
    severity = request.args.get('severity', 'all')
    limit = request.args.get('limit', 10, type=int)
    
    alerts = build_alerts(user_role)
    
    if severity != 'all':
        alerts['items'] = [a for a in alerts['items'] if a['severity'] == severity]
    
    alerts['items'] = alerts['items'][:limit]
    
    return jsonify(alerts)

@dashboard_bp.route('/api/alerts/dismiss', methods=['POST'])
def api_dismiss_alert():
    """Dismiss an alert."""
    data = request.get_json()
    alert_id = data.get('alert_id')
    
    # In production, persist dismissal to database
    return jsonify({'success': True, 'alert_id': alert_id})

@dashboard_bp.route('/api/modules/favorite', methods=['POST'])
def api_toggle_favorite():
    """Toggle module favorite status."""
    data = request.get_json()
    module_id = data.get('module_id')
    
    # In production, persist to user preferences
    return jsonify({'success': True, 'module_id': module_id, 'is_favorite': True})

@dashboard_bp.route('/api/workflow/approve', methods=['POST'])
def api_workflow_approve():
    """Quick approve a workflow item."""
    data = request.get_json()
    approval_id = data.get('approval_id')
    
    # In production, process approval through workflow engine
    return jsonify({'success': True, 'approval_id': approval_id})

@dashboard_bp.route('/api/workflow/reject', methods=['POST'])
def api_workflow_reject():
    """Quick reject a workflow item."""
    data = request.get_json()
    approval_id = data.get('approval_id')

    # In production, process rejection through workflow engine
    return jsonify({'success': True, 'approval_id': approval_id})


@dashboard_bp.route('/api/export/<export_type>')
def api_export(export_type):
    """Export dashboard data in various formats."""
    from export_utils import send_export_response

    # Get current user data
    user_role = get_user_role()
    company_id = get_company_id()

    # Build comprehensive dashboard data
    export_data = {
        'greeting': 'Dashboard Export',
        'current_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'user_role': user_role,
        'company_id': company_id,
        'kpis': build_kpis(user_role, company_id),
        'module_categories': build_module_categories(user_role, 'en'),
        'alerts': build_alerts(user_role),
        'operational_widgets': build_operational_widgets(user_role),
        'financial_widgets': build_financial_widgets(user_role),
        'workflow': build_workflow_data(user_role),
        'flow': build_flow_data(),
        'personal': build_personal_data(get_current_user_id()),
        'reports': build_reports(user_role),
        'insights': build_insights(),
        'timeline': build_timeline()
    }

    # Flatten data for export
    rows = []
    for kpi in export_data['kpis']:
        rows.append({
            'Type': 'KPI',
            'Label': kpi.get('label', ''),
            'Value': kpi.get('value', ''),
            'Formatted Value': kpi.get('formatted_value', ''),
            'Icon': kpi.get('icon', ''),
            'Severity': kpi.get('severity', ''),
            'Trend': kpi.get('trend', ''),
            'Subtext': kpi.get('subtext', ''),
            'Link': kpi.get('link', '')
        })

    for widget in export_data['operational_widgets']:
        rows.append({
            'Type': 'Operational Widget',
            'Label': widget.get('title', ''),
            'Value': widget.get('value', ''),
            'Subtitle': widget.get('subtitle', ''),
            'Badge': widget.get('badge', ''),
            'Icon': widget.get('icon', '')
        })

    for widget in export_data['financial_widgets']:
        rows.append({
            'Type': 'Financial Widget',
            'Label': widget.get('title', ''),
            'Value': widget.get('value', ''),
            'Icon': widget.get('icon', ''),
            'Comparison Label': widget.get('comparison', {}).get('label', ''),
            'Comparison Value': widget.get('comparison', {}).get('value', '')
        })

    for alert in export_data['alerts'].get('items', []):
        rows.append({
            'Type': 'Alert',
            'Title': alert.get('title', ''),
            'Message': alert.get('message', ''),
            'Severity': alert.get('severity', ''),
            'Time': alert.get('time_ago', ''),
            'Action URL': alert.get('action_url', '')
        })

    for insight in export_data['insights']:
        rows.append({
            'Type': 'AI Insight',
            'Title': insight.get('title', ''),
            'Description': insight.get('description', ''),
            'Type Label': insight.get('type_label', ''),
            'Confidence': insight.get('confidence', ''),
            'Source': insight.get('source_module', ''),
            'Time': insight.get('time_ago', '')
        })

    for event in export_data['timeline']:
        rows.append({
            'Type': 'Timeline Event',
            'Event': event.get('event', ''),
            'Details': event.get('details', ''),
            'Category': event.get('category', ''),
            'User': event.get('user', ''),
            'Time': event.get('time_ago', '')
        })

    columns = ['Type', 'Label', 'Value', 'Formatted Value', 'Icon', 'Severity',
               'Trend', 'Subtext', 'Link', 'Subtitle', 'Badge', 'Comparison Label',
               'Comparison Value', 'Message', 'Time', 'Action URL', 'Description',
               'Type Label', 'Confidence', 'Source', 'Details', 'Category', 'User']

    return send_export_response(rows, export_type, 'dashboard_export', columns, 'Dashboard Export')
