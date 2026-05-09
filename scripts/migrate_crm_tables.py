"""
CRM Extended Database Migration
==============================
Creates all tables needed for the enhanced CRM system.
Run this script to set up the CRM database schema.

Usage:
    python migrate_crm_tables.py
"""

import sqlite3
import os
from datetime import datetime

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'warehouse.db')


def get_connection():
    """Get a database connection with WAL mode."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def migrate():
    """Run all CRM migrations."""
    print("Starting CRM Extended migration...")

    conn = get_connection()

    try:
        # =============================================================================
        # CRM LEADS TABLE
        # =============================================================================
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_number TEXT UNIQUE NOT NULL,
                company_name TEXT NOT NULL,
                contact_name TEXT,
                contact_title TEXT,
                phone TEXT,
                whatsapp TEXT,
                email TEXT,
                website TEXT,
                source TEXT,
                status TEXT DEFAULT 'New',
                priority TEXT DEFAULT 'Medium',
                is_hot INTEGER DEFAULT 0,
                industry TEXT,
                employee_count INTEGER,
                annual_revenue REAL,
                address TEXT,
                city TEXT,
                country TEXT,
                assigned_to INTEGER,
                estimated_value REAL DEFAULT 0,
                currency TEXT DEFAULT 'AED',
                lead_score INTEGER DEFAULT 0,
                age_days INTEGER DEFAULT 0,
                notes TEXT,
                converted_customer_id INTEGER,
                converted_opportunity_id INTEGER,
                converted_at TIMESTAMP,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (assigned_to) REFERENCES users(id),
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        """)
        print("  - Created crm_leads table")

        # Lead contacts
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_lead_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                title TEXT,
                department TEXT,
                phone TEXT,
                email TEXT,
                is_primary INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES crm_leads(id) ON DELETE CASCADE
            )
        """)
        print("  - Created crm_lead_contacts table")

        # Lead activities
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_lead_activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                activity_type TEXT NOT NULL,
                subject TEXT NOT NULL,
                activity_date DATE,
                duration_minutes INTEGER,
                outcome TEXT,
                next_follow_up DATE,
                owner_id INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES crm_leads(id) ON DELETE CASCADE,
                FOREIGN KEY (owner_id) REFERENCES users(id)
            )
        """)
        print("  - Created crm_lead_activities table")

        # Lead notes
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_lead_notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                owner_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES crm_leads(id) ON DELETE CASCADE,
                FOREIGN KEY (owner_id) REFERENCES users(id)
            )
        """)
        print("  - Created crm_lead_notes table")

        # Lead qualification scores
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_lead_qualifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                criterion TEXT NOT NULL,
                score INTEGER DEFAULT 0,
                evaluated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (lead_id) REFERENCES crm_leads(id) ON DELETE CASCADE
            )
        """)
        print("  - Created crm_lead_qualifications table")

        # Lead conversion log
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_lead_conversion_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id INTEGER NOT NULL,
                converted_to TEXT NOT NULL,
                converted_customer_id INTEGER,
                converted_opportunity_id INTEGER,
                converted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                conversion_notes TEXT,
                FOREIGN KEY (lead_id) REFERENCES crm_leads(id) ON DELETE CASCADE
            )
        """)
        print("  - Created crm_lead_conversion_log table")

        # =============================================================================
        # CRM CUSTOMER 360 TABLES
        # =============================================================================

        # Customer contacts
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_customer_contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                title TEXT,
                department TEXT,
                role TEXT,
                phone TEXT,
                whatsapp TEXT,
                email TEXT,
                is_primary INTEGER DEFAULT 0,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id) ON DELETE CASCADE
            )
        """)
        print("  - Created crm_customer_contacts table")

        # Customer hierarchy
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_customer_hierarchy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                relationship_type TEXT,
                related_customer_id INTEGER,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id) ON DELETE CASCADE,
                FOREIGN KEY (related_customer_id) REFERENCES sales_customers(id) ON DELETE SET NULL
            )
        """)
        print("  - Created crm_customer_hierarchy table")

        # Customer segments
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                criteria TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  - Created crm_segments table")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_customer_segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                segment_id INTEGER NOT NULL,
                assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id) ON DELETE CASCADE,
                FOREIGN KEY (segment_id) REFERENCES crm_segments(id) ON DELETE CASCADE
            )
        """)
        print("  - Created crm_customer_segments table")

        # Customer credit risk
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_customer_credit_risk (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER UNIQUE NOT NULL,
                risk_score INTEGER DEFAULT 0,
                risk_level TEXT,
                factors TEXT,
                last_evaluated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id) ON DELETE CASCADE
            )
        """)
        print("  - Created crm_customer_credit_risk table")

        # =============================================================================
        # CRM JOURNEY TABLES
        # =============================================================================

        # Journey events
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_journey_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                event_date DATE,
                channel TEXT,
                description TEXT,
                reference_type TEXT,
                reference_id INTEGER,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id) ON DELETE CASCADE,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        """)
        print("  - Created crm_journey_events table")

        # Customer stage history
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_customer_stage_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                stage TEXT NOT NULL,
                entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                exited_at TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id) ON DELETE CASCADE
            )
        """)
        print("  - Created crm_customer_stage_history table")

        # Touchpoints
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_touchpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                touchpoint_type TEXT NOT NULL,
                touchpoint_date DATE,
                channel TEXT,
                description TEXT,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id) ON DELETE CASCADE
            )
        """)
        print("  - Created crm_touchpoints table")

        # Customer engagement scores
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_customer_engagement (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER UNIQUE NOT NULL,
                engagement_score INTEGER DEFAULT 0,
                engagement_level TEXT,
                last_activities INTEGER DEFAULT 0,
                last_orders INTEGER DEFAULT 0,
                last_quotations INTEGER DEFAULT 0,
                last_evaluated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id) ON DELETE CASCADE
            )
        """)
        print("  - Created crm_customer_engagement table")

        # Customer churn risk
        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_customer_churn_risk (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER UNIQUE NOT NULL,
                risk_score INTEGER DEFAULT 0,
                risk_level TEXT,
                factors TEXT,
                last_evaluated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id) ON DELETE CASCADE
            )
        """)
        print("  - Created crm_customer_churn_risk table")

        # =============================================================================
        # CRM COMPLAINTS TABLES
        # =============================================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_number TEXT UNIQUE NOT NULL,
                customer_id INTEGER,
                order_id INTEGER,
                delivery_id INTEGER,
                category TEXT,
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'New',
                subject TEXT NOT NULL,
                description TEXT,
                assigned_to INTEGER,
                resolution_target_date DATE,
                resolved_at TIMESTAMP,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id),
                FOREIGN KEY (order_id) REFERENCES sales_orders(id),
                FOREIGN KEY (delivery_id) REFERENCES sales_deliveries(id),
                FOREIGN KEY (assigned_to) REFERENCES users(id),
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        """)
        print("  - Created crm_complaints table")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_complaint_timeline (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                description TEXT,
                created_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (complaint_id) REFERENCES crm_complaints(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        print("  - Created crm_complaint_timeline table")

        # =============================================================================
        # CRM KEY ACCOUNTS TABLES
        # =============================================================================

        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_key_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER UNIQUE NOT NULL,
                account_name TEXT NOT NULL,
                tier TEXT DEFAULT 'Key Account',
                account_manager_id INTEGER,
                account_type TEXT,
                business_objectives TEXT,
                success_metrics TEXT,
                last_review_date DATE,
                next_review_date DATE,
                company_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES sales_customers(id),
                FOREIGN KEY (account_manager_id) REFERENCES users(id),
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        """)
        print("  - Created crm_key_accounts table")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_account_objectives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                objective TEXT NOT NULL,
                target_value REAL,
                current_value REAL DEFAULT 0,
                target_date DATE,
                status TEXT DEFAULT 'In Progress',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES crm_key_accounts(id) ON DELETE CASCADE
            )
        """)
        print("  - Created crm_account_objectives table")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_account_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                review_date DATE NOT NULL,
                reviewer_id INTEGER,
                overall_rating INTEGER,
                findings TEXT,
                action_items TEXT,
                next_steps TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES crm_key_accounts(id) ON DELETE CASCADE,
                FOREIGN KEY (reviewer_id) REFERENCES users(id)
            )
        """)
        print("  - Created crm_account_reviews table")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS crm_relationship_map (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                contact_name TEXT NOT NULL,
                contact_company TEXT,
                contact_role TEXT,
                relationship_type TEXT,
                interaction_frequency TEXT,
                last_interaction DATE,
                notes TEXT,
                FOREIGN KEY (account_id) REFERENCES crm_key_accounts(id) ON DELETE CASCADE
            )
        """)
        print("  - Created crm_relationship_map table")

        # =============================================================================
        # CREATE INDEXES
        # =============================================================================

        conn.execute("CREATE INDEX IF NOT EXISTS idx_crm_leads_status ON crm_leads(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_crm_leads_source ON crm_leads(source)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_crm_leads_assigned ON crm_leads(assigned_to)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_crm_leads_score ON crm_leads(lead_score)")

        conn.execute("CREATE INDEX IF NOT EXISTS idx_crm_lead_activities_lead ON crm_lead_activities(lead_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_crm_lead_activities_date ON crm_lead_activities(activity_date)")

        conn.execute("CREATE INDEX IF NOT EXISTS idx_crm_complaints_customer ON crm_complaints(customer_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_crm_complaints_status ON crm_complaints(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_crm_complaints_priority ON crm_complaints(priority)")

        conn.execute("CREATE INDEX IF NOT EXISTS idx_crm_journey_customer ON crm_journey_events(customer_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_crm_journey_date ON crm_journey_events(event_date)")

        conn.execute("CREATE INDEX IF NOT EXISTS idx_crm_touchpoints_customer ON crm_touchpoints(customer_id)")

        conn.execute("CREATE INDEX IF NOT EXISTS idx_crm_key_accounts_customer ON crm_key_accounts(customer_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_crm_key_accounts_manager ON crm_key_accounts(account_manager_id)")

        print("  - Created indexes")

        conn.commit()
        print("\nCRM Extended migration completed successfully!")

    except Exception as e:
        print(f"\nError during migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
