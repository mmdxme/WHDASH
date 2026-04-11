import re
import urllib.request
import urllib.parse
import http.cookiejar
import time

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def test_app():
    try:
        data = urllib.parse.urlencode({'username': 'admin', 'password': 'Admin@123'}).encode()
        req = opener.open('http://127.0.0.1:5000/login', data=data)
        req2 = opener.open('http://127.0.0.1:5000/')
        content = req2.read().decode('utf-8', errors='ignore')
        if 'BuildError' in content:
            match = re.search(r"Could not build url for endpoint '([^']+)'\. Did you mean '([^']+)' instead", content)
            if match:
                return match.group(1), match.group(2)
        elif 'werkzeug' in content.lower():
            return 'werkzeug_error', content[:200]
        return None, None
    except urllib.error.HTTPError as e:
        content = e.read().decode('utf-8', errors='ignore')
        match = re.search(r"Could not build url for endpoint '([^']+)'\. Did you mean '([^']+)' instead", content)
        if match:
            return match.group(1), match.group(2)
        return None, str(e.code)
    except Exception as e:
        return None, str(e)

def fix_endpoint_in_file(filepath, wrong, correct):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    old_url = "url_for('" + wrong + "')"
    new_url = "url_for('" + correct + "')"
    old_end = "request.endpoint == '" + wrong + "'"
    new_end = "request.endpoint == '" + correct + "'"

    fixed = False
    if old_url in content:
        content = content.replace(old_url, new_url)
        fixed = True
    if old_end in content:
        content = content.replace(old_end, new_end)
        fixed = True

    if fixed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

# Loop to find and fix errors
for iteration in range(100):
    wrong, correct = test_app()
    if wrong is None and correct is None:
        print('SUCCESS! All errors fixed!')
        break
    if wrong is None:
        print('Error: ' + str(correct))
        break

    print('Fixing: ' + wrong + ' -> ' + str(correct))

    fixed1 = fix_endpoint_in_file('templates/all_menus.html', wrong, correct)
    fixed2 = fix_endpoint_in_file('templates/menu_macros.html', wrong, correct)

    if not fixed1 and not fixed2:
        print('WARNING: Could not find ' + wrong + ' in template files')

    time.sleep(0.5)

print('Done!')