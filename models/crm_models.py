"""
CRM Extended Models Module
==========================
Enterprise CRM data access layer extending sales_models.py.
Provides advanced CRM functionality including:
- Lead Management with scoring and lifecycle
- Customer 360 with contacts, hierarchy, and journey
- Opportunity lifecycle with probability forecasting
- Activity tracking with engagement scoring
- Complaint and service case management
- Key Account Management
- Contract lifecycle management
- Customer journey and intelligence tracking
- Forecasting and target tracking
- CRM audit trail

Usage:
    from crm_models import (
        get_leads, create_lead, score_lead,
        get_customer_360, get_journey_timeline,
        get_forecasts, get_crm_dashboard_stats,
        # ... etc
    )
"""

from database import get_db_context, get_one, get_all, row_to_dict, rows_to_list, get_count
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import json


# =============================================================================
# CRM CONFIGURATION & LOOKUPS
# =============================================================================

CRM_LEAD_SOURCES = [
    'Website', 'Phone Inquiry', 'Walk-in', 'Referral', 'Partner',
    'Social Media', 'Email Campaign', 'Trade Show', 'Google Ads',
    'LinkedIn', 'Facebook', 'Instagram', 'Other'
]

CRM_LEAD_STATUSES = [
    'New', 'Contacted', 'Qualified', 'Unqualified', 'In Progress',
    'Converted', 'Lost', 'On Hold'
]

CRM_LEAD_PRIORITIES = ['Low', 'Medium', 'High', 'Urgent']

CRM_LEAD_QUALIFICATION_CRITERIA = [
    'Budget', 'Authority', 'Timeline', 'Need', 'Fit'
]

CRM_OPPORTUNITY_STAGES = [
    'Identified', 'Qualified', 'Proposal', 'Negotiation',
    'Committed', 'Won', 'Lost', 'On Hold', 'Cancelled'
]

CRM_ACTIVITY_TYPES = [
    'Call', 'Meeting', 'Visit', 'Email', 'Task', 'Note', 'Demo', 'Proposal Sent'
]

CRM_JOURNEY_STAGES = [
    'Awareness', 'Consideration', 'Decision', 'Purchase', 'Retention', 'Advocacy'
]

CRM_COMPLAINT_STATUSES = [
    'New', 'In Progress', 'Pending Customer', 'Escalated', 'Resolved', 'Closed'
]

CRM_COMPLAINT_PRIORITIES = ['Low', 'Medium', 'High', 'Critical']

CRM_COMPLAINT_CATEGORIES = [
    'Product Quality', 'Delivery Issue', 'Pricing', 'Service', 'Billing',
    'Technical Support', 'Other'
]

CRM_CONTRACT_STATUSES = [
    'Draft', 'Pending Approval', 'Active', 'Expiring Soon',
    'Expired', 'Terminated', 'Renewed'
]

CRM_ACCOUNT_TIERS = ['Standard', 'Preferred', 'Key Account', 'Strategic', 'Premium']

CRM_CHURN_RISK_LEVELS = ['Low', 'Medium', 'High', 'Critical']

CRM_ENGAGEMENT_SCORES = ['Very Low', 'Low', 'Medium', 'High', 'Very High']


def get_crm_lookups() -> Dict:
    """Get all CRM lookup values."""
    return {
        'lead_sources': CRM_LEAD_SOURCES,
        'lead_statuses': CRM_LEAD_STATUSES,
        'lead_priorities': CRM_LEAD_PRIORITIES,
        'qualification_criteria': CRM_LEAD_QUALIFICATION_CRITERIA,
        'opportunity_stages': CRM_OPPORTUNITY_STAGES,
        'activity_types': CRM_ACTIVITY_TYPES,
        'journey_stages': CRM_JOURNEY_STAGES,
        'complaint_statuses': CRM_COMPLAINT_STATUSES,
        'complaint_priorities': CRM_COMPLAINT_PRIORITIES,
        'complaint_categories': CRM_COMPLAINT_CATEGORIES,
        'contract_statuses': CRM_CONTRACT_STATUSES,
        'account_tiers': CRM_ACCOUNT_TIERS,
        'churn_risk_levels': CRM_CHURN_RISK_LEVELS,
        'engagement_scores': CRM_ENGAGEMENT_SCORES
    }


# =============================================================================
# LEAD MANAGEMENT
# =============================================================================

