Here is a completely rewritten and highly detailed `README.md` file for your project, incorporating all the features and context from our conversation.

-----

# Customer Portal - WePackItAll

## 🌟 Overview

The **WePackItAll Customer Portal** is a secure, modern web application built with Flask, designed to provide WePackItAll customers with 24/7 real-time visibility into their on-hand inventory. The application queries a read-only ERP database (Deacom) to present live data, ensuring customers always have the most accurate information.

This portal is a dual-interface application:

1.  **Customer-Facing Portal:** A secure, intuitive interface where customers can log in to view, filter, sort, and export their inventory data. It is designed to be fast, responsive, and user-friendly, with smart UI features like cascading filters and a global search.
2.  **Administrative Backend:** A separate, secure `/admin` section for WePackItAll staff to manage all customer portal accounts. Admins can create new users, edit existing ones, assign specific ERP customer data access, and securely reset passwords, with all actions tracked in a detailed audit log.

The application is built for production, prioritizing security (hashed passwords, session management, separate admin auth), data integrity (read-only ERP connection), and maintainability (Flask Blueprints, service-oriented architecture).

-----

## 🚀 Core Features

### Customer View (`/`)

  * **Secure Authentication:** Customers log in with an email and password. All credentials are securely hashed and stored in a dedicated local database.
  * **Forced Password Reset:** If an admin creates an account or resets a password, the user is automatically redirected to a "Change Password" screen upon their first login, ensuring the temporary password is never used to access data.
  * **Live Inventory Dashboard (`/inventory`):**
      * **Real-Time Data:** The inventory grid is populated by a direct, read-only query to the ERP database, ensuring the data is always live.
      * **Data Scoping:** Customers only see inventory associated with the `erp_customer_name(s)` assigned to their account. A special **"All"** designation grants visibility across all ERP customers, ideal for internal or broker accounts.
      * **Detailed Columns:** Displays all critical inventory data, including:
          * Part
          * Description
          * On Hand Qty
          * Unit
          * Bin
          * User Lot
          * Exp Date
          * Reference
          * PO
          * **Status** (e.g., "Available", "Quarantined", "Pending QC", "Issued to Job")
          * Last Rec Date
          * Last Tran Date
  * **Powerful Client-Side Filtering:**
      * **Global Search:** A single search box that instantly filters the table by *any* text in *any* column (Part, Description, Lot, PO, Status, etc.).
      * **Cascading Dropdown Filters:** A set of dropdown filters for **Part**, **Bin**, and **Status**. When a user selects an option in one filter, all other dropdowns instantly update to show *only* the remaining valid options.
      * **State Persistence:** All filter and sort preferences are saved in the browser's session storage, so a user's view is preserved when they refresh the page or navigate away and come back.
  * **Smart Table UI:**
      * **Dynamic Column Sizing:** The "Description" column intelligently wraps its text, preventing a single long description from stretching the table horizontally and forcing a scroll. This keeps all other data columns neat and visible.
      * **Multi-Column Sorting:** Users can click any column header to sort the data (alphabetically, numerically, or by date).
      * **Row Count:** A footer dynamically updates to show "Showing X of Y rows" as filters are applied.
  * **Data Export:** A "Download XLSX" button instantly generates and downloads an Excel file containing *only the currently visible filtered and sorted data*.

### Admin View (`/admin`)

  * **Separate Secure Login:** Administrators log in via `/admin-login` using credentials stored in the application's environment file (`.env`), completely separate from the customer database.
  * **Admin Dashboard (`/admin`):** A central hub for navigating all administrative functions.
  * **Customer Account Management (`/admin/customers`):**
      * **Full CRUD:** Admins can Create, Read, Update, and Deactivate/Reactivate customer accounts.
      * **ERP Customer Assignment:** When creating or editing a user, admins can select one or more `erp_customer_name`s from a checklist populated directly from the ERP.
      * **"All" Access:** Admins can grant a user "All" access, which overrides individual selections and provides full inventory visibility.
      * **Live Search & Filter:** The customer list can be instantly filtered by status (Active, Inactive, All) or searched by name, email, or ERP name.
  * **Admin-Initiated Password Reset:**
      * Admins can click a "Reset PW" button for any user.
      * This action generates a new, secure temporary password.
      * The system updates the user's account, flags it to "must reset", and **automatically emails** the temporary password to the customer.
  * **Audit Log (`/admin/audit`):**
      * **Immutable Record:** Automatically logs all critical admin actions (e.g., `CUSTOMER_CREATE`, `CUSTOMER_UPDATE`, `CUSTOMER_DEACTIVATE`, `ADMIN_PW_RESET_EMAIL`).
      * **Detailed View:** Shows timestamp, admin responsible, action type, target customer (ID and email), and a JSON blob of what was changed (e.g., `{'status': {'from': 'Active', 'to': 'Inactive'}}`).
      * **Filterable:** The log can be filtered by admin, action type, or searched by customer email/ID.

