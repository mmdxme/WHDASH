from app import app

# Get the raw URL map and inspect the dashboard.api_export rule
for rule in app.url_map.iter_rules():
    if rule.endpoint == 'dashboard.api_export':
        print('Found rule for dashboard.api_export')
        print(f'  rule.rule: {repr(rule.rule)}')
        print(f'  rule.arguments: {rule.arguments}')
        print(f'  rule.endpoint: {rule.endpoint}')
        print(f'  rule.methods: {rule.methods}')
        
        # Get more details about the rule
        print(f'  Has __dict__: {hasattr(rule, "__dict__")}')
        if hasattr(rule, '__dict__'):
            print(f'  Rule __dict__: {rule.__dict__}')
        
        # Check the rule's string representation
        print(f'  str(rule): {str(rule)}')
        print(f'  repr(rule): {repr(rule)}')