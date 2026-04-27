"""
Personal Finance / Money Management Routes
=========================================
Flask routes for the Personal Finance module.
Handles all personal finance operations including:
- Dashboard & Overview
- Accounts & Wallets
- Income Management
- Expense Management
- Transactions
- Budgeting
- Savings & Goals
- Investments
- Debts & Loans
- Assets
- Subscriptions
- Calendar & Reminders
- Alerts
- Categories
- Reports
- Import/Export
- Settings
"""

import json
import sqlite3
from datetime import datetime, timedelta
from flask import Blueprint, request, session, redirect, url_for, flash, render_template, jsonify, send_file
from functools import wraps
from database import get_db, get_db_context, get_one, get_all, log_audit, create_notification
from permissions import user_has_permission, require_permission
from finance_models import (
    initialize_finance_tables, initialize_finance_defaults,
    PFAccount, PFIncomeRecord, PFExpenseRecord, PFTransaction,
    PFBudget, PFFinancialGoal, PFInvestment, PFDebt, PFAsset,
    PFSubscription, PFCategory, PFAlert,
    generate_account_code, generate_income_number, generate_expense_number,
    generate_transaction_code, generate_budget_code, generate_goal_code,
    generate_investment_code, generate_debt_code, generate_asset_code,
    generate_subscription_number, generate_alert_code,
    get_account_balance, calculate_financial_health_score,
    get_budget_status, get_savings_progress,
    row_to_dict, rows_to_list
)
from export_utils import send_export_response, get_export_columns

# Create blueprint
finance_bp = Blueprint('finance', __name__, url_prefix='/finance')

# =============================================================================
# DECORATORS
# =============================================================================

def require_finance_permission(resource: str, action: str = 'view'):
    """Decorator to require finance permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please login to access this page.", "error")
                return redirect(url_for('login'))
            
            user_id = session['user_id']
            if not user_has_permission(user_id, 'finance', resource, action):
                flash(f"Access Denied. You don't have permission to {action} {resource}.", "error")
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_user_id():
    """Get current user ID from session."""
    return session.get('user_id', 1)


def get_current_user_name():
    """Get current user name."""
    user_id = session.get('user_id', 0)
    if user_id:
        user = get_one("SELECT username FROM users WHERE id = ?", (user_id,))
        if user:
            return user['username']
    return "System"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def init_finance():
    """Initialize finance module."""
    initialize_finance_tables()
    initialize_finance_defaults()


def get_finance_setting(key: str, default: str = "") -> str:
    """Get finance setting value."""
    setting = get_one(
        "SELECT setting_value FROM pf_settings WHERE setting_key = ? AND is_active = 1",
        (key,)
    )
    return setting['setting_value'] if setting else default


def log_finance_audit(action: str, entity_type: str, entity_id: int,
                      entity_reference: str = "", before_state: str = "",
                      after_state: str = "", notes: str = ""):
    """Log finance audit entry."""
    user_id = get_current_user_id()
    user_name = get_current_user_name()
    
    with get_db_context() as db:
        db.execute("""
            INSERT INTO pf_audit_records 
            (audit_code, entity_type, entity_id, action, field_name, old_value, new_value,
             user_id, user_name, ip_address, user_agent, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, (f"AUDIT-{datetime.now().strftime('%Y%m%d%H%M%S')}", entity_type, entity_id,
              action, '', before_state, after_state, user_id, user_name,
              request.remote_addr if request else '',
              request.headers.get('User-Agent', '') if request else '',
              notes))
        db.commit()


def get_categories(category_type: str = None, active_only: bool = True):
    """Get categories by type."""
    query = "SELECT * FROM pf_category_definitions WHERE 1=1"
    params = []
    if category_type:
        query += " AND category_type = ?"
        params.append(category_type)
    if active_only:
        query += " AND is_active = 1"
    query += " ORDER BY sort_order, category_name"
    return get_all(query, tuple(params))


def get_accounts(active_only: bool = True, user_id: int = None):
    """Get accounts."""
    if user_id is None:
        user_id = get_current_user_id()
    query = "SELECT * FROM pf_accounts WHERE owner_user_id = ?"
    params = [user_id]
    if active_only:
        query += " AND is_active = 1 AND is_archived = 0"
    query += " ORDER BY account_name"
    return get_all(query, tuple(params))


def format_currency(amount: float, currency: str = 'USD') -> str:
    """Format amount as currency string."""
    return f"{currency} {amount:,.2f}"


def calculate_kpis(user_id: int = None) -> dict:
    """Calculate financial KPIs for dashboard."""
    if user_id is None:
        user_id = get_current_user_id()
    
    today = datetime.now()
    month_start = today.replace(day=1).strftime('%Y-%m-%d')
    today_str = today.strftime('%Y-%m-%d')
    year_start = today.replace(month=1, day=1).strftime('%Y-%m-%d')
    
    # Monthly income
    income = get_one("""
        SELECT COALESCE(SUM(amount), 0) as total FROM pf_income_records
        WHERE owner_user_id = ? AND income_date >= ? AND is_active = 1 AND status = 'received'
    """, (user_id, month_start))
    monthly_income = income['total'] if income else 0
    
    # Monthly expenses
    expenses = get_one("""
        SELECT COALESCE(SUM(amount), 0) as total FROM pf_expense_records
        WHERE owner_user_id = ? AND expense_date >= ? AND is_active = 1 AND status = 'approved'
    """, (user_id, month_start))
    monthly_expenses = expenses['total'] if expenses else 0
    
    # Total savings
    savings = get_one("""
        SELECT COALESCE(SUM(current_amount), 0) as total FROM pf_savings_buckets
        WHERE owner_user_id = ? AND is_active = 1
    """, (user_id,))
    total_savings = savings['total'] if savings else 0
    
    # Total debts
    debts = get_one("""
        SELECT COALESCE(SUM(remaining_balance), 0) as total FROM pf_debts
        WHERE owner_user_id = ? AND is_active = 1 AND status = 'active'
    """, (user_id,))
    total_debts = debts['total'] if debts else 0
    
    # Total investments
    investments = get_one("""
        SELECT COALESCE(SUM(current_value), 0) as total FROM pf_investments
        WHERE owner_user_id = ? AND is_active = 1 AND status = 'held'
    """, (user_id,))
    total_investments = investments['total'] if investments else 0
    
    # Total assets
    assets = get_one("""
        SELECT COALESCE(SUM(current_value), 0) as total FROM pf_assets
        WHERE owner_user_id = ? AND is_active = 1 AND status = 'owned'
    """, (user_id,))
    total_assets = assets['total'] if assets else 0
    
    # Net worth
    net_worth = total_assets + total_savings + total_investments - total_debts
    
    # Savings rate
    savings_rate = (monthly_income - monthly_expenses) / monthly_income * 100 if monthly_income > 0 else 0
    
    # Budget status
    budgets = get_all("""
        SELECT * FROM pf_budgets 
        WHERE owner_user_id = ? AND is_active = 1 AND status = 'active'
        AND period_start_date <= ? AND period_end_date >= ?
    """, (user_id, today_str, today_str))
    
    total_budget = 0
    total_budget_spent = 0
    for budget in budgets:
        total_budget += budget['total_budget']
        spent = get_one("""
            SELECT COALESCE(SUM(er.amount), 0) as spent
            FROM pf_expense_records er
            INNER JOIN pf_budget_lines bl ON bl.category_id = er.category_id
            WHERE bl.budget_id = ? AND er.expense_date >= ? AND er.expense_date <= ?
            AND er.is_active = 1 AND er.status = 'approved'
        """, (budget['id'], budget['period_start_date'], budget['period_end_date']))
        total_budget_spent += spent['spent'] if spent else 0
    
    budget_used = (total_budget_spent / total_budget * 100) if total_budget > 0 else 0
    
    return {
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'net_cash_flow': monthly_income - monthly_expenses,
        'total_savings': total_savings,
        'savings_rate': savings_rate,
        'total_debts': total_debts,
        'total_assets': total_assets,
        'total_investments': total_investments,
        'net_worth': net_worth,
        'total_budget': total_budget,
        'budget_used': budget_used,
        'budget_remaining': total_budget - total_budget_spent
    }


# =============================================================================
# DASHBOARD / OVERVIEW ROUTES
# =============================================================================

@finance_bp.route('/')
@require_finance_permission('dashboard', 'view')
def dashboard():
    """Finance Dashboard - Main overview page."""
    user_id = get_current_user_id()
    user_name = get_current_user_name()
    
    # Get KPIs
    kpis = calculate_kpis(user_id)
    
    # Get health score
    health = calculate_financial_health_score(user_id)
    
    # Get recent transactions
    recent_transactions = get_all("""
        SELECT t.*, c.category_name, c.icon as category_icon, c.color as category_color,
               a.account_name
        FROM pf_transactions t
        LEFT JOIN pf_category_definitions c ON t.category_id = c.id
        LEFT JOIN pf_accounts a ON t.account_id = a.id
        WHERE t.owner_user_id = ? AND t.is_active = 1
        ORDER BY t.transaction_date DESC, t.created_at DESC
        LIMIT 10
    """, (user_id,))
    
    # Get budget statuses
    budgets = get_all("""
        SELECT * FROM pf_budgets 
        WHERE owner_user_id = ? AND is_active = 1 AND status = 'active'
        ORDER BY created_at DESC
    """, (user_id,))
    
    budget_statuses = []
    for budget in budgets:
        status = get_budget_status(budget['id'])
        status['budget_name'] = budget['budget_name']
        budget_statuses.append(status)
    
    # Get upcoming due payments
    today = datetime.now().strftime('%Y-%m-%d')
    next_30_days = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    upcoming_subs = get_all("""
        SELECT * FROM pf_subscriptions
        WHERE owner_user_id = ? AND is_active = 1 AND status = 'active'
        AND renewal_date >= ? AND renewal_date <= ?
        ORDER BY renewal_date
    """, (user_id, today, next_30_days))
    
    upcoming_debts = get_all("""
        SELECT * FROM pf_debts
        WHERE owner_user_id = ? AND is_active = 1 AND status = 'active'
        AND next_due_date >= ? AND next_due_date <= ?
        ORDER BY next_due_date
    """, (user_id, today, next_30_days))
    
    # Get alerts
    alerts = get_all("""
        SELECT * FROM pf_alerts
        WHERE owner_user_id = ? AND is_active = 1 AND is_dismissed = 0
        ORDER BY created_at DESC
        LIMIT 5
    """, (user_id,))
    
    # Get savings goals progress
    goals = get_all("""
        SELECT * FROM pf_financial_goals
        WHERE owner_user_id = ? AND is_active = 1 AND status IN ('active', 'on_track', 'at_risk')
        ORDER BY priority, target_date
    """, (user_id,))
    
    goal_progress = []
    for goal in goals:
        progress = get_savings_progress(goal['id'])
        goal_progress.append(progress)
    
    # Category spending for the month
    category_spending = get_all("""
        SELECT c.category_name, c.color, c.icon, SUM(e.amount) as total
        FROM pf_expense_records e
        INNER JOIN pf_category_definitions c ON e.category_id = c.id
        WHERE e.owner_user_id = ? AND e.expense_date >= ?
        AND e.is_active = 1 AND e.status = 'approved'
        GROUP BY c.id
        ORDER BY total DESC
        LIMIT 10
    """, (user_id, datetime.now().replace(day=1).strftime('%Y-%m-%d')))
    
    return render_template('finance/dashboard.html',
                          kpis=kpis, health=health,
                          recent_transactions=recent_transactions,
                          budget_statuses=budget_statuses,
                          upcoming_subs=upcoming_subs,
                          upcoming_debts=upcoming_debts,
                          alerts=alerts,
                          goal_progress=goal_progress,
                          category_spending=category_spending,
                          user_name=user_name)


@finance_bp.route('/overview')
@require_finance_permission('dashboard', 'view')
def overview():
    """Finance Overview - Summary page."""
    return redirect(url_for('finance.dashboard'))


# =============================================================================
# ACCOUNTS & WALLETS ROUTES
# =============================================================================

@finance_bp.route('/accounts')
@require_finance_permission('accounts', 'view')
def accounts():
    """List all accounts."""
    accounts_list = get_all("""
        SELECT a.*, 
               (SELECT COUNT(*) FROM pf_transactions t WHERE t.account_id = a.id AND t.is_active = 1) as transaction_count
        FROM pf_accounts a
        WHERE a.owner_user_id = ? AND a.is_archived = 0
        ORDER BY a.account_type, a.account_name
    """, (get_current_user_id(),))
    
    total_balance = sum(a['current_balance'] for a in accounts_list)
    
    return render_template('finance/accounts/index.html',
                          accounts=accounts_list,
                          total_balance=total_balance)


@finance_bp.route('/accounts/create', methods=['GET', 'POST'])
@require_finance_permission('accounts', 'create')
def create_account():
    """Create new account."""
    if request.method == 'POST':
        data = request.form
        account_code = generate_account_code()
        
        with get_db_context() as db:
            db.execute("""
                INSERT INTO pf_accounts 
                (account_code, account_name, account_type, account_subtype, currency,
                 opening_balance, current_balance, bank_provider, branch_reference,
                 owner_user_id, notes, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
            """, (
                account_code,
                data.get('account_name', ''),
                data.get('account_type', 'bank'),
                data.get('account_subtype', ''),
                data.get('currency', 'USD'),
                float(data.get('opening_balance', 0)),
                float(data.get('opening_balance', 0)),
                data.get('bank_provider', ''),
                data.get('branch_reference', ''),
                get_current_user_id(),
                data.get('notes', ''),
                get_current_user_id()
            ))
            db.commit()
        
        log_finance_audit('create', 'account', 0, account_code, '', '', 'New account created')
        flash(f"Account '{data.get('account_name')}' created successfully.", "success")
        return redirect(url_for('finance.accounts'))
    
    return render_template('finance/accounts/create.html')


