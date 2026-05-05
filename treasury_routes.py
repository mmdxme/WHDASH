"""
Treasury / Cash Flow Module - Route Handlers
============================================
Enterprise treasury management routes covering:
- Treasury Dashboard
- Cash Position Management
- Petty Cash & Cash Box Management
- Cash Flow Forecasting
- Collections Planning
- Payments Planning
- Bank Account Management
- Transfers
- Bank Reconciliation
- Treasury Controls & Alerts
- Liquidity Planning
- Treasury Reports
- Workflow & Approvals
- Audit Log

Author: Treasury Module Implementation
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from functools import wraps
from datetime import datetime, timedelta
import json

treasury_bp = Blueprint('treasury', __name__, url_prefix='/finance/treasury')

# Import unified permission decorator
from permissions import require_permission

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_company_id():
    """Get company ID from session or default."""
    from flask import session
    return session.get('company_id', 1)


def get_current_user_id():
    """Get current user ID from session."""
    from flask import session
    return session.get('user_id', 1)


def get_current_user():
    """Get current user info."""
    from flask import session
    return {
        'id': session.get('user_id', 1),
        'name': session.get('user_name', 'System User'),
        'role': session.get('user_role', 'Treasury Manager')
    }


def check_treasury_permission(resource, action='view'):
    """Check if user has treasury permission."""
    from flask import session
    user_permissions = session.get('permissions', {})
    treasury_perms = user_permissions.get('finance', {}).get('treasury', [])
    return action in treasury_perms or 'manage' in treasury_perms


def log_treasury_action(action, entity_type, entity_id, entity_name=None, details=None):
    """Log treasury action to audit log."""
    from treasury_models import log_treasury_audit
    user = get_current_user()
    log_treasury_audit(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_name=entity_name,
        user_id=user['id'],
        user_name=user['name'],
        user_role=user['role'],
        company_id=get_company_id()
    )


def send_treasury_flow_alert(alert_type, title, message, severity='medium', amount=None):
    """Send treasury alert to Flow."""
    from treasury_models import create_treasury_alert
    alert_data = {
        'alert_type': alert_type,
        'alert_category': alert_type,
        'severity': severity,
        'title': title,
        'message': message,
        'amount': amount,
        'company_id': get_company_id()
    }
    return create_treasury_alert(alert_data)


# ============================================================================
# TREASURY DASHBOARD
# ============================================================================

@treasury_bp.route('/dashboard')
def treasury_dashboard():
    """Main Treasury Dashboard with comprehensive KPIs."""
    company_id = get_company_id()
    
    # Import models
    from treasury_models import (
        calculate_daily_cash_position, get_treasury_alerts, 
        get_treasury_collections, get_treasury_payments,
        get_bank_accounts, get_cash_flow_forecast_data,
        get_unread_alert_count, get_critical_alerts,
        analyze_liquidity_position, get_treasury_forecasts,
        get_transfer_requests, get_treasury_controls,
        get_treasury_petty_cash_accounts, get_cash_boxes
    )
    from finance_models import get_customer_invoices, get_supplier_bills
    
    # Get current cash position
    cash_position = calculate_daily_cash_position(company_id)
    
    # Get bank accounts
    bank_accounts = get_bank_accounts(company_id=company_id, is_active=True)
    
    # Get petty cash
    petty_cash = get_treasury_petty_cash_accounts(company_id=company_id, is_active=True)
    
    # Get cash boxes
    cash_boxes = get_cash_boxes(company_id=company_id, is_active=True)
    
    # Get unread alert count
    unread_alerts = get_unread_alert_count(company_id)
    
    # Get critical alerts
    critical_alerts = get_critical_alerts(company_id)
    
    # Get 7-day forecast
    forecast_7day = get_cash_flow_forecast_data(company_id, days=7)
    
    # Get 30-day forecast
    forecast_30day = get_cash_flow_forecast_data(company_id, days=30)
    
    # Get liquidity analysis
    liquidity = analyze_liquidity_position(company_id)
    
    # Get pending transfer requests
    pending_transfers = get_transfer_requests(company_id=company_id, status='Pending')
    
    # Get pending approvals count
    pending_approval_count = len(pending_transfers)
    
    # Get treasury controls status
    controls = get_treasury_controls(company_id=company_id)
    
    # Get collections summary
    from treasury_models import get_collections_summary
    collections_summary = get_collections_summary(company_id)
    
    # Get payments summary
    from treasury_models import get_payments_summary
    payments_summary = get_payments_summary(company_id)
    
    # Calculate forecast totals
    total_7day_inflow = sum(d['inflow'] for d in forecast_7day['forecast'].values())
    total_7day_outflow = sum(d['outflow'] for d in forecast_7day['forecast'].values())
    total_7day_net = total_7day_inflow - total_7day_outflow
    
    total_30day_inflow = sum(d['inflow'] for d in forecast_30day['forecast'].values())
    total_30day_outflow = sum(d['outflow'] for d in forecast_30day['forecast'].values())
    total_30day_net = total_30day_inflow - total_30day_outflow
    
    # Get upcoming major receipts (next 7 days)
    upcoming_receipts = []
    for date_str, data in forecast_7day['forecast'].items():
        for item in data.get('inflow_items', []):
            if item['type'] == 'ar_receipt':
                upcoming_receipts.append({
                    'date': date_str,
                    'customer': item.get('customer'),
                    'reference': item.get('reference'),
                    'amount': item['amount']
                })
    
    # Get upcoming major payments (next 7 days)
    upcoming_payments = []
    for date_str, data in forecast_7day['forecast'].items():
        for item in data.get('outflow_items', []):
            if item['type'] == 'ap_payment':
                upcoming_payments.append({
                    'date': date_str,
                    'supplier': item.get('supplier'),
                    'reference': item.get('reference'),
                    'amount': item['amount']
                })
    
    # Prepare chart data
    forecast_labels = list(forecast_7day['forecast'].keys())
    inflow_data = [forecast_7day['forecast'][d]['inflow'] for d in forecast_labels]
    outflow_data = [forecast_7day['forecast'][d]['outflow'] for d in forecast_labels]
    
    # Currency breakdown
    currency_breakdown = []
    for currency, data in cash_position['by_currency'].items():
        currency_breakdown.append({
            'currency': currency,
            'total': data['total_balance'],
            'bank': data.get('bank_balance', 0),
            'petty_cash': data.get('petty_cash_balance', 0),
            'cash_boxes': data.get('cash_box_balance', 0)
        })
    
    return render_template('finance/treasury/dashboard.html',
        title='Treasury Dashboard',
        cash_position=cash_position,
        bank_accounts=bank_accounts,
        petty_cash=petty_cash,
        cash_boxes=cash_boxes,
        unread_alerts=unread_alerts,
        critical_alerts=critical_alerts,
        forecast_7day=forecast_7day,
        forecast_30day=forecast_30day,
        total_7day_inflow=total_7day_inflow,
        total_7day_outflow=total_7day_outflow,
        total_7day_net=total_7day_net,
        total_30day_inflow=total_30day_inflow,
        total_30day_outflow=total_30day_outflow,
        total_30day_net=total_30day_net,
        liquidity=liquidity,
        pending_approval_count=pending_approval_count,
        controls=controls,
        collections_summary=collections_summary,
        payments_summary=payments_summary,
        upcoming_receipts=upcoming_receipts[:5],
        upcoming_payments=upcoming_payments[:5],
        forecast_labels=json.dumps(forecast_labels),
        inflow_data=json.dumps(inflow_data),
        outflow_data=json.dumps(outflow_data),
        currency_breakdown=currency_breakdown
    )


# ============================================================================
# CASH POSITION MANAGEMENT
# ============================================================================

@treasury_bp.route('/cash-position')
def cash_position():
    """Cash Position Overview."""
    company_id = get_company_id()
    
    from treasury_models import (
        calculate_daily_cash_position, get_bank_accounts,
        get_treasury_petty_cash_accounts, get_cash_boxes,
        get_cash_position_snapshots
    )
    
    # Get current cash position
    cash_position = calculate_daily_cash_position(company_id)
    
    # Get bank accounts with balances
    bank_accounts = get_bank_accounts(company_id=company_id, is_active=True)
    
    # Get petty cash accounts
    petty_cash = get_treasury_petty_cash_accounts(company_id=company_id, is_active=True)
    
    # Get cash boxes
    cash_boxes = get_cash_boxes(company_id=company_id, is_active=True)
    
    # Get historical snapshots (last 30 days)
    end_date = datetime.now().date().isoformat()
    start_date = (datetime.now().date() - timedelta(days=30)).isoformat()
    snapshots = get_cash_position_snapshots(company_id, start_date=start_date, end_date=end_date)
    
    return render_template('finance/treasury/cash_position.html',
        title='Cash Position',
        cash_position=cash_position,
        bank_accounts=bank_accounts,
        petty_cash=petty_cash,
        cash_boxes=cash_boxes,
        snapshots=snapshots
    )


@treasury_bp.route('/cash-position/by-currency')
def cash_position_by_currency():
    """Cash Position breakdown by currency."""
    company_id = get_company_id()
    
    from treasury_models import calculate_daily_cash_position
    
    cash_position = calculate_daily_cash_position(company_id)
    
    return render_template('finance/treasury/cash_position_by_currency.html',
        title='Cash Position by Currency',
        cash_position=cash_position
    )


@treasury_bp.route('/cash-position/by-bank')
def cash_position_by_bank():
    """Cash Position breakdown by bank."""
    company_id = get_company_id()
    
    from treasury_models import get_bank_accounts
    from finance_models import get_account_balance
    
    bank_accounts = get_bank_accounts(company_id=company_id, is_active=True)
    
    # Enrich with GL balance
    for account in bank_accounts:
        if account.get('gl_account_id'):
            balance = get_account_balance(account['gl_account_id'])
            account['gl_balance'] = balance.get('balance', 0)
        else:
            account['gl_balance'] = account.get('current_balance', 0)
    
    # Group by bank
    by_bank = {}
    for account in bank_accounts:
        bank_name = account.get('bank_name', 'Unknown')
        if bank_name not in by_bank:
            by_bank[bank_name] = {
                'bank_name': bank_name,
                'accounts': [],
                'total_balance': 0,
                'currency': account.get('currency', 'AED')
            }
        by_bank[bank_name]['accounts'].append(account)
        by_bank[bank_name]['total_balance'] += float(account.get('current_balance', 0) or 0)
    
    return render_template('finance/treasury/cash_position_by_bank.html',
        title='Cash Position by Bank',
        by_bank=by_bank
    )


@treasury_bp.route('/cash-position/historical')
def cash_position_historical():
    """Historical Cash Position snapshots."""
    company_id = get_company_id()
    
    from treasury_models import get_cash_position_snapshots
    
    start_date = request.args.get('start_date', (datetime.now().date() - timedelta(days=90)).isoformat())
    end_date = request.args.get('end_date', datetime.now().date().isoformat())
    currency = request.args.get('currency')
    
    snapshots = get_cash_position_snapshots(company_id, start_date=start_date, end_date=end_date, currency=currency)
    
    return render_template('finance/treasury/cash_position_historical.html',
        title='Historical Cash Position',
        snapshots=snapshots,
        filters={'start_date': start_date, 'end_date': end_date, 'currency': currency}
    )


# ============================================================================
# PETTY CASH MANAGEMENT
# ============================================================================

@treasury_bp.route('/petty-cash')
def petty_cash_list():
    """List all petty cash accounts."""
    company_id = get_company_id()
    
    from treasury_models import get_treasury_petty_cash_accounts
    
    branch_id = request.args.get('branch_id', type=int)
    petty_cash = get_treasury_petty_cash_accounts(company_id=company_id, branch_id=branch_id)
    
    return render_template('finance/treasury/petty_cash_list.html',
        title='Petty Cash Accounts',
        petty_cash=petty_cash,
        filters={'branch_id': branch_id}
    )


@treasury_bp.route('/petty-cash/<int:account_id>')
def petty_cash_view(account_id):
    """View petty cash account details."""
    from treasury_models import get_petty_cash_account_by_id, get_cash_movements
    
    account = get_petty_cash_account_by_id(account_id)
    if not account:
        flash('Petty cash account not found', 'error')
        return redirect(url_for('treasury.petty_cash_list'))
    
    movements = get_cash_movements(company_id=get_company_id(), petty_cash_id=account_id)
    
    return render_template('finance/treasury/petty_cash_view.html',
        title=f'Petty Cash: {account["account_name"]}',
        account=account,
        movements=movements
    )


@treasury_bp.route('/petty-cash/create', methods=['GET', 'POST'])
def petty_cash_create():
    """Create new petty cash account."""
    if request.method == 'POST':
        from treasury_models import create_petty_cash_account, log_treasury_audit
        
        data = {
            'account_code': request.form.get('account_code'),
            'account_name': request.form.get('account_name'),
            'account_name_ar': request.form.get('account_name_ar'),
            'location': request.form.get('location'),
            'float_amount': request.form.get('float_amount', type=float),
            'current_balance': request.form.get('float_amount', type=float),
            'minimum_balance': request.form.get('minimum_balance', type=float),
            'maximum_transaction': request.form.get('maximum_transaction', type=float),
            'currency': request.form.get('currency', 'AED'),
            'entity_id': request.form.get('entity_id', type=int),
            'branch_id': request.form.get('branch_id', type=int),
            'gl_account_id': request.form.get('gl_account_id', type=int),
            'notes': request.form.get('notes'),
            'company_id': get_company_id(),
            'created_by': get_current_user_id()
        }
        
        account_id = create_petty_cash_account(data)
        log_treasury_action('create', 'petty_cash_account', account_id, data['account_name'])
        flash('Petty cash account created successfully', 'success')
        return redirect(url_for('treasury.petty_cash_view', account_id=account_id))
    
    from finance_models import get_accounts
    accounts = get_accounts(company_id=get_company_id(), active_only=True)
    cash_accounts = [a for a in accounts if a.get('account_type') == 'ASSET']
    
    return render_template('finance/treasury/petty_cash_create.html',
        title='Create Petty Cash Account',
        accounts=cash_accounts
    )


@treasury_bp.route('/petty-cash/<int:account_id>/edit', methods=['GET', 'POST'])
def petty_cash_edit(account_id):
    """Edit petty cash account."""
    from treasury_models import get_petty_cash_account_by_id, update_petty_cash_account, log_treasury_audit
    
    account = get_petty_cash_account_by_id(account_id)
    if not account:
        flash('Petty cash account not found', 'error')
        return redirect(url_for('treasury.petty_cash_list'))
    
    if request.method == 'POST':
        data = {
            'account_name': request.form.get('account_name'),
            'account_name_ar': request.form.get('account_name_ar'),
            'location': request.form.get('location'),
            'float_amount': request.form.get('float_amount', type=float),
            'minimum_balance': request.form.get('minimum_balance', type=float),
            'maximum_transaction': request.form.get('maximum_transaction', type=float),
            'currency': request.form.get('currency'),
            'is_active': 1 if request.form.get('is_active') else 0,
            'entity_id': request.form.get('entity_id', type=int),
            'branch_id': request.form.get('branch_id', type=int),
            'gl_account_id': request.form.get('gl_account_id', type=int),
            'notes': request.form.get('notes')
        }
        
        update_petty_cash_account(account_id, data)
        log_treasury_action('update', 'petty_cash_account', account_id, account['account_name'])
        flash('Petty cash account updated successfully', 'success')
        return redirect(url_for('treasury.petty_cash_view', account_id=account_id))
    
    from finance_models import get_accounts
    accounts = get_accounts(company_id=get_company_id(), active_only=True)
    cash_accounts = [a for a in accounts if a.get('account_type') == 'ASSET']
    
    return render_template('finance/treasury/petty_cash_edit.html',
        title=f'Edit: {account["account_name"]}',
        account=account,
        accounts=cash_accounts
    )


@treasury_bp.route('/petty-cash/<int:account_id>/top-up', methods=['POST'])
def petty_cash_topup(account_id):
    """Top up petty cash account."""
    from treasury_models import create_cash_movement, log_treasury_audit
    
    amount = request.form.get('amount', type=float)
    reference = request.form.get('reference')
    notes = request.form.get('notes')
    
    if amount <= 0:
        flash('Amount must be positive', 'error')
        return redirect(url_for('treasury.petty_cash_view', account_id=account_id))
    
    movement_data = {
        'movement_date': datetime.now().date().isoformat(),
        'movement_type': 'top_up',
        'petty_cash_account_id': account_id,
        'amount': amount,
        'reference': reference,
        'description': notes,
        'status': 'Completed',
        'approved_by': get_current_user_id(),
        'company_id': get_company_id(),
        'created_by': get_current_user_id()
    }
    
    movement_id = create_cash_movement(movement_data)
    log_treasury_action('top_up', 'petty_cash_account', account_id, f'Top up: {amount}')
    flash(f'Petty cash topped up successfully. Movement: {movement_id}', 'success')
    return redirect(url_for('treasury.petty_cash_view', account_id=account_id))


@treasury_bp.route('/petty-cash/<int:account_id>/withdraw', methods=['POST'])
def petty_cash_withdraw(account_id):
    """Withdraw from petty cash account."""
    from treasury_models import create_cash_movement, get_petty_cash_account_by_id, log_treasury_audit
    
    amount = request.form.get('amount', type=float)
    reference = request.form.get('reference')
    beneficiary = request.form.get('beneficiary_name')
    description = request.form.get('description')
    
    if amount <= 0:
        flash('Amount must be positive', 'error')
        return redirect(url_for('treasury.petty_cash_view', account_id=account_id))
    
    # Check if exceeds maximum transaction
    account = get_petty_cash_account_by_id(account_id)
    if account.get('maximum_transaction') and amount > account['maximum_transaction']:
        flash(f'Amount exceeds maximum transaction limit of {account["maximum_transaction"]}', 'error')
        return redirect(url_for('treasury.petty_cash_view', account_id=account_id))
    
    movement_data = {
        'movement_date': datetime.now().date().isoformat(),
        'movement_type': 'withdrawal',
        'petty_cash_account_id': account_id,
        'amount': amount,
        'reference': reference,
        'beneficiary_name': beneficiary,
        'description': description,
        'status': 'Completed',
        'approved_by': get_current_user_id(),
        'company_id': get_company_id(),
        'created_by': get_current_user_id()
    }
    
    movement_id = create_cash_movement(movement_data)
    log_treasury_action('withdraw', 'petty_cash_account', account_id, f'Withdrawal: {amount}')
    flash(f'Petty cash withdrawal successful. Movement: {movement_id}', 'success')
    return redirect(url_for('treasury.petty_cash_view', account_id=account_id))


# ============================================================================
# CASH BOXES
# ============================================================================

@treasury_bp.route('/cash-boxes')
def cash_boxes_list():
    """List all cash boxes."""
    company_id = get_company_id()
    
    from treasury_models import get_cash_boxes
    
    branch_id = request.args.get('branch_id', type=int)
    cash_boxes = get_cash_boxes(company_id=company_id, branch_id=branch_id)
    
    return render_template('finance/treasury/cash_boxes_list.html',
        title='Cash Boxes',
        cash_boxes=cash_boxes,
        filters={'branch_id': branch_id}
    )


@treasury_bp.route('/cash-boxes/<int:box_id>')
def cash_box_view(box_id):
    """View cash box details."""
    from treasury_models import get_cash_box_by_id, get_cash_movements
    
    box = get_cash_box_by_id(box_id)
    if not box:
        flash('Cash box not found', 'error')
        return redirect(url_for('treasury.cash_boxes_list'))
    
    movements = get_cash_movements(company_id=get_company_id(), cash_box_id=box_id)
    
    return render_template('finance/treasury/cash_box_view.html',
        title=f'Cash Box: {box["box_name"]}',
        box=box,
        movements=movements
    )


@treasury_bp.route('/cash-boxes/create', methods=['GET', 'POST'])
def cash_box_create():
    """Create new cash box."""
    if request.method == 'POST':
        from treasury_models import create_cash_box, log_treasury_audit
        
        data = {
            'box_code': request.form.get('box_code'),
            'box_name': request.form.get('box_name'),
            'box_type': request.form.get('box_type', 'cash_box'),
            'location': request.form.get('location'),
            'responsible_person_name': request.form.get('responsible_person_name'),
            'opening_balance': request.form.get('opening_balance', type=float),
            'current_balance': request.form.get('opening_balance', type=float),
            'currency': request.form.get('currency', 'AED'),
            'entity_id': request.form.get('entity_id', type=int),
            'branch_id': request.form.get('branch_id', type=int),
            'notes': request.form.get('notes'),
            'company_id': get_company_id(),
            'created_by': get_current_user_id()
        }
        
        box_id = create_cash_box(data)
        log_treasury_action('create', 'cash_box', box_id, data['box_name'])
        flash('Cash box created successfully', 'success')
        return redirect(url_for('treasury.cash_box_view', box_id=box_id))
    
    return render_template('finance/treasury/cash_box_create.html',
        title='Create Cash Box'
    )


# ============================================================================
# CASH FLOW FORECASTING
# ============================================================================

@treasury_bp.route('/forecast')
def cash_flow_forecast():
    """Cash Flow Forecast main view."""
    company_id = get_company_id()
    
    from treasury_models import (
        get_treasury_forecasts, get_cash_flow_forecast_data,
        get_forecast_items, get_forecast_summary
    )
    from treasury_models import get_treasury_forecasts as get_forecasts
    
    # Get active forecasts
    forecasts = get_forecasts(company_id=company_id, status='Approved')
    if not forecasts:
        forecasts = get_forecasts(company_id=company_id, status='Draft')
    
    active_forecast = forecasts[0] if forecasts else None
    
    # Get 30-day forecast
    forecast_30day = get_cash_flow_forecast_data(company_id, days=30)
    
    # Get 90-day forecast if needed
    forecast_90day = get_cash_flow_forecast_data(company_id, days=90)
    
    # Calculate weekly summary
    weekly_summary = []
    current_week = []
    week_num = 1
    
    for date_str, data in forecast_30day['forecast'].items():
        current_week.append(data)
        if len(current_week) == 7:
            week_inflow = sum(d['inflow'] for d in current_week)
            week_outflow = sum(d['outflow'] for d in current_week)
            weekly_summary.append({
                'week': f'Week {week_num}',
                'start_date': current_week[0]['date'],
                'end_date': current_week[-1]['date'],
                'inflow': week_inflow,
                'outflow': week_outflow,
                'net': week_inflow - week_outflow
            })
            current_week = []
            week_num += 1
    
    # Forecast summary by category
    forecast_summary = {}
    if active_forecast:
        summary = get_forecast_summary(active_forecast['id'])
        for item in summary:
            forecast_summary[item['item_type']] = item['weighted_amount']
    
    # Chart data
    forecast_labels = list(forecast_30day['forecast'].keys())
    inflow_data = [forecast_30day['forecast'][d]['inflow'] for d in forecast_labels]
    outflow_data = [forecast_30day['forecast'][d]['outflow'] for d in forecast_labels]
    
    return render_template('finance/treasury/cash_flow_forecast.html',
        title='Cash Flow Forecast',
        forecast=forecast_30day,
        forecasts=forecasts,
        active_forecast=active_forecast,
        weekly_summary=weekly_summary,
        forecast_summary=forecast_summary,
        forecast_labels=json.dumps(forecast_labels),
        inflow_data=json.dumps(inflow_data),
        outflow_data=json.dumps(outflow_data)
    )


@treasury_bp.route('/forecast/7-day')
def forecast_7_day():
    """7-Day Cash Flow Forecast."""
    company_id = get_company_id()
    
    from treasury_models import get_cash_flow_forecast_data
    
    forecast = get_cash_flow_forecast_data(company_id, days=7)
    
    return render_template('finance/treasury/forecast_7day.html',
        title='7-Day Cash Flow Forecast',
        forecast=forecast
    )


@treasury_bp.route('/forecast/30-day')
def forecast_30_day():
    """30-Day Cash Flow Forecast."""
    company_id = get_company_id()
    
    from treasury_models import get_cash_flow_forecast_data
    
    forecast = get_cash_flow_forecast_data(company_id, days=30)
    
    return render_template('finance/treasury/forecast_30day.html',
        title='30-Day Cash Flow Forecast',
        forecast=forecast
    )


@treasury_bp.route('/forecast/90-day')
def forecast_90_day():
    """90-Day Cash Flow Forecast."""
    company_id = get_company_id()
    
    from treasury_models import get_cash_flow_forecast_data
    
    forecast = get_cash_flow_forecast_data(company_id, days=90)
    
    return render_template('finance/treasury/forecast_90day.html',
        title='90-Day Cash Flow Forecast',
        forecast=forecast
    )


@treasury_bp.route('/forecast/vs-actual')
def forecast_vs_actual():
    """Forecast vs Actual comparison."""
    company_id = get_company_id()
    
    from treasury_models import get_cash_position_snapshots, get_cash_flow_forecast_data
    
    # Get actuals from last 30 days
    end_date = datetime.now().date().isoformat()
    start_date = (datetime.now().date() - timedelta(days=30)).isoformat()
    actuals = get_cash_position_snapshots(company_id, start_date=start_date, end_date=end_date)
    
    # Get forecast
    forecast = get_cash_flow_forecast_data(company_id, days=30)
    
    return render_template('finance/treasury/forecast_vs_actual.html',
        title='Forecast vs Actual',
        actuals=actuals,
        forecast=forecast
    )


@treasury_bp.route('/forecast/create', methods=['GET', 'POST'])
def forecast_create():
    """Create new cash flow forecast."""
    if request.method == 'POST':
        from treasury_models import create_treasury_forecast, log_treasury_audit
        
        forecast_type = request.form.get('forecast_type', 'rolling')
        scenario = request.form.get('scenario', 'base')
        
        data = {
            'forecast_name': request.form.get('forecast_name'),
            'forecast_type': forecast_type,
            'scenario': scenario,
            'start_date': request.form.get('start_date'),
            'end_date': request.form.get('end_date'),
            'currency': request.form.get('currency', 'AED'),
            'status': 'Draft',
            'notes': request.form.get('notes'),
            'entity_id': request.form.get('entity_id', type=int),
            'branch_id': request.form.get('branch_id', type=int),
            'company_id': get_company_id(),
            'created_by': get_current_user_id()
        }
        
        forecast_id = create_treasury_forecast(data)
        log_treasury_action('create', 'treasury_forecast', forecast_id, data['forecast_name'])
        flash('Forecast created successfully', 'success')
        return redirect(url_for('treasury.forecast_detail', forecast_id=forecast_id))
    
    return render_template('finance/treasury/forecast_create.html',
        title='Create Cash Flow Forecast'
    )


@treasury_bp.route('/forecast/<int:forecast_id>')
def forecast_detail(forecast_id):
    """View forecast detail."""
    from treasury_models import get_treasury_forecast_by_id, get_forecast_items, get_forecast_summary
    
    forecast = get_treasury_forecast_by_id(forecast_id)
    if not forecast:
        flash('Forecast not found', 'error')
        return redirect(url_for('treasury.cash_flow_forecast'))
    
    items = get_forecast_items(forecast_id)
    summary = get_forecast_summary(forecast_id)
    
    return render_template('finance/treasury/forecast_detail.html',
        title=f'Forecast: {forecast["forecast_name"]}',
        forecast=forecast,
        items=items,
        summary=summary
    )


@treasury_bp.route('/forecast/<int:forecast_id>/approve', methods=['POST'])
def forecast_approve(forecast_id):
    """Approve a forecast."""
    from treasury_models import approve_treasury_forecast, get_treasury_forecast_by_id, log_treasury_audit
    
    forecast = get_treasury_forecast_by_id(forecast_id)
    approve_treasury_forecast(forecast_id, get_current_user_id())
    log_treasury_action('approve', 'treasury_forecast', forecast_id, forecast['forecast_name'])
    flash('Forecast approved successfully', 'success')
    return redirect(url_for('treasury.forecast_detail', forecast_id=forecast_id))


# ============================================================================
# COLLECTIONS PLANNING
# ============================================================================

@treasury_bp.route('/collections')
def collections():
    """Collections Planning view."""
    company_id = get_company_id()
    
    from treasury_models import get_treasury_collections, get_collections_summary, sync_collections_from_ar
    
    # Sync from AR if requested
    if request.args.get('sync'):
        sync_collections_from_ar(company_id)
        flash('Collections synced from AR', 'success')
    
    risk_level = request.args.get('risk_level')
    likelihood = request.args.get('likelihood')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    collections = get_treasury_collections(
        company_id, start_date=start_date, end_date=end_date,
        risk_level=risk_level, likelihood=likelihood
    )
    
    summary = get_collections_summary(company_id, start_date=start_date, end_date=end_date)
    
    return render_template('finance/treasury/collections.html',
        title='Collections Planning',
        collections=collections,
        summary=summary,
        filters={'risk_level': risk_level, 'likelihood': likelihood, 'start_date': start_date, 'end_date': end_date}
    )


@treasury_bp.route('/collections/calendar')
def collections_calendar():
    """Collections calendar view."""
    company_id = get_company_id()
    
    from treasury_models import get_treasury_collections
    
    collections = get_treasury_collections(company_id)
    
    # Group by expected date
    by_date = {}
    for col in collections:
        due_date = col.get('due_date')
        if due_date:
            if due_date not in by_date:
                by_date[due_date] = []
            by_date[due_date].append(col)
    
    return render_template('finance/treasury/collections_calendar.html',
        title='Collections Calendar',
        collections_by_date=by_date
    )


@treasury_bp.route('/collections/overdue')
def collections_overdue():
    """Overdue collections view."""
    company_id = get_company_id()
    
    from treasury_models import get_treasury_collections
    
    today = datetime.now().date().isoformat()
    collections = get_treasury_collections(company_id, end_date=today)
    
    # Filter overdue
    overdue = [c for c in collections if c.get('due_date') and c['due_date'] < today]
    
    return render_template('finance/treasury/collections_overdue.html',
        title='Overdue Collections',
        overdue_collections=overdue
    )


# ============================================================================
# PAYMENTS PLANNING
# ============================================================================

@treasury_bp.route('/payments')
def payments():
    """Payments Planning view."""
    company_id = get_company_id()
    
    from treasury_models import get_treasury_payments, get_payments_summary, sync_payments_from_ap
    
    # Sync from AP if requested
    if request.args.get('sync'):
        sync_payments_from_ap(company_id)
        flash('Payments synced from AP', 'success')
    
    priority = request.args.get('priority')
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    payments_list = get_treasury_payments(
        company_id, start_date=start_date, end_date=end_date,
        priority=priority, status=status
    )
    
    summary = get_payments_summary(company_id, start_date=start_date, end_date=end_date)
    
    return render_template('finance/treasury/payments.html',
        title='Payments Planning',
        payments=payments_list,
        summary=summary,
        filters={'priority': priority, 'status': status, 'start_date': start_date, 'end_date': end_date}
    )


@treasury_bp.route('/payments/calendar')
def payments_calendar():
    """Payments calendar view."""
    company_id = get_company_id()
    
    from treasury_models import get_treasury_payments
    
    payments_list = get_treasury_payments(company_id)
    
    # Group by due date
    by_date = {}
    for pay in payments_list:
        due_date = pay.get('due_date')
        if due_date:
            if due_date not in by_date:
                by_date[due_date] = []
            by_date[due_date].append(pay)
    
    return render_template('finance/treasury/payments_calendar.html',
        title='Payments Calendar',
        payments_by_date=by_date
    )


@treasury_bp.route('/payments/cash-requirement')
def payments_cash_requirement():
    """Cash requirement view for payments."""
    company_id = get_company_id()
    
    from treasury_models import get_treasury_payments, calculate_daily_cash_position
    
    payments_list = get_treasury_payments(company_id)
    cash_position = calculate_daily_cash_position(company_id)
    
    total_required = sum(p.get('open_amount', 0) for p in payments_list)
    available_cash = cash_position['total_position']
    
    return render_template('finance/treasury/payments_cash_requirement.html',
        title='Cash Requirement View',
        payments=payments_list,
        total_required=total_required,
        available_cash=available_cash,
        shortfall=max(0, total_required - available_cash)
    )


# ============================================================================
# TRANSFERS
# ============================================================================

@treasury_bp.route('/transfers')
def transfers_list():
    """List transfer requests."""
    company_id = get_company_id()
    
    from treasury_models import get_transfer_requests
    
    status = request.args.get('status')
    request_type = request.args.get('request_type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    transfers = get_transfer_requests(
        company_id, status=status, request_type=request_type,
        start_date=start_date, end_date=end_date
    )
    
    return render_template('finance/treasury/transfers_list.html',
        title='Transfer Requests',
        transfers=transfers,
        filters={'status': status, 'request_type': request_type, 'start_date': start_date, 'end_date': end_date}
    )


@treasury_bp.route('/transfers/create', methods=['GET', 'POST'])
def transfers_create():
    """Create transfer request."""
    if request.method == 'POST':
        from treasury_models import create_transfer_request, log_treasury_audit
        from treasury_models import get_bank_accounts, get_petty_cash_accounts
        
        from_account_type = request.form.get('from_account_type')
        to_account_type = request.form.get('to_account_type')
        
        from_bank_id = None
        from_petty_id = None
        to_bank_id = None
        to_petty_id = None
        
        if from_account_type == 'bank':
            from_bank_id = request.form.get('from_bank_account_id', type=int)
        elif from_account_type == 'petty_cash':
            from_petty_id = request.form.get('from_petty_cash_id', type=int)
        
        if to_account_type == 'bank':
            to_bank_id = request.form.get('to_bank_account_id', type=int)
        elif to_account_type == 'petty_cash':
            to_petty_id = request.form.get('to_petty_cash_id', type=int)
        
        data = {
            'request_type': request.form.get('request_type', 'bank_transfer'),
            'transfer_date': request.form.get('transfer_date'),
            'from_account_type': from_account_type,
            'from_bank_account_id': from_bank_id,
            'from_petty_cash_id': from_petty_id,
            'to_account_type': to_account_type,
            'to_bank_account_id': to_bank_id,
            'to_petty_cash_id': to_petty_id,
            'amount': request.form.get('amount', type=float),
            'currency': request.form.get('currency', 'AED'),
            'reference': request.form.get('reference'),
            'reason': request.form.get('reason'),
            'urgency': request.form.get('urgency', 'normal'),
            'entity_id': request.form.get('entity_id', type=int),
            'branch_id': request.form.get('branch_id', type=int),
            'company_id': get_company_id(),
            'created_by': get_current_user_id()
        }
        
        transfer_id = create_transfer_request(data)
        log_treasury_action('create', 'transfer_request', transfer_id, f'Transfer: {data["amount"]}')
        
        # Send alert if high value
        if data['amount'] >= 500000:
            send_treasury_flow_alert(
                'high_value_transfer',
                'High Value Transfer Request',
                f'Transfer request for {data["amount"]:,.2f} {data["currency"]} requires approval',
                severity='high',
                amount=data['amount']
            )
        
        flash('Transfer request created successfully', 'success')
        return redirect(url_for('treasury.transfers_list'))
    
    from treasury_models import get_bank_accounts, get_petty_cash_accounts
    
    bank_accounts = get_bank_accounts(company_id=get_company_id(), is_active=True)
    petty_cash = get_petty_cash_accounts(company_id=get_company_id(), is_active=True)
    
    return render_template('finance/treasury/transfer_create.html',
        title='Create Transfer Request',
        bank_accounts=bank_accounts,
        petty_cash=petty_cash
    )


@treasury_bp.route('/transfers/<int:transfer_id>')
def transfer_detail(transfer_id):
    """View transfer request detail."""
    from treasury_models import get_transfer_request_by_id
    
    transfer = get_transfer_request_by_id(transfer_id)
    if not transfer:
        flash('Transfer request not found', 'error')
        return redirect(url_for('treasury.transfers_list'))
    
    return render_template('finance/treasury/transfer_detail.html',
        title=f'Transfer: {transfer["request_number"]}',
        transfer=transfer
    )


@treasury_bp.route('/transfers/<int:transfer_id>/approve', methods=['POST'])
def transfer_approve(transfer_id):
    """Approve transfer request."""
    from treasury_models import approve_transfer_request, log_treasury_audit, get_transfer_request_by_id
    
    transfer = get_transfer_request_by_id(transfer_id)
    approve_transfer_request(transfer_id, get_current_user_id())
    log_treasury_action('approve', 'transfer_request', transfer_id, transfer['request_number'])
    
    send_treasury_flow_alert(
        'transfer_approved',
        'Transfer Approved',
        f'Transfer {transfer["request_number"]} for {transfer["amount"]:,.2f} {transfer["currency"]} has been approved',
        severity='medium',
        amount=transfer['amount']
    )
    
    flash('Transfer approved successfully', 'success')
    return redirect(url_for('treasury.transfers_list'))


@treasury_bp.route('/transfers/<int:transfer_id>/reject', methods=['POST'])
def transfer_reject(transfer_id):
    """Reject transfer request."""
    from treasury_models import reject_transfer_request, log_treasury_audit, get_transfer_request_by_id
    
    reason = request.form.get('reason')
    transfer = get_transfer_request_by_id(transfer_id)
    
    reject_transfer_request(transfer_id, get_current_user_id(), reason)
    log_treasury_action('reject', 'transfer_request', transfer_id, transfer['request_number'])
    flash('Transfer rejected', 'info')
    return redirect(url_for('treasury.transfers_list'))


# ============================================================================
# BANK RECONCILIATION
# ============================================================================

@treasury_bp.route('/reconciliation')
def reconciliation():
    """Bank Reconciliation workspace."""
    company_id = get_company_id()
    
    from treasury_models import get_bank_reconciliation_status
    
    bank_account_id = request.args.get('bank_account_id', type=int)
    status = get_bank_reconciliation_status(company_id, bank_account_id)
    
    return render_template('finance/treasury/reconciliation.html',
        title='Bank Reconciliation',
        reconciliation_status=status
    )


@treasury_bp.route('/reconciliation/<int:bank_account_id>')
def reconciliation_detail(bank_account_id):
    """Reconciliation detail for a bank account."""
    from treasury_models import get_unreconciled_transactions, get_bank_reconciliation_status
    from finance_models import get_bank_account_by_id
    
    bank = get_bank_account_by_id(bank_account_id)
    if not bank:
        flash('Bank account not found', 'error')
        return redirect(url_for('treasury.reconciliation'))
    
    unreconciled = get_unreconciled_transactions(get_company_id(), bank_account_id)
    
    return render_template('finance/treasury/reconciliation_detail.html',
        title=f'Reconciliation: {bank["account_name"]}',
        bank=bank,
        unreconciled=unreconciled
    )


# ============================================================================
# TREASURY CONTROLS
# ============================================================================

@treasury_bp.route('/controls')
def controls():
    """Treasury Controls view."""
    company_id = get_company_id()
    
    from treasury_models import get_treasury_controls, get_treasury_alerts
    
    control_type = request.args.get('control_type')
    controls = get_treasury_controls(company_id=company_id, control_type=control_type)
    recent_alerts = get_treasury_alerts(company_id, start_date=(datetime.now() - timedelta(days=7)).date().isoformat())
    
    return render_template('finance/treasury/controls.html',
        title='Treasury Controls',
        controls=controls,
        recent_alerts=recent_alerts[:10],
        filters={'control_type': control_type}
    )


@treasury_bp.route('/controls/create', methods=['GET', 'POST'])
def control_create():
    """Create treasury control."""
    if request.method == 'POST':
        from treasury_models import create_treasury_control, log_treasury_audit
        
        data = {
            'control_name': request.form.get('control_name'),
            'control_type': request.form.get('control_type'),
            'control_category': request.form.get('control_category'),
            'description': request.form.get('description'),
            'control_rule': request.form.get('control_rule'),
            'threshold_value': request.form.get('threshold_value', type=float),
            'threshold_operator': request.form.get('threshold_operator'),
            'affected_operations': request.form.get('affected_operations'),
            'severity': request.form.get('severity', 'medium'),
            'company_id': get_company_id()
        }
        
        control_id = create_treasury_control(data)
        log_treasury_action('create', 'treasury_control', control_id, data['control_name'])
        flash('Treasury control created successfully', 'success')
        return redirect(url_for('treasury.controls'))
    
    return render_template('finance/treasury/control_create.html',
        title='Create Treasury Control'
    )


# ============================================================================
# TREASURY ALERTS
# ============================================================================

@treasury_bp.route('/alerts')
def alerts():
    """Treasury Alerts view."""
    company_id = get_company_id()
    
    from treasury_models import get_treasury_alerts, get_unread_alert_count
    
    is_read = None if request.args.get('is_read') == 'all' else False
    severity = request.args.get('severity')
    alert_type = request.args.get('alert_type')
    
    alerts = get_treasury_alerts(
        company_id, is_read=is_read, severity=severity,
        alert_type=alert_type
    )
    
    unread_count = get_unread_alert_count(company_id)
    
    return render_template('finance/treasury/alerts.html',
        title='Treasury Alerts',
        alerts=alerts,
        unread_count=unread_count,
        filters={'is_read': request.args.get('is_read'), 'severity': severity, 'alert_type': alert_type}
    )


@treasury_bp.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
def alert_resolve(alert_id):
    """Resolve a treasury alert."""
    from treasury_models import resolve_treasury_alert, log_treasury_audit
    
    notes = request.form.get('resolution_notes')
    resolve_treasury_alert(alert_id, get_current_user_id(), notes)
    log_treasury_action('resolve', 'treasury_alert', alert_id)
    flash('Alert resolved', 'success')
    return redirect(url_for('treasury.alerts'))


@treasury_bp.route('/alerts/mark-read/<int:alert_id>', methods=['POST'])
def alert_mark_read(alert_id):
    """Mark alert as read."""
    from database import get_db_context
    
    with get_db_context() as db:
        db.execute("UPDATE treasury_alerts SET is_read = 1 WHERE id = ?", (alert_id,))
        db.commit()
    
    return jsonify({'success': True})


# ============================================================================
# LIQUIDITY PLANNING
# ============================================================================

@treasury_bp.route('/liquidity')
def liquidity():
    """Liquidity Planning view."""
    company_id = get_company_id()
    
    from treasury_models import analyze_liquidity_position, get_liquidity_thresholds, get_cash_flow_forecast_data
    
    liquidity_analysis = analyze_liquidity_position(company_id)
    thresholds = get_liquidity_thresholds(company_id=company_id)
    forecast_30day = get_cash_flow_forecast_data(company_id, days=30)
    
    # Calculate daily liquidity forecast
    daily_forecast = []
    running_balance = liquidity_analysis['current_position']['total_position']
    
    for date_str, data in forecast_30day['forecast'].items():
        running_balance += data['net']
        daily_forecast.append({
            'date': date_str,
            'inflow': data['inflow'],
            'outflow': data['outflow'],
            'net': data['net'],
            'projected_balance': running_balance,
            'above_minimum': running_balance > liquidity_analysis['minimum_required']
        })
    
    return render_template('finance/treasury/liquidity.html',
        title='Liquidity Planning',
        liquidity=liquidity_analysis,
        thresholds=thresholds,
        daily_forecast=daily_forecast[:30]
    )


@treasury_bp.route('/liquidity/gaps')
def liquidity_gaps():
    """Liquidity gaps view."""
    company_id = get_company_id()
    
    from treasury_models import analyze_liquidity_position, get_cash_flow_forecast_data
    
    liquidity = analyze_liquidity_position(company_id)
    forecast = get_cash_flow_forecast_data(company_id, days=30)
    
    gaps = []
    running_balance = liquidity['current_position']['total_position']
    
    for date_str, data in forecast['forecast'].items():
        running_balance += data['net']
        min_required = liquidity['minimum_required']
        
        if running_balance < min_required:
            gaps.append({
                'date': date_str,
                'projected_balance': running_balance,
                'minimum_required': min_required,
                'gap': min_required - running_balance
            })
    
    return render_template('finance/treasury/liquidity_gaps.html',
        title='Liquidity Gaps',
        gaps=gaps,
        liquidity=liquidity
    )


# ============================================================================
# TREASURY REPORTS
# ============================================================================

@treasury_bp.route('/reports')
def reports():
    """Treasury Reports menu."""
    return render_template('finance/treasury/reports.html',
        title='Treasury Reports'
    )


@treasury_bp.route('/reports/cash-position')
def report_cash_position():
    """Cash Position Report."""
    company_id = get_company_id()
    
    from treasury_models import calculate_daily_cash_position, get_bank_accounts
    from treasury_models import get_treasury_petty_cash_accounts, get_cash_boxes
    
    cash_position = calculate_daily_cash_position(company_id)
    bank_accounts = get_bank_accounts(company_id=company_id, is_active=True)
    petty_cash = get_treasury_petty_cash_accounts(company_id=company_id, is_active=True)
    cash_boxes = get_cash_boxes(company_id=company_id, is_active=True)
    
    return render_template('finance/treasury/reports/cash_position_report.html',
        title='Cash Position Report',
        cash_position=cash_position,
        bank_accounts=bank_accounts,
        petty_cash=petty_cash,
        cash_boxes=cash_boxes,
        generated_date=datetime.now().isoformat()
    )


@treasury_bp.route('/reports/cash-flow')
def report_cash_flow():
    """Cash Flow Report."""
    company_id = get_company_id()
    
    from treasury_models import get_cash_flow_forecast_data
    
    forecast_30day = get_cash_flow_forecast_data(company_id, days=30)
    forecast_90day = get_cash_flow_forecast_data(company_id, days=90)
    
    return render_template('finance/treasury/reports/cash_flow_report.html',
        title='Cash Flow Report',
        forecast_30=forecast_30day,
        forecast_90=forecast_90day,
        generated_date=datetime.now().isoformat()
    )


@treasury_bp.route('/reports/collections')
def report_collections():
    """Collections Report."""
    company_id = get_company_id()
    
    from treasury_models import get_treasury_collections, get_collections_summary
    
    collections = get_treasury_collections(company_id)
    summary = get_collections_summary(company_id)
    
    return render_template('finance/treasury/reports/collections_report.html',
        title='Collections Report',
        collections=collections,
        summary=summary,
        generated_date=datetime.now().isoformat()
    )


@treasury_bp.route('/reports/payments')
def report_payments():
    """Payments Report."""
    company_id = get_company_id()
    
    from treasury_models import get_treasury_payments, get_payments_summary
    
    payments = get_treasury_payments(company_id)
    summary = get_payments_summary(company_id)
    
    return render_template('finance/treasury/reports/payments_report.html',
        title='Payments Report',
        payments=payments,
        summary=summary,
        generated_date=datetime.now().isoformat()
    )


@treasury_bp.route('/reports/liquidity')
def report_liquidity():
    """Liquidity Report."""
    company_id = get_company_id()
    
    from treasury_models import analyze_liquidity_position, get_liquidity_thresholds
    
    liquidity = analyze_liquidity_position(company_id)
    thresholds = get_liquidity_thresholds(company_id=company_id)
    
    return render_template('finance/treasury/reports/liquidity_report.html',
        title='Liquidity Report',
        liquidity=liquidity,
        thresholds=thresholds,
        generated_date=datetime.now().isoformat()
    )


@treasury_bp.route('/reports/forecast-vs-actual')
def report_forecast_vs_actual():
    """Forecast vs Actual Report."""
    company_id = get_company_id()
    
    from treasury_models import get_cash_position_snapshots, get_cash_flow_forecast_data
    
    end_date = datetime.now().date().isoformat()
    start_date = (datetime.now().date() - timedelta(days=30)).isoformat()
    actuals = get_cash_position_snapshots(company_id, start_date=start_date, end_date=end_date)
    forecast = get_cash_flow_forecast_data(company_id, days=30)
    
    return render_template('finance/treasury/reports/forecast_vs_actual_report.html',
        title='Forecast vs Actual Report',
        actuals=actuals,
        forecast=forecast,
        generated_date=datetime.now().isoformat()
    )


@treasury_bp.route('/reports/alerts')
def report_alerts():
    """Treasury Alerts Report."""
    company_id = get_company_id()
    
    from treasury_models import get_treasury_alerts
    
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).date().isoformat())
    end_date = request.args.get('end_date', datetime.now().date().isoformat())
    
    alerts = get_treasury_alerts(company_id, start_date=start_date, end_date=end_date)
    
    return render_template('finance/treasury/reports/alerts_report.html',
        title='Treasury Alerts Report',
        alerts=alerts,
        filters={'start_date': start_date, 'end_date': end_date},
        generated_date=datetime.now().isoformat()
    )


@treasury_bp.route('/reports/audit')
def report_audit():
    """Treasury Audit Report."""
    company_id = get_company_id()
    
    from treasury_models import get_treasury_audit_log
    
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).date().isoformat())
    end_date = request.args.get('end_date', datetime.now().date().isoformat())
    entity_type = request.args.get('entity_type')
    
    audit_log = get_treasury_audit_log(
        company_id, entity_type=entity_type,
        start_date=start_date, end_date=end_date
    )
    
    return render_template('finance/treasury/reports/audit_report.html',
        title='Treasury Audit Report',
        audit_log=audit_log,
        filters={'start_date': start_date, 'end_date': end_date, 'entity_type': entity_type},
        generated_date=datetime.now().isoformat()
    )


# ============================================================================
# WORKFLOW & APPROVALS
# ============================================================================

@treasury_bp.route('/approvals')
def approvals():
    """Pending Treasury Approvals."""
    company_id = get_company_id()
    
    from treasury_models import get_transfer_requests, get_treasury_forecasts
    
    pending_transfers = get_transfer_requests(company_id, status='Pending')
    pending_forecasts = get_treasury_forecasts(company_id, status='Draft')
    
    return render_template('finance/treasury/approvals.html',
        title='Pending Approvals',
        pending_transfers=pending_transfers,
        pending_forecasts=pending_forecasts
    )


@treasury_bp.route('/audit-log')
def audit_log():
    """Treasury Audit Log."""
    company_id = get_company_id()
    
    from treasury_models import get_treasury_audit_log
    
    entity_type = request.args.get('entity_type')
    user_id = request.args.get('user_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    audit_log = get_treasury_audit_log(
        company_id, entity_type=entity_type,
        user_id=user_id, start_date=start_date, end_date=end_date
    )
    
    return render_template('finance/treasury/audit_log.html',
        title='Treasury Audit Log',
        audit_log=audit_log,
        filters={'entity_type': entity_type, 'user_id': user_id, 'start_date': start_date, 'end_date': end_date}
    )


# ============================================================================
# SETTINGS
# ============================================================================

@treasury_bp.route('/settings')
def settings():
    """Treasury Settings."""
    company_id = get_company_id()
    
    from treasury_models import get_treasury_settings, get_liquidity_thresholds, get_treasury_controls
    
    settings_dict = {}
    all_settings = get_treasury_settings(company_id=company_id)
    for s in all_settings:
        settings_dict[s['setting_key']] = s['setting_value']
    
    thresholds = get_liquidity_thresholds(company_id=company_id)
    controls = get_treasury_controls(company_id=company_id)
    
    return render_template('finance/treasury/settings.html',
        title='Treasury Settings',
        settings=settings_dict,
        thresholds=thresholds,
        controls=controls
    )


@treasury_bp.route('/settings/update', methods=['POST'])
def settings_update():
    """Update treasury settings."""
    from treasury_models import set_treasury_setting, log_treasury_audit
    
    setting_key = request.form.get('setting_key')
    setting_value = request.form.get('setting_value')
    
    set_treasury_setting(setting_key, setting_value, get_company_id())
    log_treasury_action('update', 'treasury_settings', None, setting_key)
    
    flash('Settings updated successfully', 'success')
    return redirect(url_for('treasury.settings'))


# ============================================================================
# API ENDPOINTS
# ============================================================================

@treasury_bp.route('/api/alerts/unread-count')
def api_unread_alerts():
    """Get unread alert count for API."""
    from treasury_models import get_unread_alert_count
    count = get_unread_alert_count(get_company_id())
    return jsonify({'count': count})


@treasury_bp.route('/api/cash-position/summary')
def api_cash_position_summary():
    """Get cash position summary for API."""
    from treasury_models import calculate_daily_cash_position
    position = calculate_daily_cash_position(get_company_id())
    return jsonify(position)


@treasury_bp.route('/api/forecast/summary')
def api_forecast_summary():
    """Get forecast summary for API."""
    from treasury_models import get_cash_flow_forecast_data
    
    days = request.args.get('days', 30, type=int)
    forecast = get_cash_flow_forecast_data(get_company_id(), days=days)
    
    total_inflow = sum(d['inflow'] for d in forecast['forecast'].values())
    total_outflow = sum(d['outflow'] for d in forecast['forecast'].values())
    
    return jsonify({
        'total_inflow': total_inflow,
        'total_outflow': total_outflow,
        'net': total_inflow - total_outflow,
        'days': days
    })


# ============================================================================
# EXECUTIVE DASHBOARD (CFO View)
# ============================================================================

@treasury_bp.route('/executive-dashboard')
def executive_dashboard():
    """Executive Liquidity Dashboard for CFO."""
    company_id = get_company_id()
    
    from treasury_models import (
        calculate_daily_cash_position, analyze_liquidity_position,
        get_treasury_alerts, get_collections_summary, get_payments_summary,
        get_cash_flow_forecast_data, get_bank_accounts, get_treasury_controls,
        get_unread_alert_count, get_critical_alerts
    )
    
    # Cash position
    cash_position = calculate_daily_cash_position(company_id)
    
    # Liquidity analysis
    liquidity = analyze_liquidity_position(company_id)
    
    # Alerts
    unread_alerts = get_unread_alert_count(company_id)
    critical_alerts = get_critical_alerts(company_id)
    
    # Collections & Payments summaries
    collections_summary = get_collections_summary(company_id)
    payments_summary = get_payments_summary(company_id)
    
    # Forecasts
    forecast_30day = get_cash_flow_forecast_data(company_id, days=30)
    total_30day_inflow = sum(d['inflow'] for d in forecast_30day['forecast'].values())
    total_30day_outflow = sum(d['outflow'] for d in forecast_30day['forecast'].values())
    total_30day_net = total_30day_inflow - total_30day_outflow
    
    # Bank accounts summary
    bank_accounts = get_bank_accounts(company_id=company_id, is_active=True)
    
    # Controls status
    controls = get_treasury_controls(company_id=company_id)
    critical_controls = [c for c in controls if c.get('severity') == 'critical']
    
    # KPI cards data
    kpis = {
        'total_cash': cash_position['total_position'],
        'cash_available': cash_position['total_position'],
        'projected_30day_inflow': total_30day_inflow,
        'projected_30day_outflow': total_30day_outflow,
        'projected_30day_net': total_30day_net,
        'collections_at_risk': collections_summary.get('high_risk_amount', 0),
        'payments_due': payments_summary.get('total_open_amount', 0),
        'pending_approvals': len([c for c in critical_alerts if not c.get('is_resolved')]),
        'liquidity_ratio': 1.5 if liquidity['liquidity_status'] == 'healthy' else 1.0,
        'liquidity_status': liquidity['liquidity_status']
    }
    
    # Chart data for 30-day forecast
    forecast_labels = list(forecast_30day['forecast'].keys())[-14:]  # Last 14 days
    inflow_data = [forecast_30day['forecast'][d]['inflow'] for d in forecast_labels]
    outflow_data = [forecast_30day['forecast'][d]['outflow'] for d in forecast_labels]
    
    # Currency breakdown
    currency_breakdown = []
    for currency, data in cash_position['by_currency'].items():
        currency_breakdown.append({
            'currency': currency,
            'amount': data['total_balance'],
            'percentage': (data['total_balance'] / cash_position['total_position'] * 100) if cash_position['total_position'] > 0 else 0
        })
    
    return render_template('finance/treasury/executive_dashboard.html',
        title='Executive Liquidity Dashboard',
        kpis=kpis,
        cash_position=cash_position,
        liquidity=liquidity,
        unread_alerts=unread_alerts,
        critical_alerts=critical_alerts,
        collections_summary=collections_summary,
        payments_summary=payments_summary,
        bank_accounts=bank_accounts,
        controls=controls,
        critical_controls=critical_controls,
        currency_breakdown=currency_breakdown,
        forecast_labels=json.dumps(forecast_labels),
        inflow_data=json.dumps(inflow_data),
        outflow_data=json.dumps(outflow_data)
    )


# ============================================================================
# BANK STATEMENT IMPORT & RECONCILIATION
# ============================================================================

@treasury_bp.route('/bank-statements')
def bank_statements():
    """Bank Statements list."""
    company_id = get_company_id()
    
    from treasury_models import get_bank_statements, get_bank_accounts
    
    bank_account_id = request.args.get('bank_account_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    statements = get_bank_statements(
        company_id=company_id,
        bank_account_id=bank_account_id,
        start_date=start_date,
        end_date=end_date
    )
    
    bank_accounts = get_bank_accounts(company_id=company_id, is_active=True)
    
    return render_template('finance/treasury/bank_statements.html',
        title='Bank Statements',
        statements=statements,
        bank_accounts=bank_accounts,
        filters={'bank_account_id': bank_account_id, 'start_date': start_date, 'end_date': end_date}
    )


@treasury_bp.route('/bank-statements/import', methods=['GET', 'POST'])
def bank_statement_import():
    """Import bank statement."""
    company_id = get_company_id()
    
    from treasury_models import create_bank_statement, create_bank_statement_line, log_treasury_audit
    from finance_models import get_bank_accounts
    
    if request.method == 'POST':
        bank_account_id = request.form.get('bank_account_id', type=int)
        statement_date = request.form.get('statement_date')
        statement_number = request.form.get('statement_number')
        opening_balance = request.form.get('opening_balance', type=float)
        closing_balance = request.form.get('closing_balance', type=float)
        file_name = request.files.get('statement_file').filename if request.files.get('statement_file') else None
        
        statement_id = create_bank_statement({
            'bank_account_id': bank_account_id,
            'statement_date': statement_date,
            'statement_number': statement_number,
            'opening_balance': opening_balance or 0,
            'closing_balance': closing_balance or 0,
            'total_credits': request.form.get('total_credits', 0, type=float),
            'total_debits': request.form.get('total_debits', 0, type=float),
            'file_name': file_name,
            'file_type': 'MT940',
            'imported_by': get_current_user_id(),
            'company_id': company_id
        })
        
        log_treasury_action('import', 'bank_statement', statement_id, statement_number)
        flash('Bank statement imported successfully', 'success')
        return redirect(url_for('treasury.bank_statement_detail', statement_id=statement_id))
    
    bank_accounts = get_bank_accounts(company_id=company_id, is_active=True)
    
    return render_template('finance/treasury/bank_statement_import.html',
        title='Import Bank Statement',
        bank_accounts=bank_accounts
    )


@treasury_bp.route('/bank-statements/<int:statement_id>')
def bank_statement_detail(statement_id):
    """View bank statement detail."""
    from treasury_models import get_bank_statements, get_bank_statement_lines
    
    statements = get_bank_statements()
    statement = next((s for s in statements if s['id'] == statement_id), None)
    
    if not statement:
        flash('Statement not found', 'error')
        return redirect(url_for('treasury.bank_statements'))
    
    lines = get_bank_statement_lines(statement_id)
    
    return render_template('finance/treasury/bank_statement_detail.html',
        title=f'Statement: {statement.get("statement_number", statement_id)}',
        statement=statement,
        lines=lines
    )


@treasury_bp.route('/bank-statements/api/parse-mt940', methods=['POST'])
def api_parse_mt940():
    """Parse MT940 bank statement file."""
    from treasury_models import create_bank_statement, create_bank_statement_line
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    bank_account_id = request.form.get('bank_account_id', type=int)
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    company_id = get_company_id()
    
    statement_date = datetime.now().date().isoformat()
    statement_id = create_bank_statement({
        'bank_account_id': bank_account_id,
        'statement_date': statement_date,
        'statement_number': f'MT940-{datetime.now().strftime("%Y%m%d%H%M%S")}',
        'opening_balance': 0,
        'closing_balance': 0,
        'file_name': file.filename,
        'file_type': 'MT940',
        'imported_by': get_current_user_id(),
        'company_id': company_id
    })
    
    lines_content = file.read().decode('utf-8')
    
    total_credits = 0
    total_debits = 0
    
    for line_data in lines_content.split('\n'):
        if line_data.strip():
            parts = line_data.split(',')
            if len(parts) >= 4:
                amount = float(parts[3]) if parts[3] else 0
                debit_credit = 'C' if amount > 0 else 'D'
                
                line_id = create_bank_statement_line({
                    'statement_id': statement_id,
                    'line_reference': parts[0] if len(parts) > 0 else '',
                    'transaction_date': parts[1] if len(parts) > 1 else statement_date,
                    'value_date': parts[2] if len(parts) > 2 else parts[1] if len(parts) > 1 else statement_date,
                    'description': parts[4] if len(parts) > 4 else '',
                    'reference': parts[5] if len(parts) > 5 else '',
                    'amount': abs(amount),
                    'transaction_type': 'CREDIT' if debit_credit == 'C' else 'DEBIT',
                    'debit_credit': debit_credit,
                    'bank_reference': '',
                    'counterparty_name': '',
                    'company_id': company_id
                })
                
                if debit_credit == 'C':
                    total_credits += abs(amount)
                else:
                    total_debits += abs(amount)
    
    with get_db_context() as db:
        closing = float(db.execute(
            "SELECT closing_balance FROM treasury_bank_statements WHERE id = ?", (statement_id,)
        ).fetchone()['closing_balance'] or 0) + total_credits - total_debits
        db.execute("""
            UPDATE treasury_bank_statements 
            SET total_credits = ?, total_debits = ?, closing_balance = ?
            WHERE id = ?
        """, (total_credits, total_debits, closing, statement_id))
        db.commit()
    
    return jsonify({
        'success': True,
        'statement_id': statement_id,
        'lines_imported': len(lines_content.split('\n')),
        'total_credits': total_credits,
        'total_debits': total_debits
    })


@treasury_bp.route('/reconciliation/api/match', methods=['POST'])
def api_match_transaction():
    """Match a statement line to a journal entry."""
    from treasury_models import match_statement_line
    
    data = request.get_json()
    line_id = data.get('line_id')
    journal_id = data.get('journal_id')
    matched_amount = data.get('matched_amount')
    
    if not all([line_id, journal_id, matched_amount]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    match_statement_line(line_id, journal_id, matched_amount, get_current_user_id())
    
    return jsonify({'success': True})


@treasury_bp.route('/reconciliation/api/unmatch', methods=['POST'])
def api_unmatch_transaction():
    """Unmatch a previously matched statement line."""
    from treasury_models import unmatch_statement_line
    
    data = request.get_json()
    line_id = data.get('line_id')
    
    if not line_id:
        return jsonify({'error': 'Missing line_id'}), 400
    
    unmatch_statement_line(line_id, get_current_user_id())
    
    return jsonify({'success': True})


@treasury_bp.route('/reconciliation/api/unmatched-lines/<int:bank_account_id>')
def api_unmatched_lines(bank_account_id):
    """Get unreconciled lines for a bank account."""
    from treasury_models import get_unreconciled_lines
    
    lines = get_unreconciled_lines(bank_account_id, get_company_id())
    
    return jsonify({
        'lines': [{
            'id': l['id'],
            'transaction_date': l['transaction_date'],
            'description': l['description'],
            'amount': l['amount'],
            'debit_credit': l['debit_credit']
        } for l in lines]
    })


# ============================================================================
# PAYMENT RUNS
# ============================================================================

@treasury_bp.route('/payment-runs')
def payment_runs():
    """Payment runs list."""
    company_id = get_company_id()
    
    from treasury_models import get_payment_runs, get_bank_accounts
    
    status = request.args.get('status')
    bank_account_id = request.args.get('bank_account_id', type=int)
    
    runs = get_payment_runs(company_id, status=status, bank_account_id=bank_account_id)
    bank_accounts = get_bank_accounts(company_id=company_id, is_active=True)
    
    return render_template('finance/treasury/payment_runs.html',
        title='Payment Runs',
        payment_runs=runs,
        bank_accounts=bank_accounts,
        filters={'status': status, 'bank_account_id': bank_account_id}
    )


@treasury_bp.route('/payment-runs/create', methods=['GET', 'POST'])
def payment_run_create():
    """Create a new payment run."""
    company_id = get_company_id()
    
    from treasury_models import create_payment_run, add_payment_run_item, calculate_payment_run_totals
    from treasury_models import get_bank_accounts, get_payment_runs
    from finance_models import get_supplier_bills
    
    if request.method == 'POST':
        run_id = create_payment_run({
            'run_name': request.form.get('run_name'),
            'run_date': request.form.get('run_date'),
            'bank_account_id': request.form.get('bank_account_id', type=int),
            'payment_type': request.form.get('payment_type'),
            'currency': request.form.get('currency', 'AED'),
            'payment_method': request.form.get('payment_method'),
            'scheduled_date': request.form.get('scheduled_date'),
            'company_id': company_id
        })
        
        selected_bills = request.form.getlist('selected_bills')
        for bill_id in selected_bills:
            bill = next((b for b in get_supplier_bills(company_id) if b['id'] == int(bill_id)), None)
            if bill:
                add_payment_run_item(run_id, {
                    'source_type': 'supplier_bill',
                    'source_id': bill['id'],
                    'payee_name': bill.get('supplier_name'),
                    'payee_account': '',
                    'payee_bank': '',
                    'description': f'Payment for Bill #{bill.get("bill_number")}',
                    'amount': float(bill.get('total_amount', 0)) - float(bill.get('amount_paid', 0)),
                    'currency': bill.get('currency', 'AED'),
                    'priority': 5,
                    'due_date': bill.get('due_date'),
                    'company_id': company_id
                })
        
        calculate_payment_run_totals(run_id)
        log_treasury_action('create', 'payment_run', run_id, request.form.get('run_name'))
        flash('Payment run created successfully', 'success')
        return redirect(url_for('treasury.payment_run_detail', run_id=run_id))
    
    bank_accounts = get_bank_accounts(company_id=company_id, is_active=True)
    pending_bills = [b for b in get_supplier_bills(company_id) 
                     if float(b.get('total_amount', 0)) > float(b.get('amount_paid', 0))]
    
    return render_template('finance/treasury/payment_run_create.html',
        title='Create Payment Run',
        bank_accounts=bank_accounts,
        pending_bills=pending_bills
    )


@treasury_bp.route('/payment-runs/<int:run_id>')
def payment_run_detail(run_id):
    """View payment run detail."""
    from treasury_models import get_payment_runs, get_payment_run_items, calculate_payment_run_totals
    
    runs = get_payment_runs(get_company_id())
    run = next((r for r in runs if r['id'] == run_id), None)
    
    if not run:
        flash('Payment run not found', 'error')
        return redirect(url_for('treasury.payment_runs'))
    
    items = get_payment_run_items(run_id)
    
    return render_template('finance/treasury/payment_run_detail.html',
        title=f'Payment Run: {run.get("run_number")}',
        run=run,
        items=items
    )


@treasury_bp.route('/payment-runs/<int:run_id>/approve', methods=['POST'])
def payment_run_approve(run_id):
    """Approve a payment run."""
    from treasury_models import update_payment_run_status, log_treasury_audit, get_payment_runs
    
    runs = get_payment_runs(get_company_id())
    run = next((r for r in runs if r['id'] == run_id), None)
    
    update_payment_run_status(run_id, 'approved', get_current_user_id())
    log_treasury_action('approve', 'payment_run', run_id, run.get('run_number') if run else str(run_id))
    
    send_treasury_flow_alert(
        'payment_run_approved',
        'Payment Run Approved',
        f'Payment run {run.get("run_number") if run else run_id} has been approved',
        severity='high',
        amount=run.get('total_amount') if run else 0
    )
    
    flash('Payment run approved', 'success')
    return redirect(url_for('treasury.payment_run_detail', run_id=run_id))


@treasury_bp.route('/payment-runs/<int:run_id>/reject', methods=['POST'])
def payment_run_reject(run_id):
    """Reject a payment run."""
    from treasury_models import update_payment_run_status, log_treasury_audit
    
    reason = request.form.get('reason')
    update_payment_run_status(run_id, 'rejected', get_current_user_id(), reason)
    log_treasury_action('reject', 'payment_run', run_id, str(run_id))
    
    flash('Payment run rejected', 'info')
    return redirect(url_for('treasury.payment_runs'))


@treasury_bp.route('/payment-runs/<int:run_id>/execute', methods=['POST'])
def payment_run_execute(run_id):
    """Execute a payment run."""
    from treasury_models import update_payment_run_status, log_treasury_audit, get_payment_runs
    
    runs = get_payment_runs(get_company_id())
    run = next((r for r in runs if r['id'] == run_id), None)
    
    update_payment_run_status(run_id, 'executed', get_current_user_id())
    log_treasury_action('execute', 'payment_run', run_id, run.get('run_number') if run else str(run_id))
    
    send_treasury_flow_alert(
        'payment_run_executed',
        'Payment Run Executed',
        f'Payment run {run.get("run_number") if run else run_id} has been executed',
        severity='high',
        amount=run.get('total_amount') if run else 0
    )
    
    flash('Payment run executed successfully', 'success')
    return redirect(url_for('treasury.payment_runs'))


# ============================================================================
# FX CONTRACTS
# ============================================================================

@treasury_bp.route('/fx-contracts')
def fx_contracts():
    """FX Contracts list."""
    company_id = get_company_id()
    
    from treasury_models import get_fx_contracts
    
    status = request.args.get('status')
    currency = request.args.get('currency')
    
    contracts = get_fx_contracts(company_id, status=status, currency=currency)
    
    return render_template('finance/treasury/fx_contracts.html',
        title='FX Contracts',
        contracts=contracts,
        filters={'status': status, 'currency': currency}
    )


@treasury_bp.route('/fx-contracts/create', methods=['GET', 'POST'])
def fx_contract_create():
    """Create FX contract."""
    company_id = get_company_id()
    
    from treasury_models import create_fx_contract, log_treasury_audit
    
    if request.method == 'POST':
        base_currency = request.form.get('base_currency')
        quote_currency = request.form.get('quote_currency')
        base_amount = request.form.get('base_amount', type=float)
        exchange_rate = request.form.get('exchange_rate', type=float)
        quote_amount = base_amount * exchange_rate
        
        contract_id = create_fx_contract({
            'contract_type': request.form.get('contract_type', 'spot'),
            'buy_sell': request.form.get('buy_sell'),
            'base_currency': base_currency,
            'quote_currency': quote_currency,
            'base_amount': base_amount,
            'quote_amount': quote_amount,
            'exchange_rate': exchange_rate,
            'spot_rate': request.form.get('spot_rate', type=float),
            'forward_points': request.form.get('forward_points', type=float),
            'contract_date': request.form.get('contract_date'),
            'value_date': request.form.get('value_date'),
            'maturity_date': request.form.get('maturity_date'),
            'counterparty': request.form.get('counterparty'),
            'counterparty_bank': request.form.get('counterparty_bank'),
            'notes': request.form.get('notes'),
            'company_id': company_id,
            'created_by': get_current_user_id()
        })
        
        log_treasury_action('create', 'fx_contract', contract_id, f'{base_currency}/{quote_currency}')
        flash('FX contract created successfully', 'success')
        return redirect(url_for('treasury.fx_contracts'))
    
    return render_template('finance/treasury/fx_contract_create.html',
        title='Create FX Contract'
    )


@treasury_bp.route('/fx-position')
def fx_position():
    """FX Position view."""
    company_id = get_company_id()
    
    from treasury_models import get_fx_position, get_fx_contracts
    
    position = get_fx_position(company_id)
    contracts = get_fx_contracts(company_id, status='active')
    
    return render_template('finance/treasury/fx_position.html',
        title='FX Position',
        position=position,
        contracts=contracts
    )


@treasury_bp.route('/fx-contracts/<int:contract_id>/settle', methods=['POST'])
def fx_contract_settle(contract_id):
    """Settle an FX contract."""
    from treasury_models import settle_fx_contract, get_fx_contracts, log_treasury_audit
    
    contracts = get_fx_contracts(get_company_id())
    contract = next((c for c in contracts if c['id'] == contract_id), None)
    
    settlement_amount = request.form.get('settlement_amount', type=float)
    gain_loss = request.form.get('gain_loss', type=float)
    
    settle_fx_contract(contract_id, settlement_amount, gain_loss, get_current_user_id())
    log_treasury_action('settle', 'fx_contract', contract_id, contract.get('contract_number') if contract else str(contract_id))
    
    flash('FX contract settled', 'success')
    return redirect(url_for('treasury.fx_contracts'))


# ============================================================================
# CASH POOLING
# ============================================================================

@treasury_bp.route('/cash-pools')
def cash_pools():
    """Cash pools list."""
    company_id = get_company_id()
    
    from treasury_models import get_cash_pools, get_pool_members, calculate_pool_totals
    
    pools = get_cash_pools(company_id)
    
    for pool in pools:
        pool['total_balance'] = calculate_pool_totals(pool['id'])
        pool['members'] = get_pool_members(pool['id'])
    
    return render_template('finance/treasury/cash_pools.html',
        title='Cash Pools',
        pools=pools
    )


@treasury_bp.route('/cash-pools/create', methods=['GET', 'POST'])
def cash_pool_create():
    """Create a cash pool."""
    company_id = get_company_id()
    
    from treasury_models import create_cash_pool, add_pool_member, get_bank_accounts, log_treasury_audit
    
    if request.method == 'POST':
        pool_id = create_cash_pool({
            'pool_name': request.form.get('pool_name'),
            'pool_type': request.form.get('pool_type', 'physical'),
            'pooling_method': request.form.get('pooling_method', 'zero_balance'),
            'master_account_id': request.form.get('master_account_id', type=int),
            'currency': request.form.get('currency', 'AED'),
            'notes': request.form.get('notes'),
            'company_id': company_id
        })
        
        for account_id in request.form.getlist('member_accounts'):
            add_pool_member(pool_id, int(account_id), company_id)
        
        log_treasury_action('create', 'cash_pool', pool_id, request.form.get('pool_name'))
        flash('Cash pool created successfully', 'success')
        return redirect(url_for('treasury.cash_pools'))
    
    bank_accounts = get_bank_accounts(company_id=company_id, is_active=True)
    
    return render_template('finance/treasury/cash_pool_create.html',
        title='Create Cash Pool',
        bank_accounts=bank_accounts
    )


@treasury_bp.route('/cash-pools/<int:pool_id>')
def cash_pool_detail(pool_id):
    """View cash pool detail."""
    from treasury_models import get_cash_pools, get_pool_members, calculate_pool_totals
    
    pools = get_cash_pools(get_company_id())
    pool = next((p for p in pools if p['id'] == pool_id), None)
    
    if not pool:
        flash('Cash pool not found', 'error')
        return redirect(url_for('treasury.cash_pools'))
    
    members = get_pool_members(pool_id)
    total = calculate_pool_totals(pool_id)
    
    return render_template('finance/treasury/cash_pool_detail.html',
        title=f'Cash Pool: {pool["pool_name"]}',
        pool=pool,
        members=members,
        total_balance=total
    )


# ============================================================================
# COLLECTION RISK SCORING
# ============================================================================

@treasury_bp.route('/collection-scores')
def collection_scores():
    """Collection risk scores."""
    company_id = get_company_id()
    
    from treasury_models import get_collection_scores
    
    risk_classification = request.args.get('risk_classification')
    scores = get_collection_scores(company_id, risk_classification=risk_classification)
    
    return render_template('finance/treasury/collection_scores.html',
        title='Collection Risk Scores',
        scores=scores,
        filters={'risk_classification': risk_classification}
    )


@treasury_bp.route('/collection-scores/calculate', methods=['POST'])
def calculate_collection_scores():
    """Calculate collection scores for all customers."""
    from treasury_models import calculate_collection_score, save_collection_score
    from finance_models import get_customers
    
    company_id = get_company_id()
    customers = get_customers(company_id)
    
    calculated = 0
    for customer in customers:
        score = calculate_collection_score(customer['id'], company_id)
        if score:
            score['customer_name'] = customer.get('customer_name', customer.get('name', ''))
            save_collection_score(score)
            calculated += 1
    
    flash(f'Calculated scores for {calculated} customers', 'success')
    return redirect(url_for('treasury.collection_scores'))


# ============================================================================
# DUNNING SETTINGS
# ============================================================================

@treasury_bp.route('/dunning-settings')
def dunning_settings():
    """Dunning settings."""
    company_id = get_company_id()
    
    from treasury_models import get_dunning_settings
    
    settings = get_dunning_settings(company_id)
    
    return render_template('finance/treasury/dunning_settings.html',
        title='Dunning Settings',
        settings=settings
    )


# ============================================================================
# COUNTERPARTIES
# ============================================================================

@treasury_bp.route('/counterparties')
def counterparties():
    """Counterparties list."""
    company_id = get_company_id()
    
    from treasury_models import get_counterparties
    
    counterparty_type = request.args.get('counterparty_type')
    cps = get_counterparties(company_id, counterparty_type=counterparty_type)
    
    return render_template('finance/treasury/counterparties.html',
        title='Counterparties',
        counterparties=cps,
        filters={'counterparty_type': counterparty_type}
    )


@treasury_bp.route('/counterparties/create', methods=['GET', 'POST'])
def counterparty_create():
    """Create counterparty."""
    company_id = get_company_id()
    
    from treasury_models import create_counterparty, log_treasury_audit
    
    if request.method == 'POST':
        cp_id = create_counterparty({
            'counterparty_name': request.form.get('counterparty_name'),
            'counterparty_type': request.form.get('counterparty_type'),
            'bank_name': request.form.get('bank_name'),
            'bank_branch': request.form.get('bank_branch'),
            'account_number': request.form.get('account_number'),
            'iban': request.form.get('iban'),
            'swift_code': request.form.get('swift_code'),
            'routing_number': request.form.get('routing_number'),
            'contact_name': request.form.get('contact_name'),
            'contact_email': request.form.get('contact_email'),
            'contact_phone': request.form.get('contact_phone'),
            'credit_limit': request.form.get('credit_limit', type=float),
            'risk_rating': request.form.get('risk_rating'),
            'payment_terms': request.form.get('payment_terms', type=int),
            'notes': request.form.get('notes'),
            'company_id': company_id
        })
        
        log_treasury_action('create', 'counterparty', cp_id, request.form.get('counterparty_name'))
        flash('Counterparty created successfully', 'success')
        return redirect(url_for('treasury.counterparties'))
    
    return render_template('finance/treasury/counterparty_create.html',
        title='Create Counterparty'
    )


# ============================================================================
# BANK CHARGES
# ============================================================================

@treasury_bp.route('/bank-charges')
def bank_charges():
    """Bank charges view."""
    company_id = get_company_id()
    
    from treasury_models import get_bank_charges, get_bank_accounts
    
    bank_account_id = request.args.get('bank_account_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    charges = get_bank_charges(company_id, bank_account_id=bank_account_id, 
                               start_date=start_date, end_date=end_date)
    bank_accounts = get_bank_accounts(company_id=company_id, is_active=True)
    
    total_charges = sum(c['amount'] for c in charges)
    
    return render_template('finance/treasury/bank_charges.html',
        title='Bank Charges',
        charges=charges,
        bank_accounts=bank_accounts,
        total_charges=total_charges,
        filters={'bank_account_id': bank_account_id, 'start_date': start_date, 'end_date': end_date}
    )


# ============================================================================
# NOTIFICATION PREFERENCES
# ============================================================================

@treasury_bp.route('/notification-preferences', methods=['GET', 'POST'])
def notification_preferences():
    """User notification preferences."""
    from treasury_models import get_user_notification_prefs, set_notification_preference
    
    user_id = get_current_user_id()
    company_id = get_company_id()
    
    if request.method == 'POST':
        alert_type = request.form.get('alert_type')
        channel = request.form.get('channel', 'in_app')
        is_enabled = 1 if request.form.get('is_enabled') else 0
        threshold_amount = request.form.get('threshold_amount', type=float)
        severity_filter = request.form.get('severity_filter')
        
        set_notification_preference({
            'user_id': user_id,
            'alert_type': alert_type,
            'channel': channel,
            'is_enabled': is_enabled,
            'threshold_amount': threshold_amount,
            'severity_filter': severity_filter,
            'company_id': company_id
        })
        
        flash('Notification preferences updated', 'success')
    
    prefs = get_user_notification_prefs(user_id, company_id)
    
    return render_template('finance/treasury/notification_preferences.html',
        title='Notification Preferences',
        preferences=prefs
    )


# ============================================================================
# API ENDPOINTS
# ============================================================================

@treasury_bp.route('/api/cash-position/summary')
def api_cash_position_summary():
    """Get cash position summary API."""
    from treasury_models import calculate_daily_cash_position
    
    position = calculate_daily_cash_position(get_company_id())
    
    return jsonify({
        'total_position': position['total_position'],
        'by_currency': position['by_currency'],
        'bank_balance': position.get('bank_balance', 0),
        'petty_cash_balance': position.get('petty_cash_balance', 0),
        'cash_box_balance': position.get('cash_box_balance', 0)
    })


@treasury_bp.route('/api/liquidity/status')
def api_liquidity_status():
    """Get liquidity status API."""
    from treasury_models import analyze_liquidity_position
    
    liquidity = analyze_liquidity_position(get_company_id())
    
    return jsonify({
        'status': liquidity['liquidity_status'],
        'minimum_required': liquidity['minimum_required'],
        'current_position': liquidity['current_position']['total_position'],
        'issues': liquidity['issues']
    })


@treasury_bp.route('/api/alerts/count')
def api_alerts_count():
    """Get alert counts API."""
    from treasury_models import get_unread_alert_count, get_critical_alerts
    
    company_id = get_company_id()
    
    return jsonify({
        'unread_count': get_unread_alert_count(company_id),
        'critical_count': len(get_critical_alerts(company_id))
    })


@treasury_bp.route('/api/payment-runs/<int:run_id>/calculate')
def api_calculate_payment_run(run_id):
    """Calculate payment run totals."""
    from treasury_models import calculate_payment_run_totals
    
    total = calculate_payment_run_totals(run_id)
    
    return jsonify({'total': total})


@treasury_bp.route('/api/fx-position')
def api_fx_position():
    """Get FX position API."""
    from treasury_models import get_fx_position
    
    position = get_fx_position(get_company_id())
    
    return jsonify({'position': position})
