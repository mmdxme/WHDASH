"""
Personal Profile Management Module
================================
Comprehensive profile management system for the WHDASH platform.

This module provides:
- Profile overview and dashboard
- Personal information management
- Username and account identity
- Profile photo/avatar management
- Contact information
- Work/organization information
- Preferences and personalization
- Appearance and theme settings
- Notification preferences
- Security and password management
- Session and device management
- Privacy and visibility settings
- Activity log viewing
- Profile completion tracking

All routes require authentication via @require_login decorator.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from functools import wraps
from datetime import datetime, timedelta
import os
import re
import hashlib

from database import get_db, get_db_context, get_one, get_all, log_audit, create_notification
from permissions import user_has_permission

# ============================================================================
# BLUEPRINT SETUP
# ============================================================================

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

# Upload folder for avatars
AVATAR_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', 'avatars')
ALLOWED_AVATAR_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
os.makedirs(AVATAR_FOLDER, exist_ok=True)


# ============================================================================
# DECORATORS
# ============================================================================

def require_login(f):
    """Decorator to require authentication for profile routes."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please login to access this page.", "error")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def allowed_avatar_file(filename):
    """Check if the uploaded file is an allowed avatar type."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AVATAR_EXTENSIONS


def get_current_user():
    """Get current user data from session."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    user = get_one("""
        SELECT u.*, r.role_name, r.role_code,
               c.name as company_name, c.id as company_id,
               w.name as warehouse_name, w.id as warehouse_id
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        LEFT JOIN companies c ON u.company_id = c.id
        LEFT JOIN warehouses w ON u.warehouse_id = w.id
        WHERE u.id = ?
    """, (user_id,))
    return user


def get_user_profile_extra(user_id):
    """Get extended profile data from profile_extensions table."""
    return get_one("SELECT * FROM user_profile_extensions WHERE user_id = ?", (user_id,))


def calculate_profile_completion(user):
    """Calculate profile completion percentage."""
    total_fields = 10
    completed = 0
    
    # Check required fields
    if user.get('username'): completed += 1
    if user.get('email'): completed += 1
    if user.get('profile_pic'): completed += 1
    
    # Check extended profile
    ext = get_user_profile_extra(user['id'])
    if ext:
        if ext.get('first_name'): completed += 1
        if ext.get('last_name'): completed += 1
        if ext.get('phone'): completed += 1
        if ext.get('mobile'): completed += 1
        if ext.get('bio'): completed += 1
        if ext.get('date_of_birth'): completed += 1
    else:
        # Still count missing extended fields
        completed += 5  # Missing ext fields
    
    return int((completed / total_fields) * 100)


def get_user_sessions(user_id):
    """Get active sessions for a user (simulated from audit log)."""
    sessions = get_all("""
        SELECT * FROM platform_audit_log
        WHERE user_id = ? AND action IN ('LOGIN', 'SESSION_START')
        ORDER BY created_at DESC
        LIMIT 10
    """, (user_id,))
    return sessions


def get_user_activity_log(user_id, limit=50):
    """Get recent activity for a user from audit log."""
    activities = get_all("""
        SELECT * FROM platform_audit_log
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, limit))
    return activities


