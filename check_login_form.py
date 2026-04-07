"""Check login form structure"""
import requests
from urllib.parse import unquote

BASE_URL = 'https://panel.sdadparts.com'

session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
})

# Get base page
r = session.get(BASE_URL, timeout=30)
print(f"Base: {r.status_code}")

# Get CSRF
r = session.get(f'{BASE_URL}/sanctum/csrf-cookie', timeout=30)
print(f"CSRF: {r.status_code}")
csrf_token = session.cookies.get('XSRF-TOKEN', '')
csrf_token_decoded = unquote(csrf_token)
print(f"CSRF token: {csrf_token_decoded[:50]}...")

# Get login page HTML
r = session.get(f'{BASE_URL}/login', timeout=30)
print(f"Login page: {r.status_code}")

# Parse form fields
import re
# Find all input fields
inputs = re.findall(r'<input[^>]+>', r.text)
print(f"\nInput fields found: {len(inputs)}")
for inp in inputs:
    print(f"  {inp[:200]}")

# Find form action
forms = re.findall(r'<form[^>]+>', r.text)
print(f"\nForms found: {len(forms)}")
for form in forms:
    print(f"  {form}")

# Find token field
tokens = re.findall(r'name=["\']_token["\'][^>]+value=["\']([^"\']+)["\']', r.text)
print(f"\nToken fields: {tokens}")

tokens2 = re.findall(r'value=["\']([^"\']+)["\'][^>]+name=["\']_token["\']', r.text)
print(f"Token fields (reversed): {tokens2}")

# Find any hidden fields
hidden = re.findall(r'<input[^>]+type=["\']hidden["\'][^>]+>', r.text, re.IGNORECASE)
print(f"\nHidden fields: {len(hidden)}")
for h in hidden[:5]:
    print(f"  {h[:200]}")
