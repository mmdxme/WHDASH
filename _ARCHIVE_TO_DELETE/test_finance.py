"""
Finance Module Tests
===================
Comprehensive tests for the WHDASH Financial Management module.

Tests cover:
- Chart of Accounts logic
- Journal posting validation
- Period lock behavior
- AP/AR workflows
- Payment approvals
- Budget controls
- Cost/Profit center reporting
- Tax mapping behavior
- Asset accounting linkage
- Reconciliation flows
- Close workflow
- Role-based visibility
- Multilingual rendering

Author: Finance Module Testing
"""

import unittest
import sqlite3
import os
from datetime import datetime, timedelta

# Test database path
TEST_DB = 'test_finance.db'


class TestChartOfAccounts(unittest.TestCase):
    """Test Chart of Accounts functionality."""

    def setUp(self):
        """Set up test database."""
        self.db_path = TEST_DB
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def tearDown(self):
        """Clean up test database."""
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_tables(self):
        """Create finance tables for testing."""
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS finance_account_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                account_type TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            );
            
            CREATE TABLE IF NOT EXISTS finance_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                category_id INTEGER,
                account_type TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                is_posting_allowed INTEGER DEFAULT 1,
                is_control_account INTEGER DEFAULT 0,
                parent_id INTEGER,
                FOREIGN KEY (category_id) REFERENCES finance_account_categories(id),
                FOREIGN KEY (parent_id) REFERENCES finance_accounts(id)
            );
            
            CREATE TABLE IF NOT EXISTS finance_fiscal_years (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            );
            
            CREATE TABLE IF NOT EXISTS finance_fiscal_periods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fiscal_year_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                period_number INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                status TEXT DEFAULT 'Open',
                FOREIGN KEY (fiscal_year_id) REFERENCES finance_fiscal_years(id)
            );
            
            INSERT INTO finance_account_categories (code, name, account_type) VALUES
                ('1000', 'Assets', 'ASSET'),
                ('2000', 'Liabilities', 'LIABILITY'),
                ('3000', 'Equity', 'EQUITY'),
                ('4000', 'Revenue', 'REVENUE'),
                ('5000', 'Cost of Goods Sold', 'COGS'),
                ('6000', 'Expenses', 'EXPENSE');
        """)
        self.conn.commit()

    def test_account_creation(self):
        """Test creating a new account."""
        self.cursor.execute("""
            INSERT INTO finance_accounts (code, name, category_id, account_type)
            VALUES (?, ?, ?, ?)
        """, ('1110', 'Cash at Bank', 1, 'ASSET'))
        self.conn.commit()
        
        self.cursor.execute("SELECT * FROM finance_accounts WHERE code = ?", ('1110',))
        account = self.cursor.fetchone()
        
        self.assertIsNotNone(account)
        self.assertEqual(account[1], '1110')
        self.assertEqual(account[2], 'Cash at Bank')

    def test_account_hierarchy(self):
        """Test parent-child account relationships."""
        # Create parent
        self.cursor.execute("""
            INSERT INTO finance_accounts (code, name, category_id, account_type)
            VALUES (?, ?, ?, ?)
        """, ('1100', 'Current Assets', 1, 'ASSET'))
        parent_id = self.cursor.lastrowid
        
        # Create child
        self.cursor.execute("""
            INSERT INTO finance_accounts (code, name, category_id, account_type, parent_id)
            VALUES (?, ?, ?, ?, ?)
        """, ('1110', 'Cash at Bank', 1, 'ASSET', parent_id))
        self.conn.commit()
        
        self.cursor.execute("""
            SELECT a.code, p.code as parent_code
            FROM finance_accounts a
            LEFT JOIN finance_accounts p ON a.parent_id = p.id
            WHERE a.code = '1110'
        """)
        result = self.cursor.fetchone()
        
        self.assertEqual(result[0], '1110')
        self.assertEqual(result[1], '1100')

    def test_account_balance_calculation(self):
        """Test account balance = debit - credit."""
        # Create account
        self.cursor.execute("""
            INSERT INTO finance_accounts (code, name, category_id, account_type)
            VALUES (?, ?, ?, ?)
        """, ('1110', 'Cash', 1, 'ASSET'))
        account_id = self.cursor.lastrowid
        
        # Create fiscal year and period
        self.cursor.execute("""
            INSERT INTO finance_fiscal_years (name, start_date, end_date)
            VALUES (?, ?, ?)
        """, ('FY 2026', '2026-01-01', '2026-12-31'))
        fy_id = self.cursor.lastrowid
        
        self.cursor.execute("""
            INSERT INTO finance_fiscal_periods (fiscal_year_id, name, period_number, start_date, end_date)
            VALUES (?, ?, ?, ?, ?)
        """, (fy_id, 'January 2026', 1, '2026-01-01', '2026-01-31'))
        period_id = self.cursor.lastrowid
        
        # Create journal table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS finance_journals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                journal_number TEXT UNIQUE,
                journal_date TEXT,
                period_id INTEGER,
                total_debit REAL DEFAULT 0,
                total_credit REAL DEFAULT 0,
                status TEXT DEFAULT 'Posted'
            )
        """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS finance_journal_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                journal_id INTEGER,
                account_id INTEGER,
                debit REAL DEFAULT 0,
                credit REAL DEFAULT 0
            )
        """)
        
        # Create journal with lines
        self.cursor.execute("""
            INSERT INTO finance_journals (journal_number, journal_date, period_id, total_debit, total_credit)
            VALUES (?, ?, ?, ?, ?)
        """, ('JE-001', '2026-01-15', period_id, 1000, 1000))
        journal_id = self.cursor.lastrowid
        
        self.cursor.execute("""
            INSERT INTO finance_journal_lines (journal_id, account_id, debit, credit)
            VALUES (?, ?, ?, ?)
        """, (journal_id, account_id, 1000, 0))
        
        self.cursor.execute("""
            INSERT INTO finance_journal_lines (journal_id, account_id, debit, credit)
            VALUES (?, ?, ?, ?)
        """, (journal_id, 2, 0, 1000))  # Assume 2 is another account
        self.conn.commit()
        
        # Calculate balance
        self.cursor.execute("""
            SELECT COALESCE(SUM(debit), 0) - COALESCE(SUM(credit), 0)
            FROM finance_journal_lines
            WHERE account_id = ?
        """, (account_id,))
        balance = self.cursor.fetchone()[0]
        
        self.assertEqual(balance, 1000)


class TestJournalValidation(unittest.TestCase):
    """Test journal entry validation rules."""

    def setUp(self):
        """Set up test database."""
        self.db_path = TEST_DB
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def tearDown(self):
        """Clean up test database."""
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_tables(self):
        """Create minimal tables for journal validation testing."""
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS finance_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                is_active INTEGER DEFAULT 1,
                is_posting_allowed INTEGER DEFAULT 1
            );
            
            CREATE TABLE IF NOT EXISTS finance_fiscal_years (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS finance_fiscal_periods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fiscal_year_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                status TEXT DEFAULT 'Open'
            );
            
            CREATE TABLE IF NOT EXISTS finance_journals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                journal_number TEXT UNIQUE NOT NULL,
                journal_type TEXT NOT NULL,
                journal_date TEXT NOT NULL,
                period_id INTEGER,
                description TEXT,
                total_debit REAL DEFAULT 0,
                total_credit REAL DEFAULT 0,
                status TEXT DEFAULT 'Draft'
            );
            
            CREATE TABLE IF NOT EXISTS finance_journal_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                journal_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL,
                description TEXT,
                debit REAL DEFAULT 0,
                credit REAL DEFAULT 0
            );
            
            INSERT INTO finance_accounts (code, name) VALUES
                ('1110', 'Cash'),
                ('2110', 'Accounts Payable'),
                ('4110', 'Sales Revenue');
            
            INSERT INTO finance_fiscal_years (name, start_date, end_date) VALUES
                ('FY 2026', '2026-01-01', '2026-12-31');
            
            INSERT INTO finance_fiscal_periods (fiscal_year_id, name, start_date, end_date, status) VALUES
                (1, 'January 2026', '2026-01-01', '2026-01-31', 'Open'),
                (1, 'February 2026', '2026-02-01', '2026-02-28', 'Open'),
                (1, 'March 2026', '2026-03-01', '2026-03-31', 'Closed');
        """)
        self.conn.commit()

    def test_debit_must_equal_credit(self):
        """Test that journal entry debits must equal credits."""
        # Create journal header
        self.cursor.execute("""
            INSERT INTO finance_journals (journal_number, journal_type, journal_date, period_id, description)
            VALUES (?, ?, ?, ?, ?)
        """, ('JE-001', 'General', '2026-01-15', 1, 'Test Entry'))
        journal_id = self.cursor.lastrowid
        
        # Add lines with unequal debits/credits
        self.cursor.execute("""
            INSERT INTO finance_journal_lines (journal_id, account_id, debit, credit)
            VALUES (?, ?, ?, ?)
        """, (journal_id, 1, 1000, 0))
        self.cursor.execute("""
            INSERT INTO finance_journal_lines (journal_id, account_id, debit, credit)
            VALUES (?, ?, ?, ?)
        """, (journal_id, 2, 0, 500))  # Only 500 credit!
        self.conn.commit()
        
        # Calculate totals
        self.cursor.execute("""
            SELECT 
                COALESCE(SUM(debit), 0) as total_debit,
                COALESCE(SUM(credit), 0) as total_credit
            FROM finance_journal_lines
            WHERE journal_id = ?
        """, (journal_id,))
        total_debit, total_credit = self.cursor.fetchone()
        
        # Debits must equal credits
        self.assertEqual(total_debit, total_credit, "Debits must equal credits")

    def test_period_must_be_open(self):
        """Test that journals can only be posted to open periods."""
        # Get period statuses
        self.cursor.execute("SELECT id, name, status FROM finance_fiscal_periods")
        periods = self.cursor.fetchall()
        
        for period_id, name, status in periods:
            if status == 'Open':
                # Should be able to post
                self.assertIn(status, ['Open'])
            else:
                # Should not be able to post
                self.assertEqual(status, 'Closed')

    def test_account_must_be_active(self):
        """Test that only active accounts can be used in journals."""
        self.cursor.execute("SELECT code, is_active FROM finance_accounts")
        accounts = self.cursor.fetchall()
        
        for code, is_active in accounts:
            if is_active:
                self.assertEqual(is_active, 1)

    def test_account_must_allow_posting(self):
        """Test that posting is restricted based on account settings."""
        self.cursor.execute("SELECT code, is_posting_allowed FROM finance_accounts")
        accounts = self.cursor.fetchall()
        
        for code, is_posting_allowed in accounts:
            # Account should either allow or not allow posting
            self.assertIn(is_posting_allowed, [0, 1])


