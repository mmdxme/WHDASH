"""
Seed Finance Module Demo Data
================================
This script seeds realistic demo data for the Finance/Accounting module.
It creates Chart of Accounts, Fiscal Years, Journal Entries, Customer Invoices,
Supplier Bills, Receipts, Payments, Assets, Depreciation, Cost Centers,
Budgets, Tax Codes, Bank/Cash accounts, Profit Centers, and more.

Run: python seed_finance_data.py
"""

import sqlite3
import os
from datetime import datetime, timedelta
import random

DB_PATH = os.path.join(os.path.dirname(__file__), 'warehouse.db')

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
    
    cursor.execute("SELECT id FROM companies LIMIT 1")
    company = cursor.fetchone()
    company_id = company['id'] if company else 1
    
    cursor.execute("SELECT id, code FROM finance_account_categories")
    cat_map = {row['code']: row['id'] for row in cursor.fetchall()}
    
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

def seed_profit_centers(conn):
    """Seed profit centers for business segment reporting."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_profit_centers")
    if cursor.fetchone()[0] > 0:
        print("- Profit centers already exist, skipping")
        return
    
    # Schema: id, code, name, name_ar, description, parent_id, manager_name, department, is_active, company_id, created_at, updated_at
    profit_centers = [
        ('PC-001', 'Corporate Office', 'المكتب الرئيسي', 'Main headquarters office', None, 'Ahmed Hassan (CEO)', 'Corporate', 1, 1),
        ('PC-002', 'Retail Division', 'قسم التجزئة', 'Retail business unit', None, 'Omar Khalid (Retail Director)', 'Retail', 1, 1),
        ('PC-003', 'Wholesale Division', 'قسم الجملة', 'Wholesale business unit', None, 'Sara Mohammed (Wholesale Director)', 'Wholesale', 1, 1),
        ('PC-004', 'Export Division', 'قسم التصدير', 'Export business unit', None, 'Youssef Ibrahim (Export Director)', 'Export', 1, 1),
        ('PC-005', 'E-Commerce Division', 'قسم التجارة الإلكترونية', 'E-Commerce business unit', None, 'Layla Ahmed (E-Commerce Director)', 'E-Commerce', 1, 1),
    ]
    
    for pc in profit_centers:
        cursor.execute("""
            INSERT INTO finance_profit_centers 
            (code, name, name_ar, description, parent_id, manager_name, department, is_active, company_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, pc)
    
    conn.commit()
    print("- Seeded profit centers")

def seed_bank_accounts(conn):
    """Seed bank accounts."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_bank_accounts")
    if cursor.fetchone()[0] > 0:
        print("- Bank accounts already exist, skipping")
        return
    
    # Get GL account for current account
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '1020'")
    gl_current = cursor.fetchone()
    gl_current_id = gl_current['id'] if gl_current else 1
    
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '1030'")
    gl_savings = cursor.fetchone()
    gl_savings_id = gl_savings['id'] if gl_savings else 1
    
    bank_accounts = [
        ('Emirates NBD', 'Business Current Account - AED', '1234567890', 'checking', 'AED', 
         'AE123456789012345678', 'EBILAEADXXX', 'Deira Branch', 'Dubai, UAE', gl_current_id, 500000.00, 500000.00, 'camt.053', 1, 1),
        ('Emirates NBD', 'Business Savings Account - AED', '1234567891', 'savings', 'AED',
         'AE123456789012345679', 'EBILAEADXXX', 'Deira Branch', 'Dubai, UAE', gl_savings_id, 200000.00, 200000.00, 'camt.053', 1, 1),
        ('First Abu Dhabi Bank', 'Corporate Current Account - AED', '9876543210', 'checking', 'AED',
         'AE987654321012345678', 'FABAEADXXX', 'Abu Dhabi Main', 'Abu Dhabi, UAE', gl_current_id, 750000.00, 750000.00, 'camt.053', 1, 1),
        ('Standard Chartered', 'USD Business Account', 'US5432109876', 'checking', 'USD',
         'GB29NWBK60161331926819', 'SCBLAEADXXX', 'Dubai International Financial Centre', 'Dubai, UAE', gl_current_id, 100000.00, 100000.00, 'camt.053', 1, 1),
        ('Dubai Islamic Bank', 'Current Account - AED', 'DIB123456789', 'checking', 'AED',
         'AE123456789012345680', 'DIBLAEADXXX', 'Bur Dubai Branch', 'Dubai, UAE', gl_current_id, 300000.00, 300000.00, 'camt.053', 1, 1),
    ]
    
    for ba in bank_accounts:
        cursor.execute("""
            INSERT INTO finance_bank_accounts 
            (bank_name, account_name, account_number, account_type, currency, iban, swift_code, 
             branch, address, gl_account_id, current_balance, opening_balance, 
             bank_statement_format, is_active, company_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, ba)
    
    conn.commit()
    print("- Seeded bank accounts")

def seed_journal_entries(conn):
    """Seed journal entries with proper double-entry bookkeeping."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_journals")
    existing_count = cursor.fetchone()[0]
    if existing_count > 0:
        print(f"- Journal entries already exist ({existing_count}), skipping base entries")
        return
    
    def get_account_id(acc_code):
        cursor.execute("SELECT id FROM finance_accounts WHERE code = ?", (acc_code,))
        result = cursor.fetchone()
        return result['id'] if result else None
    
    def get_period_id(year, month):
        cursor.execute("""
            SELECT id FROM finance_fiscal_periods 
            WHERE strftime('%Y', start_date) = ?
            AND period_number = ?
        """, (str(year), str(month).zfill(2)))
        result = cursor.fetchone()
        return result['id'] if result else 1
    
    def create_journal(journal_num, jtype, date_str, desc, ref, source, status_val, period_id, total_debit, total_credit, lines):
        cursor.execute("""
            INSERT INTO finance_journals 
            (journal_number, journal_type, journal_date, description, reference, source_module,
             status, period_id, company_id, created_by, total_debit, total_credit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?)
        """, (journal_num, jtype, date_str, desc, ref, source, status_val, period_id, total_debit, total_credit))
        je_id = cursor.lastrowid
        for line_num, acc_id, desc_line, debit, credit, cc_id in lines:
            cursor.execute("""
                INSERT INTO finance_journal_lines 
                (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (je_id, line_num, acc_id, desc_line, debit, credit, cc_id))
        return je_id
    
    # Get account IDs
    accounts = {
        '1020': get_account_id('1020'),
        '1030': get_account_id('1030'),
        '1110': get_account_id('1110'),
        '1210': get_account_id('1210'),
        '1440': get_account_id('1440'),
        '1500': get_account_id('1500'),
        '1800': get_account_id('1800'),
        '2110': get_account_id('2110'),
        '2210': get_account_id('2210'),
        '2230': get_account_id('2230'),
        '2310': get_account_id('2310'),
        '4110': get_account_id('4110'),
        '4120': get_account_id('4120'),
        '5110': get_account_id('5110'),
        '5120': get_account_id('5120'),
        '6210': get_account_id('6210'),
        '6220': get_account_id('6220'),
        '6230': get_account_id('6230'),
        '6240': get_account_id('6240'),
        '6300': get_account_id('6300'),
        '6400': get_account_id('6400'),
        '6500': get_account_id('6500'),
        '6600': get_account_id('6600'),
        '6700': get_account_id('6700'),
        '7200': get_account_id('7200'),
        '8200': get_account_id('8200'),
    }
    
    # Journal 1: Cash Sales (already exists conceptually - creating 6 new varied entries)
    # JE-001: Monthly rent payment
    pid = get_period_id(2026, 1)
    create_journal('JE-2026-001', 'Payment', '2026-01-01', 'Rent Payment - January 2026', 'RV-2026-01', 'Manual',
                   'Posted', pid, 25000, 25000, [
                       (1, accounts['6220'], 'January rent expense - Dubai Office', 25000, 0, 1),
                       (2, accounts['1020'], 'Cash paid to landlord', 0, 25000, None)
                   ])
    
    # JE-002: DEWA utility payment
    create_journal('JE-2026-002', 'Utility', '2026-01-05', 'DEWA Bill - January 2026', 'DEWA-2026-01', 'Utility',
                   'Posted', pid, 4525, 4525, [
                       (1, accounts['6230'], 'Electricity and water - January', 3500, 0, 1),
                       (2, accounts['1800'], 'Input VAT on utilities', 525, 0, None),
                       (3, accounts['2230'], 'Utilities payable', 0, 4025, None)
                   ])
    
    # JE-003: Salary payment
    create_journal('JE-2026-003', 'Payroll', '2026-01-15', 'Salaries - January 1st half', 'SAL-2026-01A', 'Payroll',
                   'Posted', pid, 85000, 85000, [
                       (1, accounts['6210'], 'Salary expense', 85000, 0, 1),
                       (2, accounts['2210'], 'Salaries payable', 0, 85000, None)
                   ])
    
    # JE-004: Computer equipment purchase
    create_journal('JE-2026-004', 'Purchase', '2026-01-10', 'Purchase of Laptop - Dell XPS 15', 'PO-2026-001', 'Purchase',
                   'Posted', pid, 8500, 8500, [
                       (1, accounts['1440'], 'Computer equipment - Dell XPS 15', 8500, 0, 6),
                       (2, accounts['1020'], 'Payment to supplier', 0, 8500, None)
                   ])
    
    # JE-005: Customer invoice recording
    create_journal('JE-2026-005', 'Sales', '2026-01-08', 'Invoice #INV-2026-001 - Al Fardan Trading', 'INV-2026-001', 'Sales',
                   'Posted', pid, 34500, 34500, [
                       (1, accounts['1110'], 'Trade receivable - Al Fardan', 34500, 0, 3),
                       (2, accounts['2310'], 'Output VAT', 0, 4500, None),
                       (3, accounts['4110'], 'Product sales', 0, 30000, None)
                   ])
    
    # JE-006: Bank fees
    create_journal('JE-2026-006', 'Bank Charge', '2026-01-31', 'Bank fees - January 2026', 'BANK-FEE-01', 'Bank',
                   'Posted', pid, 850, 850, [
                       (1, accounts['6400'], 'Monthly bank charges - Emirates NBD', 850, 0, 2),
                       (2, accounts['1020'], 'Bank charges deducted', 0, 850, None)
                   ])
    
    conn.commit()
    print("- Seeded journal entries (6 entries)")

