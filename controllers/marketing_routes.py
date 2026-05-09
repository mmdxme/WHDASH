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

# Import export utilities
from export_utils import (
    send_export_response,
    get_export_columns
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
    """Decorator to check marketing-specific permissions.

    Maps route permission names to module.resource.action format.

    SECURITY: Uses centralized permission system via user_has_permission().
    Do NOT use session-based permission lists - they can be manipulated.
    """
    # Map route permissions to (resource, action)
    # e.g., 'dashboard' -> ('dashboard', 'view'), 'view_brands' -> ('brands', 'view')
    def _parse_permission(perm):
        parts = perm.split('_', 1)
        if len(parts) == 1:
            return (perm, 'view')  # Default to 'view' action
        else:
            # e.g., 'view_brands' -> action='view', resource='brands'
            action = parts[0]  # 'view', 'manage', etc.
            resource = parts[1]  # 'brands', 'campaigns', etc.
            return (resource, action)

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'error')
                return redirect(url_for('login'))

            user_id = session['user_id']
            resource, action = _parse_permission(permission)

            # SECURITY: Global Admin bypass is handled internally via wildcard permissions
            # in user_has_permission(). Do NOT use session-based permission lists.
            # Use the centralized permission system for proper audit logging.
            if not user_has_permission(user_id, 'marketing', resource, action):
                flash('You do not have permission to access this Marketing module.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
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
    params = []

    count_query = "SELECT COUNT(*) as cnt FROM marketing_campaigns WHERE 1=1"
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
@mkt_bp.route('/reports/export/<report_type>/<export_format>')
@mkt_login_required
def reports_export(report_type, export_format='csv'):
    """Export report data in multiple formats."""
    # Reuse the api_marketing_export handler for all formats
    valid_formats = ['csv', 'excel_text', 'excel_general', 'json', 'xml', 'txt',
                     'pdf', 'docx', 'html', 'printable', 'barcode', 'api',
                     'email', 'zip', 'backup', 'sql_dump', 'dashboard',
                     'summary', 'detailed', 'audit_log']
    if export_format not in valid_formats:
        export_format = 'csv'
    return api_marketing_export(export_type=export_format, data_type=report_type)


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
        # Parse permissions_json for template use
        if role_dict.get('permissions_json'):
            try:
                role_dict['permissions'] = json.loads(role_dict['permissions_json'])
            except (json.JSONDecodeError, TypeError):
                role_dict['permissions'] = []
        else:
            role_dict['permissions'] = []
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
# LEAD SCORING
# =============================================================================

@mkt_bp.route('/lead-scoring')
@mkt_login_required
@mkt_permission_required('view_leads')
def lead_scoring_list():
    """List lead scoring rules."""
    db = get_db()

    rules = db.execute("""
        SELECT r.*, u.username as created_by_name
        FROM marketing_lead_scoring_rules r
        LEFT JOIN users u ON r.created_by_user_id = u.id
        WHERE r.is_active = 1
        ORDER BY r.priority DESC, r.category, r.rule_name
    """).fetchall()

    # Get lead score distribution
    score_distribution = db.execute("""
        SELECT
            CASE
                WHEN ls.total_score >= 80 THEN 'Hot (80+)'
                WHEN ls.total_score >= 50 THEN 'Warm (50-79)'
                WHEN ls.total_score >= 20 THEN 'Cool (20-49)'
                ELSE 'Cold (0-19)'
            END as score_grade,
            COUNT(*) as count
        FROM marketing_lead_scores ls
        GROUP BY score_grade
        ORDER BY count DESC
    """).fetchall()

    # Get MQL/SQL counts
    mql_count = db.execute("SELECT COUNT(*) as cnt FROM marketing_lead_scores WHERE is_mql = 1").fetchone()['cnt']
    sql_count = db.execute("SELECT COUNT(*) as cnt FROM marketing_lead_scores WHERE is_sql = 1").fetchone()['cnt']

    db.close()

    return render_template('marketing/lead_scoring.html',
        title='Lead Scoring',
        rules=[dict(r) for r in rules],
        score_distribution=[dict(r) for r in score_distribution],
        mql_count=mql_count,
        sql_count=sql_count,
    )


@mkt_bp.route('/lead-scoring/rules/new', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_leads')
def lead_scoring_rule_new():
    """Create new lead scoring rule."""
    db = get_db()
    user = get_current_user()

    if request.method == 'POST':
        rule_name = request.form.get('rule_name', '').strip()
        rule_code = request.form.get('rule_code', '').strip()
        rule_type = request.form.get('rule_type', '')
        category = request.form.get('category', '')
        attribute_field = request.form.get('attribute_field', '')
        operator = request.form.get('operator', '')
        attribute_value = request.form.get('attribute_value', '')
        score_change = request.form.get('score_change', 0)
        priority = request.form.get('priority', 0)
        description = request.form.get('description', '')

        if not rule_name or not rule_type or not category:
            flash('Rule name, type, and category are required.', 'error')
            return render_template('marketing/lead_scoring_rule_edit.html', title='New Scoring Rule', rule=None)

        if not rule_code:
            rule_code = f"RULE-{rule_name[:6].upper()}-{datetime.now().strftime('%H%M%S')}"

        cursor = db.execute("""
            INSERT INTO marketing_lead_scoring_rules
            (rule_name, rule_code, rule_type, category, attribute_field, operator, attribute_value, score_change, priority, description, created_by_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (rule_name, rule_code, rule_type, category, attribute_field, operator, attribute_value, score_change, priority, description, user['id']))
        db.commit()

        flash(f'Scoring rule "{rule_name}" created successfully.', 'success')
        return redirect(url_for('marketing.lead_scoring_list'))

    db.close()
    return render_template('marketing/lead_scoring_rule_edit.html', title='New Scoring Rule', rule=None)


@mkt_bp.route('/leads/scores')
@mkt_login_required
@mkt_permission_required('view_leads')
def leads_scores_list():
    """List all leads with their scores."""
    db = get_db()

    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page

    search = request.args.get('search', '')
    score_grade = request.args.get('score_grade', '')
    show_mql = request.args.get('mql', '')
    show_sql = request.args.get('sql', '')

    query = """
        SELECT l.*, ls.total_score, ls.demographic_score, ls.behavioral_score,
               ls.engagement_score, ls.score_grade, ls.is_mql, ls.is_sql,
               ls.last_calculated_at
        FROM marketing_leads l
        LEFT JOIN marketing_lead_scores ls ON l.id = ls.lead_id
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) as cnt FROM marketing_leads l LEFT JOIN marketing_lead_scores ls ON l.id = ls.lead_id WHERE 1=1"
    params = []
    count_params = []

    if search:
        query += " AND l.lead_name LIKE ?"
        count_query += " AND l.lead_name LIKE ?"
        params.append(f"%{search}%")
        count_params.append(f"%{search}%")

    if score_grade:
        grade_conditions = {
            'Hot': 'ls.total_score >= 80',
            'Warm': 'ls.total_score >= 50 AND ls.total_score < 80',
            'Cool': 'ls.total_score >= 20 AND ls.total_score < 50',
            'Cold': '(ls.total_score < 20 OR ls.total_score IS NULL)'
        }
        if score_grade in grade_conditions:
            query += f" AND ({grade_conditions[score_grade]})"
            count_query += f" AND ({grade_conditions[score_grade]})"

    if show_mql:
        query += " AND ls.is_mql = 1"
        count_query += " AND ls.is_mql = 1"

    if show_sql:
        query += " AND ls.is_sql = 1"
        count_query += " AND ls.is_sql = 1"

    total = db.execute(count_query, count_params).fetchone()['cnt']
    query += " ORDER BY ls.total_score DESC NULLS LAST LIMIT ? OFFSET ?"
    params.extend([per_page, offset])

    leads = db.execute(query, params).fetchall()
    db.close()

    return render_template('marketing/leads_scores.html',
        title='Lead Scores',
        leads=[dict(r) for r in leads],
        page=page, per_page=per_page, total=total,
        search=search, score_grade=score_grade, show_mql=show_mql, show_sql=show_sql,
    )


@mkt_bp.route('/leads/scores/<int:lead_id>')
@mkt_login_required
@mkt_permission_required('view_leads')
def lead_score_detail(lead_id):
    """View detailed lead score breakdown."""
    db = get_db()

    lead = db.execute("SELECT * FROM marketing_leads WHERE id = ?", (lead_id,)).fetchone()
    if not lead:
        flash('Lead not found.', 'error')
        return redirect(url_for('marketing.leads_scores_list'))

    score = db.execute("SELECT * FROM marketing_lead_scores WHERE lead_id = ?", (lead_id,)).fetchone()
    score_history = db.execute("""
        SELECT h.*, r.rule_name
        FROM marketing_lead_score_history h
        LEFT JOIN marketing_lead_scoring_rules r ON h.triggered_by_rule_id = r.id
        WHERE h.lead_id = ?
        ORDER BY h.created_at DESC
        LIMIT 20
    """, (lead_id,)).fetchall()

    # Get applicable rules
    applicable_rules = db.execute("""
        SELECT * FROM marketing_lead_scoring_rules
        WHERE is_active = 1
        ORDER BY category, priority DESC
    """).fetchall()

    db.close()

    return render_template('marketing/lead_score_detail.html',
        title=f'Lead Score: {lead["lead_name"]}',
        lead=dict(lead),
        score=dict(score) if score else None,
        score_history=[dict(r) for r in score_history],
        applicable_rules=[dict(r) for r in applicable_rules],
    )


@mkt_bp.route('/api/leads/<int:lead_id>/calculate-score', methods=['POST'])
@mkt_login_required
@mkt_permission_required('manage_leads')
def api_calculate_lead_score(lead_id):
    """API to calculate lead score based on rules."""
    db = get_db()

    lead = db.execute("SELECT * FROM marketing_leads WHERE id = ?", (lead_id,)).fetchone()
    if not lead:
        db.close()
        return jsonify({'success': False, 'message': 'Lead not found'}), 404

    # Get all active rules
    rules = db.execute("SELECT * FROM marketing_lead_scoring_rules WHERE is_active = 1").fetchall()

    demographic_score = 0
    behavioral_score = 0
    engagement_score = 0
    breakdown = []

    for rule in rules:
        matches = False
        field = rule['attribute_field']
        operator = rule['operator']
        value = rule['attribute_value']

        # Check if lead matches rule criteria
        lead_value = lead.get(field) if lead else None

        if operator == 'equals' and str(lead_value).lower() == str(value).lower():
            matches = True
        elif operator == 'contains' and lead_value and str(value).lower() in str(lead_value).lower():
            matches = True
        elif operator == 'greater_than' and lead_value and float(lead_value) > float(value):
            matches = True
        elif operator == 'less_than' and lead_value and float(lead_value) < float(value):
            matches = True

        if matches:
            if rule['category'] == 'demographic':
                demographic_score += rule['score_change']
            elif rule['category'] == 'behavioral':
                behavioral_score += rule['score_change']
            elif rule['category'] == 'engagement':
                engagement_score += rule['score_change']

            breakdown.append({
                'rule_name': rule['rule_name'],
                'category': rule['category'],
                'score_change': rule['score_change'],
            })

    total_score = demographic_score + behavioral_score + engagement_score

    # Determine grade
    if total_score >= 80:
        grade = 'Hot'
    elif total_score >= 50:
        grade = 'Warm'
    elif total_score >= 20:
        grade = 'Cool'
    else:
        grade = 'Cold'

    is_mql = 1 if total_score >= 50 else 0
    is_sql = 1 if total_score >= 80 else 0

    # Update or create score record
    existing = db.execute("SELECT id FROM marketing_lead_scores WHERE lead_id = ?", (lead_id,)).fetchone()
    if existing:
        db.execute("""
            UPDATE marketing_lead_scores SET
                total_score = ?, demographic_score = ?, behavioral_score = ?,
                engagement_score = ?, score_grade = ?, is_mql = ?, is_sql = ?,
                last_calculated_at = CURRENT_TIMESTAMP,
                score_breakdown = ?
            WHERE lead_id = ?
        """, (total_score, demographic_score, behavioral_score, engagement_score, grade, is_mql, is_sql, json.dumps(breakdown), lead_id))
    else:
        db.execute("""
            INSERT INTO marketing_lead_scores
            (lead_id, total_score, demographic_score, behavioral_score, engagement_score, score_grade, is_mql, is_sql, last_calculated_at, score_breakdown)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (lead_id, total_score, demographic_score, behavioral_score, engagement_score, grade, is_mql, is_sql, json.dumps(breakdown)))

    db.commit()
    db.close()

    return jsonify({
        'success': True,
        'total_score': total_score,
        'demographic_score': demographic_score,
        'behavioral_score': behavioral_score,
        'engagement_score': engagement_score,
        'grade': grade,
        'is_mql': bool(is_mql),
        'is_sql': bool(is_sql),
        'breakdown': breakdown,
    })


# =============================================================================
# JOURNEY BUILDER / NURTURE JOURNEYS
# =============================================================================

@mkt_bp.route('/journeys')
@mkt_login_required
@mkt_permission_required('view_campaigns')
def journeys_list():
    """List nurture journeys."""
    db = get_db()

    journeys = db.execute("""
        SELECT j.*, s.name as segment_name, u.username as created_by_name
        FROM marketing_nurture_journeys j
        LEFT JOIN marketing_customer_segments s ON j.target_segment_id = s.id
        LEFT JOIN users u ON j.created_by_user_id = u.id
        ORDER BY j.created_at DESC
    """).fetchall()

    db.close()

    return render_template('marketing/journeys.html',
        title='Journey Builder',
        journeys=[dict(r) for r in journeys],
    )


@mkt_bp.route('/journeys/new', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_campaigns')
def journey_new():
    """Create new nurture journey."""
    db = get_db()
    user = get_current_user()

    segments = db.execute("SELECT id, name FROM marketing_customer_segments WHERE status = 'Active' ORDER BY name").fetchall()
    templates = db.execute("SELECT id, template_name, channel FROM marketing_templates WHERE is_active = 1 ORDER BY template_name").fetchall()

    if request.method == 'POST':
        journey_name = request.form.get('journey_name', '').strip()
        journey_code = request.form.get('journey_code', '').strip()
        journey_type = request.form.get('journey_type', '')
        description = request.form.get('description', '')
        objective = request.form.get('objective', '')
        target_segment_id = request.form.get('target_segment_id')
        entry_trigger_type = request.form.get('entry_trigger_type', '')
        status = request.form.get('status', 'Draft')

        if not journey_name or not journey_type:
            flash('Journey name and type are required.', 'error')
            return render_template('marketing/journey_edit.html', title='New Journey',
                                  journey=None, segments=[dict(r) for r in segments],
                                  templates=[dict(r) for r in templates])

        if not journey_code:
            journey_code = f"JRN-{journey_name[:6].upper()}-{datetime.now().strftime('%H%M%S')}"

        cursor = db.execute("""
            INSERT INTO marketing_nurture_journeys
            (journey_name, journey_code, journey_type, description, objective, target_segment_id,
             entry_trigger_type, status, created_by_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (journey_name, journey_code, journey_type, description, objective, target_segment_id, entry_trigger_type, status, user['id']))
        db.commit()
        journey_id = cursor.lastrowid

        flash(f'Journey "{journey_name}" created successfully.', 'success')
        return redirect(url_for('marketing.journey_edit', id=journey_id))

    db.close()
    return render_template('marketing/journey_edit.html', title='New Journey',
                          journey=None, segments=[dict(r) for r in segments],
                          templates=[dict(r) for r in templates])


@mkt_bp.route('/journeys/edit/<int:id>', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_campaigns')
def journey_edit(id):
    """Edit nurture journey and its steps."""
    db = get_db()
    user = get_current_user()

    journey = db.execute("SELECT * FROM marketing_nurture_journeys WHERE id = ?", (id,)).fetchone()
    if not journey:
        flash('Journey not found.', 'error')
        return redirect(url_for('marketing.journeys_list'))

    segments = db.execute("SELECT id, name FROM marketing_customer_segments WHERE status = 'Active' ORDER BY name").fetchall()
    templates = db.execute("SELECT id, template_name, channel FROM marketing_templates WHERE is_active = 1 ORDER BY template_name").fetchall()
    steps = db.execute("SELECT * FROM marketing_journey_steps WHERE journey_id = ? ORDER BY step_order", (id,)).fetchall()

    if request.method == 'POST':
        journey_name = request.form.get('journey_name', '').strip()
        journey_type = request.form.get('journey_type', '')
        description = request.form.get('description', '')
        objective = request.form.get('objective', '')
        target_segment_id = request.form.get('target_segment_id')
        entry_trigger_type = request.form.get('entry_trigger_type', '')
        status = request.form.get('status', 'Draft')

        db.execute("""
            UPDATE marketing_nurture_journeys SET
                journey_name = ?, journey_type = ?, description = ?, objective = ?,
                target_segment_id = ?, entry_trigger_type = ?, status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (journey_name, journey_type, description, objective, target_segment_id, entry_trigger_type, status, id))
        db.commit()

        flash('Journey updated successfully.', 'success')
        return redirect(url_for('marketing.journey_edit', id=id))

    db.close()
    return render_template('marketing/journey_edit.html', title=f'Edit: {journey["journey_name"]}',
                          journey=dict(journey), segments=[dict(r) for r in segments],
                          templates=[dict(r) for r in templates], steps=[dict(r) for r in steps])


@mkt_bp.route('/journeys/<int:id>/steps/add', methods=['POST'])
@mkt_login_required
@mkt_permission_required('manage_campaigns')
def journey_step_add(id):
    """Add a step to a journey."""
    db = get_db()

    journey = db.execute("SELECT * FROM marketing_nurture_journeys WHERE id = ?", (id,)).fetchone()
    if not journey:
        db.close()
        return jsonify({'success': False, 'message': 'Journey not found'}), 404

    step_name = request.form.get('step_name', '').strip()
    step_type = request.form.get('step_type', '')
    delay_days = request.form.get('delay_days', 0)
    delay_hours = request.form.get('delay_hours', 0)

    # Get next step order
    max_order = db.execute("SELECT MAX(step_order) as max_order FROM marketing_journey_steps WHERE journey_id = ?", (id,)).fetchone()['max_order'] or 0
    step_order = max_order + 1

    cursor = db.execute("""
        INSERT INTO marketing_journey_steps (journey_id, step_order, step_name, step_type, delay_days, delay_hours)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (id, step_order, step_name, step_type, delay_days, delay_hours))
    db.commit()
    step_id = cursor.lastrowid
    db.close()

    return jsonify({'success': True, 'step_id': step_id, 'message': 'Step added successfully'})


@mkt_bp.route('/journeys/<int:id>/publish', methods=['POST'])
@mkt_login_required
@mkt_permission_required('manage_campaigns')
def journey_publish(id):
    """Publish a journey to activate it."""
    db = get_db()
    user = get_current_user()

    journey = db.execute("SELECT * FROM marketing_nurture_journeys WHERE id = ?", (id,)).fetchone()
    if not journey:
        db.close()
        return jsonify({'success': False, 'message': 'Journey not found'}), 404

    # Check if journey has at least one step
    steps_count = db.execute("SELECT COUNT(*) as cnt FROM marketing_journey_steps WHERE journey_id = ?", (id,)).fetchone()['cnt']
    if steps_count == 0:
        db.close()
        return jsonify({'success': False, 'message': 'Journey must have at least one step before publishing'}), 400

    db.execute("""
        UPDATE marketing_nurture_journeys SET
            is_active = 1, is_published = 1, published_at = CURRENT_TIMESTAMP,
            published_by_user_id = ?, status = 'Active', updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (user['id'], id))
    db.commit()
    db.close()

    return jsonify({'success': True, 'message': 'Journey published successfully'})


@mkt_bp.route('/journeys/participants/<int:journey_id>')
@mkt_login_required
@mkt_permission_required('view_campaigns')
def journey_participants(journey_id):
    """View journey participants."""
    db = get_db()

    journey = db.execute("SELECT * FROM marketing_nurture_journeys WHERE id = ?", (journey_id,)).fetchone()
    if not journey:
        flash('Journey not found.', 'error')
        return redirect(url_for('marketing.journeys_list'))

    participants = db.execute("""
        SELECT p.*, l.lead_name, l.phone, l.email, l.lead_status,
               s.step_name as current_step_name
        FROM marketing_journey_participants p
        JOIN marketing_leads l ON p.lead_id = l.id
        LEFT JOIN marketing_journey_steps s ON p.current_step_id = s.id
        WHERE p.journey_id = ?
        ORDER BY p.enrolled_at DESC
    """, (journey_id,)).fetchall()

    db.close()

    return render_template('marketing/journey_participants.html',
        title=f'Journey Participants: {journey["journey_name"]}',
        journey=dict(journey),
        participants=[dict(r) for r in participants],
    )


# =============================================================================
# A/B TESTING
# =============================================================================

@mkt_bp.route('/ab-tests')
@mkt_login_required
@mkt_permission_required('view_reports')
def ab_tests_list():
    """List A/B tests."""
    db = get_db()

    tests = db.execute("""
        SELECT t.*, c.name as campaign_name, s.name as segment_name, u.username as created_by_name
        FROM marketing_ab_tests t
        LEFT JOIN marketing_campaigns c ON t.campaign_id = c.id
        LEFT JOIN marketing_customer_segments s ON t.target_segment_id = s.id
        LEFT JOIN users u ON t.created_by_user_id = u.id
        ORDER BY t.created_at DESC
    """).fetchall()

    db.close()

    return render_template('marketing/ab_tests.html',
        title='A/B Testing',
        tests=[dict(r) for r in tests],
    )


@mkt_bp.route('/ab-tests/new', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_campaigns')
def ab_test_new():
    """Create new A/B test."""
    db = get_db()
    user = get_current_user()

    campaigns = db.execute("SELECT id, name FROM marketing_campaigns WHERE status IN ('Active', 'Draft') ORDER BY name").fetchall()
    segments = db.execute("SELECT id, name FROM marketing_customer_segments WHERE status = 'Active' ORDER BY name").fetchall()

    if request.method == 'POST':
        test_name = request.form.get('test_name', '').strip()
        test_code = request.form.get('test_code', '').strip()
        test_type = request.form.get('test_type', '')
        hypothesis = request.form.get('hypothesis', '')
        description = request.form.get('description', '')
        campaign_id = request.form.get('campaign_id')
        target_segment_id = request.form.get('target_segment_id')
        channel = request.form.get('channel', '')
        control_variant = request.form.get('control_variant', '')
        challenger_variant = request.form.get('challenger_variant', '')
        success_metric = request.form.get('success_metric', '')
        status = request.form.get('status', 'Draft')

        if not test_name or not test_type:
            flash('Test name and type are required.', 'error')
            return render_template('marketing/ab_test_edit.html', title='New A/B Test',
                                  test=None, campaigns=[dict(r) for r in campaigns],
                                  segments=[dict(r) for r in segments])

        if not test_code:
            test_code = f"AB-{test_name[:6].upper()}-{datetime.now().strftime('%H%M%S')}"

        cursor = db.execute("""
            INSERT INTO marketing_ab_tests
            (test_name, test_code, test_type, hypothesis, description, campaign_id, target_segment_id,
             channel, control_variant, challenger_variant, success_metric, status, created_by_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (test_name, test_code, test_type, hypothesis, description, campaign_id, target_segment_id,
              channel, control_variant, challenger_variant, success_metric, status, user['id']))
        db.commit()
        test_id = cursor.lastrowid

        # Create default variants
        db.execute("""
            INSERT INTO marketing_ab_test_variants (test_id, variant_name, variant_type)
            VALUES (?, ?, 'control')
        """, (test_id, control_variant or 'Control'))

        db.execute("""
            INSERT INTO marketing_ab_test_variants (test_id, variant_name, variant_type)
            VALUES (?, ?, 'challenger')
        """, (test_id, challenger_variant or 'Challenger'))
        db.commit()

        flash(f'A/B Test "{test_name}" created successfully.', 'success')
        return redirect(url_for('marketing.ab_tests_list'))

    db.close()
    return render_template('marketing/ab_test_edit.html', title='New A/B Test',
                          test=None, campaigns=[dict(r) for r in campaigns],
                          segments=[dict(r) for r in segments])


@mkt_bp.route('/ab-tests/<int:id>')
@mkt_login_required
@mkt_permission_required('view_reports')
def ab_test_detail(id):
    """View A/B test details and results."""
    db = get_db()

    test = db.execute("""
        SELECT t.*, c.name as campaign_name, s.name as segment_name
        FROM marketing_ab_tests t
        LEFT JOIN marketing_campaigns c ON t.campaign_id = c.id
        LEFT JOIN marketing_customer_segments s ON t.target_segment_id = s.id
        WHERE t.id = ?
    """, (id,)).fetchone()

    if not test:
        flash('A/B Test not found.', 'error')
        return redirect(url_for('marketing.ab_tests_list'))

    variants = db.execute("SELECT * FROM marketing_ab_test_variants WHERE test_id = ?", (id,)).fetchall()

    db.close()

    return render_template('marketing/ab_test_detail.html',
        title=f'A/B Test: {test["test_name"]}',
        test=dict(test),
        variants=[dict(r) for r in variants],
    )


# =============================================================================
# CUSTOMER JOURNEY INTELLIGENCE
# =============================================================================

@mkt_bp.route('/journey-intelligence')
@mkt_login_required
@mkt_permission_required('view_reports')
def journey_intelligence_list():
    """List customer journey intelligence records."""
    db = get_db()

    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page

    search = request.args.get('search', '')
    journey_stage = request.args.get('journey_stage', '')

    query = """
        SELECT ji.*, l.lead_name, c.name as customer_name,
               ch.name as channel_name, camp.name as campaign_name
        FROM marketing_journey_intelligence ji
        LEFT JOIN marketing_leads l ON ji.lead_id = l.id
        LEFT JOIN sdad_customers c ON ji.customer_id = c.id
        LEFT JOIN marketing_channels ch ON ji.channel_id = ch.id
        LEFT JOIN marketing_campaigns camp ON ji.campaign_id = camp.id
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) as cnt FROM marketing_journey_intelligence WHERE 1=1"
    params = []
    count_params = []

    if search:
        query += " AND (l.lead_name LIKE ? OR c.name LIKE ?)"
        count_query += " AND (l.lead_name LIKE ? OR c.name LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
        count_params.extend([search_term, search_term])

    if journey_stage:
        query += " AND ji.journey_stage = ?"
        count_query += " AND ji.journey_stage = ?"
        params.append(journey_stage)
        count_params.append(journey_stage)

    total = db.execute(count_query, count_params).fetchone()['cnt']
    query += " ORDER BY ji.touchpoint_date DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])

    records = db.execute(query, params).fetchall()
    db.close()

    return render_template('marketing/journey_intelligence.html',
        title='Customer Journey Intelligence',
        records=[dict(r) for r in records],
        page=page, per_page=per_page, total=total,
        search=search, journey_stage=journey_stage,
    )


@mkt_bp.route('/journey-intelligence/customer/<int:customer_id>')
@mkt_login_required
@mkt_permission_required('view_reports')
def customer_journey_timeline(customer_id):
    """View complete journey timeline for a customer."""
    db = get_db()

    customer = db.execute("SELECT * FROM sdad_customers WHERE id = ?", (customer_id,)).fetchone()
    if not customer:
        # Try lead
        customer = db.execute("SELECT *, NULL as name, NULL as phone FROM marketing_leads WHERE id = ?", (customer_id,)).fetchone()
        if not customer:
            flash('Customer not found.', 'error')
            return redirect(url_for('marketing.journey_intelligence_list'))

    # Get all touchpoints
    touchpoints = db.execute("""
        SELECT ji.*, ch.name as channel_name, camp.name as campaign_name,
               cont.topic as content_name
        FROM marketing_journey_intelligence ji
        LEFT JOIN marketing_channels ch ON ji.channel_id = ch.id
        LEFT JOIN marketing_campaigns camp ON ji.campaign_id = camp.id
        LEFT JOIN marketing_content cont ON ji.content_id = cont.id
        WHERE (ji.customer_id = ? OR ji.lead_id = ?)
        ORDER BY ji.touchpoint_date DESC
    """, (customer_id, customer_id)).fetchall()

    # Get lead if applicable
    lead = None
    if customer.get('lead_name'):
        lead = dict(customer)

    # Calculate engagement metrics
    total_touchpoints = len(touchpoints)
    conversion_points = sum(1 for t in touchpoints if t['is_conversion_point'])
    avg_days_in_stage = db.execute("""
        SELECT AVG(days_in_stage) as avg_days FROM marketing_journey_intelligence
        WHERE (customer_id = ? OR lead_id = ?) AND days_in_stage > 0
    """, (customer_id, customer_id)).fetchone()['avg_days'] or 0

    db.close()

    return render_template('marketing/customer_journey_timeline.html',
        title=f'Customer Journey: {customer.get("name") or customer.get("lead_name") or "Unknown"}',
        customer=dict(customer),
        lead=lead,
        touchpoints=[dict(t) for t in touchpoints],
        total_touchpoints=total_touchpoints,
        conversion_points=conversion_points,
        avg_days_in_stage=round(avg_days_in_stage, 1),
    )


# =============================================================================
# ROI & PERFORMANCE
# =============================================================================

@mkt_bp.route('/roi')
@mkt_login_required
@mkt_permission_required('view_reports')
def roi_overview():
    """Marketing ROI dashboard."""
    db = get_db()

    date_from = request.args.get('date_from', (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

    # Get campaign ROI data
    campaign_roi = db.execute("""
        SELECT c.id, c.name, c.campaign_type, c.budget, c.actual_cost,
               c.leads_generated, c.sales_generated, c.profit_generated,
               c.new_customers_acquired,
               CASE WHEN c.actual_cost > 0 THEN ROUND((c.sales_generated - c.actual_cost) / c.actual_cost * 100, 2) ELSE 0 END as roi_percentage,
               CASE WHEN c.leads_generated > 0 THEN ROUND(c.actual_cost / c.leads_generated, 2) ELSE 0 END as cost_per_lead,
               CASE WHEN c.new_customers_acquired > 0 THEN ROUND(c.actual_cost / c.new_customers_acquired, 2) ELSE 0 END as cost_per_acquisition
        FROM marketing_campaigns c
        WHERE c.actual_cost > 0
        ORDER BY roi_percentage DESC
    """).fetchall()

    # Calculate totals
    total_investment = sum(c['actual_cost'] or 0 for c in campaign_roi)
    total_revenue = sum(c['sales_generated'] or 0 for c in campaign_roi)
    total_profit = sum(c['profit_generated'] or 0 for c in campaign_roi)
    total_leads = sum(c['leads_generated'] or 0 for c in campaign_roi)
    total_customers = sum(c['new_customers_acquired'] or 0 for c in campaign_roi)

    overall_roi = round((total_profit / total_investment * 100), 2) if total_investment > 0 else 0
    overall_cpl = round(total_investment / total_leads, 2) if total_leads > 0 else 0
    overall_cpa = round(total_investment / total_customers, 2) if total_customers > 0 else 0

    # Channel ROI breakdown
    channel_roi = db.execute("""
        SELECT ch.name as channel_name, ch.channel_type,
               SUM(cc.actual_spend) as total_spend,
               SUM(cc.leads_generated) as leads,
               SUM(cc.sales_generated) as sales,
               CASE WHEN SUM(cc.actual_spend) > 0 THEN ROUND((SUM(cc.sales_generated) - SUM(cc.actual_spend)) / SUM(cc.actual_spend) * 100, 2) ELSE 0 END as roi
        FROM marketing_channels ch
        LEFT JOIN marketing_campaign_channels cc ON ch.id = cc.channel_id
        GROUP BY ch.id
        HAVING total_spend > 0
        ORDER BY roi DESC
    """).fetchall()

    db.close()

    return render_template('marketing/roi_dashboard.html',
        title='Marketing ROI',
        campaign_roi=[dict(r) for r in campaign_roi],
        channel_roi=[dict(r) for r in channel_roi],
        totals={
            'investment': total_investment,
            'revenue': total_revenue,
            'profit': total_profit,
            'leads': total_leads,
            'customers': total_customers,
            'roi': overall_roi,
            'cpl': overall_cpl,
            'cpa': overall_cpa,
        },
        date_from=date_from,
        date_to=date_to,
    )


# =============================================================================
# MARKETING ASSETS LIBRARY
# =============================================================================

@mkt_bp.route('/assets')
@mkt_login_required
@mkt_permission_required('view_content')
def assets_list():
    """List marketing assets."""
    db = get_db()

    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page

    search = request.args.get('search', '')
    asset_type = request.args.get('asset_type', '')

    query = """
        SELECT a.*, u.username as created_by_name
        FROM marketing_assets a
        LEFT JOIN users u ON a.created_by_user_id = u.id
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) as cnt FROM marketing_assets WHERE 1=1"
    params = []
    count_params = []

    if search:
        query += " AND (a.asset_name LIKE ? OR a.tags LIKE ?)"
        count_query += " AND (asset_name LIKE ? OR tags LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
        count_params.extend([search_term, search_term])

    if asset_type:
        query += " AND a.asset_type = ?"
        count_query += " AND asset_type = ?"
        params.append(asset_type)
        count_params.append(asset_type)

    total = db.execute(count_query, count_params).fetchone()['cnt']
    query += " ORDER BY a.created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])

    assets = db.execute(query, params).fetchall()
    db.close()

    return render_template('marketing/assets.html',
        title='Marketing Assets',
        assets=[dict(r) for r in assets],
        page=page, per_page=per_page, total=total,
        search=search, asset_type=asset_type,
    )


# =============================================================================
# COMMUNICATIONS CENTER
# =============================================================================

@mkt_bp.route('/communications')
@mkt_login_required
@mkt_permission_required('view_reports')
def communications_list():
    """List marketing communications log."""
    db = get_db()

    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page

    search = request.args.get('search', '')
    channel = request.args.get('channel', '')
    status = request.args.get('status', '')

    query = """
        SELECT c.*, camp.name as campaign_name, t.template_name
        FROM marketing_communications c
        LEFT JOIN marketing_campaigns camp ON c.campaign_id = camp.id
        LEFT JOIN marketing_templates t ON c.template_id = t.id
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) as cnt FROM marketing_communications WHERE 1=1"
    params = []
    count_params = []

    if search:
        query += " AND (c.recipient_name LIKE ? OR c.subject LIKE ?)"
        count_query += " AND (recipient_name LIKE ? OR subject LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
        count_params.extend([search_term, search_term])

    if channel:
        query += " AND c.channel = ?"
        count_query += " AND channel = ?"
        params.append(channel)
        count_params.append(channel)

    if status:
        query += " AND c.status = ?"
        count_query += " AND status = ?"
        params.append(status)
        count_params.append(status)

    total = db.execute(count_query, count_params).fetchone()['cnt']
    query += " ORDER BY c.created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])

    comms = db.execute(query, params).fetchall()
    db.close()

    return render_template('marketing/communications.html',
        title='Communications Center',
        communications=[dict(r) for r in comms],
        page=page, per_page=per_page, total=total,
        search=search, channel=channel, status=status,
    )


# =============================================================================
# EXPORT CENTER
# =============================================================================

@mkt_bp.route('/exports')
@mkt_login_required
@mkt_permission_required('view_reports')
def exports_list():
    """List and manage exports."""
    db = get_db()

    configs = db.execute("""
        SELECT * FROM marketing_export_configs
        WHERE is_active = 1
        ORDER BY export_type, config_name
    """).fetchall()

    db.close()

    return render_template('marketing/exports.html',
        title='Export Center',
        configs=[dict(r) for r in configs],
    )


@mkt_bp.route('/exports/configure/<int:id>', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('view_reports')
def export_configure(id):
    """Configure and execute an export."""
    db = get_db()

    config = db.execute("SELECT * FROM marketing_export_configs WHERE id = ?", (id,)).fetchone()
    if not config:
        flash('Export configuration not found.', 'error')
        return redirect(url_for('marketing.exports_list'))

    if request.method == 'POST':
        columns = request.form.getlist('columns')
        date_from = request.form.get('date_from', '')
        date_to = request.form.get('date_to', '')
        output_format = request.form.get('output_format', 'csv')

        # Build export based on entity_type
        entity_type = config['entity_type']
        data = []
        headers = []

        if entity_type == 'campaign':
            data = db.execute("""
                SELECT * FROM marketing_campaigns
                WHERE created_at BETWEEN ? AND ?
            """, (date_from, date_to)).fetchall() if date_from and date_to else db.execute("SELECT * FROM marketing_campaigns").fetchall()
            headers = [d[0] for d in db.execute("PRAGMA table_info(marketing_campaigns)").fetchall()]

        elif entity_type == 'lead':
            data = db.execute("""
                SELECT l.*, ls.total_score, ls.score_grade
                FROM marketing_leads l
                LEFT JOIN marketing_lead_scores ls ON l.id = ls.lead_id
            """).fetchall()

        elif entity_type == 'segment':
            data = db.execute("SELECT * FROM marketing_customer_segments").fetchall()

        elif entity_type == 'channel':
            data = db.execute("SELECT * FROM marketing_channels").fetchall()

        elif entity_type == 'journey':
            data = db.execute("""
                SELECT j.*, COUNT(p.id) as participant_count
                FROM marketing_nurture_journeys j
                LEFT JOIN marketing_journey_participants p ON j.id = p.journey_id
                GROUP BY j.id
            """).fetchall()

        # Generate CSV
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        if columns:
            writer.writerow(columns)
            for row in data:
                writer.writerow([row.get(col, '') for col in columns])
        else:
            writer.writerow([d[1] for d in db.execute(f"PRAGMA table_info(marketing_{entity_type})").fetchall()])
            for row in data:
                writer.writerow(row)

        output.seek(0)
        db.close()

        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=marketing_{entity_type}_export.csv'}
        )

    db.close()
    return render_template('marketing/export_configure.html',
        title=f'Configure Export: {config["config_name"]}',
        config=dict(config),
    )


# =============================================================================
# MARKETING NOTIFICATIONS
# =============================================================================

@mkt_bp.route('/notifications')
@mkt_login_required
@mkt_permission_required('view_reports')
def notifications_list():
    """List marketing notifications for current user."""
    db = get_db()

    user_id = session.get('user_id')

    notifications = db.execute("""
        SELECT * FROM marketing_notifications
        WHERE (recipient_user_id = ? OR recipient_role = 'all')
        AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
        ORDER BY created_at DESC
        LIMIT 50
    """, (user_id,)).fetchall()

    unread_count = db.execute("""
        SELECT COUNT(*) as cnt FROM marketing_notifications
        WHERE (recipient_user_id = ? OR recipient_role = 'all')
        AND is_read = 0
        AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
    """, (user_id,)).fetchone()['cnt']

    db.close()

    return render_template('marketing/notifications.html',
        title='Marketing Notifications',
        notifications=[dict(r) for r in notifications],
        unread_count=unread_count,
    )


@mkt_bp.route('/notifications/mark-read/<int:id>', methods=['POST'])
@mkt_login_required
def notification_mark_read(id):
    """Mark notification as read."""
    db = get_db()

    db.execute("""
        UPDATE marketing_notifications SET
            is_read = 1, read_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (id,))
    db.commit()
    db.close()

    return jsonify({'success': True})


# =============================================================================
# FLOW INTEGRATION
# =============================================================================

@mkt_bp.route('/flow/send-notification', methods=['POST'])
@mkt_login_required
@mkt_permission_required('manage_campaigns')
def flow_send_notification():
    """Send a notification to Flow system."""
    data = request.get_json()

    notification_type = data.get('notification_type', 'marketing_alert')
    title = data.get('title', '')
    message = data.get('message', '')
    priority = data.get('priority', 'Normal')
    entity_type = data.get('entity_type')
    entity_id = data.get('entity_id')
    entity_name = data.get('entity_name')
    action_url = data.get('action_url')

    db = get_db()

    # Create notification in Flow format
    cursor = db.execute("""
        INSERT INTO marketing_notifications
        (notification_type, notification_title, notification_message, recipient_role,
         linked_entity_type, linked_entity_id, linked_entity_name, priority, action_url)
        VALUES (?, ?, ?, 'all', ?, ?, ?, ?, ?)
    """, (notification_type, title, message, entity_type, entity_id, entity_name, priority, action_url))
    db.commit()
    notification_id = cursor.lastrowid
    db.close()

    return jsonify({
        'success': True,
        'notification_id': notification_id,
        'message': 'Notification sent to Flow'
    })


@mkt_bp.route('/lead-scoring/new', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_leads')
def lead_scoring_new():
    """Create new lead scoring rule."""
    db = get_db()
    user = get_current_user()

    if request.method == 'POST':
        rule_name = request.form.get('rule_name', '').strip()
        rule_code = request.form.get('rule_code', '').strip()
        rule_type = request.form.get('rule_type', '')
        category = request.form.get('category', '')
        attribute_field = request.form.get('attribute_field', '')
        operator = request.form.get('operator', '')
        attribute_value = request.form.get('attribute_value', '')
        score_change = request.form.get('score_change', 0)
        priority = request.form.get('priority', 0)
        description = request.form.get('description', '')

        if not rule_name or not rule_type or not category:
            flash('Rule name, type, and category are required.', 'error')
            return render_template('marketing/lead_scoring_edit.html', title='New Scoring Rule', rule=None)

        if not rule_code:
            rule_code = f"LSR-{rule_type.upper()[:3]}-{datetime.now().strftime('%Y%m%d%H%M')}"

        cursor = db.execute("""
            INSERT INTO marketing_lead_scoring_rules
            (rule_name, rule_code, rule_type, category, attribute_field, operator, attribute_value, score_change, priority, description, created_by_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (rule_name, rule_code, rule_type, category, attribute_field, operator, attribute_value, score_change, priority, description, user['id']))
        db.commit()

        log_marketing_audit(db, 'lead_scoring_rule', cursor.lastrowid, 'CREATE',
                           new_value=json.dumps({'rule_name': rule_name, 'score_change': score_change}),
                           actor_user_id=user['id'])

        flash(f'Scoring rule "{rule_name}" created successfully.', 'success')
        return redirect(url_for('marketing.lead_scoring_list'))

    db.close()
    return render_template('marketing/lead_scoring_edit.html', title='New Scoring Rule', rule=None)


@mkt_bp.route('/lead-scoring/edit/<int:id>', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_leads')
def lead_scoring_edit(id):
    """Edit lead scoring rule."""
    db = get_db()
    user = get_current_user()

    rule = db.execute("SELECT * FROM marketing_lead_scoring_rules WHERE id = ?", (id,)).fetchone()
    if not rule:
        flash('Scoring rule not found.', 'error')
        return redirect(url_for('marketing.lead_scoring_list'))

    if request.method == 'POST':
        db.execute("""
            UPDATE marketing_lead_scoring_rules SET
                rule_name = ?, rule_code = ?, rule_type = ?, category = ?,
                attribute_field = ?, operator = ?, attribute_value = ?,
                score_change = ?, priority = ?, description = ?, is_active = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            request.form.get('rule_name', ''),
            request.form.get('rule_code', ''),
            request.form.get('rule_type', ''),
            request.form.get('category', ''),
            request.form.get('attribute_field', ''),
            request.form.get('operator', ''),
            request.form.get('attribute_value', ''),
            request.form.get('score_change', 0),
            request.form.get('priority', 0),
            request.form.get('description', ''),
            1 if request.form.get('is_active') else 0,
            id
        ))
        db.commit()

        log_marketing_audit(db, 'lead_scoring_rule', id, 'UPDATE', actor_user_id=user['id'])
        flash('Scoring rule updated successfully.', 'success')
        return redirect(url_for('marketing.lead_scoring_list'))

    db.close()
    return render_template('marketing/lead_scoring_edit.html', title=f'Edit: {rule["rule_name"]}', rule=dict(rule))


@mkt_bp.route('/lead-scoring/recalculate/<int:lead_id>', methods=['POST'])
@mkt_login_required
@mkt_permission_required('manage_leads')
def lead_scoring_recalculate(lead_id):
    """Recalculate score for a specific lead."""
    db = get_db()
    user = get_current_user()

    lead = db.execute("SELECT * FROM marketing_leads WHERE id = ?", (lead_id,)).fetchone()
    if not lead:
        return jsonify({'success': False, 'message': 'Lead not found'}), 404

    # Get active rules
    rules = db.execute("SELECT * FROM marketing_lead_scoring_rules WHERE is_active = 1").fetchall()

    demographic_score = 0
    behavioral_score = 0
    engagement_score = 0

    # Calculate scores based on rules
    for rule in rules:
        score = rule['score_change']
        if rule['category'] == 'demographic':
            demographic_score += score
        elif rule['category'] == 'behavioral':
            behavioral_score += score
        elif rule['category'] == 'engagement':
            engagement_score += score

    total_score = max(0, demographic_score + behavioral_score + engagement_score)

    # Determine grades
    if total_score >= 80:
        grade = 'Hot'
        is_mql = 1
        is_sql = 1
    elif total_score >= 50:
        grade = 'Warm'
        is_mql = 1
        is_sql = 0
    else:
        grade = 'Cold'
        is_mql = 0
        is_sql = 0

    # Update or create score record
    existing_score = db.execute("SELECT id FROM marketing_lead_scores WHERE lead_id = ?", (lead_id,)).fetchone()

    if existing_score:
        db.execute("""
            UPDATE marketing_lead_scores SET
                total_score = ?, demographic_score = ?, behavioral_score = ?, engagement_score = ?,
                is_mql = ?, is_sql = ?, score_grade = ?, last_calculated_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE lead_id = ?
        """, (total_score, demographic_score, behavioral_score, engagement_score, is_mql, is_sql, grade, lead_id))
    else:
        db.execute("""
            INSERT INTO marketing_lead_scores
            (lead_id, total_score, demographic_score, behavioral_score, engagement_score, is_mql, is_sql, score_grade, last_calculated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (lead_id, total_score, demographic_score, behavioral_score, engagement_score, is_mql, is_sql, grade))

    # Log score history
    previous_total = existing_score['total_score'] if existing_score else 0
    db.execute("""
        INSERT INTO marketing_lead_score_history
        (lead_id, score_change, previous_score, new_score, trigger_type, trigger_description, triggered_by_user_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (lead_id, total_score - previous_total, previous_total, total_score, 'manual_recalculation', 'Manual score recalculation', user['id']))

    db.commit()
    db.close()

    return jsonify({
        'success': True,
        'total_score': total_score,
        'grade': grade,
        'is_mql': bool(is_mql),
        'is_sql': bool(is_sql)
    })


# =============================================================================
# NURTURE JOURNEYS
# =============================================================================

@mkt_bp.route('/journeys/new', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_campaigns')
def journeys_new():
    """Create new nurture journey."""
    db = get_db()
    user = get_current_user()

    segments = db.execute("SELECT id, name, code FROM marketing_customer_segments WHERE status = 'Active' ORDER BY name").fetchall()
    contents = db.execute("SELECT id, topic, title FROM marketing_content WHERE status = 'Published' ORDER BY title").fetchall()
    templates = db.execute("SELECT id, template_name, channel FROM marketing_templates WHERE is_active = 1 ORDER BY template_name").fetchall()

    if request.method == 'POST':
        journey_name = request.form.get('journey_name', '').strip()
        journey_code = request.form.get('journey_code', '').strip()
        journey_type = request.form.get('journey_type', '')
        description = request.form.get('description', '')
        objective = request.form.get('objective', '')
        target_segment_id = request.form.get('target_segment_id')
        entry_trigger_type = request.form.get('entry_trigger_type', '')
        status = request.form.get('status', 'Draft')

        if not journey_name or not journey_type:
            flash('Journey name and type are required.', 'error')
            return render_template('marketing/journey_edit.html', title='New Journey', journey=None,
                                   segments=[dict(r) for r in segments], contents=[dict(r) for r in contents],
                                   templates=[dict(r) for r in templates])

        if not journey_code:
            journey_code = f"JRN-{datetime.now().strftime('%Y%m%d%H%M')}"

        cursor = db.execute("""
            INSERT INTO marketing_nurture_journeys
            (journey_name, journey_code, journey_type, description, objective, target_segment_id,
             entry_trigger_type, status, created_by_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (journey_name, journey_code, journey_type, description, objective, target_segment_id,
              entry_trigger_type, status, user['id']))
        db.commit()
        journey_id = cursor.lastrowid

        # Add journey steps if provided
        step_names = request.form.getlist('step_name')
        step_types = request.form.getlist('step_type')
        step_delays = request.form.getlist('step_delay')

        for i, (name, stype, delay) in enumerate(zip(step_names, step_types, step_delays)):
            if name and stype:
                db.execute("""
                    INSERT INTO marketing_journey_steps
                    (journey_id, step_order, step_name, step_type, delay_hours, is_entry_step)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (journey_id, i + 1, name, stype, delay or 0, 1 if i == 0 else 0))
        db.commit()

        log_marketing_audit(db, 'nurture_journey', journey_id, 'CREATE',
                           new_value=json.dumps({'journey_name': journey_name, 'journey_type': journey_type}),
                           actor_user_id=user['id'])

        flash(f'Journey "{journey_name}" created successfully.', 'success')
        return redirect(url_for('marketing.journeys_view', id=journey_id))

    db.close()
    return render_template('marketing/journey_edit.html', title='New Journey', journey=None,
                          segments=[dict(r) for r in segments], contents=[dict(r) for r in contents],
                          templates=[dict(r) for r in templates])


@mkt_bp.route('/journeys/view/<int:id>')
@mkt_login_required
@mkt_permission_required('view_campaigns')
def journeys_view(id):
    """View journey details."""
    db = get_db()

    journey = db.execute("""
        SELECT j.*, s.name as segment_name, u.username as created_by_name
        FROM marketing_nurture_journeys j
        LEFT JOIN marketing_customer_segments s ON j.target_segment_id = s.id
        LEFT JOIN users u ON j.created_by_user_id = u.id
        WHERE j.id = ?
    """, (id,)).fetchone()

    if not journey:
        flash('Journey not found.', 'error')
        return redirect(url_for('marketing.journeys_list'))

    steps = db.execute("""
        SELECT * FROM marketing_journey_steps
        WHERE journey_id = ?
        ORDER BY step_order
    """, (id,)).fetchall()

    participants = db.execute("""
        SELECT p.*, l.lead_name, l.email, l.phone
        FROM marketing_journey_participants p
        JOIN marketing_leads l ON p.lead_id = l.id
        WHERE p.journey_id = ?
        ORDER BY p.enrolled_at DESC
        LIMIT 50
    """, (id,)).fetchall()

    # Journey performance metrics
    perf_metrics = db.execute("""
        SELECT
            COUNT(*) as total_enrolled,
            SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active,
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'Dropped' THEN 1 ELSE 0 END) as dropped,
            AVG(total_engagements) as avg_engagements,
            SUM(conversion_value) as total_conversion_value
        FROM marketing_journey_participants
        WHERE journey_id = ?
    """, (id,)).fetchone()

    db.close()

    return render_template('marketing/journey_view.html',
        title=f'Journey: {journey["journey_name"]}',
        journey=dict(journey),
        steps=[dict(r) for r in steps],
        participants=[dict(r) for r in participants],
        perf_metrics=dict(perf_metrics) if perf_metrics else None,
    )


@mkt_bp.route('/journeys/edit/<int:id>', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_campaigns')
def journeys_edit(id):
    """Edit nurture journey."""
    db = get_db()
    user = get_current_user()

    journey = db.execute("SELECT * FROM marketing_nurture_journeys WHERE id = ?", (id,)).fetchone()
    if not journey:
        flash('Journey not found.', 'error')
        return redirect(url_for('marketing.journeys_list'))

    segments = db.execute("SELECT id, name, code FROM marketing_customer_segments WHERE status = 'Active' ORDER BY name").fetchall()
    contents = db.execute("SELECT id, topic, title FROM marketing_content WHERE status = 'Published' ORDER BY title").fetchall()
    templates = db.execute("SELECT id, template_name, channel FROM marketing_templates WHERE is_active = 1 ORDER BY template_name").fetchall()
    steps = db.execute("SELECT * FROM marketing_journey_steps WHERE journey_id = ? ORDER BY step_order", (id,)).fetchall()

    if request.method == 'POST':
        db.execute("""
            UPDATE marketing_nurture_journeys SET
                journey_name = ?, journey_code = ?, journey_type = ?,
                description = ?, objective = ?, target_segment_id = ?,
                entry_trigger_type = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            request.form.get('journey_name', ''),
            request.form.get('journey_code', ''),
            request.form.get('journey_type', ''),
            request.form.get('description', ''),
            request.form.get('objective', ''),
            request.form.get('target_segment_id'),
            request.form.get('entry_trigger_type', ''),
            request.form.get('status', 'Draft'),
            id
        ))
        db.commit()

        log_marketing_audit(db, 'nurture_journey', id, 'UPDATE', actor_user_id=user['id'])
        flash('Journey updated successfully.', 'success')
        return redirect(url_for('marketing.journeys_view', id=id))

    db.close()
    return render_template('marketing/journey_edit.html', title=f'Edit: {journey["journey_name"]}',
                          journey=dict(journey), steps=[dict(r) for r in steps],
                          segments=[dict(r) for r in segments], contents=[dict(r) for r in contents],
                          templates=[dict(r) for r in templates])


@mkt_bp.route('/journeys/publish/<int:id>', methods=['POST'])
@mkt_login_required
@mkt_permission_required('manage_campaigns')
def journeys_publish(id):
    """Publish a journey to make it active."""
    db = get_db()
    user = get_current_user()

    journey = db.execute("SELECT * FROM marketing_nurture_journeys WHERE id = ?", (id,)).fetchone()
    if not journey:
        return jsonify({'success': False, 'message': 'Journey not found'}), 404

    # Check if journey has at least one step
    steps = db.execute("SELECT COUNT(*) as cnt FROM marketing_journey_steps WHERE journey_id = ?", (id,)).fetchone()
    if steps['cnt'] == 0:
        return jsonify({'success': False, 'message': 'Journey must have at least one step before publishing'}), 400

    db.execute("""
        UPDATE marketing_nurture_journeys SET
            is_published = 1, is_active = 1, status = 'Active',
            published_at = CURRENT_TIMESTAMP, published_by_user_id = ?
        WHERE id = ?
    """, (user['id'], id))
    db.commit()

    log_marketing_audit(db, 'nurture_journey', id, 'PUBLISH', actor_user_id=user['id'])
    flash(f'Journey "{journey["journey_name"]}" published successfully.', 'success')

    return redirect(url_for('marketing.journeys_view', id=id))


# =============================================================================
# A/B TESTING
# =============================================================================

@mkt_bp.route('/ab-tests/new', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_campaigns')
def ab_tests_new():
    """Create new A/B test."""
    db = get_db()
    user = get_current_user()

    campaigns = db.execute("SELECT id, name FROM marketing_campaigns WHERE status IN ('Active', 'Draft') ORDER BY name").fetchall()
    segments = db.execute("SELECT id, name FROM marketing_customer_segments WHERE status = 'Active' ORDER BY name").fetchall()

    if request.method == 'POST':
        test_name = request.form.get('test_name', '').strip()
        test_code = request.form.get('test_code', '').strip()
        test_type = request.form.get('test_type', '')
        hypothesis = request.form.get('hypothesis', '')
        description = request.form.get('description', '')
        campaign_id = request.form.get('campaign_id')
        channel = request.form.get('channel', '')
        control_variant = request.form.get('control_variant', '')
        challenger_variant = request.form.get('challenger_variant', '')
        control_percentage = request.form.get('control_percentage', 50)
        success_metric = request.form.get('success_metric', '')
        start_date = request.form.get('start_date', '')
        end_date = request.form.get('end_date', '')
        status = request.form.get('status', 'Draft')

        if not test_name or not test_type:
            flash('Test name and type are required.', 'error')
            return render_template('marketing/ab_test_edit.html', title='New A/B Test', test=None,
                                   campaigns=[dict(r) for r in campaigns], segments=[dict(r) for r in segments])

        if not test_code:
            test_code = f"AB-{datetime.now().strftime('%Y%m%d%H%M')}"

        cursor = db.execute("""
            INSERT INTO marketing_ab_tests
            (test_name, test_code, test_type, hypothesis, description, campaign_id, channel,
             control_variant, challenger_variant, control_percentage, challenger_percentage,
             success_metric, start_date, end_date, status, created_by_user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (test_name, test_code, test_type, hypothesis, description, campaign_id, channel,
              control_variant, challenger_variant, control_percentage, 100 - int(control_percentage),
              success_metric, start_date, end_date, status, user['id']))
        db.commit()
        test_id = cursor.lastrowid

        # Create variants
        db.execute("""
            INSERT INTO marketing_ab_test_variants (test_id, variant_name, variant_type)
            VALUES (?, ?, 'control')
        """, (test_id, control_variant or 'Control'))

        db.execute("""
            INSERT INTO marketing_ab_test_variants (test_id, variant_name, variant_type)
            VALUES (?, ?, 'challenger')
        """, (test_id, challenger_variant or 'Challenger'))

        db.commit()

        flash(f'A/B Test "{test_name}" created successfully.', 'success')
        return redirect(url_for('marketing.ab_tests_view', id=test_id))

    db.close()
    return render_template('marketing/ab_test_edit.html', title='New A/B Test', test=None,
                          campaigns=[dict(r) for r in campaigns], segments=[dict(r) for r in segments])


@mkt_bp.route('/ab-tests/view/<int:id>')
@mkt_login_required
@mkt_permission_required('view_campaigns')
def ab_tests_view(id):
    """View A/B test details."""
    db = get_db()

    test = db.execute("""
        SELECT t.*, c.name as campaign_name, s.name as segment_name,
               u.username as created_by_name
        FROM marketing_ab_tests t
        LEFT JOIN marketing_campaigns c ON t.campaign_id = c.id
        LEFT JOIN marketing_customer_segments s ON t.target_segment_id = s.id
        LEFT JOIN users u ON t.created_by_user_id = u.id
        WHERE t.id = ?
    """, (id,)).fetchone()

    if not test:
        flash('A/B test not found.', 'error')
        return redirect(url_for('marketing.ab_tests_list'))

    variants = db.execute("SELECT * FROM marketing_ab_test_variants WHERE test_id = ?", (id,)).fetchall()

    db.close()

    return render_template('marketing/ab_test_view.html',
        title=f'A/B Test: {test["test_name"]}',
        test=dict(test),
        variants=[dict(r) for r in variants],
    )


@mkt_bp.route('/ab-tests/edit/<int:id>', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('manage_campaigns')
def ab_tests_edit(id):
    """Edit A/B test."""
    db = get_db()
    user = get_current_user()

    test = db.execute("SELECT * FROM marketing_ab_tests WHERE id = ?", (id,)).fetchone()
    if not test:
        flash('A/B test not found.', 'error')
        return redirect(url_for('marketing.ab_tests_list'))

    campaigns = db.execute("SELECT id, name FROM marketing_campaigns WHERE status IN ('Active', 'Draft') ORDER BY name").fetchall()
    segments = db.execute("SELECT id, name FROM marketing_customer_segments WHERE status = 'Active' ORDER BY name").fetchall()
    variants = db.execute("SELECT * FROM marketing_ab_test_variants WHERE test_id = ?", (id,)).fetchall()

    if request.method == 'POST':
        db.execute("""
            UPDATE marketing_ab_tests SET
                test_name = ?, test_type = ?, hypothesis = ?, description = ?,
                campaign_id = ?, channel = ?, control_variant = ?, challenger_variant = ?,
                control_percentage = ?, challenger_percentage = ?, success_metric = ?,
                start_date = ?, end_date = ?, status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            request.form.get('test_name', ''),
            request.form.get('test_type', ''),
            request.form.get('hypothesis', ''),
            request.form.get('description', ''),
            request.form.get('campaign_id'),
            request.form.get('channel', ''),
            request.form.get('control_variant', ''),
            request.form.get('challenger_variant', ''),
            request.form.get('control_percentage', 50),
            request.form.get('challenger_percentage', 50),
            request.form.get('success_metric', ''),
            request.form.get('start_date', ''),
            request.form.get('end_date', ''),
            request.form.get('status', 'Draft'),
            id
        ))
        db.commit()

        log_marketing_audit(db, 'ab_test', id, 'UPDATE', actor_user_id=user['id'])
        flash('A/B test updated successfully.', 'success')
        return redirect(url_for('marketing.ab_tests_view', id=id))

    db.close()
    return render_template('marketing/ab_test_edit.html', title=f'Edit: {test["test_name"]}',
                          test=dict(test), variants=[dict(r) for r in variants],
                          campaigns=[dict(r) for r in campaigns], segments=[dict(r) for r in segments])


# =============================================================================
# CUSTOMER JOURNEY INTELLIGENCE
# =============================================================================

@mkt_bp.route('/journey-intelligence/customer/<int:customer_id>')
@mkt_login_required
@mkt_permission_required('view_reports')
def journey_intelligence_customer(customer_id):
    """View journey intelligence for a specific customer."""
    db = get_db()

    # Get customer info
    customer = db.execute("SELECT * FROM sdad_customers WHERE id = ?", (customer_id,)).fetchone()

    # Get journey records
    journeys = db.execute("""
        SELECT ji.*, c.name as channel_name, camp.name as campaign_name
        FROM marketing_journey_intelligence ji
        LEFT JOIN marketing_channels c ON ji.channel_id = c.id
        LEFT JOIN marketing_campaigns camp ON ji.campaign_id = camp.id
        WHERE ji.customer_id = ?
        ORDER BY ji.touchpoint_date DESC
    """, (customer_id,)).fetchall()

    # Get associated leads
    leads = db.execute("SELECT * FROM marketing_leads WHERE phone LIKE ? OR email LIKE ?",
                       (f"%{customer['phone'] if customer else ''}%", f"%{customer['email'] if customer else ''}%")).fetchall()

    # Calculate journey summary
    summary = {
        'total_touchpoints': len(journeys),
        'avg_engagement': sum([j['engagement_score'] or 0 for j in journeys]) / len(journeys) if journeys else 0,
        'avg_churn_risk': sum([j['churn_risk_score'] or 0 for j in journeys]) / len(journeys) if journeys else 0,
        'conversion_value': sum([j['conversion_value'] or 0 for j in journeys]),
    }

    # Get next best actions
    next_actions = db.execute("""
        SELECT next_best_action, COUNT(*) as count
        FROM marketing_journey_intelligence
        WHERE customer_id = ? AND next_best_action IS NOT NULL
        GROUP BY next_best_action
        ORDER BY count DESC
        LIMIT 5
    """, (customer_id,)).fetchall()

    db.close()

    return render_template('marketing/journey_intelligence_customer.html',
        title=f'Customer Journey: {customer["name"] if customer else "Unknown"}',
        customer=dict(customer) if customer else None,
        journeys=[dict(j) for j in journeys],
        leads=[dict(l) for l in leads],
        summary=summary,
        next_actions=[dict(a) for a in next_actions],
    )


# =============================================================================
# ROI & PERFORMANCE
# =============================================================================

@mkt_bp.route('/roi-dashboard')
@mkt_login_required
@mkt_permission_required('view_reports')
def roi_dashboard_page():
    """Marketing ROI dashboard."""
    db = get_db()

    date_from = request.args.get('date_from', (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

    # Get campaign ROI data
    campaign_roi = db.execute("""
        SELECT
            c.id, c.name, c.campaign_type, c.status,
            c.budget, c.actual_cost,
            COALESCE(SUM(m.sales_generated), 0) as total_sales,
            COALESCE(SUM(m.new_customers_acquired), 0) as new_customers,
            CASE WHEN c.actual_cost > 0
                 THEN ROUND((COALESCE(SUM(m.sales_generated), 0) - c.actual_cost) / c.actual_cost * 100, 2)
                 ELSE 0 END as roi_percentage,
            CASE WHEN COUNT(DISTINCT l.id) > 0
                 THEN ROUND(c.actual_cost / COUNT(DISTINCT l.id), 2)
                 ELSE 0 END as cost_per_lead,
            CASE WHEN SUM(m.new_customers_acquired) > 0
                 THEN ROUND(c.actual_cost / SUM(m.new_customers_acquired), 2)
                 ELSE 0 END as cost_per_acquisition
        FROM marketing_campaigns c
        LEFT JOIN marketing_campaigns m ON c.id = m.id
        LEFT JOIN marketing_leads l ON l.related_campaign_id = c.id
        WHERE c.start_date >= ? AND c.start_date <= ?
        GROUP BY c.id
        ORDER BY roi_percentage DESC
    """, (date_from, date_to)).fetchall()

    # Get channel ROI breakdown
    channel_roi = db.execute("""
        SELECT
            ch.name as channel_name, ch.channel_type,
            SUM(cc.actual_spend) as total_spend,
            SUM(cc.leads_generated) as total_leads,
            SUM(cc.sales_generated) as total_sales,
            CASE WHEN SUM(cc.leads_generated) > 0
                 THEN ROUND(SUM(cc.actual_spend) / SUM(cc.leads_generated), 2)
                 ELSE 0 END as cost_per_lead,
            CASE WHEN SUM(cc.actual_spend) > 0
                 THEN ROUND((SUM(cc.sales_generated) - SUM(cc.actual_spend)) / SUM(cc.actual_spend) * 100, 2)
                 ELSE 0 END as roi_percentage
        FROM marketing_channels ch
        LEFT JOIN marketing_campaign_channels cc ON ch.id = cc.channel_id
        LEFT JOIN marketing_campaigns c ON cc.campaign_id = c.id
        WHERE c.start_date >= ? AND c.start_date <= ?
        GROUP BY ch.id
        ORDER BY roi_percentage DESC
    """, (date_from, date_to)).fetchall()

    # Summary metrics
    summary = db.execute("""
        SELECT
            SUM(c.actual_cost) as total_marketing_spend,
            SUM(c.sales_generated) as total_revenue,
            SUM(c.profit_generated) as total_profit,
            SUM(c.leads_generated) as total_leads,
            SUM(c.new_customers_acquired) as total_new_customers,
            CASE WHEN SUM(c.leads_generated) > 0
                 THEN ROUND(SUM(c.actual_cost) / SUM(c.leads_generated), 2)
                 ELSE 0 END as avg_cost_per_lead,
            CASE WHEN SUM(c.new_customers_acquired) > 0
                 THEN ROUND(SUM(c.actual_cost) / SUM(c.new_customers_acquired), 2)
                 ELSE 0 END as avg_cost_per_acquisition,
            CASE WHEN SUM(c.actual_cost) > 0
                 THEN ROUND((SUM(c.sales_generated) - SUM(c.actual_cost)) / SUM(c.actual_cost) * 100, 2)
                 ELSE 0 END as overall_roi
        FROM marketing_campaigns c
        WHERE c.start_date >= ? AND c.start_date <= ?
    """, (date_from, date_to)).fetchone()

    db.close()

    return render_template('marketing/roi_dashboard.html',
        title='Marketing ROI Dashboard',
        campaign_roi=[dict(r) for r in campaign_roi],
        channel_roi=[dict(r) for r in channel_roi],
        summary=dict(summary) if summary else None,
        date_from=date_from, date_to=date_to,
    )


# =============================================================================
# CHANNEL DELIVERABILITY
# =============================================================================

@mkt_bp.route('/channel-deliverability')
@mkt_login_required
@mkt_permission_required('view_channels')
def channel_deliverability():
    """Channel deliverability metrics."""
    db = get_db()

    metrics = db.execute("""
        SELECT * FROM marketing_channel_deliverability
        ORDER BY channel, period_end DESC
    """).fetchall()

    # Recent communications summary
    comm_summary = db.execute("""
        SELECT
            channel,
            COUNT(*) as total_sent,
            SUM(CASE WHEN status = 'Delivered' THEN 1 ELSE 0 END) as delivered,
            SUM(CASE WHEN status = 'Opened' THEN 1 ELSE 0 END) as opened,
            SUM(CASE WHEN status = 'Clicked' THEN 1 ELSE 0 END) as clicked,
            SUM(CASE WHEN status = 'Bounced' THEN 1 ELSE 0 END) as bounced,
            SUM(CASE WHEN status = 'Unsubscribed' THEN 1 ELSE 0 END) as unsubscribed,
            SUM(total_cost) as total_cost
        FROM marketing_communications
        GROUP BY channel
    """).fetchall()

    db.close()

    return render_template('marketing/channel_deliverability.html',
        title='Channel Deliverability',
        metrics=[dict(r) for r in metrics],
        comm_summary=[dict(r) for r in comm_summary],
    )


# =============================================================================
# MARKETING ASSETS
# =============================================================================

@mkt_bp.route('/assets-library')
@mkt_login_required
@mkt_permission_required('view_content')
def assets_library_list():
    """List marketing assets."""
    db = get_db()

    page = int(request.args.get('page', 1))
    per_page = 30
    offset = (page - 1) * per_page

    search = request.args.get('search', '')
    asset_type = request.args.get('asset_type', '')

    query = """
        SELECT a.*, u.username as created_by_name
        FROM marketing_assets a
        LEFT JOIN users u ON a.created_by_user_id = u.id
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) as cnt FROM marketing_assets WHERE 1=1"
    params = []
    count_params = []

    if search:
        query += " AND (a.asset_name LIKE ? OR a.asset_code LIKE ? OR a.tags LIKE ?)"
        count_query += " AND (asset_name LIKE ? OR asset_code LIKE ? OR tags LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
        count_params.extend([search_term, search_term, search_term])

    if asset_type:
        query += " AND a.asset_type = ?"
        count_query += " AND asset_type = ?"
        params.append(asset_type)
        count_params.append(asset_type)

    total = db.execute(count_query, count_params).fetchone()['cnt']
    query += " ORDER BY a.created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])

    assets = db.execute(query, params).fetchall()

    db.close()

    return render_template('marketing/assets.html',
        title='Marketing Assets',
        assets=[dict(r) for r in assets],
        page=page, per_page=per_page, total=total,
        search=search, asset_type=asset_type,
    )


@mkt_bp.route('/templates')
@mkt_login_required
@mkt_permission_required('view_content')
def templates_list():
    """List marketing templates."""
    db = get_db()

    templates = db.execute("""
        SELECT t.*, u.username as created_by_name
        FROM marketing_templates t
        LEFT JOIN users u ON t.created_by_user_id = u.id
        ORDER BY t.channel, t.template_name
    """).fetchall()

    db.close()

    return render_template('marketing/templates.html',
        title='Marketing Templates',
        templates=[dict(r) for r in templates],
    )


# =============================================================================
# EXPORT CENTER
# =============================================================================

@mkt_bp.route('/export-center')
@mkt_login_required
@mkt_permission_required('view_reports')
def export_center():
    """Marketing export center."""
    db = get_db()

    # Get saved export configurations
    configs = db.execute("""
        SELECT c.*, u.username as created_by_name
        FROM marketing_export_configs c
        LEFT JOIN users u ON c.created_by_user_id = u.id
        WHERE c.is_active = 1
        ORDER BY c.entity_type, c.config_name
    """).fetchall()

    # Get recent exports
    recent_exports = db.execute("""
        SELECT * FROM marketing_activity_log
        WHERE activity_type = 'export'
        ORDER BY created_at DESC
        LIMIT 20
    """).fetchall()

    db.close()

    return render_template('marketing/export_center.html',
        title='Export Center',
        configs=[dict(c) for c in configs],
        recent_exports=[dict(e) for e in recent_exports],
    )


@mkt_bp.route('/export/run/<int:config_id>', methods=['GET', 'POST'])
@mkt_login_required
@mkt_permission_required('view_reports')
def export_run(config_id):
    """Run an export with a specific configuration."""
    db = get_db()

    config = db.execute("SELECT * FROM marketing_export_configs WHERE id = ?", (config_id,)).fetchone()
    if not config:
        flash('Export configuration not found.', 'error')
        return redirect(url_for('marketing.export_center'))

    # Build export data based on entity type
    export_data = []
    headers = []

    if config['entity_type'] == 'campaign':
        headers = ['Name', 'Code', 'Type', 'Status', 'Start Date', 'End Date', 'Budget', 'Actual Cost', 'Leads', 'Sales', 'ROI %']
        rows = db.execute("""
            SELECT name, code, campaign_type, status, start_date, end_date,
                   budget, actual_cost, leads_generated, sales_generated,
                   CASE WHEN actual_cost > 0 THEN ROUND((sales_generated - actual_cost) / actual_cost * 100, 1) ELSE 0 END as roi
            FROM marketing_campaigns
            ORDER BY created_at DESC
        """).fetchall()
        export_data = [dict(r) for r in rows]

    elif config['entity_type'] == 'lead':
        headers = ['Name', 'Email', 'Phone', 'Source', 'Status', 'Importance', 'Value', 'Probability', 'Created']
        rows = db.execute("""
            SELECT l.lead_name, l.email, l.phone, s.name as source_name,
                   l.lead_status, l.importance_level, l.estimated_value,
                   l.conversion_probability, l.created_at
            FROM marketing_leads l
            LEFT JOIN marketing_lead_sources s ON l.source_id = s.id
            ORDER BY l.created_at DESC
        """).fetchall()
        export_data = [dict(r) for r in rows]

    elif config['entity_type'] == 'segment':
        headers = ['Name', 'Code', 'Type', 'Customer Type', 'Status', 'Created']
        rows = db.execute("""
            SELECT name, code, segment_type, customer_type, status, created_at
            FROM marketing_customer_segments
            ORDER BY name
        """).fetchall()
        export_data = [dict(r) for r in rows]

    elif config['entity_type'] == 'channel':
        headers = ['Name', 'Code', 'Type', 'Budget', 'Status']
        rows = db.execute("""
            SELECT name, code, channel_type, budget, status
            FROM marketing_channels
            ORDER BY name
        """).fetchall()
        export_data = [dict(r) for r in rows]

    db.close()

    # Log export
    log_marketing_audit(db, 'export', config_id, 'EXPORT',
                       new_value=json.dumps({'config_name': config['config_name'], 'entity_type': config['entity_type']}),
                       actor_user_id=get_current_user()['id'])

    # Generate file
    output = io.StringIO()
    writer = csv.writer(output)

    if config['include_headers']:
        writer.writerow(headers)

    for row in export_data:
        writer.writerow([row.get(h.lower().replace(' ', '_')) or row.get(h.lower()) or '' for h in headers])

    output.seek(0)

    filename = f"marketing_{config['entity_type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{config['output_format']}"

    return Response(
        output.getvalue(),
        mimetype='text/csv' if config['output_format'] == 'csv' else 'application/vnd.ms-excel',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


# =============================================================================
# MARKETING WORKFLOW & APPROVALS
# =============================================================================

@mkt_bp.route('/approvals')
@mkt_login_required
@mkt_permission_required('view_reports')
def approvals_list():
    """List pending approvals."""
    db = get_db()

    pending_campaigns = db.execute("""
        SELECT c.*, u.username as created_by_name
        FROM marketing_campaigns c
        LEFT JOIN users u ON c.created_by_user_id = u.id
        WHERE c.approval_state = 'Pending'
        ORDER BY c.created_at DESC
    """).fetchall()

    pending_budgets = db.execute("""
        SELECT b.*, u.username as created_by_name
        FROM marketing_budgets b
        LEFT JOIN users u ON b.created_by_user_id = u.id
        WHERE b.status = 'Pending Approval'
        ORDER BY b.created_at DESC
    """).fetchall()

    pending_content = db.execute("""
        SELECT ct.*, u.username as created_by_name
        FROM marketing_content ct
        LEFT JOIN users u ON ct.created_by_user_id = u.id
        WHERE ct.status = 'Pending Approval'
        ORDER BY ct.created_at DESC
    """).fetchall()

    db.close()

    return render_template('marketing/approvals.html',
        title='Marketing Approvals',
        pending_campaigns=[dict(r) for r in pending_campaigns],
        pending_budgets=[dict(r) for r in pending_budgets],
        pending_content=[dict(r) for r in pending_content],
    )


@mkt_bp.route('/approvals/campaign/<int:id>/approve', methods=['POST'])
@mkt_login_required
@mkt_permission_required('approve_campaigns')
def approval_campaign_approve(id):
    """Approve a campaign."""
    db = get_db()
    user = get_current_user()

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
    flash('Campaign approved successfully.', 'success')

    return redirect(url_for('marketing.approvals_list'))


@mkt_bp.route('/approvals/campaign/<int:id>/reject', methods=['POST'])
@mkt_login_required
@mkt_permission_required('approve_campaigns')
def approval_campaign_reject(id):
    """Reject a campaign."""
    db = get_db()
    user = get_current_user()
    reason = request.form.get('reason', '')

    db.execute("""
        UPDATE marketing_campaigns SET
            approval_state = 'Rejected',
            status = 'Draft'
        WHERE id = ?
    """, (id,))
    db.commit()

    log_marketing_audit(db, 'campaign', id, 'REJECT',
                       new_value=reason, actor_user_id=user['id'])
    flash('Campaign rejected.', 'warning')

    return redirect(url_for('marketing.approvals_list'))


# =============================================================================
# SLA MONITORING
# =============================================================================

@mkt_bp.route('/sla-monitoring')
@mkt_login_required
@mkt_permission_required('view_reports')
def sla_monitoring():
    """Marketing SLA monitoring."""
    db = get_db()

    # Get active SLA instances
    sla_instances = db.execute("""
        SELECT si.*, sp.policy_name, sp.policy_type,
               u.username as current_assignee_name,
               e.username as escalated_to_name
        FROM marketing_sla_instances si
        JOIN marketing_sla_policies sp ON si.sla_policy_id = sp.id
        LEFT JOIN users u ON si.current_assignee_id = u.id
        LEFT JOIN users e ON si.escalated_to_user_id = e.id
        WHERE si.status IN ('Active', 'Breached')
        ORDER BY si.status ASC, si.started_at DESC
    """).fetchall()

    # Get SLA summary
    sla_summary = db.execute("""
        SELECT
            COUNT(*) as total_active,
            SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as on_track,
            SUM(CASE WHEN status = 'Breached' THEN 1 ELSE 0 END) as breached,
            SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) as resolved
        FROM marketing_sla_instances
        WHERE status IN ('Active', 'Breached', 'Resolved')
    """).fetchone()

    db.close()

    return render_template('marketing/sla_monitoring.html',
        title='SLA Monitoring',
        sla_instances=[dict(r) for r in sla_instances],
        sla_summary=dict(sla_summary) if sla_summary else None,
    )


# =============================================================================
# BRANCH MARKETING CONFIG
# =============================================================================

@mkt_bp.route('/branch-marketing')
@mkt_login_required
@mkt_permission_required('manage_settings')
def branch_marketing_list():
    """List branch marketing configurations."""
    db = get_db()

    configs = db.execute("SELECT * FROM marketing_branch_configs ORDER BY branch_name").fetchall()

    db.close()

    return render_template('marketing/branch_marketing.html',
        title='Branch Marketing Configuration',
        configs=[dict(r) for r in configs],
    )


# =============================================================================
# REPORTS - CAMPAIGN DETAIL
# =============================================================================

@mkt_bp.route('/reports/campaign/<int:id>')
@mkt_login_required
@mkt_permission_required('view_reports')
def report_campaign_detail(id):
    """Detailed campaign report."""
    db = get_db()

    campaign = db.execute("""
        SELECT c.*, u.username as owner_name, b.name as brand_name, s.name as segment_name
        FROM marketing_campaigns c
        LEFT JOIN users u ON c.owner_user_id = u.id
        LEFT JOIN marketing_brands b ON c.target_brand_id = b.id
        LEFT JOIN marketing_customer_segments s ON c.target_segment_id = s.id
        WHERE c.id = ?
    """, (id,)).fetchone()

    if not campaign:
        flash('Campaign not found.', 'error')
        return redirect(url_for('marketing.campaigns_list'))

    # Get channel performance
    channel_perf = db.execute("""
        SELECT cc.*, c.name as channel_name, c.channel_type,
               c.budget as channel_budget
        FROM marketing_campaign_channels cc
        JOIN marketing_channels c ON cc.channel_id = c.id
        WHERE cc.campaign_id = ?
    """, (id,)).fetchall()

    # Get lead source breakdown
    lead_sources = db.execute("""
        SELECT ls.name, COUNT(l.id) as lead_count,
               SUM(l.estimated_value) as total_value,
               SUM(CASE WHEN l.lead_status = 'Converted to Customer' THEN 1 ELSE 0 END) as converted
        FROM marketing_leads l
        JOIN marketing_lead_sources ls ON l.source_id = ls.id
        WHERE l.related_campaign_id = ?
        GROUP BY ls.id
    """, (id,)).fetchall()

    # Get daily metrics
    daily_metrics = db.execute("""
        SELECT metric_date, SUM(metric_value) as value
        FROM marketing_performance_metrics
        WHERE entity_type = 'campaign' AND entity_id = ?
        GROUP BY metric_date
        ORDER BY metric_date
    """, (id,)).fetchall()

    db.close()

    return render_template('marketing/report_campaign.html',
        title=f'Campaign Report: {campaign["name"]}',
        campaign=dict(campaign),
        channel_perf=[dict(r) for r in channel_perf],
        lead_sources=[dict(r) for r in lead_sources],
        daily_metrics=[dict(r) for r in daily_metrics],
    )


# =============================================================================
# REPORTS - LEAD ANALYSIS
# =============================================================================

@mkt_bp.route('/reports/leads')
@mkt_login_required
@mkt_permission_required('view_reports')
def report_leads():
    """Lead analysis report."""
    db = get_db()

    date_from = request.args.get('date_from', (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

    # Lead by source
    leads_by_source = db.execute("""
        SELECT ls.name as source_name, COUNT(l.id) as count,
               SUM(l.estimated_value) as total_value,
               AVG(l.conversion_probability) as avg_probability
        FROM marketing_leads l
        JOIN marketing_lead_sources ls ON l.source_id = ls.id
        WHERE l.created_at >= ? AND l.created_at <= ?
        GROUP BY ls.id
        ORDER BY count DESC
    """, (date_from, date_to)).fetchall()

    # Lead by status
    leads_by_status = db.execute("""
        SELECT lead_status, COUNT(*) as count,
               SUM(estimated_value) as total_value
        FROM marketing_leads
        WHERE created_at >= ? AND created_at <= ?
        GROUP BY lead_status
    """, (date_from, date_to)).fetchall()

    # Lead scoring distribution
    scoring_dist = db.execute("""
        SELECT score_grade, COUNT(*) as count
        FROM marketing_lead_scores ls
        JOIN marketing_leads l ON ls.lead_id = l.id
        WHERE l.created_at >= ? AND l.created_at <= ?
        GROUP BY score_grade
    """, (date_from, date_to)).fetchall()

    # MQL/SQL funnel
    mql_sql = db.execute("""
        SELECT
            SUM(CASE WHEN is_mql = 1 THEN 1 ELSE 0 END) as mql_count,
            SUM(CASE WHEN is_sql = 1 THEN 1 ELSE 0 END) as sql_count,
            AVG(total_score) as avg_score
        FROM marketing_lead_scores
    """).fetchone()

    db.close()

    return render_template('marketing/report_lead.html',
        title='Lead Analysis Report',
        leads_by_source=[dict(r) for r in leads_by_source],
        leads_by_status=[dict(r) for r in leads_by_status],
        scoring_dist=[dict(r) for r in scoring_dist],
        mql_sql=dict(mql_sql) if mql_sql else None,
        date_from=date_from, date_to=date_to,
    )


# =============================================================================
# REPORTS - JOURNEY PERFORMANCE
# =============================================================================

@mkt_bp.route('/reports/journeys')
@mkt_login_required
@mkt_permission_required('view_reports')
def report_journeys():
    """Journey performance report."""
    db = get_db()

    journeys = db.execute("""
        SELECT j.*,
               (SELECT COUNT(*) FROM marketing_journey_participants WHERE journey_id = j.id) as enrolled,
               (SELECT COUNT(*) FROM marketing_journey_participants WHERE journey_id = j.id AND status = 'Completed') as completed,
               (SELECT COUNT(*) FROM marketing_journey_participants WHERE journey_id = j.id AND status = 'Active') as active,
               (SELECT AVG(total_engagements) FROM marketing_journey_participants WHERE journey_id = j.id) as avg_engagements
        FROM marketing_nurture_journeys j
        ORDER BY j.created_at DESC
    """).fetchall()

    # Overall journey metrics
    overall = db.execute("""
        SELECT
            COUNT(*) as total_journeys,
            SUM(total_enrolled) as total_enrolled,
            SUM(total_completed) as total_completed,
            AVG(avg_completion_days) as avg_completion_days,
            SUM(total_enrolled) as total_participants
        FROM marketing_nurture_journeys
    """).fetchone()

    db.close()

    return render_template('marketing/report_journey.html',
        title='Journey Performance Report',
        journeys=[dict(r) for r in journeys],
        overall=dict(overall) if overall else None,
    )


# =============================================================================
# REPORTS - CHANNEL PERFORMANCE
# =============================================================================

@mkt_bp.route('/reports/channels')
@mkt_login_required
@mkt_permission_required('view_reports')
def report_channels():
    """Channel performance report."""
    db = get_db()

    date_from = request.args.get('date_from', (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

    channels = db.execute("""
        SELECT c.*,
               COALESCE(SUM(cc.leads_generated), 0) as total_leads,
               COALESCE(SUM(cc.inquiries_generated), 0) as total_inquiries,
               COALESCE(SUM(cc.sales_generated), 0) as total_sales,
               COALESCE(AVG(cc.actual_spend), 0) as avg_spend,
               CASE WHEN SUM(cc.leads_generated) > 0
                    THEN ROUND(SUM(cc.actual_spend) / SUM(cc.leads_generated), 2)
                    ELSE 0 END as cost_per_lead
        FROM marketing_channels c
        LEFT JOIN marketing_campaign_channels cc ON c.id = cc.channel_id
        LEFT JOIN marketing_campaigns camp ON cc.campaign_id = camp.id
        WHERE camp.start_date >= ? AND camp.start_date <= ?
        GROUP BY c.id
        ORDER BY total_sales DESC
    """, (date_from, date_to)).fetchall()

    db.close()

    return render_template('marketing/report_channel.html',
        title='Channel Performance Report',
        channels=[dict(r) for r in channels],
        date_from=date_from, date_to=date_to,
    )


# =============================================================================
# REPORTS - ATTRIBUTION
# =============================================================================

@mkt_bp.route('/reports/attribution')
@mkt_login_required
@mkt_permission_required('view_reports')
def report_attribution():
    """Marketing attribution report."""
    db = get_db()

    # Attribution by campaign
    campaign_attr = db.execute("""
        SELECT c.name, c.campaign_type,
               COUNT(DISTINCT a.customer_id) as attributed_customers,
               SUM(a.revenue_generated) as attributed_revenue,
               SUM(a.profit_generated) as attributed_profit,
               COUNT(DISTINCT CASE WHEN a.is_conversion = 1 THEN a.customer_id END) as conversions
        FROM marketing_attribution a
        JOIN marketing_campaigns c ON a.campaign_id = c.id
        GROUP BY c.id
        ORDER BY attributed_revenue DESC
    """).fetchall()

    # Attribution by channel
    channel_attr = db.execute("""
        SELECT ch.name as channel_name, ch.channel_type,
               COUNT(DISTINCT a.customer_id) as attributed_customers,
               SUM(a.revenue_generated) as attributed_revenue,
               SUM(a.profit_generated) as attributed_profit
        FROM marketing_attribution a
        JOIN marketing_channels ch ON a.channel_id = ch.id
        GROUP BY ch.id
        ORDER BY attributed_revenue DESC
    """).fetchall()

    # Attribution model comparison
    models = db.execute("SELECT * FROM marketing_attribution_models WHERE is_active = 1").fetchall()

    db.close()

    return render_template('marketing/report_attribution.html',
        title='Attribution Report',
        campaign_attr=[dict(r) for r in campaign_attr],
        channel_attr=[dict(r) for r in channel_attr],
        models=[dict(r) for r in models],
    )


# =============================================================================
# MARKETING SETTINGS
# =============================================================================

@mkt_bp.route('/settings/view')
@mkt_login_required
@mkt_permission_required('manage_settings')
def settings_view():
    """View marketing settings."""
    db = get_db()

    settings = db.execute("""
        SELECT * FROM marketing_settings
        WHERE is_active = 1
        ORDER BY category, setting_key
    """).fetchall()

    # Group by category
    settings_by_cat = {}
    for s in settings:
        cat = s['category']
        if cat not in settings_by_cat:
            settings_by_cat[cat] = []
        settings_by_cat[cat].append(dict(s))

    db.close()

    return render_template('marketing/settings.html',
        title='Marketing Settings',
        settings_by_cat=settings_by_cat,
    )


# =============================================================================
# MARKETING NOTIFICATIONS
# =============================================================================

@mkt_bp.route('/notifications/read/<int:id>', methods=['POST'])
@mkt_login_required
def notifications_read(id):
    """Mark notification as read."""
    db = get_db()

    db.execute("""
        UPDATE marketing_notifications SET
            is_read = 1, read_at = CURRENT_TIMESTAMP
        WHERE id = ? AND recipient_user_id = ?
    """, (id, session['user_id']))

    db.commit()
    db.close()

    return jsonify({'success': True})


# =============================================================================
# EXPORT ENDPOINTS - ALL 20 EXPORT TYPES
# =============================================================================

MARKETING_EXPORT_TYPES = [
    'csv', 'excel_text', 'excel_general', 'json', 'xml', 'txt',
    'pdf', 'docx', 'html', 'printable', 'barcode', 'api',
    'email', 'zip', 'backup', 'sql_dump', 'dashboard',
    'summary', 'detailed', 'audit_log'
]

MARKETING_EXPORT_COLUMNS = {
    'campaigns': ['campaign_id', 'name', 'channel', 'status', 'start_date', 'budget', 'spent', 'roi'],
    'leads': ['lead_id', 'name', 'email', 'source', 'status', 'score', 'created_at'],
    'channels': ['channel_name', 'type', 'status', 'total_campaigns', 'total_budget'],
    'content': ['content_id', 'title', 'type', 'status', 'publish_date', 'views'],
    'offers': ['offer_id', 'title', 'type', 'discount', 'start_date', 'end_date', 'status'],
    'budgets': ['budget_id', 'category', 'allocated', 'spent', 'remaining', 'period'],
    'performance': ['metric', 'value', 'change', 'period', 'trend'],
    'segments': ['segment_id', 'name', 'criteria', 'member_count', 'created_at']
}


@mkt_bp.route('/api/export/<export_type>', methods=['GET', 'POST'])
@mkt_bp.route('/api/export/<data_type>/<export_type>', methods=['GET', 'POST'])
@mkt_permission_required('reports')
def api_marketing_export(export_type, data_type=None):
    """Export marketing data in all 20 formats."""
    if export_type not in MARKETING_EXPORT_TYPES:
        return jsonify({
            'error': f'Invalid export type. Valid types: {MARKETING_EXPORT_TYPES}'
        }), 400

    company_id = session.get('company_id', 0)

    # Determine data type from URL or default
    if data_type is None:
        data_type = request.args.get('type', 'campaigns')

    # Get data based on type
    if data_type == 'campaigns':
        db = get_db()
        data = db.execute("""
            SELECT * FROM marketing_campaigns
            ORDER BY created_at DESC
            LIMIT 5000
        """).fetchall()
        data = [dict(row) for row in data]
        columns = MARKETING_EXPORT_COLUMNS['campaigns']
        title = 'Marketing Campaigns'
    elif data_type == 'leads':
        db = get_db()
        data = db.execute("""
            SELECT * FROM marketing_leads
            ORDER BY created_at DESC
            LIMIT 5000
        """).fetchall()
        data = [dict(row) for row in data]
        columns = MARKETING_EXPORT_COLUMNS['leads']
        title = 'Marketing Leads'
    elif data_type == 'channels':
        db = get_db()
        data = db.execute("""
            SELECT * FROM marketing_channels
            ORDER BY channel_name
            LIMIT 5000
        """).fetchall()
        data = [dict(row) for row in data]
        columns = MARKETING_EXPORT_COLUMNS['channels']
        title = 'Marketing Channels'
    elif data_type == 'content':
        db = get_db()
        data = db.execute("""
            SELECT * FROM marketing_content
            ORDER BY created_at DESC
            LIMIT 5000
        """).fetchall()
        data = [dict(row) for row in data]
        columns = MARKETING_EXPORT_COLUMNS['content']
        title = 'Marketing Content'
    elif data_type == 'offers':
        db = get_db()
        data = db.execute("""
            SELECT * FROM marketing_offers
            ORDER BY created_at DESC
            LIMIT 5000
        """).fetchall()
        data = [dict(row) for row in data]
        columns = MARKETING_EXPORT_COLUMNS['offers']
        title = 'Marketing Offers'
    elif data_type == 'budgets':
        db = get_db()
        data = db.execute("""
            SELECT * FROM marketing_budgets
            ORDER BY period DESC
            LIMIT 5000
        """).fetchall()
        data = [dict(row) for row in data]
        columns = MARKETING_EXPORT_COLUMNS['budgets']
        title = 'Marketing Budgets'
    elif data_type == 'segments':
        db = get_db()
        data = db.execute("""
            SELECT * FROM marketing_customer_segments
            ORDER BY created_at DESC
            LIMIT 5000
        """).fetchall()
        data = [dict(row) for row in data]
        columns = MARKETING_EXPORT_COLUMNS['segments']
        title = 'Customer Segments'
    else:
        return jsonify({'error': f'Data type {data_type} not supported'}), 400

    filename = f'marketing_{data_type}_{datetime.now().strftime("%Y%m%d")}'

    return send_export_response(data, export_type, filename, columns, title)


@mkt_bp.route('/api/export/list')
@mkt_permission_required('reports')
def list_marketing_export_types():
    """List available export types for marketing module."""
    return jsonify({
        'module': 'marketing',
        'data_types': list(MARKETING_EXPORT_COLUMNS.keys()),
        'export_types': [{'type': t} for t in MARKETING_EXPORT_TYPES]
    })


# =============================================================================
# REGISTER ROUTES WITH APP
# =============================================================================

def register_marketing_routes(app):
    """Register marketing routes with the Flask app."""
    app.register_blueprint(mkt_bp)
