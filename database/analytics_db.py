# customer_portal/database/analytics_db.py
"""
Database operations for the Analytics dashboard (Local DB)
Queries Customers, ActiveSessions, and AuditLog tables.
"""

from .connection import get_db
from datetime import datetime, timedelta

class AnalyticsDB:
    """Analytics database operations"""

    def __init__(self):
        self.db = get_db()

    def get_kpi_stats(self):
        """
        Gets the 4 key performance indicators for the dashboard header
        in a single, efficient query.
        """
        query = """
            SELECT
                (SELECT COUNT(*) FROM Customers WHERE is_active = 1) AS active_customers,
                
                (SELECT COUNT(*) FROM ActiveSessions) AS current_sessions,
                
                (SELECT COUNT(*) FROM AuditLog 
                 WHERE action_type = 'CUSTOMER_LOGIN' 
                 AND timestamp >= DATEADD(day, -7, GETUTCDATE())) AS logins_last_7_days,
                 
                (SELECT COUNT(DISTINCT target_customer_id) FROM AuditLog 
                 WHERE action_type = 'CUSTOMER_LOGIN' 
                 AND timestamp >= DATEADD(day, -7, GETUTCDATE())) AS unique_logins_last_7_days
        """
        results = self.db.execute_query(query)
        return results[0] if results else {
            'active_customers': 0,
            'current_sessions': 0,
            'logins_last_7_days': 0,
            'unique_logins_last_7_days': 0
        }

    def get_logins_by_day(self, days=14):
        """
        Gets the count of customer logins grouped by day for the last N days.
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = """
            SELECT 
                CAST(timestamp AS DATE) AS login_date,
                COUNT(*) AS login_count
            FROM AuditLog
            WHERE action_type = 'CUSTOMER_LOGIN' AND timestamp >= ?
            GROUP BY CAST(timestamp AS DATE)
            ORDER BY login_date ASC;
        """
        return self.db.execute_query(query, (cutoff_date,))

    def get_most_active_customers(self, limit=10):
        """
        Gets the top N customers by login count.
        """
        query = """
            SELECT TOP (?)
                ISNULL(target_customer_email, 'Unknown') AS customer_email,
                COUNT(*) AS login_count
            FROM AuditLog
            WHERE action_type = 'CUSTOMER_LOGIN'
            GROUP BY target_customer_email
            ORDER BY login_count DESC;
        """
        return self.db.execute_query(query, (limit,))

    def get_recent_logins(self, limit=10):
        """
        Gets the last N customer login events.
        """
        query = """
            SELECT TOP (?)
                timestamp,
                target_customer_email,
                details
            FROM AuditLog
            WHERE action_type = 'CUSTOMER_LOGIN'
            ORDER BY timestamp DESC;
        """
        return self.db.execute_query(query, (limit,))

# Singleton instance
analytics_db = AnalyticsDB()