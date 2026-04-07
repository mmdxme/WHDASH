"""
Sales Management Route Handlers
==============================
Flask route handlers for all Sales Management modules.

Route Structure:
- /sales/ - Sales Dashboard
- /sales/customers/ - Customers & Accounts
- /sales/inquiries/ - Leads & Inquiries
- /sales/opportunities/ - Sales Opportunities
- /sales/pricing/ - Pricing & Sales Conditions
- /sales/quotations/ - Quotations / Proforma / Offers
- /sales/orders/ - Sales Orders
- /sales/reservations/ - Reservations & Stock Allocation
- /sales/deliveries/ - Delivery & Dispatch Coordination
- /sales/local-sales/ - Local Sales
- /sales/export-sales/ - Export Sales
- /sales/returns/ - Returns & Complaints
- /sales/targets/ - Targets, Commissions & Performance
- /sales/contracts/ - Contracts & Sales Documents
- /sales/activities/ - Sales Activities & CRM
- /sales/reports/ - Reports & Analytics
- /sales/settings/ - Settings

Usage:
    from sales_routes import register_sales_routes
    register_sales_routes(app, require_login)
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from datetime import datetime
import json


def register_sales_routes(app: Flask, require_login, require_permission, get_db):
    """Register all sales management routes."""

    # =============================================================================
    # HELPER DECORATORS
    # =============================================================================

    def sales_permission(module, resource, action):
        """Sales-specific permission decorator."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                user_id = session.get('user_id')
                if not user_id:
                    flash("Please login to access this page.", "error")
                    return redirect(url_for('login'))

                if not require_permission(user_id, module, resource, action):
                    flash(f"Access Denied. You don't have permission to {action} {resource}.", "error")
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

    # =============================================================================
    # SALES DASHBOARD
    # =============================================================================

    @app.route('/sales/')
    @app.route('/sales/dashboard/')
    def sales_dashboard():
        """Main sales dashboard."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_sales_dashboard_stats, get_salesperson_performance

        user = get_current_user()
        user_id = user['id']

        # Get date filters
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        # Get dashboard stats
        stats = get_sales_dashboard_stats(salesperson_id=None, date_from=date_from, date_to=date_to)

        # Get personal performance if user is salesperson
        performance = get_salesperson_performance(user_id, 'monthly') if 'Sales' in (user.get('role_name') or '') else None

        # Get user permissions for UI
        user_permissions = session.get('permissions', [])

        return render_template('sales/dashboard.html',
                             stats=stats,
                             performance=performance,
                             user=user,
                             date_from=date_from,
                             date_to=date_to)

    # =============================================================================
    # CUSTOMERS & ACCOUNTS
    # =============================================================================

    @app.route('/sales/customers/')
    def sales_customers():
        """Customer list page."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_sales_customers, get_sales_customers

        # Get filters
        filters = {
            'search': request.args.get('search'),
            'customer_type': request.args.get('customer_type'),
            'market': request.args.get('market'),
            'country': request.args.get('country'),
            'city': request.args.get('city'),
            'salesperson_id': request.args.get('salesperson_id'),
            'status': request.args.get('status'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        result = get_sales_customers(filters=filters, page=page, per_page=per_page)

        # Get lookup data
        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()
            countries = db.execute("SELECT DISTINCT country FROM sales_customers WHERE country IS NOT NULL ORDER BY country").fetchall()

        return render_template('sales/customers/list.html',
                             customers=result['customers'],
                             total=result['total'],
                             page=result['page'],
                             pages=result['pages'],
                             filters=filters,
                             salespersons=[dict(s) for s in salespersons],
                             countries=[dict(c) for c in countries])

    @app.route('/sales/customers/new/', methods=['GET', 'POST'])
    def sales_customers_new():
        """Create new customer."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        if request.method == 'POST':
            from sales_models import create_sales_customer
            from database import log_audit

            data = {
                'customer_code': request.form.get('customer_code'),
                'name': request.form.get('name'),
                'trade_name': request.form.get('trade_name'),
                'customer_type': request.form.get('customer_type'),
                'market': request.form.get('market'),
                'country': request.form.get('country'),
                'city': request.form.get('city'),
                'address': request.form.get('address'),
                'phone': request.form.get('phone'),
                'whatsapp': request.form.get('whatsapp'),
                'email': request.form.get('email'),
                'website': request.form.get('website'),
                'buyer_name': request.form.get('buyer_name'),
                'buyer_phone': request.form.get('buyer_phone'),
                'buyer_email': request.form.get('buyer_email'),
                'trade_type': request.form.get('trade_type'),
                'assigned_salesperson_id': request.form.get('assigned_salesperson_id'),
                'payment_terms': request.form.get('payment_terms'),
                'credit_limit': float(request.form.get('credit_limit', 0)),
                'currency': request.form.get('currency', 'AED'),
                'default_discount': float(request.form.get('default_discount', 0)),
                'price_list_id': request.form.get('price_list_id'),
                'status': request.form.get('status', 'Active'),
                'priority': request.form.get('priority', 'Medium'),
                'notes': request.form.get('notes'),
                'company_id': session.get('company_id')
            }

            customer_id = create_sales_customer(data)
            log_audit('sales_customer', customer_id, 'CREATE', session.get('user_id'),
                     notes=f"Created customer: {data['name']}")

            flash("Customer created successfully!", "success")
            return redirect(url_for('sales_customers_view', customer_id=customer_id))

        # Get lookup data
        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()
            price_lists = db.execute("SELECT * FROM sales_price_lists WHERE is_active = 1").fetchall()
            countries = db.execute("SELECT * FROM countries ORDER BY name").fetchall()

        return render_template('sales/customers/form.html',
                             customer=None,
                             salespersons=[dict(s) for s in salespersons],
                             price_lists=[dict(p) for p in price_lists],
                             countries=[dict(c) for c in countries],
                             form_action='create')

    @app.route('/sales/customers/<int:customer_id>/')
    def sales_customers_view(customer_id):
        """View customer details."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_customer_by_id, get_customer_balance, get_sales_orders, get_sales_quotations, get_sales_activities

        customer = get_customer_by_id(customer_id)
        if not customer:
            flash("Customer not found.", "error")
            return redirect(url_for('sales_customers'))

        balance = get_customer_balance(customer_id)

        # Get recent orders
        orders = get_sales_orders({'customer_id': customer_id}, page=1, per_page=5)

        # Get recent quotations
        quotations = get_sales_quotations({'customer_id': customer_id}, page=1, per_page=5)

        # Get recent activities
        activities = get_sales_activities({'customer_id': customer_id}, page=1, per_page=10)

        return render_template('sales/customers/view.html',
                             customer=customer,
                             balance=balance,
                             recent_orders=orders['orders'],
                             recent_quotations=quotations['quotations'],
                             recent_activities=activities['activities'])

    @app.route('/sales/customers/<int:customer_id>/edit/', methods=['GET', 'POST'])
    def sales_customers_edit(customer_id):
        """Edit customer."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_customer_by_id, update_sales_customer
        from database import log_audit

        customer = get_customer_by_id(customer_id)
        if not customer:
            flash("Customer not found.", "error")
            return redirect(url_for('sales_customers'))

        if request.method == 'POST':
            data = {
                'name': request.form.get('name'),
                'trade_name': request.form.get('trade_name'),
                'customer_type': request.form.get('customer_type'),
                'market': request.form.get('market'),
                'country': request.form.get('country'),
                'city': request.form.get('city'),
                'address': request.form.get('address'),
                'phone': request.form.get('phone'),
                'whatsapp': request.form.get('whatsapp'),
                'email': request.form.get('email'),
                'website': request.form.get('website'),
                'buyer_name': request.form.get('buyer_name'),
                'buyer_phone': request.form.get('buyer_phone'),
                'buyer_email': request.form.get('buyer_email'),
                'trade_type': request.form.get('trade_type'),
                'assigned_salesperson_id': request.form.get('assigned_salesperson_id'),
                'payment_terms': request.form.get('payment_terms'),
                'credit_limit': float(request.form.get('credit_limit', 0)),
                'currency': request.form.get('currency', 'AED'),
                'default_discount': float(request.form.get('default_discount', 0)),
                'price_list_id': request.form.get('price_list_id'),
                'status': request.form.get('status', 'Active'),
                'priority': request.form.get('priority', 'Medium'),
                'notes': request.form.get('notes'),
            }

            update_sales_customer(customer_id, data)
            log_audit('sales_customer', customer_id, 'UPDATE', session.get('user_id'),
                     notes=f"Updated customer: {data['name']}")

            flash("Customer updated successfully!", "success")
            return redirect(url_for('sales_customers_view', customer_id=customer_id))

        # Get lookup data
        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()
            price_lists = db.execute("SELECT * FROM sales_price_lists WHERE is_active = 1").fetchall()
            countries = db.execute("SELECT * FROM countries ORDER BY name").fetchall()

        return render_template('sales/customers/form.html',
                             customer=customer,
                             salespersons=[dict(s) for s in salespersons],
                             price_lists=[dict(p) for p in price_lists],
                             countries=[dict(c) for c in countries],
                             form_action='edit')

    # =============================================================================
    # INQUIRIES
    # =============================================================================

    @app.route('/sales/inquiries/')
    def sales_inquiries():
        """Inquiries list page."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_inquiries, get_inquiry_sources, get_inquiry_statuses

        filters = {
            'search': request.args.get('search'),
            'status': request.args.get('status'),
            'source': request.args.get('source'),
            'priority': request.args.get('priority'),
            'salesperson_id': request.args.get('salesperson_id'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
            'market': request.args.get('market'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        result = get_inquiries(filters=filters, page=page, per_page=per_page)

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()

        return render_template('sales/inquiries/list.html',
                             inquiries=result['inquiries'],
                             total=result['total'],
                             page=result['page'],
                             pages=result['pages'],
                             filters=filters,
                             salespersons=[dict(s) for s in salespersons],
                             sources=get_inquiry_sources(),
                             statuses=get_inquiry_statuses())

    @app.route('/sales/inquiries/new/', methods=['GET', 'POST'])
    def sales_inquiries_new():
        """Create new inquiry."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import create_inquiry, add_inquiry_line, get_inquiry_sources, get_inquiry_statuses

        if request.method == 'POST':
            data = {
                'customer_id': request.form.get('customer_id') or None,
                'customer_name': request.form.get('customer_name'),
                'customer_type': request.form.get('customer_type'),
                'market': request.form.get('market'),
                'country': request.form.get('country'),
                'city': request.form.get('city'),
                'inquiry_source': request.form.get('inquiry_source'),
                'priority': request.form.get('priority', 'Medium'),
                'assigned_salesperson_id': request.form.get('assigned_salesperson_id') or session.get('user_id'),
                'urgency': request.form.get('urgency'),
                'immediate_delivery': 1 if request.form.get('immediate_delivery') else 0,
                'specific_brand_required': 1 if request.form.get('specific_brand_required') else 0,
                'target_customer_price': request.form.get('target_customer_price'),
                'notes': request.form.get('notes'),
                'company_id': session.get('company_id')
            }

            inquiry_id = create_inquiry(data)

            # Add line items
            part_numbers = request.form.getlist('part_number')
            brands = request.form.getlist('brand')
            descriptions = request.form.getlist('description')
            quantities = request.form.getlist('requested_quantity')
            target_prices = request.form.getlist('target_price')
            notes_list = request.form.getlist('line_notes')

            for i in range(len(part_numbers)):
                if part_numbers[i]:
                    add_inquiry_line(inquiry_id, {
                        'part_number': part_numbers[i],
                        'brand': brands[i] if i < len(brands) else '',
                        'description': descriptions[i] if i < len(descriptions) else '',
                        'requested_quantity': int(quantities[i]) if quantities[i] else 0,
                        'target_price': float(target_prices[i]) if i < len(target_prices) and target_prices[i] else 0,
                        'notes': notes_list[i] if i < len(notes_list) else ''
                    })

            flash("Inquiry created successfully!", "success")
            return redirect(url_for('sales_inquiries_view', inquiry_id=inquiry_id))

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()
            customers = db.execute("SELECT id, name, phone, country FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()

        return render_template('sales/inquiries/form.html',
                             inquiry=None,
                             salespersons=[dict(s) for s in salespersons],
                             customers=[dict(c) for c in customers],
                             sources=get_inquiry_sources(),
                             statuses=get_inquiry_statuses(),
                             form_action='create')

    @app.route('/sales/inquiries/<int:inquiry_id>/')
    def sales_inquiries_view(inquiry_id):
        """View inquiry details."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_inquiry_by_id, update_inquiry_status

        inquiry = get_inquiry_by_id(inquiry_id)
        if not inquiry:
            flash("Inquiry not found.", "error")
            return redirect(url_for('sales_inquiries'))

        return render_template('sales/inquiries/view.html', inquiry=inquiry)

    @app.route('/sales/inquiries/<int:inquiry_id>/edit/', methods=['GET', 'POST'])
    def sales_inquiries_edit(inquiry_id):
        """Edit inquiry."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_inquiry_by_id, update_inquiry_status, add_inquiry_line

        inquiry = get_inquiry_by_id(inquiry_id)
        if not inquiry:
            flash("Inquiry not found.", "error")
            return redirect(url_for('sales_inquiries'))

        if request.method == 'POST':
            # Update status if changed
            new_status = request.form.get('status')
            if new_status and new_status != inquiry['status']:
                update_inquiry_status(inquiry_id, new_status, request.form.get('notes'))

            flash("Inquiry updated successfully!", "success")
            return redirect(url_for('sales_inquiries_view', inquiry_id=inquiry_id))

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()

        return render_template('sales/inquiries/form.html',
                             inquiry=inquiry,
                             salespersons=[dict(s) for s in salespersons],
                             sources=get_inquiry_sources(),
                             statuses=get_inquiry_statuses(),
                             form_action='edit')

    @app.route('/sales/inquiries/<int:inquiry_id>/convert-to-opportunity/', methods=['POST'])
    def sales_inquiries_convert_to_opportunity(inquiry_id):
        """Convert inquiry to opportunity."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_inquiry_by_id, create_opportunity, update_inquiry_status

        inquiry = get_inquiry_by_id(inquiry_id)
        if not inquiry:
            flash("Inquiry not found.", "error")
            return redirect(url_for('sales_inquiries'))

        # Create opportunity from inquiry
        opportunity_data = {
            'customer_id': inquiry.get('customer_id'),
            'customer_name': inquiry.get('customer_name'),
            'assigned_salesperson_id': inquiry.get('assigned_salesperson_id'),
            'source': inquiry.get('inquiry_source'),
            'market': inquiry.get('market'),
            'customer_type': inquiry.get('customer_type'),
            'notes': f"Converted from Inquiry {inquiry['inquiry_number']}",
            'company_id': session.get('company_id')
        }

        opportunity_id = create_opportunity(opportunity_data)
        update_inquiry_status(inquiry_id, 'Converted to Order', f"Converted to Opportunity")

        flash("Inquiry converted to Opportunity!", "success")
        return redirect(url_for('sales_opportunities_view', opportunity_id=opportunity_id))

    # =============================================================================
    # OPPORTUNITIES
    # =============================================================================

    @app.route('/sales/opportunities/')
    def sales_opportunities():
        """Opportunities list page."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_opportunities, get_opportunity_stages

        filters = {
            'search': request.args.get('search'),
            'stage': request.args.get('stage'),
            'salesperson_id': request.args.get('salesperson_id'),
            'source': request.args.get('source'),
            'sales_type': request.args.get('sales_type'),
            'market': request.args.get('market'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        result = get_opportunities(filters=filters, page=page, per_page=per_page)

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()

        return render_template('sales/opportunities/list.html',
                             opportunities=result['opportunities'],
                             total=result['total'],
                             page=result['page'],
                             pages=result['pages'],
                             filters=filters,
                             salespersons=[dict(s) for s in salespersons],
                             stages=get_opportunity_stages())

    @app.route('/sales/opportunities/new/', methods=['GET', 'POST'])
    def sales_opportunities_new():
        """Create new opportunity."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import create_opportunity, get_opportunity_stages

        if request.method == 'POST':
            data = {
                'customer_id': request.form.get('customer_id') or None,
                'customer_name': request.form.get('customer_name'),
                'assigned_salesperson_id': request.form.get('assigned_salesperson_id') or session.get('user_id'),
                'source': request.form.get('source'),
                'sales_type': request.form.get('sales_type'),
                'market': request.form.get('market'),
                'customer_type': request.form.get('customer_type'),
                'brand': request.form.get('brand'),
                'product_group': request.form.get('product_group'),
                'estimated_value': float(request.form.get('estimated_value', 0)),
                'success_probability': int(request.form.get('success_probability', 0)),
                'expected_close_date': request.form.get('expected_close_date'),
                'possible_competitors': request.form.get('possible_competitors'),
                'deal_risks': request.form.get('deal_risks'),
                'customer_requirements': request.form.get('customer_requirements'),
                'next_step': request.form.get('next_step'),
                'next_follow_up': request.form.get('next_follow_up'),
                'notes': request.form.get('notes'),
                'company_id': session.get('company_id')
            }

            opportunity_id = create_opportunity(data)
            flash("Opportunity created successfully!", "success")
            return redirect(url_for('sales_opportunities_view', opportunity_id=opportunity_id))

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()

        return render_template('sales/opportunities/form.html',
                             opportunity=None,
                             salespersons=[dict(s) for s in salespersons],
                             customers=[dict(c) for c in customers],
                             stages=get_opportunity_stages(),
                             form_action='create')

    @app.route('/sales/opportunities/<int:opportunity_id>/')
    def sales_opportunities_view(opportunity_id):
        """View opportunity details."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_opportunity_by_id

        opportunity = get_opportunity_by_id(opportunity_id)
        if not opportunity:
            flash("Opportunity not found.", "error")
            return redirect(url_for('sales_opportunities'))

        return render_template('sales/opportunities/view.html', opportunity=opportunity)

    @app.route('/sales/opportunities/<int:opportunity_id>/edit/', methods=['GET', 'POST'])
    def sales_opportunities_edit(opportunity_id):
        """Edit opportunity."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_opportunity_by_id, update_opportunity_stage

        opportunity = get_opportunity_by_id(opportunity_id)
        if not opportunity:
            flash("Opportunity not found.", "error")
            return redirect(url_for('sales_opportunities'))

        if request.method == 'POST':
            new_stage = request.form.get('stage')
            if new_stage and new_stage != opportunity['stage']:
                update_opportunity_stage(opportunity_id, new_stage, request.form.get('notes'))

            flash("Opportunity updated successfully!", "success")
            return redirect(url_for('sales_opportunities_view', opportunity_id=opportunity_id))

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()

        return render_template('sales/opportunities/form.html',
                             opportunity=opportunity,
                             salespersons=[dict(s) for s in salespersons],
                             stages=get_opportunity_stages(),
                             form_action='edit')

    # =============================================================================
    # QUOTATIONS
    # =============================================================================

    @app.route('/sales/quotations/')
    def sales_quotations():
        """Quotations list page."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_quotations, get_quotation_statuses

        filters = {
            'search': request.args.get('search'),
            'status': request.args.get('status'),
            'salesperson_id': request.args.get('salesperson_id'),
            'customer_id': request.args.get('customer_id'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
            'market': request.args.get('market'),
            'currency': request.args.get('currency'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        result = get_quotations(filters=filters, page=page, per_page=per_page)

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()

        return render_template('sales/quotations/list.html',
                             quotations=result['quotations'],
                             total=result['total'],
                             page=result['page'],
                             pages=result['pages'],
                             filters=filters,
                             salespersons=[dict(s) for s in salespersons],
                             customers=[dict(c) for c in customers],
                             statuses=get_quotation_statuses())

    @app.route('/sales/quotations/new/', methods=['GET', 'POST'])
    def sales_quotations_new():
        """Create new quotation."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import create_quotation, add_quotation_line, update_quotation_totals, get_quotation_statuses

        if request.method == 'POST':
            data = {
                'quotation_date': request.form.get('quotation_date'),
                'valid_until': request.form.get('valid_until'),
                'customer_id': request.form.get('customer_id') or None,
                'customer_name': request.form.get('customer_name'),
                'customer_type': request.form.get('customer_type'),
                'market': request.form.get('market'),
                'assigned_salesperson_id': request.form.get('assigned_salesperson_id') or session.get('user_id'),
                'currency': request.form.get('currency', 'AED'),
                'payment_terms': request.form.get('payment_terms'),
                'delivery_terms': request.form.get('delivery_terms'),
                'delivery_location': request.form.get('delivery_location'),
                'discount_percent': float(request.form.get('discount_percent', 0)),
                'tax_percent': float(request.form.get('tax_percent', 0)),
                'source': request.form.get('source'),
                'supply_lead_time': request.form.get('supply_lead_time'),
                'stock_status': request.form.get('stock_status'),
                'notes': request.form.get('notes'),
                'company_id': session.get('company_id')
            }

            quotation_id = create_quotation(data)

            # Add line items
            part_numbers = request.form.getlist('part_number')
            brands = request.form.getlist('brand')
            descriptions = request.form.getlist('description')
            quantities = request.form.getlist('requested_quantity')
            unit_prices = request.form.getlist('unit_price')
            discount_percents = request.form.getlist('discount_percent')
            final_prices = request.form.getlist('final_price')
            lead_times = request.form.getlist('supply_lead_time')
            stock_statuses = request.form.getlist('stock_status')

            for i in range(len(part_numbers)):
                if part_numbers[i]:
                    add_quotation_line(quotation_id, {
                        'line_number': i + 1,
                        'part_number': part_numbers[i],
                        'brand': brands[i] if i < len(brands) else '',
                        'description': descriptions[i] if i < len(descriptions) else '',
                        'requested_quantity': int(quantities[i]) if quantities[i] else 0,
                        'unit_price': float(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else 0,
                        'discount_percent': float(discount_percents[i]) if i < len(discount_percents) and discount_percents[i] else 0,
                        'final_price': float(final_prices[i]) if i < len(final_prices) and final_prices[i] else 0,
                        'supply_lead_time': lead_times[i] if i < len(lead_times) else '',
                        'stock_status': stock_statuses[i] if i < len(stock_statuses) else '',
                    })

            # Update totals
            update_quotation_totals(quotation_id)

            flash("Quotation created successfully!", "success")
            return redirect(url_for('sales_quotations_view', quotation_id=quotation_id))

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()
            customers = db.execute("SELECT id, name, payment_terms, credit_limit FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()
            parts = db.execute("SELECT part_number, name, brand FROM parts WHERE is_active = 1 ORDER BY part_number").fetchall()

        return render_template('sales/quotations/form.html',
                             quotation=None,
                             salespersons=[dict(s) for s in salespersons],
                             customers=[dict(c) for c in customers],
                             parts=[dict(p) for p in parts],
                             statuses=get_quotation_statuses(),
                             form_action='create')

    @app.route('/sales/quotations/<int:quotation_id>/')
    def sales_quotations_view(quotation_id):
        """View quotation details."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_quotation_by_id

        quotation = get_quotation_by_id(quotation_id)
        if not quotation:
            flash("Quotation not found.", "error")
            return redirect(url_for('sales_quotations'))

        return render_template('sales/quotations/view.html', quotation=quotation)

    @app.route('/sales/quotations/<int:quotation_id>/edit/', methods=['GET', 'POST'])
    def sales_quotations_edit(quotation_id):
        """Edit quotation."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_quotation_by_id, add_quotation_line, update_quotation_totals

        quotation = get_quotation_by_id(quotation_id)
        if not quotation:
            flash("Quotation not found.", "error")
            return redirect(url_for('sales_quotations'))

        if request.method == 'POST':
            # Update quotation fields
            with get_db() as db:
                db.execute("""
                    UPDATE sales_quotations SET
                        valid_until = ?, payment_terms = ?, delivery_terms = ?,
                        delivery_location = ?, discount_percent = ?, tax_percent = ?,
                        status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    request.form.get('valid_until'),
                    request.form.get('payment_terms'),
                    request.form.get('delivery_terms'),
                    request.form.get('delivery_location'),
                    float(request.form.get('discount_percent', 0)),
                    float(request.form.get('tax_percent', 0)),
                    request.form.get('status'),
                    request.form.get('notes'),
                    quotation_id
                ))
                db.commit()

            # Add new line items if any
            part_numbers = request.form.getlist('part_number')
            if part_numbers and part_numbers[0]:
                brands = request.form.getlist('brand')
                descriptions = request.form.getlist('description')
                quantities = request.form.getlist('requested_quantity')
                unit_prices = request.form.getlist('unit_price')
                final_prices = request.form.getlist('final_price')

                for i in range(len(part_numbers)):
                    if part_numbers[i]:
                        add_quotation_line(quotation_id, {
                            'line_number': len(quotation.get('lines', [])) + i + 1,
                            'part_number': part_numbers[i],
                            'brand': brands[i] if i < len(brands) else '',
                            'description': descriptions[i] if i < len(descriptions) else '',
                            'requested_quantity': int(quantities[i]) if quantities[i] else 0,
                            'unit_price': float(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else 0,
                            'final_price': float(final_prices[i]) if i < len(final_prices) and final_prices[i] else 0,
                        })

            update_quotation_totals(quotation_id)

            flash("Quotation updated successfully!", "success")
            return redirect(url_for('sales_quotations_view', quotation_id=quotation_id))

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()
            parts = db.execute("SELECT part_number, name, brand FROM parts WHERE is_active = 1 ORDER BY part_number").fetchall()

        return render_template('sales/quotations/form.html',
                             quotation=quotation,
                             salespersons=[dict(s) for s in salespersons],
                             parts=[dict(p) for p in parts],
                             statuses=get_quotation_statuses(),
                             form_action='edit')

    @app.route('/sales/quotations/<int:quotation_id>/convert-to-order/', methods=['POST'])
    def sales_quotations_convert_to_order(quotation_id):
        """Convert quotation to order."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_quotation_by_id, create_sales_order, add_order_line, update_order_status
        from database import log_audit

        quotation = get_quotation_by_id(quotation_id)
        if not quotation:
            flash("Quotation not found.", "error")
            return redirect(url_for('sales_quotations'))

        # Create order from quotation
        order_data = {
            'quotation_id': quotation_id,
            'customer_id': quotation.get('customer_id'),
            'customer_name': quotation.get('customer_name'),
            'customer_type': quotation.get('customer_type'),
            'market': quotation.get('market'),
            'assigned_salesperson_id': quotation.get('assigned_salesperson_id'),
            'currency': quotation.get('currency'),
            'payment_terms': quotation.get('payment_terms'),
            'delivery_terms': quotation.get('delivery_terms'),
            'delivery_address': quotation.get('delivery_location'),
            'discount_percent': quotation.get('discount_percent'),
            'tax_percent': quotation.get('tax_percent'),
            'total_amount': quotation.get('total_amount'),
            'notes': f"Converted from Quotation {quotation['quotation_number']}",
            'company_id': session.get('company_id')
        }

        order_id = create_sales_order(order_data)

        # Copy lines from quotation
        for line in quotation.get('lines', []):
            add_order_line(order_id, {
                'part_number': line.get('part_number'),
                'brand': line.get('brand'),
                'description': line.get('description'),
                'ordered_quantity': line.get('requested_quantity'),
                'unit_price': line.get('unit_price'),
                'discount_percent': line.get('discount_percent'),
                'final_price': line.get('final_price'),
                'tax_percent': quotation.get('tax_percent'),
                'tax_amount': 0,
                'line_total': float(line.get('final_price', 0)) * int(line.get('requested_quantity', 0)),
            })

        # Update quotation status
        with get_db() as db:
            db.execute("UPDATE sales_quotations SET status = 'Converted to Order', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (quotation_id,))
            db.commit()

        log_audit('sales_order', order_id, 'CREATE', session.get('user_id'),
                 notes=f"Created from quotation {quotation['quotation_number']}")

        flash("Quotation converted to Order!", "success")
        return redirect(url_for('sales_orders_view', order_id=order_id))

    # =============================================================================
    # SALES ORDERS
    # =============================================================================

    @app.route('/sales/orders/')
    def sales_orders():
        """Sales orders list page."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_sales_orders, get_order_statuses

        filters = {
            'search': request.args.get('search'),
            'status': request.args.get('status'),
            'salesperson_id': request.args.get('salesperson_id'),
            'customer_id': request.args.get('customer_id'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
            'market': request.args.get('market'),
            'is_export': request.args.get('is_export'),
            'priority': request.args.get('priority'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        result = get_sales_orders(filters=filters, page=page, per_page=per_page)

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()

        return render_template('sales/orders/list.html',
                             orders=result['orders'],
                             total=result['total'],
                             page=result['page'],
                             pages=result['pages'],
                             filters=filters,
                             salespersons=[dict(s) for s in salespersons],
                             customers=[dict(c) for c in customers],
                             statuses=get_order_statuses())

    @app.route('/sales/orders/new/', methods=['GET', 'POST'])
    def sales_orders_new():
        """Create new sales order."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import create_sales_order, add_order_line, get_order_statuses

        if request.method == 'POST':
            data = {
                'order_date': request.form.get('order_date'),
                'customer_id': request.form.get('customer_id') or None,
                'customer_name': request.form.get('customer_name'),
                'customer_type': request.form.get('customer_type'),
                'market': request.form.get('market'),
                'is_export': 1 if request.form.get('is_export') else 0,
                'export_country': request.form.get('export_country'),
                'incoterm': request.form.get('incoterm'),
                'transport_mode': request.form.get('transport_mode'),
                'quotation_id': request.form.get('quotation_id') or None,
                'assigned_salesperson_id': request.form.get('assigned_salesperson_id') or session.get('user_id'),
                'currency': request.form.get('currency', 'AED'),
                'payment_terms': request.form.get('payment_terms'),
                'delivery_terms': request.form.get('delivery_terms'),
                'delivery_address': request.form.get('delivery_address'),
                'shipment_type': request.form.get('shipment_type'),
                'discount_percent': float(request.form.get('discount_percent', 0)),
                'tax_percent': float(request.form.get('tax_percent', 0)),
                'priority': request.form.get('priority', 'Medium'),
                'promised_delivery_date': request.form.get('promised_delivery_date'),
                'notes': request.form.get('notes'),
                'company_id': session.get('company_id')
            }

            order_id = create_sales_order(data)

            # Add line items
            part_numbers = request.form.getlist('part_number')
            brands = request.form.getlist('brand')
            descriptions = request.form.getlist('description')
            quantities = request.form.getlist('ordered_quantity')
            unit_prices = request.form.getlist('unit_price')
            discount_percents = request.form.getlist('discount_percent')
            final_prices = request.form.getlist('final_price')

            subtotal = 0
            for i in range(len(part_numbers)):
                if part_numbers[i]:
                    line_total = float(final_prices[i] if i < len(final_prices) and final_prices[i] else 0) * int(quantities[i] if i < len(quantities) and quantities[i] else 0)
                    subtotal += line_total
                    add_order_line(order_id, {
                        'part_number': part_numbers[i],
                        'brand': brands[i] if i < len(brands) else '',
                        'description': descriptions[i] if i < len(descriptions) else '',
                        'ordered_quantity': int(quantities[i]) if i < len(quantities) and quantities[i] else 0,
                        'unit_price': float(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else 0,
                        'discount_percent': float(discount_percents[i]) if i < len(discount_percents) and discount_percents[i] else 0,
                        'final_price': float(final_prices[i]) if i < len(final_prices) and final_prices[i] else 0,
                        'tax_percent': float(request.form.get('tax_percent', 0)),
                        'tax_amount': 0,
                        'line_total': line_total,
                    })

            flash("Sales order created successfully!", "success")
            return redirect(url_for('sales_orders_view', order_id=order_id))

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()
            customers = db.execute("SELECT id, name, payment_terms, credit_limit FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()
            parts = db.execute("SELECT part_number, name, brand FROM parts WHERE is_active = 1 ORDER BY part_number").fetchall()
            quotations = db.execute("SELECT id, quotation_number, customer_name, total_amount FROM sales_quotations WHERE status IN ('Approved', 'Sent') ORDER BY quotation_date DESC").fetchall()

        return render_template('sales/orders/form.html',
                             order=None,
                             salespersons=[dict(s) for s in salespersons],
                             customers=[dict(c) for c in customers],
                             parts=[dict(p) for p in parts],
                             quotations=[dict(q) for q in quotations],
                             statuses=get_order_statuses(),
                             form_action='create')

    @app.route('/sales/orders/<int:order_id>/')
    def sales_orders_view(order_id):
        """View sales order details."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_order_by_id

        order = get_order_by_id(order_id)
        if not order:
            flash("Order not found.", "error")
            return redirect(url_for('sales_orders'))

        return render_template('sales/orders/view.html', order=order)

    @app.route('/sales/orders/<int:order_id>/edit/', methods=['GET', 'POST'])
    def sales_orders_edit(order_id):
        """Edit sales order."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_order_by_id, update_order_status, get_order_statuses

        order = get_order_by_id(order_id)
        if not order:
            flash("Order not found.", "error")
            return redirect(url_for('sales_orders'))

        if request.method == 'POST':
            new_status = request.form.get('status')
            if new_status and new_status != order['status']:
                update_order_status(order_id, new_status)

            flash("Order updated successfully!", "success")
            return redirect(url_for('sales_orders_view', order_id=order_id))

        return render_template('sales/orders/form.html',
                             order=order,
                             statuses=get_order_statuses(),
                             form_action='edit')

    @app.route('/sales/orders/<int:order_id>/approve/', methods=['POST'])
    def sales_orders_approve(order_id):
        """Approve sales order."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import update_order_status
        from database import log_audit

        update_order_status(order_id, 'Pending Reservation')
        log_audit('sales_order', order_id, 'APPROVE', session.get('user_id'))

        flash("Order approved!", "success")
        return redirect(url_for('sales_orders_view', order_id=order_id))

    # =============================================================================
    # RESERVATIONS
    # =============================================================================

    @app.route('/sales/reservations/')
    def sales_reservations():
        """Reservations list page."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_reservations, get_reservation_statuses

        filters = {
            'search': request.args.get('search'),
            'status': request.args.get('status'),
            'customer_id': request.args.get('customer_id'),
            'order_id': request.args.get('order_id'),
            'warehouse_id': request.args.get('warehouse_id'),
            'priority': request.args.get('priority'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        result = get_reservations(filters=filters, page=page, per_page=per_page)

        with get_db() as db:
            warehouses = db.execute("SELECT id, name FROM warehouses ORDER BY name").fetchall()
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()

        return render_template('sales/reservations/list.html',
                             reservations=result['reservations'],
                             total=result['total'],
                             page=result['page'],
                             pages=result['pages'],
                             filters=filters,
                             warehouses=[dict(w) for w in warehouses],
                             customers=[dict(c) for c in customers],
                             statuses=get_reservation_statuses())

    @app.route('/sales/reservations/new/', methods=['GET', 'POST'])
    def sales_reservations_new():
        """Create new reservation."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import create_reservation, get_reservation_statuses

        if request.method == 'POST':
            # Check available stock before creating reservation
            part_number = request.form.get('part_number')
            warehouse_id = request.form.get('warehouse_id')
            requested_qty = int(request.form.get('reserved_quantity', 0))

            with get_db() as db:
                stock = db.execute("""
                    SELECT COALESCE(SUM(quantity), 0) as available
                    FROM inventory WHERE part_number = ? AND warehouse_id = ?
                """, (part_number, warehouse_id)).fetchone()

                reserved = db.execute("""
                    SELECT COALESCE(SUM(reserved_quantity), 0) as reserved
                    FROM sales_reservations WHERE part_number = ? AND warehouse_id = ?
                    AND status = 'Active'
                """, (part_number, warehouse_id)).fetchone()

                available = (stock['available'] if stock else 0) - (reserved['reserved'] if reserved else 0)

                if available < requested_qty:
                    flash(f"Insufficient stock! Available: {available}, Requested: {requested_qty}", "error")
                    return redirect(url_for('sales_reservations_new'))

            data = {
                'customer_id': request.form.get('customer_id') or None,
                'reference_type': request.form.get('reference_type'),
                'reference_id': request.form.get('reference_id') or None,
                'order_id': request.form.get('order_id') or None,
                'quotation_id': request.form.get('quotation_id') or None,
                'part_number': part_number,
                'brand': request.form.get('brand'),
                'warehouse_id': warehouse_id,
                'reserved_quantity': requested_qty,
                'available_quantity_at_reservation': available,
                'expiry_date': request.form.get('expiry_date'),
                'reservation_reason': request.form.get('reservation_reason'),
                'priority': request.form.get('priority', 'Medium'),
                'assigned_salesperson_id': session.get('user_id'),
                'notes': request.form.get('notes'),
                'company_id': session.get('company_id')
            }

            reservation_id = create_reservation(data)
            flash("Reservation created successfully!", "success")
            return redirect(url_for('sales_reservations_view', reservation_id=reservation_id))

        with get_db() as db:
            warehouses = db.execute("SELECT id, name FROM warehouses ORDER BY name").fetchall()
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()
            parts = db.execute("SELECT part_number, name, brand FROM parts WHERE is_active = 1 ORDER BY part_number").fetchall()

        return render_template('sales/reservations/form.html',
                             reservation=None,
                             warehouses=[dict(w) for w in warehouses],
                             customers=[dict(c) for c in customers],
                             parts=[dict(p) for p in parts],
                             statuses=get_reservation_statuses(),
                             form_action='create')

    @app.route('/sales/reservations/<int:reservation_id>/')
    def sales_reservations_view(reservation_id):
        """View reservation details."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_reservations

        reservations = get_reservations({'reservation_id': reservation_id})
        reservation = reservations['reservations'][0] if reservations['reservations'] else None

        if not reservation:
            flash("Reservation not found.", "error")
            return redirect(url_for('sales_reservations'))

        return render_template('sales/reservations/view.html', reservation=reservation)

    @app.route('/sales/reservations/<int:reservation_id>/release/', methods=['POST'])
    def sales_reservations_release(reservation_id):
        """Release a reservation."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import release_reservation
        from database import log_audit

        release_reservation(reservation_id, request.form.get('reason'))
        log_audit('sales_reservation', reservation_id, 'RELEASE', session.get('user_id'),
                 notes=f"Released: {request.form.get('reason')}")

        flash("Reservation released!", "success")
        return redirect(url_for('sales_reservations'))

    # =============================================================================
    # DELIVERIES
    # =============================================================================

    @app.route('/sales/deliveries/')
    def sales_deliveries():
        """Deliveries list page."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_deliveries, get_delivery_statuses

        filters = {
            'search': request.args.get('search'),
            'status': request.args.get('status'),
            'order_id': request.args.get('order_id'),
            'customer_id': request.args.get('customer_id'),
            'delivery_type': request.args.get('delivery_type'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        result = get_deliveries(filters=filters, page=page, per_page=per_page)

        with get_db() as db:
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()
            vehicles = db.execute("SELECT id, vehicle_number FROM vehicles WHERE status = 'Active' ORDER BY vehicle_number").fetchall()

        return render_template('sales/deliveries/list.html',
                             deliveries=result['deliveries'],
                             total=result['total'],
                             page=result['page'],
                             pages=result['pages'],
                             filters=filters,
                             customers=[dict(c) for c in customers],
                             vehicles=[dict(v) for v in vehicles],
                             statuses=get_delivery_statuses())

    @app.route('/sales/deliveries/new/', methods=['GET', 'POST'])
    def sales_deliveries_new():
        """Create new delivery."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import create_delivery, get_delivery_statuses

        if request.method == 'POST':
            data = {
                'order_id': request.form.get('order_id'),
                'customer_id': request.form.get('customer_id'),
                'delivery_type': request.form.get('delivery_type'),
                'delivery_location': request.form.get('delivery_location'),
                'requested_date': request.form.get('requested_date'),
                'requested_time': request.form.get('requested_time'),
                'coordinator_id': session.get('user_id'),
                'vehicle_id': request.form.get('vehicle_id') or None,
                'driver_id': request.form.get('driver_id') or None,
                'notes': request.form.get('notes'),
                'company_id': session.get('company_id')
            }

            delivery_id = create_delivery(data)
            flash("Delivery created successfully!", "success")
            return redirect(url_for('sales_deliveries_view', delivery_id=delivery_id))

        with get_db() as db:
            orders = db.execute("""
                SELECT o.id, o.order_number, sc.name as customer_name, o.status
                FROM sales_orders o
                LEFT JOIN sales_customers sc ON o.customer_id = sc.id
                WHERE o.status IN ('Ready for Delivery', 'In Preparation')
                ORDER BY o.order_date DESC
            """).fetchall()
            vehicles = db.execute("SELECT id, vehicle_number FROM vehicles WHERE status = 'Active' ORDER BY vehicle_number").fetchall()

        return render_template('sales/deliveries/form.html',
                             delivery=None,
                             orders=[dict(o) for o in orders],
                             vehicles=[dict(v) for v in vehicles],
                             statuses=get_delivery_statuses(),
                             form_action='create')

    @app.route('/sales/deliveries/<int:delivery_id>/')
    def sales_deliveries_view(delivery_id):
        """View delivery details."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_delivery_by_id

        delivery = get_delivery_by_id(delivery_id)
        if not delivery:
            flash("Delivery not found.", "error")
            return redirect(url_for('sales_deliveries'))

        return render_template('sales/deliveries/view.html', delivery=delivery)

    # =============================================================================
    # RETURNS
    # =============================================================================

    @app.route('/sales/returns/')
    def sales_returns():
        """Returns list page."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_returns, get_return_statuses, get_return_reasons

        filters = {
            'search': request.args.get('search'),
            'status': request.args.get('status'),
            'return_reason': request.args.get('return_reason'),
            'customer_id': request.args.get('customer_id'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        result = get_returns(filters=filters, page=page, per_page=per_page)

        with get_db() as db:
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()

        return render_template('sales/returns/list.html',
                             returns_list=result['returns'],
                             total=result['total'],
                             page=result['page'],
                             pages=result['pages'],
                             filters=filters,
                             customers=[dict(c) for c in customers],
                             statuses=get_return_statuses(),
                             reasons=get_return_reasons())

    @app.route('/sales/returns/new/', methods=['GET', 'POST'])
    def sales_returns_new():
        """Create new return."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import create_return, get_return_statuses, get_return_reasons

        if request.method == 'POST':
            data = {
                'customer_id': request.form.get('customer_id'),
                'order_id': request.form.get('order_id') or None,
                'invoice_id': request.form.get('invoice_id') or None,
                'part_number': request.form.get('part_number'),
                'brand': request.form.get('brand'),
                'returned_quantity': int(request.form.get('returned_quantity', 0)),
                'item_condition': request.form.get('item_condition'),
                'return_reason': request.form.get('return_reason'),
                'inspection_required': 1 if request.form.get('inspection_required') else 0,
                'notes': request.form.get('notes'),
                'company_id': session.get('company_id')
            }

            return_id = create_return(data)
            flash("Return request created successfully!", "success")
            return redirect(url_for('sales_returns_view', return_id=return_id))

        with get_db() as db:
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()
            orders = db.execute("""
                SELECT o.id, o.order_number, sc.name as customer_name
                FROM sales_orders o
                LEFT JOIN sales_customers sc ON o.customer_id = sc.id
                ORDER BY o.order_date DESC LIMIT 100
            """).fetchall()

        return render_template('sales/returns/form.html',
                             return_item=None,
                             customers=[dict(c) for c in customers],
                             orders=[dict(o) for o in orders],
                             statuses=get_return_statuses(),
                             reasons=get_return_reasons(),
                             form_action='create')

    @app.route('/sales/returns/<int:return_id>/')
    def sales_returns_view(return_id):
        """View return details."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_returns

        returns = get_returns({'return_id': return_id})
        return_item = returns['returns_list'][0] if returns['returns_list'] else None

        if not return_item:
            flash("Return not found.", "error")
            return redirect(url_for('sales_returns'))

        return render_template('sales/returns/view.html', return_item=return_item)

    # =============================================================================
    # TARGETS & COMMISSIONS
    # =============================================================================

    @app.route('/sales/targets/')
    def sales_targets():
        """Sales targets page."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_sales_targets, get_target_periods

        filters = {
            'period': request.args.get('period'),
            'salesperson_id': request.args.get('salesperson_id'),
            'year': request.args.get('year', datetime.now().year),
        }

        targets = get_sales_targets(filters=filters)

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()

        return render_template('sales/targets/list.html',
                             targets=targets,
                             filters=filters,
                             salespersons=[dict(s) for s in salespersons],
                             periods=get_target_periods())

    @app.route('/sales/targets/new/', methods=['GET', 'POST'])
    def sales_targets_new():
        """Create new target."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import create_sales_target, get_target_periods

        if request.method == 'POST':
            data = {
                'salesperson_id': request.form.get('salesperson_id'),
                'period': request.form.get('period', 'Monthly'),
                'year': request.form.get('year', datetime.now().year),
                'quarter': request.form.get('quarter') or None,
                'month': request.form.get('month') or None,
                'target_amount': float(request.form.get('target_amount', 0)),
                'target_quantity': int(request.form.get('target_quantity', 0)),
                'new_customer_target': int(request.form.get('new_customer_target', 0)),
                'reactivation_target': int(request.form.get('reactivation_target', 0)),
                'brand_target': request.form.get('brand_target'),
                'product_group_target': request.form.get('product_group_target'),
                'local_target': float(request.form.get('local_target', 0)),
                'export_target': float(request.form.get('export_target', 0)),
                'notes': request.form.get('notes'),
                'company_id': session.get('company_id')
            }

            target_id = create_sales_target(data)
            flash("Target created successfully!", "success")
            return redirect(url_for('sales_targets'))

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()

        return render_template('sales/targets/form.html',
                             target=None,
                             salespersons=[dict(s) for s in salespersons],
                             periods=get_target_periods(),
                             form_action='create')

    # =============================================================================
    # CONTRACTS
    # =============================================================================

    @app.route('/sales/contracts/')
    def sales_contracts():
        """Contracts list page."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_sales_contracts, get_contract_types

        filters = {
            'search': request.args.get('search'),
            'status': request.args.get('status'),
            'customer_id': request.args.get('customer_id'),
            'contract_type': request.args.get('contract_type'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        result = get_sales_contracts(filters=filters, page=page, per_page=per_page)

        with get_db() as db:
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()

        return render_template('sales/contracts/list.html',
                             contracts=result['contracts'],
                             total=result['total'],
                             page=result['page'],
                             pages=result['pages'],
                             filters=filters,
                             customers=[dict(c) for c in customers],
                             contract_types=get_contract_types())

    @app.route('/sales/contracts/new/', methods=['GET', 'POST'])
    def sales_contracts_new():
        """Create new contract."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import create_sales_contract, get_contract_types

        if request.method == 'POST':
            data = {
                'customer_id': request.form.get('customer_id'),
                'start_date': request.form.get('start_date'),
                'end_date': request.form.get('end_date'),
                'contract_type': request.form.get('contract_type'),
                'product_group': request.form.get('product_group'),
                'brand': request.form.get('brand'),
                'pricing_terms': request.form.get('pricing_terms'),
                'payment_terms': request.form.get('payment_terms'),
                'delivery_terms': request.form.get('delivery_terms'),
                'volume_commitment': request.form.get('volume_commitment'),
                'agreed_discounts': request.form.get('agreed_discounts'),
                'sla_terms': request.form.get('sla_terms'),
                'contract_owner_id': session.get('user_id'),
                'notes': request.form.get('notes'),
                'company_id': session.get('company_id')
            }

            contract_id = create_sales_contract(data)
            flash("Contract created successfully!", "success")
            return redirect(url_for('sales_contracts'))

        with get_db() as db:
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()

        return render_template('sales/contracts/form.html',
                             contract=None,
                             customers=[dict(c) for c in customers],
                             contract_types=get_contract_types(),
                             form_action='create')

    @app.route('/sales/contracts/<int:contract_id>/')
    def sales_contracts_view(contract_id):
        """View contract details."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_sales_contracts

        contracts = get_sales_contracts({'contract_id': contract_id})
        contract = contracts['contracts'][0] if contracts['contracts'] else None

        if not contract:
            flash("Contract not found.", "error")
            return redirect(url_for('sales_contracts'))

        return render_template('sales/contracts/view.html', contract=contract)

    # =============================================================================
    # ACTIVITIES
    # =============================================================================

    @app.route('/sales/activities/')
    def sales_activities():
        """Activities list page."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_sales_activities, get_activity_types

        filters = {
            'search': request.args.get('search'),
            'activity_type': request.args.get('activity_type'),
            'customer_id': request.args.get('customer_id'),
            'owner_id': request.args.get('owner_id'),
            'reference_type': request.args.get('reference_type'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
            'status': request.args.get('status'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        result = get_sales_activities(filters=filters, page=page, per_page=per_page)

        with get_db() as db:
            users = db.execute("SELECT id, username FROM users ORDER BY username").fetchall()
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()

        return render_template('sales/activities/list.html',
                             activities=result['activities'],
                             total=result['total'],
                             page=result['page'],
                             pages=result['pages'],
                             filters=filters,
                             users=[dict(u) for u in users],
                             customers=[dict(c) for c in customers],
                             activity_types=get_activity_types())

    @app.route('/sales/activities/new/', methods=['GET', 'POST'])
    def sales_activities_new():
        """Create new activity."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import create_sales_activity, get_activity_types

        if request.method == 'POST':
            data = {
                'activity_type': request.form.get('activity_type'),
                'activity_date': request.form.get('activity_date'),
                'activity_time': request.form.get('activity_time'),
                'customer_id': request.form.get('customer_id') or None,
                'owner_id': session.get('user_id'),
                'subject': request.form.get('subject'),
                'result': request.form.get('result'),
                'next_action': request.form.get('next_action'),
                'next_follow_up_date': request.form.get('next_follow_up_date'),
                'status': request.form.get('status', 'Completed'),
                'notes': request.form.get('notes'),
                'reference_type': request.form.get('reference_type'),
                'reference_id': request.form.get('reference_id'),
                'company_id': session.get('company_id')
            }

            activity_id = create_sales_activity(data)
            flash("Activity logged successfully!", "success")
            return redirect(url_for('sales_activities'))

        with get_db() as db:
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()

        return render_template('sales/activities/form.html',
                             activity=None,
                             customers=[dict(c) for c in customers],
                             activity_types=get_activity_types(),
                             form_action='create')

    # =============================================================================
    # PRICING
    # =============================================================================

    @app.route('/sales/pricing/')
    def sales_pricing():
        """Pricing management page."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_price_lists, get_special_prices

        price_lists = get_price_lists()
        special_prices = get_special_prices()

        return render_template('sales/pricing/list.html',
                             price_lists=price_lists,
                             special_prices=special_prices)

    @app.route('/sales/pricing/special-price-request/', methods=['GET', 'POST'])
    def sales_special_price_request():
        """Create special price request."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import create_special_price_request

        if request.method == 'POST':
            data = {
                'customer_id': request.form.get('customer_id'),
                'salesperson_id': session.get('user_id'),
                'part_number': request.form.get('part_number'),
                'brand': request.form.get('brand'),
                'quantity': int(request.form.get('quantity', 0)),
                'standard_price': float(request.form.get('standard_price', 0)),
                'proposed_price': float(request.form.get('proposed_price', 0)),
                'requested_discount': float(request.form.get('requested_discount', 0)),
                'reason': request.form.get('reason'),
                'urgency': request.form.get('urgency', 'Normal'),
                'notes': request.form.get('notes'),
                'company_id': session.get('company_id')
            }

            request_id = create_special_price_request(data)
            flash("Special price request submitted!", "success")
            return redirect(url_for('sales_pricing'))

        with get_db() as db:
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()
            parts = db.execute("SELECT part_number, name, brand FROM parts WHERE is_active = 1 ORDER BY part_number").fetchall()

        return render_template('sales/pricing/special_price_request.html',
                             customers=[dict(c) for c in customers],
                             parts=[dict(p) for p in parts])

    # =============================================================================
    # REPORTS
    # =============================================================================

    @app.route('/sales/reports/')
    def sales_reports():
        """Sales reports page."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        return render_template('sales/reports/index.html')

    @app.route('/sales/reports/sales-summary/')
    def sales_reports_summary():
        """Sales summary report."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        date_from = request.args.get('date_from', datetime.now().strftime('%Y-01-01'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        with get_db() as db:
            # Sales by day
            daily_sales = db.execute("""
                SELECT DATE(order_date) as date,
                       COUNT(*) as order_count,
                       SUM(total_amount) as total_sales
                FROM sales_orders
                WHERE order_date BETWEEN ? AND ?
                GROUP BY DATE(order_date)
                ORDER BY date
            """, (date_from, date_to)).fetchall()

            # Sales by status
            by_status = db.execute("""
                SELECT status, COUNT(*) as count, SUM(total_amount) as total
                FROM sales_orders
                WHERE order_date BETWEEN ? AND ?
                GROUP BY status
            """, (date_from, date_to)).fetchall()

            # Sales by market
            by_market = db.execute("""
                SELECT market, COUNT(*) as count, SUM(total_amount) as total
                FROM sales_orders
                WHERE order_date BETWEEN ? AND ?
                GROUP BY market
            """, (date_from, date_to)).fetchall()

            # Top customers
            top_customers = db.execute("""
                SELECT sc.name, SUM(o.total_amount) as total
                FROM sales_orders o
                JOIN sales_customers sc ON o.customer_id = sc.id
                WHERE o.order_date BETWEEN ? AND ?
                GROUP BY sc.id
                ORDER BY total DESC LIMIT 10
            """, (date_from, date_to)).fetchall()

            # Top salespersons
            top_salespersons = db.execute("""
                SELECT u.username, SUM(o.total_amount) as total
                FROM sales_orders o
                JOIN users u ON o.assigned_salesperson_id = u.id
                WHERE o.order_date BETWEEN ? AND ?
                GROUP BY u.id
                ORDER BY total DESC LIMIT 10
            """, (date_from, date_to)).fetchall()

        return render_template('sales/reports/sales_summary.html',
                             daily_sales=[dict(d) for d in daily_sales],
                             by_status=[dict(s) for s in by_status],
                             by_market=[dict(m) for m in by_market],
                             top_customers=[dict(c) for c in top_customers],
                             top_salespersons=[dict(s) for s in top_salespersons],
                             date_from=date_from,
                             date_to=date_to)

    @app.route('/sales/reports/sales-by-item/')
    def sales_reports_by_item():
        """Sales by item report."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        date_from = request.args.get('date_from', datetime.now().strftime('%Y-01-01'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        with get_db() as db:
            items = db.execute("""
                SELECT ol.part_number, ol.brand,
                       SUM(ol.ordered_quantity) as total_qty,
                       SUM(ol.line_total) as total_sales
                FROM sales_order_lines ol
                JOIN sales_orders o ON ol.order_id = o.id
                WHERE o.order_date BETWEEN ? AND ?
                GROUP BY ol.part_number, ol.brand
                ORDER BY total_sales DESC
            """, (date_from, date_to)).fetchall()

        return render_template('sales/reports/sales_by_item.html',
                             items=[dict(i) for i in items],
                             date_from=date_from,
                             date_to=date_to)

    @app.route('/sales/reports/inquiry-conversion/')
    def sales_reports_inquiry_conversion():
        """Inquiry conversion report."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        date_from = request.args.get('date_from', datetime.now().strftime('%Y-01-01'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        with get_db() as db:
            by_status = db.execute("""
                SELECT status, COUNT(*) as count
                FROM sales_inquiries
                WHERE inquiry_date BETWEEN ? AND ?
                GROUP BY status
            """, (date_from, date_to)).fetchall()

            by_source = db.execute("""
                SELECT inquiry_source, COUNT(*) as count
                FROM sales_inquiries
                WHERE inquiry_date BETWEEN ? AND ?
                GROUP BY inquiry_source
            """, (date_from, date_to)).fetchall()

        return render_template('sales/reports/inquiry_conversion.html',
                             by_status=[dict(s) for s in by_status],
                             by_source=[dict(s) for s in by_source],
                             date_from=date_from,
                             date_to=date_to)

    # =============================================================================
    # SETTINGS
    # =============================================================================

    @app.route('/sales/settings/')
    def sales_settings():
        """Sales settings page."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_quotation_statuses, get_order_statuses, get_inquiry_statuses, get_opportunity_stages

        # Get current settings
        with get_db() as db:
            settings = db.execute("SELECT * FROM sales_settings").fetchall()

        return render_template('sales/settings/index.html',
                             settings=[dict(s) for s in settings])

    @app.route('/sales/settings/general/', methods=['GET', 'POST'])
    def sales_settings_general():
        """General sales settings."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        if request.method == 'POST':
            # Save settings
            with get_db() as db:
                for key in ['default_currency', 'tax_percent', 'max_discount_percent',
                           'quotation_validity_days', 'reservation_validity_days',
                           'min_margin_percent', 'credit_check_threshold']:
                    value = request.form.get(key)
                    if value is not None:
                        db.execute("""
                            INSERT OR REPLACE INTO sales_settings (setting_key, setting_value)
                            VALUES (?, ?)
                        """, (key, value))
                db.commit()

            flash("Settings saved!", "success")
            return redirect(url_for('sales_settings'))

        with get_db() as db:
            settings_rows = db.execute("SELECT setting_key, setting_value FROM sales_settings").fetchall()
            settings = {row['setting_key']: row['setting_value'] for row in settings_rows}

        return render_template('sales/settings/general.html', settings=settings)

    # =============================================================================
    # API ENDPOINTS FOR AJAX
    # =============================================================================

    @app.route('/api/sales/customer/<int:customer_id>/balance/')
    def api_customer_balance(customer_id):
        """Get customer balance API."""
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        from sales_models import get_customer_balance
        balance = get_customer_balance(customer_id)
        return jsonify(balance)

    @app.route('/api/sales/customer/<int:customer_id>/history/')
    def api_customer_history(customer_id):
        """Get customer transaction history."""
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        transactions = get_all("""
            SELECT * FROM sales_customer_transactions
            WHERE customer_id = ?
            ORDER BY transaction_date DESC LIMIT 20
        """, (customer_id,))

        return jsonify(transactions)

    @app.route('/api/sales/item/stock/<part_number>/')
    def api_item_stock(part_number):
        """Get item stock availability."""
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        with get_db() as db:
            stock = db.execute("""
                SELECT w.name as warehouse, COALESCE(SUM(i.quantity), 0) as quantity
                FROM inventory i
                JOIN warehouses w ON i.warehouse_id = w.id
                WHERE i.part_number = ?
                GROUP BY w.id
            """, (part_number,)).fetchall()

        return jsonify([dict(s) for s in stock])

    @app.route('/api/sales/item/price/<part_number>/')
    def api_item_price(part_number):
        """Get item price for customer."""
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        customer_id = request.args.get('customer_id')
        quantity = int(request.args.get('quantity', 1))

        with get_db() as db:
            # Check special price first
            if customer_id:
                special = db.execute("""
                    SELECT price FROM sales_special_prices
                    WHERE customer_id = ? AND part_number = ?
                    AND is_active = 1 AND approved = 1
                    AND valid_from <= DATE('now') AND valid_until >= DATE('now')
                    AND quantity <= ?
                    ORDER BY quantity DESC LIMIT 1
                """, (customer_id, part_number, quantity)).fetchone()

                if special:
                    return jsonify({'price': special['price'], 'source': 'special'})

            # Get standard price from parts
            part = db.execute("SELECT part_number, name, standard_price FROM parts WHERE part_number = ?", (part_number,)).fetchone()
            if part:
                return jsonify({
                    'price': part['standard_price'],
                    'source': 'standard',
                    'part_name': part['name']
                })

        return jsonify({'error': 'Item not found'}), 404

    @app.route('/api/sales/salesperson/<int:salesperson_id>/performance/')
    def api_salesperson_performance(salesperson_id):
        """Get salesperson performance metrics."""
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        from sales_models import get_salesperson_performance

        period = request.args.get('period', 'monthly')
        performance = get_salesperson_performance(salesperson_id, period)

        return jsonify(performance)

    # =============================================================================
    # LOCAL SALES & EXPORT SALES (Filtered views using existing tables)
    # =============================================================================

    @app.route('/sales/local-sales/')
    def sales_local_sales():
        """Local sales view - filtered view of orders for local market."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_sales_orders

        filters = {
            'market': 'Local',
            'search': request.args.get('search'),
            'status': request.args.get('status'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        result = get_sales_orders(filters=filters, page=page, per_page=per_page)

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()

        return render_template('sales/orders/list.html',
                             orders=result['orders'],
                             total=result['total'],
                             page=result['page'],
                             pages=result['pages'],
                             filters=filters,
                             salespersons=[dict(s) for s in salespersons],
                             customers=[],
                             statuses=get_order_statuses())

    @app.route('/sales/export-sales/')
    def sales_export_sales():
        """Export sales view - filtered view of orders for export market."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_models import get_sales_orders

        filters = {
            'market': 'Export',
            'search': request.args.get('search'),
            'status': request.args.get('status'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        result = get_sales_orders(filters=filters, page=page, per_page=per_page)

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()

        return render_template('sales/orders/list.html',
                             orders=result['orders'],
                             total=result['total'],
                             page=result['page'],
                             pages=result['pages'],
                             filters=filters,
                             salespersons=[dict(s) for s in salespersons],
                             customers=[],
                             statuses=get_order_statuses())

    return app
