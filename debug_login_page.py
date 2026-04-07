"""Debug: Take a screenshot of login page to see the actual form"""
from playwright.sync_api import sync_playwright
import os

env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                if '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

BASE_URL = os.environ.get('PEYVAST_BASE_URL', 'https://panel.sdadparts.com')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1920, 'height': 1080})

    print(f"Loading {BASE_URL}/login...")
    page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)

    print(f"URL: {page.url}")
    print(f"Title: {page.title()}")

    # Get page HTML structure
    html = page.content()

    # Save screenshot
    page.screenshot(path='login_page_screenshot.png', full_page=True)
    print("Screenshot saved to login_page_screenshot.png")

    # Find all input fields
    inputs = page.query_selector_all('input')
    print(f"\nFound {len(inputs)} input fields:")
    for inp in inputs:
        name = inp.get_attribute('name')
        type_attr = inp.get_attribute('type')
        id_attr = inp.get_attribute('id')
        placeholder = inp.get_attribute('placeholder')
        print(f"  name={name}, type={type_attr}, id={id_attr}, placeholder={placeholder}")

    # Find all buttons
    buttons = page.query_selector_all('button')
    print(f"\nFound {len(buttons)} buttons:")
    for btn in buttons:
        text = btn.inner_text()
        type_attr = btn.get_attribute('type')
        print(f"  text={text.strip()}, type={type_attr}")

    # Find form
    forms = page.query_selector_all('form')
    print(f"\nFound {len(forms)} forms")

    browser.close()