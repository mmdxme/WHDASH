"""
Extract customers by navigating through the UI - click on sidebar/navigation
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

        print("\n2. Getting CSRF and logging in...")
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
            return {{ status: resp.status, success: resp.ok, user: data.data?.user?.name || 'no user' }};
        }}
        """
        result = page.evaluate(login_script)
        print(f"   Login: {result}")
        time.sleep(2)

        print(f"   URL after login: {page.url}")

        # List all links on the page
        print("\n3. Finding links on current page...")
        links_script = """
        () => {
            const links = Array.from(document.querySelectorAll('a[href]'));
            return links.map(l => ({
                href: l.href,
                text: l.innerText.trim().substring(0, 50),
                class: l.className
            })).slice(0, 30);
        }
        """
        links = page.evaluate(links_script)
        print(f"   Found {len(links)} links:")
        for link in links:
            if link['href'] and ('dashboard' in link['href'].lower() or 'customer' in link['href'].lower()):
                print(f"     - {link['href']}: {link['text']}")

        # Try to find and click on customers link
        print("\n4. Looking for sidebar navigation...")

        nav_script = """
        () => {
            // Look for sidebar, nav, menu elements
            const selectors = [
                'nav a',
                '.sidebar a',
                '.side-nav a',
                '[role="navigation"] a',
                'aside a',
                '.nav a',
                'ul.menu a',
                '.menu a',
                '[class*="sidebar"] a',
                '[class*="nav"] a',
                '[class*="menu"] a',
            ];

            const results = [];
            for (const sel of selectors) {
                const els = document.querySelectorAll(sel);
                if (els.length > 0) {
                    results.push({
                        selector: sel,
                        count: els.length,
                        items: Array.from(els).slice(0, 5).map(el => ({
                            text: el.innerText.trim().substring(0, 50),
                            href: el.href
                        }))
                    });
                }
            }
            return results;
        }
        """
        nav_results = page.evaluate(nav_script)
        print(f"   Navigation elements found:")
        for nav in nav_results[:3]:
            print(f"     {nav['selector']}: {nav['count']} items")
            for item in nav['items']:
                if item['href']:
                    print(f"       - {item['href']}: {item['text']}")

        # Try to find any element with "customer" text and click it
        print("\n5. Looking for 'Customer' text to click...")

        click_script = """
        () => {
            // Find any clickable element with "customer" in text
            const keywords = ['customer', 'Customer', 'مشتری', 'customers', 'Customers'];
            const selectors = [];

            keywords.forEach(kw => {
                selectors.push(`a:has-text("${kw}")`);
                selectors.push(`button:has-text("${kw}")`);
                selectors.push(`[role="button"]:has-text("${kw}")`);
                selectors.push(`span:has-text("${kw}")`);
                selectors.push(`div:has-text("${kw}")`);
            });

            for (const sel of selectors) {
                try {
                    const el = document.querySelector(sel);
                    if (el && el.offsetParent !== null) {  // visible
                        const tag = el.tagName;
                        const text = el.innerText.trim().substring(0, 50);
                        const href = el.href || '';
                        return { selector: sel, tag, text, href };
                    }
                } catch(e) {}
            }
            return null;
        }
        """
        result = page.evaluate(click_script)
        print(f"   Clickable element with 'customer': {result}")

        if result and result['href']:
            print(f"\n6. Clicking on element with href: {result['href']}")
            try:
                page.goto(result['href'], timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)
                time.sleep(3)
                print(f"   URL after click: {page.url}")
            except Exception as e:
                print(f"   Navigation error: {e}")

        # Try to access via hash routing (Inertia might use hash)
        print("\n7. Trying to access via URL with query params...")

        # Check if maybe the page uses query params
        check_url_script = """
        () => {
            return {
                href: window.location.href,
                pathname: window.location.pathname,
                hash: window.location.hash,
                search: window.location.search
            };
        }
        """
        url_info = page.evaluate(check_url_script)
        print(f"   URL info: {url_info}")

        # Try to find if there's an iframe or different content area
        print("\n8. Checking for frames/iframes...")
        frames_script = """
        () => {
            return {
                frames: window.frames?.length || 0,
                iframes: document.querySelectorAll('iframe').length
            };
        }
        """
        frames = page.evaluate(frames_script)
        print(f"   Frames: {frames}")

        # Take a screenshot for debugging
        print("\n9. Saving screenshot...")
        page.screenshot(path='customers_page.png')
        print(f"   Screenshot saved to customers_page.png")

        # Get full page HTML for analysis
        print("\n10. Saving page content...")
        with open('customers_page.html', 'w', encoding='utf-8') as f:
            f.write(page.content())
        print(f"   Page saved to customers_page.html")

        browser.close()

if __name__ == "__main__":
    print("=" * 60)
    print("SDAD CUSTOMERS EXTRACTION - NAVIGATION APPROACH")
    print("=" * 60)
    extract()