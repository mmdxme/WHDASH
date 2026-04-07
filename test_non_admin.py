import requests

session = requests.Session()

# Try with a non-admin user (sale01 has role Sales which has can_manage_users=0)
login_data = {'username': 'sale01', 'password': 'sale012023'}
resp = session.post('http://localhost:5000/login', data=login_data, allow_redirects=False)
print('sale01 login:', resp.status_code, resp.headers.get('Location', ''))

resp2 = session.get('http://localhost:5000/admin/warehouses', allow_redirects=False)
print('sale01 /admin/warehouses:', resp2.status_code)
if resp2.status_code == 302:
    print('Redirected to:', resp2.headers.get('Location', ''))

# Check flash message by following redirect
if resp2.status_code == 302:
    resp3 = session.get('http://localhost:5000/admin/warehouses')
    if 'Access Denied' in resp3.text or 'permission' in resp3.text.lower():
        print('Non-admin sees access denied page')

# Try driver1
session2 = requests.Session()
login_data2 = {'username': 'driver1', 'password': 'driver123'}
resp4 = session2.post('http://localhost:5000/login', data=login_data2, allow_redirects=False)
print('\ndriver1 login:', resp4.status_code, resp4.headers.get('Location', ''))

resp5 = session2.get('http://localhost:5000/admin/warehouses', allow_redirects=False)
print('driver1 /admin/warehouses:', resp5.status_code)
if resp5.status_code == 302:
    print('Redirected to:', resp5.headers.get('Location', ''))
