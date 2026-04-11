"""
Seed Finance Module Demo Data
================================
This script seeds realistic demo data for the Finance/Accounting module.
It creates Chart of Accounts, Fiscal Years, Journal Entries, Customer Invoices,
Supplier Bills, Receipts, Payments, Assets, Depreciation, Cost Centers,
Budgets, Tax Codes, and Bank/Cash accounts.

Run: python seed_finance_data.py
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

DB_PATH = os.path.join(os.path.dirname(__file__), 'warehouse.db')

# Import finance_models to initialize schema
from finance_models import initialize_finance_schema

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def seed_account_categories(conn):
    """Seed account categories based on standard accounting classification."""
    categories = [
        ('ASSET', 'Assets', '1', 1),
        ('LIABILITY', 'Liabilities', '2', 2),
        ('EQUITY', 'Equity', '3', 3),
        ('REVENUE', 'Revenue', '4', 4),
        ('COGS', 'Cost of Goods Sold', '5', 5),
        ('EXPENSE', 'Expenses', '6', 6),
        ('OTHER_INCOME', 'Other Income', '7', 7),
        ('OTHER_EXPENSE', 'Other Expenses', '8', 8),
    ]
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_account_categories")
    if cursor.fetchone()[0] > 0:
        print("- Account categories already exist, skipping")
        return
    
    for code, name, reporting_order, financial_statement in categories:
        cursor.execute("""
            INSERT INTO finance_account_categories 
            (category_code, category_name, description, reporting_order, financial_statement, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (code, name, f'{name} category', reporting_order, financial_statement))
    conn.commit()
    print("- Seeded account categories")

