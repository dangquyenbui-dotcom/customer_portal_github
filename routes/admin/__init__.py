# customer_portal/routes/admin/__init__.py
"""
Admin routes package initialization
"""

from .panel import admin_panel_bp
from .customers import admin_customers_bp

__all__ = [
    'admin_panel_bp',
    'admin_customers_bp',
]