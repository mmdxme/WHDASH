"""
Finance Module - Additional Models
==================================
Extends finance_models.py with additional model functions needed for:
- Financial Close Tasks
- Journal Templates & Batches
- Profit Centers
- Tax Rules
- Intercompany Transactions
- Cost Allocation Rules
- Bank Reconciliation Sets
- GL/AR/AP Reconciliation Sets
- Flow Alerts

Author: Finance Module Enhancement
"""

from database import get_db_context, get_one, get_all, row_to_dict, table_exists, log_audit


# ============================================================================
# FINANCIAL CLOSE MANAGEMENT
# ============================================================================

def _create_close_tables():
    """Create financial close management tables."""
    if not table_exists('finance_close_tasks'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS finance_close_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    period_id INTEGER NOT NULL,
                    task_name TEXT NOT NULL,
                    description TEXT,
                    task_type TEXT DEFAULT 'standard',
                    assigned_to INTEGER,
                    due_date TEXT,
                    status TEXT DEFAULT 'Pending',
                    priority INTEGER DEFAULT 5,
                    completed_by INTEGER,
                    completed_at TIMESTAMP,
                    notes TEXT,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (period_id) REFERENCES finance_fiscal_periods(id),
                    FOREIGN KEY (assigned_to) REFERENCES users(id)
                )
            """)
            db.execute("CREATE INDEX idx_close_task_period ON finance_close_tasks(period_id)")
            db.execute("CREATE INDEX idx_close_task_status ON finance_close_tasks(status)")
            db.commit()
    
    # Create close checklist templates
    if not table_exists('finance_close_checklist_templates'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS finance_close_checklist_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    task_name TEXT NOT NULL,
                    description TEXT,
                    task_type TEXT DEFAULT 'standard',
                    default_priority INTEGER DEFAULT 5,
                    is_active INTEGER DEFAULT 1
                )
            """)
            db.commit()
            
            # Seed default checklist items
            defaults = [
                ('Month-End Close', 'Reconcile all bank accounts', 'Bank Rec', 1, 1),
                ('Month-End Close', 'Post depreciation entries', 'Depreciation', 2, 1),
                ('Month-End Close', 'Review AR aging', 'AR Review', 3, 1),
                ('Month-End Close', 'Review AP aging', 'AP Review', 4, 1),
                ('Month-End Close', 'Reconcile intercompany accounts', 'Intercompany', 5, 1),
                ('Month-End Close', 'Review suspense accounts', 'Suspense', 6, 1),
                ('Month-End Close', 'Prepare accruals journal', 'Accruals', 7, 1),
                ('Month-End Close', 'Run trial balance', 'Trial Balance', 8, 1),
                ('Month-End Close', 'Submit for approval', 'Approval', 9, 1),
                ('Year-End Close', 'Prepare year-end reconciliation', 'Year-End', 1, 1),
                ('Year-End Close', 'Review fixed asset register', 'Assets', 2, 1),
                ('Year-End Close', 'Prepare tax files', 'Tax', 3, 1),
                ('Year-End Close', 'Retained earnings calculation', 'Retained Earnings', 4, 1),
            ]
            for name, task_name, desc, priority, active in defaults:
                db.execute("""
                    INSERT OR IGNORE INTO finance_close_checklist_templates
                    (name, task_name, description, task_type, default_priority, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, task_name, desc, desc, priority, active))
            db.commit()


def create_close_task(data):
    """Create a close task."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO finance_close_tasks (
                period_id, task_name, description, task_type,
                assigned_to, due_date, status, priority, notes, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('period_id'),
            data.get('task_name'),
            data.get('description'),
            data.get('task_type', 'standard'),
            data.get('assigned_to'),
            data.get('due_date'),
            data.get('status', 'Pending'),
            data.get('priority', 5),
            data.get('notes'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def get_close_tasks(period_id=None, status=None):
    """Get close tasks."""
    sql = "SELECT ct.*, u.username as assigned_to_name FROM finance_close_tasks ct LEFT JOIN users u ON ct.assigned_to = u.id WHERE 1=1"
    params = []
    
    if period_id:
        sql += " AND ct.period_id = ?"
        params.append(period_id)
    
    if status:
        sql += " AND ct.status = ?"
        params.append(status)
    
    sql += " ORDER BY ct.priority, ct.due_date"
    return get_all(sql, params)


def complete_close_task(task_id, user_id):
    """Mark a close task as complete."""
    with get_db_context() as db:
        db.execute("""
            UPDATE finance_close_tasks 
            SET status = 'Completed', completed_by = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user_id, task_id))
        db.commit()


# ============================================================================
# JOURNAL TEMPLATES & BATCHES
# ============================================================================

def _create_journal_templates_tables():
    """Create journal templates and batches tables."""
    if not table_exists('finance_journal_templates'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS finance_journal_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    journal_type TEXT DEFAULT 'General',
                    lines_json TEXT,
                    company_id INTEGER,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_jt_company ON finance_journal_templates(company_id)")
            db.commit()
    
    if not table_exists('finance_journal_batches'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS finance_journal_batches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_number TEXT UNIQUE NOT NULL,
                    batch_date DATE NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'Draft',
                    total_debit REAL DEFAULT 0,
                    total_credit REAL DEFAULT 0,
                    journal_count INTEGER DEFAULT 0,
                    company_id INTEGER,
                    created_by INTEGER,
                    approved_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS finance_journal_batch_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id INTEGER NOT NULL,
                    template_id INTEGER,
                    journal_date DATE,
                    reference TEXT,
                    description TEXT,
                    total_debit REAL DEFAULT 0,
                    total_credit REAL DEFAULT 0,
                    status TEXT DEFAULT 'Pending',
                    journal_id INTEGER,
                    FOREIGN KEY (batch_id) REFERENCES finance_journal_batches(id),
                    FOREIGN KEY (template_id) REFERENCES finance_journal_templates(id),
                    FOREIGN KEY (journal_id) REFERENCES finance_journals(id)
                )
            """)
            db.execute("CREATE INDEX idx_jb_company ON finance_journal_batches(company_id)")
            db.execute("CREATE INDEX idx_jbi_batch ON finance_journal_batch_items(batch_id)")
            db.commit()


def get_journal_templates(company_id=None):
    """Get all journal templates."""
    sql = "SELECT * FROM finance_journal_templates WHERE 1=1"
    params = []
    if company_id:
        sql += " AND (company_id = ? OR company_id IS NULL)"
        params.append(company_id)
    sql += " ORDER BY name"
    return get_all(sql, params)


def get_journal_template_by_id(template_id):
    """Get template by ID."""
    return get_one("SELECT * FROM finance_journal_templates WHERE id = ?", (template_id,))


def create_journal_template(data):
    """Create a journal template."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO finance_journal_templates (
                name, description, journal_type, lines_json, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            data.get('name'),
            data.get('description'),
            data.get('journal_type', 'General'),
            data.get('lines_json'),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def get_journal_batches(company_id=None, status=None):
    """Get journal batches."""
    sql = """
        SELECT jb.*, u.username as created_by_name,
               (SELECT COUNT(*) FROM finance_journal_batch_items WHERE batch_id = jb.id) as item_count
        FROM finance_journal_batches jb
        LEFT JOIN users u ON jb.created_by = u.id
        WHERE 1=1
    """
    params = []
    
    if company_id:
        sql += " AND jb.company_id = ?"
        params.append(company_id)
    
    if status:
        sql += " AND jb.status = ?"
        params.append(status)
    
    sql += " ORDER BY jb.batch_date DESC"
    return get_all(sql, params)


def create_journal_batch(data, items=None):
    """Create a journal batch."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO finance_journal_batches (
                batch_number, batch_date, description, status,
                total_debit, total_credit, journal_count,
                company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('batch_number'),
            data.get('batch_date'),
            data.get('description'),
            data.get('status', 'Draft'),
            data.get('total_debit', 0),
            data.get('total_credit', 0),
            data.get('journal_count', 0),
            data.get('company_id'),
            data.get('created_by')
        ))
        batch_id = cursor.lastrowid
        
        # Add items if provided
        if items:
            for item in items:
                db.execute("""
                    INSERT INTO finance_journal_batch_items (
                        batch_id, template_id, journal_date, reference,
                        description, total_debit, total_credit, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    batch_id,
                    item.get('template_id'),
                    item.get('journal_date'),
                    item.get('reference'),
                    item.get('description'),
                    item.get('total_debit', 0),
                    item.get('total_credit', 0),
                    item.get('status', 'Pending')
                ))
        
        db.commit()
        return batch_id


# ============================================================================
# RECURRING JOURNALS
# ============================================================================

def _create_recurring_journals_table():
    """Create recurring journals table."""
    if not table_exists('finance_recurring_journals'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS finance_recurring_journals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    template_id INTEGER,
                    journal_type TEXT DEFAULT 'General',
                    frequency TEXT DEFAULT 'Monthly',
                    next_date DATE NOT NULL,
                    last_generated_date DATE,
                    auto_post INTEGER DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    company_id INTEGER,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (template_id) REFERENCES finance_journal_templates(id)
                )
            """)
            db.execute("CREATE INDEX idx_rj_next ON finance_recurring_journals(next_date)")
            db.execute("CREATE INDEX idx_rj_active ON finance_recurring_journals(is_active)")
            db.commit()


