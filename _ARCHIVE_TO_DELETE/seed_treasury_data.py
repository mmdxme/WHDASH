"""
Treasury Module - Demo Data Seeder
================================
Seeds realistic treasury data into WHDASH for demonstration.

Usage:
    python seed_treasury_data.py
"""

import sys
import os
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db_context, get_one, get_all, table_exists


def seed_treasury_data():
    """Seed comprehensive demo data for the Treasury module."""
    print("Seeding Treasury module demo data...")
    
    with get_db_context() as db:
        # Check if treasury tables exist
        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        table_names = [t['name'] for t in tables]
        
        available_tables = [
            'treasury_settings', 'treasury_cash_position_snapshots', 
            'treasury_petty_cash_accounts', 'treasury_cash_boxes',
            'treasury_cash_movements', 'treasury_forecasts',
            'treasury_forecast_scenarios', 'treasury_forecast_items',
            'treasury_liquidity_plans', 'treasury_collections',
            'treasury_payments_plan', 'treasury_transfer_requests',
            'treasury_controls', 'treasury_alerts',
            'treasury_bank_statements', 'treasury_bank_statement_lines',
            'treasury_payment_runs', 'treasury_payment_run_items',
            'treasury_fx_contracts', 'treasury_counterparties',
            'treasury_cash_pools', 'treasury_collection_scores',
            'treasury_transfer_approvals', 'treasury_bank_signatories',
            'treasury_workflow_rules', 'treasury_account_groups',
            'treasury_reconciliation_rules', 'treasury_notification_preferences',
            'treasury_dunning_settings', 'treasury_bank_connections',
            'treasury_bank_charges', 'treasury_cash_pool_members',
            'treasury_notional_pooling', 'treasury_liquidity_thresholds',
            'treasury_audit_log'
        ]
        
        existing_tables = [t for t in available_tables if t in table_names]
        missing = [t for t in available_tables if t not in table_names]
        
        if missing:
            print(f"[INFO] Tables not yet created: {missing[:5]}...")
        
        # Seed Treasury Settings
        if 'treasury_settings' in existing_tables:
            _seed_treasury_settings(db)
        
        # Seed Cash Boxes
        if 'treasury_cash_boxes' in existing_tables:
            _seed_cash_boxes(db)
        
        # Seed Cash Position Snapshots
        if 'treasury_cash_position_snapshots' in existing_tables:
            _seed_cash_position_snapshots(db)
        
        # Seed Petty Cash Accounts
        if 'treasury_petty_cash_accounts' in existing_tables:
            _seed_petty_cash_accounts(db)
        
        # Seed Cash Movements
        if 'treasury_cash_movements' in existing_tables:
            _seed_cash_movements(db)
        
        # Seed Collections Plan
        if 'treasury_collections' in existing_tables:
            _seed_collections(db)
        
        # Seed Payments Plan
        if 'treasury_payments_plan' in existing_tables:
            _seed_payments_plan(db)
        
        # Seed Transfer Requests
        if 'treasury_transfer_requests' in existing_tables:
            _seed_transfer_requests(db)
        
        # Seed Controls
        if 'treasury_controls' in existing_tables:
            _seed_controls(db)
        
        # Seed Alerts
        if 'treasury_alerts' in existing_tables:
            _seed_alerts(db)
        
        # Seed Counterparties
        if 'treasury_counterparties' in existing_tables:
            _seed_counterparties(db)
        
        # Seed FX Contracts
        if 'treasury_fx_contracts' in existing_tables:
            _seed_fx_contracts(db)
        
        # Seed Cash Pools
        if 'treasury_cash_pools' in existing_tables:
            _seed_cash_pools(db)
        
        # Seed Forecasts
        if 'treasury_forecasts' in existing_tables:
            _seed_forecasts(db)
        
        # Seed Bank Statements
        if 'treasury_bank_statements' in existing_tables:
            _seed_bank_statements(db)
        
        # Seed Payment Runs
        if 'treasury_payment_runs' in existing_tables:
            _seed_payment_runs(db)
        
        db.commit()
    
    print("Treasury demo data seeded successfully!")


