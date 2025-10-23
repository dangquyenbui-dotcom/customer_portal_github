# customer_portal/utils/helpers.py
"""
Helper utility functions
Common functions used across the application
"""

from datetime import datetime
from flask import request

def get_client_info():
    """
    Get client IP address and user agent for logging
    Returns: tuple: (ip_address, user_agent)
    """
    # Try common headers for IP, falling back to remote_addr
    headers_to_check = ['X-Forwarded-For', 'X-Real-IP']
    ip = request.remote_addr # Default
    for header in headers_to_check:
        value = request.headers.get(header)
        if value:
            # Take the first IP if multiple are present (e.g., in X-Forwarded-For)
            ip = value.split(',')[0].strip()
            break
            
    user_agent = request.headers.get('User-Agent', '')[:500]  # Limit to 500 chars
    return ip, user_agent

def format_datetime(dt, format_string='%Y-%m-%d %H:%M:%S'):
    """
    Format datetime object to string
    Args: dt: datetime object or string, format_string: desired output format
    Returns: str: formatted datetime string or empty string if input is None
    """
    if dt is None:
        return ''
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            # Handle potential non-ISO format strings gracefully
            return str(dt) # Return original string if parsing fails
            
    try:
        return dt.strftime(format_string)
    except (TypeError, ValueError):
        return str(dt) # Fallback

def safe_str(value, default=''):
    """
    Safely convert value to string
    Args: value: any value to convert, default: default value if conversion fails
    Returns: str: string representation of value
    """
    if value is None:
        return default
    try:
        return str(value)
    except Exception:
        return default


def safe_int(value, default=0):
    """
    Safely convert value to integer
    Args: value: any value to convert, default: default value if conversion fails
    Returns: int: integer value
    """
    if value is None:
        return default
    try:
        # Handle potential float strings before converting to int
        return int(float(value))
    except (TypeError, ValueError):
        return default