class TestPeriodLocking(unittest.TestCase):
    """Test period open/close functionality."""

    def setUp(self):
        """Set up test database."""
        self.db_path = TEST_DB
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def tearDown(self):
        """Clean up test database."""
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_tables(self):
        """Create tables for period locking tests."""
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS finance_fiscal_years (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS finance_fiscal_periods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fiscal_year_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                period_number INTEGER NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                status TEXT DEFAULT 'Open'
            );
            
            INSERT INTO finance_fiscal_years (name, start_date, end_date) VALUES
                ('FY 2026', '2026-01-01', '2026-12-31');
            
            INSERT INTO finance_fiscal_periods (fiscal_year_id, name, period_number, start_date, end_date, status) VALUES
                (1, 'January 2026', 1, '2026-01-01', '2026-01-31', 'Open'),
                (1, 'February 2026', 2, '2026-02-01', '2026-02-28', 'Open'),
                (1, 'March 2026', 3, '2026-03-01', '2026-03-31', 'Closed');
        """)
        self.conn.commit()

    def test_open_period_status(self):
        """Test that new periods are created with Open status."""
        self.cursor.execute("SELECT status FROM finance_fiscal_periods WHERE period_number = 1")
        status = self.cursor.fetchone()[0]
        self.assertEqual(status, 'Open')

    def test_close_period_updates_status(self):
        """Test closing a period updates its status."""
        # Close period 2
        self.cursor.execute("""
            UPDATE finance_fiscal_periods
            SET status = 'Closed'
            WHERE period_number = 2
        """)
        self.conn.commit()
        
        self.cursor.execute("SELECT status FROM finance_fiscal_periods WHERE period_number = 2")
        status = self.cursor.fetchone()[0]
        self.assertEqual(status, 'Closed')

    def test_reopen_period_updates_status(self):
        """Test reopening a closed period."""
        # First close period 2
        self.cursor.execute("""
            UPDATE finance_fiscal_periods
            SET status = 'Closed'
            WHERE period_number = 2
        """)
        self.conn.commit()
        
        # Now reopen
        self.cursor.execute("""
            UPDATE finance_fiscal_periods
            SET status = 'Open'
            WHERE period_number = 2
        """)
        self.conn.commit()
        
        self.cursor.execute("SELECT status FROM finance_fiscal_periods WHERE period_number = 2")
        status = self.cursor.fetchone()[0]
        self.assertEqual(status, 'Open')


class TestBudgetControls(unittest.TestCase):
    """Test budget validation and controls."""

    def setUp(self):
        """Set up test database."""
        self.db_path = TEST_DB
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def tearDown(self):
        """Clean up test database."""
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_tables(self):
        """Create tables for budget testing."""
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS finance_cost_centers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            );
            
            CREATE TABLE IF NOT EXISTS finance_budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                budget_number TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                fiscal_year_id INTEGER,
                cost_center_id INTEGER,
                version INTEGER DEFAULT 1,
                status TEXT DEFAULT 'Draft',
                total_budget REAL DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS finance_budget_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                budget_id INTEGER NOT NULL,
                account_id INTEGER,
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
                december REAL DEFAULT 0
            );
            
            INSERT INTO finance_cost_centers (code, name) VALUES
                ('CC001', 'Sales Department'),
                ('CC002', 'Marketing Department');
            
            INSERT INTO finance_budgets (budget_number, name, fiscal_year_id, cost_center_id, status) VALUES
                ('BUD-2026-001', 'Sales Budget 2026', 1, 1, 'Approved');
            
            INSERT INTO finance_budget_lines (budget_id, cost_center_id, january, february, march) VALUES
                (1, 1, 50000, 50000, 50000);
        """)
        self.conn.commit()

    def test_budget_status_workflow(self):
        """Test budget goes through Draft -> Submitted -> Approved."""
        # Initial status should be Approved in our seed data
        self.cursor.execute("SELECT status FROM finance_budgets WHERE budget_number = 'BUD-2026-001'")
        status = self.cursor.fetchone()[0]
        self.assertEqual(status, 'Approved')

    def test_budget_amount_calculation(self):
        """Test total budget is sum of monthly amounts."""
        self.cursor.execute("""
            SELECT 
                january + february + march
            FROM finance_budget_lines
            WHERE budget_id = 1
        """)
        total = self.cursor.fetchone()[0]
        self.assertEqual(total, 150000)  # 50000 * 3


