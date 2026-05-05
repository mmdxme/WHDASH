import urllib.request
import http.cookiejar

# Let's try to login first
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Step 1: Get login page to extract form fields
resp = opener.open('http://localhost:5000/login', timeout=10)
data = resp.read().decode('utf-8', errors='replace')
print('Login page status:', resp.status)
print('Has password field:', 'name="password"' in data)
print('Has username field:', 'name="username"' in data)

# Step 2: POST login (try common admin credentials)
import urllib.parse
login_data = urllib.parse.urlencode({
    'username': 'admin',
    'password': 'admin123'
}).encode('utf-8')

try:
    resp2 = opener.open('http://localhost:5000/login', data=login_data, timeout=10)
    data2 = resp2.read().decode('utf-8', errors='replace')
    print('\nAfter login:')
    print('Status:', resp2.status)
    print('Redirected to:', resp2.geturl())
    print('Is login page:', 'Sign In' in data2)

    # Try to access campaigns now
    resp3 = opener.open('http://localhost:5000/marketing/campaigns', timeout=10)
    data3 = resp3.read().decode('utf-8', errors='replace')
    print('\nCampaigns after login:')
    print('Status:', resp3.status)
    print('Is login:', 'Sign In' in data3)
    if 'Sign In' not in data3:
        print('Page title:', data3[data3.find('<title'):data3.find('</title>')][:80])
except Exception as e:
    print('Error:', type(e).__name__, str(e)[:300])