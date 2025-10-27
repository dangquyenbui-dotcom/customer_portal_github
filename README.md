Here is a completely rewritten and highly detailed `README.md` file for your project, incorporating all the features we have built, including the Active Directory integration and honeypot security.

-----

# WePackItAll - Customer Portal

## 🌟 Overview

The **WePackItAll Customer Portal** is a secure, modern web application built with Flask, designed to provide WePackItAll customers with 24/7 real-time visibility into their on-hand inventory. The application queries a read-only ERP database (Deacom) to present live data, ensuring customers always have the most accurate information.

This portal is a dual-interface application:

1.  **Customer-Facing Portal:** A secure, intuitive interface where customers can log in to view, filter, sort, and export their inventory data. It is designed to be fast, responsive, and user-friendly, with smart UI features like cascading filters and a global search.
2.  **Administrative Backend:** A separate, secure `/admin` section for WePackItAll staff to manage all customer portal accounts. It features a hybrid authentication system, allowing access to *both* a local super-admin and specific members of an Active Directory group.

The application is built for production, prioritizing security (hybrid admin auth, bot protection, hashed passwords, forced password resets), data integrity (read-only ERP connection), and maintainability (Flask Blueprints, service-oriented architecture).

-----

## 🚀 Core Features

### Customer View (`/`)

  * **Secure Authentication:** Customers log in with an email and password. All credentials are securely hashed and stored in a dedicated local database.
  * **Forced Password Reset:** If an admin creates an account or resets a password, the user is automatically redirected to a "Change Password" screen upon their first login, ensuring the temporary password is never used to access data.
  * **Live Inventory Dashboard (`/inventory`):**
      * **Real-Time Data:** The inventory grid is populated by a direct, read-only query to the ERP database, ensuring the data is always live.
      * **Data Scoping:** Customers only see inventory associated with the `erp_customer_name(s)` assigned to their account. A special **"All"** designation grants visibility across all ERP customers, ideal for internal or broker accounts.
  * **Powerful Client-Side Filtering:**
      * **Global Search:** A single search box that instantly filters the table by *any* text in *any* column (Part, Description, Lot, PO, Status, etc.).
      * **Cascading Dropdown Filters:** A set of dropdown filters for **Part**, **Bin**, and **Status**. When a user selects an option in one filter, all other dropdowns instantly update to show *only* the remaining valid options.
      * **State Persistence:** All filter and sort preferences are saved in the browser's session storage, so a user's view is preserved when they refresh the page or navigate away and come back.
  * **Smart Table UI:**
      * **Multi-Column Sorting:** Users can click any column header to sort the data (alphabetically, numerically, or by date).
      * **Row Count:** A footer dynamically updates to show "Showing X of Y rows" as filters are applied.
  * **Data Export:** A "Download XLSX" button instantly generates and downloads an Excel file containing *only the currently visible filtered and sorted data*.

### Admin View (`/admin`)

  * **Secure, Hybrid Authentication:** The admin login at `/admin-login` supports two independent methods:
    1.  **Local Admin:** A primary super-user (e.g., `cp_admin`) defined directly in the `.env` file.
    2.  **Active Directory:** Any user who is a member of the configured AD group (e.g., `Customer_Portal_Admin`) can log in with their standard company credentials.
  * **Smart Login:** The username field automatically detects and trims email domains (e.g., `quinn.bui@wepackitall.com` is processed as `quinn.bui`) for AD authentication.
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

## 🛡️ Security Features

  * **Hybrid Admin Authentication:** The admin panel is secured by checking against a local `.env` admin first, then falling back to Active Directory. This provides both emergency access (if AD is down) and centralized enterprise management.
  * **AD Lockout Prevention (Honeypot):**
      * To prevent brute-force bot attacks from locking out AD accounts, both the customer and admin login pages contain an invisible "honeypot" field (`hp_email`).
      * This field is hidden from human users via CSS but is visible to bots.
      * The server will **silently reject any login attempt** where this field is filled out, effectively stopping automated attacks without any impact on real users.
  * **Secure Password Hashing:** All customer passwords and the local admin password are stored using strong, one-way `scrypt` or `pbkdf2` hashes.
  * **Forced Password Resets:** All newly created customer accounts (and those reset by an admin) are flagged to `must_reset_password`, ensuring temporary passwords are never used to access data.
  * **Bot Protection:** No third-party services (like Google reCAPTCHA) are required. The honeypot provides a seamless, effective, and private bot-blocking mechanism.

