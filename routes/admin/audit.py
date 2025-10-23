# customer_portal/routes/admin/audit.py
"""
Admin route for viewing the audit log.
"""
from flask import Blueprint, render_template, request
from auth import admin_required
from database.audit_log import audit_db # Import the audit instance

admin_audit_bp = Blueprint('admin_audit', __name__)

@admin_audit_bp.route('/audit')
@admin_required
def view_audit_log():
    """Displays the audit log page with filtering."""
    # Pagination (optional, simple for now)
    page = request.args.get('page', 1, type=int)
    limit = 50 # Logs per page
    offset = (page - 1) * limit

    # Filters
    admin_filter = request.args.get('admin_username', '').strip() or None
    action_filter = request.args.get('action_type', '').strip() or None
    customer_filter = request.args.get('customer_search', '').strip() or None # New filter

    logs, distinct_admins, distinct_actions = audit_db.get_logs(
        limit=limit,
        offset=offset,
        admin_filter=admin_filter,
        action_filter=action_filter,
        customer_filter=customer_filter # Pass the new filter
    )

    return render_template(
        'admin/audit_log.html',
        logs=logs,
        distinct_admins=distinct_admins,
        distinct_actions=distinct_actions,
        # Pass current filter values back to template
        current_admin=admin_filter,
        current_action=action_filter,
        current_customer_search=customer_filter,
        # Basic pagination info
        page=page,
        limit=limit
    )