def get_recurring_journals(company_id=None, is_active=True):
    """Get recurring journals."""
    sql = "SELECT * FROM finance_recurring_journals WHERE 1=1"
    params = []
    
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    if is_active is not None:
        sql += " AND is_active = ?"
        params.append(1 if is_active else 0)
    
    sql += " ORDER BY next_date"
    return get_all(sql, params)


def create_recurring_journal(data):
    """Create a recurring journal."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO finance_recurring_journals (
                name, description, template_id, journal_type,
                frequency, next_date, auto_post, is_active,
                company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('name'),
            data.get('description'),
            data.get('template_id'),
            data.get('journal_type', 'General'),
            data.get('frequency', 'Monthly'),
            data.get('next_date'),
            1 if data.get('auto_post') else 0,
            1 if data.get('is_active', True) else 0,
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# PROFIT CENTERS
# ============================================================================

def _create_profit_centers_table():
    """Create profit centers table."""
    if not table_exists('finance_profit_centers'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS finance_profit_centers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    name_ar TEXT,
                    description TEXT,
                    parent_id INTEGER,
                    manager_name TEXT,
                    department TEXT,
                    is_active INTEGER DEFAULT 1,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_id) REFERENCES finance_profit_centers(id),
                    FOREIGN KEY (company_id) REFERENCES companies(id)
                )
            """)
            db.execute("CREATE INDEX idx_pc_code ON finance_profit_centers(code)")
            db.execute("CREATE INDEX idx_pc_company ON finance_profit_centers(company_id)")
            db.execute("CREATE INDEX idx_pc_parent ON finance_profit_centers(parent_id)")
            db.commit()