@finance_bp.route('/accounts/<int:account_id>/edit', methods=['GET', 'POST'])
@require_finance_permission('accounts', 'edit')
def edit_account(account_id):
    """Edit account."""
    account = get_one("SELECT * FROM pf_accounts WHERE id = ?", (account_id,))
    if not account:
        flash("Account not found.", "error")
        return redirect(url_for('finance.accounts'))
    
    if request.method == 'POST':
        data = request.form
        old_state = row_to_dict(account)
        
        with get_db_context() as db:
            db.execute("""
                UPDATE pf_accounts SET
                    account_name = ?, account_type = ?, account_subtype = ?,
                    currency = ?, bank_provider = ?, branch_reference = ?,
                    notes = ?, is_active = ?, updated_at = datetime('now'), updated_by = ?
                WHERE id = ?
            """, (
                data.get('account_name', ''),
                data.get('account_type', 'bank'),
                data.get('account_subtype', ''),
                data.get('currency', 'USD'),
                data.get('bank_provider', ''),
                data.get('branch_reference', ''),
                data.get('notes', ''),
                1 if data.get('is_active') else 0,
                get_current_user_id(),
                account_id
            ))
            db.commit()
        
        log_finance_audit('update', 'account', account_id, account['account_code'], 
                         str(old_state), str(request.form.to_dict()), 'Account updated')
        flash("Account updated successfully.", "success")
        return redirect(url_for('finance.accounts'))
    
    return render_template('finance/accounts/edit.html', account=account)


@finance_bp.route('/accounts/<int:account_id>/delete', methods=['POST'])
@require_finance_permission('accounts', 'delete')
def delete_account(account_id):
    """Archive account."""
    account = get_one("SELECT * FROM pf_accounts WHERE id = ?", (account_id,))
    if not account:
        return jsonify({'success': False, 'message': 'Account not found'})
    
    with get_db_context() as db:
        db.execute("UPDATE pf_accounts SET is_archived = 1, is_active = 0 WHERE id = ?", (account_id,))
        db.commit()
    
    log_finance_audit('archive', 'account', account_id, account['account_code'], '', '', 'Account archived')
    flash("Account archived successfully.", "success")
    return jsonify({'success': True})


@finance_bp.route('/accounts/transfer', methods=['GET', 'POST'])
@require_finance_permission('accounts', 'create')
def transfer_between_accounts():
    """Transfer between accounts."""
    accounts = get_accounts()
    
    if request.method == 'POST':
        data = request.form
        from_account_id = int(data.get('from_account_id'))
        to_account_id = int(data.get('to_account_id'))
        amount = float(data.get('amount', 0))
        currency = data.get('currency', 'USD')
        
        transfer_code = f"TRF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        with get_db_context() as db:
            # Create transfer record
            db.execute("""
                INSERT INTO pf_account_transfers
                (transfer_code, from_account_id, to_account_id, amount, currency,
                 transfer_date, transfer_type, status, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, datetime('now'), 'manual', 'completed', datetime('now'), ?)
            """, (transfer_code, from_account_id, to_account_id, amount, currency, get_current_user_id()))
            
            # Create expense transaction for source account
            db.execute("""
                INSERT INTO pf_transactions
                (transaction_code, transaction_type, amount, currency, transaction_date,
                 account_id, description, status, is_confirmed, is_active, created_at, created_by)
                VALUES (?, 'expense', ?, ?, datetime('now'), ?, ?, 'completed', 1, 1, datetime('now'), ?)
            """, (f"TXN-EXP-{datetime.now().strftime('%Y%m%d%H%M%S')}", amount, currency, from_account_id,
                  f"Transfer to account #{to_account_id}", get_current_user_id()))
            
            # Create income transaction for destination account
            db.execute("""
                INSERT INTO pf_transactions
                (transaction_code, transaction_type, amount, currency, transaction_date,
                 account_id, description, status, is_confirmed, is_active, created_at, created_by)
                VALUES (?, 'income', ?, ?, datetime('now'), ?, ?, 'completed', 1, 1, datetime('now'), ?)
            """, (f"TXN-INC-{datetime.now().strftime('%Y%m%d%H%M%S')}", amount, currency, to_account_id,
                  f"Transfer from account #{from_account_id}", get_current_user_id()))
            
            db.commit()
        
        log_finance_audit('transfer', 'account_transfer', 0, transfer_code, '', '', 
                         f"Transferred {amount} {currency} from account {from_account_id} to {to_account_id}")
        flash(f"Transfer of {currency} {amount:,.2f} completed successfully.", "success")
        return redirect(url_for('finance.accounts'))
    
    return render_template('finance/accounts/transfer.html', accounts=accounts)


# =============================================================================
# INCOME ROUTES
# =============================================================================

@finance_bp.route('/income')
@require_finance_permission('income', 'view')
def income():
    """List all income records."""
    user_id = get_current_user_id()
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    # Build filter query
    filters = []
    params = [user_id]
    
    if request.args.get('category_id'):
        filters.append("i.category_id = ?")
        params.append(request.args.get('category_id'))
    if request.args.get('income_type'):
        filters.append("i.income_type = ?")
        params.append(request.args.get('income_type'))
    if request.args.get('date_from'):
        filters.append("i.income_date >= ?")
        params.append(request.args.get('date_from'))
    if request.args.get('date_to'):
        filters.append("i.income_date <= ?")
        params.append(request.args.get('date_to'))
    if request.args.get('status'):
        filters.append("i.status = ?")
        params.append(request.args.get('status'))
    
    where_clause = " AND ".join(filters) if filters else "1=1"
    
    # Get total count
    total = get_one(f"""
        SELECT COUNT(*) as count FROM pf_income_records i
        WHERE i.owner_user_id = ? AND i.is_archived = 0 AND {where_clause}
    """, tuple(params))
    total_count = total['count'] if total else 0
    
    # Get records
    records = get_all(f"""
        SELECT i.*, c.category_name, c.color as category_color,
               a.account_name
        FROM pf_income_records i
        LEFT JOIN pf_category_definitions c ON i.category_id = c.id
        LEFT JOIN pf_accounts a ON i.account_id = a.id
        WHERE i.owner_user_id = ? AND i.is_archived = 0 AND {where_clause}
        ORDER BY i.income_date DESC, i.created_at DESC
        LIMIT ? OFFSET ?
    """, tuple(params) + (per_page, offset))
    
    categories = get_categories('income')
    
    return render_template('finance/income/index.html',
                          records=records,
                          categories=categories,
                          total_count=total_count,
                          page=page,
                          per_page=per_page)


@finance_bp.route('/income/create', methods=['GET', 'POST'])
@require_finance_permission('income', 'create')
def create_income():
    """Create new income record."""
    categories = get_categories('income')
    accounts = get_accounts()
    
    if request.method == 'POST':
        data = request.form
        income_number = generate_income_number()
        amount = float(data.get('amount', 0))
        
        with get_db_context() as db:
            db.execute("""
                INSERT INTO pf_income_records
                (income_number, income_type, source, source_name, amount, currency,
                 exchange_rate, amount_base_currency, income_date, account_id, category_id,
                 is_recurring, recurring_pattern, tax_amount, fee_amount, status,
                 notes, tags, is_active, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, datetime('now'), ?)
            """, (
                income_number,
                data.get('income_type', 'salary'),
                data.get('source', ''),
                data.get('source_name', ''),
                amount,
                data.get('currency', 'USD'),
                float(data.get('exchange_rate', 1)),
                amount * float(data.get('exchange_rate', 1)),
                data.get('income_date', datetime.now().strftime('%Y-%m-%d')),
                data.get('account_id', 0),
                data.get('category_id', 0),
                1 if data.get('is_recurring') else 0,
                data.get('recurring_pattern', ''),
                float(data.get('tax_amount', 0)),
                float(data.get('fee_amount', 0)),
                data.get('status', 'received'),
                data.get('notes', ''),
                data.get('tags', ''),
                get_current_user_id()
            ))
            db.commit()
        
        # Create corresponding transaction
        with get_db_context() as db:
            db.execute("""
                INSERT INTO pf_transactions
                (transaction_code, transaction_type, amount, currency, transaction_date,
                 account_id, income_record_id, category_id, description, status,
                 is_confirmed, is_active, created_at, created_by)
                VALUES (?, 'income', ?, ?, ?, ?, ?, ?, ?, 'completed', 1, 1, datetime('now'), ?)
            """, (
                f"TXN-{income_number}",
                amount,
                data.get('currency', 'USD'),
                data.get('income_date', datetime.now().strftime('%Y-%m-%d')),
                data.get('account_id', 0),
                data.get('category_id', 0),
                f"Income: {data.get('source_name', '')}",
                get_current_user_id()
            ))
            db.commit()
        
        log_finance_audit('create', 'income', 0, income_number, '', '', f'New income: {amount}')
        flash(f"Income record '{income_number}' created successfully.", "success")
        return redirect(url_for('finance.income'))
    
    return render_template('finance/income/create.html',
                          categories=categories,
                          accounts=accounts)


@finance_bp.route('/income/<int:income_id>/edit', methods=['GET', 'POST'])
@require_finance_permission('income', 'edit')
def edit_income(income_id):
    """Edit income record."""
    record = get_one("SELECT * FROM pf_income_records WHERE id = ?", (income_id,))
    if not record:
        flash("Income record not found.", "error")
        return redirect(url_for('finance.income'))
    
    categories = get_categories('income')
    accounts = get_accounts()
    
    if request.method == 'POST':
        data = request.form
        old_state = row_to_dict(record)
        
        with get_db_context() as db:
            db.execute("""
                UPDATE pf_income_records SET
                    income_type = ?, source = ?, source_name = ?,
                    amount = ?, currency = ?, exchange_rate = ?,
                    amount_base_currency = ?, income_date = ?,
                    account_id = ?, category_id = ?, is_recurring = ?,
                    recurring_pattern = ?, tax_amount = ?, fee_amount = ?,
                    status = ?, notes = ?, tags = ?,
                    updated_at = datetime('now'), updated_by = ?
                WHERE id = ?
            """, (
                data.get('income_type', 'salary'),
                data.get('source', ''),
                data.get('source_name', ''),
                float(data.get('amount', 0)),
                data.get('currency', 'USD'),
                float(data.get('exchange_rate', 1)),
                float(data.get('amount', 0)) * float(data.get('exchange_rate', 1)),
                data.get('income_date'),
                data.get('account_id', 0),
                data.get('category_id', 0),
                1 if data.get('is_recurring') else 0,
                data.get('recurring_pattern', ''),
                float(data.get('tax_amount', 0)),
                float(data.get('fee_amount', 0)),
                data.get('status', 'received'),
                data.get('notes', ''),
                data.get('tags', ''),
                get_current_user_id(),
                income_id
            ))
            db.commit()
        
        log_finance_audit('update', 'income', income_id, record['income_number'],
                         str(old_state), str(request.form.to_dict()), 'Income updated')
        flash("Income record updated successfully.", "success")
        return redirect(url_for('finance.income'))
    
    return render_template('finance/income/edit.html',
                          record=record,
                          categories=categories,
                          accounts=accounts)


@finance_bp.route('/income/<int:income_id>/delete', methods=['POST'])
@require_finance_permission('income', 'delete')
def delete_income(income_id):
    """Archive income record."""
    record = get_one("SELECT * FROM pf_income_records WHERE id = ?", (income_id,))
    if not record:
        return jsonify({'success': False, 'message': 'Income record not found'})
    
    with get_db_context() as db:
        db.execute("UPDATE pf_income_records SET is_archived = 1, is_active = 0 WHERE id = ?", (income_id,))
        db.commit()
    
    log_finance_audit('archive', 'income', income_id, record['income_number'], '', '', 'Income archived')
    flash("Income record archived successfully.", "success")
    return jsonify({'success': True})


# =============================================================================
# EXPENSES ROUTES
# =============================================================================

