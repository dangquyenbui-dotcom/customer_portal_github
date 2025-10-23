# customer_portal/database/erp_queries/inventory_queries.py
"""
ERP Queries related to Customer Inventory.
"""
from database.erp_connection_base import get_erp_db_connection

class ERPInventoryQueries:
    """Contains ERP query methods specific to Customer Inventory."""

    def get_inventory_by_customer(self, erp_customer_name):
        """
        Retrieves inventory details.
        If erp_customer_name is 'All', fetches for all customers.
        If erp_customer_name is a '|' delimited string, fetches for that list.
        """
        db = get_erp_db_connection()
        if not db:
            print("❌ [ERP Inventory] Failed to get ERP DB connection.")
            return []

        # === MODIFICATION: Dynamic SQL Query Building ===
        
        # The main SQL query provided by the user, without the customer filter
        sql_base = """
            SELECT
                ISNULL(dmpr1.p1_name, '') AS Customer,
                dmprod.pr_codenum AS Part,
                '' AS Customer_Part, -- Placeholder, adjust if data exists
                dmprod.pr_descrip AS Description,
                dtfifo.fi_balance AS On_Hand_Qty,
                ISNULL(dmunit.un_name, '') AS Unit,
                dmloc.lo_name AS BIN,
                dtfifo.fi_attrib2 AS Reference,
                dtfifo.fi_userlot AS User_Lot,
                CONVERT(VARCHAR(10), dtfifo.fi_expires, 101) AS Exp_Date,
                CONVERT(VARCHAR(10), dtfifo.fi_date, 101) AS Last_Transaction_Date,
                CONVERT(VARCHAR(10), dtfifo.fi_lotdate, 101) AS Last_Rec_Date,
                CASE
                    WHEN EXISTS (
                        SELECT 1
                        FROM dtfifo f2
                        WHERE f2.fi_lotnum = dtfifo.fi_lotnum
                            AND f2.fi_action = 'Finish Job'
                            AND f2.fi_postref LIKE 'JJ-%'
                    )
                    THEN ISNULL((
                        SELECT TOP 1 tor.to_billpo
                        FROM dtfifo f3
                        INNER JOIN dtljob lj ON lj.lj_jobnum = TRY_CAST(SUBSTRING(f3.fi_postref, 4, 20) AS INT)
                        INNER JOIN dtord o ON o.or_id = lj.lj_orid -- Link job line to order line
                        INNER JOIN dttord tor ON tor.to_ordnum = o.or_ordnum -- Link order line to order header for PO
                        WHERE f3.fi_lotnum = dtfifo.fi_lotnum
                            AND f3.fi_action = 'Finish Job'
                            AND f3.fi_postref LIKE 'JJ-%'
                        ORDER BY tor.to_id DESC -- Order by header ID to get the latest PO if multiple links exist
                    ), 'N/A')
                    ELSE 'N/A'
                END AS PO
            FROM dtfifo
            INNER JOIN dmprod ON dtfifo.fi_prid = dmprod.pr_id
            LEFT JOIN dmpr1 ON dmprod.pr_user5 = dmpr1.p1_id
            LEFT JOIN dmunit ON dmunit.un_id = dmprod.pr_unid
            INNER JOIN dmloc ON dtfifo.fi_loid = dmloc.lo_id
            WHERE dtfifo.fi_balance > 0
                AND dtfifo.fi_type NOT IN ('quarantine', 'job', 'staging')
        """
        
        params = []
        sql_filter = ""
        
        if not erp_customer_name:
             print("❌ [ERP Inventory] Query called with no customer name.")
             return []
        
        if erp_customer_name == "All":
            # No additional filter, but log it
            print(f"ℹ️ [ERP Inventory] Fetching ALL inventory records for 'All' account.")
            # We add p1_name to the sort order for 'All' accounts
            sql_sort = " ORDER BY dmpr1.p1_name, dmprod.pr_codenum, dtfifo.fi_userlot;"
        
        elif "|" in erp_customer_name:
            # Multiple customers
            customer_list = erp_customer_name.split('|')
            placeholders = ", ".join("?" for _ in customer_list)
            sql_filter = f" AND dmpr1.p1_name IN ({placeholders})"
            params.extend(customer_list)
            print(f"ℹ️ [ERP Inventory] Fetching inventory for {len(customer_list)} customers.")
            # We add p1_name to the sort order for multi-customer accounts
            sql_sort = " ORDER BY dmpr1.p1_name, dmprod.pr_codenum, dtfifo.fi_userlot;"
        
        else:
            # Single customer (legacy or just one selected)
            sql_filter = " AND dmpr1.p1_name = ?"
            params.append(erp_customer_name)
            print(f"ℹ️ [ERP Inventory] Fetching inventory for single customer: {erp_customer_name}")
            sql_sort = " ORDER BY dmprod.pr_codenum, dtfifo.fi_userlot;" # Original sort

        # Combine the query
        sql = sql_base + sql_filter + sql_sort
        # === END MODIFICATION ===

        results = db.execute_query(sql, params)
        if results is None: # Handle query execution failure
             print(f"❌ [ERP Inventory] Query failed for: {erp_customer_name}")
             return []
        print(f"ℹ️ [ERP Inventory] Found {len(results)} inventory records.")
        return results

    def get_all_erp_customer_names(self):
        """
        Retrieves a distinct list of all ERP customer names (from dmpr1).
        """
        db = get_erp_db_connection()
        if not db:
            print("❌ [ERP Customer List] Failed to get ERP DB connection.")
            return []

        # New query to get all distinct customer names
        sql = """
            SELECT DISTINCT p1_name
            FROM dmpr1
            WHERE p1_name IS NOT NULL AND p1_name <> ''
            ORDER BY p1_name;
        """
        results = db.execute_query(sql)
        if results is None:
             print("❌ [ERP Customer List] Query failed.")
             return []
        
        # Extract just the names from the list of dicts
        return [row['p1_name'] for row in results]