def get_profit_centers(company_id=None, active_only=True, parent_id=None):
    """Get profit centers."""
    sql = "SELECT * FROM finance_profit_centers WHERE 1=1"
    params = []
    
    if company_id:
        sql += " AND (company_id = ? OR company_id IS NULL)"
        params.append(company_id)
    
    if active_only:
        sql += " AND is_active = 1"
    
    if parent_id is not None:
        sql += " AND parent_id = ?"
        params.append(parent_id)
    
    sql += " ORDER BY code"
    return get_all(sql, params)


def get_profit_center_by_id(pc_id):
    """Get profit center by ID."""
    return get_one("SELECT * FROM finance_profit_centers WHERE id = ?", (pc_id,))


def create_profit_center(data):
    """Create a profit center."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO finance_profit_centers (
                code, name, name_ar, description, parent_id,
                manager_name, department, is_active, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('code'),
            data.get('name'),
            data.get('name_ar'),
            data.get('description'),
            data.get('parent_id'),
            data.get('manager_name'),
            data.get('department'),
            1 if data.get('is_active', True) else 0,
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def get_profit_center_balance(pc_id, account_id=None):
    """Get profit center balance."""
    sql = """
        SELECT 
            COALESCE(SUM(CASE WHEN fjl.debit > 0 THEN fjl.debit ELSE 0 END), 0) as total_debit,
            COALESCE(SUM(CASE WHEN fjl.credit > 0 THEN fjl.credit ELSE 0 END), 0) as total_credit
        FROM finance_journal_lines fjl
        JOIN finance_journals fj ON fjl.journal_id = fj.id
        WHERE fj.status = 'Posted' AND fjl.cost_center_id = ?
    """
    params = [pc_id]
    
    if account_id:
        sql += " AND fjl.account_id = ?"
        params.append(account_id)
    
    result = get_one(sql, params)
    
    if result:
        debit = float(result['total_debit'] or 0)
        credit = float(result['total_credit'] or 0)
        return {'debit_total': debit, 'credit_total': credit, 'balance': debit - credit}
    
    return {'debit_total': 0, 'credit_total': 0, 'balance': 0}


# ============================================================================
# TAX RULES
# ============================================================================

def _create_tax_rules_table():
    """Create tax rules table."""
    if not table_exists('finance_tax_rules'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS finance_tax_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    tax_code_id INTEGER,
                    source_module TEXT,
                    transaction_type TEXT,
                    journal_type TEXT,
                    account_id INTEGER,
                    rate REAL DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    priority INTEGER DEFAULT 0,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tax_code_id) REFERENCES finance_tax_codes(id),
                    FOREIGN KEY (account_id) REFERENCES finance_accounts(id)
                )
            """)
            db.execute("CREATE INDEX idx_tr_active ON finance_tax_rules(is_active)")
            db.execute("CREATE INDEX idx_tr_priority ON finance_tax_rules(priority)")
            db.commit()


