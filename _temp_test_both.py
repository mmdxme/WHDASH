import urllib.request
import http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

try:
    resp = opener.open('http://localhost:5000/marketing/campaigns', timeout=10)
    data = resp.read().decode('utf-8', errors='replace')
    print('Status:', resp.status)
    # Check for error/redirect
    if 'Sign In' in data:
        print('Redirected to login page')
    else:
        print('Got marketing page')
        # Find redirect or error
        print('Meta refresh:', '<meta http-equiv="refresh"' in data)
        print('Has login text:', 'Sign In' in data or 'sign in' in data.lower())

    # Check dashboard
    resp2 = opener.open('http://localhost:5000/marketing/', timeout=10)
    data2 = resp2.read().decode('utf-8', errors='replace')
    print('\nDashboard status:', resp2.status)
    print('Dashboard is login:', 'Sign In' in data2)
    if 'Sign In' not in data2:
        print('Dashboard title:', data2[data2.find('<title'):data2.find('</title>')][:80])
except Exception as e:
    print('Error:', type(e).__name__, str(e)[:500])