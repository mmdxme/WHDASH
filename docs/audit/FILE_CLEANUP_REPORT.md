"""
WHDASH File Cleanup Report
==========================
Classification and handling of stale/duplicate files in the repository.

FILE CLASSIFICATION:
====================

KEEP (Core application files - essential for operation):
- app.py - Main application entry point
- config.py - Configuration module
- database.py - Database connection management
- permissions.py - RBAC permission system
- settings.py - Settings management
- navigation.py - Navigation/menu structure
- master_data.py - Master data management
- reporting.py - Reporting framework
- theme_system.py, theme_engine.py - Theme management
- extensions.py - Flask extensions
- wsgi.py - WSGI entry point
- app_factory.py - Application factory pattern
- sqlite_schema.sql - Core database schema
- requirements.txt - Python dependencies

KEEP (Route modules - core business logic):
- hr_routes.py, hr_models.py
- wms_routes.py, wms_models.py
- logistics_routes.py, logistics_models.py
- sales_routes.py, sales_models.py
- sales_suite_routes.py, sales_suite_models.py
- procurement_routes.py, procurement_models.py
- finance_routes.py, finance_models.py
- quality_routes.py, quality_models.py
- asset_routes.py, asset_models.py
- maintenance_routes.py, maintenance_models.py
- ecommerce_routes.py, ecommerce_models.py
- document_routes.py, document_models.py
- workflow_routes.py, workflow_models.py
- form_routes.py, form_models.py
- admin_routes.py
- profile_routes.py
- company_routes.py, company_models.py
- planning_routes.py, planning_models.py
- marketing_routes.py, marketing_models.py
- customer_intelligence_routes.py, customer_intelligence_models.py
- social_media_routes.py, social_media_models.py
- bi_routes.py, bi_models.py, bi_reporting_models.py
- bi_advanced_routes.py
- api_gateway_routes.py, api_gateway_models.py
- issue_tracker_routes.py
- task_center_routes.py
- flow_routes.py, flow_models.py
- rest_api.py
- form_helpers.py

KEEP (Supporting services):
- services/ - Authentication, security, logging services
- repositories/ - Data access layer
- tests/ - Test suite

KEEP (Templates):
- templates/ - All HTML templates organized by module

ARCHIVE (Files to keep but not actively maintain - may be useful for reference):
- migrate_v2.py, migrate_v3.py, migrate_v4.py, migrate_v5.py, migrate_v6_delivery.py
- migrate_email_tables.py, migrate_sales_tables.py, migrate_unify.py, migrate_sales_suite.py
  (These show historical schema evolution - keep for understanding migrations)
- seed_data.py - Original seed data logic (for reference)
- seed_wms_sample_data.py - Sample WMS data (for reference)

ARCHIVE/REMOVE (Experimental or superseded files):
- binary_search.py, binary_search2.py, binary_search3.py, binary_search_exact.py - Debug utilities
- tokenize_test.py - Testing utility
- fix_models.py, fix_models2.py, fix_fresh.py, fix_all_endpoints.py, fix_employee_codes.py,
  fix_form_tables.py, fix_quality_models.py, fix_wms_data.py, fix_errors_loop.py,
  fix_maintenance.py, fix_models.py - Various fix attempts (superseded)
- count_quotes.py, scan_all_quotes.py, scan_fstrings.py - Debug utilities
- convert_lf.py, convert_and_fix.py - Line ending fixes (done)
- ast_dump_test.py - Debug utility
- track_strings.py, track_strings2.py, track_detail.py, track_fstrings.py,
  track_improved.py, track_all_strings.py - String tracking utilities
- extract_funcs.py, extract_funcs2.py, extract_v3.py, extract_via_nav.py,
  extract_js_nav.py, extract_commit_nav.py, extract_customers_hybrid.py,
  extract_customers_playwright.py - Extraction utilities (superseded)
- remove_func.py, remove_problem_funcs.py, remove_and_test.py - Debug utilities
- scrape_all_items.py, scrape_all_products_fixed.py, scrape_all_products_playwright.py,
  scrape_employees.py, scrape_via_api.py - Scraping utilities
- sync_customers_browser.py, sdad_customers_sync_v2.py, sdad_customers_sync_final.py,
  sdad_sync.py - Sync utilities (superseded by proper sync)
- missing_translations_by_lang.py - Translation utility
- init_maintenance.py - Initialization utility (functionality moved to modules)
- remove_problem_funcs.py - Debug utility
- validate.py - Validation utility
- show_lines.py, show_data.py, show_all_items.py, get_schema.py, get_customers_simple.py,
  get_customers_via_requests.py, get_all_customers.py, fetch_all_employees.py - Data inspection utilities
- final_fix.py, final_check.py - Final fix utilities (done)
- add_hr_columns.py - Schema update utility (done)
- validate.py - Validation utility
- conversion utility scripts

REMOVE (Completely superseded or experimental):
- quality_models_backup.py, quality_models_minimal.py, quality_models_simple.py,
  quality_models_lf.py, quality_models_lf_fixed.py, quality_models_test.py,
  quality_models_no_supplier.py, quality_models_backup.py - Multiple quality model versions
- seed_minimal.py, seed_sample_data.py - Superseded by comprehensive seed scripts
- run_debug.py, start_test_server.py, simple_test.py - Debug utilities
- warehouse_manager.py - Duplicate functionality
- integration.py - May be useful but unclear purpose
- admin_settings.py - May overlap with admin_routes.py
- project_models.py - Unclear purpose
- unifed_settings.py - Typo, should be unified_settings.py if needed
- admin_demo_data.py - Demo data utility

NOTE: This classification is a starting point. Each file should be reviewed
individually before deletion to ensure no unique functionality is lost.
"""

