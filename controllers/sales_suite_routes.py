"""
Sales Management Suite - Extended Route Handlers
=====================================
Additional Flask route handlers for the complete Sales Management Suite.

Handles:
- Pro forma Invoices
- Customer Purchase Orders
- Sales Confirmation Orders
- Sales Invoices
- Sales Alerts
- Enhanced Dashboard Views
- Role-specific Dashboards

Usage:
    from sales_suite_routes import register_sales_suite_routes
    register_sales_suite_routes(app, require_login, require_permission, get_db)
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from datetime import datetime
import json


def register_sales_suite_routes(app: Flask, require_login, require_permission, get_db):
    """Register all sales suite route handlers."""

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
    # PRO FORMA INVOICES
    # =============================================================================

    @app.route('/sales/proforma/')
    @app.route('/sales/proforma/invoices/')
    def sales_proforma_list():
        """Pro forma invoices list page."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import get_proforma_invoices, get_proforma_statuses

        filters = {
            'search': request.args.get('search'),
            'status': request.args.get('status'),
            'salesperson_id': request.args.get('salesperson_id'),
            'customer_id': request.args.get('customer_id'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
            'market': request.args.get('market'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        result = get_proforma_invoices(filters=filters, page=page, per_page=per_page)

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()

        return render_template('sales/proforma/list.html',
                             proforma_invoices=result['proforma_invoices'],
                             total=result['total'],
                             page=result['page'],
                             pages=result['pages'],
                             filters=filters,
                             salespersons=[dict(s) for s in salespersons],
                             customers=[dict(c) for c in customers],
                             statuses=get_proforma_statuses())

    @app.route('/sales/proforma/new/', methods=['GET', 'POST'])
    @app.route('/sales/proforma/invoices/new/', methods=['GET', 'POST'])
    def sales_proforma_new():
        """Create new pro forma invoice."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import create_proforma_invoice, add_proforma_line, update_proforma_totals, get_proforma_statuses

        if request.method == 'POST':
            data = {
                'proforma_date': request.form.get('proforma_date'),
                'valid_until': request.form.get('valid_until'),
                'customer_id': request.form.get('customer_id') or None,
                'customer_name': request.form.get('customer_name'),
                'customer_type': request.form.get('customer_type'),
                'market': request.form.get('market', 'Local'),
                'assigned_salesperson_id': request.form.get('assigned_salesperson_id') or session.get('user_id'),
                'currency': request.form.get('currency', 'AED'),
                'payment_terms': request.form.get('payment_terms'),
                'delivery_terms': request.form.get('delivery_terms'),
                'incoterm': request.form.get('incoterm'),
                'discount_percent': float(request.form.get('discount_percent', 0)),
                'tax_percent': float(request.form.get('tax_percent', 5)),
                'advance_payment_percent': float(request.form.get('advance_payment_percent', 0)),
                'bank_details': request.form.get('bank_details'),
                'status': request.form.get('status', 'Draft'),
                'source': request.form.get('source'),
                'notes': request.form.get('notes'),
                'company_id': session.get('company_id')
            }

            proforma_id = create_proforma_invoice(data)

            # Add line items
            part_numbers = request.form.getlist('part_number')
            brands = request.form.getlist('brand')
            descriptions = request.form.getlist('description')
            quantities = request.form.getlist('requested_quantity')
            unit_prices = request.form.getlist('unit_price')
            final_prices = request.form.getlist('final_price')

            for i in range(len(part_numbers)):
                if part_numbers[i]:
                    add_proforma_line(proforma_id, {
                        'line_number': i + 1,
                        'part_number': part_numbers[i],
                        'brand': brands[i] if i < len(brands) else '',
                        'description': descriptions[i] if i < len(descriptions) else '',
                        'requested_quantity': int(quantities[i]) if i < len(quantities) and quantities[i] else 0,
                        'unit_price': float(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else 0,
                        'final_price': float(final_prices[i]) if i < len(final_prices) and final_prices[i] else 0,
                        'tax_percent': float(request.form.get('tax_percent', 5)),
                        'line_total': float(final_prices[i] if i < len(final_prices) and final_prices[i] else 0) * int(quantities[i] if i < len(quantities) and quantities[i] else 0),
                    })

            update_proforma_totals(proforma_id)

            flash("Pro forma invoice created successfully!", "success")
            return redirect(url_for('sales_proforma_view', proforma_id=proforma_id))

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()
            customers = db.execute("SELECT id, name, payment_terms, credit_limit FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()
            parts = db.execute("SELECT part_number, name, brand, standard_price FROM parts WHERE is_active = 1 ORDER BY part_number").fetchall()

        return render_template('sales/proforma/form.html',
                             proforma=None,
                             salespersons=[dict(s) for s in salespersons],
                             customers=[dict(c) for c in customers],
                             parts=[dict(p) for p in parts],
                             statuses=get_proforma_statuses(),
                             form_action='create')

    @app.route('/sales/proforma/<int:proforma_id>/')
    def sales_proforma_view(proforma_id):
        """View pro forma invoice details."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import get_proforma_by_id

        proforma = get_proforma_by_id(proforma_id)
        if not proforma:
            flash("Pro forma invoice not found.", "error")
            return redirect(url_for('sales_proforma_list'))

        return render_template('sales/proforma/view.html', proforma=proforma)

    @app.route('/sales/proforma/<int:proforma_id>/edit/', methods=['GET', 'POST'])
    def sales_proforma_edit(proforma_id):
        """Edit pro forma invoice."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import get_proforma_by_id, update_proforma_totals, get_proforma_statuses

        proforma = get_proforma_by_id(proforma_id)
        if not proforma:
            flash("Pro forma invoice not found.", "error")
            return redirect(url_for('sales_proforma_list'))

        if request.method == 'POST':
            with get_db() as db:
                db.execute("""
                    UPDATE sales_proforma_invoices SET
                        valid_until = ?, payment_terms = ?, delivery_terms = ?,
                        incoterm = ?, discount_percent = ?, tax_percent = ?,
                        advance_payment_percent = ?, bank_details = ?,
                        status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    request.form.get('valid_until'),
                    request.form.get('payment_terms'),
                    request.form.get('delivery_terms'),
                    request.form.get('incoterm'),
                    float(request.form.get('discount_percent', 0)),
                    float(request.form.get('tax_percent', 5)),
                    float(request.form.get('advance_payment_percent', 0)),
                    request.form.get('bank_details'),
                    request.form.get('status'),
                    request.form.get('notes'),
                    proforma_id
                ))
                db.commit()

            update_proforma_totals(proforma_id)
            flash("Pro forma invoice updated successfully!", "success")
            return redirect(url_for('sales_proforma_view', proforma_id=proforma_id))

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()

        return render_template('sales/proforma/form.html',
                             proforma=proforma,
                             salespersons=[dict(s) for s in salespersons],
                             statuses=get_proforma_statuses(),
                             form_action='edit')

    # =============================================================================
    # CUSTOMER PURCHASE ORDERS
    # =============================================================================

    @app.route('/sales/customer-pos/')
    @app.route('/sales/customer-purchase-orders/')
    def sales_customer_pos_list():
        """Customer purchase orders list page."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import get_customer_pos, get_customer_po_statuses

        filters = {
            'search': request.args.get('search'),
            'status': request.args.get('status'),
            'review_status': request.args.get('review_status'),
            'salesperson_id': request.args.get('salesperson_id'),
            'customer_id': request.args.get('customer_id'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        result = get_customer_pos(filters=filters, page=page, per_page=per_page)

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()

        return render_template('sales/customer_pos/list.html',
                             customer_pos=result['customer_pos'],
                             total=result['total'],
                             page=result['page'],
                             pages=result['pages'],
                             filters=filters,
                             salespersons=[dict(s) for s in salespersons],
                             customers=[dict(c) for c in customers],
                             statuses=get_customer_po_statuses())

    @app.route('/sales/customer-pos/new/', methods=['GET', 'POST'])
    @app.route('/sales/customer-purchase-orders/new/', methods=['GET', 'POST'])
    def sales_customer_pos_new():
        """Create new customer PO."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import create_customer_po, add_customer_po_line, get_customer_po_statuses

        if request.method == 'POST':
            data = {
                'po_date': request.form.get('po_date'),
                'customer_id': request.form.get('customer_id') or None,
                'customer_name': request.form.get('customer_name'),
                'reference_quotation_id': request.form.get('reference_quotation_id') or None,
                'reference_proforma_id': request.form.get('reference_proforma_id') or None,
                'currency': request.form.get('currency', 'AED'),
                'payment_terms': request.form.get('payment_terms'),
                'incoterm': request.form.get('incoterm'),
                'destination_country': request.form.get('destination_country'),
                'destination_port': request.form.get('destination_port'),
                'requested_delivery_date': request.form.get('requested_delivery_date'),
                'assigned_salesperson_id': request.form.get('assigned_salesperson_id') or session.get('user_id'),
                'status': 'Received',
                'review_status': 'Pending',
                'notes': request.form.get('notes'),
                'company_id': session.get('company_id')
            }

            cpo_id = create_customer_po(data)

            # Add line items
            part_numbers = request.form.getlist('part_number')
            brands = request.form.getlist('brand')
            quantities = request.form.getlist('ordered_quantity')
            unit_prices = request.form.getlist('unit_price')

            for i in range(len(part_numbers)):
                if part_numbers[i]:
                    add_customer_po_line(cpo_id, {
                        'line_number': i + 1,
                        'part_number': part_numbers[i],
                        'brand': brands[i] if i < len(brands) else '',
                        'ordered_quantity': int(quantities[i]) if i < len(quantities) and quantities[i] else 0,
                        'unit_price': float(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else 0,
                        'total_price': float(unit_prices[i] if i < len(unit_prices) and unit_prices[i] else 0) * int(quantities[i] if i < len(quantities) and quantities[i] else 0),
                    })

            flash("Customer PO created successfully!", "success")
            return redirect(url_for('sales_customer_pos_view', cpo_id=cpo_id))

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()
            quotations = db.execute("SELECT id, quotation_number, customer_name FROM sales_quotations WHERE status IN ('Approved', 'Converted to Order') ORDER BY quotation_date DESC").fetchall()
            proformas = db.execute("SELECT id, proforma_number, customer_name FROM sales_proforma_invoices WHERE status = 'Accepted' ORDER BY proforma_date DESC").fetchall()

        return render_template('sales/customer_pos/form.html',
                             customer_po=None,
                             salespersons=[dict(s) for s in salespersons],
                             customers=[dict(c) for c in customers],
                             quotations=[dict(q) for q in quotations],
                             proformas=[dict(p) for p in proformas],
                             statuses=get_customer_po_statuses(),
                             form_action='create')

    @app.route('/sales/customer-pos/<int:cpo_id>/')
    def sales_customer_pos_view(cpo_id):
        """View customer PO details."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import get_customer_po_by_id

        cpo = get_customer_po_by_id(cpo_id)
        if not cpo:
            flash("Customer PO not found.", "error")
            return redirect(url_for('sales_customer_pos_list'))

        return render_template('sales/customer_pos/view.html', customer_po=cpo)

    # =============================================================================
    # SALES CONFIRMATIONS
    # =============================================================================

    @app.route('/sales/confirmations/')
    def sales_confirmations_list():
        """Sales confirmations list page."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import get_confirmations, get_confirmation_statuses

        filters = {
            'search': request.args.get('search'),
            'status': request.args.get('status'),
            'customer_acceptance_status': request.args.get('customer_acceptance_status'),
            'salesperson_id': request.args.get('salesperson_id'),
            'customer_id': request.args.get('customer_id'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        result = get_confirmations(filters=filters, page=page, per_page=per_page)

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()

        return render_template('sales/confirmations/list.html',
                             confirmations=result['confirmations'],
                             total=result['total'],
                             page=result['page'],
                             pages=result['pages'],
                             filters=filters,
                             salespersons=[dict(s) for s in salespersons],
                             customers=[dict(c) for c in customers],
                             statuses=get_confirmation_statuses())

    @app.route('/sales/confirmations/new/', methods=['GET', 'POST'])
    def sales_confirmations_new():
        """Create new sales confirmation."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import create_confirmation, add_confirmation_line, get_confirmation_statuses

        if request.method == 'POST':
            data = {
                'confirmation_date': request.form.get('confirmation_date'),
                'reference_quotation_id': request.form.get('reference_quotation_id') or None,
                'reference_proforma_id': request.form.get('reference_proforma_id') or None,
                'reference_customer_po_id': request.form.get('reference_customer_po_id') or None,
                'customer_id': request.form.get('customer_id') or None,
                'customer_name': request.form.get('customer_name'),
                'customer_type': request.form.get('customer_type'),
                'market': request.form.get('market', 'Local'),
                'assigned_salesperson_id': request.form.get('assigned_salesperson_id') or session.get('user_id'),
                'currency': request.form.get('currency', 'AED'),
                'payment_terms': request.form.get('payment_terms'),
                'delivery_terms': request.form.get('delivery_terms'),
                'incoterm': request.form.get('incoterm'),
                'lead_time_days': request.form.get('lead_time_days'),
                'discount_percent': float(request.form.get('discount_percent', 0)),
                'tax_percent': float(request.form.get('tax_percent', 5)),
                'status': request.form.get('status', 'Draft'),
                'notes': request.form.get('notes'),
                'company_id': session.get('company_id')
            }

            confirmation_id = create_confirmation(data)

            # Add line items
            part_numbers = request.form.getlist('part_number')
            brands = request.form.getlist('brand')
            descriptions = request.form.getlist('description')
            quantities = request.form.getlist('confirmed_quantity')
            unit_prices = request.form.getlist('unit_price')
            final_prices = request.form.getlist('final_price')

            for i in range(len(part_numbers)):
                if part_numbers[i]:
                    add_confirmation_line(confirmation_id, {
                        'line_number': i + 1,
                        'part_number': part_numbers[i],
                        'brand': brands[i] if i < len(brands) else '',
                        'description': descriptions[i] if i < len(descriptions) else '',
                        'confirmed_quantity': int(quantities[i]) if i < len(quantities) and quantities[i] else 0,
                        'unit_price': float(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else 0,
                        'final_price': float(final_prices[i]) if i < len(final_prices) and final_prices[i] else 0,
                        'tax_percent': float(request.form.get('tax_percent', 5)),
                        'line_total': float(final_prices[i] if i < len(final_prices) and final_prices[i] else 0) * int(quantities[i] if i < len(quantities) and quantities[i] else 0),
                    })

            flash("Sales confirmation created successfully!", "success")
            return redirect(url_for('sales_confirmations_view', confirmation_id=confirmation_id))

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()
            quotations = db.execute("SELECT id, quotation_number, customer_name FROM sales_quotations WHERE status = 'Approved' ORDER BY quotation_date DESC").fetchall()
            proformas = db.execute("SELECT id, proforma_number, customer_name FROM sales_proforma_invoices WHERE status = 'Accepted' ORDER BY proforma_date DESC").fetchall()

        return render_template('sales/confirmations/form.html',
                             confirmation=None,
                             salespersons=[dict(s) for s in salespersons],
                             customers=[dict(c) for c in customers],
                             quotations=[dict(q) for q in quotations],
                             proformas=[dict(p) for p in proformas],
                             statuses=get_confirmation_statuses(),
                             form_action='create')

    @app.route('/sales/confirmations/<int:confirmation_id>/')
    def sales_confirmations_view(confirmation_id):
        """View confirmation details."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import get_confirmation_by_id

        confirmation = get_confirmation_by_id(confirmation_id)
        if not confirmation:
            flash("Confirmation not found.", "error")
            return redirect(url_for('sales_confirmations_list'))

        return render_template('sales/confirmations/view.html', confirmation=confirmation)

    # =============================================================================
    # SALES INVOICES
    # =============================================================================

    @app.route('/sales/invoices/')
    def sales_invoices_list():
        """Sales invoices list page."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import get_sales_invoices, get_invoice_statuses

        filters = {
            'search': request.args.get('search'),
            'status': request.args.get('status'),
            'payment_status': request.args.get('payment_status'),
            'salesperson_id': request.args.get('salesperson_id'),
            'customer_id': request.args.get('customer_id'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
            'market': request.args.get('market'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        result = get_sales_invoices(filters=filters, page=page, per_page=per_page)

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()

        return render_template('sales/invoices/list.html',
                             invoices=result['invoices'],
                             total=result['total'],
                             page=result['page'],
                             pages=result['pages'],
                             filters=filters,
                             salespersons=[dict(s) for s in salespersons],
                             customers=[dict(c) for c in customers],
                             statuses=get_invoice_statuses())

    @app.route('/sales/invoices/new/', methods=['GET', 'POST'])
    def sales_invoices_new():
        """Create new sales invoice."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import create_sales_invoice, add_invoice_line, get_invoice_statuses

        if request.method == 'POST':
            data = {
                'invoice_date': request.form.get('invoice_date'),
                'due_date': request.form.get('due_date'),
                'order_id': request.form.get('order_id') or None,
                'delivery_id': request.form.get('delivery_id') or None,
                'customer_id': request.form.get('customer_id') or None,
                'customer_name': request.form.get('customer_name'),
                'customer_type': request.form.get('customer_type'),
                'market': request.form.get('market', 'Local'),
                'billing_address': request.form.get('billing_address'),
                'assigned_salesperson_id': request.form.get('assigned_salesperson_id') or session.get('user_id'),
                'currency': request.form.get('currency', 'AED'),
                'payment_terms': request.form.get('payment_terms'),
                'incoterm': request.form.get('incoterm'),
                'discount_percent': float(request.form.get('discount_percent', 0)),
                'tax_percent': float(request.form.get('tax_percent', 5)),
                'status': request.form.get('status', 'Draft'),
                'notes': request.form.get('notes'),
                'company_id': session.get('company_id')
            }

            invoice_id = create_sales_invoice(data)

            # Add line items
            part_numbers = request.form.getlist('part_number')
            brands = request.form.getlist('brand')
            descriptions = request.form.getlist('description')
            quantities = request.form.getlist('quantity')
            unit_prices = request.form.getlist('unit_price')
            final_prices = request.form.getlist('final_price')

            for i in range(len(part_numbers)):
                if part_numbers[i]:
                    add_invoice_line(invoice_id, {
                        'line_number': i + 1,
                        'part_number': part_numbers[i],
                        'brand': brands[i] if i < len(brands) else '',
                        'description': descriptions[i] if i < len(descriptions) else '',
                        'quantity': int(quantities[i]) if i < len(quantities) and quantities[i] else 0,
                        'unit_price': float(unit_prices[i]) if i < len(unit_prices) and unit_prices[i] else 0,
                        'final_price': float(final_prices[i]) if i < len(final_prices) and final_prices[i] else 0,
                        'tax_percent': float(request.form.get('tax_percent', 5)),
                        'line_total': float(final_prices[i] if i < len(final_prices) and final_prices[i] else 0) * int(quantities[i] if i < len(quantities) and quantities[i] else 0),
                    })

            flash("Sales invoice created successfully!", "success")
            return redirect(url_for('sales_invoices_view', invoice_id=invoice_id))

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%') ORDER BY username").fetchall()
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()
            orders = db.execute("SELECT id, order_number, customer_name FROM sales_orders WHERE status IN ('Ready for Delivery', 'Fully Delivered', 'Partially Delivered') ORDER BY order_date DESC").fetchall()

        return render_template('sales/invoices/form.html',
                             invoice=None,
                             salespersons=[dict(s) for s in salespersons],
                             customers=[dict(c) for c in customers],
                             orders=[dict(o) for o in orders],
                             statuses=get_invoice_statuses(),
                             form_action='create')

    @app.route('/sales/invoices/<int:invoice_id>/')
    def sales_invoices_view(invoice_id):
        """View invoice details."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import get_invoice_by_id

        invoice = get_invoice_by_id(invoice_id)
        if not invoice:
            flash("Invoice not found.", "error")
            return redirect(url_for('sales_invoices_list'))

        return render_template('sales/invoices/view.html', invoice=invoice)

    # =============================================================================
    # SALES ALERTS
    # =============================================================================

    @app.route('/sales/alerts/')
    def sales_alerts_list():
        """Sales alerts list page."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import get_sales_alerts, get_alert_types, get_alert_priorities

        filters = {
            'alert_type': request.args.get('alert_type'),
            'status': request.args.get('status'),
            'priority': request.args.get('priority'),
            'salesperson_id': request.args.get('salesperson_id'),
            'customer_id': request.args.get('customer_id'),
        }

        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))

        result = get_sales_alerts(filters=filters, page=page, per_page=per_page)

        with get_db() as db:
            salespersons = db.execute("SELECT id, username FROM users ORDER BY username").fetchall()
            customers = db.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 ORDER BY name").fetchall()

        return render_template('sales/alerts/list.html',
                             alerts=result['alerts'],
                             total=result['total'],
                             page=result['page'],
                             pages=result['pages'],
                             filters=filters,
                             salespersons=[dict(s) for s in salespersons],
                             customers=[dict(c) for c in customers],
                             alert_types=get_alert_types(),
                             priorities=get_alert_priorities())

    @app.route('/sales/alerts/<int:alert_id>/acknowledge/', methods=['POST'])
    def sales_alerts_acknowledge(alert_id):
        """Acknowledge an alert."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import acknowledge_alert

        acknowledge_alert(alert_id, session.get('user_id'))
        flash("Alert acknowledged!", "success")
        return redirect(url_for('sales_alerts_list'))

    @app.route('/sales/alerts/<int:alert_id>/resolve/', methods=['POST'])
    def sales_alerts_resolve(alert_id):
        """Resolve an alert."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import resolve_alert

        resolve_alert(alert_id, session.get('user_id'), request.form.get('resolution_notes'))
        flash("Alert resolved!", "success")
        return redirect(url_for('sales_alerts_list'))

    @app.route('/sales/alerts/generate/', methods=['POST'])
    def sales_alerts_generate():
        """Generate automatic sales alerts."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import generate_sales_alerts

        count = generate_sales_alerts()
        flash(f"Generated {count} new alerts!", "success")
        return redirect(url_for('sales_alerts_list'))

    # =============================================================================
    # ENHANCED DASHBOARD
    # =============================================================================

    @app.route('/sales/dashboard/suite/')
    def sales_dashboard_suite():
        """Enhanced sales dashboard with full suite metrics."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import get_sales_dashboard_suite, get_open_alerts_count

        user = get_current_user()
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        stats = get_sales_dashboard_suite(
            user_id=user['id'],
            user_role=user.get('role_name'),
            date_from=date_from,
            date_to=date_to
        )

        open_alerts = get_open_alerts_count(user['id'])

        return render_template('sales/dashboard_suite.html',
                             stats=stats,
                             user=user,
                             date_from=date_from,
                             date_to=date_to,
                             open_alerts=open_alerts)

    @app.route('/sales/dashboard/executive/')
    def sales_dashboard_executive():
        """Executive/COO sales dashboard."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import get_sales_dashboard_suite

        user = get_current_user()
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        stats = get_sales_dashboard_suite(
            user_id=user['id'],
            user_role='Executive',
            date_from=date_from,
            date_to=date_to
        )

        return render_template('sales/dashboard_executive.html',
                             stats=stats,
                             user=user,
                             date_from=date_from,
                             date_to=date_to)

    @app.route('/sales/dashboard/salesperson/')
    def sales_dashboard_salesperson():
        """Personal salesperson dashboard."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import get_salesperson_dashboard, get_open_alerts_count

        user = get_current_user()
        user_id = user['id']

        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        stats = get_salesperson_dashboard(
            salesperson_id=user_id,
            date_from=date_from,
            date_to=date_to
        )

        open_alerts = get_open_alerts_count(user_id)

        return render_template('sales/dashboard_salesperson.html',
                             stats=stats,
                             user=user,
                             date_from=date_from,
                             date_to=date_to,
                             open_alerts=open_alerts)

    @app.route('/sales/dashboard/export/')
    def sales_dashboard_export():
        """Export sales team dashboard."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        from sales_suite_models import get_sales_dashboard_suite

        user = get_current_user()
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')

        stats = get_sales_dashboard_suite(
            user_id=user['id'],
            user_role='Export',
            date_from=date_from,
            date_to=date_to
        )

        return render_template('sales/dashboard_export.html',
                             stats=stats,
                             user=user,
                             date_from=date_from,
                             date_to=date_to)

    # =============================================================================
    # ENHANCED REPORTS
    # =============================================================================

    @app.route('/sales/reports/pipeline/')
    def sales_reports_pipeline():
        """Sales pipeline analysis report."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        date_from = request.args.get('date_from', datetime.now().strftime('%Y-01-01'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        with get_db() as db:
            # Funnel data
            funnel = db.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM sales_inquiries WHERE inquiry_date BETWEEN ? AND ?) as inquiries,
                    (SELECT COUNT(*) FROM sales_quotations WHERE quotation_date BETWEEN ? AND ?) as quotations,
                    (SELECT COUNT(*) FROM sales_proforma_invoices WHERE proforma_date BETWEEN ? AND ?) as proformas,
                    (SELECT COUNT(*) FROM sales_confirmations WHERE confirmation_date BETWEEN ? AND ?) as confirmations,
                    (SELECT COUNT(*) FROM sales_orders WHERE order_date BETWEEN ? AND ?) as orders,
                    (SELECT COUNT(*) FROM sales_invoices WHERE invoice_date BETWEEN ? AND ?) as invoices
            """, (date_from, date_to, date_from, date_to, date_from, date_to, date_from, date_to,
                  date_from, date_to, date_from, date_to)).fetchone()

            # Opportunity stages
            stages = db.execute("""
                SELECT stage, COUNT(*) as count, SUM(estimated_value) as total_value
                FROM sales_opportunities
                WHERE stage NOT IN ('Won', 'Lost')
                GROUP BY stage
                ORDER BY FIELD(stage, 'Identified', 'Initial Contact', 'Qualification',
                         'Technical Review', 'Commercial Review', 'Quotation Sent',
                         'Negotiation', 'Terms Review', 'Pending Approval')
            """).fetchall()

            # Lost opportunities
            lost = db.execute("""
                SELECT COUNT(*) as count, 
                       GROUP_CONCAT(final_outcome, ', ') as reasons
                FROM sales_inquiries
                WHERE status = 'Lost' AND inquiry_date BETWEEN ? AND ?
            """, (date_from, date_to)).fetchone()

        return render_template('sales/reports/pipeline.html',
                             funnel=dict(funnel) if funnel else {},
                             stages=[dict(s) for s in stages] if stages else [],
                             lost=dict(lost) if lost else {},
                             date_from=date_from,
                             date_to=date_to)

    @app.route('/sales/reports/profitability/')
    def sales_reports_profitability():
        """Sales profitability report."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        date_from = request.args.get('date_from', datetime.now().strftime('%Y-01-01'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        with get_db() as db:
            # Sales by brand with margin
            by_brand = db.execute("""
                SELECT ol.brand,
                       SUM(ol.ordered_quantity) as qty_sold,
                       SUM(ol.line_total) as revenue,
                       SUM(ol.line_total * 0.7) as estimated_cost,
                       SUM(ol.line_total) - SUM(ol.line_total * 0.7) as gross_profit,
                       30 as margin_percent
                FROM sales_order_lines ol
                JOIN sales_orders o ON ol.order_id = o.id
                WHERE o.order_date BETWEEN ? AND ?
                GROUP BY ol.brand
                ORDER BY revenue DESC
            """, (date_from, date_to)).fetchall()

            # Sales by customer type
            by_type = db.execute("""
                SELECT o.customer_type,
                       COUNT(DISTINCT o.id) as order_count,
                       SUM(o.total_amount) as revenue
                FROM sales_orders o
                WHERE o.order_date BETWEEN ? AND ?
                GROUP BY o.customer_type
                ORDER BY revenue DESC
            """, (date_from, date_to)).fetchall()

            # Sales by market
            by_market = db.execute("""
                SELECT o.market,
                       COUNT(DISTINCT o.id) as order_count,
                       SUM(o.total_amount) as revenue
                FROM sales_orders o
                WHERE o.order_date BETWEEN ? AND ?
                GROUP BY o.market
                ORDER BY revenue DESC
            """, (date_from, date_to)).fetchall()

        return render_template('sales/reports/profitability.html',
                             by_brand=[dict(b) for b in by_brand] if by_brand else [],
                             by_type=[dict(t) for t in by_type] if by_type else [],
                             by_market=[dict(m) for m in by_market] if by_market else [],
                             date_from=date_from,
                             date_to=date_to)

    @app.route('/sales/reports/conversion/')
    def sales_reports_conversion():
        """Conversion rates analysis report."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        date_from = request.args.get('date_from', datetime.now().strftime('%Y-01-01'))
        date_to = request.args.get('date_to', datetime.now().strftime('%Y-%m-%d'))

        with get_db() as db:
            # Monthly conversion funnel
            monthly = db.execute("""
                SELECT 
                    strftime('%Y-%m', inquiry_date) as month,
                    COUNT(DISTINCT i.id) as inquiries,
                    COUNT(DISTINCT CASE WHEN EXISTS(SELECT 1 FROM sales_quotations q WHERE q.reference_inquiry_id = i.id) THEN i.id END) as quoted,
                    COUNT(DISTINCT CASE WHEN EXISTS(SELECT 1 FROM sales_orders o WHERE o.reference_inquiry_id = i.id) THEN i.id END) as ordered
                FROM sales_inquiries i
                WHERE i.inquiry_date BETWEEN ? AND ?
                GROUP BY strftime('%Y-%m', i.inquiry_date)
                ORDER BY month
            """, (date_from, date_to)).fetchall()

            # Source effectiveness
            by_source = db.execute("""
                SELECT inquiry_source,
                       COUNT(*) as inquiries,
                       SUM(CASE WHEN status = 'Converted to Order' THEN 1 ELSE 0 END) as converted,
                       SUM(CASE WHEN status = 'Lost' THEN 1 ELSE 0 END) as lost
                FROM sales_inquiries
                WHERE inquiry_date BETWEEN ? AND ?
                GROUP BY inquiry_source
                ORDER BY inquiries DESC
            """, (date_from, date_to)).fetchall()

        return render_template('sales/reports/conversion.html',
                             monthly=[dict(m) for m in monthly] if monthly else [],
                             by_source=[dict(s) for s in by_source] if by_source else [],
                             date_from=date_from,
                             date_to=date_to)

    # =============================================================================
    # API ENDPOINTS FOR AJAX
    # =============================================================================

    @app.route('/api/sales/proforma/<int:proforma_id>/totals/')
    def api_proforma_totals(proforma_id):
        """Get pro forma totals API."""
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        from sales_suite_models import get_proforma_by_id, update_proforma_totals

        proforma = get_proforma_by_id(proforma_id)
        if not proforma:
            return jsonify({'error': 'Not found'}), 404

        update_proforma_totals(proforma_id)

        return jsonify({
            'subtotal': proforma.get('subtotal', 0),
            'discount_amount': proforma.get('discount_amount', 0),
            'tax_amount': proforma.get('tax_amount', 0),
            'total_amount': proforma.get('total_amount', 0)
        })

    @app.route('/api/sales/alerts/count/')
    def api_alerts_count():
        """Get open alerts count API."""
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        from sales_suite_models import get_open_alerts_count

        count = get_open_alerts_count(session.get('user_id'))
        return jsonify({'count': count})

    @app.route('/api/sales/pipeline/summary/')
    def api_pipeline_summary():
        """Get pipeline summary API."""
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        with get_db() as db:
            summary = db.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM sales_inquiries WHERE status NOT IN ('Closed', 'Converted to Order', 'Lost')) as open_inquiries,
                    (SELECT COUNT(*) FROM sales_opportunities WHERE stage NOT IN ('Won', 'Lost', 'On Hold')) as open_opportunities,
                    (SELECT COUNT(*) FROM sales_quotations WHERE status IN ('Sent', 'Viewed', 'In Negotiation')) as pending_quotations,
                    (SELECT COUNT(*) FROM sales_proforma_invoices WHERE status = 'Issued') as pending_proformas,
                    (SELECT COUNT(*) FROM sales_confirmations WHERE customer_acceptance_status = 'Pending') as pending_confirmations,
                    (SELECT COUNT(*) FROM sales_orders WHERE status NOT IN ('Delivered', 'Cancelled', 'Closed')) as open_orders,
                    (SELECT COALESCE(SUM(estimated_value * success_probability / 100), 0) FROM sales_opportunities WHERE stage NOT IN ('Won', 'Lost', 'On Hold')) as weighted_opportunity_value
            """).fetchone()

        return jsonify(dict(summary) if summary else {})

    # =========================================================================
    # ENDPOINT ALIASES - backward compatibility for template references
    # =========================================================================
    # Template 'sales_suite_dashboard.html' uses url_for('sales_suite_dashboard')
    # but the actual route is 'sales_dashboard_suite'. This alias fixes the mismatch.
    app.add_url_rule(
        '/sales/dashboard/suite/',
        endpoint='sales_suite_dashboard',
        view_func=sales_dashboard_suite,
        methods=['GET']
    )

    return app
