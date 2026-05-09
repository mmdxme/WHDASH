"""
E-commerce Integration Routes
============================
Flask routes for the E-commerce Integration module.
Handles:
- Dashboard
- Channel Management
- Order Sync
- Inventory Sync
- Customer Sync
- Product Mapping
- Reports
- Settings
- Audit Logs
"""

import json
import sqlite3
from datetime import datetime, timedelta
from flask import Blueprint, request, session, redirect, url_for, flash, render_template, jsonify, send_file
from functools import wraps

from database import get_db, get_db_context, get_one, get_all, log_audit
from permissions import user_has_permission, require_permission, get_user_permissions_cached
from ecommerce_models import (
    init_ecommerce_tables, EcommerceChannel, EcommerceChannelProfile,
    EcommerceOrderImport, EcommerceOrderLine, EcommerceInventorySync,
    EcommerceCustomerImport, EcommerceException, EcommerceSyncJob,
    EcommerceSyncQueue, EcommerceAuditLog, EcommerceProductMapping,
    EcommerceCategoryMapping, EcommerceWarehouseMapping, EcommerceSetting
)

# Import export utilities
from export_utils import (
    send_export_response,
    get_export_columns
)

# Create blueprint
ecommerce_bp = Blueprint('ecommerce', __name__, url_prefix='/ecommerce')

# =============================================================================
# DECORATORS
# =============================================================================

def require_ecommerce_permission(resource: str, action: str = 'view'):
    """Decorator to require e-commerce permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please login to access this page.", "error")
                return redirect(url_for('login'))
            
            user_id = session['user_id']
            if not user_has_permission(user_id, 'ecommerce', resource, action):
                flash(f"Access Denied. You don't have permission to {action} {resource}.", "error")
                return redirect(url_for('index'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_user_id():
    """Get current user ID from session."""
    return session.get('user_id', 0)


def get_current_user_name():
    """Get current user name."""
    user_id = session.get('user_id', 0)
    if user_id:
        user = get_one("SELECT username FROM users WHERE id = ?", (user_id,))
        if user:
            return user['username']
    return "System"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def init_ecommerce():
    """Initialize e-commerce module."""
    init_ecommerce_tables()


def get_ecommerce_setting(key: str, default: str = "") -> str:
    """Get e-commerce setting value."""
    setting = get_one(
        "SELECT setting_value FROM ecommerce_settings WHERE setting_key = ?",
        (key,)
    )
    return setting['setting_value'] if setting else default


def log_ecommerce_audit(action: str, entity_type: str, entity_id: int,
                        entity_reference: str = "", before_state: str = "",
                        after_state: str = "", channel_id: int = 0,
                        channel_name: str = "", company_id: int = 0):
    """Log e-commerce audit entry."""
    user_id = get_current_user_id()
    user_name = get_current_user_name()
    
    with get_db_context() as db:
        db.execute("""
            INSERT INTO ecommerce_audit_logs 
            (log_type, action, channel_id, channel_name, company_id, user_id, user_name,
             entity_type, entity_id, entity_reference, before_state, after_state,
             ip_address, user_agent, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, ('sync', action, channel_id, channel_name, company_id, user_id, user_name,
              entity_type, entity_id, entity_reference, before_state, after_state,
              request.remote_addr if request else '',
              request.headers.get('User-Agent', '') if request else ''))
        db.commit()


def create_exception(exception_type: str, title: str, description: str,
                     channel_id: int = 0, channel_name: str = "",
                     reference_type: str = "", reference_id: int = 0,
                     external_ref: str = "", internal_ref: str = "",
                     source_data: str = "", severity: str = "medium") -> str:
    """Create an e-commerce exception with auto-generated number."""
    exception_number = f"EXC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    with get_db_context() as db:
        db.execute("""
            INSERT INTO ecommerce_exceptions
            (exception_number, exception_type, title, description, channel_id, channel_name,
             reference_type, order_import_id, customer_import_id, inventory_sync_id,
             external_reference, internal_reference, source_data, severity,
             created_at, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), ?)
        """, (exception_number, exception_type, title, description, channel_id, channel_name,
              reference_type, reference_id if reference_type == 'order' else 0,
              reference_id if reference_type == 'customer' else 0,
              reference_id if reference_type == 'inventory' else 0,
              external_ref, internal_ref, source_data, severity,
              get_current_user_id()))
        db.commit()
    
    return exception_number


def generate_exception_number() -> str:
    """Generate unique exception number."""
    return f"EXC-{datetime.now().strftime('%Y%m%d%H%M%S')}"


# =============================================================================
# FLOW INTEGRATION HELPER FUNCTIONS
# =============================================================================

def create_ecommerce_flow_notification(
    notification_type: str,
    title: str,
    message: str,
    channel_id: int = 0,
    channel_name: str = "",
    exception_number: str = "",
    entity_type: str = "",
    entity_id: int = 0,
    entity_reference: str = "",
    priority: str = "NORMAL",
    action_url: str = "",
    company_id: int = 0
):
    """
    Create a Flow notification for e-commerce events.
    Types: ORDER_IMPORTED, ORDER_FAILED, SYNC_FAILED, INVENTORY_ALERT,
           LOW_STOCK, EXCEPTION_CREATED, CHANNEL_HEALTH, REFUND_REQUEST,
           RETURN_REQUEST, MAPPING_ERROR, PRICING_ALERT
    """
    user_id = get_current_user_id()

    try:
        with get_db_context() as db:
            db.execute("""
                INSERT INTO ecommerce_flow_notifications
                (notification_type, title, message, entity_type, entity_id,
                 entity_reference, channel_id, channel_name, exception_number,
                 priority, action_url, created_by, company_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                notification_type, title, message, entity_type, entity_id,
                entity_reference, channel_id, channel_name, exception_number,
                priority, action_url, user_id, company_id
            ))
            db.commit()
            return True
    except Exception as e:
        # Log but don't fail - Flow notifications are non-critical
        print(f"Failed to create Flow notification: {e}")
        return False


def notify_channel_health_alert(channel_id: int, channel_name: str, health_status: str, message: str, company_id: int = 0):
    """Send alert when channel health degrades."""
    priority = "HIGH" if health_status == "critical" else "NORMAL"
    return create_ecommerce_flow_notification(
        notification_type="CHANNEL_HEALTH_ALERT",
        title=f"Channel Health Alert: {channel_name}",
        message=message,
        channel_id=channel_id,
        channel_name=channel_name,
        priority=priority,
        action_url=f"/ecommerce/channels/{channel_id}/view",
        company_id=company_id
    )


def notify_sync_failure(channel_id: int, channel_name: str, sync_type: str, error_message: str, company_id: int = 0):
    """Send alert when sync fails."""
    return create_ecommerce_flow_notification(
        notification_type="SYNC_FAILURE",
        title=f"{sync_type.title()} Sync Failed: {channel_name}",
        message=error_message,
        channel_id=channel_id,
        channel_name=channel_name,
        priority="HIGH",
        action_url=f"/ecommerce/sync/jobs",
        company_id=company_id
    )


def notify_exception_created(exception_number: str, exception_type: str, title: str, severity: str, channel_id: int = 0, channel_name: str = "", company_id: int = 0):
    """Send notification when new exception is created."""
    priority = "HIGH" if severity in ("critical", "high") else "NORMAL"
    return create_ecommerce_flow_notification(
        notification_type="EXCEPTION_CREATED",
        title=f"New {exception_type}: {title[:50]}",
        message=f"Severity: {severity.upper()}",
        channel_id=channel_id,
        channel_name=channel_name,
        exception_number=exception_number,
        entity_type="exception",
        entity_reference=exception_number,
        priority=priority,
        action_url=f"/ecommerce/exceptions/{exception_number}/view",
        company_id=company_id
    )


def notify_low_stock(channel_id: int, channel_name: str, product_name: str, current_stock: int, company_id: int = 0):
    """Send alert when product stock is low."""
    return create_ecommerce_flow_notification(
        notification_type="LOW_STOCK_ALERT",
        title=f"Low Stock Alert: {product_name[:40]}",
        message=f"Current stock: {current_stock} units on {channel_name}",
        channel_id=channel_id,
        channel_name=channel_name,
        priority="NORMAL",
        action_url=f"/ecommerce/inventory",
        company_id=company_id
    )


def notify_refund_request(exception_number: str, order_ref: str, amount: float, channel_name: str, company_id: int = 0):
    """Send notification for pending refund review."""
    return create_ecommerce_flow_notification(
        notification_type="REFUND_REQUEST",
        title=f"Refund Request: {order_ref}",
        message=f"Amount: ${amount:.2f} on {channel_name}",
        channel_name=channel_name,
        exception_number=exception_number,
        entity_type="refund",
        entity_reference=order_ref,
        priority="NORMAL",
        action_url=f"/ecommerce/exceptions/{exception_number}/view",
        company_id=company_id
    )


def notify_return_request(exception_number: str, order_ref: str, channel_name: str, company_id: int = 0):
    """Send notification for pending return review."""
    return create_ecommerce_flow_notification(
        notification_type="RETURN_REQUEST",
        title=f"Return Request: {order_ref}",
        message=f"Return request on {channel_name}",
        channel_name=channel_name,
        exception_number=exception_number,
        entity_type="return",
        entity_reference=order_ref,
        priority="NORMAL",
        action_url=f"/ecommerce/exceptions/{exception_number}/view",
        company_id=company_id
    )


def notify_order_imported(order_number: str, channel_name: str, total_amount: float, company_id: int = 0):
    """Send notification when new order is imported."""
    return create_ecommerce_flow_notification(
        notification_type="ORDER_IMPORTED",
        title=f"New Order: {order_number}",
        message=f"Amount: ${total_amount:.2f} from {channel_name}",
        channel_name=channel_name,
        entity_type="order",
        entity_reference=order_number,
        priority="NORMAL",
        action_url=f"/ecommerce/orders",
        company_id=company_id
    )


# =============================================================================
# ROUTE: E-COMMERCE DASHBOARD
# =============================================================================

@ecommerce_bp.route('/')
@ecommerce_bp.route('/dashboard')
@require_ecommerce_permission('dashboard', 'view')
def dashboard():
    """E-commerce Dashboard."""
    user_id = get_current_user_id()
    company_id = session.get('company_id', 0)
    
    # Get dashboard statistics
    stats = {
        'total_channels': 0,
        'active_channels': 0,
        'pending_orders': 0,
        'synced_orders_today': 0,
        'failed_orders': 0,
        'pending_customers': 0,
        'duplicate_customers': 0,
        'inventory_sync_failures': 0,
        'open_exceptions': 0,
        'total_orders_today': 0,
        'total_revenue_today': 0.0,
    }
    
    with get_db_context() as db:
        # Channel counts
        ch = db.execute("""
            SELECT COUNT(*) as cnt, SUM(is_active) as active
            FROM ecommerce_channels WHERE company_id = ?
        """, (company_id,)).fetchone()
        stats['total_channels'] = ch['cnt'] if ch else 0
        stats['active_channels'] = ch['active'] if ch and ch['active'] else 0
        
        # Order stats
        today = datetime.now().strftime('%Y-%m-%d')
        orders = db.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN sync_status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN sync_status = 'failed' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN DATE(imported_at) = DATE('now') THEN 1 ELSE 0 END) as today,
                SUM(CASE WHEN DATE(imported_at) = DATE('now') THEN total_amount ELSE 0 END) as revenue
            FROM ecommerce_order_imports
            WHERE company_id = ?
        """, (company_id,)).fetchone()
        if orders:
            stats['pending_orders'] = orders['pending'] or 0
            stats['failed_orders'] = orders['failed'] or 0
            stats['synced_orders_today'] = orders['today'] or 0
            stats['total_revenue_today'] = orders['revenue'] or 0.0
        
        # Customer stats
        cust = db.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN sync_status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN duplicate_review_status = 'pending' AND sync_status = 'duplicate' THEN 1 ELSE 0 END) as duplicates
            FROM ecommerce_customer_imports
            WHERE company_id = ?
        """, (company_id,)).fetchone()
        if cust:
            stats['pending_customers'] = cust['pending'] or 0
            stats['duplicate_customers'] = cust['duplicates'] or 0
        
        # Inventory sync failures
        inv = db.execute("""
            SELECT COUNT(*) as cnt FROM ecommerce_inventory_syncs
            WHERE sync_status = 'failed' AND company_id = ?
        """, (company_id,)).fetchone()
        stats['inventory_sync_failures'] = inv['cnt'] if inv else 0
        
        # Open exceptions
        exc = db.execute("""
            SELECT COUNT(*) as cnt FROM ecommerce_exceptions
            WHERE status IN ('open', 'in_review') AND company_id = ?
        """, (company_id,)).fetchone()
        stats['open_exceptions'] = exc['cnt'] if exc else 0
    
    # Recent orders
    recent_orders = get_all("""
        SELECT o.*, c.channel_name
        FROM ecommerce_order_imports o
        LEFT JOIN ecommerce_channels c ON o.channel_id = c.id
        WHERE o.company_id = ?
        ORDER BY o.imported_at DESC
        LIMIT 10
    """, (company_id,))
    
    # Recent exceptions
    recent_exceptions = get_all("""
        SELECT * FROM ecommerce_exceptions
        WHERE company_id = ? AND status IN ('open', 'in_review')
        ORDER BY created_at DESC
        LIMIT 10
    """, (company_id,))
    
    # Channel performance
    channel_perf = get_all("""
        SELECT 
            c.channel_name,
            COUNT(o.id) as order_count,
            SUM(o.total_amount) as total_sales,
            SUM(CASE WHEN o.sync_status = 'synced' THEN 1 ELSE 0 END) as synced,
            SUM(CASE WHEN o.sync_status = 'failed' THEN 1 ELSE 0 END) as failed
        FROM ecommerce_channels c
        LEFT JOIN ecommerce_order_imports o ON c.id = o.channel_id
        WHERE c.company_id = ?
        GROUP BY c.id
        ORDER BY total_sales DESC
        LIMIT 5
    """, (company_id,))
    
    return render_template('ecommerce/dashboard.html',
                         stats=stats,
                         recent_orders=recent_orders,
                         recent_exceptions=recent_exceptions,
                         channel_performance=channel_perf)


# =============================================================================
# ROUTE: CHANNEL MANAGEMENT
# =============================================================================

@ecommerce_bp.route('/channels')
@require_ecommerce_permission('channels', 'view')
def channels_list():
    """List all e-commerce channels."""
    company_id = session.get('company_id', 0)
    
    channels = get_all("""
        SELECT c.*, 
               (SELECT COUNT(*) FROM ecommerce_order_imports WHERE channel_id = c.id) as order_count,
               (SELECT COUNT(*) FROM ecommerce_exceptions WHERE channel_id = c.id AND status = 'open') as exception_count
        FROM ecommerce_channels c
        WHERE c.company_id = ?
        ORDER BY c.channel_name
    """, (company_id,))
    
    return render_template('ecommerce/channels/list.html', channels=channels)


@ecommerce_bp.route('/channels/create', methods=['GET', 'POST'])
@require_ecommerce_permission('channels', 'create')
def channels_create():
    """Create new e-commerce channel."""
    company_id = session.get('company_id', 0)
    user_id = session['user_id']
    
    if request.method == 'POST':
        channel_code = request.form.get('channel_code', '').strip()
        channel_name = request.form.get('channel_name', '').strip()
        channel_type = request.form.get('channel_type', 'website')
        warehouse_id = request.form.get('warehouse_id', 0)
        api_endpoint = request.form.get('api_endpoint', '').strip()
        api_key = request.form.get('api_key', '').strip()
        api_secret = request.form.get('api_secret', '').strip()
        webhook_url = request.form.get('webhook_url', '').strip()
        sync_direction = request.form.get('sync_direction', 'bidirectional')
        notes = request.form.get('notes', '').strip()
        
        # Validation
        if not channel_code or not channel_name:
            flash("Channel code and name are required.", "error")
            return render_template('ecommerce/channels/create.html')
        
        # Check for duplicate code
        existing = get_one(
            "SELECT id FROM ecommerce_channels WHERE channel_code = ?",
            (channel_code,)
        )
        if existing:
            flash("Channel code already exists.", "error")
            return render_template('ecommerce/channels/create.html')
        
        with get_db_context() as db:
            cursor = db.execute("""
                INSERT INTO ecommerce_channels
                (channel_code, channel_name, channel_type, company_id, warehouse_id,
                 api_endpoint, api_key, api_secret, webhook_url, sync_direction,
                 notes, created_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (channel_code, channel_name, channel_type, company_id, warehouse_id,
                  api_endpoint, api_key, api_secret, webhook_url, sync_direction,
                  notes, user_id))
            channel_id = cursor.lastrowid
            
            # Create default channel profile
            db.execute("""
                INSERT INTO ecommerce_channel_profiles (channel_id, profile_name, created_at)
                VALUES (?, ?, datetime('now'))
            """, (channel_id, f"{channel_name} Profile"))
            
            db.commit()
        
        log_ecommerce_audit('created', 'channel', channel_id, channel_code,
                           channel_id=channel_id, channel_name=channel_name,
                           company_id=company_id, after_state=json.dumps({
                               'channel_code': channel_code,
                               'channel_name': channel_name,
                               'channel_type': channel_type
                           }))
        
        flash(f"Channel '{channel_name}' created successfully.", "success")
        return redirect(url_for('ecommerce.channels_list'))
    
    # Get warehouses for dropdown
    warehouses = get_all("""
        SELECT w.id, w.warehouse_name, w.warehouse_code
        FROM warehouses w
        WHERE w.company_id = ? OR w.company_id = 0
        ORDER BY w.warehouse_name
    """, (company_id,))
    
    return render_template('ecommerce/channels/create.html', warehouses=warehouses)


