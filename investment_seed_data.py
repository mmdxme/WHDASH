"""
Investment Management Seed Data - Direct SQL Version
"""
import sqlite3
import os
from random import uniform

DATABASE = r'C:\Users\sdads\WHDASH\warehouse.db'

INVESTMENTS = [
    {'code': 'INV1001', 'title': 'Dubai Warehouse Phase 2 Expansion', 'category': 'Warehouse Expansion', 'budget': 2500000, 'approved': 2300000, 'roi': 28.5, 'status': 'Approved', 'stage': 'In Execution'},
    {'code': 'INV1002', 'title': 'Automated Storage & Retrieval System', 'category': 'Automation Equipment', 'budget': 1800000, 'approved': 1650000, 'roi': 35.2, 'status': 'Approved', 'stage': 'Implemented'},
    {'code': 'INV1003', 'title': 'ERP System Upgrade to S/4HANA', 'category': 'ERP Upgrade', 'budget': 950000, 'approved': 950000, 'roi': 42.0, 'status': 'Approved', 'stage': 'In Execution'},
    {'code': 'INV1004', 'title': 'Fleet Expansion - 20 Delivery Trucks', 'category': 'Delivery Fleet', 'budget': 3200000, 'approved': 0, 'roi': 22.1, 'status': 'Under Review', 'stage': 'Under Review'},
    {'code': 'INV1005', 'title': 'Warehouse Racking - Sharjah Facility', 'category': 'Racking System', 'budget': 880000, 'approved': 820000, 'roi': 31.0, 'status': 'Approved', 'stage': 'Implemented'},
    {'code': 'INV1006', 'title': 'CCTV & Security System Upgrade', 'category': 'CCTV', 'budget': 450000, 'approved': 420000, 'roi': 18.5, 'status': 'Approved', 'stage': 'In Execution'},
    {'code': 'INV1007', 'title': 'Electric Forklift Fleet Replacement', 'category': 'Forklifts', 'budget': 750000, 'approved': 0, 'roi': 15.2, 'status': 'Pending Approval', 'stage': 'Pending Approval'},
    {'code': 'INV1008', 'title': 'Training Platform - LMS Implementation', 'category': 'Training Platform', 'budget': 180000, 'approved': 180000, 'roi': 85.0, 'status': 'Approved', 'stage': 'Implemented'},
    {'code': 'INV1009', 'title': 'Quality Laboratory Equipment', 'category': 'Quality Lab Equipment', 'budget': 520000, 'approved': 480000, 'roi': 45.0, 'status': 'Approved', 'stage': 'In Execution'},
    {'code': 'INV1010', 'title': 'Office Fit-out - Abu Dhabi HQ', 'category': 'Office Fit-out', 'budget': 680000, 'approved': 620000, 'roi': 12.5, 'status': 'Approved', 'stage': 'Implemented'},
    {'code': 'INV1011', 'title': 'IT Infrastructure - Network Upgrade', 'category': 'IT Infrastructure', 'budget': 380000, 'approved': 350000, 'roi': 55.0, 'status': 'Approved', 'stage': 'Closed'},
    {'code': 'INV1012', 'title': 'Cold Storage Expansion', 'category': 'Warehouse Expansion', 'budget': 4200000, 'approved': 0, 'roi': 25.0, 'status': 'Draft', 'stage': 'Draft'},
    {'code': 'INV1013', 'title': 'Robotic Process Automation', 'category': 'Automation Equipment', 'budget': 280000, 'approved': 250000, 'roi': 120.0, 'status': 'Approved', 'stage': 'In Execution'},
    {'code': 'INV1014', 'title': 'Delivery Fleet Telematics', 'category': 'Delivery Fleet', 'budget': 150000, 'approved': 150000, 'roi': 68.0, 'status': 'Approved', 'stage': 'Closed'},
    {'code': 'INV1015', 'title': 'Solar Panel Installation - Dubai Warehouse', 'category': 'Energy Efficiency', 'budget': 650000, 'approved': 650000, 'roi': 32.0, 'status': 'Approved', 'stage': 'In Execution'},
    {'code': 'INV1016', 'title': 'Warehouse Management System', 'category': 'ERP Upgrade', 'budget': 720000, 'approved': 680000, 'roi': 48.0, 'status': 'Approved', 'stage': 'In Execution'},
    {'code': 'INV1017', 'title': 'Safety Equipment Upgrade', 'category': 'Safety Equipment', 'budget': 220000, 'approved': 220000, 'roi': 25.0, 'status': 'Approved', 'stage': 'Closed'},
    {'code': 'INV1018', 'title': 'ERP Integration - E-commerce Platform', 'category': 'ERP Upgrade', 'budget': 420000, 'approved': 420000, 'roi': 95.0, 'status': 'Approved', 'stage': 'Implemented'},
    {'code': 'INV1019', 'title': 'Consulting - Supply Chain Optimization', 'category': 'Consulting', 'budget': 380000, 'approved': 350000, 'roi': 180.0, 'status': 'Approved', 'stage': 'Closed'},
    {'code': 'INV1020', 'title': 'Data Analytics Platform', 'category': 'IT Infrastructure', 'budget': 350000, 'approved': 320000, 'roi': 75.0, 'status': 'Approved', 'stage': 'In Execution'},
    {'code': 'INV1021', 'title': 'Forklift Fleet Maintenance System', 'category': 'Forklifts', 'budget': 95000, 'approved': 90000, 'roi': 38.0, 'status': 'Approved', 'stage': 'Closed'},
    {'code': 'INV1022', 'title': 'Mobile Application - Field Service', 'category': 'Software License', 'budget': 280000, 'approved': 260000, 'roi': 125.0, 'status': 'Approved', 'stage': 'Implemented'},
    {'code': 'INV1023', 'title': 'Cross-Dock Facility Setup', 'category': 'Warehouse Expansion', 'budget': 1850000, 'approved': 0, 'roi': 28.0, 'status': 'Draft', 'stage': 'Draft'},
    {'code': 'INV1024', 'title': 'Employee Wellness Program', 'category': 'Training Platform', 'budget': 125000, 'approved': 125000, 'roi': 65.0, 'status': 'Approved', 'stage': 'Closed'},
    {'code': 'INV1025', 'title': 'Backup Power System', 'category': 'IT Infrastructure', 'budget': 580000, 'approved': 550000, 'roi': 35.0, 'status': 'Approved', 'stage': 'Implemented'},
]

