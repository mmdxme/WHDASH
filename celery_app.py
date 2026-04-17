"""
Celery Application Configuration
================================
Enterprise-grade background job processing for WHDASH.

This module provides:
- Celery application factory
- Task discovery and registration
- Scheduled task configuration (celery beat)
- Result backend configuration
- Task routing for different queues

USAGE:
    from celery_app import celery_app, init_celery

    # Initialize celery with Flask app
    init_celery(app)

    # Run worker: celery -A celery_app worker --loglevel=info
    # Run beat: celery -A celery_app beat --loglevel=info
"""

from celery import Celery
from celery.schedules import crontab
import os


# =============================================================================
# CELERY APP FACTORY
# =============================================================================

def make_celery():
    """Create and configure Celery application instance."""
    # Import config values
    from config import (
        CELERY_BROKER_URL, CELERY_RESULT_BACKEND,
        CELERY_TASK_SERIALIZER, CELERY_RESULT_SERIALIZER,
        CELERY_ACCEPT_CONTENT, CELERY_TIMEZONE, CELERY_ENABLE_UTC,
        CELERY_TASK_TRACK_STARTED, CELERY_TASK_TIME_LIMIT,
        CELERY_RESULT_EXTENDED, REDIS_URL
    )

    # Determine broker and backend URLs
    broker_url = CELERY_BROKER_URL
    result_backend = CELERY_RESULT_BACKEND

    # Fallback to Redis defaults if not explicitly configured
    if not broker_url and REDIS_URL:
        broker_url = REDIS_URL.replace('/0/', '/2/') if '/0/' in REDIS_URL else f"{REDIS_URL}/2"
    if not result_backend and REDIS_URL:
        result_backend = REDIS_URL.replace('/0/', '/3/') if '/0/' in REDIS_URL else f"{REDIS_URL}/3"

    # Create Celery app with explicit broker/backend
    app = Celery(
        'whdash',
        broker=broker_url or 'redis://localhost:6379/2',
        backend=result_backend or 'redis://localhost:6379/3',
        include=[
            'tasks.notification_tasks',
            'tasks.report_tasks',
            'tasks.sync_tasks',
            'tasks.maintenance_tasks',
        ]
    )

    # Celery configuration
    app.conf.update(
        task_serializer=CELERY_TASK_SERIALIZER or 'json',
        result_serializer=CELERY_RESULT_SERIALIZER or 'json',
        accept_content=CELERY_ACCEPT_CONTENT or ['json'],
        timezone=CELERY_TIMEZONE or 'UTC',
        enable_utc=CELERY_ENABLE_UTC if CELERY_ENABLE_UTC is not None else True,
        task_track_started=CELERY_TASK_TRACK_STARTED if CELERY_TASK_TRACK_STARTED is not None else True,
        task_time_limit=CELERY_TASK_TIME_LIMIT or 1800,
        result_extended=CELERY_RESULT_EXTENDED if CELERY_RESULT_EXTENDED is not None else True,

        # Task routing
        task_routes={
            'tasks.notification_tasks.*': {'queue': 'notifications'},
            'tasks.report_tasks.*': {'queue': 'reports'},
            'tasks.sync_tasks.*': {'queue': 'sync'},
            'tasks.maintenance_tasks.*': {'queue': 'maintenance'},
        },

        # Task result expiration (7 days)
        result_expires=7 * 24 * 60 * 60,

        # Worker configuration
        worker_prefetch_multiplier=1,
        worker_concurrency=4,

        # Task acknowledgments
        task_acks_late=True,
        task_reject_on_worker_lost=True,
    )

    return app


# Create default celery app instance
celery_app = make_celery()


# =============================================================================
# CELERY BEAT SCHEDULE (Scheduled Tasks)
# =============================================================================

