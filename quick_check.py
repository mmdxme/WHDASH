import urllib.request, urllib.error, time

categories = ['GENERAL','LOCALIZATION','SECURITY','APPEARANCE','USERS','ROLES','AUDIT','CRM','HR','WAREHOUSE','SALES','LOGISTICS','PURCHASING','PLANNING','MARKETING','INVENTORY','DATA_TOOLS']

for cat in categories:
    url = f'http://localhost:5000/admin/settings/{cat}'
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=3)
        print(f"OK  {cat} {resp.status}")
    except urllib.error.HTTPError as e:
        print(f"ERR {cat} HTTP {e.code}")
    except Exception as e:
        print(f"ERR {cat} {type(e).__name__}: {e}")
