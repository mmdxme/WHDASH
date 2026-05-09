import urllib.request
import http.cookiejar

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Step 1: Get login page
resp = opener.open('http://localhost:5000/login', timeout=10)
data = resp.read().decode('utf-8', errors='replace')
print('Login page status:', resp.status)
print('Has login form:', 'name="password"' in data or 'type="password"' in data)

# Step 2: Try to login (we need to find the right credentials)
# For now, let's just try to access the page with existing cookies
resp2 = opener.open('http://localhost:5000/marketing/campaigns', timeout=10)
data2 = resp2.read().decode('utf-8', errors='replace')
print('\nCampaigns status:', resp2.status)
print('Is login page:', 'Sign In' in data2)
print('Cookies:', [(c.name, c.value[:20]) for c in cj])

# Check if we can access the dashboard
resp3 = opener.open('http://localhost:5000/marketing/', timeout=10)
data3 = resp3.read().decode('utf-8', errors='replace')
print('\nDashboard status:', resp3.status)
print('Is login page:', 'Sign In' in data3)