"""
Full Playwright-based customer extraction
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

def extract_customers():
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

        print("\n2. Getting CSRF token via fetch...")
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

        print("\n3. Logging in via fetch...")
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

        print("\n4. Checking cookies:")
        cookies = context.cookies()
        has_session = any(c['name'] == 'sdadparts_crm_session' for c in cookies)
        print(f"   Has session cookie: {has_session}")

        print("\n5. Trying to navigate directly to customers URL...")
        # Try to directly navigate
        try:
            page.goto(f"{BASE_URL}/dashboard/customers", timeout=30000)
            page.wait_for_load_state("domcontentloaded", timeout=15000)
            time.sleep(3)
            print(f"   URL after navigation: {page.url}")

            if 'login' in page.url.lower():
                print("   Redirected to login - session may not work")

            # Check for any content
            content = page.content()
            has_table = '<table' in content.lower()
            has_customer = 'customer' in content.lower()
            print(f"   Has table: {has_table}")
            print(f"   Has customer text: {has_customer}")

            if has_table:
                # Extract table data
                extract_script = """
                () => {
                    const table = document.querySelector('table');
                    if (!table) return { error: 'No table found' };

                    const rows = table.querySelectorAll('tbody tr');
                    const data = [];

                    rows.forEach((row, idx) => {
                        const cells = row.querySelectorAll('td');
                        if (cells.length >= 2) {
                            const rowData = [];
                            cells.forEach(cell => {
                                rowData.push(cell.innerText.trim());
                            });
                            data.push(rowData);
                        }
                    });

                    return { rows: data.length, first: data[0] || [] };
                }
                """
                result = page.evaluate(extract_script)
                print(f"   Extract result: {result}")

        except Exception as e:
            print(f"   Navigation error: {e}")

        print("\n6. Trying to find customer data via JavaScript...")
        js_script = """
        () => {
            // Try to find Inertia page data
            const app = document.querySelector('#app');
            if (app) {
                const pageData = app.getAttribute('data-page');
                if (pageData) {
                    return { found: 'data-page', preview: pageData.substring(0, 200) };
                }
            }

            // Try window.page
            if (window.page) {
                return { found: 'window.page', keys: Object.keys(window.page) };
            }

            // Try to find any table
            const tables = document.querySelectorAll('table');
            if (tables.length > 0) {
                return { found: 'tables', count: tables.length };
            }

            return { found: 'nothing' };
        }
        """
        result = page.evaluate(js_script)
        print(f"   JS result: {result}")

        browser.close()

    return customers

if __name__ == "__main__":
    print("=== SDAD Customers Extraction via Playwright ===\n")
    customers = extract_customers()
    print(f"\nExtracted {len(customers)} customers")