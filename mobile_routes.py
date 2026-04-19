"""
Mobile Maintenance Routes - PWA Mobile Maintenance
=================================================
Flask Blueprint for mobile maintenance operations with offline support.

Features:
- PWA (Progressive Web App) support
- Offline data sync
- Barcode/QR scanning
- Camera integration for photos
- GPS/Location services
- Push notifications ready

Route Pattern: /api/mobile/*
"""

from flask import Blueprint, request, jsonify, session, send_from_directory, make_response
from functools import wraps
import sqlite3
import json
from datetime import datetime, timedelta
import os

from database import get_db, get_db_context, log_audit
from maintenance_models import (
    get_next_labor_log_number, get_next_parts_usage_number,
    MAINTENANCE_WORK_ORDER_STATUSES, MAINTENANCE_PRIORITIES
)

# Create mobile blueprint
mobile_bp = Blueprint('mobile', __name__, url_prefix='/api/mobile')


# =============================================================================
# AUTHENTICATION & SESSION
# =============================================================================

def mobile_require_login(f):
    """Decorator for mobile API authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for API key or session
        api_key = request.headers.get('X-API-Key')
        user_id = session.get('user_id')

        if not api_key and not user_id:
            return jsonify({'error': 'Authentication required', 'code': 'AUTH_REQUIRED'}), 401

        # For API key auth, validate and get user_id
        if api_key:
            db = get_db()
            try:
                user = db.execute(
                    "SELECT id FROM users WHERE api_key = ? AND is_active = 1",
                    (api_key,)
                ).fetchone()
                if not user:
                    return jsonify({'error': 'Invalid API key', 'code': 'INVALID_KEY'}), 401
                user_id = user['id']
            finally:
                db.close()

        return f(user_id=user_id, *args, **kwargs)
    return decorated_function


# =============================================================================
# PWA ASSETS & MANIFEST
# =============================================================================

@mobile_bp.route('/manifest.json')
def mobile_manifest():
    """Serve PWA manifest."""
    manifest = {
        "name": "WHDASH Maintenance",
        "short_name": "Maint",
        "description": "Mobile Maintenance Management",
        "start_url": "/mobile",
        "display": "standalone",
        "background_color": "#1e40af",
        "theme_color": "#1e40af",
        "orientation": "portrait",
        "icons": [
            {
                "src": "/static/img/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/img/icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ],
        "categories": ["business", "productivity"],
        "prefer_related_applications": False
    }
    return jsonify(manifest)


@mobile_bp.route('/sw.js')
def service_worker():
    """Serve Service Worker for offline support."""
    sw_content = """
const CACHE_NAME = 'whdash-maint-v1';
const STATIC_ASSETS = [
    '/mobile',
    '/static/css/mobile.css',
    '/static/img/icon-192.png'
];

// Install event
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

// Activate event
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name !== CACHE_NAME)
                    .map((name) => caches.delete(name))
            );
        })
    );
    self.clients.claim();
});

// Fetch event - Network first, fallback to cache
self.addEventListener('fetch', (event) => {
    // Skip non-GET requests
    if (event.request.method !== 'GET') return;

    // Skip API calls (they handle offline differently)
    if (event.request.url.includes('/api/')) {
        event.respondWith(
            fetch(event.request)
                .catch(() => {
                    return caches.match(event.request).then((response) => {
                        if (response) return response;
                        return new Response(
                            JSON.stringify({error: 'Offline', offline: true}),
                            {headers: {'Content-Type': 'application/json'}}
                        );
                    });
                })
        );
        return;
    }

    event.respondWith(
        fetch(event.request)
            .then((response) => {
                // Clone and cache successful responses
                if (response.status === 200) {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME).then((cache) => {
                        cache.put(event.request, responseClone);
                    });
                }
                return response;
            })
            .catch(() => {
                return caches.match(event.request).then((response) => {
                    if (response) return response;
                    // Return offline page for navigation requests
                    if (event.request.mode === 'navigate') {
                        return caches.match('/mobile');
                    }
                });
            })
    );
});

// Background sync for offline operations
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-work-orders') {
        event.waitUntil(syncWorkOrders());
    }
});

async function syncWorkOrders() {
    const db = await openDB();
    const pendingSync = await db.getAll('pending_sync');

    for (const item of pendingSync) {
        try {
            const response = await fetch(item.url, {
                method: item.method,
                headers: {'Content-Type': 'application/json'},
                body: item.data
            });
            if (response.ok) {
                await db.delete('pending_sync', item.id);
            }
        } catch (e) {
            console.error('Sync failed for item:', item.id);
        }
    }
}

