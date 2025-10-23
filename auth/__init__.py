# customer_portal/auth/__init__.py
"""
Authentication package initialization
"""

from .customer_auth import (
    authenticate_customer,
    authenticate_admin,
    login_required,
    admin_required
    # Add password reset functions later if implementing email
)

__all__ = [
    'authenticate_customer',
    'authenticate_admin',
    'login_required',
    'admin_required'
]