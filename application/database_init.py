"""
Database Initialization Module
==============================

Contains the init_db() function that sets up the core database tables.
This was extracted from the monolithic app.py to improve maintainability.

Usage:
    from application.database_init import init_db
    init_db()
"""

import os
import sqlite3
import random
from datetime import datetime


# ============================================================================
# Main Init DB Function
# ============================================================================

def init_db():
    """
    Initialize core database tables.

    This function was previously inline in app.py. It creates tables for:
    - customers
    - delivery_trips, delivery_stops, delivery_activity_logs, delivery_activities
    - warehouses
    - suppliers
    - customer_transactions
    - vehicles
    - task_departments, task_items, task_history, task_subtasks
    - task_transaction_categories, task_transactions, task_report_snapshots
    - task_user_permissions
    - issue_items, issue_history, issue_comments, issue_attachments
    - issue_watchers, issue_escalations, issue_categories
    - issue_sla_rules, issue_workflow_rules
    - user_task_preferences, user_preferences
    - google_workspace_tokens, google_workspace_settings
    - user_issue_preferences

    Note: Many tables use 'CREATE TABLE IF NOT EXISTS' so this is safe to run
    on existing databases.
    """
    from database import get_db

    db = get_db()

    # Create customers table
    db.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            location TEXT,
            type TEXT,
            salesperson_id INTEGER,
            working_hours TEXT,
            working_days TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (salesperson_id) REFERENCES users(id)
        )
    ''')

    # Create delivery tables
    db.execute('''
        CREATE TABLE IF NOT EXISTS delivery_trips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            driver_id INTEGER NOT NULL,
            date DATE DEFAULT CURRENT_DATE,
            warehouse_departure TIMESTAMP,
            warehouse_arrival TIMESTAMP,
            status TEXT DEFAULT 'At Warehouse',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            warehouse_checkin DATETIME,
            vehicle_id INTEGER,
            FOREIGN KEY (driver_id) REFERENCES users(id)
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS delivery_stops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            arrival_time TIMESTAMP,
            departure_time TIMESTAMP,
            arrival_gps TEXT,
            departure_gps TEXT,
            status TEXT DEFAULT 'Pending',
            sequence_order INTEGER,
            FOREIGN KEY (trip_id) REFERENCES delivery_trips(id) ON DELETE CASCADE,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS delivery_activity_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trip_id INTEGER,
            activity_type TEXT,
            customer_id INTEGER,
            timestamp TEXT,
            notes TEXT,
            FOREIGN KEY (trip_id) REFERENCES delivery_trips(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS delivery_activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seed default activities
    defaults = ['Arrival to warehouse', 'Departure from Warehouse', 'Arrival at Customer', 'Departure from Customer', 'Documents Delivery']
    for d in defaults:
        db.execute('INSERT OR IGNORE INTO delivery_activities (name) VALUES (?)', (d,))

    # Warehouse Hierarchy Schema
    db.execute('''
        CREATE TABLE IF NOT EXISTS warehouses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company_id INTEGER NOT NULL,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        )
    ''')

    # Add warehouse columns if not exist
    try:
        db.execute("ALTER TABLE inventory ADD COLUMN warehouse_id INTEGER")
    except:
        pass

    try:
        db.execute("ALTER TABLE movements ADD COLUMN warehouse_id INTEGER")
    except:
        pass

    # Migrate legacy data: create a default warehouse for each company
    companies = db.execute("SELECT id, name FROM companies").fetchall()
    for comp in companies:
        wh = db.execute("SELECT id FROM warehouses WHERE company_id = ? AND name = ?", (comp['id'], 'Main Warehouse')).fetchone()
        if not wh:
            db.execute("INSERT INTO warehouses (name, company_id) VALUES (?, ?)", ('Main Warehouse', comp['id']))
            wh_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        else:
            wh_id = wh['id']

        db.execute("UPDATE inventory SET warehouse_id = ? WHERE company_id = ? AND warehouse_id IS NULL", (wh_id, comp['id']))
        db.execute("UPDATE movements SET warehouse_id = ? WHERE company_id = ? AND warehouse_id IS NULL", (wh_id, comp['id']))

    # Suppliers Table
    db.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            code TEXT NOT NULL UNIQUE,
            contact_person TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            city TEXT,
            country TEXT,
            region TEXT,
            payment_terms TEXT DEFAULT 'Net 30',
            lead_time TEXT,
            currency TEXT DEFAULT 'USD',
            margin TEXT,
            rating INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Active',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seed default suppliers if empty
    if db.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0] == 0:
        seed_suppliers = [
            ('Global Tech Parts', 'SUP-1001', 'Ahmed Al-Rashid', 'ahmed@globaltechparts.com', '+971-4-555-0101', 'Sheik Zayed Road, Building 5', 'Dubai', 'UAE', 'HQ-Dubai', 'Net 30', '2 Days', 'AED', '18%', 4, 'Active', 'Primary parts distributor'),
            ('EuroAuto Systems', 'SUP-1002', 'Hans Mueller', 'hans@euroauto.de', '+49-69-555-0202', 'Autobahn 42', 'Frankfurt', 'Germany', 'EU-Frankfurt', 'Net 45', '5 Days', 'EUR', '22%', 5, 'Active', 'European OEM channel'),
            ('Nippon Dynamics', 'SUP-1003', 'Yuki Tanaka', 'yuki@nippondyn.jp', '+81-3-555-0303', 'Minato-ku, Roppongi', 'Tokyo', 'Japan', 'APAC-Tokyo', 'Net 60', '7 Days', 'JPY', '15%', 4, 'Active', 'Precision electronics supplier'),
            ('American Steelworks', 'SUP-1004', 'John Carter', 'john@amsteelworks.com', '+1-313-555-0404', 'Motor City Avenue', 'Detroit', 'USA', 'NA-Detroit', 'Net 30', '10 Days', 'USD', '12%', 3, 'Active', 'Heavy-duty steel components'),
            ('Desert Sands Logistics', 'SUP-1005', 'Fahad bin Salman', 'fahad@desertsands.sa', '+966-11-555-0505', 'King Fahd Road', 'Riyadh', 'Saudi Arabia', 'MENA-Riyadh', 'Net 30', '3 Days', 'SAR', '19%', 4, 'Active', 'Regional logistics partner')
        ]
        for s in seed_suppliers:
            db.execute('''INSERT INTO suppliers (name,code,contact_person,email,phone,address,city,country,region,payment_terms,lead_time,currency,margin,rating,status,notes)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', s)

    # Accounting Module Extensions
    try:
        db.execute("ALTER TABLE customers ADD COLUMN balance DECIMAL(12,2) DEFAULT 0.00")
    except:
        pass

    try:
        db.execute("ALTER TABLE customers ADD COLUMN credit_limit DECIMAL(12,2) DEFAULT 5000.00")
    except:
        pass

    db.execute('''
        CREATE TABLE IF NOT EXISTS customer_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            type TEXT NOT NULL,
            amount DECIMAL(12,2) NOT NULL,
            reference TEXT,
            notes TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE
        )
    ''')

    # Seed sample accounting data
    has_transactions = db.execute("SELECT COUNT(*) FROM customer_transactions").fetchone()[0] > 0
    if not has_transactions:
        customers_to_seed = db.execute("SELECT id FROM customers LIMIT 5").fetchall()
        for c in customers_to_seed:
            bal = round(random.uniform(500, 4500), 2)
            limit = 5000.00
            db.execute("UPDATE customers SET balance = ?, credit_limit = ? WHERE id = ?", (bal, limit, c['id']))
            db.execute('''INSERT INTO customer_transactions (customer_id, type, amount, reference, notes)
                VALUES (?, 'Invoice', ?, 'INV-SAMPLE-001', 'Initial balance migration')''', (c['id'], bal))

    # Vehicle Fleet Schema
    db.execute('''
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            plate_number TEXT,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    try:
        db.execute("ALTER TABLE delivery_trips ADD COLUMN vehicle_id INTEGER")
    except:
        pass

    # Seed default vehicles if empty
    if db.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0] == 0:
        seed_vehicles = [
            ('Toyota Hiace', 'DXB-V-1020'),
            ('Nissan Urvan', 'SHJ-G-5040'),
            ('Mercedes Sprinter', 'AUH-X-7080')
        ]
        for v_name, v_plate in seed_vehicles:
            db.execute('INSERT INTO vehicles (name, plate_number) VALUES (?, ?)', (v_name, v_plate))

    # Task Management Tables
    db.execute('''
        CREATE TABLE IF NOT EXISTS task_departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS task_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER,
            department_id INTEGER,
            task_name TEXT NOT NULL,
            priority TEXT DEFAULT 'Medium',
            report_to_user_id INTEGER,
            assigned_to_user_id INTEGER,
            progress INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Open',
            description TEXT,
            latest_note TEXT,
            due_at TEXT,
            is_archived INTEGER DEFAULT 0,
            archived_at TEXT,
            created_by_user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES companies(id),
            FOREIGN KEY (department_id) REFERENCES task_departments(id),
            FOREIGN KEY (report_to_user_id) REFERENCES users(id),
            FOREIGN KEY (assigned_to_user_id) REFERENCES users(id),
            FOREIGN KEY (created_by_user_id) REFERENCES users(id)
        )
    ''')

    # Task Items extended columns
    _add_column_if_safe(db, 'task_items', 'reminder_days', 'INTEGER DEFAULT 0')
    _add_column_if_safe(db, 'task_items', 'reminder_hours', 'INTEGER DEFAULT 0')
    _add_column_if_safe(db, 'task_items', 'progress_auto', 'INTEGER DEFAULT 0')
    _add_column_if_safe(db, 'task_items', 'last_reminder_sent', 'TEXT')

    # Task subtasks table
    db.execute('''
        CREATE TABLE IF NOT EXISTS task_subtasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_task_id INTEGER NOT NULL,
            subtask_title TEXT NOT NULL,
            description TEXT,
            assigned_to_user_id INTEGER,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Pending',
            progress INTEGER DEFAULT 0,
            due_at TEXT,
            created_by_user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_task_id) REFERENCES task_items(id) ON DELETE CASCADE,
            FOREIGN KEY (assigned_to_user_id) REFERENCES users(id),
            FOREIGN KEY (created_by_user_id) REFERENCES users(id)
        )
    ''')

    # Subtask columns
    _add_column_if_safe(db, 'task_subtasks', 'is_completed', 'INTEGER DEFAULT 0')
    _add_column_if_safe(db, 'task_subtasks', 'reminder_days', 'INTEGER DEFAULT 0')
    _add_column_if_safe(db, 'task_subtasks', 'reminder_hours', 'INTEGER DEFAULT 0')
    _add_column_if_safe(db, 'task_subtasks', 'last_reminder_sent', 'TEXT')

    db.execute('''
        CREATE TABLE IF NOT EXISTS task_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            task_name TEXT,
            action_type TEXT NOT NULL,
            field_name TEXT,
            old_value TEXT,
            new_value TEXT,
            note TEXT,
            actor_user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (actor_user_id) REFERENCES users(id)
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS task_transaction_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            color TEXT DEFAULT '#6366f1',
            icon TEXT DEFAULT 'fa-money-bill',
            is_system INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS task_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            category_id INTEGER,
            transaction_type TEXT NOT NULL,
            amount DECIMAL(12,2) DEFAULT 0,
            quantity INTEGER DEFAULT 1,
            unit TEXT DEFAULT 'unit',
            description TEXT,
            reference TEXT,
            transaction_date TEXT,
            created_by_user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES task_items(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES task_transaction_categories(id),
            FOREIGN KEY (created_by_user_id) REFERENCES users(id)
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS task_report_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_name TEXT NOT NULL,
            report_type TEXT NOT NULL,
            filters_applied TEXT,
            snapshot_data TEXT,
            created_by_user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by_user_id) REFERENCES users(id)
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS task_user_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            permission_key TEXT NOT NULL UNIQUE,
            permission_value INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Seed default departments
    default_departments = [
        ('Administration', 'Cross-functional leadership, governance, and approvals'),
        ('Sales', 'Customer acquisition, key accounts, and commercial follow-up'),
        ('Warehouse', 'Stock handling, shelving, and internal controls'),
        ('Logistics', 'Fleet, dispatch, and route execution'),
        ('Procurement', 'Supplier management and purchasing coordination'),
        ('Accounting', 'Collections, payables, and financial close'),
        ('Operations', 'Execution monitoring and service coordination'),
        ('Human Resources', 'Staffing, onboarding, and compliance')
    ]
    for dept_name, dept_desc in default_departments:
        db.execute(
            'INSERT OR IGNORE INTO task_departments (name, description) VALUES (?, ?)',
            (dept_name, dept_desc)
        )

    # Seed default transaction categories
    default_categories = [
        ('Labor', 'Employee working hours and wages', '#10b981', 'fa-clock', 1),
        ('Materials', 'Raw materials and supplies consumed', '#f59e0b', 'fa-box', 1),
        ('Equipment', 'Equipment usage and rental costs', '#6366f1', 'fa-truck', 1),
        ('Transportation', 'Travel and transport expenses', '#8b5cf6', 'fa-car', 1),
        ('Outsourcing', 'Third-party services and contractors', '#ec4899', 'fa-users', 1),
        ('Overhead', 'Indirect costs and utilities', '#64748b', 'fa-building', 1),
        ('Revenue', 'Income generated from task completion', '#22c55e', 'fa-dollar-sign', 1),
        ('Miscellaneous', 'Other task-related expenses', '#78716c', 'fa-ellipsis-h', 1),
    ]
    for cat_name, cat_desc, cat_color, cat_icon, cat_system in default_categories:
        db.execute(
            'INSERT OR IGNORE INTO task_transaction_categories (name, description, color, icon, is_system) VALUES (?, ?, ?, ?, ?)',
            (cat_name, cat_desc, cat_color, cat_icon, cat_system)
        )

    # Issue Tracker Tables
    db.execute('''
        CREATE TABLE IF NOT EXISTS issue_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            row_id INTEGER NOT NULL UNIQUE,
            issue_date TEXT NOT NULL,
            issue_date_sort TEXT,
            issue TEXT NOT NULL,
            pareto_law INTEGER DEFAULT 0,
            involved_departments TEXT,
            section_team TEXT,
            issue_type TEXT,
            writer TEXT,
            reported_by TEXT,
            priority TEXT DEFAULT 'Medium',
            status TEXT DEFAULT 'Open',
            responsible_section TEXT,
            responsible_person TEXT,
            root_cause TEXT,
            impact TEXT,
            action_plan TEXT,
            resources_needed TEXT,
            target_resolution_date TEXT,
            first_follow_up_date TEXT,
            first_follow_up_notes TEXT,
            second_follow_up_date TEXT,
            second_follow_up_notes TEXT,
            follow_up_by TEXT,
            progress_note TEXT,
            linked_issues TEXT,
            final_status TEXT,
            created_by_user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by_user_id) REFERENCES users(id)
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS issue_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            note TEXT,
            actor_user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (issue_id) REFERENCES issue_items(id) ON DELETE CASCADE,
            FOREIGN KEY (actor_user_id) REFERENCES users(id)
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS user_issue_preferences (
            user_id INTEGER PRIMARY KEY,
            visible_columns TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS issue_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_id INTEGER NOT NULL,
            user_id INTEGER,
            comment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (issue_id) REFERENCES issue_items(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS issue_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_id INTEGER NOT NULL,
            user_id INTEGER,
            filename TEXT,
            file_path TEXT,
            file_size INTEGER,
            mime_type TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (issue_id) REFERENCES issue_items(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS issue_watchers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(issue_id, user_id),
            FOREIGN KEY (issue_id) REFERENCES issue_items(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS issue_escalations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            issue_id INTEGER NOT NULL,
            escalated_by INTEGER,
            escalated_to INTEGER,
            escalation_level INTEGER DEFAULT 1,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (issue_id) REFERENCES issue_items(id) ON DELETE CASCADE,
            FOREIGN KEY (escalated_by) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (escalated_to) REFERENCES users(id) ON DELETE SET NULL
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS issue_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            parent_id INTEGER,
            default_assignee TEXT,
            default_priority TEXT DEFAULT 'Medium',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS issue_sla_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            priority TEXT NOT NULL,
            response_hours INTEGER DEFAULT 24,
            resolution_hours INTEGER DEFAULT 72,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS issue_workflow_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_status TEXT NOT NULL,
            to_status TEXT NOT NULL,
            description TEXT,
            requires_comment INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # User Preferences Table
    db.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id INTEGER PRIMARY KEY,
            theme TEXT DEFAULT 'dark',
            font_family TEXT DEFAULT 'outfit',
            font_size TEXT DEFAULT 'medium',
            font_weight TEXT DEFAULT 'regular',
            timezone TEXT DEFAULT 'Asia/Dubai',
            date_format TEXT DEFAULT 'DD/MM/YYYY',
            interface_direction TEXT DEFAULT 'auto',
            currency TEXT DEFAULT 'AED',
            density TEXT DEFAULT 'comfortable',
            reduced_motion INTEGER DEFAULT 0,
            show_seconds INTEGER DEFAULT 1,
            sidebar_compact INTEGER DEFAULT 0,
            language TEXT DEFAULT 'en',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    _add_column_if_safe(db, 'user_preferences', 'interface_direction', "TEXT DEFAULT 'auto'")
    _add_column_if_safe(db, 'user_preferences', 'font_weight', "TEXT DEFAULT 'regular'")
    _add_column_if_safe(db, 'user_preferences', 'language', "TEXT DEFAULT 'en'")
    _add_column_if_safe(db, 'user_preferences', 'nav_preferences', "TEXT DEFAULT '{}'")

    # User Task Preferences
    db.execute('''
        CREATE TABLE IF NOT EXISTS user_task_preferences (
            user_id INTEGER PRIMARY KEY,
            visible_columns TEXT,
            task_list_columns TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    _add_column_if_safe(db, 'user_task_preferences', 'task_list_columns', "TEXT DEFAULT 'type,title,parent,assigned,priority,status,progress,due'")

    # Google Workspace Tables
    db.execute('''
        CREATE TABLE IF NOT EXISTS google_workspace_tokens (
            user_id INTEGER PRIMARY KEY,
            access_token TEXT,
            refresh_token TEXT,
            token_type TEXT DEFAULT 'Bearer',
            scope TEXT,
            expires_at TEXT,
            email_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS google_workspace_settings (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            client_id TEXT,
            client_secret TEXT,
            redirect_uri TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Commit all changes
    db.commit()
    db.close()


def _add_column_if_safe(db, table, column, definition):
    """Add a column to a table if it doesn't exist (safe wrapper)."""
    try:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    except Exception:
        pass