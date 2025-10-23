# customer_portal/routes/__init__.py
"""
Routes package initialization
"""

from .main import main_bp
from .inventory import inventory_bp
# Import admin blueprints
from .admin.panel import admin_panel_bp
from .admin.customers import admin_customers_bp

__all__ = [
    'main_bp',
    'inventory_bp',
    'admin_panel_bp',      # Add admin panel
    'admin_customers_bp',  # Add customer management
]