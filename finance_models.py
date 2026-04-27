"""
Personal Finance / Money Management / Budgeting Models
=====================================================
Data models for the Personal Finance module.
Supports:
- Account & Wallet Management
- Income & Expense Tracking
- Transaction Management
- Budgeting & Budget Lines
- Savings & Financial Goals
- Investment Tracking
- Debt & Loan Management
- Asset Tracking
- Cash Flow Analysis
- Subscriptions & Recurring Payments
- Calendar Events & Reminders
- Alerts & Notifications
- Category Definitions
- Automation Rules
- Multi-Currency Support
- Family/Multi-User Profiles
- Export Presets & Dashboard Preferences
"""

import sqlite3
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from contextlib import contextmanager

BASE_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else ''
DATABASE = os.path.join(BASE_DIR, 'warehouse.db')


def get_db():
    """Get database connection."""
    db_path = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'warehouse.db'))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db_context():
    """Context manager for database operations."""
    conn = get_db()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    with get_db_context() as db:
        result = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        ).fetchone()
        return result is not None


def get_one(query: str, params: tuple = ()):
    """Execute query and return one result."""
    with get_db_context() as db:
        cursor = db.execute(query, params)
        return cursor.fetchone()


def get_all(query: str, params: tuple = ()):
    """Execute query and return all results."""
    with get_db_context() as db:
        cursor = db.execute(query, params)
        return cursor.fetchall()


def row_to_dict(row: sqlite3.Row) -> Dict:
    """Convert sqlite3.Row to dictionary."""
    if row is None:
        return None
    return dict(zip(row.keys(), row))


def rows_to_list(rows: List[sqlite3.Row]) -> List[Dict]:
    """Convert list of sqlite3.Row to list of dictionaries."""
    return [row_to_dict(row) for row in rows]


# =============================================================================
# FINANCE TABLES SQL
# =============================================================================

