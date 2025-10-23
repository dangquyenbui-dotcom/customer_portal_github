# customer_portal/routes/inventory.py
"""
Routes for customer inventory viewing.
"""

from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify, send_file, request
from auth import login_required # Use the customer login decorator
from database import get_erp_service
import openpyxl
from io import BytesIO
from datetime import datetime
import traceback

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@inventory_bp.route('/')
@login_required # Protect this route
def view_inventory():
    """Renders the main customer inventory grid page."""
    erp_service = get_erp_service()
    inventory_data = []
    error_message = None

    # Get the ERP customer name stored in the session during login
    erp_customer_name = session.get('customer', {}).get('erp_customer_name')

    if not erp_customer_name:
        flash('Customer identity not found in session. Please log in again.', 'error')
        return redirect(url_for('main.logout')) # Force logout if essential info is missing

    try:
        inventory_data = erp_service.get_customer_inventory(erp_customer_name)
    except Exception as e:
        error_message = f"Error fetching inventory data from ERP: {str(e)}"
        flash(error_message, 'error')
        traceback.print_exc() # Log the full error for debugging

    # Extract unique values for filters BEFORE passing to template
    parts = sorted(list(set(item.get('Part', '') for item in inventory_data if item.get('Part'))))
    bins = sorted(list(set(item.get('BIN', '') for item in inventory_data if item.get('BIN'))))
    # Add more filter options if needed (e.g., User_Lot, Exp_Date ranges)

    return render_template(
        'inventory_view.html',
        inventory_data=inventory_data,
        error_message=error_message,
        # Pass filter options
        filter_parts=parts,
        filter_bins=bins
    )

@inventory_bp.route('/api/export-xlsx', methods=['POST'])
@login_required # Protect this route
def export_inventory_xlsx():
    """API endpoint to export the visible inventory data to an XLSX file."""
    try:
        data = request.get_json()
        headers = data.get('headers', [])
        rows = data.get('rows', [])

        if not headers or not rows:
            return jsonify({'success': False, 'message': 'No data to export'}), 400

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Inventory Export"
        ws.append(headers)

        for row_data in rows:
            # Attempt to convert numeric-like strings, keep others as is
            processed_row = []
            for cell_value in row_data:
                if isinstance(cell_value, str):
                    cleaned_value = cell_value.replace(',', '') # Handle thousands separators
                    try:
                        # Try float first for quantities
                        processed_row.append(float(cleaned_value))
                    except ValueError:
                         # Keep as string if not a simple number (like dates, lots, text)
                        processed_row.append(cell_value)
                else:
                    processed_row.append(cell_value) # Append non-strings directly
            ws.append(processed_row)

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        customer_name = session.get('customer', {}).get('erp_customer_name', 'Export').replace(' ', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Inventory_{customer_name}_{timestamp}.xlsx"

        return send_file(
            output,
            as_attachment=True,
            download_name=filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    except Exception as e:
        print(f"❌ Error exporting inventory: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'An error occurred during export.'}), 500