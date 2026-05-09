import requests

s = requests.Session()

r = s.post('http://localhost:5000/login', 
           data={'username': 'admin', 'password': 'admin123'}, 
           allow_redirects=True)
print('Login status:', r.status_code, r.url)

r2 = s.get('http://localhost:5000/flow/new-chat')
print('new-chat status:', r2.status_code)

if 'startChat' in r2.text:
    print('startChat function: FOUND')
else:
    print('startChat function: NOT FOUND')

count = r2.text.count('onclick="startChat(')
print('Contact items rendered:', count)

if count == 0:
    idx = r2.text.find('No users found')
    if idx >= 0:
        print('Message: No users found')
    else:
        print('Page snippet:', r2.text[r2.text.find('users-list'):r2.text.find('users-list')+500] if 'users-list' in r2.text else 'NO users-list DIV')
