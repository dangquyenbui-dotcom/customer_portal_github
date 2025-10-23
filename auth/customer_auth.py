# customer_portal/auth/customer_auth.py
"""
Customer Portal Authentication Module
Handles customer and admin login/authorization.
"""

from flask import session, redirect, url_for, flash, request
from functools import wraps
from werkzeug.security import check_password_hash
from database.customer_data import customer_db # Import the instance
from config import Config

# --- Customer Authentication ---

def authenticate_customer(email, password):
    """Authenticates a customer using email and password."""
    return customer_db.verify_password(email, password)

def login_required(f):
    """Decorator to ensure a customer is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'customer' not in session:
            flash('Please log in to access this page.', 'warning')
            # Store the intended URL to redirect after login
            session['next_url'] = request.url
            return redirect(url_for('main.login'))
        # Optionally add session validation here (like in Production Portal)
        return f(*args, **kwargs)
    return decorated_function

# --- Admin Authentication ---

def authenticate_admin(username, password):
    """Authenticates the simple admin user."""
    if username == Config.ADMIN_USERNAME and Config.ADMIN_PASSWORD_HASH:
        if check_password_hash(Config.ADMIN_PASSWORD_HASH, password):
            # Return a simple dict indicating admin status
            return {'username': username, 'is_admin': True}
    return None

def admin_required(f):
    """Decorator to ensure an admin is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin' not in session or not session['admin'].get('is_admin'):
            # Check if it's a customer session trying to access admin
            if 'customer' in session:
                 flash('You do not have permission to access the admin area.', 'error')
                 return redirect(url_for('inventory.view_inventory')) # Redirect customer to their view
            else:
                 flash('Please log in as an administrator to access this page.', 'warning')
                 return redirect(url_for('main.admin_login')) # Redirect to a specific admin login
        # Optionally add session validation here
        return f(*args, **kwargs)
    return decorated_function

# --- Password Reset (Placeholder - Requires Email Setup) ---
# Add functions here later:
# - request_password_reset(email)
# - verify_reset_token(token)
# - perform_password_reset(token, new_password)