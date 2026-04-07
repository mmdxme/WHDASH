"""
Test login via Playwright browser - using fetch for API calls
"""
import os
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

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={'width': 1920, 'height': 1080},
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    )
    page = context.new_page()

    print("\n1. Loading base URL...")
    page.goto(BASE_URL, timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    print(f"   URL: {page.url}")

    print("\n2. Getting CSRF via fetch...")
    # Use fetch instead of page.goto for API calls
    csrf_script = """
    async () => {
        const resp = await fetch('/sanctum/csrf-cookie', { method: 'GET', credentials: 'include' });
        return { status: resp.status, ok: resp.ok };
    }
    """
    result = page.evaluate(csrf_script)
    print(f"   CSRF result: {result}")

    # Get cookies
    cookies = context.cookies()
    xsrf = None
    for c in cookies:
        if c['name'] == 'XSRF-TOKEN':
            xsrf = c['value']
            print(f"   XSRF Token: {xsrf[:50]}...")

    print("\n3. Logging in via fetch...")

    import urllib.parse
    xsrf_unescaped = urllib.parse.unquote(xsrf) if xsrf else ''

    login_script = f"""
    async () => {{
        const resp = await fetch('/api/login', {{
            method: 'POST',
            headers: {{
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'X-XSRF-TOKEN': '{xsrf_unescaped}'
            }},
            credentials: 'include',
            body: JSON.stringify({{
                'email': '{USERNAME}',
                'password': '{PASSWORD}'
            }})
        }});
        const data = await resp.json();
        return {{ status: resp.status, ok: resp.ok, hasToken: !!data.data?.token }};
    }}
    """
    result = page.evaluate(login_script)
    print(f"   Login result: {result}")

    page.wait_for_timeout(2000)

    print("\n4. Checking cookies after login:")
    cookies = context.cookies()
    for c in cookies:
        print(f"   {c['name']}: {c['value'][:50]}...")

    print("\n5. Navigating to customers page...")
    page.goto(f"{BASE_URL}/dashboard/customers", timeout=30000)
    page.wait_for_load_state("networkidle", timeout=15000)
    page.wait_for_timeout(2000)
    print(f"   URL: {page.url}")

    if 'login' not in page.url.lower():
        print("   SUCCESS: On customers page!")

        # Check for table content
        if page.query_selector('table'):
            print("   Found table!")

            # Extract table data
            rows = page.query_selector_all('tbody tr')
            print(f"   Found {len(rows)} rows")

            if len(rows) > 0:
                # Get first few cells
                cells = rows[0].query_selector_all('td')
                for i, cell in enumerate(cells[:5]):
                    print(f"   Cell {i}: {cell.inner_text()[:50]}")
    else:
        print("   FAILED: Still on login page")

    browser.close()

print("\nDone.")