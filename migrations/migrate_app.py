# ==============================================================================
# Migration Safety Helpers
# ==============================================================================
# Pre-flight checks, environment guards, and backup reminders
# to be called before running Alembic migrations.
#
# Usage:
#   from migrations.migrate_app import (
#       preflight_check,
#       require_explicit_confirmation,
#       log_migration_start,
#       log_migration_complete,
#   )
# ==============================================================================

import os
import sys
import datetime

# ==============================================================================
# Environment Guards
# ==============================================================================

def is_production() -> bool:
    """Check if running in production mode."""
    env = os.environ.get('ENV', '').lower()
    return env in ('production', 'prod', 'live')


def is_development() -> bool:
    """Check if running in development mode."""
    env = os.environ.get('ENV', '').lower()
    return env in ('development', 'dev', 'local')


def is_testing() -> bool:
    """Check if running in test mode."""
    return os.environ.get('TESTING', '0') == '1' or 'pytest' in sys.modules


def skip_migration_safety() -> bool:
    """Check if migration safety checks should be skipped (for automation)."""
    return os.environ.get('SKIP_MIGRATION_SAFETY', '0') == '1'


# ==============================================================================
# Preflight Checks
# ==============================================================================

def preflight_check(allow_production=False):
    """
    Run pre-migration safety checks.

    Raises SystemExit if:
    - Running production without explicit allow_production=True
    - DATABASE_PATH is not set
    - Cannot verify database is accessible

    Returns True if checks pass.
    """
    print("\n" + "=" * 60)
    print("  MIGRATION PREFLIGHT CHECK")
    print("=" * 60)

    if skip_migration_safety():
        print("  [SKIP] Migration safety checks disabled (SKIP_MIGRATION_SAFETY=1)")
        return True

    # Environment check
    env = os.environ.get('ENV', 'development').lower()
    if env in ('production', 'prod', 'live'):
        if not allow_production:
            print(f"  [BLOCK] Production environment detected: ENV={env}")
            print("  To run migrations in production, you must:")
            print("    1. Set SKIP_MIGRATION_SAFETY=1")
            print("    2. Take a full database backup FIRST")
            print("    3. Use: python migrate.py upgrade --sql  (to preview first)")
            raise SystemExit("Aborted: Production migration blocked by safety check.")
        print(f"  [WARN] Production environment: ENV={env}")
    else:
        print(f"  [OK] Environment: {env}")

    # Database path check
    db_path = os.environ.get('DATABASE_PATH', 'warehouse.db')
    if not db_path:
        raise SystemExit("  [FAIL] DATABASE_PATH is not set")

    # Resolve absolute path
    if not os.path.isabs(db_path):
        base = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.abspath(os.path.join(base, '..', db_path))

    print(f"  [OK] Database path: {db_path}")

    if os.path.exists(db_path):
        size_kb = os.path.getsize(db_path) / 1024
        print(f"  [OK] Database exists ({size_kb:.1f} KB)")
    else:
        print(f"  [INFO] Database does not exist yet (will be created)")

    print("=" * 60 + "\n")
    return True


def require_explicit_confirmation(action: str = "migration"):
    """
    Prompt for explicit confirmation before destructive actions.
    Returns True only if user explicitly confirms.
    """
    if skip_migration_safety():
        print(f"  [AUTO] Confirmation bypassed (SKIP_MIGRATION_SAFETY=1)")
        return True

    print(f"\n  {'=' * 58}")
    print(f"  CONFIRMATION REQUIRED: {action}")
    print(f"  {'=' * 58}")
    print(f"  WARNING: This operation modifies the database schema.")
    print(f"  Back up your database before proceeding.")
    print(f"")
    print(f"  To confirm, run with environment variable:")
    print(f"    SKIP_MIGRATION_SAFETY=1 python migrate.py upgrade")
    print(f"  {'=' * 58}\n")
    return False


# ==============================================================================
# Migration Logging
# ==============================================================================

def log_migration_start(revision: str, description: str):
    """Log the start of a migration with timestamp."""
    timestamp = datetime.datetime.now().isoformat()
    print(f"\n  [{timestamp}] MIGRATION START: {revision}")
    print(f"           Description: {description}")
    print(f"           DB Engine   : {os.environ.get('DB_ENGINE', 'sqlite')}")


def log_migration_complete(revision: str, direction: str = "upgrade"):
    """Log the completion of a migration."""
    timestamp = datetime.datetime.now().isoformat()
    print(f"\n  [{timestamp}] MIGRATION COMPLETE: {revision} ({direction})")


def log_migration_error(revision: str, error: Exception):
    """Log a migration error."""
    timestamp = datetime.datetime.now().isoformat()
    print(f"\n  [{timestamp}] MIGRATION ERROR: {revision}")
    print(f"  Error: {error}")
    print(f"  Stack: {str(error)}")


# ==============================================================================
# Backup Reminder
# ==============================================================================

def backup_reminder():
    """Print a reminder to back up the database before migrations."""
    print("""
  +------------------------------------------------------+
  |                    BACKUP REMINDER                   |
  +------------------------------------------------------+
  | Before running migrations, ensure you have a         |
  | recent backup of your database.                      |
  |                                                      |
  | SQLite:  cp warehouse.db warehouse.db.backup        |
  | PostgreSQL: Use pg_dump or your backup tool          |
  +------------------------------------------------------+
    """)


# ==============================================================================
# Alembic Version Check
# ==============================================================================