-----

## 💻 Technology Stack

  * **Backend:** **Python 3.10+**
      * **Framework:** **Flask** (using Application Factory pattern and Blueprints)
      * **WSGI Server:** **Waitress** (for production deployment)
  * **Database:**
      * **Application DB:** **Microsoft SQL Server** (stores user accounts, audit logs)
      * **Data Source:** **Read-Only connection to ERP (Deacom) SQL Server**
      * **Driver:** **pyodbc** (for all SQL Server connections)
  * **Frontend:**
      * **Templating:** **Jinja2**
      * **Styling:** **CSS3** (no frameworks, pure responsive CSS)
      * **JavaScript:** **Vanilla JavaScript (ES6+)** (no frameworks, all filtering/sorting/UI logic is custom)
  * **Core Libraries:**
      * **Password Hashing:** **Werkzeug**
      * **Excel Export:** **openpyxl**
      * **Email:** **smtplib** & **ssl** (standard libraries)
      * **Configuration:** **python-dotenv**

-----

## 🏗️ Architecture

The application follows a modular, service-oriented structure to separate concerns.

  * **`app.py` (Root):** The main application factory (`create_app`). Initializes Flask, loads config, and registers all blueprints.
  * **`config.py` (Root):** Loads all settings from `.env` into a `Config` class. Includes validation to ensure all required variables are set.
  * **`/auth`:**
      * `customer_auth.py`: Manages all authentication logic. Includes the `@login_required` and `@admin_required` decorators, password verification, and the crucial check that forces password resets.
  * **`/database`:**
      * `connection.py`: Manages the read/write connection to the **local Application DB** (for users, audit logs).
      * `erp_connection_base.py`: Manages the **read-only connection to the ERP DB**. Includes robust logic to try multiple ODBC drivers to find one that works.
      * `customer_data.py`: Data access layer for the `Customers` table (CRUD, password setting).
      * `audit_log.py`: Data access layer for the `AuditLog` table.
      * `erp_service.py`: A **facade** that acts as the single point of entry for all ERP data requests. It uses...
      * `erp_queries/inventory_queries.py`: Contains the raw SQL query to fetch inventory data. This is the only file that contains ERP-specific table/column names.
  * **`/routes`:** Contains the Flask **Blueprints** (controllers).
      * `main.py`: Handles core routes like `/login`, `/logout`, `/admin-login`, and `/force-change-password`.
      * `inventory.py`: Handles the customer-facing `/inventory` dashboard and the `/api/export-xlsx` endpoint.
      * `/admin/panel.py`: The admin dashboard homepage.
      * `/admin/customers.py`: All routes for admin-based customer CRUD and password resets.
      * `/admin/audit.py`: The route for viewing the audit log.
  * **`/static`:**
      * `/css`: Contains `base.css` (shared styles), `login.css` (login pages), and `admin.css` (styles for admin panel and data grids).
      * `/js`:
          * `common.js`: Shared utilities (modals, alerts).
          * `theme.js`: Dark/Light mode theme switcher.
          * `inventory.js`: **The core of the customer UI.** This file handles all client-side sorting, global search, and dynamic cascading filter logic.
      * `/img`: Contains logos and favicons.
  * **`/templates`:**
      * `base.html`: The main template all other pages extend.
      * `login.html` & `admin_login.html`: Separate login pages.
      * `inventory_view.html`: The main customer dashboard, including all HTML and CSS for the filter bar and data grid.
      * `force_change_password.html`: The page users are forced to visit.
      * `/admin/`: Templates for the admin section (panel, customer management, audit log).
      * `/email/password_reset.html`: The HTML email template sent for password resets.
  * **`/utils`:**
      * `email_service.py`: Logic for connecting to the SMTP server and sending the templated password reset email (including BCC).
      * `validators.py`: Server-side validation for email formats and password complexity.
      * `helpers.py`: Utility functions (e.g., `get_client_info`).

