"""
Sales Management Suite - Extended Models
=====================================
Additional data access functions for the complete Sales Management Suite.
Adds support for:
- Pro forma Invoices
- Customer Purchase Orders
- Sales Confirmation Orders
- Sales Invoices
- Sales Alerts
- Commission Calculations
- Enhanced Dashboard Statistics

Usage:
    from sales_suite_models import (
        get_proforma_invoices, create_proforma_invoice,
        get_customer_pos, create_customer_po,
        get_confirmations, create_confirmation,
        get_sales_invoices, create_invoice,
        get_sales_alerts, create_alert,
        get_sales_dashboard_suite,
        # etc...
    )
"""

from database import get_db_context, get_one, get_all, row_to_dict, rows_to_list
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any


# =============================================================================
# PRO FORMA INVOICES
# =============================================================================

def get_proforma_invoices(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """
    Get paginated list of pro forma invoices with filters.
    """
    where_clauses = []
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(pfi.proforma_number LIKE ? OR pfi.customer_name LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term])

        if filters.get('status'):
            where_clauses.append("pfi.status = ?")
            params.append(filters['status'])

        if filters.get('salesperson_id'):
            where_clauses.append("pfi.assigned_salesperson_id = ?")
            params.append(filters['salesperson_id'])

        if filters.get('customer_id'):
            where_clauses.append("pfi.customer_id = ?")
            params.append(filters['customer_id'])

        if filters.get('date_from'):
            where_clauses.append("pfi.proforma_date >= ?")
            params.append(filters['date_from'])

        if filters.get('date_to'):
            where_clauses.append("pfi.proforma_date <= ?")
            params.append(filters['date_to'])

        if filters.get('market'):
            where_clauses.append("pfi.market = ?")
            params.append(filters['market'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    count_sql = f"SELECT COUNT(*) as cnt FROM sales_proforma_invoices pfi WHERE {where_sql}"
    total = get_count_from_sql(count_sql, params)

    offset = (page - 1) * per_page
    sql = f"""
        SELECT pfi.*,
               u.username as assigned_salesperson_name,
               sc.name as customer_name,
               q.quotation_number as quotation_reference,
               (SELECT COUNT(*) FROM sales_proforma_lines WHERE proforma_id = pfi.id) as line_count
        FROM sales_proforma_invoices pfi
        LEFT JOIN users u ON pfi.assigned_salesperson_id = u.id
        LEFT JOIN sales_customers sc ON pfi.customer_id = sc.id
        LEFT JOIN sales_quotations q ON pfi.reference_quotation_id = q.id
        WHERE {where_sql}
        ORDER BY pfi.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        proforma_invoices = rows_to_list(rows)

    return {
        'proforma_invoices': proforma_invoices,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }


def get_proforma_by_id(proforma_id: int) -> Optional[Dict]:
    """Get a single pro forma invoice by ID with lines."""
    proforma = get_one("""
        SELECT pfi.*,
               u.username as assigned_salesperson_name,
               sc.name as customer_name, sc.phone as customer_phone,
               sc.address as customer_address, sc.payment_terms as customer_payment_terms
        FROM sales_proforma_invoices pfi
        LEFT JOIN users u ON pfi.assigned_salesperson_id = u.id
        LEFT JOIN sales_customers sc ON pfi.customer_id = sc.id
        WHERE pfi.id = ?
    """, (proforma_id,))

    if proforma:
        proforma['lines'] = get_all("""
            SELECT * FROM sales_proforma_lines WHERE proforma_id = ?
        """, (proforma_id,))

        proforma['history'] = get_all("""
            SELECT ph.*, u.username as modified_by_name
            FROM sales_proforma_history ph
            LEFT JOIN users u ON ph.modified_by = u.id
            WHERE ph.proforma_id = ?
            ORDER BY ph.modified_at DESC
        """, (proforma_id,)) if table_exists_in_db('sales_proforma_history') else []

    return proforma


def create_proforma_invoice(data: Dict) -> int:
    """Create a new pro forma invoice."""
    with get_db_context() as db:
        year = datetime.now().year
        last_pfi = db.execute("""
            SELECT proforma_number FROM sales_proforma_invoices
            WHERE proforma_number LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f'PFI-{year}%',)).fetchone()

        if last_pfi:
            last_num = int(last_pfi['proforma_number'].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        proforma_number = f"PFI-{year}-{new_num:05d}"

        cursor = db.execute("""
            INSERT INTO sales_proforma_invoices (
                proforma_number, proforma_date, valid_until, customer_id, customer_name,
                customer_type, market, assigned_salesperson_id, currency,
                payment_terms, delivery_terms, incoterm,
                subtotal, discount_percent, discount_amount, tax_percent, tax_amount,
                total_amount, advance_payment_percent, advance_payment_required,
                bank_details, status, source, notes, attachment_path, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            proforma_number,
            data.get('proforma_date', datetime.now().strftime('%Y-%m-%d')),
            data.get('valid_until'),
            data.get('customer_id'),
            data.get('customer_name'),
            data.get('customer_type'),
            data.get('market', 'Local'),
            data.get('assigned_salesperson_id'),
            data.get('currency', 'AED'),
            data.get('payment_terms'),
            data.get('delivery_terms'),
            data.get('incoterm'),
            data.get('subtotal', 0),
            data.get('discount_percent', 0),
            data.get('discount_amount', 0),
            data.get('tax_percent', 0),
            data.get('tax_amount', 0),
            data.get('total_amount', 0),
            data.get('advance_payment_percent', 0),
            data.get('advance_payment_required', 0),
            data.get('bank_details'),
            data.get('status', 'Draft'),
            data.get('source'),
            data.get('notes'),
            data.get('attachment_path'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def add_proforma_line(proforma_id: int, line_data: Dict) -> int:
    """Add a line item to a pro forma invoice."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO sales_proforma_lines (
                proforma_id, line_number, part_number, brand, description,
                requested_quantity, unit_price, discount_percent, discount_amount,
                final_price, tax_percent, tax_amount, line_total,
                supply_lead_time, stock_status, origin, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            proforma_id,
            line_data.get('line_number'),
            line_data.get('part_number'),
            line_data.get('brand'),
            line_data.get('description'),
            line_data.get('requested_quantity'),
            line_data.get('unit_price'),
            line_data.get('discount_percent', 0),
            line_data.get('discount_amount', 0),
            line_data.get('final_price'),
            line_data.get('tax_percent', 0),
            line_data.get('tax_amount', 0),
            line_data.get('line_total'),
            line_data.get('supply_lead_time'),
            line_data.get('stock_status'),
            line_data.get('origin'),
            line_data.get('notes')
        ))
        db.commit()
        return cursor.lastrowid


