import os
import sys

# Setup paths for Layered Architecture
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'controllers'))
sys.path.insert(0, os.path.join(BASE_DIR, 'models'))
sys.path.insert(0, os.path.join(BASE_DIR, 'services'))
sys.path.insert(0, os.path.join(BASE_DIR, 'repositories'))

def run_all_migrations():
    """
    Run all module-specific database initializations and seeders.
    This was extracted from app.py to prevent slow startup times and silent database errors.
    """
    from database import get_db
    from application.database_init import init_db

    print("Starting database initialization...")

    # Run init_db (main database initialization)
    init_db()
    print("Core database tables initialized.")

    try:
        from planning_models import init_planning_tables
        db = get_db()
        init_planning_tables(db)
        db.close()
        print("Planning tables initialized.")
    except Exception as e:
        print(f"Planning tables warning: {e}")

    try:
        from marketing_models import run_marketing_migrations
        from social_media_models import run_social_media_migrations
        run_marketing_migrations()
        run_social_media_migrations()
        print("Marketing/Social tables initialized.")
    except Exception as e:
        print(f"Marketing migrations warning: {e}")

    try:
        from finance_models import initialize_finance_tables
        from finance_enhancement_models import initialize_finance_enhancement_tables
        initialize_finance_tables()
        initialize_finance_enhancement_tables()
        print("Finance tables initialized.")
    except Exception as e:
        print(f"Finance tables warning: {e}")

    try:
        from quality_models import initialize_quality_tables
        from spc_models import initialize_spc_tables
        initialize_quality_tables()
        initialize_spc_tables()
        print("Quality tables initialized.")
    except Exception as e:
        print(f"Quality/SPC tables warning: {e}")

    try:
        from customer_intelligence_models import init_ci_tables
        init_ci_tables()
        print("CI tables initialized.")
    except Exception as e:
        print(f"CI tables warning: {e}")

    try:
        from project_models import init_project_tables
        init_project_tables()
        print("Project tables initialized.")
    except Exception as e:
        print(f"Project tables warning: {e}")

    try:
        from legal_tax_models import initialize_legal_tax_schema
        initialize_legal_tax_schema()
        print("Legal/Tax tables initialized.")
    except Exception as e:
        print(f"Legal/Tax schema warning: {e}")

    try:
        from api_gateway_models import init_api_gateway_tables
        init_api_gateway_tables()
        print("API Gateway tables initialized.")
    except Exception as e:
        print(f"API Gateway warning: {e}")

    try:
        from workflow_models import initialize_workflow_schema
        initialize_workflow_schema()
        print("Workflow tables initialized.")
    except Exception as e:
        print(f"Workflow schema warning: {e}")

    try:
        from integration_models import init_integration_tables
        init_integration_tables()
        print("Integration tables initialized.")
    except Exception as e:
        print(f"Integration tables warning: {e}")

    try:
        from btp_models import init_btp_tables, seed_btp_sample_data
        init_btp_tables()
        seed_btp_sample_data()
        print("BTP tables initialized.")
    except Exception as e:
        print(f"BTP tables warning: {e}")

    try:
        from grc_models import init_grc_tables, seed_grc_initial_data
        init_grc_tables()
        seed_grc_initial_data()
        print("GRC tables initialized.")
    except Exception as e:
        print(f"GRC tables warning: {e}")

    try:
        from payroll_models import run_payroll_migrations, seed_payroll_default_data
        run_payroll_migrations()
        seed_payroll_default_data()
        print("Payroll module initialized successfully")
    except Exception as e:
        print(f"Payroll module warning: {e}")

    try:
        from expense_travel_models import initialize_expense_travel_schema
        initialize_expense_travel_schema()
        print("Expense/Travel module initialized successfully")
    except Exception as e:
        print(f"Expense/Travel module warning: {e}")

    try:
        from org_planning_models import run_org_planning_migrations
        run_org_planning_migrations()
        print("Org Planning tables initialized.")
    except Exception as e:
        print(f"Org Planning migrations warning: {e}")

    try:
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
        print("Platform data initialized.")
    except Exception as e:
        print(f"Platform initialization warning: {e}")

    print("All migrations completed!")

if __name__ == '__main__':
    run_all_migrations()