def validate_username(username, user_id):
    """
    Validate username availability and format.
    Returns (is_valid, error_message).
    """
    # Check length
    if len(username) < 3:
        return False, "Username must be at least 3 characters long."
    if len(username) > 30:
        return False, "Username must not exceed 30 characters."
    
    # Check format (alphanumeric, underscores, dots allowed)
    if not re.match(r'^[a-zA-Z0-9_\.]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and dots."
    
    # Check if starts/ends with special chars
    if username[0] in ('_', '.') or username[-1] in ('_', '.'):
        return False, "Username cannot start or end with underscore or dot."
    
    # Check reserved words
    reserved = ['admin', 'root', 'system', 'superadmin', 'moderator', 'support', 'help']
    if username.lower() in reserved:
        return False, f"The username '{username}' is reserved and cannot be used."
    
    # Check availability
    existing = get_one("SELECT id FROM users WHERE username = ? AND id != ?", (username, user_id))
    if existing:
        return False, "This username is already taken. Please choose another."
    
    return True, None


def validate_password_strength(password):
    """
    Validate password strength.
    Returns (is_valid, error_message, strength_score).
    Strength: 0=weak, 1=fair, 2=strong, 3=very strong.
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long.", 0
    
    score = 0
    
    # Length check
    if len(password) >= 10:
        score += 1
    if len(password) >= 12:
        score += 1
    
    # Complexity checks
    has_upper = bool(re.search(r'[A-Z]', password))
    has_lower = bool(re.search(r'[a-z]', password))
    has_digit = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
    
    if has_upper: score += 1
    if has_lower: score += 1
    if has_digit: score += 1
    if has_special: score += 1
    
    if score < 3:
        return False, "Password is too weak. Use a mix of uppercase, lowercase, numbers, and special characters.", 1
    elif score < 5:
        return True, "Password is fair. Consider adding more complexity for better security.", 2
    elif score < 7:
        return True, "Password is strong.", 3
    else:
        return True, "Password is very strong.", 4


def save_avatar(user_id, file):
    """Save uploaded avatar and return the filename."""
    if not file or file.filename == '':
        return None
    
    if not allowed_avatar_file(file.filename):
        return None
    
    # Get current avatar to delete later
    user = get_one("SELECT profile_pic FROM users WHERE id = ?", (user_id,))
    old_avatar = user['profile_pic'] if user else None
    
    # Create secure filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"avatar_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{ext}"
    filepath = os.path.join(AVATAR_FOLDER, filename)
    
    # Save file
    file.save(filepath)
    
    # Update database
    with get_db_context() as db:
        db.execute("UPDATE users SET profile_pic = ? WHERE id = ?", (filename, user_id))
        db.commit()
    
    # Delete old avatar if exists and not default
    if old_avatar and old_avatar != 'default.png':
        old_path = os.path.join(AVATAR_FOLDER, old_avatar)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except:
                pass  # Ignore deletion errors
    
    return filename


def delete_avatar(user_id):
    """Delete user's avatar and set to default."""
    user = get_one("SELECT profile_pic FROM users WHERE id = ?", (user_id,))
    if not user or not user['profile_pic']:
        return False
    
    old_avatar = user['profile_pic']
    if old_avatar != 'default.png':
        old_path = os.path.join(AVATAR_FOLDER, old_avatar)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except:
                pass
    
    with get_db_context() as db:
        db.execute("UPDATE users SET profile_pic = 'default.png' WHERE id = ?", (user_id,))
        db.commit()
    
    return True


# ============================================================================
# PROFILE ROUTES
# ============================================================================

@profile_bp.route('/')
@require_login
def index():
    """Profile overview - main dashboard."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # Get extended profile
    ext = get_user_profile_extra(user['id'])
    
    # Calculate completion
    completion = calculate_profile_completion(user)
    
    # Get recent activity
    recent_activity = get_user_activity_log(user['id'], 10)
    
    # Get session count
    session_count = len(get_user_sessions(user['id']))
    
    # Check password age
    password_info = get_one("""
        SELECT created_at FROM platform_audit_log
        WHERE user_id = ? AND action = 'PASSWORD_CHANGE'
        ORDER BY created_at DESC LIMIT 1
    """, (user['id'],))
    
    password_age_days = None
    if password_info and password_info['created_at']:
        try:
            pdate = datetime.strptime(password_info['created_at'], '%Y-%m-%d %H:%M:%S')
            password_age_days = (datetime.now() - pdate).days
        except:
            password_age_days = None
    
    return render_template('profile/index.html',
        user=user,
        profile=ext,
        completion=completion,
        recent_activity=recent_activity,
        session_count=session_count,
        password_age_days=password_age_days,
        page_title='Profile Overview'
    )


@profile_bp.route('/personal', methods=['GET', 'POST'])
@require_login
def personal():
    """Personal information management."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # Get or create extended profile
    ext = get_user_profile_extra(user['id'])
    
    if request.method == 'POST':
        action = request.form.get('action', 'update_personal')
        
        if action == 'update_personal':
            first_name = request.form.get('first_name', '').strip()
            last_name = request.form.get('last_name', '').strip()
            display_name = request.form.get('display_name', '').strip()
            preferred_name = request.form.get('preferred_name', '').strip()
            date_of_birth = request.form.get('date_of_birth', '').strip()
            gender = request.form.get('gender', '').strip()
            nationality = request.form.get('nationality', '').strip()
            bio = request.form.get('bio', '').strip()
            headline = request.form.get('headline', '').strip()
            spoken_languages = request.form.get('spoken_languages', '').strip()
            timezone = request.form.get('timezone', '').strip()
            notes = request.form.get('notes', '').strip()
            
            # Validate names
            if first_name and len(first_name) < 2:
                flash("First name is too short.", "error")
                return render_template('profile/personal.html', user=user, profile=ext, page_title='Personal Information')
            
            if last_name and len(last_name) < 2:
                flash("Last name is too short.", "error")
                return render_template('profile/personal.html', user=user, profile=ext, page_title='Personal Information')
            
            # Save to profile_extensions table
            with get_db_context() as db:
                if ext:
                    db.execute("""
                        UPDATE user_profile_extensions SET
                            first_name = ?, last_name = ?, display_name = ?, preferred_name = ?,
                            date_of_birth = ?, gender = ?, nationality = ?, bio = ?,
                            headline = ?, spoken_languages = ?, timezone = ?, notes = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE user_id = ?
                    """, (first_name, last_name, display_name, preferred_name,
                          date_of_birth, gender, nationality, bio,
                          headline, spoken_languages, timezone, notes, user['id']))
                else:
                    db.execute("""
                        INSERT INTO user_profile_extensions 
                        (user_id, first_name, last_name, display_name, preferred_name,
                         date_of_birth, gender, nationality, bio, headline,
                         spoken_languages, timezone, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (user['id'], first_name, last_name, display_name, preferred_name,
                          date_of_birth, gender, nationality, bio, headline,
                          spoken_languages, timezone, notes))
                db.commit()
            
            # Log audit
            log_audit('profile', user['id'], 'UPDATE', user_id=user['id'],
                     field_name='personal_info', notes='Personal information updated')
            
            flash("Personal information saved successfully.", "success")
            return redirect(url_for('profile.personal'))
    
    return render_template('profile/personal.html',
        user=user,
        profile=ext,
        page_title='Personal Information'
    )


@profile_bp.route('/username', methods=['GET', 'POST'])
@require_login
def username():
    """Username and account identity management."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        new_username = request.form.get('username', '').strip()
        
        if not new_username:
            flash("Username is required.", "error")
            return render_template('profile/username.html', user=user, page_title='Username & Identity')
        
        # Validate username
        is_valid, error_msg = validate_username(new_username, user['id'])
        if not is_valid:
            flash(error_msg, "error")
            return render_template('profile/username.html', user=user, page_title='Username & Identity')
        
        # Get old username for audit
        old_username = user['username']
        
        # Update username
        with get_db_context() as db:
            db.execute("UPDATE users SET username = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                      (new_username, user['id']))
            db.commit()
        
        # Log audit
        log_audit('profile', user['id'], 'USERNAME_CHANGE', user_id=user['id'],
                 old_value=old_username, new_value=new_username,
                 notes=f'Username changed from {old_username} to {new_username}')
        
        # Update session
        session['username'] = new_username
        
        flash(f"Username changed to '{new_username}' successfully.", "success")
        return redirect(url_for('profile.username'))
    
    # Get username change history
    username_history = get_all("""
        SELECT * FROM platform_audit_log
        WHERE user_id = ? AND action = 'USERNAME_CHANGE'
        ORDER BY created_at DESC
        LIMIT 10
    """, (user['id'],))
    
    return render_template('profile/username.html',
        user=user,
        username_history=username_history,
        page_title='Username & Identity'
    )


@profile_bp.route('/avatar', methods=['GET', 'POST'])
@require_login
def avatar():
    """Profile photo/avatar management."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        action = request.form.get('action', 'upload')
        
        if action == 'upload':
            if 'avatar' not in request.files:
                flash("No file selected.", "error")
                return redirect(url_for('profile.avatar'))
            
            file = request.files['avatar']
            
            if file.filename == '':
                flash("No file selected.", "error")
                return redirect(url_for('profile.avatar'))
            
            # Validate file
            if not allowed_avatar_file(file.filename):
                flash("Invalid file type. Allowed: PNG, JPG, JPEG, GIF.", "error")
                return redirect(url_for('profile.avatar'))
            
            # Check file size (max 5MB)
            file.seek(0, 2)
            size = file.tell()
            file.seek(0)
            
            if size > 5 * 1024 * 1024:
                flash("File too large. Maximum size is 5MB.", "error")
                return redirect(url_for('profile.avatar'))
            
            # Save avatar
            filename = save_avatar(user['id'], file)
            
            if filename:
                log_audit('profile', user['id'], 'AVATAR_CHANGE', user_id=user['id'],
                         notes=f'Avatar changed to {filename}')
                flash("Profile photo updated successfully.", "success")
            else:
                flash("Failed to upload avatar. Please try again.", "error")
        
        elif action == 'delete':
            if delete_avatar(user['id']):
                log_audit('profile', user['id'], 'AVATAR_DELETE', user_id=user['id'],
                         notes='Avatar deleted')
                flash("Profile photo removed.", "success")
            else:
                flash("Failed to remove photo.", "error")
        
        return redirect(url_for('profile.avatar'))
    
    return render_template('profile/avatar.html',
        user=user,
        page_title='Profile Photo'
    )


@profile_bp.route('/contact', methods=['GET', 'POST'])
@require_login
def contact():
    """Contact information management."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    ext = get_user_profile_extra(user['id'])
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        secondary_email = request.form.get('secondary_email', '').strip()
        mobile = request.form.get('mobile', '').strip()
        secondary_mobile = request.form.get('secondary_mobile', '').strip()
        whatsapp = request.form.get('whatsapp', '').strip()
        phone_extension = request.form.get('phone_extension', '').strip()
        country = request.form.get('country', '').strip()
        city = request.form.get('city', '').strip()
        address = request.form.get('address', '').strip()
        emergency_contact_name = request.form.get('emergency_contact_name', '').strip()
        emergency_contact_phone = request.form.get('emergency_contact_phone', '').strip()
        emergency_contact_relation = request.form.get('emergency_contact_relation', '').strip()
        preferred_communication = request.form.get('preferred_communication', '').strip()
        
        # Validate email format
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash("Invalid primary email format.", "error")
            return render_template('profile/contact.html', user=user, profile=ext, page_title='Contact Information')
        
        if secondary_email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', secondary_email):
            flash("Invalid secondary email format.", "error")
            return render_template('profile/contact.html', user=user, profile=ext, page_title='Contact Information')
        
        # Validate mobile format (basic)
        if mobile and not re.match(r'^[\d\s\-\+\(\)]{8,20}$', mobile):
            flash("Invalid mobile number format.", "error")
            return render_template('profile/contact.html', user=user, profile=ext, page_title='Contact Information')
        
        # Check if email is taken by another user
        if email != user.get('email'):
            existing = get_one("SELECT id FROM users WHERE email = ? AND id != ?", (email, user['id']))
            if existing:
                flash("This email is already registered to another user.", "error")
                return render_template('profile/contact.html', user=user, profile=ext, page_title='Contact Information')
            
            # Update email in users table
            with get_db_context() as db:
                db.execute("UPDATE users SET email = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                          (email, user['id']))
                db.commit()
            
            log_audit('profile', user['id'], 'EMAIL_CHANGE', user_id=user['id'],
                     old_value=user.get('email'), new_value=email,
                     notes='Primary email changed')
            
            flash("Primary email updated.", "info")
        
        # Save extended contact info
        with get_db_context() as db:
            if ext:
                db.execute("""
                    UPDATE user_profile_extensions SET
                        secondary_email = ?, mobile = ?, secondary_mobile = ?,
                        whatsapp = ?, phone_extension = ?, country = ?, city = ?,
                        address = ?, emergency_contact_name = ?, emergency_contact_phone = ?,
                        emergency_contact_relation = ?, preferred_communication = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (secondary_email, mobile, secondary_mobile, whatsapp,
                      phone_extension, country, city, address,
                      emergency_contact_name, emergency_contact_phone,
                      emergency_contact_relation, preferred_communication, user['id']))
            else:
                db.execute("""
                    INSERT INTO user_profile_extensions 
                    (user_id, secondary_email, mobile, secondary_mobile, whatsapp,
                     phone_extension, country, city, address, emergency_contact_name,
                     emergency_contact_phone, emergency_contact_relation, preferred_communication)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user['id'], secondary_email, mobile, secondary_mobile, whatsapp,
                      phone_extension, country, city, address, emergency_contact_name,
                      emergency_contact_phone, emergency_contact_relation, preferred_communication))
            db.commit()
        
        log_audit('profile', user['id'], 'UPDATE', user_id=user['id'],
                 field_name='contact_info', notes='Contact information updated')
        
        flash("Contact information saved successfully.", "success")
        return redirect(url_for('profile.contact'))
    
    return render_template('profile/contact.html',
        user=user,
        profile=ext,
        page_title='Contact Information'
    )


@profile_bp.route('/work', methods=['GET', 'POST'])
@require_login
def work():
    """Work and organization information."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    ext = get_user_profile_extra(user['id'])
    
    # Get departments for dropdown
    departments = get_all("SELECT * FROM departments ORDER BY name")
    
    # Get positions for dropdown
    positions = get_all("SELECT * FROM positions ORDER BY name")
    
    # Get employees for manager lookup
    employees = get_all("""
        SELECT e.*, u.username 
        FROM employees e
        LEFT JOIN users u ON e.user_id = u.id
        ORDER BY e.full_name
    """)
    
    if request.method == 'POST':
        department = request.form.get('department', '').strip()
        position = request.form.get('position', '').strip()
        job_title = request.form.get('job_title', '').strip()
        employee_code = request.form.get('employee_code', '').strip()
        work_email = request.form.get('work_email', '').strip()
        work_phone = request.form.get('work_phone', '').strip()
        hire_date = request.form.get('hire_date', '').strip()
        termination_date = request.form.get('termination_date', '').strip()
        reporting_to = request.form.get('reporting_to', '').strip()
        team = request.form.get('team', '').strip()
        territory = request.form.get('territory', '').strip()
        notes = request.form.get('notes', '').strip()
        
        # Save work info
        with get_db_context() as db:
            if ext:
                db.execute("""
                    UPDATE user_profile_extensions SET
                        department = ?, position = ?, job_title = ?, employee_code = ?,
                        work_email = ?, work_phone = ?, hire_date = ?, termination_date = ?,
                        reporting_to = ?, team = ?, territory = ?, work_notes = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (department, position, job_title, employee_code, work_email,
                      work_phone, hire_date, termination_date, reporting_to,
                      team, territory, notes, user['id']))
            else:
                db.execute("""
                    INSERT INTO user_profile_extensions 
                    (user_id, department, position, job_title, employee_code,
                     work_email, work_phone, hire_date, termination_date,
                     reporting_to, team, territory, work_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user['id'], department, position, job_title, employee_code,
                      work_email, work_phone, hire_date, termination_date,
                      reporting_to, team, territory, notes))
            db.commit()
        
        log_audit('profile', user['id'], 'UPDATE', user_id=user['id'],
                 field_name='work_info', notes='Work information updated')
        
        flash("Work information saved successfully.", "success")
        return redirect(url_for('profile.work'))
    
    return render_template('profile/work.html',
        user=user,
        profile=ext,
        departments=departments,
        positions=positions,
        employees=employees,
        page_title='Work Information'
    )


@profile_bp.route('/preferences', methods=['GET', 'POST'])
@require_login
def preferences():
    """User preferences and personalization."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # Get current preferences from user_preferences table
    prefs = get_one("SELECT * FROM user_preferences WHERE user_id = ?", (user['id'],))
    
    if request.method == 'POST':
        default_landing = request.form.get('default_landing', 'dashboard')
        default_language = request.form.get('default_language', 'en')
        default_timezone = request.form.get('default_timezone', 'UTC')
        date_format = request.form.get('date_format', 'DD/MM/YYYY')
        time_format = request.form.get('time_format', '24h')
        number_format = request.form.get('number_format', '1,234.56')
        currency_display = request.form.get('currency_display', 'symbol')
        default_view_mode = request.form.get('default_view_mode', 'list')
        sidebar_default = request.form.get('sidebar_default', 'expanded')
        compact_mode = request.form.get('compact_mode', '0')
        show_welcome = request.form.get('show_welcome', '1')
        
        # Save preferences
        with get_db_context() as db:
            if prefs:
                db.execute("""
                    UPDATE user_preferences SET
                        default_landing = ?, default_language = ?, default_timezone = ?,
                        date_format = ?, time_format = ?, number_format = ?,
                        currency_display = ?, default_view_mode = ?, sidebar_default = ?,
                        compact_mode = ?, show_welcome = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (default_landing, default_language, default_timezone, date_format,
                      time_format, number_format, currency_display, default_view_mode,
                      sidebar_default, compact_mode, show_welcome, user['id']))
            else:
                db.execute("""
                    INSERT INTO user_preferences 
                    (user_id, default_landing, default_language, default_timezone,
                     date_format, time_format, number_format, currency_display,
                     default_view_mode, sidebar_default, compact_mode, show_welcome)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user['id'], default_landing, default_language, default_timezone,
                      date_format, time_format, number_format, currency_display,
                      default_view_mode, sidebar_default, compact_mode, show_welcome))
            db.commit()
        
        log_audit('profile', user['id'], 'UPDATE', user_id=user['id'],
                 field_name='preferences', notes='User preferences updated')
        
        flash("Preferences saved successfully.", "success")
        return redirect(url_for('profile.preferences'))
    
    return render_template('profile/preferences.html',
        user=user,
        preferences=prefs,
        page_title='Preferences'
    )


@profile_bp.route('/appearance', methods=['GET', 'POST'])
@require_login
def appearance():
    """Appearance and theme settings."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    prefs = get_one("SELECT * FROM user_preferences WHERE user_id = ?", (user['id'],))
    
    # Import theme options
    from theme_system import get_available_themes, get_all_theme_ids
    
    available_themes = get_available_themes()
    theme_ids = get_all_theme_ids()
    
    if request.method == 'POST':
        theme = request.form.get('theme', 'dark')
        font_family = request.form.get('font_family', 'outfit')
        font_size = request.form.get('font_size', 'medium')
        font_weight = request.form.get('font_weight', 'regular')
        table_density = request.form.get('table_density', 'comfortable')
        reduced_motion = request.form.get('reduced_motion', '0')
        interface_direction = request.form.get('interface_direction', 'ltr')
        
        # Validate theme
        if theme not in theme_ids:
            flash("Invalid theme selection.", "error")
            return render_template('profile/appearance.html', user=user, preferences=prefs,
                                 available_themes=available_themes, page_title='Appearance')
        
        # Save appearance settings
        with get_db_context() as db:
            if prefs:
                db.execute("""
                    UPDATE user_preferences SET
                        theme = ?, font_family = ?, font_size = ?, font_weight = ?,
                        density = ?, reduced_motion = ?, interface_direction = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (theme, font_family, font_size, font_weight,
                      table_density, reduced_motion, interface_direction, user['id']))
            else:
                db.execute("""
                    INSERT INTO user_preferences 
                    (user_id, theme, font_family, font_size, font_weight,
                     density, reduced_motion, interface_direction)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (user['id'], theme, font_family, font_size, font_weight,
                      table_density, reduced_motion, interface_direction))
            db.commit()
        
        # Update session theme if needed
        session['theme'] = theme
        
        log_audit('profile', user['id'], 'THEME_CHANGE', user_id=user['id'],
                 new_value=theme, notes=f'Theme changed to {theme}')
        
        flash("Appearance settings saved.", "success")
        return redirect(url_for('profile.appearance'))
    
    return render_template('profile/appearance.html',
        user=user,
        preferences=prefs,
        available_themes=available_themes,
        page_title='Appearance'
    )


@profile_bp.route('/notifications', methods=['GET', 'POST'])
@require_login
def notifications():
    """Notification preferences."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # Get or create notification preferences
    notif_prefs = get_one("SELECT * FROM user_notification_preferences WHERE user_id = ?", (user['id'],))
    
    if request.method == 'POST':
        # In-app notifications
        inapp_tasks = request.form.get('inapp_tasks', '0')
        inapp_approvals = request.form.get('inapp_approvals', '0')
        inapp_deliveries = request.form.get('inapp_deliveries', '0')
        inapp_stock = request.form.get('inapp_stock', '0')
        inapp_sales = request.form.get('inapp_sales', '0')
        inapp_hr = request.form.get('inapp_hr', '0')
        inapp_system = request.form.get('inapp_system', '1')
        
        # Email notifications
        email_tasks = request.form.get('email_tasks', '0')
        email_approvals = request.form.get('email_approvals', '0')
        email_deliveries = request.form.get('email_deliveries', '0')
        email_stock = request.form.get('email_stock', '0')
        email_sales = request.form.get('email_sales', '0')
        email_digest = request.form.get('email_digest', '0')
        
        # General settings
        daily_summary = request.form.get('daily_summary', '0')
        weekly_summary = request.form.get('weekly_summary', '0')
        urgent_only = request.form.get('urgent_only', '0')
        sound_enabled = request.form.get('sound_enabled', '1')
        quiet_hours_enabled = request.form.get('quiet_hours_enabled', '0')
        quiet_hours_start = request.form.get('quiet_hours_start', '22:00')
        quiet_hours_end = request.form.get('quiet_hours_end', '08:00')
        
        # Save notification preferences
        with get_db_context() as db:
            if notif_prefs:
                db.execute("""
                    UPDATE user_notification_preferences SET
                        inapp_tasks = ?, inapp_approvals = ?, inapp_deliveries = ?,
                        inapp_stock = ?, inapp_sales = ?, inapp_hr = ?, inapp_system = ?,
                        email_tasks = ?, email_approvals = ?, email_deliveries = ?,
                        email_stock = ?, email_sales = ?, email_digest = ?,
                        daily_summary = ?, weekly_summary = ?, urgent_only = ?,
                        sound_enabled = ?, quiet_hours_enabled = ?,
                        quiet_hours_start = ?, quiet_hours_end = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (inapp_tasks, inapp_approvals, inapp_deliveries, inapp_stock,
                      inapp_sales, inapp_hr, inapp_system, email_tasks, email_approvals,
                      email_deliveries, email_stock, email_sales, email_digest,
                      daily_summary, weekly_summary, urgent_only, sound_enabled,
                      quiet_hours_enabled, quiet_hours_start, quiet_hours_end, user['id']))
            else:
                db.execute("""
                    INSERT INTO user_notification_preferences 
                    (user_id, inapp_tasks, inapp_approvals, inapp_deliveries, inapp_stock,
                     inapp_sales, inapp_hr, inapp_system, email_tasks, email_approvals,
                     email_deliveries, email_stock, email_sales, email_digest,
                     daily_summary, weekly_summary, urgent_only, sound_enabled,
                     quiet_hours_enabled, quiet_hours_start, quiet_hours_end)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user['id'], inapp_tasks, inapp_approvals, inapp_deliveries, inapp_stock,
                      inapp_sales, inapp_hr, inapp_system, email_tasks, email_approvals,
                      email_deliveries, email_stock, email_sales, email_digest,
                      daily_summary, weekly_summary, urgent_only, sound_enabled,
                      quiet_hours_enabled, quiet_hours_start, quiet_hours_end))
            db.commit()
        
        log_audit('profile', user['id'], 'UPDATE', user_id=user['id'],
                 field_name='notification_prefs', notes='Notification preferences updated')
        
        flash("Notification preferences saved.", "success")
        return redirect(url_for('profile.notifications'))
    
    return render_template('profile/notifications.html',
        user=user,
        notif_prefs=notif_prefs,
        page_title='Notifications'
    )


@profile_bp.route('/security', methods=['GET', 'POST'])
@require_login
def security():
    """Security and password management."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # Get password change history
    password_history = get_all("""
        SELECT * FROM platform_audit_log
        WHERE user_id = ? AND action IN ('PASSWORD_CHANGE', 'PASSWORD_RESET')
        ORDER BY created_at DESC
        LIMIT 5
    """, (user['id'],))
    
    # Get last password change
    last_change = password_history[0] if password_history else None
    
    if request.method == 'POST':
        action = request.form.get('action', 'change_password')
        
        if action == 'change_password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
            
            # Validate current password
            if not check_password_hash(user['password'], current_password):
                flash("Current password is incorrect.", "error")
                return render_template('profile/security.html', user=user,
                                     last_change=last_change, page_title='Security')
            
            # Validate new password
            if new_password != confirm_password:
                flash("New passwords do not match.", "error")
                return render_template('profile/security.html', user=user,
                                     last_change=last_change, page_title='Security')
            
            # Check password strength
            is_valid, msg, strength = validate_password_strength(new_password)
            if not is_valid:
                flash(msg, "error")
                return render_template('profile/security.html', user=user,
                                     last_change=last_change, page_title='Security')
            
            # Check if password was used recently (last 3 passwords)
            recent_passwords = get_all("""
                SELECT old_value FROM platform_audit_log
                WHERE user_id = ? AND action = 'PASSWORD_CHANGE'
                ORDER BY created_at DESC LIMIT 3
            """, (user['id'],))
            
            for rec in recent_passwords:
                if check_password_hash(rec['old_value'], new_password):
                    flash("You cannot reuse a recent password. Please choose a different one.", "error")
                    return render_template('profile/security.html', user=user,
                                         last_change=last_change, page_title='Security')
            
            # Hash new password
            new_hash = generate_password_hash(new_password)
            old_hash = user['password']
            
            # Update password
            with get_db_context() as db:
                db.execute("UPDATE users SET password = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                          (new_hash, user['id']))
                db.commit()
            
            # Log audit with old password hash for history (not the actual password)
            log_audit('profile', user['id'], 'PASSWORD_CHANGE', user_id=user['id'],
                     old_value=hashlib.md5(current_password.encode()).hexdigest()[:8],
                     notes='Password changed successfully')
            
            flash("Password changed successfully. Please remember your new password.", "success")
            return redirect(url_for('profile.security'))
        
        elif action == 'force_logout':
            # Force logout from all other sessions
            with get_db_context() as db:
                db.execute("""
                    DELETE FROM platform_audit_log
                    WHERE user_id = ? AND action IN ('LOGIN', 'SESSION_START')
                    AND created_at < datetime('now')
                """, (user['id'],))
                db.commit()
            
            log_audit('profile', user['id'], 'FORCE_LOGOUT', user_id=user['id'],
                     notes='Force logout from all sessions')
            
            flash("All other sessions have been terminated.", "success")
            return redirect(url_for('profile.security'))
    
    return render_template('profile/security.html',
        user=user,
        last_change=last_change,
        password_history=password_history,
        page_title='Security'
    )


@profile_bp.route('/sessions')
@require_login
def sessions():
    """Sessions and devices management."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # Get recent login sessions from audit log
    sessions = get_all("""
        SELECT * FROM platform_audit_log
        WHERE user_id = ? AND action IN ('LOGIN', 'SESSION_START')
        ORDER BY created_at DESC
        LIMIT 20
    """, (user['id'],))
    
    # Get session stats
    total_logins = get_one("""
        SELECT COUNT(*) as cnt FROM platform_audit_log
        WHERE user_id = ? AND action = 'LOGIN'
    """, (user['id'],))
    
    return render_template('profile/sessions.html',
        user=user,
        sessions=sessions,
        total_logins=total_logins['cnt'] if total_logins else 0,
        page_title='Sessions & Devices'
    )


@profile_bp.route('/privacy', methods=['GET', 'POST'])
@require_login
def privacy():
    """Privacy and visibility settings."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # Get or create privacy preferences
    privacy_prefs = get_one("SELECT * FROM user_privacy_settings WHERE user_id = ?", (user['id'],))
    
    if request.method == 'POST':
        profile_visibility = request.form.get('profile_visibility', 'internal')
        show_email = request.form.get('show_email', '0')
        show_phone = request.form.get('show_phone', '0')
        show_mobile = request.form.get('show_mobile', '0')
        show_department = request.form.get('show_department', '1')
        show_role = request.form.get('show_role', '1')
        show_last_login = request.form.get('show_last_login', '0')
        allow_directory_search = request.form.get('allow_directory_search', '1')
        show_activity_status = request.form.get('show_activity_status', '1')
        show_online_indicator = request.form.get('show_online_indicator', '1')
        
        with get_db_context() as db:
            if privacy_prefs:
                db.execute("""
                    UPDATE user_privacy_settings SET
                        profile_visibility = ?, show_email = ?, show_phone = ?,
                        show_mobile = ?, show_department = ?, show_role = ?,
                        show_last_login = ?, allow_directory_search = ?,
                        show_activity_status = ?, show_online_indicator = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """, (profile_visibility, show_email, show_phone, show_mobile,
                      show_department, show_role, show_last_login, allow_directory_search,
                      show_activity_status, show_online_indicator, user['id']))
            else:
                db.execute("""
                    INSERT INTO user_privacy_settings 
                    (user_id, profile_visibility, show_email, show_phone, show_mobile,
                     show_department, show_role, show_last_login, allow_directory_search,
                     show_activity_status, show_online_indicator)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (user['id'], profile_visibility, show_email, show_phone, show_mobile,
                      show_department, show_role, show_last_login, allow_directory_search,
                      show_activity_status, show_online_indicator))
            db.commit()
        
        log_audit('profile', user['id'], 'UPDATE', user_id=user['id'],
                 field_name='privacy_settings', notes='Privacy settings updated')
        
        flash("Privacy settings saved.", "success")
        return redirect(url_for('profile.privacy'))
    
    return render_template('profile/privacy.html',
        user=user,
        privacy_prefs=privacy_prefs,
        page_title='Privacy & Visibility'
    )


