Customer Portal - WePackItAll

🌟 Overview

The Customer Portal is a secure web application for WePackItAll's customers, offering real-time visibility into their inventory levels stored at WePackItAll facilities. It also provides a dedicated administration interface for managing customer access and monitoring system activity.

Customer Inventory View: Customers can log in to view a filterable, sortable grid displaying live inventory data specific to their assigned ERP customer name(s). Data is sourced directly from a read-only connection to the ERP database. Customers assigned the special "All" designation can view inventory across all ERP customers.

Admin Customer Management: A secure /admin section allows WePackItAll administrators to:

Create, view, edit, and deactivate customer portal accounts.

Assign one or multiple ERP customer names (or "All") to each portal account, controlling their data visibility.

Reset customer passwords, triggering an email with a temporary password and forcing the customer to set a new one upon their next login.

Audit Log: Administrators can view a detailed log of significant actions performed within the admin section (e.g., customer creation, updates, deactivation, password resets) for accountability and tracking.

🚀 Getting Started

Prerequisites

Python 3.10+

Microsoft SQL Server (for the local CustomerPortalDB)

Read-only access to the target ERP SQL Server database (e.g., Deacom Cloud).

Appropriate ODBC Drivers installed on the server running the application (e.g., "ODBC Driver 17 for SQL Server" or similar, matching the .env configuration).

An SMTP server (like Office 365) for sending password reset emails.

Installation & Setup

Clone the Repository:

git clone <your-repository-url>
cd customer_portal


Set Up Environment Variables (.env):

Copy .env.template to a new file named .env in the project root.

Crucially, update .env with your specific configuration:

SECRET_KEY: Generate a strong, random key.

DB_*: Connection details for the local CustomerPortalDB.

ERP_*: Connection details for the read-only ERP database.

SMTP_*, EMAIL_FROM, EMAIL_BCC: Credentials and settings for your email server (e.g., Office 365). The EMAIL_BCC is optional but recommended for tracking.

ADMIN_USERNAME, ADMIN_PASSWORD_HASH: Credentials for the portal's admin access. Generate the hash using the command provided in .env.template or hash_admin.py.

