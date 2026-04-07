"""
Sales Management Data Access Layer
==================================
Centralized data access for all Sales Management entities.
This module provides CRUD operations and complex queries for:
- Customers & Accounts
- Leads & Inquiries
- Sales Opportunities
- Pricing & Sales Conditions
- Quotations / Proforma / Offers
- Sales Orders
- Reservations & Stock Allocation
- Delivery Coordination
- Local Sales & Export Sales
- Returns & Complaints
- Sales Targets & Commissions
- Contracts & Sales Documents
- Sales Activities & CRM

Usage:
    from sales_models import (
        get_customers, get_customer_by_id,
        get_inquiries, create_inquiry,
        get_opportunities, create_opportunity,
        # ... etc
    )
"""

from database import get_db_context, get_one, get_all, row_to_dict, rows_to_list, get_count, exists
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any


# =============================================================================
# CUSTOMERS & ACCOUNTS
# =============================================================================

def get_sales_customers(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """
    Get paginated list of sales customers with filters.
    """
    where_clauses = ["sc.is_active = 1"]
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(sc.customer_code LIKE ? OR sc.name LIKE ? OR sc.trade_name LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term, search_term])

        if filters.get('customer_type'):
            where_clauses.append("sc.customer_type = ?")
            params.append(filters['customer_type'])

        if filters.get('market'):
            where_clauses.append("sc.market = ?")
            params.append(filters['market'])

        if filters.get('country'):
            where_clauses.append("sc.country = ?")
            params.append(filters['country'])

        if filters.get('city'):
            where_clauses.append("sc.city = ?")
            params.append(filters['city'])

        if filters.get('salesperson_id'):
            where_clauses.append("sc.assigned_salesperson_id = ?")
            params.append(filters['salesperson_id'])

        if filters.get('status') == 'active':
            where_clauses.append("sc.status = 'Active'")
        elif filters.get('status') == 'inactive':
            where_clauses.append("sc.status = 'Inactive'")

        if filters.get('credit_risk'):
            where_clauses.append("sc.credit_status = ?")
            params.append(filters['credit_risk'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    # Count total
    count_sql = f"""
        SELECT COUNT(*) as cnt FROM sales_customers sc
        WHERE {where_sql}
    """
    total = get_count_from_sql(count_sql, params)

    # Get paginated results
    offset = (page - 1) * per_page
    sql = f"""
        SELECT sc.*,
               u.username as assigned_salesperson_name,
               COALESCE(sc.total_orders, 0) as total_orders,
               COALESCE(sc.total_revenue, 0) as total_revenue,
               COALESCE(sc.outstanding_balance, 0) as outstanding_balance
        FROM sales_customers sc
        LEFT JOIN users u ON sc.assigned_salesperson_id = u.id
        WHERE {where_sql}
        ORDER BY sc.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        customers = rows_to_list(rows)

    return {
        'customers': customers,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }


def get_customer_by_id(customer_id: int) -> Optional[Dict]:
    """Get a single customer by ID with full details."""
    sql = """
        SELECT sc.*,
               u.username as assigned_salesperson_name,
               c.name as country_name
        FROM sales_customers sc
        LEFT JOIN users u ON sc.assigned_salesperson_id = u.id
        LEFT JOIN countries c ON sc.country = c.code
        WHERE sc.id = ?
    """
    return get_one(sql, (customer_id,))


def get_customer_balance(customer_id: int) -> Dict:
    """Get customer's outstanding balance and credit info."""
    sql = """
        SELECT
            COALESCE(SUM(CASE WHEN transaction_type = 'Invoice' THEN amount ELSE 0 END), 0) as total_invoiced,
            COALESCE(SUM(CASE WHEN transaction_type = 'Payment' THEN amount ELSE 0 END), 0) as total_paid,
            COALESCE(SUM(CASE WHEN transaction_type = 'Credit' THEN amount ELSE 0 END), 0) as total_credits,
            COALESCE(SUM(CASE WHEN transaction_type = 'Invoice' THEN amount ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN transaction_type = 'Payment' THEN amount ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN transaction_type = 'Credit' THEN amount ELSE 0 END), 0) as outstanding_balance
        FROM sales_customer_transactions
        WHERE customer_id = ?
    """
    return get_one(sql, (customer_id,)) or {
        'total_invoiced': 0, 'total_paid': 0, 'total_credits': 0, 'outstanding_balance': 0
    }


def create_sales_customer(data: Dict) -> int:
    """Create a new sales customer."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO sales_customers (
                customer_code, name, trade_name, customer_type, market,
                country, city, address, phone, whatsapp, email, website,
                buyer_name, buyer_phone, buyer_email,
                trade_type, assigned_salesperson_id, payment_terms,
                credit_limit, currency, default_discount, price_list_id,
                status, priority, notes, is_active, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('customer_code'),
            data.get('name'),
            data.get('trade_name'),
            data.get('customer_type'),
            data.get('market'),
            data.get('country'),
            data.get('city'),
            data.get('address'),
            data.get('phone'),
            data.get('whatsapp'),
            data.get('email'),
            data.get('website'),
            data.get('buyer_name'),
            data.get('buyer_phone'),
            data.get('buyer_email'),
            data.get('trade_type'),
            data.get('assigned_salesperson_id'),
            data.get('payment_terms'),
            data.get('credit_limit', 0),
            data.get('currency', 'AED'),
            data.get('default_discount', 0),
            data.get('price_list_id'),
            data.get('status', 'Active'),
            data.get('priority', 'Medium'),
            data.get('notes'),
            1,
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def update_sales_customer(customer_id: int, data: Dict) -> bool:
    """Update an existing sales customer."""
    fields = []
    params = []

    updatable_fields = [
        'name', 'trade_name', 'customer_type', 'market', 'country', 'city',
        'address', 'phone', 'whatsapp', 'email', 'website', 'buyer_name',
        'buyer_phone', 'buyer_email', 'trade_type', 'assigned_salesperson_id',
        'payment_terms', 'credit_limit', 'currency', 'default_discount',
        'price_list_id', 'status', 'priority', 'notes'
    ]

    for field in updatable_fields:
        if field in data:
            fields.append(f"{field} = ?")
            params.append(data[field])

    if not fields:
        return False

    params.append(customer_id)

    sql = f"UPDATE sales_customers SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"

    with get_db_context() as db:
        db.execute(sql, params)
        db.commit()
        return True


# =============================================================================
# LEADS & INQUIRIES
# =============================================================================

def get_inquiries(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get paginated list of inquiries with filters."""
    where_clauses = []
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(inq.inquiry_number LIKE ? OR inq.customer_name LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term])

        if filters.get('status'):
            where_clauses.append("inq.status = ?")
            params.append(filters['status'])

        if filters.get('source'):
            where_clauses.append("inq.inquiry_source = ?")
            params.append(filters['source'])

        if filters.get('priority'):
            where_clauses.append("inq.priority = ?")
            params.append(filters['priority'])

        if filters.get('salesperson_id'):
            where_clauses.append("inq.assigned_salesperson_id = ?")
            params.append(filters['salesperson_id'])

        if filters.get('date_from'):
            where_clauses.append("inq.inquiry_date >= ?")
            params.append(filters['date_from'])

        if filters.get('date_to'):
            where_clauses.append("inq.inquiry_date <= ?")
            params.append(filters['date_to'])

        if filters.get('market'):
            where_clauses.append("inq.market = ?")
            params.append(filters['market'])

        if filters.get('customer_type'):
            where_clauses.append("inq.customer_type = ?")
            params.append(filters['customer_type'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    count_sql = f"SELECT COUNT(*) as cnt FROM sales_inquiries inq WHERE {where_sql}"
    total = get_count_from_sql(count_sql, params)

    offset = (page - 1) * per_page
    sql = f"""
        SELECT inq.*,
               u.username as assigned_salesperson_name,
               (SELECT COUNT(*) FROM sales_inquiry_lines WHERE inquiry_id = inq.id) as line_count
        FROM sales_inquiries inq
        LEFT JOIN users u ON inq.assigned_salesperson_id = u.id
        WHERE {where_sql}
        ORDER BY inq.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        inquiries = rows_to_list(rows)

    return {
        'inquiries': inquiries,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }


def get_inquiry_by_id(inquiry_id: int) -> Optional[Dict]:
    """Get a single inquiry by ID with lines."""
    inquiry = get_one("""
        SELECT inq.*,
               u.username as assigned_salesperson_name,
               sc.name as customer_name, sc.phone as customer_phone
        FROM sales_inquiries inq
        LEFT JOIN users u ON inq.assigned_salesperson_id = u.id
        LEFT JOIN sales_customers sc ON inq.customer_id = sc.id
        WHERE inq.id = ?
    """, (inquiry_id,))

    if inquiry:
        inquiry['lines'] = get_all("""
            SELECT * FROM sales_inquiry_lines WHERE inquiry_id = ?
        """, (inquiry_id,))

        inquiry['activities'] = get_all("""
            SELECT sa.*, u.username as owner_name
            FROM sales_activities sa
            LEFT JOIN users u ON sa.owner_id = u.id
            WHERE sa.reference_type = 'inquiry' AND sa.reference_id = ?
            ORDER BY sa.activity_date DESC
        """, (inquiry_id,))

    return inquiry


def create_inquiry(data: Dict) -> int:
    """Create a new inquiry."""
    # Generate inquiry number
    with get_db_context() as db:
        year = datetime.now().year
        last_inq = db.execute("""
            SELECT inquiry_number FROM sales_inquiries
            WHERE inquiry_number LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f'INQ-{year}%',)).fetchone()

        if last_inq:
            last_num = int(last_inq['inquiry_number'].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        inquiry_number = f"INQ-{year}-{new_num:05d}"

        cursor = db.execute("""
            INSERT INTO sales_inquiries (
                inquiry_number, inquiry_date, inquiry_time, customer_id, customer_name,
                customer_type, market, country, city, inquiry_source, priority,
                assigned_salesperson_id, status, urgency, immediate_delivery,
                specific_brand_required, target_customer_price, notes,
                reason_for_no_response, final_outcome, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            inquiry_number,
            data.get('inquiry_date', datetime.now().strftime('%Y-%m-%d')),
            data.get('inquiry_time', datetime.now().strftime('%H:%M')),
            data.get('customer_id'),
            data.get('customer_name'),
            data.get('customer_type'),
            data.get('market'),
            data.get('country'),
            data.get('city'),
            data.get('inquiry_source'),
            data.get('priority', 'Medium'),
            data.get('assigned_salesperson_id'),
            data.get('status', 'New'),
            data.get('urgency'),
            data.get('immediate_delivery', 0),
            data.get('specific_brand_required', 0),
            data.get('target_customer_price'),
            data.get('notes'),
            data.get('reason_for_no_response'),
            data.get('final_outcome'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def add_inquiry_line(inquiry_id: int, line_data: Dict) -> int:
    """Add a line item to an inquiry."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO sales_inquiry_lines (
                inquiry_id, part_number, brand, description,
                requested_quantity, target_price, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            inquiry_id,
            line_data.get('part_number'),
            line_data.get('brand'),
            line_data.get('description'),
            line_data.get('requested_quantity'),
            line_data.get('target_price'),
            line_data.get('notes')
        ))
        db.commit()
        return cursor.lastrowid


def update_inquiry_status(inquiry_id: int, status: str, notes: str = None) -> bool:
    """Update inquiry status."""
    sql = "UPDATE sales_inquiries SET status = ?, updated_at = CURRENT_TIMESTAMP"
    params = [status]

    if notes:
        sql += ", notes = ?"
        params.append(notes)

    params.append(inquiry_id)
    sql += " WHERE id = ?"

    with get_db_context() as db:
        db.execute(sql, params)
        db.commit()
        return True


# =============================================================================
# SALES OPPORTUNITIES
# =============================================================================

def get_opportunities(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get paginated list of opportunities."""
    where_clauses = []
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(opp.opportunity_number LIKE ? OR opp.customer_name LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term])

        if filters.get('stage'):
            where_clauses.append("opp.stage = ?")
            params.append(filters['stage'])

        if filters.get('salesperson_id'):
            where_clauses.append("opp.assigned_salesperson_id = ?")
            params.append(filters['salesperson_id'])

        if filters.get('source'):
            where_clauses.append("opp.source = ?")
            params.append(filters['source'])

        if filters.get('sales_type'):
            where_clauses.append("opp.sales_type = ?")
            params.append(filters['sales_type'])

        if filters.get('market'):
            where_clauses.append("opp.market = ?")
            params.append(filters['market'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    count_sql = f"SELECT COUNT(*) as cnt FROM sales_opportunities opp WHERE {where_sql}"
    total = get_count_from_sql(count_sql, params)

    offset = (page - 1) * per_page
    sql = f"""
        SELECT opp.*,
               u.username as assigned_salesperson_name,
               sc.name as customer_name
        FROM sales_opportunities opp
        LEFT JOIN users u ON opp.assigned_salesperson_id = u.id
        LEFT JOIN sales_customers sc ON opp.customer_id = sc.id
        WHERE {where_sql}
        ORDER BY opp.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        opportunities = rows_to_list(rows)

    return {
        'opportunities': opportunities,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }


def get_opportunity_by_id(opportunity_id: int) -> Optional[Dict]:
    """Get a single opportunity by ID."""
    opp = get_one("""
        SELECT opp.*,
               u.username as assigned_salesperson_name,
               sc.name as customer_name, sc.phone as customer_phone, sc.email as customer_email
        FROM sales_opportunities opp
        LEFT JOIN users u ON opp.assigned_salesperson_id = u.id
        LEFT JOIN sales_customers sc ON opp.customer_id = sc.id
        WHERE opp.id = ?
    """, (opportunity_id,))

    if opp:
        opp['activities'] = get_all("""
            SELECT sa.*, u.username as owner_name
            FROM sales_activities sa
            LEFT JOIN users u ON sa.owner_id = u.id
            WHERE sa.reference_type = 'opportunity' AND sa.reference_id = ?
            ORDER BY sa.activity_date DESC
        """, (opportunity_id,))

    return opp


def create_opportunity(data: Dict) -> int:
    """Create a new opportunity."""
    with get_db_context() as db:
        year = datetime.now().year
        last_opp = db.execute("""
            SELECT opportunity_number FROM sales_opportunities
            WHERE opportunity_number LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f'OPP-{year}%',)).fetchone()

        if last_opp:
            last_num = int(last_opp['opportunity_number'].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        opportunity_number = f"OPP-{year}-{new_num:05d}"

        cursor = db.execute("""
            INSERT INTO sales_opportunities (
                opportunity_number, customer_id, customer_name, assigned_salesperson_id,
                source, sales_type, market, customer_type, brand, product_group,
                estimated_value, success_probability, expected_close_date, stage,
                possible_competitors, deal_risks, customer_requirements,
                last_activity_date, next_step, next_follow_up, notes, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            opportunity_number,
            data.get('customer_id'),
            data.get('customer_name'),
            data.get('assigned_salesperson_id'),
            data.get('source'),
            data.get('sales_type'),
            data.get('market'),
            data.get('customer_type'),
            data.get('brand'),
            data.get('product_group'),
            data.get('estimated_value', 0),
            data.get('success_probability', 0),
            data.get('expected_close_date'),
            data.get('stage', 'Identified'),
            data.get('possible_competitors'),
            data.get('deal_risks'),
            data.get('customer_requirements'),
            datetime.now().strftime('%Y-%m-%d'),
            data.get('next_step'),
            data.get('next_follow_up'),
            data.get('notes'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def update_opportunity_stage(opportunity_id: int, stage: str, notes: str = None) -> bool:
    """Update opportunity stage."""
    sql = "UPDATE sales_opportunities SET stage = ?, last_activity_date = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP"
    params = [stage]

    if notes:
        sql += ", notes = ?"
        params.append(notes)

    params.append(opportunity_id)
    sql += " WHERE id = ?"

    with get_db_context() as db:
        db.execute(sql, params)
        db.commit()
        return True


# =============================================================================
# QUOTATIONS / PROFORMA / OFFERS
# =============================================================================

def get_quotations(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get paginated list of quotations."""
    where_clauses = []
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(q.quotation_number LIKE ? OR q.customer_name LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term])

        if filters.get('status'):
            where_clauses.append("q.status = ?")
            params.append(filters['status'])

        if filters.get('salesperson_id'):
            where_clauses.append("q.assigned_salesperson_id = ?")
            params.append(filters['salesperson_id'])

        if filters.get('customer_id'):
            where_clauses.append("q.customer_id = ?")
            params.append(filters['customer_id'])

        if filters.get('date_from'):
            where_clauses.append("q.quotation_date >= ?")
            params.append(filters['date_from'])

        if filters.get('date_to'):
            where_clauses.append("q.quotation_date <= ?")
            params.append(filters['date_to'])

        if filters.get('market'):
            where_clauses.append("q.market = ?")
            params.append(filters['market'])

        if filters.get('currency'):
            where_clauses.append("q.currency = ?")
            params.append(filters['currency'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    count_sql = f"SELECT COUNT(*) as cnt FROM sales_quotations q WHERE {where_sql}"
    total = get_count_from_sql(count_sql, params)

    offset = (page - 1) * per_page
    sql = f"""
        SELECT q.*,
               u.username as assigned_salesperson_name,
               sc.name as customer_name,
               (SELECT COUNT(*) FROM sales_quotation_lines WHERE quotation_id = q.id) as line_count
        FROM sales_quotations q
        LEFT JOIN users u ON q.assigned_salesperson_id = u.id
        LEFT JOIN sales_customers sc ON q.customer_id = sc.id
        WHERE {where_sql}
        ORDER BY q.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        quotations = rows_to_list(rows)

    return {
        'quotations': quotations,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }


def get_quotation_by_id(quotation_id: int) -> Optional[Dict]:
    """Get a single quotation by ID with lines."""
    quotation = get_one("""
        SELECT q.*,
               u.username as assigned_salesperson_name,
               sc.name as customer_name, sc.phone as customer_phone,
               sc.address as customer_address, sc.payment_terms as customer_payment_terms
        FROM sales_quotations q
        LEFT JOIN users u ON q.assigned_salesperson_id = u.id
        LEFT JOIN sales_customers sc ON q.customer_id = sc.id
        WHERE q.id = ?
    """, (quotation_id,))

    if quotation:
        quotation['lines'] = get_all("""
            SELECT * FROM sales_quotation_lines WHERE quotation_id = ?
        """, (quotation_id,))

        quotation['history'] = get_all("""
            SELECTqh.*, u.username as modified_by_name
            FROM sales_quotation_history qh
            LEFT JOIN users u ON qh.modified_by = u.id
            WHERE qh.quotation_id = ?
            ORDER BY qh.modified_at DESC
        """, (quotation_id,))

    return quotation


def create_quotation(data: Dict) -> int:
    """Create a new quotation."""
    with get_db_context() as db:
        year = datetime.now().year
        last_quot = db.execute("""
            SELECT quotation_number FROM sales_quotations
            WHERE quotation_number LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f'QUO-{year}%',)).fetchone()

        if last_quot:
            last_num = int(last_quot['quotation_number'].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        quotation_number = f"QUO-{year}-{new_num:05d}"

        cursor = db.execute("""
            INSERT INTO sales_quotations (
                quotation_number, quotation_date, valid_until, customer_id, customer_name,
                customer_type, market, assigned_salesperson_id, currency,
                payment_terms, delivery_terms, delivery_location,
                subtotal, discount_percent, discount_amount, tax_percent, tax_amount,
                total_amount, status, source, supply_lead_time, stock_status,
                notes, attachment_path, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            quotation_number,
            data.get('quotation_date', datetime.now().strftime('%Y-%m-%d')),
            data.get('valid_until'),
            data.get('customer_id'),
            data.get('customer_name'),
            data.get('customer_type'),
            data.get('market'),
            data.get('assigned_salesperson_id'),
            data.get('currency', 'AED'),
            data.get('payment_terms'),
            data.get('delivery_terms'),
            data.get('delivery_location'),
            data.get('subtotal', 0),
            data.get('discount_percent', 0),
            data.get('discount_amount', 0),
            data.get('tax_percent', 0),
            data.get('tax_amount', 0),
            data.get('total_amount', 0),
            data.get('status', 'Draft'),
            data.get('source'),
            data.get('supply_lead_time'),
            data.get('stock_status'),
            data.get('notes'),
            data.get('attachment_path'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def add_quotation_line(quotation_id: int, line_data: Dict) -> int:
    """Add a line item to a quotation."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO sales_quotation_lines (
                quotation_id, line_number, part_number, brand, description,
                requested_quantity, unit_price, discount_percent, discount_amount,
                final_price, supply_lead_time, stock_status, origin
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            quotation_id,
            line_data.get('line_number'),
            line_data.get('part_number'),
            line_data.get('brand'),
            line_data.get('description'),
            line_data.get('requested_quantity'),
            line_data.get('unit_price'),
            line_data.get('discount_percent', 0),
            line_data.get('discount_amount', 0),
            line_data.get('final_price'),
            line_data.get('supply_lead_time'),
            line_data.get('stock_status'),
            line_data.get('origin')
        ))
        db.commit()
        return cursor.lastrowid


def update_quotation_totals(quotation_id: int) -> bool:
    """Recalculate and update quotation totals."""
    quotation = get_quotation_by_id(quotation_id)
    if not quotation:
        return False

    lines = quotation.get('lines', [])
    subtotal = sum(float(line.get('final_price', 0)) * int(line.get('requested_quantity', 0)) for line in lines)

    discount_percent = float(quotation.get('discount_percent', 0))
    discount_amount = subtotal * discount_percent / 100
    taxable_amount = subtotal - discount_amount
    tax_percent = float(quotation.get('tax_percent', 0))
    tax_amount = taxable_amount * tax_percent / 100
    total = taxable_amount + tax_amount

    with get_db_context() as db:
        db.execute("""
            UPDATE sales_quotations
            SET subtotal = ?, discount_amount = ?, tax_amount = ?, total_amount = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (subtotal, discount_amount, tax_amount, total, quotation_id))
        db.commit()
        return True


# =============================================================================
# SALES ORDERS
# =============================================================================

def get_sales_orders(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get paginated list of sales orders."""
    where_clauses = []
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(o.order_number LIKE ? OR o.customer_name LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term])

        if filters.get('status'):
            where_clauses.append("o.status = ?")
            params.append(filters['status'])

        if filters.get('order_status'):  # Alias for status
            where_clauses.append("o.status = ?")
            params.append(filters['order_status'])

        if filters.get('salesperson_id'):
            where_clauses.append("o.assigned_salesperson_id = ?")
            params.append(filters['salesperson_id'])

        if filters.get('customer_id'):
            where_clauses.append("o.customer_id = ?")
            params.append(filters['customer_id'])

        if filters.get('date_from'):
            where_clauses.append("o.order_date >= ?")
            params.append(filters['date_from'])

        if filters.get('date_to'):
            where_clauses.append("o.order_date <= ?")
            params.append(filters['date_to'])

        if filters.get('market'):
            where_clauses.append("o.market = ?")
            params.append(filters['market'])

        if filters.get('is_export'):
            where_clauses.append("o.is_export = ?")
            params.append(1 if filters['is_export'] else 0)

        if filters.get('priority'):
            where_clauses.append("o.priority = ?")
            params.append(filters['priority'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    count_sql = f"SELECT COUNT(*) as cnt FROM sales_orders o WHERE {where_sql}"
    total = get_count_from_sql(count_sql, params)

    offset = (page - 1) * per_page
    sql = f"""
        SELECT o.*,
               u.username as assigned_salesperson_name,
               sc.name as customer_name,
               q.quotation_number as quotation_reference,
               (SELECT COUNT(*) FROM sales_order_lines WHERE order_id = o.id) as line_count,
               (SELECT SUM(reserved_quantity) FROM sales_reservations WHERE order_id = o.id) as total_reserved
        FROM sales_orders o
        LEFT JOIN users u ON o.assigned_salesperson_id = u.id
        LEFT JOIN sales_customers sc ON o.customer_id = sc.id
        LEFT JOIN sales_quotations q ON o.quotation_id = q.id
        WHERE {where_sql}
        ORDER BY o.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        orders = rows_to_list(rows)

    return {
        'orders': orders,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }


def get_order_by_id(order_id: int) -> Optional[Dict]:
    """Get a single order by ID with lines."""
    order = get_one("""
        SELECT o.*,
               u.username as assigned_salesperson_name,
               sc.name as customer_name, sc.phone as customer_phone,
               sc.address as customer_address, sc.payment_terms as customer_payment_terms,
               sc.credit_limit, sc.outstanding_balance as customer_balance,
               q.quotation_number as quotation_reference
        FROM sales_orders o
        LEFT JOIN users u ON o.assigned_salesperson_id = u.id
        LEFT JOIN sales_customers sc ON o.customer_id = sc.id
        LEFT JOIN sales_quotations q ON o.quotation_id = q.id
        WHERE o.id = ?
    """, (order_id,))

    if order:
        order['lines'] = get_all("""
            SELECT ol.*,
                   COALESCE((SELECT SUM(reserved_quantity) FROM sales_reservations WHERE order_line_id = ol.id), 0) as reserved_qty,
                   COALESCE((SELECT SUM(quantity) FROM sales_delivery_lines WHERE order_line_id = ol.id), 0) as delivered_qty
            FROM sales_order_lines ol
            WHERE ol.order_id = ?
        """, (order_id,))

        order['reservations'] = get_all("""
            SELECT r.*, w.name as warehouse_name
            FROM sales_reservations r
            LEFT JOIN warehouses w ON r.warehouse_id = w.id
            WHERE r.order_id = ?
        """, (order_id,))

        order['deliveries'] = get_all("""
            SELECT d.*,
                   (SELECT SUM(quantity) FROM sales_delivery_lines WHERE delivery_id = d.id) as total_items
            FROM sales_deliveries d
            WHERE d.order_id = ?
            ORDER BY d.delivery_date DESC
        """, (order_id,))

    return order


def create_sales_order(data: Dict) -> int:
    """Create a new sales order."""
    with get_db_context() as db:
        year = datetime.now().year
        last_ord = db.execute("""
            SELECT order_number FROM sales_orders
            WHERE order_number LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f'ORD-{year}%',)).fetchone()

        if last_ord:
            last_num = int(last_ord['order_number'].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        order_number = f"ORD-{year}-{new_num:05d}"

        cursor = db.execute("""
            INSERT INTO sales_orders (
                order_number, order_date, customer_id, customer_name, customer_type,
                market, is_export, export_country, incoterm, transport_mode,
                assigned_salesperson_id, quotation_id, currency,
                payment_terms, delivery_terms, delivery_address,
                shipment_type, subtotal, discount_percent, discount_amount,
                tax_percent, tax_amount, total_amount, status, priority,
                promised_delivery_date, notes, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_number,
            data.get('order_date', datetime.now().strftime('%Y-%m-%d')),
            data.get('customer_id'),
            data.get('customer_name'),
            data.get('customer_type'),
            data.get('market'),
            data.get('is_export', 0),
            data.get('export_country'),
            data.get('incoterm'),
            data.get('transport_mode'),
            data.get('assigned_salesperson_id'),
            data.get('quotation_id'),
            data.get('currency', 'AED'),
            data.get('payment_terms'),
            data.get('delivery_terms'),
            data.get('delivery_address'),
            data.get('shipment_type'),
            data.get('subtotal', 0),
            data.get('discount_percent', 0),
            data.get('discount_amount', 0),
            data.get('tax_percent', 0),
            data.get('tax_amount', 0),
            data.get('total_amount', 0),
            data.get('status', 'Registered'),
            data.get('priority', 'Medium'),
            data.get('promised_delivery_date'),
            data.get('notes'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def add_order_line(order_id: int, line_data: Dict) -> int:
    """Add a line item to an order."""
    with get_db_context() as db:
        # Get next line number
        last_line = db.execute("""
            SELECT MAX(line_number) as max_line FROM sales_order_lines WHERE order_id = ?
        """, (order_id,)).fetchone()

        next_line = (last_line['max_line'] or 0) + 1

        cursor = db.execute("""
            INSERT INTO sales_order_lines (
                order_id, line_number, part_number, brand, description,
                ordered_quantity, available_quantity, shortage_quantity,
                unit_price, discount_percent, discount_amount, final_price,
                tax_percent, tax_amount, line_total, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order_id,
            next_line,
            line_data.get('part_number'),
            line_data.get('brand'),
            line_data.get('description'),
            line_data.get('ordered_quantity'),
            line_data.get('available_quantity', 0),
            line_data.get('shortage_quantity', 0),
            line_data.get('unit_price'),
            line_data.get('discount_percent', 0),
            line_data.get('discount_amount', 0),
            line_data.get('final_price'),
            line_data.get('tax_percent', 0),
            line_data.get('tax_amount', 0),
            line_data.get('line_total'),
            line_data.get('notes')
        ))
        db.commit()
        return cursor.lastrowid


def update_order_status(order_id: int, status: str) -> bool:
    """Update order status."""
    with get_db_context() as db:
        db.execute("""
            UPDATE sales_orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?
        """, (status, order_id))
        db.commit()
        return True


# =============================================================================
# RESERVATIONS & STOCK ALLOCATION
# =============================================================================

def get_reservations(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get paginated list of reservations."""
    where_clauses = []
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(r.reservation_number LIKE ? OR sc.name LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term])

        if filters.get('status'):
            where_clauses.append("r.status = ?")
            params.append(filters['status'])

        if filters.get('customer_id'):
            where_clauses.append("r.customer_id = ?")
            params.append(filters['customer_id'])

        if filters.get('order_id'):
            where_clauses.append("r.order_id = ?")
            params.append(filters['order_id'])

        if filters.get('warehouse_id'):
            where_clauses.append("r.warehouse_id = ?")
            params.append(filters['warehouse_id'])

        if filters.get('priority'):
            where_clauses.append("r.priority = ?")
            params.append(filters['priority'])

        if filters.get('expires_before'):
            where_clauses.append("r.expiry_date < ?")
            params.append(filters['expires_before'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    count_sql = f"SELECT COUNT(*) as cnt FROM sales_reservations r WHERE {where_sql}"
    total = get_count_from_sql(count_sql, params)

    offset = (page - 1) * per_page
    sql = f"""
        SELECT r.*,
               sc.name as customer_name,
               o.order_number,
               w.name as warehouse_name,
               u.username as assigned_salesperson_name,
               apr.username as approver_name
        FROM sales_reservations r
        LEFT JOIN sales_customers sc ON r.customer_id = sc.id
        LEFT JOIN sales_orders o ON r.order_id = o.id
        LEFT JOIN warehouses w ON r.warehouse_id = w.id
        LEFT JOIN users u ON r.assigned_salesperson_id = u.id
        LEFT JOIN users apr ON r.approver_id = apr.id
        WHERE {where_sql}
        ORDER BY r.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        reservations = rows_to_list(rows)

    return {
        'reservations': reservations,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }


def create_reservation(data: Dict) -> int:
    """Create a new reservation."""
    with get_db_context() as db:
        year = datetime.now().year
        last_res = db.execute("""
            SELECT reservation_number FROM sales_reservations
            WHERE reservation_number LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f'RES-{year}%',)).fetchone()

        if last_res:
            last_num = int(last_res['reservation_number'].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        reservation_number = f"RES-{year}-{new_num:05d}"

        cursor = db.execute("""
            INSERT INTO sales_reservations (
                reservation_number, reservation_date, customer_id, reference_type,
                reference_id, order_id, quotation_id, part_number, brand,
                warehouse_id, reserved_quantity, available_quantity_at_reservation,
                expiry_date, reservation_reason, priority, status,
                assigned_salesperson_id, approver_id, notes, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            reservation_number,
            data.get('reservation_date', datetime.now().strftime('%Y-%m-%d')),
            data.get('customer_id'),
            data.get('reference_type'),
            data.get('reference_id'),
            data.get('order_id'),
            data.get('quotation_id'),
            data.get('part_number'),
            data.get('brand'),
            data.get('warehouse_id'),
            data.get('reserved_quantity'),
            data.get('available_quantity_at_reservation'),
            data.get('expiry_date'),
            data.get('reservation_reason'),
            data.get('priority', 'Medium'),
            data.get('status', 'Active'),
            data.get('assigned_salesperson_id'),
            data.get('approver_id'),
            data.get('notes'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def release_reservation(reservation_id: int, reason: str = None) -> bool:
    """Release/cancel a reservation."""
    with get_db_context() as db:
        db.execute("""
            UPDATE sales_reservations
            SET status = 'Released', released_at = CURRENT_TIMESTAMP,
                release_reason = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (reason, reservation_id))
        db.commit()
        return True


# =============================================================================
# DELIVERY COORDINATION
# =============================================================================

def get_deliveries(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get paginated list of deliveries."""
    where_clauses = []
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(d.delivery_number LIKE ? OR o.order_number LIKE ? OR sc.name LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term, search_term])

        if filters.get('status'):
            where_clauses.append("d.status = ?")
            params.append(filters['status'])

        if filters.get('order_id'):
            where_clauses.append("d.order_id = ?")
            params.append(filters['order_id'])

        if filters.get('customer_id'):
            where_clauses.append("d.customer_id = ?")
            params.append(filters['customer_id'])

        if filters.get('delivery_type'):
            where_clauses.append("d.delivery_type = ?")
            params.append(filters['delivery_type'])

        if filters.get('date_from'):
            where_clauses.append("d.requested_date >= ?")
            params.append(filters['date_from'])

        if filters.get('date_to'):
            where_clauses.append("d.requested_date <= ?")
            params.append(filters['date_to'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    count_sql = f"SELECT COUNT(*) as cnt FROM sales_deliveries d WHERE {where_sql}"
    total = get_count_from_sql(count_sql, params)

    offset = (page - 1) * per_page
    sql = f"""
        SELECT d.*,
               o.order_number,
               sc.name as customer_name,
               u.username as coordinator_name,
               v.vehicle_number,
               dr.driver_name
        FROM sales_deliveries d
        LEFT JOIN sales_orders o ON d.order_id = o.id
        LEFT JOIN sales_customers sc ON d.customer_id = sc.id
        LEFT JOIN users u ON d.coordinator_id = u.id
        LEFT JOIN vehicles v ON d.vehicle_id = v.id
        LEFT JOIN drivers dr ON d.driver_id = dr.id
        WHERE {where_sql}
        ORDER BY d.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        deliveries = rows_to_list(rows)

    return {
        'deliveries': deliveries,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }


def get_delivery_by_id(delivery_id: int) -> Optional[Dict]:
    """Get a single delivery by ID."""
    delivery = get_one("""
        SELECT d.*,
               o.order_number,
               sc.name as customer_name, sc.address as customer_address, sc.phone as customer_phone,
               u.username as coordinator_name,
               v.vehicle_number, v.vehicle_type,
               dr.driver_name, dr.driver_phone
        FROM sales_deliveries d
        LEFT JOIN sales_orders o ON d.order_id = o.id
        LEFT JOIN sales_customers sc ON d.customer_id = sc.id
        LEFT JOIN users u ON d.coordinator_id = u.id
        LEFT JOIN vehicles v ON d.vehicle_id = v.id
        LEFT JOIN drivers dr ON d.driver_id = dr.id
        WHERE d.id = ?
    """, (delivery_id,))

    if delivery:
        delivery['lines'] = get_all("""
            SELECT dl.*, ol.part_number, ol.brand, ol.description
            FROM sales_delivery_lines dl
            LEFT JOIN sales_order_lines ol ON dl.order_line_id = ol.id
            WHERE dl.delivery_id = ?
        """, (delivery_id,))

        delivery['documents'] = get_all("""
            SELECT * FROM sales_delivery_documents WHERE delivery_id = ?
        """, (delivery_id,))

    return delivery


def create_delivery(data: Dict) -> int:
    """Create a new delivery request."""
    with get_db_context() as db:
        year = datetime.now().year
        last_del = db.execute("""
            SELECT delivery_number FROM sales_deliveries
            WHERE delivery_number LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f'DEL-{year}%',)).fetchone()

        if last_del:
            last_num = int(last_del['delivery_number'].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        delivery_number = f"DEL-{year}-{new_num:05d}"

        cursor = db.execute("""
            INSERT INTO sales_deliveries (
                delivery_number, order_id, customer_id, delivery_type,
                delivery_location, requested_date, requested_time,
                coordinator_id, vehicle_id, driver_id,
                status, preparation_status, transport_status,
                actual_departure_time, actual_arrival_time,
                notes, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            delivery_number,
            data.get('order_id'),
            data.get('customer_id'),
            data.get('delivery_type'),
            data.get('delivery_location'),
            data.get('requested_date'),
            data.get('requested_time'),
            data.get('coordinator_id'),
            data.get('vehicle_id'),
            data.get('driver_id'),
            data.get('status', 'Pending'),
            data.get('preparation_status', 'Waiting for Packing'),
            data.get('transport_status', 'Pending'),
            data.get('actual_departure_time'),
            data.get('actual_arrival_time'),
            data.get('notes'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def add_delivery_line(delivery_id: int, line_data: Dict) -> int:
    """Add a line item to a delivery."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO sales_delivery_lines (
                delivery_id, order_id, order_line_id, part_number, brand,
                description, quantity, weight, volume, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            delivery_id,
            line_data.get('order_id'),
            line_data.get('order_line_id'),
            line_data.get('part_number'),
            line_data.get('brand'),
            line_data.get('description'),
            line_data.get('quantity'),
            line_data.get('weight'),
            line_data.get('volume'),
            line_data.get('notes')
        ))
        db.commit()
        return cursor.lastrowid


# =============================================================================
# RETURNS & COMPLAINTS
# =============================================================================

def get_returns(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get paginated list of returns."""
    where_clauses = []
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(r.return_number LIKE ? OR sc.name LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term])

        if filters.get('status'):
            where_clauses.append("r.status = ?")
            params.append(filters['status'])

        if filters.get('return_reason'):
            where_clauses.append("r.return_reason = ?")
            params.append(filters['return_reason'])

        if filters.get('customer_id'):
            where_clauses.append("r.customer_id = ?")
            params.append(filters['customer_id'])

        if filters.get('date_from'):
            where_clauses.append("r.return_date >= ?")
            params.append(filters['date_from'])

        if filters.get('date_to'):
            where_clauses.append("r.return_date <= ?")
            params.append(filters['date_to'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    count_sql = f"SELECT COUNT(*) as cnt FROM sales_returns r WHERE {where_sql}"
    total = get_count_from_sql(count_sql, params)

    offset = (page - 1) * per_page
    sql = f"""
        SELECT r.*,
               sc.name as customer_name,
               o.order_number,
               u.username as reviewer_name
        FROM sales_returns r
        LEFT JOIN sales_customers sc ON r.customer_id = sc.id
        LEFT JOIN sales_orders o ON r.order_id = o.id
        LEFT JOIN users u ON r.reviewer_id = u.id
        WHERE {where_sql}
        ORDER BY r.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        returns = rows_to_list(rows)

    return {
        'returns': returns,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }


def create_return(data: Dict) -> int:
    """Create a new return request."""
    with get_db_context() as db:
        year = datetime.now().year
        last_ret = db.execute("""
            SELECT return_number FROM sales_returns
            WHERE return_number LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f'RET-{year}%',)).fetchone()

        if last_ret:
            last_num = int(last_ret['return_number'].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        return_number = f"RET-{year}-{new_num:05d}"

        cursor = db.execute("""
            INSERT INTO sales_returns (
                return_number, return_date, customer_id, order_id, invoice_id,
                part_number, brand, returned_quantity, item_condition,
                return_reason, inspection_required, reviewer_id,
                review_result, final_decision, financial_impact,
                status, closure_status, notes, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            return_number,
            data.get('return_date', datetime.now().strftime('%Y-%m-%d')),
            data.get('customer_id'),
            data.get('order_id'),
            data.get('invoice_id'),
            data.get('part_number'),
            data.get('brand'),
            data.get('returned_quantity'),
            data.get('item_condition'),
            data.get('return_reason'),
            data.get('inspection_required', 0),
            data.get('reviewer_id'),
            data.get('review_result'),
            data.get('final_decision'),
            data.get('financial_impact'),
            data.get('status', 'New'),
            data.get('closure_status', 'Open'),
            data.get('notes'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


# =============================================================================
# SALES TARGETS & COMMISSIONS
# =============================================================================

def get_sales_targets(filters: Dict = None) -> List[Dict]:
    """Get sales targets with filters."""
    where_clauses = []
    params = []

    if filters:
        if filters.get('period'):
            where_clauses.append("st.period = ?")
            params.append(filters['period'])

        if filters.get('salesperson_id'):
            where_clauses.append("st.salesperson_id = ?")
            params.append(filters['salesperson_id'])

        if filters.get('year'):
            where_clauses.append("st.year = ?")
            params.append(filters['year'])

        if filters.get('quarter'):
            where_clauses.append("st.quarter = ?")
            params.append(filters['quarter'])

        if filters.get('month'):
            where_clauses.append("st.month = ?")
            params.append(filters['month'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    sql = f"""
        SELECT st.*,
               u.username as salesperson_name,
               COALESCE((SELECT SUM(total_amount) FROM sales_orders WHERE assigned_salesperson_id = st.salesperson_id
                        AND strftime('%Y', order_date) = st.year
                        AND (st.period = 'Yearly' OR st.period = 'Quarterly' AND strftime('%m', order_date) IN ('01','02','03') AND st.quarter = 1
                             OR st.period = 'Quarterly' AND strftime('%m', order_date) IN ('04','05','06') AND st.quarter = 2
                             OR st.period = 'Quarterly' AND strftime('%m', order_date) IN ('07','08','09') AND st.quarter = 3
                             OR st.period = 'Quarterly' AND strftime('%m', order_date) IN ('10','11','12') AND st.quarter = 4
                             OR st.period = 'Monthly' AND strftime('%m', order_date) = LPAD(st.month, 2, '0'))), 0) as achieved_amount
        FROM sales_targets st
        LEFT JOIN users u ON st.salesperson_id = u.id
        WHERE {where_sql}
        ORDER BY st.year DESC, st.period, st.salesperson_id
    """

    return get_all(sql, params)


def create_sales_target(data: Dict) -> int:
    """Create a new sales target."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO sales_targets (
                salesperson_id, period, year, quarter, month,
                target_amount, target_quantity, new_customer_target,
                reactivation_target, brand_target, product_group_target,
                local_target, export_target, weight_amount, weight_quantity,
                weight_new_customers, weight_reactivation, status, notes, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('salesperson_id'),
            data.get('period', 'Monthly'),
            data.get('year', datetime.now().year),
            data.get('quarter'),
            data.get('month'),
            data.get('target_amount', 0),
            data.get('target_quantity', 0),
            data.get('new_customer_target', 0),
            data.get('reactivation_target', 0),
            data.get('brand_target'),
            data.get('product_group_target'),
            data.get('local_target'),
            data.get('export_target'),
            data.get('weight_amount', 100),
            data.get('weight_quantity', 0),
            data.get('weight_new_customers', 0),
            data.get('weight_reactivation', 0),
            data.get('status', 'Active'),
            data.get('notes'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


# =============================================================================
# CONTRACTS & SALES DOCUMENTS
# =============================================================================

def get_sales_contracts(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get paginated list of sales contracts."""
    where_clauses = []
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(c.contract_number LIKE ? OR sc.name LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term])

        if filters.get('status'):
            where_clauses.append("c.status = ?")
            params.append(filters['status'])

        if filters.get('customer_id'):
            where_clauses.append("c.customer_id = ?")
            params.append(filters['customer_id'])

        if filters.get('contract_type'):
            where_clauses.append("c.contract_type = ?")
            params.append(filters['contract_type'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    count_sql = f"SELECT COUNT(*) as cnt FROM sales_contracts c WHERE {where_sql}"
    total = get_count_from_sql(count_sql, params)

    offset = (page - 1) * per_page
    sql = f"""
        SELECT c.*,
               sc.name as customer_name,
               u.username as owner_name
        FROM sales_contracts c
        LEFT JOIN sales_customers sc ON c.customer_id = sc.id
        LEFT JOIN users u ON c.contract_owner_id = u.id
        WHERE {where_sql}
        ORDER BY c.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        contracts = rows_to_list(rows)

    return {
        'contracts': contracts,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }


def create_sales_contract(data: Dict) -> int:
    """Create a new sales contract."""
    with get_db_context() as db:
        year = datetime.now().year
        last_con = db.execute("""
            SELECT contract_number FROM sales_contracts
            WHERE contract_number LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f'CON-{year}%',)).fetchone()

        if last_con:
            last_num = int(last_con['contract_number'].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        contract_number = f"CON-{year}-{new_num:05d}"

        cursor = db.execute("""
            INSERT INTO sales_contracts (
                contract_number, customer_id, start_date, end_date,
                contract_type, product_group, brand, pricing_terms,
                payment_terms, delivery_terms, volume_commitment,
                agreed_discounts, sla_terms, attachment_path,
                contract_owner_id, status, notes, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            contract_number,
            data.get('customer_id'),
            data.get('start_date'),
            data.get('end_date'),
            data.get('contract_type'),
            data.get('product_group'),
            data.get('brand'),
            data.get('pricing_terms'),
            data.get('payment_terms'),
            data.get('delivery_terms'),
            data.get('volume_commitment'),
            data.get('agreed_discounts'),
            data.get('sla_terms'),
            data.get('attachment_path'),
            data.get('contract_owner_id'),
            data.get('status', 'Active'),
            data.get('notes'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


# =============================================================================
# SALES ACTIVITIES & CRM
# =============================================================================

def get_sales_activities(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get paginated list of sales activities."""
    where_clauses = []
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(sa.subject LIKE ? OR sc.name LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term])

        if filters.get('activity_type'):
            where_clauses.append("sa.activity_type = ?")
            params.append(filters['activity_type'])

        if filters.get('customer_id'):
            where_clauses.append("sa.customer_id = ?")
            params.append(filters['customer_id'])

        if filters.get('owner_id'):
            where_clauses.append("sa.owner_id = ?")
            params.append(filters['owner_id'])

        if filters.get('reference_type'):
            where_clauses.append("sa.reference_type = ?")
            params.append(filters['reference_type'])

        if filters.get('date_from'):
            where_clauses.append("sa.activity_date >= ?")
            params.append(filters['date_from'])

        if filters.get('date_to'):
            where_clauses.append("sa.activity_date <= ?")
            params.append(filters['date_to'])

        if filters.get('status'):
            where_clauses.append("sa.status = ?")
            params.append(filters['status'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    count_sql = f"SELECT COUNT(*) as cnt FROM sales_activities sa WHERE {where_sql}"
    total = get_count_from_sql(count_sql, params)

    offset = (page - 1) * per_page
    sql = f"""
        SELECT sa.*,
               u.username as owner_name,
               sc.name as customer_name
        FROM sales_activities sa
        LEFT JOIN users u ON sa.owner_id = u.id
        LEFT JOIN sales_customers sc ON sa.customer_id = sc.id
        WHERE {where_sql}
        ORDER BY sa.activity_date DESC, sa.activity_time DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        activities = rows_to_list(rows)

    return {
        'activities': activities,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    }


def create_sales_activity(data: Dict) -> int:
    """Create a new sales activity."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO sales_activities (
                activity_type, activity_date, activity_time, customer_id,
                owner_id, subject, result, next_action, next_follow_up_date,
                status, notes, reference_type, reference_id, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('activity_type'),
            data.get('activity_date', datetime.now().strftime('%Y-%m-%d')),
            data.get('activity_time', datetime.now().strftime('%H:%M')),
            data.get('customer_id'),
            data.get('owner_id'),
            data.get('subject'),
            data.get('result'),
            data.get('next_action'),
            data.get('next_follow_up_date'),
            data.get('status', 'Completed'),
            data.get('notes'),
            data.get('reference_type'),
            data.get('reference_id'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


# =============================================================================
# PRICING & PRICE LISTS
# =============================================================================

def get_price_lists(filters: Dict = None) -> List[Dict]:
    """Get price lists."""
    where_clauses = []
    params = []

    if filters:
        if filters.get('price_list_type'):
            where_clauses.append("pl.price_list_type = ?")
            params.append(filters['price_list_type'])

        if filters.get('is_active'):
            where_clauses.append("pl.is_active = 1")

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    sql = f"""
        SELECT pl.*,
               u.username as created_by_name
        FROM sales_price_lists pl
        LEFT JOIN users u ON pl.created_by = u.id
        WHERE {where_sql}
        ORDER BY pl.name
    """

    return get_all(sql, params)


def get_price_list_items(price_list_id: int) -> List[Dict]:
    """Get items in a price list."""
    return get_all("""
        SELECT pli.*, p.name as part_name, p.description as part_description
        FROM sales_price_list_items pli
        LEFT JOIN parts p ON pli.part_number = p.part_number
        WHERE pli.price_list_id = ?
        ORDER BY pli.brand, pli.part_number
    """, (price_list_id,))


def get_special_prices(customer_id: int = None, part_number: str = None, brand: str = None) -> List[Dict]:
    """Get special prices for customer/item."""
    where_clauses = ["sp.is_active = 1", "sp.approved = 1", "sp.valid_from <= CURRENT_DATE", "sp.valid_until >= CURRENT_DATE"]
    params = []

    if customer_id:
        where_clauses.append("sp.customer_id = ?")
        params.append(customer_id)

    if part_number:
        where_clauses.append("sp.part_number = ?")
        params.append(part_number)

    if brand:
        where_clauses.append("sp.brand = ?")
        params.append(brand)

    where_sql = " AND ".join(where_clauses)

    return get_all(f"""
        SELECT sp.*, sc.name as customer_name, u.username as approved_by_name
        FROM sales_special_prices sp
        LEFT JOIN sales_customers sc ON sp.customer_id = sc.id
        LEFT JOIN users u ON sp.approved_by = u.id
        WHERE {where_sql}
        ORDER BY sp.valid_from DESC
    """, params)


def create_special_price_request(data: Dict) -> int:
    """Create a special price request."""
    with get_db_context() as db:
        year = datetime.now().year
        last_req = db.execute("""
            SELECT request_number FROM sales_special_price_requests
            WHERE request_number LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f'SPR-{year}%',)).fetchone()

        if last_req:
            last_num = int(last_req['request_number'].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        request_number = f"SPR-{year}-{new_num:05d}"

        cursor = db.execute("""
            INSERT INTO sales_special_price_requests (
                request_number, customer_id, salesperson_id, part_number, brand,
                quantity, standard_price, proposed_price, requested_discount,
                reason, urgency, status, notes, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request_number,
            data.get('customer_id'),
            data.get('salesperson_id'),
            data.get('part_number'),
            data.get('brand'),
            data.get('quantity'),
            data.get('standard_price'),
            data.get('proposed_price'),
            data.get('requested_discount'),
            data.get('reason'),
            data.get('urgency', 'Normal'),
            data.get('status', 'Pending'),
            data.get('notes'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


# =============================================================================
# DASHBOARD STATISTICS
# =============================================================================

def get_sales_dashboard_stats(salesperson_id: int = None, date_from: str = None, date_to: str = None) -> Dict:
    """Get dashboard statistics for sales."""
    today = datetime.now().strftime('%Y-%m-%d')
    current_month_start = datetime.now().strftime('%Y-%m-01')

    # Build date filters
    date_filter = ""
    date_params = []
    if date_from:
        date_filter += " AND order_date >= ?"
        date_params.append(date_from)
    if date_to:
        date_filter += " AND order_date <= ?"
        date_params.append(date_to)

    month_filter = f" AND order_date >= '{current_month_start}' AND order_date <= '{today}'"
    today_filter = f" AND order_date = '{today}'"

    # Basic counts
    stats = {}

    with get_db_context() as db:
        # Today's inquiries
        result = db.execute(f"""
            SELECT COUNT(*) as cnt FROM sales_inquiries
            WHERE DATE(created_at) = ?
        """, (today,)).fetchone()
        stats['today_inquiries'] = result['cnt'] if result else 0

        # Today's quotations
        result = db.execute(f"""
            SELECT COUNT(*) as cnt FROM sales_quotations
            WHERE DATE(created_at) = ?
        """, (today,)).fetchone()
        stats['today_quotations'] = result['cnt'] if result else 0

        # Today's orders
        result = db.execute(f"""
            SELECT COUNT(*) as cnt FROM sales_orders
            WHERE DATE(order_date) = ? {date_filter}
        """, [today] + date_params).fetchone()
        stats['today_orders'] = result['cnt'] if result else 0

        # Today's sales amount
        result = db.execute(f"""
            SELECT COALESCE(SUM(total_amount), 0) as total FROM sales_orders
            WHERE DATE(order_date) = ? {date_filter}
        """, [today] + date_params).fetchone()
        stats['today_sales_amount'] = float(result['total']) if result else 0

        # Month sales amount
        result = db.execute(f"""
            SELECT COALESCE(SUM(total_amount), 0) as total FROM sales_orders
            WHERE order_date >= ? AND order_date <= ? {date_filter}
        """, [current_month_start, today] + date_params).fetchone()
        stats['month_sales_amount'] = float(result['total']) if result else 0

        # Active customers
        result = db.execute("""
            SELECT COUNT(*) as cnt FROM sales_customers WHERE is_active = 1
        """).fetchone()
        stats['active_customers'] = result['cnt'] if result else 0

        # Inactive customers
        result = db.execute("""
            SELECT COUNT(*) as cnt FROM sales_customers WHERE is_active = 0 OR status = 'Inactive'
        """).fetchone()
        stats['inactive_customers'] = result['cnt'] if result else 0

        # Open orders
        result = db.execute(f"""
            SELECT COUNT(*) as cnt FROM sales_orders
            WHERE status NOT IN ('Delivered', 'Cancelled', 'Closed') {date_filter}
        """, date_params).fetchone()
        stats['open_orders'] = result['cnt'] if result else 0

        # Delayed orders
        result = db.execute(f"""
            SELECT COUNT(*) as cnt FROM sales_orders
            WHERE status = 'Delayed' {date_filter}
        """, date_params).fetchone()
        stats['delayed_orders'] = result['cnt'] if result else 0

        # Returns count
        result = db.execute(f"""
            SELECT COUNT(*) as cnt FROM sales_returns
            WHERE DATE(return_date) >= ? {date_filter}
        """, [current_month_start] + date_params).fetchone()
        stats['returns_count'] = result['cnt'] if result else 0

        # Open opportunities value
        result = db.execute("""
            SELECT COALESCE(SUM(estimated_value * success_probability / 100), 0) as total
            FROM sales_opportunities
            WHERE stage NOT IN ('Won', 'Lost', 'On Hold')
        """).fetchone()
        stats['open_opportunities_value'] = float(result['total']) if result else 0

        # Quotations awaiting response
        result = db.execute("""
            SELECT COUNT(*) as cnt FROM sales_quotations
            WHERE status IN ('Sent', 'Viewed', 'In Negotiation')
        """).fetchone()
        stats['pending_quotations'] = result['cnt'] if result else 0

        # Sales by salesperson (top 5)
        stats['sales_by_salesperson'] = rows_to_list(db.execute("""
            SELECT u.username as salesperson,
                   COALESCE(SUM(o.total_amount), 0) as total_sales
            FROM users u
            LEFT JOIN sales_orders o ON u.id = o.assigned_salesperson_id
                AND o.order_date >= ? AND o.order_date <= ?
            WHERE u.role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%')
            GROUP BY u.id
            ORDER BY total_sales DESC
            LIMIT 5
        """, (current_month_start, today)).fetchall())

        # Sales by customer (top 5)
        stats['sales_by_customer'] = rows_to_list(db.execute("""
            SELECT sc.name as customer,
                   COALESCE(SUM(o.total_amount), 0) as total_sales
            FROM sales_customers sc
            LEFT JOIN sales_orders o ON sc.id = o.customer_id
                AND o.order_date >= ? AND o.order_date <= ?
            GROUP BY sc.id
            ORDER BY total_sales DESC
            LIMIT 5
        """, (current_month_start, today)).fetchall())

        # Best selling brands
        stats['best_selling_brands'] = rows_to_list(db.execute("""
            SELECT brand, COUNT(*) as order_count, SUM(ordered_quantity) as total_qty
            FROM sales_order_lines
            WHERE order_id IN (SELECT id FROM sales_orders WHERE order_date >= ? AND order_date <= ?)
            GROUP BY brand
            ORDER BY total_qty DESC
            LIMIT 5
        """, (current_month_start, today)).fetchall())

    return stats


def get_salesperson_performance(salesperson_id: int, period: str = 'monthly') -> Dict:
    """Get detailed performance metrics for a salesperson."""
    today = datetime.now()
    if period == 'monthly':
        period_start = today.strftime('%Y-%m-01')
    elif period == 'quarterly':
        quarter = (today.month - 1) // 3 + 1
        period_start = today.replace(month=(quarter - 1) * 3 + 1, day=1).strftime('%Y-%m-%d')
    else:
        period_start = today.strftime('%Y-01-01')

    with get_db_context() as db:
        # Orders and sales
        orders = db.execute("""
            SELECT
                COUNT(*) as total_orders,
                COALESCE(SUM(total_amount), 0) as total_sales,
                COALESCE(AVG(total_amount), 0) as avg_order_value
            FROM sales_orders
            WHERE assigned_salesperson_id = ? AND order_date >= ?
        """, (salesperson_id, period_start)).fetchone()

        # Quotations
        quotations = db.execute("""
            SELECT
                COUNT(*) as total_quotations,
                COALESCE(SUM(total_amount), 0) as total_quotation_value,
                COALESCE(SUM(CASE WHEN status = 'Converted' THEN 1 ELSE 0 END), 0) as converted
            FROM sales_quotations
            WHERE assigned_salesperson_id = ? AND quotation_date >= ?
        """, (salesperson_id, period_start)).fetchone()

        # Inquiries
        inquiries = db.execute("""
            SELECT COUNT(*) as total_inquiries
            FROM sales_inquiries
            WHERE assigned_salesperson_id = ? AND inquiry_date >= ?
        """, (salesperson_id, period_start)).fetchone()

        # New customers
        new_customers = db.execute("""
            SELECT COUNT(*) as new_customers
            FROM sales_customers
            WHERE assigned_salesperson_id = ? AND created_at >= ?
        """, (salesperson_id, period_start)).fetchone()

        # Active opportunities
        opportunities = db.execute("""
            SELECT
                COUNT(*) as total,
                COALESCE(SUM(estimated_value), 0) as total_value
            FROM sales_opportunities
            WHERE assigned_salesperson_id = ? AND stage NOT IN ('Won', 'Lost')
        """, (salesperson_id,)).fetchone()

        return {
            'orders': dict(orders) if orders else {},
            'quotations': dict(quotations) if quotations else {},
            'inquiries': dict(inquiries) if inquiries else {},
            'new_customers': dict(new_customers) if new_customers else {},
            'opportunities': dict(opportunities) if opportunities else {},
            'period_start': period_start,
            'period_end': today.strftime('%Y-%m-%d')
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_count_from_sql(sql: str, params: List = None) -> int:
    """Execute a count SQL and return the count."""
    result = get_one(sql, params)
    return result['cnt'] if result and 'cnt' in result else 0


def get_next_document_number(prefix: str, table: str, column: str) -> str:
    """Generate next document number with prefix and zero-padded sequence."""
    year = datetime.now().year
    with get_db_context() as db:
        last_num = db.execute(f"""
            SELECT {column} FROM {table}
            WHERE {column} LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f'{prefix}-{year}%',)).fetchone()

        if last_num:
            last_seq = int(last_num[column].split('-')[-1])
            new_num = last_seq + 1
        else:
            new_num = 1

        return f"{prefix}-{year}-{new_num:05d}"


# =============================================================================
# LOOKUP DATA
# =============================================================================

def get_inquiry_sources() -> List[str]:
    """Get standard inquiry sources."""
    return ['Call', 'WhatsApp', 'Email', 'Walk-in', 'Website', 'Social Media', 'Referral', 'Exhibition', 'Cold Visit']


def get_inquiry_statuses() -> List[str]:
    """Get standard inquiry statuses."""
    return ['New', 'Under Review', 'Need Pricing', 'Need Stock Check', 'Responded',
            'In Negotiation', 'Converted to Quotation', 'Converted to Order', 'Lost', 'Closed']


def get_opportunity_stages() -> List[str]:
    """Get standard opportunity stages."""
    return ['Identified', 'Initial Contact', 'Qualification', 'Quotation Sent',
            'Negotiation', 'Terms Review', 'Pending Approval', 'Won', 'Lost', 'On Hold']


def get_quotation_statuses() -> List[str]:
    """Get standard quotation statuses."""
    return ['Draft', 'Sent', 'Viewed', 'In Negotiation', 'Revised', 'Approved', 'Rejected', 'Expired', 'Converted to Order']


def get_order_statuses() -> List[str]:
    """Get standard order statuses."""
    return ['Registered', 'Pending Approval', 'Pending Payment', 'Pending Reservation',
            'In Preparation', 'Ready for Delivery', 'Partially Delivered', 'Fully Delivered', 'Delayed', 'Cancelled']


def get_reservation_statuses() -> List[str]:
    """Get standard reservation statuses."""
    return ['Active', 'Expired', 'Released', 'Converted to Order', 'Cancelled']


def get_delivery_statuses() -> List[str]:
    """Get standard delivery statuses."""
    return ['Pending', 'Waiting for Packing', 'Ready for Dispatch', 'Dispatched',
            'In Transit', 'Delivered', 'Partially Delivered', 'Failed', 'Returned']


def get_return_reasons() -> List[str]:
    """Get standard return reasons."""
    return ['Wrong Part Number', 'Wrong Brand', 'Shortage', 'Damage', 'Price Mismatch',
            'Long Delay', 'Customer No Longer Needs', 'Quality Issue', 'Delivery Mistake', 'Other']


def get_return_statuses() -> List[str]:
    """Get standard return statuses."""
    return ['New', 'Under Review', 'Approved', 'Rejected', 'Inspection Needed', 'Closed']


def get_activity_types() -> List[str]:
    """Get standard activity types."""
    return ['Call', 'WhatsApp', 'Email', 'Visit', 'Meeting', 'Demo', 'Proposal Sent', 'Follow-up', 'Note']


def get_contract_types() -> List[str]:
    """Get standard contract types."""
    return ['Master Service Agreement', 'Supply Contract', 'Framework Agreement', 'Spot Purchase', 'Annual Contract', 'Project Contract']


def get_target_periods() -> List[str]:
    """Get target period types."""
    return ['Monthly', 'Quarterly', 'Seasonal', 'Yearly']
