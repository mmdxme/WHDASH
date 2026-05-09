"""
Customer Demand Intelligence System - Routes and Services
======================================================
Flask routes providing all Customer Intelligence APIs and page rendering.

Covers:
- Dashboard
- Customer Profiles & Enrichment
- Customer Segments
- Retail / Wholesale Analysis
- Demand & Order Analysis
- Lost Sales
- Seasonality
- Basket Analysis
- Dependency Analysis
- Financial & Credit Analysis
- Logistics & Service Analysis
- Forecast Center
- Risk, Churn & Opportunity Alerts
- Recommendations & Action Center
- Reports
- Settings
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response
from functools import wraps
import sqlite3
import os
import json
import csv
import io
from datetime import datetime, timedelta
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

from models.customer_intelligence_models import get_ci_settings, update_ci_settings, log_ci_audit

DATABASE = os.environ.get('DATABASE_PATH', os.path.join(os.path.abspath(os.path.dirname(__file__)), 'warehouse.db'))


def get_db():
    """Get database connection with Row factory for dict-like access."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def ci_permission_required(permission=None):
    """Decorator to check Customer Intelligence permissions."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            if permission:
                user_perms = session.get('ci_permissions', [])
                if 'all' not in user_perms and permission not in user_perms and not session.get('can_manage_users'):
                    flash(f'You do not have permission: {permission}', 'error')
                    return redirect(url_for('ci_dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_ci_permissions(user_id=None):
    """Get CI permissions for a user."""
    db = get_db()
    if user_id is None:
        user_id = session.get('user_id')

    role = db.execute('SELECT can_manage_users FROM roles WHERE id = ?', (session.get('role_id'),)).fetchone()
    if role and role['can_manage_users']:
        return ['all']
    
    perms = db.execute('SELECT permission_key FROM ci_user_permissions WHERE user_id = ?', (user_id,)).fetchall()
    return [p['permission_key'] for p in perms]


# =============================================================================
# ANALYTICS COMPUTATION HELPERS
# =============================================================================

def compute_customer_metrics(customer_id, company_id=None):
    """Compute all intelligence metrics for a single customer from sdad_customers data."""
    db = get_db()
    try:
        c = db.execute("SELECT * FROM sdad_customers WHERE id = ?", (customer_id,)).fetchone()
        if not c:
            return None

        # Basic profile data
        metrics = {
            'customer_id': c['id'],
            'customer_name': c['name'],
            'phone': c.get('phone'),
            'email': c.get('email'),
            'city': c.get('city'),
            'country': c.get('country'),
            'location': c.get('location'),
            'salesperson_name': c.get('salesperson_name'),
            'total_orders': c.get('total_orders', 0) or 0,
            'total_payments': c.get('total_payments', 0) or 0,
            'total_debt': c.get('total_debt', 0) or 0,
            'credit_limit': c.get('credit_limit', 0) or 0,
            'credit_status': c.get('credit_status', 'Good'),
            'last_purchase_date': c.get('last_purchase_date'),
            'active': c.get('active', 1),
            'brand_names': c.get('brand_names', ''),
            'customer_group': c.get('customer_group', ''),
            'is_export': c.get('location') == 'export',
        }

        # Days since last purchase
        if c.get('last_purchase_date'):
            try:
                last_date = datetime.strptime(str(c['last_purchase_date']), '%Y-%m-%d')
                metrics['days_since_last_purchase'] = (datetime.now() - last_date).days
            except:
                metrics['days_since_last_purchase'] = 999
        else:
            metrics['days_since_last_purchase'] = 999

        # Credit utilization
        if metrics['credit_limit'] > 0:
            metrics['credit_utilization'] = metrics['total_debt'] / metrics['credit_limit']
        else:
            metrics['credit_utilization'] = 0

        # Payment performance
        if metrics['total_orders'] > 0 and metrics['total_payments'] >= 0:
            metrics['payment_ratio'] = metrics['total_payments'] / metrics['total_orders']
        else:
            metrics['payment_ratio'] = 0

        # Determine customer type
        metrics['customer_type'] = 'wholesale' if metrics['location'] in ['export', 'wholesale'] else 'retail'

        # Key customer flag based on revenue
        settings = db.execute("SELECT * FROM ci_settings WHERE id = 1").fetchone()
        key_threshold = dict(settings).get('key_customer_revenue_threshold', 50000) if settings else 50000
        metrics['is_key'] = 1 if metrics['total_orders'] >= key_threshold else 0

        # Profitable flag (assuming margin heuristic)
        metrics['is_profitable'] = 1 if metrics['payment_ratio'] > 0.7 else 0

        # Churn risk score
        inactive_threshold = dict(settings).get('inactive_days_threshold', 90) if settings else 90
        if metrics['days_since_last_purchase'] > inactive_threshold * 2:
            metrics['churn_risk_score'] = 0.9
        elif metrics['days_since_last_purchase'] > inactive_threshold:
            metrics['churn_risk_score'] = 0.6
        else:
            metrics['churn_risk_score'] = metrics['days_since_last_purchase'] / inactive_threshold * 0.5

        # Growth score (simplified - would need historical data)
        metrics['growth_score'] = 0.5  # Neutral

        return metrics
    finally:
        db.close()


def sync_customer_to_ci(customer_id):
    """Sync/enrich a single customer from sdad_customers into CI profile."""
    db = get_db()
    try:
        c = db.execute("SELECT * FROM sdad_customers WHERE id = ?", (customer_id,)).fetchone()
        if not c:
            return False

        metrics = compute_customer_metrics(customer_id)

        # Upsert into ci_customer_profiles
        db.execute("""
            INSERT INTO ci_customer_profiles 
            (customer_id, sdad_customer_id, customer_name, contact_person, phone, email,
             city, country, market, salesperson_id, is_active, is_key, is_profitable,
             credit_limit, outstanding_balance, churn_risk_score, growth_score,
             customer_type, payment_terms, transaction_currency, notes, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(customer_id) DO UPDATE SET
                customer_name = excluded.customer_name,
                phone = excluded.phone,
                email = excluded.email,
                city = excluded.city,
                country = excluded.country,
                outstanding_balance = excluded.outstanding_balance,
                churn_risk_score = excluded.churn_risk_score,
                growth_score = excluded.growth_score,
                is_key = excluded.is_key,
                is_profitable = excluded.is_profitable,
                updated_at = CURRENT_TIMESTAMP
        """, (
            c['id'], c['id'], c['name'], c.get('username', ''),
            c.get('phone'), c.get('email'), c.get('city'), c.get('country'),
            'export' if c.get('location') == 'export' else 'local',
            None, c.get('active', 1), metrics['is_key'], metrics['is_profitable'],
            c.get('credit_limit', 0) or 0, c.get('total_debt', 0) or 0,
            metrics['churn_risk_score'], metrics['growth_score'],
            metrics['customer_type'], c.get('payment_method', 'Net 30'),
            'AED', ''
        ))
        db.commit()
        return True
    finally:
        db.close()


def auto_sync_all_customers():
    """Sync all customers from sdad_customers to CI profiles."""
    db = get_db()
    try:
        customers = db.execute("SELECT id FROM sdad_customers").fetchall()
        count = 0
        for c in customers:
            if sync_customer_to_ci(c['id']):
                count += 1
        return count
    finally:
        db.close()


def generate_alerts_for_customer(customer_id):
    """Generate risk/churn alerts for a specific customer based on current metrics."""
    db = get_db()
    try:
        settings = db.execute("SELECT * FROM ci_settings WHERE id = 1").fetchone()
        if not settings:
            return []
        
        s = dict(settings)
        metrics = compute_customer_metrics(customer_id)
        if not metrics:
            return []
        
        alerts = []
        customer_name = metrics['customer_name']
        cid = metrics['customer_id']

        # Churn risk alert
        if metrics['churn_risk_score'] >= s.get('churn_risk_threshold_high', 0.75):
            alerts.append({
                'customer_id': cid,
                'alert_type': 'churn_risk',
                'alert_category': 'retention',
                'alert_level': 'High',
                'title': f'High churn risk: {customer_name}',
                'description': f'Customer has not purchased in {metrics["days_since_last_purchase"]} days.',
                'churn_risk_score': metrics['churn_risk_score'],
                'metric_value': metrics['churn_risk_score'],
                'threshold_value': s.get('churn_risk_threshold_high'),
                'recommended_action': 'Immediate sales follow-up recommended.'
            })
        elif metrics['churn_risk_score'] >= s.get('churn_risk_threshold_medium', 0.50):
            alerts.append({
                'customer_id': cid,
                'alert_type': 'churn_risk',
                'alert_category': 'retention',
                'alert_level': 'Medium',
                'title': f'Moderate churn risk: {customer_name}',
                'description': f'Customer activity declining.',
                'churn_risk_score': metrics['churn_risk_score'],
                'metric_value': metrics['churn_risk_score'],
                'threshold_value': s.get('churn_risk_threshold_medium'),
                'recommended_action': 'Schedule customer check-in.'
            })

        # Credit risk alert
        if metrics['credit_utilization'] >= s.get('credit_utilization_threshold', 0.90):
            alerts.append({
                'customer_id': cid,
                'alert_type': 'credit_risk',
                'alert_category': 'financial',
                'alert_level': 'High',
                'title': f'Credit limit breach: {customer_name}',
                'description': f'Outstanding debt {metrics["total_debt"]:,.0f} exceeds {metrics["credit_utilization"]*100:.0f}% of credit limit.',
                'metric_value': metrics['credit_utilization'],
                'threshold_value': s.get('credit_utilization_threshold'),
                'recommended_action': 'Review and suspend credit if necessary.'
            })

        # Growth opportunity (high-value active customers)
        if metrics['is_key'] and metrics['churn_risk_score'] < 0.3:
            alerts.append({
                'customer_id': cid,
                'alert_type': 'growth_opportunity',
                'alert_category': 'growth',
                'alert_level': 'High',
                'title': f'Key account opportunity: {customer_name}',
                'description': f'High-value customer with strong activity.',
                'growth_opportunity_score': metrics['growth_score'],
                'recommended_action': 'Develop upsell and cross-sell plan.'
            })

        # Insert alerts
        for alert in alerts:
            try:
                db.execute("""
                    INSERT INTO ci_risk_alerts 
                    (customer_id, alert_type, alert_category, alert_level, title, description,
                     metric_value, threshold_value, churn_risk_score, growth_opportunity_score, recommended_action)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert['customer_id'], alert['alert_type'], alert['alert_category'],
                    alert['alert_level'], alert['title'], alert['description'],
                    alert.get('metric_value'), alert.get('threshold_value'),
                    alert.get('churn_risk_score'), alert.get('growth_opportunity_score'),
                    alert.get('recommended_action')
                ))
            except Exception as e:
                print(f"Alert insert error: {e}")
        
        db.commit()
        return alerts
    finally:
        db.close()


