import os
import sys

# Append the current directory to sys.path if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db, initialize_platform_schema

# Import specific module schema initializations
from wms_schema import initialize_wms_schema
from bi_advanced_routes import initialize_reporting_tables
from company_routes import run_company_migrations
from hr_routes import run_hr_migrations
from logistics_routes import run_logistics_migrations
from security_routes import init_security_tables

def run_all_schema_migrations():
    """
    Run all database schema migrations in a controlled, one-time script
    rather than at application runtime.
    """
    print("Initializing core platform schema...")
    initialize_platform_schema()
    
    print("Initializing WMS schema...")
    initialize_wms_schema(get_db)
    
    print("Initializing BI definitions...")
    initialize_reporting_tables()
    
    print("Initializing Company migrations...")
    run_company_migrations()
    
    print("Initializing HR migrations...")
    run_hr_migrations()
    
    print("Initializing Logistics migrations...")
    run_logistics_migrations()
    
    print("Initializing Security tables...")
    init_security_tables()
    
    print("All schemas and migrations applied successfully.")

if __name__ == '__main__':
    run_all_schema_migrations()
