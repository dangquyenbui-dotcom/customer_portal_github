# customer_portal/database/session_store.py
"""
Active Session database operations (Local DB)
Manages the ActiveSessions table for customer logins.
"""

from .connection import get_db
from config import Config
from datetime import datetime, timedelta

class SessionStoreDB:
    """Active Session database operations"""

    def __init__(self):
        self.db = get_db()
        self.ensure_table()

    def ensure_table(self):
        """Ensure the ActiveSessions table exists."""
        if not self.db.check_table_exists('ActiveSessions'):
            print("⏳ Creating ActiveSessions table...")
            create_query = """
                CREATE TABLE ActiveSessions (
                    session_id NVARCHAR(255) PRIMARY KEY NOT NULL,
                    customer_id INT NOT NULL,
                    last_seen DATETIME NOT NULL,
                    ip_address NVARCHAR(100) NULL,
                    user_agent NVARCHAR(500) NULL,
                    created_at DATETIME DEFAULT GETDATE() NOT NULL,
                    CONSTRAINT FK_Session_Customer FOREIGN KEY (customer_id) 
                        REFERENCES Customers(customer_id)
                        ON DELETE CASCADE
                );
                CREATE INDEX IX_ActiveSessions_CustomerID ON ActiveSessions(customer_id);
                CREATE INDEX IX_ActiveSessions_LastSeen ON ActiveSessions(last_seen DESC);
            """
            if self.db.execute_query(create_query):
                print("✅ ActiveSessions table created successfully.")
            else:
                print("❌ Failed to create ActiveSessions table.")

    def create_or_update(self, session_id, customer_id, ip_address, user_agent):
        """Creates or updates a session in the database."""
        now = datetime.utcnow()
        # Use MERGE for an atomic "upsert" (update or insert)
        query = """
            MERGE INTO ActiveSessions AS T
            USING (VALUES (?, ?, ?, ?, ?)) AS S (session_id, customer_id, ip_address, user_agent, last_seen)
            ON (T.session_id = S.session_id)
            WHEN MATCHED THEN
                UPDATE SET T.last_seen = S.last_seen, T.ip_address = S.ip_address, T.user_agent = S.user_agent
            WHEN NOT MATCHED THEN
                INSERT (session_id, customer_id, ip_address, user_agent, last_seen)
                VALUES (S.session_id, S.customer_id, S.ip_address, S.user_agent, S.last_seen);
        """
        params = (session_id, customer_id, ip_address, user_agent, now)
        try:
            return self.db.execute_query(query, params)
        except Exception as e:
            print(f"❌ [SessionDB] Error in create_or_update: {e}")
            return False

    def get(self, session_id):
        """Retrieves a session from the DB if it exists."""
        query = "SELECT * FROM ActiveSessions WHERE session_id = ?"
        results = self.db.execute_query(query, (session_id,))
        return results[0] if results else None

    def delete(self, session_id):
        """Deletes a session from the DB (the 'kick' action)."""
        query = "DELETE FROM ActiveSessions WHERE session_id = ?"
        return self.db.execute_query(query, (session_id,))

    def get_all_active(self):
        """Gets all active sessions, joining with customer info."""
        # We join with Customers to get names and email
        query = """
            SELECT 
                s.session_id, 
                s.customer_id, 
                s.last_seen, 
                s.ip_address, 
                s.user_agent, 
                s.created_at,
                c.first_name,
                c.last_name,
                c.email
            FROM ActiveSessions s
            JOIN Customers c ON s.customer_id = c.customer_id
            ORDER BY s.last_seen DESC
        """
        return self.db.execute_query(query)

    def prune_inactive(self, session_hours):
        """Removes sessions that haven't been seen in session_hours."""
        cutoff = datetime.utcnow() - timedelta(hours=session_hours)
        query = "DELETE FROM ActiveSessions WHERE last_seen < ?"
        try:
            success = self.db.execute_query(query, (cutoff,))
            if success:
                print(f"ℹ️ [SessionDB] Pruned stale sessions older than {cutoff}.")
        except Exception as e:
            print(f"⚠️ [SessionDB] Error pruning sessions: {e}")

# Singleton instance
session_db = SessionStoreDB()