def get_leads(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """
    Get paginated list of leads with advanced filters.
    """
    where_clauses = []
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(l.lead_number LIKE ? OR l.company_name LIKE ? OR l.contact_name LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term, search_term])

        if filters.get('status'):
            where_clauses.append("l.status = ?")
            params.append(filters['status'])

        if filters.get('source'):
            where_clauses.append("l.source = ?")
            params.append(filters['source'])

        if filters.get('priority'):
            where_clauses.append("l.priority = ?")
            params.append(filters['priority'])

        if filters.get('score_min'):
            where_clauses.append("l.lead_score >= ?")
            params.append(filters['score_min'])

        if filters.get('score_max'):
            where_clauses.append("l.lead_score <= ?")
            params.append(filters['score_max'])

        if filters.get('assigned_to'):
            where_clauses.append("l.assigned_to = ?")
            params.append(filters['assigned_to'])

        if filters.get('date_from'):
            where_clauses.append("l.created_at >= ?")
            params.append(filters['date_from'])

        if filters.get('date_to'):
            where_clauses.append("l.created_at <= ?")
            params.append(filters['date_to'])

        if filters.get('is_hot'):
            where_clauses.append("l.is_hot = 1")

        if filters.get('age_days'):
            where_clauses.append("l.age_days > ?")
            params.append(filters['age_days'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    count_sql = f"SELECT COUNT(*) as cnt FROM crm_leads l WHERE {where_sql}"
    with get_db_context() as db:
        total = db.execute(count_sql, params).fetchone()['cnt']

    offset = (page - 1) * per_page
    sql = f"""
        SELECT l.*,
               u.username as assigned_to_name,
               sc.name as converted_customer_name
        FROM crm_leads l
        LEFT JOIN users u ON l.assigned_to = u.id
        LEFT JOIN sales_customers sc ON l.converted_customer_id = sc.id
        WHERE {where_sql}
        ORDER BY l.is_hot DESC, l.lead_score DESC, l.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        leads = rows_to_list(rows)

    return {
        'leads': leads,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page if total > 0 else 1
    }


def get_lead_by_id(lead_id: int) -> Optional[Dict]:
    """Get a single lead with full details."""
    lead = get_one("""
        SELECT l.*,
               u.username as assigned_to_name
        FROM crm_leads l
        LEFT JOIN users u ON l.assigned_to = u.id
        WHERE l.id = ?
    """, (lead_id,))

    if lead:
        # Get lead contacts
        lead['contacts'] = get_all("""
            SELECT * FROM crm_lead_contacts WHERE lead_id = ?
            ORDER BY is_primary DESC, id ASC
        """, (lead_id,))

        # Get lead activities
        lead['activities'] = get_all("""
            SELECT a.*, u.username as owner_name
            FROM crm_lead_activities a
            LEFT JOIN users u ON a.owner_id = u.id
            WHERE a.lead_id = ?
            ORDER BY a.activity_date DESC
            LIMIT 20
        """, (lead_id,))

        # Get lead notes
        lead['notes'] = get_all("""
            SELECT * FROM crm_lead_notes WHERE lead_id = ?
            ORDER BY created_at DESC
        """, (lead_id,))

        # Get qualification scores
        lead['qualifications'] = get_all("""
            SELECT * FROM crm_lead_qualifications WHERE lead_id = ?
        """, (lead_id,))

        # Get conversion history
        lead['conversion_history'] = get_all("""
            SELECT * FROM crm_lead_conversion_log WHERE lead_id = ?
            ORDER BY converted_at DESC
        """, (lead_id,))

    return lead


def create_lead(data: Dict) -> int:
    """Create a new lead with auto-generated lead number."""
    with get_db_context() as db:
        year = datetime.now().year
        last_lead = db.execute("""
            SELECT lead_number FROM crm_leads
            WHERE lead_number LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f'LEAD-{year}%',)).fetchone()

        if last_lead:
            last_num = int(last_lead['lead_number'].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        lead_number = f"LEAD-{year}-{new_num:05d}"

        cursor = db.execute("""
            INSERT INTO crm_leads (
                lead_number, company_name, contact_name, contact_title,
                phone, whatsapp, email, website,
                source, status, priority, is_hot,
                industry, employee_count, annual_revenue,
                address, city, country,
                assigned_to, estimated_value, currency,
                notes, company_id, lead_score, age_days
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead_number,
            data.get('company_name'),
            data.get('contact_name'),
            data.get('contact_title'),
            data.get('phone'),
            data.get('whatsapp'),
            data.get('email'),
            data.get('website'),
            data.get('source', 'Website'),
            data.get('status', 'New'),
            data.get('priority', 'Medium'),
            1 if data.get('is_hot') else 0,
            data.get('industry'),
            data.get('employee_count'),
            data.get('annual_revenue'),
            data.get('address'),
            data.get('city'),
            data.get('country'),
            data.get('assigned_to'),
            data.get('estimated_value', 0),
            data.get('currency', 'AED'),
            data.get('notes'),
            data.get('company_id'),
            calculate_lead_score(data),
            0
        ))
        db.commit()
        return cursor.lastrowid


def update_lead(lead_id: int, data: Dict) -> bool:
    """Update an existing lead."""
    fields = []
    params = []

    updatable_fields = [
        'company_name', 'contact_name', 'contact_title', 'phone', 'whatsapp',
        'email', 'website', 'source', 'status', 'priority', 'is_hot',
        'industry', 'employee_count', 'annual_revenue', 'address', 'city',
        'country', 'assigned_to', 'estimated_value', 'currency', 'notes'
    ]

    for field in updatable_fields:
        if field in data:
            fields.append(f"{field} = ?")
            if field == 'is_hot':
                params.append(1 if data[field] else 0)
            else:
                params.append(data[field])

    if not fields:
        return False

    # Recalculate score if relevant fields changed
    if any(f in data for f in ['priority', 'source', 'estimated_value', 'status']):
        lead = get_lead_by_id(lead_id)
        if lead:
            combined_data = {**lead, **data}
            fields.append("lead_score = ?")
            params.append(calculate_lead_score(combined_data))

    fields.append("updated_at = CURRENT_TIMESTAMP")
    params.append(lead_id)

    sql = f"UPDATE crm_leads SET {', '.join(fields)} WHERE id = ?"

    with get_db_context() as db:
        db.execute(sql, params)
        db.commit()
        return True


def calculate_lead_score(lead_data: Dict) -> int:
    """
    Calculate lead score based on multiple factors.
    Future: Replace with ML model for AI-powered scoring.
    """
    score = 50  # Base score

    # Priority scoring
    priority_scores = {'Low': 0, 'Medium': 10, 'High': 20, 'Urgent': 30}
    score += priority_scores.get(lead_data.get('priority', 'Medium'), 0)

    # Source scoring
    source_scores = {
        'Referral': 25, 'Partner': 20, 'Trade Show': 15,
        'Website': 10, 'Phone Inquiry': 10, 'Walk-in': 10,
        'Social Media': 5, 'Email Campaign': 5, 'Google Ads': 5,
        'LinkedIn': 15, 'Facebook': 5, 'Instagram': 5, 'Other': 0
    }
    score += source_scores.get(lead_data.get('source', 'Other'), 0)

    # Estimated value scoring
    est_value = lead_data.get('estimated_value', 0)
    if est_value > 100000:
        score += 30
    elif est_value > 50000:
        score += 20
    elif est_value > 10000:
        score += 10
    elif est_value > 0:
        score += 5

    # Status adjustment
    status_scores = {
        'New': 5, 'Contacted': 10, 'Qualified': 20,
        'Unqualified': -20, 'In Progress': 15, 'Converted': 30,
        'Lost': -50, 'On Hold': -10
    }
    score += status_scores.get(lead_data.get('status', 'New'), 0)

    # Hot lead bonus
    if lead_data.get('is_hot'):
        score += 20

    # Industry presence
    if lead_data.get('industry'):
        score += 5

    return max(0, min(100, score))  # Clamp between 0-100


def add_lead_contact(lead_id: int, contact_data: Dict) -> int:
    """Add a contact to a lead."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO crm_lead_contacts (
                lead_id, name, title, department, phone, email,
                is_primary, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead_id,
            contact_data.get('name'),
            contact_data.get('title'),
            contact_data.get('department'),
            contact_data.get('phone'),
            contact_data.get('email'),
            1 if contact_data.get('is_primary') else 0,
            contact_data.get('notes')
        ))
        db.commit()
        return cursor.lastrowid


def log_lead_activity(lead_id: int, activity_data: Dict) -> int:
    """Log an activity for a lead."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO crm_lead_activities (
                lead_id, activity_type, subject, activity_date,
                duration_minutes, outcome, next_follow_up, owner_id, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead_id,
            activity_data.get('activity_type'),
            activity_data.get('subject'),
            activity_data.get('activity_date', datetime.now().strftime('%Y-%m-%d')),
            activity_data.get('duration_minutes'),
            activity_data.get('outcome'),
            activity_data.get('next_follow_up'),
            activity_data.get('owner_id'),
            activity_data.get('notes')
        ))
        db.commit()
        return cursor.lastrowid


def qualify_lead(lead_id: int, criteria: Dict) -> bool:
    """Score lead qualification criteria."""
    with get_db_context() as db:
        for criterion, score in criteria.items():
            db.execute("""
                INSERT OR REPLACE INTO crm_lead_qualifications (
                    lead_id, criterion, score, evaluated_at
                ) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (lead_id, criterion, score))
        db.commit()

        # Update lead score based on qualification
        total_score = sum(criteria.values()) if criteria else 0
        db.execute("""
            UPDATE crm_leads SET lead_score = lead_score + ?,
            status = CASE WHEN ? >= 4 THEN 'Qualified' ELSE status END
            WHERE id = ?
        """, (total_score, total_score, lead_id))
        db.commit()
        return True


def convert_lead_to_customer(lead_id: int, conversion_data: Dict) -> int:
    """Convert a lead to a customer."""
    from sales_models import create_sales_customer

    lead = get_lead_by_id(lead_id)
    if not lead:
        return None

    # Create customer from lead
    customer_data = {
        'name': lead['company_name'],
        'customer_type': conversion_data.get('customer_type', 'Retail'),
        'phone': lead['phone'],
        'whatsapp': lead['whatsapp'],
        'email': lead['email'],
        'address': lead['address'],
        'city': lead['city'],
        'country': lead['country'],
        'assigned_salesperson_id': lead['assigned_to'],
        'notes': f"Converted from Lead {lead['lead_number']}",
        'company_id': lead['company_id']
    }

    customer_id = create_sales_customer(customer_data)

    # Log conversion
    with get_db_context() as db:
        db.execute("""
            INSERT INTO crm_lead_conversion_log (
                lead_id, converted_to, converted_customer_id,
                converted_at, conversion_notes
            ) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (lead_id, 'customer', customer_id, conversion_data.get('notes')))

        db.execute("""
            UPDATE crm_leads SET status = 'Converted',
            converted_customer_id = ?, converted_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (customer_id, lead_id))
        db.commit()

    return customer_id


