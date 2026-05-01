from app import app

# Simulate a real browser request hitting the dashboard
with app.test_client() as client:
    # Login first
    client.post('/login', data={
        'username': 'admin',
        'password': 'admin'
    }, follow_redirects=True)
    
    # Now check the dashboard page response
    resp = client.get('/dashboard/')
    print(f'Dashboard status: {resp.status_code}')
    
    # Look for any url_for errors in the response
    if b'BuildError' in resp.data:
        print('Found BuildError in response!')
        # Find the relevant part
        idx = resp.data.find(b'BuildError')
        print(f'Context: {resp.data[idx:idx+500]}')
    elif b'Could not build' in resp.data:
        print('Found "Could not build" error!')
        idx = resp.data.find(b'Could not build')
        print(f'Context: {resp.data[idx:idx+500]}')
    else:
        print('No BuildError in response')
        # Check if the export links are rendered
        if b'dashboard/api/export' in resp.data:
            print('Found dashboard/api/export in response')
        else:
            print('No dashboard/api/export found in response')