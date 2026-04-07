import requests

session = requests.Session()

# Get login page
r = session.get('http://127.0.0.1:5000/login')
print(f"1. GET /login: {r.status_code}")

# Try to login
login_data = {
    'username': 'admin',
    'password': 'admin'  # We don't know the actual password
}
r = session.post('http://127.0.0.1:5000/login', data=login_data, allow_redirects=False)
print(f"2. POST /login: {r.status_code}")
print(f"   Location: {r.headers.get('Location', 'None')}")
print(f"   Cookies: {session.cookies.get_dict()}")

if r.status_code == 302:
    # Follow redirect
    r = session.get('http://127.0.0.1:5000/')
    print(f"3. GET / (after redirect): {r.status_code}")
    print(f"   Final URL: {r.url}")