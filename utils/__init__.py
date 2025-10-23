# customer_portal/utils/__init__.py
"""
Utility functions package
Common helper functions and validators
"""

from .helpers import (
    get_client_info,
    format_datetime,
    safe_str,
    safe_int
)

from .validators import (
    validate_email,
    validate_password # Add password validator
)

__all__ = [
    'get_client_info',
    'format_datetime',
    'safe_str',
    'safe_int',
    'validate_email',
    'validate_password'
]