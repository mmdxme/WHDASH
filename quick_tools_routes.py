"""
Quick Tools Routes
==================
API routes for the floating quick-tools system.
Provides endpoints for: Calculator, Notes, Tasks, Issues, Reminders, Favorites.
"""

from flask import Blueprint, request, session, jsonify
from functools import wraps
import re
from datetime import datetime, timedelta

from quick_tools_models import (
    get_user_notes, create_note, update_note, delete_note,
    get_user_reminders, get_due_reminders, create_reminder,
    mark_reminder_done, delete_reminder, snooze_reminder,
    mark_reminder_notified,
    get_user_favorites, create_favorite, update_favorite,
    delete_favorite, reorder_favorites,
    get_quick_preferences, update_quick_preferences,
    initialize_quick_tools_schema, get_default_favorites_for_user
)
from database import get_db_context, get_one
from permissions import user_has_permission

quick_tools_bp = Blueprint('quick_tools', __name__, url_prefix='/api/quick-tools')


def require_login(f):
    """Decorator to require login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated_function


def validate_csrf(f):
    """
    Decorator to validate CSRF token for mutating requests.
    Checks X-CSRF-TOKEN header or _token form field.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from header or form
        token = request.headers.get('X-CSRF-TOKEN')
        if not token:
            token = request.form.get('_token') if request.form else None
        if not token:
            token = request.args.get('_token')

        # Compare with session token
        session_token = session.get('csrf_token')
        if not session_token or not token:
            return jsonify({'success': False, 'error': 'CSRF token required'}), 403

        import hmac
        if not hmac.compare_digest(str(session_token), str(token)):
            return jsonify({'success': False, 'error': 'Invalid CSRF token'}), 403

        return f(*args, **kwargs)
    return decorated_function


def get_current_user_id():
    """Get current user ID from session."""
    return session.get('user_id')


def check_tool_permission(tool_name):
    """Check if user has permission to use a specific tool."""
    # Most tools are available to all logged-in users
    # Only certain admin tools would require special permissions
    if tool_name in ['admin_shortcuts']:
        return user_has_permission(session.get('user_id'), 'platform', 'settings', 'view')
    return True


# ============================================================================
# SAFE CALCULATOR
# ============================================================================

import operator

def safe_eval_expression(expr):
    """
    Safely evaluate a mathematical expression without using eval().
    Only allows basic arithmetic operations with proper precedence.
    """
    # Remove whitespace
    expr = expr.replace(' ', '')

    # Only allow digits, operators, decimal points, parentheses, and percentage
    if not re.match(r'^[\d+\-*/().%\s]+$', expr):
        return None, "Invalid characters in expression"

    # Check for empty expression
    if not expr:
        return None, "Empty expression"

    # Check for balanced parentheses
    open_count = expr.count('(')
    close_count = expr.count(')')
    if open_count != close_count:
        return None, "Unbalanced parentheses"

    try:
        # Handle percentage (x% = x/100) - replace before processing
        # But we need to be careful with the regex to not break negative numbers
        expr = re.sub(r'(\d+\.?\d*)%', r'(\1/100)', expr)

        # Parse and evaluate with proper precedence using shunting-yard algorithm
        result = evaluate_expression(expr)

        # Round to avoid floating point issues
        if isinstance(result, float):
            result = round(result, 10)
            # Remove trailing zeros
            if result == int(result):
                result = int(result)

        return result, None
    except ZeroDivisionError:
        return None, "Division by zero"
    except Exception as e:
        return None, str(e)


def tokenize(expr):
    """Convert expression string into tokens."""
    tokens = []
    i = 0
    while i < len(expr):
        c = expr[i]
        if c.isspace():
            i += 1
            continue
        if c.isdigit() or c == '.':
            # Parse number
            j = i
            while j < len(expr) and (expr[j].isdigit() or expr[j] == '.'):
                j += 1
            tokens.append(expr[i:j])
            i = j
        elif c in '+-*/()':
            tokens.append(c)
            i += 1
        else:
            raise ValueError(f"Invalid character: {c}")
    return tokens


