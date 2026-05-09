import traceback
from flask import Flask, session, got_request_exception
from marketing_routes import register_marketing_routes
from database import get_db
from permissions import get_user_permissions
from translations import get_translation, get_translations

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-for-testing'

# Mimic the real context processor
@app.context_processor
def inject_all():
    from app import build_user_preferences, get_user_preferences, get_main_menu, get_breadcrumbs, get_active_module, get_notification_badge, get_task_badge, get_platform_setting, get_default_theme, get_theme_config, get_theme_tokens, get_chart_palette, get_available_themes, theme_preview_data, get_status_color_classes, get_priority_classes, get_setting, LANGUAGES, is_rtl, get_language_direction, user_has_permission

    def t(key, default=None):
        return get_translation('en', key, default)

    return dict(
        t=t,
        translations={},
        user_preferences=type('obj', (), {'direction_resolved': 'ltr', 'theme': 'default', 'is_dark': False, 'currency_symbol': '$', 'language': 'en', 'interface_direction': 'auto'})()
    )

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
        print('Error:', resp.data[:3000])
    else:
        print('OK')