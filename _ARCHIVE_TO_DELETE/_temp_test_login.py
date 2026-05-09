import urllib.request
import urllib.parse
import http.cookiejar

# Create a cookie jar to store session
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# First get the login page to get csrf token
try:
    # Try accessing marketing campaigns directly
    resp = opener.open('http://localhost:5000/marketing/campaigns', timeout=10)
    print('Campaigns Status:', resp.status)
    data = resp.read().decode('utf-8', errors='ignore')
    print('Length:', len(data))
    print('Title tag:', data[data.find('<title'):data.find('</title>')] if '<title>' in data else 'No title')
    print('Has form:', '<form' in data)
    print('Redirect chain:', [c.name for c in cj])
except Exception as e:
    print('Error:', type(e).__name__, str(e)[:300])