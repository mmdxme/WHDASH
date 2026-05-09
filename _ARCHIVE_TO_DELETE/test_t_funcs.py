import sys
sys.path.insert(0, 'C:/Users/sdads/WHDASH')
exec(open('C:/Users/sdads/WHDASH/translations.py', encoding='utf-8').read())
print('Import OK')
from translations import get_translation, get_translations
print('Functions OK')
print(f"get_translation('fa', 'campaign'): {get_translation('fa', 'campaign')}")
print(f"get_translation('ar', 'workflow'): {get_translation('ar', 'workflow')}")
print(f"get_translation('de', 'save'): {get_translation('de', 'save')}")
print(f"get_translation('zh', 'dashboard'): {get_translation('zh', 'dashboard')}")
print(f"get_translation('es', 'settings'): {get_translation('es', 'settings')}")
print(f"get_translation('hi', 'reports'): {get_translation('hi', 'reports')}")
print(f"get_translation('ru', 'task_center'): {get_translation('ru', 'task_center')}")