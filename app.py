# customer_portal/app.py
"""
Customer Portal - Main Flask Application
"""

from flask import Flask, session, g, redirect, url_for, flash, request
import os
from datetime import timedelta
from config import Config
import socket
import traceback
from utils.helpers import get_client_info
import secrets
import random

def create_app():
    app = Flask(__name__)

    # --- Configuration ---
    app.secret_key = Config.SECRET_KEY
    app.permanent_session_lifetime = Config.PERMANENT_SESSION_LIFETIME
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production' 
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    app.static_folder = 'static'
    app.static_url_path = '/static'

    @app.context_processor
    def inject_global_vars():
        # Make config, session, and g available globally in templates
        return dict(
            config=Config,
            session=session,
            g=g
        )

    # --- Register Blueprints ---
    register_blueprints(app)

    # --- Initialize Database Connections (Test on startup) ---
    initialize_database_connections()

    @app.before_request
    def load_user_from_session():
        # === FIX: Skip this entire hook for static file requests ===
        if request.endpoint == 'static':
            return
        # === END FIX ===

        # Get DB instances
        from database import session_db, customer_db

        # --- Prune stale sessions (1% chance) ---
        if random.randint(1, 100) == 1:
            try:
                session_db.prune_inactive(Config.SESSION_HOURS)
            except Exception as e:
                print(f"⚠️ Error pruning stale sessions: {e}")

        # --- Admin session handling (unchanged) ---
        if 'admin' in session:
            g.admin = session['admin']
        else:
            g.admin = None

        # --- Customer session handling (NEW LOGIC) ---
        g.customer = None # Default to no customer
        customer_session_id = session.get('customer_session_id')
        customer_id_in_session = session.get('customer', {}).get('customer_id')

        if customer_session_id and customer_id_in_session:
            # We have a session cookie. Now, validate it against the DB.
            active_session = session_db.get(customer_session_id)

            if active_session and active_session['customer_id'] == customer_id_in_session:
                # Session is valid and in the DB.
                # Load full customer data into g for this request
                g.customer = customer_db.get_customer_by_id(customer_id_in_session)

                # Update the session's 'last_seen' time
                ip, ua = get_client_info()
                session_db.create_or_update(
                    customer_session_id,
                    customer_id_in_session,
                    ip,
                    ua
                )
            else:
                # Session ID is not in the DB (or customer_id mismatch)
                # This means they were kicked or the session expired/pruned.
                if active_session is None and 'customer' in session:
                     flash('Your session was ended, possibly by an administrator. Please log in again.', 'warning')

                # Force logout by clearing the cookie session
                session.pop('customer', None)
                session.pop('customer_session_id', None)

    @app.teardown_appcontext
    def teardown_db(exception=None):
        pass

    print("✅ Customer Portal application created.")
    return app

def register_blueprints(app):
    """Register all application blueprints"""
    print("⏳ Registering blueprints...")
    try:
        from routes.main import main_bp
        from routes.inventory import inventory_bp
        from routes.admin.panel import admin_panel_bp
        from routes.admin.customers import admin_customers_bp
        from routes.admin.audit import admin_audit_bp
        from routes.admin.sessions import admin_sessions_bp
        # === NEW IMPORT ===
        from routes.admin.analytics import admin_analytics_bp

        app.register_blueprint(main_bp)
        app.register_blueprint(inventory_bp, url_prefix='/inventory')

        app.register_blueprint(admin_panel_bp, url_prefix='/admin')
        app.register_blueprint(admin_customers_bp, url_prefix='/admin')
        app.register_blueprint(admin_audit_bp, url_prefix='/admin')
        app.register_blueprint(admin_sessions_bp, url_prefix='/admin')
        # === NEW REGISTRATION ===
        app.register_blueprint(admin_analytics_bp, url_prefix='/admin')

        print("✅ Blueprints registered.")
    except ImportError as e:
         print(f"❌ Error importing blueprints: {e}")
         traceback.print_exc()
    except Exception as e:
         print(f"❌ Unexpected error registering blueprints: {e}")
         traceback.print_exc()


