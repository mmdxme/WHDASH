"""
Finance Module Enhancements - Phase 1
=====================================
Additional routes and models to complete the enterprise finance module.

This file extends the existing finance_models.py and finance_routes.py
with missing functionality for:
- Cash Management / Treasury
- Bank Reconciliation
- Financial Close Management
- Profit Centers
- Journal Templates & Batches
- Recurring Journals
- Intercompany Accounting
- Tax Rules Engine
- Approval Workflow Integration
- Flow Integration
- Financial Audit Trail

Author: Finance Module Enhancement
"""

from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from functools import wraps
import math
from datetime import datetime, timedelta

from database import get_db_context, get_one, get_all, row_to_dict, rows_to_list

# Import helper functions from finance_routes
from finance_routes import get_company_id, get_current_user_id

# Import finance model functions from finance_models
from finance_models import (
    get_accounts, get_account_by_id, get_account_balance, get_account_ledger,
    get_fiscal_years, get_fiscal_year_by_id, get_fiscal_periods,
    get_fiscal_period_by_id, get_fiscal_period_by_date,
    is_period_open, close_period as model_close_period, reopen_period,
    get_journals, get_journal_by_id, create_journal, post_journal,
    get_bank_accounts, get_bank_account_by_id, create_bank_account,
    get_cash_transfers, get_cash_transfer_by_id, create_cash_transfer,
    get_customer_invoices, get_customer_invoice_by_id,
    get_supplier_bills, get_supplier_bill_by_id,
    get_cost_centers, get_cost_center_by_id,
    get_tax_codes, get_tax_code_by_id,
    get_budgets, get_budget_by_id,
    get_assets, get_asset_by_id,
    get_ar_aging, get_ap_aging,
    get_trial_balance, get_financial_summary,
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
# FINANCE ENHANCEMENTS BLUEPRINT
# ============================================================================

finance_bp = Blueprint('finance_enhance', __name__, url_prefix='/finance')


# ============================================================================
# CASH MANAGEMENT / TREASURY ROUTES
# ============================================================================

@finance_bp.route('/bank-accounts')
@require_permission('finance', 'bank_accounts', 'view')
def bank_accounts_list():
    """List all bank accounts."""
    company_id = get_company_id()
    bank_accounts = get_bank_accounts(company_id=company_id, is_active=True)
    
    return render_template('finance/bank_accounts/list.html',
        title='Bank Accounts',
        bank_accounts=bank_accounts
    )


@finance_bp.route('/bank-accounts/create', methods=['GET', 'POST'])
@require_permission('finance', 'bank_accounts', 'create')
def bank_accounts_create():
    """Create new bank account."""
    company_id = get_company_id()
    
    if request.method == 'POST':
        data = {
            'bank_name': request.form.get('bank_name'),
            'account_name': request.form.get('account_name'),
            'account_number': request.form.get('account_number'),
            'account_type': request.form.get('account_type', 'checking'),
            'currency': request.form.get('currency', 'AED'),
            'iban': request.form.get('iban'),
            'swift_code': request.form.get('swift_code'),
            'branch': request.form.get('branch'),
            'address': request.form.get('address'),
            'gl_account_id': request.form.get('gl_account_id', type=int) or None,
            'current_balance': request.form.get('current_balance', 0, type=float),
            'opening_balance': request.form.get('opening_balance', 0, type=float),
            'bank_statement_format': request.form.get('bank_statement_format'),
            'is_active': 1,
            'company_id': company_id,
        }
        
        try:
            account_id = create_bank_account(data)
            flash('Bank account created successfully!', 'success')
            return redirect(url_for('finance_enhance.bank_accounts_view', account_id=account_id))
        except Exception as e:
            flash(f'Error creating bank account: {str(e)}', 'error')
    
    accounts = get_accounts(company_id=company_id, active_only=True)
    return render_template('finance/bank_accounts/create.html',
        title='Create Bank Account',
        accounts=accounts
    )


@finance_bp.route('/bank-accounts/<int:account_id>')
@require_permission('finance', 'bank_accounts', 'view')
def bank_accounts_view(account_id):
    """View bank account details."""
    bank = get_bank_account_by_id(account_id)
    if not bank:
        flash('Bank account not found', 'error')
        return redirect(url_for('finance_enhance.bank_accounts_list'))
    
    # Get recent transactions
    from finance_models import get_all as db_get_all
    recent_txns = db_get_all("""
        SELECT * FROM finance_cash_transfers 
        WHERE from_bank_account_id = ? OR to_bank_account_id = ?
        ORDER BY created_at DESC LIMIT 10
    """, (account_id, account_id))
    
    return render_template('finance/bank_accounts/view.html',
        title=f'Bank Account: {bank.get("account_name")}',
        bank=bank,
        recent_transactions=recent_txns
    )


@finance_bp.route('/bank-accounts/<int:account_id>/edit', methods=['GET', 'POST'])
@require_permission('finance', 'bank_accounts', 'edit')
def bank_accounts_edit(account_id):
    """Edit bank account."""
    bank = get_bank_account_by_id(account_id)
    if not bank:
        flash('Bank account not found', 'error')
        return redirect(url_for('finance_enhance.bank_accounts_list'))
    
    if request.method == 'POST':
        data = {
            'bank_name': request.form.get('bank_name'),
            'account_name': request.form.get('account_name'),
            'account_number': request.form.get('account_number'),
            'account_type': request.form.get('account_type'),
            'currency': request.form.get('currency'),
            'iban': request.form.get('iban'),
            'swift_code': request.form.get('swift_code'),
            'branch': request.form.get('branch'),
            'address': request.form.get('address'),
            'gl_account_id': request.form.get('gl_account_id', type=int) or None,
            'bank_statement_format': request.form.get('bank_statement_format'),
            'is_active': 1 if request.form.get('is_active') == '1' else 0,
        }
        
        try:
            from finance_models import update_bank_account as update_bank
            update_bank(account_id, data)
            flash('Bank account updated successfully!', 'success')
            return redirect(url_for('finance_enhance.bank_accounts_view', account_id=account_id))
        except Exception as e:
            flash(f'Error updating bank account: {str(e)}', 'error')
    
    accounts = get_accounts(company_id=get_company_id(), active_only=True)
    return render_template('finance/bank_accounts/edit.html',
        title=f'Edit Bank Account: {bank.get("account_name")}',
        bank=bank,
        accounts=accounts
    )


@finance_bp.route('/treasury/cash-position')
@require_permission('finance', 'treasury', 'view')
def treasury_cash_position():
    """Cash position overview across all bank accounts."""
    company_id = get_company_id()
    
    bank_accounts = get_bank_accounts(company_id=company_id, is_active=True)
    
    # Calculate totals by currency
    total_by_currency = {}
    total_cash = 0
    
    for ba in bank_accounts:
        currency = ba.get('currency', 'AED')
        balance = ba.get('current_balance', 0) or 0
        
        if currency not in total_by_currency:
            total_by_currency[currency] = {'total': 0, 'accounts': []}
        
        total_by_currency[currency]['total'] += balance
        total_by_currency[currency]['accounts'].append({
            'id': ba['id'],
            'bank_name': ba['bank_name'],
            'name': ba['account_name'],
            'account_type': ba['account_type'],
            'balance': balance
        })
        total_cash += balance
    
    return render_template('finance/treasury/cash_position.html',
        title='Cash Position',
        total_cash=total_cash,
        total_by_currency=total_by_currency
    )


@finance_bp.route('/treasury/cash-flow-forecast')
@require_permission('finance', 'treasury', 'view')
def treasury_cash_flow_forecast():
    """Cash flow forecast view."""
    company_id = get_company_id()
    
    # Get open invoices and bills for cash flow prediction
    open_ar = get_customer_invoices(company_id=company_id, status='Posted')
    open_ap = get_supplier_bills(company_id=company_id, status='Posted')
    
    # Calculate expected inflows and outflows by week
    today = datetime.now().date()
    weeks = []
    
    for week in range(1, 9):
        week_start = today + timedelta(days=(week-1)*7)
        week_end = week_start + timedelta(days=7)
        
        ar_expected = sum(
            float(inv.get('total_amount', 0) or 0)
            for inv in open_ar
            if inv.get('due_date') and today <= datetime.strptime(inv['due_date'], '%Y-%m-%d').date() <= week_end
        )
        
        ap_expected = sum(
            float(bill.get('total_amount', 0) or 0)
            for bill in open_ap
            if bill.get('due_date') and today <= datetime.strptime(bill['due_date'], '%Y-%m-%d').date() <= week_end
        )
        
        weeks.append({
            'week': f'Week {week}',
            'start': week_start.strftime('%Y-%m-%d'),
            'end': week_end.strftime('%Y-%m-%d'),
            'ar_expected': ar_expected,
            'ap_expected': ap_expected,
            'net': ar_expected - ap_expected
        })
    
    return render_template('finance/treasury/cash_flow_forecast.html',
        title='Cash Flow Forecast',
        weeks=weeks
    )


@finance_bp.route('/transfers')
@require_permission('finance', 'transfers', 'view')
def transfers_list():
    """List cash transfers."""
    company_id = get_company_id()
    
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    transfers = get_cash_transfers(
        company_id=company_id,
        start_date=start_date,
        end_date=end_date,
        status=status
    )
    
    return render_template('finance/transfers/list.html',
        title='Cash Transfers',
        transfers=transfers,
        filters={'status': status, 'start_date': start_date, 'end_date': end_date}
    )


@finance_bp.route('/transfers/create', methods=['GET', 'POST'])
@require_permission('finance', 'transfers', 'create')
def transfers_create():
    """Create cash transfer between accounts."""
    company_id = get_company_id()
    user_id = get_current_user_id()
    
    if request.method == 'POST':
        data = {
            'transfer_date': request.form.get('transfer_date'),
            'from_bank_account_id': request.form.get('from_bank_account_id', type=int),
            'to_bank_account_id': request.form.get('to_bank_account_id', type=int),
            'amount': request.form.get('amount', 0, type=float),
            'currency': request.form.get('currency', 'AED'),
            'reference': request.form.get('reference'),
            'notes': request.form.get('notes'),
            'company_id': company_id,
            'created_by': user_id,
        }
        
        try:
            transfer_id = create_cash_transfer(data)
            flash('Cash transfer created successfully!', 'success')
            return redirect(url_for('finance_enhance.transfers_view', transfer_id=transfer_id))
        except Exception as e:
            flash(f'Error creating transfer: {str(e)}', 'error')
    
    bank_accounts = get_bank_accounts(company_id=company_id, is_active=True)
    return render_template('finance/transfers/create.html',
        title='Create Cash Transfer',
        bank_accounts=bank_accounts
    )


@finance_bp.route('/transfers/<int:transfer_id>')
@require_permission('finance', 'transfers', 'view')
def transfers_view(transfer_id):
    """View transfer details."""
    transfer = get_cash_transfer_by_id(transfer_id)
    if not transfer:
        flash('Transfer not found', 'error')
        return redirect(url_for('finance_enhance.transfers_list'))
    
    return render_template('finance/transfers/view.html',
        title=f'Transfer: {transfer.get("transfer_number")}',
        transfer=transfer
    )


# ============================================================================
# RECONCILIATION CENTER ROUTES
# ============================================================================

@finance_bp.route('/reconciliation')
@require_permission('finance', 'reconciliation', 'view')
def reconciliation_center():
    """Main reconciliation center dashboard."""
    company_id = get_company_id()
    
    from finance_models import get_all as db_get_all
    
    # Get reconciliation sets by type
    bank_sets = db_get_all("""
        SELECT rs.*, fb.account_name as bank_account_name,
               (SELECT COUNT(*) FROM finance_bank_reconciliation_items WHERE statement_id = rs.id) as total_items,
               (SELECT COUNT(*) FROM finance_bank_reconciliation_matches WHERE statement_id = rs.id) as matched_items
        FROM finance_bank_reconciliation_statements rs
        LEFT JOIN finance_bank_accounts fb ON rs.bank_account_id = fb.id
        WHERE rs.company_id = ?
        ORDER BY rs.created_at DESC LIMIT 10
    """, (company_id,))
    
    gl_sets = db_get_all("""
        SELECT * FROM finance_gl_reconciliation_sets
        WHERE company_id = ?
        ORDER BY created_at DESC LIMIT 10
    """, (company_id,))
    
    ar_sets = db_get_all("""
        SELECT * FROM finance_ar_reconciliation_sets
        WHERE company_id = ?
        ORDER BY created_at DESC LIMIT 10
    """, (company_id,))
    
    ap_sets = db_get_all("""
        SELECT * FROM finance_ap_reconciliation_sets
        WHERE company_id = ?
        ORDER BY created_at DESC LIMIT 10
    """, (company_id,))
    
    return render_template('finance/reconciliation/center.html',
        title='Reconciliation Center',
        bank_sets=bank_sets or [],
        gl_sets=gl_sets or [],
        ar_sets=ar_sets or [],
        ap_sets=ap_sets or []
    )


@finance_bp.route('/reconciliation/create', methods=['GET', 'POST'])
@require_permission('finance', 'reconciliation', 'create')
def reconciliation_create():
    """Start a new reconciliation."""
    company_id = get_company_id()
    recon_type = request.args.get('type', 'bank')
    
    if request.method == 'POST':
        data = {
            'recon_type': request.form.get('recon_type'),
            'reference_date': request.form.get('reference_date'),
            'bank_account_id': request.form.get('bank_account_id', type=int) or None,
            'company_id': company_id,
        }
        
        try:
            from finance_models import create_reconciliation_set
            set_id = create_reconciliation_set(data)
            flash('Reconciliation set created!', 'success')
            return redirect(url_for('finance_enhance.reconciliation_view', set_id=set_id))
        except Exception as e:
            flash(f'Error: {str(e)}', 'error')
    
    bank_accounts = get_bank_accounts(company_id=company_id, is_active=True)
    return render_template('finance/reconciliation/create.html',
        title='Start Reconciliation',
        bank_accounts=bank_accounts,
        recon_type=recon_type
    )


@finance_bp.route('/reconciliation/<int:set_id>')
@require_permission('finance', 'reconciliation', 'view')
def reconciliation_view(set_id):
    """View reconciliation set details."""
    from finance_models import get_one, get_all
    
    recon_set = get_one("""
        SELECT rs.*, fb.account_name as bank_account_name
        FROM finance_bank_reconciliation_statements rs
        LEFT JOIN finance_bank_accounts fb ON rs.bank_account_id = fb.id
        WHERE rs.id = ?
    """, (set_id,))
    
    if not recon_set:
        flash('Reconciliation set not found', 'error')
        return redirect(url_for('finance_enhance.reconciliation_center'))
    
    items = get_all("""
        SELECT * FROM finance_bank_reconciliation_items
        WHERE statement_id = ?
        ORDER BY line_number
    """, (set_id,))
    
    return render_template('finance/reconciliation/view.html',
        title=f'Reconciliation: {recon_set.get("statement_number", set_id)}',
        recon_set=recon_set,
        items=items or []
    )


# ============================================================================
# FINANCIAL CLOSE MANAGEMENT ROUTES
# ============================================================================

@finance_bp.route('/close')
@require_permission('finance', 'close', 'view')
def close_status():
    """Financial close status overview."""
    company_id = get_company_id()
    
    from finance_models import get_all as db_get_all
    
    # Get all periods with their close status
    period_summary = db_get_all("""
        SELECT 
            fp.id,
            fp.name,
            fp.period_number,
            fp.start_date,
            fp.end_date,
            fp.status,
            fy.name as fiscal_year_name,
            fy.id as fiscal_year_id,
            (SELECT COUNT(*) FROM finance_close_tasks WHERE period_id = fp.id) as total_items,
            (SELECT COUNT(*) FROM finance_close_tasks WHERE period_id = fp.id AND status = 'Completed') as completed_items
        FROM finance_fiscal_periods fp
        LEFT JOIN finance_fiscal_years fy ON fp.fiscal_year_id = fy.id
        WHERE fp.company_id = ? OR fp.company_id IS NULL
        ORDER BY fy.start_date DESC, fp.period_number DESC
    """, (company_id,))
    
    return render_template('finance/close/status.html',
        title='Financial Close Status',
        period_summary=period_summary or []
    )


@finance_bp.route('/close/period/<int:period_id>')
@require_permission('finance', 'close', 'manage')
def close_period_view(period_id):
    """Manage close tasks for a specific period."""
    company_id = get_company_id()
    
    from finance_models import get_one, get_all
    
    period = get_one("""
        SELECT fp.*, fy.name as fiscal_year_name
        FROM finance_fiscal_periods fp
        LEFT JOIN finance_fiscal_years fy ON fp.fiscal_year_id = fy.id
        WHERE fp.id = ?
    """, (period_id,))
    
    if not period:
        flash('Period not found', 'error')
        return redirect(url_for('finance_enhance.close_status'))
    
    tasks = get_all("""
        SELECT ct.*, u.username as assigned_to_name
        FROM finance_close_tasks ct
        LEFT JOIN users u ON ct.assigned_to = u.id
        WHERE ct.period_id = ?
        ORDER BY ct.due_date, ct.id
    """, (period_id,))
    
    return render_template('finance/close/period.html',
        title=f'Close: {period.get("name")}',
        period=period,
        tasks=tasks or []
    )


@finance_bp.route('/close/period/<int:period_id>/task/<int:task_id>/complete', methods=['POST'])
@require_permission('finance', 'close', 'edit')
def close_task_complete(period_id, task_id):
    """Mark a close task as complete."""
    user_id = get_current_user_id()
    
    from finance_models import get_db_context
    with get_db_context() as db:
        db.execute("""
            UPDATE finance_close_tasks 
            SET status = 'Completed', completed_by = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, task_id))
        db.commit()
    
    flash('Task marked as complete!', 'success')
    return redirect(url_for('finance_enhance.close_period_view', period_id=period_id))


@finance_bp.route('/close/period/<int:period_id>/close', methods=['POST'])
@require_permission('finance', 'close', 'close')
def close_period_action(period_id):
    """Close a fiscal period."""
    try:
        model_close_period(period_id)
        flash('Period closed successfully!', 'success')
    except Exception as e:
        flash(f'Error closing period: {str(e)}', 'error')
    
    return redirect(url_for('finance_enhance.close_status'))


@finance_bp.route('/close/period/<int:period_id>/reopen', methods=['POST'])
@require_permission('finance', 'close', 'reopen')
def reopen_period_action(period_id):
    """Reopen a closed fiscal period."""
    try:
        reopen_period(period_id)
        flash('Period reopened!', 'success')
    except Exception as e:
        flash(f'Error reopening period: {str(e)}', 'error')
    
    return redirect(url_for('finance_enhance.close_status'))


# ============================================================================
# PROFIT CENTERS ROUTES
# ============================================================================

@finance_bp.route('/profit-centers')
@require_permission('finance', 'profit_centers', 'view')
def profit_centers_list():
    """List profit centers."""
    company_id = get_company_id()
    
    from finance_models import get_all as db_get_all
    profit_centers = db_get_all("""
        SELECT pc.*, 
               (SELECT name FROM finance_cost_centers WHERE id = pc.parent_id) as parent_name,
               (SELECT COUNT(*) FROM finance_cost_centers WHERE parent_id = pc.id) as child_count
        FROM finance_profit_centers pc
        WHERE pc.company_id = ? OR pc.company_id IS NULL
        ORDER BY pc.code
    """, (company_id,))
    
    return render_template('finance/profit-centers/list.html',
        title='Profit Centers',
        profit_centers=profit_centers or []
    )


@finance_bp.route('/profit-centers/create', methods=['GET', 'POST'])
@require_permission('finance', 'profit_centers', 'create')
def profit_centers_create():
    """Create profit center."""
    company_id = get_company_id()
    user_id = get_current_user_id()
    
    if request.method == 'POST':
        from finance_models import get_db_context
        with get_db_context() as db:
            cursor = db.execute("""
                INSERT INTO finance_profit_centers (
                    code, name, name_ar, description, parent_id,
                    manager_name, department, is_active, company_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.form.get('code'),
                request.form.get('name'),
                request.form.get('name_ar'),
                request.form.get('description'),
                request.form.get('parent_id', type=int) or None,
                request.form.get('manager_name'),
                request.form.get('department'),
                1 if request.form.get('is_active') == '1' else 0,
                company_id
            ))
            db.commit()
            pc_id = cursor.lastrowid
        
        flash('Profit center created!', 'success')
        return redirect(url_for('finance_enhance.profit_centers_list'))
    
    from finance_models import get_all as db_get_all
    all_centers = db_get_all("""
        SELECT id, code, name FROM finance_profit_centers 
        WHERE (company_id = ? OR company_id IS NULL) AND is_active = 1
        ORDER BY code
    """, (company_id,))
    
    return render_template('finance/profit-centers/create.html',
        title='Create Profit Center',
        profit_centers=all_centers
    )


# ============================================================================
# JOURNAL TEMPLATES & BATCHES ROUTES
# ============================================================================

@finance_bp.route('/journal-templates')
@require_permission('finance', 'journal_templates', 'view')
def journal_templates_list():
    """List journal templates."""
    from finance_models import get_all as db_get_all
    templates = db_get_all("""
        SELECT jt.*, u.username as created_by_name
        FROM finance_journal_templates jt
        LEFT JOIN users u ON jt.created_by = u.id
        ORDER BY jt.name
    """)
    
    return render_template('finance/journals/templates.html',
        title='Journal Templates',
        templates=templates or []
    )


@finance_bp.route('/journal-templates/create', methods=['GET', 'POST'])
@require_permission('finance', 'journal_templates', 'create')
def journal_templates_create():
    """Create journal template."""
    company_id = get_company_id()
    user_id = get_current_user_id()
    
    if request.method == 'POST':
        from finance_models import get_db_context
        with get_db_context() as db:
            cursor = db.execute("""
                INSERT INTO finance_journal_templates (
                    name, description, journal_type, lines_json,
                    company_id, created_by
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                request.form.get('name'),
                request.form.get('description'),
                request.form.get('journal_type', 'General'),
                request.form.get('lines_json'),
                company_id,
                user_id
            ))
            db.commit()
            template_id = cursor.lastrowid
        
        flash('Template created!', 'success')
        return redirect(url_for('finance_enhance.journal_templates_list'))
    
    accounts = get_accounts(company_id=company_id, active_only=True)
    return render_template('finance/journals/template_create.html',
        title='Create Journal Template',
        accounts=accounts
    )


@finance_bp.route('/journal-batches')
@require_permission('finance', 'journal_batches', 'view')
def journal_batches_list():
    """List journal batches."""
    from finance_models import get_all as db_get_all
    batches = db_get_all("""
        SELECT jb.*, u.username as created_by_name,
               (SELECT COUNT(*) FROM finance_journal_batch_items WHERE batch_id = jb.id) as item_count,
               (SELECT SUM(total_debit) FROM finance_journal_batch_items WHERE batch_id = jb.id) as total_amount
        FROM finance_journal_batches jb
        LEFT JOIN users u ON jb.created_by = u.id
        ORDER BY jb.batch_date DESC
    """)
    
    return render_template('finance/journals/batches.html',
        title='Journal Batches',
        batches=batches or []
    )


# ============================================================================
# TAX RULES & TAX JURISDICTIONS ROUTES
# ============================================================================

@finance_bp.route('/tax/rules')
@require_permission('finance', 'tax', 'view')
def tax_rules_list():
    """List tax rules."""
    from finance_models import get_all as db_get_all
    rules = db_get_all("""
        SELECT tr.*, tc.name as tax_code_name
        FROM finance_tax_rules tr
        LEFT JOIN finance_tax_codes tc ON tr.tax_code_id = tc.id
        ORDER BY tr.priority, tr.name
    """)
    
    return render_template('finance/tax/rules.html',
        title='Tax Rules',
        rules=rules or []
    )


@finance_bp.route('/tax/rules/create', methods=['GET', 'POST'])
@require_permission('finance', 'tax', 'create')
def tax_rules_create():
    """Create tax rule."""
    company_id = get_company_id()
    
    if request.method == 'POST':
        from finance_models import get_db_context
        with get_db_context() as db:
            cursor = db.execute("""
                INSERT INTO finance_tax_rules (
                    name, description, tax_code_id, source_module,
                    transaction_type, journal_type, account_id,
                    rate, is_active, priority, company_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.form.get('name'),
                request.form.get('description'),
                request.form.get('tax_code_id', type=int) or None,
                request.form.get('source_module'),
                request.form.get('transaction_type'),
                request.form.get('journal_type'),
                request.form.get('account_id', type=int) or None,
                request.form.get('rate', 0, type=float),
                1 if request.form.get('is_active') == '1' else 0,
                request.form.get('priority', 0, type=int),
                company_id
            ))
            db.commit()
        
        flash('Tax rule created!', 'success')
        return redirect(url_for('finance_enhance.tax_rules_list'))
    
    tax_codes = get_tax_codes(company_id=company_id)
    accounts = get_accounts(company_id=company_id, active_only=True)
    
    return render_template('finance/tax/rule_create.html',
        title='Create Tax Rule',
        tax_codes=tax_codes,
        accounts=accounts
    )


# ============================================================================
# INTERCOMPANY ACCOUNTING ROUTES
# ============================================================================

@finance_bp.route('/intercompany')
@require_permission('finance', 'intercompany', 'view')
def intercompany_list():
    """List intercompany transactions."""
    from finance_models import get_all as db_get_all
    transactions = db_get_all("""
        SELECT ic.*, 
               fb_from.account_name as from_account_name,
               fb_to.account_name as to_account_name,
               c1.name as from_company_name,
               c2.name as to_company_name
        FROM finance_intercompany_transactions ic
        LEFT JOIN finance_bank_accounts fb_from ON ic.from_bank_account_id = fb_from.id
        LEFT JOIN finance_bank_accounts fb_to ON ic.to_bank_account_id = fb_to.id
        LEFT JOIN companies c1 ON ic.from_company_id = c1.id
        LEFT JOIN companies c2 ON ic.to_company_id = c2.id
        ORDER BY ic.transaction_date DESC
    """)
    
    return render_template('finance/intercompany/list.html',
        title='Intercompany Transactions',
        transactions=transactions or []
    )


@finance_bp.route('/intercompany/rules')
@require_permission('finance', 'intercompany', 'view')
def intercompany_rules():
    """Intercompany mapping rules."""
    from finance_models import get_all as db_get_all
    rules = db_get_all("""
        SELECT * FROM finance_intercompany_rules ORDER BY priority
    """)
    
    return render_template('finance/intercompany/rules.html',
        title='Intercompany Rules',
        rules=rules or []
    )


# ============================================================================
# FINANCIAL AUDIT TRAIL ROUTES
# ============================================================================

@finance_bp.route('/audit')
@require_permission('finance', 'audit', 'view')
def audit_trail():
    """Financial audit trail viewer."""
    from finance_models import get_all as db_get_all
    
    module = request.args.get('module')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    user_id = request.args.get('user_id', type=int)
    
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    where_clauses = ["1=1"]
    params = []
    
    if module:
        where_clauses.append("a.module = ?")
        params.append(module)
    
    if start_date:
        where_clauses.append("a.created_at >= ?")
        params.append(start_date)
    
    if end_date:
        where_clauses.append("a.created_at <= ?")
        params.append(end_date)
    
    if user_id:
        where_clauses.append("a.user_id = ?")
        params.append(user_id)
    
    where_sql = " AND ".join(where_clauses)
    
    logs = db_get_all(f"""
        SELECT a.*, u.username
        FROM audit_log a
        LEFT JOIN users u ON a.user_id = u.id
        WHERE {where_sql}
        ORDER BY a.created_at DESC
        LIMIT ? OFFSET ?
    """, params + [per_page, offset])
    
    # Get totals for pagination
    total = db_get_all(f"""
        SELECT COUNT(*) as cnt FROM audit_log a
        WHERE {where_sql}
    """, params)
    total_count = total[0]['cnt'] if total else 0
    
    return render_template('finance/audit/log.html',
        title='Financial Audit Trail',
        logs=logs or [],
        filters={'module': module, 'start_date': start_date, 'end_date': end_date, 'user_id': user_id},
        page=page,
        total_pages=(total_count + per_page - 1) // per_page
    )


# ============================================================================
# FLOW INTEGRATION - FINANCE NOTIFICATIONS
# ============================================================================

@finance_bp.route('/flow/notifications')
@require_permission('finance', 'flow', 'view')
def flow_notifications():
    """Finance-related Flow notifications."""
    company_id = get_company_id()
    user_id = get_current_user_id()
    
    from finance_models import get_all as db_get_all
    
    # Get pending approvals for finance items
    pending_approvals = db_get_all("""
        SELECT wf.*, wi.step_name, wi.status as step_status,
               u.username as requested_by_name
        FROM workflow_instances wi
        LEFT JOIN workflow_definitions wf ON wi.definition_id = wf.id
        LEFT JOIN users u ON wi.created_by = u.id
        WHERE wi.status = 'pending' AND wi.module = 'finance'
        ORDER BY wi.created_at DESC
    """)
    
    return render_template('finance/flow/notifications.html',
        title='Finance Flow Notifications',
        pending_approvals=pending_approvals or []
    )


@finance_bp.route('/api/flow/send-alert', methods=['POST'])
@require_permission('finance', 'flow', 'send')
def api_flow_send_alert():
    """Send alert notification via Flow."""
    data = request.get_json()
    
    alert_type = data.get('type')  # 'overdue_ar', 'upcoming_payment', 'budget_breach', etc.
    alert_data = data.get('data', {})
    
    # Log the alert
    from finance_models import get_db_context
    with get_db_context() as db:
        db.execute("""
            INSERT INTO finance_flow_alerts (alert_type, alert_data, company_id, created_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """, (alert_type, str(alert_data), get_company_id()))
        db.commit()
    
    # TODO: Actually send to Flow system when Flow integration is fully available
    return jsonify({
        'success': True,
        'message': 'Alert sent',
        'alert_type': alert_type
    })


# ============================================================================
# FINANCIAL REPORTS - ADDITIONAL REPORTS
# ============================================================================

@finance_bp.route('/reports/cash-flow')
@require_permission('finance', 'reports', 'view')
def reports_cash_flow():
    """Cash Flow Statement report."""
    company_id = get_company_id()
    as_of_date = request.args.get('as_of_date')
    
    from finance_models import get_all as db_get_all
    
    # Get cash movements by category
    operating = db_get_all("""
        SELECT fa.name as category, SUM(fjl.debit) - SUM(fjl.credit) as amount
        FROM finance_journal_lines fjl
        JOIN finance_accounts fa ON fjl.account_id = fa.id
        JOIN finance_journals fj ON fjl.journal_id = fj.id
        WHERE fa.category_id IN (1, 6) AND fj.status = 'Posted'
        AND fj.company_id = ?
        GROUP BY fa.id
    """, (company_id,))
    
    return render_template('finance/reports/cash_flow.html',
        title='Cash Flow Statement',
        operating=operating or [],
        filters={'as_of_date': as_of_date}
    )


@finance_bp.route('/reports/balance-sheet')
@require_permission('finance', 'reports', 'view')
def reports_balance_sheet():
    """Balance Sheet report."""
    company_id = get_company_id()
    as_of_date = request.args.get('as_of_date') or datetime.now().strftime('%Y-%m-%d')
    
    from finance_models import get_all as db_get_all
    
    # Get balance sheet data by category
    assets = db_get_all("""
        SELECT fa.code, fa.name, SUM(fjl.debit) - SUM(fjl.credit) as balance
        FROM finance_journal_lines fjl
        JOIN finance_accounts fa ON fjl.account_id = fa.id
        JOIN finance_journals fj ON fjl.journal_id = fj.id
        WHERE fa.category_id = 1 AND fj.status = 'Posted'
        AND fj.company_id = ?
        GROUP BY fa.id
        ORDER BY fa.code
    """, (company_id,))
    
    liabilities = db_get_all("""
        SELECT fa.code, fa.name, SUM(fjl.credit) - SUM(fjl.debit) as balance
        FROM finance_journal_lines fjl
        JOIN finance_accounts fa ON fjl.account_id = fa.id
        JOIN finance_journals fj ON fjl.journal_id = fj.id
        WHERE fa.category_id = 2 AND fj.status = 'Posted'
        AND fj.company_id = ?
        GROUP BY fa.id
        ORDER BY fa.code
    """, (company_id,))
    
    equity = db_get_all("""
        SELECT fa.code, fa.name, SUM(fjl.credit) - SUM(fjl.debit) as balance
        FROM finance_journal_lines fjl
        JOIN finance_accounts fa ON fjl.account_id = fa.id
        JOIN finance_journals fj ON fjl.journal_id = fj.id
        WHERE fa.category_id IN (3, 7, 8) AND fj.status = 'Posted'
        AND fj.company_id = ?
        GROUP BY fa.id
        ORDER BY fa.code
    """, (company_id,))
    
    return render_template('finance/reports/balance_sheet.html',
        title='Balance Sheet',
        assets=assets or [],
        liabilities=liabilities or [],
        equity=equity or [],
        filters={'as_of_date': as_of_date}
    )


@finance_bp.route('/reports/income-statement')
@require_permission('finance', 'reports', 'view')
def reports_income_statement():
    """Income Statement report."""
    company_id = get_company_id()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date') or datetime.now().strftime('%Y-%m-%d')
    
    from finance_models import get_all as db_get_all
    
    revenue = db_get_all("""
        SELECT fa.code, fa.name, SUM(fjl.credit) - SUM(fjl.debit) as amount
        FROM finance_journal_lines fjl
        JOIN finance_accounts fa ON fjl.account_id = fa.id
        JOIN finance_journals fj ON fjl.journal_id = fj.id
        WHERE fa.category_id = 4 AND fj.status = 'Posted'
        AND fj.company_id = ?
        GROUP BY fa.id ORDER BY fa.code
    """, (company_id,))
    
    cogs = db_get_all("""
        SELECT fa.code, fa.name, SUM(fjl.debit) - SUM(fjl.credit) as amount
        FROM finance_journal_lines fjl
        JOIN finance_accounts fa ON fjl.account_id = fa.id
        JOIN finance_journals fj ON fjl.journal_id = fj.id
        WHERE fa.category_id = 5 AND fj.status = 'Posted'
        AND fj.company_id = ?
        GROUP BY fa.id ORDER BY fa.code
    """, (company_id,))
    
    expenses = db_get_all("""
        SELECT fa.code, fa.name, SUM(fjl.debit) - SUM(fjl.credit) as amount
        FROM finance_journal_lines fjl
        JOIN finance_accounts fa ON fjl.account_id = fa.id
        JOIN finance_journals fj ON fjl.journal_id = fj.id
        WHERE fa.category_id = 6 AND fj.status = 'Posted'
        AND fj.company_id = ?
        GROUP BY fa.id ORDER BY fa.code
    """, (company_id,))
    
    return render_template('finance/reports/income_statement.html',
        title='Income Statement',
        revenue=revenue or [],
        cogs=cogs or [],
        expenses=expenses or [],
        filters={'start_date': start_date, 'end_date': end_date}
    )


# ============================================================================
# COST ALLOCATION RULES ROUTES
# ============================================================================

@finance_bp.route('/cost-allocation')
@require_permission('finance', 'cost_allocation', 'view')
def cost_allocation_list():
    """List cost allocation rules."""
    from finance_models import get_all as db_get_all
    rules = db_get_all("""
        SELECT car.*, 
               cc_from.name as from_center_name,
               cc_to.name as to_center_name,
               fa.name as account_name
        FROM finance_cost_allocation_rules car
        LEFT JOIN finance_cost_centers cc_from ON car.from_center_id = cc_from.id
        LEFT JOIN finance_cost_centers cc_to ON car.to_center_id = cc_to.id
        LEFT JOIN finance_accounts fa ON car.account_id = fa.id
        ORDER BY car.priority
    """)
    
    return render_template('finance/cost-allocation/list.html',
        title='Cost Allocation Rules',
        rules=rules or []
    )


# ============================================================================
# VARIANCE ANALYSIS REPORT
# ============================================================================

@finance_bp.route('/reports/variance-analysis')
@require_permission('finance', 'reports', 'view')
def reports_variance_analysis():
    """Budget variance analysis report."""
    company_id = get_company_id()
    fiscal_year_id = request.args.get('fiscal_year_id', type=int)
    
    from finance_models import get_all as db_get_all
    
    variances = db_get_all("""
        SELECT 
            cc.name as cost_center_name,
            fa.name as account_name,
            b.total_budget,
            COALESCE(journal_actual.actual, 0) as actual,
            (COALESCE(journal_actual.actual, 0) - b.total_budget) as variance,
            CASE WHEN b.total_budget != 0 
                 THEN ((COALESCE(journal_actual.actual, 0) - b.total_budget) / b.total_budget * 100) 
                 ELSE 0 END as variance_pct
        FROM finance_budget_lines b
        JOIN finance_cost_centers cc ON b.cost_center_id = cc.id
        JOIN finance_accounts fa ON b.account_id = fa.id
        LEFT JOIN (
            SELECT fjl.account_id, fjl.cost_center_id, SUM(fjl.debit) - SUM(fjl.credit) as actual
            FROM finance_journal_lines fjl
            JOIN finance_journals fj ON fjl.journal_id = fj.id
            WHERE fj.status = 'Posted' AND fj.company_id = ?
            GROUP BY fjl.account_id, fjl.cost_center_id
        ) journal_actual ON b.account_id = journal_actual.account_id 
                         AND b.cost_center_id = journal_actual.cost_center_id
        WHERE b.company_id = ?
        ORDER BY cc.name, fa.name
    """, (company_id, company_id))
    
    fiscal_years = get_fiscal_years(company_id=company_id)
    
    return render_template('finance/reports/variance_analysis.html',
        title='Variance Analysis',
        variances=variances or [],
        fiscal_years=fiscal_years,
        filters={'fiscal_year_id': fiscal_year_id}
    )


# ============================================================================
# APPROVAL QUEUE ROUTES
# ============================================================================

@finance_bp.route('/approvals/pending')
@require_permission('finance', 'approvals', 'view')
def approvals_pending():
    """Pending finance approvals."""
    user_id = get_current_user_id()
    
    from finance_models import get_all as db_get_all
    
    pending = db_get_all("""
        SELECT wa.*, u.username as requested_by, wi.id as instance_id,
               wi.status as workflow_status
        FROM workflow_approvals wa
        LEFT JOIN workflow_instances wi ON wa.instance_id = wi.id
        LEFT JOIN users u ON wi.created_by = u.id
        WHERE wa.approver_id = ? AND wa.status = 'pending'
        ORDER BY wa.created_at DESC
    """, (user_id,))
    
    return render_template('finance/approvals/pending.html',
        title='Pending Approvals',
        pending=pending or []
    )


@finance_bp.route('/approvals/<int:approval_id>/approve', methods=['POST'])
@require_permission('finance', 'approvals', 'approve')
def approvals_approve(approval_id):
    """Approve a finance request."""
    user_id = get_current_user_id()
    
    from finance_models import get_db_context
    with get_db_context() as db:
        db.execute("""
            UPDATE workflow_approvals 
            SET status = 'approved', approved_by = ?, approved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, approval_id))
        db.commit()
    
    flash('Approval granted!', 'success')
    return redirect(url_for('finance_enhance.approvals_pending'))


@finance_bp.route('/approvals/<int:approval_id>/reject', methods=['POST'])
@require_permission('finance', 'approvals', 'reject')
def approvals_reject(approval_id):
    """Reject a finance request."""
    user_id = get_current_user_id()
    reason = request.form.get('reason', '')
    
    from finance_models import get_db_context
    with get_db_context() as db:
        db.execute("""
            UPDATE workflow_approvals 
            SET status = 'rejected', approved_by = ?, approved_at = CURRENT_TIMESTAMP,
                rejection_reason = ?
            WHERE id = ?
        """, (user_id, reason, approval_id))
        db.commit()
    
    flash('Request rejected', 'info')
    return redirect(url_for('finance_enhance.approvals_pending'))


# ============================================================================
# FINANCE SETTINGS ROUTES
# ============================================================================

@finance_bp.route('/settings')
@require_permission('finance', 'settings', 'view')
def finance_settings():
    """Finance module settings."""
    company_id = get_company_id()
    from finance_models import get_all as db_get_all

    # Get current fiscal year
    fiscal_years = get_fiscal_years(company_id=company_id, is_active=True)
    current_fiscal_year = fiscal_years[0] if fiscal_years else None

    # Get period settings
    periods = []
    if current_fiscal_year:
        periods = get_fiscal_periods(current_fiscal_year['id'])

    return render_template('finance/settings/index.html',
        title='Finance Settings',
        fiscal_year=current_fiscal_year,
        periods=periods or []
    )


@finance_bp.route('/settings/update', methods=['POST'])
@require_permission('finance', 'settings', 'edit')
def finance_settings_update():
    """Update finance settings."""
    data = request.form

    # Update period lock settings
    period_id = data.get('period_id')
    if period_id:
        from finance_models import get_db_context
        with get_db_context() as db:
            db.execute("""
                UPDATE finance_fiscal_periods
                SET period_lock = 1
                WHERE id = ?
            """, (period_id,))
            db.commit()

    flash('Settings updated successfully', 'success')
    return redirect(url_for('finance_enhance.finance_settings'))


@finance_bp.route('/settings/numbering')
@require_permission('finance', 'settings', 'view')
def finance_numbering():
    """Finance numbering rules."""
    return render_template('finance/settings/numbering.html',
        title='Numbering Rules'
    )


@finance_bp.route('/settings/posting-policies')
@require_permission('finance', 'settings', 'view')
def finance_posting_policies():
    """Finance posting policies."""
    return render_template('finance/settings/posting_policies.html',
        title='Posting Policies'
    )


@finance_bp.route('/settings/currency')
@require_permission('finance', 'settings', 'view')
def finance_currency_settings():
    """Currency settings."""
    return render_template('finance/settings/currency.html',
        title='Currency Settings'
    )


# Register all enhancement routes
def register_finance_enhancements(app):
    """Register finance enhancement blueprint with Flask app."""
    app.register_blueprint(finance_bp)
