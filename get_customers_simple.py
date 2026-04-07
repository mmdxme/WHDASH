"""
Try to find and use the actual API endpoint for customers.
Based on earlier analysis, these endpoints exist in the Ziggy routes:
- dashboard.customers.index: /dashboard/customers
- dashboard.customers.search: /dashboard/customers/search
"""
import requests
import json
import os
import re
import html

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

# IMPORTANT: After login, we got redirected to '/' and got Auth/Login component.
# This suggests the session cookie is not being recognized for web routes.

# Let me try to find an API endpoint that works with the session cookie

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
})

print("=== Login and Try API ===\n")

# Step 1: Login
session.get(BASE_URL, timeout=30)
session.get(f"{BASE_URL}/sanctum/csrf-cookie", timeout=30)
resp = session.post(
    f"{BASE_URL}/api/login",
    json={'email': os.environ.get('PEYVAST_USERNAME'), 'password': os.environ.get('PEYVAST_PASSWORD')},
    timeout=30
)
print(f"Login: {resp.status_code}")
print(f"Cookies: {[c.name for c in session.cookies]}")

# Step 2: Try to find the actual API endpoint
# The Ziggy routes show that customers.search uses GET /dashboard/customers/search
# But this requires Inertia headers and session auth

# Let's try different approaches
print("\n--- Approach 1: Normal HTML request to search ---")
r = session.get(f"{BASE_URL}/dashboard/customers/search", timeout=30)
print(f"Status: {r.status_code}")
print(f"URL: {r.url}")

# Check if there's any useful data in query params
print(f"URL params: {r.url}")

# Check cookies
print(f"\nCookies after request:")
for c in session.cookies:
    print(f"  {c.name}: {c.value[:30]}...")

# Approach 2: Look at what happens when we access with Inertia headers
print("\n--- Approach 2: Inertia request ---")
session2 = requests.Session()
session2.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'X-Requested-With': 'XMLHttpRequest',
    'X-Inertia': 'true',
})

# Copy cookies from session1
for c in session.cookies:
    session2.cookies.set(c.name, c.value)

r = session2.get(f"{BASE_URL}/dashboard/customers", timeout=30)
print(f"Status: {r.status_code}")
if r.status_code != 200:
    print(f"Response: {r.text[:200]}")

# Approach 3: Try the Laravel API routes directly
print("\n--- Approach 3: API routes ---")
api_session = requests.Session()
api_session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
})

for c in session.cookies:
    api_session.cookies.set(c.name, c.value)

# These are the actual API endpoints based on Ziggy routes
api_endpoints = [
    '/api/reports/general-customers-stats',
    '/api/reports/top-customers',
    '/api/reports/customers-top-by-brand',
]

for ep in api_endpoints:
    r = api_session.get(f"{BASE_URL}{ep}", timeout=15)
    print(f"{ep}: {r.status_code}")
    if r.status_code == 200:
        try:
            d = r.json()
            print(f"  Keys: {list(d.keys())[:5]}")
        except:
            print(f"  Content: {r.text[:100]}")