def evaluate_expression(expr):
    """Evaluate expression using shunting-yard algorithm for proper precedence."""
    output_queue = []
    op_stack = []
    prec = {'+': 1, '-': 1, '*': 2, '/': 2}
    assoc = {'+': 'left', '-': 'left', '*': 'left', '/': 'left'}

    def apply_op():
        op = op_stack.pop()
        b = output_queue.pop()
        a = output_queue.pop()
        if op == '+':
            output_queue.append(a + b)
        elif op == '-':
            output_queue.append(a - b)
        elif op == '*':
            output_queue.append(a * b)
        elif op == '/':
            if b == 0:
                raise ZeroDivisionError()
            output_queue.append(a / b)

    tokens = tokenize(expr)

    i = 0
    while i < len(tokens):
        token = tokens[i]

        # Handle leading minus (unary) - also after operators
        if token == '-' and (i == 0 or tokens[i-1] == '(' or tokens[i-1] in '+-*/'):
            # It's a unary minus, consume the next number
            i += 1
            if i >= len(tokens):
                raise ValueError("Invalid expression")
            num_token = tokens[i]
            try:
                num = float(num_token) if '.' in num_token else int(num_token)
                output_queue.append(-num)
            except:
                raise ValueError(f"Invalid number: {num_token}")
            i += 1
            continue

        # Check if token is a number (int or float, including negative)
        is_number = False
        if token.replace('.', '', 1).replace('-', '').isdigit():
            is_number = True

        if is_number:
            try:
                num = float(token) if '.' in token else int(token)
                output_queue.append(num)
            except:
                raise ValueError(f"Invalid number: {token}")
        elif token == '(':
            op_stack.append(token)
        elif token == ')':
            while op_stack and op_stack[-1] != '(':
                apply_op()
            if not op_stack:
                raise ValueError("Mismatched parentheses")
            op_stack.pop()  # Remove '('
        elif token in '+-*/':
            while (op_stack and op_stack[-1] != '(' and
                   op_stack[-1] in prec and
                   prec[op_stack[-1]] >= prec[token] and
                   assoc[token] == 'left'):
                apply_op()
            op_stack.append(token)
        else:
            raise ValueError(f"Unknown token: {token}")
        i += 1

    while op_stack:
        if op_stack[-1] in '()':
            raise ValueError("Mismatched parentheses")
        apply_op()

    if len(output_queue) != 1:
        raise ValueError("Invalid expression")

    return output_queue[0]


@quick_tools_bp.route('/calculate', methods=['POST'])
@require_login
def calculate():
    """Evaluate a mathematical expression."""
    data = request.get_json() or {}
    expression = data.get('expression', '')
    
    if not expression:
        return jsonify({'success': False, 'error': 'No expression provided'})
    
    result, error = safe_eval_expression(expression)
    
    if error:
        return jsonify({'success': False, 'error': error})
    
    return jsonify({'success': True, 'result': result})


# ============================================================================
# QUICK NOTES
# ============================================================================

@quick_tools_bp.route('/notes', methods=['GET'])
@require_login
def get_notes():
    """Get all notes for current user."""
    user_id = get_current_user_id()
    notes = get_user_notes(user_id)
    return jsonify({'success': True, 'notes': notes})


@quick_tools_bp.route('/notes', methods=['POST'])
@require_login
@validate_csrf
def add_note():
    """Create a new note."""
    user_id = get_current_user_id()
    data = request.get_json() or {}
    
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'success': False, 'error': 'Content is required'})
    
    # Sanitize content
    content = sanitize_text(content)
    
    title = data.get('title', '')
    if title:
        title = sanitize_text(title)[:100]
    
    color = data.get('color', 'blue')
    valid_colors = ['blue', 'green', 'yellow', 'red', 'purple', 'gray']
    if color not in valid_colors:
        color = 'blue'
    
    note_id = create_note(user_id, content, title, color)
    note = get_one("SELECT * FROM quick_notes WHERE id = ?", (note_id,))
    
    return jsonify({'success': True, 'note': note})


