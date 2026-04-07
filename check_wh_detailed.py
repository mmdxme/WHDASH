import requests

# Test with different user accounts to see if permission issue
session = requests.Session()

# Try with admin
login_data = {'username': 'admin', 'password': 'admin123'}
resp = session.post('http://localhost:5000/login', data=login_data, allow_redirects=False)
print('Admin login:', resp.status_code, resp.headers.get('Location', ''))

resp2 = session.get('http://localhost:5000/admin/warehouses')
print('Admin /admin/warehouses:', resp2.status_code)

# Check session cookies
print('Session cookie:', session.cookies.get('session'))

# Check if page has proper content
content = resp2.text
if 'Warehouse Settings' in content:
    print('Page title: Warehouse Settings found')
else:
    print('Page title: Warehouse Settings NOT found')

if 'Main Warehouse' in content or 'JAFZA' in content:
    print('Warehouse data: PRESENT')
else:
    print('Warehouse data: MISSING')

# Check for actual visible warehouse names in table
import re
wh_names = re.findall(r'value="([^"]+)"/>\s*</td>\s*<td[^>]*>\s*<select', content)
print('Warehouse names in forms:', wh_names[:5])
