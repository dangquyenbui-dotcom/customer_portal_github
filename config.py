# customer_portal/config.py
"""
Configuration settings for Customer Portal
Reads sensitive information from environment variables
"""

import os
from dotenv import load_dotenv
from datetime import timedelta

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""

    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    SESSION_HOURS = int(os.getenv('SESSION_HOURS', '8'))
    PERMANENT_SESSION_LIFETIME = timedelta(hours=SESSION_HOURS)

    # --- Customer Portal Database (Local SQL Server) ---
    DB_SERVER = os.getenv('DB_SERVER')
    DB_NAME = os.getenv('DB_NAME', 'CustomerPortalDB')
    DB_USE_WINDOWS_AUTH = os.getenv('DB_USE_WINDOWS_AUTH', 'False').lower() == 'true'
    DB_USERNAME = os.getenv('DB_USERNAME')
    DB_PASSWORD = os.getenv('DB_PASSWORD')

    # --- ERP Database (Deacom - Read Only) ---
    ERP_DB_SERVER = os.getenv('ERP_DB_SERVER')
    ERP_DB_NAME = os.getenv('ERP_DB_NAME')
    ERP_DB_USERNAME = os.getenv('ERP_DB_USERNAME')
    ERP_DB_PASSWORD = os.getenv('ERP_DB_PASSWORD')
    ERP_DB_PORT = os.getenv('ERP_DB_PORT', '1433')
    ERP_DB_DRIVER = os.getenv('ERP_DB_DRIVER', 'ODBC Driver 17 for SQL Server')
    ERP_DB_TIMEOUT = int(os.getenv('ERP_DB_TIMEOUT', '30'))

    # Email settings (Optional - For Password Reset)
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'True').lower() == 'true'
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    EMAIL_FROM = os.getenv('EMAIL_FROM')

    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'cp_admin') # Simple admin user for now
    ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH') # Store hash in .env


    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'dev-key-change-in-production':
             errors.append("SECRET_KEY is required and should be changed for production.")
        if not cls.DB_SERVER: errors.append("DB_SERVER is required")
        if not cls.DB_NAME: errors.append("DB_NAME is required")
        if not cls.DB_USE_WINDOWS_AUTH and (not cls.DB_USERNAME or not cls.DB_PASSWORD):
            errors.append("DB_USERNAME and DB_PASSWORD are required when not using Windows Auth")
        if not cls.ERP_DB_SERVER: errors.append("ERP_DB_SERVER is required")
        if not cls.ERP_DB_NAME: errors.append("ERP_DB_NAME is required")
        if not cls.ERP_DB_USERNAME: errors.append("ERP_DB_USERNAME is required")
        if not cls.ERP_DB_PASSWORD: errors.append("ERP_DB_PASSWORD is required")
        if not cls.ADMIN_PASSWORD_HASH: errors.append("ADMIN_PASSWORD_HASH is required in .env for admin login")

        if errors:
            print("❌ Configuration errors:")
            for error in errors: print(f"  - {error}")
            return False
        print("✅ Configuration loaded successfully.")
        return True

# Ensure validation is called on import
Config.validate()