def seed_journal_entries_expanded(conn):
    """Add 20-30 more realistic journal entries."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_journals")
    existing_count = cursor.fetchone()[0]
    
    # Only add if we have less than 10 entries
    if existing_count >= 10:
        print(f"- Already have {existing_count} journal entries, skipping expansion")
        return
    
    def get_account_id(acc_code):
        cursor.execute("SELECT id FROM finance_accounts WHERE code = ?", (acc_code,))
        result = cursor.fetchone()
        return result['id'] if result else None
    
    def get_period_id(year, month):
        cursor.execute("""
            SELECT id FROM finance_fiscal_periods 
            WHERE strftime('%Y', start_date) = ?
            AND period_number = ?
        """, (str(year), str(month).zfill(2)))
        result = cursor.fetchone()
        return result['id'] if result else 1
    
    def create_journal(journal_num, jtype, date_str, desc, ref, source, status_val, period_id, total_debit, total_credit, lines):
        cursor.execute("""
            INSERT INTO finance_journals 
            (journal_number, journal_type, journal_date, description, reference, source_module,
             status, period_id, company_id, created_by, total_debit, total_credit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 1, ?, ?)
        """, (journal_num, jtype, date_str, desc, ref, source, status_val, period_id, total_debit, total_credit))
        je_id = cursor.lastrowid
        for line_num, acc_id, desc_line, debit, credit, cc_id in lines:
            cursor.execute("""
                INSERT INTO finance_journal_lines 
                (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (je_id, line_num, acc_id, desc_line, debit, credit, cc_id))
        return je_id
    
    accounts = {
        '1020': get_account_id('1020'),
        '1030': get_account_id('1030'),
        '1110': get_account_id('1110'),
        '1120': get_account_id('1120'),
        '1210': get_account_id('1210'),
        '1230': get_account_id('1230'),
        '1300': get_account_id('1300'),
        '1410': get_account_id('1410'),
        '1420': get_account_id('1420'),
        '1440': get_account_id('1440'),
        '1500': get_account_id('1500'),
        '1800': get_account_id('1800'),
        '2110': get_account_id('2110'),
        '2210': get_account_id('2210'),
        '2230': get_account_id('2230'),
        '2310': get_account_id('2310'),
        '3200': get_account_id('3200'),
        '3300': get_account_id('3300'),
        '4110': get_account_id('4110'),
        '4120': get_account_id('4120'),
        '4130': get_account_id('4130'),
        '5110': get_account_id('5110'),
        '5120': get_account_id('5120'),
        '6210': get_account_id('6210'),
        '6220': get_account_id('6220'),
        '6230': get_account_id('6230'),
        '6240': get_account_id('6240'),
        '6300': get_account_id('6300'),
        '6400': get_account_id('6400'),
        '6500': get_account_id('6500'),
        '6600': get_account_id('6600'),
        '6700': get_account_id('6700'),
        '7200': get_account_id('7200'),
        '8200': get_account_id('8200'),
    }
    
    # JE-007 to JE-036: Various realistic entries
    journals_data = [
        # February entries
        ('JE-2026-007', 'Payment', '2026-02-01', 'Rent Payment - February 2026', 'RV-2026-02', 'Manual', 'Posted', get_period_id(2026, 2), 25000, 25000, [
            (1, accounts['6220'], 'February rent expense - Dubai Office', 25000, 0, 1),
            (2, accounts['1020'], 'Cash paid to landlord', 0, 25000, None)
        ]),
        ('JE-2026-008', 'Utility', '2026-02-05', 'DEWA Bill - February 2026', 'DEWA-2026-02', 'Utility', 'Posted', get_period_id(2026, 2), 5175, 5175, [
            (1, accounts['6230'], 'Electricity and water - February', 4000, 0, 1),
            (2, accounts['1800'], 'Input VAT on utilities', 600, 0, None),
            (3, accounts['2230'], 'Utilities payable', 0, 4600, None)
        ]),
        ('JE-2026-009', 'Payroll', '2026-02-15', 'Salaries - February 1st half', 'SAL-2026-02A', 'Payroll', 'Posted', get_period_id(2026, 2), 85000, 85000, [
            (1, accounts['6210'], 'Salary expense', 85000, 0, 1),
            (2, accounts['2210'], 'Salaries payable', 0, 85000, None)
        ]),
        ('JE-2026-010', 'Sales', '2026-02-10', 'Service Revenue -Consulting', 'INV-2026-003', 'Sales', 'Posted', get_period_id(2026, 2), 46000, 46000, [
            (1, accounts['1110'], 'Trade receivable - Gulf Solutions', 46000, 0, 3),
            (2, accounts['2310'], 'Output VAT', 0, 6000, None),
            (3, accounts['4120'], 'Service revenue - Consulting', 0, 40000, None)
        ]),
        ('JE-2026-011', 'Purchase', '2026-02-12', 'Office furniture purchase', 'PO-2026-002', 'Purchase', 'Posted', get_period_id(2026, 2), 28000, 28000, [
            (1, accounts['1420'], 'Office furniture - Executive desks', 28000, 0, 2),
            (2, accounts['2110'], 'Payment to Office Depot', 0, 28000, None)
        ]),
        ('JE-2026-012', 'Sales', '2026-02-15', 'Wholesale invoice', 'INV-2026-004', 'Sales', 'Posted', get_period_id(2026, 2), 115000, 115000, [
            (1, accounts['1110'], 'Trade receivable - Marina Wholesale', 115000, 0, 3),
            (2, accounts['2310'], 'Output VAT', 0, 15000, None),
            (3, accounts['4130'], 'Wholesale sales', 0, 100000, None)
        ]),
        ('JE-2026-013', 'Journal', '2026-02-20', 'Prepaid insurance amortization', 'INS-2026-01', 'Manual', 'Posted', get_period_id(2026, 2), 5000, 5000, [
            (1, accounts['6240'], 'Insurance expense - Feb portion', 5000, 0, 1),
            (2, accounts['1300'], 'Prepaid insurance reduction', 0, 5000, None)
        ]),
        ('JE-2026-014', 'Bank Charge', '2026-02-28', 'Bank fees - February 2026', 'BANK-FEE-02', 'Bank', 'Posted', get_period_id(2026, 2), 920, 920, [
            (1, accounts['6400'], 'Monthly bank charges - FAB', 920, 0, 2),
            (2, accounts['1020'], 'Bank charges deducted', 0, 920, None)
        ]),
        
        # March entries
        ('JE-2026-015', 'Payment', '2026-03-01', 'Rent Payment - March 2026', 'RV-2026-03', 'Manual', 'Posted', get_period_id(2026, 3), 25000, 25000, [
            (1, accounts['6220'], 'March rent expense - Dubai Office', 25000, 0, 1),
            (2, accounts['1020'], 'Cash paid to landlord', 0, 25000, None)
        ]),
        ('JE-2026-016', 'Utility', '2026-03-05', 'DEWA Bill - March 2026', 'DEWA-2026-03', 'Utility', 'Posted', get_period_id(2026, 3), 5850, 5850, [
            (1, accounts['6230'], 'Electricity and water - March', 4500, 0, 1),
            (2, accounts['1800'], 'Input VAT on utilities', 675, 0, None),
            (3, accounts['2230'], 'Utilities payable', 0, 5175, None)
        ]),
        ('JE-2026-017', 'Payroll', '2026-03-15', 'Salaries - March 1st half', 'SAL-2026-03A', 'Payroll', 'Posted', get_period_id(2026, 3), 87500, 87500, [
            (1, accounts['6210'], 'Salary expense', 87500, 0, 1),
            (2, accounts['2210'], 'Salaries payable', 0, 87500, None)
        ]),
        ('JE-2026-018', 'Sales', '2026-03-08', 'Product sales - Retail', 'INV-2026-005', 'Sales', 'Posted', get_period_id(2026, 3), 69000, 69000, [
            (1, accounts['1110'], 'Trade receivable - Dubai Retail LLC', 69000, 0, 3),
            (2, accounts['2310'], 'Output VAT', 0, 9000, None),
            (3, accounts['4110'], 'Product sales', 0, 60000, None)
        ]),
        ('JE-2026-019', 'Purchase', '2026-03-12', 'Raw materials purchase', 'PO-2026-003', 'Purchase', 'Posted', get_period_id(2026, 3), 57500, 57500, [
            (1, accounts['1230'], 'Raw materials - Steel', 57500, 0, 7),
            (2, accounts['1800'], 'Input VAT', 8625, 0, None),
            (3, accounts['2110'], 'Due to supplier', 0, 66125, None)
        ]),
        ('JE-2026-020', 'COGS', '2026-03-25', 'Cost of goods sold - March', 'COGS-2026-03', 'Inventory', 'Posted', get_period_id(2026, 3), 35000, 35000, [
            (1, accounts['5110'], 'Cost of products sold', 35000, 0, 4),
            (2, accounts['1210'], 'Finished goods delivered', 0, 35000, None)
        ]),
        ('JE-2026-021', 'Journal', '2026-03-28', 'Internet and communication', 'COMM-2026-03', 'Manual', 'Posted', get_period_id(2026, 3), 4200, 4200, [
            (1, accounts['6500'], 'Internet - Etisalat business plan', 2500, 0, 6),
            (2, accounts['6500'], 'Mobile phones - monthly', 1200, 0, 6),
            (3, accounts['1800'], 'Input VAT', 500, 0, None),
            (4, accounts['2230'], 'Communication payable', 0, 4200, None)
        ]),
        ('JE-2026-022', 'Depreciation', '2026-03-31', 'Monthly depreciation', 'DEP-2026-03', 'Asset', 'Posted', get_period_id(2026, 3), 8500, 8500, [
            (1, accounts['6300'], 'Depreciation expense - March', 8500, 0, 1),
            (2, accounts['1500'], 'Accumulated depreciation', 0, 8500, None)
        ]),
        
        # April entries (partial - current period)
        ('JE-2026-023', 'Payment', '2026-04-01', 'Rent Payment - April 2026', 'RV-2026-04', 'Manual', 'Posted', get_period_id(2026, 4), 25000, 25000, [
            (1, accounts['6220'], 'April rent expense - Dubai Office', 25000, 0, 1),
            (2, accounts['1020'], 'Cash paid to landlord', 0, 25000, None)
        ]),
        ('JE-2026-024', 'Payroll', '2026-04-15', 'Salaries - April 1st half', 'SAL-2026-04A', 'Payroll', 'Posted', get_period_id(2026, 4), 90000, 90000, [
            (1, accounts['6210'], 'Salary expense', 90000, 0, 1),
            (2, accounts['2210'], 'Salaries payable', 0, 90000, None)
        ]),
        ('JE-2026-025', 'Sales', '2026-04-10', 'Product sales - Export', 'INV-2026-006', 'Sales', 'Posted', get_period_id(2026, 4), 92000, 92000, [
            (1, accounts['1120'], 'Trade receivable - Saudi Trading Co', 92000, 0, 4),
            (2, accounts['2310'], 'Output VAT', 0, 12000, None),
            (3, accounts['4110'], 'Export sales - zero rated', 0, 80000, None)
        ]),
        ('JE-2026-026', 'Purchase', '2026-04-12', 'IT equipment', 'PO-2026-004', 'Purchase', 'Posted', get_period_id(2026, 4), 15000, 15000, [
            (1, accounts['1440'], 'Dell servers x2', 15000, 0, 6),
            (2, accounts['1020'], 'Payment to Dell UAE', 0, 15000, None)
        ]),
        ('JE-2026-027', 'Journal', '2026-04-20', 'Maintenance expense', 'MAINT-2026-04', 'Manual', 'Posted', get_period_id(2026, 4), 6500, 6500, [
            (1, accounts['6700'], 'AC maintenance - building', 3500, 0, 1),
            (2, accounts['6700'], 'Elevator service contract', 2000, 0, 1),
            (3, accounts['1800'], 'Input VAT', 1000, 0, None),
            (4, accounts['2110'], 'Due to maintenance company', 0, 6500, None)
        ]),
        ('JE-2026-028', 'Bank Charge', '2026-04-30', 'Bank fees - April 2026', 'BANK-FEE-04', 'Bank', 'Posted', get_period_id(2026, 4), 1100, 1100, [
            (1, accounts['6400'], 'Monthly bank charges - multiple banks', 1100, 0, 2),
            (2, accounts['1020'], 'Bank charges deducted', 0, 1100, None)
        ]),
        
        # Year-end closing entries (for 2025)
        ('JE-2025-001', 'Year End', '2025-12-31', 'Close revenue accounts', 'YE-2025-REV', 'Year End', 'Posted', get_period_id(2025, 12), 2500000, 2500000, [
            (1, accounts['4110'], 'Close product sales', 1800000, 0, None),
            (2, accounts['4120'], 'Close service revenue', 400000, 0, None),
            (3, accounts['4130'], 'Close wholesale sales', 300000, 0, None),
            (4, accounts['3200'], 'Close to retained earnings', 0, 2500000, None)
        ]),
        ('JE-2025-002', 'Year End', '2025-12-31', 'Close expense accounts', 'YE-2025-EXP', 'Year End', 'Posted', get_period_id(2025, 12), 2100000, 2100000, [
            (1, accounts['3200'], 'Close from retained earnings', 1800000, 0, None),
            (2, accounts['6210'], 'Close salaries expense', 0, 900000, None),
            (3, accounts['6220'], 'Close rent expense', 0, 300000, None),
            (4, accounts['5110'], 'Close COGS', 0, 600000, None),
            (5, accounts['6300'], 'Close depreciation', 0, 100000, None),
            (6, accounts['6230'], 'Close utilities', 0, 100000, None)
        ]),
        ('JE-2025-003', 'Year End', '2025-12-31', 'Close income summary', 'YE-2025-INCOME', 'Year End', 'Posted', get_period_id(2025, 12), 400000, 400000, [
            (1, accounts['3200'], 'Net income transferred', 400000, 0, None),
            (2, accounts['3300'], 'Current year earnings', 0, 400000, None)
        ]),
    ]
    
    for jdata in journals_data:
        try:
            create_journal(*jdata)
        except Exception as e:
            print(f"  Warning: Could not create journal {jdata[0]}: {e}")
    
    conn.commit()
    print("- Seeded expanded journal entries (30 entries)")

