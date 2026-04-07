from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify, Response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
import sqlite3
import os
import re
import json
import csv
import io
from collections import Counter
from openpyxl import Workbook, load_workbook
import pandas as pd
import time
import tempfile
import openpyxl
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from datetime import datetime, timedelta
from issue_seed_data import ISSUE_SEED_DATA
from google_workspace_integration import register_google_workspace, google_workspace_report_snapshot
from email_manager import register_email_manager
from peyvast_sync import PeyvastSyncManager, get_sync_manager, run_sync as run_peyvast_sync
from translations import TRANSLATIONS, LANGUAGES, RTL_LANGUAGES, get_translation, get_translations, is_rtl, get_language_direction
from hr_routes import register_hr_routes
from wms_routes import register_wms_routes
from logistics_routes import register_logistics_routes
from company_routes import register_company_routes
from planning_routes import register_planning_routes
from marketing_routes import register_marketing_routes
from customer_intelligence_routes import register_ci_routes
from social_media_routes import register_social_media_routes
from customer_intelligence_models import init_ci_tables
from planning_models import init_planning_tables
from sales_routes import register_sales_routes
from sales_suite_routes import register_sales_suite_routes
from admin_routes import register_admin_routes
from procurement_routes import register_procurement_routes
from profile_routes import register_profile_routes

# =============================================================================
# UNIFIED PLATFORM MODULES (Enterprise Integration)
# =============================================================================
# These modules provide unified infrastructure across all modules:
# - database.py: Single source of truth for database connections
# - permissions.py: Unified RBAC system
# - settings.py: Unified settings management
# - navigation.py: Unified menu/navigation structure
# - master_data.py: Unified master data management
# - reporting.py: Unified reporting framework
# - theme_system.py: Theme tokens, palettes, and helpers

from database import (
    get_db, get_db_context, get_one, get_all,
    initialize_platform_schema, create_notification,
    log_audit, get_user_notifications,
    get_platform_setting, set_platform_setting,
    STANDARD_STATUSES, STATUS_COLORS
)
from permissions import (
    get_user_permissions, get_role_permissions,
    user_has_permission, require_permission,
    require_module_access, get_module_resources,
    initialize_permissions, invalidate_user_permission_cache
)
from settings import (
    get_setting, set_setting,
    get_settings_by_category, DEFAULT_SETTINGS,
    initialize_settings
)
from navigation import (
    MENU_STRUCTURE, get_main_menu, get_breadcrumbs,
    get_page_title, get_active_module,
    prepare_menu_for_template, get_notification_badge,
    get_menu_label
)
from master_data import (
    get_canonical_customer, get_all_canonical_customers,
    get_canonical_item, get_all_canonical_items,
    get_canonical_employee, get_all_canonical_employees,
    resolve_customer, resolve_item,
    run_master_data_health_check,
    initialize_master_data
)
from reporting import (
    get_dashboard_stats, build_inventory_report,
    build_sales_report, build_delivery_report,
    build_hr_attendance_report, build_planning_alerts_report,
    export_to_excel, export_to_csv,
    initialize_reporting
)
from theme_system import (
    get_available_themes, get_theme_config,
    get_theme_tokens, get_chart_palette,
    is_dark_theme, validate_theme,
    get_default_theme, get_all_theme_ids,
    CHART_PALETTES, AVAILABLE_THEMES
)
from theme_engine import (
    theme_css_variables, theme_inline_style,
    theme_data_attrs, chartjs_config,
    theme_preview_data, get_status_color_classes,
    get_priority_classes
)

app = Flask(__name__)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DEFAULT_SECRET_KEY = 'change-me-in-production'
app.secret_key = os.environ.get('SECRET_KEY', DEFAULT_SECRET_KEY)
app.config['TEMPLATES_AUTO_RELOAD'] = False
app.jinja_env.auto_reload = False

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(BASE_DIR, 'warehouse.db'))
UPLOAD_FOLDER = os.environ.get(
    'UPLOAD_FOLDER',
    os.path.join(BASE_DIR, 'static', 'uploads', 'avatars')
)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def ensure_database_directory():
    db_dir = os.path.dirname(os.path.abspath(DATABASE))
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)


def ensure_base_schema():
    ensure_database_directory()
    schema_path = os.path.join(BASE_DIR, 'sqlite_schema.sql')
    if not os.path.exists(schema_path):
        return

    needs_schema = not os.path.exists(DATABASE) or os.path.getsize(DATABASE) == 0
    conn = sqlite3.connect(DATABASE)
    try:
        if not needs_schema:
            table_exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'companies'"
            ).fetchone()
            needs_schema = table_exists is None

        if needs_schema:
            with open(schema_path, 'r', encoding='utf-8') as schema_file:
                conn.executescript(schema_file.read())
            conn.commit()
    finally:
        conn.close()


def ensure_admin_user():
    admin_password = os.environ.get('ADMIN_PASSWORD', '').strip()
    if not admin_password:
        return

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        role = conn.execute(
            "SELECT id FROM roles WHERE role_name = ? LIMIT 1",
            ('Global Admin',)
        ).fetchone()
        if role:
            role_id = role['id']
        else:
            conn.execute(
                "INSERT INTO roles (role_name, company_id, can_edit_stock, can_manage_users) VALUES (?, ?, ?, ?)",
                ('Global Admin', None, 1, 1)
            )
            role_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        admin_user = conn.execute(
            "SELECT id FROM users WHERE username = ? LIMIT 1",
            ('admin',)
        ).fetchone()
        hashed_password = generate_password_hash(admin_password)

        if admin_user:
            conn.execute(
                "UPDATE users SET password = ?, role_id = ? WHERE id = ?",
                (hashed_password, role_id, admin_user['id'])
            )
        else:
            conn.execute(
                "INSERT INTO users (username, email, password, role_id) VALUES (?, ?, ?, ?)",
                ('admin', 'admin@warehouse.local', hashed_password, role_id)
            )
        conn.commit()
    finally:
        conn.close()

# ─── Customer Helper Functions ──────────────────────────────────────────────────
# Note: get_db() is imported from database.py to ensure consistent settings

def get_customers_from_db(filters=None):
    """Get customers from local sdad_customers table with optional filters."""
    db = get_db()
    try:
        query = "SELECT * FROM sdad_customers WHERE 1=1"
        params = []
        
        if filters:
            if filters.get('country'):
                query += " AND country = ?"
                params.append(filters['country'])
            if filters.get('city'):
                query += " AND city = ?"
                params.append(filters['city'])
            if filters.get('customer_type'):
                query += " AND location = ?"
                params.append(filters['customer_type'])
            if filters.get('is_export') is not None:
                query += " AND location = 'export'" if filters['is_export'] else " AND location = 'local'"
            if filters.get('salesperson_id'):
                query += " AND salesperson_id = ?"
                params.append(filters['salesperson_id'])
            if filters.get('search'):
                search = f"%{filters['search']}%"
                query += " AND (name LIKE ? OR email LIKE ? OR phone LIKE ? OR customer_code LIKE ?)"
                params.extend([search, search, search, search])
        
        query += " ORDER BY total_orders DESC"
        return [dict(r) for r in db.execute(query, params).fetchall()]
    finally:
        db.close()


def get_customers_summary_from_db():
    """Get customers summary statistics from local database."""
    db = get_db()
    try:
        total = db.execute("SELECT COUNT(*) as cnt FROM sdad_customers").fetchone()['cnt']
        total_orders = db.execute("SELECT COALESCE(SUM(total_orders), 0) as t FROM sdad_customers").fetchone()['t']
        total_debt = db.execute("SELECT COALESCE(SUM(total_debt), 0) as t FROM sdad_customers").fetchone()['t']
        export_count = db.execute("SELECT COUNT(*) as cnt FROM sdad_customers WHERE location = 'export'").fetchone()['cnt']
        active_count = db.execute("SELECT COUNT(*) as cnt FROM sdad_customers WHERE active = 1").fetchone()['cnt']
        
        countries = db.execute("""
            SELECT country, COUNT(*) as cnt, SUM(total_orders) as total_sales, SUM(total_debt) as outstanding
            FROM sdad_customers WHERE country != '' GROUP BY country ORDER BY cnt DESC
        """).fetchall()
        
        locations = db.execute("""
            SELECT location, COUNT(*) as cnt, SUM(total_orders) as total_sales, SUM(total_debt) as outstanding
            FROM sdad_customers GROUP BY location ORDER BY cnt DESC
        """).fetchall()
        
        salespersons = db.execute("""
            SELECT salesperson_name, COUNT(*) as customers, SUM(total_orders) as total_sales, SUM(total_debt) as total_debt
            FROM sdad_customers WHERE salesperson_name != '' GROUP BY salesperson_name ORDER BY total_sales DESC
        """).fetchall()
        
        return {
            'total_customers': total,
            'total_orders': total_orders,
            'total_debt': total_debt,
            'total_purchases': total_orders,
            'total_outstanding': total_debt,
            'total_credit_limit': db.execute("SELECT COALESCE(SUM(credit_limit), 0) as total FROM sdad_customers").fetchone()['total'],
            'average_purchase': total_orders / total if total > 0 else 0,
            'export_customers': export_count,
            'domestic_customers': total - export_count,
            'active_customers': active_count,
            'inactive_customers': total - active_count,
            'by_country': [dict(r) for r in countries],
            'by_location': [dict(r) for r in locations],
            'by_salesperson': [dict(r) for r in salespersons],
        }
    finally:
        db.close()


def get_customers_by_country_from_db():
    """Group customers by country."""
    db = get_db()
    try:
        return [dict(r) for r in db.execute('''
            SELECT country, COUNT(*) as customer_count, SUM(total_orders) as total_sales,
                   SUM(total_debt) as total_outstanding, SUM(credit_limit) as credit_limit,
                   AVG(total_orders) as avg_sales,
                   SUM(CASE WHEN location = 'export' THEN 1 ELSE 0 END) as export_count
            FROM sdad_customers WHERE country != '' GROUP BY country ORDER BY customer_count DESC
        ''').fetchall()]
    finally:
        db.close()


def get_salesperson_performance_from_db():
    """Salesperson performance metrics."""
    db = get_db()
    try:
        return [dict(r) for r in db.execute('''
            SELECT salesperson_name, COUNT(*) as customer_count, SUM(total_orders) as total_sales,
                   SUM(total_payments) as total_payments, SUM(total_debt) as total_debt,
                   AVG(total_orders) as avg_sale, MAX(last_purchase_date) as last_sale_date
            FROM sdad_customers WHERE salesperson_name != '' GROUP BY salesperson_name ORDER BY total_sales DESC
        ''').fetchall()]
    finally:
        db.close()


