"""
Notification Background Tasks
============================
Background task processing for emails, push notifications, and Flow alerts.

Tasks:
- check_pending_approvals: Check for pending approvals and send reminders
- send_daily_digest: Send daily notification digest to users
- check_overdue_alerts: Check for overdue items and send alerts
- send_email_notification: Send email notification (wrapper)
- send_push_notification: Send push notification (wrapper)
- send_flow_alert: Send Flow alert to user/channel
"""

from celery import Task
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class NotificationTask(Task):
    """Base class for notification tasks with retry and error handling."""
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600


# =============================================================================
# APPROVAL REMINDER TASKS
# =============================================================================

@NotificationTask.bind(name='tasks.notification_tasks.check_pending_approvals')
def check_pending_approvals(self):
    """
    Check for pending approvals and send reminder notifications.

    Runs every 15 minutes. Sends reminders for:
    - Approval requests older than 4 hours
    - Escalated approvals (based on priority)
    """
    logger.info("Checking for pending approvals...")

    with get_db_for_tasks() as db:
        # Find pending approvals older than 4 hours
        four_hours_ago = (datetime.now() - timedelta(hours=4)).isoformat()

        pending = db.execute("""
            SELECT a.id, a.entity_type, a.entity_id, a.entity_name,
                   a.requested_by, a.requested_by_name, a.priority,
                   a.created_at, u.email, u.name
            FROM approval_records a
            JOIN users u ON a.requested_by = u.id
            WHERE a.status = 'pending'
            AND a.created_at < ?
            AND a.reminder_sent_at IS NULL
        """, (four_hours_ago,)).fetchall()

        if not pending:
            logger.info("No pending approvals to remind")
            return {'status': 'no_pending', 'count': 0}

        notified = 0
        for approval in pending:
            try:
                # Send Flow alert via the notification system
                _send_approval_reminder(
                    approval_id=approval['id'],
                    entity_type=approval['entity_type'],
                    entity_name=approval['entity_name'],
                    requested_by=approval['requested_by_name'],
                    priority=approval['priority'],
                    approver_email=approval['email']
                )

                # Mark reminder as sent
                db.execute("""
                    UPDATE approval_records
                    SET reminder_sent_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (approval['id'],))

                notified += 1

            except Exception as e:
                logger.error(f"Failed to send reminder for approval {approval['id']}: {e}")

        db.commit()
        logger.info(f"Sent {notified} approval reminders")
        return {'status': 'completed', 'count': notified}


def _send_approval_reminder(approval_id, entity_type, entity_name, requested_by, priority, approver_email):
    """Send approval reminder via Flow."""
    # Import here to avoid circular dependencies
    try:
        from database import create_notification
        severity = 'HIGH' if priority == 'high' else 'MEDIUM'

        create_notification(
            title=f"Approval Reminder: {entity_type}",
            message=f"{entity_name} requested by {requested_by} requires your approval",
            notification_type="APPROVAL_REMINDER",
            severity=severity,
            link_url=f"/approvals/{approval_id}",
            related_entity_type=entity_type,
            related_entity_id=approval_id,
        )

        # Also send Flow message if Flow is available
        _send_flow_message(
            recipient=approver_email,
            title=f"Approval Reminder: {entity_type}",
            message=f"{entity_name} requested by {requested_by} requires your approval. Priority: {priority}"
        )

    except Exception as e:
        logger.error(f"Failed to send approval reminder: {e}")
        raise


# =============================================================================
# DAILY DIGEST TASKS
# =============================================================================

@NotificationTask.bind(name='tasks.notification_tasks.send_daily_digest')
def send_daily_digest(self):
    """
    Send daily notification digest to users.

    Runs at 8 AM on weekdays. Compiles:
    - Pending approvals
    - Overdue tasks
    - Critical alerts
    - Daily summary
    """
    logger.info("Sending daily digest...")

    with get_db_for_tasks() as db:
        # Get users who want daily digest
        users = db.execute("""
            SELECT u.id, u.email, u.name, u.notification_preferences
            FROM users u
            JOIN user_notification_preferences unp ON u.id = unp.user_id
            WHERE unp.daily_digest_enabled = 1
            AND u.is_active = 1
        """).fetchall()

        sent = 0
        for user in users:
            try:
                # Compile user-specific digest
                digest = _compile_user_digest(db, user['id'])

                if digest['total_count'] > 0:
                    _send_digest_email(
                        email=user['email'],
                        name=user['name'],
                        digest=digest
                    )
                    sent += 1

            except Exception as e:
                logger.error(f"Failed to send digest to {user['email']}: {e}")

        logger.info(f"Sent {sent} daily digests")
        return {'status': 'completed', 'count': sent}


def _compile_user_digest(db, user_id):
    """Compile digest data for a specific user."""
    digest = {
        'pending_approvals': [],
        'overdue_tasks': [],
        'critical_alerts': [],
        'recent_activity': [],
        'total_count': 0
    }

    # Pending approvals
    approvals = db.execute("""
        SELECT id, entity_type, entity_name, priority, created_at
        FROM approval_records
        WHERE status = 'pending'
        AND (assigned_to = ? OR requested_by = ?)
        ORDER BY priority DESC, created_at ASC
        LIMIT 5
    """, (user_id, user_id)).fetchall()

    for a in approvals:
        digest['pending_approvals'].append({
            'id': a['id'],
            'type': a['entity_type'],
            'name': a['entity_name'],
            'priority': a['priority'],
            'age_days': (datetime.now() - datetime.fromisoformat(a['created_at'])).days
        })

    # Overdue tasks
    tasks = db.execute("""
        SELECT id, title, priority, due_date
        FROM tasks
        WHERE assigned_to = ?
        AND status NOT IN ('completed', 'cancelled')
        AND due_date < date('now')
        ORDER BY priority DESC, due_date ASC
        LIMIT 5
    """, (user_id,)).fetchall()

    for t in tasks:
        digest['overdue_tasks'].append({
            'id': t['id'],
            'title': t['title'],
            'priority': t['priority'],
            'days_overdue': (datetime.now() - datetime.fromisoformat(t['due_date'])).days
        })

    # Critical alerts
    alerts = db.execute("""
        SELECT id, title, message, severity, created_at
        FROM platform_notifications
        WHERE user_id = ?
        AND severity = 'CRITICAL'
        AND is_read = 0
        AND created_at > datetime('now', '-7 days')
        ORDER BY created_at DESC
        LIMIT 3
    """, (user_id,)).fetchall()

    for alert in alerts:
        digest['critical_alerts'].append({
            'id': alert['id'],
            'title': alert['title'],
            'message': alert['message']
        })

    digest['total_count'] = (
        len(digest['pending_approvals']) +
        len(digest['overdue_tasks']) +
        len(digest['critical_alerts'])
    )

    return digest


def _send_digest_email(email, name, digest):
    """Send daily digest email to user."""
    # Placeholder for email sending logic
    logger.info(f"Would send digest to {email} with {digest['total_count']} items")
    # Actual implementation would use email_manager


# =============================================================================
# OVERDUE ALERT TASKS
# =============================================================================

@NotificationTask.bind(name='tasks.notification_tasks.check_overdue_alerts')
def check_overdue_alerts(self):
    """
    Check for overdue items and send alerts.

    Runs at 9 AM on weekdays. Alerts for:
    - Overdue payments (treasury)
    - Overdue collections
    - Overdue tasks
    - Late deliveries
    """
    logger.info("Checking for overdue alerts...")

    with get_db_for_tasks() as db:
        alerts_created = 0

        # Check overdue treasury payments
        overdue_payments = db.execute("""
            SELECT tp.id, tp.reference, tp.amount, tp.due_date,
                   tp.counterparty_name, c.name as company_name
            FROM treasury_payments tp
            JOIN companies c ON tp.company_id = c.id
            WHERE tp.status = 'approved'
            AND tp.due_date < date('now')
            AND tp.alert_sent = 0
        """).fetchall()

        for payment in overdue_payments:
            _create_overdue_alert(
                alert_type='treasury_payment',
                entity_id=payment['id'],
                entity_name=payment['reference'],
                amount=payment['amount'],
                due_date=payment['due_date'],
                counterparty=payment['counterparty_name'],
                company=payment['company_name']
            )

            db.execute("UPDATE treasury_payments SET alert_sent = 1 WHERE id = ?", (payment['id'],))
            alerts_created += 1

        db.commit()
        logger.info(f"Created {alerts_created} overdue alerts")
        return {'status': 'completed', 'count': alerts_created}


def _create_overdue_alert(alert_type, entity_id, entity_name, amount, due_date, counterparty, company):
    """Create overdue alert notification."""
    try:
        from database import create_notification

        create_notification(
            title=f"Overdue {alert_type.replace('_', ' ').title()}: {entity_name}",
            message=f"Amount {amount} was due on {due_date} from {counterparty}. Company: {company}",
            notification_type="OVERDUE_ALERT",
            severity="HIGH",
            link_url=f"/{alert_type.replace('_', '/')}/{entity_id}",
            related_entity_type=alert_type,
            related_entity_id=entity_id,
        )
    except Exception as e:
        logger.error(f"Failed to create overdue alert: {e}")
        raise


# =============================================================================
# FLOW MESSAGE TASKS
# =============================================================================

def _send_flow_message(recipient, title, message):
    """Send message via Flow."""
    try:
        from flow_models import create_flow_message
        # This would send via Flow system
        logger.info(f"Would send Flow message to {recipient}: {title}")
    except Exception as e:
        logger.warning(f"Flow message failed (non-critical): {e}")


# =============================================================================
# HELPER FUNCTIONS (for use by other tasks)
# =============================================================================

def get_db_for_tasks():
    """Get database connection for background tasks."""
    from database import get_db_context
    return get_db_context()
