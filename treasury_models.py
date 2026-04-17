"""
Treasury / Cash Flow Module - Data Models
==========================================
Enterprise-grade treasury management covering:
- Cash Position Management
- Petty Cash & Cash Box Management
- Cash Flow Forecasting
- Liquidity Planning
- Treasury Controls & Alerts
- Collections Planning (AR-Treasury Sync)
- Payments Planning (AP-Treasury Sync)
- Treasury Audit & Control Logs
- Bank Account Management Extensions

Author: Treasury Module Implementation
"""

from database import get_db_context, get_one, get_all, row_to_dict, rows_to_list, table_exists, log_audit
from datetime import datetime, timedelta
import json


# ============================================================================
# TREASURY MODULE INITIALIZATION
# ============================================================================

def initialize_treasury_schema():
    """Initialize all treasury module tables."""
    _create_treasury_settings()
    _create_treasury_cash_position_snapshots()
    _create_treasury_petty_cash_accounts()
    _create_treasury_cash_boxes()
    _create_treasury_cash_movements()
    _create_treasury_forecasts()
    _create_treasury_forecast_scenarios()
    _create_treasury_forecast_items()
    _create_treasury_liquidity_plans()
    _create_treasury_liquidity_thresholds()
    _create_treasury_collections_plan()
    _create_treasury_payments_plan()
    _create_treasury_transfer_requests()
    _create_treasury_transfer_approvals()
    _create_treasury_controls()
    _create_treasury_alerts()
    _create_treasury_audit_log()
    _create_treasury_bank_signatories()
    _create_treasury_account_groups()
    _create_treasury_workflow_rules()
    _create_treasury_reconciliation_rules()
    _create_treasury_bank_statements()
    _create_treasury_bank_statement_lines()
    _create_treasury_payment_runs()
    _create_treasury_payment_run_items()
    _create_treasury_fx_contracts()
    _create_treasury_counterparties()
    _create_treasury_bank_connections()
    _create_treasury_bank_charges()
    _create_treasury_cash_pools()
    _create_treasury_cash_pool_members()
    _create_treasury_notional_pooling()
    _create_treasury_collection_scores()
    _create_treasury_dunning_settings()
    _create_treasury_notification_preferences()


# ============================================================================
# TREASURY SETTINGS
# ============================================================================

def _create_treasury_settings():
    """Create treasury settings table."""
    if not table_exists('treasury_settings'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT,
                    setting_type TEXT DEFAULT 'text',
                    category TEXT DEFAULT 'general',
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_treasury_setting_key ON treasury_settings(setting_key)")
            db.execute("CREATE INDEX idx_treasury_setting_company ON treasury_settings(company_id)")
            db.commit()


def get_treasury_setting(setting_key, company_id=None, default=None):
    """Get a treasury setting value."""
    sql = "SELECT setting_value FROM treasury_settings WHERE setting_key = ? AND is_active = 1"
    params = [setting_key]
    
    if company_id:
        sql += " AND (company_id = ? OR company_id IS NULL)"
        params.append(company_id)
    
    result = get_one(sql, params)
    return result['setting_value'] if result else default


def set_treasury_setting(setting_key, setting_value, company_id=None, category='general'):
    """Set a treasury setting."""
    with get_db_context() as db:
        db.execute("""
            INSERT INTO treasury_settings (setting_key, setting_value, category, company_id)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                updated_at = CURRENT_TIMESTAMP
        """, (setting_key, setting_value, category, company_id))
        db.commit()


def get_treasury_settings(company_id=None, category=None):
    """Get all treasury settings."""
    sql = "SELECT * FROM treasury_settings WHERE is_active = 1"
    params = []
    
    if company_id:
        sql += " AND (company_id = ? OR company_id IS NULL)"
        params.append(company_id)
    
    if category:
        sql += " AND category = ?"
        params.append(category)
    
    sql += " ORDER BY category, setting_key"
    return get_all(sql, params)


# ============================================================================
# CASH POSITION SNAPSHOTS
# ============================================================================

def _create_treasury_cash_position_snapshots():
    """Create cash position snapshots table for historical tracking."""
    if not table_exists('treasury_cash_position_snapshots'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_cash_position_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_date DATE NOT NULL,
                    bank_account_id INTEGER,
                    currency TEXT DEFAULT 'AED',
                    opening_balance REAL DEFAULT 0,
                    closing_balance REAL DEFAULT 0,
                    total_inflow REAL DEFAULT 0,
                    total_outflow REAL DEFAULT 0,
                    blocked_amount REAL DEFAULT 0,
                    available_balance REAL DEFAULT 0,
                    entity_id INTEGER,
                    branch_id INTEGER,
                    notes TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bank_account_id) REFERENCES finance_bank_accounts(id)
                )
            """)
            db.execute("CREATE INDEX idx_snap_date ON treasury_cash_position_snapshots(snapshot_date)")
            db.execute("CREATE INDEX idx_snap_bank ON treasury_cash_position_snapshots(bank_account_id)")
            db.execute("CREATE INDEX idx_snap_company ON treasury_cash_position_snapshots(company_id)")
            db.commit()


def create_cash_position_snapshot(data):
    """Create a cash position snapshot."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO treasury_cash_position_snapshots (
                snapshot_date, bank_account_id, currency, opening_balance,
                closing_balance, total_inflow, total_outflow, blocked_amount,
                available_balance, entity_id, branch_id, notes, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('snapshot_date'),
            data.get('bank_account_id'),
            data.get('currency', 'AED'),
            data.get('opening_balance', 0),
            data.get('closing_balance', 0),
            data.get('total_inflow', 0),
            data.get('total_outflow', 0),
            data.get('blocked_amount', 0),
            data.get('available_balance', 0),
            data.get('entity_id'),
            data.get('branch_id'),
            data.get('notes'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def get_cash_position_snapshots(company_id, start_date=None, end_date=None, 
                                  bank_account_id=None, currency=None):
    """Get cash position snapshots with filters."""
    sql = "SELECT * FROM treasury_cash_position_snapshots WHERE company_id = ?"
    params = [company_id]
    
    if start_date:
        sql += " AND snapshot_date >= ?"
        params.append(start_date)
    
    if end_date:
        sql += " AND snapshot_date <= ?"
        params.append(end_date)
    
    if bank_account_id:
        sql += " AND bank_account_id = ?"
        params.append(bank_account_id)
    
    if currency:
        sql += " AND currency = ?"
        params.append(currency)
    
    sql += " ORDER BY snapshot_date DESC, id DESC"
    return get_all(sql, params)


def get_todays_cash_position(company_id):
    """Get today's cash position aggregated across all accounts."""
    today = datetime.now().date().isoformat()
    
    sql = """
        SELECT 
            COALESCE(SUM(tc.closing_balance), 0) as total_closing,
            COALESCE(SUM(tc.opening_balance), 0) as total_opening,
            COALESCE(SUM(tc.total_inflow), 0) as total_inflow,
            COALESCE(SUM(tc.total_outflow), 0) as total_outflow,
            COALESCE(SUM(tc.blocked_amount), 0) as total_blocked,
            COALESCE(SUM(tc.available_balance), 0) as total_available,
            tc.currency
        FROM treasury_cash_position_snapshots tc
        WHERE tc.company_id = ? AND tc.snapshot_date = ?
        GROUP BY tc.currency
    """
    
    return get_all(sql, (company_id, today))


def get_cash_position_by_entity(company_id, date=None):
    """Get cash position breakdown by entity."""
    if not date:
        date = datetime.now().date().isoformat()
    
    sql = """
        SELECT 
            tc.entity_id,
            e.name as entity_name,
            tc.currency,
            COALESCE(SUM(tc.closing_balance), 0) as closing_balance,
            COALESCE(SUM(tc.available_balance), 0) as available_balance,
            COALESCE(SUM(tc.total_inflow), 0) as total_inflow,
            COALESCE(SUM(tc.total_outflow), 0) as total_outflow
        FROM treasury_cash_position_snapshots tc
        LEFT JOIN entities e ON tc.entity_id = e.id
        WHERE tc.company_id = ? AND tc.snapshot_date = ?
        GROUP BY tc.entity_id, tc.currency
        ORDER BY tc.entity_id, tc.currency
    """
    return get_all(sql, (company_id, date))


def get_cash_position_by_branch(company_id, date=None):
    """Get cash position breakdown by branch."""
    if not date:
        date = datetime.now().date().isoformat()
    
    sql = """
        SELECT 
            tc.branch_id,
            b.name as branch_name,
            tc.currency,
            COALESCE(SUM(tc.closing_balance), 0) as closing_balance,
            COALESCE(SUM(tc.available_balance), 0) as available_balance,
            COALESCE(SUM(tc.total_inflow), 0) as total_inflow,
            COALESCE(SUM(tc.total_outflow), 0) as total_outflow
        FROM treasury_cash_position_snapshots tc
        LEFT JOIN branches b ON tc.branch_id = b.id
        WHERE tc.company_id = ? AND tc.snapshot_date = ?
        GROUP BY tc.branch_id, tc.currency
        ORDER BY tc.branch_id, tc.currency
    """
    return get_all(sql, (company_id, date))


# ============================================================================
# PETTY CASH ACCOUNTS
# ============================================================================

def _create_treasury_petty_cash_accounts():
    """Create petty cash accounts table."""
    if not table_exists('treasury_petty_cash_accounts'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_petty_cash_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_code TEXT UNIQUE NOT NULL,
                    account_name TEXT NOT NULL,
                    account_name_ar TEXT,
                    location TEXT,
                    custodian_id INTEGER,
                    custodian_name TEXT,
                    float_amount REAL DEFAULT 0,
                    current_balance REAL DEFAULT 0,
                    minimum_balance REAL DEFAULT 100,
                    maximum_transaction REAL DEFAULT 500,
                    currency TEXT DEFAULT 'AED',
                    is_active INTEGER DEFAULT 1,
                    entity_id INTEGER,
                    branch_id INTEGER,
                    gl_account_id INTEGER,
                    notes TEXT,
                    company_id INTEGER,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (gl_account_id) REFERENCES finance_accounts(id)
                )
            """)
            db.execute("CREATE INDEX idx_petty_company ON treasury_petty_cash_accounts(company_id)")
            db.execute("CREATE INDEX idx_petty_branch ON treasury_petty_cash_accounts(branch_id)")
            db.execute("CREATE INDEX idx_petty_active ON treasury_petty_cash_accounts(is_active)")
            db.commit()


def get_petty_cash_accounts(company_id=None, branch_id=None, is_active=True):
    """Get petty cash accounts."""
    sql = "SELECT * FROM treasury_petty_cash_accounts WHERE 1=1"
    params = []
    
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    if branch_id:
        sql += " AND branch_id = ?"
        params.append(branch_id)
    
    if is_active is not None:
        sql += " AND is_active = ?"
        params.append(1 if is_active else 0)
    
    sql += " ORDER BY account_code, account_name"
    return get_all(sql, params)


def get_petty_cash_account_by_id(account_id):
    """Get a petty cash account by ID."""
    return get_one("SELECT * FROM treasury_petty_cash_accounts WHERE id = ?", (account_id,))


def create_petty_cash_account(data):
    """Create a new petty cash account."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO treasury_petty_cash_accounts (
                account_code, account_name, account_name_ar, location,
                custodian_id, custodian_name, float_amount, current_balance,
                minimum_balance, maximum_transaction, currency, is_active,
                entity_id, branch_id, gl_account_id, notes, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('account_code'),
            data.get('account_name'),
            data.get('account_name_ar'),
            data.get('location'),
            data.get('custodian_id'),
            data.get('custodian_name'),
            data.get('float_amount', 0),
            data.get('current_balance', 0),
            data.get('minimum_balance', 100),
            data.get('maximum_transaction', 500),
            data.get('currency', 'AED'),
            data.get('is_active', 1),
            data.get('entity_id'),
            data.get('branch_id'),
            data.get('gl_account_id'),
            data.get('notes'),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def update_petty_cash_account(account_id, data):
    """Update a petty cash account."""
    with get_db_context() as db:
        db.execute("""
            UPDATE treasury_petty_cash_accounts SET
                account_name = ?,
                account_name_ar = ?,
                location = ?,
                custodian_id = ?,
                custodian_name = ?,
                float_amount = ?,
                minimum_balance = ?,
                maximum_transaction = ?,
                currency = ?,
                is_active = ?,
                entity_id = ?,
                branch_id = ?,
                gl_account_id = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get('account_name'),
            data.get('account_name_ar'),
            data.get('location'),
            data.get('custodian_id'),
            data.get('custodian_name'),
            data.get('float_amount'),
            data.get('minimum_balance'),
            data.get('maximum_transaction'),
            data.get('currency'),
            data.get('is_active'),
            data.get('entity_id'),
            data.get('branch_id'),
            data.get('gl_account_id'),
            data.get('notes'),
            account_id
        ))
        db.commit()


# ============================================================================
# CASH BOXES
# ============================================================================

def _create_treasury_cash_boxes():
    """Create cash boxes table."""
    if not table_exists('treasury_cash_boxes'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_cash_boxes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    box_code TEXT UNIQUE NOT NULL,
                    box_name TEXT NOT NULL,
                    box_type TEXT DEFAULT 'cash_box',
                    location TEXT,
                    responsible_person_id INTEGER,
                    responsible_person_name TEXT,
                    opening_balance REAL DEFAULT 0,
                    current_balance REAL DEFAULT 0,
                    currency TEXT DEFAULT 'AED',
                    is_active INTEGER DEFAULT 1,
                    entity_id INTEGER,
                    branch_id INTEGER,
                    last_count_date DATE,
                    notes TEXT,
                    company_id INTEGER,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_box_company ON treasury_cash_boxes(company_id)")
            db.execute("CREATE INDEX idx_box_branch ON treasury_cash_boxes(branch_id)")
            db.commit()


def get_cash_boxes(company_id=None, branch_id=None, is_active=True):
    """Get cash boxes."""
    sql = "SELECT * FROM treasury_cash_boxes WHERE 1=1"
    params = []
    
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    if branch_id:
        sql += " AND branch_id = ?"
        params.append(branch_id)
    
    if is_active is not None:
        sql += " AND is_active = ?"
        params.append(1 if is_active else 0)
    
    sql += " ORDER BY box_code, box_name"
    return get_all(sql, params)


def get_cash_box_by_id(box_id):
    """Get a cash box by ID."""
    return get_one("SELECT * FROM treasury_cash_boxes WHERE id = ?", (box_id,))


def create_cash_box(data):
    """Create a new cash box."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO treasury_cash_boxes (
                box_code, box_name, box_type, location,
                responsible_person_id, responsible_person_name,
                opening_balance, current_balance, currency, is_active,
                entity_id, branch_id, last_count_date, notes, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('box_code'),
            data.get('box_name'),
            data.get('box_type', 'cash_box'),
            data.get('location'),
            data.get('responsible_person_id'),
            data.get('responsible_person_name'),
            data.get('opening_balance', 0),
            data.get('current_balance', 0),
            data.get('currency', 'AED'),
            data.get('is_active', 1),
            data.get('entity_id'),
            data.get('branch_id'),
            data.get('last_count_date'),
            data.get('notes'),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# CASH MOVEMENTS
# ============================================================================

def _create_treasury_cash_movements():
    """Create cash movements table for tracking petty cash transactions."""
    if not table_exists('treasury_cash_movements'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_cash_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    movement_number TEXT UNIQUE NOT NULL,
                    movement_date DATE NOT NULL,
                    movement_type TEXT NOT NULL,
                    petty_cash_account_id INTEGER,
                    cash_box_id INTEGER,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'AED',
                    balance_before REAL DEFAULT 0,
                    balance_after REAL DEFAULT 0,
                    reference TEXT,
                    description TEXT,
                    receipt_number TEXT,
                    beneficiary_name TEXT,
                    beneficiary_id INTEGER,
                    approved_by INTEGER,
                    approved_at TIMESTAMP,
                    status TEXT DEFAULT 'Completed',
                    entity_id INTEGER,
                    branch_id INTEGER,
                    company_id INTEGER,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (petty_cash_account_id) REFERENCES treasury_petty_cash_accounts(id),
                    FOREIGN KEY (cash_box_id) REFERENCES treasury_cash_boxes(id)
                )
            """)
            db.execute("CREATE INDEX idx_movement_company ON treasury_cash_movements(company_id)")
            db.execute("CREATE INDEX idx_movement_date ON treasury_cash_movements(movement_date)")
            db.execute("CREATE INDEX idx_movement_type ON treasury_cash_movements(movement_type)")
            db.execute("CREATE INDEX idx_movement_petty ON treasury_cash_movements(petty_cash_account_id)")
            db.commit()


def get_next_movement_number(company_id=None, prefix='CM'):
    """Get next cash movement number."""
    year = datetime.now().year
    sql = "SELECT MAX(movement_number) as max_num FROM treasury_cash_movements WHERE movement_number LIKE ?"
    params = (f"{prefix}-{year}-%",)
    
    result = get_one(sql, params)
    if result and result.get('max_num'):
        last_num = int(result['max_num'].split('-')[-1])
        return f"{prefix}-{year}-{last_num + 1:05d}"
    return f"{prefix}-{year}-00001"


def get_cash_movements(company_id=None, petty_cash_id=None, cash_box_id=None,
                       movement_type=None, start_date=None, end_date=None, status=None):
    """Get cash movements with filters."""
    sql = "SELECT * FROM treasury_cash_movements WHERE 1=1"
    params = []
    
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    if petty_cash_id:
        sql += " AND petty_cash_account_id = ?"
        params.append(petty_cash_id)
    
    if cash_box_id:
        sql += " AND cash_box_id = ?"
        params.append(cash_box_id)
    
    if movement_type:
        sql += " AND movement_type = ?"
        params.append(movement_type)
    
    if start_date:
        sql += " AND movement_date >= ?"
        params.append(start_date)
    
    if end_date:
        sql += " AND movement_date <= ?"
        params.append(end_date)
    
    if status:
        sql += " AND status = ?"
        params.append(status)
    
    sql += " ORDER BY movement_date DESC, id DESC"
    return get_all(sql, params)


def create_cash_movement(data):
    """Create a new cash movement and update account balance."""
    with get_db_context() as db:
        movement_number = get_next_movement_number(data.get('company_id'))
        
        # Get current balance
        current_balance = 0
        if data.get('petty_cash_account_id'):
            account = get_petty_cash_account_by_id(data['petty_cash_account_id'])
            if account:
                current_balance = account.get('current_balance', 0)
        elif data.get('cash_box_id'):
            box = get_cash_box_by_id(data['cash_box_id'])
            if box:
                current_balance = box.get('current_balance', 0)
        
        # Calculate new balance
        movement_type = data.get('movement_type', 'withdrawal')
        amount = data.get('amount', 0)
        if movement_type in ['top_up', 'deposit', 'transfer_in']:
            new_balance = current_balance + amount
        else:
            new_balance = current_balance - amount
        
        # Insert movement
        cursor = db.execute("""
            INSERT INTO treasury_cash_movements (
                movement_number, movement_date, movement_type,
                petty_cash_account_id, cash_box_id, amount, currency,
                balance_before, balance_after, reference, description,
                receipt_number, beneficiary_name, beneficiary_id,
                approved_by, approved_at, status, entity_id, branch_id,
                company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            movement_number,
            data.get('movement_date'),
            data.get('movement_type'),
            data.get('petty_cash_account_id'),
            data.get('cash_box_id'),
            amount,
            data.get('currency', 'AED'),
            current_balance,
            new_balance,
            data.get('reference'),
            data.get('description'),
            data.get('receipt_number'),
            data.get('beneficiary_name'),
            data.get('beneficiary_id'),
            data.get('approved_by'),
            datetime.now().isoformat() if data.get('approved_by') else None,
            data.get('status', 'Completed'),
            data.get('entity_id'),
            data.get('branch_id'),
            data.get('company_id'),
            data.get('created_by')
        ))
        movement_id = cursor.lastrowid
        
        # Update account balance
        if data.get('petty_cash_account_id'):
            db.execute("""
                UPDATE treasury_petty_cash_accounts SET 
                    current_balance = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_balance, data['petty_cash_account_id']))
        elif data.get('cash_box_id'):
            db.execute("""
                UPDATE treasury_cash_boxes SET 
                    current_balance = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_balance, data['cash_box_id']))
        
        db.commit()
        return movement_id


