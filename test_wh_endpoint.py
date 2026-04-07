import requests

# Login first
session = requests.Session()
login_data = {
    'username': 'admin',
    'password': 'admin123'
}
resp = session.post('http://localhost:5000/login', data=login_data, allow_redirects=False)
print('Login status:', resp.status_code)

# Now access admin/warehouses
resp2 = session.get('http://localhost:5000/admin/warehouses', allow_redirects=False)
print('Warehouses status:', resp2.status_code)
print('Location:', resp2.headers.get('Location', 'None'))
print('Content length:', len(resp2.text))
if resp2.status_code != 200:
    print('Response:', resp2.text[:500])
