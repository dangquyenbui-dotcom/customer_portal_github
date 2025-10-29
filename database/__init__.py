# customer_portal/database/__init__.py
"""
Database package initialization
Provides centralized access to database modules and service getters.
"""

from .connection import DatabaseConnection, get_db
from .erp_connection_base import get_erp_db_connection
from .erp_service import get_erp_service, close_erp_connection
from .customer_data import CustomerDataDB, customer_db
from .audit_log import AuditLogDB, audit_db
# === NEW IMPORT ===
from .session_store import SessionStoreDB, session_db
# === NEW IMPORT ===
from .analytics_db import AnalyticsDB, analytics_db

__all__ = [
    # Connection helpers
    'DatabaseConnection',
    'get_db',
    'get_erp_db_connection',
    'close_erp_connection', # Expose function to close ERP connection if needed

    # Service getters
    'get_erp_service',

    # Local DB table managers (instances)
    'CustomerDataDB', # Class
    'customer_db',    # Instance
    'AuditLogDB',
    'audit_db',
    # === NEW EXPORT ===
    'SessionStoreDB',
    'session_db',
    # === NEW EXPORT ===
    'AnalyticsDB',
    'analytics_db',
]