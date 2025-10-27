# customer_portal/auth/__init__.py
"""
Authentication package initialization
"""

from .customer_auth import (
    authenticate_customer,
    authenticate_admin,
    login_required,
    admin_required
)
# === NEW IMPORT ===
from . import ad_auth

__all__ = [
    'authenticate_customer',
    'authenticate_admin',
    'login_required',
    'admin_required',
    # === NEW EXPORT ===
    'ad_auth',
]