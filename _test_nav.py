import os
os.environ['DATABASE_PATH'] = 'C:/Users/sdads/WHDASH/database.db'

from database import get_db
db = get_db()
tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print('Tables:', [t['name'] for t in tables])
db.close()

from navigation import get_main_menu, prepare_menu_for_template
import inspect

print('get_main_menu sig:', inspect.signature(get_main_menu))
print('prepare_menu_for_template sig:', inspect.signature(prepare_menu_for_template))

try:
    menu = get_main_menu(1, 'en')
    print('Menu type:', type(menu))
    print('Menu len:', len(menu) if menu else 0)
except Exception as e:
    print('get_main_menu error:', type(e).__name__, e)

try:
    result = prepare_menu_for_template([], '/test')
    print('prepare_menu_for_template works:', result)
except Exception as e:
    print('prepare_menu_for_template error:', type(e).__name__, e)