"""
SCM Routes - Supply Chain Management Module

This module defines all Flask routes for the enterprise Supply Chain Management (SCM) system.
It provides comprehensive supply chain planning, demand planning, supply planning,
replenishment, MRP, inventory optimization, multi-echelon planning, service level management,
scenario planning, alerts, and executive dashboards.

Routes are organized by function:
- SCM Dashboard & Control Tower
- Demand Planning
- Supply Planning
- Replenishment
- MRP / Purchase Suggestions
- Inventory Optimization
- Multi-Echelon Planning
- Service Level & Fulfillment
- Scenario Planning
- Alerts & Exceptions
- Supplier & Procurement Linkage
- Warehouse & Logistics Linkage
- Reports & Analytics
- Export Center
- Workflow & Approvals
- Settings
"""

import sqlite3
import json
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, session, Response

# Import export utilities
from export_utils import (
    send_export_response,
    get_export_columns
)

scm_bp = Blueprint('scm', __name__, url_prefix='/scm')


# =============================================================================
# SUPPLY-CHAIN REDIRECT (friendly URL )
# =============================================================================

@scm_bp.route('/supply-chain')
def supply_chain_redirect():
    """Redirect /supply-chain to the SCM dashboard."""
    from flask import redirect, url_for
    return redirect(url_for('scm.dashboard'))


# =============================================================================
# EXPORT TYPES AND COLUMNS
# =============================================================================

SCM_EXPORT_TYPES = [
    'csv', 'excel_text', 'excel_general', 'json', 'xml', 'txt',
    'pdf', 'docx', 'html', 'printable', 'barcode', 'api',
    'email', 'zip', 'backup', 'sql_dump', 'dashboard',
    'summary', 'detailed', 'audit_log'
]

SCM_EXPORT_COLUMNS = {
    'demand': ['plan_id', 'item_code', 'forecast_date', 'quantity', 'confidence'],
    'supply': ['plan_id', 'item_code', 'supply_date', 'quantity', 'source'],
    'replenishment': ['item_code', 'warehouse', 'suggested_qty', 'current_stock', 'status'],
    'inventory': ['item_code', 'warehouse', 'on_hand', 'allocated', 'available'],
    'alerts': ['alert_id', 'type', 'severity', 'message', 'created_at']
}


def get_db():
    """Get database connection."""
    from flask import current_app, g
    if 'db' not in g:
        g.db = current_app.get_db()
    return g.db


def scm_permission_required(resource, action):
    """Decorator for SCM permission checks."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import redirect, url_for, session
            
            user_id = session.get('user_id')
            if not user_id:
                return redirect(url_for('auth.login'))
            
            db = get_db()
            
            # Check if user has global SCM admin
            global_admin = db.execute(
                "SELECT 1 FROM user_roles WHERE user_id = ? AND role_id = 1",
                (user_id,)
            ).fetchone()
            
            if global_admin:
                return f(*args, **kwargs)
            
            # Check specific permission
            has_permission = db.execute("""
                SELECT 1 FROM planning_user_permissions
                WHERE user_id = ? AND permission_key = ?
            """, (user_id, f"{resource}:{action}")).fetchone()
            
            if has_permission:
                return f(*args, **kwargs)
            
            # Check role-based permission
            role_perm = db.execute("""
                SELECT 1 FROM user_roles ur
                JOIN roles r ON ur.role_id = r.id
                JOIN role_permissions rp ON r.id = rp.role_id
                JOIN permissions p ON rp.permission_id = p.id
                WHERE ur.user_id = ? AND p.resource = ? AND rp.action = ?
            """, (user_id, resource, action)).fetchone()
            
            if role_perm:
                return f(*args, **kwargs)
            
            flash('You do not have permission to access this SCM function.', 'error')
            return redirect(url_for('scm_dashboard'))
        return decorated_function
    return decorator


def log_scm_audit(db, action_type, entity_type, entity_id=None, user_id=None, changes=None, notes=None):
    """Log SCM action to audit trail."""
    changes_json = json.dumps(changes) if changes else None
    db.execute("""
        INSERT INTO planning_audit_log
        (action_type, entity_type, entity_id, user_id, changes_json, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (action_type, entity_type, entity_id, user_id, changes_json, notes))
    db.commit()


def get_scm_settings(db, category=None):
    """Get SCM settings."""
    query = "SELECT setting_key, setting_value FROM planning_settings WHERE is_active = 1"
    params = []
    if category:
        query += " AND category = ?"
        params.append(category)
    rows = db.execute(query, params).fetchall()
    return {r['setting_key']: r['setting_value'] for r in rows}


# ============================================================
# SCM DASHBOARD & CONTROL TOWER
# ============================================================

@scm_bp.route('/')
@scm_bp.route('/dashboard')
@scm_permission_required('scm', 'dashboard')
def scm_dashboard():
    """Main SCM Dashboard - Supply Chain Control Tower."""
    db = get_db()
    
    # Get key metrics
    total_items = db.execute("SELECT COUNT(*) as cnt FROM wms_items WHERE is_active = 1").fetchone()['cnt']
    active_alerts = db.execute("SELECT COUNT(*) as cnt FROM planning_alerts WHERE is_acknowledged = 0").fetchone()['cnt']
    
    # Stock health metrics
    zero_stock = db.execute("""
        SELECT COUNT(*) as cnt FROM wms_inventory_balances ib
        JOIN wms_items i ON ib.item_id = i.id
        WHERE i.is_active = 1 AND ib.quantity <= 0
    """).fetchone()['cnt']
    
    below_safety = db.execute("""
        SELECT COUNT(*) as cnt FROM wms_inventory_balances ib
        JOIN wms_items i ON ib.item_id = i.id
        LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
        WHERE i.is_active = 1 AND ib.quantity > 0 
        AND ib.quantity < COALESCE(ip.safety_stock_days * (SELECT AVG(sales_quantity + consumption_quantity) / 30 
            FROM planning_demand_history WHERE item_id = i.id), 10)
    """).fetchone()['cnt']
    
    below_rop = db.execute("""
        SELECT COUNT(*) as cnt FROM wms_inventory_balances ib
        JOIN wms_items i ON ib.item_id = i.id
        LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
        WHERE i.is_active = 1 AND ib.quantity > 0 
        AND ib.quantity < COALESCE(ip.reorder_point_days * (SELECT AVG(sales_quantity + consumption_quantity) / 30 
            FROM planning_demand_history WHERE item_id = i.id), 5)
    """).fetchone()['cnt']
    
    excess_stock = db.execute("""
        SELECT COUNT(*) as cnt FROM wms_inventory_balances ib
        JOIN wms_items i ON ib.item_id = i.id
        LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
        WHERE i.is_active = 1 
        AND ib.quantity > COALESCE(ip.max_order_quantity, 1000)
    """).fetchone()['cnt']
    
    # Open recommendations
    open_purchase_recs = db.execute(
        "SELECT COUNT(*) as cnt FROM planning_purchase_recommendations WHERE status = 'OPEN'"
    ).fetchone()['cnt']
    
    open_replenishment = db.execute(
        "SELECT COUNT(*) as cnt FROM planning_replenishment_recommendations WHERE status = 'OPEN'"
    ).fetchone()['cnt']
    
    open_transfer_recs = db.execute(
        "SELECT COUNT(*) as cnt FROM planning_transfer_recommendations WHERE status = 'OPEN'"
    ).fetchone()['cnt']
    
    # Forecast status
    pending_forecasts = db.execute(
        "SELECT COUNT(*) as cnt FROM planning_forecast_runs WHERE status = 'DRAFT'"
    ).fetchone()['cnt']
    
    active_scenarios = db.execute(
        "SELECT COUNT(*) as cnt FROM planning_scenarios WHERE is_active = 1"
    ).fetchone()['cnt']
    
    # Demand & Supply Summary (last 30 days)
    recent_demand = db.execute("""
        SELECT COALESCE(SUM(sales_quantity + consumption_quantity), 0) as total
        FROM planning_demand_history
        WHERE period_start >= DATE('now', '-30 days')
    """).fetchone()['total']
    
    in_transit_value = db.execute("""
        SELECT COALESCE(SUM(ir.quantity * COALESCE(i.unit_cost, 0)), 0) as total
        FROM wms_inbound_receipts ir
        JOIN wms_items i ON ir.item_id = i.id
        WHERE ir.status IN ('APPROVED', 'SENT', 'IN_TRANSIT')
    """).fetchone()['total']
    
    # Service level metrics
    fill_rate = db.execute("""
        SELECT COALESCE(
            (SELECT SUM(shipped_quantity) * 1.0 / SUM(ordered_quantity) 
             FROM wms_dispatch_plan_lines dl
             JOIN wms_dispatch_plans d ON dl.dispatch_plan_id = d.id
             WHERE d.created_at >= DATE('now', '-30 days'))
        , 1.0) as rate
    """).fetchone()['rate'] or 0.95
    
    # Critical alerts by type
    critical_shortages = db.execute(
        "SELECT COUNT(*) as cnt FROM planning_alerts WHERE alert_type = 'STOCKOUT' AND is_acknowledged = 0"
    ).fetchone()['cnt']
    
    critical_delays = db.execute(
        "SELECT COUNT(*) as cnt FROM planning_alerts WHERE alert_type = 'SUPPLIER_DELAY' AND is_acknowledged = 0"
    ).fetchone()['cnt']
    
    # Recent alerts
    recent_alerts = db.execute("""
        SELECT a.*, i.item_code
        FROM planning_alerts a
        LEFT JOIN wms_items i ON a.item_id = i.id
        ORDER BY a.created_at DESC
        LIMIT 10
    """).fetchall()
    
    # Top shortage items
    top_shortage_items = db.execute("""
        SELECT i.item_code, i.name, COALESCE(ib.quantity, 0) as qty, 
               COALESCE(i.reorder_point, 50) as rop
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        WHERE i.is_active = 1 AND COALESCE(ib.quantity, 0) < COALESCE(i.reorder_point, 50)
        ORDER BY (COALESCE(i.reorder_point, 50) - COALESCE(ib.quantity, 0)) DESC
        LIMIT 5
    """).fetchall()
    
    # Top overstock items
    top_overstock_items = db.execute("""
        SELECT i.item_code, i.name, COALESCE(ib.quantity, 0) as qty,
               COALESCE(i.max_stock_level, 500) as max_stock
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        WHERE i.is_active = 1 AND COALESCE(ib.quantity, 0) > COALESCE(i.max_stock_level, 500)
        ORDER BY (COALESCE(ib.quantity, 0) - COALESCE(i.max_stock_level, 500)) DESC
        LIMIT 5
    """).fetchall()
    
    # Coverage stats
    coverage_stats = []
    coverage_buckets = [(7, '0-7 days'), (14, '7-14 days'), (30, '14-30 days'), (60, '30-60 days'), (999, '60+ days')]
    
    for days, label in coverage_buckets:
        if days == 999:
            count = db.execute("""
                SELECT COUNT(*) as cnt FROM wms_inventory_balances ib
                JOIN wms_items i ON ib.item_id = i.id
                WHERE i.is_active = 1 AND ib.quantity > 0
                AND (SELECT AVG(sales_quantity + consumption_quantity) / 30 FROM planning_demand_history 
                     WHERE item_id = i.id) <= 0
                OR (SELECT AVG(sales_quantity + consumption_quantity) / 30 FROM planning_demand_history 
                    WHERE item_id = i.id) * 60 <= ib.quantity
            """).fetchone()['cnt']
        else:
            count = 0
        
        coverage_stats.append({'days': label, 'count': count or 0})
    
    # Branch/Entity Summary
    branches = db.execute("SELECT id, name FROM companies WHERE is_active = 1 LIMIT 10").fetchall()
    
    return render_template('scm/dashboard/control_tower.html',
        title='SCM Control Tower',
        total_items=total_items,
        active_alerts=active_alerts,
        zero_stock=zero_stock,
        below_safety=below_safety,
        below_rop=below_rop,
        excess_stock=excess_stock,
        open_purchase_recs=open_purchase_recs,
        open_replenishment=open_replenishment,
        open_transfer_recs=open_transfer_recs,
        pending_forecasts=pending_forecasts,
        active_scenarios=active_scenarios,
        recent_demand=recent_demand,
        in_transit_value=in_transit_value,
        fill_rate=fill_rate * 100,
        critical_shortages=critical_shortages,
        critical_delays=critical_delays,
        recent_alerts=recent_alerts,
        top_shortage_items=top_shortage_items,
        top_overstock_items=top_overstock_items,
        coverage_stats=coverage_stats,
        branches=branches
    )


@scm_bp.route('/executive-dashboard')
@scm_permission_required('scm', 'dashboard')
def scm_executive_dashboard():
    """Executive SCM Dashboard for management overview."""
    db = get_db()
    
    # KPI Summary
    total_items = db.execute("SELECT COUNT(*) as cnt FROM wms_items WHERE is_active = 1").fetchone()['cnt']
    
    # Calculate service level (last 30 days)
    fill_rate = db.execute("""
        SELECT COALESCE(
            (SELECT SUM(shipped_quantity) * 1.0 / NULLIF(SUM(ordered_quantity), 0) 
             FROM wms_dispatch_plan_lines dl
             JOIN wms_dispatch_plans d ON dl.dispatch_plan_id = d.id
             WHERE d.created_at >= DATE('now', '-30 days'))
        , 0.95) as rate
    """).fetchone()['rate'] or 0.95
    
    # Stockout rate
    stockout_rate = db.execute("""
        SELECT COALESCE(
            (SELECT COUNT(DISTINCT item_id) * 1.0 / NULLIF((SELECT COUNT(*) FROM wms_items WHERE is_active = 1), 0)
             FROM planning_alerts WHERE alert_type = 'STOCKOUT' 
             AND created_at >= DATE('now', '-30 days'))
        , 0) as rate
    """).fetchone()['rate'] or 0
    
    # Average days of inventory
    avg_doi = db.execute("""
        SELECT COALESCE(
            (SELECT SUM(ib.quantity) * 1.0 / NULLIF(SUM(pd.avg_daily), 0)
             FROM wms_inventory_balances ib
             JOIN wms_items i ON ib.item_id = i.id
             LEFT JOIN (
                 SELECT item_id, AVG(sales_quantity + consumption_quantity) / 30 as avg_daily
                 FROM planning_demand_history
                 WHERE period_start >= DATE('now', '-30 days')
                 GROUP BY item_id
             ) pd ON ib.item_id = pd.item_id
             WHERE i.is_active = 1)
        , 30) as doi
    """).fetchone()['doi'] or 30
    
    # Forecast accuracy (mock - would need actual forecast vs actual comparison)
    forecast_accuracy = 0.85
    
    # Demand trends (last 7 days vs previous 7 days)
    demand_this_week = db.execute("""
        SELECT COALESCE(SUM(sales_quantity + consumption_quantity), 0) as total
        FROM planning_demand_history
        WHERE period_start >= DATE('now', '-7 days')
    """).fetchone()['total']
    
    demand_last_week = db.execute("""
        SELECT COALESCE(SUM(sales_quantity + consumption_quantity), 0) as total
        FROM planning_demand_history
        WHERE period_start >= DATE('now', '-14 days') AND period_start < DATE('now', '-7 days')
    """).fetchone()['total']
    
    demand_trend = ((demand_this_week - demand_last_week) / demand_last_week * 100) if demand_last_week > 0 else 0
    
    # Open recommendations summary
    open_pr = db.execute("SELECT COUNT(*) as cnt FROM planning_purchase_recommendations WHERE status = 'OPEN'").fetchone()['cnt']
    open_rr = db.execute("SELECT COUNT(*) as cnt FROM planning_replenishment_recommendations WHERE status = 'OPEN'").fetchone()['cnt']
    open_tr = db.execute("SELECT COUNT(*) as cnt FROM planning_transfer_recommendations WHERE status = 'OPEN'").fetchone()['cnt']
    total_recs = open_pr + open_rr + open_tr
    
    # Cost impact of recommendations
    total_rec_cost = db.execute("""
        SELECT COALESCE(SUM(estimated_total_cost), 0) as total
        FROM planning_purchase_recommendations WHERE status = 'OPEN'
    """).fetchone()['total']
    
    # Alert summary
    alerts_by_severity = db.execute("""
        SELECT severity, COUNT(*) as cnt
        FROM planning_alerts WHERE is_acknowledged = 0
        GROUP BY severity
    """).fetchall()
    alerts_by_severity = {r['severity']: r['cnt'] for r in alerts_by_severity}
    
    # Branch performance
    branch_perf = db.execute("""
        SELECT c.name, 
               COALESCE(SUM(ib.quantity), 0) as total_stock,
               COALESCE((SELECT SUM(sales_quantity + consumption_quantity) 
                        FROM planning_demand_history dh 
                        WHERE dh.company_id = c.id AND dh.period_start >= DATE('now', '-30 days')), 0) as demand_30d
        FROM companies c
        LEFT JOIN wms_inventory_balances ib ON c.id = ib.company_id
        WHERE c.is_active = 1
        GROUP BY c.id
        LIMIT 10
    """).fetchall()
    
    # Inventory ABC analysis
    abc_dist = db.execute("""
        SELECT ip.abc_class, COUNT(*) as cnt
        FROM planning_item_profiles ip
        JOIN wms_items i ON ip.item_id = i.id
        WHERE i.is_active = 1
        GROUP BY ip.abc_class
    """).fetchall()
    abc_dist = {r['abc_class']: r['cnt'] for r in abc_dist}
    
    return render_template('scm/dashboard/executive.html',
        title='Executive SCM Dashboard',
        total_items=total_items,
        fill_rate=fill_rate * 100,
        stockout_rate=stockout_rate * 100,
        avg_doi=avg_doi,
        forecast_accuracy=forecast_accuracy * 100,
        demand_trend=demand_trend,
        open_pr=open_pr,
        open_rr=open_rr,
        open_tr=open_tr,
        total_recs=total_recs,
        total_rec_cost=total_rec_cost,
        alerts_by_severity=alerts_by_severity,
        branch_perf=branch_perf,
        abc_dist=abc_dist
    )


# ============================================================
# DEMAND PLANNING
# ============================================================

@scm_bp.route('/demand')
@scm_permission_required('scm', 'demand')
def demand_planning():
    """Demand Planning main page."""
    db = get_db()
    
    # Demand summary stats
    total_demand_30d = db.execute("""
        SELECT COALESCE(SUM(sales_quantity + consumption_quantity), 0) as total
        FROM planning_demand_history
        WHERE period_start >= DATE('now', '-30 days')
    """).fetchone()['total']
    
    total_demand_90d = db.execute("""
        SELECT COALESCE(SUM(sales_quantity + consumption_quantity), 0) as total
        FROM planning_demand_history
        WHERE period_start >= DATE('now', '-90 days')
    """).fetchone()['total']
    
    avg_daily_demand = total_demand_30d / 30 if total_demand_30d > 0 else 0
    
    # Items with demand
    items_with_demand = db.execute("""
        SELECT COUNT(DISTINCT item_id) as cnt
        FROM planning_demand_history
        WHERE period_start >= DATE('now', '-30 days')
        AND (sales_quantity + consumption_quantity) > 0
    """).fetchone()['cnt']
    
    # Forecast runs
    forecast_runs = db.execute("""
        SELECT r.*, u.username as created_by_name
        FROM planning_forecast_runs r
        LEFT JOIN users u ON r.created_by = u.id
        ORDER BY r.created_at DESC
        LIMIT 10
    """).fetchall()
    
    # Demand by category
    demand_by_category = db.execute("""
        SELECT c.name as category, 
               COALESCE(SUM(dh.sales_quantity + dh.consumption_quantity), 0) as total
        FROM planning_demand_history dh
        JOIN wms_items i ON dh.item_id = i.id
        LEFT JOIN wms_categories c ON i.category_id = c.id
        WHERE dh.period_start >= DATE('now', '-30 days')
        GROUP BY c.id
        ORDER BY total DESC
    """).fetchall()
    
    return render_template('scm/demand/index.html',
        title='Demand Planning',
        total_demand_30d=total_demand_30d,
        total_demand_90d=total_demand_90d,
        avg_daily_demand=avg_daily_demand,
        items_with_demand=items_with_demand,
        forecast_runs=forecast_runs,
        demand_by_category=demand_by_category
    )


@scm_bp.route('/demand/forecast-center')
@scm_permission_required('scm', 'demand')
def demand_forecast_center():
    """Forecast Center - generate and manage forecasts."""
    db = get_db()
    
    forecast_runs = db.execute("""
        SELECT r.*, u.username as created_by_name,
               (SELECT COUNT(*) FROM planning_forecast_lines WHERE run_id = r.id) as line_count
        FROM planning_forecast_runs r
        LEFT JOIN users u ON r.created_by = u.id
        ORDER BY r.created_at DESC
    """).fetchall()
    
    return render_template('scm/demand/forecast_center.html',
        title='Forecast Center',
        forecast_runs=forecast_runs
    )


