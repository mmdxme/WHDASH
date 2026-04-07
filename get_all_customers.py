"""
Extract customers using requests only - since Playwright browser session doesn't persist cookies properly.
The key is to use the same session for login and data access.
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

def get_customers_via_spa_page():
    """Get customers by parsing the SPA dashboard page."""
    customers = []

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })

    print("=== Getting customers via SPA ===\n")

    # Step 1: Login
    print("1. GET base URL...")
    r = session.get(BASE_URL, timeout=30)
    print(f"   Status: {r.status_code}")

    print("\n2. GET sanctum/csrf-cookie...")
    r = session.get(f"{BASE_URL}/sanctum/csrf-cookie", timeout=30)
    print(f"   Status: {r.status_code}")

    print("\n3. POST /api/login...")
    resp = session.post(
        f"{BASE_URL}/api/login",
        json={'email': os.environ.get('PEYVAST_USERNAME'), 'password': os.environ.get('PEYVAST_PASSWORD')},
        timeout=30
    )
    print(f"   Status: {resp.status_code}")
    print(f"   User: {resp.json().get('data', {}).get('user', {}).get('name', 'N/A')}")

    # Step 2: Get the dashboard page (this should work with session cookie)
    print("\n4. GET /dashboard...")
    r = session.get(f"{BASE_URL}/dashboard", timeout=30)
    print(f"   Status: {r.status_code}")
    print(f"   URL: {r.url}")
    print(f"   Final URL: {r.url}")

    # Step 3: Parse any customer data from the page
    print("\n5. Parsing page for customer data...")

    if r.status_code == 200 and 'data-page' in r.text:
        # Extract the Inertia data
        match = re.search(r'data-page="([^"]+)"', r.text)
        if match:
            data_page_str = html.unescape(match.group(1))
            try:
                data_page = json.loads(data_page_str)
                print(f"   Component: {data_page.get('component')}")
                props = data_page.get('props', {})
                print(f"   Props keys: {list(props.keys())}")

                # Check for customer data in props
                for key in props:
                    val = props[key]
                    if isinstance(val, dict):
                        if 'customer' in str(key).lower():
                            print(f"   Found: {key} = {type(val)}")
                    elif isinstance(val, list) and len(val) > 0:
                        first = val[0] if val else None
                        if first and isinstance(first, dict):
                            print(f"   {key}: list[{len(val)}] of dicts, first keys: {list(first.keys())[:5]}")
                        elif first:
                            print(f"   {key}: list[{len(val)}] of {type(first).__name__}")

            except json.JSONDecodeError as e:
                print(f"   JSON error: {e}")

    # Check the cookies
    print("\n6. Session cookies:")
    for c in session.cookies:
        print(f"   {c.name}: {c.value[:50] if c.value else 'None'}...")

    return customers

def get_customers_via_api():
    """Try to get customers via API endpoints that work with Bearer token."""
    customers = []

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
    })

    print("\n\n=== Getting customers via API ===\n")

    # Login to get token
    print("1. Login...")
    r = session.get(BASE_URL, timeout=30)
    r = session.get(f"{BASE_URL}/sanctum/csrf-cookie", timeout=30)
    resp = session.post(
        f"{BASE_URL}/api/login",
        json={'email': os.environ.get('PEYVAST_USERNAME'), 'password': os.environ.get('PEYVAST_PASSWORD')},
        timeout=30
    )
    print(f"   Status: {resp.status_code}")
    data = resp.json()
    token = data.get('data', {}).get('token')
    print(f"   Token: {token[:30] if token else 'None'}...")

    # Now try various endpoints
    print("\n2. Testing API endpoints with Bearer token...")

    api_session = requests.Session()
    api_session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Authorization': f'Bearer {token}',
    })

    endpoints = [
        '/api/reports/general-customers-stats',
        '/api/reports/top-customers',
        '/dashboard/customers',
    ]

    for ep in endpoints:
        r = api_session.get(f"{BASE_URL}{ep}", timeout=15)
        print(f"\n   GET {ep}: {r.status_code}")
        if r.status_code == 200:
            try:
                d = r.json()
                print(f"   Keys: {list(d.keys())[:10]}")
            except:
                print(f"   Content: {r.text[:200]}")
        else:
            print(f"   Error: {r.text[:100]}")

    return customers

if __name__ == "__main__":
    print("=" * 60)
    print("SDAD CUSTOMERS - REQUESTS-BASED")
    print("=" * 60)

    get_customers_via_spa_page()
    get_customers_via_api()