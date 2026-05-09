from app import app

# Test rendering the actual dashboard/index.html template
with app.test_client() as client:
    # First login to get a valid session
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['company_id'] = 1
        sess['language'] = 'en'
        sess['username'] = 'Test User'
        sess['user_role'] = 'Admin'
        sess['logged_in'] = True
    
    # Now try to access the dashboard
    try:
        resp = client.get('/dashboard/')
        print(f'Dashboard response status: {resp.status_code}')
        
        if resp.status_code != 200:
            print(f'Response data: {resp.data[:500]}')
    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()