def _seed_treasury_settings(db):
    """Seed treasury settings."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM treasury_settings").fetchone()
    if existing['cnt'] > 5:
        print("  - Treasury settings already exist")
        return
    
    settings = [
        ('cash_threshold_warning', '50000', 'CASH', 'Warning threshold for low cash'),
        ('cash_threshold_critical', '10000', 'CASH', 'Critical threshold for low cash'),
        ('default_currency', 'AED', 'GENERAL', 'Default currency'),
        ('forecast_horizon_days', '90', 'FORECAST', 'Forecast horizon in days'),
        ('liquidity_check_frequency', 'daily', 'GENERAL', 'Liquidity check frequency'),
        ('auto_reconcile', '1', 'RECONCILIATION', 'Auto bank reconciliation'),
        ('max_payment_batch_size', '50', 'PAYMENTS', 'Maximum batch payment size'),
        ('require_dual_approval', '1', 'CONTROLS', 'Require dual approval for transfers'),
        ('default_bank', 'Emirates NBD', 'BANKING', 'Default bank for transactions'),
        ('fx_rate_source', 'ECB', 'FX', 'FX rate source'),
    ]
    
    for key, value, category, desc in settings:
        cursor.execute("""
            INSERT OR IGNORE INTO treasury_settings (setting_key, setting_value, category, description)
            VALUES (?, ?, ?, ?)
        """, (key, value, category, desc))
    
    print("  [OK] Treasury settings seeded")


def _seed_cash_boxes(db):
    """Seed petty cash boxes."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM treasury_cash_boxes").fetchone()
    if existing['cnt'] > 0:
        print("  - Cash boxes already exist")
        return
    
    boxes = [
        ('BOX-MAIN-001', 'Main Office Float', 'cash_box', 'Dubai', 'Main office petty cash', 5000, 1000),
        ('BOX-WH-001', 'Warehouse Float', 'cash_box', 'Jebel Ali', 'Warehouse operations float', 2000, 500),
        ('BOX-EMG-001', 'Emergency Reserve', 'cash_box', 'Dubai', 'Emergency cash reserve', 10000, 5000),
        ('BOX-TRV-001', 'Travel Advance', 'cash_box', 'Dubai', 'Staff travel advances', 3000, 1000),
    ]
    
    for code, name, box_type, location, notes, opening, current in boxes:
        cursor.execute("""
            INSERT INTO treasury_cash_boxes (box_code, box_name, box_type, location,
                responsible_person_id, responsible_person_name, opening_balance,
                current_balance, currency, is_active, created_at)
            VALUES (?, ?, ?, ?, 1, 'System User', ?, ?, 'AED', 1, ?)
        """, (code, name, box_type, location, opening, current, datetime.now().isoformat()))
    
    print("  [OK] Cash boxes seeded")