def get_tax_rules(company_id=None, is_active=True):
    """Get tax rules."""
    sql = """
        SELECT tr.*, tc.name as tax_code_name, fa.code as account_code, fa.name as account_name
        FROM finance_tax_rules tr
        LEFT JOIN finance_tax_codes tc ON tr.tax_code_id = tc.id
        LEFT JOIN finance_accounts fa ON tr.account_id = fa.id
        WHERE 1=1
    """
    params = []
    
    if company_id:
        sql += " AND (tr.company_id = ? OR tr.company_id IS NULL)"
        params.append(company_id)
    
    if is_active:
        sql += " AND tr.is_active = 1"
    
    sql += " ORDER BY tr.priority, tr.name"
    return get_all(sql, params)


def get_tax_rule_by_id(rule_id):
    """Get tax rule by ID."""
    return get_one("SELECT * FROM finance_tax_rules WHERE id = ?", (rule_id,))


def create_tax_rule(data):
    """Create a tax rule."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO finance_tax_rules (
                name, description, tax_code_id, source_module,
                transaction_type, journal_type, account_id,
                rate, is_active, priority, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('name'),
            data.get('description'),
            data.get('tax_code_id'),
            data.get('source_module'),
            data.get('transaction_type'),
            data.get('journal_type'),
            data.get('account_id'),
            data.get('rate', 0),
            1 if data.get('is_active', True) else 0,
            data.get('priority', 0),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def calculate_tax_by_rule(tax_code_id, amount, transaction_type=None, journal_type=None, company_id=None):
    """Calculate tax based on applicable rules."""
    sql = """
        SELECT tr.*, tc.name as tax_code_name, tc.rate as default_rate
        FROM finance_tax_rules tr
        LEFT JOIN finance_tax_codes tc ON tr.tax_code_id = tc.id
        WHERE tr.tax_code_id = ? AND tr.is_active = 1
    """
    params = [tax_code_id]
    
    rules = get_all(sql, params)
    
    # Find best matching rule
    applicable_rule = None
    for rule in rules:
        if transaction_type and rule.get('transaction_type') and rule['transaction_type'] != transaction_type:
            continue
        if journal_type and rule.get('journal_type') and rule['journal_type'] != journal_type:
            continue
        applicable_rule = rule
        break
    
    # Fall back to tax code default rate
    if not applicable_rule:
        tax_code = get_tax_code_by_id(tax_code_id)
        rate = tax_code.get('rate', 0) if tax_code else 0
    else:
        rate = applicable_rule.get('rate') or applicable_rule.get('default_rate', 0)
    
    tax_amount = amount * (rate / 100)
    
    return {
        'tax_code_id': tax_code_id,
        'rate': rate,
        'base_amount': amount,
        'tax_amount': tax_amount,
        'total': amount + tax_amount,
        'rule_id': applicable_rule['id'] if applicable_rule else None
    }


# ============================================================================
# INTERCOMPANY ACCOUNTING
# ============================================================================

def _create_intercompany_tables():
    """Create intercompany tables."""
    if not table_exists('finance_intercompany_transactions'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS finance_intercompany_transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_number TEXT UNIQUE NOT NULL,
                    transaction_date DATE NOT NULL,
                    from_company_id INTEGER,
                    to_company_id INTEGER,
                    from_bank_account_id INTEGER,
                    to_bank_account_id INTEGER,
                    amount REAL NOT NULL,
                    currency TEXT DEFAULT 'AED',
                    reference TEXT,
                    description TEXT,
                    status TEXT DEFAULT 'Pending',
                    journal_entry_id INTEGER,
                    company_id INTEGER,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (from_company_id) REFERENCES companies(id),
                    FOREIGN KEY (to_company_id) REFERENCES companies(id),
                    FOREIGN KEY (journal_entry_id) REFERENCES finance_journals(id)
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS finance_intercompany_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    from_company_id INTEGER,
                    to_company_id INTEGER,
                    rule_type TEXT,
                    debit_account_id INTEGER,
                    credit_account_id INTEGER,
                    is_active INTEGER DEFAULT 1,
                    priority INTEGER DEFAULT 0,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("CREATE INDEX idx_ic_from ON finance_intercompany_transactions(from_company_id)")
            db.execute("CREATE INDEX idx_ic_to ON finance_intercompany_transactions(to_company_id)")
            db.commit()


def get_intercompany_transactions(company_id=None):
    """Get intercompany transactions."""
    sql = """
        SELECT ic.*, 
               c_from.name as from_company_name,
               c_to.name as to_company_name,
               fb_from.account_name as from_account_name,
               fb_to.account_name as to_account_name
        FROM finance_intercompany_transactions ic
        LEFT JOIN companies c_from ON ic.from_company_id = c_from.id
        LEFT JOIN companies c_to ON ic.to_company_id = c_to.id
        LEFT JOIN finance_bank_accounts fb_from ON ic.from_bank_account_id = fb_from.id
        LEFT JOIN finance_bank_accounts fb_to ON ic.to_bank_account_id = fb_to.id
        WHERE 1=1
    """
    params = []
    
    if company_id:
        sql += " AND (ic.company_id = ? OR ic.from_company_id = ? OR ic.to_company_id = ?)"
        params.extend([company_id, company_id, company_id])
    
    sql += " ORDER BY ic.transaction_date DESC"
    return get_all(sql, params)


def create_intercompany_transaction(data):
    """Create an intercompany transaction."""
    with get_db_context() as db:
        # Generate transaction number
        result = db.execute("""
            SELECT MAX(CAST(SUBSTR(transaction_number, 5) AS INTEGER)) as max_num
            FROM finance_intercompany_transactions
            WHERE transaction_number LIKE 'IC-%'
        """).fetchone()
        next_num = (result['max_num'] or 0) + 1
        txn_number = f"IC-{next_num:05d}"
        
        cursor = db.execute("""
            INSERT INTO finance_intercompany_transactions (
                transaction_number, transaction_date,
                from_company_id, to_company_id,
                from_bank_account_id, to_bank_account_id,
                amount, currency, reference, description,
                status, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            txn_number,
            data.get('transaction_date'),
            data.get('from_company_id'),
            data.get('to_company_id'),
            data.get('from_bank_account_id'),
            data.get('to_bank_account_id'),
            data.get('amount'),
            data.get('currency', 'AED'),
            data.get('reference'),
            data.get('description'),
            data.get('status', 'Pending'),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


# ============================================================================
# COST ALLOCATION RULES
# ============================================================================

def _create_cost_allocation_rules_table():
    """Create cost allocation rules table."""
    if not table_exists('finance_cost_allocation_rules'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS finance_cost_allocation_rules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    from_center_id INTEGER,
                    to_center_id INTEGER,
                    account_id INTEGER,
                    allocation_method TEXT DEFAULT 'percentage',
                    allocation_value REAL DEFAULT 0,
                    is_active INTEGER DEFAULT 1,
                    priority INTEGER DEFAULT 0,
                    company_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (from_center_id) REFERENCES finance_cost_centers(id),
                    FOREIGN KEY (to_center_id) REFERENCES finance_cost_centers(id),
                    FOREIGN KEY (account_id) REFERENCES finance_accounts(id)
                )
            """)
            db.execute("CREATE INDEX idx_car_from ON finance_cost_allocation_rules(from_center_id)")
            db.execute("CREATE INDEX idx_car_to ON finance_cost_allocation_rules(to_center_id)")
            db.commit()


def get_cost_allocation_rules(company_id=None, is_active=True):
    """Get cost allocation rules."""
    sql = """
        SELECT car.*,
               cc_from.name as from_center_name,
               cc_to.name as to_center_name,
               fa.name as account_name
        FROM finance_cost_allocation_rules car
        LEFT JOIN finance_cost_centers cc_from ON car.from_center_id = cc_from.id
        LEFT JOIN finance_cost_centers cc_to ON car.to_center_id = cc_to.id
        LEFT JOIN finance_accounts fa ON car.account_id = fa.id
        WHERE 1=1
    """
    params = []
    
    if company_id:
        sql += " AND (car.company_id = ? OR car.company_id IS NULL)"
        params.append(company_id)
    
    if is_active:
        sql += " AND car.is_active = 1"
    
    sql += " ORDER BY car.priority"
    return get_all(sql, params)


# ============================================================================
# BANK RECONCILIATION SETS
# ============================================================================

def _create_bank_reconciliation_sets():
    """Create bank reconciliation sets."""
    if not table_exists('finance_bank_reconciliation_sets'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS finance_bank_reconciliation_sets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    set_number TEXT UNIQUE NOT NULL,
                    reconciliation_date DATE NOT NULL,
                    bank_account_id INTEGER,
                    statement_balance REAL DEFAULT 0,
                    gl_balance REAL DEFAULT 0,
                    difference REAL DEFAULT 0,
                    status TEXT DEFAULT 'Draft',
                    notes TEXT,
                    company_id INTEGER,
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (bank_account_id) REFERENCES finance_bank_accounts(id)
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS finance_reconciliation_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    set_id INTEGER NOT NULL,
                    item_type TEXT DEFAULT 'unmatched',
                    reference TEXT,
                    description TEXT,
                    date TEXT,
                    debit REAL DEFAULT 0,
                    credit REAL DEFAULT 0,
                    matched BOOLEAN DEFAULT 0,
                    matched_with_id INTEGER,
                    FOREIGN KEY (set_id) REFERENCES finance_bank_reconciliation_sets(id)
                )
            """)
            db.commit()


