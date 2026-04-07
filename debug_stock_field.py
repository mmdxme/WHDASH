"""Debug: Check what fields are returned for products"""
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
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
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

# Get first page of reports
r = session.get(f"{BASE_URL}/dashboard/reports/inventory/list?page=1&per_page=5", timeout=60)
data = r.json()

products = data.get('data', {}).get('products', {}).get('data', [])

print("=== Sample product fields ===")
for i, p in enumerate(products[:3]):
    print(f"\nProduct {i+1}:")
    print(f"  All keys: {list(p.keys())}")
    print(f"  barcode: {p.get('barcode')}")
    print(f"  title: {p.get('title')}")
    print(f"  total_stock: {p.get('total_stock')}")
    print(f"  stock: {p.get('stock')}")
    print(f"  quantity: {p.get('quantity')}")
    print(f"  brand_name: {p.get('brand_name')}")

# Also check inventory-list
print("\n\n=== Checking inventory-list ===")
r = session.get(f"{BASE_URL}/dashboard/warehouses/api/inventory-list", timeout=60)
data = r.json()

inventory = data.get('inventory', [])
print(f"Inventory records: {len(inventory)}")
if inventory:
    print(f"\nFirst inventory record keys: {list(inventory[0].keys())}")
    print(f"First inventory: {inventory[0]}")