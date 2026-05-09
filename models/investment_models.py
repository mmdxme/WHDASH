"""
Investment Management Module Database Models and Migrations
"""
import sqlite3
import os

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'warehouse.db'))

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

INVESTMENT_TABLES = [
    """CREATE TABLE IF NOT EXISTS investment_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE,
        description TEXT,
        parent_id INTEGER,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_portfolios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE,
        description TEXT,
        currency TEXT DEFAULT 'USD',
        total_budget REAL DEFAULT 0,
        total_approved REAL DEFAULT 0,
        status TEXT DEFAULT 'Active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_code TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        short_title TEXT,
        description TEXT,
        strategic_objective TEXT,
        business_need TEXT,
        category_id INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        department_id INTEGER,
        requesting_user_id INTEGER,
        sponsor_user_id INTEGER,
        owner_user_id INTEGER,
        currency TEXT DEFAULT 'USD',
        requested_budget REAL DEFAULT 0,
        approved_budget REAL DEFAULT 0,
        committed_amount REAL DEFAULT 0,
        actual_spent_amount REAL DEFAULT 0,
        forecast_remaining_amount REAL DEFAULT 0,
        total_expected_benefit REAL DEFAULT 0,
        annual_savings REAL DEFAULT 0,
        revenue_uplift REAL DEFAULT 0,
        cost_avoidance REAL DEFAULT 0,
        payback_period_months INTEGER,
        roi_percent REAL,
        irr_percent REAL,
        npv_amount REAL,
        hurdle_rate REAL DEFAULT 0.10,
        discount_rate REAL DEFAULT 0.10,
        risk_score REAL,
        strategic_score REAL,
        financial_score REAL,
        operational_score REAL,
        compliance_score REAL,
        weighted_total_score REAL,
        start_date DATE,
        target_end_date DATE,
        actual_end_date DATE,
        priority TEXT DEFAULT 'Medium',
        status TEXT DEFAULT 'Draft',
        lifecycle_stage TEXT DEFAULT 'Draft',
        funding_status TEXT DEFAULT 'Not Planned',
        approval_status TEXT DEFAULT 'Not Submitted',
        implementation_status TEXT DEFAULT 'Not Started',
        benefits_status TEXT DEFAULT 'Not Started',
        closure_status TEXT,
        revision_no INTEGER DEFAULT 1,
        created_by INTEGER,
        updated_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_versions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_id INTEGER NOT NULL,
        version_no INTEGER NOT NULL,
        change_summary TEXT,
        title TEXT,
        description TEXT,
        requested_budget REAL,
        approved_budget REAL,
        status TEXT,
        changed_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_evaluations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_id INTEGER NOT NULL,
        evaluation_date DATE,
        evaluator_user_id INTEGER,
        strategic_alignment_score REAL,
        financial_return_score REAL,
        urgency_score REAL,
        risk_score REAL,
        weighted_total_score REAL,
        recommendation TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_approval_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_id INTEGER NOT NULL,
        step_order INTEGER NOT NULL,
        step_name TEXT NOT NULL,
        approver_user_id INTEGER,
        approval_threshold REAL,
        status TEXT DEFAULT 'Pending',
        due_date DATETIME,
        completed_at DATETIME,
        comments TEXT,
        decision TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_approval_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_id INTEGER NOT NULL,
        step_id INTEGER,
        action TEXT NOT NULL,
        user_id INTEGER,
        comments TEXT,
        decision TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_funding_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_id INTEGER NOT NULL,
        schedule_date DATE NOT NULL,
        scheduled_amount REAL NOT NULL,
        released_amount REAL DEFAULT 0,
        withdrawn_amount REAL DEFAULT 0,
        funding_source TEXT,
        funding_type TEXT,
        reference TEXT,
        notes TEXT,
        status TEXT DEFAULT 'Planned',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_budget_allocations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_id INTEGER NOT NULL,
        fiscal_year INTEGER,
        company_id INTEGER,
        branch_id INTEGER,
        department_id INTEGER,
        cost_center_id INTEGER,
        allocated_amount REAL DEFAULT 0,
        reserved_amount REAL DEFAULT 0,
        released_amount REAL DEFAULT 0,
        spent_amount REAL DEFAULT 0,
        status TEXT DEFAULT 'Active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_cost_centers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_id INTEGER NOT NULL,
        cost_center_id INTEGER,
        profit_center_id INTEGER,
        allocation_percent REAL DEFAULT 100,
        allocated_amount REAL DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_milestones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_id INTEGER NOT NULL,
        milestone_name TEXT NOT NULL,
        description TEXT,
        owner_user_id INTEGER,
        due_date DATE,
        completed_date DATE,
        percent_complete REAL DEFAULT 0,
        status TEXT DEFAULT 'Pending',
        dependency_ids TEXT,
        blockers TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_benefits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_id INTEGER NOT NULL,
        benefit_name TEXT NOT NULL,
        benefit_type TEXT,
        description TEXT,
        target_value REAL,
        actual_value REAL,
        target_date DATE,
        review_date DATE,
        benefit_owner INTEGER,
        financial_benefit INTEGER DEFAULT 0,
        status TEXT DEFAULT 'Not Started',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_kpi_targets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_id INTEGER NOT NULL,
        kpi_name TEXT NOT NULL,
        target_value REAL,
        target_date DATE,
        measurement_unit TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_kpi_actuals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        kpi_target_id INTEGER NOT NULL,
        actual_value REAL,
        recorded_date DATE,
        recorded_by INTEGER,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_risks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_id INTEGER NOT NULL,
        risk_name TEXT NOT NULL,
        risk_category TEXT,
        description TEXT,
        probability TEXT,
        impact TEXT,
        risk_score REAL,
        mitigation_plan TEXT,
        contingency_plan TEXT,
        owner_user_id INTEGER,
        review_date DATE,
        status TEXT DEFAULT 'Active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_compliance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_id INTEGER NOT NULL,
        checklist_item TEXT NOT NULL,
        checklist_category TEXT,
        is_required INTEGER DEFAULT 0,
        is_completed INTEGER DEFAULT 0,
        completed_date DATE,
        completed_by INTEGER,
        evidence TEXT,
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_scenarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_id INTEGER NOT NULL,
        scenario_name TEXT NOT NULL,
        scenario_type TEXT,
        base_value REAL,
        optimistic_value REAL,
        pessimistic_value REAL,
        assumption_notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_cash_flows (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_id INTEGER NOT NULL,
        period_year INTEGER,
        period_month INTEGER,
        period_quarter INTEGER,
        cash_flow_type TEXT,
        planned_amount REAL,
        actual_amount REAL,
        variance_amount REAL,
        currency TEXT DEFAULT 'USD',
        notes TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_id INTEGER NOT NULL,
        document_name TEXT NOT NULL,
        document_type TEXT,
        file_path TEXT,
        file_size INTEGER,
        category TEXT,
        version_label TEXT,
        is_current INTEGER DEFAULT 1,
        uploaded_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_id INTEGER NOT NULL,
        comment_type TEXT DEFAULT 'Note',
        comment_text TEXT NOT NULL,
        parent_comment_id INTEGER,
        is_internal INTEGER DEFAULT 0,
        mentioned_user_ids TEXT,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_id INTEGER NOT NULL,
        reminder_type TEXT,
        reminder_text TEXT NOT NULL,
        due_date DATETIME,
        is_completed INTEGER DEFAULT 0,
        completed_at DATETIME,
        completed_by INTEGER,
        remind_user_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT UNIQUE NOT NULL,
        setting_value TEXT,
        setting_type TEXT,
        description TEXT,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS investment_audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        investment_id INTEGER,
        action TEXT NOT NULL,
        user_id INTEGER,
        changes TEXT,
        ip_address TEXT,
        user_agent TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""",
]

