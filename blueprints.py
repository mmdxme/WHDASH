"""Blueprint Registration Module - Centralized route blueprint registration."""
from flask import Flask


def register_all_blueprints(app: Flask):
    """Register all application blueprints."""

    # Import blueprints lazily to avoid circular imports
    from auth_routes import auth_bp
    from navigation import nav_bp
    from dashboard import dashboard_bp
    from wms_routes import register_wms_routes
    from scm_routes import register_scm_routes
    from customer_intelligence_routes import ci_bp
    from btp_routes import register_btp_routes
    from feedback_routes import fb_bp
    from hr_routes import register_hr_routes
    from org_planning_routes import register_org_planning_routes
    from project_routes import register_project_routes
    from sales_suite_routes import register_sales_suite_routes
    from social_media_routes import register_social_media_routes
    from integration_routes import register_integration_routes
    from manufacturing_routes import register_manufacturing_routes
    from spc_routes import register_spc_routes
    from quick_tools_routes import qt_bp

    # Core blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(nav_bp)
    app.register_blueprint(dashboard_bp)

    # Register WMS routes (function-based registration)
    register_wms_routes(app, None)  # get_db is passed at runtime

    # Register SCM routes
    register_scm_routes(app, None)

    # Domain-specific blueprints
    app.register_blueprint(ci_bp)

    # Register BTP routes
    register_btp_routes(app, None)

    # Feedback
    app.register_blueprint(fb_bp)

    # HR
    register_hr_routes(app, None)

    # Organization Planning
    register_org_planning_routes(app, None)

    # Project Management
    register_project_routes(app, None)

    # Sales Suite
    register_sales_suite_routes(app, None)

    # Social Media
    register_social_media_routes(app, None)

    # Integration
    register_integration_routes(app, None)

    # Manufacturing
    register_manufacturing_routes(app, None)

    # SPC (Statistical Process Control)
    register_spc_routes(app, None)

    # Quick Tools
    app.register_blueprint(qt_bp)

    return app