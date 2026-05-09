import sys
sys.path.insert(0, '.')
from database import get_db

db = get_db()

tables = ['ci_settings','ci_customer_profiles','ci_customer_segments','ci_segment_members',
          'ci_risk_alerts','ci_recommendations','ci_lost_sales','ci_forecast_runs',
          'ci_forecast_lines','ci_financial_profiles','ci_retail_behavior','ci_wholesale_behavior',
          'ci_customer_seasonality','ci_logistics_profiles','ci_customer_demand_history',
          'ci_kpi_records','ci_audit_logs']

print('CI Tables check:')
for t in tables:
    try:
        cnt = db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        print(f'  {t}: OK ({cnt} rows)')
    except Exception as e:
        print(f'  {t}: ERROR - {e}')

# Check sdad_customers
try:
    cnt = db.execute('SELECT COUNT(*) FROM sdad_customers').fetchone()[0]
    locs = db.execute("SELECT location, COUNT(*) as cnt FROM sdad_customers GROUP BY location").fetchall()
    print(f'\nsdad_customers: {cnt} rows')
    for l in locs:
        print(f'  [{l[0]}] = {l[1]}')
except Exception as e:
    print(f'sdad_customers error: {e}')

# Check route registration
print('\nRoute check:')
try:
    from controllers.customer_intelligence_routes import register_ci_routes
    print('  register_ci_routes: IMPORTABLE')
except Exception as e:
    print(f'  register_ci_routes: ERROR - {e}')

db.close()