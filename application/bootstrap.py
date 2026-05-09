"""
Application Bootstrap Module
============================

Handles application creation, configuration, and initialization.
This module replaces the startup logic that was previously mixed into app.py.

Key responsibilities:
- Flask app creation with configuration
- Environment setup
- Directory initialization
- Base schema setup
- Admin user creation
- Module initialization orchestration

Usage:
    from application.bootstrap import create_app, init_app

    app = create_app()
    init_app(app)
"""

import os
import sqlite3
from datetime import datetime
from typing import Optional, Tuple

from flask import Flask
from werkzeug.security import generate_password_hash


# ============================================================================
# Base Directory
# ============================================================================

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


# ============================================================================
# Configuration Loading
# ============================================================================

def load_config(app: Flask) -> None:
    """
    Load configuration from config module and environment variables.

    Args:
        app: Flask application instance
    """
    from config import (
        SECRET_KEY, ENV, DEBUG, DATABASE_PATH as CONFIG_DATABASE_PATH,
        UPLOAD_FOLDER as CONFIG_UPLOAD_FOLDER, SESSION_FILE_DIR
    )

    app.secret_key = SECRET_KEY
    app.config['TEMPLATES_AUTO_RELOAD'] = DEBUG
    app.jinja_env.auto_reload = DEBUG

    # Store paths
    app.config['DATABASE_PATH'] = os.environ.get('DATABASE_PATH', CONFIG_DATABASE_PATH)
    app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', CONFIG_UPLOAD_FOLDER)

    # Session cookie security
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = ENV.lower() == 'production'

    # Session directory
    if hasattr(app, 'config'):
        app.config['SESSION_FILE_DIR'] = SESSION_FILE_DIR


# ============================================================================
# Directory Initialization
# ============================================================================

def ensure_directories(app: Flask) -> None:
    """
    Ensure required directories exist.

    Args:
        app: Flask application instance
    """
    directories = [
        app.config.get('UPLOAD_FOLDER', ''),
        app.config.get('SESSION_FILE_DIR', ''),
    ]

    # Add database directory
    db_path = app.config.get('DATABASE_PATH', '')
    if db_path:
        db_dir = os.path.dirname(os.path.abspath(db_path))
        directories.append(db_dir)

    for directory in directories:
        if directory:
            os.makedirs(directory, exist_ok=True)


def ensure_database_directory() -> str:
    """Get and ensure database directory exists. Returns database path."""
    from config import DATABASE_PATH
    DATABASE = os.environ.get('DATABASE_PATH', DATABASE_PATH)
    db_dir = os.path.dirname(os.path.abspath(DATABASE))
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    return DATABASE


# ============================================================================
# Base Schema Initialization
# ============================================================================

def ensure_base_schema(DATABASE: str) -> None:
    """
    Ensure the base database schema exists.

    Args:
        DATABASE: Path to the SQLite database file
    """
    schema_path = os.path.join(BASE_DIR, 'sqlite_schema.sql')
    if not os.path.exists(schema_path):
        return

    needs_schema = not os.path.exists(DATABASE) or os.path.getsize(DATABASE) == 0

    conn = sqlite3.connect(DATABASE)
    try:
        if not needs_schema:
            table_exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'companies'"
            ).fetchone()
            needs_schema = table_exists is None

        if needs_schema:
            with open(schema_path, 'r', encoding='utf-8') as schema_file:
                conn.executescript(schema_file.read())
            conn.commit()
    finally:
        conn.close()


# ============================================================================
# Admin User Initialization
# ============================================================================