# ============================================================================
# CASH FLOW FORECASTS
# ============================================================================

def _create_treasury_forecasts():
    """Create cash flow forecasts table."""
    if not table_exists('treasury_forecasts'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_forecasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    forecast_name TEXT NOT NULL,
                    forecast_type TEXT DEFAULT 'rolling',
                    scenario TEXT DEFAULT 'base',
                    version INTEGER DEFAULT 1,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    currency TEXT DEFAULT 'AED',
                    status TEXT DEFAULT 'Draft',
                    notes TEXT,
                    entity_id INTEGER,
                    branch_id INTEGER,
                    company_id INTEGER,
                    created_by INTEGER,
                    approved_by INTEGER,
                    approved_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_forecast_company ON treasury_forecasts(company_id)")
            db.execute("CREATE INDEX idx_forecast_status ON treasury_forecasts(status)")
            db.execute("CREATE INDEX idx_forecast_dates ON treasury_forecasts(start_date, end_date)")
            db.commit()


def get_treasury_forecasts(company_id=None, status=None, scenario=None, forecast_type=None):
    """Get cash flow forecasts."""
    sql = "SELECT * FROM treasury_forecasts WHERE 1=1"
    params = []
    
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    if status:
        sql += " AND status = ?"
        params.append(status)
    
    if scenario:
        sql += " AND scenario = ?"
        params.append(scenario)
    
    if forecast_type:
        sql += " AND forecast_type = ?"
        params.append(forecast_type)
    
    sql += " ORDER BY created_at DESC"
    return get_all(sql, params)


def get_treasury_forecast_by_id(forecast_id):
    """Get a forecast by ID."""
    return get_one("SELECT * FROM treasury_forecasts WHERE id = ?", (forecast_id,))


def create_treasury_forecast(data):
    """Create a new cash flow forecast."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO treasury_forecasts (
                forecast_name, forecast_type, scenario, version,
                start_date, end_date, currency, status, notes,
                entity_id, branch_id, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('forecast_name'),
            data.get('forecast_type', 'rolling'),
            data.get('scenario', 'base'),
            data.get('version', 1),
            data.get('start_date'),
            data.get('end_date'),
            data.get('currency', 'AED'),
            data.get('status', 'Draft'),
            data.get('notes'),
            data.get('entity_id'),
            data.get('branch_id'),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def approve_treasury_forecast(forecast_id, approved_by):
    """Approve a treasury forecast."""
    with get_db_context() as db:
        db.execute("""
            UPDATE treasury_forecasts SET 
                status = 'Approved',
                approved_by = ?,
                approved_at = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (approved_by, datetime.now().isoformat(), forecast_id))
        db.commit()


# ============================================================================
# FORECAST SCENARIOS
# ============================================================================

def _create_treasury_forecast_scenarios():
    """Create forecast scenarios table."""
    if not table_exists('treasury_forecast_scenarios'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_forecast_scenarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    forecast_id INTEGER NOT NULL,
                    scenario_name TEXT NOT NULL,
                    scenario_type TEXT DEFAULT 'optimistic',
                    probability_weight REAL DEFAULT 1.0,
                    growth_rate_inflow REAL DEFAULT 0,
                    growth_rate_outflow REAL DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (forecast_id) REFERENCES treasury_forecasts(id)
                )
            """)
            db.execute("CREATE INDEX idx_scenario_forecast ON treasury_forecast_scenarios(forecast_id)")
            db.commit()


def get_forecast_scenarios(forecast_id):
    """Get scenarios for a forecast."""
    return get_all("SELECT * FROM treasury_forecast_scenarios WHERE forecast_id = ?",
                   (forecast_id,))


# ============================================================================
# FORECAST ITEMS
# ============================================================================

def _create_treasury_forecast_items():
    """Create forecast items table for detailed line items."""
    if not table_exists('treasury_forecast_items'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_forecast_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    forecast_id INTEGER NOT NULL,
                    item_date DATE NOT NULL,
                    item_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT,
                    description TEXT,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'AED',
                    probability REAL DEFAULT 1.0,
                    source TEXT,
                    source_id INTEGER,
                    is_locked INTEGER DEFAULT 0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (forecast_id) REFERENCES treasury_forecasts(id)
                )
            """)
            db.execute("CREATE INDEX idx_item_forecast ON treasury_forecast_items(forecast_id)")
            db.execute("CREATE INDEX idx_item_date ON treasury_forecast_items(item_date)")
            db.execute("CREATE INDEX idx_item_type ON treasury_forecast_items(item_type)")
            db.commit()


def get_forecast_items(forecast_id, item_type=None, start_date=None, end_date=None):
    """Get forecast items."""
    sql = "SELECT * FROM treasury_forecast_items WHERE forecast_id = ?"
    params = [forecast_id]
    
    if item_type:
        sql += " AND item_type = ?"
        params.append(item_type)
    
    if start_date:
        sql += " AND item_date >= ?"
        params.append(start_date)
    
    if end_date:
        sql += " AND item_date <= ?"
        params.append(end_date)
    
    sql += " ORDER BY item_date, item_type, category"
    return get_all(sql, params)


def create_forecast_item(data):
    """Create a forecast item."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO treasury_forecast_items (
                forecast_id, item_date, item_type, category, subcategory,
                description, amount, currency, probability, source, source_id,
                is_locked, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('forecast_id'),
            data.get('item_date'),
            data.get('item_type'),
            data.get('category'),
            data.get('subcategory'),
            data.get('description'),
            data.get('amount'),
            data.get('currency', 'AED'),
            data.get('probability', 1.0),
            data.get('source'),
            data.get('source_id'),
            data.get('is_locked', 0),
            data.get('notes')
        ))
        db.commit()
        return cursor.lastrowid


def update_forecast_item(item_id, data):
    """Update a forecast item."""
    with get_db_context() as db:
        db.execute("""
            UPDATE treasury_forecast_items SET
                item_date = ?,
                item_type = ?,
                category = ?,
                subcategory = ?,
                description = ?,
                amount = ?,
                probability = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get('item_date'),
            data.get('item_type'),
            data.get('category'),
            data.get('subcategory'),
            data.get('description'),
            data.get('amount'),
            data.get('probability'),
            data.get('notes'),
            item_id
        ))
        db.commit()


def delete_forecast_item(item_id):
    """Delete a forecast item."""
    with get_db_context() as db:
        db.execute("DELETE FROM treasury_forecast_items WHERE id = ?", (item_id,))
        db.commit()


def get_forecast_summary(forecast_id):
    """Get aggregated forecast summary by period."""
    sql = """
        SELECT 
            item_type,
            category,
            SUM(amount * probability) as weighted_amount,
            COUNT(*) as item_count
        FROM treasury_forecast_items
        WHERE forecast_id = ?
        GROUP BY item_type, category
        ORDER BY item_type, category
    """
    return get_all(sql, (forecast_id,))


# ============================================================================
# LIQUIDITY PLANS
# ============================================================================

