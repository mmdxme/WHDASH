import sys
import os
os.environ['SECRET_KEY'] = 'dev-secret-key-for-local-testing-only-1234567890abcdef'
os.environ['FLASK_ENV'] = 'development'
os.environ['DATABASE_PATH'] = 'warehouse.db'

sys.path.insert(0, '.')

import importlib
import inspect
from flask import Blueprint

# Test customer_intelligence_routes directly
print("=== Testing customer_intelligence_routes import ===")
try:
    module = importlib.import_module('controllers.customer_intelligence_routes')
    print("Module imported OK")

    blueprint_registered = False
    for obj_name, obj in inspect.getmembers(module):
        if isinstance(obj, Blueprint):
            print(f"  Found Blueprint: {obj_name} (name={obj.name})")
            blueprint_registered = True

    if not blueprint_registered:
        print("  No Blueprint found in module!")
        # Check what's in the module
        print("  Module members:")
        for name, obj in inspect.getmembers(module):
            if not name.startswith('_'):
                print(f"    {name}: {type(obj).__name__}")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()

# Now test if register_ci_routes works
print("\n=== Testing register_ci_routes ===")
try:
    from controllers.customer_intelligence_routes import register_ci_routes
    print(f"register_ci_routes: {register_ci_routes}")

    # Try calling it
    from application.bootstrap import create_app
    app = create_app()
    app.secret_key = 'dev'
    register_ci_routes(app)
    print("register_ci_routes(app) succeeded!")

    # Check routes
    ci_routes = []
    for rule in app.url_map.iter_rules():
        if 'customer' in rule.rule.lower() or 'ci_' in rule.endpoint:
            ci_routes.append(f"  {rule.rule} -> {rule.endpoint}")

    if ci_routes:
        print("\n=== CI Routes Found ===")
        for r in ci_routes:
            print(r)
    else:
        print("\n=== NO CI ROUTES registered ===")

except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()