def ensure_admin_user(DATABASE: str) -> None:
    """
    Create default admin user if not exists and ADMIN_PASSWORD is set.

    Args:
        DATABASE: Path to the SQLite database file
    """
    admin_password = os.environ.get('ADMIN_PASSWORD', '').strip()
    if not admin_password:
        return

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    try:
        role = conn.execute(
            "SELECT id FROM roles WHERE role_name = ? LIMIT 1",
            ('Global Admin',)
        ).fetchone()

        if role:
            role_id = role['id']
        else:
            conn.execute(
                "INSERT INTO roles (role_name, company_id, can_edit_stock, can_manage_users) VALUES (?, ?, ?, ?)",
                ('Global Admin', None, 1, 1)
            )
            role_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        admin_user = conn.execute(
            "SELECT id FROM users WHERE username = ? LIMIT 1",
            ('admin',)
        ).fetchone()
        hashed_password = generate_password_hash(admin_password)

        if admin_user:
            conn.execute(
                "UPDATE users SET password = ?, role_id = ? WHERE id = ?",
                (hashed_password, role_id, admin_user['id'])
            )
        else:
            conn.execute(
                "INSERT INTO users (username, email, password, role_id) VALUES (?, ?, ?, ?)",
                ('admin', 'admin@warehouse.local', hashed_password, role_id)
            )
        conn.commit()
    finally:
        conn.close()


# ============================================================================
# Platform Initialization
# ============================================================================

def initialize_platform_systems() -> None:
    """
    Initialize platform-wide systems (permissions, settings, etc).
    """
    from database import (
        initialize_platform_schema,
        initialize_permissions,
        initialize_settings,
        initialize_reporting,
        initialize_master_data
    )

    initialize_platform_schema()
    initialize_permissions()
    initialize_settings()
    initialize_reporting()
    initialize_master_data()


# ============================================================================
# Planning Tables Initialization
# ============================================================================

def initialize_planning_tables() -> None:
    """Initialize planning module tables."""
    try:
        from database import get_db
        from planning_models import init_planning_tables

        db = get_db()
        init_planning_tables(db)
        db.close()
    except Exception as e:
        print(f"Planning tables initialization warning: {e}")


# ============================================================================
# Marketing Tables Initialization
# ============================================================================

def initialize_marketing_tables() -> None:
    """Initialize marketing and social media tables."""
    try:
        from marketing_models import run_marketing_migrations
        from social_media_models import run_social_media_migrations

        run_marketing_migrations()
        run_social_media_migrations()
    except Exception as e:
        print(f"Marketing migrations warning (non-fatal): {e}")


# ============================================================================
# Finance Tables Initialization
# ============================================================================

def initialize_finance_tables() -> None:
    """Initialize finance module tables."""
    try:
        from finance_models import initialize_finance_tables
        initialize_finance_tables()
    except Exception as e:
        print(f"Finance tables initialization warning: {e}")


def initialize_finance_enhancement_tables() -> None:
    """Initialize finance enhancement tables."""
    try:
        from finance_enhancement_models import initialize_finance_enhancement_tables
        initialize_finance_enhancement_tables()
    except Exception as e:
        print(f"Finance enhancement tables warning: {e}")


# ============================================================================
# Other Module Table Initializations
# ============================================================================

def initialize_quality_tables() -> None:
    """Initialize quality management tables."""
    try:
        from quality_models import initialize_quality_tables
        initialize_quality_tables()
    except Exception as e:
        print(f"Quality tables initialization warning: {e}")


def initialize_spc_tables() -> None:
    """Initialize SPC tables."""
    try:
        from spc_models import initialize_spc_tables
        initialize_spc_tables()
    except Exception as e:
        print(f"SPC tables initialization warning: {e}")


def initialize_ci_tables() -> None:
    """Initialize Customer Intelligence tables."""
    try:
        from customer_intelligence_models import init_ci_tables
        init_ci_tables()
    except Exception as e:
        print(f"Customer Intelligence tables warning: {e}")


def initialize_project_tables() -> None:
    """Initialize Project tables."""
    try:
        from project_models import init_project_tables
        init_project_tables()
    except Exception as e:
        print(f"Project tables initialization warning: {e}")


def initialize_legal_tax_schema() -> None:
    """Initialize Legal/Tax schema."""
    try:
        from legal_tax_models import initialize_legal_tax_schema
        initialize_legal_tax_schema()
    except Exception as e:
        print(f"Legal/Tax schema initialization warning: {e}")


