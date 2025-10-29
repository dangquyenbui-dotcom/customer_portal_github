# customer_portal/auth/customer_auth.py
"""
Customer Portal Authentication Module
Handles customer and admin login/authorization.
"""

from flask import session, redirect, url_for, flash, request, g
from functools import wraps
from werkzeug.security import check_password_hash
from database.customer_data import customer_db # Import the instance
from config import Config
from .ad_auth import check_ad_admin_auth

# --- Customer Authentication ---

def authenticate_customer(email, password):
    """Authenticates a customer using email and password."""
    return customer_db.verify_password(email, password)

def login_required(f):
    """
    Decorator to ensure a customer is logged in.
    Relies on g.customer being set by the @app.before_request hook.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # === MODIFICATION: Check g.customer, not session ===
        # g.customer is populated by the app.before_request hook
        # if the session cookie is valid AND the session is in the DB
        if not hasattr(g, 'customer') or g.customer is None:
            flash('Please log in to access this page.', 'warning')
            session['next_url'] = request.url
            return redirect(url_for('main.login'))
        
        # === MODIFICATION: Get reset flag from g.customer ===
        must_reset = g.customer.get('must_reset_password', False)
        
        allowed_endpoints = ('main.force_password_change', 'main.logout')
        
        if must_reset and request.endpoint not in allowed_endpoints:
            flash('For your security, you must set a new password.', 'info')
            return redirect(url_for('main.force_password_change'))
            
        return f(*args, **kwargs)
    return decorated_function

# --- Admin Authentication ---

def authenticate_admin(username, password):
    """
    Authenticates an admin user.
    First checks the local .env admin (cp_admin).
    If that fails, attempts to authenticate against Active Directory.
    """
    
    # --- 1. Try Local Admin (from .env) ---
    if username == Config.ADMIN_USERNAME and Config.ADMIN_PASSWORD_HASH:
        if check_password_hash(Config.ADMIN_PASSWORD_HASH, password):
            print(f"✅ [Admin Auth] Local admin logged in: {username}")
            return {'username': username, 'display_name': 'Local Admin', 'is_admin': True, 'auth_method': 'local'}
    
    # --- 2. Try Active Directory Admin ---
    # Only try AD if AD_SERVER is configured (to avoid errors)
    if Config.AD_SERVER:
        print(f"ℹ️  [Admin Auth] Local auth failed for {username}. Trying Active Directory...")
        
        ad_username = username.strip() # Start with the stripped, entered username
        
        if '@' in ad_username:
            original_username = ad_username
            ad_username = ad_username.split('@')[0]
            print(f"ℹ️  [Admin Auth] Trimmed email input '{original_username}' to AD username: {ad_username}")

        ad_admin_info = check_ad_admin_auth(ad_username, password) 
        
        if ad_admin_info:
            print(f"✅ [Admin Auth] AD admin logged in: {ad_username}")
            return ad_admin_info # This dict already contains 'is_admin': True
        else:
            print(f"ℹ️  [Admin Auth] AD login failed for: {ad_username}.")
    
    # --- 3. If both fail ---
    print(f"❌ [Admin Auth] All auth methods failed for: {username}")
    return None

def admin_required(f):
    """Decorator to ensure an admin is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # === MODIFICATION: Check g.admin ===
        if not hasattr(g, 'admin') or g.admin is None or not g.admin.get('is_admin'):
            if hasattr(g, 'customer') and g.customer: # Check g.customer
                 flash('You do not have permission to access the admin area.', 'error')
                 return redirect(url_for('inventory.view_inventory'))
            else:
                 flash('Please log in as an administrator to access this page.', 'warning')
                 return redirect(url_for('main.admin_login')) 
        return f(*args, **kwargs)
    return decorated_function