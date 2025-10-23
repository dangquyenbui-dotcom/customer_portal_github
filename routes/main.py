# customer_portal/routes/main.py
"""
Main routes for Customer Portal (Login, Logout, Admin Login)
"""

from flask import Blueprint, render_template, redirect, url_for, session, request, flash, jsonify
from auth import authenticate_customer, authenticate_admin, login_required
from config import Config
from utils import get_client_info
# Import database sessions if reusing that logic
# from database.sessions import sessions_db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Redirects logged-in customers to inventory, others to login."""
    if 'customer' in session:
        return redirect(url_for('inventory.view_inventory'))
    elif 'admin' in session:
         return redirect(url_for('admin_panel.panel')) # Redirect admin to admin panel
    return redirect(url_for('main.login'))

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handles customer login."""
    if 'customer' in session:
        return redirect(url_for('inventory.view_inventory')) # Already logged in

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please enter both email and password.', 'error')
            return render_template('login.html', email=email)

        customer_info = authenticate_customer(email, password)

        if customer_info:
            # Store customer info in session
            session.permanent = True # Use the lifetime from config
            session['customer'] = {
                'customer_id': customer_info['customer_id'],
                'email': customer_info['email'],
                'first_name': customer_info['first_name'],
                'last_name': customer_info['last_name'],
                'erp_customer_name': customer_info['erp_customer_name'] # Crucial for data filtering
            }
            # Add session tracking if reusing sessions_db
            # ip, ua = get_client_info()
            # session_id = sessions_db.generate_session_id()
            # sessions_db.create_session(session_id, customer_info['email'], ip, ua) # Log email as username
            # session['session_id'] = session_id

            print(f"✅ Customer logged in: {customer_info['email']}")
            # Redirect to originally requested URL or inventory page
            next_url = session.pop('next_url', None)
            return redirect(next_url or url_for('inventory.view_inventory'))
        else:
            flash('Invalid email or password, or account inactive.', 'error')
            print(f"❌ Login failed for customer: {email}")
            return render_template('login.html', email=email) # Keep email in form

    # GET request
    return render_template('login.html')

@main_bp.route('/logout')
@login_required # Ensure only logged-in users can logout
def logout():
    """Logs out the customer."""
    customer_email = session.get('customer', {}).get('email', 'Unknown Customer')
    # session_id = session.get('session_id') # If using session tracking
    # if session_id:
    #     sessions_db.end_session(session_id)
    session.clear()
    flash('You have been successfully logged out.', 'success')
    print(f"🚪 Customer logged out: {customer_email}")
    return redirect(url_for('main.login'))

# --- Admin Login (Optional Separate Route) ---
@main_bp.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Handles admin login."""
    if 'admin' in session:
        return redirect(url_for('admin_panel.panel')) # Admin already logged in

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please enter both username and password.', 'error')
            return render_template('admin_login.html', username=username) # Reuse template or create new

        admin_info = authenticate_admin(username, password)

        if admin_info:
            session.permanent = True
            session['admin'] = admin_info # Store admin marker in session
            # Add session tracking if needed
            print(f"🔑 Admin logged in: {username}")
            return redirect(url_for('admin_panel.panel'))
        else:
            flash('Invalid admin credentials.', 'error')
            print(f"❌ Admin login failed for: {username}")
            return render_template('admin_login.html', username=username)

    # GET request
    return render_template('admin_login.html') # Need to create this template

@main_bp.route('/admin-logout')
def admin_logout():
    """Logs out the admin."""
    admin_user = session.get('admin', {}).get('username', 'Unknown Admin')
    session.pop('admin', None) # Remove only admin session key
    flash('Administrator logged out.', 'success')
    print(f"🚪 Admin logged out: {admin_user}")
    return redirect(url_for('main.admin_login'))