FINANCE_TABLES = [
    """
    CREATE TABLE IF NOT EXISTS pf_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_code TEXT UNIQUE NOT NULL,
        account_name TEXT NOT NULL,
        account_type TEXT NOT NULL DEFAULT 'bank',
        account_subtype TEXT DEFAULT '',
        currency TEXT NOT NULL DEFAULT 'USD',
        opening_balance REAL DEFAULT 0.0,
        current_balance REAL DEFAULT 0.0,
        bank_provider TEXT DEFAULT '',
        branch_reference TEXT DEFAULT '',
        owner_user_id INTEGER DEFAULT 1,
        family_profile_id INTEGER DEFAULT 0,
        is_shared INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        is_archived INTEGER DEFAULT 0,
        reconciliation_status TEXT DEFAULT 'not_reconciled',
        last_reconciled_at TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 1,
        updated_at TEXT DEFAULT (datetime('now')),
        updated_by INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_account_transfers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transfer_code TEXT UNIQUE NOT NULL,
        from_account_id INTEGER NOT NULL,
        to_account_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        currency TEXT NOT NULL DEFAULT 'USD',
        exchange_rate REAL DEFAULT 1.0,
        transfer_date TEXT NOT NULL,
        transfer_type TEXT DEFAULT 'manual',
        status TEXT DEFAULT 'completed',
        notes TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_income_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        income_number TEXT UNIQUE NOT NULL,
        income_type TEXT NOT NULL DEFAULT 'salary',
        source TEXT NOT NULL DEFAULT '',
        source_name TEXT DEFAULT '',
        amount REAL NOT NULL,
        currency TEXT NOT NULL DEFAULT 'USD',
        exchange_rate REAL DEFAULT 1.0,
        amount_base_currency REAL DEFAULT 0.0,
        income_date TEXT NOT NULL,
        account_id INTEGER DEFAULT 0,
        category_id INTEGER DEFAULT 0,
        is_recurring INTEGER DEFAULT 0,
        recurring_pattern TEXT DEFAULT '',
        tax_amount REAL DEFAULT 0.0,
        fee_amount REAL DEFAULT 0.0,
        status TEXT DEFAULT 'received',
        receipt_document_id INTEGER DEFAULT 0,
        notes TEXT DEFAULT '',
        tags TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        is_archived INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 1,
        updated_at TEXT DEFAULT (datetime('now')),
        updated_by INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_expense_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        expense_number TEXT UNIQUE NOT NULL,
        merchant_name TEXT NOT NULL DEFAULT '',
        merchant_category TEXT DEFAULT '',
        amount REAL NOT NULL,
        currency TEXT NOT NULL DEFAULT 'USD',
        exchange_rate REAL DEFAULT 1.0,
        amount_base_currency REAL DEFAULT 0.0,
        expense_date TEXT NOT NULL,
        account_id INTEGER DEFAULT 0,
        category_id INTEGER DEFAULT 0,
        payment_method TEXT DEFAULT 'cash',
        is_recurring INTEGER DEFAULT 0,
        recurring_pattern TEXT DEFAULT '',
        receipt_document_id INTEGER DEFAULT 0,
        is_flagged INTEGER DEFAULT 0,
        flag_reason TEXT DEFAULT '',
        status TEXT DEFAULT 'approved',
        tags TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        is_archived INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 1,
        updated_at TEXT DEFAULT (datetime('now')),
        updated_by INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_code TEXT UNIQUE NOT NULL,
        transaction_type TEXT NOT NULL DEFAULT 'expense',
        amount REAL NOT NULL,
        currency TEXT NOT NULL DEFAULT 'USD',
        exchange_rate REAL DEFAULT 1.0,
        amount_base_currency REAL DEFAULT 0.0,
        transaction_date TEXT NOT NULL,
        account_id INTEGER DEFAULT 0,
        income_record_id INTEGER DEFAULT 0,
        expense_record_id INTEGER DEFAULT 0,
        transfer_id INTEGER DEFAULT 0,
        category_id INTEGER DEFAULT 0,
        merchant_payee TEXT DEFAULT '',
        description TEXT DEFAULT '',
        payment_method TEXT DEFAULT 'cash',
        is_recurring INTEGER DEFAULT 0,
        recurring_pattern TEXT DEFAULT '',
        recurring_template_id INTEGER DEFAULT 0,
        scheduled_transaction_id INTEGER DEFAULT 0,
        status TEXT DEFAULT 'completed',
        is_confirmed INTEGER DEFAULT 1,
        is_flagged INTEGER DEFAULT 0,
        flag_reason TEXT DEFAULT '',
        is_split INTEGER DEFAULT 0,
        parent_transaction_id INTEGER DEFAULT 0,
        receipt_document_id INTEGER DEFAULT 0,
        tags TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        is_archived INTEGER DEFAULT 0,
        archived_at TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 1,
        updated_at TEXT DEFAULT (datetime('now')),
        updated_by INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_transaction_splits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        transaction_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        description TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_budgets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        budget_code TEXT UNIQUE NOT NULL,
        budget_name TEXT NOT NULL,
        budget_type TEXT NOT NULL DEFAULT 'monthly',
        budget_scope TEXT DEFAULT 'personal',
        total_budget REAL DEFAULT 0.0,
        currency TEXT NOT NULL DEFAULT 'USD',
        period_start_date TEXT DEFAULT '',
        period_end_date TEXT DEFAULT '',
        warning_threshold REAL DEFAULT 80.0,
        hard_cap INTEGER DEFAULT 1,
        rollover_enabled INTEGER DEFAULT 0,
        rollover_amount REAL DEFAULT 0.0,
        owner_user_id INTEGER DEFAULT 1,
        family_profile_id INTEGER DEFAULT 0,
        is_shared INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        notes TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        is_archived INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 1,
        updated_at TEXT DEFAULT (datetime('now')),
        updated_by INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_budget_lines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        budget_id INTEGER NOT NULL,
        category_id INTEGER NOT NULL,
        allocated_amount REAL NOT NULL,
        spent_amount REAL DEFAULT 0.0,
        remaining_amount REAL DEFAULT 0.0,
        warning_threshold REAL DEFAULT 80.0,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_savings_buckets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bucket_code TEXT UNIQUE NOT NULL,
        bucket_name TEXT NOT NULL,
        goal_id INTEGER DEFAULT 0,
        savings_type TEXT DEFAULT 'general',
        current_amount REAL DEFAULT 0.0,
        target_amount REAL DEFAULT 0.0,
        currency TEXT NOT NULL DEFAULT 'USD',
        priority INTEGER DEFAULT 1,
        recurring_amount REAL DEFAULT 0.0,
        recurring_frequency TEXT DEFAULT 'monthly',
        owner_user_id INTEGER DEFAULT 1,
        family_profile_id INTEGER DEFAULT 0,
        is_auto_transfer INTEGER DEFAULT 0,
        linked_account_id INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        notes TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        is_archived INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 1,
        updated_at TEXT DEFAULT (datetime('now')),
        updated_by INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_financial_goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_code TEXT UNIQUE NOT NULL,
        goal_name TEXT NOT NULL,
        goal_type TEXT NOT NULL DEFAULT 'short_term',
        target_amount REAL NOT NULL,
        current_progress REAL DEFAULT 0.0,
        currency TEXT NOT NULL DEFAULT 'USD',
        target_date TEXT DEFAULT '',
        priority INTEGER DEFAULT 2,
        linked_savings_bucket_id INTEGER DEFAULT 0,
        linked_budget_id INTEGER DEFAULT 0,
        owner_user_id INTEGER DEFAULT 1,
        family_profile_id INTEGER DEFAULT 0,
        status TEXT DEFAULT 'draft',
        notes TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        is_archived INTEGER DEFAULT 0,
        achieved_at TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 1,
        updated_at TEXT DEFAULT (datetime('now')),
        updated_by INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_investments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_code TEXT UNIQUE NOT NULL,
        asset_name TEXT NOT NULL,
        asset_class TEXT NOT NULL DEFAULT 'stock',
        asset_subclass TEXT DEFAULT '',
        quantity REAL DEFAULT 0.0,
        purchase_price REAL DEFAULT 0.0,
        purchase_value REAL DEFAULT 0.0,
        current_price REAL DEFAULT 0.0,
        current_value REAL DEFAULT 0.0,
        cost_basis REAL DEFAULT 0.0,
        realized_gain_loss REAL DEFAULT 0.0,
        unrealized_gain_loss REAL DEFAULT 0.0,
        dividends_received REAL DEFAULT 0.0,
        currency TEXT NOT NULL DEFAULT 'USD',
        acquisition_date TEXT DEFAULT '',
        disposal_date TEXT DEFAULT '',
        linked_account_id INTEGER DEFAULT 0,
        risk_level TEXT DEFAULT 'medium',
        broker_provider TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        status TEXT DEFAULT 'held',
        is_active INTEGER DEFAULT 1,
        is_archived INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 1,
        updated_at TEXT DEFAULT (datetime('now')),
        updated_by INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_investment_valuations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_id INTEGER NOT NULL,
        valuation_date TEXT NOT NULL,
        price_per_unit REAL DEFAULT 0.0,
        total_value REAL DEFAULT 0.0,
        gain_loss REAL DEFAULT 0.0,
        gain_loss_percent REAL DEFAULT 0.0,
        notes TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_debts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        debt_code TEXT UNIQUE NOT NULL,
        lender TEXT NOT NULL DEFAULT '',
        debt_type TEXT NOT NULL DEFAULT 'loan',
        principal REAL NOT NULL,
        remaining_balance REAL DEFAULT 0.0,
        monthly_installment REAL DEFAULT 0.0,
        interest_rate REAL DEFAULT 0.0,
        interest_type TEXT DEFAULT 'fixed',
        start_date TEXT DEFAULT '',
        end_date TEXT DEFAULT '',
        next_due_date TEXT DEFAULT '',
        total_paid REAL DEFAULT 0.0,
        total_interest_paid REAL DEFAULT 0.0,
        priority INTEGER DEFAULT 2,
        linked_account_id INTEGER DEFAULT 0,
        owner_user_id INTEGER DEFAULT 1,
        family_profile_id INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        notes TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        is_archived INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 1,
        updated_at TEXT DEFAULT (datetime('now')),
        updated_by INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_debt_installments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        debt_id INTEGER NOT NULL,
        installment_number INTEGER NOT NULL,
        due_date TEXT NOT NULL,
        principal_amount REAL DEFAULT 0.0,
        interest_amount REAL DEFAULT 0.0,
        total_amount REAL DEFAULT 0.0,
        paid_amount REAL DEFAULT 0.0,
        paid_date TEXT DEFAULT '',
        status TEXT DEFAULT 'pending',
        notes TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_code TEXT UNIQUE NOT NULL,
        asset_type TEXT NOT NULL DEFAULT 'cash',
        asset_name TEXT NOT NULL,
        purchase_value REAL DEFAULT 0.0,
        current_value REAL DEFAULT 0.0,
        depreciation_rate REAL DEFAULT 0.0,
        depreciation_method TEXT DEFAULT 'straight_line',
        currency TEXT NOT NULL DEFAULT 'USD',
        acquisition_date TEXT DEFAULT '',
        linked_documents TEXT DEFAULT '',
        owner_user_id INTEGER DEFAULT 1,
        family_profile_id INTEGER DEFAULT 0,
        status TEXT DEFAULT 'owned',
        notes TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        is_archived INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 1,
        updated_at TEXT DEFAULT (datetime('now')),
        updated_by INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_asset_valuations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id INTEGER NOT NULL,
        valuation_date TEXT NOT NULL,
        value REAL DEFAULT 0.0,
        change_from_previous REAL DEFAULT 0.0,
        change_percent REAL DEFAULT 0.0,
        notes TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_cashflow_snapshots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        snapshot_date TEXT NOT NULL,
        total_inflow REAL DEFAULT 0.0,
        total_outflow REAL DEFAULT 0.0,
        net_cashflow REAL DEFAULT 0.0,
        opening_balance REAL DEFAULT 0.0,
        closing_balance REAL DEFAULT 0.0,
        lowest_balance REAL DEFAULT 0.0,
        highest_balance REAL DEFAULT 0.0,
        currency TEXT DEFAULT 'USD',
        account_id INTEGER DEFAULT 0,
        owner_user_id INTEGER DEFAULT 1,
        notes TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        subscription_number TEXT UNIQUE NOT NULL,
        provider TEXT NOT NULL DEFAULT '',
        service_type TEXT NOT NULL DEFAULT 'general',
        plan_name TEXT DEFAULT '',
        amount REAL NOT NULL,
        currency TEXT NOT NULL DEFAULT 'USD',
        billing_cycle TEXT DEFAULT 'monthly',
        renewal_date TEXT NOT NULL,
        auto_renew INTEGER DEFAULT 1,
        category_id INTEGER DEFAULT 0,
        account_id INTEGER DEFAULT 0,
        reminder_days INTEGER DEFAULT 3,
        owner_user_id INTEGER DEFAULT 1,
        family_profile_id INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        cancelled_at TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        is_archived INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 1,
        updated_at TEXT DEFAULT (datetime('now')),
        updated_by INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_calendar_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        event_code TEXT UNIQUE NOT NULL,
        event_type TEXT NOT NULL DEFAULT 'payment_due',
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        event_date TEXT NOT NULL,
        end_date TEXT DEFAULT '',
        amount REAL DEFAULT 0.0,
        currency TEXT DEFAULT 'USD',
        linked_entity_type TEXT DEFAULT '',
        linked_entity_id INTEGER DEFAULT 0,
        reminder_date TEXT DEFAULT '',
        reminder_enabled INTEGER DEFAULT 1,
        is_recurring INTEGER DEFAULT 0,
        recurring_pattern TEXT DEFAULT '',
        owner_user_id INTEGER DEFAULT 1,
        family_profile_id INTEGER DEFAULT 0,
        status TEXT DEFAULT 'scheduled',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 1,
        updated_at TEXT DEFAULT (datetime('now')),
        updated_by INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alert_code TEXT UNIQUE NOT NULL,
        alert_type TEXT NOT NULL,
        title TEXT NOT NULL,
        message TEXT DEFAULT '',
        severity TEXT DEFAULT 'info',
        amount REAL DEFAULT 0.0,
        currency TEXT DEFAULT 'USD',
        linked_entity_type TEXT DEFAULT '',
        linked_entity_id INTEGER DEFAULT 0,
        is_read INTEGER DEFAULT 0,
        is_dismissed INTEGER DEFAULT 0,
        read_at TEXT DEFAULT '',
        dismissed_at TEXT DEFAULT '',
        due_date TEXT DEFAULT '',
        owner_user_id INTEGER DEFAULT 1,
        family_profile_id INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_category_definitions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_code TEXT UNIQUE NOT NULL,
        category_name TEXT NOT NULL,
        category_type TEXT NOT NULL DEFAULT 'expense',
        parent_id INTEGER DEFAULT 0,
        icon TEXT DEFAULT 'fa-folder',
        color TEXT DEFAULT '#6B7280',
        sort_order INTEGER DEFAULT 0,
        is_system INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 1,
        updated_at TEXT DEFAULT (datetime('now')),
        updated_by INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_automation_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_code TEXT UNIQUE NOT NULL,
        rule_name TEXT NOT NULL,
        rule_type TEXT NOT NULL DEFAULT 'auto_categorize',
        condition_json TEXT DEFAULT '{}',
        action_json TEXT DEFAULT '{}',
        priority INTEGER DEFAULT 5,
        is_enabled INTEGER DEFAULT 1,
        owner_user_id INTEGER DEFAULT 1,
        family_profile_id INTEGER DEFAULT 0,
        last_triggered_at TEXT DEFAULT '',
        trigger_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        notes TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 1,
        updated_at TEXT DEFAULT (datetime('now')),
        updated_by INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_receipts_documents_links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id INTEGER NOT NULL,
        document_type TEXT DEFAULT 'receipt',
        file_name TEXT DEFAULT '',
        file_path TEXT DEFAULT '',
        file_size INTEGER DEFAULT 0,
        mime_type TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_currency_rates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_currency TEXT NOT NULL,
        to_currency TEXT NOT NULL,
        rate REAL NOT NULL DEFAULT 1.0,
        rate_date TEXT NOT NULL,
        source TEXT DEFAULT 'manual',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_family_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        profile_code TEXT UNIQUE NOT NULL,
        profile_name TEXT NOT NULL,
        profile_type TEXT DEFAULT 'personal',
        primary_user_id INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 1,
        updated_at TEXT DEFAULT (datetime('now')),
        updated_by INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_family_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        family_profile_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        role TEXT DEFAULT 'member',
        can_view INTEGER DEFAULT 1,
        can_edit INTEGER DEFAULT 0,
        can_delete INTEGER DEFAULT 0,
        can_approve INTEGER DEFAULT 0,
        expense_limit REAL DEFAULT 0.0,
        is_active INTEGER DEFAULT 1,
        joined_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_export_presets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        preset_code TEXT UNIQUE NOT NULL,
        preset_name TEXT NOT NULL,
        export_type TEXT NOT NULL DEFAULT 'transactions',
        columns_json TEXT DEFAULT '[]',
        filters_json TEXT DEFAULT '{}',
        sort_json TEXT DEFAULT '{}',
        format_type TEXT DEFAULT 'csv',
        includeArchived INTEGER DEFAULT 0,
        owner_user_id INTEGER DEFAULT 1,
        is_shared INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 1,
        updated_at TEXT DEFAULT (datetime('now')),
        updated_by INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_dashboard_preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        preference_key TEXT NOT NULL,
        preference_value TEXT DEFAULT '{}',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_import_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        import_code TEXT UNIQUE NOT NULL,
        import_type TEXT NOT NULL,
        file_name TEXT DEFAULT '',
        file_path TEXT DEFAULT '',
        total_rows INTEGER DEFAULT 0,
        imported_rows INTEGER DEFAULT 0,
        failed_rows INTEGER DEFAULT 0,
        errors_json TEXT DEFAULT '[]',
        status TEXT DEFAULT 'pending',
        owner_user_id INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        completed_at TEXT DEFAULT ''
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_backup_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        backup_code TEXT UNIQUE NOT NULL,
        backup_type TEXT DEFAULT 'manual',
        file_path TEXT DEFAULT '',
        file_size INTEGER DEFAULT 0,
        record_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'completed',
        notes TEXT DEFAULT '',
        owner_user_id INTEGER DEFAULT 1,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_audit_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        audit_code TEXT UNIQUE NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        field_name TEXT DEFAULT '',
        old_value TEXT DEFAULT '',
        new_value TEXT DEFAULT '',
        user_id INTEGER DEFAULT 1,
        user_name TEXT DEFAULT '',
        ip_address TEXT DEFAULT '',
        user_agent TEXT DEFAULT '',
        notes TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT UNIQUE NOT NULL,
        setting_value TEXT DEFAULT '',
        setting_type TEXT DEFAULT 'string',
        category TEXT DEFAULT 'general',
        is_encrypted INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        updated_by INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_recurring_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_code TEXT UNIQUE NOT NULL,
        template_name TEXT NOT NULL,
        transaction_type TEXT NOT NULL DEFAULT 'expense',
        amount REAL NOT NULL,
        currency TEXT DEFAULT 'USD',
        account_id INTEGER DEFAULT 0,
        category_id INTEGER DEFAULT 0,
        merchant_payee TEXT DEFAULT '',
        description TEXT DEFAULT '',
        payment_method TEXT DEFAULT 'cash',
        recurring_pattern TEXT NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT DEFAULT '',
        next_occurrence TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        last_triggered_at TEXT DEFAULT '',
        trigger_count INTEGER DEFAULT 0,
        notes TEXT DEFAULT '',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        created_by INTEGER DEFAULT 1,
        updated_at TEXT DEFAULT (datetime('now')),
        updated_by INTEGER DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pf_financial_health_scores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        score_date TEXT NOT NULL,
        total_score REAL DEFAULT 0.0,
        income_score REAL DEFAULT 0.0,
        expense_score REAL DEFAULT 0.0,
        savings_score REAL DEFAULT 0.0,
        debt_score REAL DEFAULT 0.0,
        investment_score REAL DEFAULT 0.0,
        asset_score REAL DEFAULT 0.0,
        emergency_coverage_score REAL DEFAULT 0.0,
        debt_to_income_ratio REAL DEFAULT 0.0,
        savings_rate REAL DEFAULT 0.0,
        expense_to_income_ratio REAL DEFAULT 0.0,
        details_json TEXT DEFAULT '{}',
        created_at TEXT DEFAULT (datetime('now'))
    )
    """
]