@ecommerce_bp.route('/channels/<int:channel_id>/edit', methods=['GET', 'POST'])
@require_ecommerce_permission('channels', 'edit')
def channels_edit(channel_id):
    """Edit e-commerce channel."""
    company_id = session.get('company_id', 0)
    user_id = session['user_id']
    
    channel = get_one("""
        SELECT * FROM ecommerce_channels WHERE id = ? AND company_id = ?
    """, (channel_id, company_id))
    
    if not channel:
        flash("Channel not found.", "error")
        return redirect(url_for('ecommerce.channels_list'))
    
    if request.method == 'POST':
        channel_name = request.form.get('channel_name', '').strip()
        channel_type = request.form.get('channel_type', 'website')
        warehouse_id = request.form.get('warehouse_id', 0)
        api_endpoint = request.form.get('api_endpoint', '').strip()
        api_key = request.form.get('api_key', '').strip()
        api_secret = request.form.get('api_secret', '').strip()
        webhook_url = request.form.get('webhook_url', '').strip()
        sync_direction = request.form.get('sync_direction', 'bidirectional')
        is_active = 1 if request.form.get('is_active') else 0
        notes = request.form.get('notes', '').strip()
        
        if not channel_name:
            flash("Channel name is required.", "error")
            return render_template('ecommerce/channels/edit.html', channel=channel)
        
        before_state = json.dumps({
            'channel_name': channel['channel_name'],
            'channel_type': channel['channel_type'],
            'is_active': channel['is_active']
        })
        
        with get_db_context() as db:
            db.execute("""
                UPDATE ecommerce_channels SET
                    channel_name = ?, channel_type = ?, warehouse_id = ?,
                    api_endpoint = ?, api_key = ?, api_secret = ?,
                    webhook_url = ?, sync_direction = ?, is_active = ?,
                    notes = ?, updated_at = datetime('now'), updated_by = ?
                WHERE id = ?
            """, (channel_name, channel_type, warehouse_id, api_endpoint,
                  api_key, api_secret, webhook_url, sync_direction,
                  is_active, notes, user_id, channel_id))
            db.commit()
        
        log_ecommerce_audit('updated', 'channel', channel_id, channel['channel_code'],
                           before_state=before_state,
                           after_state=json.dumps({
                               'channel_name': channel_name,
                               'channel_type': channel_type,
                               'is_active': is_active
                           }),
                           channel_id=channel_id, channel_name=channel_name,
                           company_id=company_id)
        
        flash("Channel updated successfully.", "success")
        return redirect(url_for('ecommerce.channels_list'))
    
    warehouses = get_all("""
        SELECT w.id, w.warehouse_name, w.warehouse_code
        FROM warehouses w
        WHERE w.company_id = ? OR w.company_id = 0
        ORDER BY w.warehouse_name
    """, (company_id,))
    
    return render_template('ecommerce/channels/edit.html', channel=channel, warehouses=warehouses)


@ecommerce_bp.route('/channels/<int:channel_id>/view')
@require_ecommerce_permission('channels', 'view')
def channels_view(channel_id):
    """View channel details."""
    company_id = session.get('company_id', 0)
    
    channel = get_one("""
        SELECT * FROM ecommerce_channels WHERE id = ? AND company_id = ?
    """, (channel_id, company_id))
    
    if not channel:
        flash("Channel not found.", "error")
        return redirect(url_for('ecommerce.channels_list'))
    
    # Get channel profile
    profile = get_one("""
        SELECT * FROM ecommerce_channel_profiles WHERE channel_id = ?
    """, (channel_id,))
    
    # Get recent orders for this channel
    recent_orders = get_all("""
        SELECT * FROM ecommerce_order_imports
        WHERE channel_id = ?
        ORDER BY imported_at DESC
        LIMIT 20
    """, (channel_id,))
    
    # Get sync statistics
    sync_stats = get_one("""
        SELECT 
            COUNT(*) as total_orders,
            SUM(CASE WHEN sync_status = 'synced' THEN 1 ELSE 0 END) as synced,
            SUM(CASE WHEN sync_status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN sync_status = 'failed' THEN 1 ELSE 0 END) as failed,
            SUM(total_amount) as total_revenue
        FROM ecommerce_order_imports
        WHERE channel_id = ?
    """, (channel_id,))
    
    # Get product mappings count
    mapping_count = get_one("""
        SELECT COUNT(*) as cnt FROM ecommerce_product_mappings
        WHERE channel_id = ?
    """, (channel_id,))
    
    return render_template('ecommerce/channels/view.html',
                         channel=channel,
                         profile=profile,
                         recent_orders=recent_orders,
                         sync_stats=sync_stats,
                         mapping_count=mapping_count)


@ecommerce_bp.route('/channels/<int:channel_id>/delete', methods=['POST'])
def channels_delete(channel_id):
    """Delete channel."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    company_id = session.get('company_id', 0)
    
    channel = get_one("""
        SELECT * FROM ecommerce_channels WHERE id = ? AND company_id = ?
    """, (channel_id, company_id))
    
    if not channel:
        flash("Channel not found.", "error")
        return redirect(url_for('ecommerce.channels_list'))
    
    # Check for related records
    orders_count = get_one("""
        SELECT COUNT(*) as cnt FROM ecommerce_order_imports WHERE channel_id = ?
    """, (channel_id,))
    
    if orders_count and orders_count['cnt'] > 0:
        flash(f"Cannot delete channel with {orders_count['cnt']} associated orders. Archive it instead.", "error")
        return redirect(url_for('ecommerce.channels_edit', channel_id=channel_id))
    
    with get_db_context() as db:
        # Delete related records
        db.execute("DELETE FROM ecommerce_channel_profiles WHERE channel_id = ?", (channel_id,))
        db.execute("DELETE FROM ecommerce_product_mappings WHERE channel_id = ?", (channel_id,))
        db.execute("DELETE FROM ecommerce_category_mappings WHERE channel_id = ?", (channel_id,))
        db.execute("DELETE FROM ecommerce_warehouse_mappings WHERE channel_id = ?", (channel_id,))
        db.execute("DELETE FROM ecommerce_status_mappings WHERE channel_id = ?", (channel_id,))
        db.execute("DELETE FROM ecommerce_channels WHERE id = ?", (channel_id,))
        db.commit()
    
    log_ecommerce_audit('deleted', 'channel', channel_id, channel['channel_code'],
                        channel_id=channel_id, channel_name=channel['channel_name'],
                        company_id=company_id,
                        before_state=json.dumps({'channel_name': channel['channel_name']}))
    
    flash("Channel deleted successfully.", "success")
    return redirect(url_for('ecommerce.channels_list'))


@ecommerce_bp.route('/channels/<int:channel_id>/profile', methods=['GET', 'POST'])
def channel_profile(channel_id):
    """Manage channel profile/settings."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    company_id = session.get('company_id', 0)
    user_id = session['user_id']
    
    channel = get_one("""
        SELECT * FROM ecommerce_channels WHERE id = ? AND company_id = ?
    """, (channel_id, company_id))
    
    if not channel:
        flash("Channel not found.", "error")
        return redirect(url_for('ecommerce.channels_list'))
    
    profile = get_one("""
        SELECT * FROM ecommerce_channel_profiles WHERE channel_id = ?
    """, (channel_id,))
    
    if not profile:
        with get_db_context() as db:
            cursor = db.execute("""
                INSERT INTO ecommerce_channel_profiles (channel_id, profile_name, created_at)
                VALUES (?, ?, datetime('now'))
            """, (channel_id, f"{channel['channel_name']} Profile"))
            profile_id = cursor.lastrowid
            db.commit()
        profile = get_one("SELECT * FROM ecommerce_channel_profiles WHERE id = ?", (profile_id,))
    
    if request.method == 'POST':
        profile_name = request.form.get('profile_name', '').strip()
        
        # Product sync
        product_sync = 1 if request.form.get('product_sync_enabled') else 0
        auto_publish = 1 if request.form.get('auto_publish_products') else 0
        category_mapping = 1 if request.form.get('category_mapping_required') else 0
        
        # Inventory sync
        inventory_sync = 1 if request.form.get('inventory_sync_enabled') else 0
        inventory_interval = int(request.form.get('inventory_sync_interval', 15))
        inventory_source = request.form.get('inventory_source_type', 'available')
        exclude_reserved = 1 if request.form.get('exclude_reserved_stock') else 0
        safety_buffer = int(request.form.get('safety_stock_buffer', 0))
        
        # Order sync
        order_sync = 1 if request.form.get('order_sync_enabled') else 0
        order_auto_import = 1 if request.form.get('order_auto_import') else 0
        duplicate_detection = 1 if request.form.get('duplicate_detection_enabled') else 0
        order_prefix = request.form.get('order_prefix', '')
        
        # Customer sync
        customer_sync = 1 if request.form.get('customer_sync_enabled') else 0
        customer_auto_create = 1 if request.form.get('customer_auto_create') else 0
        customer_matching = request.form.get('customer_matching_rule', 'email')
        guest_prefix = request.form.get('guest_customer_prefix', 'GUEST')
        
        # Retry settings
        max_retries = int(request.form.get('max_retry_attempts', 3))
        retry_interval = int(request.form.get('retry_interval_minutes', 5))
        
        with get_db_context() as db:
            db.execute("""
                UPDATE ecommerce_channel_profiles SET
                    profile_name = ?,
                    product_sync_enabled = ?,
                    auto_publish_products = ?,
                    category_mapping_required = ?,
                    inventory_sync_enabled = ?,
                    inventory_sync_interval = ?,
                    inventory_source_type = ?,
                    exclude_reserved_stock = ?,
                    safety_stock_buffer = ?,
                    order_sync_enabled = ?,
                    order_auto_import = ?,
                    duplicate_detection_enabled = ?,
                    order_prefix = ?,
                    customer_sync_enabled = ?,
                    customer_auto_create = ?,
                    customer_matching_rule = ?,
                    guest_customer_prefix = ?,
                    max_retry_attempts = ?,
                    retry_interval_minutes = ?,
                    updated_at = datetime('now')
                WHERE channel_id = ?
            """, (profile_name, product_sync, auto_publish, category_mapping,
                  inventory_sync, inventory_interval, inventory_source,
                  exclude_reserved, safety_buffer, order_sync, order_auto_import,
                  duplicate_detection, order_prefix, customer_sync, customer_auto_create,
                  customer_matching, guest_prefix, max_retries, retry_interval,
                  channel_id))
            db.commit()
        
        flash("Channel profile updated.", "success")
        return redirect(url_for('ecommerce.channel_profile', channel_id=channel_id))
    
    return render_template('ecommerce/channels/profile.html', channel=channel, profile=profile)


