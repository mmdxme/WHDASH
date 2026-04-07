import urllib.request
import urllib.parse
import http.cookiejar
import sys

# Create a cookie jar to persist cookies
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', 'Mozilla/5.0')]

try:
    # Get login page
    response = opener.open('http://127.0.0.1:5000/login')
    print(f"1. GET /login: {response.getcode()}")

    # Post login with no password first to see behavior
    data = urllib.parse.urlencode({}).encode()
    response = opener.open('http://127.0.0.1:5000/login', data=data)
    print(f"2. POST /login (empty): {response.getcode()}, URL: {response.geturl()}")
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()