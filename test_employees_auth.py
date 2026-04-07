"""Test /api/employees with Bearer token"""
import requests
import json
import re

BASE_URL = 'https://panel.sdadparts.com'

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Referer': f'{BASE_URL}/dashboard',
})

def login_and_get_token():
    """Login and extract bearer token"""
    # Get CSRF token
    csrf_resp = session.get(f'{BASE_URL}/sanctum/csrf-cookie', timeout=30)
    xsrf_token = session.cookies.get('XSRF-TOKEN', '')
    xsrf_token = unquote(xsrf_token) if xsrf_token else ''

    # Login
    login_data = {'email': 'lab@sdadparts.com', 'password': 'Lab!1234'}
    resp = session.post(
        f'{BASE_URL}/login',
        data=login_data,
        headers={
            'X-XSRF-TOKEN': xsrf_token,
            'Accept': 'application/json',
        },
        allow_redirects=True,
        timeout=30
    )
    print(f"Login: {resp.status_code} - {resp.url}")
    print(f"Response content-type: {resp.headers.get('Content-Type')}")

    # Check for token in response or cookies
    # Check cookies
    print(f"\nCookies after login: {[c.name for c in session.cookies]}")

    # Check if there's a token in response headers
    print(f"Response headers: {dict(resp.headers)}")

    # Check if response has JSON with token
    try:
        json_data = resp.json()
        print(f"JSON response: {json_data}")
    except:
        pass

    # Look for Bearer token pattern in all cookies and headers
    for cookie in session.cookies:
        print(f"Cookie {cookie.name}: {cookie.value[:50] if cookie.value else 'None'}...")

    return session

def try_api_with_session():
    """Try various auth approaches for /api/employees"""
    global unquote
    from urllib.parse import unquote

    session = login_and_get_token()

    # Try 1: Direct access (might fail)
    print("\n--- Try 1: Direct /api/employees ---")
    r = session.get(f'{BASE_URL}/api/employees', timeout=15)
    print(f"Status: {r.status_code}")
    if r.status_code != 200:
        print(f"Response: {r.text[:200]}")

    # Try 2: With Accept: text/html (might be Inertia)
    print("\n--- Try 2: With Accept: text/html ---")
    session2 = requests.Session()
    session2.headers['Accept'] = 'text/html'

    csrf_resp = session2.get(f'{BASE_URL}/sanctum/csrf-cookie', timeout=30)
    xsrf_token = session2.cookies.get('XSRF-TOKEN', '')
    xsrf_token = unquote(xsrf_token) if xsrf_token else ''

    login_data = {'email': 'lab@sdadparts.com', 'password': 'Lab!1234'}
    resp = session2.post(
        f'{BASE_URL}/login',
        data=login_data,
        headers={'X-XSRF-TOKEN': xsrf_token},
        allow_redirects=True,
        timeout=30
    )
    print(f"Login: {resp.status_code} - {resp.url}")

    r2 = session2.get(f'{BASE_URL}/api/employees', timeout=15)
    print(f"/api/employees: {r2.status_code}")

    # Try 3: Look for token in page source
    print("\n--- Try 3: Look for Bearer token in page ---")
    dash_resp = session.get(f'{BASE_URL}/dashboard', timeout=15)
    if dash_resp.status_code == 200:
        # Search for Bearer token patterns
        tokens = re.findall(r'bearer["\']?\s*:\s*["\']([^"\']+)["\']', dash_resp.text, re.IGNORECASE)
        print(f"Found bearer tokens: {tokens[:3]}")
        tokens2 = re.findall(r'token["\']?\s*:\s*["\']([^"\']+)["\']', dash_resp.text, re.IGNORECASE)
        print(f"Found token patterns: {tokens2[:3]}")

        # Look for meta tags (Laravel Fortify/Inertia)
        meta_tokens = re.findall(r'<meta name="csrf-token" content="([^"]+)"', dash_resp.text)
        print(f"CSRF meta: {meta_tokens[:3]}")

        meta_tokens2 = re.findall(r'<meta[^>]+csrf[^>]+content="([^"]+)"', dash_resp.text, re.IGNORECASE)
        print(f"CSRF meta2: {meta_tokens2[:3]}")

if __name__ == '__main__':
    try_api_with_session()