@ecommerce_bp.route('/channels/<int:channel_id>/test-connection', methods=['POST'])
def channel_test_connection(channel_id):
    """Test channel API connection."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    company_id = session.get('company_id', 0)
    
    channel = get_one("""
        SELECT * FROM ecommerce_channels WHERE id = ? AND company_id = ?
    """, (channel_id, company_id))
    
    if not channel:
        return jsonify({'success': False, 'message': 'Channel not found'})
    
    # Simulate connection test
    # In production, this would make an actual API call
    api_endpoint = channel['api_endpoint']
    api_key = channel['api_key']
    
    result = {
        'success': True,
        'message': 'Connection test simulated. Configure API credentials for real test.',
        'endpoint': api_endpoint,
        'has_credentials': bool(api_key)
    }
    
    # Log the test
    with get_db_context() as db:
        db.execute("""
            UPDATE ecommerce_channels SET
                is_connected = ?,
                last_sync_at = datetime('now'),
                last_sync_status = ?,
                updated_at = datetime('now')
            WHERE id = ?
        """, (1 if result['success'] else 0, 'success' if result['success'] else 'failed', channel_id))
        db.commit()
    
    log_ecommerce_audit('test_connection', 'channel', channel_id, channel['channel_code'],
                        channel_id=channel_id, channel_name=channel['channel_name'],
                        company_id=company_id,
                        after_state=json.dumps({'result': result['message']}))
    
    return jsonify(result)


# =============================================================================
# ROUTE: ORDER SYNC
# =============================================================================

@ecommerce_bp.route('/orders')
@require_ecommerce_permission('orders', 'view')
def orders_list():
    """List e-commerce orders."""
    company_id = session.get('company_id', 0)
    
    # Get filter parameters
    status_filter = request.args.get('status', '')
    channel_filter = request.args.get('channel', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    search = request.args.get('search', '')
    
    # Build query
    query = """
        SELECT o.*, c.channel_name
        FROM ecommerce_order_imports o
        LEFT JOIN ecommerce_channels c ON o.channel_id = c.id
        WHERE o.company_id = ?
    """
    params = [company_id]
    
    if status_filter:
        query += " AND o.sync_status = ?"
        params.append(status_filter)
    
    if channel_filter:
        query += " AND o.channel_id = ?"
        params.append(channel_filter)
    
    if date_from:
        query += " AND DATE(o.order_date) >= ?"
        params.append(date_from)
    
    if date_to:
        query += " AND DATE(o.order_date) <= ?"
        params.append(date_to)
    
    if search:
        query += " AND (o.external_order_number LIKE ? OR o.customer_email LIKE ? OR o.customer_name LIKE ?)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])
    
    query += " ORDER BY o.imported_at DESC"
    
    orders = get_all(query, params)
    
    # Get channels for filter
    channels = get_all("""
        SELECT id, channel_name FROM ecommerce_channels
        WHERE company_id = ? AND is_active = 1
        ORDER BY channel_name
    """, (company_id,))
    
    # Get status counts
    status_counts = {}
    with get_db_context() as db:
        counts = db.execute("""
            SELECT sync_status, COUNT(*) as cnt
            FROM ecommerce_order_imports
            WHERE company_id = ?
            GROUP BY sync_status
        """, (company_id,)).fetchall()
        for row in counts:
            status_counts[row['sync_status']] = row['cnt']
    
    return render_template('ecommerce/orders/list.html',
                         orders=orders,
                         channels=channels,
                         status_counts=status_counts,
                         filters={
                             'status': status_filter,
                             'channel': channel_filter,
                             'date_from': date_from,
                             'date_to': date_to,
                             'search': search
                         })


@ecommerce_bp.route('/orders/pending')
def orders_pending():
    """List pending orders for import."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    company_id = session.get('company_id', 0)
    
    orders = get_all("""
        SELECT o.*, c.channel_name
        FROM ecommerce_order_imports o
        LEFT JOIN ecommerce_channels c ON o.channel_id = c.id
        WHERE o.company_id = ? AND o.sync_status = 'pending'
        ORDER BY o.imported_at ASC
    """, (company_id,))
    
    return render_template('ecommerce/orders/pending.html', orders=orders)


@ecommerce_bp.route('/orders/failed')
def orders_failed():
    """List failed orders."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    company_id = session.get('company_id', 0)
    
    orders = get_all("""
        SELECT o.*, c.channel_name
        FROM ecommerce_order_imports o
        LEFT JOIN ecommerce_channels c ON o.channel_id = c.id
        WHERE o.company_id = ? AND o.sync_status = 'failed'
        ORDER BY o.imported_at DESC
    """, (company_id,))
    
    return render_template('ecommerce/orders/failed.html', orders=orders)


@ecommerce_bp.route('/orders/synced')
def orders_synced():
    """List successfully synced orders."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    company_id = session.get('company_id', 0)
    
    orders = get_all("""
        SELECT o.*, c.channel_name
        FROM ecommerce_order_imports o
        LEFT JOIN ecommerce_channels c ON o.channel_id = c.id
        WHERE o.company_id = ? AND o.sync_status = 'synced'
        ORDER BY o.imported_at DESC
        LIMIT 100
    """, (company_id,))
    
    return render_template('ecommerce/orders/synced.html', orders=orders)


@ecommerce_bp.route('/orders/<int:order_id>/view')
@require_ecommerce_permission('orders', 'view')
def orders_view(order_id):
    """View order details."""
    company_id = session.get('company_id', 0)
    
    order = get_one("""
        SELECT o.*, c.channel_name
        FROM ecommerce_order_imports o
        LEFT JOIN ecommerce_channels c ON o.channel_id = c.id
        WHERE o.id = ? AND o.company_id = ?
    """, (order_id, company_id))
    
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for('ecommerce.orders_list'))
    
    # Get order lines
    lines = get_all("""
        SELECT * FROM ecommerce_order_lines
        WHERE order_import_id = ?
        ORDER BY line_number
    """, (order_id,))
    
    # Get status sync history
    status_history = get_all("""
        SELECT * FROM ecommerce_order_status_sync
        WHERE order_import_id = ?
        ORDER BY synced_at DESC
    """, (order_id,))
    
    return render_template('ecommerce/orders/view.html',
                         order=order,
                         lines=lines,
                         status_history=status_history)


