"""
Legal / Tax Reporting Module - API Routes
======================================
Comprehensive legal and tax reporting route handlers covering:
- Dashboard & Overview
- Tax Jurisdictions & Authorities
- Tax Registrations & Groups
- Tax Codes, Rates & Rules
- Filing Periods & Returns
- Transaction Review & Exceptions
- Obligations & Compliance Tasks
- Reconciliations
- Notices, Penalties & Disputes
- Filing Submissions & Payments
- Audit Packs & Reports
- Export Center & Settings

Author: Legal/Tax Module Implementation
"""

from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from functools import wraps
import math

# Import database helpers
from database import get_db_context, get_one, get_all, row_to_dict, rows_to_list, log_audit

# Import legal/tax models
from legal_tax_models import (
    # Initialization
    initialize_legal_tax_schema,
    # Tax Jurisdictions
    get_tax_jurisdictions, get_tax_jurisdiction_by_id, create_tax_jurisdiction, update_tax_jurisdiction, delete_tax_jurisdiction,
    # Tax Authorities
    get_tax_authorities, get_tax_authority_by_id, create_tax_authority, update_tax_authority, delete_tax_authority,
    # Legal Entities
    get_legal_entities, get_legal_entity_by_id, create_legal_entity, update_legal_entity,
    # Tax Groups
    get_tax_groups, get_tax_group_by_id, create_tax_group, update_tax_group,
    # Tax Codes
    get_tax_codes, get_tax_code_by_id, create_tax_code, update_tax_code,
    # Tax Rates
    get_tax_rates, get_tax_rate_by_id, create_tax_rate, update_tax_rate,
    # Tax Rules
    get_tax_rules, get_tax_rule_by_id, create_tax_rule, update_tax_rule,
    # Filing Periods
    get_filing_periods, get_filing_period_by_id, create_filing_period, update_filing_period, lock_filing_period, unlock_filing_period,
    # Returns
    get_returns, get_return_by_id, get_return_by_number, create_return, update_return, submit_return, approve_return, reject_return, get_next_return_number,
    # Return Lines
    get_return_lines, create_return_line, update_return_line, delete_return_line,
    # Return Adjustments
    get_return_adjustments, create_return_adjustment, approve_adjustment,
    # Return Approvals
    get_return_approvals, create_return_approval,
    # Obligations
    get_obligations, get_obligations_due_soon, get_overdue_obligations, get_obligation_by_id, create_obligation, update_obligation, complete_obligation, get_next_obligation_number,
    # Compliance Tasks
    get_compliance_tasks, get_compliance_task_by_id, create_compliance_task, update_compliance_task, complete_compliance_task, get_next_task_number,
    # Tax Review Items
    get_tax_review_items, get_tax_review_item_by_id, create_tax_review_item, update_tax_review_item, approve_tax_review_item, reject_tax_review_item, get_next_review_number,
    # Tax Review Comments
    get_return_comments, get_review_item_comments, create_tax_comment,
    # Reconciliations
    get_reconciliations, get_reconciliation_by_id, create_reconciliation, update_reconciliation, get_next_reconciliation_number,
    # Reconciliation Lines
    get_reconciliation_lines, create_reconciliation_line, match_reconciliation_line, unmatch_reconciliation_line,
    # Notices
    get_notices, get_notice_by_id, create_notice, update_notice, resolve_notice, get_next_notice_number,
    # Penalties
    get_penalties, get_penalty_by_id, create_penalty, update_penalty, pay_penalty, get_next_penalty_number,
    # Disputes
    get_disputes, get_dispute_by_id, create_dispute, update_dispute, resolve_dispute, get_next_dispute_number,
    # Filing Submissions
    get_filing_submissions, get_filing_submission_by_id, create_filing_submission, update_filing_submission, get_next_submission_number,
    # Filing Payments
    get_filing_payments, get_filing_payment_by_id, create_filing_payment, update_filing_payment, confirm_filing_payment, get_next_payment_number,
    # Audit Packs
    get_audit_packs, get_audit_pack_by_id, create_audit_pack, update_audit_pack, get_next_pack_number,
    # Report Templates
    get_report_templates, get_report_template_by_id, create_report_template,
    # Export Profiles
    get_export_profiles, get_export_profile_by_id, create_export_profile, update_export_profile,
    # Settings
    get_legal_settings, get_legal_setting, set_legal_setting,
    get_legal_tax_settings, save_legal_tax_settings,
    # Flow & Document Links
    get_flow_links, create_flow_link,
    get_document_links, create_document_link, delete_document_link,
    # Dashboard
    get_legal_tax_dashboard_stats, get_filing_calendar_events,
)

# Import permissions helper
from permissions import require_permission

# Import export utilities
from export_utils import send_export_response, get_export_columns


# =============================================================================
# EXPORT TYPES AND COLUMNS
# =============================================================================

LEGAL_TAX_EXPORT_TYPES = [
    'csv', 'excel_text', 'excel_general', 'json', 'xml', 'txt',
    'pdf', 'docx', 'html', 'printable', 'api',
    'email', 'zip', 'dashboard', 'summary', 'detailed', 'audit_log'
]

LEGAL_TAX_EXPORT_COLUMNS = {
    'jurisdictions': ['code', 'name', 'country', 'tax_type', 'is_active'],
    'authorities': ['code', 'name', 'jurisdiction', 'country', 'phone', 'email', 'is_active'],
    'entities': ['code', 'name', 'registration_number', 'vat_number', 'jurisdiction', 'city', 'country', 'is_active'],
    'tax_codes': ['code', 'name', 'tax_group', 'jurisdiction', 'is_active'],
    'tax_rates': ['code', 'name', 'rate', 'rate_type', 'effective_from', 'effective_to', 'is_active'],
    'tax_rules': ['code', 'name', 'rule_type', 'jurisdiction', 'priority', 'is_active'],
    'filing_periods': ['code', 'name', 'period_type', 'jurisdiction', 'start_date', 'end_date', 'due_date', 'status'],
    'returns': ['return_number', 'return_type', 'jurisdiction', 'period', 'status', 'filing_status', 'total_tax_due', 'due_date'],
    'return_lines': ['box_code', 'box_label', 'line_type', 'tax_code', 'base_amount', 'tax_amount'],
    'obligations': ['obligation_number', 'obligation_type', 'description', 'jurisdiction', 'due_date', 'status', 'priority', 'risk_score'],
    'compliance_tasks': ['task_number', 'task_type', 'title', 'priority', 'status', 'due_date', 'assigned_to'],
    'review_items': ['review_number', 'item_type', 'source_transaction', 'exception_type', 'severity', 'status', 'tax_amount'],
    'reconciliations': ['reconciliation_number', 'reconciliation_type', 'period', 'status', 'total_source_amount', 'total_target_amount', 'variance_amount'],
    'notices': ['notice_number', 'notice_type', 'authority', 'subject', 'severity', 'issue_date', 'due_date', 'status'],
    'penalties': ['penalty_number', 'penalty_type', 'authority', 'description', 'amount', 'penalty_date', 'due_date', 'status', 'paid_amount'],
    'disputes': ['dispute_number', 'dispute_type', 'authority', 'subject', 'amount', 'filing_date', 'status', 'decision'],
    'submissions': ['submission_number', 'filing_type', 'filing_date', 'acknowledgment_number', 'status', 'submitted_by'],
    'payments': ['payment_number', 'payment_type', 'amount', 'currency', 'payment_date', 'status', 'reference_number'],
    'audit_packs': ['pack_number', 'pack_name', 'pack_type', 'period', 'completeness_score', 'status', 'generated_at'],
    'dashboard_stats': ['metric', 'value'],
}


def get_current_user_id():
    """Get current user ID from session."""
    return session.get('user_id')


def get_company_id():
    """Get current company ID from session."""
    return session.get('company_id')


# ============================================================================
# LEGAL/TAX BLUEPRINT
# ============================================================================

legal_tax_bp = Blueprint('legal_tax', __name__, url_prefix='/legal-tax')


# ============================================================================
# DASHBOARD & OVERVIEW
# ============================================================================

@legal_tax_bp.route('/')
@legal_tax_bp.route('/dashboard')
@require_permission('legal_tax', 'dashboard', 'view')
def dashboard():
    """Main Legal/Tax Dashboard."""
    company_id = get_company_id()
    user_id = get_current_user_id()

    stats = get_legal_tax_dashboard_stats(company_id)
    upcoming_obligations = get_obligations_due_soon(days=7, company_id=company_id)
    overdue_obligations = get_overdue_obligations(company_id=company_id)

    returns = get_returns(company_id=company_id, status=None)
    recent_returns = returns[:10] if returns else []

    review_items = get_tax_review_items(company_id=company_id, status='pending')
    pending_reviews_count = len(review_items) if review_items else 0

    notices = get_notices(company_id=company_id, status='received')
    open_notices_count = len(notices) if notices else 0

    penalties = get_penalties(company_id=company_id, status='pending')
    pending_penalties_count = len(penalties) if penalties else 0

    disputes = get_disputes(company_id=company_id, status='open')
    open_disputes_count = len(disputes) if disputes else 0

    return render_template('legal_tax/dashboard.html',
        title='Legal / Tax Dashboard',
        stats=stats,
        upcoming_obligations=upcoming_obligations[:5],
        overdue_obligations=overdue_obligations[:5],
        recent_returns=recent_returns,
        pending_reviews_count=pending_reviews_count,
        open_notices_count=open_notices_count,
        pending_penalties_count=pending_penalties_count,
        open_disputes_count=open_disputes_count,
    )