def seed_ar_invoices(conn):
    """Seed AR customer invoices - expanded."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_customer_invoices")
    existing_count = cursor.fetchone()[0]
    
    if existing_count >= 5:
        print(f"- AR invoices already exist ({existing_count}), skipping base")
        return
    
    cursor.execute("SELECT id, name as customer_name FROM customers LIMIT 10")
    customers = cursor.fetchall()
    
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '1110'")
    ar_account = cursor.fetchone()
    ar_account_id = ar_account['id'] if ar_account else 1
    
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '4110'")
    rev_account = cursor.fetchone()
    rev_account_id = rev_account['id'] if rev_account else 1
    
    cursor.execute("SELECT id FROM finance_tax_codes WHERE code = 'VAT-STD'")
    tax = cursor.fetchone()
    tax_id = tax['id'] if tax else 1
    
    cursor.execute("SELECT id FROM finance_fiscal_periods WHERE strftime('%Y', start_date) = strftime('%Y', 'now') AND period_number = strftime('%m', 'now')")
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
    print("- Seeded AR invoices (5 base invoices)")

def seed_ar_invoices_expanded(conn):
    """Add 10-15 more AR invoices with realistic scenarios."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_customer_invoices")
    existing_count = cursor.fetchone()[0]
    
    if existing_count >= 15:
        print(f"- Already have {existing_count} AR invoices, skipping expansion")
        return
    
    cursor.execute("SELECT id, name FROM customers LIMIT 15")
    customers = cursor.fetchall()
    
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '1110'")
    ar_account = cursor.fetchone()
    ar_account_id = ar_account['id'] if ar_account else 1
    
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '4110'")
    rev_account = cursor.fetchone()
    rev_account_id = rev_account['id'] if rev_account else 1
    
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '4120'")
    svc_account = cursor.fetchone()
    svc_account_id = svc_account['id'] if svc_account else 1
    
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '4130'")
    ws_account = cursor.fetchone()
    ws_account_id = ws_account['id'] if ws_account else 1
    
    cursor.execute("SELECT id FROM finance_tax_codes WHERE code = 'VAT-STD'")
    vat_std = cursor.fetchone()
    vat_std_id = vat_std['id'] if vat_std else 1
    
    cursor.execute("SELECT id FROM finance_tax_codes WHERE code = 'VAT-ZERO'")
    vat_zero = cursor.fetchone()
    vat_zero_id = vat_zero['id'] if vat_zero else 1
    
    cursor.execute("SELECT id FROM finance_tax_codes WHERE code = 'VAT-EX'")
    vat_ex = cursor.fetchone()
    vat_ex_id = vat_ex['id'] if vat_ex else 1
    
    # Get different periods for variety
    def get_period(year, month):
        cursor.execute("SELECT id FROM finance_fiscal_periods WHERE strftime('%Y', start_date) = ? AND period_number = ?", 
                      (str(year), str(month).zfill(2)))
        result = cursor.fetchone()
        return result['id'] if result else 1
    
    customer_ids = [c['id'] for c in customers]
    
    # Extended invoices with variety: mix of paid/unpaid, different ages, VAT rates
    extended_invoices = [
        # Older invoices (some paid, some overdue)
        ('INV-2026-006', customer_ids[5] if len(customer_ids) > 5 else 1, 85000.00, 12750.00, date_delta(90), date_delta(60), 'Paid', vat_std_id, rev_account_id, get_period(2026, 1)),
        ('INV-2026-007', customer_ids[6] if len(customer_ids) > 6 else 1, 42000.00, 6300.00, date_delta(75), date_delta(45), 'Paid', vat_std_id, rev_account_id, get_period(2026, 1)),
        ('INV-2026-008', customer_ids[7] if len(customer_ids) > 7 else 1, 156000.00, 0, date_delta(60), date_delta(30), 'Paid', vat_zero_id, rev_account_id, get_period(2026, 2)),
        ('INV-2026-009', customer_ids[0] if len(customer_ids) > 0 else 1, 67500.00, 10125.00, date_delta(55), date_delta(25), 'Partially Paid', vat_std_id, rev_account_id, get_period(2026, 2)),
        ('INV-2026-010', customer_ids[1] if len(customer_ids) > 1 else 1, 92000.00, 13800.00, date_delta(50), date_delta(20), 'Posted', vat_std_id, rev_account_id, get_period(2026, 2)),
        
        # Recent invoices
        ('INV-2026-011', customer_ids[2] if len(customer_ids) > 2 else 1, 34000.00, 0, date_delta(35), date_delta(5), 'Paid', vat_zero_id, svc_account_id, get_period(2026, 3)),
        ('INV-2026-012', customer_ids[3] if len(customer_ids) > 3 else 1, 127000.00, 19050.00, date_delta(25), date_delta(5), 'Posted', vat_std_id, ws_account_id, get_period(2026, 3)),
        ('INV-2026-013', customer_ids[4] if len(customer_ids) > 4 else 1, 48000.00, 7200.00, date_delta(20), date_delta(-10), 'Posted', vat_std_id, rev_account_id, get_period(2026, 3)),
        ('INV-2026-014', customer_ids[5] if len(customer_ids) > 5 else 1, 215000.00, 0, date_delta(15), date_delta(-15), 'Posted', vat_zero_id, rev_account_id, get_period(2026, 3)),
        ('INV-2026-015', customer_ids[6] if len(customer_ids) > 6 else 1, 78000.00, 11700.00, date_delta(10), date_delta(-20), 'Posted', vat_std_id, svc_account_id, get_period(2026, 4)),
        
        # Overdue invoices (30/60/90 days)
        ('INV-2026-016', customer_ids[7] if len(customer_ids) > 7 else 1, 95000.00, 14250.00, date_delta(95), date_delta(65), 'Overdue', vat_std_id, rev_account_id, get_period(2025, 12)),
        ('INV-2026-017', customer_ids[8] if len(customer_ids) > 8 else 1, 145000.00, 21750.00, date_delta(120), date_delta(90), 'Overdue', vat_std_id, ws_account_id, get_period(2025, 11)),
        ('INV-2026-018', customer_ids[9] if len(customer_ids) > 9 else 1, 55000.00, 0, date_delta(85), date_delta(55), 'Overdue', vat_ex_id, svc_account_id, get_period(2026, 1)),
    ]
    
    for inv_num, cust_id, subtotal, tax_amt, inv_date, due, status, tax_id, rev_id, period_id in extended_invoices:
        total = subtotal + tax_amt
        paid = total if status == 'Paid' else (total * 0.4 if status == 'Partially Paid' else 0)
        due_amt = total - paid
        
        cursor.execute("""
            INSERT INTO finance_customer_invoices 
            (invoice_number, customer_id, invoice_date, due_date, subtotal, tax_amount, total_amount,
             amount_paid, amount_due, currency, status, receivable_account_id, revenue_account_id, 
             tax_code_id, period_id, company_id, payment_terms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'AED', ?, ?, ?, ?, ?, 1, 'Net 30')
        """, (inv_num, cust_id, inv_date, due, subtotal, tax_amt, total, paid, due_amt, status, ar_account_id, rev_id, tax_id, period_id))
    
    conn.commit()
    print("- Seeded expanded AR invoices (15 more invoices)")

