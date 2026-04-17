"""
WHDASH Background Tasks Package
============================
Enterprise-grade background task processing.

This package contains:
- notification_tasks: Email, push, and Flow notifications
- report_tasks: Scheduled report generation
- sync_tasks: Data synchronization with external systems
- maintenance_tasks: System cleanup and cache management

Each task type has its own queue for isolation and priority handling.
"""

from celery import Task
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BaseTask(Task):
    """
    Base task class with common functionality.

    Provides:
    - Automatic logging
    - Error handling with retry
    - Progress tracking
    - Context awareness
    """

    # Number of retries on failure
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handle task failure."""
        logger.error(f"Task {self.name} (ID: {task_id}) failed: {exc}")
        super().on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Handle task retry."""
        logger.warning(f"Task {self.name} (ID: {task_id}) retrying after failure: {exc}")
        super().on_retry(exc, task_id, args, kwargs, einfo)

    def on_success(self, retval, task_id, args, kwargs):
        """Handle task success."""
        logger.info(f"Task {self.name} (ID: {task_id}) completed successfully")
        super().on_success(retval, task_id, args, kwargs)


def get_db_for_tasks():
    """Get database connection for background tasks."""
    from database import get_db_context
    return get_db_context()


def log_task_audit(task_name, action, entity_type=None, entity_id=None, details=None):
    """Log task execution to audit trail."""
    try:
        from database import log_audit
        log_audit(
            entity_type=entity_type or 'background_task',
            entity_id=entity_id,
            action=action,
            notes=f"Task: {task_name} | Details: {details}" if details else f"Task: {task_name}",
        )
    except Exception as e:
        logger.error(f"Failed to log task audit: {e}")


# Import subtasks to make them available
from tasks.notification_tasks import *
from tasks.report_tasks import *
from tasks.sync_tasks import *
from tasks.maintenance_tasks import *