APP_BASE_URL (Optional): Set this to the public URL of the portal (e.g., http://portal.yourcompany.com) if email links need to point to something other than http://localhost:5001.

Create and Activate Virtual Environment:

# Navigate to the project root directory
python -m venv venv

# Activate (example for Windows PowerShell):
.\venv\Scripts\Activate.ps1
# (Use appropriate activation command for your OS/shell)


Install Dependencies:

pip install -r requirements.txt


Database Initialization (CustomerPortalDB):

Ensure the CustomerPortalDB database and the specified login/user exist on your DB_SERVER.

Grant the user necessary permissions (e.g., db_datareader, db_datawriter, db_ddladmin, CONNECT).

The application will automatically create the required tables (Customers, AuditLog, PasswordResetTokens) on its first run if they don't exist. It will also add new columns (like must_reset_password) if needed.

Run the Application (Production):
Use a production-ready WSGI server like Waitress. Ensure the virtual environment is active.

waitress-serve --host=0.0.0.0 --port=5001 --call app:create_app


(Adjust host/port. Ensure firewalls allow traffic. Port 5001 avoids conflict with Production Portal on 5000)

Access in Browser:

Customers: http://your_server_ip:5001 (redirects to /login)

Admin: http://your_server_ip:5001/admin-login

🛠️ Core Features

Customer View

Login: Secure login using email and password.

Forced Password Change: If an admin resets their password, the customer is required to set a new one immediately after logging in with the temporary password.

Inventory Dashboard (/inventory):

Displays inventory items linked to the customer's assigned ERP name(s) or all items if assigned "All". Data fetched live from ERP.

Features filtering (Part, Bin, text search) and sorting.

Export visible data to Excel (.xlsx).

Admin View (/admin)

Login (/admin-login): Separate, secure login using credentials from .env.

Dashboard (/admin): Central navigation for admin functions.

Customer Management (/admin/customers):

View, filter, and search customer accounts.

Add new customers, assigning one or multiple ERP names using checkboxes, or the special "All" designation.

Edit customer details (name, email, ERP assignments, active status).

Activate/Deactivate accounts.

Admin Password Reset: Trigger an email to the customer containing a secure, temporary password, forcing them to change it on their next login.

Audit Log (/admin/audit):

View a chronological log of actions performed by administrators (customer creation, updates, status changes, password resets).

Filter logs by administrator, action type, or target customer (ID/email).

💻 Technology Stack

Backend: Python 3, Flask

WSGI Server: Waitress

Database: Microsoft SQL Server (for local data), Read-Only connection to ERP SQL Server

Database Driver: pyodbc

Frontend: Jinja2 Templating, HTML, CSS, Vanilla JavaScript

Email: smtplib, ssl

Excel Export: openpyxl

Environment Variables: python-dotenv

Password Hashing: Werkzeug

🏗️ Architecture

Flask Application Factory: (app.py) Uses create_app() pattern.

Blueprints: Modular structure (routes/): main, inventory, admin (panel, customers, audit).

Database Layer: (database/)

Connection managers for local DB (connection.py) and ERP (erp_connection_base.py).

Service layer facade for ERP queries (erp_service.py).

Modules for local table operations: customer_data.py, audit_log.py.

Authentication: (auth/) Handles customer/admin login logic and route protection decorators (@login_required, @admin_required), including the forced password reset check.

Utilities: (utils/) Includes helpers (helpers.py), input validators (validators.py), and email sending logic (email_service.py).

Frontend: Server-side rendering (Jinja2); client-side interactions (Vanilla JS).

📁 Project Structure

/customer_portal/
│
├── app.py                  # Flask application factory & runner
├── config.py               # Configuration loader (reads .env)
├── requirements.txt        # Python dependencies
├── .env                    # Local environment variables (GITIGNORED)
├── .env.template           # Template for .env file
├── README.md               # This file
│
├── /auth/                  # Authentication & Authorization
│   ├── __init__.py
│   └── customer_auth.py    # Login logic, decorators, force reset check
│
├── /database/              # Data access layer
│   ├── __init__.py         # Exports DB instances & service getters
│   ├── connection.py       # Local DB (CustomerPortalDB) connection
│   ├── customer_data.py    # Local Customer DB operations (CRUD, PW handling)
│   ├── audit_log.py        # Local AuditLog DB operations
│   ├── erp_connection_base.py # Base ERP DB connection (pyodbc)
│   ├── erp_service.py      # Facade for ERP queries
│   └── /erp_queries/       # Specific SQL queries for ERP
│       ├── __init__.py
│       └── inventory_queries.py # Customer-specific inventory query (handles 'All')
│
├── /routes/                # Flask blueprints (controllers)
│   ├── __init__.py
│   ├── main.py             # Core routes (login, logout, force reset)
│   ├── inventory.py        # Customer inventory view routes
│   └── /admin/             # Admin panel blueprints
│       ├── __init__.py
│       ├── panel.py        # Admin dashboard route
│       ├── customers.py      # Customer CRUD & admin reset routes
│       └── audit.py          # Audit log view route
│
├── /static/                # Frontend assets (CSS, JS, Images)
│   ├── /css/               # base.css, admin.css, login.css
│   ├── /js/                # theme.js, common.js, inventory.js
│   └── /img/               # Logo images
│
├── /templates/             # Jinja2 HTML templates
│   ├── base.html
│   ├── login.html
│   ├── admin_login.html
│   ├── inventory_view.html
│   ├── force_change_password.html # New page for forced reset
│   ├── /admin/
│   │   ├── panel.html
│   │   ├── customer_management.html
│   │   └── audit_log.html    # New page for viewing audit logs
│   └── /email/
│       └── password_reset.html # New email template
│
└── /utils/                 # Helper utilities
    ├── __init__.py
    ├── helpers.py          # General utilities
    ├── validators.py       # Input validation (email, password)
    └── email_service.py    # Email sending logic


⚙️ Configuration (.env)

Key settings managed via the .env file:

SECRET_KEY: Must be set to a unique, random string.

SESSION_HOURS: Duration for user sessions.

DB_*: Connection details for the local CustomerPortalDB.

ERP_*: Connection details for the read-only ERP database.

SMTP_*, EMAIL_FROM, EMAIL_BCC: Required for the admin password reset feature.

ADMIN_USERNAME, ADMIN_PASSWORD_HASH: Credentials for the portal administrator.

APP_BASE_URL (Optional): Public URL for email links.

🏭 Running for Production

WSGI Server: Use Waitress (or Gunicorn/uWSGI). Do not use flask run or python app.py with debug=True.

waitress-serve --host=0.0.0.0 --port=5001 --call app:create_app


Configuration: Ensure a strong SECRET_KEY and correct production database/email settings are in .env.

HTTPS: Strongly recommended via a reverse proxy (Nginx, Apache, IIS).

Logging: Configure proper file-based logging in Flask for monitoring.

Virtual Environment: Always run within the activated project virtual environment.

📄 License

(Specify your project's license here)

🙏 Acknowledgements

Flask

Waitress

pyodbc

Werkzeug

openpyxl

python-dotenv

Jinja2