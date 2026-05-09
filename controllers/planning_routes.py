"""
Planning Routes - Demand Forecasting & Inventory Planning System

Enterprise-grade planning system covering:
- Planning Dashboard
- Forecast Center (generation, review, override workflow)
- Demand Analysis
- Sales & Consumption Analysis
- Inventory Health
- Replenishment Planning
- Purchase Suggestions
- Transfer Suggestions
- Safety Stock & Reorder Rules
- Supplier & Lead Time Analysis
- Customer Demand Patterns
- Lost Sales & Service Risk
- Seasonality & Trend Analysis
- Exceptions & Alerts
- Scenarios & Simulations
- Reports & Analytics
- Planning Settings
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, Response
from functools import wraps
import sqlite3
import os
import json
import io
from datetime import datetime, timedelta, date
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from collections import defaultdict
import re

from permissions import user_has_permission


def register_planning_routes(app, get_db):
    """Register all Planning routes with the Flask app."""

    # ============================================================
    # DECORATORS & HELPERS
    # ============================================================

    def planning_permission_required(resource, action):
        """Decorator to check Planning permissions using central permissions system."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if 'user_id' not in session:
                    return redirect(url_for('login'))
                user_id = session.get('user_id')
                if not user_has_permission(user_id, 'planning', resource, action):
                    flash(f"Access denied. You need '{action}' permission on '{resource}'.", "error")
                    return redirect(url_for('planning_dashboard'))
                return f(*args, **kwargs)
            return decorated_function
        return decorator

    def get_planning_permissions(user_id=None):
        """Get Planning permissions for a user."""
        db = get_db()
        if user_id is None:
            user_id = session.get('user_id')

        role = db.execute('SELECT can_manage_users FROM roles WHERE id = ?',
                          (session.get('role_id'),)).fetchone()
        if role and role['can_manage_users']:
            return ['all']

        perms = db.execute('''
            SELECT permission_key FROM planning_user_permissions
            WHERE user_id = ?
        ''', (user_id,)).fetchall()
        return [p['permission_key'] for p in perms]

    def log_planning_audit(action_type, entity_type, entity_id=None,
                             item_id=None, warehouse_id=None, company_id=None,
                             user_id=None, changes=None, notes=None):
        """Log a Planning audit entry."""
        db = get_db()
        if user_id is None:
            user_id = session.get('user_id')
        changes_json = json.dumps(changes) if changes else None
        try:
            db.execute('''
                INSERT INTO planning_audit_log
                (action_type, entity_type, entity_id, item_id, warehouse_id, company_id,
                 user_id, changes_json, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (action_type, entity_type, entity_id, item_id, warehouse_id, company_id,
                  user_id, changes_json, notes))
            db.commit()
        except Exception as e:
            print(f"Planning audit log error: {e}")

    def get_item_name(item_id):
        """Get item name/code by ID."""
        db = get_db()
        item = db.execute("SELECT item_code, name FROM wms_items WHERE id = ?", (item_id,)).fetchone()
        if item:
            return f"{item['item_code']} - {item['name']}"
        return f"Item #{item_id}"

    def get_warehouse_name(warehouse_id):
        """Get warehouse name by ID."""
        db = get_db()
        wh = db.execute("SELECT name FROM wms_warehouses WHERE id = ?", (warehouse_id,)).fetchone()
        return wh['name'] if wh else f"Warehouse #{warehouse_id}"

    def get_supplier_name(supplier_id):
        """Get supplier name by ID."""
        db = get_db()
        sup = db.execute("SELECT name FROM suppliers WHERE id = ?", (supplier_id,)).fetchone()
        return sup['name'] if sup else f"Supplier #{supplier_id}"

    def get_company_name(company_id):
        """Get company name by ID."""
        db = get_db()
        co = db.execute("SELECT name FROM companies WHERE id = ?", (company_id,)).fetchone()
        return co['name'] if co else f"Company #{company_id}"

    def parse_date(date_str, default=None):
        """Parse date string safely."""
        if not date_str:
            return default
        try:
            return datetime.strptime(str(date_str), '%Y-%m-%d').date()
        except:
            try:
                return datetime.strptime(str(date_str), '%d/%m/%Y').date()
            except:
                return default

    # ============================================================
    # PLANNING DASHBOARD
    # ============================================================

    @app.route('/planning')
    @planning_permission_required('dashboard', 'view')
    def planning_dashboard():
        """Main Planning Dashboard."""

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        today = datetime.now().date()
        month_start = (today.replace(day=1)).strftime('%Y-%m-%d')
        quarter_start = (today - timedelta(days=90)).strftime('%Y-%m-%d')

        total_items = db.execute("SELECT COUNT(*) as cnt FROM wms_items WHERE is_active = 1").fetchone()['cnt']
        active_alerts = db.execute("SELECT COUNT(*) as cnt FROM planning_alerts WHERE is_acknowledged = 0").fetchone()['cnt']

        below_safety = db.execute("""
            SELECT COUNT(DISTINCT i.id) as cnt
            FROM wms_items i
            LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
            WHERE i.is_active = 1
              AND ib.quantity < COALESCE(i.safety_stock, 0)
              AND COALESCE(i.safety_stock, 0) > 0
        """).fetchone()['cnt']

        below_rop = db.execute("""
            SELECT COUNT(DISTINCT i.id) as cnt
            FROM wms_items i
            LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
            WHERE i.is_active = 1
              AND ib.quantity < COALESCE(i.reorder_point, 0)
              AND COALESCE(i.reorder_point, 0) > 0
              AND (COALESCE(i.safety_stock, 0) = 0 OR ib.quantity >= COALESCE(i.safety_stock, 0))
        """).fetchone()['cnt']

        zero_stock = db.execute("""
            SELECT COUNT(DISTINCT i.id) as cnt
            FROM wms_items i
            LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
            WHERE i.is_active = 1
              AND COALESCE(ib.quantity, 0) <= 0
        """).fetchone()['cnt']

        excess_stock = db.execute("""
            SELECT COUNT(DISTINCT i.id) as cnt
            FROM wms_items i
            LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
            WHERE i.is_active = 1
              AND ib.quantity > COALESCE(i.max_stock_level, 0) * 1.5
              AND COALESCE(i.max_stock_level, 0) > 0
        """).fetchone()['cnt']

        open_recommendations = db.execute("""
            SELECT COUNT(*) as cnt FROM planning_replenishment_recommendations
            WHERE status = 'OPEN'
        """).fetchone()['cnt']

        open_purchase_recs = db.execute("""
            SELECT COUNT(*) as cnt FROM planning_purchase_recommendations
            WHERE status = 'OPEN'
        """).fetchone()['cnt']

        pending_forecasts = db.execute("""
            SELECT COUNT(*) as cnt FROM planning_forecast_runs WHERE status = 'DRAFT'
        """).fetchone()['cnt']

        in_transit_value = db.execute("""
            SELECT SUM(COALESCE(irl.received_quantity, 0) * COALESCE(irl.unit_cost, 0)) as val
            FROM wms_inbound_receipts ir
            JOIN wms_inbound_receipt_lines irl ON ir.id = irl.receipt_id
            JOIN wms_items i ON irl.item_id = i.id
            WHERE ir.status IN ('IN_TRANSIT', 'RECEIVING', 'APPROVED')
        """).fetchone()['val'] or 0

        stockout_alerts = db.execute("""
            SELECT COUNT(*) as cnt FROM planning_alerts
            WHERE alert_type = 'STOCKOUT' AND is_acknowledged = 0
        """).fetchone()['cnt']

        dead_stock_count = db.execute("""
            SELECT COUNT(DISTINCT i.id) as cnt
            FROM wms_items i
            LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
            LEFT JOIN wms_inventory_ledger il ON i.id = il.item_id
            WHERE i.is_active = 1
              AND COALESCE(ib.quantity, 0) > 0
              AND il.created_at < DATE('now', '-365 days')
        """).fetchone()['cnt']

        recent_demand = db.execute("""
            SELECT SUM(sales_quantity + consumption_quantity) as total
            FROM planning_demand_history
            WHERE period_start >= ?
        """, (month_start,)).fetchone()['total'] or 0

        upcoming_stockout = db.execute("""
            SELECT COUNT(*) as cnt FROM planning_alerts
            WHERE alert_type IN ('STOCKOUT', 'STOCKOUT_RISK') AND is_acknowledged = 0
        """).fetchone()['cnt']

        top_shortage_items = [dict(r) for r in db.execute("""
            SELECT i.id, i.item_code, i.name,
                   COALESCE(ib.quantity, 0) as qty,
                   COALESCE(i.reorder_point, 0) as rop
            FROM wms_items i
            LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
            WHERE i.is_active = 1
              AND COALESCE(ib.quantity, 0) < COALESCE(i.reorder_point, 0)
            ORDER BY (COALESCE(i.reorder_point, 0) - COALESCE(ib.quantity, 0)) DESC
            LIMIT 10
        """).fetchall()]

        top_overstock_items = [dict(r) for r in db.execute("""
            SELECT i.id, i.item_code, i.name,
                   COALESCE(ib.quantity, 0) as qty,
                   COALESCE(i.max_stock_level, 0) as max_stock
            FROM wms_items i
            LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
            WHERE i.is_active = 1
              AND COALESCE(i.max_stock_level, 0) > 0
              AND COALESCE(ib.quantity, 0) > COALESCE(i.max_stock_level, 0) * 1.2
            ORDER BY (COALESCE(ib.quantity, 0) - COALESCE(i.max_stock_level, 0)) DESC
            LIMIT 10
        """).fetchall()]

        alert_breakdown = [dict(r) for r in db.execute("""
            SELECT alert_type, COUNT(*) as cnt
            FROM planning_alerts
            WHERE is_acknowledged = 0
            GROUP BY alert_type
        """).fetchall()]

        recent_alerts = [dict(r) for r in db.execute("""
            SELECT a.*, i.item_code, i.name as item_name
            FROM planning_alerts a
            LEFT JOIN wms_items i ON a.item_id = i.id
            WHERE a.is_acknowledged = 0
            ORDER BY a.created_at DESC
            LIMIT 20
        """).fetchall()]

        warehouse_list = [dict(r) for r in db.execute("SELECT id, name, code FROM wms_warehouses ORDER BY name").fetchall()]
        company_list = [dict(r) for r in db.execute("SELECT id, name FROM companies ORDER BY name").fetchall()]

        coverage_stats = []
        for days_range in [(7, '7 Days'), (14, '14 Days'), (30, '30 Days'), (60, '60 Days'), (90, '90 Days')]:
            items_covered = db.execute("""
                SELECT COUNT(*) as cnt FROM (
                    SELECT i.id,
                           COALESCE(ib.quantity, 0) as qty,
                           COALESCE(
                               (SELECT SUM(sales_quantity + consumption_quantity) / 30
                                FROM planning_demand_history
                                WHERE item_id = i.id AND period_start >= DATE('now', '-30 days')),
                               0) as daily_demand
                    FROM wms_items i
                    LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
                    WHERE i.is_active = 1 AND daily_demand > 0
                )
                WHERE qty >= daily_demand * ?
            """, (days_range[0],)).fetchone()['cnt']
            coverage_stats.append({'days': days_range[1], 'count': items_covered})

        return render_template('planning/dashboard.html',
            title='Planning Dashboard',
            total_items=total_items,
            active_alerts=active_alerts,
            below_safety=below_safety,
            below_rop=below_rop,
            zero_stock=zero_stock,
            excess_stock=excess_stock,
            open_recommendations=open_recommendations,
            open_purchase_recs=open_purchase_recs,
            pending_forecasts=pending_forecasts,
            in_transit_value=in_transit_value,
            stockout_alerts=stockout_alerts,
            dead_stock_count=dead_stock_count,
            recent_demand=recent_demand,
            upcoming_stockout=upcoming_stockout,
            top_shortage_items=top_shortage_items,
            top_overstock_items=top_overstock_items,
            alert_breakdown=alert_breakdown,
            recent_alerts=recent_alerts,
            warehouse_list=warehouse_list,
            company_list=company_list,
            coverage_stats=coverage_stats,
            user_preferences=user_prefs or {}
        )

    # ============================================================
    # FORECAST CENTER
    # ============================================================

    @app.route('/planning/forecast')
    @planning_permission_required('forecasts', 'view')
    def forecast_center():
        """Forecast Center - list forecast runs and generate new ones."""

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        runs = db.execute("""
            SELECT r.*,
                   u.username as created_by_name,
                   a.username as approved_by_name
            FROM planning_forecast_runs r
            LEFT JOIN users u ON r.created_by = u.id
            LEFT JOIN users a ON r.approved_by = a.id
            ORDER BY r.created_at DESC
            LIMIT 50
        """).fetchall()

        warehouse_list = db.execute("SELECT id, name, code FROM wms_warehouses ORDER BY name").fetchall()
        company_list = db.execute("SELECT id, name FROM companies ORDER BY name").fetchall()
        now = datetime.now()

        return render_template('planning/forecast_center.html',
            title='Forecast Center',
            runs=runs,
            warehouse_list=warehouse_list,
            company_list=company_list,
            now=now,
            user_preferences=user_prefs or {}
        )

    @app.route('/planning/forecast/generate', methods=['POST'])
    @planning_permission_required('forecasts', 'create')
    def forecast_generate():
        """Generate a new forecast run."""

        db = get_db()
        method = request.form.get('method', 'MOVING_AVERAGE')
        forecast_type = request.form.get('forecast_type', 'DEMAND')
        horizon_days = int(request.form.get('horizon_days', 30))
        period_type = request.form.get('period_type', 'daily')
        warehouse_id = request.form.get('warehouse_id')
        company_id = request.form.get('company_id')
        item_ids = request.form.getlist('item_ids')

        run_name = request.form.get('run_name') or f"Forecast {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        warehouse_id = int(warehouse_id) if warehouse_id and warehouse_id.isdigit() else None
        company_id = int(company_id) if company_id and company_id.isdigit() else None

        cursor = db.execute("""
            INSERT INTO planning_forecast_runs
            (run_name, forecast_type, method, horizon_days, period_type,
             warehouse_id, company_id, status, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'DRAFT', ?)
        """, (run_name, forecast_type, method, horizon_days, period_type,
              warehouse_id, company_id, session['user_id']))
        run_id = cursor.lastrowid
        db.commit()

        settings = get_planning_settings(db)
        months = int(settings.get('DEMAND_HISTORY_MONTHS', '12'))
        use_seasonality = settings.get('USE_SEASONALITY', '1') == '1'
        use_trend = settings.get('USE_TREND', '1') == '1'

        if item_ids:
            items_query = "SELECT id FROM wms_items WHERE is_active = 1 AND id IN ({})".format(
                ','.join('?' * len(item_ids))
            )
            items = db.execute(items_query, item_ids).fetchall()
        else:
            items = db.execute("SELECT id FROM wms_items WHERE is_active = 1").fetchall()

        forecast_start = datetime.now().date()
        total_demand = 0

        for item in items:
            item_id = item['id']
            demand_data = db.execute("""
                SELECT period_start,
                       (sales_quantity + consumption_quantity) as demand
                FROM planning_demand_history
                WHERE item_id = ?
                  AND period_start >= DATE('now', '-{} months')
                ORDER BY period_start ASC
            """.format(months), (item_id,)).fetchall()

            demand_values = [r['demand'] for r in demand_data]
            periods = [r['period_start'] for r in demand_data]

            if not demand_values:
                demand_values = [0] * 30
                periods = [(forecast_start + timedelta(days=i)).strftime('%Y-%m-%d')
                           for i in range(30)]

            forecast_values = []
            for day_offset in range(horizon_days):
                if method == 'MOVING_AVERAGE':
                    base = calculate_moving_average(demand_values, window=min(7, len(demand_values)))
                elif method == 'WEIGHTED_MA':
                    base = calculate_weighted_moving_average(demand_values)
                elif method == 'SEASONAL':
                    if len(demand_values) >= 12 and use_seasonality:
                        seasonal_idx = calculate_seasonal_index(demand_values, 12)
                        idx = day_offset % 12
                        seasonal_factor = seasonal_idx.get(idx, 1.0)
                    else:
                        seasonal_factor = 1.0
                    trend_slope, trend_intercept = calculate_trend(demand_values)
                    base = trend_intercept + trend_slope * (len(demand_values) + day_offset)
                    base *= seasonal_factor
                elif method == 'TREND':
                    slope, intercept = calculate_trend(demand_values)
                    base = intercept + slope * (len(demand_values) + day_offset)
                else:
                    base = calculate_moving_average(demand_values)

                final = max(0, base)
                forecast_values.append(final)

            if method == 'SEASONAL' and len(demand_values) >= 12 and use_seasonality:
                seasonal_idx = calculate_seasonal_index(demand_values, 12)
                for i, fv in enumerate(forecast_values):
                    sf = seasonal_idx.get(i % 12, 1.0)
                    forecast_values[i] = fv * sf

            for day_offset, fv in enumerate(forecast_values):
                period_start = (forecast_start + timedelta(days=day_offset)).strftime('%Y-%m-%d')
                db.execute("""
                    INSERT INTO planning_forecast_lines
                    (run_id, item_id, warehouse_id, company_id, period_start,
                     period_type, base_quantity, final_quantity, confidence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (run_id, item_id, warehouse_id, company_id, period_start,
                      period_type, fv, fv, 0.6))
                total_demand += fv

        db.execute("""
            UPDATE planning_forecast_runs
            SET total_items = ?, total_demand = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (len(items), total_demand, run_id))
        db.commit()

        log_planning_audit('FORECAST_GENERATED', 'forecast_run', run_id,
                           user_id=session['user_id'],
                           changes={'method': method, 'horizon_days': horizon_days,
                                    'items_count': len(items), 'total_demand': total_demand})

        flash(f'Forecast generated successfully: {len(items)} items, {horizon_days} days horizon', 'success')
        return redirect(url_for('forecast_detail', run_id=run_id))

    @app.route('/planning/forecast/<int:run_id>')
    @planning_permission_required('forecasts', 'view')
    def forecast_detail(run_id):
        """View forecast run details."""

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        run = db.execute("SELECT * FROM planning_forecast_runs WHERE id = ?", (run_id,)).fetchone()
        if not run:
            flash('Forecast run not found', 'error')
            return redirect(url_for('forecast_center'))

        lines = db.execute("""
            SELECT fl.*, i.item_code, i.name as item_name
            FROM planning_forecast_lines fl
            JOIN wms_items i ON fl.item_id = i.id
            WHERE fl.run_id = ?
            ORDER BY i.item_code, fl.period_start
        """, (run_id,)).fetchall()

        by_item = defaultdict(list)
        for line in lines:
            by_item[line['item_id']].append(line)

        return render_template('planning/forecast_detail.html',
            title=f'Forecast: {run["run_name"]}',
            run=run,
            lines=lines,
            by_item=by_item,
            user_preferences=user_prefs or {}
        )

    @app.route('/planning/forecast/<int:run_id>/approve', methods=['POST'])
    @planning_permission_required('forecasts', 'approve')
    def forecast_approve(run_id):
        """Approve a forecast run."""

        db = get_db()
        db.execute("""
            UPDATE planning_forecast_runs
            SET status = 'APPROVED', approved_by = ?, approved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (session['user_id'], run_id))
        db.commit()

        log_planning_audit('FORECAST_APPROVED', 'forecast_run', run_id,
                           user_id=session['user_id'])
        flash('Forecast approved successfully', 'success')
        return redirect(url_for('forecast_detail', run_id=run_id))

    @app.route('/planning/forecast/<int:run_id>/override', methods=['POST'])
    @planning_permission_required('forecasts', 'edit')
    def forecast_override(run_id):
        """Override a forecast value."""

        db = get_db()
        item_id = request.form.get('item_id', type=int)
        period_start = request.form.get('period_start')
        override_qty = float(request.form.get('override_quantity', 0))
        reason = request.form.get('reason', '')

        line = db.execute("""
            SELECT * FROM planning_forecast_lines
            WHERE run_id = ? AND item_id = ? AND period_start = ?
        """, (run_id, item_id, period_start)).fetchone()

        if not line:
            return jsonify({'error': 'Forecast line not found'}), 404

        db.execute("""
            INSERT INTO planning_forecast_overrides
            (item_id, forecast_run_id, period_start, original_quantity, override_quantity,
             override_reason, override_type, status, created_by)
            VALUES (?, ?, ?, ?, ?, ?, 'MANUAL', 'APPROVED', ?)
        """, (item_id, run_id, period_start, line['final_quantity'], override_qty,
              reason, session['user_id']))

        db.execute("""
            UPDATE planning_forecast_lines
            SET override_quantity = ?, final_quantity = ?, override_reason = ?
            WHERE id = ?
        """, (override_qty, override_qty, reason, line['id']))
        db.commit()

        log_planning_audit('FORECAST_OVERRIDE', 'forecast_line', line['id'],
                           item_id=item_id, user_id=session['user_id'],
                           changes={'original': line['final_quantity'], 'override': override_qty})

        flash('Forecast override applied', 'success')
        return redirect(url_for('forecast_detail', run_id=run_id))

    @app.route('/planning/forecast/api/summary/<int:run_id>')
    @planning_permission_required('forecasts', 'view')
    def forecast_api_summary(run_id):
        """API endpoint for forecast summary data (for charts)."""

        db = get_db()

        daily_totals = db.execute("""
            SELECT period_start, SUM(final_quantity) as total
            FROM planning_forecast_lines
            WHERE run_id = ?
            GROUP BY period_start
            ORDER BY period_start
        """, (run_id,)).fetchall()

        item_totals = db.execute("""
            SELECT fl.item_id, i.item_code, i.name,
                   SUM(fl.final_quantity) as total_forecast
            FROM planning_forecast_lines fl
            JOIN wms_items i ON fl.item_id = i.id
            WHERE fl.run_id = ?
            GROUP BY fl.item_id
            ORDER BY total_forecast DESC
            LIMIT 20
        """, (run_id,)).fetchall()

        return jsonify({
            'daily': [{'date': r['period_start'], 'value': r['total']} for r in daily_totals],
            'top_items': [dict(r) for r in item_totals]
        })

    # ============================================================
    # DEMAND ANALYSIS
    # ============================================================

    @app.route('/planning/demand')
    @planning_permission_required('demand_analysis', 'view')
    def demand_analysis():
        """Demand Analysis page."""

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        months = request.args.get('months', 12, type=int)
        warehouse_id = request.args.get('warehouse_id', type=int)
        item_id = request.args.get('item_id', type=int)

        item_filter = ""
        params = [f"-{months} months"]
        if item_id:
            item_filter = " AND item_id = ?"
            params.append(item_id)
        if warehouse_id:
            item_filter += " AND warehouse_id = ?"
            params.append(warehouse_id)

        demand_rows = db.execute(f"""
            SELECT item_id, period_start, period_type,
                   SUM(sales_quantity) as sales,
                   SUM(consumption_quantity) as consumption,
                   SUM(sales_quantity + consumption_quantity) as total_demand,
                   SUM(order_count) as orders
            FROM planning_demand_history
            WHERE period_start >= DATE('now', ?)
            {item_filter}
            GROUP BY item_id, period_start
            ORDER BY period_start DESC
        """, params).fetchall()

        items_with_demand = db.execute(f"""
            SELECT DISTINCT item_id FROM planning_demand_history
            WHERE period_start >= DATE('now', ?)
            {item_filter}
        """, params).fetchall()

        item_ids = [r['item_id'] for r in items_with_demand]

        demand_summary = []
        for iid in item_ids[:100]:
            stats = db.execute("""
                SELECT
                    SUM(sales_quantity + consumption_quantity) as total,
                    AVG(sales_quantity + consumption_quantity) as avg_demand,
                    MAX(sales_quantity + consumption_quantity) as max_demand,
                    MIN(CASE WHEN sales_quantity + consumption_quantity > 0
                             THEN sales_quantity + consumption_quantity END) as min_demand,
                    COUNT(*) as periods,
                    SUM(order_count) as total_orders
                FROM planning_demand_history
                WHERE item_id = ? AND period_start >= DATE('now', ?)
            """, (iid, f"-{months} months")).fetchone()

            item_info = db.execute(
                "SELECT item_code, name FROM wms_items WHERE id = ?", (iid,)
            ).fetchone()

            if stats and item_info:
                demand_summary.append({
                    'item_id': iid,
                    'item_code': item_info['item_code'],
                    'item_name': item_info['name'],
                    'total_demand': stats['total'] or 0,
                    'avg_demand': stats['avg_demand'] or 0,
                    'max_demand': stats['max_demand'] or 0,
                    'min_demand': stats['min_demand'] or 0,
                    'periods': stats['periods'] or 0,
                    'total_orders': stats['total_orders'] or 0
                })

        demand_summary.sort(key=lambda x: x['total_demand'], reverse=True)

        all_items = db.execute(
            "SELECT id, item_code, name FROM wms_items WHERE is_active = 1 ORDER BY item_code"
        ).fetchall()
        warehouse_list = db.execute("SELECT id, name FROM wms_warehouses ORDER BY name").fetchall()

        return render_template('planning/demand_analysis.html',
            title='Demand Analysis',
            demand_summary=demand_summary,
            all_items=all_items,
            warehouse_list=warehouse_list,
            selected_months=months,
            selected_warehouse=warehouse_id,
            selected_item=item_id,
            user_preferences=user_prefs or {}
        )

    @app.route('/planning/demand/api/chart/<int:item_id>')
    @planning_permission_required('demand_analysis', 'view')
    def demand_api_chart(item_id):
        """API for demand chart data for a specific item."""

        db = get_db()
        months = request.args.get('months', 12, type=int)

        rows = db.execute("""
            SELECT period_start,
                   sales_quantity, consumption_quantity,
                   (sales_quantity + consumption_quantity) as total
            FROM planning_demand_history
            WHERE item_id = ? AND period_start >= DATE('now', ?)
            ORDER BY period_start ASC
        """, (item_id, f"-{months} months")).fetchall()

        return jsonify({
            'labels': [r['period_start'] for r in rows],
            'sales': [r['sales_quantity'] for r in rows],
            'consumption': [r['consumption_quantity'] for r in rows],
            'total': [r['total'] for r in rows]
        })

    # ============================================================
    # INVENTORY HEALTH
    # ============================================================

    @app.route('/planning/inventory-health')
    @planning_permission_required('inventory_health', 'view')
    def inventory_health():
        """Inventory Health analysis page."""

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        health_items = db.execute("""
            SELECT i.id, i.item_code, i.name,
                   i.safety_stock, i.reorder_point, i.min_stock_level, i.max_stock_level,
                   COALESCE(ib.quantity, 0) as current_stock,
                   COALESCE(ib.reserved, 0) as reserved,
                   COALESCE(ib.allocated, 0) as allocated,
                   COALESCE(ib.blocked, 0) as blocked,
                   ip.abc_class, ip.xyz_class, ip.criticality_level,
                   COALESCE(pip.avg_demand, 0) as avg_daily_demand,
                   CASE
                     WHEN COALESCE(ib.quantity, 0) <= 0 THEN 'STOCKOUT'
                     WHEN COALESCE(ib.quantity, 0) < COALESCE(i.safety_stock, 0)
                          AND COALESCE(i.safety_stock, 0) > 0 THEN 'BELOW_SAFETY'
                     WHEN COALESCE(ib.quantity, 0) < COALESCE(i.reorder_point, 0)
                          AND COALESCE(i.reorder_point, 0) > 0 THEN 'BELOW_ROP'
                     WHEN COALESCE(ib.quantity, 0) > COALESCE(i.max_stock_level, 0) * 1.5
                          AND COALESCE(i.max_stock_level, 0) > 0 THEN 'EXCESS'
                     WHEN COALESCE(ib.quantity, 0) > COALESCE(i.max_stock_level, 0)
                          AND COALESCE(i.max_stock_level, 0) > 0 THEN 'OVERSTOCK'
                     ELSE 'HEALTHY'
                   END as health_status
            FROM wms_items i
            LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
            LEFT JOIN planning_item_profiles ip ON i.id = ip.item_id
            LEFT JOIN (
                SELECT item_id, AVG(sales_quantity + consumption_quantity) / 30 as avg_demand
                FROM planning_demand_history
                WHERE period_start >= DATE('now', '-12 months')
                GROUP BY item_id
            ) pip ON i.id = pip.item_id
            WHERE i.is_active = 1
            ORDER BY
                CASE health_status
                  WHEN 'STOCKOUT' THEN 1
                  WHEN 'BELOW_SAFETY' THEN 2
                  WHEN 'BELOW_ROP' THEN 3
                  WHEN 'EXCESS' THEN 4
                  WHEN 'OVERSTOCK' THEN 5
                  ELSE 6
                END,
                i.item_code
        """).fetchall()

        status_counts = {
            'STOCKOUT': 0, 'BELOW_SAFETY': 0, 'BELOW_ROP': 0,
            'OVERSTOCK': 0, 'EXCESS': 0, 'HEALTHY': 0
        }
        for item in health_items:
            status_counts[item['health_status']] = status_counts.get(item['health_status'], 0) + 1

        return render_template('planning/inventory_health.html',
            title='Inventory Health',
            health_items=health_items,
            status_counts=status_counts,
            user_preferences=user_prefs or {}
        )

    # ============================================================
    # REPLENISHMENT PLANNING
    # ============================================================

    @app.route('/planning/replenishment')
    @planning_permission_required('replenishment', 'view')
    def replenishment_planning():
        """Replenishment planning page - shows recommendations."""

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        status_filter = request.args.get('status', 'OPEN')
        priority_filter = request.args.get('priority')

        query = """
            SELECT r.*, i.item_code, i.name as item_name,
                   w.name as warehouse_name,
                   s.name as supplier_name
            FROM planning_replenishment_recommendations r
            JOIN wms_items i ON r.item_id = i.id
            LEFT JOIN wms_warehouses w ON r.warehouse_id = w.id
            LEFT JOIN suppliers s ON r.suggested_supplier_id = s.id
            WHERE 1=1
        """
        params = []

        if status_filter and status_filter != 'ALL':
            query += " AND r.status = ?"
            params.append(status_filter)
        if priority_filter:
            query += " AND r.priority >= ?"
            params.append(int(priority_filter))

        query += " ORDER BY r.priority DESC, r.created_at DESC LIMIT 200"

        recs = db.execute(query, params).fetchall()

        return render_template('planning/replenishment.html',
            title='Replenishment Planning',
            recommendations=recs,
            status_filter=status_filter,
            user_preferences=user_prefs or {}
        )

    @app.route('/planning/replenishment/generate', methods=['POST'])
    @planning_permission_required('replenishment', 'create')
    def replenishment_generate():
        """Generate replenishment recommendations."""

        db = get_db()
        settings = get_planning_settings(db)
        horizon = int(settings.get('FORECAST_HORIZON_DAYS', '30'))

        db.execute("DELETE FROM planning_replenishment_recommendations WHERE status = 'OPEN'")
        db.commit()

        items = db.execute("""
            SELECT id FROM wms_items WHERE is_active = 1
        """).fetchall()

        created = 0
        for item in items:
            req = calculate_net_requirement(item['id'], db, days_ahead=horizon)
            if req and req['net_requirement'] > 0:
                priority = 50
                if req['stockout_risk'] == 'CRITICAL':
                    priority = 90
                elif req['stockout_risk'] == 'HIGH':
                    priority = 70
                elif req['days_of_coverage'] > 30:
                    priority = 30

                db.execute("""
                    INSERT INTO planning_replenishment_recommendations
                    (item_id, warehouse_id, company_id, recommendation_type, action,
                     priority, current_stock, safety_stock_level, reorder_point_level,
                     forecasted_demand, open_demand, open_supply,
                     recommended_quantity, recommended_date,
                     service_level_impact, stockout_risk, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
                """, (
                    item['id'], req['warehouse_id'], req['company_id'],
                    'NORMAL', 'PURCHASE' if req['net_requirement'] > 0 else 'HOLD',
                    priority, req['current_stock'], req['safety_stock'],
                    req.get('reorder_point', 0), req['forecast_demand'],
                    req['open_orders'], req['in_transit'],
                    req['recommended_quantity'],
                    (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
                    req.get('service_level_impact'), req['stockout_risk']
                ))
                created += 1

        db.commit()
        log_planning_audit('REPLENISHMENT_GENERATED', 'batch', None,
                           user_id=session['user_id'],
                           changes={'recommendations_created': created})

        flash(f'Generated {created} replenishment recommendations', 'success')
        return redirect(url_for('replenishment_planning'))

    @app.route('/planning/replenishment/<int:rec_id>/approve', methods=['POST'])
    @planning_permission_required('replenishment', 'approve')
    def replenishment_approve(rec_id):
        """Approve a replenishment recommendation."""

        db = get_db()
        db.execute("""
            UPDATE planning_replenishment_recommendations
            SET status = 'APPROVED', approved_by = ?, approved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (session['user_id'], rec_id))
        db.commit()

        log_planning_audit('REPLENISHMENT_APPROVED', 'replenishment_rec', rec_id,
                           user_id=session['user_id'])
        flash('Recommendation approved', 'success')
        return redirect(url_for('replenishment_planning'))

    @app.route('/planning/replenishment/<int:rec_id>/dismiss', methods=['POST'])
    @planning_permission_required('replenishment', 'edit')
    def replenishment_dismiss(rec_id):
        """Dismiss/dismiss a replenishment recommendation."""

        db = get_db()
        db.execute("""
            UPDATE planning_replenishment_recommendations
            SET status = 'DISMISSED', reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (session['user_id'], rec_id))
        db.commit()

        log_planning_audit('REPLENISHMENT_DISMISSED', 'replenishment_rec', rec_id,
                           user_id=session['user_id'])
        flash('Recommendation dismissed', 'info')
        return redirect(url_for('replenishment_planning'))

    # ============================================================
    # PURCHASE SUGGESTIONS
    # ============================================================

    @app.route('/planning/purchase-suggestions')
    @planning_permission_required('purchase_suggestions', 'view')
    def purchase_suggestions():
        """Purchase suggestions page."""

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        status_filter = request.args.get('status', 'OPEN')
        priority_filter = request.args.get('priority')

        query = """
            SELECT p.*, i.item_code, i.name as item_name,
                   s.name as supplier_name, s.lead_time as supplier_lead_time,
                   w.name as warehouse_name
            FROM planning_purchase_recommendations p
            JOIN wms_items i ON p.item_id = i.id
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            LEFT JOIN wms_warehouses w ON p.warehouse_id = w.id
            WHERE 1=1
        """
        params = []
        if status_filter and status_filter != 'ALL':
            query += " AND p.status = ?"
            params.append(status_filter)
        if priority_filter:
            query += " AND p.priority >= ?"
            params.append(int(priority_filter))

        query += " ORDER BY p.priority DESC, p.created_at DESC LIMIT 200"
        recs = db.execute(query, params).fetchall()

        suppliers = db.execute("SELECT id, name FROM suppliers ORDER BY name").fetchall()
        warehouse_list = db.execute("SELECT id, name FROM wms_warehouses ORDER BY name").fetchall()

        return render_template('planning/purchase_suggestions.html',
            title='Purchase Suggestions',
            recommendations=recs,
            suppliers=suppliers,
            warehouse_list=warehouse_list,
            status_filter=status_filter,
            user_preferences=user_prefs or {}
        )

    @app.route('/planning/purchase-suggestions/generate', methods=['POST'])
    @planning_permission_required('purchase_suggestions', 'create')
    def purchase_suggestions_generate():
        """Generate purchase recommendations from replenishment and item-supplier data."""

        db = get_db()
        settings = get_planning_settings(db)
        horizon = int(settings.get('FORECAST_HORIZON_DAYS', '30'))

        db.execute("DELETE FROM planning_purchase_recommendations WHERE status = 'OPEN'")
        db.commit()

        items = db.execute("SELECT id FROM wms_items WHERE is_active = 1").fetchall()
        created = 0

        for item in items:
            req = calculate_net_requirement(item['id'], db, days_ahead=horizon)
            if not req or req['net_requirement'] <= 0:
                continue

            supplier_rows = db.execute("""
                SELECT sup.*, its.supplier_id, its.lead_time_days, its.moq, its.unit_cost
                FROM wms_item_suppliers its
                JOIN suppliers sup ON its.supplier_id = sup.id
                WHERE its.item_id = ?
                ORDER BY its.is_preferred DESC, its.unit_cost ASC
                LIMIT 1
            """, (item['id'],)).fetchall()

            if not supplier_rows:
                supplier_rows = db.execute("""
                    SELECT s.*, s.id as supplier_id, 7 as lead_time_days, 0 as moq, 0 as unit_cost
                    FROM suppliers s LIMIT 1
                """).fetchall()

            for sup in supplier_rows:
                priority = 50
                if req['stockout_risk'] in ('CRITICAL', 'HIGH'):
                    priority = 80
                    rec_type = 'EMERGENCY'
                else:
                    rec_type = 'NORMAL'

                suggested_order_date = datetime.now().date()
                suggested_arrival = suggested_order_date + timedelta(days=sup['lead_time_days'] or 7)

                moq = sup['moq'] or 0
                multiple = 1
                rec_qty = req['recommended_quantity']
                if moq > 0 and rec_qty < moq:
                    rec_qty = moq
                elif multiple > 1:
                    rec_qty = ((rec_qty / multiple) + 1) * multiple

                est_cost = rec_qty * (sup['unit_cost'] or 0)

                db.execute("""
                    INSERT INTO planning_purchase_recommendations
                    (item_id, warehouse_id, company_id, supplier_id, recommendation_type,
                     action, priority, current_stock, forecasted_demand, open_po_quantity,
                     in_transit_quantity, recommended_quantity, suggested_order_date,
                     suggested_arrival_date, suggested_unit_cost, estimated_total_cost,
                     moq, order_multiple, lead_time_days, shortage_date, shortage_risk,
                     budget_impact, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
                """, (
                    item['id'], req['warehouse_id'], req['company_id'], sup['supplier_id'],
                    rec_type, 'BUY', priority, req['current_stock'], req['forecast_demand'],
                    req['open_po'], req['in_transit'], rec_qty,
                    suggested_order_date.strftime('%Y-%m-%d'),
                    suggested_arrival.strftime('%Y-%m-%d'),
                    sup['unit_cost'] or 0, est_cost,
                    moq, multiple, sup['lead_time_days'] or 7,
                    (datetime.now() + timedelta(days=req['days_of_coverage'])).strftime('%Y-%m-%d')
                    if req['days_of_coverage'] < 999 else None,
                    req['stockout_risk'], est_cost
                ))
                created += 1
                break

        db.commit()
        log_planning_audit('PURCHASE_RECS_GENERATED', 'batch', None,
                           user_id=session['user_id'],
                           changes={'recommendations_created': created})

        flash(f'Generated {created} purchase recommendations', 'success')
        return redirect(url_for('purchase_suggestions'))

    @app.route('/planning/purchase-suggestions/<int:rec_id>/approve', methods=['POST'])
    @planning_permission_required('purchase_suggestions', 'approve')
    def purchase_approve(rec_id):
        """Approve a purchase recommendation."""

        db = get_db()
        db.execute("""
            UPDATE planning_purchase_recommendations
            SET status = 'APPROVED', approved_by = ?, approved_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (session['user_id'], rec_id))
        db.commit()

        log_planning_audit('PURCHASE_REC_APPROVED', 'purchase_rec', rec_id,
                           user_id=session['user_id'])
        flash('Purchase recommendation approved', 'success')
        return redirect(url_for('purchase_suggestions'))

    # ============================================================
    # TRANSFER SUGGESTIONS
    # ============================================================

    @app.route('/planning/transfer-suggestions')
    @planning_permission_required('transfer_suggestions', 'view')
    def transfer_suggestions():
        """Transfer suggestions page."""

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        recs = db.execute("""
            SELECT t.*, i.item_code, i.name as item_name,
                   sw.name as source_warehouse, dw.name as dest_warehouse
            FROM planning_transfer_recommendations t
            JOIN wms_items i ON t.item_id = i.id
            LEFT JOIN wms_warehouses sw ON t.source_warehouse_id = sw.id
            LEFT JOIN wms_warehouses dw ON t.destination_warehouse_id = dw.id
            WHERE t.status = 'OPEN'
            ORDER BY t.priority DESC, t.created_at DESC
            LIMIT 200
        """).fetchall()

        warehouses = db.execute("SELECT id, name FROM wms_warehouses ORDER BY name").fetchall()

        return render_template('planning/transfer_suggestions.html',
            title='Transfer Suggestions',
            recommendations=recs,
            warehouses=warehouses,
            user_preferences=user_prefs or {}
        )

    @app.route('/planning/transfer-suggestions/generate', methods=['POST'])
    @planning_permission_required('transfer_suggestions', 'create')
    def transfer_suggestions_generate():
        """Generate transfer recommendations to balance stock across warehouses."""

        db = get_db()
        db.execute("DELETE FROM planning_transfer_recommendations WHERE status = 'OPEN'")
        db.commit()

        warehouses = db.execute("SELECT id, name FROM wms_warehouses").fetchall()
        created = 0

        for wh_src in warehouses:
            for wh_dst in warehouses:
                if wh_src['id'] == wh_dst['id']:
                    continue

                excess_rows = db.execute("""
                    SELECT ib.item_id, SUM(ib.quantity) as qty, i.reorder_point
                    FROM wms_inventory_balances ib
                    JOIN wms_items i ON ib.item_id = i.id
                    WHERE ib.warehouse_id = ?
                      AND i.is_active = 1
                      AND ib.quantity > COALESCE(i.reorder_point, 0) * 1.5
                    GROUP BY ib.item_id
                """, (wh_src['id'],)).fetchall()

                shortage_rows = db.execute("""
                    SELECT ib.item_id, SUM(ib.quantity) as qty, i.reorder_point
                    FROM wms_inventory_balances ib
                    JOIN wms_items i ON ib.item_id = i.id
                    WHERE ib.warehouse_id = ?
                      AND i.is_active = 1
                      AND ib.quantity < COALESCE(i.reorder_point, 0)
                    GROUP BY ib.item_id
                """, (wh_dst['id'],)).fetchall()

                shortage_items = {r['item_id']: r for r in shortage_rows}

                for excess in excess_rows:
                    if excess['item_id'] in shortage_items:
                        shortage = shortage_items[excess['item_id']]
                        transfer_qty = min(
                            excess['qty'] - (excess['reorder_point'] or 0) * 1.5,
                            (excess['reorder_point'] or 0) - shortage['qty']
                        )
                        if transfer_qty > 0:
                            db.execute("""
                                INSERT INTO planning_transfer_recommendations
                                (item_id, source_warehouse_id, destination_warehouse_id,
                                 source_current_stock, destination_current_stock,
                                 source_excess_quantity, destination_shortage_quantity,
                                 recommended_quantity, action, priority, status)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
                            """, (
                                excess['item_id'], wh_src['id'], wh_dst['id'],
                                excess['qty'], shortage['qty'],
                                excess['qty'] - (excess['reorder_point'] or 0) * 1.5,
                                (excess['reorder_point'] or 0) - shortage['qty'],
                                transfer_qty, 'TRANSFER', 60
                            ))
                            created += 1

        db.commit()
        flash(f'Generated {created} transfer recommendations', 'success')
        return redirect(url_for('transfer_suggestions'))

    # ============================================================
    # SAFETY STOCK & REORDER RULES
    # ============================================================

    @app.route('/planning/safety-stock')
    @planning_permission_required('safety_stock', 'view')
    def safety_stock_rules():
        """Safety Stock & Reorder Rules management page."""

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        profiles = db.execute("""
            SELECT ip.*, i.item_code, i.name as item_name
            FROM planning_item_profiles ip
            JOIN wms_items i ON ip.item_id = i.id
            ORDER BY i.item_code
            LIMIT 200
        """).fetchall()

        policies = db.execute("""
            SELECT * FROM planning_policies WHERE is_active = 1
            ORDER BY name
        """).fetchall()

        all_items = db.execute(
            "SELECT id, item_code, name FROM wms_items WHERE is_active = 1 ORDER BY item_code"
        ).fetchall()

        return render_template('planning/safety_stock_rules.html',
            title='Safety Stock & Reorder Rules',
            profiles=profiles,
            policies=policies,
            all_items=all_items,
            user_preferences=user_prefs or {}
        )

    @app.route('/planning/safety-stock/save', methods=['POST'])
    @planning_permission_required('safety_stock', 'edit')
    def safety_stock_save():
        """Save safety stock / reorder parameters for an item."""

        db = get_db()
        item_id = request.form.get('item_id', type=int)
        safety_stock = float(request.form.get('safety_stock', 0))
        reorder_point = float(request.form.get('reorder_point', 0))
        min_stock = float(request.form.get('min_stock', 0))
        max_stock = float(request.form.get('max_stock', 0))
        lead_time_days = int(request.form.get('lead_time_days', 7))
        moq = float(request.form.get('min_order_quantity', 0))
        order_multiple = float(request.form.get('order_multiple', 1))
        service_level = float(request.form.get('service_level_target', 0.95))
        planning_method = request.form.get('planning_method', 'AUTO')
        forecast_method = request.form.get('forecast_method', 'MOVING_AVERAGE')

        existing = db.execute(
            "SELECT id FROM planning_item_profiles WHERE item_id = ?", (item_id,)
        ).fetchone()

        if existing:
            db.execute("""
                UPDATE planning_item_profiles
                SET safety_stock_days = ?, lead_time_days = ?, min_order_quantity = ?,
                    order_multiple = ?, service_level_target = ?, planning_method = ?,
                    forecast_method = ?, updated_at = CURRENT_TIMESTAMP
                WHERE item_id = ?
            """, (int(safety_stock), lead_time_days, moq, order_multiple,
                  service_level, planning_method, forecast_method, item_id))
            profile_id = existing['id']
        else:
            cursor = db.execute("""
                INSERT INTO planning_item_profiles
                (item_id, safety_stock_days, lead_time_days, min_order_quantity,
                 order_multiple, service_level_target, planning_method, forecast_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (item_id, int(safety_stock), lead_time_days, moq, order_multiple,
                  service_level, planning_method, forecast_method))
            profile_id = cursor.lastrowid

        db.execute("""
            UPDATE wms_items
            SET safety_stock = ?, reorder_point = ?, min_stock_level = ?, max_stock_level = ?
            WHERE id = ?
        """, (safety_stock, reorder_point, min_stock, max_stock, item_id))
        db.commit()

        log_planning_audit('SAFETY_STOCK_UPDATED', 'item', item_id,
                           item_id=item_id, user_id=session['user_id'],
                           changes={'safety_stock': safety_stock, 'reorder_point': reorder_point,
                                    'min': min_stock, 'max': max_stock, 'lead_time': lead_time_days})

        flash('Safety stock and reorder rules saved', 'success')
        return redirect(url_for('safety_stock_rules'))

    @app.route('/planning/safety-stock/calculate', methods=['POST'])
    @planning_permission_required('safety_stock', 'view')
    def safety_stock_calculate():
        """Calculate recommended safety stock for an item using formula."""

        db = get_db()
        item_id = request.form.get('item_id', type=int)
        method = request.form.get('method', 'FORMULA')

        recommended_ss = calculate_safety_stock(item_id, db, method=method)
        recommended_rop = calculate_reorder_point(item_id, db)

        return jsonify({
            'recommended_safety_stock': round(recommended_ss, 2),
            'recommended_reorder_point': round(recommended_rop, 2)
        })

    # ============================================================
    # SUPPLIER & LEAD TIME ANALYSIS
    # ============================================================

    @app.route('/planning/supplier-analysis')
    @planning_permission_required('supplier_analysis', 'view')
    def supplier_analysis():
        """Supplier lead time and performance analysis."""

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        supplier_perf = db.execute("""
            SELECT spp.*, s.name as supplier_name, s.code as supplier_code,
                   s.lead_time as default_lead_time, s.rating as supplier_rating,
                   s.country as supplier_country
            FROM planning_supplier_performance spp
            JOIN suppliers s ON spp.supplier_id = s.id
            ORDER BY s.name, spp.period_start DESC
            LIMIT 200
        """).fetchall()

        suppliers = db.execute("""
            SELECT s.*,
                   (SELECT AVG(lead_time_days) FROM wms_item_suppliers WHERE supplier_id = s.id) as avg_lead_time,
                   (SELECT COUNT(*) FROM wms_item_suppliers WHERE supplier_id = s.id) as item_count
            FROM suppliers s
            ORDER BY s.name
        """).fetchall()

        return render_template('planning/supplier_analysis.html',
            title='Supplier & Lead Time Analysis',
            supplier_perf=supplier_perf,
            suppliers=suppliers,
            user_preferences=user_prefs or {}
        )

    @app.route('/planning/supplier-analysis/refresh', methods=['POST'])
    @planning_permission_required('supplier_analysis', 'edit')
    def supplier_analysis_refresh():
        """Refresh supplier performance metrics."""

        db = get_db()
        today = datetime.now().date()
        period_start = today.replace(day=1).strftime('%Y-%m-%d')

        suppliers = db.execute("SELECT id FROM suppliers").fetchall()
        created = 0

        for sup in suppliers:
            receipts = db.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN received_date <= expected_date THEN 1 ELSE 0 END) as on_time,
                       SUM(quantity) as total_qty,
                       SUM(received_quantity) as received_qty,
                       AVG(lead_time_days) as avg_lt
                FROM wms_inbound_receipts
                WHERE supplier_id = ? AND received_date >= ?
            """, (sup['id'], period_start)).fetchone()

            if receipts and receipts['total'] and receipts['total'] > 0:
                on_time_pct = (receipts['on_time'] or 0) / receipts['total'] * 100
                fill_rate = (receipts['received_qty'] or 0) / (receipts['total_qty'] or 1) * 100

                db.execute("""
                    INSERT INTO planning_supplier_performance
                    (supplier_id, period_type, period_start, total_orders, on_time_count,
                     on_time_percent, total_quantity_ordered, total_quantity_received,
                     fill_rate, avg_lead_time_days)
                    VALUES (?, 'MONTHLY', ?, ?, ?, ?, ?, ?, ?, ?)
                """, (sup['id'], period_start, receipts['total'],
                      receipts['on_time'] or 0, on_time_pct,
                      receipts['total_qty'] or 0, receipts['received_qty'] or 0,
                      fill_rate, receipts['avg_lt'] or 7))
                created += 1

        db.commit()
        flash(f'Updated performance data for {created} suppliers', 'success')
        return redirect(url_for('supplier_analysis'))

    # ============================================================
    # CUSTOMER DEMAND PATTERNS
    # ============================================================

    @app.route('/planning/customer-patterns')
    @planning_permission_required('customer_patterns', 'view')
    def customer_patterns():
        """Customer demand pattern analysis."""

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        patterns = db.execute("""
            SELECT cdp.*, c.name as customer_name, c.code as customer_code,
                   i.item_code, i.name as item_name
            FROM planning_customer_demand_patterns cdp
            LEFT JOIN sdad_customers c ON cdp.customer_id = c.id
            LEFT JOIN wms_items i ON cdp.item_id = i.id
            ORDER BY cdp.total_value DESC
            LIMIT 200
        """).fetchall()

        key_customers = db.execute("""
            SELECT c.*, cdp.total_orders, cdp.total_quantity, cdp.total_value,
                   cdp.demand_trend, cdp.is_key_customer, cdp.is_at_risk
            FROM sdad_customers c
            LEFT JOIN planning_customer_demand_patterns cdp ON c.id = cdp.customer_id
            ORDER BY COALESCE(cdp.total_value, 0) DESC
            LIMIT 50
        """).fetchall()

        return render_template('planning/customer_patterns.html',
            title='Customer Demand Patterns',
            patterns=patterns,
            key_customers=key_customers,
            user_preferences=user_prefs or {}
        )

    @app.route('/planning/customer-patterns/refresh', methods=['POST'])
    @planning_permission_required('customer_patterns', 'edit')
    def customer_patterns_refresh():
        """Refresh customer demand pattern analysis."""

        db = get_db()

        customers = db.execute("SELECT id FROM sdad_customers").fetchall()
        created = 0

        for cust in customers:
            stats = db.execute("""
                SELECT COUNT(*) as total_orders,
                       SUM(quantity) as total_qty,
                       SUM(total_value) as total_val,
                       AVG(quantity) as avg_qty,
                       MIN(order_date) as first_order,
                       MAX(order_date) as last_order
                FROM (
                    SELECT quantity, quantity * COALESCE(unit_price, 0) as total_value, order_date
                    FROM planning_sales_history
                    WHERE customer_id = ?
                )
            """, (cust['id'],)).fetchone()

            if stats and stats['total_orders'] and stats['total_orders'] > 0:
                total_days = (datetime.now().date() - stats['last_order']).days if stats['last_order'] else 0
                avg_interval = total_days / stats['total_orders'] if stats['total_orders'] > 1 else 0

                trend = 'STABLE'
                is_key = 1 if stats['total_val'] and stats['total_val'] > 10000 else 0
                is_at_risk = 1 if total_days > 180 else 0

                db.execute("""
                    INSERT INTO planning_customer_demand_patterns
                    (customer_id, total_orders, total_quantity, total_value,
                     avg_order_quantity, avg_order_interval_days, last_order_date,
                     first_order_date, is_key_customer, is_at_risk, demand_trend)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(customer_id) DO UPDATE SET
                        total_orders = excluded.total_orders,
                        total_quantity = excluded.total_quantity,
                        total_value = excluded.total_value,
                        avg_order_quantity = excluded.avg_order_quantity,
                        avg_order_interval_days = excluded.avg_order_interval_days,
                        last_order_date = excluded.last_order_date,
                        updated_at = CURRENT_TIMESTAMP
                """, (cust['id'], stats['total_orders'], stats['total_qty'] or 0,
                      stats['total_val'] or 0, stats['avg_qty'] or 0,
                      avg_interval, stats['last_order'], stats['first_order'],
                      is_key, is_at_risk, trend))
                created += 1

        db.commit()
        flash(f'Updated patterns for {created} customers', 'success')
        return redirect(url_for('customer_patterns'))

    # ============================================================
    # LOST SALES & SERVICE RISK
    # ============================================================

    @app.route('/planning/lost-sales')
    @planning_permission_required('lost_sales', 'view')
    def lost_sales():
        """Lost sales and service risk analysis."""

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        lost_sales = db.execute("""
            SELECT ls.*, i.item_code, i.name as item_name,
                   c.name as customer_name
            FROM planning_lost_sales ls
            JOIN wms_items i ON ls.item_id = i.id
            LEFT JOIN sdad_customers c ON ls.customer_id = c.id
            ORDER BY ls.lost_date DESC
            LIMIT 200
        """).fetchall()

        total_lost_value = sum(r['lost_value'] or 0 for r in lost_sales)
        total_lost_qty = sum(r['lost_quantity'] or 0 for r in lost_sales)

        return render_template('planning/lost_sales.html',
            title='Lost Sales & Service Risk',
            lost_sales=lost_sales,
            total_lost_value=total_lost_value,
            total_lost_qty=total_lost_qty,
            user_preferences=user_prefs or {}
        )

    @app.route('/planning/lost-sales/record', methods=['POST'])
    @planning_permission_required('lost_sales', 'create')
    def lost_sales_record():
        """Record a lost sale."""

        db = get_db()
        item_id = request.form.get('item_id', type=int)
        customer_id = request.form.get('customer_id', type=int)
        lost_date = request.form.get('lost_date')
        requested_qty = float(request.form.get('requested_quantity', 0))
        fulfilled_qty = float(request.form.get('fulfilled_quantity', 0))
        lost_qty = requested_qty - fulfilled_qty
        unit_price = float(request.form.get('unit_price', 0))
        lost_value = lost_qty * unit_price
        reason = request.form.get('lost_reason', '')

        db.execute("""
            INSERT INTO planning_lost_sales
            (item_id, customer_id, lost_date, requested_quantity, fulfilled_quantity,
             lost_quantity, unit_price, lost_value, lost_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (item_id, customer_id, lost_date, requested_qty, fulfilled_qty,
              lost_qty, unit_price, lost_value, reason))
        db.commit()

        log_planning_audit('LOST_SALE_RECORDED', 'lost_sale', None,
                           item_id=item_id, customer_id=customer_id,
                           user_id=session['user_id'],
                           changes={'lost_value': lost_value, 'lost_qty': lost_qty})

        flash('Lost sale recorded', 'success')
        return redirect(url_for('lost_sales'))

    # ============================================================
    # SEASONALITY & TREND ANALYSIS
    # ============================================================

    @app.route('/planning/seasonality')
    @planning_permission_required('seasonality', 'view')
    def seasonality_analysis():
        """Seasonality and trend analysis."""

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        items = db.execute("""
            SELECT i.id, i.item_code, i.name,
                   pip.demand_trend as pattern_class,
                   pip.is_seasonal
            FROM wms_items i
            LEFT JOIN planning_item_profiles pip ON i.id = pip.item_id
            WHERE i.is_active = 1
            ORDER BY i.item_code
            LIMIT 100
        """).fetchall()

        monthly_patterns = db.execute("""
            SELECT
                strftime('%Y-%m', period_start) as month_key,
                AVG(sales_quantity + consumption_quantity) as avg_demand,
                MAX(sales_quantity + consumption_quantity) as peak_demand,
                MIN(sales_quantity + consumption_quantity) as min_demand,
                COUNT(DISTINCT item_id) as active_items
            FROM planning_demand_history
            WHERE period_start >= DATE('now', '-24 months')
            GROUP BY strftime('%Y-%m', period_start)
            ORDER BY month_key
        """).fetchall()

        return render_template('planning/seasonality.html',
            title='Seasonality & Trend Analysis',
            items=items,
            monthly_patterns=monthly_patterns,
            user_preferences=user_prefs or {}
        )

    @app.route('/planning/seasonality/api/trend/<int:item_id>')
    @planning_permission_required('seasonality', 'view')
    def seasonality_api(item_id):
        """API for seasonality/trend data for an item."""

        db = get_db()
        rows = db.execute("""
            SELECT period_start,
                   (sales_quantity + consumption_quantity) as demand
            FROM planning_demand_history
            WHERE item_id = ? AND period_start >= DATE('now', '-24 months')
            ORDER BY period_start ASC
        """, (item_id,)).fetchall()

        demand_values = [r['demand'] for r in rows]
        pattern = classify_demand_pattern(demand_values)
        slope, intercept = calculate_trend(demand_values)

        return jsonify({
            'pattern': pattern,
            'trend_slope': round(slope, 4),
            'trend_intercept': round(intercept, 2),
            'seasonal_indices': calculate_seasonal_index(demand_values, 12) if len(demand_values) >= 12 else {},
            'data': [{'date': r['period_start'], 'demand': r['demand']} for r in rows]
        })

    # ============================================================
    # EXCEPTIONS & ALERTS
    # ============================================================

    @app.route('/planning/alerts')
    @planning_permission_required('alerts', 'view')
    def planning_alerts():
        """Planning exceptions and alerts center."""

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        acknowledged = request.args.get('acknowledged', '0')
        severity = request.args.get('severity')
        alert_type = request.args.get('alert_type')

        query = """
            SELECT a.*, i.item_code, i.name as item_name,
                   w.name as warehouse_name,
                   s.name as supplier_name
            FROM planning_alerts a
            LEFT JOIN wms_items i ON a.item_id = i.id
            LEFT JOIN wms_warehouses w ON a.warehouse_id = w.id
            LEFT JOIN suppliers s ON a.supplier_id = s.id
            WHERE 1=1
        """
        params = []

        if acknowledged == '0':
            query += " AND a.is_acknowledged = 0"
        if severity:
            query += " AND a.severity = ?"
            params.append(severity)
        if alert_type:
            query += " AND a.alert_type = ?"
            params.append(alert_type)

        query += " ORDER BY a.created_at DESC LIMIT 200"

        alerts = db.execute(query, params).fetchall()

        alert_types = db.execute("""
            SELECT DISTINCT alert_type FROM planning_alerts ORDER BY alert_type
        """).fetchall()

        return render_template('planning/alerts.html',
            title='Exceptions & Alerts',
            alerts=alerts,
            alert_types=[r['alert_type'] for r in alert_types],
            acknowledged=acknowledged,
            selected_severity=severity,
            selected_alert_type=alert_type,
            user_preferences=user_prefs or {}
        )

    @app.route('/planning/alerts/acknowledge/<int:alert_id>', methods=['POST'])
    @planning_permission_required('alerts', 'edit')
    def alert_acknowledge(alert_id):
        """Acknowledge an alert."""

        db = get_db()
        notes = request.form.get('notes', '')
        db.execute("""
            UPDATE planning_alerts
            SET is_acknowledged = 1, acknowledged_by = ?,
                acknowledged_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (session['user_id'], alert_id))
        db.commit()

        log_planning_audit('ALERT_ACKNOWLEDGED', 'alert', alert_id,
                           user_id=session['user_id'], notes=notes)
        flash('Alert acknowledged', 'info')
        return redirect(url_for('planning_alerts'))

    @app.route('/planning/alerts/generate', methods=['POST'])
    @planning_permission_required('alerts', 'create')
    def alerts_generate():
        """Generate planning alerts from current inventory state."""

        db = get_db()
        generate_planning_alerts(db)
        flash('Planning alerts generated', 'success')
        return redirect(url_for('planning_alerts'))

    # ============================================================
    # SCENARIOS & SIMULATIONS
    # ============================================================

    @app.route('/planning/scenarios')
    @planning_permission_required('scenarios', 'view')
    def scenarios():
        """Scenario planning and simulation center."""

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        scenarios_list = db.execute("""
            SELECT s.*, u.username as created_by_name
            FROM planning_scenarios s
            LEFT JOIN users u ON s.created_by = u.id
            ORDER BY s.created_at DESC
            LIMIT 50
        """).fetchall()

        return render_template('planning/scenarios.html',
            title='Scenarios & Simulations',
            scenarios=scenarios_list,
            user_preferences=user_prefs or {}
        )

    @app.route('/planning/scenarios/create', methods=['POST'])
    @planning_permission_required('scenarios', 'create')
    def scenarios_create():
        """Create a new planning scenario."""

        db = get_db()
        name = request.form.get('name')
        description = request.form.get('description', '')
        scenario_type = request.form.get('scenario_type', 'DEMAND_CHANGE')
        params_json = request.form.get('parameters_json', '{}')

        cursor = db.execute("""
            INSERT INTO planning_scenarios
            (name, description, scenario_type, parameters_json, created_by)
            VALUES (?, ?, ?, ?, ?)
        """, (name, description, scenario_type, params_json, session['user_id']))
        scenario_id = cursor.lastrowid
        db.commit()

        log_planning_audit('SCENARIO_CREATED', 'scenario', scenario_id,
                           user_id=session['user_id'],
                           changes={'name': name, 'type': scenario_type})

        flash(f'Scenario "{name}" created', 'success')
        return redirect(url_for('scenario_detail', scenario_id=scenario_id))

    @app.route('/planning/scenarios/<int:scenario_id>')
    @planning_permission_required('scenarios', 'view')
    def scenario_detail(scenario_id):
        """View scenario details and impact."""

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        scenario = db.execute(
            "SELECT * FROM planning_scenarios WHERE id = ?", (scenario_id,)
        ).fetchone()

        lines = db.execute("""
            SELECT sl.*, i.item_code, i.name as item_name
            FROM planning_scenario_lines sl
            JOIN wms_items i ON sl.item_id = i.id
            WHERE sl.scenario_id = ?
            ORDER BY ABS(sl.impact_value) DESC
        """, (scenario_id,)).fetchall()

        return render_template('planning/scenario_detail.html',
            title=f'Scenario: {scenario["name"] if scenario else "Not Found"}',
            scenario=scenario,
            lines=lines,
            user_preferences=user_prefs or {}
        )

    @app.route('/planning/scenarios/<int:scenario_id>/run', methods=['POST'])
    @planning_permission_required('scenarios', 'edit')
    def scenario_run(scenario_id):
        """Run a scenario simulation."""

        db = get_db()
        scenario = db.execute(
            "SELECT * FROM planning_scenarios WHERE id = ?", (scenario_id,)
        ).fetchone()

        if not scenario:
            flash('Scenario not found', 'error')
            return redirect(url_for('scenarios'))

        params = json.loads(scenario['parameters_json'] or '{}')
        scenario_type = scenario['scenario_type']

        db.execute("DELETE FROM planning_scenario_lines WHERE scenario_id = ?", (scenario_id,))

        items = db.execute("SELECT id FROM wms_items WHERE is_active = 1").fetchall()
        created = 0

        demand_change_pct = params.get('demand_change_percent', 0)
        lead_time_change = params.get('lead_time_change_days', 0)
        supplier_fail = params.get('supplier_id') 

        for item in items:
            if scenario_type == 'DEMAND_CHANGE':
                req = calculate_net_requirement(item['id'], db, days_ahead=30)
                if req:
                    changed_demand = req['forecast_demand'] * (1 + demand_change_pct / 100)
                    changed_net = max(0, changed_demand - req['sellable_stock'] - req['in_transit'])
                    base_net = req['net_requirement']

                    db.execute("""
                        INSERT INTO planning_scenario_lines
                        (scenario_id, item_id, metric_name, base_value, scenario_value, impact_value)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (scenario_id, item['id'], 'NET_REQUIREMENT',
                          base_net, changed_net, changed_net - base_net))
                    created += 1

            elif scenario_type == 'LEAD_TIME_CHANGE':
                req = calculate_net_requirement(item['id'], db, days_ahead=30)
                if req:
                    profile = db.execute(
                        "SELECT lead_time_days FROM planning_item_profiles WHERE item_id = ?",
                        (item['id'],)
                    ).fetchone()
                    orig_lt = (profile['lead_time_days'] or 7) if profile else 7
                    new_lt = max(1, orig_lt + lead_time_change)
                    days_impact = new_lt - orig_lt

                    db.execute("""
                        INSERT INTO planning_scenario_lines
                        (scenario_id, item_id, metric_name, base_value, scenario_value, impact_value)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (scenario_id, item['id'], 'LEAD_TIME_DAYS', orig_lt, new_lt, days_impact))
                    created += 1

        db.execute("""
            UPDATE planning_scenarios
            SET total_impact_items = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (created, scenario_id))
        db.commit()

        log_planning_audit('SCENARIO_RUN', 'scenario', scenario_id,
                           user_id=session['user_id'],
                           changes={'type': scenario_type, 'items_impacted': created})

        flash(f'Scenario simulation ran: {created} items impacted', 'success')
        return redirect(url_for('scenario_detail', scenario_id=scenario_id))

    # ============================================================
    # REPORTS & ANALYTICS
    # ============================================================

    @app.route('/planning/reports')
    @planning_permission_required('reports', 'view')
    def planning_reports():
        """Planning reports and analytics center."""

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        kpi_records = db.execute("""
            SELECT kpi_name, period_type, period_start, value, target
            FROM planning_kpi_records
            ORDER BY period_start DESC
            LIMIT 100
        """).fetchall()

        return render_template('planning/reports.html',
            title='Reports & Analytics',
            kpi_records=kpi_records,
            user_preferences=user_prefs or {}
        )

    @app.route('/planning/reports/kpi-snapshot', methods=['POST'])
    @planning_permission_required('reports', 'create')
    def kpi_snapshot():
        """Take a KPI snapshot."""

        db = get_db()
        snapshot_kpis(db)
        flash('KPI snapshot captured', 'success')
        return redirect(url_for('planning_reports'))

    @app.route('/planning/reports/forecast-accuracy')
    @planning_permission_required('reports', 'view')
    def forecast_accuracy_report():
        """Forecast accuracy report."""

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        accuracy_data = db.execute("""
            SELECT
                fl.item_id, i.item_code, i.name,
                AVG(ABS(fl.final_quantity - COALESCE(pdh.actual_qty, 0))) as mae,
                AVG(CASE WHEN pdh.actual_qty > 0
                         THEN ABS(fl.final_quantity - pdh.actual_qty) / pdh.actual_qty
                         ELSE 0 END) as mape,
                AVG(CASE WHEN pdh.actual_qty > 0 AND fl.final_quantity > 0
                         THEN 1 - ABS(fl.final_quantity - pdh.actual_qty) / GREATEST(fl.final_quantity, pdh.actual_qty)
                         ELSE 0.5 END) as accuracy
            FROM planning_forecast_lines fl
            JOIN wms_items i ON fl.item_id = i.id
            LEFT JOIN (
                SELECT item_id, period_start, SUM(sales_quantity + consumption_quantity) as actual_qty
                FROM planning_demand_history
                GROUP BY item_id, period_start
            ) pdh ON fl.item_id = pdh.item_id AND fl.period_start = pdh.period_start
            JOIN planning_forecast_runs fr ON fl.run_id = fr.id
            WHERE fr.status = 'APPROVED'
            GROUP BY fl.item_id
            ORDER BY accuracy ASC
        """).fetchall()

        return render_template('planning/report_forecast_accuracy.html',
            title='Forecast Accuracy Report',
            accuracy_data=accuracy_data,
            user_preferences=user_prefs or {}
        )

    @app.route('/planning/reports/inventory-turnover')
    @planning_permission_required('reports', 'view')
    def inventory_turnover_report():
        """Inventory turnover report."""

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        turnover_data = db.execute("""
            SELECT
                i.id, i.item_code, i.name,
                COALESCE(ib.quantity, 0) as current_stock,
                COALESCE(pdh.annual_demand, 0) as annual_consumption,
                CASE WHEN COALESCE(ib.quantity, 0) > 0
                     THEN COALESCE(pdh.annual_demand, 0) / COALESCE(ib.quantity, 0)
                     ELSE 0 END as turnover_ratio,
                CASE WHEN COALESCE(pdh.annual_demand, 0) > 0
                     THEN COALESCE(ib.quantity, 0) * 365 / COALESCE(pdh.annual_demand, 0)
                     ELSE 999 END as days_of_inventory
            FROM wms_items i
            LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
            LEFT JOIN (
                SELECT item_id, SUM(sales_quantity + consumption_quantity) * 12 as annual_demand
                FROM planning_demand_history
                WHERE period_start >= DATE('now', '-12 months')
                GROUP BY item_id
            ) pdh ON i.id = pdh.item_id
            WHERE i.is_active = 1
            ORDER BY turnover_ratio ASC
        """).fetchall()

        return render_template('planning/report_inventory_turnover.html',
            title='Inventory Turnover Report',
            turnover_data=turnover_data,
            user_preferences=user_prefs or {}
        )

    @app.route('/planning/reports/export/<string:report_type>')
    @planning_permission_required('reports', 'view')
    def planning_report_export(report_type):
        """Export a planning report to Excel."""

        db = get_db()
        wb = Workbook()
        ws = wb.active
        header_fill = PatternFill("solid", fgColor="1e40af")
        header_font = Font(color="FFFFFF", bold=True)

        if report_type == 'inventory_health':
            ws.title = "Inventory Health"
            ws.append(['Item Code', 'Name', 'Current Stock', 'Safety Stock',
                        'Reorder Point', 'Status'])
            rows = db.execute("""
                SELECT i.item_code, i.name,
                       COALESCE(ib.quantity, 0) as qty,
                       COALESCE(i.safety_stock, 0) as ss,
                       COALESCE(i.reorder_point, 0) as rop,
                       CASE WHEN COALESCE(ib.quantity, 0) <= 0 THEN 'STOCKOUT'
                            WHEN COALESCE(ib.quantity, 0) < COALESCE(i.safety_stock, 0) THEN 'BELOW_SAFETY'
                            WHEN COALESCE(ib.quantity, 0) < COALESCE(i.reorder_point, 0) THEN 'BELOW_ROP'
                            ELSE 'HEALTHY' END as status
                FROM wms_items i
                LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id
                WHERE i.is_active = 1
            """).fetchall()
            for row in rows:
                ws.append([row['item_code'], row['name'], row['qty'],
                            row['ss'], row['rop'], row['status']])

        elif report_type == 'purchase_suggestions':
            ws.title = "Purchase Suggestions"
            ws.append(['Item', 'Supplier', 'Qty', 'Est. Cost', 'Order Date',
                        'Arrival Date', 'Priority', 'Status'])
            rows = db.execute("""
                SELECT i.item_code, s.name as supplier, p.recommended_quantity,
                       p.estimated_total_cost, p.suggested_order_date,
                       p.suggested_arrival_date, p.priority, p.status
                FROM planning_purchase_recommendations p
                JOIN wms_items i ON p.item_id = i.id
                LEFT JOIN suppliers s ON p.supplier_id = s.id
                WHERE p.status = 'OPEN'
            """).fetchall()
            for row in rows:
                ws.append([row['item_code'], row['supplier'], row['recommended_quantity'],
                            row['estimated_total_cost'], row['suggested_order_date'],
                            row['suggested_arrival_date'], row['priority'], row['status']])

        elif report_type == 'forecast':
            ws.title = "Forecast Summary"
            ws.append(['Item Code', 'Name', 'Total Forecast', 'Avg Daily', 'Period'])
            rows = db.execute("""
                SELECT i.item_code, i.name,
                       SUM(fl.final_quantity) as total_fc,
                       AVG(fl.final_quantity) as avg_daily,
                       fr.run_name
                FROM planning_forecast_lines fl
                JOIN wms_items i ON fl.item_id = i.id
                JOIN planning_forecast_runs fr ON fl.run_id = fr.id
                WHERE fr.status IN ('DRAFT', 'APPROVED')
                GROUP BY fl.item_id, fr.id
            """).fetchall()
            for row in rows:
                ws.append([row['item_code'], row['name'], row['total_fc'],
                            row['avg_daily'], row['run_name']])

        elif report_type == 'alerts':
            ws.title = "Planning Alerts"
            ws.append(['Type', 'Severity', 'Title', 'Item', 'Created', 'Acknowledged'])
            rows = db.execute("""
                SELECT alert_type, severity, title, i.item_code,
                       a.created_at, CASE WHEN is_acknowledged = 1 THEN 'Yes' ELSE 'No' END
                FROM planning_alerts a
                LEFT JOIN wms_items i ON a.item_id = i.id
                ORDER BY a.created_at DESC
            """).fetchall()
            for row in rows:
                ws.append([row['alert_type'], row['severity'], row['title'],
                            row['item_code'], row['created_at'], row[5]])

        elif report_type == 'kpi':
            ws.title = "KPI Summary"
            ws.append(['KPI', 'Period Type', 'Period', 'Value', 'Target'])
            rows = db.execute("""
                SELECT kpi_name, period_type, period_start, value, target
                FROM planning_kpi_records
                ORDER BY period_start DESC
            """).fetchall()
            for row in rows:
                ws.append([row['kpi_name'], row['period_type'], row['period_start'],
                            row['value'], row['target']])

        else:
            flash('Unknown report type', 'error')
            return redirect(url_for('planning_reports'))

        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        as_attachment=True, download_name=f'planning_{report_type}_{datetime.now().strftime("%Y%m%d")}.xlsx')

    # ============================================================
    # PLANNING SETTINGS
    # ============================================================

    @app.route('/planning/settings')
    @planning_permission_required('settings', 'view')
    def planning_settings():
        """Planning settings page."""

        if not session.get('can_manage_users'):
            flash('Access denied. Planning settings require admin rights.', 'error')
            return redirect(url_for('planning_dashboard'))

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        settings = get_planning_settings(db)

        categories = db.execute("""
            SELECT DISTINCT category FROM planning_settings ORDER BY category
        """).fetchall()

        policies = db.execute("""
            SELECT * FROM planning_policies WHERE is_active = 1 ORDER BY name
        """).fetchall()

        return render_template('planning/settings.html',
            title='Planning Settings',
            settings=settings,
            categories=[r['category'] for r in categories],
            policies=policies,
            user_preferences=user_prefs or {}
        )

    @app.route('/planning/settings/save', methods=['POST'])
    @planning_permission_required('settings', 'edit')
    def planning_settings_save():
        """Save planning settings."""

        if not session.get('can_manage_users'):
            return jsonify({'error': 'Permission denied'}), 403

        db = get_db()

        for key, value in request.form.items():
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                save_planning_setting(db, setting_key, value)

        flash('Settings saved successfully', 'success')
        return redirect(url_for('planning_settings'))

    @app.route('/planning/settings/policy/save', methods=['POST'])
    @planning_permission_required('settings', 'edit')
    def planning_policy_save():
        """Save a planning policy."""

        db = get_db()
        policy_id = request.form.get('policy_id', type=int)
        name = request.form.get('name')
        policy_type = request.form.get('policy_type', 'REORDER_POINT')
        description = request.form.get('description', '')
        safety_stock_days = int(request.form.get('safety_stock_days', 7))
        safety_stock_factor = float(request.form.get('safety_stock_factor', 1.65))
        reorder_point_days = int(request.form.get('reorder_point_days', 3))
        min_stock = float(request.form.get('min_stock', 0))
        max_stock = float(request.form.get('max_stock', 0))
        forecast_method = request.form.get('forecast_method', 'MOVING_AVERAGE')
        forecast_horizon = int(request.form.get('forecast_horizon_days', 30))
        service_level = float(request.form.get('target_service_level', 0.95))
        moq = float(request.form.get('min_order_quantity', 0))
        order_multiple = float(request.form.get('order_multiple', 1))

        if policy_id:
            db.execute("""
                UPDATE planning_policies
                SET name = ?, policy_type = ?, description = ?,
                    safety_stock_days = ?, safety_stock_factor = ?,
                    reorder_point_days = ?, min_stock = ?, max_stock = ?,
                    forecast_method = ?, forecast_horizon_days = ?,
                    target_service_level = ?, min_order_quantity = ?,
                    order_multiple = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (name, policy_type, description, safety_stock_days, safety_stock_factor,
                  reorder_point_days, min_stock, max_stock, forecast_method, forecast_horizon,
                  service_level, moq, order_multiple, policy_id))
        else:
            cursor = db.execute("""
                INSERT INTO planning_policies
                (name, policy_type, description, safety_stock_days, safety_stock_factor,
                 reorder_point_days, min_stock, max_stock, forecast_method, forecast_horizon_days,
                 target_service_level, min_order_quantity, order_multiple, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, policy_type, description, safety_stock_days, safety_stock_factor,
                  reorder_point_days, min_stock, max_stock, forecast_method, forecast_horizon,
                  service_level, moq, order_multiple, session['user_id']))
            policy_id = cursor.lastrowid

        db.commit()
        log_planning_audit('POLICY_SAVED', 'planning_policy', policy_id,
                           user_id=session['user_id'],
                           changes={'name': name, 'type': policy_type})

        flash(f'Policy "{name}" saved', 'success')
        return redirect(url_for('planning_settings'))

    # ============================================================
    # DATA MANAGEMENT
    # ============================================================

    @app.route('/planning/aggregate-demand', methods=['POST'])
    @planning_permission_required('demand_analysis', 'edit')
    def aggregate_demand():
        """Aggregate demand data from WMS ledger into planning_demand_history."""

        db = get_db()
        months = int(request.form.get('months', 12))

        items = db.execute("SELECT id FROM wms_items WHERE is_active = 1").fetchall()
        processed = 0

        for item in items:
            aggregate_demand_from_ledger(db, item['id'], months=months)
            processed += 1

        flash(f'Aggregated demand data for {processed} items', 'success')
        return redirect(url_for('demand_analysis'))

    # ============================================================
    # API ENDPOINTS
    # ============================================================

    @app.route('/planning/api/dashboard-summary')
    @planning_permission_required('dashboard', 'view')
    def api_dashboard_summary():
        """API: Dashboard summary numbers."""

        db = get_db()
        today = datetime.now().date().strftime('%Y-%m-%d')

        summary = {
            'total_items': db.execute("SELECT COUNT(*) as n FROM wms_items WHERE is_active = 1").fetchone()['n'],
            'active_alerts': db.execute("SELECT COUNT(*) as n FROM planning_alerts WHERE is_acknowledged = 0").fetchone()['n'],
            'open_recommendations': db.execute("SELECT COUNT(*) as n FROM planning_replenishment_recommendations WHERE status = 'OPEN'").fetchone()['n'],
            'open_purchase_recs': db.execute("SELECT COUNT(*) as n FROM planning_purchase_recommendations WHERE status = 'OPEN'").fetchone()['n'],
            'pending_forecasts': db.execute("SELECT COUNT(*) as n FROM planning_forecast_runs WHERE status = 'DRAFT'").fetchone()['n'],
            'below_safety': db.execute("SELECT COUNT(*) as n FROM wms_items i JOIN wms_inventory_balances ib ON i.id = ib.item_id WHERE COALESCE(ib.quantity, 0) < COALESCE(i.safety_stock, 0) AND COALESCE(i.safety_stock, 0) > 0").fetchone()['n'],
            'below_rop': db.execute("SELECT COUNT(*) as n FROM wms_items i JOIN wms_inventory_balances ib ON i.id = ib.item_id WHERE COALESCE(ib.quantity, 0) < COALESCE(i.reorder_point, 0) AND COALESCE(i.reorder_point, 0) > 0").fetchone()['n'],
            'zero_stock': db.execute("SELECT COUNT(*) as n FROM wms_items i LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id WHERE COALESCE(ib.quantity, 0) <= 0").fetchone()['n'],
            'excess_stock': db.execute("SELECT COUNT(*) as n FROM wms_items i LEFT JOIN wms_inventory_balances ib ON i.id = ib.item_id WHERE COALESCE(ib.quantity, 0) > COALESCE(i.max_stock_level, 0) * 1.5 AND COALESCE(i.max_stock_level, 0) > 0").fetchone()['n'],
        }
        return jsonify(summary)

    @app.route('/planning/api/net-requirement/<int:item_id>')
    @planning_permission_required('replenishment', 'view')
    def api_net_requirement(item_id):
        """API: Get net requirement for an item."""

        db = get_db()
        days = request.args.get('days', 30, type=int)
        req = calculate_net_requirement(item_id, db, days_ahead=days)
        return jsonify(req or {})

    @app.route('/planning/api/demand-summary/<int:item_id>')
    @planning_permission_required('demand_analysis', 'view')
    def api_demand_summary(item_id):
        """API: Get demand summary for an item."""

        db = get_db()
        stats = get_demand_stats(db, item_id)
        pattern = None
        if stats:
            demand_values = [stats['avg_demand']] * 30
            pattern = classify_demand_pattern(demand_values)

        return jsonify({
            'stats': stats,
            'pattern': pattern
        })

    @app.route('/planning/api/item-profile/<int:item_id>')
    @planning_permission_required('demand_analysis', 'view')
    def api_item_profile(item_id):
        """API: Get planning profile for an item."""

        db = get_db()
        profile = db.execute(
            "SELECT * FROM planning_item_profiles WHERE item_id = ?", (item_id,)
        ).fetchone()

        item = db.execute("""
            SELECT i.*, c.name as category_name, b.name as brand_name
            FROM wms_items i
            LEFT JOIN wms_item_categories c ON i.category_id = c.id
            LEFT JOIN wms_item_brands b ON i.brand_id = b.id
            WHERE i.id = ?
        """, (item_id,)).fetchone()

        suppliers = db.execute("""
            SELECT s.id, s.name, its.lead_time_days, its.moq, its.unit_cost, its.is_preferred
            FROM wms_item_suppliers its
            JOIN suppliers s ON its.supplier_id = s.id
            WHERE its.item_id = ?
            ORDER BY its.is_preferred DESC, s.name
        """, (item_id,)).fetchall()

        current_stock = db.execute("""
            SELECT ib.warehouse_id, w.name as warehouse_name, ib.quantity, ib.reserved
            FROM wms_inventory_balances ib
            JOIN wms_warehouses w ON ib.warehouse_id = w.id
            WHERE ib.item_id = ?
        """, (item_id,)).fetchall()

        return jsonify({
            'profile': dict(profile) if profile else None,
            'item': dict(item) if item else None,
            'suppliers': [dict(s) for s in suppliers],
            'stock': [dict(s) for s in current_stock]
        })


# Import helpers from planning_models
from planning_models import (
    get_demand_stats, get_planning_settings, save_planning_setting,
    calculate_moving_average, calculate_weighted_moving_average,
    calculate_seasonal_index, calculate_trend, classify_demand_pattern,
    calculate_safety_stock, calculate_reorder_point, calculate_net_requirement,
    generate_planning_alerts, aggregate_demand_from_ledger, snapshot_kpis
)
