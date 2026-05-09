import urllib.request
import http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

try:
    # First hit the login page to get session cookie
    resp = opener.open('http://localhost:5000/login', timeout=10)
    print('Login page status:', resp.status)
    content = resp.read().decode('utf-8')
    print('Login page title:', content.split('<title>')[1].split('</title>')[0] if '<title>' in content else 'No title')
    print()
    
    # Try dashboard
    resp2 = opener.open('http://localhost:5000/finance/dashboard', timeout=10)
    print('Dashboard status:', resp2.status)
    content2 = resp2.read().decode('utf-8')
    print('Dashboard title:', content2.split('<title>')[1].split('</title>')[0] if '<title>' in content2 else 'No title')
    print('Dashboard content length:', len(content2))
except Exception as e:
    print('Error:', e)