def _create_treasury_liquidity_plans():
    """Create liquidity plans table."""
    if not table_exists('treasury_liquidity_plans'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_liquidity_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_name TEXT NOT NULL,
                    plan_type TEXT DEFAULT 'weekly',
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    currency TEXT DEFAULT 'AED',
                    minimum_buffer REAL DEFAULT 0,
                    target_surplus REAL DEFAULT 0,
                    status TEXT DEFAULT 'Draft',
                    notes TEXT,
                    entity_id INTEGER,
                    company_id INTEGER,
                    created_by INTEGER,
                    approved_by INTEGER,
                    approved_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_liq_plan_company ON treasury_liquidity_plans(company_id)")
            db.execute("CREATE INDEX idx_liq_plan_dates ON treasury_liquidity_plans(start_date, end_date)")
            db.commit()


def _create_treasury_liquidity_thresholds():
    """Create liquidity thresholds table."""
    if not table_exists('treasury_liquidity_thresholds'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_liquidity_thresholds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    threshold_name TEXT NOT NULL,
                    threshold_type TEXT NOT NULL,
                    threshold_value REAL NOT NULL,
                    comparison_operator TEXT DEFAULT 'less_than',
                    currency TEXT DEFAULT 'AED',
                    urgency_level TEXT DEFAULT 'normal',
                    notification_enabled INTEGER DEFAULT 1,
                    auto_action TEXT,
                    entity_id INTEGER,
                    branch_id INTEGER,
                    company_id INTEGER,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_threshold_company ON treasury_liquidity_thresholds(company_id)")
            db.commit()


def get_liquidity_thresholds(company_id=None, is_active=True):
    """Get liquidity thresholds."""
    sql = "SELECT * FROM treasury_liquidity_thresholds WHERE 1=1"
    params = []
    
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    if is_active is not None:
        sql += " AND is_active = ?"
        params.append(1 if is_active else 0)
    
    sql += " ORDER BY urgency_level DESC, threshold_value"
    return get_all(sql, params)


def create_liquidity_threshold(data):
    """Create a liquidity threshold."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO treasury_liquidity_thresholds (
                threshold_name, threshold_type, threshold_value,
                comparison_operator, currency, urgency_level,
                notification_enabled, auto_action, entity_id,
                branch_id, company_id, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('threshold_name'),
            data.get('threshold_type'),
            data.get('threshold_value'),
            data.get('comparison_operator', 'less_than'),
            data.get('currency', 'AED'),
            data.get('urgency_level', 'normal'),
            data.get('notification_enabled', 1),
            data.get('auto_action'),
            data.get('entity_id'),
            data.get('branch_id'),
            data.get('company_id'),
            data.get('is_active', 1)
        ))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# COLLECTIONS PLANNING (AR-Treasury Sync)
# ============================================================================

def _create_treasury_collections_plan():
    """Create collections planning table."""
    if not table_exists('treasury_collections_plan'):
        if not table_exists('treasury_collections'):
            with get_db_context() as db:
                db.execute("""
                    CREATE TABLE treasury_collections (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        collection_number TEXT UNIQUE NOT NULL,
                        invoice_id INTEGER,
                        customer_id INTEGER,
                        customer_name TEXT,
                        invoice_number TEXT,
                        invoice_date DATE,
                        due_date DATE,
                        original_amount REAL NOT NULL,
                        open_amount REAL NOT NULL,
                        expected_amount REAL,
                        expected_date DATE,
                        likelihood TEXT DEFAULT 'expected',
                        risk_level TEXT DEFAULT 'normal',
                        collector_id INTEGER,
                        collector_name TEXT,
                        branch_id INTEGER,
                        company_id INTEGER,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                db.execute("CREATE INDEX idx_collections_company ON treasury_collections(company_id)")
                db.execute("CREATE INDEX idx_collections_due ON treasury_collections(due_date)")
                db.execute("CREATE INDEX idx_collections_customer ON treasury_collections(customer_id)")
                db.commit()


def get_treasury_collections(company_id=None, start_date=None, end_date=None,
                              risk_level=None, likelihood=None):
    """Get collections plan items."""
    sql = "SELECT * FROM treasury_collections WHERE company_id = ?"
    params = [company_id]
    
    if start_date:
        sql += " AND due_date >= ?"
        params.append(start_date)
    
    if end_date:
        sql += " AND due_date <= ?"
        params.append(end_date)
    
    if risk_level:
        sql += " AND risk_level = ?"
        params.append(risk_level)
    
    if likelihood:
        sql += " AND likelihood = ?"
        params.append(likelihood)
    
    sql += " ORDER BY due_date, risk_level DESC"
    return get_all(sql, params)


def sync_collections_from_ar(company_id):
    """Sync collections from AR invoices."""
    from finance_models import get_customer_invoices
    
    # Get posted but unpaid invoices
    invoices = get_customer_invoices(company_id=company_id, status='Posted')
    
    for invoice in invoices:
        if float(invoice.get('total_amount', 0) or 0) > float(invoice.get('amount_paid', 0) or 0):
            open_amount = float(invoice['total_amount']) - float(invoice.get('amount_paid', 0))
            
            # Check if already exists
            existing = get_one(
                "SELECT id FROM treasury_collections WHERE invoice_id = ?",
                (invoice['id'],)
            )
            
            if not existing:
                with get_db_context() as db:
                    db.execute("""
                        INSERT INTO treasury_collections (
                            collection_number, invoice_id, customer_id, customer_name,
                            invoice_number, invoice_date, due_date, original_amount,
                            open_amount, expected_amount, expected_date,
                            likelihood, risk_level, company_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        f"COL-{datetime.now().year}-{invoice['id']:05d}",
                        invoice['id'],
                        invoice.get('customer_id'),
                        invoice.get('customer_name'),
                        invoice.get('invoice_number'),
                        invoice.get('invoice_date'),
                        invoice.get('due_date'),
                        invoice.get('total_amount'),
                        open_amount,
                        open_amount,
                        invoice.get('due_date'),
                        'expected',
                        'normal',
                        company_id
                    ))
                    db.commit()


def get_collections_summary(company_id, start_date=None, end_date=None):
    """Get collections summary statistics."""
    sql = """
        SELECT 
            COUNT(*) as total_collections,
            SUM(open_amount) as total_open_amount,
            SUM(CASE WHEN risk_level = 'high' THEN open_amount ELSE 0 END) as high_risk_amount,
            SUM(CASE WHEN risk_level = 'medium' THEN open_amount ELSE 0 END) as medium_risk_amount,
            SUM(CASE WHEN risk_level = 'normal' THEN open_amount ELSE 0 END) as normal_risk_amount,
            SUM(CASE WHEN likelihood = 'certain' THEN open_amount ELSE 0 END) as certain_amount,
            SUM(CASE WHEN likelihood = 'probable' THEN open_amount ELSE 0 END) as probable_amount,
            SUM(CASE WHEN likelihood = 'possible' THEN open_amount ELSE 0 END) as possible_amount,
            SUM(CASE WHEN likelihood = 'uncertain' THEN open_amount ELSE 0 END) as uncertain_amount
        FROM treasury_collections
        WHERE company_id = ?
    """
    params = [company_id]
    
    if start_date:
        sql += " AND due_date >= ?"
        params.append(start_date)
    
    if end_date:
        sql += " AND due_date <= ?"
        params.append(end_date)
    
    result = get_one(sql, params)
    return result if result else {}


# ============================================================================
# PAYMENTS PLANNING (AP-Treasury Sync)
# ============================================================================

def _create_treasury_payments_plan():
    """Create payments planning table."""
    if not table_exists('treasury_payments_plan'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_payments_plan (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_number TEXT UNIQUE NOT NULL,
                    bill_id INTEGER,
                    supplier_id INTEGER,
                    supplier_name TEXT,
                    bill_number TEXT,
                    bill_date DATE,
                    due_date DATE,
                    original_amount REAL NOT NULL,
                    open_amount REAL NOT NULL,
                    planned_amount REAL,
                    planned_date DATE,
                    priority TEXT DEFAULT 'normal',
                    payment_method TEXT,
                    bank_account_id INTEGER,
                    status TEXT DEFAULT 'Planned',
                    branch_id INTEGER,
                    company_id INTEGER,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_payments_company ON treasury_payments_plan(company_id)")
            db.execute("CREATE INDEX idx_payments_due ON treasury_payments_plan(due_date)")
            db.execute("CREATE INDEX idx_payments_supplier ON treasury_payments_plan(supplier_id)")
            db.commit()


def get_treasury_payments(company_id=None, start_date=None, end_date=None,
                           priority=None, status=None):
    """Get payments plan items."""
    sql = "SELECT * FROM treasury_payments_plan WHERE company_id = ?"
    params = [company_id]
    
    if start_date:
        sql += " AND due_date >= ?"
        params.append(start_date)
    
    if end_date:
        sql += " AND due_date <= ?"
        params.append(end_date)
    
    if priority:
        sql += " AND priority = ?"
        params.append(priority)
    
    if status:
        sql += " AND status = ?"
        params.append(status)
    
    sql += " ORDER BY due_date, priority DESC"
    return get_all(sql, params)


def sync_payments_from_ap(company_id):
    """Sync payments from AP bills."""
    from finance_models import get_supplier_bills
    
    # Get posted but unpaid bills
    bills = get_supplier_bills(company_id=company_id, status='Posted')
    
    for bill in bills:
        if float(bill.get('total_amount', 0) or 0) > float(bill.get('amount_paid', 0) or 0):
            open_amount = float(bill['total_amount']) - float(bill.get('amount_paid', 0))
            
            # Check if already exists
            existing = get_one(
                "SELECT id FROM treasury_payments_plan WHERE bill_id = ?",
                (bill['id'],)
            )
            
            if not existing:
                with get_db_context() as db:
                    db.execute("""
                        INSERT INTO treasury_payments_plan (
                            payment_number, bill_id, supplier_id, supplier_name,
                            bill_number, bill_date, due_date, original_amount,
                            open_amount, planned_amount, planned_date,
                            priority, payment_method, status, company_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        f"PAY-{datetime.now().year}-{bill['id']:05d}",
                        bill['id'],
                        bill.get('supplier_id'),
                        bill.get('supplier_name'),
                        bill.get('bill_number'),
                        bill.get('bill_date'),
                        bill.get('due_date'),
                        bill.get('total_amount'),
                        open_amount,
                        open_amount,
                        bill.get('due_date'),
                        'normal',
                        bill.get('payment_method'),
                        'Planned',
                        company_id
                    ))
                    db.commit()


def get_payments_summary(company_id, start_date=None, end_date=None):
    """Get payments summary statistics."""
    sql = """
        SELECT 
            COUNT(*) as total_payments,
            SUM(open_amount) as total_open_amount,
            SUM(CASE WHEN priority = 'critical' THEN open_amount ELSE 0 END) as critical_amount,
            SUM(CASE WHEN priority = 'high' THEN open_amount ELSE 0 END) as high_priority_amount,
            SUM(CASE WHEN priority = 'normal' THEN open_amount ELSE 0 END) as normal_priority_amount,
            SUM(CASE WHEN status = 'Planned' THEN open_amount ELSE 0 END) as planned_amount,
            SUM(CASE WHEN status = 'Approved' THEN open_amount ELSE 0 END) as approved_amount,
            SUM(CASE WHEN status = 'Paid' THEN open_amount ELSE 0 END) as paid_amount
        FROM treasury_payments_plan
        WHERE company_id = ?
    """
    params = [company_id]
    
    if start_date:
        sql += " AND due_date >= ?"
        params.append(start_date)
    
    if end_date:
        sql += " AND due_date <= ?"
        params.append(end_date)
    
    result = get_one(sql, params)
    return result if result else {}


# ============================================================================
# TRANSFER REQUESTS
# ============================================================================

def _create_treasury_transfer_requests():
    """Create transfer requests table for approval workflow."""
    if not table_exists('treasury_transfer_requests'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_transfer_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_number TEXT UNIQUE NOT NULL,
                    request_type TEXT DEFAULT 'bank_transfer',
                    transfer_date DATE NOT NULL,
                    from_account_type TEXT,
                    from_bank_account_id INTEGER,
                    from_petty_cash_id INTEGER,
                    to_account_type TEXT,
                    to_bank_account_id INTEGER,
                    to_petty_cash_id INTEGER,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'AED',
                    exchange_rate REAL DEFAULT 1.0,
                    reference TEXT,
                    reason TEXT,
                    urgency TEXT DEFAULT 'normal',
                    status TEXT DEFAULT 'Pending',
                    requires_approval INTEGER DEFAULT 1,
                    approved_by INTEGER,
                    approved_at TIMESTAMP,
                    rejected_by INTEGER,
                    rejected_at TIMESTAMP,
                    rejection_reason TEXT,
                    entity_id INTEGER,
                    branch_id INTEGER,
                    company_id INTEGER,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_transfer_req_company ON treasury_transfer_requests(company_id)")
            db.execute("CREATE INDEX idx_transfer_req_status ON treasury_transfer_requests(status)")
            db.execute("CREATE INDEX idx_transfer_req_date ON treasury_transfer_requests(transfer_date)")
            db.commit()


def get_next_transfer_request_number(company_id=None):
    """Get next transfer request number."""
    year = datetime.now().year
    sql = "SELECT MAX(request_number) as max_num FROM treasury_transfer_requests WHERE request_number LIKE ?"
    params = (f"TRF-{year}-%",)
    
    result = get_one(sql, params)
    if result and result.get('max_num'):
        last_num = int(result['max_num'].split('-')[-1])
        return f"TRF-{year}-{last_num + 1:05d}"
    return f"TRF-{year}-00001"


def get_transfer_requests(company_id=None, status=None, request_type=None,
                           start_date=None, end_date=None):
    """Get transfer requests."""
    sql = "SELECT * FROM treasury_transfer_requests WHERE 1=1"
    params = []
    
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    if status:
        sql += " AND status = ?"
        params.append(status)
    
    if request_type:
        sql += " AND request_type = ?"
        params.append(request_type)
    
    if start_date:
        sql += " AND transfer_date >= ?"
        params.append(start_date)
    
    if end_date:
        sql += " AND transfer_date <= ?"
        params.append(end_date)
    
    sql += " ORDER BY created_at DESC"
    return get_all(sql, params)


def get_transfer_request_by_id(request_id):
    """Get a transfer request by ID."""
    return get_one("SELECT * FROM treasury_transfer_requests WHERE id = ?", (request_id,))


def create_transfer_request(data):
    """Create a transfer request."""
    with get_db_context() as db:
        request_number = get_next_transfer_request_number(data.get('company_id'))
        
        # Check if approval is required based on amount
        amount = data.get('amount', 0)
        requires_approval = 1
        
        cursor = db.execute("""
            INSERT INTO treasury_transfer_requests (
                request_number, request_type, transfer_date,
                from_account_type, from_bank_account_id, from_petty_cash_id,
                to_account_type, to_bank_account_id, to_petty_cash_id,
                amount, currency, exchange_rate, reference, reason, urgency,
                status, requires_approval, entity_id, branch_id, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request_number,
            data.get('request_type', 'bank_transfer'),
            data.get('transfer_date'),
            data.get('from_account_type'),
            data.get('from_bank_account_id'),
            data.get('from_petty_cash_id'),
            data.get('to_account_type'),
            data.get('to_bank_account_id'),
            data.get('to_petty_cash_id'),
            amount,
            data.get('currency', 'AED'),
            data.get('exchange_rate', 1.0),
            data.get('reference'),
            data.get('reason'),
            data.get('urgency', 'normal'),
            'Pending',
            requires_approval,
            data.get('entity_id'),
            data.get('branch_id'),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def approve_transfer_request(request_id, approved_by, notes=None):
    """Approve a transfer request."""
    with get_db_context() as db:
        db.execute("""
            UPDATE treasury_transfer_requests SET
                status = 'Approved',
                approved_by = ?,
                approved_at = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (approved_by, datetime.now().isoformat(), request_id))
        db.commit()
        
        # Get request details
        request = get_transfer_request_by_id(request_id)
        return request


def reject_transfer_request(request_id, rejected_by, reason):
    """Reject a transfer request."""
    with get_db_context() as db:
        db.execute("""
            UPDATE treasury_transfer_requests SET
                status = 'Rejected',
                rejected_by = ?,
                rejected_at = ?,
                rejection_reason = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (rejected_by, datetime.now().isoformat(), reason, request_id))
        db.commit()


# ============================================================================
# TRANSFER APPROVALS
# ============================================================================

def _create_treasury_transfer_approvals():
    """Create transfer approvals table for multi-level approval workflow."""
    if not table_exists('treasury_transfer_approvals'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_transfer_approvals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transfer_request_id INTEGER NOT NULL,
                    approval_level INTEGER DEFAULT 1,
                    approver_id INTEGER NOT NULL,
                    approver_name TEXT,
                    approval_status TEXT DEFAULT 'Pending',
                    approval_date TIMESTAMP,
                    comments TEXT,
                    delegation_from_id INTEGER,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (transfer_request_id) REFERENCES treasury_transfer_requests(id)
                )
            """)
            db.execute("CREATE INDEX idx_approval_request ON treasury_transfer_approvals(transfer_request_id)")
            db.commit()


# ============================================================================
# TREASURY CONTROLS
# ============================================================================

def _create_treasury_controls():
    """Create treasury controls table."""
    if not table_exists('treasury_controls'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_controls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    control_name TEXT NOT NULL,
                    control_type TEXT NOT NULL,
                    control_category TEXT,
                    description TEXT,
                    control_rule TEXT,
                    threshold_value REAL,
                    threshold_operator TEXT,
                    affected_operations TEXT,
                    is_active INTEGER DEFAULT 1,
                    severity TEXT DEFAULT 'medium',
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_controls_company ON treasury_controls(company_id)")
            db.execute("CREATE INDEX idx_controls_type ON treasury_controls(control_type)")
            db.commit()


def get_treasury_controls(company_id=None, is_active=True, control_type=None):
    """Get treasury controls."""
    sql = "SELECT * FROM treasury_controls WHERE 1=1"
    params = []
    
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    if is_active is not None:
        sql += " AND is_active = ?"
        params.append(1 if is_active else 0)
    
    if control_type:
        sql += " AND control_type = ?"
        params.append(control_type)
    
    sql += " ORDER BY severity DESC, control_name"
    return get_all(sql, params)


def create_treasury_control(data):
    """Create a treasury control."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO treasury_controls (
                control_name, control_type, control_category, description,
                control_rule, threshold_value, threshold_operator,
                affected_operations, is_active, severity, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('control_name'),
            data.get('control_type'),
            data.get('control_category'),
            data.get('description'),
            data.get('control_rule'),
            data.get('threshold_value'),
            data.get('threshold_operator'),
            data.get('affected_operations'),
            data.get('is_active', 1),
            data.get('severity', 'medium'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def check_treasury_control(control_name, amount, company_id=None):
    """Check if an operation passes a treasury control."""
    control = get_one(
        "SELECT * FROM treasury_controls WHERE control_name = ? AND is_active = 1",
        (control_name,)
    )
    
    if not control:
        return {'passed': True, 'control': None}
    
    threshold = control.get('threshold_value')
    operator = control.get('threshold_operator', 'less_than')
    
    passed = True
    if threshold:
        if operator == 'less_than':
            passed = amount < threshold
        elif operator == 'less_equal':
            passed = amount <= threshold
        elif operator == 'greater_than':
            passed = amount > threshold
        elif operator == 'greater_equal':
            passed = amount >= threshold
        elif operator == 'equal':
            passed = amount == threshold
    
    return {
        'passed': passed,
        'control': control,
        'threshold': threshold,
        'amount': amount
    }


# ============================================================================
# TREASURY ALERTS
# ============================================================================

def _create_treasury_alerts():
    """Create treasury alerts table."""
    if not table_exists('treasury_alerts'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_number TEXT UNIQUE NOT NULL,
                    alert_type TEXT NOT NULL,
                    alert_category TEXT,
                    severity TEXT DEFAULT 'medium',
                    title TEXT NOT NULL,
                    message TEXT,
                    source TEXT,
                    source_id INTEGER,
                    amount REAL,
                    currency TEXT,
                    bank_account_id INTEGER,
                    entity_id INTEGER,
                    branch_id INTEGER,
                    is_read INTEGER DEFAULT 0,
                    is_resolved INTEGER DEFAULT 0,
                    resolved_by INTEGER,
                    resolved_at TIMESTAMP,
                    resolution_notes TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_alerts_company ON treasury_alerts(company_id)")
            db.execute("CREATE INDEX idx_alerts_type ON treasury_alerts(alert_type)")
            db.execute("CREATE INDEX idx_alerts_severity ON treasury_alerts(severity)")
            db.execute("CREATE INDEX idx_alerts_read ON treasury_alerts(is_read)")
            db.commit()


def get_next_alert_number(company_id=None):
    """Get next alert number."""
    year = datetime.now().year
    sql = "SELECT MAX(alert_number) as max_num FROM treasury_alerts WHERE alert_number LIKE ?"
    params = (f"ALT-{year}-%",)
    
    result = get_one(sql, params)
    if result and result.get('max_num'):
        last_num = int(result['max_num'].split('-')[-1])
        return f"ALT-{year}-{last_num + 1:05d}"
    return f"ALT-{year}-00001"


def get_treasury_alerts(company_id=None, is_read=None, is_resolved=None,
                         alert_type=None, severity=None, start_date=None, end_date=None):
    """Get treasury alerts."""
    sql = "SELECT * FROM treasury_alerts WHERE 1=1"
    params = []
    
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    if is_read is not None:
        sql += " AND is_read = ?"
        params.append(1 if is_read else 0)
    
    if is_resolved is not None:
        sql += " AND is_resolved = ?"
        params.append(1 if is_resolved else 0)
    
    if alert_type:
        sql += " AND alert_type = ?"
        params.append(alert_type)
    
    if severity:
        sql += " AND severity = ?"
        params.append(severity)
    
    if start_date:
        sql += " AND created_at >= ?"
        params.append(start_date)
    
    if end_date:
        sql += " AND created_at <= ?"
        params.append(end_date)
    
    sql += " ORDER BY severity DESC, created_at DESC"
    return get_all(sql, params)


def create_treasury_alert(data):
    """Create a treasury alert."""
    with get_db_context() as db:
        alert_number = get_next_alert_number(data.get('company_id'))
        
        cursor = db.execute("""
            INSERT INTO treasury_alerts (
                alert_number, alert_type, alert_category, severity, title,
                message, source, source_id, amount, currency,
                bank_account_id, entity_id, branch_id, is_read, is_resolved,
                company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert_number,
            data.get('alert_type'),
            data.get('alert_category'),
            data.get('severity', 'medium'),
            data.get('title'),
            data.get('message'),
            data.get('source'),
            data.get('source_id'),
            data.get('amount'),
            data.get('currency'),
            data.get('bank_account_id'),
            data.get('entity_id'),
            data.get('branch_id'),
            0,
            0,
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def resolve_treasury_alert(alert_id, resolved_by, notes=None):
    """Resolve a treasury alert."""
    with get_db_context() as db:
        db.execute("""
            UPDATE treasury_alerts SET
                is_resolved = 1,
                resolved_by = ?,
                resolved_at = ?,
                resolution_notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (resolved_by, datetime.now().isoformat(), notes, alert_id))
        db.commit()


def get_unread_alert_count(company_id=None):
    """Get count of unread alerts."""
    sql = "SELECT COUNT(*) as count FROM treasury_alerts WHERE is_read = 0 AND is_resolved = 0"
    params = []
    
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    result = get_one(sql, params)
    return result['count'] if result else 0


def get_critical_alerts(company_id=None):
    """Get critical alerts that need immediate attention."""
    sql = """
        SELECT * FROM treasury_alerts 
        WHERE severity = 'critical' 
        AND is_resolved = 0 
        AND company_id = ?
        ORDER BY created_at DESC
    """
    return get_all(sql, (company_id,))


# ============================================================================
# TREASURY AUDIT LOG
# ============================================================================

def _create_treasury_audit_log():
    """Create treasury audit log table."""
    if not table_exists('treasury_audit_log'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_number TEXT UNIQUE NOT NULL,
                    action TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id INTEGER,
                    entity_name TEXT,
                    field_name TEXT,
                    old_value TEXT,
                    new_value TEXT,
                    change_reason TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    user_id INTEGER NOT NULL,
                    user_name TEXT,
                    user_role TEXT,
                    company_id INTEGER,
                    branch_id INTEGER,
                    entity_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_audit_company ON treasury_audit_log(company_id)")
            db.execute("CREATE INDEX idx_audit_entity ON treasury_audit_log(entity_type, entity_id)")
            db.execute("CREATE INDEX idx_audit_user ON treasury_audit_log(user_id)")
            db.execute("CREATE INDEX idx_audit_date ON treasury_audit_log(created_at)")
            db.commit()


def get_next_audit_number():
    """Get next audit number."""
    year = datetime.now().year
    result = get_one(
        "SELECT MAX(audit_number) as max_num FROM treasury_audit_log WHERE audit_number LIKE ?",
        (f"AUD-{year}-%",)
    )
    if result and result.get('max_num'):
        last_num = int(result['max_num'].split('-')[-1])
        return f"AUD-{year}-{last_num + 1:05d}"
    return f"AUD-{year}-00001"


def log_treasury_audit(action, entity_type, entity_id, entity_name=None,
                        field_name=None, old_value=None, new_value=None,
                        change_reason=None, user_id=None, user_name=None,
                        user_role=None, company_id=None, branch_id=None):
    """Log a treasury audit event."""
    with get_db_context() as db:
        audit_number = get_next_audit_number()
        
        db.execute("""
            INSERT INTO treasury_audit_log (
                audit_number, action, entity_type, entity_id, entity_name,
                field_name, old_value, new_value, change_reason,
                user_id, user_name, user_role, company_id, branch_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            audit_number,
            action,
            entity_type,
            entity_id,
            entity_name,
            field_name,
            str(old_value) if old_value else None,
            str(new_value) if new_value else None,
            change_reason,
            user_id,
            user_name,
            user_role,
            company_id,
            branch_id
        ))
        db.commit()


def get_treasury_audit_log(company_id=None, entity_type=None, entity_id=None,
                            user_id=None, action=None, start_date=None, end_date=None):
    """Get treasury audit log entries."""
    sql = "SELECT * FROM treasury_audit_log WHERE 1=1"
    params = []
    
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    if entity_type:
        sql += " AND entity_type = ?"
        params.append(entity_type)
    
    if entity_id:
        sql += " AND entity_id = ?"
        params.append(entity_id)
    
    if user_id:
        sql += " AND user_id = ?"
        params.append(user_id)
    
    if action:
        sql += " AND action = ?"
        params.append(action)
    
    if start_date:
        sql += " AND created_at >= ?"
        params.append(start_date)
    
    if end_date:
        sql += " AND created_at <= ?"
        params.append(end_date)
    
    sql += " ORDER BY created_at DESC"
    return get_all(sql, params)


# ============================================================================
# BANK SIGNATORIES
# ============================================================================

def _create_treasury_bank_signatories():
    """Create bank signatories table."""
    if not table_exists('treasury_bank_signatories'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_bank_signatories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bank_account_id INTEGER NOT NULL,
                    signatory_name TEXT NOT NULL,
                    signatory_title TEXT,
                    signatory_email TEXT,
                    signatory_phone TEXT,
                    signature_type TEXT DEFAULT 'primary',
                    is_active INTEGER DEFAULT 1,
                    authorization_limit REAL,
                    requires_dual_signature INTEGER DEFAULT 0,
                            company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bank_account_id) REFERENCES finance_bank_accounts(id)
                )
            """)
            db.execute("CREATE INDEX idx_signatory_bank ON treasury_bank_signatories(bank_account_id)")
            db.commit()


def get_bank_signatories(bank_account_id):
    """Get signatories for a bank account."""
    return get_all(
        "SELECT * FROM treasury_bank_signatories WHERE bank_account_id = ? AND is_active = 1",
        (bank_account_id,)
    )


def create_bank_signatory(data):
    """Create a bank signatory."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO treasury_bank_signatories (
                bank_account_id, signatory_name, signatory_title,
                signatory_email, signatory_phone, signature_type,
                is_active, authorization_limit, requires_dual_signature, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('bank_account_id'),
            data.get('signatory_name'),
            data.get('signatory_title'),
            data.get('signatory_email'),
            data.get('signatory_phone'),
            data.get('signature_type', 'primary'),
            data.get('is_active', 1),
            data.get('authorization_limit'),
            data.get('requires_dual_signature', 0),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# ACCOUNT GROUPS
# ============================================================================

def _create_treasury_account_groups():
    """Create treasury account groups for grouping bank accounts."""
    if not table_exists('treasury_account_groups'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_account_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_code TEXT UNIQUE NOT NULL,
                    group_name TEXT NOT NULL,
                    group_name_ar TEXT,
                    group_type TEXT DEFAULT 'bank',
                    description TEXT,
                    parent_group_id INTEGER,
                    is_active INTEGER DEFAULT 1,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_group_company ON treasury_account_groups(company_id)")
            db.commit()


def get_treasury_account_groups(company_id=None, group_type=None):
    """Get treasury account groups."""
    sql = "SELECT * FROM treasury_account_groups WHERE is_active = 1"
    params = []
    
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    if group_type:
        sql += " AND group_type = ?"
        params.append(group_type)
    
    sql += " ORDER BY group_code, group_name"
    return get_all(sql, params)


def create_treasury_account_group(data):
    """Create a treasury account group."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO treasury_account_groups (
                group_code, group_name, group_name_ar, group_type,
                description, parent_group_id, is_active, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('group_code'),
            data.get('group_name'),
            data.get('group_name_ar'),
            data.get('group_type', 'bank'),
            data.get('description'),
            data.get('parent_group_id'),
            data.get('is_active', 1),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# WORKFLOW RULES
# ============================================================================

def _create_treasury_workflow_rules():
    """Create treasury workflow rules for approval matrices."""
    if not table_exists('treasury_workflow_rules'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_workflow_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    condition_field TEXT,
                    condition_operator TEXT,
                    condition_value TEXT,
                    approval_levels INTEGER DEFAULT 1,
                    level_1_approver_role TEXT,
                    level_1_approver_user_id INTEGER,
                    level_1_min_amount REAL,
                    level_1_max_amount REAL,
                    level_2_approver_role TEXT,
                    level_2_approver_user_id INTEGER,
                    level_2_min_amount REAL,
                    level_2_max_amount REAL,
                    level_3_approver_role TEXT,
                    level_3_approver_user_id INTEGER,
                    level_3_min_amount REAL,
                    escalation_days INTEGER DEFAULT 3,
                    is_active INTEGER DEFAULT 1,
                    priority INTEGER DEFAULT 0,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_workflow_op ON treasury_workflow_rules(operation_type)")
            db.commit()


def get_treasury_workflow_rules(company_id=None, operation_type=None, is_active=True):
    """Get treasury workflow rules."""
    sql = "SELECT * FROM treasury_workflow_rules WHERE 1=1"
    params = []
    
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    if operation_type:
        sql += " AND operation_type = ?"
        params.append(operation_type)
    
    if is_active is not None:
        sql += " AND is_active = ?"
        params.append(1 if is_active else 0)
    
    sql += " ORDER BY priority DESC, id"
    return get_all(sql, params)


def get_applicable_workflow_rule(operation_type, amount, company_id=None):
    """Get the applicable workflow rule for an operation."""
    rules = get_treasury_workflow_rules(company_id=company_id, operation_type=operation_type)
    
    for rule in rules:
        min_amount = rule.get(f'level_1_min_amount', 0) or 0
        max_amount = rule.get(f'level_1_max_amount') or float('inf')
        
        if min_amount <= amount <= max_amount:
            return rule
    
    return None


# ============================================================================
# RECONCILIATION RULES
# ============================================================================

def _create_treasury_reconciliation_rules():
    """Create bank reconciliation rules."""
    if not table_exists('treasury_reconciliation_rules'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_reconciliation_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_name TEXT NOT NULL,
                    rule_type TEXT DEFAULT 'matching',
                    matching_criteria TEXT,
                    auto_match_enabled INTEGER DEFAULT 0,
                    tolerance_amount REAL DEFAULT 0,
                    tolerance_percentage REAL DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_recon_rule_company ON treasury_reconciliation_rules(company_id)")
            db.commit()


# ============================================================================
# DAILY CASH POSITION CALCULATIONS
# ============================================================================

def calculate_daily_cash_position(company_id, date=None):
    """
    Calculate comprehensive daily cash position.
    Aggregates data from bank accounts, petty cash, and cash boxes.
    """
    if not date:
        date = datetime.now().date().isoformat()
    
    # Get bank account balances
    bank_accounts = get_bank_accounts(company_id=company_id, is_active=True)
    
    # Get petty cash balances
    petty_cash_accounts = get_petty_cash_accounts(company_id=company_id, is_active=True)
    
    # Get cash box balances
    cash_boxes = get_cash_boxes(company_id=company_id, is_active=True)
    
    # Aggregate by currency
    position_by_currency = {}
    total_position = 0
    
    for account in bank_accounts:
        currency = account.get('currency', 'AED')
        balance = float(account.get('current_balance', 0) or 0)
        
        if currency not in position_by_currency:
            position_by_currency[currency] = {
                'bank_balance': 0,
                'petty_cash_balance': 0,
                'cash_box_balance': 0,
                'total_balance': 0,
                'bank_accounts': 0,
                'petty_cash_accounts': 0,
                'cash_boxes': 0
            }
        
        position_by_currency[currency]['bank_balance'] += balance
        position_by_currency[currency]['total_balance'] += balance
        position_by_currency[currency]['bank_accounts'] += 1
        total_position += balance
    
    for account in petty_cash_accounts:
        currency = account.get('currency', 'AED')
        balance = float(account.get('current_balance', 0) or 0)
        
        if currency not in position_by_currency:
            position_by_currency[currency] = {
                'bank_balance': 0,
                'petty_cash_balance': 0,
                'cash_box_balance': 0,
                'total_balance': 0,
                'bank_accounts': 0,
                'petty_cash_accounts': 0,
                'cash_boxes': 0
            }
        
        position_by_currency[currency]['petty_cash_balance'] += balance
        position_by_currency[currency]['total_balance'] += balance
        position_by_currency[currency]['petty_cash_accounts'] += 1
        total_position += balance
    
    for box in cash_boxes:
        currency = box.get('currency', 'AED')
        balance = float(box.get('current_balance', 0) or 0)
        
        if currency not in position_by_currency:
            position_by_currency[currency] = {
                'bank_balance': 0,
                'petty_cash_balance': 0,
                'cash_box_balance': 0,
                'total_balance': 0,
                'bank_accounts': 0,
                'petty_cash_accounts': 0,
                'cash_boxes': 0
            }
        
        position_by_currency[currency]['cash_box_balance'] += balance
        position_by_currency[currency]['total_balance'] += balance
        position_by_currency[currency]['cash_boxes'] += 1
        total_position += balance
    
    return {
        'date': date,
        'total_position': total_position,
        'by_currency': position_by_currency,
        'bank_account_count': len(bank_accounts),
        'petty_cash_count': len(petty_cash_accounts),
        'cash_box_count': len(cash_boxes)
    }


def get_cash_flow_forecast_data(company_id, days=30, forecast_id=None):
    """
    Get cash flow forecast data for specified days.
    Combines expected inflows (from AR) and outflows (from AP).
    """
    from finance_models import get_customer_invoices, get_supplier_bills
    
    today = datetime.now().date()
    end_date = today + timedelta(days=days)
    
    # Get open AR invoices
    open_ar = get_customer_invoices(company_id=company_id, status='Posted')
    
    # Get open AP bills
    open_ap = get_supplier_bills(company_id=company_id, status='Posted')
    
    # Calculate daily forecasts
    forecast_by_date = {}
    
    # Initialize all days
    for i in range(days + 1):
        day = today + timedelta(days=i)
        date_str = day.isoformat()
        forecast_by_date[date_str] = {
            'date': date_str,
            'day_name': day.strftime('%A'),
            'inflow': 0,
            'outflow': 0,
            'net': 0,
            'inflow_items': [],
            'outflow_items': []
        }
    
    # Add expected inflows from AR
    for inv in open_ar:
        due_date_str = inv.get('due_date')
        if due_date_str:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            if today <= due_date <= end_date:
                amount = float(inv.get('total_amount', 0) or 0) - float(inv.get('amount_paid', 0) or 0)
                if amount > 0:
                    if due_date_str in forecast_by_date:
                        forecast_by_date[due_date_str]['inflow'] += amount
                        forecast_by_date[due_date_str]['inflow_items'].append({
                            'type': 'ar_receipt',
                            'id': inv.get('id'),
                            'reference': inv.get('invoice_number'),
                            'customer': inv.get('customer_name'),
                            'amount': amount
                        })
    
    # Add expected outflows from AP
    for bill in open_ap:
        due_date_str = bill.get('due_date')
        if due_date_str:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            if today <= due_date <= end_date:
                amount = float(bill.get('total_amount', 0) or 0) - float(bill.get('amount_paid', 0) or 0)
                if amount > 0:
                    if due_date_str in forecast_by_date:
                        forecast_by_date[due_date_str]['outflow'] += amount
                        forecast_by_date[due_date_str]['outflow_items'].append({
                            'type': 'ap_payment',
                            'id': bill.get('id'),
                            'reference': bill.get('bill_number'),
                            'supplier': bill.get('supplier_name'),
                            'amount': amount
                        })
    
    # Calculate net position for each day
    for date_str, data in forecast_by_date.items():
        data['net'] = data['inflow'] - data['outflow']
    
    return {
        'start_date': today.isoformat(),
        'end_date': end_date.isoformat(),
        'days': days,
        'forecast': forecast_by_date
    }


def get_weekly_forecast_summary(company_id, weeks=4):
    """Get weekly aggregated forecast data."""
    daily = get_cash_flow_forecast_data(company_id, days=weeks*7)
    
    weekly_summary = []
    current_week = []
    week_num = 1
    
    for date_str, data in daily['forecast'].items():
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
                'net': week_inflow - week_outflow,
                'daily_data': current_week
            })
            current_week = []
            week_num += 1
    
    return weekly_summary


# ============================================================================
# LIQUIDITY ANALYSIS
# ============================================================================

def analyze_liquidity_position(company_id, date=None):
    """
    Analyze liquidity position and identify gaps or surpluses.
    """
    if not date:
        date = datetime.now().date().isoformat()
    
    # Get current cash position
    current_position = calculate_daily_cash_position(company_id, date)
    
    # Get liquidity thresholds
    thresholds = get_liquidity_thresholds(company_id=company_id)
    
    # Get 7-day forecast
    forecast_7day = get_cash_flow_forecast_data(company_id, days=7)
    
    # Get 30-day forecast
    forecast_30day = get_cash_flow_forecast_data(company_id, days=30)
    
    # Calculate minimum liquidity required
    total_min_threshold = sum(t.get('threshold_value', 0) for t in thresholds 
                              if t.get('threshold_type') == 'minimum_balance')
    
    # Identify issues
    issues = []
    
    for currency, data in current_position['by_currency'].items():
        available = data['total_balance']
        
        # Check against thresholds
        for threshold in thresholds:
            if threshold.get('threshold_type') == 'minimum_balance':
                min_required = threshold.get('threshold_value', 0)
                if available < min_required:
                    issues.append({
                        'type': 'below_minimum',
                        'severity': threshold.get('urgency_level', 'high'),
                        'currency': currency,
                        'available': available,
                        'required': min_required,
                        'gap': min_required - available
                    })
    
    # Calculate projected position
    projected_7day_net = sum(d['net'] for d in forecast_7day['forecast'].values())
    projected_30day_net = sum(d['net'] for d in forecast_30day['forecast'].values())
    
    return {
        'date': date,
        'current_position': current_position,
        'thresholds': thresholds,
        'projected_7day_net': projected_7day_net,
        'projected_30day_net': projected_30day_net,
        'minimum_required': total_min_threshold,
        'issues': issues,
        'liquidity_status': 'healthy' if not issues else 'at_risk'
    }


# ============================================================================
# BANK RECONCILIATION HELPERS
# ============================================================================

def get_bank_reconciliation_status(company_id, bank_account_id=None):
    """Get reconciliation status for bank accounts."""
    sql = """
        SELECT 
            fb.id as bank_account_id,
            fb.bank_name,
            fb.account_name,
            fb.account_number,
            fb.current_balance,
            COALESCE(brs.closing_balance, 0) as statement_balance,
            COALESCE(brs.statement_date) as last_reconciled_date,
            COALESCE(brs.closing_balance, 0) - fb.current_balance as difference
        FROM finance_bank_accounts fb
        LEFT JOIN (
            SELECT bank_account_id, closing_balance, statement_date
            FROM finance_bank_reconciliation_statements
            WHERE id IN (
                SELECT MAX(id) 
                FROM finance_bank_reconciliation_statements 
                GROUP BY bank_account_id
            )
        ) brs ON fb.id = brs.bank_account_id
        WHERE fb.company_id = ?
    """
    params = [company_id]
    
    if bank_account_id:
        sql += " AND fb.id = ?"
        params.append(bank_account_id)
    
    return get_all(sql, params)


def get_unreconciled_transactions(company_id, bank_account_id=None, days=30):
    """Get unreconciled transactions for bank account."""
    start_date = (datetime.now().date() - timedelta(days=days)).isoformat()
    
    sql = """
        SELECT * FROM finance_journal_lines
        WHERE account_id IN (
            SELECT gl_account_id FROM finance_bank_accounts 
            WHERE company_id = ? AND gl_account_id IS NOT NULL
        )
        AND created_at >= ?
    """
    params = [company_id, start_date]
    
    if bank_account_id:
        sql += " AND account_id IN (SELECT gl_account_id FROM finance_bank_accounts WHERE id = ?)"
        params.append(bank_account_id)
    
    return get_all(sql, params)


# ============================================================================
# SAMPLE DATA GENERATION
# ============================================================================

def generate_sample_treasury_data(company_id):
    """Generate realistic sample treasury data for demo purposes."""
    
    # Sample bank accounts
    sample_banks = [
        {'bank_name': 'Emirates NBD', 'account_name': 'Main Operating Account', 'account_number': '0521-7845-3021', 'currency': 'AED', 'current_balance': 2450000, 'account_type': 'checking'},
        {'bank_name': 'Emirates NBD', 'account_name': 'Payroll Account', 'account_number': '0521-7845-3022', 'currency': 'AED', 'current_balance': 450000, 'account_type': 'payroll'},
        {'bank_name': 'Abu Dhabi Commercial Bank', 'account_name': 'Main Operating Account', 'account_number': '0712-3456-7890', 'currency': 'AED', 'current_balance': 1820000, 'account_type': 'checking'},
        {'bank_name': 'Standard Chartered', 'account_name': 'USD Operations', 'account_number': '0891-2345-6789', 'currency': 'USD', 'current_balance': 890000, 'account_type': 'checking'},
        {'bank_name': 'HSBC', 'account_name': 'EUR Account', 'account_number': '0456-7890-1234', 'currency': 'EUR', 'current_balance': 340000, 'account_type': 'checking'},
        {'bank_name': 'First Abu Dhabi Bank', 'account_name': 'Reserve Account', 'account_number': '0345-6789-0123', 'currency': 'AED', 'current_balance': 5000000, 'account_type': 'savings'},
    ]
    
    for bank in sample_banks:
        bank['company_id'] = company_id
        bank['opening_balance'] = bank['current_balance']
        bank['is_active'] = 1
        create_bank_account(bank)
    
    # Sample petty cash accounts
    sample_petty = [
        {'account_code': 'PC-001', 'account_name': 'Main Office Petty Cash', 'float_amount': 5000, 'current_balance': 3850, 'currency': 'AED', 'location': 'Main Office'},
        {'account_code': 'PC-002', 'account_name': 'Warehouse Petty Cash', 'float_amount': 2000, 'current_balance': 1540, 'currency': 'AED', 'location': 'Warehouse'},
        {'account_code': 'PC-003', 'account_name': 'Branch Petty Cash', 'float_amount': 3000, 'current_balance': 2750, 'currency': 'AED', 'location': 'Dubai Branch'},
    ]
    
    for pc in sample_petty:
        pc['company_id'] = company_id
        pc['is_active'] = 1
        create_petty_cash_account(pc)
    
    # Sample cash boxes
    sample_boxes = [
        {'box_code': 'CB-001', 'box_name': 'Main Reception Cash Box', 'opening_balance': 1000, 'current_balance': 850, 'currency': 'AED', 'location': 'Main Reception'},
        {'box_code': 'CB-002', 'box_name': 'Cafeteria Cash Box', 'opening_balance': 500, 'current_balance': 320, 'currency': 'AED', 'location': 'Cafeteria'},
    ]
    
    for box in sample_boxes:
        box['company_id'] = company_id
        box['is_active'] = 1
        create_cash_box(box)
    
    # Sample treasury alerts
    sample_alerts = [
        {'alert_type': 'low_balance', 'alert_category': 'liquidity', 'severity': 'high', 'title': 'Low Balance Alert - Payroll Account', 'message': 'Payroll account balance below minimum threshold', 'amount': 450000, 'currency': 'AED', 'company_id': company_id},
        {'alert_type': 'large_outflow', 'alert_category': 'cash_flow', 'severity': 'medium', 'title': 'Large Outflow Detected', 'message': 'Single transaction exceeding 500,000 AED detected', 'amount': 750000, 'currency': 'AED', 'company_id': company_id},
        {'alert_type': 'overdue_collection', 'alert_category': 'collections', 'severity': 'high', 'title': 'Overdue Collection Alert', 'message': 'Invoice #INV-2026-0045 is 45 days overdue', 'amount': 125000, 'currency': 'AED', 'company_id': company_id},
        {'alert_type': 'reconciliation', 'alert_category': 'reconciliation', 'severity': 'medium', 'title': 'Reconciliation Gap', 'message': 'Bank statement does not match GL for account ****3021', 'amount': 15420, 'currency': 'AED', 'company_id': company_id},
    ]
    
    for alert in sample_alerts:
        create_treasury_alert(alert)
    
    # Sample treasury controls
    sample_controls = [
        {'control_name': 'high_value_transfer', 'control_type': 'transfer_limit', 'control_category': 'approval', 'description': 'High value transfers require dual approval', 'threshold_value': 500000, 'threshold_operator': 'greater_equal', 'affected_operations': 'bank_transfer', 'severity': 'high', 'company_id': company_id},
        {'control_name': 'petty_cash_limit', 'control_type': 'transaction_limit', 'control_category': 'petty_cash', 'description': 'Single petty cash transaction limit', 'threshold_value': 1000, 'threshold_operator': 'greater_than', 'affected_operations': 'petty_cash_withdrawal', 'severity': 'medium', 'company_id': company_id},
        {'control_name': 'minimum_cash_balance', 'control_type': 'balance_threshold', 'control_category': 'liquidity', 'description': 'Minimum operating cash balance required', 'threshold_value': 500000, 'threshold_operator': 'less_than', 'affected_operations': 'all', 'severity': 'critical', 'company_id': company_id},
    ]
    
    for control in sample_controls:
        create_treasury_control(control)
    
    # Sample liquidity thresholds
    sample_thresholds = [
        {'threshold_name': 'Minimum AED Operating Balance', 'threshold_type': 'minimum_balance', 'threshold_value': 500000, 'comparison_operator': 'less_than', 'currency': 'AED', 'urgency_level': 'critical', 'company_id': company_id},
        {'threshold_name': 'Warning AED Balance', 'threshold_type': 'minimum_balance', 'threshold_value': 1000000, 'comparison_operator': 'less_than', 'currency': 'AED', 'urgency_level': 'high', 'company_id': company_id},
        {'threshold_name': 'Minimum USD Balance', 'threshold_type': 'minimum_balance', 'threshold_value': 100000, 'comparison_operator': 'less_than', 'currency': 'USD', 'urgency_level': 'high', 'company_id': company_id},
    ]
    
    for threshold in sample_thresholds:
        create_liquidity_threshold(threshold)
    
    return True


# ============================================================================
# BANK STATEMENT IMPORT & RECONCILIATION ENHANCEMENTS
# ============================================================================

def _create_treasury_bank_statements():
    """Create bank statements table for reconciliation."""
    if not table_exists('treasury_bank_statements'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_bank_statements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bank_account_id INTEGER NOT NULL,
                    statement_number TEXT,
                    statement_date DATE NOT NULL,
                    opening_balance REAL DEFAULT 0,
                    closing_balance REAL DEFAULT 0,
                    total_credits REAL DEFAULT 0,
                    total_debits REAL DEFAULT 0,
                    currency TEXT DEFAULT 'AED',
                    file_name TEXT,
                    file_type TEXT DEFAULT 'MT940',
                    import_status TEXT DEFAULT 'imported',
                    imported_by INTEGER,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bank_account_id) REFERENCES finance_bank_accounts(id)
                )
            """)
            db.execute("CREATE INDEX idx_stmt_bank ON treasury_bank_statements(bank_account_id)")
            db.execute("CREATE INDEX idx_stmt_date ON treasury_bank_statements(statement_date)")
            db.commit()


def _create_treasury_bank_statement_lines():
    """Create bank statement lines table."""
    if not table_exists('treasury_bank_statement_lines'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_bank_statement_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    statement_id INTEGER NOT NULL,
                    line_reference TEXT,
                    transaction_date DATE NOT NULL,
                    value_date DATE,
                    description TEXT,
                    reference TEXT,
                    amount REAL NOT NULL,
                    transaction_type TEXT,
                    debit_credit TEXT,
                    bank_reference TEXT,
                    counterparty_account TEXT,
                    counterparty_name TEXT,
                    category TEXT,
                    is_reconciled INTEGER DEFAULT 0,
                    matched_journal_id INTEGER,
                    matched_amount REAL,
                    tolerance REAL DEFAULT 0,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (statement_id) REFERENCES treasury_bank_statements(id)
                )
            """)
            db.execute("CREATE INDEX idx_line_stmt ON treasury_bank_statement_lines(statement_id)")
            db.execute("CREATE INDEX idx_line_date ON treasury_bank_statement_lines(transaction_date)")
            db.execute("CREATE INDEX idx_line_reconciled ON treasury_bank_statement_lines(is_reconciled)")
            db.commit()


def create_bank_statement(statement_data):
    """Create a new bank statement."""
    with get_db_context() as db:
        db.execute("""
            INSERT INTO treasury_bank_statements 
            (bank_account_id, statement_number, statement_date, opening_balance, closing_balance,
             total_credits, total_debits, currency, file_name, file_type, import_status, imported_by, company_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            statement_data.get('bank_account_id'),
            statement_data.get('statement_number'),
            statement_data.get('statement_date'),
            statement_data.get('opening_balance', 0),
            statement_data.get('closing_balance', 0),
            statement_data.get('total_credits', 0),
            statement_data.get('total_debits', 0),
            statement_data.get('currency', 'AED'),
            statement_data.get('file_name'),
            statement_data.get('file_type', 'MT940'),
            statement_data.get('import_status', 'imported'),
            statement_data.get('imported_by'),
            statement_data.get('company_id')
        ))
        db.commit()
        return db.execute("SELECT last_insert_rowid() as id").fetchone()['id']


def create_bank_statement_line(line_data):
    """Create a bank statement line."""
    with get_db_context() as db:
        db.execute("""
            INSERT INTO treasury_bank_statement_lines
            (statement_id, line_reference, transaction_date, value_date, description, reference,
             amount, transaction_type, debit_credit, bank_reference, counterparty_account, 
             counterparty_name, category, company_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            line_data.get('statement_id'),
            line_data.get('line_reference'),
            line_data.get('transaction_date'),
            line_data.get('value_date'),
            line_data.get('description'),
            line_data.get('reference'),
            line_data.get('amount'),
            line_data.get('transaction_type'),
            line_data.get('debit_credit'),
            line_data.get('bank_reference'),
            line_data.get('counterparty_account'),
            line_data.get('counterparty_name'),
            line_data.get('category'),
            line_data.get('company_id')
        ))
        db.commit()
        return db.execute("SELECT last_insert_rowid() as id").fetchone()['id']


def get_bank_statements(bank_account_id=None, company_id=None, start_date=None, end_date=None):
    """Get bank statements with optional filters."""
    sql = "SELECT * FROM treasury_bank_statements WHERE 1=1"
    params = []
    
    if bank_account_id:
        sql += " AND bank_account_id = ?"
        params.append(bank_account_id)
    
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    if start_date:
        sql += " AND statement_date >= ?"
        params.append(start_date)
    
    if end_date:
        sql += " AND statement_date <= ?"
        params.append(end_date)
    
    sql += " ORDER BY statement_date DESC"
    return get_all(sql, params)


def get_bank_statement_lines(statement_id):
    """Get lines for a bank statement."""
    return get_all(
        "SELECT * FROM treasury_bank_statement_lines WHERE statement_id = ? ORDER BY transaction_date",
        [statement_id]
    )


def get_unreconciled_lines(bank_account_id, company_id, days=30):
    """Get unreconciled statement lines."""
    start_date = (datetime.now().date() - timedelta(days=days)).isoformat()
    
    sql = """
        SELECT l.*, s.statement_date, s.statement_number, s.bank_account_id
        FROM treasury_bank_statement_lines l
        JOIN treasury_bank_statements s ON l.statement_id = s.id
        WHERE l.is_reconciled = 0 
        AND s.bank_account_id = ?
        AND s.company_id = ?
        AND l.transaction_date >= ?
        ORDER BY l.transaction_date
    """
    return get_all(sql, [bank_account_id, company_id, start_date])


def match_statement_line(line_id, journal_id, matched_amount, user_id):
    """Match a statement line to a journal entry."""
    with get_db_context() as db:
        db.execute("""
            UPDATE treasury_bank_statement_lines
            SET is_reconciled = 1, matched_journal_id = ?, matched_amount = ?
            WHERE id = ?
        """, (journal_id, matched_amount, line_id))
        
        log_treasury_audit(
            action='matched',
            entity_type='bank_statement_line',
            entity_id=line_id,
            user_id=user_id,
            company_id=get_company_id(),
            details={'journal_id': journal_id, 'matched_amount': matched_amount}
        )
        db.commit()


def unmatch_statement_line(line_id, user_id):
    """Unmatch a previously matched statement line."""
    with get_db_context() as db:
        db.execute("""
            UPDATE treasury_bank_statement_lines
            SET is_reconciled = 0, matched_journal_id = NULL, matched_amount = NULL
            WHERE id = ?
        """, [line_id])
        
        log_treasury_audit(
            action='unmatched',
            entity_type='bank_statement_line',
            entity_id=line_id,
            user_id=user_id,
            company_id=get_company_id()
        )
        db.commit()


# ============================================================================
# PAYMENT RUNS
# ============================================================================

def _create_treasury_payment_runs():
    """Create payment runs table."""
    if not table_exists('treasury_payment_runs'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_payment_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_number TEXT UNIQUE NOT NULL,
                    run_name TEXT,
                    run_date DATE NOT NULL,
                    bank_account_id INTEGER,
                    payment_type TEXT,
                    total_amount REAL DEFAULT 0,
                    currency TEXT DEFAULT 'AED',
                    status TEXT DEFAULT 'draft',
                    payment_method TEXT,
                    scheduled_date DATE,
                    executed_date DATETIME,
                    executed_by INTEGER,
                    approved_by INTEGER,
                    rejection_reason TEXT,
                    notes TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bank_account_id) REFERENCES finance_bank_accounts(id)
                )
            """)
            db.execute("CREATE INDEX idx_payrun_number ON treasury_payment_runs(run_number)")
            db.execute("CREATE INDEX idx_payrun_status ON treasury_payment_runs(status)")
            db.execute("CREATE INDEX idx_payrun_date ON treasury_payment_runs(run_date)")
            db.commit()


def _create_treasury_payment_run_items():
    """Create payment run items table."""
    if not table_exists('treasury_payment_run_items'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_payment_run_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_run_id INTEGER NOT NULL,
                    source_type TEXT,
                    source_id INTEGER,
                    payee_name TEXT,
                    payee_account TEXT,
                    payee_bank TEXT,
                    description TEXT,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'AED',
                    priority INTEGER DEFAULT 5,
                    due_date DATE,
                    status TEXT DEFAULT 'pending',
                    is_selected INTEGER DEFAULT 1,
                    rejection_reason TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (payment_run_id) REFERENCES treasury_payment_runs(id)
                )
            """)
            db.execute("CREATE INDEX idx_payrunitem_run ON treasury_payment_run_items(payment_run_id)")
            db.execute("CREATE INDEX idx_payrunitem_status ON treasury_payment_run_items(status)")
            db.commit()


def create_payment_run(run_data):
    """Create a new payment run."""
    with get_db_context() as db:
        run_number = f"PR-{datetime.now().strftime('%Y%m%d')}-{db.execute('SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM treasury_payment_runs').fetchone()['next_id']}"
        
        db.execute("""
            INSERT INTO treasury_payment_runs
            (run_number, run_name, run_date, bank_account_id, payment_type, currency, 
             status, payment_method, scheduled_date, company_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_number,
            run_data.get('run_name'),
            run_data.get('run_date'),
            run_data.get('bank_account_id'),
            run_data.get('payment_type'),
            run_data.get('currency', 'AED'),
            'draft',
            run_data.get('payment_method'),
            run_data.get('scheduled_date'),
            run_data.get('company_id')
        ))
        db.commit()
        return db.execute("SELECT last_insert_rowid() as id").fetchone()['id']


def add_payment_run_item(run_id, item_data):
    """Add an item to a payment run."""
    with get_db_context() as db:
        db.execute("""
            INSERT INTO treasury_payment_run_items
            (payment_run_id, source_type, source_id, payee_name, payee_account, payee_bank,
             description, amount, currency, priority, due_date, company_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            item_data.get('source_type'),
            item_data.get('source_id'),
            item_data.get('payee_name'),
            item_data.get('payee_account'),
            item_data.get('payee_bank'),
            item_data.get('description'),
            item_data.get('amount'),
            item_data.get('currency', 'AED'),
            item_data.get('priority', 5),
            item_data.get('due_date'),
            item_data.get('company_id')
        ))
        db.commit()


def get_payment_runs(company_id, status=None, bank_account_id=None):
    """Get payment runs with filters."""
    sql = "SELECT * FROM treasury_payment_runs WHERE company_id = ?"
    params = [company_id]
    
    if status:
        sql += " AND status = ?"
        params.append(status)
    
    if bank_account_id:
        sql += " AND bank_account_id = ?"
        params.append(bank_account_id)
    
    sql += " ORDER BY run_date DESC"
    return get_all(sql, params)


def get_payment_run_items(run_id):
    """Get items in a payment run."""
    return get_all(
        "SELECT * FROM treasury_payment_run_items WHERE payment_run_id = ? ORDER BY priority, due_date",
        [run_id]
    )


def update_payment_run_status(run_id, status, user_id, notes=None):
    """Update payment run status."""
    with get_db_context() as db:
        update_fields = "status = ?, updated_at = CURRENT_TIMESTAMP"
        params = [status, run_id]
        
        if status == 'executed':
            update_fields += ", executed_date = CURRENT_TIMESTAMP, executed_by = ?"
            params.append(user_id)
        elif status == 'approved':
            update_fields += ", approved_by = ?"
            params.append(user_id)
        elif status == 'rejected':
            update_fields += ", rejection_reason = ?"
            params.append(notes)
        
        db.execute(f"UPDATE treasury_payment_runs SET {update_fields} WHERE id = ?", params)
        db.commit()


def calculate_payment_run_totals(run_id):
    """Calculate and update payment run totals."""
    items = get_payment_run_items(run_id)
    total = sum(item['amount'] for item in items if item['is_selected'])
    
    with get_db_context() as db:
        db.execute("UPDATE treasury_payment_runs SET total_amount = ? WHERE id = ?", [total, run_id])
        db.commit()
    
    return total


# ============================================================================
# FX CONTRACTS
# ============================================================================

def _create_treasury_fx_contracts():
    """Create FX contracts table."""
    if not table_exists('treasury_fx_contracts'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_fx_contracts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contract_number TEXT UNIQUE NOT NULL,
                    contract_type TEXT NOT NULL,
                    buy_sell TEXT NOT NULL,
                    base_currency TEXT NOT NULL,
                    quote_currency TEXT NOT NULL,
                    base_amount REAL NOT NULL,
                    quote_amount REAL NOT NULL,
                    exchange_rate REAL NOT NULL,
                    spot_rate REAL,
                    forward_points REAL DEFAULT 0,
                    contract_date DATE NOT NULL,
                    value_date DATE NOT NULL,
                    maturity_date DATE,
                    counterparty TEXT,
                    counterparty_bank TEXT,
                    status TEXT DEFAULT 'active',
                    settlement_status TEXT DEFAULT 'unsettled',
                    settlement_date DATE,
                    settlement_amount REAL,
                    gain_loss REAL,
                    notes TEXT,
                    company_id INTEGER,
                    created_by INTEGER,
                    approved_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_fx_contract_number ON treasury_fx_contracts(contract_number)")
            db.execute("CREATE INDEX idx_fx_status ON treasury_fx_contracts(status)")
            db.execute("CREATE INDEX idx_fx_value_date ON treasury_fx_contracts(value_date)")
            db.commit()


def create_fx_contract(contract_data):
    """Create a new FX contract."""
    with get_db_context() as db:
        contract_number = f"FX-{datetime.now().strftime('%Y%m%d')}-{db.execute('SELECT COALESCE(MAX(id), 0) + 1 as next_id FROM treasury_fx_contracts').fetchone()['next_id']}"
        
        db.execute("""
            INSERT INTO treasury_fx_contracts
            (contract_number, contract_type, buy_sell, base_currency, quote_currency,
             base_amount, quote_amount, exchange_rate, spot_rate, forward_points,
             contract_date, value_date, maturity_date, counterparty, counterparty_bank,
             status, settlement_status, notes, company_id, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            contract_number,
            contract_data.get('contract_type', 'spot'),
            contract_data.get('buy_sell'),
            contract_data.get('base_currency'),
            contract_data.get('quote_currency'),
            contract_data.get('base_amount'),
            contract_data.get('quote_amount'),
            contract_data.get('exchange_rate'),
            contract_data.get('spot_rate'),
            contract_data.get('forward_points', 0),
            contract_data.get('contract_date'),
            contract_data.get('value_date'),
            contract_data.get('maturity_date'),
            contract_data.get('counterparty'),
            contract_data.get('counterparty_bank'),
            'active',
            'unsettled',
            contract_data.get('notes'),
            contract_data.get('company_id'),
            contract_data.get('created_by')
        ))
        db.commit()
        return db.execute("SELECT last_insert_rowid() as id").fetchone()['id']


def get_fx_contracts(company_id, status=None, currency=None):
    """Get FX contracts with filters."""
    sql = "SELECT * FROM treasury_fx_contracts WHERE company_id = ?"
    params = [company_id]
    
    if status:
        sql += " AND status = ?"
        params.append(status)
    
    if currency:
        sql += " AND (base_currency = ? OR quote_currency = ?)"
        params.extend([currency, currency])
    
    sql += " ORDER BY contract_date DESC"
    return get_all(sql, params)


def settle_fx_contract(contract_id, settlement_amount, gain_loss, user_id):
    """Settle an FX contract."""
    with get_db_context() as db:
        db.execute("""
            UPDATE treasury_fx_contracts
            SET settlement_status = 'settled', settlement_date = CURRENT_DATE,
                settlement_amount = ?, gain_loss = ?, status = 'settled',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (settlement_amount, gain_loss, contract_id))
        
        log_treasury_audit(
            action='settled',
            entity_type='fx_contract',
            entity_id=contract_id,
            user_id=user_id,
            company_id=get_company_id(),
            details={'settlement_amount': settlement_amount, 'gain_loss': gain_loss}
        )
        db.commit()


def get_fx_position(company_id, date=None):
    """Calculate FX position by currency."""
    if not date:
        date = datetime.now().date().isoformat()
    
    contracts = get_fx_contracts(company_id, status='active')
    
    positions = {}
    for contract in contracts:
        base = contract['base_currency']
        quote = contract['quote_currency']
        base_amt = contract['base_amount']
        quote_amt = contract['quote_amount']
        
        if contract['buy_sell'] == 'buy':
            positions[base] = positions.get(base, 0) + base_amt
            positions[quote] = positions.get(quote, 0) - quote_amt
        else:
            positions[base] = positions.get(base, 0) - base_amt
            positions[quote] = positions.get(quote, 0) + quote_amt
    
    return positions


# ============================================================================
# COUNTERPARTIES & BANKING RELATIONSHIPS
# ============================================================================

def _create_treasury_counterparties():
    """Create treasury counterparties table."""
    if not table_exists('treasury_counterparties'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_counterparties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    counterparty_name TEXT NOT NULL,
                    counterparty_type TEXT,
                    bank_name TEXT,
                    bank_branch TEXT,
                    account_number TEXT,
                    iban TEXT,
                    swift_code TEXT,
                    routing_number TEXT,
                    contact_name TEXT,
                    contact_email TEXT,
                    contact_phone TEXT,
                    credit_limit REAL,
                    current_exposure REAL DEFAULT 0,
                    risk_rating TEXT,
                    payment_terms INTEGER,
                    bank_charges REAL DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    notes TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_cp_name ON treasury_counterparties(counterparty_name)")
            db.execute("CREATE INDEX idx_cp_type ON treasury_counterparties(counterparty_type)")
            db.commit()


def _create_treasury_bank_connections():
    """Create bank connections table."""
    if not table_exists('treasury_bank_connections'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_bank_connections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bank_account_id INTEGER,
                    connection_type TEXT,
                    api_endpoint TEXT,
                    api_key TEXT,
                    is_active INTEGER DEFAULT 0,
                    last_sync DATETIME,
                    sync_status TEXT,
                    sync_frequency TEXT,
                    authentication_method TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bank_account_id) REFERENCES finance_bank_accounts(id)
                )
            """)
            db.execute("CREATE INDEX idx_bc_account ON treasury_bank_connections(bank_account_id)")
            db.commit()


def _create_treasury_bank_charges():
    """Create bank charges tracking table."""
    if not table_exists('treasury_bank_charges'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_bank_charges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bank_account_id INTEGER,
                    charge_date DATE NOT NULL,
                    charge_type TEXT,
                    description TEXT,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'AED',
                    reference TEXT,
                    is_automated INTEGER DEFAULT 0,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bank_account_id) REFERENCES finance_bank_accounts(id)
                )
            """)
            db.execute("CREATE INDEX idx_charge_account ON treasury_bank_charges(bank_account_id)")
            db.execute("CREATE INDEX idx_charge_date ON treasury_bank_charges(charge_date)")
            db.commit()


def create_counterparty(cp_data):
    """Create a new counterparty."""
    with get_db_context() as db:
        db.execute("""
            INSERT INTO treasury_counterparties
            (counterparty_name, counterparty_type, bank_name, bank_branch, account_number,
             iban, swift_code, routing_number, contact_name, contact_email, contact_phone,
             credit_limit, risk_rating, payment_terms, notes, company_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cp_data.get('counterparty_name'),
            cp_data.get('counterparty_type'),
            cp_data.get('bank_name'),
            cp_data.get('bank_branch'),
            cp_data.get('account_number'),
            cp_data.get('iban'),
            cp_data.get('swift_code'),
            cp_data.get('routing_number'),
            cp_data.get('contact_name'),
            cp_data.get('contact_email'),
            cp_data.get('contact_phone'),
            cp_data.get('credit_limit'),
            cp_data.get('risk_rating'),
            cp_data.get('payment_terms'),
            cp_data.get('notes'),
            cp_data.get('company_id')
        ))
        db.commit()
        return db.execute("SELECT last_insert_rowid() as id").fetchone()['id']


def get_counterparties(company_id, counterparty_type=None, is_active=True):
    """Get counterparties with filters."""
    sql = "SELECT * FROM treasury_counterparties WHERE company_id = ?"
    params = [company_id]
    
    if counterparty_type:
        sql += " AND counterparty_type = ?"
        params.append(counterparty_type)
    
    if is_active is not None:
        sql += " AND is_active = ?"
        params.append(1 if is_active else 0)
    
    sql += " ORDER BY counterparty_name"
    return get_all(sql, params)


def create_bank_charge(charge_data):
    """Create a bank charge entry."""
    with get_db_context() as db:
        db.execute("""
            INSERT INTO treasury_bank_charges
            (bank_account_id, charge_date, charge_type, description, amount, currency, reference, company_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            charge_data.get('bank_account_id'),
            charge_data.get('charge_date'),
            charge_data.get('charge_type'),
            charge_data.get('description'),
            charge_data.get('amount'),
            charge_data.get('currency', 'AED'),
            charge_data.get('reference'),
            charge_data.get('company_id')
        ))
        db.commit()


def get_bank_charges(company_id, bank_account_id=None, start_date=None, end_date=None):
    """Get bank charges with filters."""
    sql = "SELECT * FROM treasury_bank_charges WHERE company_id = ?"
    params = [company_id]
    
    if bank_account_id:
        sql += " AND bank_account_id = ?"
        params.append(bank_account_id)
    
    if start_date:
        sql += " AND charge_date >= ?"
        params.append(start_date)
    
    if end_date:
        sql += " AND charge_date <= ?"
        params.append(end_date)
    
    sql += " ORDER BY charge_date DESC"
    return get_all(sql, params)


# ============================================================================
# CASH POOLING & CONCENTRATION
# ============================================================================

def _create_treasury_cash_pools():
    """Create cash pools table."""
    if not table_exists('treasury_cash_pools'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_cash_pools (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pool_name TEXT NOT NULL,
                    pool_type TEXT NOT NULL,
                    pooling_method TEXT,
                    master_account_id INTEGER,
                    currency TEXT DEFAULT 'AED',
                    total_balance REAL DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    notes TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (master_account_id) REFERENCES finance_bank_accounts(id)
                )
            """)
            db.execute("CREATE INDEX idx_pool_name ON treasury_cash_pools(pool_name)")
            db.execute("CREATE INDEX idx_pool_type ON treasury_cash_pools(pool_type)")
            db.commit()


def _create_treasury_cash_pool_members():
    """Create cash pool members table."""
    if not table_exists('treasury_cash_pool_members'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_cash_pool_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pool_id INTEGER NOT NULL,
                    bank_account_id INTEGER NOT NULL,
                    account_role TEXT DEFAULT 'member',
                    current_balance REAL DEFAULT 0,
                    pooled_balance REAL DEFAULT 0,
                    interest_applied REAL DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pool_id) REFERENCES treasury_cash_pools(id),
                    FOREIGN KEY (bank_account_id) REFERENCES finance_bank_accounts(id)
                )
            """)
            db.execute("CREATE INDEX idx_poolmember_pool ON treasury_cash_pool_members(pool_id)")
            db.execute("CREATE INDEX idx_poolmember_account ON treasury_cash_pool_members(bank_account_id)")
            db.commit()


def _create_treasury_notional_pooling():
    """Create notional pooling structure table."""
    if not table_exists('treasury_notional_pooling'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_notional_pooling (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pool_id INTEGER NOT NULL,
                    currency TEXT NOT NULL,
                    total_inflows REAL DEFAULT 0,
                    total_outflows REAL DEFAULT 0,
                    net_position REAL DEFAULT 0,
                    interest_rate REAL DEFAULT 0,
                    interest_amount REAL DEFAULT 0,
                    calculation_date DATE,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (pool_id) REFERENCES treasury_cash_pools(id)
                )
            """)
            db.execute("CREATE INDEX idx_notional_pool ON treasury_notional_pooling(pool_id)")
            db.commit()


