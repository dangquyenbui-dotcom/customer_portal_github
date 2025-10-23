# customer_portal/routes/admin/customers.py
"""
Admin routes for managing customer accounts.
"""
from flask import Blueprint, render_template, redirect, url_for, session, request, flash, jsonify
from auth import admin_required
from database.customer_data import customer_db
from database.audit_log import audit_db # --- NEW IMPORT ---
from database import get_erp_service
from utils.validators import validate_email, validate_password
from utils.email_service import send_password_reset_email
import secrets

admin_customers_bp = Blueprint('admin_customers', __name__)

@admin_customers_bp.route('/customers')
@admin_required
def manage_customers():
    """Displays the customer management page."""
    search_term = request.args.get('search', '').strip()
    status_filter = request.args.get('status', 'active')

    customers = customer_db.get_all_customers(include_inactive=True)

    filtered_customers = []
    for cust in customers:
        is_active = cust.get('is_active', False)
        status_match = (status_filter == 'all' or
                        (status_filter == 'active' and is_active) or
                        (status_filter == 'inactive' and not is_active))

        search_match = False
        if not search_term:
            search_match = True
        else:
            term = search_term.lower()
            if (term in cust.get('first_name', '').lower() or
                term in cust.get('last_name', '').lower() or
                term in cust.get('email', '').lower() or
                term in cust.get('erp_customer_name', '').lower().replace('|', ', ')):
                search_match = True

        if status_match and search_match:
            filtered_customers.append(cust)

    erp_service = get_erp_service()
    try:
        erp_customer_names = erp_service.get_all_customer_names()
    except Exception as e:
        print(f"❌ Error fetching ERP customer names: {e}")
        flash("Error fetching ERP customer list.", "error")
        erp_customer_names = []

    return render_template(
        'admin/customer_management.html',
        customers=filtered_customers,
        erp_customer_names=erp_customer_names,
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

    erp_customer_names_list = request.form.getlist('erp_customer_name')
    if not erp_customer_names_list:
        flash("Error adding customer: At least one ERP Customer Name (or 'All') must be selected.", 'error')
        return redirect(url_for('admin_customers.manage_customers'))

    erp_customer_name = "All" if "All" in erp_customer_names_list else "|".join(sorted(erp_customer_names_list))

    is_valid_email, email_error = validate_email(email)
    if not is_valid_email:
        flash(f"Error adding customer: {email_error}", 'error')
        return redirect(url_for('admin_customers.manage_customers'))

    is_valid_password, password_error = validate_password(password)
    if not is_valid_password:
        flash(f"Error adding customer: {password_error}", 'error')
        return redirect(url_for('admin_customers.manage_customers'))

    if not first_name or not last_name:
         flash("Error adding customer: First Name and Last Name are required.", 'error')
         return redirect(url_for('admin_customers.manage_customers'))

    # Attempt to create customer
    success, message = customer_db.create_customer(
        first_name, last_name, email, password, erp_customer_name
    )

    # --- NEW: Audit Logging ---
    if success:
        # Fetch the newly created customer to get the ID for logging
        new_customer = customer_db.get_customer_by_email(email)
        audit_db.log_event(
            action_type='CUSTOMER_CREATE',
            target_customer_id=new_customer['customer_id'] if new_customer else None,
            target_customer_email=email,
            details=f"Created customer {first_name} {last_name} with ERP names: '{erp_customer_name}'"
        )
    # --- END NEW ---

    flash(message, 'success' if success else 'error')
    return redirect(url_for('admin_customers.manage_customers'))

@admin_customers_bp.route('/customers/edit/<int:customer_id>', methods=['POST'])
@admin_required
def edit_customer(customer_id):
    """Handles editing an existing customer."""

    # --- NEW: Get current state for audit ---
    customer_before = customer_db.get_customer_by_id(customer_id)
    if not customer_before:
         return jsonify({'success': False, 'message': 'Customer not found.'})
    # --- END NEW ---

    first_name = request.form.get('edit_first_name', '').strip()
    last_name = request.form.get('edit_last_name', '').strip()
    email = request.form.get('edit_email', '').strip().lower()
    is_active_new = request.form.get('edit_is_active') == 'true'

    erp_customer_names_list = request.form.getlist('edit_erp_customer_name')
    if not erp_customer_names_list:
        return jsonify({'success': False, 'message': 'At least one ERP Customer Name (or "All") must be selected.'})

    erp_customer_name_new = "All" if "All" in erp_customer_names_list else "|".join(sorted(erp_customer_names_list))

    is_valid_email, email_error = validate_email(email)
    if not is_valid_email:
        return jsonify({'success': False, 'message': email_error})

    if not first_name or not last_name:
         return jsonify({'success': False, 'message': 'First Name and Last Name are required.'})

    # Attempt to update customer profile
    success, message = customer_db.update_customer(
        customer_id, first_name, last_name, email, erp_customer_name_new, is_active_new
    )

    # --- NEW: Audit Logging for profile changes ---
    changes = {}
    if success:
        if customer_before['first_name'] != first_name: changes['first_name'] = {'from': customer_before['first_name'], 'to': first_name}
        if customer_before['last_name'] != last_name: changes['last_name'] = {'from': customer_before['last_name'], 'to': last_name}
        if customer_before['email'] != email: changes['email'] = {'from': customer_before['email'], 'to': email}
        if customer_before['erp_customer_name'] != erp_customer_name_new: changes['erp_customer_name'] = {'from': customer_before['erp_customer_name'], 'to': erp_customer_name_new}
        if customer_before['is_active'] != is_active_new: changes['is_active'] = {'from': customer_before['is_active'], 'to': is_active_new}

        if changes:
             audit_db.log_event(
                 action_type='CUSTOMER_UPDATE',
                 target_customer_id=customer_id,
                 target_customer_email=email, # Log new email in case it changed
                 details=changes # Store changes as JSON
             )
    # --- END NEW ---

    # --- Password Update (Optional) ---
    new_password = request.form.get('edit_password', '')
    password_updated = False
    if new_password:
        is_valid_password, password_error = validate_password(new_password)
        if not is_valid_password:
             # Don't fail the whole request, just add warning
             message += f" (Password not updated: {password_error})"
        else:
            password_update_success = customer_db.admin_set_password(customer_id, new_password)
            if not password_update_success:
                 message += " (Password update failed.)"
                 success = False # Consider overall failure if password was attempted but failed
            else:
                 message += " (Password updated, user must reset.)"
                 password_updated = True # Flag for audit log

    # --- NEW: Audit Logging for optional password change ---
    if password_updated:
        audit_db.log_event(
            action_type='CUSTOMER_PW_SET_BY_ADMIN', # Different action from forced reset email
            target_customer_id=customer_id,
            target_customer_email=email,
            details="Admin set a new password via edit form."
        )
    # --- END NEW ---

    return jsonify({'success': success, 'message': message})


@admin_customers_bp.route('/customers/deactivate/<int:customer_id>', methods=['POST'])
@admin_required
def deactivate_customer(customer_id):
    """Deactivates a customer account."""
    customer = customer_db.get_customer_by_id(customer_id) # Get info before change
    success, message = customer_db.set_active_status(customer_id, is_active=False)
    # --- NEW: Audit Logging ---
    if success and customer:
        audit_db.log_event(
            action_type='CUSTOMER_DEACTIVATE',
            target_customer_id=customer_id,
            target_customer_email=customer['email'],
            details=f"Deactivated customer {customer['first_name']} {customer['last_name']}"
        )
    # --- END NEW ---
    return jsonify({'success': success, 'message': message})


@admin_customers_bp.route('/customers/reactivate/<int:customer_id>', methods=['POST'])
@admin_required
def reactivate_customer(customer_id):
    """Reactivates a customer account."""
    customer = customer_db.get_customer_by_id(customer_id) # Get info before change
    success, message = customer_db.set_active_status(customer_id, is_active=True)
    # --- NEW: Audit Logging ---
    if success and customer:
        audit_db.log_event(
            action_type='CUSTOMER_REACTIVATE',
            target_customer_id=customer_id,
            target_customer_email=customer['email'],
            details=f"Reactivated customer {customer['first_name']} {customer['last_name']}"
        )
    # --- END NEW ---
    return jsonify({'success': success, 'message': message})


# --- Admin-Initiated Password Reset ---
@admin_customers_bp.route('/customers/admin-reset-password/<int:customer_id>', methods=['POST'])
@admin_required
def admin_reset_password(customer_id):
    """
    Generates a new temporary password, updates the customer account,
    and emails the temporary password to the customer.
    """
    customer = customer_db.get_customer_by_id(customer_id)
    if not customer:
        return jsonify({'success': False, 'message': 'Customer not found.'})

    temp_password = secrets.token_urlsafe(10)
    db_success = customer_db.admin_set_password(customer_id, temp_password)

    if not db_success:
        return jsonify({'success': False, 'message': 'Failed to update password in database.'})

    # --- NEW: Audit Log before sending email (in case email fails) ---
    audit_db.log_event(
        action_type='ADMIN_PW_RESET_EMAIL',
        target_customer_id=customer_id,
        target_customer_email=customer['email'],
        details=f"Admin initiated password reset email for {customer['first_name']} {customer['last_name']}"
    )
    # --- END NEW ---

    email_success, email_message = send_password_reset_email(
        to_email=customer['email'],
        first_name=customer['first_name'],
        temp_password=temp_password
    )

    if not email_success:
        return jsonify({
            'success': False,
            'message': f"Password was reset, but email failed: {email_message}. " + \
                       f"Please manually provide the password to the user: {temp_password}"
        })

    return jsonify({
        'success': True,
        'message': f"Password reset email successfully sent to {customer['email']}."
    })

