"""
Debug the redirect issue with session cookies
"""
import requests
import json
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

BASE_URL = 'https://panel.sdadparts.com'

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})

print("=== Debug Session Cookies ===\n")

# Login
session.get(BASE_URL, timeout=30)
session.get(f"{BASE_URL}/sanctum/csrf-cookie", timeout=30)
resp = session.post(
    f"{BASE_URL}/api/login",
    json={'email': os.environ.get('PEYVAST_USERNAME'), 'password': os.environ.get('PEYVAST_PASSWORD')},
    timeout=30
)
print(f"Login: {resp.status_code}")

print("\nCookies after login:")
for c in session.cookies:
    print(f"  {c.name}: {c.value[:50]}...")

# Try getting dashboard
print("\n--- GET /dashboard ---")
r = session.get(f"{BASE_URL}/dashboard", timeout=30)
print(f"Status: {r.status_code}")
print(f"URL: {r.url}")
print(f"Final URL: {r.url}")
print(f"History: {r.history}")
for c in session.cookies:
    print(f"  {c.name}: {c.value[:50]}...")

# Try getting customers
print("\n--- GET /dashboard/customers ---")
r = session.get(f"{BASE_URL}/dashboard/customers", timeout=30, allow_redirects=True)
print(f"Status: {r.status_code}")
print(f"URL: {r.url}")
print(f"Final URL: {r.url}")
print(f"History: {r.history}")

# Try getting customers with no redirects
print("\n--- GET /dashboard/customers (no redirect) ---")
r = session.get(f"{BASE_URL}/dashboard/customers", timeout=30, allow_redirects=False)
print(f"Status: {r.status_code}")
print(f"Headers location: {r.headers.get('Location', 'None')}")

# Check if the issue is with www vs non-www
print("\n--- Trying explicit URL ---")
r = session.get("https://panel.sdadparts.com/dashboard/customers", timeout=30)
print(f"Status: {r.status_code}")
print(f"URL: {r.url}")

# Check if we're hitting the wrong domain
print("\n--- Final cookie check ---")
print(f"All cookies: {[c.name for c in session.cookies]}")
print(f"Cookie domains: {[(c.name, c.domain) for c in session.cookies]}")