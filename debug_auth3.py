"""Debug authentication"""
import os
import requests
from urllib.parse import unquote

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

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json, */*',
})

print("1. Get base page...")
r = session.get(BASE_URL, timeout=30)
print(f"   Status: {r.status_code}")

print("\n2. Get CSRF cookie...")
r = session.get(f"{BASE_URL}/sanctum/csrf-cookie", timeout=30)
print(f"   Status: {r.status_code}")
print(f"   Cookies: {[c.name for c in session.cookies]}")

xsrf = unquote(session.cookies.get('XSRF-TOKEN', ''))
print(f"   XSRF: {xsrf[:30]}...")

print("\n3. POST /login...")
r = session.post(
    f"{BASE_URL}/login",
    data={'email': USERNAME, 'password': PASSWORD},
    headers={
        'X-XSRF-TOKEN': xsrf,
        'Content-Type': 'application/x-www-form-urlencoded',
    },
    allow_redirects=True,
    timeout=30
)
print(f"   Status: {r.status_code}")
print(f"   URL: {r.url}")

if 'dashboard' in r.url.lower():
    print("\n   SUCCESS!")
else:
    print("\n   FAILED - still at login page")