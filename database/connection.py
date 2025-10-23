# customer_portal/database/connection.py
"""
Database connection management for CustomerPortalDB
Handles connection pooling and basic operations for the LOCAL database.
"""

import pyodbc
from config import Config
from contextlib import contextmanager
import traceback

class DatabaseConnection:
    """Local Database (CustomerPortalDB) connection handler"""

    def __init__(self):
        self.connection = None
        self._connection_string = self._build_connection_string()
        # Attempt initial connection
        self.connect()

    def _build_connection_string(self):
        """Build the local database connection string"""
        # Prioritized list of potential drivers to try (braces removed)
        drivers_to_try = [
            'ODBC Driver 17 for SQL Server', # Often preferred
            'ODBC Driver 18 for SQL Server',
            'SQL Server Native Client 11.0',
            'SQL Server'
        ]
        drivers = list(dict.fromkeys(d for d in drivers_to_try if d)) # Ensure no None or empty strings

        if Config.DB_USE_WINDOWS_AUTH:
            base_string = (
                f"SERVER={Config.DB_SERVER};"
                f"DATABASE={Config.DB_NAME};"
                f"Trusted_Connection=yes;"
                f"TrustServerCertificate=yes;" # Often needed for modern SQL Server
                f"Connection Timeout=30;"
            )
        else:
            base_string = (
                f"SERVER={Config.DB_SERVER};"
                f"DATABASE={Config.DB_NAME};"
                f"UID={Config.DB_USERNAME};"
                f"PWD={Config.DB_PASSWORD};"
                f"TrustServerCertificate=yes;"
                f"Connection Timeout=30;"
            )

        # Try drivers to find a working connection string
        for driver in drivers:
            try:
                conn_str = f"DRIVER={{{driver}}};{base_string}"
                # Test connection immediately
                test_conn = pyodbc.connect(conn_str, timeout=5)
                test_conn.close()
                print(f"✅ [Local DB] Connection test successful with driver: {driver}")
                return conn_str # Return the first working one
            except pyodbc.Error as e:
                print(f"ℹ️  [Local DB] Driver '{driver}' failed: {e}. Trying next...")
                continue
            except Exception as e:
                print(f"ℹ️  [Local DB] Unexpected error testing driver '{driver}': {e}. Trying next...")
                continue

        print(f"❌ [Local DB] FATAL: Could not establish connection string. All attempted drivers failed.")
        return None # Indicate failure

    def connect(self):
        """Establish database connection"""
        if not self._connection_string:
            print("❌ [Local DB] Cannot connect: No valid connection string found.")
            return False
        try:
            # Check if connection exists and is alive
            if self.connection:
                try:
                    self.connection.cursor().execute("SELECT 1")
                    # print("ℹ️ [Local DB] Reusing existing connection.")
                    return True
                except (pyodbc.Error, AttributeError):
                    print("⚠️ [Local DB] Connection lost. Reconnecting...")
                    self.disconnect() # Clean up old connection

            # print("ℹ️ [Local DB] Establishing new connection...")
            self.connection = pyodbc.connect(self._connection_string)
            self.connection.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
            self.connection.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
            self.connection.setencoding(encoding='utf-8')
            # print("✅ [Local DB] New connection established.")
            return True
        except pyodbc.Error as e:
            print(f"❌ [Local DB] Connection failed: {str(e)}")
            self.connection = None
            return False
        except Exception as e:
            print(f"❌ [Local DB] Unexpected connection error: {str(e)}")
            self.connection = None
            return False

    def disconnect(self):
        """Close database connection"""
        if self.connection:
            try:
                self.connection.close()
                self.connection = None
                # print("ℹ️ [Local DB] Connection closed.")
            except pyodbc.Error as e:
                print(f"⚠️ [Local DB] Error disconnecting: {str(e)}")
        self.connection = None

    def test_connection(self):
        """Test database connection"""
        return self.connect() # connect() already includes a test

    @contextmanager
    def get_cursor(self):
        """Provides a cursor within a context manager, ensuring connection."""
        if not self.connect():
            raise ConnectionError("Failed to establish database connection")
        cursor = None
        try:
            cursor = self.connection.cursor()
            yield cursor
        except pyodbc.Error as e:
            print(f"❌ [Local DB] Database Error: {e}")
            traceback.print_exc()
            if self.connection:
                try: self.connection.rollback()
                except pyodbc.Error: pass # Ignore rollback errors if connection is broken
            raise # Re-raise the exception
        finally:
            if cursor:
                try: cursor.close()
                except pyodbc.Error: pass # Ignore if cursor is already closed or invalid

    def execute_query(self, query, params=None):
        """
        Execute a query and return results.
        For SELECT, returns list of dicts. For others, returns True/False.
        """
        with self.get_cursor() as cursor:
            try:
                cursor.execute(query, params or [])
                if cursor.description:
                    columns = [column[0] for column in cursor.description]
                    results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                    return results
                else:
                    self.connection.commit()
                    return True
            except Exception as e: # Catch broader exceptions during execution
                 print(f"❌ [Local DB] Query execution failed: {str(e)}")
                 print(f"   Query: {query[:500]}{'...' if len(query) > 500 else ''}") # Log truncated query
                 print(f"   Params: {params}")
                 # Rollback might not be necessary if commit wasn't reached, but doesn't hurt
                 if self.connection:
                     try: self.connection.rollback()
                     except pyodbc.Error: pass
                 return [] if query.strip().upper().startswith('SELECT') else False

    def execute_scalar(self, query, params=None):
        """Execute a query and return a single value"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params or [])
            result = cursor.fetchone()
            return result[0] if result else None

    def check_table_exists(self, table_name):
        """Check if a table exists in the database"""
        try:
            # More reliable check using INFORMATION_SCHEMA
            query = """
                SELECT COUNT(*)
                FROM INFORMATION_SCHEMA.TABLES
                WHERE TABLE_SCHEMA = 'dbo' AND TABLE_NAME = ? AND TABLE_CATALOG = ?
            """
            result = self.execute_scalar(query, (table_name, Config.DB_NAME))
            return result is not None and result > 0
        except Exception as e:
            print(f"⚠️ [Local DB] Table check failed for '{table_name}': {str(e)}")
            return False # Assume table doesn't exist if check fails


# Global instance (singleton pattern)
_db_instance = None

def get_db():
    """Get the global database instance for the local DB"""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseConnection()
        if _db_instance.connection is None:
             raise ConnectionError("Failed to initialize the primary local database connection.")
    return _db_instance