def seed_ap_bills(conn):
    """Seed AP supplier bills - base."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_supplier_bills")
    existing_count = cursor.fetchone()[0]
    
    if existing_count >= 5:
        print(f"- AP bills already exist ({existing_count}), skipping base")
        return
    
    cursor.execute("SELECT id, name as supplier_name FROM suppliers LIMIT 10")
    suppliers = cursor.fetchall()
    
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '2110'")
    ap_account = cursor.fetchone()
    ap_account_id = ap_account['id'] if ap_account else 1
    
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '5110'")
    exp_account = cursor.fetchone()
    exp_account_id = exp_account['id'] if exp_account else 1
    
    cursor.execute("SELECT id FROM finance_tax_codes WHERE code = 'VAT-STD'")
    tax = cursor.fetchone()
    tax_id = tax['id'] if tax else 1
    
    cursor.execute("SELECT id FROM finance_fiscal_periods WHERE strftime('%Y', start_date) = strftime('%Y', 'now') AND period_number = strftime('%m', 'now')")
    period = cursor.fetchone()
    period_id = period['id'] if period else 1
    
    supplier_ids = [s['id'] for s in suppliers]
    
    bills = [
        (f'BILL-2026-001', supplier_ids[0] if len(supplier_ids) > 0 else 1, 25000.00, 3750.00, date_delta(40), date_delta(10), 'Posted', exp_account_id),
        (f'BILL-2026-002', supplier_ids[1] if len(supplier_ids) > 1 else 1, 30000.00, 4500.00, date_delta(35), date_delta(5), 'Posted', exp_account_id),
        (f'BILL-2026-003', supplier_ids[2] if len(supplier_ids) > 2 else 1, 50000.00, 7500.00, date_delta(25), date_delta(-5), 'Posted', exp_account_id),
        (f'BILL-2026-004', supplier_ids[3] if len(supplier_ids) > 3 else 1, 35000.00, 5250.00, date_delta(20), date_delta(-10), 'Posted', exp_account_id),
        (f'BILL-2026-005', supplier_ids[4] if len(supplier_ids) > 4 else 1, 15000.00, 2250.00, date_delta(15), date_delta(-15), 'Posted', exp_account_id),
    ]
    
    for bill_num, supp_id, subtotal, tax_amt, bill_date, due, status, exp_id in bills:
        total = subtotal + tax_amt
        cursor.execute("""
            INSERT INTO finance_supplier_bills 
            (bill_number, supplier_id, bill_date, due_date, subtotal, tax_amount, total_amount,
             amount_paid, amount_due, currency, status, payable_account_id, expense_account_id,
             tax_code_id, period_id, company_id, payment_terms)
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, 'AED', ?, ?, ?, ?, ?, 1, 'Net 30')
        """, (bill_num, supp_id, bill_date, due, subtotal, tax_amt, total, total, status, ap_account_id, exp_id, tax_id, period_id))
    
    conn.commit()
    print("- Seeded AP bills (5 base bills)")

def seed_ap_bills_expanded(conn):
    """Add 10-15 more AP bills with realistic scenarios."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_supplier_bills")
    existing_count = cursor.fetchone()[0]
    
    if existing_count >= 15:
        print(f"- Already have {existing_count} AP bills, skipping expansion")
        return
    
    cursor.execute("SELECT id FROM suppliers LIMIT 20")
    suppliers = cursor.fetchall()
    
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '2110'")
    ap_account = cursor.fetchone()
    ap_account_id = ap_account['id'] if ap_account else 1
    
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '5110'")
    cogs_account = cursor.fetchone()
    cogs_account_id = cogs_account['id'] if cogs_account else 1
    
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '5120'")
    labor_account = cursor.fetchone()
    labor_account_id = labor_account['id'] if labor_account else 1
    
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '6220'")
    rent_account = cursor.fetchone()
    rent_account_id = rent_account['id'] if rent_account else 1
    
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '6230'")
    util_account = cursor.fetchone()
    util_account_id = util_account['id'] if util_account else 1
    
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '6600'")
    it_account = cursor.fetchone()
    it_account_id = it_account['id'] if it_account else 1
    
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '6700'")
    maint_account = cursor.fetchone()
    maint_account_id = maint_account['id'] if maint_account else 1
    
    cursor.execute("SELECT id FROM finance_tax_codes WHERE code = 'VAT-STD'")
    vat_std = cursor.fetchone()
    vat_std_id = vat_std['id'] if vat_std else 1
    
    cursor.execute("SELECT id FROM finance_tax_codes WHERE code = 'CUST-5'")
    cust_5 = cursor.fetchone()
    cust_5_id = cust_5['id'] if cust_5 else 1
    
    def get_period(year, month):
        cursor.execute("SELECT id FROM finance_fiscal_periods WHERE strftime('%Y', start_date) = ? AND period_number = ?", 
                      (str(year), str(month).zfill(2)))
        result = cursor.fetchone()
        return result['id'] if result else 1
    
    supplier_ids = [s['id'] for s in suppliers]
    
    extended_bills = [
        # Utility bills
        ('BILL-2026-006', supplier_ids[5] if len(supplier_ids) > 5 else 1, 4500.00, 675.00, date_delta(85), date_delta(55), 'Paid', util_account_id, vat_std_id, get_period(2026, 1)),
        ('BILL-2026-007', supplier_ids[6] if len(supplier_ids) > 6 else 1, 5200.00, 780.00, date_delta(70), date_delta(40), 'Paid', util_account_id, vat_std_id, get_period(2026, 1)),
        ('BILL-2026-008', supplier_ids[7] if len(supplier_ids) > 7 else 1, 4800.00, 720.00, date_delta(55), date_delta(25), 'Partially Paid', util_account_id, vat_std_id, get_period(2026, 2)),
        
        # Rent bills
        ('BILL-2026-009', supplier_ids[0] if len(supplier_ids) > 0 else 1, 75000.00, 0, date_delta(45), date_delta(15), 'Paid', rent_account_id, vat_std_id, get_period(2026, 2)),
        ('BILL-2026-010', supplier_ids[0] if len(supplier_ids) > 0 else 1, 75000.00, 0, date_delta(15), date_delta(-15), 'Posted', rent_account_id, vat_std_id, get_period(2026, 4)),
        
        # Inventory/supplier bills
        ('BILL-2026-011', supplier_ids[8] if len(supplier_ids) > 8 else 1, 125000.00, 18750.00, date_delta(60), date_delta(30), 'Paid', cogs_account_id, vat_std_id, get_period(2026, 1)),
        ('BILL-2026-012', supplier_ids[9] if len(supplier_ids) > 9 else 1, 85000.00, 12750.00, date_delta(40), date_delta(10), 'Posted', cogs_account_id, vat_std_id, get_period(2026, 2)),
        ('BILL-2026-013', supplier_ids[5] if len(supplier_ids) > 5 else 1, 67000.00, 10050.00, date_delta(30), date_delta(0), 'Posted', cogs_account_id, vat_std_id, get_period(2026, 3)),
        
        # Service/IT bills
        ('BILL-2026-014', supplier_ids[6] if len(supplier_ids) > 6 else 1, 25000.00, 3750.00, date_delta(50), date_delta(20), 'Partially Paid', it_account_id, vat_std_id, get_period(2026, 2)),
        ('BILL-2026-015', supplier_ids[7] if len(supplier_ids) > 7 else 1, 18000.00, 2700.00, date_delta(25), date_delta(-5), 'Posted', it_account_id, vat_std_id, get_period(2026, 3)),
        
        # Overdue bills
        ('BILL-2026-016', supplier_ids[8] if len(supplier_ids) > 8 else 1, 95000.00, 14250.00, date_delta(95), date_delta(65), 'Overdue', cogs_account_id, vat_std_id, get_period(2025, 12)),
        ('BILL-2026-017', supplier_ids[9] if len(supplier_ids) > 9 else 1, 145000.00, 21750.00, date_delta(120), date_delta(90), 'Overdue', cogs_account_id, cust_5_id, get_period(2025, 11)),
        
        # Maintenance
        ('BILL-2026-018', supplier_ids[0] if len(supplier_ids) > 0 else 1, 15000.00, 2250.00, date_delta(35), date_delta(5), 'Posted', maint_account_id, vat_std_id, get_period(2026, 3)),
    ]
    
    for bill_num, supp_id, subtotal, tax_amt, bill_date, due, status, exp_id, tax_id, period_id in extended_bills:
        total = subtotal + tax_amt
        paid = total if status == 'Paid' else (total * 0.5 if status == 'Partially Paid' else 0)
        due_amt = total - paid
        
        cursor.execute("""
            INSERT INTO finance_supplier_bills 
            (bill_number, supplier_id, bill_date, due_date, subtotal, tax_amount, total_amount,
             amount_paid, amount_due, currency, status, payable_account_id, expense_account_id,
             tax_code_id, period_id, company_id, payment_terms)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'AED', ?, ?, ?, ?, ?, 1, 'Net 30')
        """, (bill_num, supp_id, bill_date, due, subtotal, tax_amt, total, paid, due_amt, status, ap_account_id, exp_id, tax_id, period_id))
    
    conn.commit()
    print("- Seeded expanded AP bills (15 more bills)")

