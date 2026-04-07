"""Test scraping employees from the SPA using requests session that maintains cookies properly"""
import requests
import json
import re

BASE_URL = 'https://panel.sdadparts.com'

def login():
    """Login and maintain session properly"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    })

    # Step 1: Get initial cookies
    resp = session.get(BASE_URL, timeout=30)
    print(f"Step 1 - Initial load: {resp.status_code}")

    # Step 2: Get CSRF token
    csrf_resp = session.get(f'{BASE_URL}/sanctum/csrf-cookie', timeout=30)
    xsrf_token = session.cookies.get('XSRF-TOKEN', '')
    from urllib.parse import unquote
    xsrf_token = unquote(xsrf_token)
    print(f"Step 2 - CSRF: {xsrf_token[:30]}...")

    # Step 3: Login
    login_data = {'email': 'lab@sdadparts.com', 'password': 'Lab!1234'}
    resp = session.post(
        f'{BASE_URL}/login',
        data=login_data,
        headers={'X-XSRF-TOKEN': xsrf_token},
        allow_redirects=True,
        timeout=30
    )
    print(f"Step 3 - Login: {resp.status_code} - {resp.url}")

    # Check cookies after login
    print(f"Cookies after login: {[c.name for c in session.cookies]}")

    return session

def get_employees_page(session):
    """Try to get employees from the dashboard page"""
    # Get dashboard page which should have employee data
    resp = session.get(f'{BASE_URL}/dashboard', timeout=30)
    print(f"Dashboard: {resp.status_code}")

    if resp.status_code == 200:
        # Look for employee data patterns in the HTML/Inertia payload
        html = resp.text

        # Look for Inertia page data
        inertia_matches = re.findall(r'page-dataurl="([^"]+)"', html)
        print(f"Inertia page-dataurl matches: {inertia_matches[:3]}")

        # Look for any JSON data embedded
        json_matches = re.findall(r'<script[^>]*type="application/json"[^>]*>([^<]+)</script>', html)
        print(f"JSON script tags: {len(json_matches)}")

        for i, match in enumerate(json_matches[:3]):
            try:
                data = json.loads(match)
                print(f"  JSON {i}: {str(data)[:200]}...")
            except:
                pass

        # Look for employee-related content
        if 'employee' in html.lower():
            print("Found 'employee' in HTML")
            # Find context around it
            idx = html.lower().find('employee')
            print(f"  Context: {html[max(0,idx-50):idx+100]}")

        # Try to find any API URLs
        api_urls = re.findall(r'["\'](/api/[^"\']+)["\']', html)
        print(f"API URLs found: {api_urls[:10]}")

    return resp

def try_hr_routes(session):
    """Try various HR-related routes"""
    routes = [
        '/dashboard/hr',
        '/dashboard/employees',
        '/dashboard/staff',
        '/hr',
        '/employees',
    ]

    for route in routes:
        try:
            r = session.get(f'{BASE_URL}{route}', timeout=15)
            print(f"{route}: {r.status_code}")
            if r.status_code == 200:
                if 'employee' in r.text.lower():
                    print(f"  -> Has 'employee' content")
        except Exception as e:
            print(f"{route}: Error - {e}")

if __name__ == '__main__':
    session = login()

    print("\n=== Get Dashboard ===")
    get_employees_page(session)

    print("\n=== Try HR routes ===")
    try_hr_routes(session)