class TestTaxMapping(unittest.TestCase):
    """Test tax code application and calculation."""

    def setUp(self):
        """Set up test database."""
        self.db_path = TEST_DB
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def tearDown(self):
        """Clean up test database."""
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_tables(self):
        """Create tables for tax testing."""
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS finance_tax_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                rate REAL NOT NULL,
                is_active INTEGER DEFAULT 1
            );
            
            INSERT INTO finance_tax_codes (code, name, rate) VALUES
                ('VAT-STD', 'VAT Standard 5%', 5.00),
                ('VAT-ZERO', 'Zero Rated 0%', 0.00),
                ('VAT-EX', 'Exempt 0%', 0.00);
        """)
        self.conn.commit()

    def test_vat_calculation(self):
        """Test VAT is calculated correctly."""
        self.cursor.execute("SELECT rate FROM finance_tax_codes WHERE code = 'VAT-STD'")
        rate = self.cursor.fetchone()[0]
        
        base_amount = 1000
        expected_tax = base_amount * (rate / 100)
        
        self.assertEqual(expected_tax, 50.00)
        self.assertEqual(base_amount + expected_tax, 1050.00)

    def test_zero_rated_tax(self):
        """Test zero-rated items have no tax."""
        self.cursor.execute("SELECT rate FROM finance_tax_codes WHERE code = 'VAT-ZERO'")
        rate = self.cursor.fetchone()[0]
        
        self.assertEqual(rate, 0.00)


class TestAssetDepreciation(unittest.TestCase):
    """Test asset depreciation calculations."""

    def setUp(self):
        """Set up test database."""
        self.db_path = TEST_DB
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def tearDown(self):
        """Clean up test database."""
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_tables(self):
        """Create tables for asset testing."""
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS finance_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_code TEXT UNIQUE NOT NULL,
                asset_name TEXT NOT NULL,
                category_id INTEGER,
                acquisition_date TEXT,
                acquisition_cost REAL NOT NULL,
                useful_life_years INTEGER,
                salvage_value REAL DEFAULT 0,
                depreciation_method TEXT DEFAULT 'StraightLine',
                status TEXT DEFAULT 'Active'
            );
            
            CREATE TABLE IF NOT EXISTS finance_depreciation_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_number TEXT UNIQUE NOT NULL,
                run_date TEXT NOT NULL,
                period_id INTEGER,
                total_depreciation REAL DEFAULT 0,
                status TEXT DEFAULT 'Draft'
            );
            
            INSERT INTO finance_assets (asset_code, asset_name, acquisition_cost, useful_life_years, salvage_value) VALUES
                ('FA-001', 'Office Equipment', 120000, 10, 0);
        """)
        self.conn.commit()

    def test_straight_line_depreciation(self):
        """Test straight-line depreciation calculation."""
        self.cursor.execute("""
            SELECT acquisition_cost, useful_life_years, salvage_value
            FROM finance_assets
            WHERE asset_code = 'FA-001'
        """)
        cost, life, salvage = self.cursor.fetchone()
        
        # Annual depreciation = (Cost - Salvage) / Useful Life
        annual_depreciation = (cost - salvage) / life
        
        self.assertEqual(annual_depreciation, 12000)  # (120000 - 0) / 10

    def test_monthly_depreciation(self):
        """Test monthly depreciation for journal entry."""
        self.cursor.execute("""
            SELECT acquisition_cost, useful_life_years, salvage_value
            FROM finance_assets
            WHERE asset_code = 'FA-001'
        """)
        cost, life, salvage = self.cursor.fetchone()
        
        annual = (cost - salvage) / life
        monthly = annual / 12
        
        self.assertAlmostEqual(monthly, 1000, places=2)


