"""
Marketing Module Routes and API Endpoints
=========================================
This file contains all marketing-related Flask routes and API endpoints.

Routes are organized by Marketing module:
1. Marketing Dashboard
2. Brands
3. Market & Competitor Intelligence
4. Customer Segments
5. Marketing Channels
6. Campaigns
7. Advertising
8. Content & Content Calendar
9. Leads
10. Funnel & Conversion Tracking
11. Offers & Promotions
12. Budgets & Costs
13. Performance Analytics
14. Seasonality & Timing
15. Recommendations & Alerts
16. Reports & Analytics
17. Settings

Each route has proper:
- Authentication checks
- Permission checks
- Input validation
- Error handling
- Audit logging
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file, Response
from functools import wraps
from datetime import datetime, timedelta, date
import sqlite3
import json
import csv
import io
from marketing_models import (
    get_db, run_marketing_migrations, get_marketing_setting, update_marketing_setting,
    log_marketing_audit, get_marketing_dashboard_data, get_campaign_summary_stats,
    get_lead_stats, get_channel_performance, MARKETING_TABLES,
    get_user_marketing_permissions, get_marketing_role_users,
    MARKETING_DEFAULT_PERMISSIONS, MARKETING_DEFAULT_ROLES,
    generate_marketing_alerts, generate_marketing_recommendations, run_marketing_insights
)

mkt_bp = Blueprint('marketing', __name__, url_prefix='/marketing')


# =============================================================================
# DECORATORS AND HELPERS
# =============================================================================

def mkt_login_required(f):
    """Decorator to require marketing login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please log in first.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def mkt_permission_required(permission: str):
    """Decorator to check marketing-specific permissions."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'error')
                return redirect(url_for('login'))
            
            # Super admin bypass
            if session.get('role_name') == 'Global Admin':
                return f(*args, **kwargs)
            
            # Check specific marketing permissions from session or role
            mkt_permissions = session.get('marketing_permissions', [])
            if 'all_marketing' in mkt_permissions or permission in mkt_permissions:
                return f(*args, **kwargs)
            
            flash('You do not have permission to access this Marketing module.', 'error')
            return redirect(url_for('index'))
        return decorated_function
    return decorator


def get_current_user():
    """Get current logged-in user info."""
    if 'user_id' not in session:
        return None
    return {
        'id': session.get('user_id'),
        'username': session.get('username'),
        'role_id': session.get('role_id'),
        'role_name': session.get('role_name'),
    }


def get_user_companies():
    """Get companies accessible to current user."""
    if session.get('role_name') == 'Global Admin':
        return None  # All companies
    return session.get('company_id')


def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed."""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


# =============================================================================
# MARKETING DASHBOARD
# =============================================================================

@mkt_bp.route('/')
@mkt_bp.route('/dashboard')
@mkt_login_required
@mkt_permission_required('dashboard')
def marketing_dashboard():
    """Main marketing dashboard with KPIs and summaries."""
    db = get_db()
    
    # Get date filters
    date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
    
    # Get dashboard data
    dash_data = get_marketing_dashboard_data(db, date_from=date_from, date_to=date_to)
    
    # Get recent campaigns
    recent_campaigns = db.execute("""
        SELECT id, name, campaign_type, status, start_date, end_date, 
               budget, actual_cost, leads_generated, sales_generated
        FROM marketing_campaigns
        ORDER BY created_at DESC
        LIMIT 10
    """).fetchall()
    
    # Get recent leads
    recent_leads = db.execute("""
        SELECT l.id, l.lead_name, l.phone, l.source_id, l.lead_status, 
               l.conversion_probability, l.created_at,
               ls.name as source_name
        FROM marketing_leads l
        LEFT JOIN marketing_lead_sources ls ON l.source_id = ls.id
        ORDER BY l.created_at DESC
        LIMIT 10
    """).fetchall()
    
    # Get open alerts count
    open_alerts = db.execute("""
        SELECT COUNT(*) as cnt FROM marketing_alerts WHERE is_resolved = 0
    """).fetchone()['cnt']
    
    # Get recommendations count
    open_recommendations = db.execute("""
        SELECT COUNT(*) as cnt FROM marketing_recommendations WHERE status = 'Open'
    """).fetchone()['cnt']
    
    db.close()
    
    return render_template('marketing/dashboard.html',
        title='Marketing Dashboard',
        dash_data=dash_data,
        recent_campaigns=[dict(r) for r in recent_campaigns],
        recent_leads=[dict(r) for r in recent_leads],
        open_alerts=open_alerts,
        open_recommendations=open_recommendations,
        date_from=date_from,
        date_to=date_to,
    )


# =============================================================================
# BRANDS
# =============================================================================

@mkt_bp.route('/brands')
@mkt_login_required
@mkt_permission_required('view_brands')
def brands_list():
    """List all brand profiles."""
    db = get_db()
    
    # Pagination
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    # Filters
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    # Build query
    query = "SELECT * FROM marketing_brands WHERE 1=1"
    count_query = "SELECT COUNT(*) as cnt FROM marketing_brands WHERE 1=1"
    params = []
    count_params = []
    
    if search:
        query += " AND (name LIKE ? OR trade_name LIKE ? OR code LIKE ?)"
        count_query += " AND (name LIKE ? OR trade_name LIKE ? OR code LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
        count_params.extend([search_term, search_term, search_term])
    
    if status:
        query += " AND status = ?"
        count_query += " AND status = ?"
        params.append(status)
        count_params.append(status)
    
    # Get total count
    total = db.execute(count_query, count_params).fetchone()['cnt']
    
    # Get paginated results
    query += " ORDER BY name LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    brands = db.execute(query, params).fetchall()
    
    db.close()
    
    return render_template('marketing/brands.html',
        title='Brand Profiles',
        brands=[dict(r) for r in brands],
        page=page,
        per_page=per_page,
        total=total,
        search=search,
        status=status,
    )


@mkt_bp.route('/brands/new', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_brands')
def brands_new():
    """Create a new brand profile."""
    db = get_db()
    user = get_current_user()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        trade_name = request.form.get('trade_name', '').strip()
        code = request.form.get('code', '').strip()
        
        if not name:
            flash('Brand name is required.', 'error')
            return render_template('marketing/brand_edit.html', title='New Brand', brand=None, edit_mode=True)
        
        if not code:
            # Generate code from name
            code = ''.join([w[0] for w in name.split()]).upper()[:6]
        
        # Check for duplicate code
        existing = db.execute("SELECT id FROM marketing_brands WHERE code = ?", (code,)).fetchone()
        if existing:
            flash(f'Brand code "{code}" already exists. Please use a unique code.', 'error')
            return render_template('marketing/brand_edit.html', title='New Brand', brand=None, edit_mode=True)
        
        # Extract form fields
        identity = request.form.get('identity', '')
        positioning = request.form.get('positioning', '')
        tone_of_voice = request.form.get('tone_of_voice', '')
        brand_values = request.form.get('brand_values', '')
        competitive_advantage = request.form.get('competitive_advantage', '')
        core_message = request.form.get('core_message', '')
        slogan = request.form.get('slogan', '')
        color_system = request.form.get('color_system', '')
        allowed_messaging = request.form.get('allowed_messaging', '')
        target_market = request.form.get('target_market', '')
        target_segments = request.form.get('target_segments', '')
        status = request.form.get('status', 'Active')
        notes = request.form.get('notes', '')
        
        # Insert
        cursor = db.execute("""
            INSERT INTO marketing_brands 
            (name, trade_name, code, identity, positioning, tone_of_voice, brand_values,
             competitive_advantage, core_message, slogan, color_system, allowed_messaging,
             target_market, target_segments, status, notes, created_by_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, trade_name, code, identity, positioning, tone_of_voice, brand_values,
              competitive_advantage, core_message, slogan, color_system, allowed_messaging,
              target_market, target_segments, status, notes, user['id']))
        db.commit()
        brand_id = cursor.lastrowid
        
        # Log audit
        log_marketing_audit(db, 'brand', brand_id, 'CREATE', 
                           new_value=json.dumps({'name': name, 'code': code}),
                           actor_user_id=user['id'])
        
        flash(f'Brand "{name}" created successfully.', 'success')
        return redirect(url_for('marketing.brands_view', id=brand_id))
    
    db.close()
    return render_template('marketing/brand_edit.html', title='New Brand', brand=None, edit_mode=True)


@mkt_bp.route('/brands/view/<int:id>')
@mkt_login_required
@mkt_permission_required('view_brands')
def brands_view(id):
    """View brand profile details."""
    db = get_db()
    brand = db.execute("SELECT * FROM marketing_brands WHERE id = ?", (id,)).fetchone()
    
    if not brand:
        flash('Brand not found.', 'error')
        return redirect(url_for('marketing.brands_list'))
    
    # Get linked campaigns
    campaigns = db.execute("""
        SELECT id, name, campaign_type, status, start_date, end_date
        FROM marketing_campaigns
        WHERE target_brand_id = ?
        ORDER BY start_date DESC
        LIMIT 10
    """, (id,)).fetchall()
    
    # Get content linked to this brand
    content = db.execute("""
        SELECT id, topic, title, content_format, status, publish_date
        FROM marketing_content
        WHERE linked_brand_id = ?
        ORDER BY publish_date DESC
        LIMIT 10
    """, (id,)).fetchall()
    
    # Get brand performance metrics
    metrics = db.execute("""
        SELECT metric_date, metric_name, metric_value, metric_unit
        FROM marketing_performance_metrics
        WHERE entity_type = 'brand' AND entity_id = ?
        ORDER BY metric_date DESC
        LIMIT 20
    """, (id,)).fetchall()
    
    db.close()
    
    return render_template('marketing/brand_view.html',
        title=f'Brand: {brand["name"]}',
        brand=dict(brand),
        campaigns=[dict(r) for r in campaigns],
        content=[dict(r) for r in content],
        metrics=[dict(r) for r in metrics],
    )


@mkt_bp.route('/brands/edit/<int:id>', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_brands')
def brands_edit(id):
    """Edit a brand profile."""
    db = get_db()
    user = get_current_user()
    
    brand = db.execute("SELECT * FROM marketing_brands WHERE id = ?", (id,)).fetchone()
    if not brand:
        flash('Brand not found.', 'error')
        return redirect(url_for('marketing.brands_list'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        trade_name = request.form.get('trade_name', '').strip()
        code = request.form.get('code', '').strip()
        
        if not name:
            flash('Brand name is required.', 'error')
            return render_template('marketing/brand_edit.html', title=f'Edit: {brand["name"]}', brand=dict(brand), edit_mode=True)
        
        # Check for duplicate code (excluding current brand)
        existing = db.execute("SELECT id FROM marketing_brands WHERE code = ? AND id != ?", (code, id)).fetchone()
        if existing:
            flash(f'Brand code "{code}" already exists. Please use a unique code.', 'error')
            return render_template('marketing/brand_edit.html', title=f'Edit: {brand["name"]}', brand=dict(brand), edit_mode=True)
        
        # Build update query
        db.execute("""
            UPDATE marketing_brands SET
                name = ?, trade_name = ?, code = ?,
                identity = ?, positioning = ?, tone_of_voice = ?, brand_values = ?,
                competitive_advantage = ?, core_message = ?, slogan = ?,
                color_system = ?, allowed_messaging = ?, target_market = ?,
                target_segments = ?, status = ?, notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            name, trade_name, code,
            request.form.get('identity', ''),
            request.form.get('positioning', ''),
            request.form.get('tone_of_voice', ''),
            request.form.get('brand_values', ''),
            request.form.get('competitive_advantage', ''),
            request.form.get('core_message', ''),
            request.form.get('slogan', ''),
            request.form.get('color_system', ''),
            request.form.get('allowed_messaging', ''),
            request.form.get('target_market', ''),
            request.form.get('target_segments', ''),
            request.form.get('status', 'Active'),
            request.form.get('notes', ''),
            id
        ))
        db.commit()
        
        # Log audit
        log_marketing_audit(db, 'brand', id, 'UPDATE',
                           new_value=json.dumps({'name': name, 'code': code}),
                           actor_user_id=user['id'])
        
        flash(f'Brand "{name}" updated successfully.', 'success')
        return redirect(url_for('marketing.brands_view', id=id))
    
    db.close()
    return render_template('marketing/brand_edit.html', title=f'Edit: {brand["name"]}', brand=dict(brand), edit_mode=True)


