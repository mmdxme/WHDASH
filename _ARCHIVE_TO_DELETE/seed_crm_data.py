"""
CRM Sample Data Seeder
=====================
Creates realistic sample data for the CRM module.
Run this script to populate the CRM tables with demo data.

Usage:
    python seed_crm_data.py
"""

import sqlite3
import os
import random
from datetime import datetime, timedelta

DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'warehouse.db')

# Sample data
FIRST_NAMES = ['Ahmed', 'Mohammed', 'Ali', 'Sara', 'Fatima', 'Yusuf', 'Aisha', 'Omar', 'Layla', 'Hassan', 'Zainab', 'Khaled', 'Nadia', 'Tariq', 'Rania']
LAST_NAMES = ['Al-Rashid', 'Al-Mansour', 'Al-Farsi', 'Al-Qureshi', 'Al-Zahrawi', 'Ibn-Alb', 'Ben-Hassan', 'El-Amin', 'Al-Mukhtar', 'Al-Shareef']
COMPANY_PREFIXES = ['Al', 'Middle East', 'Gulf', 'Emirates', 'Arabian', 'Dubai', 'Abu Dhabi', 'Sharjah']
COMPANY_TYPES = ['Trading', 'Industries', 'Group', 'LLC', 'Corp', 'Est.', 'Partners', 'Holdings']
INDUSTRIES = ['Construction', 'Manufacturing', 'Retail', 'Healthcare', 'Technology', 'Logistics', 'Food & Beverage', 'Automotive', 'Energy', 'Real Estate']
CITIES = ['Dubai', 'Abu Dhabi', 'Sharjah', 'Al Ain', 'Riyadh', 'Jeddah', 'Manama', 'Doha', 'Muscat', 'Kuwait City']
COUNTRIES = ['AE', 'SA', 'BH', 'QA', 'OM', 'KW']
LEAD_SOURCES = ['Website', 'Phone Inquiry', 'Walk-in', 'Referral', 'Partner', 'Social Media', 'Email Campaign', 'Trade Show', 'Google Ads', 'LinkedIn']
LEAD_STATUSES = ['New', 'Contacted', 'Qualified', 'Unqualified', 'In Progress', 'Converted', 'Lost', 'On Hold']
LEAD_PRIORITIES = ['Low', 'Medium', 'High', 'Urgent']
ACTIVITY_TYPES = ['Call', 'Meeting', 'Visit', 'Email', 'Task', 'Note']
COMPLAINT_CATEGORIES = ['Product Quality', 'Delivery Issue', 'Pricing', 'Service', 'Billing', 'Technical Support']
COMPLAINT_STATUSES = ['New', 'In Progress', 'Pending Customer', 'Escalated', 'Resolved', 'Closed']
COMPLAINT_PRIORITIES = ['Low', 'Medium', 'High', 'Critical']
ACCOUNT_TIERS = ['Standard', 'Preferred', 'Key Account', 'Strategic', 'Premium']


def get_connection():
    """Get a database connection with WAL mode."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def random_date(start_days_ago=365, end_days_ago=0):
    """Generate a random date within a range."""
    start = datetime.now() - timedelta(days=start_days_ago)
    end = datetime.now() - timedelta(days=end_days_ago)
    delta = end - start
    random_days = random.randint(0, delta.days)
    return (start + timedelta(days=random_days)).strftime('%Y-%m-%d')


def generate_lead_number(cursor, year):
    """Generate a unique lead number."""
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM crm_leads WHERE lead_number LIKE ?
    """, (f'LEAD-{year}%',))
    count = cursor.fetchone()['cnt']
    return f"LEAD-{year}-{str(count + 1).zfill(5)}"


def generate_complaint_number(cursor, year):
    """Generate a unique complaint number."""
    cursor.execute("""
        SELECT COUNT(*) as cnt FROM crm_complaints WHERE complaint_number LIKE ?
    """, (f'CMP-{year}%',))
    count = cursor.fetchone()['cnt']
    return f"CMP-{year}-{str(count + 1).zfill(5)}"