@finance_bp.route('/expenses')
@require_finance_permission('expenses', 'view')
def expenses():
    """List all expense records."""
    user_id = get_current_user_id()
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    filters = []
    params = [user_id]
    
    if request.args.get('category_id'):
        filters.append("e.category_id = ?")
        params.append(request.args.get('category_id'))
    if request.args.get('merchant_name'):
        filters.append("e.merchant_name LIKE ?")
        params.append(f"%{request.args.get('merchant_name')}%")
    if request.args.get('date_from'):
        filters.append("e.expense_date >= ?")
        params.append(request.args.get('date_from'))
    if request.args.get('date_to'):
        filters.append("e.expense_date <= ?")
        params.append(request.args.get('date_to'))
    if request.args.get('status'):
        filters.append("e.status = ?")
        params.append(request.args.get('status'))
    if request.args.get('is_flagged'):
        filters.append("e.is_flagged = 1")
    
    where_clause = " AND ".join(filters) if filters else "1=1"
    
    total = get_one(f"""
        SELECT COUNT(*) as count FROM pf_expense_records e
        WHERE e.owner_user_id = ? AND e.is_archived = 0 AND {where_clause}
    """, tuple(params))
    total_count = total['count'] if total else 0
    
    records = get_all(f"""
        SELECT e.*, c.category_name, c.color as category_color, c.icon as category_icon,
               a.account_name
        FROM pf_expense_records e
        LEFT JOIN pf_category_definitions c ON e.category_id = c.id
        LEFT JOIN pf_accounts a ON e.account_id = a.id
        WHERE e.owner_user_id = ? AND e.is_archived = 0 AND {where_clause}
        ORDER BY e.expense_date DESC, e.created_at DESC
        LIMIT ? OFFSET ?
    """, tuple(params) + (per_page, offset))
    
    categories = get_categories('expense')
    
    return render_template('finance/expenses/index.html',
                          records=records,
                          categories=categories,
                          total_count=total_count,
                          page=page,
                          per_page=per_page)


@finance_bp.route('/expenses/create', methods=['GET', 'POST'])
@require_finance_permission('expenses', 'create')
def create_expense():
    """Create new expense record."""
    categories = get_categories('expense')
    accounts = get_accounts()
    
    if request.method == 'POST':
        data = request.form
        expense_number = generate_expense_number()
        amount = float(data.get('amount', 0))
        
        with get_db_context() as db:
            db.execute("""
                INSERT INTO pf_expense_records
                (expense_number, merchant_name, merchant_category, amount, currency,
                 exchange_rate, amount_base_currency, expense_date, account_id, category_id,
                 payment_method, is_recurring, recurring_pattern, receipt_document_id,
                 is_flagged, flag_reason, status, tags, notes, is_active, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, datetime('now'), ?)
            """, (
                expense_number,
                data.get('merchant_name', ''),
                data.get('merchant_category', ''),
                amount,
                data.get('currency', 'USD'),
                float(data.get('exchange_rate', 1)),
                amount * float(data.get('exchange_rate', 1)),
                data.get('expense_date', datetime.now().strftime('%Y-%m-%d')),
                data.get('account_id', 0),
                data.get('category_id', 0),
                data.get('payment_method', 'cash'),
                1 if data.get('is_recurring') else 0,
                data.get('recurring_pattern', ''),
                data.get('receipt_document_id', 0),
                1 if data.get('is_flagged') else 0,
                data.get('flag_reason', ''),
                data.get('status', 'approved'),
                data.get('tags', ''),
                data.get('notes', ''),
                get_current_user_id()
            ))
            db.commit()
        
        # Create transaction
        with get_db_context() as db:
            db.execute("""
                INSERT INTO pf_transactions
                (transaction_code, transaction_type, amount, currency, transaction_date,
                 account_id, expense_record_id, category_id, merchant_payee, description,
                 payment_method, status, is_confirmed, is_active, created_at, created_by)
                VALUES (?, 'expense', ?, ?, ?, ?, ?, ?, ?, ?, ?, 'completed', 1, 1, datetime('now'), ?)
            """, (
                f"TXN-{expense_number}",
                amount,
                data.get('currency', 'USD'),
                data.get('expense_date', datetime.now().strftime('%Y-%m-%d')),
                data.get('account_id', 0),
                data.get('category_id', 0),
                data.get('merchant_name', ''),
                data.get('notes', ''),
                data.get('payment_method', 'cash'),
                get_current_user_id()
            ))
            db.commit()
        
        log_finance_audit('create', 'expense', 0, expense_number, '', '', f'New expense: {amount}')
        flash(f"Expense record '{expense_number}' created successfully.", "success")
        return redirect(url_for('finance.expenses'))
    
    return render_template('finance/expenses/create.html',
                          categories=categories,
                          accounts=accounts)


@finance_bp.route('/expenses/<int:expense_id>/edit', methods=['GET', 'POST'])
@require_finance_permission('expenses', 'edit')
def edit_expense(expense_id):
    """Edit expense record."""
    record = get_one("SELECT * FROM pf_expense_records WHERE id = ?", (expense_id,))
    if not record:
        flash("Expense record not found.", "error")
        return redirect(url_for('finance.expenses'))
    
    categories = get_categories('expense')
    accounts = get_accounts()
    
    if request.method == 'POST':
        data = request.form
        old_state = row_to_dict(record)
        
        with get_db_context() as db:
            db.execute("""
                UPDATE pf_expense_records SET
                    merchant_name = ?, merchant_category = ?, amount = ?,
                    currency = ?, exchange_rate = ?, amount_base_currency = ?,
                    expense_date = ?, account_id = ?, category_id = ?,
                    payment_method = ?, is_recurring = ?, recurring_pattern = ?,
                    is_flagged = ?, flag_reason = ?, status = ?,
                    tags = ?, notes = ?,
                    updated_at = datetime('now'), updated_by = ?
                WHERE id = ?
            """, (
                data.get('merchant_name', ''),
                data.get('merchant_category', ''),
                float(data.get('amount', 0)),
                data.get('currency', 'USD'),
                float(data.get('exchange_rate', 1)),
                float(data.get('amount', 0)) * float(data.get('exchange_rate', 1)),
                data.get('expense_date'),
                data.get('account_id', 0),
                data.get('category_id', 0),
                data.get('payment_method', 'cash'),
                1 if data.get('is_recurring') else 0,
                data.get('recurring_pattern', ''),
                1 if data.get('is_flagged') else 0,
                data.get('flag_reason', ''),
                data.get('status', 'approved'),
                data.get('tags', ''),
                data.get('notes', ''),
                get_current_user_id(),
                expense_id
            ))
            db.commit()
        
        log_finance_audit('update', 'expense', expense_id, record['expense_number'],
                         str(old_state), str(request.form.to_dict()), 'Expense updated')
        flash("Expense record updated successfully.", "success")
        return redirect(url_for('finance.expenses'))
    
    return render_template('finance/expenses/edit.html',
                          record=record,
                          categories=categories,
                          accounts=accounts)


@finance_bp.route('/expenses/<int:expense_id>/delete', methods=['POST'])
@require_finance_permission('expenses', 'delete')
def delete_expense(expense_id):
    """Archive expense record."""
    record = get_one("SELECT * FROM pf_expense_records WHERE id = ?", (expense_id,))
    if not record:
        return jsonify({'success': False, 'message': 'Expense record not found'})
    
    with get_db_context() as db:
        db.execute("UPDATE pf_expense_records SET is_archived = 1, is_active = 0 WHERE id = ?", (expense_id,))
        db.commit()
    
    log_finance_audit('archive', 'expense', expense_id, record['expense_number'], '', '', 'Expense archived')
    flash("Expense record archived successfully.", "success")
    return jsonify({'success': True})


# =============================================================================
# TRANSACTIONS ROUTES
# =============================================================================

@finance_bp.route('/transactions')
@require_finance_permission('transactions', 'view')
def transactions():
    """List all transactions."""
    user_id = get_current_user_id()
    page = int(request.args.get('page', 1))
    per_page = 25
    offset = (page - 1) * per_page
    
    filters = []
    params = [user_id]
    
    if request.args.get('transaction_type'):
        filters.append("t.transaction_type = ?")
        params.append(request.args.get('transaction_type'))
    if request.args.get('category_id'):
        filters.append("t.category_id = ?")
        params.append(request.args.get('category_id'))
    if request.args.get('account_id'):
        filters.append("t.account_id = ?")
        params.append(request.args.get('account_id'))
    if request.args.get('date_from'):
        filters.append("t.transaction_date >= ?")
        params.append(request.args.get('date_from'))
    if request.args.get('date_to'):
        filters.append("t.transaction_date <= ?")
        params.append(request.args.get('date_to'))
    if request.args.get('status'):
        filters.append("t.status = ?")
        params.append(request.args.get('status'))
    if request.args.get('search'):
        filters.append("(t.description LIKE ? OR t.merchant_payee LIKE ? OR t.transaction_code LIKE ?)")
        search_term = f"%{request.args.get('search')}%"
        params.extend([search_term, search_term, search_term])
    
    where_clause = " AND ".join(filters) if filters else "1=1"
    
    total = get_one(f"""
        SELECT COUNT(*) as count FROM pf_transactions t
        WHERE t.owner_user_id = ? AND t.is_archived = 0 AND {where_clause}
    """, tuple(params))
    total_count = total['count'] if total else 0
    
    transactions_list = get_all(f"""
        SELECT t.*, c.category_name, c.color as category_color, c.icon as category_icon,
               a.account_name, a.account_type
        FROM pf_transactions t
        LEFT JOIN pf_category_definitions c ON t.category_id = c.id
        LEFT JOIN pf_accounts a ON t.account_id = a.id
        WHERE t.owner_user_id = ? AND t.is_archived = 0 AND {where_clause}
        ORDER BY t.transaction_date DESC, t.created_at DESC
        LIMIT ? OFFSET ?
    """, tuple(params) + (per_page, offset))
    
    categories = get_categories()
    accounts = get_accounts()
    
    return render_template('finance/transactions/index.html',
                          transactions=transactions_list,
                          categories=categories,
                          accounts=accounts,
                          total_count=total_count,
                          page=page,
                          per_page=per_page)


@finance_bp.route('/transactions/create', methods=['GET', 'POST'])
@require_finance_permission('transactions', 'create')
def create_transaction():
    """Create new transaction."""
    categories = get_categories()
    accounts = get_accounts()
    
    if request.method == 'POST':
        data = request.form
        transaction_code = generate_transaction_code()
        amount = float(data.get('amount', 0))
        
        with get_db_context() as db:
            db.execute("""
                INSERT INTO pf_transactions
                (transaction_code, transaction_type, amount, currency, exchange_rate,
                 amount_base_currency, transaction_date, account_id, category_id,
                 merchant_payee, description, payment_method, is_recurring, recurring_pattern,
                 status, is_confirmed, is_flagged, flag_reason, tags, notes,
                 is_active, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, datetime('now'), ?)
            """, (
                transaction_code,
                data.get('transaction_type', 'expense'),
                amount,
                data.get('currency', 'USD'),
                float(data.get('exchange_rate', 1)),
                amount * float(data.get('exchange_rate', 1)),
                data.get('transaction_date', datetime.now().strftime('%Y-%m-%d')),
                data.get('account_id', 0),
                data.get('category_id', 0),
                data.get('merchant_payee', ''),
                data.get('description', ''),
                data.get('payment_method', 'cash'),
                1 if data.get('is_recurring') else 0,
                data.get('recurring_pattern', ''),
                data.get('status', 'completed'),
                1 if data.get('is_confirmed') else 0,
                1 if data.get('is_flagged') else 0,
                data.get('flag_reason', ''),
                data.get('tags', ''),
                data.get('notes', ''),
                get_current_user_id()
            ))
            db.commit()
        
        log_finance_audit('create', 'transaction', 0, transaction_code, '', '', 
                         f'New {data.get("transaction_type")}: {amount}')
        flash(f"Transaction '{transaction_code}' created successfully.", "success")
        return redirect(url_for('finance.transactions'))
    
    return render_template('finance/transactions/create.html',
                          categories=categories,
                          accounts=accounts)


@finance_bp.route('/transactions/<int:transaction_id>/edit', methods=['GET', 'POST'])
@require_finance_permission('transactions', 'edit')
def edit_transaction(transaction_id):
    """Edit transaction."""
    record = get_one("SELECT * FROM pf_transactions WHERE id = ?", (transaction_id,))
    if not record:
        flash("Transaction not found.", "error")
        return redirect(url_for('finance.transactions'))
    
    categories = get_categories()
    accounts = get_accounts()
    
    if request.method == 'POST':
        data = request.form
        old_state = row_to_dict(record)
        
        with get_db_context() as db:
            db.execute("""
                UPDATE pf_transactions SET
                    transaction_type = ?, amount = ?, currency = ?,
                    exchange_rate = ?, amount_base_currency = ?,
                    transaction_date = ?, account_id = ?, category_id = ?,
                    merchant_payee = ?, description = ?, payment_method = ?,
                    is_recurring = ?, recurring_pattern = ?, status = ?,
                    is_confirmed = ?, is_flagged = ?, flag_reason = ?,
                    tags = ?, notes = ?,
                    updated_at = datetime('now'), updated_by = ?
                WHERE id = ?
            """, (
                data.get('transaction_type', 'expense'),
                float(data.get('amount', 0)),
                data.get('currency', 'USD'),
                float(data.get('exchange_rate', 1)),
                float(data.get('amount', 0)) * float(data.get('exchange_rate', 1)),
                data.get('transaction_date'),
                data.get('account_id', 0),
                data.get('category_id', 0),
                data.get('merchant_payee', ''),
                data.get('description', ''),
                data.get('payment_method', 'cash'),
                1 if data.get('is_recurring') else 0,
                data.get('recurring_pattern', ''),
                data.get('status', 'completed'),
                1 if data.get('is_confirmed') else 0,
                1 if data.get('is_flagged') else 0,
                data.get('flag_reason', ''),
                data.get('tags', ''),
                data.get('notes', ''),
                get_current_user_id(),
                transaction_id
            ))
            db.commit()
        
        log_finance_audit('update', 'transaction', transaction_id, record['transaction_code'],
                         str(old_state), str(request.form.to_dict()), 'Transaction updated')
        flash("Transaction updated successfully.", "success")
        return redirect(url_for('finance.transactions'))
    
    return render_template('finance/transactions/edit.html',
                          record=record,
                          categories=categories,
                          accounts=accounts)


