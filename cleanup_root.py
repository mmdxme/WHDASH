import os
import shutil

def mkdir_if_not_exists(path):
    if not os.path.exists(path):
        os.makedirs(path)

mkdir_if_not_exists("docs")
mkdir_if_not_exists("docs/audit")
mkdir_if_not_exists("scripts")
mkdir_if_not_exists("scripts/fixes")
mkdir_if_not_exists("scripts/tools")
mkdir_if_not_exists("scripts/scrape")
mkdir_if_not_exists("scripts/translations")
mkdir_if_not_exists("archive")
mkdir_if_not_exists("bootstrap")

fixes_prefixes = ["fix_", "diagnose_"]
tools_prefixes = ["find_", "extract_", "trace_", "track_", "check_", "parse_", "byte_", "bracket_", "count_", "scan_", "debug", "binary_search", "combine_"]
scrape_prefixes = ["scrape_", "sdad_", "get_customers", "extract_customers"]
translations_prefixes = ["add_ru_", "add_bi_", "add_doc_", "add_finance_", "add_project_", "fill_ru", "fix_en_", "fix_fa_"]

core_files = {
    "app.py", "app_factory.py", "blueprints.py", "celery_app.py", "config.py", "constants.py", 
    "csrf_protection.py", "database.py", "database_health.py", "extensions.py", "wsgi.py", "settings.py", 
    "unified_settings.py", "translation_loader.py", "rebuild.py", "rest_api.py", "reporting.py", 
    "permissions.py", "navigation.py", "master_data.py", "migrate.py", "theme_engine.py", "theme_system.py", 
    "validation.py", "webhook_manager.py", "wms_sap_adapter.py", "wms_schema.py", "integration.py", 
    "export_utils.py", "event_system.py", "email_manager.py", "form_helpers.py", "form_workflow.py", 
    "analytics_engine.py", "jinja_filters.py", "cleanup_root.py"
}

for file in os.listdir("."):
    if not os.path.isfile(file):
        continue
        
    if file.endswith(".md") or file.endswith(".html"):
        if "REPORT" in file.upper() or "AUDIT" in file.upper() or "QA" in file.upper() or "CHECKLIST" in file.upper() or "PROGRESS" in file.upper():
            shutil.move(file, os.path.join("docs", "audit", file))
        elif file.upper() == "README.md":
            pass
        else:
            shutil.move(file, os.path.join("docs", file))
            
    elif file.endswith(".txt") and file not in ["requirements.txt"]:
        if "REPORT" in file.upper() or "AUDIT" in file.upper():
            shutil.move(file, os.path.join("docs", "audit", file))
        else:
            shutil.move(file, os.path.join("archive", file))
            
    elif file.endswith(".py") and file not in core_files and not file.endswith("_routes.py") and not file.endswith("_models.py") and not file.endswith("_settings.py") and not file.endswith("translations.py"):
        if any(file.startswith(p) for p in fixes_prefixes):
            shutil.move(file, os.path.join("scripts", "fixes", file))
        elif any(file.startswith(p) for p in scrape_prefixes):
            shutil.move(file, os.path.join("scripts", "scrape", file))
        elif any(file.startswith(p) for p in translations_prefixes):
            shutil.move(file, os.path.join("scripts", "translations", file))
        elif any(file.startswith(p) for p in tools_prefixes) or file.endswith("_test.py") or file.endswith("_check.py"):
            shutil.move(file, os.path.join("scripts", "tools", file))
        elif "seed" in file or "demo" in file or file.startswith("reseed"):
            shutil.move(file, os.path.join("bootstrap", file))
        elif "migrate" in file:
            shutil.move(file, os.path.join("scripts", file))
        else:
            shutil.move(file, os.path.join("scripts", file))
            
    elif file.endswith(".json"):
        shutil.move(file, os.path.join("archive", file))
