"""Check form routes are registered."""
from app import app

print('Form routes (prefix: /forms):')
count = 0
for rule in app.url_map.iter_rules():
    if rule.rule.startswith('/forms'):
        count += 1
        methods = ','.join(sorted([m for m in rule.methods if m not in ['HEAD', 'OPTIONS']]))
        print(f'  {methods:12} {rule.rule}')

print(f'\nTotal: {count} routes')
