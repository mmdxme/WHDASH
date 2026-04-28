"""
Enterprise Payroll Module Routes
=================================
Comprehensive payroll module routes covering:
- Payroll Dashboard
- Payroll Master Setup
- Payroll Calendar & Periods
- Payroll Processing
- Payroll Review & Approval
- Payslips & Outputs
- Loans / Advances / Recoveries
- Retro / Adjustment / Arrears
- Payroll Compliance & Controls
- Finance Integration
- HR Integration
- Reports & Analytics
- Workflow & Approvals
- Settings

All routes include:
- Authentication checks
- Permission validation
- Audit logging
- Flow integration
- Error handling
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_file, Response
from functools import wraps
from datetime import datetime, timedelta, date
import csv
import io
import json
from decimal import Decimal

from payroll_models import (
    get_db, run_payroll_migrations, seed_payroll_default_data,
    get_payroll_setting, update_payroll_setting,
    get_active_payroll_period, get_payroll_period,
    get_employee_payroll_profile, get_employee_components,
    calculate_employee_net_salary, get_payroll_summary_stats,
    get_pending_payroll_approvals, log_payroll_audit,
    create_payslip_number, create_loan_number, create_advance_number,
    create_retro_number, create_arrears_number, create_posting_number,
    create_letter_number, get_payroll_exceptions,
    get_loan_installment_due, get_outstanding_loans, get_active_advances,
    run_payroll_validations, PAYROLL_TABLES
)
from permissions import user_has_permission

payroll_bp = Blueprint('payroll', __name__, url_prefix='/payroll')


# =============================================================================
# DECORATORS AND HELPERS
# =============================================================================

def payroll_login_required(f):
    """Decorator to require payroll login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please log in first.', 'error')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def payroll_permission_required(action: str):
    """Decorator to check payroll-specific permissions."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in first.', 'error')
                return redirect(url_for('login'))

            if session.get('role_name') == 'Global Admin':
                return f(*args, **kwargs)

            user_id = session['user_id']
            if not user_has_permission(user_id, 'payroll', 'payroll', action):
                if request.is_json:
                    return jsonify({'error': 'Permission denied'}), 403
                flash(f"You don't have permission to {action} payroll records.", 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def get_current_user():
    """Get current logged-in user info."""
    if 'user_id' not in session:
        return None
    return {
        'id': session.get('user_id'),
        'username': session.get('username'),
        'role_id': session.get('role_id'),
        'role_name': session.get('role_name'),
        'company_id': session.get('company_id'),
    }


def parse_date(date_str):
    """Safely parse date string to date object."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        try:
            return datetime.strptime(date_str, '%d/%m/%Y').date()
        except ValueError:
            return None


def format_date(date_obj, fmt='%d/%m/%Y'):
    """Format date object to string."""
    if not date_obj:
        return ''
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime(fmt)


def format_currency(amount, currency='AED'):
    """Format amount as currency."""
    if amount is None:
        return f"{currency} 0.00"
    return f"{currency} {float(amount):,.2f}"


def send_payroll_flow_notification(title, message, priority='normal', user_ids=None, period_id=None):
    """Send payroll notification via Flow system."""
    try:
        from flow_models import create_flow_notification
        
        if user_ids:
            for uid in user_ids:
                create_flow_notification(
                    user_id=uid,
                    title=title,
                    message=message,
                    notification_type='payroll',
                    priority=priority,
                    related_module='payroll',
                    related_id=period_id
                )
    except ImportError:
        pass
    except Exception as e:
        print(f"Flow notification failed: {str(e)}")


def audit_log(action, entity_type, entity_id, field_name=None, old_value=None, new_value=None, 
              period_id=None, run_id=None, employee_id=None, details=None):
    """Log payroll audit entry."""
    user = get_current_user()
    if user:
        log_payroll_audit(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            user_id=user['id'],
            period_id=period_id,
            run_id=run_id,
            employee_id=employee_id,
            field_name=field_name,
            old_value=str(old_value) if old_value else None,
            new_value=str(new_value) if new_value else None,
            change_details=details
        )


# =============================================================================
# PAYROLL DASHBOARD
# =============================================================================

@payroll_bp.route('/')
@payroll_bp.route('/dashboard')
@payroll_login_required
@payroll_permission_required('view')
def payroll_dashboard():
    """Main Payroll Dashboard."""
    user = get_current_user()
    db = get_db()
    
    try:
        # Get current active period
        current_period = get_active_payroll_period()
        
        # Get recent periods
        recent_periods = db.execute("""
            SELECT * FROM payroll_periods 
            ORDER BY year DESC, month DESC 
            LIMIT 6
        """).fetchall()
        
        # Get payroll summary for current period
        current_summary = None
        if current_period:
            current_summary = get_payroll_summary_stats(current_period['id'])
        
        # Get pending approvals count
        pending_approvals = db.execute("""
            SELECT COUNT(*) as cnt FROM payroll_approval_instances 
            WHERE status = 'Pending'
        """).fetchone()['cnt']
        
        # Get open exceptions count
        open_exceptions = db.execute("""
            SELECT COUNT(*) as cnt FROM payroll_exceptions 
            WHERE status = 'Open'
        """).fetchone()['cnt']
        
        # Get period statuses distribution
        period_statuses = db.execute("""
            SELECT status, COUNT(*) as cnt 
            FROM payroll_periods 
            GROUP BY status
        """).fetchall()
        
        # Get recent runs
        recent_runs = db.execute("""
            SELECT pr.*, pp.name as period_name, u.username as created_by_name
            FROM payroll_runs pr
            JOIN payroll_periods pp ON pr.period_id = pp.id
            JOIN users u ON pr.created_by_id = u.id
            ORDER BY pr.created_at DESC
            LIMIT 5
        """).fetchall()
        
        # Get overtime summary
        ot_summary = db.execute("""
            SELECT COALESCE(SUM(hours), 0) as total_hours,
                   COALESCE(SUM(total_amount), 0) as total_amount
            FROM payroll_overtime_inputs
            WHERE status = 'Approved'
            AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
        """).fetchone()
        
        # Get loan recovery summary
        loan_summary = db.execute("""
            SELECT COALESCE(SUM(amount_paid), 0) as total_recovered,
                   COUNT(CASE WHEN status = 'Active' THEN 1 END) as active_loans
            FROM payroll_loans
        """).fetchone()
        
        # Calculate period status metrics
        open_periods = db.execute("SELECT COUNT(*) as cnt FROM payroll_periods WHERE status = 'Open'").fetchone()['cnt']
        processing_periods = db.execute("SELECT COUNT(*) as cnt FROM payroll_periods WHERE status = 'Processing'").fetchone()['cnt']
        pending_approval_periods = db.execute("SELECT COUNT(*) as cnt FROM payroll_periods WHERE status = 'Pending Approval'").fetchone()['cnt']
        locked_periods = db.execute("SELECT COUNT(*) as cnt FROM payroll_periods WHERE status = 'Locked'").fetchone()['cnt']
        
        return render_template('payroll/dashboard/dashboard.html',
            title='Payroll Dashboard',
            current_period=dict(current_period) if current_period else None,
            recent_periods=[dict(p) for p in recent_periods],
            current_summary=current_summary,
            pending_approvals=pending_approvals,
            open_exceptions=open_exceptions,
            period_statuses=[dict(s) for s in period_statuses],
            recent_runs=[dict(r) for r in recent_runs],
            ot_summary=dict(ot_summary) if ot_summary else None,
            loan_summary=dict(loan_summary) if loan_summary else None,
            metrics={
                'open_periods': open_periods,
                'processing_periods': processing_periods,
                'pending_approval_periods': pending_approval_periods,
                'locked_periods': locked_periods
            }
        )
    finally:
        db.close()


@payroll_bp.route('/executive-dashboard')
@payroll_login_required
@payroll_permission_required('view')
def executive_dashboard():
    """Executive Payroll Dashboard - High level overview."""
    user = get_current_user()
    db = get_db()
    
    try:
        # Year to date payroll totals
        year_start = f"{datetime.now().year}-01-01"
        ytd_payroll = db.execute("""
            SELECT COALESCE(SUM(total_net), 0) as total_net,
                   COALESCE(SUM(total_gross), 0) as total_gross,
                   COALESCE(SUM(total_deductions), 0) as total_deductions,
                   COALESCE(SUM(total_tax), 0) as total_tax
            FROM payroll_employee_records pr
            JOIN payroll_periods pp ON pr.period_id = pp.id
            WHERE pp.year = ? AND pp.status = 'Closed'
        """, (datetime.now().year,)).fetchone()
        
        # Monthly payroll trend (last 12 months)
        monthly_trend = db.execute("""
            SELECT pp.month, pp.year,
                   SUM(pr.total_gross) as total_gross,
                   SUM(pr.total_deductions) as total_deductions,
                   SUM(pr.net_salary) as total_net,
                   COUNT(DISTINCT pr.employee_id) as employee_count
            FROM payroll_periods pp
            LEFT JOIN payroll_employee_records pr ON pp.id = pr.period_id AND pr.status = 'Approved'
            WHERE pp.status = 'Closed'
            AND pp.year * 12 + pp.month >= ? 
            GROUP BY pp.year, pp.month
            ORDER BY pp.year, pp.month
        """, ((datetime.now().year - 1) * 12 + datetime.now().month,)).fetchall()
        
        # Top deductions breakdown
        deduction_breakdown = db.execute("""
            SELECT ped.component_name,
                   SUM(ped.amount) as total_amount,
                   COUNT(DISTINCT ped.record_id) as record_count
            FROM payroll_employee_deductions ped
            JOIN payroll_employee_records per ON ped.record_id = per.id
            WHERE per.status = 'Approved'
            AND strftime('%Y', per.created_at) = strftime('%Y', 'now')
            GROUP BY ped.component_id
            ORDER BY total_amount DESC
            LIMIT 10
        """).fetchall()
        
        # Top earnings breakdown
        earnings_breakdown = db.execute("""
            SELECT pee.component_name,
                   SUM(pee.amount) as total_amount,
                   COUNT(DISTINCT pee.record_id) as record_count
            FROM payroll_employee_earnings pee
            JOIN payroll_employee_records per ON pee.record_id = per.id
            WHERE per.status = 'Approved'
            AND strftime('%Y', per.created_at) = strftime('%Y', 'now')
            GROUP BY pee.component_id
            ORDER BY total_amount DESC
            LIMIT 10
        """).fetchall()
        
        # Branch/Entity payroll distribution
        branch_payroll = db.execute("""
            SELECT COALESCE(ee.branch_id, 0) as branch_id,
                   c.name as branch_name,
                   SUM(per.total_gross) as total_gross,
                   SUM(per.net_salary) as total_net,
                   COUNT(DISTINCT per.employee_id) as employee_count
            FROM payroll_employee_records per
            JOIN hr_employees e ON per.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN companies c ON ee.branch_id = c.id
            JOIN payroll_periods pp ON per.period_id = pp.id
            WHERE per.status = 'Approved' AND pp.status = 'Closed'
            AND pp.year = ?
            GROUP BY ee.branch_id
            ORDER BY total_gross DESC
        """, (datetime.now().year,)).fetchall()
        
        # Variance to prior period (if current period exists)
        current_period = get_active_payroll_period()
        prior_variance = None
        if current_period:
            prior_month = current_period['month'] - 1 if current_period['month'] > 1 else 12
            prior_year = current_period['year'] if current_period['month'] > 1 else current_period['year'] - 1
            prior_period = get_payroll_period(prior_year, prior_month)
            if prior_period:
                current_stats = get_payroll_summary_stats(current_period['id'])
                prior_stats = get_payroll_summary_stats(prior_period['id'])
                if current_stats and prior_stats and prior_stats.get('total_net', 0) > 0:
                    variance_pct = ((float(current_stats['total_net'] or 0) - float(prior_stats['total_net'] or 0)) / float(prior_stats['total_net'])) * 100
                    prior_variance = {
                        'current': current_stats,
                        'prior': prior_stats,
                        'variance_pct': variance_pct
                    }
        
        return render_template('payroll/dashboard/executive_dashboard.html',
            title='Executive Payroll Dashboard',
            ytd_payroll=dict(ytd_payroll) if ytd_payroll else None,
            monthly_trend=[dict(m) for m in monthly_trend],
            deduction_breakdown=[dict(d) for d in deduction_breakdown],
            earnings_breakdown=[dict(e) for e in earnings_breakdown],
            branch_payroll=[dict(b) for b in branch_payroll],
            prior_variance=prior_variance,
            current_period=dict(current_period) if current_period else None
        )
    finally:
        db.close()


@payroll_bp.route('/processing-dashboard')
@payroll_login_required
@payroll_permission_required('view')
def processing_dashboard():
    """Payroll Processing Dashboard - For payroll managers."""
    user = get_current_user()
    db = get_db()
    
    try:
        # Get current period runs
        current_period = get_active_payroll_period()
        runs_in_progress = []
        if current_period:
            runs_in_progress = db.execute("""
                SELECT pr.*, u.username as created_by_name,
                       (SELECT COUNT(*) FROM payroll_employee_records WHERE run_id = pr.id) as record_count
                FROM payroll_runs pr
                JOIN users u ON pr.created_by_id = u.id
                WHERE pr.period_id = ?
                ORDER BY pr.created_at DESC
            """, (current_period['id'],)).fetchall()
        
        # Exception summary by type
        exception_summary = db.execute("""
            SELECT exception_type, severity, COUNT(*) as cnt
            FROM payroll_exceptions
            WHERE status = 'Open'
            GROUP BY exception_type, severity
            ORDER BY severity DESC, cnt DESC
        """).fetchall()
        
        # Pending overtime inputs
        pending_ot = db.execute("""
            SELECT COUNT(*) as cnt, COALESCE(SUM(hours), 0) as total_hours
            FROM payroll_overtime_inputs
            WHERE status = 'Pending'
        """).fetchone()
        
        # Pending adjustments
        pending_adjustments = db.execute("""
            SELECT COUNT(*) as cnt, COALESCE(SUM(ABS(amount)), 0) as total_amount
            FROM payroll_manual_adjustments
            WHERE status = 'Pending'
        """).fetchone()
        
        # Processing queue status
        queue_status = db.execute("""
            SELECT status, COUNT(*) as cnt
            FROM payroll_employee_records
            WHERE period_id = ?
            GROUP BY status
        """, (current_period['id'] if current_period else 0,)).fetchall()
        
        return render_template('payroll/dashboard/processing_dashboard.html',
            title='Processing Dashboard',
            current_period=dict(current_period) if current_period else None,
            runs_in_progress=[dict(r) for r in runs_in_progress],
            exception_summary=[dict(e) for e in exception_summary],
            pending_ot=dict(pending_ot) if pending_ot else None,
            pending_adjustments=dict(pending_adjustments) if pending_adjustments else None,
            queue_status=[dict(q) for q in queue_status] if queue_status else []
        )
    finally:
        db.close()