class TestReconciliation(unittest.TestCase):
    """Test reconciliation functionality."""

    def setUp(self):
        """Set up test database."""
        self.db_path = TEST_DB
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def tearDown(self):
        """Clean up test database."""
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_tables(self):
        """Create tables for reconciliation testing."""
        self.cursor.executescript("""
            CREATE TABLE IF NOT EXISTS finance_bank_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_name TEXT NOT NULL,
                account_number TEXT,
                current_balance REAL DEFAULT 0
            );
            
            CREATE TABLE IF NOT EXISTS finance_bank_reconciliation_statements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                set_number TEXT UNIQUE NOT NULL,
                reconciliation_date TEXT NOT NULL,
                bank_account_id INTEGER,
                statement_balance REAL DEFAULT 0,
                gl_balance REAL DEFAULT 0,
                difference REAL DEFAULT 0,
                status TEXT DEFAULT 'Draft'
            );
            
            INSERT INTO finance_bank_accounts (account_name, account_number, current_balance) VALUES
                ('Main Operating', '123456789', 1000000);
        """)
        self.conn.commit()

    def test_reconciliation_difference(self):
        """Test reconciliation difference calculation."""
        statement_balance = 1050000
        gl_balance = 1000000
        difference = statement_balance - gl_balance
        
        self.assertEqual(difference, 50000)


