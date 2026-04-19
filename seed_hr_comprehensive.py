"""
HR Module Comprehensive Sample Data Seeder
==========================================
This script seeds comprehensive sample data across all HR module areas.
Run this after initial HR migrations to populate demo data.

Usage:
    python seed_hr_comprehensive.py
"""

from datetime import datetime, timedelta, date
import random
import sqlite3

def get_db():
    """Get database connection."""
    return sqlite3.connect('whdash.db')

def seed_hr_comprehensive():
    """Seed comprehensive HR sample data."""
    db = get_db()
    cursor = db.cursor()
    
    try:
        print("Starting HR comprehensive data seeding...")
        
        # Get existing IDs for foreign key references
        departments = db.execute("SELECT id, name FROM hr_departments").fetchall()
        positions = db.execute("SELECT id, title FROM hr_positions").fetchall()
        leave_types = db.execute("SELECT id, name FROM hr_leave_types").fetchall()
        shifts = db.execute("SELECT id, name FROM hr_shifts").fetchall()
        employees = db.execute("SELECT id, first_name, last_name FROM hr_employees").fetchall()
        
        dept_dict = {d['name']: d['id'] for d in departments}
        pos_dict = {p['title']: p['id'] for p in positions}
        leave_dict = {lt['name']: lt['id'] for lt in leave_types}
        shift_dict = {s['name']: s['id'] for s in shifts}
        emp_list = [(e['id'], e['first_name'], e['last_name']) for e in employees]
        
        # =====================================================================
        # 1. SEED ADDITIONAL DEPARTMENTS
        # =====================================================================
        additional_depts = [
            ('Legal', 'Active'),
            ('Public Relations', 'Active'),
            ('Research & Development', 'Active'),
            ('Customer Success', 'Active'),
        ]
        
        for name, status in additional_depts:
            try:
                db.execute("INSERT INTO hr_departments (name, code, status) VALUES (?, ?, ?)",
                          (name, name[:3].upper(), status))
            except:
                pass
        
        db.commit()
        print("  [OK] Departments seeded")
        
        # =====================================================================
        # 2. SEED ADDITIONAL POSITIONS
        # =====================================================================
        additional_positions = [
            ('Legal Counsel', 'Legal', 'A002'),
            ('PR Manager', 'Public Relations', 'A003'),
            ('R&D Engineer', 'Research & Development', 'A004'),
            ('Customer Success Manager', 'Customer Success', 'A005'),
        ]
        
        for title, dept, code in additional_positions:
            try:
                db.execute("INSERT INTO hr_positions (title, department, code, is_active) VALUES (?, ?, ?, 1)",
                          (title, dept, code))
            except:
                pass
        
        db.commit()
        print("  [OK] Positions seeded")
        
        # =====================================================================
        # 3. SEED ATTENDANCE RECORDS
        # =====================================================================
        today = date.today()
        
        for emp_id, fname, lname in emp_list[:20]:  # First 20 employees
            for days_ago in range(30):  # Last 30 days
                att_date = today - timedelta(days=days_ago)
                day_name = att_date.strftime('%A')
                
                # Skip weekends for some realism
                if day_name in ['Saturday', 'Sunday'] and random.random() < 0.7:
                    continue
                
                # Random status: Present (85%), Late (10%), Absent (5%)
                status_rand = random.random()
                if status_rand < 0.85:
                    status = 'Present'
                    check_in = f"{random.randint(7, 9)}:{random.randint(0, 59):02d}:00"
                    check_out = f"{random.randint(16, 19)}:{random.randint(0, 59):02d}:00"
                elif status_rand < 0.95:
                    status = 'Late'
                    check_in = f"{9}:{random.randint(10, 59):02d}:00"
                    check_out = f"{random.randint(16, 18)}:{random.randint(0, 59):02d}:00"
                else:
                    status = 'Absent'
                    check_in = None
                    check_out = None
                
                try:
                    db.execute("""
                        INSERT INTO hr_attendance_records 
                        (employee_id, attendance_date, check_in, check_out, status, shift_id)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (emp_id, att_date.isoformat(), check_in, check_out, status, 
                          shift_dict.get('Day Shift (UAE)', 1)))
                except:
                    pass
        
        db.commit()
        print("  [OK] Attendance records seeded")
        
        # =====================================================================
        # 4. SEED LEAVE REQUESTS AND BALANCES
        # =====================================================================
        leave_statuses = ['Approved', 'Pending', 'Rejected']
        
        for emp_id, fname, lname in emp_list[:15]:  # First 15 employees
            year = today.year
            
            # Create leave balance for each leave type
            for lt_name, lt_id in leave_dict.items():
                try:
                    db.execute("""
                        INSERT INTO hr_leave_balances
                        (employee_id, leave_type_id, year, total_days, used_days, pending_days, balance_days)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (emp_id, lt_id, year, 
                          random.randint(10, 30),  # total_days
                          random.randint(0, 10),   # used_days  
                          random.randint(0, 3),   # pending_days
                          random.randint(5, 20)))  # balance_days
                except:
                    pass
            
            # Create some leave requests
            for _ in range(random.randint(0, 3)):
                lt_name = random.choice(list(leave_dict.keys()))
                lt_id = leave_dict[lt_name]
                start_date = today + timedelta(days=random.randint(1, 60))
                end_date = start_date + timedelta(days=random.randint(1, 5))
                status = random.choice(leave_statuses)
                
                try:
                    db.execute("""
                        INSERT INTO hr_leave_requests
                        (employee_id, leave_type_id, start_date, end_date, total_days,
                         reason, status, applied_on)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (emp_id, lt_id, start_date.isoformat(), end_date.isoformat(),
                          (end_date - start_date).days + 1,
                          f'Personal leave request',
                          status, (today - timedelta(days=random.randint(1, 30))).isoformat()))
                except:
                    pass
        
        db.commit()
        print("  [OK] Leave requests and balances seeded")
        
        # =====================================================================
        # 5. SEED PAYROLL PERIODS AND RECORDS
        # =====================================================================
        # Create payroll periods for last 6 months
        for months_ago in range(6):
            year = today.year
            month = today.month - months_ago
            if month <= 0:
                month += 12
                year -= 1
            
            period_name = f"{year}-{month:02d}"
            
            try:
                db.execute("""
                    INSERT INTO hr_payroll_periods
                    (name, year, month, period_start, period_end, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (period_name, year, month,
                      f"{year}-{month:02d}-01",
                      f"{year}-{month:02d}-28" if month != 2 else f"{year}-{month:02d}-30",
                      'Closed' if months_ago > 0 else 'Open'))
                
                period_id = db.execute("SELECT last_insert_rowid() as id").fetchone()['id']
                
                # Create payroll records for some employees
                for emp_id, fname, lname in emp_list[:10]:
                    basic = random.randint(5000, 15000)
                    housing = basic * 0.25
                    transport = 500
                    food = 300
                    total_earnings = basic + housing + transport + food
                    total_deductions = total_earnings * 0.1
                    net = total_earnings - total_deductions
                    
                    try:
                        db.execute("""
                            INSERT INTO hr_payroll_records
                            (period_id, employee_id, basic_salary, housing_allowance,
                             transport_allowance, food_allowance, total_earnings,
                             total_deductions, net_salary, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (period_id, emp_id, basic, housing, transport, food,
                              total_earnings, total_deductions, net, 'Approved'))
                    except:
                        pass
                        
            except:
                pass
        
        db.commit()
        print("  [OK] Payroll periods and records seeded")
        
        # =====================================================================
        # 6. SEED OVERTIME REQUESTS
        # =====================================================================
        ot_statuses = ['Approved', 'Pending', 'Rejected']
        
        for emp_id, fname, lname in emp_list[:10]:
            for _ in range(random.randint(0, 2)):
                ot_date = today - timedelta(days=random.randint(1, 30))
                hours = random.choice([1, 2, 3, 4])
                status = random.choice(ot_statuses)
                
                try:
                    db.execute("""
                        INSERT INTO hr_overtime_requests
                        (employee_id, ot_date, hours, reason, status, applied_on)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (emp_id, ot_date.isoformat(), hours,
                          'Project deadline requirement', status,
                          (today - timedelta(days=random.randint(1, 10))).isoformat()))
                except:
                    pass
        
        db.commit()
        print("  [OK] Overtime requests seeded")
        
        # =====================================================================
        # 7. SEED TRAINING PROGRAMS AND ENROLLMENTS
        # =====================================================================
        programs = [
            ('Corporate Leadership', 'Leadership', 'Internal', 8, 16, 1),
            ('Technical Skills Workshop', 'Technical', 'External', 16, 40, 1),
            ('Communication Skills', 'Soft Skills', 'Internal', 8, 20, 1),
            ('Health & Safety', 'Compliance', 'Internal', 4, 50, 1),
            ('IT Security Awareness', 'IT', 'E-Learning', 2, 100, 1),
        ]
        
        program_ids = []
        for title, ptype, pcategory, duration, capacity, active in programs:
            try:
                db.execute("""
                    INSERT INTO hr_training_programs
                    (title, training_type, category, duration_hours, max_capacity, is_active, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (title, ptype, pcategory, duration, capacity, active,
                      f'Training program for {ptype.lower()}'))
                program_ids.append(db.execute("SELECT last_insert_rowid() as id").fetchone()['id'])
            except:
                pass
        
        db.commit()
        print("  [OK] Training programs seeded")
        
        # Create training sessions and enrollments
        for i, prog_id in enumerate(program_ids[:3]):
            start_date = today + timedelta(days=random.randint(1, 30))
            try:
                db.execute("""
                    INSERT INTO hr_training_sessions
                    (program_id, session_title, start_date, end_date, location, trainer, max_attendees)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (prog_id, f'Session {i+1}', start_date.isoformat(),
                      (start_date + timedelta(days=1)).isoformat(),
                      'Training Room A', 'External Trainer', 20))
                
                session_id = db.execute("SELECT last_insert_rowid() as id").fetchone()['id']
                
                # Enroll employees
                for emp_id, fname, lname in emp_list[:random.randint(5, 10)]:
                    status = random.choice(['Enrolled', 'Completed', 'In Progress'])
                    try:
                        db.execute("""
                            INSERT INTO hr_training_enrollments
                            (employee_id, session_id, status, completion_date, certificate_number)
                            VALUES (?, ?, ?, ?, ?)
                        """, (emp_id, session_id, status,
                              (today - timedelta(days=random.randint(1, 60))).isoformat() if status == 'Completed' else None,
                              f'CERT-{random.randint(10000, 99999)}' if status == 'Completed' else None))
                    except:
                        pass
            except:
                pass
        
        db.commit()
        print("  [OK] Training sessions and enrollments seeded")
        
        # =====================================================================
        # 8. SEED RECRUITMENT REQUISITIONS AND CANDIDATES
        # =====================================================================
        requisitions = [
            ('Senior Software Engineer', 'Engineering', 'Full-time', 'Open'),
            ('Marketing Manager', 'Marketing', 'Full-time', 'Open'),
            ('Sales Executive', 'Sales', 'Contract', 'In Progress'),
            ('HR Coordinator', 'Human Resources', 'Full-time', 'Closed'),
        ]
        
        req_ids = []
        for title, dept, emp_type, status in requisitions:
            try:
                db.execute("""
                    INSERT INTO hr_recruitment_requisitions
                    (title, department, employment_type, status, vacancy_count,
                     salary_min, salary_max, requested_by_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (title, dept, emp_type, status, random.randint(1, 3),
                      random.randint(5000, 10000), random.randint(10000, 20000), 1))
                req_ids.append(db.execute("SELECT last_insert_rowid() as id").fetchone()['id'])
            except:
                pass
        
        db.commit()
        print("  [OK] Recruitment requisitions seeded")
        
        # Add candidates
        candidate_names = [
            ('Ahmed', 'Hassan'), ('Fatima', 'Ali'), ('Mohammed', 'Khalid'),
            ('Aisha', 'Rahman'), ('Omar', 'Farouk'), ('Layla', 'Samir'),
        ]
        
        for req_id in req_ids[:2]:
            for fname, lname in candidate_names[:random.randint(3, 6)]:
                status = random.choice(['Applied', 'Screening', 'Interview', 'Offer', 'Hired'])
                try:
                    db.execute("""
                        INSERT INTO hr_candidates
                        (requisition_id, first_name, last_name, email, phone,
                         current_company, current_position, experience_years,
                         status, hiring_status, applied_on)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (req_id, fname, lname, f'{fname.lower()}.{lname.lower()}@email.com',
                          f'+97150{random.randint(1000000, 9999999)}',
                          f'Company {random.randint(1, 10)}',
                          f'Position {random.randint(1, 5)}',
                          random.randint(1, 15), status,
                          'Hired' if status == 'Hired' else 'In Process',
                          (today - timedelta(days=random.randint(1, 60))).isoformat()))
                except:
                    pass
        
        db.commit()
        print("  [OK] Candidates seeded")
        
        # =====================================================================
        # 9. SEED PERFORMANCE REVIEWS
        # =====================================================================
        review_types = ['Annual', 'Probation', 'Quarterly', 'Project-based']
        ratings = [1, 2, 3, 4, 5]
        
        for emp_id, fname, lname in emp_list[:15]:
            for _ in range(random.randint(1, 2)):
                review_date = today - timedelta(days=random.randint(1, 180))
                review_type = random.choice(review_types)
                rating = random.choice(ratings)
                status = random.choice(['Completed', 'Pending', 'In Progress'])
                
                try:
                    db.execute("""
                        INSERT INTO hr_performance_reviews
                        (employee_id, review_type, review_period, overall_rating,
                         strengths, areas_for_improvement, comments, status, reviewed_by_id, review_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (emp_id, review_type, review_date.strftime('%Y'),
                          rating if status == 'Completed' else None,
                          'Good communication skills',
                          'Time management can be improved',
                          f'Performance review for {fname}',
                          status, 1, review_date.isoformat()))
                except:
                    pass
        
        db.commit()
        print("  [OK] Performance reviews seeded")
        
        # =====================================================================
        # 10. SEED ANNOUNCEMENTS
        # =====================================================================
        announcements = [
            ('Company Annual Gala 2026', 'General', 'Normal', 
             'Join us for the annual company gala celebration...'),
            ('New HR Policy Update', 'Policy', 'High',
             'Please note the updated HR policies effective immediately...'),
            ('Office Renovation Notice', 'Facilities', 'Normal',
             'The office will undergo renovation starting next month...'),
            ('Holiday Schedule', 'General', 'Normal',
             'Please find attached the holiday schedule for the year...'),
        ]
        
        for title, atype, priority, content in announcements:
            try:
                db.execute("""
                    INSERT INTO hr_announcements
                    (title, content, announcement_type, priority, is_active,
                     valid_from, valid_to, created_by_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (title, content, atype, priority, 1,
                      today.isoformat(),
                      (today + timedelta(days=30)).isoformat(), 1))
            except:
                pass
        
        db.commit()
        print("  [OK] Announcements seeded")
        
        # =====================================================================
        # 11. SEED DOCUMENTS
        # =====================================================================
        doc_types = ['Passport', 'Emirates ID', 'Visa', 'Labour Card', 'Contract']
        
        for emp_id, fname, lname in emp_list[:10]:
            for doc_type in doc_types[:random.randint(2, 4)]:
                issue_date = today - timedelta(days=random.randint(100, 365))
                # Some expired, some valid
                if random.random() < 0.2:
                    expiry_date = today - timedelta(days=random.randint(1, 30))
                else:
                    expiry_date = today + timedelta(days=random.randint(30, 365))
                
                try:
                    db.execute("""
                        INSERT INTO hr_employee_documents
                        (employee_id, document_type, document_name, document_number,
                         issue_date, expiry_date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (emp_id, doc_type, f'{fname} {doc_type}',
                          f'DOC-{random.randint(100000, 999999)}',
                          issue_date.isoformat(), expiry_date.isoformat()))
                except:
                    pass
        
        db.commit()
        print("  [OK] Employee documents seeded")
        
        # =====================================================================
        # 12. SEED HR CASES
        # =====================================================================
        case_types = ['Complaint', 'Inquiry', 'Request', 'Grievance']
        case_statuses = ['Open', 'In Progress', 'Resolved', 'Closed']
        
        for emp_id, fname, lname in emp_list[:10]:
            for _ in range(random.randint(0, 2)):
                case_type = random.choice(case_types)
                status = random.choice(case_statuses)
                
                try:
                    db.execute("""
                        INSERT INTO hr_cases
                        (employee_id, case_type, subject, description, status,
                         priority, created_by_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (emp_id, case_type,
                          f'{case_type} regarding workplace',
                          f'Details about the {case_type.lower()} case',
                          status, random.choice(['Low', 'Medium', 'High']), 1))
                except:
                    pass
        
        db.commit()
        print("  [OK] HR cases seeded")
        
        # =====================================================================
        # 13. SEED LOANS
        # =====================================================================
        loan_statuses = ['Active', 'Completed', 'Pending']
        
        for emp_id, fname, lname in emp_list[:10]:
            if random.random() < 0.4:  # 40% have a loan
                status = random.choice(loan_statuses)
                loan_amount = random.randint(5000, 50000)
                monthly_deduction = random.randint(500, 2000)
                
                try:
                    db.execute("""
                        INSERT INTO hr_loans
                        (employee_id, loan_type, principal_amount, interest_rate,
                         monthly_deduction, tenure_months, remaining_amount,
                         status, application_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (emp_id, 'Personal Loan', loan_amount, 0,
                          monthly_deduction, loan_amount // monthly_deduction,
                          loan_amount if status == 'Active' else 0,
                          status, (today - timedelta(days=random.randint(30, 180))).isoformat()))
                except:
                    pass
        
        db.commit()
        print("  [OK] Loans seeded")
        
        print("\n" + "="*50)
        print("HR Comprehensive Data Seeding Complete!")
        print("="*50)
        print(f"  - Departments: {len(departments) + len(additional_depts)}")
        print(f"  - Employees: {len(employees)}")
        print(f"  - Attendance Records: ~600")
        print(f"  - Leave Balances & Requests: Multiple")
        print(f"  - Payroll Periods: 6")
        print(f"  - Training Programs: {len(programs)}")
        print(f"  - Recruitment: {len(requisitions)} requisitions + candidates")
        print(f"  - Performance Reviews: Multiple")
        print(f"  - Announcements: {len(announcements)}")
        print(f"  - Documents: Multiple")
        print(f"  - Cases: Multiple")
        print(f"  - Loans: Multiple")
        print("="*50)
        
    except Exception as e:
        print(f"Error during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    seed_hr_comprehensive()
