"""
Procurement Management Routes
============================
Flask routes for the complete Procurement & Purchasing Management System.

Covers:
- Procurement Dashboard
- Supplier Management
- Purchase Requisitions
- RFQ / Supplier Inquiries
- Quotations & Comparison
- Vendor Selection & Approvals
- Purchase Orders
- Shipment & ETA Tracking
- Receiving Coordination
- Local Purchasing
- Import / International Purchasing
- Returns, Claims & Discrepancies
- Contracts & Price Agreements
- Budgets, Approvals & Controls
- Supplier Performance
- Reports & Analytics
- Settings
"""

from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, Response
from functools import wraps

from procurement_models import (
    initialize_procurement_tables,
    get_suppliers, get_supplier_by_id, create_supplier, update_supplier,
    get_requisitions, get_requisition_by_id, create_requisition, update_requisition_status,
    get_rfqs, get_rfq_by_id, create_rfq,
    get_quotations, get_quotation_by_id, create_quotation,
    get_purchase_orders, get_purchase_order_by_id, create_purchase_order,
    get_claims, create_claim, create_return,
    get_contracts, create_contract,
    get_procurement_dashboard_stats, get_supplier_performance_summary,
    get_procurement_alerts, create_procurement_alert,
    get_procurement_setting, set_procurement_setting, get_all_procurement_settings,
    log_procurement_audit
)


