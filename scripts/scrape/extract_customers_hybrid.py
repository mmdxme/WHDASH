"""
Hybrid approach: login with requests, then use browser for data extraction
"""
import os
import sys
import json
import time
import requests
import http.cookiejar
from playwright.sync_api import sync_playwright

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

def extract_with_requests():
    """Extract customers using requests library with full session handling."""
    customers = []

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    })

    print("=== Requests-based extraction ===\n")

    # Step 1: Get initial page
    print("1. GET base URL...")
    r = session.get(BASE_URL, timeout=30)
    print(f"   Status: {r.status_code}")

    # Step 2: Get CSRF
    print("2. GET sanctum/csrf-cookie...")
    r = session.get(f"{BASE_URL}/sanctum/csrf-cookie", timeout=30)
    print(f"   Status: {r.status_code}")

    # Step 3: Login
    print("3. POST /api/login...")
    resp = session.post(
        f"{BASE_URL}/api/login",
        json={'email': USERNAME, 'password': PASSWORD},
        timeout=30
    )
    print(f"   Status: {resp.status_code}")
    print(f"   Response: {resp.text[:200]}")

    # Step 4: Get customers page with full HTML
    print("\n4. GET /dashboard/customers...")
    r = session.get(f"{BASE_URL}/dashboard/customers", timeout=30)
    print(f"   Status: {r.status_code}")
    print(f"   URL: {r.url}")

    # Parse the page to find any customer data
    if r.status_code == 200:
        import re
        import html

        # Look for Inertia data
        match = re.search(r'data-page="([^"]+)"', r.text)
        if match:
            data_page_str = html.unescape(match.group(1))
            try:
                data_page = json.loads(data_page_str)
                component = data_page.get('component', '')
                props = data_page.get('props', {})
                print(f"   Component: {component}")
                print(f"   Props keys: {list(props.keys())}")

                # Try to find any customer-related data
                def search_nested(obj, depth=0, max_depth=5):
                    if depth > max_depth:
                        return
                    if isinstance(obj, dict):
                        for k, v in obj.items():
                            if 'customer' in k.lower():
                                print(f"   Found key with 'customer': {k}")
                            if isinstance(v, (dict, list)):
                                search_nested(v, depth + 1, max_depth)
                    elif isinstance(obj, list):
                        for item in obj[:5]:  # Limit search
                            search_nested(item, depth + 1, max_depth)

                search_nested(props)

            except json.JSONDecodeError as e:
                print(f"   JSON error: {e}")

        # Look for any JavaScript that loads customer data
        js_urls = re.findall(r'(?:fetch|axios|get|post)\(["\']([^"\']*(?:customer|customers)[^"\']*)["\']', r.text, re.IGNORECASE)
        if js_urls:
            print(f"\n   Found JS URLs with 'customer':")
            for url in js_urls[:5]:
                print(f"     {url}")

    return customers

def extract_with_browser():
    """Extract customers using Playwright browser."""
    customers = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        print("\n=== Browser-based extraction ===\n")

        # Login via JavaScript
        print("1. Loading page and getting CSRF...")
        page.goto(BASE_URL, timeout=30000)
        page.wait_for_load_state("networkidle", timeout=15000)

        csrf_script = """
        async () => {
            const resp = await fetch('/sanctum/csrf-cookie', {
                method: 'GET',
                credentials: 'include'
            });
            return { status: resp.status };
        }
        """
        page.evaluate(csrf_script)
        time.sleep(1)

        print("2. Logging in via fetch...")
        import urllib.parse
        cookies = context.cookies()
        xsrf = None
        for c in cookies:
            if c['name'] == 'XSRF-TOKEN':
                xsrf = urllib.parse.unquote(c['value'])
                break

        login_script = f"""
        async () => {{
            const resp = await fetch('/api/login', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'X-XSRF-TOKEN': '{xsrf}'
                }},
                credentials: 'include',
                body: JSON.stringify({{
                    'email': '{USERNAME}',
                    'password': '{PASSWORD}'
                }})
            }});
            const data = await resp.json();
            return {{ status: resp.status, success: resp.ok, hasToken: !!data.data?.token }};
        }}
        """
        result = page.evaluate(login_script)
        print(f"   Login result: {result}")
        time.sleep(2)

        # Now try to click on customers link or navigate
        print("3. Looking for customers link...")

        # Try to find any customer-related link
        link_script = """
        () => {
            const links = Array.from(document.querySelectorAll('a[href*="customer"]'));
            return links.map(l => ({ href: l.href, text: l.innerText.trim() }));
        }
        """
        links = page.evaluate(link_script)
        print(f"   Found {len(links)} customer links: {links[:3]}")

        # Try to click on any sidebar link to customers
        click_script = """
        () => {
            // Try to find and click a customers link
            const selectors = [
                'a[href*="/dashboard/customers"]',
                'a[href*="customer"]',
                'a[href*="Customer"]',
                'button[data-href*="customer"]',
                '[class*="customer"]',
            ];

            for (const sel of selectors) {
                const el = document.querySelector(sel);
                if (el) {
                    el.click();
                    return { clicked: sel, text: el.innerText?.trim() || el.textContent?.trim() || 'no text' };
                }
            }
            return { clicked: null };
        }
        """
        result = page.evaluate(click_script)
        print(f"   Click result: {result}")
        time.sleep(3)

        print(f"   Current URL after click: {page.url}")

        # Extract any table data
        table_script = """
        () => {
            const tables = document.querySelectorAll('table');
            const result = [];

            tables.forEach((table, ti) => {
                const headers = Array.from(table.querySelectorAll('th')).map(th => th.innerText.trim());
                const rows = Array.from(table.querySelectorAll('tbody tr')).map(row => {
                    return Array.from(row.querySelectorAll('td')).map(td => td.innerText.trim());
                });
                result.push({ headers, rows: rows.slice(0, 10) });
            });

            return result;
        }
        """
        tables = page.evaluate(table_script)
        print(f"   Found {len(tables)} tables")

        for i, t in enumerate(tables):
            print(f"   Table {i}: {len(t['rows'])} rows")
            if t['headers']:
                print(f"     Headers: {t['headers']}")
            if t['rows']:
                print(f"     First row: {t['rows'][0]}")

        browser.close()

    return customers

if __name__ == "__main__":
    print("=" * 60)
    print("SDAD CUSTOMERS EXTRACTION TEST")
    print("=" * 60)

    # Try requests first
    extract_with_requests()

    # Then try browser
    extract_with_browser()