def seed_chart_of_accounts(conn):
    """Seed a comprehensive Chart of Accounts."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_accounts")
    if cursor.fetchone()[0] > 0:
        print("- Chart of accounts already exists, skipping")
        return
    
    # Get company for multi-company support
    cursor.execute("SELECT id FROM companies LIMIT 1")
    company = cursor.fetchone()
    company_id = company['id'] if company else 1
    
    # Get category IDs
    cursor.execute("SELECT id, code FROM finance_account_categories")
    cat_map = {row['code']: row['id'] for row in cursor.fetchall()}
    
    # Accounts: (code, name, account_type, category_id, parent_code, is_posting_allowed, is_control_account, is_cost_center_allowed)
    accounts = [
        # ASSETS (1000-1999)
        ('1000', 'Cash and Cash Equivalents', 'ASSET', cat_map.get('ASSET'), None, 1, 0, 1),
        ('1010', 'Cash on Hand', 'ASSET', cat_map.get('ASSET'), '1000', 1, 0, 1),
        ('1020', 'Cash at Bank - Current Account', 'ASSET', cat_map.get('ASSET'), '1000', 1, 1, 1),
        ('1030', 'Cash at Bank - Savings Account', 'ASSET', cat_map.get('ASSET'), '1000', 1, 0, 1),
        ('1100', 'Accounts Receivable', 'ASSET', cat_map.get('ASSET'), None, 1, 1, 1),
        ('1110', 'AR - Trade Customers', 'ASSET', cat_map.get('ASSET'), '1100', 1, 1, 1),
        ('1120', 'AR - Related Parties', 'ASSET', cat_map.get('ASSET'), '1100', 1, 0, 1),
        ('1130', 'AR - Employees', 'ASSET', cat_map.get('ASSET'), '1100', 1, 0, 1),
        ('1200', 'Inventory', 'ASSET', cat_map.get('ASSET'), None, 1, 0, 1),
        ('1210', 'Finished Goods', 'ASSET', cat_map.get('ASSET'), '1200', 1, 0, 1),
        ('1220', 'Work in Progress', 'ASSET', cat_map.get('ASSET'), '1200', 1, 0, 1),
        ('1230', 'Raw Materials', 'ASSET', cat_map.get('ASSET'), '1200', 1, 0, 1),
        ('1300', 'Prepaid Expenses', 'ASSET', cat_map.get('ASSET'), None, 1, 0, 1),
        ('1400', 'Fixed Assets', 'ASSET', cat_map.get('ASSET'), None, 1, 0, 0),
        ('1410', 'Land and Buildings', 'ASSET', cat_map.get('ASSET'), '1400', 1, 0, 0),
        ('1420', 'Office Equipment', 'ASSET', cat_map.get('ASSET'), '1400', 1, 0, 0),
        ('1430', 'Vehicles', 'ASSET', cat_map.get('ASSET'), '1400', 1, 0, 0),
        ('1440', 'Computer Equipment', 'ASSET', cat_map.get('ASSET'), '1400', 1, 0, 0),
        ('1500', 'Accumulated Depreciation', 'ASSET', cat_map.get('ASSET'), None, 1, 0, 0),
        ('1600', 'Intangible Assets', 'ASSET', cat_map.get('ASSET'), None, 1, 0, 0),
        ('1700', 'Deposits', 'ASSET', cat_map.get('ASSET'), None, 1, 0, 1),
        ('1800', 'VAT Receivable', 'ASSET', cat_map.get('ASSET'), None, 1, 0, 0),
        
        # LIABILITIES (2000-2999)
        ('2000', 'Current Liabilities', 'LIABILITY', cat_map.get('LIABILITY'), None, 1, 0, 1),
        ('2100', 'Accounts Payable', 'LIABILITY', cat_map.get('LIABILITY'), None, 1, 1, 1),
        ('2110', 'AP - Trade Suppliers', 'LIABILITY', cat_map.get('LIABILITY'), '2100', 1, 1, 1),
        ('2120', 'AP - Related Parties', 'LIABILITY', cat_map.get('LIABILITY'), '2100', 1, 0, 1),
        ('2200', 'Accrued Expenses', 'LIABILITY', cat_map.get('LIABILITY'), None, 1, 0, 1),
        ('2210', 'Salaries Payable', 'LIABILITY', cat_map.get('LIABILITY'), '2200', 1, 0, 1),
        ('2220', 'Interest Payable', 'LIABILITY', cat_map.get('LIABILITY'), '2200', 1, 0, 1),
        ('2230', 'Utilities Payable', 'LIABILITY', cat_map.get('LIABILITY'), '2200', 1, 0, 1),
        ('2300', 'Taxes Payable', 'LIABILITY', cat_map.get('LIABILITY'), None, 1, 0, 1),
        ('2310', 'VAT Payable', 'LIABILITY', cat_map.get('LIABILITY'), '2300', 1, 0, 1),
        ('2320', 'Income Tax Payable', 'LIABILITY', cat_map.get('LIABILITY'), '2300', 1, 0, 1),
        ('2330', 'Withholding Tax Payable', 'LIABILITY', cat_map.get('LIABILITY'), '2300', 1, 0, 1),
        ('2400', 'Deferred Revenue', 'LIABILITY', cat_map.get('LIABILITY'), None, 1, 0, 1),
        ('2500', 'Long-term Liabilities', 'LIABILITY', cat_map.get('LIABILITY'), None, 1, 0, 1),
        ('2510', 'Bank Loans', 'LIABILITY', cat_map.get('LIABILITY'), '2500', 1, 0, 1),
        ('2600', 'Customer Deposits', 'LIABILITY', cat_map.get('LIABILITY'), None, 1, 0, 1),
        
        # EQUITY (3000-3999)
        ('3000', 'Equity', 'EQUITY', cat_map.get('EQUITY'), None, 1, 0, 0),
        ('3100', 'Capital Stock', 'EQUITY', cat_map.get('EQUITY'), '3000', 1, 0, 0),
        ('3200', 'Retained Earnings', 'EQUITY', cat_map.get('EQUITY'), '3000', 1, 0, 0),
        ('3300', 'Current Year Earnings', 'EQUITY', cat_map.get('EQUITY'), '3000', 1, 0, 0),
        ('3400', 'Owner Drawings', 'EQUITY', cat_map.get('EQUITY'), '3000', 1, 0, 0),
        
        # REVENUE (4000-4999)
        ('4000', 'Revenue', 'REVENUE', cat_map.get('REVENUE'), None, 1, 0, 1),
        ('4100', 'Sales Revenue', 'REVENUE', cat_map.get('REVENUE'), None, 1, 0, 1),
        ('4110', 'Product Sales', 'REVENUE', cat_map.get('REVENUE'), '4100', 1, 0, 1),
        ('4120', 'Service Revenue', 'REVENUE', cat_map.get('REVENUE'), '4100', 1, 0, 1),
        ('4130', 'Wholesale Sales', 'REVENUE', cat_map.get('REVENUE'), '4100', 1, 0, 1),
        ('4200', 'Other Revenue', 'REVENUE', cat_map.get('REVENUE'), None, 1, 0, 1),
        ('4210', 'Interest Income', 'REVENUE', cat_map.get('REVENUE'), '4200', 1, 0, 1),
        ('4220', 'Commission Income', 'REVENUE', cat_map.get('REVENUE'), '4200', 1, 0, 1),
        ('4300', 'Sales Returns', 'REVENUE', cat_map.get('REVENUE'), None, 1, 0, 1),
        ('4400', 'Sales Discounts', 'REVENUE', cat_map.get('REVENUE'), None, 1, 0, 1),
        
        # COST OF GOODS SOLD (5000-5999)
        ('5000', 'Cost of Goods Sold', 'COGS', cat_map.get('COGS'), None, 1, 0, 1),
        ('5100', 'Cost of Products Sold', 'COGS', cat_map.get('COGS'), None, 1, 0, 1),
        ('5110', 'Direct Material Cost', 'COGS', cat_map.get('COGS'), '5100', 1, 0, 1),
        ('5120', 'Direct Labor Cost', 'COGS', cat_map.get('COGS'), '5100', 1, 0, 1),
        ('5130', 'Manufacturing Overhead', 'COGS', cat_map.get('COGS'), '5100', 1, 0, 1),
        ('5200', 'Inventory Adjustment', 'COGS', cat_map.get('COGS'), None, 1, 0, 1),
        
        # EXPENSES (6000-6999)
        ('6000', 'Operating Expenses', 'EXPENSE', cat_map.get('EXPENSE'), None, 1, 0, 1),
        ('6100', 'Selling Expenses', 'EXPENSE', cat_map.get('EXPENSE'), None, 1, 0, 1),
        ('6110', 'Advertising', 'EXPENSE', cat_map.get('EXPENSE'), '6100', 1, 0, 1),
        ('6120', 'Sales Commissions', 'EXPENSE', cat_map.get('EXPENSE'), '6100', 1, 0, 1),
        ('6130', 'Travel and Entertainment', 'EXPENSE', cat_map.get('EXPENSE'), '6100', 1, 0, 1),
        ('6200', 'General and Administrative', 'EXPENSE', cat_map.get('EXPENSE'), None, 1, 0, 1),
        ('6210', 'Salaries and Wages', 'EXPENSE', cat_map.get('EXPENSE'), '6200', 1, 0, 1),
        ('6220', 'Rent Expense', 'EXPENSE', cat_map.get('EXPENSE'), '6200', 1, 0, 1),
        ('6230', 'Utilities Expense', 'EXPENSE', cat_map.get('EXPENSE'), '6200', 1, 0, 1),
        ('6240', 'Insurance Expense', 'EXPENSE', cat_map.get('EXPENSE'), '6200', 1, 0, 1),
        ('6250', 'Office Supplies', 'EXPENSE', cat_map.get('EXPENSE'), '6200', 1, 0, 1),
        ('6260', 'Professional Fees', 'EXPENSE', cat_map.get('EXPENSE'), '6200', 1, 0, 1),
        ('6300', 'Depreciation Expense', 'EXPENSE', cat_map.get('EXPENSE'), None, 1, 0, 1),
        ('6400', 'Bank Charges', 'EXPENSE', cat_map.get('EXPENSE'), None, 1, 0, 1),
        ('6500', 'Communication Expense', 'EXPENSE', cat_map.get('EXPENSE'), None, 1, 0, 1),
        ('6600', 'IT Expenses', 'EXPENSE', cat_map.get('EXPENSE'), None, 1, 0, 1),
        ('6700', 'Maintenance and Repairs', 'EXPENSE', cat_map.get('EXPENSE'), None, 1, 0, 1),
        ('6800', 'Training and Development', 'EXPENSE', cat_map.get('EXPENSE'), None, 1, 0, 1),
        
        # OTHER INCOME (7000-7999)
        ('7000', 'Other Income', 'OTHER_INCOME', cat_map.get('OTHER_INCOME'), None, 1, 0, 1),
        ('7100', 'Interest Income', 'OTHER_INCOME', cat_map.get('OTHER_INCOME'), '7000', 1, 0, 1),
        ('7200', 'Gain on Asset Disposal', 'OTHER_INCOME', cat_map.get('OTHER_INCOME'), '7000', 1, 0, 1),
        ('7300', 'Rental Income', 'OTHER_INCOME', cat_map.get('OTHER_INCOME'), '7000', 1, 0, 1),
        
        # OTHER EXPENSES (8000-8999)
        ('8000', 'Other Expenses', 'OTHER_EXPENSE', cat_map.get('OTHER_EXPENSE'), None, 1, 0, 1),
        ('8100', 'Interest Expense', 'OTHER_EXPENSE', cat_map.get('OTHER_EXPENSE'), '8000', 1, 0, 1),
        ('8200', 'Loss on Asset Disposal', 'OTHER_EXPENSE', cat_map.get('OTHER_EXPENSE'), '8000', 1, 0, 1),
        ('8300', 'Charitable Contributions', 'OTHER_EXPENSE', cat_map.get('OTHER_EXPENSE'), '8000', 1, 0, 1),
        ('8400', 'Penalties and Fines', 'OTHER_EXPENSE', cat_map.get('OTHER_EXPENSE'), '8000', 1, 0, 1),
    ]
    
    # First pass: insert all accounts to get IDs
    code_to_id = {}
    for code, name, acc_type, cat_id, parent_code, posting, control, cc_allowed in accounts:
        parent_id = code_to_id.get(parent_code) if parent_code else None
        cursor.execute("""
            INSERT INTO finance_accounts 
            (code, name, account_type, category_id, parent_id, 
             is_active, is_posting_allowed, is_control_account, is_cost_center_allowed, company_id)
            VALUES (?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
        """, (code, name, acc_type, cat_id, parent_id, posting, control, cc_allowed, company_id))
        code_to_id[code] = cursor.lastrowid
    
    conn.commit()
    print("- Seeded Chart of Accounts")

def seed_fiscal_years(conn):
    """Seed fiscal years and periods."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_fiscal_years")
    if cursor.fetchone()[0] > 0:
        print("- Fiscal years already exist, skipping")
        return
    
    now = datetime.now()
    fiscal_years_data = [
        ('FY 2024', f'{now.year-2}-01-01', f'{now.year-2}-12-31'),
        ('FY 2025', f'{now.year-1}-01-01', f'{now.year-1}-12-31'),
        ('FY 2026', f'{now.year}-01-01', f'{now.year}-12-31'),
    ]
    
    for fy_name, start, end in fiscal_years_data:
        cursor.execute("""
            INSERT INTO finance_fiscal_years (name, start_date, end_date, company_id)
            VALUES (?, ?, ?, 1)
        """, (fy_name, start, end))
        fy_id = cursor.lastrowid
        
        # Create 12 monthly periods
        year = int(start[:4])
        is_current_year = (year == now.year)
        for month in range(1, 13):
            period_start = f'{year}-{month:02d}-01'
            if month == 12:
                period_end = f'{year}-12-31'
            else:
                next_month = month + 1
                period_end = f'{year}-{next_month:02d}-01'
                period_end = (datetime.strptime(period_end, '%Y-%m-%d') - timedelta(days=1)).strftime('%Y-%m-%d')
            
            # For past years, close all periods. For current year, keep open.
            period_status = 'Open' if is_current_year else 'Closed'
            cursor.execute("""
                INSERT INTO finance_fiscal_periods 
                (fiscal_year_id, name, period_number, start_date, end_date, status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (fy_id, f'{fy_name} P{month:02d}', month, period_start, period_end, period_status))
    
    conn.commit()
    print("- Seeded fiscal years and periods")

def seed_tax_codes(conn):
    """Seed tax codes for VAT and other taxes."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_tax_codes")
    if cursor.fetchone()[0] > 0:
        print("- Tax codes already exist, skipping")
        return
    
    # Tax codes will be seeded by the finance_models initialization, but we can add more
    additional_tax_codes = [
        ('VAT-STD', 'Standard VAT 15%', 'VAT', 15.00, 'Output'),
        ('VAT-ZERO', 'Zero Rated VAT 0%', 'VAT', 0.00, 'Output'),
        ('VAT-EX', 'Exempt VAT 0%', 'VAT', 0.00, 'Exempt'),
        ('TAX-5', 'Sales Tax 5%', 'Sales Tax', 5.00, 'Output'),
        ('TAX-10', 'Service Tax 10%', 'Service Tax', 10.00, 'Output'),
        ('CUST-5', 'Customs Duty 5%', 'Customs', 5.00, 'Input'),
        ('CUST-10', 'Customs Duty 10%', 'Customs', 10.00, 'Input'),
        ('NO-TX', 'No Tax', 'None', 0.00, 'Exempt'),
    ]
    
    # Check if already seeded
    cursor.execute("SELECT COUNT(*) FROM finance_tax_codes")
    if cursor.fetchone()[0] == 0:
        for code, name, tax_type, rate, category in additional_tax_codes:
            cursor.execute("""
                INSERT INTO finance_tax_codes 
                (code, name, tax_type, rate, is_inclusive, is_active, company_id)
                VALUES (?, ?, ?, ?, 0, 1, 1)
            """, (code, name, tax_type, rate))
    
    conn.commit()
    print("- Seeded tax codes")

