from app import app
from flask import url_for

# Test with single quotes like the template
test_template = "{{ url_for('dashboard.api_export', export_type='csv') }}"

with app.test_request_context():
    result = app.jinja_env.from_string(test_template).render()
    print(f'Single quotes test result: {result}')

# Test multiple export types
for fmt in ['csv', 'excel_text', 'excel_general', 'json', 'xml', 'txt', 'pdf', 'html']:
    try:
        result = app.jinja_env.from_string("{{ url_for('dashboard.api_export', export_type='" + fmt + "') }}").render()
        print(f'{fmt}: {result}')
    except Exception as e:
        print(f'{fmt}: ERROR - {e}')