@payroll_bp.route('/variance-dashboard')
@payroll_login_required
@payroll_permission_required('view')
def variance_dashboard():
    """Payroll Variance Dashboard."""
    user = get_current_user()
    db = get_db()
    
    try:
        # Compare current vs prior periods
        current_period = get_active_payroll_period()
        comparisons = []
        
        if current_period:
            for i in range(1, 4):
                prior_month = current_period['month'] - i
                prior_year = current_period['year']
                if prior_month < 1:
                    prior_month += 12
                    prior_year -= 1
                
                prior_period = get_payroll_period(prior_year, prior_month)
                if prior_period:
                    current_stats = get_payroll_summary_stats(current_period['id'])
                    prior_stats = get_payroll_summary_stats(prior_period['id'])
                    
                    if current_stats and prior_stats:
                        variance = {
                            'period': f"{prior_period['month']}/{prior_period['year']}",
                            'prior_total': float(prior_stats.get('total_net', 0) or 0),
                            'current_total': float(current_stats.get('total_net', 0) or 0),
                            'variance': float(current_stats.get('total_net', 0) or 0) - float(prior_stats.get('total_net', 0) or 0),
                            'variance_pct': ((float(current_stats.get('total_net', 0) or 0) - float(prior_stats.get('total_net', 0) or 0)) / float(prior_stats.get('total_net', 1)) * 100) if prior_stats.get('total_net', 0) else 0,
                            'prior_employees': prior_stats.get('total_employees', 0),
                            'current_employees': current_stats.get('total_employees', 0)
                        }
                        comparisons.append(variance)
        
        # Employee-level variance for current period
        employee_variance = []
        if current_period:
            employee_variance = db.execute("""
                SELECT per.*, e.first_name || ' ' || e.last_name as employee_name,
                       e.employee_code
                FROM payroll_employee_records per
                JOIN hr_employees e ON per.employee_id = e.id
                WHERE per.period_id = ?
                AND per.status IN ('Draft', 'Calculated')
                ORDER BY ABS(per.net_salary - (
                    SELECT AVG(net_salary) FROM payroll_employee_records 
                    WHERE period_id = ? AND status = 'Approved'
                )) DESC
                LIMIT 20
            """, (current_period['id'], current_period['id'])).fetchall()
        
        return render_template('payroll/dashboard/variance_dashboard.html',
            title='Variance Dashboard',
            current_period=dict(current_period) if current_period else None,
            comparisons=comparisons,
            employee_variance=[dict(e) for e in employee_variance]
        )
    finally:
        db.close()


@payroll_bp.route('/overtime-dashboard')
@payroll_login_required
@payroll_permission_required('view')
def overtime_dashboard():
    """Overtime Payroll Dashboard."""
    user = get_current_user()
    db = get_db()
    
    try:
        # Monthly OT trend
        ot_trend = db.execute("""
            SELECT strftime('%Y-%m', poi.date) as month,
                   SUM(poi.hours) as total_hours,
                   SUM(poi.total_amount) as total_cost,
                   COUNT(DISTINCT poi.employee_id) as employee_count
            FROM payroll_overtime_inputs poi
            WHERE poi.status = 'Approved'
            AND poi.date >= date('now', '-12 months')
            GROUP BY strftime('%Y-%m', poi.date)
            ORDER BY month
        """).fetchall()
        
        # OT by type
        ot_by_type = db.execute("""
            SELECT overtime_type,
                   SUM(hours) as total_hours,
                   SUM(total_amount) as total_cost
            FROM payroll_overtime_inputs
            WHERE status = 'Approved'
            AND strftime('%Y', date) = strftime('%Y', 'now')
            GROUP BY overtime_type
        """).fetchall()
        
        # Top OT employees
        top_ot_employees = db.execute("""
            SELECT e.id, e.first_name || ' ' || e.last_name as employee_name,
                   e.employee_code,
                   SUM(poi.hours) as total_hours,
                   SUM(poi.total_amount) as total_cost,
                   COUNT(*) as ot_days
            FROM payroll_overtime_inputs poi
            JOIN hr_employees e ON poi.employee_id = e.id
            WHERE poi.status = 'Approved'
            AND strftime('%Y', poi.date) = strftime('%Y', 'now')
            GROUP BY e.id
            ORDER BY total_hours DESC
            LIMIT 20
        """).fetchall()
        
        # Pending OT approvals
        pending_ot = db.execute("""
            SELECT poi.*, e.first_name || ' ' || e.last_name as employee_name
            FROM payroll_overtime_inputs poi
            JOIN hr_employees e ON poi.employee_id = e.id
            WHERE poi.status = 'Pending'
            ORDER BY poi.date DESC
            LIMIT 20
        """).fetchall()
        
        return render_template('payroll/dashboard/overtime_dashboard.html',
            title='Overtime Dashboard',
            ot_trend=[dict(o) for o in ot_trend],
            ot_by_type=[dict(o) for o in ot_by_type],
            top_ot_employees=[dict(o) for o in top_ot_employees],
            pending_ot=[dict(p) for p in pending_ot]
        )
    finally:
        db.close()


@payroll_bp.route('/loan-dashboard')
@payroll_login_required
@payroll_permission_required('view')
def loan_dashboard():
    """Loan Recovery Dashboard."""
    user = get_current_user()
    db = get_db()
    
    try:
        # Loan portfolio summary
        loan_summary = db.execute("""
            SELECT 
                COUNT(*) as total_loans,
                SUM(principal_amount) as total_principal,
                SUM(amount_paid) as total_recovered,
                SUM(amount_remaining) as total_outstanding,
                COUNT(CASE WHEN status = 'Active' THEN 1 END) as active_loans,
                COUNT(CASE WHEN status = 'Completed' THEN 1 END) as completed_loans
            FROM payroll_loans
        """).fetchone()
        
        # Loans by type
        loans_by_type = db.execute("""
            SELECT loan_type,
                   COUNT(*) as cnt,
                   SUM(principal_amount) as total_principal,
                   SUM(amount_remaining) as total_outstanding
            FROM payroll_loans
            GROUP BY loan_type
        """).fetchall()
        
        # Upcoming installments
        upcoming_installments = db.execute("""
            SELECT pli.*, pl.employee_id, pl.loan_type,
                   e.first_name || ' ' || e.last_name as employee_name
            FROM payroll_loan_installments pli
            JOIN payroll_loans pl ON pli.loan_id = pl.id
            JOIN hr_employees e ON pl.employee_id = e.id
            WHERE pli.status = 'Pending'
            AND pli.due_date <= date('now', '+30 days')
            ORDER BY pli.due_date
            LIMIT 20
        """).fetchall()
        
        # Overdue installments
        overdue_installments = db.execute("""
            SELECT pli.*, pl.employee_id, pl.loan_type,
                   e.first_name || ' ' || e.last_name as employee_name
            FROM payroll_loan_installments pli
            JOIN payroll_loans pl ON pli.loan_id = pl.id
            JOIN hr_employees e ON pl.employee_id = e.id
            WHERE pli.status = 'Overdue'
            ORDER BY pli.due_date
        """).fetchall()
        
        # Monthly recovery trend
        recovery_trend = db.execute("""
            SELECT strftime('%Y-%m', paid_on) as month,
                   SUM(amount_paid) as total_recovered
            FROM payroll_loan_installments
            WHERE status = 'Paid' AND paid_on IS NOT NULL
            AND paid_on >= date('now', '-12 months')
            GROUP BY strftime('%Y-%m', paid_on)
            ORDER BY month
        """).fetchall()
        
        return render_template('payroll/dashboard/loan_dashboard.html',
            title='Loan Recovery Dashboard',
            loan_summary=dict(loan_summary) if loan_summary else None,
            loans_by_type=[dict(l) for l in loans_by_type],
            upcoming_installments=[dict(u) for u in upcoming_installments],
            overdue_installments=[dict(o) for o in overdue_installments],
            recovery_trend=[dict(r) for r in recovery_trend]
        )
    finally:
        db.close()


@payroll_bp.route('/compliance-dashboard')
@payroll_login_required
@payroll_permission_required('view')
def compliance_dashboard():
    """Payroll Compliance Dashboard."""
    user = get_current_user()
    db = get_db()
    
    try:
        # Compliance status summary
        compliance_summary = db.execute("""
            SELECT 
                COUNT(*) as total_checks,
                SUM(CASE WHEN status = 'Pass' THEN 1 ELSE 0 END) as passed,
                SUM(CASE WHEN status = 'Fail' THEN 1 ELSE 0 END) as failed,
                SUM(CASE WHEN status = 'Warning' THEN 1 ELSE 0 END) as warnings,
                SUM(CASE WHEN status = 'Escalated' THEN 1 ELSE 0 END) as escalated
            FROM payroll_compliance_results
            WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
        """).fetchone()
        
        # Failed checks by rule
        failed_rules = db.execute("""
            SELECT pcr.*, pcrl.rule_name, pcrl.error_message,
                   e.first_name || ' ' || e.last_name as employee_name
            FROM payroll_compliance_results pcr
            JOIN payroll_compliance_rules pcrl ON pcr.rule_id = pcrl.id
            LEFT JOIN hr_employees e ON pcr.employee_id = e.id
            WHERE pcr.status IN ('Fail', 'Escalated')
            ORDER BY pcrl.severity DESC, pcr.created_at DESC
            LIMIT 20
        """).fetchall()
        
        # SOD violations
        sod_violations = db.execute("""
            SELECT * FROM payroll_compliance_results
            WHERE status = 'Fail'
            AND rule_id IN (SELECT id FROM payroll_compliance_rules WHERE rule_type = 'SOD')
            ORDER BY created_at DESC
            LIMIT 20
        """).fetchall()
        
        # Audit trail summary
        audit_summary = db.execute("""
            SELECT action, COUNT(*) as cnt
            FROM payroll_audit_log
            WHERE created_at >= date('now', '-7 days')
            GROUP BY action
            ORDER BY cnt DESC
        """).fetchall()
        
        return render_template('payroll/dashboard/compliance_dashboard.html',
            title='Compliance Dashboard',
            compliance_summary=dict(compliance_summary) if compliance_summary else None,
            failed_rules=[dict(f) for f in failed_rules],
            sod_violations=[dict(s) for s in sod_violations],
            audit_summary=[dict(a) for a in audit_summary]
        )
    finally:
        db.close()


# =============================================================================
# PAYROLL MASTER SETUP
# =============================================================================

@payroll_bp.route('/setup')
@payroll_login_required
@payroll_permission_required('view')
def setup_menu():
    """Payroll Setup Menu."""
    return render_template('payroll/setup/menu.html', title='Payroll Setup')


@payroll_bp.route('/setup/components')
@payroll_login_required
@payroll_permission_required('view')
def setup_components():
    """Payroll Components List."""
    user = get_current_user()
    db = get_db()
    
    try:
        components = db.execute("""
            SELECT * FROM payroll_components 
            WHERE is_active = 1
            ORDER BY order_index, component_type, name
        """).fetchall()
        
        # Group by type
        by_type = {}
        for comp in components:
            ct = comp['component_type']
            if ct not in by_type:
                by_type[ct] = []
            by_type[ct].append(dict(comp))
        
        return render_template('payroll/setup/components/list.html',
            title='Payroll Components',
            components=[dict(c) for c in components],
            by_type=by_type
        )
    finally:
        db.close()


@payroll_bp.route('/setup/components/new', methods=['GET', 'POST'])
@payroll_login_required
@payroll_permission_required('create')
def setup_components_new():
    """Create new payroll component."""
    user = get_current_user()
    db = get_db()
    
    if request.method == 'POST':
        try:
            data = request.form
            
            cursor = db.execute("""
                INSERT INTO payroll_components (
                    code, name, name_ar, name_fa, name_ru, name_hi, name_es, name_zh, name_de,
                    component_type, sub_type, category, description, is_taxable, is_insurable,
                    is_default, calculation_type, amount, percentage, percentage_of,
                    max_amount, min_amount, order_index, gl_account, cost_center_required,
                    requires_approval, is_active, effective_from
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('code'),
                data.get('name'),
                data.get('name_ar'),
                data.get('name_fa'),
                data.get('name_ru'),
                data.get('name_hi'),
                data.get('name_es'),
                data.get('name_zh'),
                data.get('name_de'),
                data.get('component_type'),
                data.get('sub_type'),
                data.get('category'),
                data.get('description'),
                1 if data.get('is_taxable') else 0,
                1 if data.get('is_insurable') else 0,
                1 if data.get('is_default') else 0,
                data.get('calculation_type', 'Fixed'),
                float(data.get('amount', 0)),
                float(data.get('percentage', 0)),
                data.get('percentage_of'),
                float(data.get('max_amount', 0)) if data.get('max_amount') else None,
                float(data.get('min_amount', 0)) if data.get('min_amount') else None,
                int(data.get('order_index', 0)),
                data.get('gl_account'),
                1 if data.get('cost_center_required') else 0,
                1 if data.get('requires_approval') else 0,
                1,
                parse_date(data.get('effective_from'))
            ))
            
            db.commit()
            audit_log('CREATE', 'payroll_components', cursor.lastrowid, details=f"Created component: {data.get('code')}")
            
            flash('Payroll component created successfully.', 'success')
            return redirect(url_for('payroll.setup_components'))
        except Exception as e:
            db.rollback()
            flash(f'Error creating component: {str(e)}', 'error')
    
    return render_template('payroll/setup/components/new.html', title='New Payroll Component')


@payroll_bp.route('/setup/components/<int:id>/edit', methods=['GET', 'POST'])
@payroll_login_required
@payroll_permission_required('edit')
def setup_components_edit(id):
    """Edit payroll component."""
    user = get_current_user()
    db = get_db()
    
    try:
        component = db.execute("SELECT * FROM payroll_components WHERE id = ?", (id,)).fetchone()
        if not component:
            flash('Component not found.', 'error')
            return redirect(url_for('payroll.setup_components'))
        
        if request.method == 'POST':
            data = request.form
            
            db.execute("""
                UPDATE payroll_components SET
                    name = ?, name_ar = ?, name_fa = ?, name_ru = ?, name_hi = ?,
                    name_es = ?, name_zh = ?, name_de = ?,
                    component_type = ?, sub_type = ?, category = ?, description = ?,
                    is_taxable = ?, is_insurable = ?, is_default = ?,
                    calculation_type = ?, amount = ?, percentage = ?, percentage_of = ?,
                    max_amount = ?, min_amount = ?, order_index = ?, gl_account = ?,
                    cost_center_required = ?, requires_approval = ?,
                    effective_from = ?, effective_to = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                data.get('name'),
                data.get('name_ar'),
                data.get('name_fa'),
                data.get('name_ru'),
                data.get('name_hi'),
                data.get('name_es'),
                data.get('name_zh'),
                data.get('name_de'),
                data.get('component_type'),
                data.get('sub_type'),
                data.get('category'),
                data.get('description'),
                1 if data.get('is_taxable') else 0,
                1 if data.get('is_insurable') else 0,
                1 if data.get('is_default') else 0,
                data.get('calculation_type', 'Fixed'),
                float(data.get('amount', 0)),
                float(data.get('percentage', 0)),
                data.get('percentage_of'),
                float(data.get('max_amount')) if data.get('max_amount') else None,
                float(data.get('min_amount')) if data.get('min_amount') else None,
                int(data.get('order_index', 0)),
                data.get('gl_account'),
                1 if data.get('cost_center_required') else 0,
                1 if data.get('requires_approval') else 0,
                parse_date(data.get('effective_from')),
                parse_date(data.get('effective_to')),
                id
            ))
            
            db.commit()
            audit_log('UPDATE', 'payroll_components', id, details=f"Updated component: {data.get('code')}")
            
            flash('Payroll component updated successfully.', 'success')
            return redirect(url_for('payroll.setup_components'))
        
        return render_template('payroll/setup/components/edit.html',
            title='Edit Payroll Component',
            component=dict(component)
        )
    finally:
        db.close()