def update_proforma_totals(proforma_id: int) -> bool:
    """Recalculate and update pro forma totals."""
    proforma = get_proforma_by_id(proforma_id)
    if not proforma:
        return False

    lines = proforma.get('lines', [])
    subtotal = sum(float(line.get('final_price', 0)) * int(line.get('requested_quantity', 0)) for line in lines)

    discount_percent = float(proforma.get('discount_percent', 0))
    discount_amount = subtotal * discount_percent / 100
    taxable_amount = subtotal - discount_amount
    tax_percent = float(proforma.get('tax_percent', 0))
    tax_amount = taxable_amount * tax_percent / 100
    total = taxable_amount + tax_amount

    with get_db_context() as db:
        db.execute("""
            UPDATE sales_proforma_invoices
            SET subtotal = ?, discount_amount = ?, tax_amount = ?, total_amount = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (subtotal, discount_amount, tax_amount, total, proforma_id))
        db.commit()
        return True


# =============================================================================
# CUSTOMER PURCHASE ORDERS (Incoming from customers)
# =============================================================================

def get_customer_pos(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get paginated list of customer purchase orders."""
    where_clauses = []
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(cpo.customer_po_number LIKE ? OR cpo.customer_name LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term])

        if filters.get('status'):
            where_clauses.append("cpo.status = ?")
            params.append(filters['status'])

        if filters.get('review_status'):
            where_clauses.append("cpo.review_status = ?")
            params.append(filters['review_status'])

        if filters.get('salesperson_id'):
            where_clauses.append("cpo.assigned_salesperson_id = ?")
            params.append(filters['salesperson_id'])

        if filters.get('customer_id'):
            where_clauses.append("cpo.customer_id = ?")
            params.append(filters['customer_id'])

        if filters.get('date_from'):
            where_clauses.append("cpo.po_date >= ?")
            params.append(filters['date_from'])

        if filters.get('date_to'):
            where_clauses.append("cpo.po_date <= ?")
            params.append(filters['date_to'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    count_sql = f"SELECT COUNT(*) as cnt FROM sales_customer_purchase_orders cpo WHERE {where_sql}"
    total = get_count_from_sql(count_sql, params)

    offset = (page - 1) * per_page
    sql = f"""
        SELECT cpo.*,
               u.username as assigned_salesperson_name,
               sc.name as customer_name,
               q.quotation_number as quotation_reference,
               pfi.proforma_number as proforma_reference,
               (SELECT COUNT(*) FROM sales_customer_po_lines WHERE customer_po_id = cpo.id) as line_count
        FROM sales_customer_purchase_orders cpo
        LEFT JOIN users u ON cpo.assigned_salesperson_id = u.id
        LEFT JOIN sales_customers sc ON cpo.customer_id = sc.id
        LEFT JOIN sales_quotations q ON cpo.reference_quotation_id = q.id
        LEFT JOIN sales_proforma_invoices pfi ON cpo.reference_proforma_id = pfi.id
        WHERE {where_sql}
        ORDER BY cpo.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        customer_pos = rows_to_list(rows)

    return {
        'customer_pos': customer_pos,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }


def get_customer_po_by_id(cpo_id: int) -> Optional[Dict]:
    """Get a single customer PO by ID with lines."""
    cpo = get_one("""
        SELECT cpo.*,
               u.username as assigned_salesperson_name,
               sc.name as customer_name, sc.phone as customer_phone,
               sc.address as customer_address, sc.payment_terms as customer_payment_terms,
               q.quotation_number as quotation_reference,
               pfi.proforma_number as proforma_reference
        FROM sales_customer_purchase_orders cpo
        LEFT JOIN users u ON cpo.assigned_salesperson_id = u.id
        LEFT JOIN sales_customers sc ON cpo.customer_id = sc.id
        LEFT JOIN sales_quotations q ON cpo.reference_quotation_id = q.id
        LEFT JOIN sales_proforma_invoices pfi ON cpo.reference_proforma_id = pfi.id
        WHERE cpo.id = ?
    """, (cpo_id,))

    if cpo:
        cpo['lines'] = get_all("""
            SELECT * FROM sales_customer_po_lines WHERE customer_po_id = ?
        """, (cpo_id,))

    return cpo


def create_customer_po(data: Dict) -> int:
    """Create a new customer purchase order."""
    with get_db_context() as db:
        year = datetime.now().year
        last_cpo = db.execute("""
            SELECT customer_po_number FROM sales_customer_purchase_orders
            WHERE customer_po_number LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f'CPO-{year}%',)).fetchone()

        if last_cpo:
            last_num = int(last_cpo['customer_po_number'].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        cpo_number = f"CPO-{year}-{new_num:05d}"

        cursor = db.execute("""
            INSERT INTO sales_customer_purchase_orders (
                customer_po_number, po_date, customer_id, customer_name,
                reference_quotation_id, reference_proforma_id, reference_confirmation_id,
                currency, payment_terms, incoterm, destination_country, destination_port,
                subtotal, discount_percent, discount_amount, tax_percent, tax_amount,
                total_amount, requested_delivery_date, assigned_salesperson_id,
                status, review_status, discrepancy_notes, mapping_notes,
                converted_to_order_id, notes, attachment_path, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cpo_number,
            data.get('po_date', datetime.now().strftime('%Y-%m-%d')),
            data.get('customer_id'),
            data.get('customer_name'),
            data.get('reference_quotation_id'),
            data.get('reference_proforma_id'),
            data.get('reference_confirmation_id'),
            data.get('currency', 'AED'),
            data.get('payment_terms'),
            data.get('incoterm'),
            data.get('destination_country'),
            data.get('destination_port'),
            data.get('subtotal', 0),
            data.get('discount_percent', 0),
            data.get('discount_amount', 0),
            data.get('tax_percent', 0),
            data.get('tax_amount', 0),
            data.get('total_amount', 0),
            data.get('requested_delivery_date'),
            data.get('assigned_salesperson_id'),
            data.get('status', 'Received'),
            data.get('review_status', 'Pending'),
            data.get('discrepancy_notes'),
            data.get('mapping_notes'),
            data.get('converted_to_order_id'),
            data.get('notes'),
            data.get('attachment_path'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def add_customer_po_line(cpo_id: int, line_data: Dict) -> int:
    """Add a line item to a customer PO."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO sales_customer_po_lines (
                customer_po_id, line_number, part_number, brand, description,
                ordered_quantity, unit_price, total_price,
                requested_delivery_date, mapping_status,
                mapped_order_line_id, discrepancy_type, discrepancy_notes, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cpo_id,
            line_data.get('line_number'),
            line_data.get('part_number'),
            line_data.get('brand'),
            line_data.get('description'),
            line_data.get('ordered_quantity'),
            line_data.get('unit_price'),
            line_data.get('total_price'),
            line_data.get('requested_delivery_date'),
            line_data.get('mapping_status', 'Pending'),
            line_data.get('mapped_order_line_id'),
            line_data.get('discrepancy_type'),
            line_data.get('discrepancy_notes'),
            line_data.get('notes')
        ))
        db.commit()
        return cursor.lastrowid