LIFECYCLE_STAGES = ['Draft', 'Submitted', 'Under Review', 'Needs Revision', 'Scored',
    'Pending Approval', 'Approved', 'Rejected', 'Deferred', 'On Hold',
    'Budget Reserved', 'Funding Released', 'In Execution', 'Partially Implemented',
    'Implemented', 'Under Benefit Review', 'Closed', 'Cancelled']

FUNDING_STATUSES = ['Not Planned', 'Planned', 'Partially Funded', 'Fully Funded',
    'Frozen', 'Released', 'Exhausted', 'Returned']

def init_investment_tables():
    conn = get_db()
    try:
        for table_sql in INVESTMENT_TABLES:
            conn.execute(table_sql)
        
        # Initialize defaults
        defaults = [
            ('investment_default_currency', 'USD', 'string', 'Default currency'),
            ('investment_default_discount_rate', '0.10', 'number', 'Default discount rate'),
            ('investment_number_prefix', 'INV', 'string', 'Investment code prefix'),
            ('investment_number_sequence', '1000', 'number', 'Starting sequence'),
        ]
        for key, value, vtype, desc in defaults:
            conn.execute("""
                INSERT OR IGNORE INTO investment_settings (setting_key, setting_value, setting_type, description)
                VALUES (?, ?, ?, ?)
            """, (key, value, vtype, desc))
        
        # Initialize categories
        categories = [
            ('Warehouse Expansion', 'EXP', 'Capital expansion for warehouse facilities'),
            ('Racking System', 'RACK', 'Storage racking and shelving systems'),
            ('Forklifts', 'FORK', 'Material handling equipment'),
            ('ERP Upgrade', 'ERP', 'Enterprise resource planning systems'),
            ('CCTV', 'CCTV', 'Security and surveillance systems'),
            ('Delivery Fleet', 'FLEET', 'Transportation and delivery vehicles'),
            ('Automation Equipment', 'AUTO', 'Process automation and robotics'),
            ('Office Fit-out', 'OFFICE', 'Office renovation and furnishing'),
            ('IT Infrastructure', 'IT', 'IT hardware and networking'),
            ('Training Platform', 'TRAIN', 'Employee training and development'),
            ('Quality Lab Equipment', 'LAB', 'Quality control laboratory equipment'),
            ('Energy Efficiency', 'ENERGY', 'Energy saving and sustainability'),
            ('Safety Equipment', 'SAFETY', 'Workplace safety equipment'),
            ('Software License', 'SOFT', 'Software licenses and subscriptions'),
            ('Consulting', 'CONSULT', 'Professional consulting services'),
        ]
        for name, code, desc in categories:
            conn.execute("""
                INSERT OR IGNORE INTO investment_categories (name, code, description)
                VALUES (?, ?, ?)
            """, (name, code, desc))
        
        conn.commit()
    finally:
        conn.close()

