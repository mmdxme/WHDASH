import traceback
from flask import Flask, session
from marketing_routes import register_marketing_routes

app = Flask(__name__)
app.secret_key = 'test-secret'

# Register the context processor similar to the real app
@app.context_processor
def inject_user_prefs():
    class FakePrefs:
        direction_resolved = 'ltr'
        theme = 'default'
        is_dark = False
        currency_symbol = '$'
        language = 'en'
        interface_direction = 'auto'
    return dict(user_preferences=FakePrefs())

register_marketing_routes(app)

with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['username'] = 'admin'
        sess['role_name'] = 'Global Admin'
        sess['marketing_permissions'] = ['all_marketing']
    resp = client.get('/marketing/campaigns')
    print('Status:', resp.status_code)
    if resp.status_code != 200:
        print('Error:', resp.data[:2000])
    else:
        print('OK - works with context processor')