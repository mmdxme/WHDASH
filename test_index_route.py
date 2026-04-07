import os
os.environ['FLASK_DEBUG'] = '1'

from app import app
with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['user_id'] = 1
        sess['username'] = 'admin'
        sess['role_id'] = 1
        sess['role_name'] = 'Global Admin'
        sess['company_id'] = None
        sess['can_edit_stock'] = True
        sess['can_manage_users'] = True
        sess['profile_pic'] = None

    response = client.get('/')
    print(f"GET / status: {response.status_code}")
    if response.status_code != 200:
        print(f"Error data: {response.data[:500]}")