-----

## 🛠️ Getting Started

### Prerequisites

  * Python 3.10+
  * Microsoft SQL Server (for the local `CustomerPortalDB`)
  * Read-only access to the target ERP (Deacom) SQL Server database
  * **ODBC Driver for SQL Server:** The server running the app must have a compatible ODBC driver installed (e.g., "ODBC Driver 17 for SQL Server").
  * **SMTP Server:** Access to an email server (like Office 365) for sending password reset emails.

### Installation & Setup

1.  **Clone the Repository:**

    ```bash
    git clone <your-repository-url>
    cd customer_portal
    ```

2.  **Create and Activate Virtual Environment:**

    ```bash
    # Create the environment
    python -m venv venv

    # Activate (Windows PowerShell)
    .\venv\Scripts\Activate.ps1
    # (or on macOS/Linux: source venv/bin/activate)
    ```

3.  **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up Environment Variables (`.env`):**

      * Copy the `.env.template` file to a new file named `.env`.
      * Open `.env` and fill in *all* the required values:
          * `SECRET_KEY`: Generate a strong random key.
          * `DB_*`: Connection details for your **local** SQL Server (for user accounts).
          * `ERP_*`: Connection details for the **read-only ERP** database.
          * `SMTP_*`: Credentials for your email server.
          * `ADMIN_USERNAME`: The username for the admin login (e.g., `cp_admin`).
          * `ADMIN_PASSWORD_HASH`: **This is critical.** You must generate a hash for your desired admin password.
              * Run the included `hash_admin.py` script (`python hash_admin.py`) and copy the resulting hash.
              * *Alternatively*, run this one-time command:
                ```bash
                python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your_chosen_password'))"
                ```
              * Paste the generated hash (it will start with `scrypt:`) into the `.env` file.

5.  **Initialize the Database:**

      * Ensure the database specified in `DB_NAME` exists on your `DB_SERVER`.
      * Ensure the user in `DB_USERNAME` has `db_owner` (or at minimum `db_datareader`, `db_datawriter`, and `db_ddladmin`) permissions on that database.
      * **The application will automatically create all required tables (`Customers`, `AuditLog`, `PasswordResetTokens`) on its first run.**

6.  **Run the Application (Development):**

      * (Ensure your virtual environment is active)

    <!-- end list -->

    ```bash
    flask run --host=0.0.0.0 --port=5001
    ```

7.  **Run the Application (Production):**

      * Use a production-grade WSGI server like Waitress:

    <!-- end list -->

    ```bash
    waitress-serve --host=0.0.0.0 --port=5001 app:create_app
    ```

8.  **Access in Browser:**

      * **Customer Portal:** `http://your_server_ip:5001`
      * **Admin Portal:** `http://your_server_ip:5001/admin-login`

-----

## ⚙️ Configuration (`.env`)

All sensitive data and environment-specific settings are managed in the `.env` file.

  * `SECRET_KEY`: A long, random string used for signing session cookies. **Must be changed for production.**
  * `SESSION_HOURS`: How long a user's session lasts before they are required to log in again.
  * `APP_BASE_URL`: (Optional) The public URL of the portal (e.g., `https://portal.wepackitall.com`). If set, this will be used in password reset emails instead of `localhost`.
  * `DB_*` vars: Define the connection to the **local** SQL Server that stores customer accounts, sessions, and audit logs.
  * `ERP_*` vars: Define the **read-only** connection to the Deacom ERP database. `ERP_DB_DRIVER` must match an installed ODBC driver on the server.
  * `SMTP_*` vars: Defines the email server for sending password resets. `EMAIL_BCC` is optional but recommended for tracking sent emails.
  * `ADMIN_USERNAME` / `ADMIN_PASSWORD_HASH`: Credentials for the `/admin` section. **Do not store a plain-text password.**

-----

## 🏭 Running for Production

  * **WSGI Server:** **Do not use `flask run` in production.** Use a proper WSGI server like **Waitress** (as shown above) or Gunicorn.
  * **HTTPS:** This application should be run behind a reverse proxy (like **Nginx**, **Apache**, or **IIS**) that handles SSL/TLS termination (HTTPS). This is critical for protecting passwords and session data.
  * **Environment:** Ensure the `.env` file is secured and not publicly accessible.
  * **Firewall:** Ensure the server's firewall allows traffic on the port you are running on (e.g., 5001).