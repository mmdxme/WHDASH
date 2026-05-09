from http.client import HTTPConnection
from urllib.parse import urlencode

conn = HTTPConnection('127.0.0.1', 5000)

# Get login page
conn.request('GET', '/login')
resp = conn.getresponse()
print(f"1. GET /login: {resp.status}")
headers = dict(resp.getheaders())
print(f"   Set-Cookie: {headers.get('Set-Cookie', 'None')[:80]}...")

# Post login
body = urlencode({'username': 'admin', 'password': 'admin'})
headers = {'Content-Type': 'application/x-www-form-urlencoded'}
conn.request('POST', '/login', body=body, headers=headers)
resp = conn.getresponse()
print(f"2. POST /login: {resp.status}")
print(f"   Location: {resp.getheader('Location')}")
headers = dict(resp.getheaders())
print(f"   Set-Cookie: {headers.get('Set-Cookie', 'None')[:80] if headers.get('Set-Cookie') else 'None'}...")

# Get index
cookie = headers.get('Set-Cookie', '')
conn.request('GET', '/', headers={'Cookie': cookie})
resp = conn.getresponse()
print(f"3. GET /: {resp.status}")
print(f"   Final URL path: {resp.reason}")