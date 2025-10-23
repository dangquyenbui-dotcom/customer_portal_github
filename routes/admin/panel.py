# customer_portal/routes/admin/panel.py
"""
Admin panel main dashboard route.
"""
from flask import Blueprint, render_template, redirect, url_for, session, flash
from auth import admin_required # Use the admin decorator

admin_panel_bp = Blueprint('admin_panel', __name__)

@admin_panel_bp.route('/') # Base route for /admin
@admin_required # Protect this route
def panel():
    """Displays the main admin dashboard."""
    # You can add logic here later to fetch dashboard stats if needed
    return render_template('admin/panel.html')