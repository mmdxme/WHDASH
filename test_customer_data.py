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
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})

print("Step 1: Login via session cookies")
session.get(base_url, timeout=30)
session.get(f"{base_url}/sanctum/csrf-cookie", timeout=30)
resp = session.post(
    f"{base_url}/api/login",
    json={
        'email': os.environ.get('PEYVAST_USERNAME'),
        'password': os.environ.get('PEYVAST_PASSWORD')
    },
    timeout=30
)
print(f"  Login: {resp.status_code}")

print("\nStep 2: Get customers page")
r = session.get(f"{base_url}/dashboard/customers", timeout=30)
print(f"  Status: {r.status_code}")
print(f"  URL: {r.url}")

# Extract data-page JSON
print("\nStep 3: Parse Inertia data")
match = re.search(r'data-page="([^"]+)"', r.text)
if match:
    data_page_str = match.group(1)
    # Unescape HTML entities
    data_page_str = html.unescape(data_page_str)
    # Parse JSON
    try:
        data_page = json.loads(data_page_str)
        print(f"  Component: {data_page.get('component')}")
        props = data_page.get('props', {})
        print(f"  Props keys: {list(props.keys())[:20]}")

        # Look for customers data
        if 'customers' in props:
            print(f"  Found 'customers' in props!")
            customers = props['customers']
            if isinstance(customers, list):
                print(f"    List with {len(customers)} items")
                if len(customers) > 0:
                    print(f"    First item keys: {list(customers[0].keys()) if isinstance(customers[0], dict) else customers[0]}")
            elif isinstance(customers, dict):
                print(f"    Dict with keys: {list(customers.keys())}")

        # Look for any data that might contain customers
        for key in props.keys():
            if 'customer' in key.lower() or 'data' in key.lower():
                val = props[key]
                if isinstance(val, list) and len(val) > 0:
                    print(f"  {key}: list with {len(val)} items")
                    if isinstance(val[0], dict):
                        print(f"    First item keys: {list(val[0].keys())[:10]}")

    except json.JSONDecodeError as e:
        print(f"  JSON parse error: {e}")
        print(f"  Data preview: {data_page_str[:500]}")
else:
    print("  No data-page found")

# Also look for window.page
print("\nStep 4: Check for window.page")
match = re.search(r'window\.page\s*=\s*(\{.*?\});', r.text, re.DOTALL)
if match:
    print(f"  Found window.page")
    try:
        page_data = json.loads(match.group(1))
        print(f"  Keys: {list(page_data.keys())}")
    except:
        print(f"  Could not parse: {match.group(1)[:200]}")
else:
    print("  No window.page found")