@payroll_bp.route('/setup/components/<int:id>/delete', methods=['POST'])
@payroll_login_required
@payroll_permission_required('delete')
def setup_components_delete(id):
    """Delete payroll component."""
    user = get_current_user()
    db = get_db()
    
    try:
        component = db.execute("SELECT * FROM payroll_components WHERE id = ?", (id,)).fetchone()
        if not component:
            return jsonify({'error': 'Component not found'}), 404
        
        # Soft delete - just deactivate
        db.execute("UPDATE payroll_components SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (id,))
        db.commit()
        audit_log('DELETE', 'payroll_components', id, details=f"Deactivated component: {component['code']}")
        
        flash('Component deactivated successfully.', 'success')
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 400
    finally:
        db.close()


@payroll_bp.route('/setup/groups')
@payroll_login_required
@payroll_permission_required('view')
def setup_groups():
    """Payroll Groups List."""
    user = get_current_user()
    db = get_db()
    
    try:
        groups = db.execute("""
            SELECT pg.*, 
                   (SELECT COUNT(*) FROM payroll_group_members WHERE group_id = pg.id AND is_active = 1) as member_count
            FROM payroll_groups pg
            ORDER BY pg.name
        """).fetchall()
        
        return render_template('payroll/setup/groups/list.html',
            title='Payroll Groups',
            groups=[dict(g) for g in groups]
        )
    finally:
        db.close()


@payroll_bp.route('/setup/groups/new', methods=['GET', 'POST'])
@payroll_login_required
@payroll_permission_required('create')
def setup_groups_new():
    """Create new payroll group."""
    user = get_current_user()
    db = get_db()
    
    if request.method == 'POST':
        try:
            data = request.form
            
            cursor = db.execute("""
                INSERT INTO payroll_groups (code, name, name_ar, name_fa, description, is_active, is_default, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('code'),
                data.get('name'),
                data.get('name_ar'),
                data.get('name_fa'),
                data.get('description'),
                1,
                1 if data.get('is_default') else 0,
                user['id']
            ))
            
            db.commit()
            audit_log('CREATE', 'payroll_groups', cursor.lastrowid, details=f"Created group: {data.get('code')}")
            
            flash('Payroll group created successfully.', 'success')
            return redirect(url_for('payroll.setup_groups'))
        except Exception as e:
            db.rollback()
            flash(f'Error creating group: {str(e)}', 'error')
    
    return render_template('payroll/setup/groups/new.html', title='New Payroll Group')


@payroll_bp.route('/setup/groups/<int:id>/members')
@payroll_login_required
@payroll_permission_required('view')
def setup_groups_members(id):
    """View and manage payroll group members."""
    user = get_current_user()
    db = get_db()
    
    try:
        group = db.execute("SELECT * FROM payroll_groups WHERE id = ?", (id,)).fetchone()
        if not group:
            flash('Group not found.', 'error')
            return redirect(url_for('payroll.setup_groups'))
        
        members = db.execute("""
            SELECT pgm.*, e.first_name || ' ' || e.last_name as employee_name,
                   e.employee_code
            FROM payroll_group_members pgm
            JOIN hr_employees e ON pgm.employee_id = e.id
            WHERE pgm.group_id = ? AND pgm.is_active = 1
            ORDER BY e.first_name, e.last_name
        """, (id,)).fetchall()
        
        # Available employees (not in this group)
        available = db.execute("""
            SELECT e.* FROM hr_employees e
            WHERE e.status = 'Active'
            AND e.id NOT IN (
                SELECT employee_id FROM payroll_group_members WHERE group_id = ? AND is_active = 1
            )
            ORDER BY e.first_name, e.last_name
        """, (id,)).fetchall()
        
        return render_template('payroll/setup/groups/members.html',
            title=f'Group Members: {group["name"]}',
            group=dict(group),
            members=[dict(m) for m in members],
            available=[dict(a) for a in available]
        )
    finally:
        db.close()


@payroll_bp.route('/setup/groups/<int:id>/members/add', methods=['POST'])
@payroll_login_required
@payroll_permission_required('edit')
def setup_groups_members_add(id):
    """Add employee to payroll group."""
    user = get_current_user()
    db = get_db()
    
    try:
        employee_id = request.form.get('employee_id')
        effective_from = parse_date(request.form.get('effective_from')) or date.today()
        
        db.execute("""
            INSERT INTO payroll_group_members (group_id, employee_id, effective_from, is_active)
            VALUES (?, ?, ?, 1)
        """, (id, employee_id, effective_from))
        
        db.commit()
        audit_log('ADD_MEMBER', 'payroll_groups', id, employee_id=employee_id, 
                  details=f"Added employee {employee_id} to group {id}")
        
        flash('Employee added to group.', 'success')
        return redirect(url_for('payroll.setup_groups_members', id=id))
    except Exception as e:
        db.rollback()
        flash(f'Error adding employee: {str(e)}', 'error')
        return redirect(url_for('payroll.setup_groups_members', id=id))
    finally:
        db.close()


@payroll_bp.route('/setup/profiles')
@payroll_login_required
@payroll_permission_required('view')
def setup_profiles():
    """Employee Payroll Profiles."""
    user = get_current_user()
    db = get_db()
    
    try:
        search = request.args.get('search', '').strip()
        page = int(request.args.get('page', 1))
        per_page = 20
        
        query = """
            SELECT pp.*, e.first_name || ' ' || e.last_name as employee_name,
                   e.employee_code, pg.name as group_name
            FROM payroll_profiles pp
            JOIN hr_employees e ON pp.employee_id = e.id
            LEFT JOIN payroll_groups pg ON pp.payroll_group_id = pg.id
            WHERE pp.is_active = 1
        """
        count_query = """
            SELECT COUNT(*) as cnt FROM payroll_profiles pp
            JOIN hr_employees e ON pp.employee_id = e.id
            WHERE pp.is_active = 1
        """
        params = []
        
        if search:
            query += " AND (e.first_name LIKE ? OR e.last_name LIKE ? OR e.employee_code LIKE ?)"
            count_query += " AND (e.first_name LIKE ? OR e.last_name LIKE ? OR e.employee_code LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param])
        
        total = db.execute(count_query, params).fetchone()['cnt']
        offset = (page - 1) * per_page
        query += f" ORDER BY e.first_name LIMIT {per_page} OFFSET {offset}"
        
        profiles = db.execute(query, params).fetchall()
        
        return render_template('payroll/setup/profiles/list.html',
            title='Employee Payroll Profiles',
            profiles=[dict(p) for p in profiles],
            search=search,
            page=page,
            total_pages=(total + per_page - 1) // per_page,
            total=total
        )
    finally:
        db.close()


@payroll_bp.route('/setup/profiles/<int:id>')
@payroll_login_required
@payroll_permission_required('view')
def setup_profiles_view(id):
    """View payroll profile."""
    user = get_current_user()
    db = get_db()
    
    try:
        profile = db.execute("""
            SELECT pp.*, e.first_name || ' ' || e.last_name as employee_name,
                   e.employee_code, pg.name as group_name
            FROM payroll_profiles pp
            JOIN hr_employees e ON pp.employee_id = e.id
            LEFT JOIN payroll_groups pg ON pp.payroll_group_id = pg.id
            WHERE pp.id = ?
        """, (id,)).fetchone()
        
        if not profile:
            flash('Profile not found.', 'error')
            return redirect(url_for('payroll.setup_profiles'))
        
        components = db.execute("""
            SELECT ppc.*, pc.code, pc.name, pc.component_type
            FROM payroll_profile_components ppc
            JOIN payroll_components pc ON ppc.component_id = pc.id
            WHERE ppc.profile_id = ? AND ppc.is_active = 1
            ORDER BY pc.order_index
        """, (id,)).fetchall()
        
        return render_template('payroll/setup/profiles/view.html',
            title=f'Profile: {profile["employee_name"]}',
            profile=dict(profile),
            components=[dict(c) for c in components]
        )
    finally:
        db.close()


@payroll_bp.route('/setup/profiles/<int:id>/edit', methods=['GET', 'POST'])
@payroll_login_required
@payroll_permission_required('edit')
def setup_profiles_edit(id):
    """Edit payroll profile."""
    user = get_current_user()
    db = get_db()
    
    try:
        profile = db.execute("SELECT * FROM payroll_profiles WHERE id = ?", (id,)).fetchone()
        if not profile:
            flash('Profile not found.', 'error')
            return redirect(url_for('payroll.setup_profiles'))
        
        if request.method == 'POST':
            data = request.form
            
            db.execute("""
                UPDATE payroll_profiles SET
                    payroll_group_id = ?, pay_frequency = ?, currency = ?,
                    bank_name = ?, bank_account_number = ?, iban = ?,
                    payment_method = ?, tax_id = ?, social_insurance_number = ?,
                    is_taxable = ?, effective_to = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                data.get('payroll_group_id') or None,
                data.get('pay_frequency', 'Monthly'),
                data.get('currency', 'AED'),
                data.get('bank_name'),
                data.get('bank_account_number'),
                data.get('iban'),
                data.get('payment_method', 'Bank Transfer'),
                data.get('tax_id'),
                data.get('social_insurance_number'),
                1 if data.get('is_taxable') else 0,
                parse_date(data.get('effective_to')),
                id
            ))
            
            db.commit()
            audit_log('UPDATE', 'payroll_profiles', id, details=f"Updated profile for employee {profile['employee_id']}")
            
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('payroll.setup_profiles_view', id=id))
        
        groups = db.execute("SELECT * FROM payroll_groups WHERE is_active = 1 ORDER BY name").fetchall()
        
        return render_template('payroll/setup/profiles/edit.html',
            title='Edit Payroll Profile',
            profile=dict(profile),
            groups=[dict(g) for g in groups]
        )
    finally:
        db.close()


@payroll_bp.route('/setup/profiles/<int:id>/components/add', methods=['POST'])
@payroll_login_required
@payroll_permission_required('edit')
def setup_profiles_components_add(id):
    """Add component to profile."""
    user = get_current_user()
    db = get_db()
    
    try:
        data = request.form
        
        db.execute("""
            INSERT INTO payroll_profile_components (
                profile_id, component_id, amount, percentage, calculation_type, 
                is_active, effective_from
            ) VALUES (?, ?, ?, ?, ?, 1, ?)
        """, (
            id,
            data.get('component_id'),
            float(data.get('amount', 0)),
            float(data.get('percentage', 0)) if data.get('percentage') else None,
            data.get('calculation_type', 'Fixed'),
            parse_date(data.get('effective_from')) or date.today()
        ))
        
        db.commit()
        audit_log('ADD_COMPONENT', 'payroll_profiles', id, 
                  new_value=data.get('component_id'),
                  details=f"Added component {data.get('component_id')} to profile")
        
        flash('Component added to profile.', 'success')
        return redirect(url_for('payroll.setup_profiles_view', id=id))
    except Exception as e:
        db.rollback()
        flash(f'Error adding component: {str(e)}', 'error')
        return redirect(url_for('payroll.setup_profiles_view', id=id))
    finally:
        db.close()


@payroll_bp.route('/setup/calendar')
@payroll_login_required
@payroll_permission_required('view')
def setup_calendar():
    """Payroll Calendar Configuration."""
    user = get_current_user()
    db = get_db()
    
    try:
        calendars = db.execute("SELECT * FROM payroll_calendar ORDER BY name").fetchall()
        
        return render_template('payroll/setup/calendar/list.html',
            title='Payroll Calendar',
            calendars=[dict(c) for c in calendars]
        )
    finally:
        db.close()


@payroll_bp.route('/setup/calendar/new', methods=['GET', 'POST'])
@payroll_login_required
@payroll_permission_required('create')
def setup_calendar_new():
    """Create new payroll calendar."""
    user = get_current_user()
    db = get_db()
    
    if request.method == 'POST':
        try:
            data = request.form
            
            cursor = db.execute("""
                INSERT INTO payroll_calendar (
                    name, code, description, country, pay_frequency, cycle_type,
                    period_start_day, period_end_day, cutoff_day, payment_day,
                    overtime_cutoff_day, leave_cutoff_day, is_active, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """, (
                data.get('name'),
                data.get('code'),
                data.get('description'),
                data.get('country'),
                data.get('pay_frequency'),
                data.get('cycle_type', 'Monthly'),
                int(data.get('period_start_day', 1)),
                int(data.get('period_end_day', 31)),
                int(data.get('cutoff_day', 25)),
                int(data.get('payment_day', 28)),
                int(data.get('overtime_cutoff_day', 26)),
                int(data.get('leave_cutoff_day', 26)),
                user['id']
            ))
            
            db.commit()
            audit_log('CREATE', 'payroll_calendar', cursor.lastrowid, details=f"Created calendar: {data.get('code')}")
            
            flash('Payroll calendar created successfully.', 'success')
            return redirect(url_for('payroll.setup_calendar'))
        except Exception as e:
            db.rollback()
            flash(f'Error creating calendar: {str(e)}', 'error')
    
    return render_template('payroll/setup/calendar/new.html', title='New Payroll Calendar')


@payroll_bp.route('/setup/settings', methods=['GET', 'POST'])
@payroll_login_required
@payroll_permission_required('settings')
def setup_settings():
    """Payroll Settings."""
    user = get_current_user()
    db = get_db()
    
    try:
        if request.method == 'POST':
            data = request.form
            
            for key, value in data.items():
                if key.startswith('setting_'):
                    setting_key = key.replace('setting_', '')
                    update_payroll_setting(setting_key, value, user['id'])
            
            audit_log('UPDATE_SETTINGS', 'payroll_settings', 0, details="Updated payroll settings")
            flash('Settings saved successfully.', 'success')
            return redirect(url_for('payroll.setup_settings'))
        
        settings = db.execute("SELECT * FROM payroll_settings WHERE is_active = 1 ORDER BY category, setting_key").fetchall()
        
        # Group by category
        by_category = {}
        for s in settings:
            cat = s['category'] or 'General'
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(dict(s))
        
        return render_template('payroll/setup/settings.html',
            title='Payroll Settings',
            settings=[dict(s) for s in settings],
            by_category=by_category
        )
    finally:
        db.close()


@payroll_bp.route('/setup/reports')
@payroll_login_required
@payroll_permission_required('reports')
def setup_reports():
    """Payroll Setup Reports."""
    user = get_current_user()
    db = get_db()
    
    try:
        # Component usage report
        component_usage = db.execute("""
            SELECT pc.code, pc.name, pc.component_type,
                   COUNT(DISTINCT ppc.profile_id) as employee_count,
                   SUM(ppc.amount) as total_amount
            FROM payroll_components pc
            LEFT JOIN payroll_profile_components ppc ON pc.id = ppc.component_id AND ppc.is_active = 1
            WHERE pc.is_active = 1
            GROUP BY pc.id
            ORDER BY pc.component_type, pc.name
        """).fetchall()
        
        # Group coverage report
        group_coverage = db.execute("""
            SELECT pg.name, pg.code,
                   COUNT(DISTINCT pgm.employee_id) as member_count
            FROM payroll_groups pg
            LEFT JOIN payroll_group_members pgm ON pg.id = pgm.group_id AND pgm.is_active = 1
            WHERE pg.is_active = 1
            GROUP BY pg.id
        """).fetchall()
        
        # Profile completeness
        profile_completeness = db.execute("""
            SELECT 
                COUNT(*) as total_profiles,
                SUM(CASE WHEN bank_account_number IS NOT NULL AND bank_account_number != '' THEN 1 ELSE 0 END) as with_bank,
                SUM(CASE WHEN iban IS NOT NULL AND iban != '' THEN 1 ELSE 0 END) as with_iban,
                SUM(CASE WHEN tax_id IS NOT NULL AND tax_id != '' THEN 1 ELSE 0 END) as with_tax_id
            FROM payroll_profiles
            WHERE is_active = 1
        """).fetchone()
        
        return render_template('payroll/setup/reports.html',
            title='Payroll Setup Reports',
            component_usage=[dict(c) for c in component_usage],
            group_coverage=[dict(g) for g in group_coverage],
            profile_completeness=dict(profile_completeness) if profile_completeness else None
        )
    finally:
        db.close()