@legal_tax_bp.route('/overview')
@require_permission('legal_tax', 'dashboard', 'view')
def overview():
    """Overview page with module summary."""
    company_id = get_company_id()
    stats = get_legal_tax_dashboard_stats(company_id)

    recent_returns = get_returns(company_id=company_id)
    recent_returns = recent_returns[:5] if recent_returns else []

    obligations = get_obligations(company_id=company_id, status='pending')
    urgent_obligations = [o for o in obligations if o.get('risk_score', 0) >= 70][:5]

    notices = get_notices(company_id=company_id, status='received')
    recent_notices = notices[:5] if notices else []

    return render_template('legal_tax/overview.html',
        title='Legal / Tax Overview',
        stats=stats,
        recent_returns=recent_returns,
        urgent_obligations=urgent_obligations,
        recent_notices=recent_notices,
    )


# ============================================================================
# FILING CALENDAR
# ============================================================================

@legal_tax_bp.route('/filing-calendar')
@require_permission('legal_tax', 'obligations', 'view')
def filing_calendar():
    """Filing Calendar view."""
    company_id = get_company_id()
    start_date = request.args.get('start')
    end_date = request.args.get('end')

    events = get_filing_calendar_events(company_id=company_id, start_date=start_date, end_date=end_date)
    obligations = get_obligations(company_id=company_id)
    periods = get_filing_periods(company_id=company_id)

    return render_template('legal_tax/filing_calendar.html',
        title='Filing Calendar',
        events=events,
        obligations=obligations,
        periods=periods,
    )


# ============================================================================
# TAX JURISDICTIONS
# ============================================================================

@legal_tax_bp.route('/jurisdictions')
@require_permission('legal_tax', 'jurisdictions', 'view')
def jurisdictions_list():
    """List all tax jurisdictions."""
    company_id = get_company_id()
    active_only = request.args.get('active_only', 'true').lower() == 'true'

    jurisdictions = get_tax_jurisdictions(company_id=company_id, active_only=active_only)

    return render_template('legal_tax/jurisdictions/list.html',
        title='Tax Jurisdictions',
        jurisdictions=jurisdictions,
        active_only=active_only,
    )


@legal_tax_bp.route('/jurisdictions/<int:jurisdiction_id>')
@require_permission('legal_tax', 'jurisdictions', 'view')
def jurisdictions_view(jurisdiction_id):
    """View a single jurisdiction."""
    jurisdiction = get_tax_jurisdiction_by_id(jurisdiction_id)
    if not jurisdiction:
        flash("Jurisdiction not found.", "error")
        return redirect(url_for('legal_tax.jurisdictions_list'))

    authorities = get_tax_authorities(jurisdiction_id=jurisdiction_id)
    tax_codes = get_tax_codes(jurisdiction_id=jurisdiction_id)

    return render_template('legal_tax/jurisdictions/view.html',
        title=jurisdiction['name'],
        jurisdiction=jurisdiction,
        authorities=authorities,
        tax_codes=tax_codes,
    )


@legal_tax_bp.route('/jurisdictions/create', methods=['GET', 'POST'])
@require_permission('legal_tax', 'jurisdictions', 'create')
def jurisdictions_create():
    """Create a new tax jurisdiction."""
    if request.method == 'POST':
        data = {
            'code': request.form.get('code'),
            'name': request.form.get('name'),
            'name_ar': request.form.get('name_ar'),
            'name_fa': request.form.get('name_fa'),
            'country': request.form.get('country'),
            'region': request.form.get('region'),
            'tax_type': request.form.get('tax_type'),
            'is_active': 1 if request.form.get('is_active') else 0,
            'company_id': get_company_id(),
            'created_by': get_current_user_id(),
        }

        try:
            jurisdiction_id = create_tax_jurisdiction(data)
            log_audit('jurisdiction_created', user_id=get_current_user_id(), record_id=jurisdiction_id,
                     entity_type='tax_jurisdiction', details=f"Jurisdiction created: {data['code']}")
            flash("Tax jurisdiction created successfully.", "success")
            return redirect(url_for('legal_tax.jurisdictions_view', jurisdiction_id=jurisdiction_id))
        except Exception as e:
            flash(f"Error creating jurisdiction: {str(e)}", "error")

    return render_template('legal_tax/jurisdictions/create.html',
        title='Create Tax Jurisdiction',
    )


@legal_tax_bp.route('/jurisdictions/<int:jurisdiction_id>/edit', methods=['GET', 'POST'])
@require_permission('legal_tax', 'jurisdictions', 'edit')
def jurisdictions_edit(jurisdiction_id):
    """Edit a tax jurisdiction."""
    jurisdiction = get_tax_jurisdiction_by_id(jurisdiction_id)
    if not jurisdiction:
        flash("Jurisdiction not found.", "error")
        return redirect(url_for('legal_tax.jurisdictions_list'))

    if request.method == 'POST':
        data = {
            'code': request.form.get('code'),
            'name': request.form.get('name'),
            'name_ar': request.form.get('name_ar'),
            'name_fa': request.form.get('name_fa'),
            'country': request.form.get('country'),
            'region': request.form.get('region'),
            'tax_type': request.form.get('tax_type'),
            'is_active': 1 if request.form.get('is_active') else 0,
        }

        try:
            update_tax_jurisdiction(jurisdiction_id, data)
            log_audit('jurisdiction_updated', user_id=get_current_user_id(), record_id=jurisdiction_id,
                     entity_type='tax_jurisdiction', details=f"Jurisdiction updated: {data['code']}")
            flash("Tax jurisdiction updated successfully.", "success")
            return redirect(url_for('legal_tax.jurisdictions_view', jurisdiction_id=jurisdiction_id))
        except Exception as e:
            flash(f"Error updating jurisdiction: {str(e)}", "error")

    return render_template('legal_tax/jurisdictions/edit.html',
        title=f"Edit: {jurisdiction['name']}",
        jurisdiction=jurisdiction,
    )


@legal_tax_bp.route('/jurisdictions/<int:jurisdiction_id>/delete', methods=['POST'])
@require_permission('legal_tax', 'jurisdictions', 'delete')
def jurisdictions_delete(jurisdiction_id):
    """Delete a tax jurisdiction."""
    jurisdiction = get_tax_jurisdiction_by_id(jurisdiction_id)
    if not jurisdiction:
        return jsonify({'error': 'Jurisdiction not found'}), 404

    try:
        delete_tax_jurisdiction(jurisdiction_id)
        log_audit('jurisdiction_deleted', user_id=get_current_user_id(), record_id=jurisdiction_id,
                 entity_type='tax_jurisdiction', details=f"Jurisdiction deleted: {jurisdiction['code']}")
        flash("Tax jurisdiction deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting jurisdiction: {str(e)}", "error")

    return redirect(url_for('legal_tax.jurisdictions_list'))


# ============================================================================
# TAX AUTHORITIES
# ============================================================================

@legal_tax_bp.route('/authorities')
@require_permission('legal_tax', 'authorities', 'view')
def authorities_list():
    """List all tax authorities."""
    company_id = get_company_id()
    jurisdiction_id = request.args.get('jurisdiction_id', type=int)

    authorities = get_tax_authorities(jurisdiction_id=jurisdiction_id, company_id=company_id)
    jurisdictions = get_tax_jurisdictions(company_id=company_id)

    return render_template('legal_tax/authorities/list.html',
        title='Tax Authorities',
        authorities=authorities,
        jurisdictions=jurisdictions,
        selected_jurisdiction=jurisdiction_id,
    )


@legal_tax_bp.route('/authorities/<int:authority_id>')
@require_permission('legal_tax', 'authorities', 'view')
def authorities_view(authority_id):
    """View a single tax authority."""
    authority = get_tax_authority_by_id(authority_id)
    if not authority:
        flash("Tax authority not found.", "error")
        return redirect(url_for('legal_tax.authorities_list'))

    jurisdiction = get_tax_jurisdiction_by_id(authority['jurisdiction_id']) if authority['jurisdiction_id'] else None

    return render_template('legal_tax/authorities/view.html',
        title=authority['name'],
        authority=authority,
        jurisdiction=jurisdiction,
    )


