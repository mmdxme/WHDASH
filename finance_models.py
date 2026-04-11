"""
Finance / Accounting Module - Data Models
========================================
Centralized finance module models covering:
- Chart of Accounts
- General Ledger & Journal Entries
- Accounts Receivable (Customer Invoices, Receipts, Credit Notes)
- Accounts Payable (Supplier Bills, Payments, Debit Notes)
- Asset Management & Depreciation
- Cost Centers
- Budget Management
- Tax Management (VAT)
- Fiscal Years & Periods

Author: Finance Module Implementation
"""

from database import get_db_context, get_one, get_all, row_to_dict, rows_to_list, table_exists, log_audit

# ============================================================================
# FINANCE MODULE INITIALIZATION
# ============================================================================

def initialize_finance_schema():
    """Initialize all finance module tables."""
    _create_account_categories()
    _create_chart_of_accounts()
    _create_fiscal_years_periods()
    _create_journals()
    _create_customer_invoices()
    _create_customer_receipts()
    _create_customer_credit_notes()
    _create_supplier_bills()
    _create_supplier_payments()
    _create_supplier_debit_notes()
    _create_assets()
    _create_asset_categories()
    _create_depreciation()
    _create_cost_centers()
    _create_budgets()
    _create_tax_codes()
    _create_tax_rules()
    # Note: posting_rules and finance_settings tables are created within _create_journals()


# ============================================================================
# ACCOUNT CATEGORIES
# ============================================================================

def _create_account_categories():
    """Create account categories table."""
    if not table_exists('finance_account_categories'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE finance_account_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    name_ar TEXT,
                    account_type TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    display_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_acc_cat_type ON finance_account_categories(account_type)")
            db.commit()
            
            # Seed default account categories
            default_categories = [
                ('1000', 'Assets', 'الأصول', 'ASSET', 1, 1),
                ('2000', 'Liabilities', 'الخصوم', 'LIABILITY', 1, 2),
                ('3000', 'Equity', 'حقوق الملكية', 'EQUITY', 1, 3),
                ('4000', 'Revenue', 'الإيرادات', 'REVENUE', 1, 4),
                ('5000', 'Cost of Goods Sold', 'تكلفة البضاعة المباعة', 'COGS', 1, 5),
                ('6000', 'Expenses', 'المصروفات', 'EXPENSE', 1, 6),
                ('7000', 'Other Income', 'دخل آخر', 'OTHER_INCOME', 1, 7),
                ('8000', 'Other Expenses', 'مصروفات أخرى', 'OTHER_EXPENSE', 1, 8),
            ]
            for code, name, name_ar, acc_type, is_active, order in default_categories:
                db.execute("""
                    INSERT OR IGNORE INTO finance_account_categories 
                    (code, name, name_ar, account_type, is_active, display_order)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (code, name, name_ar, acc_type, is_active, order))
            db.commit()


def get_account_categories():
    """Get all active account categories."""
    return get_all("""
        SELECT * FROM finance_account_categories 
        WHERE is_active = 1 
        ORDER BY display_order, code
    """)


def get_account_category_by_id(category_id):
    """Get account category by ID."""
    return get_one("SELECT * FROM finance_account_categories WHERE id = ?", (category_id,))


# ============================================================================
# CHART OF ACCOUNTS
# ============================================================================

def _create_chart_of_accounts():
    """Create chart of accounts table."""
    if not table_exists('finance_accounts'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE finance_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    name_ar TEXT,
                    description TEXT,
                    category_id INTEGER,
                    parent_id INTEGER,
                    account_type TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    is_posting_allowed INTEGER DEFAULT 1,
                    is_control_account INTEGER DEFAULT 0,
                    is_cost_center_allowed INTEGER DEFAULT 0,
                    tax_code_id INTEGER,
                    default_currency TEXT DEFAULT 'AED',
                    company_id INTEGER,
                    opening_balance REAL DEFAULT 0,
                    opening_balance_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES finance_account_categories(id),
                    FOREIGN KEY (parent_id) REFERENCES finance_accounts(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX idx_acc_code ON finance_accounts(code)")
            db.execute("CREATE INDEX idx_acc_category ON finance_accounts(category_id)")
            db.execute("CREATE INDEX idx_acc_parent ON finance_accounts(parent_id)")
            db.execute("CREATE INDEX idx_acc_type ON finance_accounts(account_type)")
            db.execute("CREATE INDEX idx_acc_company ON finance_accounts(company_id)")
            db.commit()


def get_accounts(company_id=None, active_only=True, category_id=None, parent_id=None):
    """
    Get chart of accounts with optional filters.
    
    Args:
        company_id: Filter by company
        active_only: Only active accounts
        category_id: Filter by category
        parent_id: Filter by parent account
    """
    sql = "SELECT * FROM finance_accounts WHERE 1=1"
    params = []
    
    if company_id:
        sql += " AND (company_id = ? OR company_id IS NULL)"
        params.append(company_id)
    
    if active_only:
        sql += " AND is_active = 1"
    
    if category_id:
        sql += " AND category_id = ?"
        params.append(category_id)
    
    if parent_id is not None:
        sql += " AND parent_id = ?"
        params.append(parent_id)
    
    sql += " ORDER BY code"
    
    return get_all(sql, params if params else None)


def get_account_by_id(account_id):
    """Get a single account by ID."""
    return get_one("SELECT * FROM finance_accounts WHERE id = ?", (account_id,))


def get_account_by_code(code):
    """Get a single account by code."""
    return get_one("SELECT * FROM finance_accounts WHERE code = ?", (code,))


def create_account(data):
    """Create a new account."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO finance_accounts (
                code, name, name_ar, description, category_id, parent_id,
                account_type, is_active, is_posting_allowed, is_control_account,
                is_cost_center_allowed, tax_code_id, default_currency, company_id,
                opening_balance, opening_balance_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('code'),
            data.get('name'),
            data.get('name_ar'),
            data.get('description'),
            data.get('category_id'),
            data.get('parent_id'),
            data.get('account_type'),
            data.get('is_active', 1),
            data.get('is_posting_allowed', 1),
            data.get('is_control_account', 0),
            data.get('is_cost_center_allowed', 0),
            data.get('tax_code_id'),
            data.get('default_currency', 'AED'),
            data.get('company_id'),
            data.get('opening_balance', 0),
            data.get('opening_balance_date')
        ))
        db.commit()
        return cursor.lastrowid


def update_account(account_id, data):
    """Update an existing account."""
    fields = []
    values = []
    
    updatable_fields = [
        'code', 'name', 'name_ar', 'description', 'category_id', 'parent_id',
        'account_type', 'is_active', 'is_posting_allowed', 'is_control_account',
        'is_cost_center_allowed', 'tax_code_id', 'default_currency', 'company_id',
        'opening_balance', 'opening_balance_date'
    ]
    
    for field in updatable_fields:
        if field in data:
            fields.append(f"{field} = ?")
            values.append(data[field])
    
    if not fields:
        return False
    
    fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(account_id)
    
    with get_db_context() as db:
        db.execute(f"""
            UPDATE finance_accounts 
            SET {', '.join(fields)}
            WHERE id = ?
        """, values)
        db.commit()
        return True


def get_account_balance(account_id, period_id=None, as_of_date=None):
    """
    Calculate account balance (debit - credit).
    
    Args:
        account_id: Account ID
        period_id: Optional fiscal period ID to filter by
        as_of_date: Optional date to calculate balance up to
    
    Returns:
        Dictionary with debit_total, credit_total, balance
    """
    sql = """
        SELECT 
            COALESCE(SUM(CASE WHEN debit > 0 THEN debit ELSE 0 END), 0) as debit_total,
            COALESCE(SUM(CASE WHEN credit > 0 THEN credit ELSE 0 END), 0) as credit_total
        FROM finance_journal_lines
        WHERE account_id = ?
    """
    params = [account_id]
    
    if period_id:
        sql += " AND journal_id IN (SELECT id FROM finance_journals WHERE period_id = ?)"
        params.append(period_id)
    
    if as_of_date:
        sql += " AND journal_id IN (SELECT id FROM finance_journals WHERE journal_date <= ?)"
        params.append(as_of_date)
    
    result = get_one(sql, params)
    
    if result:
        debit = float(result['debit_total'] or 0)
        credit = float(result['credit_total'] or 0)
        return {
            'debit_total': debit,
            'credit_total': credit,
            'balance': debit - credit
        }
    
    return {'debit_total': 0, 'credit_total': 0, 'balance': 0}


# ============================================================================
# FISCAL YEARS & PERIODS
# ============================================================================

