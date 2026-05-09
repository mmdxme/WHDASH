import os
import re

def convert_to_blueprints(controllers_dir):
    for filename in os.listdir(controllers_dir):
        if not filename.endswith('_routes.py'):
            continue
            
        filepath = os.path.join(controllers_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        module_name = filename.replace('_routes.py', '')
        bp_name = f"{module_name}_bp"
        
        # Check if it already has a blueprint
        if f"{bp_name} = Blueprint" in content or "Blueprint(" in content:
            continue
            
        # We need to find the register_..._routes function
        # This regex looks for 'def register_xxx_routes(app...):'
        # and we want to comment it out or adapt it.
        # However, a simpler way is to just inject a Blueprint at the top,
        # and replace @app.route with @bp.route, but if they are nested, 
        # it's tricky.
        
        # Instead, let's inject a blueprint creation and modify the app parameter
        # actually, the easiest way to standardize is to create a dynamic blueprint wrapper
        # inside routes_registry.py. Let's not modify 50 files if it might break.
        pass

if __name__ == "__main__":
    convert_to_blueprints('controllers')
