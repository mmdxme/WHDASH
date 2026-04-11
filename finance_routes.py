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


# Register the blueprint with the Flask app
def register_finance_routes(app):
    """Register finance routes with the Flask app."""
    app.register_blueprint(finance_bp)
