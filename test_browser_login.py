"""
Test login via Playwright browser - to capture full login flow with JavaScript
"""
import os
import sys
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

print(f"Testing Playwright login to {BASE_URL}")
print(f"Username: {USERNAME}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    page = context.new_page()

    # Track responses
    def log_response(response):
        if 'api' in response.url or 'customer' in response.url.lower():
            print(f"  {response.status} {response.url[:80]}")

    page.on("response", log_response)

    print("\n1. Loading base URL...")
    page.goto(BASE_URL, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    print(f"   URL: {page.url}")

    print("\n2. Getting CSRF token...")
    page.goto(f"{BASE_URL}/sanctum/csrf-cookie", timeout=30000)
    page.wait_for_timeout(1000)

    # Get cookies
    cookies = context.cookies()
    xsrf = None
    for c in cookies:
        if c['name'] == 'XSRF-TOKEN':
            xsrf = c['value']
            print(f"   XSRF Token: {xsrf[:50]}...")

    print("\n3. Logging in via form fill...")

    # Try to fill login form
    try:
        page.goto(f"{BASE_URL}/login", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=15000)
        print(f"   Login page URL: {page.url}")
        print(f"   Login page title: {page.title()}")

        # Check for form elements
        page.wait_for_timeout(2000)

        # Fill email
        email_input = page.wait_for_selector('input[name="email"], input[type="email"]', timeout=5000)
        if email_input:
            email_input.fill(USERNAME)
            print(f"   Filled email")

        # Fill password
        password_input = page.wait_for_selector('input[name="password"], input[type="password"]', timeout=5000)
        if password_input:
            password_input.fill(PASSWORD)
            print(f"   Filled password")

        # Click submit
        page.click('button[type="submit"]')
        print(f"   Clicked submit")
        page.wait_for_timeout(3000)

        print(f"   URL after submit: {page.url}")

    except Exception as e:
        print(f"   Form fill error: {e}")

    print("\n4. Trying direct navigation to customers...")

    # Try to access customers
    try:
        page.goto(f"{BASE_URL}/dashboard/customers", timeout=30000)
        page.wait_for_load_state("networkidle", timeout=15000)
        page.wait_for_timeout(2000)
        print(f"   URL: {page.url}")
        print(f"   Title: {page.title()}")

        # Check for customer data
        if 'customer' in page.content().lower() or 'table' in page.content().lower():
            print("   Found customer/table content!")

        # Save page for inspection
        with open('playwright_customers.html', 'w', encoding='utf-8') as f:
            f.write(page.content())
        print("   Saved page to playwright_customers.html")

    except Exception as e:
        print(f"   Navigation error: {e}")

    print("\n5. Final cookie state:")
    final_cookies = context.cookies()
    for c in final_cookies:
        print(f"   {c['name']}: {c['value'][:50]}...")

    browser.close()

print("\nDone.")