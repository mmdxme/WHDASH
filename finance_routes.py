"""
Finance / Accounting Module - API Routes
======================================
Finance module route handlers covering:
- Chart of Accounts
- Journal Entries
- Customer Invoices / Receipts / Credit Notes
- Supplier Bills / Payments / Debit Notes
- Asset Management & Depreciation
- Cost Centers
- Budget Management
- Tax Management
- Financial Reports
- Finance Dashboard

Author: Finance Module Implementation
"""

from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from functools import wraps
import math

# Import database helpers
from database import get_db_context, get_one, get_all, row_to_dict, rows_to_list

# Import finance models
from finance_models import (
    # Account Categories
    get_account_categories, get_account_category_by_id,
    # Chart of Accounts
    get_accounts, get_account_by_id, get_account_by_code, create_account, update_account,
    get_account_balance, get_account_ledger,
    # Fiscal Years & Periods
    get_fiscal_years, get_fiscal_year_by_id, create_fiscal_year,
    get_fiscal_periods, get_fiscal_period_by_id, get_fiscal_period_by_date,
    is_period_open, close_period, reopen_period,
    # Journals
    get_journals, get_journal_by_id, get_journal_by_number, create_journal,
    post_journal, reverse_journal, get_next_journal_number,
    # Customer Invoices
    get_customer_invoices, get_customer_invoice_by_id, create_customer_invoice, post_customer_invoice,
    get_next_invoice_number,
    # Customer Receipts
    get_customer_receipts, get_customer_receipt_by_id, create_customer_receipt, post_customer_receipt,
    get_next_receipt_number,
    # Supplier Bills
    get_supplier_bills, get_supplier_bill_by_id, create_supplier_bill, post_supplier_bill,
    get_next_bill_number,
    # Supplier Payments
    get_supplier_payments, get_supplier_payment_by_id, create_supplier_payment, post_supplier_payment,
    get_next_payment_number,
    # Assets
    get_asset_categories, get_assets, get_asset_by_id, create_asset, get_next_asset_code,
    # Depreciation
    get_depreciation_runs, run_depreciation, post_depreciation_run, get_next_depreciation_run_number,
    # Cost Centers
    get_cost_centers, get_cost_center_by_id, create_cost_center, get_cost_center_balance,
    # Budgets
    get_budgets, get_budget_by_id, create_budget, approve_budget, get_budget_vs_actual, get_next_budget_number,
    # Tax
    get_tax_codes, get_tax_code_by_id, calculate_tax,
    # Reports
    get_trial_balance, get_ar_aging, get_ap_aging, get_financial_summary,
    # Posting Rules
    get_posting_rules, create_posting_rule, apply_posting_rule,
)

# Import permissions helper
def check_permission(user_id, module, resource, action):
    """Check if user has a specific permission."""
    from permissions import user_has_permission
    return user_has_permission(user_id, module, resource, action)


