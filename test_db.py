from app import app, get_db

with app.app_context():
    db = get_db()
    tables = db.execute('SELECT name FROM sqlite_master WHERE type="table"').fetchall()
    print("Tables:", [t[0] for t in tables])

    # Check if companies table exists
    if 'companies' in [t[0] for t in tables]:
        companies = db.execute('SELECT COUNT(*) as c FROM companies').fetchone()
        print(f"Companies count: {companies['c']}")
    else:
        print("No companies table!")

    # Check if users table exists
    if 'users' in [t[0] for t in tables]:
        users = db.execute('SELECT COUNT(*) as c FROM users').fetchone()
        print(f"Users count: {users['c']}")
    else:
        print("No users table!")