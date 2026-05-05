import urllib.request, urllib.error

cats = ['GENERAL','LOCALIZATION','SECURITY','APPEARANCE','USERS','ROLES','AUDIT','CRM','HR','WAREHOUSE','SALES','LOGISTICS','PURCHASING','PLANNING','MARKETING','INVENTORY','DATA_TOOLS']

for cat in cats:
    url = 'http://localhost:5000/admin/settings/' + cat
    try:
        req = urllib.request.Request(url)
        resp = urllib.request.urlopen(req, timeout=5)
        print('OK  %s %d' % (cat, resp.status))
    except urllib.error.HTTPError as e:
        print('ERR %s HTTP %d' % (cat, e.code))
    except Exception as e:
        print('ERR %s %s' % (cat, str(e)[:80]))