def initialize_api_gateway_tables() -> None:
    """Initialize API Gateway tables."""
    try:
        from api_gateway_models import init_api_gateway_tables
        init_api_gateway_tables()
    except Exception as e:
        print(f"API Gateway tables warning: {e}")


def initialize_workflow_schema() -> None:
    """Initialize Workflow/BPM schema."""
    try:
        from workflow_models import initialize_workflow_schema
        initialize_workflow_schema()
    except Exception as e:
        print(f"Workflow schema initialization warning: {e}")


def initialize_integration_tables() -> None:
    """Initialize Integration tables."""
    try:
        from integration_models import init_integration_tables
        init_integration_tables()
    except Exception as e:
        print(f"Integration tables warning: {e}")


def initialize_btp_tables() -> None:
    """Initialize BTP tables."""
    try:
        from btp_models import init_btp_tables, seed_btp_sample_data
        init_btp_tables()
        seed_btp_sample_data()
    except Exception as e:
        print(f"BTP tables warning: {e}")


def initialize_grc_tables() -> None:
    """Initialize GRC tables."""
    try:
        from grc_models import init_grc_tables, seed_grc_initial_data
        init_grc_tables()
        seed_grc_initial_data()
    except Exception as e:
        print(f"GRC tables warning: {e}")


def initialize_expense_travel_schema() -> None:
    """Initialize Expense/Travel schema."""
    try:
        from expense_travel_models import initialize_expense_travel_schema
        initialize_expense_travel_schema()
    except Exception as e:
        print(f"Expense/Travel schema warning: {e}")


def run_payroll_migrations() -> None:
    """Run payroll migrations."""
    try:
        from payroll_models import run_payroll_migrations, seed_payroll_default_data
        run_payroll_migrations()
        seed_payroll_default_data()
    except Exception as e:
        print(f"Payroll migrations warning: {e}")


def run_org_planning_migrations() -> None:
    """Run organizational planning migrations."""
    try:
        from org_planning_models import run_org_planning_migrations
        run_org_planning_migrations()
    except Exception as e:
        print(f"Org Planning migrations warning: {e}")


# ============================================================================
# Main Application Factory
# ============================================================================

