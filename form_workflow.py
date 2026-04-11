# ============================================================================
# FORM WORKFLOW PROCESSOR ENGINE
# Handles workflow execution, routing, escalation, and SLA tracking
# ============================================================================

from database import get_db_context, get_one, get_all, log_audit
from form_models import (
    get_submission, get_template_workflow, get_workflow_steps,
    get_workflow_transitions, update_submission_status,
    assign_submission, add_approval, create_form_notification
)
from permissions import get_user_permissions


# ============================================================================
# WORKFLOW PROCESSOR
# ============================================================================

class WorkflowProcessor:
    """Processes workflow steps and transitions for form submissions."""

    def __init__(self, submission_id):
        self.submission_id = submission_id
        self.submission = get_submission(submission_id)
        self.workflow = None
        self.steps = []
        self.current_step = None

        if self.submission:
            self.workflow = get_template_workflow(self.submission['template_id'])
            if self.workflow:
                self.steps = get_workflow_steps(self.workflow['id'])
                self._find_current_step()

    def _find_current_step(self):
        """Find the current workflow step for this submission."""
        from form_models import get_current_workflow_step
        step_id = get_current_workflow_step(self.submission_id)
        if step_id:
            for step in self.steps:
                if step['id'] == step_id:
                    self.current_step = step
                    break

    def can_transition(self, action, user_id):
        """Check if a user can perform an action on the current step."""
        if not self.current_step:
            return False

        step = self.current_step

        # Check if action is allowed at this step
        allowed_actions = step.get('allowed_actions', '').split(',')
        if action not in allowed_actions and '*' not in allowed_actions:
            return False

        # Check user permission
        if step['approver_type'] == 'role':
            user_perms = get_user_permissions(user_id)
            if step['approver_id'] not in user_perms:
                return False
        elif step['approver_type'] == 'user':
            if step['approver_id'] != user_id:
                # Check if user is a delegate
                if not self._is_delegate(user_id, step['approver_id']):
                    return False

        return True

    def _is_delegate(self, user_id, approver_id):
        """Check if user_id is a delegate for approver_id."""
        delegation = get_one("""
            SELECT 1 FROM form_approvals
            WHERE approved_by = ? AND is_delegated = 1
            AND submission_id = ?
        """, (approver_id, self.submission_id))
        return delegation is not None

    def execute_action(self, action, user_id, comment=None, data=None):
        """Execute a workflow action (approve, reject, return, etc.)."""
        if not self.can_transition(action, user_id):
            return {'success': False, 'message': 'Action not permitted'}

        data = data or {}

        # Find transition for this action
        transition = self._find_transition(action)
        if not transition and self.current_step:
            # Use step's default next step
            if action == 'approve':
                next_step_id = self.current_step.get('next_step_id')
            elif action == 'reject':
                next_step_id = self.current_step.get('reject_step_id')
            elif action == 'return':
                next_step_id = self.current_step.get('return_step_id')
            else:
                next_step_id = None
        elif transition:
            next_step_id = transition['to_step_id']
        else:
            next_step_id = None

        # Execute pre-transition hooks
        pre_result = self._execute_pre_hook(action, user_id, data)
        if not pre_result['success']:
            return pre_result

        # Record the action
        if action in ['approve', 'reject', 'return', 'revise']:
            add_approval(
                submission_id=self.submission_id,
                workflow_step_id=self.current_step['id'] if self.current_step else None,
                approved_by=user_id,
                approval_action=action,
                approval_comment=comment
            )

        # Update submission status
        status_map = {
            'approve': 'approved',
            'reject': 'rejected',
            'return': 'returned_for_correction',
            'submit': 'submitted',
            'escalate': 'escalated',
            'delegate': 'delegated'
        }
        new_status = status_map.get(action, self.submission['status'])
        update_submission_status(self.submission_id, new_status, user_id, reason=comment)

        # Move to next step
        if next_step_id:
            self._move_to_step(next_step_id, user_id)

            # Assign to next approver
            next_step = self._get_step(next_step_id)
            if next_step and next_step.get('assigned_to'):
                assign_submission(
                    submission_id=self.submission_id,
                    assigned_to=next_step['assigned_to'],
                    assigned_by=user_id,
                    workflow_step_id=next_step_id
                )

                # Notify next approver
                create_form_notification(
                    submission_id=self.submission_id,
                    notification_type='pending_approval',
                    title='Pending Approval',
                    message=f'A form requires your approval: {self.submission["submission_number"]}',
                    recipient_id=next_step['assigned_to']
                )
        else:
            # Finalize if no more steps
            self._finalize_workflow(user_id)

        # Execute post-transition hooks
        self._execute_post_hook(action, user_id, data)

        # Log audit
        log_audit('form_workflow', self.submission_id, action.upper(), user_id, notes=comment)

        return {'success': True, 'message': f'Action {action} completed', 'next_step': next_step_id}

    def _find_transition(self, action):
        """Find a transition matching the action."""
        if not self.workflow:
            return None

        transitions = get_workflow_transitions(self.workflow['id'])
        for t in transitions:
            if t['action'] == action and t['from_step_id'] == (self.current_step['id'] if self.current_step else None):
                return t
        return None

    def _get_step(self, step_id):
        """Get a workflow step by ID."""
        for step in self.steps:
            if step['id'] == step_id:
                return step
        return None

    def _move_to_step(self, step_id, user_id):
        """Move submission to a new workflow step."""
        with get_db_context() as db:
            db.execute("""
                UPDATE form_submissions
                SET current_step_id = ?, current_step_status = 'in_progress'
                WHERE id = ?
            """, (step_id, self.submission_id))
            db.commit()

    def _finalize_workflow(self, user_id):
        """Finalize the workflow (all steps complete)."""
        with get_db_context() as db:
            db.execute("""
                UPDATE form_submissions
                SET current_step_status = 'completed', workflow_completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (self.submission_id,))
            db.commit()

        # Notify submitter of completion
        create_form_notification(
            submission_id=self.submission_id,
            notification_type='completed',
            title='Form Completed',
            message=f'Your form {self.submission["submission_number"]} has been approved.',
            recipient_id=self.submission['submitted_by']
        )

    def _execute_pre_hook(self, action, user_id, data):
        """Execute pre-transition hook (validation, etc.)."""
        # Check required fields based on action
        if action == 'reject' and not data.get('comment'):
            return {'success': False, 'message': 'Rejection reason is required'}

        if action == 'return' and not data.get('comment'):
            return {'success': False, 'message': 'Return reason is required'}

        # Check attachments if required by step
        if action == 'approve' and self.current_step:
            if self.current_step.get('require_attachment'):
                attachments = get_all("""
                    SELECT 1 FROM form_submission_attachments
                    WHERE submission_id = ? AND workflow_step_id = ?
                """, (self.submission_id, self.current_step['id']))
                if not attachments:
                    return {'success': False, 'message': 'Attachments are required for approval'}

        return {'success': True}

    def _execute_post_hook(self, action, user_id, data):
        """Execute post-transition hook (notifications, etc.)."""
        # Send notifications
        if action == 'approve':
            # Notify submitter
            create_form_notification(
                submission_id=self.submission_id,
                notification_type='approval',
                title='Form Approved',
                message=f'Your form {self.submission["submission_number"]} has been approved.',
                recipient_id=self.submission['submitted_by']
            )

        elif action == 'reject':
            # Notify submitter
            create_form_notification(
                submission_id=self.submission_id,
                notification_type='rejection',
                title='Form Rejected',
                message=f'Your form {self.submission["submission_number"]} has been rejected.',
                recipient_id=self.submission['submitted_by']
            )

        elif action == 'return':
            # Notify submitter
            create_form_notification(
                submission_id=self.submission_id,
                notification_type='return',
                title='Form Returned',
                message=f'Your form {self.submission["submission_number"]} has been returned for correction.',
                recipient_id=self.submission['submitted_by']
            )


# ============================================================================
# SLA AND ESCALATION ENGINE
# ============================================================================

def check_sla_breaches():
    """Check for SLA breaches and trigger escalations."""
    from datetime import datetime, timedelta

    # Find pending assignments past SLA
    pending = get_all("""
        SELECT fa.*, fs.submission_number, fs.status
        FROM form_assignments fa
        JOIN form_submissions fs ON fa.submission_id = fs.id
        WHERE fa.status = 'pending'
        AND fa.due_date IS NOT NULL
        AND fa.due_date < ?
        AND fa.is_active = 1
    """, (datetime.now().isoformat(),))

    for assignment in pending:
        # Check if already escalated
        existing = get_one("""
            SELECT 1 FROM form_notifications
            WHERE submission_id = ? AND notification_type = 'sla_breach'
            AND created_at > ?
        """, (assignment['submission_id'], assignment['due_date']))

        if not existing:
            # Mark as breached
            with get_db_context() as db:
                db.execute("""
                    UPDATE form_assignments SET status = 'breached'
                    WHERE id = ?
                """, (assignment['id'],))
                db.commit()

            # Notify
            create_form_notification(
                submission_id=assignment['submission_id'],
                notification_type='sla_breach',
                title='SLA Breach',
                message=f'Form {assignment["submission_number"]} has breached its SLA.',
                recipient_id=assignment['assigned_to']
            )

            # Trigger escalation
            escalate_submission(assignment['submission_id'], assignment['assigned_to'])


def escalate_submission(submission_id, from_user_id):
    """Escalate a submission to a higher authority."""
    submission = get_submission(submission_id)
    if not submission:
        return

    workflow = get_template_workflow(submission['template_id'])
    if not workflow:
        return

    steps = get_workflow_steps(workflow['id'])

    # Find escalation step (usually the last step or designated escalation step)
    escalation_step = None
    for step in reversed(steps):
        if step.get('is_escalation'):
            escalation_step = step
            break

    if not escalation_step:
        # Use next step in sequence
        current_order = 0
        if submission.get('current_step_id'):
            current = [s for s in steps if s['id'] == submission['current_step_id']]
            if current:
                current_order = current[0].get('step_order', 0)

        for step in steps:
            if step.get('step_order', 0) > current_order:
                escalation_step = step
                break

    if escalation_step and escalation_step.get('escalation_user_id'):
        # Reassign to escalation user
        with get_db_context() as db:
            db.execute("""
                UPDATE form_assignments SET is_active = 0
                WHERE submission_id = ?
            """, (submission_id,))
            db.commit()

        assign_submission(
            submission_id=submission_id,
            assigned_to=escalation_step['escalation_user_id'],
            assigned_by=from_user_id,
            workflow_step_id=escalation_step['id'],
            priority='high',
            notes=f'Automatically escalated due to SLA breach'
        )

        # Update status
        update_submission_status(submission_id, 'escalated', from_user_id,
                                reason='Escalated due to SLA breach')

        # Notify escalation user
        create_form_notification(
            submission_id=submission_id,
            notification_type='escalation',
            title='Escalated Form',
            message=f'A form has been escalated to you: {submission["submission_number"]}',
            recipient_id=escalation_step['escalation_user_id']
        )


def get_pending_approvers():
    """Get list of users with pending approvals and their counts."""
    pending = get_all("""
        SELECT fa.assigned_to, COUNT(*) as pending_count,
               u.username, u.email
        FROM form_assignments fa
        JOIN users u ON fa.assigned_to = u.id
        WHERE fa.status = 'pending' AND fa.is_active = 1
        GROUP BY fa.assigned_to
    """)
    return pending


def calculate_approval_time(submission_id):
    """Calculate average approval time for a submission."""
    approvals = get_all("""
        SELECT created_at FROM form_approvals
        WHERE submission_id = ?
        ORDER BY created_at ASC
    """, (submission_id,))

    if len(approvals) < 2:
        return None

    # Simplified: just count days between first and last approval
    first = datetime.fromisoformat(approvals[0]['created_at'])
    last = datetime.fromisoformat(approvals[-1]['created_at'])
    delta = last - first

    return delta.total_seconds() / 3600  # hours


# ============================================================================
# CONDITIONAL ROUTING ENGINE
# ============================================================================

def evaluate_routing_condition(condition, submission_id):
    """
    Evaluate a routing condition.
    Conditions are stored as JSON: {"field": "amount", "operator": "gt", "value": 1000}
    """
    import json

    if not condition:
        return True

    try:
        if isinstance(condition, str):
            cond = json.loads(condition)
        else:
            cond = condition
    except:
        return True

    # Get field value
    field = get_one("""
        SELECT ff.field_code, fsv.field_value
        FROM form_fields ff
        JOIN form_submission_values fsv ON ff.id = fsv.field_id
        WHERE ff.field_code = ? AND fsv.submission_id = ?
    """, (cond.get('field'), submission_id))

    if not field:
        return False

    field_value = field['field_value']
    cond_value = cond.get('value')
    operator = cond.get('operator', 'eq')

    # Try numeric comparison
    try:
        field_num = float(field_value)
        cond_num = float(cond_value)

        if operator == 'eq':
            return field_num == cond_num
        elif operator == 'ne':
            return field_num != cond_num
        elif operator == 'gt':
            return field_num > cond_num
        elif operator == 'gte':
            return field_num >= cond_num
        elif operator == 'lt':
            return field_num < cond_num
        elif operator == 'lte':
            return field_num <= cond_num
    except (ValueError, TypeError):
        pass

    # String comparison
    if operator == 'eq':
        return str(field_value).lower() == str(cond_value).lower()
    elif operator == 'ne':
        return str(field_value).lower() != str(cond_value).lower()
    elif operator == 'contains':
        return str(cond_value).lower() in str(field_value).lower()
    elif operator == 'startswith':
        return str(field_value).lower().startswith(str(cond_value).lower())
    elif operator == 'endswith':
        return str(field_value).lower().endswith(str(cond_value).lower())

    return False


def determine_next_step(submission_id, current_step_id, action):
    """
    Determine the next workflow step based on conditions.
    Used for conditional routing.
    """
    submission = get_submission(submission_id)
    if not submission:
        return None

    workflow = get_template_workflow(submission['template_id'])
    if not workflow:
        return None

    transitions = get_workflow_transitions(workflow['id'])

    # Find matching transitions from current step
    matching_transitions = [t for t in transitions if t['from_step_id'] == current_step_id and t['action'] == action]

    for transition in matching_transitions:
        # Check condition
        if transition.get('condition'):
            if evaluate_routing_condition(transition['condition'], submission_id):
                return transition['to_step_id']
        else:
            # Default transition (no condition)
            if transition.get('is_default'):
                return transition['to_step_id']

    return None


# ============================================================================
# DELEGATION ENGINE
# ============================================================================

def delegate_approval(submission_id, from_user_id, to_user_id, reason=None):
    """Delegate approval authority to another user."""
    # Check if delegation is allowed
    submission = get_submission(submission_id)
    if not submission:
        return {'success': False, 'message': 'Submission not found'}

    # Verify from_user has authority
    assignment = get_one("""
        SELECT 1 FROM form_assignments
        WHERE submission_id = ? AND assigned_to = ? AND is_active = 1
    """, (submission_id, from_user_id))

    if not assignment:
        return {'success': False, 'message': 'You are not authorized for this submission'}

    # Deactivate current assignment
    with get_db_context() as db:
        db.execute("""
            UPDATE form_assignments
            SET is_active = 0, reassigned_to = ?, reassigned_at = CURRENT_TIMESTAMP
            WHERE submission_id = ? AND assigned_to = ?
        """, (to_user_id, submission_id, from_user_id))
        db.commit()

    # Create new delegation assignment
    new_assignment_id = assign_submission(
        submission_id=submission_id,
        assigned_to=to_user_id,
        assigned_by=from_user_id,
        workflow_step_id=submission.get('current_step_id'),
        notes=f'Delegated: {reason}' if reason else 'Delegated'
    )

    # Record delegation in approvals
    add_approval(
        submission_id=submission_id,
        workflow_step_id=submission.get('current_step_id'),
        approved_by=from_user_id,
        approval_action='delegate',
        approval_comment=f'Delegated to user {to_user_id}: {reason}' if reason else f'Delegated to user {to_user_id}',
        is_delegated=True,
        delegated_from=from_user_id
    )

    # Notify delegate
    create_form_notification(
        submission_id=submission_id,
        notification_type='delegation',
        title='Form Delegated',
        message=f'You have been delegated to approve form: {submission["submission_number"]}',
        recipient_id=to_user_id
    )

    log_audit('form_delegation', submission_id, 'DELEGATE', from_user_id,
              notes=f'Delegated to user {to_user_id}')

    return {'success': True, 'message': 'Delegation successful'}


def get_delegation_history(submission_id):
    """Get delegation history for a submission."""
    return get_all("""
        SELECT fa.*, u_from.username as from_username, u_to.username as to_username
        FROM form_approvals fa
        LEFT JOIN users u_from ON fa.approved_by = u_from.id
        LEFT JOIN users u_to ON fa.delegated_from = u_to.id
        WHERE fa.submission_id = ? AND fa.is_delegated = 1
        ORDER BY fa.created_at DESC
    """, (submission_id,))


# ============================================================================
# WORKFLOW SUMMARY HELPERS
# ============================================================================

def get_workflow_summary(submission_id):
    """Get a summary of workflow progress for a submission."""
    submission = get_submission(submission_id)
    if not submission:
        return None

    workflow = get_template_workflow(submission['template_id'])
    if not workflow:
        return {'no_workflow': True}

    steps = get_workflow_steps(workflow['id'])
    approvals = get_all("""
        SELECT fa.*, u.username as approver_name
        FROM form_approvals fa
        LEFT JOIN users u ON fa.approved_by = u.id
        WHERE fa.submission_id = ?
        ORDER BY fa.created_at ASC
    """, (submission_id,))

    summary = {
        'workflow_name': workflow['name'],
        'total_steps': len(steps),
        'current_step': submission.get('current_step_id'),
        'completed_steps': [],
        'pending_step': None,
        'approval_history': approvals
    }

    # Determine completed vs pending
    for step in steps:
        step_approvals = [a for a in approvals if a['workflow_step_id'] == step['id']]
        if step_approvals:
            summary['completed_steps'].append({
                'step': step,
                'approvals': step_approvals
            })
        elif summary['pending_step'] is None:
            summary['pending_step'] = step

    return summary


def is_workflow_complete(submission_id):
    """Check if workflow is complete for a submission."""
    submission = get_submission(submission_id)
    if not submission:
        return False

    # If status is final, workflow is complete
    final_statuses = ['approved', 'rejected', 'cancelled', 'closed']
    if submission['status'] in final_statuses:
        return True

    # Check if all required steps have approvals
    workflow = get_template_workflow(submission['template_id'])
    if not workflow:
        return submission['status'] not in ['draft', 'submitted']

    steps = get_workflow_steps(workflow['id'])
    for step in steps:
        if step.get('is_required'):
            has_approval = get_one("""
                SELECT 1 FROM form_approvals
                WHERE submission_id = ? AND workflow_step_id = ?
            """, (submission_id, step['id']))
            if not has_approval:
                return False

    return True