# =============================================================================
# INDEXES FOR PERFORMANCE
# =============================================================================

FINANCE_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_pf_accounts_code ON pf_accounts(account_code)",
    "CREATE INDEX IF NOT EXISTS idx_pf_accounts_owner ON pf_accounts(owner_user_id)",
    "CREATE INDEX IF NOT EXISTS idx_pf_accounts_type ON pf_accounts(account_type)",
    "CREATE INDEX IF NOT EXISTS idx_pf_accounts_currency ON pf_accounts(currency)",
    "CREATE INDEX IF NOT EXISTS idx_pf_transactions_code ON pf_transactions(transaction_code)",
    "CREATE INDEX IF NOT EXISTS idx_pf_transactions_date ON pf_transactions(transaction_date)",
    "CREATE INDEX IF NOT EXISTS idx_pf_transactions_type ON pf_transactions(transaction_type)",
    "CREATE INDEX IF NOT EXISTS idx_pf_transactions_account ON pf_transactions(account_id)",
    "CREATE INDEX IF NOT EXISTS idx_pf_transactions_category ON pf_transactions(category_id)",
    "CREATE INDEX IF NOT EXISTS idx_pf_transactions_status ON pf_transactions(status)",
    "CREATE INDEX IF NOT EXISTS idx_pf_income_records_number ON pf_income_records(income_number)",
    "CREATE INDEX IF NOT EXISTS idx_pf_income_records_date ON pf_income_records(income_date)",
    "CREATE INDEX IF NOT EXISTS idx_pf_expense_records_number ON pf_expense_records(expense_number)",
    "CREATE INDEX IF NOT EXISTS idx_pf_expense_records_date ON pf_expense_records(expense_date)",
    "CREATE INDEX IF NOT EXISTS idx_pf_budgets_code ON pf_budgets(budget_code)",
    "CREATE INDEX IF NOT EXISTS idx_pf_budgets_type ON pf_budgets(budget_type)",
    "CREATE INDEX IF NOT EXISTS idx_pf_goals_code ON pf_financial_goals(goal_code)",
    "CREATE INDEX IF NOT EXISTS idx_pf_goals_status ON pf_financial_goals(status)",
    "CREATE INDEX IF NOT EXISTS idx_pf_investments_code ON pf_investments(investment_code)",
    "CREATE INDEX IF NOT EXISTS idx_pf_investments_class ON pf_investments(asset_class)",
    "CREATE INDEX IF NOT EXISTS idx_pf_debts_code ON pf_debts(debt_code)",
    "CREATE INDEX IF NOT EXISTS idx_pf_debts_status ON pf_debts(status)",
    "CREATE INDEX IF NOT EXISTS idx_pf_assets_code ON pf_assets(asset_code)",
    "CREATE INDEX IF NOT EXISTS idx_pf_assets_type ON pf_assets(asset_type)",
    "CREATE INDEX IF NOT EXISTS idx_pf_subscriptions_number ON pf_subscriptions(subscription_number)",
    "CREATE INDEX IF NOT EXISTS idx_pf_subscriptions_renewal ON pf_subscriptions(renewal_date)",
    "CREATE INDEX IF NOT EXISTS idx_pf_alerts_type ON pf_alerts(alert_type)",
    "CREATE INDEX IF NOT EXISTS idx_pf_alerts_owner ON pf_alerts(owner_user_id)",
    "CREATE INDEX IF NOT EXISTS idx_pf_alerts_read ON pf_alerts(is_read)",
    "CREATE INDEX IF NOT EXISTS idx_pf_categories_type ON pf_category_definitions(category_type)",
    "CREATE INDEX IF NOT EXISTS idx_pf_calendar_date ON pf_calendar_events(event_date)",
    "CREATE INDEX IF NOT EXISTS idx_pf_calendar_type ON pf_calendar_events(event_type)"
]


