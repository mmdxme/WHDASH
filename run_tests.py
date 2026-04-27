import sys
sys.path.insert(0, '.')

print('=== Running Manual Security Module Tests ===')

# Test 1: Import and basic functionality
print('')
print('Test 1: Import and Initialize')
try:
    from security_models import (
        init_security_tables, get_sso_providers, get_security_policies,
        get_security_events, get_security_alerts,
        hash_password, verify_password, generate_session_id
    )
    init_security_tables()
    print('PASS: Models import and init')
except Exception as e:
    print('FAIL: ' + str(e))

# Test 2: SSO Providers
print('')
print('Test 2: SSO Providers')
try:
    providers = get_sso_providers()
    print('PASS: Found ' + str(len(providers)) + ' SSO providers')
    for p in providers[:3]:
        print('  - ' + str(p.get('provider_name', '?')) + ' (' + str(p.get('provider_code', '?')) + ')')
except Exception as e:
    print('FAIL: ' + str(e))

# Test 3: Security Policies
print('')
print('Test 3: Security Policies')
try:
    policies = get_security_policies()
    print('PASS: Found ' + str(len(policies)) + ' policies')
except Exception as e:
    print('FAIL: ' + str(e))

# Test 4: Security Events
print('')
print('Test 4: Security Events')
try:
    events = get_security_events(limit=5)
    print('PASS: Found ' + str(len(events)) + ' recent events')
except Exception as e:
    print('FAIL: ' + str(e))

# Test 5: Password Functions
print('')
print('Test 5: Password Hashing')
try:
    h, s = hash_password('SecurePassword123!')
    assert verify_password('SecurePassword123!', h, s) == True
    assert verify_password('WrongPassword', h, s) == False
    print('PASS: Password hashing/verification works')
except Exception as e:
    print('FAIL: ' + str(e))

# Test 6: Session ID Generation
print('')
print('Test 6: Session ID Generation')
try:
    sid1 = generate_session_id()
    sid2 = generate_session_id()
    assert sid1 != sid2
    assert len(sid1) > 30
    print('PASS: Generated session IDs: ' + sid1[:20] + '...')
except Exception as e:
    print('FAIL: ' + str(e))

# Test 7: Routes Registration
print('')
print('Test 7: Flask Routes')
try:
    from flask import Flask
    from security_routes import register_security_routes

    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test'
    register_security_routes(app)

    routes = [r.rule for r in app.url_map.iter_rules() if 'security' in r.rule]
    print('PASS: Registered ' + str(len(routes)) + ' security routes')

    critical_routes = ['/security/', '/security/mfa', '/security/sessions', '/security/events', '/security/alerts']
    for cr in critical_routes:
        if cr in routes:
            print('  PASS: ' + cr + ' exists')
        else:
            print('  FAIL: ' + cr + ' MISSING')
except Exception as e:
    print('FAIL: ' + str(e))
    import traceback
    traceback.print_exc()

print('')
print('=== All Tests Complete ===')