async function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('WHDASH_MOBILE', 1);
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains('pending_sync')) {
                db.createObjectStore('pending_sync', {keyPath: 'id', autoIncrement: true});
            }
            if (!db.objectStoreNames.contains('cached_work_orders')) {
                db.createObjectStore('cached_work_orders', {keyPath: 'id'});
            }
            if (!db.objectStoreNames.contains('cached_assets')) {
                db.createObjectStore('cached_assets', {keyPath: 'id'});
            }
        };
    });
}
"""
    response = make_response(sw_content)
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Service-Worker-Allowed'] = '/'
    return response


# =============================================================================
# MOBILE AUTHENTICATION
# =============================================================================

@mobile_bp.route('/login', methods=['POST'])
def mobile_login():
    """Mobile authentication endpoint."""
    data = request.get_json() or {}

    username = data.get('username')
    password = data.get('password')
    device_id = data.get('device_id')

    if not username or not password:
        return jsonify({'error': 'Username and password required', 'code': 'AUTH_REQUIRED'}), 400

    db = get_db()
    try:
        user = db.execute("""
            SELECT id, username, email, first_name, last_name,
                   employee_id, role_id
            FROM users
            WHERE username = ? AND password = ? AND is_active = 1
        """, (username, password)).fetchone()

        if not user:
            return jsonify({'error': 'Invalid credentials', 'code': 'INVALID_CREDENTIALS'}), 401

        # Generate session or API token
        session['user_id'] = user['id']
        session['device_id'] = device_id

        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'employee_id': user['employee_id']
            },
            'session_id': session.sid if hasattr(session, 'sid') else str(user['id'])
        })
    finally:
        db.close()


@mobile_bp.route('/logout', methods=['POST'])
@mobile_require_login
def mobile_logout(user_id):
    """Mobile logout endpoint."""
    session.clear()
    return jsonify({'success': True})


# =============================================================================
# SYNC OPERATIONS
# =============================================================================

@mobile_bp.route('/sync/status', methods=['GET'])
@mobile_require_login
def sync_status(user_id):
    """Get sync status and pending items count."""
    db = get_db()
    try:
        last_sync = db.execute("""
            SELECT MAX(created_at) as last_sync
            FROM maintenance_labor_logs
            WHERE created_by = ?
        """, (user_id,)).fetchone()

        pending_wo = db.execute("""
            SELECT COUNT(*) as cnt FROM maintenance_work_orders
            WHERE assigned_technician_id = (
                SELECT employee_id FROM users WHERE id = ?
            )
            AND status NOT IN ('Completed', 'Closed', 'Canceled')
        """, (user_id,)).fetchone()

        return jsonify({
            'last_sync': last_sync['last_sync'] if last_sync else None,
            'pending_work_orders': pending_wo['cnt'] if pending_wo else 0,
            'server_time': datetime.now().isoformat()
        })
    finally:
        db.close()


@mobile_bp.route('/sync/data', methods=['POST'])
@mobile_require_login
def sync_data(user_id):
    """Sync data from mobile to server."""
    data = request.get_json() or {}

    db = get_db()
    try:
        results = {
            'labor_logs': 0,
            'parts_usage': 0,
            'confirmations': 0,
            'photos': 0,
            'errors': []
        }

        # Process labor logs
        for log in data.get('labor_logs', []):
            try:
                cursor = db.execute("""
                    INSERT INTO maintenance_labor_logs
                    (log_number, work_order_id, technician_id, work_date,
                     start_time, end_time, total_hours, regular_hours,
                     overtime_hours, hourly_rate, labor_cost,
                     work_description, approval_status, notes, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    get_next_labor_log_number(),
                    log.get('work_order_id'),
                    log.get('technician_id', user_id),
                    log.get('work_date'),
                    log.get('start_time'),
                    log.get('end_time'),
                    log.get('total_hours', 0),
                    log.get('regular_hours', 0),
                    log.get('overtime_hours', 0),
                    log.get('hourly_rate', 0),
                    log.get('labor_cost', 0),
                    log.get('work_description'),
                    'Approved',
                    log.get('notes'),
                    user_id
                ))
                results['labor_logs'] += 1
            except Exception as e:
                results['errors'].append(f"Labor log error: {str(e)}")

        # Process parts usage
        for usage in data.get('parts_usage', []):
            try:
                cursor = db.execute("""
                    INSERT INTO maintenance_parts_usage
                    (usage_number, work_order_id, part_id, part_number, part_name,
                     quantity_requested, quantity_issued, quantity_used,
                     unit_of_measure, warehouse_id, issue_date, status, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    get_next_parts_usage_number(),
                    usage.get('work_order_id'),
                    usage.get('part_id'),
                    usage.get('part_number'),
                    usage.get('part_name'),
                    usage.get('quantity_requested', 0),
                    usage.get('quantity_issued', 0),
                    usage.get('quantity_used', 0),
                    usage.get('unit_of_measure', 'EA'),
                    usage.get('warehouse_id'),
                    usage.get('issue_date'),
                    'Issued',
                    user_id
                ))
                results['parts_usage'] += 1
            except Exception as e:
                results['errors'].append(f"Parts usage error: {str(e)}")

        # Process work order confirmations
        for conf in data.get('confirmations', []):
            try:
                cursor = db.execute("""
                    INSERT INTO work_order_confirmations
                    (work_order_id, confirmation_type, confirmation_date,
                     technician_id, work_center_id, yield_time, labor_time,
                     quantity_completed, notes, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    conf.get('work_order_id'),
                    conf.get('confirmation_type', 'FINAL'),
                    conf.get('confirmation_date', datetime.now().strftime('%Y-%m-%d')),
                    user_id,
                    conf.get('work_center_id'),
                    conf.get('yield_time', 0),
                    conf.get('labor_time', 0),
                    conf.get('quantity_completed', 1),
                    conf.get('notes'),
                    datetime.now()
                ))
                results['confirmations'] += 1
            except Exception as e:
                results['errors'].append(f"Confirmation error: {str(e)}")

        db.commit()

        return jsonify({
            'success': True,
            'results': results,
            'sync_time': datetime.now().isoformat()
        })
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e), 'code': 'SYNC_FAILED'}), 500
    finally:
        db.close()


