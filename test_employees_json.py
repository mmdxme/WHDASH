"""Test the employees JSON endpoint"""
import requests
import json
import re
from urllib.parse import unquote

BASE_URL = 'https://panel.sdadparts.com'

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
})

# Login
csrf_resp = session.get(f'{BASE_URL}/sanctum/csrf-cookie', timeout=30)
xsrf_token = session.cookies.get('XSRF-TOKEN', '')
xsrf_token = unquote(xsrf_token)

login_data = {'email': 'lab@sdadparts.com', 'password': 'Lab!1234'}
resp = session.post(
    f'{BASE_URL}/login',
    data=login_data,
    headers={'X-XSRF-TOKEN': xsrf_token, 'Accept': 'application/json'},
    timeout=30
)
print(f"Login: {resp.status_code}")
print(f"Response: {resp.text[:200]}")

# Try the JSON employees endpoint
print("\n=== /dashboard/employees/json ===")
r = session.get(f'{BASE_URL}/dashboard/employees/json', timeout=30)
print(f"Status: {r.status_code}")
print(f"Content-Type: {r.headers.get('Content-Type')}")
if r.status_code == 200:
    try:
        data = r.json()
        print(f"JSON type: {type(data)}")
        if isinstance(data, dict):
            print(f"Keys: {list(data.keys())}")
            for k, v in data.items():
                if isinstance(v, list):
                    print(f"  {k}: list with {len(v)} items")
                    if v:
                        print(f"    First: {json.dumps(v[0], indent=2)[:500]}")
                elif isinstance(v, dict):
                    print(f"  {k}: dict with keys {list(v.keys())}")
                else:
                    print(f"  {k}: {str(v)[:100]}")
        elif isinstance(data, list):
            print(f"List with {len(data)} items")
            if data:
                print(f"First: {json.dumps(data[0], indent=2)[:500]}")
    except Exception as e:
        print(f"Error: {e}")
        print(f"Raw: {r.text[:500]}")
else:
    print(f"Error: {r.text[:300]}")

# Also try /api/employees
print("\n=== /api/employees ===")
r2 = session.get(f'{BASE_URL}/api/employees', timeout=30)
print(f"Status: {r2.status_code}")
print(f"Content-Type: {r2.headers.get('Content-Type')}")
if r2.status_code == 200:
    try:
        data = r2.json()
        print(f"Data: {json.dumps(data, indent=2)[:500]}")
    except:
        print(f"Raw: {r2.text[:300]}")
else:
    print(f"Error: {r2.text[:300]}")
