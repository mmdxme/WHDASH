"""
Social Media Management System - Routes and API Endpoints
========================================================
This file contains all Flask routes and API endpoints for the Social Media Management System.

Routes are organized by section:
1. Dashboard
2. Accounts & Platforms
3. Content Calendar
4. Content Production & Archive
5. Publishing & Scheduling
6. Messages & Interactions
7. Leads & Conversion
8. Campaigns & Advertising
9. Brand & Market Monitoring
10. Reports & Analytics
11. Settings
12. Roles & Permissions

Each route has proper authentication, permission checks, input validation, error handling, and audit logging.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file, Response
from functools import wraps
from datetime import datetime, timedelta, date
import sqlite3
import json
import csv
import io
from social_media_models import (
    get_db, run_social_media_migrations, get_social_setting, update_social_setting,
    log_social_audit, get_social_dashboard_data, get_campaign_summary_stats,
    get_content_performance, SOCIAL_MEDIA_TABLES
)

sm_bp = Blueprint('social_media', __name__, url_prefix='/social-media')


# =============================================================================
# DECORATORS AND HELPERS
# =============================================================================

def sm_login_required(f):
    """Decorator to require social media module login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please log in first.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def sm_permission_required(permission: str):
    """Decorator to check social media-specific permissions."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Please log in first.', 'error')
                return redirect(url_for('login'))
            
            # Super admin bypass
            if session.get('role_name') == 'Global Admin':
                return f(*args, **kwargs)
            
            # Check specific social media permissions from session or role
            sm_permissions = session.get('social_media_permissions', [])
            if 'all_social_media' in sm_permissions or permission in sm_permissions:
                return f(*args, **kwargs)
            
            flash('You do not have permission to access this Social Media module.', 'error')
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


def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed."""
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'mp4', 'mov', 'avi'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


# =============================================================================
# SOCIAL MEDIA DASHBOARD
# =============================================================================

@sm_bp.route('/')
@sm_bp.route('/dashboard')
@sm_login_required
def social_dashboard():
    """Main social media dashboard with KPIs and summaries."""
    db = get_db()
    
    # Get date filters
    date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
    platform = request.args.get('platform', '')
    
    # Get dashboard data
    dash_data = get_social_dashboard_data(db, date_from=date_from, date_to=date_to, platform=platform)
    
    # Get recent campaigns
    recent_campaigns = db.execute("""
        SELECT id, campaign_name, campaign_type, campaign_status, start_date, end_date,
               approved_budget, actual_budget, total_leads, total_sales, roas
        FROM social_campaigns
        ORDER BY created_at DESC
        LIMIT 10
    """).fetchall()
    
    # Get pending content
    pending_content = db.execute("""
        SELECT id, internal_title, target_platform, production_status, approval_status, priority
        FROM social_content_production
        WHERE production_status IN ('Ready for Review', 'Ready for Publishing')
        ORDER BY priority ASC, created_at DESC
        LIMIT 10
    """).fetchall()
    
    # Get open alerts
    open_alerts = db.execute("""
        SELECT id, alert_type, alert_title, severity, entity_name, created_at
        FROM social_alerts
        WHERE is_resolved = 0
        ORDER BY created_at DESC
        LIMIT 10
    """).fetchall()
    
    # Get message summary
    message_summary = db.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN is_unread = 1 THEN 1 ELSE 0 END) as unread,
            SUM(CASE WHEN thread_status = 'Open' AND is_unread = 1 THEN 1 ELSE 0 END) as unanswered
        FROM social_message_threads
        WHERE is_archived = 0
    """).fetchone()
    
    # Get lead summary
    lead_summary = db.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN lead_status = 'New' THEN 1 ELSE 0 END) as new_leads,
            SUM(CASE WHEN lead_status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
            SUM(CASE WHEN lead_status = 'Converted' THEN 1 ELSE 0 END) as converted
        FROM social_leads
    """).fetchone()
    
    # Get platform list for filter
    platforms = db.execute("""
        SELECT DISTINCT platform FROM social_accounts WHERE inactive_archive = 0
    """).fetchall()
    
    db.close()
    
    return render_template('social_media/dashboard.html',
        title='Social Media Dashboard',
        dash_data=dash_data,
        recent_campaigns=[dict(r) for r in recent_campaigns],
        pending_content=[dict(r) for r in pending_content],
        open_alerts=[dict(r) for r in open_alerts],
        message_summary=dict(message_summary) if message_summary else {},
        lead_summary=dict(lead_summary) if lead_summary else {},
        platforms=[r['platform'] for r in platforms],
        date_from=date_from,
        date_to=date_to,
        platform_filter=platform,
    )


# =============================================================================
# ACCOUNTS & PLATFORMS
# =============================================================================

@sm_bp.route('/accounts')
@sm_login_required
@sm_permission_required('view_accounts')
def accounts_list():
    """List all social media accounts."""
    db = get_db()
    
    # Pagination
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    # Filters
    search = request.args.get('search', '')
    platform = request.args.get('platform', '')
    status = request.args.get('status', '')
    
    # Build query
    query = "SELECT * FROM social_accounts WHERE 1=1"
    count_query = "SELECT COUNT(*) as cnt FROM social_accounts WHERE 1=1"
    params = []
    
    if search:
        query += " AND (account_name LIKE ? OR username LIKE ? OR account_link LIKE ?)"
        count_query += " AND (account_name LIKE ? OR username LIKE ? OR account_link LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
    
    if platform:
        query += " AND platform = ?"
        count_query += " AND platform = ?"
        params.append(platform)
    
    if status:
        query += " AND account_status = ?"
        count_query += " AND account_status = ?"
        params.append(status)
    
    # Get total count
    total = db.execute(count_query, params).fetchone()['cnt']
    
    # Add pagination
    query += " ORDER BY platform, account_name LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    accounts = db.execute(query, params).fetchall()
    platforms = db.execute("SELECT DISTINCT platform FROM social_accounts").fetchall()
    
    db.close()
    
    return render_template('social_media/accounts/list.html',
        title='Social Accounts',
        accounts=[dict(r) for r in accounts],
        platforms=[r['platform'] for r in platforms],
        total=total,
        page=page,
        per_page=per_page,
        search=search,
        platform_filter=platform,
        status_filter=status,
    )


@sm_bp.route('/accounts/new', methods=['GET', 'POST'])
@sm_login_required
@sm_permission_required('create_accounts')
def accounts_new():
    """Create a new social media account."""
    db = get_db()
    
    if request.method == 'POST':
        platform = request.form.get('platform', '').strip()
        account_name = request.form.get('account_name', '').strip()
        username = request.form.get('username', '').strip()
        account_link = request.form.get('account_link', '').strip()
        company_id = request.form.get('company_id')
        target_market = request.form.get('target_market', '').strip()
        primary_language = request.form.get('primary_language', 'en').strip()
        account_type = request.form.get('account_type', 'Business').strip()
        account_status = request.form.get('account_status', 'Active').strip()
        connected_email = request.form.get('connected_email', '').strip()
        connected_mobile = request.form.get('connected_mobile', '').strip()
        two_factor_enabled = 1 if request.form.get('two_factor_enabled') else 0
        business_manager_id = request.form.get('business_manager_id', '').strip()
        pixel_tracking_id = request.form.get('pixel_tracking_id', '').strip()
        whatsapp_linked_number = request.form.get('whatsapp_linked_number', '').strip()
        website_linked_url = request.form.get('website_linked_url', '').strip()
        notes = request.form.get('notes', '').strip()
        
        # Validation
        if not platform or not account_name:
            flash('Platform and Account Name are required.', 'error')
            return render_template('social_media/accounts/new.html', title='New Account')
        
        # Check duplicate
        existing = db.execute("""
            SELECT id FROM social_accounts WHERE platform = ? AND username = ?
        """, (platform, username)).fetchone()
        
        if existing:
            flash('An account with this platform and username already exists.', 'error')
            return render_template('social_media/accounts/new.html', title='New Account')
        
        # Insert new account
        cursor = db.execute("""
            INSERT INTO social_accounts (
                platform, account_name, username, account_link, company_id, target_market,
                primary_language, account_type, account_status, connected_email, connected_mobile,
                two_factor_enabled, business_manager_id, pixel_tracking_id, whatsapp_linked_number,
                website_linked_url, notes, created_by_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (platform, account_name, username, account_link, company_id, target_market,
              primary_language, account_type, account_status, connected_email, connected_mobile,
              two_factor_enabled, business_manager_id, pixel_tracking_id, whatsapp_linked_number,
              website_linked_url, notes, session.get('user_id')))
        db.commit()
        
        account_id = cursor.lastrowid
        
        # Log audit
        log_social_audit(db, 'social_accounts', account_id, 'CREATE', 
                         user_id=session.get('user_id'))
        
        flash(f'Social account "{account_name}" created successfully.', 'success')
        return redirect(url_for('social_media.accounts_list'))
    
    companies = db.execute("SELECT id, name FROM companies").fetchall()
    db.close()
    
    return render_template('social_media/accounts/new.html',
        title='New Social Account',
        companies=[dict(r) for r in companies],
    )


@sm_bp.route('/accounts/edit/<int:id>', methods=['GET', 'POST'])
@sm_login_required
@sm_permission_required('edit_accounts')
def accounts_edit(id):
    """Edit an existing social media account."""
    db = get_db()
    
    account = db.execute("SELECT * FROM social_accounts WHERE id = ?", (id,)).fetchone()
    if not account:
        flash('Account not found.', 'error')
        return redirect(url_for('social_media.accounts_list'))
    
    if request.method == 'POST':
        platform = request.form.get('platform', '').strip()
        account_name = request.form.get('account_name', '').strip()
        username = request.form.get('username', '').strip()
        account_link = request.form.get('account_link', '').strip()
        company_id = request.form.get('company_id')
        target_market = request.form.get('target_market', '').strip()
        primary_language = request.form.get('primary_language', 'en').strip()
        account_type = request.form.get('account_type', 'Business').strip()
        account_status = request.form.get('account_status', 'Active').strip()
        connected_email = request.form.get('connected_email', '').strip()
        connected_mobile = request.form.get('connected_mobile', '').strip()
        two_factor_enabled = 1 if request.form.get('two_factor_enabled') else 0
        business_manager_id = request.form.get('business_manager_id', '').strip()
        pixel_tracking_id = request.form.get('pixel_tracking_id', '').strip()
        whatsapp_linked_number = request.form.get('whatsapp_linked_number', '').strip()
        website_linked_url = request.form.get('website_linked_url', '').strip()
        notes = request.form.get('notes', '').strip()
        
        # Validation
        if not platform or not account_name:
            flash('Platform and Account Name are required.', 'error')
            return render_template('social_media/accounts/edit.html', title='Edit Account', account=dict(account))
        
        # Update account
        db.execute("""
            UPDATE social_accounts SET
                platform = ?, account_name = ?, username = ?, account_link = ?,
                company_id = ?, target_market = ?, primary_language = ?, account_type = ?,
                account_status = ?, connected_email = ?, connected_mobile = ?,
                two_factor_enabled = ?, business_manager_id = ?, pixel_tracking_id = ?,
                whatsapp_linked_number = ?, website_linked_url = ?, notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (platform, account_name, username, account_link, company_id, target_market,
              primary_language, account_type, account_status, connected_email, connected_mobile,
              two_factor_enabled, business_manager_id, pixel_tracking_id, whatsapp_linked_number,
              website_linked_url, notes, id))
        db.commit()
        
        # Log audit
        log_social_audit(db, 'social_accounts', id, 'UPDATE',
                         user_id=session.get('user_id'))
        
        flash(f'Account "{account_name}" updated successfully.', 'success')
        return redirect(url_for('social_media.accounts_list'))
    
    companies = db.execute("SELECT id, name FROM companies").fetchall()
    db.close()
    
    return render_template('social_media/accounts/edit.html',
        title='Edit Social Account',
        account=dict(account),
        companies=[dict(r) for r in companies],
    )