CATEGORIES = [
    ('Warehouse Expansion', 'EXP'),
    ('Racking System', 'RACK'),
    ('Forklifts', 'FORK'),
    ('ERP Upgrade', 'ERP'),
    ('CCTV', 'CCTV'),
    ('Delivery Fleet', 'FLEET'),
    ('Automation Equipment', 'AUTO'),
    ('Office Fit-out', 'OFFICE'),
    ('IT Infrastructure', 'IT'),
    ('Training Platform', 'TRAIN'),
    ('Quality Lab Equipment', 'LAB'),
    ('Energy Efficiency', 'ENERGY'),
    ('Safety Equipment', 'SAFETY'),
    ('Software License', 'SOFT'),
    ('Consulting', 'CONSULT'),
]

def seed():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    
    # Drop existing investment tables to recreate without FK constraints
    tables_to_drop = [
        'investment_audit_log', 'investment_settings', 'investment_reminders',
        'investment_comments', 'investment_documents', 'investment_cash_flows',
        'investment_scenarios', 'investment_compliance', 'investment_risks',
        'investment_kpi_actuals', 'investment_kpi_targets', 'investment_benefits',
        'investment_milestones', 'investment_cost_centers', 'investment_budget_allocations',
        'investment_funding_schedules', 'investment_approval_history', 'investment_approval_steps',
        'investment_evaluations', 'investment_versions', 'investment_requests',
        'investment_portfolios', 'investment_categories'
    ]
    
    for table in tables_to_drop:
        try:
            conn.execute(f"DROP TABLE IF EXISTS {table}")
        except:
            pass
    
    conn.commit()
    
    # Create tables without FK constraints
    conn.execute("""
        CREATE TABLE IF NOT EXISTS investment_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT UNIQUE,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS investment_requests (
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
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS investment_milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            investment_id INTEGER NOT NULL,
            milestone_name TEXT NOT NULL,
            description TEXT,
            owner_user_id INTEGER,
            due_date DATE,
            completed_date DATE,
            percent_complete REAL DEFAULT 0,
            status TEXT DEFAULT 'Pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS investment_benefits (
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS investment_risks (
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS investment_funding_schedules (
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
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS investment_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            setting_key TEXT UNIQUE NOT NULL,
            setting_value TEXT,
            setting_type TEXT,
            description TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE TABLE IF NOT EXISTS investment_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            investment_id INTEGER,
            action TEXT NOT NULL,
            user_id INTEGER,
            changes TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    
    # Seed categories
    for name, code in CATEGORIES:
        conn.execute("INSERT OR IGNORE INTO investment_categories (name, code) VALUES (?, ?)", (name, code))
    
    # Seed settings
    settings = [
        ('investment_number_prefix', 'INV'),
        ('investment_number_sequence', '2000'),
    ]
    for key, val in settings:
        conn.execute("INSERT OR IGNORE INTO investment_settings (setting_key, setting_value) VALUES (?, ?)", (key, val))
    
    conn.commit()
    
    # Get category IDs
    category_map = {}
    for row in conn.execute("SELECT id, name FROM investment_categories").fetchall():
        category_map[row['name']] = row['id']
    
    # Get user IDs
    user_ids = [r[0] for r in conn.execute("SELECT id FROM users LIMIT 5").fetchall()]
    if not user_ids:
        user_ids = [1, 2, 3, 4, 5]
    
    for inv in INVESTMENTS:
        category_id = category_map.get(inv['category'], 1)
        owner_id = user_ids[0]
        sponsor_id = user_ids[1]
        requester_id = user_ids[0]
        
        committed = inv['approved'] * uniform(0.6, 0.9) if inv['approved'] > 0 else 0
        spent = committed * uniform(0.3, 0.8)
        
        conn.execute("""
            INSERT INTO investment_requests (
                investment_code, title, category_id, owner_user_id, sponsor_user_id, requesting_user_id,
                currency, requested_budget, approved_budget, committed_amount, actual_spent_amount,
                forecast_remaining_amount, roi_percent, priority, status, lifecycle_stage,
                funding_status, approval_status, start_date, target_end_date, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            inv['code'], inv['title'], category_id, owner_id, sponsor_id, requester_id,
            'USD', inv['budget'], inv['approved'], committed, spent,
            inv['approved'] - spent if inv['approved'] > spent else 0,
            inv['roi'], 'High', inv['status'], inv['stage'], 'Planned', inv['status'],
            '2026-01-01', '2026-12-31'
        ))
        
        investment_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # Add milestones
        if inv['stage'] != 'Draft':
            milestones = [
                ('Initiation', 'Completed'),
                ('Planning', 'Completed' if inv['stage'] in ['Implemented', 'Closed', 'In Execution'] else 'In Progress'),
                ('Execution', 'Completed' if inv['stage'] in ['Implemented', 'Closed'] else 'In Progress'),
                ('Go-Live', 'Completed' if inv['stage'] in ['Implemented', 'Closed'] else 'Pending'),
            ]
            for i, (name, status) in enumerate(milestones):
                pct = 100 if status == 'Completed' else 50
                conn.execute("""
                    INSERT INTO investment_milestones (investment_id, milestone_name, due_date, percent_complete, status)
                    VALUES (?, ?, ?, ?, ?)
                """, (investment_id, name, f'2026-{i+1:02d}-15', pct, status))
        
        # Add benefit
        conn.execute("""
            INSERT INTO investment_benefits (investment_id, benefit_name, benefit_type, target_value, actual_value, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (investment_id, 'Cost Reduction', 'Financial', inv['budget'] * 0.15, 
              inv['budget'] * 0.12 if inv['stage'] in ['Implemented', 'Closed'] else 0,
              'On Track' if inv['stage'] in ['Implemented', 'Closed'] else 'Tracking'))
        
        # Add risk
        if inv['roi'] > 30:
            conn.execute("""
                INSERT INTO investment_risks (investment_id, risk_name, risk_category, probability, impact, risk_score, mitigation_plan, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (investment_id, 'Supply Chain Delay', 'Operational', 'High', 'High', 4, 'Early ordering', 'Active'))
        
        # Add funding schedule
        if inv['approved'] > 0:
            quarterly = inv['approved'] / 4
            for i in range(4):
                conn.execute("""
                    INSERT INTO investment_funding_schedules (investment_id, schedule_date, scheduled_amount, released_amount, withdrawn_amount, funding_source, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (investment_id, f'2026-0{i+1}-01', quarterly, quarterly if i < 2 else 0, quarterly * 0.7 if i < 2 else 0, 'Internal Budget', 'Released' if i < 2 else 'Planned'))
    
    conn.commit()
    
    count = conn.execute("SELECT COUNT(*) FROM investment_requests").fetchone()[0]
    print(f"Successfully seeded {count} investment records!")
    conn.close()

if __name__ == '__main__':
    seed()