def seed_crm_leads(conn, num_leads=50):
    """Seed CRM leads."""
    print(f"  Creating {num_leads} CRM leads...")

    # Get existing users for assignment
    cursor = conn.execute("SELECT id FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%')")
    salespersons = [row['id'] for row in cursor.fetchall()]
    if not salespersons:
        salespersons = [1]

    for i in range(num_leads):
        year = random.choice([2025, 2026])
        lead_number = generate_lead_number(conn.cursor(), year)

        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        company_name = f"{random.choice(COMPANY_PREFIXES)} {random.choice(COMPANY_TYPES)} {last_name}"

        lead_data = {
            'lead_number': lead_number,
            'company_name': company_name,
            'contact_name': f"{first_name} {last_name}",
            'contact_title': random.choice(['Manager', 'Director', 'CEO', 'Procurement Head', 'Purchasing Manager']),
            'phone': f"+971 {random.randint(50, 59)} {random.randint(100, 999)} {random.randint(1000, 9999)}",
            'whatsapp': f"+971 {random.randint(50, 59)} {random.randint(100, 999)} {random.randint(1000, 9999)}",
            'email': f"{first_name.lower()}.{last_name.lower()}@{company_name.lower().replace(' ', '')}.com",
            'website': f"www.{company_name.lower().replace(' ', '')}.com",
            'source': random.choice(LEAD_SOURCES),
            'status': random.choices(LEAD_STATUSES, weights=[20, 15, 15, 5, 10, 10, 10, 15])[0],
            'priority': random.choices(LEAD_PRIORITIES, weights=[30, 40, 20, 10])[0],
            'is_hot': 1 if random.random() < 0.2 else 0,
            'industry': random.choice(INDUSTRIES),
            'employee_count': random.choice([10, 50, 100, 200, 500, 1000]),
            'annual_revenue': random.choice([100000, 500000, 1000000, 5000000, 10000000, 50000000]),
            'city': random.choice(CITIES),
            'country': random.choice(COUNTRIES),
            'assigned_to': random.choice(salespersons),
            'estimated_value': random.randint(5000, 500000),
            'currency': 'AED',
            'lead_score': random.randint(20, 95),
            'age_days': random.randint(0, 90),
            'notes': f"Lead from {random.choice(['trade show', 'referral', 'website inquiry', 'cold call', 'partner channel'])}",
            'created_at': random_date(365, 0),
            'company_id': 1
        }

        conn.execute("""
            INSERT INTO crm_leads (
                lead_number, company_name, contact_name, contact_title, phone, whatsapp,
                email, website, source, status, priority, is_hot, industry, employee_count,
                annual_revenue, city, country, assigned_to, estimated_value, currency,
                lead_score, age_days, notes, created_at, company_id
            ) VALUES (
                :lead_number, :company_name, :contact_name, :contact_title, :phone, :whatsapp,
                :email, :website, :source, :status, :priority, :is_hot, :industry, :employee_count,
                :annual_revenue, :city, :country, :assigned_to, :estimated_value, :currency,
                :lead_score, :age_days, :notes, :created_at, :company_id
            )
        """, lead_data)

    conn.commit()
    print(f"    Created {num_leads} leads")


def seed_crm_lead_activities(conn, num_activities=100):
    """Seed lead activities."""
    print(f"  Creating {num_activities} lead activities...")

    cursor = conn.execute("SELECT id FROM crm_leads LIMIT 20")
    lead_ids = [row['id'] for row in cursor.fetchall()]
    if not lead_ids:
        lead_ids = [1]

    cursor = conn.execute("SELECT id FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%')")
    salespersons = [row['id'] for row in cursor.fetchall()]
    if not salespersons:
        salespersons = [1]

    for i in range(num_activities):
        activity_data = {
            'lead_id': random.choice(lead_ids),
            'activity_type': random.choice(ACTIVITY_TYPES),
            'subject': random.choice([
                'Initial contact made', 'Follow-up call', 'Product demo scheduled',
                'Proposal sent', 'Price negotiation', 'Contract review',
                'Technical discussion', 'Site visit completed', 'Email follow-up'
            ]),
            'activity_date': random_date(180, 0),
            'duration_minutes': random.choice([15, 30, 45, 60, 90, 120]),
            'outcome': random.choice([
                'Positive response', 'Needs follow-up', 'Waiting for feedback',
                'Scheduled next meeting', 'Proposal under review'
            ]),
            'next_follow_up': random_date(30, 0),
            'owner_id': random.choice(salespersons),
            'notes': f"Activity notes for reference"
        }

        conn.execute("""
            INSERT INTO crm_lead_activities (
                lead_id, activity_type, subject, activity_date, duration_minutes,
                outcome, next_follow_up, owner_id, notes
            ) VALUES (
                :lead_id, :activity_type, :subject, :activity_date, :duration_minutes,
                :outcome, :next_follow_up, :owner_id, :notes
            )
        """, activity_data)

    conn.commit()
    print(f"    Created {num_activities} lead activities")


