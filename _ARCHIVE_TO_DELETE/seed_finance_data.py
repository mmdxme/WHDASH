"""
Personal Finance Seed Data
========================
Seeds realistic demo data for the Personal Finance module.
Run this script to populate the finance tables with sample data.
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'warehouse.db')


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def seed_finance_data():
    """Seed all finance data."""
    print("Seeding Personal Finance data...")
    
    # Initialize tables first
    from finance_models import initialize_finance_tables, initialize_finance_defaults
    initialize_finance_tables()
    initialize_finance_defaults()
    
    conn = get_db()
    cursor = conn.cursor()
    
    user_id = 1  # Default user
    today = datetime.now()
    month_start = today.replace(day=1)
    
    # =================================================================
    # ACCOUNTS
    # =================================================================
    print("Creating accounts...")
    accounts = [
        ('ACC-001', 'Cash Wallet', 'cash', 'USD', 2500.00, 2500.00, '', '', user_id, 1, 'active'),
        ('ACC-002', 'Emirates NBD Salary', 'bank', 'AED', 15000.00, 48500.00, 'Emirates NBD', 'DUBAI MAIN BR', user_id, 1, 'active'),
        ('ACC-003', 'ADCB Savings', 'savings', 'AED', 50000.00, 78500.00, 'ADCB', 'SAVINGS DEP', user_id, 1, 'active'),
        ('ACC-004', 'USD Travel Wallet', 'digital', 'USD', 3000.00, 3000.00, 'Revolut', 'ONLINE', user_id, 1, 'active'),
        ('ACC-005', 'Gold Savings Account', 'savings', 'AED', 10000.00, 15400.00, 'Gold & Money', 'GOLD DEP', user_id, 1, 'active'),
        ('ACC-006', 'Investment Account', 'investment', 'USD', 25000.00, 25000.00, 'Interactive Brokers', 'PORTFOLIO', user_id, 1, 'active'),
        ('ACC-007', 'Joint Family Account', 'joint', 'AED', 5000.00, 12500.00, 'Emirates Islamic', 'JOINT-FAMILY', user_id, 1, 'active'),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO pf_accounts
        (account_code, account_name, account_type, currency, opening_balance, current_balance,
         bank_provider, branch_reference, owner_user_id, is_active, is_archived, reconciliation_status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [
        ('ACC-001', 'Cash Wallet', 'cash', 'USD', 2500.00, 2500.00, '', '', user_id, 1, 0, 'not_reconciled', 'now'),
        ('ACC-002', 'Emirates NBD Salary', 'bank', 'AED', 15000.00, 48500.00, 'Emirates NBD', 'DUBAI MAIN BR', user_id, 1, 0, 'not_reconciled', 'now'),
        ('ACC-003', 'ADCB Savings', 'savings', 'AED', 50000.00, 78500.00, 'ADCB', 'SAVINGS DEP', user_id, 1, 0, 'not_reconciled', 'now'),
        ('ACC-004', 'USD Travel Wallet', 'digital', 'USD', 3000.00, 3000.00, 'Revolut', 'ONLINE', user_id, 1, 0, 'not_reconciled', 'now'),
        ('ACC-005', 'Gold Savings Account', 'savings', 'AED', 10000.00, 15400.00, 'Gold & Money', 'GOLD DEP', user_id, 1, 0, 'not_reconciled', 'now'),
        ('ACC-006', 'Investment Account', 'investment', 'USD', 25000.00, 25000.00, 'Interactive Brokers', 'PORTFOLIO', user_id, 1, 0, 'not_reconciled', 'now'),
        ('ACC-007', 'Joint Family Account', 'joint', 'AED', 5000.00, 12500.00, 'Emirates Islamic', 'JOINT-FAMILY', user_id, 1, 0, 'not_reconciled', 'now'),
    ])
    
    # =================================================================
    # CATEGORIES (Default categories already seeded, add more)
    # =================================================================
    print("Adding custom categories...")
    custom_categories = [
        ('CAT-CUSTOM1', 'Pet Care', 'expense', 'fa-paw', '#FF9F43', 20),
        ('CAT-CUSTOM2', 'Home Improvement', 'expense', 'fa-tools', '#00D2D3', 21),
        ('CAT-CUSTOM3', 'Freelance Income', 'income', 'fa-laptop-code', '#1DD1A1', 11),
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO pf_category_definitions 
        (category_code, category_name, category_type, icon, color, sort_order, is_system, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 0, datetime('now'))
    """, custom_categories)
    
    # =================================================================
    # INCOME RECORDS
    # =================================================================
    print("Creating income records...")
    income_records = []
    
    # Monthly salary for past 6 months
    for month_offset in range(6):
        month_date = month_start - timedelta(days=30 * month_offset)
        income_records.append((
            f'INC-{month_date.strftime("%Y%m")}001',
            'salary',
            'employer',
            'TechCorp Industries FZE',
            18500.00,
            'AED',
            1.0,
            18500.00,
            month_date.strftime('%Y-%m-%d'),
            2,  # Emirates NBD account
            1,  # Salary category
            1, 'monthly',
            0, 0,
            'received',
            0, '', '',
            1, 0, 'now', user_id
        ))
        
        # Bonus (quarterly)
        if month_offset % 3 == 0:
            income_records.append((
                f'INC-{month_date.strftime("%Y%m")}002',
                'bonus',
                'employer',
                'TechCorp Industries FZE - Performance Bonus',
                5000.00,
                'AED',
                1.0,
                5000.00,
                (month_date + timedelta(days=15)).strftime('%Y-%m-%d'),
                2,
                2,  # Bonus category
                0, '', 0, 0,
                'received',
                0, '', '',
                1, 0, 'now', user_id
            ))
    
    # Freelance income (occasional)
    for i in range(3):
        days_ago = random.randint(10, 50)
        income_records.append((
            f'INC-FREELANCE{i+1:03d}',
            'freelance',
            'client',
            f'Freelance Project Client {i+1}',
            random.choice([1500, 2500, 3500, 5000]),
            'USD',
            3.6725,  # AED to USD rate
            random.choice([1500, 2500, 3500, 5000]) * 3.6725,
            (today - timedelta(days=days_ago)).strftime('%Y-%m-%d'),
            4,  # USD Wallet
            17,  # Freelance category
            0, '', 0, 0,
            'received',
            0, '', '',
            1, 0, 'now', user_id
        ))
    
    # Rental income
    for month_offset in range(6):
        month_date = month_start - timedelta(days=30 * month_offset)
        income_records.append((
            f'INC-{month_date.strftime("%Y%m")}003',
            'rental',
            'tenant',
            'Studio Apartment - Tenant A',
            4500.00,
            'AED',
            1.0,
            4500.00,
            month_date.strftime('%Y-%m-%d'),
            3,  # ADCB Savings
            5,  # Rental category
            1, 'monthly',
            0, 0,
            'received',
            0, '', '',
            1, 0, 'now', user_id
        ))
    
    cursor.executemany("""
        INSERT OR REPLACE INTO pf_income_records
        (income_number, income_type, source, source_name, amount, currency, exchange_rate,
         amount_base_currency, income_date, account_id, category_id, is_recurring, recurring_pattern,
         tax_amount, fee_amount, status, receipt_document_id, notes, tags, is_active, is_archived, created_at, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
    """, income_records)
    
    # =================================================================
    # EXPENSE RECORDS
    # =================================================================
    print("Creating expense records...")
    expense_templates = [
        ('Rent', 8500, 'housing', 4, 'bank_transfer'),
        ('DEWA Electricity', 650, 'utilities', 1, 'bank_transfer'),
        ('Emirates Internet', 299, 'utilities', 1, 'card'),
        ('Du Mobile', 125, 'utilities', 1, 'card'),
        ('Car Fuel', 280, 'transport', 1, 'card'),
        ('Car Insurance', 450, 'insurance', 1, 'bank_transfer'),
        ('Car Service', 350, 'transport', 1, 'card'),
        ('Car Registration', 100, 'transport', 1, 'bank_transfer'),
        ('Grocery - Carrefour', 850, 'food', 1, 'card'),
        ('Grocery - Union Coop', 420, 'food', 1, 'card'),
        ('Restaurant - Local', 180, 'food', 1, 'card'),
        ('Restaurant - Fine Dining', 450, 'food', 1, 'card'),
        ('Coffee - Starbucks', 65, 'food', 1, 'card'),
        ('Pharmacy', 150, 'healthcare', 1, 'card'),
        ('Gym Membership', 299, 'healthcare', 1, 'bank_transfer'),
        ('Shopping - Mall', 600, 'shopping', 1, 'card'),
        ('Shopping - Online', 350, 'shopping', 1, 'card'),
        ('Entertainment - Movies', 90, 'entertainment', 1, 'card'),
        ('Entertainment - Events', 250, 'entertainment', 1, 'card'),
        ('Home Supplies', 200, 'housing', 1, 'card'),
        ('Pet Care', 150, 'expense', 1, 'card'),
        ('Mobile Apps', 45, 'subscriptions', 1, 'card'),
        ('Online Subscriptions', 85, 'subscriptions', 1, 'card'),
    ]
    
    expense_records = []
    expense_categories = {
        'housing': 5, 'utilities': 4, 'transport': 2, 'food': 1, 
        'healthcare': 6, 'shopping': 3, 'entertainment': 7, 'subscriptions': 15,
        'insurance': 11, 'expense': 16
    }
    
    # Create expenses for past 3 months
    for month_offset in range(3):
        month_date = month_start - timedelta(days=30 * month_offset)
        
        for template in expense_templates:
            name, amount, category, pay_method_idx, pay_type = template
            
            # Vary amounts slightly
            varied_amount = amount * random.uniform(0.9, 1.1)
            
            # Random day in month (avoiding first 2 days which might be future)
            day = random.randint(3, 28)
            expense_date = month_date.replace(day=day).strftime('%Y-%m-%d')
            
            # Account varies by payment type
            account_id = 1 if pay_type == 'cash' else (2 if pay_type == 'card' else 2)
            
            expense_records.append((
                f'EXP-{month_date.strftime("%Y%m")}{len(expense_records)+1:04d}',
                name,
                category,
                round(varied_amount, 2),
                'AED',
                1.0,
                round(varied_amount, 2),
                expense_date,
                account_id,
                expense_categories.get(category, 16),
                pay_type,
                0, '',
                0, 0, 0, '',
                'approved',
                '', '',
                1, 0, 'now', user_id
            ))
    
    # Add some flagged unusual expenses
    for i in range(3):
        days_ago = random.randint(5, 25)
        expense_records.append((
            f'EXP-UNUSUAL{i+1:03d}',
            'Large Purchase - Electronics',
            'shopping',
            random.choice([2500, 3800, 4500, 5200]),
            'AED',
            1.0,
            random.choice([2500, 3800, 4500, 5200]),
            (today - timedelta(days=days_ago)).strftime('%Y-%m-%d'),
            2,
            3,
            'card',
            0, '', 0, 1, 1,
            f'Unusual amount - please verify: {random.choice(["Expected?", "Correct vendor?", "Double charged?"])}',
            'approved', '', '',
            1, 0, 'now', user_id
        ))
    
    cursor.executemany("""
        INSERT OR REPLACE INTO pf_expense_records
        (expense_number, merchant_name, merchant_category, amount, currency, exchange_rate,
         amount_base_currency, expense_date, account_id, category_id, payment_method,
         is_recurring, recurring_pattern, receipt_document_id, is_flagged, flag_reason,
         status, tags, notes, is_active, is_archived, created_at, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
    """, expense_records)
    
    # =================================================================
    # TRANSACTIONS (Mirror income/expenses)
    # =================================================================
    print("Creating transaction records...")
    
    # Get income and expense IDs to create transactions
    cursor.execute("SELECT id, amount, currency, income_date, category_id, account_id, 'income' as type FROM pf_income_records WHERE is_active = 1")
    incomes = cursor.fetchall()
    
    cursor.execute("SELECT id, amount, currency, expense_date, category_id, account_id, 'expense' as type FROM pf_expense_records WHERE is_active = 1")
    expenses = cursor.fetchall()
    
    transactions = []
    txn_counter = 1
    
    for inc in incomes:
        transactions.append((
            f'TXN-INC-{txn_counter:06d}',
            'income',
            inc['amount'],
            inc['currency'],
            1.0,
            inc['amount'],
            inc['income_date'],
            inc['account_id'],
            inc['id'],
            0,
            0,
            inc['category_id'],
            'Income Transfer',
            inc['source'],
            'bank_transfer',
            0, '',
            'completed',
            1, 0, 0, '', '',
            1, 0, '', datetime('now'), user_id, datetime('now'), user_id
        ))
        txn_counter += 1
    
    for exp in expenses:
        transactions.append((
            f'TXN-EXP-{txn_counter:06d}',
            'expense',
            exp['amount'],
            exp['currency'],
            1.0,
            exp['amount'],
            exp['expense_date'],
            exp['account_id'],
            0,
            exp['id'],
            0,
            exp['category_id'],
            exp['merchant_name'],
            '',
            exp['payment_method'],
            0, '',
            'completed',
            1, 0, 0, '', '',
            1, 0, '', datetime('now'), user_id, datetime('now'), user_id
        ))
        txn_counter += 1
    
    cursor.executemany("""
        INSERT OR REPLACE INTO pf_transactions
        (transaction_code, transaction_type, amount, currency, exchange_rate, amount_base_currency,
         transaction_date, account_id, income_record_id, expense_record_id, transfer_id, category_id,
         merchant_payee, description, payment_method, is_recurring, recurring_pattern, status,
         is_confirmed, is_flagged, flag_reason, is_split, parent_transaction_id, receipt_document_id,
         tags, notes, is_active, is_archived, archived_at, created_at, created_by, updated_at, updated_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, datetime('now'), ?)
    """, transactions)
    
    # =================================================================
    # BUDGETS
    # =================================================================
    print("Creating budgets...")
    budgets = [
        (
            'BDG-2024-001',
            'Monthly Household Budget',
            'monthly',
            'personal',
            25000.00,
            'AED',
            month_start.strftime('%Y-%m-%d'),
            (month_start + timedelta(days=30)).strftime('%Y-%m-%d'),
            80.0, 1, 0, 0,
            user_id, 0, 0,
            'active', '', 1, 0, 'now', user_id, datetime('now'), user_id
        ),
        (
            'BDG-2024-002',
            'Food & Dining Budget',
            'monthly',
            'personal',
            5000.00,
            'AED',
            month_start.strftime('%Y-%m-%d'),
            (month_start + timedelta(days=30)).strftime('%Y-%m-%d'),
            80.0, 1, 0, 0,
            user_id, 0, 0,
            'active', '', 1, 0, 'now', user_id, datetime('now'), user_id
        ),
        (
            'BDG-2024-003',
            'Transport Budget',
            'monthly',
            'personal',
            2000.00,
            'AED',
            month_start.strftime('%Y-%m-%d'),
            (month_start + timedelta(days=30)).strftime('%Y-%m-%d'),
            80.0, 1, 0, 0,
            user_id, 0, 0,
            'active', '', 1, 0, 'now', user_id, datetime('now'), user_id
        ),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO pf_budgets
        (budget_code, budget_name, budget_type, budget_scope, total_budget, currency,
         period_start_date, period_end_date, warning_threshold, hard_cap, rollover_enabled,
         rollover_amount, owner_user_id, family_profile_id, is_shared, status, notes,
         is_active, is_archived, created_at, created_by, updated_at, updated_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, datetime('now'), ?)
    """, budgets)
    
    # Get budget IDs and create budget lines
    cursor.execute("SELECT id FROM pf_budgets WHERE budget_code = 'BDG-2024-001'")
    household_budget_id = cursor.fetchone()[0]
    cursor.execute("SELECT id FROM pf_budgets WHERE budget_code = 'BDG-2024-002'")
    food_budget_id = cursor.fetchone()[0]
    
    budget_lines = [
        (household_budget_id, 5, 8500.00, 0.0, 80.0),   # Housing
        (household_budget_id, 4, 1200.00, 0.0, 80.0),  # Utilities
        (household_budget_id, 2, 2000.00, 0.0, 80.0),   # Transport
        (household_budget_id, 1, 5000.00, 0.0, 80.0),    # Food
        (household_budget_id, 3, 2500.00, 0.0, 80.0),   # Shopping
        (household_budget_id, 7, 1000.00, 0.0, 80.0),    # Entertainment
        (household_budget_id, 11, 500.00, 0.0, 80.0),    # Insurance
        (household_budget_id, 15, 500.00, 0.0, 80.0),    # Subscriptions
        (food_budget_id, 1, 5000.00, 0.0, 80.0),         # Food category
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO pf_budget_lines
        (budget_id, category_id, allocated_amount, spent_amount, warning_threshold, created_at)
        VALUES (?, ?, ?, ?, ?, datetime('now'))
    """, budget_lines)
    
    # =================================================================
    # SAVINGS BUCKETS
    # =================================================================
    print("Creating savings buckets...")
    savings = [
        ('SAV-001', 'Emergency Fund', 0, 'emergency', 28000.00, 50000.00, 'AED', 1, 2000.00, 'monthly', user_id, 0, 0, 3, 'active', '6 months expenses coverage target', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('SAV-002', 'Vacation Fund', 0, 'goal', 4500.00, 15000.00, 'AED', 2, 1000.00, 'monthly', user_id, 0, 0, 5, 'active', 'Dubai to Japan trip 2025', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('SAV-003', 'New Car Down Payment', 0, 'goal', 18000.00, 60000.00, 'AED', 1, 3000.00, 'monthly', user_id, 0, 0, 2, 'active', 'Target: 2026', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('SAV-004', 'Home Down Payment', 0, 'goal', 150000.00, 450000.00, 'AED', 3, 5000.00, 'monthly', user_id, 0, 0, 1, 'active', 'Target property in 3 years', 1, 0, 'now', user_id, datetime('now'), user_id),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO pf_savings_buckets
        (bucket_code, bucket_name, goal_id, savings_type, current_amount, target_amount,
         currency, priority, recurring_amount, recurring_frequency, owner_user_id,
         family_profile_id, is_auto_transfer, linked_account_id, status, notes,
         is_active, is_archived, created_at, created_by, updated_at, updated_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, datetime('now'), ?)
    """, savings)
    
    # =================================================================
    # FINANCIAL GOALS
    # =================================================================
    print("Creating financial goals...")
    goals = [
        ('GL-001', 'Emergency Fund Goal', 'emergency', 50000.00, 28000.00, 'AED', (today + timedelta(days=365)).strftime('%Y-%m-%d'), 1, 0, 0, user_id, 'active', '6 months expenses coverage', 1, 0, '', datetime('now'), user_id, datetime('now'), user_id),
        ('GL-002', 'Japan Vacation', 'short_term', 15000.00, 4500.00, 'AED', (today + timedelta(days=300)).strftime('%Y-%m-%d'), 2, 0, 0, user_id, 'active', 'Family trip', 1, 0, '', datetime('now'), user_id, datetime('now'), user_id),
        ('GL-003', 'Car Purchase', 'medium_term', 60000.00, 18000.00, 'AED', (today + timedelta(days=730)).strftime('%Y-%m-%d'), 2, 0, 0, user_id, 'active', 'Down payment for new car', 1, 0, '', datetime('now'), user_id, datetime('now'), user_id),
        ('GL-004', 'House Down Payment', 'long_term', 450000.00, 150000.00, 'AED', (today + timedelta(days=1095)).strftime('%Y-%m-%d'), 1, 0, 0, user_id, 'active', 'Dream home', 1, 0, '', datetime('now'), user_id, datetime('now'), user_id),
        ('GL-005', 'Retirement Fund', 'long_term', 1500000.00, 125000.00, 'AED', (today + timedelta(days=3650)).strftime('%Y-%m-%d'), 1, 0, 0, user_id, 'active', 'Retirement at 50', 1, 0, '', datetime('now'), user_id, datetime('now'), user_id),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO pf_financial_goals
        (goal_code, goal_name, goal_type, target_amount, current_progress, currency,
         target_date, priority, linked_savings_bucket_id, linked_budget_id, owner_user_id,
         status, notes, is_active, is_archived, achieved_at, created_at, created_by, updated_at, updated_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, datetime('now'), ?)
    """, goals)
    
    # =================================================================
    # INVESTMENTS
    # =================================================================
    print("Creating investments...")
    investments = [
        ('INV-001', 'Apple Inc. (AAPL)', 'stock', 'US Tech', 50, 175.00, 8750.00, 178.50, 8925.00, 8750.00, 0, 175.00, 0, 'USD', (today - timedelta(days=365)).strftime('%Y-%m-%d'), '', 6, 'medium', 'Interactive Brokers', 'Long term hold', 'held', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('INV-002', 'Tesla Inc. (TSLA)', 'stock', 'US Tech', 25, 245.00, 6125.00, 238.00, 5950.00, 6125.00, 0, -175.00, 250, 'USD', (today - timedelta(days=180)).strftime('%Y-%m-%d'), '', 6, 'high', 'Interactive Brokers', 'Speculative position', 'held', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('INV-003', 'Vanguard Total Stock ETF', 'etf', 'US Index', 100, 220.00, 22000.00, 225.00, 22500.00, 22000.00, 0, 500.00, 400, 'USD', (today - timedelta(days=730)).strftime('%Y-%m-%d'), '', 6, 'low', 'Interactive Brokers', 'Core holding', 'held', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('INV-004', 'Gold Bullion 100g', 'gold', 'Precious Metals', 5, 6000.00, 30000.00, 6300.00, 31500.00, 30000.00, 0, 1500.00, 0, 'AED', (today - timedelta(days=400)).strftime('%Y-%m-%d'), '', 5, 'medium', 'Gold & Money Dubai', 'Inflation hedge', 'held', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('INV-005', 'Bitcoin (BTC)', 'crypto', 'Cryptocurrency', 0.15, 42000.00, 6300.00, 38500.00, 5775.00, 6300.00, 0, -525.00, 0, 'USD', (today - timedelta(days=200)).strftime('%Y-%m-%d'), '', 6, 'high', 'Binance', 'Speculative', 'held', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('INV-006', 'Fixed Deposit - Emirates NBD', 'bond', 'Bank Deposit', 1, 50000.00, 50000.00, 52500.00, 52500.00, 50000.00, 0, 2500.00, 0, 'AED', (today - timedelta(days=180)).strftime('%Y-%m-%d'), '', 2, 'low', 'Emirates NBD', 'Fixed income', 'held', 1, 0, 'now', user_id, datetime('now'), user_id),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO pf_investments
        (investment_code, asset_name, asset_class, asset_subclass, quantity, purchase_price,
         purchase_value, current_price, current_value, cost_basis, realized_gain_loss,
         unrealized_gain_loss, dividends_received, currency, acquisition_date, disposal_date,
         linked_account_id, risk_level, broker_provider, notes, status, is_active, is_archived,
         created_at, created_by, updated_at, updated_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, datetime('now'), ?)
    """, investments)
    
    # =================================================================
    # DEBTS
    # =================================================================
    print("Creating debts...")
    debts = [
        ('DEBT-001', 'Auto Finance - Toyota', 'loan', 85000.00, 62000.00, 2100.00, 3.9, 'fixed', (today - timedelta(days=365)).strftime('%Y-%m-%d'), (today + timedelta(days=1095)).strftime('%Y-%m-%d'), (today + timedelta(days=30)).strftime('%Y-%m-%d'), 23000.00, 3500.00, 1, 0, user_id, 'active', 'Toyota Camry financing', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('DEBT-002', 'Credit Card - Emirates NBD', 'credit_card', 15000.00, 8500.00, 450.00, 1.5, 'revolving', '', '', (today + timedelta(days=15)).strftime('%Y-%m-%d'), 15000.00, 1800.00, 2, 0, user_id, 'active', 'Outstanding balance', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('DEBT-003', 'Personal Loan - ADCB', 'personal', 30000.00, 18500.00, 1100.00, 5.5, 'fixed', (today - timedelta(days=240)).strftime('%Y-%m-%d'), (today + timedelta(days=660)).strftime('%Y-%m-%d'), (today + timedelta(days=25)).strftime('%Y-%m-%d'), 8500.00, 2200.00, 2, 0, user_id, 'active', 'Home improvement loan', 1, 0, 'now', user_id, datetime('now'), user_id),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO pf_debts
        (debt_code, lender, debt_type, principal, remaining_balance, monthly_installment,
         interest_rate, interest_type, start_date, end_date, next_due_date, total_paid,
         total_interest_paid, priority, linked_account_id, owner_user_id, status, notes,
         is_active, is_archived, created_at, created_by, updated_at, updated_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, datetime('now'), ?)
    """, debts)
    
    # =================================================================
    # ASSETS
    # =================================================================
    print("Creating assets...")
    assets = [
        ('AST-001', 'Personal Car - Toyota Camry', 'vehicle', 85000.00, 75000.00, 10.0, 'straight_line', 'AED', (today - timedelta(days=365)).strftime('%Y-%m-%d'), '', user_id, 'owned', 'Primary vehicle', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('AST-002', 'Cash Reserve - Emergency', 'cash', 28000.00, 28000.00, 0, '', 'AED', '', '', user_id, 'owned', 'Emergency cash reserve', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('AST-003', 'Gold Jewelry Collection', 'jewelry', 25000.00, 28000.00, 0, '', 'AED', (today - timedelta(days=730)).strftime('%Y-%m-%d'), '', user_id, 'owned', 'Family gold', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('AST-004', 'MacBook Pro 16"', 'digital', 8500.00, 6500.00, 25.0, 'straight_line', 'AED', (today - timedelta(days=500)).strftime('%Y-%m-%d'), '', user_id, 'owned', 'Work laptop', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('AST-005', 'iPhone 15 Pro', 'digital', 5500.00, 4500.00, 25.0, 'straight_line', 'AED', (today - timedelta(days=180)).strftime('%Y-%m-%d'), '', user_id, 'owned', 'Personal phone', 1, 0, 'now', user_id, datetime('now'), user_id),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO pf_assets
        (asset_code, asset_type, asset_name, purchase_value, current_value, depreciation_rate,
         depreciation_method, currency, acquisition_date, linked_documents, owner_user_id,
         status, notes, is_active, is_archived, created_at, created_by, updated_at, updated_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, datetime('now'), ?)
    """, assets)
    
    # =================================================================
    # SUBSCRIPTIONS
    # =================================================================
    print("Creating subscriptions...")
    subscriptions = [
        ('SUB-001', 'Netflix Premium', 'streaming', '4K Plan', 69.00, 'AED', 'monthly', (today + timedelta(days=12)).strftime('%Y-%m-%d'), 1, 15, 2, 3, user_id, 'active', '', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('SUB-002', 'Spotify Premium', 'streaming', 'Family Plan', 55.00, 'AED', 'monthly', (today + timedelta(days=18)).strftime('%Y-%m-%d'), 1, 15, 1, 3, user_id, 'active', '', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('SUB-003', 'Amazon Prime', 'membership', 'Annual', 365.00, 'AED', 'yearly', (today + timedelta(days=245)).strftime('%Y-%m-%d'), 1, 14, 4, 3, user_id, 'active', '', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('SUB-004', 'Du Home Internet', 'utilities', 'Premium Package', 499.00, 'AED', 'monthly', (today + timedelta(days=8)).strftime('%Y-%m-%d'), 1, 4, 2, 3, user_id, 'active', '', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('SUB-005', 'Car Insurance - Comprehensive', 'insurance', 'Annual Premium', 4500.00, 'AED', 'yearly', (today + timedelta(days=95)).strftime('%Y-%m-%d'), 1, 30, 11, 2, user_id, 'active', '', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('SUB-006', 'Gym Membership - Fitness First', 'membership', 'Annual', 3600.00, 'AED', 'yearly', (today + timedelta(days=180)).strftime('%Y-%m-%d'), 1, 6, 2, 3, user_id, 'active', '', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('SUB-007', 'Microsoft 365 Family', 'software', 'Annual Subscription', 350.00, 'AED', 'yearly', (today + timedelta(days=120)).strftime('%Y-%m-%d'), 1, 16, 2, 3, user_id, 'active', '', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('SUB-008', 'Apple iCloud 200GB', 'software', 'Monthly', 29.99, 'AED', 'monthly', (today + timedelta(days=22)).strftime('%Y-%m-%d'), 1, 15, 1, 3, user_id, 'active', '', 1, 0, 'now', user_id, datetime('now'), user_id),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO pf_subscriptions
        (subscription_number, provider, service_type, plan_name, amount, currency,
         billing_cycle, renewal_date, auto_renew, category_id, account_id, reminder_days,
         owner_user_id, status, notes, is_active, is_archived, created_at, created_by, updated_at, updated_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, datetime('now'), ?)
    """, subscriptions)
    
    # =================================================================
    # ALERTS
    # =================================================================
    print("Creating alerts...")
    alerts = [
        ('ALT-001', 'overspending', 'High Spending Alert', 'Your food budget is 85% consumed with 10 days remaining in the month.', 'warning', 0, 'AED', 'budget', 0, 0, 0, '', user_id, 1, datetime('now')),
        ('ALT-002', 'due_payment', 'Subscription Renewal Due', 'Netflix Premium (69 AED) renews in 12 days.', 'info', 69, 'AED', 'subscription', 0, 0, (today + timedelta(days=12)).strftime('%Y-%m-%d'), user_id, 1, datetime('now')),
        ('ALT-003', 'low_balance', 'Low Balance Warning', 'Your Cash Wallet balance is below 1000 AED.', 'warning', 2500, 'AED', 'account', 0, 1, '', user_id, 1, datetime('now')),
        ('ALT-004', 'debt_due', 'Debt Payment Due', 'Personal Loan installment (1100 AED) is due in 5 days.', 'info', 1100, 'AED', 'debt', 0, 3, (today + timedelta(days=5)).strftime('%Y-%m-%d'), user_id, 1, datetime('now')),
        ('ALT-005', 'unusual_expense', 'Unusual Transaction Detected', 'A large transaction of 5200 AED was recorded at Electronics Store.', 'danger', 5200, 'AED', 'expense', 0, 0, '', user_id, 1, datetime('now')),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO pf_alerts
        (alert_code, alert_type, title, message, severity, amount, currency,
         linked_entity_type, linked_entity_id, due_date, owner_user_id, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, alerts)
    
    # =================================================================
    # CURRENCY RATES
    # =================================================================
    print("Creating currency rates...")
    currency_rates = [
        ('USD', 'AED', 3.6725, today.strftime('%Y-%m-%d'), 'manual'),
        ('EUR', 'AED', 3.9850, today.strftime('%Y-%m-%d'), 'manual'),
        ('GBP', 'AED', 4.5625, today.strftime('%Y-%m-%d'), 'manual'),
        ('SAR', 'AED', 0.9792, today.strftime('%Y-%m-%d'), 'manual'),
        ('INR', 'AED', 0.0445, today.strftime('%Y-%m-%d'), 'manual'),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO pf_currency_rates
        (from_currency, to_currency, rate, rate_date, source, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, 1, datetime('now'))
    """, currency_rates)
    
    # =================================================================
    # FAMILY PROFILES
    # =================================================================
    print("Creating family profiles...")
    family = [
        ('FAM-001', 'Personal', 'personal', user_id, 1, datetime('now'), user_id, datetime('now'), user_id),
        ('FAM-002', 'Family Shared', 'family', user_id, 1, datetime('now'), user_id, datetime('now'), user_id),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO pf_family_profiles
        (profile_code, profile_name, profile_type, primary_user_id, is_active, created_at, created_by, updated_at, updated_by)
        VALUES (?, ?, ?, ?, ?, datetime('now'), ?, datetime('now'), ?)
    """, family)
    
    # =================================================================
    # AUTOMATION RULES
    # =================================================================
    print("Creating automation rules...")
    import json
    automation_rules = [
        ('RULE-001', 'Auto-Categorize Coffee Shops', 'auto_categorize',
         json.dumps({'type': 'contains', 'field': 'merchant_name', 'value': 'Starbucks'}),
         json.dumps({'action': 'set_category', 'category_id': 1}),
         5, 1, user_id, datetime('now'), 0, 'active', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('RULE-002', 'Auto-Categorize Restaurants', 'auto_categorize',
         json.dumps({'type': 'contains', 'field': 'merchant_name', 'value': 'Restaurant'}),
         json.dumps({'action': 'set_category', 'category_id': 1}),
         5, 1, user_id, datetime('now'), 0, 'active', 1, 0, 'now', user_id, datetime('now'), user_id),
        ('RULE-003', 'Alert Large Transactions', 'alert',
         json.dumps({'type': 'greater_than', 'field': 'amount', 'value': '5000'}),
         json.dumps({'action': 'create_alert', 'severity': 'warning'}),
         3, 1, user_id, datetime('now'), 0, 'active', 1, 0, 'now', user_id, datetime('now'), user_id),
    ]
    
    cursor.executemany("""
        INSERT OR REPLACE INTO pf_automation_rules
        (rule_code, rule_name, rule_type, condition_json, action_json, priority,
         is_enabled, owner_user_id, last_triggered_at, trigger_count, status, notes,
         is_active, created_at, created_by, updated_at, updated_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?, ?, ?, ?, ?, datetime('now'), ?, datetime('now'), ?)
    """, automation_rules)
    
    conn.commit()
    conn.close()
    
    print("Personal Finance data seeded successfully!")
    return True


if __name__ == '__main__':
    seed_finance_data()
