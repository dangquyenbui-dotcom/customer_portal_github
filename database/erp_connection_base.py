# database/erp_connection_base.py
"""
Dedicated ERP Database Connection Base.
Handles the raw pyodbc connection logic.
"""
import pyodbc
import traceback
from config import Config
from flask import g # === NEW IMPORT ===

class ERPConnection:
    """Handles the raw connection to the ERP database."""
    def __init__(self):
        self.connection = None
        # === MODIFICATION: Build connection string on init ===
        self._connection_string = self._build_connection_string()
        if not self._connection_string:
            raise ConnectionError("Failed to build connection string for ERP DB.")
        # === MODIFICATION: Connect on init ===
        self._connect()


    def _build_connection_string(self):
        """Builds the ERP connection string."""
        # Prioritized list of potential drivers to try (braces removed)
        drivers_to_try = [
            Config.ERP_DB_DRIVER,  # First, try the one from .env
            'ODBC Driver 18 for SQL Server',
            'ODBC Driver 17 for SQL Server',
            'SQL Server Native Client 11.0',
            'SQL Server'
        ]

        # Remove duplicates while preserving order
        drivers = list(dict.fromkeys(d for d in drivers_to_try if d)) # Ensure no None or empty strings

        for driver in drivers:
            try:
                # The f-string correctly adds the necessary braces around the driver name
                connection_string = (
                    f"DRIVER={{{driver}}};"
                    f"SERVER={Config.ERP_DB_SERVER},{Config.ERP_DB_PORT};"
                    f"DATABASE={Config.ERP_DB_NAME};"
                    f"UID={Config.ERP_DB_USERNAME};"
                    f"PWD={Config.ERP_DB_PASSWORD};"
                    f"TrustServerCertificate=yes;"
                    f"Connection Timeout={Config.ERP_DB_TIMEOUT};"
                )
                # === MODIFICATION: Test connection string ===
                test_conn = pyodbc.connect(connection_string, autocommit=True, timeout=5)
                test_conn.close()
                # === END MODIFICATION ===
                
                print(f"✅ [ERP_DB] Connection successful using driver: {driver}")
                return connection_string  # Save the working string
                
            except pyodbc.Error as e:
                # Only print error if it's not a driver-related issue that we expect to retry
                if 'driver' not in str(e).lower():
                    print(f"❌ [ERP_DB] Connection Error: {e}")
                print(f"ℹ️  [ERP_DB] Driver '{driver}' failed. Trying next...")
                continue # Try the next driver in the list

        print(f"❌ [ERP_DB] FATAL: Connection failed. All attempted drivers were unsuccessful.")
        return None
        

    def _connect(self):
        """Internal connect method."""
        try:
            self.connection = pyodbc.connect(self._connection_string, autocommit=True)
            return True
        except pyodbc.Error as e:
            print(f"❌ [ERP_DB] Connection Error: {e}")
            self.connection = None
            return False
            
    def test_connection(self):
        """Test database connection"""
        if not self._connection_string:
            return False
        try:
            test_conn = pyodbc.connect(self._connection_string, autocommit=True, timeout=5)
            test_conn.close()
            return True
        except Exception as e:
            print(f"❌ [ERP_DB] Test connection failed: {e}")
            return False

    def execute_query(self, sql, params=None):
        """Executes a SQL query and returns results as a list of dicts."""
        # === MODIFICATION: Check connection and reconnect if closed ===
        if self.connection is None or getattr(self.connection, 'closed', True):
            print("ℹ️ [ERP_DB] Connection is closed. Reconnecting...")
            if not self._connect():
                print("❌ [ERP_DB] Cannot execute query, reconnection failed.")
                return []
        # === END MODIFICATION ===

        try:
            cursor = self.connection.cursor()
            cursor.execute(sql, params or [])
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                cursor.close()
                return results
            cursor.close()
            # Handle cases like INSERT/UPDATE/DELETE where description might be None
            # If autocommit=True, changes are already committed.
            return [] # Return empty list for non-SELECT or empty results
        except pyodbc.Error as e:
            print(f"❌ [ERP_DB] Query Failed: {e}")
            print(f"   SQL: {sql}")
            print(f"   Params: {params}")
            traceback.print_exc()
            # === MODIFICATION: Close connection on error to force reconnect next time ===
            self.close() 
            return []
        except Exception as e:
            print(f"❌ [ERP_DB] Unexpected error during query execution: {e}")
            traceback.print_exc()
            self.close()
            return []

    def close(self):
        """Closes the database connection."""
        if self.connection:
            try:
                self.connection.close()
                self.connection = None
                print("ℹ️ [ERP_DB] Connection closed.")
            except pyodbc.Error as e:
                print(f"⚠️ [ERP_DB] Error closing connection: {e}")


# === MODIFICATION: Remove global instance ===
# _erp_connection_instance = None

def get_erp_db_connection():
    """
    Gets a shared instance of the ERP connection.
    Creates a new one if it doesn't exist or seems closed.
    """
    # === MODIFICATION: Use Flask's 'g' context ===
    if 'erp_db' not in g:
        g.erp_db = ERPConnection()
    return g.erp_db
    # === END MODIFICATION ===

# === NEW FUNCTION ===
def close_erp_db(e=None):
    """Closes the ERP database connection in the current context."""
    db = g.pop('erp_db', None)
    if db is not None:
        db.close()
# === END NEW FUNCTION ===