@sm_bp.route('/accounts/delete/<int:id>', methods=['POST'])
@sm_login_required
@sm_permission_required('delete_accounts')
def accounts_delete(id):
    """Delete a social media account."""
    db = get_db()
    
    account = db.execute("SELECT * FROM social_accounts WHERE id = ?", (id,)).fetchone()
    if not account:
        flash('Account not found.', 'error')
        return redirect(url_for('social_media.accounts_list'))
    
    # Archive instead of delete
    db.execute("UPDATE social_accounts SET inactive_archive = 1, account_status = 'Archived' WHERE id = ?", (id,))
    db.commit()
    
    log_social_audit(db, 'social_accounts', id, 'ARCHIVE',
                     user_id=session.get('user_id'))
    
    flash(f'Account "{account["account_name"]}" archived successfully.', 'success')
    return redirect(url_for('social_media.accounts_list'))


@sm_bp.route('/accounts/view/<int:id>')
@sm_login_required
@sm_permission_required('view_accounts')
def accounts_view(id):
    """View social media account details."""
    db = get_db()
    
    account = db.execute("SELECT * FROM social_accounts WHERE id = ?", (id,)).fetchone()
    if not account:
        flash('Account not found.', 'error')
        return redirect(url_for('social_media.accounts_list'))
    
    # Get recent performance
    recent_content = db.execute("""
        SELECT * FROM social_content_archive
        WHERE linked_account_id = ?
        ORDER BY published_at DESC
        LIMIT 10
    """, (id,)).fetchall()
    
    # Get message stats
    message_stats = db.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN is_unread = 1 THEN 1 ELSE 0 END) as unread
        FROM social_message_threads
        WHERE account_id = ?
    """, (id,)).fetchone()
    
    db.close()
    
    return render_template('social_media/accounts/view.html',
        title='Account Details',
        account=dict(account),
        recent_content=[dict(r) for r in recent_content],
        message_stats=dict(message_stats) if message_stats else {},
    )


# =============================================================================
# CONTENT PRODUCTION
# =============================================================================

@sm_bp.route('/content')
@sm_login_required
@sm_permission_required('view_content')
def content_list():
    """List all content production items."""
    db = get_db()
    
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    platform = request.args.get('platform', '')
    
    query = "SELECT * FROM social_content_production WHERE 1=1"
    count_query = "SELECT COUNT(*) as cnt FROM social_content_production WHERE 1=1"
    params = []
    
    if search:
        query += " AND (internal_title LIKE ? OR display_title LIKE ?)"
        count_query += " AND (internal_title LIKE ? OR display_title LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
    
    if status:
        query += " AND production_status = ?"
        count_query += " AND production_status = ?"
        params.append(status)
    
    if platform:
        query += " AND target_platform = ?"
        count_query += " AND target_platform = ?"
        params.append(platform)
    
    total = db.execute(count_query, params).fetchone()['cnt']
    query += " ORDER BY priority ASC, created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    content_items = db.execute(query, params).fetchall()
    
    db.close()
    
    return render_template('social_media/content/list.html',
        title='Content Production',
        content_items=[dict(r) for r in content_items],
        total=total,
        page=page,
        per_page=per_page,
        search=search,
        status_filter=status,
        platform_filter=platform,
    )


@sm_bp.route('/content/new', methods=['GET', 'POST'])
@sm_login_required
@sm_permission_required('create_content')
def content_new():
    """Create new content production item."""
    db = get_db()
    
    if request.method == 'POST':
        internal_title = request.form.get('internal_title', '').strip()
        display_title = request.form.get('display_title', '').strip()
        target_platform = request.form.get('target_platform', '').strip()
        content_type = request.form.get('content_type', '').strip()
        content_format = request.form.get('content_format', '').strip()
        content_pillar = request.form.get('content_pillar', '').strip()
        topic = request.form.get('topic', '').strip()
        content_objective = request.form.get('content_objective', '').strip()
        target_audience = request.form.get('target_audience', '').strip()
        language = request.form.get('language', 'en').strip()
        caption = request.form.get('caption', '').strip()
        hook = request.form.get('hook', '').strip()
        cta_text = request.form.get('cta_text', '').strip()
        hashtags = request.form.get('hashtags', '').strip()
        keywords = request.form.get('keywords', '').strip()
        related_brand = request.form.get('related_brand', '').strip()
        related_products = request.form.get('related_products', '').strip()
        related_skus = request.form.get('related_skus', '').strip()
        destination_link = request.form.get('destination_link', '').strip()
        priority = int(request.form.get('priority', 3))
        production_status = request.form.get('production_status', 'Idea').strip()
        notes = request.form.get('notes', '').strip()
        
        # Generate content code
        content_code = f"SC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # Validation
        if not internal_title or not target_platform:
            flash('Internal Title and Target Platform are required.', 'error')
            return render_template('social_media/content/new.html', title='New Content')
        
        cursor = db.execute("""
            INSERT INTO social_content_production (
                content_code, internal_title, display_title, target_platform, content_type,
                content_format, content_pillar, topic, content_objective, target_audience,
                language, caption, hook, cta_text, hashtags, keywords, related_brand,
                related_products, related_skus, destination_link, priority, production_status,
                notes, creator_id, created_by_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (content_code, internal_title, display_title, target_platform, content_type,
              content_format, content_pillar, topic, content_objective, target_audience,
              language, caption, hook, cta_text, hashtags, keywords, related_brand,
              related_products, related_skus, destination_link, priority, production_status,
              notes, session.get('user_id'), session.get('user_id')))
        db.commit()
        
        content_id = cursor.lastrowid
        log_social_audit(db, 'social_content_production', content_id, 'CREATE',
                         user_id=session.get('user_id'))
        
        flash(f'Content "{internal_title}" created successfully.', 'success')
        return redirect(url_for('social_media.content_list'))
    
    # Get dropdown values from settings
    platforms = db.execute("SELECT setting_value FROM social_settings WHERE setting_key LIKE 'instagram_handle' OR setting_key LIKE 'facebook_page'").fetchall()
    
    # Get campaigns for linking
    campaigns = db.execute("""
        SELECT id, campaign_name FROM social_campaigns 
        WHERE campaign_status IN ('Active', 'Draft')
    """).fetchall()
    
    db.close()
    
    return render_template('social_media/content/new.html',
        title='New Content',
        campaigns=[dict(r) for r in campaigns],
    )


