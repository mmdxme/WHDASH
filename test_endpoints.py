import urllib.request

endpoints = [
    'http://localhost:5000/accounting',
    'http://localhost:5000/procurement',
    'http://localhost:5000/delivery/customer_table'
]

for url in endpoints:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            print(f"{url}: {response.getcode()}")
    except urllib.error.HTTPError as e:
        print(f"{url} HTTPError: {e.code} - {e.reason}")
        import tempfile, hashlib
        fname = f"error_{hashlib.md5(url.encode()).hexdigest()}.html"
        with open(fname, 'wb') as f:
            f.write(e.read())
        print(f"Saved response to {fname}")
    except Exception as e:
        print(f"{url} Error: {e}")
