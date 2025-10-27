# customer_portal/auth/ad_auth.py
"""
Active Directory (LDAP3) Authentication Module
Handles AD admin authentication and authorization
"""

from ldap3 import Server, Connection, ALL, SIMPLE, SUBTREE
import ldap3.core.exceptions
from config import Config

def get_ad_user_info(username):
    """Get AD groups for a user using the service account"""
    try:
        server = Server(Config.AD_SERVER, port=Config.AD_PORT, get_info=ALL)
        service_user = f'{Config.AD_SERVICE_ACCOUNT}@{Config.AD_DOMAIN}'

        service_conn = Connection(
            server,
            user=service_user,
            password=Config.AD_SERVICE_PASSWORD,
            authentication=SIMPLE,
            auto_bind=True
        )

        search_filter = f'(&(objectClass=user)(sAMAccountName={username}))'
        service_conn.search(
            Config.AD_BASE_DN,
            search_filter,
            SUBTREE,
            attributes=['memberOf', 'displayName', 'mail']
        )

        if service_conn.entries:
            user_entry = service_conn.entries[0]

            groups = []
            if hasattr(user_entry, 'memberOf') and user_entry.memberOf:
                for group_dn in user_entry.memberOf:
                    group_name = str(group_dn).split(',')[0].replace('CN=', '')
                    groups.append(group_name)

            display_name = str(user_entry.displayName) if hasattr(user_entry, 'displayName') else username
            email = str(user_entry.mail) if hasattr(user_entry, 'mail') else f'{username}@{Config.AD_DOMAIN}'

            service_conn.unbind()

            return {
                'groups': groups,
                'display_name': display_name,
                'email': email
            }

        service_conn.unbind()
        return None

    except Exception as e:
        print(f"❌ [AD Auth] Error getting user groups: {str(e)}")
        return None

def check_ad_admin_auth(username, password):
    """
    Authenticate user against Active Directory.
    Returns an admin session dict if successful and in the admin group.
    """

    # --- Test Mode for Development ---
    if Config.TEST_MODE:
        print("⚠️  [AD Auth] TEST_MODE is enabled. Simulating AD admin login.")
        if password == "password": # Use a simple password for test mode
            return {
                'username': username,
                'display_name': 'AD Admin (Test)',
                'email': f'{username}@{Config.AD_DOMAIN}',
                'is_admin': True,
                'auth_method': 'ad_test'
            }
        else:
            return None

    # --- Real AD Authentication ---
    try:
        server = Server(Config.AD_SERVER, port=Config.AD_PORT, get_info=ALL)
        user_principal = f'{username}@{Config.AD_DOMAIN}'

        try:
            # --- 1. Attempt user authentication (bind) ---
            user_conn = Connection(
                server,
                user=user_principal,
                password=password,
                authentication=SIMPLE,
                auto_bind=True
            )
            user_conn.unbind()
            print(f"✅ [AD Auth] User bind successful: {username}")

            # --- 2. Get user info and check group membership ---
            user_info = get_ad_user_info(username)

            if user_info:
                # Check if user is in the required admin group
                is_portal_admin = Config.AD_PORTAL_ADMIN_GROUP in user_info['groups']

                if is_portal_admin:
                    print(f"✅ [AD Auth] User {username} found in admin group '{Config.AD_PORTAL_ADMIN_GROUP}'.")
                    return {
                        'username': username,
                        'display_name': user_info['display_name'],
                        'email': user_info['email'],
                        'is_admin': True, # This is the key permission
                        'auth_method': 'ad'
                    }
                else:
                    print(f"⚠️  [AD Auth] User {username} authenticated but is not in the required admin group.")
                    return None

        except ldap3.core.exceptions.LDAPBindError:
            print(f"ℹ️  [AD Auth] Invalid AD credentials for user: {username}")
            return None # Failed AD auth, and wasn't local admin
        
        except Exception as e:
            print(f"❌ [AD Auth] AD Authentication error: {str(e)}")
            return None

    except Exception as e:
        print(f"❌ [AD Auth] AD Server connection error: {str(e)}")
        return None

    return None