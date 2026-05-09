from app import app

# Test just the url_for call for api_export without extending any template
with app.test_request_context():
    from flask import session, url_for
    
    # Set up session data
    session['user_id'] = 1
    session['company_id'] = 1
    session['language'] = 'en'
    session['username'] = 'Test User'
    session['user_role'] = 'Admin'
    
    # Try ONLY the url_for call - without any template rendering
    try:
        url = url_for('dashboard.api_export', export_type='csv')
        print(f'SUCCESS: url_for returned: {url}')
    except Exception as e:
        print(f'ERROR in url_for: {e}')
        import traceback
        traceback.print_exc()
    
    # Now try to render just the url_for expression
    try:
        result = app.jinja_env.compile_expression("{{ url_for('dashboard.api_export', export_type='csv') }}")
        rendered = result()
        print(f'SUCCESS: expression returned: {rendered}')
    except Exception as e:
        print(f'ERROR in expression: {e}')
        import traceback
        traceback.print_exc()