"""Test /api/employees endpoint"""
import requests
import json

BASE_URL = 'https://panel.sdadparts.com'

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
})

# Login first
csrf_resp = session.get(f'{BASE_URL}/sanctum/csrf-cookie', timeout=30)
xsrf_token = session.cookies.get('XSRF-TOKEN', '')
from urllib.parse import unquote
xsrf_token = unquote(xsrf_token)

login_data = {'email': 'lab@sdadparts.com', 'password': 'Lab!1234'}
resp = session.post(f'{BASE_URL}/login', data=login_data, headers={'X-XSRF-TOKEN': xsrf_token}, allow_redirects=True, timeout=30)
print(f"Login: {resp.status_code} - {resp.url}")

# Try /api/employees
print("\nFetching /api/employees...")
emp_resp = session.get(f'{BASE_URL}/api/employees', timeout=30)
print(f"Status: {emp_resp.status_code}")
print(f"Content-Type: {emp_resp.headers.get('Content-Type')}")

if emp_resp.status_code == 200:
    try:
        data = emp_resp.json()
        print(f"\nData type: {type(data)}")
        if isinstance(data, dict):
            print(f"Keys: {list(data.keys())}")
            for k, v in data.items():
                if isinstance(v, list):
                    print(f"  {k}: list with {len(v)} items")
                    if v:
                        print(f"    First item keys: {list(v[0].keys()) if isinstance(v[0], dict) else v[0]}")
                        print(f"    Sample: {json.dumps(v[0], indent=2)[:500]}")
                elif isinstance(v, dict):
                    print(f"  {k}: dict with keys {list(v.keys())}")
                else:
                    print(f"  {k}: {v}")
        elif isinstance(data, list):
            print(f"List with {len(data)} items")
            if data:
                print(f"First item: {json.dumps(data[0], indent=2)}")
    except Exception as e:
        print(f"JSON parse error: {e}")
        print(f"Raw response (first 1000 chars): {emp_resp.text[:1000]}")