@ecommerce_bp.route('/orders/<int:order_id>/retry', methods=['POST'])
def orders_retry(order_id):
    """Retry failed order sync."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    company_id = session.get('company_id', 0)
    user_id = session['user_id']
    
    order = get_one("""
        SELECT * FROM ecommerce_order_imports WHERE id = ? AND company_id = ?
    """, (order_id, company_id))
    
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for('ecommerce.orders_list'))
    
    if order['sync_status'] != 'failed':
        flash("Only failed orders can be retried.", "error")
        return redirect(url_for('ecommerce.orders_view', order_id=order_id))
    
    with get_db_context() as db:
        db.execute("""
            UPDATE ecommerce_order_imports SET
                sync_status = 'pending',
                sync_error = '',
                retry_count = retry_count + 1,
                last_retry_at = datetime('now'),
                updated_at = datetime('now')
            WHERE id = ?
        """, (order_id,))
        db.commit()
    
    log_ecommerce_audit('retry', 'order', order_id, order['external_order_number'],
                        channel_id=order['channel_id'],
                        company_id=company_id,
                        after_state=json.dumps({
                            'retry_count': order['retry_count'] + 1
                        }))
    
    flash("Order queued for retry.", "success")
    return redirect(url_for('ecommerce.orders_view', order_id=order_id))


@ecommerce_bp.route('/orders/import', methods=['POST'])
def orders_import():
    """Import new orders from channels (webhook/manual trigger)."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    company_id = session.get('company_id', 0)
    user_id = session['user_id']
    
    data = request.get_json() or {}
    
    channel_id = data.get('channel_id')
    orders_data = data.get('orders', [])
    
    if not channel_id:
        return jsonify({'success': False, 'message': 'Channel ID required'})
    
    channel = get_one("""
        SELECT * FROM ecommerce_channels WHERE id = ? AND company_id = ?
    """, (channel_id, company_id))
    
    if not channel:
        return jsonify({'success': False, 'message': 'Channel not found'})
    
    imported_count = 0
    failed_count = 0
    errors = []
    
    with get_db_context() as db:
        for order_data in orders_data:
            try:
                external_order_id = order_data.get('id') or order_data.get('order_id', '')
                external_order_number = order_data.get('order_number', external_order_id)
                
                # Check for duplicate
                existing = db.execute("""
                    SELECT id FROM ecommerce_order_imports
                    WHERE channel_id = ? AND external_order_id = ?
                """, (channel_id, external_order_id)).fetchone()
                
                if existing:
                    continue  # Skip duplicates
                
                # Parse customer info
                customer = order_data.get('customer', {})
                
                # Parse shipping info
                shipping = order_data.get('shipping', {})
                
                # Parse billing
                billing = order_data.get('billing', {})
                
                # Parse items
                items = order_data.get('items', [])
                
                # Calculate totals
                subtotal = sum(float(item.get('price', 0)) * int(item.get('quantity', 1)) for item in items)
                discount = float(order_data.get('discount_amount', 0))
                tax = float(order_data.get('tax_amount', 0))
                shipping_cost = float(order_data.get('shipping_cost', 0))
                total = subtotal - discount + tax + shipping_cost
                
                # Insert order
                cursor = db.execute("""
                    INSERT INTO ecommerce_order_imports
                    (external_order_id, external_order_number, channel_id, channel_name,
                     company_id, warehouse_id, customer_email, customer_phone, customer_name,
                     is_guest, billing_name, billing_company, billing_address, billing_city,
                     billing_state, billing_country, billing_postal_code, billing_phone,
                     shipping_name, shipping_company, shipping_address, shipping_city,
                     shipping_state, shipping_country, shipping_postal_code, shipping_phone,
                     shipping_method, shipping_cost, order_date, order_datetime, currency,
                     subtotal, discount_amount, tax_amount, total_amount,
                     payment_method, payment_method_display, payment_status,
                     fulfillment_status, order_status, sync_status, external_data,
                     imported_at, imported_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                            ?, datetime('now'), ?)
                """, (
                    external_order_id, external_order_number, channel_id, channel['channel_name'],
                    company_id, channel['warehouse_id'],
                    customer.get('email', ''), customer.get('phone', ''),
                    f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
                    1 if customer.get('is_guest') else 0,
                    billing.get('name', ''), billing.get('company', ''),
                    billing.get('address', ''), billing.get('city', ''),
                    billing.get('state', ''), billing.get('country', ''),
                    billing.get('postal_code', ''), billing.get('phone', ''),
                    shipping.get('name', ''), shipping.get('company', ''),
                    shipping.get('address', ''), shipping.get('city', ''),
                    shipping.get('state', ''), shipping.get('country', ''),
                    shipping.get('postal_code', ''), shipping.get('phone', ''),
                    shipping.get('method', ''), shipping_cost,
                    order_data.get('order_date', ''), order_data.get('order_datetime', ''),
                    order_data.get('currency', 'USD'),
                    subtotal, discount, tax, total,
                    order_data.get('payment_method', ''),
                    order_data.get('payment_method_display', ''),
                    order_data.get('payment_status', 'pending'),
                    order_data.get('fulfillment_status', 'unfulfilled'),
                    order_data.get('order_status', 'pending'),
                    'pending',
                    json.dumps(order_data),
                    user_id
                ))
                
                order_import_id = cursor.lastrowid
                
                # Insert order lines
                for idx, item in enumerate(items):
                    db.execute("""
                        INSERT INTO ecommerce_order_lines
                        (order_import_id, line_number, external_product_id,
                         external_product_name, external_sku, external_barcode,
                         quantity, unit_price, discount_amount, tax_amount,
                         total_amount, tax_rate)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        order_import_id, idx + 1,
                        item.get('product_id', ''), item.get('name', ''),
                        item.get('sku', ''), item.get('barcode', ''),
                        int(item.get('quantity', 1)),
                        float(item.get('price', 0)),
                        float(item.get('discount', 0)),
                        float(item.get('tax', 0)),
                        float(item.get('total', 0)),
                        float(item.get('tax_rate', 0))
                    ))
                
                imported_count += 1
                
            except Exception as e:
                failed_count += 1
                errors.append(str(e))
    
    log_ecommerce_audit('import', 'order', 0, f"{imported_count} orders",
                        channel_id=channel_id, channel_name=channel['channel_name'],
                        company_id=company_id,
                        after_state=json.dumps({
                            'imported': imported_count,
                            'failed': failed_count
                        }))
    
    return jsonify({
        'success': True,
        'imported': imported_count,
        'failed': failed_count,
        'errors': errors
    })


# =============================================================================
# ROUTE: INVENTORY SYNC
# =============================================================================

@ecommerce_bp.route('/inventory')
@require_ecommerce_permission('inventory', 'view')
def inventory_list():
    """List inventory sync records."""
    company_id = session.get('company_id', 0)
    
    # Get filter parameters
    channel_filter = request.args.get('channel', '')
    status_filter = request.args.get('status', '')
    
    query = """
        SELECT i.*, c.channel_name
        FROM ecommerce_inventory_syncs i
        LEFT JOIN ecommerce_channels c ON i.channel_id = c.id
        WHERE i.company_id = ?
    """
    params = [company_id]
    
    if channel_filter:
        query += " AND i.channel_id = ?"
        params.append(channel_filter)
    
    if status_filter:
        query += " AND i.sync_status = ?"
        params.append(status_filter)
    
    query += " ORDER BY i.last_synced_at DESC"
    
    records = get_all(query, params)
    
    channels = get_all("""
        SELECT id, channel_name FROM ecommerce_channels
        WHERE company_id = ? AND is_active = 1
        ORDER BY channel_name
    """, (company_id,))
    
    return render_template('ecommerce/inventory/list.html',
                         records=records,
                         channels=channels,
                         status_filter=status_filter,
                         channel_filter=channel_filter)


@ecommerce_bp.route('/inventory/sync', methods=['POST'])
def inventory_sync():
    """Trigger inventory sync to channel."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    company_id = session.get('company_id', 0)
    user_id = session['user_id']
    
    data = request.get_json() or {}
    channel_id = data.get('channel_id')
    warehouse_id = data.get('warehouse_id')
    
    if not channel_id:
        return jsonify({'success': False, 'message': 'Channel ID required'})
    
    channel = get_one("""
        SELECT * FROM ecommerce_channels WHERE id = ? AND company_id = ?
    """, (channel_id, company_id))
    
    if not channel:
        return jsonify({'success': False, 'message': 'Channel not found'})
    
    # Get channel profile
    profile = get_one("""
        SELECT * FROM ecommerce_channel_profiles WHERE channel_id = ?
    """, (channel_id,))
    
    if not profile or not profile['inventory_sync_enabled']:
        return jsonify({'success': False, 'message': 'Inventory sync not enabled for this channel'})
    
    # Create sync job
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO ecommerce_sync_jobs
            (job_type, channel_id, channel_name, company_id, warehouse_id,
             status, sync_mode, started_at, created_by)
            VALUES (?, ?, ?, ?, ?, 'running', 'manual', datetime('now'), ?)
        """, ('inventory_sync', channel_id, channel['channel_name'],
              company_id, warehouse_id or channel['warehouse_id'], user_id))
        job_id = cursor.lastrowid
        db.commit()
    
    # In production, this would trigger actual inventory sync
    # For now, simulate sync
    
    with get_db_context() as db:
        db.execute("""
            UPDATE ecommerce_sync_jobs SET
                status = 'completed',
                completed_at = datetime('now'),
                items_processed = 0,
                items_successful = 0,
                items_failed = 0
            WHERE id = ?
        """, (job_id,))
        db.commit()
    
    log_ecommerce_audit('sync', 'inventory', 0, f"Inventory sync job {job_id}",
                        channel_id=channel_id, channel_name=channel['channel_name'],
                        company_id=company_id)
    
    return jsonify({
        'success': True,
        'message': 'Inventory sync initiated',
        'job_id': job_id
    })


# =============================================================================
# ROUTE: CUSTOMER SYNC
# =============================================================================

@ecommerce_bp.route('/customers')
@require_ecommerce_permission('customers', 'view')
def customers_list():
    """List imported customers."""
    company_id = session.get('company_id', 0)
    
    # Filters
    status_filter = request.args.get('status', '')
    channel_filter = request.args.get('channel', '')
    duplicate_filter = request.args.get('duplicate', '')
    search = request.args.get('search', '')
    
    query = """
        SELECT c.*, ch.channel_name
        FROM ecommerce_customer_imports c
        LEFT JOIN ecommerce_channels ch ON c.channel_id = ch.id
        WHERE c.company_id = ?
    """
    params = [company_id]
    
    if status_filter:
        query += " AND c.sync_status = ?"
        params.append(status_filter)
    
    if channel_filter:
        query += " AND c.channel_id = ?"
        params.append(channel_filter)
    
    if duplicate_filter == 'yes':
        query += " AND c.duplicate_review_status = 'pending'"
    
    if search:
        query += " AND (c.email LIKE ? OR c.full_name LIKE ? OR c.phone LIKE ?)"
        search_param = f"%{search}%"
        params.extend([search_param, search_param, search_param])
    
    query += " ORDER BY c.imported_at DESC"
    
    customers = get_all(query, params)
    
    channels = get_all("""
        SELECT id, channel_name FROM ecommerce_channels
        WHERE company_id = ? AND is_active = 1
        ORDER BY channel_name
    """, (company_id,))
    
    return render_template('ecommerce/customers/list.html',
                         customers=customers,
                         channels=channels,
                         filters={
                             'status': status_filter,
                             'channel': channel_filter,
                             'duplicate': duplicate_filter,
                             'search': search
                         })


@ecommerce_bp.route('/customers/duplicates')
def customers_duplicates():
    """List customers pending duplicate review."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    company_id = session.get('company_id', 0)
    
    customers = get_all("""
        SELECT c.*, ch.channel_name
        FROM ecommerce_customer_imports c
        LEFT JOIN ecommerce_channels ch ON c.channel_id = ch.id
        WHERE c.company_id = ? AND c.duplicate_review_status = 'pending'
        ORDER BY c.imported_at DESC
    """, (company_id,))
    
    return render_template('ecommerce/customers/duplicates.html', customers=customers)


@ecommerce_bp.route('/customers/<int:customer_id>/view')
@require_ecommerce_permission('customers', 'view')
def customers_view(customer_id):
    """View customer import details."""
    company_id = session.get('company_id', 0)
    
    customer = get_one("""
        SELECT c.*, ch.channel_name
        FROM ecommerce_customer_imports c
        LEFT JOIN ecommerce_channels ch ON c.channel_id = ch.id
        WHERE c.id = ? AND c.company_id = ?
    """, (customer_id, company_id))
    
    if not customer:
        flash("Customer not found.", "error")
        return redirect(url_for('ecommerce.customers_list'))
    
    # Get match history
    matches = get_all("""
        SELECT m.*, cu.username as customer_name
        FROM ecommerce_customer_matches m
        LEFT JOIN users cu ON m.internal_customer_id = cu.id
        WHERE m.customer_import_id = ?
        ORDER BY m.match_confidence DESC
    """, (customer_id,))
    
    return render_template('ecommerce/customers/view.html',
                         customer=customer,
                         matches=matches)


@ecommerce_bp.route('/customers/<int:customer_id>/resolve-duplicate', methods=['POST'])
def customers_resolve_duplicate(customer_id):
    """Resolve duplicate customer (approve match or create new)."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    company_id = session.get('company_id', 0)
    user_id = session['user_id']
    
    customer = get_one("""
        SELECT * FROM ecommerce_customer_imports WHERE id = ? AND company_id = ?
    """, (customer_id, company_id))
    
    if not customer:
        flash("Customer not found.", "error")
        return redirect(url_for('ecommerce.customers_list'))
    
    action = request.form.get('action')  # 'approve' or 'create_new'
    internal_customer_id = request.form.get('internal_customer_id')
    notes = request.form.get('notes', '')
    
    if action == 'approve' and internal_customer_id:
        # Link to existing customer
        with get_db_context() as db:
            db.execute("""
                UPDATE ecommerce_customer_imports SET
                    internal_customer_id = ?,
                    duplicate_review_status = 'approved',
                    duplicate_reviewed_by = ?,
                    duplicate_reviewed_at = datetime('now'),
                    sync_status = 'synced',
                    notes = ?
                WHERE id = ?
            """, (internal_customer_id, user_id, notes, customer_id))
            db.commit()
        
        flash("Customer linked to existing record.", "success")
    
    elif action == 'create_new':
        # Create new customer
        with get_db_context() as db:
            # Create customer in main customers table
            cursor = db.execute("""
                INSERT INTO customers
                (company_name, email, phone, mobile, address, city, state, country,
                 postal_code, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                customer['company_name'], customer['email'], customer['phone'],
                customer['mobile'],
                customer['shipping_address'] or customer['billing_address'],
                customer['shipping_city'] or customer['billing_city'],
                customer['shipping_state'] or customer['billing_state'],
                customer['shipping_country'] or customer['billing_country'],
                customer['shipping_postal_code'] or customer['billing_postal_code']
            ))
            new_customer_id = cursor.lastrowid
            
            db.execute("""
                UPDATE ecommerce_customer_imports SET
                    internal_customer_id = ?,
                    duplicate_review_status = 'approved',
                    duplicate_reviewed_by = ?,
                    duplicate_reviewed_at = datetime('now'),
                    sync_status = 'synced',
                    notes = ?
                WHERE id = ?
            """, (new_customer_id, user_id, notes, customer_id))
            db.commit()
        
        flash("New customer created and linked.", "success")
    
    else:
        # Reject
        with get_db_context() as db:
            db.execute("""
                UPDATE ecommerce_customer_imports SET
                    duplicate_review_status = 'rejected',
                    duplicate_reviewed_by = ?,
                    duplicate_reviewed_at = datetime('now'),
                    sync_status = 'skipped',
                    notes = ?
                WHERE id = ?
            """, (user_id, notes, customer_id))
            db.commit()
        
        flash("Customer import rejected.", "info")
    
    return redirect(url_for('ecommerce.customers_duplicates'))


# =============================================================================
# ROUTE: EXCEPTIONS
# =============================================================================