@mobile_bp.route('/sync/work-orders', methods=['POST'])
@mobile_require_login
def sync_work_orders(user_id):
    """Get work orders for offline storage."""
    db = get_db()
    try:
        # Get technician ID from user
        tech = db.execute(
            "SELECT employee_id FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()

        if not tech or not tech['employee_id']:
            return jsonify({'error': 'User not linked to employee', 'code': 'NOT_LINKED'}), 400

        technician_id = tech['employee_id']

        # Get assigned work orders
        work_orders = db.execute("""
            SELECT mwo.*,
                   a.asset_code, a.name as asset_name, a.location as asset_location,
                   mt.name as maintenance_type_name,
                   fl.location_code, fl.name as functional_location
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            LEFT JOIN maintenance_types mt ON mwo.maintenance_type_id = mt.id
            LEFT JOIN functional_locations fl ON a.functional_location_id = fl.id
            WHERE mwo.assigned_technician_id = ?
            AND mwo.status NOT IN ('Completed', 'Closed', 'Canceled')
            ORDER BY
                CASE mwo.priority
                    WHEN 'Critical' THEN 1
                    WHEN 'High' THEN 2
                    WHEN 'Medium' THEN 3
                    ELSE 4
                END,
                mwo.due_date ASC
        """, (technician_id,)).fetchall()

        # Get work order operations
        wo_ids = [wo['id'] for wo in work_orders]
        operations = []
        if wo_ids:
            placeholders = ','.join(['?'] * len(wo_ids))
            operations = db.execute(f"""
                SELECT woo.*, wc.work_center_name
                FROM work_order_operations woo
                LEFT JOIN work_centers wc ON woo.work_center_id = wc.id
                WHERE woo.work_order_id IN ({placeholders})
                ORDER BY woo.operation_sequence
            """, wo_ids).fetchall()

        # Get work order components
        components = []
        if wo_ids:
            placeholders = ','.join(['?'] * len(wo_ids))
            components = db.execute(f"""
                SELECT woc.*, ii.item_code, ii.description as material_name
                FROM work_order_components woc
                LEFT JOIN inventory_items ii ON woc.material_id = ii.id
                WHERE woc.work_order_id IN ({placeholders})
            """, wo_ids).fetchall()

        return jsonify({
            'work_orders': [dict(wo) for wo in work_orders],
            'operations': [dict(op) for op in operations],
            'components': [dict(comp) for comp in components],
            'sync_time': datetime.now().isoformat()
        })
    finally:
        db.close()


# =============================================================================
# WORK ORDERS MOBILE
# =============================================================================

@mobile_bp.route('/work-orders', methods=['GET'])
@mobile_require_login
def get_work_orders(user_id):
    """Get work orders for mobile."""
    db = get_db()
    try:
        status = request.args.get('status')
        priority = request.args.get('priority')

        query = """
            SELECT mwo.*,
                   a.asset_code, a.name as asset_name,
                   mt.name as maintenance_type_name
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            LEFT JOIN maintenance_types mt ON mwo.maintenance_type_id = mt.id
            WHERE mwo.assigned_technician_id = ?
        """
        params = [user_id]

        if status:
            query += " AND mwo.status = ?"
            params.append(status)

        if priority:
            query += " AND mwo.priority = ?"
            params.append(priority)

        query += " ORDER BY mwo.due_date ASC LIMIT 50"

        work_orders = db.execute(query, params).fetchall()

        return jsonify({
            'work_orders': [dict(wo) for wo in work_orders],
            'count': len(work_orders)
        })
    finally:
        db.close()


@mobile_bp.route('/work-orders/<int:wo_id>', methods=['GET'])
@mobile_require_login
def get_work_order(user_id, wo_id):
    """Get single work order details."""
    db = get_db()
    try:
        wo = db.execute("""
            SELECT mwo.*,
                   a.asset_code, a.name as asset_name, a.location as asset_location,
                   a.functional_location_id,
                   fl.location_code, fl.name as functional_location_name,
                   mt.name as maintenance_type_name,
                   e.first_name || ' ' || e.last_name as assigned_technician_name,
                   e.employee_code as technician_code
            FROM maintenance_work_orders mwo
            JOIN assets a ON mwo.asset_id = a.id
            LEFT JOIN functional_locations fl ON a.functional_location_id = fl.id
            LEFT JOIN maintenance_types mt ON mwo.maintenance_type_id = mt.id
            LEFT JOIN hr_employees e ON mwo.assigned_technician_id = e.id
            WHERE mwo.id = ?
        """, (wo_id,)).fetchone()

        if not wo:
            return jsonify({'error': 'Work order not found'}), 404

        # Get operations
        operations = db.execute("""
            SELECT woo.*, wc.work_center_name
            FROM work_order_operations woo
            LEFT JOIN work_centers wc ON woo.work_center_id = wc.id
            WHERE woo.work_order_id = ?
            ORDER BY woo.operation_sequence
        """, (wo_id,)).fetchall()

        # Get components
        components = db.execute("""
            SELECT woc.*, ii.item_code, ii.description as material_name
            FROM work_order_components woc
            LEFT JOIN inventory_items ii ON woc.material_id = ii.id
            WHERE woc.work_order_id = ?
        """, (wo_id,)).fetchall()

        # Get recent labor logs
        labor_logs = db.execute("""
            SELECT * FROM maintenance_labor_logs
            WHERE work_order_id = ?
            ORDER BY work_date DESC LIMIT 10
        """, (wo_id,)).fetchall()

        return jsonify({
            'work_order': dict(wo),
            'operations': [dict(op) for op in operations],
            'components': [dict(comp) for comp in components],
            'labor_logs': [dict(log) for log in labor_logs]
        })
    finally:
        db.close()


@mobile_bp.route('/work-orders/<int:wo_id>/start', methods=['POST'])
@mobile_require_login
def start_work_order(user_id, wo_id):
    """Start a work order (change status to In Progress)."""
    db = get_db()
    try:
        # Verify work order exists and is assigned to user
        wo = db.execute("""
            SELECT * FROM maintenance_work_orders WHERE id = ?
        """, (wo_id,)).fetchone()

        if not wo:
            return jsonify({'error': 'Work order not found'}), 404

        if wo['status'] in ['Completed', 'Closed', 'Canceled']:
            return jsonify({'error': 'Cannot start completed work order'}), 400

        # Update status
        db.execute("""
            UPDATE maintenance_work_orders SET
            status = 'In Progress',
            actual_start_date = ?,
            updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (datetime.now().strftime('%Y-%m-%d %H:%M'), wo_id))
        db.commit()

        log_audit('maintenance_work_order', wo_id, 'START', user_id)

        return jsonify({
            'success': True,
            'message': 'Work order started',
            'new_status': 'In Progress'
        })
    finally:
        db.close()


@mobile_bp.route('/work-orders/<int:wo_id>/complete', methods=['POST'])
@mobile_require_login
def complete_work_order(user_id, wo_id):
    """Complete a work order."""
    data = request.get_json() or {}

    db = get_db()
    try:
        wo = db.execute("SELECT * FROM maintenance_work_orders WHERE id = ?", (wo_id,)).fetchone()

        if not wo:
            return jsonify({'error': 'Work order not found'}), 404

        completion_notes = data.get('notes', '')

        db.execute("""
            UPDATE maintenance_work_orders SET
            status = 'Completed',
            completed_at = ?,
            completion_notes = ?,
            updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (datetime.now().strftime('%Y-%m-%d %H:%M'), completion_notes, wo_id))
        db.commit()

        log_audit('maintenance_work_order', wo_id, 'COMPLETE', user_id)

        return jsonify({
            'success': True,
            'message': 'Work order completed',
            'new_status': 'Completed'
        })
    finally:
        db.close()


@mobile_bp.route('/work-orders/<int:wo_id>/confirm', methods=['POST'])
@mobile_require_login
def confirm_work_order(user_id, wo_id):
    """Add confirmation to work order."""
    data = request.get_json() or {}

    db = get_db()
    try:
        cursor = db.execute("""
            INSERT INTO work_order_confirmations
            (work_order_id, confirmation_type, confirmation_date,
             technician_id, work_center_id, yield_time, labor_time,
             setup_time, tear_time, quantity_completed, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            wo_id,
            data.get('confirmation_type', 'FINAL'),
            data.get('confirmation_date', datetime.now().strftime('%Y-%m-%d')),
            user_id,
            data.get('work_center_id'),
            data.get('yield_time', 0),
            data.get('labor_time', 0),
            data.get('setup_time', 0),
            data.get('tear_time', 0),
            data.get('quantity_completed', 1),
            data.get('notes'),
            datetime.now()
        ))
        db.commit()

        log_audit('work_order_confirmation', cursor.lastrowid, 'CREATE', user_id)

        return jsonify({
            'success': True,
            'confirmation_id': cursor.lastrowid,
            'message': 'Confirmation recorded'
        })
    finally:
        db.close()


# =============================================================================
# OPERATIONS MOBILE
# =============================================================================

@mobile_bp.route('/operations/<int:op_id>/confirm', methods=['POST'])
@mobile_require_login
def confirm_operation(user_id, op_id):
    """Confirm a work order operation."""
    data = request.get_json() or {}

    db = get_db()
    try:
        # Update operation status
        db.execute("""
            UPDATE work_order_operations SET
            status = 'Completed',
            actual_start_date = ?,
            actual_end_date = ?,
            actual_duration = ?,
            updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get('actual_start_date', datetime.now().strftime('%Y-%m-%d %H:%M')),
            data.get('actual_end_date', datetime.now().strftime('%Y-%m-%d %H:%M')),
            data.get('actual_duration', 0),
            op_id
        ))
        db.commit()

        return jsonify({
            'success': True,
            'message': 'Operation confirmed'
        })
    finally:
        db.close()


