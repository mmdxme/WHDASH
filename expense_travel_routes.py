"""
Expense / Travel Management Module - Flask Routes
================================================
Comprehensive API routes covering:
- Expense Claims CRUD and Workflow
- Travel Requests CRUD and Authorization
- Cash Advances CRUD and Settlement
- Receipts Management
- Policy Enforcement
- Reimbursement Processing
- Dashboard & Analytics
- Export Functionality
- HR/Finance Integration Points

Author: Expense/Travel Module Implementation
"""

import os
import json
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import Blueprint, request, jsonify, render_template, send_file, redirect, url_for, flash, session
from werkzeug.utils import secure_filename

# Import database and utilities
from database import get_db_context, get_one, get_all, log_audit, create_notification
import permissions as perm_module
from translations import get_translation, get_language_direction, is_rtl
from navigation import get_page_title, get_breadcrumbs

# ============================================================================
# BLUEPRINT SETUP
# ============================================================================

expense_travel_bp = Blueprint('expense_travel', __name__, 
                               url_prefix='/expense-travel',
                               template_folder='templates')

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_current_user():
    """Get current user from session."""
    return session.get('user_id'), session.get('username'), session.get('role_id'), session.get('company_id')


def require_expense_permission(resource, action):
    """Decorator to check expense module permissions."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id, username, role_id, company_id = get_current_user()
            if not user_id:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please login to continue', 'warning')
                return redirect(url_for('login'))
            
            # Check module-level permission
            has_perm = perm_module.user_has_permission(user_id, 'expense_travel', resource, action)
            if not has_perm:
                if request.is_json:
                    return jsonify({'error': 'Permission denied'}), 403
                flash('You do not have permission to access this resource', 'danger')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def init_expense_travel_module():
    """Initialize the expense/travel module - called on first access."""
    try:
        from expense_travel_models import initialize_expense_travel_schema
        initialize_expense_travel_schema()
        return True
    except Exception as e:
        print(f"Error initializing expense/travel module: {e}")
        return False


def handle_uploaded_file(file, upload_folder, subfolder=''):
    """Handle file upload and return file path."""
    if not file or file.filename == '':
        return None, None
    
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    
    if subfolder:
        upload_path = os.path.join(upload_folder, subfolder)
    else:
        upload_path = upload_folder
    
    os.makedirs(upload_path, exist_ok=True)
    
    file_path = os.path.join(upload_path, unique_filename)
    file.save(file_path)
    
    file_size = os.path.getsize(file_path)
    
    return unique_filename, file_path


# ============================================================================
# DASHBOARD ROUTES
# ============================================================================

@expense_travel_bp.route('/')
@expense_travel_bp.route('/dashboard')
def dashboard():
    """Main expense/travel dashboard."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    # Get dashboard stats
    from expense_travel_models import get_expense_dashboard_stats
    stats = get_expense_dashboard_stats(
        company_id=company_id,
        user_id=user_id,
        role='employee' if role_id not in [1, 2, 3] else 'manager'
    )
    
    # Get recent claims
    from expense_travel_models import get_expense_claims
    recent_claims = get_expense_claims({'limit': 5})
    
    # Get pending approvals for current user
    from expense_travel_models import get_expense_claims, get_travel_requests, get_cash_advances
    pending_claims = get_expense_claims({
        'status': 'submitted',
        'limit': 5
    })
    pending_travel = get_travel_requests({
        'status': 'submitted',
        'limit': 5
    })
    pending_advances = get_cash_advances({
        'status': 'submitted',
        'limit': 5
    })
    
    page_title = get_page_title('expense_travel_dashboard')
    breadcrumbs = get_breadcrumbs('expense_travel', 'expense_travel_dashboard')
    
    return render_template(
        'expense_travel/dashboard.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs,
        stats=stats,
        recent_claims=recent_claims,
        pending_claims=pending_claims,
        pending_travel=pending_travel,
        pending_advances=pending_advances
    )


@expense_travel_bp.route('/executive-dashboard')
def executive_dashboard():
    """Executive expense/travel dashboard."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    from expense_travel_models import get_expense_dashboard_stats
    stats = get_expense_dashboard_stats(company_id=company_id)
    
    # Get summaries
    from expense_travel_models import get_expense_summary_by_department, get_expense_summary_by_category
    dept_summary = get_expense_summary_by_department()
    category_summary = get_expense_summary_by_category()
    
    page_title = get_page_title('expense_travel_exec_dashboard')
    breadcrumbs = get_breadcrumbs('expense_travel', 'expense_travel_exec_dashboard')
    
    return render_template(
        'expense_travel/executive_dashboard.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs,
        stats=stats,
        dept_summary=dept_summary,
        category_summary=category_summary
    )


# ============================================================================
# EXPENSE CLAIMS ROUTES
# ============================================================================

@expense_travel_bp.route('/claims')
def claims_list():
    """List all expense claims."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    # Get filter parameters
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    search = request.args.get('search', '')
    
    filters = {'limit': 50}
    if status:
        filters['status'] = status
    if date_from:
        filters['date_from'] = date_from
    if date_to:
        filters['date_to'] = date_to
    if search:
        filters['search'] = search
    
    # Role-based filtering
    if role_id not in [1, 2, 3]:  # Not admin/manager/finance
        filters['employee_id'] = user_id
    
    from expense_travel_models import get_expense_claims
    claims = get_expense_claims(filters)
    
    page_title = get_page_title('expense_claims')
    breadcrumbs = get_breadcrumbs('expense_travel', 'expense_claims')
    
    return render_template(
        'expense_travel/claims/list.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs,
        claims=claims,
        status_filter=status,
        date_from=date_from,
        date_to=date_to,
        search=search
    )


