"""
Direct API approach for SDAD customers - using requests session
"""
import requests
import json
import os
import re
import html

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

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})

print("=== SDAD Customers Direct API ===\n")

# Step 1: Login
print("1. Logging in...")
session.get(BASE_URL, timeout=30)
session.get(f"{BASE_URL}/sanctum/csrf-cookie", timeout=30)
resp = session.post(
    f"{BASE_URL}/api/login",
    json={'email': os.environ.get('PEYVAST_USERNAME'), 'password': os.environ.get('PEYVAST_PASSWORD')},
    timeout=30
)
print(f"   Status: {resp.status_code}")
if resp.status_code != 200:
    print("   FAILED!")
    exit(1)

# Step 2: Get customers page to find API endpoints
print("\n2. Getting customers page to find data...")
r = session.get(f"{BASE_URL}/dashboard/customers", timeout=30)

# Parse Inertia data from page
match = re.search(r'data-page="([^"]+)"', r.text)
if match:
    data_page_str = html.unescape(match.group(1))
    try:
        data_page = json.loads(data_page_str)
        print(f"   Component: {data_page.get('component')}")
        props = data_page.get('props', {})
        print(f"   Props keys: {list(props.keys())}")

        # Look for customer data in various places
        for key in props:
            val = props[key]
            if isinstance(val, list) and len(val) > 0:
                first = val[0] if val else None
                if first:
                    print(f"   {key}: list[{len(val)}] with first item keys: {list(first.keys()) if isinstance(first, dict) else type(first)}")

        # Look for any URL patterns we can query
        if 'filters' in props:
            print(f"   filters: {props['filters']}")
        if 'url' in props:
            print(f"   url: {props['url']}")

    except json.JSONDecodeError as e:
        print(f"   JSON error: {e}")

# Step 3: Look at the JS to find API endpoints
print("\n3. Searching for API URLs in page...")

# Look for fetch/axios URLs
url_patterns = re.findall(r'fetch\(["\']([^"\']+)["\']', r.text)
url_patterns += re.findall(r'axios\.get\(["\']([^"\']+)["\']', r.text)
url_patterns += re.findall(r'route\(["\']([^"\']+)["\']', r.text)
url_patterns = list(set(url_patterns))

# Filter to customer-related URLs
customer_urls = [u for u in url_patterns if 'customer' in u.lower()]
print(f"   Customer-related URLs found: {len(customer_urls)}")
for u in customer_urls[:10]:
    print(f"     {u}")

# Step 4: Try to make direct Inertia requests
print("\n4. Trying direct Inertia requests...")

# Inertia expects these headers
inertia_headers = {
    'X-Requested-With': 'XMLHttpRequest',
    'X-Inertia': 'true',
    'Accept': 'application/json',
}

# Try to get the same page via Inertia
r2 = session.get(f"{BASE_URL}/dashboard/customers", headers=inertia_headers, timeout=30)
print(f"   Status: {r2.status_code}")
if r2.status_code == 200:
    try:
        data = r2.json()
        print(f"   JSON keys: {list(data.keys())}")
        if 'props' in data:
            print(f"   Props keys: {list(data['props'].keys())}")
    except Exception as e:
        print(f"   Error: {e}")

# Try the search endpoint with Inertia headers
r3 = session.get(f"{BASE_URL}/dashboard/customers/search", headers=inertia_headers, timeout=30)
print(f"\n   Search endpoint status: {r3.status_code}")
if r3.status_code == 200:
    try:
        data = r3.json()
        print(f"   JSON keys: {list(data.keys())}")
    except:
        print(f"   Content: {r3.text[:200]}")

print("\nDone.")