@finance_bp.route('/transactions/<int:transaction_id>/delete', methods=['POST'])
@require_finance_permission('transactions', 'delete')
def delete_transaction(transaction_id):
    """Archive transaction."""
    record = get_one("SELECT * FROM pf_transactions WHERE id = ?", (transaction_id,))
    if not record:
        return jsonify({'success': False, 'message': 'Transaction not found'})
    
    with get_db_context() as db:
        db.execute("""
            UPDATE pf_transactions 
            SET is_archived = 1, is_active = 0, archived_at = datetime('now')
            WHERE id = ?
        """, (transaction_id,))
        db.commit()
    
    log_finance_audit('archive', 'transaction', transaction_id, record['transaction_code'], '', '', 'Transaction archived')
    return jsonify({'success': True})


@finance_bp.route('/transactions/bulk-action', methods=['POST'])
@require_finance_permission('transactions', 'edit')
def bulk_transaction_action():
    """Bulk action on transactions."""
    data = request.get_json()
    action = data.get('action')
    transaction_ids = data.get('ids', [])
    
    if not transaction_ids:
        return jsonify({'success': False, 'message': 'No transactions selected'})
    
    with get_db_context() as db:
        if action == 'confirm':
            db.execute(f"""
                UPDATE pf_transactions SET is_confirmed = 1, updated_at = datetime('now')
                WHERE id IN ({','.join('?' * len(transaction_ids))})
            """, transaction_ids)
        elif action == 'unconfirm':
            db.execute(f"""
                UPDATE pf_transactions SET is_confirmed = 0, updated_at = datetime('now')
                WHERE id IN ({','.join('?' * len(transaction_ids))})
            """, transaction_ids)
        elif action == 'flag':
            db.execute(f"""
                UPDATE pf_transactions SET is_flagged = 1, updated_at = datetime('now')
                WHERE id IN ({','.join('?' * len(transaction_ids))})
            """, transaction_ids)
        elif action == 'archive':
            db.execute(f"""
                UPDATE pf_transactions SET is_archived = 1, is_active = 0, archived_at = datetime('now')
                WHERE id IN ({','.join('?' * len(transaction_ids))})
            """, transaction_ids)
        db.commit()
    
    return jsonify({'success': True, 'count': len(transaction_ids)})


# =============================================================================
# BUDGETS ROUTES
# =============================================================================

@finance_bp.route('/budgets')
@require_finance_permission('budgets', 'view')
def budgets():
    """List all budgets."""
    user_id = get_current_user_id()
    today = datetime.now().strftime('%Y-%m-%d')
    
    budgets_list = get_all("""
        SELECT * FROM pf_budgets
        WHERE owner_user_id = ? AND is_archived = 0
        ORDER BY created_at DESC
    """, (user_id,))
    
    budget_data = []
    for budget in budgets_list:
        status = get_budget_status(budget['id'])
        budget_dict = row_to_dict(budget)
        budget_dict.update(status)
        budget_data.append(budget_dict)
    
    return render_template('finance/budgets/index.html', budgets=budget_data)


@finance_bp.route('/budgets/create', methods=['GET', 'POST'])
@require_finance_permission('budgets', 'create')
def create_budget():
    """Create new budget."""
    categories = get_categories('expense')
    
    if request.method == 'POST':
        data = request.form
        budget_code = generate_budget_code()
        
        period_start = data.get('period_start_date', datetime.now().replace(day=1).strftime('%Y-%m-%d'))
        period_end = data.get('period_end_date', (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1 - timedelta(days=1)).strftime('%Y-%m-%d'))
        
        with get_db_context() as db:
            budget_id = db.execute("""
                INSERT INTO pf_budgets
                (budget_code, budget_name, budget_type, budget_scope, total_budget, currency,
                 period_start_date, period_end_date, warning_threshold, hard_cap,
                 rollover_enabled, owner_user_id, status, notes, is_active, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, 1, datetime('now'), ?)
            """, (
                budget_code,
                data.get('budget_name', ''),
                data.get('budget_type', 'monthly'),
                data.get('budget_scope', 'personal'),
                float(data.get('total_budget', 0)),
                data.get('currency', 'USD'),
                period_start,
                period_end,
                float(data.get('warning_threshold', 80)),
                1 if data.get('hard_cap') else 0,
                1 if data.get('rollover_enabled') else 0,
                get_current_user_id(),
                data.get('notes', ''),
                get_current_user_id()
            )).lastrowid
            
            # Add budget lines
            category_allocations = data.getlist('category_allocations')
            for i, cat_id in enumerate(data.getlist('category_ids')):
                if cat_id and i < len(category_allocations):
                    db.execute("""
                        INSERT INTO pf_budget_lines
                        (budget_id, category_id, allocated_amount, warning_threshold, created_at)
                        VALUES (?, ?, ?, ?, datetime('now'))
                    """, (budget_id, int(cat_id), float(category_allocations[i]), 
                          float(data.get('warning_threshold', 80))))
            
            db.commit()
        
        log_finance_audit('create', 'budget', budget_id, budget_code, '', '', 'New budget created')
        flash(f"Budget '{data.get('budget_name')}' created successfully.", "success")
        return redirect(url_for('finance.budgets'))
    
    return render_template('finance/budgets/create.html', categories=categories)


@finance_bp.route('/budgets/<int:budget_id>/edit', methods=['GET', 'POST'])
@require_finance_permission('budgets', 'edit')
def edit_budget(budget_id):
    """Edit budget."""
    budget = get_one("SELECT * FROM pf_budgets WHERE id = ?", (budget_id,))
    if not budget:
        flash("Budget not found.", "error")
        return redirect(url_for('finance.budgets'))
    
    categories = get_categories('expense')
    budget_lines = get_all("SELECT * FROM pf_budget_lines WHERE budget_id = ?", (budget_id,))
    
    if request.method == 'POST':
        data = request.form
        
        with get_db_context() as db:
            db.execute("""
                UPDATE pf_budgets SET
                    budget_name = ?, budget_type = ?, budget_scope = ?,
                    total_budget = ?, currency = ?,
                    period_start_date = ?, period_end_date = ?,
                    warning_threshold = ?, hard_cap = ?, rollover_enabled = ?,
                    status = ?, notes = ?,
                    updated_at = datetime('now'), updated_by = ?
                WHERE id = ?
            """, (
                data.get('budget_name', ''),
                data.get('budget_type', 'monthly'),
                data.get('budget_scope', 'personal'),
                float(data.get('total_budget', 0)),
                data.get('currency', 'USD'),
                data.get('period_start_date'),
                data.get('period_end_date'),
                float(data.get('warning_threshold', 80)),
                1 if data.get('hard_cap') else 0,
                1 if data.get('rollover_enabled') else 0,
                data.get('status', 'active'),
                data.get('notes', ''),
                get_current_user_id(),
                budget_id
            ))
            
            # Update budget lines
            db.execute("DELETE FROM pf_budget_lines WHERE budget_id = ?", (budget_id,))
            
            for i, cat_id in enumerate(data.getlist('category_ids')):
                alloc = data.getlist('category_allocations')[i] if i < len(data.getlist('category_allocations')) else 0
                if cat_id:
                    db.execute("""
                        INSERT INTO pf_budget_lines
                        (budget_id, category_id, allocated_amount, warning_threshold, created_at)
                        VALUES (?, ?, ?, ?, datetime('now'))
                    """, (budget_id, int(cat_id), float(alloc), float(data.get('warning_threshold', 80))))
            
            db.commit()
        
        log_finance_audit('update', 'budget', budget_id, budget['budget_code'], '', '', 'Budget updated')
        flash("Budget updated successfully.", "success")
        return redirect(url_for('finance.budgets'))
    
    status = get_budget_status(budget_id)
    return render_template('finance/budgets/edit.html', 
                          budget=budget, 
                          budget_lines=budget_lines,
                          categories=categories,
                          status=status)


@finance_bp.route('/budgets/<int:budget_id>/delete', methods=['POST'])
@require_finance_permission('budgets', 'delete')
def delete_budget(budget_id):
    """Archive budget."""
    budget = get_one("SELECT * FROM pf_budgets WHERE id = ?", (budget_id,))
    if not budget:
        return jsonify({'success': False, 'message': 'Budget not found'})
    
    with get_db_context() as db:
        db.execute("UPDATE pf_budgets SET is_archived = 1, is_active = 0 WHERE id = ?", (budget_id,))
        db.commit()
    
    log_finance_audit('archive', 'budget', budget_id, budget['budget_code'], '', '', 'Budget archived')
    return jsonify({'success': True})


# =============================================================================
# SAVINGS & GOALS ROUTES
# =============================================================================

@finance_bp.route('/goals')
@require_finance_permission('goals', 'view')
def goals():
    """List all financial goals."""
    user_id = get_current_user_id()
    
    goals_list = get_all("""
        SELECT g.*, sb.bucket_name, sb.current_amount as savings_amount
        FROM pf_financial_goals g
        LEFT JOIN pf_savings_buckets sb ON g.linked_savings_bucket_id = sb.id
        WHERE g.owner_user_id = ? AND g.is_archived = 0
        ORDER BY g.priority, g.target_date
    """, (user_id,))
    
    goals_data = []
    for goal in goals_list:
        progress = get_savings_progress(goal['id'])
        goal_dict = row_to_dict(goal)
        goal_dict.update(progress)
        goals_data.append(goal_dict)
    
    return render_template('finance/goals/index.html', goals=goals_data)


@finance_bp.route('/goals/create', methods=['GET', 'POST'])
@require_finance_permission('goals', 'create')
def create_goal():
    """Create new financial goal."""
    savings_buckets = get_all("""
        SELECT * FROM pf_savings_buckets 
        WHERE owner_user_id = ? AND is_active = 1
    """, (get_current_user_id(),))
    
    if request.method == 'POST':
        data = request.form
        goal_code = generate_goal_code()
        
        with get_db_context() as db:
            db.execute("""
                INSERT INTO pf_financial_goals
                (goal_code, goal_name, goal_type, target_amount, current_progress,
                 currency, target_date, priority, linked_savings_bucket_id,
                 owner_user_id, status, notes, is_active, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, 1, datetime('now'), ?)
            """, (
                goal_code,
                data.get('goal_name', ''),
                data.get('goal_type', 'short_term'),
                float(data.get('target_amount', 0)),
                float(data.get('current_progress', 0)),
                data.get('currency', 'USD'),
                data.get('target_date', ''),
                int(data.get('priority', 2)),
                data.get('linked_savings_bucket_id', 0),
                get_current_user_id(),
                data.get('notes', ''),
                get_current_user_id()
            ))
            db.commit()
        
        log_finance_audit('create', 'goal', 0, goal_code, '', '', f'New goal: {data.get("goal_name")}')
        flash(f"Goal '{data.get('goal_name')}' created successfully.", "success")
        return redirect(url_for('finance.goals'))
    
    return render_template('finance/goals/create.html', savings_buckets=savings_buckets)


@finance_bp.route('/goals/<int:goal_id>/edit', methods=['GET', 'POST'])
@require_finance_permission('goals', 'edit')
def edit_goal(goal_id):
    """Edit financial goal."""
    goal = get_one("SELECT * FROM pf_financial_goals WHERE id = ?", (goal_id,))
    if not goal:
        flash("Goal not found.", "error")
        return redirect(url_for('finance.goals'))
    
    savings_buckets = get_all("""
        SELECT * FROM pf_savings_buckets 
        WHERE owner_user_id = ? AND is_active = 1
    """, (get_current_user_id(),))
    
    if request.method == 'POST':
        data = request.form
        
        with get_db_context() as db:
            db.execute("""
                UPDATE pf_financial_goals SET
                    goal_name = ?, goal_type = ?, target_amount = ?,
                    current_progress = ?, currency = ?, target_date = ?,
                    priority = ?, linked_savings_bucket_id = ?,
                    status = ?, notes = ?,
                    updated_at = datetime('now'), updated_by = ?
                WHERE id = ?
            """, (
                data.get('goal_name', ''),
                data.get('goal_type', 'short_term'),
                float(data.get('target_amount', 0)),
                float(data.get('current_progress', 0)),
                data.get('currency', 'USD'),
                data.get('target_date', ''),
                int(data.get('priority', 2)),
                data.get('linked_savings_bucket_id', 0),
                data.get('status', 'active'),
                data.get('notes', ''),
                get_current_user_id(),
                goal_id
            ))
            db.commit()
        
        log_finance_audit('update', 'goal', goal_id, goal['goal_code'], '', '', 'Goal updated')
        flash("Goal updated successfully.", "success")
        return redirect(url_for('finance.goals'))
    
    progress = get_savings_progress(goal_id)
    return render_template('finance/goals/edit.html', 
                          goal=goal, 
                          savings_buckets=savings_buckets,
                          progress=progress)


