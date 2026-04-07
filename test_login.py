import requests

try:
    response = requests.get('http://127.0.0.1:5000/login', timeout=5)
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    print(f"Content preview: {response.text[:1000]}")
except Exception as e:
    print(f"Error: {e}")