def _seed_cash_position_snapshots(db):
    """Seed cash position snapshots."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM treasury_cash_position_snapshots").fetchone()
    if existing['cnt'] > 20:
        print("  - Cash position snapshots already exist")
        return
    
    # Generate snapshots for 4 banks over 90 days
    banks = [
        (1, 'Emirates NBD - AED', 'AED'),
        (2, 'Emirates NBD - USD', 'USD'),
        (3, 'Standard Chartered - AED', 'AED'),
        (4, 'First Abu Dhabi Bank - AED', 'AED'),
    ]
    base_balances = {1: 2450000, 2: 485000, 3: 1890000, 4: 3200000}
    
    for days_ago in range(90):
        snapshot_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        for bank_acct_id, bank_name, currency in banks:
            base = base_balances[bank_acct_id]
            variation = random.uniform(-0.05, 0.05)
            opening = base * (1 + variation)
            closing = opening * (1 + random.uniform(-0.02, 0.02))
            inflow = closing - opening if closing > opening else 0
            outflow = opening - closing if opening > closing else 0
            
            cursor.execute("""
                INSERT INTO treasury_cash_position_snapshots 
                (snapshot_date, bank_account_id, currency, opening_balance, closing_balance,
                 total_inflow, total_outflow, blocked_amount, available_balance,
                 entity_id, branch_id, company_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, 1, 1, 1, ?)
            """, (snapshot_date, bank_acct_id, currency, opening, closing, inflow, outflow, closing, datetime.now().isoformat()))
    
    print("  [OK] Cash position snapshots seeded")


def _seed_petty_cash_accounts(db):
    """Seed petty cash accounts."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM treasury_petty_cash_accounts").fetchone()
    if existing['cnt'] > 0:
        print("  - Petty cash accounts already exist")
        return
    
    accounts = [
        ('PCA-MAIN-001', 'Main Office AED', 'AED', 'Dubai', 'Main office petty cash', 5000, 1000, 20000),
        ('PCA-WH-001', 'Warehouse AED', 'AED', 'Jebel Ali', 'Warehouse operations', 2000, 500, 5000),
        ('PCA-EMG-001', 'Emergency AED', 'AED', 'Dubai', 'Emergency reserve', 10000, 5000, 50000),
        ('PCA-TRV-001', 'Travel AED', 'AED', 'Dubai', 'Staff travel advances', 3000, 1000, 10000),
    ]
    
    for code, name, currency, location, notes, float_amt, min_bal, max_trans in accounts:
        cursor.execute("""
            INSERT INTO treasury_petty_cash_accounts 
            (account_code, account_name, currency, location, custodian_id, custodian_name,
             float_amount, current_balance, minimum_balance, maximum_transaction,
             is_active, created_by, created_at)
            VALUES (?, ?, ?, ?, 1, 'System User', ?, ?, ?, ?, 1, 1, ?)
        """, (code, name, currency, location, float_amt, float_amt, min_bal, max_trans, datetime.now().isoformat()))
    
    print("  [OK] Petty cash accounts seeded")


