import urllib.request
import urllib.parse
import http.cookiejar

# Create a cookie jar to persist cookies
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# Get login page
response = opener.open('http://127.0.0.1:5000/login')
print(f"1. GET /login: {response.getcode()}")

# Post login credentials - try 'admin' with any password
data = urllib.parse.urlencode({
    'username': 'admin',
    'password': 'admin'  # placeholder
}).encode()

response = opener.open('http://127.0.0.1:5000/login', data=data)
print(f"2. POST /login: {response.getcode()}")
print(f"   Final URL: {response.geturl()}")
print(f"   Cookies: {[c.name for c in cj]}")

# Now try to access /
response = opener.open('http://127.0.0.1:5000/')
print(f"3. GET /: {response.getcode()}")
print(f"   Final URL: {response.geturl()}")