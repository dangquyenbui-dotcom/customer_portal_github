# customer_portal/database/customer_data.py
"""
Customer database operations (Local DB)
Manages the Customers and PasswordResetTokens tables.
"""

from .connection import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets

class CustomerDataDB:
    """Customer database operations"""

    def __init__(self):
        self.db = get_db()
        self.ensure_tables()

    def ensure_tables(self):
        """Ensure the Customers and PasswordResetTokens tables exist."""
        with self.db.get_connection() as conn:
            if not conn.check_table_exists('Customers'):
                print("⏳ Creating Customers table...")
                create_customers_query = """
                    CREATE TABLE Customers (
                        customer_id INT IDENTITY(1,1) PRIMARY KEY,
                        first_name NVARCHAR(100) NOT NULL,
                        last_name NVARCHAR(100) NOT NULL,
                        email NVARCHAR(255) NOT NULL UNIQUE,
                        password_hash NVARCHAR(255) NOT NULL,
                        erp_customer_name NVARCHAR(255) NOT NULL,
                        is_active BIT DEFAULT 1 NOT NULL,
                        created_date DATETIME DEFAULT GETDATE() NOT NULL,
                        last_login_date DATETIME NULL
                    );
                    CREATE INDEX IX_Customers_ErpName ON Customers(erp_customer_name);
                    CREATE INDEX IX_Customers_Active ON Customers(is_active);
                """
                if conn.execute_query(create_customers_query):
                    print("✅ Customers table created successfully.")
                else:
                    print("❌ Failed to create Customers table.")

            if not conn.check_table_exists('PasswordResetTokens'):
                print("⏳ Creating PasswordResetTokens table...")
                create_tokens_query = """
                    CREATE TABLE PasswordResetTokens (
                        token_id INT IDENTITY(1,1) PRIMARY KEY,
                        customer_id INT NOT NULL,
                        token_hash NVARCHAR(255) NOT NULL UNIQUE,
                        expiry_date DATETIME NOT NULL,
                        is_used BIT DEFAULT 0 NOT NULL,
                        CONSTRAINT FK_Token_Customer FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
                    );
                     CREATE INDEX IX_Tokens_Expiry ON PasswordResetTokens(expiry_date);
                     CREATE INDEX IX_Tokens_Used ON PasswordResetTokens(is_used);
                """
                if conn.execute_query(create_tokens_query):
                    print("✅ PasswordResetTokens table created successfully.")
                else:
                     print("❌ Failed to create PasswordResetTokens table.")

    def create_customer(self, first_name, last_name, email, password, erp_customer_name):
        """Creates a new customer record."""
        email = email.lower().strip()
        erp_customer_name = erp_customer_name.strip()
        if not all([first_name, last_name, email, password, erp_customer_name]):
             return False, "All fields are required."

        if self.get_customer_by_email(email):
            return False, "Email address already exists."

        password_hash = generate_password_hash(password)
        query = """
            INSERT INTO Customers (first_name, last_name, email, password_hash, erp_customer_name, is_active)
            VALUES (?, ?, ?, ?, ?, 1)
        """
        params = (first_name, last_name, email, password_hash, erp_customer_name)
        success = self.db.execute_query(query, params)
        return success, "Customer created successfully." if success else "Failed to create customer."

    def get_customer_by_email(self, email):
        """Retrieves a customer by email address."""
        email = email.lower().strip()
        query = "SELECT * FROM Customers WHERE email = ?"
        results = self.db.execute_query(query, (email,))
        return results[0] if results else None

    def get_customer_by_id(self, customer_id):
        """Retrieves a customer by their ID."""
        query = "SELECT * FROM Customers WHERE customer_id = ?"
        results = self.db.execute_query(query, (customer_id,))
        return results[0] if results else None

    def verify_password(self, email, password):
        """Verifies a customer's password."""
        customer = self.get_customer_by_email(email)
        if customer and customer['is_active'] and check_password_hash(customer['password_hash'], password):
            self.update_last_login(customer['customer_id'])
            return customer # Return customer data on successful login
        return None

    def update_last_login(self, customer_id):
        """Updates the last login timestamp for a customer."""
        query = "UPDATE Customers SET last_login_date = GETDATE() WHERE customer_id = ?"
        self.db.execute_query(query, (customer_id,))

    def get_all_customers(self, include_inactive=False):
         """Gets a list of all customers."""
         query = "SELECT customer_id, first_name, last_name, email, erp_customer_name, is_active, created_date, last_login_date FROM Customers"
         if not include_inactive:
             query += " WHERE is_active = 1"
         query += " ORDER BY last_name, first_name"
         return self.db.execute_query(query)

    def update_customer(self, customer_id, first_name, last_name, email, erp_customer_name, is_active):
         """Updates customer details."""
         email = email.lower().strip()
         erp_customer_name = erp_customer_name.strip()

         # Check if email is already used by another customer
         existing = self.get_customer_by_email(email)
         if existing and existing['customer_id'] != customer_id:
             return False, "Email address is already in use by another customer."

         query = """
            UPDATE Customers
            SET first_name = ?, last_name = ?, email = ?, erp_customer_name = ?, is_active = ?
            WHERE customer_id = ?
         """
         params = (first_name, last_name, email, erp_customer_name, 1 if is_active else 0, customer_id)
         success = self.db.execute_query(query, params)
         return success, "Customer updated successfully." if success else "Failed to update customer."

    def set_active_status(self, customer_id, is_active):
        """Sets the active status of a customer."""
        query = "UPDATE Customers SET is_active = ? WHERE customer_id = ?"
        success = self.db.execute_query(query, (1 if is_active else 0, customer_id))
        action = "activated" if is_active else "deactivated"
        return success, f"Customer {action} successfully." if success else f"Failed to {action} customer."

    # --- Password Reset Methods ---

    def create_password_reset_token(self, customer_id):
        """Creates a password reset token."""
        token = secrets.token_urlsafe(32)
        token_hash = generate_password_hash(token) # Hash the token itself for storage
        expiry_date = datetime.utcnow() + timedelta(hours=1) # Token valid for 1 hour

        query = """
            INSERT INTO PasswordResetTokens (customer_id, token_hash, expiry_date, is_used)
            VALUES (?, ?, ?, 0)
        """
        success = self.db.execute_query(query, (customer_id, token_hash, expiry_date))
        return token if success else None # Return the *plain* token to be sent to user

    def validate_password_reset_token(self, token):
         """Validates a token and returns customer_id if valid."""
         query = """
             SELECT customer_id, token_hash, expiry_date
             FROM PasswordResetTokens
             WHERE expiry_date > GETUTCDATE() AND is_used = 0
         """
         tokens = self.db.execute_query(query)
         for record in tokens or []:
             if check_password_hash(record['token_hash'], token):
                 return record['customer_id'] # Valid token found
         return None

    def reset_password(self, customer_id, new_password):
        """Resets the customer's password."""
        new_password_hash = generate_password_hash(new_password)
        query = "UPDATE Customers SET password_hash = ? WHERE customer_id = ?"
        success = self.db.execute_query(query, (new_password_hash, customer_id))
        return success

    def mark_token_used(self, token):
        """Marks a password reset token as used."""
        query = """
             UPDATE PasswordResetTokens
             SET is_used = 1
             WHERE token_hash IN (
                 SELECT token_hash FROM PasswordResetTokens WHERE expiry_date > GETUTCDATE() AND is_used = 0
             )
         """
        # We need to find the specific hash matching the token
        find_query = """
             SELECT token_hash
             FROM PasswordResetTokens
             WHERE expiry_date > GETUTCDATE() AND is_used = 0
         """
        tokens = self.db.execute_query(find_query)
        target_hash = None
        for record in tokens or []:
            if check_password_hash(record['token_hash'], token):
                 target_hash = record['token_hash']
                 break

        if target_hash:
             mark_query = "UPDATE PasswordResetTokens SET is_used = 1 WHERE token_hash = ?"
             self.db.execute_query(mark_query, (target_hash,))

# Singleton instance
customer_db = CustomerDataDB()