def seed_cost_centers(conn):
    """Seed cost centers."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_cost_centers")
    if cursor.fetchone()[0] > 0:
        print("- Cost centers already exist, skipping")
        return
    
    cost_centers = [
        ('CC-001', 'Executive Office', 'Executive', 'Ahmed Hassan', 1, 1),
        ('CC-002', 'Finance Department', 'Finance', 'Fatima Ali', 1, 1),
        ('CC-003', 'Sales and Marketing', 'Sales', 'Omar Khalid', 1, 1),
        ('CC-004', 'Operations', 'Operations', 'Sara Mohammed', 1, 1),
        ('CC-005', 'Human Resources', 'HR', 'Youssef Ibrahim', 1, 1),
        ('CC-006', 'IT Department', 'IT', 'Layla Ahmed', 1, 1),
        ('CC-007', 'Warehouse', 'Warehouse', 'Karim Nasser', 1, 1),
        ('CC-008', 'Procurement', 'Procurement', 'Noor Hassan', 1, 1),
    ]
    
    for cc in cost_centers:
        cursor.execute("""
            INSERT INTO finance_cost_centers 
            (code, name, department, manager_name, company_id, is_active)
            VALUES (?, ?, ?, ?, ?, ?)
        """, cc)
    
    conn.commit()
    print("- Seeded cost centers")

def seed_journal_entries(conn):
    """Seed journal entries with proper double-entry bookkeeping."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_journals")
    if cursor.fetchone()[0] > 0:
        print("- Journal entries already exist, skipping")
        return
    
    # Get account IDs
    def get_account_id(acc_code):
        cursor.execute("SELECT id FROM finance_accounts WHERE code = ?", (acc_code,))
        result = cursor.fetchone()
        return result['id'] if result else None
    
    # Get fiscal period for current year
    cursor.execute("""
        SELECT id FROM finance_fiscal_periods 
        WHERE strftime('%Y', start_date) = strftime('%Y', 'now')
        AND period_number = strftime('%m', 'now')
    """)
    period = cursor.fetchone()
    period_id = period['id'] if period else 1
    
    # Journal 1: Record sales (debit cash, credit revenue)
    cash_id = get_account_id('1020')
    sales_id = get_account_id('4110')
    cogs_id = get_account_id('5110')
    inventory_id = get_account_id('1210')
    vat_id = get_account_id('2310')
    
    if all([cash_id, sales_id, cogs_id, inventory_id, vat_id]):
        cursor.execute("""
            INSERT INTO finance_journals 
            (journal_number, journal_type, journal_date, description, reference, source_module,
             status, period_id, company_id, created_by, total_debit, total_credit)
            VALUES ('JE-2026-001', 'Sales', date('now', '-45 days'), 'Cash Sales - Invoice #INV-001', 'INV-001', 'Sales',
                    'Posted', ?, 1, 1, 11500, 11500)
        """, (period_id,))
        je_id = cursor.lastrowid
        
        # Debit Cash
        cursor.execute("""
            INSERT INTO finance_journal_lines 
            (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
            VALUES (?, 1, ?, 'Cash received from customer', 11500, 0, NULL)
        """, (je_id, cash_id))
        
        # Credit VAT Payable
        cursor.execute("""
            INSERT INTO finance_journal_lines 
            (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
            VALUES (?, 2, ?, 'Output VAT collected', 0, 1500, NULL)
        """, (je_id, vat_id))
        
        # Credit Revenue
        cursor.execute("""
            INSERT INTO finance_journal_lines 
            (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
            VALUES (?, 3, ?, 'Sales revenue', 0, 10000, NULL)
        """, (je_id, sales_id))
        
        # Debit COGS
        cursor.execute("""
            INSERT INTO finance_journal_lines 
            (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
            VALUES (?, 4, ?, 'Cost of goods sold', 6000, 0, NULL)
        """, (je_id, cogs_id))
        
        # Credit Inventory
        cursor.execute("""
            INSERT INTO finance_journal_lines 
            (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
            VALUES (?, 5, ?, 'Inventory delivered', 0, 6000, NULL)
        """, (je_id, inventory_id))
    
    # Journal 2: Pay rent expense
    rent_exp_id = get_account_id('6220')
    cash_pay_id = get_account_id('1020')
    
    if all([rent_exp_id, cash_pay_id]):
        cursor.execute("""
            INSERT INTO finance_journals 
            (journal_number, journal_type, journal_date, description, reference, source_module,
             status, period_id, company_id, created_by, total_debit, total_credit)
            VALUES ('JE-2026-002', 'Payment', date('now', '-30 days'), 'Rent Payment - January 2026', 'RV-2026-001', 'Manual',
                    'Posted', ?, 1, 1, 25000, 25000)
        """, (period_id,))
        je_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO finance_journal_lines 
            (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
            VALUES (?, 1, ?, 'January rent expense', 25000, 0, 1)
        """, (je_id, rent_exp_id))
        
        cursor.execute("""
            INSERT INTO finance_journal_lines 
            (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
            VALUES (?, 2, ?, 'Cash paid to landlord', 0, 25000, NULL)
        """, (je_id, cash_pay_id))
    
    # Journal 3: Pay salaries
    salary_exp_id = get_account_id('6210')
    salary_pay_id = get_account_id('2210')
    
    if all([salary_exp_id, salary_pay_id]):
        cursor.execute("""
            INSERT INTO finance_journals 
            (journal_number, journal_type, journal_date, description, reference, source_module,
             status, period_id, company_id, created_by, total_debit, total_credit)
            VALUES ('JE-2026-003', 'Payroll', date('now', '-20 days'), 'Salaries - January 2nd half', 'SAL-2026-001', 'Payroll',
                    'Posted', ?, 1, 1, 85000, 85000)
        """, (period_id,))
        je_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO finance_journal_lines 
            (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
            VALUES (?, 1, ?, 'Salary expense', 85000, 0, 1)
        """, (je_id, salary_exp_id))
        
        cursor.execute("""
            INSERT INTO finance_journal_lines 
            (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
            VALUES (?, 2, ?, 'Salaries payable', 0, 85000, NULL)
        """, (je_id, salary_pay_id))
    
    # Journal 4: Purchase fixed asset
    computer_eq_id = get_account_id('1440')
    cash_purch_id = get_account_id('1020')
    
    if all([computer_eq_id, cash_purch_id]):
        cursor.execute("""
            INSERT INTO finance_journals 
            (journal_number, journal_type, journal_date, description, reference, source_module,
             status, period_id, company_id, created_by, total_debit, total_credit)
            VALUES ('JE-2026-004', 'Purchase', date('now', '-15 days'), 'Purchase of Laptop - Dell XPS 15', 'PO-2026-001', 'Purchase',
                    'Posted', ?, 1, 1, 8500, 8500)
        """, (period_id,))
        je_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO finance_journal_lines 
            (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
            VALUES (?, 1, ?, 'Computer equipment - Dell XPS 15', 8500, 0, 6)
        """, (je_id, computer_eq_id))
        
        cursor.execute("""
            INSERT INTO finance_journal_lines 
            (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
            VALUES (?, 2, ?, 'Payment to supplier', 0, 8500, NULL)
        """, (je_id, cash_purch_id))
    
    # Journal 5: Utility bill
    util_exp_id = get_account_id('6230')
    util_pay_id = get_account_id('2210')
    vat_recv_id = get_account_id('1800')
    
    if all([util_exp_id, util_pay_id, vat_recv_id]):
        cursor.execute("""
            INSERT INTO finance_journals 
            (journal_number, journal_type, journal_date, description, reference, source_module,
             status, period_id, company_id, created_by, total_debit, total_credit)
            VALUES ('JE-2026-005', 'Utility', date('now', '-10 days'), 'DEWA Bill - February 2026', 'DEWA-2026-002', 'Utility',
                    'Posted', ?, 1, 1, 4025, 4025)
        """, (period_id,))
        je_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO finance_journal_lines 
            (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
            VALUES (?, 1, ?, 'Electricity and water', 3500, 0, 1)
        """, (je_id, util_exp_id))
        
        cursor.execute("""
            INSERT INTO finance_journal_lines 
            (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
            VALUES (?, 2, ?, 'Input VAT claimed', 525, 0, NULL)
        """, (je_id, vat_recv_id))
        
        cursor.execute("""
            INSERT INTO finance_journal_lines 
            (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
            VALUES (?, 3, ?, 'Utilities payable', 0, 4025, NULL)
        """, (je_id, util_pay_id))
    
    # Journal 6: Customer invoice (AR)
    ar_trade_id = get_account_id('1110')
    sales_rev_id = get_account_id('4110')
    vat_pay_id = get_account_id('2310')
    
    if all([ar_trade_id, sales_rev_id, vat_pay_id]):
        cursor.execute("""
            INSERT INTO finance_journals 
            (journal_number, journal_type, journal_date, description, reference, source_module,
             status, period_id, company_id, created_by, total_debit, total_credit)
            VALUES ('JE-2026-006', 'Sales', date('now', '-5 days'), 'Invoice #INV-2026-002 - Al Fardan Trading', 'INV-2026-002', 'Sales',
                    'Posted', ?, 1, 1, 34500, 34500)
        """, (period_id,))
        je_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO finance_journal_lines 
            (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
            VALUES (?, 1, ?, 'Trade receivable - Al Fardan', 34500, 0, 3)
        """, (je_id, ar_trade_id))
        
        cursor.execute("""
            INSERT INTO finance_journal_lines 
            (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
            VALUES (?, 2, ?, 'Output VAT', 0, 4500, NULL)
        """, (je_id, vat_pay_id))
        
        cursor.execute("""
            INSERT INTO finance_journal_lines 
            (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
            VALUES (?, 3, ?, 'Product sales', 0, 30000, NULL)
        """, (je_id, sales_rev_id))
    
    conn.commit()
    print("- Seeded journal entries")

def seed_ar_invoices(conn):
    """Seed AR customer invoices."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_customer_invoices")
    if cursor.fetchone()[0] > 0:
        print("- AR invoices already exist, skipping")
        return
    
    # Get customer IDs
    cursor.execute("SELECT id, name as customer_name FROM customers LIMIT 5")
    customers = cursor.fetchall()
    
    # Get AR account
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '1110'")
    ar_account = cursor.fetchone()
    ar_account_id = ar_account['id'] if ar_account else 1
    
    # Get revenue account
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '4110'")
    rev_account = cursor.fetchone()
    rev_account_id = rev_account['id'] if rev_account else 1
    
    # Get tax code
    cursor.execute("SELECT id FROM finance_tax_codes WHERE code = 'VAT-STD'")
    tax = cursor.fetchone()
    tax_id = tax['id'] if tax else 1
    
    # Get period
    cursor.execute("""
        SELECT id FROM finance_fiscal_periods 
        WHERE strftime('%Y', start_date) = strftime('%Y', 'now')
        AND period_number = strftime('%m', 'now')
    """)
    period = cursor.fetchone()
    period_id = period['id'] if period else 1
    
    customer_ids = [c['id'] for c in customers]
    
    invoices = [
        (f'INV-2026-001', customer_ids[0] if len(customer_ids) > 0 else 1, 50000.00, 7500.00, date_delta(45), date_delta(15), 'Posted'),
        (f'INV-2026-002', customer_ids[1] if len(customer_ids) > 1 else 1, 30000.00, 4500.00, date_delta(30), date_delta(0), 'Posted'),
        (f'INV-2026-003', customer_ids[2] if len(customer_ids) > 2 else 1, 75000.00, 11250.00, date_delta(20), date_delta(-10), 'Posted'),
        (f'INV-2026-004', customer_ids[3] if len(customer_ids) > 3 else 1, 100000.00, 15000.00, date_delta(15), date_delta(-5), 'Posted'),
        (f'INV-2026-005', customer_ids[4] if len(customer_ids) > 4 else 1, 40000.00, 6000.00, date_delta(10), date_delta(-20), 'Posted'),
    ]
    
    for inv_num, cust_id, subtotal, tax_amt, inv_date, due, status in invoices:
        total = subtotal + tax_amt
        cursor.execute("""
            INSERT INTO finance_customer_invoices 
            (invoice_number, customer_id, invoice_date, due_date, subtotal, tax_amount, total_amount,
             amount_paid, amount_due, currency, status, receivable_account_id, revenue_account_id, 
             tax_code_id, period_id, company_id, payment_terms)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, 'AED', ?, ?, ?, ?, ?, 1, 'Net 30')
        """, (inv_num, cust_id, inv_date, due, subtotal, tax_amt, total, total, status, ar_account_id, rev_account_id, tax_id, period_id))
    
    conn.commit()
    print("- Seeded AR invoices")

def date_delta(days):
    return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

def seed_ap_bills(conn):
    """Seed AP supplier bills."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_supplier_bills")
    if cursor.fetchone()[0] > 0:
        print("- AP bills already exist, skipping")
        return
    
    # Get supplier IDs
    cursor.execute("SELECT id, name as supplier_name FROM suppliers LIMIT 5")
    suppliers = cursor.fetchall()
    
    # Get AP account
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '2110'")
    ap_account = cursor.fetchone()
    ap_account_id = ap_account['id'] if ap_account else 1
    
    # Get expense account
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '5110'")
    exp_account = cursor.fetchone()
    exp_account_id = exp_account['id'] if exp_account else 1
    
    # Get tax code
    cursor.execute("SELECT id FROM finance_tax_codes WHERE code = 'VAT-STD'")
    tax = cursor.fetchone()
    tax_id = tax['id'] if tax else 1
    
    # Get period
    cursor.execute("""
        SELECT id FROM finance_fiscal_periods 
        WHERE strftime('%Y', start_date) = strftime('%Y', 'now')
        AND period_number = strftime('%m', 'now')
    """)
    period = cursor.fetchone()
    period_id = period['id'] if period else 1
    
    supplier_ids = [s['id'] for s in suppliers]
    
    bills = [
        (f'BILL-2026-001', supplier_ids[0] if len(supplier_ids) > 0 else 1, 25000.00, 3750.00, date_delta(40), date_delta(10), 'Posted'),
        (f'BILL-2026-002', supplier_ids[1] if len(supplier_ids) > 1 else 1, 30000.00, 4500.00, date_delta(35), date_delta(5), 'Posted'),
        (f'BILL-2026-003', supplier_ids[2] if len(supplier_ids) > 2 else 1, 50000.00, 7500.00, date_delta(25), date_delta(-5), 'Posted'),
        (f'BILL-2026-004', supplier_ids[3] if len(supplier_ids) > 3 else 1, 35000.00, 5250.00, date_delta(20), date_delta(-10), 'Posted'),
        (f'BILL-2026-005', supplier_ids[4] if len(supplier_ids) > 4 else 1, 15000.00, 2250.00, date_delta(15), date_delta(-15), 'Posted'),
    ]
    
    for bill_num, supp_id, subtotal, tax_amt, bill_date, due, status in bills:
        total = subtotal + tax_amt
        cursor.execute("""
            INSERT INTO finance_supplier_bills 
            (bill_number, supplier_id, bill_date, due_date, subtotal, tax_amount, total_amount,
             amount_paid, amount_due, currency, status, payable_account_id, expense_account_id,
             tax_code_id, period_id, company_id, payment_terms)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, 'AED', ?, ?, ?, ?, ?, 1, 'Net 30')
        """, (bill_num, supp_id, bill_date, due, subtotal, tax_amt, total, total, status, ap_account_id, exp_account_id, tax_id, period_id))
    
    conn.commit()
    print("- Seeded AP bills")

def seed_fixed_assets(conn):
    """Seed fixed assets."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_assets")
    if cursor.fetchone()[0] > 0:
        print("- Fixed assets already exist, skipping")
        return
    
    # Get asset category
    cursor.execute("SELECT id FROM finance_asset_categories LIMIT 1")
    cat = cursor.fetchone()
    category_id = cat['id'] if cat else 1
    
    # Get cost center
    cursor.execute("SELECT id FROM finance_cost_centers LIMIT 1")
    cc = cursor.fetchone()
    cost_center_id = cc['id'] if cc else 1
    
    # Get asset account
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '1440'")
    asset_acc = cursor.fetchone()
    asset_account_id = asset_acc['id'] if asset_acc else 1
    
    # Get accumulated depreciation account
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '1500'")
    depr_acc = cursor.fetchone()
    accumulated_depr_account_id = depr_acc['id'] if depr_acc else 1
    
    # Get depreciation expense account
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '6300'")
    exp_acc = cursor.fetchone()
    depreciation_expense_account_id = exp_acc['id'] if exp_acc else 1
    
    assets = [
        ('AST-2024-001', 'Dell XPS 15 Laptop', category_id, date_delta(365), date_delta(365), 8500.00, 3, 'Straight Line', 425.00, 0, 0, 'Active', 'IT Room', 'IT Admin', None, None, 'SN-LP-001', None, 1, None, cost_center_id, asset_account_id, accumulated_depr_account_id, depreciation_expense_account_id),
        ('AST-2024-002', 'HP LaserJet Printer', category_id, date_delta(320), date_delta(320), 2200.00, 3, 'Straight Line', 110.00, 0, 0, 'Active', 'IT Room', 'IT Admin', None, None, 'SN-PR-001', None, 1, None, cost_center_id, asset_account_id, accumulated_depr_account_id, depreciation_expense_account_id),
        ('AST-2024-003', 'Toyota Camry 2024', category_id, date_delta(280), date_delta(280), 125000.00, 5, 'Straight Line', 6250.00, 0, 0, 'Active', 'Parking', 'Driver', None, None, 'SN-VH-001', None, 1, None, cost_center_id, asset_account_id, accumulated_depr_account_id, depreciation_expense_account_id),
        ('AST-2024-004', 'Office Furniture Set', category_id, date_delta(240), date_delta(240), 35000.00, 10, 'Straight Line', 3500.00, 0, 0, 'Active', 'Main Office', 'Office Manager', None, None, 'SN-OF-001', None, 1, None, cost_center_id, asset_account_id, accumulated_depr_account_id, depreciation_expense_account_id),
        ('AST-2024-005', 'Server Rack System', category_id, date_delta(180), date_delta(180), 45000.00, 5, 'Straight Line', 4500.00, 0, 0, 'Active', 'Server Room', 'IT Admin', None, None, 'SN-SR-001', None, 1, None, cost_center_id, asset_account_id, accumulated_depr_account_id, depreciation_expense_account_id),
        ('AST-2025-001', 'MacBook Pro 16"', category_id, date_delta(90), date_delta(90), 12000.00, 3, 'Straight Line', 2000.00, 0, 0, 'Active', 'IT Room', 'Developer', None, None, 'SN-MB-001', None, 1, None, cost_center_id, asset_account_id, accumulated_depr_account_id, depreciation_expense_account_id),
        ('AST-2025-002', 'Conference Room Projector', category_id, date_delta(60), date_delta(60), 7500.00, 5, 'Straight Line', 750.00, 0, 0, 'Active', 'Conference Room', 'Reception', None, None, 'SN-PJ-001', None, 1, None, cost_center_id, asset_account_id, accumulated_depr_account_id, depreciation_expense_account_id),
        ('AST-2026-001', 'Forklift - Toyota 8FGU25', category_id, date_delta(15), date_delta(15), 85000.00, 10, 'Straight Line', 4250.00, 0, 0, 'Active', 'Warehouse', 'Warehouse Manager', None, None, 'SN-FL-001', None, 1, None, cost_center_id, asset_account_id, accumulated_depr_account_id, depreciation_expense_account_id),
    ]
    
    for ast in assets:
        cursor.execute("""
            INSERT INTO finance_assets 
            (asset_code, asset_name, category_id, acquisition_date, capitalization_date,
             acquisition_cost, useful_life_years, depreciation_method, salvage_value, 
             accumulated_depreciation, net_book_value, status, location, custodian,
             supplier_id, purchase_order_id, serial_number, notes, company_id, branch_id, cost_center_id,
             asset_account_id, accumulated_depr_account_id, depreciation_expense_account_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ast)
    
    conn.commit()
    print("- Seeded fixed assets")

def seed_budgets(conn):
    """Seed budgets."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_budgets")
    if cursor.fetchone()[0] > 0:
        print("- Budgets already exist, skipping")
        return
    
    # Get fiscal year
    cursor.execute("SELECT id FROM finance_fiscal_years WHERE name = 'FY 2026'")
    fy = cursor.fetchone()
    fy_id = fy['id'] if fy else 1
    
    # Get expense accounts
    cursor.execute("""
        SELECT fa.id, fa.code
        FROM finance_accounts fa
        JOIN finance_account_categories fac ON fa.category_id = fac.id
        WHERE fac.account_type = 'EXPENSE'
        LIMIT 5
    """)
    expense_accounts = cursor.fetchall()
    
    budgets = [
        ('BUD-2026-001', 'Operating Budget FY2026', fy_id, 'Approved', 'Annual operating budget for 2026'),
        ('BUD-2026-002', 'Marketing Budget FY2026', fy_id, 'Approved', 'Marketing and advertising budget'),
        ('BUD-2026-003', 'IT Infrastructure Budget', fy_id, 'Approved', 'IT upgrades and maintenance'),
        ('BUD-2026-004', 'HR Training Budget', fy_id, 'Draft', 'Employee training and development'),
    ]
    
    for bud in budgets:
        cursor.execute("""
            INSERT INTO finance_budgets
            (budget_number, budget_name, fiscal_year_id, status, notes, company_id)
            VALUES (?, ?, ?, ?, ?, 1)
        """, bud)
        budget_id = cursor.lastrowid
        
        # Add budget lines for each month
        for month in range(1, 13):
            for acc in expense_accounts[:3]:
                # Amount per month for each account
                monthly_amount = 10000.00  # Simplified
                cursor.execute("""
                    INSERT INTO finance_budget_lines
                    (budget_id, account_id, period_number, amount)
                    VALUES (?, ?, ?, ?)
                """, (budget_id, acc['id'], month, monthly_amount))
    
    conn.commit()
    print("- Seeded budgets")

def main():
    print("=" * 60)
    print("SEEDING FINANCE MODULE DEMO DATA")
    print("=" * 60)
    
    try:
        # First initialize the finance schema (create tables)
        print("\nInitializing finance tables...")
        initialize_finance_schema()
        print("- Finance tables created successfully")
        
        conn = get_connection()
        
        print("\nStarting seed process...")
        seed_account_categories(conn)
        seed_chart_of_accounts(conn)
        seed_fiscal_years(conn)
        seed_tax_codes(conn)
        seed_cost_centers(conn)
        seed_journal_entries(conn)
        seed_ar_invoices(conn)
        seed_ap_bills(conn)
        seed_fixed_assets(conn)
        seed_budgets(conn)
        
        print("\n" + "=" * 60)
        print("FINANCE DATA SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nSeed data includes:")
        print("- Account categories (8 categories)")
        print("- Chart of accounts (70+ accounts)")
        print("- Fiscal years 2024, 2025, 2026 with 12 periods each")
        print("- Tax codes (VAT, Sales Tax, Customs)")
        print("- Cost centers (8 departments)")
        print("- Journal entries with double-entry bookkeeping")
        print("- AR invoices (5 customer invoices)")
        print("- AP bills (5 supplier bills)")
        print("- Fixed assets (8 assets)")
        print("- Budgets (4 budgets with monthly allocations)")
        print("\nRun: python app.py and navigate to Finance module.")
        
        conn.close()
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