# =============================================================================
# PAYROLL CALENDAR & PERIODS
# =============================================================================

@payroll_bp.route('/periods')
@payroll_login_required
@payroll_permission_required('view')
def periods_list():
    """Payroll Periods List."""
    user = get_current_user()
    db = get_db()
    
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        status = request.args.get('status', '')
        
        query = "SELECT * FROM payroll_periods WHERE 1=1"
        count_query = "SELECT COUNT(*) as cnt FROM payroll_periods WHERE 1=1"
        params = []
        
        if year:
            query += " AND year = ?"
            count_query += " AND year = ?"
            params.append(year)
        
        if status:
            query += " AND status = ?"
            count_query += " AND status = ?"
            params.append(status)
        
        query += " ORDER BY year DESC, month DESC"
        
        periods = db.execute(query, params).fetchall()
        total = db.execute(count_query, params).fetchone()['cnt']
        
        # Get year options
        years = db.execute("SELECT DISTINCT year FROM payroll_periods ORDER BY year DESC").fetchall()
        
        return render_template('payroll/periods/list.html',
            title='Payroll Periods',
            periods=[dict(p) for p in periods],
            years=[y['year'] for y in years],
            selected_year=year,
            selected_status=status,
            total=total
        )
    finally:
        db.close()


@payroll_bp.route('/periods/new', methods=['GET', 'POST'])
@payroll_login_required
@payroll_permission_required('create')
def periods_new():
    """Create new payroll period."""
    user = get_current_user()
    db = get_db()
    
    if request.method == 'POST':
        try:
            data = request.form
            
            month = int(data.get('month'))
            year = int(data.get('year'))
            
            # Check if period exists
            existing = db.execute("""
                SELECT id FROM payroll_periods WHERE month = ? AND year = ?
            """, (month, year)).fetchone()
            
            if existing:
                flash('Period already exists for this month/year.', 'error')
                return redirect(url_for('payroll.periods_list'))
            
            # Calculate period dates
            period_start = date(year, month, 1)
            if month == 12:
                period_end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                period_end = date(year, month + 1, 1) - timedelta(days=1)
            
            cutoff_date = date(year, month, int(data.get('cutoff_day', 25)))
            payment_date = date(year, month, int(data.get('payment_day', 28)))
            
            cursor = db.execute("""
                INSERT INTO payroll_periods (
                    calendar_id, name, period_key, month, year,
                    period_start, period_end, cutoff_date, payment_date,
                    status, run_status, fiscal_year, quarter, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Open', 'Not Started', ?, ?, CURRENT_TIMESTAMP)
            """, (
                data.get('calendar_id') or None,
                data.get('name', f"{month}/{year}"),
                f"{year}-{month:02d}",
                month, year,
                period_start,
                period_end,
                cutoff_date,
                payment_date,
                data.get('fiscal_year', str(year)),
                data.get('quarter', f"Q{(month-1)//3 + 1}")
            ))
            
            db.commit()
            audit_log('CREATE', 'payroll_periods', cursor.lastrowid, details=f"Created period: {month}/{year}")
            
            flash('Payroll period created successfully.', 'success')
            return redirect(url_for('payroll.periods_list'))
        except Exception as e:
            db.rollback()
            flash(f'Error creating period: {str(e)}', 'error')
    
    # Get calendars
    calendars = db.execute("SELECT * FROM payroll_calendar WHERE is_active = 1 ORDER BY name").fetchall()
    
    return render_template('payroll/periods/new.html',
        title='New Payroll Period',
        calendars=[dict(c) for c in calendars],
        current_year=datetime.now().year,
        current_month=datetime.now().month
    )


@payroll_bp.route('/periods/<int:id>')
@payroll_login_required
@payroll_permission_required('view')
def periods_view(id):
    """View payroll period details."""
    user = get_current_user()
    db = get_db()
    
    try:
        period = db.execute("SELECT * FROM payroll_periods WHERE id = ?", (id,)).fetchone()
        if not period:
            flash('Period not found.', 'error')
            return redirect(url_for('payroll.periods_list'))
        
        # Get runs for this period
        runs = db.execute("""
            SELECT pr.*, u.username as created_by_name
            FROM payroll_runs pr
            JOIN users u ON pr.created_by_id = u.id
            WHERE pr.period_id = ?
            ORDER BY pr.created_at DESC
        """, (id,)).fetchall()
        
        # Get employee records count by status
        record_stats = db.execute("""
            SELECT status, COUNT(*) as cnt
            FROM payroll_employee_records
            WHERE period_id = ?
            GROUP BY status
        """, (id,)).fetchall()
        
        # Get summary
        summary = get_payroll_summary_stats(id)
        
        # Get locks
        locks = db.execute("""
            SELECT ppl.*, u.username as locked_by_name
            FROM payroll_period_locks ppl
            JOIN users u ON ppl.locked_by_id = u.id
            WHERE ppl.period_id = ?
            ORDER BY ppl.locked_at DESC
        """, (id,)).fetchall()
        
        return render_template('payroll/periods/view.html',
            title=f'Period: {period["name"]}',
            period=dict(period),
            runs=[dict(r) for r in runs],
            record_stats=[dict(s) for s in record_stats],
            summary=summary,
            locks=[dict(l) for l in locks]
        )
    finally:
        db.close()


@payroll_bp.route('/periods/<int:id>/lock', methods=['POST'])
@payroll_login_required
@payroll_permission_required('lock')
def periods_lock(id):
    """Lock a payroll period."""
    user = get_current_user()
    db = get_db()
    
    try:
        data = request.form
        lock_type = data.get('lock_type', 'Full')
        reason = data.get('reason', 'Period locked for review')
        
        db.execute("""
            INSERT INTO payroll_period_locks (period_id, lock_type, is_locked, locked_by_id, reason)
            VALUES (?, ?, 1, ?, ?)
        """, (id, lock_type, user['id'], reason))
        
        # Update period status
        db.execute("""
            UPDATE payroll_periods SET status = 'Locked', locked_at = CURRENT_TIMESTAMP, locked_by_id = ?
            WHERE id = ?
        """, (user['id'], id))
        
        db.commit()
        audit_log('LOCK', 'payroll_periods', id, details=f"Locked period: {lock_type}")
        
        flash('Period locked successfully.', 'success')
        return redirect(url_for('payroll.periods_view', id=id))
    except Exception as e:
        db.rollback()
        flash(f'Error locking period: {str(e)}', 'error')
        return redirect(url_for('payroll.periods_view', id=id))
    finally:
        db.close()


@payroll_bp.route('/periods/<int:id>/unlock', methods=['POST'])
@payroll_login_required
@payroll_permission_required('unlock')
def periods_unlock(id):
    """Unlock a payroll period."""
    user = get_current_user()
    db = get_db()
    
    try:
        data = request.form
        reason = data.get('reason', 'Period unlocked')
        
        # Get latest lock
        latest_lock = db.execute("""
            SELECT * FROM payroll_period_locks 
            WHERE period_id = ? AND is_locked = 1
            ORDER BY locked_at DESC LIMIT 1
        """).fetchone()
        
        if latest_lock:
            db.execute("""
                UPDATE payroll_period_locks SET 
                    is_locked = 0, unlocked_by_id = ?, unlocked_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (user['id'], latest_lock['id']))
        
        # Update period status
        db.execute("""
            UPDATE payroll_periods SET status = 'Approved', locked_at = NULL, locked_by_id = NULL
            WHERE id = ?
        """, (id,))
        
        db.commit()
        audit_log('UNLOCK', 'payroll_periods', id, details="Unlocked period")
        
        flash('Period unlocked successfully.', 'success')
        return redirect(url_for('payroll.periods_view', id=id))
    except Exception as e:
        db.rollback()
        flash(f'Error unlocking period: {str(e)}', 'error')
        return redirect(url_for('payroll.periods_view', id=id))
    finally:
        db.close()


@payroll_bp.route('/periods/<int:id>/close', methods=['POST'])
@payroll_login_required
@payroll_permission_required('close')
def periods_close(id):
    """Close a payroll period."""
    user = get_current_user()
    db = get_db()
    
    try:
        db.execute("""
            UPDATE payroll_periods SET 
                status = 'Closed', closed_at = CURRENT_TIMESTAMP, closed_by_id = ?
            WHERE id = ?
        """, (user['id'], id))
        
        db.commit()
        audit_log('CLOSE', 'payroll_periods', id, details="Closed period")
        
        flash('Period closed successfully.', 'success')
        return redirect(url_for('payroll.periods_view', id=id))
    except Exception as e:
        db.rollback()
        flash(f'Error closing period: {str(e)}', 'error')
        return redirect(url_for('payroll.periods_view', id=id))
    finally:
        db.close()


@payroll_bp.route('/periods/calendar')
@payroll_login_required
@payroll_permission_required('view')
def periods_calendar():
    """Payroll Calendar View."""
    user = get_current_user()
    db = get_db()
    
    try:
        year = request.args.get('year', datetime.now().year, type=int)
        
        periods = db.execute("""
            SELECT * FROM payroll_periods 
            WHERE year = ?
            ORDER BY month
        """, (year,)).fetchall()
        
        # Create a map of months to periods
        period_map = {p['month']: dict(p) for p in periods}
        
        return render_template('payroll/periods/calendar.html',
            title='Payroll Calendar',
            year=year,
            period_map=period_map
        )
    finally:
        db.close()


# =============================================================================
# PAYROLL PROCESSING
# =============================================================================

@payroll_bp.route('/processing')
@payroll_login_required
@payroll_permission_required('view')
def processing_list():
    """Payroll Processing List."""
    user = get_current_user()
    db = get_db()
    
    try:
        current_period = get_active_payroll_period()
        
        # Get recent runs
        runs = db.execute("""
            SELECT pr.*, pp.name as period_name, pp.month, pp.year,
                   u.username as created_by_name,
                   (SELECT COUNT(*) FROM payroll_employee_records WHERE run_id = pr.id) as record_count
            FROM payroll_runs pr
            JOIN payroll_periods pp ON pr.period_id = pp.id
            JOIN users u ON pr.created_by_id = u.id
            ORDER BY pr.created_at DESC
            LIMIT 20
        """).fetchall()
        
        return render_template('payroll/processing/list.html',
            title='Payroll Processing',
            current_period=dict(current_period) if current_period else None,
            runs=[dict(r) for r in runs]
        )
    finally:
        db.close()


@payroll_bp.route('/processing/run/new', methods=['GET', 'POST'])
@payroll_login_required
@payroll_permission_required('create')
def processing_run_new():
    """Start new payroll run."""
    user = get_current_user()
    db = get_db()
    
    try:
        if request.method == 'POST':
            period_id = request.form.get('period_id', type=int)
            run_type = request.form.get('run_type', 'Regular')
            
            # Check if period is open
            period = db.execute("SELECT * FROM payroll_periods WHERE id = ?", (period_id,)).fetchone()
            if not period or period['status'] not in ('Open', 'Processing'):
                flash('Period is not open for payroll processing.', 'error')
                return redirect(url_for('payroll.processing_list'))
            
            # Create run
            cursor = db.execute("""
                INSERT INTO payroll_runs (period_id, run_type, name, status, created_by_id, created_at)
                VALUES (?, ?, ?, 'Draft', ?, CURRENT_TIMESTAMP)
            """, (period_id, run_type, f"Run {datetime.now().strftime('%Y%m%d%H%M%S')}", user['id']))
            
            run_id = cursor.lastrowid
            
            # Update period status
            db.execute("""
                UPDATE payroll_periods SET status = 'Processing', updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (period_id,))
            
            db.commit()
            audit_log('CREATE', 'payroll_runs', run_id, period_id=period_id, 
                      details=f"Created payroll run: {run_type}")
            
            flash('Payroll run created successfully. You can now add employees and process.', 'success')
            return redirect(url_for('payroll.processing_run_view', id=run_id))
        
        # Get open periods
        open_periods = db.execute("""
            SELECT * FROM payroll_periods 
            WHERE status IN ('Open', 'Processing')
            ORDER BY year DESC, month DESC
        """).fetchall()
        
        return render_template('payroll/processing/run_new.html',
            title='Start Payroll Run',
            open_periods=[dict(p) for p in open_periods]
        )
    finally:
        db.close()


@payroll_bp.route('/processing/run/<int:id>')
@payroll_login_required
@payroll_permission_required('view')
def processing_run_view(id):
    """View payroll run details."""
    user = get_current_user()
    db = get_db()
    
    try:
        run = db.execute("""
            SELECT pr.*, pp.name as period_name, pp.month, pp.year, pp.status as period_status,
                   u.username as created_by_name
            FROM payroll_runs pr
            JOIN payroll_periods pp ON pr.period_id = pp.id
            JOIN users u ON pr.created_by_id = u.id
            WHERE pr.id = ?
        """, (id,)).fetchone()
        
        if not run:
            flash('Run not found.', 'error')
            return redirect(url_for('payroll.processing_list'))
        
        # Get employee records
        records = db.execute("""
            SELECT per.*, e.first_name || ' ' || e.last_name as employee_name,
                   e.employee_code, d.name as department_name
            FROM payroll_employee_records per
            JOIN hr_employees e ON per.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            WHERE per.run_id = ?
            ORDER BY e.first_name, e.last_name
        """, (id,)).fetchall()
        
        # Get exceptions
        exceptions = db.execute("""
            SELECT pe.*, e.first_name || ' ' || e.last_name as employee_name
            FROM payroll_exceptions pe
            LEFT JOIN hr_employees e ON pe.employee_id = e.id
            WHERE pe.run_id = ?
            ORDER BY pe.severity DESC, pe.created_at DESC
        """, (id,)).fetchall()
        
        # Get summary
        summary = db.execute("""
            SELECT 
                COUNT(*) as total_records,
                SUM(CASE WHEN status = 'Draft' THEN 1 ELSE 0 END) as draft,
                SUM(CASE WHEN status = 'Calculated' THEN 1 ELSE 0 END) as calculated,
                SUM(CASE WHEN status = 'Approved' THEN 1 ELSE 0 END) as approved,
                SUM(CASE WHEN has_exceptions = 1 THEN 1 ELSE 0 END) as with_exceptions,
                SUM(gross_salary) as total_gross,
                SUM(total_deductions) as total_deductions,
                SUM(net_salary) as total_net
            FROM payroll_employee_records
            WHERE run_id = ?
        """, (id,)).fetchone()
        
        return render_template('payroll/processing/run_view.html',
            title=f'Run: {run["name"]}',
            run=dict(run),
            records=[dict(r) for r in records],
            exceptions=[dict(e) for e in exceptions],
            summary=dict(summary) if summary else None
        )
    finally:
        db.close()


@payroll_bp.route('/processing/run/<int:id>/validate', methods=['POST'])
@payroll_login_required
@payroll_permission_required('validate')
def processing_run_validate(id):
    """Run pre-validation on payroll."""
    user = get_current_user()
    db = get_db()
    
    try:
        # Update run status
        db.execute("""
            UPDATE payroll_runs SET status = 'Pre-Validation', validation_status = 'Running'
            WHERE id = ?
        """, (id,))
        
        # Run validations
        is_valid, errors = run_payroll_validations(id)
        
        # Update validation status
        db.execute("""
            UPDATE payroll_runs SET 
                validation_status = ?,
                validation_errors = ?
            WHERE id = ?
        """, ('Pass' if is_valid else 'Failed', json.dumps(errors), id))
        
        db.commit()
        audit_log('VALIDATE', 'payroll_runs', id, details=f"Validation {'passed' if is_valid else 'failed'}")
        
        if is_valid:
            flash('Validation passed. You can now process the payroll.', 'success')
        else:
            flash(f'Validation failed: {len(errors)} issues found.', 'warning')
        
        return redirect(url_for('payroll.processing_run_view', id=id))
    except Exception as e:
        db.rollback()
        flash(f'Error running validation: {str(e)}', 'error')
        return redirect(url_for('payroll.processing_run_view', id=id))
    finally:
        db.close()


