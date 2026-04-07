"""
Test using Bearer token from login response
"""
import requests
import json
import os

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

# Create session for initial login only
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
})

print("=== Bearer Token Auth Test ===\n")

# Step 1: Login and get token
print("1. Login...")
session.get(BASE_URL, timeout=30)
session.get(f"{BASE_URL}/sanctum/csrf-cookie", timeout=30)
resp = session.post(
    f"{BASE_URL}/api/login",
    json={'email': os.environ.get('PEYVAST_USERNAME'), 'password': os.environ.get('PEYVAST_PASSWORD')},
    timeout=30
)
print(f"   Status: {resp.status_code}")
data = resp.json()
token = data.get('data', {}).get('token')
print(f"   Token: {token[:30] if token else 'None'}...")

# Step 2: Create new session with Bearer token
print("\n2. Creating session with Bearer token...")
api_session = requests.Session()
api_session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Authorization': f'Bearer {token}',
})

# Step 3: Try various API endpoints
print("\n3. Testing API endpoints...")

endpoints = [
    '/api/user',
    '/api/dashboard',
    '/api/customers',
    '/dashboard/api/customers',
]

for ep in endpoints:
    r = api_session.get(f"{BASE_URL}{ep}", timeout=15)
    print(f"   GET {ep}: {r.status_code}")
    if r.status_code == 200:
        try:
            d = r.json()
            print(f"     Keys: {list(d.keys())[:5]}")
        except:
            print(f"     Content: {r.text[:100]}")
    else:
        print(f"     Error: {r.text[:100]}")

# Step 4: Try Inertia request
print("\n4. Testing Inertia request...")
inertia_session = requests.Session()
inertia_session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Authorization': f'Bearer {token}',
    'X-Requested-With': 'XMLHttpRequest',
    'X-Inertia': 'true',
})

r = inertia_session.get(f"{BASE_URL}/dashboard/customers", timeout=15)
print(f"   GET /dashboard/customers (Inertia): {r.status_code}")
if r.status_code == 200:
    try:
        d = r.json()
        print(f"   Keys: {list(d.keys())}")
    except:
        print(f"   Content: {r.text[:200]}")
else:
    print(f"   Error: {r.text[:200]}")