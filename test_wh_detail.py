import requests

session = requests.Session()
login_data = {'username': 'admin', 'password': 'admin123'}
resp = session.post('http://localhost:5000/login', data=login_data, allow_redirects=False)
print('Login status:', resp.status_code)

resp2 = session.get('http://localhost:5000/admin/warehouses')
content = resp2.text

# Check for error indicators
if 'Error' in content or 'error' in content:
    print('Has error text')

# Check if warehouses appear
if 'Main Warehouse' in content or 'JAFZA' in content:
    print('Warehouse data present')
else:
    print('NO warehouse data!')

# Check if companies appear
if 'AFRA' in content or 'Carmania' in content:
    print('Company data present')
else:
    print('NO company data!')

# Check for jinja template errors
if 'TemplateAssertionError' in content or 'UndefinedError' in content:
    print('TEMPLATE ERROR DETECTED')
    idx = content.find('TemplateAssertionError')
    print(content[idx:idx+500])

# Try POST to add a warehouse
resp3 = session.post('http://localhost:5000/admin/warehouses', data={
    'action': 'add',
    'name': 'Test WH',
    'company_id': '3'
}, allow_redirects=False)
print('\nAdd warehouse status:', resp3.status_code)
print('Add warehouse location:', resp3.headers.get('Location', 'None'))