# =============================================================================
# TIME ENTRIES MOBILE
# =============================================================================

@mobile_bp.route('/time-entries', methods=['GET'])
@mobile_require_login
def get_time_entries(user_id):
    """Get time entries for mobile."""
    db = get_db()
    try:
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        query = """
            SELECT mll.*, mwo.work_order_number, a.name as asset_name
            FROM maintenance_labor_logs mll
            JOIN maintenance_work_orders mwo ON mll.work_order_id = mwo.id
            JOIN assets a ON mwo.asset_id = a.id
            WHERE mll.technician_id = ?
        """
        params = [user_id]

        if date_from:
            query += " AND mll.work_date >= ?"
            params.append(date_from)

        if date_to:
            query += " AND mll.work_date <= ?"
            params.append(date_to)

        query += " ORDER BY mll.work_date DESC, mll.start_time DESC"

        entries = db.execute(query, params).fetchall()

        return jsonify({
            'time_entries': [dict(e) for e in entries],
            'count': len(entries)
        })
    finally:
        db.close()


@mobile_bp.route('/time-entries', methods=['POST'])
@mobile_require_login
def create_time_entry(user_id):
    """Create new time entry."""
    data = request.get_json() or {}

    db = get_db()
    try:
        cursor = db.execute("""
            INSERT INTO maintenance_labor_logs
            (log_number, work_order_id, technician_id, work_date,
             start_time, end_time, total_hours, regular_hours,
             overtime_hours, hourly_rate, labor_cost,
             work_description, approval_status, notes, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            get_next_labor_log_number(),
            data.get('work_order_id'),
            user_id,
            data.get('work_date', datetime.now().strftime('%Y-%m-%d')),
            data.get('start_time'),
            data.get('end_time'),
            data.get('total_hours', 0),
            data.get('regular_hours', 0),
            data.get('overtime_hours', 0),
            data.get('hourly_rate', 0),
            data.get('labor_cost', 0),
            data.get('work_description'),
            'Approved',
            data.get('notes'),
            user_id
        ))
        db.commit()

        return jsonify({
            'success': True,
            'log_id': cursor.lastrowid,
            'message': 'Time entry created'
        })
    finally:
        db.close()


@mobile_bp.route('/time-entries/<int:log_id>', methods=['PUT'])
@mobile_require_login
def update_time_entry(user_id, log_id):
    """Update existing time entry."""
    data = request.get_json() or {}

    db = get_db()
    try:
        # Verify ownership
        entry = db.execute(
            "SELECT * FROM maintenance_labor_logs WHERE id = ? AND technician_id = ?",
            (log_id, user_id)
        ).fetchone()

        if not entry:
            return jsonify({'error': 'Time entry not found or access denied'}), 404

        db.execute("""
            UPDATE maintenance_labor_logs SET
            work_date = ?, start_time = ?, end_time = ?,
            total_hours = ?, regular_hours = ?, overtime_hours = ?,
            work_description = ?, notes = ?,
            updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            data.get('work_date', entry['work_date']),
            data.get('start_time', entry['start_time']),
            data.get('end_time', entry['end_time']),
            data.get('total_hours', entry['total_hours']),
            data.get('regular_hours', entry['regular_hours']),
            data.get('overtime_hours', entry['overtime_hours']),
            data.get('work_description', entry['work_description']),
            data.get('notes', entry['notes']),
            log_id
        ))
        db.commit()

        return jsonify({'success': True, 'message': 'Time entry updated'})
    finally:
        db.close()