@expense_travel_bp.route('/claims/new', methods=['GET', 'POST'])
def claims_new():
    """Create new expense claim."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        data = request.form.to_dict()
        data['employee_id'] = user_id
        data['employee_code'] = username
        data['employee_name'] = username
        data['submitted_by'] = user_id
        data['submitted_by_name'] = username
        
        from expense_travel_models import create_expense_claim
        claim_id, claim_number = create_expense_claim(data)
        
        log_expense_audit('expense_claim', claim_id, 'CREATE', user_id=user_id, user_name=username,
                          notes=f"Created expense claim {claim_number}")
        
        flash(f'Expense claim {claim_number} created successfully', 'success')
        return redirect(url_for('expense_travel.claims_edit', claim_id=claim_id))
    
    # Get expense categories for form
    from expense_travel_models import get_expense_categories
    categories = get_expense_categories()
    
    page_title = get_page_title('expense_claims_new')
    breadcrumbs = get_breadcrumbs('expense_travel', 'expense_claims_new')
    
    return render_template(
        'expense_travel/claims/new.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs,
        categories=categories
    )


@expense_travel_bp.route('/claims/<int:claim_id>')
def claims_detail(claim_id):
    """View expense claim details."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    from expense_travel_models import get_expense_claim_by_id, get_expense_claim_lines
    claim = get_expense_claim_by_id(claim_id)
    
    if not claim:
        flash('Expense claim not found', 'danger')
        return redirect(url_for('expense_travel.claims_list'))
    
    # Check access
    if claim['employee_id'] != user_id and role_id not in [1, 2, 3]:
        flash('You do not have permission to view this claim', 'danger')
        return redirect(url_for('expense_travel.claims_list'))
    
    lines = get_expense_claim_lines(claim_id)
    
    # Get receipts
    from expense_travel_models import get_expense_receipts
    receipts = get_expense_receipts({'claim_id': claim_id})
    
    page_title = get_page_title('expense_claims_detail')
    breadcrumbs = get_breadcrumbs('expense_travel', 'expense_claims_detail')
    
    return render_template(
        'expense_travel/claims/detail.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs,
        claim=claim,
        lines=lines,
        receipts=receipts
    )


@expense_travel_bp.route('/claims/<int:claim_id>/edit', methods=['GET', 'POST'])
def claims_edit(claim_id):
    """Edit expense claim."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    from expense_travel_models import get_expense_claim_by_id, get_expense_claim_lines, update_expense_claim
    claim = get_expense_claim_by_id(claim_id)
    
    if not claim:
        flash('Expense claim not found', 'danger')
        return redirect(url_for('expense_travel.claims_list'))
    
    # Check access
    if claim['employee_id'] != user_id and role_id not in [1, 2, 3]:
        flash('You do not have permission to edit this claim', 'danger')
        return redirect(url_for('expense_travel.claims_list'))
    
    # Only allow editing draft claims
    if claim['status'] not in ['draft', 'returned']:
        flash('Only draft or returned claims can be edited', 'warning')
        return redirect(url_for('expense_travel.claims_detail', claim_id=claim_id))
    
    if request.method == 'POST':
        data = request.form.to_dict()
        update_expense_claim(claim_id, data)
        
        log_expense_audit('expense_claim', claim_id, 'UPDATE', user_id=user_id, user_name=username,
                          notes=f"Updated expense claim {claim['claim_number']}")
        
        flash('Expense claim updated successfully', 'success')
        return redirect(url_for('expense_travel.claims_detail', claim_id=claim_id))
    
    lines = get_expense_claim_lines(claim_id)
    
    from expense_travel_models import get_expense_categories, get_expense_receipts
    categories = get_expense_categories()
    receipts = get_expense_receipts({'claim_id': claim_id})
    
    page_title = get_page_title('expense_claims_edit')
    breadcrumbs = get_breadcrumbs('expense_travel', 'expense_claims_edit')
    
    return render_template(
        'expense_travel/claims/edit.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs,
        claim=claim,
        lines=lines,
        categories=categories,
        receipts=receipts
    )


@expense_travel_bp.route('/claims/<int:claim_id>/add-line', methods=['POST'])
def claims_add_line(claim_id):
    """Add a line item to expense claim."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        if request.is_json:
            return jsonify({'error': 'Authentication required'}), 401
        return redirect(url_for('login'))
    
    from expense_travel_models import get_expense_claim_by_id, add_expense_claim_line, update_expense_claim
    from expense_travel_models import get_expense_category_by_id
    
    claim = get_expense_claim_by_id(claim_id)
    if not claim:
        if request.is_json:
            return jsonify({'error': 'Claim not found'}), 404
        flash('Claim not found', 'danger')
        return redirect(url_for('expense_travel.claims_list'))
    
    if claim['status'] not in ['draft', 'returned']:
        if request.is_json:
            return jsonify({'error': 'Cannot add lines to submitted claim'}), 400
        flash('Cannot add lines to submitted claim', 'warning')
        return redirect(url_for('expense_travel.claims_edit', claim_id=claim_id))
    
    data = request.form.to_dict()
    
    # Get category info
    if data.get('category_id'):
        category = get_expense_category_by_id(data['category_id'])
        if category:
            data['category_code'] = category['code']
            data['category_name'] = category['name']
    
    data['claim_id'] = claim_id
    line_id = add_expense_claim_line(claim_id, data)
    
    log_expense_audit('expense_claim_line', line_id, 'CREATE', user_id=user_id, user_name=username,
                      notes=f"Added line to claim {claim['claim_number']}")
    
    if request.is_json:
        return jsonify({'success': True, 'line_id': line_id})
    
    flash('Line item added successfully', 'success')
    return redirect(url_for('expense_travel.claims_edit', claim_id=claim_id))


