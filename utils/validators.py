# customer_portal/utils/validators.py
"""
Input validation functions
"""

import re

def validate_email(email):
    """
    Validate email address
    Args: email: email address to validate
    Returns: tuple: (is_valid, error_message)
    """
    if not email:
        return False, "Email is required"

    email = email.strip().lower()

    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    if not re.match(pattern, email):
        return False, "Invalid email format"

    if len(email) > 255:
        return False, "Email address is too long"

    return True, None

def validate_password(password):
    """
    Validate password complexity
    Args: password: password to validate
    Returns: tuple: (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"

    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if len(password) > 100:
        return False, "Password must be less than 100 characters"

    # Add more complexity rules if desired (e.g., require numbers, symbols, uppercase)
    # Example: Check for at least one number
    # if not re.search(r"\d", password):
    #     return False, "Password must contain at least one number"
    # Example: Check for at least one uppercase letter
    # if not re.search(r"[A-Z]", password):
    #     return False, "Password must contain at least one uppercase letter"

    return True, None