@mkt_bp.route('/brands/delete/<int:id>', methods=['POST'])
@mkt_login_required
@mkt_permission_required('manage_brands')
def brands_delete(id):
    """Delete a brand (soft delete by setting status)."""
    db = get_db()
    user = get_current_user()
    
    brand = db.execute("SELECT * FROM marketing_brands WHERE id = ?", (id,)).fetchone()
    if not brand:
        return jsonify({'success': False, 'message': 'Brand not found'}), 404
    
    db.execute("UPDATE marketing_brands SET status = 'Deleted', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (id,))
    db.commit()
    
    log_marketing_audit(db, 'brand', id, 'DELETE',
                       old_value=json.dumps({'name': brand['name']}),
                       actor_user_id=user['id'])
    
    flash(f'Brand "{brand["name"]}" deleted successfully.', 'success')
    return redirect(url_for('marketing.brands_list'))


# =============================================================================
# MARKET & COMPETITOR INTELLIGENCE
# =============================================================================

@mkt_bp.route('/market-intelligence')
@mkt_login_required
@mkt_permission_required('view_market_intel')
def market_intelligence_list():
    """List market intelligence entries."""
    db = get_db()
    
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    search = request.args.get('search', '')
    market_type = request.args.get('market_type', '')
    
    query = "SELECT * FROM marketing_market_intelligence WHERE 1=1"
    count_query = "SELECT COUNT(*) as cnt FROM marketing_market_intelligence WHERE 1=1"
    params = []
    count_params = []
    
    if search:
        query += " AND (market_name LIKE ? OR competitor_name LIKE ? OR country LIKE ?)"
        count_query += " AND (market_name LIKE ? OR competitor_name LIKE ? OR country LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
        count_params.extend([search_term, search_term, search_term])
    
    if market_type:
        query += " AND market_type = ?"
        count_query += " AND market_type = ?"
        params.append(market_type)
        count_params.append(market_type)
    
    total = db.execute(count_query, count_params).fetchone()['cnt']
    query += " ORDER BY market_name LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    entries = db.execute(query, params).fetchall()
    db.close()
    
    return render_template('marketing/market_intelligence.html',
        title='Market & Competitor Intelligence',
        entries=[dict(r) for r in entries],
        page=page, per_page=per_page, total=total,
        search=search, market_type=market_type,
    )


@mkt_bp.route('/market-intelligence/new', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_market_intel')
def market_intelligence_new():
    """Create new market intelligence entry."""
    db = get_db()
    user = get_current_user()
    
    if request.method == 'POST':
        market_name = request.form.get('market_name', '').strip()
        if not market_name:
            flash('Market name is required.', 'error')
            return render_template('marketing/market_intelligence_edit.html', title='New Market Entry', entry=None)
        
        cursor = db.execute("""
            INSERT INTO marketing_market_intelligence
            (market_name, market_type, region, country, city,
             is_local, is_export, is_retail, is_wholesale, is_b2b, is_b2c,
             competitor_name, competitor_scope, competitor_brands, competitor_pricing,
             competitor_ad_style, competitor_channels, competitor_strengths, competitor_weaknesses,
             estimated_market_share, market_gaps, market_threats, recommended_strategy,
             status, notes, created_by_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            market_name,
            request.form.get('market_type', ''),
            request.form.get('region', ''),
            request.form.get('country', ''),
            request.form.get('city', ''),
            1 if request.form.get('is_local') else 0,
            1 if request.form.get('is_export') else 0,
            1 if request.form.get('is_retail') else 0,
            1 if request.form.get('is_wholesale') else 0,
            1 if request.form.get('is_b2b') else 0,
            1 if request.form.get('is_b2c') else 0,
            request.form.get('competitor_name', ''),
            request.form.get('competitor_scope', ''),
            request.form.get('competitor_brands', ''),
            request.form.get('competitor_pricing', ''),
            request.form.get('competitor_ad_style', ''),
            request.form.get('competitor_channels', ''),
            request.form.get('competitor_strengths', ''),
            request.form.get('competitor_weaknesses', ''),
            request.form.get('estimated_market_share', ''),
            request.form.get('market_gaps', ''),
            request.form.get('market_threats', ''),
            request.form.get('recommended_strategy', ''),
            request.form.get('status', 'Active'),
            request.form.get('notes', ''),
            user['id']
        ))
        db.commit()
        entry_id = cursor.lastrowid
        
        log_marketing_audit(db, 'market_intel', entry_id, 'CREATE',
                           new_value=json.dumps({'market_name': market_name}),
                           actor_user_id=user['id'])
        
        flash(f'Market entry "{market_name}" created successfully.', 'success')
        return redirect(url_for('marketing.market_intelligence_view', id=entry_id))
    
    db.close()
    return render_template('marketing/market_intelligence_edit.html', title='New Market Entry', entry=None)


@mkt_bp.route('/market-intelligence/view/<int:id>')
@mkt_login_required
@mkt_permission_required('view_market_intel')
def market_intelligence_view(id):
    """View market intelligence entry."""
    db = get_db()
    entry = db.execute("SELECT * FROM marketing_market_intelligence WHERE id = ?", (id,)).fetchone()
    
    if not entry:
        flash('Market entry not found.', 'error')
        return redirect(url_for('marketing.market_intelligence_list'))
    
    db.close()
    return render_template('marketing/market_intelligence_view.html',
        title=f'Market: {entry["market_name"]}',
        entry=dict(entry))


@mkt_bp.route('/market-intelligence/edit/<int:id>', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_market_intel')
def market_intelligence_edit(id):
    """Edit market intelligence entry."""
    db = get_db()
    user = get_current_user()
    
    entry = db.execute("SELECT * FROM marketing_market_intelligence WHERE id = ?", (id,)).fetchone()
    if not entry:
        flash('Market entry not found.', 'error')
        return redirect(url_for('marketing.market_intelligence_list'))
    
    if request.method == 'POST':
        db.execute("""
            UPDATE marketing_market_intelligence SET
                market_name = ?, market_type = ?, region = ?, country = ?, city = ?,
                is_local = ?, is_export = ?, is_retail = ?, is_wholesale = ?, is_b2b = ?, is_b2c = ?,
                competitor_name = ?, competitor_scope = ?, competitor_brands = ?, competitor_pricing = ?,
                competitor_ad_style = ?, competitor_channels = ?, competitor_strengths = ?, competitor_weaknesses = ?,
                estimated_market_share = ?, market_gaps = ?, market_threats = ?, recommended_strategy = ?,
                status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            request.form.get('market_name', ''),
            request.form.get('market_type', ''),
            request.form.get('region', ''),
            request.form.get('country', ''),
            request.form.get('city', ''),
            1 if request.form.get('is_local') else 0,
            1 if request.form.get('is_export') else 0,
            1 if request.form.get('is_retail') else 0,
            1 if request.form.get('is_wholesale') else 0,
            1 if request.form.get('is_b2b') else 0,
            1 if request.form.get('is_b2c') else 0,
            request.form.get('competitor_name', ''),
            request.form.get('competitor_scope', ''),
            request.form.get('competitor_brands', ''),
            request.form.get('competitor_pricing', ''),
            request.form.get('competitor_ad_style', ''),
            request.form.get('competitor_channels', ''),
            request.form.get('competitor_strengths', ''),
            request.form.get('competitor_weaknesses', ''),
            request.form.get('estimated_market_share', ''),
            request.form.get('market_gaps', ''),
            request.form.get('market_threats', ''),
            request.form.get('recommended_strategy', ''),
            request.form.get('status', 'Active'),
            request.form.get('notes', ''),
            id
        ))
        db.commit()
        
        log_marketing_audit(db, 'market_intel', id, 'UPDATE',
                           actor_user_id=user['id'])
        
        flash('Market entry updated successfully.', 'success')
        return redirect(url_for('marketing.market_intelligence_view', id=id))
    
    db.close()
    return render_template('marketing/market_intelligence_edit.html',
        title=f'Edit: {entry["market_name"]}',
        entry=dict(entry))


# =============================================================================
# CUSTOMER SEGMENTS
# =============================================================================

@mkt_bp.route('/segments')
@mkt_login_required
@mkt_permission_required('view_segments')
def segments_list():
    """List customer segments."""
    db = get_db()
    
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    search = request.args.get('search', '')
    segment_type = request.args.get('segment_type', '')
    
    query = "SELECT * FROM marketing_customer_segments WHERE 1=1"
    count_query = "SELECT COUNT(*) as cnt FROM marketing_customer_segments WHERE 1=1"
    params = []
    count_params = []
    
    if search:
        query += " AND (name LIKE ? OR code LIKE ? OR description LIKE ?)"
        count_query += " AND (name LIKE ? OR code LIKE ? OR description LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
        count_params.extend([search_term, search_term, search_term])
    
    if segment_type:
        query += " AND segment_type = ?"
        count_query += " AND segment_type = ?"
        params.append(segment_type)
        count_params.append(segment_type)
    
    total = db.execute(count_query, count_params).fetchone()['cnt']
    query += " ORDER BY name LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    segments = db.execute(query, params).fetchall()
    db.close()
    
    return render_template('marketing/segments.html',
        title='Customer Segments',
        segments=[dict(r) for r in segments],
        page=page, per_page=per_page, total=total,
        search=search, segment_type=segment_type,
    )


@mkt_bp.route('/segments/new', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_segments')
def segments_new():
    """Create new customer segment."""
    db = get_db()
    user = get_current_user()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip()
        
        if not name:
            flash('Segment name is required.', 'error')
            return render_template('marketing/segment_edit.html', title='New Segment', segment=None)
        
        if not code:
            code = ''.join([w[0] for w in name.split()]).upper()[:8]
        
        cursor = db.execute("""
            INSERT INTO marketing_customer_segments
            (name, code, description, segment_type, customer_type,
             is_retail, is_wholesale, is_local, is_export, country, city,
             industry, trade_type, purchase_volume_min, purchase_volume_max,
             purchase_frequency, loyalty_level, buying_power,
             price_sensitivity, brand_sensitivity, speed_sensitivity,
             persona_description, preferred_products, preferred_brands,
             is_dynamic, segment_rules, status, notes, created_by_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, code, request.form.get('description', ''),
            request.form.get('segment_type', ''),
            request.form.get('customer_type', ''),
            1 if request.form.get('is_retail') else 0,
            1 if request.form.get('is_wholesale') else 0,
            1 if request.form.get('is_local') else 0,
            1 if request.form.get('is_export') else 0,
            request.form.get('country', ''),
            request.form.get('city', ''),
            request.form.get('industry', ''),
            request.form.get('trade_type', ''),
            request.form.get('purchase_volume_min', 0),
            request.form.get('purchase_volume_max', 0),
            request.form.get('purchase_frequency', ''),
            request.form.get('loyalty_level', ''),
            request.form.get('buying_power', ''),
            request.form.get('price_sensitivity', ''),
            request.form.get('brand_sensitivity', ''),
            request.form.get('speed_sensitivity', ''),
            request.form.get('persona_description', ''),
            request.form.get('preferred_products', ''),
            request.form.get('preferred_brands', ''),
            1 if request.form.get('is_dynamic') else 0,
            request.form.get('segment_rules', ''),
            request.form.get('status', 'Active'),
            request.form.get('notes', ''),
            user['id']
        ))
        db.commit()
        seg_id = cursor.lastrowid
        
        log_marketing_audit(db, 'segment', seg_id, 'CREATE',
                           new_value=json.dumps({'name': name, 'code': code}),
                           actor_user_id=user['id'])
        
        flash(f'Segment "{name}" created successfully.', 'success')
        return redirect(url_for('marketing.segments_view', id=seg_id))
    
    db.close()
    return render_template('marketing/segment_edit.html', title='New Segment', segment=None)


@mkt_bp.route('/segments/view/<int:id>')
@mkt_login_required
@mkt_permission_required('view_segments')
def segments_view(id):
    """View segment details."""
    db = get_db()
    segment = db.execute("SELECT * FROM marketing_customer_segments WHERE id = ?", (id,)).fetchone()
    
    if not segment:
        flash('Segment not found.', 'error')
        return redirect(url_for('marketing.segments_list'))
    
    # Get campaigns targeting this segment
    campaigns = db.execute("""
        SELECT id, name, campaign_type, status, start_date
        FROM marketing_campaigns
        WHERE target_segment_id = ?
        ORDER BY start_date DESC
        LIMIT 10
    """, (id,)).fetchall()
    
    db.close()
    
    return render_template('marketing/segment_view.html',
        title=f'Segment: {segment["name"]}',
        segment=dict(segment),
        campaigns=[dict(r) for r in campaigns],
    )


@mkt_bp.route('/segments/edit/<int:id>', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_segments')
def segments_edit(id):
    """Edit customer segment."""
    db = get_db()
    user = get_current_user()
    
    segment = db.execute("SELECT * FROM marketing_customer_segments WHERE id = ?", (id,)).fetchone()
    if not segment:
        flash('Segment not found.', 'error')
        return redirect(url_for('marketing.segments_list'))
    
    if request.method == 'POST':
        db.execute("""
            UPDATE marketing_customer_segments SET
                name = ?, code = ?, description = ?, segment_type = ?, customer_type = ?,
                is_retail = ?, is_wholesale = ?, is_local = ?, is_export = ?,
                country = ?, city = ?, industry = ?, trade_type = ?,
                purchase_volume_min = ?, purchase_volume_max = ?,
                purchase_frequency = ?, loyalty_level = ?, buying_power = ?,
                price_sensitivity = ?, brand_sensitivity = ?, speed_sensitivity = ?,
                persona_description = ?, preferred_products = ?, preferred_brands = ?,
                is_dynamic = ?, segment_rules = ?, status = ?, notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            request.form.get('name', ''),
            request.form.get('code', ''),
            request.form.get('description', ''),
            request.form.get('segment_type', ''),
            request.form.get('customer_type', ''),
            1 if request.form.get('is_retail') else 0,
            1 if request.form.get('is_wholesale') else 0,
            1 if request.form.get('is_local') else 0,
            1 if request.form.get('is_export') else 0,
            request.form.get('country', ''),
            request.form.get('city', ''),
            request.form.get('industry', ''),
            request.form.get('trade_type', ''),
            request.form.get('purchase_volume_min', 0),
            request.form.get('purchase_volume_max', 0),
            request.form.get('purchase_frequency', ''),
            request.form.get('loyalty_level', ''),
            request.form.get('buying_power', ''),
            request.form.get('price_sensitivity', ''),
            request.form.get('brand_sensitivity', ''),
            request.form.get('speed_sensitivity', ''),
            request.form.get('persona_description', ''),
            request.form.get('preferred_products', ''),
            request.form.get('preferred_brands', ''),
            1 if request.form.get('is_dynamic') else 0,
            request.form.get('segment_rules', ''),
            request.form.get('status', 'Active'),
            request.form.get('notes', ''),
            id
        ))
        db.commit()
        
        log_marketing_audit(db, 'segment', id, 'UPDATE', actor_user_id=user['id'])
        flash('Segment updated successfully.', 'success')
        return redirect(url_for('marketing.segments_view', id=id))
    
    db.close()
    return render_template('marketing/segment_edit.html', title=f'Edit: {segment["name"]}', segment=dict(segment))


# =============================================================================
# MARKETING CHANNELS
# =============================================================================

@mkt_bp.route('/channels')
@mkt_login_required
@mkt_permission_required('view_channels')
def channels_list():
    """List marketing channels."""
    db = get_db()
    
    channels = db.execute("""
        SELECT c.*, u.username as owner_name,
               (SELECT COUNT(*) FROM marketing_campaign_channels WHERE channel_id = c.id) as campaign_count
        FROM marketing_channels c
        LEFT JOIN users u ON c.owner_user_id = u.id
        ORDER BY c.channel_type, c.name
    """).fetchall()
    
    db.close()
    
    return render_template('marketing/channels.html',
        title='Marketing Channels',
        channels=[dict(r) for r in channels],
    )


@mkt_bp.route('/channels/new', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_channels')
def channels_new():
    """Create new marketing channel."""
    db = get_db()
    user = get_current_user()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip()
        channel_type = request.form.get('channel_type', '').strip()
        
        if not name or not channel_type:
            flash('Channel name and type are required.', 'error')
            return render_template('marketing/channel_edit.html', title='New Channel', channel=None)
        
        if not code:
            code = ''.join([w[0] for w in name.split()]).upper()[:8]
        
        cursor = db.execute("""
            INSERT INTO marketing_channels
            (name, code, channel_type, description, owner_user_id,
             budget, target_audience, expected_kpi, status, notes, created_by_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, code, channel_type,
            request.form.get('description', ''),
            request.form.get('owner_user_id'),
            request.form.get('budget', 0),
            request.form.get('target_audience', ''),
            request.form.get('expected_kpi', ''),
            request.form.get('status', 'Active'),
            request.form.get('notes', ''),
            user['id']
        ))
        db.commit()
        
        flash(f'Channel "{name}" created successfully.', 'success')
        return redirect(url_for('marketing.channels_list'))
    
    db.close()
    return render_template('marketing/channel_edit.html', title='New Channel', channel=None)


@mkt_bp.route('/channels/edit/<int:id>', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_channels')
def channels_edit(id):
    """Edit marketing channel."""
    db = get_db()
    user = get_current_user()
    
    channel = db.execute("SELECT * FROM marketing_channels WHERE id = ?", (id,)).fetchone()
    if not channel:
        flash('Channel not found.', 'error')
        return redirect(url_for('marketing.channels_list'))
    
    if request.method == 'POST':
        db.execute("""
            UPDATE marketing_channels SET
                name = ?, code = ?, channel_type = ?,
                description = ?, owner_user_id = ?, budget = ?,
                target_audience = ?, expected_kpi = ?, status = ?, notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            request.form.get('name', ''),
            request.form.get('code', ''),
            request.form.get('channel_type', ''),
            request.form.get('description', ''),
            request.form.get('owner_user_id'),
            request.form.get('budget', 0),
            request.form.get('target_audience', ''),
            request.form.get('expected_kpi', ''),
            request.form.get('status', 'Active'),
            request.form.get('notes', ''),
            id
        ))
        db.commit()
        
        flash('Channel updated successfully.', 'success')
        return redirect(url_for('marketing.channels_list'))
    
    db.close()
    return render_template('marketing/channel_edit.html', title=f'Edit: {channel["name"]}', channel=dict(channel))


# =============================================================================
# CAMPAIGNS
# =============================================================================

@mkt_bp.route('/campaigns')
@mkt_login_required
@mkt_permission_required('view_campaigns')
def campaigns_list():
    """List marketing campaigns."""
    db = get_db()
    
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    campaign_type = request.args.get('campaign_type', '')
    
    query = """
        SELECT c.*, u.username as owner_name,
               b.name as brand_name,
               s.name as segment_name
        FROM marketing_campaigns c
        LEFT JOIN users u ON c.owner_user_id = u.id
        LEFT JOIN marketing_brands b ON c.target_brand_id = b.id
        LEFT JOIN marketing_customer_segments s ON c.target_segment_id = s.id
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) as cnt FROM marketing_campaigns WHERE 1=1"
    params = []
    count_params = []
    
    if search:
        query += " AND (c.name LIKE ? OR c.code LIKE ?)"
        count_query += " AND (name LIKE ? OR code LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
        count_params.extend([search_term, search_term])
    
    if status:
        query += " AND c.status = ?"
        count_query += " AND status = ?"
        params.append(status)
        count_params.append(status)
    
    if campaign_type:
        query += " AND c.campaign_type = ?"
        count_query += " AND campaign_type = ?"
        params.append(campaign_type)
        count_params.append(campaign_type)
    
    total = db.execute(count_query, count_params).fetchone()['cnt']
    query += " ORDER BY c.created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    campaigns = db.execute(query, params).fetchall()
    
    # Get campaign types from settings
    campaign_types = db.execute("""
        SELECT setting_value FROM marketing_settings 
        WHERE category = 'campaign_types' AND is_active = 1
    """).fetchall()
    
    db.close()
    
    return render_template('marketing/campaigns.html',
        title='Campaigns',
        campaigns=[dict(r) for r in campaigns],
        page=page, per_page=per_page, total=total,
        search=search, status=status, campaign_type=campaign_type,
        campaign_types=[r['setting_value'] for r in campaign_types],
    )


@mkt_bp.route('/campaigns/new', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_campaigns')
def campaigns_new():
    """Create new marketing campaign."""
    db = get_db()
    user = get_current_user()
    
    # Get lookup data
    brands = db.execute("SELECT id, name FROM marketing_brands WHERE status = 'Active' ORDER BY name").fetchall()
    segments = db.execute("SELECT id, name FROM marketing_customer_segments WHERE status = 'Active' ORDER BY name").fetchall()
    channels = db.execute("SELECT id, name, channel_type FROM marketing_channels WHERE status = 'Active' ORDER BY name").fetchall()
    salespersons = db.execute("SELECT id, username FROM users ORDER BY username").fetchall()
    
    campaign_types = db.execute("""
        SELECT setting_value FROM marketing_settings 
        WHERE category = 'campaign_types' AND is_active = 1
    """).fetchall()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip()
        campaign_type = request.form.get('campaign_type', '').strip()
        
        if not name or not campaign_type:
            flash('Campaign name and type are required.', 'error')
            return render_template('marketing/campaign_edit.html', title='New Campaign', campaign=None,
                                   brands=[dict(r) for r in brands], segments=[dict(r) for r in segments],
                                   channels=[dict(r) for r in channels], salespersons=[dict(r) for r in salespersons],
                                   campaign_types=[r['setting_value'] for r in campaign_types])
        
        if not code:
            code = f"CMP-{datetime.now().strftime('%Y%m%d')}"
        
        # Generate unique code if exists
        existing = db.execute("SELECT id FROM marketing_campaigns WHERE code = ?", (code,)).fetchone()
        if existing:
            code = f"{code}-{datetime.now().strftime('%H%M%S')}"
        
        cursor = db.execute("""
            INSERT INTO marketing_campaigns
            (name, code, campaign_type, goal, start_date, end_date,
             target_market, target_segment_id, target_brand_id, target_products,
             budget, owner_user_id, main_message, sales_offer, ad_copy,
             media_assets, landing_page_url, posting_frequency, target_kpi,
             status, approval_state, linked_lead_source, notes, created_by_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, code, campaign_type,
            request.form.get('goal', ''),
            request.form.get('start_date', ''),
            request.form.get('end_date', ''),
            request.form.get('target_market', ''),
            request.form.get('target_segment_id'),
            request.form.get('target_brand_id'),
            request.form.get('target_products', ''),
            request.form.get('budget', 0),
            request.form.get('owner_user_id'),
            request.form.get('main_message', ''),
            request.form.get('sales_offer', ''),
            request.form.get('ad_copy', ''),
            request.form.get('media_assets', ''),
            request.form.get('landing_page_url', ''),
            request.form.get('posting_frequency', ''),
            request.form.get('target_kpi', ''),
            request.form.get('status', 'Draft'),
            'Pending',
            request.form.get('linked_lead_source', ''),
            request.form.get('notes', ''),
            user['id']
        ))
        db.commit()
        camp_id = cursor.lastrowid
        
        # Handle campaign channels
        selected_channels = request.form.getlist('selected_channels')
        for chan_id in selected_channels:
            chan_budget = request.form.get(f'channel_budget_{chan_id}', 0)
            db.execute("""
                INSERT INTO marketing_campaign_channels (campaign_id, channel_id, budget_allocated)
                VALUES (?, ?, ?)
            """, (camp_id, chan_id, chan_budget))
        db.commit()
        
        log_marketing_audit(db, 'campaign', camp_id, 'CREATE',
                           new_value=json.dumps({'name': name, 'code': code, 'type': campaign_type}),
                           actor_user_id=user['id'])
        
        flash(f'Campaign "{name}" created successfully.', 'success')
        return redirect(url_for('marketing.campaigns_view', id=camp_id))
    
    db.close()
    return render_template('marketing/campaign_edit.html', title='New Campaign', campaign=None,
                          brands=[dict(r) for r in brands], segments=[dict(r) for r in segments],
                          channels=[dict(r) for r in channels], salespersons=[dict(r) for r in salespersons],
                          campaign_types=[r['setting_value'] for r in campaign_types])