# =============================================================================
# INITIALIZE TABLES
# =============================================================================

def initialize_finance_tables():
    """Create all Personal Finance tables."""
    with get_db_context() as db:
        for table_sql in FINANCE_TABLES:
            db.execute(table_sql)
        for index_sql in FINANCE_INDEXES:
            db.execute(index_sql)
        db.commit()
    return True


# =============================================================================
# DATACLASS MODELS
# =============================================================================

@dataclass
class PFAccount:
    id: int = 0
    account_code: str = ""
    account_name: str = ""
    account_type: str = "bank"
    account_subtype: str = ""
    currency: str = "USD"
    opening_balance: float = 0.0
    current_balance: float = 0.0
    bank_provider: str = ""
    branch_reference: str = ""
    owner_user_id: int = 1
    family_profile_id: int = 0
    is_shared: int = 0
    is_active: int = 1
    is_archived: int = 0
    reconciliation_status: str = "not_reconciled"
    last_reconciled_at: str = ""
    notes: str = ""
    created_at: str = ""
    created_by: int = 1
    updated_at: str = ""
    updated_by: int = 1

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PFIncomeRecord:
    id: int = 0
    income_number: str = ""
    income_type: str = "salary"
    source: str = ""
    source_name: str = ""
    amount: float = 0.0
    currency: str = "USD"
    exchange_rate: float = 1.0
    amount_base_currency: float = 0.0
    income_date: str = ""
    account_id: int = 0
    category_id: int = 0
    is_recurring: int = 0
    recurring_pattern: str = ""
    tax_amount: float = 0.0
    fee_amount: float = 0.0
    status: str = "received"
    receipt_document_id: int = 0
    notes: str = ""
    tags: str = ""
    is_active: int = 1
    is_archived: int = 0
    created_at: str = ""
    created_by: int = 1
    updated_at: str = ""
    updated_by: int = 1

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PFExpenseRecord:
    id: int = 0
    expense_number: str = ""
    merchant_name: str = ""
    merchant_category: str = ""
    amount: float = 0.0
    currency: str = "USD"
    exchange_rate: float = 1.0
    amount_base_currency: float = 0.0
    expense_date: str = ""
    account_id: int = 0
    category_id: int = 0
    payment_method: str = "cash"
    is_recurring: int = 0
    recurring_pattern: str = ""
    receipt_document_id: int = 0
    is_flagged: int = 0
    flag_reason: str = ""
    status: str = "approved"
    tags: str = ""
    notes: str = ""
    is_active: int = 1
    is_archived: int = 0
    created_at: str = ""
    created_by: int = 1
    updated_at: str = ""
    updated_by: int = 1

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PFTransaction:
    id: int = 0
    transaction_code: str = ""
    transaction_type: str = "expense"
    amount: float = 0.0
    currency: str = "USD"
    exchange_rate: float = 1.0
    amount_base_currency: float = 0.0
    transaction_date: str = ""
    account_id: int = 0
    income_record_id: int = 0
    expense_record_id: int = 0
    transfer_id: int = 0
    category_id: int = 0
    merchant_payee: str = ""
    description: str = ""
    payment_method: str = "cash"
    is_recurring: int = 0
    recurring_pattern: str = ""
    recurring_template_id: int = 0
    scheduled_transaction_id: int = 0
    status: str = "completed"
    is_confirmed: int = 1
    is_flagged: int = 0
    flag_reason: str = ""
    is_split: int = 0
    parent_transaction_id: int = 0
    receipt_document_id: int = 0
    tags: str = ""
    notes: str = ""
    is_active: int = 1
    is_archived: int = 0
    archived_at: str = ""
    created_at: str = ""
    created_by: int = 1
    updated_at: str = ""
    updated_by: int = 1

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PFBudget:
    id: int = 0
    budget_code: str = ""
    budget_name: str = ""
    budget_type: str = "monthly"
    budget_scope: str = "personal"
    total_budget: float = 0.0
    currency: str = "USD"
    period_start_date: str = ""
    period_end_date: str = ""
    warning_threshold: float = 80.0
    hard_cap: int = 1
    rollover_enabled: int = 0
    rollover_amount: float = 0.0
    owner_user_id: int = 1
    family_profile_id: int = 0
    is_shared: int = 0
    status: str = "active"
    notes: str = ""
    is_active: int = 1
    is_archived: int = 0
    created_at: str = ""
    created_by: int = 1
    updated_at: str = ""
    updated_by: int = 1

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PFFinancialGoal:
    id: int = 0
    goal_code: str = ""
    goal_name: str = ""
    goal_type: str = "short_term"
    target_amount: float = 0.0
    current_progress: float = 0.0
    currency: str = "USD"
    target_date: str = ""
    priority: int = 2
    linked_savings_bucket_id: int = 0
    linked_budget_id: int = 0
    owner_user_id: int = 1
    family_profile_id: int = 0
    status: str = "draft"
    notes: str = ""
    is_active: int = 1
    is_archived: int = 0
    achieved_at: str = ""
    created_at: str = ""
    created_by: int = 1
    updated_at: str = ""
    updated_by: int = 1

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PFInvestment:
    id: int = 0
    investment_code: str = ""
    asset_name: str = ""
    asset_class: str = "stock"
    asset_subclass: str = ""
    quantity: float = 0.0
    purchase_price: float = 0.0
    purchase_value: float = 0.0
    current_price: float = 0.0
    current_value: float = 0.0
    cost_basis: float = 0.0
    realized_gain_loss: float = 0.0
    unrealized_gain_loss: float = 0.0
    dividends_received: float = 0.0
    currency: str = "USD"
    acquisition_date: str = ""
    disposal_date: str = ""
    linked_account_id: int = 0
    risk_level: str = "medium"
    broker_provider: str = ""
    notes: str = ""
    status: str = "held"
    is_active: int = 1
    is_archived: int = 0
    created_at: str = ""
    created_by: int = 1
    updated_at: str = ""
    updated_by: int = 1

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PFDebt:
    id: int = 0
    debt_code: str = ""
    lender: str = ""
    debt_type: str = "loan"
    principal: float = 0.0
    remaining_balance: float = 0.0
    monthly_installment: float = 0.0
    interest_rate: float = 0.0
    interest_type: str = "fixed"
    start_date: str = ""
    end_date: str = ""
    next_due_date: str = ""
    total_paid: float = 0.0
    total_interest_paid: float = 0.0
    priority: int = 2
    linked_account_id: int = 0
    owner_user_id: int = 1
    family_profile_id: int = 0
    status: str = "active"
    notes: str = ""
    is_active: int = 1
    is_archived: int = 0
    created_at: str = ""
    created_by: int = 1
    updated_at: str = ""
    updated_by: int = 1

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PFAsset:
    id: int = 0
    asset_code: str = ""
    asset_type: str = "cash"
    asset_name: str = ""
    purchase_value: float = 0.0
    current_value: float = 0.0
    depreciation_rate: float = 0.0
    depreciation_method: str = "straight_line"
    currency: str = "USD"
    acquisition_date: str = ""
    linked_documents: str = ""
    owner_user_id: int = 1
    family_profile_id: int = 0
    status: str = "owned"
    notes: str = ""
    is_active: int = 1
    is_archived: int = 0
    created_at: str = ""
    created_by: int = 1
    updated_at: str = ""
    updated_by: int = 1

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PFSubscription:
    id: int = 0
    subscription_number: str = ""
    provider: str = ""
    service_type: str = "general"
    plan_name: str = ""
    amount: float = 0.0
    currency: str = "USD"
    billing_cycle: str = "monthly"
    renewal_date: str = ""
    auto_renew: int = 1
    category_id: int = 0
    account_id: int = 0
    reminder_days: int = 3
    owner_user_id: int = 1
    family_profile_id: int = 0
    status: str = "active"
    cancelled_at: str = ""
    notes: str = ""
    is_active: int = 1
    is_archived: int = 0
    created_at: str = ""
    created_by: int = 1
    updated_at: str = ""
    updated_by: int = 1

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PFCategory:
    id: int = 0
    category_code: str = ""
    category_name: str = ""
    category_type: str = "expense"
    parent_id: int = 0
    icon: str = "fa-folder"
    color: str = "#6B7280"
    sort_order: int = 0
    is_system: int = 0
    is_active: int = 1
    created_at: str = ""
    created_by: int = 1
    updated_at: str = ""
    updated_by: int = 1

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PFAlert:
    id: int = 0
    alert_code: str = ""
    alert_type: str = ""
    title: str = ""
    message: str = ""
    severity: str = "info"
    amount: float = 0.0
    currency: str = "USD"
    linked_entity_type: str = ""
    linked_entity_id: int = 0
    is_read: int = 0
    is_dismissed: int = 0
    read_at: str = ""
    dismissed_at: str = ""
    due_date: str = ""
    owner_user_id: int = 1
    family_profile_id: int = 0
    is_active: int = 1
    created_at: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