def _seed_cash_movements(db):
    """Seed cash movements."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM treasury_cash_movements").fetchone()
    if existing['cnt'] > 30:
        print("  - Cash movements already exist")
        return
    
    movement_types_list = ['inflow', 'outflow']
    descriptions = [
        'Customer payment - Al Futtaim Group',
        'Supplier payment - Bosch Automotive',
        'Employee expense reimbursement',
        'Bank transfer to USD account',
        'Cash withdrawal for petty cash',
        'Customer payment - Emirates Trading',
        'Rent payment - Dubai Office',
        'Utility bill payment - DEWA',
        'Insurance premium payment',
        'Equipment purchase',
    ]
    
    # Get petty cash accounts
    cursor.execute("SELECT id FROM treasury_petty_cash_accounts LIMIT 4")
    pc_accounts = [r['id'] for r in cursor.fetchall()] or [1, 2, 3, 4]
    
    for i in range(50):
        movement_type = random.choice(movement_types_list)
        amount = random.uniform(500, 50000)
        desc = random.choice(descriptions)
        date = (datetime.now() - timedelta(days=random.randint(0, 60))).strftime('%Y-%m-%d')
        pc_id = random.choice(pc_accounts)
        
        # Get balance before
        bal_before = random.uniform(1000, 50000)
        bal_after = bal_before + amount if movement_type == 'inflow' else bal_before - amount
        
        cursor.execute("""
            INSERT INTO treasury_cash_movements 
            (movement_number, movement_date, movement_type, petty_cash_account_id,
             amount, currency, balance_before, balance_after, reference,
             description, approved_by, approved_at, status, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, 'AED', ?, ?, ?, ?, 1, ?, 'Completed', 1, ?)
        """, (
            f'MOV-2026-{i+1:05d}',
            date,
            movement_type,
            pc_id,
            amount,
            bal_before,
            bal_after,
            f'REF-{i+1:04d}',
            desc,
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
    
    print("  [OK] Cash movements seeded")


def _seed_collections(db):
    """Seed AR collections plan."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM treasury_collections").fetchone()
    if existing['cnt'] > 5:
        print("  - Collections plan already exist")
        return
    
    customers = [
        ('Al Futtaim Group', 245000),
        ('Emirates Trading LLC', 189000),
        ('Al Shirawi Group', 156000),
        ('Al Ghurair Foods', 98000),
        ('Dubai Customs', 340000),
    ]
    
    for i, (cust_name, amount) in enumerate(customers):
        due_date = (datetime.now() + timedelta(days=random.randint(-30, 60))).strftime('%Y-%m-%d')
        invoice_date = (datetime.now() - timedelta(days=random.randint(30, 90))).strftime('%Y-%m-%d')
        likelihood = random.choice(['expected', 'likely', 'unlikely', 'certain'])
        risk_level = random.choice(['normal', 'medium', 'high'])
        
        cursor.execute("""
            INSERT INTO treasury_collections 
            (collection_number, customer_name, invoice_number, invoice_date, due_date,
             original_amount, open_amount, expected_amount, expected_date,
             likelihood, risk_level, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f'COL-2026-{i+1:04d}',
            cust_name,
            f'INV-2026-{random.randint(1,100):04d}',
            invoice_date,
            due_date,
            amount,
            amount * random.uniform(0.3, 1.0),
            amount * random.uniform(0.5, 1.0),
            due_date,
            likelihood,
            risk_level,
            f'Collection for {cust_name}',
            datetime.now().isoformat()
        ))
    
    print("  [OK] Collections plan seeded")


def _seed_payments_plan(db):
    """Seed AP payments plan."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM treasury_payments_plan").fetchone()
    if existing['cnt'] > 5:
        print("  - Payments plan already exist")
        return
    
    suppliers = [
        ('Bosch Automotive FZE', 125000),
        ('Michelin Middle East', 89000),
        ('Shell Middle East', 156000),
        ('Continental AG', 78000),
        ('Valeo Group', 45000),
    ]
    
    for i, (supp_name, amount) in enumerate(suppliers):
        due_date = (datetime.now() + timedelta(days=random.randint(-15, 45))).strftime('%Y-%m-%d')
        bill_date = (datetime.now() - timedelta(days=random.randint(15, 60))).strftime('%Y-%m-%d')
        
        cursor.execute("""
            INSERT INTO treasury_payments_plan 
            (payment_number, supplier_name, bill_number, bill_date, due_date,
             original_amount, open_amount, planned_amount, planned_date,
             priority, payment_method, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f'PAY-2026-{i+1:04d}',
            supp_name,
            f'BILL-2026-{random.randint(1,100):04d}',
            bill_date,
            due_date,
            amount,
            amount * random.uniform(0.5, 1.0),
            amount,
            due_date,
            random.choice(['Normal', 'High', 'Urgent']),
            random.choice(['Bank Transfer', 'Cheque']),
            random.choice(['Pending', 'Approved', 'Paid', 'Scheduled']),
            datetime.now().isoformat()
        ))
    
    print("  [OK] Payments plan seeded")


def _seed_transfer_requests(db):
    """Seed internal transfer requests."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM treasury_transfer_requests").fetchone()
    if existing['cnt'] > 5:
        print("  - Transfer requests already exist")
        return
    
    transfers = [
        ('intercompany', 'AED Current - Emirates NBD', 'USD Account - Emirates NBD', 250000, 'Approved'),
        ('intercompany', 'AED Current - SCB', 'USD Account - SCB', 150000, 'Approved'),
        ('petty_cash', 'Main Cash Box', 'Warehouse Float', 5000, 'Completed'),
        ('intercompany', 'FAB Account', 'Emergency Reserve', 10000, 'Pending'),
    ]
    
    for i, (req_type, from_acc, to_acc, amount, status) in enumerate(transfers):
        date = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
        
        cursor.execute("""
            INSERT INTO treasury_transfer_requests 
            (request_number, request_type, transfer_date, from_account_type,
             from_bank_account_id, to_account_type, to_bank_account_id,
             amount, currency, reference, status, requires_approval,
             approved_by, approved_at, entity_id, branch_id, company_id,
             created_by, created_at)
            VALUES (?, ?, ?, 'bank_account', 1, 'bank_account', 2, ?, 'AED',
             ?, ?, 1, 1, ?, 1, 1, 1, 1, ?)
        """, (f'TRF-2026-{i+1:04d}', req_type, date, amount, f'REF-TRF-{i+1}', status, datetime.now().isoformat(), datetime.now().isoformat()))
    
    print("  [OK] Transfer requests seeded")