@legal_tax_bp.route('/authorities/create', methods=['GET', 'POST'])
@require_permission('legal_tax', 'authorities', 'create')
def authorities_create():
    """Create a new tax authority."""
    company_id = get_company_id()
    jurisdictions = get_tax_jurisdictions(company_id=company_id)

    if request.method == 'POST':
        data = {
            'code': request.form.get('code'),
            'name': request.form.get('name'),
            'name_ar': request.form.get('name_ar'),
            'name_fa': request.form.get('name_fa'),
            'jurisdiction_id': request.form.get('jurisdiction_id'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'country': request.form.get('country'),
            'postal_code': request.form.get('postal_code'),
            'phone': request.form.get('phone'),
            'email': request.form.get('email'),
            'website': request.form.get('website'),
            'contact_person': request.form.get('contact_person'),
            'is_active': 1 if request.form.get('is_active') else 0,
            'company_id': company_id,
            'created_by': get_current_user_id(),
        }

        try:
            authority_id = create_tax_authority(data)
            log_audit('authority_created', user_id=get_current_user_id(), record_id=authority_id,
                     entity_type='tax_authority', details=f"Authority created: {data['code']}")
            flash("Tax authority created successfully.", "success")
            return redirect(url_for('legal_tax.authorities_view', authority_id=authority_id))
        except Exception as e:
            flash(f"Error creating authority: {str(e)}", "error")

    return render_template('legal_tax/authorities/create.html',
        title='Create Tax Authority',
        jurisdictions=jurisdictions,
    )


@legal_tax_bp.route('/authorities/<int:authority_id>/edit', methods=['GET', 'POST'])
@require_permission('legal_tax', 'authorities', 'edit')
def authorities_edit(authority_id):
    """Edit a tax authority."""
    authority = get_tax_authority_by_id(authority_id)
    if not authority:
        flash("Tax authority not found.", "error")
        return redirect(url_for('legal_tax.authorities_list'))

    company_id = get_company_id()
    jurisdictions = get_tax_jurisdictions(company_id=company_id)

    if request.method == 'POST':
        data = {
            'code': request.form.get('code'),
            'name': request.form.get('name'),
            'name_ar': request.form.get('name_ar'),
            'name_fa': request.form.get('name_fa'),
            'jurisdiction_id': request.form.get('jurisdiction_id'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'country': request.form.get('country'),
            'postal_code': request.form.get('postal_code'),
            'phone': request.form.get('phone'),
            'email': request.form.get('email'),
            'website': request.form.get('website'),
            'contact_person': request.form.get('contact_person'),
            'is_active': 1 if request.form.get('is_active') else 0,
        }

        try:
            update_tax_authority(authority_id, data)
            log_audit('authority_updated', user_id=get_current_user_id(), record_id=authority_id,
                     entity_type='tax_authority', details=f"Authority updated: {data['code']}")
            flash("Tax authority updated successfully.", "success")
            return redirect(url_for('legal_tax.authorities_view', authority_id=authority_id))
        except Exception as e:
            flash(f"Error updating authority: {str(e)}", "error")

    return render_template('legal_tax/authorities/edit.html',
        title=f"Edit: {authority['name']}",
        authority=authority,
        jurisdictions=jurisdictions,
    )


# ============================================================================
# REGISTRATIONS (LEGAL ENTITIES)
# ============================================================================

@legal_tax_bp.route('/registrations')
@require_permission('legal_tax', 'registrations', 'view')
def registrations_list():
    """List all legal entities."""
    company_id = get_company_id()
    jurisdiction_id = request.args.get('jurisdiction_id', type=int)

    entities = get_legal_entities(company_id=company_id, jurisdiction_id=jurisdiction_id)
    jurisdictions = get_tax_jurisdictions(company_id=company_id)

    return render_template('legal_tax/registrations/list.html',
        title='Tax Registrations',
        entities=entities,
        jurisdictions=jurisdictions,
        selected_jurisdiction=jurisdiction_id,
    )


@legal_tax_bp.route('/registrations/<int:entity_id>')
@require_permission('legal_tax', 'registrations', 'view')
def registrations_view(entity_id):
    """View a single legal entity."""
    entity = get_legal_entity_by_id(entity_id)
    if not entity:
        flash("Registration not found.", "error")
        return redirect(url_for('legal_tax.registrations_list'))

    jurisdiction = get_tax_jurisdiction_by_id(entity['jurisdiction_id']) if entity['jurisdiction_id'] else None

    return render_template('legal_tax/registrations/view.html',
        title=entity['name'],
        entity=entity,
        jurisdiction=jurisdiction,
    )


@legal_tax_bp.route('/registrations/create', methods=['GET', 'POST'])
@require_permission('legal_tax', 'registrations', 'create')
def registrations_create():
    """Create a new legal entity."""
    company_id = get_company_id()
    jurisdictions = get_tax_jurisdictions(company_id=company_id)

    if request.method == 'POST':
        data = {
            'code': request.form.get('code'),
            'name': request.form.get('name'),
            'name_ar': request.form.get('name_ar'),
            'name_fa': request.form.get('name_fa'),
            'registration_number': request.form.get('registration_number'),
            'tax_identification_number': request.form.get('tax_identification_number'),
            'vat_number': request.form.get('vat_number'),
            'jurisdiction_id': request.form.get('jurisdiction_id'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'country': request.form.get('country'),
            'postal_code': request.form.get('postal_code'),
            'phone': request.form.get('phone'),
            'email': request.form.get('email'),
            'is_active': 1 if request.form.get('is_active') else 0,
            'company_id': company_id,
            'created_by': get_current_user_id(),
        }

        try:
            entity_id = create_legal_entity(data)
            log_audit('entity_created', user_id=get_current_user_id(), record_id=entity_id,
                     entity_type='legal_entity', details=f"Entity created: {data['code']}")
            flash("Tax registration created successfully.", "success")
            return redirect(url_for('legal_tax.registrations_view', entity_id=entity_id))
        except Exception as e:
            flash(f"Error creating registration: {str(e)}", "error")

    return render_template('legal_tax/registrations/create.html',
        title='Create Tax Registration',
        jurisdictions=jurisdictions,
    )


@legal_tax_bp.route('/registrations/<int:entity_id>/edit', methods=['GET', 'POST'])
@require_permission('legal_tax', 'registrations', 'edit')
def registrations_edit(entity_id):
    """Edit a legal entity."""
    entity = get_legal_entity_by_id(entity_id)
    if not entity:
        flash("Registration not found.", "error")
        return redirect(url_for('legal_tax.registrations_list'))

    company_id = get_company_id()
    jurisdictions = get_tax_jurisdictions(company_id=company_id)

    if request.method == 'POST':
        data = {
            'code': request.form.get('code'),
            'name': request.form.get('name'),
            'name_ar': request.form.get('name_ar'),
            'name_fa': request.form.get('name_fa'),
            'registration_number': request.form.get('registration_number'),
            'tax_identification_number': request.form.get('tax_identification_number'),
            'vat_number': request.form.get('vat_number'),
            'jurisdiction_id': request.form.get('jurisdiction_id'),
            'address': request.form.get('address'),
            'city': request.form.get('city'),
            'country': request.form.get('country'),
            'postal_code': request.form.get('postal_code'),
            'phone': request.form.get('phone'),
            'email': request.form.get('email'),
            'is_active': 1 if request.form.get('is_active') else 0,
        }

        try:
            update_legal_entity(entity_id, data)
            log_audit('entity_updated', user_id=get_current_user_id(), record_id=entity_id,
                     entity_type='legal_entity', details=f"Entity updated: {data['code']}")
            flash("Tax registration updated successfully.", "success")
            return redirect(url_for('legal_tax.registrations_view', entity_id=entity_id))
        except Exception as e:
            flash(f"Error updating registration: {str(e)}", "error")

    return render_template('legal_tax/registrations/edit.html',
        title=f"Edit: {entity['name']}",
        entity=entity,
        jurisdictions=jurisdictions,
    )


# ============================================================================
# TAX CODES
# ============================================================================

@legal_tax_bp.route('/tax-codes')
@require_permission('legal_tax', 'tax_codes', 'view')
def tax_codes_list():
    """List all tax codes."""
    company_id = get_company_id()
    jurisdiction_id = request.args.get('jurisdiction_id', type=int)

    tax_codes = get_tax_codes(company_id=company_id, jurisdiction_id=jurisdiction_id)
    jurisdictions = get_tax_jurisdictions(company_id=company_id)
    tax_groups = get_tax_groups(company_id=company_id)

    return render_template('legal_tax/tax_codes/list.html',
        title='Tax Codes',
        tax_codes=tax_codes,
        jurisdictions=jurisdictions,
        tax_groups=tax_groups,
        selected_jurisdiction=jurisdiction_id,
    )


@legal_tax_bp.route('/tax-codes/create', methods=['GET', 'POST'])
@require_permission('legal_tax', 'tax_codes', 'create')
def tax_codes_create():
    """Create a new tax code."""
    company_id = get_company_id()
    jurisdictions = get_tax_jurisdictions(company_id=company_id)
    tax_groups = get_tax_groups(company_id=company_id)
    tax_rates = get_tax_rates(company_id=company_id)

    if request.method == 'POST':
        data = {
            'code': request.form.get('code'),
            'name': request.form.get('name'),
            'name_ar': request.form.get('name_ar'),
            'name_fa': request.form.get('name_fa'),
            'description': request.form.get('description'),
            'tax_group_id': request.form.get('tax_group_id'),
            'jurisdiction_id': request.form.get('jurisdiction_id'),
            'tax_rate_id': request.form.get('tax_rate_id'),
            'is_active': 1 if request.form.get('is_active') else 0,
            'company_id': company_id,
            'created_by': get_current_user_id(),
        }

        try:
            tax_code_id = create_tax_code(data)
            log_audit('tax_code_created', user_id=get_current_user_id(), record_id=tax_code_id,
                     entity_type='tax_code', details=f"Tax code created: {data['code']}")
            flash("Tax code created successfully.", "success")
            return redirect(url_for('legal_tax.tax_codes_list'))
        except Exception as e:
            flash(f"Error creating tax code: {str(e)}", "error")

    return render_template('legal_tax/tax_codes/create.html',
        title='Create Tax Code',
        jurisdictions=jurisdictions,
        tax_groups=tax_groups,
        tax_rates=tax_rates,
    )


@legal_tax_bp.route('/tax-codes/<int:tax_code_id>/edit', methods=['GET', 'POST'])
@require_permission('legal_tax', 'tax_codes', 'edit')
def tax_codes_edit(tax_code_id):
    """Edit a tax code."""
    tax_code = get_tax_code_by_id(tax_code_id)
    if not tax_code:
        flash("Tax code not found.", "error")
        return redirect(url_for('legal_tax.tax_codes_list'))

    company_id = get_company_id()
    jurisdictions = get_tax_jurisdictions(company_id=company_id)
    tax_groups = get_tax_groups(company_id=company_id)
    tax_rates = get_tax_rates(company_id=company_id)

    if request.method == 'POST':
        data = {
            'code': request.form.get('code'),
            'name': request.form.get('name'),
            'name_ar': request.form.get('name_ar'),
            'name_fa': request.form.get('name_fa'),
            'description': request.form.get('description'),
            'tax_group_id': request.form.get('tax_group_id'),
            'jurisdiction_id': request.form.get('jurisdiction_id'),
            'tax_rate_id': request.form.get('tax_rate_id'),
            'is_active': 1 if request.form.get('is_active') else 0,
        }

        try:
            update_tax_code(tax_code_id, data)
            log_audit('tax_code_updated', user_id=get_current_user_id(), record_id=tax_code_id,
                     entity_type='tax_code', details=f"Tax code updated: {data['code']}")
            flash("Tax code updated successfully.", "success")
            return redirect(url_for('legal_tax.tax_codes_list'))
        except Exception as e:
            flash(f"Error updating tax code: {str(e)}", "error")

    return render_template('legal_tax/tax_codes/edit.html',
        title=f"Edit: {tax_code['code']}",
        tax_code=tax_code,
        jurisdictions=jurisdictions,
        tax_groups=tax_groups,
        tax_rates=tax_rates,
    )


# ============================================================================
# TAX RULES
# ============================================================================

@legal_tax_bp.route('/tax-rules')
@require_permission('legal_tax', 'tax_rules', 'view')
def tax_rules_list():
    """List all tax rules."""
    company_id = get_company_id()
    jurisdiction_id = request.args.get('jurisdiction_id', type=int)
    rule_type = request.args.get('rule_type')

    tax_rules = get_tax_rules(company_id=company_id, jurisdiction_id=jurisdiction_id, rule_type=rule_type)
    jurisdictions = get_tax_jurisdictions(company_id=company_id)

    return render_template('legal_tax/tax_rules/list.html',
        title='Tax Rules',
        tax_rules=tax_rules,
        jurisdictions=jurisdictions,
        selected_jurisdiction=jurisdiction_id,
        selected_rule_type=rule_type,
    )


@legal_tax_bp.route('/tax-rules/create', methods=['GET', 'POST'])
@require_permission('legal_tax', 'tax_rules', 'create')
def tax_rules_create():
    """Create a new tax rule."""
    company_id = get_company_id()
    jurisdictions = get_tax_jurisdictions(company_id=company_id)
    tax_codes = get_tax_codes(company_id=company_id)

    if request.method == 'POST':
        data = {
            'code': request.form.get('code'),
            'name': request.form.get('name'),
            'name_ar': request.form.get('name_ar'),
            'name_fa': request.form.get('name_fa'),
            'description': request.form.get('description'),
            'tax_code_id': request.form.get('tax_code_id'),
            'jurisdiction_id': request.form.get('jurisdiction_id'),
            'rule_type': request.form.get('rule_type'),
            'priority': request.form.get('priority', 0),
            'is_active': 1 if request.form.get('is_active') else 0,
            'company_id': company_id,
            'created_by': get_current_user_id(),
        }

        try:
            rule_id = create_tax_rule(data)
            log_audit('tax_rule_created', user_id=get_current_user_id(), record_id=rule_id,
                     entity_type='tax_rule', details=f"Tax rule created: {data['code']}")
            flash("Tax rule created successfully.", "success")
            return redirect(url_for('legal_tax.tax_rules_list'))
        except Exception as e:
            flash(f"Error creating tax rule: {str(e)}", "error")

    return render_template('legal_tax/tax_rules/create.html',
        title='Create Tax Rule',
        jurisdictions=jurisdictions,
        tax_codes=tax_codes,
    )


# ============================================================================
# FILING PERIODS
# ============================================================================

@legal_tax_bp.route('/filing-periods')
@require_permission('legal_tax', 'filing_periods', 'view')
def filing_periods_list():
    """List all filing periods."""
    company_id = get_company_id()
    jurisdiction_id = request.args.get('jurisdiction_id', type=int)
    status = request.args.get('status')

    periods = get_filing_periods(company_id=company_id, jurisdiction_id=jurisdiction_id, status=status)
    jurisdictions = get_tax_jurisdictions(company_id=company_id)

    return render_template('legal_tax/filing_periods/list.html',
        title='Filing Periods',
        periods=periods,
        jurisdictions=jurisdictions,
        selected_jurisdiction=jurisdiction_id,
        selected_status=status,
    )


@legal_tax_bp.route('/filing-periods/create', methods=['GET', 'POST'])
@require_permission('legal_tax', 'filing_periods', 'create')
def filing_periods_create():
    """Create a new filing period."""
    company_id = get_company_id()
    jurisdictions = get_tax_jurisdictions(company_id=company_id)
    authorities = get_tax_authorities(company_id=company_id)

    if request.method == 'POST':
        data = {
            'code': request.form.get('code'),
            'name': request.form.get('name'),
            'period_type': request.form.get('period_type'),
            'jurisdiction_id': request.form.get('jurisdiction_id'),
            'authority_id': request.form.get('authority_id'),
            'start_date': request.form.get('start_date'),
            'end_date': request.form.get('end_date'),
            'due_date': request.form.get('due_date'),
            'filing_frequency': request.form.get('filing_frequency'),
            'status': request.form.get('status', 'open'),
            'company_id': company_id,
            'created_by': get_current_user_id(),
        }

        try:
            period_id = create_filing_period(data)
            log_audit('filing_period_created', user_id=get_current_user_id(), record_id=period_id,
                     entity_type='filing_period', details=f"Filing period created: {data['code']}")
            flash("Filing period created successfully.", "success")
            return redirect(url_for('legal_tax.filing_periods_list'))
        except Exception as e:
            flash(f"Error creating filing period: {str(e)}", "error")

    return render_template('legal_tax/filing_periods/create.html',
        title='Create Filing Period',
        jurisdictions=jurisdictions,
        authorities=authorities,
    )


@legal_tax_bp.route('/filing-periods/<int:period_id>/lock', methods=['POST'])
@require_permission('legal_tax', 'filing_periods', 'edit')
def filing_periods_lock(period_id):
    """Lock a filing period."""
    try:
        lock_filing_period(period_id, get_current_user_id())
        log_audit('filing_period_locked', user_id=get_current_user_id(), record_id=period_id,
                 entity_type='filing_period', details=f"Filing period locked")
        flash("Filing period locked successfully.", "success")
    except Exception as e:
        flash(f"Error locking period: {str(e)}", "error")

    return redirect(url_for('legal_tax.filing_periods_list'))


@legal_tax_bp.route('/filing-periods/<int:period_id>/unlock', methods=['POST'])
@require_permission('legal_tax', 'filing_periods', 'edit')
def filing_periods_unlock(period_id):
    """Unlock a filing period."""
    try:
        unlock_filing_period(period_id)
        log_audit('filing_period_unlocked', user_id=get_current_user_id(), record_id=period_id,
                 entity_type='filing_period', details=f"Filing period unlocked")
        flash("Filing period unlocked successfully.", "success")
    except Exception as e:
        flash(f"Error unlocking period: {str(e)}", "error")

    return redirect(url_for('legal_tax.filing_periods_list'))


# ============================================================================
# RETURNS WORKSPACE
# ============================================================================

@legal_tax_bp.route('/returns')
@require_permission('legal_tax', 'returns', 'view')
def returns_list():
    """List all returns."""
    company_id = get_company_id()
    jurisdiction_id = request.args.get('jurisdiction_id', type=int)
    status = request.args.get('status')
    filing_status = request.args.get('filing_status')

    returns = get_returns(company_id=company_id, jurisdiction_id=jurisdiction_id, status=status, filing_status=filing_status)
    jurisdictions = get_tax_jurisdictions(company_id=company_id)

    return render_template('legal_tax/returns/list.html',
        title='Returns Workspace',
        returns=returns,
        jurisdictions=jurisdictions,
        selected_jurisdiction=jurisdiction_id,
        selected_status=status,
        selected_filing_status=filing_status,
    )


@legal_tax_bp.route('/returns/<int:return_id>')
@require_permission('legal_tax', 'returns', 'view')
def returns_view(return_id):
    """View a single return."""
    return_obj = get_return_by_id(return_id)
    if not return_obj:
        flash("Return not found.", "error")
        return redirect(url_for('legal_tax.returns_list'))

    lines = get_return_lines(return_id)
    adjustments = get_return_adjustments(return_id)
    approvals = get_return_approvals(return_id)
    comments = get_return_comments(return_id)
    documents = get_document_links('return', return_id)

    jurisdiction = get_tax_jurisdiction_by_id(return_obj['jurisdiction_id']) if return_obj['jurisdiction_id'] else None
    period = get_filing_period_by_id(return_obj['filing_period_id']) if return_obj['filing_period_id'] else None

    return render_template('legal_tax/returns/view.html',
        title=f"Return: {return_obj['return_number']}",
        return_obj=return_obj,
        lines=lines,
        adjustments=adjustments,
        approvals=approvals,
        comments=comments,
        documents=documents,
        jurisdiction=jurisdiction,
        period=period,
    )


@legal_tax_bp.route('/returns/create', methods=['GET', 'POST'])
@require_permission('legal_tax', 'returns', 'create')
def returns_create():
    """Create a new return."""
    company_id = get_company_id()
    jurisdictions = get_tax_jurisdictions(company_id=company_id)
    periods = get_filing_periods(company_id=company_id, status='open')
    entities = get_legal_entities(company_id=company_id)

    if request.method == 'POST':
        return_type = request.form.get('return_type')
        return_number = get_next_return_number(return_type, company_id)

        data = {
            'return_number': return_number,
            'return_type': return_type,
            'filing_period_id': request.form.get('filing_period_id'),
            'jurisdiction_id': request.form.get('jurisdiction_id'),
            'authority_id': request.form.get('authority_id'),
            'entity_id': request.form.get('entity_id'),
            'tax_jurisdiction_id': request.form.get('jurisdiction_id'),
            'status': 'draft',
            'filing_status': 'pending',
            'company_id': company_id,
            'created_by': get_current_user_id(),
        }

        try:
            return_id = create_return(data)
            log_audit('return_created', user_id=get_current_user_id(), record_id=return_id,
                     entity_type='legal_return', details=f"Return created: {return_number}")
            flash("Return created successfully.", "success")
            return redirect(url_for('legal_tax.returns_view', return_id=return_id))
        except Exception as e:
            flash(f"Error creating return: {str(e)}", "error")

    return render_template('legal_tax/returns/create.html',
        title='Create Return',
        jurisdictions=jurisdictions,
        periods=periods,
        entities=entities,
    )


@legal_tax_bp.route('/returns/<int:return_id>/submit', methods=['POST'])
@require_permission('legal_tax', 'returns', 'submit')
def returns_submit(return_id):
    """Submit a return for review."""
    try:
        submit_return(return_id, get_current_user_id())
        log_audit('return_submitted', user_id=get_current_user_id(), record_id=return_id,
                 entity_type='legal_return', details=f"Return submitted for review")
        flash("Return submitted successfully.", "success")
    except Exception as e:
        flash(f"Error submitting return: {str(e)}", "error")

    return redirect(url_for('legal_tax.returns_view', return_id=return_id))


@legal_tax_bp.route('/returns/<int:return_id>/approve', methods=['POST'])
@require_permission('legal_tax', 'returns', 'approve')
def returns_approve(return_id):
    """Approve a return."""
    try:
        approve_return(return_id, get_current_user_id())
        create_return_approval({
            'return_id': return_id,
            'approver_id': get_current_user_id(),
            'action': 'approved',
            'comments': request.form.get('comments', ''),
            'company_id': get_company_id(),
        })
        log_audit('return_approved', user_id=get_current_user_id(), record_id=return_id,
                 entity_type='legal_return', details=f"Return approved")
        flash("Return approved successfully.", "success")
    except Exception as e:
        flash(f"Error approving return: {str(e)}", "error")

    return redirect(url_for('legal_tax.returns_view', return_id=return_id))


@legal_tax_bp.route('/returns/<int:return_id>/reject', methods=['POST'])
@require_permission('legal_tax', 'returns', 'approve')
def returns_reject(return_id):
    """Reject a return."""
    reason = request.form.get('reason', 'No reason provided')
    try:
        reject_return(return_id, get_current_user_id(), reason)
        create_return_approval({
            'return_id': return_id,
            'approver_id': get_current_user_id(),
            'action': 'rejected',
            'comments': reason,
            'company_id': get_company_id(),
        })
        log_audit('return_rejected', user_id=get_current_user_id(), record_id=return_id,
                 entity_type='legal_return', details=f"Return rejected: {reason}")
        flash("Return rejected.", "warning")
    except Exception as e:
        flash(f"Error rejecting return: {str(e)}", "error")

    return redirect(url_for('legal_tax.returns_view', return_id=return_id))


# ============================================================================
# TRANSACTION REVIEW
# ============================================================================

@legal_tax_bp.route('/transaction-review')
@require_permission('legal_tax', 'transaction_review', 'view')
def transaction_review_list():
    """List all tax review items."""
    company_id = get_company_id()
    status = request.args.get('status')
    severity = request.args.get('severity')
    item_type = request.args.get('item_type')

    review_items = get_tax_review_items(company_id=company_id, status=status, severity=severity, item_type=item_type)

    return render_template('legal_tax/transaction_review/list.html',
        title='Transaction Review',
        review_items=review_items,
        selected_status=status,
        selected_severity=severity,
        selected_item_type=item_type,
    )


@legal_tax_bp.route('/transaction-review/<int:item_id>')
@require_permission('legal_tax', 'transaction_review', 'view')
def transaction_review_view(item_id):
    """View a single review item."""
    item = get_tax_review_item_by_id(item_id)
    if not item:
        flash("Review item not found.", "error")
        return redirect(url_for('legal_tax.transaction_review_list'))

    comments = get_review_item_comments(item_id)

    return render_template('legal_tax/transaction_review/view.html',
        title=f"Review: {item['review_number']}",
        item=item,
        comments=comments,
    )


@legal_tax_bp.route('/transaction-review/<int:item_id>/approve', methods=['POST'])
@require_permission('legal_tax', 'transaction_review', 'approve')
def transaction_review_approve(item_id):
    """Approve a review item."""
    notes = request.form.get('notes', '')
    try:
        approve_tax_review_item(item_id, get_current_user_id(), notes)
        log_audit('review_item_approved', user_id=get_current_user_id(), record_id=item_id,
                 entity_type='tax_review_item', details=f"Review item approved")
        flash("Review item approved.", "success")
    except Exception as e:
        flash(f"Error approving item: {str(e)}", "error")

    return redirect(url_for('legal_tax.transaction_review_view', item_id=item_id))


@legal_tax_bp.route('/transaction-review/<int:item_id>/reject', methods=['POST'])
@require_permission('legal_tax', 'transaction_review', 'approve')
def transaction_review_reject(item_id):
    """Reject a review item."""
    reason = request.form.get('reason', 'No reason provided')
    try:
        reject_tax_review_item(item_id, get_current_user_id(), reason)
        log_audit('review_item_rejected', user_id=get_current_user_id(), record_id=item_id,
                 entity_type='tax_review_item', details=f"Review item rejected: {reason}")
        flash("Review item rejected.", "warning")
    except Exception as e:
        flash(f"Error rejecting item: {str(e)}", "error")

    return redirect(url_for('legal_tax.transaction_review_view', item_id=item_id))


# ============================================================================
# OBLIGATIONS
# ============================================================================

@legal_tax_bp.route('/obligations')
@require_permission('legal_tax', 'obligations', 'view')
def obligations_list():
    """List all obligations."""
    company_id = get_company_id()
    jurisdiction_id = request.args.get('jurisdiction_id', type=int)
    status = request.args.get('status')

    obligations = get_obligations(company_id=company_id, jurisdiction_id=jurisdiction_id, status=status)
    jurisdictions = get_tax_jurisdictions(company_id=company_id)

    return render_template('legal_tax/obligations/list.html',
        title='Compliance Obligations',
        obligations=obligations,
        jurisdictions=jurisdictions,
        selected_jurisdiction=jurisdiction_id,
        selected_status=status,
    )


@legal_tax_bp.route('/obligations/create', methods=['GET', 'POST'])
@require_permission('legal_tax', 'obligations', 'create')
def obligations_create():
    """Create a new obligation."""
    company_id = get_company_id()
    jurisdictions = get_tax_jurisdictions(company_id=company_id)
    authorities = get_tax_authorities(company_id=company_id)

    if request.method == 'POST':
        obligation_type = request.form.get('obligation_type')
        obligation_number = get_next_obligation_number(obligation_type, company_id)

        data = {
            'obligation_number': obligation_number,
            'obligation_type': obligation_type,
            'description': request.form.get('description'),
            'description_ar': request.form.get('description_ar'),
            'description_fa': request.form.get('description_fa'),
            'jurisdiction_id': request.form.get('jurisdiction_id'),
            'authority_id': request.form.get('authority_id'),
            'filing_period_id': request.form.get('filing_period_id'),
            'due_date': request.form.get('due_date'),
            'filing_frequency': request.form.get('filing_frequency'),
            'status': 'pending',
            'priority': request.form.get('priority', 'normal'),
            'risk_score': request.form.get('risk_score', 0),
            'assigned_to': request.form.get('assigned_to'),
            'reminder_date': request.form.get('reminder_date'),
            'notes': request.form.get('notes'),
            'company_id': company_id,
            'created_by': get_current_user_id(),
        }

        try:
            obligation_id = create_obligation(data)
            log_audit('obligation_created', user_id=get_current_user_id(), record_id=obligation_id,
                     entity_type='legal_obligation', details=f" Obligation created: {obligation_number}")
            flash("Obligation created successfully.", "success")
            return redirect(url_for('legal_tax.obligations_list'))
        except Exception as e:
            flash(f"Error creating obligation: {str(e)}", "error")

    return render_template('legal_tax/obligations/create.html',
        title='Create Obligation',
        jurisdictions=jurisdictions,
        authorities=authorities,
    )


@legal_tax_bp.route('/obligations/<int:obligation_id>/complete', methods=['POST'])
@require_permission('legal_tax', 'obligations', 'edit')
def obligations_complete(obligation_id):
    """Mark an obligation as completed."""
    try:
        complete_obligation(obligation_id)
        log_audit('obligation_completed', user_id=get_current_user_id(), record_id=obligation_id,
                 entity_type='legal_obligation', details=f"Obligation completed")
        flash("Obligation marked as completed.", "success")
    except Exception as e:
        flash(f"Error completing obligation: {str(e)}", "error")

    return redirect(url_for('legal_tax.obligations_list'))


# ============================================================================
# RECONCILIATIONS
# ============================================================================

@legal_tax_bp.route('/reconciliations')
@require_permission('legal_tax', 'reconciliations', 'view')
def reconciliations_list():
    """List all reconciliations."""
    company_id = get_company_id()
    status = request.args.get('status')
    reconciliation_type = request.args.get('reconciliation_type')

    reconciliations = get_reconciliations(company_id=company_id, status=status, reconciliation_type=reconciliation_type)

    return render_template('legal_tax/reconciliations/list.html',
        title='Reconciliations',
        reconciliations=reconciliations,
        selected_status=status,
        selected_type=reconciliation_type,
    )


@legal_tax_bp.route('/reconciliations/<int:recon_id>')
@require_permission('legal_tax', 'reconciliations', 'view')
def reconciliations_view(recon_id):
    """View a single reconciliation."""
    recon = get_reconciliation_by_id(recon_id)
    if not recon:
        flash("Reconciliation not found.", "error")
        return redirect(url_for('legal_tax.reconciliations_list'))

    lines = get_reconciliation_lines(recon_id)

    return render_template('legal_tax/reconciliations/view.html',
        title=f"Reconciliation: {recon['reconciliation_number']}",
        recon=recon,
        lines=lines,
    )


@legal_tax_bp.route('/reconciliations/create', methods=['GET', 'POST'])
@require_permission('legal_tax', 'reconciliations', 'create')
def reconciliations_create():
    """Create a new reconciliation."""
    company_id = get_company_id()
    periods = get_filing_periods(company_id=company_id, status='open')
    jurisdictions = get_tax_jurisdictions(company_id=company_id)

    if request.method == 'POST':
        reconciliation_type = request.form.get('reconciliation_type')
        reconciliation_number = get_next_reconciliation_number(reconciliation_type, company_id)

        data = {
            'reconciliation_number': reconciliation_number,
            'reconciliation_type': reconciliation_type,
            'period_id': request.form.get('period_id'),
            'jurisdiction_id': request.form.get('jurisdiction_id'),
            'entity_id': request.form.get('entity_id'),
            'status': 'draft',
            'notes': request.form.get('notes'),
            'company_id': company_id,
            'created_by': get_current_user_id(),
        }

        try:
            recon_id = create_reconciliation(data)
            log_audit('reconciliation_created', user_id=get_current_user_id(), record_id=recon_id,
                     entity_type='legal_reconciliation', details=f"Reconciliation created: {reconciliation_number}")
            flash("Reconciliation created successfully.", "success")
            return redirect(url_for('legal_tax.reconciliations_view', recon_id=recon_id))
        except Exception as e:
            flash(f"Error creating reconciliation: {str(e)}", "error")

    return render_template('legal_tax/reconciliations/create.html',
        title='Create Reconciliation',
        periods=periods,
        jurisdictions=jurisdictions,
    )


@legal_tax_bp.route('/reconciliations/<int:line_id>/match', methods=['POST'])
@require_permission('legal_tax', 'reconciliations', 'edit')
def reconciliations_match(line_id):
    """Match a reconciliation line."""
    explanation = request.form.get('explanation', '')
    try:
        match_reconciliation_line(line_id, get_current_user_id(), explanation)
        log_audit('reconciliation_line_matched', user_id=get_current_user_id(), record_id=line_id,
                 entity_type='reconciliation_line', details=f"Line matched")
        flash("Line matched successfully.", "success")
    except Exception as e:
        flash(f"Error matching line: {str(e)}", "error")

    recon_id = request.form.get('recon_id')
    return redirect(url_for('legal_tax.reconciliations_view', recon_id=recon_id))


# ============================================================================
# NOTICES / PENALTIES / DISPUTES
# ============================================================================

@legal_tax_bp.route('/notices')
@require_permission('legal_tax', 'notices', 'view')
def notices_list():
    """List all notices."""
    company_id = get_company_id()
    status = request.args.get('status')
    severity = request.args.get('severity')

    notices = get_notices(company_id=company_id, status=status, severity=severity)

    return render_template('legal_tax/notices/list.html',
        title='Notices',
        notices=notices,
        selected_status=status,
        selected_severity=severity,
    )


@legal_tax_bp.route('/notices/<int:notice_id>')
@require_permission('legal_tax', 'notices', 'view')
def notices_view(notice_id):
    """View a single notice."""
    notice = get_notice_by_id(notice_id)
    if not notice:
        flash("Notice not found.", "error")
        return redirect(url_for('legal_tax.notices_list'))

    documents = get_document_links('notice', notice_id)

    return render_template('legal_tax/notices/view.html',
        title=f"Notice: {notice['notice_number']}",
        notice=notice,
        documents=documents,
    )


@legal_tax_bp.route('/notices/create', methods=['GET', 'POST'])
@require_permission('legal_tax', 'notices', 'create')
def notices_create():
    """Create a new notice."""
    company_id = get_company_id()
    authorities = get_tax_authorities(company_id=company_id)
    entities = get_legal_entities(company_id=company_id)

    if request.method == 'POST':
        notice_type = request.form.get('notice_type')
        notice_number = get_next_notice_number(notice_type, company_id)

        data = {
            'notice_number': notice_number,
            'notice_type': notice_type,
            'authority_id': request.form.get('authority_id'),
            'entity_id': request.form.get('entity_id'),
            'subject': request.form.get('subject'),
            'content': request.form.get('content'),
            'severity': request.form.get('severity', 'medium'),
            'issue_date': request.form.get('issue_date'),
            'due_date': request.form.get('due_date'),
            'response_deadline': request.form.get('response_deadline'),
            'status': 'received',
            'assigned_to': request.form.get('assigned_to'),
            'company_id': company_id,
            'created_by': get_current_user_id(),
        }

        try:
            notice_id = create_notice(data)
            log_audit('notice_created', user_id=get_current_user_id(), record_id=notice_id,
                     entity_type='legal_notice', details=f"Notice created: {notice_number}")
            flash("Notice created successfully.", "success")
            return redirect(url_for('legal_tax.notices_view', notice_id=notice_id))
        except Exception as e:
            flash(f"Error creating notice: {str(e)}", "error")

    return render_template('legal_tax/notices/create.html',
        title='Create Notice',
        authorities=authorities,
        entities=entities,
    )


@legal_tax_bp.route('/notices/<int:notice_id>/resolve', methods=['POST'])
@require_permission('legal_tax', 'notices', 'edit')
def notices_resolve(notice_id):
    """Resolve a notice."""
    notes = request.form.get('notes', '')
    try:
        resolve_notice(notice_id, get_current_user_id(), notes)
        log_audit('notice_resolved', user_id=get_current_user_id(), record_id=notice_id,
                 entity_type='legal_notice', details=f"Notice resolved")
        flash("Notice resolved.", "success")
    except Exception as e:
        flash(f"Error resolving notice: {str(e)}", "error")

    return redirect(url_for('legal_tax.notices_view', notice_id=notice_id))


@legal_tax_bp.route('/penalties')
@require_permission('legal_tax', 'penalties', 'view')
def penalties_list():
    """List all penalties."""
    company_id = get_company_id()
    status = request.args.get('status')

    penalties = get_penalties(company_id=company_id, status=status)

    return render_template('legal_tax/penalties/list.html',
        title='Penalties',
        penalties=penalties,
        selected_status=status,
    )


@legal_tax_bp.route('/penalties/create', methods=['GET', 'POST'])
@require_permission('legal_tax', 'penalties', 'create')
def penalties_create():
    """Create a new penalty."""
    company_id = get_company_id()
    authorities = get_tax_authorities(company_id=company_id)
    entities = get_legal_entities(company_id=company_id)

    if request.method == 'POST':
        penalty_type = request.form.get('penalty_type')
        penalty_number = get_next_penalty_number(penalty_type, company_id)

        data = {
            'penalty_number': penalty_number,
            'penalty_type': penalty_type,
            'notice_id': request.form.get('notice_id'),
            'authority_id': request.form.get('authority_id'),
            'entity_id': request.form.get('entity_id'),
            'description': request.form.get('description'),
            'amount': request.form.get('amount', 0),
            'currency': request.form.get('currency', 'USD'),
            'penalty_date': request.form.get('penalty_date'),
            'due_date': request.form.get('due_date'),
            'status': 'pending',
            'company_id': company_id,
            'created_by': get_current_user_id(),
        }

        try:
            penalty_id = create_penalty(data)
            log_audit('penalty_created', user_id=get_current_user_id(), record_id=penalty_id,
                     entity_type='legal_penalty', details=f"Penalty created: {penalty_number}")
            flash("Penalty created successfully.", "success")
            return redirect(url_for('legal_tax.penalties_list'))
        except Exception as e:
            flash(f"Error creating penalty: {str(e)}", "error")

    return render_template('legal_tax/penalties/create.html',
        title='Create Penalty',
        authorities=authorities,
        entities=entities,
    )


@legal_tax_bp.route('/disputes')
@require_permission('legal_tax', 'disputes', 'view')
def disputes_list():
    """List all disputes."""
    company_id = get_company_id()
    status = request.args.get('status')

    disputes = get_disputes(company_id=company_id, status=status)

    return render_template('legal_tax/disputes/list.html',
        title='Disputes',
        disputes=disputes,
        selected_status=status,
    )


@legal_tax_bp.route('/disputes/create', methods=['GET', 'POST'])
@require_permission('legal_tax', 'disputes', 'create')
def disputes_create():
    """Create a new dispute."""
    company_id = get_company_id()
    authorities = get_tax_authorities(company_id=company_id)
    entities = get_legal_entities(company_id=company_id)

    if request.method == 'POST':
        dispute_type = request.form.get('dispute_type')
        dispute_number = get_next_dispute_number(dispute_type, company_id)

        data = {
            'dispute_number': dispute_number,
            'dispute_type': dispute_type,
            'authority_id': request.form.get('authority_id'),
            'entity_id': request.form.get('entity_id'),
            'notice_id': request.form.get('notice_id'),
            'penalty_id': request.form.get('penalty_id'),
            'subject': request.form.get('subject'),
            'description': request.form.get('description'),
            'amount': request.form.get('amount', 0),
            'currency': request.form.get('currency', 'USD'),
            'filing_date': request.form.get('filing_date'),
            'hearing_date': request.form.get('hearing_date'),
            'status': 'open',
            'company_id': company_id,
            'created_by': get_current_user_id(),
        }

        try:
            dispute_id = create_dispute(data)
            log_audit('dispute_created', user_id=get_current_user_id(), record_id=dispute_id,
                     entity_type='legal_dispute', details=f"Dispute created: {dispute_number}")
            flash("Dispute created successfully.", "success")
            return redirect(url_for('legal_tax.disputes_list'))
        except Exception as e:
            flash(f"Error creating dispute: {str(e)}", "error")

    return render_template('legal_tax/disputes/create.html',
        title='Create Dispute',
        authorities=authorities,
        entities=entities,
    )


# ============================================================================
# COMPLIANCE TASKS
# ============================================================================

@legal_tax_bp.route('/compliance-tasks')
@require_permission('legal_tax', 'compliance_tasks', 'view')
def compliance_tasks_list():
    """List all compliance tasks."""
    company_id = get_company_id()
    status = request.args.get('status')
    assigned_to = request.args.get('assigned_to', type=int)

    tasks = get_compliance_tasks(company_id=company_id, status=status, assigned_to=assigned_to)

    return render_template('legal_tax/compliance_tasks/list.html',
        title='Compliance Tasks',
        tasks=tasks,
        selected_status=status,
    )


@legal_tax_bp.route('/compliance-tasks/create', methods=['GET', 'POST'])
@require_permission('legal_tax', 'compliance_tasks', 'create')
def compliance_tasks_create():
    """Create a new compliance task."""
    company_id = get_company_id()

    if request.method == 'POST':
        task_type = request.form.get('task_type')
        task_number = get_next_task_number(task_type, company_id)

        data = {
            'task_number': task_number,
            'task_type': task_type,
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'obligation_id': request.form.get('obligation_id'),
            'return_id': request.form.get('return_id'),
            'priority': request.form.get('priority', 'normal'),
            'status': 'pending',
            'due_date': request.form.get('due_date'),
            'assigned_to': request.form.get('assigned_to'),
            'notes': request.form.get('notes'),
            'company_id': company_id,
            'created_by': get_current_user_id(),
        }

        try:
            task_id = create_compliance_task(data)
            log_audit('compliance_task_created', user_id=get_current_user_id(), record_id=task_id,
                     entity_type='compliance_task', details=f"Task created: {task_number}")
            flash("Compliance task created successfully.", "success")
            return redirect(url_for('legal_tax.compliance_tasks_list'))
        except Exception as e:
            flash(f"Error creating task: {str(e)}", "error")

    return render_template('legal_tax/compliance_tasks/create.html',
        title='Create Compliance Task',
    )


@legal_tax_bp.route('/compliance-tasks/<int:task_id>/complete', methods=['POST'])
@require_permission('legal_tax', 'compliance_tasks', 'edit')
def compliance_tasks_complete(task_id):
    """Complete a compliance task."""
    try:
        complete_compliance_task(task_id, get_current_user_id())
        log_audit('compliance_task_completed', user_id=get_current_user_id(), record_id=task_id,
                 entity_type='compliance_task', details=f"Task completed")
        flash("Task completed.", "success")
    except Exception as e:
        flash(f"Error completing task: {str(e)}", "error")

    return redirect(url_for('legal_tax.compliance_tasks_list'))


# ============================================================================
# AUDIT PACK CENTER
# ============================================================================

@legal_tax_bp.route('/audit-packs')
@require_permission('legal_tax', 'audit_packs', 'view')
def audit_packs_list():
    """List all audit packs."""
    company_id = get_company_id()
    status = request.args.get('status')

    packs = get_audit_packs(company_id=company_id, status=status)

    return render_template('legal_tax/audit_packs/list.html',
        title='Audit Pack Center',
        packs=packs,
        selected_status=status,
    )


@legal_tax_bp.route('/audit-packs/create', methods=['GET', 'POST'])
@require_permission('legal_tax', 'audit_packs', 'create')
def audit_packs_create():
    """Create a new audit pack."""
    company_id = get_company_id()
    periods = get_filing_periods(company_id=company_id)
    jurisdictions = get_tax_jurisdictions(company_id=company_id)

    if request.method == 'POST':
        pack_type = request.form.get('pack_type')
        pack_number = get_next_pack_number(pack_type, company_id)

        data = {
            'pack_number': pack_number,
            'pack_name': request.form.get('pack_name'),
            'pack_type': pack_type,
            'period_id': request.form.get('period_id'),
            'jurisdiction_id': request.form.get('jurisdiction_id'),
            'entity_id': request.form.get('entity_id'),
            'status': 'draft',
            'notes': request.form.get('notes'),
            'company_id': company_id,
            'created_by': get_current_user_id(),
        }

        try:
            pack_id = create_audit_pack(data)
            log_audit('audit_pack_created', user_id=get_current_user_id(), record_id=pack_id,
                     entity_type='audit_pack', details=f"Audit pack created: {pack_number}")
            flash("Audit pack created successfully.", "success")
            return redirect(url_for('legal_tax.audit_packs_list'))
        except Exception as e:
            flash(f"Error creating audit pack: {str(e)}", "error")

    return render_template('legal_tax/audit_packs/create.html',
        title='Create Audit Pack',
        periods=periods,
        jurisdictions=jurisdictions,
    )


# ============================================================================
# REPORTS
# ============================================================================

@legal_tax_bp.route('/reports')
@require_permission('legal_tax', 'reports', 'view')
def reports_list():
    """List all reports."""
    company_id = get_company_id()
    templates = get_report_templates(company_id=company_id)

    return render_template('legal_tax/reports/list.html',
        title='Legal / Tax Reports',
        templates=templates,
    )


@legal_tax_bp.route('/reports/filing-calendar')
@require_permission('legal_tax', 'reports', 'view')
def report_filing_calendar():
    """Filing calendar report."""
    company_id = get_company_id()
    obligations = get_obligations(company_id=company_id)

    return render_template('legal_tax/reports/filing_calendar.html',
        title='Filing Calendar Report',
        obligations=obligations,
    )


@legal_tax_bp.route('/reports/filing-status')
@require_permission('legal_tax', 'reports', 'view')
def report_filing_status():
    """Filing status report."""
    company_id = get_company_id()
    returns = get_returns(company_id=company_id)

    return render_template('legal_tax/reports/filing_status.html',
        title='Filing Status Report',
        returns=returns,
    )


@legal_tax_bp.route('/reports/tax-exception')
@require_permission('legal_tax', 'reports', 'view')
def report_tax_exception():
    """Tax exception report."""
    company_id = get_company_id()
    review_items = get_tax_review_items(company_id=company_id)

    return render_template('legal_tax/reports/tax_exception.html',
        title='Tax Exception Report',
        review_items=review_items,
    )


@legal_tax_bp.route('/reports/obligation-summary')
@require_permission('legal_tax', 'reports', 'view')
def report_obligation_summary():
    """Obligation summary report."""
    company_id = get_company_id()
    obligations = get_obligations(company_id=company_id)
    overdue = get_overdue_obligations(company_id=company_id)

    return render_template('legal_tax/reports/obligation_summary.html',
        title='Obligation Summary Report',
        obligations=obligations,
        overdue_count=len(overdue) if overdue else 0,
    )


@legal_tax_bp.route('/reports/penalty-dispute')
@require_permission('legal_tax', 'reports', 'view')
def report_penalty_dispute():
    """Penalty and dispute report."""
    company_id = get_company_id()
    penalties = get_penalties(company_id=company_id)
    disputes = get_disputes(company_id=company_id)

    return render_template('legal_tax/reports/penalty_dispute.html',
        title='Penalty & Dispute Report',
        penalties=penalties,
        disputes=disputes,
    )


# ============================================================================
# EXPORT CENTER
# ============================================================================

@legal_tax_bp.route('/export-center')
@require_permission('legal_tax', 'export', 'view')
def export_center():
    """Export center page."""
    company_id = get_company_id()
    profiles = get_export_profiles(company_id=company_id)

    return render_template('legal_tax/export_center.html',
        title='Export Center',
        profiles=profiles,
        export_types=LEGAL_TAX_EXPORT_TYPES,
    )


@legal_tax_bp.route('/api/export/<export_type>', methods=['GET', 'POST'])
@require_permission('legal_tax', 'export', 'export')
def api_export(export_type):
    """API endpoint for exports."""
    if export_type not in LEGAL_TAX_EXPORT_TYPES:
        return jsonify({'error': 'Invalid export type'}), 400

    data_type = request.args.get('data_type', 'returns')
    company_id = get_company_id()

    columns = LEGAL_TAX_EXPORT_COLUMNS.get(data_type, [])
    data = []

    if data_type == 'returns':
        data = get_returns(company_id=company_id)
    elif data_type == 'jurisdictions':
        data = get_tax_jurisdictions(company_id=company_id)
    elif data_type == 'authorities':
        data = get_tax_authorities(company_id=company_id)
    elif data_type == 'obligations':
        data = get_obligations(company_id=company_id)
    elif data_type == 'review_items':
        data = get_tax_review_items(company_id=company_id)
    elif data_type == 'reconciliations':
        data = get_reconciliations(company_id=company_id)
    elif data_type == 'notices':
        data = get_notices(company_id=company_id)
    elif data_type == 'penalties':
        data = get_penalties(company_id=company_id)
    elif data_type == 'disputes':
        data = get_disputes(company_id=company_id)
    elif data_type == 'audit_packs':
        data = get_audit_packs(company_id=company_id)
    else:
        data = get_returns(company_id=company_id)

    filename = f"legal_tax_{data_type}_{export_type}"

    log_audit('legal_tax_export', user_id=get_current_user_id(),
             entity_type='export', details=f"Exported {data_type} as {export_type}")

    return send_export_response(data, export_type, filename, columns, f"Legal/Tax {data_type.title()} Report")


# ============================================================================
# SETTINGS
# ============================================================================

@legal_tax_bp.route('/settings')
@require_permission('legal_tax', 'settings', 'view')
def settings_page():
    """Settings page."""
    company_id = get_company_id()
    settings = get_legal_tax_settings(company_id=company_id)
    jurisdictions = get_tax_jurisdictions(company_id=company_id)

    return render_template('legal_tax/settings.html',
        title='Legal / Tax Settings',
        settings=settings,
        jurisdictions=jurisdictions,
    )


@legal_tax_bp.route('/settings/save', methods=['POST'])
@require_permission('legal_tax', 'settings', 'edit')
def settings_save():
    """Save settings."""
    company_id = get_company_id()

    data = {
        'jurisdiction_id': request.form.get('jurisdiction_id'),
        'filing_frequency': request.form.get('filing_frequency'),
        'default_approval_workflow': request.form.get('default_approval_workflow'),
        'auto_reminder_days': request.form.get('auto_reminder_days', 7),
        'reminder_repeat_days': request.form.get('reminder_repeat_days', 3),
        'late_filing_penalty_rate': request.form.get('late_filing_penalty_rate', 0),
        'late_payment_penalty_rate': request.form.get('late_payment_penalty_rate', 0),
        'require_attachment_for_filing': 1 if request.form.get('require_attachment_for_filing') else 0,
        'allow_amendment_after_filing': 1 if request.form.get('allow_amendment_after_filing') else 0,
        'lock_period_after_filing': 1 if request.form.get('lock_period_after_filing') else 0,
        'risk_score_threshold': request.form.get('risk_score_threshold', 70),
        'default_currency': request.form.get('default_currency', 'USD'),
        'enable_auto_reconciliation': 1 if request.form.get('enable_auto_reconciliation') else 0,
    }

    try:
        save_legal_tax_settings(data, company_id)
        log_audit('legal_settings_updated', user_id=get_current_user_id(),
                 entity_type='legal_settings', details=f"Settings updated")
        flash("Settings saved successfully.", "success")
    except Exception as e:
        flash(f"Error saving settings: {str(e)}", "error")

    return redirect(url_for('legal_tax.settings_page'))


# ============================================================================
# SAMPLE DATA
# ============================================================================

@legal_tax_bp.route('/sample-data')
@require_permission('legal_tax', 'settings', 'view')
def sample_data_page():
    """Sample data management page."""
    company_id = get_company_id()

    jurisdictions = get_tax_jurisdictions(company_id=company_id)
    authorities = get_tax_authorities(company_id=company_id)
    entities = get_legal_entities(company_id=company_id)
    obligations = get_obligations(company_id=company_id)

    return render_template('legal_tax/sample_data.html',
        title='Sample Data',
        jurisdictions=jurisdictions,
        authorities=authorities,
        entities=entities,
        obligations=obligations,
        has_data=len(jurisdictions) > 0,
    )


@legal_tax_bp.route('/sample-data/generate', methods=['POST'])
@require_permission('legal_tax', 'settings', 'edit')
def sample_data_generate():
    """Generate sample data."""
    try:
        from seed_legal_tax_data import seed_legal_tax_data
        seed_legal_tax_data()
        log_audit('legal_sample_data_generated', user_id=get_current_user_id(),
                 entity_type='seed_data', details=f"Sample data generated")
        flash("Sample data generated successfully.", "success")
    except Exception as e:
        flash(f"Error generating sample data: {str(e)}", "error")

    return redirect(url_for('legal_tax.sample_data_page'))


# ============================================================================
# REGISTER LEGAL/TAX ROUTES
# ============================================================================

def register_legal_tax_routes(app):
    """Register legal/tax routes with the Flask app."""
    app.register_blueprint(legal_tax_bp)
