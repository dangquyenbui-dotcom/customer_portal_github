# customer_portal/routes/__init__.py
"""
Routes package initialization
"""

from .main import main_bp
from .inventory import inventory_bp
# Import admin blueprints
from .admin.panel import admin_panel_bp
from .admin.customers import admin_customers_bp
# === MODIFIED: Add all admin blueprints ===
from .admin.audit import admin_audit_bp
from .admin.sessions import admin_sessions_bp
from .admin.analytics import admin_analytics_bp
# === END MODIFICATION ===


__all__ = [
    'main_bp',
    'inventory_bp',
    'admin_panel_bp',      # Add admin panel
    'admin_customers_bp',  # Add customer management
    # === MODIFIED: Add all admin blueprints ===
    'admin_audit_bp',
    'admin_sessions_bp',
    'admin_analytics_bp',
    # === END MODIFICATION ===
]