"""
Demo Data Seeds - Customer Intelligence
========================================
Sample/demo data for the Customer Intelligence module.
These seeds populate sdad_customers and all CI supporting tables.

Functions:
  seed_ci_customers()           - 25 sample customers with full CI data
  seed_ci_risk_alerts()         - Sample risk/churn/credit alerts
  seed_ci_recommendations()     - Sample actionable recommendations
  seed_ci_lost_sales()          - Sample lost sales records
  seed_ci_segments()             - Populate segment members
  seed_ci_forecasts()           - Sample forecast runs and lines
  seed_ci_financial_profiles()   - Financial profiles per customer
  seed_ci_retail_behavior()      - Retail behavior profiles
  seed_ci_wholesale_behavior()   - Wholesale behavior profiles
  seed_ci_seasonality()          - Seasonality patterns
  seed_ci_logistics_profiles()   - Logistics profiles
  seed_ci_demand_history()       - Demand history records
"""

import random
from datetime import datetime, timedelta


def seed_ci_customers(db_getter):
    """Seed sample customers into sdad_customers with full CI data."""
    db = db_getter()

    # Check if sdad_customers exists and has data
    try:
        count = db.execute("SELECT COUNT(*) FROM sdad_customers").fetchone()[0]
        if count > 0:
            print("  [SKIP] sdad_customers already has data")
            db.close()
            return
    except Exception:
        pass

    # Ensure sdad_customers table exists with required CI columns
    db.execute('''
        CREATE TABLE IF NOT EXISTS sdad_customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id TEXT UNIQUE,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            phone2 TEXT DEFAULT '',
            email TEXT DEFAULT '',
            website TEXT DEFAULT '',
            country TEXT DEFAULT 'UAE',
            city TEXT DEFAULT 'Dubai',
            state TEXT DEFAULT '',
            address TEXT DEFAULT '',
            locale TEXT DEFAULT '',
            postal_code TEXT DEFAULT '',
            customer_type TEXT DEFAULT '',
            business_type TEXT DEFAULT '',
            is_export INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            is_verified INTEGER DEFAULT 1,
            balance REAL DEFAULT 0.0,
            credit_limit REAL DEFAULT 5000.0,
            total_purchases REAL DEFAULT 0.0,
            total_paid REAL DEFAULT 0.0,
            outstanding REAL DEFAULT 0.0,
            last_purchase_date TEXT DEFAULT '',
            last_purchase_amount REAL DEFAULT 0.0,
            first_purchase_date TEXT DEFAULT '',
            purchase_count INTEGER DEFAULT 0,
            average_purchase REAL DEFAULT 0.0,
            salesperson_id TEXT DEFAULT '',
            salesperson_name TEXT DEFAULT '',
            sales_team TEXT DEFAULT '',
            created_at TEXT DEFAULT '',
            updated_at TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            tags TEXT DEFAULT '',
            local_customer_id INTEGER DEFAULT 0,
            last_synced_at TEXT DEFAULT CURRENT_TIMESTAMP,
            created_at_ts TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at_ts TEXT DEFAULT CURRENT_TIMESTAMP,
            location TEXT DEFAULT 'retail',
            total_orders REAL DEFAULT 0,
            total_payments REAL DEFAULT 0,
            total_debt REAL DEFAULT 0,
            credit_status TEXT DEFAULT 'Good',
            active INTEGER DEFAULT 1,
            last_purchase_date_org TEXT DEFAULT '',
            created_at_org TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Ensure ALTER TABLE for any missing columns
    _add_col_if_safe(db, 'sdad_customers', 'location', "TEXT DEFAULT 'retail'")
    _add_col_if_safe(db, 'sdad_customers', 'total_orders', "REAL DEFAULT 0")
    _add_col_if_safe(db, 'sdad_customers', 'total_payments', "REAL DEFAULT 0")
    _add_col_if_safe(db, 'sdad_customers', 'total_debt', "REAL DEFAULT 0")
    _add_col_if_safe(db, 'sdad_customers', 'credit_status', "TEXT DEFAULT 'Good'")
    _add_col_if_safe(db, 'sdad_customers', 'active', "INTEGER DEFAULT 1")
    _add_col_if_safe(db, 'sdad_customers', 'last_purchase_date_org', "TEXT DEFAULT ''")
    _add_col_if_safe(db, 'sdad_customers', 'created_at_org', "TEXT DEFAULT CURRENT_TIMESTAMP")
    _add_col_if_safe(db, 'sdad_customers', 'payment_method', "TEXT DEFAULT 'Net 30'")
    _add_col_if_safe(db, 'sdad_customers', 'customer_code', "TEXT DEFAULT ''")
    _add_col_if_safe(db, 'sdad_customers', 'username', "TEXT DEFAULT ''")

    db.commit()

    # Realistic UAE/Gulf customer data
    customers = [
        # (name, phone, email, city, country, location, salesperson, total_orders, total_payments, total_debt, credit_limit, active, last_purchase_days_ago)
        ("Al Futtaim Auto Parts", "+971-4-555-0100", "info@alfuttaiauto.ae", "Dubai", "UAE", "wholesale", "Khalid Al-Mansoori", 287500, 265000, 22500, 100000, 1, 3),
        ("Nasser Al-Rashid Trading", "+971-2-555-0200", "contact@nartrading.ae", "Abu Dhabi", "UAE", "wholesale", "Fatima Al-Hassan", 198400, 180000, 18400, 75000, 1, 7),
        ("Gulf Motors LLC", "+971-6-555-0300", "sales@gulfmotors.ae", "Sharjah", "UAE", "retail", "Omar Sheikh", 142300, 142300, 0, 50000, 1, 1),
        ("Emirates Automotive", "+971-4-555-0400", "info@emiratesauto.ae", "Dubai", "UAE", "retail", "Khalid Al-Mansoori", 98500, 90000, 8500, 40000, 1, 5),
        ("Al Bahath Exports", "+971-4-555-0500", "export@albahath.com", "Dubai", "UAE", "export", "Aisha Al-Raís", 312000, 290000, 22000, 150000, 1, 2),
        ("Sharjah Auto Spare", "+971-6-555-0600", "parts@sharjahauto.ae", "Sharjah", "UAE", "wholesale", "Omar Sheikh", 76300, 70000, 6300, 30000, 1, 10),
        ("Abu Dhabi Motors", "+971-2-555-0700", "info@abudhabimotors.ae", "Abu Dhabi", "UAE", "wholesale", "Fatima Al-Hassan", 221000, 205000, 16000, 100000, 1, 4),
        ("Dubai Premium Cars", "+971-4-555-0800", "sales@dubaipremium.ae", "Dubai", "UAE", "retail", "Khalid Al-Mansoori", 65400, 60000, 5400, 25000, 1, 6),
        ("RAK Automotive", "+971-7-555-0900", "info@rakauto.ae", "Ras Al Khaimah", "UAE", "retail", "Hassan Ali", 34200, 31000, 3200, 15000, 1, 8),
        ("Fujairah Trucks Co.", "+971-9-555-1000", "fleet@fujtrucks.ae", "Fujairah", "UAE", "wholesale", "Omar Sheikh", 178600, 160000, 18600, 80000, 1, 12),
        ("Umm Al Quwain Auto", "+971-6-555-1100", "info@uaqauto.ae", "Umm Al Quwain", "UAE", "retail", "Hassan Ali", 18700, 15000, 3700, 10000, 1, 15),
        ("Saudi Arabian Motors", "+966-11-555-2000", "info@saudimotors.com", "Riyadh", "Saudi Arabia", "export", "Aisha Al-Raís", 445000, 420000, 25000, 200000, 1, 2),
        ("Bahrain Auto Parts", "+973-17-555-3000", "parts@bahrainauto.com", "Manama", "Bahrain", "export", "Fatima Al-Hassan", 156000, 145000, 11000, 70000, 1, 5),
        ("Qatar Automotive", "+974-4-555-4000", "info@qatarauto.com", "Doha", "Qatar", "export", "Khalid Al-Mansoori", 287000, 270000, 17000, 130000, 1, 3),
        ("Kuwait Motors Corp", "+965-2-555-5000", "sales@kuwaitmotors.com", "Kuwait City", "Kuwait", "export", "Aisha Al-Raís", 198000, 185000, 13000, 90000, 1, 7),
        ("Muscat Auto Supplies", "+968-24-555-6000", "info@muscatauto.com", "Muscat", "Oman", "export", "Omar Sheikh", 87400, 82000, 5400, 40000, 1, 9),
        ("Al Ain Garage", "+971-3-555-0700", "garage@alaingarage.ae", "Al Ain", "UAE", "retail", "Hassan Ali", 42300, 40000, 2300, 20000, 1, 4),
        ("Jebel Ali Fleet", "+971-4-555-1200", "fleet@jebelalifleet.ae", "Dubai", "UAE", "wholesale", "Khalid Al-Mansoori", 312000, 290000, 22000, 150000, 1, 3),
        # Inactive / high-risk customers
        ("Dried Up Motors", "+971-4-555-9900", "info@driedupmotors.ae", "Dubai", "UAE", "wholesale", "Omar Sheikh", 12500, 8000, 4500, 20000, 0, 120),
        ("Al Wasl Auto", "+971-4-555-8800", "info@waslauto.ae", "Dubai", "UAE", "retail", "Hassan Ali", 8200, 3000, 5200, 15000, 0, 95),
        # New customers
        ("Green Valley Motors", "+971-6-555-7700", "info@greenvalley.ae", "Sharjah", "UAE", "retail", "Fatima Al-Hassan", 12500, 10000, 2500, 10000, 1, 15),
        ("Skyline Automotive", "+971-2-555-6600", "info@skylineauto.ae", "Abu Dhabi", "UAE", "wholesale", "Khalid Al-Mansoori", 45000, 40000, 5000, 25000, 1, 8),
        ("Red Sea Trading", "+966-12-555-2100", "trade@redsea.com", "Jeddah", "Saudi Arabia", "export", "Aisha Al-Raís", 520000, 480000, 40000, 250000, 1, 1),
        ("Oman Gulf Motors", "+968-22-555-6100", "info@omangulf.com", "Muscat", "Oman", "export", "Omar Sheikh", 134000, 120000, 14000, 60000, 1, 6),
        ("Desert Wind Auto", "+971-4-555-5500", "info@desertwind.ae", "Dubai", "UAE", "retail", "Hassan Ali", 29800, 25000, 4800, 15000, 1, 11),
    ]

    now = datetime.now()
    for c in customers:
        name, phone, email, city, country, location, salesperson, total_orders, total_payments, total_debt, credit_limit, active, last_purchase_days = c
        last_purchase = (now - timedelta(days=last_purchase_days)).strftime('%Y-%m-%d')
        created = (now - timedelta(days=random.randint(180, 730))).strftime('%Y-%m-%d')

        # Determine credit_status based on debt
        if total_debt > 0 and total_debt / (total_orders + 1) > 0.15:
            credit_status = 'Risky'
        elif total_debt > credit_limit * 0.8:
            credit_status = 'Warning'
        else:
            credit_status = 'Good'

        # High risk flag
        high_risk = 1 if (active == 0 or last_purchase_days > 90) else 0

        db.execute("""
            INSERT INTO sdad_customers (
                name, phone, email, city, country, location,
                salesperson_name, total_orders, total_payments, total_debt,
                credit_limit, active, last_purchase_date_org, created_at_org,
                credit_status, payment_method, is_credit_blocked, customer_code,
                is_active, last_purchase_date, total_purchases, total_paid, outstanding
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name, phone, email, city, country, location,
            salesperson, total_orders, total_payments, total_debt,
            credit_limit, active, last_purchase, created,
            credit_status, 'Net 30', 1 if high_risk else 0,
            f"CUST-{random.randint(1000,9999)}",
            active, last_purchase, total_orders, total_payments, total_debt
        ))

    db.commit()
    db.close()
    print("  [OK] CI customers seeded")


def seed_ci_risk_alerts(db_getter):
    """Seed sample risk alerts."""
    db = db_getter()

    if db.execute("SELECT COUNT(*) FROM ci_risk_alerts").fetchone()[0] > 0:
        print("  [SKIP] ci_risk_alerts already has data")
        db.close()
        return

    customers = db.execute("SELECT id, name FROM sdad_customers LIMIT 15").fetchall()
    if not customers:
        print("  [SKIP] No customers found for alerts")
        db.close()
        return

    alerts_data = [
        ('churn_risk', 'retention', 'High', 'Immediate sales follow-up recommended.'),
        ('churn_risk', 'retention', 'Medium', 'Schedule customer check-in.'),
        ('credit_risk', 'financial', 'High', 'Review and suspend credit if necessary.'),
        ('growth_opportunity', 'growth', 'High', 'Develop upsell and cross-sell plan.'),
        ('churn_risk', 'retention', 'Medium', 'Send re-engagement offer.'),
        ('credit_risk', 'financial', 'Medium', 'Monitor outstanding balance closely.'),
        ('payment_risk', 'financial', 'Low', 'Review payment history.'),
        ('growth_opportunity', 'growth', 'Medium', 'Propose volume discount.'),
    ]

    now = datetime.now()
    for i, c in enumerate(customers[:10]):
        alert_type, category, level, action = alerts_data[i % len(alerts_data)]
        days_ago = random.randint(1, 30)
        created = (now - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')

        churn_score = round(random.uniform(0.3, 0.9), 2) if alert_type == 'churn_risk' else None
        growth_score = round(random.uniform(0.4, 0.9), 2) if alert_type == 'growth_opportunity' else None
        metric_val = churn_score or growth_score or round(random.uniform(0.5, 0.95), 2)

        title_map = {
            'churn_risk': f'Churn risk detected: {c["name"]}',
            'credit_risk': f'Credit limit concern: {c["name"]}',
            'growth_opportunity': f'Growth opportunity: {c["name"]}',
            'payment_risk': f'Payment delay: {c["name"]}',
        }

        db.execute("""
            INSERT INTO ci_risk_alerts (
                customer_id, alert_type, alert_category, alert_level,
                title, description, metric_value, threshold_value,
                churn_risk_score, growth_opportunity_score, recommended_action, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c['id'], alert_type, category, level,
            title_map.get(alert_type, f'Alert for {c["name"]}'),
            f'Automated monitoring alert for {c["name"]}',
            metric_val, 0.75, churn_score, growth_score, action, created
        ))

    db.commit()
    db.close()
    print("  [OK] CI risk alerts seeded")


def seed_ci_recommendations(db_getter):
    """Seed sample recommendations."""
    db = db_getter()

    if db.execute("SELECT COUNT(*) FROM ci_recommendations").fetchone()[0] > 0:
        print("  [SKIP] ci_recommendations already has data")
        db.close()
        return

    customers = db.execute("SELECT id, name FROM sdad_customers LIMIT 15").fetchall()
    if not customers:
        print("  [SKIP] No customers found for recommendations")
        db.close()
        return

    recs = [
        ('upsell', 'High', 'Launch premium product bundle for top-spending customers', 'cross_sell', 'Champions Package'),
        ('retention', 'High', 'Personalized discount offer for at-risk accounts', 'retention_campaign', 'Win-Back Discount'),
        ('credit_review', 'Medium', 'Conduct quarterly credit limit review', 'credit_management', None),
        ('growth', 'Medium', 'Propose annual supply contract with volume discounts', 'contract_proposal', 'Annual Contract'),
        ('churn_prevention', 'High', 'Schedule executive-level relationship review', 'executive_engagement', 'Executive Meeting'),
        ('upsell', 'Low', 'Introduce new product line during next visit', 'product_launch', 'New Line Introduction'),
        ('payment_improvement', 'Medium', 'Offer early payment incentive (2% discount)', 'payment_terms', 'Early Payment Discount'),
        ('demand_forecast', 'Low', 'Prepare inventory buffer for seasonal demand spike', 'inventory_planning', 'Seasonal Buffer'),
    ]

    now = datetime.now()
    for i, c in enumerate(customers[:12]):
        rec_type, priority, title, action, campaign = recs[i % len(recs)]
        days_ago = random.randint(1, 45)
        created = (now - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
        target = (now + timedelta(days=random.randint(7, 60))).strftime('%Y-%m-%d')
        status = random.choice(['Open', 'Open', 'Open', 'Approved', 'Implemented'])

        db.execute("""
            INSERT INTO ci_recommendations (
                customer_id, recommendation_type, title, description,
                priority, action_category, suggested_campaign, target_date,
                estimated_impact, effort_level, is_approved, is_implemented,
                status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c['id'], rec_type, title,
            f'AI-generated recommendation for {c["name"]}: {title.lower()}.',
            priority, action, campaign, target,
            round(random.uniform(5000, 80000), 0),
            random.choice(['Low', 'Medium', 'High']),
            1 if status in ('Approved', 'Implemented') else 0,
            1 if status == 'Implemented' else 0,
            status, created
        ))

    db.commit()
    db.close()
    print("  [OK] CI recommendations seeded")


def seed_ci_lost_sales(db_getter):
    """Seed sample lost sales records."""
    db = db_getter()

    if db.execute("SELECT COUNT(*) FROM ci_lost_sales").fetchone()[0] > 0:
        print("  [SKIP] ci_lost_sales already has data")
        db.close()
        return

    customers = db.execute("SELECT id, name FROM sdad_customers LIMIT 15").fetchall()
    if not customers:
        print("  [SKIP] No customers found for lost sales")
        db.close()
        return

    reasons = [
        ('Stockout - primary item unavailable', 'Stockout'),
        ('Price 10% higher than competitor', 'Price'),
        ('Competitor offered faster delivery', 'Delivery'),
        ('Customer switched to direct supplier', 'Channel'),
        ('Quality complaint from previous order', 'Quality'),
        ('Credit terms not acceptable', 'Credit'),
        ('Item discontinued, no substitute offered', 'Stockout'),
        ('Late delivery impact on operations', 'Delivery'),
    ]
    competitors = ['AutoZone MENA', 'German Parts International', 'Asia Motors Corp', 'EuroParts Direct', 'GulfSpare LLC', '']

    now = datetime.now()
    for i, c in enumerate(customers[:10]):
        reason, category = reasons[i % len(reasons)]
        days_ago = random.randint(5, 90)
        lost_date = (now - timedelta(days=days_ago)).strftime('%Y-%m-%d')
        lost_amount = round(random.uniform(3000, 45000), 2)
        lost_profit = round(lost_amount * random.uniform(0.15, 0.30), 2)

        db.execute("""
            INSERT INTO ci_lost_sales (
                customer_id, lost_date, reason, reason_category,
                lost_amount, lost_profit, competitor_name,
                follow_up_action, follow_up_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c['id'], lost_date, reason, category,
            lost_amount, lost_profit,
            random.choice(competitors),
            'Follow up scheduled' if i % 3 == 0 else '',
            'Pending review' if i % 2 == 0 else ''
        ))

    db.commit()
    db.close()
    print("  [OK] CI lost sales seeded")


def seed_ci_forecasts(db_getter):
    """Seed sample forecast runs and lines."""
    db = db_getter()

    if db.execute("SELECT COUNT(*) FROM ci_forecast_runs").fetchone()[0] > 0:
        print("  [SKIP] ci_forecast_runs already has data")
        db.close()
        return

    customers = db.execute("SELECT id, name, total_orders FROM sdad_customers LIMIT 20").fetchall()
    if not customers:
        print("  [SKIP] No customers found for forecasts")
        db.close()
        return

    now = datetime.now()
    # Create a completed forecast run
    run_name = f"Monthly Forecast {now.strftime('%B %Y')}"
    period_start = now.strftime('%Y-%m-%d')
    period_end = (now + timedelta(days=90)).strftime('%Y-%m-%d')

    db.execute("""
        INSERT INTO ci_forecast_runs (
            run_name, forecast_type, customer_scope, period_start, period_end,
            granularity, status, total_customers_forecasted, total_demand_forecasted,
            created_at, completed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_name, 'customer_demand', 'all', period_start, period_end,
        'monthly', 'completed', len(customers),
        sum(c['total_orders'] for c in customers if c['total_orders']) * 0.15,
        now.strftime('%Y-%m-%d %H:%M:%S'),
        now.strftime('%Y-%m-%d %H:%M:%S')
    ))
    run_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Create forecast lines
    for c in customers:
        if not c['total_orders'] or c['total_orders'] < 100:
            continue
        monthly_avg = c['total_orders'] / 12
        for month_offset in range(1, 4):
            forecast_date = (now + timedelta(days=30 * month_offset)).strftime('%Y-%m-%d')
            season_factor = 1.0 + 0.2 * (((month_offset % 12) + 3) % 12 / 6 - 1)
            predicted = monthly_avg * season_factor
            confidence = round(random.uniform(0.65, 0.85), 2)

            db.execute("""
                INSERT INTO ci_forecast_lines (
                    run_id, customer_id, forecast_date, period_type,
                    predicted_demand, confidence_level,
                    prediction_interval_low, prediction_interval_high
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id, c['id'], forecast_date, 'monthly',
                round(predicted, 2), confidence,
                round(predicted * 0.8, 2), round(predicted * 1.2, 2)
            ))

    db.commit()
    db.close()
    print("  [OK] CI forecasts seeded")


def seed_ci_financial_profiles(db_getter):
    """Seed financial profiles for customers."""
    db = db_getter()

    if db.execute("SELECT COUNT(*) FROM ci_financial_profiles").fetchone()[0] > 0:
        print("  [SKIP] ci_financial_profiles already has data")
        db.close()
        return

    customers = db.execute("SELECT id, total_orders, total_payments FROM sdad_customers LIMIT 20").fetchall()
    if not customers:
        print("  [SKIP] No customers found for financial profiles")
        db.close()
        return

    for c in customers:
        orders = c['total_orders'] or 0
        payments = c['total_payments'] or 0

        db.execute("""
            INSERT INTO ci_financial_profiles (
                customer_id, avg_purchase_amount, total_yearly_purchase,
                customer_margin, discount_percentage_received,
                net_customer_profit, avg_payment_delay_days,
                payment_discipline_score, credit_utilization,
                profitability_after_service, total_revenue_generated,
                financial_rating
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c['id'],
            round(orders / max(c['purchase_count'], 1), 2) if c.get('purchase_count') else round(orders / 10, 2),
            round(orders, 2),
            round(random.uniform(0.12, 0.28), 3),
            round(random.uniform(0.02, 0.08), 3),
            round(orders * random.uniform(0.08, 0.18), 2),
            round(random.uniform(5, 45), 1),
            round(random.uniform(0.6, 0.95), 2),
            round(random.uniform(0.1, 0.8), 2),
            round(payments * random.uniform(0.85, 0.95), 2),
            round(payments, 2),
            random.randint(1, 5)
        ))

    db.commit()
    db.close()
    print("  [OK] CI financial profiles seeded")


def seed_ci_retail_behavior(db_getter):
    """Seed retail behavior profiles."""
    db = db_getter()

    if db.execute("SELECT COUNT(*) FROM ci_retail_behavior").fetchone()[0] > 0:
        print("  [SKIP] ci_retail_behavior already has data")
        db.close()
        return

    customers = db.execute("""
        SELECT id FROM sdad_customers
        WHERE location NOT IN ('export', 'wholesale')
        LIMIT 15
    """).fetchall()
    if not customers:
        print("  [SKIP] No retail customers for behavior profiles")
        db.close()
        return

    for c in customers:
        db.execute("""
            INSERT INTO ci_retail_behavior (
                customer_id, visits_per_month, avg_basket_value, avg_sku_count,
                avg_time_between_purchases_days, urgent_purchase_ratio,
                loyalty_score, price_sensitivity_score, brand_loyalty_score,
                demand_volatility, preferred_payment_method, preferred_brand,
                accepts_substitutes, prefers_immediate_stock
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c['id'],
            round(random.uniform(1, 8), 1),
            round(random.uniform(200, 3000), 2),
            round(random.uniform(2, 15), 1),
            round(random.uniform(7, 45), 1),
            round(random.uniform(0.05, 0.35), 2),
            round(random.uniform(0.3, 0.9), 2),
            round(random.uniform(0.2, 0.8), 2),
            round(random.uniform(0.3, 0.85), 2),
            round(random.uniform(0.1, 0.6), 2),
            random.choice(['Cash', 'Credit Card', 'Bank Transfer']),
            random.choice(['Bosch', 'Mann', 'Valeo', 'NGK', 'Continental']),
            random.randint(0, 1),
            random.randint(0, 1)
        ))

    db.commit()
    db.close()
    print("  [OK] CI retail behavior seeded")


def seed_ci_wholesale_behavior(db_getter):
    """Seed wholesale behavior profiles."""
    db = db_getter()

    if db.execute("SELECT COUNT(*) FROM ci_wholesale_behavior").fetchone()[0] > 0:
        print("  [SKIP] ci_wholesale_behavior already has data")
        db.close()
        return

    customers = db.execute("""
        SELECT id FROM sdad_customers
        WHERE location IN ('wholesale', 'export')
        LIMIT 15
    """).fetchall()
    if not customers:
        print("  [SKIP] No wholesale customers for behavior profiles")
        db.close()
        return

    for c in customers:
        db.execute("""
            INSERT INTO ci_wholesale_behavior (
                customer_id, avg_order_volume, order_frequency_per_month,
                order_cycle_days, order_regularity_score, payment_discipline_score,
                purchase_growth_rate, brand_stability_score, basket_stability_score,
                customer_lifetime_value, discount_sensitivity, lead_time_sensitivity,
                has_contract, has_reserved_stock, prefers_single_brand
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c['id'],
            round(random.uniform(5000, 80000), 2),
            round(random.uniform(0.5, 6), 1),
            round(random.uniform(15, 90), 1),
            round(random.uniform(0.5, 0.95), 2),
            round(random.uniform(0.6, 0.95), 2),
            round(random.uniform(-0.1, 0.3), 3),
            round(random.uniform(0.5, 0.9), 2),
            round(random.uniform(0.4, 0.85), 2),
            round(random.uniform(100000, 2000000), 2),
            round(random.uniform(0.2, 0.7), 2),
            round(random.uniform(0.3, 0.8), 2),
            random.randint(0, 1),
            random.randint(0, 1),
            random.randint(0, 1)
        ))

    db.commit()
    db.close()
    print("  [OK] CI wholesale behavior seeded")


def seed_ci_seasonality(db_getter):
    """Seed seasonality patterns for customers."""
    db = db_getter()

    if db.execute("SELECT COUNT(*) FROM ci_customer_seasonality").fetchone()[0] > 0:
        print("  [SKIP] ci_customer_seasonality already has data")
        db.close()
        return

    customers = db.execute("SELECT id FROM sdad_customers LIMIT 20").fetchall()
    if not customers:
        print("  [SKIP] No customers for seasonality")
        db.close()
        return

    # Realistic monthly index patterns (UAE auto parts market)
    patterns = [
        [0.6, 0.7, 0.9, 1.0, 1.1, 0.8, 0.5, 0.6, 0.8, 1.0, 1.3, 1.5],  # Standard
        [0.4, 0.5, 0.7, 0.9, 1.2, 1.4, 0.9, 0.5, 0.7, 0.9, 1.1, 1.6],  # Summer peak
        [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.3, 1.1, 1.0, 0.9, 0.8],  # Stable year-round
        [0.5, 0.6, 0.8, 1.1, 1.3, 1.5, 1.2, 0.7, 0.6, 0.8, 1.0, 1.4],  # Ramadan/Eid effect
    ]

    for c in customers:
        pat = random.choice(patterns)
        peak = [i+1 for i, v in enumerate(pat) if v == max(pat)][:3]
        low = [i+1 for i, v in enumerate(pat) if v == min(pat)][:2]

        db.execute("""
            INSERT INTO ci_customer_seasonality (
                customer_id, month_1, month_2, month_3, month_4, month_5, month_6,
                month_7, month_8, month_9, month_10, month_11, month_12,
                peak_month_1, peak_month_2, peak_month_3,
                low_month_1, low_month_2,
                ramadan_effect, eid_effect, summer_effect, winter_effect,
                seasonality_type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c['id'],
            *pat[:12],
            peak[0] if len(peak) > 0 else None,
            peak[1] if len(peak) > 1 else None,
            peak[2] if len(peak) > 2 else None,
            low[0] if len(low) > 0 else None,
            low[1] if len(low) > 1 else None,
            round(random.uniform(0.05, 0.25), 2),
            round(random.uniform(0.1, 0.3), 2),
            round(random.uniform(0.1, 0.4), 2),
            round(random.uniform(0.0, 0.15), 2),
            'seasonal' if max(pat) / min(pat) > 1.5 else 'stable'
        ))

    db.commit()
    db.close()
    print("  [OK] CI seasonality seeded")


def seed_ci_logistics_profiles(db_getter):
    """Seed logistics profiles for customers."""
    db = db_getter()

    if db.execute("SELECT COUNT(*) FROM ci_logistics_profiles").fetchone()[0] > 0:
        print("  [SKIP] ci_logistics_profiles already has data")
        db.close()
        return

    customers = db.execute("SELECT id FROM sdad_customers WHERE location != 'export' LIMIT 20").fetchall()
    if not customers:
        print("  [SKIP] No local customers for logistics profiles")
        db.close()
        return

    for c in customers:
        db.execute("""
            INSERT INTO ci_logistics_profiles (
                customer_id, is_self_pickup, delivery_service_type,
                multiple_deliveries_per_day, consolidated_delivery,
                urgent_delivery_ratio, fixed_vs_changing_location,
                delivery_location_count, delivery_time_sensitivity,
                total_deliveries, cost_per_delivery,
                small_order_ratio, bulk_order_ratio,
                operational_pressure_score, route_complexity_score,
                service_burden_score, avg_delivery_lead_time_hours,
                delivery_success_rate
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            c['id'],
            random.randint(0, 1),
            random.choice(['standard', 'express', 'scheduled']),
            random.randint(0, 1),
            random.randint(0, 1),
            round(random.uniform(0.0, 0.4), 2),
            random.choice(['fixed', 'changing']),
            random.randint(1, 5),
            round(random.uniform(0.1, 0.9), 2),
            random.randint(10, 200),
            round(random.uniform(15, 120), 2),
            round(random.uniform(0.2, 0.7), 2),
            round(random.uniform(0.1, 0.5), 2),
            round(random.uniform(0.2, 0.8), 2),
            round(random.uniform(0.2, 0.75), 2),
            round(random.uniform(0.15, 0.7), 2),
            round(random.uniform(2, 48), 1),
            round(random.uniform(0.85, 0.99), 2)
        ))

    db.commit()
    db.close()
    print("  [OK] CI logistics profiles seeded")


def seed_ci_demand_history(db_getter):
    """Seed demand history for customers."""
    db = db_getter()

    if db.execute("SELECT COUNT(*) FROM ci_customer_demand_history").fetchone()[0] > 0:
        print("  [SKIP] ci_customer_demand_history already has data")
        db.close()
        return

    customers = db.execute("SELECT id, total_orders FROM sdad_customers LIMIT 20").fetchall()
    if not customers:
        print("  [SKIP] No customers for demand history")
        db.close()
        return

    now = datetime.now()
    for c in customers:
        if not c['total_orders'] or c['total_orders'] < 1000:
            continue
        monthly_avg = c['total_orders'] / 12

        for month_offset in range(0, 6):
            record_date = (now - timedelta(days=30 * month_offset)).replace(day=1).strftime('%Y-%m-%d')
            season_factor = 1.0 + 0.2 * (((month_offset % 12) + 3) % 12 / 6 - 1)
            base_demand = monthly_avg * season_factor

            db.execute("""
                INSERT INTO ci_customer_demand_history (
                    customer_id, record_date, period_type,
                    request_count, confirmed_order_count, preorder_count,
                    purchase_count, purchase_amount, conversion_rate,
                    avg_order_value
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c['id'], record_date, 'monthly',
                int(base_demand * random.uniform(1.1, 1.3)),
                int(base_demand * random.uniform(0.85, 1.0)),
                int(base_demand * random.uniform(0.05, 0.15)),
                int(base_demand * random.uniform(0.8, 0.95)),
                round(base_demand * random.uniform(0.8, 1.0), 2),
                round(random.uniform(0.7, 0.9), 2),
                round(base_demand / random.randint(3, 15), 2)
            ))

    db.commit()
    db.close()
    print("  [OK] CI demand history seeded")


def seed_ci_kpi_records(db_getter):
    """Seed KPI snapshot records."""
    db = db_getter()

    if db.execute("SELECT COUNT(*) FROM ci_kpi_records").fetchone()[0] > 0:
        print("  [SKIP] ci_kpi_records already has data")
        db.close()
        return

    customers = db.execute("SELECT id FROM sdad_customers LIMIT 15").fetchall()
    if not customers:
        print("  [SKIP] No customers for KPI records")
        db.close()
        return

    now = datetime.now()
    kpi_names = [
        'monthly_revenue', 'order_count', 'avg_order_value', 'payment_delay_days',
        'credit_utilization', 'churn_risk_score', 'customer_lifetime_value',
        'demand_volatility', 'service_burden_score', 'collection_risk_score'
    ]

    for c in customers:
        for kpi in random.sample(kpi_names, 4):
            period_end = (now - timedelta(days=random.randint(0, 60))).strftime('%Y-%m-%d')
            period_start = (datetime.strptime(period_end, '%Y-%m-%d') - timedelta(days=30)).strftime('%Y-%m-%d')

            db.execute("""
                INSERT INTO ci_kpi_records (
                    customer_id, kpi_name, kpi_category, kpi_value, kpi_unit,
                    period_start, period_end, comparison_value, trend_direction,
                    recorded_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c['id'], kpi, 'financial',
                round(random.uniform(1000, 150000), 2),
                'AED' if 'revenue' in kpi or 'value' in kpi else 'days' if 'delay' in kpi else 'score',
                period_start, period_end,
                round(random.uniform(500, 120000), 2),
                random.choice(['up', 'down', 'stable']),
                now.strftime('%Y-%m-%d %H:%M:%S')
            ))

    db.commit()
    db.close()
    print("  [OK] CI KPI records seeded")


def seed_ci_settings(db_getter):
    """Ensure CI settings row exists."""
    db = db_getter()

    try:
        existing = db.execute("SELECT COUNT(*) FROM ci_settings").fetchone()[0]
        if existing == 0:
            db.execute("INSERT INTO ci_settings (id) VALUES (1)")
            db.commit()
            print("  [OK] CI settings seeded")
        else:
            print("  [SKIP] CI settings already exists")
    except Exception as e:
        print(f"  [WARN] CI settings seed: {e}")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _add_col_if_safe(db, table, column, definition):
    """Add a column if it doesn't exist (safe wrapper)."""
    try:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    except Exception:
        pass
