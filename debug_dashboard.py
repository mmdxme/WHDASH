import urllib.request
import http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

try:
    # First hit the login page to get session cookie
    resp = opener.open('http://localhost:5000/login', timeout=10)
    content = resp.read().decode('utf-8')

    # Check for flash messages or redirect indicators
    if 'flash' in content.lower():
        print('Login page has flash messages')
    if 'redirect' in content.lower():
        print('Login page has redirect logic')

    # Check for form action
    if 'action=' in content:
        import re
        forms = re.findall(r'<form[^>]*>', content)
        print('Forms found:', forms)

    # Try dashboard
    resp2 = opener.open('http://localhost:5000/finance/dashboard', timeout=10)
    content2 = resp2.read().decode('utf-8')

    # Print first 2000 chars of dashboard response
    print('\n--- Dashboard Response (first 2000 chars) ---')
    print(content2[:2000])
except Exception as e:
    import traceback
    print('Error:', e)
    traceback.print_exc()