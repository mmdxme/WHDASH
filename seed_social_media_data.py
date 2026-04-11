"""
Seed Social Media Module Demo Data
=================================
Seeds realistic social media management data for testing and demonstration.

Usage:
    python seed_social_media_data.py
    or import and call seed_social_media_data()
"""

import sqlite3
import os
import random
from datetime import datetime, timedelta

DATABASE = os.path.join(os.path.dirname(__file__), 'warehouse.db')


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def initialize_tables():
    """Initialize social media tables if needed."""
    from social_media_models import run_social_media_migrations
    run_social_media_migrations()


def seed_social_media_data():
    """Seed comprehensive social media demo data."""
    db = get_db()
    cursor = db.cursor()
    
    print("Seeding Social Media module demo data...")
    
    # Initialize tables
    try:
        initialize_tables()
    except Exception as e:
        print(f"Note: {e}")
    
    # Seed Social Accounts
    print("  Creating social accounts...")
    accounts = [
        ('Instagram', 'MMDx_Official', '@MMDx_Official', 'Business', 'Active', '+971-50-123-4567', 'info@whdash.ae'),
        ('LinkedIn', 'MMDx Company', 'MMDx-LLC', 'Business', 'Active', '+971-50-123-4567', 'info@whdash.ae'),
        ('Twitter', 'MMDx', '@MMDx_ae', 'Business', 'Active', '+971-50-123-4567', 'info@whdash.ae'),
        ('Facebook', 'MMDx UAE', 'MMDxuae', 'Business', 'Active', '+971-50-123-4567', 'info@whdash.ae'),
        ('WhatsApp', 'MMDx Business', '+971501234567', 'Business', 'Active', '+971-50-123-4567', 'info@whdash.ae'),
    ]
    
    for platform, name, username, acc_type, status, phone, email in accounts:
        try:
            cursor.execute("""
                INSERT INTO social_accounts (platform, account_name, username, account_type,
                    account_status, phone, connected_email, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (platform, name, username, acc_type, status, phone, email, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        except:
            pass
    
    db.commit()
    
    # Seed Content Calendar entries
    print("  Creating content calendar...")
    content_types = ['Post', 'Story', 'Reel', 'Article', 'Video', 'Carousel']
    statuses = ['Draft', 'Scheduled', 'Published', 'Failed']
    
    for i in range(15):
        pub_date = datetime.now() + timedelta(days=random.randint(-7, 30))
        status = 'Published' if pub_date < datetime.now() else random.choice(['Draft', 'Scheduled'])
        try:
            cursor.execute("""
                INSERT INTO social_content_calendar (content_type, content_caption, platform,
                    publish_date, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                random.choice(content_types),
                f'Exciting news about our latest products and services! #{i+1}',
                random.choice(['Instagram', 'LinkedIn', 'Twitter', 'Facebook']),
                pub_date.strftime('%Y-%m-%d %H:%M:%S'),
                status,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
        except:
            pass
    
    db.commit()
    
    # Seed Content Production
    print("  Creating content production entries...")
    for i in range(10):
        try:
            cursor.execute("""
                INSERT INTO social_content_production (content_type, content_title, content_body,
                    target_platform, content_status, requester, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                random.choice(['Post', 'Story', 'Video', 'Article']),
                f'Content Item {i+1}',
                f'This is the body of content item {i+1} for social media publication.',
                random.choice(['Instagram', 'LinkedIn', 'Twitter', 'Facebook', 'All']),
                random.choice(['Draft', 'In Review', 'Approved', 'Published']),
                'Marketing Team',
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
        except:
            pass
    
    db.commit()
    
    # Seed Publish Queue
    print("  Creating publish queue...")
    for i in range(8):
        try:
            cursor.execute("""
                INSERT INTO social_publish_queue (account_id, content_caption, platform,
                    scheduled_time, publish_status, retry_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                random.randint(1, 5),
                f'Queue post #{i+1} - Check out our latest offerings!',
                random.choice(['Instagram', 'LinkedIn', 'Twitter', 'Facebook']),
                (datetime.now() + timedelta(hours=random.randint(1, 48))).strftime('%Y-%m-%d %H:%M:%S'),
                random.choice(['Pending', 'Published', 'Failed']),
                random.randint(0, 2),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
        except:
            pass
    
    db.commit()
    
    # Seed Social Campaigns
    print("  Creating social campaigns...")
    campaign_types = ['Awareness', 'Traffic', 'Conversion', 'Lead Gen', 'Engagement']
    
    for i in range(6):
        start = datetime.now() - timedelta(days=random.randint(0, 30))
        end = start + timedelta(days=random.randint(14, 60))
        try:
            cursor.execute("""
                INSERT INTO social_campaigns (campaign_name, platform, campaign_type,
                    objective, status, budget, start_date, end_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f'Social Campaign {i+1}',
                random.choice(['Instagram', 'LinkedIn', 'Facebook', 'Twitter', 'Multi']),
                random.choice(campaign_types),
                random.choice(['Reach', 'Traffic', 'Leads', 'Sales']),
                random.choice(['Draft', 'Scheduled', 'Active', 'Paused', 'Completed']),
                random.uniform(1000, 15000),
                start.strftime('%Y-%m-%d'),
                end.strftime('%Y-%m-%d'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
        except:
            pass
    
    db.commit()
    
    # Seed Social Ads
    print("  Creating social ads...")
    ad_statuses = ['Draft', 'Active', 'Paused', 'Completed', 'Rejected']
    
    for i in range(10):
        try:
            cursor.execute("""
                INSERT INTO social_ads (ad_name, platform, campaign_id, ad_type,
                    creative_content, target_audience, budget_daily, bid_strategy,
                    status, impressions, clicks, conversions, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f'Ad Creative {i+1}',
                random.choice(['Instagram', 'LinkedIn', 'Facebook', 'Twitter']),
                random.randint(1, 6),
                random.choice(['Image', 'Video', 'Carousel', 'Stories']),
                f'Ad creative content for campaign #{i+1}',
                f'Audience: Adults 25-54 interested in industrial supplies',
                random.uniform(50, 500),
                random.choice(['CPM', 'CPC', 'CPA', 'CPL']),
                random.choice(ad_statuses),
                random.randint(1000, 50000),
                random.randint(50, 1000),
                random.randint(5, 100),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
        except:
            pass
    
    db.commit()
    
    # Seed Social Leads
    print("  Creating social leads...")
    lead_statuses = ['New', 'Contacted', 'Qualified', 'Nurturing', 'Converted', 'Lost']
    
    for i in range(15):
        try:
            cursor.execute("""
                INSERT INTO social_leads (lead_number, platform, contact_name, contact_email,
                    contact_phone, company, source_post, status, lead_value, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f'SM-LEAD-{i+1:04d}',
                random.choice(['Instagram', 'LinkedIn', 'Facebook', 'Twitter', 'WhatsApp']),
                f'Social Contact {i+1}',
                f'contact{i+1}@social_lead.com',
                f'+971-50-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                f'Company from Social {i+1}',
                f'Post engagement or DM interaction #{i+1}',
                random.choice(lead_statuses),
                random.uniform(1000, 100000),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
        except:
            pass
    
    db.commit()
    
    # Seed Audiences
    print("  Creating audiences...")
    audiences = [
        ('Industrial Buyers', 'Decision makers in manufacturing and construction', 50000, 'Active'),
        ('Fleet Managers', 'Managers of vehicle and equipment fleets', 25000, 'Active'),
        ('Procurement Professionals', 'Procurement officers and buyers', 35000, 'Active'),
        ('Warehouse Managers', 'Operations and warehouse management', 20000, 'Active'),
        ('Government Buyers', 'Government sector procurement', 45000, 'Active'),
    ]
    
    for name, desc, size, status in audiences:
        try:
            cursor.execute("""
                INSERT INTO social_audiences (audience_name, description, audience_size,
                    demographics, interests, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                name, desc, size,
                'Age 25-65, Male/Female, Decision Makers',
                'Industrial equipment, B2B services, Procurement',
                status,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
        except:
            pass
    
    db.commit()
    
    # Seed KPIs
    print("  Creating KPIs...")
    kpis = [
        ('Followers', 'Total followers across platforms', 15000, 18000, 20000),
        ('Engagement Rate', 'Average engagement percentage', 3.5, 4.2, 5.0),
        ('Reach', 'Monthly reach', 100000, 150000, 200000),
        ('Impressions', 'Monthly impressions', 500000, 750000, 1000000),
        ('Leads', 'Leads generated from social', 50, 75, 100),
        ('Conversions', 'Conversions attributed to social', 10, 18, 25),
    ]
    
    for name, desc, prev, curr, target in kpis:
        try:
            cursor.execute("""
                INSERT INTO social_kpis (kpi_name, description, previous_value,
                    current_value, target_value, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, desc, prev, curr, target, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        except:
            pass
    
    db.commit()
    
    # Seed Monitoring keywords
    print("  Creating monitoring entries...")
    keywords = ['MMDx', 'Warehouse Management', 'Industrial Supplies UAE', 'Spare Parts Dubai']
    
    for keyword in keywords:
        try:
            cursor.execute("""
                INSERT INTO social_monitoring (keyword, platform, sentiment_trend,
                    mentions, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                keyword,
                random.choice(['Instagram', 'LinkedIn', 'Twitter', 'Facebook', 'All']),
                random.choice(['Positive', 'Neutral', 'Negative']),
                random.randint(10, 500),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
        except:
            pass
    
    db.commit()
    
    print("✓ Social Media module seeded successfully")
    db.close()


if __name__ == '__main__':
    seed_social_media_data()