@sm_bp.route('/content/edit/<int:id>', methods=['GET', 'POST'])
@sm_login_required
@sm_permission_required('edit_content')
def content_edit(id):
    """Edit content production item."""
    db = get_db()
    
    content = db.execute("SELECT * FROM social_content_production WHERE id = ?", (id,)).fetchone()
    if not content:
        flash('Content not found.', 'error')
        return redirect(url_for('social_media.content_list'))
    
    if request.method == 'POST':
        display_title = request.form.get('display_title', '').strip()
        target_platform = request.form.get('target_platform', '').strip()
        content_type = request.form.get('content_type', '').strip()
        content_format = request.form.get('content_format', '').strip()
        content_pillar = request.form.get('content_pillar', '').strip()
        topic = request.form.get('topic', '').strip()
        content_objective = request.form.get('content_objective', '').strip()
        target_audience = request.form.get('target_audience', '').strip()
        language = request.form.get('language', 'en').strip()
        caption = request.form.get('caption', '').strip()
        hook = request.form.get('hook', '').strip()
        cta_text = request.form.get('cta_text', '').strip()
        hashtags = request.form.get('hashtags', '').strip()
        keywords = request.form.get('keywords', '').strip()
        related_brand = request.form.get('related_brand', '').strip()
        related_products = request.form.get('related_products', '').strip()
        related_skus = request.form.get('related_skus', '').strip()
        destination_link = request.form.get('destination_link', '').strip()
        priority = int(request.form.get('priority', 3))
        production_status = request.form.get('production_status', 'Idea').strip()
        notes = request.form.get('notes', '').strip()
        
        db.execute("""
            UPDATE social_content_production SET
                display_title = ?, target_platform = ?, content_type = ?, content_format = ?,
                content_pillar = ?, topic = ?, content_objective = ?, target_audience = ?,
                language = ?, caption = ?, hook = ?, cta_text = ?, hashtags = ?, keywords = ?,
                related_brand = ?, related_products = ?, related_skus = ?, destination_link = ?,
                priority = ?, production_status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (display_title, target_platform, content_type, content_format,
              content_pillar, topic, content_objective, target_audience,
              language, caption, hook, cta_text, hashtags, keywords,
              related_brand, related_products, related_skus, destination_link,
              priority, production_status, notes, id))
        db.commit()
        
        log_social_audit(db, 'social_content_production', id, 'UPDATE',
                         user_id=session.get('user_id'))
        
        flash('Content updated successfully.', 'success')
        return redirect(url_for('social_media.content_list'))
    
    campaigns = db.execute("""
        SELECT id, campaign_name FROM social_campaigns 
        WHERE campaign_status IN ('Active', 'Draft')
    """).fetchall()
    
    db.close()
    
    return render_template('social_media/content/edit.html',
        title='Edit Content',
        content=dict(content),
        campaigns=[dict(r) for r in campaigns],
    )


@sm_bp.route('/content/view/<int:id>')
@sm_login_required
@sm_permission_required('view_content')
def content_view(id):
    """View content production item details."""
    db = get_db()
    
    content = db.execute("""
        SELECT c.*, u.username as creator_name
        FROM social_content_production c
        LEFT JOIN users u ON c.creator_id = u.id
        WHERE c.id = ?
    """, (id,)).fetchone()
    
    if not content:
        flash('Content not found.', 'error')
        return redirect(url_for('social_media.content_list'))
    
    # Get related calendar items
    calendar_items = db.execute("""
        SELECT * FROM social_content_calendar WHERE content_id = ?
        ORDER BY publish_date DESC
    """, (id,)).fetchall()
    
    # Get related archive items
    archive_items = db.execute("""
        SELECT * FROM social_content_archive WHERE content_code = ?
        ORDER BY published_at DESC
    """, (content['content_code'],)).fetchall()
    
    db.close()
    
    return render_template('social_media/content/view.html',
        title='Content Details',
        content=dict(content),
        calendar_items=[dict(r) for r in calendar_items],
        archive_items=[dict(r) for r in archive_items],
    )


@sm_bp.route('/content/delete/<int:id>', methods=['POST'])
@sm_login_required
@sm_permission_required('delete_content')
def content_delete(id):
    """Delete content production item."""
    db = get_db()
    
    content = db.execute("SELECT * FROM social_content_production WHERE id = ?", (id,)).fetchone()
    if not content:
        flash('Content not found.', 'error')
        return redirect(url_for('social_media.content_list'))
    
    db.execute("DELETE FROM social_content_production WHERE id = ?", (id,))
    db.commit()
    
    log_social_audit(db, 'social_content_production', id, 'DELETE',
                     user_id=session.get('user_id'))
    
    flash('Content deleted successfully.', 'success')
    return redirect(url_for('social_media.content_list'))


# =============================================================================
# CONTENT CALENDAR
# =============================================================================

@sm_bp.route('/calendar')
@sm_login_required
@sm_permission_required('view_calendar')
def content_calendar():
    """Content calendar view."""
    db = get_db()
    
    # Get view type (daily, weekly, monthly)
    view = request.args.get('view', 'monthly')
    current_date = datetime.now()
    
    if view == 'daily':
        date_from = current_date.strftime('%Y-%m-%d')
        date_to = date_from
    elif view == 'weekly':
        start_of_week = current_date - timedelta(days=current_date.weekday())
        date_from = start_of_week.strftime('%Y-%m-%d')
        date_to = (start_of_week + timedelta(days=6)).strftime('%Y-%m-%d')
    else:  # monthly
        date_from = current_date.replace(day=1).strftime('%Y-%m-%d')
        last_day = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        date_to = last_day.strftime('%Y-%m-%d')
    
    # Get calendar items
    calendar_items = db.execute("""
        SELECT c.*, p.internal_title, p.display_title, p.caption, p.hashtags,
               a.account_name
        FROM social_content_calendar c
        LEFT JOIN social_content_production p ON c.content_id = p.id
        LEFT JOIN social_accounts a ON c.platform = a.platform
        WHERE c.publish_date BETWEEN ? AND ?
        ORDER BY c.publish_date, c.publish_time
    """, (date_from, date_to)).fetchall()
    
    # Group by date
    calendar_by_date = {}
    for item in calendar_items:
        date_key = item['publish_date']
        if date_key not in calendar_by_date:
            calendar_by_date[date_key] = []
        calendar_by_date[date_key].append(dict(item))
    
    # Get platforms for filter
    platforms = db.execute("SELECT DISTINCT platform FROM social_accounts WHERE inactive_archive = 0").fetchall()
    
    db.close()
    
    return render_template('social_media/calendar/calendar.html',
        title='Content Calendar',
        calendar_items=[dict(r) for r in calendar_items],
        calendar_by_date=calendar_by_date,
        platforms=[r['platform'] for r in platforms],
        view=view,
        date_from=date_from,
        date_to=date_to,
    )


@sm_bp.route('/calendar/new', methods=['GET', 'POST'])
@sm_login_required
@sm_permission_required('create_calendar')
def calendar_new():
    """Add item to content calendar."""
    db = get_db()
    
    if request.method == 'POST':
        content_id = request.form.get('content_id')
        publish_date = request.form.get('publish_date', '').strip()
        publish_time = request.form.get('publish_time', '').strip()
        platform = request.form.get('platform', '').strip()
        content_type = request.form.get('content_type', '').strip()
        content_topic = request.form.get('content_topic', '').strip()
        content_objective = request.form.get('content_objective', '').strip()
        target_audience = request.form.get('target_audience', '').strip()
        target_market = request.form.get('target_market', '').strip()
        linked_campaign_id = request.form.get('linked_campaign_id')
        related_product = request.form.get('related_product', '').strip()
        related_brand = request.form.get('related_brand', '').strip()
        cta = request.form.get('cta', '').strip()
        calendar_status = request.form.get('calendar_status', 'Scheduled').strip()
        priority = int(request.form.get('priority', 3))
        timezone = request.form.get('timezone', 'Asia/Dubai').strip()
        notes = request.form.get('notes', '').strip()
        
        if not publish_date or not platform:
            flash('Publish Date and Platform are required.', 'error')
            return render_template('social_media/calendar/new.html', title='New Calendar Item')
        
        cursor = db.execute("""
            INSERT INTO social_content_calendar (
                content_id, publish_date, publish_time, platform, content_type,
                content_topic, content_objective, target_audience, target_market,
                linked_campaign_id, related_product, related_brand, cta,
                calendar_status, priority, timezone, notes, created_by_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (content_id, publish_date, publish_time, platform, content_type,
              content_topic, content_objective, target_audience, target_market,
              linked_campaign_id, related_product, related_brand, cta,
              calendar_status, priority, timezone, notes, session.get('user_id')))
        db.commit()
        
        log_social_audit(db, 'social_content_calendar', cursor.lastrowid, 'CREATE',
                         user_id=session.get('user_id'))
        
        flash('Calendar item added successfully.', 'success')
        return redirect(url_for('social_media.content_calendar'))
    
    # Get content items for dropdown
    content_items = db.execute("""
        SELECT id, content_code, internal_title, target_platform
        FROM social_content_production
        WHERE production_status IN ('Ready for Publishing', 'Approved')
    """).fetchall()
    
    # Get campaigns
    campaigns = db.execute("SELECT id, campaign_name FROM social_campaigns").fetchall()
    
    # Get platforms
    platforms = db.execute("SELECT DISTINCT platform FROM social_accounts WHERE inactive_archive = 0").fetchall()
    
    db.close()
    
    return render_template('social_media/calendar/new.html',
        title='New Calendar Item',
        content_items=[dict(r) for r in content_items],
        campaigns=[dict(r) for r in campaigns],
        platforms=[r['platform'] for r in platforms],
    )


@sm_bp.route('/calendar/edit/<int:id>', methods=['GET', 'POST'])
@sm_login_required
@sm_permission_required('edit_calendar')
def calendar_edit(id):
    """Edit calendar item."""
    db = get_db()
    
    item = db.execute("SELECT * FROM social_content_calendar WHERE id = ?", (id,)).fetchone()
    if not item:
        flash('Calendar item not found.', 'error')
        return redirect(url_for('social_media.content_calendar'))
    
    if request.method == 'POST':
        publish_date = request.form.get('publish_date', '').strip()
        publish_time = request.form.get('publish_time', '').strip()
        platform = request.form.get('platform', '').strip()
        content_type = request.form.get('content_type', '').strip()
        calendar_status = request.form.get('calendar_status', 'Scheduled').strip()
        priority = int(request.form.get('priority', 3))
        notes = request.form.get('notes', '').strip()
        
        db.execute("""
            UPDATE social_content_calendar SET
                publish_date = ?, publish_time = ?, platform = ?, content_type = ?,
                calendar_status = ?, priority = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (publish_date, publish_time, platform, content_type,
              calendar_status, priority, notes, id))
        db.commit()
        
        log_social_audit(db, 'social_content_calendar', id, 'UPDATE',
                         user_id=session.get('user_id'))
        
        flash('Calendar item updated successfully.', 'success')
        return redirect(url_for('social_media.content_calendar'))
    
    campaigns = db.execute("SELECT id, campaign_name FROM social_campaigns").fetchall()
    platforms = db.execute("SELECT DISTINCT platform FROM social_accounts WHERE inactive_archive = 0").fetchall()
    
    db.close()
    
    return render_template('social_media/calendar/edit.html',
        title='Edit Calendar Item',
        item=dict(item),
        campaigns=[dict(r) for r in campaigns],
        platforms=[r['platform'] for r in platforms],
    )


@sm_bp.route('/calendar/delete/<int:id>', methods=['POST'])
@sm_login_required
@sm_permission_required('delete_calendar')
def calendar_delete(id):
    """Delete calendar item."""
    db = get_db()
    
    item = db.execute("SELECT * FROM social_content_calendar WHERE id = ?", (id,)).fetchone()
    if not item:
        flash('Calendar item not found.', 'error')
        return redirect(url_for('social_media.content_calendar'))
    
    db.execute("DELETE FROM social_content_calendar WHERE id = ?", (id,))
    db.commit()
    
    log_social_audit(db, 'social_content_calendar', id, 'DELETE',
                     user_id=session.get('user_id'))
    
    flash('Calendar item deleted successfully.', 'success')
    return redirect(url_for('social_media.content_calendar'))


# =============================================================================
# PUBLISHING & SCHEDULING
# =============================================================================

@sm_bp.route('/publishing')
@sm_login_required
@sm_permission_required('view_publishing')
def publishing_queue():
    """Publishing queue view."""
    db = get_db()
    
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    status = request.args.get('status', '')
    platform = request.args.get('platform', '')
    
    query = """
        SELECT q.*, c.internal_title, a.account_name
        FROM social_publish_queue q
        LEFT JOIN social_content_production c ON q.content_id = c.id
        LEFT JOIN social_accounts a ON q.account_id = a.id
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) as cnt FROM social_publish_queue q WHERE 1=1"
    params = []
    
    if status:
        query += " AND q.queue_status = ?"
        count_query += " AND q.queue_status = ?"
        params.append(status)
    
    if platform:
        query += " AND q.platform = ?"
        count_query += " AND q.platform = ?"
        params.append(platform)
    
    total = db.execute(count_query, params).fetchone()['cnt']
    query += " ORDER BY q.publish_date, q.publish_time LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    queue_items = db.execute(query, params).fetchall()
    
    db.close()
    
    return render_template('social_media/publishing/queue.html',
        title='Publishing Queue',
        queue_items=[dict(r) for r in queue_items],
        total=total,
        page=page,
        per_page=per_page,
        status_filter=status,
        platform_filter=platform,
    )


@sm_bp.route('/publishing/new', methods=['GET', 'POST'])
@sm_login_required
@sm_permission_required('create_publishing')
def publishing_new():
    """Create new publishing schedule."""
    db = get_db()
    
    if request.method == 'POST':
        content_id = request.form.get('content_id')
        calendar_id = request.form.get('calendar_id')
        account_id = request.form.get('account_id')
        platform = request.form.get('platform', '').strip()
        publish_date = request.form.get('publish_date', '').strip()
        publish_time = request.form.get('publish_time', '').strip()
        timezone = request.form.get('timezone', 'Asia/Dubai').strip()
        publish_type = request.form.get('publish_type', 'Scheduled').strip()
        publishing_mode = request.form.get('publishing_mode', 'Manual').strip()
        is_group_publish = 1 if request.form.get('is_group_publish') else 0
        utm_source = request.form.get('utm_source', '').strip()
        utm_medium = request.form.get('utm_medium', '').strip()
        utm_campaign = request.form.get('utm_campaign', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not publish_date or not platform:
            flash('Publish Date and Platform are required.', 'error')
            return render_template('social_media/publishing/new.html', title='New Publish')
        
        cursor = db.execute("""
            INSERT INTO social_publish_queue (
                content_id, calendar_id, account_id, platform, publish_date, publish_time,
                timezone, publish_type, publishing_mode, is_group_publish,
                utm_source, utm_medium, utm_campaign, notes, created_by_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (content_id, calendar_id, account_id, platform, publish_date, publish_time,
              timezone, publish_type, publishing_mode, is_group_publish,
              utm_source, utm_medium, utm_campaign, notes, session.get('user_id')))
        db.commit()
        
        log_social_audit(db, 'social_publish_queue', cursor.lastrowid, 'CREATE',
                         user_id=session.get('user_id'))
        
        flash('Publishing schedule created successfully.', 'success')
        return redirect(url_for('social_media.publishing_queue'))
    
    content_items = db.execute("""
        SELECT id, content_code, internal_title, target_platform, production_status
        FROM social_content_production
        WHERE production_status IN ('Ready for Publishing', 'Approved')
    """).fetchall()
    
    calendar_items = db.execute("""
        SELECT id, publish_date, platform, calendar_status
        FROM social_content_calendar
        WHERE calendar_status = 'Scheduled'
    """).fetchall()
    
    accounts = db.execute("""
        SELECT id, platform, account_name FROM social_accounts WHERE inactive_archive = 0
    """).fetchall()
    
    db.close()
    
    return render_template('social_media/publishing/new.html',
        title='New Publishing Schedule',
        content_items=[dict(r) for r in content_items],
        calendar_items=[dict(r) for r in calendar_items],
        accounts=[dict(r) for r in accounts],
    )


@sm_bp.route('/publishing/publish/<int:id>', methods=['POST'])
@sm_login_required
@sm_permission_required('publish')
def publishing_publish(id):
    """Publish content now."""
    db = get_db()
    
    queue_item = db.execute("SELECT * FROM social_publish_queue WHERE id = ?", (id,)).fetchone()
    if not queue_item:
        return jsonify({'error': 'Queue item not found'}), 404
    
    # Update queue status
    db.execute("""
        UPDATE social_publish_queue SET
            queue_status = 'Published',
            published_at = CURRENT_TIMESTAMP,
            attempts = attempts + 1,
            last_attempt_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (id,))
    
    # Add to publish history
    db.execute("""
        INSERT INTO social_publish_history (
            queue_id, content_id, account_id, platform, publish_date,
            publish_type, publishing_mode, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (id, queue_item['content_id'], queue_item['account_id'], queue_item['platform'],
          datetime.now().strftime('%Y-%m-%d %H:%M:%S'), queue_item['publish_type'],
          queue_item['publishing_mode'], 'Published'))
    
    # Update content status
    if queue_item['content_id']:
        db.execute("""
            UPDATE social_content_production SET
                production_status = 'Published',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (queue_item['content_id'],))
    
    db.commit()
    
    log_social_audit(db, 'social_publish_queue', id, 'PUBLISH',
                     user_id=session.get('user_id'))
    
    return jsonify({'success': True, 'message': 'Content published successfully.'})


@sm_bp.route('/publishing/cancel/<int:id>', methods=['POST'])
@sm_login_required
@sm_permission_required('cancel_publishing')
def publishing_cancel(id):
    """Cancel scheduled publishing."""
    db = get_db()
    
    queue_item = db.execute("SELECT * FROM social_publish_queue WHERE id = ?", (id,)).fetchone()
    if not queue_item:
        return jsonify({'error': 'Queue item not found'}), 404
    
    db.execute("""
        UPDATE social_publish_queue SET queue_status = 'Cancelled' WHERE id = ?
    """, (id,))
    db.commit()
    
    log_social_audit(db, 'social_publish_queue', id, 'CANCEL',
                     user_id=session.get('user_id'))
    
    return jsonify({'success': True, 'message': 'Publishing cancelled.'})


# =============================================================================
# MESSAGES & INTERACTIONS
# =============================================================================

@sm_bp.route('/messages')
@sm_login_required
@sm_permission_required('view_messages')
def messages_list():
    """List all message threads."""
    db = get_db()
    
    page = int(request.args.get('page', 1))
    per_page = 30
    offset = (page - 1) * per_page
    
    search = request.args.get('search', '')
    classification = request.args.get('classification', '')
    status = request.args.get('status', '')
    platform = request.args.get('platform', '')
    
    query = """
        SELECT t.*, a.account_name, u.username as responder_name
        FROM social_message_threads t
        LEFT JOIN social_accounts a ON t.account_id = a.id
        LEFT JOIN users u ON t.assigned_responder_id = u.id
        WHERE 1=1 AND t.is_archived = 0
    """
    count_query = "SELECT COUNT(*) as cnt FROM social_message_threads t WHERE 1=1 AND t.is_archived = 0"
    params = []
    
    if search:
        query += " AND (t.sender_name LIKE ? OR t.sender_username LIKE ? OR t.sender_phone LIKE ?)"
        count_query += " AND (t.sender_name LIKE ? OR t.sender_username LIKE ? OR t.sender_phone LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
    
    if classification:
        query += " AND t.message_classification = ?"
        count_query += " AND t.message_classification = ?"
        params.append(classification)
    
    if status:
        query += " AND t.thread_status = ?"
        count_query += " AND t.thread_status = ?"
        params.append(status)
    
    if platform:
        query += " AND t.platform = ?"
        count_query += " AND t.platform = ?"
        params.append(platform)
    
    total = db.execute(count_query, params).fetchone()['cnt']
    query += " ORDER BY t.last_message_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    threads = db.execute(query, params).fetchall()
    
    db.close()
    
    return render_template('social_media/messages/list.html',
        title='Messages & Interactions',
        threads=[dict(r) for r in threads],
        total=total,
        page=page,
        per_page=per_page,
        search=search,
        classification_filter=classification,
        status_filter=status,
        platform_filter=platform,
    )


@sm_bp.route('/messages/view/<int:id>')
@sm_login_required
@sm_permission_required('view_messages')
def messages_view(id):
    """View message thread details."""
    db = get_db()
    
    thread = db.execute("""
        SELECT t.*, a.account_name, u.username as responder_name
        FROM social_message_threads t
        LEFT JOIN social_accounts a ON t.account_id = a.id
        LEFT JOIN users u ON t.assigned_responder_id = u.id
        WHERE t.id = ?
    """, (id,)).fetchone()
    
    if not thread:
        flash('Thread not found.', 'error')
        return redirect(url_for('social_media.messages_list'))
    
    # Mark as read
    if thread['is_unread']:
        db.execute("UPDATE social_message_threads SET is_unread = 0 WHERE id = ?", (id,))
        db.commit()
    
    # Get messages in thread
    messages = db.execute("""
        SELECT m.*, u.username as replied_by_name
        FROM social_messages m
        LEFT JOIN users u ON m.replied_by_id = u.id
        WHERE m.thread_id = ?
        ORDER BY m.created_at ASC
    """, (id,)).fetchall()
    
    # Get saved replies
    saved_replies = db.execute("""
        SELECT * FROM social_saved_replies WHERE is_active = 1
    """).fetchall()
    
    db.close()
    
    return render_template('social_media/messages/view.html',
        title='Message Thread',
        thread=dict(thread),
        messages=[dict(r) for r in messages],
        saved_replies=[dict(r) for r in saved_replies],
    )


@sm_bp.route('/messages/reply/<int:id>', methods=['POST'])
@sm_login_required
@sm_permission_required('reply_messages')
def messages_reply(id):
    """Reply to a message thread."""
    db = get_db()
    
    thread = db.execute("SELECT * FROM social_message_threads WHERE id = ?", (id,)).fetchone()
    if not thread:
        return jsonify({'error': 'Thread not found'}), 404
    
    reply_text = request.form.get('reply_text', '').strip()
    convert_to_lead = request.form.get('convert_to_lead') == '1'
    
    if not reply_text:
        return jsonify({'error': 'Reply text is required'}), 400
    
    # Add reply message
    cursor = db.execute("""
        INSERT INTO social_messages (
            thread_id, message_platform, sender_type, message_text,
            is_incoming, is_read, message_status, replied_by_id,
            replied_at, response_result
        ) VALUES (?, ?, 'Admin', ?, 0, 1, 'Replied', ?, CURRENT_TIMESTAMP, ?)
    """, (id, thread['platform'], reply_text, session.get('user_id'), 'Sent'))
    db.commit()
    
    # Update thread
    db.execute("""
        UPDATE social_message_threads SET
            message_count = message_count + 1,
            thread_status = 'Responded',
            last_response_at = CURRENT_TIMESTAMP,
            is_unread = 0,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (id,))
    db.commit()
    
    # Convert to lead if requested
    if convert_to_lead:
        # This would create a lead from the message
        pass
    
    log_social_audit(db, 'social_messages', cursor.lastrowid, 'REPLY',
                     user_id=session.get('user_id'))
    
    return jsonify({'success': True, 'message': 'Reply sent successfully.'})


@sm_bp.route('/messages/assign', methods=['POST'])
@sm_login_required
@sm_permission_required('assign_messages')
def messages_assign():
    """Assign message thread to a responder."""
    db = get_db()
    
    thread_id = request.form.get('thread_id')
    responder_id = request.form.get('responder_id')
    
    if not thread_id or not responder_id:
        return jsonify({'error': 'Thread ID and Responder ID are required'}), 400
    
    db.execute("""
        UPDATE social_message_threads SET
            assigned_responder_id = ?,
            thread_status = 'Assigned',
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (responder_id, thread_id))
    db.commit()
    
    log_social_audit(db, 'social_message_threads', thread_id, 'ASSIGN',
                     new_value=str(responder_id), user_id=session.get('user_id'))
    
    return jsonify({'success': True, 'message': 'Thread assigned successfully.'})


@sm_bp.route('/messages/convert-to-lead/<int:id>', methods=['POST'])
@sm_login_required
@sm_permission_required('create_leads')
def messages_convert_to_lead(id):
    """Convert message thread to a lead."""
    db = get_db()
    
    thread = db.execute("SELECT * FROM social_message_threads WHERE id = ?", (id,)).fetchone()
    if not thread:
        return jsonify({'error': 'Thread not found'}), 404
    
    # Create lead from thread
    cursor = db.execute("""
        INSERT INTO social_leads (
            lead_name, phone, whatsapp, email, country, city,
            source_platform, funnel_stage, lead_status,
            assigned_salesperson_id, entry_date,
            created_by_user_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        thread['sender_name'] or 'Unknown',
        thread['sender_phone'],
        thread['sender_phone'],  # WhatsApp same as phone
        thread['sender_email'],
        thread['sender_country'],
        thread['sender_city'],
        thread['platform'],
        'Message',
        'New',
        session.get('user_id'),
        datetime.now().strftime('%Y-%m-%d'),
        session.get('user_id')
    ))
    db.commit()
    
    lead_id = cursor.lastrowid
    
    # Update thread with lead conversion
    db.execute("""
        UPDATE social_message_threads SET
            convert_to_lead = 1,
            thread_status = 'Converted'
        WHERE id = ?
    """, (id,))
    db.commit()
    
    # Mark the latest message with lead_id
    latest_message = db.execute("""
        SELECT id FROM social_messages WHERE thread_id = ? ORDER BY created_at DESC LIMIT 1
    """, (id,)).fetchone()
    
    if latest_message:
        db.execute("UPDATE social_messages SET lead_id = ? WHERE id = ?", (lead_id, latest_message['id']))
        db.commit()
    
    log_social_audit(db, 'social_message_threads', id, 'CONVERT_TO_LEAD',
                     new_value=str(lead_id), user_id=session.get('user_id'))
    
    return jsonify({'success': True, 'message': 'Lead created successfully.', 'lead_id': lead_id})


# =============================================================================
# LEADS & CONVERSION
# =============================================================================

@sm_bp.route('/leads')
@sm_login_required
@sm_permission_required('view_leads')
def leads_list():
    """List all social media leads."""
    db = get_db()
    
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    source = request.args.get('source', '')
    funnel_stage = request.args.get('funnel_stage', '')
    
    query = """
        SELECT l.*, u.username as assigned_to_name,
               c.campaign_name as source_campaign_name
        FROM social_leads l
        LEFT JOIN users u ON l.assigned_salesperson_id = u.id
        LEFT JOIN social_campaigns c ON l.source_campaign_id = c.id
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) as cnt FROM social_leads l WHERE 1=1"
    params = []
    
    if search:
        query += " AND (l.lead_name LIKE ? OR l.phone LIKE ? OR l.email LIKE ?)"
        count_query += " AND (l.lead_name LIKE ? OR l.phone LIKE ? OR l.email LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
    
    if status:
        query += " AND l.lead_status = ?"
        count_query += " AND l.lead_status = ?"
        params.append(status)
    
    if source:
        query += " AND l.source_platform = ?"
        count_query += " AND l.source_platform = ?"
        params.append(source)
    
    if funnel_stage:
        query += " AND l.funnel_stage = ?"
        count_query += " AND l.funnel_stage = ?"
        params.append(funnel_stage)
    
    total = db.execute(count_query, params).fetchone()['cnt']
    query += " ORDER BY l.created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    leads = db.execute(query, params).fetchall()
    
    db.close()
    
    return render_template('social_media/leads/list.html',
        title='Social Media Leads',
        leads=[dict(r) for r in leads],
        total=total,
        page=page,
        per_page=per_page,
        search=search,
        status_filter=status,
        source_filter=source,
        funnel_filter=funnel_stage,
    )


@sm_bp.route('/leads/new', methods=['GET', 'POST'])
@sm_login_required
@sm_permission_required('create_leads')
def leads_new():
    """Create new social media lead."""
    db = get_db()
    
    if request.method == 'POST':
        lead_name = request.form.get('lead_name', '').strip()
        phone = request.form.get('phone', '').strip()
        whatsapp = request.form.get('whatsapp', '').strip()
        email = request.form.get('email', '').strip()
        country = request.form.get('country', '').strip()
        city = request.form.get('city', '').strip()
        customer_type = request.form.get('customer_type', '').strip()
        is_wholesale = 1 if request.form.get('is_wholesale') else 0
        is_retail = 1 if request.form.get('is_retail') else 0
        is_local = 1 if request.form.get('is_local') else 0
        is_export = 1 if request.form.get('is_export') else 0
        source_platform = request.form.get('source_platform', '').strip()
        source_campaign_id = request.form.get('source_campaign_id')
        brand_interest = request.form.get('brand_interest', '').strip()
        product_interest = request.form.get('product_interest', '').strip()
        part_number_interest = request.form.get('part_number_interest', '').strip()
        estimated_value = float(request.form.get('estimated_value', 0))
        urgency_level = request.form.get('urgency_level', 'Medium').strip()
        funnel_stage = request.form.get('funnel_stage', 'Message').strip()
        assigned_salesperson_id = request.form.get('assigned_salesperson_id')
        notes = request.form.get('notes', '').strip()
        
        if not lead_name:
            flash('Lead Name is required.', 'error')
            return render_template('social_media/leads/new.html', title='New Lead')
        
        cursor = db.execute("""
            INSERT INTO social_leads (
                lead_name, phone, whatsapp, email, country, city,
                customer_type, is_wholesale, is_retail, is_local, is_export,
                source_platform, source_campaign_id, brand_interest, product_interest,
                part_number_interest, estimated_value, urgency_level, funnel_stage,
                assigned_salesperson_id, entry_date, notes, created_by_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (lead_name, phone, whatsapp, email, country, city,
              customer_type, is_wholesale, is_retail, is_local, is_export,
              source_platform, source_campaign_id, brand_interest, product_interest,
              part_number_interest, estimated_value, urgency_level, funnel_stage,
              assigned_salesperson_id, datetime.now().strftime('%Y-%m-%d'),
              notes, session.get('user_id')))
        db.commit()
        
        log_social_audit(db, 'social_leads', cursor.lastrowid, 'CREATE',
                         user_id=session.get('user_id'))
        
        flash(f'Lead "{lead_name}" created successfully.', 'success')
        return redirect(url_for('social_media.leads_list'))
    
    campaigns = db.execute("SELECT id, campaign_name FROM social_campaigns").fetchall()
    salespersons = db.execute("""
        SELECT id, username FROM users 
        WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%')
    """).fetchall()
    
    db.close()
    
    return render_template('social_media/leads/new.html',
        title='New Social Lead',
        campaigns=[dict(r) for r in campaigns],
        salespersons=[dict(r) for r in salespersons],
    )


@sm_bp.route('/leads/edit/<int:id>', methods=['GET', 'POST'])
@sm_login_required
@sm_permission_required('edit_leads')
def leads_edit(id):
    """Edit social media lead."""
    db = get_db()
    
    lead = db.execute("SELECT * FROM social_leads WHERE id = ?", (id,)).fetchone()
    if not lead:
        flash('Lead not found.', 'error')
        return redirect(url_for('social_media.leads_list'))
    
    if request.method == 'POST':
        lead_name = request.form.get('lead_name', '').strip()
        phone = request.form.get('phone', '').strip()
        whatsapp = request.form.get('whatsapp', '').strip()
        email = request.form.get('email', '').strip()
        country = request.form.get('country', '').strip()
        city = request.form.get('city', '').strip()
        customer_type = request.form.get('customer_type', '').strip()
        is_wholesale = 1 if request.form.get('is_wholesale') else 0
        is_retail = 1 if request.form.get('is_retail') else 0
        is_local = 1 if request.form.get('is_local') else 0
        is_export = 1 if request.form.get('is_export') else 0
        source_platform = request.form.get('source_platform', '').strip()
        source_campaign_id = request.form.get('source_campaign_id')
        brand_interest = request.form.get('brand_interest', '').strip()
        product_interest = request.form.get('product_interest', '').strip()
        part_number_interest = request.form.get('part_number_interest', '').strip()
        estimated_value = float(request.form.get('estimated_value', 0))
        urgency_level = request.form.get('urgency_level', 'Medium').strip()
        funnel_stage = request.form.get('funnel_stage', 'Message').strip()
        lead_status = request.form.get('lead_status', 'New').strip()
        assigned_salesperson_id = request.form.get('assigned_salesperson_id')
        next_followup_date = request.form.get('next_followup_date', '').strip()
        notes = request.form.get('notes', '').strip()
        
        db.execute("""
            UPDATE social_leads SET
                lead_name = ?, phone = ?, whatsapp = ?, email = ?, country = ?, city = ?,
                customer_type = ?, is_wholesale = ?, is_retail = ?, is_local = ?, is_export = ?,
                source_platform = ?, source_campaign_id = ?, brand_interest = ?, product_interest = ?,
                part_number_interest = ?, estimated_value = ?, urgency_level = ?, funnel_stage = ?,
                lead_status = ?, assigned_salesperson_id = ?, next_followup_date = ?,
                notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (lead_name, phone, whatsapp, email, country, city,
              customer_type, is_wholesale, is_retail, is_local, is_export,
              source_platform, source_campaign_id, brand_interest, product_interest,
              part_number_interest, estimated_value, urgency_level, funnel_stage,
              lead_status, assigned_salesperson_id, next_followup_date,
              notes, id))
        db.commit()
        
        log_social_audit(db, 'social_leads', id, 'UPDATE',
                         user_id=session.get('user_id'))
        
        flash('Lead updated successfully.', 'success')
        return redirect(url_for('social_media.leads_list'))
    
    campaigns = db.execute("SELECT id, campaign_name FROM social_campaigns").fetchall()
    salespersons = db.execute("""
        SELECT id, username FROM users 
        WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%')
    """).fetchall()
    
    db.close()
    
    return render_template('social_media/leads/edit.html',
        title='Edit Lead',
        lead=dict(lead),
        campaigns=[dict(r) for r in campaigns],
        salespersons=[dict(r) for r in salespersons],
    )


@sm_bp.route('/leads/view/<int:id>')
@sm_login_required
@sm_permission_required('view_leads')
def leads_view(id):
    """View lead details."""
    db = get_db()
    
    lead = db.execute("""
        SELECT l.*, u.username as assigned_to_name,
               c.campaign_name as source_campaign_name
        FROM social_leads l
        LEFT JOIN users u ON l.assigned_salesperson_id = u.id
        LEFT JOIN social_campaigns c ON l.source_campaign_id = c.id
        WHERE l.id = ?
    """, (id,)).fetchone()
    
    if not lead:
        flash('Lead not found.', 'error')
        return redirect(url_for('social_media.leads_list'))
    
    # Get follow-ups
    followups = db.execute("""
        SELECT f.*, u.username as assigned_to_name
        FROM social_lead_followups f
        LEFT JOIN users u ON f.assigned_to_id = u.id
        WHERE f.lead_id = ?
        ORDER BY f.followup_date DESC
    """, (id,)).fetchall()
    
    db.close()
    
    return render_template('social_media/leads/view.html',
        title='Lead Details',
        lead=dict(lead),
        followups=[dict(r) for r in followups],
    )


@sm_bp.route('/leads/followup/<int:id>', methods=['POST'])
@sm_login_required
@sm_permission_required('edit_leads')
def leads_followup(id):
    """Add follow-up to lead."""
    db = get_db()
    
    lead = db.execute("SELECT * FROM social_leads WHERE id = ?", (id,)).fetchone()
    if not lead:
        return jsonify({'error': 'Lead not found'}), 404
    
    followup_type = request.form.get('followup_type', '').strip()
    followup_method = request.form.get('followup_method', '').strip()
    followup_notes = request.form.get('followup_notes', '').strip()
    followup_result = request.form.get('followup_result', '').strip()
    next_followup_date = request.form.get('next_followup_date', '').strip()
    assigned_to_id = request.form.get('assigned_to_id')
    
    cursor = db.execute("""
        INSERT INTO social_lead_followups (
            lead_id, followup_date, followup_type, followup_method,
            followup_notes, followup_result, next_followup_date,
            assigned_to_id, is_completed, completed_at, created_by_user_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (id, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), followup_type,
          followup_method, followup_notes, followup_result, next_followup_date,
          assigned_to_id, 1 if followup_result else 0,
          datetime.now().strftime('%Y-%m-%d %H:%M:%S') if followup_result else None,
          session.get('user_id')))
    db.commit()
    
    # Update lead
    db.execute("""
        UPDATE social_leads SET
            followup_count = followup_count + 1,
            last_followup_at = CURRENT_TIMESTAMP,
            next_followup_date = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (next_followup_date if next_followup_date else None, id))
    db.commit()
    
    log_social_audit(db, 'social_lead_followups', cursor.lastrowid, 'CREATE',
                     user_id=session.get('user_id'))
    
    flash('Follow-up added successfully.', 'success')
    return redirect(url_for('social_media.leads_view', id=id))


# =============================================================================
# CAMPAIGNS & ADVERTISING
# =============================================================================

@sm_bp.route('/campaigns')
@sm_login_required
@sm_permission_required('view_campaigns')
def campaigns_list():
    """List all social campaigns."""
    db = get_db()
    
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    search = request.args.get('search', '')
    status = request.args.get('status', '')
    platform = request.args.get('platform', '')
    
    query = """
        SELECT c.*, u.username as manager_name
        FROM social_campaigns c
        LEFT JOIN users u ON c.campaign_manager_id = u.id
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) as cnt FROM social_campaigns c WHERE 1=1"
    params = []
    
    if search:
        query += " AND (c.campaign_name LIKE ? OR c.campaign_code LIKE ?)"
        count_query += " AND (c.campaign_name LIKE ? OR c.campaign_code LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term])
    
    if status:
        query += " AND c.campaign_status = ?"
        count_query += " AND c.campaign_status = ?"
        params.append(status)
    
    if platform:
        query += " AND c.platform = ?"
        count_query += " AND c.platform = ?"
        params.append(platform)
    
    total = db.execute(count_query, params).fetchone()['cnt']
    query += " ORDER BY c.created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    campaigns = db.execute(query, params).fetchall()
    
    db.close()
    
    return render_template('social_media/campaigns/list.html',
        title='Social Campaigns',
        campaigns=[dict(r) for r in campaigns],
        total=total,
        page=page,
        per_page=per_page,
        search=search,
        status_filter=status,
        platform_filter=platform,
    )


@sm_bp.route('/campaigns/new', methods=['GET', 'POST'])
@sm_login_required
@sm_permission_required('create_campaigns')
def campaigns_new():
    """Create new social campaign."""
    db = get_db()
    
    if request.method == 'POST':
        campaign_name = request.form.get('campaign_name', '').strip()
        campaign_code = request.form.get('campaign_code', '').strip() or f"SC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        campaign_type = request.form.get('campaign_type', '').strip()
        campaign_objective = request.form.get('campaign_objective', '').strip()
        platform = request.form.get('platform', '').strip()
        target_market = request.form.get('target_market', '').strip()
        target_audience = request.form.get('target_audience', '').strip()
        customer_type = request.form.get('customer_type', '').strip()
        target_brand = request.form.get('target_brand', '').strip()
        target_products = request.form.get('target_products', '').strip()
        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()
        approved_budget = float(request.form.get('approved_budget', 0))
        campaign_manager_id = request.form.get('campaign_manager_id')
        main_message = request.form.get('main_message', '').strip()
        cta_text = request.form.get('cta_text', '').strip()
        target_landing_url = request.form.get('target_landing_url', '').strip()
        target_whatsapp = request.form.get('target_whatsapp', '').strip()
        utm_source = request.form.get('utm_source', '').strip()
        utm_medium = request.form.get('utm_medium', '').strip()
        utm_campaign = request.form.get('utm_campaign', '').strip()
        campaign_status = request.form.get('campaign_status', 'Draft').strip()
        notes = request.form.get('notes', '').strip()
        
        if not campaign_name:
            flash('Campaign Name is required.', 'error')
            return render_template('social_media/campaigns/new.html', title='New Campaign')
        
        cursor = db.execute("""
            INSERT INTO social_campaigns (
                campaign_name, campaign_code, campaign_type, campaign_objective,
                platform, target_market, target_audience, customer_type, target_brand,
                target_products, start_date, end_date, approved_budget, campaign_manager_id,
                main_message, cta_text, target_landing_url, target_whatsapp,
                utm_source, utm_medium, utm_campaign, campaign_status, notes,
                created_by_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (campaign_name, campaign_code, campaign_type, campaign_objective,
              platform, target_market, target_audience, customer_type, target_brand,
              target_products, start_date, end_date, approved_budget, campaign_manager_id,
              main_message, cta_text, target_landing_url, target_whatsapp,
              utm_source, utm_medium, utm_campaign, campaign_status, notes,
              session.get('user_id')))
        db.commit()
        
        log_social_audit(db, 'social_campaigns', cursor.lastrowid, 'CREATE',
                         user_id=session.get('user_id'))
        
        flash(f'Campaign "{campaign_name}" created successfully.', 'success')
        return redirect(url_for('social_media.campaigns_list'))
    
    managers = db.execute("""
        SELECT id, username FROM users 
        WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Manager%' OR role_name LIKE '%Admin%')
    """).fetchall()
    
    db.close()
    
    return render_template('social_media/campaigns/new.html',
        title='New Campaign',
        managers=[dict(r) for r in managers],
    )


@sm_bp.route('/campaigns/edit/<int:id>', methods=['GET', 'POST'])
@sm_login_required
@sm_permission_required('edit_campaigns')
def campaigns_edit(id):
    """Edit social campaign."""
    db = get_db()
    
    campaign = db.execute("SELECT * FROM social_campaigns WHERE id = ?", (id,)).fetchone()
    if not campaign:
        flash('Campaign not found.', 'error')
        return redirect(url_for('social_media.campaigns_list'))
    
    if request.method == 'POST':
        campaign_name = request.form.get('campaign_name', '').strip()
        campaign_type = request.form.get('campaign_type', '').strip()
        campaign_objective = request.form.get('campaign_objective', '').strip()
        platform = request.form.get('platform', '').strip()
        target_market = request.form.get('target_market', '').strip()
        target_audience = request.form.get('target_audience', '').strip()
        customer_type = request.form.get('customer_type', '').strip()
        target_brand = request.form.get('target_brand', '').strip()
        target_products = request.form.get('target_products', '').strip()
        start_date = request.form.get('start_date', '').strip()
        end_date = request.form.get('end_date', '').strip()
        approved_budget = float(request.form.get('approved_budget', 0))
        campaign_manager_id = request.form.get('campaign_manager_id')
        main_message = request.form.get('main_message', '').strip()
        cta_text = request.form.get('cta_text', '').strip()
        target_landing_url = request.form.get('target_landing_url', '').strip()
        target_whatsapp = request.form.get('target_whatsapp', '').strip()
        utm_source = request.form.get('utm_source', '').strip()
        utm_medium = request.form.get('utm_medium', '').strip()
        utm_campaign = request.form.get('utm_campaign', '').strip()
        campaign_status = request.form.get('campaign_status', 'Draft').strip()
        notes = request.form.get('notes', '').strip()
        
        db.execute("""
            UPDATE social_campaigns SET
                campaign_name = ?, campaign_type = ?, campaign_objective = ?,
                platform = ?, target_market = ?, target_audience = ?, customer_type = ?,
                target_brand = ?, target_products = ?, start_date = ?, end_date = ?,
                approved_budget = ?, campaign_manager_id = ?, main_message = ?,
                cta_text = ?, target_landing_url = ?, target_whatsapp = ?,
                utm_source = ?, utm_medium = ?, utm_campaign = ?,
                campaign_status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (campaign_name, campaign_type, campaign_objective,
              platform, target_market, target_audience, customer_type,
              target_brand, target_products, start_date, end_date,
              approved_budget, campaign_manager_id, main_message,
              cta_text, target_landing_url, target_whatsapp,
              utm_source, utm_medium, utm_campaign,
              campaign_status, notes, id))
        db.commit()
        
        log_social_audit(db, 'social_campaigns', id, 'UPDATE',
                         user_id=session.get('user_id'))
        
        flash('Campaign updated successfully.', 'success')
        return redirect(url_for('social_media.campaigns_list'))
    
    managers = db.execute("""
        SELECT id, username FROM users 
        WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Manager%' OR role_name LIKE '%Admin%')
    """).fetchall()
    
    db.close()
    
    return render_template('social_media/campaigns/edit.html',
        title='Edit Campaign',
        campaign=dict(campaign),
        managers=[dict(r) for r in managers],
    )


@sm_bp.route('/campaigns/view/<int:id>')
@sm_login_required
@sm_permission_required('view_campaigns')
def campaigns_view(id):
    """View campaign details."""
    db = get_db()
    
    campaign = db.execute("""
        SELECT c.*, u.username as manager_name
        FROM social_campaigns c
        LEFT JOIN users u ON c.campaign_manager_id = u.id
        WHERE c.id = ?
    """, (id,)).fetchone()
    
    if not campaign:
        flash('Campaign not found.', 'error')
        return redirect(url_for('social_media.campaigns_list'))
    
    # Get ads for this campaign
    ads = db.execute("""
        SELECT * FROM social_ads WHERE parent_campaign_id = ?
        ORDER BY created_at DESC
    """, (id,)).fetchall()
    
    # Get related content
    content = db.execute("""
        SELECT * FROM social_content_production
        WHERE related_campaign_id = ?
        ORDER BY created_at DESC
    """, (id,)).fetchall()
    
    db.close()
    
    return render_template('social_media/campaigns/view.html',
        title='Campaign Details',
        campaign=dict(campaign),
        ads=[dict(r) for r in ads],
        content=[dict(r) for r in content],
    )


@sm_bp.route('/campaigns/delete/<int:id>', methods=['POST'])
@sm_login_required
@sm_permission_required('delete_campaigns')
def campaigns_delete(id):
    """Delete campaign."""
    db = get_db()
    
    campaign = db.execute("SELECT * FROM social_campaigns WHERE id = ?", (id,)).fetchone()
    if not campaign:
        flash('Campaign not found.', 'error')
        return redirect(url_for('social_media.campaigns_list'))
    
    db.execute("DELETE FROM social_campaigns WHERE id = ?", (id,))
    db.commit()
    
    log_social_audit(db, 'social_campaigns', id, 'DELETE',
                     user_id=session.get('user_id'))
    
    flash('Campaign deleted successfully.', 'success')
    return redirect(url_for('social_media.campaigns_list'))


# =============================================================================
# ADS MANAGEMENT
# =============================================================================

@sm_bp.route('/ads')
@sm_login_required
@sm_permission_required('view_ads')
def ads_list():
    """List all social ads."""
    db = get_db()
    
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    status = request.args.get('status', '')
    platform = request.args.get('platform', '')
    campaign_id = request.args.get('campaign_id')
    
    query = """
        SELECT a.*, c.campaign_name
        FROM social_ads a
        LEFT JOIN social_campaigns c ON a.parent_campaign_id = c.id
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) as cnt FROM social_ads a WHERE 1=1"
    params = []
    
    if status:
        query += " AND a.ad_status = ?"
        count_query += " AND a.ad_status = ?"
        params.append(status)
    
    if platform:
        query += " AND a.platform = ?"
        count_query += " AND a.platform = ?"
        params.append(platform)
    
    if campaign_id:
        query += " AND a.parent_campaign_id = ?"
        count_query += " AND a.parent_campaign_id = ?"
        params.append(campaign_id)
    
    total = db.execute(count_query, params).fetchone()['cnt']
    query += " ORDER BY a.created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    ads = db.execute(query, params).fetchall()
    
    db.close()
    
    return render_template('social_media/ads/list.html',
        title='Social Ads',
        ads=[dict(r) for r in ads],
        total=total,
        page=page,
        per_page=per_page,
        status_filter=status,
        platform_filter=platform,
        campaign_filter=campaign_id,
    )


@sm_bp.route('/ads/new', methods=['GET', 'POST'])
@sm_login_required
@sm_permission_required('create_ads')
def ads_new():
    """Create new social ad."""
    db = get_db()
    
    if request.method == 'POST':
        parent_campaign_id = request.form.get('parent_campaign_id')
        ad_set_name = request.form.get('ad_set_name', '').strip()
        ad_name = request.form.get('ad_name', '').strip()
        ad_objective = request.form.get('ad_objective', '').strip()
        platform = request.form.get('platform', '').strip()
        audience_definition = request.form.get('audience_definition', '').strip()
        age_min = int(request.form.get('age_min', 18))
        age_max = int(request.form.get('age_max', 65))
        gender = request.form.get('gender', '').strip()
        locations = request.form.get('locations', '').strip()
        languages = request.form.get('languages', '').strip()
        customer_type = request.form.get('customer_type', '').strip()
        ad_copy = request.form.get('ad_copy', '').strip()
        cta_text = request.form.get('cta_text', '').strip()
        daily_budget = float(request.form.get('daily_budget', 0))
        total_budget = float(request.form.get('total_budget', 0))
        start_time = request.form.get('start_time', '').strip()
        end_time = request.form.get('end_time', '').strip()
        ad_status = request.form.get('ad_status', 'Draft').strip()
        notes = request.form.get('notes', '').strip()
        
        if not ad_name or not platform:
            flash('Ad Name and Platform are required.', 'error')
            return render_template('social_media/ads/new.html', title='New Ad')
        
        cursor = db.execute("""
            INSERT INTO social_ads (
                parent_campaign_id, ad_set_name, ad_name, ad_objective, platform,
                audience_definition, age_min, age_max, gender, locations, languages,
                customer_type, ad_copy, cta_text, daily_budget, total_budget,
                start_time, end_time, ad_status, notes, created_by_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (parent_campaign_id, ad_set_name, ad_name, ad_objective, platform,
              audience_definition, age_min, age_max, gender, locations, languages,
              customer_type, ad_copy, cta_text, daily_budget, total_budget,
              start_time, end_time, ad_status, notes, session.get('user_id')))
        db.commit()
        
        log_social_audit(db, 'social_ads', cursor.lastrowid, 'CREATE',
                         user_id=session.get('user_id'))
        
        flash(f'Ad "{ad_name}" created successfully.', 'success')
        return redirect(url_for('social_media.ads_list'))
    
    campaigns = db.execute("SELECT id, campaign_name FROM social_campaigns").fetchall()
    
    db.close()
    
    return render_template('social_media/ads/new.html',
        title='New Social Ad',
        campaigns=[dict(r) for r in campaigns],
    )


# =============================================================================
# BRAND & MARKET MONITORING
# =============================================================================

@sm_bp.route('/monitoring')
@sm_login_required
@sm_permission_required('view_monitoring')
def monitoring_list():
    """List all monitoring records."""
    db = get_db()
    
    page = int(request.args.get('page', 1))
    per_page = 20
    offset = (page - 1) * per_page
    
    mtype = request.args.get('type', '')
    platform = request.args.get('platform', '')
    
    query = """
        SELECT m.*, u.username as owner_name
        FROM social_monitoring m
        LEFT JOIN users u ON m.assigned_owner_id = u.id
        WHERE 1=1
    """
    count_query = "SELECT COUNT(*) as cnt FROM social_monitoring m WHERE 1=1"
    params = []
    
    if mtype:
        query += " AND m.monitoring_type = ?"
        count_query += " AND m.monitoring_type = ?"
        params.append(mtype)
    
    if platform:
        query += " AND m.platform = ?"
        count_query += " AND m.platform = ?"
        params.append(platform)
    
    total = db.execute(count_query, params).fetchone()['cnt']
    query += " ORDER BY m.created_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    records = db.execute(query, params).fetchall()
    
    db.close()
    
    return render_template('social_media/monitoring/list.html',
        title='Brand & Market Monitoring',
        records=[dict(r) for r in records],
        total=total,
        page=page,
        per_page=per_page,
        type_filter=mtype,
        platform_filter=platform,
    )


@sm_bp.route('/monitoring/new', methods=['GET', 'POST'])
@sm_login_required
@sm_permission_required('create_monitoring')
def monitoring_new():
    """Create new monitoring record."""
    db = get_db()
    
    if request.method == 'POST':
        monitoring_type = request.form.get('monitoring_type', '').strip()
        monitored_entity = request.form.get('monitored_entity', '').strip()
        platform = request.form.get('platform', '').strip()
        source_link = request.form.get('source_link', '').strip()
        observed_text = request.form.get('observed_text', '').strip()
        category = request.form.get('category', '').strip()
        sentiment = request.form.get('sentiment', '').strip()
        importance_level = request.form.get('importance_level', 'Medium').strip()
        requires_action = 1 if request.form.get('requires_action') else 0
        assigned_owner_id = request.form.get('assigned_owner_id')
        record_date = request.form.get('record_date', '').strip()
        notes = request.form.get('notes', '').strip()
        
        if not monitoring_type or not monitored_entity:
            flash('Monitoring Type and Monitored Entity are required.', 'error')
            return render_template('social_media/monitoring/new.html', title='New Record')
        
        cursor = db.execute("""
            INSERT INTO social_monitoring (
                monitoring_type, monitored_entity, platform, source_link,
                observed_text, category, sentiment, importance_level, requires_action,
                assigned_owner_id, record_date, notes, created_by_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (monitoring_type, monitored_entity, platform, source_link,
              observed_text, category, sentiment, importance_level, requires_action,
              assigned_owner_id, record_date if record_date else datetime.now().strftime('%Y-%m-%d'),
              notes, session.get('user_id')))
        db.commit()
        
        log_social_audit(db, 'social_monitoring', cursor.lastrowid, 'CREATE',
                         user_id=session.get('user_id'))
        
        flash('Monitoring record created successfully.', 'success')
        return redirect(url_for('social_media.monitoring_list'))
    
    db.close()
    
    return render_template('social_media/monitoring/new.html',
        title='New Monitoring Record',
    )


# =============================================================================
# REPORTS & ANALYTICS
# =============================================================================

@sm_bp.route('/reports')
@sm_login_required
@sm_permission_required('view_reports')
def reports():
    """Social media reports dashboard."""
    db = get_db()
    
    date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
    platform = request.args.get('platform', '')
    
    # Content performance
    content_perf = get_content_performance(db, date_from, date_to, platform)
    
    # Platform breakdown
    platform_stats = db.execute("""
        SELECT 
            platform,
            COUNT(*) as posts,
            SUM(reach) as total_reach,
            SUM(impressions) as total_impressions,
            SUM(engagement) as total_engagement,
            SUM(leads_generated) as total_leads,
            SUM(sales_generated) as total_sales
        FROM social_content_archive
        WHERE date(published_at) BETWEEN ? AND ?
        GROUP BY platform
    """, (date_from, date_to)).fetchall()
    
    # Campaign performance
    campaign_stats = db.execute("""
        SELECT 
            c.*,
            COUNT(a.id) as ads_count,
            SUM(a.impressions_count) as total_impressions,
            SUM(a.clicks_count) as total_clicks,
            SUM(a.amount_spent) as total_spent,
            SUM(a.sales_revenue) as total_revenue
        FROM social_campaigns c
        LEFT JOIN social_ads a ON c.id = a.parent_campaign_id
        WHERE date(c.start_date) BETWEEN ? AND ?
        GROUP BY c.id
        ORDER BY c.total_sales DESC
    """, (date_from, date_to)).fetchall()
    
    # Lead funnel
    lead_funnel = db.execute("""
        SELECT funnel_stage, COUNT(*) as count
        FROM social_leads
        GROUP BY funnel_stage
    """).fetchall()
    
    db.close()
    
    return render_template('social_media/reports/index.html',
        title='Social Media Reports',
        content_performance=[dict(r) for r in content_perf],
        platform_stats=[dict(r) for r in platform_stats],
        campaign_stats=[dict(r) for r in campaign_stats],
        lead_funnel=[dict(r) for r in lead_funnel],
        date_from=date_from,
        date_to=date_to,
        platform_filter=platform,
    )


@sm_bp.route('/reports/content-performance')
@sm_login_required
@sm_permission_required('view_reports')
def reports_content_performance():
    """Content performance detailed report."""
    db = get_db()
    
    date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
    platform = request.args.get('platform', '')
    
    content = get_content_performance(db, date_from, date_to, platform)
    
    db.close()
    
    return render_template('social_media/reports/content_performance.html',
        title='Content Performance Report',
        content=[dict(r) for r in content],
        date_from=date_from,
        date_to=date_to,
        platform_filter=platform,
    )


@sm_bp.route('/reports/export/<report_type>')
@sm_login_required
@sm_permission_required('export_reports')
def reports_export(report_type):
    """Export report as CSV."""
    db = get_db()
    
    date_from = request.args.get('date_from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))
    
    if report_type == 'content':
        data = get_content_performance(db, date_from, date_to)
        headers = ['Code', 'Platform', 'Title', 'Published At', 'Reach', 'Impressions', 
                   'Engagement', 'Leads', 'Sales']
        rows = [[r['content_code'], r['platform'], r['display_title'], 
                 r['published_at'], r['reach'], r['impressions'],
                 r['engagement'], r['leads_generated'], r['sales_generated']] for r in data]
    elif report_type == 'leads':
        data = db.execute("SELECT * FROM social_leads ORDER BY created_at DESC").fetchall()
        headers = ['Name', 'Phone', 'Source', 'Status', 'Stage', 'Value', 'Created']
        rows = [[r['lead_name'], r['phone'], r['source_platform'], 
                 r['lead_status'], r['funnel_stage'], r['estimated_value'], r['created_at']] for r in data]
    elif report_type == 'campaigns':
        data = db.execute("SELECT * FROM social_campaigns ORDER BY created_at DESC").fetchall()
        headers = ['Name', 'Code', 'Platform', 'Status', 'Budget', 'Leads', 'Sales', 'ROAS']
        rows = [[r['campaign_name'], r['campaign_code'], r['platform'],
                 r['campaign_status'], r['approved_budget'], r['total_leads'],
                 r['total_sales'], r['roas']] for r in data]
    else:
        flash('Unknown report type.', 'error')
        return redirect(url_for('social_media.reports'))
    
    db.close()
    
    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=social_{report_type}_{datetime.now().strftime("%Y%m%d")}.csv'}
    )


# =============================================================================
# SETTINGS
# =============================================================================

@sm_bp.route('/settings')
@sm_login_required
@sm_permission_required('view_settings')
def settings():
    """Social media settings."""
    db = get_db()
    
    category = request.args.get('category', 'general')
    
    settings_list = db.execute("""
        SELECT * FROM social_settings
        WHERE category = ? AND is_active = 1
        ORDER BY setting_key
    """, (category,)).fetchall()
    
    db.close()
    
    return render_template('social_media/settings/index.html',
        title='Social Media Settings',
        settings_list=[dict(r) for r in settings_list],
        category=category,
    )


@sm_bp.route('/settings/update', methods=['POST'])
@sm_login_required
@sm_permission_required('edit_settings')
def settings_update():
    """Update social media settings."""
    db = get_db()
    
    for key, value in request.form.items():
        if key.startswith('setting_'):
            setting_key = key.replace('setting_', '')
            update_social_setting(db, setting_key, value, session.get('user_id'))
    
    db.close()
    
    flash('Settings updated successfully.', 'success')
    return redirect(url_for('social_media.settings'))


# =============================================================================
# ROLES & PERMISSIONS
# =============================================================================

@sm_bp.route('/roles')
@sm_login_required
@sm_permission_required('view_roles')
def roles_list():
    """List social media roles."""
    db = get_db()
    
    roles = db.execute("SELECT * FROM social_roles ORDER BY role_name").fetchall()
    
    db.close()
    
    return render_template('social_media/roles/list.html',
        title='Social Media Roles',
        roles=[dict(r) for r in roles],
    )


@sm_bp.route('/roles/new', methods=['GET', 'POST'])
@sm_login_required
@sm_permission_required('create_roles')
def roles_new():
    """Create new social media role."""
    db = get_db()
    
    if request.method == 'POST':
        role_name = request.form.get('role_name', '').strip()
        role_code = request.form.get('role_code', '').strip()
        description = request.form.get('description', '').strip()
        can_view_financials = 1 if request.form.get('can_view_financials') else 0
        can_approve = 1 if request.form.get('can_approve') else 0
        can_publish = 1 if request.form.get('can_publish') else 0
        can_manage_team = 1 if request.form.get('can_manage_team') else 0
        can_view_all_accounts = 1 if request.form.get('can_view_all_accounts') else 0
        
        if not role_name:
            flash('Role Name is required.', 'error')
            return render_template('social_media/roles/new.html', title='New Role')
        
        cursor = db.execute("""
            INSERT INTO social_roles (
                role_name, role_code, description, is_system_role,
                can_view_financials, can_approve, can_publish, can_manage_team,
                can_view_all_accounts, created_by_user_id
            ) VALUES (?, ?, ?, 0, ?, ?, ?, ?, ?, ?)
        """, (role_name, role_code, description, can_view_financials,
              can_approve, can_publish, can_manage_team, can_view_all_accounts,
              session.get('user_id')))
        db.commit()
        
        log_social_audit(db, 'social_roles', cursor.lastrowid, 'CREATE',
                         user_id=session.get('user_id'))
        
        flash(f'Role "{role_name}" created successfully.', 'success')
        return redirect(url_for('social_media.roles_list'))
    
    db.close()
    
    return render_template('social_media/roles/new.html', title='New Role')


@sm_bp.route('/roles/assign', methods=['GET', 'POST'])
@sm_login_required
@sm_permission_required('assign_roles')
def roles_assign():
    """Assign social media role to user."""
    db = get_db()
    
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        social_role_id = request.form.get('social_role_id')
        
        if not user_id or not social_role_id:
            flash('User and Role are required.', 'error')
            return redirect(url_for('social_media.roles_assign'))
        
        # Check if assignment exists
        existing = db.execute("""
            SELECT id FROM social_user_roles WHERE user_id = ? AND social_role_id = ?
        """, (user_id, social_role_id)).fetchone()
        
        if existing:
            flash('User already has this role.', 'warning')
            return redirect(url_for('social_media.roles_assign'))
        
        cursor = db.execute("""
            INSERT INTO social_user_roles (user_id, social_role_id, assigned_by_id)
            VALUES (?, ?, ?)
        """, (user_id, social_role_id, session.get('user_id')))
        db.commit()
        
        log_social_audit(db, 'social_user_roles', cursor.lastrowid, 'ASSIGN',
                         user_id=session.get('user_id'))
        
        flash('Role assigned successfully.', 'success')
        return redirect(url_for('social_media.roles_list'))
    
    users = db.execute("SELECT id, username, email FROM users ORDER BY username").fetchall()
    roles = db.execute("SELECT id, role_name FROM social_roles WHERE status = 'Active'").fetchall()
    
    # Get current assignments
    assignments = db.execute("""
        SELECT ur.*, u.username, r.role_name
        FROM social_user_roles ur
        JOIN users u ON ur.user_id = u.id
        JOIN social_roles r ON ur.social_role_id = r.id
        WHERE ur.is_active = 1
    """).fetchall()
    
    db.close()
    
    return render_template('social_media/roles/assign.html',
        title='Assign Roles',
        users=[dict(r) for r in users],
        roles=[dict(r) for r in roles],
        assignments=[dict(r) for r in assignments],
    )


# =============================================================================
# ALERTS
# =============================================================================

@sm_bp.route('/alerts')
@sm_login_required
@sm_permission_required('view_alerts')
def alerts_list():
    """List all social media alerts."""
    db = get_db()
    
    resolved = request.args.get('resolved', '0') == '1'
    
    alerts = db.execute("""
        SELECT a.*, u.username as resolved_by_name
        FROM social_alerts a
        LEFT JOIN users u ON a.resolved_by_user_id = u.id
        WHERE a.is_resolved = ?
        ORDER BY a.created_at DESC
    """, (1 if resolved else 0,)).fetchall()
    
    db.close()
    
    return render_template('social_media/alerts/list.html',
        title='Social Media Alerts',
        alerts=[dict(r) for r in alerts],
        show_resolved=resolved,
    )


@sm_bp.route('/alerts/resolve/<int:id>', methods=['POST'])
@sm_login_required
@sm_permission_required('resolve_alerts')
def alerts_resolve(id):
    """Resolve an alert."""
    db = get_db()
    
    resolution_notes = request.form.get('resolution_notes', '').strip()
    
    db.execute("""
        UPDATE social_alerts SET
            is_resolved = 1,
            resolved_at = CURRENT_TIMESTAMP,
            resolved_by_user_id = ?,
            resolution_notes = ?
        WHERE id = ?
    """, (session.get('user_id'), resolution_notes, id))
    db.commit()
    
    log_social_audit(db, 'social_alerts', id, 'RESOLVE',
                     user_id=session.get('user_id'))
    
    flash('Alert resolved successfully.', 'success')
    return redirect(url_for('social_media.alerts_list'))


# =============================================================================
# SAVED REPLIES
# =============================================================================

@sm_bp.route('/saved-replies')
@sm_login_required
@sm_permission_required('view_saved_replies')
def saved_replies_list():
    """List saved replies."""
    db = get_db()
    
    replies = db.execute("""
        SELECT r.*, u.username as created_by_name
        FROM social_saved_replies r
        LEFT JOIN users u ON r.created_by_user_id = u.id
        WHERE r.is_active = 1
        ORDER BY r.reply_category, r.reply_title
    """).fetchall()
    
    db.close()
    
    return render_template('social_media/messages/saved_replies.html',
        title='Saved Replies',
        replies=[dict(r) for r in replies],
    )


@sm_bp.route('/saved-replies/new', methods=['GET', 'POST'])
@sm_login_required
@sm_permission_required('create_saved_replies')
def saved_replies_new():
    """Create new saved reply."""
    db = get_db()
    
    if request.method == 'POST':
        reply_title = request.form.get('reply_title', '').strip()
        reply_category = request.form.get('reply_category', '').strip()
        reply_text = request.form.get('reply_text', '').strip()
        shortcut_code = request.form.get('shortcut_code', '').strip()
        platform = request.form.get('platform', '').strip()
        message_type = request.form.get('message_type', '').strip()
        
        if not reply_title or not reply_text:
            flash('Title and Reply Text are required.', 'error')
            return render_template('social_media/messages/saved_reply_new.html', title='New Saved Reply')
        
        cursor = db.execute("""
            INSERT INTO social_saved_replies (
                reply_title, reply_category, reply_text, shortcut_code,
                platform, message_type, created_by_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (reply_title, reply_category, reply_text, shortcut_code,
              platform, message_type, session.get('user_id')))
        db.commit()
        
        flash('Saved reply created successfully.', 'success')
        return redirect(url_for('social_media.saved_replies_list'))
    
    db.close()
    
    return render_template('social_media/messages/saved_reply_new.html', title='New Saved Reply')


# =============================================================================
# CONTENT ARCHIVE
# =============================================================================

@sm_bp.route('/archive')
@sm_login_required
@sm_permission_required('view_archive')
def content_archive():
    """Content archive view."""
    db = get_db()
    
    page = int(request.args.get('page', 1))
    per_page = 30
    offset = (page - 1) * per_page
    
    search = request.args.get('search', '')
    platform = request.args.get('platform', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = "SELECT * FROM social_content_archive WHERE 1=1"
    count_query = "SELECT COUNT(*) as cnt FROM social_content_archive WHERE 1=1"
    params = []
    
    if search:
        query += " AND (display_title LIKE ? OR internal_title LIKE ? OR caption LIKE ?)"
        count_query += " AND (display_title LIKE ? OR internal_title LIKE ? OR caption LIKE ?)"
        search_term = f"%{search}%"
        params.extend([search_term, search_term, search_term])
    
    if platform:
        query += " AND platform = ?"
        count_query += " AND platform = ?"
        params.append(platform)
    
    if date_from:
        query += " AND date(published_at) >= ?"
        count_query += " AND date(published_at) >= ?"
        params.append(date_from)
    
    if date_to:
        query += " AND date(published_at) <= ?"
        count_query += " AND date(published_at) <= ?"
        params.append(date_to)
    
    total = db.execute(count_query, params).fetchone()['cnt']
    query += " ORDER BY published_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, offset])
    
    archived = db.execute(query, params).fetchall()
    
    db.close()
    
    return render_template('social_media/content/archive.html',
        title='Content Archive',
        archived=[dict(r) for r in archived],
        total=total,
        page=page,
        per_page=per_page,
        search=search,
        platform_filter=platform,
        date_from=date_from,
        date_to=date_to,
    )


# =============================================================================
# API ENDPOINTS
# =============================================================================

@sm_bp.route('/api/dashboard-stats')
@sm_login_required
def api_dashboard_stats():
    """Get dashboard statistics as JSON."""
    db = get_db()
    stats = get_social_dashboard_data(db)
    db.close()
    return jsonify(stats)


@sm_bp.route('/api/campaign/<int:id>/metrics')
@sm_login_required
def api_campaign_metrics(id):
    """Get campaign metrics as JSON."""
    db = get_db()
    
    campaign = db.execute("SELECT * FROM social_campaigns WHERE id = ?", (id,)).fetchone()
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404
    
    # Get content for this campaign
    content = db.execute("""
        SELECT * FROM social_content_archive
        WHERE linked_campaign_id = ?
        ORDER BY published_at DESC
    """, (id,)).fetchall()
    
    # Get ads for this campaign
    ads = db.execute("""
        SELECT * FROM social_ads WHERE parent_campaign_id = ?
    """, (id,)).fetchall()
    
    db.close()
    
    return jsonify({
        'campaign': dict(campaign),
        'content': [dict(r) for r in content],
        'ads': [dict(r) for r in ads],
    })


@sm_bp.route('/api/calendar/<date>')
@sm_login_required
def api_calendar_day(date):
    """Get calendar items for a specific date."""
    db = get_db()
    
    items = db.execute("""
        SELECT c.*, p.internal_title, p.display_title
        FROM social_content_calendar c
        LEFT JOIN social_content_production p ON c.content_id = p.id
        WHERE c.publish_date = ?
        ORDER BY c.publish_time
    """, (date,)).fetchall()
    
    db.close()
    
    return jsonify([dict(r) for r in items])


# =============================================================================
# ROUTE REGISTRATION
# =============================================================================

def register_social_media_routes(app):
    """Register social media routes with the Flask app."""
    app.register_blueprint(sm_bp)
