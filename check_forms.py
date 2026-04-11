"""Check form builder tables."""
from form_models import initialize_form_builder_tables
initialize_form_builder_tables()
print('Tables initialized OK')

from database import get_all
tables = get_all("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'form_%' ORDER BY name")
print(f'Found {len(tables)} form_* tables:')
for t in tables:
    print(f'  - {t["name"]}')
