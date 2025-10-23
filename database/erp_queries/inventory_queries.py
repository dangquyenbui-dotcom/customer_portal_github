# customer_portal/database/erp_queries/inventory_queries.py
"""
ERP Queries related to Customer Inventory.
"""
from database.erp_connection_base import get_erp_db_connection

class ERPInventoryQueries:
    """Contains ERP query methods specific to Customer Inventory."""

    def get_inventory_by_customer(self, erp_customer_name):
        """
        Retrieves inventory details filtered by the ERP customer name.
        Excludes quarantine, job, and staging locations.
        """
        db = get_erp_db_connection()
        if not db:
            print("❌ [ERP Inventory] Failed to get ERP DB connection.")
            return []

        # The main SQL query provided by the user
        sql = """
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
                AND dmpr1.p1_name = ? -- Filter by the specific customer name
            ORDER BY dmprod.pr_codenum, dtfifo.fi_userlot; -- Added sorting
        """
        params = [erp_customer_name]
        results = db.execute_query(sql, params)
        if results is None: # Handle query execution failure
             print(f"❌ [ERP Inventory] Query failed for customer: {erp_customer_name}")
             return []
        print(f"ℹ️ [ERP Inventory] Found {len(results)} inventory records for customer: {erp_customer_name}")
        return results