def seed_ar_receipts(conn):
    """Seed customer receipts."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_customer_receipts")
    if cursor.fetchone()[0] > 0:
        print("- AR receipts already exist, skipping")
        return
    
    cursor.execute("SELECT id FROM customers LIMIT 10")
    customers = cursor.fetchall()
    
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '1020'")
    cash_account = cursor.fetchone()
    cash_account_id = cash_account['id'] if cash_account else 1
    
    cursor.execute("SELECT id FROM finance_bank_accounts LIMIT 1")
    bank_account = cursor.fetchone()
    bank_account_id = bank_account['id'] if bank_account else 1
    
    cursor.execute("SELECT id FROM finance_customer_invoices LIMIT 10")
    invoices = cursor.fetchall()
    
    customer_ids = [c['id'] for c in customers]
    invoice_ids = [i['id'] for i in invoices]
    
    receipts = [
        ('RCT-2026-001', customer_ids[0] if len(customer_ids) > 0 else 1, date_delta(40), 57500.00, 0, 'Bank Transfer', 'Transfer from Al Fardan Trading', 'Posted', invoice_ids[0] if len(invoice_ids) > 0 else None),
        ('RCT-2026-002', customer_ids[1] if len(customer_ids) > 1 else 1, date_delta(25), 34500.00, 0, 'Check', 'Check #123456', 'Posted', invoice_ids[1] if len(invoice_ids) > 1 else None),
        ('RCT-2026-003', customer_ids[2] if len(customer_ids) > 2 else 1, date_delta(15), 86250.00, 500, 'Bank Transfer', 'Partial payment - Gulf Solutions', 'Posted', invoice_ids[2] if len(invoice_ids) > 2 else None),
        ('RCT-2026-004', customer_ids[3] if len(customer_ids) > 3 else 1, date_delta(10), 50000.00, 0, 'Cash', 'Cash deposit', 'Posted', invoice_ids[3] if len(invoice_ids) > 3 else None),
        ('RCT-2026-005', customer_ids[4] if len(customer_ids) > 4 else 1, date_delta(5), 46000.00, 0, 'Bank Transfer', 'Dubai Retail LLC payment', 'Posted', invoice_ids[4] if len(invoice_ids) > 4 else None),
        ('RCT-2026-006', customer_ids[5] if len(customer_ids) > 5 else 1, date_delta(80), 97750.00, 1500, 'Bank Transfer', 'Saudi Trading Co - early payment', 'Posted', invoice_ids[5] if len(invoice_ids) > 5 else None),
        ('RCT-2026-007', customer_ids[6] if len(customer_ids) > 6 else 1, date_delta(20), 48250.00, 0, 'Check', 'Marina Wholesale partial', 'Posted', invoice_ids[6] if len(invoice_ids) > 6 else None),
        ('RCT-2026-008', customer_ids[7] if len(customer_ids) > 7 else 1, date_delta(12), 92000.00, 0, 'Bank Transfer', 'Full settlement - Export invoice', 'Posted', invoice_ids[7] if len(invoice_ids) > 7 else None),
        ('RCT-2026-009', customer_ids[0] if len(customer_ids) > 0 else 1, date_delta(3), 35000.00, 0, 'Bank Transfer', 'Advance payment', 'Unapplied', None),
        ('RCT-2026-010', customer_ids[1] if len(customer_ids) > 1 else 1, date_delta(1), 15000.00, 0, 'Cash', 'Customer deposit', 'Unapplied', None),
    ]
    
    for rct_num, cust_id, rct_date, amount, discount, method, ref, status, inv_id in receipts:
        cursor.execute("""
            INSERT INTO finance_customer_receipts 
            (receipt_number, customer_id, receipt_date, amount_received, discount_allowed, 
             payment_method, reference_number, notes, status, cash_account_id, bank_account_id,
             invoice_id, company_id, created_by, posted_by, posted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, 1, datetime('now'))
        """, (rct_num, cust_id, rct_date, amount, discount, method, ref, f'Payment {status}', status, 
              cash_account_id, bank_account_id, inv_id))
        
        receipt_id = cursor.lastrowid
        
        # Create receipt line if linked to invoice
        if inv_id:
            cursor.execute("""
                INSERT INTO finance_customer_receipt_lines 
                (receipt_id, invoice_id, amount_allocated, discount_used, line_number)
                VALUES (?, ?, ?, ?, 1)
            """, (receipt_id, inv_id, amount, discount))
    
    conn.commit()
    print("- Seeded AR receipts (10 receipts)")

def seed_ap_payments(conn):
    """Seed supplier payments."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_supplier_payments")
    if cursor.fetchone()[0] > 0:
        print("- AP payments already exist, skipping")
        return
    
    cursor.execute("SELECT id FROM suppliers LIMIT 10")
    suppliers = cursor.fetchall()
    
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '1020'")
    cash_account = cursor.fetchone()
    cash_account_id = cash_account['id'] if cash_account else 1
    
    cursor.execute("SELECT id FROM finance_bank_accounts LIMIT 1")
    bank_account = cursor.fetchone()
    bank_account_id = bank_account['id'] if bank_account else 1
    
    cursor.execute("SELECT id FROM finance_supplier_bills LIMIT 10")
    bills = cursor.fetchall()
    
    supplier_ids = [s['id'] for s in suppliers]
    bill_ids = [b['id'] for b in bills]
    
    payments = [
        ('PMT-2026-001', supplier_ids[0] if len(supplier_ids) > 0 else 1, date_delta(35), 28750.00, 0, 'Bank Transfer', 'Payment to Emirates Supplies', 'Posted', bill_ids[0] if len(bill_ids) > 0 else None),
        ('PMT-2026-002', supplier_ids[1] if len(supplier_ids) > 1 else 1, date_delta(30), 34500.00, 500, 'Check', 'Check #789012', 'Posted', bill_ids[1] if len(bill_ids) > 1 else None),
        ('PMT-2026-003', supplier_ids[2] if len(supplier_ids) > 2 else 1, date_delta(20), 57500.00, 0, 'Bank Transfer', 'Gulf Materials - partial', 'Posted', bill_ids[2] if len(bill_ids) > 2 else None),
        ('PMT-2026-004', supplier_ids[3] if len(supplier_ids) > 3 else 1, date_delta(15), 40250.00, 0, 'Bank Transfer', 'Full settlement', 'Posted', bill_ids[3] if len(bill_ids) > 3 else None),
        ('PMT-2026-005', supplier_ids[4] if len(supplier_ids) > 4 else 1, date_delta(10), 17250.00, 0, 'Cash', 'Cash payment - stationery', 'Posted', bill_ids[4] if len(bill_ids) > 4 else None),
        ('PMT-2026-006', supplier_ids[5] if len(supplier_ids) > 5 else 1, date_delta(75), 51750.00, 1500, 'Bank Transfer', 'Early payment discount', 'Posted', bill_ids[5] if len(bill_ids) > 5 else None),
        ('PMT-2026-007', supplier_ids[6] if len(supplier_ids) > 6 else 1, date_delta(25), 28650.00, 0, 'Check', 'Check #456789', 'Posted', bill_ids[6] if len(bill_ids) > 6 else None),
        ('PMT-2026-008', supplier_ids[7] if len(supplier_ids) > 7 else 1, date_delta(18), 97750.00, 0, 'Bank Transfer', 'Full settlement - inventory', 'Posted', bill_ids[7] if len(bill_ids) > 7 else None),
        ('PMT-2026-009', supplier_ids[0] if len(supplier_ids) > 0 else 1, date_delta(5), 25000.00, 0, 'Bank Transfer', 'Advance to landlord', 'Unapplied', None),
        ('PMT-2026-010', supplier_ids[1] if len(supplier_ids) > 1 else 1, date_delta(2), 15000.00, 0, 'Cash', 'Advance payment', 'Unapplied', None),
    ]
    
    for pmt_num, supp_id, pmt_date, amount, discount, method, ref, status, bill_id in payments:
        cursor.execute("""
            INSERT INTO finance_supplier_payments 
            (payment_number, supplier_id, payment_date, amount_paid, discount_received,
             payment_method, reference_number, notes, status, cash_account_id, bank_account_id,
             bill_id, company_id, created_by, posted_by, posted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1, 1, datetime('now'))
        """, (pmt_num, supp_id, pmt_date, amount, discount, method, ref, f'Payment {status}',
              cash_account_id, bank_account_id, bill_id))
        
        payment_id = cursor.lastrowid
        
        if bill_id:
            cursor.execute("""
                INSERT INTO finance_supplier_payment_lines 
                (payment_id, bill_id, amount_allocated, discount_used, line_number)
                VALUES (?, ?, ?, ?, 1)
            """, (payment_id, bill_id, amount, discount))
    
    conn.commit()
    print("- Seeded AP payments (10 payments)")

