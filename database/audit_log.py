# customer_portal/database/audit_log.py
"""
Audit Log database operations (Local DB)
Manages the AuditLog table.
"""

from .connection import get_db
from flask import session # To get admin username
import json

class AuditLogDB:
    """Audit Log database operations"""

    def __init__(self):
        self.db = get_db()
        self.ensure_table()

    def ensure_table(self):
        """Ensure the AuditLog table exists."""
        if not self.db.check_table_exists('AuditLog'):
            print("⏳ Creating AuditLog table...")
            create_query = """
                CREATE TABLE AuditLog (
                    log_id INT IDENTITY(1,1) PRIMARY KEY,
                    timestamp DATETIME DEFAULT GETDATE() NOT NULL,
                    admin_username NVARCHAR(100) NOT NULL,
                    action_type NVARCHAR(50) NOT NULL, -- e.g., CREATE, UPDATE, DEACTIVATE, REACTIVATE, ADMIN_PW_RESET
                    target_customer_id INT NULL, -- FK would require handling customer deletion
                    target_customer_email NVARCHAR(255) NULL, -- Log email for easier lookup
                    details NVARCHAR(MAX) NULL -- Can store JSON string or descriptive text
                );
                CREATE INDEX IX_AuditLog_Timestamp ON AuditLog(timestamp DESC);
                CREATE INDEX IX_AuditLog_Admin ON AuditLog(admin_username);
                CREATE INDEX IX_AuditLog_Action ON AuditLog(action_type);
                CREATE INDEX IX_AuditLog_TargetCustomer ON AuditLog(target_customer_id);
            """
            if self.db.execute_query(create_query):
                print("✅ AuditLog table created successfully.")
            else:
                print("❌ Failed to create AuditLog table.")

    def log_event(self, action_type, target_customer_id=None, target_customer_email=None, details=None):
        """Logs an audit event."""
        admin_username = session.get('admin', {}).get('username', 'SYSTEM') # Get admin from session

        # Ensure details are stored appropriately (simple string or JSON string)
        if isinstance(details, (dict, list)):
            details_str = json.dumps(details)
        else:
            details_str = str(details) if details is not None else None

        query = """
            INSERT INTO AuditLog (admin_username, action_type, target_customer_id, target_customer_email, details)
            VALUES (?, ?, ?, ?, ?)
        """
        params = (
            admin_username,
            action_type,
            target_customer_id,
            target_customer_email,
            details_str
        )
        try:
            success = self.db.execute_query(query, params)
            if not success:
                print(f"⚠️ [Audit Log] Failed to log event: {action_type} by {admin_username}")
        except Exception as e:
            # Prevent audit errors from breaking main functionality
            print(f"❌ [Audit Log] CRITICAL ERROR logging event: {e}")

    def get_logs(self, limit=100, offset=0, admin_filter=None, action_filter=None, customer_filter=None):
        """Retrieves audit logs with optional filtering."""
        query = "SELECT log_id, timestamp, admin_username, action_type, target_customer_id, target_customer_email, details FROM AuditLog"
        filters = []
        params = []

        if admin_filter:
            filters.append("admin_username = ?")
            params.append(admin_filter)
        if action_filter:
            filters.append("action_type = ?")
            params.append(action_filter)
        if customer_filter: # Can filter by ID or email
             filters.append("(target_customer_id = ? OR target_customer_email LIKE ?)")
             try:
                 # Try converting to int for ID search
                 customer_id = int(customer_filter)
                 params.append(customer_id)
             except ValueError:
                 # If not an int, assume it's not a valid ID for direct match
                 params.append(None) # Parameter for target_customer_id
             
             # Parameter for email search (use wildcard)
             params.append(f"%{customer_filter}%")


        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " ORDER BY timestamp DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
        params.extend([offset, limit])

        logs = self.db.execute_query(query, params)
        
        # Get distinct admins and actions for filter dropdowns
        distinct_admins = [row['admin_username'] for row in self.db.execute_query("SELECT DISTINCT admin_username FROM AuditLog ORDER BY admin_username")]
        distinct_actions = [row['action_type'] for row in self.db.execute_query("SELECT DISTINCT action_type FROM AuditLog ORDER BY action_type")]

        return logs or [], distinct_admins, distinct_actions


# Singleton instance
audit_db = AuditLogDB()