def _create_fiscal_years_periods():
    """Create fiscal years and periods tables."""
    if not table_exists('finance_fiscal_years'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE finance_fiscal_years (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            db.execute("""
                CREATE TABLE finance_fiscal_periods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fiscal_year_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    period_number INTEGER NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    status TEXT DEFAULT 'Open',
                    period_type TEXT DEFAULT 'Month',
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (fiscal_year_id) REFERENCES finance_fiscal_years(id)
                )
            """)
            
            db.execute("CREATE INDEX idx_fy_company ON finance_fiscal_years(company_id)")
            db.execute("CREATE INDEX idx_fp_year ON finance_fiscal_periods(fiscal_year_id)")
            db.execute("CREATE INDEX idx_fp_status ON finance_fiscal_periods(status)")
            db.execute("CREATE INDEX idx_fp_dates ON finance_fiscal_periods(start_date, end_date)")
            db.commit()


def get_fiscal_years(company_id=None):
    """Get all fiscal years."""
    sql = "SELECT * FROM finance_fiscal_years WHERE 1=1"
    params = []
    
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    sql += " ORDER BY start_date DESC"
    return get_all(sql, params if params else None)


def get_fiscal_year_by_id(year_id):
    """Get fiscal year by ID."""
    return get_one("SELECT * FROM finance_fiscal_years WHERE id = ?", (year_id,))


def create_fiscal_year(data):
    """Create a new fiscal year and its periods."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO finance_fiscal_years (name, start_date, end_date, is_active, company_id)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data.get('name'),
            data.get('start_date'),
            data.get('end_date'),
            data.get('is_active', 1),
            data.get('company_id')
        ))
        year_id = cursor.lastrowid
        
        # Create monthly periods
        from datetime import datetime, timedelta
        start = datetime.strptime(data.get('start_date'), '%Y-%m-%d')
        end = datetime.strptime(data.get('end_date'), '%Y-%m-%d')
        
        period_num = 1
        current = start
        while current <= end:
            month_start = current
            month_end = (current + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            
            if month_end > end:
                month_end = end
            
            period_name = current.strftime('%B %Y')
            
            db.execute("""
                INSERT INTO finance_fiscal_periods 
                (fiscal_year_id, name, period_number, start_date, end_date, status, period_type, company_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (year_id, period_name, period_num, 
                  current.strftime('%Y-%m-%d'), month_end.strftime('%Y-%m-%d'),
                  'Open', 'Month', data.get('company_id')))
            
            current = current.replace(day=1) + timedelta(days=32)
            current = current.replace(day=1)
            period_num += 1
        
        db.commit()
        return year_id


def get_fiscal_periods(year_id=None, company_id=None, status=None):
    """Get fiscal periods with optional filters."""
    sql = "SELECT * FROM finance_fiscal_periods WHERE 1=1"
    params = []
    
    if year_id:
        sql += " AND fiscal_year_id = ?"
        params.append(year_id)
    
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    if status:
        sql += " AND status = ?"
        params.append(status)
    
    sql += " ORDER BY period_number"
    
    return get_all(sql, params if params else None)


def get_fiscal_period_by_id(period_id):
    """Get fiscal period by ID."""
    return get_one("SELECT * FROM finance_fiscal_periods WHERE id = ?", (period_id,))


def get_fiscal_period_by_date(date_str, company_id=None):
    """Get the fiscal period that contains a given date."""
    sql = """
        SELECT * FROM finance_fiscal_periods 
        WHERE start_date <= ? AND end_date >= ?
    """
    params = [date_str, date_str]
    
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    sql += " LIMIT 1"
    
    return get_one(sql, params)


def is_period_open(period_id):
    """Check if a fiscal period is open for posting."""
    period = get_fiscal_period_by_id(period_id)
    if period:
        return period.get('status') == 'Open'
    return False


def close_period(period_id):
    """Close a fiscal period."""
    with get_db_context() as db:
        db.execute("""
            UPDATE finance_fiscal_periods 
            SET status = 'Closed', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (period_id,))
        db.commit()


def reopen_period(period_id):
    """Reopen a closed fiscal period (requires special permission)."""
    with get_db_context() as db:
        db.execute("""
            UPDATE finance_fiscal_periods 
            SET status = 'Open', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (period_id,))
        db.commit()


# ============================================================================
# JOURNALS
# ============================================================================

def _create_journals():
    """Create journals and journal lines tables."""
    if not table_exists('finance_journals'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE finance_journals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    journal_number TEXT UNIQUE NOT NULL,
                    journal_type TEXT NOT NULL,
                    journal_date TEXT NOT NULL,
                    period_id INTEGER,
                    reference TEXT,
                    source_module TEXT,
                    source_id INTEGER,
                    description TEXT,
                    memo TEXT,
                    total_debit REAL DEFAULT 0,
                    total_credit REAL DEFAULT 0,
                    status TEXT DEFAULT 'Draft',
                    is_reversed INTEGER DEFAULT 0,
                    reversed_by_id INTEGER,
                    reversal_of_id INTEGER,
                    company_id INTEGER,
                    branch_id INTEGER,
                    warehouse_id INTEGER,
                    cost_center_id INTEGER,
                    created_by INTEGER,
                    approved_by INTEGER,
                    posted_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    posted_at TIMESTAMP,
                    FOREIGN KEY (period_id) REFERENCES finance_fiscal_periods(id),
                    FOREIGN KEY (cost_center_id) REFERENCES finance_cost_centers(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            
            db.execute("""
                CREATE TABLE finance_journal_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    journal_id INTEGER NOT NULL,
                    line_number INTEGER NOT NULL,
                    account_id INTEGER NOT NULL,
                    description TEXT,
                    debit REAL DEFAULT 0,
                    credit REAL DEFAULT 0,
                    tax_code_id INTEGER,
                    tax_amount REAL DEFAULT 0,
                    cost_center_id INTEGER,
                    reference TEXT,
                    due_date TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (journal_id) REFERENCES finance_journals(id),
                    FOREIGN KEY (account_id) REFERENCES finance_accounts(id),
                    FOREIGN KEY (tax_code_id) REFERENCES finance_tax_codes(id),
                    FOREIGN KEY (cost_center_id) REFERENCES finance_cost_centers(id)
                )
            """)
            
            db.execute("""
                CREATE TABLE finance_posting_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    source_module TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    debit_account_id INTEGER,
                    credit_account_id INTEGER,
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (debit_account_id) REFERENCES finance_accounts(id),
                    FOREIGN KEY (credit_account_id) REFERENCES finance_accounts(id)
                )
            """)
            
            db.execute("""
                CREATE TABLE finance_document_numbering (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_type TEXT NOT NULL,
                    prefix TEXT,
                    next_number INTEGER DEFAULT 1,
                    suffix TEXT,
                    padding INTEGER DEFAULT 5,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            db.execute("CREATE INDEX idx_journal_number ON finance_journals(journal_number)")
            db.execute("CREATE INDEX idx_journal_date ON finance_journals(journal_date)")
            db.execute("CREATE INDEX idx_journal_status ON finance_journals(status)")
            db.execute("CREATE INDEX idx_journal_period ON finance_journals(period_id)")
            db.execute("CREATE INDEX idx_journal_type ON finance_journals(journal_type)")
            db.execute("CREATE INDEX idx_journal_company ON finance_journals(company_id)")
            db.execute("CREATE INDEX idx_journal_source ON finance_journals(source_module, source_id)")
            db.execute("CREATE INDEX idx_jline_journal ON finance_journal_lines(journal_id)")
            db.execute("CREATE INDEX idx_jline_account ON finance_journal_lines(account_id)")
            db.commit()


def get_journals(company_id=None, status=None, journal_type=None, period_id=None,
                 start_date=None, end_date=None, limit=100, offset=0):
    """Get journals with filters."""
    sql = "SELECT * FROM finance_journals WHERE 1=1"
    params = []
    
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    if status:
        sql += " AND status = ?"
        params.append(status)
    
    if journal_type:
        sql += " AND journal_type = ?"
        params.append(journal_type)
    
    if period_id:
        sql += " AND period_id = ?"
        params.append(period_id)
    
    if start_date:
        sql += " AND journal_date >= ?"
        params.append(start_date)
    
    if end_date:
        sql += " AND journal_date <= ?"
        params.append(end_date)
    
    sql += " ORDER BY journal_date DESC, id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    return get_all(sql, params)


def get_journal_by_id(journal_id):
    """Get a journal by ID with its lines."""
    journal = get_one("SELECT * FROM finance_journals WHERE id = ?", (journal_id,))
    if journal:
        journal['lines'] = get_all("""
            SELECT jl.*, fa.code as account_code, fa.name as account_name
            FROM finance_journal_lines jl
            LEFT JOIN finance_accounts fa ON jl.account_id = fa.id
            WHERE jl.journal_id = ?
            ORDER BY jl.line_number
        """, (journal_id,))
    return journal


def get_journal_by_number(journal_number):
    """Get a journal by its number."""
    return get_one("SELECT * FROM finance_journals WHERE journal_number = ?", (journal_number,))


def get_next_journal_number(journal_type='General', company_id=None):
    """Generate next journal number."""
    prefix_map = {
        'General': 'JE',
        'Sales': 'SI',
        'Purchase': 'PI',
        'Payment': 'PMT',
        'Receipt': 'RCT',
        'Adjustment': 'ADJ',
        'Reversal': 'REV',
        'Depreciation': 'DEP',
        'Opening': 'OPG',
        'Closing': 'CLG',
    }
    
    prefix = prefix_map.get(journal_type, 'JE')
    
    # Get company prefix if company_id provided
    if company_id:
        company = get_one("SELECT code FROM companies WHERE id = ?", (company_id,))
        if company and company.get('code'):
            prefix = f"{company['code']}-{prefix}"
    
    # Get current max number for this prefix
    result = get_one("""
        SELECT MAX(CAST(SUBSTR(journal_number, LENGTH(?) + 1) AS INTEGER)) as max_num
        FROM finance_journals
        WHERE journal_number LIKE ? || '%'
    """, (prefix, prefix))
    
    next_num = (result.get('max_num') or 0) + 1
    return f"{prefix}-{next_num:05d}"


def create_journal(data, lines):
    """
    Create a new journal with lines.
    
    Args:
        data: Dictionary with journal header data
        lines: List of dictionaries with line data
    
    Returns:
        journal_id if successful, None if failed
    """
    # Validate debit = credit
    total_debit = sum(float(line.get('debit', 0)) for line in lines)
    total_credit = sum(float(line.get('credit', 0)) for line in lines)
    
    if abs(total_debit - total_credit) > 0.01:
        raise ValueError(f"Debit ({total_debit}) must equal Credit ({total_credit})")
    
    # Get period for the journal date
    period = get_fiscal_period_by_date(data.get('journal_date'), data.get('company_id'))
    if not period:
        raise ValueError(f"No fiscal period found for date {data.get('journal_date')}")
    
    if period.get('status') != 'Open':
        raise ValueError(f"Fiscal period {period.get('name')} is not open")
    
    with get_db_context() as db:
        journal_number = get_next_journal_number(
            data.get('journal_type', 'General'),
            data.get('company_id')
        )
        
        cursor = db.execute("""
            INSERT INTO finance_journals (
                journal_number, journal_type, journal_date, period_id, reference,
                source_module, source_id, description, memo, total_debit, total_credit,
                status, company_id, branch_id, warehouse_id, cost_center_id,
                created_by, approved_by, posted_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            journal_number,
            data.get('journal_type', 'General'),
            data.get('journal_date'),
            period.get('id'),
            data.get('reference'),
            data.get('source_module'),
            data.get('source_id'),
            data.get('description'),
            data.get('memo'),
            total_debit,
            total_credit,
            data.get('status', 'Draft'),
            data.get('company_id'),
            data.get('branch_id'),
            data.get('warehouse_id'),
            data.get('cost_center_id'),
            data.get('created_by'),
            data.get('approved_by'),
            data.get('posted_by')
        ))
        
        journal_id = cursor.lastrowid
        
        # Insert journal lines
        for idx, line in enumerate(lines, 1):
            db.execute("""
                INSERT INTO finance_journal_lines (
                    journal_id, line_number, account_id, description,
                    debit, credit, tax_code_id, tax_amount, cost_center_id,
                    reference, due_date, company_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                journal_id,
                idx,
                line.get('account_id'),
                line.get('description'),
                line.get('debit', 0),
                line.get('credit', 0),
                line.get('tax_code_id'),
                line.get('tax_amount', 0),
                line.get('cost_center_id'),
                line.get('reference'),
                line.get('due_date'),
                line.get('company_id')
            ))
        
        db.commit()
        return journal_id


def post_journal(journal_id, user_id):
    """
    Post a journal to the general ledger.
    
    Args:
        journal_id: Journal ID to post
        user_id: User posting the journal
    
    Returns:
        True if successful
    """
    journal = get_journal_by_id(journal_id)
    if not journal:
        raise ValueError("Journal not found")
    
    if journal.get('status') == 'Posted':
        raise ValueError("Journal is already posted")
    
    if journal.get('status') == 'Reversed':
        raise ValueError("Cannot post a reversed journal")
    
    # Check period is open
    period = get_fiscal_period_by_id(journal.get('period_id'))
    if period and period.get('status') != 'Open':
        raise ValueError(f"Period {period.get('name')} is closed")
    
    with get_db_context() as db:
        db.execute("""
            UPDATE finance_journals 
            SET status = 'Posted', 
                posted_by = ?, 
                posted_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, journal_id))
        db.commit()
    
    return True


def reverse_journal(journal_id, user_id, reversal_date=None, reversal_memo=None):
    """
    Reverse a posted journal.
    
    Args:
        journal_id: Journal ID to reverse
        user_id: User performing reversal
        reversal_date: Date for the reversal (defaults to today)
        reversal_memo: Optional memo for reversal
    
    Returns:
        New journal ID if successful
    """
    original = get_journal_by_id(journal_id)
    if not original:
        raise ValueError("Journal not found")
    
    if original.get('status') != 'Posted':
        raise ValueError("Only posted journals can be reversed")
    
    if original.get('is_reversed'):
        raise ValueError("Journal is already reversed")
    
    from datetime import datetime
    rev_date = reversal_date or datetime.now().strftime('%Y-%m-%d')
    
    # Create reversal journal
    reversal_lines = []
    for line in original.get('lines', []):
        reversal_lines.append({
            'account_id': line.get('account_id'),
            'description': line.get('description'),
            'debit': line.get('credit'),  # Swap debit/credit
            'credit': line.get('debit'),
            'tax_code_id': line.get('tax_code_id'),
            'tax_amount': line.get('tax_amount'),
            'cost_center_id': line.get('cost_center_id'),
            'reference': f"Reversal of {original.get('journal_number')}",
        })
    
    with get_db_context() as db:
        journal_number = get_next_journal_number('Reversal', original.get('company_id'))
        
        cursor = db.execute("""
            INSERT INTO finance_journals (
                journal_number, journal_type, journal_date, period_id, reference,
                source_module, source_id, description, memo, total_debit, total_credit,
                status, is_reversed, reversed_by_id, reversal_of_id,
                company_id, branch_id, warehouse_id, cost_center_id,
                created_by, approved_by, posted_by, posted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            journal_number,
            'Reversal',
            rev_date,
            original.get('period_id'),
            f"Reversal of {original.get('journal_number')}",
            original.get('source_module'),
            original.get('source_id'),
            f"Reversal: {original.get('description')}",
            reversal_memo or f"Reversal of JE# {original.get('journal_number')}",
            original.get('total_credit'),  # Same totals but debit/credit swapped
            original.get('total_debit'),
            'Posted',
            1,  # is_reversed flag
            user_id,  # reversed_by_id
            journal_id,  # reversal_of_id
            original.get('company_id'),
            original.get('branch_id'),
            original.get('warehouse_id'),
            original.get('cost_center_id'),
            user_id,
            user_id,
            user_id,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        reversal_id = cursor.lastrowid
        
        # Insert reversal lines
        for idx, line in enumerate(reversal_lines, 1):
            db.execute("""
                INSERT INTO finance_journal_lines (
                    journal_id, line_number, account_id, description,
                    debit, credit, tax_code_id, tax_amount, cost_center_id,
                    reference, company_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                reversal_id,
                idx,
                line.get('account_id'),
                line.get('description'),
                line.get('debit'),
                line.get('credit'),
                line.get('tax_code_id'),
                line.get('tax_amount'),
                line.get('cost_center_id'),
                line.get('reference'),
                line.get('company_id')
            ))
        
        # Mark original as reversed
        db.execute("""
            UPDATE finance_journals 
            SET status = 'Reversed', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (journal_id,))
        
        db.commit()
        return reversal_id


# ============================================================================
# CUSTOMER INVOICES (Accounts Receivable)
# ============================================================================

def _create_customer_invoices():
    """Create customer invoices table for AR tracking."""
    if not table_exists('finance_customer_invoices'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE finance_customer_invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_number TEXT UNIQUE NOT NULL,
                    customer_id INTEGER NOT NULL,
                    invoice_date TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    period_id INTEGER,
                    sales_order_id INTEGER,
                    delivery_id INTEGER,
                    currency TEXT DEFAULT 'AED',
                    exchange_rate REAL DEFAULT 1.0,
                    subtotal REAL DEFAULT 0,
                    discount_percent REAL DEFAULT 0,
                    discount_amount REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    tax_code_id INTEGER,
                    total_amount REAL DEFAULT 0,
                    amount_paid REAL DEFAULT 0,
                    amount_due REAL DEFAULT 0,
                    status TEXT DEFAULT 'Draft',
                    receivable_account_id INTEGER,
                    revenue_account_id INTEGER,
                    company_id INTEGER,
                    branch_id INTEGER,
                    warehouse_id INTEGER,
                    cost_center_id INTEGER,
                    payment_terms TEXT,
                    notes TEXT,
                    attachment_path TEXT,
                    created_by INTEGER,
                    approved_by INTEGER,
                    posted_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    posted_at TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(id),
                    FOREIGN KEY (period_id) REFERENCES finance_fiscal_periods(id),
                    FOREIGN KEY (tax_code_id) REFERENCES finance_tax_codes(id),
                    FOREIGN KEY (receivable_account_id) REFERENCES finance_accounts(id),
                    FOREIGN KEY (revenue_account_id) REFERENCES finance_accounts(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            
            db.execute("""
                CREATE TABLE finance_customer_invoice_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_id INTEGER NOT NULL,
                    line_number INTEGER NOT NULL,
                    product_id INTEGER,
                    description TEXT,
                    quantity REAL DEFAULT 1,
                    unit_price REAL DEFAULT 0,
                    discount_percent REAL DEFAULT 0,
                    discount_amount REAL DEFAULT 0,
                    tax_code_id INTEGER,
                    tax_percent REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    line_total REAL DEFAULT 0,
                    cost_center_id INTEGER,
                    FOREIGN KEY (invoice_id) REFERENCES finance_customer_invoices(id),
                    FOREIGN KEY (product_id) REFERENCES parts(id),
                    FOREIGN KEY (tax_code_id) REFERENCES finance_tax_codes(id),
                    FOREIGN KEY (cost_center_id) REFERENCES finance_cost_centers(id)
                )
            """)
            
            db.execute("CREATE INDEX idx_ar_inv_number ON finance_customer_invoices(invoice_number)")
            db.execute("CREATE INDEX idx_ar_inv_customer ON finance_customer_invoices(customer_id)")
            db.execute("CREATE INDEX idx_ar_inv_date ON finance_customer_invoices(invoice_date)")
            db.execute("CREATE INDEX idx_ar_inv_status ON finance_customer_invoices(status)")
            db.execute("CREATE INDEX idx_ar_inv_company ON finance_customer_invoices(company_id)")
            db.commit()


def get_customer_invoices(company_id=None, customer_id=None, status=None,
                          start_date=None, end_date=None, limit=100, offset=0):
    """Get customer invoices with filters."""
    sql = """
        SELECT ci.*, c.name as customer_name, c.id as customer_code
        FROM finance_customer_invoices ci
        LEFT JOIN customers c ON ci.customer_id = c.id
        WHERE 1=1
    """
    params = []
    
    if company_id:
        sql += " AND ci.company_id = ?"
        params.append(company_id)
    
    if customer_id:
        sql += " AND ci.customer_id = ?"
        params.append(customer_id)
    
    if status:
        sql += " AND ci.status = ?"
        params.append(status)
    
    if start_date:
        sql += " AND ci.invoice_date >= ?"
        params.append(start_date)
    
    if end_date:
        sql += " AND ci.invoice_date <= ?"
        params.append(end_date)
    
    sql += " ORDER BY ci.invoice_date DESC, ci.id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    return get_all(sql, params)


def get_customer_invoice_by_id(invoice_id):
    """Get a customer invoice by ID with lines."""
    invoice = get_one("""
        SELECT ci.*, c.name as customer_name, c.id as customer_code,
               c.credit_limit, c.payment_terms as customer_payment_terms
        FROM finance_customer_invoices ci
        LEFT JOIN customers c ON ci.customer_id = c.id
        WHERE ci.id = ?
    """, (invoice_id,))
    
    if invoice:
        invoice['lines'] = get_all("""
            SELECT cil.*, p.part_number, p.name as product_name
            FROM finance_customer_invoice_lines cil
            LEFT JOIN parts p ON cil.product_id = p.id
            WHERE cil.invoice_id = ?
            ORDER BY cil.line_number
        """, (invoice_id,))
    
    return invoice


def get_next_invoice_number(company_id=None):
    """Generate next invoice number."""
    prefix = 'INV'
    
    if company_id:
        company = get_one("SELECT code FROM companies WHERE id = ?", (company_id,))
        if company and company.get('code'):
            prefix = f"{company['code']}-INV"
    
    result = get_one("""
        SELECT MAX(CAST(SUBSTR(invoice_number, LENGTH(?) + 1) AS INTEGER)) as max_num
        FROM finance_customer_invoices
        WHERE invoice_number LIKE ? || '%'
    """, (prefix, prefix))
    
    next_num = (result.get('max_num') or 0) + 1
    return f"{prefix}-{next_num:05d}"


def create_customer_invoice(data, lines):
    """Create a customer invoice with lines."""
    subtotal = sum(float(line.get('line_total', 0)) for line in lines)
    tax_amount = sum(float(line.get('tax_amount', 0)) for line in lines)
    discount_amount = sum(float(line.get('discount_amount', 0)) for line in lines)
    total = subtotal + tax_amount - discount_amount
    
    with get_db_context() as db:
        invoice_number = get_next_invoice_number(data.get('company_id'))
        
        # Get fiscal period
        period = get_fiscal_period_by_date(data.get('invoice_date'), data.get('company_id'))
        period_id = period.get('id') if period else None
        
        cursor = db.execute("""
            INSERT INTO finance_customer_invoices (
                invoice_number, customer_id, invoice_date, due_date, period_id,
                sales_order_id, delivery_id, currency, exchange_rate,
                subtotal, discount_percent, discount_amount, tax_amount, tax_code_id,
                total_amount, amount_paid, amount_due, status,
                receivable_account_id, revenue_account_id,
                company_id, branch_id, warehouse_id, cost_center_id,
                payment_terms, notes, attachment_path, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_number,
            data.get('customer_id'),
            data.get('invoice_date'),
            data.get('due_date'),
            period_id,
            data.get('sales_order_id'),
            data.get('delivery_id'),
            data.get('currency', 'AED'),
            data.get('exchange_rate', 1.0),
            subtotal,
            data.get('discount_percent', 0),
            discount_amount,
            tax_amount,
            data.get('tax_code_id'),
            total,
            0,
            total,
            data.get('status', 'Draft'),
            data.get('receivable_account_id'),
            data.get('revenue_account_id'),
            data.get('company_id'),
            data.get('branch_id'),
            data.get('warehouse_id'),
            data.get('cost_center_id'),
            data.get('payment_terms'),
            data.get('notes'),
            data.get('attachment_path'),
            data.get('created_by')
        ))
        
        invoice_id = cursor.lastrowid
        
        # Insert lines
        for idx, line in enumerate(lines, 1):
            db.execute("""
                INSERT INTO finance_customer_invoice_lines (
                    invoice_id, line_number, product_id, description,
                    quantity, unit_price, discount_percent, discount_amount,
                    tax_code_id, tax_percent, tax_amount, line_total, cost_center_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_id,
                idx,
                line.get('product_id'),
                line.get('description'),
                line.get('quantity', 1),
                line.get('unit_price', 0),
                line.get('discount_percent', 0),
                line.get('discount_amount', 0),
                line.get('tax_code_id'),
                line.get('tax_percent', 0),
                line.get('tax_amount', 0),
                line.get('line_total', 0),
                line.get('cost_center_id')
            ))
        
        db.commit()
        return invoice_id


def post_customer_invoice(invoice_id, user_id):
    """
    Post a customer invoice - creates GL entries.
    
    Args:
        invoice_id: Invoice ID to post
        user_id: User posting
    
    Returns:
        journal_id if successful
    """
    invoice = get_customer_invoice_by_id(invoice_id)
    if not invoice:
        raise ValueError("Invoice not found")
    
    if invoice.get('status') != 'Draft':
        raise ValueError("Only draft invoices can be posted")
    
    # Get default AR and revenue accounts if not set
    receivable_acct = invoice.get('receivable_account_id')
    revenue_acct = invoice.get('revenue_account_id')
    
    if not receivable_acct:
        # Try to find default AR account
        ar_account = get_one("""
            SELECT id FROM finance_accounts 
            WHERE account_type = 'ASSET' AND is_control_account = 1 
            AND is_active = 1 LIMIT 1
        """)
        receivable_acct = ar_account.get('id') if ar_account else None
    
    if not revenue_acct:
        # Try to find default revenue account
        rev_account = get_one("""
            SELECT id FROM finance_accounts 
            WHERE account_type = 'REVENUE' AND is_active = 1 LIMIT 1
        """)
        revenue_acct = rev_account.get('id') if rev_account else None
    
    # Create journal entries
    journal_lines = []
    
    # Debit: Accounts Receivable (customer)
    journal_lines.append({
        'account_id': receivable_acct,
        'description': f"Invoice #{invoice.get('invoice_number')} - {invoice.get('customer_name')}",
        'debit': invoice.get('total_amount', 0),
        'credit': 0,
        'tax_code_id': invoice.get('tax_code_id'),
        'tax_amount': invoice.get('tax_amount', 0),
        'cost_center_id': invoice.get('cost_center_id')
    })
    
    # Credit: Revenue (for each line or total)
    journal_lines.append({
        'account_id': revenue_acct,
        'description': f"Invoice #{invoice.get('invoice_number')} - Revenue",
        'debit': 0,
        'credit': invoice.get('subtotal', 0),
        'tax_code_id': invoice.get('tax_code_id'),
        'tax_amount': 0,
        'cost_center_id': invoice.get('cost_center_id')
    })
    
    # Tax liability entry if tax
    if invoice.get('tax_amount', 0) > 0:
        tax_account = get_one("""
            SELECT id FROM finance_accounts 
            WHERE name LIKE '%VAT%' OR name LIKE '%Tax%' 
            AND account_type = 'LIABILITY' AND is_active = 1 LIMIT 1
        """)
        if tax_account:
            journal_lines.append({
                'account_id': tax_account.get('id'),
                'description': f"Output VAT - Invoice #{invoice.get('invoice_number')}",
                'debit': 0,
                'credit': invoice.get('tax_amount', 0),
                'tax_code_id': None,
                'tax_amount': 0,
                'cost_center_id': invoice.get('cost_center_id')
            })
    
    # Create journal
    journal_data = {
        'journal_type': 'Sales',
        'journal_date': invoice.get('invoice_date'),
        'reference': invoice.get('invoice_number'),
        'source_module': 'AR',
        'source_id': invoice_id,
        'description': f"Customer Invoice #{invoice.get('invoice_number')}",
        'memo': invoice.get('notes'),
        'company_id': invoice.get('company_id'),
        'branch_id': invoice.get('branch_id'),
        'warehouse_id': invoice.get('warehouse_id'),
        'cost_center_id': invoice.get('cost_center_id'),
        'created_by': user_id,
        'status': 'Posted',
        'posted_by': user_id
    }
    
    journal_id = create_journal(journal_data, journal_lines)
    
    # Update invoice status
    with get_db_context() as db:
        db.execute("""
            UPDATE finance_customer_invoices 
            SET status = 'Posted', posted_by = ?, posted_at = CURRENT_TIMESTAMP,
                receivable_account_id = ?, revenue_account_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, receivable_acct, revenue_acct, invoice_id))
        db.commit()
    
    return journal_id


# ============================================================================
# CUSTOMER RECEIPTS (Collections)
# ============================================================================

def _create_customer_receipts():
    """Create customer receipts table."""
    if not table_exists('finance_customer_receipts'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE finance_customer_receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_number TEXT UNIQUE NOT NULL,
                    customer_id INTEGER NOT NULL,
                    receipt_date TEXT NOT NULL,
                    period_id INTEGER,
                    invoice_id INTEGER,
                    currency TEXT DEFAULT 'AED',
                    exchange_rate REAL DEFAULT 1.0,
                    amount_received REAL DEFAULT 0,
                    discount_allowed REAL DEFAULT 0,
                    bank_charges REAL DEFAULT 0,
                    total_allocated REAL DEFAULT 0,
                    payment_method TEXT,
                    reference_number TEXT,
                    notes TEXT,
                    status TEXT DEFAULT 'Draft',
                    cash_account_id INTEGER,
                    bank_account_id INTEGER,
                    company_id INTEGER,
                    branch_id INTEGER,
                    created_by INTEGER,
                    posted_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    posted_at TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(id),
                    FOREIGN KEY (invoice_id) REFERENCES finance_customer_invoices(id),
                    FOREIGN KEY (period_id) REFERENCES finance_fiscal_periods(id),
                    FOREIGN KEY (cash_account_id) REFERENCES finance_accounts(id),
                    FOREIGN KEY (bank_account_id) REFERENCES finance_accounts(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            
            db.execute("""
                CREATE TABLE finance_customer_receipt_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_id INTEGER NOT NULL,
                    invoice_id INTEGER NOT NULL,
                    amount_allocated REAL DEFAULT 0,
                    discount_used REAL DEFAULT 0,
                    line_number INTEGER NOT NULL,
                    FOREIGN KEY (receipt_id) REFERENCES finance_customer_receipts(id),
                    FOREIGN KEY (invoice_id) REFERENCES finance_customer_invoices(id)
                )
            """)
            
            db.execute("CREATE INDEX idx_ar_recpt_number ON finance_customer_receipts(receipt_number)")
            db.execute("CREATE INDEX idx_ar_recpt_customer ON finance_customer_receipts(customer_id)")
            db.execute("CREATE INDEX idx_ar_recpt_date ON finance_customer_receipts(receipt_date)")
            db.commit()


def get_customer_receipts(company_id=None, customer_id=None, status=None, limit=100, offset=0):
    """Get customer receipts."""
    sql = """
        SELECT cr.*, c.name as customer_name, c.id as customer_code
        FROM finance_customer_receipts cr
        LEFT JOIN customers c ON cr.customer_id = c.id
        WHERE 1=1
    """
    params = []
    
    if company_id:
        sql += " AND cr.company_id = ?"
        params.append(company_id)
    
    if customer_id:
        sql += " AND cr.customer_id = ?"
        params.append(customer_id)
    
    if status:
        sql += " AND cr.status = ?"
        params.append(status)
    
    sql += " ORDER BY cr.receipt_date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    return get_all(sql, params)


def get_customer_receipt_by_id(receipt_id):
    """Get receipt by ID with allocations."""
    receipt = get_one("""
        SELECT cr.*, c.name as customer_name
        FROM finance_customer_receipts cr
        LEFT JOIN customers c ON cr.customer_id = c.id
        WHERE cr.id = ?
    """, (receipt_id,))
    
    if receipt:
        receipt['allocations'] = get_all("""
            SELECT crl.*, ci.invoice_number, ci.total_amount as invoice_total,
                   ci.amount_paid as invoice_paid, ci.amount_due as invoice_due
            FROM finance_customer_receipt_lines crl
            LEFT JOIN finance_customer_invoices ci ON crl.invoice_id = ci.id
            WHERE crl.receipt_id = ?
        """, (receipt_id,))
    
    return receipt


def get_next_receipt_number(company_id=None):
    """Generate next receipt number."""
    prefix = 'RCT'
    
    if company_id:
        company = get_one("SELECT code FROM companies WHERE id = ?", (company_id,))
        if company and company.get('code'):
            prefix = f"{company['code']}-RCT"
    
    result = get_one("""
        SELECT MAX(CAST(SUBSTR(receipt_number, LENGTH(?) + 1) AS INTEGER)) as max_num
        FROM finance_customer_receipts
        WHERE receipt_number LIKE ? || '%'
    """, (prefix, prefix))
    
    next_num = (result.get('max_num') or 0) + 1
    return f"{prefix}-{next_num:05d}"


def create_customer_receipt(data, allocations):
    """Create a customer receipt with allocations to invoices."""
    total_allocated = sum(float(alloc.get('amount_allocated', 0)) for alloc in allocations)
    
    with get_db_context() as db:
        receipt_number = get_next_receipt_number(data.get('company_id'))
        
        period = get_fiscal_period_by_date(data.get('receipt_date'), data.get('company_id'))
        period_id = period.get('id') if period else None
        
        cursor = db.execute("""
            INSERT INTO finance_customer_receipts (
                receipt_number, customer_id, receipt_date, period_id, invoice_id,
                currency, exchange_rate, amount_received, discount_allowed,
                bank_charges, total_allocated, payment_method, reference_number,
                notes, status, cash_account_id, bank_account_id,
                company_id, branch_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            receipt_number,
            data.get('customer_id'),
            data.get('receipt_date'),
            period_id,
            data.get('invoice_id'),
            data.get('currency', 'AED'),
            data.get('exchange_rate', 1.0),
            data.get('amount_received', 0),
            data.get('discount_allowed', 0),
            data.get('bank_charges', 0),
            total_allocated,
            data.get('payment_method'),
            data.get('reference_number'),
            data.get('notes'),
            data.get('status', 'Draft'),
            data.get('cash_account_id'),
            data.get('bank_account_id'),
            data.get('company_id'),
            data.get('branch_id'),
            data.get('created_by')
        ))
        
        receipt_id = cursor.lastrowid
        
        # Insert allocation lines
        for idx, alloc in enumerate(allocations, 1):
            db.execute("""
                INSERT INTO finance_customer_receipt_lines (
                    receipt_id, invoice_id, amount_allocated, discount_used, line_number
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                receipt_id,
                alloc.get('invoice_id'),
                alloc.get('amount_allocated', 0),
                alloc.get('discount_used', 0),
                idx
            ))
        
        db.commit()
        return receipt_id


def post_customer_receipt(receipt_id, user_id):
    """Post a customer receipt - creates GL entries and updates invoice balances."""
    receipt = get_customer_receipt_by_id(receipt_id)
    if not receipt:
        raise ValueError("Receipt not found")
    
    if receipt.get('status') != 'Draft':
        raise ValueError("Only draft receipts can be posted")
    
    # Get bank/cash account
    bank_acct = receipt.get('bank_account_id') or receipt.get('cash_account_id')
    if not bank_acct:
        bank_acct = get_one("""
            SELECT id FROM finance_accounts 
            WHERE account_type = 'ASSET' AND name LIKE '%Bank%' 
            AND is_active = 1 LIMIT 1
        """)
        bank_acct = bank_acct.get('id') if bank_acct else None
    
    # Get AR account
    ar_acct = get_one("""
        SELECT id FROM finance_accounts 
        WHERE account_type = 'ASSET' AND is_control_account = 1 
        AND is_active = 1 LIMIT 1
    """)
    ar_acct = ar_acct.get('id') if ar_acct else None
    
    # Create journal
    journal_lines = []
    
    # Debit: Bank/Cash
    journal_lines.append({
        'account_id': bank_acct,
        'description': f"Receipt #{receipt.get('receipt_number')} from {receipt.get('customer_name')}",
        'debit': receipt.get('amount_received', 0),
        'credit': 0
    })
    
    # Credit: AR (for amount allocated to invoices)
    if receipt.get('total_allocated', 0) > 0:
        journal_lines.append({
            'account_id': ar_acct,
            'description': f"Collection from {receipt.get('customer_name')}",
            'debit': 0,
            'credit': receipt.get('total_allocated', 0)
        })
    
    # Credit: Discount Allowed (if any)
    if receipt.get('discount_allowed', 0) > 0:
        disc_acct = get_one("""
            SELECT id FROM finance_accounts 
            WHERE account_type = 'EXPENSE' AND name LIKE '%Discount%' 
            AND is_active = 1 LIMIT 1
        """)
        if disc_acct:
            journal_lines.append({
                'account_id': disc_acct.get('id'),
                'description': f"Discount allowed - {receipt.get('customer_name')}",
                'debit': 0,
                'credit': receipt.get('discount_allowed', 0)
            })
    
    journal_data = {
        'journal_type': 'Receipt',
        'journal_date': receipt.get('receipt_date'),
        'reference': receipt.get('receipt_number'),
        'source_module': 'AR',
        'source_id': receipt_id,
        'description': f"Customer Receipt #{receipt.get('receipt_number')}",
        'memo': receipt.get('notes'),
        'company_id': receipt.get('company_id'),
        'branch_id': receipt.get('branch_id'),
        'created_by': user_id,
        'status': 'Posted',
        'posted_by': user_id
    }
    
    journal_id = create_journal(journal_data, journal_lines)
    
    # Update invoice balances
    for alloc in receipt.get('allocations', []):
        with get_db_context() as db:
            # Update invoice amount_paid and amount_due
            db.execute("""
                UPDATE finance_customer_invoices 
                SET amount_paid = amount_paid + ?,
                    amount_due = amount_due - ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (alloc.get('amount_allocated', 0), alloc.get('amount_allocated', 0), alloc.get('invoice_id')))
            
            # Update receipt status
            db.execute("""
                UPDATE finance_customer_receipts 
                SET status = 'Posted', posted_by = ?, posted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (user_id, receipt_id))
            db.commit()
    
    return journal_id


# ============================================================================
# CUSTOMER CREDIT NOTES
# ============================================================================

def _create_customer_credit_notes():
    """Create customer credit notes table."""
    if not table_exists('finance_customer_credit_notes'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE finance_customer_credit_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    credit_note_number TEXT UNIQUE NOT NULL,
                    customer_id INTEGER NOT NULL,
                    invoice_id INTEGER,
                    credit_note_date TEXT NOT NULL,
                    period_id INTEGER,
                    reason TEXT,
                    currency TEXT DEFAULT 'AED',
                    subtotal REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    total_amount REAL DEFAULT 0,
                    amount_applied REAL DEFAULT 0,
                    status TEXT DEFAULT 'Draft',
                    company_id INTEGER,
                    branch_id INTEGER,
                    created_by INTEGER,
                    posted_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (customer_id) REFERENCES customers(id),
                    FOREIGN KEY (invoice_id) REFERENCES finance_customer_invoices(id),
                    FOREIGN KEY (period_id) REFERENCES finance_fiscal_periods(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            
            db.execute("""
                CREATE TABLE finance_customer_credit_note_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    credit_note_id INTEGER NOT NULL,
                    line_number INTEGER NOT NULL,
                    description TEXT,
                    quantity REAL DEFAULT 1,
                    unit_price REAL DEFAULT 0,
                    tax_code_id INTEGER,
                    tax_amount REAL DEFAULT 0,
                    line_total REAL DEFAULT 0,
                    FOREIGN KEY (credit_note_id) REFERENCES finance_customer_credit_notes(id)
                )
            """)
            
            db.execute("CREATE INDEX idx_ar_cn_number ON finance_customer_credit_notes(credit_note_number)")
            db.execute("CREATE INDEX idx_ar_cn_customer ON finance_customer_credit_notes(customer_id)")
            db.commit()


# ============================================================================
# SUPPLIER BILLS (Accounts Payable)
# ============================================================================

def _create_supplier_bills():
    """Create supplier bills table for AP tracking."""
    if not table_exists('finance_supplier_bills'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE finance_supplier_bills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bill_number TEXT UNIQUE NOT NULL,
                    supplier_id INTEGER NOT NULL,
                    bill_date TEXT NOT NULL,
                    due_date TEXT NOT NULL,
                    period_id INTEGER,
                    purchase_order_id INTEGER,
                    currency TEXT DEFAULT 'AED',
                    exchange_rate REAL DEFAULT 1.0,
                    subtotal REAL DEFAULT 0,
                    discount_percent REAL DEFAULT 0,
                    discount_amount REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    tax_code_id INTEGER,
                    total_amount REAL DEFAULT 0,
                    amount_paid REAL DEFAULT 0,
                    amount_due REAL DEFAULT 0,
                    status TEXT DEFAULT 'Draft',
                    payable_account_id INTEGER,
                    expense_account_id INTEGER,
                    company_id INTEGER,
                    branch_id INTEGER,
                    warehouse_id INTEGER,
                    cost_center_id INTEGER,
                    payment_terms TEXT,
                    notes TEXT,
                    attachment_path TEXT,
                    created_by INTEGER,
                    approved_by INTEGER,
                    posted_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    posted_at TIMESTAMP,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                    FOREIGN KEY (period_id) REFERENCES finance_fiscal_periods(id),
                    FOREIGN KEY (tax_code_id) REFERENCES finance_tax_codes(id),
                    FOREIGN KEY (payable_account_id) REFERENCES finance_accounts(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            
            db.execute("""
                CREATE TABLE finance_supplier_bill_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bill_id INTEGER NOT NULL,
                    line_number INTEGER NOT NULL,
                    product_id INTEGER,
                    description TEXT,
                    quantity REAL DEFAULT 1,
                    unit_price REAL DEFAULT 0,
                    discount_percent REAL DEFAULT 0,
                    discount_amount REAL DEFAULT 0,
                    tax_code_id INTEGER,
                    tax_percent REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    line_total REAL DEFAULT 0,
                    cost_center_id INTEGER,
                    FOREIGN KEY (bill_id) REFERENCES finance_supplier_bills(id),
                    FOREIGN KEY (product_id) REFERENCES parts(id),
                    FOREIGN KEY (tax_code_id) REFERENCES finance_tax_codes(id)
                )
            """)
            
            db.execute("CREATE INDEX idx_ap_bill_number ON finance_supplier_bills(bill_number)")
            db.execute("CREATE INDEX idx_ap_bill_supplier ON finance_supplier_bills(supplier_id)")
            db.execute("CREATE INDEX idx_ap_bill_date ON finance_supplier_bills(bill_date)")
            db.execute("CREATE INDEX idx_ap_bill_status ON finance_supplier_bills(status)")
            db.commit()


def get_supplier_bills(company_id=None, supplier_id=None, status=None,
                       start_date=None, end_date=None, limit=100, offset=0):
    """Get supplier bills with filters."""
    sql = """
        SELECT sb.*, s.name as supplier_name, s.code as supplier_code
        FROM finance_supplier_bills sb
        LEFT JOIN suppliers s ON sb.supplier_id = s.id
        WHERE 1=1
    """
    params = []
    
    if company_id:
        sql += " AND sb.company_id = ?"
        params.append(company_id)
    
    if supplier_id:
        sql += " AND sb.supplier_id = ?"
        params.append(supplier_id)
    
    if status:
        sql += " AND sb.status = ?"
        params.append(status)
    
    if start_date:
        sql += " AND sb.bill_date >= ?"
        params.append(start_date)
    
    if end_date:
        sql += " AND sb.bill_date <= ?"
        params.append(end_date)
    
    sql += " ORDER BY sb.bill_date DESC, sb.id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    return get_all(sql, params)


def get_supplier_bill_by_id(bill_id):
    """Get supplier bill by ID with lines."""
    bill = get_one("""
        SELECT sb.*, s.name as supplier_name, s.code as supplier_code,
               s.payment_terms as supplier_payment_terms
        FROM finance_supplier_bills sb
        LEFT JOIN suppliers s ON sb.supplier_id = s.id
        WHERE sb.id = ?
    """, (bill_id,))
    
    if bill:
        bill['lines'] = get_all("""
            SELECT sbl.*, p.part_number, p.name as product_name
            FROM finance_supplier_bill_lines sbl
            LEFT JOIN parts p ON sbl.product_id = p.id
            WHERE sbl.bill_id = ?
            ORDER BY sbl.line_number
        """, (bill_id,))
    
    return bill


def get_next_bill_number(company_id=None):
    """Generate next bill number."""
    prefix = 'BILL'
    
    if company_id:
        company = get_one("SELECT code FROM companies WHERE id = ?", (company_id,))
        if company and company.get('code'):
            prefix = f"{company['code']}-BILL"
    
    result = get_one("""
        SELECT MAX(CAST(SUBSTR(bill_number, LENGTH(?) + 1) AS INTEGER)) as max_num
        FROM finance_supplier_bills
        WHERE bill_number LIKE ? || '%'
    """, (prefix, prefix))
    
    next_num = (result.get('max_num') or 0) + 1
    return f"{prefix}-{next_num:05d}"


def create_supplier_bill(data, lines):
    """Create a supplier bill with lines."""
    subtotal = sum(float(line.get('line_total', 0)) for line in lines)
    tax_amount = sum(float(line.get('tax_amount', 0)) for line in lines)
    discount_amount = sum(float(line.get('discount_amount', 0)) for line in lines)
    total = subtotal + tax_amount - discount_amount
    
    with get_db_context() as db:
        bill_number = get_next_bill_number(data.get('company_id'))
        
        period = get_fiscal_period_by_date(data.get('bill_date'), data.get('company_id'))
        period_id = period.get('id') if period else None
        
        cursor = db.execute("""
            INSERT INTO finance_supplier_bills (
                bill_number, supplier_id, bill_date, due_date, period_id,
                purchase_order_id, currency, exchange_rate,
                subtotal, discount_percent, discount_amount, tax_amount, tax_code_id,
                total_amount, amount_paid, amount_due, status,
                payable_account_id, expense_account_id,
                company_id, branch_id, warehouse_id, cost_center_id,
                payment_terms, notes, attachment_path, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            bill_number,
            data.get('supplier_id'),
            data.get('bill_date'),
            data.get('due_date'),
            period_id,
            data.get('purchase_order_id'),
            data.get('currency', 'AED'),
            data.get('exchange_rate', 1.0),
            subtotal,
            data.get('discount_percent', 0),
            discount_amount,
            tax_amount,
            data.get('tax_code_id'),
            total,
            0,
            total,
            data.get('status', 'Draft'),
            data.get('payable_account_id'),
            data.get('expense_account_id'),
            data.get('company_id'),
            data.get('branch_id'),
            data.get('warehouse_id'),
            data.get('cost_center_id'),
            data.get('payment_terms'),
            data.get('notes'),
            data.get('attachment_path'),
            data.get('created_by')
        ))
        
        bill_id = cursor.lastrowid
        
        for idx, line in enumerate(lines, 1):
            db.execute("""
                INSERT INTO finance_supplier_bill_lines (
                    bill_id, line_number, product_id, description,
                    quantity, unit_price, discount_percent, discount_amount,
                    tax_code_id, tax_percent, tax_amount, line_total, cost_center_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                bill_id, idx, line.get('product_id'), line.get('description'),
                line.get('quantity', 1), line.get('unit_price', 0),
                line.get('discount_percent', 0), line.get('discount_amount', 0),
                line.get('tax_code_id'), line.get('tax_percent', 0),
                line.get('tax_amount', 0), line.get('line_total', 0),
                line.get('cost_center_id')
            ))
        
        db.commit()
        return bill_id


def post_supplier_bill(bill_id, user_id):
    """Post a supplier bill - creates GL entries."""
    bill = get_supplier_bill_by_id(bill_id)
    if not bill:
        raise ValueError("Bill not found")
    
    if bill.get('status') != 'Draft':
        raise ValueError("Only draft bills can be posted")
    
    payable_acct = bill.get('payable_account_id')
    expense_acct = bill.get('expense_account_id')
    
    if not payable_acct:
        ap_account = get_one("""
            SELECT id FROM finance_accounts 
            WHERE account_type = 'LIABILITY' AND is_control_account = 1 
            AND is_active = 1 LIMIT 1
        """)
        payable_acct = ap_account.get('id') if ap_account else None
    
    if not expense_acct:
        exp_account = get_one("""
            SELECT id FROM finance_accounts 
            WHERE account_type = 'EXPENSE' AND is_active = 1 LIMIT 1
        """)
        expense_acct = exp_account.get('id') if exp_account else None
    
    journal_lines = []
    
    # Debit: Expense
    journal_lines.append({
        'account_id': expense_acct,
        'description': f"Bill #{bill.get('bill_number')} from {bill.get('supplier_name')}",
        'debit': bill.get('subtotal', 0),
        'credit': 0,
        'cost_center_id': bill.get('cost_center_id')
    })
    
    # Credit: Accounts Payable
    journal_lines.append({
        'account_id': payable_acct,
        'description': f"Bill #{bill.get('bill_number')} - {bill.get('supplier_name')}",
        'debit': 0,
        'credit': bill.get('total_amount', 0),
        'cost_center_id': bill.get('cost_center_id')
    })
    
    journal_data = {
        'journal_type': 'Purchase',
        'journal_date': bill.get('bill_date'),
        'reference': bill.get('bill_number'),
        'source_module': 'AP',
        'source_id': bill_id,
        'description': f"Supplier Bill #{bill.get('bill_number')}",
        'memo': bill.get('notes'),
        'company_id': bill.get('company_id'),
        'branch_id': bill.get('branch_id'),
        'cost_center_id': bill.get('cost_center_id'),
        'created_by': user_id,
        'status': 'Posted',
        'posted_by': user_id
    }
    
    journal_id = create_journal(journal_data, journal_lines)
    
    with get_db_context() as db:
        db.execute("""
            UPDATE finance_supplier_bills 
            SET status = 'Posted', posted_by = ?, posted_at = CURRENT_TIMESTAMP,
                payable_account_id = ?, expense_account_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, payable_acct, expense_acct, bill_id))
        db.commit()
    
    return journal_id


# ============================================================================
# SUPPLIER PAYMENTS
# ============================================================================

def _create_supplier_payments():
    """Create supplier payments table."""
    if not table_exists('finance_supplier_payments'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE finance_supplier_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_number TEXT UNIQUE NOT NULL,
                    supplier_id INTEGER NOT NULL,
                    payment_date TEXT NOT NULL,
                    period_id INTEGER,
                    bill_id INTEGER,
                    currency TEXT DEFAULT 'AED',
                    exchange_rate REAL DEFAULT 1.0,
                    amount_paid REAL DEFAULT 0,
                    discount_received REAL DEFAULT 0,
                    bank_charges REAL DEFAULT 0,
                    total_allocated REAL DEFAULT 0,
                    payment_method TEXT,
                    reference_number TEXT,
                    notes TEXT,
                    status TEXT DEFAULT 'Draft',
                    cash_account_id INTEGER,
                    bank_account_id INTEGER,
                    company_id INTEGER,
                    branch_id INTEGER,
                    created_by INTEGER,
                    posted_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    posted_at TIMESTAMP,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                    FOREIGN KEY (bill_id) REFERENCES finance_supplier_bills(id),
                    FOREIGN KEY (period_id) REFERENCES finance_fiscal_periods(id),
                    FOREIGN KEY (cash_account_id) REFERENCES finance_accounts(id),
                    FOREIGN KEY (bank_account_id) REFERENCES finance_accounts(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            
            db.execute("""
                CREATE TABLE finance_supplier_payment_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_id INTEGER NOT NULL,
                    bill_id INTEGER NOT NULL,
                    amount_allocated REAL DEFAULT 0,
                    discount_used REAL DEFAULT 0,
                    line_number INTEGER NOT NULL,
                    FOREIGN KEY (payment_id) REFERENCES finance_supplier_payments(id),
                    FOREIGN KEY (bill_id) REFERENCES finance_supplier_bills(id)
                )
            """)
            
            db.execute("CREATE INDEX idx_ap_pmt_number ON finance_supplier_payments(payment_number)")
            db.execute("CREATE INDEX idx_ap_pmt_supplier ON finance_supplier_payments(supplier_id)")
            db.execute("CREATE INDEX idx_ap_pmt_date ON finance_supplier_payments(payment_date)")
            db.commit()


def get_supplier_payments(company_id=None, supplier_id=None, status=None, limit=100, offset=0):
    """Get supplier payments."""
    sql = """
        SELECT sp.*, s.name as supplier_name, s.code as supplier_code
        FROM finance_supplier_payments sp
        LEFT JOIN suppliers s ON sp.supplier_id = s.id
        WHERE 1=1
    """
    params = []
    
    if company_id:
        sql += " AND sp.company_id = ?"
        params.append(company_id)
    
    if supplier_id:
        sql += " AND sp.supplier_id = ?"
        params.append(supplier_id)
    
    if status:
        sql += " AND sp.status = ?"
        params.append(status)
    
    sql += " ORDER BY sp.payment_date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    return get_all(sql, params)


def get_supplier_payment_by_id(payment_id):
    """Get payment by ID with allocations."""
    payment = get_one("""
        SELECT sp.*, s.name as supplier_name
        FROM finance_supplier_payments sp
        LEFT JOIN suppliers s ON sp.supplier_id = s.id
        WHERE sp.id = ?
    """, (payment_id,))
    
    if payment:
        payment['allocations'] = get_all("""
            SELECT spl.*, sb.bill_number, sb.total_amount as bill_total,
                   sb.amount_paid as bill_paid, sb.amount_due as bill_due
            FROM finance_supplier_payment_lines spl
            LEFT JOIN finance_supplier_bills sb ON spl.bill_id = sb.id
            WHERE spl.payment_id = ?
        """, (payment_id,))
    
    return payment


def get_next_payment_number(company_id=None):
    """Generate next payment number."""
    prefix = 'PMT'
    
    if company_id:
        company = get_one("SELECT code FROM companies WHERE id = ?", (company_id,))
        if company and company.get('code'):
            prefix = f"{company['code']}-PMT"
    
    result = get_one("""
        SELECT MAX(CAST(SUBSTR(payment_number, LENGTH(?) + 1) AS INTEGER)) as max_num
        FROM finance_supplier_payments
        WHERE payment_number LIKE ? || '%'
    """, (prefix, prefix))
    
    next_num = (result.get('max_num') or 0) + 1
    return f"{prefix}-{next_num:05d}"


def create_supplier_payment(data, allocations):
    """Create a supplier payment with allocations."""
    total_allocated = sum(float(alloc.get('amount_allocated', 0)) for alloc in allocations)
    
    with get_db_context() as db:
        payment_number = get_next_payment_number(data.get('company_id'))
        
        period = get_fiscal_period_by_date(data.get('payment_date'), data.get('company_id'))
        period_id = period.get('id') if period else None
        
        cursor = db.execute("""
            INSERT INTO finance_supplier_payments (
                payment_number, supplier_id, payment_date, period_id, bill_id,
                currency, exchange_rate, amount_paid, discount_received,
                bank_charges, total_allocated, payment_method, reference_number,
                notes, status, cash_account_id, bank_account_id,
                company_id, branch_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            payment_number,
            data.get('supplier_id'),
            data.get('payment_date'),
            period_id,
            data.get('bill_id'),
            data.get('currency', 'AED'),
            data.get('exchange_rate', 1.0),
            data.get('amount_paid', 0),
            data.get('discount_received', 0),
            data.get('bank_charges', 0),
            total_allocated,
            data.get('payment_method'),
            data.get('reference_number'),
            data.get('notes'),
            data.get('status', 'Draft'),
            data.get('cash_account_id'),
            data.get('bank_account_id'),
            data.get('company_id'),
            data.get('branch_id'),
            data.get('created_by')
        ))
        
        payment_id = cursor.lastrowid
        
        for idx, alloc in enumerate(allocations, 1):
            db.execute("""
                INSERT INTO finance_supplier_payment_lines (
                    payment_id, bill_id, amount_allocated, discount_used, line_number
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                payment_id,
                alloc.get('bill_id'),
                alloc.get('amount_allocated', 0),
                alloc.get('discount_used', 0),
                idx
            ))
        
        db.commit()
        return payment_id


def post_supplier_payment(payment_id, user_id):
    """Post a supplier payment - creates GL entries."""
    payment = get_supplier_payment_by_id(payment_id)
    if not payment:
        raise ValueError("Payment not found")
    
    if payment.get('status') != 'Draft':
        raise ValueError("Only draft payments can be posted")
    
    bank_acct = payment.get('bank_account_id') or payment.get('cash_account_id')
    if not bank_acct:
        bank_acct = get_one("""
            SELECT id FROM finance_accounts 
            WHERE account_type = 'ASSET' AND name LIKE '%Bank%' 
            AND is_active = 1 LIMIT 1
        """)
        bank_acct = bank_acct.get('id') if bank_acct else None
    
    ap_acct = get_one("""
        SELECT id FROM finance_accounts 
        WHERE account_type = 'LIABILITY' AND is_control_account = 1 
        AND is_active = 1 LIMIT 1
    """)
    ap_acct = ap_acct.get('id') if ap_acct else None
    
    journal_lines = []
    
    # Debit: AP
    if payment.get('total_allocated', 0) > 0:
        journal_lines.append({
            'account_id': ap_acct,
            'description': f"Payment to {payment.get('supplier_name')}",
            'debit': payment.get('total_allocated', 0),
            'credit': 0
        })
    
    # Credit: Bank/Cash
    journal_lines.append({
        'account_id': bank_acct,
        'description': f"Payment #{payment.get('payment_number')} to {payment.get('supplier_name')}",
        'debit': 0,
        'credit': payment.get('amount_paid', 0)
    })
    
    # Debit: Discount Received (if any)
    if payment.get('discount_received', 0) > 0:
        disc_acct = get_one("""
            SELECT id FROM finance_accounts 
            WHERE account_type = 'OTHER_INCOME' AND name LIKE '%Discount%' 
            AND is_active = 1 LIMIT 1
        """)
        if disc_acct:
            journal_lines.append({
                'account_id': disc_acct.get('id'),
                'description': f"Discount received - {payment.get('supplier_name')}",
                'debit': payment.get('discount_received', 0),
                'credit': 0
            })
    
    journal_data = {
        'journal_type': 'Payment',
        'journal_date': payment.get('payment_date'),
        'reference': payment.get('payment_number'),
        'source_module': 'AP',
        'source_id': payment_id,
        'description': f"Supplier Payment #{payment.get('payment_number')}",
        'memo': payment.get('notes'),
        'company_id': payment.get('company_id'),
        'branch_id': payment.get('branch_id'),
        'created_by': user_id,
        'status': 'Posted',
        'posted_by': user_id
    }
    
    journal_id = create_journal(journal_data, journal_lines)
    
    for alloc in payment.get('allocations', []):
        with get_db_context() as db:
            db.execute("""
                UPDATE finance_supplier_bills 
                SET amount_paid = amount_paid + ?,
                    amount_due = amount_due - ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (alloc.get('amount_allocated', 0), alloc.get('amount_allocated', 0), alloc.get('bill_id')))
            
            db.execute("""
                UPDATE finance_supplier_payments 
                SET status = 'Posted', posted_by = ?, posted_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (user_id, payment_id))
            db.commit()
    
    return journal_id


# ============================================================================
# SUPPLIER DEBIT NOTES
# ============================================================================

def _create_supplier_debit_notes():
    """Create supplier debit notes table."""
    if not table_exists('finance_supplier_debit_notes'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE finance_supplier_debit_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    debit_note_number TEXT UNIQUE NOT NULL,
                    supplier_id INTEGER NOT NULL,
                    bill_id INTEGER,
                    debit_note_date TEXT NOT NULL,
                    period_id INTEGER,
                    reason TEXT,
                    currency TEXT DEFAULT 'AED',
                    subtotal REAL DEFAULT 0,
                    tax_amount REAL DEFAULT 0,
                    total_amount REAL DEFAULT 0,
                    amount_applied REAL DEFAULT 0,
                    status TEXT DEFAULT 'Draft',
                    company_id INTEGER,
                    branch_id INTEGER,
                    created_by INTEGER,
                    posted_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                    FOREIGN KEY (bill_id) REFERENCES finance_supplier_bills(id),
                    FOREIGN KEY (period_id) REFERENCES finance_fiscal_periods(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            
            db.execute("""
                CREATE TABLE finance_supplier_debit_note_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    debit_note_id INTEGER NOT NULL,
                    line_number INTEGER NOT NULL,
                    description TEXT,
                    quantity REAL DEFAULT 1,
                    unit_price REAL DEFAULT 0,
                    tax_code_id INTEGER,
                    tax_amount REAL DEFAULT 0,
                    line_total REAL DEFAULT 0,
                    FOREIGN KEY (debit_note_id) REFERENCES finance_supplier_debit_notes(id)
                )
            """)
            
            db.execute("CREATE INDEX idx_ap_dn_number ON finance_supplier_debit_notes(debit_note_number)")
            db.commit()


# ============================================================================
# ASSET MANAGEMENT
# ============================================================================

def _create_asset_categories():
    """Create asset categories table."""
    if not table_exists('finance_asset_categories'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE finance_asset_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    name_ar TEXT,
                    depreciation_method TEXT DEFAULT 'StraightLine',
                    useful_life_years INTEGER DEFAULT 5,
                    salvage_value_percent REAL DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Seed default asset categories
            default_categories = [
                ('FURN', 'Furniture & Fixtures', 'الأثاث والتجهيزات', 'StraightLine', 10, 5),
                ('OFFE', 'Office Equipment', 'معدات المكاتب', 'StraightLine', 5, 0),
                ('ITEQ', 'IT Equipment', 'معدات تقنية المعلومات', 'StraightLine', 3, 0),
                ('VEHI', 'Vehicles', 'المركبات', 'StraightLine', 5, 10),
                ('MACH', 'Machinery', 'الآلات', 'StraightLine', 10, 5),
                ('LEAS', 'Leasehold Improvements', 'تحسينات العقارات المؤجرة', 'StraightLine', 5, 0),
                ('LAND', 'Land', 'الأراضي', 'None', 0, 0),
                ('BULD', 'Buildings', 'المباني', 'StraightLine', 40, 10),
            ]
            for code, name, name_ar, method, life, salvage in default_categories:
                db.execute("""
                    INSERT OR IGNORE INTO finance_asset_categories 
                    (code, name, name_ar, depreciation_method, useful_life_years, salvage_value_percent)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (code, name, name_ar, method, life, salvage))
            db.commit()


def _create_assets():
    """Create fixed assets table."""
    if not table_exists('finance_assets'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE finance_assets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    asset_code TEXT UNIQUE NOT NULL,
                    asset_name TEXT NOT NULL,
                    asset_name_ar TEXT,
                    category_id INTEGER NOT NULL,
                    acquisition_date TEXT NOT NULL,
                    capitalization_date TEXT,
                    acquisition_cost REAL DEFAULT 0,
                    useful_life_years INTEGER,
                    depreciation_method TEXT,
                    salvage_value REAL DEFAULT 0,
                    accumulated_depreciation REAL DEFAULT 0,
                    net_book_value REAL DEFAULT 0,
                    status TEXT DEFAULT 'Active',
                    location TEXT,
                    custodian TEXT,
                    supplier_id INTEGER,
                    purchase_order_id INTEGER,
                    serial_number TEXT,
                    notes TEXT,
                    company_id INTEGER,
                    branch_id INTEGER,
                    cost_center_id INTEGER,
                    asset_account_id INTEGER,
                    accumulated_depr_account_id INTEGER,
                    depreciation_expense_account_id INTEGER,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES finance_asset_categories(id),
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                    FOREIGN KEY (cost_center_id) REFERENCES finance_cost_centers(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            
            db.execute("CREATE INDEX idx_asset_code ON finance_assets(asset_code)")
            db.execute("CREATE INDEX idx_asset_category ON finance_assets(category_id)")
            db.execute("CREATE INDEX idx_asset_status ON finance_assets(status)")
            db.execute("CREATE INDEX idx_asset_company ON finance_assets(company_id)")
            db.commit()


def get_asset_categories():
    """Get all active asset categories."""
    return get_all("SELECT * FROM finance_asset_categories WHERE is_active = 1 ORDER BY code")


def get_assets(company_id=None, category_id=None, status=None, limit=100, offset=0):
    """Get assets with filters."""
    sql = """
        SELECT fa.*, fac.name as category_name, fac.code as category_code,
               c.name as company_name, cc.name as cost_center_name
        FROM finance_assets fa
        LEFT JOIN finance_asset_categories fac ON fa.category_id = fac.id
        LEFT JOIN companies c ON fa.company_id = c.id
        LEFT JOIN finance_cost_centers cc ON fa.cost_center_id = cc.id
        WHERE 1=1
    """
    params = []
    
    if company_id:
        sql += " AND fa.company_id = ?"
        params.append(company_id)
    
    if category_id:
        sql += " AND fa.category_id = ?"
        params.append(category_id)
    
    if status:
        sql += " AND fa.status = ?"
        params.append(status)
    
    sql += " ORDER BY fa.asset_code LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    return get_all(sql, params)


def get_asset_by_id(asset_id):
    """Get asset by ID."""
    return get_one("""
        SELECT fa.*, fac.name as category_name, fac.depreciation_method,
               s.name as supplier_name, cc.name as cost_center_name
        FROM finance_assets fa
        LEFT JOIN finance_asset_categories fac ON fa.category_id = fac.id
        LEFT JOIN suppliers s ON fa.supplier_id = s.id
        LEFT JOIN finance_cost_centers cc ON fa.cost_center_id = cc.id
        WHERE fa.id = ?
    """, (asset_id,))


def get_next_asset_code():
    """Generate next asset code."""
    prefix = 'FA'
    
    result = get_one("""
        SELECT MAX(CAST(SUBSTR(asset_code, LENGTH(?) + 1) AS INTEGER)) as max_num
        FROM finance_assets
        WHERE asset_code LIKE ? || '%'
    """, (prefix, prefix))
    
    next_num = (result.get('max_num') or 0) + 1
    return f"{prefix}-{next_num:05d}"


def create_asset(data):
    """Create a new fixed asset."""
    with get_db_context() as db:
        asset_code = get_next_asset_code()
        
        cursor = db.execute("""
            INSERT INTO finance_assets (
                asset_code, asset_name, asset_name_ar, category_id,
                acquisition_date, capitalization_date, acquisition_cost,
                useful_life_years, depreciation_method, salvage_value,
                accumulated_depreciation, net_book_value, status,
                location, custodian, supplier_id, purchase_order_id,
                serial_number, notes, company_id, branch_id, cost_center_id,
                asset_account_id, accumulated_depr_account_id,
                depreciation_expense_account_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            asset_code,
            data.get('asset_name'),
            data.get('asset_name_ar'),
            data.get('category_id'),
            data.get('acquisition_date'),
            data.get('capitalization_date'),
            data.get('acquisition_cost', 0),
            data.get('useful_life_years'),
            data.get('depreciation_method'),
            data.get('salvage_value', 0),
            0,  # accumulated_depreciation
            data.get('acquisition_cost', 0),  # net_book_value = cost initially
            data.get('status', 'Active'),
            data.get('location'),
            data.get('custodian'),
            data.get('supplier_id'),
            data.get('purchase_order_id'),
            data.get('serial_number'),
            data.get('notes'),
            data.get('company_id'),
            data.get('branch_id'),
            data.get('cost_center_id'),
            data.get('asset_account_id'),
            data.get('accumulated_depr_account_id'),
            data.get('depreciation_expense_account_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# DEPRECIATION
# ============================================================================

def _create_depreciation():
    """Create depreciation tables."""
    if not table_exists('finance_depreciation_runs'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE finance_depreciation_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_number TEXT UNIQUE NOT NULL,
                    run_date TEXT NOT NULL,
                    period_id INTEGER NOT NULL,
                    description TEXT,
                    total_depreciation REAL DEFAULT 0,
                    asset_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'Draft',
                    company_id INTEGER,
                    created_by INTEGER,
                    posted_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    posted_at TIMESTAMP,
                    FOREIGN KEY (period_id) REFERENCES finance_fiscal_periods(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            
            db.execute("""
                CREATE TABLE finance_depreciation_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    asset_id INTEGER NOT NULL,
                    asset_code TEXT,
                    asset_name TEXT,
                    acquisition_cost REAL,
                    salvage_value REAL,
                    depreciable_amount REAL,
                    useful_life_months INTEGER,
                    age_months INTEGER,
                    depreciation_this_run REAL,
                    accumulated_depreciation REAL,
                    net_book_value REAL,
                    line_number INTEGER NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES finance_depreciation_runs(id),
                    FOREIGN KEY (asset_id) REFERENCES finance_assets(id)
                )
            """)
            
            db.execute("CREATE INDEX idx_depr_run ON finance_depreciation_entries(run_id)")
            db.execute("CREATE INDEX idx_depr_asset ON finance_depreciation_entries(asset_id)")
            db.commit()


def get_depreciation_runs(company_id=None, status=None):
    """Get depreciation runs."""
    sql = """
        SELECT fdr.*, fp.name as period_name,
               u.username as created_by_name
        FROM finance_depreciation_runs fdr
        LEFT JOIN finance_fiscal_periods fp ON fdr.period_id = fp.id
        LEFT JOIN users u ON fdr.created_by = u.id
        WHERE 1=1
    """
    params = []
    
    if company_id:
        sql += " AND fdr.company_id = ?"
        params.append(company_id)
    
    if status:
        sql += " AND fdr.status = ?"
        params.append(status)
    
    sql += " ORDER BY fdr.run_date DESC"
    
    return get_all(sql, params if params else None)


def get_next_depreciation_run_number():
    """Generate next depreciation run number."""
    prefix = 'DEP'
    
    result = get_one("""
        SELECT MAX(CAST(SUBSTR(run_number, LENGTH(?) + 1) AS INTEGER)) as max_num
        FROM finance_depreciation_runs
        WHERE run_number LIKE ? || '%'
    """, (prefix, prefix))
    
    next_num = (result.get('max_num') or 0) + 1
    return f"{prefix}-{next_num:05d}"


def calculate_depreciation_for_asset(asset, age_months=0):
    """
    Calculate depreciation for a single asset.
    
    Args:
        asset: Asset dictionary
        age_months: Current age in months
    
    Returns:
        Dictionary with depreciation details
    """
    cost = float(asset.get('acquisition_cost', 0))
    salvage = float(asset.get('salvage_value', 0))
    useful_life_months = int(asset.get('useful_life_years', 5)) * 12
    
    if useful_life_months <= 0:
        return {'depreciation_this_run': 0, 'accumulated': 0, 'net_book_value': cost}
    
    depreciable_amount = cost - salvage
    monthly_depr = depreciable_amount / useful_life_months
    
    depreciation_this_run = monthly_depr
    accumulated = float(asset.get('accumulated_depreciation', 0)) + depreciation_this_run
    net_book_value = cost - accumulated
    
    # Ensure we don't go below salvage value
    if net_book_value < salvage:
        depreciation_this_run = max(0, net_book_value - salvage)
        net_book_value = salvage
        accumulated = cost - salvage
    
    return {
        'depreciation_this_run': depreciation_this_run,
        'accumulated': accumulated,
        'net_book_value': net_book_value
    }


def run_depreciation(period_id, company_id=None, user_id=None, description=None):
    """
    Run depreciation for all eligible assets in a period.
    
    Args:
        period_id: Fiscal period ID
        company_id: Optional company filter
        user_id: User running depreciation
        description: Optional description
    
    Returns:
        depreciation_run_id if successful
    """
    period = get_fiscal_period_by_id(period_id)
    if not period:
        raise ValueError("Fiscal period not found")
    
    if period.get('status') != 'Open':
        raise ValueError("Cannot run depreciation for a closed period")
    
    # Get eligible assets
    sql = """
        SELECT fa.* FROM finance_assets fa
        WHERE fa.status = 'Active'
        AND fa.depreciation_method != 'None'
        AND fa.acquisition_date <= ?
    """
    params = [period.get('end_date')]
    
    if company_id:
        sql += " AND fa.company_id = ?"
        params.append(company_id)
    
    assets = get_all(sql, params)
    
    if not assets:
        raise ValueError("No eligible assets found for depreciation")
    
    with get_db_context() as db:
        run_number = get_next_depreciation_run_number()
        
        cursor = db.execute("""
            INSERT INTO finance_depreciation_runs (
                run_number, run_date, period_id, description, status,
                company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            run_number,
            period.get('end_date'),
            period_id,
            description or f"Depreciation run for {period.get('name')}",
            'Draft',
            company_id,
            user_id
        ))
        
        run_id = cursor.lastrowid
        
        total_depreciation = 0
        line_num = 1
        
        for asset in assets:
            # Calculate age in months
            from datetime import datetime
            acq_date = datetime.strptime(asset.get('acquisition_date'), '%Y-%m-%d')
            end_date = datetime.strptime(period.get('end_date'), '%Y-%m-%d')
            age_months = (end_date.year - acq_date.year) * 12 + (end_date.month - acq_date.month)
            
            depr = calculate_depreciation_for_asset(asset, age_months)
            
            db.execute("""
                INSERT INTO finance_depreciation_entries (
                    run_id, asset_id, asset_code, asset_name,
                    acquisition_cost, salvage_value, depreciable_amount,
                    useful_life_months, age_months, depreciation_this_run,
                    accumulated_depreciation, net_book_value, line_number
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                asset.get('id'),
                asset.get('asset_code'),
                asset.get('asset_name'),
                asset.get('acquisition_cost'),
                asset.get('salvage_value'),
                asset.get('acquisition_cost') - asset.get('salvage_value'),
                asset.get('useful_life_years', 5) * 12,
                age_months,
                depr['depreciation_this_run'],
                depr['accumulated'],
                depr['net_book_value'],
                line_num
            ))
            
            # Update asset accumulated depreciation and net book value
            db.execute("""
                UPDATE finance_assets 
                SET accumulated_depreciation = ?,
                    net_book_value = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (depr['accumulated'], depr['net_book_value'], asset.get('id')))
            
            total_depreciation += depr['depreciation_this_run']
            line_num += 1
        
        db.execute("""
            UPDATE finance_depreciation_runs 
            SET total_depreciation = ?, asset_count = ?
            WHERE id = ?
        """, (total_depreciation, len(assets), run_id))
        
        db.commit()
        return run_id


def post_depreciation_run(run_id, user_id):
    """Post a depreciation run - creates GL entries."""
    run = get_one("SELECT * FROM finance_depreciation_runs WHERE id = ?", (run_id,))
    if not run:
        raise ValueError("Depreciation run not found")
    
    if run.get('status') != 'Draft':
        raise ValueError("Only draft depreciation runs can be posted")
    
    entries = get_all("SELECT * FROM finance_depreciation_entries WHERE run_id = ?", (run_id,))
    
    if not entries:
        raise ValueError("No depreciation entries found")
    
    # Get accounts
    depr_exp_acct = get_one("""
        SELECT id FROM finance_accounts 
        WHERE account_type = 'EXPENSE' AND name LIKE '%Depreciation%' 
        AND is_active = 1 LIMIT 1
    """)
    depr_exp_acct_id = depr_exp_acct.get('id') if depr_exp_acct else None
    
    accum_acct = get_one("""
        SELECT id FROM finance_accounts 
        WHERE account_type = 'ASSET' AND name LIKE '%Accumulated%' 
        AND is_active = 1 LIMIT 1
    """)
    accum_acct_id = accum_acct.get('id') if accum_acct else None
    
    if not depr_exp_acct_id or not accum_acct_id:
        raise ValueError("Depreciation expense or accumulated depreciation account not found")
    
    # Create journal
    journal_lines = []
    
    for entry in entries:
        if entry.get('depreciation_this_run', 0) > 0:
            # Debit: Depreciation Expense
            journal_lines.append({
                'account_id': depr_exp_acct_id,
                'description': f"Depreciation - {entry.get('asset_name')}",
                'debit': entry.get('depreciation_this_run', 0),
                'credit': 0,
                'cost_center_id': None
            })
            
            # Credit: Accumulated Depreciation
            journal_lines.append({
                'account_id': accum_acct_id,
                'description': f"Accumulated Depreciation - {entry.get('asset_name')}",
                'debit': 0,
                'credit': entry.get('depreciation_this_run', 0),
                'cost_center_id': None
            })
    
    if not journal_lines:
        raise ValueError("No depreciation amounts to post")
    
    period = get_fiscal_period_by_id(run.get('period_id'))
    
    journal_data = {
        'journal_type': 'Depreciation',
        'journal_date': run.get('run_date'),
        'reference': run.get('run_number'),
        'source_module': 'Assets',
        'source_id': run_id,
        'description': f"Depreciation Run #{run.get('run_number')}",
        'memo': run.get('description'),
        'company_id': run.get('company_id'),
        'created_by': user_id,
        'status': 'Posted',
        'posted_by': user_id
    }
    
    journal_id = create_journal(journal_data, journal_lines)
    
    with get_db_context() as db:
        db.execute("""
            UPDATE finance_depreciation_runs 
            SET status = 'Posted', posted_by = ?, posted_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, run_id))
        db.commit()
    
    return journal_id


# ============================================================================
# COST CENTERS
# ============================================================================

def _create_cost_centers():
    """Create cost centers table."""
    if not table_exists('finance_cost_centers'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE finance_cost_centers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    name_ar TEXT,
                    description TEXT,
                    parent_id INTEGER,
                    manager_name TEXT,
                    department TEXT,
                    is_active INTEGER DEFAULT 1,
                    is_operational INTEGER DEFAULT 1,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES finance_cost_centers(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            
            db.execute("CREATE INDEX idx_cc_code ON finance_cost_centers(code)")
            db.execute("CREATE INDEX idx_cc_parent ON finance_cost_centers(parent_id)")
            db.execute("CREATE INDEX idx_cc_company ON finance_cost_centers(company_id)")
            db.commit()


def get_cost_centers(company_id=None, active_only=True, parent_id=None):
    """Get cost centers."""
    sql = "SELECT * FROM finance_cost_centers WHERE 1=1"
    params = []
    
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    if active_only:
        sql += " AND is_active = 1"
    
    if parent_id is not None:
        sql += " AND parent_id = ?"
        params.append(parent_id)
    
    sql += " ORDER BY code"
    
    return get_all(sql, params if params else None)


def get_cost_center_by_id(cc_id):
    """Get cost center by ID."""
    return get_one("SELECT * FROM finance_cost_centers WHERE id = ?", (cc_id,))


def create_cost_center(data):
    """Create a new cost center."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO finance_cost_centers (
                code, name, name_ar, description, parent_id,
                manager_name, department, is_active, is_operational, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('code'),
            data.get('name'),
            data.get('name_ar'),
            data.get('description'),
            data.get('parent_id'),
            data.get('manager_name'),
            data.get('department'),
            data.get('is_active', 1),
            data.get('is_operational', 1),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def get_cost_center_balance(cc_id, account_type=None, as_of_date=None):
    """
    Get total balance for a cost center.
    
    Args:
        cc_id: Cost center ID
        account_type: Filter by account type (ASSET, EXPENSE, etc.)
        as_of_date: Optional date filter
    """
    sql = """
        SELECT 
            COALESCE(SUM(CASE WHEN jl.debit > 0 THEN jl.debit ELSE 0 END), 0) as total_debit,
            COALESCE(SUM(CASE WHEN jl.credit > 0 THEN jl.credit ELSE 0 END), 0) as total_credit
        FROM finance_journal_lines jl
        INNER JOIN finance_journals j ON jl.journal_id = j.id
        INNER JOIN finance_accounts a ON jl.account_id = a.id
        WHERE jl.cost_center_id = ?
        AND j.status = 'Posted'
    """
    params = [cc_id]
    
    if account_type:
        sql += " AND a.account_type = ?"
        params.append(account_type)
    
    if as_of_date:
        sql += " AND j.journal_date <= ?"
        params.append(as_of_date)
    
    result = get_one(sql, params)
    
    if result:
        return {
            'total_debit': float(result['total_debit'] or 0),
            'total_credit': float(result['total_credit'] or 0),
            'balance': float(result['total_debit'] or 0) - float(result['total_credit'] or 0)
        }
    
    return {'total_debit': 0, 'total_credit': 0, 'balance': 0}


# ============================================================================
# BUDGET MANAGEMENT
# ============================================================================

def _create_budgets():
    """Create budget tables."""
    if not table_exists('finance_budgets'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE finance_budgets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    budget_number TEXT UNIQUE NOT NULL,
                    budget_name TEXT NOT NULL,
                    fiscal_year_id INTEGER NOT NULL,
                    version INTEGER DEFAULT 1,
                    status TEXT DEFAULT 'Draft',
                    company_id INTEGER,
                    branch_id INTEGER,
                    cost_center_id INTEGER,
                    prepared_by INTEGER,
                    approved_by INTEGER,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (fiscal_year_id) REFERENCES finance_fiscal_periods(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id),
                    FOREIGN KEY (cost_center_id) REFERENCES finance_cost_centers(id)
                )
            """)
            
            db.execute("""
                CREATE TABLE finance_budget_lines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    budget_id INTEGER NOT NULL,
                    account_id INTEGER NOT NULL,
                    cost_center_id INTEGER,
                    january REAL DEFAULT 0,
                    february REAL DEFAULT 0,
                    march REAL DEFAULT 0,
                    april REAL DEFAULT 0,
                    may REAL DEFAULT 0,
                    june REAL DEFAULT 0,
                    july REAL DEFAULT 0,
                    august REAL DEFAULT 0,
                    september REAL DEFAULT 0,
                    october REAL DEFAULT 0,
                    november REAL DEFAULT 0,
                    december REAL DEFAULT 0,
                    total_budget REAL DEFAULT 0,
                    total_actual REAL DEFAULT 0,
                    variance REAL DEFAULT 0,
                    line_number INTEGER NOT NULL,
                    notes TEXT,
                    FOREIGN KEY (budget_id) REFERENCES finance_budgets(id),
                    FOREIGN KEY (account_id) REFERENCES finance_accounts(id),
                    FOREIGN KEY (cost_center_id) REFERENCES finance_cost_centers(id)
                )
            """)
            
            db.execute("CREATE INDEX idx_budget_number ON finance_budgets(budget_number)")
            db.execute("CREATE INDEX idx_budget_year ON finance_budgets(fiscal_year_id)")
            db.execute("CREATE INDEX idx_budget_status ON finance_budgets(status)")
            db.execute("CREATE INDEX idx_budget_line ON finance_budget_lines(budget_id)")
            db.commit()


def get_budgets(company_id=None, fiscal_year_id=None, status=None):
    """Get budgets."""
    sql = """
        SELECT fb.*, ffy.name as fiscal_year_name,
               u1.username as prepared_by_name,
               u2.username as approved_by_name,
               cc.name as cost_center_name
        FROM finance_budgets fb
        LEFT JOIN finance_fiscal_years ffy ON fb.fiscal_year_id = ffy.id
        LEFT JOIN users u1 ON fb.prepared_by = u1.id
        LEFT JOIN users u2 ON fb.approved_by = u2.id
        LEFT JOIN finance_cost_centers cc ON fb.cost_center_id = cc.id
        WHERE 1=1
    """
    params = []
    
    if company_id:
        sql += " AND fb.company_id = ?"
        params.append(company_id)
    
    if fiscal_year_id:
        sql += " AND fb.fiscal_year_id = ?"
        params.append(fiscal_year_id)
    
    if status:
        sql += " AND fb.status = ?"
        params.append(status)
    
    sql += " ORDER BY fb.budget_number DESC"
    
    return get_all(sql, params if params else None)


def get_budget_by_id(budget_id):
    """Get budget by ID with lines."""
    budget = get_one("""
        SELECT fb.*, ffy.name as fiscal_year_name, ffy.start_date, ffy.end_date,
               cc.name as cost_center_name
        FROM finance_budgets fb
        LEFT JOIN finance_fiscal_years ffy ON fb.fiscal_year_id = ffy.id
        LEFT JOIN finance_cost_centers cc ON fb.cost_center_id = cc.id
        WHERE fb.id = ?
    """, (budget_id,))
    
    if budget:
        budget['lines'] = get_all("""
            SELECT fbl.*, fa.code as account_code, fa.name as account_name,
                   cc.name as cost_center_name
            FROM finance_budget_lines fbl
            LEFT JOIN finance_accounts fa ON fbl.account_id = fa.id
            LEFT JOIN finance_cost_centers cc ON fbl.cost_center_id = cc.id
            WHERE fbl.budget_id = ?
            ORDER BY fbl.line_number
        """, (budget_id,))
    
    return budget


def get_next_budget_number():
    """Generate next budget number."""
    prefix = 'BUD'
    
    result = get_one("""
        SELECT MAX(CAST(SUBSTR(budget_number, LENGTH(?) + 1) AS INTEGER)) as max_num
        FROM finance_budgets
        WHERE budget_number LIKE ? || '%'
    """, (prefix, prefix))
    
    next_num = (result.get('max_num') or 0) + 1
    return f"{prefix}-{next_num:05d}"


def create_budget(data, lines):
    """Create a budget with lines."""
    with get_db_context() as db:
        budget_number = get_next_budget_number()
        
        cursor = db.execute("""
            INSERT INTO finance_budgets (
                budget_number, budget_name, fiscal_year_id, version, status,
                company_id, branch_id, cost_center_id, prepared_by, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            budget_number,
            data.get('budget_name'),
            data.get('fiscal_year_id'),
            data.get('version', 1),
            data.get('status', 'Draft'),
            data.get('company_id'),
            data.get('branch_id'),
            data.get('cost_center_id'),
            data.get('prepared_by'),
            data.get('notes')
        ))
        
        budget_id = cursor.lastrowid
        
        for idx, line in enumerate(lines, 1):
            monthly_total = sum([
                float(line.get('january', 0)), float(line.get('february', 0)),
                float(line.get('march', 0)), float(line.get('april', 0)),
                float(line.get('may', 0)), float(line.get('june', 0)),
                float(line.get('july', 0)), float(line.get('august', 0)),
                float(line.get('september', 0)), float(line.get('october', 0)),
                float(line.get('november', 0)), float(line.get('december', 0))
            ])
            
            db.execute("""
                INSERT INTO finance_budget_lines (
                    budget_id, account_id, cost_center_id,
                    january, february, march, april, may, june,
                    july, august, september, october, november, december,
                    total_budget, total_actual, variance, line_number, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                budget_id,
                line.get('account_id'),
                line.get('cost_center_id'),
                line.get('january', 0), line.get('february', 0),
                line.get('march', 0), line.get('april', 0),
                line.get('may', 0), line.get('june', 0),
                line.get('july', 0), line.get('august', 0),
                line.get('september', 0), line.get('october', 0),
                line.get('november', 0), line.get('december', 0),
                monthly_total, 0, 0,
                idx,
                line.get('notes')
            ))
        
        db.commit()
        return budget_id


def approve_budget(budget_id, user_id):
    """Approve a budget."""
    with get_db_context() as db:
        db.execute("""
            UPDATE finance_budgets 
            SET status = 'Approved', approved_by = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND status = 'Draft'
        """, (user_id, budget_id))
        db.commit()


def get_budget_vs_actual(budget_id):
    """
    Compare budget vs actual for a budget.
    
    Returns budget lines with actual amounts calculated from posted journals.
    """
    budget = get_budget_by_id(budget_id)
    if not budget:
        return None
    
    fiscal_year = get_fiscal_year_by_id(budget.get('fiscal_year_id'))
    if not fiscal_year:
        return budget
    
    from datetime import datetime
    
    for line in budget.get('lines', []):
        account_id = line.get('account_id')
        cc_id = line.get('cost_center_id')
        
        actual_by_month = []
        
        for month in range(1, 13):
            month_name = ['january', 'february', 'march', 'april', 'may', 'june',
                         'july', 'august', 'september', 'october', 'november', 'december'][month - 1]
            
            # Get period for this month
            start_day = fiscal_year.get('start_date')[:4] + '-' + f'{month:02d}' + '-01'
            
            try:
                period = get_fiscal_period_by_date(start_day, budget.get('company_id'))
                if period:
                    # Sum actuals for this account/cost center in this period
                    sql = """
                        SELECT COALESCE(SUM(jl.debit), 0) as actual
                        FROM finance_journal_lines jl
                        INNER JOIN finance_journals j ON jl.journal_id = j.id
                        WHERE jl.account_id = ?
                        AND j.period_id = ?
                        AND j.status = 'Posted'
                    """
                    params = [account_id, period.get('id')]
                    
                    if cc_id:
                        sql += " AND jl.cost_center_id = ?"
                        params.append(cc_id)
                    
                    result = get_one(sql, params)
                    actual_by_month.append(result.get('actual', 0) if result else 0)
                else:
                    actual_by_month.append(0)
            except:
                actual_by_month.append(0)
        
        line['actual_by_month'] = actual_by_month
        line['total_actual'] = sum(actual_by_month)
        line['variance'] = line.get('total_budget', 0) - line['total_actual']
    
    return budget


# ============================================================================
# TAX MANAGEMENT
# ============================================================================

def _create_tax_codes():
    """Create tax codes table."""
    if not table_exists('finance_tax_codes'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE finance_tax_codes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    name_ar TEXT,
                    tax_type TEXT NOT NULL,
                    rate REAL DEFAULT 0,
                    is_inclusive INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    description TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            
            # Seed default tax codes
            default_codes = [
                ('STANDARD', 'Standard Rate 15%', 'السعر القياسي 15%', 'Output', 15.0, 0, 1),
                ('ZERO', 'Zero Rated 0%', 'معدل صفر 0%', 'Output', 0.0, 0, 1),
                ('EXEMPT', 'Exempt 0%', 'معفى 0%', 'Output', 0.0, 0, 1),
                ('STANDARD_IN', 'Standard Rate 15% (Input)', 'السعر القياسي 15% (مدخل)', 'Input', 15.0, 0, 1),
                ('REVERSE', 'Reverse Charge', 'الوعاء العكسي', 'ReverseCharge', 15.0, 0, 1),
            ]
            for code, name, name_ar, tax_type, rate, inclusive, active in default_codes:
                db.execute("""
                    INSERT OR IGNORE INTO finance_tax_codes 
                    (code, name, name_ar, tax_type, rate, is_inclusive, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (code, name, name_ar, tax_type, rate, inclusive, active))
            
            db.execute("CREATE INDEX idx_tax_code ON finance_tax_codes(code)")
            db.commit()


def _create_tax_rules():
    """Create tax rules table."""
    if not table_exists('finance_tax_rules'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE finance_tax_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    tax_code_id INTEGER NOT NULL,
                    source_type TEXT,
                    source_subtype TEXT,
                    account_id INTEGER,
                    condition TEXT,
                    is_active INTEGER DEFAULT 1,
                    company_id INTEGER,
                    priority INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tax_code_id) REFERENCES finance_tax_codes(id),
                    FOREIGN KEY (account_id) REFERENCES finance_accounts(id)
                )
            """)
            db.commit()


def _create_finance_settings():
    """Create finance settings table."""
    if not table_exists('finance_settings'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE finance_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT UNIQUE NOT NULL,
                    setting_value TEXT,
                    category TEXT DEFAULT 'General',
                    description TEXT,
                    is_active INTEGER DEFAULT 1,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Seed default finance settings
            defaults = [
                ('default_currency', 'AED', 'General', 'Default currency for finance'),
                ('default_country', 'UAE', 'General', 'Default country for tax'),
                ('base_tax_code', 'STANDARD', 'Tax', 'Base tax code for transactions'),
                ('ar_control_account', '', 'Accounts', 'Default AR control account'),
                ('ap_control_account', '', 'Accounts', 'Default AP control account'),
                ('cash_account', '', 'Accounts', 'Default cash account'),
                ('bank_account', '', 'Accounts', 'Default bank account'),
                ('vat_output_account', '', 'Tax', 'VAT output liability account'),
                ('vat_input_account', '', 'Tax', 'VAT input recoverable account'),
                ('depreciation_expense_account', '', 'Assets', 'Depreciation expense account'),
                ('accumulated_depr_account', '', 'Assets', 'Accumulated depreciation account'),
                ('auto_post_journals', '0', 'Posting', 'Auto-post journals on creation'),
                ('require_journal_approval', '0', 'Posting', 'Require approval before posting'),
                ('allow_back_dating', '0', 'Posting', 'Allow posting to closed periods'),
                ('fiscal_year_start_month', '1', 'Fiscal', 'Month when fiscal year starts'),
                ('number_format_prefix', '', 'Numbering', 'Document number prefix'),
            ]
            for key, value, category, desc in defaults:
                db.execute("""
                    INSERT OR IGNORE INTO finance_settings 
                    (setting_key, setting_value, category, description)
                    VALUES (?, ?, ?, ?)
                """, (key, value, category, desc))
            
            db.commit()


def get_tax_codes(company_id=None, tax_type=None, active_only=True):
    """Get tax codes."""
    sql = "SELECT * FROM finance_tax_codes WHERE 1=1"
    params = []
    
    if company_id:
        sql += " AND (company_id = ? OR company_id IS NULL)"
        params.append(company_id)
    
    if active_only:
        sql += " AND is_active = 1"
    
    if tax_type:
        sql += " AND tax_type = ?"
        params.append(tax_type)
    
    sql += " ORDER BY code"
    
    return get_all(sql, params)


def get_tax_code_by_id(tax_id):
    """Get tax code by ID."""
    return get_one("SELECT * FROM finance_tax_codes WHERE id = ?", (tax_id,))


def calculate_tax(tax_code_id, amount, is_inclusive=True):
    """
    Calculate tax amount.
    
    Args:
        tax_code_id: Tax code ID
        amount: Transaction amount
        is_inclusive: Whether the amount includes tax
    
    Returns:
        Dictionary with subtotal, tax_amount, total
    """
    tax_code = get_tax_code_by_id(tax_code_id)
    if not tax_code:
        return {'subtotal': amount, 'tax_amount': 0, 'total': amount}
    
    rate = float(tax_code.get('rate', 0)) / 100
    
    if is_inclusive or tax_code.get('is_inclusive'):
        # Tax is included in amount
        subtotal = amount / (1 + rate)
        tax_amount = amount - subtotal
    else:
        # Tax is exclusive
        subtotal = amount
        tax_amount = amount * rate
    
    return {
        'subtotal': round(subtotal, 2),
        'tax_amount': round(tax_amount, 2),
        'total': round(subtotal + tax_amount, 2),
        'rate': tax_code.get('rate', 0)
    }


# ============================================================================
# FINANCIAL REPORTS HELPERS
# ============================================================================

def get_trial_balance(company_id=None, period_id=None, as_of_date=None):
    """
    Generate trial balance.
    
    Args:
        company_id: Filter by company
        period_id: Use balances from a specific period
        as_of_date: Calculate balances up to a date
    
    Returns:
        List of accounts with debit/credit balances
    """
    accounts = get_accounts(company_id=company_id, active_only=True)
    
    trial_balance = []
    
    for account in accounts:
        balance_info = get_account_balance(
            account.get('id'),
            period_id=period_id,
            as_of_date=as_of_date
        )
        
        # Add opening balance if no transactions
        if balance_info['debit_total'] == 0 and balance_info['credit_total'] == 0:
            opening = float(account.get('opening_balance', 0) or 0)
            if opening != 0:
                if opening > 0:
                    balance_info['debit_total'] = opening
                else:
                    balance_info['credit_total'] = abs(opening)
                balance_info['balance'] = opening
        
        # Only include accounts with activity or opening balance
        if balance_info['debit_total'] > 0 or balance_info['credit_total'] > 0:
            trial_balance.append({
                'account_id': account.get('id'),
                'account_code': account.get('code'),
                'account_name': account.get('name'),
                'account_type': account.get('account_type'),
                'category_name': account.get('category_id'),
                'debit': balance_info['debit_total'],
                'credit': balance_info['credit_total']
            })
    
    return trial_balance


def get_account_ledger(account_id, start_date=None, end_date=None, 
                       cost_center_id=None, company_id=None):
    """
    Get detailed ledger for a specific account.
    
    Args:
        account_id: Account ID
        start_date: Start date filter
        end_date: End date filter
        cost_center_id: Filter by cost center
        company_id: Filter by company
    
    Returns:
        List of journal lines with running balance
    """
    account = get_account_by_id(account_id)
    if not account:
        return []
    
    opening_balance = float(account.get('opening_balance', 0) or 0)
    
    sql = """
        SELECT jl.*, j.journal_number, j.journal_date, j.description as journal_desc,
               j.period_id, fa.code as account_code, fa.name as account_name,
               cc.code as cost_center_code, cc.name as cost_center_name
        FROM finance_journal_lines jl
        INNER JOIN finance_journals j ON jl.journal_id = j.id
        LEFT JOIN finance_accounts fa ON jl.account_id = fa.id
        LEFT JOIN finance_cost_centers cc ON jl.cost_center_id = cc.id
        WHERE jl.account_id = ?
        AND j.status = 'Posted'
    """
    params = [account_id]
    
    if start_date:
        sql += " AND j.journal_date >= ?"
        params.append(start_date)
    
    if end_date:
        sql += " AND j.journal_date <= ?"
        params.append(end_date)
    
    if cost_center_id:
        sql += " AND jl.cost_center_id = ?"
        params.append(cost_center_id)
    
    if company_id:
        sql += " AND j.company_id = ?"
        params.append(company_id)
    
    sql += " ORDER BY j.journal_date, j.id"
    
    lines = get_all(sql, params)
    
    # Calculate running balance
    running_balance = opening_balance
    result_lines = []
    
    # Opening entry if has opening balance
    if opening_balance != 0:
        result_lines.append({
            'id': None,
            'journal_number': 'Opening',
            'journal_date': account.get('opening_balance_date') or '1900-01-01',
            'description': 'Opening Balance',
            'debit': opening_balance if opening_balance > 0 else 0,
            'credit': abs(opening_balance) if opening_balance < 0 else 0,
            'balance': opening_balance,
            'cost_center_name': None,
            'is_opening': True
        })
        running_balance = opening_balance
    
    for line in lines:
        debit = float(line.get('debit', 0) or 0)
        credit = float(line.get('credit', 0) or 0)
        running_balance += debit - credit
        
        result_lines.append({
            'id': line.get('id'),
            'journal_number': line.get('journal_number'),
            'journal_date': line.get('journal_date'),
            'description': line.get('description') or line.get('journal_desc'),
            'debit': debit,
            'credit': credit,
            'balance': running_balance,
            'cost_center_name': line.get('cost_center_name'),
            'reference': line.get('reference'),
            'is_opening': False
        })
    
    return result_lines


def get_ar_aging(customer_id=None, company_id=None, as_of_date=None):
    """
    Get AR aging summary.
    
    Args:
        customer_id: Filter by customer
        company_id: Filter by company
        as_of_date: Date for aging calculation
    
    Returns:
        List of customers with aging buckets
    """
    date_filter = as_of_date or 'today'
    
    sql = """
        SELECT c.id as customer_id, c.id as customer_code, c.name as customer_name,
               ci.invoice_number, ci.invoice_date, ci.due_date,
               ci.total_amount, ci.amount_paid, ci.amount_due,
               ci.status,
               julianday('now') - julianday(ci.due_date) as days_overdue
        FROM finance_customer_invoices ci
        INNER JOIN customers c ON ci.customer_id = c.id
        WHERE ci.status IN ('Posted', 'PartiallyPaid')
        AND ci.amount_due > 0
    """
    params = []
    
    if customer_id:
        sql += " AND c.id = ?"
        params.append(customer_id)
    
    if company_id:
        sql += " AND ci.company_id = ?"
        params.append(company_id)
    
    if as_of_date:
        sql += " AND ci.due_date <= ?"
        params.append(as_of_date)
    
    sql += " ORDER BY c.name, ci.due_date"
    
    invoices = get_all(sql, params)
    
    # Group by customer
    customers = {}
    for inv in invoices:
        cid = inv.get('customer_id')
        if cid not in customers:
            customers[cid] = {
                'customer_id': cid,
                'customer_code': inv.get('customer_code'),
                'customer_name': inv.get('customer_name'),
                'total_due': 0,
                'current': 0,
                'days_1_30': 0,
                'days_31_60': 0,
                'days_61_90': 0,
                'days_over_90': 0,
                'invoices': []
            }
        
        amount_due = float(inv.get('amount_due', 0) or 0)
        days_overdue = float(inv.get('days_overdue', 0) or 0)
        
        customers[cid]['total_due'] += amount_due
        customers[cid]['invoices'].append({
            'invoice_number': inv.get('invoice_number'),
            'invoice_date': inv.get('invoice_date'),
            'due_date': inv.get('due_date'),
            'amount_due': amount_due,
            'days_overdue': days_overdue
        })
        
        if days_overdue <= 0:
            customers[cid]['current'] += amount_due
        elif days_overdue <= 30:
            customers[cid]['days_1_30'] += amount_due
        elif days_overdue <= 60:
            customers[cid]['days_31_60'] += amount_due
        elif days_overdue <= 90:
            customers[cid]['days_61_90'] += amount_due
        else:
            customers[cid]['days_over_90'] += amount_due
    
    return list(customers.values())


def get_ap_aging(supplier_id=None, company_id=None, as_of_date=None):
    """
    Get AP aging summary.
    
    Args:
        supplier_id: Filter by supplier
        company_id: Filter by company
        as_of_date: Date for aging calculation
    
    Returns:
        List of suppliers with aging buckets
    """
    date_filter = as_of_date or 'today'
    
    sql = """
        SELECT s.id as supplier_id, s.code as supplier_code, s.name as supplier_name,
               sb.bill_number, sb.bill_date, sb.due_date,
               sb.total_amount, sb.amount_paid, sb.amount_due,
               sb.status,
               julianday('now') - julianday(sb.due_date) as days_overdue
        FROM finance_supplier_bills sb
        INNER JOIN suppliers s ON sb.supplier_id = s.id
        WHERE sb.status IN ('Posted', 'PartiallyPaid')
        AND sb.amount_due > 0
    """
    params = []
    
    if supplier_id:
        sql += " AND s.id = ?"
        params.append(supplier_id)
    
    if company_id:
        sql += " AND sb.company_id = ?"
        params.append(company_id)
    
    if as_of_date:
        sql += " AND sb.due_date <= ?"
        params.append(as_of_date)
    
    sql += " ORDER BY s.name, sb.due_date"
    
    bills = get_all(sql, params)
    
    # Group by supplier
    suppliers = {}
    for bill in bills:
        sid = bill.get('supplier_id')
        if sid not in suppliers:
            suppliers[sid] = {
                'supplier_id': sid,
                'supplier_code': bill.get('supplier_code'),
                'supplier_name': bill.get('supplier_name'),
                'total_due': 0,
                'current': 0,
                'days_1_30': 0,
                'days_31_60': 0,
                'days_61_90': 0,
                'days_over_90': 0,
                'bills': []
            }
        
        amount_due = float(bill.get('amount_due', 0) or 0)
        days_overdue = float(bill.get('days_overdue', 0) or 0)
        
        suppliers[sid]['total_due'] += amount_due
        suppliers[sid]['bills'].append({
            'bill_number': bill.get('bill_number'),
            'bill_date': bill.get('bill_date'),
            'due_date': bill.get('due_date'),
            'amount_due': amount_due,
            'days_overdue': days_overdue
        })
        
        if days_overdue <= 0:
            suppliers[sid]['current'] += amount_due
        elif days_overdue <= 30:
            suppliers[sid]['days_1_30'] += amount_due
        elif days_overdue <= 60:
            suppliers[sid]['days_31_60'] += amount_due
        elif days_overdue <= 90:
            suppliers[sid]['days_61_90'] += amount_due
        else:
            suppliers[sid]['days_over_90'] += amount_due
    
    return list(suppliers.values())


def get_financial_summary(company_id=None, period_id=None, start_date=None, end_date=None):
    """
    Get high-level financial summary for dashboard.
    
    Returns:
        Dictionary with total receivables, payables, revenue, expenses, etc.
    """
    summary = {
        'total_receivables': 0,
        'total_payables': 0,
        'total_revenue': 0,
        'total_expenses': 0,
        'net_profit': 0,
        'total_assets': 0,
        'total_liabilities': 0,
        'total_equity': 0,
    }
    
    # Get AR total
    ar_result = get_one("""
        SELECT COALESCE(SUM(amount_due), 0) as total
        FROM finance_customer_invoices
        WHERE status IN ('Posted', 'PartiallyPaid')
        AND amount_due > 0
    """)
    if ar_result:
        summary['total_receivables'] = float(ar_result['total'] or 0)
    
    # Get AP total
    ap_result = get_one("""
        SELECT COALESCE(SUM(amount_due), 0) as total
        FROM finance_supplier_bills
        WHERE status IN ('Posted', 'PartiallyPaid')
        AND amount_due > 0
    """)
    if ap_result:
        summary['total_payables'] = float(ap_result['total'] or 0)
    
    # Get current period revenue
    revenue_sql = """
        SELECT COALESCE(SUM(jl.credit), 0) as total
        FROM finance_journal_lines jl
        INNER JOIN finance_journals j ON jl.journal_id = j.id
        INNER JOIN finance_accounts a ON jl.account_id = a.id
        WHERE j.status = 'Posted'
        AND a.account_type = 'REVENUE'
    """
    revenue_params = []
    if period_id:
        revenue_sql += " AND j.period_id = ?"
        revenue_params.append(period_id)
    if start_date:
        revenue_sql += " AND j.journal_date >= ?"
        revenue_params.append(start_date)
    if end_date:
        revenue_sql += " AND j.journal_date <= ?"
        revenue_params.append(end_date)
    
    rev_result = get_one(revenue_sql, revenue_params if revenue_params else None)
    if rev_result:
        summary['total_revenue'] = float(rev_result['total'] or 0)
    
    # Get current period expenses
    expense_sql = """
        SELECT COALESCE(SUM(jl.debit), 0) as total
        FROM finance_journal_lines jl
        INNER JOIN finance_journals j ON jl.journal_id = j.id
        INNER JOIN finance_accounts a ON jl.account_id = a.id
        WHERE j.status = 'Posted'
        AND a.account_type IN ('EXPENSE', 'COGS')
    """
    expense_params = []
    if period_id:
        expense_sql += " AND j.period_id = ?"
        expense_params.append(period_id)
    if start_date:
        expense_sql += " AND j.journal_date >= ?"
        expense_params.append(start_date)
    if end_date:
        expense_sql += " AND j.journal_date <= ?"
        expense_params.append(end_date)
    
    exp_result = get_one(expense_sql, expense_params if expense_params else None)
    if exp_result:
        summary['total_expenses'] = float(exp_result['total'] or 0)
    
    summary['net_profit'] = summary['total_revenue'] - summary['total_expenses']
    
    return summary


# ============================================================================
# POSTING RULES MANAGEMENT
# ============================================================================

def get_posting_rules(source_module=None, source_type=None, company_id=None):
    """Get posting rules with filters."""
    sql = "SELECT * FROM finance_posting_rules WHERE is_active = 1"
    params = []
    
    if source_module:
        sql += " AND source_module = ?"
        params.append(source_module)
    
    if source_type:
        sql += " AND source_type = ?"
        params.append(source_type)
    
    if company_id:
        sql += " AND (company_id = ? OR company_id IS NULL)"
        params.append(company_id)
    
    return get_all(sql, params)


def create_posting_rule(data):
    """Create a new posting rule."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO finance_posting_rules (
                name, source_module, source_type, debit_account_id,
                credit_account_id, description, is_active, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('name'),
            data.get('source_module'),
            data.get('source_type'),
            data.get('debit_account_id'),
            data.get('credit_account_id'),
            data.get('description'),
            data.get('is_active', 1),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def apply_posting_rule(source_module, source_type, company_id=None):
    """
    Apply posting rule to get default accounts for a transaction.
    
    Returns:
        Dictionary with debit_account_id and credit_account_id
    """
    rules = get_posting_rules(source_module, source_type, company_id)
    
    if rules:
        rule = rules[0]
        return {
            'debit_account_id': rule.get('debit_account_id'),
            'credit_account_id': rule.get('credit_account_id'),
            'rule_name': rule.get('name')
        }
    
    return None


# Initialize finance schema when module is imported
initialize_finance_schema()