@ecommerce_bp.route('/exceptions')
@require_ecommerce_permission('exceptions', 'view')
def exceptions_list():
    """List e-commerce exceptions."""
    company_id = session.get('company_id', 0)
    
    status_filter = request.args.get('status', 'open')
    severity_filter = request.args.get('severity', '')
    type_filter = request.args.get('type', '')
    channel_filter = request.args.get('channel', '')
    
    query = """
        SELECT e.*, c.channel_name
        FROM ecommerce_exceptions e
        LEFT JOIN ecommerce_channels c ON e.channel_id = c.id
        WHERE e.company_id = ?
    """
    params = [company_id]
    
    if status_filter:
        query += " AND e.status = ?"
        params.append(status_filter)
    
    if severity_filter:
        query += " AND e.severity = ?"
        params.append(severity_filter)
    
    if type_filter:
        query += " AND e.exception_type = ?"
        params.append(type_filter)
    
    if channel_filter:
        query += " AND e.channel_id = ?"
        params.append(channel_filter)
    
    query += " ORDER BY e.created_at DESC"
    
    exceptions = get_all(query, params)
    
    channels = get_all("""
        SELECT id, channel_name FROM ecommerce_channels
        WHERE company_id = ? AND is_active = 1
        ORDER BY channel_name
    """, (company_id,))
    
    # Get counts
    with get_db_context() as db:
        open_count = db.execute("""
            SELECT COUNT(*) as cnt FROM ecommerce_exceptions
            WHERE company_id = ? AND status = 'open'
        """, (company_id,)).fetchone()['cnt']
        
        critical_count = db.execute("""
            SELECT COUNT(*) as cnt FROM ecommerce_exceptions
            WHERE company_id = ? AND status = 'open' AND severity = 'critical'
        """, (company_id,)).fetchone()['cnt']
    
    return render_template('ecommerce/exceptions/list.html',
                         exceptions=exceptions,
                         channels=channels,
                         open_count=open_count,
                         critical_count=critical_count,
                         filters={
                             'status': status_filter,
                             'severity': severity_filter,
                             'type': type_filter,
                             'channel': channel_filter
                         })


@ecommerce_bp.route('/exceptions/<exception_number>/view')
def exceptions_view(exception_number):
    """View exception details."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    company_id = session.get('company_id', 0)
    
    exception = get_one("""
        SELECT e.*, c.channel_name
        FROM ecommerce_exceptions e
        LEFT JOIN ecommerce_channels c ON e.channel_id = c.id
        WHERE e.exception_number = ? AND e.company_id = ?
    """, (exception_number, company_id))
    
    if not exception:
        flash("Exception not found.", "error")
        return redirect(url_for('ecommerce.exceptions_list'))
    
    # Parse JSON data if present
    source_data = {}
    internal_state = {}
    
    if exception['source_data']:
        try:
            source_data = json.loads(exception['source_data'])
        except:
            pass
    
    if exception['internal_state']:
        try:
            internal_state = json.loads(exception['internal_state'])
        except:
            pass
    
    return render_template('ecommerce/exceptions/view.html',
                         exception=exception,
                         source_data=source_data,
                         internal_state=internal_state)


@ecommerce_bp.route('/exceptions/<exception_number>/resolve', methods=['POST'])
def exceptions_resolve(exception_number):
    """Resolve an exception."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    company_id = session.get('company_id', 0)
    user_id = session['user_id']
    
    exception = get_one("""
        SELECT * FROM ecommerce_exceptions
        WHERE exception_number = ? AND company_id = ?
    """, (exception_number, company_id))
    
    if not exception:
        flash("Exception not found.", "error")
        return redirect(url_for('ecommerce.exceptions_list'))
    
    resolution_action = request.form.get('resolution_action', 'resolved')
    resolution_notes = request.form.get('resolution_notes', '')
    
    with get_db_context() as db:
        db.execute("""
            UPDATE ecommerce_exceptions SET
                status = 'resolved',
                resolution_action = ?,
                resolution_notes = ?,
                resolved_by = ?,
                resolved_at = datetime('now'),
                updated_at = datetime('now')
            WHERE exception_number = ?
        """, (resolution_action, resolution_notes, user_id, exception_number))
        db.commit()
    
    log_ecommerce_audit('resolved', 'exception', exception['id'], exception_number,
                        channel_id=exception['channel_id'],
                        company_id=company_id,
                        after_state=json.dumps({
                            'resolution_action': resolution_action,
                            'resolved_by': user_id
                        }))
    
    flash("Exception resolved.", "success")
    return redirect(url_for('ecommerce.exceptions_list'))


# =============================================================================
# ROUTE: REPORTS
# =============================================================================

@ecommerce_bp.route('/reports')
@require_ecommerce_permission('reports', 'view')
def reports():
    """E-commerce Reports."""
    company_id = session.get('company_id', 0)
    
    # Get report data
    with get_db_context() as db:
        # Channel sales summary
        channel_sales = db.execute("""
            SELECT 
                c.channel_name,
                COUNT(o.id) as order_count,
                SUM(o.total_amount) as total_sales,
                AVG(o.total_amount) as avg_order_value,
                SUM(CASE WHEN o.payment_status = 'paid' THEN o.total_amount ELSE 0 END) as paid_amount
            FROM ecommerce_channels c
            LEFT JOIN ecommerce_order_imports o ON c.id = o.channel_id
            WHERE c.company_id = ?
            GROUP BY c.id
        """, (company_id,)).fetchall()
        
        # Order status summary
        order_status = db.execute("""
            SELECT order_status, COUNT(*) as cnt, SUM(total_amount) as amount
            FROM ecommerce_order_imports
            WHERE company_id = ?
            GROUP BY order_status
        """, (company_id,)).fetchall()
        
        # Sync status summary
        sync_status = db.execute("""
            SELECT sync_status, COUNT(*) as cnt
            FROM ecommerce_order_imports
            WHERE company_id = ?
            GROUP BY sync_status
        """, (company_id,)).fetchall()
        
        # Daily orders (last 30 days)
        daily_orders = db.execute("""
            SELECT 
                DATE(imported_at) as date,
                COUNT(*) as order_count,
                SUM(total_amount) as daily_sales
            FROM ecommerce_order_imports
            WHERE company_id = ?
                AND imported_at >= DATE('now', '-30 days')
            GROUP BY DATE(imported_at)
            ORDER BY date
        """, (company_id,)).fetchall()
        
        # Top selling products
        top_products = db.execute("""
            SELECT 
                l.external_product_name,
                l.external_sku,
                SUM(l.quantity) as total_qty,
                SUM(l.total_amount) as total_revenue
            FROM ecommerce_order_lines l
            JOIN ecommerce_order_imports o ON l.order_import_id = o.id
            WHERE o.company_id = ?
            GROUP BY l.external_product_id
            ORDER BY total_qty DESC
            LIMIT 10
        """, (company_id,)).fetchall()
        
        # Exception summary
        exception_summary = db.execute("""
            SELECT exception_type, severity, COUNT(*) as cnt
            FROM ecommerce_exceptions
            WHERE company_id = ?
            GROUP BY exception_type, severity
        """, (company_id,)).fetchall()
    
    return render_template('ecommerce/reports/index.html',
                         channel_sales=channel_sales,
                         order_status=order_status,
                         sync_status=sync_status,
                         daily_orders=daily_orders,
                         top_products=top_products,
                         exception_summary=exception_summary)


@ecommerce_bp.route('/reports/channel-sales')
def reports_channel_sales():
    """Channel sales report."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    company_id = session.get('company_id', 0)
    date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
    
    sales = get_all("""
        SELECT 
            c.id as channel_id,
            c.channel_name,
            c.channel_type,
            COUNT(o.id) as order_count,
            SUM(o.total_amount) as total_sales,
            SUM(o.tax_amount) as total_tax,
            SUM(o.shipping_cost) as total_shipping,
            AVG(o.total_amount) as avg_order_value,
            SUM(CASE WHEN o.payment_status = 'paid' THEN o.total_amount ELSE 0 END) as collected,
            SUM(CASE WHEN o.payment_status = 'pending' THEN o.total_amount ELSE 0 END) as pending_payment
        FROM ecommerce_channels c
        LEFT JOIN ecommerce_order_imports o ON c.id = o.channel_id
            AND DATE(o.order_date) BETWEEN ? AND ?
        WHERE c.company_id = ?
        GROUP BY c.id
        ORDER BY total_sales DESC
    """, (date_from, date_to, company_id))
    
    return render_template('ecommerce/reports/channel_sales.html',
                         sales=sales,
                         date_from=date_from,
                         date_to=date_to)


@ecommerce_bp.route('/reports/sync-status')
def reports_sync_status():
    """Sync status report."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    company_id = session.get('company_id', 0)
    
    # Order sync status by channel
    order_sync = get_all("""
        SELECT 
            c.channel_name,
            SUM(CASE WHEN o.sync_status = 'synced' THEN 1 ELSE 0 END) as synced,
            SUM(CASE WHEN o.sync_status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN o.sync_status = 'failed' THEN 1 ELSE 0 END) as failed,
            SUM(CASE WHEN o.sync_status = 'importing' THEN 1 ELSE 0 END) as importing,
            COUNT(o.id) as total
        FROM ecommerce_channels c
        LEFT JOIN ecommerce_order_imports o ON c.id = o.channel_id
        WHERE c.company_id = ?
        GROUP BY c.id
    """, (company_id,))
    
    # Customer sync status
    customer_sync = get_all("""
        SELECT 
            c.channel_name,
            SUM(CASE WHEN cu.sync_status = 'synced' THEN 1 ELSE 0 END) as synced,
            SUM(CASE WHEN cu.sync_status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN cu.sync_status = 'duplicate' THEN 1 ELSE 0 END) as duplicates,
            SUM(CASE WHEN cu.sync_status = 'failed' THEN 1 ELSE 0 END) as failed,
            COUNT(cu.id) as total
        FROM ecommerce_channels c
        LEFT JOIN ecommerce_customer_imports cu ON c.id = cu.channel_id
        WHERE c.company_id = ?
        GROUP BY c.id
    """, (company_id,))
    
    # Inventory sync status
    inventory_sync = get_all("""
        SELECT 
            c.channel_name,
            SUM(CASE WHEN i.sync_status = 'synced' THEN 1 ELSE 0 END) as synced,
            SUM(CASE WHEN i.sync_status = 'failed' THEN 1 ELSE 0 END) as failed,
            SUM(CASE WHEN i.sync_status = 'pending' THEN 1 ELSE 0 END) as pending,
            COUNT(i.id) as total
        FROM ecommerce_channels c
        LEFT JOIN ecommerce_inventory_syncs i ON c.id = i.channel_id
        WHERE c.company_id = ?
        GROUP BY c.id
    """, (company_id,))
    
    return render_template('ecommerce/reports/sync_status.html',
                         order_sync=order_sync,
                         customer_sync=customer_sync,
                         inventory_sync=inventory_sync)


@ecommerce_bp.route('/reports/exception-report')
def reports_exceptions():
    """Exception report."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    company_id = session.get('company_id', 0)
    date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
    
    exceptions = get_all("""
        SELECT 
            e.*,
            c.channel_name
        FROM ecommerce_exceptions e
        LEFT JOIN ecommerce_channels c ON e.channel_id = c.id
        WHERE e.company_id = ?
            AND DATE(e.created_at) BETWEEN ? AND ?
        ORDER BY e.created_at DESC
    """, (company_id, date_from, date_to))
    
    # Summary by type
    summary = get_all("""
        SELECT 
            exception_type,
            severity,
            COUNT(*) as count
        FROM ecommerce_exceptions
        WHERE company_id = ?
            AND DATE(created_at) BETWEEN ? AND ?
        GROUP BY exception_type, severity
    """, (company_id, date_from, date_to))
    
    return render_template('ecommerce/reports/exceptions.html',
                         exceptions=exceptions,
                         summary=summary,
                         date_from=date_from,
                         date_to=date_to)


# =============================================================================
# ROUTE: SETTINGS
# =============================================================================

@ecommerce_bp.route('/settings')
@require_ecommerce_permission('settings', 'view')
def settings():
    """E-commerce settings."""
    company_id = session.get('company_id', 0)
    
    # Get all settings
    settings_map = {}
    settings_list = get_all("""
        SELECT * FROM ecommerce_settings
        WHERE company_id = ? OR company_id = 0
        ORDER BY setting_key
    """, (company_id,))
    
    for s in settings_list:
        if s['channel_id'] is None:
            settings_map[s['setting_key']] = s['setting_value']
    
    # Get status mappings
    channels = get_all("""
        SELECT id, channel_name FROM ecommerce_channels
        WHERE company_id = ? AND is_active = 1
        ORDER BY channel_name
    """, (company_id,))
    
    return render_template('ecommerce/settings/index.html',
                         settings=settings_map,
                         channels=channels)


@ecommerce_bp.route('/settings/save', methods=['POST'])
def settings_save():
    """Save e-commerce settings."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    company_id = session.get('company_id', 0)
    
    settings_to_save = [
        'ecommerce_default_currency',
        'ecommerce_default_payment_status',
        'ecommerce_default_fulfillment_status',
        'ecommerce_max_retry_attempts',
        'ecommerce_retry_interval_minutes',
        'ecommerce_order_prefix',
        'ecommerce_customer_prefix',
        'ecommerce_enable_audit_log',
        'ecommerce_enable_webhook_log',
        'ecommerce_enable_api_log',
    ]
    
    with get_db_context() as db:
        for key in settings_to_save:
            value = request.form.get(key, '')
            
            # Determine type
            if key == 'ecommerce_max_retry_attempts' or key == 'ecommerce_retry_interval_minutes':
                value = str(int(value)) if value else '0'
            elif key == 'ecommerce_enable_audit_log' or key == 'ecommerce_enable_webhook_log' or key == 'ecommerce_enable_api_log':
                value = '1' if value else '0'
            
            # Check if exists
            existing = db.execute("""
                SELECT id FROM ecommerce_settings WHERE setting_key = ?
            """, (key,)).fetchone()
            
            if existing:
                db.execute("""
                    UPDATE ecommerce_settings SET
                        setting_value = ?,
                        updated_at = datetime('now'),
                        updated_by = ?
                    WHERE setting_key = ?
                """, (value, user_id, key))
            else:
                db.execute("""
                    INSERT INTO ecommerce_settings (setting_key, setting_value, updated_at, updated_by)
                    VALUES (?, ?, datetime('now'), ?)
                """, (key, value, user_id))
        
        db.commit()
    
    flash("Settings saved.", "success")
    return redirect(url_for('ecommerce.settings'))


