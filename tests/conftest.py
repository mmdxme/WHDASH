"""
WHDASH Test Infrastructure
==========================
Provides shared fixtures and utilities for testing the WHDASH application.
"""

import pytest
import os
import sys
import tempfile
import sqlite3
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables before importing app modules
os.environ['FLASK_ENV'] = 'testing'
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only'
os.environ['DATABASE_PATH'] = ':memory:'


@pytest.fixture(scope='function')
def test_db():
    """
    Create an in-memory test database with the basic schema.
    Yields a connection that is closed and discarded after the test.
    """
    # Create in-memory database
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    
    # Create basic schema
    schema = """
    CREATE TABLE companies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    );
    
    CREATE TABLE roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_name TEXT NOT NULL,
        company_id INTEGER,
        can_edit_stock INTEGER DEFAULT 0,
        can_manage_users INTEGER DEFAULT 0
    );
    
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role_id INTEGER NOT NULL,
        profile_pic TEXT DEFAULT 'default.png',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (role_id) REFERENCES roles(id)
    );
    
    CREATE TABLE role_permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_id INTEGER NOT NULL,
        module TEXT NOT NULL,
        resource TEXT NOT NULL,
        action TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(role_id, module, resource, action)
    );
    """
    conn.executescript(schema)
    
    # Insert test data
    conn.execute("INSERT INTO companies (name) VALUES ('Test Company')")
    conn.execute("""
        INSERT INTO roles (role_name, company_id, can_edit_stock, can_manage_users)
        VALUES ('Global Admin', NULL, 1, 1)
    """)
    conn.commit()
    
    yield conn
    
    conn.close()


@pytest.fixture(scope='function')
def app(test_db):
    """
    Create a test Flask application instance.
    """
    from flask import Flask
    from werkzeug.security import generate_password_hash
    
    # Create a minimal test app
    test_app = Flask(__name__)
    test_app.config['SECRET_KEY'] = 'test-secret-key'
    test_app.config['TESTING'] = True
    test_app.config['WTF_CSRF_ENABLED'] = False
    
    # Store test db connection factory
    def get_test_db():
        return test_db
    
    test_app.test_db = get_test_db
    
    # Add test routes
    @test_app.route('/test/login_required')
    def test_login_required():
        from flask import session
        if 'user_id' not in session:
            return 'Unauthorized', 401
        return 'OK'
    
    @test_app.route('/test/csrf', methods=['POST'])
    def test_csrf():
        from flask import request, session
        token = request.form.get('csrf_token')
        if not token or token != session.get('csrf_token'):
            return 'CSRF Failed', 400
        return 'OK'
    
    @test_app.route('/test/session')
    def test_session():
        from flask import session
        session['test'] = 'value'
        return 'OK'
    
    yield test_app


@pytest.fixture(scope='function')
def client(app):
    """
    Create a test client for the Flask application.
    """
    return app.test_client()


@pytest.fixture(scope='function')
def authenticated_client(app, test_db):
    """
    Create an authenticated test client with a logged-in user.
    """
    from werkzeug.security import generate_password_hash
    
    # Create a test user with hashed password
    hashed_pw = generate_password_hash('testpassword')
    test_db.execute("""
        INSERT INTO users (username, email, password, role_id)
        VALUES ('testuser', 'test@example.com', ?, 1)
    """, (hashed_pw,))
    test_db.commit()
    
    with app.test_client() as client:
        with client.session_transaction() as sess:
            sess['user_id'] = 1
            sess['username'] = 'testuser'
            sess['role_id'] = 1
        yield client


@pytest.fixture
def sample_user_data():
    """
    Return sample user data for creating test users.
    """
    return {
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'SecurePass123!',
        'role_id': 1
    }


@pytest.fixture
def sample_company_data():
    """
    Return sample company data for creating test companies.
    """
    return {
        'name': 'New Test Company'
    }