def _seed_controls(db):
    """Seed treasury controls."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM treasury_controls").fetchone()
    if existing['cnt'] > 5:
        print("  - Treasury controls already exist")
        return
    
    controls = [
        ('Dual Authorization for Transfers', 'authorization', 'cash_management',
         'All transfers above AED 50,000 require two approvals',
         'amount > 50000', 50000, '>', 'payments,transfers', 1, 'High'),
        ('Daily Cash Position Reporting', 'monitoring', 'reporting',
         'Treasury must report cash position by 10 AM daily',
         None, 0, None, 'reporting', 1, 'Medium'),
        ('Weekly Bank Reconciliation', 'reconciliation', 'banking',
         'All bank accounts reconciled weekly',
         None, 0, None, 'reconciliation', 1, 'Medium'),
        ('Monthly Liquidity Review', 'monitoring', 'liquidity',
         'Liquidity forecast reviewed monthly by Treasury Manager',
         None, 0, None, 'planning', 1, 'Low'),
        ('Quarterly FX Exposure Review', 'monitoring', 'fx',
         'Foreign exchange positions reviewed quarterly',
         None, 0, None, 'fx_risk', 1, 'Medium'),
    ]
    
    for name, ctype, cat, desc, rule, threshold, op, ops, active, severity in controls:
        cursor.execute("""
            INSERT INTO treasury_controls 
            (control_name, control_type, control_category, description, control_rule,
             threshold_value, threshold_operator, affected_operations,
             is_active, severity, company_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
        """, (name, ctype, cat, desc, rule, threshold, op, ops, active, severity, datetime.now().isoformat()))
    
    print("  [OK] Treasury controls seeded")


def _seed_alerts(db):
    """Seed treasury alerts."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM treasury_alerts").fetchone()
    if existing['cnt'] > 5:
        print("  - Treasury alerts already exist")
        return
    
    alerts = [
        ('LOW_CASH', 'cash', 'LOW_CASH', 'Warning', 'Cash balance below warning threshold',
         'AED Current account balance at Emirates NBD below AED 50,000', 'Treasury', None, 45000, 'AED'),
        ('OVERDUE_PAYMENT', 'payment', 'OVERDUE', 'Warning', 'Payment overdue for supplier',
         'Payment to Bosch Automotive FZE is 15 days overdue', 'Finance', None, 125000, 'AED'),
        ('FX_EXPOSURE', 'fx', 'FX_EXPOSURE', 'Info', 'USD exposure exceeds 20%',
         'USD/EUR exposure exceeds 20% of total portfolio', 'Treasury', None, None, 'USD'),
        ('SLA_BREACH', 'approval', 'SLA_BREACH', 'Critical', 'Payment approval SLA breached',
         'Invoice #INV-2026-056 approval SLA breached by 2 days', 'Finance', None, 78000, 'AED'),
        ('BANK_RECONCILE', 'reconciliation', 'PENDING_RECONCILE', 'Info', 'Bank reconciliation pending',
         'Standard Chartered account reconciliation 5 days overdue', 'Treasury', None, None, 'AED'),
        ('CASH_FORECAST', 'liquidity', 'LOW_CASH_FORECAST', 'Warning', '30-day forecast shortfall',
         'Cash forecast shows potential shortfall in week 3 of April', 'Treasury', None, 500000, 'AED'),
    ]
    
    for alert_type, cat, acat, sev, title, msg, src, sid, amt, cur in alerts:
        cursor.execute("""
            INSERT INTO treasury_alerts 
            (alert_number, alert_type, alert_category, severity, title, message, source,
             source_id, amount, currency, is_read, is_resolved, company_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 1, ?)
        """, (f'ALERT-2026-{random.randint(1,999):04d}', alert_type, cat, sev, title, msg, src, sid, amt, cur, datetime.now().isoformat()))
    
    print("  [OK] Treasury alerts seeded")