@expense_travel_bp.route('/claims/<int:claim_id>/submit', methods=['POST'])
def claims_submit(claim_id):
    """Submit expense claim for approval."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        if request.is_json:
            return jsonify({'error': 'Authentication required'}), 401
        return redirect(url_for('login'))
    
    from expense_travel_models import get_expense_claim_by_id, update_expense_claim
    
    claim = get_expense_claim_by_id(claim_id)
    if not claim:
        if request.is_json:
            return jsonify({'error': 'Claim not found'}), 404
        flash('Claim not found', 'danger')
        return redirect(url_for('expense_travel.claims_list'))
    
    if claim['employee_id'] != user_id:
        if request.is_json:
            return jsonify({'error': 'Permission denied'}), 403
        flash('You can only submit your own claims', 'danger')
        return redirect(url_for('expense_travel.claims_list'))
    
    if claim['status'] not in ['draft', 'returned']:
        if request.is_json:
            return jsonify({'error': 'Claim cannot be submitted'}), 400
        flash('This claim cannot be submitted', 'warning')
        return redirect(url_for('expense_travel.claims_detail', claim_id=claim_id))
    
    # Update status
    update_expense_claim(claim_id, {
        'status': 'submitted',
        'submission_date': datetime.now().strftime('%Y-%m-%d'),
        'submitted_by': user_id,
        'submitted_by_name': username
    })
    
    log_expense_audit('expense_claim', claim_id, 'SUBMIT', user_id=user_id, user_name=username,
                      notes=f"Submitted expense claim {claim['claim_number']}")
    
    # Create notification for approvers
    create_notification(
        title=f'Expense Claim Submitted: {claim["claim_number"]}',
        message=f'{username} has submitted expense claim {claim["claim_number"]} for {claim["total_amount"]} {claim["currency"]}',
        notification_type='APPROVAL',
        severity='MEDIUM',
        related_entity_type='expense_claim',
        related_entity_id=claim_id,
        company_id=company_id
    )
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Claim submitted successfully'})
    
    flash('Expense claim submitted successfully', 'success')
    return redirect(url_for('expense_travel.claims_detail', claim_id=claim_id))


@expense_travel_bp.route('/claims/<int:claim_id>/approve', methods=['POST'])
def claims_approve(claim_id):
    """Approve expense claim."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        if request.is_json:
            return jsonify({'error': 'Authentication required'}), 401
        return redirect(url_for('login'))
    
    # Check permission
    if role_id not in [1, 2, 3]:  # admin, manager, finance
        if request.is_json:
            return jsonify({'error': 'Permission denied'}), 403
        flash('You do not have permission to approve claims', 'danger')
        return redirect(url_for('expense_travel.claims_list'))
    
    from expense_travel_models import get_expense_claim_by_id, update_expense_claim
    
    claim = get_expense_claim_by_id(claim_id)
    if not claim:
        if request.is_json:
            return jsonify({'error': 'Claim not found'}), 404
        flash('Claim not found', 'danger')
        return redirect(url_for('expense_travel.claims_list'))
    
    if claim['status'] != 'submitted':
        if request.is_json:
            return jsonify({'error': 'Claim is not pending approval'}), 400
        flash('This claim is not pending approval', 'warning')
        return redirect(url_for('expense_travel.claims_detail', claim_id=claim_id))
    
    notes = request.form.get('notes', '') if request.method == 'POST' else ''
    
    update_expense_claim(claim_id, {
        'status': 'approved',
        'approved_by': user_id,
        'approved_by_name': username,
        'approval_level': 1
    })
    
    log_expense_audit('expense_claim', claim_id, 'APPROVE', user_id=user_id, user_name=username,
                      notes=f"Approved expense claim {claim['claim_number']}")
    
    # Notify employee
    create_notification(
        title=f'Expense Claim Approved: {claim["claim_number"]}',
        message=f'Your expense claim {claim["claim_number"]} has been approved',
        notification_type='SUCCESS',
        severity='LOW',
        user_id=claim['employee_id'],
        related_entity_type='expense_claim',
        related_entity_id=claim_id,
        company_id=company_id
    )
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Claim approved successfully'})
    
    flash('Expense claim approved successfully', 'success')
    return redirect(url_for('expense_travel.claims_detail', claim_id=claim_id))


@expense_travel_bp.route('/claims/<int:claim_id>/reject', methods=['POST'])
def claims_reject(claim_id):
    """Reject expense claim."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        if request.is_json:
            return jsonify({'error': 'Authentication required'}), 401
        return redirect(url_for('login'))
    
    if role_id not in [1, 2, 3]:
        if request.is_json:
            return jsonify({'error': 'Permission denied'}), 403
        flash('You do not have permission to reject claims', 'danger')
        return redirect(url_for('expense_travel.claims_list'))
    
    from expense_travel_models import get_expense_claim_by_id, update_expense_claim
    
    claim = get_expense_claim_by_id(claim_id)
    if not claim:
        if request.is_json:
            return jsonify({'error': 'Claim not found'}), 404
        flash('Claim not found', 'danger')
        return redirect(url_for('expense_travel.claims_list'))
    
    reason = request.form.get('reason', 'No reason provided')
    
    update_expense_claim(claim_id, {
        'status': 'rejected',
        'rejected_by': user_id,
        'rejected_by_name': username,
        'rejection_reason': reason
    })
    
    log_expense_audit('expense_claim', claim_id, 'REJECT', user_id=user_id, user_name=username,
                      notes=f"Rejected expense claim {claim['claim_number']}. Reason: {reason}")
    
    create_notification(
        title=f'Expense Claim Rejected: {claim["claim_number"]}',
        message=f'Your expense claim {claim["claim_number"]} has been rejected. Reason: {reason}',
        notification_type='ERROR',
        severity='MEDIUM',
        user_id=claim['employee_id'],
        related_entity_type='expense_claim',
        related_entity_id=claim_id,
        company_id=company_id
    )
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Claim rejected'})
    
    flash('Expense claim rejected', 'danger')
    return redirect(url_for('expense_travel.claims_detail', claim_id=claim_id))


# ============================================================================
# TRAVEL REQUESTS ROUTES
# ============================================================================

@expense_travel_bp.route('/travel')
def travel_list():
    """List all travel requests."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    status = request.args.get('status', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    search = request.args.get('search', '')
    
    filters = {'limit': 50}
    if status:
        filters['status'] = status
    if date_from:
        filters['date_from'] = date_from
    if date_to:
        filters['date_to'] = date_to
    if search:
        filters['search'] = search
    
    if role_id not in [1, 2, 3]:
        filters['employee_id'] = user_id
    
    from expense_travel_models import get_travel_requests
    requests = get_travel_requests(filters)
    
    page_title = get_page_title('travel_requests')
    breadcrumbs = get_breadcrumbs('expense_travel', 'travel_requests')
    
    return render_template(
        'expense_travel/travel/list.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs,
        requests=requests,
        status_filter=status,
        date_from=date_from,
        date_to=date_to,
        search=search
    )