@mkt_bp.route('/campaigns/view/<int:id>')
@mkt_login_required
@mkt_permission_required('view_campaigns')
def campaigns_view(id):
    """View campaign details."""
    db = get_db()
    
    campaign = db.execute("""
        SELECT c.*, u.username as owner_name,
               b.name as brand_name,
               s.name as segment_name,
               ap.username as approved_by_name
        FROM marketing_campaigns c
        LEFT JOIN users u ON c.owner_user_id = u.id
        LEFT JOIN marketing_brands b ON c.target_brand_id = b.id
        LEFT JOIN marketing_customer_segments s ON c.target_segment_id = s.id
        LEFT JOIN users ap ON c.approved_by_user_id = ap.id
        WHERE c.id = ?
    """, (id,)).fetchone()
    
    if not campaign:
        flash('Campaign not found.', 'error')
        return redirect(url_for('marketing.campaigns_list'))
    
    # Get campaign channels
    camp_channels = db.execute("""
        SELECT cc.*, c.name as channel_name, c.channel_type
        FROM marketing_campaign_channels cc
        JOIN marketing_channels c ON cc.channel_id = c.id
        WHERE cc.campaign_id = ?
    """, (id,)).fetchall()
    
    # Get leads for this campaign
    leads = db.execute("""
        SELECT COUNT(*) as cnt FROM marketing_leads WHERE related_campaign_id = ?
    """, (id,)).fetchone()['cnt']
    
    # Get content linked to this campaign
    content = db.execute("""
        SELECT id, topic, title, content_format, status, publish_date
        FROM marketing_content
        WHERE linked_campaign_id = ?
        ORDER BY publish_date DESC
    """, (id,)).fetchall()
    
    db.close()
    
    return render_template('marketing/campaign_view.html',
        title=f'Campaign: {campaign["name"]}',
        campaign=dict(campaign),
        camp_channels=[dict(r) for r in camp_channels],
        leads_count=leads,
        content=[dict(r) for r in content],
    )


