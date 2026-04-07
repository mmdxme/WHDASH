"""Debug to see if products/search is paginated"""
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

# Try different pages
print("=== Testing /dashboard/products/search ===\n")

for page in [1, 2, 3, 4, 5]:
    url = f"{BASE_URL}/dashboard/products/search"
    params = {'search': '', 'page': page, 'per_page': 500}
    r = session.get(url, params=params, timeout=60)
    data = r.json()

    if isinstance(data, list):
        print(f"Page {page}: {len(data)} items (list)")
    else:
        print(f"Page {page}: type={type(data).__name__}")
        if isinstance(data, dict):
            print(f"  keys: {list(data.keys())}")
            if 'data' in data:
                inner = data['data']
                if isinstance(inner, list):
                    print(f"  data is list: {len(inner)} items")
                elif isinstance(inner, dict):
                    print(f"  data is dict: {list(inner.keys())}")

print("\n=== Now let's see if there are MORE products ===\n")

# Try with empty search but different per_page values
for per_page in [100, 500, 1000]:
    url = f"{BASE_URL}/dashboard/products/search"
    params = {'search': '', 'page': 1, 'per_page': per_page}
    r = session.get(url, params=params, timeout=60)
    data = r.json()

    if isinstance(data, list):
        print(f"per_page={per_page}: {len(data)} items")
    else:
        print(f"per_page={per_page}: response is not a list")