@expense_travel_bp.route('/travel/new', methods=['GET', 'POST'])
def travel_new():
    """Create new travel request."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        data = request.form.to_dict()
        data['employee_id'] = user_id
        data['employee_code'] = username
        data['employee_name'] = username
        data['submitted_by'] = user_id
        data['submitted_by_name'] = username
        
        # Calculate trip days
        if data.get('travel_start_date') and data.get('travel_end_date'):
            start = datetime.strptime(data['travel_start_date'], '%Y-%m-%d')
            end = datetime.strptime(data['travel_end_date'], '%Y-%m-%d')
            data['total_trip_days'] = (end - start).days + 1
        
        from expense_travel_models import create_travel_request
        request_id, travel_number = create_travel_request(data)
        
        log_expense_audit('travel_request', request_id, 'CREATE', user_id=user_id, user_name=username,
                          notes=f"Created travel request {travel_number}")
        
        flash(f'Travel request {travel_number} created successfully', 'success')
        return redirect(url_for('expense_travel.travel_edit', request_id=request_id))
    
    page_title = get_page_title('travel_requests_new')
    breadcrumbs = get_breadcrumbs('expense_travel', 'travel_requests_new')
    
    return render_template(
        'expense_travel/travel/new.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs
    )


@expense_travel_bp.route('/travel/<int:request_id>')
def travel_detail(request_id):
    """View travel request details."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    from expense_travel_models import get_travel_request_by_id, get_travel_itineraries
    
    travel = get_travel_request_by_id(request_id)
    if not travel:
        flash('Travel request not found', 'danger')
        return redirect(url_for('expense_travel.travel_list'))
    
    if travel['employee_id'] != user_id and role_id not in [1, 2, 3]:
        flash('You do not have permission to view this request', 'danger')
        return redirect(url_for('expense_travel.travel_list'))
    
    itineraries = get_travel_itineraries(request_id)
    
    page_title = get_page_title('travel_requests_detail')
    breadcrumbs = get_breadcrumbs('expense_travel', 'travel_requests_detail')
    
    return render_template(
        'expense_travel/travel/detail.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs,
        travel=travel,
        itineraries=itineraries
    )


@expense_travel_bp.route('/travel/<int:request_id>/edit', methods=['GET', 'POST'])
def travel_edit(request_id):
    """Edit travel request."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    from expense_travel_models import get_travel_request_by_id, get_travel_itineraries
    
    travel = get_travel_request_by_id(request_id)
    if not travel:
        flash('Travel request not found', 'danger')
        return redirect(url_for('expense_travel.travel_list'))
    
    if travel['employee_id'] != user_id and role_id not in [1, 2, 3]:
        flash('You do not have permission to edit this request', 'danger')
        return redirect(url_for('expense_travel.travel_list'))
    
    if travel['status'] not in ['draft', 'returned']:
        flash('Only draft or returned requests can be edited', 'warning')
        return redirect(url_for('expense_travel.travel_detail', request_id=request_id))
    
    if request.method == 'POST':
        from expense_travel_models import update_travel_request

        data = request.form.to_dict()
        update_travel_request(request_id, data)

        log_expense_audit('travel_request', request_id, 'UPDATE', user_id=user_id, user_name=username,
                          notes=f"Updated travel request {travel['travel_number']}")

        flash('Travel request updated successfully', 'success')
        return redirect(url_for('expense_travel.travel_detail', request_id=request_id))
    
    itineraries = get_travel_itineraries(request_id)
    
    page_title = get_page_title('travel_requests_edit')
    breadcrumbs = get_breadcrumbs('expense_travel', 'travel_requests_edit')
    
    return render_template(
        'expense_travel/travel/edit.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs,
        travel=travel,
        itineraries=itineraries
    )


@expense_travel_bp.route('/travel/<int:request_id>/submit', methods=['POST'])
def travel_submit(request_id):
    """Submit travel request for approval."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        if request.is_json:
            return jsonify({'error': 'Authentication required'}), 401
        return redirect(url_for('login'))
    
    from expense_travel_models import get_travel_request_by_id
    
    travel = get_travel_request_by_id(request_id)
    if not travel:
        if request.is_json:
            return jsonify({'error': 'Request not found'}), 404
        flash('Request not found', 'danger')
        return redirect(url_for('expense_travel.travel_list'))
    
    if travel['employee_id'] != user_id:
        if request.is_json:
            return jsonify({'error': 'Permission denied'}), 403
        flash('You can only submit your own requests', 'danger')
        return redirect(url_for('expense_travel.travel_list'))
    
    if travel['status'] not in ['draft', 'returned']:
        if request.is_json:
            return jsonify({'error': 'Request cannot be submitted'}), 400
        flash('This request cannot be submitted', 'warning')
        return redirect(url_for('expense_travel.travel_detail', request_id=request_id))
    
    with get_db_context() as db:
        db.execute("UPDATE travel_requests SET status = 'submitted', submission_date = ? WHERE id = ?",
                   (datetime.now().strftime('%Y-%m-%d'), request_id))
        db.commit()
    
    log_expense_audit('travel_request', request_id, 'SUBMIT', user_id=user_id, user_name=username,
                      notes=f"Submitted travel request {travel['travel_number']}")
    
    create_notification(
        title=f'Travel Request Submitted: {travel["travel_number"]}',
        message=f'{username} has submitted travel request {travel["travel_number"]} for {travel["destination_city"]}',
        notification_type='APPROVAL',
        severity='MEDIUM',
        related_entity_type='travel_request',
        related_entity_id=request_id,
        company_id=company_id
    )
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Travel request submitted successfully'})
    
    flash('Travel request submitted successfully', 'success')
    return redirect(url_for('expense_travel.travel_detail', request_id=request_id))