@profile_bp.route('/activity')
@require_login
def activity():
    """Personal activity log."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # Get activity with pagination
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    activities = get_all("""
        SELECT * FROM platform_audit_log
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ? OFFSET ?
    """, (user['id'], per_page, offset))
    
    # Get total count for pagination
    total = get_one("""
        SELECT COUNT(*) as cnt FROM platform_audit_log WHERE user_id = ?
    """, (user['id'],))
    
    total_pages = (total['cnt'] // per_page) + (1 if total['cnt'] % per_page else 0)
    
    return render_template('profile/activity.html',
        user=user,
        activities=activities,
        page=page,
        total_pages=total_pages,
        page_title='Activity Log'
    )


@profile_bp.route('/linked-accounts')
@require_login
def linked_accounts():
    """Linked accounts and external connections."""
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    
    # Get linked accounts if table exists
    linked = get_all("""
        SELECT * FROM user_linked_accounts WHERE user_id = ?
        ORDER BY created_at DESC
    """, (user['id'],))
    
    return render_template('profile/linked_accounts.html',
        user=user,
        linked_accounts=linked,
        page_title='Linked Accounts'
    )


@profile_bp.route('/api/validate-username')
@require_login
def api_validate_username():
    """API endpoint to check username availability."""
    username = request.args.get('username', '').strip()
    
    if not username:
        return jsonify({'valid': False, 'message': 'Username is required.'})
    
    user_id = session.get('user_id')
    is_valid, error_msg = validate_username(username, user_id)
    
    if is_valid:
        return jsonify({'valid': True, 'message': 'Username is available.'})
    else:
        return jsonify({'valid': False, 'message': error_msg})


@profile_bp.route('/api/check-password-strength')
@require_login
def api_check_password_strength():
    """API endpoint to check password strength."""
    password = request.args.get('password', '')
    
    is_valid, msg, strength = validate_password_strength(password)
    
    return jsonify({
        'valid': is_valid,
        'message': msg,
        'strength': strength,
        'score': strength
    })


# ============================================================================
# ROUTE REGISTRATION
# ============================================================================

def register_profile_routes(app):
    """Register profile blueprint with the Flask app."""
    app.register_blueprint(profile_bp)
    
    # Add profile routes to navigation breadcrumbs
    from navigation import ROUTE_BREADCRUMBS, PAGE_TITLES
    
    profile_routes = {
        '/profile': 'My Profile',
        '/profile/personal': 'Personal Information',
        '/profile/username': 'Username & Identity',
        '/profile/avatar': 'Profile Photo',
        '/profile/contact': 'Contact Information',
        '/profile/work': 'Work Information',
        '/profile/preferences': 'Preferences',
        '/profile/appearance': 'Appearance',
        '/profile/notifications': 'Notifications',
        '/profile/security': 'Security',
        '/profile/sessions': 'Sessions',
        '/profile/privacy': 'Privacy',
        '/profile/activity': 'Activity Log',
        '/profile/linked-accounts': 'Linked Accounts',
    }
    
    for route, title in profile_routes.items():
        if route not in PAGE_TITLES:
            PAGE_TITLES[route] = title
        if route not in ROUTE_BREADCRUMBS:
            ROUTE_BREADCRUMBS[route] = [
                {'label': 'My Profile', 'label_ar': 'ملفي', 'label_fa': 'پروفایل من', 'url': '/profile'}
            ]
