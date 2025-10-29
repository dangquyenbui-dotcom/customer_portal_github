# customer_portal/routes/admin/sessions.py
"""
Admin route for viewing and managing active sessions.
"""
from flask import Blueprint, render_template, request, jsonify, g
from auth import admin_required
from database.session_store import session_db
from database.audit_log import audit_db

admin_sessions_bp = Blueprint('admin_sessions', __name__)

@admin_sessions_bp.route('/sessions')
@admin_required
def view_sessions():
    """Displays the active sessions page."""
    active_sessions = []
    try:
        active_sessions = session_db.get_all_active()
    except Exception as e:
        print(f"❌ Error fetching active sessions: {e}")
        # Handle error, maybe flash a message
    
    return render_template(
        'admin/active_sessions.html',
        sessions=active_sessions
    )

@admin_sessions_bp.route('/sessions/kick', methods=['POST'])
@admin_required
def kick_session():
    """API endpoint to kick (delete) a customer session."""
    data = request.get_json()
    session_id = data.get('session_id')
    customer_id = data.get('customer_id')
    customer_email = data.get('customer_email')

    if not session_id:
        return jsonify({'success': False, 'message': 'Session ID is required.'}), 400

    try:
        success = session_db.delete(session_id)
        if success:
            # Log the kick action
            audit_db.log_event(
                action_type='CUSTOMER_SESSION_KICK',
                target_customer_id=customer_id,
                target_customer_email=customer_email,
                details=f"Admin {g.admin.get('username')} remotely ended session."
            )
            return jsonify({'success': True, 'message': 'Session ended successfully.'})
        else:
            return jsonify({'success': False, 'message': 'Session not found or already ended.'})
    except Exception as e:
        print(f"❌ Error kicking session {session_id}: {e}")
        return jsonify({'success': False, 'message': 'An error occurred.'}), 500