def initialize_database_connections():
    """Initialize and test database connections on startup"""
    print("⏳ Initializing database connections...")
    all_ok = True
    try:
        from database import get_db
        local_db = get_db()
        if local_db.test_connection():
            print("✅ Local DB (CustomerPortalDB): Connected")
            # === MODIFIED: Added analytics_db ===
            from database import customer_db, audit_db, session_db, analytics_db
            print("✅ Local DB Tables (Customers, AuditLog, ActiveSessions, Analytics) Checked/Created.")
        else:
            print("❌ Local DB (CustomerPortalDB): Connection FAILED")
            all_ok = False
    except Exception as e:
        print(f"❌ Local DB (CustomerPortalDB): Initialization Error: {e}")
        traceback.print_exc()
        all_ok = False

    try:
        from database import get_erp_db_connection # Use the __init__ file import
        erp_db = get_erp_db_connection()
        if erp_db and erp_db.connection:
            print("✅ ERP DB (Read-Only): Connected")
        elif erp_db and erp_db._connection_string:
             print("✅ ERP DB (Read-Only): Connection String Ready")
        else:
             print("❌ ERP DB (Read-Only): Connection FAILED during setup")
             all_ok = False
    except Exception as e:
        print(f"❌ ERP DB (Read-Only): Initialization Error: {e}")
        traceback.print_exc()
        all_ok = False

    if all_ok:
        print("✅ All database connections initialized successfully.")
    else:
        print("⚠️ Errors occurred during database initialization. Check logs and config.")


def get_local_ip():
    """Get the local IP address of the machine"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🚀 LAUNCHING CUSTOMER PORTAL")
    print("="*50)

    project_root = os.path.dirname(__file__)
    os.makedirs(os.path.join(project_root, 'static', 'css'), exist_ok=True)
    os.makedirs(os.path.join(project_root, 'static', 'js'), exist_ok=True)
    os.makedirs(os.path.join(project_root, 'static', 'img'), exist_ok=True)
    os.makedirs(os.path.join(project_root, 'templates', 'admin'), exist_ok=True)
    os.makedirs(os.path.join(project_root, 'templates', 'email'), exist_ok=True)

    local_ip = get_local_ip()

    if not Config.validate():
        print("\n❌ Aborting due to configuration errors.")
        exit(1)

    print("\n--- Configuration ---")
    print(f"Database:     {Config.DB_SERVER}/{Config.DB_NAME}")
    print(f"ERP Database: {Config.ERP_DB_SERVER}/{Config.ERP_DB_NAME}")
    print(f"SMTP Server:  {Config.SMTP_SERVER}:{Config.SMTP_PORT}")
    print(f"Secret Key:   {'Set' if Config.SECRET_KEY != 'dev-key-change-in-production' else '!!! NOT SET (Using Default) !!!'}")
    print(f"Admin User:   {Config.ADMIN_USERNAME}")
    print("-" * 20)

    app = create_app()

    print("\n" + "="*50)
    print("✅ SERVER READY - ACCESS URLS:")
    print(f"   Local:   http://localhost:5001")
    print(f"   Network: http://{local_ip}:5001")
    print("\n" + "="*50)
    debug_mode = os.getenv('FLASK_ENV') == 'development' or os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')
    if debug_mode:
        print("⚠️ RUNNING IN DEVELOPMENT (DEBUG) MODE ⚠️")
        print("   Do not use this for production.")
        print("   Server will auto-reload on code changes.")
    else:
        print("🚀 RUNNING IN PRODUCTION MODE")
    print("="*50)
    print("\n   Press CTRL+C to stop the server.\n")

    app.run(host='0.0.0.0', port=5001, debug=debug_mode)