def create_reconciliation_set(data):
    """Create a reconciliation set."""
    with get_db_context() as db:
        # Generate set number
        result = db.execute("""
            SELECT MAX(CAST(SUBSTR(set_number, 5) AS INTEGER)) as max_num
            FROM finance_bank_reconciliation_sets
            WHERE set_number LIKE 'REC-%'
        """).fetchone()
        next_num = (result['max_num'] or 0) + 1
        set_number = f"REC-{next_num:05d}"
        
        cursor = db.execute("""
            INSERT INTO finance_bank_reconciliation_sets (
                set_number, reconciliation_date, bank_account_id,
                statement_balance, gl_balance, difference,
                status, notes, company_id, created_by
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            set_number,
            data.get('reconciliation_date'),
            data.get('bank_account_id'),
            data.get('statement_balance', 0),
            data.get('gl_balance', 0),
            data.get('difference', 0),
            data.get('status', 'Draft'),
            data.get('notes'),
            data.get('company_id'),
            data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


def get_reconciliation_sets(recon_type='bank', company_id=None):
    """Get reconciliation sets by type."""
    if recon_type == 'bank':
        return get_all("""
            SELECT rs.*, fb.account_name as bank_account_name,
                   (SELECT COUNT(*) FROM finance_reconciliation_items WHERE set_id = rs.id) as total_items,
                   (SELECT COUNT(*) FROM finance_reconciliation_items WHERE set_id = rs.id AND matched = 1) as matched_items
            FROM finance_bank_reconciliation_sets rs
            LEFT JOIN finance_bank_accounts fb ON rs.bank_account_id = fb.id
            WHERE rs.company_id = ?
            ORDER BY rs.reconciliation_date DESC
        """, (company_id,))
    elif recon_type == 'gl':
        return get_all("""
            SELECT * FROM finance_gl_reconciliation_sets
            WHERE company_id = ?
            ORDER BY reconciliation_date DESC
        """, (company_id,))
    elif recon_type == 'ar':
        return get_all("""
            SELECT * FROM finance_ar_reconciliation_sets
            WHERE company_id = ?
            ORDER BY reconciliation_date DESC
        """, (company_id,))
    elif recon_type == 'ap':
        return get_all("""
            SELECT * FROM finance_ap_reconciliation_sets
            WHERE company_id = ?
            ORDER BY reconciliation_date DESC
        """, (company_id,))
    return []


# ============================================================================
# FLOW ALERTS TABLE
# ============================================================================

def _create_flow_alerts_table():
    """Create finance flow alerts table."""
    if not table_exists('finance_flow_alerts'):
        with get_db_context() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS finance_flow_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL,
                    alert_data TEXT,
                    company_id INTEGER,
                    user_id INTEGER,
                    is_read INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.commit()


def create_finance_flow_alert(alert_type, alert_data, company_id=None, user_id=None):
    """Create a finance flow alert."""
    with get_db_context() as db:
        db.execute("""
            INSERT INTO finance_flow_alerts (alert_type, alert_data, company_id, user_id)
            VALUES (?, ?, ?, ?)
        """, (alert_type, str(alert_data), company_id, user_id))
        db.commit()


def get_finance_flow_alerts(company_id=None, user_id=None, is_read=None, limit=50):
    """Get finance flow alerts."""
    sql = "SELECT * FROM finance_flow_alerts WHERE 1=1"
    params = []
    
    if company_id:
        sql += " AND company_id = ?"
        params.append(company_id)
    
    if user_id:
        sql += " AND user_id = ?"
        params.append(user_id)
    
    if is_read is not None:
        sql += " AND is_read = ?"
        params.append(1 if is_read else 0)
    
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    
    return get_all(sql, params)


# ============================================================================
# INITIALIZATION
# ============================================================================

def initialize_finance_enhancement_tables():
    """Initialize all enhancement tables."""
    _create_close_tables()
    _create_journal_templates_tables()
    _create_recurring_journals_table()
    _create_profit_centers_table()
    _create_tax_rules_table()
    _create_intercompany_tables()
    _create_cost_allocation_rules_table()
    _create_bank_reconciliation_sets()
    _create_flow_alerts_table()
