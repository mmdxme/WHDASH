"""Test /api/employees with Inertia SPA session"""
import requests
import json

BASE_URL = 'https://panel.sdadparts.com'

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'X-Inertia': 'true',
    'X-Inertia-Version': 'whatever',
})

from urllib.parse import unquote

def login():
    """Login to panel"""
    csrf_resp = session.get(f'{BASE_URL}/sanctum/csrf-cookie', timeout=30)
    xsrf_token = session.cookies.get('XSRF-TOKEN', '')
    xsrf_token = unquote(xsrf_token)

    login_data = {'email': 'lab@sdadparts.com', 'password': 'Lab!1234'}
    resp = session.post(
        f'{BASE_URL}/login',
        data=login_data,
        headers={'X-XSRF-TOKEN': xsrf_token},
        allow_redirects=True,
        timeout=30
    )
    print(f"Login: {resp.status_code} - {resp.url}")
    return resp

def get_employees():
    """Get employees from API"""
    # Try different Accept types
    headers_list = [
        {'Accept': 'application/json'},
        {'Accept': 'text/html'},
        {'Accept': '*/*'},
        {'Accept': 'text/html,application/json'},
    ]

    for headers in headers_list:
        sess = requests.Session()
        sess.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })

        # Login first
        csrf_resp = sess.get(f'{BASE_URL}/sanctum/csrf-cookie', timeout=30)
        xsrf_token = sess.cookies.get('XSRF-TOKEN', '')
        xsrf_token = unquote(xsrf_token)

        login_data = {'email': 'lab@sdadparts.com', 'password': 'Lab!1234'}
        resp = sess.post(
            f'{BASE_URL}/login',
            data=login_data,
            headers={'X-XSRF-TOKEN': xsrf_token},
            allow_redirects=True,
            timeout=30
        )

        # Now try with different Accept header
        sess.headers.update(headers)
        r = sess.get(f'{BASE_URL}/api/employees', timeout=15)

        print(f"\nAccept: {headers['Accept']}")
        print(f"  Status: {r.status_code}")
        print(f"  Content-Type: {r.headers.get('Content-Type', 'none')}")
        if r.status_code == 200:
            try:
                data = r.json()
                print(f"  JSON data type: {type(data)}")
                if isinstance(data, list):
                    print(f"  List length: {len(data)}")
                    if data:
                        print(f"  First item: {json.dumps(data[0], indent=2)[:300]}")
                elif isinstance(data, dict):
                    print(f"  Dict keys: {list(data.keys())}")
            except Exception as e:
                print(f"  JSON error: {e}")
                print(f"  Raw: {r.text[:300]}")
        else:
            print(f"  Error: {r.text[:200]}")

def get_employees_with_inertia():
    """Try with Inertia headers"""
    login()

    # Now try with Inertia
    session.headers.update({
        'Accept': 'text/html',
        'X-Inertia': 'true',
    })

    r = session.get(f'{BASE_URL}/api/employees', timeout=15)
    print(f"\nWith Inertia headers:")
    print(f"  Status: {r.status_code}")
    print(f"  Content-Type: {r.headers.get('Content-Type')}")

    if r.status_code == 200:
        try:
            data = r.json()
            print(f"  Data: {json.dumps(data, indent=2)[:500]}")
        except:
            print(f"  Raw: {r.text[:500]}")
    else:
        print(f"  Response: {r.text[:300]}")

if __name__ == '__main__':
    print("=== Test 1: Different Accept headers ===")
    get_employees()

    print("\n=== Test 2: With Inertia headers ===")
    get_employees_with_inertia()
