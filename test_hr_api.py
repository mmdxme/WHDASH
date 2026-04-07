"""Test HR API endpoints on SDAD Panel"""
import requests
import re

BASE_URL = 'https://panel.sdadparts.com'

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})

def test_login():
    """Try to login to the panel"""
    print("Testing login...")
    try:
        # Get CSRF token first
        csrf_resp = session.get(f'{BASE_URL}/sanctum/csrf-cookie', timeout=30)
        xsrf_token = session.cookies.get('XSRF-TOKEN', '')
        if xsrf_token:
            from urllib.parse import unquote
            xsrf_token = unquote(xsrf_token)
            print(f"Got CSRF token: {xsrf_token[:30]}...")

        # Try login
        login_data = {
            'email': 'lab@sdadparts.com',
            'password': 'Lab!1234'
        }
        resp = session.post(
            f'{BASE_URL}/login',
            data=login_data,
            headers={'X-XSRF-TOKEN': xsrf_token},
            allow_redirects=True,
            timeout=30
        )
        print(f"Login response: {resp.status_code} - {resp.url}")

        if 'dashboard' in resp.url.lower() or 'peyvast' in resp.url.lower():
            print("Login successful!")
            return True
    except Exception as e:
        print(f"Login error: {e}")
    return False

def test_hr_endpoints():
    """Test HR-related API endpoints"""
    endpoints = [
        '/api/hr/employees',
        '/api/employees',
        '/api/users',
        '/api/hr/all-employees',
        '/api/v1/employees',
        '/dashboard/hr/employees',
        '/api/employee/all',
        '/api/staff',
        '/api/hr/all',
    ]

    print("\nTesting HR endpoints...")
    for ep in endpoints:
        try:
            r = session.get(f'{BASE_URL}{ep}', timeout=15)
            print(f"{ep}: {r.status_code}")
            if r.status_code == 200 and 'application/json' in r.headers.get('Content-Type', ''):
                print(f"  -> JSON response!")
                try:
                    data = r.json()
                    if isinstance(data, dict):
                        print(f"  -> Keys: {list(data.keys())[:10]}")
                    elif isinstance(data, list):
                        print(f"  -> List with {len(data)} items")
                except:
                    pass
        except Exception as e:
            print(f"{ep}: Error - {str(e)[:50]}")

def test_any_json_endpoints():
    """Find any working JSON endpoints"""
    print("\nLooking for working JSON endpoints...")

    # Try to get dashboard and look for API patterns
    try:
        resp = session.get(f'{BASE_URL}/dashboard', timeout=15)
        print(f"Dashboard: {resp.status_code}")

        # Look for API URLs in the page source
        api_patterns = re.findall(r'["\'](/api/[^"\']+)["\']', resp.text)
        print(f"Found API patterns: {api_patterns[:10]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    if test_login():
        test_hr_endpoints()
        test_any_json_endpoints()