# =============================================================================
# ROUTE REGISTRATION
# =============================================================================

def register_ci_routes(app):
    """Register all Customer Intelligence routes."""

    @app.route('/customer-intelligence/dashboard')
    @app.route('/customer-intelligence')
    @ci_permission_required('view_dashboard')
    def ci_dashboard():
        """Customer Intelligence main dashboard."""
        db = get_db()
        try:
            # Core stats
            total = db.execute("SELECT COUNT(*) as cnt FROM sdad_customers").fetchone()['cnt']
            active = db.execute("SELECT COUNT(*) as cnt FROM sdad_customers WHERE active = 1").fetchone()['cnt']
            
            # Customer type breakdown
            retail = db.execute("SELECT COUNT(*) as cnt FROM sdad_customers WHERE location NOT IN ('export', 'wholesale')").fetchone()['cnt']
            wholesale = db.execute("SELECT COUNT(*) as cnt FROM sdad_customers WHERE location IN ('wholesale', 'export')").fetchone()['cnt']
            export_customers = db.execute("SELECT COUNT(*) as cnt FROM sdad_customers WHERE location = 'export'").fetchone()['cnt']
            
            # Revenue stats
            total_revenue = db.execute("SELECT COALESCE(SUM(total_orders), 0) as t FROM sdad_customers").fetchone()['t']
            total_debt = db.execute("SELECT COALESCE(SUM(total_debt), 0) as t FROM sdad_customers").fetchone()['t']
            
            # Key customers (top 10% by revenue)
            key_threshold = db.execute("SELECT COALESCE(key_customer_revenue_threshold, 50000) as t FROM ci_settings WHERE id = 1").fetchone()['t']
            key_customers = db.execute("SELECT COUNT(*) as cnt FROM sdad_customers WHERE total_orders >= ?", (key_threshold,)).fetchone()['cnt']
            
            # High-risk customers
            inactive_threshold = db.execute("SELECT COALESCE(inactive_days_threshold, 90) as t FROM ci_settings WHERE id = 1").fetchone()['t']
            high_risk = db.execute("""
                SELECT COUNT(*) as cnt FROM sdad_customers 
                WHERE active = 1 AND (last_purchase_date IS NULL OR 
                    julianday('now') - julianday(last_purchase_date) > ?)
            """, (inactive_threshold,)).fetchone()['cnt']
            
            # New customers (last 30 days - using created_at)
            new_customers = db.execute("""
                SELECT COUNT(*) as cnt FROM sdad_customers 
                WHERE julianday('now') - julianday(created_at) <= 30
            """).fetchone()['cnt']
            
            # Location breakdown
            by_location = db.execute("""
                SELECT location, COUNT(*) as cnt, SUM(total_orders) as revenue 
                FROM sdad_customers GROUP BY location ORDER BY cnt DESC
            """).fetchall()
            
            # Top customers by revenue
            top_customers = db.execute("""
                SELECT name, total_orders, total_debt, city, country, salesperson_name, active
                FROM sdad_customers ORDER BY total_orders DESC LIMIT 10
            """).fetchall()
            
            # Salesperson distribution
            by_salesperson = db.execute("""
                SELECT salesperson_name, COUNT(*) as customers, SUM(total_orders) as revenue
                FROM sdad_customers WHERE salesperson_name != '' 
                GROUP BY salesperson_name ORDER BY revenue DESC LIMIT 10
            """).fetchall()
            
            # Recent alerts
            recent_alerts = db.execute("""
                SELECT a.*, c.name as customer_name 
                FROM ci_risk_alerts a
                LEFT JOIN sdad_customers c ON a.customer_id = c.id
                WHERE a.is_resolved = 0
                ORDER BY a.created_at DESC LIMIT 10
            """).fetchall()
            
            # Country distribution
            by_country = db.execute("""
                SELECT country, COUNT(*) as cnt, SUM(total_orders) as revenue
                FROM sdad_customers WHERE country != '' 
                GROUP BY country ORDER BY cnt DESC LIMIT 10
            """).fetchall()
            
            # Monthly trend (last 6 months of customer count)
            monthly_new = []
            for i in range(5, -1, -1):
                month_start = (datetime.now() - timedelta(days=30*i)).replace(day=1).strftime('%Y-%m-%d')
                month_end = (datetime.now() - timedelta(days=30*(i-1))).replace(day=1).strftime('%Y-%m-%d') if i > 0 else datetime.now().strftime('%Y-%m-%d')
                cnt = db.execute("""
                    SELECT COUNT(*) as cnt FROM sdad_customers 
                    WHERE created_at >= ? AND created_at < ?
                """, (month_start, month_end)).fetchone()['cnt']
                monthly_new.append({
                    'month': datetime.strptime(month_start, '%Y-%m-%d').strftime('%b %Y'),
                    'count': cnt
                })
            
            settings = dict(db.execute("SELECT * FROM ci_settings WHERE id = 1").fetchone())
            
            return render_template(
                'customer_intelligence/dashboard.html',
                title='Customer Intelligence',
                stats={
                    'total_customers': total,
                    'active_customers': active,
                    'inactive_customers': total - active,
                    'new_customers': new_customers,
                    'retail_customers': retail,
                    'wholesale_customers': wholesale,
                    'export_customers': export_customers,
                    'key_customers': key_customers,
                    'high_risk_customers': high_risk,
                    'total_revenue': total_revenue,
                    'total_debt': total_debt,
                },
                by_location=[dict(r) for r in by_location],
                top_customers=[dict(r) for r in top_customers],
                by_salesperson=[dict(r) for r in by_salesperson],
                by_country=[dict(r) for r in by_country],
                recent_alerts=[dict(r) for r in recent_alerts],
                monthly_new=monthly_new,
                settings=settings
            )
        finally:
            db.close()

    # ── Customer Profiles ──────────────────────────────────────────────────────

    @app.route('/customer-intelligence/profiles')
    @ci_permission_required('view_profiles')
    def ci_profiles():
        """Customer Intelligence - Customer Profiles list."""
        db = get_db()
        try:
            page = request.args.get('page', 1, type=int)
            per_page = 50
            offset = (page - 1) * per_page
            
            search = request.args.get('search', '')
            sort_by = request.args.get('sort', 'total_orders')
            sort_dir = request.args.get('dir', 'desc').upper()
            if sort_dir not in ('ASC', 'DESC'):
                sort_dir = 'DESC'
            customer_type = request.args.get('type', '')
            market = request.args.get('market', '')
            salesperson_list = request.args.getlist('salesperson') if request.args.getlist('salesperson') else ['']
            active_filter_list = request.args.getlist('active') if request.args.getlist('active') else ['']
            type_list = request.args.getlist('type') if request.args.getlist('type') else ['']
            market_list = request.args.getlist('market') if request.args.getlist('market') else ['']

            query = "SELECT * FROM sdad_customers WHERE 1=1"
            count_query = "SELECT COUNT(*) as cnt FROM sdad_customers WHERE 1=1"
            params = []

            if search:
                query += " AND (name LIKE ? OR customer_code LIKE ? OR phone LIKE ?)"
                count_query += " AND (name LIKE ? OR customer_code LIKE ? OR phone LIKE ?)"
                params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])

            if type_list and type_list != ['']:
                placeholders = ','.join('?' * len(type_list))
                query += f" AND location IN ({placeholders})"
                count_query += f" AND location IN ({placeholders})"
                params.extend(type_list)

            if market_list and market_list != ['']:
                market_clauses = []
                for m in market_list:
                    if m == 'export':
                        market_clauses.append("location = 'export'")
                    elif m == 'local':
                        market_clauses.append("location != 'export'")
                if market_clauses:
                    clause = '(' + ' OR '.join(market_clauses) + ')'
                    query += f" AND {clause}"
                    count_query += f" AND {clause}"

            if salesperson_list and salesperson_list != ['']:
                placeholders = ','.join('?' * len(salesperson_list))
                query += f" AND salesperson_name IN ({placeholders})"
                count_query += f" AND salesperson_name IN ({placeholders})"
                params.extend(salesperson_list)

            if active_filter_list and active_filter_list != ['']:
                active_clauses = []
                for af in active_filter_list:
                    if af == 'active':
                        active_clauses.append('active = 1')
                    elif af == 'inactive':
                        active_clauses.append('active = 0')
                if active_clauses:
                    query += " AND (" + ' OR '.join(active_clauses) + ')'
                    count_query += " AND (" + ' OR '.join(active_clauses) + ')'

            # Sorting
            sort_col = 'total_orders' if sort_by == 'revenue' else sort_by if sort_by in ('name', 'total_orders', 'total_debt', 'credit_limit', 'last_purchase_date') else 'total_orders'
            query += f" ORDER BY {sort_col} {sort_dir} LIMIT {per_page} OFFSET {offset}"
            
            total_count = db.execute(count_query, params).fetchone()['cnt']
            customers = db.execute(query, params).fetchall()
            salespersons = db.execute("SELECT DISTINCT salesperson_name FROM sdad_customers WHERE salesperson_name != '' ORDER BY salesperson_name").fetchall()
            
            return render_template(
                'customer_intelligence/profiles.html',
                title='Customer Profiles',
                customers=[dict(r) for r in customers],
                salespersons=[r['salesperson_name'] for r in salespersons],
                pagination={
                    'page': page,
                    'per_page': per_page,
                    'total': total_count,
                    'pages': (total_count + per_page - 1) // per_page
                },
                filters={
                    'search': search,
                    'type': type_list,
                    'market': market_list,
                    'salesperson': salesperson_list,
                    'active': active_filter_list,
                    'sort': sort_by,
                    'dir': sort_dir
                }
            )
        finally:
            db.close()

    @app.route('/customer-intelligence/profiles/<int:customer_id>')
    @ci_permission_required('view_profiles')
    def ci_profile_detail(customer_id):
        """Customer Intelligence - Customer Profile Detail."""
        db = get_db()
        try:
            customer = db.execute("SELECT * FROM sdad_customers WHERE id = ?", (customer_id,)).fetchone()
            if not customer:
                flash("Customer not found.", "error")
                return redirect(url_for('ci_profiles'))
            
            c = dict(customer)
            metrics = compute_customer_metrics(customer_id)
            
            # Get CI profile if exists
            ci_profile = db.execute("SELECT * FROM ci_customer_profiles WHERE customer_id = ?", (customer_id,)).fetchone()
            
            # Get alerts for this customer
            alerts = db.execute("""
                SELECT * FROM ci_risk_alerts WHERE customer_id = ? AND is_resolved = 0
                ORDER BY created_at DESC LIMIT 10
            """, (customer_id,)).fetchall()
            
            # Get recommendations
            recommendations = db.execute("""
                SELECT * FROM ci_recommendations WHERE customer_id = ? AND status = 'Open'
                ORDER BY priority DESC, created_at DESC LIMIT 10
            """, (customer_id,)).fetchall()
            
            # Get KPIs
            kpis = db.execute("""
                SELECT * FROM ci_kpi_records WHERE customer_id = ?
                ORDER BY recorded_at DESC LIMIT 20
            """, (customer_id,)).fetchall()
            
            # Financial summary
            fin_profile = db.execute("SELECT * FROM ci_financial_profiles WHERE customer_id = ?", (customer_id,)).fetchone()
            
            # Logistics profile
            log_profile = db.execute("SELECT * FROM ci_logistics_profiles WHERE customer_id = ?", (customer_id,)).fetchone()
            
            # Retail behavior
            retail_b = db.execute("SELECT * FROM ci_retail_behavior WHERE customer_id = ?", (customer_id,)).fetchone()
            
            # Wholesale behavior
            wholesale_b = db.execute("SELECT * FROM ci_wholesale_behavior WHERE customer_id = ?", (customer_id,)).fetchone()
            
            # Seasonality
            seasonality = db.execute("SELECT * FROM ci_customer_seasonality WHERE customer_id = ?", (customer_id,)).fetchone()
            
            # Demand history
            demand_history = db.execute("""
                SELECT * FROM ci_customer_demand_history WHERE customer_id = ?
                ORDER BY record_date DESC LIMIT 12
            """, (customer_id,)).fetchall()
            
            # Lost sales
            lost_sales = db.execute("""
                SELECT * FROM ci_lost_sales WHERE customer_id = ?
                ORDER BY lost_date DESC LIMIT 10
            """, (customer_id,)).fetchall()
            
            # Segments
            segments = db.execute("""
                SELECT s.* FROM ci_customer_segments s
                JOIN ci_segment_members m ON s.id = m.segment_id
                WHERE m.customer_id = ?
            """, (customer_id,)).fetchall()
            
            return render_template(
                'customer_intelligence/profile_detail.html',
                title=f'Profile: {c["name"]}',
                customer=c,
                metrics=metrics or {},
                ci_profile=dict(ci_profile) if ci_profile else None,
                alerts=[dict(r) for r in alerts],
                recommendations=[dict(r) for r in recommendations],
                kpis=[dict(r) for r in kpis],
                fin_profile=dict(fin_profile) if fin_profile else None,
                log_profile=dict(log_profile) if log_profile else None,
                retail_b=dict(retail_b) if retail_b else None,
                wholesale_b=dict(wholesale_b) if wholesale_b else None,
                seasonality=dict(seasonality) if seasonality else None,
                demand_history=[dict(r) for r in demand_history],
                lost_sales=[dict(r) for r in lost_sales],
                segments=[dict(r) for r in segments]
            )
        finally:
            db.close()

    @app.route('/customer-intelligence/profiles/<int:customer_id>/enrich', methods=['POST'])
    @ci_permission_required('edit_profiles')
    def ci_enrich_profile(customer_id):
        """Enrich/sync a customer into the CI system."""
        sync_customer_to_ci(customer_id)
        generate_alerts_for_customer(customer_id)
        flash("Customer profile enriched successfully.", "success")
        return redirect(url_for('ci_profile_detail', customer_id=customer_id))

    @app.route('/customer-intelligence/profiles/create', methods=['GET', 'POST'])
    @ci_permission_required('edit_profiles')
    def ci_profile_create():
        """Create a new customer."""
        db = get_db()
        try:
            if request.method == 'POST':
                name = request.form.get('name', '').strip()
                if not name:
                    flash("Customer name is required.", "error")
                    return redirect(url_for('ci_profile_create'))

                db.execute("""
                    INSERT INTO sdad_customers (name, phone, email, city, country, location,
                        salesperson_name, credit_limit, payment_method, active, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, CURRENT_TIMESTAMP)
                """, (
                    name,
                    request.form.get('phone'),
                    request.form.get('email'),
                    request.form.get('city'),
                    request.form.get('country'),
                    request.form.get('location', 'retail'),
                    request.form.get('salesperson_name'),
                    request.form.get('credit_limit', 0, type=float),
                    request.form.get('payment_method', 'Net 30')
                ))
                db.commit()
                flash(f"Customer '{name}' created.", "success")
                return redirect(url_for('ci_profiles'))

            return render_template('customer_intelligence/profile_edit.html', title='Create Customer')
        finally:
            db.close()

    @app.route('/customer-intelligence/profiles/<int:customer_id>/edit', methods=['GET', 'POST'])
    @ci_permission_required('edit_profiles')
    def ci_profile_edit(customer_id):
        """Edit an existing customer."""
        db = get_db()
        try:
            customer = db.execute("SELECT * FROM sdad_customers WHERE id = ?", (customer_id,)).fetchone()
            if not customer:
                flash("Customer not found.", "error")
                return redirect(url_for('ci_profiles'))

            if request.method == 'POST':
                db.execute("""
                    UPDATE sdad_customers SET
                        name = ?, phone = ?, email = ?, city = ?, country = ?,
                        location = ?, salesperson_name = ?, credit_limit = ?,
                        payment_method = ?, active = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    request.form.get('name'),
                    request.form.get('phone'),
                    request.form.get('email'),
                    request.form.get('city'),
                    request.form.get('country'),
                    request.form.get('location'),
                    request.form.get('salesperson_name'),
                    request.form.get('credit_limit', 0, type=float),
                    request.form.get('payment_method'),
                    1 if request.form.get('active') else 0,
                    customer_id
                ))
                db.commit()
                flash("Customer updated.", "success")
                return redirect(url_for('ci_profile_detail', customer_id=customer_id))

            return render_template('customer_intelligence/profile_edit.html',
                                 title=f'Edit: {customer["name"]}',
                                 customer=dict(customer))
        finally:
            db.close()

    @app.route('/customer-intelligence/profiles/delete', methods=['POST'])
    @ci_permission_required('edit_profiles')
    def ci_delete_customers():
        """Delete multiple customers."""
        import json
        db = get_db()
        try:
            data = request.get_json()
            customer_ids = data.get('customer_ids', [])
            if not customer_ids:
                return jsonify({'success': False, 'error': 'No customers selected'}), 400
            placeholders = ','.join('?' * len(customer_ids))
            db.execute(f"DELETE FROM sdad_customers WHERE id IN ({placeholders})", customer_ids)
            return jsonify({'success': True, 'deleted': len(customer_ids)})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            db.close()

    # ── Segments ──────────────────────────────────────────────────────────────

    @app.route('/customer-intelligence/segments')
    @ci_permission_required('manage_segments')
    def ci_segments():
        """Customer Intelligence - Segments."""
        db = get_db()
        try:
            segments = db.execute("""
                SELECT s.*, 
                    (SELECT COUNT(*) FROM ci_segment_members WHERE segment_id = s.id) as member_count,
                    u.username as created_by_name
                FROM ci_customer_segments s
                LEFT JOIN users u ON s.created_by = u.id
                ORDER BY s.is_system DESC, s.segment_name
            """).fetchall()
            
            return render_template(
                'customer_intelligence/segments.html',
                title='Customer Segments',
                segments=[dict(r) for r in segments]
            )
        finally:
            db.close()

    @app.route('/customer-intelligence/segments/<int:segment_id>')
    @ci_permission_required('view_profiles')
    def ci_segment_detail(segment_id):
        """View segment members."""
        db = get_db()
        try:
            segment = db.execute("SELECT * FROM ci_customer_segments WHERE id = ?", (segment_id,)).fetchone()
            if not segment:
                flash("Segment not found.", "error")
                return redirect(url_for('ci_segments'))

            members = db.execute("""
                SELECT c.*, m.added_at
                FROM ci_segment_members m
                JOIN sdad_customers c ON m.customer_id = c.id
                WHERE m.segment_id = ?
                ORDER BY c.total_orders DESC
            """, (segment_id,)).fetchall()

            return render_template(
                'customer_intelligence/segment_detail.html',
                title=f'Segment: {segment["segment_name"]}',
                segment=dict(segment),
                members=[dict(r) for r in members]
            )
        finally:
            db.close()

    @app.route('/customer-intelligence/segments/create', methods=['GET', 'POST'])
    @ci_permission_required('manage_segments')
    def ci_segment_create():
        """Create a new segment."""
        db = get_db()
        try:
            if request.method == 'POST':
                name = request.form.get('segment_name', '').strip()
                code = request.form.get('segment_code', '').strip()
                seg_type = request.form.get('segment_type', 'behavioral')
                description = request.form.get('description', '')
                is_dynamic = 1 if request.form.get('is_dynamic') else 0

                if not name or not code:
                    flash("Name and code are required.", "error")
                    return redirect(url_for('ci_segment_create'))

                db.execute("""
                    INSERT INTO ci_customer_segments
                    (segment_name, segment_code, segment_type, description, is_dynamic, created_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (name, code, seg_type, description, is_dynamic, session.get('user_id')))
                db.commit()
                flash(f"Segment '{name}' created.", "success")
                return redirect(url_for('ci_segments'))

            return render_template('customer_intelligence/segment_create.html', title='Create Segment')
        finally:
            db.close()

    @app.route('/customer-intelligence/segments/<int:segment_id>/add-customers', methods=['POST'])
    @ci_permission_required('manage_segments')
    def ci_segment_add_customers(segment_id):
        """Add customers to a segment."""
        db = get_db()
        try:
            data = request.get_json()
            customer_ids = data.get('customer_ids', [])
            if not customer_ids:
                return jsonify({'success': False, 'error': 'No customers selected'}), 400

            for cid in customer_ids:
                db.execute("""
                    INSERT OR IGNORE INTO ci_segment_members (segment_id, customer_id, added_by)
                    VALUES (?, ?, ?)
                """, (segment_id, cid, session.get('user_id')))
            db.commit()
            return jsonify({'success': True, 'added': len(customer_ids)})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            db.close()

    @app.route('/customer-intelligence/segments/<int:segment_id>/remove-customers', methods=['POST'])
    @ci_permission_required('manage_segments')
    def ci_segment_remove_customers(segment_id):
        """Remove customers from a segment."""
        db = get_db()
        try:
            data = request.get_json()
            customer_ids = data.get('customer_ids', [])
            if not customer_ids:
                return jsonify({'success': False, 'error': 'No customers selected'}), 400

            placeholders = ','.join('?' * len(customer_ids))
            db.execute(f"DELETE FROM ci_segment_members WHERE segment_id = ? AND customer_id IN ({placeholders})",
                       [segment_id] + customer_ids)
            db.commit()
            return jsonify({'success': True, 'removed': len(customer_ids)})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
        finally:
            db.close()

    # ── RFM Analysis ───────────────────────────────────────────────────────────

    @app.route('/customer-intelligence/rfm')
    @ci_permission_required('view_analytics')
    def ci_rfm_analysis():
        """RFM (Recency, Frequency, Monetary) segmentation analysis."""
        db = get_db()
        try:
            today = datetime.now()

            # Compute RFM scores for all customers
            rfm_data = db.execute("""
                SELECT
                    c.id,
                    c.name,
                    c.city,
                    c.country,
                    c.total_orders,
                    c.total_payments,
                    c.last_purchase_date,
                    c.active,
                    julianday('now') - julianday(COALESCE(c.last_purchase_date, c.created_at)) as days_inactive
                FROM sdad_customers c
                WHERE c.active = 1
            """).fetchall()

            # Score customers: R=1-3, F=1-3, M=1-3
            rfm_records = []
            for c in rfm_data:
                d = dict(c)

                # Recency: lower days_inactive = better (score 3), >180 days = score 1
                if d['days_inactive'] <= 30:
                    r_score = 3
                elif d['days_inactive'] <= 90:
                    r_score = 2
                else:
                    r_score = 1

                # Frequency: based on total_orders (proxy for order count)
                orders = d['total_orders'] or 0
                if orders >= 50000:
                    f_score = 3
                elif orders >= 10000:
                    f_score = 2
                else:
                    f_score = 1

                # Monetary: total_payments as proxy
                payments = d['total_payments'] or 0
                if payments >= 40000:
                    m_score = 3
                elif payments >= 10000:
                    m_score = 2
                else:
                    m_score = 1

                rfm_score = r_score * 100 + f_score * 10 + m_score

                # Segment label
                if rfm_score >= 333:
                    segment = 'Champions'
                    seg_color = 'purple'
                elif rfm_score >= 323:
                    segment = 'Loyal'
                    seg_color = 'blue'
                elif rfm_score >= 313:
                    segment = 'Promising'
                    seg_color = 'cyan'
                elif rfm_score >= 233:
                    segment = 'At Risk'
                    seg_color = 'amber'
                elif rfm_score >= 133:
                    segment = 'Needs Attention'
                    seg_color = 'orange'
                else:
                    segment = 'Churned'
                    seg_color = 'red'

                rfm_records.append({
                    'id': d['id'],
                    'name': d['name'],
                    'city': d['city'],
                    'country': d['country'],
                    'total_orders': d['total_orders'],
                    'total_payments': d['total_payments'],
                    'days_inactive': int(d['days_inactive']),
                    'r_score': r_score,
                    'f_score': f_score,
                    'm_score': m_score,
                    'rfm_score': rfm_score,
                    'segment': segment,
                    'seg_color': seg_color,
                    'active': d['active']
                })

            # Sort by RFM score descending
            rfm_records.sort(key=lambda x: x['rfm_score'], reverse=True)

            # Summary counts
            segment_summary = {}
            for r in rfm_records:
                seg = r['segment']
                if seg not in segment_summary:
                    segment_summary[seg] = {'count': 0, 'total_revenue': 0, 'color': r['seg_color']}
                segment_summary[seg]['count'] += 1
                segment_summary[seg]['total_revenue'] += r['total_orders'] or 0

            # RFM matrix data (count per R x F combination)
            rfm_matrix = {}
            for r in rfm_records:
                key = f"R{r['r_score']}F{r['f_score']}"
                rfm_matrix[key] = rfm_matrix.get(key, 0) + 1

            return render_template(
                'customer_intelligence/rfm.html',
                title='RFM Analysis',
                rfm_records=rfm_records[:200],
                segment_summary=segment_summary,
                rfm_matrix=rfm_matrix,
                total_analyzed=len(rfm_records)
            )
        finally:
            db.close()

    @app.route('/customer-intelligence/rfm/export')
    @ci_permission_required('export_reports')
    def ci_rfm_export():
        """Export RFM analysis as CSV."""
        db = get_db()
        try:
            today = datetime.now()
            rfm_data = db.execute("""
                SELECT
                    c.id, c.name, c.city, c.country, c.total_orders, c.total_payments,
                    c.last_purchase_date, c.active,
                    julianday('now') - julianday(COALESCE(c.last_purchase_date, c.created_at)) as days_inactive
                FROM sdad_customers c WHERE c.active = 1
            """).fetchall()

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Customer ID', 'Name', 'City', 'Country', 'Total Orders', 'Total Payments',
                             'Last Purchase', 'Days Inactive', 'R Score', 'F Score', 'M Score', 'RFM Score', 'Segment'])

            for c in rfm_data:
                d = dict(c)
                days = int(d['days_inactive'])
                r_score = 3 if days <= 30 else (2 if days <= 90 else 1)
                f_score = 3 if (d['total_orders'] or 0) >= 50000 else (2 if (d['total_orders'] or 0) >= 10000 else 1)
                m_score = 3 if (d['total_payments'] or 0) >= 40000 else (2 if (d['total_payments'] or 0) >= 10000 else 1)
                rfm_score = r_score * 100 + f_score * 10 + m_score

                if rfm_score >= 333:
                    segment = 'Champions'
                elif rfm_score >= 323:
                    segment = 'Loyal'
                elif rfm_score >= 313:
                    segment = 'Promising'
                elif rfm_score >= 233:
                    segment = 'At Risk'
                elif rfm_score >= 133:
                    segment = 'Needs Attention'
                else:
                    segment = 'Churned'

                writer.writerow([d['id'], d['name'], d['city'], d['country'], d['total_orders'],
                                 d['total_payments'], d['last_purchase_date'], days,
                                 r_score, f_score, m_score, rfm_score, segment])

            output.seek(0)
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=CI_RFM_{today.strftime("%Y%m%d")}.csv'}
            )
        finally:
            db.close()

    # ── Demand & Order Analysis ───────────────────────────────────────────────

    @app.route('/customer-intelligence/demand')
    @ci_permission_required('view_analytics')
    def ci_demand():
        """Customer Intelligence - Demand & Order Analysis."""
        db = get_db()
        try:
            # Summary stats
            total_demand = db.execute("SELECT COALESCE(SUM(total_orders), 0) as t FROM sdad_customers").fetchone()['t']
            
            # Top demanders
            top_demand = db.execute("""
                SELECT id, name, total_orders, city, country, salesperson_name,
                       last_purchase_date, active
                FROM sdad_customers
                ORDER BY total_orders DESC LIMIT 50
            """).fetchall()
            
            # Demand by location
            demand_by_location = db.execute("""
                SELECT location, COUNT(*) as customers, 
                       SUM(total_orders) as total_demand,
                       AVG(total_orders) as avg_demand
                FROM sdad_customers GROUP BY location
            """).fetchall()
            
            # Demand by country
            demand_by_country = db.execute("""
                SELECT country, COUNT(*) as customers,
                       SUM(total_orders) as total_demand
                FROM sdad_customers WHERE country != '' 
                GROUP BY country ORDER BY total_demand DESC LIMIT 20
            """).fetchall()
            
            # By salesperson
            demand_by_sp = db.execute("""
                SELECT salesperson_name, COUNT(*) as customers,
                       SUM(total_orders) as total_demand,
                       AVG(total_orders) as avg_demand
                FROM sdad_customers WHERE salesperson_name != ''
                GROUP BY salesperson_name ORDER BY total_demand DESC
            """).fetchall()
            
            return render_template(
                'customer_intelligence/demand.html',
                title='Demand & Order Analysis',
                total_demand=total_demand,
                top_demand=[dict(r) for r in top_demand],
                demand_by_location=[dict(r) for r in demand_by_location],
                demand_by_country=[dict(r) for r in demand_by_country],
                demand_by_salesperson=[dict(r) for r in demand_by_sp]
            )
        finally:
            db.close()

    # ── Lost Sales ────────────────────────────────────────────────────────────

    @app.route('/customer-intelligence/lost-sales')
    @ci_permission_required('view_lost_sales')
    def ci_lost_sales():
        """Customer Intelligence - Lost Sales & Unmet Demand."""
        db = get_db()
        try:
            lost_sales = db.execute("""
                SELECT l.*, c.name as customer_name, c.city, c.country
                FROM ci_lost_sales l
                LEFT JOIN sdad_customers c ON l.customer_id = c.id
                ORDER BY l.lost_date DESC LIMIT 100
            """).fetchall()
            
            total_lost = db.execute("SELECT COALESCE(SUM(lost_amount), 0) as t FROM ci_lost_sales").fetchone()['t']
            total_lost_profit = db.execute("SELECT COALESCE(SUM(lost_profit), 0) as t FROM ci_lost_sales").fetchone()['t']
            
            by_reason = db.execute("""
                SELECT reason_category, COUNT(*) as cnt, SUM(lost_amount) as total
                FROM ci_lost_sales GROUP BY reason_category
            """).fetchall()

            customers_for_dropdown = db.execute(
                "SELECT id, name FROM sdad_customers ORDER BY total_orders DESC LIMIT 200"
            ).fetchall()

            return render_template(
                'customer_intelligence/lost_sales.html',
                title='Lost Sales & Unmet Demand',
                lost_sales=[dict(r) for r in lost_sales],
                total_lost=total_lost,
                total_lost_profit=total_lost_profit,
                by_reason=[dict(r) for r in by_reason],
                customers_for_dropdown=[dict(r) for r in customers_for_dropdown]
            )
        finally:
            db.close()

    @app.route('/customer-intelligence/lost-sales/add', methods=['POST'])
    @ci_permission_required('manage_lost_sales')
    def ci_lost_sales_add():
        """Add a lost sales record."""
        db = get_db()
        try:
            customer_id = request.form.get('customer_id', type=int)
            reason = request.form.get('reason', '')
            reason_category = request.form.get('reason_category', 'Stockout')
            lost_amount = request.form.get('lost_amount', 0, type=float)
            competitor = request.form.get('competitor_name', '')
            notes = request.form.get('notes', '')
            
            db.execute("""
                INSERT INTO ci_lost_sales 
                (customer_id, lost_date, reason, reason_category, lost_amount, competitor_name, follow_up_notes)
                VALUES (?, DATE('now'), ?, ?, ?, ?, ?)
            """, (customer_id, reason, reason_category, lost_amount, competitor, notes))
            db.commit()
            flash("Lost sales record added.", "success")
        except Exception as e:
            flash(f"Error: {e}", "error")
        finally:
            db.close()
        return redirect(request.referrer or url_for('ci_lost_sales'))

    # ── Seasonality ────────────────────────────────────────────────────────────

    @app.route('/customer-intelligence/seasonality')
    @ci_permission_required('view_analytics')
    def ci_seasonality():
        """Customer Intelligence - Seasonality & Time Patterns."""
        db = get_db()
        try:
            seasonality_data = db.execute("""
                SELECT s.*, c.name as customer_name
                FROM ci_customer_seasonality s
                LEFT JOIN sdad_customers c ON s.customer_id = c.id
                ORDER BY c.total_orders DESC LIMIT 100
            """).fetchall()
            
            return render_template(
                'customer_intelligence/seasonality.html',
                title='Seasonality & Time Patterns',
                seasonality_data=[dict(r) for r in seasonality_data]
            )
        finally:
            db.close()

    # ── Financial & Credit Analysis ───────────────────────────────────────────

    @app.route('/customer-intelligence/financial')
    @ci_permission_required('view_financial')
    def ci_financial():
        """Customer Intelligence - Financial & Credit Analysis."""
        db = get_db()
        try:
            # Financial summary
            total_revenue = db.execute("SELECT COALESCE(SUM(total_orders), 0) as t FROM sdad_customers").fetchone()['t']
            total_debt = db.execute("SELECT COALESCE(SUM(total_debt), 0) as t FROM sdad_customers").fetchone()['t']
            total_payments = db.execute("SELECT COALESCE(SUM(total_payments), 0) as t FROM sdad_customers").fetchone()['t']
            
            # Credit risk distribution
            credit_risky = db.execute("SELECT COUNT(*) as cnt FROM sdad_customers WHERE is_credit_blocked = 1").fetchone()['cnt']
            total_customers = db.execute("SELECT COUNT(*) as cnt FROM sdad_customers").fetchone()['cnt']
            credit_ok = total_customers - credit_risky
            
            # Top debtors
            top_debtors = db.execute("""
                SELECT name, total_debt, credit_limit, credit_status, city, country
                FROM sdad_customers 
                ORDER BY total_debt DESC LIMIT 30
            """).fetchall()
            
            # Payment discipline
            payment_analysis = db.execute("""
                SELECT payment_method, COUNT(*) as cnt, SUM(total_orders) as revenue
                FROM sdad_customers WHERE payment_method != ''
                GROUP BY payment_method
            """).fetchall()
            
            return render_template(
                'customer_intelligence/financial.html',
                title='Financial & Credit Analysis',
                total_revenue=total_revenue,
                total_debt=total_debt,
                total_payments=total_payments,
                credit_risky=credit_risky,
                top_debtors=[dict(r) for r in top_debtors],
                payment_analysis=[dict(r) for r in payment_analysis]
            )
        finally:
            db.close()

    # ── Logistics & Service Analysis ─────────────────────────────────────────

    @app.route('/customer-intelligence/logistics')
    @ci_permission_required('view_logistics')
    def ci_logistics():
        """Customer Intelligence - Logistics & Service Analysis."""
        db = get_db()
        try:
            # Delivery-based stats
            delivery_customers = db.execute("""
                SELECT c.name, c.city, c.country, c.salesperson_name,
                       c.total_orders, c.total_debt, c.active
                FROM sdad_customers c
                WHERE c.location NOT IN ('export')
                ORDER BY c.total_orders DESC LIMIT 50
            """).fetchall()
            
            export_customers = db.execute("""
                SELECT * FROM sdad_customers 
                WHERE location = 'export'
                ORDER BY total_orders DESC LIMIT 50
            """).fetchall()
            
            return render_template(
                'customer_intelligence/logistics.html',
                title='Logistics & Service Analysis',
                delivery_customers=[dict(r) for r in delivery_customers],
                export_customers=[dict(r) for r in export_customers]
            )
        finally:
            db.close()

    # ── Forecast Center ──────────────────────────────────────────────────────

    @app.route('/customer-intelligence/forecast')
    @ci_permission_required('view_forecast')
    def ci_forecast():
        """Customer Intelligence - Forecast Center."""
        db = get_db()
        try:
            forecast_runs = db.execute("""
                SELECT r.*, u.username as created_by_name,
                    (SELECT COUNT(*) FROM ci_forecast_lines WHERE run_id = r.id) as line_count
                FROM ci_forecast_runs r
                LEFT JOIN users u ON r.created_by = u.id
                ORDER BY r.created_at DESC LIMIT 20
            """).fetchall()
            
            # Active forecasts
            active_forecast = db.execute("""
                SELECT * FROM ci_forecast_runs WHERE status = 'completed'
                ORDER BY created_at DESC LIMIT 1
            """).fetchone()
            
            forecast_lines = []
            if active_forecast:
                forecast_lines = db.execute("""
                    SELECT l.*, c.name as customer_name, c.city
                    FROM ci_forecast_lines l
                    JOIN sdad_customers c ON l.customer_id = c.id
                    WHERE l.run_id = ?
                    ORDER BY l.predicted_demand DESC LIMIT 100
                """, (active_forecast['id'],)).fetchall()
            
            return render_template(
                'customer_intelligence/forecast.html',
                title='Forecast Center',
                forecast_runs=[dict(r) for r in forecast_runs],
                active_forecast=dict(active_forecast) if active_forecast else None,
                forecast_lines=[dict(r) for r in forecast_lines]
            )
        finally:
            db.close()

    @app.route('/customer-intelligence/forecast/generate', methods=['POST'])
    @ci_permission_required('generate_forecast')
    def ci_forecast_generate():
        """Generate a new demand forecast."""
        db = get_db()
        try:
            forecast_type = request.form.get('forecast_type', 'customer_demand')
            period_months = request.form.get('period_months', 6, type=int)
            customer_scope = request.form.get('customer_scope', 'all')
            
            run_name = f"Forecast {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            # Create forecast run
            db.execute("""
                INSERT INTO ci_forecast_runs 
                (run_name, forecast_type, customer_scope, period_start, period_end, status, created_by)
                VALUES (?, ?, ?, DATE('now'), DATE('now', '+' || ? || ' months'), 'running', ?)
            """, (run_name, forecast_type, customer_scope, period_months, session.get('user_id')))
            run_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
            
            # Generate simple forecasts based on historical data
            customers = db.execute("SELECT id, name, total_orders, total_payments FROM sdad_customers").fetchall()
            total_forecasted = 0
            customer_count = 0
            
            for c in customers:
                if c['total_orders'] and c['total_orders'] > 0:
                    # Simple moving average forecast
                    monthly_avg = c['total_orders'] / 12 if c['total_orders'] else 0
                    for month_offset in range(1, period_months + 1):
                        forecast_date = (datetime.now() + timedelta(days=30*month_offset)).strftime('%Y-%m-%d')
                        
                        # Apply seasonality factor (simplified)
                        season_factor = 1.0 + 0.2 * (((month_offset % 12) + 3) % 12 / 6 - 1)
                        predicted = monthly_avg * season_factor
                        
                        db.execute("""
                            INSERT INTO ci_forecast_lines
                            (run_id, customer_id, forecast_date, period_type, predicted_demand,
                             confidence_level, prediction_interval_low, prediction_interval_high)
                            VALUES (?, ?, ?, 'monthly', ?, 0.70, ?, ?)
                        """, (run_id, c['id'], forecast_date, predicted, 
                              predicted * 0.8, predicted * 1.2))
                        total_forecasted += predicted
                        customer_count += 1
            
            # Update run as completed
            db.execute("""
                UPDATE ci_forecast_runs 
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP,
                    total_customers_forecasted = ?, total_demand_forecasted = ?
                WHERE id = ?
            """, (customer_count, total_forecasted, run_id))
            db.commit()
            
            flash(f"Forecast generated: {customer_count} customers, {total_forecasted:,.0f} total demand.", "success")
        except Exception as e:
            flash(f"Forecast error: {e}", "error")
        finally:
            db.close()
        return redirect(url_for('ci_forecast'))

    # ── Risk, Churn & Opportunity Alerts ─────────────────────────────────────

    @app.route('/customer-intelligence/alerts')
    @ci_permission_required('view_alerts')
    def ci_alerts():
        """Customer Intelligence - Risk, Churn & Opportunity Alerts."""
        db = get_db()
        try:
            alert_level = request.args.get('level', '')
            alert_type = request.args.get('type', '')
            resolved = request.args.get('resolved', '0')
            
            query = """
                SELECT a.*, c.name as customer_name, c.city, c.country, c.salesperson_name
                FROM ci_risk_alerts a
                LEFT JOIN sdad_customers c ON a.customer_id = c.id
                WHERE 1=1
            """
            params = []
            
            if resolved == '0':
                query += " AND a.is_resolved = 0"
            
            if alert_level:
                query += " AND a.alert_level = ?"
                params.append(alert_level)
            
            if alert_type:
                query += " AND a.alert_type = ?"
                params.append(alert_type)
            
            query += " ORDER BY a.created_at DESC LIMIT 100"
            
            alerts = db.execute(query, params).fetchall()
            
            # Alert summary counts
            alert_counts = {
                'total': db.execute("SELECT COUNT(*) as cnt FROM ci_risk_alerts WHERE is_resolved = 0").fetchone()['cnt'],
                'high': db.execute("SELECT COUNT(*) as cnt FROM ci_risk_alerts WHERE is_resolved = 0 AND alert_level = 'High'").fetchone()['cnt'],
                'medium': db.execute("SELECT COUNT(*) as cnt FROM ci_risk_alerts WHERE is_resolved = 0 AND alert_level = 'Medium'").fetchone()['cnt'],
                'low': db.execute("SELECT COUNT(*) as cnt FROM ci_risk_alerts WHERE is_resolved = 0 AND alert_level = 'Low'").fetchone()['cnt'],
                'churn': db.execute("SELECT COUNT(*) as cnt FROM ci_risk_alerts WHERE is_resolved = 0 AND alert_type = 'churn_risk'").fetchone()['cnt'],
                'credit': db.execute("SELECT COUNT(*) as cnt FROM ci_risk_alerts WHERE is_resolved = 0 AND alert_type = 'credit_risk'").fetchone()['cnt'],
                'growth': db.execute("SELECT COUNT(*) as cnt FROM ci_risk_alerts WHERE is_resolved = 0 AND alert_type = 'growth_opportunity'").fetchone()['cnt'],
            }
            
            return render_template(
                'customer_intelligence/alerts.html',
                title='Risk & Opportunity Alerts',
                alerts=[dict(r) for r in alerts],
                alert_counts=alert_counts,
                filters={'level': alert_level, 'type': alert_type, 'resolved': resolved}
            )
        finally:
            db.close()

    @app.route('/customer-intelligence/alerts/<int:alert_id>/resolve', methods=['POST'])
    @ci_permission_required('manage_alerts')
    def ci_alert_resolve(alert_id):
        """Mark an alert as resolved."""
        db = get_db()
        try:
            notes = request.form.get('resolution_notes', '')
            db.execute("""
                UPDATE ci_risk_alerts 
                SET is_resolved = 1, resolved_at = CURRENT_TIMESTAMP,
                    resolved_by = ?, resolution_notes = ?
                WHERE id = ?
            """, (session.get('user_id'), notes, alert_id))
            db.commit()
            flash("Alert resolved.", "success")
        finally:
            db.close()
        return redirect(url_for('ci_alerts'))

    @app.route('/customer-intelligence/alerts/generate', methods=['POST'])
    @ci_permission_required('manage_alerts')
    def ci_alerts_generate():
        """Auto-generate alerts for all customers."""
        db = get_db()
        try:
            customers = db.execute("SELECT id FROM sdad_customers").fetchall()
            total_alerts = 0
            for c in customers:
                alerts = generate_alerts_for_customer(c['id'])
                total_alerts += len(alerts)
            flash(f"Generated {total_alerts} alerts.", "success")
        finally:
            db.close()
        return redirect(url_for('ci_alerts'))

    # ── Recommendations ───────────────────────────────────────────────────────

    @app.route('/customer-intelligence/recommendations')
    @ci_permission_required('view_recommendations')
    def ci_recommendations():
        """Customer Intelligence - Recommendations & Action Center."""
        db = get_db()
        try:
            status = request.args.get('status', 'Open')
            rec_type = request.args.get('type', '')
            priority = request.args.get('priority', '')
            
            query = """
                SELECT r.*, c.name as customer_name, c.city, c.country, c.salesperson_name
                FROM ci_recommendations r
                LEFT JOIN sdad_customers c ON r.customer_id = c.id
                WHERE 1=1
            """
            params = []
            
            if status:
                query += " AND r.status = ?"
                params.append(status)
            
            if rec_type:
                query += " AND r.recommendation_type = ?"
                params.append(rec_type)
            
            if priority:
                query += " AND r.priority = ?"
                params.append(priority)
            
            query += " ORDER BY r.priority DESC, r.created_at DESC LIMIT 100"
            
            recommendations = db.execute(query, params).fetchall()
            
            # Summary
            summary = {
                'open': db.execute("SELECT COUNT(*) as cnt FROM ci_recommendations WHERE status = 'Open'").fetchone()['cnt'],
                'approved': db.execute("SELECT COUNT(*) as cnt FROM ci_recommendations WHERE status = 'Approved'").fetchone()['cnt'],
                'implemented': db.execute("SELECT COUNT(*) as cnt FROM ci_recommendations WHERE status = 'Implemented'").fetchone()['cnt'],
            }
            
            return render_template(
                'customer_intelligence/recommendations.html',
                title='Recommendations & Actions',
                recommendations=[dict(r) for r in recommendations],
                summary=summary,
                filters={'status': status, 'type': rec_type, 'priority': priority}
            )
        finally:
            db.close()

    @app.route('/customer-intelligence/recommendations/<int:rec_id>/approve', methods=['POST'])
    @ci_permission_required('approve_recommendations')
    def ci_rec_approve(rec_id):
        """Approve a recommendation."""
        db = get_db()
        try:
            db.execute("""
                UPDATE ci_recommendations 
                SET is_approved = 1, approved_by = ?, approved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (session.get('user_id'), rec_id))
            db.commit()
            flash("Recommendation approved.", "success")
        finally:
            db.close()
        return redirect(url_for('ci_recommendations'))

    @app.route('/customer-intelligence/recommendations/<int:rec_id>/implement', methods=['POST'])
    @ci_permission_required('manage_recommendations')
    def ci_rec_implement(rec_id):
        """Mark recommendation as implemented."""
        db = get_db()
        try:
            notes = request.form.get('implementation_notes', '')
            db.execute("""
                UPDATE ci_recommendations 
                SET is_implemented = 1, implemented_at = CURRENT_TIMESTAMP,
                    implementation_notes = ?, status = 'Implemented'
                WHERE id = ?
            """, (notes, rec_id))
            db.commit()
            flash("Recommendation marked as implemented.", "success")
        finally:
            db.close()
        return redirect(url_for('ci_recommendations'))

    # ── Reports ────────────────────────────────────────────────────────────────

    @app.route('/customer-intelligence/reports')
    @ci_permission_required('view_reports')
    def ci_reports():
        """Customer Intelligence - Reports & Analytics."""
        return render_template(
            'customer_intelligence/reports.html',
            title='Customer Intelligence Reports'
        )

    @app.route('/customer-intelligence/reports/export/<string:report_type>')
    @ci_permission_required('export_reports')
    def ci_report_export(report_type):
        """Export a customer intelligence report."""
        fmt = request.args.get('format', 'xlsx').lower()
        db = get_db()
        try:
            if report_type == 'customers':
                headers = ['Name', 'Phone', 'City', 'Country', 'Location', 'Salesperson',
                          'Total Orders', 'Total Payments', 'Total Debt', 'Credit Limit',
                          'Credit Status', 'Active', 'Last Purchase']
                data = db.execute("SELECT name, phone, city, country, location, salesperson_name, total_orders, total_payments, total_debt, credit_limit, credit_status, active, last_purchase_date FROM sdad_customers ORDER BY total_orders DESC").fetchall()
            elif report_type == 'segments':
                headers = ['Segment Name', 'Code', 'Type', 'Description', 'Dynamic', 'System', 'Member Count']
                data = db.execute("""
                    SELECT s.segment_name, s.segment_code, s.segment_type, s.description,
                           s.is_dynamic, s.is_system,
                           (SELECT COUNT(*) FROM ci_segment_members WHERE segment_id = s.id) as member_count
                    FROM ci_customer_segments s ORDER BY s.segment_name
                """).fetchall()
            elif report_type == 'alerts':
                headers = ['Customer', 'Alert Type', 'Category', 'Level', 'Title', 'Description', 'Status', 'Created']
                data = db.execute("""
                    SELECT c.name, a.alert_type, a.alert_category, a.alert_level, a.title,
                           a.description,
                           CASE WHEN a.is_resolved = 0 THEN 'Open' ELSE 'Resolved' END as status,
                           a.created_at
                    FROM ci_risk_alerts a
                    LEFT JOIN sdad_customers c ON a.customer_id = c.id
                    ORDER BY a.created_at DESC
                """).fetchall()
            elif report_type == 'recommendations':
                headers = ['Customer', 'Type', 'Title', 'Priority', 'Status', 'Target Date', 'Created']
                data = db.execute("""
                    SELECT c.name, r.recommendation_type, r.title, r.priority, r.status,
                           r.target_date, r.created_at
                    FROM ci_recommendations r
                    LEFT JOIN sdad_customers c ON r.customer_id = c.id
                    ORDER BY r.created_at DESC
                """).fetchall()
            elif report_type == 'lost_sales':
                headers = ['Customer', 'Date', 'Reason', 'Category', 'Amount', 'Profit Lost', 'Competitor']
                data = db.execute("""
                    SELECT c.name, l.lost_date, l.reason, l.reason_category, l.lost_amount,
                           l.lost_profit, l.competitor_name
                    FROM ci_lost_sales l
                    LEFT JOIN sdad_customers c ON l.customer_id = c.id
                    ORDER BY l.lost_date DESC
                """).fetchall()
            elif report_type == 'financial_summary':
                headers = ['Customer', 'City', 'Country', 'Total Revenue', 'Total Payments',
                          'Outstanding Debt', 'Credit Limit', 'Credit Status', 'Payment Method', 'Active']
                data = db.execute("""
                    SELECT c.name, c.city, c.country, c.total_orders, c.total_payments,
                           c.total_debt, c.credit_limit, c.credit_status, c.payment_method, c.active
                    FROM sdad_customers c ORDER BY c.total_orders DESC
                """).fetchall()
            elif report_type == 'churn_analysis':
                headers = ['Customer', 'City', 'Country', 'Total Orders', 'Total Payments',
                          'Last Purchase Date', 'Days Inactive', 'Churn Risk Score', 'Active']
                data = db.execute("""
                    SELECT c.name, c.city, c.country, c.total_orders, c.total_payments,
                           c.last_purchase_date,
                           CAST(julianday('now') - julianday(COALESCE(c.last_purchase_date, c.created_at)) AS INTEGER) as days_inactive,
                           CASE
                               WHEN julianday('now') - julianday(COALESCE(c.last_purchase_date, c.created_at)) > 180 THEN 'High'
                               WHEN julianday('now') - julianday(COALESCE(c.last_purchase_date, c.created_at)) > 90 THEN 'Medium'
                               ELSE 'Low'
                           END as churn_risk,
                           c.active
                    FROM sdad_customers c ORDER BY days_inactive DESC
                """).fetchall()
            else:
                data = []
                headers = []

            if fmt == 'csv':
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(headers)
                for row in data:
                    writer.writerow([v for v in row])
                output.seek(0)
                return Response(
                    output.getvalue(),
                    mimetype='text/csv',
                    headers={'Content-Disposition': f'attachment; filename=CI_{report_type}_{datetime.now().strftime("%Y%m%d")}.csv'}
                )

            wb = Workbook()
            ws = wb.active
            ws.title = report_type.replace('_', ' ').title()
            header_fill = PatternFill("solid", fgColor="0D3B66")
            header_font = Font(bold=True, color="FFFFFF", size=11)
            header_alignment = Alignment(horizontal="center", vertical="center")

            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.fill = header_fill
                cell.font = header_font
                cell.alignment = header_alignment

            for row_idx, row in enumerate(data, 2):
                for col_idx, value in enumerate(row, 1):
                    ws.cell(row=row_idx, column=col_idx, value=value)

            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column].width = adjusted_width

            output = io.BytesIO()
            wb.save(output)
            output.seek(0)

            return Response(
                output.getvalue(),
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                headers={'Content-Disposition': f'attachment; filename=CI_{report_type}_{datetime.now().strftime("%Y%m%d")}.xlsx'}
            )
        finally:
            db.close()

    # ── Settings ──────────────────────────────────────────────────────────────

    @app.route('/customer-intelligence/settings', methods=['GET', 'POST'])
    @ci_permission_required('manage_settings')
    def ci_settings():
        """Customer Intelligence - Settings."""
        db = get_db()
        try:
            if request.method == 'POST':
                settings_data = {
                    'churn_risk_threshold_high': request.form.get('churn_risk_threshold_high', 0.75, type=float),
                    'churn_risk_threshold_medium': request.form.get('churn_risk_threshold_medium', 0.50, type=float),
                    'growth_threshold_high': request.form.get('growth_threshold_high', 0.30, type=float),
                    'growth_threshold_low': request.form.get('growth_threshold_low', -0.20, type=float),
                    'inactive_days_threshold': request.form.get('inactive_days_threshold', 90, type=int),
                    'payment_delay_threshold_days': request.form.get('payment_delay_threshold_days', 30, type=int),
                    'credit_utilization_threshold': request.form.get('credit_utilization_threshold', 0.90, type=float),
                    'min_order_frequency_wholesale': request.form.get('min_order_frequency_wholesale', 2, type=int),
                    'min_order_volume_wholesale': request.form.get('min_order_volume_wholesale', 1000, type=float),
                    'forecast_confidence_threshold': request.form.get('forecast_confidence_threshold', 0.70, type=float),
                    'seasonality_spike_threshold': request.form.get('seasonality_spike_threshold', 1.5, type=float),
                    'service_burden_threshold_high': request.form.get('service_burden_threshold_high', 0.80, type=float),
                    'operational_pressure_threshold': request.form.get('operational_pressure_threshold', 0.70, type=float),
                    'profit_margin_threshold_low': request.form.get('profit_margin_threshold_low', 0.10, type=float),
                    'lost_sales_alert_threshold': request.form.get('lost_sales_alert_threshold', 0.15, type=float),
                    'customer_lifetime_months': request.form.get('customer_lifetime_months', 36, type=int),
                    'key_customer_revenue_threshold': request.form.get('key_customer_revenue_threshold', 50000, type=float),
                    'high_value_customer_threshold': request.form.get('high_value_customer_threshold', 100000, type=float),
                    'forecast_horizon_months': request.form.get('forecast_horizon_months', 6, type=int),
                    'min_data_points_for_forecast': request.form.get('min_data_points_for_forecast', 3, type=int),
                    'auto_alert_generation': 1 if request.form.get('auto_alert_generation') else 0,
                    'auto_forecast_generation': 1 if request.form.get('auto_forecast_generation') else 0,
                    'seasonality_detection_enabled': 1 if request.form.get('seasonality_detection_enabled') else 0,
                }
                update_ci_settings(settings_data)
                flash("Settings updated successfully.", "success")
                return redirect(url_for('ci_settings'))
            
            settings = get_ci_settings()
            return render_template(
                'customer_intelligence/settings.html',
                title='Customer Intelligence Settings',
                settings=settings
            )
        finally:
            db.close()

    @app.route('/customer-intelligence/sync-all', methods=['POST'])
    @ci_permission_required('manage_settings')
    def ci_sync_all():
        """Sync all customers to CI profiles."""
        try:
            count = auto_sync_all_customers()
            flash(f"Synced {count} customers to Customer Intelligence.", "success")
        except Exception as e:
            flash(f"Sync error: {e}", "error")
        return redirect(url_for('ci_dashboard'))

    # ── API Endpoints ─────────────────────────────────────────────────────────

    @app.route('/api/customer-intelligence/dashboard-stats')
    @ci_permission_required('view_dashboard')
    def ci_api_dashboard_stats():
        """API endpoint for dashboard statistics."""
        db = get_db()
        try:
            stats = {
                'total_customers': db.execute("SELECT COUNT(*) as cnt FROM sdad_customers").fetchone()['cnt'],
                'active_customers': db.execute("SELECT COUNT(*) as cnt FROM sdad_customers WHERE active = 1").fetchone()['cnt'],
                'total_revenue': db.execute("SELECT COALESCE(SUM(total_orders), 0) as t FROM sdad_customers").fetchone()['t'],
                'total_debt': db.execute("SELECT COALESCE(SUM(total_debt), 0) as t FROM sdad_customers").fetchone()['t'],
                'open_alerts': db.execute("SELECT COUNT(*) as cnt FROM ci_risk_alerts WHERE is_resolved = 0").fetchone()['cnt'],
                'open_recommendations': db.execute("SELECT COUNT(*) as cnt FROM ci_recommendations WHERE status = 'Open'").fetchone()['cnt'],
            }
            return jsonify(stats)
        finally:
            db.close()

    @app.route('/api/customer-intelligence/metrics/<int:customer_id>')
    @ci_permission_required('view_profiles')
    def ci_api_metrics(customer_id):
        """API endpoint for single customer metrics."""
        metrics = compute_customer_metrics(customer_id)
        if not metrics:
            return jsonify({'error': 'Customer not found'}), 404
        return jsonify(metrics)

    print("Customer Intelligence routes registered.")
