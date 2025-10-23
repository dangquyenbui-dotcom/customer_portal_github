# customer_portal/routes/admin/customers.py
"""
Admin routes for managing customer accounts.
"""
from flask import Blueprint, render_template, redirect, url_for, session, request, flash, jsonify
from auth import admin_required
from database.customer_data import customer_db # Import the instance
from database import get_erp_service # Import the ERP service
from utils.validators import validate_email, validate_password
from werkzeug.security import generate_password_hash # Needed for password updates

admin_customers_bp = Blueprint('admin_customers', __name__)

@admin_customers_bp.route('/customers')
@admin_required
def manage_customers():
    """Displays the customer management page."""
    search_term = request.args.get('search', '').strip()
    status_filter = request.args.get('status', 'active') # Default to active

    customers = customer_db.get_all_customers(include_inactive=True) # Get all for filtering

    filtered_customers = []
    for cust in customers:
        # Filter by status
        is_active = cust.get('is_active', False)
        status_match = False
        if status_filter == 'all':
            status_match = True
        elif status_filter == 'active' and is_active:
            status_match = True
        elif status_filter == 'inactive' and not is_active:
            status_match = True

        # Filter by search term (case-insensitive)
        search_match = False
        if not search_term:
            search_match = True
        else:
            term = search_term.lower()
            if (term in cust.get('first_name', '').lower() or
                term in cust.get('last_name', '').lower() or
                term in cust.get('email', '').lower() or
                term in cust.get('erp_customer_name', '').lower()):
                search_match = True

        if status_match and search_match:
            filtered_customers.append(cust)
            
    # --- NEW: Get ERP Customer List for Dropdown ---
    erp_service = get_erp_service()
    try:
        erp_customer_names = erp_service.get_all_customer_names()
    except Exception as e:
        print(f"❌ Error fetching ERP customer names: {e}")
        flash("Error fetching ERP customer list. Field will be a text input.", "error")
        erp_customer_names = []
    # --- End New Feature ---

    return render_template(
        'admin/customer_management.html',
        customers=filtered_customers,
        erp_customer_names=erp_customer_names, # Pass the list to the template
        search_term=search_term,
        status_filter=status_filter
        )

@admin_customers_bp.route('/customers/add', methods=['POST'])
@admin_required
def add_customer():
    """Handles adding a new customer."""
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    erp_customer_name = request.form.get('erp_customer_name', '').strip()

    # --- Validation ---
    is_valid_email, email_error = validate_email(email)
    if not is_valid_email:
        flash(f"Error adding customer: {email_error}", 'error')
        return redirect(url_for('admin_customers.manage_customers'))

    is_valid_password, password_error = validate_password(password)
    if not is_valid_password:
        flash(f"Error adding customer: {password_error}", 'error')
        return redirect(url_for('admin_customers.manage_customers'))

    if not first_name or not last_name or not erp_customer_name:
         flash("Error adding customer: First Name, Last Name, and ERP Customer Name are required.", 'error')
         return redirect(url_for('admin_customers.manage_customers'))
    # --- End Validation ---

    success, message = customer_db.create_customer(
        first_name, last_name, email, password, erp_customer_name
    )

    flash(message, 'success' if success else 'error')
    return redirect(url_for('admin_customers.manage_customers'))

@admin_customers_bp.route('/customers/edit/<int:customer_id>', methods=['POST'])
@admin_required
def edit_customer(customer_id):
    """Handles editing an existing customer."""
    first_name = request.form.get('edit_first_name', '').strip()
    last_name = request.form.get('edit_last_name', '').strip()
    email = request.form.get('edit_email', '').strip().lower()
    erp_customer_name = request.form.get('edit_erp_customer_name', '').strip()
    is_active = request.form.get('edit_is_active') == 'true' # Checkbox value

    # --- Validation ---
    is_valid_email, email_error = validate_email(email)
    if not is_valid_email:
        return jsonify({'success': False, 'message': email_error})

    if not first_name or not last_name or not erp_customer_name:
         return jsonify({'success': False, 'message': 'First Name, Last Name, and ERP Customer Name are required.'})
    # --- End Validation ---

    success, message = customer_db.update_customer(
        customer_id, first_name, last_name, email, erp_customer_name, is_active
    )

    # --- Password Update (Optional) ---
    new_password = request.form.get('edit_password', '')
    if new_password: # Only update password if a new one is provided
        is_valid_password, password_error = validate_password(new_password)
        if not is_valid_password:
             return jsonify({'success': False, 'message': f"Password not updated: {password_error}"})

        password_update_success = customer_db.reset_password(customer_id, new_password)
        if not password_update_success:
             # Don't overwrite the main success message if profile update worked
             if success:
                 message += " (Password update failed.)"
             else:
                 message = "Profile update failed and password update failed."
             success = False # Overall operation failed if password update failed
        elif success:
             message += " (Password updated.)"

    return jsonify({'success': success, 'message': message})


@admin_customers_bp.route('/customers/deactivate/<int:customer_id>', methods=['POST'])
@admin_required
def deactivate_customer(customer_id):
    """Deactivates a customer account."""
    success, message = customer_db.set_active_status(customer_id, is_active=False)
    # Using deleteItem JS function which expects this JSON format
    return jsonify({'success': success, 'message': message})


@admin_customers_bp.route('/customers/reactivate/<int:customer_id>', methods=['POST'])
@admin_required
def reactivate_customer(customer_id):
    """Reactivates a customer account."""
    success, message = customer_db.set_active_status(customer_id, is_active=True)
    # Adapt JS if needed, but this format is common
    return jsonify({'success': success, 'message': message})

# --- Placeholder for Password Reset Trigger ---
# @admin_customers_bp.route('/customers/trigger-reset/<int:customer_id>', methods=['POST'])
# @admin_required
# def trigger_password_reset(customer_id):
#     # 1. Get customer email
#     # 2. Create reset token using customer_db.create_password_reset_token
#     # 3. Construct reset link (e.g., /reset-password?token=...)
#     # 4. Send email with the link (using smtplib or Flask-Mail)
#     # 5. Return success/error JSON
#     return jsonify({'success': False, 'message': 'Password reset via email not yet implemented.'})