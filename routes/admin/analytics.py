# customer_portal/routes/admin/analytics.py
"""
Admin route for viewing usage analytics.
"""
from flask import Blueprint, render_template, g
from auth import admin_required
from database import analytics_db
import json

admin_analytics_bp = Blueprint('admin_analytics', __name__)

@admin_analytics_bp.route('/analytics')
@admin_required
def view_analytics():
    """Displays the usage analytics dashboard."""
    
    kpi_stats = analytics_db.get_kpi_stats()
    logins_by_day = analytics_db.get_logins_by_day(days=14)
    most_active = analytics_db.get_most_active_customers(limit=10)
    recent_logins = analytics_db.get_recent_logins(limit=10)
    
    # Process data for Chart.js
    chart_labels = [row['login_date'].strftime('%Y-%m-%d') for row in logins_by_day]
    chart_data = [row['login_count'] for row in logins_by_day]

    # Clean up recent_logins details (extract IP)
    for login in recent_logins:
        try:
            # Details are stored as a string like "Login from IP: 127.0.0.1"
            login['ip_address'] = login['details'].split('Login from IP: ')[1]
        except Exception:
            login['ip_address'] = 'N/A'
            
    return render_template(
        'admin/analytics.html',
        kpi_stats=kpi_stats,
        most_active_customers=most_active,
        recent_logins=recent_logins,
        chart_labels=json.dumps(chart_labels),
        chart_data=json.dumps(chart_data)
    )