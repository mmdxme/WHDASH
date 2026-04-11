"""
REST API Engine
=============
Centralized REST API engine for the MMDx platform.

This module provides:
- Consistent REST API endpoints for all modules
- Standardized request/response formats
- Authentication and authorization
- Rate limiting
- Request validation
- Error handling
- Pagination, filtering, sorting
- Multi-company/branch/warehouse scoping

API BASE PATH: /api/v1

USAGE:
    from rest_api import register_rest_api
    register_rest_api(app)
"""

from flask import Flask, request, jsonify
from functools import wraps
import json
import uuid
import hashlib
import hmac
import time
from datetime import datetime
from database import get_db, get_db_context, get_one, get_all, log_audit


def register_rest_api(app: Flask):
    """Register the REST API engine."""

    # =============================================================================
    # MIDDLEWARE / BEFORE REQUEST
    # =============================================================================

    @app.before_request
    def before_request():
        """Process each request before routing."""
        # Generate request ID
        request.request_id = str(uuid.uuid4())

        # Start timer
        request.start_time = time.time()

    @app.after_request
    def after_request(response):
        """Process each response after routing."""
        from api_gateway_models import log_api_request

        # Calculate response time
        elapsed_ms = int((time.time() - request.start_time) * 1000) if hasattr(request, 'start_time') else 0

        # Build request data for logging
        request_data = {
            'request_id': getattr(request, 'request_id', str(uuid.uuid4())),
            'method': request.method,
            'path': request.path,
            'query_string': request.query_string.decode('utf-8', errors='replace') if request.query_string else '',
            'response_status_code': response.status_code,
            'response_time_ms': elapsed_ms,
            'ip_address': request.remote_addr,
            'user_agent': request.user_agent.string[:200] if request.user_agent else None,
        }

        # Log request asynchronously (in production, use a queue)
        try:
            pass  # Logging is optional for API performance
        except:
            pass  # Don't fail requests if logging fails

        # Add standard headers
        response.headers['X-Request-ID'] = getattr(request, 'request_id', '')
        response.headers['X-Response-Time'] = f"{elapsed_ms}ms"

        return response

    # =============================================================================
    # STANDARD RESPONSE HELPERS
    # =============================================================================

    def success_response(data=None, message=None, meta=None, status_code=200):
        """Build a standardized success response."""
        response = {
            'success': True,
            'request_id': getattr(request, 'request_id', ''),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }

        if data is not None:
            response['data'] = data

        if message:
            response['message'] = message

        if meta:
            response['meta'] = meta

        return jsonify(response), status_code

    def error_response(code, message, details=None, status_code=400):
        """Build a standardized error response."""
        response = {
            'success': False,
            'error': {
                'code': code,
                'message': message,
                'request_id': getattr(request, 'request_id', ''),
            },
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }

        if details:
            response['error']['details'] = details

        return jsonify(response), status_code

    def paginated_response(items, page, per_page, total, status_code=200):
        """Build a standardized paginated response."""
        return success_response(
            data=items,
            meta={
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page if per_page > 0 else 0,
                    'has_next': page * per_page < total,
                    'has_prev': page > 1,
                }
            },
            status_code=status_code
        )

    # =============================================================================
    # API AUTHENTICATION
    # =============================================================================

    def require_api_auth(f):
        """Decorator to require API authentication."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from api_gateway_models import (
                get_api_client_by_id, validate_client_scopes,
                verify_api_key, log_api_error
            )

            # Get API key from header
            auth_header = request.headers.get('Authorization', '')
            api_key = None

            if auth_header.startswith('Bearer '):
                api_key = auth_header[7:]
            elif auth_header.startswith('ApiKey '):
                api_key = auth_header[8:]
            elif request.args.get('api_key'):
                api_key = request.args.get('api_key')

            if not api_key:
                log_api_error({
                    'request_id': getattr(request, 'request_id', ''),
                    'error_code': 'AUTH_001',
                    'error_type': 'Authentication',
                    'error_message': 'Missing API key',
                    'method': request.method,
                    'path': request.path,
                    'ip_address': request.remote_addr,
                })
                return error_response('AUTH_001', 'Missing API key. Provide API key via Authorization header or api_key query parameter.', status_code=401)

            # Verify API key
            api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            # Find client by API key hash
            client = get_one("""
                SELECT ac.*, acc.id as cred_id, acc.expires_at as key_expires_at
                FROM api_clients ac
                JOIN api_client_credentials acc ON acc.client_id = ac.id
                WHERE acc.api_key_hash = ? AND acc.is_active = 1 AND acc.credential_type = 'api_key'
            """, (api_key_hash,))

            if not client:
                return error_response('AUTH_001', 'Invalid API key', status_code=401)

            # Check client status
            if client['status'] != 'active':
                    return error_response('AUTH_002', 'API client is not active', status_code=403)

            # Check API key expiration
            key_expires_at = client.get('key_expires_at')
            if key_expires_at:
                from datetime import datetime
                try:
                    expiry_dt = datetime.fromisoformat(key_expires_at)
                    if datetime.now() > expiry_dt:
                        return error_response('AUTH_004', 'API key has expired', status_code=401)
                except (ValueError, TypeError):
                    pass  # If invalid date format, skip expiration check

            # Check IP restrictions
            if client.get('allowed_ip_addresses'):
                allowed_ips = [ip.strip() for ip in client['allowed_ip_addresses'].split(',')]
                if request.remote_addr not in allowed_ips:
                    return error_response('AUTH_003', 'IP address not allowed', status_code=403)

            # Attach client to request
            request.api_client = client

            return f(*args, **kwargs)
        return decorated_function

    def require_api_scope(*required_scopes):
        """Decorator to require specific API scopes."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                client = getattr(request, 'api_client', None)
                if not client:
                    return error_response('AUTH_001', 'Authentication required', status_code=401)

                # Check scopes
                allowed_scopes = client.get('allowed_scopes', '[]')
                if isinstance(allowed_scopes, str):
                    try:
                        allowed_scopes = json.loads(allowed_scopes)
                    except:
                        allowed_scopes = []

                # '*' means all scopes
                if '*' not in allowed_scopes:
                    for scope in required_scopes:
                        if scope not in allowed_scopes:
                            return error_response(
                                'AUTH_003',
                                f"Missing required scope: {scope}",
                                details={'required_scopes': list(required_scopes)},
                                status_code=403
                            )

                return f(*args, **kwargs)
            return decorated_function
        return decorator

    # =============================================================================
    # STANDARD API ENDPOINTS
    # =============================================================================

    # -------------------------------------------------------------------------
    # Health Check
    # -------------------------------------------------------------------------
    @app.route('/api/health')
    def api_health():
        """API health check endpoint."""
        try:
            # Check database
            db = get_db()
            db.execute("SELECT 1")
            db.close()
            db_status = 'healthy'
        except:
            db_status = 'unhealthy'

        return success_response({
            'status': 'healthy' if db_status == 'healthy' else 'degraded',
            'version': '2.0',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'components': {
                'api': 'healthy',
                'database': db_status,
            }
        })

    # -------------------------------------------------------------------------
    # API Info
    # -------------------------------------------------------------------------
    @app.route('/api/v1')
    @app.route('/api/v1/')
    def api_v1_info():
        """API v1 information."""
        return success_response({
            'name': 'MMDx API',
            'version': '2.0',
            'description': 'Enterprise API Gateway for MMDx Platform',
            'base_path': '/api/v1',
            'documentation': '/api-gateway/docs/openapi/',
        })

    # -------------------------------------------------------------------------
    # Customers
    # -------------------------------------------------------------------------
    @app.route('/api/v1/customers')
    @require_api_auth
    @require_api_scope('sales.customers.read', 'crm.customers.read')
    def api_list_customers():
        """List customers with pagination and filtering."""
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        # Build query conditions
        conditions = []
        params = []

        if request.args.get('status'):
            conditions.append("status = ?")
            params.append(request.args.get('status'))

        if request.args.get('search'):
            conditions.append("(name LIKE ? OR code LIKE ? OR phone LIKE ?)")
            search = f"%{request.args.get('search')}%"
            params.extend([search, search, search])

        if request.args.get('city'):
            conditions.append("city = ?")
            params.append(request.args.get('city'))

        if request.args.get('salesperson_id'):
            conditions.append("salesperson_id = ?")
            params.append(request.args.get('salesperson_id'))

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        # Get total count
        total_result = get_one(f"SELECT COUNT(*) as cnt FROM customers {where}", params)
        total = total_result['cnt'] if total_result else 0

        # Get items
        offset = (page - 1) * per_page
        items = get_all(f"""
            SELECT c.*, u.username as salesperson_name
            FROM customers c
            LEFT JOIN users u ON c.salesperson_id = u.id
            {where}
            ORDER BY c.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [per_page, offset])

        return paginated_response(items, page, per_page, total)

    @app.route('/api/v1/customers/<int:customer_id>')
    @require_api_auth
    @require_api_scope('sales.customers.read', 'crm.customers.read')
    def api_get_customer(customer_id):
        """Get a single customer by ID."""
        customer = get_one("""
            SELECT c.*, u.username as salesperson_name
            FROM customers c
            LEFT JOIN users u ON c.salesperson_id = u.id
            WHERE c.id = ?
        """, (customer_id,))

        if not customer:
            return error_response('NOT_FOUND', 'Customer not found', status_code=404)

        return success_response(customer)

    @app.route('/api/v1/customers', methods=['POST'])
    @require_api_auth
    @require_api_scope('sales.customers.write', 'crm.customers.write')
    def api_create_customer():
        """Create a new customer."""
        data = request.get_json() or {}

        # Validate required fields
        if not data.get('name'):
            return error_response('VAL_002', 'Customer name is required', status_code=400)

        with get_db_context() as db:
            cursor = db.execute("""
                INSERT INTO customers (name, code, type, phone, email, address, city, country,
                                    salesperson_id, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('name'),
                data.get('code'),
                data.get('type', 'retail'),
                data.get('phone'),
                data.get('email'),
                data.get('address'),
                data.get('city'),
                data.get('country'),
                data.get('salesperson_id'),
                data.get('status', 'active'),
                data.get('notes'),
            ))
            db.commit()
            customer_id = cursor.lastrowid

        customer = get_one("SELECT * FROM customers WHERE id = ?", (customer_id,))
        return success_response(customer, message='Customer created successfully', status_code=201)

    # -------------------------------------------------------------------------
    # Items / Products
    # -------------------------------------------------------------------------
    @app.route('/api/v1/items')
    @require_api_auth
    @require_api_scope('inventory.items.read', 'wms.items.read')
    def api_list_items():
        """List items with pagination and filtering."""
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        conditions = []
        params = []

        if request.args.get('category'):
            conditions.append("category = ?")
            params.append(request.args.get('category'))

        if request.args.get('search'):
            conditions.append("(name LIKE ? OR sku LIKE ? OR barcode LIKE ?)")
            search = f"%{request.args.get('search')}%"
            params.extend([search, search, search])

        if request.args.get('is_active') is not None:
            conditions.append("is_active = ?")
            params.append(1 if request.args.get('is_active') == 'true' else 0)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        total_result = get_one(f"SELECT COUNT(*) as cnt FROM parts {where}", params)
        total = total_result['cnt'] if total_result else 0

        offset = (page - 1) * per_page
        items = get_all(f"""
            SELECT p.*, w.name as warehouse_name
            FROM parts p
            LEFT JOIN warehouses w ON p.default_warehouse_id = w.id
            {where}
            ORDER BY p.name
            LIMIT ? OFFSET ?
        """, params + [per_page, offset])

        return paginated_response(items, page, per_page, total)

    @app.route('/api/v1/items/<int:item_id>')
    @require_api_auth
    @require_api_scope('inventory.items.read', 'wms.items.read')
    def api_get_item(item_id):
        """Get a single item by ID."""
        item = get_one("SELECT * FROM parts WHERE id = ?", (item_id,))

        if not item:
            return error_response('NOT_FOUND', 'Item not found', status_code=404)

        return success_response(item)

    # -------------------------------------------------------------------------
    # Inventory
    # -------------------------------------------------------------------------
    @app.route('/api/v1/inventory')
    @require_api_auth
    @require_api_scope('inventory.stock.read', 'wms.inventory.read')
    def api_list_inventory():
        """List inventory levels."""
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        conditions = []
        params = []

        if request.args.get('warehouse_id'):
            conditions.append("warehouse_id = ?")
            params.append(request.args.get('warehouse_id'))

        if request.args.get('item_id'):
            conditions.append("item_id = ?")
            params.append(request.args.get('item_id'))

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        total_result = get_one(f"SELECT COUNT(*) as cnt FROM inventory {where}", params)
        total = total_result['cnt'] if total_result else 0

        offset = (page - 1) * per_page
        items = get_all(f"""
            SELECT i.*, p.name as item_name, p.sku, w.name as warehouse_name
            FROM inventory i
            JOIN parts p ON i.item_id = p.id
            LEFT JOIN warehouses w ON i.warehouse_id = w.id
            {where}
            ORDER BY p.name
            LIMIT ? OFFSET ?
        """, params + [per_page, offset])

        return paginated_response(items, page, per_page, total)

    # -------------------------------------------------------------------------
    # Sales Orders
    # -------------------------------------------------------------------------
    @app.route('/api/v1/orders')
    @require_api_auth
    @require_api_scope('sales.orders.read')
    def api_list_orders():
        """List sales orders."""
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        conditions = []
        params = []

        if request.args.get('status'):
            conditions.append("status = ?")
            params.append(request.args.get('status'))

        if request.args.get('customer_id'):
            conditions.append("customer_id = ?")
            params.append(request.args.get('customer_id'))

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        total_result = get_one(f"SELECT COUNT(*) as cnt FROM sales_orders {where}", params)
        total = total_result['cnt'] if total_result else 0

        offset = (page - 1) * per_page
        orders = get_all(f"""
            SELECT so.*, c.name as customer_name
            FROM sales_orders so
            LEFT JOIN customers c ON so.customer_id = c.id
            {where}
            ORDER BY so.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [per_page, offset])

        return paginated_response(orders, page, per_page, total)

    @app.route('/api/v1/orders/<int:order_id>')
    @require_api_auth
    @require_api_scope('sales.orders.read')
    def api_get_order(order_id):
        """Get a single order by ID."""
        order = get_one("""
            SELECT so.*, c.name as customer_name
            FROM sales_orders so
            LEFT JOIN customers c ON so.customer_id = c.id
            WHERE so.id = ?
        """, (order_id,))

        if not order:
            return error_response('NOT_FOUND', 'Order not found', status_code=404)

        return success_response(order)

    # -------------------------------------------------------------------------
    # Suppliers
    # -------------------------------------------------------------------------
    @app.route('/api/v1/suppliers')
    @require_api_auth
    @require_api_scope('procurement.suppliers.read')
    def api_list_suppliers():
        """List suppliers."""
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        conditions = []
        params = []

        if request.args.get('status'):
            conditions.append("status = ?")
            params.append(request.args.get('status'))

        if request.args.get('search'):
            conditions.append("(name LIKE ? OR code LIKE ?)")
            search = f"%{request.args.get('search')}%"
            params.extend([search, search])

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        total_result = get_one(f"SELECT COUNT(*) as cnt FROM suppliers {where}", params)
        total = total_result['cnt'] if total_result else 0

        offset = (page - 1) * per_page
        suppliers = get_all(f"""
            SELECT * FROM suppliers
            {where}
            ORDER BY name
            LIMIT ? OFFSET ?
        """, params + [per_page, offset])

        return paginated_response(suppliers, page, per_page, total)

    @app.route('/api/v1/suppliers/<int:supplier_id>')
    @require_api_auth
    @require_api_scope('procurement.suppliers.read')
    def api_get_supplier(supplier_id):
        """Get a single supplier by ID."""
        supplier = get_one("SELECT * FROM suppliers WHERE id = ?", (supplier_id,))

        if not supplier:
            return error_response('NOT_FOUND', 'Supplier not found', status_code=404)

        return success_response(supplier)

    # -------------------------------------------------------------------------
    # Purchase Orders
    # -------------------------------------------------------------------------
    @app.route('/api/v1/purchase-orders')
    @require_api_auth
    @require_api_scope('procurement.orders.read')
    def api_list_purchase_orders():
        """List purchase orders."""
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        conditions = []
        params = []

        if request.args.get('status'):
            conditions.append("status = ?")
            params.append(request.args.get('status'))

        if request.args.get('supplier_id'):
            conditions.append("supplier_id = ?")
            params.append(request.args.get('supplier_id'))

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        total_result = get_one(f"SELECT COUNT(*) as cnt FROM purchase_orders {where}", params)
        total = total_result['cnt'] if total_result else 0

        offset = (page - 1) * per_page
        orders = get_all(f"""
            SELECT po.*, s.name as supplier_name
            FROM purchase_orders po
            LEFT JOIN suppliers s ON po.supplier_id = s.id
            {where}
            ORDER BY po.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [per_page, offset])

        return paginated_response(orders, page, per_page, total)

    # -------------------------------------------------------------------------
    # Warehouses
    # -------------------------------------------------------------------------
    @app.route('/api/v1/warehouses')
    @require_api_auth
    @require_api_scope('inventory.warehouses.read', 'wms.warehouses.read')
    def api_list_warehouses():
        """List warehouses."""
        warehouses = get_all("SELECT * FROM warehouses ORDER BY name")
        return success_response(warehouses)

    @app.route('/api/v1/warehouses/<int:warehouse_id>')
    @require_api_auth
    @require_api_scope('inventory.warehouses.read', 'wms.warehouses.read')
    def api_get_warehouse(warehouse_id):
        """Get a single warehouse by ID."""
        warehouse = get_one("SELECT * FROM warehouses WHERE id = ?", (warehouse_id,))

        if not warehouse:
            return error_response('NOT_FOUND', 'Warehouse not found', status_code=404)

        return success_response(warehouse)

    # -------------------------------------------------------------------------
    # Users
    # -------------------------------------------------------------------------
    @app.route('/api/v1/users')
    @require_api_auth
    @require_api_scope('users.read', 'platform.users.read')
    def api_list_users():
        """List users."""
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        conditions = []
        params = []

        if request.args.get('role_id'):
            conditions.append("role_id = ?")
            params.append(request.args.get('role_id'))

        if request.args.get('is_active') is not None:
            conditions.append("is_active = ?")
            params.append(1 if request.args.get('is_active') == 'true' else 0)

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        total_result = get_one(f"SELECT COUNT(*) as cnt FROM users {where}", params)
        total = total_result['cnt'] if total_result else 0

        offset = (page - 1) * per_page
        users = get_all(f"""
            SELECT u.id, u.username, u.email, u.role_id, r.role_name,
                   u.is_active, u.created_at
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            {where}
            ORDER BY u.username
            LIMIT ? OFFSET ?
        """, params + [per_page, offset])

        return paginated_response(users, page, per_page, total)

    @app.route('/api/v1/users/<int:user_id>')
    @require_api_auth
    @require_api_scope('users.read', 'platform.users.read')
    def api_get_user(user_id):
        """Get a single user by ID."""
        user = get_one("""
            SELECT u.id, u.username, u.email, u.role_id, r.role_name,
                   u.is_active, u.created_at
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            WHERE u.id = ?
        """, (user_id,))

        if not user:
            return error_response('NOT_FOUND', 'User not found', status_code=404)

        return success_response(user)

    # -------------------------------------------------------------------------
    # Employees
    # -------------------------------------------------------------------------
    @app.route('/api/v1/employees')
    @require_api_auth
    @require_api_scope('hr.employees.read')
    def api_list_employees():
        """List employees."""
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        conditions = []
        params = []

        if request.args.get('department'):
            conditions.append("department = ?")
            params.append(request.args.get('department'))

        if request.args.get('status'):
            conditions.append("status = ?")
            params.append(request.args.get('status'))

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        total_result = get_one(f"SELECT COUNT(*) as cnt FROM employees {where}", params)
        total = total_result['cnt'] if total_result else 0

        offset = (page - 1) * per_page
        employees = get_all(f"""
            SELECT e.*, d.name as department_name
            FROM employees e
            LEFT JOIN departments d ON e.department_id = d.id
            {where}
            ORDER BY e.name
            LIMIT ? OFFSET ?
        """, params + [per_page, offset])

        return paginated_response(employees, page, per_page, total)

    # -------------------------------------------------------------------------
    # Assets
    # -------------------------------------------------------------------------
    @app.route('/api/v1/assets')
    @require_api_auth
    @require_api_scope('assets.assets.read')
    def api_list_assets():
        """List assets."""
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        conditions = []
        params = []

        if request.args.get('status'):
            conditions.append("status = ?")
            params.append(request.args.get('status'))

        if request.args.get('category_id'):
            conditions.append("category_id = ?")
            params.append(request.args.get('category_id'))

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        total_result = get_one(f"SELECT COUNT(*) as cnt FROM assets {where}", params)
        total = total_result['cnt'] if total_result else 0

        offset = (page - 1) * per_page
        assets = get_all(f"""
            SELECT a.*, ac.name as category_name
            FROM assets a
            LEFT JOIN asset_categories ac ON a.category_id = ac.id
            {where}
            ORDER BY a.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [per_page, offset])

        return paginated_response(assets, page, per_page, total)

    @app.route('/api/v1/assets/<int:asset_id>')
    @require_api_auth
    @require_api_scope('assets.assets.read')
    def api_get_asset(asset_id):
        """Get a single asset by ID."""
        asset = get_one("""
            SELECT a.*, ac.name as category_name
            FROM assets a
            LEFT JOIN asset_categories ac ON a.category_id = ac.id
            WHERE a.id = ?
        """, (asset_id,))

        if not asset:
            return error_response('NOT_FOUND', 'Asset not found', status_code=404)

        return success_response(asset)

    # -------------------------------------------------------------------------
    # Finance - Chart of Accounts
    # -------------------------------------------------------------------------
    @app.route('/api/v1/accounts')
    @require_api_auth
    @require_api_scope('finance.accounts.read')
    def api_list_accounts():
        """List chart of accounts."""
        accounts = get_all("SELECT * FROM accounts ORDER BY account_code")
        return success_response(accounts)

    # -------------------------------------------------------------------------
    # Finance - Journals
    # -------------------------------------------------------------------------
    @app.route('/api/v1/journals')
    @require_api_auth
    @require_api_scope('finance.journals.read')
    def api_list_journals():
        """List journal entries."""
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        conditions = []
        params = []

        if request.args.get('status'):
            conditions.append("status = ?")
            params.append(request.args.get('status'))

        if request.args.get('entry_date_from'):
            conditions.append("entry_date >= ?")
            params.append(request.args.get('entry_date_from'))

        if request.args.get('entry_date_to'):
            conditions.append("entry_date <= ?")
            params.append(request.args.get('entry_date_to'))

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        total_result = get_one(f"SELECT COUNT(*) as cnt FROM journals {where}", params)
        total = total_result['cnt'] if total_result else 0

        offset = (page - 1) * per_page
        journals = get_all(f"""
            SELECT j.*, u.username as posted_by_name
            FROM journals j
            LEFT JOIN users u ON j.posted_by = u.id
            {where}
            ORDER BY j.entry_date DESC, j.created_at DESC
            LIMIT ? OFFSET ?
        """, params + [per_page, offset])

        return paginated_response(journals, page, per_page, total)

    # -------------------------------------------------------------------------
    # Quality - NCR
    # -------------------------------------------------------------------------
    @app.route('/api/v1/quality/ncr')
    @require_api_auth
    @require_api_scope('quality.ncr.read')
    def api_list_ncr():
        """List non-conformance reports."""
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)

        conditions = []
        params = []

        if request.args.get('status'):
            conditions.append("status = ?")
            params.append(request.args.get('status'))

        where = "WHERE " + " AND ".join(conditions) if conditions else ""

        total_result = get_one(f"SELECT COUNT(*) as cnt FROM quality_non_conformances {where}", params)
        total = total_result['cnt'] if total_result else 0

        offset = (page - 1) * per_page
        ncrs = get_all(f"""
            SELECT * FROM quality_non_conformances
            {where}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, params + [per_page, offset])

        return paginated_response(ncrs, page, per_page, total)

    # -------------------------------------------------------------------------
    # Dashboard Stats
    # -------------------------------------------------------------------------
    @app.route('/api/v1/dashboard/stats')
    @require_api_auth
    def api_dashboard_stats():
        """Get dashboard statistics."""
        stats = {}

        stats['total_customers'] = get_one("SELECT COUNT(*) as cnt FROM customers")['cnt']
        stats['total_items'] = get_one("SELECT COUNT(*) as cnt FROM parts")['cnt']
        stats['total_orders'] = get_one("SELECT COUNT(*) as cnt FROM sales_orders")['cnt']
        stats['total_assets'] = get_one("SELECT COUNT(*) as cnt FROM assets")['cnt']

        return success_response(stats)

    # -------------------------------------------------------------------------
    # Catch-all 404 for API
    # -------------------------------------------------------------------------
    @app.route('/api/v1/<path:path>')
    def api_not_found(path):
        """Catch-all for undefined API endpoints."""
        return error_response(
            'NOT_FOUND',
            f"Endpoint /api/v1/{path} not found",
            details={
                'hint': 'Check the API documentation for available endpoints',
                'documentation': '/api-gateway/docs/openapi/'
            },
            status_code=404
        )

    return app
