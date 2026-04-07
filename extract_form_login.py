"""
Extract customers - use form-based login instead of API
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

        print("1. Loading login page directly...")
        page.goto(f"{BASE_URL}/login", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"   URL: {page.url}")
        print(f"   Title: {page.title()}")

        # Check what form elements exist
        print("\n2. Checking form elements...")
        form_script = """
        () => {
            const emailInput = document.querySelector('input[name="email"], input[type="email"], input[id="email"]');
            const passwordInput = document.querySelector('input[name="password"], input[type="password"], input[id="password"]');
            const submitBtn = document.querySelector('button[type="submit"], button:has-text("Login"), button:has-text("Sign in"), input[type="submit"]');

            return {
                hasEmail: !!emailInput,
                hasPassword: !!passwordInput,
                hasSubmit: !!submitBtn,
                emailType: emailInput?.type,
                passwordType: passwordInput?.type,
                submitText: submitBtn?.innerText?.trim() || submitBtn?.value
            };
        }
        """
        form_info = page.evaluate(form_script)
        print(f"   Form info: {form_info}")

        if not form_info['hasEmail'] or not form_info['hasPassword']:
            print("   WARNING: Form elements not found!")

        print("\n3. Filling login form...")
        try:
            # Try to find email input
            email_input = page.wait_for_selector('input[name="email"], input[type="email"]', timeout=5000)
            email_input.fill(USERNAME)
            print(f"   Filled email")

            # Fill password
            password_input = page.wait_for_selector('input[name="password"]', timeout=5000)
            password_input.fill(PASSWORD)
            print(f"   Filled password")

            # Click submit
            print("\n4. Clicking submit...")
            page.click('button[type="submit"]')
            page.wait_for_timeout(5000)

            print(f"   URL after submit: {page.url}")
            print(f"   Title after submit: {page.title()}")

            # Check if we're logged in
            if 'login' not in page.url.lower():
                print("   SUCCESS: Logged in!")

                # Navigate to customers
                print("\n5. Navigating to customers...")

                # Try direct URL
                page.goto(f"{BASE_URL}/dashboard/customers", timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)
                page.wait_for_timeout(3000)
                print(f"   URL: {page.url}")

                # Look for table
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

            else:
                print("   FAILED: Still on login page")

        except Exception as e:
            print(f"   Error: {e}")
            import traceback
            traceback.print_exc()

        browser.close()

    return customers

if __name__ == "__main__":
    print("=" * 60)
    print("SDAD CUSTOMERS - FORM LOGIN")
    print("=" * 60)
    customers = extract()
    print(f"\nExtracted: {len(customers)} customers")