def require_login(f):
    """Decorator factory that redirects unauthenticated users to login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        allowed_routes = ['login', 'static', 'set_language']
        if request.endpoint not in allowed_routes and 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


register_google_workspace(app, get_db)
register_email_manager(app, get_db)
register_hr_routes(app)
register_wms_routes(app, get_db)
register_company_routes(app)
register_logistics_routes(app)
register_planning_routes(app, get_db)
register_marketing_routes(app)
register_ci_routes(app)
register_social_media_routes(app)
register_sales_routes(app, require_login, user_has_permission, get_db)
register_sales_suite_routes(app, require_login, user_has_permission, get_db)
register_admin_routes(app)
register_procurement_routes(app, get_db)
register_profile_routes(app)

# Register Business Intelligence routes
from bi_routes import register_bi_routes
register_bi_routes(app)

# Initialize Customer Intelligence tables
init_ci_tables()

def init_db():
    db = get_db()
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
        
    # Warehouse Hierarchy Schema Migration
    db.execute('''
        CREATE TABLE IF NOT EXISTS warehouses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company_id INTEGER NOT NULL,
            FOREIGN KEY (company_id) REFERENCES companies (id)
        )
    ''')
    
    try:
        db.execute("ALTER TABLE inventory ADD COLUMN warehouse_id INTEGER")
    except:
        pass
        
    try:
        db.execute("ALTER TABLE movements ADD COLUMN warehouse_id INTEGER")
    except:
        pass

    # Migrate legacy data: create a default warehouse for each company and remap constraints
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

    # ── Suppliers Table ──
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
    # Seed default suppliers if table is empty
    if db.execute("SELECT COUNT(*) FROM suppliers").fetchone()[0] == 0:
        seed_suppliers = [
            ('Global Tech Parts','SUP-1001','Ahmed Al-Rashid','ahmed@globaltechparts.com','+971-4-555-0101','Sheik Zayed Road, Building 5','Dubai','UAE','HQ-Dubai','Net 30','2 Days','AED','18%',4,'Active','Primary parts distributor'),
            ('EuroAuto Systems','SUP-1002','Hans Mueller','hans@euroauto.de','+49-69-555-0202','Autobahn 42','Frankfurt','Germany','EU-Frankfurt','Net 45','5 Days','EUR','22%',5,'Active','European OEM channel'),
            ('Nippon Dynamics','SUP-1003','Yuki Tanaka','yuki@nippondyn.jp','+81-3-555-0303','Minato-ku, Roppongi','Tokyo','Japan','APAC-Tokyo','Net 60','7 Days','JPY','15%',4,'Active','Precision electronics supplier'),
            ('American Steelworks','SUP-1004','John Carter','john@amsteelworks.com','+1-313-555-0404','Motor City Avenue','Detroit','USA','NA-Detroit','Net 30','10 Days','USD','12%',3,'Active','Heavy-duty steel components'),
            ('Desert Sands Logistics','SUP-1005','Fahad bin Salman','fahad@desertsands.sa','+966-11-555-0505','King Fahd Road','Riyadh','Saudi Arabia','MENA-Riyadh','Net 30','3 Days','SAR','19%',4,'Active','Regional logistics partner')
        ]
        for s in seed_suppliers:
            db.execute('''INSERT INTO suppliers (name,code,contact_person,email,phone,address,city,country,region,payment_terms,lead_time,currency,margin,rating,status,notes) 
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', s)

    # ── Accounting Module Extensions ──
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
            type TEXT NOT NULL, -- 'Invoice', 'Payment', 'Adjustment'
            amount DECIMAL(12,2) NOT NULL,
            reference TEXT,
            notes TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE
        )
    ''')

    # Seed sample accounting data if empty (simplified check)
    has_transactions = db.execute("SELECT COUNT(*) FROM customer_transactions").fetchone()[0] > 0
    if not has_transactions:
        # Get up to 5 customers to seed
        customers_to_seed = db.execute("SELECT id FROM customers LIMIT 5").fetchall()
        import random
        for c in customers_to_seed:
            bal = round(random.uniform(500, 4500), 2)
            limit = 5000.00
            db.execute("UPDATE customers SET balance = ?, credit_limit = ? WHERE id = ?", (bal, limit, c['id']))
            # Initial Invoice
            db.execute('''INSERT INTO customer_transactions (customer_id, type, amount, reference, notes) 
                VALUES (?, 'Invoice', ?, 'INV-SAMPLE-001', 'Initial balance migration')''', (c['id'], bal))

    # ── Vehicle Fleet Schema ──
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

    # Task Items extended columns (with try/except for existing databases)
    try:
        db.execute("ALTER TABLE task_items ADD COLUMN reminder_days INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        db.execute("ALTER TABLE task_items ADD COLUMN reminder_hours INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        db.execute("ALTER TABLE task_items ADD COLUMN progress_auto INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        db.execute("ALTER TABLE task_items ADD COLUMN last_reminder_sent TEXT")
    except Exception:
        pass

    # Ensure subtasks table has is_completed column
    try:
        db.execute("ALTER TABLE task_subtasks ADD COLUMN is_completed INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        db.execute("ALTER TABLE task_subtasks ADD COLUMN reminder_days INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        db.execute("ALTER TABLE task_subtasks ADD COLUMN reminder_hours INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        db.execute("ALTER TABLE task_subtasks ADD COLUMN last_reminder_sent TEXT")
    except Exception:
        pass

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

    # ── Task Subtasks Table ──
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

    # ── Task Transaction Categories ──
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

    # ── Task Transactions Table ──
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

    # ── Task Reports / Analytics ──
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

    # ── User Task Permissions ──
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
        CREATE TABLE IF NOT EXISTS user_task_preferences (
            user_id INTEGER PRIMARY KEY,
            visible_columns TEXT,
            task_list_columns TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    try:
        db.execute("ALTER TABLE user_task_preferences ADD COLUMN task_list_columns TEXT DEFAULT 'type,title,parent,assigned,priority,status,progress,due'")
    except Exception:
        pass
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
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
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
    try:
        db.execute("ALTER TABLE user_preferences ADD COLUMN interface_direction TEXT DEFAULT 'auto'")
    except Exception:
        pass
    try:
        db.execute("ALTER TABLE user_preferences ADD COLUMN font_weight TEXT DEFAULT 'regular'")
    except Exception:
        pass
    try:
        db.execute("ALTER TABLE user_preferences ADD COLUMN language TEXT DEFAULT 'en'")
    except Exception:
        pass

    def parse_seed_issue_date_sort(issue_date):
        if not issue_date or str(issue_date).strip().lower() == 'past':
            return None
        try:
            return datetime.strptime(str(issue_date).strip(), '%d/%m/%Y').strftime('%Y-%m-%d')
        except ValueError:
            return None

    if db.execute("SELECT COUNT(*) FROM issue_items").fetchone()[0] == 0:
        admin_user = db.execute("SELECT id FROM users WHERE username = 'admin' LIMIT 1").fetchone()
        created_by_user_id = admin_user['id'] if admin_user else None
        for seed_issue in ISSUE_SEED_DATA:
            involved_departments = '|'.join(
                [part.strip() for part in str(seed_issue.get('involved_departments') or '').split('/') if part.strip()]
            )
            db.execute(
                '''
                INSERT OR IGNORE INTO issue_items (
                    row_id, issue_date, issue_date_sort, issue, pareto_law, involved_departments,
                    section_team, issue_type, writer, reported_by, priority, status,
                    responsible_section, responsible_person, root_cause, impact,
                    action_plan, resources_needed, target_resolution_date, first_follow_up_date,
                    first_follow_up_notes, second_follow_up_date, second_follow_up_notes,
                    follow_up_by, progress_note, linked_issues, final_status, created_by_user_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    seed_issue['row_id'],
                    seed_issue['issue_date'],
                    parse_seed_issue_date_sort(seed_issue['issue_date']),
                    seed_issue['issue'],
                    1 if seed_issue.get('pareto_law') else 0,
                    involved_departments,
                    '',
                    seed_issue.get('issue_type', 'Problem'),
                    seed_issue.get('writer', ''),
                    seed_issue.get('reported_by', ''),
                    seed_issue.get('priority', 'Medium'),
                    seed_issue.get('status', 'Open'),
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    created_by_user_id
                )
            )

    db.commit()

ensure_base_schema()
init_db()
ensure_admin_user()

# Initialize Planning tables
db = get_db()
init_planning_tables(db)
db.close()

# Initialize Marketing tables
from marketing_models import run_marketing_migrations
from social_media_models import run_social_media_migrations
run_marketing_migrations()
run_social_media_migrations()

# =============================================================================
# UNIFIED PLATFORM INITIALIZATION
# =============================================================================
# Initialize the unified platform infrastructure that provides:
# - Centralized database connections
# - Unified permission/RBAC system
# - Centralized settings management
# - Unified navigation/menu structure
# - Master data management
# - Reporting framework

initialize_platform_schema()  # Database - unified audit, notifications, settings
initialize_permissions()        # RBAC - unified permission system
initialize_settings()          # Settings - unified settings tables
initialize_reporting()         # Reporting - unified reporting tables
initialize_master_data()      # Master data - mapping tables

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.before_request
def check_session_auth():
    """Before-request hook that enforces login for all protected routes."""
    allowed_routes = ['login', 'static', 'set_language']
    if request.endpoint not in allowed_routes and 'user_id' not in session:
        return redirect(url_for('login'))


@app.context_processor
def inject_translations():
    """Inject translation function and translations into all templates."""
    def t(key, default=None):
        user_id = session.get('user_id')
        if user_id:
            prefs = get_user_preferences()
            lang = prefs.get('language', 'en')
        else:
            lang = 'en'
        return get_translation(lang, key, default)

    user_id = session.get('user_id')
    if user_id:
        prefs = get_user_preferences()
        lang = prefs.get('language', 'en')
        translations = get_translations(lang)
        languages = LANGUAGES
    else:
        translations = get_translations('en')
        languages = LANGUAGES

    return dict(
        t=t,
        translations=translations,
        languages=languages,
        is_rtl=is_rtl,
        get_language_direction=get_language_direction
    )


def admin_required(f=None):
    """Decorator that works both as @admin_required and @admin_required()."""
    def decorator(fn):
        @wraps(fn)
        def decorated_function(*args, **kwargs):
            if not session.get('can_manage_users'):
                flash("Access Denied. You do not have permission to view this page.", "error")
                return redirect(url_for('index'))
            return fn(*args, **kwargs)
        return decorated_function
    if f is None:
        return decorator
    elif callable(f):
        return decorator(f)
    else:
        return decorator

def stock_admin_required(f):
    """Decorator that allows any authenticated user to access stock sync pages.
    This is because stock data is viewable by all warehouse users.
    Admin-only actions (like sync trigger) have separate permission checks.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash("Access Denied. Please login first.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_globals():
    user_preferences = get_user_preferences()
    direction_preference = user_preferences.get('interface_direction', 'auto')
    browser_language = (request.accept_languages.best or '').lower()
    auto_rtl = browser_language.startswith(('ar', 'fa', 'ur', 'he'))
    resolved_direction = 'rtl' if direction_preference == 'rtl' or (direction_preference == 'auto' and auto_rtl) else 'ltr'
    user_preferences['direction_resolved'] = resolved_direction
    
    # Get language for menu translation
    language = user_preferences.get('language', 'en')
    
    # Get current user ID from session
    user_id = session.get('user_id')
    
    # Build unified navigation menu
    main_menu = []
    breadcrumbs = []
    current_module = None
    
    if user_id:
        main_menu = get_main_menu(user_id, language)
        breadcrumbs = get_breadcrumbs(request.path, language)
        current_module = get_active_module(request.path)
    
    # Get notification and task badges
    notification_count = 0
    task_badge = 0
    if user_id:
        try:
            notification_count = get_notification_badge(user_id)
            task_badge = get_one(
                "SELECT COUNT(*) as cnt FROM task_items WHERE assigned_to_user_id = ? AND status NOT IN ('Completed', 'Canceled')",
                (user_id,)
            )
            task_badge = task_badge['cnt'] if task_badge else 0
        except:
            pass
    
    # Get platform settings
    platform_name = get_platform_setting('platform_name', 'WHDASH')
    
    return dict(
        APP_NAME=platform_name,
        user_preferences=user_preferences,
        main_menu=main_menu,
        breadcrumbs=breadcrumbs,
        current_module=current_module,
        notification_count=notification_count,
        task_badge=task_badge,
        # Expose unified status helpers
        STATUS_COLORS=STATUS_COLORS,
        STANDARD_STATUSES=STANDARD_STATUSES,
        # Expose permission helpers for templates
        user_has_permission=lambda m, r, a: user_has_permission(user_id, m, r, a) if user_id else False,
        # Expose theme system helpers
        available_themes=get_available_themes(),
        current_theme_id=user_preferences.get('theme', get_default_theme()),
        current_theme_config=get_theme_config(user_preferences.get('theme', get_default_theme())),
        theme_tokens=get_theme_tokens(user_preferences.get('theme', get_default_theme())),
        chart_palette=get_chart_palette(user_preferences.get('theme', get_default_theme())),
        # Expose theme engine helpers
        theme_preview_data=theme_preview_data(),
        get_status_color_classes=get_status_color_classes,
        get_priority_classes=get_priority_classes,
        # Expose settings helpers
        get_setting=get_setting,
    )


TASK_PRIORITIES = ['Low', 'Medium', 'High', 'Critical']
TASK_STATUSES = ['Open', 'In Progress', 'Review', 'Completed', 'Canceled']
TASK_COLUMN_OPTIONS = [
    {'key': 'source', 'label': 'Source', 'description': 'Import source and origin badge'},
    {'key': 'company', 'label': 'Company', 'description': 'Owning company or subsidiary'},
    {'key': 'department', 'label': 'Department', 'description': 'Task department or team'},
    {'key': 'task', 'label': 'Task', 'description': 'Task title and audit stamp'},
    {'key': 'assigned_to', 'label': 'Assigned To', 'description': 'Execution owner'},
    {'key': 'priority', 'label': 'Priority', 'description': 'Task urgency level'},
    {'key': 'report_to', 'label': 'Report To', 'description': 'Manager or escalation owner'},
    {'key': 'progress', 'label': 'Progress %', 'description': 'Completion progress bar'},
    {'key': 'status', 'label': 'Status', 'description': 'Lifecycle state'},
    {'key': 'desc', 'label': 'Desc', 'description': 'Primary description field'},
    {'key': 'time', 'label': 'Time', 'description': 'Due time and future-task marker'},
    {'key': 'add_desc', 'label': 'Add desc', 'description': 'Latest execution update'},
    {'key': 'subtasks', 'label': 'Subtasks', 'description': 'View and manage subtasks'},
]
TASK_COLUMN_KEYS = [item['key'] for item in TASK_COLUMN_OPTIONS]
TASK_DEFAULT_VISIBLE_COLUMNS = TASK_COLUMN_KEYS[:]

# Task List (combined task + subtask view) columns
TASK_LIST_COLUMN_OPTIONS = [
    {'key': 'type', 'label': 'Type', 'description': 'Task or Subtask badge'},
    {'key': 'title', 'label': 'Title', 'description': 'Item title and description'},
    {'key': 'parent', 'label': 'Parent Task', 'description': 'Parent task for subtasks'},
    {'key': 'assigned', 'label': 'Assigned To', 'description': 'Person responsible'},
    {'key': 'priority', 'label': 'Priority', 'description': 'Urgency level'},
    {'key': 'status', 'label': 'Status', 'description': 'Current state'},
    {'key': 'progress', 'label': 'Progress', 'description': 'Completion percentage'},
    {'key': 'due', 'label': 'Due Date', 'description': 'Deadline'},
]
TASK_LIST_COLUMN_KEYS = [item['key'] for item in TASK_LIST_COLUMN_OPTIONS]
TASK_LIST_DEFAULT_COLUMNS = TASK_LIST_COLUMN_KEYS[:]

# Subtask constants
SUBTASK_PRIORITIES = ['Low', 'Medium', 'High', 'Critical']
SUBTASK_STATUSES = ['Pending', 'In Progress', 'Completed', 'Cancelled']
SUBTASK_COLUMN_OPTIONS = [
    {'key': 'checkbox', 'label': '', 'description': 'Completion checkbox'},
    {'key': 'subtask', 'label': 'Subtask', 'description': 'Subtask title and details'},
    {'key': 'assigned_to', 'label': 'Assigned To', 'description': 'Subtask owner'},
    {'key': 'priority', 'label': 'Priority', 'description': 'Urgency level'},
    {'key': 'status', 'label': 'Status', 'description': 'Current state'},
    {'key': 'progress', 'label': 'Progress %', 'description': 'Completion percentage'},
    {'key': 'due_at', 'label': 'Due Date', 'description': 'Deadline'},
    {'key': 'actions', 'label': 'Actions', 'description': 'Edit/Delete actions'},
]
SUBTASK_COLUMN_KEYS = [item['key'] for item in SUBTASK_COLUMN_OPTIONS]
SUBTASK_DEFAULT_VISIBLE_COLUMNS = SUBTASK_COLUMN_KEYS[:]

# Transaction constants
TRANSACTION_TYPES = ['Expense', 'Revenue', 'Time', 'Resource']
TRANSACTION_STATUSES = ['Pending', 'Approved', 'Rejected', 'Cancelled']

# Report constants
REPORT_TYPES = ['Status', 'Priority', 'Department', 'User', 'Timeline', 'Financial', 'Productivity']
REPORT_INTERVALS = ['Daily', 'Weekly', 'Monthly', 'Quarterly', 'Yearly', 'Custom']

ISSUE_PRIORITY_OPTIONS = ['High', 'Medium', 'Low']
ISSUE_STATUS_OPTIONS = ['Open', 'Pending', 'Closed']
ISSUE_TYPE_OPTIONS = ['Problem', 'Suggestion', 'Issue']
ISSUE_COLUMN_OPTIONS = [
    {'key': 'row_id', 'label': 'Row ID', 'rtl': 'ردیف'},
    {'key': 'issue_date', 'label': 'Date', 'rtl': 'تاریخ'},
    {'key': 'issue', 'label': 'Issue', 'rtl': 'مسئله'},
    {'key': 'pareto_law', 'label': 'Pareto Law', 'rtl': 'قانون پارتو'},
    {'key': 'involved_departments', 'label': 'Involved Department', 'rtl': 'بخش های درگیر'},
    {'key': 'section_team', 'label': 'Section / Team', 'rtl': 'بخش / تیم درگیر'},
    {'key': 'issue_type', 'label': 'Type', 'rtl': 'نوع'},
    {'key': 'writer', 'label': 'Writer', 'rtl': 'نویسنده'},
    {'key': 'reported_by', 'label': 'Reported By', 'rtl': 'گزارش شده'},
    {'key': 'priority', 'label': 'Priority', 'rtl': 'اولویت'},
    {'key': 'status', 'label': 'Status', 'rtl': 'وضعیت'},
    {'key': 'responsible_section', 'label': 'Responsible Section', 'rtl': 'بخش مسئول'},
    {'key': 'responsible_person', 'label': 'Responsible Person', 'rtl': 'فرد مسئول'},
    {'key': 'root_cause', 'label': 'Root Cause', 'rtl': 'علت ریشه‌ای'},
    {'key': 'impact', 'label': 'Impact', 'rtl': 'تأثیر مشکل'},
    {'key': 'action_plan', 'label': 'Action Plan', 'rtl': 'برنامه اقدام'},
    {'key': 'resources_needed', 'label': 'Resources Needed', 'rtl': 'منابع لازم'},
    {'key': 'target_resolution_date', 'label': 'Target Resolution Date', 'rtl': 'تاریخ هدف رفع'},
    {'key': 'first_follow_up_date', 'label': 'First Follow-up Date', 'rtl': 'تاریخ پیگیری اول'},
    {'key': 'first_follow_up_notes', 'label': 'Notes', 'rtl': 'یادداشت'},
    {'key': 'second_follow_up_date', 'label': 'Second Follow-up Date', 'rtl': 'تاریخ پیگیری دوم'},
    {'key': 'second_follow_up_notes', 'label': 'Notes 2', 'rtl': 'یادداشت دوم'},
    {'key': 'follow_up_by', 'label': 'Follow-up By', 'rtl': 'پیگیری توسط'},
    {'key': 'progress_note', 'label': 'Note of Progress', 'rtl': 'یادداشت پیشرفت'},
    {'key': 'linked_issues', 'label': 'Linked Issues', 'rtl': 'مشکلات مرتبط'},
    {'key': 'final_status', 'label': 'Final Status', 'rtl': 'وضعیت نهایی'}
]
ISSUE_COLUMN_KEYS = [item['key'] for item in ISSUE_COLUMN_OPTIONS]
ISSUE_DEFAULT_VISIBLE_COLUMNS = ISSUE_COLUMN_KEYS[:]
USER_THEME_OPTIONS = [
    {'value': 'dark', 'label': 'Dark Night'},
    {'value': 'light', 'label': 'Light Day'},
    {'value': 'blue', 'label': 'Ocean Blue'},
    {'value': 'green', 'label': 'Forest Green'},
    {'value': 'orange', 'label': 'Sunset Orange'},
    {'value': 'purple', 'label': 'Royal Purple'}
]
USER_FONT_FAMILY_OPTIONS = [
    {'value': 'outfit', 'label': 'Outfit', 'stack': "'Outfit', 'Vazirmatn', 'Noto Sans Arabic', 'Noto Sans', sans-serif"},
    {'value': 'manrope', 'label': 'Manrope', 'stack': "'Manrope', 'Vazirmatn', 'Noto Sans Arabic', 'Noto Sans', sans-serif"},
    {'value': 'tajawal', 'label': 'Tajawal', 'stack': "'Tajawal', 'Vazirmatn', 'Noto Sans Arabic', sans-serif"},
    {'value': 'space_grotesk', 'label': 'Space Grotesk', 'stack': "'Space Grotesk', 'Vazirmatn', 'Noto Sans Arabic', 'Noto Sans', sans-serif"},
    {'value': 'vazirmatn', 'label': 'Vazirmatn', 'stack': "'Vazirmatn', 'Noto Sans Arabic', 'Noto Sans', sans-serif"},
    {'value': 'noto_sans', 'label': 'Noto Sans', 'stack': "'Noto Sans', 'Vazirmatn', 'Noto Sans Arabic', sans-serif"},
    {'value': 'calibri', 'label': 'Calibri', 'stack': "'Calibri', 'Carlito', 'Segoe UI', 'Vazirmatn', 'Noto Sans Arabic', sans-serif"}
]
USER_FONT_SIZE_OPTIONS = [
    {'value': 'small', 'label': 'Small', 'size': '15px'},
    {'value': 'medium', 'label': 'Medium', 'size': '16px'},
    {'value': 'large', 'label': 'Large', 'size': '18px'}
]
USER_FONT_WEIGHT_OPTIONS = [
    {'value': 'regular', 'label': 'Regular', 'weight': '400'},
    {'value': 'semibold', 'label': 'Semi Bold', 'weight': '600'},
    {'value': 'bold', 'label': 'Bold', 'weight': '700'}
]
USER_TIMEZONE_OPTIONS = [
    {'value': 'Asia/Dubai', 'label': 'Dubai (GMT+4)'},
    {'value': 'Asia/Tehran', 'label': 'Tehran (GMT+3:30)'},
    {'value': 'Asia/Kabul', 'label': 'Kabul (GMT+4:30)'},
    {'value': 'Asia/Karachi', 'label': 'Karachi (GMT+5)'},
    {'value': 'Asia/Kolkata', 'label': 'Mumbai / New Delhi (GMT+5:30)'},
    {'value': 'Asia/Dhaka', 'label': 'Dhaka (GMT+6)'},
    {'value': 'Asia/Bangkok', 'label': 'Bangkok (GMT+7)'},
    {'value': 'Asia/Jakarta', 'label': 'Jakarta (GMT+7)'},
    {'value': 'Asia/Singapore', 'label': 'Singapore (GMT+8)'},
    {'value': 'Asia/Hong_Kong', 'label': 'Hong Kong (GMT+8)'},
    {'value': 'Asia/Shanghai', 'label': 'Shanghai (GMT+8)'},
    {'value': 'Asia/Tokyo', 'label': 'Tokyo (GMT+9)'},
    {'value': 'Asia/Seoul', 'label': 'Seoul (GMT+9)'},
    {'value': 'Asia/Yerevan', 'label': 'Yerevan (GMT+4)'},
    {'value': 'Asia/Tbilisi', 'label': 'Tbilisi (GMT+4)'},
    {'value': 'Asia/Baghdad', 'label': 'Baghdad (GMT+3)'},
    {'value': 'Asia/Kuwait', 'label': 'Kuwait (GMT+3)'},
    {'value': 'Asia/Riyadh', 'label': 'Riyadh (GMT+3)'},
    {'value': 'Asia/Qatar', 'label': 'Qatar (GMT+3)'},
    {'value': 'Europe/Istanbul', 'label': 'Istanbul (GMT+3)'},
    {'value': 'Europe/Moscow', 'label': 'Moscow (GMT+3)'},
    {'value': 'Europe/Baku', 'label': 'Baku (GMT+4)'},
    {'value': 'Europe/Athens', 'label': 'Athens (GMT+2)'},
    {'value': 'Europe/Bucharest', 'label': 'Bucharest (GMT+2)'},
    {'value': 'Europe/Vienna', 'label': 'Vienna (GMT+1)'},
    {'value': 'Europe/Berlin', 'label': 'Berlin (GMT+1)'},
    {'value': 'Europe/Amsterdam', 'label': 'Amsterdam (GMT+1)'},
    {'value': 'Europe/Paris', 'label': 'Paris (GMT+1)'},
    {'value': 'Europe/Madrid', 'label': 'Madrid (GMT+1)'},
    {'value': 'Europe/London', 'label': 'London (GMT+0)'},
    {'value': 'Europe/Warsaw', 'label': 'Warsaw (GMT+1)'},
    {'value': 'Africa/Cairo', 'label': 'Cairo (GMT+2)'},
    {'value': 'Africa/Nairobi', 'label': 'Nairobi (GMT+3)'},
    {'value': 'Africa/Lagos', 'label': 'Lagos (GMT+1)'},
    {'value': 'Australia/Sydney', 'label': 'Sydney (GMT+10)'},
    {'value': 'Australia/Perth', 'label': 'Perth (GMT+8)'},
    {'value': 'Pacific/Auckland', 'label': 'Auckland (GMT+12)'},
    {'value': 'America/Toronto', 'label': 'Toronto (GMT-5)'},
    {'value': 'America/New_York', 'label': 'New York (GMT-5)'},
    {'value': 'America/Chicago', 'label': 'Chicago (GMT-6)'},
    {'value': 'America/Denver', 'label': 'Denver (GMT-7)'},
    {'value': 'America/Los_Angeles', 'label': 'Los Angeles (GMT-8)'},
    {'value': 'America/Vancouver', 'label': 'Vancouver (GMT-8)'},
    {'value': 'America/Mexico_City', 'label': 'Mexico City (GMT-6)'},
    {'value': 'America/Sao_Paulo', 'label': 'Sao Paulo (GMT-3)'},
    {'value': 'America/Buenos_Aires', 'label': 'Buenos Aires (GMT-3)'},
    {'value': 'UTC', 'label': 'UTC'}
]
USER_DATE_FORMAT_OPTIONS = [
    {'value': 'DD/MM/YYYY', 'label': 'DD/MM/YYYY'},
    {'value': 'MM/DD/YYYY', 'label': 'MM/DD/YYYY'},
    {'value': 'YYYY-MM-DD', 'label': 'YYYY-MM-DD'}
]
USER_DIRECTION_OPTIONS = [
    {'value': 'auto', 'label': 'Auto'},
    {'value': 'ltr', 'label': 'Left to Right'},
    {'value': 'rtl', 'label': 'Right to Left'}
]

# Language options for preferences
USER_LANGUAGE_OPTIONS = [
    {'value': 'en', 'label': 'English'},
    {'value': 'fa', 'label': 'فارسی (Persian)'},
    {'value': 'ar', 'label': 'العربية (Arabic)'},
    {'value': 'ru', 'label': 'Русский (Russian)'}
]
USER_CURRENCY_OPTIONS = [
    {'value': 'AED', 'label': 'AED'},
    {'value': 'USD', 'label': 'USD'},
    {'value': 'EUR', 'label': 'EUR'},
    {'value': 'GBP', 'label': 'GBP'},
    {'value': 'SAR', 'label': 'SAR'},
    {'value': 'INR', 'label': 'INR'},
    {'value': 'PKR', 'label': 'PKR'}
]
USER_DENSITY_OPTIONS = [
    {'value': 'compact', 'label': 'Compact'},
    {'value': 'comfortable', 'label': 'Comfortable'},
    {'value': 'spacious', 'label': 'Spacious'}
]
USER_BOOLEAN_OPTIONS = [
    {'value': '1', 'label': 'Enabled'},
    {'value': '0', 'label': 'Disabled'}
]
USER_PREFERENCE_DEFAULTS = {
    'theme': 'dark',
    'font_family': 'outfit',
    'font_size': 'medium',
    'font_weight': 'regular',
    'timezone': 'Asia/Dubai',
    'date_format': 'DD/MM/YYYY',
    'interface_direction': 'auto',
    'currency': 'AED',
    'density': 'comfortable',
    'reduced_motion': 0,
    'show_seconds': 1,
    'sidebar_compact': 0,
    'language': 'en'
}
FUTURE_TASK_KEYWORDS = (
    'future',
    'tomorrow',
    'next week',
    'next month',
    'later',
    'آینده',
    'اينده',
    'فردا',
    'بعد از مرخصی',
    'بعد از مرخصي',
    'پس از مرخصی',
    'پس از مرخصي'
)


def user_can_manage_all_tasks():
    return bool(session.get('can_manage_users'))


def user_can_create_subtasks():
    """Check if current user can create subtasks"""
    return bool(session.get('user_id'))


def user_can_edit_subtasks():
    """Check if current user can edit subtasks they own or are assigned to"""
    return bool(session.get('user_id'))


def user_can_delete_subtasks():
    """Check if current user can delete subtasks"""
    return bool(session.get('can_manage_users'))


def user_can_manage_task_transactions():
    """Check if current user can manage task transactions"""
    return bool(session.get('can_manage_users') or session.get('can_edit_stock'))


def user_can_view_task_reports():
    """Check if current user can view task reports"""
    return bool(session.get('user_id'))


def user_can_export_task_reports():
    """Check if current user can export task reports"""
    return bool(session.get('can_manage_users'))


# ─── Warehouse Stock Sync Permissions ─────────────────────────────────────────

def user_can_sync_stock():
    """Check if current user can trigger stock synchronization with Peyvast"""
    return bool(session.get('can_manage_users') or session.get('can_edit_stock'))

def user_can_view_live_stock():
    """Check if current user can view live synced stock data"""
    return bool(session.get('user_id'))

def user_can_view_stock_source_details():
    """Check if current user can view stock source details like seller/invoice"""
    return bool(session.get('can_manage_users') or session.get('can_edit_stock'))

def user_can_export_stock_reports():
    """Check if current user can export stock reports"""
    return bool(session.get('can_manage_users') or session.get('can_edit_stock'))

def user_can_view_part_costs():
    """Check if current user can view part cost information (last purchase price, avg unit cost)"""
    return bool(session.get('can_manage_users') or session.get('can_edit_stock'))

def user_can_view_supplier_invoice_details():
    """Check if current user can view supplier and invoice details"""
    return bool(session.get('can_manage_users'))

def user_can_manage_stock_sync_settings():
    """Check if current user can manage stock sync settings (schedule, credentials, etc)"""
    return bool(session.get('can_manage_users'))


def normalize_subtask_priority(priority_value):
    """Normalize subtask priority value"""
    priority = (priority_value or 'Medium').strip()
    return priority if priority in SUBTASK_PRIORITIES else 'Medium'


def normalize_subtask_status(status_value):
    """Normalize subtask status value"""
    status = (status_value or 'Pending').strip()
    return status if status in SUBTASK_STATUSES else 'Pending'


def sanitize_task_transaction_columns(raw_columns):
    """Ensure only valid transaction columns are returned"""
    valid_columns = ['category', 'type', 'amount', 'quantity', 'unit', 'description', 'reference', 'date', 'actions']
    if not raw_columns:
        return valid_columns
    return [col for col in raw_columns if col in valid_columns]


def get_user_task_permissions(db, user_id):
    """Get all task-related permissions for a user"""
    rows = db.execute(
        'SELECT permission_key, permission_value FROM task_user_permissions WHERE user_id = ?',
        (user_id,)
    ).fetchall()
    return {row['permission_key']: row['permission_value'] for row in rows}


def check_user_task_permission(db, user_id, permission_key):
    """Check if user has a specific task permission"""
    row = db.execute(
        'SELECT permission_value FROM task_user_permissions WHERE user_id = ? AND permission_key = ?',
        (user_id, permission_key)
    ).fetchone()
    return bool(row and row['permission_value'])


def preference_option_values(options):
    return {option['value'] for option in options}


def build_user_preferences(raw_preferences=None):
    preferences = dict(USER_PREFERENCE_DEFAULTS)
    if isinstance(raw_preferences, sqlite3.Row):
        raw_preferences = dict(raw_preferences)
    if isinstance(raw_preferences, dict):
        preferences.update({key: raw_preferences.get(key) for key in preferences.keys() if key in raw_preferences})

    theme_values = get_all_theme_ids()
    font_values = preference_option_values(USER_FONT_FAMILY_OPTIONS)
    font_size_values = preference_option_values(USER_FONT_SIZE_OPTIONS)
    font_weight_values = preference_option_values(USER_FONT_WEIGHT_OPTIONS)
    timezone_values = preference_option_values(USER_TIMEZONE_OPTIONS)
    date_format_values = preference_option_values(USER_DATE_FORMAT_OPTIONS)
    direction_values = preference_option_values(USER_DIRECTION_OPTIONS)
    currency_values = preference_option_values(USER_CURRENCY_OPTIONS)
    density_values = preference_option_values(USER_DENSITY_OPTIONS)
    language_values = preference_option_values(USER_LANGUAGE_OPTIONS)

    preferences['theme'] = preferences['theme'] if preferences['theme'] in theme_values else USER_PREFERENCE_DEFAULTS['theme']
    preferences['font_family'] = preferences['font_family'] if preferences['font_family'] in font_values else USER_PREFERENCE_DEFAULTS['font_family']
    preferences['font_size'] = preferences['font_size'] if preferences['font_size'] in font_size_values else USER_PREFERENCE_DEFAULTS['font_size']
    preferences['font_weight'] = preferences['font_weight'] if preferences['font_weight'] in font_weight_values else USER_PREFERENCE_DEFAULTS['font_weight']
    preferences['timezone'] = preferences['timezone'] if preferences['timezone'] in timezone_values else USER_PREFERENCE_DEFAULTS['timezone']
    preferences['date_format'] = preferences['date_format'] if preferences['date_format'] in date_format_values else USER_PREFERENCE_DEFAULTS['date_format']
    preferences['interface_direction'] = preferences['interface_direction'] if preferences['interface_direction'] in direction_values else USER_PREFERENCE_DEFAULTS['interface_direction']
    preferences['currency'] = preferences['currency'] if preferences['currency'] in currency_values else USER_PREFERENCE_DEFAULTS['currency']
    preferences['density'] = preferences['density'] if preferences['density'] in density_values else USER_PREFERENCE_DEFAULTS['density']
    preferences['language'] = preferences['language'] if preferences['language'] in language_values else USER_PREFERENCE_DEFAULTS['language']
    preferences['reduced_motion'] = 1 if int(preferences.get('reduced_motion') or 0) else 0
    preferences['show_seconds'] = 1 if int(preferences.get('show_seconds') or 0) else 0
    preferences['sidebar_compact'] = 1 if int(preferences.get('sidebar_compact') or 0) else 0

    font_stack_map = {option['value']: option['stack'] for option in USER_FONT_FAMILY_OPTIONS}
    font_size_map = {option['value']: option['size'] for option in USER_FONT_SIZE_OPTIONS}
    font_weight_map = {option['value']: option['weight'] for option in USER_FONT_WEIGHT_OPTIONS}
    preferences['font_stack'] = font_stack_map.get(preferences['font_family'], "'Outfit', sans-serif")
    preferences['font_size_value'] = font_size_map.get(preferences['font_size'], '16px')
    preferences['font_weight_value'] = font_weight_map.get(preferences['font_weight'], '400')
    preferences['timezone_label'] = preferences['timezone'].split('/')[-1].replace('_', ' ')
    preferences['is_dark'] = is_dark_theme(preferences['theme'])

    # Resolve direction based on language and interface_direction setting
    lang_direction = get_language_direction(preferences['language'])
    if preferences['interface_direction'] == 'auto':
        preferences['direction_resolved'] = lang_direction
    else:
        preferences['direction_resolved'] = preferences['interface_direction']

    return preferences


def get_user_preferences(db=None, user_id=None):
    resolved_user_id = user_id or session.get('user_id')
    if not resolved_user_id:
        return build_user_preferences()

    local_db = db or get_db()
    row = local_db.execute(
        "SELECT * FROM user_preferences WHERE user_id = ?",
        (resolved_user_id,)
    ).fetchone()
    return build_user_preferences(row)


def save_user_preferences_record(db, user_id, preferences):
    sanitized = build_user_preferences(preferences)
    db.execute(
        '''
        INSERT INTO user_preferences (
            user_id, theme, font_family, font_size, font_weight, timezone, date_format, interface_direction, currency,
            density, reduced_motion, show_seconds, sidebar_compact, language, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            theme = excluded.theme,
            font_family = excluded.font_family,
            font_size = excluded.font_size,
            font_weight = excluded.font_weight,
            timezone = excluded.timezone,
            date_format = excluded.date_format,
            interface_direction = excluded.interface_direction,
            currency = excluded.currency,
            density = excluded.density,
            reduced_motion = excluded.reduced_motion,
            show_seconds = excluded.show_seconds,
            sidebar_compact = excluded.sidebar_compact,
            language = excluded.language,
            updated_at = CURRENT_TIMESTAMP
        ''',
        (
            user_id,
            sanitized['theme'],
            sanitized['font_family'],
            sanitized['font_size'],
            sanitized['font_weight'],
            sanitized['timezone'],
            sanitized['date_format'],
            sanitized['interface_direction'],
            sanitized['currency'],
            sanitized['density'],
            sanitized['reduced_motion'],
            sanitized['show_seconds'],
            sanitized['sidebar_compact'],
            sanitized['language']
        )
    )
    return sanitized


def get_task_scope_clause(alias='t'):
    if user_can_manage_all_tasks():
        return '', []

    current_user_id = session.get('user_id')
    current_company_id = session.get('company_id')
    scope_parts = []
    scope_params = []

    if current_user_id:
        scope_parts.append(
            f"{alias}.created_by_user_id = ? OR {alias}.assigned_to_user_id = ? OR {alias}.report_to_user_id = ?"
        )
        scope_params.extend([current_user_id, current_user_id, current_user_id])

    if current_company_id:
        scope_parts.append(f"{alias}.company_id = ?")
        scope_params.append(current_company_id)

    if not scope_parts:
        return " AND 1 = 0", []

    return f" AND ({' OR '.join(scope_parts)})", scope_params


def get_task_sort_expression(sort_by):
    sort_map = {
        'task_name': 'LOWER(t.task_name)',
        'company': 'LOWER(COALESCE(c.name, \'\'))',
        'department': 'LOWER(COALESCE(d.name, \'\'))',
        'priority': (
            "CASE t.priority "
            "WHEN 'Critical' THEN 4 "
            "WHEN 'High' THEN 3 "
            "WHEN 'Medium' THEN 2 "
            "WHEN 'Low' THEN 1 "
            "ELSE 0 END"
        ),
        'report_to': 'LOWER(COALESCE(r.username, \'\'))',
        'assigned_to': 'LOWER(COALESCE(a.username, \'\'))',
        'progress': 't.progress',
        'status': (
            "CASE t.status "
            "WHEN 'Canceled' THEN 1 "
            "WHEN 'Open' THEN 2 "
            "WHEN 'In Progress' THEN 3 "
            "WHEN 'Review' THEN 4 "
            "WHEN 'Completed' THEN 5 "
            "ELSE 6 END"
        ),
        'due_at': 'COALESCE(t.due_at, \'\')',
        'updated_at': 'COALESCE(t.updated_at, t.created_at)',
        'created_at': 't.created_at'
    }
    return sort_map.get(sort_by, 'COALESCE(t.updated_at, t.created_at)')


def clamp_progress(progress_value):
    try:
        progress = int(progress_value)
    except (TypeError, ValueError):
        progress = 0
    return max(0, min(progress, 100))


def recalculate_task_progress_from_subtasks(db, task_id):
    """Recalculate and update task_items.progress_auto based on subtask completion.
    Returns the new progress value or None if no subtasks exist."""
    total = db.execute(
        'SELECT COUNT(*) FROM task_subtasks WHERE parent_task_id = ?', (task_id,)
    ).fetchone()[0]
    if total == 0:
        return None
    completed = db.execute(
        "SELECT COUNT(*) FROM task_subtasks WHERE parent_task_id = ? AND status = 'Completed'",
        (task_id,)
    ).fetchone()[0]
    new_progress = int((completed * 100) / total)
    db.execute(
        'UPDATE task_items SET progress_auto = ? WHERE id = ?',
        (new_progress, task_id)
    )
    return new_progress


def update_task_progress_if_not_manual(db, task_id):
    """Only update task progress if it's not manually set (progress_auto >= 0 means auto mode)."""
    task = db.execute('SELECT progress_auto, progress FROM task_items WHERE id = ?', (task_id,)).fetchone()
    if not task:
        return
    if task['progress_auto'] is not None and task['progress_auto'] < 0:
        return
    subtask_count = db.execute(
        'SELECT COUNT(*) FROM task_subtasks WHERE parent_task_id = ?', (task_id,)
    ).fetchone()[0]
    if subtask_count == 0:
        return
    auto_progress = recalculate_task_progress_from_subtasks(db, task_id)
    if auto_progress is not None:
        db.execute(
            'UPDATE task_items SET progress = ? WHERE id = ?',
            (auto_progress, task_id)
        )


def parse_optional_int(value):
    if value in (None, '', 'null'):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def normalize_task_status(status_value):
    status = (status_value or 'Open').strip()
    return status if status in TASK_STATUSES else 'Open'


def normalize_task_priority(priority_value):
    priority = (priority_value or 'Medium').strip()
    return priority if priority in TASK_PRIORITIES else 'Medium'


def parse_task_due_datetime(raw_value):
    if raw_value in (None, ''):
        return None

    due_text = str(raw_value).strip()
    if not due_text:
        return None

    normalized = due_text.replace('T', ' ')
    candidates = [normalized]
    if len(normalized) >= 19:
        candidates.append(normalized[:19])
    if len(normalized) >= 16:
        candidates.append(normalized[:16])
    if len(normalized) >= 10:
        candidates.append(normalized[:10])

    for candidate in candidates:
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d'):
            try:
                return datetime.strptime(candidate, fmt)
            except ValueError:
                continue

    try:
        parsed = datetime.fromisoformat(due_text.replace('Z', '+00:00'))
        if parsed.tzinfo:
            return parsed.astimezone().replace(tzinfo=None)
        return parsed
    except ValueError:
        return None


def task_mentions_future(task):
    searchable = ' '.join([
        str(task.get('task_name') or ''),
        str(task.get('description') or ''),
        str(task.get('latest_note') or '')
    ]).lower()
    return any(keyword in searchable for keyword in FUTURE_TASK_KEYWORDS)


def annotate_task_note_metadata(task):
    raw_note = str(task.get('latest_note') or '').strip()
    parts = [part.strip() for part in raw_note.split('|') if part.strip()]
    visible_parts = []
    source_row = None
    source_report_to = ''
    raw_status = ''

    for part in parts:
        row_match = re.fullmatch(r'\[row:(\d+)\]', part, flags=re.IGNORECASE)
        if row_match:
            source_row = int(row_match.group(1))
            continue
        if part.lower().startswith('report to:'):
            source_report_to = part.split(':', 1)[1].strip()
            continue
        if part.lower().startswith('status(raw):'):
            raw_status = part.split(':', 1)[1].strip()
            continue
        if part.lower().startswith('imported from sheet row '):
            source_row_match = re.search(r'(\d+)', part)
            if source_row_match:
                source_row = int(source_row_match.group(1))
            continue
        if part.lower().startswith('sheet report to:'):
            source_report_to = part.split(':', 1)[1].strip()
            continue
        if part.lower().startswith('sheet status:'):
            raw_status = part.split(':', 1)[1].strip()
            continue
        visible_parts.append(part)

    task['source_row'] = source_row
    task['source_label'] = f'Row {source_row}' if source_row else 'Manual'
    task['task_origin'] = 'Imported' if source_row else 'Manual'
    task['source_report_to'] = source_report_to
    task['raw_status_label'] = raw_status
    task['display_note'] = ' | '.join(visible_parts)
    task['report_to_display'] = task.get('report_to_name') or source_report_to or 'Unassigned'
    task['assigned_to_display'] = task.get('assigned_to_name') or 'Unassigned'
    return task


def compose_task_latest_note(note_text, source_row=None, source_report_to='', raw_status=''):
    parts = []
    if source_row:
        parts.append(f'[row:{source_row}]')
    if (note_text or '').strip():
        parts.append(note_text.strip())
    if (source_report_to or '').strip():
        parts.append(f"Report To: {source_report_to.strip()}")
    if (raw_status or '').strip():
        parts.append(f"Status(raw): {raw_status.strip()}")
    return ' | '.join(parts)


def annotate_task_time_flags(task, now_value=None):
    now_value = now_value or datetime.now()
    due_datetime = parse_task_due_datetime(task.get('due_at'))
    is_due_in_future = bool(due_datetime and due_datetime > now_value)
    is_keyword_future = task_mentions_future(task)
    is_archived = int(task.get('is_archived') or 0) == 1
    is_completed = (task.get('status') or '').strip() == 'Completed'

    is_future_task = (not is_archived) and (not is_completed) and (is_due_in_future or is_keyword_future)
    task['is_future_task'] = is_future_task
    task['is_future_due'] = is_due_in_future
    task['future_reason'] = 'due_at' if is_due_in_future else ('keyword' if is_keyword_future else '')
    task['is_future_without_time'] = is_future_task and due_datetime is None
    return task


def prepare_task_for_view(task, now_value=None):
    annotate_task_note_metadata(task)
    annotate_task_time_flags(task, now_value)
    task['time_display'] = task['due_at'][:16].replace('T', ' ') if task.get('due_at') else 'No due time'
    if task.get('is_future_without_time'):
        task['time_display'] = 'Missing time (Future Task)'
    return task


def user_can_edit_issues():
    return bool(session.get('can_manage_users') or session.get('can_edit_stock'))


def parse_issue_date_sort_value(issue_date):
    raw_value = str(issue_date or '').strip()
    if not raw_value or raw_value.lower() == 'past':
        return None
    for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(raw_value, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None


def split_issue_departments(value):
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    raw_value = str(value or '').strip()
    if not raw_value:
        return []
    delimiter = '|' if '|' in raw_value else '/'
    return [item.strip() for item in raw_value.split(delimiter) if item.strip()]


def serialize_issue_departments(value):
    return '|'.join(split_issue_departments(value))


def normalize_issue_priority(priority_value):
    priority = (priority_value or 'Medium').strip().title()
    return priority if priority in ISSUE_PRIORITY_OPTIONS else 'Medium'


def normalize_issue_status(status_value):
    status = (status_value or 'Open').strip().title()
    return status if status in ISSUE_STATUS_OPTIONS else 'Open'


def normalize_issue_type(issue_type):
    normalized = (issue_type or 'Problem').strip().title()
    return normalized if normalized in ISSUE_TYPE_OPTIONS else 'Problem'


def issue_priority_badge(priority):
    return {
        'High': 'bg-rose-500/15 text-rose-200 border-rose-400/30',
        'Medium': 'bg-amber-500/15 text-amber-200 border-amber-400/30',
        'Low': 'bg-emerald-500/15 text-emerald-200 border-emerald-400/30'
    }.get(priority, 'bg-slate-500/10 text-slate-300 border-slate-500/20')


def issue_status_badge(status):
    return {
        'Open': 'bg-sky-500/15 text-sky-200 border-sky-400/30',
        'Pending': 'bg-amber-500/15 text-amber-200 border-amber-400/30',
        'Closed': 'bg-emerald-500/15 text-emerald-200 border-emerald-400/30'
    }.get(status, 'bg-slate-500/10 text-slate-300 border-slate-500/20')


def issue_type_badge(issue_type):
    return {
        'Problem': 'bg-rose-500/15 text-rose-200 border-rose-400/30',
        'Suggestion': 'bg-violet-500/15 text-violet-200 border-violet-400/30',
        'Issue': 'bg-cyan-500/15 text-cyan-200 border-cyan-400/30'
    }.get(issue_type, 'bg-slate-500/10 text-slate-300 border-slate-500/20')


def sanitize_issue_visible_columns(raw_columns):
    if isinstance(raw_columns, str):
        try:
            raw_columns = json.loads(raw_columns)
        except (TypeError, ValueError, json.JSONDecodeError):
            raw_columns = []
    if not isinstance(raw_columns, list):
        raw_columns = []

    visible_columns = []
    for column_key in raw_columns:
        normalized_key = str(column_key or '').strip()
        if normalized_key in ISSUE_COLUMN_KEYS and normalized_key not in visible_columns:
            visible_columns.append(normalized_key)

    return visible_columns or ISSUE_DEFAULT_VISIBLE_COLUMNS[:]


def get_issue_visible_columns(db):
    user_id = session.get('user_id')
    if not user_id:
        return ISSUE_DEFAULT_VISIBLE_COLUMNS[:]

    preference_row = db.execute(
        "SELECT visible_columns FROM user_issue_preferences WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    return sanitize_issue_visible_columns(preference_row['visible_columns'] if preference_row else [])


def sanitize_task_visible_columns(raw_columns):
    if isinstance(raw_columns, str):
        try:
            raw_columns = json.loads(raw_columns)
        except (TypeError, ValueError, json.JSONDecodeError):
            raw_columns = []
    if not isinstance(raw_columns, list):
        raw_columns = []

    visible_columns = []
    for column_key in raw_columns:
        normalized_key = str(column_key or '').strip()
        if normalized_key in TASK_COLUMN_KEYS and normalized_key not in visible_columns:
            visible_columns.append(normalized_key)

    return visible_columns or TASK_DEFAULT_VISIBLE_COLUMNS[:]


def get_task_visible_columns(db):
    user_id = session.get('user_id')
    if not user_id:
        return TASK_DEFAULT_VISIBLE_COLUMNS[:]

    preference_row = db.execute(
        "SELECT visible_columns FROM user_task_preferences WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    return sanitize_task_visible_columns(preference_row['visible_columns'] if preference_row else [])


def prepare_issue_for_view(issue):
    issue['involved_departments_list'] = split_issue_departments(issue.get('involved_departments'))
    issue['involved_departments_display'] = ' / '.join(issue['involved_departments_list']) or 'Unassigned'
    issue['issue_date_sort_value'] = issue.get('issue_date_sort') or parse_issue_date_sort_value(issue.get('issue_date'))
    issue['priority_badge'] = issue_priority_badge(issue.get('priority'))
    issue['status_badge'] = issue_status_badge(issue.get('status'))
    issue['type_badge'] = issue_type_badge(issue.get('issue_type'))
    issue['pareto_display'] = 'Yes' if int(issue.get('pareto_law') or 0) else 'No'
    issue['linked_issues_display'] = issue.get('linked_issues') or '--'
    issue['final_status_display'] = issue.get('final_status') or '--'
    issue['responsible_person_display'] = issue.get('responsible_person') or 'Unassigned'
    issue['responsible_section_display'] = issue.get('responsible_section') or 'Unassigned'
    return issue


def build_issue_report(issues):
    status_counter = Counter(issue.get('status') or 'Open' for issue in issues)
    priority_counter = Counter(issue.get('priority') or 'Medium' for issue in issues)
    type_counter = Counter(issue.get('issue_type') or 'Problem' for issue in issues)
    department_counter = Counter()
    owner_counter = Counter()
    reporter_counter = Counter()

    for issue in issues:
        for department in issue.get('involved_departments_list', []):
            department_counter[department] += 1
        owner_counter[issue.get('responsible_person_display') or 'Unassigned'] += 1
        reporter_counter[issue.get('reported_by') or 'Unassigned'] += 1

    top_department = department_counter.most_common(1)
    top_owner = [(name, total) for name, total in owner_counter.most_common() if name != 'Unassigned']
    top_reporter = [(name, total) for name, total in reporter_counter.most_common() if name != 'Unassigned']

    return {
        'summary': {
            'total': len(issues),
            'unassigned_owner': sum(1 for issue in issues if issue.get('responsible_person_display') == 'Unassigned'),
            'missing_root_cause': sum(1 for issue in issues if not (issue.get('root_cause') or '').strip()),
            'missing_action_plan': sum(1 for issue in issues if not (issue.get('action_plan') or '').strip()),
            'missing_target_date': sum(1 for issue in issues if not (issue.get('target_resolution_date') or '').strip()),
            'high_priority_open': sum(1 for issue in issues if issue.get('priority') == 'High' and issue.get('status') != 'Closed'),
        },
        'status_chart': [{'label': label, 'total': status_counter.get(label, 0)} for label in ISSUE_STATUS_OPTIONS],
        'priority_chart': [{'label': label, 'total': priority_counter.get(label, 0)} for label in ISSUE_PRIORITY_OPTIONS],
        'type_chart': [{'label': label, 'total': type_counter.get(label, 0)} for label in ISSUE_TYPE_OPTIONS],
        'department_chart': [{'label': label, 'total': total} for label, total in department_counter.most_common(8)],
        'owner_chart': [{'label': label, 'total': total} for label, total in owner_counter.most_common(8)],
        'executive': {
            'top_department': top_department[0][0] if top_department else '--',
            'top_department_total': top_department[0][1] if top_department else 0,
            'top_owner': top_owner[0][0] if top_owner else '--',
            'top_owner_total': top_owner[0][1] if top_owner else 0,
            'top_reporter': top_reporter[0][0] if top_reporter else '--',
            'top_reporter_total': top_reporter[0][1] if top_reporter else 0,
        }
    }


def build_task_report(tasks):
    status_counter = Counter(task.get('status') or 'Open' for task in tasks)
    priority_counter = Counter(task.get('priority') or 'Medium' for task in tasks)
    company_counter = Counter(task.get('company_name') or 'Unassigned' for task in tasks)
    department_counter = Counter(task.get('department_name') or 'Unassigned' for task in tasks)
    owner_counter = Counter(task.get('assigned_to_display') or 'Unassigned' for task in tasks)

    active_tasks = [
        task for task in tasks
        if not task.get('is_archived') and (task.get('status') or 'Open') != 'Completed'
    ]
    top_company = company_counter.most_common(1)
    top_department = department_counter.most_common(1)
    top_owner = [(name, total) for name, total in owner_counter.most_common() if name != 'Unassigned']

    return {
        'summary': {
            'total': len(tasks),
            'active': len(active_tasks),
            'completed': sum(1 for task in tasks if task.get('status') == 'Completed'),
            'canceled': sum(1 for task in tasks if task.get('status') == 'Canceled'),
            'review': sum(1 for task in tasks if task.get('status') == 'Review'),
            'archived': sum(1 for task in tasks if task.get('is_archived')),
            'future': sum(1 for task in tasks if task.get('is_future_task')),
            'future_missing_time': sum(1 for task in tasks if task.get('is_future_without_time')),
            'overdue': sum(
                1 for task in tasks
                if not task.get('is_archived')
                and (task.get('status') or 'Open') != 'Completed'
                and task.get('due_at')
                and task.get('is_overdue')
            ),
            'unassigned_owner': sum(1 for task in tasks if task.get('assigned_to_display') == 'Unassigned'),
            'high_priority_open': sum(
                1 for task in tasks
                if task.get('priority') in ('High', 'Critical')
                and (task.get('status') or 'Open') != 'Completed'
                and not task.get('is_archived')
            ),
            'average_progress': round(
                sum(int(task.get('progress') or 0) for task in tasks) / len(tasks),
                1
            ) if tasks else 0,
        },
        'status_chart': [{'label': label, 'total': status_counter.get(label, 0)} for label in TASK_STATUSES],
        'priority_chart': [{'label': label, 'total': priority_counter.get(label, 0)} for label in TASK_PRIORITIES],
        'company_chart': [{'label': label, 'total': total} for label, total in company_counter.most_common(8)],
        'department_chart': [{'label': label, 'total': total} for label, total in department_counter.most_common(8)],
        'owner_chart': [{'label': label, 'total': total} for label, total in owner_counter.most_common(8)],
        'executive': {
            'top_company': top_company[0][0] if top_company else '--',
            'top_company_total': top_company[0][1] if top_company else 0,
            'top_department': top_department[0][0] if top_department else '--',
            'top_department_total': top_department[0][1] if top_department else 0,
            'top_owner': top_owner[0][0] if top_owner else '--',
            'top_owner_total': top_owner[0][1] if top_owner else 0,
        }
    }


def log_issue_history(db, issue_id, action_type, note=''):
    db.execute(
        '''
        INSERT INTO issue_history (issue_id, action_type, note, actor_user_id)
        VALUES (?, ?, ?, ?)
        ''',
        (issue_id, action_type, note, session.get('user_id'))
    )


def log_task_history(db, task_id, task_name, action_type, field_name='', old_value=None,
                     new_value=None, note=''):
    db.execute(
        '''
        INSERT INTO task_history (
            task_id, task_name, action_type, field_name, old_value, new_value, note, actor_user_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            task_id,
            task_name,
            action_type,
            field_name,
            '' if old_value is None else str(old_value),
            '' if new_value is None else str(new_value),
            note,
            session.get('user_id')
        )
    )


def fetch_task_record(db, task_id):
    task = db.execute(
        '''
        SELECT t.*, c.name AS company_name, d.name AS department_name,
               r.username AS report_to_name, a.username AS assigned_to_name,
               creator.username AS created_by_name
        FROM task_items t
        LEFT JOIN companies c ON t.company_id = c.id
        LEFT JOIN task_departments d ON t.department_id = d.id
        LEFT JOIN users r ON t.report_to_user_id = r.id
        LEFT JOIN users a ON t.assigned_to_user_id = a.id
        LEFT JOIN users creator ON t.created_by_user_id = creator.id
        WHERE t.id = ?
        ''',
        (task_id,)
    ).fetchone()
    if not task:
        return None

    if user_can_manage_all_tasks():
        return task

    current_user_id = session.get('user_id')
    current_company_id = session.get('company_id')
    allowed = current_user_id in (
        task['created_by_user_id'],
        task['assigned_to_user_id'],
        task['report_to_user_id']
    )
    if current_company_id and task['company_id'] == current_company_id:
        allowed = True
    return task if allowed else None


def build_task_base_query(args):
    filters = {
        'q': args.get('q', '').strip(),
        'company_id': parse_optional_int(args.get('company_id')),
        'department_id': parse_optional_int(args.get('department_id')),
        'assigned_to': parse_optional_int(args.get('assigned_to')),
        'report_to': parse_optional_int(args.get('report_to')),
        'status': (args.get('status', 'all') or 'all').strip(),
        'priority': (args.get('priority', 'all') or 'all').strip(),
        'archived': (args.get('archived', 'active') or 'active').strip(),
        'sort_by': (args.get('sort_by', 'updated_at') or 'updated_at').strip(),
        'sort_dir': 'desc' if (args.get('sort_dir', 'desc') or 'desc').lower() == 'desc' else 'asc'
    }

    base_sql = '''
        FROM task_items t
        LEFT JOIN companies c ON t.company_id = c.id
        LEFT JOIN task_departments d ON t.department_id = d.id
        LEFT JOIN users r ON t.report_to_user_id = r.id
        LEFT JOIN users a ON t.assigned_to_user_id = a.id
        LEFT JOIN users creator ON t.created_by_user_id = creator.id
        WHERE 1=1
    '''
    params = []

    scope_clause, scope_params = get_task_scope_clause('t')
    base_sql += scope_clause
    params.extend(scope_params)

    if filters['archived'] == 'active':
        base_sql += ' AND t.is_archived = 0'
    elif filters['archived'] == 'archived':
        base_sql += ' AND t.is_archived = 1'

    if filters['q']:
        base_sql += '''
            AND (
                LOWER(t.task_name) LIKE ?
                OR LOWER(COALESCE(t.description, '')) LIKE ?
                OR LOWER(COALESCE(t.latest_note, '')) LIKE ?
                OR LOWER(COALESCE(c.name, '')) LIKE ?
                OR LOWER(COALESCE(d.name, '')) LIKE ?
            )
        '''
        like_term = f"%{filters['q'].lower()}%"
        params.extend([like_term, like_term, like_term, like_term, like_term])

    if filters['company_id']:
        base_sql += ' AND t.company_id = ?'
        params.append(filters['company_id'])
    if filters['department_id']:
        base_sql += ' AND t.department_id = ?'
        params.append(filters['department_id'])
    if filters['assigned_to']:
        base_sql += ' AND t.assigned_to_user_id = ?'
        params.append(filters['assigned_to'])
    if filters['report_to']:
        base_sql += ' AND t.report_to_user_id = ?'
        params.append(filters['report_to'])
    if filters['status'] != 'all':
        base_sql += ' AND t.status = ?'
        params.append(filters['status'])
    if filters['priority'] != 'all':
        base_sql += ' AND t.priority = ?'
        params.append(filters['priority'])

    return base_sql, params, filters

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if username and password:
            db = get_db()
            user = db.execute("SELECT * FROM users WHERE username = ? OR email = ?", (username, username)).fetchone()
            
            if user and check_password_hash(user['password'], password):
                session.clear()
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role_id'] = user['role_id']
                session['profile_pic'] = user['profile_pic']
                
                role = db.execute("SELECT role_name, company_id, can_edit_stock, can_manage_users FROM roles WHERE id = ?", (user['role_id'],)).fetchone()
                
                session['role_name'] = role['role_name']
                session['company_id'] = role['company_id']
                session['can_edit_stock'] = bool(role['can_edit_stock'])
                session['can_manage_users'] = bool(role['can_manage_users'])

                # Load marketing permissions for the user
                from marketing_models import get_user_marketing_permissions
                session['marketing_permissions'] = get_user_marketing_permissions(user['id'])

                return redirect(url_for('index'))
            else:
                flash("Invalid username or password.", "error")
        else:
            flash("Please fill in all fields.", "error")
            
    return render_template('login.html')

@app.route('/login/google')
def login_google():
    flash("Google OAuth strategy is not yet configured for this domain.", "info")
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    db = get_db()
    companies = [dict(r) for r in db.execute("SELECT * FROM companies ORDER BY name").fetchall()]
    categories = [dict(r) for r in db.execute("SELECT * FROM categories ORDER BY name").fetchall()]
    brands = [dict(r) for r in db.execute("SELECT * FROM brands ORDER BY name").fetchall()]
    statuses = [dict(r) for r in db.execute("SELECT * FROM statuses ORDER BY name").fetchall()]
    vitalities = [dict(r) for r in db.execute("SELECT * FROM vitalities ORDER BY name").fetchall()]
    
    return render_template('index.html', title="Dashboard", companies=companies, categories=categories, brands=brands, statuses=statuses, vitalities=vitalities)

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    db = get_db()
    user_id = session['user_id']
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            
            if not username or not email:
                flash("Username and Email are required.", "error")
            else:
                check = db.execute("SELECT id FROM users WHERE (username = ? OR email = ?) AND id != ?", (username, email, user_id)).fetchone()
                if check:
                    flash("Username or Email already taken by another user.", "error")
                else:
                    db.execute("UPDATE users SET username = ?, email = ? WHERE id = ?", (username, email, user_id))
                    db.commit()
                    session['username'] = username
                    flash("Profile updated successfully.", "success")
                    
        elif action == 'update_password':
            current = request.form.get('current_password', '')
            new_pw = request.form.get('new_password', '')
            
            user = db.execute("SELECT password FROM users WHERE id = ?", (user_id,)).fetchone()
            if check_password_hash(user['password'], current):
                if len(new_pw) >= 6:
                    db.execute("UPDATE users SET password = ? WHERE id = ?", (generate_password_hash(new_pw), user_id))
                    db.commit()
                    flash("Password changed successfully.", "success")
                else:
                    flash("New password must be at least 6 characters.", "error")
            else:
                flash("Current password is incorrect.", "error")
                
        elif action == 'update_avatar':
            if 'avatar' in request.files:
                file = request.files['avatar']
                if file and file.filename and allowed_file(file.filename):
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    filename = f"user_{user_id}_{int(time.time())}.{ext}"
                    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    
                    db.execute("UPDATE users SET profile_pic = ? WHERE id = ?", (filename, user_id))
                    db.commit()
                    session['profile_pic'] = filename
                    flash("Profile picture updated!", "success")
                else:
                    flash("Invalid file type. Only JPG, PNG, and GIF allowed.", "error")

    user = db.execute("SELECT username, email, profile_pic FROM users WHERE id = ?", (user_id,)).fetchone()
    return render_template('profile.html', title="My Profile", user=user)


@app.route('/preferences', methods=['GET', 'POST'])
def preferences():
    db = get_db()
    user_id = session['user_id']
    current_preferences = get_user_preferences(db, user_id)

    if request.method == 'POST':
        updated_preferences = {
            'theme': request.form.get('theme', current_preferences['theme']).strip(),
            'font_family': request.form.get('font_family', current_preferences['font_family']).strip(),
            'font_size': request.form.get('font_size', current_preferences['font_size']).strip(),
            'font_weight': request.form.get('font_weight', current_preferences['font_weight']).strip(),
            'timezone': request.form.get('timezone', current_preferences['timezone']).strip(),
            'date_format': request.form.get('date_format', current_preferences['date_format']).strip(),
            'interface_direction': request.form.get('interface_direction', current_preferences['interface_direction']).strip(),
            'currency': request.form.get('currency', current_preferences['currency']).strip(),
            'density': request.form.get('density', current_preferences['density']).strip(),
            'reduced_motion': request.form.get('reduced_motion', str(current_preferences['reduced_motion'])).strip(),
            'show_seconds': request.form.get('show_seconds', str(current_preferences['show_seconds'])).strip(),
            'sidebar_compact': request.form.get('sidebar_compact', str(current_preferences['sidebar_compact'])).strip(),
            'language': request.form.get('language', current_preferences['language']).strip()
        }
        save_user_preferences_record(db, user_id, updated_preferences)
        db.commit()
        flash("Workspace preferences updated successfully.", "success")
        return redirect(url_for('preferences'))

    return render_template(
        'preferences.html',
        title="My Preferences",
        preferences=current_preferences,
        available_themes=get_available_themes(),
        theme_options=USER_THEME_OPTIONS,
        language_options=USER_LANGUAGE_OPTIONS,
        languages=LANGUAGES,
        font_family_options=USER_FONT_FAMILY_OPTIONS,
        font_size_options=USER_FONT_SIZE_OPTIONS,
        font_weight_options=USER_FONT_WEIGHT_OPTIONS,
        timezone_options=USER_TIMEZONE_OPTIONS,
        date_format_options=USER_DATE_FORMAT_OPTIONS,
        direction_options=USER_DIRECTION_OPTIONS,
        currency_options=USER_CURRENCY_OPTIONS,
        density_options=USER_DENSITY_OPTIONS,
        boolean_options=USER_BOOLEAN_OPTIONS,
        translations=get_translations(current_preferences['language'])
    )


@app.route('/preferences/quick', methods=['POST'])
def quick_preference_update():
    db = get_db()
    user_id = session['user_id']
    current_preferences = get_user_preferences(db, user_id)
    data = request.get_json() or {}
    field = (data.get('field') or '').strip()
    value = data.get('value')

    if field not in USER_PREFERENCE_DEFAULTS:
        return jsonify({'success': False, 'message': 'Unsupported preference field.'}), 400

    current_preferences[field] = value
    saved_preferences = save_user_preferences_record(db, user_id, current_preferences)
    db.commit()
    return jsonify({'success': True, 'message': 'Preference saved.', 'preferences': saved_preferences})


@app.route('/api/theme/switch', methods=['POST'])
def api_switch_theme():
    """API endpoint for live theme switching without page reload."""
    data = request.get_json() or {}
    theme_id = (data.get('theme') or '').strip()

    # Validate theme
    if not validate_theme(theme_id):
        return jsonify({'success': False, 'message': 'Invalid theme.'}), 400

    user_id = session.get('user_id')
    if user_id:
        # Save to database
        db = get_db()
        current_preferences = get_user_preferences(db, user_id)
        current_preferences['theme'] = theme_id
        saved_preferences = save_user_preferences_record(db, user_id, current_preferences)
        db.commit()

        return jsonify({
            'success': True,
            'message': 'Theme saved.',
            'theme': theme_id,
            'is_dark': is_dark_theme(theme_id),
            'chart_palette': get_chart_palette(theme_id)
        })
    else:
        # Not logged in, just return success with localStorage hint
        return jsonify({
            'success': True,
            'message': 'Theme set for session.',
            'theme': theme_id,
            'is_dark': is_dark_theme(theme_id),
            'chart_palette': get_chart_palette(theme_id),
            'save_to_storage': True
        })


@app.route('/api/theme/current', methods=['GET'])
def api_current_theme():
    """Get current theme configuration."""
    user_id = session.get('user_id')
    if user_id:
        prefs = get_user_preferences(user_id)
        theme_id = prefs.get('theme', get_default_theme())
    else:
        theme_id = get_default_theme()

    return jsonify({
        'theme': theme_id,
        'config': get_theme_config(theme_id),
        'is_dark': is_dark_theme(theme_id),
        'chart_palette': get_chart_palette(theme_id),
        'tokens': get_theme_tokens(theme_id)
    })


@app.route('/api/theme/list', methods=['GET'])
def api_list_themes():
    """Get list of all available themes."""
    return jsonify({
        'themes': [
            {
                'id': t['id'],
                'name': t['name'],
                'label': t['label'],
                'description': t['description'],
                'is_dark': t['is_dark'],
                'preview': t.get('preview', {})
            }
            for t in get_available_themes()
        ],
        'default': get_default_theme()
    })


@app.route('/set-language', methods=['POST'])
def set_language():
    """Set the user's language preference and return translations."""
    data = request.get_json() or {}
    lang_code = data.get('language', 'en').strip()

    # Validate language code
    valid_languages = [l['code'] for l in LANGUAGES]
    if lang_code not in valid_languages:
        return jsonify({'success': False, 'message': 'Unsupported language.'}), 400

    user_id = session.get('user_id')
    if user_id:
        db = get_db()
        current_preferences = get_user_preferences(db, user_id)
        current_preferences['language'] = lang_code
        saved_preferences = save_user_preferences_record(db, user_id, current_preferences)
        db.commit()
    else:
        # For non-logged in users, just return translations
        saved_preferences = {'language': lang_code}

    return jsonify({
        'success': True,
        'language': lang_code,
        'direction': get_language_direction(lang_code),
        'translations': get_translations(lang_code),
        'is_rtl': is_rtl(lang_code)
    })


@app.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    db = get_db()
    
    if request.method == 'POST':
        action = request.form.get('action')
        try:
            if action == 'add_category':
                name = request.form.get('category_name', '').strip()
                if name:
                    db.execute("INSERT INTO categories (name) VALUES (?)", (name,))
                    flash("Category added successfully.", "success")
            elif action == 'add_brand':
                name = request.form.get('brand_name', '').strip()
                type_ = request.form.get('brand_type', 'Genuine')
                if name:
                    db.execute("INSERT INTO brands (name, type) VALUES (?, ?)", (name, type_))
                    flash("Brand added successfully.", "success")
            elif action == 'add_status':
                name = request.form.get('status_name', '').strip()
                if name:
                    db.execute("INSERT INTO statuses (name) VALUES (?)", (name,))
                    flash("Status added successfully.", "success")
            elif action == 'add_vitality':
                name = request.form.get('vitality_name', '').strip()
                if name:
                    db.execute("INSERT INTO vitalities (name) VALUES (?)", (name,))
                    flash("Vitality category added successfully.", "success")
            elif action and action.startswith('delete_'):
                table = action.split('_')[1]
                item_id = int(request.form.get('id', 0))
                allowed_tables = {'category': 'categories', 'brand': 'brands', 'status': 'statuses', 'vitality': 'vitalities', 'vehicle': 'vehicles'}
                if table in allowed_tables and item_id:
                    db.execute(f"DELETE FROM {allowed_tables[table]} WHERE id = ?", (item_id,))
                    flash(f"{table.capitalize()} deleted successfully.", "success")
            elif action == 'add_vehicle':
                v_name = request.form.get('vehicle_name', '').strip()
                v_plate = request.form.get('vehicle_plate', '').strip()
                if v_name:
                    db.execute("INSERT INTO vehicles (name, plate_number) VALUES (?, ?)", (v_name, v_plate))
                    flash("Vehicle added successfully.", "success")
            db.commit()
        except Exception as e:
            flash(f"Database Error: {str(e)}", "error")

    categories = db.execute("SELECT * FROM categories ORDER BY name").fetchall()
    brands = db.execute("SELECT * FROM brands ORDER BY name").fetchall()
    statuses = db.execute("SELECT * FROM statuses ORDER BY name").fetchall()
    vitalities = db.execute("SELECT * FROM vitalities ORDER BY name").fetchall()
    companies = db.execute("SELECT * FROM companies ORDER BY name").fetchall()
    vehicles = db.execute("SELECT * FROM vehicles ORDER BY name").fetchall()
    
    return render_template('settings.html', title="System Settings", categories=categories, brands=brands, statuses=statuses, vitalities=vitalities, companies=companies, vehicles=vehicles)

@app.route('/parts_settings', methods=['GET', 'POST'])
@admin_required
def parts_settings():
    db = get_db()

    # Auto-sync with Peyvast on every page load (GET requests)
    if request.method == 'GET':
        try:
            sync_manager = PeyvastSyncManager()
            sync_manager.ensure_sync_schema()
            sync_manager.sync_all()
        except Exception as e:
            pass  # Silent fail, show existing data

    if request.method == 'POST':
        action = request.form.get('action')
        part_id = request.form.get('part_id')
        
        if action == 'update_part' and part_id:
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            notes = request.form.get('notes', '').strip()
            fitted_vehicle = request.form.get('fitted_vehicle', '').strip()
            brand_id = request.form.get('brand_id') or None
            vitality_id = request.form.get('vitality_id') or None
            weight = request.form.get('weight', 0, type=float)
            length = request.form.get('length', 0, type=float)
            width = request.form.get('width', 0, type=float)
            height = request.form.get('height', 0, type=float)
            reorder_point = request.form.get('reorder_point', 0, type=int)
            cost_price = request.form.get('cost_price', 0, type=float)
            hs_code = request.form.get('hs_code', '').strip()
            
            db.execute("""
                UPDATE parts SET name = ?, description = ?, notes = ?, fitted_vehicle = ?,
                       brand_id = ?, vitality_id = ?, weight = ?, length = ?, width = ?, height = ?,
                       reorder_point = ?, cost_price = ?, hs_code = ?
                WHERE id = ?
            """, (name, description, notes, fitted_vehicle, brand_id, vitality_id, weight, length, width, height, reorder_point, cost_price, hs_code, part_id))
            db.commit()
            flash("Part updated successfully.", "success")
        elif action == 'clear_hs_code' and part_id:
            db.execute("UPDATE parts SET hs_code = NULL WHERE id = ?", (part_id,))
            db.commit()
            flash("HS Code removed successfully.", "success")
        elif action == 'delete_part' and part_id:
            part = db.execute("SELECT part_number FROM parts WHERE id = ?", (part_id,)).fetchone()
            if part:
                db.execute("DELETE FROM parts WHERE id = ?", (part_id,))
                db.commit()
                flash(f"Part number '{part['part_number']}' removed successfully.", "success")
            else:
                flash("Part not found.", "error")
            
    parts = db.execute("""
        SELECT p.*, b.name as brand_name, cat.name as category_name, v.name as vitality_name
        FROM parts p
        LEFT JOIN brands b ON p.brand_id = b.id
        LEFT JOIN categories cat ON p.category_id = cat.id
        LEFT JOIN vitalities v ON p.vitality_id = v.id
        ORDER BY p.part_number
    """).fetchall()
    
    brands = db.execute("SELECT * FROM brands ORDER BY name").fetchall()
    vitalities = db.execute("SELECT * FROM vitalities ORDER BY name").fetchall()
    
    # Get inventory per warehouse for each part
    inventory_map = {}
    inv_rows = db.execute("""
        SELECT i.part_id, c.name as company_name, i.quantity
        FROM inventory i
        JOIN companies c ON i.company_id = c.id
        WHERE c.name != 'Holding Company'
        ORDER BY c.name
    """).fetchall()
    for row in inv_rows:
        pid = row['part_id']
        if pid not in inventory_map:
            inventory_map[pid] = []
        inventory_map[pid].append({'warehouse': row['company_name'], 'qty': row['quantity']})
    
    return render_template('parts_settings.html', title="Part Attributes", parts=parts, brands=brands, vitalities=vitalities, inventory_map=inventory_map)

@app.route('/parts_template')
@admin_required
def parts_template():
    """Download a pre-formatted Excel template for bulk part import."""
    wb = Workbook()
    ws = wb.active
    ws.title = 'Parts Import'
    headers = ['Part Number', 'Name', 'Description', 'Brand', 'Fitted Vehicle', 'Notes', 'Cost Price (AED)', 'Weight (kg)', 'Length (cm)', 'Width (cm)', 'Height (cm)', 'Reorder Point']
    ws.append(headers)
    # Example row
    ws.append(['OEM-00001-A', 'Front Brake Disc', 'Premium ceramic brake disc', 'Bosch', 'Toyota Camry 2023', 'Fragile - handle with care', 125.50, 1.20, 30.00, 30.00, 5.00, 10])
    
    # Style header
    from openpyxl.styles import Font, PatternFill
    for cell in ws[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(start_color='0EA5E9', end_color='0EA5E9', fill_type='solid')
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 20
    
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return Response(
        buf.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={'Content-Disposition': 'attachment; filename=Parts_Import_Template.xlsx'}
    )

@app.route('/parts_import', methods=['POST'])
@admin_required
def parts_import():
    """Import parts from an uploaded Excel file."""
    file = request.files.get('file')
    if not file or not file.filename.endswith(('.xlsx', '.xls')):
        flash('Please upload a valid Excel file (.xlsx).', 'error')
        return redirect(url_for('parts_settings'))
    
    db = get_db()
    try:
        wb = load_workbook(file)
        ws = wb.active
        rows = list(ws.iter_rows(min_row=2, values_only=True))
        updated: int = 0
        created: int = 0
        
        # Get brand name -> id map
        brand_map = {}
        for b in db.execute('SELECT id, name FROM brands').fetchall():
            brand_map[b['name'].lower()] = b['id']
        
        for row in rows:
            if not row or not row[0]:
                continue
            part_number = str(row[0]).strip()
            name = str(row[1] or '').strip()
            description = str(row[2] or '').strip()
            brand_name = str(row[3] or '').strip()
            fitted_vehicle = str(row[4] or '').strip()
            notes = str(row[5] or '').strip()
            cost_price = float(row[6] or 0)
            weight = float(row[7] or 0)
            length = float(row[8] or 0)
            width = float(row[9] or 0)
            height = float(row[10] or 0)
            reorder_point = int(row[11] or 0)
            
            brand_id = brand_map.get(brand_name.lower())
            
            existing = db.execute('SELECT id FROM parts WHERE part_number = ?', (part_number,)).fetchone()
            if existing:
                db.execute("""
                    UPDATE parts SET name=?, description=?, fitted_vehicle=?, notes=?,
                           brand_id=?, cost_price=?, weight=?, length=?, width=?, height=?, reorder_point=?
                    WHERE id=?
                """, (name, description, fitted_vehicle, notes, brand_id, cost_price, weight, length, width, height, reorder_point, existing['id']))
                updated = int(updated + 1)
            else:
                db.execute("""
                    INSERT INTO parts (part_number, name, description, fitted_vehicle, notes, brand_id, cost_price, weight, length, width, height, reorder_point)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (part_number, name, description, fitted_vehicle, notes, brand_id, cost_price, weight, length, width, height, reorder_point))
                created = int(created + 1)
        
        db.commit()
        flash(f'Import complete: {created} created, {updated} updated.', 'success')
    except Exception as e:
        flash(f'Import failed: {str(e)}', 'error')
    
    return redirect(url_for('parts_settings'))

@app.route('/api/parts/bulk_delete', methods=['POST'])
@admin_required
def parts_bulk_delete():
    db = get_db()
    part_ids = request.form.getlist('ids[]')
    if not part_ids:
        return jsonify({"status": "error", "msg": "No parts selected"}), 400
    
    try:
        placeholders = ','.join('?' for _ in part_ids)
        db.execute(f"DELETE FROM parts WHERE id IN ({placeholders})", part_ids)
        db.commit()
        return jsonify({"status": "success", "msg": f"Successfully removed {len(part_ids)} parts"})
    except Exception as e:
        return jsonify({"status": "error", "msg": str(e)}), 500

@app.route('/api/parts/export_excel')
@admin_required
def parts_export_excel():
    db = get_db()
    parts = db.execute("""
        SELECT p.part_number, p.name, p.description, b.name as brand, p.fitted_vehicle, 
               p.notes, p.cost_price, p.weight, p.length, p.width, p.height, p.reorder_point, p.hs_code
        FROM parts p
        LEFT JOIN brands b ON p.brand_id = b.id
        ORDER BY p.part_number
    """).fetchall()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Parts Inventory"
    
    headers = ['Part Number', 'Name', 'Description', 'Brand', 'Fitted Vehicle', 'Notes', 'Cost Price (AED)', 'Weight (kg)', 'Length (cm)', 'Width (cm)', 'Height (cm)', 'Reorder Point', 'HS Code']
    ws.append(headers)
    
    for p in parts:
        ws.append(list(p))
        
    for cell in ws[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(start_color='0EA5E9', end_color='0EA5E9', fill_type='solid')
        
    for col in ws.columns:
        ws.column_dimensions[col[0].column_letter].width = 18

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    
    return Response(
        buf.getvalue(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=Parts_Export_{datetime.now().strftime('%Y%m%d')}.xlsx"}
    )

@app.route('/admin/warehouses', methods=['GET', 'POST'])
@admin_required
def admin_warehouses():
    db = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            name = request.form.get('name', '').strip()
            company_id = request.form.get('company_id')
            if name and company_id:
                try:
                    db.execute("INSERT INTO warehouses (name, company_id) VALUES (?, ?)", (name, company_id))
                    db.commit()
                    flash(f"Warehouse '{name}' added successfully.", "success")
                except sqlite3.Error as e:
                    flash(f"Error adding warehouse: {e}", "error")
            else:
                flash("Name and Company are required.", "error")
        elif action == 'edit':
            w_id = request.form.get('warehouse_id')
            name = request.form.get('name', '').strip()
            company_id = request.form.get('company_id')
            if w_id and name and company_id:
                try:
                    db.execute("UPDATE warehouses SET name = ?, company_id = ? WHERE id = ?", (name, company_id, w_id))
                    db.commit()
                    flash("Warehouse updated.", "success")
                except sqlite3.Error as e:
                    flash(f"Error updating warehouse: {e}", "error")
        elif action == 'delete':
            w_id = request.form.get('warehouse_id')
            inv = db.execute("SELECT id FROM inventory WHERE warehouse_id = ?", (w_id,)).fetchone()
            if inv:
                flash("Cannot delete warehouse. It has active inventory.", "error")
            else:
                db.execute("DELETE FROM warehouses WHERE id = ?", (w_id,))
                db.commit()
                flash("Warehouse removed.", "success")
        return redirect(url_for('admin_warehouses'))
        
    warehouses = db.execute('''
        SELECT w.*, c.name as company_name 
        FROM warehouses w 
        JOIN companies c ON w.company_id = c.id 
        ORDER BY c.name, w.name
    ''').fetchall()
    companies = db.execute("SELECT id, name FROM companies WHERE name != 'Holding Company' ORDER BY name").fetchall()
    
    return render_template('admin_warehouses.html', title="Warehouse Settings", warehouses=warehouses, companies=companies)

@app.route('/location_settings', methods=['GET', 'POST'])
@admin_required
def location_settings():
    db = get_db()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_location':
            rack = request.form.get('rack', '').strip()
            bay = request.form.get('bay', '').strip()
            level = request.form.get('level', '').strip()
            position = request.form.get('position', '').strip()
            bin_val = request.form.get('bin', '').strip()
            max_oil = request.form.get('max_oil_capacity', 0, type=float)
            max_wt = request.form.get('max_weight', 0, type=float)
            comp_id = request.form.get('company_id')
            
            code = f"{rack}-{bay}-{level}-{position}-{bin_val}"
            if rack and bay and level and position and bin_val:
                try:
                    db.execute("""
                        INSERT INTO locations (location_code, rack, bay, level, position, bin, max_oil_capacity, max_weight, company_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (code, rack, bay, level, position, bin_val, max_oil, max_wt, comp_id))
                    db.commit()
                    flash("Location registered successfully.", "success")
                except sqlite3.IntegrityError:
                    flash("This location code already exists.", "error")
            else:
                flash("All 5 coordinate fields are required.", "error")
        
        elif action == 'update_location':
            loc_id = request.form.get('id')
            max_oil = request.form.get('max_oil_capacity', 0, type=float)
            max_wt = request.form.get('max_weight', 0, type=float)
            comp_id = request.form.get('company_id')
            if loc_id:
                db.execute("UPDATE locations SET max_oil_capacity = ?, max_weight = ?, company_id = ? WHERE id = ?", (max_oil, max_wt, comp_id, loc_id))
                db.commit()
                flash("Location updated.", "success")
                
        elif action == 'delete_location':
            loc_id = request.form.get('id')
            if loc_id:
                db.execute("DELETE FROM locations WHERE id = ?", (loc_id,))
                db.commit()
                flash("Location deleted.", "success")

    locations = [dict(row) for row in db.execute('''
        SELECT l.*, c.name as company_name 
        FROM locations l 
        LEFT JOIN companies c ON l.company_id = c.id
        ORDER BY l.rack, l.bay, l.bin
    ''').fetchall()]
    
    companies = [dict(row) for row in db.execute("SELECT * FROM companies ORDER BY name").fetchall()]
    
    return render_template('location_settings.html', title="Location Infrastructure", 
                           locations=locations, companies=companies)

@app.route('/locations/export')
@admin_required
def export_locations():
    db = get_db()
    locations = db.execute("""
        SELECT l.location_code, l.rack, l.bay, l.level, l.position, l.bin, l.max_oil_capacity, l.max_weight, c.name as company_name
        FROM locations l 
        LEFT JOIN companies c ON l.company_id = c.id
        ORDER BY l.location_code
    """).fetchall()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Warehouse Locations"
    
    # Header
    headers = ["#", "Location Code", "Rack", "Bay", "Level", "Position", "Bin", "Max Oil (L)", "Max Weight (KG)", "Assigned Company"]
    ws.append(headers)
    
    for idx, loc in enumerate(locations, 1):
        ws.append([
            idx,
            loc['location_code'],
            loc['rack'],
            loc['bay'],
            loc['level'],
            loc['position'],
            loc['bin'],
            loc['max_oil_capacity'],
            loc['max_weight'],
            loc['company_name'] or 'Unassigned'
        ])
    
    # Styling
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4F46E5", end_color="4F46E5", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
        
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return Response(
        output.read(),
        headers={"Content-Disposition": "attachment; filename=warehouse_locations.xlsx"},
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route('/users', methods=['GET', 'POST'])
@admin_required
def users():
    db = get_db()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add_user':
            username = request.form.get('username', '').strip()
            email = request.form.get('email', '').strip()
            role_id = request.form.get('role_id')
            password = request.form.get('password')
            
            if username and email and role_id and password:
                try:
                    hash_pw = generate_password_hash(password)
                    db.execute("INSERT INTO users (username, email, password, role_id) VALUES (?, ?, ?, ?)", 
                               (username, email, hash_pw, role_id))
                    db.commit()
                    flash("User created successfully.", "success")
                except sqlite3.IntegrityError:
                    flash("Error creating user. Username/Email may already exist.", "error")
                    
        elif action == 'delete_user':
            item_id = int(request.form.get('user_id', 0))
            if item_id == session['user_id']:
                flash("You cannot delete your own account.", "error")
            else:
                db.execute("DELETE FROM users WHERE id = ?", (item_id,))
                db.commit()
                flash("User deleted.", "success")
                
        elif action == 'add_role':
            role_name = request.form.get('role_name', '').strip()
            company_id = request.form.get('company_id')
            company_id = int(company_id) if company_id else None
            
            # Extract granular permissions
            can_edit = 1 if 'can_edit_stock' in request.form else 0
            can_reports = 1 if 'can_view_reports' in request.form else 0
            can_val = 1 if 'can_view_valuation' in request.form else 0
            can_parts = 1 if 'can_manage_parts' in request.form else 0
            can_locs = 1 if 'can_manage_locations' in request.form else 0
            can_tax = 1 if 'can_manage_taxonomies' in request.form else 0
            can_users = 1 if 'can_manage_users' in request.form else 0
            
            if role_name:
                db.execute("""
                    INSERT INTO roles (
                        role_name, company_id, can_edit_stock, can_manage_users, 
                        can_view_reports, can_view_valuation, can_manage_parts, 
                        can_manage_locations, can_manage_taxonomies
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (role_name, company_id, can_edit, can_users, can_reports, can_val, can_parts, can_locs, can_tax))
                db.commit()
                flash("Advanced Role created successfully.", "success")
        
        elif action == 'update_user_role':
            user_id = int(request.form.get('user_id', 0))
            new_role_id = request.form.get('role_id')
            if user_id and new_role_id:
                db.execute("UPDATE users SET role_id = ? WHERE id = ?", (new_role_id, user_id))
                db.commit()
                flash("User role assigned successfully.", "success")
        
        elif action == 'update_role_definition':
            role_id = int(request.form.get('role_id', 0))
            role_name = request.form.get('role_name', '').strip()
            company_id = request.form.get('company_id') if request.form.get('company_id') else None
            
            can_edit = 1 if 'can_edit_stock' in request.form else 0
            can_parts = 1 if 'can_manage_parts' in request.form else 0
            can_reports = 1 if 'can_view_reports' in request.form else 0
            can_val = 1 if 'can_view_valuation' in request.form else 0
            can_locs = 1 if 'can_manage_locations' in request.form else 0
            can_tax = 1 if 'can_manage_taxonomies' in request.form else 0
            can_users = 1 if 'can_manage_users' in request.form else 0
            
            if role_id and role_name:
                db.execute("""
                    UPDATE roles SET 
                        role_name = ?, company_id = ?, can_edit_stock = ?, can_manage_users = ?, 
                        can_view_reports = ?, can_view_valuation = ?, can_manage_parts = ?, 
                        can_manage_locations = ?, can_manage_taxonomies = ?
                    WHERE id = ?
                """, (role_name, company_id, can_edit, can_users, can_reports, can_val, can_parts, can_locs, can_tax, role_id))
                db.commit()
                flash("Role definition updated.", "success")

        elif action == 'delete_role':
            role_id = int(request.form.get('role_id', 0))
            # Check if role is in use
            count = db.execute("SELECT COUNT(*) as c FROM users WHERE role_id = ?", (role_id,)).fetchone()['c']
            if count > 0:
                flash(f"Cannot delete role. It is currently assigned to {count} users.", "error")
            else:
                db.execute("DELETE FROM roles WHERE id = ?", (role_id,))
                db.commit()
                flash("Role deleted successfully.", "success")
        
        elif action == 'reset_password':
            user_id = int(request.form.get('user_id', 0))
            new_pw = request.form.get('new_password', '').strip()
            if user_id and new_pw:
                db.execute("UPDATE users SET password = ? WHERE id = ?", (generate_password_hash(new_pw), user_id))
                db.commit()
                flash("Password reset successfully.", "success")

    users_list = [dict(row) for row in db.execute('''
        SELECT u.id, u.username, u.email, u.profile_pic, u.role_id, u.created_at, r.role_name, c.name as company_name 
        FROM users u 
        JOIN roles r ON u.role_id = r.id 
        LEFT JOIN companies c ON r.company_id = c.id
        ORDER BY u.created_at DESC
    ''').fetchall()]
    
    roles_list = [dict(row) for row in db.execute('''
        SELECT r.*, c.name as company_name 
        FROM roles r 
        LEFT JOIN companies c ON r.company_id = c.id 
        ORDER BY r.role_name
    ''').fetchall()]
    
    companies = [dict(row) for row in db.execute("SELECT * FROM companies ORDER BY name").fetchall()]
    
    return render_template('users.html', title="User Management", users=users_list, roles=roles_list, companies=companies)


@app.route('/tasks')
def task_manager():
    db = get_db()
    base_sql, params, filters = build_task_base_query(request.args)
    sort_expr = get_task_sort_expression(filters['sort_by'])
    sort_dir = filters['sort_dir'].upper()

    page = max(request.args.get('page', 1, type=int), 1)
    per_page = 50
    total_tasks = db.execute(f"SELECT COUNT(*) {base_sql}", params).fetchone()[0]
    total_pages = max((total_tasks + per_page - 1) // per_page, 1) if total_tasks else 1
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * per_page

    task_rows = db.execute(
        f'''
        SELECT t.*, c.name AS company_name, d.name AS department_name,
               r.username AS report_to_name, a.username AS assigned_to_name,
               creator.username AS created_by_name,
               (SELECT COUNT(*) FROM task_subtasks WHERE parent_task_id = t.id) AS subtask_count
        {base_sql}
        ORDER BY {sort_expr} {sort_dir}, t.id DESC
        LIMIT ? OFFSET ?
        ''',
        params + [per_page, offset]
    ).fetchall()
    now_value = datetime.now()
    tasks = [prepare_task_for_view(dict(row), now_value) for row in task_rows]

    stats_row = db.execute(
        f'''
        SELECT
            COUNT(*) AS total_tasks,
            SUM(CASE WHEN t.status = 'Completed' THEN 1 ELSE 0 END) AS completed_tasks,
            SUM(CASE WHEN t.status = 'Canceled' THEN 1 ELSE 0 END) AS canceled_tasks,
            SUM(CASE WHEN t.is_archived = 1 THEN 1 ELSE 0 END) AS archived_tasks,
            AVG(COALESCE(t.progress, 0)) AS average_progress,
            SUM(
                CASE
                    WHEN t.is_archived = 0
                     AND COALESCE(t.status, '') != 'Completed'
                     AND COALESCE(t.due_at, '') != ''
                     AND t.due_at < datetime('now')
                    THEN 1 ELSE 0
                END
            ) AS overdue_tasks
        {base_sql}
        ''',
        params
    ).fetchone()
    stats = dict(stats_row)

    status_breakdown = [
        dict(row) for row in db.execute(
            f'''
            SELECT COALESCE(t.status, 'Open') AS label, COUNT(*) AS total
            {base_sql}
            GROUP BY COALESCE(t.status, 'Open')
            ORDER BY total DESC, label ASC
            ''',
            params
        ).fetchall()
    ]
    department_breakdown = [
        dict(row) for row in db.execute(
            f'''
            SELECT COALESCE(d.name, 'Unassigned') AS label, COUNT(*) AS total
            {base_sql}
            GROUP BY COALESCE(d.name, 'Unassigned')
            ORDER BY total DESC, label ASC
            LIMIT 8
            ''',
            params
        ).fetchall()
    ]
    company_breakdown = [
        dict(row) for row in db.execute(
            f'''
            SELECT COALESCE(c.name, 'Unassigned') AS label, COUNT(*) AS total
            {base_sql}
            GROUP BY COALESCE(c.name, 'Unassigned')
            ORDER BY total DESC, label ASC
            LIMIT 8
            ''',
            params
        ).fetchall()
    ]
    future_task_rows = db.execute(
        f'''
        SELECT t.*, c.name AS company_name, d.name AS department_name,
               r.username AS report_to_name, a.username AS assigned_to_name,
               creator.username AS created_by_name
        {base_sql}
        ORDER BY
            CASE WHEN COALESCE(t.due_at, '') = '' THEN 1 ELSE 0 END,
            COALESCE(t.due_at, ''),
            t.id DESC
        ''',
        params
    ).fetchall()
    future_tasks = []
    for row in future_task_rows:
        candidate = prepare_task_for_view(dict(row), now_value)
        if candidate.get('is_future_task'):
            future_tasks.append(candidate)
    stats['future_tasks'] = len(future_tasks)
    stats['future_missing_time'] = sum(1 for task in future_tasks if task.get('is_future_without_time'))

    history_query = '''
        SELECT h.*, actor.username AS actor_name
        FROM task_history h
        LEFT JOIN users actor ON h.actor_user_id = actor.id
        LEFT JOIN task_items t ON h.task_id = t.id
        WHERE 1=1
    '''
    history_params = []
    if not user_can_manage_all_tasks():
        history_scope, history_scope_params = get_task_scope_clause('t')
        history_query += history_scope
        history_params.extend(history_scope_params)
    history_query += ' ORDER BY h.created_at DESC LIMIT 40'
    history_rows = db.execute(history_query, history_params).fetchall()
    task_history = [dict(row) for row in history_rows]

    companies = [dict(row) for row in db.execute("SELECT id, name FROM companies ORDER BY name").fetchall()]
    departments = [dict(row) for row in db.execute(
        "SELECT * FROM task_departments WHERE status = 'Active' ORDER BY name"
    ).fetchall()]
    task_users_query = '''
        SELECT u.id, u.username, r.role_name, c.name AS company_name
        FROM users u
        JOIN roles r ON u.role_id = r.id
        LEFT JOIN companies c ON r.company_id = c.id
    '''
    task_users_params = []
    if not user_can_manage_all_tasks() and session.get('company_id'):
        task_users_query += ' WHERE r.company_id = ? OR r.company_id IS NULL'
        task_users_params.append(session.get('company_id'))
    task_users_query += ' ORDER BY u.username'
    task_users = [dict(row) for row in db.execute(task_users_query, task_users_params).fetchall()]

    page_start = offset + 1 if total_tasks else 0
    page_end = offset + len(tasks)
    page_window = list(range(max(1, page - 2), min(total_pages, page + 2) + 1))
    visible_task_columns = get_task_visible_columns(db)

    return render_template(
        'tasks.html',
        title="Task Command Center",
        tasks=tasks,
        stats=stats,
        filters=filters,
        companies=companies,
        departments=departments,
        task_users=task_users,
        task_history=task_history,
        status_breakdown=status_breakdown,
        department_breakdown=department_breakdown,
        company_breakdown=company_breakdown,
        future_tasks=future_tasks,
        task_column_options=TASK_COLUMN_OPTIONS,
        task_column_keys=TASK_COLUMN_KEYS,
        visible_task_columns=visible_task_columns,
        task_priorities=TASK_PRIORITIES,
        task_statuses=TASK_STATUSES,
        total_tasks=total_tasks,
        page=page,
        total_pages=total_pages,
        page_window=page_window,
        page_start=page_start,
        page_end=page_end,
        per_page=per_page,
        now_value=datetime.now().strftime('%Y-%m-%dT%H:%M')
    )


@app.route('/tasks/export')
def export_tasks():
    db = get_db()
    base_sql, params, filters = build_task_base_query(request.args)
    sort_expr = get_task_sort_expression(filters['sort_by'])
    sort_dir = filters['sort_dir'].upper()
    rows = db.execute(
        f'''
        SELECT
            t.id AS "#",
            COALESCE(c.name, 'Unassigned') AS "Company",
            COALESCE(d.name, 'Unassigned') AS "Department",
            t.task_name AS "Task",
            COALESCE(a.username, 'Unassigned') AS "Assigned To",
            COALESCE(r.username, 'Unassigned') AS "Report To",
            t.priority AS "Priority",
            t.progress AS "Progress %",
            t.status AS "Status",
            COALESCE(t.description, '') AS "Desc",
            COALESCE(t.latest_note, '') AS "Add desc",
            COALESCE(t.due_at, '') AS "Time",
            CASE WHEN t.is_archived = 1 THEN 'Archived' ELSE 'Active' END AS "Lifecycle",
            COALESCE(t.created_at, '') AS "Created At",
            COALESCE(t.updated_at, '') AS "Updated At"
        {base_sql}
        ORDER BY {sort_expr} {sort_dir}, t.id DESC
        ''',
        params
    ).fetchall()
    df = pd.DataFrame([dict(row) for row in rows])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Tasks')
    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name=f"task_command_center_{datetime.now().strftime('%Y%m%d')}.xlsx"
    )


@app.route('/tasks/save', methods=['POST'])
def save_task():
    db = get_db()
    data = request.get_json() or {}
    task_id = parse_optional_int(data.get('task_id'))
    company_id = parse_optional_int(data.get('company_id'))
    department_id = parse_optional_int(data.get('department_id'))
    report_to_user_id = parse_optional_int(data.get('report_to_user_id'))
    assigned_to_user_id = parse_optional_int(data.get('assigned_to_user_id'))
    task_name = (data.get('task_name') or '').strip()
    description = (data.get('description') or '').strip()
    latest_note = (data.get('latest_note') or '').strip()
    due_at = (data.get('due_at') or '').strip() or None
    priority = normalize_task_priority(data.get('priority'))
    status = normalize_task_status(data.get('status'))
    progress = clamp_progress(data.get('progress'))
    reminder_days = max(0, int(data.get('reminder_days', 0) or 0))
    reminder_hours = max(0, int(data.get('reminder_hours', 0) or 0))

    if not task_name or not company_id or not department_id:
        return jsonify({'success': False, 'message': 'Company, department, and task title are required.'}), 400

    if status == 'Completed':
        progress = 100
    elif progress == 100 and status != 'Completed':
        status = 'Completed'

    source_row = None
    source_report_to = ''
    raw_status_label = ''
    if task_id:
        existing_task = fetch_task_record(db, task_id)
        if not existing_task:
            return jsonify({'success': False, 'message': 'Task not found or access denied.'}), 404
        existing_task_meta = annotate_task_note_metadata(dict(existing_task))
        source_row = existing_task_meta.get('source_row')
        source_report_to = existing_task_meta.get('source_report_to', '')
        raw_status_label = existing_task_meta.get('raw_status_label', '')
    latest_note_value = compose_task_latest_note(
        latest_note,
        source_row=source_row,
        source_report_to=source_report_to,
        raw_status=raw_status_label
    )

    payload = {
        'company_id': company_id,
        'department_id': department_id,
        'task_name': task_name,
        'priority': priority,
        'report_to_user_id': report_to_user_id,
        'assigned_to_user_id': assigned_to_user_id,
        'progress': progress,
        'status': status,
        'description': description,
        'latest_note': latest_note_value,
        'due_at': due_at,
        'reminder_days': reminder_days,
        'reminder_hours': reminder_hours
    }

    if task_id:
        changed_fields = []
        for field_name, new_value in payload.items():
            old_value = existing_task[field_name]
            if (old_value or '') != (new_value or ''):
                changed_fields.append((field_name, old_value, new_value))

        db.execute(
            '''
            UPDATE task_items
            SET company_id = ?, department_id = ?, task_name = ?, priority = ?,
                report_to_user_id = ?, assigned_to_user_id = ?, progress = ?, status = ?,
                description = ?, latest_note = ?, due_at = ?, reminder_days = ?, reminder_hours = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''',
            (
                payload['company_id'], payload['department_id'], payload['task_name'], payload['priority'],
                payload['report_to_user_id'], payload['assigned_to_user_id'], payload['progress'], payload['status'],
                payload['description'], payload['latest_note'], payload['due_at'],
                payload['reminder_days'], payload['reminder_hours'], task_id
            )
        )
        for field_name, old_value, new_value in changed_fields:
            log_task_history(
                db, task_id, payload['task_name'], 'updated',
                field_name=field_name, old_value=old_value, new_value=new_value
            )
        if latest_note_value:
            log_task_history(
                db, task_id, payload['task_name'], 'note',
                field_name='latest_note', new_value=latest_note_value, note=latest_note
            )
        db.commit()
        return jsonify({'success': True, 'message': 'Task updated successfully.'})

    cursor = db.execute(
        '''
        INSERT INTO task_items (
            company_id, department_id, task_name, priority, report_to_user_id,
            assigned_to_user_id, progress, status, description, latest_note,
            due_at, reminder_days, reminder_hours, created_by_user_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            payload['company_id'], payload['department_id'], payload['task_name'], payload['priority'],
            payload['report_to_user_id'], payload['assigned_to_user_id'], payload['progress'],
            payload['status'], payload['description'], payload['latest_note'], payload['due_at'],
            payload['reminder_days'], payload['reminder_hours'], session.get('user_id')
        )
    )
    new_task_id = cursor.lastrowid
    log_task_history(db, new_task_id, payload['task_name'], 'created', note=payload['description'])
    if latest_note_value:
        log_task_history(
            db, new_task_id, payload['task_name'], 'note',
            field_name='latest_note', new_value=latest_note_value, note=latest_note
        )
    db.commit()
    return jsonify({'success': True, 'message': 'Task created successfully.'})


@app.route('/tasks/bulk_action', methods=['POST'])
def task_bulk_action():
    db = get_db()
    data = request.get_json() or {}
    action = (data.get('action') or '').strip().lower()
    task_ids = [parse_optional_int(task_id) for task_id in data.get('task_ids', [])]
    task_ids = [task_id for task_id in task_ids if task_id]
    target_status = normalize_task_status(data.get('status'))

    if not task_ids:
        return jsonify({'success': False, 'message': 'No tasks were selected.'}), 400

    if action in ('delete', 'remove') and not user_can_manage_all_tasks():
        return jsonify({'success': False, 'message': 'Only administrators can delete tasks.'}), 403

    affected = 0
    for task_id in task_ids:
        task = fetch_task_record(db, task_id)
        if not task:
            continue

        if action == 'archive':
            if task['is_archived']:
                continue
            db.execute(
                "UPDATE task_items SET is_archived = 1, archived_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (task_id,)
            )
            log_task_history(db, task_id, task['task_name'], 'archived')
            affected += 1
        elif action == 'unarchive':
            db.execute(
                "UPDATE task_items SET is_archived = 0, archived_at = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (task_id,)
            )
            log_task_history(db, task_id, task['task_name'], 'unarchived')
            affected += 1
        elif action == 'status':
            progress = 100 if target_status in ('Completed', 'Canceled') else task['progress']
            # Archive task when marked as Completed or Canceled
            if target_status in ('Completed', 'Canceled') and not task['is_archived']:
                db.execute(
                    "UPDATE task_items SET status = ?, progress = ?, is_archived = 1, archived_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (target_status, progress, task_id)
                )
                log_task_history(db, task_id, task['task_name'], 'archived')
            else:
                db.execute(
                    "UPDATE task_items SET status = ?, progress = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (target_status, progress, task_id)
                )
                log_task_history(
                    db, task_id, task['task_name'], 'status_changed',
                    field_name='status', old_value=task['status'], new_value=target_status
                )
            affected += 1
        elif action in ('delete', 'remove'):
            log_task_history(db, task_id, task['task_name'], 'deleted', note='Task removed from active register')
            db.execute("DELETE FROM task_items WHERE id = ?", (task_id,))
            affected += 1

    db.commit()
    return jsonify({'success': True, 'message': f'{affected} task(s) updated.', 'affected': affected})


@app.route('/tasks/toggle_complete', methods=['POST'])
def toggle_task_complete():
    """Toggle task completion (set to Completed or back to In Progress)"""
    db = get_db()
    data = request.get_json() or {}
    task_id = parse_optional_int(data.get('task_id'))

    if not task_id:
        return jsonify({'success': False, 'message': 'Task ID is required'}), 400

    task = fetch_task_record(db, task_id)
    if not task:
        return jsonify({'success': False, 'message': 'Task not found'}), 404

    current_status = task['status']
    if current_status == 'Completed' or current_status == 'Canceled':
        new_status = 'In Progress'
        new_progress = task['progress'] if task['progress'] < 100 else 80
    else:
        new_status = 'Completed'
        new_progress = 100

    # Archive task when marked as Completed or Canceled
    if new_status == 'Completed' and not task['is_archived']:
        db.execute(
            "UPDATE task_items SET status = ?, progress = ?, is_archived = 1, archived_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_status, new_progress, task_id)
        )
        log_task_history(db, task_id, task['task_name'], 'archived')
    else:
        db.execute(
            "UPDATE task_items SET status = ?, progress = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (new_status, new_progress, task_id)
        )
        log_task_history(db, task_id, task['task_name'], 'status_changed',
                         field_name='status', old_value=current_status, new_value=new_status)
    db.commit()
    return jsonify({'success': True, 'status': new_status, 'progress': new_progress})


@app.route('/tasks/delete', methods=['POST'])
def delete_task_item():
    """Delete a task and its subtasks"""
    if not user_can_manage_all_tasks():
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    db = get_db()
    data = request.get_json() or {}
    task_id = parse_optional_int(data.get('task_id'))

    if not task_id:
        return jsonify({'success': False, 'message': 'Task ID is required'}), 400

    task = fetch_task_record(db, task_id)
    if not task:
        return jsonify({'success': False, 'message': 'Task not found'}), 404

    log_task_history(db, task_id, task['task_name'], 'deleted', note='Task removed')
    db.execute("DELETE FROM task_subtasks WHERE parent_task_id = ?", (task_id,))
    db.execute("DELETE FROM task_items WHERE id = ?", (task_id,))
    db.commit()
    return jsonify({'success': True, 'message': 'Task deleted'})


@app.route('/tasks/note', methods=['POST'])
def add_task_note():
    db = get_db()
    data = request.get_json() or {}
    task_id = parse_optional_int(data.get('task_id'))
    note = (data.get('note') or '').strip()
    progress = data.get('progress')
    status_value = data.get('status')

    if not task_id or not note:
        return jsonify({'success': False, 'message': 'Task and note are required.'}), 400

    task = fetch_task_record(db, task_id)
    if not task:
        return jsonify({'success': False, 'message': 'Task not found or access denied.'}), 404
    task_meta = annotate_task_note_metadata(dict(task))

    new_progress = clamp_progress(progress if progress is not None else task['progress'])
    new_status = normalize_task_status(status_value if status_value is not None else task['status'])
    if new_status in ('Completed', 'Canceled'):
        new_progress = 100
    new_latest_note = compose_task_latest_note(
        note,
        source_row=task_meta.get('source_row'),
        source_report_to=task_meta.get('source_report_to', ''),
        raw_status=task_meta.get('raw_status_label', '')
    )

    # Archive task when marked as Completed or Canceled
    if new_status in ('Completed', 'Canceled') and not task['is_archived']:
        db.execute(
            '''
            UPDATE task_items
            SET latest_note = ?, progress = ?, status = ?, is_archived = 1, archived_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''',
            (new_latest_note, new_progress, new_status, task_id)
        )
        log_task_history(db, task_id, task['task_name'], 'archived')
    else:
        db.execute(
            '''
            UPDATE task_items
            SET latest_note = ?, progress = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''',
            (new_latest_note, new_progress, new_status, task_id)
        )
    log_task_history(
        db, task_id, task['task_name'], 'note',
        field_name='latest_note', old_value=task['latest_note'],
        new_value=new_latest_note, note=note
    )
    if new_progress != task['progress']:
        log_task_history(
            db, task_id, task['task_name'], 'progress_changed',
            field_name='progress', old_value=task['progress'], new_value=new_progress
        )
    if new_status != task['status']:
        log_task_history(
            db, task_id, task['task_name'], 'status_changed',
            field_name='status', old_value=task['status'], new_value=new_status
        )
    db.commit()
    return jsonify({'success': True})


@app.route('/tasks/progress/override', methods=['POST'])
def set_task_progress_manual():
    """Manually override task progress, locking it from auto-calculation."""
    db = get_db()
    data = request.get_json() or {}
    task_id = parse_optional_int(data.get('task_id'))
    progress = clamp_progress(data.get('progress'))
    is_manual = bool(data.get('is_manual', True))

    if not task_id:
        return jsonify({'success': False, 'message': 'Task ID is required.'}), 400

    task = fetch_task_record(db, task_id)
    if not task:
        return jsonify({'success': False, 'message': 'Task not found.'}), 404

    db.execute(
        'UPDATE task_items SET progress = ?, progress_auto = ? WHERE id = ?',
        (progress, -1 if is_manual else 0, task_id)
    )
    db.commit()
    return jsonify({'success': True, 'progress': progress})


@app.route('/tasks/subtasks/<int:task_id>')
def get_task_subtasks_inline(task_id):
    """Get inline subtasks for a task (used in task row expansion)."""
    db = get_db()
    subtasks = db.execute('''
        SELECT s.*,
               a.username AS assigned_to_name
        FROM task_subtasks s
        LEFT JOIN users a ON s.assigned_to_user_id = a.id
        WHERE s.parent_task_id = ?
        ORDER BY s.priority DESC, s.created_at ASC
    ''', (task_id,)).fetchall()
    return jsonify([dict(row) for row in subtasks])


@app.route('/tasks/reminders/check')
def check_task_reminders():
    """Return tasks where reminder time has been reached but not yet notified."""
    db = get_db()
    now = datetime.now()
    tasks = db.execute('''
        SELECT t.id, t.task_name, t.due_at, t.reminder_days, t.reminder_hours,
               t.last_reminder_sent, t.assigned_to_user_id, t.report_to_user_id,
               a.username AS assigned_to_name, a.email AS assigned_to_email,
               r.username AS report_to_name, r.email AS report_to_email,
               t.progress, t.status
        FROM task_items t
        LEFT JOIN users a ON t.assigned_to_user_id = a.id
        LEFT JOIN users r ON t.report_to_user_id = r.id
        WHERE t.due_at IS NOT NULL
          AND t.due_at != ''
          AND t.status NOT IN ('Completed', 'Archived')
          AND (t.last_reminder_sent IS NULL OR t.last_reminder_sent = '')
    ''').fetchall()

    reminders = []
    for task in tasks:
        due_at = task['due_at']
        if not due_at:
            continue
        try:
            due_dt = datetime.fromisoformat(due_at.replace(' ', 'T'))
        except (ValueError, TypeError):
            try:
                due_dt = datetime.strptime(due_at, '%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                continue

        reminder_days = task['reminder_days'] or 0
        reminder_hours = task['reminder_hours'] or 0
        total_reminder_seconds = (reminder_days * 86400) + (reminder_hours * 3600)
        reminder_time = due_dt - timedelta(seconds=total_reminder_seconds)

        if now >= reminder_time:
            recipients = []
            if task['assigned_to_email']:
                recipients.append({'name': task['assigned_to_name'], 'email': task['assigned_to_email']})
            if task['report_to_email']:
                recipients.append({'name': task['report_to_name'], 'email': task['report_to_email']})
            reminders.append({
                'task_id': task['id'],
                'task_name': task['task_name'],
                'due_at': due_at,
                'reminder_text': f"Reminder: '{task['task_name']}' is due on {due_at}. " +
                                 f"You'll be notified {reminder_days} days and {reminder_hours} hours before.",
                'recipients': recipients,
                'progress': task['progress'],
                'status': task['status']
            })
    return jsonify(reminders)


@app.route('/tasks/reminders/mark_sent', methods=['POST'])
def mark_reminder_sent():
    """Mark that a reminder was sent for a task."""
    db = get_db()
    data = request.get_json() or {}
    task_id = parse_optional_int(data.get('task_id'))
    if task_id:
        db.execute(
            "UPDATE task_items SET last_reminder_sent = datetime('now') WHERE id = ?",
            (task_id,)
        )
        db.commit()
    return jsonify({'success': True})


def _send_reminder_email(recipients, task_name, due_at, reminder_type='Task'):
    """Helper to send a reminder email."""
    try:
        from email_manager import get_email_config
        email_config = get_email_config()
        if not email_config or not email_config.get('smtp_host'):
            return False
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'Reminder: {task_name} is due on {due_at}'
        body = f'''Hello,

This is a reminder that the following {reminder_type} is due:

{'_' * 50}
Title: {task_name}
Due Date: {due_at}
{'_' * 50}

Please take action before the deadline.

Best regards,
WHDASH Notification System
'''
        msg.attach(MIMEText(body, 'plain'))
        msg['From'] = email_config.get('smtp_username', 'noreply@whdash.local')

        for recipient in recipients:
            email = recipient.get('email')
            if not email:
                continue
            msg['To'] = email
            try:
                with smtplib.SMTP(email_config['smtp_host'], email_config.get('smtp_port', 587)) as server:
                    server.starttls()
                    server.login(email_config['smtp_username'], email_config['smtp_password'])
                    server.send_message(msg)
            except Exception:
                continue
        return True
    except Exception:
        return False


@app.route('/tasks/reminders/send', methods=['POST'])
def send_task_reminders():
    """Check and send due reminders for tasks and subtasks, then mark them sent."""
    db = get_db()
    data = request.get_json() or {}
    task_ids = data.get('task_ids', [])
    subtask_ids = data.get('subtask_ids', [])
    results = {'tasks': [], 'subtasks': [], 'errors': []}

    # Process task reminders
    for task_id in task_ids:
        task = db.execute('''
            SELECT t.id, t.task_name, t.due_at, t.reminder_days, t.reminder_hours,
                   t.last_reminder_sent, t.assigned_to_user_id, t.report_to_user_id,
                   a.username AS assigned_to_name, a.email AS assigned_to_email,
                   r.username AS report_to_name, r.email AS report_to_email
            FROM task_items t
            LEFT JOIN users a ON t.assigned_to_user_id = a.id
            LEFT JOIN users r ON t.report_to_user_id = r.id
            WHERE t.id = ? AND t.due_at IS NOT NULL AND t.due_at != ''
              AND t.status NOT IN ('Completed', 'Archived')
        ''', (task_id,)).fetchone()

        if not task:
            continue
        due_at = task['due_at']
        try:
            due_dt = datetime.fromisoformat(due_at.replace(' ', 'T'))
        except (ValueError, TypeError):
            try:
                due_dt = datetime.strptime(due_at, '%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                continue

        reminder_days = task['reminder_days'] or 0
        reminder_hours = task['reminder_hours'] or 0
        total_reminder_seconds = (reminder_days * 86400) + (reminder_hours * 3600)
        reminder_time = due_dt - timedelta(seconds=total_reminder_seconds)

        if datetime.now() >= reminder_time:
            recipients = []
            if task['assigned_to_email']:
                recipients.append({'name': task['assigned_to_name'], 'email': task['assigned_to_email']})
            if task['report_to_email']:
                recipients.append({'name': task['report_to_name'], 'email': task['report_to_email']})
            if recipients:
                _send_reminder_email(recipients, task['task_name'], due_at, 'Task')
            db.execute("UPDATE task_items SET last_reminder_sent = datetime('now') WHERE id = ?", (task_id,))
            db.commit()
            results['tasks'].append(task_id)

    # Process subtask reminders
    for subtask_id in subtask_ids:
        st = db.execute('''
            SELECT s.id, s.subtask_title, s.due_at, s.reminder_days, s.reminder_hours,
                   s.last_reminder_sent, s.assigned_to_user_id,
                   a.username AS assigned_to_name, a.email AS assigned_to_email,
                   p.task_name AS parent_task_name
            FROM task_subtasks s
            LEFT JOIN users a ON s.assigned_to_user_id = a.id
            LEFT JOIN task_items p ON s.parent_task_id = p.id
            WHERE s.id = ? AND s.due_at IS NOT NULL AND s.due_at != ''
              AND s.status NOT IN ('Completed', 'Canceled')
        ''', (subtask_id,)).fetchone()

        if not st:
            continue
        due_at = st['due_at']
        try:
            due_dt = datetime.fromisoformat(due_at.replace(' ', 'T'))
        except (ValueError, TypeError):
            try:
                due_dt = datetime.strptime(due_at, '%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                continue

        reminder_days = st['reminder_days'] or 0
        reminder_hours = st['reminder_hours'] or 0
        total_reminder_seconds = (reminder_days * 86400) + (reminder_hours * 3600)
        reminder_time = due_dt - timedelta(seconds=total_reminder_seconds)

        if datetime.now() >= reminder_time:
            recipients = []
            if st['assigned_to_email']:
                recipients.append({'name': st['assigned_to_name'], 'email': st['assigned_to_email']})
            if recipients:
                full_title = f"{st['subtask_title']} (parent: {st['parent_task_name']})"
                _send_reminder_email(recipients, full_title, due_at, 'Subtask')
            db.execute("UPDATE task_subtasks SET last_reminder_sent = datetime('now') WHERE id = ?", (subtask_id,))
            db.commit()
            results['subtasks'].append(subtask_id)

    return jsonify({'success': True, 'results': results})


@app.route('/subtasks/reminders/check')
def check_subtask_reminders():
    """Return subtasks where reminder time has been reached but not yet notified."""
    db = get_db()
    now = datetime.now()
    subtasks = db.execute('''
        SELECT s.id, s.subtask_title, s.due_at, s.reminder_days, s.reminder_hours,
               s.last_reminder_sent, s.assigned_to_user_id,
               a.username AS assigned_to_name, a.email AS assigned_to_email,
               p.task_name AS parent_task_name
        FROM task_subtasks s
        LEFT JOIN users a ON s.assigned_to_user_id = a.id
        LEFT JOIN task_items p ON s.parent_task_id = p.id
        WHERE s.due_at IS NOT NULL
          AND s.due_at != ''
          AND s.status NOT IN ('Completed', 'Canceled')
          AND (s.last_reminder_sent IS NULL OR s.last_reminder_sent = '')
    ''').fetchall()

    reminders = []
    for st in subtasks:
        due_at = st['due_at']
        if not due_at:
            continue
        try:
            due_dt = datetime.fromisoformat(due_at.replace(' ', 'T'))
        except (ValueError, TypeError):
            try:
                due_dt = datetime.strptime(due_at, '%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                continue

        reminder_days = st['reminder_days'] or 0
        reminder_hours = st['reminder_hours'] or 0
        total_reminder_seconds = (reminder_days * 86400) + (reminder_hours * 3600)
        reminder_time = due_dt - timedelta(seconds=total_reminder_seconds)

        if now >= reminder_time:
            recipients = []
            if st['assigned_to_email']:
                recipients.append({'name': st['assigned_to_name'], 'email': st['assigned_to_email']})
            reminders.append({
                'subtask_id': st['id'],
                'subtask_title': st['subtask_title'],
                'parent_task_name': st['parent_task_name'] or '',
                'due_at': due_at,
                'reminder_text': f"Reminder: Subtask '{st['subtask_title']}' (parent: {st['parent_task_name']}) is due on {due_at}. " +
                                 f"You'll be notified {reminder_days} days and {reminder_hours} hours before.",
                'recipients': recipients,
                'progress': st['progress'],
                'status': st['status']
            })
    return jsonify(reminders)


@app.route('/subtasks/reminders/mark_sent', methods=['POST'])
def mark_subtask_reminder_sent():
    """Mark that a reminder was sent for a subtask."""
    db = get_db()
    data = request.get_json() or {}
    subtask_id = data.get('subtask_id')
    if subtask_id:
        db.execute(
            "UPDATE task_subtasks SET last_reminder_sent = datetime('now') WHERE id = ?",
            (subtask_id,)
        )
        db.commit()
    return jsonify({'success': True})


@app.route('/tasks/departments/save', methods=['POST'])
@admin_required
def save_task_department():
    db = get_db()
    data = request.get_json() or {}
    department_id = parse_optional_int(data.get('department_id'))
    name = (data.get('name') or '').strip()
    description = (data.get('description') or '').strip()
    status = (data.get('status') or 'Active').strip()

    if not name:
        return jsonify({'success': False, 'message': 'Department name is required.'}), 400

    try:
        if department_id:
            db.execute(
                "UPDATE task_departments SET name = ?, description = ?, status = ? WHERE id = ?",
                (name, description, status, department_id)
            )
        else:
            db.execute(
                "INSERT INTO task_departments (name, description, status) VALUES (?, ?, ?)",
                (name, description, status)
            )
        db.commit()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'A department with this name already exists.'}), 400


@app.route('/tasks/departments/delete', methods=['POST'])
@admin_required
def delete_task_department():
    db = get_db()
    data = request.get_json() or {}
    department_id = parse_optional_int(data.get('department_id'))
    if not department_id:
        return jsonify({'success': False, 'message': 'Invalid department.'}), 400

    in_use = db.execute("SELECT COUNT(*) FROM task_items WHERE department_id = ?", (department_id,)).fetchone()[0]
    if in_use:
        return jsonify({'success': False, 'message': 'This department is linked to existing tasks.'}), 400

    db.execute("DELETE FROM task_departments WHERE id = ?", (department_id,))
    db.commit()
    return jsonify({'success': True})


@app.route('/issues')
def issue_tracker():
    db = get_db()
    issue_rows = db.execute(
        '''
        SELECT *
        FROM issue_items
        ORDER BY
            CASE WHEN issue_date_sort IS NULL THEN 1 ELSE 0 END,
            COALESCE(issue_date_sort, ''),
            row_id ASC
        '''
    ).fetchall()
    issues = [prepare_issue_for_view(dict(row)) for row in issue_rows]

    issue_departments = sorted({dept for issue in issues for dept in issue['involved_departments_list']}, key=str.lower)
    issue_people = set()
    for user_row in db.execute("SELECT username FROM users ORDER BY username").fetchall():
        if user_row['username']:
            issue_people.add(user_row['username'])
    for issue in issues:
        for field_name in ('writer', 'reported_by', 'responsible_person', 'follow_up_by'):
            if issue.get(field_name) and issue[field_name] != '-':
                issue_people.add(issue[field_name])

    stats = {
        'total': len(issues),
        'open': sum(1 for issue in issues if issue.get('status') == 'Open'),
        'pending': sum(1 for issue in issues if issue.get('status') == 'Pending'),
        'closed': sum(1 for issue in issues if issue.get('status') == 'Closed'),
        'pareto': sum(1 for issue in issues if int(issue.get('pareto_law') or 0) == 1),
    }

    recent_updates = [
        dict(row) for row in db.execute(
            '''
            SELECT h.*, i.row_id, i.issue, actor.username AS actor_name
            FROM issue_history h
            JOIN issue_items i ON i.id = h.issue_id
            LEFT JOIN users actor ON actor.id = h.actor_user_id
            ORDER BY h.created_at DESC, h.id DESC
            LIMIT 12
            '''
        ).fetchall()
    ] 

    visible_issue_columns = get_issue_visible_columns(db)
    issue_report = build_issue_report(issues)

    return render_template(
        'issues.html',
        title='Issue Tracker',
        issues=issues,
        stats=stats,
        issue_report=issue_report,
        issue_departments=issue_departments,
        issue_column_options=ISSUE_COLUMN_OPTIONS,
        issue_column_keys=ISSUE_COLUMN_KEYS,
        visible_issue_columns=visible_issue_columns,
        issue_priority_options=ISSUE_PRIORITY_OPTIONS,
        issue_status_options=ISSUE_STATUS_OPTIONS,
        issue_type_options=ISSUE_TYPE_OPTIONS,
        issue_people_options=sorted(issue_people, key=str.lower),
        can_edit_issues=user_can_edit_issues(),
        recent_updates=recent_updates,
        today_value=datetime.now().strftime('%Y-%m-%d')
    )


@app.route('/issues/save', methods=['POST'])
def save_issue():
    if not user_can_edit_issues():
        return jsonify({'success': False, 'message': 'You do not have permission to edit issues.'}), 403

    db = get_db()
    data = request.get_json() or {}
    issue_id = parse_optional_int(data.get('issue_id'))
    existing_issue = None
    if issue_id:
        existing_issue = db.execute("SELECT * FROM issue_items WHERE id = ?", (issue_id,)).fetchone()
        if not existing_issue:
            return jsonify({'success': False, 'message': 'Issue not found.'}), 404

    row_id = parse_optional_int(data.get('row_id'))
    if not row_id:
        row_id = existing_issue['row_id'] if existing_issue else db.execute(
            "SELECT COALESCE(MAX(row_id), 0) + 1 FROM issue_items"
        ).fetchone()[0]

    issue_date = (data.get('issue_date') or '').strip() or 'Past'
    issue_date_sort = parse_issue_date_sort_value(issue_date)
    issue_text = (data.get('issue') or '').strip()
    if not issue_text:
        return jsonify({'success': False, 'message': 'Issue title is required.'}), 400

    duplicate = db.execute(
        "SELECT id FROM issue_items WHERE row_id = ? AND id != COALESCE(?, -1) LIMIT 1",
        (row_id, issue_id)
    ).fetchone()
    if duplicate:
        return jsonify({'success': False, 'message': 'Row ID is already in use.'}), 400

    payload = {
        'row_id': row_id,
        'issue_date': issue_date,
        'issue_date_sort': issue_date_sort,
        'issue': issue_text,
        'pareto_law': 1 if str(data.get('pareto_law')).lower() in ('true', '1', 'yes', 'on') else 0,
        'involved_departments': serialize_issue_departments(data.get('involved_departments')),
        'section_team': (data.get('section_team') or '').strip(),
        'issue_type': normalize_issue_type(data.get('issue_type')),
        'writer': (data.get('writer') or '').strip(),
        'reported_by': (data.get('reported_by') or '').strip(),
        'priority': normalize_issue_priority(data.get('priority')),
        'status': normalize_issue_status(data.get('status')),
        'responsible_section': (data.get('responsible_section') or '').strip(),
        'responsible_person': (data.get('responsible_person') or '').strip(),
        'root_cause': (data.get('root_cause') or '').strip(),
        'impact': (data.get('impact') or '').strip(),
        'action_plan': (data.get('action_plan') or '').strip(),
        'resources_needed': (data.get('resources_needed') or '').strip(),
        'target_resolution_date': (data.get('target_resolution_date') or '').strip(),
        'first_follow_up_date': (data.get('first_follow_up_date') or '').strip(),
        'first_follow_up_notes': (data.get('first_follow_up_notes') or '').strip(),
        'second_follow_up_date': (data.get('second_follow_up_date') or '').strip(),
        'second_follow_up_notes': (data.get('second_follow_up_notes') or '').strip(),
        'follow_up_by': (data.get('follow_up_by') or '').strip(),
        'progress_note': (data.get('progress_note') or '').strip(),
        'linked_issues': (data.get('linked_issues') or '').strip(),
        'final_status': (data.get('final_status') or '').strip(),
    }

    if issue_id:
        db.execute(
            '''
            UPDATE issue_items
            SET row_id = ?, issue_date = ?, issue_date_sort = ?, issue = ?, pareto_law = ?, involved_departments = ?,
                section_team = ?, issue_type = ?, writer = ?, reported_by = ?, priority = ?, status = ?,
                responsible_section = ?, responsible_person = ?, root_cause = ?, impact = ?, action_plan = ?,
                resources_needed = ?, target_resolution_date = ?, first_follow_up_date = ?, first_follow_up_notes = ?,
                second_follow_up_date = ?, second_follow_up_notes = ?, follow_up_by = ?, progress_note = ?,
                linked_issues = ?, final_status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            ''',
            (
                payload['row_id'], payload['issue_date'], payload['issue_date_sort'], payload['issue'], payload['pareto_law'],
                payload['involved_departments'], payload['section_team'], payload['issue_type'], payload['writer'],
                payload['reported_by'], payload['priority'], payload['status'], payload['responsible_section'],
                payload['responsible_person'], payload['root_cause'], payload['impact'], payload['action_plan'],
                payload['resources_needed'], payload['target_resolution_date'], payload['first_follow_up_date'],
                payload['first_follow_up_notes'], payload['second_follow_up_date'], payload['second_follow_up_notes'],
                payload['follow_up_by'], payload['progress_note'], payload['linked_issues'], payload['final_status'], issue_id
            )
        )
        log_issue_history(db, issue_id, 'updated', note=f"Issue row {row_id} updated")
        db.commit()
        return jsonify({
            'success': True,
            'message': 'Issue updated successfully.',
            'issue_id': issue_id,
            'row_id': row_id
        })

    cursor = db.execute(
        '''
        INSERT INTO issue_items (
            row_id, issue_date, issue_date_sort, issue, pareto_law, involved_departments,
            section_team, issue_type, writer, reported_by, priority, status,
            responsible_section, responsible_person, root_cause, impact, action_plan,
            resources_needed, target_resolution_date, first_follow_up_date, first_follow_up_notes,
            second_follow_up_date, second_follow_up_notes, follow_up_by, progress_note,
            linked_issues, final_status, created_by_user_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            payload['row_id'], payload['issue_date'], payload['issue_date_sort'], payload['issue'], payload['pareto_law'],
            payload['involved_departments'], payload['section_team'], payload['issue_type'], payload['writer'],
            payload['reported_by'], payload['priority'], payload['status'], payload['responsible_section'],
            payload['responsible_person'], payload['root_cause'], payload['impact'], payload['action_plan'],
            payload['resources_needed'], payload['target_resolution_date'], payload['first_follow_up_date'],
            payload['first_follow_up_notes'], payload['second_follow_up_date'], payload['second_follow_up_notes'],
            payload['follow_up_by'], payload['progress_note'], payload['linked_issues'], payload['final_status'],
            session.get('user_id')
        )
    )
    new_issue_id = cursor.lastrowid
    log_issue_history(db, new_issue_id, 'created', note=f"Issue row {row_id} created")
    db.commit()
    return jsonify({
        'success': True,
        'message': 'Issue created successfully.',
        'issue_id': new_issue_id,
        'row_id': row_id
    })


@app.route('/issues/preferences', methods=['POST'])
def save_issue_preferences():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please sign in to save issue view preferences.'}), 403

    db = get_db()
    data = request.get_json() or {}
    visible_columns = sanitize_issue_visible_columns(data.get('visible_columns', []))

    db.execute(
        '''
        INSERT INTO user_issue_preferences (user_id, visible_columns, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            visible_columns = excluded.visible_columns,
            updated_at = CURRENT_TIMESTAMP
        ''',
        (user_id, json.dumps(visible_columns, ensure_ascii=False))
    )
    db.commit()
    return jsonify({'success': True, 'message': 'Issue table view saved.', 'visible_columns': visible_columns})


@app.route('/tasks/preferences', methods=['POST'])
def save_task_preferences():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please sign in to save task view preferences.'}), 403

    db = get_db()
    data = request.get_json() or {}
    visible_columns = sanitize_task_visible_columns(data.get('visible_columns', []))

    db.execute(
        '''
        INSERT INTO user_task_preferences (user_id, visible_columns, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            visible_columns = excluded.visible_columns,
            updated_at = CURRENT_TIMESTAMP
        ''',
        (user_id, json.dumps(visible_columns, ensure_ascii=False))
    )
    db.commit()
    return jsonify({'success': True, 'message': 'Task table view saved.', 'visible_columns': visible_columns})


@app.route('/issues/bulk_action', methods=['POST'])
def issue_bulk_action():
    if not user_can_edit_issues():
        return jsonify({'success': False, 'message': 'You do not have permission to update issues.'}), 403

    db = get_db()
    data = request.get_json() or {}
    action = (data.get('action') or '').strip().lower()
    issue_ids = [parse_optional_int(issue_id) for issue_id in data.get('issue_ids', [])]
    issue_ids = [issue_id for issue_id in issue_ids if issue_id]
    target_status = normalize_issue_status(data.get('status'))

    if not issue_ids:
        return jsonify({'success': False, 'message': 'No issues were selected.'}), 400

    affected = 0
    for issue_id in issue_ids:
        issue_row = db.execute("SELECT id, row_id FROM issue_items WHERE id = ?", (issue_id,)).fetchone()
        if not issue_row:
            continue

        if action == 'status':
            db.execute(
                "UPDATE issue_items SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (target_status, issue_id)
            )
            log_issue_history(db, issue_id, 'status_changed', note=f"Status set to {target_status}")
            affected += 1
        elif action in ('delete', 'remove'):
            log_issue_history(db, issue_id, 'deleted', note=f"Issue row {issue_row['row_id']} removed")
            db.execute("DELETE FROM issue_items WHERE id = ?", (issue_id,))
            affected += 1

    db.commit()
    return jsonify({'success': True, 'message': f'{affected} issue(s) updated.', 'affected': affected})

@app.route('/reports')
@admin_required
def reports():
    db = get_db()
    now_value = datetime.now()
    
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # 1. Quantity by Subsidiary
    qty_by_subsidiary = [dict(r) for r in db.execute('''
        SELECT c.name, SUM(i.quantity) as total 
        FROM inventory i 
        JOIN companies c ON i.company_id = c.id 
        GROUP BY c.id
    ''').fetchall()]
    
    # 2. Location Occupancy
    loc_row = db.execute('''
        SELECT 
            (SELECT COUNT(*) FROM locations) as total_locs,
            (SELECT COUNT(DISTINCT zone) FROM inventory WHERE quantity > 0) as occupied_locs
    ''').fetchone()
    
    t_locs = int(loc_row['total_locs'] or 0)
    o_locs = int(loc_row['occupied_locs'] or 0)
    f_locs = int(t_locs - o_locs)
    
    loc_stats = {'total_locs': t_locs, 'occupied_locs': o_locs, 'free_locs': f_locs}
    
    # 3. Quantity by Brand (Top 10)
    qty_by_brand = [dict(r) for r in db.execute('''
        SELECT b.name, SUM(i.quantity) as total 
        FROM inventory i 
        JOIN parts p ON i.part_id = p.id 
        JOIN brands b ON p.brand_id = b.id 
        GROUP BY b.id 
        ORDER BY total DESC LIMIT 10
    ''').fetchall()]
    
    # 4. Diversity Stats
    div_row = db.execute('''
        SELECT 
            (SELECT COUNT(DISTINCT part_id) FROM inventory) as unique_parts,
            (SELECT COUNT(*) FROM brands) as total_brands,
            (SELECT COUNT(*) FROM categories) as total_categories
    ''').fetchone()
    diversity = dict(div_row) if div_row else {}
    
    # 5. Category Reports
    category_reports = [dict(r) for r in db.execute('''
        SELECT cat.name, COUNT(DISTINCT p.id) as part_count, SUM(i.quantity) as total_qty
        FROM inventory i 
        JOIN parts p ON i.part_id = p.id 
        JOIN categories cat ON p.category_id = cat.id 
        GROUP BY cat.id
    ''').fetchall()]
    
    # 6. Financial Valuation (AED)
    fin_stats = dict(db.execute('''
        SELECT 
            SUM(i.quantity * p.cost_price) as grand_total_value
        FROM inventory i 
        JOIN parts p ON i.part_id = p.id
    ''').fetchone())
    
    value_by_brand = [dict(r) for r in db.execute('''
        SELECT b.name, SUM(i.quantity * p.cost_price) as total_val 
        FROM inventory i 
        JOIN parts p ON i.part_id = p.id 
        JOIN brands b ON p.brand_id = b.id 
        GROUP BY b.id 
        ORDER BY total_val DESC LIMIT 10
    ''').fetchall()]
    
    value_by_category = [dict(r) for r in db.execute('''
        SELECT cat.name, SUM(i.quantity * p.cost_price) as total_val 
        FROM inventory i 
        JOIN parts p ON i.part_id = p.id 
        JOIN categories cat ON p.category_id = cat.id 
        GROUP BY cat.id
    ''').fetchall()]

    value_by_subsidiary = [dict(r) for r in db.execute('''
        SELECT c.name, SUM(i.quantity * p.cost_price) as total_val 
        FROM inventory i 
        JOIN parts p ON i.part_id = p.id 
        JOIN companies c ON i.company_id = c.id 
        GROUP BY c.id
    ''').fetchall()]

    # 7. Top Items by Value
    top_parts_value = [dict(r) for r in db.execute('''
        SELECT p.part_number, p.name, SUM(i.quantity) as total_qty, 
               SUM(i.quantity * p.cost_price) as total_val,
               cat.name as category, b.name as brand
        FROM inventory i
        JOIN parts p ON i.part_id = p.id
        LEFT JOIN categories cat ON p.category_id = cat.id
        LEFT JOIN brands b ON p.brand_id = b.id
        GROUP BY p.id
        ORDER BY total_val DESC
        LIMIT 20
    ''').fetchall()]

    # 8. Top Items by Quantity
    top_parts_qty = [dict(r) for r in db.execute('''
        SELECT p.part_number, p.name, SUM(i.quantity) as total_qty,
               SUM(i.quantity * p.cost_price) as total_val,
               cat.name as category, b.name as brand
        FROM inventory i
        JOIN parts p ON i.part_id = p.id
        LEFT JOIN categories cat ON p.category_id = cat.id
        LEFT JOIN brands b ON p.brand_id = b.id
        GROUP BY p.id
        ORDER BY total_qty DESC
        LIMIT 20
    ''').fetchall()]

    # 9. HS Code Cumulative Report
    hs_code_summary = [dict(r) for r in db.execute('''
        SELECT p.hs_code, COUNT(DISTINCT p.id) as part_count, SUM(i.quantity) as total_qty,
               SUM(i.quantity * p.cost_price) as total_val
        FROM inventory i
        JOIN parts p ON i.part_id = p.id
        WHERE p.hs_code IS NOT NULL AND p.hs_code != ''
        GROUP BY p.hs_code
        ORDER BY total_qty DESC
    ''').fetchall()]

    # 10. HS Code Balance by Company
    hs_by_company = [dict(r) for r in db.execute('''
        SELECT p.hs_code, c.name as company, SUM(i.quantity) as total_qty,
               SUM(i.quantity * p.cost_price) as total_val
        FROM inventory i
        JOIN parts p ON i.part_id = p.id
        JOIN companies c ON i.company_id = c.id
        WHERE p.hs_code IS NOT NULL AND p.hs_code != ''
        GROUP BY p.hs_code, c.id
        ORDER BY p.hs_code, c.name
    ''').fetchall()]

    # 11. HS Code Balance by Warehouse
    hs_by_warehouse = [dict(r) for r in db.execute('''
        SELECT p.hs_code, w.name as warehouse, c.name as company, SUM(i.quantity) as total_qty,
               SUM(i.quantity * p.cost_price) as total_val
        FROM inventory i
        JOIN parts p ON i.part_id = p.id
        JOIN warehouses w ON i.warehouse_id = w.id
        JOIN companies c ON w.company_id = c.id
        WHERE p.hs_code IS NOT NULL AND p.hs_code != ''
        GROUP BY p.hs_code, w.id
        ORDER BY p.hs_code, c.name, w.name
    ''').fetchall()]

    task_report_rows = db.execute(
        '''
        SELECT t.*, c.name AS company_name, d.name AS department_name,
               r.username AS report_to_name, a.username AS assigned_to_name,
               creator.username AS created_by_name
        FROM task_items t
        LEFT JOIN companies c ON t.company_id = c.id
        LEFT JOIN task_departments d ON t.department_id = d.id
        LEFT JOIN users r ON t.report_to_user_id = r.id
        LEFT JOIN users a ON t.assigned_to_user_id = a.id
        LEFT JOIN users creator ON t.created_by_user_id = creator.id
        ORDER BY t.updated_at DESC, t.id DESC
        '''
    ).fetchall()
    task_report = build_task_report([
        prepare_task_for_view(dict(row), now_value) for row in task_report_rows
    ])

    issue_report_rows = db.execute(
        '''
        SELECT *
        FROM issue_items
        ORDER BY
            CASE WHEN issue_date_sort IS NULL THEN 1 ELSE 0 END,
            COALESCE(issue_date_sort, ''),
            row_id ASC
        '''
    ).fetchall()
    issue_records = [prepare_issue_for_view(dict(row)) for row in issue_report_rows]
    issue_report = build_issue_report(issue_records)
    workspace_report = google_workspace_report_snapshot(db, session.get('user_id'))

    integration_report = {
        'summary': {
            'total_work_items': task_report['summary']['total'] + issue_report['summary']['total'],
            'active_work_items': task_report['summary']['active'] + sum(
                1 for issue in issue_records if issue.get('status') in ('Open', 'Pending')
            ),
            'accountability_gaps': task_report['summary']['unassigned_owner'] + issue_report['summary']['unassigned_owner'],
            'missing_resolution_inputs': (
                issue_report['summary']['missing_root_cause']
                + issue_report['summary']['missing_action_plan']
                + issue_report['summary']['missing_target_date']
                + task_report['summary']['future_missing_time']
            ),
        },
        'source_chart': [
            {'label': 'Task Center', 'total': task_report['summary']['total']},
            {'label': 'Issue Tracker', 'total': issue_report['summary']['total']},
        ],
        'risk_chart': [
            {'label': 'High Priority Tasks', 'total': task_report['summary']['high_priority_open']},
            {'label': 'High Priority Issues', 'total': issue_report['summary']['high_priority_open']},
            {'label': 'Canceled Tasks', 'total': task_report['summary']['canceled']},
            {'label': 'Pending Issues', 'total': next((item['total'] for item in issue_report['status_chart'] if item['label'] == 'Pending'), 0)},
        ],
        'discipline_chart': [
            {'label': 'Task Future Time Missing', 'total': task_report['summary']['future_missing_time']},
            {'label': 'Issue Missing Root Cause', 'total': issue_report['summary']['missing_root_cause']},
            {'label': 'Issue Missing Action Plan', 'total': issue_report['summary']['missing_action_plan']},
            {'label': 'Issue Missing Target Date', 'total': issue_report['summary']['missing_target_date']},
        ]
    }

    return render_template('reports.html', title="Master Reports",
                           qty_by_sub=qty_by_subsidiary,
                           loc_stats=loc_stats,
                           qty_by_brand=qty_by_brand,
                           diversity=diversity,
                           category_reports=category_reports,
                           fin_stats=fin_stats,
                           value_by_brand=value_by_brand,
                           value_by_category=value_by_category,
                           value_by_sub=value_by_subsidiary,
                           top_parts_value=top_parts_value,
                           top_parts_qty=top_parts_qty,
                           hs_code_summary=hs_code_summary,
                           hs_by_company=hs_by_company,
                           hs_by_warehouse=hs_by_warehouse,
                           task_report=task_report,
                           issue_report=issue_report,
                           workspace_report=workspace_report,
                           integration_report=integration_report,
                           start_date=start_date,
                           end_date=end_date)

@app.route('/reports/valuation_details')
@admin_required
def reports_valuation_details():
    db = get_db()
    # All items ordered by total value
    items = db.execute('''
        SELECT p.part_number, p.name, SUM(i.quantity) as total_qty, 
               SUM(i.quantity * p.cost_price) as total_val,
               cat.name as category, b.name as brand,
               GROUP_CONCAT(DISTINCT c.name) as companies
        FROM inventory i
        JOIN parts p ON i.part_id = p.id
        LEFT JOIN categories cat ON p.category_id = cat.id
        LEFT JOIN brands b ON p.brand_id = b.id
        LEFT JOIN companies c ON i.company_id = c.id
        GROUP BY p.id
        ORDER BY total_val DESC
    ''').fetchall()
    return render_template('reports_details.html', title="Valuation Analysis (Complete)", items=items, type="valuation")

@app.route('/reports/volume_details')
@admin_required
def reports_volume_details():
    db = get_db()
    # All items ordered by quantity
    items = db.execute('''
        SELECT p.part_number, p.name, SUM(i.quantity) as total_qty,
               SUM(i.quantity * p.cost_price) as total_val,
               cat.name as category, b.name as brand,
               GROUP_CONCAT(DISTINCT c.name) as companies
        FROM inventory i
        JOIN parts p ON i.part_id = p.id
        LEFT JOIN categories cat ON p.category_id = cat.id
        LEFT JOIN brands b ON p.brand_id = b.id
        LEFT JOIN companies c ON i.company_id = c.id
        GROUP BY p.id
        ORDER BY total_qty DESC
    ''').fetchall()
    return render_template('reports_details.html', title="Volume Analysis (Complete)", items=items, type="volume")

@app.route('/reports/export')
@admin_required
def export_reports():
    type = request.args.get('type', 'value')
    db = get_db()
    
    if type == 'value':
        title = "Top Parts by Valuation (AED)"
        query = '''
            SELECT p.part_number, p.name, SUM(i.quantity) as total_qty, 
                   SUM(i.quantity * p.cost_price) as total_val,
                   cat.name as category, b.name as brand
            FROM inventory i
            JOIN parts p ON i.part_id = p.id
            LEFT JOIN categories cat ON p.category_id = cat.id
            LEFT JOIN brands b ON p.brand_id = b.id
            GROUP BY p.id
            ORDER BY total_val DESC
        '''
    else:
        title = "Top Parts by Quantity (PCs)"
        query = '''
            SELECT p.part_number, p.name, SUM(i.quantity) as total_qty,
                   SUM(i.quantity * p.cost_price) as total_val,
                   cat.name as category, b.name as brand
            FROM inventory i
            JOIN parts p ON i.part_id = p.id
            LEFT JOIN categories cat ON p.category_id = cat.id
            LEFT JOIN brands b ON p.brand_id = b.id
            GROUP BY p.id
            ORDER BY total_qty DESC
        '''
        
    rows = db.execute(query).fetchall()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Stock Report"
    
    # Header styling
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    
    headers = ["#", "Part Number", "Description", "Category", "Brand", "Quantity (PCs)", "Total Valuation (AED)"]
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal='center')
        
    for idx, row in enumerate(rows, 1):
        ws.cell(row=idx+1, column=1, value=idx)
        ws.cell(row=idx+1, column=2, value=row['part_number'])
        ws.cell(row=idx+1, column=3, value=row['name'])
        ws.cell(row=idx+1, column=4, value=row['category'])
        ws.cell(row=idx+1, column=5, value=row['brand'])
        ws.cell(row=idx+1, column=6, value=row['total_qty'])
        ws.cell(row=idx+1, column=7, value=row['total_val'])
        
    # Auto-adjust column width
    for column in ws.columns:
        max_len = 0
        cells = [c for c in column]
        for cell in cells:
            try:
                val_str = str(cell.value or "")
                if len(val_str) > max_len:
                    max_len = len(val_str)
            except (ValueError, TypeError):
                pass
        
        # Apply standard padding
        final_width = float(max_len + 2.5)
        ws.column_dimensions[cells[0].column_letter].width = final_width

    filename = f"report_{type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    path = os.path.join(tempfile.gettempdir(), filename)
    wb.save(path)
    return send_file(path, as_attachment=True)

@app.route('/executive-dashboard')
@require_login
def executive_dashboard():
    db = get_db()
    now_value = datetime.now()
    period = request.args.get('period', 'week')
    
    # Core KPI Stats
    fin_stats = dict(db.execute('''
        SELECT COALESCE(SUM(i.quantity * p.cost_price), 0) as total_value
        FROM inventory i JOIN parts p ON i.part_id = p.id
    ''').fetchone() or {'total_value': 0})
    
    # Task Stats
    task_rows = db.execute('''
        SELECT status, COUNT(*) as count FROM task_items GROUP BY status
    ''').fetchall()
    task_status = {row['status']: row['count'] for row in task_rows}
    total_tasks = sum(task_status.values())
    tasks_completed = task_status.get('Completed', 0)
    
    # Issue Stats
    issue_rows = db.execute('''
        SELECT status, priority, COUNT(*) as count FROM issue_items GROUP BY status, priority
    ''').fetchall()
    total_issues = sum(row['count'] for row in issue_rows)
    open_issues = sum(row['count'] for row in issue_rows if row['status'] in ('Open', 'Pending'))
    high_priority_issues = sum(row['count'] for row in issue_rows if row['priority'] == 'High' and row['status'] != 'Closed')
    
    # Employee Stats (from HR module if available)
    try:
        emp_row = db.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active
            FROM employees
        ''').fetchone()
        total_employees = emp_row['total'] if emp_row else 0
        active_employees = emp_row['active'] if emp_row else 0
    except:
        total_employees = 0
        active_employees = 0
    
    # Delivery Stats
    delivery_rows = db.execute('''
        SELECT status, COUNT(*) as count FROM delivery_trips GROUP BY status
    ''').fetchall()
    total_deliveries = sum(row['count'] for row in delivery_rows)
    completed_deliveries = sum(row['count'] for row in delivery_rows if row['status'] == 'Completed')
    delivery_success = int((completed_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0)
    
    # Inventory Stats
    inv_stats = dict(db.execute('''
        SELECT 
            COALESCE(SUM(quantity), 0) as total_qty,
            COUNT(DISTINCT part_id) as item_count,
            COUNT(CASE WHEN quantity <= 0 THEN 1 END) as out_count,
            COUNT(CASE WHEN quantity > 0 AND quantity <= 10 THEN 1 END) as low_count
        FROM inventory
    ''').fetchone() or {'total_qty': 0, 'item_count': 0, 'out_count': 0, 'low_count': 0})
    
    # Customer Stats
    customer_stats = dict(db.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN created_at >= date('now', '-30 days') THEN 1 END) as new_this_month
        FROM customers
    ''').fetchone() or {'total': 0, 'new_this_month': 0})
    
    # Location Stats
    loc_stats = db.execute('''
        SELECT 
            COUNT(*) as total_locs,
            COUNT(CASE WHEN zone IS NOT NULL AND zone != '' THEN 1 END) as occupied
        FROM locations
    ''').fetchone()
    occupied_locations = loc_stats['occupied'] if loc_stats else 0
    total_locations = loc_stats['total_locs'] if loc_stats else 0
    
    # Vehicle Stats
    vehicle_stats = db.execute('''
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN status = 'Active' THEN 1 END) as active
        FROM vehicles
    ''').fetchone()
    total_vehicles = vehicle_stats['total'] if vehicle_stats else 0
    active_vehicles = vehicle_stats['active'] if vehicle_stats else 0
    
    # Department Performance (mock data - can be replaced with real HR data)
    department_performance = [
        {'name': 'Warehouse Operations', 'tasks': 45, 'completion_rate': 82, 'performance_score': 78, 'color': 'cyan', 'icon': 'warehouse'},
        {'name': 'Sales & Marketing', 'tasks': 38, 'completion_rate': 91, 'performance_score': 88, 'color': 'emerald', 'icon': 'chart-line'},
        {'name': 'Logistics & Delivery', 'tasks': 52, 'completion_rate': 87, 'performance_score': 85, 'color': 'amber', 'icon': 'truck-fast'},
        {'name': 'HR & Administration', 'tasks': 18, 'completion_rate': 95, 'performance_score': 92, 'color': 'purple', 'icon': 'users'},
        {'name': 'Finance & Accounting', 'tasks': 24, 'completion_rate': 89, 'performance_score': 86, 'color': 'brand', 'icon': 'file-invoice-dollar'},
    ]
    
    # System Health
    system_health = [
        {'name': 'Google Workspace', 'status': 'Connected', 'color': 'emerald', 'icon': 'google'},
        {'name': 'Peyvast Sync', 'status': 'Active', 'color': 'emerald', 'icon': 'cloud'},
        {'name': 'Email System', 'status': 'Operational', 'color': 'emerald', 'icon': 'envelope'},
        {'name': 'Database', 'status': 'Healthy', 'color': 'emerald', 'icon': 'database'},
        {'name': 'API Services', 'status': 'Operational', 'color': 'emerald', 'icon': 'server'},
    ]
    
    kpi = {
        'total_revenue': fin_stats.get('total_value', 0),
        'revenue_growth': 15000,
        'total_tasks': total_tasks,
        'tasks_completed': tasks_completed,
        'tasks_not_started': task_status.get('Not Started', 0),
        'tasks_in_progress': task_status.get('In Progress', 0),
        'tasks_blocked': task_status.get('Blocked', 0),
        'open_issues': open_issues,
        'high_priority_issues': high_priority_issues,
        'total_employees': total_employees,
        'active_employees': active_employees,
        'employee_retention': 94,
        'attendance_rate': 96,
        'avg_salary': 8500,
        'turnover_rate': 4,
        'total_deliveries': total_deliveries,
        'delivery_success_rate': delivery_success,
        'fleet_utilization': 78,
        'on_time_delivery': 92,
        'avg_delivery_time': 45,
        'inventory_value': fin_stats.get('total_value', 0),
        'inventory_items': inv_stats.get('item_count', 0),
        'stock_normal_pct': 72,
        'stock_low_pct': 18,
        'stock_out_pct': 10,
        'total_customers': customer_stats.get('total', 0),
        'active_customers': int(customer_stats.get('total', 0) * 0.75),
        'new_customers': customer_stats.get('new_this_month', 0),
        'avg_order_value': 4500,
        'warehouse_occupancy': int((occupied_locations / total_locations * 100) if total_locations > 0 else 75),
        'occupied_locations': occupied_locations,
        'available_locations': total_locations - occupied_locations,
        'active_vehicles': active_vehicles,
        'total_vehicles': total_vehicles,
        'issues_critical_open': sum(1 for r in issue_rows if r['priority'] == 'Critical' and r['status'] != 'Closed'),
        'issues_high_open': sum(1 for r in issue_rows if r['priority'] == 'High' and r['status'] != 'Closed'),
        'issues_medium_open': sum(1 for r in issue_rows if r['priority'] == 'Medium' and r['status'] != 'Closed'),
        'issues_low_open': sum(1 for r in issue_rows if r['priority'] == 'Low' and r['status'] != 'Closed'),
        'issues_critical_resolved': sum(1 for r in issue_rows if r['priority'] == 'Critical' and r['status'] == 'Closed'),
        'issues_high_resolved': sum(1 for r in issue_rows if r['priority'] == 'High' and r['status'] == 'Closed'),
        'issues_medium_resolved': sum(1 for r in issue_rows if r['priority'] == 'Medium' and r['status'] == 'Closed'),
        'issues_low_resolved': sum(1 for r in issue_rows if r['priority'] == 'Low' and r['status'] == 'Closed'),
        'sales_by_region': ['Dubai', 'Abu Dhabi', 'Sharjah', 'Al Ain', 'Other'],
        'sales_by_region_value': [45000, 38000, 22000, 15000, 10000],
        'revenue_trend': [65000, 72000, 68000, 85000, 92000, 88000, 95000, 102000, 98000, 115000, 125000, 135000],
    }
    
    return render_template('executive_dashboard.html', title="Executive Command Center",
                           kpi=kpi,
                           department_performance=department_performance,
                           system_health=system_health,
                           period=period)

@app.route('/api/inventory', methods=['GET'])
def api_inventory():
    db = get_db()
    
    comp_ids = request.args.get('company_id', '').split(',')
    cat_ids = request.args.get('category_id', '').split(',')
    brand_ids = request.args.get('brand_id', '').split(',')
    status_ids = request.args.get('status_id', '').split(',')
    vitality_ids = request.args.get('vitality_id', '').split(',')
    health_statuses = request.args.get('health_status', '').split(',')
    zone = request.args.get('zone', '').strip()
    
    comp_ids = [c for c in comp_ids if c]
    cat_ids = [c for c in cat_ids if c]
    brand_ids = [b for b in brand_ids if b]
    status_ids = [s for s in status_ids if s]
    vitality_ids = [v for v in vitality_ids if v]
    health_statuses = [h for h in health_statuses if h]
    
    locked_company = session.get('company_id')
    if locked_company:
        comp_ids = [str(locked_company)]
        
    query = """
        SELECT i.id, p.part_number, p.description, p.cost_price, p.reorder_point,
               p.weight, p.length, p.width, p.height,
               i.quantity, i.zone, c.name as subsidiary, cat.name as category,
               b.name as brand, s.name as status, v.name as vitality_name
        FROM inventory i
        JOIN parts p ON i.part_id = p.id
        JOIN companies c ON i.company_id = c.id
        LEFT JOIN categories cat ON p.category_id = cat.id
        LEFT JOIN brands b ON p.brand_id = b.id
        LEFT JOIN statuses s ON p.status_id = s.id
        LEFT JOIN vitalities v ON p.vitality_id = v.id
        WHERE 1=1
    """
    
    params = []
    if comp_ids:
        placeholders = ','.join('?' for _ in comp_ids)
        query += f" AND i.company_id IN ({placeholders})"
        params.extend(comp_ids)
    if cat_ids:
        placeholders = ','.join('?' for _ in cat_ids)
        query += f" AND p.category_id IN ({placeholders})"
        params.extend(cat_ids)
    if brand_ids:
        placeholders = ','.join('?' for _ in brand_ids)
        query += f" AND p.brand_id IN ({placeholders})"
        params.extend(brand_ids)
    if status_ids:
        placeholders = ','.join('?' for _ in status_ids)
        query += f" AND p.status_id IN ({placeholders})"
        params.extend(status_ids)
    if vitality_ids:
        placeholders = ','.join('?' for _ in vitality_ids)
        query += f" AND p.vitality_id IN ({placeholders})"
        params.extend(vitality_ids)
    if zone:
        query += " AND i.zone LIKE ?"
        params.append(f"%{zone}%")
        
    query += " ORDER BY c.name, p.part_number"
    
    rows = db.execute(query, params).fetchall()
    
    data = []
    for row in rows:
        # Defensive numeric handling
        qty = row['quantity'] if row['quantity'] is not None else 0
        price = row['cost_price'] if row['cost_price'] is not None else 0
        reorder = row['reorder_point'] if row['reorder_point'] is not None else 0
        
        val = qty * price
        
        # Guard against division by zero or null reorder point
        health = 'Healthy'
        if qty < reorder:
            health = 'Critical'
        elif qty < reorder * 1.5:
            health = 'Warning'
        else:
            health = 'Healthy'
        
        # Filter by health status if requested
        if health_statuses and health not in health_statuses:
            continue
            
        data.append({
            'id': row['id'],
            'part_number': row['part_number'],
            'description': row['description'] or '',
            'subsidiary': row['subsidiary'],
            'zone': row['zone'] or 'Unassigned',
            'category': row['category'] or 'Uncategorized',
            'brand': row['brand'] or 'No Brand',
            'status': row['status'] or 'N/A',
            'vitality': row['vitality_name'] or 'Healthy',
            'quantity': qty,
            'reorder_point': reorder,
            'cost_price': float(f"{float(price):.2f}"),
            'total_value': float(f"{float(val):.2f}"),
            'health': health,
            'weight': float(f"{float(row['weight'] or 0):.2f}"),
            'length': float(f"{float(row['length'] or 0):.2f}"),
            'width': float(f"{float(row['width'] or 0):.2f}"),
            'height': float(f"{float(row['height'] or 0):.2f}")
        })
        
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    total = len(data)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    page_data = data[start:end]

    return jsonify({
        'status': 'success',
        'data': page_data,
        'total': total,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages
    })

@app.route('/export', methods=['POST'])
def export():
    req = request.get_json()
    if not req:
        return "Invalid Request", 400
        
    filters = req.get('filters', {})
    cols = req.get('selected_columns', [])
    
    if not cols:
        return "No columns selected", 400
        
    db = get_db()
    
    comp_ids = filters.get('company_id', '')
    if isinstance(comp_ids, list): comp_ids = [c for c in comp_ids if c]
    elif isinstance(comp_ids, str): comp_ids = [c for c in comp_ids.split(',') if c]
    else: comp_ids = []

    cat_ids = filters.get('category_id', '')
    if isinstance(cat_ids, list): cat_ids = [c for c in cat_ids if c]
    elif isinstance(cat_ids, str): cat_ids = [c for c in cat_ids.split(',') if c]
    else: cat_ids = []

    brand_ids = filters.get('brand_id', '')
    if isinstance(brand_ids, list): brand_ids = [c for c in brand_ids if c]
    elif isinstance(brand_ids, str): brand_ids = [c for c in brand_ids.split(',') if c]
    else: brand_ids = []

    status_ids = filters.get('status_id', '')
    if isinstance(status_ids, list): status_ids = [c for c in status_ids if c]
    elif isinstance(status_ids, str): status_ids = [c for c in status_ids.split(',') if c]
    else: status_ids = []
    
    zone = filters.get('zone', '').strip()
    
    locked_company = session.get('company_id')
    if locked_company:
        comp_ids = [str(locked_company)]
        
    query = """
        SELECT i.id, p.part_number, p.description, p.cost_price, p.reorder_point,
               i.quantity, i.zone as zone_location, c.name as subsidiary, cat.name as category,
               b.name as brand, s.name as status
        FROM inventory i
        JOIN parts p ON i.part_id = p.id
        JOIN companies c ON i.company_id = c.id
        LEFT JOIN categories cat ON p.category_id = cat.id
        LEFT JOIN brands b ON p.brand_id = b.id
        LEFT JOIN statuses s ON p.status_id = s.id
        WHERE 1=1
    """
    params = []
    
    if comp_ids:
        placeholders = ','.join('?' for _ in comp_ids)
        query += f" AND i.company_id IN ({placeholders})"
        params.extend(comp_ids)
    if cat_ids:
        placeholders = ','.join('?' for _ in cat_ids)
        query += f" AND p.category_id IN ({placeholders})"
        params.extend(cat_ids)
    if brand_ids:
        placeholders = ','.join('?' for _ in brand_ids)
        query += f" AND p.brand_id IN ({placeholders})"
        params.extend(brand_ids)
    if status_ids:
        placeholders = ','.join('?' for _ in status_ids)
        query += f" AND p.status_id IN ({placeholders})"
        params.extend(status_ids)
    if zone:
        query += " AND i.zone LIKE ?"
        params.append(f"%{zone}%")
        
    rows = db.execute(query, params).fetchall()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    headers = [c.replace('_', ' ').title() for c in cols]
    writer.writerow(headers)
    
    for row in rows:
        row_dict = dict(row)
        if 'zone_location' in cols and not row_dict.get('zone_location'):
            row_dict['zone_location'] = 'Unassigned'
            
        qty = float(row_dict.get('quantity') or 0)
        cost = float(row_dict.get('cost_price') or 0)
        reorder = float(row_dict.get('reorder_point') or 0)
        
        if 'total_value' in cols:
            row_dict['total_value'] = f"{qty * cost:.2f}"
            
        if 'health' in cols:
            row_dict['health'] = "Critical" if qty <= reorder else ("Warning" if qty <= reorder * 1.2 else "Healthy")
            
        writer.writerow([row_dict.get(c, '') for c in cols])
        
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename=Warehouse_Export_{int(time.time())}.csv"}
    )

# ═══════════════════════════════════════════
# DELIVERY LIFECYCLE MANAGEMENT
# ═══════════════════════════════════════════

@app.route('/delivery')
def delivery():
    db = get_db()
    user_id = session.get('user_id')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    trip_row = db.execute('''
        SELECT t.*, v.name as vehicle_name 
        FROM delivery_trips t
        LEFT JOIN vehicles v ON t.vehicle_id = v.id
        WHERE t.driver_id = ? AND t.status != 'Completed'
        ORDER BY t.created_at DESC LIMIT 1
    ''', (user_id,)).fetchone()
    
    trip = dict(trip_row) if trip_row else None
    
    activities = []
    total_count = 0
    role_name = session.get('role_name', '')
    is_admin = role_name == 'admin'
    if is_admin:
        customers = [dict(r) for r in db.execute("SELECT * FROM customers ORDER BY name").fetchall()]
    else:
        customers = [dict(r) for r in db.execute("SELECT * FROM customers WHERE salesperson_id = ? ORDER BY name", (user_id,)).fetchall()]
    activities_list = [dict(r) for r in db.execute("SELECT * FROM delivery_activities ORDER BY name").fetchall()]
    vehicles = [dict(r) for r in db.execute("SELECT * FROM vehicles WHERE status = 'Active' ORDER BY name").fetchall()]
    
    if trip:
        # User is in active trip
        total_count = db.execute("SELECT COUNT(*) FROM delivery_activity_logs WHERE trip_id = ?", (trip['id'],)).fetchone()[0]
        activities = db.execute('''
            SELECT l.*, c.name as customer_name 
            FROM delivery_activity_logs l
            LEFT JOIN customers c ON l.customer_id = c.id
            WHERE l.trip_id = ? 
            ORDER BY l.sequence_order DESC, l.timestamp DESC LIMIT ? OFFSET ?
        ''', (trip['id'], per_page, offset)).fetchall()
    
    return render_template('delivery.html', title="Strategic Logistics Hub",
                           trip=trip, activities=[dict(r) for r in activities],
                           customers=customers, activities_list=activities_list,
                           vehicles=vehicles,
                           total_count=total_count, per_page=per_page, page=page,
                           total_pages=(total_count + per_page - 1) // per_page,
                           offset=offset, is_admin=is_admin)

@app.route('/api/delivery/update_vehicle', methods=['POST'])
def delivery_update_vehicle():
    db = get_db()
    user_id = session.get('user_id')
    vehicle_id = request.form.get('vehicle_id')
    trip_id = request.form.get('trip_id')
    
    if vehicle_id and trip_id:
        db.execute('UPDATE delivery_trips SET vehicle_id = ? WHERE id = ? AND driver_id = ?', 
                   (vehicle_id, trip_id, user_id))
        db.commit()
        return jsonify({"status": "success", "msg": "Vehicle assigned to active mission."})
    return jsonify({"status": "error", "msg": "Missing vehicle or trip identifier."}), 400

@app.route('/api/delivery/edit_log', methods=['POST'])
def delivery_edit_log():
    db = get_db()
    log_id = request.form.get('id')
    new_time = request.form.get('timestamp')
    db.execute('UPDATE delivery_activity_logs SET timestamp = ? WHERE id = ?', (new_time, log_id))
    db.commit()
    return jsonify({"status": "success", "msg": "Precision Log Updated"})

@app.route('/api/delivery/move_log', methods=['POST'])
def delivery_move_log():
    db = get_db()
    log_id = request.form.get('id')
    direction = request.form.get('direction')
    current = db.execute('SELECT id, sequence_order, trip_id FROM delivery_activity_logs WHERE id = ?', (log_id,)).fetchone()
    if not current:
        return jsonify({"status": "error", "msg": "Log not found"}), 404
        
    seq = current['sequence_order']
    trip_id = current['trip_id']
    
    # "up" visually means moving to a HIGHER sequence_order in DESC list
    if direction == 'up':
        adjacent = db.execute('SELECT id, sequence_order FROM delivery_activity_logs WHERE trip_id = ? AND sequence_order > ? ORDER BY sequence_order ASC LIMIT 1', (trip_id, seq)).fetchone()
    else:
        adjacent = db.execute('SELECT id, sequence_order FROM delivery_activity_logs WHERE trip_id = ? AND sequence_order < ? ORDER BY sequence_order DESC LIMIT 1', (trip_id, seq)).fetchone()
        
    if adjacent:
        db.execute('UPDATE delivery_activity_logs SET sequence_order = ? WHERE id = ?', (adjacent['sequence_order'], current['id']))
        db.execute('UPDATE delivery_activity_logs SET sequence_order = ? WHERE id = ?', (seq, adjacent['id']))
        db.commit()
        return jsonify({"status": "success", "msg": "Order calibrated"})
    return jsonify({"status": "success", "msg": "Already at boundary"})

@app.route('/api/delivery/delete_log', methods=['POST'])
def delivery_delete_log():
    db = get_db()
    log_id = request.form.get('id')
    db.execute('DELETE FROM delivery_activity_logs WHERE id = ?', (log_id,))
    db.commit()
    return jsonify({"status": "success", "msg": "Event Log Excised"})

@app.route('/api/delivery/stop/delete', methods=['POST'])
def delivery_stop_delete():
    db = get_db()
    trip_id = request.form.get('trip_id')
    customer_id = request.form.get('customer_id')
    db.execute('''
        DELETE FROM delivery_activity_logs 
        WHERE trip_id = ? AND customer_id = ? 
        AND (activity_type LIKE 'Arrival%' OR activity_type LIKE 'Departure%')
    ''', (trip_id, customer_id))
    db.commit()
    return jsonify({"status": "success", "msg": "Transaction Stop Excised"})

@app.route('/api/delivery/stop/update', methods=['POST'])
def delivery_stop_update():
    db = get_db()
    trip_id = request.form.get('trip_id')
    customer_id = request.form.get('customer_id')
    arrival_time = request.form.get('arrival_time')
    departure_time = request.form.get('departure_time')
    
    # Update Arrival
    if arrival_time:
        exist = db.execute("SELECT id FROM delivery_activity_logs WHERE trip_id = ? AND customer_id = ? AND activity_type LIKE 'Arrival%'", (trip_id, customer_id)).fetchone()
        if exist:
            db.execute("UPDATE delivery_activity_logs SET timestamp = ? WHERE id = ?", (arrival_time, exist['id']))
        else:
            db.execute("INSERT INTO delivery_activity_logs (trip_id, customer_id, activity_type, timestamp) VALUES (?, ?, 'Arrival at Customer', ?)", (trip_id, customer_id, arrival_time))
    
    # Update Departure
    if departure_time:
        exist = db.execute("SELECT id FROM delivery_activity_logs WHERE trip_id = ? AND customer_id = ? AND activity_type LIKE 'Departure%'", (trip_id, customer_id)).fetchone()
        if exist:
            db.execute("UPDATE delivery_activity_logs SET timestamp = ? WHERE id = ?", (departure_time, exist['id']))
        else:
            db.execute("INSERT INTO delivery_activity_logs (trip_id, customer_id, activity_type, timestamp) VALUES (?, ?, 'Departure from Customer', ?)", (trip_id, customer_id, departure_time))
            
    db.commit()
    return jsonify({"status": "success", "msg": "Stop Metrics Synchronized"})

@app.route('/api/delivery/quick_log', methods=['POST'])
def delivery_quick_log():
    db = get_db()
    trip_id = request.form.get('trip_id')
    customer_id = request.form.get('customer_id')
    activity = request.form.get('type') # 'Arrival' or 'Departure'
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    label = "Arrival at Customer" if activity == 'Arrival' else "Departure from Customer"
    db.execute("INSERT INTO delivery_activity_logs (trip_id, customer_id, activity_type, timestamp) VALUES (?, ?, ?, ?)", 
               (trip_id, customer_id, label, now))
    db.commit()
    return jsonify({"status": "success", "msg": f"{activity} Logged"})

@app.route('/delivery/export_activities')
@admin_required
def delivery_export_activities():
    db = get_db()
    data = db.execute('''
        SELECT 
            l.id, l.timestamp, l.activity_type, 
            c.name as customer, c.location,
            u.username as driver
        FROM delivery_activity_logs l
        JOIN delivery_trips t ON l.trip_id = t.id
        JOIN users u ON t.driver_id = u.id
        LEFT JOIN customers c ON l.customer_id = c.id
        ORDER BY l.timestamp DESC
    ''').fetchall()

    wb = Workbook()
    ws = wb.active
    ws.title = "Tactical Distribution Audit"
    
    headers = ['Sequence ID', 'Chronometer Log', 'Activity Protocol', 'Associated Client', 'Geospatial Location', 'Driver']
    ws.append(headers)
    
    for row in data:
        ws.append(list(row))
        
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="10b981", end_color="10b981", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")

    filename = f"logistic_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    path = os.path.join(tempfile.gettempdir(), filename)
    wb.save(path)
    return send_file(path, as_attachment=True)

@app.route('/api/delivery/checkin', methods=['POST'])
def delivery_checkin():
    db = get_db()
    user_id = session.get('user_id')
    custom_time = request.form.get('custom_time') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    vehicle_id = request.form.get('vehicle_id')
    
    db.execute('''
        INSERT INTO delivery_trips (driver_id, vehicle_id, warehouse_checkin, status, date) 
        VALUES (?, ?, ?, "Loading", date("now"))
    ''', (user_id, vehicle_id, custom_time))
    db.commit()
    flash("Warehouse Arrival Logged.", "success")
    return redirect(url_for('delivery'))

@app.route('/api/delivery/warehouse_departure', methods=['POST'])
def delivery_wh_departure():
    db = get_db()
    user_id = session.get('user_id')
    custom_time = request.form.get('custom_time') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    trip = db.execute('SELECT id FROM delivery_trips WHERE driver_id = ? AND status = "Loading"', (user_id,)).fetchone()
    if not trip:
        flash("Record Arrival first.", "error")
        return redirect(url_for('delivery'))
        
    db.execute('UPDATE delivery_trips SET warehouse_departure = ?, status = "Active" WHERE id = ?', 
               (custom_time, trip['id']))
    db.commit()
    flash("Warehouse Departure Logged. Mission Accounted.", "success")
    return redirect(url_for('delivery'))

@app.route('/api/delivery/log_entry', methods=['POST'])
def delivery_log_entry():
    db = get_db()
    user_id = session.get('user_id')
    activity_type = request.form.get('activity')
    customer_id = request.form.get('customer_id') or None
    custom_time = request.form.get('custom_time') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    vehicle_id = request.form.get('vehicle_id')
    
    # 1. Ensure active trip
    trip = db.execute('SELECT id FROM delivery_trips WHERE driver_id = ? AND status != "Completed"', (user_id,)).fetchone()
    
    if not trip and activity_type == 'Arrival to warehouse':
         cursor = db.execute('''
            INSERT INTO delivery_trips (driver_id, vehicle_id, warehouse_checkin, status, date) 
            VALUES (?, ?, ?, "Active", date("now"))
         ''', (user_id, vehicle_id, custom_time))
         trip_id = cursor.lastrowid
    elif not trip:
        return jsonify({"status": "error", "msg": "No active mission log. Start by arriving at warehouse or select vehicle."}), 400
    else:
        trip_id = trip['id']

    max_order = db.execute('SELECT MAX(sequence_order) FROM delivery_activity_logs WHERE trip_id = ?', (trip_id,)).fetchone()[0] or 0
    new_order = max_order + 1

    db.execute('''
        INSERT INTO delivery_activity_logs (trip_id, activity_type, customer_id, timestamp, sequence_order)
        VALUES (?, ?, ?, ?, ?)
    ''', (trip_id, activity_type, customer_id, custom_time, new_order))
    
    db.commit()
    return jsonify({"status": "success", "msg": f"Registered: {activity_type}"})

@app.route('/api/delivery/arrival/<int:stop_id>', methods=['POST'])
def delivery_arrival(stop_id):
    db = get_db()
    custom_time = request.form.get('custom_time') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    gps = request.form.get('gps', 'Hidden')
    db.execute('UPDATE delivery_stops SET arrival_time = ?, arrival_gps = ?, status = "Arrived" WHERE id = ?', 
               (custom_time, gps, stop_id))
    db.commit()
    return jsonify({"status": "success", "msg": "Arrival Registered"})

@app.route('/api/delivery/departure/<int:stop_id>', methods=['POST'])
def delivery_departure(stop_id):
    db = get_db()
    custom_time = request.form.get('custom_time') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    gps = request.form.get('gps', 'Hidden')
    db.execute('UPDATE delivery_stops SET departure_time = ?, departure_gps = ?, status = "Departed" WHERE id = ?', 
               (custom_time, gps, stop_id))
    db.commit()
    return jsonify({"status": "success", "msg": "Departure Registered"})

@app.route('/api/delivery/complete/<int:trip_id>', methods=['POST'])
def delivery_complete(trip_id):
    db = get_db()
    custom_time = request.form.get('custom_time') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    db.execute('UPDATE delivery_trips SET warehouse_arrival = ?, status = "Completed" WHERE id = ?', 
               (custom_time, trip_id))
    db.commit()
    return redirect(url_for('delivery'))

@app.route('/delivery_report')
@admin_required
def delivery_report():
    db = get_db()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    date_filter = ""
    params = []
    if start_date and end_date:
        date_filter = " AND timestamp BETWEEN ? AND ?"
        params = [f"{start_date} 00:00:00", f"{end_date} 23:59:59"]
    
    # Summary Metrics (with date filter)
    trip_filter = ""
    t_params = []
    if start_date and end_date:
        trip_filter = " WHERE date BETWEEN ? AND ?"
        t_params = [start_date, end_date]

    total_trips = db.execute(f"SELECT COUNT(*) FROM delivery_trips {trip_filter}", t_params).fetchone()[0]
    total_activities = db.execute(f"SELECT COUNT(*) FROM delivery_activity_logs WHERE 1=1 {date_filter}", params).fetchone()[0]
    
    # Customer Stats (with date filter)
    # Using window function to calculate time difference to the previous activity based on sequence_order
    # This reflects "The time between this two activity consider as a delivery time for second customer"
    customer_stats = db.execute(f'''
        SELECT 
            c.name as customer,
            COUNT(DISTINCT l.trip_id) as visits,
            COALESCE(AVG(durations.diff_mins), 0) as avg_mins,
            COALESCE(SUM(durations.diff_mins), 0) as total_mins
        FROM (
            SELECT id, trip_id, customer_id, 
                   COALESCE((julianday(timestamp) - julianday(LAG(timestamp) OVER (PARTITION BY trip_id ORDER BY sequence_order ASC))) * 1440, 0) as diff_mins
            FROM delivery_activity_logs
            WHERE 1=1 {date_filter.replace('timestamp', 'timestamp')}
        ) durations
        JOIN delivery_activity_logs l ON durations.id = l.id
        JOIN customers c ON l.customer_id = c.id
        WHERE durations.diff_mins > 0
        GROUP BY c.id
        ORDER BY total_mins DESC
    ''', params).fetchall()

    # Delivery Order Stats
    order_stats = db.execute(f'''
        WITH TripDurations AS (
            SELECT l.id, l.trip_id, l.customer_id, l.sequence_order,
                   COALESCE((julianday(l.timestamp) - julianday(LAG(l.timestamp) OVER (PARTITION BY l.trip_id ORDER BY l.sequence_order ASC))) * 1440, 0) as diff_mins
            FROM delivery_activity_logs l
            WHERE 1=1 {date_filter.replace('timestamp', 'timestamp')}
        ),
        CustomerGroups AS (
            SELECT trip_id, customer_id, SUM(diff_mins) as total_mins, MIN(sequence_order) as min_seq
            FROM TripDurations
            WHERE diff_mins > 0 AND customer_id IS NOT NULL
            GROUP BY trip_id, customer_id
        ),
        RankedGroups AS (
            SELECT total_mins, RANK() OVER (PARTITION BY trip_id ORDER BY min_seq ASC) as delivery_order
            FROM CustomerGroups
        )
        SELECT delivery_order, COUNT(*) as deliveries_count, AVG(total_mins) as avg_mins
        FROM RankedGroups
        GROUP BY delivery_order
        ORDER BY delivery_order ASC
        LIMIT 10
    ''', params).fetchall()

    # Recent Logs (with date filter)
    # Note: Using the same params for recent logs
    recent_logs = db.execute(f'''
        SELECT l.*, c.name as customer_name, u.username as driver
        FROM delivery_activity_logs l
        JOIN delivery_trips t ON l.trip_id = t.id
        JOIN users u ON t.driver_id = u.id
        LEFT JOIN customers c ON l.customer_id = c.id
        WHERE 1=1 {date_filter}
        ORDER BY l.timestamp DESC LIMIT 100
    ''', params).fetchall()

    return render_template('delivery_report.html', title="Logistics Intelligence", 
                           total_trips=total_trips,
                           total_activities=total_activities,
                           customer_stats=[dict(r) for r in customer_stats],
                           order_stats=[dict(r) for r in order_stats],
                           recent_logs=[dict(r) for r in recent_logs],
                           start_date=start_date,
                           end_date=end_date)

@app.route('/api/reports/logistic_stats')
@admin_required
def api_logistic_stats():
    db = get_db()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    date_filter = ""
    params = []
    if start_date and end_date:
        date_filter = " AND timestamp BETWEEN ? AND ?"
        params = [f"{start_date} 00:00:00", f"{end_date} 23:59:59"]

    # Customer Time Bar Chart
    cust_data = db.execute(f'''
        SELECT c.name, SUM(durations.diff_mins) as total
        FROM (
            SELECT id, trip_id, customer_id, 
                   COALESCE((julianday(timestamp) - julianday(LAG(timestamp) OVER (PARTITION BY trip_id ORDER BY sequence_order ASC))) * 1440, 0) as diff_mins
            FROM delivery_activity_logs
            WHERE 1=1 {date_filter}
        ) durations
        JOIN delivery_activity_logs l ON durations.id = l.id
        JOIN customers c ON l.customer_id = c.id
        WHERE durations.diff_mins > 0
        GROUP BY c.id ORDER BY total DESC LIMIT 10
    ''', params).fetchall()
    
    # Activity Pie Chart
    # Use different param naming for single table
    act_filter = date_filter
    act_data = db.execute(f'''
        SELECT activity_type, COUNT(*) as count
        FROM delivery_activity_logs
        WHERE 1=1 {act_filter}
        GROUP BY activity_type
    ''', params).fetchall()

    # Deliveries Per Day (line/area chart)
    daily_data = db.execute(f'''
        SELECT DATE(timestamp) as day, COUNT(DISTINCT customer_id) as delivery_count
        FROM delivery_activity_logs
        WHERE customer_id IS NOT NULL AND activity_type LIKE '%Arrival%Customer%' {date_filter}
        GROUP BY DATE(timestamp)
        ORDER BY day ASC
    ''', params).fetchall()

    # Customer Visit Frequency (horizontal bar chart)
    visit_data = db.execute(f'''
        SELECT c.name, COUNT(DISTINCT DATE(l.timestamp)) as visit_days
        FROM delivery_activity_logs l
        JOIN customers c ON l.customer_id = c.id
        WHERE l.activity_type LIKE '%Arrival%Customer%' {date_filter}
        GROUP BY c.id
        ORDER BY visit_days DESC LIMIT 12
    ''', params).fetchall()

    return jsonify({
        "customers": [r['name'] for r in cust_data],
        "customer_times": [round(r['total'] or 0, 1) for r in cust_data],
        "activities": [r['activity_type'] for r in act_data],
        "activity_counts": [r['count'] for r in act_data],
        "daily_labels": [r['day'] for r in daily_data],
        "daily_deliveries": [r['delivery_count'] for r in daily_data],
        "visit_customers": [r['name'] for r in visit_data],
        "visit_counts": [r['visit_days'] for r in visit_data]
    })

@app.route('/delivery_settings', methods=['GET', 'POST'])
@admin_required
def delivery_settings():
    db = get_db()
    if request.method == 'POST':
        action = request.form.get('action')
        name = request.form.get('name', '').strip()
        
        if action == 'add' and name:
            try:
                db.execute('INSERT INTO delivery_activities (name) VALUES (?)', (name,))
                db.commit()
                flash(f"Logistics Protocol '{name}' added successfully.", "success")
            except:
                flash("Activity already exists or database error.", "error")
        elif action == 'delete':
            act_id = request.form.get('id')
            db.execute('DELETE FROM delivery_activities WHERE id = ?', (act_id,))
            db.commit()
            flash("Logistics Protocol removed from circulation.", "success")
        
        # Vehicle Management Actions
        elif action == 'vehicle_add':
            v_name = request.form.get('v_name', '').strip()
            v_plate = request.form.get('v_plate', '').strip()
            if v_name:
                db.execute('INSERT INTO vehicles (name, plate_number) VALUES (?, ?)', (v_name, v_plate))
                db.commit()
                flash(f"Vehicle '{v_name}' registered.", "success")
        elif action == 'vehicle_delete':
            v_id = request.form.get('v_id')
            db.execute('DELETE FROM vehicles WHERE id = ?', (v_id,))
            db.commit()
            flash("Vehicle decomissioned.", "success")
        elif action == 'vehicle_update':
            v_id = request.form.get('v_id')
            v_name = request.form.get('v_name', '').strip()
            v_plate = request.form.get('v_plate', '').strip()
            if v_id and v_name:
                db.execute('UPDATE vehicles SET name = ?, plate_number = ? WHERE id = ?', (v_name, v_plate, v_id))
                db.commit()
                flash(f"Vehicle '{v_name}' updated successfully.", "success")
            
    activities = db.execute('SELECT * FROM delivery_activities ORDER BY name').fetchall()
    vehicles = db.execute('SELECT * FROM vehicles ORDER BY name').fetchall()
    return render_template('delivery_settings.html', title="Delivery Settings", 
                           activities=[dict(r) for r in activities],
                           vehicles=[dict(r) for r in vehicles])

@app.route('/delivery/export')
@admin_required
def delivery_export():
    db = get_db()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    date_filter = ""
    params = []
    if start_date and end_date:
        date_filter = " AND l.timestamp BETWEEN ? AND ?"
        params = [f"{start_date} 00:00:00", f"{end_date} 23:59:59"]
        
    # High Fidelity Audit Logs
    data = db.execute(f'''
        SELECT 
            l.timestamp, u.username as driver, l.activity_type, 
            c.name as customer, c.location
        FROM delivery_activity_logs l
        JOIN delivery_trips t ON l.trip_id = t.id
        JOIN users u ON t.driver_id = u.id
        LEFT JOIN customers c ON l.customer_id = c.id
        WHERE 1=1 {date_filter}
        ORDER BY l.timestamp DESC
    ''', params).fetchall()

    wb = Workbook()
    
    # Sheet 1: Raw Transaction Ledger
    ws1 = wb.active
    ws1.title = "Transaction Ledger"
    headers1 = ['Chronometer Log', 'Operator', 'Activity Protocol', 'Client Association', 'Geospatial Location']
    ws1.append(headers1)
    for r in data: ws1.append(list(r))
    for cell in ws1[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="0ea5e9", end_color="0ea5e9", fill_type="solid")

    # Sheet 2: Efficiency Intelligence
    ws2 = wb.create_sheet("Efficiency Analytics")
    
    stats_filter = date_filter.replace('l.timestamp', 'l_arr.timestamp')
    cust_stats = db.execute(f'''
        SELECT c.name, COUNT(*), SUM((julianday(l_dep.timestamp) - julianday(l_arr.timestamp)) * 1440)
        FROM delivery_activity_logs l_arr
        JOIN delivery_activity_logs l_dep ON l_arr.trip_id = l_dep.trip_id AND l_arr.customer_id = l_dep.customer_id
        JOIN customers c ON l_arr.customer_id = c.id
        WHERE l_arr.activity_type LIKE 'Arrival at Customer' AND l_dep.activity_type LIKE 'Departure from Customer'
        {stats_filter}
        GROUP BY c.id
    ''', params).fetchall()
    
    ws2.append(['Customer Association', 'Total Engagements', 'Total Service Mins'])
    for r in cust_stats: ws2.append(list(r))
    for cell in ws2[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="10b981", end_color="10b981", fill_type="solid")

    filename = f"logistics_intelligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    path = os.path.join(tempfile.gettempdir(), filename)
    wb.save(path)
    return send_file(path, as_attachment=True)

@app.route('/delivery/customer_table/export')
@admin_required
def customer_delivery_table_export():
    db = get_db()
    
    # Reuse filtering logic or just export all for simplicity, 
    # but let's try to match current view if possible.
    filter_type = request.args.get('filter', 'today')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    date_filter = ""
    params = []
    today = datetime.now()
    if filter_type == 'today':
        date_filter = " AND l.timestamp >= ?"
        params.append(today.strftime('%Y-%m-%d') + " 00:00:00")
    elif filter_type == 'week':
        start_of_week = today - timedelta(days=today.weekday())
        date_filter = " AND l.timestamp >= ?"
        params.append(start_of_week.strftime('%Y-%m-%d') + " 00:00:00")
    elif filter_type == 'month':
        start_of_month = today.replace(day=1)
        date_filter = " AND l.timestamp >= ?"
        params.append(start_of_month.strftime('%Y-%m-%d') + " 00:00:00")
    elif filter_type == 'custom' and start_date and end_date:
        date_filter = " AND l.timestamp BETWEEN ? AND ?"
        params.append(start_date + " 00:00:00")
        params.append(end_date + " 23:59:59")

    logs = db.execute(f'''
        SELECT 
            l.trip_id, l.customer_id, l.activity_type, l.timestamp,
            c.name as customer_name, u.username as driver
        FROM delivery_activity_logs l
        JOIN delivery_trips t ON l.trip_id = t.id
        JOIN users u ON t.driver_id = u.id
        LEFT JOIN customers c ON l.customer_id = c.id
        WHERE c.id IS NOT NULL {date_filter}
        ORDER BY l.trip_id, l.timestamp ASC
    ''', params).fetchall()
    
    stops_map = {}
    trip_sequences = {}
    for log in logs:
        key = (log['trip_id'], log['customer_id'])
        if key not in stops_map:
            stops_map[key] = {
                'date': log['timestamp'].split(' ')[0] if log['timestamp'] else '',
                'customer_name': log['customer_name'],
                'driver': log['driver'],
                'arrival_time': None,
                'departure_time': None,
            }
            if log['trip_id'] not in trip_sequences: trip_sequences[log['trip_id']] = []
            trip_sequences[log['trip_id']].append(log['customer_id'])
        if 'Arrival' in log['activity_type']: stops_map[key]['arrival_time'] = log['timestamp']
        elif 'Departure' in log['activity_type']: stops_map[key]['departure_time'] = log['timestamp']

    wb = Workbook()
    ws = wb.active
    ws.title = "Customer Delivery Audit"
    ws.append(['Date', 'Customer', 'Driver', 'Arrival', 'Departure', 'Offloading (Min)', 'Delivery (Min)'])
    
    for trip_id, sequence in trip_sequences.items():
        prev_dep = None
        for cust_id in sequence:
            s = stops_map[(trip_id, cust_id)]
            off = ""
            deliv = ""
            if s['arrival_time'] and s['departure_time']:
                off = round((datetime.strptime(s['departure_time'], '%Y-%m-%d %H:%M:%S') - datetime.strptime(s['arrival_time'], '%Y-%m-%d %H:%M:%S')).total_seconds()/60, 1)
            if prev_dep and s['arrival_time']:
                deliv = round((datetime.strptime(s['arrival_time'], '%Y-%m-%d %H:%M:%S') - datetime.strptime(prev_dep, '%Y-%m-%d %H:%M:%S')).total_seconds()/60, 1)
            
            ws.append([s['date'], s['customer_name'], s['driver'], 
                       s['arrival_time'].split(' ')[1] if s['arrival_time'] else 'NA',
                       s['departure_time'].split(' ')[1] if s['departure_time'] else 'NA',
                       off, deliv])
            prev_dep = s['departure_time']

    # Header styling
    for cell in ws[1]:
        # openpyxl expects the color kwarg in lowercase; using Color raises TypeError
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="1e293b", end_color="1e293b", fill_type="solid")

    filename = f"customer_delivery_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    path = os.path.join(tempfile.gettempdir(), filename)
    wb.save(path)
    return send_file(path, as_attachment=True)

@app.route('/api/delivery/move_stop', methods=['POST'])
def delivery_move_stop():
    db = get_db()
    trip_id = request.form.get('trip_id')
    customer_id = request.form.get('customer_id')
    direction = request.form.get('direction')
    
    logs = db.execute('SELECT id, sequence_order, customer_id FROM delivery_activity_logs WHERE trip_id = ? ORDER BY sequence_order ASC', (trip_id,)).fetchall()
    
    blocks = []
    current_cust = None
    curr_block = []
    
    # We create contiguous blocks per customer so we can swap them intact
    for log in logs:
        # group warehouse (None) with adjacent blocks or standalone
        # simpler: just group by sequential customer_id blocks
        if log['customer_id'] != current_cust:
            if curr_block:
                blocks.append((current_cust, curr_block))
            current_cust = log['customer_id']
            curr_block = [log]
        else:
            curr_block.append(log)
    if curr_block:
        blocks.append((current_cust, curr_block))
        
    idx = -1
    for i, b in enumerate(blocks):
        if str(b[0]) == str(customer_id):
            idx = i
            break
            
    if idx == -1:
        return jsonify({"status": "error", "msg": "Stop not found"}), 404
        
    if direction == 'up' and idx > 0:
        blocks[idx], blocks[idx-1] = blocks[idx-1], blocks[idx]
    elif direction == 'down' and idx < len(blocks) - 1:
        blocks[idx], blocks[idx+1] = blocks[idx+1], blocks[idx]
    else:
        return jsonify({"status": "success", "msg": "Already at boundary"})
        
    new_seq = 1
    for cust, block in blocks:
        for log in block:
            db.execute('UPDATE delivery_activity_logs SET sequence_order = ? WHERE id = ?', (new_seq, log['id']))
            new_seq += 1
            
    db.commit()
    return jsonify({"status": "success", "msg": "Delivery order calibrated"})

@app.route('/delivery/customer_table')
@admin_required
def customer_delivery_table():
    try:
        db = get_db()
        
        # 1. Date Filtration Logic
        filter_type = request.args.get('filter', 'today')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        date_filter = ""
        params = []
        
        today = datetime.now()
        if filter_type == 'today':
            date_filter = " AND l.timestamp >= ?"
            params.append(today.strftime('%Y-%m-%d') + " 00:00:00")
        elif filter_type == 'week':
            # Start of current week (Monday)
            start_of_week = today - timedelta(days=today.weekday())
            date_filter = " AND l.timestamp >= ?"
            params.append(start_of_week.strftime('%Y-%m-%d') + " 00:00:00")
        elif filter_type == 'month':
            start_of_month = today.replace(day=1)
            date_filter = " AND l.timestamp >= ?"
            params.append(start_of_month.strftime('%Y-%m-%d') + " 00:00:00")
        elif filter_type == 'custom' and start_date and end_date:
            date_filter = " AND l.timestamp BETWEEN ? AND ?"
            params.extend([f"{start_date} 00:00:00", f"{end_date} 23:59:59"])
        
        # 2. Fetch all relevant logs
        # We need to sort by trip and then timestamp to process the sequence
        # 2a. Fetch customer activity logs (sorted by sequence_order)
        logs = db.execute(f'''
            SELECT 
                l.id, l.trip_id, l.customer_id, l.activity_type, l.timestamp,
                c.name as customer_name, u.username as driver,
                t.warehouse_departure
            FROM delivery_activity_logs l
            JOIN delivery_trips t ON l.trip_id = t.id
            JOIN users u ON t.driver_id = u.id
            LEFT JOIN customers c ON l.customer_id = c.id
            WHERE c.id IS NOT NULL {date_filter}
            ORDER BY l.trip_id, l.sequence_order ASC
        ''', params).fetchall()
        
        # 2b. Fetch ALL warehouse departure logs for trips that have customer logs today
        # These have customer_id IS NULL and contain 'Departure from Warehouse'
        # We need the departure time closest to (but before) the first customer arrival
        trip_ids_in_scope = set()
        for log in logs:
            trip_ids_in_scope.add(log['trip_id'])
        
        wh_dep_from_logs = {}
        for tid in trip_ids_in_scope:
            wh_log = db.execute('''
                SELECT timestamp FROM delivery_activity_logs 
                WHERE trip_id = ? AND customer_id IS NULL 
                  AND activity_type LIKE '%Departure%Warehouse%'
                ORDER BY timestamp DESC LIMIT 1
            ''', (tid,)).fetchone()
            if wh_log:
                wh_dep_from_logs[tid] = wh_log['timestamp']
        
        # 3. Process logs into Stops
        stops_map = {}
        trip_sequences = {}
        trip_wh_dep = {}
        
        for log in logs:
            key = (log['trip_id'], log['customer_id'])
            if key not in stops_map:
                ts_parts = log['timestamp'].split(' ') if log['timestamp'] else []
                ts_date = ts_parts[0] if len(ts_parts) > 0 else ''
                
                day_name = ''
                if ts_date:
                    try:
                        day_name = datetime.strptime(ts_date, '%Y-%m-%d').strftime('%A')
                    except:
                        day_name = 'Unknown'

                stops_map[key] = {
                    'trip_id': log['trip_id'],
                    'customer_id': log['customer_id'],
                    'customer_name': log['customer_name'],
                    'driver': log['driver'],
                    'arrival_time': log['timestamp'] if 'Arrival' in log['activity_type'] else None,
                    'arrival_log_id': log['id'] if 'Arrival' in log['activity_type'] else None,
                    'departure_time': log['timestamp'] if 'Departure' in log['activity_type'] else None,
                    'departure_log_id': log['id'] if 'Departure' in log['activity_type'] else None,
                    'timestamp': log['timestamp'],
                    'date': ts_date,
                    'day_name': day_name
                }
                
                if log['trip_id'] not in trip_sequences:
                    trip_sequences[log['trip_id']] = []
                trip_sequences[log['trip_id']].append(log['customer_id'])
                
                # Warehouse departure: prefer delivery_trips column, fallback to activity log
                if log['trip_id'] not in trip_wh_dep:
                    wh = log['warehouse_departure'] or wh_dep_from_logs.get(log['trip_id'])
                    trip_wh_dep[log['trip_id']] = wh
                
            if 'Arrival' in log['activity_type']:
                stops_map[key]['arrival_time'] = log['timestamp']
                stops_map[key]['arrival_log_id'] = log['id']
            elif 'Departure' in log['activity_type']:
                stops_map[key]['departure_time'] = log['timestamp']
                stops_map[key]['departure_log_id'] = log['id']

        # 4. Calculate Time Metrics
        def safe_parse_time(ts):
            """Try multiple timestamp formats"""
            if not ts:
                return None
            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S.%f'):
                try:
                    return datetime.strptime(ts.strip(), fmt)
                except:
                    continue
            return None
        
        final_stops = []
        for trip_id, sequence in trip_sequences.items():
            prev_departure = None
            order_idx = 1
            unique_seq = []
            for c in sequence:
                if c not in unique_seq: unique_seq.append(c)
            
            wh_dep = trip_wh_dep.get(trip_id)
                
            for cust_id in unique_seq:
                stop = stops_map[(trip_id, cust_id)]
                stop['delivery_order'] = order_idx
                
                # Offloading Time (Arrival to Departure at same customer)
                if stop['arrival_time'] and stop['departure_time']:
                    arr_dt = safe_parse_time(stop['arrival_time'])
                    dep_dt = safe_parse_time(stop['departure_time'])
                    if arr_dt and dep_dt:
                        diff = abs((dep_dt - arr_dt).total_seconds()) / 60
                        stop['offloading_time'] = round(diff, 1)
                    else:
                        stop['offloading_time'] = None
                else:
                    stop['offloading_time'] = None
                    
                # Delivery Time
                # 1st stop: warehouse_departure -> customer arrival
                # Subsequent: previous customer departure -> current customer arrival
                if order_idx == 1 and wh_dep and stop['arrival_time']:
                    wh_dt = safe_parse_time(wh_dep)
                    c_arr = safe_parse_time(stop['arrival_time'])
                    if wh_dt and c_arr:
                        diff = abs((c_arr - wh_dt).total_seconds()) / 60
                        stop['delivery_time'] = round(diff, 1)
                    else:
                        stop['delivery_time'] = None
                elif order_idx > 1 and prev_departure and stop['arrival_time']:
                    p_dep = safe_parse_time(prev_departure)
                    c_arr = safe_parse_time(stop['arrival_time'])
                    if p_dep and c_arr:
                        diff = abs((c_arr - p_dep).total_seconds()) / 60
                        stop['delivery_time'] = round(diff, 1)
                    else:
                        stop['delivery_time'] = None
                else:
                    stop['delivery_time'] = None
                    
                final_stops.append(stop)
                prev_departure = stop['departure_time']
                order_idx += 1

        # Sort final stops by delivery_order within each trip, then by date desc
        final_stops.sort(key=lambda x: (x.get('date', '') or '', x.get('delivery_order', 99)), reverse=False)
        final_stops.sort(key=lambda x: x.get('date', '') or '', reverse=True)

        return render_template('customer_delivery_table.html', 
                               title="Customer Delivery Table",
                               stops=final_stops,
                               filter_type=filter_type,
                               start_date=start_date,
                               end_date=end_date)
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        try:
            with open('error_log.txt', 'a') as f:
                f.write(f"\n--- {datetime.now()} ---\n")
                f.write(err_msg)
        except:
            pass
        return f"FATAL DEBUG: {str(e)}<br><pre>{err_msg}</pre>", 500

@app.route('/customers', methods=['GET', 'POST'])
def customers():
    db = get_db()
    if request.method == 'POST':
        # Add new customer logic
        name = request.form.get('name')
        phone = request.form.get('phone')
        location = request.form.get('location')
        c_type = request.form.get('type')
        salesperson_id = request.form.get('salesperson_id')
        working_hours = request.form.get('working_hours')
        working_days = request.form.get('working_days')
        
        db.execute('''
            INSERT INTO customers (name, phone, location, type, salesperson_id, working_hours, working_days)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, phone, location, c_type, salesperson_id, working_hours, working_days))
        db.commit()
        flash("Enterprise Client Registered Successfully", "success")
        return redirect(url_for('customers'))

    # Load all customers from local database (sdad_customers table - already synced data)
    customers_rows = db.execute('''
        SELECT
            s.id as sdad_id,
            s.customer_id as sdad_customer_id,
            s.name,
            s.username,
            s.email,
            s.phone,
            s.whatsapp_phone,
            s.location,
            s.country,
            s.city,
            s.state,
            s.address,
            s.postal_code,
            s.total_orders,
            s.total_payments,
            s.total_debt,
            s.credit_limit,
            s.credit_status,
            s.has_credit_enabled,
            s.payment_method,
            s.payment_deadline_days,
            s.last_purchase_date,
            s.salesperson_name,
            s.sales_team,
            s.brand_names,
            s.customer_group,
            s.customer_code,
            s.trn_number,
            s.is_credit_blocked,
            s.active,
            s.created_at,
            s.updated_at,
            s.local_customer_id
        FROM sdad_customers s
        ORDER BY s.total_orders DESC
    ''').fetchall()

    # Summary stats
    total_customers = db.execute("SELECT COUNT(*) as cnt FROM sdad_customers").fetchone()['cnt']
    active_customers = db.execute("SELECT COUNT(*) as cnt FROM sdad_customers WHERE active = 1").fetchone()['cnt']
    total_debt = db.execute("SELECT COALESCE(SUM(total_debt), 0) as t FROM sdad_customers").fetchone()['t']
    total_orders_sum = db.execute("SELECT COALESCE(SUM(total_orders), 0) as t FROM sdad_customers").fetchone()['t']
    countries_count = db.execute("SELECT COUNT(DISTINCT country) as cnt FROM sdad_customers WHERE country != ''").fetchone()['cnt']

    users_rows = db.execute("SELECT id, username FROM users ORDER BY username").fetchall()

    return render_template('customers.html', title="Client Registry",
                           customers=[dict(r) for r in customers_rows],
                           users=[dict(r) for r in users_rows],
                           stats={
                               'total': total_customers,
                               'active': active_customers,
                               'total_debt': total_debt,
                               'total_orders': total_orders_sum,
                               'countries': countries_count
                           })

@app.route('/customers/edit/<int:id>', methods=['POST'])
@admin_required
def edit_customer(id):
    db = get_db()
    name = request.form.get('name')
    phone = request.form.get('phone')
    location = request.form.get('location')
    c_type = request.form.get('type')
    salesperson_id = request.form.get('salesperson_id')
    working_hours = request.form.get('working_hours')
    working_days = request.form.get('working_days')
    
    db.execute('''
        UPDATE sdad_customers
        SET name = ?, phone = ?, location = ?, type = ?, salesperson_id = ?, working_hours = ?, working_days = ?
        WHERE id = ?
    ''', (name, phone, location, c_type, salesperson_id, working_hours, working_days, id))
    db.commit()
    flash("Enterprise Profile Synchronized", "success")
    return redirect(url_for('customers'))

@app.route('/customers/delete/<int:id>', methods=['POST'])
@admin_required
def delete_customer(id):
    db = get_db()
    db.execute("DELETE FROM sdad_customers WHERE id = ?", (id,))
    db.commit()
    flash("Client Profile Removed", "success")
    return redirect(url_for('customers'))

@app.route('/customers/sample-template')
@admin_required
def customers_sample_template():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Phone", "Location", "Type", "Salesperson_Username", "Working_Hours", "Working_Days"])
    writer.writerow(["Sample Motors", "050-0000000", "Dubai, UAE", "Wholesale", "admin", "08:30-17:30", "Sun-Thu"])
    
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=Customer_Import_Template.csv"}
    )


@app.route('/accounting')
@admin_required
def accounting():
    db = get_db()
    # Summary stats
    stats = db.execute('''
        SELECT 
            SUM(balance) as total_receivable,
            COUNT(CASE WHEN balance > credit_limit THEN 1 END) as over_limit_count,
            (SELECT SUM(amount) FROM customer_transactions WHERE type='Payment' AND transaction_date >= date('now', 'start of month')) as monthly_collections
        FROM customers
    ''').fetchone()
    
    # Recent transactions
    recent_tx = db.execute('''
        SELECT t.*, c.name as customer_name
        FROM customer_transactions t
        JOIN customers c ON t.customer_id = c.id
        ORDER BY t.transaction_date DESC
        LIMIT 10
    ''').fetchall()
    
    return render_template('accounting.html', title="Accounting Hub", stats=dict(stats), transactions=recent_tx)

@app.route('/accounting/customers')
@admin_required
def accounting_customers():
    db = get_db()
    customers = db.execute('''
        SELECT *, (balance / credit_limit * 100) as credit_usage
        FROM customers
        ORDER BY balance DESC
    ''').fetchall()
    return render_template('accounting_customers.html', title="Customer Balances", customers=customers)

@app.route('/accounting/transactions')
@admin_required
def accounting_transactions():
    db = get_db()
    transactions = db.execute('''
        SELECT t.*, c.name as customer_name
        FROM customer_transactions t
        JOIN customers c ON t.customer_id = c.id
        ORDER BY t.transaction_date DESC
    ''').fetchall()
    return render_template('accounting_transactions.html', title="Financial Ledger", transactions=transactions)

@app.route('/customers/import', methods=['POST'])
@admin_required
def customers_import():
    if 'file' not in request.files:
        flash("No file part", "error")
        return redirect(url_for('customers'))
        
    file = request.files['file']
    if file.filename == '':
        flash("No selected file", "error")
        return redirect(url_for('customers'))
        
    if file and file.filename.endswith('.csv'):
        stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
        reader = csv.DictReader(stream)
        
        db = get_db()
        success_count = 0
        error_count = 0
        
        # Pre-fetch usernames for resolution
        users = {u['username']: u['id'] for u in db.execute("SELECT id, username FROM users").fetchall()}
        
        for row in reader:
            try:
                name = row.get('Name')
                phone = row.get('Phone')
                location = row.get('Location')
                c_type = row.get('Type')
                sp_user = row.get('Salesperson_Username', 'admin')
                hours = row.get('Working_Hours', '08:00-17:00')
                days = row.get('Working_Days', 'Daily')
                
                sp_id = users.get(sp_user, users.get('admin', 1))
                
                if name:
                    db.execute('''
                        INSERT INTO customers (name, phone, location, type, salesperson_id, working_hours, working_days)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (name, phone, location, c_type, sp_id, hours, days))
                    success_count += 1
            except Exception as e:
                print(f"Import Error: {e}")
                error_count += 1
                
        db.commit()
        flash(f"Data Ingest Complete: {success_count} records imported. {error_count} failures.", "success")
    else:
        flash("Invalid file format. Please use CSV.", "error")
        
    return redirect(url_for('customers'))

@app.route('/customers/export')
@admin_required
def customers_export():
    db = get_db()
    rows = db.execute('''
        SELECT c.*, u.username as salesperson_name
        FROM customers c
        LEFT JOIN users u ON c.salesperson_id = u.id
        ORDER BY c.name ASC
    ''').fetchall()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Client Registry"
    
    headers = ["Name", "Phone", "Location", "Type", "Sales Representative", "Working Hours", "Working Days"]
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_num, value=header)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="0EA5E9", end_color="0EA5E9", fill_type="solid")
        cell.alignment = Alignment(horizontal="center")
        
    for r_idx, row in enumerate(rows, 2):
        ws.cell(row=r_idx, column=1, value=row['name'])
        ws.cell(row=r_idx, column=2, value=row['phone'])
        ws.cell(row=r_idx, column=3, value=row['location'])
        ws.cell(row=r_idx, column=4, value=row['type'])
        ws.cell(row=r_idx, column=5, value=row['salesperson_name'])
        ws.cell(row=r_idx, column=6, value=row['working_hours'])
        ws.cell(row=r_idx, column=7, value=row['working_days'])
        
    # Standard auto-width logic
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except: pass
        ws.column_dimensions[column].width = max_length + 5

    filename = f"Client_Registry_{datetime.now().strftime('%Y%m%d')}.xlsx"
    path = os.path.join(tempfile.gettempdir(), filename)
    wb.save(path)
    return send_file(path, as_attachment=True)

def get_effective_hs_expression(inv_alias='i', part_alias='p'):
    return (
        f"CASE "
        f"WHEN {inv_alias}.hs_code IS NOT NULL THEN NULLIF(TRIM({inv_alias}.hs_code), '') "
        f"ELSE NULLIF(TRIM({part_alias}.hs_code), '') "
        f"END"
    )


def build_inventory_dashboard_sql(report_mode, q_part='', q_hs='', f_warehouses=None,
                                  f_brands=None, f_status='all', sort_by=None, sort_dir='asc'):
    report_mode = 'hs' if report_mode == 'hs' else 'part'
    f_warehouses = f_warehouses or []
    f_brands = f_brands or []
    sort_dir = 'desc' if str(sort_dir).lower() == 'desc' else 'asc'

    effective_hs = get_effective_hs_expression('i', 'p')
    base_from = '''
        FROM inventory i
        LEFT JOIN parts p ON i.part_id = p.id
        LEFT JOIN warehouses w ON i.warehouse_id = w.id
        LEFT JOIN companies company_direct ON i.company_id = company_direct.id
        LEFT JOIN companies company_warehouse ON w.company_id = company_warehouse.id
        LEFT JOIN brands b ON p.brand_id = b.id
        WHERE 1=1
    '''
    params = []

    if q_part:
        base_from += " AND COALESCE(p.part_number, '') LIKE ?"
        params.append(f"%{q_part}%")
    if q_hs:
        base_from += f" AND COALESCE({effective_hs}, '') LIKE ?"
        params.append(f"%{q_hs}%")
    if f_warehouses:
        placeholders = ', '.join(['?'] * len(f_warehouses))
        base_from += f" AND i.warehouse_id IN ({placeholders})"
        params.extend(f_warehouses)
    if f_brands:
        placeholders = ', '.join(['?'] * len(f_brands))
        base_from += f" AND p.brand_id IN ({placeholders})"
        params.extend(f_brands)

    if report_mode == 'hs':
        base_query = f'''
            SELECT
                {effective_hs} as hs_code,
                COUNT(DISTINCT p.id) as part_count,
                GROUP_CONCAT(DISTINCT COALESCE(p.part_number, 'HS Independent Record')) as part_numbers,
                GROUP_CONCAT(DISTINCT COALESCE(p.description, 'No description')) as descriptions,
                SUM(i.quantity) as quantity,
                GROUP_CONCAT(DISTINCT COALESCE(w.name, company_direct.name, 'Unassigned')) as warehouse_names,
                GROUP_CONCAT(DISTINCT COALESCE(company_warehouse.name, company_direct.name, 'Unassigned')) as company_names,
                GROUP_CONCAT(DISTINCT COALESCE(b.name, 'Standard')) as brand_names,
                GROUP_CONCAT(DISTINCT COALESCE(p.supplier, 'Standard')) as suppliers
            {base_from}
            AND {effective_hs} IS NOT NULL
            GROUP BY {effective_hs}
        '''
        if f_status == 'in_stock':
            base_query += " HAVING SUM(i.quantity) > 10"
        elif f_status == 'low':
            base_query += " HAVING SUM(i.quantity) > 0 AND SUM(i.quantity) <= 10"
        elif f_status == 'out':
            base_query += " HAVING SUM(i.quantity) = 0"

        sort_map = {
            'hs_code': 'hs_code',
            'part_count': 'part_count',
            'quantity': 'quantity',
            'warehouse': 'warehouse_names',
            'brand': 'brand_names',
            'supplier': 'suppliers',
        }
        sort_by = sort_by if sort_by in sort_map else 'hs_code'
    else:
        base_query = f'''
            SELECT
                i.id as inv_id,
                p.id as part_id,
                p.part_number,
                p.description,
                {effective_hs} as hs_code,
                COALESCE(p.supplier, 'Standard') as supplier,
                COALESCE(company_warehouse.name, company_direct.name, 'Unassigned') as company_name,
                COALESCE(w.name, company_direct.name, 'Unassigned') as warehouse_name,
                i.quantity,
                i.zone,
                COALESCE(b.name, 'Standard') as brand_name,
                i.receiving_date,
                i.reserved_customer
            {base_from}
        '''
        # Part report should only show rows that are actually linked to a usable part number.
        base_query += " AND TRIM(COALESCE(p.part_number, '')) != ''"
        if f_status == 'in_stock':
            base_query += " AND i.quantity > 10"
        elif f_status == 'low':
            base_query += " AND i.quantity > 0 AND i.quantity <= 10"
        elif f_status == 'out':
            base_query += " AND i.quantity = 0"

        sort_map = {
            'part_number': 'part_number',
            'brand': 'brand_name',
            'quantity': 'quantity',
            'warehouse': 'warehouse_name',
            'company': 'company_name',
            'hs_code': 'hs_code',
            'supplier': 'supplier',
            'receiving_date': 'receiving_date',
            'reserved_customer': 'reserved_customer',
        }
        sort_by = sort_by if sort_by in sort_map else 'part_number'

    order_clause = f"{sort_map[sort_by]} {'DESC' if sort_dir == 'desc' else 'ASC'}"
    return base_query, params, order_clause, sort_by, sort_dir


@app.route('/dashboard')
@admin_required
def inventory_dashboard():
    db = get_db()

    # Auto-sync with Peyvast on every page load
    try:
        sync_manager = PeyvastSyncManager()
        sync_manager.ensure_sync_schema()
        sync_manager.sync_all()
    except Exception as e:
        pass  # Silent fail, show existing data

    q_part = request.args.get('q_part', '').strip()
    q_hs = request.args.get('q_hs', '').strip()
    f_warehouses = request.args.getlist('f_warehouse')
    f_brands = request.args.getlist('f_brand')
    f_status = request.args.get('f_status', 'all')
    report_mode = request.args.get('report_mode', 'part')
    sort_by = request.args.get('sort_by')
    sort_dir = request.args.get('sort_dir', 'asc')
    page = max(request.args.get('page', 1, type=int), 1)
    per_page = 100

    base_query, params, order_clause, sort_by, sort_dir = build_inventory_dashboard_sql(
        report_mode=report_mode,
        q_part=q_part,
        q_hs=q_hs,
        f_warehouses=f_warehouses,
        f_brands=f_brands,
        f_status=f_status,
        sort_by=sort_by,
        sort_dir=sort_dir
    )

    total_count = db.execute(
        f"SELECT COUNT(*) FROM ({base_query}) dashboard_rows",
        params
    ).fetchone()[0]
    total_pages = max((total_count + per_page - 1) // per_page, 1) if total_count else 1
    if page > total_pages:
        page = total_pages

    offset = (page - 1) * per_page
    items = [
        dict(row) for row in db.execute(
            f"{base_query} ORDER BY {order_clause} LIMIT ? OFFSET ?",
            params + [per_page, offset]
        ).fetchall()
    ]

    warehouses = db.execute('''
        SELECT w.id, w.name, c.name as company_name
        FROM warehouses w
        LEFT JOIN companies c ON w.company_id = c.id
        ORDER BY c.name, w.name
    ''').fetchall()
    brands = db.execute("SELECT id, name FROM brands ORDER BY name").fetchall()

    filter_options = {
        'warehouses': [dict(row) for row in warehouses],
        'brands': [dict(row) for row in brands]
    }
    page_window = list(range(max(1, page - 2), min(total_pages, page + 2) + 1))
    page_start = offset + 1 if total_count else 0
    page_end = offset + len(items)

    return render_template(
        'dashboard.html',
        title="Inventory Dashboard",
        items=items,
        filter_options=filter_options,
        report_mode=report_mode,
        total_count=total_count,
        page=page,
        total_pages=total_pages,
        page_window=page_window,
        page_start=page_start,
        page_end=page_end,
        per_page=per_page,
        sort_by=sort_by,
        sort_dir=sort_dir
    )


@app.route('/dashboard/export')
@admin_required
def export_inventory():
    db = get_db()

    q_part = request.args.get('q_part', '').strip()
    q_hs = request.args.get('q_hs', '').strip()
    f_warehouses = request.args.getlist('f_warehouse')
    f_brands = request.args.getlist('f_brand')
    f_status = request.args.get('f_status', 'all')
    report_mode = request.args.get('report_mode', 'part')
    sort_by = request.args.get('sort_by')
    sort_dir = request.args.get('sort_dir', 'asc')

    base_query, params, order_clause, _, _ = build_inventory_dashboard_sql(
        report_mode=report_mode,
        q_part=q_part,
        q_hs=q_hs,
        f_warehouses=f_warehouses,
        f_brands=f_brands,
        f_status=f_status,
        sort_by=sort_by,
        sort_dir=sort_dir
    )
    rows = [
        dict(row) for row in db.execute(
            f"{base_query} ORDER BY {order_clause}",
            params
        ).fetchall()
    ]

    if report_mode == 'hs':
        export_rows = [{
            'HS Code': row['hs_code'] or 'N/A',
            'Included Parts': row['part_numbers'] or 'HS Independent Record',
            'Part Count': row['part_count'],
            'Total Qty': row['quantity'],
            'Warehouses': row['warehouse_names'] or 'Unassigned',
            'Companies': row['company_names'] or 'Unassigned',
            'Brands': row['brand_names'] or 'Standard',
            'Suppliers': row['suppliers'] or 'Standard'
        } for row in rows]
    else:
        export_rows = [{
            'Part Number': row['part_number'] or 'HS Independent Record',
            'Description': row['description'] or 'No description',
            'Brand': row['brand_name'],
            'Qty': row['quantity'],
            'Warehouse': row['warehouse_name'],
            'Company': row['company_name'],
            'Zone': row['zone'] or 'Unassigned',
            'HS Code': row['hs_code'] or 'N/A',
            'Supplier': row['supplier'] or 'Standard',
            'Receiving Date': row['receiving_date'] or '--',
            'Reserved Customer': row['reserved_customer'] or 'Available'
        } for row in rows]

    df = pd.DataFrame(export_rows)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name=f'inventory_{report_mode}_{datetime.now().strftime("%Y%m%d")}.xlsx'
    )

@app.route('/dashboard/template/<t_type>')
@admin_required
def download_template(t_type):
    output = io.BytesIO()
    wb = Workbook()
    ws = wb.active
    
    if t_type == 'entry':
        ws.append(['Description', 'Qty', 'Amount', 'Gr Weight', 'COO', 'HS Code'])
    elif t_type == 'exit' or t_type == 'transfer':
        ws.append(['Part Number', 'Qty'])
        
    wb.save(output)
    output.seek(0)
    
    filename = f"MMD_{t_type}_template.xlsx"
    return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     as_attachment=True, download_name=filename)

@app.route('/dashboard/entry', methods=['GET', 'POST'])
@admin_required
def dash_entry():
    db = get_db()
    if request.method == 'POST':
        method = request.form.get('entry_method', 'part')
        warehouse_id = request.form.get('warehouse_id')
        supplier = request.form.get('supplier', '').strip()
        receiving_date = request.form.get('receiving_date', '').strip()
        
        rows = []
        if method == 'part':
            bulk_data = request.form.get('bulk_data', '')
            for line in bulk_data.splitlines():
                parts_data = line.strip().split('\t')
                if len(parts_data) < 2: parts_data = line.strip().split(',')
                if len(parts_data) >= 2:
                    rows.append({'part_number': parts_data[0].strip(), 'qty': parts_data[1].strip()})
        elif method == 'hs':
            hs_bulk_data = request.form.get('hs_bulk_data', '')
            for line in hs_bulk_data.splitlines():
                cols = line.strip().split('\t')
                if len(cols) < 6: cols = line.strip().split(',')
                if len(cols) >= 6:
                    rows.append({'description': cols[0].strip(), 'qty': cols[1].strip(), 'hs_code': cols[5].strip()})
        elif method == 'excel':
            file = request.files.get('excel_file')
            if file and file.filename.endswith(('.xlsx', '.xls')):
                try:
                    df = pd.read_excel(file)
                    for _, r in df.iterrows():
                        if 'Part Number' in df.columns:
                            rows.append({'part_number': str(r['Part Number']), 'qty': r['Qty']})
                        elif 'HS Code' in df.columns:
                            rows.append({'description': r.get('Description', ''), 'qty': r['Qty'], 'hs_code': str(r['HS Code'])})
                except Exception as e:
                    flash(f"Excel Error: {str(e)}", "error")

        if rows and warehouse_id:
            wh = db.execute("SELECT company_id FROM warehouses WHERE id = ?", (warehouse_id,)).fetchone()
            company_id = wh['company_id'] if wh else None
            
            if company_id:
                count = 0
                errors = 0
                for item in rows:
                    part_number = item.get('part_number')
                    hs_code = item.get('hs_code')
                    try:
                        qty = int(float(str(item.get('qty', 0))))
                    except:
                        qty = 0
                    
                    if qty <= 0: continue
                    
                    pid = None
                    if part_number:
                        pt = db.execute("SELECT id FROM parts WHERE part_number = ?", (part_number,)).fetchone()
                        if pt: pid = pt['id']
                    
                    if not pid and hs_code:
                        pt = db.execute("SELECT id FROM parts WHERE hs_code = ? LIMIT 1", (hs_code,)).fetchone()
                        if pt: pid = pt['id']
                    
                    # Auto-create part if it's an HS entry and part not found
                    if not pid and hs_code:
                        # Required: part_number is NOT NULL. Use HS Code as part_number.
                        db.execute("INSERT INTO parts (part_number, hs_code, description) VALUES (?, ?, ?)",
                                   (hs_code, hs_code, item.get('description', 'Auto-created from HS Import')))
                        pid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
                    
                    if pid:
                        if supplier:
                            db.execute("UPDATE parts SET supplier = ? WHERE id = ?", (supplier, pid))
                        
                        inv = db.execute("SELECT id FROM inventory WHERE part_id = ? AND warehouse_id = ?", (pid, warehouse_id)).fetchone()
                        if inv:
                            db.execute("UPDATE inventory SET quantity = quantity + ?, receiving_date = ? WHERE part_id = ? AND warehouse_id = ?", 
                                       (qty, receiving_date, pid, warehouse_id))
                        else:
                            db.execute("INSERT INTO inventory (part_id, company_id, warehouse_id, quantity, receiving_date) VALUES (?, ?, ?, ?, ?)",
                                       (pid, company_id, warehouse_id, qty, receiving_date))
                            
                        db.execute("INSERT INTO movements (part_id, company_id, warehouse_id, user_id, movement_type, quantity) VALUES (?, ?, ?, ?, 'IN', ?)",
                                   (pid, company_id, warehouse_id, session['user_id'], qty))
                        count += 1
                    else:
                        errors += 1
                db.commit()
                msg = f"Import successful: {count} items processed."
                if errors > 0: msg += f" ({errors} items failed/not found)."
                flash(msg, "success" if errors == 0 else "warning")
                return redirect(url_for('inventory_dashboard'))
    
    parts = db.execute("SELECT id, part_number, description FROM parts ORDER BY part_number").fetchall()
    warehouses = db.execute("SELECT w.*, c.name as company_name FROM warehouses w JOIN companies c ON w.company_id = c.id ORDER BY c.name, w.name").fetchall()
    suppliers = db.execute("SELECT * FROM suppliers WHERE status = 'Active' ORDER BY name").fetchall()
    return render_template('dash_entry.html', title="Stock Entry", parts=parts, warehouses=warehouses, suppliers=suppliers)

@app.route('/dashboard/exit', methods=['GET', 'POST'])
@admin_required
def dash_exit():
    db = get_db()
    if request.method == 'POST':
        method = request.form.get('entry_method', 'part')
        warehouse_id = request.form.get('warehouse_id')
        customer = request.form.get('customer', '').strip()
        
        rows = []
        if method == 'part':
            bulk_data = request.form.get('bulk_data', '')
            for line in bulk_data.splitlines():
                parts_data = line.strip().split('\t')
                if len(parts_data) < 2: parts_data = line.strip().split(',')
                if len(parts_data) >= 2:
                    rows.append({'part_number': parts_data[0].strip(), 'qty': parts_data[1].strip()})
        elif method == 'hs':
            hs_bulk_data = request.form.get('hs_bulk_data', '')
            for line in hs_bulk_data.splitlines():
                cols = line.strip().split('\t')
                if len(cols) < 6: cols = line.strip().split(',')
                if len(cols) >= 6:
                    rows.append({'description': cols[0].strip(), 'qty': cols[1].strip(), 'hs_code': cols[5].strip()})
        elif method == 'excel':
            file = request.files.get('excel_file')
            if file and file.filename.endswith(('.xlsx', '.xls')):
                try:
                    df = pd.read_excel(file)
                    for _, r in df.iterrows():
                        if 'Part Number' in df.columns:
                            rows.append({'part_number': str(r['Part Number']), 'qty': r['Qty']})
                        elif 'HS Code' in df.columns:
                            rows.append({'description': r.get('Description', ''), 'qty': r['Qty'], 'hs_code': str(r['HS Code'])})
                except Exception as e:
                    flash(f"Excel Error: {str(e)}", "error")

        if rows and warehouse_id:
            wh = db.execute("SELECT company_id FROM warehouses WHERE id = ?", (warehouse_id,)).fetchone()
            company_id = wh['company_id'] if wh else None
            
            if company_id:
                count = 0
                errors = 0
                for item in rows:
                    part_number = item.get('part_number')
                    hs_code = item.get('hs_code')
                    try:
                        qty = int(float(str(item.get('qty', 0))))
                    except:
                        qty = 0
                        
                    if qty <= 0: continue
                    
                    pid = None
                    if part_number:
                        pt = db.execute("SELECT id FROM parts WHERE part_number = ?", (part_number,)).fetchone()
                        if pt: pid = pt['id']
                    
                    if not pid and hs_code:
                        pt = db.execute("SELECT id FROM parts WHERE hs_code = ? LIMIT 1", (hs_code,)).fetchone()
                        if pt: pid = pt['id']
                        
                    if pid:
                        inv = db.execute("SELECT id, quantity FROM inventory WHERE part_id = ? AND warehouse_id = ?", (pid, warehouse_id)).fetchone()
                        if inv and inv['quantity'] >= qty:
                            db.execute("UPDATE inventory SET quantity = quantity - ?, reserved_customer = ? WHERE part_id = ? AND warehouse_id = ?", 
                                       (qty, customer, pid, warehouse_id))
                            db.execute("INSERT INTO movements (part_id, company_id, warehouse_id, user_id, movement_type, quantity, reference) VALUES (?, ?, ?, ?, 'OUT', ?, ?)",
                                       (pid, company_id, warehouse_id, session['user_id'], qty, customer))
                            count += 1
                        else:
                            errors += 1
                    else:
                        errors += 1
                db.commit()
                msg = f"Exit successful: {count} items processed."
                if errors > 0: msg += f" ({errors} items failed/insufficient stock)."
                flash(msg, "success" if errors == 0 else "warning")
                return redirect(url_for('inventory_dashboard'))
            
    parts = db.execute("SELECT id, part_number, description FROM parts ORDER BY part_number").fetchall()
    warehouses = db.execute("SELECT w.*, c.name as company_name FROM warehouses w JOIN companies c ON w.company_id = c.id ORDER BY c.name, w.name").fetchall()
    return render_template('dash_exit.html', title="Stock Exit", parts=parts, warehouses=warehouses)

@app.route('/dashboard/transfer', methods=['GET', 'POST'])
@admin_required
def dash_transfer():
    db = get_db()
    if request.method == 'POST':
        method = request.form.get('entry_method', 'part')
        src_id = request.form.get('src_warehouse_id')
        dest_id = request.form.get('dest_warehouse_id')
        
        rows = []
        if method == 'part' or method == 'hs': # Transfer uses Part/HS lookup similarly
            bulk_data = request.form.get('bulk_data', '') if method == 'part' else request.form.get('hs_bulk_data', '')
            for line in bulk_data.splitlines():
                parts_data = line.strip().split('\t')
                if len(parts_data) < 2: parts_data = line.strip().split(',')
                if method == 'part' and len(parts_data) >= 2:
                    rows.append({'part_number': parts_data[0].strip(), 'qty': parts_data[1].strip()})
                elif method == 'hs' and len(parts_data) >= 6:
                    rows.append({'hs_code': parts_data[5].strip(), 'qty': parts_data[1].strip()})
        elif method == 'excel':
            file = request.files.get('excel_file')
            if file and file.filename.endswith(('.xlsx', '.xls')):
                try:
                    df = pd.read_excel(file)
                    for _, r in df.iterrows():
                        rows.append({'part_number': str(r['Part Number']), 'qty': r['Qty']})
                except Exception as e:
                    flash(f"Excel Error: {str(e)}", "error")

        if rows and src_id and dest_id and src_id != dest_id:
            src_wh = db.execute("SELECT company_id FROM warehouses WHERE id = ?", (src_id,)).fetchone()
            dest_wh = db.execute("SELECT company_id FROM warehouses WHERE id = ?", (dest_id,)).fetchone()
            src_company_id = src_wh['company_id'] if src_wh else None
            dest_company_id = dest_wh['company_id'] if dest_wh else None
            
            if src_company_id and dest_company_id:
                count = 0
                errors = 0
                for item in rows:
                    part_number = item.get('part_number')
                    hs_code = item.get('hs_code')
                    try:
                        qty = int(float(str(item.get('qty', 0))))
                    except:
                        qty = 0
                        
                    if qty > 0:
                        pid = None
                        target_hs = None

                        if part_number:
                            pt = db.execute("SELECT id FROM parts WHERE part_number = ?", (part_number,)).fetchone()
                            if pt: pid = pt['id']
                        
                        if not pid and hs_code:
                            pt = db.execute("SELECT id FROM parts WHERE hs_code = ? LIMIT 1", (hs_code,)).fetchone()
                            if pt: 
                                pid = pt['id']
                            else:
                                target_hs = hs_code

                        if pid:
                            inv_src = db.execute("SELECT id, quantity FROM inventory WHERE part_id = ? AND warehouse_id = ?", (pid, src_id)).fetchone()
                            if inv_src and inv_src['quantity'] >= qty:
                                db.execute("INSERT INTO movements (part_id, company_id, warehouse_id, user_id, movement_type, quantity) VALUES (?, ?, ?, ?, 'TRANSFER OUT', ?)",
                                           (pid, src_company_id, src_id, session['user_id'], qty))
                                
                                inv_dest = db.execute("SELECT id FROM inventory WHERE part_id = ? AND warehouse_id = ?", (pid, dest_id)).fetchone()
                                if inv_dest:
                                    db.execute("UPDATE inventory SET quantity = quantity + ? WHERE part_id = ? AND warehouse_id = ?", (qty, pid, dest_id))
                                else:
                                    db.execute("INSERT INTO inventory (part_id, company_id, warehouse_id, quantity) VALUES (?, ?, ?, ?)", (pid, dest_company_id, dest_id, qty))
                                db.execute("INSERT INTO movements (part_id, company_id, warehouse_id, user_id, movement_type, quantity) VALUES (?, ?, ?, ?, 'TRANSFER IN', ?)",
                                           (pid, dest_company_id, dest_id, session['user_id'], qty))
                                count += 1
                            else:
                                errors += 1
                        else:
                            errors += 1
                db.commit()
                msg = f"Transfer successful: {count} items processed."
                if errors > 0: msg += f" ({errors} items failed/insufficient stock)."
                flash(msg, "success" if errors == 0 else "warning")
                return redirect(url_for('inventory_dashboard'))
            
    parts = db.execute("SELECT id, part_number, description FROM parts ORDER BY part_number").fetchall()
    warehouses = db.execute("SELECT w.*, c.name as company_name FROM warehouses w JOIN companies c ON w.company_id = c.id ORDER BY c.name, w.name").fetchall()
    return render_template('dash_transfer.html', title="Stock Transfer", parts=parts, warehouses=warehouses)

@app.route('/hs-codes')
@admin_required
def hs_codes():
    db = get_db()
    
    # Cumulative HS Code summary
    hs_summary = db.execute('''
        SELECT COALESCE(i.hs_code, p.hs_code) as hs_code,
               COUNT(DISTINCT p.id) as part_count,
               SUM(i.quantity) as total_qty,
               SUM(i.quantity * COALESCE(p.cost_price, 0)) as total_val
        FROM inventory i
        LEFT JOIN parts p ON i.part_id = p.id
        WHERE COALESCE(i.hs_code, p.hs_code) IS NOT NULL
              AND COALESCE(i.hs_code, p.hs_code) != ''
        GROUP BY COALESCE(i.hs_code, p.hs_code)
        ORDER BY total_qty DESC
    ''').fetchall()
    
    # HS Code by Company
    hs_company = db.execute('''
        SELECT COALESCE(i.hs_code, p.hs_code) as hs_code, c.name as company, SUM(i.quantity) as total_qty,
               SUM(i.quantity * COALESCE(p.cost_price, 0)) as total_val
        FROM inventory i
        LEFT JOIN parts p ON i.part_id = p.id
        JOIN companies c ON i.company_id = c.id
        WHERE COALESCE(i.hs_code, p.hs_code) IS NOT NULL AND COALESCE(i.hs_code, p.hs_code) != ''
        GROUP BY COALESCE(i.hs_code, p.hs_code), c.id
        ORDER BY COALESCE(i.hs_code, p.hs_code), c.name
    ''').fetchall()
    
    # HS Code by Warehouse
    hs_warehouse = db.execute('''
        SELECT COALESCE(i.hs_code, p.hs_code) as hs_code, w.name as warehouse, c.name as company, SUM(i.quantity) as total_qty,
               SUM(i.quantity * COALESCE(p.cost_price, 0)) as total_val
        FROM inventory i
        LEFT JOIN parts p ON i.part_id = p.id
        JOIN warehouses w ON i.warehouse_id = w.id
        JOIN companies c ON w.company_id = c.id
        WHERE COALESCE(i.hs_code, p.hs_code) IS NOT NULL AND COALESCE(i.hs_code, p.hs_code) != ''
        GROUP BY COALESCE(i.hs_code, p.hs_code), w.id
        ORDER BY c.name, w.name, COALESCE(i.hs_code, p.hs_code)
    ''').fetchall()
    
    # Parts detail per HS Code
    hs_parts = db.execute('''
        SELECT COALESCE(i.hs_code, p.hs_code) as hs_code, p.part_number, p.description, SUM(i.quantity) as total_qty,
               c.name as company, w.name as warehouse
        FROM inventory i
        LEFT JOIN parts p ON i.part_id = p.id
        JOIN warehouses w ON i.warehouse_id = w.id
        JOIN companies c ON w.company_id = c.id
        WHERE COALESCE(i.hs_code, p.hs_code) IS NOT NULL AND COALESCE(i.hs_code, p.hs_code) != ''
        GROUP BY COALESCE(i.hs_code, p.hs_code), p.id, w.id
        ORDER BY COALESCE(i.hs_code, p.hs_code), c.name, w.name
    ''').fetchall()
    
    return render_template('hs_codes.html', title="HS Code Reports",
                           hs_summary=hs_summary, hs_company=hs_company,
                           hs_warehouse=hs_warehouse, hs_parts=hs_parts)

# ─── Peyvast Stock Sync Routes ──────────────────────────────────────────────

@app.route('/stock-sync')
@stock_admin_required
def stock_sync():
    """Main stock sync interface - auto-syncs with Peyvast Panel on every page load."""
    sync_manager = PeyvastSyncManager()
    sync_manager.ensure_sync_schema()

    auto_sync = request.args.get('auto_sync', 'false').lower() == 'true'
    sync_triggered = False

    # Always auto-sync on page load (GET request)
    if request.method == 'GET' and not auto_sync:
        auto_sync = True

    if request.method == 'POST' or auto_sync:
        result = sync_manager.sync_all()
        sync_triggered = True
        if result['success']:
            flash(f"Successfully synced {result['items_synced']} items from Peyvast Panel!", "success")
        else:
            flash(f"Sync completed with errors: {', '.join(result['errors'])}", "warning")

        if auto_sync and request.method == 'GET':
            # For auto-sync on page load, don't redirect, just show updated data
            pass
        elif request.method == 'POST' and not auto_sync:
            return redirect(url_for('stock_sync'))

    # Get current sync status and products
    exclude_out_of_stock = request.args.get('exclude_out_of_stock', 'false').lower() == 'true'
    filters = {'exclude_out_of_stock': exclude_out_of_stock} if exclude_out_of_stock else {}
    products = sync_manager.get_all_products(filters=filters)
    all_products_count = sync_manager.get_all_products_count()
    warehouses = sync_manager.get_warehouses()
    categories = sync_manager.get_categories()
    brands = sync_manager.get_brands()
    summary = sync_manager.get_stock_summary()
    sync_logs = sync_manager.get_sync_status()
    summary['active_products'] = summary['total_products'] - summary['low_stock'] - summary['out_of_stock']

    return render_template('stock_sync.html', title="Stock Sync",
                           products=products, warehouses=warehouses,
                           categories=categories, brands=brands, summary=summary,
                           sync_logs=sync_logs, auto_sync=auto_sync,
                           exclude_out_of_stock=exclude_out_of_stock,
                           all_products_count=all_products_count)

@app.route('/sync-status')
@stock_admin_required
def sync_status():
    """View sync history and status."""
    sync_manager = PeyvastSyncManager()
    sync_manager.ensure_sync_schema()

    logs = sync_manager.get_sync_status()
    summary = sync_manager.get_stock_summary()

    return render_template('sync_status.html', title="Sync Status",
                           sync_logs=logs, summary=summary)

@app.route('/low-stock-alerts')
@stock_admin_required
def low_stock_alerts():
    """View items below minimum stock level."""
    sync_manager = PeyvastSyncManager()
    sync_manager.ensure_sync_schema()

    low_stock = sync_manager.get_low_stock_items()
    out_of_stock = sync_manager.get_out_of_stock_items()

    return render_template('low_stock_alerts.html', title="Low Stock Alerts",
                           low_stock=low_stock, out_of_stock=out_of_stock)

@app.route('/out-of-stock')
@stock_admin_required
def out_of_stock():
    """View items that are out of stock."""
    sync_manager = PeyvastSyncManager()
    sync_manager.ensure_sync_schema()

    items = sync_manager.get_out_of_stock_items()

    return render_template('out_of_stock.html', title="Out of Stock Items",
                           items=items)

@app.route('/stock-summary-report')
@stock_admin_required
def stock_summary_report():
    """View overall stock summary report."""
    sync_manager = PeyvastSyncManager()
    sync_manager.ensure_sync_schema()

    summary = sync_manager.get_stock_summary()
    products = sync_manager.get_all_products()
    by_warehouse = sync_manager.get_stock_by_warehouse()

    return render_template('stock_summary_report.html', title="Stock Summary",
                           summary=summary, products=products,
                           by_warehouse=by_warehouse)

@app.route('/category-report')
@stock_admin_required
def category_report():
    """View stock by category."""
    sync_manager = PeyvastSyncManager()
    sync_manager.ensure_sync_schema()

    summary = sync_manager.get_stock_summary()
    categories = sync_manager.get_categories()
    products = sync_manager.get_all_products()

    # Group products by category
    category_data = {}
    for cat in categories:
        cat_products = [p for p in products if p.get('category') == cat['name']]
        if cat_products:
            category_data[cat['name']] = {
                'products': cat_products,
                'count': len(cat_products),
                'total_qty': sum(p.get('current_stock', 0) for p in cat_products)
            }

    return render_template('category_report.html', title="Category Report",
                           category_data=category_data, summary=summary)

@app.route('/api/sync/trigger', methods=['POST'])
@stock_admin_required
def api_sync_trigger():
    """API endpoint to trigger sync."""
    sync_manager = PeyvastSyncManager()
    try:
        result = sync_manager.sync_all()
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'errors': [str(e)]}), 500

@app.route('/api/sync/products', methods=['GET'])
@stock_admin_required
def api_sync_products():
    """API endpoint to get synced products."""
    sync_manager = PeyvastSyncManager()
    products = sync_manager.get_all_products()
    return jsonify({'success': True, 'products': products})

@app.route('/api/sync/low-stock', methods=['GET'])
@stock_admin_required
def api_sync_low_stock():
    """API endpoint to get low stock items."""
    sync_manager = PeyvastSyncManager()
    low_stock = sync_manager.get_low_stock_items()
    return jsonify({'success': True, 'items': low_stock})

@app.route('/customers-reports')
@app.route('/customers-reports/<report_type>')
@stock_admin_required
def customers_reports(report_type=None):
    """Customer reports dashboard with various report types."""
    if not report_type:
        report_type = request.args.get('type', 'summary')

    # Get filters from request
    filters = {}
    country = request.args.get('country')
    city = request.args.get('city')
    customer_type = request.args.get('customer_type')
    search = request.args.get('search')
    salesperson = request.args.get('salesperson')

    if country:
        filters['country'] = country
    if city:
        filters['city'] = city
    if customer_type:
        filters['customer_type'] = customer_type
    if search:
        filters['search'] = search
    if salesperson:
        filters['salesperson_id'] = salesperson

    # Get data based on report type
    data = {}
    report_title = "Customer Reports"

    if report_type == 'summary':
        data = get_customers_summary_from_db()
        report_title = "Customers Summary"
    elif report_type == 'by_country':
        data['countries'] = get_customers_by_country_from_db()
        report_title = "Customers by Country"
    elif report_type == 'by_city':
        db = get_db()
        try:
            if country:
                data['cities'] = [dict(r) for r in db.execute('''
                    SELECT city, country, COUNT(*) as customer_count,
                           SUM(total_orders) as total_sales, SUM(total_debt) as total_debt
                    FROM sdad_customers WHERE city != '' AND country = ?
                    GROUP BY city, country ORDER BY customer_count DESC
                ''', (country,)).fetchall()]
            else:
                data['cities'] = [dict(r) for r in db.execute('''
                    SELECT city, country, COUNT(*) as customer_count,
                           SUM(total_orders) as total_sales, SUM(total_debt) as total_debt
                    FROM sdad_customers WHERE city != '' GROUP BY city, country ORDER BY customer_count DESC
                ''').fetchall()]
        finally:
            db.close()
        report_title = "Customers by City"
    elif report_type == 'by_locale':
        db = get_db()
        try:
            data['locales'] = [dict(r) for r in db.execute('''
                SELECT location, COUNT(*) as customer_count, SUM(total_orders) as total_sales, SUM(total_debt) as total_debt
                FROM sdad_customers GROUP BY location ORDER BY customer_count DESC
            ''').fetchall()]
        finally:
            db.close()
        report_title = "Customers by Locale/Area"
    elif report_type == 'by_type':
        db = get_db()
        try:
            data['types'] = [dict(r) for r in db.execute('''
                SELECT location as customer_type, COUNT(*) as customer_count,
                       SUM(total_orders) as total_sales, SUM(total_debt) as total_debt, AVG(credit_limit) as avg_credit_limit
                FROM sdad_customers GROUP BY location ORDER BY customer_count DESC
            ''').fetchall()]
        finally:
            db.close()
        report_title = "Customers by Type"
    elif report_type == 'by_salesperson':
        data['salespersons'] = get_salesperson_performance_from_db()
        report_title = "Salesperson Performance"
    elif report_type == 'export':
        data['customers'] = get_customers_from_db({'is_export': True})
        report_title = "Export Customers"
    elif report_type == 'domestic':
        data['customers'] = get_customers_from_db({'is_export': False})
        report_title = "Domestic Customers"
    elif report_type == 'top_purchases':
        db = get_db()
        try:
            data['customers'] = [dict(r) for r in db.execute('''
                SELECT * FROM sdad_customers ORDER BY total_orders DESC LIMIT 50
            ''').fetchall()]
        finally:
            db.close()
        report_title = "Top Customers by Purchases"
    elif report_type == 'top_outstanding':
        db = get_db()
        try:
            data['customers'] = [dict(r) for r in db.execute('''
                SELECT * FROM sdad_customers ORDER BY total_debt DESC LIMIT 50
            ''').fetchall()]
        finally:
            db.close()
        report_title = "Top Customers by Outstanding"
    elif report_type == 'credit_overdue':
        db = get_db()
        try:
            data['customers'] = [dict(r) for r in db.execute('''
                SELECT * FROM sdad_customers
                WHERE credit_status IN ('overdue', 'blocked') OR is_credit_blocked = 1
                ORDER BY total_debt DESC
            ''').fetchall()]
        finally:
            db.close()
        report_title = "Customers with Credit Overdue"
    elif report_type == 'activity':
        db = get_db()
        try:
            cutoff = datetime.now().strftime('%Y-%m-%d')
            days = 90
            active = db.execute('''
                SELECT COUNT(*) as cnt FROM sdad_customers
                WHERE last_purchase_date >= date('now', '-' || ? || ' days')
            ''', (days,)).fetchone()['cnt']
            
            inactive = db.execute('''
                SELECT COUNT(*) as cnt FROM sdad_customers
                WHERE last_purchase_date < date('now', '-' || ? || ' days') OR last_purchase_date = ''
            ''', (days,)).fetchone()['cnt']
            
            new = db.execute('''
                SELECT COUNT(*) as cnt FROM sdad_customers
                WHERE created_at >= datetime('now', '-' || ? || ' days')
            ''', (days,)).fetchone()['cnt']
            
            data = {
                'active_customers': active,
                'inactive_customers': inactive,
                'new_customers': new,
                'period_days': days
            }
        finally:
            db.close()
        report_title = "Customer Activity Report"
    elif report_type == 'new':
        days = int(request.args.get('days', 30))
        db = get_db()
        try:
            data['customers'] = [dict(r) for r in db.execute('''
                SELECT * FROM sdad_customers
                WHERE created_at >= datetime('now', '-' || ? || ' days')
                ORDER BY created_at DESC
            ''', (days,)).fetchall()]
        finally:
            db.close()
        report_title = f"New Customers (Last {days} days)"
    elif report_type == 'all':
        data['customers'] = get_customers_from_db(filters=filters)
        report_title = "All Customers"

    # Get filter options for dropdowns
    summary = get_customers_summary_from_db()

    return render_template('customers_reports.html', title=report_title,
                           report_type=report_type, data=data,
                           filters=filters, summary=summary,
                           countries=[c['country'] for c in summary.get('by_country', [])],
                           salespersons=summary.get('by_salesperson', []))

@app.route('/customers-by-country')
@stock_admin_required
def customers_by_country():
    """Detailed view of customers grouped by country."""
    countries = get_customers_by_country_from_db()
    summary = get_customers_summary_from_db()
    
    return render_template('customers_by_country.html', title="Customers by Country",
                           countries=countries, summary=summary)

@app.route('/customers-by-salesperson')
@stock_admin_required
def customers_by_salesperson():
    """Detailed view of customers grouped by salesperson."""
    salespersons = get_salesperson_performance_from_db()
    summary = get_customers_summary_from_db()
    
    return render_template('customers_by_salesperson.html', title="Customers by Salesperson",
                           salespersons=salespersons, summary=summary)

@app.route('/api/customers/all', methods=['GET'])
@stock_admin_required
def api_customers_all():
    """API endpoint to get all customers from local database."""
    db = get_db()
    try:
        customers = db.execute("SELECT * FROM sdad_customers ORDER BY total_orders DESC").fetchall()
        return jsonify({'success': True, 'customers': [dict(c) for c in customers]})
    finally:
        db.close()

@app.route('/api/customers/summary', methods=['GET'])
@stock_admin_required
def api_customers_summary():
    """API endpoint to get customers summary from local database."""
    db = get_db()
    try:
        total = db.execute("SELECT COUNT(*) as cnt FROM sdad_customers").fetchone()['cnt']
        total_orders = db.execute("SELECT COALESCE(SUM(total_orders), 0) as t FROM sdad_customers").fetchone()['t']
        total_debt = db.execute("SELECT COALESCE(SUM(total_debt), 0) as t FROM sdad_customers").fetchone()['t']
        export_count = db.execute("SELECT COUNT(*) as cnt FROM sdad_customers WHERE location = 'export'").fetchone()['cnt']
        active_count = db.execute("SELECT COUNT(*) as cnt FROM sdad_customers WHERE active = 1").fetchone()['cnt']
        
        countries = db.execute("SELECT country, COUNT(*) as cnt, SUM(total_orders) as total_sales FROM sdad_customers WHERE country != '' GROUP BY country ORDER BY cnt DESC").fetchall()
        
        summary = {
            'total_customers': total,
            'total_orders': total_orders,
            'total_debt': total_debt,
            'export_customers': export_count,
            'domestic_customers': total - export_count,
            'active_customers': active_count,
            'inactive_customers': total - active_count,
            'by_country': [dict(c) for c in countries]
        }
        return jsonify({'success': True, 'summary': summary})
    finally:
        db.close()

@app.route('/api/customers/export/<format>', methods=['GET'])
@stock_admin_required
def api_customers_export(format):
    """Export customers data in various formats."""
    db = get_db()
    try:
        query = "SELECT * FROM sdad_customers WHERE 1=1"
        params = []

        if request.args.get('country'):
            query += " AND country = ?"
            params.append(request.args.get('country'))
        if request.args.get('customer_type'):
            query += " AND location = ?"
            params.append(request.args.get('customer_type'))
        if request.args.get('is_export'):
            query += " AND location = 'export'" if request.args.get('is_export') == 'true' else " AND location = 'local'"

        query += " ORDER BY total_orders DESC"
        customers = db.execute(query, params).fetchall()
        customers = [dict(c) for c in customers]
    finally:
        db.close()

    if format == 'csv':
        output = io.StringIO()
        if customers:
            writer = csv.DictWriter(output, fieldnames=customers[0].keys())
            writer.writeheader()
            writer.writerows(customers)
        return Response(output.getvalue(), mimetype='text/csv',
                       headers={'Content-Disposition': 'attachment; filename=customers.csv'})

    elif format == 'json':
        return jsonify({'success': True, 'customers': customers})

    elif format == 'excel':
        wb = Workbook()
        ws = wb.active
        ws.title = "Customers"

        if customers:
            # Headers
            headers = list(customers[0].keys())
            ws.append(headers)

            # Data
            for customer in customers:
                ws.append(list(customer.values()))

            # Auto-adjust column widths
            for col in ws.columns:
                max_length = 0
                col_letter = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                ws.column_dimensions[col_letter].width = min(max_length + 2, 50)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        as_attachment=True, download_name='customers.xlsx')

    return jsonify({'success': False, 'message': 'Invalid format'}), 400

@app.route('/api/sync/import-csv', methods=['POST'])
@stock_admin_required
def api_sync_import_csv():
    """API endpoint to import stock data from CSV file."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    if not file.filename.endswith('.csv'):
        return jsonify({'success': False, 'message': 'File must be a CSV'}), 400

    try:
        # Save uploaded file temporarily
        import os
        import tempfile
        from werkzeug.utils import secure_filename

        filename = secure_filename(file.filename)
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        file.save(temp_path)

        # Import using sync manager
        sync_manager = PeyvastSyncManager()
        sync_manager.ensure_sync_schema()
        result = sync_manager.import_from_csv(temp_path)

        # Clean up temp file
        os.remove(temp_path)

        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/sync/import-excel', methods=['POST'])
@stock_admin_required
def api_sync_import_excel():
    """API endpoint to import stock data from Excel file."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400

    allowed_extensions = {'xlsx', 'xls'}
    if not any(file.filename.endswith(ext) for ext in allowed_extensions):
        return jsonify({'success': False, 'message': 'File must be an Excel file (.xlsx or .xls)'}), 400

    try:
        # Save uploaded file temporarily
        import os
        import tempfile
        from werkzeug.utils import secure_filename

        filename = secure_filename(file.filename)
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        file.save(temp_path)

        # Import using sync manager
        sync_manager = PeyvastSyncManager()
        sync_manager.ensure_sync_schema()
        result = sync_manager.import_from_excel(temp_path)

        # Clean up temp file
        os.remove(temp_path)

        return jsonify(result)

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/inventory/update_hs', methods=['POST'])
@admin_required
def update_hs_group():
    data = request.get_json()
    old_hs = data.get('old_hs')
    new_hs = data.get('new_hs')
    
    if not old_hs or not new_hs:
        return jsonify({'success': False, 'message': 'Invalid data'}), 400
        
    db = get_db()
    try:
        # Update in parts table
        db.execute('UPDATE parts SET hs_code = ? WHERE hs_code = ?', (new_hs, old_hs))
        # Update in inventory table (if anyone set it manually there)
        db.execute('UPDATE inventory SET hs_code = ? WHERE hs_code = ?', (new_hs, old_hs))
        # Update in movements table for history
        db.execute('UPDATE movements SET hs_code = ? WHERE hs_code = ?', (new_hs, old_hs))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/inventory/remove_hs', methods=['POST'])
@admin_required
def remove_hs_group():
    data = request.get_json()
    hs_code = data.get('hs_code')
    
    if not hs_code:
        return jsonify({'success': False, 'message': 'Invalid HS Code'}), 400
        
    db = get_db()
    try:
        # Clear hs_code from parts and inventory
        db.execute('UPDATE parts SET hs_code = NULL WHERE hs_code = ?', (hs_code,))
        db.execute('UPDATE inventory SET hs_code = NULL WHERE hs_code = ?', (hs_code,))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/inventory/delete_part', methods=['POST'])
@admin_required
def delete_part_endpoint():
    data = request.get_json()
    part_number = data.get('part_number')
    
    if not part_number:
        return jsonify({'success': False, 'message': 'Invalid Part Number'}), 400
        
    db = get_db()
    try:
        # Get part ID first
        part = db.execute('SELECT id FROM parts WHERE part_number = ?', (part_number,)).fetchone()
        if not part:
            return jsonify({'success': False, 'message': 'Part not found'}), 404
            
        part_id = part['id']
        
        # Delete from inventory, movements, and parts
        db.execute('DELETE FROM inventory WHERE part_id = ?', (part_id,))
        db.execute('DELETE FROM movements WHERE part_id = ?', (part_id,))
        db.execute('DELETE FROM parts WHERE id = ?', (part_id,))
        db.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/inventory/dashboard_bulk_action', methods=['POST'])
@admin_required
def inventory_dashboard_bulk_action():
    data = request.get_json() or {}
    action = (data.get('action') or '').strip().lower()
    report_mode = 'hs' if data.get('report_mode') == 'hs' else 'part'
    selected_ids = data.get('selected_ids') or []
    new_hs = (data.get('new_hs') or '').strip()

    db = get_db()

    try:
        if report_mode == 'part':
            inventory_ids = []
            for item in selected_ids:
                try:
                    inventory_ids.append(int(item))
                except (TypeError, ValueError):
                    continue

            if not inventory_ids:
                return jsonify({'success': False, 'message': 'No inventory rows selected.'}), 400

            placeholders = ','.join('?' for _ in inventory_ids)

            if action == 'edit':
                if not new_hs:
                    return jsonify({'success': False, 'message': 'New HS code is required.'}), 400
                cursor = db.execute(
                    f"UPDATE inventory SET hs_code = ? WHERE id IN ({placeholders})",
                    [new_hs] + inventory_ids
                )
            elif action == 'remove':
                # Empty string intentionally overrides any part-level default HS code for the selected rows.
                cursor = db.execute(
                    f"UPDATE inventory SET hs_code = '' WHERE id IN ({placeholders})",
                    inventory_ids
                )
            elif action == 'delete':
                cursor = db.execute(
                    f"DELETE FROM inventory WHERE id IN ({placeholders})",
                    inventory_ids
                )
            else:
                return jsonify({'success': False, 'message': 'Unsupported bulk action.'}), 400

            db.commit()
            return jsonify({'success': True, 'affected': cursor.rowcount})

        hs_codes = [str(item).strip() for item in selected_ids if str(item).strip()]
        if not hs_codes:
            return jsonify({'success': False, 'message': 'No HS groups selected.'}), 400

        placeholders = ','.join('?' for _ in hs_codes)
        if action == 'edit':
            if not new_hs:
                return jsonify({'success': False, 'message': 'New HS code is required.'}), 400

            affected = 0
            affected += db.execute(
                f"UPDATE parts SET hs_code = ? WHERE hs_code IN ({placeholders})",
                [new_hs] + hs_codes
            ).rowcount
            affected += db.execute(
                f"UPDATE inventory SET hs_code = ? WHERE hs_code IN ({placeholders})",
                [new_hs] + hs_codes
            ).rowcount
            affected += db.execute(
                f"UPDATE movements SET hs_code = ? WHERE hs_code IN ({placeholders})",
                [new_hs] + hs_codes
            ).rowcount
        elif action == 'remove':
            affected = 0
            affected += db.execute(
                f"UPDATE parts SET hs_code = NULL WHERE hs_code IN ({placeholders})",
                hs_codes
            ).rowcount
            affected += db.execute(
                f"UPDATE inventory SET hs_code = NULL WHERE hs_code IN ({placeholders})",
                hs_codes
            ).rowcount
            affected += db.execute(
                f"UPDATE movements SET hs_code = NULL WHERE hs_code IN ({placeholders})",
                hs_codes
            ).rowcount
        elif action == 'delete':
            effective_hs = get_effective_hs_expression('i', 'p')
            affected = db.execute(f'''
                DELETE FROM inventory
                WHERE id IN (
                    SELECT i.id
                    FROM inventory i
                    LEFT JOIN parts p ON i.part_id = p.id
                    WHERE {effective_hs} IN ({placeholders})
                )
            ''', hs_codes).rowcount
        else:
            return jsonify({'success': False, 'message': 'Unsupported bulk action.'}), 400

        db.commit()
        return jsonify({'success': True, 'affected': affected})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/hs-codes/export')
@admin_required
def export_hs_reports():
    db = get_db()
    
    # 1. HS Summary
    df_summary = pd.read_sql_query('''
        SELECT COALESCE(i.hs_code, p.hs_code) as "HS Code", COUNT(DISTINCT p.id) as "Part Count", SUM(i.quantity) as "Total Qty",
               SUM(i.quantity * COALESCE(p.cost_price, 0)) as "Total Val (AED)"
        FROM inventory i
        LEFT JOIN parts p ON i.part_id = p.id
        WHERE COALESCE(i.hs_code, p.hs_code) IS NOT NULL AND COALESCE(i.hs_code, p.hs_code) != ''
        GROUP BY "HS Code"
        ORDER BY "Total Qty" DESC
    ''', db)
    
    # 2. HS By Company
    df_company = pd.read_sql_query('''
        SELECT COALESCE(i.hs_code, p.hs_code) as "HS Code", c.name as "Company", SUM(i.quantity) as "Qty",
               SUM(i.quantity * COALESCE(p.cost_price, 0)) as "Val (AED)"
        FROM inventory i
        LEFT JOIN parts p ON i.part_id = p.id
        JOIN companies c ON i.company_id = c.id
        WHERE COALESCE(i.hs_code, p.hs_code) IS NOT NULL AND COALESCE(i.hs_code, p.hs_code) != ''
        GROUP BY "HS Code", c.id
        ORDER BY "HS Code", c.name
    ''', db)

    # 3. HS By Warehouse
    df_warehouse = pd.read_sql_query('''
        SELECT COALESCE(i.hs_code, p.hs_code) as "HS Code", w.name as "Warehouse", c.name as "Company", SUM(i.quantity) as "Qty",
               SUM(i.quantity * COALESCE(p.cost_price, 0)) as "Val (AED)"
        FROM inventory i
        LEFT JOIN parts p ON i.part_id = p.id
        JOIN warehouses w ON i.warehouse_id = w.id
        JOIN companies c ON w.company_id = c.id
        WHERE COALESCE(i.hs_code, p.hs_code) IS NOT NULL AND COALESCE(i.hs_code, p.hs_code) != ''
        GROUP BY "HS Code", w.id
        ORDER BY "Company", "Warehouse", "HS Code"
    ''', db)

    # 4. HS Detail (Parts)
    df_detail = pd.read_sql_query('''
        SELECT COALESCE(i.hs_code, p.hs_code) as "HS Code", p.part_number as "Part Number", p.description as "Description",
               c.name as "Company", w.name as "Warehouse", SUM(i.quantity) as "Qty"
        FROM inventory i
        LEFT JOIN parts p ON i.part_id = p.id
        JOIN warehouses w ON i.warehouse_id = w.id
        JOIN companies c ON w.company_id = c.id
        WHERE COALESCE(i.hs_code, p.hs_code) IS NOT NULL AND COALESCE(i.hs_code, p.hs_code) != ''
        GROUP BY "HS Code", p.id, w.id
        ORDER BY "HS Code", "Company", "Warehouse"
    ''', db)

    # 4. Details
    df_details = pd.read_sql_query('''
        SELECT p.hs_code as "HS Code", p.part_number as "Part Number", p.description as "Description", 
               SUM(i.quantity) as "Qty", c.name as "Company", w.name as "Warehouse"
        FROM inventory i
        JOIN parts p ON i.part_id = p.id
        JOIN warehouses w ON i.warehouse_id = w.id
        JOIN companies c ON w.company_id = c.id
        WHERE p.hs_code IS NOT NULL AND p.hs_code != ''
        GROUP BY p.hs_code, p.id, w.id
        ORDER BY p.hs_code, c.name, w.name
    ''', db)

    filename = f"HS_Intelligence_Report_{datetime.now().strftime('%Y%m%d')}.xlsx"
    path = os.path.join(tempfile.gettempdir(), filename)
    
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        df_company.to_excel(writer, sheet_name='By Company', index=False)
        df_warehouse.to_excel(writer, sheet_name='By Warehouse', index=False)
        df_details.to_excel(writer, sheet_name='Details', index=False)
        
        # Simple Styling
        for sheetname in writer.sheets:
            ws = writer.sheets[sheetname]
            for cell in ws[1]:
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="10B981", end_color="10B981", fill_type="solid")
    
    return send_file(path, as_attachment=True)

# ════════════════════════════════════════════════════════════════════════════
# SUBTASK ROUTES
# ════════════════════════════════════════════════════════════════════════════

@app.route('/subtasks/<int:parent_task_id>')
def get_subtasks(parent_task_id):
    """Get all subtasks for a parent task"""
    db = get_db()
    subtasks = db.execute('''
        SELECT s.*,
               a.username AS assigned_to_name,
               creator.username AS created_by_name,
               t.task_name AS parent_task_name
        FROM task_subtasks s
        LEFT JOIN users a ON s.assigned_to_user_id = a.id
        LEFT JOIN users creator ON s.created_by_user_id = creator.id
        LEFT JOIN task_items t ON s.parent_task_id = t.id
        WHERE s.parent_task_id = ?
        ORDER BY s.priority DESC, s.created_at ASC
    ''', (parent_task_id,)).fetchall()
    return jsonify([dict(row) for row in subtasks])


@app.route('/subtasks/save', methods=['POST'])
def save_subtask():
    """Create or update a subtask"""
    if not user_can_create_subtasks():
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    db = get_db()
    data = request.get_json() or {}
    subtask_id = data.get('id')
    parent_task_id = data.get('parent_task_id')

    if not parent_task_id:
        return jsonify({'success': False, 'message': 'Parent task is required'}), 400

    subtask_title = (data.get('subtask_title') or '').strip()
    if not subtask_title:
        return jsonify({'success': False, 'message': 'Subtask title is required'}), 400

    description = (data.get('description') or '').strip()
    assigned_to_user_id = data.get('assigned_to_user_id')
    priority = normalize_subtask_priority(data.get('priority'))
    status = normalize_subtask_status(data.get('status'))
    progress = max(0, min(100, int(data.get('progress', 0))))
    due_at = data.get('due_at') or None
    reminder_days = max(0, int(data.get('reminder_days', 0) or 0))
    reminder_hours = max(0, int(data.get('reminder_hours', 0) or 0))

    try:
        if subtask_id:
            existing = db.execute('SELECT id FROM task_subtasks WHERE id = ?', (subtask_id,)).fetchone()
            if not existing:
                return jsonify({'success': False, 'message': 'Subtask not found'}), 404

            db.execute('''
                UPDATE task_subtasks SET
                    subtask_title = ?, description = ?, assigned_to_user_id = ?,
                    priority = ?, status = ?, progress = ?, due_at = ?,
                    reminder_days = ?, reminder_hours = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (subtask_title, description, assigned_to_user_id, priority,
                  status, progress, due_at, reminder_days, reminder_hours, subtask_id))
            db.commit()
            recalculate_task_progress_from_subtasks(db, parent_task_id)
            update_task_progress_if_not_manual(db, parent_task_id)
            db.commit()
            return jsonify({'success': True, 'message': 'Subtask updated', 'id': subtask_id})
        else:
            cursor = db.execute('''
                INSERT INTO task_subtasks
                    (parent_task_id, subtask_title, description, assigned_to_user_id,
                     priority, status, progress, due_at, reminder_days, reminder_hours,
                     created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (parent_task_id, subtask_title, description, assigned_to_user_id,
                  priority, status, progress, due_at, reminder_days, reminder_hours,
                  session.get('user_id')))
            new_subtask_id = cursor.lastrowid
            db.commit()
            recalculate_task_progress_from_subtasks(db, parent_task_id)
            update_task_progress_if_not_manual(db, parent_task_id)
            db.commit()
            return jsonify({'success': True, 'message': 'Subtask created', 'id': new_subtask_id})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/subtasks/delete', methods=['POST'])
def delete_subtask():
    """Delete a subtask"""
    if not user_can_delete_subtasks():
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    db = get_db()
    data = request.get_json() or {}
    subtask_id = data.get('id')

    if not subtask_id:
        return jsonify({'success': False, 'message': 'Subtask ID is required'}), 400

    try:
        parent = db.execute('SELECT parent_task_id FROM task_subtasks WHERE id = ?', (subtask_id,)).fetchone()
        db.execute('DELETE FROM task_subtasks WHERE id = ?', (subtask_id,))
        db.commit()
        if parent:
            recalculate_task_progress_from_subtasks(db, parent['parent_task_id'])
            update_task_progress_if_not_manual(db, parent['parent_task_id'])
            db.commit()
        return jsonify({'success': True, 'message': 'Subtask deleted'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/subtasks/bulk_action', methods=['POST'])
def subtask_bulk_action():
    """Bulk update subtasks (status, priority, delete)"""
    if not user_can_edit_subtasks():
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    db = get_db()
    data = request.get_json() or {}
    action = (data.get('action') or '').strip().lower()
    subtask_ids = [int(x) for x in data.get('subtask_ids', []) if str(x).isdigit()]

    if not subtask_ids:
        return jsonify({'success': False, 'message': 'No subtasks selected'}), 400

    affected = 0
    parent_task_ids = set()
    try:
        if action == 'status':
            new_status = normalize_subtask_status(data.get('status'))
            for sid in subtask_ids:
                parent = db.execute('SELECT parent_task_id FROM task_subtasks WHERE id = ?', (sid,)).fetchone()
                if parent:
                    parent_task_ids.add(parent['parent_task_id'])
                db.execute('UPDATE task_subtasks SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                           (new_status, sid))
                affected += 1
        elif action == 'priority':
            for sid in subtask_ids:
                db.execute('UPDATE task_subtasks SET priority = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                           (new_priority, sid))
                affected += 1
        elif action == 'delete':
            if not user_can_delete_subtasks():
                return jsonify({'success': False, 'message': 'Permission denied'}), 403
            for sid in subtask_ids:
                parent = db.execute('SELECT parent_task_id FROM task_subtasks WHERE id = ?', (sid,)).fetchone()
                if parent:
                    parent_task_ids.add(parent['parent_task_id'])
                db.execute('DELETE FROM task_subtasks WHERE id = ?', (sid,))
                affected += 1
        else:
            return jsonify({'success': False, 'message': 'Invalid action'}), 400

        db.commit()
        for pid in parent_task_ids:
            recalculate_task_progress_from_subtasks(db, pid)
            update_task_progress_if_not_manual(db, pid)
        db.commit()
        return jsonify({'success': True, 'message': f'{affected} subtask(s) updated'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/subtasks/toggle_complete/<int:subtask_id>', methods=['POST'])
def toggle_subtask_complete(subtask_id):
    """Toggle subtask completion status"""
    if not user_can_edit_subtasks():
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    db = get_db()
    subtask = db.execute('SELECT id, status, progress, parent_task_id FROM task_subtasks WHERE id = ?',
                         (subtask_id,)).fetchone()

    if not subtask:
        return jsonify({'success': False, 'message': 'Subtask not found'}), 404

    current_status = subtask['status']
    new_status = 'Completed' if current_status != 'Completed' else 'In Progress'
    new_progress = 100 if new_status == 'Completed' else subtask['progress']

    db.execute('UPDATE task_subtasks SET status = ?, progress = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
               (new_status, new_progress, subtask_id))
    db.commit()
    recalculate_task_progress_from_subtasks(db, subtask['parent_task_id'])
    update_task_progress_if_not_manual(db, subtask['parent_task_id'])
    db.commit()
    return jsonify({'success': True, 'status': new_status, 'progress': new_progress})


@app.route('/subtasks/all')
def list_all_subtasks():
    """Get all subtasks with optional filters"""
    db = get_db()
    parent_task_id = request.args.get('parent_task_id', type=int)
    status = request.args.get('status')
    priority = request.args.get('priority')
    assigned_to = request.args.get('assigned_to_user_id', type=int)

    query = '''
        SELECT s.*,
               a.username AS assigned_to_name,
               creator.username AS created_by_name,
               t.task_name AS parent_task_name
        FROM task_subtasks s
        LEFT JOIN users a ON s.assigned_to_user_id = a.id
        LEFT JOIN users creator ON s.created_by_user_id = creator.id
        LEFT JOIN task_items t ON s.parent_task_id = t.id
        WHERE 1=1
    '''
    params = []

    if parent_task_id:
        query += ' AND s.parent_task_id = ?'
        params.append(parent_task_id)
    if status:
        query += ' AND s.status = ?'
        params.append(status)
    if priority:
        query += ' AND s.priority = ?'
        params.append(priority)
    if assigned_to:
        query += ' AND s.assigned_to_user_id = ?'
        params.append(assigned_to)

    query += ' ORDER BY s.priority DESC, s.created_at ASC'

    subtasks = db.execute(query, params).fetchall()
    return jsonify([dict(row) for row in subtasks])


# ════════════════════════════════════════════════════════════════════════════
# TASK TRANSACTION ROUTES
# ════════════════════════════════════════════════════════════════════════════

@app.route('/task-transactions')
def task_transactions():
    """Main transactions list page"""
    db = get_db()

    # Ensure session has required fields
    if 'profile_pic' not in session:
        session['profile_pic'] = 'default.png'

    page = max(request.args.get('page', 1, type=int), 1)
    per_page = 50
    task_id_filter = request.args.get('task_id', type=int)
    category_filter = request.args.get('category_id', type=int)
    type_filter = request.args.get('type')

    where_clause = 'WHERE 1=1'
    params = []

    if task_id_filter:
        where_clause += ' AND t.task_id = ?'
        params.append(task_id_filter)
    if category_filter:
        where_clause += ' AND t.category_id = ?'
        params.append(category_filter)
    if type_filter:
        where_clause += ' AND t.transaction_type = ?'
        params.append(type_filter)

    total = db.execute(f'SELECT COUNT(*) FROM task_transactions t {where_clause}', params).fetchone()[0]
    total_pages = max((total + per_page - 1) // per_page, 1) if total else 1
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * per_page

    transactions = db.execute(f'''
        SELECT t.*,
               c.name AS category_name, c.color AS category_color, c.icon AS category_icon,
               ti.task_name,
               u.username AS created_by_name
        FROM task_transactions t
        LEFT JOIN task_transaction_categories c ON t.category_id = c.id
        LEFT JOIN task_items ti ON t.task_id = ti.id
        LEFT JOIN users u ON t.created_by_user_id = u.id
        {where_clause}
        ORDER BY t.created_at DESC
        LIMIT ? OFFSET ?
    ''', params + [per_page, offset]).fetchall()

    categories = db.execute('SELECT * FROM task_transaction_categories ORDER BY name').fetchall()
    tasks = db.execute('SELECT id, task_name FROM task_items ORDER BY task_name').fetchall()

    summary = db.execute(f'''
        SELECT
            COALESCE(SUM(CASE WHEN t.transaction_type = 'Expense' THEN t.amount * t.quantity ELSE 0 END), 0) AS total_expenses,
            COALESCE(SUM(CASE WHEN t.transaction_type = 'Revenue' THEN t.amount * t.quantity ELSE 0 END), 0) AS total_revenue,
            COALESCE(SUM(CASE WHEN t.transaction_type = 'Time' THEN t.quantity ELSE 0 END), 0) AS total_time_units,
            COUNT(*) AS total_transactions
        FROM task_transactions t {where_clause}
    ''', params).fetchone()

    return render_template(
        'task_transactions.html',
        title='Task Transactions',
        transactions=[dict(row) for row in transactions],
        categories=[dict(row) for row in categories],
        tasks=[dict(row) for row in tasks],
        summary=dict(summary),
        filters={
            'task_id': task_id_filter,
            'category_id': category_filter,
            'type': type_filter
        },
        page=page,
        total_pages=total_pages,
        total=total,
        per_page=per_page,
        transaction_types=TRANSACTION_TYPES
    )


@app.route('/task-transactions/save', methods=['POST'])
def save_task_transaction():
    """Create or update a task transaction"""
    if not user_can_manage_task_transactions():
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    db = get_db()
    data = request.get_json() or {}
    transaction_id = data.get('id')

    task_id = data.get('task_id')
    if not task_id:
        return jsonify({'success': False, 'message': 'Task is required'}), 400

    transaction_type = (data.get('transaction_type') or '').strip()
    if transaction_type not in TRANSACTION_TYPES:
        return jsonify({'success': False, 'message': 'Invalid transaction type'}), 400

    category_id = data.get('category_id')
    amount = max(0, float(data.get('amount', 0)))
    quantity = max(1, int(data.get('quantity', 1)))
    unit = (data.get('unit') or 'unit').strip()
    description = (data.get('description') or '').strip()
    reference = (data.get('reference') or '').strip()
    transaction_date = data.get('transaction_date') or None

    try:
        if transaction_id:
            db.execute('''
                UPDATE task_transactions SET
                    task_id = ?, category_id = ?, transaction_type = ?,
                    amount = ?, quantity = ?, unit = ?, description = ?,
                    reference = ?, transaction_date = ?
                WHERE id = ?
            ''', (task_id, category_id, transaction_type, amount, quantity, unit,
                  description, reference, transaction_date, transaction_id))
            db.commit()
            return jsonify({'success': True, 'message': 'Transaction updated', 'id': transaction_id})
        else:
            cursor = db.execute('''
                INSERT INTO task_transactions
                    (task_id, category_id, transaction_type, amount, quantity, unit,
                     description, reference, transaction_date, created_by_user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (task_id, category_id, transaction_type, amount, quantity, unit,
                  description, reference, transaction_date, session.get('user_id')))
            db.commit()
            return jsonify({'success': True, 'message': 'Transaction created', 'id': cursor.lastrowid})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/task-transactions/delete', methods=['POST'])
def delete_task_transaction():
    """Delete a task transaction"""
    if not user_can_manage_task_transactions():
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    db = get_db()
    data = request.get_json() or {}
    transaction_id = data.get('id')

    if not transaction_id:
        return jsonify({'success': False, 'message': 'Transaction ID is required'}), 400

    try:
        db.execute('DELETE FROM task_transactions WHERE id = ?', (transaction_id,))
        db.commit()
        return jsonify({'success': True, 'message': 'Transaction deleted'})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/task-transactions/by-task/<int:task_id>')
def get_task_transactions(task_id):
    """Get all transactions for a specific task"""
    db = get_db()
    transactions = db.execute('''
        SELECT t.*,
               c.name AS category_name, c.color AS category_color, c.icon AS category_icon,
               u.username AS created_by_name
        FROM task_transactions t
        LEFT JOIN task_transaction_categories c ON t.category_id = c.id
        LEFT JOIN users u ON t.created_by_user_id = u.id
        WHERE t.task_id = ?
        ORDER BY t.transaction_date DESC, t.created_at DESC
    ''', (task_id,)).fetchall()

    summary = db.execute('''
        SELECT
            COALESCE(SUM(CASE WHEN transaction_type = 'Expense' THEN amount * quantity ELSE 0 END), 0) AS total_expenses,
            COALESCE(SUM(CASE WHEN transaction_type = 'Revenue' THEN amount * quantity ELSE 0 END), 0) AS total_revenue,
            COALESCE(SUM(CASE WHEN transaction_type = 'Time' THEN quantity ELSE 0 END), 0) AS total_time_units,
            COUNT(*) AS total_count
        FROM task_transactions
        WHERE task_id = ?
    ''', (task_id,)).fetchone()

    return jsonify({
        'transactions': [dict(row) for row in transactions],
        'summary': dict(summary) if summary else {}
    })


@app.route('/task-transactions/summary')
def get_transactions_summary():
    """Get transactions summary/analytics"""
    db = get_db()

    by_category = db.execute('''
        SELECT c.name, c.color,
               COALESCE(SUM(CASE WHEN t.transaction_type = 'Expense' THEN t.amount * t.quantity ELSE 0 END), 0) AS total_expenses,
               COALESCE(SUM(CASE WHEN t.transaction_type = 'Revenue' THEN t.amount * t.quantity ELSE 0 END), 0) AS total_revenue,
               COUNT(t.id) AS transaction_count
        FROM task_transaction_categories c
        LEFT JOIN task_transactions t ON c.id = t.category_id
        GROUP BY c.id
        ORDER BY total_expenses DESC
    ''').fetchall()

    by_type = db.execute('''
        SELECT transaction_type,
               SUM(amount * quantity) AS total_amount,
               SUM(quantity) AS total_quantity,
               COUNT(*) AS count
        FROM task_transactions
        GROUP BY transaction_type
    ''').fetchall()

    by_month = db.execute('''
        SELECT strftime('%Y-%m', transaction_date) AS month,
               transaction_type,
               SUM(amount * quantity) AS total_amount
        FROM task_transactions
        WHERE transaction_date IS NOT NULL
        GROUP BY month, transaction_type
        ORDER BY month DESC
        LIMIT 12
    ''').fetchall()

    return jsonify({
        'by_category': [dict(row) for row in by_category],
        'by_type': [dict(row) for row in by_type],
        'by_month': [dict(row) for row in by_month]
    })


@app.route('/task-transactions/export')
def export_transactions():
    """Export transactions to CSV"""
    if not user_can_export_task_reports():
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    db = get_db()
    task_id = request.args.get('task_id', type=int)

    query = '''
        SELECT t.*, c.name AS category_name, ti.task_name,
               u.username AS created_by_name
        FROM task_transactions t
        LEFT JOIN task_transaction_categories c ON t.category_id = c.id
        LEFT JOIN task_items ti ON t.task_id = ti.id
        LEFT JOIN users u ON t.created_by_user_id = u.id
    '''
    params = []
    if task_id:
        query += ' WHERE t.task_id = ?'
        params.append(task_id)
    query += ' ORDER BY t.transaction_date DESC, t.created_at DESC'

    transactions = db.execute(query, params).fetchall()

    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Task', 'Category', 'Type', 'Amount', 'Quantity', 'Unit',
                     'Description', 'Reference', 'Date', 'Created By'])

    for t in transactions:
        writer.writerow([
            t['id'], t['task_name'], t['category_name'], t['transaction_type'],
            t['amount'], t['quantity'], t['unit'], t['description'],
            t['reference'], t['transaction_date'], t['created_by_name']
        ])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'task_transactions_{datetime.now().strftime("%Y%m%d")}.csv'
    )


# ════════════════════════════════════════════════════════════════════════════
# TASK REPORT ROUTES
# ════════════════════════════════════════════════════════════════════════════

@app.route('/task-reports')
def task_reports():
    """Main task reports page"""
    db = get_db()

    # Ensure session has required fields
    if 'profile_pic' not in session:
        session['profile_pic'] = 'default.png'

    companies = [dict(row) for row in db.execute('SELECT id, name FROM companies ORDER BY name').fetchall()]
    departments = [dict(row) for row in db.execute(
        "SELECT * FROM task_departments WHERE status = 'Active' ORDER BY name"
    ).fetchall()]
    task_users = [dict(row) for row in db.execute(
        'SELECT id, username FROM users ORDER BY username'
    ).fetchall()]

    snapshots = []
    if user_can_view_task_reports():
        snapshots = db.execute('''
            SELECT rs.*, u.username AS created_by_name
            FROM task_report_snapshots rs
            LEFT JOIN users u ON rs.created_by_user_id = u.id
            ORDER BY rs.created_at DESC
            LIMIT 20
        ''').fetchall()

    return render_template(
        'task_reports.html',
        title='Task Reports',
        companies=companies,
        departments=departments,
        task_users=task_users,
        snapshots=[dict(row) for row in snapshots] if snapshots else [],
        report_types=REPORT_TYPES,
        report_intervals=REPORT_INTERVALS,
        task_priorities=TASK_PRIORITIES,
        task_statuses=TASK_STATUSES
    )


@app.route('/task-reports/generate', methods=['POST'])
def generate_task_report():
    """Generate a new task report"""
    if not user_can_view_task_reports():
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    db = get_db()
    data = request.get_json() or {}
    report_type = data.get('report_type')

    if report_type not in REPORT_TYPES:
        return jsonify({'success': False, 'message': 'Invalid report type'}), 400

    filters = {
        'company_id': data.get('company_id'),
        'department_id': data.get('department_id'),
        'user_id': data.get('user_id'),
        'priority': data.get('priority'),
        'status': data.get('status'),
        'date_from': data.get('date_from'),
        'date_to': data.get('date_to')
    }

    base_sql = 'FROM task_items t'
    join_sql = ''
    where_sql = 'WHERE 1=1'
    params = []

    if filters['company_id']:
        where_sql += ' AND t.company_id = ?'
        params.append(filters['company_id'])
    if filters['department_id']:
        where_sql += ' AND t.department_id = ?'
        params.append(filters['department_id'])
    if filters['user_id']:
        where_sql += ' AND (t.assigned_to_user_id = ? OR t.report_to_user_id = ?)'
        params.extend([filters['user_id'], filters['user_id']])
    if filters['priority']:
        where_sql += ' AND t.priority = ?'
        params.append(filters['priority'])
    if filters['status']:
        where_sql += ' AND t.status = ?'
        params.append(filters['status'])

    full_sql = f'{base_sql} {where_sql}'

    report_data = {}

    if report_type == 'Status':
        rows = db.execute(f'''
            SELECT COALESCE(t.status, 'Open') AS label, COUNT(*) AS count
            {full_sql}
            GROUP BY label ORDER BY count DESC
        ''', params).fetchall()
        report_data = {'labels': [r['label'] for r in rows], 'values': [r['count'] for r in rows]}

    elif report_type == 'Priority':
        rows = db.execute(f'''
            SELECT COALESCE(t.priority, 'Medium') AS label, COUNT(*) AS count
            {full_sql}
            GROUP BY label ORDER BY count DESC
        ''', params).fetchall()
        report_data = {'labels': [r['label'] for r in rows], 'values': [r['count'] for r in rows]}

    elif report_type == 'Department':
        rows = db.execute(f'''
            SELECT COALESCE(d.name, 'Unassigned') AS label, COUNT(*) AS count
            FROM task_items t
            LEFT JOIN task_departments d ON t.department_id = d.id
            {where_sql}
            GROUP BY label ORDER BY count DESC
        ''', params).fetchall()
        report_data = {'labels': [r['label'] for r in rows], 'values': [r['count'] for r in rows]}

    elif report_type == 'User':
        rows = db.execute(f'''
            SELECT COALESCE(u.username, 'Unassigned') AS label, COUNT(*) AS count
            FROM task_items t
            LEFT JOIN users u ON t.assigned_to_user_id = u.id
            {where_sql}
            GROUP BY label ORDER BY count DESC
        ''', params).fetchall()
        report_data = {'labels': [r['label'] for r in rows], 'values': [r['count'] for r in rows]}

    elif report_type == 'Timeline':
        rows = db.execute(f'''
            SELECT strftime('%Y-%m', t.due_at) AS month, COUNT(*) AS count
            {full_sql}
            AND t.due_at IS NOT NULL
            GROUP BY month ORDER BY month DESC LIMIT 12
        ''', params).fetchall()
        report_data = {'labels': [r['month'] for r in rows], 'values': [r['count'] for r in rows]}

    elif report_type == 'Financial':
        trans_data = db.execute('''
            SELECT
                COALESCE(SUM(CASE WHEN tt.transaction_type = 'Expense' THEN tt.amount * tt.quantity ELSE 0 END), 0) AS total_expenses,
                COALESCE(SUM(CASE WHEN tt.transaction_type = 'Revenue' THEN tt.amount * tt.quantity ELSE 0 END), 0) AS total_revenue,
                COUNT(DISTINCT tt.task_id) AS tasks_with_transactions
            FROM task_transactions tt
            JOIN task_items t ON tt.task_id = t.id
            WHERE 1=1
        ''' + ''.join([f' AND t.{k} = ?' for k, v in filters.items() if v]), params).fetchone()
        report_data = {
            'total_expenses': float(trans_data['total_expenses']) if trans_data else 0,
            'total_revenue': float(trans_data['total_revenue']) if trans_data else 0,
            'tasks_with_transactions': trans_data['tasks_with_transactions'] if trans_data else 0
        }

    elif report_type == 'Productivity':
        rows = db.execute(f'''
            SELECT
                u.username,
                COUNT(*) AS tasks_completed,
                AVG(t.progress) AS avg_progress
            FROM task_items t
            LEFT JOIN users u ON t.assigned_to_user_id = u.id
            {where_sql}
            AND t.status = 'Completed'
            GROUP BY u.id ORDER BY tasks_completed DESC
        ''', params).fetchall()
        report_data = {
            'users': [{'username': r['username'], 'tasks_completed': r['tasks_completed'],
                       'avg_progress': float(r['avg_progress'])} for r in rows]
        }

    return jsonify({'success': True, 'report_type': report_type, 'data': report_data, 'filters': filters})


@app.route('/task-reports/save-snapshot', methods=['POST'])
def save_task_report_snapshot():
    """Save a report snapshot for later viewing"""
    if not user_can_view_task_reports():
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    db = get_db()
    data = request.get_json() or {}
    report_name = (data.get('report_name') or '').strip()
    report_type = data.get('report_type')
    filters_applied = json.dumps(data.get('filters', {}), ensure_ascii=False)
    snapshot_data = json.dumps(data.get('snapshot_data', {}), ensure_ascii=False)

    if not report_name or not report_type:
        return jsonify({'success': False, 'message': 'Report name and type are required'}), 400

    try:
        cursor = db.execute('''
            INSERT INTO task_report_snapshots
                (report_name, report_type, filters_applied, snapshot_data, created_by_user_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (report_name, report_type, filters_applied, snapshot_data, session.get('user_id')))
        db.commit()
        return jsonify({'success': True, 'message': 'Snapshot saved', 'id': cursor.lastrowid})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/task-reports/snapshots')
def get_report_snapshots():
    """Get saved report snapshots"""
    if not user_can_view_task_reports():
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    db = get_db()
    snapshots = db.execute('''
        SELECT rs.*, u.username AS created_by_name
        FROM task_report_snapshots rs
        LEFT JOIN users u ON rs.created_by_user_id = u.id
        ORDER BY rs.created_at DESC
    ''').fetchall()
    return jsonify([dict(row) for row in snapshots])


@app.route('/task-reports/export/<report_type>')
def export_task_report(report_type):
    """Export a task report"""
    if not user_can_export_task_reports():
        return jsonify({'success': False, 'message': 'Permission denied'}), 403

    db = get_db()
    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == 'Status':
        writer.writerow(['Status', 'Count'])
        rows = db.execute('SELECT COALESCE(status, "Open") AS label, COUNT(*) AS count FROM task_items GROUP BY label').fetchall()
        for r in rows:
            writer.writerow([r['label'], r['count']])

    elif report_type == 'Priority':
        writer.writerow(['Priority', 'Count'])
        rows = db.execute('SELECT COALESCE(priority, "Medium") AS label, COUNT(*) AS count FROM task_items GROUP BY label').fetchall()
        for r in rows:
            writer.writerow([r['label'], r['count']])

    elif report_type == 'Financial':
        writer.writerow(['Metric', 'Value'])
        summary = db.execute('''
            SELECT
                COALESCE(SUM(CASE WHEN transaction_type = 'Expense' THEN amount * quantity ELSE 0 END), 0) AS total_expenses,
                COALESCE(SUM(CASE WHEN transaction_type = 'Revenue' THEN amount * quantity ELSE 0 END), 0) AS total_revenue
            FROM task_transactions
        ''').fetchone()
        writer.writerow(['Total Expenses', summary['total_expenses']])
        writer.writerow(['Total Revenue', summary['total_revenue']])

    else:
        writer.writerow(['Report Type', report_type, 'Generated', datetime.now().isoformat()])

    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'task_report_{report_type}_{datetime.now().strftime("%Y%m%d")}.csv'
    )


@app.route('/task-reports/analytics')
def get_task_analytics():
    """Get analytics data for dashboard widgets"""
    db = get_db()

    stats = db.execute('''
        SELECT
            COUNT(*) AS total_tasks,
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed_tasks,
            SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress_tasks,
            SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) AS open_tasks,
            AVG(COALESCE(progress, 0)) AS avg_progress
        FROM task_items
    ''').fetchone()

    subtask_stats = db.execute('''
        SELECT
            COUNT(*) AS total_subtasks,
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed_subtasks,
            AVG(COALESCE(progress, 0)) AS avg_subtask_progress
        FROM task_subtasks
    ''').fetchone()

    return jsonify({
        'tasks': dict(stats) if stats else {},
        'subtasks': dict(subtask_stats) if subtask_stats else {}
    })


# ════════════════════════════════════════════════════════════════════════════
# PAGE ROUTES FOR NEW TEMPLATES
# ════════════════════════════════════════════════════════════════════════════

@app.route('/subtasks-page')
def subtasks_page():
    """Subtasks management page"""
    db = get_db()

    # Ensure session has required fields
    if 'profile_pic' not in session:
        session['profile_pic'] = 'default.png'

    tasks = db.execute('''
        SELECT t.id, t.task_name, t.status AS task_status,
               (SELECT COUNT(*) FROM task_subtasks WHERE parent_task_id = t.id) AS subtask_count,
               (SELECT COUNT(*) FROM task_subtasks WHERE parent_task_id = t.id AND status = 'Completed') AS completed_count
        FROM task_items t
        WHERE t.is_archived = 0
        ORDER BY t.task_name
    ''').fetchall()

    subtask_users = [dict(row) for row in db.execute(
        'SELECT id, username FROM users ORDER BY username'
    ).fetchall()]

    return render_template(
        'subtasks.html',
        title='Sub Tasks',
        tasks=[dict(row) for row in tasks],
        subtask_users=subtask_users,
        subtask_priorities=SUBTASK_PRIORITIES,
        subtask_statuses=SUBTASK_STATUSES,
        subtask_column_options=SUBTASK_COLUMN_OPTIONS
    )


@app.route('/task-list')
def task_list_page():
    """Combined task + subtask view with column visibility"""
    db = get_db()

    if 'profile_pic' not in session:
        session['profile_pic'] = 'default.png'

    # Get all active tasks
    tasks = db.execute('''
        SELECT t.id, t.task_name, t.description, t.priority, t.status, t.progress,
               t.due_at, t.assigned_to_user_id, t.latest_note,
               t.reminder_days, t.reminder_hours,
               a.username AS assigned_to_name
        FROM task_items t
        LEFT JOIN users a ON t.assigned_to_user_id = a.id
        WHERE t.is_archived = 0
        ORDER BY t.updated_at DESC
    ''').fetchall()

    # Get all subtasks
    subtasks = db.execute('''
        SELECT s.id, s.parent_task_id, s.subtask_title, s.description, s.priority,
               s.status, s.progress, s.due_at, s.assigned_to_user_id,
               s.reminder_days, s.reminder_hours,
               a.username AS assigned_to_name
        FROM task_subtasks s
        LEFT JOIN users a ON s.assigned_to_user_id = a.id
        ORDER BY s.updated_at DESC
    ''').fetchall()

    task_users = [dict(row) for row in db.execute(
        'SELECT id, username FROM users ORDER BY username'
    ).fetchall()]

    # Get saved column preferences
    user_id = session.get('user_id')
    visible_columns = TASK_LIST_DEFAULT_COLUMNS[:]
    if user_id:
        row = db.execute(
            "SELECT task_list_columns FROM user_task_preferences WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        if row and row['task_list_columns']:
            saved = row['task_list_columns']
            if isinstance(saved, str) and saved.strip():
                try:
                    saved = json.loads(saved)
                except (TypeError, ValueError, json.JSONDecodeError):
                    saved = []
            if isinstance(saved, list):
                visible_columns = [c for c in TASK_LIST_DEFAULT_COLUMNS if c in saved]
            if not visible_columns:
                visible_columns = TASK_LIST_DEFAULT_COLUMNS[:]

    return render_template(
        'task_list.html',
        title='Task List',
        tasks=[dict(row) for row in tasks],
        subtasks=[dict(row) for row in subtasks],
        task_users=task_users,
        task_priorities=TASK_PRIORITIES,
        task_statuses=TASK_STATUSES,
        subtask_priorities=SUBTASK_PRIORITIES,
        subtask_statuses=SUBTASK_STATUSES,
        column_options=TASK_LIST_COLUMN_OPTIONS,
        column_keys=TASK_LIST_COLUMN_KEYS,
        default_columns=TASK_LIST_DEFAULT_COLUMNS,
        visible_columns=visible_columns
    )


@app.route('/task-list/columns', methods=['POST'])
def save_task_list_columns():
    """Save task list column visibility preferences"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Please sign in.'}), 403

    db = get_db()
    data = request.get_json() or {}
    columns = data.get('visible_columns', [])

    # Validate columns
    columns = [c for c in columns if c in TASK_LIST_COLUMN_KEYS]
    if not columns:
        columns = TASK_LIST_DEFAULT_COLUMNS[:]

    db.execute('''
        INSERT INTO user_task_preferences (user_id, task_list_columns, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(user_id) DO UPDATE SET
            task_list_columns = excluded.task_list_columns,
            updated_at = CURRENT_TIMESTAMP
    ''', (user_id, json.dumps(columns)))
    db.commit()
    return jsonify({'success': True, 'message': 'Column preferences saved.', 'visible_columns': columns})


if __name__ == '__main__':
    # Always enable debug mode for local development
    os.environ['FLASK_DEBUG'] = '1'
    app.debug = True
    host = '127.0.0.1'
    port = 5000
    print(f"Starting Flask server on http://{host}:{port}")
    print(f"Debug mode: ON")
    app.run(host=host, port=port, debug=True, use_reloader=True)
    print(f"Server stopped")