def register_procurement_routes(app, get_db):
    """Register all Procurement routes with the Flask app."""

    # ============================================================
    # DECORATORS & HELPERS
    # ============================================================

    def procurement_permission_required(module: str, resource: str, action: str):
        """Decorator to check procurement permissions using central permissions system."""
        from permissions import user_has_permission
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if 'user_id' not in session:
                    return redirect(url_for('login'))

                user_id = session['user_id']
                if not user_has_permission(user_id, module, resource, action):
                    flash(f"Access Denied. You don't have permission to {action} {resource}.", "error")
                    return redirect(url_for('procurement_dashboard'))
                return f(*args, **kwargs)
            return decorated_function
        return decorator

    def get_current_user():
        """Get current user info from session."""
        return {
            'id': session.get('user_id'),
            'username': session.get('username'),
            'role_id': session.get('role_id'),
            'company_id': session.get('company_id'),
            'warehouse_id': session.get('warehouse_id')
        }

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

    def parse_datetime(dt_str, default=None):
        """Parse datetime string safely."""
        if not dt_str:
            return default
        try:
            return datetime.strptime(str(dt_str), '%Y-%m-%d %H:%M:%S')
        except:
            try:
                return datetime.strptime(str(dt_str), '%Y-%m-%dT%H:%M')
            except:
                try:
                    return datetime.strptime(str(dt_str), '%d/%m/%Y %H:%M')
                except:
                    return default

    # Initialize procurement tables on first request
    @app.before_request
    def init_procurement():
        if not hasattr(app, '_procurement_initialized'):
            initialize_procurement_tables()
            app._procurement_initialized = True

    # ============================================================
    # PROCUREMENT DASHBOARD
    # ============================================================

    @app.route('/procurement')
    @app.route('/procurement/dashboard')
    @procurement_permission_required('procurement', 'dashboard', 'view')
    def procurement_dashboard():
        """Main Procurement Dashboard."""
        user = get_current_user()
        stats = get_procurement_dashboard_stats(user['id'])
        alerts = get_procurement_alerts({'is_read': False})[:10]

        # Recent activity
        recent_pos = get_purchase_orders(page=1, per_page=5)
        recent_requisitions = get_requisitions(page=1, per_page=5)

        db = get_db()
        user_prefs = db.execute(
            "SELECT * FROM user_preferences WHERE user_id = ?", (session['user_id'],)
        ).fetchone()

        return render_template('procurement/dashboard.html',
            stats=stats,
            alerts=alerts,
            recent_pos=recent_pos['items'],
            recent_requisitions=recent_requisitions['items'],
            current_user=user,
            user_prefs=dict(user_prefs) if user_prefs else None,
            page_title='Procurement Dashboard'
        )

    # ============================================================
    # SUPPLIER MANAGEMENT
    # ============================================================

    @app.route('/procurement/suppliers')
    @procurement_permission_required('procurement', 'suppliers', 'view')
    def procurement_suppliers():
        """Supplier list page."""
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        supplier_type = request.args.get('type', '')
        country = request.args.get('country', '')
        is_preferred = request.args.get('preferred', '')

        filters = {}
        if search:
            filters['search'] = search
        if status:
            filters['status'] = status
        if supplier_type:
            filters['supplier_type'] = supplier_type
        if country:
            filters['country'] = country
        if is_preferred:
            filters['is_preferred'] = True

        suppliers = get_suppliers(filters, page=page)

        # Get filter options
        db = get_db()
        countries = db.execute("SELECT DISTINCT country FROM suppliers WHERE country IS NOT NULL AND country != '' ORDER BY country").fetchall()
        supplier_types = ['LOCAL', 'INTERNATIONAL', 'STRATEGIC', 'EMERGENCY']

        return render_template('procurement/suppliers/list.html',
            suppliers=suppliers['items'],
            total=suppliers['total'],
            page=page,
            pages=suppliers['pages'],
            filters=filters,
            countries=[c['country'] for c in countries],
            supplier_types=supplier_types,
            page_title='Suppliers'
        )

    @app.route('/procurement/suppliers/new', methods=['GET', 'POST'])
    @procurement_permission_required('procurement', 'suppliers', 'create')
    def procurement_suppliers_new():
        """Create new supplier."""
        if request.method == 'POST':
            data = {
                'name': request.form.get('name'),
                'code': request.form.get('code'),
                'supplier_type': request.form.get('supplier_type', 'LOCAL'),
                'trade_name': request.form.get('trade_name'),
                'contact_person': request.form.get('contact_person'),
                'email': request.form.get('email'),
                'phone': request.form.get('phone'),
                'whatsapp': request.form.get('whatsapp'),
                'address': request.form.get('address'),
                'city': request.form.get('city'),
                'country': request.form.get('country'),
                'region': request.form.get('region'),
                'payment_terms': request.form.get('payment_terms'),
                'lead_time': request.form.get('lead_time'),
                'currency': request.form.get('currency', 'AED'),
                'rating': request.form.get('rating', 0),
                'status': request.form.get('status', 'Active'),
                'notes': request.form.get('notes'),
                'website': request.form.get('website'),
                'tax_number': request.form.get('tax_number'),
                'vat_number': request.form.get('vat_number'),
                'bank_name': request.form.get('bank_name'),
                'bank_account': request.form.get('bank_account'),
                'swift_code': request.form.get('swift_code'),
                'iban': request.form.get('iban'),
                'moq': request.form.get('moq', 1),
                'order_multiple': request.form.get('order_multiple', 1),
                'lead_time_standard': request.form.get('lead_time_standard'),
                'is_preferred': 1 if request.form.get('is_preferred') else 0,
                'is_strategic': 1 if request.form.get('is_strategic') else 0,
                'is_emergency': 1 if request.form.get('is_emergency') else 0,
                'risk_level': request.form.get('risk_level', 'LOW'),
                'category': request.form.get('category'),
                'subcategory': request.form.get('subcategory'),
                'related_brands': request.form.get('related_brands'),
                'related_item_groups': request.form.get('related_item_groups'),
            }

            if not data['name'] or not data['code']:
                flash('Name and Code are required', 'error')
                return redirect(url_for('procurement_suppliers_new'))

            user = get_current_user()
            supplier_id = create_supplier(data, user['id'])

            flash(f'Supplier created successfully: {data["code"]}', 'success')
            return redirect(url_for('procurement_suppliers_view', supplier_id=supplier_id))

        return render_template('procurement/suppliers/form.html',
            supplier=None,
            is_new=True,
            page_title='New Supplier'
        )

    @app.route('/procurement/suppliers/<int:supplier_id>')
    @procurement_permission_required('procurement', 'suppliers', 'view')
    def procurement_suppliers_view(supplier_id):
        """View supplier details."""
        supplier = get_supplier_by_id(supplier_id)
        if not supplier:
            flash('Supplier not found', 'error')
            return redirect(url_for('procurement_suppliers'))

        db = get_db()

        return render_template('procurement/suppliers/view.html',
            supplier=supplier,
            page_title=f'Supplier: {supplier["name"]}'
        )

    @app.route('/procurement/suppliers/<int:supplier_id>/edit', methods=['GET', 'POST'])
    @procurement_permission_required('procurement', 'suppliers', 'edit')
    def procurement_suppliers_edit(supplier_id):
        """Edit supplier."""
        if request.method == 'POST':
            data = {
                'name': request.form.get('name'),
                'code': request.form.get('code'),
                'supplier_type': request.form.get('supplier_type', 'LOCAL'),
                'trade_name': request.form.get('trade_name'),
                'contact_person': request.form.get('contact_person'),
                'email': request.form.get('email'),
                'phone': request.form.get('phone'),
                'whatsapp': request.form.get('whatsapp'),
                'address': request.form.get('address'),
                'city': request.form.get('city'),
                'country': request.form.get('country'),
                'region': request.form.get('region'),
                'payment_terms': request.form.get('payment_terms'),
                'lead_time': request.form.get('lead_time'),
                'currency': request.form.get('currency', 'AED'),
                'rating': request.form.get('rating', 0),
                'status': request.form.get('status', 'Active'),
                'notes': request.form.get('notes'),
                'website': request.form.get('website'),
                'tax_number': request.form.get('tax_number'),
                'vat_number': request.form.get('vat_number'),
                'bank_name': request.form.get('bank_name'),
                'bank_account': request.form.get('bank_account'),
                'swift_code': request.form.get('swift_code'),
                'iban': request.form.get('iban'),
                'moq': request.form.get('moq', 1),
                'order_multiple': request.form.get('order_multiple', 1),
                'lead_time_standard': request.form.get('lead_time_standard'),
                'is_preferred': 1 if request.form.get('is_preferred') else 0,
                'is_strategic': 1 if request.form.get('is_strategic') else 0,
                'is_emergency': 1 if request.form.get('is_emergency') else 0,
                'is_blacklisted': 1 if request.form.get('is_blacklisted') else 0,
                'risk_level': request.form.get('risk_level', 'LOW'),
                'category': request.form.get('category'),
                'subcategory': request.form.get('subcategory'),
                'related_brands': request.form.get('related_brands'),
                'related_item_groups': request.form.get('related_item_groups'),
            }

            user = get_current_user()
            update_supplier(supplier_id, data, user['id'])

            flash('Supplier updated successfully', 'success')
            return redirect(url_for('procurement_suppliers_view', supplier_id=supplier_id))

        supplier = get_supplier_by_id(supplier_id)
        if not supplier:
            flash('Supplier not found', 'error')
            return redirect(url_for('procurement_suppliers'))

        return render_template('procurement/suppliers/form.html',
            supplier=supplier,
            is_new=False,
            page_title=f'Edit Supplier: {supplier["name"]}'
        )

    # ============================================================
    # PURCHASE REQUISITIONS
    # ============================================================

    @app.route('/procurement/requisitions')
    @procurement_permission_required('procurement', 'requisitions', 'view')
    def procurement_requisitions():
        """Requisition list page."""
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        priority = request.args.get('priority', '')
        urgency = request.args.get('urgency', '')

        filters = {}
        if search:
            filters['search'] = search
        if status:
            filters['status'] = status
        if priority:
            filters['priority'] = priority
        if urgency:
            filters['urgency'] = urgency

        requisitions = get_requisitions(filters, page=page)

        return render_template('procurement/requisitions/list.html',
            requisitions=requisitions['items'],
            total=requisitions['total'],
            page=page,
            pages=requisitions['pages'],
            filters=filters,
            page_title='Purchase Requisitions'
        )

    @app.route('/procurement/requisitions/new', methods=['GET', 'POST'])
    @procurement_permission_required('procurement', 'requisitions', 'create')
    def procurement_requisitions_new():
        """Create new requisition."""
        if request.method == 'POST':
            user = get_current_user()

            # Parse lines from form
            lines = []
            item_codes = request.form.getlist('item_code')
            for i, code in enumerate(item_codes):
                if code:
                    lines.append({
                        'item_id': request.form.getlist('item_id')[i] if i < len(request.form.getlist('item_id')) else None,
                        'item_code': code,
                        'item_name': request.form.getlist('item_name')[i] if i < len(request.form.getlist('item_name')) else '',
                        'brand': request.form.getlist('brand')[i] if i < len(request.form.getlist('brand')) else '',
                        'part_number': request.form.getlist('part_number')[i] if i < len(request.form.getlist('part_number')) else '',
                        'requested_qty': request.form.getlist('requested_qty')[i] if i < len(request.form.getlist('requested_qty')) else 0,
                        'unit_of_measure': request.form.getlist('unit_of_measure')[i] if i < len(request.form.getlist('unit_of_measure')) else 'PCS',
                        'required_date': request.form.getlist('required_date')[i] if i < len(request.form.getlist('required_date')) else '',
                        'estimated_unit_price': request.form.getlist('estimated_unit_price')[i] if i < len(request.form.getlist('estimated_unit_price')) else 0,
                        'preferred_supplier_id': request.form.getlist('preferred_supplier_id')[i] if i < len(request.form.getlist('preferred_supplier_id')) else None,
                        'preferred_supplier_name': request.form.getlist('preferred_supplier_name')[i] if i < len(request.form.getlist('preferred_supplier_name')) else '',
                        'purpose': request.form.getlist('purpose')[i] if i < len(request.form.getlist('purpose')) else '',
                        'remarks': request.form.getlist('remarks')[i] if i < len(request.form.getlist('remarks')) else '',
                    })

            if not lines:
                flash('At least one line item is required', 'error')
                return redirect(url_for('procurement_requisitions_new'))

            data = {
                'requisition_date': request.form.get('requisition_date', datetime.now().strftime('%Y-%m-%d')),
                'requester_id': user['id'],
                'requester_name': user['username'],
                'department': request.form.get('department'),
                'company_id': request.form.get('company_id'),
                'warehouse_id': request.form.get('warehouse_id'),
                'source_type': request.form.get('source_type', 'MANUAL'),
                'priority': request.form.get('priority', 'MEDIUM'),
                'urgency': request.form.get('urgency', 'NORMAL'),
                'notes': request.form.get('notes'),
                'internal_notes': request.form.get('internal_notes'),
            }

            requisition_id = create_requisition(data, lines, user['id'])

            flash(f'Requisition created successfully', 'success')
            return redirect(url_for('procurement_requisitions_view', requisition_id=requisition_id))

        db = get_db()
        companies = db.execute("SELECT * FROM companies ORDER BY name").fetchall()
        warehouses = db.execute("SELECT * FROM warehouses ORDER BY name").fetchall()
        suppliers = get_suppliers({'status': 'Active'}, per_page=1000)['items']

        return render_template('procurement/requisitions/form.html',
            requisition=None,
            is_new=True,
            companies=companies,
            warehouses=warehouses,
            suppliers=suppliers,
            page_title='New Requisition'
        )

    @app.route('/procurement/requisitions/<int:requisition_id>')
    @procurement_permission_required('procurement', 'requisitions', 'view')
    def procurement_requisitions_view(requisition_id):
        """View requisition details."""
        requisition = get_requisition_by_id(requisition_id)
        if not requisition:
            flash('Requisition not found', 'error')
            return redirect(url_for('procurement_requisitions'))

        return render_template('procurement/requisitions/view.html',
            requisition=requisition,
            page_title=f'Requisition: {requisition["requisition_number"]}'
        )

    @app.route('/procurement/requisitions/<int:requisition_id>/status', methods=['POST'])
    @procurement_permission_required('procurement', 'requisitions', 'edit')
    def procurement_requisitions_status(requisition_id):
        """Update requisition status."""
        new_status = request.form.get('status')
        rejection_reason = request.form.get('rejection_reason')
        user = get_current_user()

        if new_status:
            update_requisition_status(requisition_id, new_status, user['id'], rejection_reason)
            flash(f'Requisition status updated to {new_status}', 'success')

        return redirect(url_for('procurement_requisitions_view', requisition_id=requisition_id))

    @app.route('/procurement/requisitions/<int:requisition_id>/convert-to-rfq', methods=['POST'])
    @procurement_permission_required('procurement', 'requisitions', 'convert')
    def procurement_requisitions_to_rfq(requisition_id):
        """Convert requisition to RFQ."""
        requisition = get_requisition_by_id(requisition_id)
        if not requisition:
            flash('Requisition not found', 'error')
            return redirect(url_for('procurement_requisitions'))

        # Redirect to RFQ creation with pre-filled data
        return redirect(url_for('procurement_rfqs_new', requisition_id=requisition_id))

    # ============================================================
    # RFQ MANAGEMENT
    # ============================================================

    @app.route('/procurement/rfqs')
    @procurement_permission_required('procurement', 'rfqs', 'view')
    def procurement_rfqs():
        """RFQ list page."""
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', '')

        filters = {}
        if search:
            filters['search'] = search
        if status:
            filters['status'] = status

        rfqs = get_rfqs(filters, page=page)

        return render_template('procurement/rfqs/list.html',
            rfqs=rfqs['items'],
            total=rfqs['total'],
            page=page,
            pages=rfqs['pages'],
            filters=filters,
            page_title='RFQ / Supplier Inquiries'
        )

    @app.route('/procurement/rfqs/new', methods=['GET', 'POST'])
    @procurement_permission_required('procurement', 'rfqs', 'create')
    def procurement_rfqs_new():
        """Create new RFQ."""
        # Pre-fill from requisition if provided
        prefill_data = None
        requisition_id = request.args.get('requisition_id', type=int)
        if requisition_id:
            prefill_data = get_requisition_by_id(requisition_id)

        if request.method == 'POST':
            user = get_current_user()

            # Parse lines
            lines = []
            item_codes = request.form.getlist('item_code')
            for i, code in enumerate(item_codes):
                if code:
                    lines.append({
                        'item_id': request.form.getlist('item_id')[i] if i < len(request.form.getlist('item_id')) else None,
                        'item_code': code,
                        'item_name': request.form.getlist('item_name')[i] if i < len(request.form.getlist('item_name')) else '',
                        'brand': request.form.getlist('brand')[i] if i < len(request.form.getlist('brand')) else '',
                        'part_number': request.form.getlist('part_number')[i] if i < len(request.form.getlist('part_number')) else '',
                        'requested_qty': request.form.getlist('requested_qty')[i] if i < len(request.form.getlist('requested_qty')) else 0,
                        'unit_of_measure': request.form.getlist('unit_of_measure')[i] if i < len(request.form.getlist('unit_of_measure')) else 'PCS',
                        'specifications': request.form.getlist('specifications')[i] if i < len(request.form.getlist('specifications')) else '',
                        'target_price': request.form.getlist('target_price')[i] if i < len(request.form.getlist('target_price')) else None,
                    })

            # Parse supplier IDs
            supplier_ids = [int(sid) for sid in request.form.getlist('supplier_ids') if sid]

            if not lines:
                flash('At least one line item is required', 'error')
                return redirect(url_for('procurement_rfqs_new'))

            if not supplier_ids:
                flash('At least one supplier is required', 'error')
                return redirect(url_for('procurement_rfqs_new'))

            data = {
                'rfq_date': request.form.get('rfq_date', datetime.now().strftime('%Y-%m-%d')),
                'buyer_id': user['id'],
                'buyer_name': user['username'],
                'company_id': request.form.get('company_id'),
                'warehouse_id': request.form.get('warehouse_id'),
                'source_requisition_id': request.form.get('source_requisition_id'),
                'currency': request.form.get('currency', 'AED'),
                'response_due_date': request.form.get('response_due_date'),
                'requested_delivery_date': request.form.get('requested_delivery_date'),
                'incoterm': request.form.get('incoterm'),
                'payment_terms': request.form.get('payment_terms'),
                'shipping_method': request.form.get('shipping_method'),
                'delivery_address': request.form.get('delivery_address'),
                'urgency': request.form.get('urgency', 'NORMAL'),
                'notes': request.form.get('notes'),
                'internal_notes': request.form.get('internal_notes'),
            }

            rfq_id = create_rfq(data, lines, supplier_ids, user['id'])

            flash(f'RFQ created successfully', 'success')
            return redirect(url_for('procurement_rfqs_view', rfq_id=rfq_id))

        db = get_db()
        companies = db.execute("SELECT * FROM companies ORDER BY name").fetchall()
        warehouses = db.execute("SELECT * FROM warehouses ORDER BY name").fetchall()
        suppliers = get_suppliers({'status': 'Active'}, per_page=1000)['items']

        return render_template('procurement/rfqs/form.html',
            rfq=None,
            prefill=prefill_data,
            is_new=True,
            companies=companies,
            warehouses=warehouses,
            suppliers=suppliers,
            page_title='New RFQ'
        )

    @app.route('/procurement/rfqs/<int:rfq_id>')
    @procurement_permission_required('procurement', 'rfqs', 'view')
    def procurement_rfqs_view(rfq_id):
        """View RFQ details."""
        rfq = get_rfq_by_id(rfq_id)
        if not rfq:
            flash('RFQ not found', 'error')
            return redirect(url_for('procurement_rfqs'))

        return render_template('procurement/rfqs/view.html',
            rfq=rfq,
            page_title=f'RFQ: {rfq["rfq_number"]}'
        )

    @app.route('/procurement/rfqs/<int:rfq_id>/send', methods=['POST'])
    @procurement_permission_required('procurement', 'rfqs', 'send')
    def procurement_rfqs_send(rfq_id):
        """Send RFQ to suppliers."""
        db = get_db()
        db.execute("UPDATE procurement_rfqs SET status = 'SENT', updated_at = datetime('now') WHERE id = ?", (rfq_id,))
        db.commit()

        flash('RFQ sent to suppliers', 'success')
        return redirect(url_for('procurement_rfqs_view', rfq_id=rfq_id))

    # ============================================================
    # QUOTATIONS
    # ============================================================

    @app.route('/procurement/quotations')
    @procurement_permission_required('procurement', 'quotations', 'view')
    def procurement_quotations():
        """Quotation list page."""
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        rfq_id = request.args.get('rfq_id', type=int)
        supplier_id = request.args.get('supplier_id', type=int)

        filters = {}
        if search:
            filters['search'] = search
        if status:
            filters['status'] = status
        if rfq_id:
            filters['rfq_id'] = rfq_id
        if supplier_id:
            filters['supplier_id'] = supplier_id

        quotations = get_quotations(filters, page=page)

        return render_template('procurement/quotations/list.html',
            quotations=quotations['items'],
            total=quotations['total'],
            page=page,
            pages=quotations['pages'],
            filters=filters,
            page_title='Supplier Quotations'
        )

    @app.route('/procurement/quotations/new', methods=['GET', 'POST'])
    @procurement_permission_required('procurement', 'quotations', 'create')
    def procurement_quotations_new():
        """Create new quotation."""
        rfq_id = request.args.get('rfq_id', type=int)
        prefill_data = None
        if rfq_id:
            prefill_data = get_rfq_by_id(rfq_id)

        if request.method == 'POST':
            user = get_current_user()

            # Parse lines
            lines = []
            item_codes = request.form.getlist('item_code')
            for i, code in enumerate(item_codes):
                if code:
                    lines.append({
                        'item_id': request.form.getlist('item_id')[i] if i < len(request.form.getlist('item_id')) else None,
                        'item_code': code,
                        'item_name': request.form.getlist('item_name')[i] if i < len(request.form.getlist('item_name')) else '',
                        'brand': request.form.getlist('brand')[i] if i < len(request.form.getlist('brand')) else '',
                        'part_number': request.form.getlist('part_number')[i] if i < len(request.form.getlist('part_number')) else '',
                        'quoted_qty': request.form.getlist('quoted_qty')[i] if i < len(request.form.getlist('quoted_qty')) else 0,
                        'unit_of_measure': request.form.getlist('unit_of_measure')[i] if i < len(request.form.getlist('unit_of_measure')) else 'PCS',
                        'unit_price': request.form.getlist('unit_price')[i] if i < len(request.form.getlist('unit_price')) else 0,
                        'discount_percent': request.form.getlist('discount_percent')[i] if i < len(request.form.getlist('discount_percent')) else 0,
                        'requested_qty': request.form.getlist('requested_qty')[i] if i < len(request.form.getlist('requested_qty')) else 0,
                    })

            if not lines:
                flash('At least one line item is required', 'error')
                return redirect(url_for('procurement_quotations_new'))

            data = {
                'rfq_id': request.form.get('rfq_id'),
                'supplier_id': request.form.get('supplier_id'),
                'supplier_name': request.form.get('supplier_name'),
                'quotation_date': request.form.get('quotation_date', datetime.now().strftime('%Y-%m-%d')),
                'validity_date': request.form.get('validity_date'),
                'currency': request.form.get('currency', 'AED'),
                'incoterm': request.form.get('incoterm'),
                'payment_terms': request.form.get('payment_terms'),
                'lead_time_days': request.form.get('lead_time_days'),
                'moq': request.form.get('moq', 1),
                'order_multiple': request.form.get('order_multiple', 1),
                'freight_cost': request.form.get('freight_cost', 0),
                'other_charges': request.form.get('other_charges', 0),
                'notes': request.form.get('notes'),
                'internal_notes': request.form.get('internal_notes'),
            }

            quotation_id = create_quotation(data, lines, user['id'])

            flash(f'Quotation created successfully', 'success')
            return redirect(url_for('procurement_quotations_view', quotation_id=quotation_id))

        db = get_db()
        suppliers = get_suppliers({'status': 'Active'}, per_page=1000)['items']

        return render_template('procurement/quotations/form.html',
            quotation=None,
            prefill=prefill_data,
            is_new=True,
            suppliers=suppliers,
            page_title='New Quotation'
        )

    @app.route('/procurement/quotations/<int:quotation_id>')
    @procurement_permission_required('procurement', 'quotations', 'view')
    def procurement_quotations_view(quotation_id):
        """View quotation details."""
        quotation = get_quotation_by_id(quotation_id)
        if not quotation:
            flash('Quotation not found', 'error')
            return redirect(url_for('procurement_quotations'))

        return render_template('procurement/quotations/view.html',
            quotation=quotation,
            page_title=f'Quotation: {quotation["quotation_number"]}'
        )

    @app.route('/procurement/quotations/compare/<int:rfq_id>')
    @procurement_permission_required('procurement', 'quotations', 'compare')
    def procurement_quotations_compare(rfq_id):
        """Compare quotations for an RFQ."""
        rfq = get_rfq_by_id(rfq_id)
        if not rfq:
            flash('RFQ not found', 'error')
            return redirect(url_for('procurement_rfqs'))

        return render_template('procurement/quotations/compare.html',
            rfq=rfq,
            quotations=rfq['quotations'],
            page_title=f'Quotation Comparison: {rfq["rfq_number"]}'
        )

    # ============================================================
    # PURCHASE ORDERS
    # ============================================================

    @app.route('/procurement/orders')
    @procurement_permission_required('procurement', 'orders', 'view')
    def procurement_orders():
        """Purchase order list page."""
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        po_type = request.args.get('po_type', '')
        supplier_id = request.args.get('supplier_id', type=int)
        is_overdue = request.args.get('is_overdue', '')

        filters = {}
        if search:
            filters['search'] = search
        if status:
            filters['status'] = status
        if po_type:
            filters['po_type'] = po_type
        if supplier_id:
            filters['supplier_id'] = supplier_id
        if is_overdue:
            filters['is_overdue'] = True

        orders = get_purchase_orders(filters, page=page)

        return render_template('procurement/orders/list.html',
            orders=orders['items'],
            total=orders['total'],
            page=page,
            pages=orders['pages'],
            filters=filters,
            page_title='Purchase Orders'
        )

    @app.route('/procurement/orders/new', methods=['GET', 'POST'])
    @procurement_permission_required('procurement', 'orders', 'create')
    def procurement_orders_new():
        """Create new purchase order."""
        # Pre-fill from quotation or vendor selection
        prefill_data = None
        quotation_id = request.args.get('quotation_id', type=int)
        vendor_selection_id = request.args.get('vendor_selection_id', type=int)

        if request.method == 'POST':
            user = get_current_user()

            # Parse lines
            lines = []
            item_codes = request.form.getlist('item_code')
            for i, code in enumerate(item_codes):
                if code:
                    lines.append({
                        'item_id': request.form.getlist('item_id')[i] if i < len(request.form.getlist('item_id')) else None,
                        'item_code': code,
                        'item_name': request.form.getlist('item_name')[i] if i < len(request.form.getlist('item_name')) else '',
                        'brand': request.form.getlist('brand')[i] if i < len(request.form.getlist('brand')) else '',
                        'part_number': request.form.getlist('part_number')[i] if i < len(request.form.getlist('part_number')) else '',
                        'ordered_qty': request.form.getlist('ordered_qty')[i] if i < len(request.form.getlist('ordered_qty')) else 0,
                        'unit_of_measure': request.form.getlist('unit_of_measure')[i] if i < len(request.form.getlist('unit_of_measure')) else 'PCS',
                        'unit_price': request.form.getlist('unit_price')[i] if i < len(request.form.getlist('unit_price')) else 0,
                        'discount_percent': request.form.getlist('discount_percent')[i] if i < len(request.form.getlist('discount_percent')) else 0,
                        'expected_delivery_date': request.form.getlist('expected_delivery_date')[i] if i < len(request.form.getlist('expected_delivery_date')) else '',
                        'remarks': request.form.getlist('remarks')[i] if i < len(request.form.getlist('remarks')) else '',
                    })

            if not lines:
                flash('At least one line item is required', 'error')
                return redirect(url_for('procurement_orders_new'))

            data = {
                'po_date': request.form.get('po_date', datetime.now().strftime('%Y-%m-%d')),
                'po_type': request.form.get('po_type', 'STANDARD'),
                'supplier_id': request.form.get('supplier_id'),
                'supplier_name': request.form.get('supplier_name'),
                'buyer_id': user['id'],
                'buyer_name': user['username'],
                'company_id': request.form.get('company_id'),
                'branch_id': request.form.get('branch_id'),
                'warehouse_id': request.form.get('warehouse_id'),
                'source_requisition_id': request.form.get('source_requisition_id'),
                'source_rfq_id': request.form.get('source_rfq_id'),
                'source_quotation_id': request.form.get('source_quotation_id'),
                'currency': request.form.get('currency', 'AED'),
                'payment_terms': request.form.get('payment_terms'),
                'incoterm': request.form.get('incoterm'),
                'shipment_method': request.form.get('shipment_method'),
                'delivery_address': request.form.get('delivery_address'),
                'expected_ship_date': request.form.get('expected_ship_date'),
                'expected_delivery_date': request.form.get('expected_delivery_date'),
                'discount_amount': request.form.get('discount_amount', 0),
                'freight_cost': request.form.get('freight_cost', 0),
                'other_charges': request.form.get('other_charges', 0),
                'notes': request.form.get('notes'),
                'internal_notes': request.form.get('internal_notes'),
                'terms_conditions': request.form.get('terms_conditions'),
            }

            po_id = create_purchase_order(data, lines, user['id'])

            flash(f'Purchase Order created successfully', 'success')
            return redirect(url_for('procurement_orders_view', po_id=po_id))

        db = get_db()
        companies = db.execute("SELECT * FROM companies ORDER BY name").fetchall()
        warehouses = db.execute("SELECT * FROM warehouses ORDER BY name").fetchall()
        suppliers = get_suppliers({'status': 'Active'}, per_page=1000)['items']

        return render_template('procurement/orders/form.html',
            order=None,
            prefill=prefill_data,
            is_new=True,
            companies=companies,
            warehouses=warehouses,
            suppliers=suppliers,
            page_title='New Purchase Order'
        )

    @app.route('/procurement/orders/<int:po_id>')
    @procurement_permission_required('procurement', 'orders', 'view')
    def procurement_orders_view(po_id):
        """View purchase order details."""
        order = get_purchase_order_by_id(po_id)
        if not order:
            flash('Purchase Order not found', 'error')
            return redirect(url_for('procurement_orders'))

        return render_template('procurement/orders/view.html',
            order=order,
            page_title=f'PO: {order["po_number"]}'
        )

    @app.route('/procurement/orders/<int:po_id>/approve', methods=['POST'])
    @procurement_permission_required('procurement', 'orders', 'approve')
    def procurement_orders_approve(po_id):
        """Approve a purchase order."""
        user = get_current_user()
        db = get_db()
        db.execute("""
            UPDATE procurement_purchase_orders
            SET approval_status = 'APPROVED', approved_by = ?, approved_at = datetime('now')
            WHERE id = ?
        """, (user['id'], po_id))
        db.execute("""
            INSERT INTO procurement_po_history (po_id, action_type, changed_by, change_reason)
            VALUES (?, 'APPROVED', ?, 'Approved by buyer')
        """, (po_id, user['id']))
        db.commit()

        flash('Purchase Order approved', 'success')
        return redirect(url_for('procurement_orders_view', po_id=po_id))

    @app.route('/procurement/orders/<int:po_id>/status', methods=['POST'])
    @procurement_permission_required('procurement', 'orders', 'edit')
    def procurement_orders_status(po_id):
        """Update purchase order status."""
        new_status = request.form.get('status')
        user = get_current_user()

        if new_status:
            db = get_db()
            db.execute("""
                UPDATE procurement_purchase_orders
                SET status = ?, updated_at = datetime('now')
                WHERE id = ?
            """, (new_status, po_id))
            db.execute("""
                INSERT INTO procurement_po_history (po_id, action_type, field_name, old_value, new_value, changed_by)
                VALUES (?, 'STATUS_CHANGE', 'status', (SELECT status FROM procurement_purchase_orders WHERE id = ?), ?, ?)
            """, (po_id, po_id, new_status, user['id']))
            db.commit()

            flash(f'Purchase Order status updated to {new_status}', 'success')

        return redirect(url_for('procurement_orders_view', po_id=po_id))

    # ============================================================
    # SHIPMENTS
    # ============================================================

    @app.route('/procurement/shipments')
    @procurement_permission_required('procurement', 'shipments', 'view')
    def procurement_shipments():
        """Shipment tracking list."""
        db = get_db()
        page = request.args.get('page', 1, type=int)
        status = request.args.get('status', '')

        where_clause = "1=1"
        params = []

        if status:
            where_clause += " AND ps.status = ?"
            params.append(status)

        count_sql = f"SELECT COUNT(*) as cnt FROM procurement_shipments ps WHERE {where_clause}"
        total = db.execute(count_sql, params).fetchone()['cnt']

        offset = (page - 1) * 50
        sql = f"""
            SELECT ps.*, ppo.po_number, s.name as supplier_name
            FROM procurement_shipments ps
            LEFT JOIN procurement_purchase_orders ppo ON ps.po_id = ppo.id
            LEFT JOIN suppliers s ON ps.supplier_id = s.id
            WHERE {where_clause}
            ORDER BY ps.created_at DESC
            LIMIT 50 OFFSET ?
        """
        params.append(offset)

        shipments = db.execute(sql, params).fetchall()

        return render_template('procurement/shipments/list.html',
            shipments=[dict(s) for s in shipments],
            total=total,
            page=page,
            filters={'status': status},
            page_title='Shipment Tracking'
        )

    @app.route('/procurement/shipments/<int:shipment_id>')
    @procurement_permission_required('procurement', 'shipments', 'view')
    def procurement_shipments_view(shipment_id):
        """View shipment details."""
        db = get_db()
        shipment = db.execute("""
            SELECT ps.*, ppo.po_number, s.name as supplier_name
            FROM procurement_shipments ps
            LEFT JOIN procurement_purchase_orders ppo ON ps.po_id = ppo.id
            LEFT JOIN suppliers s ON ps.supplier_id = s.id
            WHERE ps.id = ?
        """, (shipment_id,)).fetchone()

        if not shipment:
            flash('Shipment not found', 'error')
            return redirect(url_for('procurement_shipments'))

        return render_template('procurement/shipments/view.html',
            shipment=dict(shipment),
            page_title=f'Shipment: {shipment["shipment_number"]}'
        )

    # ============================================================
    # RECEIVING
    # ============================================================

    @app.route('/procurement/receiving')
    @procurement_permission_required('procurement', 'receiving', 'view')
    def procurement_receiving():
        """Receiving coordination page."""
        db = get_db()
        today = datetime.now().strftime('%Y-%m-%d')

        # Expected receipts
        expected_receipts = db.execute("""
            SELECT per.*, ppo.po_number, ppo.supplier_name, w.name as warehouse_name
            FROM procurement_expected_receipts per
            LEFT JOIN procurement_purchase_orders ppo ON per.po_id = ppo.id
            LEFT JOIN warehouses w ON per.warehouse_id = w.id
            WHERE per.status = 'PENDING'
            ORDER BY per.expected_date ASC
            LIMIT 100
        """).fetchall()

        # Overdue
        overdue_receipts = db.execute("""
            SELECT per.*, ppo.po_number, ppo.supplier_name, w.name as warehouse_name
            FROM procurement_expected_receipts per
            LEFT JOIN procurement_purchase_orders ppo ON per.po_id = ppo.id
            LEFT JOIN warehouses w ON per.warehouse_id = w.id
            WHERE per.expected_date < ? AND per.status = 'PENDING'
            ORDER BY per.expected_date ASC
        """, (today,)).fetchall()

        # Recent receiving
        recent_receiving = db.execute("""
            SELECT prr.*, ppo.po_number, ppo.supplier_name
            FROM procurement_receiving prr
            LEFT JOIN procurement_purchase_orders ppo ON prr.po_id = ppo.id
            ORDER BY prr.created_at DESC
            LIMIT 20
        """).fetchall()

        return render_template('procurement/receiving/list.html',
            expected_receipts=[dict(e) for e in expected_receipts],
            overdue_receipts=[dict(o) for o in overdue_receipts],
            recent_receiving=[dict(r) for r in recent_receiving],
            page_title='Receiving Coordination'
        )

    @app.route('/procurement/receiving/<int:receipt_id>')
    @procurement_permission_required('procurement', 'receiving', 'view')
    def procurement_receiving_view(receipt_id):
        """View receiving details."""
        db = get_db()
        receipt = db.execute("""
            SELECT prr.*, ppo.po_number, ppo.supplier_name, w.name as warehouse_name
            FROM procurement_receiving prr
            LEFT JOIN procurement_purchase_orders ppo ON prr.po_id = ppo.id
            LEFT JOIN warehouses w ON prr.warehouse_id = w.id
            WHERE prr.id = ?
        """, (receipt_id,)).fetchone()

        if not receipt:
            flash('Receipt not found', 'error')
            return redirect(url_for('procurement_receiving'))

        lines = db.execute("""
            SELECT * FROM procurement_receiving_lines WHERE receiving_id = ?
        """, (receipt_id,)).fetchall()

        return render_template('procurement/receiving/view.html',
            receipt=dict(receipt),
            lines=[dict(l) for l in lines],
            page_title=f'Receipt: {receipt["receipt_number"]}'
        )

    # ============================================================
    # CLAIMS & RETURNS
    # ============================================================

    @app.route('/procurement/claims')
    @procurement_permission_required('procurement', 'claims', 'view')
    def procurement_claims():
        """Claims list page."""
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        claim_type = request.args.get('claim_type', '')

        filters = {}
        if search:
            filters['search'] = search
        if status:
            filters['status'] = status
        if claim_type:
            filters['claim_type'] = claim_type

        claims = get_claims(filters, page=page)

        return render_template('procurement/claims/list.html',
            claims=claims['items'],
            total=claims['total'],
            page=page,
            pages=claims['pages'],
            filters=filters,
            page_title='Claims & Discrepancies'
        )

    @app.route('/procurement/claims/new', methods=['GET', 'POST'])
    @procurement_permission_required('procurement', 'claims', 'create')
    def procurement_claims_new():
        """Create new claim."""
        if request.method == 'POST':
            user = get_current_user()

            data = {
                'claim_date': request.form.get('claim_date', datetime.now().strftime('%Y-%m-%d')),
                'claim_type': request.form.get('claim_type', 'QUALITY'),
                'po_id': request.form.get('po_id'),
                'po_number': request.form.get('po_number'),
                'receiving_id': request.form.get('receiving_id'),
                'discrepancy_id': request.form.get('discrepancy_id'),
                'supplier_id': request.form.get('supplier_id'),
                'supplier_name': request.form.get('supplier_name'),
                'item_id': request.form.get('item_id'),
                'item_name': request.form.get('item_name'),
                'part_number': request.form.get('part_number'),
                'affected_qty': request.form.get('affected_qty', 0),
                'unit_cost': request.form.get('unit_cost', 0),
                'issue_type': request.form.get('issue_type'),
                'issue_description': request.form.get('issue_description'),
                'requested_resolution': request.form.get('requested_resolution', 'CREDIT'),
                'financial_impact': request.form.get('financial_impact', 0),
            }

            claim_id = create_claim(data, user['id'])

            flash(f'Claim created successfully', 'success')
            return redirect(url_for('procurement_claims_view', claim_id=claim_id))

        db = get_db()
        suppliers = get_suppliers({'status': 'Active'}, per_page=1000)['items']
        open_pos = get_purchase_orders({'status': 'APPROVED'}, per_page=1000)['items']

        return render_template('procurement/claims/form.html',
            claim=None,
            is_new=True,
            suppliers=suppliers,
            open_pos=open_pos,
            page_title='New Claim'
        )

    @app.route('/procurement/claims/<int:claim_id>')
    @procurement_permission_required('procurement', 'claims', 'view')
    def procurement_claims_view(claim_id):
        """View claim details."""
        db = get_db()
        claim = db.execute("SELECT * FROM procurement_claims WHERE id = ?", (claim_id,)).fetchone()

        if not claim:
            flash('Claim not found', 'error')
            return redirect(url_for('procurement_claims'))

        return render_template('procurement/claims/view.html',
            claim=dict(claim),
            page_title=f'Claim: {claim["claim_number"]}'
        )

    @app.route('/procurement/returns/new', methods=['GET', 'POST'])
    @procurement_permission_required('procurement', 'returns', 'create')
    def procurement_returns_new():
        """Create new return."""
        if request.method == 'POST':
            user = get_current_user()

            data = {
                'return_date': request.form.get('return_date', datetime.now().strftime('%Y-%m-%d')),
                'claim_id': request.form.get('claim_id'),
                'po_id': request.form.get('po_id'),
                'supplier_id': request.form.get('supplier_id'),
                'supplier_name': request.form.get('supplier_name'),
                'item_id': request.form.get('item_id'),
                'item_name': request.form.get('item_name'),
                'part_number': request.form.get('part_number'),
                'return_qty': request.form.get('return_qty', 0),
                'return_reason': request.form.get('return_reason'),
                'return_type': request.form.get('return_type', 'RETURN'),
                'notes': request.form.get('notes'),
            }

            return_id = create_return(data, user['id'])

            flash(f'Return created successfully', 'success')
            return redirect(url_for('procurement_claims'))

        suppliers = get_suppliers({'status': 'Active'}, per_page=1000)['items']
        return render_template('procurement/claims/return_form.html',
            is_new=True,
            suppliers=suppliers,
            page_title='New Return'
        )

    # ============================================================
    # CONTRACTS
    # ============================================================

    @app.route('/procurement/contracts')
    @procurement_permission_required('procurement', 'contracts', 'view')
    def procurement_contracts():
        """Contracts list page."""
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        contract_type = request.args.get('contract_type', '')

        filters = {}
        if search:
            filters['search'] = search
        if status:
            filters['status'] = status
        if contract_type:
            filters['contract_type'] = contract_type

        contracts = get_contracts(filters, page=page)

        return render_template('procurement/contracts/list.html',
            contracts=contracts['items'],
            total=contracts['total'],
            page=page,
            pages=contracts['pages'],
            filters=filters,
            page_title='Contracts & Agreements'
        )

    @app.route('/procurement/contracts/new', methods=['GET', 'POST'])
    @procurement_permission_required('procurement', 'contracts', 'create')
    def procurement_contracts_new():
        """Create new contract."""
        if request.method == 'POST':
            user = get_current_user()

            # Parse price lines
            lines = []
            item_codes = request.form.getlist('item_code')
            for i, code in enumerate(item_codes):
                if code:
                    lines.append({
                        'item_id': request.form.getlist('item_id')[i] if i < len(request.form.getlist('item_id')) else None,
                        'item_code': code,
                        'item_name': request.form.getlist('item_name')[i] if i < len(request.form.getlist('item_name')) else '',
                        'brand': request.form.getlist('brand')[i] if i < len(request.form.getlist('brand')) else '',
                        'part_number': request.form.getlist('part_number')[i] if i < len(request.form.getlist('part_number')) else '',
                        'negotiated_price': request.form.getlist('negotiated_price')[i] if i < len(request.form.getlist('negotiated_price')) else 0,
                        'unit_of_measure': request.form.getlist('unit_of_measure')[i] if i < len(request.form.getlist('unit_of_measure')) else 'PCS',
                    })

            data = {
                'contract_name': request.form.get('contract_name'),
                'supplier_id': request.form.get('supplier_id'),
                'supplier_name': request.form.get('supplier_name'),
                'contract_type': request.form.get('contract_type', 'STANDARD'),
                'start_date': request.form.get('start_date'),
                'end_date': request.form.get('end_date'),
                'total_value': request.form.get('total_value', 0),
                'currency': request.form.get('currency', 'AED'),
                'payment_terms': request.form.get('payment_terms'),
                'incoterm': request.form.get('incoterm'),
                'moq': request.form.get('moq', 1),
                'lead_time_commitment': request.form.get('lead_time_commitment'),
                'sla_terms': request.form.get('sla_terms'),
                'rebate_percent': request.form.get('rebate_percent', 0),
                'special_conditions': request.form.get('special_conditions'),
                'auto_renewal': 1 if request.form.get('auto_renewal') else 0,
                'renewal_notice_days': request.form.get('renewal_notice_days', 30),
                'covered_brands': request.form.get('covered_brands'),
                'covered_item_groups': request.form.get('covered_item_groups'),
                'owner_id': user['id'],
                'owner_name': user['username'],
                'notes': request.form.get('notes'),
            }

            contract_id = create_contract(data, lines if lines else None, user['id'])

            flash(f'Contract created successfully', 'success')
            return redirect(url_for('procurement_contracts_view', contract_id=contract_id))

        suppliers = get_suppliers({'status': 'Active'}, per_page=1000)['items']

        return render_template('procurement/contracts/form.html',
            contract=None,
            is_new=True,
            suppliers=suppliers,
            page_title='New Contract'
        )

    @app.route('/procurement/contracts/<int:contract_id>')
    @procurement_permission_required('procurement', 'contracts', 'view')
    def procurement_contracts_view(contract_id):
        """View contract details."""
        db = get_db()
        contract = db.execute("SELECT * FROM procurement_contracts WHERE id = ?", (contract_id,)).fetchone()

        if not contract:
            flash('Contract not found', 'error')
            return redirect(url_for('procurement_contracts'))

        lines = db.execute("SELECT * FROM procurement_contract_lines WHERE contract_id = ?", (contract_id,)).fetchall()

        return render_template('procurement/contracts/view.html',
            contract=dict(contract),
            lines=[dict(l) for l in lines],
            page_title=f'Contract: {contract["contract_number"]}'
        )

    # ============================================================
    # SUPPLIER PERFORMANCE
    # ============================================================

    @app.route('/procurement/performance')
    @procurement_permission_required('procurement', 'performance', 'view')
    def procurement_performance():
        """Supplier performance page."""
        supplier_id = request.args.get('supplier_id', type=int)
        performance_data = get_supplier_performance_summary(supplier_id if supplier_id else None)

        return render_template('procurement/performance.html',
            suppliers=performance_data,
            selected_supplier_id=supplier_id,
            page_title='Supplier Performance'
        )

    # ============================================================
    # REPORTS
    # ============================================================

    @app.route('/procurement/reports')
    @procurement_permission_required('procurement', 'reports', 'view')
    def procurement_reports():
        """Procurement reports page."""
        return render_template('procurement/reports.html',
            page_title='Procurement Reports'
        )

    @app.route('/procurement/reports/spend-analysis')
    @procurement_permission_required('procurement', 'reports', 'export')
    def procurement_reports_spend():
        """Spend analysis report."""
        db = get_db()

        # Spend by supplier
        spend_by_supplier = db.execute("""
            SELECT s.name, s.code, SUM(po.total_amount) as total_spend, COUNT(*) as po_count
            FROM procurement_purchase_orders po
            JOIN suppliers s ON po.supplier_id = s.id
            WHERE po.status NOT IN ('CANCELLED')
            GROUP BY s.id
            ORDER BY total_spend DESC
            LIMIT 50
        """).fetchall()

        # Spend by month
        spend_by_month = db.execute("""
            SELECT strftime('%Y-%m', po_date) as month, SUM(total_amount) as total
            FROM procurement_purchase_orders
            WHERE status NOT IN ('CANCELLED')
            GROUP BY month
            ORDER BY month DESC
            LIMIT 12
        """).fetchall()

        # Spend by status
        spend_by_status = db.execute("""
            SELECT status, COUNT(*) as count, SUM(total_amount) as total
            FROM procurement_purchase_orders
            GROUP BY status
        """).fetchall()

        return render_template('procurement/reports/spend_analysis.html',
            spend_by_supplier=[dict(s) for s in spend_by_supplier],
            spend_by_month=[dict(s) for s in spend_by_month],
            spend_by_status=[dict(s) for s in spend_by_status],
            page_title='Spend Analysis'
        )

    @app.route('/procurement/reports/po-status')
    @procurement_permission_required('procurement', 'reports', 'view')
    def procurement_reports_po_status():
        """PO status report."""
        db = get_db()

        pos = get_purchase_orders(per_page=500)['items']

        return render_template('procurement/reports/po_status.html',
            pos=pos,
            page_title='PO Status Report'
        )

    # ============================================================
    # SETTINGS
    # ============================================================

    @app.route('/procurement/settings')
    @procurement_permission_required('procurement', 'settings', 'view')
    def procurement_settings():
        """Procurement settings page."""
        category = request.args.get('category', 'GENERAL')
        settings = get_all_procurement_settings(category)

        return render_template('procurement/settings.html',
            settings=settings,
            current_category=category,
            page_title='Procurement Settings'
        )

    @app.route('/procurement/settings/save', methods=['POST'])
    @procurement_permission_required('procurement', 'settings', 'edit')
    def procurement_settings_save():
        """Save procurement settings."""
        for key, value in request.form.items():
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                set_procurement_setting(setting_key, value)

        flash('Settings saved successfully', 'success')
        return redirect(url_for('procurement_settings'))

    # ============================================================
    # API ENDPOINTS
    # ============================================================

    @app.route('/api/procurement/dashboard-stats')
    @procurement_permission_required('procurement', 'dashboard', 'view')
    def api_procurement_dashboard_stats():
        """API endpoint for dashboard stats."""
        stats = get_procurement_dashboard_stats(session['user_id'])
        return jsonify(stats)

    @app.route('/api/procurement/suppliers/search')
    @procurement_permission_required('procurement', 'suppliers', 'view')
    def api_procurement_suppliers_search():
        """API endpoint to search suppliers."""
        query = request.args.get('q', '')
        suppliers = get_suppliers({'search': query, 'status': 'Active'}, per_page=20)['items']

        return jsonify([{
            'id': s['id'],
            'name': s['name'],
            'code': s['code'],
            'country': s.get('country', ''),
            'supplier_type': s.get('supplier_type', ''),
            'payment_terms': s.get('payment_terms', ''),
            'moq': s.get('moq', 1),
        } for s in suppliers])

    @app.route('/api/procurement/alerts/mark-read', methods=['POST'])
    def api_procurement_alerts_mark_read():
        """Mark alert as read."""
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401

        alert_ids = request.json.get('alert_ids', [])
        if alert_ids:
            db = get_db()
            placeholders = ','.join(['?' for _ in alert_ids])
            db.execute(f"""
                UPDATE procurement_alerts SET is_read = 1
                WHERE id IN ({placeholders})
            """, alert_ids)
            db.commit()

        return jsonify({'success': True})

    # ============================================================
    # EXPORT ENDPOINTS
    # ============================================================

    @app.route('/procurement/export/suppliers')
    def procurement_export_suppliers():
        """Export suppliers to Excel."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        suppliers = get_suppliers(per_page=10000)['items']

        wb = Workbook()
        ws = wb.active
        ws.title = "Suppliers"

        # Headers
        headers = ['Code', 'Name', 'Type', 'Country', 'City', 'Phone', 'Email',
                   'Payment Terms', 'Lead Time', 'MOQ', 'Preferred', 'Status', 'Rating']
        ws.append(headers)

        for s in suppliers:
            ws.append([
                s.get('code', ''),
                s.get('name', ''),
                s.get('supplier_type', ''),
                s.get('country', ''),
                s.get('city', ''),
                s.get('phone', ''),
                s.get('email', ''),
                s.get('payment_terms', ''),
                s.get('lead_time', ''),
                s.get('moq', ''),
                'Yes' if s.get('is_preferred') else 'No',
                s.get('status', ''),
                s.get('rating', 0),
            ])

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        as_attachment=True, download_name='suppliers.xlsx')

    @app.route('/procurement/export/orders')
    def procurement_export_orders():
        """Export purchase orders to Excel."""
        if 'user_id' not in session:
            return redirect(url_for('login'))

        orders = get_purchase_orders(per_page=10000)['items']

        wb = Workbook()
        ws = wb.active
        ws.title = "Purchase Orders"

        headers = ['PO Number', 'Date', 'Supplier', 'Buyer', 'Warehouse', 'Status',
                   'Total Amount', 'Currency', 'Expected Delivery', 'Received Amount']
        ws.append(headers)

        for o in orders:
            ws.append([
                o.get('po_number', ''),
                o.get('po_date', ''),
                o.get('supplier_name', ''),
                o.get('buyer_name', ''),
                o.get('warehouse_id', ''),
                o.get('status', ''),
                o.get('total_amount', 0),
                o.get('currency', ''),
                o.get('expected_delivery_date', ''),
                o.get('received_amount', 0),
            ])

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)

        return send_file(output, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                        as_attachment=True, download_name='purchase_orders.xlsx')