def seed_crm_complaints(conn, num_complaints=20):
    """Seed customer complaints."""
    print(f"  Creating {num_complaints} complaints...")

    cursor = conn.execute("SELECT id FROM sales_customers LIMIT 30")
    customer_ids = [row['id'] for row in cursor.fetchall()]
    if not customer_ids:
        customer_ids = [1]

    cursor = conn.execute("SELECT id FROM sales_orders LIMIT 20")
    order_ids = [row['id'] for row in cursor.fetchall()]
    if not order_ids:
        order_ids = [None]

    cursor = conn.execute("SELECT id FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%')")
    salespersons = [row['id'] for row in cursor.fetchall()]
    if not salespersons:
        salespersons = [1]

    for i in range(num_complaints):
        year = 2026
        complaint_number = generate_complaint_number(conn.cursor(), year)

        complaint_data = {
            'complaint_number': complaint_number,
            'customer_id': random.choice(customer_ids),
            'order_id': random.choice(order_ids + [None, None, None]),
            'delivery_id': None,
            'category': random.choice(COMPLAINT_CATEGORIES),
            'priority': random.choices(COMPLAINT_PRIORITIES, weights=[20, 40, 25, 15])[0],
            'status': random.choices(COMPLAINT_STATUSES, weights=[15, 25, 10, 10, 25, 15])[0],
            'subject': random.choice([
                'Product quality issue', 'Delivery delay', 'Wrong item delivered',
                'Billing discrepancy', 'Pricing concern', 'Service response time',
                'Technical support needed', 'Product malfunction', ' packaging damage'
            ]),
            'description': f"Customer reported an issue that requires immediate attention. Details to follow.",
            'assigned_to': random.choice(salespersons),
            'resolution_target_date': random_date(30, 0),
            'created_at': random_date(90, 0),
            'company_id': 1
        }

        cursor = conn.execute("""
            INSERT INTO crm_complaints (
                complaint_number, customer_id, order_id, delivery_id, category, priority, status,
                subject, description, assigned_to, resolution_target_date, created_at, company_id
            ) VALUES (
                :complaint_number, :customer_id, :order_id, :delivery_id, :category, :priority, :status,
                :subject, :description, :assigned_to, :resolution_target_date, :created_at, :company_id
            )
        """, complaint_data)

        # Add timeline entry
        complaint_id = cursor.lastrowid
        conn.execute("""
            INSERT INTO crm_complaint_timeline (
                complaint_id, event_type, description, created_by, created_at
            ) VALUES (?, 'Created', ?, ?, ?)
        """, (complaint_id, f"Complaint {complaint_number} created", complaint_data['assigned_to'], complaint_data['created_at']))

    conn.commit()
    print(f"    Created {num_complaints} complaints")


