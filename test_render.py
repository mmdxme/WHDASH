from app import app

# Test actually rendering the template that contains the url_for call
with app.test_request_context():
    # Simulate being inside a request
    from flask import session
    
    # Set up session data
    session['user_id'] = 1
    session['company_id'] = 1
    session['language'] = 'en'
    session['username'] = 'Test User'
    session['user_role'] = 'Admin'
    
    # Try to render just a portion of the template - the export section
    template_content = '''
{% extends "base.html" %}
{% block content %}
<section class="dashboard-zone zone-export">
    <a href="{{ url_for('dashboard.api_export', export_type='csv') }}">Export CSV</a>
</section>
{% endblock %}
'''
    
    try:
        result = app.jinja_env.from_string(template_content).render()
        print('SUCCESS: Template rendered correctly')
        print(result[:200])
    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()