@expense_travel_bp.route('/travel/<int:request_id>/approve', methods=['POST'])
def travel_approve(request_id):
    """Approve travel request."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        if request.is_json:
            return jsonify({'error': 'Authentication required'}), 401
        return redirect(url_for('login'))
    
    if role_id not in [1, 2, 3]:
        if request.is_json:
            return jsonify({'error': 'Permission denied'}), 403
        flash('You do not have permission to approve requests', 'danger')
        return redirect(url_for('expense_travel.travel_list'))
    
    from expense_travel_models import get_travel_request_by_id
    
    travel = get_travel_request_by_id(request_id)
    if not travel:
        if request.is_json:
            return jsonify({'error': 'Request not found'}), 404
        flash('Request not found', 'danger')
        return redirect(url_for('expense_travel.travel_list'))
    
    with get_db_context() as db:
        db.execute("""UPDATE travel_requests 
                       SET status = 'approved', approved_by = ?, approved_by_name = ?,
                           approval_date = ?, approval_level = 1
                       WHERE id = ?""",
                   (user_id, username, datetime.now().strftime('%Y-%m-%d'), request_id))
        db.commit()
    
    log_expense_audit('travel_request', request_id, 'APPROVE', user_id=user_id, user_name=username,
                      notes=f"Approved travel request {travel['travel_number']}")
    
    create_notification(
        title=f'Travel Request Approved: {travel["travel_number"]}',
        message=f'Your travel request {travel["travel_number"]} has been approved',
        notification_type='SUCCESS',
        severity='LOW',
        user_id=travel['employee_id'],
        related_entity_type='travel_request',
        related_entity_id=request_id,
        company_id=company_id
    )
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Travel request approved'})
    
    flash('Travel request approved successfully', 'success')
    return redirect(url_for('expense_travel.travel_detail', request_id=request_id))


@expense_travel_bp.route('/travel/<int:request_id>/reject', methods=['POST'])
def travel_reject(request_id):
    """Reject travel request."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        if request.is_json:
            return jsonify({'error': 'Authentication required'}), 401
        return redirect(url_for('login'))
    
    if role_id not in [1, 2, 3]:
        if request.is_json:
            return jsonify({'error': 'Permission denied'}), 403
        flash('You do not have permission to reject requests', 'danger')
        return redirect(url_for('expense_travel.travel_list'))
    
    from expense_travel_models import get_travel_request_by_id
    travel = get_travel_request_by_id(request_id)
    
    reason = request.form.get('reason', 'No reason provided')
    
    with get_db_context() as db:
        db.execute("""UPDATE travel_requests 
                       SET status = 'rejected', rejected_by = ?, rejected_by_name = ?,
                           rejection_reason = ?
                       WHERE id = ?""",
                   (user_id, username, reason, request_id))
        db.commit()
    
    log_expense_audit('travel_request', request_id, 'REJECT', user_id=user_id, user_name=username,
                      notes=f"Rejected travel request {travel['travel_number']}. Reason: {reason}")
    
    create_notification(
        title=f'Travel Request Rejected: {travel["travel_number"]}',
        message=f'Your travel request {travel["travel_number"]} has been rejected. Reason: {reason}',
        notification_type='ERROR',
        severity='MEDIUM',
        user_id=travel['employee_id'],
        related_entity_type='travel_request',
        related_entity_id=request_id,
        company_id=company_id
    )
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Travel request rejected'})
    
    flash('Travel request rejected', 'danger')
    return redirect(url_for('expense_travel.travel_detail', request_id=request_id))


# ============================================================================
# CASH ADVANCES ROUTES
# ============================================================================

@expense_travel_bp.route('/advances')
def advances_list():
    """List all cash advances."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    status = request.args.get('status', '')
    
    filters = {'limit': 50}
    if status:
        filters['status'] = status
    
    if role_id not in [1, 2, 3]:
        filters['employee_id'] = user_id
    
    from expense_travel_models import get_cash_advances
    advances = get_cash_advances(filters)
    
    page_title = get_page_title('cash_advances')
    breadcrumbs = get_breadcrumbs('expense_travel', 'cash_advances')
    
    return render_template(
        'expense_travel/advances/list.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs,
        advances=advances,
        status_filter=status
    )


@expense_travel_bp.route('/advances/new', methods=['GET', 'POST'])
def advances_new():
    """Create new cash advance request."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        data = request.form.to_dict()
        data['employee_id'] = user_id
        data['employee_code'] = username
        data['employee_name'] = username
        data['submitted_by'] = user_id
        data['submitted_by_name'] = username
        
        from expense_travel_models import create_cash_advance
        advance_id, advance_number = create_cash_advance(data)
        
        log_expense_audit('cash_advance', advance_id, 'CREATE', user_id=user_id, user_name=username,
                          notes=f"Created cash advance {advance_number}")
        
        flash(f'Cash advance {advance_number} created successfully', 'success')
        return redirect(url_for('expense_travel.advances_detail', advance_id=advance_id))
    
    page_title = get_page_title('cash_advances_new')
    breadcrumbs = get_breadcrumbs('expense_travel', 'cash_advances_new')
    
    return render_template(
        'expense_travel/advances/new.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs
    )