def create_cash_pool(pool_data):
    """Create a new cash pool."""
    with get_db_context() as db:
        db.execute("""
            INSERT INTO treasury_cash_pools
            (pool_name, pool_type, pooling_method, master_account_id, currency, notes, company_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            pool_data.get('pool_name'),
            pool_data.get('pool_type', 'physical'),
            pool_data.get('pooling_method', 'zero_balance'),
            pool_data.get('master_account_id'),
            pool_data.get('currency', 'AED'),
            pool_data.get('notes'),
            pool_data.get('company_id')
        ))
        db.commit()
        return db.execute("SELECT last_insert_rowid() as id").fetchone()['id']


def add_pool_member(pool_id, bank_account_id, company_id):
    """Add a member to a cash pool."""
    with get_db_context() as db:
        db.execute("""
            INSERT INTO treasury_cash_pool_members
            (pool_id, bank_account_id, company_id)
            VALUES (?, ?, ?)
        """, (pool_id, bank_account_id, company_id))
        db.commit()


def get_cash_pools(company_id, is_active=True):
    """Get cash pools."""
    sql = "SELECT * FROM treasury_cash_pools WHERE company_id = ?"
    if is_active:
        sql += " AND is_active = 1"
    sql += " ORDER BY pool_name"
    return get_all(sql, [company_id])


def get_pool_members(pool_id):
    """Get members of a cash pool."""
    return get_all("""
        SELECT m.*, a.bank_name, a.account_name, a.account_number, a.current_balance
        FROM treasury_cash_pool_members m
        JOIN finance_bank_accounts a ON m.bank_account_id = a.id
        WHERE m.pool_id = ? AND m.is_active = 1
    """, [pool_id])


def calculate_pool_totals(pool_id):
    """Calculate and update pool totals."""
    members = get_pool_members(pool_id)
    total = sum(m['current_balance'] or 0 for m in members)
    
    with get_db_context() as db:
        db.execute("UPDATE treasury_cash_pools SET total_balance = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                   [total, pool_id])
        db.commit()
    
    return total


# ============================================================================
# COLLECTION RISK SCORING
# ============================================================================

def _create_treasury_collection_scores():
    """Create collection risk scores table."""
    if not table_exists('treasury_collection_scores'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_collection_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER,
                    customer_name TEXT,
                    scoring_date DATE NOT NULL,
                    payment_history_score REAL DEFAULT 0,
                    overdue_behavior_score REAL DEFAULT 0,
                    collection_probability REAL DEFAULT 0,
                    risk_classification TEXT,
                    total_exposure REAL DEFAULT 0,
                    overdue_exposure REAL DEFAULT 0,
                    collection_agent_id INTEGER,
                    recommended_action TEXT,
                    next_follow_up DATE,
                    notes TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_score_customer ON treasury_collection_scores(customer_id)")
            db.execute("CREATE INDEX idx_score_date ON treasury_collection_scores(scoring_date)")
            db.execute("CREATE INDEX idx_score_risk ON treasury_collection_scores(risk_classification)")
            db.commit()


def _create_treasury_dunning_settings():
    """Create dunning settings table."""
    if not table_exists('treasury_dunning_settings'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_dunning_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dunning_level INTEGER NOT NULL,
                    level_name TEXT NOT NULL,
                    days_overdue INTEGER NOT NULL,
                    reminder_template TEXT,
                    escalation_action TEXT,
                    interest_rate REAL DEFAULT 0,
                    penalty_rate REAL DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_dunning_level ON treasury_dunning_settings(dunning_level)")
            db.commit()


def calculate_collection_score(customer_id, company_id):
    """Calculate collection risk score for a customer."""
    from finance_models import get_customer_invoices
    
    invoices = get_customer_invoices(company_id=company_id, customer_id=customer_id)
    
    if not invoices:
        return None
    
    total_exposure = sum(float(inv.get('total_amount', 0) or 0) for inv in invoices)
    overdue_exposure = sum(
        float(inv.get('total_amount', 0) or 0) - float(inv.get('amount_paid', 0) or 0)
        for inv in invoices
        if inv.get('due_date') and datetime.strptime(inv['due_date'], '%Y-%m-%d').date() < datetime.now().date()
    )
    
    overdue_count = sum(
        1 for inv in invoices
        if inv.get('due_date') and datetime.strptime(inv['due_date'], '%Y-%m-%d').date() < datetime.now().date()
    )
    total_count = len(invoices)
    
    payment_history_score = max(0, 100 - (overdue_count / max(total_count, 1) * 100))
    overdue_behavior_score = max(0, 100 - (overdue_exposure / max(total_exposure, 1) * 100))
    
    collection_probability = (payment_history_score * 0.4 + overdue_behavior_score * 0.6)
    
    if collection_probability >= 80:
        risk_classification = 'low'
    elif collection_probability >= 50:
        risk_classification = 'medium'
    else:
        risk_classification = 'high'
    
    return {
        'customer_id': customer_id,
        'scoring_date': datetime.now().date().isoformat(),
        'payment_history_score': payment_history_score,
        'overdue_behavior_score': overdue_behavior_score,
        'collection_probability': collection_probability,
        'risk_classification': risk_classification,
        'total_exposure': total_exposure,
        'overdue_exposure': overdue_exposure,
        'company_id': company_id
    }


def save_collection_score(score_data):
    """Save a collection score."""
    with get_db_context() as db:
        db.execute("""
            INSERT INTO treasury_collection_scores
            (customer_id, customer_name, scoring_date, payment_history_score, overdue_behavior_score,
             collection_probability, risk_classification, total_exposure, overdue_exposure,
             collection_agent_id, recommended_action, next_follow_up, notes, company_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            score_data.get('customer_id'),
            score_data.get('customer_name'),
            score_data.get('scoring_date'),
            score_data.get('payment_history_score', 0),
            score_data.get('overdue_behavior_score', 0),
            score_data.get('collection_probability', 0),
            score_data.get('risk_classification'),
            score_data.get('total_exposure', 0),
            score_data.get('overdue_exposure', 0),
            score_data.get('collection_agent_id'),
            score_data.get('recommended_action'),
            score_data.get('next_follow_up'),
            score_data.get('notes'),
            score_data.get('company_id')
        ))
        db.commit()


