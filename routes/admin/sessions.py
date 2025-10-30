# customer_portal/routes/admin/sessions.py
"""
Admin route for viewing and managing active sessions.
"""
from flask import Blueprint, render_template, request, jsonify, g, current_app, flash
from auth import admin_required
from database.session_store import session_db
from database.audit_log import audit_db
# === NEW IMPORTS ===
from zoneinfo import ZoneInfo
from datetime import timezone
# === END NEW IMPORTS ===

admin_sessions_bp = Blueprint('admin_sessions', __name__)

@admin_sessions_bp.route('/sessions')
@admin_required
def view_sessions():
    """Displays the active sessions page."""
    
    # === NEW: Auto-prune logic ===
    auto_kick_enabled = current_app.config.get('AUTO_KICK_ENABLED', False)
    if auto_kick_enabled:
        print("ℹ️ [Admin Sessions] Auto-kick is ON. Pruning sessions > 3 hours old.")
        try:
            kicked_sessions = session_db.prune_by_hours(hours=3)
            if kicked_sessions:
                # Log each kick
                for kicked in kicked_sessions:
                    audit_db.log_event(
                        action_type='CUSTOMER_SESSION_KICK',
                        target_customer_id=kicked.get('customer_id'),
                        target_customer_email=kicked.get('target_customer_email'),
                        details="Auto-kicked session: inactive for > 3 hours."
                    )
                flash(f"Auto-kicked {len(kicked_sessions)} inactive session(s).", 'info')
        except Exception as e:
            print(f"❌ Error during auto-prune: {e}")
            flash("An error occurred during automatic session pruning.", 'error')
    # === END NEW ===

    active_sessions = []
    try:
        active_sessions = session_db.get_all_active()
        
        # === NEW: Timezone Conversion ===
        try:
            pst_pdt_zone = ZoneInfo("America/Los_Angeles")
            
            for s in active_sessions:
                # 1. Assume the DB time is naive UTC (from datetime.utcnow())
                # 2. Set the timezone to UTC
                # 3. Convert to the target PST/PDT timezone
                if s.get('last_seen'):
                    s['last_seen'] = s['last_seen'].replace(tzinfo=timezone.utc).astimezone(pst_pdt_zone)
                if s.get('created_at'):
                    s['created_at'] = s['created_at'].replace(tzinfo=timezone.utc).astimezone(pst_pdt_zone)
        except Exception as tz_e:
            print(f"⚠️ Error converting timezones: {tz_e}. Falling back to UTC.")
            # If conversion fails, the template will just show UTC
        # === END NEW ===

    except Exception as e:
        print(f"❌ Error fetching active sessions: {e}")
        flash("Error fetching active sessions.", "error")
    
    return render_template(
        'admin/active_sessions.html',
        sessions=active_sessions,
        auto_kick_enabled=auto_kick_enabled # Pass state to template
    )

# === NEW ROUTE ===
@admin_sessions_bp.route('/sessions/set-autokick', methods=['POST'])
@admin_required
def set_autokick():
    """Sets the auto-kick configuration."""
    data = request.get_json()
    enabled = data.get('enabled', False)
    
    current_app.config['AUTO_KICK_ENABLED'] = enabled
    status_str = "ENABLED" if enabled else "DISABLED"
    
    audit_db.log_event(
        action_type='SYSTEM_SETTING_CHANGE',
        details=f"Admin {g.admin.get('username')} {status_str} 3-hour session auto-kick."
    )
    print(f"ℹ️ [Admin Sessions] Auto-kick set to: {status_str}")

    kicked_count = 0
    if enabled:
        # Also run a prune immediately
        try:
            kicked_sessions = session_db.prune_by_hours(hours=3)
            kicked_count = len(kicked_sessions)
            if kicked_sessions:
                for kicked in kicked_sessions:
                    audit_db.log_event(
                        action_type='CUSTOMER_SESSION_KICK',
                        target_customer_id=kicked.get('customer_id'),
                        target_customer_email=kicked.get('target_customer_email'),
                        details="Kicked on enable: inactive for > 3 hours."
                    )
        except Exception as e:
            print(f"❌ Error during prune-on-enable: {e}")
            return jsonify({'success': False, 'message': f'Setting saved, but an error occurred during pruning: {e}'}), 500

    return jsonify({
        'success': True, 
        'message': f'Auto-kick {status_str}. {kicked_count} session(s) pruned.',
        'newState': status_str
    })
# === END NEW ROUTE ===

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