def _seed_counterparties(db):
    """Seed banking counterparties."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM treasury_counterparties").fetchone()
    if existing['cnt'] > 5:
        print("  - Counterparties already exist")
        return
    
    counterparties = [
        ('Emirates NBD', 'Bank', 'UAE', 'Active'),
        ('Standard Chartered', 'Bank', 'UAE', 'Active'),
        ('First Abu Dhabi Bank', 'Bank', 'UAE', 'Active'),
        ('HSBC Middle East', 'Bank', 'UAE', 'Active'),
        ('Abu Dhabi Commercial Bank', 'Bank', 'UAE', 'Active'),
        ('Al Futtaim Group', 'Corporate', 'UAE', 'Active'),
        ('Emirates Trading LLC', 'Corporate', 'UAE', 'Active'),
    ]
    
    for name, ctype, country, status in counterparties:
        cursor.execute("""
            INSERT INTO treasury_counterparties 
            (counterparty_name, counterparty_type, country, status, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (name, ctype, country, status, datetime.now().isoformat()))
    
    print("  [OK] Counterparties seeded")


def _seed_fx_contracts(db):
    """Seed FX contracts."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM treasury_fx_contracts").fetchone()
    if existing['cnt'] > 5:
        print("  - FX contracts already exist")
        return
    
    contracts = [
        ('USD/AED', 'Spot', 250000, 3.6725, 'Emirates NBD', 'Pending'),
        ('EUR/AED', 'Forward', 150000, 3.9825, 'Standard Chartered', 'Active'),
        ('GBP/AED', 'Spot', 100000, 4.4525, 'FAB', 'Settled'),
        ('USD/AED', 'Forward', 500000, 3.6850, 'Emirates NBD', 'Active'),
        ('JPY/AED', 'Spot', 2000000, 0.025, 'HSBC', 'Settled'),
    ]
    
    for pair, contract_type, amount, rate, bank, status in contracts:
        start_date = (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=random.randint(30, 90))).strftime('%Y-%m-%d')
        
        cursor.execute("""
            INSERT INTO treasury_fx_contracts 
            (currency_pair, contract_type, amount, exchange_rate, counterparty_bank,
             start_date, end_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (pair, contract_type, amount, rate, bank, start_date, end_date, status, datetime.now().isoformat()))
    
    print("  [OK] FX contracts seeded")


def _seed_cash_pools(db):
    """Seed cash pools."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM treasury_cash_pools").fetchone()
    if existing['cnt'] > 0:
        print("  - Cash pools already exist")
        return
    
    pools = [
        ('MMDx AED Master Pool', 'AED', 'Physical', 'Active'),
        ('MMDx USD Pool', 'USD', 'Notional', 'Active'),
        ('MMDx Regional Pool', 'AED', 'Notional', 'Active'),
    ]
    
    for name, currency, pool_type, status in pools:
        total_balance = random.uniform(5000000, 15000000)
        
        cursor.execute("""
            INSERT INTO treasury_cash_pools 
            (pool_name, currency, pool_type, total_balance, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, currency, pool_type, total_balance, status, datetime.now().isoformat()))
    
    print("  [OK] Cash pools seeded")