@expense_travel_bp.route('/advances/<int:advance_id>')
def advances_detail(advance_id):
    """View cash advance details."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    from expense_travel_models import get_cash_advance_by_id
    
    advance = get_cash_advance_by_id(advance_id)
    if not advance:
        flash('Cash advance not found', 'danger')
        return redirect(url_for('expense_travel.advances_list'))
    
    if advance['employee_id'] != user_id and role_id not in [1, 2, 3]:
        flash('You do not have permission to view this advance', 'danger')
        return redirect(url_for('expense_travel.advances_list'))
    
    page_title = get_page_title('cash_advances_detail')
    breadcrumbs = get_breadcrumbs('expense_travel', 'cash_advances_detail')
    
    return render_template(
        'expense_travel/advances/detail.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs,
        advance=advance
    )


@expense_travel_bp.route('/advances/<int:advance_id>/submit', methods=['POST'])
def advances_submit(advance_id):
    """Submit cash advance for approval."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        if request.is_json:
            return jsonify({'error': 'Authentication required'}), 401
        return redirect(url_for('login'))
    
    from expense_travel_models import get_cash_advance_by_id
    
    advance = get_cash_advance_by_id(advance_id)
    if not advance:
        if request.is_json:
            return jsonify({'error': 'Advance not found'}), 404
        flash('Advance not found', 'danger')
        return redirect(url_for('expense_travel.advances_list'))
    
    if advance['employee_id'] != user_id:
        if request.is_json:
            return jsonify({'error': 'Permission denied'}), 403
        flash('You can only submit your own advances', 'danger')
        return redirect(url_for('expense_travel.advances_list'))
    
    with get_db_context() as db:
        db.execute("""UPDATE cash_advances 
                       SET status = 'submitted', submission_date = ?
                       WHERE id = ?""",
                   (datetime.now().strftime('%Y-%m-%d'), advance_id))
        db.commit()
    
    log_expense_audit('cash_advance', advance_id, 'SUBMIT', user_id=user_id, user_name=username,
                      notes=f"Submitted cash advance {advance['advance_number']}")
    
    create_notification(
        title=f'Cash Advance Submitted: {advance["advance_number"]}',
        message=f'{username} has submitted cash advance {advance["advance_number"]} for {advance["requested_amount"]} {advance["requested_currency"]}',
        notification_type='APPROVAL',
        severity='MEDIUM',
        related_entity_type='cash_advance',
        related_entity_id=advance_id,
        company_id=company_id
    )
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Cash advance submitted successfully'})
    
    flash('Cash advance submitted successfully', 'success')
    return redirect(url_for('expense_travel.advances_detail', advance_id=advance_id))


@expense_travel_bp.route('/advances/<int:advance_id>/approve', methods=['POST'])
def advances_approve(advance_id):
    """Approve cash advance."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        if request.is_json:
            return jsonify({'error': 'Authentication required'}), 401
        return redirect(url_for('login'))
    
    if role_id not in [1, 2, 3]:
        if request.is_json:
            return jsonify({'error': 'Permission denied'}), 403
        flash('You do not have permission to approve advances', 'danger')
        return redirect(url_for('expense_travel.advances_list'))
    
    from expense_travel_models import get_cash_advance_by_id
    
    advance = get_cash_advance_by_id(advance_id)
    if not advance:
        if request.is_json:
            return jsonify({'error': 'Advance not found'}), 404
        flash('Advance not found', 'danger')
        return redirect(url_for('expense_travel.advances_list'))
    
    approved_amount = request.form.get('approved_amount', advance['requested_amount'])
    
    with get_db_context() as db:
        db.execute("""UPDATE cash_advances 
                       SET status = 'approved', approved_amount = ?, approved_amount_currency = ?,
                           approval_date = ?, current_approver_id = ?, current_approver_name = ?
                       WHERE id = ?""",
                   (approved_amount, advance['requested_currency'], datetime.now().strftime('%Y-%m-%d'),
                    user_id, username, advance_id))
        db.commit()
    
    log_expense_audit('cash_advance', advance_id, 'APPROVE', user_id=user_id, user_name=username,
                      notes=f"Approved cash advance {advance['advance_number']} for {approved_amount} {advance['requested_currency']}")
    
    create_notification(
        title=f'Cash Advance Approved: {advance["advance_number"]}',
        message=f'Your cash advance {advance["advance_number"]} has been approved for {approved_amount} {advance["requested_currency"]}',
        notification_type='SUCCESS',
        severity='LOW',
        user_id=advance['employee_id'],
        related_entity_type='cash_advance',
        related_entity_id=advance_id,
        company_id=company_id
    )
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Cash advance approved'})
    
    flash('Cash advance approved successfully', 'success')
    return redirect(url_for('expense_travel.advances_detail', advance_id=advance_id))


# ============================================================================
# RECEIPTS ROUTES
# ============================================================================

@expense_travel_bp.route('/receipts')
def receipts_list():
    """List all receipts."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    from expense_travel_models import get_expense_receipts
    
    filters = {}
    if role_id not in [1, 2, 3]:
        filters['uploaded_by'] = user_id
    
    receipts = get_expense_receipts(filters)
    
    page_title = get_page_title('receipts')
    breadcrumbs = get_breadcrumbs('expense_travel', 'receipts')
    
    return render_template(
        'expense_travel/receipts/list.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs,
        receipts=receipts
    )


