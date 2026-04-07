"""Scrape employees - use requests for login then playwright for navigation"""
from playwright.sync_api import sync_playwright
import requests
import time
from urllib.parse import unquote

BASE_URL = 'https://panel.sdadparts.com'
EMAIL = 'lab@sdadparts.com'
PASSWORD = 'Lab!1234'

def do_login():
    """Login with requests"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    })

    # First visit base URL to get initial cookies
    r = session.get(BASE_URL, timeout=30)
    print(f"Base URL: {r.status_code}")

    # Get CSRF
    r = session.get(f'{BASE_URL}/sanctum/csrf-cookie', timeout=30)
    print(f"CSRF: {r.status_code}")
    csrf_token = session.cookies.get('XSRF-TOKEN', '')
    csrf_token = unquote(csrf_token)
    print(f"CSRF token: {csrf_token[:30]}...")

    # Login
    login_data = {
        'email': EMAIL,
        'password': PASSWORD,
        '_token': csrf_token
    }

    r = session.post(
        f'{BASE_URL}/login',
        data=login_data,
        headers={
            'X-XSRF-TOKEN': csrf_token,
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        allow_redirects=True,
        timeout=30
    )
    print(f"Login POST: {r.status_code} - {r.url}")

    # Check if logged in
    if 'dashboard' in r.url.lower():
        print("Login successful!")
    else:
        print(f"Login redirected to: {r.url}")

    # Get all cookies
    cookies = {c.name: c.value for c in session.cookies}
    print(f"Cookies obtained: {list(cookies.keys())}")

    return cookies

def scrape_with_playwright(cookies):
    """Navigate with Playwright using cookies"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()

        # Add cookies
        cookie_list = []
        for name, value in cookies.items():
            cookie_list.append({
                'name': name,
                'value': value,
                'domain': '.sdadparts.com',
                'path': '/',
                'secure': True,
                'httpOnly': name == 'sdadparts_crm_session'
            })

        context.add_cookies(cookie_list)

        page = context.new_page()

        # Go to base URL first
        print("\nNavigating to base URL...")
        r = page.goto(BASE_URL, timeout=60000)
        print(f"Base URL: {r.status} - {page.url}")
        time.sleep(3)

        print(f"Title: {page.title()}")

        # Now try dashboard
        print("\nNavigating to dashboard...")
        r = page.goto(f'{BASE_URL}/dashboard', timeout=60000)
        print(f"Dashboard: {r.status} - {page.url}")
        time.sleep(3)

        print(f"Title: {page.title()}")

        # Now employees
        print("\nNavigating to employees...")
        r = page.goto(f'{BASE_URL}/dashboard/employees', timeout=60000)
        print(f"Employees: {r.status} - {page.url}")
        time.sleep(5)

        print(f"Title: {page.title()}")

        # Check URL
        if 'login' in page.url.lower():
            print("Still logged out!")
            # Try to get error message
            error = page.evaluate('document.body.innerText')
            print(f"Error text: {error[:300]}")
        else:
            # We might be on the employees page
            print(f"On page: {page.url}")

            # Look for tables
            tables = page.query_selector_all('table')
            print(f"Tables: {len(tables)}")

            if tables:
                headers = page.evaluate("""() => {
                    const ths = document.querySelectorAll('table thead th');
                    return Array.from(ths).map(th => th.innerText.trim());
                }""")
                print(f"Headers: {headers}")

                rows = page.evaluate("""() => {
                    const trs = document.querySelectorAll('table tbody tr');
                    return Array.from(trs).slice(0, 30).map(tr => {
                        const tds = tr.querySelectorAll('td');
                        return Array.from(tds).map(td => td.innerText.trim());
                    });
                }""")
                print(f"Rows: {len(rows)}")
                for i, row in enumerate(rows[:10]):
                    print(f"  {i}: {row}")

        browser.close()

if __name__ == '__main__':
    print("=== Login ===")
    cookies = do_login()

    print("\n=== Scrape ===")
    scrape_with_playwright(cookies)
