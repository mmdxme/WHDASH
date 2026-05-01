import sys
# Ensure no cached modules
for m in list(sys.modules.keys()):
    if 'flask' in m.lower() or 'werkzeug' in m.lower() or 'dashboard' in m.lower():
        del sys.modules[m]

from flask import Flask, Blueprint, url_for

# Create a minimal test app
test_app = Flask(__name__)
test_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@test_bp.route('/api/export/<export_type>')
def api_export(export_type):
    return f'Export {export_type}'

@test_bp.route('/')
def index():
    return url_for('dashboard.api_export', export_type='csv')

test_app.register_blueprint(test_bp)

with test_app.test_request_context():
    result = url_for('dashboard.api_export', export_type='csv')
    print(f'SUCCESS: {result}')