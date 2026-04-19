"""
Seed Payroll Data
=================
Comprehensive sample data for the payroll module including:
- Payroll periods
- Employee payroll profiles and components
- Sample payroll runs
- Loans and advances
- Retro adjustments
- Compliance rules
"""

import sqlite3
import os
from datetime import datetime, timedelta, date
import random

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'warehouse.db'))


def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def seed_payroll_data():
    """Seed comprehensive payroll sample data."""
    db = get_db()
    
    try:
        # Check if already seeded
        existing = db.execute("SELECT COUNT(*) as cnt FROM payroll_periods").fetchone()['cnt']
        if existing > 0:
            print("Payroll data already exists. Skipping seed.")
            return
        
        print("Seeding payroll data...")
        
        # 1. Create payroll calendar
        db.execute("""
            INSERT INTO payroll_calendar (name, code, description, country, pay_frequency, cycle_type,
                period_start_day, period_end_day, cutoff_day, payment_day, is_active, created_by)
            VALUES ('UAE Monthly', 'UAE_MONTHLY', 'UAE standard monthly payroll calendar', 'UAE', 'Monthly', 'Monthly',
                1, 31, 25, 28, 1, 1)
        """)
        calendar_id = db.execute("SELECT last_insert_rowid() as id").fetchone()['id']
        
        # 2. Create payroll periods for current year
        months = [
            ('January', 1), ('February', 2), ('March', 3), ('April', 4), ('May', 5), ('June', 6),
            ('July', 7), ('August', 8), ('September', 9), ('October', 10), ('November', 11), ('December', 12)
        ]
        current_year = datetime.now().year
        current_month = datetime.now().month
        
        period_ids = {}
        for month_name, month_num in months:
            start_date = date(current_year, month_num, 1)
            if month_num == 12:
                end_date = date(current_year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = date(current_year, month_num + 1, 1) - timedelta(days=1)
            
            cutoff = date(current_year, month_num, 25)
            payment = date(current_year, month_num, 28)
            
            # Determine status based on month
            if month_num > current_month:
                status = 'Open'
                run_status = 'Not Started'
            elif month_num == current_month:
                status = 'Processing'
                run_status = 'Draft'
            elif month_num == current_month - 1:
                status = 'Locked'
                run_status = 'Approved'
            else:
                status = 'Closed'
                run_status = 'Closed'
            
            cursor = db.execute("""
                INSERT INTO payroll_periods (calendar_id, name, period_key, month, year,
                    period_start, period_end, cutoff_date, payment_date, status, run_status,
                    fiscal_year, quarter, total_employees, total_gross, total_deductions, total_net)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                calendar_id, f"{month_name} {current_year}", f"{current_year}-{month_num:02d}",
                month_num, current_year, start_date, end_date, cutoff, payment,
                status, run_status, str(current_year), f"Q{(month_num-1)//3 + 1}",
                0, 0, 0, 0
            ))
            period_ids[month_num] = cursor.lastrowid
        
        # 3. Get existing employees for payroll profiles
        employees = db.execute("""
            SELECT id, first_name, last_name, employee_code FROM hr_employees 
            WHERE status = 'Active' LIMIT 50
        """).fetchall()
        
        if not employees:
            print("No employees found. Creating sample employees first...")
            # Create sample employees
            sample_employees = [
                ('EMP001', 'Ahmed', 'Al Mansouri', 'Active'),
                ('EMP002', 'Fatima', 'Al Zahra', 'Active'),
                ('EMP003', 'Mohammed', 'Hassan', 'Active'),
                ('EMP004', 'Sara', 'Khalid', 'Active'),
                ('EMP005', 'Omar', 'Ibrahim', 'Active'),
                ('EMP006', 'Layla', 'Mohammed', 'Active'),
                ('EMP007', 'Yusuf', 'Ahmed', 'Active'),
                ('EMP008', 'Noor', 'Hassan', 'Active'),
                ('EMP009', 'Ali', 'Omar', 'Active'),
                ('EMP010', 'Mariam', 'Khalid', 'Active'),
            ]
            for code, fname, lname, status in sample_employees:
                db.execute("""
                    INSERT INTO hr_employees (employee_code, first_name, last_name, status, hire_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (code, fname, lname, status, date(2020, 1, 1)))
            employees = db.execute("""
                SELECT id, first_name, last_name, employee_code FROM hr_employees 
                WHERE status = 'Active' LIMIT 50
            """).fetchall()
        
        # 4. Create payroll profiles for employees
        profile_ids = {}
        for emp in employees:
            cursor = db.execute("""
                INSERT INTO payroll_profiles (employee_id, payroll_group_id, pay_frequency, currency,
                    bank_name, payment_method, is_active, effective_from)
                VALUES (?, 1, 'Monthly', 'AED', 'First Abu Dhabi Bank', 'Bank Transfer', 1, ?)
            """, (emp['id'], date(2020, 1, 1)))
            profile_ids[emp['id']] = cursor.lastrowid
        
        # 5. Create profile components with realistic salaries
        components = db.execute("SELECT * FROM payroll_components WHERE is_active = 1").fetchall()
        basic_id = next((c['id'] for c in components if c['code'] == 'BASIC'), None)
        hra_id = next((c['id'] for c in components if c['code'] == 'HRA'), None)
        transport_id = next((c['id'] for c in components if c['code'] == 'TRANSPORT'), None)
        medical_id = next((c['id'] for c in components if c['code'] == 'MEDICAL'), None)
        
        salaries = [8000, 12000, 15000, 20000, 25000, 30000, 35000, 40000, 50000, 60000]
        
        for emp in employees:
            profile_id = profile_ids.get(emp['id'])
            if not profile_id:
                continue
            
            basic_salary = random.choice(salaries)
            hra_amount = basic_salary * 0.25
            transport_amount = 1500
            medical_amount = 800
            
            # Basic Salary
            if basic_id:
                db.execute("""
                    INSERT INTO payroll_profile_components (profile_id, component_id, amount, calculation_type, is_active, effective_from)
                    VALUES (?, ?, ?, 'Fixed', 1, ?)
                """, (profile_id, basic_id, basic_salary, date(2020, 1, 1)))
            
            # HRA
            if hra_id:
                db.execute("""
                    INSERT INTO payroll_profile_components (profile_id, component_id, amount, calculation_type, is_active, effective_from)
                    VALUES (?, ?, ?, 'Fixed', 1, ?)
                """, (profile_id, hra_id, hra_amount, date(2020, 1, 1)))
            
            # Transport
            if transport_id:
                db.execute("""
                    INSERT INTO payroll_profile_components (profile_id, component_id, amount, calculation_type, is_active, effective_from)
                    VALUES (?, ?, ?, 'Fixed', 1, ?)
                """, (profile_id, transport_id, transport_amount, date(2020, 1, 1)))
            
            # Medical
            if medical_id:
                db.execute("""
                    INSERT INTO payroll_profile_components (profile_id, component_id, amount, calculation_type, is_active, effective_from)
                    VALUES (?, ?, ?, 'Fixed', 1, ?)
                """, (profile_id, medical_id, medical_amount, date(2020, 1, 1)))
        
        # 6. Create sample payroll runs for past months
        for month_num in range(1, current_month - 1):
            period_id = period_ids.get(month_num)
            if not period_id:
                continue
            
            cursor = db.execute("""
                INSERT INTO payroll_runs (period_id, run_type, name, status, total_records,
                    total_gross, total_deductions, total_net, created_by_id, created_at)
                VALUES (?, 'Regular', ?, 'Approved', ?, ?, ?, ?, 1, ?)
            """, (
                period_id, f"Regular Run - {months[month_num-1][0]} {current_year}",
                len(employees), 0, 0, 0, datetime.now() - timedelta(days=30*(current_month-month_num))
            ))
            run_id = cursor.lastrowid
            
            # Create employee records
            total_gross = 0
            total_ded = 0
            total_net = 0
            
            for emp in employees:
                profile_id = profile_ids.get(emp['id'])
                if not profile_id:
                    continue
                
                # Get basic salary
                basic = db.execute("""
                    SELECT amount FROM payroll_profile_components 
                    WHERE profile_id = ? AND component_id = ?
                """, (profile_id, basic_id)).fetchone()
                
                basic_salary = basic['amount'] if basic else 10000
                total_allowances = basic_salary * 0.30
                gross = basic_salary + total_allowances
                deductions = gross * 0.10
                net = gross - deductions
                
                db.execute("""
                    INSERT INTO payroll_employee_records (run_id, period_id, employee_id, profile_id,
                        basic_salary, total_allowances, total_deductions, gross_salary, net_salary,
                        days_worked, status, approved_by_id, approved_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Approved', 1, ?)
                """, (run_id, period_id, emp['id'], profile_id, basic_salary, total_allowances,
                      deductions, gross, net, 30, datetime.now() - timedelta(days=30*(current_month-month_num))))
                
                total_gross += gross
                total_ded += deductions
                total_net += net
            
            # Update run totals
            db.execute("""
                UPDATE payroll_runs SET total_gross = ?, total_deductions = ?, total_net = ?
                WHERE id = ?
            """, (total_gross, total_ded, total_net, run_id))
            
            # Update period totals
            db.execute("""
                UPDATE payroll_periods SET total_employees = ?, total_gross = ?, 
                    total_deductions = ?, total_net = ?
                WHERE id = ?
            """, (len(employees), total_gross, total_ded, total_net, period_id))
        
        # 7. Create sample loans for some employees
        loan_types = ['Personal', 'Housing', 'Car', 'Education']
        for i, emp in enumerate(employees[:10]):
            principal = random.choice([10000, 20000, 30000, 50000])
            tenure = random.choice([6, 12, 18, 24])
            monthly = principal / tenure
            
            cursor = db.execute("""
                INSERT INTO payroll_loans (loan_number, employee_id, loan_type, principal_amount,
                    interest_rate, total_amount, tenure_months, monthly_installment,
                    amount_paid, amount_remaining, installments_paid, installments_remaining,
                    start_date, end_date, status, approved_by_id, approved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active', 1, ?)
            """, (
                f"LN{current_year}{i+1:04d}", emp['id'], random.choice(loan_types),
                principal, 0, principal, tenure, monthly,
                monthly * random.randint(1, tenure-1), principal - monthly * random.randint(1, tenure-1),
                random.randint(1, tenure-1), tenure - random.randint(1, tenure-1),
                date(current_year, 1, 1), date(current_year, 1, 1) + timedelta(days=30*tenure),
                datetime.now() - timedelta(days=60)
            ))
            loan_id = cursor.lastrowid
            
            # Create installments
            for j in range(1, tenure + 1):
                db.execute("""
                    INSERT INTO payroll_loan_installments (loan_id, installment_number, due_date,
                        installment_amount, principal_amount, interest_amount, amount_paid, status)
                    VALUES (?, ?, ?, ?, ?, 0, ?, ?)
                """, (
                    loan_id, j, date(current_year, 1, 1) + timedelta(days=30*j),
                    monthly, monthly, monthly, 'Paid' if j < tenure - 2 else 'Pending'
                ))
        
        # 8. Create sample advances
        for i, emp in enumerate(employees[5:8]):
            amount = random.choice([2000, 3000, 5000, 7000])
            db.execute("""
                INSERT INTO payroll_advances (advance_number, employee_id, amount, recovery_amount,
                    recovery_months, monthly_recovery, reason, status, approved_by_id, approved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'In Recovery', 1, ?)
            """, (
                f"ADV{current_year}{i+1:04d}", emp['id'], amount, amount,
                3, amount/3, 'Emergency advance', datetime.now() - timedelta(days=45)
            ))
        
        # 9. Create sample retro adjustments
        for emp in employees[:3]:
            retro_num = db.execute("SELECT COUNT(*) as cnt FROM payroll_retro_adjustments").fetchone()['cnt'] + 1
            db.execute("""
                INSERT INTO payroll_retro_adjustments (retro_number, employee_id, period_id,
                    adjustment_type, component_id, component_code, component_name,
                    original_amount, new_amount, difference, reason, status, approved_by_id, approved_at)
                VALUES (?, ?, ?, 'Correction', ?, 'BASIC', 'Basic Salary', ?, ?, ?, ?, 1, ?)
            """, (
                f"RETRO{current_year}{retro_num:04d}", emp['id'], period_ids.get(2),
                basic_id, 15000, 17000, 2000, 'Salary correction - missed increase',
                'Approved', datetime.now() - timedelta(days=30)
            ))
        
        # 10. Create sample payroll exceptions
        exception_types = [
            ('Missing Bank Details', 'High'),
            ('Tax ID Required', 'Critical'),
            ('Overtime Limit Exceeded', 'Medium'),
            ('Duplicate Payment Risk', 'Critical'),
            ('Leave Without Pay', 'Medium'),
        ]
        
        for i, (exc_type, severity) in enumerate(exception_types):
            emp = employees[i % len(employees)]
            db.execute("""
                INSERT INTO payroll_exceptions (period_id, employee_id, exception_type,
                    severity, error_message, status)
                VALUES (?, ?, ?, ?, ?, 'Open')
            """, (
                period_ids.get(current_month - 1), emp['id'], exc_type,
                severity, f"{exc_type} detected for {emp['first_name']} {emp['last_name']}"
            ))
        
        # 11. Create sample finance postings
        for month_num in range(1, min(4, current_month - 1)):
            period_id = period_ids.get(month_num)
            if not period_id:
                continue
            
            cursor = db.execute("""
                INSERT INTO payroll_finance_postings (posting_number, period_id, run_id,
                    posting_type, description, total_amount, status, posted_by_id, posted_at)
                VALUES (?, ?, NULL, 'Salary', ?, ?, 'Posted', 1, ?)
            """, (
                f"PP{current_year}{month_num:02d}001", period_id,
                f"Payroll posting for {months[month_num-1][0]} {current_year}",
                500000, datetime.now() - timedelta(days=30*(current_month-month_num))
            ))
            posting_id = cursor.lastrowid
            
            # Add journal lines
            db.execute("""
                INSERT INTO payroll_finance_lines (posting_id, gl_account, line_type, description, debit_amount)
                VALUES (?, '6100-Salary Expense', 'Debit', 'Salary expense', ?)
            """, (posting_id, 500000))
            
            db.execute("""
                INSERT INTO payroll_finance_lines (posting_id, gl_account, line_type, description, credit_amount)
                VALUES (?, '1200-Cash/Bank', 'Credit', 'Net salary payable', ?)
            """, (posting_id, 450000))
            
            db.execute("""
                INSERT INTO payroll_finance_lines (posting_id, gl_account, line_type, description, credit_amount)
                VALUES (?, '2200-Tax Payable', 'Credit', 'Tax withholding', ?)
            """, (posting_id, 50000))
        
        # 12. Create compliance results
        rules = db.execute("SELECT id, rule_code FROM payroll_compliance_rules").fetchall()
        for rule in rules[:5]:
            db.execute("""
                INSERT INTO payroll_compliance_results (period_id, rule_id, status, details, created_at)
                VALUES (?, ?, 'Pass', 'Validation passed', ?)
            """, (period_ids.get(current_month - 1), rule['id'], datetime.now() - timedelta(days=7)))
        
        # 13. Create sample audit log entries
        actions = ['CREATE', 'UPDATE', 'APPROVE', 'VIEW', 'EXPORT']
        for i in range(20):
            emp = employees[i % len(employees)]
            action = random.choice(actions)
            db.execute("""
                INSERT INTO payroll_audit_log (action, entity_type, entity_id, user_id,
                    employee_id, period_id, change_details, created_at)
                VALUES (?, 'payroll_employee_records', ?, 1, ?, ?, ?, ?)
            """, (
                action, emp['id'], emp['id'], period_ids.get(current_month - 1),
                f"Sample {action.lower()} action",
                datetime.now() - timedelta(hours=random.randint(1, 720))
            ))
        
        # 14. Create payroll settings if not exist
        settings = [
            ('payroll_currency', 'AED', 'String', 'General'),
            ('overtime_rate_weekday', '1.50', 'Number', 'Overtime'),
            ('overtime_rate_weekend', '2.00', 'Number', 'Overtime'),
            ('overtime_rate_holiday', '2.50', 'Number', 'Overtime'),
            ('auto_generate_payslips', 'true', 'Boolean', 'Payslip'),
            ('require_payslip_approval', 'false', 'Boolean', 'Payslip'),
            ('enable_payroll_approval_workflow', 'true', 'Boolean', 'Workflow'),
            ('lock_period_on_approval', 'true', 'Boolean', 'Period'),
            ('retro_processing_enabled', 'true', 'Boolean', 'Retro'),
            ('loan_recovery_auto', 'true', 'Boolean', 'Loan'),
        ]
        
        for key, value, stype, cat in settings:
            db.execute("""
                INSERT INTO payroll_settings (setting_key, setting_value, setting_type, category, is_active)
                VALUES (?, ?, ?, ?, 1)
            """, (key, value, stype, cat))
        
        db.commit()
        print("Payroll sample data seeded successfully!")
        print(f"  - {len(employees)} employees with payroll profiles")
        print(f"  - {len(period_ids)} payroll periods created")
        print(f"  - 10 sample loans created")
        print(f"  - Sample exceptions, retro adjustments, and finance postings created")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding payroll data: {str(e)}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    seed_payroll_data()
