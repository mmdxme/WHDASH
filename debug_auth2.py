"""Debug cookies after API login"""

import os
import requests
import json

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
    'Accept': 'application/json, */*',
})

print("=" * 60)
print("COOKIE DEBUG AFTER API LOGIN")
print("=" * 60)

# Step 1: Initial cookies
print("\n1. Getting initial cookies...")
session.get(BASE_URL + "/", timeout=30)
session.get(BASE_URL + "/sanctum/csrf-cookie", timeout=30)

print("\nCookies after initial load:")
for c in session.cookies:
    print(f"   {c.name}: {c.value[:50] if c.value else 'None'}...")

# Step 2: API login
print("\n2. API login...")
resp = session.post(
    BASE_URL + "/api/login",
    json={'email': USERNAME, 'password': PASSWORD},
    timeout=30
)
print(f"   Status: {resp.status_code}")
print(f"   Response: {resp.text[:300]}...")

print("\nCookies after API login:")
for c in session.cookies:
    print(f"   {c.name}: {c.value[:50] if c.value else 'None'}...")

# Step 3: Try various endpoints
print("\n3. Testing various endpoints...")
endpoints = [
    "/dashboard",
    "/dashboard/",
    "/dashboard/peyvast",
    "/dashboard/peyvast?page=database%2Fstock-management",
    "/api/user/info",
    "/api/brands/all",
]

for ep in endpoints:
    r = session.get(BASE_URL + ep, timeout=15)
    print(f"   GET {ep}: {r.status_code}")
    if r.status_code == 200:
        try:
            data = r.json()
            if isinstance(data, dict):
                print(f"      Keys: {list(data.keys())[:5]}")
            elif isinstance(data, list):
                print(f"      List length: {len(data)}")
        except:
            print(f"      Content preview: {r.text[:100]}")

# Step 4: Try accessing with Accept header
print("\n4. Testing with Accept: text/html...")
r = session.get(BASE_URL + "/dashboard", headers={'Accept': 'text/html'}, timeout=15)
print(f"   GET /dashboard: {r.status_code}")
print(f"   Final URL: {r.url}")