def seed_fixed_assets(conn):
    """Seed fixed assets - base."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_assets")
    if cursor.fetchone()[0] > 0:
        print("- Fixed assets already exist, skipping")
        return
    
    cursor.execute("SELECT id FROM finance_asset_categories LIMIT 1")
    cat = cursor.fetchone()
    category_id = cat['id'] if cat else 1
    
    cursor.execute("SELECT id FROM finance_cost_centers LIMIT 1")
    cc = cursor.fetchone()
    cost_center_id = cc['id'] if cc else 1
    
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '1440'")
    asset_acc = cursor.fetchone()
    asset_account_id = asset_acc['id'] if asset_acc else 1
    
    cursor.execute("SELECT id FROM finance_accounts WHERE code = '1500'")
    depr_acc = cursor.fetchone()
    accumulated_depr_account_id = depr_acc['id'] if depr_acc else 1
    
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
    print("- Seeded fixed assets (8 assets)")

def seed_asset_transactions(conn):
    """Seed asset acquisition, disposal, and transfer transactions."""
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master WHERE type='table' AND name='finance_asset_transactions'
    """)
    if not cursor.fetchone():
        print("- finance_asset_transactions table does not exist, skipping asset transactions seed")
        return
    
    cursor.execute("SELECT COUNT(*) FROM finance_asset_transactions")
    if cursor.fetchone()[0] > 0:
        print("- Asset transactions already exist, skipping")
        return
    
    cursor.execute("SELECT id FROM finance_assets LIMIT 5")
    assets = cursor.fetchall()
    asset_ids = [a['id'] for a in assets]
    
    cursor.execute("SELECT id FROM finance_cost_centers LIMIT 3")
    cc_list = cursor.fetchall()
    cc_ids = [c['id'] for c in cc_list]
    
    cursor.execute("SELECT id FROM finance_fiscal_periods WHERE strftime('%Y', start_date) = strftime('%Y', 'now') LIMIT 1")
    period = cursor.fetchone()
    period_id = period['id'] if period else 1
    
    transactions = [
        # Asset acquisitions
        ('ATXN-2026-001', asset_ids[0] if len(asset_ids) > 0 else 1, 'Acquisition', date_delta(365), period_id, 1, 8500.00, 8500.00, None, None, None, None, 'Dell XPS 15 Laptop', 'Posted', 1, 1),
        ('ATXN-2026-002', asset_ids[2] if len(asset_ids) > 2 else 1, 'Acquisition', date_delta(280), period_id, 1, 125000.00, 125000.00, None, None, None, None, 'Toyota Camry 2024', 'Posted', 1, 1),
        ('ATXN-2026-003', asset_ids[4] if len(asset_ids) > 4 else 1, 'Acquisition', date_delta(180), period_id, 1, 45000.00, 45000.00, None, None, None, None, 'Server Rack System', 'Posted', 1, 1),
        ('ATXN-2026-004', asset_ids[6] if len(asset_ids) > 6 else 1, 'Acquisition', date_delta(60), period_id, 1, 7500.00, 7500.00, None, None, None, None, 'Conference Room Projector', 'Posted', 1, 1),
        
        # Asset disposal (of an older fully depreciated asset)
        ('ATXN-2026-005', asset_ids[1] if len(asset_ids) > 1 else 1, 'Disposal', date_delta(30), period_id, 1, 0, 0, 500.00, -1700.00, None, None, 'HP Printer - sold for scrap', 'Posted', 1, 1),
        
        # Asset transfer
        ('ATXN-2026-006', asset_ids[3] if len(asset_ids) > 3 else 1, 'Transfer', date_delta(45), period_id, 1, 0, 0, None, None, cc_ids[0] if len(cc_ids) > 0 else 1, cc_ids[1] if len(cc_ids) > 1 else 2, 'Office furniture moved to Finance Dept', 'Posted', 1, 1),
    ]
    
    for txn in transactions:
        cursor.execute("""
            INSERT INTO finance_asset_transactions 
            (transaction_number, asset_id, transaction_type, transaction_date, period_id,
             quantity, unit_price, total_amount, disposal_proceeds, gain_loss,
             from_cost_center_id, to_cost_center_id, description, status, company_id, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, txn)
    
    conn.commit()
    print("- Seeded asset transactions (6 transactions)")

def seed_depreciation_runs(conn):
    """Seed depreciation runs for past periods."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_depreciation_runs")
    if cursor.fetchone()[0] > 0:
        print("- Depreciation runs already exist, skipping")
        return
    
    cursor.execute("SELECT id FROM finance_assets")
    assets = cursor.fetchall()
    asset_ids = [a['id'] for a in assets]
    
    def get_period(year, month):
        cursor.execute("SELECT id FROM finance_fiscal_periods WHERE strftime('%Y', start_date) = ? AND period_number = ?", 
                      (str(year), str(month).zfill(2)))
        result = cursor.fetchone()
        return result['id'] if result else 1
    
    runs = [
        ('DEP-2026-01', '2026-01-31', get_period(2026, 1), 'January 2026 depreciation', 8500.00, len(asset_ids), 'Posted'),
        ('DEP-2026-02', '2026-02-28', get_period(2026, 2), 'February 2026 depreciation', 8500.00, len(asset_ids), 'Posted'),
        ('DEP-2026-03', '2026-03-31', get_period(2026, 3), 'March 2026 depreciation', 8500.00, len(asset_ids), 'Posted'),
        ('DEP-2026-04', '2026-04-30', get_period(2026, 4), 'April 2026 depreciation', 8500.00, len(asset_ids), 'Posted'),
        ('DEP-2025-09', '2025-09-30', get_period(2025, 9), 'September 2025 depreciation', 7500.00, len(asset_ids), 'Posted'),
        ('DEP-2025-10', '2025-10-31', get_period(2025, 10), 'October 2025 depreciation', 7500.00, len(asset_ids), 'Posted'),
        ('DEP-2025-11', '2025-11-30', get_period(2025, 11), 'November 2025 depreciation', 7500.00, len(asset_ids), 'Posted'),
        ('DEP-2025-12', '2025-12-31', get_period(2025, 12), 'December 2025 depreciation', 7500.00, len(asset_ids), 'Posted'),
    ]
    
    for run_num, run_date, period_id, desc, total_depr, asset_count, status in runs:
        cursor.execute("""
            INSERT INTO finance_depreciation_runs 
            (run_number, run_date, period_id, description, total_depreciation, asset_count, status, company_id, created_by, posted_by, posted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, 1, 1, datetime('now'))
        """, (run_num, run_date, period_id, desc, total_depr, asset_count, status))
        
        run_id = cursor.lastrowid
        
        # Add depreciation entries for each asset
        for i, asset_id in enumerate(asset_ids):
            cursor.execute("""
                INSERT INTO finance_depreciation_entries 
                (run_id, asset_id, depreciation_this_run, line_number)
                VALUES (?, ?, ?, ?)
            """, (run_id, asset_id, 8500.00 if i < 4 else 7500.00, i + 1))
    
    conn.commit()
    print("- Seeded depreciation runs (8 runs)")