@quick_tools_bp.route('/notes/<int:note_id>', methods=['PUT'])
@require_login
@validate_csrf
def edit_note(note_id):
    """Update an existing note."""
    user_id = get_current_user_id()
    data = request.get_json() or {}
    
    content = data.get('content')
    title = data.get('title')
    color = data.get('color')
    is_pinned = data.get('is_pinned')
    
    if content is not None:
        content = sanitize_text(content)
    if title is not None:
        title = sanitize_text(title)[:100]
    if color is not None:
        valid_colors = ['blue', 'green', 'yellow', 'red', 'purple', 'gray']
        if color not in valid_colors:
            color = None
    
    success = update_note(note_id, user_id, content, title, color, is_pinned)
    
    if not success:
        return jsonify({'success': False, 'error': 'Note not found or update failed'})
    
    note = get_one("SELECT * FROM quick_notes WHERE id = ?", (note_id,))
    return jsonify({'success': True, 'note': note})


@quick_tools_bp.route('/notes/<int:note_id>', methods=['DELETE'])
@require_login
@validate_csrf
def remove_note(note_id):
    """Delete a note."""
    user_id = get_current_user_id()
    success = delete_note(note_id, user_id)
    
    if not success:
        return jsonify({'success': False, 'error': 'Note not found'})
    
    return jsonify({'success': True})


# ============================================================================
# QUICK REMINDERS
# ============================================================================

@quick_tools_bp.route('/reminders', methods=['GET'])
@require_login
def get_reminders():
    """Get all reminders for current user."""
    user_id = get_current_user_id()
    include_done = request.args.get('include_done', 'false').lower() == 'true'
    reminders = get_user_reminders(user_id, include_done)
    return jsonify({'success': True, 'reminders': reminders})


@quick_tools_bp.route('/reminders/due', methods=['GET'])
@require_login
def get_reminders_due():
    """Get reminders that are due."""
    user_id = get_current_user_id()
    reminders = get_due_reminders(user_id)
    return jsonify({'success': True, 'reminders': reminders})


@quick_tools_bp.route('/reminders', methods=['POST'])
@require_login
@validate_csrf
def add_reminder():
    """Create a new reminder."""
    user_id = get_current_user_id()
    data = request.get_json() or {}
    
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'success': False, 'error': 'Title is required'})
    
    title = sanitize_text(title)[:200]
    
    # Parse remind_at
    remind_at_str = data.get('remind_at')
    if not remind_at_str:
        return jsonify({'success': False, 'error': 'Reminder time is required'})
    
    try:
        # Try ISO format first
        remind_at = datetime.fromisoformat(remind_at_str.replace('Z', '+00:00'))
        remind_at = remind_at.strftime('%Y-%m-%d %H:%M:%S')
    except ValueError:
        return jsonify({'success': False, 'error': 'Invalid datetime format'})
    
    description = data.get('description', '')
    if description:
        description = sanitize_text(description)[:500]
    
    link_url = data.get('link_url', '')
    if link_url and not link_url.startswith('/') and not link_url.startswith('http'):
        link_url = ''
    
    link_label = data.get('link_label', '')[:50]
    
    reminder_id = create_reminder(user_id, title, remind_at, description, link_url, link_label)
    reminder = get_one("SELECT * FROM quick_reminders WHERE id = ?", (reminder_id,))
    
    return jsonify({'success': True, 'reminder': reminder})


@quick_tools_bp.route('/reminders/<int:reminder_id>/done', methods=['POST'])
@require_login
@validate_csrf
def done_reminder(reminder_id):
    """Mark a reminder as done."""
    user_id = get_current_user_id()
    success = mark_reminder_done(reminder_id, user_id)
    
    if not success:
        return jsonify({'success': False, 'error': 'Reminder not found'})
    
    return jsonify({'success': True})