def get_collection_scores(company_id, risk_classification=None):
    """Get collection scores."""
    sql = "SELECT * FROM treasury_collection_scores WHERE company_id = ?"
    params = [company_id]
    
    if risk_classification:
        sql += " AND risk_classification = ?"
        params.append(risk_classification)
    
    sql += " ORDER BY collection_probability ASC"
    return get_all(sql, params)


def create_dunning_setting(setting_data):
    """Create dunning level setting."""
    with get_db_context() as db:
        db.execute("""
            INSERT INTO treasury_dunning_settings
            (dunning_level, level_name, days_overdue, reminder_template, escalation_action,
             interest_rate, penalty_rate, is_active, company_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            setting_data.get('dunning_level'),
            setting_data.get('level_name'),
            setting_data.get('days_overdue'),
            setting_data.get('reminder_template'),
            setting_data.get('escalation_action'),
            setting_data.get('interest_rate', 0),
            setting_data.get('penalty_rate', 0),
            setting_data.get('is_active', 1),
            setting_data.get('company_id')
        ))
        db.commit()


def get_dunning_settings(company_id):
    """Get dunning settings."""
    return get_all(
        "SELECT * FROM treasury_dunning_settings WHERE company_id = ? AND is_active = 1 ORDER BY dunning_level",
        [company_id]
    )


# ============================================================================
# NOTIFICATION PREFERENCES
# ============================================================================

def _create_treasury_notification_preferences():
    """Create notification preferences table."""
    if not table_exists('treasury_notification_preferences'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE treasury_notification_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    alert_type TEXT NOT NULL,
                    channel TEXT DEFAULT 'in_app',
                    is_enabled INTEGER DEFAULT 1,
                    threshold_amount REAL,
                    severity_filter TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_notif_user ON treasury_notification_preferences(user_id)")
            db.execute("CREATE INDEX idx_notif_type ON treasury_notification_preferences(alert_type)")
            db.commit()


def set_notification_preference(pref_data):
    """Set a notification preference."""
    with get_db_context() as db:
        db.execute("""
            INSERT INTO treasury_notification_preferences
            (user_id, alert_type, channel, is_enabled, threshold_amount, severity_filter, company_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, alert_type, channel) DO UPDATE SET
                is_enabled = excluded.is_enabled,
                threshold_amount = excluded.threshold_amount,
                severity_filter = excluded.severity_filter,
                updated_at = CURRENT_TIMESTAMP
        """, (
            pref_data.get('user_id'),
            pref_data.get('alert_type'),
            pref_data.get('channel', 'in_app'),
            pref_data.get('is_enabled', 1),
            pref_data.get('threshold_amount'),
            pref_data.get('severity_filter'),
            pref_data.get('company_id')
        ))
        db.commit()


def get_user_notification_prefs(user_id, company_id):
    """Get notification preferences for a user."""
    return get_all(
        "SELECT * FROM treasury_notification_preferences WHERE user_id = ? AND company_id = ?",
        [user_id, company_id]
    )


# ============================================================================
# ENHANCED INITIALIZATION
# ============================================================================

def initialize_treasury_schema_enhanced():
    """Initialize all treasury module tables including new ones."""
    initialize_treasury_schema()
    
    _create_treasury_bank_statements()
    _create_treasury_bank_statement_lines()
    _create_treasury_payment_runs()
    _create_treasury_payment_run_items()
    _create_treasury_fx_contracts()
    _create_treasury_counterparties()
    _create_treasury_bank_connections()
    _create_treasury_bank_charges()
    _create_treasury_cash_pools()
    _create_treasury_cash_pool_members()
    _create_treasury_notional_pooling()
    _create_treasury_collection_scores()
    _create_treasury_dunning_settings()
    _create_treasury_notification_preferences()