def _seed_forecasts(db):
    """Seed cash flow forecasts."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM treasury_forecasts").fetchone()
    if existing['cnt'] > 0:
        print("  - Forecasts already exist")
        return
    
    scenarios = ['base', 'best', 'worst']
    
    for i, scenario in enumerate(scenarios):
        cursor.execute("""
            INSERT INTO treasury_forecasts 
            (forecast_name, forecast_type, scenario, version, start_date, end_date,
             currency, status, entity_id, company_id, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f'30-Day Cash Flow Forecast - {scenario.title()}',
            'cash_flow',
            scenario,
            1,
            datetime.now().strftime('%Y-%m-%d'),
            (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'),
            'AED',
            'Draft' if scenario != 'base' else 'Active',
            1, 1, 1,
            datetime.now().isoformat()
        ))
        
        # Add forecast scenarios
        forecast_id = cursor.lastrowid
        scenario_types = [('pessimistic', 0.7, -0.02, 0.03), ('most_likely', 1.0, 0.01, 0.01), ('optimistic', 1.3, 0.05, -0.01)]
        
        for scen_name, weight, inflow_growth, outflow_growth in scenario_types:
            cursor.execute("""
                INSERT INTO treasury_forecast_scenarios 
                (forecast_id, scenario_name, scenario_type, probability_weight,
                 growth_rate_inflow, growth_rate_outflow, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (forecast_id, scen_name.title(), scen_name, weight, inflow_growth, outflow_growth, datetime.now().isoformat()))
    
    print("  [OK] Forecasts seeded")


def _seed_bank_statements(db):
    """Seed bank statement records."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM treasury_bank_statements").fetchone()
    if existing['cnt'] > 0:
        print("  - Bank statements already exist")
        return
    
    statements = [
        ('Emirates NBD - AED', '2026-03', '2026-03-31', 2450000, 'Active'),
        ('SCB - AED', '2026-03', '2026-03-31', 1890000, 'Active'),
        ('FAB - AED', '2026-03', '2026-03-31', 3200000, 'Active'),
    ]
    
    for bank, period, statement_date, ending_balance, status in statements:
        cursor.execute("""
            INSERT INTO treasury_bank_statements 
            (bank_name, account_number, period, statement_date, 
             opening_balance, ending_balance, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (bank, 'ACC-001', period, statement_date, ending_balance * 0.95, ending_balance, status, datetime.now().isoformat()))
    
    print("  [OK] Bank statements seeded")


def _seed_payment_runs(db):
    """Seed payment runs."""
    cursor = db.cursor()
    existing = cursor.execute("SELECT COUNT(*) as cnt FROM treasury_payment_runs").fetchone()
    if existing['cnt'] > 0:
        print("  - Payment runs already exist")
        return
    
    runs = [
        ('Weekly AP Run - Week 12', 'Approved', 450000, '2026-03-20'),
        ('Weekly AP Run - Week 13', 'Processing', 520000, '2026-03-27'),
        ('Weekly AP Run - Week 14', 'Scheduled', 380000, '2026-04-03'),
        ('Monthly Supplier Settlement', 'Completed', 1250000, '2026-03-01'),
    ]
    
    for name, status, total_amount, scheduled_date in runs:
        cursor.execute("""
            INSERT INTO treasury_payment_runs 
            (run_name, status, total_amount, currency, scheduled_date,
             executed_date, created_by, created_at)
            VALUES (?, ?, ?, 'AED', ?, NULL, 1, ?)
        """, (name, status, total_amount, scheduled_date, datetime.now().isoformat()))
    
    print("  [OK] Payment runs seeded")


def main():
    """Main entry point."""
    print("=" * 60)
    print("Treasury Module - Demo Data Seeder")
    print("=" * 60)
    print()
    seed_treasury_data()
    print()
    print("=" * 60)
    print("Treasury demo data seeding completed!")
    print("=" * 60)


if __name__ == '__main__':
    main()