@quick_tools_bp.route('/reminders/<int:reminder_id>/snooze', methods=['POST'])
@require_login
@validate_csrf
def snooze_reminder_route(reminder_id):
    """Snooze a reminder."""
    user_id = get_current_user_id()
    data = request.get_json() or {}
    
    minutes = data.get('minutes', 30)
    if not isinstance(minutes, int) or minutes < 1:
        minutes = 30
    
    new_time = datetime.now() + timedelta(minutes=minutes)
    new_remind_at = new_time.strftime('%Y-%m-%d %H:%M:%S')
    
    success = snooze_reminder(reminder_id, user_id, new_remind_at)
    
    if not success:
        return jsonify({'success': False, 'error': 'Reminder not found'})
    
    reminder = get_one("SELECT * FROM quick_reminders WHERE id = ?", (reminder_id,))
    return jsonify({'success': True, 'reminder': reminder})


@quick_tools_bp.route('/reminders/<int:reminder_id>', methods=['DELETE'])
@require_login
@validate_csrf
def remove_reminder(reminder_id):
    """Delete a reminder."""
    user_id = get_current_user_id()
    success = delete_reminder(reminder_id, user_id)
    
    if not success:
        return jsonify({'success': False, 'error': 'Reminder not found'})
    
    return jsonify({'success': True})


# ============================================================================
# QUICK FAVORITES
# ============================================================================

@quick_tools_bp.route('/favorites', methods=['GET'])
@require_login
def get_favorites():
    """Get all favorites for current user."""
    user_id = get_current_user_id()
    favorites = get_user_favorites(user_id)
    
    # If no favorites exist, seed defaults
    if not favorites:
        defaults = get_default_favorites_for_user(user_id)
        for i, fav in enumerate(defaults):
            create_favorite(user_id, fav['label'], fav['url'], fav['icon'], fav['color'], i)
        favorites = get_user_favorites(user_id)
    
    return jsonify({'success': True, 'favorites': favorites})


@quick_tools_bp.route('/favorites', methods=['POST'])
@require_login
@validate_csrf
def add_favorite():
    """Create a new favorite."""
    user_id = get_current_user_id()
    data = request.get_json() or {}
    
    label = data.get('label', '').strip()
    if not label:
        return jsonify({'success': False, 'error': 'Label is required'})
    
    label = sanitize_text(label)[:50]
    
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'})
    
    # Validate URL
    if not url.startswith('/') and not url.startswith('http'):
        url = '/' + url
    
    icon = data.get('icon', 'fa-star')[:30]
    color = data.get('color', 'blue')
    valid_colors = ['blue', 'green', 'yellow', 'red', 'purple', 'gray', 'orange']
    if color not in valid_colors:
        color = 'blue'
    
    sort_order = data.get('sort_order', 0)
    if not isinstance(sort_order, int):
        sort_order = 0
    
    fav_id = create_favorite(user_id, label, url, icon, color, sort_order)
    favorite = get_one("SELECT * FROM quick_favorites WHERE id = ?", (fav_id,))
    
    return jsonify({'success': True, 'favorite': favorite})


@quick_tools_bp.route('/favorites/<int:favorite_id>', methods=['PUT'])
@require_login
@validate_csrf
def edit_favorite(favorite_id):
    """Update an existing favorite."""
    user_id = get_current_user_id()
    data = request.get_json() or {}
    
    label = data.get('label')
    url = data.get('url')
    icon = data.get('icon')
    color = data.get('color')
    sort_order = data.get('sort_order')
    
    if label is not None:
        label = sanitize_text(label)[:50]
    if url is not None:
        if not url.startswith('/') and not url.startswith('http'):
            url = '/' + url
    if icon is not None:
        icon = icon[:30]
    if color is not None:
        valid_colors = ['blue', 'green', 'yellow', 'red', 'purple', 'gray', 'orange']
        if color not in valid_colors:
            color = None
    
    success = update_favorite(favorite_id, user_id, label, url, icon, color, sort_order)
    
    if not success:
        return jsonify({'success': False, 'error': 'Favorite not found'})
    
    favorite = get_one("SELECT * FROM quick_favorites WHERE id = ?", (favorite_id,))
    return jsonify({'success': True, 'favorite': favorite})