-----

## 💻 Technology Stack

  * **Backend:** **Python 3.10+**
      * **Framework:** **Flask** (using Application Factory pattern and Blueprints)
      * **WSGI Server:** **Waitress** (for production deployment)
  * **Database:**
      * **Application DB:** **Microsoft SQL Server** (stores user accounts, audit logs)
      * **Data Source:** **Read-Only connection to ERP (Deacom) SQL Server**
      * **Driver:** **pyodbc** (for all SQL Server connections)
  * **Authentication:**
      * **Active Directory:** **ldap3** (modern, pure-Python library for LDAP communication)
      * **Local Hashing:** **Werkzeug**
  * **Frontend:**
      * **Templating:** **Jinja2**
      * **Styling:** **CSS3** (no frameworks, pure responsive CSS)
      * **JavaScript:** **Vanilla JavaScript (ES6+)**
  * **Core Libraries:**
      * **Excel Export:** **openpyxl**
      * **Email:** **smtplib** & **ssl** (standard libraries)
      * **Configuration:** **python-dotenv**

-----

## 🏗️ Architecture

The application follows a modular, service-oriented structure to separate concerns.

  * **`app.py` (Root):** The main application factory (`create_app`). Initializes Flask, loads config, and registers all blueprints.
  * **`config.py` (Root):** Loads all settings from `.env` into a `Config` class. Includes validation to ensure all required variables are set.
  * **`/auth`:**
      * **`ad_auth.py`:** (NEW) Manages all Active Directory (LDAP) connections and group validation using the `ldap3` library.
      * **`customer_auth.py`:** Manages customer login/registration *and* orchestrates the hybrid admin login (checking local first, then AD). Includes logic for trimming email domains.
  * **`/database`:**
      * `connection.py`: Manages the read/write connection to the **local Application DB** (for users, audit logs).
      * `erp_connection_base.py`: Manages the **read-only connection to the ERP DB**. Includes robust logic to try multiple ODBC drivers.
      * `customer_data.py`: Data access layer for the `Customers` table (CRUD, password setting).
      * `audit_log.py`: Data access layer for the `AuditLog` table.
      * `erp_service.py`: A **facade** that acts as the single point of entry for all ERP data requests.
  * **`/routes`:** Contains the Flask **Blueprints** (controllers).
      * `main.py`: Handles core routes like `/login`, `/logout`, `/admin-login`, and `/force-change-password`. Includes the server-side honeypot check.
      * `inventory.py`: Handles the customer-facing `/inventory` dashboard and the `/api/export-xlsx` endpoint.
      * `/admin/panel.py`, `customers.py`, `audit.py`: All routes for the admin backend.
  * **`/static`:** Contains all CSS, JS, and image assets. `inventory.js` contains the client-side filtering/sorting logic.
  * **`/templates`:**
      * `login.html` & `admin_login.html`: Contain the user-facing forms, including the invisible **honeypot** field for bot protection.
      * `inventory_view.html`: The main customer dashboard.
      * `/admin/`: Templates for the admin section.
      * `/email/`: HTML templates for welcome and password reset emails.
  * **`/utils`:**
      * `email_service.py`: Logic for sending templated emails.
      * `validators.py`: Server-side validation for email/password.

-----

## 🛠️ Getting Started