@expense_travel_bp.route('/receipts/upload/<int:claim_id>/<int:line_id>', methods=['POST'])
def receipts_upload(claim_id, line_id):
    """Upload receipt for claim line."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        if request.is_json:
            return jsonify({'error': 'Authentication required'}), 401
        return redirect(url_for('login'))
    
    if 'file' not in request.files:
        if request.is_json:
            return jsonify({'error': 'No file provided'}), 400
        flash('No file provided', 'danger')
        return redirect(url_for('expense_travel.claims_edit', claim_id=claim_id))
    
    file = request.files['file']
    
    if file.filename == '':
        if request.is_json:
            return jsonify({'error': 'No file selected'}), 400
        flash('No file selected', 'danger')
        return redirect(url_for('expense_travel.claims_edit', claim_id=claim_id))
    
    # Handle upload
    upload_folder = os.path.join('static', 'uploads', 'expense_receipts')
    unique_filename, file_path = handle_uploaded_file(file, upload_folder, f'claim_{claim_id}')
    
    if not unique_filename:
        if request.is_json:
            return jsonify({'error': 'Upload failed'}), 500
        flash('File upload failed', 'danger')
        return redirect(url_for('expense_travel.claims_edit', claim_id=claim_id))
    
    from expense_travel_models import add_expense_receipt
    
    receipt_data = {
        'claim_id': claim_id,
        'claim_line_id': line_id,
        'file_name': unique_filename,
        'file_path': file_path,
        'file_size': os.path.getsize(file_path),
        'mime_type': file.content_type,
        'original_file_name': file.filename,
        'receipt_date': request.form.get('receipt_date', datetime.now().strftime('%Y-%m-%d')),
        'merchant_name': request.form.get('merchant_name', ''),
        'total_amount': request.form.get('total_amount', 0),
        'currency': request.form.get('currency', 'AED'),
        'uploaded_by': user_id,
        'uploaded_by_name': username
    }
    
    receipt_id, receipt_number = add_expense_receipt(receipt_data)
    
    log_expense_audit('expense_receipt', receipt_id, 'UPLOAD', user_id=user_id, user_name=username,
                      notes=f"Uploaded receipt {receipt_number} for claim {claim_id}")
    
    if request.is_json:
        return jsonify({'success': True, 'receipt_id': receipt_id, 'receipt_number': receipt_number})
    
    flash(f'Receipt uploaded successfully: {receipt_number}', 'success')
    return redirect(url_for('expense_travel.claims_edit', claim_id=claim_id))


# ============================================================================
# REIMBURSEMENTS ROUTES
# ============================================================================

@expense_travel_bp.route('/reimbursements')
def reimbursements_list():
    """List all reimbursements."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    from expense_travel_models import get_reimbursements
    
    filters = {}
    if role_id not in [1, 2, 3]:
        filters['employee_id'] = user_id
    
    reimbursements = get_reimbursements(filters)
    
    page_title = get_page_title('reimbursements')
    breadcrumbs = get_breadcrumbs('expense_travel', 'reimbursements')
    
    return render_template(
        'expense_travel/reimbursements/list.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs,
        reimbursements=reimbursements
    )


@expense_travel_bp.route('/reimbursements/<int:reim_id>')
def reimbursements_detail(reim_id):
    """View reimbursement details."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    from expense_travel_models import get_reimbursements
    
    reim = get_one("SELECT * FROM expense_reimbursements WHERE id = ?", (reim_id,))
    if not reim:
        flash('Reimbursement not found', 'danger')
        return redirect(url_for('expense_travel.reimbursements_list'))
    
    if reim['employee_id'] != user_id and role_id not in [1, 2, 3]:
        flash('You do not have permission to view this reimbursement', 'danger')
        return redirect(url_for('expense_travel.reimbursements_list'))
    
    page_title = get_page_title('reimbursements_detail')
    breadcrumbs = get_breadcrumbs('expense_travel', 'reimbursements_detail')
    
    return render_template(
        'expense_travel/reimbursements/detail.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs,
        reimbursement=reim
    )


# ============================================================================
# REPORTS ROUTES
# ============================================================================

@expense_travel_bp.route('/reports')
def reports_list():
    """List available reports."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    page_title = get_page_title('expense_reports')
    breadcrumbs = get_breadcrumbs('expense_travel', 'expense_reports')
    
    return render_template(
        'expense_travel/reports/list.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs
    )


@expense_travel_bp.route('/reports/expense-claims')
def reports_expense_claims():
    """Expense claims report."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    department = request.args.get('department', '')
    status = request.args.get('status', '')
    
    from expense_travel_models import get_expense_claims, get_expense_summary_by_department, get_expense_summary_by_category
    
    filters = {}
    if date_from:
        filters['date_from'] = date_from
    if date_to:
        filters['date_to'] = date_to
    if department:
        filters['department_id'] = department
    if status:
        filters['status'] = status
    
    claims = get_expense_claims(filters)
    dept_summary = get_expense_summary_by_department(date_from, date_to, company_id)
    category_summary = get_expense_summary_by_category(date_from, date_to, company_id)
    
    page_title = get_page_title('expense_claims_report')
    breadcrumbs = get_breadcrumbs('expense_travel', 'expense_claims_report')
    
    return render_template(
        'expense_travel/reports/expense_claims.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs,
        claims=claims,
        dept_summary=dept_summary,
        category_summary=category_summary,
        date_from=date_from,
        date_to=date_to,
        department=department,
        status=status
    )


@expense_travel_bp.route('/reports/travel-requests')
def reports_travel():
    """Travel requests report."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    from expense_travel_models import get_travel_requests, get_travel_summary_by_destination
    
    filters = {}
    if date_from:
        filters['date_from'] = date_from
    if date_to:
        filters['date_to'] = date_to
    
    requests = get_travel_requests(filters)
    destination_summary = get_travel_summary_by_destination(date_from, date_to, company_id)
    
    page_title = get_page_title('travel_requests_report')
    breadcrumbs = get_breadcrumbs('expense_travel', 'travel_requests_report')
    
    return render_template(
        'expense_travel/reports/travel_requests.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs,
        requests=requests,
        destination_summary=destination_summary,
        date_from=date_from,
        date_to=date_to
    )


@expense_travel_bp.route('/reports/cash-advances')
def reports_advances():
    """Cash advances report."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    from expense_travel_models import get_cash_advances
    
    advances = get_cash_advances({'limit': 100})
    
    page_title = get_page_title('cash_advances_report')
    breadcrumbs = get_breadcrumbs('expense_travel', 'cash_advances_report')
    
    return render_template(
        'expense_travel/reports/cash_advances.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs,
        advances=advances
    )


# ============================================================================
# EXPORT ROUTES
# ============================================================================

@expense_travel_bp.route('/export/claims')
def export_claims():
    """Export expense claims to Excel."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    from expense_travel_models import get_expense_claims
    from openpyxl import Workbook
    
    claims = get_expense_claims({})
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Expense Claims"
    
    # Headers
    headers = ['Claim #', 'Date', 'Employee', 'Department', 'Status', 'Amount', 'Currency', 'Business Purpose']
    ws.append(headers)
    
    # Data
    for claim in claims:
        ws.append([
            claim.get('claim_number', ''),
            claim.get('claim_date', ''),
            claim.get('employee_name', ''),
            claim.get('department_name', ''),
            claim.get('status', ''),
            claim.get('total_amount', 0),
            claim.get('currency', 'AED'),
            claim.get('business_purpose', '')
        ])
    
    filename = f"expense_claims_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb.save(filename)
    
    log_expense_audit('export', None, 'EXPORT_EXPENSE_CLAIMS', user_id=user_id, user_name=username,
                      notes=f"Exported {len(claims)} expense claims")
    
    return send_file(filename, as_attachment=True)


