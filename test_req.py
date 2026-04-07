import requests

try:
    response = requests.get('http://127.0.0.1:5000/', timeout=5, allow_redirects=False)
    print(f"Status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    if response.status_code in [301, 302, 303, 307, 308]:
        print(f"Redirect to: {response.headers.get('Location', 'N/A')}")
    else:
        print(f"Content preview: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")