def seed_budgets(conn):
    """Seed budgets - base."""
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM finance_budgets")
    if cursor.fetchone()[0] > 0:
        print("- Budgets already exist, skipping")
        return
    
    cursor.execute("SELECT id FROM finance_fiscal_years WHERE name = 'FY 2026'")
    fy = cursor.fetchone()
    fy_id = fy['id'] if fy else 1
    
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
        
        for month in range(1, 13):
            for acc in expense_accounts[:3]:
                monthly_amount = 10000.00
                cursor.execute("""
                    INSERT INTO finance_budget_lines
                    (budget_id, account_id, period_number, amount)
                    VALUES (?, ?, ?, ?)
                """, (budget_id, acc['id'], month, monthly_amount))
    
    conn.commit()
    print("- Seeded budgets (4 budgets)")

def seed_budget_actuals(conn):
    """Seed journal entries representing actuals that match budgeted amounts."""
    cursor = conn.cursor()
    
    # Check if budget actuals already exist
    cursor.execute("SELECT COUNT(*) FROM finance_journals WHERE journal_number LIKE 'ACT-%'")
    if cursor.fetchone()[0] > 0:
        print("- Budget actuals already exist, skipping")
        return
    
    def get_account_id(acc_code):
        cursor.execute("SELECT id FROM finance_accounts WHERE code = ?", (acc_code,))
        result = cursor.fetchone()
        return result['id'] if result else None
    
    def get_period_id(year, month):
        cursor.execute("""
            SELECT id FROM finance_fiscal_periods 
            WHERE strftime('%Y', start_date) = ?
            AND period_number = ?
        """, (str(year), str(month).zfill(2)))
        result = cursor.fetchone()
        return result['id'] if result else 1
    
    accounts = {
        '6210': get_account_id('6210'),
        '6220': get_account_id('6220'),
        '6230': get_account_id('6230'),
        '6110': get_account_id('6110'),
        '6600': get_account_id('6600'),
        '6700': get_account_id('6700'),
        '1020': get_account_id('1020'),
        '2310': get_account_id('2310'),
    }
    
    # Get cost centers
    cursor.execute("SELECT id FROM finance_cost_centers LIMIT 4")
    cc_list = cursor.fetchall()
    cc_ids = [c['id'] for c in cc_list]
    
    # Create "actual" journal entries that are close to budget
    # These represent real expenses recorded in the system
    # cc_ids has 8 items (CC-001 to CC-008), so use modulo to avoid index issues
    actuals_data = [
        # January 2026
        (get_period_id(2026, 1), '2026-01-15', '6210', 85000, cc_ids[0] if len(cc_ids) > 0 else 1),  # Salaries
        (get_period_id(2026, 1), '2026-01-01', '6220', 24000, cc_ids[0] if len(cc_ids) > 0 else 1),  # Rent
        (get_period_id(2026, 1), '2026-01-05', '6230', 3500, cc_ids[0] if len(cc_ids) > 0 else 1),  # Utilities
        (get_period_id(2026, 1), '2026-01-10', '6110', 12000, cc_ids[2] if len(cc_ids) > 2 else 3),  # Advertising
        (get_period_id(2026, 1), '2026-01-20', '6600', 8000, cc_ids[5] if len(cc_ids) > 5 else 6),  # IT
        (get_period_id(2026, 1), '2026-01-25', '6700', 5000, cc_ids[3] if len(cc_ids) > 3 else 4),  # Maintenance
        
        # February 2026
        (get_period_id(2026, 2), '2026-02-15', '6210', 85000, cc_ids[0] if len(cc_ids) > 0 else 1),
        (get_period_id(2026, 2), '2026-02-01', '6220', 24000, cc_ids[0] if len(cc_ids) > 0 else 1),
        (get_period_id(2026, 2), '2026-02-05', '6230', 4000, cc_ids[0] if len(cc_ids) > 0 else 1),
        (get_period_id(2026, 2), '2026-02-12', '6110', 15000, cc_ids[2] if len(cc_ids) > 2 else 3),
        (get_period_id(2026, 2), '2026-02-20', '6600', 9500, cc_ids[5] if len(cc_ids) > 5 else 6),
        (get_period_id(2026, 2), '2026-02-25', '6700', 4500, cc_ids[3] if len(cc_ids) > 3 else 4),
        
        # March 2026
        (get_period_id(2026, 3), '2026-03-15', '6210', 87500, cc_ids[0] if len(cc_ids) > 0 else 1),
        (get_period_id(2026, 3), '2026-03-01', '6220', 24000, cc_ids[0] if len(cc_ids) > 0 else 1),
        (get_period_id(2026, 3), '2026-03-05', '6230', 4500, cc_ids[0] if len(cc_ids) > 0 else 1),
        (get_period_id(2026, 3), '2026-03-12', '6110', 11000, cc_ids[2] if len(cc_ids) > 2 else 3),
        (get_period_id(2026, 3), '2026-03-20', '6600', 8500, cc_ids[5] if len(cc_ids) > 5 else 6),
        (get_period_id(2026, 3), '2026-03-25', '6700', 6000, cc_ids[3] if len(cc_ids) > 3 else 4),
        
        # April 2026
        (get_period_id(2026, 4), '2026-04-15', '6210', 90000, cc_ids[0] if len(cc_ids) > 0 else 1),
        (get_period_id(2026, 4), '2026-04-01', '6220', 25000, cc_ids[0] if len(cc_ids) > 0 else 1),
        (get_period_id(2026, 4), '2026-04-05', '6230', 4800, cc_ids[0] if len(cc_ids) > 0 else 1),
        (get_period_id(2026, 4), '2026-04-12', '6110', 18000, cc_ids[2] if len(cc_ids) > 2 else 3),
        (get_period_id(2026, 4), '2026-04-20', '6600', 12000, cc_ids[5] if len(cc_ids) > 5 else 6),
        (get_period_id(2026, 4), '2026-04-25', '6700', 5500, cc_ids[3] if len(cc_ids) > 3 else 4),
    ]
    
    for i, (period_id, date_str, acc_code, amount, cc_id) in enumerate(actuals_data):
        journal_num = f'ACT-2026-{i+1:03d}'
        acc_id = accounts.get(acc_code)
        
        if acc_id and accounts['1020']:
            vat_amount = amount * 0.15 if acc_code not in ['6210', '6220'] else 0
            total = amount + vat_amount
            
            cursor.execute("""
                INSERT INTO finance_journals 
                (journal_number, journal_type, journal_date, description, reference, source_module,
                 status, period_id, company_id, created_by, total_debit, total_credit)
                VALUES (?, 'Actual', ?, ?, ?, 'Budget', 'Posted', ?, 1, 1, ?, ?)
            """, (journal_num, date_str, f'Actual expense - {acc_code}', f'ACT-{acc_code}', period_id, total, total))
            
            je_id = cursor.lastrowid
            
            # Debit expense
            cursor.execute("""
                INSERT INTO finance_journal_lines 
                (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
                VALUES (?, 1, ?, ?, ?, 0, ?)
            """, (je_id, acc_id, f'Expense {acc_code}', amount, cc_id))
            
            # Credit cash
            cursor.execute("""
                INSERT INTO finance_journal_lines 
                (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
                VALUES (?, 2, ?, ?, 0, ?, NULL)
            """, (je_id, accounts['1020'], 'Cash paid', total))
            
            # VAT if applicable
            if vat_amount > 0:
                cursor.execute("""
                    INSERT INTO finance_journal_lines 
                    (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
                    VALUES (?, 3, ?, ?, ?, 0, NULL)
                """, (je_id, accounts['2310'], 'Output VAT', vat_amount))
    
    conn.commit()
    print("- Seeded budget actuals (24 entries)")