@finance_bp.route('/goals/<int:goal_id>/delete', methods=['POST'])
@require_finance_permission('goals', 'delete')
def delete_goal(goal_id):
    """Archive goal."""
    goal = get_one("SELECT * FROM pf_financial_goals WHERE id = ?", (goal_id,))
    if not goal:
        return jsonify({'success': False, 'message': 'Goal not found'})
    
    with get_db_context() as db:
        db.execute("UPDATE pf_financial_goals SET is_archived = 1, is_active = 0 WHERE id = ?", (goal_id,))
        db.commit()
    
    log_finance_audit('archive', 'goal', goal_id, goal['goal_code'], '', '', 'Goal archived')
    return jsonify({'success': True})


@finance_bp.route('/savings')
@require_finance_permission('savings', 'view')
def savings():
    """List all savings buckets."""
    user_id = get_current_user_id()
    
    buckets = get_all("""
        SELECT sb.*, g.goal_name, g.target_amount as goal_target
        FROM pf_savings_buckets sb
        LEFT JOIN pf_financial_goals g ON sb.goal_id = g.id
        WHERE sb.owner_user_id = ? AND sb.is_archived = 0
        ORDER BY sb.priority, sb.bucket_name
    """, (user_id,))
    
    return render_template('finance/savings/index.html', buckets=buckets)


@finance_bp.route('/savings/create', methods=['GET', 'POST'])
@require_finance_permission('savings', 'create')
def create_savings_bucket():
    """Create savings bucket."""
    if request.method == 'POST':
        data = request.form
        bucket_code = f"SAV-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        with get_db_context() as db:
            db.execute("""
                INSERT INTO pf_savings_buckets
                (bucket_code, bucket_name, goal_id, savings_type, current_amount,
                 target_amount, currency, priority, recurring_amount, recurring_frequency,
                 owner_user_id, is_auto_transfer, linked_account_id, status, notes,
                 is_active, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, 1, datetime('now'), ?)
            """, (
                bucket_code,
                data.get('bucket_name', ''),
                data.get('goal_id', 0),
                data.get('savings_type', 'general'),
                float(data.get('current_amount', 0)),
                float(data.get('target_amount', 0)),
                data.get('currency', 'USD'),
                int(data.get('priority', 1)),
                float(data.get('recurring_amount', 0)),
                data.get('recurring_frequency', 'monthly'),
                get_current_user_id(),
                1 if data.get('is_auto_transfer') else 0,
                data.get('linked_account_id', 0),
                data.get('notes', ''),
                get_current_user_id()
            ))
            db.commit()
        
        flash(f"Savings bucket '{data.get('bucket_name')}' created successfully.", "success")
        return redirect(url_for('finance.savings'))
    
    goals = get_all("SELECT * FROM pf_financial_goals WHERE owner_user_id = ? AND is_active = 1", 
                   (get_current_user_id(),))
    accounts = get_accounts()
    return render_template('finance/savings/create.html', goals=goals, accounts=accounts)


# =============================================================================
# INVESTMENTS ROUTES
# =============================================================================

@finance_bp.route('/investments')
@require_finance_permission('investments', 'view')
def investments():
    """List all investments."""
    user_id = get_current_user_id()
    
    investments_list = get_all("""
        SELECT i.*, a.account_name
        FROM pf_investments i
        LEFT JOIN pf_accounts a ON i.linked_account_id = a.id
        WHERE i.owner_user_id = ? AND i.is_archived = 0
        ORDER BY i.asset_class, i.asset_name
    """, (user_id,))
    
    # Calculate totals
    total_cost = sum(inv['cost_basis'] for inv in investments_list)
    total_current = sum(inv['current_value'] for inv in investments_list)
    total_gain_loss = total_current - total_cost
    total_gain_loss_pct = (total_gain_loss / total_cost * 100) if total_cost > 0 else 0
    
    return render_template('finance/investments/index.html',
                          investments=investments_list,
                          total_cost=total_cost,
                          total_current=total_current,
                          total_gain_loss=total_gain_loss,
                          total_gain_loss_pct=total_gain_loss_pct)


@finance_bp.route('/investments/create', methods=['GET', 'POST'])
@require_finance_permission('investments', 'create')
def create_investment():
    """Create new investment."""
    accounts = get_accounts()
    
    if request.method == 'POST':
        data = request.form
        investment_code = generate_investment_code()
        quantity = float(data.get('quantity', 0))
        purchase_price = float(data.get('purchase_price', 0))
        purchase_value = quantity * purchase_price
        
        with get_db_context() as db:
            db.execute("""
                INSERT INTO pf_investments
                (investment_code, asset_name, asset_class, asset_subclass, quantity,
                 purchase_price, purchase_value, current_price, current_value,
                 cost_basis, realized_gain_loss, unrealized_gain_loss,
                 dividends_received, currency, acquisition_date, linked_account_id,
                 risk_level, broker_provider, notes, status, is_active,
                 created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, ?, ?, ?, ?, ?, ?, ?, 'held', 1, datetime('now'), ?)
            """, (
                investment_code,
                data.get('asset_name', ''),
                data.get('asset_class', 'stock'),
                data.get('asset_subclass', ''),
                quantity,
                purchase_price,
                purchase_value,
                purchase_price,  # current_price starts at purchase
                purchase_value,  # current_value starts at purchase
                purchase_value,  # cost_basis
                data.get('currency', 'USD'),
                data.get('acquisition_date', datetime.now().strftime('%Y-%m-%d')),
                data.get('linked_account_id', 0),
                data.get('risk_level', 'medium'),
                data.get('broker_provider', ''),
                data.get('notes', ''),
                get_current_user_id()
            ))
            db.commit()
        
        log_finance_audit('create', 'investment', 0, investment_code, '', '', f'New investment: {data.get("asset_name")}')
        flash(f"Investment '{data.get('asset_name')}' created successfully.", "success")
        return redirect(url_for('finance.investments'))
    
    return render_template('finance/investments/create.html', accounts=accounts)


@finance_bp.route('/investments/<int:investment_id>/edit', methods=['GET', 'POST'])
@require_finance_permission('investments', 'edit')
def edit_investment(investment_id):
    """Edit investment."""
    investment = get_one("SELECT * FROM pf_investments WHERE id = ?", (investment_id,))
    if not investment:
        flash("Investment not found.", "error")
        return redirect(url_for('finance.investments'))
    
    accounts = get_accounts()
    
    if request.method == 'POST':
        data = request.form
        quantity = float(data.get('quantity', 0))
        purchase_price = float(data.get('purchase_price', 0))
        current_price = float(data.get('current_price', 0))
        current_value = quantity * current_price
        cost_basis = quantity * purchase_price
        
        with get_db_context() as db:
            db.execute("""
                UPDATE pf_investments SET
                    asset_name = ?, asset_class = ?, asset_subclass = ?,
                    quantity = ?, purchase_price = ?, purchase_value = ?,
                    current_price = ?, current_value = ?, cost_basis = ?,
                    currency = ?, acquisition_date = ?, linked_account_id = ?,
                    risk_level = ?, broker_provider = ?, notes = ?, status = ?,
                    updated_at = datetime('now'), updated_by = ?
                WHERE id = ?
            """, (
                data.get('asset_name', ''),
                data.get('asset_class', 'stock'),
                data.get('asset_subclass', ''),
                quantity,
                purchase_price,
                quantity * purchase_price,
                current_price,
                current_value,
                cost_basis,
                data.get('currency', 'USD'),
                data.get('acquisition_date'),
                data.get('linked_account_id', 0),
                data.get('risk_level', 'medium'),
                data.get('broker_provider', ''),
                data.get('notes', ''),
                data.get('status', 'held'),
                get_current_user_id(),
                investment_id
            ))
            db.commit()
        
        log_finance_audit('update', 'investment', investment_id, investment['investment_code'], '', '', 'Investment updated')
        flash("Investment updated successfully.", "success")
        return redirect(url_for('finance.investments'))
    
    return render_template('finance/investments/edit.html', 
                          investment=investment, 
                          accounts=accounts)


@finance_bp.route('/investments/<int:investment_id>/delete', methods=['POST'])
@require_finance_permission('investments', 'delete')
def delete_investment(investment_id):
    """Archive investment."""
    investment = get_one("SELECT * FROM pf_investments WHERE id = ?", (investment_id,))
    if not investment:
        return jsonify({'success': False, 'message': 'Investment not found'})
    
    with get_db_context() as db:
        db.execute("UPDATE pf_investments SET is_archived = 1, is_active = 0 WHERE id = ?", (investment_id,))
        db.commit()
    
    log_finance_audit('archive', 'investment', investment_id, investment['investment_code'], '', '', 'Investment archived')
    return jsonify({'success': True})


# =============================================================================
# DEBTS & LOANS ROUTES
# =============================================================================

@finance_bp.route('/debts')
@require_finance_permission('debts', 'view')
def debts():
    """List all debts."""
    user_id = get_current_user_id()
    
    debts_list = get_all("""
        SELECT d.*, a.account_name
        FROM pf_debts d
        LEFT JOIN pf_accounts a ON d.linked_account_id = a.id
        WHERE d.owner_user_id = ? AND d.is_archived = 0
        ORDER BY d.priority, d.next_due_date
    """, (user_id,))
    
    total_debt = sum(d['remaining_balance'] for d in debts_list)
    total_monthly = sum(d['monthly_installment'] for d in debts_list)
    
    return render_template('finance/debts/index.html',
                          debts=debts_list,
                          total_debt=total_debt,
                          total_monthly=total_monthly)


@finance_bp.route('/debts/create', methods=['GET', 'POST'])
@require_finance_permission('debts', 'create')
def create_debt():
    """Create new debt."""
    accounts = get_accounts()
    
    if request.method == 'POST':
        data = request.form
        debt_code = generate_debt_code()
        
        with get_db_context() as db:
            db.execute("""
                INSERT INTO pf_debts
                (debt_code, lender, debt_type, principal, remaining_balance,
                 monthly_installment, interest_rate, interest_type,
                 start_date, end_date, next_due_date, linked_account_id,
                 priority, owner_user_id, status, notes, is_active,
                 created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, 1, datetime('now'), ?)
            """, (
                debt_code,
                data.get('lender', ''),
                data.get('debt_type', 'loan'),
                float(data.get('principal', 0)),
                float(data.get('remaining_balance', 0)),
                float(data.get('monthly_installment', 0)),
                float(data.get('interest_rate', 0)),
                data.get('interest_type', 'fixed'),
                data.get('start_date', ''),
                data.get('end_date', ''),
                data.get('next_due_date', ''),
                data.get('linked_account_id', 0),
                int(data.get('priority', 2)),
                get_current_user_id(),
                data.get('notes', ''),
                get_current_user_id()
            ))
            db.commit()
        
        log_finance_audit('create', 'debt', 0, debt_code, '', '', f'New debt: {data.get("lender")}')
        flash(f"Debt '{data.get('lender')}' created successfully.", "success")
        return redirect(url_for('finance.debts'))
    
    return render_template('finance/debts/create.html', accounts=accounts)


@finance_bp.route('/debts/<int:debt_id>/edit', methods=['GET', 'POST'])
@require_finance_permission('debts', 'edit')
def edit_debt(debt_id):
    """Edit debt."""
    debt = get_one("SELECT * FROM pf_debts WHERE id = ?", (debt_id,))
    if not debt:
        flash("Debt not found.", "error")
        return redirect(url_for('finance.debts'))
    
    accounts = get_accounts()
    
    if request.method == 'POST':
        data = request.form
        
        with get_db_context() as db:
            db.execute("""
                UPDATE pf_debts SET
                    lender = ?, debt_type = ?, principal = ?,
                    remaining_balance = ?, monthly_installment = ?,
                    interest_rate = ?, interest_type = ?,
                    start_date = ?, end_date = ?, next_due_date = ?,
                    linked_account_id = ?, priority = ?,
                    status = ?, notes = ?,
                    updated_at = datetime('now'), updated_by = ?
                WHERE id = ?
            """, (
                data.get('lender', ''),
                data.get('debt_type', 'loan'),
                float(data.get('principal', 0)),
                float(data.get('remaining_balance', 0)),
                float(data.get('monthly_installment', 0)),
                float(data.get('interest_rate', 0)),
                data.get('interest_type', 'fixed'),
                data.get('start_date', ''),
                data.get('end_date', ''),
                data.get('next_due_date', ''),
                data.get('linked_account_id', 0),
                int(data.get('priority', 2)),
                data.get('status', 'active'),
                data.get('notes', ''),
                get_current_user_id(),
                debt_id
            ))
            db.commit()
        
        log_finance_audit('update', 'debt', debt_id, debt['debt_code'], '', '', 'Debt updated')
        flash("Debt updated successfully.", "success")
        return redirect(url_for('finance.debts'))
    
    return render_template('finance/debts/edit.html', debt=debt, accounts=accounts)


@finance_bp.route('/debts/<int:debt_id>/delete', methods=['POST'])
@require_finance_permission('debts', 'delete')
def delete_debt(debt_id):
    """Archive debt."""
    debt = get_one("SELECT * FROM pf_debts WHERE id = ?", (debt_id,))
    if not debt:
        return jsonify({'success': False, 'message': 'Debt not found'})
    
    with get_db_context() as db:
        db.execute("UPDATE pf_debts SET is_archived = 1, is_active = 0 WHERE id = ?", (debt_id,))
        db.commit()
    
    log_finance_audit('archive', 'debt', debt_id, debt['debt_code'], '', '', 'Debt archived')
    return jsonify({'success': True})