# =============================================================================
# ROUTE: AUDIT LOGS
# =============================================================================

@ecommerce_bp.route('/audit-logs')
@require_ecommerce_permission('audit_logs', 'view')
def audit_logs():
    """View e-commerce audit logs."""
    company_id = session.get('company_id', 0)
    
    # Filters
    log_type = request.args.get('type', '')
    action = request.args.get('action', '')
    channel_filter = request.args.get('channel', '')
    entity_type = request.args.get('entity', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = """
        SELECT * FROM ecommerce_audit_logs
        WHERE company_id = ?
    """
    params = [company_id]
    
    if log_type:
        query += " AND log_type = ?"
        params.append(log_type)
    
    if action:
        query += " AND action = ?"
        params.append(action)
    
    if channel_filter:
        query += " AND channel_id = ?"
        params.append(channel_filter)
    
    if entity_type:
        query += " AND entity_type = ?"
        params.append(entity_type)
    
    if date_from:
        query += " AND DATE(timestamp) >= ?"
        params.append(date_from)
    
    if date_to:
        query += " AND DATE(timestamp) <= ?"
        params.append(date_to)
    
    query += " ORDER BY timestamp DESC LIMIT 200"
    
    logs = get_all(query, params)
    
    channels = get_all("""
        SELECT id, channel_name FROM ecommerce_channels
        WHERE company_id = ? ORDER BY channel_name
    """, (company_id,))
    
    return render_template('ecommerce/audit_logs.html',
                         logs=logs,
                         channels=channels,
                         filters={
                             'type': log_type,
                             'action': action,
                             'channel': channel_filter,
                             'entity': entity_type,
                             'date_from': date_from,
                             'date_to': date_to
                         })


# =============================================================================
# ROUTE: PRODUCT MAPPINGS
# =============================================================================

@ecommerce_bp.route('/mappings/products')
@require_ecommerce_permission('mappings', 'view')
def mappings_products():
    """List product mappings."""
    company_id = session.get('company_id', 0)
    channel_filter = request.args.get('channel', '')
    
    query = """
        SELECT m.*, c.channel_name, i.item_name, i.item_sku
        FROM ecommerce_product_mappings m
        LEFT JOIN ecommerce_channels c ON m.channel_id = c.id
        LEFT JOIN items i ON m.internal_item_id = i.id
        WHERE 1=1
    """
    params = []
    
    if channel_filter:
        query += " AND m.channel_id = ?"
        params.append(channel_filter)
    
    query += " ORDER BY m.created_at DESC"
    
    mappings = get_all(query, params)
    
    channels = get_all("""
        SELECT id, channel_name FROM ecommerce_channels
        WHERE company_id = ? AND is_active = 1
        ORDER BY channel_name
    """, (company_id,))
    
    return render_template('ecommerce/mappings/products.html',
                         mappings=mappings,
                         channels=channels,
                         channel_filter=channel_filter)


@ecommerce_bp.route('/mappings/products/create', methods=['GET', 'POST'])
@require_ecommerce_permission('mappings', 'create')
def mappings_products_create():
    """Create product mapping."""
    company_id = session.get('company_id', 0)
    
    if request.method == 'POST':
        channel_id = request.form.get('channel_id')
        internal_item_id = request.form.get('internal_item_id')
        internal_sku = request.form.get('internal_sku', '').strip()
        internal_barcode = request.form.get('internal_barcode', '').strip()
        external_product_id = request.form.get('external_product_id', '').strip()
        external_sku = request.form.get('external_sku', '').strip()
        external_barcode = request.form.get('external_barcode', '').strip()
        external_url = request.form.get('external_url', '').strip()
        
        if not channel_id or not external_product_id:
            flash("Channel and external product ID are required.", "error")
            return redirect(url_for('ecommerce.mappings_products'))
        
        with get_db_context() as db:
            db.execute("""
                INSERT INTO ecommerce_product_mappings
                (channel_id, internal_item_id, internal_sku, internal_barcode,
                 external_product_id, external_sku, external_barcode, external_url,
                 created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (channel_id, internal_item_id or 0, internal_sku, internal_barcode,
                  external_product_id, external_sku, external_barcode, external_url))
            db.commit()
        
        flash("Product mapping created.", "success")
        return redirect(url_for('ecommerce.mappings_products'))
    
    channels = get_all("""
        SELECT id, channel_name FROM ecommerce_channels
        WHERE company_id = ? AND is_active = 1
        ORDER BY channel_name
    """, (company_id,))
    
    return render_template('ecommerce/mappings/products_create.html', channels=channels)


@ecommerce_bp.route('/mappings/categories')
def mappings_categories():
    """List category mappings."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    company_id = session.get('company_id', 0)
    
    mappings = get_all("""
        SELECT m.*, c.channel_name
        FROM ecommerce_category_mappings m
        LEFT JOIN ecommerce_channels c ON m.channel_id = c.id
        ORDER BY c.channel_name, m.internal_category_name
    """, (company_id,))
    
    channels = get_all("""
        SELECT id, channel_name FROM ecommerce_channels
        WHERE company_id = ? AND is_active = 1
        ORDER BY channel_name
    """, (company_id,))
    
    return render_template('ecommerce/mappings/categories.html',
                         mappings=mappings,
                         channels=channels)


# =============================================================================
# FULFILLMENT & RETURNS
# =============================================================================

@ecommerce_bp.route('/fulfillment')
@require_ecommerce_permission('fulfillment', 'view')
def fulfillment():
    """Fulfillment & Returns dashboard."""
    company_id = session.get('company_id', 0)

    # Get fulfillment stats
    stats = {}
    with get_db_context() as db:
        # Shipments by status
        shipments = db.execute("""
            SELECT fulfillment_status, COUNT(*) as cnt
            FROM ecommerce_order_imports
            WHERE company_id = ? AND fulfillment_status != 'unfulfilled'
            GROUP BY fulfillment_status
        """, (company_id,)).fetchall()
        stats['shipments'] = {s['fulfillment_status']: s['cnt'] for s in shipments}

        # Returns stats
        returns = db.execute("""
            SELECT COUNT(*) as cnt FROM ecommerce_exceptions
            WHERE company_id = ? AND exception_type = 'return_request'
        """, (company_id,)).fetchone()
        stats['total_returns'] = returns['cnt'] if returns else 0

        # Pending refunds
        refunds = db.execute("""
            SELECT COUNT(*) as cnt FROM ecommerce_exceptions
            WHERE company_id = ? AND exception_type = 'refund_request' AND status = 'open'
        """, (company_id,)).fetchone()
        stats['pending_refunds'] = refunds['cnt'] if refunds else 0

    # Recent fulfillment activity
    recent_fulfillment = get_all("""
        SELECT o.*, c.channel_name
        FROM ecommerce_order_imports o
        LEFT JOIN ecommerce_channels c ON o.channel_id = c.id
        WHERE o.company_id = ? AND o.fulfillment_status IN ('shipped', 'delivered')
        ORDER BY o.updated_at DESC
        LIMIT 20
    """, (company_id,))

    return render_template('ecommerce/fulfillment/index.html',
                         stats=stats,
                         recent_fulfillment=recent_fulfillment)


@ecommerce_bp.route('/fulfillment/returns')
@require_ecommerce_permission('fulfillment', 'view')
def fulfillment_returns():
    """List return requests."""
    company_id = session.get('company_id', 0)

    returns = get_all("""
        SELECT e.*, c.channel_name
        FROM ecommerce_exceptions e
        LEFT JOIN ecommerce_channels c ON e.channel_id = c.id
        WHERE e.company_id = ? AND e.exception_type = 'return_request'
        ORDER BY e.created_at DESC
    """, (company_id,))

    return render_template('ecommerce/fulfillment/returns.html', returns=returns)


@ecommerce_bp.route('/fulfillment/refunds')
@require_ecommerce_permission('fulfillment', 'view')
def fulfillment_refunds():
    """List refund requests."""
    company_id = session.get('company_id', 0)

    refunds = get_all("""
        SELECT e.*, c.channel_name
        FROM ecommerce_exceptions e
        LEFT JOIN ecommerce_channels c ON e.channel_id = c.id
        WHERE e.company_id = ? AND e.exception_type = 'refund_request'
        ORDER BY e.created_at DESC
    """, (company_id,))

    return render_template('ecommerce/fulfillment/refunds.html', refunds=refunds)


@ecommerce_bp.route('/orders/shipped')
@require_ecommerce_permission('orders', 'view')
def orders_shipped():
    """List shipped orders."""
    company_id = session.get('company_id', 0)

    orders = get_all("""
        SELECT o.*, c.channel_name
        FROM ecommerce_order_imports o
        LEFT JOIN ecommerce_channels c ON o.channel_id = c.id
        WHERE o.company_id = ? AND o.fulfillment_status = 'shipped'
        ORDER BY o.shipped_at DESC
    """, (company_id,))

    return render_template('ecommerce/orders/shipped.html', orders=orders)


@ecommerce_bp.route('/orders/delivered')
@require_ecommerce_permission('orders', 'view')
def orders_delivered():
    """List delivered orders."""
    company_id = session.get('company_id', 0)

    orders = get_all("""
        SELECT o.*, c.channel_name
        FROM ecommerce_order_imports o
        LEFT JOIN ecommerce_channels c ON o.channel_id = c.id
        WHERE o.company_id = ? AND o.fulfillment_status = 'delivered'
        ORDER BY o.delivered_at DESC
    """, (company_id,))

    return render_template('ecommerce/orders/delivered.html', orders=orders)


@ecommerce_bp.route('/orders/cancelled')
@require_ecommerce_permission('orders', 'view')
def orders_cancelled():
    """List cancelled orders."""
    company_id = session.get('company_id', 0)

    orders = get_all("""
        SELECT o.*, c.channel_name
        FROM ecommerce_order_imports o
        LEFT JOIN ecommerce_channels c ON o.channel_id = c.id
        WHERE o.company_id = ? AND o.order_status = 'cancelled'
        ORDER BY o.updated_at DESC
    """, (company_id,))

    return render_template('ecommerce/orders/cancelled.html', orders=orders)


# =============================================================================
# COMMERCE ANALYTICS
# =============================================================================

@ecommerce_bp.route('/analytics')
@require_ecommerce_permission('analytics', 'view')
def analytics():
    """Commerce Analytics dashboard."""
    company_id = session.get('company_id', 0)

    # Date range for reports
    date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

    # Channel performance metrics
    channel_metrics = get_all("""
        SELECT
            c.id as channel_id,
            c.channel_name,
            c.channel_type,
            COUNT(o.id) as order_count,
            SUM(o.total_amount) as total_revenue,
            AVG(o.total_amount) as avg_order_value,
            SUM(CASE WHEN o.payment_status = 'paid' THEN 1 ELSE 0 END) as paid_orders,
            SUM(CASE WHEN o.fulfillment_status = 'delivered' THEN 1 ELSE 0 END) as delivered_orders,
            SUM(CASE WHEN o.order_status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_orders
        FROM ecommerce_channels c
        LEFT JOIN ecommerce_order_imports o ON c.id = o.channel_id
            AND DATE(o.order_date) BETWEEN ? AND ?
        WHERE c.company_id = ?
        GROUP BY c.id
        ORDER BY total_revenue DESC
    """, (date_from, date_to, company_id))

    # Daily sales trend
    daily_sales = get_all("""
        SELECT
            DATE(order_date) as date,
            COUNT(*) as orders,
            SUM(total_amount) as revenue
        FROM ecommerce_order_imports
        WHERE company_id = ? AND DATE(order_date) BETWEEN ? AND ?
        GROUP BY DATE(order_date)
        ORDER BY date
    """, (company_id, date_from, date_to))

    # Top products
    top_products = get_all("""
        SELECT
            l.external_product_name,
            l.external_sku,
            SUM(l.quantity) as units_sold,
            SUM(l.total_amount) as revenue
        FROM ecommerce_order_lines l
        JOIN ecommerce_order_imports o ON l.order_import_id = o.id
        WHERE o.company_id = ? AND DATE(o.order_date) BETWEEN ? AND ?
        GROUP BY l.external_product_id
        ORDER BY revenue DESC
        LIMIT 10
    """, (company_id, date_from, date_to))

    # Order status distribution
    status_dist = get_all("""
        SELECT order_status, COUNT(*) as cnt
        FROM ecommerce_order_imports
        WHERE company_id = ? AND DATE(order_date) BETWEEN ? AND ?
        GROUP BY order_status
    """, (company_id, date_from, date_to))

    # Fulfillment metrics
    fulfillment_metrics = get_one("""
        SELECT
            SUM(CASE WHEN fulfillment_status = 'unfulfilled' THEN 1 ELSE 0 END) as unfulfilled,
            SUM(CASE WHEN fulfillment_status = 'processing' THEN 1 ELSE 0 END) as processing,
            SUM(CASE WHEN fulfillment_status = 'shipped' THEN 1 ELSE 0 END) as shipped,
            SUM(CASE WHEN fulfillment_status = 'delivered' THEN 1 ELSE 0 END) as delivered
        FROM ecommerce_order_imports
        WHERE company_id = ? AND DATE(order_date) BETWEEN ? AND ?
    """, (company_id, date_from, date_to))

    return render_template('ecommerce/analytics/index.html',
                         channel_metrics=channel_metrics,
                         daily_sales=daily_sales,
                         top_products=top_products,
                         status_dist=status_dist,
                         fulfillment_metrics=fulfillment_metrics,
                         date_from=date_from,
                         date_to=date_to)


@ecommerce_bp.route('/analytics/product-performance')
@require_ecommerce_permission('analytics', 'view')
def analytics_product_performance():
    """Product performance report."""
    company_id = session.get('company_id', 0)

    date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

    products = get_all("""
        SELECT
            l.external_product_id,
            l.external_product_name,
            l.external_sku,
            c.channel_name,
            SUM(l.quantity) as units_sold,
            SUM(l.total_amount) as total_revenue,
            AVG(l.unit_price) as avg_price,
            COUNT(DISTINCT l.order_import_id) as order_count
        FROM ecommerce_order_lines l
        JOIN ecommerce_order_imports o ON l.order_import_id = o.id
        LEFT JOIN ecommerce_channels c ON o.channel_id = c.id
        WHERE o.company_id = ? AND DATE(o.order_date) BETWEEN ? AND ?
        GROUP BY l.external_product_id, c.id
        ORDER BY total_revenue DESC
    """, (company_id, date_from, date_to))

    return render_template('ecommerce/analytics/product_performance.html',
                         products=products,
                         date_from=date_from,
                         date_to=date_to)


@ecommerce_bp.route('/analytics/conversion')
@require_ecommerce_permission('analytics', 'view')
def analytics_conversion():
    """Conversion analytics."""
    company_id = session.get('company_id', 0)

    # Get conversion metrics
    metrics = get_one("""
        SELECT
            COUNT(DISTINCT customer_email) as unique_customers,
            COUNT(*) as total_orders,
            SUM(CASE WHEN order_status = 'completed' THEN 1 ELSE 0 END) as completed_orders,
            SUM(CASE WHEN order_status = 'cancelled' THEN 1 ELSE 0 END) as cancelled_orders
        FROM ecommerce_order_imports
        WHERE company_id = ?
    """, (company_id,))

    # Repeat customer analysis
    repeat_customers = get_all("""
        SELECT
            customer_email,
            COUNT(*) as order_count,
            SUM(total_amount) as lifetime_value
        FROM ecommerce_order_imports
        WHERE company_id = ? AND customer_email IS NOT NULL AND customer_email != ''
        GROUP BY customer_email
        HAVING COUNT(*) > 1
        ORDER BY lifetime_value DESC
        LIMIT 20
    """, (company_id,))

    return render_template('ecommerce/analytics/conversion.html',
                         metrics=metrics,
                         repeat_customers=repeat_customers)


# =============================================================================
# CHANNEL STATUS & HEALTH
# =============================================================================

@ecommerce_bp.route('/channels/status')
@require_ecommerce_permission('channels', 'view')
def channels_status():
    """Channel health status view."""
    company_id = session.get('company_id', 0)

    channels = get_all("""
        SELECT
            c.*,
            p.inventory_sync_enabled,
            p.order_sync_enabled,
            p.customer_sync_enabled,
            (SELECT COUNT(*) FROM ecommerce_order_imports WHERE channel_id = c.id) as total_orders,
            (SELECT COUNT(*) FROM ecommerce_order_imports WHERE channel_id = c.id AND sync_status = 'failed') as failed_orders,
            (SELECT COUNT(*) FROM ecommerce_exceptions WHERE channel_id = c.id AND status = 'open') as open_exceptions,
            (SELECT MAX(last_synced_at) FROM ecommerce_inventory_syncs WHERE channel_id = c.id) as last_inventory_sync
        FROM ecommerce_channels c
        LEFT JOIN ecommerce_channel_profiles p ON c.id = p.channel_id
        WHERE c.company_id = ?
        ORDER BY c.channel_name
    """, (company_id,))

    return render_template('ecommerce/channels/status.html', channels=channels)


@ecommerce_bp.route('/channels/logs')
@require_ecommerce_permission('channels', 'view')
def channels_logs():
    """Channel API/webhook logs."""
    company_id = session.get('company_id', 0)
    channel_id = request.args.get('channel', '')

    query = """
        SELECT * FROM ecommerce_api_logs
        WHERE company_id = ?
    """
    params = [company_id]

    if channel_id:
        query += " AND channel_id = ?"
        params.append(channel_id)

    query += " ORDER BY created_at DESC LIMIT 200"

    logs = get_all(query, params)

    channels = get_all("""
        SELECT id, channel_name FROM ecommerce_channels
        WHERE company_id = ? ORDER BY channel_name
    """, (company_id,))

    return render_template('ecommerce/channels/logs.html', logs=logs, channels=channels, channel_filter=channel_id)


# =============================================================================
# CATALOG & PUBLISHING
# =============================================================================

@ecommerce_bp.route('/catalog')
@require_ecommerce_permission('catalog', 'view')
def catalog():
    """Catalog management dashboard."""
    company_id = session.get('company_id', 0)

    # Get catalog stats
    stats = {}
    with get_db_context() as db:
        total_mappings = db.execute("""
            SELECT COUNT(*) as cnt FROM ecommerce_product_mappings pm
            JOIN ecommerce_channels c ON pm.channel_id = c.id
            WHERE c.company_id = ?
        """, (company_id,)).fetchone()
        stats['total_mappings'] = total_mappings['cnt'] if total_mappings else 0

        published = db.execute("""
            SELECT COUNT(*) as cnt FROM ecommerce_product_mappings pm
            JOIN ecommerce_channels c ON pm.channel_id = c.id
            WHERE c.company_id = ? AND pm.sync_status = 'synced'
        """, (company_id,)).fetchone()
        stats['published'] = published['cnt'] if published else 0

        pending = db.execute("""
            SELECT COUNT(*) as cnt FROM ecommerce_product_mappings pm
            JOIN ecommerce_channels c ON pm.channel_id = c.id
            WHERE c.company_id = ? AND pm.sync_status = 'pending'
        """, (company_id,)).fetchone()
        stats['pending'] = pending['cnt'] if pending else 0

        failed = db.execute("""
            SELECT COUNT(*) as cnt FROM ecommerce_product_mappings pm
            JOIN ecommerce_channels c ON pm.channel_id = c.id
            WHERE c.company_id = ? AND pm.sync_status = 'failed'
        """, (company_id,)).fetchone()
        stats['failed'] = failed['cnt'] if failed else 0

    return render_template('ecommerce/catalog/index.html', stats=stats)


@ecommerce_bp.route('/catalog/publish-queue')
@require_ecommerce_permission('catalog', 'view')
def catalog_publish_queue():
    """Product publish queue."""
    company_id = session.get('company_id', 0)

    products = get_all("""
        SELECT pm.*, c.channel_name, i.item_name, i.item_sku
        FROM ecommerce_product_mappings pm
        JOIN ecommerce_channels c ON pm.channel_id = c.id
        LEFT JOIN items i ON pm.internal_item_id = i.id
        WHERE c.company_id = ? AND pm.sync_status = 'pending'
        ORDER BY pm.created_at DESC
    """, (company_id,))

    return render_template('ecommerce/catalog/publish_queue.html', products=products)


@ecommerce_bp.route('/catalog/published')
@require_ecommerce_permission('catalog', 'view')
def catalog_published():
    """Published products."""
    company_id = session.get('company_id', 0)

    products = get_all("""
        SELECT pm.*, c.channel_name, i.item_name, i.item_sku
        FROM ecommerce_product_mappings pm
        JOIN ecommerce_channels c ON pm.channel_id = c.id
        LEFT JOIN items i ON pm.internal_item_id = i.id
        WHERE c.company_id = ? AND pm.sync_status = 'synced'
        ORDER BY pm.last_synced_at DESC
    """, (company_id,))

    return render_template('ecommerce/catalog/published.html', products=products)


@ecommerce_bp.route('/catalog/failed')
@require_ecommerce_permission('catalog', 'view')
def catalog_failed():
    """Failed publishing."""
    company_id = session.get('company_id', 0)

    products = get_all("""
        SELECT pm.*, c.channel_name, i.item_name, i.item_sku
        FROM ecommerce_product_mappings pm
        JOIN ecommerce_channels c ON pm.channel_id = c.id
        LEFT JOIN items i ON pm.internal_item_id = i.id
        WHERE c.company_id = ? AND pm.sync_status = 'failed'
        ORDER BY pm.updated_at DESC
    """, (company_id,))

    return render_template('ecommerce/catalog/failed.html', products=products)


# =============================================================================
# PRICING & PROMOTIONS
# =============================================================================

@ecommerce_bp.route('/pricing')
@require_ecommerce_permission('pricing', 'view')
def pricing():
    """Pricing & Promotions dashboard."""
    company_id = session.get('company_id', 0)

    # Get pricing stats
    stats = {}
    with get_db_context() as db:
        price_lists = db.execute("""
            SELECT COUNT(DISTINCT channel_id) as cnt
            FROM ecommerce_channel_profiles
            WHERE product_sync_enabled = 1
        """).fetchone()
        stats['active_price_lists'] = price_lists['cnt'] if price_lists else 0

        active_promotions = db.execute("""
            SELECT COUNT(*) as cnt FROM ecommerce_exceptions
            WHERE company_id = ? AND exception_type = 'promotion_sync' AND status = 'open'
        """, (company_id,)).fetchone()
        stats['active_promotions'] = active_promotions['cnt'] if active_promotions else 0

    return render_template('ecommerce/pricing/index.html', stats=stats)


@ecommerce_bp.route('/pricing/lists')
@require_ecommerce_permission('pricing', 'view')
def pricing_lists():
    """Channel price lists."""
    company_id = session.get('company_id', 0)

    channels = get_all("""
        SELECT c.*, p.product_sync_enabled, p.inventory_sync_enabled
        FROM ecommerce_channels c
        LEFT JOIN ecommerce_channel_profiles p ON c.id = p.channel_id
        WHERE c.company_id = ? AND c.is_active = 1
        ORDER BY c.channel_name
    """, (company_id,))

    return render_template('ecommerce/pricing/lists.html', channels=channels)


@ecommerce_bp.route('/pricing/promotions')
@require_ecommerce_permission('pricing', 'view')
def pricing_promotions():
    """Promotions management."""
    company_id = session.get('company_id', 0)

    promotions = get_all("""
        SELECT e.*, c.channel_name
        FROM ecommerce_exceptions e
        LEFT JOIN ecommerce_channels c ON e.channel_id = c.id
        WHERE e.company_id = ? AND e.exception_type = 'promotion_sync'
        ORDER BY e.created_at DESC
    """, (company_id,))

    return render_template('ecommerce/pricing/promotions.html', promotions=promotions)


# =============================================================================
# CRM / MARKETING LINKAGE
# =============================================================================

@ecommerce_bp.route('/crm-linkage')
@require_ecommerce_permission('crm_linkage', 'view')
def crm_linkage():
    """CRM / Marketing Linkage dashboard."""
    company_id = session.get('company_id', 0)

    # Linkage stats
    stats = {}
    with get_db_context() as db:
        # Customers with linked CRM profiles
        linked = db.execute("""
            SELECT COUNT(*) as cnt FROM ecommerce_customer_imports
            WHERE company_id = ? AND internal_customer_id > 0
        """, (company_id,)).fetchone()
        stats['linked_customers'] = linked['cnt'] if linked else 0

        # Orders from linked customers
        orders_from_linked = db.execute("""
            SELECT COUNT(*) as cnt FROM ecommerce_order_imports o
            JOIN ecommerce_customer_imports c ON o.customer_email = c.email
            WHERE c.company_id = ? AND c.internal_customer_id > 0
        """, (company_id,)).fetchone()
        stats['orders_from_linked'] = orders_from_linked['cnt'] if orders_from_linked else 0

    return render_template('ecommerce/crm_linkage/index.html', stats=stats)


@ecommerce_bp.route('/crm-linkage/customer-360')
@require_ecommerce_permission('crm_linkage', 'view')
def crm_linkage_customer_360():
    """Customer 360 commerce view."""
    company_id = session.get('company_id', 0)

    customers = get_all("""
        SELECT
            c.*,
            ch.channel_name,
            COUNT(o.id) as order_count,
            SUM(o.total_amount) as lifetime_value,
            MAX(o.order_date) as last_order_date
        FROM ecommerce_customer_imports c
        LEFT JOIN ecommerce_channels ch ON c.channel_id = ch.id
        LEFT JOIN ecommerce_order_imports o ON c.email = o.customer_email
        WHERE c.company_id = ? AND c.internal_customer_id > 0
        GROUP BY c.id
        ORDER BY lifetime_value DESC
        LIMIT 50
    """, (company_id,))

    return render_template('ecommerce/crm_linkage/customer_360.html', customers=customers)


# =============================================================================
# WORKFLOW & APPROVALS
# =============================================================================

@ecommerce_bp.route('/workflow')
@require_ecommerce_permission('workflow', 'view')
def workflow():
    """Workflow & Approvals dashboard."""
    company_id = session.get('company_id', 0)

    # Get pending approvals
    pending = get_all("""
        SELECT e.*, c.channel_name
        FROM ecommerce_exceptions e
        LEFT JOIN ecommerce_channels c ON e.channel_id = c.id
        WHERE e.company_id = ? AND e.status IN ('open', 'in_review')
            AND e.severity IN ('high', 'critical')
        ORDER BY e.created_at DESC
        LIMIT 20
    """, (company_id,))

    return render_template('ecommerce/workflow/index.html', pending=pending)


@ecommerce_bp.route('/workflow/pending')
@require_ecommerce_permission('workflow', 'view')
def workflow_pending():
    """Pending approvals list."""
    company_id = session.get('company_id', 0)

    approvals = get_all("""
        SELECT e.*, c.channel_name
        FROM ecommerce_exceptions e
        LEFT JOIN ecommerce_channels c ON e.channel_id = c.id
        WHERE e.company_id = ? AND e.status IN ('open', 'in_review')
        ORDER BY
            CASE e.severity
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                ELSE 4
            END,
            e.created_at ASC
    """, (company_id,))

    return render_template('ecommerce/workflow/pending.html', approvals=approvals)


@ecommerce_bp.route('/workflow/history')
@require_ecommerce_permission('workflow', 'view')
def workflow_history():
    """Approval history."""
    company_id = session.get('company_id', 0)

    history = get_all("""
        SELECT e.*, c.channel_name
        FROM ecommerce_exceptions e
        LEFT JOIN ecommerce_channels c ON e.channel_id = c.id
        WHERE e.company_id = ? AND e.status IN ('resolved', 'cancelled')
        ORDER BY e.resolved_at DESC
        LIMIT 100
    """, (company_id,))

    return render_template('ecommerce/workflow/history.html', history=history)


# =============================================================================
# REPORTS - EXPORT CENTER
# =============================================================================

@ecommerce_bp.route('/reports/export')
@require_ecommerce_permission('reports', 'export')
def reports_export():
    """Export center for e-commerce reports."""
    company_id = session.get('company_id', 0)

    return render_template('ecommerce/reports/export.html')


# =============================================================================
# SYNC ENGINE
# =============================================================================

@ecommerce_bp.route('/sync/run', methods=['POST'])
def sync_run():
    """Manually trigger sync for a channel."""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'})
    
    company_id = session.get('company_id', 0)
    user_id = session['user_id']
    
    data = request.get_json() or {}
    channel_id = data.get('channel_id')
    sync_type = data.get('type', 'order')  # order, inventory, customer
    
    if not channel_id:
        return jsonify({'success': False, 'message': 'Channel ID required'})
    
    channel = get_one("""
        SELECT * FROM ecommerce_channels WHERE id = ? AND company_id = ?
    """, (channel_id, company_id))
    
    if not channel:
        return jsonify({'success': False, 'message': 'Channel not found'})
    
    profile = get_one("""
        SELECT * FROM ecommerce_channel_profiles WHERE channel_id = ?
    """, (channel_id,))
    
    # Create sync job
    job_id = 0
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO ecommerce_sync_jobs
            (job_type, channel_id, channel_name, company_id,
             status, sync_mode, started_at, created_by)
            VALUES (?, ?, ?, ?, 'running', 'manual', datetime('now'), ?)
        """, (f'{sync_type}_sync', channel_id, channel['channel_name'],
              company_id, user_id))
        job_id = cursor.lastrowid
        db.commit()
    
    # In production, this would trigger actual sync
    # For now, return success
    
    log_ecommerce_audit('sync_started', sync_type, job_id, f"Manual {sync_type} sync",
                        channel_id=channel_id, channel_name=channel['channel_name'],
                        company_id=company_id)
    
    return jsonify({
        'success': True,
        'message': f'{sync_type.title()} sync initiated',
        'job_id': job_id
    })


@ecommerce_bp.route('/sync/jobs')
def sync_jobs():
    """View sync job history."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    company_id = session.get('company_id', 0)
    
    jobs = get_all("""
        SELECT * FROM ecommerce_sync_jobs
        WHERE company_id = ?
        ORDER BY created_at DESC
        LIMIT 100
    """, (company_id,))
    
    return render_template('ecommerce/sync_jobs.html', jobs=jobs)


# =============================================================================
# EXPORT ENDPOINTS - ALL 20 EXPORT TYPES
# =============================================================================

ECOMMERCE_EXPORT_TYPES = [
    'csv', 'excel_text', 'excel_general', 'json', 'xml', 'txt',
    'pdf', 'docx', 'html', 'printable', 'barcode', 'api',
    'email', 'zip', 'backup', 'sql_dump', 'dashboard',
    'summary', 'detailed', 'audit_log'
]

ECOMMERCE_EXPORT_COLUMNS = {
    'orders': ['order_number', 'customer_name', 'email', 'total_amount', 'status', 'order_date'],
    'channels': ['channel_name', 'platform', 'is_active', 'sync_status', 'last_sync'],
    'customers': ['email', 'first_name', 'last_name', 'phone', 'total_orders', 'lifetime_value'],
    'products': ['sku', 'item_name', 'channel_name', 'sync_status', 'price', 'stock'],
    'inventory': ['sku', 'item_name', 'warehouse', 'quantity', 'reserved', 'available'],
    'exceptions': ['exception_number', 'exception_type', 'title', 'severity', 'status', 'created_at'],
    'audit': ['action', 'entity_type', 'user_name', 'timestamp', 'ip_address', 'changes']
}


@ecommerce_bp.route('/api/export/<export_type>', methods=['GET', 'POST'])
@ecommerce_bp.route('/api/export/<data_type>/<export_type>', methods=['GET', 'POST'])
@require_ecommerce_permission('reports', 'export')
def api_export(export_type, data_type=None):
    """Export e-commerce data in all 20 formats."""
    if export_type not in ECOMMERCE_EXPORT_TYPES:
        return jsonify({
            'error': f'Invalid export type. Valid types: {ECOMMERCE_EXPORT_TYPES}'
        }), 400

    company_id = session.get('company_id', 0)

    # Determine data type from URL or default
    if data_type is None:
        data_type = request.args.get('type', 'orders')

    # Get data based on type
    if data_type == 'orders':
        data = get_all("""
            SELECT o.*, c.channel_name
            FROM ecommerce_order_imports o
            LEFT JOIN ecommerce_channels c ON o.channel_id = c.id
            WHERE o.company_id = ?
            ORDER BY o.order_date DESC
            LIMIT 5000
        """, (company_id,))
        columns = ECOMMERCE_EXPORT_COLUMNS['orders']
        title = 'E-commerce Orders'
    elif data_type == 'channels':
        data = get_all("""
            SELECT * FROM ecommerce_channels
            WHERE company_id = ?
            ORDER BY channel_name
        """, (company_id,))
        columns = ECOMMERCE_EXPORT_COLUMNS['channels']
        title = 'E-commerce Channels'
    elif data_type == 'customers':
        data = get_all("""
            SELECT c.*, ch.channel_name,
                   COUNT(o.id) as total_orders,
                   COALESCE(SUM(o.total_amount), 0) as lifetime_value
            FROM ecommerce_customer_imports c
            LEFT JOIN ecommerce_channels ch ON c.channel_id = ch.id
            LEFT JOIN ecommerce_order_imports o ON c.email = o.customer_email
            WHERE c.company_id = ?
            GROUP BY c.id
            ORDER BY lifetime_value DESC
            LIMIT 5000
        """, (company_id,))
        columns = ECOMMERCE_EXPORT_COLUMNS['customers']
        title = 'E-commerce Customers'
    elif data_type == 'products':
        data = get_all("""
            SELECT pm.*, c.channel_name, i.item_name, i.item_sku
            FROM ecommerce_product_mappings pm
            JOIN ecommerce_channels c ON pm.channel_id = c.id
            LEFT JOIN items i ON pm.internal_item_id = i.id
            WHERE c.company_id = ?
            ORDER BY pm.last_synced_at DESC
            LIMIT 5000
        """, (company_id,))
        columns = ECOMMERCE_EXPORT_COLUMNS['products']
        title = 'E-commerce Products'
    elif data_type == 'inventory':
        data = get_all("""
            SELECT i.*, w.warehouse_name
            FROM ecommerce_inventory_sync i
            LEFT JOIN warehouses w ON i.warehouse_id = w.id
            WHERE i.company_id = ?
            ORDER BY i.last_synced_at DESC
            LIMIT 5000
        """, (company_id,))
        columns = ECOMMERCE_EXPORT_COLUMNS['inventory']
        title = 'E-commerce Inventory'
    elif data_type == 'exceptions':
        data = get_all("""
            SELECT * FROM ecommerce_exceptions
            WHERE company_id = ?
            ORDER BY created_at DESC
            LIMIT 5000
        """, (company_id,))
        columns = ECOMMERCE_EXPORT_COLUMNS['exceptions']
        title = 'E-commerce Exceptions'
    elif data_type == 'audit':
        data = get_all("""
            SELECT * FROM ecommerce_audit_logs
            WHERE company_id = ?
            ORDER BY timestamp DESC
            LIMIT 5000
        """, (company_id,))
        columns = ECOMMERCE_EXPORT_COLUMNS['audit']
        title = 'E-commerce Audit Log'
    else:
        return jsonify({'error': f'Data type {data_type} not supported'}), 400

    filename = f'ecommerce_{data_type}_{datetime.now().strftime("%Y%m%d")}'

    return send_export_response(data, export_type, filename, columns, title)


@ecommerce_bp.route('/api/export/list')
@require_ecommerce_permission('reports', 'export')
def list_export_types():
    """List available export types for e-commerce module."""
    return jsonify({
        'module': 'ecommerce',
        'data_types': list(ECOMMERCE_EXPORT_COLUMNS.keys()),
        'export_types': [{'type': t} for t in ECOMMERCE_EXPORT_TYPES]
    })


# =============================================================================
# REGISTER BLUEPRINT
# =============================================================================

def register_ecommerce_routes(app):
    """Register e-commerce routes with Flask app."""
    init_ecommerce()
    app.register_blueprint(ecommerce_bp)
