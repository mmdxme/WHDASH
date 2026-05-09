from app import app

# Get all dashboard endpoints and their details
print('Dashboard API endpoints detail:')
for rule in app.url_map.iter_rules():
    if 'dashboard.api' in str(rule.endpoint):
        r = rule
        print(f'Endpoint: {r.endpoint}')
        print(f'  Rule: {r.rule}')
        print(f'  Methods: {r.methods}')
        print(f'  Arguments: {r.arguments}')
        print(f'  Endpoint parts: {r.endpoint.split(".")}')
        print()