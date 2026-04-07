import requests
import json
import os

env_path = '.env'
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

base_url = 'https://panel.sdadparts.com'
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
})

print("Step 1: Get base page")
r = session.get(base_url, timeout=30)
print(f"  Status: {r.status_code}")

print("\nStep 2: Get CSRF cookie")
r = session.get(f"{base_url}/sanctum/csrf-cookie", timeout=30)
print(f"  Status: {r.status_code}")
print(f"  Cookies: {dict(session.cookies)}")

print("\nStep 3: API Login")
resp = session.post(
    f"{base_url}/api/login",
    json={
        'email': os.environ.get('PEYVAST_USERNAME'),
        'password': os.environ.get('PEYVAST_PASSWORD')
    },
    timeout=30
)
print(f"  Status: {resp.status_code}")
print(f"  Cookies after login: {dict(session.cookies)}")

print("\nStep 4: Get dashboard with Inertia headers")
session.headers.update({
    'X-Requested-With': 'XMLHttpRequest',
    'X-Inertia': 'true',
    'Accept': 'application/json',
})

r = session.get(f"{base_url}/dashboard/customers", timeout=30)
print(f"  Status: {r.status_code}")
print(f"  Content-Type: {r.headers.get('Content-Type')}")

if r.status_code == 200:
    try:
        data = r.json()
        print(f"  JSON keys: {list(data.keys())}")
        if 'props' in data:
            print(f"  Props keys: {list(data['props'].keys())}")
    except Exception as e:
        print(f"  Not JSON: {e}")
        print(f"  Preview: {r.text[:500]}")