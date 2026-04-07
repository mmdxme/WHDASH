import requests

session = requests.Session()
login_data = {'username': 'admin', 'password': 'admin123'}
session.post('http://localhost:5000/login', data=login_data, allow_redirects=False)

resp = session.get('http://localhost:5000/admin/warehouses')

# Look for flash messages in the HTML
content = resp.text

# Find all div elements with alert, error, warning, success classes
import re

# Flash message patterns
flash_patterns = [
    r'class="[^"]*alert[^"]*"[^>]*>([^<]+)',
    r'class="[^"]*flash[^"]*"[^>]*>([^<]+)',
    r'class="[^"]*error[^"]*"[^>]*>([^<]+)',
    r'class="[^"]*success[^"]*"[^>]*>([^<]+)',
]

for pattern in flash_patterns:
    matches = re.findall(pattern, content, re.IGNORECASE)
    if matches:
        print(f'Pattern {pattern}: {matches[:5]}')

# Find any text that looks like an error message
error_keywords = ['Access Denied', 'Permission', 'You need', 'not authorized', '404', '500', 'Internal Server Error', 'TemplateAssertionError', 'UndefinedError', 'jinja2']
for keyword in error_keywords:
    if keyword.lower() in content.lower():
        idx = content.lower().find(keyword.lower())
        print(f'\nFound "{keyword}" at {idx}:')
        print(content[max(0,idx-50):idx+150].replace('\n', ' '))

# Count actual warehouse rows in the table
wh_rows = re.findall(r'<tr class="wh-row[^"]*"[^>]*>', content)
print(f'\nWarehouse rows found: {len(wh_rows)}')

# Count total option elements in the form
select_options = re.findall(r'<select[^>]*name="company_id"[^>]*>.*?</select>', content, re.DOTALL)
print(f'Company select dropdowns: {len(select_options)}')
