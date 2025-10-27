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
    
    # === NEW: Add TEST_MODE for AD auth debugging ===
    TEST_MODE = os.getenv('TEST_MODE', 'False').lower() == 'true'
    # === END NEW ===

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

    # Email settings are now required
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
    SMTP_USE_TLS = os.getenv('SMTP_USE_TLS', 'True').lower() == 'true'
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    EMAIL_FROM = os.getenv('EMAIL_FROM')
    EMAIL_BCC = os.getenv('EMAIL_BCC')

    # --- Local Admin User ---
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'cp_admin')
    ADMIN_PASSWORD_HASH = os.getenv('ADMIN_PASSWORD_HASH')

    # === Active Directory Admin Settings ===
    AD_SERVER = os.getenv('AD_SERVER')
    AD_DOMAIN = os.getenv('AD_DOMAIN')
    AD_PORT = int(os.getenv('AD_PORT', '389'))
    AD_SERVICE_ACCOUNT = os.getenv('AD_SERVICE_ACCOUNT')
    AD_SERVICE_PASSWORD = os.getenv('AD_SERVICE_PASSWORD')
    AD_BASE_DN = os.getenv('AD_BASE_DN')
    AD_PORTAL_ADMIN_GROUP = os.getenv('AD_PORTAL_ADMIN_GROUP')


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

        # Validate Email Settings
        if not cls.SMTP_SERVER: errors.append("SMTP_SERVER is required for password resets")
        if not cls.SMTP_USERNAME: errors.append("SMTP_USERNAME is required for password resets")
        if not cls.SMTP_PASSWORD: errors.append("SMTP_PASSWORD is required for password resets")
        if not cls.EMAIL_FROM: errors.append("EMAIL_FROM is required for password resets")
        if cls.EMAIL_BCC and '@' not in cls.EMAIL_BCC:
             errors.append("EMAIL_BCC, if provided, must be a valid email address.")

        # Validate AD Settings
        ad_settings = [cls.AD_SERVER, cls.AD_DOMAIN, cls.AD_SERVICE_ACCOUNT, cls.AD_SERVICE_PASSWORD, cls.AD_BASE_DN, cls.AD_PORTAL_ADMIN_GROUP]
        if any(ad_settings):
            if not cls.AD_SERVER: errors.append("AD_SERVER is required for AD auth.")
            if not cls.AD_DOMAIN: errors.append("AD_DOMAIN is required for AD auth.")
            if not cls.AD_SERVICE_ACCOUNT: errors.append("AD_SERVICE_ACCOUNT is required for AD auth.")
            if not cls.AD_SERVICE_PASSWORD: errors.append("AD_SERVICE_PASSWORD is required for AD auth.")
            if not cls.AD_BASE_DN: errors.append("AD_BASE_DN is required for AD auth.")
            if not cls.AD_PORTAL_ADMIN_GROUP: errors.append("AD_PORTAL_ADMIN_GROUP is required for AD auth.")
        else:
            print("ℹ️  AD_SERVER not found in .env, skipping Active Directory admin auth.")

        if errors:
            print("❌ Configuration errors:")
            for error in errors: print(f"  - {error}")
            return False
        
        if cls.TEST_MODE:
            print("⚠️  [CONFIG] TEST_MODE is enabled. AD auth will be skipped.")
            
        print("✅ Configuration loaded successfully.")
        return True

# Ensure validation is called on import
Config.validate()