### Prerequisites

  * Python 3.10+
  * Microsoft SQL Server (for the local `CustomerPortalDB`)
  * Read-only access to the target ERP (Deacom) SQL Server database
  * **ODBC Driver for SQL Server:** The server running the app must have a compatible ODBC driver installed (e.g., "ODBC Driver 17 for SQL Server").
  * **Active Directory:** AD credentials for a service account that can bind and read group memberships.
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
      * Open `.env` and fill in *all* the required values, especially the database, SMTP, and AD sections.
      * **To generate the `ADMIN_PASSWORD_HASH`:**
          * Run this one-time command in your terminal:
            ```bash
            python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your_chosen_password', 'scrypt:32768:8:1'))"
            ```
          * Paste the *entire* output (starting with `scrypt:`) into the `.env` file.

5.  **Initialize the Database:**

      * Ensure the database specified in `DB_NAME` exists on your `DB_SERVER`.
      * Ensure the user in `DB_USERNAME` has `db_owner` (or at minimum `db_datareader`, `db_datawriter`, and `db_ddladmin`) permissions on that database.
      * **The application will automatically create all required tables (`Customers`, `AuditLog`) on its first run.**

6.  **Run the Application (Production):**

      * Use a production-grade WSGI server like Waitress:

    <!-- end list -->

    ```bash
    waitress-serve --host=0.0.0.0 --port=5001 app:create_app
    ```

7.  **Access in Browser:**

      * **Customer Portal:** `http://your_server_ip:5001`
      * **Admin Portal:** `http://your_server_ip:5001/admin-login`

-----

## ⚙️ Configuration (`.env`)

[cite\_start]All sensitive data and environment-specific settings are managed in the `.env` file[cite: 2].

### General

  * `SECRET_KEY`: A long, random string used for signing session cookies. **Must be changed for production.**
  * `SESSION_HOURS`: How long a user's session lasts before they are required to log in again.
  * `TEST_MODE`: (Optional) Set to `True` to bypass AD authentication for testing.

### Local Application Database

  * `DB_SERVER`: URL/IP of the SQL Server for the app's *local* database.
  * `DB_NAME`: Name of the database (e.g., `CustomerPortalDB`).
  * `DB_USE_WINDOWS_AUTH`: Set to `True` or `False`.
  * `DB_USERNAME`: SQL user for the local DB.
  * `DB_PASSWORD`: Password for the local DB user.

### ERP (Deacom) Database

  * `ERP_DB_SERVER`: URL/IP of the read-only ERP database.
  * `ERP_DB_NAME`: Name of the ERP database.
  * `ERP_DB_USERNAME`: Read-only SQL user for the ERP DB.
  * `ERP_DB_PASSWORD`: Password for the ERP DB user.
  * `ERP_DB_DRIVER`: The name of the ODBC driver installed on the server (e.g., `ODBC Driver 17 for SQL Server`).

### Email Server

  * `SMTP_SERVER`: URL of your SMTP provider (e.g., `smtp.office365.com`).
  * `SMTP_PORT`: Port for the SMTP server (e.g., `587`).
  * `SMTP_USE_TLS`: `True` or `False`.
  * `SMTP_USERNAME`: Email address to send from.
  * `SMTP_PASSWORD`: Password for the email account.
  * `EMAIL_FROM`: The "From" address shown to users.
  * `EMAIL_BCC`: (Optional) An email address to BCC on all outgoing mail for logging.

### Admin Authentication

  * **Local Admin (Primary)**
      * `ADMIN_USERNAME`: Username for the local super-admin (e.g., `cp_admin`).
      * `ADMIN_PASSWORD_HASH`: The generated `scrypt` hash for the local admin's password.
  * **Active Directory (Fallback)**
      * `AD_SERVER`: URL/IP of your domain controller (e.g., `wpia-pdc.wepackitall.local`).
      * `AD_DOMAIN`: Your internal AD domain (e.g., `wepackitall.local`).
      * `AD_PORT`: `389` (non-SSL) or `636` (SSL).
      * `AD_SERVICE_ACCOUNT`: A read-only service account username.
      * `AD_SERVICE_PASSWORD`: The service account's password.
      * `AD_BASE_DN`: The base DN to start searches from (e.g., `DC=wepackitall,DC=local`).
      * `AD_PORTAL_ADMIN_GROUP`: The *exact name* of the AD security group that grants admin access (e.g., `Customer_Portal_Admin`).