@expense_travel_bp.route('/export/travel')
def export_travel():
    """Export travel requests to Excel."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    from expense_travel_models import get_travel_requests
    from openpyxl import Workbook
    
    requests = get_travel_requests({})
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Travel Requests"
    
    headers = ['Travel #', 'Employee', 'Destination', 'Start Date', 'End Date', 'Days', 'Est. Cost', 'Status']
    ws.append(headers)
    
    for req in requests:
        ws.append([
            req.get('travel_number', ''),
            req.get('employee_name', ''),
            f"{req.get('destination_city', '')}, {req.get('destination_country', '')}",
            req.get('travel_start_date', ''),
            req.get('travel_end_date', ''),
            req.get('total_trip_days', 0),
            req.get('estimated_total_cost', 0),
            req.get('status', '')
        ])
    
    filename = f"travel_requests_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    wb.save(filename)
    
    log_expense_audit('export', None, 'EXPORT_TRAVEL_REQUESTS', user_id=user_id, user_name=username,
                      notes=f"Exported {len(requests)} travel requests")
    
    return send_file(filename, as_attachment=True)


# ============================================================================
# POLICY ROUTES
# ============================================================================

@expense_travel_bp.route('/policies')
def policies_list():
    """List expense/travel policies."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    if role_id not in [1, 2]:  # Only admin and manager
        flash('You do not have permission to view policies', 'danger')
        return redirect(url_for('expense_travel.dashboard'))
    
    from expense_travel_models import get_expense_policies, get_expense_categories
    
    policies = get_expense_policies()
    categories = get_expense_categories()
    
    page_title = get_page_title('expense_policies')
    breadcrumbs = get_breadcrumbs('expense_travel', 'expense_policies')
    
    return render_template(
        'expense_travel/policies/list.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs,
        policies=policies,
        categories=categories
    )


# ============================================================================
# SETTINGS ROUTES
# ============================================================================

@expense_travel_bp.route('/settings')
def settings_page():
    """Expense/travel settings page."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return redirect(url_for('login'))
    
    if role_id not in [1]:  # Only admin
        flash('You do not have permission to access settings', 'danger')
        return redirect(url_for('expense_travel.dashboard'))
    
    from expense_travel_models import get_expense_setting
    
    settings = {
        'default_currency': get_expense_setting('default_currency', 'AED'),
        'require_receipt_threshold': get_expense_setting('require_receipt_threshold', '25'),
        'auto_approve_below': get_expense_setting('auto_approve_below', '50'),
        'reimbursement_cycle_days': get_expense_setting('reimbursement_cycle_days', '7'),
        'advance_recovery_threshold_days': get_expense_setting('advance_recovery_threshold_days', '30'),
        'max_mileage_rate': get_expense_setting('max_mileage_rate', '3'),
        'expense_claim_prefix': get_expense_setting('expense_claim_prefix', 'EXP'),
        'travel_request_prefix': get_expense_setting('travel_request_prefix', 'TRV'),
        'advance_prefix': get_expense_setting('advance_prefix', 'ADV'),
    }
    
    page_title = get_page_title('expense_settings')
    breadcrumbs = get_breadcrumbs('expense_travel', 'expense_settings')
    
    return render_template(
        'expense_travel/settings/index.html',
        page_title=page_title,
        breadcrumbs=breadcrumbs,
        settings=settings
    )


@expense_travel_bp.route('/settings/save', methods=['POST'])
def settings_save():
    """Save expense/travel settings."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        if request.is_json:
            return jsonify({'error': 'Authentication required'}), 401
        return redirect(url_for('login'))
    
    if role_id not in [1]:
        if request.is_json:
            return jsonify({'error': 'Permission denied'}), 403
        flash('You do not have permission to modify settings', 'danger')
        return redirect(url_for('expense_travel.dashboard'))
    
    from expense_travel_models import set_expense_setting
    
    data = request.form.to_dict()
    
    for key, value in data.items():
        set_expense_setting(key, value)
    
    log_expense_audit('expense_settings', None, 'UPDATE', user_id=user_id, user_name=username,
                      notes="Updated expense/travel settings")
    
    if request.is_json:
        return jsonify({'success': True, 'message': 'Settings saved successfully'})
    
    flash('Settings saved successfully', 'success')
    return redirect(url_for('expense_travel.settings_page'))


# ============================================================================
# API JSON ENDPOINTS
# ============================================================================

@expense_travel_bp.route('/api/stats')
def api_stats():
    """Get dashboard stats as JSON."""
    init_expense_travel_module()
    user_id, username, role_id, company_id = get_current_user()
    
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    from expense_travel_models import get_expense_dashboard_stats
    
    stats = get_expense_dashboard_stats(
        company_id=company_id,
        user_id=user_id,
        role='employee' if role_id not in [1, 2, 3] else 'manager'
    )
    
    return jsonify(stats)


@expense_travel_bp.route('/api/categories')
def api_categories():
    """Get expense categories as JSON."""
    init_expense_travel_module()
    
    from expense_travel_models import get_expense_categories
    
    category_type = request.args.get('type', None)
    categories = get_expense_categories(category_type)
    
    return jsonify(categories)


@expense_travel_bp.route('/api/policies')
def api_policies():
    """Get expense policies as JSON."""
    init_expense_travel_module()
    
    from expense_travel_models import get_expense_policies
    
    policy_type = request.args.get('type', None)
    policies = get_expense_policies(policy_type)
    
    return jsonify(policies)
