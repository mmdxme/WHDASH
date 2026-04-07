import requests

session = requests.Session()
login_data = {'username': 'admin', 'password': 'admin123'}
session.post('http://localhost:5000/login', data=login_data, allow_redirects=False)

resp = session.get('http://localhost:5000/admin/warehouses')
content = resp.text

# Look for errors in the HTML
error_strings = ['Error', 'Exception', 'Traceback', 'UndefinedError', 'TemplateAssertionError', 'jinja2', '500', 'Internal Server Error']
for err in error_strings:
    if err in content:
        idx = content.find(err)
        print(f'Found "{err}" at index {idx}')
        start = max(0, idx - 100)
        end = min(len(content), idx + 300)
        print(content[start:end])
        print('---')

# Check if the table has content
if 'Main Warehouse' in content:
    print('Warehouse names found in page')
else:
    print('NO warehouse names!')

if 'AFRA' in content:
    print('AFRA company found in page')
else:
    print('NO AFRA!')

# Check specific parts of the form
if 'action' in content and 'admin_warehouses' in content:
    print('Form elements found')