# =============================================================================
# SALES CONFIRMATION ORDERS
# =============================================================================

def get_confirmations(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get paginated list of sales confirmations."""
    where_clauses = []
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(sc.confirmation_number LIKE ? OR sc.customer_name LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term])

        if filters.get('status'):
            where_clauses.append("sc.status = ?")
            params.append(filters['status'])

        if filters.get('customer_acceptance_status'):
            where_clauses.append("sc.customer_acceptance_status = ?")
            params.append(filters['customer_acceptance_status'])

        if filters.get('salesperson_id'):
            where_clauses.append("sc.assigned_salesperson_id = ?")
            params.append(filters['salesperson_id'])

        if filters.get('customer_id'):
            where_clauses.append("sc.customer_id = ?")
            params.append(filters['customer_id'])

        if filters.get('date_from'):
            where_clauses.append("sc.confirmation_date >= ?")
            params.append(filters['date_from'])

        if filters.get('date_to'):
            where_clauses.append("sc.confirmation_date <= ?")
            params.append(filters['date_to'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    count_sql = f"SELECT COUNT(*) as cnt FROM sales_confirmations sc WHERE {where_sql}"
    total = get_count_from_sql(count_sql, params)

    offset = (page - 1) * per_page
    sql = f"""
        SELECT sc.*,
               u.username as assigned_salesperson_name,
               cust.name as customer_name,
               q.quotation_number as quotation_reference,
               pfi.proforma_number as proforma_reference,
               (SELECT COUNT(*) FROM sales_confirmation_lines WHERE confirmation_id = sc.id) as line_count
        FROM sales_confirmations sc
        LEFT JOIN users u ON sc.assigned_salesperson_id = u.id
        LEFT JOIN sales_customers cust ON sc.customer_id = cust.id
        LEFT JOIN sales_quotations q ON sc.reference_quotation_id = q.id
        LEFT JOIN sales_proforma_invoices pfi ON sc.reference_proforma_id = pfi.id
        WHERE {where_sql}
        ORDER BY sc.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        confirmations = rows_to_list(rows)

    return {
        'confirmations': confirmations,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }


def get_confirmation_by_id(confirmation_id: int) -> Optional[Dict]:
    """Get a single confirmation by ID with lines."""
    confirmation = get_one("""
        SELECT sc.*,
               u.username as assigned_salesperson_name,
               cust.name as customer_name, cust.phone as customer_phone,
               cust.address as customer_address, cust.payment_terms as customer_payment_terms,
               q.quotation_number as quotation_reference,
               pfi.proforma_number as proforma_reference,
               cpo.customer_po_number as customer_po_reference
        FROM sales_confirmations sc
        LEFT JOIN users u ON sc.assigned_salesperson_id = u.id
        LEFT JOIN sales_customers cust ON sc.customer_id = cust.id
        LEFT JOIN sales_quotations q ON sc.reference_quotation_id = q.id
        LEFT JOIN sales_proforma_invoices pfi ON sc.reference_proforma_id = pfi.id
        LEFT JOIN sales_customer_purchase_orders cpo ON sc.reference_customer_po_id = cpo.id
        WHERE sc.id = ?
    """, (confirmation_id,))

    if confirmation:
        confirmation['lines'] = get_all("""
            SELECT * FROM sales_confirmation_lines WHERE confirmation_id = ?
        """, (confirmation_id,))

    return confirmation


def create_confirmation(data: Dict) -> int:
    """Create a new sales confirmation."""
    with get_db_context() as db:
        year = datetime.now().year
        last_conf = db.execute("""
            SELECT confirmation_number FROM sales_confirmations
            WHERE confirmation_number LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f'SCO-{year}%',)).fetchone()

        if last_conf:
            last_num = int(last_conf['confirmation_number'].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        confirmation_number = f"SCO-{year}-{new_num:05d}"

        cursor = db.execute("""
            INSERT INTO sales_confirmations (
                confirmation_number, confirmation_date,
                reference_quotation_id, reference_proforma_id, reference_customer_po_id,
                customer_id, customer_name, customer_type, market,
                assigned_salesperson_id, currency,
                payment_terms, delivery_terms, incoterm, lead_time_days,
                subtotal, discount_percent, discount_amount, tax_percent, tax_amount,
                total_amount, customer_acceptance_status, customer_acceptance_date,
                acceptance_notes, status, notes, attachment_path, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            confirmation_number,
            data.get('confirmation_date', datetime.now().strftime('%Y-%m-%d')),
            data.get('reference_quotation_id'),
            data.get('reference_proforma_id'),
            data.get('reference_customer_po_id'),
            data.get('customer_id'),
            data.get('customer_name'),
            data.get('customer_type'),
            data.get('market', 'Local'),
            data.get('assigned_salesperson_id'),
            data.get('currency', 'AED'),
            data.get('payment_terms'),
            data.get('delivery_terms'),
            data.get('incoterm'),
            data.get('lead_time_days'),
            data.get('subtotal', 0),
            data.get('discount_percent', 0),
            data.get('discount_amount', 0),
            data.get('tax_percent', 0),
            data.get('tax_amount', 0),
            data.get('total_amount', 0),
            data.get('customer_acceptance_status', 'Pending'),
            data.get('customer_acceptance_date'),
            data.get('acceptance_notes'),
            data.get('status', 'Draft'),
            data.get('notes'),
            data.get('attachment_path'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def add_confirmation_line(confirmation_id: int, line_data: Dict) -> int:
    """Add a line item to a confirmation."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO sales_confirmation_lines (
                confirmation_id, line_number, part_number, brand, description,
                confirmed_quantity, unit_price, discount_percent, discount_amount,
                final_price, tax_percent, tax_amount, line_total,
                delivery_date, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            confirmation_id,
            line_data.get('line_number'),
            line_data.get('part_number'),
            line_data.get('brand'),
            line_data.get('description'),
            line_data.get('confirmed_quantity'),
            line_data.get('unit_price'),
            line_data.get('discount_percent', 0),
            line_data.get('discount_amount', 0),
            line_data.get('final_price'),
            line_data.get('tax_percent', 0),
            line_data.get('tax_amount', 0),
            line_data.get('line_total'),
            line_data.get('delivery_date'),
            line_data.get('notes')
        ))
        db.commit()
        return cursor.lastrowid


# =============================================================================
# SALES INVOICES
# =============================================================================

def get_sales_invoices(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get paginated list of sales invoices."""
    where_clauses = []
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(si.invoice_number LIKE ? OR si.customer_name LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term])

        if filters.get('status'):
            where_clauses.append("si.status = ?")
            params.append(filters['status'])

        if filters.get('payment_status'):
            where_clauses.append("si.payment_status = ?")
            params.append(filters['payment_status'])

        if filters.get('salesperson_id'):
            where_clauses.append("si.assigned_salesperson_id = ?")
            params.append(filters['salesperson_id'])

        if filters.get('customer_id'):
            where_clauses.append("si.customer_id = ?")
            params.append(filters['customer_id'])

        if filters.get('date_from'):
            where_clauses.append("si.invoice_date >= ?")
            params.append(filters['date_from'])

        if filters.get('date_to'):
            where_clauses.append("si.invoice_date <= ?")
            params.append(filters['date_to'])

        if filters.get('market'):
            where_clauses.append("si.market = ?")
            params.append(filters['market'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    count_sql = f"SELECT COUNT(*) as cnt FROM sales_invoices si WHERE {where_sql}"
    total = get_count_from_sql(count_sql, params)

    offset = (page - 1) * per_page
    sql = f"""
        SELECT si.*,
               u.username as assigned_salesperson_name,
               sc.name as customer_name,
               o.order_number as order_reference,
               d.delivery_number as delivery_reference,
               (SELECT COUNT(*) FROM sales_invoice_lines WHERE invoice_id = si.id) as line_count
        FROM sales_invoices si
        LEFT JOIN users u ON si.assigned_salesperson_id = u.id
        LEFT JOIN sales_customers sc ON si.customer_id = sc.id
        LEFT JOIN sales_orders o ON si.order_id = o.id
        LEFT JOIN sales_deliveries d ON si.delivery_id = d.id
        WHERE {where_sql}
        ORDER BY si.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        invoices = rows_to_list(rows)

    return {
        'invoices': invoices,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }


def get_invoice_by_id(invoice_id: int) -> Optional[Dict]:
    """Get a single invoice by ID with lines."""
    invoice = get_one("""
        SELECT si.*,
               u.username as assigned_salesperson_name,
               sc.name as customer_name, sc.phone as customer_phone,
               sc.address as customer_address, sc.payment_terms as customer_payment_terms,
               o.order_number as order_reference,
               d.delivery_number as delivery_reference
        FROM sales_invoices si
        LEFT JOIN users u ON si.assigned_salesperson_id = u.id
        LEFT JOIN sales_customers sc ON si.customer_id = sc.id
        LEFT JOIN sales_orders o ON si.order_id = o.id
        LEFT JOIN sales_deliveries d ON si.delivery_id = d.id
        WHERE si.id = ?
    """, (invoice_id,))

    if invoice:
        invoice['lines'] = get_all("""
            SELECT * FROM sales_invoice_lines WHERE invoice_id = ?
        """, (invoice_id,))

    return invoice


def create_sales_invoice(data: Dict) -> int:
    """Create a new sales invoice."""
    with get_db_context() as db:
        year = datetime.now().year
        last_inv = db.execute("""
            SELECT invoice_number FROM sales_invoices
            WHERE invoice_number LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f'INV-{year}%',)).fetchone()

        if last_inv:
            last_num = int(last_inv['invoice_number'].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        invoice_number = f"INV-{year}-{new_num:05d}"

        cursor = db.execute("""
            INSERT INTO sales_invoices (
                invoice_number, invoice_date, due_date,
                order_id, delivery_id,
                customer_id, customer_name, customer_type, market,
                billing_address, assigned_salesperson_id, currency,
                payment_terms, incoterm,
                subtotal, discount_percent, discount_amount, tax_percent, tax_amount,
                total_amount, amount_paid, amount_due,
                payment_status, status, eor_invoice_number, eor_status,
                notes, attachment_path, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_number,
            data.get('invoice_date', datetime.now().strftime('%Y-%m-%d')),
            data.get('due_date'),
            data.get('order_id'),
            data.get('delivery_id'),
            data.get('customer_id'),
            data.get('customer_name'),
            data.get('customer_type'),
            data.get('market', 'Local'),
            data.get('billing_address'),
            data.get('assigned_salesperson_id'),
            data.get('currency', 'AED'),
            data.get('payment_terms'),
            data.get('incoterm'),
            data.get('subtotal', 0),
            data.get('discount_percent', 0),
            data.get('discount_amount', 0),
            data.get('tax_percent', 0),
            data.get('tax_amount', 0),
            data.get('total_amount', 0),
            data.get('amount_paid', 0),
            data.get('amount_due', 0),
            data.get('payment_status', 'Unpaid'),
            data.get('status', 'Draft'),
            data.get('eor_invoice_number'),
            data.get('eor_status'),
            data.get('notes'),
            data.get('attachment_path'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def add_invoice_line(invoice_id: int, line_data: Dict) -> int:
    """Add a line item to an invoice."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO sales_invoice_lines (
                invoice_id, line_number, part_number, brand, description,
                quantity, unit_price, discount_percent, discount_amount,
                final_price, tax_percent, tax_amount, line_total,
                delivery_line_id, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            invoice_id,
            line_data.get('line_number'),
            line_data.get('part_number'),
            line_data.get('brand'),
            line_data.get('description'),
            line_data.get('quantity'),
            line_data.get('unit_price'),
            line_data.get('discount_percent', 0),
            line_data.get('discount_amount', 0),
            line_data.get('final_price'),
            line_data.get('tax_percent', 0),
            line_data.get('tax_amount', 0),
            line_data.get('line_total'),
            line_data.get('delivery_line_id'),
            line_data.get('notes')
        ))
        db.commit()
        return cursor.lastrowid


# =============================================================================
# SALES ALERTS
# =============================================================================

def get_sales_alerts(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get paginated list of sales alerts."""
    where_clauses = []
    params = []

    if filters:
        if filters.get('alert_type'):
            where_clauses.append("sa.alert_type = ?")
            params.append(filters['alert_type'])

        if filters.get('status'):
            where_clauses.append("sa.status = ?")
            params.append(filters['status'])

        if filters.get('priority'):
            where_clauses.append("sa.priority = ?")
            params.append(filters['priority'])

        if filters.get('salesperson_id'):
            where_clauses.append("sa.salesperson_id = ?")
            params.append(filters['salesperson_id'])

        if filters.get('customer_id'):
            where_clauses.append("sa.customer_id = ?")
            params.append(filters['customer_id'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    count_sql = f"SELECT COUNT(*) as cnt FROM sales_alerts sa WHERE {where_sql}"
    total = get_count_from_sql(count_sql, params)

    offset = (page - 1) * per_page
    sql = f"""
        SELECT sa.*,
               u.username as salesperson_name,
               sc.name as customer_name
        FROM sales_alerts sa
        LEFT JOIN users u ON sa.salesperson_id = u.id
        LEFT JOIN sales_customers sc ON sa.customer_id = sc.id
        WHERE {where_sql}
        ORDER BY 
            CASE sa.priority 
                WHEN 'Critical' THEN 1 
                WHEN 'High' THEN 2 
                WHEN 'Medium' THEN 3 
                ELSE 4 
            END,
            sa.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        alerts = rows_to_list(rows)

    return {
        'alerts': alerts,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }


def get_alert_by_id(alert_id: int) -> Optional[Dict]:
    """Get a single alert by ID."""
    return get_one("""
        SELECT sa.*,
               u.username as salesperson_name,
               sc.name as customer_name
        FROM sales_alerts sa
        LEFT JOIN users u ON sa.salesperson_id = u.id
        LEFT JOIN sales_customers sc ON sa.customer_id = sc.id
        WHERE sa.id = ?
    """, (alert_id,))


def create_alert(data: Dict) -> int:
    """Create a new sales alert."""
    with get_db_context() as db:
        # Generate alert code
        year = datetime.now().year
        last_alert = db.execute("""
            SELECT alert_code FROM sales_alerts
            WHERE alert_code LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f'ALT-{year}%',)).fetchone()

        if last_alert:
            last_num = int(last_alert['alert_code'].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        alert_code = f"ALT-{year}-{new_num:05d}"

        cursor = db.execute("""
            INSERT INTO sales_alerts (
                alert_type, alert_code, title, message,
                reference_type, reference_id, customer_id, salesperson_id,
                priority, status, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('alert_type'),
            alert_code,
            data.get('title'),
            data.get('message'),
            data.get('reference_type'),
            data.get('reference_id'),
            data.get('customer_id'),
            data.get('salesperson_id'),
            data.get('priority', 'Medium'),
            data.get('status', 'Open'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def acknowledge_alert(alert_id: int, user_id: int) -> bool:
    """Acknowledge an alert."""
    with get_db_context() as db:
        db.execute("""
            UPDATE sales_alerts
            SET status = 'Acknowledged', acknowledged_at = CURRENT_TIMESTAMP, acknowledged_by = ?
            WHERE id = ?
        """, (user_id, alert_id))
        db.commit()
        return True


def resolve_alert(alert_id: int, user_id: int, resolution_notes: str = None) -> bool:
    """Resolve an alert."""
    with get_db_context() as db:
        db.execute("""
            UPDATE sales_alerts
            SET status = 'Resolved', resolved_at = CURRENT_TIMESTAMP, 
                resolved_by = ?, resolution_notes = ?
            WHERE id = ?
        """, (user_id, resolution_notes, alert_id))
        db.commit()
        return True


def get_open_alerts_count(salesperson_id: int = None) -> int:
    """Get count of open alerts, optionally filtered by salesperson."""
    sql = "SELECT COUNT(*) as cnt FROM sales_alerts WHERE status IN ('Open', 'Acknowledged')"
    params = []
    
    if salesperson_id:
        sql += " AND (salesperson_id = ? OR salesperson_id IS NULL)"
        params.append(salesperson_id)
    
    result = get_one(sql, params)
    return result['cnt'] if result else 0


def generate_sales_alerts():
    """
    Generate automatic sales alerts based on business rules.
    Should be called periodically (e.g., daily via scheduler).
    """
    today = datetime.now().date()
    alerts_created = 0

    with get_db_context() as db:
        # Alert: Quotations expiring soon
        expiry_threshold = today + timedelta(days=7)
        expiring_quotations = db.execute("""
            SELECT q.id, q.quotation_number, q.valid_until, 
                   sc.name as customer_name, sc.id as customer_id,
                   u.id as salesperson_id
            FROM sales_quotations q
            LEFT JOIN sales_customers sc ON q.customer_id = sc.id
            LEFT JOIN users u ON q.assigned_salesperson_id = u.id
            WHERE q.status IN ('Sent', 'Viewed', 'In Negotiation')
            AND q.valid_until IS NOT NULL
            AND q.valid_until <= ?
            AND q.valid_until >= ?
        """, (expiry_threshold, today)).fetchall()

        for q in expiring_quotations:
            # Check if alert already exists
            existing = db.execute("""
                SELECT id FROM sales_alerts 
                WHERE reference_type = 'quotation' AND reference_id = ?
                AND alert_type = 'quotation_expiry' AND status != 'Resolved'
            """, (q['id'],)).fetchone()
            
            if not existing:
                days_left = (q['valid_until'] - today).days
                db.execute("""
                    INSERT INTO sales_alerts (
                        alert_type, alert_code, title, message,
                        reference_type, reference_id, customer_id, salesperson_id,
                        priority, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    'quotation_expiry',
                    f'ALT-{today.year}-AUTO',
                    f'Quotation {q["quotation_number"]} expiring in {days_left} days',
                    f'Quotation for {q["customer_name"]} expires on {q["valid_until"]}',
                    'quotation', q['id'], q['customer_id'], q['salesperson_id'],
                    'High' if days_left <= 3 else 'Medium',
                    'Open'
                ))
                alerts_created += 1

        # Alert: Reservations expiring soon
        expiring_reservations = db.execute("""
            SELECT r.id, r.reservation_number, r.expiry_date,
                   sc.name as customer_name, sc.id as customer_id,
                   u.id as salesperson_id
            FROM sales_reservations r
            LEFT JOIN sales_customers sc ON r.customer_id = sc.id
            LEFT JOIN users u ON r.assigned_salesperson_id = u.id
            WHERE r.status = 'Active'
            AND r.expiry_date IS NOT NULL
            AND r.expiry_date <= ?
            AND r.expiry_date >= ?
        """, (today + timedelta(days=1), today)).fetchall()

        for r in expiring_reservations:
            existing = db.execute("""
                SELECT id FROM sales_alerts 
                WHERE reference_type = 'reservation' AND reference_id = ?
                AND alert_type = 'reservation_expiry' AND status != 'Resolved'
            """, (r['id'],)).fetchone()
            
            if not existing:
                db.execute("""
                    INSERT INTO sales_alerts (
                        alert_type, alert_code, title, message,
                        reference_type, reference_id, customer_id, salesperson_id,
                        priority, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    'reservation_expiry',
                    f'ALT-{today.year}-AUTO',
                    f'Reservation {r["reservation_number"]} expiring today',
                    f'Reservation for {r["customer_name"]} expires on {r["expiry_date"]}',
                    'reservation', r['id'], r['customer_id'], r['salesperson_id'],
                    'High', 'Open'
                ))
                alerts_created += 1

        # Alert: Customers approaching credit limit
        credit_risk_customers = db.execute("""
            SELECT sc.id, sc.name, sc.credit_limit, sc.outstanding_balance,
                   u.id as salesperson_id
            FROM sales_customers sc
            LEFT JOIN users u ON sc.assigned_salesperson_id = u.id
            WHERE sc.credit_limit > 0
            AND sc.outstanding_balance >= sc.credit_limit * 0.8
            AND sc.status = 'Active'
        """).fetchall()

        for c in credit_risk_customers:
            utilization = (c['outstanding_balance'] / c['credit_limit']) * 100 if c['credit_limit'] > 0 else 0
            existing = db.execute("""
                SELECT id FROM sales_alerts 
                WHERE customer_id = ?
                AND alert_type = 'credit_limit' AND status != 'Resolved'
            """, (c['id'],)).fetchone()
            
            if not existing:
                db.execute("""
                    INSERT INTO sales_alerts (
                        alert_type, alert_code, title, message,
                        customer_id, salesperson_id, priority, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    'credit_limit',
                    f'ALT-{today.year}-AUTO',
                    f'Customer {c["name"]} at {utilization:.0f}% credit utilization',
                    f'Credit limit: {c["credit_limit"]}, Outstanding: {c["outstanding_balance"]}',
                    c['id'], c['salesperson_id'],
                    'High' if utilization >= 100 else 'Medium',
                    'Open'
                ))
                alerts_created += 1

        # Alert: Inquiries without response beyond SLA
        sla_threshold = today - timedelta(hours=4)
        unresponded_inquiries = db.execute("""
            SELECT si.id, si.inquiry_number, si.inquiry_date, si.created_at,
                   sc.name as customer_name, sc.id as customer_id,
                   u.id as salesperson_id
            FROM sales_inquiries si
            LEFT JOIN sales_customers sc ON si.customer_id = sc.id
            LEFT JOIN users u ON si.assigned_salesperson_id = u.id
            WHERE si.status = 'New'
            AND datetime(si.created_at) < datetime(?)
        """, (sla_threshold.isoformat(),)).fetchall()

        for i in unresponded_inquiries:
            existing = db.execute("""
                SELECT id FROM sales_alerts 
                WHERE reference_type = 'inquiry' AND reference_id = ?
                AND alert_type = 'inquiry_sla' AND status != 'Resolved'
            """, (i['id'],)).fetchone()
            
            if not existing:
                db.execute("""
                    INSERT INTO sales_alerts (
                        alert_type, alert_code, title, message,
                        reference_type, reference_id, customer_id, salesperson_id,
                        priority, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    'inquiry_sla',
                    f'ALT-{today.year}-AUTO',
                    f'Inquiry {i["inquiry_number"]} pending response',
                    f'Inquiry from {i["customer_name"]} received on {i["inquiry_date"]} has not been responded to within SLA',
                    'inquiry', i['id'], i['customer_id'], i['salesperson_id'],
                    'High', 'Open'
                ))
                alerts_created += 1

        db.commit()

    return alerts_created


# =============================================================================
# SALES COMMISSIONS
# =============================================================================

def calculate_commission(order_id: int, invoice_id: int = None) -> Dict:
    """
    Calculate commission for a sales order/invoice.
    Returns commission details based on rules and margins.
    """
    order = get_one("""
        SELECT o.*, u.id as salesperson_id
        FROM sales_orders o
        LEFT JOIN users u ON o.assigned_salesperson_id = u.id
        WHERE o.id = ?
    """, (order_id,))

    if not order:
        return {'error': 'Order not found'}

    # Get commission rules
    rules = get_all("""
        SELECT * FROM sales_commission_rules
        WHERE is_active = 1
        AND (effective_from IS NULL OR effective_from <= DATE('now'))
        AND (effective_until IS NULL OR effective_until >= DATE('now'))
        ORDER BY tier_from DESC
    """)

    # Get invoice details if available
    invoice_amount = 0
    margin_percent = 0
    
    if invoice_id:
        invoice = get_one("SELECT * FROM sales_invoices WHERE id = ?", (invoice_id,))
        if invoice:
            invoice_amount = invoice.get('total_amount', 0)
    
    # Simple commission calculation based on total order amount
    total_amount = invoice_amount if invoice_amount > 0 else order.get('total_amount', 0)
    
    # Find applicable rule
    commission_percent = 2.0  # Default
    commission_amount = 0
    
    for rule in rules:
        if total_amount >= rule.get('tier_from', 0):
            if rule.get('tier_to') is None or total_amount <= rule['tier_to']:
                commission_percent = rule.get('commission_percent', 2.0)
                commission_amount = total_amount * commission_percent / 100
                break

    return {
        'order_id': order_id,
        'invoice_id': invoice_id,
        'salesperson_id': order.get('salesperson_id'),
        'base_amount': total_amount,
        'commission_percent': commission_percent,
        'commission_amount': commission_amount,
        'margin_percent': margin_percent
    }


def record_commission(commission_data: Dict) -> int:
    """Record a commission entry."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO sales_commissions (
                invoice_id, order_id, salesperson_id,
                commission_amount, commission_percent, base_amount, margin_percent,
                status, notes, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            commission_data.get('invoice_id'),
            commission_data.get('order_id'),
            commission_data.get('salesperson_id'),
            commission_data.get('commission_amount', 0),
            commission_data.get('commission_percent', 0),
            commission_data.get('base_amount', 0),
            commission_data.get('margin_percent', 0),
            commission_data.get('status', 'Pending'),
            commission_data.get('notes'),
            commission_data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


# =============================================================================
# ENHANCED DASHBOARD STATISTICS
# =============================================================================

def get_sales_dashboard_suite(user_id: int = None, user_role: str = None, 
                               date_from: str = None, date_to: str = None) -> Dict:
    """
    Get comprehensive dashboard statistics for Sales Management Suite.
    Returns KPIs and analytics tailored to user's role.
    """
    today = datetime.now().strftime('%Y-%m-%d')
    current_month_start = datetime.now().strftime('%Y-%m-01')
    
    # Default date filters
    if not date_from:
        date_from = current_month_start
    if not date_to:
        date_to = today

    stats = {}

    with get_db_context() as db:
        # Today's metrics
        stats['today'] = dict(db.execute("""
            SELECT 
                (SELECT COUNT(*) FROM sales_inquiries WHERE DATE(created_at) = ?) as inquiries,
                (SELECT COUNT(*) FROM sales_quotations WHERE DATE(created_at) = ?) as quotations,
                (SELECT COUNT(*) FROM sales_proforma_invoices WHERE DATE(created_at) = ?) as proformas,
                (SELECT COUNT(*) FROM sales_confirmations WHERE DATE(created_at) = ?) as confirmations,
                (SELECT COUNT(*) FROM sales_orders WHERE DATE(order_date) = ?) as orders,
                (SELECT COUNT(*) FROM sales_invoices WHERE DATE(invoice_date) = ?) as invoices,
                (SELECT COALESCE(SUM(total_amount), 0) FROM sales_orders WHERE DATE(order_date) = ?) as sales_amount,
                (SELECT COUNT(*) FROM sales_customer_purchase_orders WHERE DATE(received_date) = ?) as customer_pos
            FROM (SELECT 1) as dummy
        """, (today, today, today, today, today, today, today, today)).fetchone())

        # Month cumulative metrics
        stats['month'] = dict(db.execute("""
            SELECT 
                (SELECT COUNT(*) FROM sales_inquiries WHERE inquiry_date >= ? AND inquiry_date <= ?) as inquiries,
                (SELECT COUNT(*) FROM sales_quotations WHERE quotation_date >= ? AND quotation_date <= ?) as quotations,
                (SELECT COUNT(*) FROM sales_proforma_invoices WHERE proforma_date >= ? AND proforma_date <= ?) as proformas,
                (SELECT COUNT(*) FROM sales_confirmations WHERE confirmation_date >= ? AND confirmation_date <= ?) as confirmations,
                (SELECT COUNT(*) FROM sales_orders WHERE order_date >= ? AND order_date <= ?) as orders,
                (SELECT COUNT(*) FROM sales_invoices WHERE invoice_date >= ? AND invoice_date <= ?) as invoices,
                (SELECT COALESCE(SUM(total_amount), 0) FROM sales_orders WHERE order_date >= ? AND order_date <= ?) as sales_amount,
                (SELECT COUNT(*) FROM sales_returns WHERE return_date >= ? AND return_date <= ?) as returns
            FROM (SELECT 1) as dummy
        """, (date_from, date_to, date_from, date_to, date_from, date_to, date_from, date_to,
              date_from, date_to, date_from, date_to, date_from, date_to, date_from, date_to)).fetchone())

        # Customer metrics
        stats['customers'] = dict(db.execute("""
            SELECT 
                (SELECT COUNT(*) FROM sales_customers WHERE is_active = 1) as active,
                (SELECT COUNT(*) FROM sales_customers WHERE status = 'Inactive' OR is_active = 0) as inactive,
                (SELECT COUNT(*) FROM sales_customers WHERE outstanding_balance > credit_limit * 0.8 AND credit_limit > 0) as at_risk
            FROM (SELECT 1) as dummy
        """).fetchone())

        # Pipeline metrics
        stats['pipeline'] = dict(db.execute("""
            SELECT 
                (SELECT COUNT(*) FROM sales_inquiries WHERE status NOT IN ('Closed', 'Converted to Order', 'Lost')) as open_inquiries,
                (SELECT COUNT(*) FROM sales_opportunities WHERE stage NOT IN ('Won', 'Lost', 'On Hold')) as open_opportunities,
                (SELECT COALESCE(SUM(estimated_value * success_probability / 100), 0) FROM sales_opportunities WHERE stage NOT IN ('Won', 'Lost', 'On Hold')) as weighted_value,
                (SELECT COUNT(*) FROM sales_quotations WHERE status IN ('Sent', 'Viewed', 'In Negotiation')) as pending_quotations,
                (SELECT COUNT(*) FROM sales_proforma_invoices WHERE status IN ('Issued', 'Viewed')) as pending_proformas
            FROM (SELECT 1) as dummy
        """).fetchone())

        # Order fulfillment metrics
        stats['fulfillment'] = dict(db.execute("""
            SELECT 
                (SELECT COUNT(*) FROM sales_orders WHERE status NOT IN ('Delivered', 'Cancelled', 'Closed')) as open_orders,
                (SELECT COUNT(*) FROM sales_orders WHERE status = 'Delayed') as delayed_orders,
                (SELECT COUNT(*) FROM sales_orders WHERE status IN ('Pending Approval', 'Pending Payment', 'Pending Reservation')) as pending_action,
                (SELECT COUNT(*) FROM sales_reservations WHERE status = 'Active' AND expiry_date < ?) as expired_reservations
            FROM (SELECT 1) as dummy
        """, (today,)).fetchone())

        # Financial metrics
        stats['financial'] = dict(db.execute("""
            SELECT 
                (SELECT COALESCE(SUM(total_amount), 0) FROM sales_invoices WHERE payment_status = 'Unpaid') as total_receivables,
                (SELECT COALESCE(SUM(total_amount), 0) FROM sales_invoices WHERE payment_status = 'Overdue') as overdue_receivables,
                (SELECT COALESCE(SUM(total_amount), 0) FROM sales_invoices WHERE invoice_date >= ? AND invoice_date <= ?) as month_invoiced,
                (SELECT COALESCE(SUM(amount_paid), 0) FROM sales_invoices WHERE invoice_date >= ? AND invoice_date <= ?) as month_collected
            FROM (SELECT 1) as dummy
        """, (date_from, date_to, date_from, date_to)).fetchone())

        # Top performers - Salespersons
        stats['top_salespersons'] = rows_to_list(db.execute("""
            SELECT u.username as salesperson,
                   COUNT(DISTINCT o.id) as order_count,
                   COALESCE(SUM(o.total_amount), 0) as total_sales
            FROM users u
            LEFT JOIN sales_orders o ON u.id = o.assigned_salesperson_id 
                AND o.order_date >= ? AND o.order_date <= ?
            WHERE u.role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%')
            GROUP BY u.id
            ORDER BY total_sales DESC
            LIMIT 5
        """, (date_from, date_to)).fetchall())

        # Top customers
        stats['top_customers'] = rows_to_list(db.execute("""
            SELECT sc.name as customer,
                   COUNT(DISTINCT o.id) as order_count,
                   COALESCE(SUM(o.total_amount), 0) as total_sales
            FROM sales_customers sc
            LEFT JOIN sales_orders o ON sc.id = o.customer_id 
                AND o.order_date >= ? AND o.order_date <= ?
            WHERE sc.is_active = 1
            GROUP BY sc.id
            ORDER BY total_sales DESC
            LIMIT 5
        """, (date_from, date_to)).fetchall())

        # Best selling brands
        stats['best_brands'] = rows_to_list(db.execute("""
            SELECT brand, COUNT(*) as order_count, SUM(ordered_quantity) as total_qty
            FROM sales_order_lines
            WHERE order_id IN (SELECT id FROM sales_orders WHERE order_date >= ? AND order_date <= ?)
            GROUP BY brand
            ORDER BY total_qty DESC
            LIMIT 5
        """, (date_from, date_to)).fetchall())

        # Conversion funnel
        stats['conversion_funnel'] = dict(db.execute("""
            SELECT 
                (SELECT COUNT(*) FROM sales_inquiries WHERE inquiry_date >= ? AND inquiry_date <= ?) as inquiries,
                (SELECT COUNT(*) FROM sales_quotations WHERE quotation_date >= ? AND quotation_date <= ?) as quotations,
                (SELECT COUNT(*) FROM sales_proforma_invoices WHERE proforma_date >= ? AND proforma_date <= ?) as proformas,
                (SELECT COUNT(*) FROM sales_confirmations WHERE confirmation_date >= ? AND confirmation_date <= ?) as confirmations,
                (SELECT COUNT(*) FROM sales_orders WHERE order_date >= ? AND order_date <= ?) as orders,
                (SELECT COUNT(*) FROM sales_invoices WHERE invoice_date >= ? AND invoice_date <= ?) as invoices
            FROM (SELECT 1) as dummy
        """, (date_from, date_to, date_from, date_to, date_from, date_to, date_from, date_to,
              date_from, date_to, date_from, date_to)).fetchone())

        # Calculate conversion rates
        inquiries = stats['conversion_funnel']['inquiries'] or 1
        quotations = stats['conversion_funnel']['quotations'] or 0
        proformas = stats['conversion_funnel']['proformas'] or 0
        confirmations = stats['conversion_funnel']['confirmations'] or 0
        orders = stats['conversion_funnel']['orders'] or 0
        invoices = stats['conversion_funnel']['invoices'] or 0

        stats['conversion_rates'] = {
            'inquiry_to_quote': round((quotations / inquiries) * 100, 1) if inquiries > 0 else 0,
            'quote_to_proforma': round((proformas / quotations) * 100, 1) if quotations > 0 else 0,
            'proforma_to_confirmation': round((confirmations / proformas) * 100, 1) if proformas > 0 else 0,
            'confirmation_to_order': round((orders / confirmations) * 100, 1) if confirmations > 0 else 0,
            'order_to_invoice': round((invoices / orders) * 100, 1) if orders > 0 else 0,
            'overall_inquiry_to_invoice': round((invoices / inquiries) * 100, 1) if inquiries > 0 else 0
        }

        # Open alerts count
        stats['open_alerts'] = get_open_alerts_count(user_id)

        # Target achievement (if targets exist)
        target_result = db.execute("""
            SELECT SUM(target_amount) as total_target
            FROM sales_targets
            WHERE year = ? AND period = 'Monthly' AND status = 'Active'
        """, (datetime.now().year,)).fetchone()
        
        if target_result and target_result['total_target']:
            stats['target_achievement'] = round(
                (stats['month']['sales_amount'] / target_result['total_target']) * 100, 1
            )
        else:
            stats['target_achievement'] = 0

    return stats


def get_salesperson_dashboard(salesperson_id: int, date_from: str = None, date_to: str = None) -> Dict:
    """Get dashboard statistics for a specific salesperson."""
    today = datetime.now().strftime('%Y-%m-%d')
    current_month_start = datetime.now().strftime('%Y-%m-01')
    
    if not date_from:
        date_from = current_month_start
    if not date_to:
        date_to = today

    stats = {}

    with get_db_context() as db:
        # Personal metrics
        stats['personal'] = dict(db.execute("""
            SELECT 
                (SELECT COUNT(*) FROM sales_inquiries WHERE assigned_salesperson_id = ? AND inquiry_date >= ? AND inquiry_date <= ?) as inquiries,
                (SELECT COUNT(*) FROM sales_quotations WHERE assigned_salesperson_id = ? AND quotation_date >= ? AND quotation_date <= ?) as quotations,
                (SELECT COUNT(*) FROM sales_orders WHERE assigned_salesperson_id = ? AND order_date >= ? AND order_date <= ?) as orders,
                (SELECT COALESCE(SUM(total_amount), 0) FROM sales_orders WHERE assigned_salesperson_id = ? AND order_date >= ? AND order_date <= ?) as sales_amount,
                (SELECT COUNT(*) FROM sales_opportunities WHERE assigned_salesperson_id = ? AND stage NOT IN ('Won', 'Lost')) as open_opportunities
            FROM (SELECT 1) as dummy
        """, (salesperson_id, date_from, date_to, salesperson_id, date_from, date_to,
              salesperson_id, date_from, date_to, salesperson_id, date_from, date_to,
              salesperson_id)).fetchone())

        # Today's activity
        stats['today'] = dict(db.execute("""
            SELECT 
                (SELECT COUNT(*) FROM sales_activities WHERE owner_id = ? AND activity_date = ?) as activities,
                (SELECT COUNT(*) FROM sales_inquiries WHERE assigned_salesperson_id = ? AND DATE(created_at) = ?) as new_inquiries
            FROM (SELECT 1) as dummy
        """, (salesperson_id, today, salesperson_id, today)).fetchone())

        # Pending actions
        stats['pending'] = dict(db.execute("""
            SELECT 
                (SELECT COUNT(*) FROM sales_quotations WHERE assigned_salesperson_id = ? AND status IN ('Sent', 'Viewed')) as pending_quotations,
                (SELECT COUNT(*) FROM sales_proforma_invoices WHERE assigned_salesperson_id = ? AND status = 'Issued') as pending_proformas,
                (SELECT COUNT(*) FROM sales_confirmations WHERE assigned_salesperson_id = ? AND customer_acceptance_status = 'Pending') as pending_confirmations,
                (SELECT COUNT(*) FROM sales_activities WHERE owner_id = ? AND next_follow_up_date <= ?) as overdue_followups
            FROM (SELECT 1) as dummy
        """, (salesperson_id, salesperson_id, salesperson_id, salesperson_id, today)).fetchone())

        # Target vs Achievement
        target = db.execute("""
            SELECT target_amount FROM sales_targets
            WHERE salesperson_id = ? AND year = ? AND period = 'Monthly' AND status = 'Active'
            LIMIT 1
        """, (salesperson_id, datetime.now().year)).fetchone()
        
        if target:
            stats['target'] = target['target_amount']
            stats['achievement'] = round(
                (stats['personal']['sales_amount'] / target['target_amount']) * 100, 1
            ) if target['target_amount'] > 0 else 0
        else:
            stats['target'] = 0
            stats['achievement'] = 0

        # Open alerts for this salesperson
        stats['alerts'] = get_open_alerts_count(salesperson_id)

    return stats


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_count_from_sql(sql: str, params: List = None) -> int:
    """Execute a count SQL and return the count."""
    result = get_one(sql, params)
    return result['cnt'] if result and 'cnt' in result else 0


def table_exists_in_db(table_name: str) -> bool:
    """Check if a table exists in the database."""
    result = get_one("""
        SELECT name FROM sqlite_master WHERE type='table' AND name = ?
    """, (table_name,))
    return result is not None


def get_proforma_statuses() -> List[str]:
    """Get standard pro forma statuses."""
    return ['Draft', 'Issued', 'Viewed', 'Under Review', 'Revised', 
            'Accepted', 'Rejected', 'Expired', 'Converted']


def get_customer_po_statuses() -> List[str]:
    """Get standard customer PO statuses."""
    return ['Received', 'Under Review', 'Needs Clarification', 'Approved', 
            'Partially Accepted', 'Rejected', 'Converted to Order']


def get_confirmation_statuses() -> List[str]:
    """Get standard confirmation statuses."""
    return ['Draft', 'Sent', 'Confirmed by Customer', 'Revised', 
            'Cancelled', 'Converted to Order']


def get_invoice_statuses() -> List[str]:
    """Get standard invoice statuses."""
    return ['Draft', 'Posted', 'Sent', 'Partially Paid', 'Paid', 
            'Overdue', 'Cancelled', 'Credit Note Issued']


def get_alert_types() -> List[str]:
    """Get standard alert types."""
    return [
        'quotation_expiry', 'proforma_expiry', 'confirmation_pending',
        'reservation_expiry', 'inquiry_sla', 'order_delay',
        'credit_limit', 'payment_overdue', 'return_requested',
        'document_missing', 'price_change', 'stock_shortage'
    ]


def get_alert_priorities() -> List[str]:
    """Get standard alert priorities."""
    return ['Low', 'Medium', 'High', 'Critical']
