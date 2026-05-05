import sys
sys.path.insert(0, 'C:/Users/sdads/WHDASH')

from permissions import get_user_permissions, get_all_roles
from navigation import get_main_menu, prepare_menu_for_template
from database import get_one
import json

user_id = 1
language = 'en'

user_perms = get_user_permissions(user_id)
menu = get_main_menu(user_id, language)
current_path = '/admin/workflows'

context = {
    'user_id': user_id,
    'username': 'Admin',
    'language': language,
    'direction': 'rtl' if language in ['ar', 'fa'] else 'ltr',
    'menu': prepare_menu_for_template(menu, current_path),
    'permissions': sorted(user_perms) if user_perms else [],
}

context['workflows'] = [{'id': 1, 'workflow_type': 'test', 'module': 'SALES', 'label': 'Test', 'description': '', 'requires_approval': 1, 'is_active': 1}]
context['roles'] = get_all_roles()

print("Roles type:", type(context['roles']))
print("First role permissions type:", type(context['roles'][0]['permissions']) if context['roles'] else 'N/A')
if context['roles']:
    print("First role permissions:", context['roles'][0]['permissions'][:3])

try:
    result = json.dumps(context)
    print("JSON serialization succeeded!")
except Exception as e:
    print(f"JSON serialization failed: {e}")