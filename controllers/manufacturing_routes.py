"""
Manufacturing Management Routes
================================
Flask routes for the Manufacturing module (MES/PP).

Provides endpoints for:
- Manufacturing Dashboard
- Production Orders
- Work Centers
- Bill of Materials
- Routings
- Quality Control
- Production Reports

Route Pattern: /manufacturing/*
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash, session, send_file
from functools import wraps
import sqlite3
import os
import json
from datetime import datetime, timedelta
from io import BytesIO

from database import get_db, get_db_context, get_one, get_all, log_audit, create_notification
from permissions import user_has_permission, require_permission


# Create blueprint
manufacturing_bp = Blueprint('manufacturing', __name__, url_prefix='/manufacturing')


# =============================================================================
# ROUTE REGISTRATION
# =============================================================================

def register_manufacturing_routes(app):
    """Register manufacturing management routes with the Flask app."""
    init_manufacturing_tables()
    app.register_blueprint(manufacturing_bp)


# =============================================================================
# AUTHENTICATION AND PERMISSION HELPERS
# =============================================================================

def require_login(f):
    """Decorator to require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please login to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def require_manufacturing_permission(action):
    """Decorator factory for manufacturing-specific permissions."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please login to access this page.', 'error')
                return redirect(url_for('login'))
            # Check manufacturing permission
            if not user_has_permission(session['user_id'], 'manufacturing'):
                flash('You do not have permission to access Manufacturing.', 'error')
                if request.is_json:
                    return jsonify({'error': 'Permission denied'}), 403
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

def init_manufacturing_tables():
    """Initialize manufacturing tables in the database."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Production Orders table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mfg_production_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            product_id INTEGER,
            quantity REAL DEFAULT 0,
            completed_quantity REAL DEFAULT 0,
            status TEXT DEFAULT 'DRAFT',
            priority TEXT DEFAULT 'NORMAL',
            work_center_id INTEGER,
            scheduled_start TEXT,
            scheduled_end TEXT,
            actual_start TEXT,
            actual_end TEXT,
            bom_id INTEGER,
            routing_id INTEGER,
            notes TEXT,
            created_by INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Work Centers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mfg_work_centers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            location TEXT,
            capacity_hours REAL DEFAULT 0,
            efficiency REAL DEFAULT 100,
            status TEXT DEFAULT 'ACTIVE',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Bill of Materials table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mfg_bom (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            product_id INTEGER,
            version TEXT DEFAULT '1.0',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # BOM Components table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mfg_bom_components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bom_id INTEGER NOT NULL,
            item_id INTEGER NOT NULL,
            quantity REAL DEFAULT 0,
            unit TEXT,
            is_critical INTEGER DEFAULT 0,
            FOREIGN KEY (bom_id) REFERENCES mfg_bom(id)
        )
    ''')
    
    # Routings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mfg_routings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            product_id INTEGER,
            version TEXT DEFAULT '1.0',
            is_active INTEGER DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Routing Operations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mfg_routing_operations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            routing_id INTEGER NOT NULL,
            sequence INTEGER DEFAULT 1,
            work_center_id INTEGER,
            operation_code TEXT,
            description TEXT,
            standard_hours REAL DEFAULT 0,
            setup_time REAL DEFAULT 0,
            run_time REAL DEFAULT 0,
            wait_time REAL DEFAULT 0,
            move_time REAL DEFAULT 0,
            FOREIGN KEY (routing_id) REFERENCES mfg_routings(id)
        )
    ''')
    
    # Production Schedule table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mfg_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            work_center_id INTEGER,
            scheduled_date TEXT,
            shift TEXT,
            planned_hours REAL DEFAULT 0,
            actual_hours REAL DEFAULT 0,
            status TEXT DEFAULT 'SCHEDULED',
            notes TEXT,
            FOREIGN KEY (order_id) REFERENCES mfg_production_orders(id)
        )
    ''')
    
    conn.commit()
    conn.close()


# =============================================================================
# DASHBOARD
# =============================================================================

@manufacturing_bp.route('/')
@manufacturing_bp.route('/dashboard')
@require_login
def dashboard():
    """Display manufacturing dashboard."""
    conn = get_db()
    
    # Get production order stats
    orders = conn.execute('''
        SELECT status, COUNT(*) as count 
        FROM mfg_production_orders 
        GROUP BY status
    ''').fetchall()
    
    work_centers = conn.execute('SELECT COUNT(*) as count FROM mfg_work_centers WHERE status = ?', ('ACTIVE',)).fetchone()
    
    conn.close()
    
    stats = {
        'total_orders': sum(o['count'] for o in orders),
        'draft': next((o['count'] for o in orders if o['status'] == 'DRAFT'), 0),
        'scheduled': next((o['count'] for o in orders if o['status'] == 'SCHEDULED'), 0),
        'in_progress': next((o['count'] for o in orders if o['status'] == 'IN_PROGRESS'), 0),
        'completed': next((o['count'] for o in orders if o['status'] == 'COMPLETED'), 0),
        'cancelled': next((o['count'] for o in orders if o['status'] == 'CANCELLED'), 0),
        'work_centers': work_centers['count'] if work_centers else 0
    }
    
    return render_template('manufacturing/dashboard.html', stats=stats)


# =============================================================================
# PRODUCTION ORDERS
# =============================================================================

@manufacturing_bp.route('/orders')
@require_login
def orders():
    """List all production orders."""
    conn = get_db()
    orders = conn.execute('SELECT * FROM mfg_production_orders ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('manufacturing/orders.html', orders=orders)


@manufacturing_bp.route('/orders/<int:order_id>')
@require_login
def order_detail(order_id):
    """View production order details."""
    conn = get_db()
    order = conn.execute('SELECT * FROM mfg_production_orders WHERE id = ?', (order_id,)).fetchone()
    
    if not order:
        conn.close()
        flash('Production order not found.', 'error')
        return redirect(url_for('manufacturing.orders'))
    
    components = conn.execute('''
        SELECT c.*, i.name as item_name 
        FROM mfg_bom_components c 
        LEFT JOIN inventory_items i ON c.item_id = i.id 
        WHERE c.bom_id = ?
    ''', (order['bom_id'],)).fetchall() if order['bom_id'] else []
    
    conn.close()
    return render_template('manufacturing/order_detail.html', order=order, components=components)


@manufacturing_bp.route('/orders/create', methods=['GET', 'POST'])
@require_login
def create_order():
    """Create a new production order."""
    if request.method == 'POST':
        conn = get_db()
        order_number = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        conn.execute('''
            INSERT INTO mfg_production_orders 
            (order_number, product_id, quantity, status, priority, work_center_id, 
             scheduled_start, scheduled_end, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_number,
            request.form.get('product_id'),
            request.form.get('quantity', 0),
            request.form.get('status', 'DRAFT'),
            request.form.get('priority', 'NORMAL'),
            request.form.get('work_center_id'),
            request.form.get('scheduled_start'),
            request.form.get('scheduled_end'),
            request.form.get('notes'),
            session.get('user_id')
        ))
        conn.commit()
        conn.close()
        
        flash('Production order created successfully.', 'success')
        return redirect(url_for('manufacturing.orders'))
    
    return render_template('manufacturing/order_form.html')