def get_investment_stats():
    conn = get_db()
    try:
        stats = {}
        stats['totals'] = conn.execute("""
            SELECT SUM(requested_budget) as total_requested,
                   SUM(approved_budget) as total_approved,
                   SUM(committed_amount) as total_committed,
                   SUM(actual_spent_amount) as total_spent
            FROM investment_requests
        """).fetchone() or {}
        
        cursor = conn.execute("""
            SELECT lifecycle_stage, COUNT(*) as count
            FROM investment_requests GROUP BY lifecycle_stage
        """)
        stats['by_stage'] = [dict(row) for row in cursor.fetchall()]
        
        cursor = conn.execute("""
            SELECT status, COUNT(*) as count
            FROM investment_requests GROUP BY status
        """)
        stats['by_status'] = [dict(row) for row in cursor.fetchall()]
        
        stats['pending_approvals'] = conn.execute("""
            SELECT COUNT(*) as count FROM investment_requests
            WHERE approval_status = 'Pending Approval'
        """).fetchone()['count']
        
        stats['avg_roi'] = conn.execute("""
            SELECT AVG(roi_percent) as avg_roi FROM investment_requests
            WHERE roi_percent IS NOT NULL
        """).fetchone()['avg_roi'] or 0
        
        return stats
    finally:
        conn.close()

def get_active_investments(filters=None):
    conn = get_db()
    try:
        sql = """
            SELECT i.*, c.name as category_name
            FROM investment_requests i
            LEFT JOIN investment_categories c ON i.category_id = c.id
            WHERE 1=1
        """
        params = []
        if filters:
            if filters.get('status'):
                sql += " AND i.status = ?"
                params.append(filters['status'])
            if filters.get('category_id'):
                sql += " AND i.category_id = ?"
                params.append(filters['category_id'])
            if filters.get('search'):
                sql += " AND (i.title LIKE ? OR i.investment_code LIKE ?)"
                search_term = f"%{filters['search']}%"
                params.extend([search_term, search_term])
        sql += " ORDER BY i.created_at DESC"
        cursor = conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()

def get_investment_by_id(investment_id):
    conn = get_db()
    try:
        investment = conn.execute("""
            SELECT i.*, c.name as category_name
            FROM investment_requests i
            LEFT JOIN investment_categories c ON i.category_id = c.id
            WHERE i.id = ?
        """, (investment_id,)).fetchone()
        
        if not investment:
            return None
        
        result = dict(investment)
        result['milestones'] = conn.execute("""
            SELECT * FROM investment_milestones WHERE investment_id = ? ORDER BY due_date
        """, (investment_id,)).fetchall()
        result['benefits'] = conn.execute("""
            SELECT * FROM investment_benefits WHERE investment_id = ?
        """, (investment_id,)).fetchall()
        result['risks'] = conn.execute("""
            SELECT * FROM investment_risks WHERE investment_id = ?
        """, (investment_id,)).fetchall()
        result['documents'] = conn.execute("""
            SELECT * FROM investment_documents WHERE investment_id = ? ORDER BY created_at DESC
        """, (investment_id,)).fetchall()
        result['funding_schedules'] = conn.execute("""
            SELECT * FROM investment_funding_schedules WHERE investment_id = ? ORDER BY schedule_date
        """, (investment_id,)).fetchall()
        result['approval_history'] = conn.execute("""
            SELECT ah.*, u.username as user_name
            FROM investment_approval_history ah
            LEFT JOIN users u ON ah.user_id = u.id
            WHERE ah.investment_id = ? ORDER BY ah.created_at DESC
        """, (investment_id,)).fetchall()
        return result
    finally:
        conn.close()

def get_next_investment_code():
    conn = get_db()
    try:
        prefix_row = conn.execute("SELECT setting_value FROM investment_settings WHERE setting_key = 'investment_number_prefix'").fetchone()
        seq_row = conn.execute("SELECT setting_value FROM investment_settings WHERE setting_key = 'investment_number_sequence'").fetchone()
        prefix = prefix_row['setting_value'] if prefix_row else 'INV'
        seq = int(seq_row['setting_value']) if seq_row else 1000
        conn.execute("UPDATE investment_settings SET setting_value = ? WHERE setting_key = 'investment_number_sequence'", (str(seq + 1),))
        conn.commit()
        return f"{prefix}{seq}"
    finally:
        conn.close()

def log_investment_audit(investment_id, action, user_id=None, changes=None):
    import json
    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO investment_audit_log (investment_id, action, user_id, changes, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (investment_id, action, user_id, json.dumps(changes) if changes else None))
        conn.commit()
    finally:
        conn.close()
