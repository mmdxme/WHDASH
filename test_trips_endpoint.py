import requests

response = requests.get('http://localhost:5000/logistics/trips', allow_redirects=False)
print(f"Status: {response.status_code}")
print(f"Location: {response.headers.get('Location', 'N/A')}")
print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
print(f"Content length: {len(response.content)}")
if response.status_code != 200:
    print(f"Response: {response.text[:500]}")