# Files recommended for removal (unsafe to delete without verification)
FILES_FOR_REMOVAL = [
    # Duplicate quality model versions
    'quality_models_backup.py',
    'quality_models_minimal.py',
    'quality_models_simple.py',
    'quality_models_lf.py',
    'quality_models_lf_fixed.py',
    'quality_models_test.py',
    'quality_models_no_supplier.py',

    # Superseded debug/fix scripts
    'binary_search.py',
    'binary_search2.py',
    'binary_search3.py',
    'binary_search_exact.py',
    'tokenize_test.py',
    'run_debug.py',
    'simple_test.py',
    'start_test_server.py',
]

# Files to archive (can be moved to archive/ folder)
FILES_FOR_ARCHIVE = [
    # Migration scripts (keep for reference)
    'migrate_v2.py',
    'migrate_v3.py',
    'migrate_v4.py',
    'migrate_v5.py',
    'migrate_v6_delivery.py',
    'migrate_email_tables.py',
    'migrate_sales_tables.py',
    'migrate_unify.py',
    'migrate_sales_suite.py',

    # Seed scripts (superseded by comprehensive seeds)
    'seed_minimal.py',
    'seed_sample_data.py',
    'seed_data.py',

    # Debug/fix scripts
    'fix_models.py',
    'fix_models2.py',
    'fix_fresh.py',
    'fix_all_endpoints.py',
    'fix_employee_codes.py',
    'fix_form_tables.py',
    'fix_quality_models.py',
    'fix_wms_data.py',
    'fix_errors_loop.py',
    'fix_maintenance.py',

    # Extraction utilities
    'extract_funcs.py',
    'extract_funcs2.py',
    'extract_v3.py',
    'extract_via_nav.py',
    'extract_js_nav.py',
    'extract_commit_nav.py',
    'extract_customers_hybrid.py',
    'extract_customers_playwright.py',

    # Scraping utilities
    'scrape_all_items.py',
    'scrape_all_products_fixed.py',
    'scrape_all_products_playwright.py',
    'scrape_employees.py',
    'scrape_via_api.py',

    # Sync utilities (superseded)
    'sync_customers_browser.py',
    'sdad_customers_sync_v2.py',
    'sdad_customers_sync_final.py',
    'sdad_sync.py',

    # String tracking
    'track_strings.py',
    'track_strings2.py',
    'track_detail.py',
    'track_fstrings.py',
    'track_improved.py',
    'track_all_strings.py',

    # Data inspection utilities
    'show_lines.py',
    'show_data.py',
    'show_all_items.py',
    'get_schema.py',
    'get_customers_simple.py',
    'get_customers_via_requests.py',
    'get_all_customers.py',
    'fetch_all_employees.py',
]


if __name__ == '__main__':
    import os

    print("WHDASH File Cleanup Report")
    print("=" * 70)
    print()
    print("Files recommended for removal (verify before deleting):")
    for f in FILES_FOR_REMOVAL:
        exists = os.path.exists(f)
        status = "[EXISTS]" if exists else "[MISSING]"
        print(f"  {status} {f}")

    print()
    print("Files recommended for archiving:")
    for f in FILES_FOR_ARCHIVE:
        exists = os.path.exists(f)
        status = "[EXISTS]" if exists else "[MISSING]"
        print(f"  {status} {f}")
