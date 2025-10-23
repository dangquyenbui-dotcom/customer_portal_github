# customer_portal/app.py
"""
Customer Portal - Main Flask Application
"""

from flask import Flask, session, g
import os
from datetime import timedelta
from config import Config
import socket
import traceback

def create_app():
    app = Flask(__name__)

    # --- Configuration ---
    app.secret_key = Config.SECRET_KEY
    app.permanent_session_lifetime = Config.PERMANENT_SESSION_LIFETIME
    app.config['SESSION_COOKIE_SECURE'] = False # Set to True if using HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' # Or 'Strict'

    # Configure static files path
    app.static_folder = 'static'
    app.static_url_path = '/static'

    # --- Jinja Globals ---
    # Make config and session available globally in templates
    @app.context_processor
    def inject_global_vars():
        return dict(
            config=Config,
            session=session
        )

    # --- Register Blueprints ---
    register_blueprints(app)

    # --- Initialize Database Connections (Test on startup) ---
    initialize_database_connections()

    # --- Request Teardown ---
    @app.teardown_appcontext
    def teardown_db(exception=None):
        # Optional: Close ERP connection if needed (depends on pooling/driver behavior)
        # from database import close_erp_connection
        # close_erp_connection()
        pass # Local DB managed by context manager/singleton

    print("✅ Customer Portal application created.")
    return app

def register_blueprints(app):
    """Register all application blueprints"""
    print("⏳ Registering blueprints...")
    try:
        from routes.main import main_bp
        from routes.inventory import inventory_bp
        # --- Import Admin Blueprints ---
        from routes.admin.panel import admin_panel_bp
        from routes.admin.customers import admin_customers_bp

        app.register_blueprint(main_bp)
        # Register inventory under '/inventory' prefix
        app.register_blueprint(inventory_bp, url_prefix='/inventory')

        # Register admin blueprints under /admin prefix
        app.register_blueprint(admin_panel_bp, url_prefix='/admin')
        app.register_blueprint(admin_customers_bp, url_prefix='/admin')

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
        from database import get_db # Use the __init__ file import
        local_db = get_db()
        if local_db.test_connection():
            print("✅ Local DB (CustomerPortalDB): Connected")
            # Ensure tables are created/checked after connection is confirmed
            # Importing customer_db triggers ensure_tables via its __init__
            from database import customer_db
            print("✅ Local DB Tables Checked/Created.")
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
        # ERP connection might establish lazily, check instance exists
        if erp_db and erp_db.connection:
            print("✅ ERP DB (Read-Only): Connected")
        elif erp_db and erp_db._connection_string:
             print("✅ ERP DB (Read-Only): Connection String Ready (will connect on first query)")
        else:
             print("❌ ERP DB (Read-Only): Connection FAILED during setup")
             all_ok = False # Treat as failure if setup failed
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
        # doesn't even have to be reachable
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

    # Ensure static directories exist (optional, good practice)
    project_root = os.path.dirname(__file__)
    os.makedirs(os.path.join(project_root, 'static', 'css'), exist_ok=True)
    os.makedirs(os.path.join(project_root, 'static', 'js'), exist_ok=True)
    os.makedirs(os.path.join(project_root, 'static', 'img'), exist_ok=True)
    os.makedirs(os.path.join(project_root, 'templates', 'admin'), exist_ok=True)
    os.makedirs(os.path.join(project_root, 'templates', 'components'), exist_ok=True)

    local_ip = get_local_ip()

    # Validate config one more time before running
    if not Config.validate():
        print("\n❌ Aborting due to configuration errors.")
        exit(1)

    print("\n--- Configuration ---")
    print(f"Database:     {Config.DB_SERVER}/{Config.DB_NAME}")
    print(f"ERP Database: {Config.ERP_DB_SERVER}/{Config.ERP_DB_NAME}")
    print(f"Secret Key:   {'Set' if Config.SECRET_KEY != 'dev-key-change-in-production' else '!!! NOT SET (Using Default) !!!'}")
    print(f"Admin User:   {Config.ADMIN_USERNAME}")
    print("-" * 20)

    app = create_app() # Create the Flask app instance

    print("\n" + "="*50)
    print("✅ SERVER READY - ACCESS URLS:")
    # Use port 5001 to avoid conflict with Production Portal if run on same machine
    print(f"   Local:   http://localhost:5001")
    print(f"   Network: http://{local_ip}:5001")
    print("="*50)
    print("\nℹ️  Ensure firewall allows port 5001.")
    print("   Press CTRL+C to stop the server.\n")

    # Use Waitress for serving
    try:
        from waitress import serve
        serve(app, host='0.0.0.0', port=5001)
    except ImportError:
         print("\n⚠️ Waitress not found. Falling back to Flask's development server.")
         print("   Install waitress (`pip install waitress`) for a more suitable server.")
         app.run(host='0.0.0.0', port=5001, debug=False) # debug=False is safer
    except Exception as e:
         print(f"❌ Failed to start server: {e}")