@scm_bp.route('/demand/forecast/generate', methods=['POST'])
@scm_permission_required('scm', 'demand')
def demand_generate_forecast():
    """Generate a new forecast run."""
    db = get_db()
    settings = get_scm_settings(db)
    
    run_name = request.form.get('run_name', f"Forecast {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    method = request.form.get('method', 'MOVING_AVERAGE')
    horizon_days = int(request.form.get('horizon_days', settings.get('FORECAST_HORIZON_DAYS', 30)))
    
    # Create forecast run
    cursor = db.execute("""
        INSERT INTO planning_forecast_runs 
        (run_name, forecast_type, method, horizon_days, status, created_by)
        VALUES (?, ?, ?, ?, 'DRAFT', ?)
    """, (run_name, 'DEMAND', method, horizon_days, session.get('user_id')))
    run_id = cursor.lastrowid
    
    # Get all items with demand history
    items = db.execute("""
        SELECT DISTINCT item_id FROM planning_demand_history
        WHERE period_start >= DATE('now', '-12 months')
    """).fetchall()
    
    for item_row in items:
        item_id = item_row['item_id']
        
        # Get demand history for this item
        history = db.execute("""
            SELECT period_start, sales_quantity + consumption_quantity as demand
            FROM planning_demand_history
            WHERE item_id = ? AND period_start >= DATE('now', '-12 months')
            ORDER BY period_start
        """, (item_id,)).fetchall()
        
        if not history:
            continue
        
        demand_values = [h['demand'] for h in history]
        
        # Calculate forecast based on method
        if method == 'MOVING_AVERAGE':
            forecast_value = sum(demand_values[-3:]) / min(3, len(demand_values))
        elif method == 'WEIGHTED_MOVING_AVERAGE':
            weights = [0.5, 0.3, 0.2] if len(demand_values) >= 3 else [1.0]
            forecast_value = sum(v * w for v, w in zip(demand_values[-3:], weights)) / sum(weights)
        elif method == 'EXPONENTIAL_SMOOTHING':
            alpha = 0.3
            forecast_value = demand_values[0]
            for v in demand_values[1:]:
                forecast_value = alpha * v + (1 - alpha) * forecast_value
        else:
            forecast_value = sum(demand_values[-3:]) / min(3, len(demand_values))
        
        # Generate daily forecasts for the horizon
        for day_offset in range(horizon_days):
            forecast_date = (datetime.now() + timedelta(days=day_offset)).strftime('%Y-%m-%d')
            
            db.execute("""
                INSERT INTO planning_forecast_lines
                (run_id, item_id, period_start, period_type, base_quantity, final_quantity)
                VALUES (?, ?, ?, 'daily', ?, ?)
            """, (run_id, item_id, forecast_date, forecast_value, forecast_value))
    
    db.commit()
    
    log_scm_audit(db, 'FORECAST_GENERATED', 'forecast_run', run_id,
                   user_id=session.get('user_id'),
                   changes={'method': method, 'horizon_days': horizon_days})
    
    flash(f'Forecast "{run_name}" generated successfully.', 'success')
    return redirect(url_for('scm.demand_forecast_center'))


@scm_bp.route('/demand/forecast/<int:run_id>')
@scm_permission_required('scm', 'demand')
def demand_forecast_detail(run_id):
    """View forecast run details."""
    db = get_db()
    
    run = db.execute("SELECT * FROM planning_forecast_runs WHERE id = ?", (run_id,)).fetchone()
    if not run:
        flash('Forecast run not found.', 'error')
        return redirect(url_for('scm.demand_forecast_center'))
    
    forecast_lines = db.execute("""
        SELECT fl.*, i.item_code, i.name as item_name
        FROM planning_forecast_lines fl
        JOIN wms_items i ON fl.item_id = i.id
        WHERE fl.run_id = ?
        ORDER BY i.item_code, fl.period_start
        LIMIT 100
    """, (run_id,)).fetchall()
    
    return render_template('scm/demand/forecast_detail.html',
        title=f'Forecast: {run["run_name"]}',
        run=run,
        forecast_lines=forecast_lines
    )


@scm_bp.route('/demand/by-item/<int:item_id>')
@scm_permission_required('scm', 'demand')
def demand_by_item(item_id):
    """Demand forecast by item."""
    db = get_db()
    
    item = db.execute("SELECT * FROM wms_items WHERE id = ?", (item_id,)).fetchone()
    if not item:
        flash('Item not found.', 'error')
        return redirect(url_for('scm.demand_planning'))
    
    # Historical demand
    demand_history = db.execute("""
        SELECT period_start, sales_quantity, consumption_quantity,
               sales_quantity + consumption_quantity as total_demand
        FROM planning_demand_history
        WHERE item_id = ? AND period_start >= DATE('now', '-12 months')
        ORDER BY period_start
    """, (item_id,)).fetchall()
    
    # Latest forecast
    latest_forecast = db.execute("""
        SELECT fl.*, r.run_name
        FROM planning_forecast_lines fl
        JOIN planning_forecast_runs r ON fl.run_id = r.id
        WHERE fl.item_id = ? AND r.status = 'DRAFT'
        ORDER BY fl.period_start
        LIMIT 30
    """, (item_id,)).fetchall()
    
    # Demand stats
    demand_stats = db.execute("""
        SELECT 
            SUM(sales_quantity + consumption_quantity) as total_demand,
            AVG(sales_quantity + consumption_quantity) as avg_demand,
            MAX(sales_quantity + consumption_quantity) as max_demand,
            MIN(CASE WHEN sales_quantity + consumption_quantity > 0 THEN sales_quantity + consumption_quantity END) as min_demand
        FROM planning_demand_history
        WHERE item_id = ? AND period_start >= DATE('now', '-12 months')
    """, (item_id,)).fetchone()
    
    return render_template('scm/demand/forecast_by_item.html',
        title=f'Demand: {item["item_code"]}',
        item=item,
        demand_history=demand_history,
        latest_forecast=latest_forecast,
        demand_stats=demand_stats
    )


@scm_bp.route('/demand/by-warehouse')
@scm_permission_required('scm', 'demand')
def demand_by_warehouse():
    """Demand forecast by warehouse."""
    db = get_db()
    
    warehouses = db.execute("SELECT id, name FROM wms_warehouses WHERE is_active = 1").fetchall()
    
    warehouse_demand = []
    for wh in warehouses:
        demand = db.execute("""
            SELECT COALESCE(SUM(sales_quantity + consumption_quantity), 0) as total
            FROM planning_demand_history
            WHERE warehouse_id = ? AND period_start >= DATE('now', '-30 days')
        """, (wh['id'],)).fetchone()['total']
        
        items_count = db.execute("""
            SELECT COUNT(DISTINCT item_id) as cnt
            FROM planning_demand_history
            WHERE warehouse_id = ? AND period_start >= DATE('now', '-30 days')
            AND (sales_quantity + consumption_quantity) > 0
        """, (wh['id'],)).fetchone()['cnt']
        
        warehouse_demand.append({
            'warehouse': wh,
            'total_demand_30d': demand,
            'items_count': items_count
        })
    
    return render_template('scm/demand/forecast_by_warehouse.html',
        title='Demand by Warehouse',
        warehouse_demand=warehouse_demand
    )


@scm_bp.route('/demand/versions')
@scm_permission_required('scm', 'demand')
def demand_versions():
    """Forecast versions comparison."""
    db = get_db()
    
    forecast_runs = db.execute("""
        SELECT r.*, 
               (SELECT COUNT(*) FROM planning_forecast_lines WHERE run_id = r.id) as line_count,
               u.username as created_by_name
        FROM planning_forecast_runs r
        LEFT JOIN users u ON r.created_by = u.id
        ORDER BY r.created_at DESC
    """).fetchall()
    
    return render_template('scm/demand/forecast_versions.html',
        title='Forecast Versions',
        forecast_runs=forecast_runs
    )


@scm_bp.route('/demand/overrides')
@scm_permission_required('scm', 'demand')
def demand_overrides():
    """Forecast manual overrides."""
    db = get_db()
    
    overrides = db.execute("""
        SELECT o.*, i.item_code, i.name as item_name,
               u.username as created_by_name
        FROM planning_forecast_overrides o
        JOIN wms_items i ON o.item_id = i.id
        LEFT JOIN users u ON o.created_by = u.id
        ORDER BY o.created_at DESC
        LIMIT 50
    """).fetchall()
    
    return render_template('scm/demand/forecast_overrides.html',
        title='Forecast Overrides',
        overrides=overrides
    )


@scm_bp.route('/demand/accuracy')
@scm_permission_required('scm', 'demand')
def demand_accuracy():
    """Forecast accuracy analysis."""
    db = get_db()
    
    # Calculate forecast accuracy metrics
    # This would compare actual demand vs forecasted demand
    
    accuracy_metrics = db.execute("""
        SELECT 
            r.id as run_id,
            r.run_name,
            r.status,
            r.approved_at,
            u.username as approved_by
        FROM planning_forecast_runs r
        LEFT JOIN users u ON r.approved_by = u.id
        WHERE r.status = 'APPROVED'
        ORDER BY r.approved_at DESC
        LIMIT 10
    """).fetchall()
    
    # Bias analysis
    bias_analysis = []
    
    return render_template('scm/demand/forecast_accuracy.html',
        title='Forecast Accuracy',
        accuracy_metrics=accuracy_metrics,
        bias_analysis=bias_analysis
    )


@scm_bp.route('/demand/reports')
@scm_permission_required('scm', 'reports')
def demand_reports():
    """Demand planning reports."""
    return render_template('scm/demand/reports.html',
        title='Demand Reports'
    )


# ============================================================
# ENTERPRISE DEMAND PLANNING: CONTROL TOWER
# ============================================================

@scm_bp.route('/demand/control-tower')
@scm_permission_required('scm', 'demand')
def demand_control_tower():
    """Forecast Control Tower - Global demand planning command center."""
    db = get_db()

    # Key metrics
    active_forecast_runs = db.execute("""
        SELECT COUNT(*) as cnt FROM planning_forecast_runs WHERE status = 'DRAFT'
    """).fetchone()['cnt']

    approved_forecasts = db.execute("""
        SELECT COUNT(*) as cnt FROM planning_forecast_versions WHERE status = 'APPROVED'
    """).fetchone()['cnt']

    pending_overrides = db.execute("""
        SELECT COUNT(*) as cnt FROM planning_forecast_overrides WHERE status = 'PENDING'
    """).fetchone()['cnt']

    high_error_items = db.execute("""
        SELECT COUNT(*) as cnt FROM planning_volatility_alerts
        WHERE alert_type IN ('HIGH_VOLATILITY', 'DEMAND_SPIKE', 'DEMAND_DROP')
        AND is_acknowledged = 0
    """).fetchone()['cnt']

    consensus_pending = db.execute("""
        SELECT COUNT(*) as cnt FROM planning_consensus_forecasts WHERE status = 'DRAFT'
    """).fetchone()['cnt']

    # Recent alerts
    recent_alerts = db.execute("""
        SELECT a.*, i.item_code, i.name as item_name
        FROM planning_alerts a
        LEFT JOIN wms_items i ON a.item_id = i.id
        ORDER BY a.created_at DESC
        LIMIT 10
    """).fetchall()

    # High priority items needing attention
    critical_watchlist = db.execute("""
        SELECT va.*, i.item_code, i.name as item_name
        FROM planning_volatility_alerts va
        LEFT JOIN wms_items i ON va.item_id = i.id
        WHERE va.is_acknowledged = 0 AND va.severity IN ('HIGH', 'CRITICAL')
        ORDER BY va.created_at DESC
        LIMIT 10
    """).fetchall()

    # Forecast vs actual headline
    forecast_vs_actual = db.execute("""
        SELECT
            COALESCE(SUM(fl.final_quantity), 0) as total_forecast,
            COALESCE(SUM(dh.sales_quantity + dh.consumption_quantity), 0) as total_actual
        FROM planning_forecast_lines fl
        LEFT JOIN planning_demand_history dh
            ON fl.item_id = dh.item_id
            AND fl.period_start = dh.period_start
        WHERE fl.period_start >= DATE('now', '-30 days')
    """).fetchone()

    return render_template('scm/demand/control_tower.html',
        title='Forecast Control Tower',
        active_forecast_runs=active_forecast_runs,
        approved_forecasts=approved_forecasts,
        pending_overrides=pending_overrides,
        high_error_items=high_error_items,
        consensus_pending=consensus_pending,
        recent_alerts=recent_alerts,
        critical_watchlist=critical_watchlist,
        forecast_vs_actual=forecast_vs_actual
    )


# ============================================================
# ENTERPRISE DEMAND PLANNING: STATISTICAL FORECASTING
# ============================================================

@scm_bp.route('/demand/statistical')
@scm_permission_required('scm', 'demand')
def demand_statistical():
    """Statistical Forecasting - various forecasting methods."""
    db = get_db()

    items = db.execute("""
        SELECT i.id, i.item_code, i.name, ip.forecast_method, ip.planning_method
        FROM wms_items i
        LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
        WHERE i.is_active = 1
        ORDER BY i.item_code
        LIMIT 100
    """).fetchall()

    return render_template('scm/demand/statistical_forecasting.html',
        title='Statistical Forecasting',
        items=items
    )


@scm_bp.route('/demand/statistical/generate', methods=['POST'])
@scm_permission_required('scm', 'demand')
def demand_generate_statistical():
    """Generate forecast using selected statistical method."""
    db = get_db()

    method = request.form.get('method', 'MOVING_AVERAGE')
    horizon_days = int(request.form.get('horizon_days', 30))
    item_ids = request.form.getlist('item_ids')
    run_name = request.form.get('run_name', f"{method} Forecast {datetime.now().strftime('%Y-%m-%d')}")

    from planning_models import generate_statistical_forecast

    created_runs = []
    for item_id in item_ids:
        run_id = generate_statistical_forecast(
            db, int(item_id), method=method,
            horizon_days=horizon_days, period_type='daily',
            created_by=session.get('user_id'),
            run_name=f"{run_name} - Item {item_id}"
        )
        if run_id:
            created_runs.append(run_id)

    flash(f'Generated {len(created_runs)} forecast(s) using {method}.', 'success')
    return redirect(url_for('scm.demand_statistical'))


@scm_bp.route('/demand/statistical/compare')
@scm_permission_required('scm', 'demand')
def demand_compare_methods():
    """Compare different forecasting methods for items."""
    db = get_db()
    item_id = request.args.get('item_id', type=int)

    if not item_id:
        flash('Please select an item.', 'error')
        return redirect(url_for('scm.demand_statistical'))

    item = db.execute("SELECT * FROM wms_items WHERE id = ?", (item_id,)).fetchone()

    history = db.execute("""
        SELECT period_start, sales_quantity + consumption_quantity as demand
        FROM planning_demand_history
        WHERE item_id = ? AND period_start >= DATE('now', '-12 months')
        ORDER BY period_start
    """, (item_id,)).fetchall()

    from planning_models import (
        calculate_moving_average, calculate_weighted_moving_average_v2,
        calculate_exponential_smoothing, calculate_double_exponential_smoothing,
        calculate_triple_exponential_smoothing
    )

    demand_values = [h['demand'] for h in history]

    methods = {}
    if len(demand_values) >= 3:
        methods['MOVING_AVERAGE_3'] = calculate_moving_average(demand_values, 3)
        methods['MOVING_AVERAGE_6'] = calculate_moving_average(demand_values, 6)
        methods['WMA'] = calculate_weighted_moving_average_v2(demand_values, [0.5, 0.3, 0.2])
        methods['EXP_SMOOTH'] = calculate_exponential_smoothing(demand_values, 0.3)

    if len(demand_values) >= 6:
        level, trend = calculate_double_exponential_smoothing(demand_values, 0.3, 0.1)
        methods['DOUBLE_EXP'] = level + trend * 3

    if len(demand_values) >= 24:
        forecast, _ = calculate_triple_exponential_smoothing(demand_values, 0.3, 0.1, 0.1, 12)
        methods['HOLT_WINTERS'] = forecast

    model_performance = db.execute("""
        SELECT * FROM planning_model_performance
        WHERE item_id = ?
        ORDER BY period_start DESC
        LIMIT 20
    """, (item_id,)).fetchall()

    return render_template('scm/demand/model_comparison.html',
        title='Forecast Model Comparison',
        item=item,
        demand_history=history,
        methods=methods,
        model_performance=model_performance
    )


# ============================================================
# ENTERPRISE DEMAND PLANNING: FORECAST VERSIONS
# ============================================================

@scm_bp.route('/demand/versions/list')
@scm_permission_required('scm', 'demand')
def demand_versions_list():
    """List all forecast versions."""
    db = get_db()

    versions = db.execute("""
        SELECT v.*, u.username as created_by_name,
               p.username as published_by_name
        FROM planning_forecast_versions v
        LEFT JOIN users u ON v.created_by = u.id
        LEFT JOIN users p ON v.published_by = p.id
        ORDER BY v.created_at DESC
    """).fetchall()

    return render_template('scm/demand/versions_list.html',
        title='Forecast Versions',
        versions=versions
    )


@scm_bp.route('/demand/versions/create', methods=['POST'])
@scm_permission_required('scm', 'demand')
def demand_create_version():
    """Create a new forecast version snapshot."""
    db = get_db()

    version_name = request.form.get('version_name')
    forecast_run_id = request.form.get('forecast_run_id', type=int)
    is_baseline = request.form.get('is_baseline') == '1'

    from planning_models import create_forecast_version

    version_id = create_forecast_version(
        db, version_name, forecast_run_id,
        created_by=session.get('user_id'),
        is_baseline=is_baseline
    )

    flash(f'Version "{version_name}" created successfully.', 'success')
    return redirect(url_for('scm.demand_versions_detail', version_id=version_id))


@scm_bp.route('/demand/versions/<int:version_id>')
@scm_permission_required('scm', 'demand')
def demand_versions_detail(version_id):
    """View forecast version details."""
    db = get_db()

    version = db.execute("""
        SELECT v.*, u.username as created_by_name
        FROM planning_forecast_versions v
        LEFT JOIN users u ON v.created_by = u.id
        WHERE v.id = ?
    """, (version_id,)).fetchone()

    if not version:
        flash('Version not found.', 'error')
        return redirect(url_for('scm.demand_versions_list'))

    lines = db.execute("""
        SELECT vl.*, i.item_code, i.name as item_name,
               w.name as warehouse_name
        FROM planning_forecast_version_lines vl
        JOIN wms_items i ON vl.item_id = i.id
        LEFT JOIN wms_warehouses w ON vl.warehouse_id = w.id
        WHERE vl.version_id = ?
        ORDER BY i.item_code, vl.period_start
        LIMIT 200
    """, (version_id,)).fetchall()

    return render_template('scm/demand/version_detail.html',
        title=f'Version: {version["version_name"]}',
        version=version,
        lines=lines
    )


@scm_bp.route('/demand/versions/<int:version_id>/freeze', methods=['POST'])
@scm_permission_required('scm', 'demand')
def demand_versions_freeze(version_id):
    """Freeze a forecast version."""
    db = get_db()

    from planning_models import freeze_forecast_version

    freeze_forecast_version(db, version_id, session.get('user_id'))

    flash('Version frozen successfully.', 'success')
    return redirect(url_for('scm.demand_versions_detail', version_id=version_id))


@scm_bp.route('/demand/versions/<int:version_id>/publish', methods=['POST'])
@scm_permission_required('scm', 'demand')
def demand_versions_publish(version_id):
    """Publish a forecast version."""
    db = get_db()

    from planning_models import publish_forecast_version

    publish_forecast_version(db, version_id, session.get('user_id'))

    flash('Version published successfully.', 'success')
    return redirect(url_for('scm.demand_versions_detail', version_id=version_id))


@scm_bp.route('/demand/versions/<int:version_id>/clone', methods=['POST'])
@scm_permission_required('scm', 'demand')
def demand_versions_clone(version_id):
    """Clone a forecast version."""
    db = get_db()

    new_name = request.form.get('new_name')

    from planning_models import clone_forecast_version

    new_version_id = clone_forecast_version(
        db, version_id, new_name,
        created_by=session.get('user_id')
    )

    flash(f'Version cloned as "{new_name}".', 'success')
    return redirect(url_for('scm.demand_versions_detail', version_id=new_version_id))


@scm_bp.route('/demand/versions/compare')
@scm_permission_required('scm', 'demand')
def demand_versions_compare():
    """Compare two forecast versions."""
    db = get_db()

    version_id_1 = request.args.get('version_id_1', type=int)
    version_id_2 = request.args.get('version_id_2', type=int)

    if not version_id_1 or not version_id_2:
        versions = db.execute("""
            SELECT * FROM planning_forecast_versions ORDER BY created_at DESC LIMIT 20
        """).fetchall()
        return render_template('scm/demand/versions_compare_select.html',
            title='Compare Versions',
            versions=versions
        )

    from planning_models import compare_forecast_versions

    comparison = compare_forecast_versions(db, version_id_1, version_id_2)

    version_1 = db.execute("SELECT * FROM planning_forecast_versions WHERE id = ?",
                           (version_id_1,)).fetchone()
    version_2 = db.execute("SELECT * FROM planning_forecast_versions WHERE id = ?",
                           (version_id_2,)).fetchone()

    return render_template('scm/demand/versions_compare.html',
        title='Version Comparison',
        comparison=comparison,
        version_1=version_1,
        version_2=version_2
    )


# ============================================================
# ENTERPRISE DEMAND PLANNING: FORECAST OVERRIDES
# ============================================================

@scm_bp.route('/demand/overrides/list')
@scm_permission_required('scm', 'demand')
def demand_overrides_list():
    """List all forecast overrides."""
    db = get_db()

    status = request.args.get('status')

    query = """
        SELECT o.*, i.item_code, i.name as item_name,
               u.username as created_by_name,
               r.username as reviewed_by_name
        FROM planning_forecast_overrides o
        JOIN wms_items i ON o.item_id = i.id
        LEFT JOIN users u ON o.created_by = u.id
        LEFT JOIN users r ON o.reviewed_by = r.id
    """
    params = []

    if status:
        query += " WHERE o.status = ?"
        params.append(status)

    query += " ORDER BY o.created_at DESC LIMIT 100"

    overrides = db.execute(query, params).fetchall()

    return render_template('scm/demand/overrides_list.html',
        title='Forecast Overrides',
        overrides=overrides,
        current_status=status
    )


@scm_bp.route('/demand/overrides/create', methods=['POST'])
@scm_permission_required('scm', 'demand')
def demand_overrides_create():
    """Create a new forecast override."""
    db = get_db()

    item_id = request.form.get('item_id', type=int)
    period_start = request.form.get('period_start')
    original_quantity = float(request.form.get('original_quantity', 0))
    override_quantity = float(request.form.get('override_quantity', 0))
    override_reason = request.form.get('override_reason')
    override_type = request.form.get('override_type', 'MANUAL')

    cursor = db.execute("""
        INSERT INTO planning_forecast_overrides
        (item_id, period_start, original_quantity, override_quantity, override_reason,
         override_type, status, created_by)
        VALUES (?, ?, ?, ?, ?, ?, 'PENDING', ?)
    """, (item_id, period_start, original_quantity, override_quantity,
          override_reason, override_type, session.get('user_id')))

    override_id = cursor.lastrowid

    from planning_models import create_override_approval, notify_pending_approval
    create_override_approval(db, override_id, session.get('user_id'))
    notify_pending_approval(db, 'override', override_id,
                          f'Override for item {item_id}',
                          'DEMAND_PLANNER')

    db.commit()

    flash('Override created and pending approval.', 'success')
    return redirect(url_for('scm.demand_overrides_list'))


@scm_bp.route('/demand/overrides/bulk', methods=['GET', 'POST'])
@scm_permission_required('scm', 'demand')
def demand_overrides_bulk():
    """Bulk forecast overrides."""
    if request.method == 'POST':
        db = get_db()

        item_ids = request.form.getlist('item_ids')
        period_start = request.form.get('period_start')
        override_percent = float(request.form.get('override_percent', 0))
        override_reason = request.form.get('override_reason')

        for item_id in item_ids:
            item = db.execute("SELECT id FROM wms_items WHERE id = ?", (item_id,)).fetchone()
            if item:
                avg_qty = db.execute("""
                    SELECT AVG(sales_quantity + consumption_quantity) as avg_qty
                    FROM planning_demand_history
                    WHERE item_id = ? AND period_start >= DATE('now', '-30 days')
                """, (item_id,)).fetchone()['avg_qty'] or 0

                original_quantity = avg_qty
                override_quantity = avg_qty * (1 + override_percent / 100)

                db.execute("""
                    INSERT INTO planning_forecast_overrides
                    (item_id, period_start, original_quantity, override_quantity,
                     override_reason, override_type, status, created_by)
                    VALUES (?, ?, ?, ?, ?, 'BULK', 'PENDING', ?)
                """, (item_id, period_start, original_quantity, override_quantity,
                      override_reason, session.get('user_id')))

        db.commit()
        flash(f'Bulk override applied to {len(item_ids)} items.', 'success')
        return redirect(url_for('scm.demand_overrides_list'))

    db = get_db()
    items = db.execute("SELECT id, item_code, name FROM wms_items WHERE is_active = 1 LIMIT 100").fetchall()
    return render_template('scm/demand/overrides_bulk.html',
        title='Bulk Forecast Override',
        items=items
    )


@scm_bp.route('/demand/overrides/<int:override_id>/approve', methods=['POST'])
@scm_permission_required('scm', 'demand')
def demand_overrides_approve(override_id):
    """Approve a forecast override."""
    db = get_db()

    review_notes = request.form.get('review_notes', '')

    from planning_models import approve_override

    approve_override(db, override_id, session.get('user_id'), review_notes)

    flash('Override approved.', 'success')
    return redirect(url_for('scm.demand_overrides_list'))


@scm_bp.route('/demand/overrides/<int:override_id>/reject', methods=['POST'])
@scm_permission_required('scm', 'demand')
def demand_overrides_reject(override_id):
    """Reject a forecast override."""
    db = get_db()

    review_notes = request.form.get('review_notes', '')

    from planning_models import reject_override

    reject_override(db, override_id, session.get('user_id'), review_notes)

    flash('Override rejected.', 'warning')
    return redirect(url_for('scm.demand_overrides_list'))


# ============================================================
# ENTERPRISE DEMAND PLANNING: DEMAND DRIVERS & CAUSAL FACTORS
# ============================================================

@scm_bp.route('/demand/drivers')
@scm_permission_required('scm', 'demand')
def demand_drivers():
    """Demand drivers and causal factors management."""
    db = get_db()

    drivers = db.execute("""
        SELECT d.*, i.item_code, i.name as item_name
        FROM planning_demand_drivers d
        LEFT JOIN wms_items i ON d.item_id = i.id
        ORDER BY d.start_date DESC
        LIMIT 50
    """).fetchall()

    promotions = db.execute("""
        SELECT * FROM planning_promotion_impact
        ORDER BY start_date DESC
        LIMIT 50
    """).fetchall()

    holidays = db.execute("""
        SELECT * FROM planning_holiday_calendar
        WHERE holiday_date >= DATE('now')
        ORDER BY holiday_date
        LIMIT 30
    """).fetchall()

    return render_template('scm/demand/demand_drivers.html',
        title='Demand Drivers',
        drivers=drivers,
        promotions=promotions,
        holidays=holidays
    )


@scm_bp.route('/demand/drivers/create', methods=['POST'])
@scm_permission_required('scm', 'demand')
def demand_drivers_create():
    """Create a new demand driver."""
    db = get_db()

    driver_name = request.form.get('driver_name')
    driver_type = request.form.get('driver_type')
    impact_factor = float(request.form.get('impact_factor', 1.0))
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    description = request.form.get('description')

    from planning_models import create_demand_driver

    create_demand_driver(
        db, driver_name, driver_type, impact_factor,
        start_date, end_date,
        created_by=session.get('user_id'),
        description=description
    )

    flash('Demand driver created.', 'success')
    return redirect(url_for('scm.demand_drivers'))


@scm_bp.route('/demand/promotions')
@scm_permission_required('scm', 'demand')
def demand_promotions():
    """Promotion impact management."""
    db = get_db()

    promotions = db.execute("""
        SELECT p.*, i.item_code, i.name as item_name
        FROM planning_promotion_impact p
        LEFT JOIN wms_items i ON p.item_id = i.id
        ORDER BY p.start_date DESC
    """).fetchall()

    return render_template('scm/demand/promotions.html',
        title='Promotion Impact',
        promotions=promotions
    )


@scm_bp.route('/demand/promotions/create', methods=['POST'])
@scm_permission_required('scm', 'demand')
def demand_promotions_create():
    """Create a new promotion record."""
    db = get_db()

    promotion_name = request.form.get('promotion_name')
    promotion_type = request.form.get('promotion_type')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    expected_uplift = float(request.form.get('expected_uplift_percent', 0))
    budget = float(request.form.get('budget_allocated', 0))

    from planning_models import create_promotion_record

    create_promotion_record(
        db, promotion_name, promotion_type, start_date, end_date,
        expected_uplift_percent=expected_uplift,
        budget_allocated=budget,
        created_by=session.get('user_id')
    )

    flash('Promotion record created.', 'success')
    return redirect(url_for('scm.demand_promotions'))


# ============================================================
# ENTERPRISE DEMAND PLANNING: CONSENSUS PLANNING
# ============================================================

@scm_bp.route('/demand/consensus')
@scm_permission_required('scm', 'demand')
def demand_consensus():
    """Consensus planning - collaborative forecast input."""
    db = get_db()

    consensus_items = db.execute("""
        SELECT c.*, i.item_code, i.name as item_name
        FROM planning_consensus_forecasts c
        JOIN wms_items i ON c.item_id = i.id
        ORDER BY c.created_at DESC
        LIMIT 50
    """).fetchall()

    return render_template('scm/demand/consensus_planning.html',
        title='Consensus Planning',
        consensus_items=consensus_items
    )


@scm_bp.route('/demand/consensus/input', methods=['POST'])
@scm_permission_required('scm', 'demand')
def demand_consensus_input():
    """Submit consensus forecast input (sales, planner, marketing)."""
    db = get_db()

    item_id = request.form.get('item_id', type=int)
    period_start = request.form.get('period_start')
    version_id = request.form.get('version_id', type=int)

    sales_input = request.form.get('sales_input', type=float)
    planner_input = request.form.get('planner_input', type=float)
    marketing_input = request.form.get('marketing_input', type=float)

    from planning_models import create_consensus_forecast

    create_consensus_forecast(
        db, version_id, item_id, period_start,
        sales_input=sales_input,
        planner_input=planner_input,
        marketing_input=marketing_input,
        created_by=session.get('user_id')
    )

    flash('Consensus input recorded.', 'success')
    return redirect(url_for('scm.demand_consensus'))


@scm_bp.route('/demand/consensus/<int:consensus_id>/resolve', methods=['POST'])
@scm_permission_required('scm', 'demand')
def demand_consensus_resolve(consensus_id):
    """Resolve consensus disagreement with final value."""
    db = get_db()

    final_value = float(request.form.get('final_value', 0))

    from planning_models import resolve_consensus_disagreement

    resolve_consensus_disagreement(db, consensus_id, final_value, session.get('user_id'))

    flash('Consensus disagreement resolved.', 'success')
    return redirect(url_for('scm.demand_consensus'))


# ============================================================
# ENTERPRISE DEMAND PLANNING: ACCURACY & BIAS ANALYTICS
# ============================================================

@scm_bp.route('/demand/accuracy/dashboard')
@scm_permission_required('scm', 'demand')
def demand_accuracy_dashboard():
    """Forecast accuracy dashboard with comprehensive metrics."""
    db = get_db()

    # Overall accuracy metrics
    accuracy_summary = db.execute("""
        SELECT
            COUNT(DISTINCT item_id) as items_measured,
            AVG(mape) as avg_mape,
            AVG(bias) as avg_bias,
            SUM(CASE WHEN bias > 0 THEN 1 ELSE 0 END) as over_forecast_count,
            SUM(CASE WHEN bias < 0 THEN 1 ELSE 0 END) as under_forecast_count
        FROM planning_forecast_accuracy
        WHERE mape IS NOT NULL
    """).fetchone()

    # High error items
    high_error_items = db.execute("""
        SELECT fa.*, i.item_code, i.name as item_name
        FROM planning_forecast_accuracy fa
        JOIN wms_items i ON fa.item_id = i.id
        WHERE fa.mape > 20
        ORDER BY fa.mape DESC
        LIMIT 20
    """).fetchall()

    # Bias by planner
    bias_by_planner = db.execute("""
        SELECT u.username, AVG(fb.bias_percent) as avg_bias
        FROM planning_forecast_bias fb
        JOIN users u ON fb.planner_id = u.id
        GROUP BY fb.planner_id
        ORDER BY avg_bias DESC
    """).fetchall()

    # Accuracy trend
    accuracy_trend = db.execute("""
        SELECT
            DATE(calculated_at) as date,
            AVG(mape) as daily_mape
        FROM planning_forecast_accuracy
        WHERE calculated_at >= DATE('now', '-30 days')
        GROUP BY DATE(calculated_at)
        ORDER BY date
    """).fetchall()

    return render_template('scm/demand/accuracy_dashboard.html',
        title='Forecast Accuracy Dashboard',
        accuracy_summary=accuracy_summary,
        high_error_items=high_error_items,
        bias_by_planner=bias_by_planner,
        accuracy_trend=accuracy_trend
    )


@scm_bp.route('/demand/accuracy/by-item/<int:item_id>')
@scm_permission_required('scm', 'demand')
def demand_accuracy_by_item(item_id):
    """Forecast accuracy for a specific item."""
    db = get_db()

    item = db.execute("SELECT * FROM wms_items WHERE id = ?", (item_id,)).fetchone()

    accuracy_records = db.execute("""
        SELECT * FROM planning_forecast_accuracy
        WHERE item_id = ?
        ORDER BY period_start DESC
        LIMIT 50
    """, (item_id,)).fetchall()

    bias_records = db.execute("""
        SELECT * FROM planning_forecast_bias
        WHERE item_id = ?
        ORDER BY period_start DESC
        LIMIT 50
    """, (item_id,)).fetchone()

    return render_template('scm/demand/accuracy_by_item.html',
        title=f'Accuracy: {item["item_code"] if item else "Item"}',
        item=item,
        accuracy_records=accuracy_records,
        bias_records=bias_records
    )


@scm_bp.route('/demand/accuracy/calculate', methods=['POST'])
@scm_permission_required('scm', 'demand')
def demand_calculate_accuracy():
    """Calculate forecast accuracy for items."""
    db = get_db()

    item_ids = request.form.getlist('item_ids')

    from planning_models import calculate_item_forecast_accuracy

    for item_id in item_ids:
        calculate_item_forecast_accuracy(db, int(item_id))

    flash(f'Accuracy calculated for {len(item_ids)} items.', 'success')
    return redirect(url_for('scm.demand_accuracy_dashboard'))


# ============================================================
# ENTERPRISE DEMAND PLANNING: DEMAND SENSING SCAFFOLD
# ============================================================

@scm_bp.route('/demand/sensing')
@scm_permission_required('scm', 'demand')
def demand_sensing():
    """Demand sensing - short-term demand signals and anomalies."""
    db = get_db()

    signals = db.execute("""
        SELECT s.*, i.item_code, i.name as item_name
        FROM planning_demand_signals s
        LEFT JOIN wms_items i ON s.item_id = i.id
        ORDER BY s.signal_date DESC
        LIMIT 50
    """).fetchall()

    volatility_alerts = db.execute("""
        SELECT va.*, i.item_code, i.name as item_name
        FROM planning_volatility_alerts va
        LEFT JOIN wms_items i ON va.item_id = i.id
        WHERE va.is_acknowledged = 0
        ORDER BY va.severity DESC, va.created_at DESC
        LIMIT 30
    """).fetchall()

    return render_template('scm/demand/demand_sensing.html',
        title='Demand Sensing',
        signals=signals,
        volatility_alerts=volatility_alerts
    )


@scm_bp.route('/demand/sensing/detect', methods=['POST'])
@scm_permission_required('scm', 'demand')
def demand_sensing_detect():
    """Run demand volatility detection."""
    db = get_db()

    item_ids = request.form.getlist('item_ids')

    from planning_models import detect_demand_volatility, detect_demand_spike_or_drop

    detected_count = 0
    for item_id in item_ids:
        result1 = detect_demand_volatility(db, int(item_id))
        result2 = detect_demand_spike_or_drop(db, int(item_id))
        if result1 or result2:
            detected_count += 1

    flash(f'Detection complete. {detected_count} items flagged.', 'success')
    return redirect(url_for('scm.demand_sensing'))


@scm_bp.route('/demand/sensing/volatility/<int:alert_id>/acknowledge', methods=['POST'])
@scm_permission_required('scm', 'demand')
def demand_sensing_acknowledge(alert_id):
    """Acknowledge a volatility alert."""
    db = get_db()

    resolution_notes = request.form.get('resolution_notes', '')

    db.execute("""
        UPDATE planning_volatility_alerts
        SET is_acknowledged = 1,
            acknowledged_by = ?,
            acknowledged_at = CURRENT_TIMESTAMP,
            resolution_notes = ?
        WHERE id = ?
    """, (session.get('user_id'), resolution_notes, alert_id))

    db.commit()

    flash('Alert acknowledged.', 'success')
    return redirect(url_for('scm.demand_sensing'))


# ============================================================
# ENTERPRISE DEMAND PLANNING: SCENARIO PLANNING
# ============================================================

@scm_bp.route('/demand/scenarios')
@scm_permission_required('scm', 'scenarios')
def demand_scenarios():
    """Scenario planning - what-if analysis."""
    db = get_db()

    scenarios = db.execute("""
        SELECT s.*, u.username as created_by_name
        FROM planning_scenarios s
        LEFT JOIN users u ON s.created_by = u.id
        WHERE s.is_active = 1
        ORDER BY s.created_at DESC
    """).fetchall()

    return render_template('scm/demand/scenarios.html',
        title='Scenario Planning',
        scenarios=scenarios
    )


@scm_bp.route('/demand/scenarios/create', methods=['POST'])
@scm_permission_required('scm', 'scenarios')
def demand_scenarios_create():
    """Create a new planning scenario."""
    db = get_db()

    scenario_name = request.form.get('scenario_name')
    scenario_type = request.form.get('scenario_type')
    description = request.form.get('description')
    uplift_percent = float(request.form.get('uplift_percent', 0))
    demand_shift = float(request.form.get('demand_shift', 0))

    params = {
        'uplift_percent': uplift_percent,
        'demand_shift': demand_shift
    }

    from planning_models import create_scenario_from_forecast

    scenario_id = create_scenario_from_forecast(
        db, scenario_name, scenario_type,
        parameters=params,
        created_by=session.get('user_id'),
        description=description
    )

    flash(f'Scenario "{scenario_name}" created.', 'success')
    return redirect(url_for('scm.demand_scenarios_detail', scenario_id=scenario_id))


@scm_bp.route('/demand/scenarios/<int:scenario_id>')
@scm_permission_required('scm', 'scenarios')
def demand_scenarios_detail(scenario_id):
    """View scenario details and impacts."""
    db = get_db()

    scenario = db.execute("SELECT * FROM planning_scenarios WHERE id = ?",
                          (scenario_id,)).fetchone()

    if not scenario:
        flash('Scenario not found.', 'error')
        return redirect(url_for('scm.demand_scenarios'))

    lines = db.execute("""
        SELECT sl.*, i.item_code, i.name as item_name
        FROM planning_scenario_lines sl
        JOIN wms_items i ON sl.item_id = i.id
        WHERE sl.scenario_id = ?
        ORDER BY ABS(sl.impact_value) DESC
        LIMIT 100
    """, (scenario_id,)).fetchall()

    return render_template('scm/demand/scenario_detail.html',
        title=f'Scenario: {scenario["name"]}',
        scenario=scenario,
        lines=lines
    )


@scm_bp.route('/demand/scenarios/<int:scenario_id>/apply', methods=['POST'])
@scm_permission_required('scm', 'scenarios')
def demand_scenarios_apply(scenario_id):
    """Apply scenario assumptions and calculate impacts."""
    db = get_db()

    from planning_models import apply_scenario_assumptions

    apply_scenario_assumptions(db, scenario_id)

    flash('Scenario assumptions applied.', 'success')
    return redirect(url_for('scm.demand_scenarios_detail', scenario_id=scenario_id))


@scm_bp.route('/demand/scenarios/compare')
@scm_permission_required('scm', 'scenarios')
def demand_scenarios_compare():
    """Compare multiple scenarios."""
    db = get_db()

    scenario_ids = request.args.getlist('scenario_ids', type=int)

    if len(scenario_ids) < 2:
        scenarios = db.execute("SELECT * FROM planning_scenarios WHERE is_active = 1").fetchall()
        return render_template('scm/demand/scenarios_compare_select.html',
            title='Compare Scenarios',
            scenarios=scenarios
        )

    comparison_data = []
    for sid in scenario_ids:
        scenario = db.execute("SELECT * FROM planning_scenarios WHERE id = ?", (sid,)).fetchone()
        summary = db.execute("""
            SELECT
                SUM(base_value) as total_base,
                SUM(scenario_value) as total_scenario,
                SUM(impact_value) as total_impact,
                AVG(impact_percent) as avg_impact_pct
            FROM planning_scenario_lines
            WHERE scenario_id = ?
        """, (sid,)).fetchone()

        comparison_data.append({
            'scenario': scenario,
            'summary': summary
        })

    return render_template('scm/demand/scenarios_compare.html',
        title='Scenario Comparison',
        comparison_data=comparison_data
    )


# ============================================================
# ENTERPRISE DEMAND PLANNING: EXCEPTIONS & ALERTS
# ============================================================

@scm_bp.route('/demand/exceptions')
@scm_permission_required('scm', 'alerts')
def demand_exceptions():
    """Demand planning exceptions and alerts queue."""
    db = get_db()

    exception_types = {
        'FORECAST_DEVIATION': db.execute("""
            SELECT COUNT(*) as cnt FROM planning_alerts
            WHERE alert_type = 'FORECAST_DEVIATION' AND is_acknowledged = 0
        """).fetchone()['cnt'],
        'ACCURACY_BREACH': db.execute("""
            SELECT COUNT(*) as cnt FROM planning_volatility_alerts
            WHERE alert_type = 'HIGH_VOLATILITY' AND is_acknowledged = 0
        """).fetchone()['cnt'],
        'HIGH_BIAS': db.execute("""
            SELECT COUNT(*) as cnt FROM planning_forecast_bias
            WHERE ABS(bias_percent) > 20 AND bias_percent IS NOT NULL
        """).fetchone()['cnt'],
        'PENDING_OVERRIDES': db.execute("""
            SELECT COUNT(*) as cnt FROM planning_forecast_overrides
            WHERE status = 'PENDING'
        """).fetchone()['cnt'],
        'PENDING_CONSENSUS': db.execute("""
            SELECT COUNT(*) as cnt FROM planning_consensus_forecasts
            WHERE status = 'DRAFT' AND disagreement_level != 'LOW'
        """).fetchone()['cnt'],
    }

    all_exceptions = db.execute("""
        SELECT 'ALERT' as source, id, alert_type, severity, title, message,
               item_id, created_at, is_acknowledged
        FROM planning_alerts
        WHERE is_acknowledged = 0
        UNION ALL
        SELECT 'VOLATILITY' as source, id, alert_type, severity,
               alert_type || ' Alert' as title,
               'Volatility alert for item' as message,
               item_id, created_at, is_acknowledged
        FROM planning_volatility_alerts
        WHERE is_acknowledged = 0
        ORDER BY created_at DESC
        LIMIT 50
    """).fetchall()

    return render_template('scm/demand/exceptions.html',
        title='Demand Exceptions',
        exception_types=exception_types,
        all_exceptions=all_exceptions
    )


@scm_bp.route('/demand/exceptions/escalate', methods=['POST'])
@scm_permission_required('scm', 'alerts')
def demand_exceptions_escalate():
    """Escalate an exception to management."""
    db = get_db()

    exception_id = request.form.get('exception_id', type=int)
    exception_type = request.form.get('exception_type')
    notes = request.form.get('escalation_notes', '')

    from planning_models import create_flow_notification

    create_flow_notification(
        db,
        f'EXCEPTION_ESCALATION_{exception_type}',
        f'Escalated: {exception_type}',
        notes,
        entity_type='exception',
        entity_id=exception_id,
        priority='HIGH',
        created_by=session.get('user_id')
    )

    flash('Exception escalated.', 'warning')
    return redirect(url_for('scm.demand_exceptions'))


# ============================================================
# ENTERPRISE DEMAND PLANNING: SCM LINKAGE
# ============================================================

@scm_bp.route('/demand/scm-linkage')
@scm_permission_required('scm', 'demand')
def demand_scm_linkage():
    """Forecast impact on SCM and replenishment."""
    db = get_db()

    # Forecast impact summary
    forecast_impact = db.execute("""
        SELECT
            SUM(fl.final_quantity) as total_forecast_demand,
            COUNT(DISTINCT fl.item_id) as items_forecasted,
            SUM(pr.recommended_quantity) as total_replen_rec,
            SUM(pp.recommended_quantity) as total_purchase_rec
        FROM planning_forecast_lines fl
        LEFT JOIN planning_replenishment_recommendations pr ON fl.item_id = pr.item_id
        LEFT JOIN planning_purchase_recommendations pp ON fl.item_id = pp.item_id
        WHERE fl.period_start BETWEEN DATE('now') AND DATE('now', '+30 days')
    """).fetchone()

    # Items at replenishment risk
    replen_risk = db.execute("""
        SELECT i.item_code, i.name, pr.*
        FROM planning_replenishment_recommendations pr
        JOIN wms_items i ON pr.item_id = i.id
        WHERE pr.status = 'OPEN' AND pr.priority > 70
        ORDER BY pr.priority DESC
        LIMIT 20
    """).fetchall()

    return render_template('scm/demand/scm_linkage.html',
        title='SCM Linkage',
        forecast_impact=forecast_impact,
        replen_risk=replen_risk
    )


# ============================================================
# ENTERPRISE DEMAND PLANNING: SALES/MARKETING LINKAGE
# ============================================================

@scm_bp.route('/demand/sales-linkage')
@scm_permission_required('scm', 'demand')
def demand_sales_linkage():
    """Demand forecast linkage to sales and marketing."""
    db = get_db()

    # Sales trends
    sales_trends = db.execute("""
        SELECT
            DATE(invoice_date) as date,
            SUM(quantity) as total_qty,
            SUM(total_value) as total_value
        FROM planning_sales_history
        WHERE invoice_date >= DATE('now', '-30 days')
        GROUP BY DATE(invoice_date)
        ORDER BY date
    """).fetchall()

    # Campaign impact
    campaign_impact = db.execute("""
        SELECT p.*,
               COALESCE(SUM(dh.sales_quantity), 0) as uplift_demand
        FROM planning_promotion_impact p
        LEFT JOIN planning_demand_history dh
            ON p.item_id = dh.item_id
            AND dh.period_start BETWEEN p.start_date AND p.end_date
        GROUP BY p.id
        ORDER BY p.start_date DESC
    """).fetchall()

    return render_template('scm/demand/sales_linkage.html',
        title='Sales & Marketing Linkage',
        sales_trends=sales_trends,
        campaign_impact=campaign_impact
    )


# ============================================================
# ENTERPRISE DEMAND PLANNING: WORKFLOW & APPROVALS
# ============================================================

@scm_bp.route('/demand/approvals')
@scm_permission_required('scm', 'workflow')
def demand_approvals():
    """Forecast approval queue."""
    db = get_db()

    pending_approvals = db.execute("""
        SELECT oa.*, o.item_id, o.override_quantity, o.override_reason,
               i.item_code, i.name as item_name,
               u.username as requested_by_name
        FROM planning_override_approvals oa
        JOIN planning_forecast_overrides o ON oa.override_id = o.id
        JOIN wms_items i ON o.item_id = i.id
        JOIN users u ON oa.requested_by = u.id
        WHERE oa.approval_status = 'PENDING'
        ORDER BY oa.requested_at DESC
    """).fetchall()

    return render_template('scm/demand/approvals.html',
        title='Forecast Approvals',
        pending_approvals=pending_approvals
    )


# ============================================================
# ENTERPRISE DEMAND PLANNING: SETTINGS
# ============================================================

@scm_bp.route('/demand/settings')
@scm_permission_required('scm', 'settings')
def demand_settings():
    """Demand planning settings."""
    db = get_db()

    settings = db.execute("SELECT * FROM planning_settings WHERE is_active = 1").fetchall()

    settings_dict = {s['setting_key']: s['setting_value'] for s in settings}

    return render_template('scm/demand/settings.html',
        title='Demand Planning Settings',
        settings=settings_dict
    )


@scm_bp.route('/demand/settings/update', methods=['POST'])
@scm_permission_required('scm', 'settings')
def demand_settings_update():
    """Update demand planning settings."""
    db = get_db()

    setting_key = request.form.get('setting_key')
    setting_value = request.form.get('setting_value')

    from planning_models import save_planning_setting

    save_planning_setting(db, setting_key, setting_value)

    flash('Setting updated.', 'success')
    return redirect(url_for('scm.demand_settings'))


@scm_bp.route('/demand/settings/forecast-rules')
@scm_permission_required('scm', 'settings')
def demand_settings_forecast_rules():
    """Forecast method and model settings."""
    db = get_db()

    policies = db.execute("SELECT * FROM planning_policies WHERE is_active = 1").fetchall()

    item_profiles = db.execute("""
        SELECT ip.*, i.item_code, i.name as item_name
        FROM planning_item_profiles ip
        JOIN wms_items i ON ip.item_id = i.id
        LIMIT 50
    """).fetchall()

    return render_template('scm/demand/settings_forecast_rules.html',
        title='Forecast Rules',
        policies=policies,
        item_profiles=item_profiles
    )


@scm_bp.route('/demand/settings/accuracy')
@scm_permission_required('scm', 'settings')
def demand_settings_accuracy():
    """Accuracy calculation settings."""
    db = get_db()

    return render_template('scm/demand/settings_accuracy.html',
        title='Accuracy Settings'
    )


# ============================================================
# SUPPLY PLANNING
# ============================================================

@scm_bp.route('/supply')
@scm_permission_required('scm', 'supply')
def supply_planning():
    """Supply Planning main page."""
    db = get_db()
    
    # Incoming supply
    incoming_supply = db.execute("""
        SELECT ir.*, i.item_code, i.name as item_name,
               s.name as supplier_name
        FROM wms_inbound_receipts ir
        JOIN wms_items i ON ir.item_id = i.id
        LEFT JOIN suppliers s ON ir.supplier_id = s.id
        WHERE ir.status IN ('APPROVED', 'SENT', 'IN_TRANSIT')
        ORDER BY ir.expected_arrival_date
        LIMIT 20
    """).fetchall()
    
    # Open PO summary
    open_po_count = db.execute("""
        SELECT COUNT(*) as cnt FROM wms_inbound_receipts
        WHERE status IN ('APPROVED', 'SENT', 'IN_TRANSIT')
    """).fetchone()['cnt']
    
    open_po_value = db.execute("""
        SELECT COALESCE(SUM(ir.quantity * COALESCE(i.unit_cost, 0)), 0) as total
        FROM wms_inbound_receipts ir
        JOIN wms_items i ON ir.item_id = i.id
        WHERE ir.status IN ('APPROVED', 'SENT', 'IN_TRANSIT')
    """).fetchone()['total']
    
    # Supply by warehouse
    supply_by_warehouse = db.execute("""
        SELECT w.id, w.name,
               COALESCE(SUM(ib.quantity), 0) as current_stock,
               COALESCE((SELECT SUM(quantity - COALESCE(received_quantity, 0))
                        FROM wms_inbound_receipts
                        WHERE warehouse_id = w.id AND status IN ('APPROVED', 'SENT', 'IN_TRANSIT')), 0) as in_transit
        FROM wms_warehouses w
        LEFT JOIN wms_inventory_balances ib ON w.id = ib.warehouse_id
        WHERE w.is_active = 1
        GROUP BY w.id
    """).fetchall()
    
    return render_template('scm/supply/index.html',
        title='Supply Planning',
        incoming_supply=incoming_supply,
        open_po_count=open_po_count,
        open_po_value=open_po_value,
        supply_by_warehouse=supply_by_warehouse
    )


@scm_bp.route('/supply/pipeline')
@scm_permission_required('scm', 'supply')
def supply_pipeline():
    """Incoming supply pipeline view."""
    db = get_db()
    
    pipeline = db.execute("""
        SELECT ir.*, i.item_code, i.name as item_name,
               s.name as supplier_name,
               w.name as warehouse_name
        FROM wms_inbound_receipts ir
        JOIN wms_items i ON ir.item_id = i.id
        LEFT JOIN suppliers s ON ir.supplier_id = s.id
        LEFT JOIN wms_warehouses w ON ir.warehouse_id = w.id
        WHERE ir.status IN ('APPROVED', 'SENT', 'IN_TRANSIT', 'RECEIVING')
        ORDER BY ir.expected_arrival_date
    """).fetchall()
    
    return render_template('scm/supply/pipeline.html',
        title='Supply Pipeline',
        pipeline=pipeline
    )


@scm_bp.route('/supply/risks')
@scm_permission_required('scm', 'supply')
def supply_risks():
    """Open supply risks and delays."""
    db = get_db()
    
    # Delayed receipts
    delayed_receipts = db.execute("""
        SELECT ir.*, i.item_code, i.name as item_name,
               s.name as supplier_name,
               w.name as warehouse_name
        FROM wms_inbound_receipts ir
        JOIN wms_items i ON ir.item_id = i.id
        LEFT JOIN suppliers s ON ir.supplier_id = s.id
        LEFT JOIN wms_warehouses w ON ir.warehouse_id = w.id
        WHERE ir.status IN ('APPROVED', 'SENT', 'IN_TRANSIT')
        AND ir.expected_arrival_date < DATE('now')
        ORDER BY ir.expected_arrival_date
    """).fetchall()
    
    # Items with supply shortage
    shortage_items = db.execute("""
        SELECT i.item_code, i.name,
               COALESCE(ib.quantity, 0) as current_stock,
               COALESCE((SELECT SUM(quantity - COALESCE(received_quantity, 0))
                        FROM wms_inbound_receipts
                        WHERE item_id = i.id AND status IN ('APPROVED', 'SENT', 'IN_TRANSIT')), 0) as incoming,
               COALESCE((SELECT AVG(sales_quantity + consumption_quantity) / 30
                        FROM planning_demand_history
                        WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')), 0) as daily_demand
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        WHERE i.is_active = 1
        HAVING (current_stock + incoming) < daily_demand * 7
        ORDER BY (daily_demand * 7 - current_stock - incoming) DESC
        LIMIT 20
    """).fetchall()
    
    return render_template('scm/supply/risks.html',
        title='Supply Risks',
        delayed_receipts=delayed_receipts,
        shortage_items=shortage_items
    )


@scm_bp.route('/supply/constraints')
@scm_permission_required('scm', 'supply')
def supply_constraints():
    """Supply constraints analysis."""
    db = get_db()
    
    # Items with constraints (long lead time, MOQ, etc.)
    constrained_items = db.execute("""
        SELECT i.item_code, i.name,
               ip.lead_time_days, ip.min_order_quantity, ip.order_multiple,
               COALESCE(ib.quantity, 0) as current_stock
        FROM wms_items i
        LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        WHERE i.is_active = 1
        AND (ip.lead_time_days > 14 OR ip.min_order_quantity > 100)
        ORDER BY ip.lead_time_days DESC
        LIMIT 30
    """).fetchall()
    
    return render_template('scm/supply/constraints.html',
        title='Supply Constraints',
        constrained_items=constrained_items
    )


@scm_bp.route('/supply/coverage')
@scm_permission_required('scm', 'supply')
def supply_coverage():
    """Coverage analysis - days of supply by item."""
    db = get_db()
    
    coverage_data = db.execute("""
        SELECT i.item_code, i.name,
               COALESCE(ib.quantity, 0) as current_stock,
               COALESCE((SELECT SUM(quantity - COALESCE(received_quantity, 0))
                        FROM wms_inbound_receipts
                        WHERE item_id = i.id AND status IN ('APPROVED', 'SENT', 'IN_TRANSIT')), 0) as in_transit,
               COALESCE((SELECT AVG(sales_quantity + consumption_quantity) / 30
                        FROM planning_demand_history
                        WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')), 0) as daily_demand,
               COALESCE(ip.safety_stock_days, 7) as safety_days
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
        WHERE i.is_active = 1
        ORDER BY current_stock / NULLIF(daily_demand, 0) ASC
        LIMIT 50
    """).fetchall()
    
    return render_template('scm/supply/coverage.html',
        title='Coverage Analysis',
        coverage_data=coverage_data
    )


@scm_bp.route('/supply/reports')
@scm_permission_required('scm', 'reports')
def supply_reports():
    """Supply planning reports."""
    return render_template('scm/supply/reports.html',
        title='Supply Reports'
    )


# ============================================================
# REPLENISHMENT
# ============================================================

@scm_bp.route('/replenishment')
@scm_permission_required('scm', 'replenishment')
def replenishment_planning():
    """Main replenishment planning page."""
    db = get_db()
    
    recommendations = db.execute("""
        SELECT r.*, i.item_code, i.name as item_name,
               s.name as supplier_name,
               u.username as created_by
        FROM planning_replenishment_recommendations r
        JOIN wms_items i ON r.item_id = i.id
        LEFT JOIN suppliers s ON r.suggested_supplier_id = s.id
        LEFT JOIN users u ON r.created_by = u.id
        ORDER BY r.priority DESC, r.created_at DESC
        LIMIT 50
    """).fetchall()
    
    status_filter = request.args.get('status', 'OPEN')
    
    if status_filter != 'ALL':
        recommendations = [r for r in recommendations if r['status'] == status_filter]
    
    # Summary stats
    open_count = db.execute("SELECT COUNT(*) as cnt FROM planning_replenishment_recommendations WHERE status = 'OPEN'").fetchone()['cnt']
    approved_count = db.execute("SELECT COUNT(*) as cnt FROM planning_replenishment_recommendations WHERE status = 'APPROVED'").fetchone()['cnt']
    
    return render_template('scm/replenishment/index.html',
        title='Replenishment Planning',
        recommendations=recommendations,
        status_filter=status_filter,
        open_count=open_count,
        approved_count=approved_count
    )


@scm_bp.route('/replenishment/queue')
@scm_permission_required('scm', 'replenishment')
def replenishment_queue():
    """Replenishment approval queue."""
    db = get_db()
    
    queue = db.execute("""
        SELECT r.*, i.item_code, i.name as item_name,
               COALESCE(ib.quantity, 0) as current_stock
        FROM planning_replenishment_recommendations r
        JOIN wms_items i ON r.item_id = i.id
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        WHERE r.status = 'OPEN'
        ORDER BY r.priority DESC, r.created_at DESC
    """).fetchall()
    
    return render_template('scm/replenishment/queue.html',
        title='Replenishment Queue',
        queue=queue
    )


@scm_bp.route('/replenishment/generate', methods=['POST'])
@scm_permission_required('scm', 'replenishment')
def replenishment_generate():
    """Generate replenishment recommendations."""
    db = get_db()
    settings = get_scm_settings(db)
    
    # Clear existing OPEN recommendations
    db.execute("DELETE FROM planning_replenishment_recommendations WHERE status = 'OPEN'")
    
    # Get items that need replenishment
    items = db.execute("""
        SELECT i.id as item_id, i.item_code, i.name,
               COALESCE(ib.quantity, 0) as current_stock,
               COALESCE((SELECT AVG(sales_quantity + consumption_quantity) / 30
                        FROM planning_demand_history
                        WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')), 0) as daily_demand,
               ip.lead_time_days, ip.safety_stock_days, ip.min_order_quantity,
               ip.reorder_point_days, ip.max_order_quantity,
               (SELECT s.id FROM wms_item_suppliers wis JOIN suppliers s ON wis.supplier_id = s.id 
                WHERE wis.item_id = i.id ORDER BY s.priority LIMIT 1) as supplier_id
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
        WHERE i.is_active = 1
        AND COALESCE(ib.quantity, 0) < COALESCE(ip.reorder_point_days, 5) * COALESCE(
            (SELECT AVG(sales_quantity + consumption_quantity) / 30
             FROM planning_demand_history
             WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')), 10)
    """).fetchall()
    
    for item in items:
        if item['daily_demand'] <= 0:
            continue
        
        safety_stock = item['safety_stock_days'] or 7
        reorder_point = item['reorder_point_days'] or 3
        lead_time = item['lead_time_days'] or 7
        
        # Calculate recommended quantity
        target_stock = item['daily_demand'] * (safety_stock + lead_time + reorder_point)
        recommended_qty = max(target_stock - item['current_stock'], item['min_order_quantity'] or 0)
        
        if recommended_qty <= 0:
            continue
        
        # Priority calculation
        coverage_days = item['current_stock'] / item['daily_demand'] if item['daily_demand'] > 0 else 999
        if coverage_days < safety_stock:
            priority = 100
        elif coverage_days < safety_stock + lead_time:
            priority = 80
        elif coverage_days < 14:
            priority = 60
        else:
            priority = 40
        
        suggested_date = (datetime.now() + timedelta(days=lead_time)).strftime('%Y-%m-%d')
        
        db.execute("""
            INSERT INTO planning_replenishment_recommendations
            (item_id, warehouse_id, recommendation_type, action, priority,
             current_stock, forecasted_demand, recommended_quantity,
             recommended_date, suggested_supplier_id, status, created_by)
            VALUES (?, ?, 'STOCK_REPLENISHMENT', 'PURCHASE', ?, ?, ?, ?, ?, ?, 'OPEN', ?)
        """, (item['item_id'], None, priority, item['current_stock'],
              item['daily_demand'] * 30, recommended_qty, suggested_date,
              item['supplier_id'], session.get('user_id')))
    
    db.commit()
    
    log_scm_audit(db, 'REPLENISHMENT_GENERATED', 'batch', None,
                   user_id=session.get('user_id'))
    
    flash('Replenishment recommendations generated.', 'success')
    return redirect(url_for('scm.replenishment_planning'))


@scm_bp.route('/replenishment/<int:rec_id>/approve', methods=['POST'])
@scm_permission_required('scm', 'replenishment')
def replenishment_approve(rec_id):
    """Approve a replenishment recommendation."""
    db = get_db()
    
    db.execute("""
        UPDATE planning_replenishment_recommendations
        SET status = 'APPROVED', approved_by = ?, approved_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (session.get('user_id'), rec_id))
    db.commit()
    
    log_scm_audit(db, 'REPLENISHMENT_APPROVED', 'replenishment', rec_id,
                   user_id=session.get('user_id'))
    
    flash('Replenishment approved.', 'success')
    return redirect(url_for('scm.replenishment_planning'))


@scm_bp.route('/replenishment/<int:rec_id>/dismiss', methods=['POST'])
@scm_permission_required('scm', 'replenishment')
def replenishment_dismiss(rec_id):
    """Dismiss a replenishment recommendation."""
    db = get_db()
    
    db.execute("""
        UPDATE planning_replenishment_recommendations
        SET status = 'DISMISSED', reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (session.get('user_id'), rec_id))
    db.commit()
    
    log_scm_audit(db, 'REPLENISHMENT_DISMISSED', 'replenishment', rec_id,
                   user_id=session.get('user_id'))
    
    flash('Replenishment dismissed.', 'info')
    return redirect(url_for('scm.replenishment_planning'))


@scm_bp.route('/replenishment/min-max')
@scm_permission_required('scm', 'replenishment')
def replenishment_min_max():
    """Min/Max planning rules."""
    db = get_db()
    
    min_max_rules = db.execute("""
        SELECT ip.*, i.item_code, i.name as item_name
        FROM planning_item_profiles ip
        JOIN wms_items i ON ip.item_id = i.id
        WHERE i.is_active = 1
        ORDER BY i.item_code
        LIMIT 50
    """).fetchall()
    
    return render_template('scm/replenishment/min_max.html',
        title='Min/Max Planning',
        min_max_rules=min_max_rules
    )


@scm_bp.route('/replenishment/safety-stock')
@scm_permission_required('scm', 'replenishment')
def replenishment_safety_stock():
    """Safety stock rules configuration."""
    db = get_db()
    
    safety_rules = db.execute("""
        SELECT ip.*, i.item_code, i.name as item_name
        FROM planning_item_profiles ip
        JOIN wms_items i ON ip.item_id = i.id
        WHERE i.is_active = 1
        ORDER BY i.item_code
        LIMIT 50
    """).fetchall()
    
    return render_template('scm/replenishment/safety_stock.html',
        title='Safety Stock Rules',
        safety_rules=safety_rules
    )


@scm_bp.route('/replenishment/branch-refill')
@scm_permission_required('scm', 'replenishment')
def replenishment_branch_refill():
    """Branch refill planning."""
    db = get_db()
    
    branches = db.execute("SELECT id, name FROM companies WHERE is_active = 1").fetchall()
    
    branch_refill = []
    for branch in branches:
        stock_level = db.execute("""
            SELECT COALESCE(SUM(quantity), 0) as total
            FROM wms_inventory_balances
            WHERE company_id = ?
        """, (branch['id'],)).fetchone()['total']
        
        demand_30d = db.execute("""
            SELECT COALESCE(SUM(sales_quantity + consumption_quantity), 0) as total
            FROM planning_demand_history
            WHERE company_id = ? AND period_start >= DATE('now', '-30 days')
        """, (branch['id'],)).fetchone()['total']
        
        branch_refill.append({
            'branch': branch,
            'current_stock': stock_level,
            'demand_30d': demand_30d,
            'coverage_days': stock_level / (demand_30d / 30) if demand_30d > 0 else 999
        })
    
    return render_template('scm/replenishment/branch_refill.html',
        title='Branch Refill Planning',
        branch_refill=branch_refill
    )


@scm_bp.route('/replenishment/warehouse-refill')
@scm_permission_required('scm', 'replenishment')
def replenishment_warehouse_refill():
    """Warehouse refill planning."""
    db = get_db()
    
    warehouses = db.execute("SELECT id, name FROM wms_warehouses WHERE is_active = 1").fetchall()
    
    warehouse_refill = []
    for wh in warehouses:
        stock_level = db.execute("""
            SELECT COALESCE(SUM(quantity), 0) as total
            FROM wms_inventory_balances
            WHERE warehouse_id = ?
        """, (wh['id'],)).fetchone()['total']
        
        demand_30d = db.execute("""
            SELECT COALESCE(SUM(sales_quantity + consumption_quantity), 0) as total
            FROM planning_demand_history
            WHERE warehouse_id = ? AND period_start >= DATE('now', '-30 days')
        """, (wh['id'],)).fetchone()['total']
        
        warehouse_refill.append({
            'warehouse': wh,
            'current_stock': stock_level,
            'demand_30d': demand_30d,
            'coverage_days': stock_level / (demand_30d / 30) if demand_30d > 0 else 999
        })
    
    return render_template('scm/replenishment/warehouse_refill.html',
        title='Warehouse Refill Planning',
        warehouse_refill=warehouse_refill
    )


@scm_bp.route('/replenishment/alerts')
@scm_permission_required('scm', 'replenishment')
def replenishment_alerts():
    """Replenishment-related alerts."""
    db = get_db()
    
    alerts = db.execute("""
        SELECT a.*, i.item_code, i.name as item_name
        FROM planning_alerts a
        LEFT JOIN wms_items i ON a.item_id = i.id
        WHERE a.alert_type IN ('REORDER_POINT_BREACH', 'SAFETY_STOCK_BREACH', 'STOCKOUT')
        AND a.is_acknowledged = 0
        ORDER BY a.created_at DESC
        LIMIT 50
    """).fetchall()
    
    return render_template('scm/replenishment/alerts.html',
        title='Replenishment Alerts',
        alerts=alerts
    )


@scm_bp.route('/replenishment/approvals')
@scm_permission_required('scm', 'approvals')
def replenishment_approvals():
    """Replenishment approval workflow."""
    db = get_db()
    
    pending = db.execute("""
        SELECT r.*, i.item_code, i.name as item_name
        FROM planning_replenishment_recommendations r
        JOIN wms_items i ON r.item_id = i.id
        WHERE r.status = 'OPEN'
        ORDER BY r.priority DESC
    """).fetchall()
    
    recent_approved = db.execute("""
        SELECT r.*, i.item_code, i.name as item_name,
               u.username as approved_by_name
        FROM planning_replenishment_recommendations r
        JOIN wms_items i ON r.item_id = i.id
        LEFT JOIN users u ON r.approved_by = u.id
        WHERE r.status = 'APPROVED'
        ORDER BY r.approved_at DESC
        LIMIT 20
    """).fetchall()
    
    return render_template('scm/replenishment/approvals.html',
        title='Replenishment Approvals',
        pending=pending,
        recent_approved=recent_approved
    )


@scm_bp.route('/replenishment/reports')
@scm_permission_required('scm', 'reports')
def replenishment_reports():
    """Replenishment reports."""
    return render_template('scm/replenishment/reports.html',
        title='Replenishment Reports'
    )


# ============================================================
# MRP / PURCHASE SUGGESTIONS
# ============================================================

@scm_bp.route('/mrp')
@scm_permission_required('scm', 'mrp')
def mrp_planning():
    """MRP main page."""
    db = get_db()
    
    # MRP exceptions
    exceptions = db.execute("""
        SELECT a.*, i.item_code, i.name as item_name
        FROM planning_alerts a
        LEFT JOIN wms_items i ON a.item_id = i.id
        WHERE a.alert_type IN ('STOCKOUT', 'SHORTAGE', 'EXCESS')
        AND a.is_acknowledged = 0
        ORDER BY a.severity DESC, a.created_at DESC
        LIMIT 20
    """).fetchall()
    
    # Purchase suggestions
    purchase_suggestions = db.execute("""
        SELECT p.*, i.item_code, i.name as item_name,
               s.name as supplier_name
        FROM planning_purchase_recommendations p
        JOIN wms_items i ON p.item_id = i.id
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.status = 'OPEN'
        ORDER BY p.priority DESC
        LIMIT 20
    """).fetchall()
    
    # Reschedule suggestions
    reschedule = db.execute("""
        SELECT * FROM planning_purchase_recommendations
        WHERE status = 'OPEN' AND recommendation_type = 'RESCHEDULE'
        ORDER BY priority DESC
        LIMIT 20
    """).fetchall()
    
    return render_template('scm/mrp/index.html',
        title='MRP / Purchase Suggestions',
        exceptions=exceptions,
        purchase_suggestions=purchase_suggestions,
        reschedule=reschedule
    )


@scm_bp.route('/mrp/run', methods=['POST'])
@scm_permission_required('scm', 'mrp')
def mrp_run():
    """Run MRP calculation."""
    db = get_db()
    settings = get_scm_settings(db)
    
    horizon_days = int(request.form.get('horizon_days', 30))
    
    # Clear existing OPEN purchase recommendations
    db.execute("DELETE FROM planning_purchase_recommendations WHERE status = 'OPEN'")
    
    # Get items with net requirements
    items = db.execute("""
        SELECT i.id as item_id, i.item_code, i.name,
               COALESCE(ib.quantity, 0) as current_stock,
               COALESCE((SELECT SUM(quantity - COALESCE(received_quantity, 0))
                        FROM wms_inbound_receipts
                        WHERE item_id = i.id AND status IN ('APPROVED', 'SENT', 'IN_TRANSIT')), 0) as in_transit,
               COALESCE((SELECT AVG(sales_quantity + consumption_quantity) / 30
                        FROM planning_demand_history
                        WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')), 0) as daily_demand,
               ip.lead_time_days, ip.min_order_quantity, ip.order_multiple,
               ip.service_level_target,
               (SELECT s.id FROM wms_item_suppliers wis JOIN suppliers s ON wis.supplier_id = s.id 
                WHERE wis.item_id = i.id ORDER BY s.priority LIMIT 1) as supplier_id
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
        WHERE i.is_active = 1
    """).fetchall()
    
    for item in items:
        if item['daily_demand'] <= 0:
            continue
        
        # Calculate net requirement
        available = item['current_stock'] + item['in_transit']
        total_demand = item['daily_demand'] * horizon_days
        
        net_requirement = total_demand - available
        
        if net_requirement <= 0:
            continue
        
        # Apply MOQ and multiple
        recommended_qty = net_requirement
        if item['min_order_quantity'] and item['min_order_quantity'] > 0:
            recommended_qty = max(recommended_qty, item['min_order_quantity'])
        if item['order_multiple'] and item['order_multiple'] > 1:
            recommended_qty = ((recommended_qty / item['order_multiple']) + 1) * item['order_multiple']
        
        # Priority based on coverage
        coverage_days = available / item['daily_demand'] if item['daily_demand'] > 0 else 999
        if coverage_days < 0:
            priority = 100
        elif coverage_days < 7:
            priority = 80
        elif coverage_days < 14:
            priority = 60
        else:
            priority = 40
        
        suggested_order_date = (datetime.now() + timedelta(days=max(0, item['lead_time_days'] or 7 - coverage_days))).strftime('%Y-%m-%d')
        suggested_arrival_date = (datetime.now() + timedelta(days=item['lead_time_days'] or 7)).strftime('%Y-%m-%d')
        
        # Get estimated cost
        unit_cost = db.execute(
            "SELECT COALESCE(unit_cost, 0) as cost FROM wms_item_suppliers WHERE item_id = ? LIMIT 1",
            (item['item_id'],)
        ).fetchone()
        unit_cost = unit_cost['cost'] if unit_cost else 0
        estimated_cost = recommended_qty * unit_cost
        
        db.execute("""
            INSERT INTO planning_purchase_recommendations
            (item_id, supplier_id, recommendation_type, action, priority,
             current_stock, forecasted_demand, in_transit_quantity,
             recommended_quantity, suggested_order_date, suggested_arrival_date,
             lead_time_days, estimated_total_cost, status, created_by)
            VALUES (?, ?, 'NORMAL', 'PURCHASE', ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
        """, (item['item_id'], item['supplier_id'], priority, item['current_stock'],
              item['daily_demand'] * horizon_days, item['in_transit'],
              recommended_qty, suggested_order_date, suggested_arrival_date,
              item['lead_time_days'] or 7, estimated_cost, session.get('user_id')))
    
    db.commit()
    
    log_scm_audit(db, 'MRP_RUN', 'batch', None,
                   user_id=session.get('user_id'),
                   changes={'horizon_days': horizon_days})
    
    flash(f'MRP run completed. {len(items)} items processed.', 'success')
    return redirect(url_for('scm.mrp_planning'))


@scm_bp.route('/mrp/exceptions')
@scm_permission_required('scm', 'mrp')
def mrp_exceptions():
    """MRP exceptions view."""
    db = get_db()
    
    exceptions = db.execute("""
        SELECT a.*, i.item_code, i.name as item_name,
               ib.quantity as current_stock
        FROM planning_alerts a
        LEFT JOIN wms_items i ON a.item_id = i.id
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        WHERE a.alert_type IN ('STOCKOUT', 'SHORTAGE', 'EXCESS', 'LEAD_TIME_CHANGE')
        ORDER BY a.severity DESC, a.created_at DESC
    """).fetchall()
    
    return render_template('scm/mrp/exceptions.html',
        title='MRP Exceptions',
        exceptions=exceptions
    )


@scm_bp.route('/mrp/suggestions')
@scm_permission_required('scm', 'mrp')
def mrp_suggestions():
    """Purchase suggestions list."""
    db = get_db()
    
    status_filter = request.args.get('status', 'OPEN')
    
    query = """
        SELECT p.*, i.item_code, i.name as item_name,
               s.name as supplier_name
        FROM planning_purchase_recommendations p
        JOIN wms_items i ON p.item_id = i.id
        LEFT JOIN suppliers s ON p.supplier_id = s.id
    """
    if status_filter != 'ALL':
        query += f" WHERE p.status = '{status_filter}'"
    query += " ORDER BY p.priority DESC, p.created_at DESC"
    
    suggestions = db.execute(query).fetchall()
    
    return render_template('scm/mrp/suggestions.html',
        title='Purchase Suggestions',
        suggestions=suggestions,
        status_filter=status_filter
    )


@scm_bp.route('/mrp/suggestions/generate', methods=['POST'])
@scm_permission_required('scm', 'mrp')
def mrp_generate_suggestions():
    """Generate purchase suggestions (standalone)."""
    return redirect(url_for('scm.mrp_run'))


@scm_bp.route('/mrp/reschedule')
@scm_permission_required('scm', 'mrp')
def mrp_reschedule():
    """Reschedule suggestions."""
    db = get_db()
    
    reschedule_sugs = db.execute("""
        SELECT p.*, i.item_code, i.name as item_name,
               ir.expected_arrival_date as current_eta
        FROM planning_purchase_recommendations p
        JOIN wms_items i ON p.item_id = i.id
        LEFT JOIN wms_inbound_receipts ir ON i.id = ir.item_id AND ir.status IN ('APPROVED', 'SENT', 'IN_TRANSIT')
        WHERE p.status = 'OPEN' AND p.recommendation_type = 'RESCHEDULE'
        ORDER BY p.priority DESC
    """).fetchall()
    
    return render_template('scm/mrp/reschedule.html',
        title='Reschedule Suggestions',
        reschedule_sugs=reschedule_sugs
    )


@scm_bp.route('/mrp/shortage')
@scm_permission_required('scm', 'mrp')
def mrp_shortage():
    """Shortage proposals."""
    db = get_db()
    
    shortages = db.execute("""
        SELECT i.item_code, i.name,
               COALESCE(ib.quantity, 0) as current_stock,
               COALESCE((SELECT SUM(quantity - COALESCE(received_quantity, 0))
                        FROM wms_inbound_receipts
                        WHERE item_id = i.id AND status IN ('APPROVED', 'SENT', 'IN_TRANSIT')), 0) as incoming,
               COALESCE((SELECT AVG(sales_quantity + consumption_quantity) / 30
                        FROM planning_demand_history
                        WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')), 0) as daily_demand,
               COALESCE((SELECT AVG(sales_quantity + consumption_quantity) / 30
                        FROM planning_demand_history
                        WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')), 0) * 7 as weekly_demand
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        WHERE i.is_active = 1
        AND (COALESCE(ib.quantity, 0) + COALESCE((SELECT SUM(quantity - COALESCE(received_quantity, 0))
                                                FROM wms_inbound_receipts
                                                WHERE item_id = i.id AND status IN ('APPROVED', 'SENT', 'IN_TRANSIT')), 0))
             < COALESCE((SELECT AVG(sales_quantity + consumption_quantity) / 30
                        FROM planning_demand_history
                        WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')), 0) * 7
        ORDER BY (COALESCE((SELECT AVG(sales_quantity + consumption_quantity) / 30
                           FROM planning_demand_history
                           WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')), 0) * 7
                  - COALESCE(ib.quantity, 0) - COALESCE((SELECT SUM(quantity - COALESCE(received_quantity, 0))
                        FROM wms_inbound_receipts
                        WHERE item_id = i.id AND status IN ('APPROVED', 'SENT', 'IN_TRANSIT')), 0)) DESC
    """).fetchall()
    
    return render_template('scm/mrp/shortage.html',
        title='Shortage Proposals',
        shortages=shortages
    )


@scm_bp.route('/mrp/excess')
@scm_permission_required('scm', 'mrp')
def mrp_excess():
    """Excess stock suggestions."""
    db = get_db()
    
    excess_items = db.execute("""
        SELECT i.item_code, i.name,
               COALESCE(ib.quantity, 0) as current_stock,
               COALESCE(ip.max_order_quantity, 1000) as max_stock,
               COALESCE((SELECT AVG(sales_quantity + consumption_quantity) / 30
                        FROM planning_demand_history
                        WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')), 0) as daily_demand,
               (COALESCE(ib.quantity, 0) - COALESCE(ip.max_order_quantity, 1000)) as excess_quantity
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
        WHERE i.is_active = 1
        AND COALESCE(ib.quantity, 0) > COALESCE(ip.max_order_quantity, 1000)
        ORDER BY excess_quantity DESC
    """).fetchall()
    
    return render_template('scm/mrp/excess.html',
        title='Excess Stock Suggestions',
        excess_items=excess_items
    )


@scm_bp.route('/mrp/planner-queue')
@scm_permission_required('scm', 'mrp')
def mrp_planner_queue():
    """Planner review queue for MRP."""
    db = get_db()
    
    queue = db.execute("""
        SELECT p.*, i.item_code, i.name as item_name,
               s.name as supplier_name
        FROM planning_purchase_recommendations p
        JOIN wms_items i ON p.item_id = i.id
        LEFT JOIN suppliers s ON p.supplier_id = s.id
        WHERE p.status = 'OPEN'
        ORDER BY p.priority DESC, p.created_at DESC
    """).fetchall()
    
    return render_template('scm/mrp/planner_queue.html',
        title='Planner Review Queue',
        queue=queue
    )


@scm_bp.route('/mrp/reports')
@scm_permission_required('scm', 'reports')
def mrp_reports():
    """MRP reports."""
    return render_template('scm/mrp/reports.html',
        title='MRP Reports'
    )


# ============================================================
# INVENTORY OPTIMIZATION
# ============================================================

@scm_bp.route('/inventory-optimization')
@scm_permission_required('scm', 'inventory')
def inventory_optimization():
    """Inventory optimization main page."""
    db = get_db()
    
    # Stock health overview
    stock_health = {
        'healthy': db.execute("""
            SELECT COUNT(*) as cnt FROM wms_inventory_balances ib
            JOIN wms_items i ON ib.item_id = i.id
            LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
            WHERE i.is_active = 1 AND COALESCE(ib.quantity, 0) > 0
            AND COALESCE(ib.quantity, 0) BETWEEN 
                COALESCE(ip.safety_stock_days, 7) * (SELECT AVG(sales_quantity + consumption_quantity) / 30 
                    FROM planning_demand_history WHERE item_id = i.id)
                AND COALESCE(ip.max_order_quantity, 1000)
        """).fetchone()['cnt'],
        'low_stock': db.execute("""
            SELECT COUNT(*) as cnt FROM wms_inventory_balances ib
            JOIN wms_items i ON ib.item_id = i.id
            WHERE i.is_active = 1 AND COALESCE(ib.quantity, 0) > 0
            AND COALESCE(ib.quantity, 0) < 
                (SELECT AVG(sales_quantity + consumption_quantity) / 30 
                 FROM planning_demand_history WHERE item_id = i.id) * 7
        """).fetchone()['cnt'],
        'overstock': db.execute("""
            SELECT COUNT(*) as cnt FROM wms_inventory_balances ib
            JOIN wms_items i ON ib.item_id = i.id
            LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
            WHERE i.is_active = 1
            AND COALESCE(ib.quantity, 0) > COALESCE(ip.max_order_quantity, 1000)
        """).fetchone()['cnt'],
        'stockout': db.execute("""
            SELECT COUNT(*) as cnt FROM wms_inventory_balances ib
            JOIN wms_items i ON ib.item_id = i.id
            WHERE i.is_active = 1 AND COALESCE(ib.quantity, 0) <= 0
        """).fetchone()['cnt']
    }
    
    # Slow/Dead stock
    slow_dead = db.execute("""
        SELECT i.item_code, i.name,
               COALESCE(ib.quantity, 0) as current_stock,
               (SELECT MAX(period_start) FROM planning_demand_history WHERE item_id = i.id) as last_movement
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        WHERE i.is_active = 1 AND COALESCE(ib.quantity, 0) > 0
        AND NOT EXISTS (SELECT 1 FROM planning_demand_history 
                        WHERE item_id = i.id AND period_start >= DATE('now', '-90 days'))
        ORDER BY ib.quantity DESC
        LIMIT 20
    """).fetchall()
    
    return render_template('scm/inventory_optimization/index.html',
        title='Inventory Optimization',
        stock_health=stock_health,
        slow_dead=slow_dead
    )


@scm_bp.route('/inventory-optimization/stock-health')
@scm_permission_required('scm', 'inventory')
def inventory_stock_health():
    """Detailed stock health view."""
    db = get_db()
    
    items = db.execute("""
        SELECT i.item_code, i.name,
               COALESCE(ib.quantity, 0) as current_stock,
               COALESCE((SELECT AVG(sales_quantity + consumption_quantity) / 30
                        FROM planning_demand_history
                        WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')), 0) as daily_demand,
               COALESCE(ib.quantity, 0) / NULLIF((SELECT AVG(sales_quantity + consumption_quantity) / 30
                        FROM planning_demand_history
                        WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')), 0) as days_of_stock,
               ip.safety_stock_days, ip.abc_class, ip.xyz_class
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
        WHERE i.is_active = 1
        ORDER BY days_of_stock ASC
        LIMIT 100
    """).fetchall()
    
    return render_template('scm/inventory_optimization/stock_health.html',
        title='Stock Health',
        items=items
    )


@scm_bp.route('/inventory-optimization/service-level')
@scm_permission_required('scm', 'inventory')
def inventory_service_level():
    """Service level targets and tracking."""
    db = get_db()
    
    service_levels = db.execute("""
        SELECT ip.*, i.item_code, i.name as item_name,
               ip.service_level_target * 100 as target_pct
        FROM planning_item_profiles ip
        JOIN wms_items i ON ip.item_id = i.id
        WHERE i.is_active = 1
        ORDER BY i.item_code
        LIMIT 50
    """).fetchall()
    
    return render_template('scm/inventory_optimization/service_level.html',
        title='Service Level Targets',
        service_levels=service_levels
    )


@scm_bp.route('/inventory-optimization/safety-stock')
@scm_permission_required('scm', 'inventory')
def inventory_safety_stock():
    """Safety stock optimization."""
    db = get_db()
    
    safety_stock_items = db.execute("""
        SELECT i.item_code, i.name,
               COALESCE(ib.quantity, 0) as current_stock,
               ip.safety_stock_days, ip.service_level_target,
               (SELECT AVG(sales_quantity + consumption_quantity) / 30
                FROM planning_demand_history
                WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')) as daily_demand,
               (SELECT AVG(sales_quantity + consumption_quantity) / 30
                FROM planning_demand_history
                WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')) * ip.safety_stock_days as calculated_ss
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
        WHERE i.is_active = 1 AND ip.safety_stock_days IS NOT NULL
        ORDER BY i.item_code
        LIMIT 50
    """).fetchall()
    
    return render_template('scm/inventory_optimization/safety_stock.html',
        title='Safety Stock Optimization',
        safety_stock_items=safety_stock_items
    )


@scm_bp.route('/inventory-optimization/excess-slow-dead')
@scm_permission_required('scm', 'inventory')
def inventory_excess_slow_dead():
    """Excess, slow, and dead stock analysis."""
    db = get_db()
    
    # Excess stock (> max)
    excess = db.execute("""
        SELECT i.item_code, i.name,
               COALESCE(ib.quantity, 0) as current_stock,
               COALESCE(ip.max_order_quantity, 1000) as max_stock,
               (COALESCE(ib.quantity, 0) - COALESCE(ip.max_order_quantity, 1000)) as excess_value
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
        WHERE i.is_active = 1
        AND COALESCE(ib.quantity, 0) > COALESCE(ip.max_order_quantity, 1000)
        ORDER BY excess_value DESC
    """).fetchall()
    
    # Slow moving (> 90 days no movement)
    slow = db.execute("""
        SELECT i.item_code, i.name,
               COALESCE(ib.quantity, 0) as current_stock,
               (SELECT MAX(period_start) FROM planning_demand_history WHERE item_id = i.id) as last_movement
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        WHERE i.is_active = 1 AND COALESCE(ib.quantity, 0) > 0
        AND (SELECT MAX(period_start) FROM planning_demand_history WHERE item_id = i.id) < DATE('now', '-90 days')
        ORDER BY ib.quantity DESC
    """).fetchall()
    
    # Dead stock (> 365 days no movement)
    dead = db.execute("""
        SELECT i.item_code, i.name,
               COALESCE(ib.quantity, 0) as current_stock,
               (SELECT MAX(period_start) FROM planning_demand_history WHERE item_id = i.id) as last_movement
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        WHERE i.is_active = 1 AND COALESCE(ib.quantity, 0) > 0
        AND (SELECT MAX(period_start) FROM planning_demand_history WHERE item_id = i.id) < DATE('now', '-365 days')
        ORDER BY ib.quantity DESC
    """).fetchall()
    
    return render_template('scm/inventory_optimization/excess_slow_dead.html',
        title='Excess/Slow/Dead Stock',
        excess=excess,
        slow=slow,
        dead=dead
    )


@scm_bp.route('/inventory-optimization/abc-xyz')
@scm_permission_required('scm', 'inventory')
def inventory_abc_xyz():
    """ABC/XYZ analysis."""
    db = get_db()
    
    # ABC classification
    abc_class = db.execute("""
        SELECT ip.abc_class, COUNT(*) as count
        FROM planning_item_profiles ip
        JOIN wms_items i ON ip.item_id = i.id
        WHERE i.is_active = 1
        GROUP BY ip.abc_class
    """).fetchall()
    
    # XYZ classification
    xyz_class = db.execute("""
        SELECT ip.xyz_class, COUNT(*) as count
        FROM planning_item_profiles ip
        JOIN wms_items i ON ip.item_id = i.id
        WHERE i.is_active = 1
        GROUP BY ip.xyz_class
    """).fetchall()
    
    # Combined analysis
    combined = db.execute("""
        SELECT ip.abc_class, ip.xyz_class, COUNT(*) as count
        FROM planning_item_profiles ip
        JOIN wms_items i ON ip.item_id = i.id
        WHERE i.is_active = 1
        GROUP BY ip.abc_class, ip.xyz_class
        ORDER BY ip.abc_class, ip.xyz_class
    """).fetchall()
    
    return render_template('scm/inventory_optimization/abc_xyz.html',
        title='ABC/XYZ Analysis',
        abc_class=abc_class,
        xyz_class=xyz_class,
        combined=combined
    )


@scm_bp.route('/inventory-optimization/risk-heatmap')
@scm_permission_required('scm', 'inventory')
def inventory_risk_heatmap():
    """Stock risk heatmap."""
    db = get_db()
    
    risk_items = db.execute("""
        SELECT i.item_code, i.name,
               COALESCE(ib.quantity, 0) as current_stock,
               (SELECT AVG(sales_quantity + consumption_quantity) / 30
                FROM planning_demand_history
                WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')) as daily_demand,
               ip.abc_class, ip.criticality_level,
               CASE 
                   WHEN COALESCE(ib.quantity, 0) <= 0 THEN 'CRITICAL'
                   WHEN COALESCE(ib.quantity, 0) < (SELECT AVG(sales_quantity + consumption_quantity) / 30
                        FROM planning_demand_history
                        WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')) * 7 THEN 'HIGH'
                   WHEN COALESCE(ib.quantity, 0) < (SELECT AVG(sales_quantity + consumption_quantity) / 30
                        FROM planning_demand_history
                        WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')) * 14 THEN 'MEDIUM'
                   ELSE 'LOW'
               END as risk_level
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
        WHERE i.is_active = 1
        ORDER BY risk_level, i.item_code
        LIMIT 100
    """).fetchall()
    
    return render_template('scm/inventory_optimization/risk_heatmap.html',
        title='Stock Risk Heatmap',
        risk_items=risk_items
    )


@scm_bp.route('/inventory-optimization/overstock-understock')
@scm_permission_required('scm', 'inventory')
def inventory_overstock_understock():
    """Overstock and understock alerts."""
    db = get_db()
    
    overstock = db.execute("""
        SELECT i.item_code, i.name,
               COALESCE(ib.quantity, 0) as current_stock,
               COALESCE(ip.max_order_quantity, 1000) as max_stock,
               COALESCE((SELECT AVG(sales_quantity + consumption_quantity) / 30
                        FROM planning_demand_history
                        WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')), 0) as daily_demand,
               (COALESCE(ib.quantity, 0) / NULLIF((SELECT AVG(sales_quantity + consumption_quantity) / 30
                        FROM planning_demand_history
                        WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')), 0)) as days_of_stock
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
        WHERE i.is_active = 1
        AND COALESCE(ib.quantity, 0) > COALESCE(ip.max_order_quantity, 1000)
        ORDER BY (COALESCE(ib.quantity, 0) - COALESCE(ip.max_order_quantity, 1000)) DESC
    """).fetchall()
    
    understock = db.execute("""
        SELECT i.item_code, i.name,
               COALESCE(ib.quantity, 0) as current_stock,
               COALESCE(ip.safety_stock_days, 7) * (SELECT AVG(sales_quantity + consumption_quantity) / 30
                        FROM planning_demand_history
                        WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')) as safety_stock,
               COALESCE((SELECT AVG(sales_quantity + consumption_quantity) / 30
                        FROM planning_demand_history
                        WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')), 0) as daily_demand
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
        WHERE i.is_active = 1
        AND COALESCE(ib.quantity, 0) < COALESCE(ip.safety_stock_days, 7) * (SELECT AVG(sales_quantity + consumption_quantity) / 30
                        FROM planning_demand_history
                        WHERE item_id = i.id AND period_start >= DATE('now', '-30 days'))
        ORDER BY ib.quantity ASC
    """).fetchall()
    
    return render_template('scm/inventory_optimization/overstock_understock.html',
        title='Overstock/Understock Alerts',
        overstock=overstock,
        understock=understock
    )


@scm_bp.route('/inventory-optimization/reports')
@scm_permission_required('scm', 'reports')
def inventory_reports():
    """Inventory optimization reports."""
    return render_template('scm/inventory_optimization/reports.html',
        title='Inventory Optimization Reports'
    )


# ============================================================
# MULTI-ECHELON PLANNING
# ============================================================

@scm_bp.route('/multi-echelon')
@scm_permission_required('scm', 'network')
def multi_echelon_planning():
    """Multi-echelon planning main page."""
    db = get_db()
    
    # Network overview
    warehouses = db.execute("SELECT id, name FROM wms_warehouses WHERE is_active = 1").fetchall()
    
    network_summary = []
    for wh in warehouses:
        stock = db.execute("SELECT COALESCE(SUM(quantity), 0) as total FROM wms_inventory_balances WHERE warehouse_id = ?", (wh['id'],)).fetchone()['total']
        demand = db.execute("""
            SELECT COALESCE(SUM(sales_quantity + consumption_quantity), 0) as total
            FROM planning_demand_history
            WHERE warehouse_id = ? AND period_start >= DATE('now', '-30 days')
        """, (wh['id'],)).fetchone()['total']
        
        network_summary.append({
            'warehouse': wh,
            'current_stock': stock,
            'demand_30d': demand,
            'coverage_days': stock / (demand / 30) if demand > 0 else 999
        })
    
    return render_template('scm/multi_echelon/index.html',
        title='Multi-Echelon Planning',
        network_summary=network_summary
    )


@scm_bp.route('/multi-echelon/network-view')
@scm_permission_required('scm', 'network')
def multi_echelon_network_view():
    """Network view of inventory across echelons."""
    db = get_db()
    
    # Get all warehouses and their stock levels
    warehouses = db.execute("""
        SELECT w.id, w.name, w.warehouse_type,
               COALESCE(SUM(ib.quantity), 0) as total_stock
        FROM wms_warehouses w
        LEFT JOIN wms_inventory_balances ib ON w.id = ib.warehouse_id
        WHERE w.is_active = 1
        GROUP BY w.id
    """).fetchall()
    
    return render_template('scm/multi_echelon/network_view.html',
        title='Network View',
        warehouses=warehouses
    )


@scm_bp.route('/multi-echelon/source-destination')
@scm_permission_required('scm', 'network')
def multi_echelon_source_destination():
    """Source to destination planning."""
    db = get_db()
    
    # Transfer recommendations
    transfers = db.execute("""
        SELECT t.*, i.item_code, i.name as item_name,
               sw.name as source_warehouse, dw.name as dest_warehouse
        FROM planning_transfer_recommendations t
        JOIN wms_items i ON t.item_id = i.id
        LEFT JOIN wms_warehouses sw ON t.source_warehouse_id = sw.id
        LEFT JOIN wms_warehouses dw ON t.destination_warehouse_id = dw.id
        WHERE t.status = 'OPEN'
        ORDER BY t.priority DESC
    """).fetchall()
    
    return render_template('scm/multi_echelon/source_destination.html',
        title='Source-to-Destination',
        transfers=transfers
    )


@scm_bp.route('/multi-echelon/cross-warehouse')
@scm_permission_required('scm', 'network')
def multi_echelon_cross_warehouse():
    """Cross-warehouse balancing."""
    db = get_db()
    
    # Items with excess in one warehouse and shortage in another
    cross_wh = db.execute("""
        SELECT i.item_code, i.name,
               w1.name as excess_warehouse, w1.id as excess_wh_id,
               COALESCE(ib1.quantity, 0) as excess_qty,
               w2.name as shortage_warehouse, w2.id as shortage_wh_id,
               COALESCE(ib2.quantity, 0) as shortage_qty
        FROM wms_items i
        CROSS JOIN wms_warehouses w1
        CROSS JOIN wms_warehouses w2
        LEFT JOIN wms_inventory_balances ib1 ON i.id = ib1.item_id AND ib1.warehouse_id = w1.id
        LEFT JOIN wms_inventory_balances ib2 ON i.id = ib2.item_id AND ib2.warehouse_id = w2.id
        WHERE w1.is_active = 1 AND w2.is_active = 1 AND w1.id != w2.id
        AND COALESCE(ib1.quantity, 0) > 100
        AND COALESCE(ib2.quantity, 0) < 20
        ORDER BY (COALESCE(ib1.quantity, 0) - 100) DESC
        LIMIT 30
    """).fetchall()
    
    return render_template('scm/multi_echelon/cross_warehouse.html',
        title='Cross-Warehouse Balancing',
        cross_wh=cross_wh
    )


@scm_bp.route('/multi-echelon/inter-branch')
@scm_permission_required('scm', 'network')
def multi_echelon_inter_branch():
    """Inter-branch reallocation."""
    db = get_db()
    
    branches = db.execute("SELECT id, name FROM companies WHERE is_active = 1").fetchall()
    
    return render_template('scm/multi_echelon/inter_branch.html',
        title='Inter-Branch Reallocation',
        branches=branches
    )


@scm_bp.route('/multi-echelon/transfer-suggestions')
@scm_permission_required('scm', 'network')
def multi_echelon_transfer_suggestions():
    """Transfer suggestions generated by the system."""
    db = get_db()
    
    suggestions = db.execute("""
        SELECT t.*, i.item_code, i.name as item_name,
               sw.name as source, dw.name as destination
        FROM planning_transfer_recommendations t
        JOIN wms_items i ON t.item_id = i.id
        LEFT JOIN wms_warehouses sw ON t.source_warehouse_id = sw.id
        LEFT JOIN wms_warehouses dw ON t.destination_warehouse_id = dw.id
        ORDER BY t.priority DESC, t.created_at DESC
        LIMIT 50
    """).fetchall()
    
    return render_template('scm/multi_echelon/transfer_suggestions.html',
        title='Transfer Suggestions',
        suggestions=suggestions
    )


@scm_bp.route('/multi-echelon/reports')
@scm_permission_required('scm', 'reports')
def multi_echelon_reports():
    """Multi-echelon planning reports."""
    return render_template('scm/multi_echelon/reports.html',
        title='MEIO Reports'
    )


# ============================================================
# SERVICE LEVEL & FULFILLMENT
# ============================================================

@scm_bp.route('/service-level')
@scm_permission_required('scm', 'service')
def service_level_planning():
    """Service level and fulfillment main page."""
    db = get_db()
    
    # Service level metrics
    fill_rate = db.execute("""
        SELECT COALESCE(
            (SELECT SUM(shipped_quantity) * 1.0 / NULLIF(SUM(ordered_quantity), 0) 
             FROM wms_dispatch_plan_lines dl
             JOIN wms_dispatch_plans d ON dl.dispatch_plan_id = d.id
             WHERE d.created_at >= DATE('now', '-30 days'))
        , 0.95) as rate
    """).fetchone()['rate'] or 0.95
    
    # OTIF rate (On Time In Full)
    otif_rate = fill_rate  # Simplified
    
    return render_template('scm/service_level/index.html',
        title='Service Level & Fulfillment',
        fill_rate=fill_rate * 100,
        otif_rate=otif_rate * 100
    )


@scm_bp.route('/service-level/dashboard')
@scm_permission_required('scm', 'service')
def service_level_dashboard():
    """Service level dashboard."""
    db = get_db()
    
    # Fill rate by warehouse
    fill_by_warehouse = db.execute("""
        SELECT w.name,
               COALESCE((SELECT SUM(shipped_quantity) * 1.0 / NULLIF(SUM(ordered_quantity), 0)
                         FROM wms_dispatch_plan_lines dl
                         JOIN wms_dispatch_plans d ON dl.dispatch_plan_id = d.id
                         WHERE d.warehouse_id = w.id AND d.created_at >= DATE('now', '-30 days')), 0.95) as fill_rate
        FROM wms_warehouses w
        WHERE w.is_active = 1
    """).fetchall()
    
    # Service level by category
    fill_by_category = db.execute("""
        SELECT c.name as category,
               COALESCE((SELECT SUM(shipped_quantity) * 1.0 / NULLIF(SUM(ordered_quantity), 0)
                         FROM wms_dispatch_plan_lines dl
                         JOIN wms_dispatch_plans d ON dl.dispatch_plan_id = d.id
                         JOIN wms_items i ON dl.item_id = i.id
                         WHERE i.category_id = c.id AND d.created_at >= DATE('now', '-30 days')), 0.95) as fill_rate
        FROM wms_categories c
        WHERE c.is_active = 1
    """).fetchall()
    
    return render_template('scm/service_level/dashboard.html',
        title='Service Level Dashboard',
        fill_by_warehouse=fill_by_warehouse,
        fill_by_category=fill_by_category
    )


@scm_bp.route('/service-level/fill-rate')
@scm_permission_required('scm', 'service')
def service_level_fill_rate():
    """Fill rate analysis."""
    db = get_db()
    
    fill_rate_trend = db.execute("""
        SELECT DATE(d.created_at) as date,
               SUM(shipped_quantity) * 1.0 / NULLIF(SUM(ordered_quantity), 0) as fill_rate
        FROM wms_dispatch_plan_lines dl
        JOIN wms_dispatch_plans d ON dl.dispatch_plan_id = d.id
        WHERE d.created_at >= DATE('now', '-30 days')
        GROUP BY DATE(d.created_at)
        ORDER BY date
    """).fetchall()
    
    return render_template('scm/service_level/fill_rate.html',
        title='Fill Rate Analysis',
        fill_rate_trend=fill_rate_trend
    )


@scm_bp.route('/service-level/otif')
@scm_permission_required('scm', 'service')
def service_level_otif():
    """OTIF analysis view."""
    return render_template('scm/service_level/otif.html',
        title='OTIF Analysis'
    )


@scm_bp.route('/service-level/backorder')
@scm_permission_required('scm', 'service')
def service_level_backorder():
    """Backorder impact view."""
    db = get_db()
    
    backorders = db.execute("""
        SELECT i.item_code, i.name,
               COALESCE(SUM(dl.ordered_quantity - dl.shipped_quantity), 0) as backorder_qty,
               COUNT(DISTINCT d.id) as order_count
        FROM wms_dispatch_plan_lines dl
        JOIN wms_dispatch_plans d ON dl.dispatch_plan_id = d.id
        JOIN wms_items i ON dl.item_id = i.id
        WHERE d.created_at >= DATE('now', '-30 days')
        AND dl.ordered_quantity > dl.shipped_quantity
        GROUP BY i.id
        ORDER BY backorder_qty DESC
    """).fetchall()
    
    return render_template('scm/service_level/backorder.html',
        title='Backorder Impact',
        backorders=backorders
    )


@scm_bp.route('/service-level/lost-demand')
@scm_permission_required('scm', 'service')
def service_level_lost_demand():
    """Lost demand view."""
    db = get_db()
    
    lost_sales = db.execute("""
        SELECT ls.*, i.item_code, i.name as item_name
        FROM planning_lost_sales ls
        JOIN wms_items i ON ls.item_id = i.id
        ORDER BY ls.lost_date DESC
        LIMIT 50
    """).fetchall()
    
    return render_template('scm/service_level/lost_demand.html',
        title='Lost Demand',
        lost_sales=lost_sales
    )


@scm_bp.route('/service-level/reports')
@scm_permission_required('scm', 'reports')
def service_level_reports():
    """Service level reports."""
    return render_template('scm/service_level/reports.html',
        title='Fulfillment Reports'
    )


# ============================================================
# SCENARIO PLANNING
# ============================================================

@scm_bp.route('/scenarios')
@scm_permission_required('scm', 'scenarios')
def scenario_planning():
    """Scenario planning main page."""
    db = get_db()
    
    scenarios = db.execute("""
        SELECT s.*, u.username as created_by_name
        FROM planning_scenarios s
        LEFT JOIN users u ON s.created_by = u.id
        WHERE s.is_active = 1
        ORDER BY s.created_at DESC
    """).fetchall()
    
    return render_template('scm/scenarios/index.html',
        title='Scenario Planning',
        scenarios=scenarios
    )


@scm_bp.route('/scenarios/create', methods=['POST'])
@scm_permission_required('scm', 'scenarios')
def scenario_create():
    """Create a new scenario."""
    db = get_db()
    
    name = request.form.get('name')
    description = request.form.get('description', '')
    scenario_type = request.form.get('scenario_type', 'DEMAND_SPIKE')
    parameters = request.form.get('parameters', '{}')
    
    cursor = db.execute("""
        INSERT INTO planning_scenarios
        (name, description, scenario_type, parameters_json, is_active, created_by)
        VALUES (?, ?, ?, ?, 1, ?)
    """, (name, description, scenario_type, parameters, session.get('user_id')))
    scenario_id = cursor.lastrowid
    db.commit()
    
    log_scm_audit(db, 'SCENARIO_CREATED', 'scenario', scenario_id,
                   user_id=session.get('user_id'))
    
    flash(f'Scenario "{name}" created.', 'success')
    return redirect(url_for('scm.scenario_detail', scenario_id=scenario_id))


@scm_bp.route('/scenarios/<int:scenario_id>')
@scm_permission_required('scm', 'scenarios')
def scenario_detail(scenario_id):
    """Scenario detail view."""
    db = get_db()
    
    scenario = db.execute("SELECT * FROM planning_scenarios WHERE id = ?", (scenario_id,)).fetchone()
    if not scenario:
        flash('Scenario not found.', 'error')
        return redirect(url_for('scm.scenario_planning'))
    
    scenario_lines = db.execute("""
        SELECT sl.*, i.item_code, i.name as item_name
        FROM planning_scenario_lines sl
        JOIN wms_items i ON sl.item_id = i.id
        WHERE sl.scenario_id = ?
        ORDER BY ABS(sl.impact_value) DESC
        LIMIT 50
    """, (scenario_id,)).fetchall()
    
    return render_template('scm/scenarios/detail.html',
        title=f'Scenario: {scenario["name"]}',
        scenario=scenario,
        scenario_lines=scenario_lines
    )


@scm_bp.route('/scenarios/<int:scenario_id>/run', methods=['POST'])
@scm_permission_required('scm', 'scenarios')
def scenario_run(scenario_id):
    """Run a scenario simulation."""
    db = get_db()
    
    scenario = db.execute("SELECT * FROM planning_scenarios WHERE id = ?", (scenario_id,)).fetchone()
    if not scenario:
        flash('Scenario not found.', 'error')
        return redirect(url_for('scm.scenario_planning'))
    
    # Parse parameters
    params = json.loads(scenario['parameters_json'] or '{}')
    scenario_type = scenario['scenario_type']
    
    # Apply scenario impact
    if scenario_type == 'DEMAND_SPIKE':
        impact_pct = params.get('demand_increase_pct', 20) / 100.0
        
        items = db.execute("SELECT id FROM wms_items WHERE is_active = 1").fetchall()
        for item in items:
            base_demand = db.execute("""
                SELECT COALESCE(AVG(sales_quantity + consumption_quantity), 0) as demand
                FROM planning_demand_history
                WHERE item_id = ? AND period_start >= DATE('now', '-30 days')
            """, (item['id'],)).fetchone()['demand']
            
            scenario_value = base_demand * (1 + impact_pct)
            impact_value = scenario_value - base_demand
            
            db.execute("""
                INSERT INTO planning_scenario_lines
                (scenario_id, item_id, metric_name, base_value, scenario_value, impact_value, impact_percent)
                VALUES (?, ?, 'DEMAND', ?, ?, ?, ?)
            """, (scenario_id, item['id'], base_demand, scenario_value, impact_value, impact_pct * 100))
    
    # Update scenario totals
    total_items = db.execute("SELECT COUNT(*) as cnt FROM planning_scenario_lines WHERE scenario_id = ?", (scenario_id,)).fetchone()['cnt']
    total_impact = db.execute("SELECT SUM(impact_value) as total FROM planning_scenario_lines WHERE scenario_id = ?", (scenario_id,)).fetchone()['total']
    
    db.execute("""
        UPDATE planning_scenarios
        SET total_impact_items = ?, total_shortage_impact = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (total_items, total_impact or 0, scenario_id))
    db.commit()
    
    log_scm_audit(db, 'SCENARIO_RUN', 'scenario', scenario_id,
                   user_id=session.get('user_id'))
    
    flash('Scenario simulation completed.', 'success')
    return redirect(url_for('scm.scenario_detail', scenario_id=scenario_id))


@scm_bp.route('/scenarios/comparison')
@scm_permission_required('scm', 'scenarios')
def scenario_comparison():
    """Compare multiple scenarios."""
    db = get_db()
    
    scenarios = db.execute("""
        SELECT * FROM planning_scenarios
        WHERE is_active = 1
        ORDER BY created_at DESC
        LIMIT 5
    """).fetchall()
    
    return render_template('scm/scenarios/comparison.html',
        title='Scenario Comparison',
        scenarios=scenarios
    )


@scm_bp.route('/scenarios/reports')
@scm_permission_required('scm', 'reports')
def scenario_reports():
    """Scenario planning reports."""
    return render_template('scm/scenarios/reports.html',
        title='Scenario Reports'
    )


# ============================================================
# ALERTS & EXCEPTIONS
# ============================================================

@scm_bp.route('/alerts')
@scm_permission_required('scm', 'alerts')
def scm_alerts():
    """SCM Alerts main page."""
    db = get_db()
    
    alerts = db.execute("""
        SELECT a.*, i.item_code, i.name as item_name
        FROM planning_alerts a
        LEFT JOIN wms_items i ON a.item_id = i.id
        WHERE a.is_acknowledged = 0
        ORDER BY 
            CASE a.severity 
                WHEN 'CRITICAL' THEN 1 
                WHEN 'HIGH' THEN 2 
                WHEN 'MEDIUM' THEN 3 
                ELSE 4 
            END,
            a.created_at DESC
        LIMIT 100
    """).fetchall()
    
    # Alert summary by type
    alert_summary = db.execute("""
        SELECT alert_type, severity, COUNT(*) as cnt
        FROM planning_alerts
        WHERE is_acknowledged = 0
        GROUP BY alert_type, severity
    """).fetchall()
    
    return render_template('scm/alerts/index.html',
        title='SCM Alerts',
        alerts=alerts,
        alert_summary=alert_summary
    )


@scm_bp.route('/alerts/shortage')
@scm_permission_required('scm', 'alerts')
def alerts_shortage():
    """Shortage alerts."""
    db = get_db()
    
    alerts = db.execute("""
        SELECT a.*, i.item_code, i.name as item_name
        FROM planning_alerts a
        LEFT JOIN wms_items i ON a.item_id = i.id
        WHERE a.alert_type IN ('STOCKOUT', 'SHORTAGE', 'REORDER_POINT_BREACH')
        AND a.is_acknowledged = 0
        ORDER BY a.created_at DESC
    """).fetchall()
    
    return render_template('scm/alerts/shortage.html',
        title='Shortage Alerts',
        alerts=alerts
    )


@scm_bp.route('/alerts/overstock')
@scm_permission_required('scm', 'alerts')
def alerts_overstock():
    """Overstock alerts."""
    db = get_db()
    
    alerts = db.execute("""
        SELECT a.*, i.item_code, i.name as item_name
        FROM planning_alerts a
        LEFT JOIN wms_items i ON a.item_id = i.id
        WHERE a.alert_type IN ('OVERSTOCK', 'EXCESS')
        AND a.is_acknowledged = 0
        ORDER BY a.created_at DESC
    """).fetchall()
    
    return render_template('scm/alerts/overstock.html',
        title='Overstock Alerts',
        alerts=alerts
    )


@scm_bp.route('/alerts/forecast-deviation')
@scm_permission_required('scm', 'alerts')
def alerts_forecast_deviation():
    """Forecast deviation alerts."""
    db = get_db()
    
    alerts = db.execute("""
        SELECT a.*, i.item_code, i.name as item_name
        FROM planning_alerts a
        LEFT JOIN wms_items i ON a.item_id = i.id
        WHERE a.alert_type = 'FORECAST_DEVIATION'
        AND a.is_acknowledged = 0
        ORDER BY a.created_at DESC
    """).fetchall()
    
    return render_template('scm/alerts/forecast_deviation.html',
        title='Forecast Deviation Alerts',
        alerts=alerts
    )


@scm_bp.route('/alerts/delayed-supply')
@scm_permission_required('scm', 'alerts')
def alerts_delayed_supply():
    """Delayed supply alerts."""
    db = get_db()
    
    alerts = db.execute("""
        SELECT a.*, i.item_code, i.name as item_name,
               ir.expected_arrival_date, ir.status as receipt_status
        FROM planning_alerts a
        LEFT JOIN wms_items i ON a.item_id = i.id
        LEFT JOIN wms_inbound_receipts ir ON a.item_id = ir.item_id AND ir.status IN ('APPROVED', 'SENT', 'IN_TRANSIT')
        WHERE a.alert_type = 'SUPPLIER_DELAY'
        AND a.is_acknowledged = 0
        ORDER BY a.created_at DESC
    """).fetchall()
    
    return render_template('scm/alerts/delayed_supply.html',
        title='Delayed Supply Alerts',
        alerts=alerts
    )


@scm_bp.route('/alerts/low-coverage')
@scm_permission_required('scm', 'alerts')
def alerts_low_coverage():
    """Low coverage alerts."""
    db = get_db()
    
    alerts = db.execute("""
        SELECT a.*, i.item_code, i.name as item_name
        FROM planning_alerts a
        LEFT JOIN wms_items i ON a.item_id = i.id
        WHERE a.alert_type = 'LOW_COVERAGE'
        AND a.is_acknowledged = 0
        ORDER BY a.created_at DESC
    """).fetchall()
    
    return render_template('scm/alerts/low_coverage.html',
        title='Low Coverage Alerts',
        alerts=alerts
    )


@scm_bp.route('/alerts/critical-watchlist')
@scm_permission_required('scm', 'alerts')
def alerts_critical_watchlist():
    """Critical item watchlist."""
    db = get_db()
    
    critical_items = db.execute("""
        SELECT i.item_code, i.name,
               ip.criticality_level, ip.planning_method,
               COALESCE(ib.quantity, 0) as current_stock,
               (SELECT AVG(sales_quantity + consumption_quantity) / 30
                FROM planning_demand_history
                WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')) as daily_demand
        FROM wms_items i
        LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        WHERE i.is_active = 1
        AND ip.criticality_level = 'CRITICAL'
        ORDER BY i.item_code
    """).fetchall()
    
    return render_template('scm/alerts/critical_watchlist.html',
        title='Critical Item Watchlist',
        critical_items=critical_items
    )


@scm_bp.route('/alerts/escalation')
@scm_permission_required('scm', 'alerts')
def alerts_escalation():
    """Escalation queue."""
    db = get_db()
    
    escalated = db.execute("""
        SELECT a.*, i.item_code, i.name as item_name
        FROM planning_alerts a
        LEFT JOIN wms_items i ON a.item_id = i.id
        WHERE a.severity = 'CRITICAL'
        AND a.is_acknowledged = 0
        ORDER BY a.created_at DESC
    """).fetchall()
    
    return render_template('scm/alerts/escalation.html',
        title='Escalation Queue',
        escalated=escalated
    )


@scm_bp.route('/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@scm_permission_required('scm', 'alerts')
def alert_acknowledge(alert_id):
    """Acknowledge an alert."""
    db = get_db()
    
    db.execute("""
        UPDATE planning_alerts
        SET is_acknowledged = 1, acknowledged_by = ?, acknowledged_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (session.get('user_id'), alert_id))
    db.commit()
    
    log_scm_audit(db, 'ALERT_ACKNOWLEDGED', 'alert', alert_id,
                   user_id=session.get('user_id'))
    
    flash('Alert acknowledged.', 'success')
    return redirect(url_for('scm.scm_alerts'))


@scm_bp.route('/alerts/generate', methods=['POST'])
@scm_permission_required('scm', 'alerts')
def alerts_generate():
    """Generate planning alerts."""
    db = get_db()
    
    from planning_models import generate_planning_alerts
    generate_planning_alerts(db)
    
    flash('Alerts generated.', 'success')
    return redirect(url_for('scm.scm_alerts'))


@scm_bp.route('/alerts/reports')
@scm_permission_required('scm', 'reports')
def alerts_reports():
    """Exception reports."""
    return render_template('scm/alerts/reports.html',
        title='Exception Reports'
    )


# ============================================================
# SUPPLIER & PROCUREMENT LINKAGE
# ============================================================

@scm_bp.route('/supplier')
@scm_permission_required('scm', 'supplier')
def supplier_linkage():
    """Supplier and procurement linkage main page."""
    db = get_db()
    
    suppliers = db.execute("""
        SELECT s.*, 
               (SELECT COUNT(*) FROM wms_item_suppliers WHERE supplier_id = s.id) as item_count
        FROM suppliers s
        WHERE s.is_active = 1
        ORDER BY s.name
        LIMIT 20
    """).fetchall()
    
    return render_template('scm/supplier/index.html',
        title='Supplier & Procurement Linkage',
        suppliers=suppliers
    )


@scm_bp.route('/supplier/lead-times')
@scm_permission_required('scm', 'supplier')
def supplier_lead_times():
    """Supplier lead times view."""
    db = get_db()
    
    lead_times = db.execute("""
        SELECT s.name as supplier_name, i.item_code, i.name as item_name,
               wis.lead_time_days, wis.is_preferred
        FROM wms_item_suppliers wis
        JOIN suppliers s ON wis.supplier_id = s.id
        JOIN wms_items i ON wis.item_id = i.id
        WHERE s.is_active = 1 AND i.is_active = 1
        ORDER BY s.name, i.item_code
        LIMIT 50
    """).fetchall()
    
    return render_template('scm/supplier/lead_times.html',
        title='Supplier Lead Times',
        lead_times=lead_times
    )


@scm_bp.route('/supplier/open-pos')
@scm_permission_required('scm', 'supplier')
def supplier_open_pos():
    """Open POs impact on supply."""
    db = get_db()
    
    open_pos = db.execute("""
        SELECT ir.*, i.item_code, i.name as item_name,
               s.name as supplier_name
        FROM wms_inbound_receipts ir
        JOIN wms_items i ON ir.item_id = i.id
        LEFT JOIN suppliers s ON ir.supplier_id = s.id
        WHERE ir.status IN ('APPROVED', 'SENT', 'IN_TRANSIT')
        ORDER BY ir.expected_arrival_date
    """).fetchall()
    
    return render_template('scm/supplier/open_pos.html',
        title='Open Purchase Orders',
        open_pos=open_pos
    )


@scm_bp.route('/supplier/risk')
@scm_permission_required('scm', 'supplier')
def supplier_risk():
    """Supply risk by supplier."""
    db = get_db()
    
    supplier_risk = db.execute("""
        SELECT s.name,
               COUNT(DISTINCT ir.item_id) as items_on_order,
               SUM(ir.quantity - COALESCE(ir.received_quantity, 0)) as pending_qty,
               (SELECT COUNT(*) FROM planning_alerts WHERE supplier_id = s.id AND is_acknowledged = 0) as alert_count
        FROM suppliers s
        LEFT JOIN wms_inbound_receipts ir ON s.id = ir.supplier_id AND ir.status IN ('APPROVED', 'SENT', 'IN_TRANSIT')
        WHERE s.is_active = 1
        GROUP BY s.id
        ORDER BY alert_count DESC, pending_qty DESC
    """).fetchall()
    
    return render_template('scm/supplier/risk.html',
        title='Supply Risk by Supplier',
        supplier_risk=supplier_risk
    )


@scm_bp.route('/supplier/reliability')
@scm_permission_required('scm', 'supplier')
def supplier_reliability():
    """Supplier reliability metrics."""
    db = get_db()
    
    reliability = db.execute("""
        SELECT spp.*, s.name as supplier_name
        FROM planning_supplier_performance spp
        JOIN suppliers s ON spp.supplier_id = s.id
        ORDER BY spp.period_start DESC
        LIMIT 50
    """).fetchall()
    
    return render_template('scm/supplier/reliability.html',
        title='Supplier Reliability',
        reliability=reliability
    )


@scm_bp.route('/supplier/reports')
@scm_permission_required('scm', 'reports')
def supplier_reports():
    """Procurement-SCM reports."""
    return render_template('scm/supplier/reports.html',
        title='Procurement-SCM Reports'
    )


# ============================================================
# WAREHOUSE & LOGISTICS LINKAGE
# ============================================================

@scm_bp.route('/warehouse')
@scm_permission_required('scm', 'warehouse')
def warehouse_linkage():
    """Warehouse and logistics linkage main page."""
    db = get_db()
    
    warehouses = db.execute("""
        SELECT w.*,
               COALESCE(SUM(ib.quantity), 0) as total_stock
        FROM wms_warehouses w
        LEFT JOIN wms_inventory_balances ib ON w.id = ib.warehouse_id
        WHERE w.is_active = 1
        GROUP BY w.id
    """).fetchall()
    
    return render_template('scm/warehouse/index.html',
        title='Warehouse & Logistics Linkage',
        warehouses=warehouses
    )


@scm_bp.route('/warehouse/coverage')
@scm_permission_required('scm', 'warehouse')
def warehouse_coverage():
    """Warehouse coverage view."""
    db = get_db()
    
    coverage = db.execute("""
        SELECT w.name as warehouse_name,
               COALESCE(SUM(ib.quantity), 0) as current_stock,
               COALESCE((SELECT SUM(quantity - COALESCE(received_quantity, 0))
                        FROM wms_inbound_receipts
                        WHERE warehouse_id = w.id AND status IN ('APPROVED', 'SENT', 'IN_TRANSIT')), 0) as in_transit,
               COALESCE((SELECT SUM(sales_quantity + consumption_quantity)
                        FROM planning_demand_history
                        WHERE warehouse_id = w.id AND period_start >= DATE('now', '-30 days')), 0) as demand_30d
        FROM wms_warehouses w
        LEFT JOIN wms_inventory_balances ib ON w.id = ib.warehouse_id
        WHERE w.is_active = 1
        GROUP BY w.id
    """).fetchall()
    
    return render_template('scm/warehouse/coverage.html',
        title='Warehouse Coverage',
        coverage=coverage
    )


@scm_bp.route('/warehouse/in-transit')
@scm_permission_required('scm', 'warehouse')
def warehouse_in_transit():
    """In-transit stock view."""
    db = get_db()
    
    in_transit = db.execute("""
        SELECT ir.*, i.item_code, i.name as item_name,
               w.name as warehouse_name,
               s.name as supplier_name
        FROM wms_inbound_receipts ir
        JOIN wms_items i ON ir.item_id = i.id
        LEFT JOIN wms_warehouses w ON ir.warehouse_id = w.id
        LEFT JOIN suppliers s ON ir.supplier_id = s.id
        WHERE ir.status IN ('APPROVED', 'SENT', 'IN_TRANSIT')
        ORDER BY ir.expected_arrival_date
    """).fetchall()
    
    return render_template('scm/warehouse/in_transit.html',
        title='In-Transit Stock',
        in_transit=in_transit
    )


@scm_bp.route('/warehouse/transfer-pipeline')
@scm_permission_required('scm', 'warehouse')
def warehouse_transfer_pipeline():
    """Transfer pipeline view."""
    db = get_db()
    
    transfers = db.execute("""
        SELECT t.*, i.item_code, i.name as item_name,
               sw.name as source, dw.name as destination
        FROM planning_transfer_recommendations t
        JOIN wms_items i ON t.item_id = i.id
        LEFT JOIN wms_warehouses sw ON t.source_warehouse_id = sw.id
        LEFT JOIN wms_warehouses dw ON t.destination_warehouse_id = dw.id
        WHERE t.status IN ('OPEN', 'APPROVED')
        ORDER BY t.created_at DESC
    """).fetchall()
    
    return render_template('scm/warehouse/transfer_pipeline.html',
        title='Transfer Pipeline',
        transfers=transfers
    )


@scm_bp.route('/warehouse/dispatch-risk')
@scm_permission_required('scm', 'warehouse')
def warehouse_dispatch_risk():
    """Dispatch risk affecting service level."""
    db = get_db()
    
    dispatch_risks = db.execute("""
        SELECT d.*, i.item_code, i.name as item_name,
               w.name as warehouse_name
        FROM wms_dispatch_plans d
        JOIN wms_dispatch_plan_lines dl ON d.id = dl.dispatch_plan_id
        JOIN wms_items i ON dl.item_id = i.id
        LEFT JOIN wms_warehouses w ON d.warehouse_id = w.id
        WHERE d.status IN ('CONFIRMED', 'PICKING', 'PACKING')
        AND d.scheduled_date <= DATE('now', '+3 days')
        ORDER BY d.scheduled_date
        LIMIT 30
    """).fetchall()
    
    return render_template('scm/warehouse/dispatch_risk.html',
        title='Dispatch Risk',
        dispatch_risks=dispatch_risks
    )


@scm_bp.route('/warehouse/reports')
@scm_permission_required('scm', 'reports')
def warehouse_reports():
    """Warehouse-SCM reports."""
    return render_template('scm/warehouse/reports.html',
        title='Warehouse-SCM Reports'
    )


# ============================================================
# REPORTS & ANALYTICS
# ============================================================

@scm_bp.route('/reports')
@scm_permission_required('scm', 'reports')
def reports_center():
    """SCM Reports center."""
    return render_template('scm/reports/index.html',
        title='SCM Reports & Analytics'
    )


@scm_bp.route('/reports/demand')
@scm_permission_required('scm', 'reports')
def report_demand():
    """Demand report."""
    db = get_db()
    
    demand_data = db.execute("""
        SELECT i.item_code, i.name,
               COALESCE(SUM(dh.sales_quantity + dh.consumption_quantity), 0) as total_demand,
               COALESCE(AVG(dh.sales_quantity + dh.consumption_quantity), 0) as avg_demand
        FROM planning_demand_history dh
        RIGHT JOIN wms_items i ON dh.item_id = i.id
        WHERE i.is_active = 1
        AND dh.period_start >= DATE('now', '-30 days')
        GROUP BY i.id
        ORDER BY total_demand DESC
    """).fetchall()
    
    return render_template('scm/reports/demand_report.html',
        title='Demand Report',
        demand_data=demand_data
    )


@scm_bp.route('/reports/supply')
@scm_permission_required('scm', 'reports')
def report_supply():
    """Supply report."""
    db = get_db()
    
    supply_data = db.execute("""
        SELECT i.item_code, i.name,
               COALESCE(ib.quantity, 0) as current_stock,
               COALESCE((SELECT SUM(quantity - COALESCE(received_quantity, 0))
                        FROM wms_inbound_receipts
                        WHERE item_id = i.id AND status IN ('APPROVED', 'SENT', 'IN_TRANSIT')), 0) as in_transit
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        WHERE i.is_active = 1
        ORDER BY current_stock ASC
    """).fetchall()
    
    return render_template('scm/reports/supply_report.html',
        title='Supply Report',
        supply_data=supply_data
    )


@scm_bp.route('/reports/replenishment')
@scm_permission_required('scm', 'reports')
def report_replenishment():
    """Replenishment report."""
    db = get_db()
    
    repl_data = db.execute("""
        SELECT r.*, i.item_code, i.name as item_name
        FROM planning_replenishment_recommendations r
        JOIN wms_items i ON r.item_id = i.id
        ORDER BY r.created_at DESC
        LIMIT 100
    """).fetchall()
    
    return render_template('scm/reports/replenishment_report.html',
        title='Replenishment Report',
        repl_data=repl_data
    )


@scm_bp.route('/reports/inventory')
@scm_permission_required('scm', 'reports')
def report_inventory():
    """Inventory optimization report."""
    db = get_db()
    
    inv_data = db.execute("""
        SELECT i.item_code, i.name,
               COALESCE(ib.quantity, 0) as current_stock,
               ip.abc_class, ip.xyz_class
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
        WHERE i.is_active = 1
        ORDER BY i.item_code
    """).fetchall()
    
    return render_template('scm/reports/inventory_report.html',
        title='Inventory Report',
        inv_data=inv_data
    )


@scm_bp.route('/reports/service-level')
@scm_permission_required('scm', 'reports')
def report_service_level():
    """Service level report."""
    return render_template('scm/reports/service_level_report.html',
        title='Service Level Report'
    )


@scm_bp.route('/reports/exceptions')
@scm_permission_required('scm', 'reports')
def report_exceptions():
    """Exception report."""
    db = get_db()
    
    exceptions = db.execute("""
        SELECT a.*, i.item_code, i.name as item_name
        FROM planning_alerts a
        LEFT JOIN wms_items i ON a.item_id = i.id
        ORDER BY a.created_at DESC
        LIMIT 100
    """).fetchall()
    
    return render_template('scm/reports/exception_report.html',
        title='Exception Report',
        exceptions=exceptions
    )


@scm_bp.route('/reports/branch')
@scm_permission_required('scm', 'reports')
def report_branch():
    """Branch SCM report."""
    db = get_db()
    
    branches = db.execute("""
        SELECT c.name,
               COALESCE((SELECT SUM(quantity) FROM wms_inventory_balances WHERE company_id = c.id), 0) as stock,
               COALESCE((SELECT SUM(sales_quantity + consumption_quantity) 
                        FROM planning_demand_history WHERE company_id = c.id 
                        AND period_start >= DATE('now', '-30 days')), 0) as demand
        FROM companies c
        WHERE c.is_active = 1
    """).fetchall()
    
    return render_template('scm/reports/branch_report.html',
        title='Branch SCM Report',
        branches=branches
    )


@scm_bp.route('/reports/custom')
@scm_permission_required('scm', 'reports')
def report_custom():
    """Custom report builder."""
    return render_template('scm/reports/custom.html',
        title='Custom Report Builder'
    )


# ============================================================
# EXPORT CENTER
# ============================================================

@scm_bp.route('/export')
@scm_permission_required('scm', 'reports')
def export_center():
    """Export center for SCM data."""
    return render_template('scm/export/index.html',
        title='Export Center'
    )


@scm_bp.route('/export/demand', methods=['GET', 'POST'])
@scm_permission_required('scm', 'reports')
def export_demand():
    """Export demand data."""
    db = get_db()
    
    if request.method == 'POST':
        format_type = request.form.get('format', 'csv')
        
        data = db.execute("""
            SELECT i.item_code, i.name,
                   dh.period_start, dh.sales_quantity, dh.consumption_quantity,
                   dh.sales_quantity + dh.consumption_quantity as total_demand
            FROM planning_demand_history dh
            JOIN wms_items i ON dh.item_id = i.id
            WHERE dh.period_start >= DATE('now', '-12 months')
            ORDER BY i.item_code, dh.period_start
        """).fetchall()
        
        if format_type == 'csv':
            csv_output = "item_code,item_name,period_start,sales_qty,consumption_qty,total_demand\n"
            for row in data:
                csv_output += f"{row['item_code']},{row['name']},{row['period_start']},{row['sales_quantity']},{row['consumption_quantity']},{row['total_demand']}\n"
            
            return Response(
                csv_output,
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=demand_export.csv'}
            )
        elif format_type == 'excel':
            # For Excel, return CSV with Excel MIME type (simplified)
            csv_output = "item_code,item_name,period_start,sales_qty,consumption_qty,total_demand\n"
            for row in data:
                csv_output += f"{row['item_code']},{row['name']},{row['period_start']},{row['sales_quantity']},{row['consumption_quantity']},{row['total_demand']}\n"
            
            return Response(
                csv_output,
                mimetype='application/vnd.ms-excel',
                headers={'Content-Disposition': 'attachment; filename=demand_export.xls'}
            )
    
    return render_template('scm/export/demand.html',
        title='Export Demand Data'
    )


@scm_bp.route('/export/supply', methods=['GET', 'POST'])
@scm_permission_required('scm', 'reports')
def export_supply():
    """Export supply data."""
    db = get_db()
    
    if request.method == 'POST':
        format_type = request.form.get('format', 'csv')
        include_po = request.form.get('include_po', 'yes')
        
        # Build query based on options
        query = """
            SELECT i.item_code, i.name as item_name,
                   COALESCE(ib.quantity, 0) as current_stock,
                   COALESCE(ir.quantity, 0) as in_transit_qty,
                   COALESCE(ip.lead_time_days, 0) as lead_time_days,
                   COALESCE(ip.reorder_point, 0) as reorder_point,
                   s.name as supplier_name,
                   COALESCE(pov.quantity, 0) as open_po_qty,
                   COALESCE(pov.expected_date, 'N/A') as expected_date
            FROM wms_items i
            LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
            LEFT JOIN wms_inbound_receipts ir ON i.id = ir.item_id AND ir.status IN ('APPROVED', 'SENT', 'IN_TRANSIT')
            LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
            LEFT JOIN suppliers s ON i.default_supplier_id = s.id
            LEFT JOIN (
                SELECT item_id, SUM(quantity) as quantity, MAX(expected_date) as expected_date
                FROM procurement_order_values
                WHERE status IN ('APPROVED', 'SENT')
                GROUP BY item_id
            ) pov ON i.id = pov.item_id
            WHERE i.is_active = 1
            ORDER BY i.item_code
        """
        
        data = db.execute(query).fetchall()
        
        if format_type == 'csv':
            csv_output = "item_code,item_name,current_stock,in_transit,lead_time,reorder_point,supplier,open_po_qty,expected_date\n"
            for row in data:
                csv_output += f"{row['item_code']},{row['item_name']},{row['current_stock']},{row['in_transit_qty']},{row['lead_time_days']},{row['reorder_point']},{row['supplier_name'] or ''},{row['open_po_qty']},{row['expected_date']}\n"
            
            return Response(
                csv_output,
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=supply_export.csv'}
            )
        elif format_type == 'excel':
            csv_output = "item_code,item_name,current_stock,in_transit,lead_time,reorder_point,supplier,open_po_qty,expected_date\n"
            for row in data:
                csv_output += f"{row['item_code']},{row['item_name']},{row['current_stock']},{row['in_transit_qty']},{row['lead_time_days']},{row['reorder_point']},{row['supplier_name'] or ''},{row['open_po_qty']},{row['expected_date']}\n"
            
            return Response(
                csv_output,
                mimetype='application/vnd.ms-excel',
                headers={'Content-Disposition': 'attachment; filename=supply_export.xls'}
            )
    
    return render_template('scm/export/supply.html',
        title='Export Supply Data'
    )


@scm_bp.route('/export/replenishment', methods=['GET', 'POST'])
@scm_permission_required('scm', 'reports')
def export_replenishment():
    """Export replenishment data."""
    db = get_db()
    
    if request.method == 'POST':
        format_type = request.form.get('format', 'csv')
        
        data = db.execute("""
            SELECT r.id, i.item_code, i.name as item_name,
                   r.recommended_quantity, r.recommended_date,
                   r.priority, r.status, r.created_at,
                   w.name as warehouse_name,
                   COALESCE(ib.quantity, 0) as current_stock,
                   COALESCE(ip.reorder_point, 0) as reorder_point
            FROM planning_replenishment_recommendations r
            JOIN wms_items i ON r.item_id = i.id
            LEFT JOIN warehouses w ON r.warehouse_id = w.id
            LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id AND ib.warehouse_id = r.warehouse_id
            LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
            WHERE r.status = 'OPEN'
            ORDER BY r.priority DESC, r.created_at DESC
        """).fetchall()
        
        if format_type == 'csv':
            csv_output = "id,item_code,item_name,warehouse,current_stock,reorder_point,rec_qty,rec_date,priority,status,created\n"
            for row in data:
                csv_output += f"{row['id']},{row['item_code']},{row['item_name']},{row['warehouse_name']},{row['current_stock']},{row['reorder_point']},{row['recommended_quantity']},{row['recommended_date']},{row['priority']},{row['status']},{row['created_at']}\n"
            
            return Response(
                csv_output,
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=replenishment_export.csv'}
            )
        elif format_type == 'excel':
            csv_output = "id,item_code,item_name,warehouse,current_stock,reorder_point,rec_qty,rec_date,priority,status,created\n"
            for row in data:
                csv_output += f"{row['id']},{row['item_code']},{row['item_name']},{row['warehouse_name']},{row['current_stock']},{row['reorder_point']},{row['recommended_quantity']},{row['recommended_date']},{row['priority']},{row['status']},{row['created_at']}\n"
            
            return Response(
                csv_output,
                mimetype='application/vnd.ms-excel',
                headers={'Content-Disposition': 'attachment; filename=replenishment_export.xls'}
            )
    
    return render_template('scm/export/replenishment.html',
        title='Export Replenishment Data'
    )


@scm_bp.route('/export/inventory', methods=['GET', 'POST'])
@scm_permission_required('scm', 'reports')
def export_inventory():
    """Export inventory data."""
    db = get_db()
    
    if request.method == 'POST':
        format_type = request.form.get('format', 'csv')
        
        data = db.execute("""
            SELECT i.item_code, i.name as item_name,
                   COALESCE(ib.quantity, 0) as quantity,
                   COALESCE(ib.reserved_quantity, 0) as reserved,
                   COALESCE(ib.available_quantity, 0) as available,
                   COALESCE(i.unit_cost, 0) as unit_cost,
                   COALESCE(ib.quantity * i.unit_cost, 0) as total_value,
                   COALESCE(ip.min_stock, 0) as min_stock,
                   COALESCE(ip.max_stock, 0) as max_stock,
                   COALESCE(ip.reorder_point, 0) as reorder_point,
                   COALESCE(ip.safety_stock, 0) as safety_stock,
                   c.name as category,
                   w.name as warehouse
            FROM wms_items i
            LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
            LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
            LEFT JOIN categories c ON i.category_id = c.id
            LEFT JOIN warehouses w ON ib.warehouse_id = w.id
            WHERE i.is_active = 1
            ORDER BY i.item_code, w.name
        """).fetchall()
        
        if format_type == 'csv':
            csv_output = "item_code,item_name,warehouse,category,quantity,reserved,available,unit_cost,total_value,min,max,reorder_point,safety_stock\n"
            for row in data:
                csv_output += f"{row['item_code']},{row['item_name']},{row['warehouse'] or ''},{row['category'] or ''},{row['quantity']},{row['reserved']},{row['available']},{row['unit_cost']},{row['total_value']},{row['min_stock']},{row['max_stock']},{row['reorder_point']},{row['safety_stock']}\n"
            
            return Response(
                csv_output,
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=inventory_export.csv'}
            )
        elif format_type == 'excel':
            csv_output = "item_code,item_name,warehouse,category,quantity,reserved,available,unit_cost,total_value,min,max,reorder_point,safety_stock\n"
            for row in data:
                csv_output += f"{row['item_code']},{row['item_name']},{row['warehouse'] or ''},{row['category'] or ''},{row['quantity']},{row['reserved']},{row['available']},{row['unit_cost']},{row['total_value']},{row['min_stock']},{row['max_stock']},{row['reorder_point']},{row['safety_stock']}\n"
            
            return Response(
                csv_output,
                mimetype='application/vnd.ms-excel',
                headers={'Content-Disposition': 'attachment; filename=inventory_export.xls'}
            )
    
    return render_template('scm/export/inventory.html',
        title='Export Inventory Data'
    )


@scm_bp.route('/export/configure', methods=['GET', 'POST'])
@scm_permission_required('scm', 'reports')
def export_configure():
    """Configure export settings."""
    db = get_db()
    
    if request.method == 'POST':
        # Save export configuration
        export_format = request.form.get('default_format', 'csv')
        include_headers = request.form.get('include_headers', 'yes')
        date_format = request.form.get('date_format', 'YYYY-MM-DD')
        decimal_separator = request.form.get('decimal_separator', '.')
        
        # Store in session or database
        session['export_config'] = {
            'format': export_format,
            'include_headers': include_headers == 'yes',
            'date_format': date_format,
            'decimal_separator': decimal_separator
        }
        
        flash('Export configuration saved successfully', 'success')
        return redirect(url_for('scm.export_configure'))
    
    config = session.get('export_config', {
        'format': 'csv',
        'include_headers': True,
        'date_format': 'YYYY-MM-DD',
        'decimal_separator': '.'
    })
    
    return render_template('scm/export/configure.html',
        title='Configure Export Settings',
        config=config
    )


# ============================================================
# WORKFLOW & APPROVALS
# ============================================================

@scm_bp.route('/workflow')
@scm_permission_required('scm', 'workflow')
def workflow_approvals():
    """Workflow and approvals main page."""
    return render_template('scm/workflow/index.html',
        title='Workflow & Approvals'
    )


@scm_bp.route('/workflow/pending')
@scm_permission_required('scm', 'workflow')
def workflow_pending():
    """Pending approvals queue."""
    db = get_db()
    
    pending_repl = db.execute("""
        SELECT 'Replenishment' as type, r.id, r.created_at, i.item_code, r.recommended_quantity as qty
        FROM planning_replenishment_recommendations r
        JOIN wms_items i ON r.item_id = i.id
        WHERE r.status = 'OPEN'
        UNION ALL
        SELECT 'Purchase' as type, p.id, p.created_at, i.item_code, p.recommended_quantity as qty
        FROM planning_purchase_recommendations p
        JOIN wms_items i ON p.item_id = i.id
        WHERE p.status = 'OPEN'
        ORDER BY created_at DESC
    """).fetchall()
    
    return render_template('scm/workflow/pending.html',
        title='Pending Approvals',
        pending=pending_repl
    )


@scm_bp.route('/workflow/history')
@scm_permission_required('scm', 'workflow')
def workflow_history():
    """Approval history."""
    db = get_db()
    
    history = db.execute("""
        SELECT a.*, u.username as approved_by_name
        FROM planning_audit_log a
        LEFT JOIN users u ON a.user_id = u.id
        WHERE a.action_type LIKE '%APPROVED%' OR a.action_type LIKE '%DISMISSED%'
        ORDER BY a.created_at DESC
        LIMIT 50
    """).fetchall()
    
    return render_template('scm/workflow/history.html',
        title='Approval History',
        history=history
    )


# ============================================================
# SETTINGS
# ============================================================

@scm_bp.route('/settings')
@scm_permission_required('scm', 'settings')
def scm_settings():
    """SCM Settings main page."""
    db = get_db()
    
    settings = get_scm_settings(db)
    
    return render_template('scm/settings/index.html',
        title='SCM Settings',
        settings=settings
    )


@scm_bp.route('/settings/forecast-rules')
@scm_permission_required('scm', 'settings')
def settings_forecast_rules():
    """Forecast rules configuration."""
    db = get_db()
    
    policies = db.execute("""
        SELECT * FROM planning_policies
        WHERE policy_type = 'FORECAST' AND is_active = 1
    """).fetchall()
    
    return render_template('scm/settings/forecast_rules.html',
        title='Forecast Rules',
        policies=policies
    )


@scm_bp.route('/settings/replenishment-rules')
@scm_permission_required('scm', 'settings')
def settings_replenishment_rules():
    """Replenishment rules configuration."""
    db = get_db()
    
    policies = db.execute("""
        SELECT * FROM planning_policies
        WHERE policy_type = 'REPLENISHMENT' AND is_active = 1
    """).fetchall()
    
    return render_template('scm/settings/replenishment_rules.html',
        title='Replenishment Rules',
        policies=policies
    )


@scm_bp.route('/settings/service-level-settings')
@scm_permission_required('scm', 'settings')
def settings_service_level():
    """Service level settings."""
    db = get_db()
    
    return render_template('scm/settings/service_level.html',
        title='Service Level Settings'
    )


@scm_bp.route('/settings/lead-time-settings')
@scm_permission_required('scm', 'settings')
def settings_lead_time():
    """Lead time settings."""
    db = get_db()
    
    return render_template('scm/settings/lead_time.html',
        title='Lead Time Settings'
    )


@scm_bp.route('/settings/exception-thresholds')
@scm_permission_required('scm', 'settings')
def settings_exception_thresholds():
    """Exception threshold settings."""
    db = get_db()
    
    return render_template('scm/settings/exception_thresholds.html',
        title='Exception Thresholds'
    )


@scm_bp.route('/settings/export-settings')
@scm_permission_required('scm', 'settings')
def settings_export():
    """Export settings."""
    return render_template('scm/settings/export.html',
        title='Export Settings'
    )


@scm_bp.route('/settings/branch-entity')
@scm_permission_required('scm', 'settings')
def settings_branch_entity():
    """Branch/Entity settings."""
    db = get_db()
    
    branches = db.execute("SELECT id, name, code FROM companies WHERE is_active = 1").fetchall()
    
    return render_template('scm/settings/branch_entity.html',
        title='Branch/Entity Settings',
        branches=branches
    )


@scm_bp.route('/settings/notification-settings')
@scm_permission_required('scm', 'settings')
def settings_notifications():
    """Notification settings."""
    return render_template('scm/settings/notifications.html',
        title='Notification Settings'
    )


@scm_bp.route('/settings/save', methods=['POST'])
@scm_permission_required('scm', 'settings')
def scm_settings_save():
    """Save SCM settings."""
    db = get_db()
    
    for key, value in request.form.items():
        if key.startswith('setting_'):
            setting_key = key.replace('setting_', '')
            existing = db.execute(
                "SELECT id FROM planning_settings WHERE setting_key = ?", (setting_key,)
            ).fetchone()
            
            if existing:
                db.execute(
                    "UPDATE planning_settings SET setting_value = ?, updated_at = CURRENT_TIMESTAMP WHERE setting_key = ?",
                    (value, setting_key)
                )
            else:
                db.execute(
                    "INSERT INTO planning_settings (setting_key, setting_value, setting_type, category) VALUES (?, ?, 'STRING', 'SCM')",
                    (setting_key, value)
                )
    
    db.commit()
    
    log_scm_audit(db, 'SETTINGS_UPDATED', 'settings', None,
                   user_id=session.get('user_id'))
    
    flash('Settings saved.', 'success')
    return redirect(url_for('scm.scm_settings'))


# ============================================================
# CONTROL TOWER & PLANNING WORKSPACE
# ============================================================

@scm_bp.route('/control-tower')
@scm_permission_required('scm', 'dashboard')
def control_tower():
    """SCM Control Tower - Global Supply Chain Visibility."""
    db = get_db()
    
    # Critical shortages
    shortages = db.execute("""
        SELECT a.*, i.item_code, i.name as item_name,
               COALESCE(ib.quantity, 0) as current_stock
        FROM planning_alerts a
        LEFT JOIN wms_items i ON a.item_id = i.id
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        WHERE a.alert_type IN ('STOCKOUT', 'SHORTAGE')
        AND a.is_acknowledged = 0
        ORDER BY a.priority DESC, a.created_at DESC
        LIMIT 20
    """).fetchall()
    
    # Overstock items
    overstocks = db.execute("""
        SELECT a.*, i.item_code, i.name as item_name,
               COALESCE(ib.quantity, 0) as current_stock
        FROM planning_alerts a
        LEFT JOIN wms_items i ON a.item_id = i.id
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        WHERE a.alert_type = 'OVERSTOCK'
        AND a.is_acknowledged = 0
        ORDER BY a.priority DESC
        LIMIT 20
    """).fetchall()
    
    # Urgent actions
    urgent_actions = db.execute("""
        SELECT COUNT(*) as cnt FROM planning_alerts
        WHERE is_acknowledged = 0 AND priority = 'HIGH'
    """).fetchone()['cnt']
    
    # Delayed supply
    delayed_supply = db.execute("""
        SELECT COUNT(*) as cnt FROM procurement_order_values
        WHERE status IN ('APPROVED', 'SENT')
        AND expected_date < DATE('now')
    """).fetchone()['cnt']
    
    # Service level breaches
    service_breaches = db.execute("""
        SELECT COUNT(*) as cnt FROM planning_alerts
        WHERE alert_type = 'SERVICE_BREACH'
        AND is_acknowledged = 0
    """).fetchone()['cnt']
    
    return render_template('scm/dashboard/control_tower.html',
        title='SCM Control Tower',
        shortages=shortages,
        overstocks=overstocks,
        urgent_actions=urgent_actions,
        delayed_supply=delayed_supply,
        service_breaches=service_breaches
    )


@scm_bp.route('/workspace')
@scm_permission_required('scm', 'dashboard')
def planning_workspace():
    """SCM Planning Workspace."""
    db = get_db()
    
    # Active forecasts
    active_forecasts = db.execute("""
        SELECT f.*, COUNT(dh.id) as data_points
        FROM planning_forecast_runs f
        LEFT JOIN planning_demand_history dh ON f.id = dh.forecast_run_id
        WHERE f.status = 'ACTIVE'
        GROUP BY f.id
        ORDER BY f.created_at DESC
        LIMIT 10
    """).fetchall()
    
    # Open replenishment
    open_replenishment = db.execute("""
        SELECT COUNT(*) as cnt FROM planning_replenishment_recommendations
        WHERE status = 'OPEN'
    """).fetchone()['cnt']
    
    # MRP exceptions
    mrp_exceptions = db.execute("""
        SELECT COUNT(*) as cnt FROM planning_alerts
        WHERE alert_type IN ('MRP_EXCEPTION', 'RESCHEDULE')
        AND is_acknowledged = 0
    """).fetchone()['cnt']
    
    # Pending approvals
    pending_approvals = db.execute("""
        SELECT COUNT(*) as cnt FROM planning_replenishment_recommendations
        WHERE status = 'PENDING_APPROVAL'
    """).fetchone()['cnt']
    
    return render_template('scm/dashboard/workspace.html',
        title='Planning Workspace',
        active_forecasts=active_forecasts,
        open_replenishment=open_replenishment,
        mrp_exceptions=mrp_exceptions,
        pending_approvals=pending_approvals
    )


# ============================================================
# DEMAND - ADDITIONAL ROUTES
# ============================================================

@scm_bp.route('/demand/by-brand')
@scm_permission_required('scm', 'demand')
def demand_by_brand():
    """Demand forecast by brand."""
    db = get_db()
    
    brands = db.execute("""
        SELECT i.brand, COALESCE(SUM(dh.sales_quantity), 0) as total_sales,
               COALESCE(AVG(dh.sales_quantity), 0) as avg_sales,
               COUNT(DISTINCT i.id) as item_count
        FROM wms_items i
        LEFT JOIN planning_demand_history dh ON i.id = dh.item_id
        WHERE i.is_active = 1 AND i.brand IS NOT NULL
        GROUP BY i.brand
        ORDER BY total_sales DESC
    """).fetchall()
    
    return render_template('scm/demand/forecast_by_brand.html',
        title='Forecast by Brand',
        brands=brands
    )


@scm_bp.route('/demand/by-customer-segment')
@scm_permission_required('scm', 'demand')
def demand_by_customer_segment():
    """Demand forecast by customer segment."""
    db = get_db()
    
    segments = db.execute("""
        SELECT COALESCE(c.customer_type, 'RETAIL') as segment,
               COALESCE(SUM(dh.sales_quantity), 0) as total_sales,
               COALESCE(AVG(dh.sales_quantity), 0) as avg_sales,
               COUNT(DISTINCT i.id) as item_count
        FROM wms_items i
        LEFT JOIN planning_demand_history dh ON i.id = dh.item_id
        LEFT JOIN customers c ON dh.customer_id = c.id
        WHERE i.is_active = 1
        GROUP BY c.customer_type
        ORDER BY total_sales DESC
    """).fetchall()
    
    return render_template('scm/demand/forecast_by_customer_segment.html',
        title='Forecast by Customer Segment',
        segments=segments
    )


# ============================================================
# SUPPLY - ADDITIONAL ROUTES
# ============================================================

@scm_bp.route('/supply/by-item')
@scm_permission_required('scm', 'supply')
def supply_by_item():
    """Supply by item view."""
    db = get_db()
    
    items = db.execute("""
        SELECT i.id, i.item_code, i.name as item_name,
               COALESCE(ib.quantity, 0) as current_stock,
               COALESCE(pov.quantity, 0) as on_order,
               COALESCE(it.quantity, 0) as in_transit,
               COALESCE(ip.lead_time_days, 0) as lead_time
        FROM wms_items i
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
        LEFT JOIN (
            SELECT item_id, SUM(quantity) as quantity
            FROM procurement_order_values
            WHERE status IN ('APPROVED', 'SENT')
            GROUP BY item_id
        ) pov ON i.id = pov.item_id
        LEFT JOIN (
            SELECT item_id, SUM(quantity) as quantity
            FROM logistics_trip_stops
            WHERE status = 'IN_TRANSIT'
            GROUP BY item_id
        ) it ON i.id = it.item_id
        LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
        WHERE i.is_active = 1
        ORDER BY (COALESCE(ib.quantity, 0) + COALESCE(pov.quantity, 0)) ASC
    """).fetchall()
    
    return render_template('scm/supply/by_item.html',
        title='Supply by Item',
        items=items
    )


@scm_bp.route('/supply/by-warehouse')
@scm_permission_required('scm', 'supply')
def supply_by_warehouse():
    """Supply by warehouse view."""
    db = get_db()
    
    warehouses = db.execute("""
        SELECT w.id, w.name as warehouse_name,
               COUNT(DISTINCT ib.item_id) as item_count,
               COALESCE(SUM(ib.quantity), 0) as total_stock,
               COALESCE((SELECT SUM(quantity) FROM logistics_trip_stops WHERE warehouse_id = w.id AND status = 'IN_TRANSIT'), 0) as in_transit
        FROM warehouses w
        LEFT JOIN wms_inventory_balances ib ON w.id = ib.warehouse_id
        WHERE w.is_active = 1
        GROUP BY w.id
        ORDER BY total_stock DESC
    """).fetchall()
    
    return render_template('scm/supply/by_warehouse.html',
        title='Supply by Warehouse',
        warehouses=warehouses
    )


@scm_bp.route('/supply/allocation')
@scm_permission_required('scm', 'supply')
def supply_allocation():
    """Supply allocation planning."""
    db = get_db()
    
    allocations = db.execute("""
        SELECT i.item_code, i.name as item_name,
               w.name as warehouse_name,
               COALESCE(ib.quantity, 0) as current_stock,
               COALESCE(pd.sales_quantity, 0) as demand,
               CASE WHEN COALESCE(pd.sales_quantity, 0) > 0
                    THEN (COALESCE(ib.quantity, 0) / NULLIF(pd.sales_quantity, 0)) * 100
                    ELSE 100 END as coverage_pct
        FROM wms_items i
        CROSS JOIN warehouses w
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id AND w.id = ib.warehouse_id
        LEFT JOIN (
            SELECT item_id, SUM(sales_quantity) as sales_quantity
            FROM planning_demand_history
            WHERE period_start >= DATE('now', '-30 days')
            GROUP BY item_id
        ) pd ON i.id = pd.item_id
        WHERE w.is_active = 1 AND i.is_active = 1
        ORDER BY coverage_pct ASC
    """).fetchall()
    
    return render_template('scm/supply/allocation.html',
        title='Allocation Planning',
        allocations=allocations
    )


@scm_bp.route('/supply/scenarios')
@scm_permission_required('scm', 'supply')
def supply_scenarios():
    """Supply planning scenarios."""
    db = get_db()
    
    scenarios = db.execute("""
        SELECT s.*, u.username as created_by_name
        FROM planning_scenarios s
        LEFT JOIN users u ON s.created_by = u.id
        WHERE s.scenario_type = 'SUPPLY'
        ORDER BY s.created_at DESC
    """).fetchall()
    
    return render_template('scm/supply/scenarios.html',
        title='Supply Scenarios',
        scenarios=scenarios
    )


# ============================================================
# REPLENISHMENT - ADDITIONAL ROUTES
# ============================================================

@scm_bp.route('/replenishment/reorder')
@scm_permission_required('scm', 'replenishment')
def replenishment_reorder():
    """Reorder recommendations view."""
    db = get_db()
    
    recommendations = db.execute("""
        SELECT r.id, i.item_code, i.name as item_name,
               w.name as warehouse_name,
               COALESCE(ib.quantity, 0) as current_stock,
               COALESCE(ip.reorder_point, 0) as reorder_point,
               COALESCE(ip.min_quantity, 0) as min_qty,
               COALESCE(ip.max_quantity, 0) as max_qty,
               r.recommended_quantity,
               r.recommended_date,
               r.priority,
               r.status
        FROM planning_replenishment_recommendations r
        JOIN wms_items i ON r.item_id = i.id
        LEFT JOIN warehouses w ON r.warehouse_id = w.id
        LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id AND w.id = ib.warehouse_id
        LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
        WHERE r.recommendation_type = 'REORDER'
        AND r.status IN ('OPEN', 'PENDING_APPROVAL')
        ORDER BY r.priority DESC, r.created_at DESC
    """).fetchall()
    
    return render_template('scm/replenishment/reorder.html',
        title='Reorder Recommendations',
        recommendations=recommendations
    )


# ============================================================
# API ENDPOINTS
# ============================================================

@scm_bp.route('/api/dashboard-summary')
@scm_permission_required('scm', 'dashboard')
def api_dashboard_summary():
    """API endpoint for dashboard summary data."""
    db = get_db()
    
    summary = {
        'total_items': db.execute("SELECT COUNT(*) as cnt FROM wms_items WHERE is_active = 1").fetchone()['cnt'],
        'active_alerts': db.execute("SELECT COUNT(*) as cnt FROM planning_alerts WHERE is_acknowledged = 0").fetchone()['cnt'],
        'open_recommendations': db.execute("SELECT COUNT(*) as cnt FROM planning_replenishment_recommendations WHERE status = 'OPEN'").fetchone()['cnt'],
        'fill_rate': 0.95
    }
    
    return jsonify(summary)


@scm_bp.route('/api/net-requirement/<int:item_id>')
@scm_permission_required('scm', 'demand')
def api_net_requirement(item_id):
    """API endpoint for net requirement calculation."""
    db = get_db()
    
    from planning_models import calculate_net_requirement
    result = calculate_net_requirement(item_id, db)
    
    return jsonify(result or {})


# =============================================================================
# API EXPORT ENDPOINTS
# =============================================================================

@scm_bp.route('/api/export/<export_type>', methods=['GET', 'POST'])
@scm_bp.route('/api/export/<data_type>/<export_type>', methods=['GET', 'POST'])
@scm_permission_required('scm', 'view')
def api_scm_export(export_type, data_type=None):
    """Export SCM data in all 20 formats."""
    if export_type not in SCM_EXPORT_TYPES:
        return jsonify({
            'error': f'Invalid export type. Valid types: {SCM_EXPORT_TYPES}'
        }), 400

    db = get_db()
    company_id = session.get('company_id', 0)

    # Determine data type from URL or default
    if data_type is None:
        data_type = request.args.get('type', 'demand')

    # Get data based on type
    if data_type == 'demand':
        data = db.execute("""
            SELECT * FROM planning_demand_plans
            WHERE company_id = ?
            ORDER BY forecast_date DESC
            LIMIT 5000
        """, (company_id,)).fetchall()
        data = [dict(row) for row in data]
        columns = SCM_EXPORT_COLUMNS['demand']
        title = 'Demand Plans'
    elif data_type == 'supply':
        data = db.execute("""
            SELECT * FROM planning_supply_plans
            WHERE company_id = ?
            ORDER BY supply_date DESC
            LIMIT 5000
        """, (company_id,)).fetchall()
        data = [dict(row) for row in data]
        columns = SCM_EXPORT_COLUMNS['supply']
        title = 'Supply Plans'
    elif data_type == 'replenishment':
        data = db.execute("""
            SELECT * FROM planning_replenishment_recommendations
            WHERE company_id = ?
            ORDER BY created_at DESC
            LIMIT 5000
        """, (company_id,)).fetchall()
        data = [dict(row) for row in data]
        columns = SCM_EXPORT_COLUMNS['replenishment']
        title = 'Replenishment Recommendations'
    elif data_type == 'inventory':
        data = db.execute("""
            SELECT i.*, w.name as warehouse_name
            FROM wms_inventory i
            LEFT JOIN wms_warehouses w ON i.warehouse_id = w.id
            WHERE i.company_id = ?
            ORDER BY i.last_updated DESC
            LIMIT 5000
        """, (company_id,)).fetchall()
        data = [dict(row) for row in data]
        columns = SCM_EXPORT_COLUMNS['inventory']
        title = 'SCM Inventory'
    elif data_type == 'alerts':
        data = db.execute("""
            SELECT * FROM planning_alerts
            WHERE company_id = ?
            ORDER BY created_at DESC
            LIMIT 5000
        """, (company_id,)).fetchall()
        data = [dict(row) for row in data]
        columns = SCM_EXPORT_COLUMNS['alerts']
        title = 'Planning Alerts'
    else:
        return jsonify({'error': f'Data type {data_type} not supported'}), 400

    filename = f'scm_{data_type}_{datetime.now().strftime("%Y%m%d")}'

    return send_export_response(data, export_type, filename, columns, title)


@scm_bp.route('/api/export/list')
@scm_permission_required('scm', 'view')
def list_scm_export_types():
    """List available export types for SCM module."""
    return jsonify({
        'module': 'scm',
        'data_types': list(SCM_EXPORT_COLUMNS.keys()),
        'export_types': [{'type': t} for t in SCM_EXPORT_TYPES]
    })


def register_scm_routes(app, get_db):
    """Register SCM routes with the Flask app."""
    app.register_blueprint(scm_bp)
