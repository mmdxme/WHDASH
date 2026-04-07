"""Debug authentication step by step"""

import os
import requests
import re

# Load .env
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

BASE_URL = os.environ.get('PEYVAST_BASE_URL', 'https://panel.sdadparts.com')
USERNAME = os.environ.get('PEYVAST_USERNAME', '')
PASSWORD = os.environ.get('PEYVAST_PASSWORD', '')

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})

print("=" * 60)
print("AUTHENTICATION DEBUG")
print("=" * 60)

print("\n1. Loading main page...")
r1 = session.get(BASE_URL + "/", timeout=30)
print(f"   Status: {r1.status_code}")
print(f"   Final URL: {r1.url}")

print("\n2. Checking cookies after main page:")
for c in session.cookies:
    print(f"   {c.name}: {c.value[:50] if c.value else 'None'}...")

print("\n3. Getting CSRF from sanctum...")
r2 = session.get(BASE_URL + "/sanctum/csrf-cookie", timeout=30)
print(f"   Status: {r2.status_code}")

print("\n4. Cookies after sanctum:")
for c in session.cookies:
    print(f"   {c.name}: {c.value[:50] if c.value else 'None'}...")

print("\n5. Trying GET /login...")
r3 = session.get(BASE_URL + "/login", timeout=30)
print(f"   Status: {r3.status_code}")
print(f"   Final URL: {r3.url}")

if r3.status_code == 200:
    # Find CSRF token
    match = re.search(r'name="_token"[^>]*value="([^"]+)"', r3.text)
    if match:
        print(f"   Found CSRF token: {match.group(1)[:30]}...")
    else:
        print("   No CSRF token found in form")

    # Find any token-like values
    token_matches = re.findall(r'value="([^"]{20,})"', r3.text)
    if token_matches:
        print(f"   Possible tokens: {token_matches[:3]}")

print("\n6. Trying POST /login with direct approach...")

# Try just email/password without token
r4 = session.post(
    BASE_URL + "/login",
    data={'email': USERNAME, 'password': PASSWORD},
    allow_redirects=True,
    timeout=30
)
print(f"   Status: {r4.status_code}")
print(f"   Final URL: {r4.url}")

print("\n7. Trying to access dashboard directly...")
r5 = session.get(BASE_URL + "/dashboard", timeout=30)
print(f"   Status: {r5.status_code}")
print(f"   Final URL: {r5.url}")

if 'login' not in r5.url.lower():
    print("   SUCCESS: Dashboard accessible!")
else:
    print("   FAILED: Still needs login")

print("\n8. Testing various auth endpoints...")
endpoints = [
    "/api/login",
    "/login",
    "/dashboard/login",
]
for ep in endpoints:
    r = session.post(BASE_URL + ep, data={'email': USERNAME, 'password': PASSWORD}, timeout=15)
    print(f"   POST {ep}: {r.status_code}")
