"""Debug pagination structure"""
import os
import requests
from urllib.parse import unquote

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
USERNAME = os.environ.get('PEYVAST_USERNAME', '')
PASSWORD = os.environ.get('PEYVAST_PASSWORD', '')

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, */*',
})

# Auth
session.get(f"{BASE_URL}/sanctum/csrf-cookie", timeout=30)
xsrf = unquote(session.cookies.get('XSRF-TOKEN', ''))

session.post(
    f"{BASE_URL}/login",
    data={'email': USERNAME, 'password': PASSWORD},
    headers={'X-XSRF-TOKEN': xsrf, 'Content-Type': 'application/x-www-form-urlencoded'},
    allow_redirects=True,
    timeout=30
)

# Test products/search with pagination
print("=== Testing /dashboard/products/search ===\n")

for page in [1, 2, 3]:
    url = f"{BASE_URL}/dashboard/products/search"
    params = {'search': '', 'page': page, 'per_page': 500}
    print(f"Page {page}:")
    r = session.get(url, params=params, timeout=60)
    print(f"  Status: {r.status_code}")

    if r.status_code == 200:
        data = r.json()
        print(f"  Keys: {list(data.keys())}")

        if 'data' in data:
            inner = data['data']
            print(f"  Inner type: {type(inner)}")
            if isinstance(inner, dict):
                print(f"  Inner keys: {list(inner.keys())}")

                # Check for products
                if 'data' in inner:
                    products = inner['data']
                    print(f"  Products type: {type(products)}, length: {len(products) if isinstance(products, list) else 'N/A'}")
                if 'products' in inner:
                    prods = inner['products']
                    print(f"  Products key exists, type: {type(prods)}")
                    if isinstance(prods, dict):
                        print(f"    keys: {list(prods.keys())}")

                # Check for pagination
                if 'pagination' in inner:
                    print(f"  Pagination: {inner['pagination']}")
                if 'products' in inner and isinstance(inner['products'], dict):
                    if 'pagination' in inner['products']:
                        print(f"  Products pagination: {inner['products']['pagination']}")

            elif isinstance(inner, list):
                print(f"  Inner is list, length: {len(inner)}")

    print()