@mkt_bp.route('/campaigns/edit/<int:id>', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_campaigns')
def campaigns_edit(id):
    """Edit marketing campaign."""
    db = get_db()
    user = get_current_user()
    
    campaign = db.execute("SELECT * FROM marketing_campaigns WHERE id = ?", (id,)).fetchone()
    if not campaign:
        flash('Campaign not found.', 'error')
        return redirect(url_for('marketing.campaigns_list'))
    
    brands = db.execute("SELECT id, name FROM marketing_brands WHERE status = 'Active' ORDER BY name").fetchall()
    segments = db.execute("SELECT id, name FROM marketing_customer_segments WHERE status = 'Active' ORDER BY name").fetchall()
    channels = db.execute("SELECT id, name, channel_type FROM marketing_channels WHERE status = 'Active' ORDER BY name").fetchall()
    salespersons = db.execute("SELECT id, username FROM users ORDER BY username").fetchall()
    
    campaign_types = db.execute("""
        SELECT setting_value FROM marketing_settings 
        WHERE category = 'campaign_types' AND is_active = 1
    """).fetchall()
    
    # Get current campaign channels
    current_channels = db.execute("""
        SELECT channel_id, budget_allocated FROM marketing_campaign_channels WHERE campaign_id = ?
    """, (id,)).fetchall()
    current_channel_ids = [r['channel_id'] for r in current_channels]
    current_channel_budgets = {r['channel_id']: r['budget_allocated'] for r in current_channels}
    
    if request.method == 'POST':
        db.execute("""
            UPDATE marketing_campaigns SET
                name = ?, code = ?, campaign_type = ?, goal = ?,
                start_date = ?, end_date = ?, target_market = ?,
                target_segment_id = ?, target_brand_id = ?, target_products = ?,
                budget = ?, owner_user_id = ?, main_message = ?,
                sales_offer = ?, ad_copy = ?, media_assets = ?,
                landing_page_url = ?, posting_frequency = ?, target_kpi = ?,
                status = ?, linked_lead_source = ?, notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            request.form.get('name', ''),
            request.form.get('code', ''),
            request.form.get('campaign_type', ''),
            request.form.get('goal', ''),
            request.form.get('start_date', ''),
            request.form.get('end_date', ''),
            request.form.get('target_market', ''),
            request.form.get('target_segment_id'),
            request.form.get('target_brand_id'),
            request.form.get('target_products', ''),
            request.form.get('budget', 0),
            request.form.get('owner_user_id'),
            request.form.get('main_message', ''),
            request.form.get('sales_offer', ''),
            request.form.get('ad_copy', ''),
            request.form.get('media_assets', ''),
            request.form.get('landing_page_url', ''),
            request.form.get('posting_frequency', ''),
            request.form.get('target_kpi', ''),
            request.form.get('status', 'Draft'),
            request.form.get('linked_lead_source', ''),
            request.form.get('notes', ''),
            id
        ))
        
        # Update campaign channels
        db.execute("DELETE FROM marketing_campaign_channels WHERE campaign_id = ?", (id,))
        selected_channels = request.form.getlist('selected_channels')
        for chan_id in selected_channels:
            chan_budget = request.form.get(f'channel_budget_{chan_id}', 0)
            db.execute("""
                INSERT INTO marketing_campaign_channels (campaign_id, channel_id, budget_allocated)
                VALUES (?, ?, ?)
            """, (id, chan_id, chan_budget))
        
        db.commit()
        
        log_marketing_audit(db, 'campaign', id, 'UPDATE', actor_user_id=user['id'])
        flash('Campaign updated successfully.', 'success')
        return redirect(url_for('marketing.campaigns_view', id=id))
    
    db.close()
    
    return render_template('marketing/campaign_edit.html', title=f'Edit: {campaign["name"]}',
                          campaign=dict(campaign),
                          brands=[dict(r) for r in brands], segments=[dict(r) for r in segments],
                          channels=[dict(r) for r in channels], salespersons=[dict(r) for r in salespersons],
                          campaign_types=[r['setting_value'] for r in campaign_types],
                          current_channel_ids=current_channel_ids,
                          current_channel_budgets=current_channel_budgets)


@mkt_bp.route('/campaigns/approve/<int:id>', methods=['POST'])
@mkt_login_required
@mkt_permission_required('approve_campaigns')
def campaigns_approve(id):
    """Approve a marketing campaign."""
    db = get_db()
    user = get_current_user()
    
    campaign = db.execute("SELECT * FROM marketing_campaigns WHERE id = ?", (id,)).fetchone()
    if not campaign:
        return jsonify({'success': False, 'message': 'Campaign not found'}), 404
    
    db.execute("""
        UPDATE marketing_campaigns SET
            approval_state = 'Approved',
            approved_by_user_id = ?,
            approved_at = CURRENT_TIMESTAMP,
            status = 'Active'
        WHERE id = ?
    """, (user['id'], id))
    db.commit()
    
    log_marketing_audit(db, 'campaign', id, 'APPROVE', actor_user_id=user['id'])
    
    flash(f'Campaign "{campaign["name"]}" approved successfully.', 'success')
    return redirect(url_for('marketing.campaigns_view', id=id))


@mkt_bp.route('/campaigns/delete/<int:id>', methods=['POST'])
@mkt_login_required
@mkt_permission_required('manage_campaigns')
def campaigns_delete(id):
    """Delete a campaign."""
    db = get_db()
    user = get_current_user()
    
    campaign = db.execute("SELECT * FROM marketing_campaigns WHERE id = ?", (id,)).fetchone()
    if not campaign:
        return jsonify({'success': False, 'message': 'Campaign not found'}), 404
    
    db.execute("DELETE FROM marketing_campaign_channels WHERE campaign_id = ?", (id,))
    db.execute("DELETE FROM marketing_campaigns WHERE id = ?", (id,))
    db.commit()
    
    log_marketing_audit(db, 'campaign', id, 'DELETE',
                       old_value=json.dumps({'name': campaign['name']}),
                       actor_user_id=user['id'])
    
    flash(f'Campaign "{campaign["name"]}" deleted successfully.', 'success')
    return redirect(url_for('marketing.campaigns_list'))


# =============================================================================
# ADVERTISING
# =============================================================================

@mkt_bp.route('/advertisements')
@mkt_login_required
@mkt_permission_required('view_advertisements')
def advertisements_list():
    """List advertisements."""
    db = get_db()
    
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    ad_type = request.args.get('ad_type', '')
    
    query = """
        SELECT a.*, c.name as channel_name,
               b.name as brand_name,
               u.username as created_by_name
        FROM marketing_advertisements a
        LEFT JOIN marketing_channels c ON a.channel_id = c.id
        LEFT JOIN marketing_brands b ON a.linked_brand_id = b.id
        LEFT JOIN users u ON a.created_by_user_id = u.id
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) as cnt FROM marketing_advertisements WHERE 1=1"
    params = []
    count_params = []
    
    if search:
        query += " AND (a.title LIKE ? OR a.content_text LIKE ?)"
        count_query += " AND (title LIKE ? OR content_text LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
        count_params.extend([search_term, search_term])
    
    if status:
        query += " AND a.status = ?"
        count_query += " AND a.status = ?"
        params.append(status)
        count_params.append(status)
    
    if ad_type:
        query += " AND a.advertisement_type = ?"
        count_query += " AND a.advertisement_type = ?"
        params.append(ad_type)
        count_params.append(ad_type)
    
    total = db.execute(count_query, count_params).fetchone()['cnt']
    query += " ORDER BY a.created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    ads = db.execute(query, params).fetchall()
    
    ad_types = db.execute("""
        SELECT setting_value FROM marketing_settings 
        WHERE category = 'ad_types' AND is_active = 1
    """).fetchall()
    
    db.close()
    
    return render_template('marketing/advertisements.html',
        title='Advertisements',
        ads=[dict(r) for r in ads],
        page=page, per_page=per_page, total=total,
        search=search, status=status, ad_type=ad_type,
        ad_types=[r['setting_value'] for r in ad_types],
    )


@mkt_bp.route('/advertisements/new', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_advertisements')
def advertisements_new():
    """Create new advertisement."""
    db = get_db()
    user = get_current_user()
    
    channels = db.execute("SELECT id, name FROM marketing_channels WHERE status = 'Active'").fetchall()
    brands = db.execute("SELECT id, name FROM marketing_brands WHERE status = 'Active'").fetchall()
    campaigns = db.execute("SELECT id, name FROM marketing_campaigns WHERE status IN ('Active', 'Draft')").fetchall()
    
    ad_types = db.execute("""
        SELECT setting_value FROM marketing_settings 
        WHERE category = 'ad_types' AND is_active = 1
    """).fetchall()
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Advertisement title is required.', 'error')
            return render_template('marketing/advertisement_edit.html', title='New Advertisement', ad=None,
                                   channels=[dict(r) for r in channels], brands=[dict(r) for r in brands],
                                   campaigns=[dict(r) for r in campaigns], ad_types=[r['setting_value'] for r in ad_types])
        
        cursor = db.execute("""
            INSERT INTO marketing_advertisements
            (title, advertisement_type, objective, channel_id, publish_date,
             placement, content_text, cta_text, cta_url, budget,
             audience, linked_campaign_id, linked_brand_id, linked_products,
             validity_date, status, notes, created_by_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title,
            request.form.get('advertisement_type', ''),
            request.form.get('objective', ''),
            request.form.get('channel_id'),
            request.form.get('publish_date', ''),
            request.form.get('placement', ''),
            request.form.get('content_text', ''),
            request.form.get('cta_text', ''),
            request.form.get('cta_url', ''),
            request.form.get('budget', 0),
            request.form.get('audience', ''),
            request.form.get('linked_campaign_id'),
            request.form.get('linked_brand_id'),
            request.form.get('linked_products', ''),
            request.form.get('validity_date', ''),
            request.form.get('status', 'Draft'),
            request.form.get('notes', ''),
            user['id']
        ))
        db.commit()
        
        flash(f'Advertisement "{title}" created successfully.', 'success')
        return redirect(url_for('marketing.advertisements_list'))
    
    db.close()
    return render_template('marketing/advertisement_edit.html', title='New Advertisement', ad=None,
                          channels=[dict(r) for r in channels], brands=[dict(r) for r in brands],
                          campaigns=[dict(r) for r in campaigns], ad_types=[r['setting_value'] for r in ad_types])


@mkt_bp.route('/advertisements/edit/<int:id>', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_advertisements')
def advertisements_edit(id):
    """Edit advertisement."""
    db = get_db()
    user = get_current_user()
    
    ad = db.execute("SELECT * FROM marketing_advertisements WHERE id = ?", (id,)).fetchone()
    if not ad:
        flash('Advertisement not found.', 'error')
        return redirect(url_for('marketing.advertisements_list'))
    
    channels = db.execute("SELECT id, name FROM marketing_channels WHERE status = 'Active'").fetchall()
    brands = db.execute("SELECT id, name FROM marketing_brands WHERE status = 'Active'").fetchall()
    campaigns = db.execute("SELECT id, name FROM marketing_campaigns WHERE status IN ('Active', 'Draft')").fetchall()
    
    ad_types = db.execute("""
        SELECT setting_value FROM marketing_settings 
        WHERE category = 'ad_types' AND is_active = 1
    """).fetchall()
    
    if request.method == 'POST':
        db.execute("""
            UPDATE marketing_advertisements SET
                title = ?, advertisement_type = ?, objective = ?,
                channel_id = ?, publish_date = ?, placement = ?,
                content_text = ?, cta_text = ?, cta_url = ?, budget = ?,
                audience = ?, linked_campaign_id = ?, linked_brand_id = ?,
                linked_products = ?, validity_date = ?, status = ?, notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            request.form.get('title', ''),
            request.form.get('advertisement_type', ''),
            request.form.get('objective', ''),
            request.form.get('channel_id'),
            request.form.get('publish_date', ''),
            request.form.get('placement', ''),
            request.form.get('content_text', ''),
            request.form.get('cta_text', ''),
            request.form.get('cta_url', ''),
            request.form.get('budget', 0),
            request.form.get('audience', ''),
            request.form.get('linked_campaign_id'),
            request.form.get('linked_brand_id'),
            request.form.get('linked_products', ''),
            request.form.get('validity_date', ''),
            request.form.get('status', 'Draft'),
            request.form.get('notes', ''),
            id
        ))
        db.commit()
        
        flash('Advertisement updated successfully.', 'success')
        return redirect(url_for('marketing.advertisements_list'))
    
    db.close()
    return render_template('marketing/advertisement_edit.html', title=f'Edit: {ad["title"]}', ad=dict(ad),
                          channels=[dict(r) for r in channels], brands=[dict(r) for r in brands],
                          campaigns=[dict(r) for r in campaigns], ad_types=[r['setting_value'] for r in ad_types])


# =============================================================================
# CONTENT & CONTENT CALENDAR
# =============================================================================

@mkt_bp.route('/content')
@mkt_login_required
@mkt_permission_required('view_content')
def content_list():
    """List content items."""
    db = get_db()
    
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    content_format = request.args.get('content_format', '')
    
    query = """
        SELECT ct.*, c.name as channel_name,
               b.name as brand_name,
               u.username as creator_name
        FROM marketing_content ct
        LEFT JOIN marketing_channels c ON ct.channel_id = c.id
        LEFT JOIN marketing_brands b ON ct.linked_brand_id = b.id
        LEFT JOIN users u ON ct.content_creator_id = u.id
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) as cnt FROM marketing_content WHERE 1=1"
    params = []
    count_params = []
    
    if search:
        query += " AND (ct.topic LIKE ? OR ct.title LIKE ?)"
        count_query += " AND (topic LIKE ? OR title LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
        count_params.extend([search_term, search_term])
    
    if status:
        query += " AND ct.status = ?"
        count_query += " AND ct.status = ?"
        params.append(status)
        count_params.append(status)
    
    if content_format:
        query += " AND ct.content_format = ?"
        count_query += " AND ct.content_format = ?"
        params.append(content_format)
        count_params.append(content_format)
    
    total = db.execute(count_query, count_params).fetchone()['cnt']
    query += " ORDER BY ct.publish_date DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    content_items = db.execute(query, params).fetchall()
    
    content_formats = db.execute("""
        SELECT setting_value FROM marketing_settings 
        WHERE category = 'content_formats' AND is_active = 1
    """).fetchall()
    
    db.close()
    
    return render_template('marketing/content_list.html',
        title='Content',
        content_items=[dict(r) for r in content_items],
        page=page, per_page=per_page, total=total,
        search=search, status=status, content_format=content_format,
        content_formats=[r['setting_value'] for r in content_formats],
    )


@mkt_bp.route('/content/new', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_content')
def content_new():
    """Create new content item."""
    db = get_db()
    user = get_current_user()
    
    channels = db.execute("SELECT id, name FROM marketing_channels WHERE status = 'Active'").fetchall()
    brands = db.execute("SELECT id, name FROM marketing_brands WHERE status = 'Active'").fetchall()
    campaigns = db.execute("SELECT id, name FROM marketing_campaigns WHERE status IN ('Active', 'Draft')").fetchall()
    creators = db.execute("SELECT id, username FROM users ORDER BY username").fetchall()
    
    content_types = db.execute("SELECT setting_value FROM marketing_settings WHERE category = 'content_types' AND is_active = 1").fetchall()
    content_formats = db.execute("SELECT setting_value FROM marketing_settings WHERE category = 'content_formats' AND is_active = 1").fetchall()
    
    if request.method == 'POST':
        topic = request.form.get('topic', '').strip()
        if not topic:
            flash('Content topic is required.', 'error')
            return render_template('marketing/content_edit.html', title='New Content', content=None,
                                   channels=[dict(r) for r in channels], brands=[dict(r) for r in brands],
                                   campaigns=[dict(r) for r in campaigns], creators=[dict(r) for r in creators],
                                   content_types=[r['setting_value'] for r in content_types],
                                   content_formats=[r['setting_value'] for r in content_formats])
        
        cursor = db.execute("""
            INSERT INTO marketing_content
            (topic, title, content_objective, target_audience, channel_id,
             content_format, content_text, publish_date, content_creator_id,
             linked_campaign_id, linked_brand_id, linked_products, linked_market,
             status, notes, created_by_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            topic,
            request.form.get('title', ''),
            request.form.get('content_objective', ''),
            request.form.get('target_audience', ''),
            request.form.get('channel_id'),
            request.form.get('content_format', ''),
            request.form.get('content_text', ''),
            request.form.get('publish_date', ''),
            request.form.get('content_creator_id'),
            request.form.get('linked_campaign_id'),
            request.form.get('linked_brand_id'),
            request.form.get('linked_products', ''),
            request.form.get('linked_market', ''),
            request.form.get('status', 'Draft'),
            request.form.get('notes', ''),
            user['id']
        ))
        db.commit()
        
        flash(f'Content "{topic}" created successfully.', 'success')
        return redirect(url_for('marketing.content_list'))
    
    db.close()
    return render_template('marketing/content_edit.html', title='New Content', content=None,
                          channels=[dict(r) for r in channels], brands=[dict(r) for r in brands],
                          campaigns=[dict(r) for r in campaigns], creators=[dict(r) for r in creators],
                          content_types=[r['setting_value'] for r in content_types],
                          content_formats=[r['setting_value'] for r in content_formats])


