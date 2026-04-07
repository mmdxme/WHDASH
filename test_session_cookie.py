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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})

print("Step 1: Get initial page")
r = session.get(base_url, timeout=30)
print(f"  Status: {r.status_code}")

print("\nStep 2: Get CSRF")
r = session.get(f"{base_url}/sanctum/csrf-cookie", timeout=30)
print(f"  Status: {r.status_code}")
print(f"  Cookies: {dict(session.cookies)}")

print("\nStep 3: Login")
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

# Extract token if returned
try:
    data = resp.json()
    api_token = data.get('data', {}).get('token')
    print(f"  API Token: {api_token[:30] if api_token else 'None'}...")
except:
    api_token = None

print("\nStep 4: Try dashboard with session cookies")
r = session.get(f"{base_url}/dashboard/customers", timeout=30)
print(f"  Status: {r.status_code}")
print(f"  Final URL: {r.url}")

if r.status_code == 200:
    # Check if it's Inertia page
    if 'Inertia' in r.text or 'data-page' in r.text:
        print("  Got Inertia page!")
        # Find the page props
        import re
        match = re.search(r'data-page="([^"]+)"', r.text)
        if match:
            print(f"  Found data-page attribute")
        match = re.search(r'window\.page\s*=\s*(\{.*?\});', r.text, re.DOTALL)
        if match:
            print(f"  Found window.page data")
    else:
        print(f"  Content preview: {r.text[:500]}")

print("\nStep 5: Try with Bearer token via headers")
session2 = requests.Session()
session2.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Authorization': f'Bearer {api_token}',
    'Accept': 'application/json',
})

r = session2.get(f"{base_url}/api/user", timeout=30)
print(f"  /api/user: {r.status_code}")
if r.status_code == 200:
    print(f"  Response: {r.text[:300]}")

r = session2.get(f"{base_url}/dashboard/customers", timeout=30)
print(f"  /dashboard/customers: {r.status_code}")
print(f"  URL: {r.url}")