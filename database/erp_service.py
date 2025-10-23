# customer_portal/database/erp_service.py
"""
ERP Service Layer for Customer Portal
Acts as a facade, coordinating calls to specific ERP query modules.
"""
from .erp_connection_base import get_erp_db_connection
from .erp_queries import ERPInventoryQueries

class ErpService:
    """Contains business logic for querying the ERP database."""

    def __init__(self):
        # Instantiate query classes. They use the shared connection internally.
        self.inventory_queries = ERPInventoryQueries()

    def get_customer_inventory(self, erp_customer_name):
        """Fetches inventory filtered by customer name."""
        if not erp_customer_name:
            print("⚠️ [ERP Service] Called get_customer_inventory without customer name.")
            return []
        return self.inventory_queries.get_inventory_by_customer(erp_customer_name)

    def get_all_customer_names(self):
        """Fetches a list of all distinct ERP customer names."""
        return self.inventory_queries.get_all_erp_customer_names()

# --- Singleton instance management ---
_erp_service_instance = None

def get_erp_service():
    """Gets the global singleton instance of the ErpService."""
    global _erp_service_instance
    if _erp_service_instance is None:
        print("ℹ️ Creating new ErpService instance.")
        _erp_service_instance = ErpService()
    return _erp_service_instance

# Optional: Function to explicitly close the connection if needed
def close_erp_connection():
    """Explicitly closes the shared ERP database connection."""
    conn_instance = get_erp_db_connection()
    if conn_instance:
        conn_instance.close()
    global _erp_service_instance
    _erp_service_instance = None