"""
Extract customers - use page.reload() after login instead of goto
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

        print("\n3. Logging in...")
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

        print("\n4. Checking cookies after login:")
        cookies = context.cookies()
        for c in cookies:
            print(f"   {c['name']}: {c['value'][:50]}...")

        print("\n5. Reloading page instead of goto...")
        page.reload(timeout=30000)
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(2)
        print(f"   URL after reload: {page.url}")

        print("\n6. Looking for table...")
        table_script = """
        () => {
            const tables = document.querySelectorAll('table');
            const result = [];
            tables.forEach((table, i) => {
                const headers = Array.from(table.querySelectorAll('th')).map(th => th.innerText.trim());
                const rows = Array.from(table.querySelectorAll('tbody tr')).slice(0, 10).map(row => {
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
                if t['rows']:
                    print(f"     First row: {t['rows'][0]}")

        # Check URL and component
        print(f"\n7. URL: {page.url}")
        check_script = """
        () => {
            const app = document.querySelector('#app');
            if (app) {
                const dataPage = app.getAttribute('data-page');
                if (dataPage) {
                    try {
                        const parsed = JSON.parse(dataPage);
                        return { component: parsed.component, propsKeys: Object.keys(parsed.props || {}) };
                    } catch(e) {
                        return { error: e.message };
                    }
                }
            }
            return { error: 'No #app found' };
        }
        """
        page_info = page.evaluate(check_script)
        print(f"   Page info: {page_info}")

        browser.close()

    return customers

if __name__ == "__main__":
    print("=" * 60)
    print("SDAD CUSTOMERS EXTRACTION v3")
    print("=" * 60)
    customers = extract()
    print(f"\nExtracted: {len(customers)} customers")