@quick_tools_bp.route('/favorites/<int:favorite_id>', methods=['DELETE'])
@require_login
@validate_csrf
def remove_favorite(favorite_id):
    """Delete a favorite."""
    user_id = get_current_user_id()
    success = delete_favorite(favorite_id, user_id)
    
    if not success:
        return jsonify({'success': False, 'error': 'Favorite not found'})
    
    return jsonify({'success': True})


@quick_tools_bp.route('/favorites/reorder', methods=['POST'])
@require_login
@validate_csrf
def reorder_favorites_route():
    """Reorder favorites."""
    user_id = get_current_user_id()
    data = request.get_json() or {}
    
    orders = data.get('orders', [])
    if not isinstance(orders, list):
        return jsonify({'success': False, 'error': 'Invalid orders format'})
    
    success = reorder_favorites(user_id, orders)
    
    if not success:
        return jsonify({'success': False, 'error': 'Reorder failed'})
    
    return jsonify({'success': True})


@quick_tools_bp.route('/favorites/add-current', methods=['POST'])
@require_login
@validate_csrf
def add_current_page_favorite():
    """Add current page as a favorite."""
    user_id = get_current_user_id()
    data = request.get_json() or {}

    url = data.get('url', '')
    label = data.get('label', '')

    if not url:
        return jsonify({'success': False, 'error': 'URL is required'})

    if not label:
        # Try to get from navigation
        from navigation import get_menu_label
        label = get_menu_label(url) or url.split('/')[-1].replace('-', ' ').title()

    # Check if already exists
    existing = get_one(
        "SELECT id FROM quick_favorites WHERE user_id = ? AND url = ? AND is_active = 1",
        (user_id, url)
    )
    if existing:
        return jsonify({'success': False, 'error': 'Already in favorites'})

    fav_id = create_favorite(user_id, label, url, 'fa-bookmark', 'blue', 0)
    favorite = get_one("SELECT * FROM quick_favorites WHERE id = ?", (fav_id,))

    return jsonify({'success': True, 'favorite': favorite})


@quick_tools_bp.route('/favorites/navigation', methods=['GET'])
@require_login
def get_navigation_favorites():
    """
    Get available navigation items that can be added as favorites.
    Returns permission-filtered menu items.
    """
    user_id = get_current_user_id()

    # Import navigation structure
    from navigation import MENU_STRUCTURE

    available_items = []

    # Define icon mapping for common modules
    icon_map = {
        'dashboard': 'fa-home',
        'tasks': 'fa-tasks',
        'issues': 'fa-bug',
        'hr': 'fa-users',
        'wms': 'fa-warehouse',
        'logistics': 'fa-truck',
        'finance': 'fa-chart-line',
        'procurement': 'fa-shopping-cart',
        'sales': 'fa-dollar-sign',
        'marketing': 'fa-bullhorn',
        'quality': 'fa-check-circle',
        'maintenance': 'fa-wrench',
        'reports': 'fa-chart-bar',
        'settings': 'fa-cog',
    }

    def extract_items(structure, prefix=''):
        for key, value in structure.items():
            if isinstance(value, dict):
                # It's a module
                url = value.get('url')
                if url and url.startswith('/'):
                    icon = icon_map.get(key, 'fa-link')
                    available_items.append({
                        'label': key.replace('_', ' ').title(),
                        'url': url,
                        'icon': icon,
                        'category': prefix or 'Main'
                    })
                # Recurse into children
                if 'children' in value:
                    extract_items(value['children'], key)
            elif isinstance(value, list):
                # It's a list of items
                for item in value:
                    if isinstance(item, dict):
                        url = item.get('url')
                        if url and url.startswith('/'):
                            icon = icon_map.get(key, 'fa-link')
                            available_items.append({
                                'label': item.get('label', key).replace('_', ' ').title(),
                                'url': url,
                                'icon': icon,
                                'category': prefix or 'Main'
                            })

    extract_items(MENU_STRUCTURE)

    return jsonify({'success': True, 'navigation': available_items})


