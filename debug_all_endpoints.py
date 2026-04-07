"""Debug to find endpoints with MORE products"""
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
    allow_redirects=True, timeout=30
)

# Try different endpoints
endpoints = [
    "/dashboard/products/search?search=&page=1&per_page=100",
    "/dashboard/warehouses/api/inventory-list",
    "/dashboard/warehouses/api/inventory-list?per_page=1000",
    "/dashboard/reports/inventory/list",
    "/dashboard/reports/inventory/list?page=1&per_page=100",
    "/dashboard/stock-management",
    "/api/stock",
    "/api/products",
    "/dashboard/products",
    "/dashboard/products/all",
    "/api/products/all",
]

print("=== Testing endpoints ===\n")

for ep in endpoints:
    url = BASE_URL + ep
    r = session.get(url, timeout=60)

    try:
        data = r.json()
        if isinstance(data, list):
            print(f"{ep}: {len(data)} items (list)")
        elif isinstance(data, dict):
            keys = list(data.keys())
            print(f"{ep}: dict with keys {keys}")
            # Check for data counts
            for k in ['data', 'products', 'inventory', 'items']:
                if k in data:
                    v = data[k]
                    if isinstance(v, list):
                        print(f"  {k}: {len(v)} items")
                    elif isinstance(v, dict):
                        print(f"  {k}: dict with keys {list(v.keys())}")
    except:
        print(f"{ep}: not JSON (status {r.status_code})")

print("\n=== Testing reports inventory ===")
for page in [1, 2, 3]:
    url = f"{BASE_URL}/dashboard/reports/inventory/list?page={page}&per_page=100"
    r = session.get(url, timeout=60)
    print(f"Page {page}: status={r.status_code}")
    if r.status_code == 200:
        try:
            data = r.json()
            print(f"  keys: {list(data.keys())}")
            if 'data' in data:
                inner = data['data']
                if isinstance(inner, dict):
                    print(f"  data keys: {list(inner.keys())}")
                    prods = inner.get('products', {})
                    if isinstance(prods, dict):
                        print(f"  products keys: {list(prods.keys())}")
                        if 'data' in prods:
                            print(f"  products.data length: {len(prods['data'])}")
                        if 'pagination' in prods:
                            print(f"  pagination: {prods['pagination']}")
        except Exception as e:
            print(f"  error: {e}")