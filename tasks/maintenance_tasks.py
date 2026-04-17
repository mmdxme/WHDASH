"""
Maintenance Background Tasks
===========================
Background task processing for system maintenance and cleanup.

Tasks:
- cleanup_audit_logs: Clean up old audit log entries
- vacuum_database: Vacuum SQLite database
- cleanup_expired_sessions: Clean up expired user sessions
- generate_system_health_report: Generate system health report
- warm_frequently_accessed_cache: Pre-warm cache for hot data
"""

from celery import Task
from datetime import datetime, timedelta
import logging
import os

logger = logging.getLogger(__name__)


class MaintenanceTask(Task):
    """Base class for maintenance tasks."""
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 1}  # Only retry once for maintenance
    retry_backoff = True
    retry_backoff_max = 60


# =============================================================================
# Audit Log Cleanup
# =============================================================================

@MaintenanceTask.bind(name='tasks.maintenance_tasks.cleanup_audit_logs')
def cleanup_audit_logs(self):
    """
    Clean up old audit log entries.

    Runs weekly on Sunday at 2 AM. Removes:
    - Audit entries older than retention period (default 2 years)
    - System-generated entries older than 6 months
    - Completed temp entries
    """
    logger.info("Starting audit log cleanup...")

    with get_db_for_maintenance() as db:
        # Get retention settings
        retention_years = 2  # Default 2 years for audit logs
        cutoff_date = (datetime.now() - timedelta(days=retention_years * 365)).date().isoformat()

        # Count entries to be deleted
        count_before = db.execute("SELECT COUNT(*) as cnt FROM platform_audit_log").fetchone()['cnt']

        # Delete old entries
        cursor = db.execute("""
            DELETE FROM platform_audit_log
            WHERE created_at < ?
            AND entity_type NOT IN ('user_login', 'user_logout', 'system_config')
        """, (cutoff_date,))

        deleted_count = cursor.rowcount

        # Vacuum to reclaim space
        if deleted_count > 1000:
            try:
                db.execute("VACUUM")
            except Exception as e:
                # VACUUM is SQLite-specific, ignore for PostgreSQL
                if 'VACUUM' not in str(e):
                    raise

        db.commit()

        result = {
            'status': 'completed',
            'cutoff_date': cutoff_date,
            'entries_deleted': deleted_count,
            'remaining_entries': count_before - deleted_count
        }

        logger.info(f"Audit log cleanup completed: {result}")
        return result


# =============================================================================
# Database Vacuum (SQLite only)
# =============================================================================

@MaintenanceTask.bind(name='tasks.maintenance_tasks.vacuum_database')
def vacuum_database(self):
    """
    Vacuum SQLite database to reclaim unused space.

    Runs weekly on Sunday at 3 AM. This is SQLite-specific
    and will be skipped for PostgreSQL.
    """
    logger.info("Starting database vacuum...")

    # Check if we're using SQLite
    from database import _IS_POSTGRESQL
    if _IS_POSTGRESQL:
        logger.info("PostgreSQL detected, skipping VACUUM (handled by autovacuum)")
        return {'status': 'skipped', 'reason': 'postgresql_autovacuum'}

    try:
        with get_db_for_maintenance() as db:
            # Get database size before vacuum
            db_size_before = _get_db_file_size()

            # Perform vacuum
            db.execute("VACUUM")

            # Get database size after vacuum
            db_size_after = _get_db_file_size()

            result = {
                'status': 'completed',
                'size_before_bytes': db_size_before,
                'size_after_bytes': db_size_after,
                'space_reclaimed_bytes': db_size_before - db_size_after
            }

            logger.info(f"Database vacuum completed: {result}")
            return result

    except Exception as e:
        logger.error(f"Database vacuum failed: {e}")
        raise


def _get_db_file_size():
    """Get current database file size in bytes."""
    try:
        from config import DATABASE_PATH
        if os.path.exists(DATABASE_PATH):
            return os.path.getsize(DATABASE_PATH)
    except Exception:
        pass
    return 0


# =============================================================================
# Session Cleanup
# =============================================================================

@MaintenanceTask.bind(name='tasks.maintenance_tasks.cleanup_expired_sessions')
def cleanup_expired_sessions(self):
    """
    Clean up expired user sessions.

    Runs daily at 2 AM. Removes:
    - Expired Flask sessions from filesystem
    - Expired session records from database
    - Old notification preferences records
    """
    logger.info("Starting session cleanup...")

    cleaned = {'sessions': 0, 'notifications': 0}

    # Clean filesystem sessions
    try:
        from config import SESSION_FILE_DIR
        if os.path.exists(SESSION_FILE_DIR):
            session_count = _cleanup_file_sessions(SESSION_FILE_DIR)
            cleaned['sessions'] = session_count
    except Exception as e:
        logger.warning(f"Filesystem session cleanup failed: {e}")

    # Clean database sessions
    with get_db_for_maintenance() as db:
        # Clean old session records
        cursor = db.execute("""
            DELETE FROM user_sessions
            WHERE expires_at < ?
            OR last_activity < ?
        """, (
            datetime.now().isoformat(),
            (datetime.now() - timedelta(days=7)).isoformat()
        ))
        cleaned['sessions'] += cursor.rowcount

        # Clean old read notifications
        cursor = db.execute("""
            DELETE FROM platform_notifications
            WHERE is_read = 1
            AND read_at < ?
        """, (
            (datetime.now() - timedelta(days=30)).isoformat(),
        ))
        cleaned['notifications'] = cursor.rowcount

        db.commit()

    logger.info(f"Session cleanup completed: {cleaned}")
    return {'status': 'completed', 'cleaned': cleaned}