# =============================================================================
# HELPER FUNCTIONS FOR FINANCE OPERATIONS
# =============================================================================

def generate_account_code() -> str:
    """Generate unique account code."""
    return f"ACC-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def generate_income_number() -> str:
    """Generate unique income number."""
    return f"INC-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def generate_expense_number() -> str:
    """Generate unique expense number."""
    return f"EXP-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def generate_transaction_code() -> str:
    """Generate unique transaction code."""
    return f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def generate_budget_code() -> str:
    """Generate unique budget code."""
    return f"BDG-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def generate_goal_code() -> str:
    """Generate unique goal code."""
    return f"GL-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def generate_investment_code() -> str:
    """Generate unique investment code."""
    return f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def generate_debt_code() -> str:
    """Generate unique debt code."""
    return f"DEBT-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def generate_asset_code() -> str:
    """Generate unique asset code."""
    return f"AST-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def generate_subscription_number() -> str:
    """Generate unique subscription number."""
    return f"SUB-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def generate_alert_code() -> str:
    """Generate unique alert code."""
    return f"ALT-{datetime.now().strftime('%Y%m%d%H%M%S')}"


def get_account_balance(account_id: int) -> float:
    """Calculate current balance for an account based on transactions."""
    result = get_one("""
        SELECT 
            COALESCE(opening_balance, 0) as opening,
            COALESCE(SUM(CASE WHEN transaction_type = 'income' AND is_active = 1 THEN amount ELSE 0 END), 0) as total_income,
            COALESCE(SUM(CASE WHEN transaction_type = 'expense' AND is_active = 1 THEN amount ELSE 0 END), 0) as total_expense,
            COALESCE(SUM(CASE WHEN transaction_type = 'transfer' AND from_account_id = ? AND is_active = 1 THEN amount ELSE 0 END), 0) as transfers_out,
            COALESCE(SUM(CASE WHEN transaction_type = 'transfer' AND to_account_id = ? AND is_active = 1 THEN amount ELSE 0 END), 0) as transfers_in
        FROM pf_accounts a
        LEFT JOIN pf_transactions t ON t.account_id = a.id
        WHERE a.id = ?
        GROUP BY a.id
    """, (account_id, account_id, account_id))
    
    if result:
        return (result['opening'] + result['total_income'] + result['transfers_in'] - 
                result['total_expense'] - result['transfers_out'])
    return 0.0