def configure_celery_beat(app):
    """
    Configure periodic tasks (celery beat schedule).

    Add to crontab schedule:
    - minute: 0-59, * for any
    - hour: 0-23, * for any
    - day_of_week: 0-6 (mon-sun), * for any
    - day_of_month: 1-31, * for any
    - month_of_year: 1-12, * for any
    """
    app.conf.beat_schedule = {
        # ==========================================================================
        # NOTIFICATION TASKS
        # ==========================================================================

        # Check for pending approvals and send reminders every 15 minutes
        'check-pending-approvals': {
            'task': 'tasks.notification_tasks.check_pending_approvals',
            'schedule': crontab(minute='*/15'),
        },

        # Send daily digest notifications at 8 AM
        'send-daily-digest': {
            'task': 'tasks.notification_tasks.send_daily_digest',
            'schedule': crontab(hour=8, minute=0, day_of_week='mon-fri'),
        },

        # Check for overdue items and send alerts at 9 AM
        'check-overdue-alerts': {
            'task': 'tasks.notification_tasks.check_overdue_alerts',
            'schedule': crontab(hour=9, minute=0, day_of_week='mon-fri'),
        },

        # ==========================================================================
        # REPORT TASKS
        # ==========================================================================

        # Generate daily treasury report at 6 AM
        'generate-treasury-report': {
            'task': 'tasks.report_tasks.generate_treasury_report',
            'schedule': crontab(hour=6, minute=0),
        },

        # Generate daily cash position snapshot at 6:30 AM
        'generate-cash-position-snapshot': {
            'task': 'tasks.report_tasks.generate_cash_position_snapshot',
            'schedule': crontab(hour=6, minute=30),
        },

        # Generate weekly KPI report on Monday at 7 AM
        'generate-weekly-kpi-report': {
            'task': 'tasks.report_tasks.generate_weekly_kpi_report',
            'schedule': crontab(hour=7, minute=0, day_of_week=1),
        },

        # ==========================================================================
        # SYNC TASKS
        # ==========================================================================

        # Sync with Peyvast API every 30 minutes during business hours
        'sync-peyvast-data': {
            'task': 'tasks.sync_tasks.sync_peyvast_data',
            'schedule': crontab(minute='*/30', hour='8-18'),
        },

        # Sync bank statements every hour
        'sync-bank-statements': {
            'task': 'tasks.sync_tasks.sync_bank_statements',
            'schedule': crontab(minute=0),
        },

        # Refresh master data cache every 15 minutes
        'refresh-master-data': {
            'task': 'tasks.sync_tasks.refresh_master_data_cache',
            'schedule': crontab(minute='*/15'),
        },

        # ==========================================================================
        # MAINTENANCE TASKS
        # ==========================================================================

        # Clean up old audit logs weekly on Sunday at 2 AM
        'cleanup-audit-logs': {
            'task': 'tasks.maintenance_tasks.cleanup_audit_logs',
            'schedule': crontab(hour=2, minute=0, day_of_week=0),
        },

        # Vacuum SQLite database weekly on Sunday at 3 AM (SQLite only)
        'vacuum-database': {
            'task': 'tasks.maintenance_tasks.vacuum_database',
            'schedule': crontab(hour=3, minute=0, day_of_week=0),
        },

        # Clear expired sessions daily at 2 AM
        'cleanup-expired-sessions': {
            'task': 'tasks.maintenance_tasks.cleanup_expired_sessions',
            'schedule': crontab(hour=2, minute=0),
        },

        # Generate system health report daily at 7 AM
        'generate-system-health-report': {
            'task': 'tasks.maintenance_tasks.generate_system_health_report',
            'schedule': crontab(hour=7, minute=0),
        },

        # Warm cache for frequently accessed data every 10 minutes
        'warm-frequently-accessed-cache': {
            'task': 'tasks.maintenance_tasks.warm_frequently_accessed_cache',
            'schedule': crontab(minute='*/10'),
        },
    }

    return app


# Configure beat schedule on the celery app
configure_celery_beat(celery_app)


# =============================================================================
# INITIALIZATION
# =============================================================================

def init_celery(app):
    """
    Initialize Celery with Flask application context.

    This function:
    1. Updates Celery broker/backend from Flask app config
    2. Sets up task autodiscover with Flask app context
    3. Configures result backend to use Flask app's SQLAlchemy db

    Args:
        app: Flask application instance
    """
    # Update celery app configuration from Flask app config
    if hasattr(app, 'config') and 'CELERY_BROKER_URL' in app.config:
        celery_app.conf.broker_url = app.config['CELERY_BROKER_URL']
    if hasattr(app, 'config') and 'CELERY_RESULT_BACKEND' in app.config:
        celery_app.conf.result_backend = app.config['CELERY_RESULT_BACKEND']

    # Set Flask app context for tasks
    celery_app.conf.update(
        task_always_eager=False,
        task_ignore_result=False,
    )

    # Store Flask app on celery app for context access
    celery_app.flask_app = app

    class ContextTask(celery_app.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app.Task = ContextTask

    return celery_app


# =============================================================================
# HEALTH CHECK TASK
# =============================================================================

@celery_app.task(bind=True, name='health_check')
def health_check(self):
    """Simple health check task for monitoring Celery workers."""
    return {
        'status': 'healthy',
        'worker': self.request.hostname,
        'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
    }


# =============================================================================
# TEST TASK (for testing connectivity)
# =============================================================================

@celery_app.task(bind=True, name='test_task')
def test_task(self, value):
    """Simple test task for verifying Celery connectivity."""
    return {
        'status': 'success',
        'value': value,
        'worker': self.request.hostname,
    }