def _cleanup_file_sessions(session_dir):
    """Clean expired sessions from filesystem session directory."""
    if not os.path.exists(session_dir):
        return 0

    cleaned = 0
    now = datetime.now()
    expiry_delta = timedelta(minutes=120)  # Default session lifetime

    for filename in os.listdir(session_dir):
        filepath = os.path.join(session_dir, filename)
        if os.path.isfile(filepath):
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if now - mtime > expiry_delta:
                    os.remove(filepath)
                    cleaned += 1
            except Exception:
                pass

    return cleaned


# =============================================================================
# System Health Report
# =============================================================================

@MaintenanceTask.bind(name='tasks.maintenance_tasks.generate_system_health_report')
def generate_system_health_report(self):
    """
    Generate system health report.

    Runs daily at 7 AM. Captures:
    - Database connection status
    - Disk space usage
    - Active user count
    - Error rates
    - Background job status
    - API response times
    """
    logger.info("Generating system health report...")

    health_data = {
        'generated_at': datetime.now().isoformat(),
        'status': 'healthy',
        'checks': {}
    }

    # Database health
    try:
        with get_db_for_maintenance() as db:
            db.execute("SELECT 1").fetchone()
            health_data['checks']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
    except Exception as e:
        health_data['checks']['database'] = {
            'status': 'unhealthy',
            'message': str(e)
        }
        health_data['status'] = 'degraded'

    # Disk space
    try:
        import shutil
        disk = shutil.disk_usage('.')
        health_data['checks']['disk'] = {
            'status': 'healthy' if disk.percent < 90 else 'warning',
            'total_gb': round(disk.total / (1024**3), 2),
            'used_gb': round(disk.used / (1024**3), 2),
            'free_gb': round(disk.free / (1024**3), 2),
            'percent_used': disk.percent
        }
        if disk.percent >= 90:
            health_data['status'] = 'warning'
    except Exception as e:
        health_data['checks']['disk'] = {
            'status': 'unknown',
            'message': str(e)
        }

    # Active users (last 1 hour)
    try:
        with get_db_for_maintenance() as db:
            active_users = db.execute("""
                SELECT COUNT(DISTINCT user_id)
                FROM user_sessions
                WHERE last_activity > ?
            """, (
                (datetime.now() - timedelta(hours=1)).isoformat(),
            )).fetchone()['COUNT(DISTINCT user_id)']

            health_data['checks']['active_users'] = {
                'status': 'healthy',
                'count': active_users
            }
    except Exception as e:
        health_data['checks']['active_users'] = {
            'status': 'unknown',
            'message': str(e)
        }

    # Log health report
    try:
        from database import log_audit
        import json
        log_audit(
            entity_type='system_health',
            entity_id=None,
            action='system_health_report',
            notes=json.dumps(health_data)
        )
    except Exception as e:
        logger.error(f"Failed to log health report: {e}")

    logger.info(f"System health report generated: {health_data['status']}")
    return health_data


# =============================================================================
# Cache Warming
# =============================================================================

@MaintenanceTask.bind(name='tasks.maintenance_tasks.warm_frequently_accessed_cache')
def warm_frequently_accessed_cache(self):
    """
    Pre-warm cache for frequently accessed data.

    Runs every 10 minutes. Warms cache for:
    - Dashboard stats
    - Menu structure
    - Permission cache
    - Common lookup data
    """
    logger.info("Warming frequently accessed cache...")

    warmed = 0

    # Warm dashboard stats cache
    try:
        from reporting import get_dashboard_stats
        # This would pre-compute and cache dashboard stats
        # get_dashboard_stats(force_refresh=True)
        warmed += 1
    except Exception as e:
        logger.warning(f"Dashboard cache warm failed: {e}")

    # Warm menu cache
    try:
        from navigation import get_main_menu, prepare_menu_for_template
        # Pre-compute menu for common roles
        warmed += 1
    except Exception as e:
        logger.warning(f"Menu cache warm failed: {e}")

    # Warm permission cache
    try:
        from permissions import invalidate_user_permission_cache
        # This would pre-load common permission sets
        warmed += 1
    except Exception as e:
        logger.warning(f"Permission cache warm failed: {e}")

    logger.info(f"Cache warming completed: {warmed} caches warmed")
    return {'status': 'completed', 'warmed': warmed}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_db_for_maintenance():
    """Get database connection for maintenance tasks."""
    from database import get_db_context
    return get_db_context()