@finance_bp.route('/debts/<int:debt_id>/record-payment', methods=['POST'])
@require_finance_permission('debts', 'edit')
def record_debt_payment(debt_id):
    """Record debt payment."""
    debt = get_one("SELECT * FROM pf_debts WHERE id = ?", (debt_id,))
    if not debt:
        return jsonify({'success': False, 'message': 'Debt not found'})
    
    data = request.get_json()
    payment_amount = float(data.get('amount', 0))
    
    with get_db_context() as db:
        new_balance = debt['remaining_balance'] - payment_amount
        db.execute("""
            UPDATE pf_debts SET
                remaining_balance = ?,
                total_paid = total_paid + ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (max(0, new_balance), payment_amount, debt_id))
        db.commit()
    
    return jsonify({'success': True, 'new_balance': max(0, new_balance)})


# =============================================================================
# ASSETS ROUTES
# =============================================================================

@finance_bp.route('/assets')
@require_finance_permission('assets', 'view')
def assets():
    """List all assets."""
    user_id = get_current_user_id()
    
    assets_list = get_all("""
        SELECT * FROM pf_assets
        WHERE owner_user_id = ? AND is_archived = 0
        ORDER BY asset_type, asset_name
    """, (user_id,))
    
    total_value = sum(a['current_value'] for a in assets_list)
    total_purchase = sum(a['purchase_value'] for a in assets_list)
    
    return render_template('finance/assets/index.html',
                          assets=assets_list,
                          total_value=total_value,
                          total_purchase=total_purchase)


@finance_bp.route('/assets/create', methods=['GET', 'POST'])
@require_finance_permission('assets', 'create')
def create_asset():
    """Create new asset."""
    if request.method == 'POST':
        data = request.form
        asset_code = generate_asset_code()
        
        with get_db_context() as db:
            db.execute("""
                INSERT INTO pf_assets
                (asset_code, asset_type, asset_name, purchase_value, current_value,
                 depreciation_rate, depreciation_method, currency, acquisition_date,
                 owner_user_id, status, notes, is_active, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'owned', ?, 1, datetime('now'), ?)
            """, (
                asset_code,
                data.get('asset_type', 'cash'),
                data.get('asset_name', ''),
                float(data.get('purchase_value', 0)),
                float(data.get('current_value', 0)),
                float(data.get('depreciation_rate', 0)),
                data.get('depreciation_method', 'straight_line'),
                data.get('currency', 'USD'),
                data.get('acquisition_date', ''),
                get_current_user_id(),
                data.get('notes', ''),
                get_current_user_id()
            ))
            db.commit()
        
        flash(f"Asset '{data.get('asset_name')}' created successfully.", "success")
        return redirect(url_for('finance.assets'))
    
    return render_template('finance/assets/create.html')


@finance_bp.route('/assets/<int:asset_id>/edit', methods=['GET', 'POST'])
@require_finance_permission('assets', 'edit')
def edit_asset(asset_id):
    """Edit asset."""
    asset = get_one("SELECT * FROM pf_assets WHERE id = ?", (asset_id,))
    if not asset:
        flash("Asset not found.", "error")
        return redirect(url_for('finance.assets'))
    
    if request.method == 'POST':
        data = request.form
        
        with get_db_context() as db:
            db.execute("""
                UPDATE pf_assets SET
                    asset_type = ?, asset_name = ?,
                    purchase_value = ?, current_value = ?,
                    depreciation_rate = ?, depreciation_method = ?,
                    currency = ?, acquisition_date = ?,
                    status = ?, notes = ?,
                    updated_at = datetime('now'), updated_by = ?
                WHERE id = ?
            """, (
                data.get('asset_type', 'cash'),
                data.get('asset_name', ''),
                float(data.get('purchase_value', 0)),
                float(data.get('current_value', 0)),
                float(data.get('depreciation_rate', 0)),
                data.get('depreciation_method', 'straight_line'),
                data.get('currency', 'USD'),
                data.get('acquisition_date', ''),
                data.get('status', 'owned'),
                data.get('notes', ''),
                get_current_user_id(),
                asset_id
            ))
            db.commit()
        
        flash("Asset updated successfully.", "success")
        return redirect(url_for('finance.assets'))
    
    return render_template('finance/assets/edit.html', asset=asset)


@finance_bp.route('/assets/<int:asset_id>/delete', methods=['POST'])
@require_finance_permission('assets', 'delete')
def delete_asset(asset_id):
    """Archive asset."""
    asset = get_one("SELECT * FROM pf_assets WHERE id = ?", (asset_id,))
    if not asset:
        return jsonify({'success': False, 'message': 'Asset not found'})
    
    with get_db_context() as db:
        db.execute("UPDATE pf_assets SET is_archived = 1, is_active = 0 WHERE id = ?", (asset_id,))
        db.commit()
    
    return jsonify({'success': True})


# =============================================================================
# SUBSCRIPTIONS ROUTES
# =============================================================================

@finance_bp.route('/subscriptions')
@require_finance_permission('subscriptions', 'view')
def subscriptions():
    """List all subscriptions."""
    user_id = get_current_user_id()
    
    subs = get_all("""
        SELECT s.*, c.category_name, a.account_name
        FROM pf_subscriptions s
        LEFT JOIN pf_category_definitions c ON s.category_id = c.id
        LEFT JOIN pf_accounts a ON s.account_id = a.id
        WHERE s.owner_user_id = ? AND s.is_archived = 0
        ORDER BY s.renewal_date
    """, (user_id,))
    
    total_monthly = sum(s['amount'] for s in subs if s['billing_cycle'] == 'monthly' and s['status'] == 'active')
    total_yearly = sum(s['amount'] * 12 for s in subs if s['billing_cycle'] == 'yearly' and s['status'] == 'active')
    
    return render_template('finance/subscriptions/index.html',
                          subscriptions=subs,
                          total_monthly=total_monthly,
                          total_yearly=total_yearly)


@finance_bp.route('/subscriptions/create', methods=['GET', 'POST'])
@require_finance_permission('subscriptions', 'create')
def create_subscription():
    """Create new subscription."""
    categories = get_categories('expense')
    accounts = get_accounts()
    
    if request.method == 'POST':
        data = request.form
        sub_number = generate_subscription_number()
        
        with get_db_context() as db:
            db.execute("""
                INSERT INTO pf_subscriptions
                (subscription_number, provider, service_type, plan_name, amount,
                 currency, billing_cycle, renewal_date, auto_renew, category_id,
                 account_id, reminder_days, owner_user_id, status, notes,
                 is_active, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?, 1, datetime('now'), ?)
            """, (
                sub_number,
                data.get('provider', ''),
                data.get('service_type', 'general'),
                data.get('plan_name', ''),
                float(data.get('amount', 0)),
                data.get('currency', 'USD'),
                data.get('billing_cycle', 'monthly'),
                data.get('renewal_date', ''),
                1 if data.get('auto_renew') else 0,
                data.get('category_id', 0),
                data.get('account_id', 0),
                int(data.get('reminder_days', 3)),
                get_current_user_id(),
                data.get('notes', ''),
                get_current_user_id()
            ))
            db.commit()
        
        flash(f"Subscription '{data.get('provider')}' created successfully.", "success")
        return redirect(url_for('finance.subscriptions'))
    
    return render_template('finance/subscriptions/create.html',
                          categories=categories,
                          accounts=accounts)


@finance_bp.route('/subscriptions/<int:sub_id>/edit', methods=['GET', 'POST'])
@require_finance_permission('subscriptions', 'edit')
def edit_subscription(sub_id):
    """Edit subscription."""
    sub = get_one("SELECT * FROM pf_subscriptions WHERE id = ?", (sub_id,))
    if not sub:
        flash("Subscription not found.", "error")
        return redirect(url_for('finance.subscriptions'))
    
    categories = get_categories('expense')
    accounts = get_accounts()
    
    if request.method == 'POST':
        data = request.form
        
        with get_db_context() as db:
            db.execute("""
                UPDATE pf_subscriptions SET
                    provider = ?, service_type = ?, plan_name = ?,
                    amount = ?, currency = ?, billing_cycle = ?,
                    renewal_date = ?, auto_renew = ?, category_id = ?,
                    account_id = ?, reminder_days = ?, status = ?, notes = ?,
                    updated_at = datetime('now'), updated_by = ?
                WHERE id = ?
            """, (
                data.get('provider', ''),
                data.get('service_type', 'general'),
                data.get('plan_name', ''),
                float(data.get('amount', 0)),
                data.get('currency', 'USD'),
                data.get('billing_cycle', 'monthly'),
                data.get('renewal_date', ''),
                1 if data.get('auto_renew') else 0,
                data.get('category_id', 0),
                data.get('account_id', 0),
                int(data.get('reminder_days', 3)),
                data.get('status', 'active'),
                data.get('notes', ''),
                get_current_user_id(),
                sub_id
            ))
            db.commit()
        
        flash("Subscription updated successfully.", "success")
        return redirect(url_for('finance.subscriptions'))
    
    return render_template('finance/subscriptions/edit.html',
                          sub=sub,
                          categories=categories,
                          accounts=accounts)


@finance_bp.route('/subscriptions/<int:sub_id>/cancel', methods=['POST'])
@require_finance_permission('subscriptions', 'edit')
def cancel_subscription(sub_id):
    """Cancel subscription."""
    sub = get_one("SELECT * FROM pf_subscriptions WHERE id = ?", (sub_id,))
    if not sub:
        return jsonify({'success': False, 'message': 'Subscription not found'})
    
    with get_db_context() as db:
        db.execute("""
            UPDATE pf_subscriptions 
            SET status = 'cancelled', cancelled_at = datetime('now'), updated_at = datetime('now')
            WHERE id = ?
        """, (sub_id,))
        db.commit()
    
    return jsonify({'success': True})


# =============================================================================
# CATEGORIES ROUTES
# =============================================================================

@finance_bp.route('/categories')
@require_finance_permission('categories', 'view')
def categories():
    """List all categories."""
    expense_cats = get_categories('expense')
    income_cats = get_categories('income')
    
    return render_template('finance/categories/index.html',
                          expense_categories=expense_cats,
                          income_categories=income_cats)


@finance_bp.route('/categories/create', methods=['GET', 'POST'])
@require_finance_permission('categories', 'create')
def create_category():
    """Create new category."""
    if request.method == 'POST':
        data = request.form
        cat_code = f"CAT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        with get_db_context() as db:
            db.execute("""
                INSERT INTO pf_category_definitions
                (category_code, category_name, category_type, parent_id, icon, color,
                 sort_order, is_active, created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, datetime('now'), ?)
            """, (
                cat_code,
                data.get('category_name', ''),
                data.get('category_type', 'expense'),
                data.get('parent_id', 0),
                data.get('icon', 'fa-folder'),
                data.get('color', '#6B7280'),
                int(data.get('sort_order', 0)),
                get_current_user_id()
            ))
            db.commit()
        
        flash(f"Category '{data.get('category_name')}' created successfully.", "success")
        return redirect(url_for('finance.categories'))
    
    parent_cats = get_categories(active_only=False)
    return render_template('finance/categories/create.html', parent_categories=parent_cats)


@finance_bp.route('/categories/<int:cat_id>/edit', methods=['GET', 'POST'])
@require_finance_permission('categories', 'edit')
def edit_category(cat_id):
    """Edit category."""
    cat = get_one("SELECT * FROM pf_category_definitions WHERE id = ?", (cat_id,))
    if not cat:
        flash("Category not found.", "error")
        return redirect(url_for('finance.categories'))
    
    if request.method == 'POST':
        data = request.form
        
        with get_db_context() as db:
            db.execute("""
                UPDATE pf_category_definitions SET
                    category_name = ?, parent_id = ?, icon = ?, color = ?,
                    sort_order = ?, is_active = ?,
                    updated_at = datetime('now'), updated_by = ?
                WHERE id = ?
            """, (
                data.get('category_name', ''),
                data.get('parent_id', 0),
                data.get('icon', 'fa-folder'),
                data.get('color', '#6B7280'),
                int(data.get('sort_order', 0)),
                1 if data.get('is_active') else 0,
                get_current_user_id(),
                cat_id
            ))
            db.commit()
        
        flash("Category updated successfully.", "success")
        return redirect(url_for('finance.categories'))
    
    parent_cats = get_categories(active_only=False)
    return render_template('finance/categories/edit.html', category=cat, parent_categories=parent_cats)


# =============================================================================
# ALERTS ROUTES
# =============================================================================

@finance_bp.route('/alerts')
@require_finance_permission('alerts', 'view')
def alerts():
    """List all alerts."""
    user_id = get_current_user_id()
    
    alerts_list = get_all("""
        SELECT * FROM pf_alerts
        WHERE owner_user_id = ? AND is_active = 1
        ORDER BY 
            CASE WHEN is_dismissed = 0 AND is_read = 0 THEN 0 ELSE 1 END,
            severity DESC,
            created_at DESC
    """, (user_id,))
    
    unread_count = len([a for a in alerts_list if not a['is_read'] and not a['is_dismissed']])
    
    return render_template('finance/alerts/index.html',
                          alerts=alerts_list,
                          unread_count=unread_count)


@finance_bp.route('/alerts/<int:alert_id>/read', methods=['POST'])
@require_finance_permission('alerts', 'edit')
def mark_alert_read(alert_id):
    """Mark alert as read."""
    with get_db_context() as db:
        db.execute("""
            UPDATE pf_alerts SET is_read = 1, read_at = datetime('now')
            WHERE id = ?
        """, (alert_id,))
        db.commit()
    return jsonify({'success': True})


@finance_bp.route('/alerts/<int:alert_id>/dismiss', methods=['POST'])
@require_finance_permission('alerts', 'edit')
def dismiss_alert(alert_id):
    """Dismiss alert."""
    with get_db_context() as db:
        db.execute("""
            UPDATE pf_alerts SET is_dismissed = 1, dismissed_at = datetime('now')
            WHERE id = ?
        """, (alert_id,))
        db.commit()
    return jsonify({'success': True})


@finance_bp.route('/alerts/dismiss-all', methods=['POST'])
@require_finance_permission('alerts', 'edit')
def dismiss_all_alerts():
    """Dismiss all alerts."""
    with get_db_context() as db:
        db.execute("""
            UPDATE pf_alerts SET is_dismissed = 1, dismissed_at = datetime('now')
            WHERE owner_user_id = ? AND is_dismissed = 0
        """, (get_current_user_id(),))
        db.commit()
    return jsonify({'success': True})


# =============================================================================
# REPORTS ROUTES
# =============================================================================

@finance_bp.route('/reports')
@require_finance_permission('reports', 'view')
def reports():
    """Finance reports overview."""
    return render_template('finance/reports/index.html')


@finance_bp.route('/reports/income')
@require_finance_permission('reports', 'view')
def report_income():
    """Income report."""
    user_id = get_current_user_id()
    date_from = request.args.get('date_from', datetime.now().replace(day=1).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
    
    records = get_all("""
        SELECT i.*, c.category_name, a.account_name
        FROM pf_income_records i
        LEFT JOIN pf_category_definitions c ON i.category_id = c.id
        LEFT JOIN pf_accounts a ON i.account_id = a.id
        WHERE i.owner_user_id = ? AND i.income_date >= ? AND i.income_date <= ?
        AND i.is_active = 1
        ORDER BY i.income_date DESC
    """, (user_id, date_from, date_to))
    
    total = sum(r['amount'] for r in records)
    
    by_category = get_all("""
        SELECT c.category_name, c.color, SUM(i.amount) as total
        FROM pf_income_records i
        LEFT JOIN pf_category_definitions c ON i.category_id = c.id
        WHERE i.owner_user_id = ? AND i.income_date >= ? AND i.income_date <= ?
        AND i.is_active = 1
        GROUP BY c.id
        ORDER BY total DESC
    """, (user_id, date_from, date_to))
    
    return render_template('finance/reports/income.html',
                          records=records,
                          total=total,
                          by_category=by_category,
                          date_from=date_from,
                          date_to=date_to)


@finance_bp.route('/reports/expenses')
@require_finance_permission('reports', 'view')
def report_expenses():
    """Expense report."""
    user_id = get_current_user_id()
    date_from = request.args.get('date_from', datetime.now().replace(day=1).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
    
    records = get_all("""
        SELECT e.*, c.category_name, c.color as category_color, c.icon as category_icon,
               a.account_name
        FROM pf_expense_records e
        LEFT JOIN pf_category_definitions c ON e.category_id = c.id
        LEFT JOIN pf_accounts a ON e.account_id = a.id
        WHERE e.owner_user_id = ? AND e.expense_date >= ? AND e.expense_date <= ?
        AND e.is_active = 1
        ORDER BY e.expense_date DESC
    """, (user_id, date_from, date_to))
    
    total = sum(r['amount'] for r in records)
    
    by_category = get_all("""
        SELECT c.category_name, c.color, c.icon, SUM(e.amount) as total, COUNT(*) as count
        FROM pf_expense_records e
        LEFT JOIN pf_category_definitions c ON e.category_id = c.id
        WHERE e.owner_user_id = ? AND e.expense_date >= ? AND e.expense_date <= ?
        AND e.is_active = 1
        GROUP BY c.id
        ORDER BY total DESC
    """, (user_id, date_from, date_to))
    
    by_merchant = get_all("""
        SELECT merchant_name, SUM(amount) as total, COUNT(*) as count
        FROM pf_expense_records
        WHERE owner_user_id = ? AND expense_date >= ? AND expense_date <= ?
        AND is_active = 1 AND merchant_name != ''
        GROUP BY merchant_name
        ORDER BY total DESC
        LIMIT 20
    """, (user_id, date_from, date_to))
    
    return render_template('finance/reports/expenses.html',
                          records=records,
                          total=total,
                          by_category=by_category,
                          by_merchant=by_merchant,
                          date_from=date_from,
                          date_to=date_to)


@finance_bp.route('/reports/budget')
@require_finance_permission('reports', 'view')
def report_budget():
    """Budget report."""
    user_id = get_current_user_id()
    
    budgets = get_all("""
        SELECT * FROM pf_budgets
        WHERE owner_user_id = ? AND is_active = 1
        ORDER BY created_at DESC
    """, (user_id,))
    
    budget_data = []
    for budget in budgets:
        status = get_budget_status(budget['id'])
        lines = get_all("""
            SELECT bl.*, c.category_name, c.color,
                   COALESCE(SUM(e.amount), 0) as spent
            FROM pf_budget_lines bl
            LEFT JOIN pf_category_definitions c ON bl.category_id = c.id
            LEFT JOIN pf_expense_records e ON e.category_id = bl.category_id
                AND e.expense_date >= ? AND e.expense_date <= ?
                AND e.is_active = 1 AND e.status = 'approved'
            WHERE bl.budget_id = ?
            GROUP BY bl.id
        """, (budget['period_start_date'], budget['period_end_date'], budget['id']))
        
        budget_dict = row_to_dict(budget)
        budget_dict.update(status)
        budget_dict['lines'] = [row_to_dict(l) for l in lines]
        budget_data.append(budget_dict)
    
    return render_template('finance/reports/budget.html', budgets=budget_data)


@finance_bp.route('/reports/net-worth')
@require_finance_permission('reports', 'view')
def report_net_worth():
    """Net worth report."""
    user_id = get_current_user_id()
    health = calculate_financial_health_score(user_id)
    
    # Assets breakdown
    assets = get_all("""
        SELECT asset_type, SUM(current_value) as total
        FROM pf_assets
        WHERE owner_user_id = ? AND is_active = 1
        GROUP BY asset_type
    """, (user_id,))
    
    # Investments breakdown
    investments = get_all("""
        SELECT asset_class, SUM(current_value) as total
        FROM pf_investments
        WHERE owner_user_id = ? AND is_active = 1 AND status = 'held'
        GROUP BY asset_class
    """, (user_id,))
    
    # Savings
    savings = get_all("""
        SELECT bucket_name, current_amount
        FROM pf_savings_buckets
        WHERE owner_user_id = ? AND is_active = 1
    """, (user_id,))
    
    # Debts
    debts = get_all("""
        SELECT debt_type, SUM(remaining_balance) as total
        FROM pf_debts
        WHERE owner_user_id = ? AND is_active = 1
        GROUP BY debt_type
    """, (user_id,))
    
    return render_template('finance/reports/net_worth.html',
                          health=health,
                          assets=assets,
                          investments=investments,
                          savings=savings,
                          debts=debts)


@finance_bp.route('/reports/cash-flow')
@require_finance_permission('reports', 'view')
def report_cash_flow():
    """Cash flow report."""
    user_id = get_current_user_id()
    date_from = request.args.get('date_from', datetime.now().replace(day=1).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
    
    # Daily inflow/outflow
    daily_flow = get_all("""
        SELECT 
            transaction_date,
            SUM(CASE WHEN transaction_type = 'income' THEN amount ELSE 0 END) as inflow,
            SUM(CASE WHEN transaction_type = 'expense' THEN amount ELSE 0 END) as outflow
        FROM pf_transactions
        WHERE owner_user_id = ? AND transaction_date >= ? AND transaction_date <= ?
        AND is_active = 1
        GROUP BY transaction_date
        ORDER BY transaction_date
    """, (user_id, date_from, date_to))
    
    total_inflow = sum(d['inflow'] for d in daily_flow)
    total_outflow = sum(d['outflow'] for d in daily_flow)
    
    return render_template('finance/reports/cash_flow.html',
                          daily_flow=daily_flow,
                          total_inflow=total_inflow,
                          total_outflow=total_outflow,
                          net_flow=total_inflow - total_outflow,
                          date_from=date_from,
                          date_to=date_to)


# =============================================================================
# CASH FLOW ROUTES
# =============================================================================

@finance_bp.route('/cash-flow')
@require_finance_permission('cash_flow', 'view')
def cash_flow():
    """Cash flow overview."""
    user_id = get_current_user_id()
    
    # Account balances
    accounts = get_all("""
        SELECT a.*, 
               COALESCE(SUM(CASE WHEN t.transaction_type = 'income' AND t.is_active = 1 THEN t.amount ELSE 0 END), 0) as total_inflow,
               COALESCE(SUM(CASE WHEN t.transaction_type = 'expense' AND t.is_active = 1 THEN t.amount ELSE 0 END), 0) as total_outflow
        FROM pf_accounts a
        LEFT JOIN pf_transactions t ON t.account_id = a.id
        WHERE a.owner_user_id = ? AND a.is_active = 1
        GROUP BY a.id
    """, (user_id,))
    
    total_balance = sum(a['current_balance'] for a in accounts)
    total_inflow = sum(a['total_inflow'] for a in accounts)
    total_outflow = sum(a['total_outflow'] for a in accounts)
    
    return render_template('finance/cashflow/index.html',
                          accounts=accounts,
                          total_balance=total_balance,
                          total_inflow=total_inflow,
                          total_outflow=total_outflow)


# =============================================================================
# CALENDAR ROUTES
# =============================================================================

@finance_bp.route('/calendar')
@require_finance_permission('calendar', 'view')
def calendar():
    """Finance calendar view."""
    user_id = get_current_user_id()
    month = request.args.get('month', datetime.now().month)
    year = request.args.get('year', datetime.now().year)
    
    start_date = f"{year}-{month:02d}-01"
    end_date = (datetime(int(year), int(month), 1) + timedelta(days=32)).replace(day=1).strftime('%Y-%m-%d')
    
    events = get_all("""
        SELECT * FROM pf_calendar_events
        WHERE owner_user_id = ? AND event_date >= ? AND event_date < ?
        AND is_active = 1
        ORDER BY event_date
    """, (user_id, start_date, end_date))
    
    # Get subscription renewals
    subs = get_all("""
        SELECT subscription_number as event_code, provider as title, 
               renewal_date as event_date, amount, currency, 'subscription' as event_type
        FROM pf_subscriptions
        WHERE owner_user_id = ? AND renewal_date >= ? AND renewal_date < ?
        AND is_active = 1 AND status = 'active'
    """, (user_id, start_date, end_date))
    
    # Get debt due dates
    debts = get_all("""
        SELECT debt_code as event_code, lender as title,
               next_due_date as event_date, monthly_installment as amount, 
               currency, 'debt' as event_type
        FROM pf_debts
        WHERE owner_user_id = ? AND next_due_date >= ? AND next_due_date < ?
        AND is_active = 1 AND status = 'active'
    """, (user_id, start_date, end_date))
    
    return render_template('finance/calendar/index.html',
                          events=events,
                          subscriptions=subs,
                          debts=debts,
                          month=int(month),
                          year=int(year))


# =============================================================================
# IMPORT / EXPORT ROUTES
# =============================================================================

@finance_bp.route('/export/<export_type>')
@require_finance_permission('export', 'view')
def export_data(export_type):
    """Export finance data."""
    user_id = get_current_user_id()
    
    # Get columns from request
    columns = request.args.getlist('columns')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    if export_type == 'transactions':
        query = """
            SELECT t.transaction_code, t.transaction_date, t.transaction_type,
                   t.amount, t.currency, t.merchant_payee, t.description,
                   c.category_name, a.account_name, t.status, t.tags, t.notes
            FROM pf_transactions t
            LEFT JOIN pf_category_definitions c ON t.category_id = c.id
            LEFT JOIN pf_accounts a ON t.account_id = a.id
            WHERE t.owner_user_id = ? AND t.is_active = 1
        """
        params = [user_id]
        
        if date_from:
            query += " AND t.transaction_date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND t.transaction_date <= ?"
            params.append(date_to)
        
        query += " ORDER BY t.transaction_date DESC"
        
        rows = get_all(query, tuple(params))
        data = [row_to_dict(row) for row in rows]
        
        columns_options = [
            ('transaction_code', 'Transaction Code'),
            ('transaction_date', 'Date'),
            ('transaction_type', 'Type'),
            ('amount', 'Amount'),
            ('currency', 'Currency'),
            ('merchant_payee', 'Merchant/Payee'),
            ('description', 'Description'),
            ('category_name', 'Category'),
            ('account_name', 'Account'),
            ('status', 'Status'),
            ('tags', 'Tags'),
            ('notes', 'Notes')
        ]
        
    elif export_type == 'income':
        query = """
            SELECT i.income_number, i.income_date, i.income_type, i.source_name,
                   i.amount, i.currency, c.category_name, a.account_name,
                   i.status, i.notes
            FROM pf_income_records i
            LEFT JOIN pf_category_definitions c ON i.category_id = c.id
            LEFT JOIN pf_accounts a ON i.account_id = a.id
            WHERE i.owner_user_id = ? AND i.is_active = 1
        """
        params = [user_id]
        
        if date_from:
            query += " AND i.income_date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND i.income_date <= ?"
            params.append(date_to)
        
        rows = get_all(query + " ORDER BY i.income_date DESC", tuple(params))
        data = [row_to_dict(row) for row in rows]
        
        columns_options = [
            ('income_number', 'Income Number'),
            ('income_date', 'Date'),
            ('income_type', 'Type'),
            ('source_name', 'Source'),
            ('amount', 'Amount'),
            ('currency', 'Currency'),
            ('category_name', 'Category'),
            ('account_name', 'Account'),
            ('status', 'Status'),
            ('notes', 'Notes')
        ]
        
    elif export_type == 'expenses':
        query = """
            SELECT e.expense_number, e.expense_date, e.merchant_name,
                   e.amount, e.currency, c.category_name, a.account_name,
                   e.payment_method, e.status, e.tags, e.notes
            FROM pf_expense_records e
            LEFT JOIN pf_category_definitions c ON e.category_id = c.id
            LEFT JOIN pf_accounts a ON e.account_id = a.id
            WHERE e.owner_user_id = ? AND e.is_active = 1
        """
        params = [user_id]
        
        if date_from:
            query += " AND e.expense_date >= ?"
            params.append(date_from)
        if date_to:
            query += " AND e.expense_date <= ?"
            params.append(date_to)
        
        rows = get_all(query + " ORDER BY e.expense_date DESC", tuple(params))
        data = [row_to_dict(row) for row in rows]
        
        columns_options = [
            ('expense_number', 'Expense Number'),
            ('expense_date', 'Date'),
            ('merchant_name', 'Merchant'),
            ('amount', 'Amount'),
            ('currency', 'Currency'),
            ('category_name', 'Category'),
            ('account_name', 'Account'),
            ('payment_method', 'Payment Method'),
            ('status', 'Status'),
            ('tags', 'Tags'),
            ('notes', 'Notes')
        ]
        
    elif export_type == 'budgets':
        rows = get_all("""
            SELECT b.budget_code, b.budget_name, b.budget_type, b.total_budget,
                   b.currency, b.period_start_date, b.period_end_date,
                   b.warning_threshold, b.status, b.notes
            FROM pf_budgets b
            WHERE b.owner_user_id = ? AND b.is_active = 1
            ORDER BY b.created_at DESC
        """, (user_id,))
        data = [row_to_dict(row) for row in rows]
        
        columns_options = [
            ('budget_code', 'Budget Code'),
            ('budget_name', 'Name'),
            ('budget_type', 'Type'),
            ('total_budget', 'Total Budget'),
            ('currency', 'Currency'),
            ('period_start_date', 'Start Date'),
            ('period_end_date', 'End Date'),
            ('warning_threshold', 'Warning Threshold %'),
            ('status', 'Status'),
            ('notes', 'Notes')
        ]
        
    else:
        data = []
        columns_options = []
    
    format_type = request.args.get('format', 'csv')
    
    if format_type == 'csv':
        return send_export_response(data, 'finance_export.csv', 'csv', columns_options)
    elif format_type == 'excel_text':
        return send_export_response(data, 'finance_export.xlsx', 'excel_text', columns_options)
    elif format_type == 'excel_general':
        return send_export_response(data, 'finance_export.xlsx', 'excel_general', columns_options)
    elif format_type == 'json':
        return send_export_response(data, 'finance_export.json', 'json', columns_options)
    else:
        return send_export_response(data, 'finance_export.csv', 'csv', columns_options)


# =============================================================================
# SETTINGS ROUTES
# =============================================================================

@finance_bp.route('/settings')
@require_finance_permission('settings', 'view')
def settings():
    """Finance settings."""
    settings_list = get_all("""
        SELECT * FROM pf_settings WHERE is_active = 1
        ORDER BY category, setting_key
    """)
    
    return render_template('finance/settings/index.html', settings=settings_list)


@finance_bp.route('/settings/update', methods=['POST'])
@require_finance_permission('settings', 'edit')
def update_settings():
    """Update finance settings."""
    data = request.form
    
    for key, value in data.items():
        if key.startswith('setting_'):
            setting_key = key.replace('setting_', '')
            with get_db_context() as db:
                db.execute("""
                    INSERT INTO pf_settings (setting_key, setting_value, updated_at)
                    VALUES (?, ?, datetime('now'))
                    ON CONFLICT(setting_key) DO UPDATE SET
                        setting_value = excluded.setting_value,
                        updated_at = datetime('now')
                """, (setting_key, value))
                db.commit()
    
    flash("Settings updated successfully.", "success")
    return redirect(url_for('finance.settings'))


# =============================================================================
# ANALYSIS / INSIGHTS ROUTES
# =============================================================================

@finance_bp.route('/analysis')
@require_finance_permission('analysis', 'view')
def analysis():
    """Smart analysis and insights."""
    user_id = get_current_user_id()
    health = calculate_financial_health_score(user_id)
    
    # Get top expense categories
    top_categories = get_all("""
        SELECT c.category_name, c.color, SUM(e.amount) as total
        FROM pf_expense_records e
        INNER JOIN pf_category_definitions c ON e.category_id = c.id
        WHERE e.owner_user_id = ? AND e.expense_date >= ?
        AND e.is_active = 1
        GROUP BY c.id
        ORDER BY total DESC
        LIMIT 5
    """, (user_id, datetime.now().replace(day=1).strftime('%Y-%m-%d')))
    
    # Unusual expenses (flagged)
    unusual = get_all("""
        SELECT * FROM pf_expense_records
        WHERE owner_user_id = ? AND is_flagged = 1 AND is_active = 1
        ORDER BY expense_date DESC
        LIMIT 10
    """, (user_id,))
    
    # Savings suggestions
    monthly_expenses = health.get('total_expenses', 0)
    suggested_savings = monthly_expenses * 0.2  # 20% rule
    
    insights = []
    
    if health['expense_to_income_ratio'] > 80:
        insights.append({
            'type': 'warning',
            'title': 'High Expense Ratio',
            'message': f'Your expenses are {health["expense_to_income_ratio"]:.1f}% of income. Consider reducing discretionary spending.'
        })
    
    if health['savings_rate'] < 10:
        insights.append({
            'type': 'info',
            'title': 'Low Savings Rate',
            'message': f'Your savings rate is {health["savings_rate"]:.1f}%. Aim for at least 20% of income.'
        })
    
    if health['debt_to_income_ratio'] > 3:
        insights.append({
            'type': 'danger',
            'title': 'High Debt Burden',
            'message': f'Your debt-to-income ratio is {health["debt_to_income_ratio"]:.1f}. Focus on debt reduction.'
        })
    
    if len(unusual) > 0:
        insights.append({
            'type': 'warning',
            'title': 'Unusual Transactions Detected',
            'message': f'You have {len(unusual)} flagged transactions that may need review.'
        })
    
    return render_template('finance/analysis/index.html',
                          health=health,
                          top_categories=top_categories,
                          unusual=unusual,
                          suggested_savings=suggested_savings,
                          insights=insights)


# =============================================================================
# DOCUMENTS ROUTES
# =============================================================================

@finance_bp.route('/documents')
@require_finance_permission('documents', 'view')
def documents():
    """Finance documents."""
    user_id = get_current_user_id()
    
    documents_list = get_all("""
        SELECT rdl.*, 
               CASE rdl.entity_type 
                   WHEN 'expense' THEN e.expense_number
                   WHEN 'income' THEN i.income_number
                   WHEN 'asset' THEN a.asset_code
                   ELSE rdl.entity_type
               END as entity_reference
        FROM pf_receipts_documents_links rdl
        LEFT JOIN pf_expense_records e ON rdl.entity_type = 'expense' AND rdl.entity_id = e.id
        LEFT JOIN pf_income_records i ON rdl.entity_type = 'income' AND rdl.entity_id = i.id
        LEFT JOIN pf_assets a ON rdl.entity_type = 'asset' AND rdl.entity_id = a.id
        WHERE rdl.created_by = ?
        ORDER BY rdl.created_at DESC
    """, (user_id,))
    
    return render_template('finance/documents/index.html', documents=documents_list)


# =============================================================================
# AUTOMATION RULES ROUTES
# =============================================================================

@finance_bp.route('/automation')
@require_finance_permission('automation', 'view')
def automation():
    """Automation rules."""
    user_id = get_current_user_id()
    
    rules = get_all("""
        SELECT * FROM pf_automation_rules
        WHERE owner_user_id = ? AND is_active = 1
        ORDER BY priority, rule_name
    """, (user_id,))
    
    return render_template('finance/automation/index.html', rules=rules)


@finance_bp.route('/automation/create', methods=['GET', 'POST'])
@require_finance_permission('automation', 'create')
def create_automation_rule():
    """Create automation rule."""
    if request.method == 'POST':
        data = request.form
        rule_code = f"RULE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        condition = {
            'type': data.get('condition_type', ''),
            'field': data.get('condition_field', ''),
            'operator': data.get('condition_operator', ''),
            'value': data.get('condition_value', '')
        }
        
        action = {
            'type': data.get('action_type', ''),
            'category_id': data.get('action_category_id', 0),
            'add_tag': data.get('action_add_tag', ''),
            'create_alert': data.get('action_create_alert', False)
        }
        
        with get_db_context() as db:
            db.execute("""
                INSERT INTO pf_automation_rules
                (rule_code, rule_name, rule_type, condition_json, action_json,
                 priority, is_enabled, owner_user_id, status, is_active,
                 created_at, created_by)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, 'active', 1, datetime('now'), ?)
            """, (
                rule_code,
                data.get('rule_name', ''),
                data.get('rule_type', 'auto_categorize'),
                json.dumps(condition),
                json.dumps(action),
                int(data.get('priority', 5)),
                get_current_user_id(),
                get_current_user_id()
            ))
            db.commit()
        
        flash(f"Automation rule '{data.get('rule_name')}' created successfully.", "success")
        return redirect(url_for('finance.automation'))
    
    categories = get_categories()
    return render_template('finance/automation/create.html', categories=categories)


# =============================================================================
# MULTI-CURRENCY ROUTES
# =============================================================================

@finance_bp.route('/currencies')
@require_finance_permission('currencies', 'view')
def currencies():
    """Currency rates management."""
    rates = get_all("""
        SELECT * FROM pf_currency_rates
        WHERE is_active = 1
        ORDER BY from_currency, to_currency
    """)
    
    return render_template('finance/currencies/index.html', rates=rates)


@finance_bp.route('/currencies/add-rate', methods=['POST'])
@require_finance_permission('currencies', 'create')
def add_currency_rate():
    """Add currency rate."""
    data = request.form
    
    with get_db_context() as db:
        db.execute("""
            INSERT INTO pf_currency_rates
            (from_currency, to_currency, rate, rate_date, source, is_active, created_at)
            VALUES (?, ?, ?, ?, 'manual', 1, datetime('now'))
        """, (
            data.get('from_currency', ''),
            data.get('to_currency', ''),
            float(data.get('rate', 1)),
            data.get('rate_date', datetime.now().strftime('%Y-%m-%d'))
        ))
        db.commit()
    
    flash("Currency rate added successfully.", "success")
    return redirect(url_for('finance.currencies'))


# =============================================================================
# FAMILY / MULTI-USER ROUTES
# =============================================================================

@finance_bp.route('/family')
@require_finance_permission('family', 'view')
def family():
    """Family profiles."""
    user_id = get_current_user_id()
    
    profiles = get_all("""
        SELECT fp.*, u.username as primary_user_name
        FROM pf_family_profiles fp
        LEFT JOIN users u ON fp.primary_user_id = u.id
        WHERE fp.primary_user_id = ? OR fp.is_active = 1
    """, (user_id,))
    
    return render_template('finance/family/index.html', profiles=profiles)


# =============================================================================
# API ENDPOINTS FOR AJAX
# =============================================================================

@finance_bp.route('/api/kpis')
def api_kpis():
    """API endpoint for KPI data."""
    user_id = get_current_user_id()
    kpis = calculate_kpis(user_id)
    return jsonify(kpis)


@finance_bp.route('/api/health-score')
def api_health_score():
    """API endpoint for health score."""
    user_id = get_current_user_id()
    health = calculate_financial_health_score(user_id)
    return jsonify(health)


@finance_bp.route('/api/category-spending')
def api_category_spending():
    """API endpoint for category spending."""
    user_id = get_current_user_id()
    month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    
    spending = get_all("""
        SELECT c.category_name, c.color, c.icon, SUM(e.amount) as total
        FROM pf_expense_records e
        INNER JOIN pf_category_definitions c ON e.category_id = c.id
        WHERE e.owner_user_id = ? AND e.expense_date >= ?
        AND e.is_active = 1 AND e.status = 'approved'
        GROUP BY c.id
        ORDER BY total DESC
        LIMIT 10
    """, (user_id, month_start))
    
    return jsonify([row_to_dict(row) for row in spending])


# =============================================================================
# REGISTER ROUTES
# =============================================================================

def register_finance_routes(app):
    """Register finance routes with the app."""
    app.register_blueprint(finance_bp)
