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

print("Step 1: Login")
resp = session.post(
    f"{base_url}/api/login",
    json={
        'email': os.environ.get('PEYVAST_USERNAME'),
        'password': os.environ.get('PEYVAST_PASSWORD')
    },
    timeout=30
)
print(f"  Status: {resp.status_code}")
data = resp.json()
token = data.get('data', {}).get('token')
print(f"  Token: {token[:50] if token else 'None'}...")

print("\nStep 2: Get customers with Bearer token")
session.headers.update({
    'Authorization': f'Bearer {token}',
    'Accept': 'application/json',
})

r = session.get(f"{base_url}/dashboard/customers", timeout=30)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    try:
        d = r.json()
        print(f"  JSON keys: {list(d.keys())}")
        if 'props' in d:
            print(f"  Props keys: {list(d['props'].keys())[:20]}")
    except:
        print(f"  Content: {r.text[:500]}")
else:
    print(f"  Error: {r.text[:300]}")

# Try the search endpoint
print("\nStep 3: Try customers/search endpoint")
r = session.get(f"{base_url}/dashboard/customers/search", timeout=30)
print(f"  Status: {r.status_code}")
if r.status_code == 200:
    try:
        d = r.json()
        print(f"  JSON keys: {list(d.keys())}")
    except:
        print(f"  Content: {r.text[:500]}")