def seed_crm_key_accounts(conn, num_accounts=10):
    """Seed key accounts."""
    print(f"  Creating {num_accounts} key accounts...")

    cursor = conn.execute("SELECT id, name FROM sales_customers WHERE is_active = 1 LIMIT 20")
    customers = cursor.fetchall()
    if not customers:
        customers = [(1, 'Sample Customer')]

    cursor = conn.execute("SELECT id FROM users WHERE role_id IN (SELECT id FROM roles WHERE role_name LIKE '%Sales%')")
    salespersons = [row['id'] for row in cursor.fetchall()]
    if not salespersons:
        salespersons = [1]

    for i, customer in enumerate(customers[:num_accounts]):
        account_data = {
            'customer_id': customer['id'],
            'account_name': f"{customer['name']} - Key Account",
            'tier': random.choice(ACCOUNT_TIERS),
            'account_manager_id': random.choice(salespersons),
            'account_type': random.choice(['Strategic', 'Global', 'Regional', 'National']),
            'business_objectives': 'Increase revenue, expand product range, improve satisfaction',
            'success_metrics': 'Revenue growth, order frequency, customer satisfaction',
            'last_review_date': random_date(90, 0),
            'next_review_date': random_date(30, 0),
            'created_at': random_date(365, 0),
            'company_id': 1
        }

        cursor = conn.execute("""
            INSERT INTO crm_key_accounts (
                customer_id, account_name, tier, account_manager_id, account_type,
                business_objectives, success_metrics, last_review_date, next_review_date,
                created_at, company_id
            ) VALUES (
                :customer_id, :account_name, :tier, :account_manager_id, :account_type,
                :business_objectives, :success_metrics, :last_review_date, :next_review_date,
                :created_at, :company_id
            )
        """, account_data)

        # Add objectives
        account_id = cursor.lastrowid
        for obj in ['Revenue Target', 'Order Frequency', 'Customer Satisfaction']:
            conn.execute("""
                INSERT INTO crm_account_objectives (
                    account_id, objective, target_value, current_value, target_date, status
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                account_id, f" Achieve {obj.lower()}",
                random.randint(100000, 1000000),
                random.randint(50000, 800000),
                random_date(365, 0),
                random.choice(['In Progress', 'Achieved', 'On Track'])
            ))

    conn.commit()
    print(f"    Created {num_accounts} key accounts")


def seed_crm_journey_events(conn, num_events=50):
    """Seed customer journey events."""
    print(f"  Creating {num_events} journey events...")

    cursor = conn.execute("SELECT id FROM sales_customers LIMIT 20")
    customer_ids = [row['id'] for row in cursor.fetchall()]
    if not customer_ids:
        customer_ids = [1]

    event_types = ['Awareness', 'Inquiry', 'Quote', 'Purchase', 'Delivery', 'Support', 'Renewal']
    channels = ['Website', 'Phone', 'Email', 'Walk-in', 'Partner', 'Social Media']

    for i in range(num_events):
        event_data = {
            'customer_id': random.choice(customer_ids),
            'event_type': random.choice(event_types),
            'event_date': random_date(365, 0),
            'channel': random.choice(channels),
            'description': random.choice([
                'Customer made first inquiry', 'Quote sent to customer', 'Order placed',
                'Delivery completed', 'Support ticket resolved', 'Contract renewed',
                'New product interest expressed', 'Price negotiation held'
            ]),
            'reference_type': random.choice(['inquiry', 'quotation', 'order', 'delivery', None]),
            'reference_id': random.randint(1, 100),
            'created_at': random_date(365, 0),
            'company_id': 1
        }

        conn.execute("""
            INSERT INTO crm_journey_events (
                customer_id, event_type, event_date, channel, description,
                reference_type, reference_id, created_at, company_id
            ) VALUES (
                :customer_id, :event_type, :event_date, :channel, :description,
                :reference_type, :reference_id, :created_at, :company_id
            )
        """, event_data)

    conn.commit()
    print(f"    Created {num_events} journey events")


def seed_crm_segments(conn):
    """Seed customer segments."""
    print("  Creating customer segments...")

    segments = [
        {'name': 'Premium Customers', 'description': 'High-value customers with frequent purchases'},
        {'name': 'Growth Accounts', 'description': 'Growing customers with increasing order frequency'},
        {'name': 'At Risk', 'description': 'Customers showing signs of churn'},
        {'name': 'New Customers', 'description': 'Recently acquired customers'},
        {'name': 'Dormant', 'description': 'Customers with no activity in 90+ days'},
    ]

    for seg in segments:
        conn.execute("""
            INSERT INTO crm_segments (name, description, is_active) VALUES (?, ?, 1)
        """, (seg['name'], seg['description']))

    conn.commit()
    print(f"    Created {len(segments)} segments")


def main():
    """Run all CRM seeders."""
    print("\n" + "="*60)
    print("CRM Sample Data Seeder")
    print("="*60)

    conn = get_connection()

    try:
        print("\nSeeding CRM data...")

        seed_crm_segments(conn)
        seed_crm_leads(conn, num_leads=50)
        seed_crm_lead_activities(conn, num_activities=100)
        seed_crm_complaints(conn, num_complaints=20)
        seed_crm_key_accounts(conn, num_accounts=10)
        seed_crm_journey_events(conn, num_events=50)

        print("\n" + "="*60)
        print("CRM Sample data seeding completed successfully!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\nError seeding CRM data: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
