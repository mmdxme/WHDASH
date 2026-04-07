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
    'Accept': 'application/json, text/html, */*',
})

print("Step 1: Get base page")
r = session.get(base_url, timeout=30)
print(f"  Status: {r.status_code}")

print("\nStep 2: Get CSRF cookie")
r = session.get(f"{base_url}/sanctum/csrf-cookie", timeout=30)
print(f"  Status: {r.status_code}")

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
print(f"  Response body: {resp.text[:1000]}")

# Check if token is returned
try:
    data = resp.json()
    print(f"  JSON response: {json.dumps(data, indent=2)[:500]}")
except:
    print("  Response is not JSON")

print("\nStep 4: Try dashboard with session cookie")
r = session.get(f"{base_url}/dashboard/customers", timeout=30)
print(f"  Status: {r.status_code}")
print(f"  Final URL: {r.url}")
print(f"  Content preview: {r.text[:300]}")