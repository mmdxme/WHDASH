from app import app

# Test the ACTUAL dashboard route that causes the error
# by simulating what happens when Flask renders the template

with app.test_request_context('/dashboard/', method='GET'):
    from flask import session, render_template_string
    
    # Set up minimal session
    session['user_id'] = 1
    session['company_id'] = 1
    session['language'] = 'en'
    session['username'] = 'Test User'
    session['user_role'] = 'Admin'
    
    # Check the actual URL rules for dashboard
    print('Looking for dashboard.api_export rule...')
    for rule in app.url_map.iter_rules():
        if rule.endpoint == 'dashboard.api_export':
            print(f'  Found: {rule.rule}')
            print(f'  Arguments: {rule.arguments}')
    
    # Now try to use url_for to build the URL
    from flask import url_for
    print()
    print('Testing url_for:')
    try:
        url = url_for('dashboard.api_export', export_type='csv')
        print(f'  SUCCESS: {url}')
    except Exception as e:
        print(f'  ERROR: {type(e).__name__}: {e}')