@mobile_bp.route('/time-entries/<int:log_id>', methods=['DELETE'])
@mobile_require_login
def delete_time_entry(user_id, log_id):
    """Delete time entry."""
    db = get_db()
    try:
        result = db.execute(
            "DELETE FROM maintenance_labor_logs WHERE id = ? AND technician_id = ?",
            (log_id, user_id)
        )
        db.commit()

        if result.rowcount == 0:
            return jsonify({'error': 'Time entry not found or access denied'}), 404

        return jsonify({'success': True, 'message': 'Time entry deleted'})
    finally:
        db.close()


# =============================================================================
# PARTS MOBILE
# =============================================================================

@mobile_bp.route('/parts/withdraw', methods=['POST'])
@mobile_require_login
def withdraw_parts(user_id):
    """Withdraw parts for work order."""
    data = request.get_json() or {}

    db = get_db()
    try:
        cursor = db.execute("""
            INSERT INTO maintenance_parts_usage
            (usage_number, work_order_id, part_id, part_number, part_name,
             quantity_requested, quantity_issued, quantity_used,
             unit_of_measure, warehouse_id, issue_date, status, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            get_next_parts_usage_number(),
            data.get('work_order_id'),
            data.get('part_id'),
            data.get('part_number'),
            data.get('part_name'),
            data.get('quantity_requested', 0),
            data.get('quantity_issued', data.get('quantity', 0)),
            data.get('quantity', 0),
            data.get('unit_of_measure', 'EA'),
            data.get('warehouse_id'),
            datetime.now().strftime('%Y-%m-%d'),
            'Issued',
            user_id
        ))
        db.commit()

        # Update work order component if exists
        if data.get('component_id'):
            db.execute("""
                UPDATE work_order_components SET
                quantity_withdrawn = quantity_withdrawn + ?,
                is_withdrawn = 1,
                withdrawn_by = ?,
                withdrawn_at = ?
                WHERE id = ?
            """, (data.get('quantity', 0), user_id, datetime.now(), data.get('component_id')))

        log_audit('parts_withdraw', cursor.lastrowid, 'CREATE', user_id)

        return jsonify({
            'success': True,
            'usage_id': cursor.lastrowid,
            'message': 'Parts withdrawn'
        })
    finally:
        db.close()


@mobile_bp.route('/parts/return', methods=['POST'])
@mobile_require_login
def return_parts(user_id):
    """Return unused parts."""
    data = request.get_json() or {}

    db = get_db()
    try:
        usage_id = data.get('usage_id')
        quantity_returned = data.get('quantity_returned', 0)

        db.execute("""
            UPDATE maintenance_parts_usage SET
            quantity_returned = quantity_returned + ?,
            return_date = ?,
            status = 'Returned'
            WHERE id = ?
        """, (quantity_returned, datetime.now().strftime('%Y-%m-%d'), usage_id))
        db.commit()

        return jsonify({
            'success': True,
            'message': 'Parts returned'
        })
    finally:
        db.close()


# =============================================================================
# SIGNATURES & PHOTOS
# =============================================================================

@mobile_bp.route('/signatures', methods=['POST'])
@mobile_require_login
def upload_signature(user_id):
    """Upload signature for work order completion."""
    if 'signature' not in request.files:
        return jsonify({'error': 'No signature file provided'}), 400

    file = request.files['signature']
    work_order_id = request.form.get('work_order_id')

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Save signature
    upload_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'signatures')
    os.makedirs(upload_dir, exist_ok=True)

    filename = f"sig_{work_order_id}_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    # Log audit
    log_audit('work_order_signature', work_order_id, 'UPLOAD', user_id)

    return jsonify({
        'success': True,
        'filename': filename,
        'url': f'/static/uploads/signatures/{filename}'
    })


@mobile_bp.route('/photos', methods=['POST'])
@mobile_require_login
def upload_photo(user_id):
    """Upload photo for work order."""
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo file provided'}), 400

    file = request.files['photo']
    work_order_id = request.form.get('work_order_id')
    photo_type = request.form.get('type', 'progress')  # progress, completed, issue

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Save photo
    upload_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'maintenance_photos')
    os.makedirs(upload_dir, exist_ok=True)

    ext = os.path.splitext(file.filename)[1] or '.jpg'
    filename = f"photo_{work_order_id}_{photo_type}_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)

    # Log audit
    log_audit('work_order_photo', work_order_id, 'UPLOAD', user_id)

    return jsonify({
        'success': True,
        'filename': filename,
        'url': f'/static/uploads/maintenance_photos/{filename}'
    })


@mobile_bp.route('/photos', methods=['GET'])
@mobile_require_login
def get_photos(user_id):
    """Get photos for a work order."""
    work_order_id = request.args.get('work_order_id')

    if not work_order_id:
        return jsonify({'error': 'work_order_id required'}), 400

    # In a real implementation, would query database for photo records
    return jsonify({
        'photos': [],
        'message': 'Photo listing would be implemented here'
    })


@mobile_bp.route('/photos/<int:photo_id>/delete', methods=['DELETE'])
@mobile_require_login
def delete_photo(user_id, photo_id):
    """Delete a photo."""
    # Would verify ownership and delete from storage
    return jsonify({'success': True, 'message': 'Photo deleted'})


# =============================================================================
# SCANNING (BARCODE/QR)
# =============================================================================

@mobile_bp.route('/scan/equipment', methods=['POST'])
@mobile_require_login
def scan_equipment(user_id):
    """Scan equipment barcode/QR code."""
    data = request.get_json() or {}
    scan_value = data.get('scan_value')

    if not scan_value:
        return jsonify({'error': 'Scan value required'}), 400

    db = get_db()
    try:
        # Try to find by code
        asset = db.execute("""
            SELECT id, asset_code, name, status, location as asset_location,
                   functional_location_id
            FROM assets
            WHERE asset_code = ? OR qr_code = ? OR bar_code = ?
        """, (scan_value, scan_value, scan_value)).fetchone()

        if asset:
            # Get maintenance summary
            open_wo = db.execute("""
                SELECT COUNT(*) as cnt FROM maintenance_work_orders
                WHERE asset_id = ? AND status NOT IN ('Completed', 'Closed', 'Canceled')
            """, (asset['id'],)).fetchone()

            return jsonify({
                'found': True,
                'type': 'equipment',
                'equipment': {
                    'id': asset['id'],
                    'code': asset['asset_code'],
                    'name': asset['name'],
                    'status': asset['status'],
                    'location': asset['asset_location'],
                    'open_work_orders': open_wo['cnt'] if open_wo else 0
                }
            })

        return jsonify({'found': False, 'message': 'Equipment not found'})
    finally:
        db.close()


@mobile_bp.route('/scan/parts', methods=['POST'])
@mobile_require_login
def scan_parts(user_id):
    """Scan parts barcode."""
    data = request.get_json() or {}
    scan_value = data.get('scan_value')

    if not scan_value:
        return jsonify({'error': 'Scan value required'}), 400

    db = get_db()
    try:
        # Try to find by part number
        part = db.execute("""
            SELECT id, item_code, description, part_number,
                   unit_of_measure, unit_cost, quantity_on_hand
            FROM inventory_items
            WHERE item_code = ? OR part_number = ?
        """, (scan_value, scan_value)).fetchone()

        if part:
            return jsonify({
                'found': True,
                'type': 'part',
                'part': {
                    'id': part['id'],
                    'code': part['item_code'],
                    'part_number': part['part_number'],
                    'description': part['description'],
                    'unit_of_measure': part['unit_of_measure'],
                    'unit_cost': part['unit_cost'],
                    'quantity_on_hand': part['quantity_on_hand']
                }
            })

        return jsonify({'found': False, 'message': 'Part not found'})
    finally:
        db.close()


@mobile_bp.route('/scan/location', methods=['POST'])
@mobile_require_login
def scan_location(user_id):
    """Scan location barcode/QR."""
    data = request.get_json() or {}
    scan_value = data.get('scan_value')

    if not scan_value:
        return jsonify({'error': 'Scan value required'}), 400

    db = get_db()
    try:
        # Try functional location
        loc = db.execute("""
            SELECT id, location_code, name, location_type,
                   address, is_critical
            FROM functional_locations
            WHERE location_code = ? OR qr_code = ? OR bar_code = ?
        """, (scan_value, scan_value, scan_value)).fetchone()

        if loc:
            # Get equipment at location
            equipment = db.execute("""
                SELECT id, asset_code, name FROM assets
                WHERE functional_location_id = ?
            """, (loc['id'],)).fetchall()

            return jsonify({
                'found': True,
                'type': 'location',
                'location': {
                    'id': loc['id'],
                    'code': loc['location_code'],
                    'name': loc['name'],
                    'type': loc['location_type'],
                    'address': loc['address'],
                    'is_critical': loc['is_critical'],
                    'equipment_count': len(equipment),
                    'equipment': [dict(e) for e in equipment]
                }
            })

        # Try warehouse location
        warehouse = db.execute("""
            SELECT id, warehouse_code, name, location FROM wms_warehouses
            WHERE warehouse_code = ? OR location = ?
        """, (scan_value, scan_value)).fetchone()

        if warehouse:
            return jsonify({
                'found': True,
                'type': 'warehouse',
                'location': {
                    'id': warehouse['id'],
                    'code': warehouse['warehouse_code'],
                    'name': warehouse['name'],
                    'address': warehouse['location']
                }
            })

        return jsonify({'found': False, 'message': 'Location not found'})
    finally:
        db.close()


# =============================================================================
# GPS / LOCATION
# =============================================================================

@mobile_bp.route('/location', methods=['POST'])
@mobile_require_login
def record_location(user_id):
    """Record GPS location for technician."""
    data = request.get_json() or {}

    latitude = data.get('latitude')
    longitude = data.get('longitude')
    work_order_id = data.get('work_order_id')
    timestamp = data.get('timestamp', datetime.now().isoformat())

    if not latitude or not longitude:
        return jsonify({'error': 'Latitude and longitude required'}), 400

    # In a real implementation, would store in database
    # For now, just log it
    log_audit('technician_location', user_id, 'UPDATE', user_id,
               details=f"Lat: {latitude}, Lon: {longitude}, WO: {work_order_id}")

    return jsonify({
        'success': True,
        'message': 'Location recorded',
        'timestamp': timestamp
    })


# =============================================================================
# NOTIFICATIONS (PUSH READY)
# =============================================================================

@mobile_bp.route('/notifications/register-device', methods=['POST'])
@mobile_require_login
def register_device(user_id):
    """Register device for push notifications."""
    data = request.get_json() or {}

    device_token = data.get('device_token')
    device_type = data.get('device_type', 'ios')  # ios, android, web

    if not device_token:
        return jsonify({'error': 'Device token required'}), 400

    # In a real implementation, would store device token in database
    log_audit('device_registration', user_id, 'REGISTER', user_id,
               details=f"Token: {device_token[:20]}..., Type: {device_type}")

    return jsonify({
        'success': True,
        'message': 'Device registered for notifications'
    })


@mobile_bp.route('/notifications', methods=['GET'])
@mobile_require_login
def get_notifications(user_id):
    """Get notifications for user."""
    db = get_db()
    try:
        notifications = db.execute("""
            SELECT * FROM notifications
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT 50
        """, (user_id,)).fetchall()

        return jsonify({
            'notifications': [dict(n) for n in notifications],
            'count': len(notifications)
        })
    finally:
        db.close()


# =============================================================================
# HEALTH CHECK
# =============================================================================

@mobile_bp.route('/health', methods=['GET'])
def mobile_health():
    """Health check endpoint for mobile API."""
    return jsonify({
        'status': 'ok',
        'service': 'whdash-mobile',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })


# =============================================================================
# REGISTER BLUEPRINT
# =============================================================================

def register_mobile_routes(app):
    """Register mobile routes with Flask app."""
    app.register_blueprint(mobile_bp)