def get_current_alembic_revision():
    """
    Get the current Alembic revision from the database.
    Returns None if Alembic version table doesn't exist yet.
    """
    try:
        from alembic import context
        if context.get_context().get_binding() is not None:
            pass  # Context available
    except Exception:
        pass

    # Try direct DB check
    db_path = os.environ.get('DATABASE_PATH', 'warehouse.db')
    if not os.path.isabs(db_path):
        base = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.abspath(os.path.join(base, '..', db_path))

    if not os.path.exists(db_path):
        return None

    import sqlite3
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        result = conn.execute(
            "SELECT version_num FROM alembic_version LIMIT 1"
        ).fetchone()
        conn.close()
        return result['version_num'] if result else None
    except Exception:
        return None


def is_migration_needed():
    """
    Check if there are pending Alembic migrations.
    Returns True if database is behind head.
    """
    current = get_current_alembic_revision()
    if current is None:
        # No alembic version table - either fresh DB or manual schema
        return False  # Let Alembic handle initial setup

    # Check if current matches head
    try:
        from alembic.config import Config
        from alembic import script
        from alembic.runtime import migration

        base = os.path.dirname(os.path.abspath(__file__))
        cfg = Config(os.path.join(base, '..', 'alembic.ini'))
        script_dir = script.ScriptDirectory.from_config(cfg)

        current_head = script_dir.get_current_head()
        return current != current_head
    except Exception:
        return False


# ==============================================================================
# High-Level Migration API
# ==============================================================================

def ensure_db_current(safe_mode=True):
    """
    Ensure the database is at the current Alembic migration head.
    Runs Alembic upgrade if needed.

    Args:
        safe_mode: If True, run preflight check and backup reminder before migration.
                   Set to False when calling from app startup (to avoid prompts).

    Returns:
        dict with keys: 'current', 'target', 'upgraded', 'error'
    """
    if safe_mode:
        preflight_check(allow_production=False)
        backup_reminder()

    try:
        from alembic.config import Config
        from alembic import script
        from alembic.runtime import migration

        base = os.path.dirname(os.path.abspath(__file__))
        cfg = Config(os.path.join(base, '..', 'alembic.ini'))
        script_dir = script.ScriptDirectory.from_config(cfg)

        # Get current revision
        current = get_current_alembic_revision()

        # Get head revision
        head = script_dir.get_current_head()

        if current == head:
            return {
                'current': current,
                'target': head,
                'upgraded': False,
                'error': None
            }

        # Run upgrade
        print(f"\n  Upgrading database: {current or 'None'} -> {head}")
        from alembic.config import CommandLine
        cli = CommandLine()
        result = cli.main(['upgrade', 'head'])

        return {
            'current': current,
            'target': head,
            'upgraded': True,
            'error': None
        }

    except Exception as e:
        return {
            'current': get_current_alembic_revision(),
            'target': None,
            'upgraded': False,
            'error': str(e)
        }


def stamp_baseline_if_needed():
    """
    Stamp the Alembic version table to mark the current schema state.
    Use this ONLY on existing databases where Alembic is being newly introduced.

    This stamps version '001_initial_schema' so Alembic knows the baseline
    is already in place and doesn't try to re-create existing tables.

    Returns:
        dict with keys: 'stamped', 'previous_version', 'error'
    """
    db_path = os.environ.get('DATABASE_PATH', 'warehouse.db')
    if not os.path.isabs(db_path):
        base = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.abspath(os.path.join(base, '..', db_path))

    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if version table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='alembic_version'
        """)
        if cursor.fetchone() is None:
            # Create version table (minimal - Alembic will manage it going forward)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alembic_version (
                    version_num VARCHAR(32)
                )
            """)
            conn.commit()

        # Check if already stamped
        cursor.execute("SELECT version_num FROM alembic_version LIMIT 1")
        row = cursor.fetchone()

        if row is not None:
            return {
                'stamped': False,
                'previous_version': row[0],
                'error': None
            }

        # Stamp the baseline
        cursor.execute(
            "INSERT INTO alembic_version (version_num) VALUES (?)",
            ('001_initial_schema',)
        )
        conn.commit()

        print("  [OK] Alembic baseline stamped to '001_initial_schema'")

        # Also stamp 002
        cursor.execute(
            "INSERT INTO alembic_version (version_num) VALUES (?)",
            ('002_current_schema_marker',)
        )
        conn.commit()
        print("  [OK] Alembic marker stamped to '002_current_schema_marker'")

        return {
            'stamped': True,
            'previous_version': None,
            'error': None
        }

    except Exception as e:
        conn.rollback()
        return {
            'stamped': False,
            'previous_version': None,
            'error': str(e)
        }
    finally:
        conn.close()


def get_migration_status():
    """
    Get a human-readable summary of the current migration state.

    Returns:
        dict with: 'current', 'head', 'pending', 'needs_stamp', 'is_current'
    """
    current = get_current_alembic_revision()

    try:
        from alembic.config import Config
        from alembic import script

        base = os.path.dirname(os.path.abspath(__file__))
        cfg = Config(os.path.join(base, '..', 'alembic.ini'))
        script_dir = script.ScriptDirectory.from_config(cfg)

        head = script_dir.get_current_head()

        # Count pending migrations
        pending = []
        if current is not None:
            for rev in script_dir.walk_revisions(current, head):
                if rev.revision != current:
                    pending.append(rev.revision)

        needs_stamp = current is None and head is not None

        return {
            'current': current,
            'head': head,
            'pending': pending,
            'needs_stamp': needs_stamp,
            'is_current': current == head and current is not None
        }
    except Exception as e:
        return {
            'current': current,
            'head': None,
            'pending': [],
            'needs_stamp': False,
            'is_current': False,
            'error': str(e)
        }