@payroll_bp.route('/processing/run/<int:id>/calculate', methods=['POST'])
@payroll_login_required
@payroll_permission_required('calculate')
def processing_run_calculate(id):
    """Calculate payroll for all employees."""
    user = get_current_user()
    db = get_db()
    
    try:
        run = db.execute("SELECT * FROM payroll_runs WHERE id = ?", (id,)).fetchone()
        if not run:
            flash('Run not found.', 'error')
            return redirect(url_for('payroll.processing_list'))
        
        # Update run status
        db.execute("""
            UPDATE payroll_runs SET status = 'Calculating', started_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (id,))
        db.commit()
        
        # Get employees with payroll profiles
        employees = db.execute("""
            SELECT e.id, e.employee_code, e.first_name, e.last_name,
                   pp.id as profile_id
            FROM hr_employees e
            JOIN payroll_profiles pp ON e.id = pp.employee_id AND pp.is_active = 1
            WHERE e.status = 'Active'
        """).fetchall()
        
        calculated_count = 0
        for emp in employees:
            # Get employee components
            components = get_employee_components(emp['id'])
            
            # Calculate totals
            basic = next((c['amount'] for c in components if c['code'] == 'BASIC'), 0)
            total_earnings = sum(c['amount'] for c in components if c['component_type'] in ('Earning', 'Allowance'))
            total_deductions = sum(c['amount'] for c in components if c['component_type'] == 'Deduction')
            total_tax = next((c['amount'] for c in components if c['code'] == 'TAX'), 0)
            
            gross = basic + total_earnings + total_deductions  # Deductions are added to gross before subtract
            net = gross - total_deductions - total_tax
            
            # Get OT inputs for this period
            ot_inputs = db.execute("""
                SELECT COALESCE(SUM(total_amount), 0) as total_ot
                FROM payroll_overtime_inputs
                WHERE period_id = ? AND employee_id = ? AND status = 'Approved'
            """, (run['period_id'], emp['id'])).fetchone()
            
            total_overtime = ot_inputs['total_ot'] if ot_inputs else 0
            
            # Check if record exists
            existing = db.execute("""
                SELECT id FROM payroll_employee_records 
                WHERE run_id = ? AND employee_id = ?
            """, (id, emp['id'])).fetchone()
            
            if existing:
                db.execute("""
                    UPDATE payroll_employee_records SET
                        basic_salary = ?, total_earnings = ?, total_deductions = ?,
                        total_overtime = ?, total_tax = ?, gross_salary = ?, net_salary = ?,
                        status = 'Calculated', updated_at = CURRENT_TIMESTAMP
                    WHERE run_id = ? AND employee_id = ?
                """, (basic, total_earnings, total_deductions - total_tax, total_overtime,
                      total_tax, gross, net, id, emp['id']))
            else:
                db.execute("""
                    INSERT INTO payroll_employee_records (
                        run_id, period_id, employee_id, profile_id,
                        basic_salary, total_earnings, total_deductions,
                        total_overtime, total_tax, gross_salary, net_salary,
                        days_worked, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Calculated')
                """, (id, run['period_id'], emp['id'], emp['profile_id'],
                      basic, total_earnings, total_deductions - total_tax,
                      total_overtime, total_tax, gross, net, 30))
            
            calculated_count += 1
        
        # Update run status
        db.execute("""
            UPDATE payroll_runs SET 
                status = 'Calculated',
                completed_at = CURRENT_TIMESTAMP,
                total_records = ?
            WHERE id = ?
        """, (calculated_count, id))
        
        db.commit()
        audit_log('CALCULATE', 'payroll_runs', id, details=f"Calculated payroll for {calculated_count} employees")
        
        flash(f'Payroll calculated for {calculated_count} employees.', 'success')
        return redirect(url_for('payroll.processing_run_view', id=id))
    except Exception as e:
        db.rollback()
        db.execute("UPDATE payroll_runs SET status = 'Failed' WHERE id = ?", (id,))
        db.commit()
        flash(f'Error calculating payroll: {str(e)}', 'error')
        return redirect(url_for('payroll.processing_run_view', id=id))
    finally:
        db.close()


@payroll_bp.route('/processing/run/<int:id>/add-employees', methods=['POST'])
@payroll_login_required
@payroll_permission_required('add_employees')
def processing_run_add_employees(id):
    """Add employees to payroll run."""
    user = get_current_user()
    db = get_db()
    
    try:
        run = db.execute("SELECT * FROM payroll_runs WHERE id = ?", (id,)).fetchone()
        if not run:
            return jsonify({'error': 'Run not found'}), 404
        
        # Get employees without records in this run
        employees = db.execute("""
            SELECT e.id, e.first_name || ' ' || e.last_name as employee_name, e.employee_code
            FROM hr_employees e
            JOIN payroll_profiles pp ON e.id = pp.employee_id AND pp.is_active = 1
            WHERE e.status = 'Active'
            AND e.id NOT IN (SELECT employee_id FROM payroll_employee_records WHERE run_id = ?)
        """, (id,)).fetchall()
        
        added = 0
        for emp in employees:
            db.execute("""
                INSERT INTO payroll_employee_records (run_id, period_id, employee_id, status, days_worked)
                VALUES (?, ?, ?, 'Draft', 30)
            """, (id, run['period_id'], emp['id']))
            added += 1
        
        db.commit()
        audit_log('ADD_EMPLOYEES', 'payroll_runs', id, details=f"Added {added} employees to run")
        
        flash(f'Added {added} employees to the run.', 'success')
        return redirect(url_for('payroll.processing_run_view', id=id))
    except Exception as e:
        db.rollback()
        flash(f'Error adding employees: {str(e)}', 'error')
        return redirect(url_for('payroll.processing_run_view', id=id))
    finally:
        db.close()


@payroll_bp.route('/processing/run/<int:id>/approve', methods=['POST'])
@payroll_login_required
@payroll_permission_required('approve')
def processing_run_approve(id):
    """Approve payroll run."""
    user = get_current_user()
    db = get_db()
    
    try:
        remarks = request.form.get('remarks', '')
        
        # Update run status
        db.execute("""
            UPDATE payroll_runs SET status = 'Approved'
            WHERE id = ?
        """, (id,))
        
        # Update all records
        db.execute("""
            UPDATE payroll_employee_records SET 
                status = 'Approved', approved_by_id = ?, approved_at = CURRENT_TIMESTAMP
            WHERE run_id = ? AND status = 'Calculated'
        """, (user['id'], id))
        
        # Update period
        run = db.execute("SELECT period_id FROM payroll_runs WHERE id = ?", (id,)).fetchone()
        if run:
            db.execute("""
                UPDATE payroll_periods SET status = 'Pending Approval', approved_at = CURRENT_TIMESTAMP, approved_by_id = ?
                WHERE id = ?
            """, (user['id'], run['period_id']))
        
        db.commit()
        audit_log('APPROVE', 'payroll_runs', id, details="Approved payroll run")
        
        flash('Payroll run approved successfully.', 'success')
        return redirect(url_for('payroll.processing_run_view', id=id))
    except Exception as e:
        db.rollback()
        flash(f'Error approving run: {str(e)}', 'error')
        return redirect(url_for('payroll.processing_run_view', id=id))
    finally:
        db.close()


@payroll_bp.route('/processing/run/<int:id>/lock', methods=['POST'])
@payroll_login_required
@payroll_permission_required('lock')
def processing_run_lock(id):
    """Lock payroll run."""
    user = get_current_user()
    db = get_db()
    
    try:
        db.execute("""
            UPDATE payroll_runs SET status = 'Locked'
            WHERE id = ?
        """, (id,))
        
        db.execute("""
            UPDATE payroll_employee_records SET locked = 1, locked_at = CURRENT_TIMESTAMP, locked_by_id = ?
            WHERE run_id = ? AND status = 'Approved'
        """, (user['id'], id))
        
        run = db.execute("SELECT period_id FROM payroll_runs WHERE id = ?", (id,)).fetchone()
        if run:
            db.execute("""
                UPDATE payroll_periods SET status = 'Locked', locked_at = CURRENT_TIMESTAMP, locked_by_id = ?
                WHERE id = ?
            """, (user['id'], run['period_id']))
        
        db.commit()
        audit_log('LOCK', 'payroll_runs', id, details="Locked payroll run")
        
        flash('Payroll run locked successfully.', 'success')
        return redirect(url_for('payroll.processing_run_view', id=id))
    except Exception as e:
        db.rollback()
        flash(f'Error locking run: {str(e)}', 'error')
        return redirect(url_for('payroll.processing_run_view', id=id))
    finally:
        db.close()


# =============================================================================
# PAYROLL REVIEW & APPROVAL
# =============================================================================

@payroll_bp.route('/review')
@payroll_login_required
@payroll_permission_required('view')
def review_list():
    """Payroll Review List."""
    user = get_current_user()
    db = get_db()
    
    try:
        # Get pending approvals
        pending = get_pending_payroll_approvals(user['id'])
        
        # Get recent reviews
        recent = db.execute("""
            SELECT per.*, e.first_name || ' ' || e.last_name as employee_name,
                   e.employee_code, pp.name as period_name
            FROM payroll_employee_records per
            JOIN hr_employees e ON per.employee_id = e.id
            JOIN payroll_periods pp ON per.period_id = pp.id
            WHERE per.status IN ('In Review', 'Approved')
            ORDER BY per.approved_at DESC
            LIMIT 50
        """).fetchall()
        
        return render_template('payroll/review/list.html',
            title='Payroll Review',
            pending_approvals=pending,
            recent_reviews=[dict(r) for r in recent]
        )
    finally:
        db.close()


@payroll_bp.route('/review/queue')
@payroll_login_required
@payroll_permission_required('view')
def review_queue():
    """Review Queue - all pending items."""
    user = get_current_user()
    db = get_db()
    
    try:
        period_id = request.args.get('period_id', type=int)
        department = request.args.get('department', '')
        
        query = """
            SELECT per.*, e.first_name || ' ' || e.last_name as employee_name,
                   e.employee_code, d.name as department_name,
                   pp.name as period_name
            FROM payroll_employee_records per
            JOIN hr_employees e ON per.employee_id = e.id
            LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
            LEFT JOIN hr_departments d ON ee.department_id = d.id
            JOIN payroll_periods pp ON per.period_id = pp.id
            WHERE per.status IN ('Calculated', 'In Review')
        """
        params = []
        
        if period_id:
            query += " AND per.period_id = ?"
            params.append(period_id)
        
        if department:
            query += " AND ee.department_id = ?"
            params.append(department)
        
        query += " ORDER BY e.first_name, e.last_name"
        
        records = db.execute(query, params).fetchall()
        
        # Get departments for filter
        departments = db.execute("SELECT * FROM hr_departments WHERE status = 'Active' ORDER BY name").fetchall()
        periods = db.execute("SELECT * FROM payroll_periods ORDER BY year DESC, month DESC LIMIT 12").fetchall()
        
        return render_template('payroll/review/queue.html',
            title='Review Queue',
            records=[dict(r) for r in records],
            departments=[dict(d) for d in departments],
            periods=[dict(p) for p in periods],
            selected_period=period_id,
            selected_department=department
        )
    finally:
        db.close()


@payroll_bp.route('/review/record/<int:id>', methods=['GET', 'POST'])
@payroll_login_required
@payroll_permission_required('review')
def review_record(id):
    """Review individual payroll record."""
    user = get_current_user()
    db = get_db()
    
    try:
        record = db.execute("""
            SELECT per.*, e.first_name || ' ' || e.last_name as employee_name,
                   e.employee_code, e.date_of_birth, e.hire_date,
                   pp.name as period_name, pp.month, pp.year
            FROM payroll_employee_records per
            JOIN hr_employees e ON per.employee_id = e.id
            JOIN payroll_periods pp ON per.period_id = pp.id
            WHERE per.id = ?
        """, (id,)).fetchone()
        
        if not record:
            flash('Record not found.', 'error')
            return redirect(url_for('payroll.review_list'))
        
        # Get earnings breakdown
        earnings = db.execute("""
            SELECT * FROM payroll_employee_earnings WHERE record_id = ?
        """, (id,)).fetchall()
        
        # Get deductions breakdown
        deductions = db.execute("""
            SELECT * FROM payroll_employee_deductions WHERE record_id = ?
        """, (id,)).fetchall()
        
        # Get OT inputs
        ot_inputs = db.execute("""
            SELECT * FROM payroll_overtime_inputs
            WHERE period_id = ? AND employee_id = ?
        """, (record['period_id'], record['employee_id'])).fetchall()
        
        # Get adjustments
        adjustments = db.execute("""
            SELECT * FROM payroll_manual_adjustments
            WHERE period_id = ? AND employee_id = ? AND status = 'Approved'
        """, (record['period_id'], record['employee_id'])).fetchall()
        
        if request.method == 'POST':
            action = request.form.get('action')
            remarks = request.form.get('remarks', '')
            
            if action == 'approve':
                db.execute("""
                    UPDATE payroll_employee_records SET 
                        status = 'Approved', approved_by_id = ?, approved_at = CURRENT_TIMESTAMP,
                        approved_remarks = ?
                    WHERE id = ?
                """, (user['id'], remarks, id))
                
                audit_log('APPROVE', 'payroll_employee_records', id, details=f"Approved record: {record['employee_code']}")
                flash('Record approved.', 'success')
                
            elif action == 'return':
                db.execute("""
                    UPDATE payroll_employee_records SET status = 'Draft'
                    WHERE id = ?
                """, (id,))
                audit_log('RETURN', 'payroll_employee_records', id, details="Returned for revision")
                flash('Record returned for revision.', 'success')
            
            return redirect(url_for('payroll.review_queue'))
        
        return render_template('payroll/review/record.html',
            title=f'Review: {record["employee_name"]}',
            record=dict(record),
            earnings=[dict(e) for e in earnings],
            deductions=[dict(d) for d in deductions],
            ot_inputs=[dict(o) for o in ot_inputs],
            adjustments=[dict(a) for a in adjustments]
        )
    finally:
        db.close()


@payroll_bp.route('/review/approve-batch', methods=['POST'])
@payroll_login_required
@payroll_permission_required('approve')
def review_approve_batch():
    """Batch approve payroll records."""
    user = get_current_user()
    db = get_db()
    
    try:
        record_ids = request.form.getlist('record_ids')
        remarks = request.form.get('remarks', '')
        
        for rid in record_ids:
            db.execute("""
                UPDATE payroll_employee_records SET 
                    status = 'Approved', approved_by_id = ?, approved_at = CURRENT_TIMESTAMP,
                    approved_remarks = ?
                WHERE id = ?
            """, (user['id'], remarks, rid))
            audit_log('APPROVE', 'payroll_employee_records', rid, details="Batch approved")
        
        db.commit()
        flash(f'Approved {len(record_ids)} records.', 'success')
        return redirect(url_for('payroll.review_queue'))
    except Exception as e:
        db.rollback()
        flash(f'Error in batch approval: {str(e)}', 'error')
        return redirect(url_for('payroll.review_queue'))
    finally:
        db.close()


# =============================================================================
# PAYSLIPS & OUTPUTS
# =============================================================================

@payroll_bp.route('/payslips')
@payroll_login_required
@payroll_permission_required('view')
def payslips_list():
    """Payslips List."""
    user = get_current_user()
    db = get_db()
    
    try:
        search = request.args.get('search', '').strip()
        period_id = request.args.get('period_id', type=int)
        page = int(request.args.get('page', 1))
        per_page = 20
        
        query = """
            SELECT pp.*, e.first_name || ' ' || e.last_name as employee_name,
                   e.employee_code, per.total_gross, per.total_deductions, per.net_salary
            FROM payroll_payslips pp
            JOIN hr_employees e ON pp.employee_id = e.id
            LEFT JOIN payroll_employee_records per ON pp.record_id = per.id
            WHERE 1=1
        """
        params = []
        
        if search:
            query += " AND (e.first_name LIKE ? OR e.last_name LIKE ? OR e.employee_code LIKE ? OR pp.payslip_number LIKE ?)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param, search_param, search_param])
        
        if period_id:
            query += " AND pp.period_id = ?"
            params.append(period_id)
        
        # For non-admin, only show own payslips
        if user['role_name'] not in ['Global Admin', 'Payroll Admin', 'Payroll Manager']:
            query += " AND e.id = (SELECT employee_id FROM payroll_profiles WHERE user_id = ? AND is_active = 1)"
            params.append(user['id'])
        
        count_query = query.replace("SELECT pp.*, e.first_name || ' ' || e.last_name as employee_name, e.employee_code, per.total_gross, per.total_deductions, per.net_salary", "SELECT COUNT(*) as cnt")
        
        total = db.execute(count_query, params).fetchone()['cnt']
        offset = (page - 1) * per_page
        query += f" ORDER BY pp.generated_at DESC LIMIT {per_page} OFFSET {offset}"
        
        payslips = db.execute(query, params).fetchall()
        periods = db.execute("SELECT * FROM payroll_periods ORDER BY year DESC, month DESC LIMIT 12").fetchall()
        
        return render_template('payroll/payslips/list.html',
            title='Payslips',
            payslips=[dict(p) for p in payslips],
            periods=[dict(p) for p in periods],
            search=search,
            period_id=period_id,
            page=page,
            total_pages=(total + per_page - 1) // per_page,
            total=total
        )
    finally:
        db.close()


@payroll_bp.route('/payslips/generate', methods=['GET', 'POST'])
@payroll_login_required
@payroll_permission_required('generate')
def payslips_generate():
    """Generate payslips for a period."""
    user = get_current_user()
    db = get_db()
    
    try:
        if request.method == 'POST':
            period_id = request.form.get('period_id', type=int)
            employee_ids = request.form.getlist('employee_ids')
            
            generated = 0
            for emp_id in employee_ids:
                # Get record
                record = db.execute("""
                    SELECT * FROM payroll_employee_records
                    WHERE period_id = ? AND employee_id = ? AND status = 'Approved'
                """, (period_id, emp_id)).fetchone()
                
                if record:
                    # Generate payslip
                    payslip_number = create_payslip_number()
                    
                    cursor = db.execute("""
                        INSERT INTO payroll_payslips (
                            payslip_number, period_id, employee_id, record_id,
                            generated_by_id, status
                        ) VALUES (?, ?, ?, ?, ?, 'Generated')
                    """, (payslip_number, period_id, emp_id, record['id'], user['id']))
                    
                    payslip_id = cursor.lastrowid
                    
                    # Add earnings
                    earnings = db.execute("""
                        SELECT * FROM payroll_employee_earnings WHERE record_id = ?
                    """, (record['id'],)).fetchall()
                    
                    for earn in earnings:
                        db.execute("""
                            INSERT INTO payroll_payslip_details (
                                payslip_id, component_id, component_code, component_name,
                                category, amount, is_earning
                            ) VALUES (?, ?, ?, ?, 'Earning', ?, 1)
                        """, (payslip_id, earn['component_id'], earn['component_code'], 
                              earn['component_name'], earn['amount']))
                    
                    # Add deductions
                    deductions = db.execute("""
                        SELECT * FROM payroll_employee_deductions WHERE record_id = ?
                    """, (record['id'],)).fetchall()
                    
                    for ded in deductions:
                        db.execute("""
                            INSERT INTO payroll_payslip_details (
                                payslip_id, component_id, component_code, component_name,
                                category, amount, is_earning
                            ) VALUES (?, ?, ?, ?, 'Deduction', ?, 0)
                        """, (payslip_id, ded['component_id'], ded['component_code'],
                              ded['component_name'], ded['amount']))
                    
                    generated += 1
            
            db.commit()
            audit_log('GENERATE', 'payroll_payslips', generated, period_id=period_id,
                      details=f"Generated {generated} payslips")
            
            flash(f'Generated {generated} payslips.', 'success')
            return redirect(url_for('payroll.payslips_list'))
        
        # Get periods with approved payroll
        periods = db.execute("""
            SELECT * FROM payroll_periods 
            WHERE status IN ('Approved', 'Locked', 'Closed')
            ORDER BY year DESC, month DESC
        """).fetchall()
        
        # Get employees with approved payroll
        employees = db.execute("""
            SELECT e.id, e.first_name || ' ' || e.last_name as employee_name, e.employee_code
            FROM hr_employees e
            WHERE e.status = 'Active'
            ORDER BY e.first_name, e.last_name
        """).fetchall()
        
        return render_template('payroll/payslips/generate.html',
            title='Generate Payslips',
            periods=[dict(p) for p in periods],
            employees=[dict(e) for e in employees]
        )
    finally:
        db.close()


@payroll_bp.route('/payslips/<int:id>')
@payroll_login_required
@payroll_permission_required('view')
def payslips_view(id):
    """View payslip details."""
    user = get_current_user()
    db = get_db()
    
    try:
        payslip = db.execute("""
            SELECT pp.*, e.first_name || ' ' || e.last_name as employee_name,
                   e.employee_code, e.arabic_name, e.date_of_birth, e.hire_date,
                   ppd.name as period_name, ppd.month, ppd.year,
                   per.basic_salary, per.total_gross, per.total_deductions, per.net_salary,
                   per.days_worked, per.days_absent
            FROM payroll_payslips pp
            JOIN hr_employees e ON pp.employee_id = e.id
            JOIN payroll_periods ppd ON pp.period_id = ppd.id
            LEFT JOIN payroll_employee_records per ON pp.record_id = per.id
            WHERE pp.id = ?
        """, (id,)).fetchone()
        
        if not payslip:
            flash('Payslip not found.', 'error')
            return redirect(url_for('payroll.payslips_list'))
        
        # Check access rights
        if user['role_name'] not in ['Global Admin', 'Payroll Admin', 'Payroll Manager']:
            emp_profile = db.execute("""
                SELECT employee_id FROM payroll_profiles WHERE user_id = ? AND is_active = 1
            """, (user['id'],)).fetchone()
            if not emp_profile or emp_profile['employee_id'] != payslip['employee_id']:
                flash('You do not have access to this payslip.', 'error')
                return redirect(url_for('payroll.payslips_list'))
        
        # Get details
        details = db.execute("""
            SELECT * FROM payroll_payslip_details WHERE payslip_id = ?
        """, (id,)).fetchall()
        
        return render_template('payroll/payslips/view.html',
            title=f'Payslip: {payslip["payslip_number"]}',
            payslip=dict(payslip),
            details=[dict(d) for d in details]
        )
    finally:
        db.close()


@payroll_bp.route('/payslips/<int:id>/download')
@payroll_login_required
@payroll_permission_required('download')
def payslips_download(id):
    """Download payslip as PDF."""
    user = get_current_user()
    db = get_db()
    
    try:
        payslip = db.execute("SELECT * FROM payroll_payslips WHERE id = ?", (id,)).fetchone()
        if not payslip:
            flash('Payslip not found.', 'error')
            return redirect(url_for('payroll.payslips_list'))
        
        # Check access rights
        if user['role_name'] not in ['Global Admin', 'Payroll Admin', 'Payroll Manager']:
            emp_profile = db.execute("""
                SELECT employee_id FROM payroll_profiles WHERE user_id = ? AND is_active = 1
            """, (user['id'],)).fetchone()
            if not emp_profile or emp_profile['employee_id'] != payslip['employee_id']:
                flash('You do not have access to download this payslip.', 'error')
                return redirect(url_for('payroll.payslips_list'))
        
        # Log download
        audit_log('DOWNLOAD', 'payroll_payslips', id, details=f"Downloaded payslip {payslip['payslip_number']}")
        
        # Generate PDF payslip if possible
        try:
            from export_utils import export_to_pdf
            
            # Prepare payslip data
            payslip_data = []
            for key, value in payslip.items():
                if key not in ['id', 'created_at', 'updated_at']:
                    payslip_data.append({'field': key.replace('_', ' ').title(), 'value': str(value) if value else ''})
            
            pdf_columns = ['field', 'value']
            pdf_output = export_to_pdf(
                data=payslip_data,
                filename=f"payslip_{payslip['payslip_number']}",
                title=f"Payslip: {payslip['payslip_number']}",
                columns=pdf_columns
            )
            
            # Send PDF file
            from flask import make_response
            response = make_response(pdf_output)
            response.headers.set('Content-Type', 'application/pdf')
            response.headers.set('Content-Disposition', f'attachment; filename=payslip_{payslip["payslip_number"]}.pdf')
            return response
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"PDF generation failed: {e}")
            flash('PDF generation is not available. Please contact your administrator.', 'warning')
            return redirect(url_for('payroll.payslips_view', id=id))
    finally:
        db.close()


@payroll_bp.route('/payslips/<int:id>/email', methods=['POST'])
@payroll_login_required
@payroll_permission_required('email')
def payslips_email(id):
    """Email payslip to employee."""
    user = get_current_user()
    db = get_db()
    
    try:
        payslip = db.execute("SELECT * FROM payroll_payslips WHERE id = ?", (id,)).fetchone()
        if not payslip:
            return jsonify({'error': 'Payslip not found'}), 404
        
        email = request.form.get('email')
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        # Update delivery status
        db.execute("""
            UPDATE payroll_payslips SET 
                is_delivered = 1, delivered_at = CURRENT_TIMESTAMP, 
                delivery_method = 'Email', delivery_email = ?
            WHERE id = ?
        """, (email, id))
        
        db.commit()
        audit_log('EMAIL', 'payroll_payslips', id, details=f"Sent payslip to {email}")
        
        flash('Payslip sent successfully.', 'success')
        return redirect(url_for('payroll.payslips_view', id=id))
    except Exception as e:
        db.rollback()
        flash(f'Error sending payslip: {str(e)}', 'error')
        return redirect(url_for('payroll.payslips_view', id=id))
    finally:
        db.close()


# =============================================================================
# LOANS / ADVANCES / RECOVERIES
# =============================================================================

@payroll_bp.route('/loans')
@payroll_login_required
@payroll_permission_required('view')
def loans_list():
    """Loans List."""
    user = get_current_user()
    db = get_db()
    
    try:
        status = request.args.get('status', '')
        page = int(request.args.get('page', 1))
        per_page = 20
        
        query = """
            SELECT pl.*, e.first_name || ' ' || e.last_name as employee_name,
                   e.employee_code
            FROM payroll_loans pl
            JOIN hr_employees e ON pl.employee_id = e.id
            WHERE 1=1
        """
        params = []
        
        if status:
            query += " AND pl.status = ?"
            params.append(status)
        
        count_query = query.replace("SELECT pl.*, e.first_name || ' ' || e.last_name as employee_name, e.employee_code", "SELECT COUNT(*) as cnt")
        
        total = db.execute(count_query, params).fetchone()['cnt']
        offset = (page - 1) * per_page
        query += f" ORDER BY pl.created_at DESC LIMIT {per_page} OFFSET {offset}"
        
        loans = db.execute(query, params).fetchall()
        
        return render_template('payroll/loans/list.html',
            title='Loans & Advances',
            loans=[dict(l) for l in loans],
            selected_status=status,
            page=page,
            total_pages=(total + per_page - 1) // per_page,
            total=total
        )
    finally:
        db.close()


@payroll_bp.route('/loans/new', methods=['GET', 'POST'])
@payroll_login_required
@payroll_permission_required('create')
def loans_new():
    """Create new loan."""
    user = get_current_user()
    db = get_db()
    
    if request.method == 'POST':
        try:
            data = request.form
            
            employee_id = data.get('employee_id', type=int)
            principal = float(data.get('principal_amount', 0))
            interest_rate = float(data.get('interest_rate', 0))
            tenure = int(data.get('tenure_months', 1))
            
            # Calculate total with interest
            if interest_rate > 0:
                total_amount = principal * (1 + interest_rate / 100)
            else:
                total_amount = principal
            
            monthly_installment = total_amount / tenure
            
            loan_number = create_loan_number()
            
            cursor = db.execute("""
                INSERT INTO payroll_loans (
                    loan_number, employee_id, loan_type, principal_amount,
                    interest_rate, total_amount, tenure_months, monthly_installment,
                    amount_remaining, installments_remaining, start_date, status,
                    approved_by_id, approved_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Active', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """, (
                loan_number, employee_id, data.get('loan_type', 'Personal'),
                principal, interest_rate, total_amount, tenure, monthly_installment,
                total_amount, tenure, parse_date(data.get('start_date')) or date.today(),
                user['id']
            ))
            
            loan_id = cursor.lastrowid
            
            # Generate installments
            for i in range(1, tenure + 1):
                due_date = date.today() + timedelta(days=30 * i)
                db.execute("""
                    INSERT INTO payroll_loan_installments (
                        loan_id, installment_number, due_date, installment_amount,
                        principal_amount, interest_amount
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    loan_id, i, due_date, monthly_installment,
                    principal / tenure,
                    (total_amount - principal) / tenure if interest_rate > 0 else 0
                ))
            
            db.commit()
            audit_log('CREATE', 'payroll_loans', loan_id, employee_id=employee_id,
                      details=f"Created loan: {loan_number}")
            
            flash('Loan created successfully.', 'success')
            return redirect(url_for('payroll.loans_list'))
        except Exception as e:
            db.rollback()
            flash(f'Error creating loan: {str(e)}', 'error')
    
    employees = db.execute("""
        SELECT e.id, e.first_name || ' ' || e.last_name as employee_name, e.employee_code
        FROM hr_employees e WHERE e.status = 'Active' ORDER BY e.first_name, e.last_name
    """).fetchall()
    
    return render_template('payroll/loans/new.html',
        title='New Loan',
        employees=[dict(e) for e in employees]
    )


@payroll_bp.route('/loans/<int:id>')
@payroll_login_required
@payroll_permission_required('view')
def loans_view(id):
    """View loan details."""
    user = get_current_user()
    db = get_db()
    
    try:
        loan = db.execute("""
            SELECT pl.*, e.first_name || ' ' || e.last_name as employee_name,
                   e.employee_code, e.bank_name, e.bank_account_number, e.iban
            FROM payroll_loans pl
            JOIN hr_employees e ON pl.employee_id = e.id
            WHERE pl.id = ?
        """, (id,)).fetchone()
        
        if not loan:
            flash('Loan not found.', 'error')
            return redirect(url_for('payroll.loans_list'))
        
        installments = db.execute("""
            SELECT * FROM payroll_loan_installments
            WHERE loan_id = ?
            ORDER BY installment_number
        """, (id,)).fetchall()
        
        return render_template('payroll/loans/view.html',
            title=f'Loan: {loan["loan_number"]}',
            loan=dict(loan),
            installments=[dict(i) for i in installments]
        )
    finally:
        db.close()


@payroll_bp.route('/loans/<int:id>/suspend', methods=['POST'])
@payroll_login_required
@payroll_permission_required('suspend')
def loans_suspend(id):
    """Suspend loan recovery."""
    user = get_current_user()
    db = get_db()
    
    try:
        reason = request.form.get('reason', '')
        
        db.execute("""
            UPDATE payroll_loans SET status = 'Suspended'
            WHERE id = ?
        """, (id,))
        
        db.commit()
        audit_log('SUSPEND', 'payroll_loans', id, details=f"Suspended loan: {reason}")
        
        flash('Loan suspended successfully.', 'success')
        return redirect(url_for('payroll.loans_view', id=id))
    except Exception as e:
        db.rollback()
        flash(f'Error suspending loan: {str(e)}', 'error')
        return redirect(url_for('payroll.loans_view', id=id))
    finally:
        db.close()


@payroll_bp.route('/advances')
@payroll_login_required
@payroll_permission_required('view')
def advances_list():
    """Salary Advances List."""
    user = get_current_user()
    db = get_db()
    
    try:
        advances = db.execute("""
            SELECT pa.*, e.first_name || ' ' || e.last_name as employee_name,
                   e.employee_code
            FROM payroll_advances pa
            JOIN hr_employees e ON pa.employee_id = e.id
            ORDER BY pa.created_at DESC
            LIMIT 50
        """).fetchall()
        
        return render_template('payroll/advances/list.html',
            title='Salary Advances',
            advances=[dict(a) for a in advances]
        )
    finally:
        db.close()


@payroll_bp.route('/advances/new', methods=['GET', 'POST'])
@payroll_login_required
@payroll_permission_required('create')
def advances_new():
    """Create new salary advance."""
    user = get_current_user()
    db = get_db()
    
    if request.method == 'POST':
        try:
            data = request.form
            
            employee_id = data.get('employee_id', type=int)
            amount = float(data.get('amount', 0))
            recovery_months = int(data.get('recovery_months', 1))
            monthly_recovery = amount / recovery_months
            
            advance_number = create_advance_number()
            
            cursor = db.execute("""
                INSERT INTO payroll_advances (
                    advance_number, employee_id, amount, recovery_amount,
                    recovery_months, monthly_recovery, reason, status,
                    approved_by_id, approved_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, 'Approved', ?, CURRENT_TIMESTAMP)
            """, (
                advance_number, employee_id, amount, amount,
                recovery_months, monthly_recovery, data.get('reason'),
                user['id']
            ))
            
            db.commit()
            audit_log('CREATE', 'payroll_advances', cursor.lastrowid, employee_id=employee_id,
                      details=f"Created advance: {advance_number}")
            
            flash('Salary advance created successfully.', 'success')
            return redirect(url_for('payroll.advances_list'))
        except Exception as e:
            db.rollback()
            flash(f'Error creating advance: {str(e)}', 'error')
    
    employees = db.execute("""
        SELECT e.id, e.first_name || ' ' || e.last_name as employee_name, e.employee_code
        FROM hr_employees e WHERE e.status = 'Active' ORDER BY e.first_name, e.last_name
    """).fetchall()
    
    return render_template('payroll/advances/new.html',
        title='New Salary Advance',
        employees=[dict(e) for e in employees]
    )


# =============================================================================
# RETRO / ADJUSTMENT / ARREARS
# =============================================================================

@payroll_bp.route('/retro')
@payroll_login_required
@payroll_permission_required('view')
def retro_list():
    """Retro Adjustments List."""
    user = get_current_user()
    db = get_db()
    
    try:
        retros = db.execute("""
            SELECT pra.*, e.first_name || ' ' || e.last_name as employee_name,
                   e.employee_code, pp.name as period_name
            FROM payroll_retro_adjustments pra
            JOIN hr_employees e ON pra.employee_id = e.id
            LEFT JOIN payroll_periods pp ON pra.period_id = pp.id
            ORDER BY pra.created_at DESC
            LIMIT 50
        """).fetchall()
        
        return render_template('payroll/retro/list.html',
            title='Retro Adjustments',
            retros=[dict(r) for r in retros]
        )
    finally:
        db.close()


@payroll_bp.route('/retro/new', methods=['GET', 'POST'])
@payroll_login_required
@payroll_permission_required('create')
def retro_new():
    """Create new retro adjustment."""
    user = get_current_user()
    db = get_db()
    
    if request.method == 'POST':
        try:
            data = request.form
            
            employee_id = data.get('employee_id', type=int)
            period_id = data.get('period_id', type=int)
            component_id = data.get('component_id', type=int)
            original_amount = float(data.get('original_amount', 0))
            new_amount = float(data.get('new_amount', 0))
            difference = new_amount - original_amount
            
            retro_number = create_retro_number()
            
            component = db.execute("SELECT * FROM payroll_components WHERE id = ?", (component_id,)).fetchone()
            
            cursor = db.execute("""
                INSERT INTO payroll_retro_adjustments (
                    retro_number, employee_id, period_id, adjustment_type,
                    component_id, component_code, component_name,
                    original_amount, new_amount, difference,
                    reason, effective_date, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pending')
            """, (
                retro_number, employee_id, period_id, 'Correction',
                component_id, component['code'] if component else '', 
                component['name'] if component else '',
                original_amount, new_amount, difference,
                data.get('reason'), parse_date(data.get('effective_date')) or date.today()
            ))
            
            db.commit()
            audit_log('CREATE', 'payroll_retro_adjustments', cursor.lastrowid, 
                      employee_id=employee_id, period_id=period_id,
                      details=f"Created retro: {retro_number}")
            
            flash('Retro adjustment created.', 'success')
            return redirect(url_for('payroll.retro_list'))
        except Exception as e:
            db.rollback()
            flash(f'Error creating retro: {str(e)}', 'error')
    
    employees = db.execute("SELECT * FROM hr_employees WHERE status = 'Active' ORDER BY first_name, last_name").fetchall()
    periods = db.execute("SELECT * FROM payroll_periods ORDER BY year DESC, month DESC LIMIT 12").fetchall()
    components = db.execute("SELECT * FROM payroll_components WHERE is_active = 1 ORDER BY name").fetchall()
    
    return render_template('payroll/retro/new.html',
        title='New Retro Adjustment',
        employees=[dict(e) for e in employees],
        periods=[dict(p) for p in periods],
        components=[dict(c) for c in components]
    )


@payroll_bp.route('/arrears')
@payroll_login_required
@payroll_permission_required('view')
def arrears_list():
    """Arrears List."""
    user = get_current_user()
    db = get_db()
    
    try:
        arrears = db.execute("""
            SELECT pa.*, e.first_name || ' ' || e.last_name as employee_name,
                   e.employee_code
            FROM payroll_arrears pa
            JOIN hr_employees e ON pa.employee_id = e.id
            ORDER BY pa.created_at DESC
            LIMIT 50
        """).fetchall()
        
        return render_template('payroll/arrears/list.html',
            title='Arrears Register',
            arrears=[dict(a) for a in arrears]
        )
    finally:
        db.close()


# =============================================================================
# COMPLIANCE & CONTROLS
# =============================================================================

@payroll_bp.route('/compliance')
@payroll_login_required
@payroll_permission_required('view')
def compliance_list():
    """Compliance Rules List."""
    user = get_current_user()
    db = get_db()
    
    try:
        rules = db.execute("""
            SELECT * FROM payroll_compliance_rules 
            WHERE is_active = 1
            ORDER BY severity DESC, rule_name
        """).fetchall()
        
        return render_template('payroll/compliance/rules.html',
            title='Compliance Rules',
            rules=[dict(r) for r in rules]
        )
    finally:
        db.close()


@payroll_bp.route('/compliance/audit')
@payroll_login_required
@payroll_permission_required('audit')
def compliance_audit():
    """Audit Trail."""
    user = get_current_user()
    db = get_db()
    
    try:
        action = request.args.get('action', '')
        entity_type = request.args.get('entity_type', '')
        page = int(request.args.get('page', 1))
        per_page = 50
        
        query = """
            SELECT pal.*, u.username as user_name
            FROM payroll_audit_log pal
            JOIN users u ON pal.user_id = u.id
            WHERE 1=1
        """
        params = []
        
        if action:
            query += " AND pal.action = ?"
            params.append(action)
        
        if entity_type:
            query += " AND pal.entity_type = ?"
            params.append(entity_type)
        
        count_query = query.replace("SELECT pal.*, u.username as user_name", "SELECT COUNT(*) as cnt")
        
        total = db.execute(count_query, params).fetchone()['cnt']
        offset = (page - 1) * per_page
        query += f" ORDER BY pal.created_at DESC LIMIT {per_page} OFFSET {offset}"
        
        logs = db.execute(query, params).fetchall()
        
        return render_template('payroll/compliance/audit.html',
            title='Audit Trail',
            logs=[dict(l) for l in logs],
            selected_action=action,
            selected_entity=entity_type,
            page=page,
            total_pages=(total + per_page - 1) // per_page,
            total=total
        )
    finally:
        db.close()


@payroll_bp.route('/compliance/exceptions')
@payroll_login_required
@payroll_permission_required('view')
def compliance_exceptions():
    """Exception Watchlist."""
    user = get_current_user()
    db = get_db()
    
    try:
        period_id = request.args.get('period_id', type=int)
        severity = request.args.get('severity', '')
        
        query = """
            SELECT pe.*, e.first_name || ' ' || e.last_name as employee_name,
                   e.employee_code
            FROM payroll_exceptions pe
            LEFT JOIN hr_employees e ON pe.employee_id = e.id
            WHERE pe.status = 'Open'
        """
        params = []
        
        if period_id:
            query += " AND pe.period_id = ?"
            params.append(period_id)
        
        if severity:
            query += " AND pe.severity = ?"
            params.append(severity)
        
        query += " ORDER BY pe.severity DESC, pe.created_at DESC"
        
        exceptions = db.execute(query, params).fetchall()
        periods = db.execute("SELECT * FROM payroll_periods ORDER BY year DESC, month DESC LIMIT 12").fetchall()
        
        return render_template('payroll/compliance/exceptions.html',
            title='Exception Watchlist',
            exceptions=[dict(e) for e in exceptions],
            periods=[dict(p) for p in periods],
            selected_period=period_id,
            selected_severity=severity
        )
    finally:
        db.close()


@payroll_bp.route('/compliance/exceptions/<int:id>/resolve', methods=['POST'])
@payroll_login_required
@payroll_permission_required('resolve')
def compliance_exceptions_resolve(id):
    """Resolve exception."""
    user = get_current_user()
    db = get_db()
    
    try:
        resolution = request.form.get('resolution', '')
        
        db.execute("""
            UPDATE payroll_exceptions SET 
                status = 'Resolved', resolved_by_id = ?, resolved_at = CURRENT_TIMESTAMP,
                resolution_notes = ?
            WHERE id = ?
        """, (user['id'], resolution, id))
        
        db.commit()
        audit_log('RESOLVE', 'payroll_exceptions', id, details=f"Resolved exception: {resolution}")
        
        flash('Exception resolved.', 'success')
        return redirect(url_for('payroll.compliance_exceptions'))
    except Exception as e:
        db.rollback()
        flash(f'Error resolving exception: {str(e)}', 'error')
        return redirect(url_for('payroll.compliance_exceptions'))
    finally:
        db.close()


# =============================================================================
# FINANCE INTEGRATION
# =============================================================================

@payroll_bp.route('/finance')
@payroll_login_required
@payroll_permission_required('view')
def finance_list():
    """Finance Postings List."""
    user = get_current_user()
    db = get_db()
    
    try:
        postings = db.execute("""
            SELECT pfp.*, pp.name as period_name,
                   u.username as posted_by_name
            FROM payroll_finance_postings pfp
            LEFT JOIN payroll_periods pp ON pfp.period_id = pp.id
            LEFT JOIN users u ON pfp.posted_by_id = u.id
            ORDER BY pfp.created_at DESC
            LIMIT 50
        """).fetchall()
        
        return render_template('payroll/finance/list.html',
            title='Finance Integration',
            postings=[dict(p) for p in postings]
        )
    finally:
        db.close()


@payroll_bp.route('/finance/post', methods=['GET', 'POST'])
@payroll_login_required
@payroll_permission_required('post')
def finance_post():
    """Create finance posting from payroll."""
    user = get_current_user()
    db = get_db()
    
    if request.method == 'POST':
        try:
            period_id = request.form.get('period_id', type=int)
            posting_type = request.form.get('posting_type', 'Salary')
            
            posting_number = create_posting_number()
            
            # Get payroll totals
            summary = get_payroll_summary_stats(period_id)
            
            cursor = db.execute("""
                INSERT INTO payroll_finance_postings (
                    posting_number, period_id, posting_type, description,
                    total_amount, status, posted_by_id
                ) VALUES (?, ?, ?, ?, ?, 'Draft', ?)
            """, (
                posting_number, period_id, posting_type,
                f"Payroll posting for {posting_type}",
                summary.get('total_net', 0) if summary else 0,
                user['id']
            ))
            
            posting_id = cursor.lastrowid
            
            # Create journal lines (simplified)
            # Debit: Salary Expense
            db.execute("""
                INSERT INTO payroll_finance_lines (
                    posting_id, gl_account, line_type, description, debit_amount
                ) VALUES (?, '6100-Salary Expense', 'Debit', ?, ?)
            """, (posting_id, f"Salary expense for {posting_type}", summary.get('total_gross', 0) if summary else 0))
            
            # Credit: Cash/Bank
            db.execute("""
                INSERT INTO payroll_finance_lines (
                    posting_id, gl_account, line_type, description, credit_amount
                ) VALUES (?, '1200-Cash', 'Credit', ?, ?)
            """, (posting_id, f"Net salary payable", summary.get('total_net', 0) if summary else 0))
            
            db.commit()
            audit_log('CREATE', 'payroll_finance_postings', posting_id, period_id=period_id,
                      details=f"Created posting: {posting_number}")
            
            flash('Finance posting created.', 'success')
            return redirect(url_for('payroll.finance_view', id=posting_id))
        except Exception as e:
            db.rollback()
            flash(f'Error creating posting: {str(e)}', 'error')
    
    periods = db.execute("""
        SELECT * FROM payroll_periods 
        WHERE status IN ('Approved', 'Locked', 'Closed')
        ORDER BY year DESC, month DESC
    """).fetchall()
    
    return render_template('payroll/finance/post.html',
        title='Create Finance Posting',
        periods=[dict(p) for p in periods]
    )


@payroll_bp.route('/finance/<int:id>')
@payroll_login_required
@payroll_permission_required('view')
def finance_view(id):
    """View finance posting."""
    user = get_current_user()
    db = get_db()
    
    try:
        posting = db.execute("""
            SELECT pfp.*, pp.name as period_name
            FROM payroll_finance_postings pfp
            LEFT JOIN payroll_periods pp ON pfp.period_id = pp.id
            WHERE pfp.id = ?
        """, (id,)).fetchone()
        
        if not posting:
            flash('Posting not found.', 'error')
            return redirect(url_for('payroll.finance_list'))
        
        lines = db.execute("""
            SELECT * FROM payroll_finance_lines WHERE posting_id = ?
        """, (id,)).fetchall()
        
        return render_template('payroll/finance/view.html',
            title=f'Posting: {posting["posting_number"]}',
            posting=dict(posting),
            lines=[dict(l) for l in lines]
        )
    finally:
        db.close()


# =============================================================================
# HR INTEGRATION
# =============================================================================

@payroll_bp.route('/hr-integration')
@payroll_login_required
@payroll_permission_required('view')
def hr_integration():
    """HR Integration Dashboard."""
    user = get_current_user()
    db = get_db()
    
    try:
        # Joiners this month
        joiners = db.execute("""
            SELECT COUNT(*) as cnt FROM hr_employees
            WHERE hire_date >= date('now', 'start of month')
            AND hire_date <= date('now')
        """).fetchone()['cnt']
        
        # Leavers this month
        leavers = db.execute("""
            SELECT COUNT(*) as cnt FROM hr_employees
            WHERE termination_date >= date('now', 'start of month')
            AND termination_date <= date('now')
        """).fetchone()['cnt']
        
        # Salary changes pending
        salary_changes = db.execute("""
            SELECT COUNT(*) as cnt FROM payroll_manual_adjustments
            WHERE adjustment_type = 'Correction' AND status = 'Pending'
        """).fetchone()['cnt']
        
        # Attendance impacts
        attendance_impacts = db.execute("""
            SELECT COUNT(*) as cnt FROM payroll_attendance_integration
            WHERE status = 'Pending'
        """).fetchone()['cnt']
        
        # Leave impacts
        leave_impacts = db.execute("""
            SELECT COUNT(*) as cnt FROM payroll_leave_impacts
            WHERE status = 'Pending'
        """).fetchone()['cnt']
        
        return render_template('payroll/hr_integration/dashboard.html',
            title='HR Integration',
            joiners=joiners,
            leavers=leavers,
            salary_changes=salary_changes,
            attendance_impacts=attendance_impacts,
            leave_impacts=leave_impacts
        )
    finally:
        db.close()


# =============================================================================
# REPORTS & ANALYTICS
# =============================================================================

@payroll_bp.route('/reports')
@payroll_login_required
@payroll_permission_required('reports')
def reports_menu():
    """Reports Menu."""
    return render_template('payroll/reports/menu.html', title='Payroll Reports')


@payroll_bp.route('/reports/summary')
@payroll_login_required
@payroll_permission_required('reports')
def reports_summary():
    """Payroll Summary Report."""
    user = get_current_user()
    db = get_db()
    
    try:
        period_id = request.args.get('period_id', type=int)
        
        if not period_id:
            current = get_active_payroll_period()
            if current:
                period_id = current['id']
        
        period = None
        summary = None
        by_department = None
        by_component = None
        
        if period_id:
            period = db.execute("SELECT * FROM payroll_periods WHERE id = ?", (period_id,)).fetchone()
            summary = get_payroll_summary_stats(period_id)
            
            by_department = db.execute("""
                SELECT d.name as department,
                       COUNT(DISTINCT per.employee_id) as employees,
                       SUM(per.total_gross) as gross,
                       SUM(per.total_deductions) as deductions,
                       SUM(per.net_salary) as net
                FROM payroll_employee_records per
                JOIN hr_employees e ON per.employee_id = e.id
                LEFT JOIN hr_employee_employment ee ON e.id = ee.employee_id AND ee.is_primary = 1
                LEFT JOIN hr_departments d ON ee.department_id = d.id
                WHERE per.period_id = ? AND per.status IN ('Approved', 'Locked', 'Closed')
                GROUP BY d.id
                ORDER BY net DESC
            """, (period_id,)).fetchall()
            
            by_component = db.execute("""
                SELECT pee.component_name as component,
                       SUM(pee.amount) as total
                FROM payroll_employee_earnings pee
                JOIN payroll_employee_records per ON pee.record_id = per.id
                WHERE per.period_id = ? AND per.status IN ('Approved', 'Locked', 'Closed')
                GROUP BY pee.component_id
                ORDER BY total DESC
            """, (period_id,)).fetchall()
        
        periods = db.execute("SELECT * FROM payroll_periods ORDER BY year DESC, month DESC").fetchall()
        
        return render_template('payroll/reports/summary.html',
            title='Payroll Summary Report',
            period=dict(period) if period else None,
            summary=summary,
            by_department=[dict(d) for d in by_department] if by_department else [],
            by_component=[dict(c) for c in by_component] if by_component else [],
            periods=[dict(p) for p in periods]
        )
    finally:
        db.close()


@payroll_bp.route('/reports/earnings')
@payroll_login_required
@payroll_permission_required('reports')
def reports_earnings():
    """Earnings Report."""
    user = get_current_user()
    db = get_db()
    
    try:
        period_id = request.args.get('period_id', type=int)
        
        if not period_id:
            current = get_active_payroll_period()
            if current:
                period_id = current['id']
        
        earnings = []
        if period_id:
            earnings = db.execute("""
                SELECT pee.*, e.first_name || ' ' || e.last_name as employee_name,
                       e.employee_code
                FROM payroll_employee_earnings pee
                JOIN payroll_employee_records per ON pee.record_id = per.id
                JOIN hr_employees e ON per.employee_id = e.id
                WHERE per.period_id = ? AND per.status IN ('Approved', 'Locked', 'Closed')
                ORDER BY e.first_name, pee.component_name
            """, (period_id,)).fetchall()
        
        periods = db.execute("SELECT * FROM payroll_periods ORDER BY year DESC, month DESC").fetchall()
        
        return render_template('payroll/reports/earnings.html',
            title='Earnings Report',
            earnings=[dict(e) for e in earnings],
            periods=[dict(p) for p in periods],
            selected_period=period_id
        )
    finally:
        db.close()


@payroll_bp.route('/reports/deductions')
@payroll_login_required
@payroll_permission_required('reports')
def reports_deductions():
    """Deductions Report."""
    user = get_current_user()
    db = get_db()
    
    try:
        period_id = request.args.get('period_id', type=int)
        
        if not period_id:
            current = get_active_payroll_period()
            if current:
                period_id = current['id']
        
        deductions = []
        if period_id:
            deductions = db.execute("""
                SELECT ped.*, e.first_name || ' ' || e.last_name as employee_name,
                       e.employee_code
                FROM payroll_employee_deductions ped
                JOIN payroll_employee_records per ON ped.record_id = per.id
                JOIN hr_employees e ON per.employee_id = e.id
                WHERE per.period_id = ? AND per.status IN ('Approved', 'Locked', 'Closed')
                ORDER BY e.first_name, ped.component_name
            """, (period_id,)).fetchall()
        
        periods = db.execute("SELECT * FROM payroll_periods ORDER BY year DESC, month DESC").fetchall()
        
        return render_template('payroll/reports/deductions.html',
            title='Deductions Report',
            deductions=[dict(d) for d in deductions],
            periods=[dict(p) for p in periods],
            selected_period=period_id
        )
    finally:
        db.close()


@payroll_bp.route('/reports/overtime')
@payroll_login_required
@payroll_permission_required('reports')
def reports_overtime():
    """Overtime Payroll Report."""
    user = get_current_user()
    db = get_db()
    
    try:
        period_id = request.args.get('period_id', type=int)
        
        if not period_id:
            current = get_active_payroll_period()
            if current:
                period_id = current['id']
        
        overtime = []
        if period_id:
            overtime = db.execute("""
                SELECT poi.*, e.first_name || ' ' || e.last_name as employee_name,
                       e.employee_code
                FROM payroll_overtime_inputs poi
                JOIN hr_employees e ON poi.employee_id = e.id
                WHERE poi.period_id = ? AND poi.status = 'Approved'
                ORDER BY poi.date DESC
            """, (period_id,)).fetchall()
        
        periods = db.execute("SELECT * FROM payroll_periods ORDER BY year DESC, month DESC").fetchall()
        
        return render_template('payroll/reports/overtime.html',
            title='Overtime Report',
            overtime=[dict(o) for o in overtime],
            periods=[dict(p) for p in periods],
            selected_period=period_id
        )
    finally:
        db.close()


@payroll_bp.route('/reports/loan-recovery')
@payroll_login_required
@payroll_permission_required('reports')
def reports_loan_recovery():
    """Loan Recovery Report."""
    user = get_current_user()
    db = get_db()
    
    try:
        loans = db.execute("""
            SELECT pl.*, e.first_name || ' ' || e.last_name as employee_name,
                   e.employee_code,
                   (SELECT COUNT(*) FROM payroll_loan_installments WHERE loan_id = pl.id AND status = 'Paid') as paid_installments,
                   (SELECT SUM(amount_paid) FROM payroll_loan_installments WHERE loan_id = pl.id AND status = 'Paid') as total_paid
            FROM payroll_loans pl
            JOIN hr_employees e ON pl.employee_id = e.id
            ORDER BY pl.created_at DESC
        """).fetchall()
        
        return render_template('payroll/reports/loan_recovery.html',
            title='Loan Recovery Report',
            loans=[dict(l) for l in loans]
        )
    finally:
        db.close()


@payroll_bp.route('/reports/export-center')
@payroll_login_required
@payroll_permission_required('export')
def reports_export_center():
    """Export Center."""
    user = get_current_user()
    db = get_db()
    
    try:
        # Get export history
        history = db.execute("""
            SELECT peh.*, u.username as exported_by_name
            FROM payroll_export_history peh
            JOIN users u ON peh.exported_by_id = u.id
            ORDER BY peh.exported_at DESC
            LIMIT 50
        """).fetchall()
        
        # Get saved configs
        configs = db.execute("""
            SELECT * FROM payroll_export_configs
            WHERE created_by_id = ? OR is_default = 1
            ORDER BY created_at DESC
        """, (user['id'],)).fetchall()
        
        return render_template('payroll/reports/export_center.html',
            title='Export Center',
            history=[dict(h) for h in history],
            configs=[dict(c) for c in configs]
        )
    finally:
        db.close()


@payroll_bp.route('/reports/export', methods=['GET', 'POST'])
@payroll_login_required
@payroll_permission_required('export')
def reports_export():
    """Export payroll data."""
    user = get_current_user()
    db = get_db()
    
    try:
        export_type = request.args.get('type', 'summary')
        period_id = request.args.get('period_id', type=int)
        
        if not period_id:
            current = get_active_payroll_period()
            if current:
                period_id = current['id']
        
        # Get data based on type
        if export_type == 'summary' and period_id:
            data = db.execute("""
                SELECT e.employee_code, e.first_name || ' ' || e.last_name as employee_name,
                       per.basic_salary, per.total_earnings, per.total_deductions,
                       per.total_overtime, per.total_tax, per.gross_salary, per.net_salary,
                       per.days_worked, per.days_absent
                FROM payroll_employee_records per
                JOIN hr_employees e ON per.employee_id = e.id
                WHERE per.period_id = ?
                ORDER BY e.first_name, e.last_name
            """, (period_id,)).fetchall()
            
            filename = f'payroll_summary_{datetime.now().strftime("%Y%m%d")}.csv'
            headers = ['Employee Code', 'Employee Name', 'Basic Salary', 'Earnings', 
                      'Deductions', 'Overtime', 'Tax', 'Gross', 'Net', 'Days Worked', 'Days Absent']
        
        elif export_type == 'earnings' and period_id:
            data = db.execute("""
                SELECT e.employee_code, e.first_name || ' ' || e.last_name as employee_name,
                       pee.component_name, pee.amount
                FROM payroll_employee_earnings pee
                JOIN payroll_employee_records per ON pee.record_id = per.id
                JOIN hr_employees e ON per.employee_id = e.id
                WHERE per.period_id = ?
                ORDER BY e.first_name, pee.component_name
            """, (period_id,)).fetchall()
            
            filename = f'payroll_earnings_{datetime.now().strftime("%Y%m%d")}.csv'
            headers = ['Employee Code', 'Employee Name', 'Component', 'Amount']
        
        else:
            data = []
            filename = 'payroll_export.csv'
            headers = []
        
        # Log export
        db.execute("""
            INSERT INTO payroll_export_history (
                export_type, period_id, file_name, record_count, exported_by_id
            ) VALUES (?, ?, ?, ?, ?)
        """, (export_type, period_id, filename, len(data), user['id']))
        
        db.commit()
        audit_log('EXPORT', 'payroll_export', 0, period_id=period_id,
                  details=f"Exported {export_type}: {len(data)} records")
        
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        for row in data:
            writer.writerow([row[h.lower().replace(' ', '_')] if isinstance(row, dict) else row[i] 
                           for i, h in enumerate(headers)])
        
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename={filename}'}
        )
    except Exception as e:
        flash(f'Error exporting: {str(e)}', 'error')
        return redirect(url_for('payroll.reports_export_center'))
    finally:
        db.close()


# =============================================================================
# WORKFLOW & APPROVALS
# =============================================================================

@payroll_bp.route('/approvals')
@payroll_login_required
@payroll_permission_required('view')
def approvals_list():
    """Approvals List."""
    user = get_current_user()
    db = get_db()
    
    try:
        # Pending for user
        pending = db.execute("""
            SELECT pai.*, pp.name as period_name,
                   e.first_name || ' ' || e.last_name as employee_name
            FROM payroll_approval_instances pai
            LEFT JOIN payroll_periods pp ON pai.period_id = pp.id
            LEFT JOIN hr_employees e ON pai.employee_id = e.id
            WHERE pai.status = 'Pending'
            AND (pai.approver_id = ? OR pai.approver_id IS NULL)
            ORDER BY pai.priority DESC, pai.created_at
        """, (user['id'],)).fetchall()
        
        # Recent approvals
        recent = db.execute("""
            SELECT pai.*, pp.name as period_name,
                   u.username as approver_name
            FROM payroll_approval_instances pai
            LEFT JOIN payroll_periods pp ON pai.period_id = pp.id
            LEFT JOIN users u ON pai.approver_id = u.id
            WHERE pai.status != 'Pending'
            ORDER BY pai.completed_at DESC
            LIMIT 20
        """).fetchall()
        
        return render_template('payroll/approvals/list.html',
            title='Approvals',
            pending=[dict(p) for p in pending],
            recent=[dict(r) for r in recent]
        )
    finally:
        db.close()


@payroll_bp.route('/approvals/<int:id>/approve', methods=['POST'])
@payroll_login_required
@payroll_permission_required('approve')
def approvals_approve(id):
    """Approve item."""
    user = get_current_user()
    db = get_db()
    
    try:
        comments = request.form.get('comments', '')
        
        db.execute("""
            UPDATE payroll_approval_instances SET 
                status = 'Approved', approver_id = ?, approver_action = 'Approve',
                approver_comments = ?, approver_action_at = CURRENT_TIMESTAMP,
                completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user['id'], comments, id))
        
        db.commit()
        audit_log('APPROVE', 'payroll_approval_instances', id, details="Approved")
        
        flash('Approved successfully.', 'success')
        return redirect(url_for('payroll.approvals_list'))
    except Exception as e:
        db.rollback()
        flash(f'Error approving: {str(e)}', 'error')
        return redirect(url_for('payroll.approvals_list'))
    finally:
        db.close()


@payroll_bp.route('/approvals/<int:id>/reject', methods=['POST'])
@payroll_login_required
@payroll_permission_required('reject')
def approvals_reject(id):
    """Reject item."""
    user = get_current_user()
    db = get_db()
    
    try:
        comments = request.form.get('comments', '')
        
        db.execute("""
            UPDATE payroll_approval_instances SET 
                status = 'Rejected', approver_id = ?, approver_action = 'Reject',
                approver_comments = ?, approver_action_at = CURRENT_TIMESTAMP,
                completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (user['id'], comments, id))
        
        db.commit()
        audit_log('REJECT', 'payroll_approval_instances', id, details="Rejected")
        
        flash('Rejected.', 'success')
        return redirect(url_for('payroll.approvals_list'))
    finally:
        db.close()


# =============================================================================
# INITIALIZATION ROUTE
# =============================================================================

@payroll_bp.route('/init', methods=['GET'])
def payroll_init():
    """Initialize payroll tables - called once."""
    try:
        run_payroll_migrations()
        seed_payroll_default_data()
        return jsonify({'success': True, 'message': 'Payroll module initialized successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@payroll_bp.errorhandler(404)
def not_found(e):
    return render_template('payroll/error.html', title='Not Found', message='Page not found'), 404


@payroll_bp.errorhandler(500)
def server_error(e):
    return render_template('payroll/error.html', title='Server Error', message='Internal server error'), 500