def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Create and configure the Flask application.

    Args:
        config_name: Configuration name ('development', 'production', etc.)

    Returns:
        Configured Flask application instance
    """
    import os
    base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    app = Flask(__name__, root_path=base_dir)

    # Load configuration
    load_config(app)

    # Ensure directories exist
    ensure_directories(app)

    # Register essential filters early to avoid template errors
    import datetime

    @app.template_filter('date')
    def _date_filter(value, format='%Y-%m-%d'):
        """Format date - handles 'now' string, datetime objects, and ISO date strings."""
        if value == 'now' or value is None:
            return datetime.datetime.now().strftime(format)
        if isinstance(value, str):
            try:
                value = datetime.datetime.fromisoformat(value)
            except ValueError:
                try:
                    value = datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    return value
        if isinstance(value, (datetime.datetime, datetime.date)):
            return value.strftime(format)
        return value

    return app


def init_app(app: Flask) -> None:
    """
    Initialize the application with all required systems.

    This replaces the inline initialization code that was in app.py.

    Args:
        app: Flask application instance
    """
    # Database setup
    DATABASE = ensure_database_directory()
    ensure_base_schema(DATABASE)

    # Run init_db() from app.py
    from application.database_init import init_db
    init_db()

    # Admin user
    ensure_admin_user(DATABASE)

    # Platform systems
    initialize_platform_systems()

    # ========================================================================
    # MIGRATION FRAMEWORK INTEGRATION
    # ========================================================================
    # Ensure the Alembic version table is in sync with the actual DB state.
    # This handles existing databases where Alembic is newly introduced.
    # Safe to call on every startup - idempotent and fast when DB is current.
    #
    # NEW SCHEMA CHANGES: All future schema changes must go through Alembic
    # migrations. Do NOT add new CREATE TABLE logic to init_*() functions.
    #
    # Migration flow:
    #   1. stamp_baseline_if_needed() - marks existing DBs with Alembic baseline
    #   2. upgrade_to_head()           - applies any pending Alembic migrations
    #   3. init_*() deprecated calls   - safe fallback (tables already exist via migrations)
    # ========================================================================

    from migrations import stamp_baseline_if_needed, ensure_db_current

    try:
        stamp_result = stamp_baseline_if_needed()
        if stamp_result.get('stamped'):
            print("  [MIGRATION] Alembic baseline stamped for existing database")
        elif stamp_result.get('previous_version'):
            pass  # Already has Alembic version - normal case
    except Exception as e:
        print(f"  [MIGRATION] Baseline stamp check: {e}")

    # Apply any pending Alembic migrations (runs fast when DB is current)
    # Set safe_mode=False to avoid prompting during app startup
    try:
        upgrade_result = ensure_db_current(safe_mode=False)
        if upgrade_result.get('upgraded'):
            print(f"  [MIGRATION] Database upgraded to: {upgrade_result.get('target')}")
        elif upgrade_result.get('error'):
            print(f"  [MIGRATION] Upgrade check: {upgrade_result.get('error')}")
    except Exception as e:
        print(f"  [MIGRATION] Upgrade error: {e}")

    # ========================================================================
    # MODULE-SPECIFIC TABLES (DEPRECATED)
    # ========================================================================
    # These init_* functions are DEPRECATED. They remain only for backward
    # compatibility with existing databases that may have tables created by these
    # functions before Alembic was integrated.
    #
    # On a properly migrated database, these will be no-ops because:
    #   - Alembic 003 migration has already created the tables (IF NOT EXISTS)
    #   - CREATE TABLE IF NOT EXISTS is safe to call on existing tables
    #
    # DO NOT add new CREATE TABLE logic to these functions.
    # All new schema changes must go through: python migrate.py revision -m "..."

    _call_deprecated_init("planning", initialize_planning_tables)
    _call_deprecated_init("marketing", initialize_marketing_tables)
    _call_deprecated_init("finance", initialize_finance_tables)
    _call_deprecated_init("finance_enhancement", initialize_finance_enhancement_tables)
    _call_deprecated_init("quality", initialize_quality_tables)
    _call_deprecated_init("spc", initialize_spc_tables)
    _call_deprecated_init("ci", initialize_ci_tables)
    _call_deprecated_init("project", initialize_project_tables)
    _call_deprecated_init("legal_tax", initialize_legal_tax_schema)
    _call_deprecated_init("api_gateway", initialize_api_gateway_tables)
    _call_deprecated_init("workflow", initialize_workflow_schema)
    _call_deprecated_init("integration", initialize_integration_tables)
    _call_deprecated_init("btp", initialize_btp_tables)
    _call_deprecated_init("grc", initialize_grc_tables)
    _call_deprecated_init("expense_travel", initialize_expense_travel_schema)

    try:
        run_payroll_migrations()
    except Exception as e:
        print(f"  [DEPRECATED] payroll migrations: {e}")

    try:
        run_org_planning_migrations()
    except Exception as e:
        print(f"  [DEPRECATED] org_planning migrations: {e}")

    # NOTE: GRC comprehensive seeding was previously called here from seed_grc_data.py.
    # GRC reference data is now seeded through the organized seeds/ framework.
    # Use: python seeds/runner.py --mode demo  for demo data seeding.


def _call_deprecated_init(name, func):
    """Call a deprecated init function, catching and logging any errors."""
    try:
        func()
    except Exception as e:
        print(f"  [DEPRECATED] {name} init: {e}")


# ============================================================================
# Convenience Function
# ============================================================================

def get_database_path() -> str:
    """Get the configured database path."""
    from config import DATABASE_PATH
    return os.environ.get('DATABASE_PATH', DATABASE_PATH)