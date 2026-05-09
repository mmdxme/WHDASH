from app import app
from flask import url_for

# Test if we can render a simple template with url_for
test_template = '{{ url_for("dashboard.api_export", export_type="csv") }}'

with app.test_request_context():
    result = app.jinja_env.from_string(test_template).render()
    print(f'Simple test result: {result}')