@quick_tools_bp.route('/favorites/check-access', methods=['POST'])
@require_login
@validate_csrf
def check_favorite_access():
    """
    Check if a URL is accessible for the current user.
    Used for permission-aware favorite filtering.
    """
    user_id = get_current_user_id()
    data = request.get_json() or {}

    url = data.get('url', '')
    if not url:
        return jsonify({'success': False, 'accessible': False})

    # Define restricted paths that require special permissions
    restricted_paths = {
        '/admin': ('platform', 'users', 'view'),
        '/settings': ('platform', 'settings', 'view'),
        '/tasks/settings': ('tasks', 'settings', 'view'),
        '/reports': ('reports', 'reports', 'view'),
    }

    # Check if URL matches restricted paths
    for path, (module, resource, action) in restricted_paths.items():
        if url.startswith(path):
            if not user_has_permission(user_id, module, resource, action):
                return jsonify({'success': True, 'accessible': False})
            break

    # If no restriction matched, allow access
    return jsonify({'success': True, 'accessible': True})


# ============================================================================
# QUICK TASK CREATOR
# ============================================================================

@quick_tools_bp.route('/task/create', methods=['POST'])
@require_login
@validate_csrf
def create_quick_task():
    """Create a task quickly via quick tools."""
    user_id = get_current_user_id()
    data = request.get_json() or {}
    
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'success': False, 'error': 'Title is required'})
    
    title = sanitize_text(title)[:200]
    
    description = data.get('description', '')
    if description:
        description = sanitize_text(description)[:1000]
    
    priority = data.get('priority', 'Medium')
    valid_priorities = ['Low', 'Medium', 'High', 'Critical']
    if priority not in valid_priorities:
        priority = 'Medium'
    
    due_at = data.get('due_at')
    if due_at:
        try:
            due_dt = datetime.fromisoformat(due_at.replace('Z', '+00:00'))
            due_at = due_dt.strftime('%Y-%m-%d %H:%M:%S')
        except ValueError:
            due_at = None
    
    assigned_to = data.get('assigned_to')
    if assigned_to:
        try:
            assigned_to = int(assigned_to)
        except (ValueError, TypeError):
            assigned_to = user_id  # Default to self
    else:
        assigned_to = user_id  # Default to self
    
    # Create the task
    with get_db_context() as db:
        db.execute("""
            INSERT INTO task_items (
                task_name, description, priority, status, due_at,
                assigned_to_user_id, created_by_user_id, company_id,
                progress, is_archived, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            title, description, priority, 'Open', due_at,
            assigned_to, user_id, session.get('company_id'),
            0, 0
        ))
        task_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # Log history
        db.execute("""
            INSERT INTO task_history (task_id, action, user_id, details, created_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (task_id, 'created', user_id, f'Task created via Quick Tools'))
    
    task = get_one("SELECT * FROM task_items WHERE id = ?", (task_id,))
    
    return jsonify({
        'success': True,
        'task': task,
        'task_url': f'/tasks/edit/{task_id}'
    })


@quick_tools_bp.route('/task/departments', methods=['GET'])
@require_login
def get_task_departments():
    """Get task departments for dropdown."""
    departments = get_all("SELECT id, name FROM task_departments ORDER BY name")
    return jsonify({'success': True, 'departments': departments})


@quick_tools_bp.route('/task/users', methods=['GET'])
@require_login
def get_task_users():
    """Get users for task assignment dropdown."""
    users = get_all("""
        SELECT id, username,
               COALESCE(display_name, username) as display_name
        FROM users ORDER BY display_name
    """)
    return jsonify({'success': True, 'users': users})


# ============================================================================
# QUICK ISSUE CREATOR
# ============================================================================

@quick_tools_bp.route('/issue/create', methods=['POST'])
@require_login
@validate_csrf
def create_quick_issue():
    """Create an issue quickly via quick tools."""
    user_id = get_current_user_id()
    data = request.get_json() or {}
    
    title = data.get('title', '').strip()
    if not title:
        return jsonify({'success': False, 'error': 'Title is required'})
    
    title = sanitize_text(title)[:200]
    
    description = data.get('description', '')
    if description:
        description = sanitize_text(description)[:1000]
    
    issue_type = data.get('issue_type', 'Issue')
    valid_types = ['Problem', 'Suggestion', 'Issue']
    if issue_type not in valid_types:
        issue_type = 'Issue'
    
    priority = data.get('priority', 'Medium')
    valid_priorities = ['Low', 'Medium', 'High', 'Critical']
    if priority not in valid_priorities:
        priority = 'Medium'
    
    category = data.get('category', '')
    if category:
        category = sanitize_text(category)[:50]
    
    # Create the issue - use actual column names from issue_items table
    with get_db_context() as db:
        db.execute("""
            INSERT INTO issue_items (
                issue, description, issue_type, priority, status,
                involved_departments, reported_by, created_by_user_id, company_id,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, (
            title, description, issue_type, priority, 'Open',
            category, str(user_id), user_id, session.get('company_id')
        ))
        issue_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    issue = get_one("SELECT * FROM issue_items WHERE id = ?", (issue_id,))
    
    return jsonify({
        'success': True,
        'issue': issue,
        'issue_url': f'/issues/{issue_id}'
    })


# ============================================================================
# PREFERENCES
# ============================================================================

@quick_tools_bp.route('/preferences', methods=['GET'])
@require_login
def get_preferences():
    """Get quick tool preferences."""
    user_id = get_current_user_id()
    prefs = get_quick_preferences(user_id)
    return jsonify({'success': True, 'preferences': prefs})


@quick_tools_bp.route('/preferences', methods=['PUT'])
@require_login
@validate_csrf
def save_preferences():
    """Update quick tool preferences."""
    user_id = get_current_user_id()
    data = request.get_json() or {}
    
    success = update_quick_preferences(user_id, **data)
    
    if not success:
        return jsonify({'success': False, 'error': 'Update failed'})
    
    prefs = get_quick_preferences(user_id)
    return jsonify({'success': True, 'preferences': prefs})


# ============================================================================
# BROWSER NOTIFICATIONS FOR REMINDERS
# ============================================================================

@quick_tools_bp.route('/reminders/check-due', methods=['GET'])
@require_login
def check_due_reminders():
    """
    Check for due reminders and return them for browser notification.
    This endpoint should be polled by the client.
    """
    user_id = get_current_user_id()

    # Get due reminders
    due_reminders = get_due_reminders(user_id)

    if not due_reminders:
        return jsonify({'success': True, 'due': [], 'count': 0})

    # Format for notification
    formatted = []
    for rem in due_reminders:
        # Mark as notified to prevent re-notification
        mark_reminder_notified(rem['id'])

        formatted.append({
            'id': rem['id'],
            'title': rem['title'],
            'description': rem.get('description', ''),
            'remind_at': rem['remind_at'],
            'link_url': rem.get('link_url', ''),
            'link_label': rem.get('link_label', '')
        })

    return jsonify({
        'success': True,
        'due': formatted,
        'count': len(formatted)
    })


# ============================================================================
# UTILITIES
# ============================================================================

def sanitize_text(text):
    """Sanitize text to prevent XSS."""
    if not text:
        return ''
    # Escape HTML entities
    text = str(text)
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    text = text.replace('"', '&quot;')
    text = text.replace("'", '&#x27;')
    return text


def escape_html(text):
    """Alias for sanitize_text for clarity."""
    return sanitize_text(text)


# ============================================================================
# INITIALIZATION
# ============================================================================

def register_quick_tools_routes(app):
    """Register quick tools routes with the app."""
    initialize_quick_tools_schema()
    app.register_blueprint(quick_tools_bp)
