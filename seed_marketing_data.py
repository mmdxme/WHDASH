"""
Seed Marketing Module Demo Data
===============================
Seeds realistic marketing data for testing and demonstration.

Usage:
    python seed_marketing_data.py
    or import and call seed_marketing_data()
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
    """Initialize marketing tables if needed."""
    from marketing_models import run_marketing_migrations
    run_marketing_migrations()


def seed_marketing_data():
    """Seed comprehensive marketing demo data."""
    db = get_db()
    cursor = db.cursor()
    
    print("Seeding Marketing module demo data...")
    
    # Initialize tables
    try:
        initialize_tables()
    except Exception as e:
        print(f"Note: {e}")
    
    # Seed Brands
    print("  Creating brands...")
    brands = [
        ('MMDx Premium', 'Premium', 'BRAND-001', 'High-quality industrial supplies and spare parts for demanding applications', 'Active'),
        ('MMDx Economy', 'Economy', 'BRAND-002', 'Cost-effective solutions without compromising on quality', 'Active'),
        ('MMDx Professional', 'Pro', 'BRAND-003', 'Professional grade products for commercial and industrial use', 'Active'),
        ('MMDx Classic', 'Classic', 'BRAND-004', 'Traditional quality with modern reliability', 'Active'),
    ]
    
    for name, trade, code, desc, status in brands:
        try:
            cursor.execute("""
                INSERT INTO marketing_brands (name, trade_name, code, identity, competitive_advantage, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, trade, code, f'Brand identity for {name}', desc, status, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        except:
            pass
    
    db.commit()
    
    # Seed Market Intelligence
    print("  Creating market intelligence...")
    intel_types = ['Competitor Pricing', 'Market Trend', 'Customer Feedback', 'Industry News']
    
    for i in range(8):
        try:
            cursor.execute("""
                INSERT INTO marketing_market_intelligence (intelligence_type, title, description,
                    source, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                random.choice(intel_types),
                f'Market Intelligence Report {i+1}',
                f'Analysis of market conditions and trends for Q{i+1}',
                random.choice(['Internal Research', 'External Consultant', 'Industry Report', 'Online Research']),
                random.choice(['Active', 'Archived', 'Under Review']),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
        except:
            pass
    
    db.commit()
    
    # Seed Customer Segments
    print("  Creating customer segments...")
    segments = [
        ('Enterprise', 'Large corporate customers with high volume needs', 500000, 'Active'),
        ('Government', 'Government and public sector entities', 300000, 'Active'),
        ('SMB', 'Small and medium businesses', 100000, 'Active'),
        ('Individual', 'Individual consumers', 10000, 'Active'),
        ('Distribution', 'Distribution channel partners', 250000, 'Active'),
    ]
    
    for name, desc, value, status in segments:
        try:
            cursor.execute("""
                INSERT INTO marketing_customer_segments (segment_name, description, estimated_value, status, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (name, desc, value, status, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        except:
            pass
    
    db.commit()
    
    # Seed Marketing Channels
    print("  Creating marketing channels...")
    channels = [
        ('Website', 'Corporate website and landing pages', 'Digital', 'Active'),
        ('Social Media', 'Social media platforms', 'Digital', 'Active'),
        ('Email', 'Email marketing campaigns', 'Digital', 'Active'),
        ('Trade Shows', 'Industry trade shows and exhibitions', 'Events', 'Active'),
        ('Print', 'Print advertising and brochures', 'Traditional', 'Active'),
        ('Referral', 'Referral and word of mouth', 'Organic', 'Active'),
    ]
    
    for name, desc, ctype, status in channels:
        try:
            cursor.execute("""
                INSERT INTO marketing_channels (channel_name, description, channel_type, is_active, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (name, desc, ctype, 1 if status == 'Active' else 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        except:
            pass
    
    db.commit()
    
    # Seed Campaigns
    print("  Creating campaigns...")
    campaigns = [
        ('Spring Sale 2026', 'Campaign', 'EXTERNAL', 'Active', 50000, 'Annual spring promotion'),
        ('Ramadan Promotion', 'Seasonal', 'EXTERNAL', 'Active', 75000, 'Ramadan season offers'),
        ('B2B Outreach Program', 'Lead Generation', 'INTERNAL', 'Active', 25000, 'Targeted B2B leads'),
        ('Brand Awareness Drive', 'Brand Building', 'EXTERNAL', 'Planning', 100000, 'Brand visibility campaign'),
        ('Summer Clearance', 'Campaign', 'EXTERNAL', 'Draft', 30000, 'End of season clearance'),
        ('Industrial Expo 2026', 'Events', 'EXTERNAL', 'Active', 80000, 'Participation in industrial expo'),
    ]
    
    for name, ctype, scope, status, budget, desc in campaigns:
        start = datetime.now()
        end = start + timedelta(days=random.randint(30, 120))
        try:
            cursor.execute("""
                INSERT INTO marketing_campaigns (campaign_name, campaign_type, campaign_scope, status,
                    budget_allocated, start_date, end_date, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, ctype, scope, status, budget, start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'),
                  desc, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        except:
            pass
    
    db.commit()
    
    # Seed Leads
    print("  Creating leads...")
    sources = ['Website', 'Referral', 'Social Media', 'Trade Show', 'Cold Call', 'Partner', 'Email Campaign']
    industries = ['Construction', 'Manufacturing', 'Oil & Gas', 'Retail', 'Government', 'Healthcare', 'Education']
    
    for i in range(20):
        status = random.choice(['New', 'Contacted', 'Qualified', 'Proposal', 'Negotiation', 'Converted', 'Lost'])
        lead_date = datetime.now() - timedelta(days=random.randint(1, 180))
        try:
            cursor.execute("""
                INSERT INTO marketing_leads (lead_number, company_name, contact_name, contact_email,
                    contact_phone, industry, lead_source, status, lead_value, probability,
                    expected_close_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f'LEAD-2026-{i+1:04d}',
                f'Company {i+1} Trading LLC',
                f'Contact Person {i+1}',
                f'contact{i+1}@company{i+1}.com',
                f'+971-50-{random.randint(100, 999)}-{random.randint(1000, 9999)}',
                random.choice(industries),
                random.choice(sources),
                status,
                random.uniform(5000, 500000),
                random.uniform(0.1, 0.9),
                (lead_date + timedelta(days=random.randint(30, 120))).strftime('%Y-%m-%d'),
                lead_date.strftime('%Y-%m-%d %H:%M:%S')
            ))
        except:
            pass
    
    db.commit()
    
    # Seed Funnel Stages
    print("  Creating funnel stages...")
    stages = [
        ('Awareness', 'Lead becomes aware of brand', 1, 100),
        ('Interest', 'Lead shows interest in products', 2, 60),
        ('Consideration', 'Lead is comparing options', 3, 40),
        ('Intent', 'Lead intends to purchase', 4, 25),
        ('Purchase', 'Lead converts to customer', 5, 15),
        ('Retention', 'Customer repeat purchase', 6, 80),
    ]
    
    for name, desc, stage_order, conv_rate in stages:
        try:
            cursor.execute("""
                INSERT INTO marketing_funnel_stages (stage_name, description, stage_order,
                    conversion_rate, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, (name, desc, stage_order, conv_rate, 1))
        except:
            pass
    
    db.commit()
    
    # Seed Offers/Promotions
    print("  Creating offers...")
    offers = [
        ('Spring Discount 20%', 'Discount', 'Spring Sale 2026', 'Active', 20),
        ('Volume Discount', 'Discount', 'B2B Outreach', 'Active', 15),
        ('Free Shipping', 'Promotion', 'Summer Clearance', 'Active', 0),
        ('Bundle Deal', 'Bundle', 'Ramadan Promotion', 'Active', 10),
    ]
    
    for name, otype, campaign, status, discount in offers:
        try:
            cursor.execute("""
                INSERT INTO marketing_offers (offer_name, offer_type, campaign_name, discount_percent,
                    status, start_date, end_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                name, otype, campaign, discount, status,
                datetime.now().strftime('%Y-%m-%d'),
                (datetime.now() + timedelta(days=60)).strftime('%Y-%m-%d'),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
        except:
            pass
    
    db.commit()
    
    # Seed Budgets and Costs
    print("  Creating budgets and costs...")
    budget_items = [
        ('Digital Marketing', 50000, 'Approved'),
        ('Trade Shows', 30000, 'Approved'),
        ('Print Advertising', 15000, 'Approved'),
        ('Content Creation', 20000, 'Pending'),
        ('SEO/SEM', 25000, 'Approved'),
    ]
    
    for item, amount, status in budget_items:
        try:
            cursor.execute("""
                INSERT INTO marketing_budgets (budget_name, allocated_amount, spent_amount,
                    status, fiscal_year, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                item, amount, random.uniform(0, amount * 0.7), status,
                datetime.now().year,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
        except:
            pass
    
    db.commit()
    
    # Seed Performance Metrics
    print("  Creating performance metrics...")
    metrics = [
        ('Website Traffic', 'Sessions', 15000, 18000, 20000),
        ('Lead Generation', 'Leads', 50, 75, 100),
        ('Conversion Rate', 'Percent', 2.5, 3.0, 3.5),
        ('Customer Acquisition Cost', 'AED', 500, 450, 400),
        ('Social Media Followers', 'Count', 5000, 6000, 7500),
    ]
    
    for name, unit, prev, curr, target in metrics:
        try:
            cursor.execute("""
                INSERT INTO marketing_performance_metrics (metric_name, unit_of_measure,
                    previous_value, current_value, target_value, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, unit, prev, curr, target, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        except:
            pass
    
    db.commit()
    
    print("✓ Marketing module seeded successfully")
    db.close()


if __name__ == '__main__':
    seed_marketing_data()