def calculate_financial_health_score(user_id: int = 1) -> Dict:
    """Calculate overall financial health score (0-100)."""
    today = datetime.now().strftime('%Y-%m-%d')
    month_start = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    
    # Get income for current month
    income = get_one("""
        SELECT COALESCE(SUM(amount), 0) as total FROM pf_income_records
        WHERE owner_user_id = ? AND income_date >= ? AND is_active = 1 AND status = 'received'
    """, (user_id, month_start))
    total_income = income['total'] if income else 0
    
    # Get expenses for current month
    expenses = get_one("""
        SELECT COALESCE(SUM(amount), 0) as total FROM pf_expense_records
        WHERE owner_user_id = ? AND expense_date >= ? AND is_active = 1 AND status = 'approved'
    """, (user_id, month_start))
    total_expenses = expenses['total'] if expenses else 0
    
    # Get savings
    savings = get_one("""
        SELECT COALESCE(SUM(current_amount), 0) as total FROM pf_savings_buckets
        WHERE owner_user_id = ? AND is_active = 1
    """, (user_id,))
    total_savings = savings['total'] if savings else 0
    
    # Get total debts
    debts = get_one("""
        SELECT COALESCE(SUM(remaining_balance), 0) as total FROM pf_debts
        WHERE owner_user_id = ? AND is_active = 1 AND status = 'active'
    """, (user_id,))
    total_debts = debts['total'] if debts else 0
    
    # Get total investments
    investments = get_one("""
        SELECT COALESCE(SUM(current_value), 0) as total FROM pf_investments
        WHERE owner_user_id = ? AND is_active = 1 AND status = 'held'
    """, (user_id,))
    total_investments = investments['total'] if investments else 0
    
    # Get total assets
    assets = get_one("""
        SELECT COALESCE(SUM(current_value), 0) as total FROM pf_assets
        WHERE owner_user_id = ? AND is_active = 1 AND status = 'owned'
    """, (user_id,))
    total_assets = assets['total'] if assets else 0
    
    # Calculate net worth
    net_worth = total_assets + total_savings + total_investments - total_debts
    
    # Calculate scores
    scores = {}
    
    # Income score (0-25) - based on income stability and amount
    if total_income > 0:
        scores['income_score'] = min(25, (total_income / 10000) * 25)
    else:
        scores['income_score'] = 0
    
    # Expense score (0-25) - lower expenses relative to income is better
    if total_income > 0:
        expense_ratio = total_expenses / total_income
        if expense_ratio <= 0.5:
            scores['expense_score'] = 25
        elif expense_ratio <= 0.7:
            scores['expense_score'] = 20
        elif expense_ratio <= 0.85:
            scores['expense_score'] = 15
        elif expense_ratio <= 1.0:
            scores['expense_score'] = 10
        else:
            scores['expense_score'] = 5
    else:
        scores['expense_score'] = 0
    
    # Savings score (0-20) - savings rate
    if total_income > 0:
        savings_rate = (total_savings / total_income) * 100
        if savings_rate >= 20:
            scores['savings_score'] = 20
        elif savings_rate >= 15:
            scores['savings_score'] = 16
        elif savings_rate >= 10:
            scores['savings_score'] = 12
        elif savings_rate >= 5:
            scores['savings_score'] = 8
        else:
            scores['savings_score'] = 4
    else:
        scores['savings_score'] = 0
    
    # Debt score (0-15) - debt to income ratio
    if total_income > 0:
        debt_ratio = total_debts / total_income
        if debt_ratio <= 1:
            scores['debt_score'] = 15
        elif debt_ratio <= 2:
            scores['debt_score'] = 12
        elif debt_ratio <= 3:
            scores['debt_score'] = 8
        elif debt_ratio <= 5:
            scores['debt_score'] = 4
        else:
            scores['debt_score'] = 0
    else:
        scores['debt_score'] = 0
    
    # Investment score (0-10)
    if total_income > 0:
        investment_ratio = total_investments / total_income
        if investment_ratio >= 3:
            scores['investment_score'] = 10
        elif investment_ratio >= 2:
            scores['investment_score'] = 8
        elif investment_ratio >= 1:
            scores['investment_score'] = 6
        elif investment_ratio >= 0.5:
            scores['investment_score'] = 4
        else:
            scores['investment_score'] = 2
    else:
        scores['investment_score'] = 0
    
    # Asset score (0-5)
    if net_worth > 100000:
        scores['asset_score'] = 5
    elif net_worth > 50000:
        scores['asset_score'] = 4
    elif net_worth > 20000:
        scores['asset_score'] = 3
    elif net_worth > 5000:
        scores['asset_score'] = 2
    elif net_worth > 0:
        scores['asset_score'] = 1
    else:
        scores['asset_score'] = 0
    
    # Emergency coverage score (0-5) - months of expenses covered
    if total_expenses > 0:
        months_covered = total_savings / (total_expenses / 30)
        if months_covered >= 6:
            scores['emergency_coverage_score'] = 5
        elif months_covered >= 3:
            scores['emergency_coverage_score'] = 4
        elif months_covered >= 1:
            scores['emergency_coverage_score'] = 3
        elif months_covered >= 0.5:
            scores['emergency_coverage_score'] = 2
        else:
            scores['emergency_coverage_score'] = 1
    else:
        scores['emergency_coverage_score'] = 5  # No expenses = fully covered
    
    # Total score
    scores['total_score'] = sum(scores.values())
    
    # Ratios
    scores['debt_to_income_ratio'] = total_debts / total_income if total_income > 0 else 0
    scores['savings_rate'] = (total_savings / total_income * 100) if total_income > 0 else 0
    scores['expense_to_income_ratio'] = (total_expenses / total_income * 100) if total_income > 0 else 0
    scores['net_worth'] = net_worth
    scores['total_income'] = total_income
    scores['total_expenses'] = total_expenses
    scores['total_savings'] = total_savings
    scores['total_debts'] = total_debts
    scores['total_investments'] = total_investments
    scores['total_assets'] = total_assets
    
    return scores


