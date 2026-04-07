import requests
import json
import os
import re
import html

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

# Create a single session and use it for all requests
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})

print("=== Testing SDAD Panel Login Flow ===\n")

# Step 1: Get initial page
print("1. GET base URL")
r = session.get(base_url, timeout=30)
print(f"   Status: {r.status_code}")
print(f"   URL after: {r.url}")
print(f"   Cookies: {list(session.cookies.keys())}")

# Step 2: Get CSRF cookie
print("\n2. GET sanctum/csrf-cookie")
r = session.get(f"{base_url}/sanctum/csrf-cookie", timeout=30)
print(f"   Status: {r.status_code}")
print(f"   Cookies: {list(session.cookies.keys())}")

# Step 3: API Login
print("\n3. POST /api/login")
resp = session.post(
    f"{base_url}/api/login",
    json={
        'email': os.environ.get('PEYVAST_USERNAME'),
        'password': os.environ.get('PEYVAST_PASSWORD')
    },
    timeout=30
)
print(f"   Status: {resp.status_code}")
print(f"   Response preview: {resp.text[:200]}")
print(f"   Cookies after: {list(session.cookies.keys())}")
print(f"   Session cookie value length: {len(session.cookies.get('sdadparts_crm_session', ''))}")

# Step 4: Access dashboard (should already be logged in based on session cookie)
print("\n4. GET /dashboard")
r = session.get(f"{base_url}/dashboard", timeout=30)
print(f"   Status: {r.status_code}")
print(f"   URL: {r.url}")
if 'login' in r.url.lower():
    print("   WARNING: Redirected to login!")
else:
    print("   SUCCESS: Dashboard accessible!")
    # Check for Inertia
    if 'Inertia' in r.text or 'data-page' in r.text:
        print("   Inertia page detected!")

# Step 5: Access customers page
print("\n5. GET /dashboard/customers")
r = session.get(f"{base_url}/dashboard/customers", timeout=30)
print(f"   Status: {r.status_code}")
print(f"   URL: {r.url}")
if 'login' in r.url.lower():
    print("   WARNING: Redirected to login!")
else:
    print("   SUCCESS: Customers page accessible!")
    if 'Inertia' in r.text or 'data-page' in r.text:
        print("   Inertia page detected!")
        # Try to extract data
        match = re.search(r'data-page="([^"]+)"', r.text)
        if match:
            data_page_str = html.unescape(match.group(1))
            try:
                data_page = json.loads(data_page_str)
                print(f"   Component: {data_page.get('component')}")
            except:
                pass