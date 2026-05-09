"""
API Gateway Route Handlers
=========================
Flask route handlers for the enterprise API Gateway module.

Route Structure:
- /api-gateway/ - API Gateway Dashboard
- /api-gateway/rest-api/ - REST API Management
  - /api-gateway/rest-api/explorer/ - API Explorer
  - /api-gateway/rest-api/routes/ - Route Registry
  - /api-gateway/rest-api/versions/ - API Versions
  - /api-gateway/rest-api/logs/ - Request Logs
- /api-gateway/auth/ - Authentication & Access
  - /api-gateway/auth/clients/ - API Clients
  - /api-gateway/auth/credentials/ - API Keys & Tokens
  - /api-gateway/auth/scopes/ - Scope Management
  - /api-gateway/auth/policies/ - Access Policies
- /api-gateway/integrations/ - External Integrations
  - /api-gateway/integrations/profiles/ - Integration Profiles
  - /api-gateway/integrations/runs/ - Sync Jobs
  - /api-gateway/integrations/exceptions/ - Integration Exceptions
- /api-gateway/webhooks/ - Webhooks
  - /api-gateway/webhooks/events/ - Event Catalog
  - /api-gateway/webhooks/subscriptions/ - Webhook Endpoints
  - /api-gateway/webhooks/deliveries/ - Delivery Logs
  - /api-gateway/webhooks/failed/ - Failed Deliveries
- /api-gateway/docs/ - Documentation
  - /api-gateway/docs/openapi/ - OpenAPI/Swagger
  - /api-gateway/docs/guides/ - API Guides
  - /api-gateway/docs/webhooks/ - Webhook Docs
- /api-gateway/monitoring/ - Monitoring
  - /api-gateway/monitoring/usage/ - Usage Metrics
  - /api-gateway/monitoring/errors/ - Error Metrics
  - /api-gateway/monitoring/rate-limits/ - Rate Limit Events
  - /api-gateway/monitoring/health/ - Health Status
- /api-gateway/settings/ - Settings
- /api-gateway/audit/ - Audit Logs

Usage:
    from api_gateway_routes import register_api_gateway_routes
    register_api_gateway_routes(app, require_login, require_permission, get_db)
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from functools import wraps
from datetime import datetime, timedelta
import json
import csv
import io


def register_api_gateway_routes(app: Flask, require_login, require_permission, get_db):
    """Register all API Gateway routes."""

    # =============================================================================
    # HELPER DECORATORS
    # =============================================================================

    def api_gateway_permission(action):
        """API Gateway-specific permission decorator."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                user_id = session.get('user_id')
                if not user_id:
                    flash("Please login to access this page.", "error")
                    return redirect(url_for('login'))

                # Check for API Admin or Global Admin role
                user_role = session.get('role_name', '')
                if 'API Admin' in user_role or 'Global Admin' in user_role:
                    return f(*args, **kwargs)

                # Check permission via platform permission system
                if not require_permission(user_id, 'platform', 'settings', 'edit'):
                    flash("Access Denied. You need API Gateway admin permissions.", "error")
                    return redirect(url_for('index'))

                return f(*args, **kwargs)
            return decorated_function
        return decorator

    def api_gateway_readonly():
        """API Gateway read-only permission decorator for monitors and auditors."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                user_id = session.get('user_id')
                if not user_id:
                    flash("Please login to access this page.", "error")
                    return redirect(url_for('login'))

                # Allow API Admin, Global Admin, API Monitor, API Support, Auditor
                user_role = session.get('role_name', '')
                allowed_roles = ['API Admin', 'Global Admin', 'API Monitor', 'API Support', 'Auditor']
                if any(role in user_role for role in allowed_roles):
                    return f(*args, **kwargs)

                # Check if user has at least read access
                if not require_permission(user_id, 'platform', 'settings', 'view'):
                    flash("Access Denied. You need API Gateway view permissions.", "error")
                    return redirect(url_for('index'))

                return f(*args, **kwargs)
            return decorated_function
        return decorator

    def get_current_user():
        """Get current user info from session."""
        return {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'role_id': session.get('role_id'),
            'role_name': session.get('role_name'),
            'company_id': session.get('company_id')
        }

    def get_base_context():
        """Get common template context."""
        user = get_current_user()
        user_permissions = session.get('permissions', [])
        return {
            'current_user': user,
            'user_permissions': user_permissions,
            'page_title': 'API Gateway'
        }

    # =============================================================================
    # API GATEWAY DASHBOARD
    # =============================================================================

    @app.route('/api-gateway/')
    @app.route('/api-gateway/dashboard/')
    def api_gateway_dashboard():
        """Main API Gateway dashboard."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_gateway_stats, get_api_usage_metrics, get_api_request_logs, get_api_error_logs, get_webhook_subscriptions

        days = int(request.args.get('days', 7))

        # Get dashboard stats
        stats = get_api_gateway_stats()

        # Get usage metrics for selected period
        metrics = get_api_usage_metrics(days)

        # Get recent request logs
        recent_logs = get_api_request_logs(page=1, per_page=10)
        recent_errors = get_api_error_logs(page=1, per_page=10)

        # Get active webhooks
        active_webhooks = get_webhook_subscriptions({'active': True}, page=1, per_page=5)

        # Prepare chart data
        metrics_labels = [m['date'] for m in metrics] if metrics else []
        metrics_requests = [m['requests'] for m in metrics] if metrics else []
        metrics_errors = [m['errors'] for m in metrics] if metrics else []

        context = get_base_context()
        context.update({
            'stats': stats,
            'metrics': metrics,
            'metrics_labels': metrics_labels,
            'metrics_requests': metrics_requests,
            'metrics_errors': metrics_errors,
            'days': days,
            'recent_logs': recent_logs['logs'],
            'recent_errors': recent_errors['logs'],
            'active_webhooks': active_webhooks['subscriptions'],
            'page_title': 'API Gateway Dashboard'
        })

        return render_template('api_gateway/dashboard.html', **context)

    # =============================================================================
    # REST API MANAGEMENT
    # =============================================================================

    @app.route('/api-gateway/rest-api/')
    @app.route('/api-gateway/rest-api/routes/')
    def api_gateway_routes():
        """Route Registry - list all registered API routes."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_routes, get_api_versions

        # Get filters
        filters = {
            'module': request.args.get('module'),
            'method': request.args.get('method'),
            'version_id': request.args.get('version_id'),
            'is_active': request.args.get('is_active'),
            'search': request.args.get('search'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        routes = get_api_routes(filters=filters, page=page, per_page=per_page)
        versions = get_api_versions()

        # Get modules list
        modules = [
            ('sales', 'Sales'),
            ('crm', 'CRM'),
            ('wms', 'Warehouse'),
            ('inventory', 'Inventory'),
            ('procurement', 'Procurement'),
            ('finance', 'Finance'),
            ('hr', 'HR'),
            ('assets', 'Assets'),
            ('maintenance', 'Maintenance'),
            ('quality', 'Quality'),
            ('logistics', 'Logistics'),
            ('marketing', 'Marketing'),
            ('planning', 'Planning'),
            ('ecommerce', 'E-commerce'),
            ('platform', 'Platform'),
        ]

        context = get_base_context()
        context.update({
            'routes': routes['routes'],
            'total': routes['total'],
            'page': routes['page'],
            'pages': routes['pages'],
            'per_page': per_page,
            'versions': versions,
            'modules': modules,
            'filters': filters,
            'page_title': 'Route Registry'
        })

        return render_template('api_gateway/rest_api/routes.html', **context)

    @app.route('/api-gateway/rest-api/versions/')
    def api_gateway_versions():
        """API Versions management."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_versions

        versions = get_api_versions()

        context = get_base_context()
        context.update({
            'versions': versions,
            'page_title': 'API Versions'
        })

        return render_template('api_gateway/rest_api/versions.html', **context)

    @app.route('/api-gateway/rest-api/logs/')
    def api_gateway_request_logs():
        """API Request Logs."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_request_logs

        filters = {
            'client_id': request.args.get('client_id'),
            'method': request.args.get('method'),
            'path': request.args.get('path'),
            'status_code': request.args.get('status_code'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        logs = get_api_request_logs(filters=filters, page=page, per_page=per_page)

        # Get clients for filter dropdown
        from api_gateway_models import get_api_clients
        clients_result = get_api_clients(page=1, per_page=100)
        clients = clients_result['clients']

        context = get_base_context()
        context.update({
            'logs': logs['logs'],
            'total': logs['total'],
            'page': logs['page'],
            'pages': logs['pages'],
            'per_page': per_page,
            'clients': clients,
            'filters': filters,
            'page_title': 'Request Logs'
        })

        return render_template('api_gateway/rest_api/logs.html', **context)

    @app.route('/api-gateway/rest-api/explorer/')
    def api_gateway_explorer():
        """Interactive API Explorer."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_routes, get_api_versions, get_api_scopes

        versions = get_api_versions()
        routes = get_api_routes(page=1, per_page=200)
        scopes = get_api_scopes()

        context = get_base_context()
        context.update({
            'versions': versions,
            'routes': routes['routes'][:50],  # Limit for explorer
            'scopes': scopes,
            'page_title': 'API Explorer'
        })

        return render_template('api_gateway/rest_api/explorer.html', **context)

    # =============================================================================
    # AUTHENTICATION & ACCESS
    # =============================================================================

    @app.route('/api-gateway/auth/clients/')
    def api_gateway_clients():
        """API Clients list."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_clients, get_count

        filters = {
            'search': request.args.get('search'),
            'status': request.args.get('status'),
            'client_type': request.args.get('client_type'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        clients = get_api_clients(filters=filters, page=page, per_page=per_page)

        # Get additional stats
        total_clients = get_count("api_clients", "")
        active_count = get_count("api_clients", "status='active'")
        pending_count = get_count("api_clients", "status='pending'")
        credentials_count = get_count("api_client_credentials", "is_active=1")

        # Add usage stats to each client
        from database import get_all
        from datetime import datetime, timedelta
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()

        for client in clients['clients']:
            usage = get_all("""
                SELECT COUNT(*) as count FROM api_request_logs
                WHERE client_id = ? AND created_at >= ?
            """, (client['id'], week_ago))
            client['usage_count'] = usage[0]['count'] if usage else 0

            # Calculate usage percentage of rate limit
            if client.get('max_requests_per_day'):
                daily_limit = client['max_requests_per_day']
                client['usage_pct'] = min((client['usage_count'] / daily_limit / 7) * 100, 100)
            else:
                client['usage_pct'] = 0

        context = get_base_context()
        context.update({
            'clients': clients['clients'],
            'total': clients['total'],
            'page': clients['page'],
            'pages': clients['pages'],
            'per_page': per_page,
            'filters': filters,
            'active_count': active_count,
            'pending_count': pending_count,
            'credentials_count': credentials_count,
            'page_title': 'API Clients'
        })

        return render_template('api_gateway/auth/clients.html', **context)

    @app.route('/api-gateway/auth/clients/new/', methods=['GET', 'POST'])
    def api_gateway_clients_new():
        """Create new API Client."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        if request.method == 'POST':
            from api_gateway_models import create_api_client, create_api_client_credential

            data = {
                'client_name': request.form.get('client_name'),
                'client_type': request.form.get('client_type', 'external'),
                'owner_name': request.form.get('owner_name'),
                'owner_email': request.form.get('owner_email'),
                'department': request.form.get('department'),
                'integration_purpose': request.form.get('integration_purpose'),
                'allowed_scopes': request.form.getlist('allowed_scopes'),
                'allowed_modules': request.form.getlist('allowed_modules'),
                'allowed_ip_addresses': request.form.get('allowed_ip_addresses'),
                'rate_limit_profile': request.form.get('rate_limit_profile'),
                'max_requests_per_day': request.form.get('max_requests_per_day'),
                'require_approval': request.form.get('require_approval') == 'on',
                'notes': request.form.get('notes'),
            }

            client_id = create_api_client(data, created_by=session.get('user_id'))

            # Create primary API key credential
            credential = create_api_client_credential(
                client_id, 'api_key', created_by=session.get('user_id'),
                notes='Primary API Key'
            )

            flash(f"API Client created successfully. API Key: {credential['api_key']}", "success")
            return redirect(url_for('api_gateway_clients'))

        from api_gateway_models import get_api_scopes, get_rate_limit_profiles

        scopes = get_api_scopes({'is_active': True})
        rl_profiles = get_rate_limit_profiles()

        modules = [
            ('sales', 'Sales'), ('crm', 'CRM'), ('wms', 'Warehouse'),
            ('procurement', 'Procurement'), ('finance', 'Finance'),
            ('hr', 'HR'), ('assets', 'Assets'), ('maintenance', 'Maintenance'),
            ('quality', 'Quality'), ('logistics', 'Logistics'),
            ('marketing', 'Marketing'), ('ecommerce', 'E-commerce'),
            ('platform', 'Platform'),
        ]

        context = get_base_context()
        context.update({
            'scopes': scopes,
            'rl_profiles': rl_profiles,
            'modules': modules,
            'page_title': 'Create API Client'
        })

        return render_template('api_gateway/auth/client_form.html', **context)

    @app.route('/api-gateway/auth/clients/<int:client_id>/')
    def api_gateway_client_detail(client_id):
        """API Client detail view."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import (
            get_api_client_by_id, get_api_client_credentials,
            get_rate_limit_profile
        )

        client = get_api_client_by_id(client_id)
        if not client:
            flash("API Client not found.", "error")
            return redirect(url_for('api_gateway_clients'))

        credentials = get_api_client_credentials(client_id)
        rl_profile = get_rate_limit_profile(client['rate_limit_profile']) if client.get('rate_limit_profile') else None

        # Parse JSON fields
        if client.get('allowed_scopes') and isinstance(client['allowed_scopes'], str):
            try:
                client['allowed_scopes_list'] = json.loads(client['allowed_scopes'])
            except:
                client['allowed_scopes_list'] = []
        else:
            client['allowed_scopes_list'] = client.get('allowed_scopes', [])

        if client.get('allowed_modules') and isinstance(client['allowed_modules'], str):
            try:
                client['allowed_modules_list'] = json.loads(client['allowed_modules'])
            except:
                client['allowed_modules_list'] = []
        else:
            client['allowed_modules_list'] = client.get('allowed_modules', [])

        context = get_base_context()
        context.update({
            'client': client,
            'credentials': credentials,
            'rl_profile': rl_profile,
            'page_title': f"API Client: {client['client_name']}"
        })

        return render_template('api_gateway/auth/client_detail.html', **context)

    @app.route('/api-gateway/auth/clients/<int:client_id>/edit/', methods=['GET', 'POST'])
    def api_gateway_client_edit(client_id):
        """Edit API Client."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_client_by_id, update_api_client, get_api_scopes, get_rate_limit_profiles

        client = get_api_client_by_id(client_id)
        if not client:
            flash("API Client not found.", "error")
            return redirect(url_for('api_gateway_clients'))

        if request.method == 'POST':
            data = {
                'client_name': request.form.get('client_name'),
                'owner_name': request.form.get('owner_name'),
                'owner_email': request.form.get('owner_email'),
                'department': request.form.get('department'),
                'integration_purpose': request.form.get('integration_purpose'),
                'allowed_scopes': request.form.getlist('allowed_scopes'),
                'allowed_modules': request.form.getlist('allowed_modules'),
                'allowed_ip_addresses': request.form.get('allowed_ip_addresses'),
                'rate_limit_profile': request.form.get('rate_limit_profile'),
                'max_requests_per_day': request.form.get('max_requests_per_day'),
                'status': request.form.get('status'),
                'notes': request.form.get('notes'),
            }

            update_api_client(client_id, data)
            flash("API Client updated successfully.", "success")
            return redirect(url_for('api_gateway_client_detail', client_id=client_id))

        scopes = get_api_scopes({'is_active': True})
        rl_profiles = get_rate_limit_profiles()

        # Parse JSON fields
        if client.get('allowed_scopes') and isinstance(client['allowed_scopes'], str):
            try:
                client['allowed_scopes_list'] = json.loads(client['allowed_scopes'])
            except:
                client['allowed_scopes_list'] = []
        else:
            client['allowed_scopes_list'] = client.get('allowed_scopes', [])

        if client.get('allowed_modules') and isinstance(client['allowed_modules'], str):
            try:
                client['allowed_modules_list'] = json.loads(client['allowed_modules'])
            except:
                client['allowed_modules_list'] = []
        else:
            client['allowed_modules_list'] = client.get('allowed_modules', [])

        modules = [
            ('sales', 'Sales'), ('crm', 'CRM'), ('wms', 'Warehouse'),
            ('procurement', 'Procurement'), ('finance', 'Finance'),
            ('hr', 'HR'), ('assets', 'Assets'), ('maintenance', 'Maintenance'),
            ('quality', 'Quality'), ('logistics', 'Logistics'),
            ('marketing', 'Marketing'), ('ecommerce', 'E-commerce'),
            ('platform', 'Platform'),
        ]

        context = get_base_context()
        context.update({
            'client': client,
            'scopes': scopes,
            'rl_profiles': rl_profiles,
            'modules': modules,
            'page_title': f"Edit API Client: {client['client_name']}"
        })

        return render_template('api_gateway/auth/client_form.html', **context)

    @app.route('/api-gateway/auth/clients/<int:client_id>/credentials/new/', methods=['POST'])
    def api_gateway_new_credential(client_id):
        """Create new credential for API client."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import create_api_client_credential, get_api_client_by_id

        credential_type = request.form.get('credential_type', 'api_key')

        credential = create_api_client_credential(
            client_id, credential_type,
            created_by=session.get('user_id'),
            notes=request.form.get('notes')
        )

        # Return JSON for AJAX
        if request.headers.get('Accept') == 'application/json' or request.is_json:
            return jsonify({
                'success': True,
                'credential': {
                    'id': credential['id'],
                    'type': credential['credential_type'],
                    'api_key': credential.get('api_key'),
                    'api_secret': credential.get('api_secret'),
                    'jwt_secret': credential.get('jwt_secret'),
                }
            })

        flash("Credential created successfully.", "success")
        return redirect(url_for('api_gateway_client_detail', client_id=client_id))

    @app.route('/api-gateway/auth/scopes/')
    def api_gateway_scopes():
        """API Scopes management."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_scopes

        filters = {
            'module': request.args.get('module'),
            'search': request.args.get('search'),
        }

        scopes = get_api_scopes(filters=filters)

        # Group by module
        scopes_by_module = {}
        for scope in scopes:
            mod = scope['module']
            if mod not in scopes_by_module:
                scopes_by_module[mod] = []
            scopes_by_module[mod].append(scope)

        modules = [
            ('sales', 'Sales'), ('crm', 'CRM'), ('wms', 'Warehouse'),
            ('inventory', 'Inventory'), ('procurement', 'Procurement'),
            ('finance', 'Finance'), ('hr', 'HR'), ('assets', 'Assets'),
            ('maintenance', 'Maintenance'), ('quality', 'Quality'),
            ('logistics', 'Logistics'), ('marketing', 'Marketing'),
            ('planning', 'Planning'), ('ecommerce', 'E-commerce'),
            ('platform', 'Platform'), ('reports', 'Reports'),
        ]

        context = get_base_context()
        context.update({
            'scopes': scopes,
            'scopes_by_module': scopes_by_module,
            'modules': modules,
            'filters': filters,
            'page_title': 'API Scopes'
        })

        return render_template('api_gateway/auth/scopes.html', **context)

    @app.route('/api-gateway/auth/policies/')
    def api_gateway_policies():
        """Access Policies management."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        context = get_base_context()
        context.update({
            'page_title': 'Access Policies'
        })

        return render_template('api_gateway/auth/policies.html', **context)

    # =============================================================================
    # WEBHOOKS
    # =============================================================================

    @app.route('/api-gateway/webhooks/')
    @app.route('/api-gateway/webhooks/events/')
    def api_gateway_webhook_events():
        """Webhook Event Catalog."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_webhook_events

        filters = {
            'module': request.args.get('module'),
            'search': request.args.get('search'),
        }

        events = get_webhook_events(filters=filters)

        # Group by module
        events_by_module = {}
        for event in events:
            mod = event['module']
            if mod not in events_by_module:
                events_by_module[mod] = []
            events_by_module[mod].append(event)

        modules = [
            ('sales', 'Sales'), ('crm', 'CRM'), ('wms', 'Warehouse'),
            ('inventory', 'Inventory'), ('procurement', 'Procurement'),
            ('finance', 'Finance'), ('hr', 'HR'), ('assets', 'Assets'),
            ('maintenance', 'Maintenance'), ('quality', 'Quality'),
            ('logistics', 'Logistics'), ('marketing', 'Marketing'),
            ('ecommerce', 'E-commerce'), ('platform', 'Platform'),
        ]

        context = get_base_context()
        context.update({
            'events': events,
            'events_by_module': events_by_module,
            'modules': modules,
            'filters': filters,
            'page_title': 'Webhook Event Catalog'
        })

        return render_template('api_gateway/webhooks/events.html', **context)

    @app.route('/api-gateway/webhooks/subscriptions/')
    def api_gateway_webhook_subscriptions():
        """Webhook Subscriptions list."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_webhook_subscriptions, get_count

        filters = {
            'active': request.args.get('active'),
            'search': request.args.get('search'),
            'event_code': request.args.get('event_code'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        subscriptions = get_webhook_subscriptions(filters=filters, page=page, per_page=per_page)

        # Get webhook stats
        total_subs = get_count("webhook_subscriptions", "")
        active_subs = get_count("webhook_subscriptions", "active=1")
        deliveries_today = get_count("webhook_deliveries", "created_at >= datetime('now', '-1 day')")
        failed_today = get_count("webhook_deliveries", "delivery_status='failed' AND created_at >= datetime('now', '-1 day')")

        context = get_base_context()
        context.update({
            'subscriptions': subscriptions['subscriptions'],
            'total': subscriptions['total'],
            'page': subscriptions['page'],
            'pages': subscriptions['pages'],
            'per_page': per_page,
            'filters': filters,
            'total_subs': total_subs,
            'active_subs': active_subs,
            'deliveries_today': deliveries_today,
            'failed_today': failed_today,
            'page_title': 'Webhook Subscriptions'
        })

        return render_template('api_gateway/webhooks/subscriptions.html', **context)

    @app.route('/api-gateway/webhooks/subscriptions/new/', methods=['GET', 'POST'])
    def api_gateway_webhook_new():
        """Create new Webhook Subscription."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        if request.method == 'POST':
            from api_gateway_models import create_webhook_subscription, get_webhook_events

            subscribed_events = request.form.getlist('subscribed_events')

            data = {
                'endpoint_name': request.form.get('endpoint_name'),
                'target_url': request.form.get('target_url'),
                'active': request.form.get('active') == 'on',
                'subscribed_events': subscribed_events,
                'auth_method': request.form.get('auth_method', 'none'),
                'auth_secret': request.form.get('auth_secret') if request.form.get('auth_method') == 'secret' else None,
                'auth_header_name': request.form.get('auth_header_name', 'X-Webhook-Signature'),
                'retry_policy': {
                    'max_retries': int(request.form.get('max_retries', 3)),
                    'backoff': request.form.get('retry_backoff', 'exponential')
                },
                'timeout_seconds': int(request.form.get('timeout_seconds', 30)),
                'max_retries': int(request.form.get('max_retries', 3)),
                'owner_name': request.form.get('owner_name'),
                'owner_email': request.form.get('owner_email'),
                'environment_tag': request.form.get('environment_tag'),
                'notes': request.form.get('notes'),
            }

            sub_id = create_webhook_subscription(data, created_by=session.get('user_id'))
            flash("Webhook subscription created successfully.", "success")
            return redirect(url_for('api_gateway_webhook_subscriptions'))

        from api_gateway_models import get_webhook_events

        events = get_webhook_events({'is_active': True})

        context = get_base_context()
        context.update({
            'events': events,
            'page_title': 'Create Webhook Subscription'
        })

        return render_template('api_gateway/webhooks/subscription_form.html', **context)

    @app.route('/api-gateway/webhooks/subscriptions/<int:sub_id>/')
    def api_gateway_webhook_detail(sub_id):
        """Webhook Subscription detail."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_webhook_subscription_by_id, get_webhook_deliveries

        subscription = get_webhook_subscription_by_id(sub_id)
        if not subscription:
            flash("Webhook subscription not found.", "error")
            return redirect(url_for('api_gateway_webhook_subscriptions'))

        deliveries = get_webhook_deliveries({'subscription_id': sub_id}, page=1, per_page=20)

        # Parse JSON fields
        if subscription.get('subscribed_events'):
            try:
                subscription['events_list'] = json.loads(subscription['subscribed_events'])
            except:
                subscription['events_list'] = []
        else:
            subscription['events_list'] = []

        context = get_base_context()
        context.update({
            'subscription': subscription,
            'deliveries': deliveries['deliveries'],
            'page_title': f"Webhook: {subscription['endpoint_name']}"
        })

        return render_template('api_gateway/webhooks/subscription_detail.html', **context)

    @app.route('/api-gateway/webhooks/subscriptions/<int:sub_id>/edit/', methods=['GET', 'POST'])
    def api_gateway_webhook_edit(sub_id):
        """Edit Webhook Subscription."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_webhook_subscription_by_id, update_webhook_subscription, get_webhook_events

        subscription = get_webhook_subscription_by_id(sub_id)
        if not subscription:
            flash("Webhook subscription not found.", "error")
            return redirect(url_for('api_gateway_webhook_subscriptions'))

        if request.method == 'POST':
            subscribed_events = request.form.getlist('subscribed_events')

            data = {
                'endpoint_name': request.form.get('endpoint_name'),
                'target_url': request.form.get('target_url'),
                'active': request.form.get('active') == 'on',
                'subscribed_events': subscribed_events,
                'auth_method': request.form.get('auth_method', 'none'),
                'auth_secret': request.form.get('auth_secret') if request.form.get('auth_method') == 'secret' else None,
                'auth_header_name': request.form.get('auth_header_name', 'X-Webhook-Signature'),
                'retry_policy': {
                    'max_retries': int(request.form.get('max_retries', 3)),
                    'backoff': request.form.get('retry_backoff', 'exponential')
                },
                'timeout_seconds': int(request.form.get('timeout_seconds', 30)),
                'max_retries': int(request.form.get('max_retries', 3)),
                'owner_name': request.form.get('owner_name'),
                'owner_email': request.form.get('owner_email'),
                'environment_tag': request.form.get('environment_tag'),
                'notes': request.form.get('notes'),
            }

            update_webhook_subscription(sub_id, data)
            flash("Webhook subscription updated successfully.", "success")
            return redirect(url_for('api_gateway_webhook_detail', sub_id=sub_id))

        events = get_webhook_events({'is_active': True})

        if subscription.get('subscribed_events'):
            try:
                subscription['events_list'] = json.loads(subscription['subscribed_events'])
            except:
                subscription['events_list'] = []
        else:
            subscription['events_list'] = []

        context = get_base_context()
        context.update({
            'subscription': subscription,
            'events': events,
            'page_title': f"Edit Webhook: {subscription['endpoint_name']}"
        })

        return render_template('api_gateway/webhooks/subscription_form.html', **context)

    @app.route('/api-gateway/webhooks/deliveries/')
    def api_gateway_webhook_deliveries():
        """Webhook Delivery Logs."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_webhook_deliveries, get_webhook_subscriptions, get_count
        from datetime import datetime, timedelta

        filters = {
            'subscription_id': request.args.get('subscription_id'),
            'event_code': request.args.get('event_code'),
            'status': request.args.get('status'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        deliveries = get_webhook_deliveries(filters=filters, page=page, per_page=per_page)
        subscriptions = get_webhook_subscriptions(page=1, per_page=100)

        # Calculate stats
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
        total_deliveries = get_count("webhook_deliveries", f"created_at >= '{week_ago}'")
        success_count = get_count("webhook_deliveries", f"delivery_status='success' AND created_at >= '{week_ago}'")
        failed_count = get_count("webhook_deliveries", f"delivery_status='failed' AND created_at >= '{week_ago}'")
        pending_count = get_count("webhook_deliveries", f"delivery_status='pending' AND created_at >= '{week_ago}'")

        success_rate = (success_count / total_deliveries * 100) if total_deliveries > 0 else 100

        # Average delivery time
        from database import get_one
        avg_result = get_one("""
            SELECT AVG(response_time_ms) FROM webhook_deliveries
            WHERE created_at >= ? AND response_time_ms IS NOT NULL
        """, (week_ago,))
        avg_delivery_time = round(avg_result[0], 2) if avg_result and avg_result[0] else 0

        # Trend data for chart (last 7 days)
        trend_labels = []
        success_trend = []
        failed_trend = []
        for i in range(7):
            day = (datetime.utcnow() - timedelta(days=i)).date().isoformat()
            trend_labels.insert(0, day)
            day_start = f"{day} 00:00:00"
            day_end = f"{day} 23:59:59"
            success_trend.insert(0, get_count("webhook_deliveries", f"delivery_status='success' AND created_at >= '{day_start}' AND created_at <= '{day_end}'"))
            failed_trend.insert(0, get_count("webhook_deliveries", f"delivery_status='failed' AND created_at >= '{day_start}' AND created_at <= '{day_end}'"))

        context = get_base_context()
        context.update({
            'deliveries': deliveries['deliveries'],
            'total': deliveries['total'],
            'page': deliveries['page'],
            'pages': deliveries['pages'],
            'per_page': per_page,
            'subscriptions': subscriptions['subscriptions'],
            'filters': filters,
            'total_deliveries': total_deliveries,
            'success_count': success_count,
            'failed_count': failed_count,
            'pending_count': pending_count,
            'success_rate': success_rate,
            'avg_delivery_time': avg_delivery_time,
            'trend_labels': trend_labels,
            'success_trend': success_trend,
            'failed_trend': failed_trend,
            'page_title': 'Webhook Deliveries'
        })

        return render_template('api_gateway/webhooks/deliveries.html', **context)

    @app.route('/api-gateway/webhooks/failed/')
    def api_gateway_webhook_failed():
        """Failed Webhook Deliveries."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_webhook_deliveries, get_webhook_subscriptions

        filters = {
            'status': 'failed',
            'subscription_id': request.args.get('subscription_id'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        deliveries = get_webhook_deliveries(filters=filters, page=page, per_page=per_page)
        subscriptions = get_webhook_subscriptions(page=1, per_page=100)

        context = get_base_context()
        context.update({
            'deliveries': deliveries['deliveries'],
            'total': deliveries['total'],
            'page': deliveries['page'],
            'pages': deliveries['pages'],
            'per_page': per_page,
            'subscriptions': subscriptions['subscriptions'],
            'filters': filters,
            'page_title': 'Failed Deliveries'
        })

        return render_template('api_gateway/webhooks/failed.html', **context)

    @app.route('/api-gateway/webhooks/deliveries/<delivery_id>/retry/', methods=['POST'])
    def api_gateway_retry_delivery(delivery_id):
        """Retry a failed webhook delivery."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import retry_webhook_delivery

        success = retry_webhook_delivery(delivery_id)

        if request.headers.get('Accept') == 'application/json' or request.is_json:
            return jsonify({'success': success})

        if success:
            flash("Webhook delivery queued for retry.", "success")
        else:
            flash("Could not retry delivery. Maximum attempts reached.", "error")

        return redirect(url_for('api_gateway_webhook_deliveries'))

    # =============================================================================
    # INTEGRATIONS
    # =============================================================================

    @app.route('/api-gateway/integrations/')
    @app.route('/api-gateway/integrations/profiles/')
    def api_gateway_integrations():
        """Integration Profiles list."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_integration_profiles

        filters = {
            'integration_type': request.args.get('integration_type'),
            'module': request.args.get('module'),
            'direction': request.args.get('direction'),
            'is_active': request.args.get('is_active'),
            'search': request.args.get('search'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        profiles = get_integration_profiles(filters=filters, page=page, per_page=per_page)

        context = get_base_context()
        context.update({
            'profiles': profiles['profiles'],
            'total': profiles['total'],
            'page': profiles['page'],
            'pages': profiles['pages'],
            'per_page': per_page,
            'filters': filters,
            'page_title': 'Integration Profiles'
        })

        return render_template('api_gateway/integrations/profiles.html', **context)

    @app.route('/api-gateway/integrations/profiles/new/', methods=['GET', 'POST'])
    def api_gateway_integration_new():
        """Create new Integration Profile."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        if request.method == 'POST':
            from api_gateway_models import create_integration_profile

            data = {
                'integration_name': request.form.get('integration_name'),
                'integration_type': request.form.get('integration_type'),
                'module': request.form.get('module'),
                'direction': request.form.get('direction'),
                'description': request.form.get('description'),
                'module_scope': request.form.getlist('module_scope'),
                'sync_schedule': request.form.get('sync_schedule'),
                'sync_trigger': request.form.get('sync_trigger', 'manual'),
                'retry_policy': {
                    'max_retries': int(request.form.get('max_retries', 3)),
                    'backoff': request.form.get('retry_backoff', 'exponential')
                },
                'timeout_seconds': int(request.form.get('timeout_seconds', 30)),
                'owner_name': request.form.get('owner_name'),
                'owner_email': request.form.get('owner_email'),
                'department': request.form.get('department'),
                'notes': request.form.get('notes'),
            }

            profile_id = create_integration_profile(data, created_by=session.get('user_id'))
            flash("Integration profile created successfully.", "success")
            return redirect(url_for('api_gateway_integrations'))

        modules = [
            ('sales', 'Sales'), ('crm', 'CRM'), ('wms', 'Warehouse'),
            ('inventory', 'Inventory'), ('procurement', 'Procurement'),
            ('finance', 'Finance'), ('hr', 'HR'), ('assets', 'Assets'),
            ('maintenance', 'Maintenance'), ('quality', 'Quality'),
            ('logistics', 'Logistics'), ('marketing', 'Marketing'),
            ('ecommerce', 'E-commerce'), ('platform', 'Platform'),
        ]

        integration_types = [
            ('ecommerce', 'E-commerce Platform'),
            ('accounting', 'Accounting System'),
            ('shipping', 'Shipping Provider'),
            ('crm', 'CRM System'),
            ('bi', 'Business Intelligence'),
            ('partner', 'Partner Integration'),
            ('mobile', 'Mobile App'),
            ('custom', 'Custom Integration'),
        ]

        context = get_base_context()
        context.update({
            'modules': modules,
            'integration_types': integration_types,
            'page_title': 'Create Integration Profile'
        })

        return render_template('api_gateway/integrations/profile_form.html', **context)

    @app.route('/api-gateway/integrations/profiles/<int:profile_id>/')
    def api_gateway_integration_detail(profile_id):
        """Integration Profile detail."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_integration_profile_by_id, get_integration_runs

        profile = get_integration_profile_by_id(profile_id)
        if not profile:
            flash("Integration profile not found.", "error")
            return redirect(url_for('api_gateway_integrations'))

        runs = get_integration_runs({'integration_id': profile_id}, page=1, per_page=20)

        context = get_base_context()
        context.update({
            'profile': profile,
            'runs': runs['runs'],
            'page_title': f"Integration: {profile['integration_name']}"
        })

        return render_template('api_gateway/integrations/profile_detail.html', **context)

    @app.route('/api-gateway/integrations/runs/')
    def api_gateway_integration_runs():
        """Integration Runs history."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_integration_runs, get_integration_profiles

        filters = {
            'integration_id': request.args.get('integration_id'),
            'status': request.args.get('status'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        runs = get_integration_runs(filters=filters, page=page, per_page=per_page)
        profiles = get_integration_profiles(page=1, per_page=100)

        context = get_base_context()
        context.update({
            'runs': runs['runs'],
            'total': runs['total'],
            'page': runs['page'],
            'pages': runs['pages'],
            'per_page': per_page,
            'profiles': profiles['profiles'],
            'filters': filters,
            'page_title': 'Integration Runs'
        })

        return render_template('api_gateway/integrations/runs.html', **context)

    @app.route('/api-gateway/integrations/exceptions/')
    def api_gateway_integration_exceptions():
        """Integration Exceptions."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_integration_exceptions, get_integration_profiles

        filters = {
            'integration_id': request.args.get('integration_id'),
            'is_resolved': request.args.get('is_resolved'),
            'exception_type': request.args.get('exception_type'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        exceptions = get_integration_exceptions(filters=filters, page=page, per_page=per_page)
        profiles = get_integration_profiles(page=1, per_page=100)

        context = get_base_context()
        context.update({
            'exceptions': exceptions['exceptions'],
            'total': exceptions['total'],
            'page': exceptions['page'],
            'pages': exceptions['pages'],
            'per_page': per_page,
            'profiles': profiles['profiles'],
            'filters': filters,
            'page_title': 'Integration Exceptions'
        })

        return render_template('api_gateway/integrations/exceptions.html', **context)

    # =============================================================================
    # DOCUMENTATION
    # =============================================================================

    @app.route('/api-gateway/docs/')
    def api_gateway_docs():
        """API Documentation index."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_docs, get_api_versions

        docs = get_api_docs({'is_published': True}, page=1, per_page=50)
        versions = get_api_versions()

        context = get_base_context()
        context.update({
            'docs': docs['docs'],
            'versions': versions,
            'page_title': 'API Documentation'
        })

        return render_template('api_gateway/docs/index.html', **context)

    @app.route('/api-gateway/docs/openapi/')
    def api_gateway_openapi():
        """OpenAPI/Swagger documentation."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_routes, get_api_versions, get_api_scopes

        routes = get_api_routes(page=1, per_page=500)
        versions = get_api_versions()
        scopes = get_api_scopes({'is_active': True})

        # Build OpenAPI spec
        openapi_spec = {
            'openapi': '3.0.0',
            'info': {
                'title': 'MMDx API',
                'description': 'Enterprise API Gateway for MMDx Platform',
                'version': '2.0'
            },
            'servers': [{'url': '/api/v1'}, {'url': '/api/v2'}],
            'paths': {}
        }

        for route in routes['routes']:
            path = route['path']
            if path not in openapi_spec['paths']:
                openapi_spec['paths'][path] = {}

            method = route['method'].lower()
            openapi_spec['paths'][path][method] = {
                'summary': route.get('description', f"{route['method']} {route['path']}"),
                'tags': [route['module']],
                'security': [{'apiKey': []}] if route.get('auth_required') else [],
                'responses': {
                    '200': {'description': 'Successful response'},
                    '401': {'description': 'Unauthorized'},
                    '403': {'description': 'Forbidden'},
                }
            }

        context = get_base_context()
        context.update({
            'openapi_spec': json.dumps(openapi_spec, indent=2),
            'page_title': 'OpenAPI Specification'
        })

        return render_template('api_gateway/docs/openapi.html', **context)

    @app.route('/api-gateway/docs/guides/')
    def api_gateway_guides():
        """API Guides documentation."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        context = get_base_context()
        context.update({
            'page_title': 'API Guides'
        })

        return render_template('api_gateway/docs/guides.html', **context)

    @app.route('/api-gateway/docs/auth/')
    def api_gateway_auth_docs():
        """Authentication documentation."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        context = get_base_context()
        context.update({
            'page_title': 'Authentication Guide'
        })

        return render_template('api_gateway/docs/auth_guide.html', **context)

    @app.route('/api-gateway/docs/errors/')
    def api_gateway_error_codes():
        """Error Code Reference."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        error_codes = [
            {'code': 'AUTH_001', 'type': 'Authentication', 'message': 'Invalid API key', 'description': 'The provided API key is invalid or has been revoked.'},
            {'code': 'AUTH_002', 'type': 'Authentication', 'message': 'Expired token', 'description': 'The authentication token has expired.'},
            {'code': 'AUTH_003', 'type': 'Authentication', 'message': 'Insufficient scopes', 'description': 'The API key does not have required scopes.'},
            {'code': 'RATE_001', 'type': 'Rate Limiting', 'message': 'Rate limit exceeded', 'description': 'Too many requests. Please wait before retrying.'},
            {'code': 'VAL_001', 'type': 'Validation', 'message': 'Invalid request body', 'description': 'The request body does not match the expected schema.'},
            {'code': 'VAL_002', 'type': 'Validation', 'message': 'Missing required field', 'description': 'A required field is missing from the request.'},
            {'code': 'NOT_FOUND', 'type': 'Resource', 'message': 'Resource not found', 'description': 'The requested resource does not exist.'},
            {'code': 'FORBIDDEN', 'type': 'Authorization', 'message': 'Access denied', 'description': 'You do not have permission to access this resource.'},
            {'code': 'SERVER_ERROR', 'type': 'Server', 'message': 'Internal server error', 'description': 'An unexpected error occurred. Please try again later.'},
        ]

        context = get_base_context()
        context.update({
            'error_codes': error_codes,
            'page_title': 'Error Code Reference'
        })

        return render_template('api_gateway/docs/error_codes.html', **context)

    # =============================================================================
    # MONITORING
    # =============================================================================

    @app.route('/api-gateway/monitoring/')
    @app.route('/api-gateway/monitoring/usage/')
    def api_gateway_usage():
        """API Usage Metrics."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_usage_metrics

        days = int(request.args.get('days', 7))
        metrics = get_api_usage_metrics(days)

        # Get top clients by request count
        from database import get_all, get_count
        top_clients = get_all("""
            SELECT ac.client_name, ac.client_code, COUNT(*) as request_count
            FROM api_request_logs arl
            JOIN api_clients ac ON arl.client_id = ac.id
            WHERE arl.created_at >= datetime('now', '-{} days')
            GROUP BY ac.id
            ORDER BY request_count DESC
            LIMIT 10
        """.format(days))

        # Get top endpoints by request count
        top_endpoints = get_all("""
            SELECT method, path, COUNT(*) as request_count
            FROM api_request_logs
            WHERE created_at >= datetime('now', '-{} days')
            GROUP BY method, path
            ORDER BY request_count DESC
            LIMIT 10
        """.format(days))

        # Calculate totals and averages
        total_requests = sum(m['requests'] for m in metrics) if metrics else 0
        total_errors = sum(m['errors'] for m in metrics) if metrics else 0
        avg_response = sum(m['avg_response_ms'] for m in metrics) / len(metrics) if metrics and metrics else 0

        # Error rate and success rate
        success_rate = ((total_requests - total_errors) / total_requests * 100) if total_requests > 0 else 100

        # P50, P90, P95, P99 from database
        from api_gateway_models import get_db
        p50, p90, p95, p99, p95_response, timeout_count = 0, 0, 0, 0, 0, 0
        try:
            with get_db() as db:
                # P50 (median)
                p50_row = db.execute("""
                    SELECT response_time_ms FROM api_request_logs
                    WHERE created_at >= datetime('now', '-{} days') AND response_time_ms IS NOT NULL
                    ORDER BY response_time_ms ASC
                    LIMIT 1 OFFSET (SELECT COUNT(*) / 2 FROM api_request_logs
                                    WHERE created_at >= datetime('now', '-{} days') AND response_time_ms IS NOT NULL)
                """.format(days, days)).fetchone()
                p50 = p50_row[0] if p50_row else 0

                # P95
                p95_row = db.execute("""
                    SELECT response_time_ms FROM api_request_logs
                    WHERE created_at >= datetime('now', '-{} days') AND response_time_ms IS NOT NULL
                    ORDER BY response_time_ms ASC
                    LIMIT 1 OFFSET (SELECT COUNT(*) * 95 / 100 FROM api_request_logs
                                    WHERE created_at >= datetime('now', '-{} days') AND response_time_ms IS NOT NULL)
                """.format(days, days)).fetchone()
                p95 = p95_row[0] if p95_row else 0

                # P99
                p99_row = db.execute("""
                    SELECT response_time_ms FROM api_request_logs
                    WHERE created_at >= datetime('now', '-{} days') AND response_time_ms IS NOT NULL
                    ORDER BY response_time_ms ASC
                    LIMIT 1 OFFSET (SELECT COUNT(*) * 99 / 100 FROM api_request_logs
                                    WHERE created_at >= datetime('now', '-{} days') AND response_time_ms IS NOT NULL)
                """.format(days, days)).fetchone()
                p99 = p99_row[0] if p99_row else 0

                # Timeout count
                timeout_row = db.execute("""
                    SELECT COUNT(*) FROM api_request_logs
                    WHERE created_at >= datetime('now', '-{} days') AND response_time_ms > 30000
                """.format(days)).fetchone()
                timeout_count = timeout_row[0] if timeout_row else 0

                # P95 for display
                p95_response = p95
        except:
            pass

        # Prepare chart data
        metrics_labels = [m['date'] for m in metrics] if metrics else []
        metrics_requests = [m['requests'] for m in metrics] if metrics else []
        metrics_errors = [m['errors'] for m in metrics] if metrics else []
        error_rates = [m['error_rate'] for m in metrics] if metrics else []

        # Client chart data
        client_names = [c['client_name'] for c in top_clients] if top_clients else []
        client_counts = [c['request_count'] for c in top_clients] if top_clients else []

        # Endpoint chart data
        endpoint_labels = [f"{e['method']} {e['path'][:30]}" for e in top_endpoints] if top_endpoints else []
        endpoint_counts = [e['request_count'] for e in top_endpoints] if top_endpoints else []

        context = get_base_context()
        context.update({
            'metrics': metrics,
            'metrics_labels': metrics_labels,
            'metrics_requests': metrics_requests,
            'metrics_errors': metrics_errors,
            'error_rates': error_rates,
            'days': days,
            'total_requests': total_requests,
            'total_errors': total_errors,
            'success_rate': success_rate,
            'avg_response': round(avg_response, 2),
            'p50': p50,
            'p90': p90,
            'p95': p95,
            'p99': p99,
            'p95_response': p95_response,
            'timeout_count': timeout_count,
            'top_clients': top_clients,
            'top_endpoints': top_endpoints,
            'client_names': client_names,
            'client_counts': client_counts,
            'endpoint_labels': endpoint_labels,
            'endpoint_counts': endpoint_counts,
            'page_title': 'Usage Metrics'
        })

        return render_template('api_gateway/monitoring/usage.html', **context)

    @app.route('/api-gateway/monitoring/errors/')
    def api_gateway_errors():
        """API Error Metrics."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_error_logs

        filters = {
            'error_type': request.args.get('error_type'),
            'is_resolved': request.args.get('is_resolved'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        errors = get_api_error_logs(filters=filters, page=page, per_page=per_page)

        # Get error summary
        from database import get_all, get_count
        error_summary = get_all("""
            SELECT error_code, error_type, COUNT(*) as count
            FROM api_error_logs
            WHERE created_at >= datetime('now', '-7 days')
            GROUP BY error_code, error_type
            ORDER BY count DESC
            LIMIT 20
        """)

        # Error counts by type
        from datetime import datetime, timedelta
        week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()

        client_errors = get_count("api_error_logs", f"error_type = 'client' AND created_at >= '{week_ago}'")
        server_errors = get_count("api_error_logs", f"error_type = 'server' AND created_at >= '{week_ago}'")
        timeout_errors = get_count("api_error_logs", f"error_type = 'timeout' AND created_at >= '{week_ago}'")
        auth_errors = get_count("api_error_logs", f"error_type = 'auth' AND created_at >= '{week_ago}'")
        resolved_errors = get_count("api_error_logs", f"is_resolved = 1 AND created_at >= '{week_ago}'")

        # Average resolution time (in minutes)
        avg_resolution_time = 0

        # Error trend data for chart (last 7 days)
        error_trend_labels = []
        error_trend_data = []
        for i in range(7):
            day = (datetime.utcnow() - timedelta(days=i)).date().isoformat()
            error_trend_labels.insert(0, day)
            count = get_count("api_error_logs", f"created_at >= '{day} 00:00:00' AND created_at <= '{day} 23:59:59'")
            error_trend_data.insert(0, count)

        context = get_base_context()
        context.update({
            'errors': errors['logs'],
            'total': errors['total'],
            'page': errors['page'],
            'pages': errors['pages'],
            'per_page': per_page,
            'error_summary': error_summary,
            'filters': filters,
            'client_errors': client_errors,
            'server_errors': server_errors,
            'timeout_errors': timeout_errors,
            'auth_errors': auth_errors,
            'resolved_errors': resolved_errors,
            'avg_resolution_time': avg_resolution_time,
            'error_trend_labels': error_trend_labels,
            'error_trend_data': error_trend_data,
            'page_title': 'Error Metrics'
        })

        return render_template('api_gateway/monitoring/errors.html', **context)

    @app.route('/api-gateway/export/errors/csv/')
    def api_gateway_export_errors_csv():
        """Export error logs as CSV."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_error_logs

        filters = {
            'error_type': request.args.get('error_type'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
        }

        errors = get_api_error_logs(filters=filters, page=1, per_page=10000)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Error ID', 'Error Code', 'Type', 'Message', 'Method', 'Path', 'Client', 'Resolved', 'Created At'])

        for e in errors['logs']:
            writer.writerow([
                e.get('error_id'),
                e.get('error_code'),
                e.get('error_type'),
                e.get('error_message'),
                e.get('method'),
                e.get('path'),
                e.get('client_code'),
                'Yes' if e.get('is_resolved') else 'No',
                e.get('created_at'),
            ])

        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'api_errors_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

    @app.route('/api-gateway/export/errors/json/')
    def api_gateway_export_errors_json():
        """Export error logs as JSON."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_error_logs

        filters = {
            'error_type': request.args.get('error_type'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
        }

        errors = get_api_error_logs(filters=filters, page=1, per_page=10000)

        response = jsonify({
            'export_date': datetime.now().isoformat(),
            'total_records': len(errors['logs']),
            'errors': errors['logs']
        })
        response.headers['Content-Disposition'] = f'attachment; filename=api_errors_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        return response

    @app.route('/api-gateway/monitoring/rate-limits/')
    def api_gateway_rate_limits():
        """Rate Limit Events."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from database import get_all

        # Get rate-limited requests
        rate_limited = get_all("""
            SELECT arl.client_id, ac.client_name, ac.client_code,
                   COUNT(*) as limited_count,
                   MIN(arl.created_at) as first_limited,
                   MAX(arl.created_at) as last_limited
            FROM api_request_logs arl
            JOIN api_clients ac ON arl.client_id = ac.id
            WHERE arl.response_status_code = 429
            AND arl.created_at >= datetime('now', '-7 days')
            GROUP BY arl.client_id
            ORDER BY limited_count DESC
        """)

        context = get_base_context()
        context.update({
            'rate_limited': rate_limited,
            'page_title': 'Rate Limit Events'
        })

        return render_template('api_gateway/monitoring/rate_limits.html', **context)

    @app.route('/api-gateway/monitoring/health/')
    def api_gateway_health():
        """API Health Status."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_versions
        from database import get_one, get_all, get_count
        from datetime import datetime, timedelta

        # Check database
        db_status = 'healthy'
        try:
            get_one("SELECT 1")
        except:
            db_status = 'unhealthy'

        # Get versions
        versions = get_api_versions()

        # Get route count per version
        with get_db() as db:
            for v in versions:
                count = db.execute("SELECT COUNT(*) FROM api_route_registry WHERE version_id = ?", (v['id'],)).fetchone()[0]
                v['route_count'] = count

        # Get metrics
        yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
        total_requests = get_count("api_request_logs", f"created_at >= '{yesterday}'")
        total_errors = get_count("api_error_logs", f"is_resolved = 0 AND created_at >= '{yesterday}'")
        error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0

        # Get latency percentiles
        p50, p90, p95, p99 = 0, 0, 0, 0
        avg_latency = 0
        try:
            with get_db() as db:
                # Average latency
                avg_row = db.execute("""
                    SELECT AVG(response_time_ms) FROM api_request_logs
                    WHERE created_at >= ? AND response_time_ms IS NOT NULL
                """, (yesterday,)).fetchone()
                avg_latency = round(avg_row[0], 2) if avg_row and avg_row[0] else 0

                # P50
                p50_row = db.execute("""
                    SELECT response_time_ms FROM api_request_logs
                    WHERE created_at >= ? AND response_time_ms IS NOT NULL
                    ORDER BY response_time_ms ASC
                    LIMIT 1 OFFSET (SELECT COUNT(*) / 2 FROM api_request_logs
                                    WHERE created_at >= ? AND response_time_ms IS NOT NULL)
                """, (yesterday, yesterday)).fetchone()
                p50 = p50_row[0] if p50_row else 0

                # P90
                p90_row = db.execute("""
                    SELECT response_time_ms FROM api_request_logs
                    WHERE created_at >= ? AND response_time_ms IS NOT NULL
                    ORDER BY response_time_ms ASC
                    LIMIT 1 OFFSET (SELECT COUNT(*) * 90 / 100 FROM api_request_logs
                                    WHERE created_at >= ? AND response_time_ms IS NOT NULL)
                """, (yesterday, yesterday)).fetchone()
                p90 = p90_row[0] if p90_row else 0

                # P95
                p95_row = db.execute("""
                    SELECT response_time_ms FROM api_request_logs
                    WHERE created_at >= ? AND response_time_ms IS NOT NULL
                    ORDER BY response_time_ms ASC
                    LIMIT 1 OFFSET (SELECT COUNT(*) * 95 / 100 FROM api_request_logs
                                    WHERE created_at >= ? AND response_time_ms IS NOT NULL)
                """, (yesterday, yesterday)).fetchone()
                p95 = p95_row[0] if p95_row else 0

                # P99
                p99_row = db.execute("""
                    SELECT response_time_ms FROM api_request_logs
                    WHERE created_at >= ? AND response_time_ms IS NOT NULL
                    ORDER BY response_time_ms ASC
                    LIMIT 1 OFFSET (SELECT COUNT(*) * 99 / 100 FROM api_request_logs
                                    WHERE created_at >= ? AND response_time_ms IS NOT NULL)
                """, (yesterday, yesterday)).fetchone()
                p99 = p99_row[0] if p99_row else 0
        except:
            pass

        # Calculate uptime (rough estimate based on error rate)
        uptime = 100 - error_rate

        # Components
        components = [
            {'name': 'Database', 'status': db_status, 'latency_ms': 5},
            {'name': 'API Gateway Core', 'status': 'healthy', 'latency_ms': 12},
            {'name': 'Webhook Engine', 'status': 'healthy', 'latency_ms': 8},
            {'name': 'Rate Limiter', 'status': 'healthy', 'latency_ms': 3},
        ]

        context = get_base_context()
        context.update({
            'components': components,
            'versions': versions,
            'total_requests': total_requests,
            'total_errors': total_errors,
            'error_rate': round(error_rate, 2),
            'uptime': round(uptime, 2),
            'avg_latency': avg_latency,
            'p50': round(p50, 2),
            'p90': round(p90, 2),
            'p95': round(p95, 2),
            'p99': round(p99, 2),
            'last_checked': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'page_title': 'Health Status'
        })

        return render_template('api_gateway/monitoring/health.html', **context)

    # =============================================================================
    # SETTINGS
    # =============================================================================

    @app.route('/api-gateway/settings/')
    def api_gateway_settings():
        """API Gateway Settings."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_settings_by_category

        categories = [
            'API_VERSIONING',
            'SECURITY',
            'RATE_LIMITING',
            'WEBHOOKS',
            'LOGGING',
            'AUDIT',
            'IDEMPOTENCY',
            'AUTH',
        ]

        settings_by_category = {}
        for cat in categories:
            settings_by_category[cat] = get_api_settings_by_category(cat)

        context = get_base_context()
        context.update({
            'settings_by_category': settings_by_category,
            'categories': categories,
            'page_title': 'API Gateway Settings'
        })

        return render_template('api_gateway/settings/index.html', **context)

    @app.route('/api-gateway/settings/rate-limits/')
    def api_gateway_settings_rate_limits():
        """Rate Limit Rules settings."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_rate_limit_profiles

        profiles = get_rate_limit_profiles()

        context = get_base_context()
        context.update({
            'profiles': profiles,
            'page_title': 'Rate Limit Rules'
        })

        return render_template('api_gateway/settings/rate_limits.html', **context)

    @app.route('/api-gateway/settings/security/')
    def api_gateway_settings_security():
        """CORS and Security settings."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        context = get_base_context()
        context.update({
            'page_title': 'Security Settings'
        })

        return render_template('api_gateway/settings/security.html', **context)

    # =============================================================================
    # AUDIT LOGS
    # =============================================================================

    @app.route('/api-gateway/audit/')
    @app.route('/api-gateway/audit/access/')
    def api_gateway_audit():
        """API Gateway Audit Logs."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from database import get_all

        # Get recent audit records related to API Gateway
        # This would be integrated with platform_audit_log
        audit_logs = get_all("""
            SELECT * FROM platform_audit_log
            WHERE entity_type IN ('api_client', 'webhook_subscription', 'integration_profile',
                                  'api_scope', 'api_route', 'api_version')
            ORDER BY created_at DESC
            LIMIT 100
        """)

        context = get_base_context()
        context.update({
            'audit_logs': audit_logs,
            'page_title': 'Audit Logs'
        })

        return render_template('api_gateway/audit/index.html', **context)

    # =============================================================================
    # EXPORT FUNCTIONS
    # =============================================================================

    @app.route('/api-gateway/export/logs/csv/')
    def api_gateway_export_logs_csv():
        """Export request logs as CSV."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        export_format = request.args.get('format', 'csv')

        from api_gateway_models import get_api_request_logs

        filters = {
            'client_id': request.args.get('client_id'),
            'method': request.args.get('method'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
        }

        logs = get_api_request_logs(filters=filters, page=1, per_page=10000)

        if export_format == 'json':
            response = jsonify({
                'export_date': datetime.now().isoformat(),
                'total_records': len(logs['logs']),
                'logs': logs['logs']
            })
            response.headers['Content-Disposition'] = f'attachment; filename=api_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            return response

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'Request ID', 'Timestamp', 'Method', 'Path', 'Status',
            'Client', 'User', 'Response Time (ms)', 'IP Address'
        ])

        # Data
        for log in logs['logs']:
            writer.writerow([
                log.get('request_id'),
                log.get('created_at'),
                log.get('method'),
                log.get('path'),
                log.get('response_status_code'),
                log.get('client_code'),
                log.get('user_username'),
                log.get('response_time_ms'),
                log.get('ip_address'),
            ])

        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'api_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

    @app.route('/api-gateway/export/usage/csv/')
    def api_gateway_export_usage_csv():
        """Export usage metrics as CSV."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_usage_metrics

        days = int(request.args.get('days', 30))
        metrics = get_api_usage_metrics(days)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Requests', 'Errors', 'Error Rate (%)', 'Avg Response (ms)'])

        for m in metrics:
            writer.writerow([m['date'], m['requests'], m['errors'], f"{m['error_rate']:.2f}", m['avg_response_ms']])

        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'api_usage_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

    @app.route('/api-gateway/export/usage/json/')
    def api_gateway_export_usage_json():
        """Export usage metrics as JSON."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_usage_metrics

        days = int(request.args.get('days', 30))
        metrics = get_api_usage_metrics(days)

        response = jsonify({
            'export_date': datetime.now().isoformat(),
            'period_days': days,
            'metrics': metrics
        })
        response.headers['Content-Disposition'] = f'attachment; filename=api_usage_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        return response

    @app.route('/api-gateway/export/usage/excel/')
    def api_gateway_export_usage_excel():
        """Export usage metrics as Excel (CSV with formatting for Excel)."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_usage_metrics, get_api_request_logs
        from database import get_all

        days = int(request.args.get('days', 30))
        metrics = get_api_usage_metrics(days)

        # Get top clients
        top_clients = get_all("""
            SELECT ac.client_name, ac.client_code, COUNT(*) as request_count
            FROM api_request_logs arl
            JOIN api_clients ac ON arl.client_id = ac.id
            WHERE arl.created_at >= datetime('now', '-{} days')
            GROUP BY ac.id
            ORDER BY request_count DESC
            LIMIT 10
        """.format(days))

        output = io.StringIO()
        writer = csv.writer(output)

        # Write Usage Report sheet
        writer.writerow(['API Usage Report - Last {} Days'.format(days)])
        writer.writerow(['Generated: {}'.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))])
        writer.writerow([])
        writer.writerow(['Date', 'Requests', 'Errors', 'Error Rate (%)', 'Avg Response (ms)', 'Success Rate (%)'])

        total_requests = 0
        total_errors = 0
        for m in metrics:
            total_requests += m['requests']
            total_errors += m['errors']
            success_rate = ((m['requests'] - m['errors']) / m['requests'] * 100) if m['requests'] > 0 else 100
            writer.writerow([m['date'], m['requests'], m['errors'], f"{m['error_rate']:.2f}", m['avg_response_ms'], f"{success_rate:.2f}"])

        writer.writerow([])
        writer.writerow(['Total', total_requests, total_errors, f"{(total_errors/total_requests*100) if total_requests > 0 else 0:.2f}", '', ''])

        # Write Top Clients sheet
        writer.writerow([])
        writer.writerow(['Top API Clients by Request Count'])
        writer.writerow(['Client Name', 'Client Code', 'Requests', 'Share (%)'])
        for c in top_clients:
            share = (c['request_count'] / total_requests * 100) if total_requests > 0 else 0
            writer.writerow([c['client_name'], c['client_code'], c['request_count'], f"{share:.2f}"])

        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='application/vnd.ms-excel',
            as_attachment=True,
            download_name=f'api_usage_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xls'
        )

    @app.route('/api-gateway/export/webhooks/csv/')
    def api_gateway_export_webhooks_csv():
        """Export webhook deliveries as CSV."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_webhook_deliveries

        filters = {
            'subscription_id': request.args.get('subscription_id'),
            'status': request.args.get('status'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
        }

        deliveries = get_webhook_deliveries(filters=filters, page=1, per_page=10000)

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow([
            'Delivery ID', 'Event', 'Subscription', 'Status', 'HTTP Code',
            'Response Time (ms)', 'Attempt', 'Delivered At'
        ])

        for d in deliveries['deliveries']:
            writer.writerow([
                d.get('delivery_id'),
                d.get('event_code'),
                d.get('subscription_code'),
                d.get('delivery_status'),
                d.get('http_status_code'),
                d.get('response_time_ms'),
                d.get('attempt_number'),
                d.get('delivered_at'),
            ])

        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'webhook_deliveries_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

    # =============================================================================
    # AJAX API FOR FRONTEND
    # =============================================================================

    @app.route('/api-gateway/api/clients/<int:client_id>/toggle-status/', methods=['POST'])
    def api_gateway_toggle_client_status(client_id):
        """Toggle API client status."""
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        from api_gateway_models import get_api_client_by_id, update_api_client

        client = get_api_client_by_id(client_id)
        if not client:
            return jsonify({'error': 'Client not found'}), 404

        new_status = 'inactive' if client['status'] == 'active' else 'active'
        update_api_client(client_id, {'status': new_status})

        return jsonify({'success': True, 'new_status': new_status})

    @app.route('/api-gateway/api/webhooks/<int:sub_id>/toggle/', methods=['POST'])
    def api_gateway_toggle_webhook(sub_id):
        """Toggle webhook subscription status."""
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        from api_gateway_models import get_webhook_subscription_by_id, update_webhook_subscription

        sub = get_webhook_subscription_by_id(sub_id)
        if not sub:
            return jsonify({'error': 'Subscription not found'}), 404

        new_active = 0 if sub['active'] else 1
        update_webhook_subscription(sub_id, {'active': new_active})

        return jsonify({'success': True, 'new_active': new_active})

    @app.route('/api-gateway/api/integrations/<int:profile_id>/toggle/', methods=['POST'])
    def api_gateway_toggle_integration(profile_id):
        """Toggle integration profile status."""
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        from api_gateway_models import get_integration_profile_by_id, update_integration_profile

        profile = get_integration_profile_by_id(profile_id)
        if not profile:
            return jsonify({'error': 'Profile not found'}), 404

        new_active = 0 if profile['is_active'] else 1
        update_integration_profile(profile_id, {'is_active': new_active})

        return jsonify({'success': True, 'new_active': new_active})

    # =============================================================================
    # EXPORT ROUTES
    # =============================================================================

    @app.route('/api-gateway/export/clients/csv/')
    def api_gateway_export_clients_csv():
        """Export API clients as CSV."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_clients

        clients = get_api_clients(page=1, per_page=10000)

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Client Code', 'Client Name', 'Type', 'Owner', 'Email', 'Department', 'Status', 'Rate Limit', 'Created'])

        for c in clients['clients']:
            writer.writerow([
                c.get('client_code'),
                c.get('client_name'),
                c.get('client_type'),
                c.get('owner_name'),
                c.get('owner_email'),
                c.get('department'),
                c.get('status'),
                c.get('rate_limit_profile'),
                c.get('created_at'),
            ])

        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'api_clients_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )

    @app.route('/api-gateway/export/clients/json/')
    def api_gateway_export_clients_json():
        """Export API clients as JSON."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_api_clients

        clients = get_api_clients(page=1, per_page=10000)

        response = jsonify({
            'export_date': datetime.now().isoformat(),
            'total_records': len(clients['clients']),
            'clients': clients['clients']
        })
        response.headers['Content-Disposition'] = f'attachment; filename=api_clients_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        return response

    @app.route('/api-gateway/export/webhooks/json/')
    def api_gateway_export_webhooks_json():
        """Export webhook subscriptions as JSON."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from api_gateway_models import get_webhook_subscriptions

        subscriptions = get_webhook_subscriptions(page=1, per_page=10000)

        response = jsonify({
            'export_date': datetime.now().isoformat(),
            'total_records': len(subscriptions['subscriptions']),
            'subscriptions': subscriptions['subscriptions']
        })
        response.headers['Content-Disposition'] = f'attachment; filename=webhooks_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        return response
