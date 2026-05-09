"""
Extract customers - use JavaScript navigation instead of page.goto()
"""
import os
import sys
import json
import time
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

def extract():
    customers = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        print("1. Loading base URL...")
        page.goto(BASE_URL, timeout=30000)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"   URL: {page.url}")

        print("\n2. Getting CSRF...")
        import urllib.parse

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

        cookies = context.cookies()
        xsrf = None
        for c in cookies:
            if c['name'] == 'XSRF-TOKEN':
                xsrf = urllib.parse.unquote(c['value'])
                break
        print(f"   XSRF: {xsrf[:30] if xsrf else 'None'}...")

        print("\n3. Logging in via fetch...")
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
            return {{ status: resp.status, success: resp.ok, user: data.data?.user?.name }};
        }}
        """
        result = page.evaluate(login_script)
        print(f"   Login result: {result}")

        time.sleep(2)

        print("\n4. Checking cookies:")
        cookies = context.cookies()
        for c in cookies:
            print(f"   {c['name']}: {c['value'][:50]}...")

        print("\n5. Using Inertia.visit() for SPA navigation...")

        # Try using Inertia.visit if available
        inertia_script = """
        async () => {
            if (window.Laravel && window.Laravel.Inertia) {
                await window.Laravel.Inertia.visit('/dashboard/customers');
                return { method: 'Inertia.visit', url: window.location.href };
            } else if (window.route) {
                const url = window.route('dashboard.customers.index').url();
                window.location.href = url;
                return { method: 'route()', url };
            } else {
                window.location.href = '/dashboard/customers';
                return { method: 'location.href', url: '/dashboard/customers' };
            }
        }
        """

        # Actually use simpler approach - just change location via JS
        js_nav_script = """
        () => {
            // Use Inertia if available
            if (typeof window.Inertia !== 'undefined') {
                window.Inertia.visit('/dashboard/customers', { preserveState: true });
            } else {
                window.location.href = '/dashboard/customers';
            }
            return { done: true };
        }
        """

        print("   Executing JS navigation...")
        page.evaluate(js_nav_script)
        print("   Waiting for navigation...")
        page.wait_for_timeout(5000)
        page.wait_for_load_state("networkidle", timeout=15000)
        page.wait_for_timeout(2000)

        print(f"   URL after JS nav: {page.url}")

        # Check for table
        print("\n6. Looking for table...")
        table_script = """
        () => {
            const tables = document.querySelectorAll('table');
            const result = [];
            tables.forEach((table, i) => {
                const headers = Array.from(table.querySelectorAll('th')).map(th => th.innerText.trim());
                const rows = Array.from(table.querySelectorAll('tbody tr')).slice(0, 20).map(row => {
                    return Array.from(row.querySelectorAll('td')).map(td => td.innerText.trim());
                });
                result.push({ headers, rows });
            });
            return result;
        }
        """
        tables = page.evaluate(table_script)
        print(f"   Found {len(tables)} tables")

        if tables:
            for i, t in enumerate(tables):
                print(f"   Table {i}: {len(t['rows'])} rows")
                if t['headers']:
                    print(f"     Headers: {t['headers']}")

        # Check component
        check_script = """
        () => {
            const app = document.querySelector('#app');
            if (app) {
                const dataPage = app.getAttribute('data-page');
                if (dataPage) {
                    try {
                        const parsed = JSON.parse(dataPage);
                        return { component: parsed.component };
                    } catch(e) {}
                }
            }
            return { error: 'not found' };
        }
        """
        page_info = page.evaluate(check_script)
        print(f"   Component: {page_info}")

        browser.close()

    return customers

if __name__ == "__main__":
    print("=" * 60)
    print("SDAD CUSTOMERS - JS NAVIGATION")
    print("=" * 60)
    customers = extract()
    print(f"\nExtracted: {len(customers)} customers")