@mkt_bp.route('/content/edit/<int:id>', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_content')
def content_edit(id):
    """Edit content item."""
    db = get_db()
    user = get_current_user()
    
    content = db.execute("SELECT * FROM marketing_content WHERE id = ?", (id,)).fetchone()
    if not content:
        flash('Content not found.', 'error')
        return redirect(url_for('marketing.content_list'))
    
    channels = db.execute("SELECT id, name FROM marketing_channels WHERE status = 'Active'").fetchall()
    brands = db.execute("SELECT id, name FROM marketing_brands WHERE status = 'Active'").fetchall()
    campaigns = db.execute("SELECT id, name FROM marketing_campaigns WHERE status IN ('Active', 'Draft')").fetchall()
    creators = db.execute("SELECT id, username FROM users ORDER BY username").fetchall()
    
    content_types = db.execute("SELECT setting_value FROM marketing_settings WHERE category = 'content_types' AND is_active = 1").fetchall()
    content_formats = db.execute("SELECT setting_value FROM marketing_settings WHERE category = 'content_formats' AND is_active = 1").fetchall()
    
    if request.method == 'POST':
        db.execute("""
            UPDATE marketing_content SET
                topic = ?, title = ?, content_objective = ?, target_audience = ?,
                channel_id = ?, content_format = ?, content_text = ?, publish_date = ?,
                content_creator_id = ?, linked_campaign_id = ?, linked_brand_id = ?,
                linked_products = ?, linked_market = ?, status = ?, notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            request.form.get('topic', ''),
            request.form.get('title', ''),
            request.form.get('content_objective', ''),
            request.form.get('target_audience', ''),
            request.form.get('channel_id'),
            request.form.get('content_format', ''),
            request.form.get('content_text', ''),
            request.form.get('publish_date', ''),
            request.form.get('content_creator_id'),
            request.form.get('linked_campaign_id'),
            request.form.get('linked_brand_id'),
            request.form.get('linked_products', ''),
            request.form.get('linked_market', ''),
            request.form.get('status', 'Draft'),
            request.form.get('notes', ''),
            id
        ))
        db.commit()
        
        flash('Content updated successfully.', 'success')
        return redirect(url_for('marketing.content_list'))
    
    db.close()
    return render_template('marketing/content_edit.html', title=f'Edit: {content["topic"]}', content=dict(content),
                          channels=[dict(r) for r in channels], brands=[dict(r) for r in brands],
                          campaigns=[dict(r) for r in campaigns], creators=[dict(r) for r in creators],
                          content_types=[r['setting_value'] for r in content_types],
                          content_formats=[r['setting_value'] for r in content_formats])


@mkt_bp.route('/content-calendar')
@mkt_login_required
@mkt_permission_required('view_content')
def content_calendar():
    """Content calendar view."""
    db = get_db()
    
    # Get month/year from request or use current
    month = int(request.args.get('month', datetime.now().month))
    year = int(request.args.get('year', datetime.now().year))
    
    # Get all planned content for the month
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{year}-{month:02d}-31"
    
    calendar_items = db.execute("""
        SELECT cc.*, c.name as channel_name,
               b.name as brand_name
        FROM marketing_content_calendar cc
        LEFT JOIN marketing_channels c ON cc.channel_id = c.id
        LEFT JOIN marketing_brands b ON cc.linked_brand_id = b.id
        WHERE cc.planned_date BETWEEN ? AND ?
        ORDER BY cc.planned_date, cc.planned_time
    """, (start_date, end_date)).fetchall()
    
    # Get campaign types for reference
    campaign_types = db.execute("""
        SELECT setting_value FROM marketing_settings 
        WHERE category = 'campaign_types' AND is_active = 1
    """).fetchall()
    
    db.close()
    
    return render_template('marketing/content_calendar.html',
        title='Content Calendar',
        calendar_items=[dict(r) for r in calendar_items],
        month=month, year=year,
        campaign_types=[r['setting_value'] for r in campaign_types],
    )


# =============================================================================
# LEADS
# =============================================================================

@mkt_bp.route('/leads')
@mkt_login_required
@mkt_permission_required('view_leads')
def leads_list():
    """List marketing leads."""
    db = get_db()
    
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    source_id = request.args.get('source_id', '')
    
    query = """
        SELECT l.*, ls.name as source_name,
               u.username as assigned_name,
               c.name as campaign_name
        FROM marketing_leads l
        LEFT JOIN marketing_lead_sources ls ON l.source_id = ls.id
        LEFT JOIN users u ON l.assigned_salesperson_id = u.id
        LEFT JOIN marketing_campaigns c ON l.related_campaign_id = c.id
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) as cnt FROM marketing_leads WHERE 1=1"
    params = []
    count_params = []
    
    if search:
        query += " AND (l.lead_name LIKE ? OR l.phone LIKE ? OR l.email LIKE ?)"
        count_query += " AND (lead_name LIKE ? OR phone LIKE ? OR email LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
        count_params.extend([search_term, search_term, search_term])
    
    if status:
        query += " AND l.lead_status = ?"
        count_query += " AND l.lead_status = ?"
        params.append(status)
        count_params.append(status)
    
    if source_id:
        query += " AND l.source_id = ?"
        count_query += " AND l.source_id = ?"
        params.append(source_id)
        count_params.append(source_id)
    
    total = db.execute(count_query, count_params).fetchone()['cnt']
    query += " ORDER BY l.created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    leads = db.execute(query, params).fetchall()
    
    sources = db.execute("SELECT id, name FROM marketing_lead_sources WHERE status = 'Active' ORDER BY name").fetchall()
    
    lead_statuses = db.execute("""
        SELECT setting_value FROM marketing_settings 
        WHERE category = 'lead_statuses' AND is_active = 1
    """).fetchall()
    
    db.close()
    
    return render_template('marketing/leads.html',
        title='Leads',
        leads=[dict(r) for r in leads],
        page=page, per_page=per_page, total=total,
        search=search, status=status, source_id=source_id,
        sources=[dict(r) for r in sources],
        lead_statuses=[r['setting_value'] for r in lead_statuses],
    )


@mkt_bp.route('/leads/new', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_leads')
def leads_new():
    """Create new lead."""
    db = get_db()
    user = get_current_user()
    
    sources = db.execute("SELECT id, name, code FROM marketing_lead_sources WHERE status = 'Active'").fetchall()
    brands = db.execute("SELECT id, name FROM marketing_brands WHERE status = 'Active'").fetchall()
    campaigns = db.execute("SELECT id, name FROM marketing_campaigns WHERE status IN ('Active', 'Draft')").fetchall()
    salespersons = db.execute("SELECT id, username FROM users ORDER BY username").fetchall()
    
    lead_statuses = db.execute("SELECT setting_value FROM marketing_settings WHERE category = 'lead_statuses' AND is_active = 1").fetchall()
    importance_levels = db.execute("SELECT setting_value FROM marketing_settings WHERE category = 'importance_levels' AND is_active = 1").fetchall()
    
    if request.method == 'POST':
        lead_name = request.form.get('lead_name', '').strip()
        if not lead_name:
            flash('Lead name is required.', 'error')
            return render_template('marketing/lead_edit.html', title='New Lead', lead=None,
                                   sources=[dict(r) for r in sources], brands=[dict(r) for r in brands],
                                   campaigns=[dict(r) for r in campaigns], salespersons=[dict(r) for r in salespersons],
                                   lead_statuses=[r['setting_value'] for r in lead_statuses],
                                   importance_levels=[r['setting_value'] for r in importance_levels])
        
        cursor = db.execute("""
            INSERT INTO marketing_leads
            (lead_name, phone, whatsapp, email, city, country, industry, trade_type,
             source_id, product_interest, brand_interest, customer_type,
             importance_level, lead_status, assigned_salesperson_id, follow_up_date,
             follow_up_notes, related_campaign_id, related_market,
             estimated_value, conversion_probability, notes, created_by_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead_name,
            request.form.get('phone', ''),
            request.form.get('whatsapp', ''),
            request.form.get('email', ''),
            request.form.get('city', ''),
            request.form.get('country', ''),
            request.form.get('industry', ''),
            request.form.get('trade_type', ''),
            request.form.get('source_id'),
            request.form.get('product_interest', ''),
            request.form.get('brand_interest', ''),
            request.form.get('customer_type', ''),
            request.form.get('importance_level', 'Medium'),
            request.form.get('lead_status', 'New'),
            request.form.get('assigned_salesperson_id'),
            request.form.get('follow_up_date', ''),
            request.form.get('follow_up_notes', ''),
            request.form.get('related_campaign_id'),
            request.form.get('related_market', ''),
            request.form.get('estimated_value', 0),
            request.form.get('conversion_probability', 0),
            request.form.get('notes', ''),
            user['id']
        ))
        db.commit()
        lead_id = cursor.lastrowid
        
        # Log funnel entry
        first_stage = db.execute("SELECT id FROM marketing_funnel_stages WHERE stage_order = 1").fetchone()
        if first_stage:
            db.execute("""
                INSERT INTO marketing_funnel_records (lead_id, stage_id)
                VALUES (?, ?)
            """, (lead_id, first_stage['id']))
            db.commit()
        
        log_marketing_audit(db, 'lead', lead_id, 'CREATE',
                           new_value=json.dumps({'name': lead_name}),
                           actor_user_id=user['id'])
        
        flash(f'Lead "{lead_name}" created successfully.', 'success')
        return redirect(url_for('marketing.leads_view', id=lead_id))
    
    db.close()
    return render_template('marketing/lead_edit.html', title='New Lead', lead=None,
                          sources=[dict(r) for r in sources], brands=[dict(r) for r in brands],
                          campaigns=[dict(r) for r in campaigns], salespersons=[dict(r) for r in salespersons],
                          lead_statuses=[r['setting_value'] for r in lead_statuses],
                          importance_levels=[r['setting_value'] for r in importance_levels])


@mkt_bp.route('/leads/view/<int:id>')
@mkt_login_required
@mkt_permission_required('view_leads')
def leads_view(id):
    """View lead details."""
    db = get_db()
    
    lead = db.execute("""
        SELECT l.*, ls.name as source_name, ls.code as source_code,
               u.username as assigned_name,
               c.name as campaign_name,
               b.name as brand_interest_name
        FROM marketing_leads l
        LEFT JOIN marketing_lead_sources ls ON l.source_id = ls.id
        LEFT JOIN users u ON l.assigned_salesperson_id = u.id
        LEFT JOIN marketing_campaigns c ON l.related_campaign_id = c.id
        LEFT JOIN marketing_brands b ON l.brand_interest = CAST(b.id AS TEXT)
        WHERE l.id = ?
    """, (id,)).fetchone()
    
    if not lead:
        flash('Lead not found.', 'error')
        return redirect(url_for('marketing.leads_list'))
    
    # Get funnel history
    funnel_history = db.execute("""
        SELECT fr.*, fs.name as stage_name, fs.stage_order
        FROM marketing_funnel_records fr
        JOIN marketing_funnel_stages fs ON fr.stage_id = fs.id
        WHERE fr.lead_id = ?
        ORDER BY fr.entering_date DESC
    """, (id,)).fetchall()
    
    # Get lead activities
    activities = db.execute("""
        SELECT * FROM marketing_audit_logs
        WHERE entity_type = 'lead' AND entity_id = ?
        ORDER BY created_at DESC
        LIMIT 20
    """, (id,)).fetchall()
    
    db.close()
    
    return render_template('marketing/lead_view.html',
        title=f'Lead: {lead["lead_name"]}',
        lead=dict(lead),
        funnel_history=[dict(r) for r in funnel_history],
        activities=[dict(r) for r in activities],
    )


@mkt_bp.route('/leads/edit/<int:id>', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_leads')
def leads_edit(id):
    """Edit lead."""
    db = get_db()
    user = get_current_user()
    
    lead = db.execute("SELECT * FROM marketing_leads WHERE id = ?", (id,)).fetchone()
    if not lead:
        flash('Lead not found.', 'error')
        return redirect(url_for('marketing.leads_list'))
    
    sources = db.execute("SELECT id, name, code FROM marketing_lead_sources WHERE status = 'Active'").fetchall()
    brands = db.execute("SELECT id, name FROM marketing_brands WHERE status = 'Active'").fetchall()
    campaigns = db.execute("SELECT id, name FROM marketing_campaigns WHERE status IN ('Active', 'Draft')").fetchall()
    salespersons = db.execute("SELECT id, username FROM users ORDER BY username").fetchall()
    
    lead_statuses = db.execute("SELECT setting_value FROM marketing_settings WHERE category = 'lead_statuses' AND is_active = 1").fetchall()
    importance_levels = db.execute("SELECT setting_value FROM marketing_settings WHERE category = 'importance_levels' AND is_active = 1").fetchall()
    
    if request.method == 'POST':
        old_status = lead['lead_status']
        new_status = request.form.get('lead_status', 'New')
        
        db.execute("""
            UPDATE marketing_leads SET
                lead_name = ?, phone = ?, whatsapp = ?, email = ?,
                city = ?, country = ?, industry = ?, trade_type = ?,
                source_id = ?, product_interest = ?, brand_interest = ?,
                customer_type = ?, importance_level = ?, lead_status = ?,
                assigned_salesperson_id = ?, follow_up_date = ?,
                follow_up_notes = ?, related_campaign_id = ?, related_market = ?,
                estimated_value = ?, conversion_probability = ?,
                lost_reason = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            request.form.get('lead_name', ''),
            request.form.get('phone', ''),
            request.form.get('whatsapp', ''),
            request.form.get('email', ''),
            request.form.get('city', ''),
            request.form.get('country', ''),
            request.form.get('industry', ''),
            request.form.get('trade_type', ''),
            request.form.get('source_id'),
            request.form.get('product_interest', ''),
            request.form.get('brand_interest', ''),
            request.form.get('customer_type', ''),
            request.form.get('importance_level', 'Medium'),
            new_status,
            request.form.get('assigned_salesperson_id'),
            request.form.get('follow_up_date', ''),
            request.form.get('follow_up_notes', ''),
            request.form.get('related_campaign_id'),
            request.form.get('related_market', ''),
            request.form.get('estimated_value', 0),
            request.form.get('conversion_probability', 0),
            request.form.get('lost_reason', ''),
            request.form.get('notes', ''),
            id
        ))
        
        # If status changed to converted, record conversion
        if new_status == 'Converted to Customer' and old_status != 'Converted to Customer':
            db.execute("UPDATE marketing_leads SET converted_at = CURRENT_TIMESTAMP WHERE id = ?", (id,))
        
        db.commit()
        
        log_marketing_audit(db, 'lead', id, 'UPDATE',
                           field_name='lead_status',
                           old_value=old_status,
                           new_value=new_status,
                           actor_user_id=user['id'])
        
        flash('Lead updated successfully.', 'success')
        return redirect(url_for('marketing.leads_view', id=id))
    
    db.close()
    return render_template('marketing/lead_edit.html', title=f'Edit: {lead["lead_name"]}', lead=dict(lead),
                          sources=[dict(r) for r in sources], brands=[dict(r) for r in brands],
                          campaigns=[dict(r) for r in campaigns], salespersons=[dict(r) for r in salespersons],
                          lead_statuses=[r['setting_value'] for r in lead_statuses],
                          importance_levels=[r['setting_value'] for r in importance_levels])


@mkt_bp.route('/leads/assign', methods=['POST'])
@mkt_login_required
@mkt_permission_required('assign_leads')
def leads_assign():
    """Assign leads to a salesperson."""
    data = request.get_json()
    lead_ids = data.get('lead_ids', [])
    salesperson_id = data.get('salesperson_id')
    
    if not lead_ids or not salesperson_id:
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    db = get_db()
    user = get_current_user()
    
    for lead_id in lead_ids:
        db.execute("""
            UPDATE marketing_leads SET
                assigned_salesperson_id = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (salesperson_id, lead_id))
        
        log_marketing_audit(db, 'lead', lead_id, 'ASSIGN',
                           new_value=json.dumps({'salesperson_id': salesperson_id}),
                           actor_user_id=user['id'])
    
    db.commit()
    db.close()
    
    return jsonify({'success': True, 'message': f'{len(lead_ids)} lead(s) assigned successfully.'})


# =============================================================================
# FUNNEL & CONVERSION TRACKING
# =============================================================================

@mkt_bp.route('/funnel')
@mkt_login_required
@mkt_permission_required('view_reports')
def funnel_view():
    """View marketing funnel."""
    db = get_db()
    
    # Get funnel stages with counts
    funnel_stages = db.execute("""
        SELECT 
            fs.id, fs.name, fs.code, fs.stage_order, fs.stage_type, fs.description,
            COUNT(fr.id) as records_in_stage,
            AVG(ROUND((julianday(COALESCE(fr.exiting_date, CURRENT_TIMESTAMP)) - julianday(fr.entering_date)) * 24)) as avg_hours_in_stage
        FROM marketing_funnel_stages fs
        LEFT JOIN marketing_funnel_records fr ON fs.id = fr.stage_id
        WHERE fs.status = 'Active'
        GROUP BY fs.id
        ORDER BY fs.stage_order
    """).fetchall()
    
    # Calculate conversion rates between stages
    funnel_data = []
    prev_count = 0
    for stage in funnel_stages:
        stage_dict = dict(stage)
        if prev_count > 0:
            stage_dict['conversion_rate'] = round((stage_dict['records_in_stage'] / prev_count) * 100, 1) if prev_count > 0 else 0
        else:
            stage_dict['conversion_rate'] = 100
        prev_count = stage_dict['records_in_stage']
        funnel_data.append(stage_dict)
    
    # Get channel funnel breakdown
    channel_funnel = db.execute("""
        SELECT 
            c.name as channel_name,
            fs.name as stage_name,
            COUNT(fr.id) as count
        FROM marketing_funnel_records fr
        JOIN marketing_channels c ON fr.attributed_channel_id = c.id
        JOIN marketing_funnel_stages fs ON fr.stage_id = fs.id
        GROUP BY c.id, fs.stage_order
        ORDER BY c.name, fs.stage_order
    """).fetchall()
    
    # Get campaign funnel breakdown
    campaign_funnel = db.execute("""
        SELECT 
            c.name as campaign_name,
            c.code as campaign_code,
            fs.name as stage_name,
            COUNT(fr.id) as count
        FROM marketing_funnel_records fr
        JOIN marketing_campaigns c ON fr.attributed_campaign_id = c.id
        JOIN marketing_funnel_stages fs ON fr.stage_id = fs.id
        GROUP BY c.id, fs.stage_order
        ORDER BY c.name, fs.stage_order
    """).fetchall()
    
    db.close()
    
    return render_template('marketing/funnel.html',
        title='Funnel & Conversion',
        funnel_stages=funnel_data,
        channel_funnel=[dict(r) for r in channel_funnel],
        campaign_funnel=[dict(r) for r in campaign_funnel],
    )


# =============================================================================
# OFFERS & PROMOTIONS
# =============================================================================

@mkt_bp.route('/offers')
@mkt_login_required
@mkt_permission_required('view_offers')
def offers_list():
    """List offers and promotions."""
    db = get_db()
    
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    
    query = """
        SELECT o.*, u.username as salesperson_name,
               c.name as campaign_name
        FROM marketing_offers o
        LEFT JOIN users u ON o.responsible_salesperson_id = u.id
        LEFT JOIN marketing_campaigns c ON o.linked_campaign_id = c.id
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) as cnt FROM marketing_offers WHERE 1=1"
    params = []
    count_params = []
    
    if search:
        query += " AND (o.offer_number LIKE ? OR o.target_customer LIKE ?)"
        count_query += " AND (offer_number LIKE ? OR target_customer LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
        count_params.extend([search_term, search_term])
    
    if status:
        query += " AND o.status = ?"
        count_query += " AND o.status = ?"
        params.append(status)
        count_params.append(status)
    
    total = db.execute(count_query, count_params).fetchone()['cnt']
    query += " ORDER BY o.offer_date DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    offers = db.execute(query, params).fetchall()
    
    db.close()
    
    return render_template('marketing/offers.html',
        title='Offers & Promotions',
        offers=[dict(r) for r in offers],
        page=page, per_page=per_page, total=total,
        search=search, status=status,
    )


@mkt_bp.route('/offers/new', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_offers')
def offers_new():
    """Create new offer."""
    db = get_db()
    user = get_current_user()
    
    campaigns = db.execute("SELECT id, name FROM marketing_campaigns WHERE status IN ('Active', 'Draft')").fetchall()
    channels = db.execute("SELECT id, name FROM marketing_channels WHERE status = 'Active'").fetchall()
    salespersons = db.execute("SELECT id, username FROM users ORDER BY username").fetchall()
    leads = db.execute("SELECT id, lead_name FROM marketing_leads ORDER BY lead_name").fetchall()
    
    if request.method == 'POST':
        offer_number = request.form.get('offer_number', '').strip()
        if not offer_number:
            offer_number = f"OFF-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        cursor = db.execute("""
            INSERT INTO marketing_offers
            (offer_number, offer_date, target_customer, customer_type,
             products_included, brands_included, discount_percentage, validity_period,
             responsible_salesperson_id, offer_result, linked_campaign_id,
             linked_channel_id, linked_lead_id, status, notes, created_by_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            offer_number,
            request.form.get('offer_date', ''),
            request.form.get('target_customer', ''),
            request.form.get('customer_type', ''),
            request.form.get('products_included', ''),
            request.form.get('brands_included', ''),
            request.form.get('discount_percentage', 0),
            request.form.get('validity_period', ''),
            request.form.get('responsible_salesperson_id'),
            request.form.get('offer_result', ''),
            request.form.get('linked_campaign_id'),
            request.form.get('linked_channel_id'),
            request.form.get('linked_lead_id'),
            request.form.get('status', 'Sent'),
            request.form.get('notes', ''),
            user['id']
        ))
        db.commit()
        
        flash(f'Offer "{offer_number}" created successfully.', 'success')
        return redirect(url_for('marketing.offers_list'))
    
    db.close()
    return render_template('marketing/offer_edit.html', title='New Offer', offer=None,
                          campaigns=[dict(r) for r in campaigns],
                          channels=[dict(r) for r in channels],
                          salespersons=[dict(r) for r in salespersons],
                          leads=[dict(r) for r in leads])


@mkt_bp.route('/offers/edit/<int:id>', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_offers')
def offers_edit(id):
    """Edit offer."""
    db = get_db()
    user = get_current_user()
    
    offer = db.execute("SELECT * FROM marketing_offers WHERE id = ?", (id,)).fetchone()
    if not offer:
        flash('Offer not found.', 'error')
        return redirect(url_for('marketing.offers_list'))
    
    campaigns = db.execute("SELECT id, name FROM marketing_campaigns WHERE status IN ('Active', 'Draft')").fetchall()
    channels = db.execute("SELECT id, name FROM marketing_channels WHERE status = 'Active'").fetchall()
    salespersons = db.execute("SELECT id, username FROM users ORDER BY username").fetchall()
    leads = db.execute("SELECT id, lead_name FROM marketing_leads ORDER BY lead_name").fetchall()
    
    if request.method == 'POST':
        db.execute("""
            UPDATE marketing_offers SET
                offer_number = ?, offer_date = ?, target_customer = ?, customer_type = ?,
                products_included = ?, brands_included = ?, discount_percentage = ?,
                validity_period = ?, responsible_salesperson_id = ?, offer_result = ?,
                linked_campaign_id = ?, linked_channel_id = ?, linked_lead_id = ?,
                is_opened = ?, status = ?, notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            request.form.get('offer_number', ''),
            request.form.get('offer_date', ''),
            request.form.get('target_customer', ''),
            request.form.get('customer_type', ''),
            request.form.get('products_included', ''),
            request.form.get('brands_included', ''),
            request.form.get('discount_percentage', 0),
            request.form.get('validity_period', ''),
            request.form.get('responsible_salesperson_id'),
            request.form.get('offer_result', ''),
            request.form.get('linked_campaign_id'),
            request.form.get('linked_channel_id'),
            request.form.get('linked_lead_id'),
            1 if request.form.get('is_opened') else 0,
            request.form.get('status', 'Sent'),
            request.form.get('notes', ''),
            id
        ))
        db.commit()
        
        flash('Offer updated successfully.', 'success')
        return redirect(url_for('marketing.offers_list'))
    
    db.close()
    return render_template('marketing/offer_edit.html', title=f'Edit: {offer["offer_number"]}', offer=dict(offer),
                          campaigns=[dict(r) for r in campaigns],
                          channels=[dict(r) for r in channels],
                          salespersons=[dict(r) for r in salespersons],
                          leads=[dict(r) for r in leads])


# =============================================================================
# BUDGETS & COSTS
# =============================================================================

@mkt_bp.route('/budgets')
@mkt_login_required
@mkt_permission_required('view_budgets')
def budgets_list():
    """List marketing budgets."""
    db = get_db()
    
    budgets = db.execute("""
        SELECT b.*, u.username as approved_by_name,
               cr.username as created_by_name
        FROM marketing_budgets b
        LEFT JOIN users u ON b.approved_by_user_id = u.id
        LEFT JOIN users cr ON b.created_by_user_id = cr.id
        ORDER BY b.period_start DESC
    """).fetchall()
    
    db.close()
    
    return render_template('marketing/budgets.html',
        title='Marketing Budgets',
        budgets=[dict(r) for r in budgets],
    )


@mkt_bp.route('/budgets/new', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_budgets')
def budgets_new():
    """Create new budget."""
    db = get_db()
    user = get_current_user()
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Budget name is required.', 'error')
            return render_template('marketing/budget_edit.html', title='New Budget', budget=None)
        
        cursor = db.execute("""
            INSERT INTO marketing_budgets
            (name, budget_type, period_type, period_start, period_end,
             total_budget, branding_budget, digital_budget, print_budget,
             exhibition_budget, content_budget, status, notes, created_by_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            request.form.get('budget_type', ''),
            request.form.get('period_type', ''),
            request.form.get('period_start', ''),
            request.form.get('period_end', ''),
            request.form.get('total_budget', 0),
            request.form.get('branding_budget', 0),
            request.form.get('digital_budget', 0),
            request.form.get('print_budget', 0),
            request.form.get('exhibition_budget', 0),
            request.form.get('content_budget', 0),
            request.form.get('status', 'Draft'),
            request.form.get('notes', ''),
            user['id']
        ))
        db.commit()
        
        flash(f'Budget "{name}" created successfully.', 'success')
        return redirect(url_for('marketing.budgets_list'))
    
    db.close()
    return render_template('marketing/budget_edit.html', title='New Budget', budget=None)


@mkt_bp.route('/costs')
@mkt_login_required
@mkt_permission_required('view_budgets')
def costs_list():
    """List marketing costs."""
    db = get_db()
    
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    search = request.args.get('search', '')
    cost_type = request.args.get('cost_type', '')
    
    query = """
        SELECT mc.*, u.username as approved_by_name,
               c.name as campaign_name,
               ch.name as channel_name
        FROM marketing_costs mc
        LEFT JOIN users u ON mc.approved_by_user_id = u.id
        LEFT JOIN marketing_campaigns c ON mc.linked_campaign_id = c.id
        LEFT JOIN marketing_channels ch ON mc.linked_channel_id = ch.id
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) as cnt FROM marketing_costs WHERE 1=1"
    params = []
    count_params = []
    
    if search:
        query += " AND (mc.description LIKE ? OR mc.vendor_name LIKE ?)"
        count_query += " AND (description LIKE ? OR vendor_name LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
        count_params.extend([search_term, search_term])
    
    if cost_type:
        query += " AND mc.cost_type = ?"
        count_query += " AND mc.cost_type = ?"
        params.append(cost_type)
        count_params.append(cost_type)
    
    total = db.execute(count_query, count_params).fetchone()['cnt']
    query += " ORDER BY mc.cost_date DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    costs = db.execute(query, params).fetchall()
    
    db.close()
    
    return render_template('marketing/costs.html',
        title='Marketing Costs',
        costs=[dict(r) for r in costs],
        page=page, per_page=per_page, total=total,
        search=search, cost_type=cost_type,
    )


@mkt_bp.route('/costs/new', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_costs')
def costs_new():
    """Create new cost entry."""
    db = get_db()
    user = get_current_user()
    
    campaigns = db.execute("SELECT id, name FROM marketing_campaigns").fetchall()
    channels = db.execute("SELECT id, name FROM marketing_channels WHERE status = 'Active'").fetchall()
    brands = db.execute("SELECT id, name FROM marketing_brands WHERE status = 'Active'").fetchall()
    
    if request.method == 'POST':
        cursor = db.execute("""
            INSERT INTO marketing_costs
            (cost_date, cost_type, description, amount, currency,
             linked_campaign_id, linked_channel_id, linked_brand_id,
             linked_market, invoice_reference, vendor_name,
             status, notes, created_by_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form.get('cost_date', ''),
            request.form.get('cost_type', ''),
            request.form.get('description', ''),
            request.form.get('amount', 0),
            request.form.get('currency', 'AED'),
            request.form.get('linked_campaign_id'),
            request.form.get('linked_channel_id'),
            request.form.get('linked_brand_id'),
            request.form.get('linked_market', ''),
            request.form.get('invoice_reference', ''),
            request.form.get('vendor_name', ''),
            request.form.get('status', 'Pending'),
            request.form.get('notes', ''),
            user['id']
        ))
        db.commit()
        
        flash('Cost entry created successfully.', 'success')
        return redirect(url_for('marketing.costs_list'))
    
    db.close()
    return render_template('marketing/cost_edit.html', title='New Cost Entry', cost=None,
                          campaigns=[dict(r) for r in campaigns],
                          channels=[dict(r) for r in channels],
                          brands=[dict(r) for r in brands])


# =============================================================================
# PERFORMANCE ANALYTICS
# =============================================================================

@mkt_bp.route('/analytics')
@mkt_login_required
@mkt_permission_required('view_reports')
def analytics():
    """Marketing performance analytics."""
    db = get_db()
    
    # Get date range
    date_from = request.args.get('date_from', (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
    
    # Campaign performance
    campaign_perf = db.execute("""
        SELECT 
            id, name, campaign_type, status,
            budget, actual_cost,
            leads_generated, inquiries_generated, quotations_generated,
            purchases_generated, sales_generated, profit_generated,
            new_customers_acquired, reactivated_customers,
            CASE WHEN actual_cost > 0 THEN ROUND((sales_generated - actual_cost) / actual_cost * 100, 2) ELSE 0 END as roi,
            CASE WHEN leads_generated > 0 THEN ROUND(actual_cost / leads_generated, 2) ELSE 0 END as cpl,
            CASE WHEN purchases_generated > 0 THEN ROUND(actual_cost / purchases_generated, 2) ELSE 0 END as cpa
        FROM marketing_campaigns
        WHERE start_date BETWEEN ? AND ? OR end_date BETWEEN ? AND ?
        ORDER BY roi DESC
    """, (date_from, date_to, date_from, date_to)).fetchall()
    
    # Channel performance
    channel_perf = get_channel_performance(db, date_from=date_from, date_to=date_to)
    
    # Lead source performance
    source_perf = db.execute("""
        SELECT 
            ls.id, ls.name as source_name, ls.source_type,
            COUNT(l.id) as leads_count,
            SUM(CASE WHEN l.lead_status = 'Converted to Customer' THEN 1 ELSE 0 END) as conversions,
            AVG(l.conversion_probability) as avg_conversion_prob,
            SUM(l.estimated_value) as total_estimated_value
        FROM marketing_lead_sources ls
        LEFT JOIN marketing_leads l ON ls.id = l.source_id
            AND (l.created_at BETWEEN ? AND ? OR l.created_at IS NULL)
        GROUP BY ls.id
        ORDER BY conversions DESC
    """, (date_from, date_to)).fetchall()
    
    # Content performance
    content_perf = db.execute("""
        SELECT 
            id, topic, content_format, channel_id,
            reach, impressions, clicks, ctr,
            engagement, shares, saves, comments,
            messages_generated, purchases_generated
        FROM marketing_content
        WHERE publish_date BETWEEN ? AND ?
        ORDER BY engagement DESC
    """, (date_from, date_to)).fetchall()
    
    # Monthly trend
    monthly_trend = db.execute("""
        SELECT 
            strftime('%Y-%m', start_date) as month,
            COUNT(*) as campaigns,
            SUM(budget) as total_budget,
            SUM(actual_cost) as total_spend,
            SUM(sales_generated) as total_sales
        FROM marketing_campaigns
        WHERE start_date IS NOT NULL
        GROUP BY strftime('%Y-%m', start_date)
        ORDER BY month DESC
        LIMIT 12
    """).fetchall()
    
    db.close()
    
    return render_template('marketing/analytics.html',
        title='Performance Analytics',
        date_from=date_from, date_to=date_to,
        campaign_perf=[dict(r) for r in campaign_perf],
        channel_perf=channel_perf,
        source_perf=[dict(r) for r in source_perf],
        content_perf=[dict(r) for r in content_perf],
        monthly_trend=[dict(r) for r in monthly_trend],
    )


# =============================================================================
# ALERTS & RECOMMENDATIONS
# =============================================================================

@mkt_bp.route('/alerts')
@mkt_login_required
@mkt_permission_required('view_alerts')
def alerts_list():
    """List marketing alerts."""
    db = get_db()
    
    alerts = db.execute("""
        SELECT a.*, c.name as campaign_name,
               ch.name as channel_name
        FROM marketing_alerts a
        LEFT JOIN marketing_campaigns c ON a.linked_campaign_id = c.id
        LEFT JOIN marketing_channels ch ON a.linked_channel_id = ch.id
        ORDER BY 
            CASE a.severity 
                WHEN 'Critical' THEN 1 
                WHEN 'High' THEN 2 
                WHEN 'Medium' THEN 3 
                ELSE 4 
            END,
            a.created_at DESC
        LIMIT 100
    """).fetchall()
    
    db.close()
    
    return render_template('marketing/alerts.html',
        title='Alerts',
        alerts=[dict(r) for r in alerts],
    )


@mkt_bp.route('/alerts/resolve/<int:id>', methods=['POST'])
@mkt_login_required
@mkt_permission_required('manage_alerts')
def alerts_resolve(id):
    """Resolve an alert."""
    db = get_db()
    user = get_current_user()
    
    alert = db.execute("SELECT * FROM marketing_alerts WHERE id = ?", (id,)).fetchone()
    if not alert:
        return jsonify({'success': False, 'message': 'Alert not found'}), 404
    
    db.execute("""
        UPDATE marketing_alerts SET
            is_resolved = 1,
            resolved_at = CURRENT_TIMESTAMP,
            resolved_by_user_id = ?,
            resolution_notes = ?
        WHERE id = ?
    """, (user['id'], request.form.get('resolution_notes', ''), id))
    db.commit()
    
    flash('Alert resolved successfully.', 'success')
    return redirect(url_for('marketing.alerts_list'))


@mkt_bp.route('/recommendations')
@mkt_login_required
def recommendations_list():
    """List recommendations."""
    db = get_db()
    
    recommendations = db.execute("""
        SELECT r.*, u.username as implemented_by_name
        FROM marketing_recommendations r
        LEFT JOIN users u ON r.implemented_by_user_id = u.id
        ORDER BY 
            CASE r.priority 
                WHEN 'High' THEN 1 
                WHEN 'Medium' THEN 2 
                ELSE 3 
            END,
            r.created_at DESC
        LIMIT 100
    """).fetchall()
    
    db.close()
    
    return render_template('marketing/recommendations.html',
        title='Recommendations',
        recommendations=[dict(r) for r in recommendations],
    )


@mkt_bp.route('/recommendations/implement/<int:id>', methods=['POST'])
@mkt_login_required
@mkt_permission_required('manage_recommendations')
def recommendations_implement(id):
    """Mark recommendation as implemented."""
    db = get_db()
    user = get_current_user()
    
    db.execute("""
        UPDATE marketing_recommendations SET
            status = 'Implemented',
            implemented_at = CURRENT_TIMESTAMP,
            implemented_by_user_id = ?
        WHERE id = ?
    """, (user['id'], id))
    db.commit()
    
    flash('Recommendation marked as implemented.', 'success')
    return redirect(url_for('marketing.recommendations_list'))


@mkt_bp.route('/insights/run', methods=['POST'])
@mkt_login_required
@mkt_permission_required('manage_alerts')
def run_insights():
    """Run the marketing insights engine to generate alerts and recommendations."""
    user = get_current_user()

    result = run_marketing_insights(user['id'])

    flash(f'Insights generated: {result["alerts_created"]} alerts, {result["recommendations_created"]} recommendations created.', 'success')
    return redirect(url_for('marketing.alerts_list'))


# =============================================================================
# REPORTS
# =============================================================================

@mkt_bp.route('/reports')
@mkt_login_required
@mkt_permission_required('view_reports')
def reports_menu():
    """Marketing reports menu."""
    return render_template('marketing/reports.html', title='Marketing Reports')


@mkt_bp.route('/reports/campaign-report')
@mkt_login_required
@mkt_permission_required('view_reports')
def campaign_report():
    """Campaign performance report."""
    db = get_db()
    
    date_from = request.args.get('date_from', (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
    campaign_type = request.args.get('campaign_type', '')
    status = request.args.get('status', '')
    
    query = """
        SELECT c.*, u.username as owner_name,
               b.name as brand_name,
               s.name as segment_name
        FROM marketing_campaigns c
        LEFT JOIN users u ON c.owner_user_id = u.id
        LEFT JOIN marketing_brands b ON c.target_brand_id = b.id
        LEFT JOIN marketing_customer_segments s ON c.target_segment_id = s.id
        WHERE 1=1
    """
    params = []
    
    if date_from:
        query += " AND c.start_date >= ?"
        params.append(date_from)
    
    if date_to:
        query += " AND c.end_date <= ?"
        params.append(date_to)
    
    if campaign_type:
        query += " AND c.campaign_type = ?"
        params.append(campaign_type)
    
    if status:
        query += " AND c.status = ?"
        params.append(status)
    
    query += " ORDER BY c.start_date DESC"
    
    campaigns = db.execute(query, params).fetchall()
    
    campaign_types = db.execute("""
        SELECT setting_value FROM marketing_settings 
        WHERE category = 'campaign_types' AND is_active = 1
    """).fetchall()
    
    db.close()
    
    return render_template('marketing/report_campaign.html',
        title='Campaign Report',
        campaigns=[dict(r) for r in campaigns],
        date_from=date_from, date_to=date_to,
        campaign_type=campaign_type, status=status,
        campaign_types=[r['setting_value'] for r in campaign_types],
    )


@mkt_bp.route('/reports/lead-report')
@mkt_login_required
@mkt_permission_required('view_reports')
def lead_report():
    """Lead report."""
    db = get_db()
    
    date_from = request.args.get('date_from', (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
    source_id = request.args.get('source_id', '')
    status = request.args.get('status', '')
    
    query = """
        SELECT l.*, ls.name as source_name,
               u.username as assigned_name,
               c.name as campaign_name
        FROM marketing_leads l
        LEFT JOIN marketing_lead_sources ls ON l.source_id = ls.id
        LEFT JOIN users u ON l.assigned_salesperson_id = u.id
        LEFT JOIN marketing_campaigns c ON l.related_campaign_id = c.id
        WHERE 1=1
    """
    params = []
    
    if date_from:
        query += " AND date(l.created_at) >= ?"
        params.append(date_from)
    
    if date_to:
        query += " AND date(l.created_at) <= ?"
        params.append(date_to)
    
    if source_id:
        query += " AND l.source_id = ?"
        params.append(source_id)
    
    if status:
        query += " AND l.lead_status = ?"
        params.append(status)
    
    query += " ORDER BY l.created_at DESC"
    
    leads = db.execute(query, params).fetchall()
    sources = db.execute("SELECT id, name FROM marketing_lead_sources WHERE status = 'Active'").fetchall()
    
    db.close()
    
    return render_template('marketing/report_lead.html',
        title='Lead Report',
        leads=[dict(r) for r in leads],
        date_from=date_from, date_to=date_to,
        source_id=source_id, status=status,
        sources=[dict(r) for r in sources],
    )


@mkt_bp.route('/reports/channel-report')
@mkt_login_required
@mkt_permission_required('view_reports')
def channel_report():
    """Channel performance report."""
    db = get_db()
    
    channel_perf = get_channel_performance(db)
    
    db.close()
    
    return render_template('marketing/report_channel.html',
        title='Channel Report',
        channel_perf=channel_perf,
    )


@mkt_bp.route('/reports/export/<report_type>')
@mkt_login_required
def reports_export(report_type):
    """Export report data."""
    db = get_db()
    
    if report_type == 'campaigns':
        data = db.execute("""
            SELECT c.*, u.username as owner_name, b.name as brand_name
            FROM marketing_campaigns c
            LEFT JOIN users u ON c.owner_user_id = u.id
            LEFT JOIN marketing_brands b ON c.target_brand_id = b.id
            ORDER BY c.start_date DESC
        """).fetchall()
        filename = 'campaigns_report.csv'
        columns = ['id', 'name', 'code', 'campaign_type', 'status', 'start_date', 'end_date',
                   'budget', 'actual_cost', 'leads_generated', 'inquiries_generated',
                   'purchases_generated', 'sales_generated', 'roi', 'owner_name', 'brand_name']
    
    elif report_type == 'leads':
        data = db.execute("""
            SELECT l.*, ls.name as source_name, u.username as assigned_name
            FROM marketing_leads l
            LEFT JOIN marketing_lead_sources ls ON l.source_id = ls.id
            LEFT JOIN users u ON l.assigned_salesperson_id = u.id
            ORDER BY l.created_at DESC
        """).fetchall()
        filename = 'leads_report.csv'
        columns = ['id', 'lead_name', 'phone', 'email', 'source_name', 'lead_status',
                   'importance_level', 'estimated_value', 'conversion_probability',
                   'assigned_name', 'created_at']
    
    elif report_type == 'channel':
        data = get_channel_performance(db)
        filename = 'channel_report.csv'
        columns = ['name', 'channel_type', 'budget', 'actual_spend', 'leads_generated',
                   'inquiries_generated', 'sales_generated', 'cost_per_lead']
        data = [type('obj', (object,), d) for d in data]
    
    else:
        flash('Unknown report type.', 'error')
        return redirect(url_for('marketing.reports_menu'))
    
    db.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(columns)
    
    for row in data:
        if isinstance(row, dict):
            writer.writerow([row.get(col, '') for col in columns])
        else:
            writer.writerow([getattr(row, col, '') for col in columns])
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


# =============================================================================
# MARKETING ROLES & PERMISSIONS MANAGEMENT
# =============================================================================

@mkt_bp.route('/roles')
@mkt_login_required
@mkt_permission_required('manage_settings')
def roles_list():
    """List marketing roles."""
    db = get_db()
    roles = db.execute("SELECT * FROM marketing_roles ORDER BY role_name").fetchall()

    # Get user count for each role
    roles_data = []
    for role in roles:
        role_dict = dict(role)
        user_count = db.execute(
            "SELECT COUNT(*) as cnt FROM marketing_user_roles WHERE marketing_role_id = ? AND is_active = 1",
            (role['id'],)
        ).fetchone()['cnt']
        role_dict['user_count'] = user_count
        roles_data.append(role_dict)

    db.close()

    return render_template('marketing/roles/list.html',
        title='Marketing Roles',
        roles=roles_data,
    )


@mkt_bp.route('/roles/new', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_settings')
def roles_new():
    """Create new marketing role."""
    db = get_db()
    user = get_current_user()

    if request.method == 'POST':
        role_name = request.form.get('role_name', '').strip()
        role_code = request.form.get('role_code', '').strip()
        description = request.form.get('description', '').strip()
        can_view_financials = 1 if request.form.get('can_view_financials') else 0
        can_approve = 1 if request.form.get('can_approve') else 0
        can_publish = 1 if request.form.get('can_publish') else 0
        can_manage_team = 1 if request.form.get('can_manage_team') else 0
        can_view_all_data = 1 if request.form.get('can_view_all_data') else 0

        # Get selected permissions
        selected_permissions = request.form.getlist('permissions')

        if not role_name or not role_code:
            flash('Role name and code are required.', 'error')
        else:
            try:
                db.execute("""
                    INSERT INTO marketing_roles
                    (role_name, role_code, description, is_system_role, permissions_json,
                     can_view_financials, can_approve, can_publish, can_manage_team, can_view_all_data,
                     created_by_user_id)
                    VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    role_name, role_code, description,
                    json.dumps(selected_permissions),
                    can_view_financials, can_approve, can_publish, can_manage_team, can_view_all_data,
                    user['id']
                ))
                db.commit()
                flash('Marketing role created successfully.', 'success')
                return redirect(url_for('marketing.roles_list'))
            except sqlite3.IntegrityError:
                flash('Role code already exists.', 'error')

    db.close()
    return render_template('marketing/roles/new.html',
        title='New Marketing Role',
        permissions=MARKETING_DEFAULT_PERMISSIONS,
    )


@mkt_bp.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_settings')
def roles_edit(role_id):
    """Edit marketing role."""
    db = get_db()
    user = get_current_user()

    role = db.execute("SELECT * FROM marketing_roles WHERE id = ?", (role_id,)).fetchone()
    if not role:
        db.close()
        flash('Role not found.', 'error')
        return redirect(url_for('marketing.roles_list'))

    if request.method == 'POST':
        role_name = request.form.get('role_name', '').strip()
        description = request.form.get('description', '').strip()
        can_view_financials = 1 if request.form.get('can_view_financials') else 0
        can_approve = 1 if request.form.get('can_approve') else 0
        can_publish = 1 if request.form.get('can_publish') else 0
        can_manage_team = 1 if request.form.get('can_manage_team') else 0
        can_view_all_data = 1 if request.form.get('can_view_all_data') else 0
        selected_permissions = request.form.getlist('permissions')

        if not role_name:
            flash('Role name is required.', 'error')
        else:
            db.execute("""
                UPDATE marketing_roles
                SET role_name = ?, description = ?, permissions_json = ?,
                    can_view_financials = ?, can_approve = ?, can_publish = ?,
                    can_manage_team = ?, can_view_all_data = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                role_name, description, json.dumps(selected_permissions),
                can_view_financials, can_approve, can_publish, can_manage_team, can_view_all_data,
                role_id
            ))
            db.commit()
            flash('Role updated successfully.', 'success')
            return redirect(url_for('marketing.roles_list'))

    db.close()
    current_perms = json.loads(role['permissions_json']) if role['permissions_json'] else []
    return render_template('marketing/roles/edit.html',
        title='Edit Marketing Role',
        role=dict(role),
        current_permissions=current_perms,
        permissions=MARKETING_DEFAULT_PERMISSIONS,
    )


@mkt_bp.route('/roles/<int:role_id>/delete', methods=['POST'])
@mkt_login_required
@mkt_permission_required('manage_settings')
def roles_delete(role_id):
    """Delete marketing role."""
    db = get_db()

    role = db.execute("SELECT * FROM marketing_roles WHERE id = ?", (role_id,)).fetchone()
    if not role:
        db.close()
        flash('Role not found.', 'error')
        return redirect(url_for('marketing.roles_list'))

    if role['is_system_role']:
        db.close()
        flash('Cannot delete system role.', 'error')
        return redirect(url_for('marketing.roles_list'))

    # Check if role has users assigned
    user_count = db.execute(
        "SELECT COUNT(*) as cnt FROM marketing_user_roles WHERE marketing_role_id = ? AND is_active = 1",
        (role_id,)
    ).fetchone()['cnt']

    if user_count > 0:
        db.close()
        flash(f'Cannot delete role with {user_count} assigned users. Remove assignments first.', 'error')
        return redirect(url_for('marketing.roles_list'))

    db.execute("DELETE FROM marketing_roles WHERE id = ?", (role_id,))
    db.commit()
    db.close()

    flash('Role deleted successfully.', 'success')
    return redirect(url_for('marketing.roles_list'))


@mkt_bp.route('/roles/assign', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_settings')
def roles_assign():
    """Assign marketing role to users."""
    db = get_db()
    user = get_current_user()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'assign':
            user_id = request.form.get('user_id')
            role_id = request.form.get('role_id')

            if not user_id or not role_id:
                flash('User and role are required.', 'error')
            else:
                # Check if assignment already exists
                existing = db.execute(
                    "SELECT id FROM marketing_user_roles WHERE user_id = ? AND marketing_role_id = ?",
                    (user_id, role_id)
                ).fetchone()

                if existing:
                    # Reactivate if exists but inactive
                    db.execute(
                        "UPDATE marketing_user_roles SET is_active = 1 WHERE id = ?",
                        (existing['id'],)
                    )
                    flash('Role assignment updated.', 'success')
                else:
                    db.execute("""
                        INSERT INTO marketing_user_roles (user_id, marketing_role_id, assigned_by_id)
                        VALUES (?, ?, ?)
                    """, (user_id, role_id, user['id']))
                    flash('Role assigned successfully.', 'success')

                db.commit()

        elif action == 'remove':
            assignment_id = request.form.get('assignment_id')
            db.execute(
                "UPDATE marketing_user_roles SET is_active = 0 WHERE id = ?",
                (assignment_id,)
            )
            db.commit()
            flash('Role assignment removed.', 'success')

    # Get active roles
    roles = db.execute("SELECT id, role_name FROM marketing_roles WHERE status = 'Active' ORDER BY role_name").fetchall()

    # Get all assignments with user and role details
    assignments = db.execute("""
        SELECT mur.id, mur.assigned_at,
               u.id as user_id, u.username, u.email,
               mr.id as role_id, mr.role_name
        FROM marketing_user_roles mur
        JOIN users u ON mur.user_id = u.id
        JOIN marketing_roles mr ON mur.marketing_role_id = mr.id
        WHERE mur.is_active = 1
        ORDER BY mur.assigned_at DESC
    """).fetchall()

    db.close()

    return render_template('marketing/roles/assign.html',
        title='Assign Marketing Roles',
        roles=[dict(r) for r in roles],
        assignments=[dict(a) for a in assignments],
    )


@mkt_bp.route('/roles/<int:role_id>/users')
@mkt_login_required
@mkt_permission_required('manage_settings')
def roles_users(role_id):
    """View users in a marketing role."""
    db = get_db()

    role = db.execute("SELECT * FROM marketing_roles WHERE id = ?", (role_id,)).fetchone()
    if not role:
        db.close()
        flash('Role not found.', 'error')
        return redirect(url_for('marketing.roles_list'))

    users = get_marketing_role_users(role_id)

    db.close()

    return render_template('marketing/roles/role_users.html',
        title=f'Users in {role["role_name"]}',
        role=dict(role),
        users=users,
    )


# =============================================================================
# SETTINGS
# =============================================================================

@mkt_bp.route('/settings')
@mkt_login_required
@mkt_permission_required('manage_settings')
def settings():
    """Marketing settings."""
    db = get_db()
    
    # Get all settings grouped by category
    settings_data = {}
    rows = db.execute("""
        SELECT setting_key, setting_value, setting_type, category, description, is_active
        FROM marketing_settings
        ORDER BY category, setting_key
    """).fetchall()
    
    for row in rows:
        cat = row['category']
        if cat not in settings_data:
            settings_data[cat] = []
        settings_data[cat].append(dict(row))
    
    db.close()
    
    return render_template('marketing/settings.html',
        title='Marketing Settings',
        settings_data=settings_data,
    )


@mkt_bp.route('/settings/update', methods=['POST'])
@mkt_login_required
@mkt_permission_required('manage_settings')
def settings_update():
    """Update marketing settings."""
    db = get_db()
    user = get_current_user()
    
    for key, value in request.form.items():
        if key.startswith('setting_'):
            setting_key = key.replace('setting_', '')
            db.execute("""
                UPDATE marketing_settings 
                SET setting_value = ?, updated_by_user_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE setting_key = ?
            """, (value, user['id'], setting_key))
    
    db.commit()
    db.close()
    
    flash('Settings updated successfully.', 'success')
    return redirect(url_for('marketing.settings'))


# =============================================================================
# SEASONALITY
# =============================================================================

@mkt_bp.route('/seasonality')
@mkt_login_required
@mkt_permission_required('view_reports')
def seasonality():
    """Seasonality management."""
    db = get_db()
    
    seasons = db.execute("""
        SELECT * FROM marketing_seasonality
        ORDER BY start_month, start_day
    """).fetchall()
    
    db.close()
    
    return render_template('marketing/seasonality.html',
        title='Seasonality & Timing',
        seasons=[dict(r) for r in seasons],
    )


# =============================================================================
# CROSS-MODULE INTEGRATION ROUTES
# =============================================================================

@mkt_bp.route('/customer-insights/<int:customer_id>')
@mkt_login_required
@mkt_permission_required('view_leads')
def customer_insights(customer_id):
    """View customer insights linking marketing, sales, and inventory data."""
    db = get_db()

    # Get customer from CRM
    customer = db.execute("SELECT * FROM sdad_customers WHERE id = ?", (customer_id,)).fetchone()
    if not customer:
        db.close()
        flash('Customer not found.', 'error')
        return redirect(url_for('marketing.leads_list'))

    # Get related leads
    leads = db.execute("""
        SELECT * FROM marketing_leads
        WHERE phone LIKE ? OR email LIKE ?
        ORDER BY created_at DESC
    """, (f"%{customer['phone']}%", customer.get('email', ''))).fetchall()

    # Get purchase history
    purchases = db.execute("""
        SELECT * FROM sdad_sales_transactions
        WHERE customer_id = ?
        ORDER BY transaction_date DESC
        LIMIT 20
    """, (customer_id,)).fetchall()

    # Get related campaigns
    campaigns = db.execute("""
        SELECT DISTINCT c.* FROM marketing_campaigns c
        JOIN marketing_attribution ma ON c.id = ma.campaign_id
        WHERE ma.customer_id = ?
        ORDER BY c.start_date DESC
    """, (customer_id,)).fetchall()

    # Get inventory interests (based on purchased categories)
    inventory_interests = db.execute("""
        SELECT p.name, p.part_number, i.quantity_in_stock, b.name as brand
        FROM parts p
        LEFT JOIN inventory i ON p.id = i.part_id
        LEFT JOIN brands b ON p.brand_id = b.id
        LIMIT 10
    """).fetchall()

    db.close()

    return render_template('marketing/customer_insights.html',
        title=f'Customer Insights - {customer["name"]}',
        customer=dict(customer),
        leads=[dict(l) for l in leads],
        purchases=[dict(p) for p in purchases],
        campaigns=[dict(c) for c in campaigns],
        inventory_interests=[dict(i) for i in inventory_interests],
    )


@mkt_bp.route('/campaign-impact/<int:campaign_id>')
@mkt_login_required
@mkt_permission_required('view_campaigns')
def campaign_impact(campaign_id):
    """View the sales impact of a marketing campaign."""
    db = get_db()

    campaign = db.execute("SELECT * FROM marketing_campaigns WHERE id = ?", (campaign_id,)).fetchone()
    if not campaign:
        db.close()
        flash('Campaign not found.', 'error')
        return redirect(url_for('marketing.campaigns_list'))

    # Get attribution data
    attribution = db.execute("""
        SELECT ma.*, c.name as customer_name, c.phone, c.city
        FROM marketing_attribution ma
        LEFT JOIN sdad_customers c ON ma.customer_id = c.id
        WHERE ma.campaign_id = ?
        ORDER BY ma.attributed_at DESC
    """, (campaign_id,)).fetchall()

    # Get linked sales
    sales = db.execute("""
        SELECT st.*, c.name as customer_name
        FROM sdad_sales_transactions st
        LEFT JOIN sdad_customers c ON st.customer_id = c.id
        WHERE st.transaction_date BETWEEN ? AND ?
        ORDER BY st.transaction_date DESC
    """, (campaign['start_date'], campaign.get('end_date') or datetime.now().strftime('%Y-%m-%d'))).fetchall()

    db.close()

    return render_template('marketing/campaign_impact.html',
        title=f'Campaign Impact - {campaign["name"]}',
        campaign=dict(campaign),
        attribution=[dict(a) for a in attribution],
        sales=[dict(s) for s in sales],
    )


@mkt_bp.route('/api/customer-search')
@mkt_login_required
def api_customer_search():
    """API to search for customers in CRM to link with marketing leads."""
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])

    db = get_db()
    customers = db.execute("""
        SELECT id, name, phone, email, city, country, customer_type, total_sales
        FROM sdad_customers
        WHERE name LIKE ? OR phone LIKE ? OR email LIKE ?
        LIMIT 20
    """, (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
    db.close()

    return jsonify([dict(c) for c in customers])


@mkt_bp.route('/api/inventory-search')
@mkt_login_required
@mkt_permission_required('view_campaigns')
def api_inventory_search():
    """API to search inventory for marketing campaign planning."""
    query = request.args.get('q', '')
    brand_id = request.args.get('brand_id')
    category_id = request.args.get('category_id')

    db = get_db()
    sql = """
        SELECT p.id, p.part_number, p.name, b.name as brand_name,
               c.name as category_name, i.quantity_in_stock, i.location
        FROM parts p
        LEFT JOIN brands b ON p.brand_id = b.id
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN inventory i ON p.id = i.part_id
        WHERE (p.name LIKE ? OR p.part_number LIKE ?)
    """
    params = [f'%{query}%', f'%{query}%']

    if brand_id:
        sql += " AND b.id = ?"
        params.append(brand_id)

    if category_id:
        sql += " AND c.id = ?"
        params.append(category_id)

    sql += " LIMIT 50"

    parts = db.execute(sql, params).fetchall()
    db.close()

    return jsonify([dict(p) for p in parts])


@mkt_bp.route('/lead/<int:lead_id>/convert', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_leads')
def lead_convert(lead_id):
    """Convert a marketing lead to a CRM customer."""
    db = get_db()
    user = get_current_user()

    lead = db.execute("SELECT * FROM marketing_leads WHERE id = ?", (lead_id,)).fetchone()
    if not lead:
        db.close()
        flash('Lead not found.', 'error')
        return redirect(url_for('marketing.leads_list'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'link_existing':
            customer_id = request.form.get('customer_id')
            if customer_id:
                from marketing_models import link_lead_to_customer
                link_lead_to_customer(db, lead_id, customer_id, user['id'])
                flash('Lead linked to existing customer successfully.', 'success')
                return redirect(url_for('marketing.leads_list'))

        elif action == 'create_new':
            # Create new customer in CRM
            customer_name = request.form.get('customer_name')
            customer_phone = request.form.get('customer_phone')
            customer_email = request.form.get('customer_email')
            customer_city = request.form.get('customer_city')

            if not customer_name:
                flash('Customer name is required.', 'error')
            else:
                cursor = db.execute("""
                    INSERT INTO sdad_customers (name, phone, email, city, salesperson_name, created_at)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (customer_name, customer_phone, customer_email, customer_city, user.get('username', '')))
                customer_id = cursor.lastrowid

                from marketing_models import link_lead_to_customer
                link_lead_to_customer(db, lead_id, customer_id, user['id'])

                flash(f'Lead converted to new customer (ID: {customer_id}).', 'success')
                return redirect(url_for('marketing.leads_list'))

    db.close()
    return render_template('marketing/lead_convert.html',
        title=f'Convert Lead - {lead.get("name", "Unknown")}',
        lead=dict(lead),
    )


# =============================================================================
# API ENDPOINTS
# =============================================================================

@mkt_bp.route('/api/dashboard-stats')
@mkt_login_required
def api_dashboard_stats():
    """API endpoint for dashboard statistics."""
    db = get_db()
    
    date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
    
    dash_data = get_marketing_dashboard_data(db, date_from=date_from, date_to=date_to)
    
    db.close()
    
    return jsonify(dash_data)


@mkt_bp.route('/api/campaign/<int:id>/metrics')
@mkt_login_required
def api_campaign_metrics(id):
    """API endpoint for campaign metrics."""
    db = get_db()
    
    metrics = db.execute("""
        SELECT * FROM marketing_performance_metrics
        WHERE entity_type = 'campaign' AND entity_id = ?
        ORDER BY metric_date DESC
        LIMIT 50
    """, (id,)).fetchall()
    
    db.close()
    
    return jsonify([dict(r) for r in metrics])


@mkt_bp.route('/api/funnel-data')
@mkt_login_required
def api_funnel_data():
    """API endpoint for funnel visualization data."""
    db = get_db()
    
    funnel_stages = db.execute("""
        SELECT 
            fs.id, fs.name, fs.stage_order,
            COUNT(fr.id) as count,
            AVG(ROUND((julianday(COALESCE(fr.exiting_date, CURRENT_TIMESTAMP)) - julianday(fr.entering_date)) * 24)) as avg_hours
        FROM marketing_funnel_stages fs
        LEFT JOIN marketing_funnel_records fr ON fs.id = fr.stage_id
        WHERE fs.status = 'Active'
        GROUP BY fs.id
        ORDER BY fs.stage_order
    """).fetchall()
    
    db.close()
    
    return jsonify([dict(r) for r in funnel_stages])


# =============================================================================
# REGISTER ROUTES WITH APP
# =============================================================================

def register_marketing_routes(app):
    """Register marketing routes with the Flask app."""
    app.register_blueprint(mkt_bp)