def get_budget_status(budget_id: int) -> Dict:
    """Get budget spending status."""
    budget = get_one("SELECT * FROM pf_budgets WHERE id = ?", (budget_id,))
    if not budget:
        return {}
    
    # Get spent amount for budget lines
    spent = get_all("""
        SELECT bl.category_id, bl.allocated_amount, 
               COALESCE(SUM(er.amount), 0) as spent
        FROM pf_budget_lines bl
        LEFT JOIN pf_expense_records er ON er.category_id = bl.category_id
            AND er.expense_date >= ? AND er.expense_date <= ?
            AND er.is_active = 1 AND er.status = 'approved'
        WHERE bl.budget_id = ?
        GROUP BY bl.category_id
    """, (budget['period_start_date'], budget['period_end_date'], budget_id))
    
    total_spent = sum(row['spent'] for row in spent)
    total_budget = budget['total_budget']
    remaining = total_budget - total_spent
    percent_used = (total_spent / total_budget * 100) if total_budget > 0 else 0
    
    return {
        'budget_id': budget_id,
        'total_budget': total_budget,
        'total_spent': total_spent,
        'remaining': remaining,
        'percent_used': percent_used,
        'is_over_budget': total_spent > total_budget,
        'is_near_limit': percent_used >= budget['warning_threshold']
    }


