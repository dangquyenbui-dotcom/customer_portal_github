# customer_portal/routes/main.py
"""
Main routes for Customer Portal (Login, Logout, Admin Login)
"""

from flask import Blueprint, render_template, redirect, url_for, session, request, flash, jsonify
from auth import authenticate_customer, authenticate_admin, login_required
from config import Config
from utils import get_client_info, validate_password 
from database.customer_data import customer_db 

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Redirects logged-in customers to inventory, others to login."""
    if 'customer' in session:
        if session.get('customer', {}).get('must_reset_password', False):
            return redirect(url_for('main.force_password_change'))
        return redirect(url_for('inventory.view_inventory'))
    elif 'admin' in session:
         return redirect(url_for('admin_panel.panel')) 
    return redirect(url_for('main.login'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handles customer login."""
    if 'customer' in session:
        if session.get('customer', {}).get('must_reset_password', False):
            return redirect(url_for('main.force_password_change'))
        return redirect(url_for('inventory.view_inventory')) 

    if request.method == 'POST':
        # === NEW: Honeypot Check ===
        # This 'hp_email' field is hidden from users. If it's filled out,
        # it's a bot. We silently fail by just re-rendering the page.
        if request.form.get('hp_email'):
            print("❌ [Bot] Honeypot field filled on customer login page. Bot detected.")
            return render_template('login.html', email=request.form.get('email', ''))
        # === END NEW ===

        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('login.html', email=email)

        customer_info = authenticate_customer(email, password)

        if customer_info:
            session.permanent = True 
            session['customer'] = {
                'customer_id': customer_info['customer_id'],
                'email': customer_info['email'],
                'first_name': customer_info['first_name'],
                'last_name': customer_info['last_name'],
                'erp_customer_name': customer_info['erp_customer_name'],
                'must_reset_password': customer_info.get('must_reset_password', False)
            }
            
            print(f"✅ Customer logged in: {customer_info['email']}")
            
            if customer_info.get('must_reset_password', False):
                flash('For your security, you must set a new password.', 'info')
                return redirect(url_for('main.force_password_change'))

            next_url = session.pop('next_url', None)
            return redirect(next_url or url_for('inventory.view_inventory'))
        else:
            flash('Invalid email or password, or account inactive.', 'error')
            print(f"❌ Login failed for customer: {email}")
            return render_template('login.html', email=email) 

    return render_template('login.html')

@main_bp.route('/logout')
@login_required 
def logout():
    """Logs out the customer."""
    customer_email = session.get('customer', {}).get('email', 'Unknown Customer')
    session.clear()
    flash('You have been successfully logged out.', 'success')
    print(f"🚪 Customer logged out: {customer_email}")
    return redirect(url_for('main.login'))

@main_bp.route('/force-change-password', methods=['GET', 'POST'])
@login_required
def force_password_change():
    """
    Shows a page forcing the user to change their password.
    """
    if not session.get('customer', {}).get('must_reset_password', False):
        return redirect(url_for('inventory.view_inventory'))
        
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if new_password != confirm_password:
            flash('Passwords do not match. Please try again.', 'error')
            return render_template('force_change_password.html')
            
        is_valid, error_msg = validate_password(new_password)
        if not is_valid:
            flash(error_msg, 'error')
            return render_template('force_change_password.html')
            
        customer_id = session['customer']['customer_id']
        success = customer_db.reset_password(customer_id, new_password)
        
        if success:
            session['customer']['must_reset_password'] = False
            session.modified = True 
            flash('Your password has been updated successfully.', 'success')
            return redirect(url_for('inventory.view_inventory'))
        else:
            flash('An error occurred while updating your password. Please try again.', 'error')

    return render_template('force_change_password.html')


# --- Admin Login (Optional Separate Route) ---
@main_bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Handles admin login."""
    if 'admin' in session:
        return redirect(url_for('admin_panel.panel')) 

    if request.method == 'POST':
        # === NEW: Honeypot Check ===
        if request.form.get('hp_email'):
            print("❌ [Bot] Honeypot field filled on admin login page. Bot detected.")
            return render_template('admin_login.html', username=request.form.get('username', ''))
        # === END NEW ===

        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('admin_login.html', username=username) 

        admin_info = authenticate_admin(username, password)

        if admin_info:
            session.permanent = True
            session['admin'] = admin_info 
            print(f"🔑 Admin logged in: {username} (Method: {admin_info.get('auth_method', 'unknown')})")
            return redirect(url_for('admin_panel.panel'))
        else:
            flash('Invalid admin credentials.', 'error')
            print(f"❌ Admin login failed for: {username}. See auth logs for details.")
            return render_template('admin_login.html', username=username)

    return render_template('admin_login.html') 

@main_bp.route('/admin-logout')
def admin_logout():
    """Logs out the admin."""
    admin_user = session.get('admin', {}).get('username', 'Unknown Admin')
    session.pop('admin', None) 
    flash('Administrator logged out.', 'success')
    print(f"🚪 Admin logged out: {admin_user}")
    return redirect(url_for('main.admin_login'))