def convert_lead_to_opportunity(lead_id: int, opp_data: Dict) -> int:
    """Convert a lead to an opportunity."""
    from sales_models import create_opportunity

    lead = get_lead_by_id(lead_id)
    if not lead:
        return None

    opportunity_data = {
        'customer_id': None,  # Will be linked after customer conversion
        'customer_name': lead['company_name'],
        'assigned_salesperson_id': lead['assigned_to'],
        'source': lead['source'],
        'estimated_value': opp_data.get('estimated_value', lead.get('estimated_value', 0)),
        'success_probability': opp_data.get('probability', 20),
        'expected_close_date': opp_data.get('expected_close_date'),
        'stage': 'Identified',
        'notes': f"Converted from Lead {lead['lead_number']}",
        'company_id': lead['company_id']
    }

    opportunity_id = create_opportunity(opportunity_data)

    # Log conversion
    with get_db_context() as db:
        db.execute("""
            INSERT INTO crm_lead_conversion_log (
                lead_id, converted_to, converted_opportunity_id,
                converted_at, conversion_notes
            ) VALUES (?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (lead_id, 'opportunity', opportunity_id, opp_data.get('notes')))

        db.execute("""
            UPDATE crm_leads SET status = 'Converted',
            converted_opportunity_id = ?, converted_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (opportunity_id, lead_id))
        db.commit()

    return opportunity_id


# =============================================================================
# CUSTOMER 360
# =============================================================================

def get_customer_360(customer_id: int) -> Optional[Dict]:
    """
    Get comprehensive 360-degree view of a customer.
    Includes all interactions, history, and intelligence.
    """
    # Basic customer info
    customer = get_one("""
        SELECT sc.*,
               u.username as assigned_salesperson_name,
               c.name as country_name
        FROM sales_customers sc
        LEFT JOIN users u ON sc.assigned_salesperson_id = u.id
        LEFT JOIN countries c ON sc.country = c.code
        WHERE sc.id = ?
    """, (customer_id,))

    if not customer:
        return None

    # Get contacts
    customer['contacts'] = get_all("""
        SELECT * FROM crm_customer_contacts
        WHERE customer_id = ?
        ORDER BY is_primary DESC, id ASC
    """, (customer_id,))

    # Get customer hierarchy (parent/child)
    customer['hierarchy'] = get_all("""
        SELECT * FROM crm_customer_hierarchy
        WHERE customer_id = ? OR related_customer_id = ?
    """, (customer_id, customer_id))

    # Get segment assignments
    customer['segments'] = get_all("""
        SELECT cs.*, csg.name as segment_name, csg.description as segment_description
        FROM crm_customer_segments cs
        LEFT JOIN crm_segments csg ON cs.segment_id = csg.id
        WHERE cs.customer_id = ?
    """, (customer_id,))

    # Get financial summary
    customer['financials'] = get_one("""
        SELECT
            COALESCE(SUM(CASE WHEN transaction_type = 'Invoice' THEN amount ELSE 0 END), 0) as total_invoiced,
            COALESCE(SUM(CASE WHEN transaction_type = 'Payment' THEN amount ELSE 0 END), 0) as total_paid,
            COALESCE(SUM(CASE WHEN transaction_type = 'Credit' THEN amount ELSE 0 END), 0) as total_credits,
            COALESCE(SUM(CASE WHEN transaction_type = 'Invoice' THEN amount ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN transaction_type = 'Payment' THEN amount ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN transaction_type = 'Credit' THEN amount ELSE 0 END), 0) as outstanding_balance
        FROM sales_customer_transactions
        WHERE customer_id = ?
    """, (customer_id,)) or {'total_invoiced': 0, 'total_paid': 0, 'total_credits': 0, 'outstanding_balance': 0}

    # Get credit risk
    customer['credit_risk'] = get_one("""
        SELECT * FROM crm_customer_credit_risk WHERE customer_id = ?
    """, (customer_id,))

    # Get open opportunities
    customer['opportunities'] = get_all("""
        SELECT * FROM sales_opportunities
        WHERE customer_id = ? AND stage NOT IN ('Won', 'Lost', 'Cancelled')
        ORDER BY created_at DESC
    """, (customer_id,))

    # Get open quotations
    customer['quotations'] = get_all("""
        SELECT * FROM sales_quotations
        WHERE customer_id = ? AND status NOT IN ('Accepted', 'Rejected', 'Expired')
        ORDER BY created_at DESC
    """, (customer_id,))

    # Get open orders
    customer['orders'] = get_all("""
        SELECT * FROM sales_orders
        WHERE customer_id = ? AND status NOT IN ('Delivered', 'Cancelled')
        ORDER BY created_at DESC
    """, (customer_id,))

    # Get recent activities
    customer['activities'] = get_all("""
        SELECT sa.*, u.username as owner_name
        FROM sales_activities sa
        LEFT JOIN users u ON sa.owner_id = u.id
        WHERE sa.customer_id = ?
        ORDER BY sa.activity_date DESC
        LIMIT 20
    """, (customer_id,))

    # Get journey timeline
    customer['journey_timeline'] = get_all("""
        SELECT * FROM crm_journey_events
        WHERE customer_id = ?
        ORDER BY event_date DESC
        LIMIT 50
    """, (customer_id,))

    # Get complaints
    customer['complaints'] = get_all("""
        SELECT * FROM crm_complaints
        WHERE customer_id = ?
        ORDER BY created_at DESC
    """, (customer_id,))

    # Get contracts
    customer['contracts'] = get_all("""
        SELECT * FROM sales_contracts
        WHERE customer_id = ?
        ORDER BY created_at DESC
    """, (customer_id,))

    # Get engagement score
    customer['engagement_score'] = calculate_customer_engagement_score(customer_id)

    # Get churn risk
    customer['churn_risk'] = calculate_churn_risk(customer_id)

    # Get key account info
    customer['key_account'] = get_one("""
        SELECT * FROM crm_key_accounts WHERE customer_id = ?
    """, (customer_id,))

    return customer


