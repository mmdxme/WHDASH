"""
Routes Registry Module
======================

Centralized route and blueprint registration.
This module replaces the scattered register_* calls that were in app.py.

Usage:
    from app.routes_registry import register_all_routes, register_blueprints

    app = create_app()
    register_blueprints(app)
    register_all_routes(app)
"""

from flask import Flask, redirect, url_for
import secrets


# ============================================================================
# Module Import Helpers
# ============================================================================

def _import_route_module(module_name: str):
    """Import a route module dynamically."""
    import importlib
    return importlib.import_module(module_name)


def _safe_register(register_func, *args, **kwargs):
    """
    Safely call a register function, catching and logging errors.

    Returns:
        True if successful, False if failed
    """
    try:
        register_func(*args, **kwargs)
        return True
    except Exception as e:
        print(f"Warning: Route registration failed for {register_func.__name__}: {e}")
        return False


# ============================================================================
# Blueprint Registration
# ============================================================================

def register_blueprints(app: Flask) -> None:
    """
    Register all Flask Blueprints with the application.

    Args:
        app: Flask application instance
    """
    # Import blueprints - skip modules that don't exist
    blueprint_imports = [
        ('task_center_routes', 'task_bp'),
        ('issue_tracker_routes', 'issue_bp'),
        ('expense_travel_routes', 'expense_travel_bp'),
        ('dashboard_routes', 'dashboard_bp'),
        ('payroll_routes', 'payroll_bp'),
    ]

    for module_name, bp_name in blueprint_imports:
        try:
            module = __import__(module_name, fromlist=[bp_name])
            bp = getattr(module, bp_name, None)
            if bp is not None:
                if module_name == 'dashboard_routes':
                    app.register_blueprint(bp)
                else:
                    url_prefixs = {
                        'task_center_routes': '/task-center',
                        'issue_tracker_routes': '/issues',
                        'expense_travel_routes': '/expense-travel',
                        'payroll_routes': '/payroll',
                    }
                    app.register_blueprint(bp, url_prefix=url_prefixs.get(module_name, '/'))
        except ImportError:
            print(f"Warning: Blueprint module '{module_name}' not found - skipping")
        except Exception as e:
            print(f"Warning: Blueprint registration failed for {module_name}.{bp_name}: {e}")

    # Redirect root URL to dashboard
    @app.route('/')
    def root_redirect():
        return redirect('/dashboard/')


# ============================================================================
# Route Registration
# ============================================================================

def register_all_routes(app: Flask) -> None:
    """
    Register all module routes with the application using a unified architecture.
    
    This replaces the messy register_* functions and enforces a strict standard
    where every module must expose a Flask Blueprint object (e.g., 'hr_bp').
    """
    import os
    import importlib
    import inspect
    from flask import Blueprint

    # Track registration for summary
    registered = []
    failed = []

    # Dynamically scan the controllers directory for modules
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    controllers_dir = os.path.join(base_dir, 'controllers')
    
    if not os.path.exists(controllers_dir):
        print("Warning: controllers directory not found.")
        return

    for filename in os.listdir(controllers_dir):
        if filename.endswith('_routes.py') or filename.endswith('_controller.py'):
            module_name = filename[:-3]
            
            try:
                # Import the module
                module = importlib.import_module(module_name)
                blueprint_registered = False

                # Scan module for Blueprint instances
                for obj_name, obj in inspect.getmembers(module):
                    if isinstance(obj, Blueprint):
                        # Found a blueprint, register it
                        app.register_blueprint(obj)
                        registered.append(f"{module_name}.{obj_name}")
                        blueprint_registered = True
                        break # Only register the first blueprint found per module

                if not blueprint_registered:
                    failed.append((module_name, "No Blueprint object found in module"))

            except Exception as e:
                failed.append((module_name, str(e)))

    # Print summary
    print(f"Registered {len(registered)} route blueprints dynamically.")
    if failed:
        print(f"Failed to register blueprints for: {[f[0] for f in failed]}")


# ============================================================================
# Health Check Routes
# ============================================================================

def register_health_routes(app: Flask) -> None:
    """
    Register health check endpoints.

    Args:
        app: Flask application instance
    """

    @app.route('/health')
    def health():
        return {'status': 'healthy', 'service': 'MMDx'}, 200

    @app.route('/ready')
    def ready():
        from database import get_db, table_exists

        checks = {}
        healthy = True

        # Database check
        try:
            db = get_db()
            db.execute('SELECT 1').fetchone()
            db.close()
            checks['database'] = 'ok'
        except Exception as e:
            checks['database'] = f'error: {str(e)}'
            healthy = False

        # Schema check
        try:
            schema_ok = table_exists('companies') and table_exists('users')
            checks['schema'] = 'ok' if schema_ok else 'not_initialized'
            if not schema_ok:
                healthy = False
        except Exception as e:
            checks['schema'] = f'error: {str(e)}'
            healthy = False

        status = 200 if healthy else 503
        return {'status': 'ready' if healthy else 'not_ready', 'checks': checks}, status

    @app.route('/live')
    def live():
        return {'status': 'live'}, 200


# ============================================================================
# Module-specific Registration
# ============================================================================

def register_integration_routes(app: Flask) -> None:
    """Register Google Workspace and Email integration routes."""
    try:
        from google_workspace_integration import register_google_workspace
        register_google_workspace(app, get_db)
    except Exception as e:
        print(f"Warning: Google Workspace routes registration failed: {e}")

    try:
        from email_manager import register_email_manager
        register_email_manager(app, get_db)
    except Exception as e:
        print(f"Warning: Email Manager routes registration failed: {e}")


# ============================================================================
# Legacy Redirects
# ============================================================================

def register_redirects(app: Flask) -> None:
    """
    Register redirect routes for backward compatibility.

    Args:
        app: Flask application instance
    """

    @app.route('/supply-chain')
    def supply_chain_redirect():
        return redirect('/scm/')

    @app.route('/scm')
    def scm_redirect():
        from flask import redirect
        return redirect('/scm/')

    @app.route('/wms')
    def wms_redirect():
        from flask import redirect
        return redirect('/wms/')


# ============================================================================
# Import for register_all_routes
# ============================================================================

import importlib