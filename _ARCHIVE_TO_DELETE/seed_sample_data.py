"""
Seed Sample Data Script
=======================
Populates the MMDx database with realistic sample data for demonstration purposes.
Run this script to see the dashboard with populated data.
"""

import sqlite3
import os
import random
from datetime import datetime, timedelta
import hashlib

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'warehouse.db')

def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def count_rows(table):
    cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
    return cursor.fetchone()['cnt']

def seed_data():
    global cursor
    db = get_db()
    cursor = db.cursor()
    
    print("Seeding sample data...")
    
    # =====================================================================
    # 1. SEED USERS (if empty or minimal)
    # =====================================================================
    print("Seeding users...")
    
    user_count = count_rows('users')
    
    if user_count < 5:
        users = [
            ('admin', 'admin@warehouse.local', 'Admin User', '123456', 1),
            ('ahmed.hassan', 'ahmed.hassan@warehouse.local', 'Ahmed Hassan', '123456', 2),
            ('fatima.ali', 'fatima.ali@warehouse.local', 'Fatima Ali', '123456', 3),
            ('omar.khalid', 'omar.khalid@warehouse.local', 'Omar Khalid', '123456', 1),
            ('sara.mohammed', 'sara.mohammed@warehouse.local', 'Sara Mohammed', '123456', 2),
            ('youssef.ali', 'youssef.ali@warehouse.local', 'Youssef Ali', '123456', 1),
            ('layla.ahmed', 'layla.ahmed@warehouse.local', 'Layla Ahmed', '123456', 1),
            ('khaled.saeed', 'khaled.saeed@warehouse.local', 'Khaled Saeed', '123456', 3),
            ('nour.hussein', 'nour.hussein@warehouse.local', 'Nour Hussein', '123456', 1),
            ('tariq.mansoor', 'tariq.mansoor@warehouse.local', 'Tariq Mansoor', '123456', 1),
        ]
        
        for username, email, name, password, role_id in users:
            password_hash = hash_password(password)
            cursor.execute("""
                INSERT OR IGNORE INTO users (username, email, password, role_id, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (username, email, password_hash, role_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        db.commit()
    else:
        print(f"  Skipping users (already has {user_count} records)")
    
    # Get user IDs
    user_ids = {}
    cursor.execute("SELECT id, username FROM users")
    for row in cursor.fetchall():
        user_ids[row['username']] = row['id']
    
    # =====================================================================
    # 2. SEED HR DEPARTMENTS (if empty)
    # =====================================================================
    print("Seeding HR departments...")
    
    dept_count = count_rows('hr_departments')
    
    if dept_count < 3:
        departments = [
            (1, 'Executive', 'EXEC', 'Executive Leadership', 'Active'),
            (2, 'Sales & Marketing', 'SALES', 'Sales and Marketing', 'Active'),
            (3, 'Human Resources', 'HR', 'Human Resources', 'Active'),
            (4, 'Finance & Accounting', 'FIN', 'Finance and Accounting', 'Active'),
            (5, 'Operations & Warehouse', 'OPS', 'Operations and Warehouse', 'Active'),
            (6, 'Procurement', 'PROC', 'Procurement and Supply Chain', 'Active'),
            (7, 'Information Technology', 'IT', 'IT Support and Systems', 'Active'),
            (8, 'Quality Assurance', 'QA', 'Quality Assurance', 'Active'),
        ]
        
        for dept_id, name, code, desc, status in departments:
            cursor.execute("""
                INSERT OR IGNORE INTO hr_departments (id, name, code, description, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (dept_id, name, code, desc, status, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        db.commit()
    else:
        print(f"  Skipping departments (already has {dept_count} records)")
    
    # =====================================================================
    # 3. SEED HR POSITIONS (if empty)
    # =====================================================================
    print("Seeding HR positions...")
    
    pos_count = count_rows('hr_positions')
    
    if pos_count < 5:
        positions = [
            (1, 'CEO', 1, 'Chief Executive Officer', 'Executive'),
            (2, 'CFO', 1, 'Chief Financial Officer', 'Executive'),
            (3, 'CTO', 1, 'Chief Technology Officer', 'Executive'),
            (4, 'Sales Manager', 2, 'Sales Manager', 'Management'),
            (5, 'Sales Executive', 2, 'Sales Executive', 'Staff'),
            (6, 'HR Manager', 3, 'HR Manager', 'Management'),
            (7, 'HR Officer', 3, 'HR Officer', 'Staff'),
            (8, 'Accountant', 4, 'Accountant', 'Staff'),
            (9, 'Warehouse Manager', 5, 'Warehouse Manager', 'Management'),
            (10, 'Forklift Operator', 5, 'Forklift Operator', 'Staff'),
            (11, 'Procurement Manager', 6, 'Procurement Manager', 'Management'),
            (12, 'Procurement Officer', 6, 'Procurement Officer', 'Staff'),
            (13, 'IT Manager', 7, 'IT Manager', 'Management'),
            (14, 'IT Support', 7, 'IT Support Specialist', 'Staff'),
            (15, 'QA Manager', 8, 'Quality Assurance Manager', 'Management'),
        ]
        
        for pos_id, title, dept_id, desc, grade in positions:
            cursor.execute("""
                INSERT OR IGNORE INTO hr_positions (id, title, department_id, description, grade, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (pos_id, title, dept_id, desc, grade, 'Active', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        db.commit()
    else:
        print(f"  Skipping positions (already has {pos_count} records)")
    
    # =====================================================================
    # 4. SEED LEAVE TYPES (if empty)
    # =====================================================================
    print("Seeding leave types...")
    
    lt_count = count_rows('hr_leave_types')
    
    if lt_count < 3:
        leave_types = [
            (1, 'Annual Leave', 'AL', 21, 1, 1, 0),
            (2, 'Sick Leave', 'SL', 14, 1, 1, 1),
            (3, 'Emergency Leave', 'EL', 5, 1, 1, 0),
            (4, 'Maternity Leave', 'ML', 90, 0, 1, 1),
            (5, 'Paternity Leave', 'PL', 5, 0, 1, 0),
        ]
        
        for lt_id, name, code, days, is_paid, requires_approval, requires_doc in leave_types:
            cursor.execute("""
                INSERT OR IGNORE INTO hr_leave_types (id, name, code, default_days, is_paid, requires_approval, requires_document, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (lt_id, name, code, days, is_paid, requires_approval, requires_doc, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        db.commit()
    else:
        print(f"  Skipping leave types (already has {lt_count} records)")
    
    # =====================================================================
    # 5. SEED HR EMPLOYEES (if empty)
    # =====================================================================
    print("Seeding HR employees...")
    
    emp_count = count_rows('hr_employees')
    
    if emp_count < 5:
        employee_data = [
            ('EMP-001', 'Ahmed', 'Mohammed', 'Al Hasan', 'Male', 'UAE', datetime(1980, 5, 15).strftime('%Y-%m-%d'), 'Single'),
            ('EMP-002', 'Fatima', 'Ali', 'Al Zahra', 'Female', 'UAE', datetime(1985, 8, 22).strftime('%Y-%m-%d'), 'Married'),
            ('EMP-003', 'Omar', 'Khalid', 'Al Maktoum', 'Male', 'UAE', datetime(1982, 3, 10).strftime('%Y-%m-%d'), 'Married'),
            ('EMP-004', 'Sara', 'Youssef', 'Al Subhi', 'Female', 'Oman', datetime(1990, 11, 5).strftime('%Y-%m-%d'), 'Single'),
            ('EMP-005', 'Youssef', 'Ibrahim', 'Al Hamadi', 'Male', 'Saudi Arabia', datetime(1988, 7, 18).strftime('%Y-%m-%d'), 'Married'),
            ('EMP-006', 'Layla', 'Hassan', 'Al Qasimi', 'Female', 'UAE', datetime(1992, 2, 28).strftime('%Y-%m-%d'), 'Single'),
            ('EMP-007', 'Khaled', 'Saeed', 'Al Nuaimi', 'Male', 'UAE', datetime(1987, 9, 14).strftime('%Y-%m-%d'), 'Married'),
            ('EMP-008', 'Nour', 'Mahmoud', 'Al Husseini', 'Female', 'Jordan', datetime(1995, 4, 20).strftime('%Y-%m-%d'), 'Single'),
            ('EMP-009', 'Tariq', 'Mansoor', 'Al Mazrouei', 'Male', 'UAE', datetime(1983, 12, 8).strftime('%Y-%m-%d'), 'Married'),
            ('EMP-010', 'Mariam', 'Faisal', 'Al Breiki', 'Female', 'UAE', datetime(1991, 6, 25).strftime('%Y-%m-%d'), 'Married'),
            ('EMP-011', 'Hassan', 'Ali', 'Al Rashidi', 'Male', 'Kuwait', datetime(1986, 10, 12).strftime('%Y-%m-%d'), 'Single'),
            ('EMP-012', 'Amira', 'Hussein', 'Al Adawi', 'Female', 'Egypt', datetime(1993, 1, 30).strftime('%Y-%m-%d'), 'Married'),
            ('EMP-013', 'Faisal', 'Abdulrahman', 'Al Muhairi', 'Male', 'UAE', datetime(1989, 8, 5).strftime('%Y-%m-%d'), 'Single'),
            ('EMP-014', 'Salma', 'Khalil', 'Al Shamsi', 'Female', 'UAE', datetime(1994, 3, 17).strftime('%Y-%m-%d'), 'Single'),
            ('EMP-015', 'Bilal', 'Yousef', 'Al Kindi', 'Male', 'Pakistan', datetime(1990, 7, 22).strftime('%Y-%m-%d'), 'Married'),
        ]
        
        for emp_code, first, middle, last, gender, nat, dob, marital in employee_data:
            hire_date = (datetime.now() - timedelta(days=random.randint(180, 1500))).strftime('%Y-%m-%d')
            
            cursor.execute("""
                INSERT INTO hr_employees 
                (employee_code, first_name, middle_name, last_name, gender, nationality,
                 date_of_birth, marital_status, mobile, email, status, hire_date, employment_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                emp_code, first, middle, last, gender, nat, dob, marital,
                f'+971-50-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                f'{first.lower()}.{last.lower()}@warehouse.local',
                'Active', hire_date, 'Full-time',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            
            emp_id = cursor.lastrowid
            
            # Create employment record
            cursor.execute("""
                INSERT INTO hr_employee_employment 
                (employee_id, company_id, department_id, position_id, employment_status, contract_type, start_date, is_primary, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (emp_id, 1, random.randint(1, 8), random.randint(1, 15), 'Active', 'Permanent', hire_date, 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            # Initialize leave balances
            current_year = datetime.now().year
            leave_types_list = [(1, 21), (2, 14), (3, 5)]
            for lt_id, default_days in leave_types_list:
                used = random.randint(0, default_days // 2)
                cursor.execute("""
                    INSERT INTO hr_leave_balances (employee_id, leave_type_id, year, total_days, used_days, pending_days)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (emp_id, lt_id, current_year, default_days, used, 0))
        
        db.commit()
    else:
        print(f"  Skipping employees (already has {emp_count} records)")
    
    # =====================================================================
    # 6. SEED ATTENDANCE RECORDS (if empty)
    # =====================================================================
    print("Seeding attendance records...")
    
    att_count = count_rows('hr_attendance_records')
    
    if att_count < 50:
        cursor.execute("SELECT id FROM hr_employees WHERE status = 'Active' LIMIT 10")
        emp_ids = [row['id'] for row in cursor.fetchall()]
        
        statuses_att = ['Present', 'Present', 'Present', 'Present', 'Present', 'Absent', 'Late', 'On Leave']
        
        for emp_id in emp_ids:
            for days_ago in range(1, 31):
                date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
                
                # Skip weekends
                weekday = (datetime.now() - timedelta(days=days_ago)).weekday()
                if weekday >= 5:
                    continue
                
                status = random.choice(statuses_att)
                check_in = '08:30' if status in ['Present', 'Late'] else None
                check_out = '17:30' if status in ['Present', 'Late'] else None
                late_minutes = 15 if status == 'Late' else 0
                
                cursor.execute("""
                    INSERT OR IGNORE INTO hr_attendance_records 
                    (employee_id, date, check_in, check_out, status, late_minutes, work_hours, remarks)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (emp_id, date, check_in, check_out, status, late_minutes, 8 if status == 'Present' else 0, ''))
        
        db.commit()
    else:
        print(f"  Skipping attendance (already has {att_count} records)")
    
    # =====================================================================
    # 7. SEED TASKS (if table exists and empty)
    # =====================================================================
    print("Seeding tasks...")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'")
    if cursor.fetchone():
        task_count = count_rows('tasks')
        if task_count < 5:
            tasks = [
                ('Review quarterly sales report', 'Open', 'High', 'Sales & Marketing'),
                ('Update inventory system', 'In Progress', 'Medium', 'Operations & Warehouse'),
                ('HR policy revision', 'Open', 'Medium', 'Human Resources'),
                ('Equipment maintenance check', 'Open', 'Low', 'Operations & Warehouse'),
                ('Prepare budget projection', 'In Progress', 'High', 'Finance & Accounting'),
                ('Supplier contract renewal', 'Review', 'Medium', 'Procurement'),
                ('Staff training session', 'Open', 'Medium', 'Human Resources'),
                ('System backup verification', 'Completed', 'High', 'Information Technology'),
                ('Quality audit preparation', 'In Progress', 'High', 'Quality Assurance'),
                ('Customer feedback review', 'Open', 'Medium', 'Sales & Marketing'),
            ]
            
            for title, status, priority, department in tasks:
                due_date = (datetime.now() + timedelta(days=random.randint(1, 30))).strftime('%Y-%m-%d')
                cursor.execute("""
                    INSERT INTO tasks (title, status, priority, department, due_date, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (title, status, priority, department, due_date, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            db.commit()
        else:
            print(f"  Skipping tasks (already has {task_count} records)")
    
    # =====================================================================
    # 8. SEED ISSUES (if table exists and empty)
    # =====================================================================
    print("Seeding issues...")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='issues'")
    if cursor.fetchone():
        issue_count = count_rows('issues')
        if issue_count < 5:
            issues = [
                ('Delayed shipment from supplier', 'High', 'Procurement', 'Open'),
                ('System login issue', 'Medium', 'Information Technology', 'In Progress'),
                ('Customer complaint - wrong item', 'Medium', 'Sales & Marketing', 'Open'),
                ('Warehouse temperature alert', 'Critical', 'Operations & Warehouse', 'Open'),
                ('Invoice discrepancy', 'Low', 'Finance & Accounting', 'Resolved'),
                ('Staff shortage - night shift', 'High', 'Operations & Warehouse', 'Open'),
            ]
            
            for title, severity, department, status in issues:
                cursor.execute("""
                    INSERT INTO issues (title, severity, department, status, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (title, severity, department, status, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            db.commit()
        else:
            print(f"  Skipping issues (already has {issue_count} records)")
    
    # =====================================================================
    # 9. SEED ANNOUNCEMENTS (if table exists and empty)
    # =====================================================================
    print("Seeding announcements...")
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='hr_announcements'")
    if cursor.fetchone():
        ann_count = count_rows('hr_announcements')
        if ann_count < 3:
            announcements = [
                ('Welcome to MMDx Platform', 'We are excited to announce the launch of our new unified dashboard system. This platform brings together all HR, inventory, sales, and management functions in one beautiful interface.', 'General', 'Normal', 1, None, None),
                ('Office Closure Notice', 'The office will be closed on National Day, December 2nd. All staff are requested to plan accordingly. Emergency contacts remain active.', 'Urgent', 'High', 1, '2026-12-01', '2026-12-03'),
                ('New HR Policy Update', 'Please review the updated leave and attendance policies effective January 2026. Key changes include flexible working hours and enhanced parental leave.', 'Policy', 'High', 1, '2026-01-01', '2026-06-30'),
                ('Sales Target Achievement', 'Congratulations to the sales team for achieving 120% of Q3 targets! A celebration event will be held next Friday.', 'Event', 'Normal', 1, None, None),
                ('IT System Maintenance', 'Scheduled maintenance window: Saturday 2:00 AM - 6:00 AM. All systems will be unavailable during this period.', 'IT', 'Critical', 1, None, None),
                ('Holiday Schedule 2026', 'The official holiday schedule for 2026 has been published. Please check the HR portal for detailed information.', 'HR', 'Normal', 1, '2026-01-01', '2026-12-31'),
            ]

            for title, content, ann_type, priority, is_active, valid_from, valid_to in announcements:
                cursor.execute("""
                    INSERT INTO hr_announcements (title, content, announcement_type, priority, is_active, valid_from, valid_to, created_by_id, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
                """, (title, content, ann_type, priority, is_active, valid_from, valid_to, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            
            db.commit()
        else:
            print(f"  Skipping announcements (already has {ann_count} records)")
    
    # =====================================================================
    # 10. SEED PLATFORM SETTINGS
    # =====================================================================
    print("Seeding settings...")
    
    settings = [
        ('default_currency', 'AED', 'GENERAL'),
        ('tax_percent', '5', 'GENERAL'),
        ('company_name', 'MMDx Trading LLC', 'COMPANY'),
        ('support_email', 'support@warehouse.local', 'COMPANY'),
    ]
    
    for key, value, category in settings:
        cursor.execute("""
            INSERT OR REPLACE INTO platform_settings (setting_key, setting_value, category, created_at)
            VALUES (?, ?, ?, ?)
        """, (key, value, category, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
    
    db.commit()
    
    # =====================================================================
    # COMPLETE
    # =====================================================================
    db.close()
    
    print("\n" + "="*50)
    print("Sample data seeded successfully!")
    print("="*50)
    print("\nLogin credentials:")
    print("  Username: admin  | Password: 123456")
    print("  Username: ahmed.hassan  | Password: 123456")
    print("  Username: fatima.ali  | Password: 123456")
    print("\nExplore the dashboard to see sample data!")

if __name__ == '__main__':
    seed_data()