def get_savings_progress(goal_id: int) -> Dict:
    """Get savings goal progress."""
    goal = get_one("SELECT * FROM pf_financial_goals WHERE id = ?", (goal_id,))
    if not goal:
        return {}
    
    current = goal['current_progress']
    target = goal['target_amount']
    percent = (current / target * 100) if target > 0 else 0
    
    remaining = target - current
    days_remaining = 0
    if goal['target_date']:
        target_date = datetime.strptime(goal['target_date'], '%Y-%m-%d')
        days_remaining = (target_date - datetime.now()).days
    
    required_monthly = remaining / max(days_remaining / 30, 1) if days_remaining > 0 else remaining
    
    return {
        'goal_id': goal_id,
        'goal_name': goal['goal_name'],
        'target_amount': target,
        'current_progress': current,
        'remaining': remaining,
        'percent_complete': percent,
        'days_remaining': days_remaining,
        'required_monthly_savings': required_monthly,
        'is_on_track': current >= (target * (1 - days_remaining / 365)) if days_remaining > 0 else True,
        'status': goal['status']
    }


# =============================================================================
# SEED DEFAULT DATA
# =============================================================================

DEFAULT_EXPENSE_CATEGORIES = [
    ('CAT-FOOD', 'Food & Dining', 'expense', 'fa-utensils', '#FF6B6B', 1),
    ('CAT-TRANS', 'Transportation', 'expense', 'fa-car', '#4ECDC4', 2),
    ('CAT-SHOP', 'Shopping', 'expense', 'fa-shopping-bag', '#45B7D1', 3),
    ('CAT-UTIL', 'Utilities', 'expense', 'fa-bolt', '#96CEB4', 4),
    ('CAT-HOUS', 'Housing', 'expense', 'fa-home', '#FFEAA7', 5),
    ('CAT-HEAL', 'Healthcare', 'expense', 'fa-heartbeat', '#DDA0DD', 6),
    ('CAT-ENT', 'Entertainment', 'expense', 'fa-film', '#98D8C8', 7),
    ('CAT-EDU', 'Education', 'expense', 'fa-graduation-cap', '#F7DC6F', 8),
    ('CAT-PERS', 'Personal Care', 'expense', 'fa-spa', '#BB8FCE', 9),
    ('CAT-GIFT', 'Gifts & Donations', 'expense', 'fa-gift', '#F8B500', 10),
    ('CAT-INS', 'Insurance', 'expense', 'fa-shield-alt', '#85C1E2', 11),
    ('CAT-TAX', 'Taxes & Fees', 'expense', 'fa-file-invoice', '#F1948A', 12),
    ('CAT-DEBT', 'Debt Payments', 'expense', 'fa-credit-card', '#AED6F1', 13),
    ('CAT-TRVL', 'Travel', 'expense', 'fa-plane', '#82E0AA', 14),
    ('CAT-SUB', 'Subscriptions', 'expense', 'fa-sync', '#AF7AC5', 15),
    ('CAT-OTHER', 'Other Expenses', 'expense', 'fa-ellipsis-h', '#BDC3C7', 99),
]

DEFAULT_INCOME_CATEGORIES = [
    ('CAT-SAL', 'Salary', 'income', 'fa-briefcase', '#27AE60', 1),
    ('CAT-BON', 'Bonus', 'income', 'fa-star', '#2ECC71', 2),
    ('CAT-FREE', 'Freelance', 'income', 'fa-laptop', '#1ABC9C', 3),
    ('CAT-INVE', 'Investment Income', 'income', 'fa-chart-line', '#3498DB', 4),
    ('CAT-RENT', 'Rental Income', 'income', 'fa-building', '#9B59B6', 5),
    ('CAT-DIV', 'Dividends', 'income', 'fa-coins', '#F39C12', 6),
    ('CAT-SIDE', 'Side Business', 'income', 'fa-store', '#E74C3C', 7),
    ('CAT-GIFT', 'Gifts Received', 'income', 'fa-gift', '#16A085', 8),
    ('CAT-REF', 'Refunds', 'income', 'fa-undo', '#2980B9', 9),
    ('CAT-OTHER', 'Other Income', 'income', 'fa-plus-circle', '#8E44AD', 99),
]

DEFAULT_ACCOUNT_TYPES = [
    ('cash', 'Cash Wallet'),
    ('bank', 'Bank Account'),
    ('card', 'Credit/Debit Card'),
    ('digital', 'Digital Wallet'),
    ('savings', 'Savings Account'),
    ('investment', 'Investment Account'),
    ('foreign', 'Foreign Currency Account'),
    ('joint', 'Joint Account'),
]


def seed_default_categories():
    """Seed default expense and income categories."""
    with get_db_context() as db:
        for cat in DEFAULT_EXPENSE_CATEGORIES + DEFAULT_INCOME_CATEGORIES:
            db.execute("""
                INSERT OR IGNORE INTO pf_category_definitions 
                (category_code, category_name, category_type, icon, color, sort_order, is_system, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, datetime('now'))
            """, cat)
        db.commit()
    return True


def seed_default_settings():
    """Seed default finance settings."""
    defaults = [
        ('pf_default_currency', 'USD', 'string', 'general'),
        ('pf_default_date_format', '%Y-%m-%d', 'string', 'general'),
        ('pf_number_format', '1,234.56', 'string', 'general'),
        ('pf_timezone', 'UTC', 'string', 'general'),
        ('pf_budget_warning_threshold', '80', 'number', 'budget'),
        ('pf_enable_auto_categorize', '1', 'boolean', 'automation'),
        ('pf_enable_alerts', '1', 'boolean', 'notifications'),
        ('pf_alert_low_balance_threshold', '100', 'number', 'notifications'),
        ('pf_family_mode', '0', 'boolean', 'family'),
        ('pf_export_format', 'csv', 'string', 'export'),
        ('pf_backup_enabled', '1', 'boolean', 'backup'),
    ]
    
    with get_db_context() as db:
        for key, value, vtype, category in defaults:
            db.execute("""
                INSERT OR IGNORE INTO pf_settings 
                (setting_key, setting_value, setting_type, category, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            """, (key, value, vtype, category))
        db.commit()
    return True


def initialize_finance_defaults():
    """Initialize all default data for finance module."""
    seed_default_categories()
    seed_default_settings()
    return True
