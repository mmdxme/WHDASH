"""
Debug script to find the actual API endpoints on Peyvast Panel
"""

import os
import re
import requests
from urllib.parse import unquote

# Load .env
env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key.strip(), value.strip())

PEYVAST_BASE_URL = os.environ.get('PEYVAST_BASE_URL', 'https://panel.sdadparts.com')
USERNAME = os.environ.get('PEYVAST_USERNAME', '')
PASSWORD = os.environ.get('PEYVAST_PASSWORD', '')

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})

# Authenticate
print("Authenticating...")
session.get(f"{PEYVAST_BASE_URL}/", timeout=30)
session.get(f"{PEYVAST_BASE_URL}/sanctum/csrf-cookie", timeout=30)
xsrf_token = session.cookies.get('XSRF-TOKEN', '')
xsrf_token = unquote(xsrf_token)

resp = session.post(
    f"{PEYVAST_BASE_URL}/login",
    data={'email': USERNAME, 'password': PASSWORD},
    headers={
        'X-XSRF-TOKEN': xsrf_token,
        'Content-Type': 'application/x-www-form-urlencoded',
    },
    allow_redirects=True,
    timeout=30
)
print(f"Login: {resp.status_code} - {resp.url}")

# Try to access the stock management page and extract API calls
print("\nFetching stock management page...")
stock_url = f"{PEYVAST_BASE_URL}/dashboard/peyvast?page=database%2Fstock-management&role=admin"
resp = session.get(stock_url, timeout=30)
print(f"Page load: {resp.status_code}")

# Look for API endpoints in the HTML/JS
content = resp.text

# Find fetch/axios calls
api_calls = re.findall(r'fetch\s*\(\s*[\'"`]([^\'"`]+)[\'"`]', content)
api_calls += re.findall(r'axios\.(?:get|post)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]', content)
api_calls += re.findall(r'\.get\s*\(\s*[\'"`]([^\'"`]+)[\'"`]', content)
api_calls += re.findall(r'url\s*:\s*[\'"`]([^\'"`]+)[\'"`]', content)

print("\nFound API endpoints:")
seen = set()
for endpoint in api_calls:
    if endpoint not in seen and ('api' in endpoint.lower() or 'data' in endpoint.lower() or 'stock' in endpoint.lower() or 'product' in endpoint.lower() or 'inventory' in endpoint.lower()):
        seen.add(endpoint)
        print(f"  - {endpoint}")

# Look for JSON data in the page
json_patterns = re.findall(r'window\.\w+\s*=\s*(\{.*?\});', content, re.DOTALL)
if json_patterns:
    print("\nFound window.* data objects (first 500 chars each):")
    for i, pattern in enumerate(json_patterns[:5]):
        print(f"  {i+1}. {pattern[:500]}...")

# Try to find Laravel DATA variable
laravel_data = re.findall(r'Data\s*=\s*(\{.*?\});', content, re.DOTALL)
if laravel_data:
    print("\nFound Laravel Data:")
    print(laravel_data[0][:1000])

# Save full page for inspection
with open('stock_page.html', 'w', encoding='utf-8') as f:
    f.write(content)
print(f"\nFull page saved to stock_page.html ({len(content)} bytes)")

# Try specific endpoints that might have more data
print("\n" + "="*60)
print("Testing various endpoints:")
print("="*60)

endpoints_to_test = [
    "/api/products",
    "/api/stock",
    "/api/inventory",
    "/api/warehouses",
    "/dashboard/api/products",
    "/dashboard/api/stock",
    "/dashboard/api/inventory",
    "/dashboard/api/warehouses",
    "/api/v1/products",
    "/api/v1/stock",
]

for endpoint in endpoints_to_test:
    url = f"{PEYVAST_BASE_URL}{endpoint}"
    try:
        resp = session.get(url, timeout=15)
        print(f"{endpoint}: {resp.status_code} ({len(resp.text)} bytes)")
        if resp.status_code == 200 and len(resp.text) > 50:
            try:
                data = resp.json()
                if isinstance(data, dict):
                    print(f"  Keys: {list(data.keys())[:10]}")
                elif isinstance(data, list):
                    print(f"  List length: {len(data)}")
            except:
                print(f"  Content preview: {resp.text[:200]}")
    except Exception as e:
        print(f"{endpoint}: ERROR - {e}")