def calculate_customer_engagement_score(customer_id: int) -> Dict:
    """Calculate customer engagement score based on recent activities."""
    score = 50  # Base score
    level = 'Medium'

    # Count recent activities (last 90 days)
    recent_count = get_count("""
        SELECT COUNT(*) FROM sales_activities
        WHERE customer_id = ? AND activity_date >= ?
    """, (customer_id, (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')))

    # Count recent orders (last 90 days)
    recent_orders = get_count("""
        SELECT COUNT(*) FROM sales_orders
        WHERE customer_id = ? AND order_date >= ?
    """, (customer_id, (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')))

    # Count recent quotations (last 90 days)
    recent_quotes = get_count("""
        SELECT COUNT(*) FROM sales_quotations
        WHERE customer_id = ? AND quotation_date >= ?
    """, (customer_id, (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')))

    # Calculate score
    score += recent_count * 2  # Activities weighted
    score += recent_orders * 10  # Orders heavily weighted
    score += recent_quotes * 5  # Quotes moderately weighted

    # Determine level
    if score >= 80:
        level = 'Very High'
    elif score >= 60:
        level = 'High'
    elif score >= 40:
        level = 'Medium'
    elif score >= 20:
        level = 'Low'
    else:
        level = 'Very Low'

    return {
        'score': min(100, score),
        'level': level,
        'recent_activities': recent_count,
        'recent_orders': recent_orders,
        'recent_quotations': recent_quotes
    }


def calculate_churn_risk(customer_id: int) -> Dict:
    """Calculate customer churn risk based on multiple factors."""
    risk_score = 0
    factors = []

    # Check last purchase date
    customer = get_one("""
        SELECT last_purchase_date FROM sales_customers WHERE id = ?
    """, (customer_id,))

    if customer and customer.get('last_purchase_date'):
        days_since = (datetime.now() - datetime.strptime(customer['last_purchase_date'], '%Y-%m-%d')).days

        if days_since > 180:
            risk_score += 40
            factors.append({'factor': 'No purchase in 6+ months', 'impact': 'High'})
        elif days_since > 90:
            risk_score += 25
            factors.append({'factor': 'No purchase in 3+ months', 'impact': 'Medium'})
        elif days_since > 60:
            risk_score += 10
            factors.append({'factor': 'No purchase in 2 months', 'impact': 'Low'})

    # Check outstanding balance vs credit limit
    balance_info = get_one("""
        SELECT sc.credit_limit, COALESCE(SUM(CASE WHEN transaction_type = 'Invoice' THEN amount ELSE 0 END), 0) -
               COALESCE(SUM(CASE WHEN transaction_type = 'Payment' THEN amount ELSE 0 END), 0) as balance
        FROM sales_customers sc
        LEFT JOIN sales_customer_transactions sct ON sc.id = sct.customer_id
        WHERE sc.id = ?
        GROUP BY sc.id
    """, (customer_id,))

    if balance_info:
        if balance_info['credit_limit'] > 0:
            utilization = balance_info['balance'] / balance_info['credit_limit']
            if utilization > 0.9:
                risk_score += 30
                factors.append({'factor': 'Credit limit nearly maxed', 'impact': 'High'})
            elif utilization > 0.7:
                risk_score += 15
                factors.append({'factor': 'High credit utilization', 'impact': 'Medium'})

    # Check engagement score
    engagement = calculate_customer_engagement_score(customer_id)
    if engagement['level'] in ['Very Low', 'Low']:
        risk_score += 20
        factors.append({'factor': 'Low engagement', 'impact': 'Medium'})

    # Check for open complaints
    open_complaints = get_count("""
        SELECT COUNT(*) FROM crm_complaints
        WHERE customer_id = ? AND status NOT IN ('Resolved', 'Closed')
    """, (customer_id,))
    if open_complaints > 2:
        risk_score += 25
        factors.append({'factor': 'Multiple open complaints', 'impact': 'High'})
    elif open_complaints > 0:
        risk_score += 10
        factors.append({'factor': 'Has open complaints', 'impact': 'Low'})

    # Determine risk level
    if risk_score >= 60:
        risk_level = 'Critical'
    elif risk_score >= 40:
        risk_level = 'High'
    elif risk_score >= 20:
        risk_level = 'Medium'
    else:
        risk_level = 'Low'

    return {
        'risk_score': min(100, risk_score),
        'risk_level': risk_level,
        'factors': factors
    }


def add_customer_contact(customer_id: int, contact_data: Dict) -> int:
    """Add a contact person to a customer."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO crm_customer_contacts (
                customer_id, name, title, department, role,
                phone, whatsapp, email, is_primary, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_id,
            contact_data.get('name'),
            contact_data.get('title'),
            contact_data.get('department'),
            contact_data.get('role'),
            contact_data.get('phone'),
            contact_data.get('whatsapp'),
            contact_data.get('email'),
            1 if contact_data.get('is_primary') else 0,
            contact_data.get('notes')
        ))
        db.commit()
        return cursor.lastrowid


# =============================================================================
# OPPORTUNITY ENHANCEMENTS
# =============================================================================

def get_crm_opportunities(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get opportunities with CRM enhancements (stages, forecasting)."""
    where_clauses = []
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(opp.opportunity_number LIKE ? OR opp.customer_name LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term])

        if filters.get('stage'):
            if ',' in filters['stage']:
                stages = filters['stage'].split(',')
                placeholders = ','.join(['?' for _ in stages])
                where_clauses.append(f"opp.stage IN ({placeholders})")
                params.extend(stages)
            else:
                where_clauses.append("opp.stage = ?")
                params.append(filters['stage'])

        if filters.get('salesperson_id'):
            where_clauses.append("opp.assigned_salesperson_id = ?")
            params.append(filters['salesperson_id'])

        if filters.get('source'):
            where_clauses.append("opp.source = ?")
            params.append(filters['source'])

        if filters.get('market'):
            where_clauses.append("opp.market = ?")
            params.append(filters['market'])

        if filters.get('probability_min'):
            where_clauses.append("opp.success_probability >= ?")
            params.append(filters['probability_min'])

        if filters.get('value_min'):
            where_clauses.append("opp.estimated_value >= ?")
            params.append(filters['value_min'])

        if filters.get('date_from'):
            where_clauses.append("opp.created_at >= ?")
            params.append(filters['date_from'])

        if filters.get('date_to'):
            where_clauses.append("opp.created_at <= ?")
            params.append(filters['date_to'])

        if filters.get('stage_not'):
            where_clauses.append("opp.stage NOT IN (?, ?)")
            params.extend(['Won', 'Lost'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    with get_db_context() as db:
        total = db.execute(f"SELECT COUNT(*) as cnt FROM sales_opportunities opp WHERE {where_sql}", params).fetchone()['cnt']

    offset = (page - 1) * per_page
    sql = f"""
        SELECT opp.*,
               u.username as assigned_salesperson_name,
               sc.name as customer_name,
               (opp.estimated_value * opp.success_probability / 100.0) as weighted_value
        FROM sales_opportunities opp
        LEFT JOIN users u ON opp.assigned_salesperson_id = u.id
        LEFT JOIN sales_customers sc ON opp.customer_id = sc.id
        WHERE {where_sql}
        ORDER BY weighted_value DESC, opp.created_at DESC
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
        'pages': (total + per_page - 1) // per_page if total > 0 else 1
    }


def get_opportunity_pipeline_summary() -> Dict:
    """Get pipeline summary by stage with values."""
    sql = """
        SELECT
            stage,
            COUNT(*) as count,
            SUM(estimated_value) as total_value,
            AVG(success_probability) as avg_probability,
            SUM(estimated_value * success_probability / 100.0) as weighted_value
        FROM sales_opportunities
        WHERE stage NOT IN ('Won', 'Lost', 'Cancelled')
        GROUP BY stage
        ORDER BY
            CASE stage
                WHEN 'Identified' THEN 1
                WHEN 'Qualified' THEN 2
                WHEN 'Proposal' THEN 3
                WHEN 'Negotiation' THEN 4
                WHEN 'Committed' THEN 5
                ELSE 6
            END
    """
    stages = get_all(sql)

    # Calculate totals
    total_value = sum(s.get('total_value', 0) for s in stages)
    total_weighted = sum(s.get('weighted_value', 0) for s in stages)

    return {
        'stages': stages,
        'total_value': total_value,
        'total_weighted_value': total_weighted,
        'stage_count': len(stages)
    }


# =============================================================================
# ACTIVITY MANAGEMENT
# =============================================================================

def get_crm_activities(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get CRM activities with enhanced filtering."""
    where_clauses = []
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(sa.subject LIKE ? OR sa.notes LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term])

        if filters.get('activity_type'):
            where_clauses.append("sa.activity_type = ?")
            params.append(filters['activity_type'])

        if filters.get('owner_id'):
            where_clauses.append("sa.owner_id = ?")
            params.append(filters['owner_id'])

        if filters.get('customer_id'):
            where_clauses.append("sa.customer_id = ?")
            params.append(filters['customer_id'])

        if filters.get('reference_type'):
            where_clauses.append("sa.reference_type = ?")
            params.append(filters['reference_type'])

        if filters.get('reference_id'):
            where_clauses.append("sa.reference_id = ?")
            params.append(filters['reference_id'])

        if filters.get('date_from'):
            where_clauses.append("sa.activity_date >= ?")
            params.append(filters['date_from'])

        if filters.get('date_to'):
            where_clauses.append("sa.activity_date <= ?")
            params.append(filters['date_to'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    with get_db_context() as db:
        total = db.execute(f"SELECT COUNT(*) as cnt FROM sales_activities sa WHERE {where_sql}", params).fetchone()['cnt']

    offset = (page - 1) * per_page
    sql = f"""
        SELECT sa.*,
               u.username as owner_name,
               sc.name as customer_name
        FROM sales_activities sa
        LEFT JOIN users u ON sa.owner_id = u.id
        LEFT JOIN sales_customers sc ON sa.customer_id = sc.id
        WHERE {where_sql}
        ORDER BY sa.activity_date DESC, sa.id DESC
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
        'pages': (total + per_page - 1) // per_page if total > 0 else 1
    }


def create_crm_activity(activity_data: Dict) -> int:
    """Create a new CRM activity."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO sales_activities (
                activity_type, subject, activity_date, duration_minutes,
                customer_id, reference_type, reference_id,
                owner_id, outcome, next_follow_up, notes,
                company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            activity_data.get('activity_type'),
            activity_data.get('subject'),
            activity_data.get('activity_date', datetime.now().strftime('%Y-%m-%d')),
            activity_data.get('duration_minutes'),
            activity_data.get('customer_id'),
            activity_data.get('reference_type'),
            activity_data.get('reference_id'),
            activity_data.get('owner_id'),
            activity_data.get('outcome'),
            activity_data.get('next_follow_up'),
            activity_data.get('notes'),
            activity_data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


# =============================================================================
# COMPLAINTS & SERVICE CASES
# =============================================================================

def get_complaints(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get customer complaints with filters."""
    where_clauses = []
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(c.complaint_number LIKE ? OR c.subject LIKE ? OR sc.name LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term, search_term])

        if filters.get('status'):
            where_clauses.append("c.status = ?")
            params.append(filters['status'])

        if filters.get('priority'):
            where_clauses.append("c.priority = ?")
            params.append(filters['priority'])

        if filters.get('category'):
            where_clauses.append("c.category = ?")
            params.append(filters['category'])

        if filters.get('customer_id'):
            where_clauses.append("c.customer_id = ?")
            params.append(filters['customer_id'])

        if filters.get('assigned_to'):
            where_clauses.append("c.assigned_to = ?")
            params.append(filters['assigned_to'])

        if filters.get('date_from'):
            where_clauses.append("c.created_at >= ?")
            params.append(filters['date_from'])

        if filters.get('date_to'):
            where_clauses.append("c.created_at <= ?")
            params.append(filters['date_to'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    with get_db_context() as db:
        total = db.execute(f"SELECT COUNT(*) as cnt FROM crm_complaints c WHERE {where_sql}", params).fetchone()['cnt']

    offset = (page - 1) * per_page
    sql = f"""
        SELECT c.*,
               u.username as assigned_to_name,
               sc.name as customer_name
        FROM crm_complaints c
        LEFT JOIN users u ON c.assigned_to = u.id
        LEFT JOIN sales_customers sc ON c.customer_id = sc.id
        WHERE {where_sql}
        ORDER BY
            CASE c.priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,
            c.created_at DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        complaints = rows_to_list(rows)

    return {
        'complaints': complaints,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page if total > 0 else 1
    }


def get_complaint_by_id(complaint_id: int) -> Optional[Dict]:
    """Get complaint details with timeline."""
    complaint = get_one("""
        SELECT c.*,
               u.username as assigned_to_name,
               sc.name as customer_name, sc.phone as customer_phone, sc.email as customer_email
        FROM crm_complaints c
        LEFT JOIN users u ON c.assigned_to = u.id
        LEFT JOIN sales_customers sc ON c.customer_id = sc.id
        WHERE c.id = ?
    """, (complaint_id,))

    if complaint:
        # Get timeline
        complaint['timeline'] = get_all("""
            SELECT * FROM crm_complaint_timeline
            WHERE complaint_id = ?
            ORDER BY created_at ASC
        """, (complaint_id,))

        # Get linked orders/deliveries
        if complaint.get('order_id'):
            complaint['order'] = get_one("SELECT * FROM sales_orders WHERE id = ?", (complaint['order_id'],))
        if complaint.get('delivery_id'):
            complaint['delivery'] = get_one("SELECT * FROM sales_deliveries WHERE id = ?", (complaint['delivery_id'],))

    return complaint


def create_complaint(data: Dict) -> int:
    """Create a new customer complaint."""
    with get_db_context() as db:
        year = datetime.now().year
        last_cmp = db.execute("""
            SELECT complaint_number FROM crm_complaints
            WHERE complaint_number LIKE ?
            ORDER BY id DESC LIMIT 1
        """, (f'CMP-{year}%',)).fetchone()

        if last_cmp:
            last_num = int(last_cmp['complaint_number'].split('-')[-1])
            new_num = last_num + 1
        else:
            new_num = 1

        complaint_number = f"CMP-{year}-{new_num:05d}"

        cursor = db.execute("""
            INSERT INTO crm_complaints (
                complaint_number, customer_id, order_id, delivery_id,
                category, priority, status, subject, description,
                assigned_to, resolution_target_date, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            complaint_number,
            data.get('customer_id'),
            data.get('order_id'),
            data.get('delivery_id'),
            data.get('category'),
            data.get('priority', 'Medium'),
            data.get('status', 'New'),
            data.get('subject'),
            data.get('description'),
            data.get('assigned_to'),
            data.get('resolution_target_date'),
            data.get('company_id')
        ))
        db.commit()
        complaint_id = cursor.lastrowid

        # Log creation in timeline
        db.execute("""
            INSERT INTO crm_complaint_timeline (
                complaint_id, event_type, description, created_by
            ) VALUES (?, 'Created', ?, ?)
        """, (complaint_id, f"Complaint created: {data.get('subject')}", data.get('assigned_to')))
        db.commit()

        return complaint_id


def update_complaint_status(complaint_id: int, status: str, notes: str = None, user_id: int = None) -> bool:
    """Update complaint status with timeline logging."""
    with get_db_context() as db:
        db.execute("""
            UPDATE crm_complaints SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, complaint_id))

        db.execute("""
            INSERT INTO crm_complaint_timeline (
                complaint_id, event_type, description, created_by
            ) VALUES (?, 'Status Changed', ?, ?)
        """, (complaint_id, f"Status changed to {status}. {notes or ''}", user_id))
        db.commit()
        return True


def add_complaint_response(complaint_id: int, response_data: Dict) -> int:
    """Add a response to a complaint."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO crm_complaint_timeline (
                complaint_id, event_type, description, created_by
            ) VALUES (?, 'Response', ?, ?)
        """, (
            complaint_id,
            response_data.get('description'),
            response_data.get('created_by')
        ))
        db.commit()
        return cursor.lastrowid


# =============================================================================
# KEY ACCOUNT MANAGEMENT
# =============================================================================

def get_key_accounts(filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
    """Get key accounts with filters."""
    where_clauses = []
    params = []

    if filters:
        if filters.get('search'):
            where_clauses.append("(ka.account_name LIKE ? OR sc.name LIKE ?)")
            search_term = f"%{filters['search']}%"
            params.extend([search_term, search_term])

        if filters.get('tier'):
            where_clauses.append("ka.tier = ?")
            params.append(filters['tier'])

        if filters.get('account_manager_id'):
            where_clauses.append("ka.account_manager_id = ?")
            params.append(filters['account_manager_id'])

    where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

    with get_db_context() as db:
        total = db.execute(f"SELECT COUNT(*) as cnt FROM crm_key_accounts ka WHERE {where_sql}", params).fetchone()['cnt']

    offset = (page - 1) * per_page
    sql = f"""
        SELECT ka.*,
               u.username as account_manager_name,
               sc.name as customer_name, sc.total_revenue, sc.total_orders
        FROM crm_key_accounts ka
        LEFT JOIN users u ON ka.account_manager_id = u.id
        LEFT JOIN sales_customers sc ON ka.customer_id = sc.id
        WHERE {where_sql}
        ORDER BY ka.tier ASC, sc.total_revenue DESC
        LIMIT ? OFFSET ?
    """
    params.extend([per_page, offset])

    with get_db_context() as db:
        rows = db.execute(sql, params).fetchall()
        accounts = rows_to_list(rows)

    return {
        'accounts': accounts,
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page if total > 0 else 1
    }


def create_key_account(data: Dict) -> int:
    """Create a key account."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO crm_key_accounts (
                customer_id, account_name, tier, account_manager_id,
                account_type, business_objectives, success_metrics,
                last_review_date, next_review_date, company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get('customer_id'),
            data.get('account_name'),
            data.get('tier', 'Key Account'),
            data.get('account_manager_id'),
            data.get('account_type'),
            data.get('business_objectives'),
            data.get('success_metrics'),
            data.get('last_review_date'),
            data.get('next_review_date'),
            data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def get_account_plan(account_id: int) -> Optional[Dict]:
    """Get account plan with objectives."""
    account = get_one("""
        SELECT ka.*,
               u.username as account_manager_name,
               sc.name as customer_name
        FROM crm_key_accounts ka
        LEFT JOIN users u ON ka.account_manager_id = u.id
        LEFT JOIN sales_customers sc ON ka.customer_id = sc.id
        WHERE ka.id = ?
    """, (account_id,))

    if account:
        account['objectives'] = get_all("""
            SELECT * FROM crm_account_objectives
            WHERE account_id = ?
            ORDER BY target_date ASC
        """, (account_id,))

        account['reviews'] = get_all("""
            SELECT * FROM crm_account_reviews
            WHERE account_id = ?
            ORDER BY review_date DESC
        """, (account_id,))

        account['relationship_map'] = get_all("""
            SELECT * FROM crm_relationship_map
            WHERE account_id = ?
        """, (account_id,))

    return account


# =============================================================================
# FORECASTING & TARGETS
# =============================================================================

def get_crm_forecasts(filters: Dict = None) -> Dict:
    """Get sales forecasts by various dimensions."""
    # Monthly forecast
    monthly_sql = """
        SELECT
            strftime('%Y-%m', expected_close_date) as month,
            stage,
            COUNT(*) as opportunity_count,
            SUM(estimated_value) as total_value,
            SUM(estimated_value * success_probability / 100.0) as weighted_value
        FROM sales_opportunities
        WHERE expected_close_date IS NOT NULL
        AND stage NOT IN ('Lost', 'Cancelled')
    """

    params = []
    if filters:
        if filters.get('salesperson_id'):
            monthly_sql += " AND assigned_salesperson_id = ?"
            params.append(filters['salesperson_id'])
        if filters.get('date_from'):
            monthly_sql += " AND expected_close_date >= ?"
            params.append(filters['date_from'])
        if filters.get('date_to'):
            monthly_sql += " AND expected_close_date <= ?"
            params.append(filters['date_to'])

    monthly_sql += " GROUP BY month, stage ORDER BY month ASC"

    monthly_forecast = get_all(monthly_sql, params)

    # Aggregate by month
    monthly_totals = {}
    for row in monthly_forecast:
        month = row['month']
        if month not in monthly_totals:
            monthly_totals[month] = {
                'month': month,
                'total_value': 0,
                'weighted_value': 0,
                'count': 0
            }
        monthly_totals[month]['total_value'] += row['total_value']
        monthly_totals[month]['weighted_value'] += row['weighted_value']
        monthly_totals[month]['count'] += row['opportunity_count']

    # Get targets
    target_sql = """
        SELECT * FROM sales_targets
        WHERE 1=1
    """
    target_params = []
    if filters:
        if filters.get('salesperson_id'):
            target_sql += " AND salesperson_id = ?"
            target_params.append(filters['salesperson_id'])
        if filters.get('year'):
            target_sql += " AND target_year = ?"
            target_params.append(filters['year'])
        if filters.get('quarter'):
            target_sql += " AND target_quarter = ?"
            target_params.append(filters['quarter'])

    targets = get_all(target_sql, target_params)

    return {
        'monthly_forecast': list(monthly_totals.values()),
        'stage_breakdown': monthly_forecast,
        'targets': targets
    }


def get_salesperson_forecast(salesperson_id: int, year: int = None, quarter: int = None) -> Dict:
    """Get individual salesperson forecast vs target."""
    if year is None:
        year = datetime.now().year

    # Get salesperson's targets
    targets = get_all("""
        SELECT * FROM sales_targets
        WHERE salesperson_id = ? AND target_year = ?
        ORDER BY target_quarter ASC
    """, (salesperson_id, year))

    # Get actual sales by month
    actuals = get_all("""
        SELECT
            strftime('%Y-%m', order_date) as month,
            SUM(total_amount) as actual_sales
        FROM sales_orders
        WHERE assigned_salesperson_id = ?
        AND strftime('%Y', order_date) = ?
        AND status NOT IN ('Cancelled')
        GROUP BY month
    """, (salesperson_id, str(year)))

    # Build monthly comparison
    monthly_data = {}
    for target in targets:
        for month in range(1, 13):
            month_key = f"{year}-{month:02d}"
            if month_key not in monthly_data:
                monthly_data[month_key] = {'month': month_key, 'target': 0, 'actual': 0}

            q = target.get('target_quarter')
            if q:
                q_months = {1: [1, 2, 3], 2: [4, 5, 6], 3: [7, 8, 9], 4: [10, 11, 12]}.get(q, [])
                if month in q_months:
                    monthly_data[month_key]['target'] += target.get('monthly_target', 0)

    for actual in actuals:
        if actual['month'] in monthly_data:
            monthly_data[actual['month']]['actual'] = actual['actual_sales']

    return {
        'year': year,
        'targets': targets,
        'monthly_data': list(monthly_data.values())
    }


# =============================================================================
# CUSTOMER JOURNEY
# =============================================================================

def get_customer_journey(customer_id: int) -> Dict:
    """Get customer journey with all touchpoints."""
    # Get all journey events
    events = get_all("""
        SELECT * FROM crm_journey_events
        WHERE customer_id = ?
        ORDER BY event_date ASC
    """, (customer_id,))

    # Get customer stage history
    stages = get_all("""
        SELECT * FROM crm_customer_stage_history
        WHERE customer_id = ?
        ORDER BY entered_at DESC
    """, (customer_id,))

    # Get touchpoints
    touchpoints = get_all("""
        SELECT * FROM crm_touchpoints
        WHERE customer_id = ?
        ORDER BY touchpoint_date DESC
    """, (customer_id,))

    # Current stage
    current_stage = stages[0] if stages else None

    return {
        'events': events,
        'stages': stages,
        'touchpoints': touchpoints,
        'current_stage': current_stage,
        'journey_length_days': calculate_journey_length(events)
    }


def log_journey_event(customer_id: int, event_data: Dict) -> int:
    """Log a journey event."""
    with get_db_context() as db:
        cursor = db.execute("""
            INSERT INTO crm_journey_events (
                customer_id, event_type, event_date,
                channel, description, reference_type, reference_id,
                company_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_id,
            event_data.get('event_type'),
            event_data.get('event_date', datetime.now().strftime('%Y-%m-%d')),
            event_data.get('channel'),
            event_data.get('description'),
            event_data.get('reference_type'),
            event_data.get('reference_id'),
            event_data.get('company_id')
        ))
        db.commit()
        return cursor.lastrowid


def calculate_journey_length(events: List[Dict]) -> int:
    """Calculate total journey length in days."""
    if not events:
        return 0

    first_event = events[0]
    last_event = events[-1]

    try:
        first_date = datetime.strptime(first_event['event_date'], '%Y-%m-%d')
        last_date = datetime.strptime(last_event['event_date'], '%Y-%m-%d')
        return (last_date - first_date).days
    except:
        return 0


# =============================================================================
# CRM DASHBOARD STATS
# =============================================================================

def get_crm_dashboard_stats(salesperson_id: int = None, date_from: str = None, date_to: str = None) -> Dict:
    """Get comprehensive CRM dashboard statistics."""
    params = []
    where_clause = "1=1"

    if salesperson_id:
        where_clause += " AND assigned_to = ?"
        params.append(salesperson_id)

    # Lead stats
    lead_stats = get_one("""
        SELECT
            COUNT(*) as total_leads,
            SUM(CASE WHEN status = 'New' THEN 1 ELSE 0 END) as new_leads,
            SUM(CASE WHEN status = 'Qualified' THEN 1 ELSE 0 END) as qualified_leads,
            SUM(CASE WHEN status = 'Converted' THEN 1 ELSE 0 END) as converted_leads,
            SUM(CASE WHEN status = 'Lost' THEN 1 ELSE 0 END) as lost_leads,
            SUM(CASE WHEN is_hot = 1 THEN 1 ELSE 0 END) as hot_leads,
            AVG(lead_score) as avg_lead_score
        FROM crm_leads
        WHERE 1=1
        {date_filter}
    """.format(date_filter=f" AND created_at >= '{date_from}'" if date_from else ""))

    # Opportunity stats
    opp_stats = get_one("""
        SELECT
            COUNT(*) as total_opportunities,
            SUM(CASE WHEN stage NOT IN ('Won', 'Lost', 'Cancelled') THEN 1 ELSE 0 END) as open_opportunities,
            SUM(CASE WHEN stage = 'Won' THEN 1 ELSE 0 END) as won_opportunities,
            SUM(CASE WHEN stage = 'Lost' THEN 1 ELSE 0 END) as lost_opportunities,
            SUM(CASE WHEN stage NOT IN ('Won', 'Lost', 'Cancelled') THEN estimated_value ELSE 0 END) as pipeline_value,
            SUM(CASE WHEN stage = 'Won' THEN estimated_value ELSE 0 END) as won_value,
            AVG(success_probability) as avg_probability
        FROM sales_opportunities
        WHERE 1=1
        {date_filter}
    """.format(date_filter=f" AND created_at >= '{date_from}'" if date_from else ""))

    # Activity stats
    activity_stats = get_one("""
        SELECT
            COUNT(*) as total_activities,
            SUM(CASE WHEN activity_type = 'Call' THEN 1 ELSE 0 END) as calls,
            SUM(CASE WHEN activity_type = 'Meeting' THEN 1 ELSE 0 END) as meetings,
            SUM(CASE WHEN activity_type = 'Visit' THEN 1 ELSE 0 END) as visits,
            SUM(duration_minutes) as total_minutes
        FROM sales_activities
        WHERE 1=1
        {date_filter}
    """.format(date_filter=f" AND activity_date >= '{date_from}'" if date_from else ""))

    # Complaint stats
    complaint_stats = get_one("""
        SELECT
            COUNT(*) as total_complaints,
            SUM(CASE WHEN status = 'New' THEN 1 ELSE 0 END) as open_complaints,
            SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) as resolved_complaints,
            SUM(CASE WHEN priority = 'Critical' THEN 1 ELSE 0 END) as critical_complaints
        FROM crm_complaints
        WHERE 1=1
        {date_filter}
    """.format(date_filter=f" AND created_at >= '{date_from}'" if date_from else ""))

    # Pipeline by stage
    pipeline = get_all("""
        SELECT
            stage,
            COUNT(*) as count,
            SUM(estimated_value) as value
        FROM sales_opportunities
        WHERE stage NOT IN ('Won', 'Lost', 'Cancelled')
        GROUP BY stage
    """)

    # Lead sources distribution
    lead_sources = get_all("""
        SELECT source, COUNT(*) as count
        FROM crm_leads
        WHERE source IS NOT NULL
        GROUP BY source
        ORDER BY count DESC
    """)

    # Top leads
    top_leads = get_all("""
        SELECT * FROM crm_leads
        WHERE status NOT IN ('Converted', 'Lost')
        ORDER BY is_hot DESC, lead_score DESC
        LIMIT 10
    """)

    # Recent activities
    recent_activities = get_all("""
        SELECT sa.*, u.username as owner_name, sc.name as customer_name
        FROM sales_activities sa
        LEFT JOIN users u ON sa.owner_id = u.id
        LEFT JOIN sales_customers sc ON sa.customer_id = sc.id
        ORDER BY sa.created_at DESC
        LIMIT 10
    """)

    # Today's tasks/follow-ups
    today_followups = get_all("""
        SELECT sa.*, u.username as owner_name, sc.name as customer_name
        FROM sales_activities sa
        LEFT JOIN users u ON sa.owner_id = u.id
        LEFT JOIN sales_customers sc ON sa.customer_id = sc.id
        WHERE sa.next_follow_up = ?
        ORDER BY sa.created_at DESC
    """, (datetime.now().strftime('%Y-%m-%d'),))

    # Open complaints by priority
    open_complaints = get_all("""
        SELECT c.*, sc.name as customer_name
        FROM crm_complaints c
        LEFT JOIN sales_customers sc ON c.customer_id = sc.id
        WHERE c.status NOT IN ('Resolved', 'Closed')
        ORDER BY
            CASE c.priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,
            c.created_at DESC
        LIMIT 10
    """)

    return {
        'leads': lead_stats or {},
        'opportunities': opp_stats or {},
        'activities': activity_stats or {},
        'complaints': complaint_stats or {},
        'pipeline': pipeline,
        'lead_sources': lead_sources,
        'top_leads': top_leads,
        'recent_activities': recent_activities,
        'today_followups': today_followups,
        'open_complaints': open_complaints
    }


# =============================================================================
# CRM REPORTS
# =============================================================================

def get_lead_conversion_report(filters: Dict = None) -> Dict:
    """Generate lead conversion analysis report."""
    date_from = filters.get('date_from', (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d'))
    date_to = filters.get('date_to', datetime.now().strftime('%Y-%m-%d'))

    # Overall conversion
    overall = get_one("""
        SELECT
            COUNT(*) as total_leads,
            SUM(CASE WHEN status = 'Converted' THEN 1 ELSE 0 END) as converted,
            SUM(CASE WHEN status = 'Lost' THEN 1 ELSE 0 END) as lost,
            SUM(CASE WHEN status IN ('Converted', 'Lost') THEN 0 ELSE 1 END) as in_progress,
            AVG(lead_score) as avg_score_converted,
            AVG(CASE WHEN status = 'Converted' THEN lead_score END) as avg_score_converted
        FROM crm_leads
        WHERE created_at >= ? AND created_at <= ?
    """, (date_from, date_to)) or {}

    # Conversion by source
    by_source = get_all("""
        SELECT
            source,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'Converted' THEN 1 ELSE 0 END) as converted,
            AVG(CASE WHEN status = 'Converted' THEN lead_score END) as avg_score
        FROM crm_leads
        WHERE created_at >= ? AND created_at <= ?
        GROUP BY source
        ORDER BY total DESC
    """, (date_from, date_to))

    # Conversion by month
    by_month = get_all("""
        SELECT
            strftime('%Y-%m', created_at) as month,
            COUNT(*) as total,
            SUM(CASE WHEN status = 'Converted' THEN 1 ELSE 0 END) as converted,
            SUM(CASE WHEN status = 'Lost' THEN 1 ELSE 0 END) as lost
        FROM crm_leads
        WHERE created_at >= ? AND created_at <= ?
        GROUP BY month
        ORDER BY month ASC
    """, (date_from, date_to))

    # Average time to conversion
    avg_conversion_time = get_one("""
        SELECT AVG(
            julianday(converted_at) - julianday(created_at)
        ) as avg_days
        FROM crm_leads
        WHERE status = 'Converted'
        AND created_at >= ? AND created_at <= ?
    """, (date_from, date_to))

    return {
        'overall': overall,
        'by_source': by_source,
        'by_month': by_month,
        'avg_conversion_days': avg_conversion_time.get('avg_days', 0) if avg_conversion_time else 0,
        'date_range': {'from': date_from, 'to': date_to}
    }


def get_sales_pipeline_report(filters: Dict = None) -> Dict:
    """Generate pipeline analysis report."""
    # Pipeline value by stage
    by_stage = get_all("""
        SELECT
            stage,
            COUNT(*) as count,
            SUM(estimated_value) as total_value,
            AVG(success_probability) as avg_probability,
            SUM(estimated_value * success_probability / 100.0) as weighted_value,
            MIN(estimated_value) as min_value,
            MAX(estimated_value) as max_value,
            AVG(estimated_value) as avg_value
        FROM sales_opportunities
        WHERE stage NOT IN ('Won', 'Lost', 'Cancelled')
        GROUP BY stage
        ORDER BY
            CASE stage
                WHEN 'Identified' THEN 1
                WHEN 'Qualified' THEN 2
                WHEN 'Proposal' THEN 3
                WHEN 'Negotiation' THEN 4
                WHEN 'Committed' THEN 5
                ELSE 6
            END
    """)

    # Won/Lost analysis
    won_lost = get_one("""
        SELECT
            SUM(CASE WHEN stage = 'Won' THEN estimated_value ELSE 0 END) as won_value,
            SUM(CASE WHEN stage = 'Lost' THEN estimated_value ELSE 0 END) as lost_value,
            COUNT(CASE WHEN stage = 'Won' THEN 1 END) as won_count,
            COUNT(CASE WHEN stage = 'Lost' THEN 1 END) as lost_count
        FROM sales_opportunities
    """) or {}

    # Win rate
    total_closed = (won_lost.get('won_count', 0) + won_lost.get('lost_count', 0))
    win_rate = (won_lost.get('won_count', 0) / total_closed * 100) if total_closed > 0 else 0

    # Average deal size
    avg_deal_size = get_one("""
        SELECT AVG(estimated_value) as avg_deal_size
        FROM sales_opportunities
        WHERE stage = 'Won'
    """)

    # Pipeline velocity (avg days in stage)
    velocity = get_all("""
        SELECT
            stage,
            AVG(julianday(updated_at) - julianday(created_at)) as avg_days
        FROM sales_opportunities
        WHERE stage NOT IN ('Won', 'Lost', 'Cancelled')
        GROUP BY stage
    """)

    return {
        'by_stage': by_stage,
        'won_lost': won_lost,
        'win_rate': win_rate,
        'avg_deal_size': avg_deal_size.get('avg_deal_size', 0) if avg_deal_size else 0,
        'velocity': velocity
    }


def get_customer_analysis_report(filters: Dict = None) -> Dict:
    """Generate customer analysis report."""
    # Customer distribution by tier
    by_tier = get_all("""
        SELECT
            COALESCE(ka.tier, 'Standard') as tier,
            COUNT(*) as customer_count,
            SUM(sc.total_revenue) as total_revenue,
            AVG(sc.total_revenue) as avg_revenue
        FROM sales_customers sc
        LEFT JOIN crm_key_accounts ka ON sc.id = ka.customer_id
        WHERE sc.is_active = 1
        GROUP BY COALESCE(ka.tier, 'Standard')
    """)

    # Revenue by customer
    by_revenue = get_all("""
        SELECT
            sc.id, sc.name, sc.customer_code,
            sc.total_revenue, sc.total_orders, sc.last_purchase_date,
            sc.outstanding_balance, sc.credit_limit
        FROM sales_customers sc
        WHERE sc.is_active = 1
        ORDER BY sc.total_revenue DESC
        LIMIT 50
    """)

    # Churn risk distribution
    churn_risk = get_all("""
        SELECT
            risk_level,
            COUNT(*) as count
        FROM crm_customer_churn_risk
        GROUP BY risk_level
    """)

    # Engagement distribution
    engagement = get_all("""
        SELECT
            engagement_level,
            COUNT(*) as count
        FROM crm_customer_engagement
        GROUP BY engagement_level
    """)

    return {
        'by_tier': by_tier,
        'top_customers': by_revenue,
        'churn_risk': churn_risk,
        'engagement': engagement
    }


# =============================================================================
# EXPORT HELPERS
# =============================================================================

def get_exportable_leads(filters: Dict = None) -> List[Dict]:
    """Get leads data formatted for export."""
    result = get_leads(filters, page=1, per_page=10000)
    return result['leads']


def get_exportable_opportunities(filters: Dict = None) -> List[Dict]:
    """Get opportunities data formatted for export."""
    result = get_crm_opportunities(filters, page=1, per_page=10000)
    return result['opportunities']


def get_exportable_activities(filters: Dict = None) -> List[Dict]:
    """Get activities data formatted for export."""
    result = get_crm_activities(filters, page=1, per_page=10000)
    return result['activities']
