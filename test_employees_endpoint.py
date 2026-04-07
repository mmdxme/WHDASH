"""Test the employees-form-submissions-data-table endpoint"""
import requests
import json

BASE_URL = 'https://panel.sdadparts.com'

def login():
    """Login and maintain session"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    })

    csrf_resp = session.get(f'{BASE_URL}/sanctum/csrf-cookie', timeout=30)
    xsrf_token = session.cookies.get('XSRF-TOKEN', '')
    from urllib.parse import unquote
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
    return session

def test_endpoint(session, endpoint, name):
    """Test an API endpoint"""
    print(f"\n=== {name} ===")
    print(f"Endpoint: {endpoint}")

    r = session.get(f'{BASE_URL}{endpoint}', timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Content-Type: {r.headers.get('Content-Type')}")

    if r.status_code == 200:
        # Check if it's HTML or JSON
        if 'html' in r.headers.get('Content-Type', '').lower():
            print("Response is HTML")
            if len(r.text) < 1000:
                print(f"HTML content: {r.text[:500]}")
            else:
                print(f"HTML length: {len(r.text)}")
        else:
            try:
                data = r.json()
                print(f"JSON type: {type(data)}")
                if isinstance(data, dict):
                    print(f"Keys: {list(data.keys())}")
                    # Print some data
                    for k, v in data.items():
                        if isinstance(v, list):
                            print(f"  {k}: list with {len(v)} items")
                            if v:
                                print(f"    First item: {json.dumps(v[0], indent=2)[:500]}")
                        elif isinstance(v, dict):
                            print(f"  {k}: dict with keys {list(v.keys())}")
                        else:
                            print(f"  {k}: {v}")
                elif isinstance(data, list):
                    print(f"List with {len(data)} items")
                    if data:
                        print(f"First: {json.dumps(data[0], indent=2)[:500]}")
            except Exception as e:
                print(f"JSON error: {e}")
                print(f"Raw: {r.text[:500]}")
    else:
        print(f"Error: {r.text[:300]}")

if __name__ == '__main__':
    session = login()

    # Test the discovered endpoint
    test_endpoint(session, '/api/reports/employees-form-submissions-data-table', 'Employees Form Submissions')

    # Also try other related endpoints
    test_endpoint(session, '/api/employees', 'Direct Employees')
    test_endpoint(session, '/api/reports/employees', 'Reports Employees')

    # Try with different Accept
    session2 = requests.Session()
    csrf_resp = session2.get(f'{BASE_URL}/sanctum/csrf-cookie', timeout=30)
    xsrf_token = session2.cookies.get('XSRF-TOKEN', '')
    from urllib.parse import unquote
    xsrf_token = unquote(xsrf_token)
    login_data = {'email': 'lab@sdadparts.com', 'password': 'Lab!1234'}
    resp = session2.post(f'{BASE_URL}/login', data=login_data, headers={'X-XSRF-TOKEN': xsrf_token}, allow_redirects=True, timeout=30)
    session2.headers.update({'Accept': 'application/json'})
    test_endpoint(session2, '/api/reports/employees-form-submissions-data-table', 'With JSON Accept')