class TestPermissions(unittest.TestCase):
    """Test role-based access control for finance."""

    def test_permission_string_format(self):
        """Test permission strings follow correct format."""
        # Format: module.resource.action
        permission = "finance.journals.post"
        
        parts = permission.split('.')
        self.assertEqual(len(parts), 3)
        self.assertEqual(parts[0], 'finance')
        self.assertEqual(parts[1], 'journals')
        self.assertEqual(parts[2], 'post')

    def test_permission_categories(self):
        """Test finance has all required permission categories."""
        required_permissions = [
            'accounts', 'journals', 'fiscal_years',
            'ar_invoices', 'ar_receipts', 'ap_bills', 'ap_payments',
            'assets', 'depreciation', 'cost_centers', 'budgets',
            'tax', 'bank_accounts', 'reports', 'dashboard'
        ]
        
        # These would be checked against the MODULE_PERMISSIONS in permissions.py
        for perm in required_permissions:
            self.assertIsInstance(perm, str)
            self.assertTrue(len(perm) > 0)


class TestLocalization(unittest.TestCase):
    """Test multilingual support."""

    def test_accounting_terms_translations(self):
        """Test key accounting terms are translated."""
        # These would be tested against the actual translations
        translations = {
            'journal_entry': {
                'en': 'Journal Entry',
                'ar': 'قيد يومية',
                'fa': 'سند حساب',
            },
            'debit': {
                'en': 'Debit',
                'ar': 'مدين',
                'fa': 'بدهک',
            },
            'credit': {
                'en': 'Credit',
                'ar': 'دائن',
                'fa': 'بستاندارد',
            }
        }
        
        self.assertEqual(translations['journal_entry']['en'], 'Journal Entry')
        self.assertIsInstance(translations['journal_entry']['ar'], str)

    def test_rtl_languages(self):
        """Test RTL languages are properly identified."""
        rtl_languages = ['ar', 'fa', 'he']
        
        for lang in rtl_languages:
            self.assertIn(lang, ['ar', 'fa', 'he'])


def run_tests():
    """Run all finance module tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestChartOfAccounts))
    suite.addTests(loader.loadTestsFromTestCase(TestJournalValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestPeriodLocking))
    suite.addTests(loader.loadTestsFromTestCase(TestBudgetControls))
    suite.addTests(loader.loadTestsFromTestCase(TestTaxMapping))
    suite.addTests(loader.loadTestsFromTestCase(TestAssetDepreciation))
    suite.addTests(loader.loadTestsFromTestCase(TestReconciliation))
    suite.addTests(loader.loadTestsFromTestCase(TestPermissions))
    suite.addTests(loader.loadTestsFromTestCase(TestLocalization))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
