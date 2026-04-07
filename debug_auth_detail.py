"""Debug authentication in detail"""
import os
import requests
from urllib.parse import unquote

env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

BASE_URL = 'https://panel.sdadparts.com'
USERNAME = os.environ.get('PEYVAST_USERNAME', '')
PASSWORD = os.environ.get('PEYVAST_PASSWORD', '')

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})

print("=== Step 1: Get base page ===")
r = session.get(BASE_URL, timeout=30)
print(f"Status: {r.status_code}")
print(f"URL: {r.url}")

print("\n=== Step 2: Get CSRF ===")
r = session.get(f"{BASE_URL}/sanctum/csrf-cookie", timeout=30)
print(f"Status: {r.status_code}")

print("\nCookies after CSRF:")
for c in session.cookies:
    print(f"  {c.name}: {c.value[:50]}...")

xsrf = unquote(session.cookies.get('XSRF-TOKEN', ''))
print(f"\nXSRF Token: {xsrf[:50]}...")

print("\n=== Step 3: Login via POST /login ===")
r = session.post(
    f"{BASE_URL}/login",
    data={'email': USERNAME, 'password': PASSWORD},
    headers={
        'X-XSRF-TOKEN': xsrf,
        'Content-Type': 'application/x-www-form-urlencoded',
    },
    allow_redirects=True,
    timeout=30
)
print(f"Status: {r.status_code}")
print(f"URL: {r.url}")

print("\nCookies after login:")
for c in session.cookies:
    print(f"  {c.name}: {c.value[:50]}...")

print("\n=== Step 4: Try API login ===")
# Reset and try API login
session2 = requests.Session()
session2.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, */*',
})

session2.get(f"{BASE_URL}/sanctum/csrf-cookie", timeout=30)
xsrf2 = unquote(session2.cookies.get('XSRF-TOKEN', ''))

r = session2.post(
    f"{BASE_URL}/api/login",
    json={'email': USERNAME, 'password': PASSWORD},
    timeout=30
)
print(f"API Login Status: {r.status_code}")
print(f"Response: {r.text[:500]}")

print("\nCookies after API login:")
for c in session2.cookies:
    print(f"  {c.name}: {c.value[:50]}...")

print("\n=== Step 5: Try accessing dashboard with session 1 ===")
r = session.get(f"{BASE_URL}/dashboard", timeout=30)
print(f"Status: {r.status_code}")
print(f"URL: {r.url}")

print("\n=== Step 6: Try accessing dashboard with session 2 ===")
r = session2.get(f"{BASE_URL}/dashboard", timeout=30)
print(f"Status: {r.status_code}")
print(f"URL: {r.url}")

print("\n=== Step 7: Try accessing products with session 1 ===")
r = session.get(f"{BASE_URL}/dashboard/products/search", timeout=30)
print(f"products/search Status: {r.status_code}")

print("\n=== Step 8: Try with session 2 ===")
r = session2.get(f"{BASE_URL}/dashboard/products/search", timeout=30)
print(f"products/search Status: {r.status_code}")

# Check if maybe it's a Sanctum token issue
print("\n=== Step 9: Try with Authorization header ===")
# Get the token from API login if available
if r.status_code != 401:
    try:
        data = r.json()
        token = data.get('data', {}).get('token')
        if token:
            print(f"Got token: {token[:30]}...")

            # Try with bearer token
            r = requests.get(
                f"{BASE_URL}/dashboard/products/search",
                headers={
                    'Authorization': f'Bearer {token}',
                    'Accept': 'application/json',
                },
                timeout=30
            )
            print(f"With Bearer: {r.status_code}")
    except:
        pass