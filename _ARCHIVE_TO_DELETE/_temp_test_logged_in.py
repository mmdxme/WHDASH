import urllib.request
import http.cookiejar
import urllib.parse

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Login first
login_data = urllib.parse.urlencode({
    'username': 'admin',
    'password': 'admin123'
}).encode('utf-8')
resp = opener.open('http://localhost:5000/login', data=login_data, timeout=10)
data = resp.read().decode('utf-8', errors='replace')
print('Login OK, redirected to:', resp.geturl())

# Now test both marketing routes
for url, name in [
    ('http://localhost:5000/marketing/', 'Dashboard'),
    ('http://localhost:5000/marketing/campaigns', 'Campaigns'),
    ('http://localhost:5000/marketing/campaigns/new', 'Campaigns New'),
]:
    resp = opener.open(url, timeout=10)
    data = resp.read().decode('utf-8', errors='replace')
    is_login = 'Sign In' in data
    title = data[data.find('<title'):data.find('</title>')][:80] if '<title>' in data else 'No title'
    print(f'{name}: Status={resp.status}, Login={is_login}, Title={title}')