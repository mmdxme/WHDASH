import sys, os
os.environ['SECRET_KEY'] = 'dev-secret-key-for-local-testing-only-1234567890abcdef'
os.environ['FLASK_ENV'] = 'development'
os.environ['DATABASE_PATH'] = 'warehouse.db'
sys.path.insert(0, '.')

# Just test the app_factory.register_all_routes function in isolation
from app_factory import register_all_routes as app_factory_register_all_routes
from application.bootstrap import create_app

app = create_app()

# Do minimal setup
from config import SECRET_KEY, ENV, DEBUG
app.secret_key = SECRET_KEY
app.config['TEMPLATES_AUTO_RELOAD'] = DEBUG
app.jinja_env.auto_reload = DEBUG

print("Calling app_factory.register_all_routes...")
try:
    app_factory_register_all_routes(app)
    print("SUCCESS!")
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()

# Check CI routes
ci_routes = []
for rule in app.url_map.iter_rules():
    if 'customer' in rule.rule.lower():
        ci_routes.append(f'{rule.rule} -> {rule.endpoint}')

print(f"\nTotal routes: {len(list(app.url_map.iter_rules()))}")
print(f"CI routes found: {len(ci_routes)}")
for r in ci_routes:
    print(f"  {r}")