# =============================================================================
# WORK CENTERS
# =============================================================================

@manufacturing_bp.route('/work-centers')
@require_login
def work_centers():
    """List all work centers."""
    conn = get_db()
    centers = conn.execute('SELECT * FROM mfg_work_centers ORDER BY code').fetchall()
    conn.close()
    return render_template('manufacturing/work_centers.html', work_centers=centers)


@manufacturing_bp.route('/work-centers/create', methods=['GET', 'POST'])
@require_login
def create_work_center():
    """Create a new work center."""
    if request.method == 'POST':
        conn = get_db()
        code = request.form.get('code')
        
        try:
            conn.execute('''
                INSERT INTO mfg_work_centers 
                (code, name, description, location, capacity_hours, efficiency, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                code,
                request.form.get('name'),
                request.form.get('description'),
                request.form.get('location'),
                request.form.get('capacity_hours', 8),
                request.form.get('efficiency', 100),
                request.form.get('status', 'ACTIVE')
            ))
            conn.commit()
            flash('Work center created successfully.', 'success')
            return redirect(url_for('manufacturing.work_centers'))
        except sqlite3.IntegrityError:
            flash(f'Work center code "{code}" already exists.', 'error')
        finally:
            conn.close()
    
    return render_template('manufacturing/work_center_form.html')


# =============================================================================
# BILL OF MATERIALS
# =============================================================================

@manufacturing_bp.route('/bom')
@require_login
def bom_list():
    """List all Bill of Materials."""
    conn = get_db()
    boms = conn.execute('''
        SELECT b.*, p.name as product_name 
        FROM mfg_bom b 
        LEFT JOIN products p ON b.product_id = p.id 
        ORDER BY b.code
    ''').fetchall()
    conn.close()
    return render_template('manufacturing/bom_list.html', boms=boms)


# =============================================================================
# ROUTINGS
# =============================================================================

@manufacturing_bp.route('/routings')
@require_login
def routings():
    """List all routings."""
    conn = get_db()
    routings = conn.execute('''
        SELECT r.*, p.name as product_name 
        FROM mfg_routings r 
        LEFT JOIN products p ON r.product_id = p.id 
        ORDER BY r.code
    ''').fetchall()
    conn.close()
    return render_template('manufacturing/routings.html', routings=routings)


# =============================================================================
# API ENDPOINTS
# =============================================================================

@manufacturing_bp.route('/api/stats')
@require_login
def api_stats():
    """Get manufacturing statistics as JSON."""
    conn = get_db()
    
    stats = {
        'orders': {},
        'work_centers': {},
        'efficiency': 0
    }
    
    orders = conn.execute('SELECT status, COUNT(*) as count FROM mfg_production_orders GROUP BY status').fetchall()
    for o in orders:
        stats['orders'][o['status']] = o['count']
    
    work_centers = conn.execute('SELECT COUNT(*) as count FROM mfg_work_centers WHERE status = ?', ('ACTIVE',)).fetchone()
    stats['work_centers']['active'] = work_centers['count'] if work_centers else 0
    
    conn.close()
    return jsonify(stats)


@manufacturing_bp.route('/api/orders', methods=['GET', 'POST'])
@require_login
def api_orders():
    """API endpoint for production orders."""
    conn = get_db()
    
    if request.method == 'POST':
        data = request.json
        order_number = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        conn.execute('''
            INSERT INTO mfg_production_orders 
            (order_number, product_id, quantity, status, priority, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            order_number,
            data.get('product_id'),
            data.get('quantity', 0),
            data.get('status', 'DRAFT'),
            data.get('priority', 'NORMAL'),
            data.get('notes'),
            session.get('user_id')
        ))
        conn.commit()
        order_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
        conn.close()
        return jsonify({'success': True, 'order_id': order_id})
    
    orders = conn.execute('SELECT * FROM mfg_production_orders ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(o) for o in orders])


@manufacturing_bp.route('/api/schedule')
@require_login
def api_schedule():
    """Get production schedule."""
    conn = get_db()
    schedule = conn.execute('''
        SELECT s.*, o.order_number, w.code as work_center_code, w.name as work_center_name
        FROM mfg_schedule s
        LEFT JOIN mfg_production_orders o ON s.order_id = o.id
        LEFT JOIN mfg_work_centers w ON s.work_center_id = w.id
        ORDER BY s.scheduled_date
    ''').fetchall()
    conn.close()
    return jsonify([dict(s) for s in schedule])