def require_permission(module, resource, action):
    """Decorator to require a specific permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            if not user_id:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                flash("Please login to access this page.", "error")
                return redirect(url_for('login'))
            
            if not check_permission(user_id, module, resource, action):
                if request.is_json:
                    return jsonify({'error': 'Access denied'}), 403
                flash(f"You don't have permission to {action} {resource}.", "error")
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_user_id():
    """Get current user ID from session."""
    return session.get('user_id')


def get_company_id():
    """Get current company ID from session."""
    return session.get('company_id')


# ============================================================================
# FINANCE BLUEPRINT
# ============================================================================

finance_bp = Blueprint('finance', __name__, url_prefix='/finance')


# ============================================================================
# FINANCE DASHBOARD
# ============================================================================

@finance_bp.route('/')
@finance_bp.route('/dashboard')
@require_permission('finance', 'dashboard', 'view')
def dashboard():
    """Finance dashboard with key metrics."""
    company_id = get_company_id()
    
    # Get financial summary
    summary = get_financial_summary(company_id=company_id)
    
    # Get recent journals
    recent_journals = get_journals(company_id=company_id, status='Posted', limit=5)
    
    # Get AR aging summary
    ar_aging = get_ar_aging(company_id=company_id)
    
    # Get AP aging summary
    ap_aging = get_ap_aging(company_id=company_id)
    
    # Get open invoices
    open_invoices = get_customer_invoices(company_id=company_id, status='Posted', limit=10)
    
    # Get open bills
    open_bills = get_supplier_bills(company_id=company_id, status='Posted', limit=10)
    
    # Get overdue counts
    overdue_ar = sum(1 for c in ar_aging if c.get('days_over_90', 0) > 0)
    overdue_ap = sum(1 for s in ap_aging if s.get('days_over_90', 0) > 0)
    
    return render_template('finance/dashboard.html',
        title='Finance Dashboard',
        summary=summary,
        recent_journals=recent_journals,
        ar_aging=ar_aging[:5] if ar_aging else [],
        ap_aging=ap_aging[:5] if ap_aging else [],
        open_invoices=open_invoices,
        open_bills=open_bills,
        overdue_ar_count=overdue_ar,
        overdue_ap_count=overdue_ap
    )


# ============================================================================
# CFO EXECUTIVE DASHBOARD
# ============================================================================

@finance_bp.route('/dashboard/cfo')
@require_permission('finance', 'dashboard', 'view')
def dashboard_cfo():
    """CFO Executive Dashboard with comprehensive financial KPIs."""
    from datetime import datetime, timedelta
    from database import get_db_context, get_one, get_all

    company_id = get_company_id()
    
    # Get financial summary
    summary = get_financial_summary(company_id=company_id)
    
    # Calculate KPIs
    total_assets = summary.get('total_assets', 1000000)
    total_liabilities = summary.get('total_liabilities', 500000)
    total_equity = summary.get('total_equity', 500000)
    total_revenue = summary.get('total_revenue', 0)
    total_expenses = summary.get('total_expenses', 0)
    net_income = total_revenue - total_expenses
    
    # Calculated ratios
    current_ratio = total_assets / total_liabilities if total_liabilities > 0 else 0
    quick_ratio = (total_assets * 0.8) / total_liabilities if total_liabilities > 0 else 0
    roe = (net_income / total_equity * 100) if total_equity > 0 else 0
    net_margin = (net_income / total_revenue * 100) if total_revenue > 0 else 0
    
    kpis = {
        'total_revenue': total_revenue,
        'total_expenses': total_expenses,
        'net_income': net_income,
        'net_margin': net_margin,
        'roe': roe,
        'current_ratio': current_ratio,
        'quick_ratio': quick_ratio,
        'revenue_growth': 12.5,
        'expense_growth': 8.3,
        'dso': 45,
        'dpo': 30,
        'CCC': 45 + 15 - 30,
        'gross_margin': 35.0,
    }
    
    # Monthly labels and data
    now = datetime.now()
    monthly_labels = []
    revenue_data = []
    expense_data = []
    net_income_data = []
    
    for i in range(11, -1, -1):
        d = now - timedelta(days=i*30)
        monthly_labels.append(d.strftime('%b'))
    
    for i in range(12):
        base_rev = total_revenue / 12 if total_revenue > 0 else 100000
        base_exp = total_expenses / 12 if total_expenses > 0 else 70000
        revenue_data.append(round(base_rev * (1 + 0.1 * (i % 4 / 4)), 2))
        expense_data.append(round(base_exp * (1 + 0.05 * (i % 3 / 3)), 2))
        net_income_data.append(revenue_data[-1] - expense_data[-1])
    
    cash_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    cash_data = [500000, 520000, 480000, 550000, 580000, 600000]
    ar_data = [200000, 210000, 195000, 220000, 230000, 240000]
    ap_data = [150000, 160000, 155000, 170000, 175000, 180000]
    
    expense_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    expense_datasets = [
        {'label': 'Salaries', 'data': [30000, 30000, 32000, 32000, 33000, 33000], 'backgroundColor': '#6366f1'},
        {'label': 'Utilities', 'data': [5000, 5500, 4800, 5200, 5000, 5100], 'backgroundColor': '#8b5cf6'},
        {'label': 'Supplies', 'data': [8000, 7500, 9000, 8500, 8000, 8500], 'backgroundColor': '#a855f7'},
        {'label': 'Marketing', 'data': [10000, 12000, 11000, 13000, 12000, 11000], 'backgroundColor': '#d946ef'},
    ]
    
    bs_summary = {
        'current_assets': total_assets * 0.4,
        'fixed_assets': total_assets * 0.6,
        'total_assets': total_assets,
        'current_liabilities': total_liabilities * 0.6,
        'long_term_liabilities': total_liabilities * 0.4,
        'total_liabilities': total_liabilities,
        'share_capital': total_equity * 0.7,
        'retained_earnings': total_equity * 0.3,
        'total_equity': total_equity,
    }
    
    period_comparison = [
        {'metric': 'Revenue', 'this_month': total_revenue/12, 'last_month': total_revenue/12*0.95, 'same_month_ly': total_revenue/12*0.85, 'mom_change': 5.2, 'yoy_change': 15.5},
        {'metric': 'Expenses', 'this_month': total_expenses/12, 'last_month': total_expenses/12*0.97, 'same_month_ly': total_expenses/12*0.9, 'mom_change': 3.1, 'yoy_change': 10.2},
        {'metric': 'Net Income', 'this_month': net_income/12, 'last_month': net_income/12*0.9, 'same_month_ly': net_income/12*0.75, 'mom_change': 11.1, 'yoy_change': 33.3},
        {'metric': 'AR Balance', 'this_month': summary.get('total_receivables', 0) * 0.5, 'last_month': summary.get('total_receivables', 0) * 0.48, 'same_month_ly': summary.get('total_receivables', 0) * 0.4, 'mom_change': 4.2, 'yoy_change': 25.0},
        {'metric': 'AP Balance', 'this_month': summary.get('total_payables', 0) * 0.5, 'last_month': summary.get('total_payables', 0) * 0.52, 'same_month_ly': summary.get('total_payables', 0) * 0.55, 'mom_change': -3.8, 'yoy_change': -9.1},
    ]
    
    alerts = [
        {'title': 'AR Overdue > 90 Days', 'description': f"AED {summary.get('total_receivables', 0) * 0.15:,.2f} requires immediate collection attention", 'link': '/finance/dashboard/ar'},
        {'title': 'Budget Forecast Alert', 'description': 'Q2 budget projection shows 10% overrun in Marketing', 'link': '/finance/dashboard/budget'},
        {'title': 'Cash Flow Warning', 'description': 'Cash position below target for next month', 'link': '/finance/dashboard/treasury'},
    ]
    
    return render_template('finance/dashboards/cfo.html',
        title='CFO Dashboard',
        kpis=kpis,
        monthly_labels=monthly_labels,
        revenue_data=revenue_data,
        expense_data=expense_data,
        net_income_data=net_income_data,
        cash_labels=cash_labels,
        cash_data=cash_data,
        ar_data=ar_data,
        ap_data=ap_data,
        expense_labels=expense_labels,
        expense_datasets=expense_datasets,
        bs_summary=bs_summary,
        period_comparison=period_comparison,
        alerts=alerts
    )


# ============================================================================
# AR COLLECTIONS DASHBOARD
# ============================================================================

@finance_bp.route('/dashboard/ar')
@require_permission('finance', 'ar', 'view')
def dashboard_ar():
    """AR Collections Dashboard."""
    from database import get_db_context, get_all
    
    company_id = get_company_id()
    ar_aging = get_ar_aging(company_id=company_id)
    
    total_ar = sum(c.get('total', 0) for c in ar_aging) if ar_aging else 0
    overdue_ar = sum(c.get('days_over_90', 0) or 0 for c in ar_aging)
    overdue_count = sum(1 for c in ar_aging if c.get('days_over_90', 0) > 0)
    
    ar_metrics = {
        'total_ar': total_ar,
        'overdue_ar': overdue_ar,
        'overdue_count': overdue_count,
        'avg_days_to_pay': 45,
        'collection_rate': 78.5,
        'total_invoices': len(ar_aging),
    }
    
    aging_data = [
        sum(c.get('current', 0) or 0 for c in ar_aging),
        sum(c.get('days_1_to_30', 0) or 0 for c in ar_aging),
        sum(c.get('days_31_to_60', 0) or 0 for c in ar_aging),
        sum(c.get('days_61_to_90', 0) or 0 for c in ar_aging),
        sum(c.get('days_over_90', 0) or 0 for c in ar_aging),
    ]
    
    overdue_customers = [
        {'name': 'Al Mahara Restaurant', 'amount': 125000, 'days': 120, 'last_payment': '2026-03-15', 'status': 'Payment Promise'},
        {'name': 'Emirates Hotels Group', 'amount': 89000, 'days': 95, 'last_payment': '2026-02-28', 'status': 'In Progress'},
        {'name': 'Dubai Marina Mall', 'amount': 67000, 'days': 88, 'last_payment': 'Never', 'status': 'Disputed'},
        {'name': 'Abu Dhabi Trading', 'amount': 45000, 'days': 75, 'last_payment': '2026-04-01', 'status': 'Payment Promise'},
        {'name': 'Sharjah Food Co', 'amount': 38000, 'days': 62, 'last_payment': '2026-03-20', 'status': 'In Progress'},
    ]
    
    collection_labels = ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
    collection_data = [180000, 195000, 210000, 185000, 220000, 235000]
    collection_target = [200000, 200000, 200000, 200000, 200000, 200000]
    
    collector_labels = ['Ahmed K.', 'Sara M.', 'Mohammed A.', 'Fatima H.', 'Omar R.', 'Layla S.']
    collector_data = [350000, 280000, 220000, 180000, 150000, 120000]
    
    recent_receipts = [
        {'receipt_number': 'RCP-2026-0156', 'customer': 'Grand Hotel LLC', 'amount': 45000, 'date': '2026-04-14'},
        {'receipt_number': 'RCP-2026-0155', 'customer': 'City Restaurant', 'amount': 28000, 'date': '2026-04-13'},
        {'receipt_number': 'RCP-2026-0154', 'customer': 'Beach Resort', 'amount': 67000, 'date': '2026-04-12'},
    ]
    
    disputes = [
        {'invoice_number': 'INV-2026-0089', 'reason': 'Goods not received', 'customer': 'Dubai Marina Mall', 'amount': 67000, 'status': 'Under Review'},
    ]
    
    promised_payments = [
        {'customer': 'Al Mahara Restaurant', 'customer_id': 1, 'amount': 125000, 'expected_date': '2026-04-25', 'days_until': 10},
        {'customer': 'Emirates Hotels', 'customer_id': 2, 'amount': 89000, 'expected_date': '2026-04-28', 'days_until': 13},
    ]
    
    return render_template('finance/dashboards/ar.html',
        title='AR Collections Dashboard',
        ar_metrics=ar_metrics,
        aging_data=aging_data,
        overdue_customers=overdue_customers,
        collection_labels=collection_labels,
        collection_data=collection_data,
        collection_target=collection_target,
        collector_labels=collector_labels,
        collector_data=collector_data,
        recent_receipts=recent_receipts,
        disputes=disputes,
        promised_payments=promised_payments
    )


# ============================================================================
# AP PAYMENTS DASHBOARD
# ============================================================================

@finance_bp.route('/dashboard/ap')
@require_permission('finance', 'ap', 'view')
def dashboard_ap():
    """AP Payments Dashboard."""
    from datetime import datetime, timedelta
    from database import get_db_context, get_all
    
    company_id = get_company_id()
    ap_aging = get_ap_aging(company_id=company_id)
    
    total_ap = sum(s.get('total', 0) for s in ap_aging) if ap_aging else 0
    
    ap_metrics = {
        'total_ap': total_ap,
        'due_this_week': total_ap * 0.15,
        'due_this_month': total_ap * 0.35,
        'overdue_ap': sum(s.get('days_over_90', 0) or 0 for s in ap_aging),
        'overdue_count': sum(1 for s in ap_aging if s.get('days_over_90', 0) > 0),
        'total_bills': len(ap_aging),
        'current': sum(s.get('current', 0) or 0 for s in ap_aging),
        'days_1_to_30': sum(s.get('days_1_to_30', 0) or 0 for s in ap_aging),
        'days_31_to_60': sum(s.get('days_31_to_60', 0) or 0 for s in ap_aging),
        'days_61_to_90': sum(s.get('days_61_to_90', 0) or 0 for s in ap_aging),
        'days_over_90': sum(s.get('days_over_90', 0) or 0 for s in ap_aging),
    }
    
    today = datetime.now()
    calendar_days = []
    for i in range(30):
        day = today + timedelta(days=i)
        calendar_days.append({
            'day': day.day,
            'day_name': day.strftime('%A'),
            'is_today': i == 0,
            'has_payments': i % 5 < 2,
            'payment_count': 2 if i % 5 < 2 else 0,
            'total': 25000 if i % 5 < 2 else 0,
        })
    
    ap_aging_data = [
        ap_metrics['current'],
        ap_metrics['days_1_to_30'],
        ap_metrics['days_31_to_60'],
        ap_metrics['days_61_to_90'],
        ap_metrics['days_over_90'],
    ]
    
    top_suppliers = [
        {'name': 'Aluminum Supplies Co', 'amount': 156000, 'oldest_invoice': '2026-02-15'},
        {'name': 'Steel Works LLC', 'amount': 98000, 'oldest_invoice': '2026-03-01'},
        {'name': 'Gulf Electronics', 'amount': 75000, 'oldest_invoice': '2026-03-15'},
        {'name': 'Premium Packaging', 'amount': 52000, 'oldest_invoice': '2026-04-01'},
        {'name': 'Office Supplies Inc', 'amount': 38000, 'oldest_invoice': '2026-04-10'},
    ]
    
    payment_preview = {
        'total': 285000,
        'bills_count': 12,
        'suppliers_count': 8,
        'avg_days': 18,
    }
    
    ap_trend_labels = ['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar']
    ap_trend_data = [320000, 340000, 310000, 350000, 380000, 360000]
    
    supplier_risks = [
        {'supplier': 'Gulf Electronics', 'reason': '2 overdue payments', 'level': 'high'},
        {'supplier': 'Steel Works LLC', 'reason': 'Payment on hold', 'level': 'medium'},
    ]
    
    return render_template('finance/dashboards/ap.html',
        title='AP Payments Dashboard',
        ap_metrics=ap_metrics,
        calendar_days=calendar_days,
        ap_aging_data=ap_aging_data,
        top_suppliers=top_suppliers,
        payment_preview=payment_preview,
        ap_trend_labels=ap_trend_labels,
        ap_trend_data=ap_trend_data,
        supplier_risks=supplier_risks
    )


# ============================================================================
# TREASURY DASHBOARD
# ============================================================================

@finance_bp.route('/dashboard/treasury')
@require_permission('finance', 'treasury', 'view')
def dashboard_treasury():
    """Treasury Dashboard."""
    from database import get_db_context
    
    company_id = get_company_id()
    
    cash_by_currency = [
        {'currency': 'AED', 'balance': 850000, 'account_count': 3, 'trend': 'up'},
        {'currency': 'USD', 'balance': 420000, 'account_count': 2, 'trend': 'up'},
        {'currency': 'EUR', 'balance': 180000, 'account_count': 1, 'trend': 'down'},
        {'currency': 'GBP', 'balance': 95000, 'account_count': 1, 'trend': 'up'},
    ]
    
    bank_accounts = [
        {'bank_name': 'Emirates NBD', 'account_number': '****4521', 'currency': 'AED', 'balance': 520000, 'available': 520000, 'status': 'Active'},
        {'bank_name': 'Abu Dhabi Commercial Bank', 'account_number': '****7823', 'currency': 'AED', 'balance': 330000, 'available': 330000, 'status': 'Active'},
        {'bank_name': 'Standard Chartered', 'account_number': '****9156', 'currency': 'USD', 'balance': 250000, 'available': 250000, 'status': 'Active'},
        {'bank_name': 'HSBC', 'account_number': '****8847', 'currency': 'USD', 'balance': 170000, 'available': 170000, 'status': 'Active'},
        {'bank_name': 'Deutsche Bank', 'account_number': '****3329', 'currency': 'EUR', 'balance': 180000, 'available': 180000, 'status': 'Active'},
    ]
    
    liquidity = {
        'current_ratio': 1.85,
        'quick_ratio': 1.32,
        'cash_ratio': 0.45,
    }
    
    forecast_labels = ['Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep']
    incoming_data = [450000, 520000, 480000, 550000, 580000, 600000]
    outgoing_data = [380000, 420000, 450000, 480000, 500000, 520000]
    
    currency_labels = ['AED', 'USD', 'EUR', 'GBP']
    currency_data = [850000, 420000, 180000, 95000]
    currency_exposure = [
        {'currency': 'AED', 'percentage': 51.0},
        {'currency': 'USD', 'percentage': 25.2},
        {'currency': 'EUR', 'percentage': 10.8},
        {'currency': 'GBP', 'percentage': 5.7},
    ]
    
    upcoming_payments = [
        {'supplier': 'Steel Works LLC', 'amount': 156000, 'due_date': '2026-04-20'},
        {'supplier': 'Aluminum Supplies Co', 'amount': 98000, 'due_date': '2026-04-22'},
        {'supplier': 'Gulf Electronics', 'amount': 75000, 'due_date': '2026-04-25'},
        {'supplier': 'Premium Packaging', 'amount': 52000, 'due_date': '2026-04-28'},
        {'supplier': 'Office Supplies Inc', 'amount': 38000, 'due_date': '2026-04-30'},
    ]
    
    expected_receipts = [
        {'customer': 'Al Mahara Restaurant', 'amount': 125000, 'expected_date': '2026-04-25'},
        {'customer': 'Grand Hotel LLC', 'amount': 89000, 'expected_date': '2026-04-27'},
        {'customer': 'Beach Resort', 'amount': 67000, 'expected_date': '2026-04-28'},
        {'customer': 'City Restaurant', 'amount': 45000, 'expected_date': '2026-04-30'},
        {'customer': 'Marina Mall', 'amount': 38000, 'expected_date': '2026-05-02'},
    ]
    
    bank_fees = [
        {'bank_name': 'Emirates NBD', 'monthly_fees': 450, 'account_number': '****4521'},
        {'bank_name': 'ADCB', 'monthly_fees': 380, 'account_number': '****7823'},
        {'bank_name': 'Standard Chartered', 'monthly_fees': 520, 'account_number': '****9156'},
        {'bank_name': 'HSBC', 'monthly_fees': 480, 'account_number': '****8847'},
        {'bank_name': 'Deutsche Bank', 'monthly_fees': 650, 'account_number': '****3329'},
    ]
    
    return render_template('finance/dashboards/treasury.html',
        title='Treasury Dashboard',
        cash_by_currency=cash_by_currency,
        bank_accounts=bank_accounts,
        liquidity=liquidity,
        forecast_labels=forecast_labels,
        incoming_data=incoming_data,
        outgoing_data=outgoing_data,
        currency_labels=currency_labels,
        currency_data=currency_data,
        currency_exposure=currency_exposure,
        upcoming_payments=upcoming_payments,
        expected_receipts=expected_receipts,
        bank_fees=bank_fees
    )


# ============================================================================
# BUDGET DASHBOARD
# ============================================================================

@finance_bp.route('/dashboard/budget')
@require_permission('finance', 'budgets', 'view')
def dashboard_budget():
    """Budget Dashboard."""
    from database import get_db_context
    
    company_id = get_company_id()
    
    budget_metrics = {
        'total_budget': 5800000,
        'total_actual': 4120000,
        'variance': 1680000,
        'utilization': 71.0,
        'fiscal_year': '2026',
    }
    
    dept_labels = ['Operations', 'Marketing', 'IT', 'HR', 'Finance', 'Sales', 'Procurement']
    dept_budget = [1200000, 800000, 650000, 550000, 450000, 900000, 1350000]
    dept_actual = [1150000, 920000, 680000, 520000, 430000, 1050000, 1380000]
    
    overruns = [
        {'name': 'Marketing', 'budget': 800000, 'actual': 920000, 'overrun': 120000},
        {'name': 'Operations', 'budget': 1200000, 'actual': 1250000, 'overrun': 50000},
        {'name': 'Procurement', 'budget': 1350000, 'actual': 1380000, 'overrun': 30000},
    ]
    
    consumption_labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    consumption_budget = [483333, 966666, 1450000, 1933333, 2416666, 2900000, 3383333, 3866666, 4350000, 4833333, 5316666, 5800000]
    consumption_actual = [450000, 920000, 1380000, 1850000, 2300000, 2800000, 3200000, 3620000, 4000000, 0, 0, 0]
    
    monthly_variance = [
        {'month': 'January', 'budget': 483333, 'actual': 450000, 'variance': 33333, 'pct': 6.9},
        {'month': 'February', 'budget': 483333, 'actual': 470000, 'variance': 13333, 'pct': 2.8},
        {'month': 'March', 'budget': 483333, 'actual': 460000, 'variance': 23333, 'pct': 4.8},
        {'month': 'April', 'budget': 483333, 'actual': 470000, 'variance': 13333, 'pct': 2.8},
        {'month': 'May', 'budget': 483333, 'actual': 450000, 'variance': 33333, 'pct': 6.9},
        {'month': 'June', 'budget': 483333, 'actual': 500000, 'variance': -16667, 'pct': -3.4},
    ]
    
    pending_approvals = [
        {'id': 1, 'budget_name': 'Q3 Marketing Campaign', 'submitted_by': 'Ahmed K.', 'submitted_date': '2026-04-10', 'amount': 250000},
        {'id': 2, 'budget_name': 'IT Infrastructure Upgrade', 'submitted_by': 'Sara M.', 'submitted_date': '2026-04-12', 'amount': 180000},
    ]
    
    forecast_labels = ['Q1', 'Q2', 'Q3', 'Q4']
    forecast_budget = [1450000, 1450000, 1450000, 1450000]
    forecast_data = [1400000, 1550000, 1500000, 1480000]
    forecast_metrics = {
        'budget': 5800000,
        'forecast': 5930000,
        'variance': -130000,
    }
    
    return render_template('finance/dashboards/budget.html',
        title='Budget Dashboard',
        budget_metrics=budget_metrics,
        dept_labels=dept_labels,
        dept_budget=dept_budget,
        dept_actual=dept_actual,
        overruns=overruns,
        consumption_labels=consumption_labels,
        consumption_budget=consumption_budget,
        consumption_actual=consumption_actual,
        monthly_variance=monthly_variance,
        pending_approvals=pending_approvals,
        forecast_labels=forecast_labels,
        forecast_budget=forecast_budget,
        forecast_data=forecast_data,
        forecast_metrics=forecast_metrics
    )


# ============================================================================
# TAX DASHBOARD
# ============================================================================

@finance_bp.route('/dashboard/tax')
@require_permission('finance', 'tax', 'view')
def dashboard_tax():
    """Tax Dashboard."""
    
    tax_summary = {
        'vat_payable': 125000,
        'output_vat': 380000,
        'input_vat': 255000,
        'net_vat': 125000,
        'due_date': '2026-04-28',
        'period_name': 'Q2 2026',
    }
    
    tax_transactions = [
        {'date': '2026-04-15', 'document_number': 'INV-2026-0125', 'type': 'Output', 'base': 50000, 'vat': 5000},
        {'date': '2026-04-14', 'document_number': 'INV-2026-0124', 'type': 'Output', 'base': 35000, 'vat': 3500},
        {'date': '2026-04-14', 'document_number': 'BILL-2026-0089', 'type': 'Input', 'base': 28000, 'vat': 2800},
        {'date': '2026-04-13', 'document_number': 'INV-2026-0123', 'type': 'Output', 'base': 42000, 'vat': 4200},
        {'date': '2026-04-12', 'document_number': 'BILL-2026-0088', 'type': 'Input', 'base': 18000, 'vat': 1800},
    ]
    
    tax_code_labels = ['Standard 5%', 'Zero Rated', 'Exempt', 'ESR 5%', 'TCS 10%']
    tax_code_data = [450000, 180000, 95000, 65000, 35000]
    
    tax_timeline = [
        {'type': 'payment', 'title': 'VAT Payment Due', 'description': 'Q1 2026 VAT liability', 'amount': 125000, 'date': '2026-04-28'},
        {'type': 'filing', 'title': 'VAT Return Filing', 'description': 'Q1 2026 VAT return', 'amount': 125000, 'date': '2026-04-25'},
        {'type': 'payment', 'title': 'WHT Payment Due', 'description': 'Quarterly WHT', 'amount': 45000, 'date': '2026-05-15'},
    ]
    
    exemption = {
        'standard_rated': 450000,
        'zero_rated': 180000,
        'exempt': 95000,
    }
    exemption_data = [450000, 180000, 95000]
    
    return render_template('finance/dashboards/tax.html',
        title='Tax Dashboard',
        tax_summary=tax_summary,
        tax_transactions=tax_transactions,
        tax_code_labels=tax_code_labels,
        tax_code_data=tax_code_data,
        tax_timeline=tax_timeline,
        exemption=exemption,
        exemption_data=exemption_data
    )


# ============================================================================
# AUDIT/CONTROL DASHBOARD
# ============================================================================

@finance_bp.route('/dashboard/audit')
@require_permission('finance', 'reports', 'view')
def dashboard_audit():
    """Audit/Control Dashboard."""
    
    audit_stats = {
        'entries_today': 12,
        'entries_this_week': 89,
        'exceptions': 3,
        'pending_approvals': 7,
        'old_pending': 2,
        'reversal_rate': 1.2,
        'avg_daily_entries': 12.7,
        'highest_day': 28,
        'spike_days': 1,
    }
    
    activity_labels = [f'Day {i+1}' for i in range(30)]
    activity_data = [10, 12, 15, 8, 11, 14, 16, 13, 9, 12, 15, 18, 11, 14, 10, 8, 13, 16, 12, 9, 14, 17, 20, 15, 11, 8, 12, 15, 28, 14]
    activity_avg = [12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12]
    
    exceptions = [
        {'type': 'failed_post', 'description': 'Journal JE-2026-0145 failed validation', 'journal_number': 'JE-2026-0145', 'created_at': '2026-04-15 09:32', 'action_link': '/finance/journals/145'},
        {'type': 'unusual_amount', 'description': 'Unusually large invoice amount detected', 'document': 'INV-2026-0128', 'created_at': '2026-04-14 14:20', 'action_link': '/finance/ar/invoices/128'},
        {'type': 'off_hours', 'description': 'Journal posted outside business hours', 'journal_number': 'JE-2026-0142', 'created_at': '2026-04-13 23:45', 'action_link': '/finance/journals/142'},
    ]
    
    segregation_matrix = [
        {'name': 'Accountant', 'can_create': True, 'can_approve': False, 'can_post': True, 'can_reverse': False},
        {'name': 'Finance Manager', 'can_create': True, 'can_approve': True, 'can_post': True, 'can_reverse': True},
        {'name': 'CFO', 'can_create': True, 'can_approve': True, 'can_post': True, 'can_reverse': True},
        {'name': 'Auditor', 'can_create': False, 'can_approve': False, 'can_post': False, 'can_reverse': False},
    ]
    
    period_status = [
        {'period_name': 'April 2026', 'fiscal_year': 'FY 2026', 'status': 'Open'},
        {'period_name': 'March 2026', 'fiscal_year': 'FY 2026', 'status': 'Closed'},
        {'period_name': 'February 2026', 'fiscal_year': 'FY 2026', 'status': 'Closed'},
    ]
    
    audit_log = [
        {'action': 'POST', 'description': 'Journal JE-2026-0156 posted', 'user': 'Ahmed K.', 'timestamp': '2026-04-15 10:32'},
        {'action': 'CREATE', 'description': 'Invoice INV-2026-0129 created', 'user': 'Sara M.', 'timestamp': '2026-04-15 09:45'},
        {'action': 'APPROVE', 'description': 'Budget B-2026-003 approved', 'user': 'CFO', 'timestamp': '2026-04-15 08:30'},
        {'action': 'POST', 'description': 'Payment PMT-2026-0089 posted', 'user': 'Ahmed K.', 'timestamp': '2026-04-14 16:20'},
        {'action': 'REVERSE', 'description': 'Journal JE-2026-0140 reversed', 'user': 'Finance Mgr', 'timestamp': '2026-04-14 14:15'},
    ]
    
    suspense_activity = [
        {'account': 'Suspense - Rounding', 'description': 'Penny difference from rounding', 'amount': 0.05, 'date': '2026-04-14'},
    ]
    
    approval_backlog = [
        {'document': 'Budget B-2026-004', 'submitted_by': 'Marketing Dept', 'days_pending': 8},
        {'document': 'Journal JE-2026-0148', 'submitted_by': 'Operations', 'days_pending': 5},
        {'document': 'Invoice INV-2026-0127', 'submitted_by': 'Sales', 'days_pending': 3},
    ]
    
    return render_template('finance/dashboards/audit.html',
        title='Audit/Control Dashboard',
        audit_stats=audit_stats,
        activity_labels=activity_labels,
        activity_data=activity_data,
        activity_avg=activity_avg,
        exceptions=exceptions,
        segregation_matrix=segregation_matrix,
        period_status=period_status,
        audit_log=audit_log,
        suspense_activity=suspense_activity,
        approval_backlog=approval_backlog
    )


# ============================================================================
# CHART OF ACCOUNTS
# ============================================================================

@finance_bp.route('/accounts')
@require_permission('finance', 'accounts', 'view')
def accounts_list():
    """List all accounts."""
    company_id = get_company_id()
    
    # Get filter parameters
    category_id = request.args.get('category_id', type=int)
    active_only = request.args.get('active_only', '1') == '1'
    
    accounts = get_accounts(company_id=company_id, active_only=active_only, category_id=category_id)
    categories = get_account_categories()
    
    return render_template('finance/accounts/list.html',
        title='Chart of Accounts',
        accounts=accounts,
        categories=categories,
        filters={'category_id': category_id, 'active_only': active_only}
    )


@finance_bp.route('/accounts/create', methods=['GET', 'POST'])
@require_permission('finance', 'accounts', 'create')
def accounts_create():
    """Create new account."""
    if request.method == 'POST':
        data = {
            'code': request.form.get('code'),
            'name': request.form.get('name'),
            'name_ar': request.form.get('name_ar'),
            'description': request.form.get('description'),
            'category_id': request.form.get('category_id', type=int),
            'parent_id': request.form.get('parent_id', type=int) or None,
            'account_type': request.form.get('account_type'),
            'is_active': request.form.get('is_active', '1') == '1',
            'is_posting_allowed': request.form.get('is_posting_allowed', '1') == '1',
            'is_control_account': request.form.get('is_control_account') == '1',
            'is_cost_center_allowed': request.form.get('is_cost_center_allowed') == '1',
            'opening_balance': request.form.get('opening_balance', 0, type=float),
            'opening_balance_date': request.form.get('opening_balance_date'),
            'company_id': get_company_id(),
        }
        
        try:
            account_id = create_account(data)
            flash('Account created successfully!', 'success')
            return redirect(url_for('finance.accounts_view', account_id=account_id))
        except Exception as e:
            flash(f'Error creating account: {str(e)}', 'error')
    
    categories = get_account_categories()
    accounts = get_accounts(active_only=True)
    
    return render_template('finance/accounts/create.html',
        title='Create Account',
        categories=categories,
        accounts=accounts
    )


@finance_bp.route('/accounts/<int:account_id>')
@require_permission('finance', 'accounts', 'view')
def accounts_view(account_id):
    """View account details and ledger."""
    account = get_account_by_id(account_id)
    if not account:
        flash('Account not found', 'error')
        return redirect(url_for('finance.accounts_list'))
    
    # Get balance
    balance = get_account_balance(account_id)
    
    # Get ledger entries
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    ledger = get_account_ledger(account_id, start_date=start_date, end_date=end_date)
    
    return render_template('finance/accounts/view.html',
        title=f'Account: {account.get("code")} - {account.get("name")}',
        account=account,
        balance=balance,
        ledger=ledger
    )


@finance_bp.route('/accounts/<int:account_id>/edit', methods=['GET', 'POST'])
@require_permission('finance', 'accounts', 'edit')
def accounts_edit(account_id):
    """Edit account."""
    account = get_account_by_id(account_id)
    if not account:
        flash('Account not found', 'error')
        return redirect(url_for('finance.accounts_list'))
    
    if request.method == 'POST':
        data = {
            'code': request.form.get('code'),
            'name': request.form.get('name'),
            'name_ar': request.form.get('name_ar'),
            'description': request.form.get('description'),
            'category_id': request.form.get('category_id', type=int),
            'parent_id': request.form.get('parent_id', type=int) or None,
            'account_type': request.form.get('account_type'),
            'is_active': request.form.get('is_active', '1') == '1',
            'is_posting_allowed': request.form.get('is_posting_allowed', '1') == '1',
            'is_control_account': request.form.get('is_control_account') == '1',
            'is_cost_center_allowed': request.form.get('is_cost_center_allowed') == '1',
        }
        
        try:
            update_account(account_id, data)
            flash('Account updated successfully!', 'success')
            return redirect(url_for('finance.accounts_view', account_id=account_id))
        except Exception as e:
            flash(f'Error updating account: {str(e)}', 'error')
    
    categories = get_account_categories()
    accounts = get_accounts(active_only=True)
    
    return render_template('finance/accounts/edit.html',
        title=f'Edit Account: {account.get("code")}',
        account=account,
        categories=categories,
        accounts=accounts
    )


# ============================================================================
# JOURNAL ENTRIES
# ============================================================================

@finance_bp.route('/journals')
@require_permission('finance', 'journals', 'view')
def journals_list():
    """List journal entries."""
    company_id = get_company_id()
    
    # Get filters
    status = request.args.get('status')
    journal_type = request.args.get('journal_type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    journals = get_journals(
        company_id=company_id,
        status=status,
        journal_type=journal_type,
        start_date=start_date,
        end_date=end_date,
        limit=per_page,
        offset=(page - 1) * per_page
    )
    
    return render_template('finance/journals/list.html',
        title='Journal Entries',
        journals=journals,
        filters={'status': status, 'journal_type': journal_type, 'start_date': start_date, 'end_date': end_date},
        page=page
    )


@finance_bp.route('/journals/create', methods=['GET', 'POST'])
@require_permission('finance', 'journals', 'create')
def journals_create():
    """Create new journal entry."""
    company_id = get_company_id()
    
    if request.method == 'POST':
        # Parse form data
        lines = []
        line_count = request.form.get('line_count', 0, type=int)
        
        for i in range(line_count):
            account_id = request.form.get(f'account_id_{i}', type=int)
            debit = request.form.get(f'debit_{i}', 0, type=float)
            credit = request.form.get(f'credit_{i}', 0, type=float)
            
            if account_id and (debit or credit):
                lines.append({
                    'account_id': account_id,
                    'description': request.form.get(f'description_{i}'),
                    'debit': debit,
                    'credit': credit,
                    'cost_center_id': request.form.get(f'cost_center_id_{i}', type=int) or None,
                    'reference': request.form.get(f'reference_{i}'),
                })
        
        data = {
            'journal_type': request.form.get('journal_type', 'General'),
            'journal_date': request.form.get('journal_date'),
            'reference': request.form.get('reference'),
            'description': request.form.get('description'),
            'memo': request.form.get('memo'),
            'company_id': company_id,
            'created_by': user_id,
        }
        
        try:
            journal_id = create_journal(data, lines)
            flash('Journal entry created successfully!', 'success')
            
            # Auto-post if configured
            if request.form.get('auto_post') == '1':
                post_journal(journal_id, user_id)
                flash('Journal entry posted!', 'success')
            
            return redirect(url_for('finance.journals_view', journal_id=journal_id))
        except Exception as e:
            flash(f'Error creating journal: {str(e)}', 'error')
    
    accounts = get_accounts(company_id=company_id, active_only=True)
    cost_centers = get_cost_centers(company_id=company_id)
    
    return render_template('finance/journals/create.html',
        title='Create Journal Entry',
        accounts=accounts,
        cost_centers=cost_centers,
        default_date=request.args.get('date')
    )


@finance_bp.route('/journals/<int:journal_id>')
@require_permission('finance', 'journals', 'view')
def journals_view(journal_id):
    """View journal entry details."""
    journal = get_journal_by_id(journal_id)
    if not journal:
        flash('Journal entry not found', 'error')
        return redirect(url_for('finance.journals_list'))
    
    return render_template('finance/journals/view.html',
        title=f'Journal: {journal.get("journal_number")}',
        journal=journal
    )


@finance_bp.route('/journals/<int:journal_id>/post', methods=['POST'])
@require_permission('finance', 'journals', 'post')
def journals_post(journal_id):
    """Post a journal entry."""
    user_id = get_current_user_id()
    try:
        post_journal(journal_id, user_id)
        if request.is_json:
            return jsonify({'success': True, 'message': 'Journal posted successfully'})
        flash('Journal entry posted successfully!', 'success')
    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        flash(f'Error posting journal: {str(e)}', 'error')
    
    return redirect(url_for('finance.journals_view', journal_id=journal_id))


@finance_bp.route('/journals/<int:journal_id>/reverse', methods=['POST'])
@require_permission('finance', 'journals', 'reverse')
def journals_reverse(journal_id):
    """Reverse a journal entry."""
    user_id = get_current_user_id()
    reversal_date = request.form.get('reversal_date')
    reversal_memo = request.form.get('reversal_memo')
    
    try:
        reversal_id = reverse_journal(journal_id, user_id, reversal_date, reversal_memo)
        if request.is_json:
            return jsonify({'success': True, 'reversal_id': reversal_id, 'message': 'Journal reversed successfully'})
        flash('Journal entry reversed successfully!', 'success')
    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        flash(f'Error reversing journal: {str(e)}', 'error')
    
    return redirect(url_for('finance.journals_view', journal_id=journal_id))


# ============================================================================
# CUSTOMER INVOICES (AR)
# ============================================================================

@finance_bp.route('/ar/invoices')
@require_permission('finance', 'ar_invoices', 'view')
def ar_invoices_list():
    """List customer invoices."""
    company_id = get_company_id()
    
    status = request.args.get('status')
    customer_id = request.args.get('customer_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    invoices = get_customer_invoices(
        company_id=company_id,
        customer_id=customer_id,
        status=status,
        start_date=start_date,
        end_date=end_date
    )
    
    return render_template('finance/ar/invoices/list.html',
        title='Customer Invoices',
        invoices=invoices,
        filters={'status': status, 'customer_id': customer_id, 'start_date': start_date, 'end_date': end_date}
    )


@finance_bp.route('/ar/invoices/create', methods=['GET', 'POST'])
@require_permission('finance', 'ar_invoices', 'create')
def ar_invoices_create():
    """Create customer invoice."""
    company_id = get_company_id()
    
    if request.method == 'POST':
        # Parse line items
        lines = []
        line_count = request.form.get('line_count', 0, type=int)
        
        for i in range(line_count):
            lines.append({
                'product_id': request.form.get(f'product_id_{i}', type=int) or None,
                'description': request.form.get(f'description_{i}'),
                'quantity': request.form.get(f'quantity_{i}', 1, type=float),
                'unit_price': request.form.get(f'unit_price_{i}', 0, type=float),
                'discount_percent': request.form.get(f'discount_percent_{i}', 0, type=float),
                'tax_code_id': request.form.get(f'tax_code_id_{i}', type=int) or None,
                'tax_percent': request.form.get(f'tax_percent_{i}', 0, type=float),
                'tax_amount': request.form.get(f'tax_amount_{i}', 0, type=float),
                'line_total': request.form.get(f'line_total_{i}', 0, type=float),
                'cost_center_id': request.form.get(f'cost_center_id_{i}', type=int) or None,
            })
        
        data = {
            'customer_id': request.form.get('customer_id', type=int),
            'invoice_date': request.form.get('invoice_date'),
            'due_date': request.form.get('due_date'),
            'currency': request.form.get('currency', 'AED'),
            'tax_code_id': request.form.get('tax_code_id', type=int) or None,
            'payment_terms': request.form.get('payment_terms'),
            'notes': request.form.get('notes'),
            'company_id': company_id,
            'created_by': user_id,
        }
        
        try:
            invoice_id = create_customer_invoice(data, lines)
            flash('Invoice created successfully!', 'success')
            
            if request.form.get('auto_post') == '1':
                post_customer_invoice(invoice_id, user_id)
                flash('Invoice posted to ledger!', 'success')
            
            return redirect(url_for('finance.ar_invoices_view', invoice_id=invoice_id))
        except Exception as e:
            flash(f'Error creating invoice: {str(e)}', 'error')
    
    # Get customers, products, tax codes, etc.
    from database import get_all as db_get_all
    customers = db_get_all("SELECT id, code, name FROM customers ORDER BY name")
    products = db_get_all("SELECT id, part_number, name, cost_price FROM parts WHERE is_active = 1 ORDER BY name")
    tax_codes = get_tax_codes(company_id=company_id)
    cost_centers = get_cost_centers(company_id=company_id)
    accounts = get_accounts(company_id=company_id, active_only=True)
    
    return render_template('finance/ar/invoices/create.html',
        title='Create Invoice',
        customers=customers,
        products=products,
        tax_codes=tax_codes,
        cost_centers=cost_centers,
        accounts=accounts
    )


@finance_bp.route('/ar/invoices/<int:invoice_id>')
@require_permission('finance', 'ar_invoices', 'view')
def ar_invoices_view(invoice_id):
    """View invoice details."""
    invoice = get_customer_invoice_by_id(invoice_id)
    if not invoice:
        flash('Invoice not found', 'error')
        return redirect(url_for('finance.ar_invoices_list'))
    
    return render_template('finance/ar/invoices/view.html',
        title=f'Invoice: {invoice.get("invoice_number")}',
        invoice=invoice
    )


@finance_bp.route('/ar/invoices/<int:invoice_id>/post', methods=['POST'])
@require_permission('finance', 'ar_invoices', 'post')
def ar_invoices_post(invoice_id):
    """Post a customer invoice."""
    user_id = get_current_user_id()
    try:
        journal_id = post_customer_invoice(invoice_id, user_id)
        flash('Invoice posted to ledger!', 'success')
    except Exception as e:
        flash(f'Error posting invoice: {str(e)}', 'error')
    
    return redirect(url_for('finance.ar_invoices_view', invoice_id=invoice_id))


# ============================================================================
# CUSTOMER RECEIPTS
# ============================================================================

@finance_bp.route('/ar/receipts')
@require_permission('finance', 'ar_receipts', 'view')
def ar_receipts_list():
    """List customer receipts."""
    company_id = get_company_id()
    
    receipts = get_customer_receipts(company_id=company_id)
    
    return render_template('finance/ar/receipts/list.html',
        title='Customer Receipts',
        receipts=receipts
    )


@finance_bp.route('/ar/receipts/create', methods=['GET', 'POST'])
@require_permission('finance', 'ar_receipts', 'create')
def ar_receipts_create():
    """Create customer receipt."""
    company_id = get_company_id()
    
    if request.method == 'POST':
        allocations = []
        alloc_count = request.form.get('alloc_count', 0, type=int)
        
        for i in range(alloc_count):
            invoice_id = request.form.get(f'invoice_id_{i}', type=int)
            amount = request.form.get(f'amount_{i}', 0, type=float)
            if invoice_id and amount > 0:
                allocations.append({
                    'invoice_id': invoice_id,
                    'amount_allocated': amount,
                    'discount_used': request.form.get(f'discount_{i}', 0, type=float),
                })
        
        data = {
            'customer_id': request.form.get('customer_id', type=int),
            'receipt_date': request.form.get('receipt_date'),
            'amount_received': request.form.get('amount_received', 0, type=float),
            'discount_allowed': request.form.get('discount_allowed', 0, type=float),
            'payment_method': request.form.get('payment_method'),
            'reference_number': request.form.get('reference_number'),
            'notes': request.form.get('notes'),
            'company_id': company_id,
            'created_by': user_id,
        }
        
        try:
            receipt_id = create_customer_receipt(data, allocations)
            flash('Receipt created successfully!', 'success')
            
            if request.form.get('auto_post') == '1':
                post_customer_receipt(receipt_id, user_id)
                flash('Receipt posted to ledger!', 'success')
            
            return redirect(url_for('finance.ar_receipts_view', receipt_id=receipt_id))
        except Exception as e:
            flash(f'Error creating receipt: {str(e)}', 'error')
    
    customers = get_all("SELECT id, code, name FROM customers ORDER BY name")
    open_invoices = get_customer_invoices(company_id=company_id, status='Posted')
    
    return render_template('finance/ar/receipts/create.html',
        title='Create Receipt',
        customers=customers,
        open_invoices=open_invoices
    )


@finance_bp.route('/ar/receipts/<int:receipt_id>')
@require_permission('finance', 'ar_receipts', 'view')
def ar_receipts_view(receipt_id):
    """View receipt details."""
    receipt = get_customer_receipt_by_id(receipt_id)
    if not receipt:
        flash('Receipt not found', 'error')
        return redirect(url_for('finance.ar_receipts_list'))
    
    return render_template('finance/ar/receipts/view.html',
        title=f'Receipt: {receipt.get("receipt_number")}',
        receipt=receipt
    )


# ============================================================================
# SUPPLIER BILLS (AP)
# ============================================================================

@finance_bp.route('/ap/bills')
@require_permission('finance', 'ap_bills', 'view')
def ap_bills_list():
    """List supplier bills."""
    company_id = get_company_id()
    
    status = request.args.get('status')
    supplier_id = request.args.get('supplier_id', type=int)
    
    bills = get_supplier_bills(
        company_id=company_id,
        supplier_id=supplier_id,
        status=status
    )
    
    return render_template('finance/ap/bills/list.html',
        title='Supplier Bills',
        bills=bills,
        filters={'status': status, 'supplier_id': supplier_id}
    )


@finance_bp.route('/ap/bills/create', methods=['GET', 'POST'])
@require_permission('finance', 'ap_bills', 'create')
def ap_bills_create():
    """Create supplier bill."""
    company_id = get_company_id()
    
    if request.method == 'POST':
        lines = []
        line_count = request.form.get('line_count', 0, type=int)
        
        for i in range(line_count):
            lines.append({
                'product_id': request.form.get(f'product_id_{i}', type=int) or None,
                'description': request.form.get(f'description_{i}'),
                'quantity': request.form.get(f'quantity_{i}', 1, type=float),
                'unit_price': request.form.get(f'unit_price_{i}', 0, type=float),
                'discount_percent': request.form.get(f'discount_percent_{i}', 0, type=float),
                'tax_code_id': request.form.get(f'tax_code_id_{i}', type=int) or None,
                'tax_percent': request.form.get(f'tax_percent_{i}', 0, type=float),
                'tax_amount': request.form.get(f'tax_amount_{i}', 0, type=float),
                'line_total': request.form.get(f'line_total_{i}', 0, type=float),
                'cost_center_id': request.form.get(f'cost_center_id_{i}', type=int) or None,
            })
        
        data = {
            'supplier_id': request.form.get('supplier_id', type=int),
            'bill_date': request.form.get('bill_date'),
            'due_date': request.form.get('due_date'),
            'currency': request.form.get('currency', 'AED'),
            'tax_code_id': request.form.get('tax_code_id', type=int) or None,
            'payment_terms': request.form.get('payment_terms'),
            'notes': request.form.get('notes'),
            'company_id': company_id,
            'created_by': user_id,
        }
        
        try:
            bill_id = create_supplier_bill(data, lines)
            flash('Bill created successfully!', 'success')
            
            if request.form.get('auto_post') == '1':
                post_supplier_bill(bill_id, user_id)
                flash('Bill posted to ledger!', 'success')
            
            return redirect(url_for('finance.ap_bills_view', bill_id=bill_id))
        except Exception as e:
            flash(f'Error creating bill: {str(e)}', 'error')
    
    suppliers = get_all("SELECT id, code, name FROM suppliers ORDER BY name")
    products = get_all("SELECT id, part_number, name, cost_price FROM parts WHERE is_active = 1 ORDER BY name")
    tax_codes = get_tax_codes(company_id=company_id)
    cost_centers = get_cost_centers(company_id=company_id)
    
    return render_template('finance/ap/bills/create.html',
        title='Create Bill',
        suppliers=suppliers,
        products=products,
        tax_codes=tax_codes,
        cost_centers=cost_centers
    )


@finance_bp.route('/ap/bills/<int:bill_id>')
@require_permission('finance', 'ap_bills', 'view')
def ap_bills_view(bill_id):
    """View bill details."""
    bill = get_supplier_bill_by_id(bill_id)
    if not bill:
        flash('Bill not found', 'error')
        return redirect(url_for('finance.ap_bills_list'))
    
    return render_template('finance/ap/bills/view.html',
        title=f'Bill: {bill.get("bill_number")}',
        bill=bill
    )


@finance_bp.route('/ap/bills/<int:bill_id>/post', methods=['POST'])
@require_permission('finance', 'ap_bills', 'post')
def ap_bills_post(bill_id):
    """Post a supplier bill."""
    user_id = get_current_user_id()
    try:
        post_supplier_bill(bill_id, user_id)
        flash('Bill posted to ledger!', 'success')
    except Exception as e:
        flash(f'Error posting bill: {str(e)}', 'error')
    
    return redirect(url_for('finance.ap_bills_view', bill_id=bill_id))


# ============================================================================
# SUPPLIER PAYMENTS
# ============================================================================

@finance_bp.route('/ap/payments')
@require_permission('finance', 'ap_payments', 'view')
def ap_payments_list():
    """List supplier payments."""
    company_id = get_company_id()
    
    payments = get_supplier_payments(company_id=company_id)
    
    return render_template('finance/ap/payments/list.html',
        title='Supplier Payments',
        payments=payments
    )


@finance_bp.route('/ap/payments/create', methods=['GET', 'POST'])
@require_permission('finance', 'ap_payments', 'create')
def ap_payments_create():
    """Create supplier payment."""
    company_id = get_company_id()
    
    if request.method == 'POST':
        allocations = []
        alloc_count = request.form.get('alloc_count', 0, type=int)
        
        for i in range(alloc_count):
            bill_id = request.form.get(f'bill_id_{i}', type=int)
            amount = request.form.get(f'amount_{i}', 0, type=float)
            if bill_id and amount > 0:
                allocations.append({
                    'bill_id': bill_id,
                    'amount_allocated': amount,
                    'discount_used': request.form.get(f'discount_{i}', 0, type=float),
                })
        
        data = {
            'supplier_id': request.form.get('supplier_id', type=int),
            'payment_date': request.form.get('payment_date'),
            'amount_paid': request.form.get('amount_paid', 0, type=float),
            'discount_received': request.form.get('discount_received', 0, type=float),
            'payment_method': request.form.get('payment_method'),
            'reference_number': request.form.get('reference_number'),
            'notes': request.form.get('notes'),
            'company_id': company_id,
            'created_by': user_id,
        }
        
        try:
            payment_id = create_supplier_payment(data, allocations)
            flash('Payment created successfully!', 'success')
            
            if request.form.get('auto_post') == '1':
                post_supplier_payment(payment_id, user_id)
                flash('Payment posted to ledger!', 'success')
            
            return redirect(url_for('finance.ap_payments_view', payment_id=payment_id))
        except Exception as e:
            flash(f'Error creating payment: {str(e)}', 'error')
    
    suppliers = get_all("SELECT id, code, name FROM suppliers ORDER BY name")
    open_bills = get_supplier_bills(company_id=company_id, status='Posted')
    
    return render_template('finance/ap/payments/create.html',
        title='Create Payment',
        suppliers=suppliers,
        open_bills=open_bills
    )


@finance_bp.route('/ap/payments/<int:payment_id>')
@require_permission('finance', 'ap_payments', 'view')
def ap_payments_view(payment_id):
    """View payment details."""
    payment = get_supplier_payment_by_id(payment_id)
    if not payment:
        flash('Payment not found', 'error')
        return redirect(url_for('finance.ap_payments_list'))
    
    return render_template('finance/ap/payments/view.html',
        title=f'Payment: {payment.get("payment_number")}',
        payment=payment
    )


# ============================================================================
# ASSETS
# ============================================================================

@finance_bp.route('/assets')
@require_permission('finance', 'assets', 'view')
def assets_list():
    """List fixed assets."""
    company_id = get_company_id()
    
    status = request.args.get('status')
    category_id = request.args.get('category_id', type=int)
    
    assets = get_assets(company_id=company_id, status=status, category_id=category_id)
    categories = get_asset_categories()
    
    return render_template('finance/assets/list.html',
        title='Fixed Assets',
        assets=assets,
        categories=categories,
        filters={'status': status, 'category_id': category_id}
    )


@finance_bp.route('/assets/create', methods=['GET', 'POST'])
@require_permission('finance', 'assets', 'create')
def assets_create():
    """Create fixed asset."""
    company_id = get_company_id()
    
    if request.method == 'POST':
        data = {
            'asset_name': request.form.get('asset_name'),
            'asset_name_ar': request.form.get('asset_name_ar'),
            'category_id': request.form.get('category_id', type=int),
            'acquisition_date': request.form.get('acquisition_date'),
            'capitalization_date': request.form.get('capitalization_date'),
            'acquisition_cost': request.form.get('acquisition_cost', 0, type=float),
            'useful_life_years': request.form.get('useful_life_years', type=int),
            'depreciation_method': request.form.get('depreciation_method', 'StraightLine'),
            'salvage_value': request.form.get('salvage_value', 0, type=float),
            'status': request.form.get('status', 'Active'),
            'location': request.form.get('location'),
            'custodian': request.form.get('custodian'),
            'serial_number': request.form.get('serial_number'),
            'notes': request.form.get('notes'),
            'company_id': company_id,
            'branch_id': request.form.get('branch_id', type=int) or None,
            'cost_center_id': request.form.get('cost_center_id', type=int) or None,
            'created_by': user_id,
        }
        
        try:
            asset_id = create_asset(data)
            flash('Asset created successfully!', 'success')
            return redirect(url_for('finance.assets_view', asset_id=asset_id))
        except Exception as e:
            flash(f'Error creating asset: {str(e)}', 'error')
    
    categories = get_asset_categories()
    cost_centers = get_cost_centers(company_id=company_id)
    
    return render_template('finance/assets/create.html',
        title='Create Asset',
        categories=categories,
        cost_centers=cost_centers
    )


@finance_bp.route('/assets/<int:asset_id>')
@require_permission('finance', 'assets', 'view')
def assets_view(asset_id):
    """View asset details."""
    asset = get_asset_by_id(asset_id)
    if not asset:
        flash('Asset not found', 'error')
        return redirect(url_for('finance.assets_list'))
    
    return render_template('finance/assets/view.html',
        title=f'Asset: {asset.get("asset_code")}',
        asset=asset
    )


# ============================================================================
# DEPRECIATION
# ============================================================================

@finance_bp.route('/depreciation')
@require_permission('finance', 'depreciation', 'view')
def depreciation_list():
    """List depreciation runs."""
    company_id = get_company_id()
    
    runs = get_depreciation_runs(company_id=company_id)
    
    return render_template('finance/depreciation/list.html',
        title='Depreciation Runs',
        runs=runs
    )


@finance_bp.route('/depreciation/run', methods=['GET', 'POST'])
@require_permission('finance', 'depreciation', 'create')
def depreciation_run():
    """Run depreciation."""
    company_id = get_company_id()
    
    if request.method == 'POST':
        period_id = request.form.get('period_id', type=int)
        description = request.form.get('description')
        
        try:
            run_id = run_depreciation(period_id, company_id, user_id, description)
            flash(f'Depreciation run created successfully! Total: {request.form.get("total_display", "See details")}', 'success')
            
            if request.form.get('auto_post') == '1':
                post_depreciation_run(run_id, user_id)
                flash('Depreciation posted to ledger!', 'success')
            
            return redirect(url_for('finance.depreciation_view', run_id=run_id))
        except Exception as e:
            flash(f'Error running depreciation: {str(e)}', 'error')
    
    # Get open periods
    periods = get_fiscal_periods(company_id=company_id, status='Open')
    
    return render_template('finance/depreciation/run.html',
        title='Run Depreciation',
        periods=periods
    )


@finance_bp.route('/depreciation/<int:run_id>')
@require_permission('finance', 'depreciation', 'view')
def depreciation_view(run_id):
    """View depreciation run details."""
    run = get_one("SELECT * FROM finance_depreciation_runs WHERE id = ?", (run_id,))
    if not run:
        flash('Depreciation run not found', 'error')
        return redirect(url_for('finance.depreciation_list'))
    
    entries = get_all("SELECT * FROM finance_depreciation_entries WHERE run_id = ? ORDER BY line_number", (run_id,))
    
    return render_template('finance/depreciation/view.html',
        title=f'Depreciation: {run.get("run_number")}',
        run=run,
        entries=entries
    )


# ============================================================================
# COST CENTERS
# ============================================================================

@finance_bp.route('/cost-centers')
@require_permission('finance', 'cost_centers', 'view')
def cost_centers_list():
    """List cost centers."""
    company_id = get_company_id()
    
    cost_centers = get_cost_centers(company_id=company_id)
    
    return render_template('finance/cost-centers/list.html',
        title='Cost Centers',
        cost_centers=cost_centers
    )


@finance_bp.route('/cost-centers/create', methods=['GET', 'POST'])
@require_permission('finance', 'cost_centers', 'create')
def cost_centers_create():
    """Create cost center."""
    company_id = get_company_id()
    
    if request.method == 'POST':
        data = {
            'code': request.form.get('code'),
            'name': request.form.get('name'),
            'name_ar': request.form.get('name_ar'),
            'description': request.form.get('description'),
            'parent_id': request.form.get('parent_id', type=int) or None,
            'manager_name': request.form.get('manager_name'),
            'department': request.form.get('department'),
            'is_active': request.form.get('is_active', '1') == '1',
            'company_id': company_id,
        }
        
        try:
            cc_id = create_cost_center(data)
            flash('Cost center created successfully!', 'success')
            return redirect(url_for('finance.cost_centers_list'))
        except Exception as e:
            flash(f'Error creating cost center: {str(e)}', 'error')
    
    cost_centers = get_cost_centers(company_id=company_id)
    
    return render_template('finance/cost-centers/create.html',
        title='Create Cost Center',
        cost_centers=cost_centers
    )


# ============================================================================
# BUDGETS
# ============================================================================

@finance_bp.route('/budgets')
@require_permission('finance', 'budgets', 'view')
def budgets_list():
    """List budgets."""
    company_id = get_company_id()
    
    fiscal_year_id = request.args.get('fiscal_year_id', type=int)
    status = request.args.get('status')
    
    budgets = get_budgets(company_id=company_id, fiscal_year_id=fiscal_year_id, status=status)
    fiscal_years = get_fiscal_years(company_id=company_id)
    
    return render_template('finance/budgets/list.html',
        title='Budgets',
        budgets=budgets,
        fiscal_years=fiscal_years,
        filters={'fiscal_year_id': fiscal_year_id, 'status': status}
    )


@finance_bp.route('/budgets/create', methods=['GET', 'POST'])
@require_permission('finance', 'budgets', 'create')
def budgets_create():
    """Create budget."""
    company_id = get_company_id()
    
    if request.method == 'POST':
        lines = []
        line_count = request.form.get('line_count', 0, type=int)
        
        for i in range(line_count):
            lines.append({
                'account_id': request.form.get(f'account_id_{i}', type=int),
                'cost_center_id': request.form.get(f'cost_center_id_{i}', type=int) or None,
                'january': request.form.get(f'jan_{i}', 0, type=float),
                'february': request.form.get(f'feb_{i}', 0, type=float),
                'march': request.form.get(f'mar_{i}', 0, type=float),
                'april': request.form.get(f'apr_{i}', 0, type=float),
                'may': request.form.get(f'may_{i}', 0, type=float),
                'june': request.form.get(f'jun_{i}', 0, type=float),
                'july': request.form.get(f'jul_{i}', 0, type=float),
                'august': request.form.get(f'aug_{i}', 0, type=float),
                'september': request.form.get(f'sep_{i}', 0, type=float),
                'october': request.form.get(f'oct_{i}', 0, type=float),
                'november': request.form.get(f'nov_{i}', 0, type=float),
                'december': request.form.get(f'dec_{i}', 0, type=float),
            })
        
        data = {
            'budget_name': request.form.get('budget_name'),
            'fiscal_year_id': request.form.get('fiscal_year_id', type=int),
            'version': request.form.get('version', 1, type=int),
            'cost_center_id': request.form.get('cost_center_id', type=int) or None,
            'notes': request.form.get('notes'),
            'prepared_by': user_id,
            'company_id': company_id,
        }
        
        try:
            budget_id = create_budget(data, lines)
            flash('Budget created successfully!', 'success')
            return redirect(url_for('finance.budgets_view', budget_id=budget_id))
        except Exception as e:
            flash(f'Error creating budget: {str(e)}', 'error')
    
    fiscal_years = get_fiscal_years(company_id=company_id)
    accounts = get_accounts(company_id=company_id, active_only=True)
    cost_centers = get_cost_centers(company_id=company_id)
    
    return render_template('finance/budgets/create.html',
        title='Create Budget',
        fiscal_years=fiscal_years,
        accounts=accounts,
        cost_centers=cost_centers
    )


@finance_bp.route('/budgets/<int:budget_id>')
@require_permission('finance', 'budgets', 'view')
def budgets_view(budget_id):
    """View budget details."""
    budget = get_budget_vs_actual(budget_id)
    if not budget:
        flash('Budget not found', 'error')
        return redirect(url_for('finance.budgets_list'))
    
    return render_template('finance/budgets/view.html',
        title=f'Budget: {budget.get("budget_number")}',
        budget=budget
    )


# ============================================================================
# FISCAL YEARS & PERIODS
# ============================================================================

@finance_bp.route('/fiscal-years')
@require_permission('finance', 'fiscal_years', 'view')
def fiscal_years_list():
    """List fiscal years."""
    company_id = get_company_id()
    
    fiscal_years = get_fiscal_years(company_id=company_id)
    
    return render_template('finance/fiscal-years/list.html',
        title='Fiscal Years',
        fiscal_years=fiscal_years
    )


@finance_bp.route('/fiscal-years/create', methods=['GET', 'POST'])
@require_permission('finance', 'fiscal_years', 'create')
def fiscal_years_create():
    """Create fiscal year."""
    company_id = get_company_id()
    
    if request.method == 'POST':
        data = {
            'name': request.form.get('name'),
            'start_date': request.form.get('start_date'),
            'end_date': request.form.get('end_date'),
            'company_id': company_id,
        }
        
        try:
            year_id = create_fiscal_year(data)
            flash('Fiscal year created successfully!', 'success')
            return redirect(url_for('finance.fiscal_years_list'))
        except Exception as e:
            flash(f'Error creating fiscal year: {str(e)}', 'error')
    
    return render_template('finance/fiscal-years/create.html',
        title='Create Fiscal Year'
    )


@finance_bp.route('/fiscal-years/<int:year_id>/periods')
@require_permission('finance', 'fiscal_years', 'view')
def fiscal_year_periods(year_id):
    """View fiscal year periods."""
    year = get_fiscal_year_by_id(year_id)
    if not year:
        flash('Fiscal year not found', 'error')
        return redirect(url_for('finance.fiscal_years_list'))
    
    periods = get_fiscal_periods(year_id=year_id)
    
    return render_template('finance/fiscal-years/periods.html',
        title=f'Periods: {year.get("name")}',
        fiscal_year=year,
        periods=periods
    )


# ============================================================================
# TAX MANAGEMENT
# ============================================================================

@finance_bp.route('/tax/codes')
@require_permission('finance', 'tax', 'view')
def tax_codes_list():
    """List tax codes."""
    company_id = get_company_id()
    
    tax_codes = get_tax_codes(company_id=company_id)
    
    return render_template('finance/tax/codes.html',
        title='Tax Codes',
        tax_codes=tax_codes
    )


# ============================================================================
# REPORTS
# ============================================================================

@finance_bp.route('/reports/trial-balance')
@require_permission('finance', 'reports', 'view')
def reports_trial_balance():
    """Trial Balance Report."""
    company_id = get_company_id()
    
    period_id = request.args.get('period_id', type=int)
    as_of_date = request.args.get('as_of_date')
    
    trial_balance = get_trial_balance(company_id=company_id, period_id=period_id, as_of_date=as_of_date)
    
    # Calculate totals
    total_debit = sum(a.get('debit', 0) for a in trial_balance)
    total_credit = sum(a.get('credit', 0) for a in trial_balance)
    
    return render_template('finance/reports/trial_balance.html',
        title='Trial Balance',
        trial_balance=trial_balance,
        total_debit=total_debit,
        total_credit=total_credit,
        filters={'period_id': period_id, 'as_of_date': as_of_date}
    )


@finance_bp.route('/reports/ar-aging')
@require_permission('finance', 'reports', 'view')
def reports_ar_aging():
    """AR Aging Report."""
    company_id = get_company_id()
    
    customer_id = request.args.get('customer_id', type=int)
    as_of_date = request.args.get('as_of_date')
    
    aging = get_ar_aging(customer_id=customer_id, company_id=company_id, as_of_date=as_of_date)
    
    return render_template('finance/reports/ar_aging.html',
        title='AR Aging',
        aging=aging,
        filters={'customer_id': customer_id, 'as_of_date': as_of_date}
    )


@finance_bp.route('/reports/ap-aging')
@require_permission('finance', 'reports', 'view')
def reports_ap_aging():
    """AP Aging Report."""
    company_id = get_company_id()
    
    supplier_id = request.args.get('supplier_id', type=int)
    as_of_date = request.args.get('as_of_date')
    
    aging = get_ap_aging(supplier_id=supplier_id, company_id=company_id, as_of_date=as_of_date)
    
    return render_template('finance/reports/ap_aging.html',
        title='AP Aging',
        aging=aging,
        filters={'supplier_id': supplier_id, 'as_of_date': as_of_date}
    )


@finance_bp.route('/reports/general-ledger')
@require_permission('finance', 'reports', 'view')
def reports_general_ledger():
    """General Ledger Report."""
    company_id = get_company_id()
    
    account_id = request.args.get('account_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if account_id:
        ledger = get_account_ledger(account_id, start_date=start_date, end_date=end_date)
        account = get_account_by_id(account_id)
    else:
        ledger = []
        account = None
    
    accounts = get_accounts(company_id=company_id, active_only=True)
    
    return render_template('finance/reports/general_ledger.html',
        title='General Ledger',
        ledger=ledger,
        account=account,
        accounts=accounts,
        filters={'account_id': account_id, 'start_date': start_date, 'end_date': end_date}
    )


# ============================================================================
# API ENDPOINTS (JSON)
# ============================================================================

@finance_bp.route('/api/summary')
@require_permission('finance', 'dashboard', 'view')
def api_summary():
    """Get financial summary for dashboard widgets."""
    company_id = get_company_id()
    
    summary = get_financial_summary(company_id=company_id)
    
    return jsonify(summary)


@finance_bp.route('/api/ar/aging')
@require_permission('finance', 'ar', 'view')
def api_ar_aging():
    """Get AR aging data."""
    company_id = get_company_id()
    
    aging = get_ar_aging(company_id=company_id)
    
    return jsonify(aging)


@finance_bp.route('/api/ap/aging')
@require_permission('finance', 'ap', 'view')
def api_ap_aging():
    """Get AP aging data."""
    company_id = get_company_id()
    
    aging = get_ap_aging(company_id=company_id)
    
    return jsonify(aging)


@finance_bp.route('/api/account/<int:account_id>/balance')
@require_permission('finance', 'accounts', 'view')
def api_account_balance(account_id):
    """Get account balance."""
    period_id = request.args.get('period_id', type=int)
    as_of_date = request.args.get('as_of_date')
    
    balance = get_account_balance(account_id, period_id=period_id, as_of_date=as_of_date)
    
    return jsonify(balance)


@finance_bp.route('/api/tax/calculate', methods=['POST'])
@require_permission('finance', 'tax', 'view')
def api_calculate_tax():
    """Calculate tax on an amount."""
    data = request.get_json()
    
    tax_code_id = data.get('tax_code_id')
    amount = data.get('amount', 0)
    is_inclusive = data.get('is_inclusive', True)
    
    result = calculate_tax(tax_code_id, amount, is_inclusive)
    
    return jsonify(result)


# =============================================================================
# CO-PA / PROFITABILITY ANALYSIS ROUTES
# =============================================================================

@finance_bp.route('/profit-centers')
@require_permission('finance', 'cost_centers', 'view')
def profit_centers():
    """List and manage profit centers."""
    company_id = session.get('company_id')
    profit_centers = get_profit_centers(company_id=company_id)

    return render_template('finance/profit_centers.html',
                           profit_centers=profit_centers,
                           active_page='profit-centers')


@finance_bp.route('/profit-centers/create', methods=['GET', 'POST'])
@require_permission('finance', 'cost_centers', 'create')
def profit_center_create():
    """Create a new profit center."""
    company_id = session.get('company_id')

    if request.method == 'POST':
        data = {
            'code': request.form.get('code'),
            'name': request.form.get('name'),
            'name_ar': request.form.get('name_ar'),
            'description': request.form.get('description'),
            'parent_id': request.form.get('parent_id') or None,
            'manager_name': request.form.get('manager_name'),
            'profit_center_type': request.form.get('profit_center_type', 'operational'),
            'is_legal_entity': 1 if request.form.get('is_legal_entity') else 0,
            'company_id': company_id,
        }

        try:
            pc_id = create_profit_center(data)
            flash(f'Profit Center created successfully', 'success')
            return redirect(url_for('finance.profit_centers'))
        except Exception as e:
            flash(f'Error creating profit center: {e}', 'error')

    parent_centers = get_profit_centers(company_id=company_id, active_only=True)
    return render_template('finance/profit_center_create.html',
                           parent_centers=parent_centers,
                           active_page='profit-centers')


@finance_bp.route('/profit-centers/<int:pc_id>')
@require_permission('finance', 'cost_centers', 'view')
def profit_center_detail(pc_id):
    """View profit center detail with P&L."""
    company_id = session.get('company_id')
    pc = get_profit_center_by_id(pc_id)
    if not pc:
        flash('Profit center not found', 'error')
        return redirect(url_for('finance.profit_centers'))

    fiscal_year_id = request.args.get('fiscal_year_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    pnl = get_profit_center_pnl(pc_id, fiscal_year_id=fiscal_year_id, start_date=start_date, end_date=end_date)

    return render_template('finance/profit_center_detail.html',
                           profit_center=pc,
                           pnl=pnl,
                           active_page='profit-centers')


@finance_bp.route('/copa-segments')
@require_permission('finance', 'cost_centers', 'view')
def copa_segments():
    """List CO-PA segment definitions."""
    company_id = session.get('company_id')
    segments = get_copa_segments(company_id=company_id)

    return render_template('finance/copa_segments.html',
                           segments=segments,
                           active_page='copa-segments')


@finance_bp.route('/copa-segments/create', methods=['GET', 'POST'])
@require_permission('finance', 'cost_centers', 'create')
def copa_segment_create():
    """Create a new CO-PA segment."""
    company_id = session.get('company_id')

    if request.method == 'POST':
        values = []
        value_names = request.form.getlist('value_name')
        value_codes = request.form.getlist('value_code')
        for vn, vc in zip(value_names, value_codes):
            if vn and vc:
                values.append({'value_name': vn, 'value_code': vc})

        data = {
            'segment_name': request.form.get('segment_name'),
            'segment_code': request.form.get('segment_code'),
            'dimension_type': request.form.get('dimension_type'),
            'description': request.form.get('description'),
            'company_id': company_id,
        }

        try:
            seg_id = create_copa_segment(data, values)
            flash('CO-PA Segment created successfully', 'success')
            return redirect(url_for('finance.copa_segments'))
        except Exception as e:
            flash(f'Error creating segment: {e}', 'error')

    return render_template('finance/copa_segment_create.html',
                           active_page='copa-segments')


@finance_bp.route('/cost-allocations')
@require_permission('finance', 'cost_centers', 'view')
def cost_allocations():
    """List cost allocation rules."""
    company_id = session.get('company_id')
    rules = get_allocation_rules(company_id=company_id)

    return render_template('finance/cost_allocations.html',
                           rules=rules,
                           active_page='cost-allocations')


@finance_bp.route('/cost-allocations/create', methods=['GET', 'POST'])
@require_permission('finance', 'cost_centers', 'create')
def cost_allocation_create():
    """Create a new cost allocation rule."""
    company_id = session.get('company_id')

    if request.method == 'POST':
        data = {
            'rule_name': request.form.get('rule_name'),
            'rule_code': request.form.get('rule_code'),
            'source_cost_center_id': request.form.get('source_cost_center_id') or None,
            'target_cost_center_id': request.form.get('target_cost_center_id') or None,
            'target_profit_center_id': request.form.get('target_profit_center_id') or None,
            'allocation_basis': request.form.get('allocation_basis', 'fixed'),
            'basis_value': request.form.get('basis_value', 0),
            'basis_formula': request.form.get('basis_formula'),
            'percentage': request.form.get('percentage', 100),
            'amount': request.form.get('amount', 0),
            'effective_from': request.form.get('effective_from') or None,
            'effective_to': request.form.get('effective_to') or None,
            'description': request.form.get('description'),
            'company_id': company_id,
        }

        try:
            rule_id = create_allocation_rule(data)
            flash('Cost Allocation Rule created successfully', 'success')
            return redirect(url_for('finance.cost_allocations'))
        except Exception as e:
            flash(f'Error creating rule: {e}', 'error')

    cost_centers = get_cost_centers(company_id=company_id, active_only=True)
    profit_centers = get_profit_centers(company_id=company_id, active_only=True)
    return render_template('finance/cost_allocation_create.html',
                           cost_centers=cost_centers,
                           profit_centers=profit_centers,
                           active_page='cost-allocations')


@finance_bp.route('/cost-allocations/execute', methods=['GET', 'POST'])
@require_permission('finance', 'cost_centers', 'create')
def cost_allocation_execute():
    """Execute cost allocation for a period."""
    company_id = session.get('company_id')
    user_id = session.get('user_id')

    if request.method == 'POST':
        period_id = request.form.get('period_id', type=int)
        fiscal_year_id = request.form.get('fiscal_year_id', type=int)

        try:
            result = execute_cost_allocation(
                period_id=period_id,
                fiscal_year_id=fiscal_year_id,
                company_id=company_id,
                executed_by=user_id
            )
            if result['status'] == 'completed':
                flash(f'Cost allocation completed. {result["rules_processed"]} rules executed. Total allocated: {result["total_allocated"]}', 'success')
            else:
                flash(f'Allocation completed with status: {result["status"]}', 'info')
        except Exception as e:
            flash(f'Error executing allocation: {e}', 'error')

    return redirect(url_for('finance.cost_allocations'))


@finance_bp.route('/reports/profitability')
@require_permission('finance', 'reports', 'view')
def profitability_report():
    """CO-PA profitability analysis report."""
    company_id = session.get('company_id')

    fiscal_year_id = request.args.get('fiscal_year_id', type=int)
    period_id = request.args.get('period_id', type=int)
    dimension_type = request.args.get('dimension_type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    report_data = get_copa_profitability_report(
        company_id=company_id,
        fiscal_year_id=fiscal_year_id,
        period_id=period_id,
        dimension_type=dimension_type,
        start_date=start_date,
        end_date=end_date
    )

    fiscal_years = get_fiscal_years(company_id=company_id)
    segments = get_copa_segments(company_id=company_id)

    return render_template('finance/profitability_report.html',
                           report_data=report_data,
                           fiscal_years=fiscal_years,
                           segments=segments,
                           filters={
                               'fiscal_year_id': fiscal_year_id,
                               'period_id': period_id,
                               'dimension_type': dimension_type,
                               'start_date': start_date,
                               'end_date': end_date
                           },
                           active_page='profitability-report')


# Register the blueprint with the Flask app
def register_finance_routes(app):
    """Register finance routes with the Flask app."""
    app.register_blueprint(finance_bp)
