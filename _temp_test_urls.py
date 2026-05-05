import urllib.request
import http.cookiejar
import sys

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', 'Mozilla/5.0')]

def test_url(url, name):
    try:
        resp = opener.open(url, timeout=10)
        data = resp.read().decode('utf-8', errors='replace')
        is_login = 'Sign In' in data or 'sign in' in data.lower()
        title = data[data.find('<title'):data.find('</title>')][:100] if '<title>' in data else 'No title'
        print(f'{name}: Status={resp.status}, Login={is_login}, Title={title}')
        return not is_login
    except Exception as e:
        print(f'{name}: Error - {type(e).__name__}: {str(e)[:100]}')
        return False

# Test marketing routes
print('=== Marketing Routes ===')
test_url('http://localhost:5000/marketing/', 'Dashboard')
test_url('http://localhost:5000/marketing/campaigns', 'Campaigns')

print('\n=== Other Routes for comparison ===')
test_url('http://localhost:5000/', 'Root')
test_url('http://localhost:5000/admin/', 'Admin')
test_url('http://localhost:5000/scm/', 'SCM')