def seed_tax_transactions(conn):
    """Seed VAT and tax transactions."""
    cursor = conn.cursor()
    
    # Check if tax transactions already exist
    cursor.execute("SELECT COUNT(*) FROM finance_journals WHERE journal_number LIKE 'VAT-%'")
    if cursor.fetchone()[0] > 0:
        print("- Tax transactions already exist, skipping")
        return
    
    def get_account_id(acc_code):
        cursor.execute("SELECT id FROM finance_accounts WHERE code = ?", (acc_code,))
        result = cursor.fetchone()
        return result['id'] if result else None
    
    def get_period_id(year, month):
        cursor.execute("""
            SELECT id FROM finance_fiscal_periods 
            WHERE strftime('%Y', start_date) = ?
            AND period_number = ?
        """, (str(year), str(month).zfill(2)))
        result = cursor.fetchone()
        return result['id'] if result else 1
    
    accounts = {
        '1800': get_account_id('1800'),
        '2310': get_account_id('2310'),
        '1020': get_account_id('1020'),
    }
    
    # VAT payable to tax authority payments
    vat_payments = [
        # Pay VAT for Sep 2025
        ('VAT-2025-09', '2025-10-20', get_period_id(2025, 10), 45000.00, 'VAT payment for September 2025'),
        # Pay VAT for Oct 2025
        ('VAT-2025-10', '2025-11-20', get_period_id(2025, 11), 52000.00, 'VAT payment for October 2025'),
        # Pay VAT for Nov 2025
        ('VAT-2025-11', '2025-12-20', get_period_id(2025, 12), 48000.00, 'VAT payment for November 2025'),
        # Pay VAT for Dec 2025
        ('VAT-2025-12', '2026-01-20', get_period_id(2026, 1), 55000.00, 'VAT payment for December 2025'),
        # Pay VAT for Jan 2026
        ('VAT-2026-01', '2026-02-20', get_period_id(2026, 2), 62000.00, 'VAT payment for January 2026'),
        # Pay VAT for Feb 2026
        ('VAT-2026-02', '2026-03-20', get_period_id(2026, 3), 58000.00, 'VAT payment for February 2026'),
    ]
    
    for vat_num, vat_date, period_id, amount, desc in vat_payments:
        if accounts['1800'] and accounts['2310'] and accounts['1020']:
            cursor.execute("""
                INSERT INTO finance_journals 
                (journal_number, journal_type, journal_date, description, reference, source_module,
                 status, period_id, company_id, created_by, total_debit, total_credit)
                VALUES (?, 'Tax', ?, ?, ?, 'Tax', 'Posted', ?, 1, 1, ?, ?)
            """, (vat_num, vat_date, desc, vat_num, period_id, amount, amount))
            
            je_id = cursor.lastrowid
            
            # Debit VAT Payable
            cursor.execute("""
                INSERT INTO finance_journal_lines 
                (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
                VALUES (?, 1, ?, 'VAT paid to tax authority', ?, 0, NULL)
            """, (je_id, accounts['2310'], amount))
            
            # Credit Cash
            cursor.execute("""
                INSERT INTO finance_journal_lines 
                (journal_id, line_number, account_id, description, debit, credit, cost_center_id)
                VALUES (?, 2, ?, 'Cash paid', 0, ?, NULL)
            """, (je_id, accounts['1020'], amount))
    
    conn.commit()
    print("- Seeded tax transactions (6 VAT payments)")

def seed_reconciliations(conn):
    """Seed bank reconciliation sets."""
    cursor = conn.cursor()
    
    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master WHERE type='table' AND name='finance_reconciliation_sets'
    """)
    if not cursor.fetchone():
        print("- finance_reconciliation_sets table does not exist, skipping reconciliations")
        return
    
    cursor.execute("SELECT COUNT(*) FROM finance_reconciliation_sets")
    if cursor.fetchone()[0] > 0:
        print("- Reconciliation sets already exist, skipping")
        return
    
    cursor.execute("SELECT id FROM finance_bank_accounts LIMIT 1")
    bank = cursor.fetchone()
    bank_id = bank['id'] if bank else 1
    
    # Get a past period
    cursor.execute("SELECT id FROM finance_fiscal_periods WHERE strftime('%Y', start_date) = '2026' AND period_number = '03'")
    period = cursor.fetchone()
    period_id = period['id'] if period else 1
    
    reconciliations = [
        # March 2026 reconciliation - in progress
        # (recon_type, ref_date, bank_id, status, total, matched, unmatched, debit, credit, diff, reviewed_by, reviewed_at, notes)
        ('RECON-2026-03', '2026-03-31', bank_id, 'In Progress', 15, 12, 3, 500000.00, 485000.00, 15000.00, None, None, 'March 2026 bank reconciliation'),
        # February 2026 - completed
        ('RECON-2026-02', '2026-02-28', bank_id, 'Completed', 18, 18, 0, 480000.00, 480000.00, 0.00, 1, '2026-02-28', 'February 2026 - reconciled'),
        # January 2026 - completed
        ('RECON-2026-01', '2026-01-31', bank_id, 'Completed', 20, 20, 0, 450000.00, 450000.00, 0.00, 1, '2026-01-31', 'January 2026 - reconciled'),
    ]
    
    for recon in reconciliations:
        cursor.execute("""
            INSERT INTO finance_reconciliation_sets 
            (reconciliation_type, reference_date, bank_account_id, status, total_items, matched_items, 
             unmatched_items, total_debit, total_credit, difference, reviewed_by, reviewed_at, notes, company_id, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, 1)
        """, recon)
        
        set_id = cursor.lastrowid
        
        # Add some reconciliation items for the in-progress one
        if '2026-03' in recon[0]:
            items = [
                ('Statement', 'CHK-101', '2026-03-05', 'Deposit - customer payment', 25000.00, 0),
                ('Statement', 'CHK-102', '2026-03-10', 'Deposit - customer payment', 35000.00, 0),
                ('Statement', 'CHK-103', '2026-03-15', 'Wire transfer out - rent', 0, 25000.00),
                ('Statement', 'CHK-104', '2026-03-20', 'Wire transfer out - supplier', 0, 45000.00),
                ('Book', 'JE-2026-015', '2026-03-05', 'Customer receipt - Al Fardan', 25000.00, 0),
                ('Book', 'JE-2026-016', '2026-03-10', 'Customer receipt - Dubai Retail', 35000.00, 0),
                ('Book', 'JE-2026-017', '2026-03-15', 'Rent payment', 0, 25000.00),
                ('Book', 'JE-2026-018', '2026-03-20', 'Supplier payment', 0, 45000.00),
            ]
            
            for i, item_data in enumerate(items[:6]):
                cursor.execute("""
                    INSERT INTO finance_reconciliation_items 
                    (set_id, item_type, source, source_id, transaction_date, description, debit, credit, is_matched)
                    VALUES (?, ?, ?, NULL, ?, ?, ?, ?, ?)
                """, (set_id, item_data[0], item_data[1], item_data[2], item_data[3], item_data[4], item_data[5], 1 if i < 6 else 0))
    
    conn.commit()
    print("- Seeded reconciliation sets (3 sets)")

def date_delta(days):
    return (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

def main():
    print("=" * 60)
    print("SEEDING FINANCE MODULE DEMO DATA")
    print("=" * 60)
    
    try:
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
        seed_profit_centers(conn)
        seed_bank_accounts(conn)
        seed_journal_entries(conn)
        seed_journal_entries_expanded(conn)
        seed_ar_invoices(conn)
        seed_ar_invoices_expanded(conn)
        seed_ap_bills(conn)
        seed_ap_bills_expanded(conn)
        seed_ar_receipts(conn)
        seed_ap_payments(conn)
        seed_fixed_assets(conn)
        seed_asset_transactions(conn)
        seed_depreciation_runs(conn)
        seed_budgets(conn)
        seed_budget_actuals(conn)
        seed_tax_transactions(conn)
        seed_reconciliations(conn)
        
        print("\n" + "=" * 60)
        print("FINANCE DATA SEEDING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\nSeed data includes:")
        print("- Account categories (8 categories)")
        print("- Chart of accounts (70+ accounts)")
        print("- Fiscal years 2024, 2025, 2026 with 12 periods each")
        print("- Tax codes (VAT, Sales Tax, Customs)")
        print("- Cost centers (8 departments)")
        print("- Profit centers (5 business segments)")
        print("- Bank accounts (5 accounts)")
        print("- Journal entries (30+ entries with double-entry bookkeeping)")
        print("- AR invoices (18 invoices with mix of paid/unpaid/overdue)")
        print("- AR receipts (10 customer receipts)")
        print("- AP bills (18 supplier bills)")
        print("- AP payments (10 supplier payments)")
        print("- Fixed assets (8 assets with acquisitions/disposals/transfers)")
        print("- Asset transactions (6 transactions)")
        print("- Depreciation runs (8 monthly runs)")
        print("- Budgets (4 budgets with monthly allocations)")
        print("- Budget actuals (24 actual entries)")
        print("- Tax transactions (6 VAT payments)")
        print("- Bank reconciliations (3 reconciliation sets)")
        print("\nRun: python app.py and navigate to Finance module.")
        
        conn.close()
        
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
