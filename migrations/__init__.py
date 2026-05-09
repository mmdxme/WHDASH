# Migrations Package
#
# Public API:
#   from migrations import ensure_db_current, stamp_baseline_if_needed, get_migration_status
#
# These are lazy imports to avoid triggering config.py SECRET_KEY check
# at import time (config.py requires SECRET_KEY in production mode).

def __getattr__(name):
    if name == 'ensure_db_current':
        from migrations.migrate_app import ensure_db_current
        return ensure_db_current
    elif name == 'stamp_baseline_if_needed':
        from migrations.migrate_app import stamp_baseline_if_needed
        return stamp_baseline_if_needed
    elif name == 'get_migration_status':
        from migrations.migrate_app import get_migration_status
        return get_migration_status
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")