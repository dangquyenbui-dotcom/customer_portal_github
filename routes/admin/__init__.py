# customer_portal/routes/admin/__init__.py
"""
Admin routes package initialization
"""

from .panel import admin_panel_bp
from .customers import admin_customers_bp
from .audit import admin_audit_bp
# === NEW IMPORT ===
from .sessions import admin_sessions_bp

__all__ = [
    'admin_panel_bp',
    'admin_customers_bp',
    'admin_audit_bp',
    # === NEW EXPORT ===
    'admin_sessions_bp',
]