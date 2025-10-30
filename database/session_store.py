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
        # === MODIFICATION: Do not store db instance ===
        # self.db = get_db() 
        # === MODIFICATION: REMOVE ensure_tables() call ===
        # self.ensure_table()
        pass # Init does nothing now

    def ensure_table(self):
        """Ensure the ActiveSessions table exists."""
        db = get_db() # === ADDED ===
        if not db.check_table_exists('ActiveSessions'): # === MODIFIED ===
            print("⏳ Creating ActiveSessions table...")
            create_query = """
                CREATE TABLE ActiveSessions (
                    session_id NVARCHAR(255) PRIMARY KEY NOT NULL,
                    customer_id INT NOT NULL,
                    last_seen DATETIME NOT NULL,
                    ip_address NVARCHAR(100) NULL,
                    user_agent NVARCHAR(500) NULL,
                    
                    -- === MODIFICATION: Use GETUTCDATE() for consistency ===
                    created_at DATETIME DEFAULT GETUTCDATE() NOT NULL,
                    -- === END MODIFICATION ===
                    
                    CONSTRAINT FK_Session_Customer FOREIGN KEY (customer_id) 
                        REFERENCES Customers(customer_id)
                        ON DELETE CASCADE
                );
                CREATE INDEX IX_ActiveSessions_CustomerID ON ActiveSessions(customer_id);
                CREATE INDEX IX_ActiveSessions_LastSeen ON ActiveSessions(last_seen DESC);
            """
            if db.execute_query(create_query): # === MODIFIED ===
                print("✅ ActiveSessions table created successfully.")
            else:
                print("❌ Failed to create ActiveSessions table.")

    def create_or_update(self, session_id, customer_id, ip_address, user_agent):
        """Creates or updates a session in the database."""
        db = get_db()
        # This one variable will be used for BOTH last_seen and created_at
        now_utc = datetime.utcnow() 
        
        # === MODIFICATION: Explicitly set created_at on INSERT ===
        # Use MERGE for an atomic "upsert" (update or insert)
        query = """
            MERGE INTO ActiveSessions AS T
            USING (VALUES (?, ?, ?, ?, ?)) AS S (session_id, customer_id, ip_address, user_agent, now_utc)
            ON (T.session_id = S.session_id)
            
            -- When session exists, just update last_seen and info
            WHEN MATCHED THEN
                UPDATE SET 
                    T.last_seen = S.now_utc, 
                    T.ip_address = S.ip_address, 
                    T.user_agent = S.user_agent
            
            -- When session is new, explicitly insert ALL columns, including created_at
            WHEN NOT MATCHED THEN
                INSERT (session_id, customer_id, ip_address, user_agent, last_seen, created_at)
                VALUES (S.session_id, S.customer_id, S.ip_address, S.user_agent, S.now_utc, S.now_utc);
        """
        # The params tuple now correctly matches the 5 values in the USING clause
        params = (session_id, customer_id, ip_address, user_agent, now_utc)
        # === END MODIFICATION ===
        try:
            return db.execute_query(query, params)
        except Exception as e:
            print(f"❌ [SessionDB] Error in create_or_update: {e}")
            return False

    def get(self, session_id):
        """Retrieves a session from the DB if it exists."""
        db = get_db() # === ADDED ===
        query = "SELECT * FROM ActiveSessions WHERE session_id = ?"
        results = db.execute_query(query, (session_id,)) # === MODIFIED ===
        return results[0] if results else None

    def delete(self, session_id):
        """Deletes a session from the DB (the 'kick' action)."""
        db = get_db() # === ADDED ===
        query = "DELETE FROM ActiveSessions WHERE session_id = ?"
        return db.execute_query(query, (session_id,)) # === MODIFIED ===

    def get_all_active(self):
        """Gets all active sessions, joining with customer info."""
        db = get_db() # === ADDED ===
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
        return db.execute_query(query) # === MODIFIED ===

    # === NEW METHOD ===
    def prune_by_hours(self, hours):
        """
        Removes sessions older than N hours and returns a list
        of customers who were kicked.
        """
        db = get_db()
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        # Step 1: Find sessions to be pruned and get their info for logging
        # We need to join with Customers to get email
        find_query = """
            SELECT 
                s.session_id, 
                s.customer_id, 
                c.email AS target_customer_email
            FROM ActiveSessions s
            LEFT JOIN Customers c ON s.customer_id = c.customer_id
            WHERE s.last_seen < ?
        """
        sessions_to_prune = db.execute_query(find_query, (cutoff,))
        
        if not sessions_to_prune:
            return [] # Nothing to do
        
        # Step 2: Delete them
        session_ids = [s['session_id'] for s in sessions_to_prune]
        # Create placeholders for the IN clause
        placeholders = ','.join('?' for _ in session_ids)
        delete_query = f"DELETE FROM ActiveSessions WHERE session_id IN ({placeholders})"
        
        try:
            success = db.execute_query(delete_query, session_ids)
            if success:
                print(f"ℹ️ [SessionDB] Pruned {len(sessions_to_prune)} sessions older than {hours} hours.")
                return sessions_to_prune # Return list of kicked users
            else:
                print("⚠️ [SessionDB] Prune delete query failed.")
                return []
        except Exception as e:
            print(f"⚠️ [SessionDB] Error pruning sessions by hour: {e}")
            return []
            
    # === MODIFIED: Update prune_inactive to use the new method ===
    def prune_inactive(self, session_hours):
        """Removes sessions that haven't been seen in session_hours."""
        # This function is called randomly, so we don't need the return value
        self.prune_by_hours(session_hours)

# Singleton instance
session_db = SessionStoreDB()