# Run this from the WHDASH directory
import sys
sys.path.insert(0, 'C:/Users/sdads/WHDASH')

from flask import Flask, session, request
from application.context_processors import register_context_processors

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'
app.config['DATABASE_PATH'] = 'C:/Users/sdads/WHDASH/database.db'

register_context_processors(app)

# Simulate a logged-in session and render a template
with app.test_request_context('/customer-intelligence/dashboard'):
    session['user_id'] = 1
    session['language'] = 'en'
    # Try to get the context processor result via template render
    with app.app_context():
        from flask import render_template_string
        try:
            result = render_template_string('{{ main_menu }}')
            print('Result:', result)
        except Exception as e:
            print('Error:', type(e).__name__, e)