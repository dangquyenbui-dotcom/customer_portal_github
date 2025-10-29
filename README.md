# WePackItAll - Customer Portal

## 🌟 Overview

The **WePackItAll Customer Portal** is a secure, modern, and robust web application built with Flask. It is designed to provide WePackItAll customers with 24/7, real-time visibility into their on-hand inventory by querying a read-only ERP database (Deacom).

This application is a complete, dual-interface system:

1.  **Customer-Facing Portal:** A secure, intuitive, and high-performance interface where customers can log in to view, filter, sort, and export their live inventory data. It is designed with a focus on usability, with features like client-side search, dynamic filters, and persistent view states.
2.  **Administrative Backend:** A comprehensive `/admin` section for WePackItAll staff to manage every aspect of the portal. It features a powerful hybrid authentication system (local admin + Active Directory) and provides tools for customer management, security auditing, session monitoring, and usage analytics.

The application is built for production, prioritizing security (hybrid auth, bot protection, DB-backed sessions, forced password resets), data integrity (read-only ERP connection), and maintainability (Flask Blueprints, service-oriented architecture).

-----

## 🚀 Core Features

### Customer-Facing Portal (`/`)

  * **Secure Authentication:** Customers log in with an email and password. All credentials are securely hashed (`scrypt` or `pbkdf2`) and stored in a dedicated local SQL database.
  * **Database-Backed Sessions:** User sessions are not just browser cookies. Upon login, a secure session ID is created in the `ActiveSessions` database table. Every user request is validated against this table, enabling features like remote session termination ("kick").
  * **Forced Password Reset:** If an admin creates an account or resets a password, the user's account is flagged (`must_reset_password`). The user is automatically redirected to a dedicated "Change Password" screen upon their first login, ensuring temporary passwords are never used to access data.
  * **Live Inventory Dashboard (`/inventory`):**
      * **Real-Time Data:** The inventory grid is populated by a direct, read-only query to the ERP database, ensuring the data is always live.
      * **Data Scoping:** Customers only see inventory associated with the `erp_customer_name(s)` assigned to their account. A special **"All"** designation grants visibility across all ERP customers, and the system can handle assignments for multiple, specific customers (e.g., `Customer A|Customer B`).
  * **Powerful Data Grid UI (`inventory_view.html`):**
      * **Global Client-Side Search:** A single search box that instantly filters the entire table by *any* text in *any* column (Part, Description, Lot, PO, etc.).
      * **Dynamic Cascading Filters:** A set of dropdown filters for **Part**, **Bin**, and **Status**. When a user selects an option in one filter, all other dropdowns are instantly re-populated to show *only* the remaining valid options.
      * **Client-Side Sorting:** Users can click any column header (e.g., Part, On Hand Qty, Exp Date) to sort the data (alphabetically, numerically, or by date).
      * **State Persistence:** All filter and sort preferences are saved in the browser's `sessionStorage`, so a user's view is preserved when they refresh the page or navigate away and come back.
      * **Data Export:** A "Download XLSX" button that instantly generates and downloads an Excel file containing *only the currently visible filtered and sorted data*.
      * **Dynamic Summary:** A footer dynamically updates to show "Showing X of Y rows" as filters are applied.

-----

### Administrative Backend (`/admin`)

  * **Secure Hybrid Authentication:** The admin login at `/admin-login` supports two independent methods, providing both redundancy and enterprise integration:
    1.  **Local Admin:** A primary super-user (e.g., `cp_admin`) defined directly in the `.env` file.
    2.  **Active Directory:** Any user who is a member of the configured AD security group (e.g., `Customer_Portal_Admin`) can log in with their standard company credentials.
    <!-- end list -->
      * The system intelligently trims email domains (e.g., `user@domain.com` is processed as `user`) to simplify AD login.
  * **Admin Dashboard (`/admin/panel`):** A central hub for navigating all administrative functions.
  * **Customer Account Management (`/admin/customers`):**
      * **Full CRUD:** Admins can Create, Read, Update, and Deactivate/Reactivate customer accounts.
      * **Live ERP Customer Assignment:** When creating or editing a user, admins can select one or more `erp_customer_name`s from a checklist populated *live* from the ERP database.
      * **Usability:** A search bar is included *inside the modal* to filter the long list of ERP customers, making selection fast and easy.
      * **Client-Side Table Filtering:** The main customer list can be instantly filtered by a live search bar, while status (Active, Inactive, All) is handled by the server.
      * **Automated Welcome Email:** When adding a new customer, a secure temporary password is automatically generated and emailed to the user with a welcome message.
      * **Admin-Initiated Password Reset:** Admins can click a "Reset PW" button for any user. This generates a new temporary password, flags the account to `must_reset_password`, and **automatically emails** the temporary password to the customer.
  * **Audit Log (`/admin/audit`):**
      * **Immutable Record:** Automatically logs all critical administrative and system actions (e.g., `CUSTOMER_CREATE`, `CUSTOMER_UPDATE`, `CUSTOMER_DEACTIVATE`, `ADMIN_PW_RESET_EMAIL`, `CUSTOMER_LOGIN`, `CUSTOMER_LOGOUT`, `CUSTOMER_SESSION_KICK`).
      * **Detailed View:** Shows timestamp, admin responsible (or 'SYSTEM'), action type, target customer (ID and email), and a detailed JSON blob of what was changed (e.g., `{'is_active': {'from': true, 'to': false}}`).
      * **Filterable:** The log can be filtered by admin, action type, or searched by customer email/ID.
  * **Active Session Management (`/admin/sessions`):**
      * **Live View:** Displays a list of all customers *currently logged in* by querying the `ActiveSessions` table.
      * **Session Details:** Shows the customer's name, email, IP address, User Agent, and last seen time.
      * **"Kick Session" Functionality:** Admins can remotely terminate any active session with one click. This deletes the session from the database, forcing the user to log in again on their next action.
  * **Usage Analytics Dashboard (`/admin/analytics`):**
      * **At-a-Glance KPIs:** Displays key performance indicators: **Active Customers**, **Logins (Last 7 Days)**, **Unique Logins (Last 7 Days)**, and **Currently Active Sessions**.
      * **Login Chart:** A Chart.js line graph visualizes "Logins per Day" over the last 14 days.
      * **Data Tables:** Shows the "Most Active Customers" (by login count) and a list of "Recent Logins" with their IP addresses.

-----

## 🛡️ Security Features

  * **DB-Backed Session Validation:** The system does not trust the browser's cookie alone. On every request, the `customer_session_id` from the cookie is validated against the `ActiveSessions` database table. If it's not present (e.g., due to an admin "kick" or timeout), the user is immediately logged out.
  * **AD Account Lockout Prevention (Honeypot):**
      * To prevent brute-force bot attacks from locking out valuable Active Directory accounts, both the customer and admin login pages contain an invisible "honeypot" field (`hp_email`).
      * This field is hidden from human users via CSS but is visible to bots.
      * The server will **silently reject any login attempt** where this field is filled out, effectively stopping automated attacks without any impact on real users or triggering AD lockout policies.
  * **Forced Password Reset:** Ensures temporary passwords (from creation or admin reset) are never used to access data. The `must_reset_password` flag forces the user into a password-change-only workflow until it's updated.
  * **Secure Password Hashing:** All customer passwords and the local admin password are stored using strong, one-way `scrypt` or `pbkdf2` hashes via `werkzeug.security`.
  * **Strict Read-Only ERP Connection:** The connection to the (assumed) sensitive ERP database is configured to be strictly read-only, preventing any possibility of data modification from the portal.
  * **Email as Username:** Customers log in with their email address, which is less guessable than a username.
  * **Configuration Validation:** The `config.py` file validates all necessary environment variables on startup, preventing the app from running in an insecure or broken state (e.g., missing `SECRET_KEY` or `ADMIN_PASSWORD_HASH`).

-----

## 💻 Technology Stack

  * **Backend:** **Python 3.10+**
      * **Framework:** **Flask** (using Application Factory pattern and Blueprints).
      * **WSGI Server:** **Waitress** (for production deployment).
  * **Database:**
      * **Application DB:** **Microsoft SQL Server** (stores `Customers`, `AuditLog`, `ActiveSessions`, `PasswordResetTokens`).
      * **Data Source:** **Read-Only connection to ERP (Deacom) SQL Server**.
      * **Driver:** **pyodbc** (for all SQL Server connections).
  * **Authentication:**
      * **Active Directory:** **ldap3** (modern, pure-Python library for LDAP communication).
      * **Local Hashing:** **Werkzeug**.
  * **Frontend:**
      * **Templating:** **Jinja2**.
      * **Styling:** **Vanilla CSS3** (a custom, responsive, dark-mode-ready theme).
      * **JavaScript:** **Vanilla JavaScript (ES6+)** (no jQuery or frameworks).
      * **Charting:** **Chart.js** (for the analytics dashboard).
  * **Core Libraries:**
      * **Excel Export:** **openpyxl**.
      * **Email:** **smtplib** & **ssl** (Python standard libraries).
      * **Configuration:** **python-dotenv**.

-----

## 🏗️ Architecture

The application follows a modular, service-oriented structure to separate concerns.

  * **`app.py` (Root):** The main application factory (`create_app`). Initializes Flask, loads config, registers all blueprints, and manages the global `g` context.
  * **`config.py` (Root):** Loads all settings from `.env` into a `Config` class and validates them on import.
  * **`/auth`:**
      * `ad_auth.py`: Manages all Active Directory (LDAP) connections and group validation.
      * `customer_auth.py`: Orchestrates the hybrid admin/customer login logic and provides the `@login_required` / `@admin_required` decorators.
  * **`/database`:**
      * `connection.py`: Manages the read/write connection to the **local Application DB**.
      * `erp_connection_base.py`: Manages the **read-only connection to the ERP DB**. Includes robust logic to try multiple ODBC drivers.
      * `customer_data.py`: Data Access Layer (DAL) for the `Customers` table.
      * `audit_log.py`: DAL for the `AuditLog` table.
      * `session_store.py`: DAL for the `ActiveSessions` table.
      * `analytics_db.py`: A read-only DAL that performs complex queries on other tables (like `AuditLog`) to generate analytics.
      * `erp_service.py`: A **Facade** that acts as the single point of entry for all ERP data requests.
      * `erp_queries/`: Contains the raw SQL and logic specific to querying the ERP (e.g., `inventory_queries.py`).
  * **`/routes`:** Contains the Flask **Blueprints** (controllers).
      * `main.py`: Handles core routes like `/login`, `/logout`, `/admin-login`, and `/force-change-password`. Includes the server-side honeypot check.
      * `inventory.py`: Handles the customer-facing `/inventory` dashboard and the `/api/export-xlsx` endpoint.
      * `/admin/`: All routes for the admin backend, cleanly separated by function (`panel.py`, `customers.py`, `audit.py`, `sessions.py`, `analytics.py`).
  * **`/static`:**
      * `/css`: Contains all CSS files (`base.css`, `admin.css`, `login.css`).
      * `/js`: Contains all client-side JavaScript (`common.js`, `theme.js`, `inventory.js`).
      * `/img`: Contains all logos and favicons.
  * **`/templates`:**
      * `base.html`: The master template with the navbar and theme-switching logic.
      * `login.html` & `admin_login.html`: Login pages, including the **honeypot** field.
      * `inventory_view.html`: The main customer dashboard.
      * `/admin/`: All templates for the admin section.
      * `/email/`: HTML templates for the welcome and password reset emails.
  * **`/utils`:**
      * `email_service.py`: Logic for formatting and sending templated emails via SMTP.
      * `helpers.py`: Common helper functions (e.g., `get_client_info`).
      * `validators.py`: Server-side validation for email/password strength.

-----

## 🗄️ Local Database Schema

The application automatically creates and manages the following tables in the local `CustomerPortalDB`:

  * **`Customers`**: Stores customer login information.
      * `customer_id` (PK)
      * `first_name`, `last_name`, `email` (UNIQUE)
      * `password_hash` (stores the hashed password)
      * `erp_customer_name` (stores the `|` delimited list or "All")
      * `is_active` (BIT)
      * `last_login_date` (DATETIME)
      * `must_reset_password` (BIT, default 1)
  * **`ActiveSessions`**: Stores all currently valid user sessions.
      * `session_id` (PK, the secure token)
      * `customer_id` (FK to Customers)
      * `last_seen` (DATETIME)
      * `ip_address`, `user_agent`, `created_at`
  * **`AuditLog`**: A write-only log of all important actions.
      * `log_id` (PK)
      * `timestamp` (DATETIME)
      * `admin_username` (e.g., 'cp\_admin', 'ad\_user', or 'SYSTEM')
      * `action_type` (e.g., 'CUSTOMER\_CREATE', 'CUSTOMER\_LOGIN')
      * `target_customer_id`, `target_customer_email`
      * `details` (NVARCHAR(MAX), stores text or JSON)
  * **`PasswordResetTokens`**: (Future-Use) A table for a "Forgot Password" self-serve workflow (not yet implemented).

-----

## 🛠️ Installation & Setup

### Prerequisites

  * Python 3.10+
  * Microsoft SQL Server (for the local `CustomerPortalDB`).
  * Read-only access to the target ERP (Deacom) SQL Server database.
  * **ODBC Driver:** The server running the app must have a compatible MS SQL ODBC driver installed (e.g., "ODBC Driver 17 for SQL Server").
  * **Active Directory:** (Optional, but recommended) AD credentials for a service account that can bind and read group memberships.
  * **SMTP Server:** Access to an email server (like Office 365) for sending welcome and password reset emails.

### Installation

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
          * Run this one-time command in your activated virtual environment:
            ```bash
            python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('your_chosen_password', 'scrypt:32768:8:1'))"
            ```
          * Paste the *entire* output (starting with `scrypt:...`) into the `.env` file for `ADMIN_PASSWORD_HASH`.

5.  **Initialize the Database:**

      * Ensure the database specified in `DB_NAME` exists on your `DB_SERVER`.
      * Ensure the user in `DB_USERNAME` has `db_owner` permissions on that database.
      * **The application will automatically create all required tables (`Customers`, `AuditLog`, `ActiveSessions`, etc.) on its first run.**

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

This file is critical for all application functionality.

### General

  * `SECRET_KEY`: A long, random string used for signing session cookies. **Must be changed for production.**
  * `SESSION_HOURS`: How long a user's session lasts before they are required to log in again.
  * `TEST_MODE`: (Optional) Set to `True` to bypass AD authentication for testing.

### Local Application Database (Read/Write)

  * `DB_SERVER`: URL/IP of the SQL Server for the app's *local* database.
  * `DB_NAME`: Name of the database (e.g., `CustomerPortalDB`).
  * `DB_USE_WINDOWS_AUTH`: `True` or `False`.
  * `DB_USERNAME`: SQL user for the local DB.
  * `DB_PASSWORD`: Password for the local DB user.

### ERP (Deacom) Database (Read-Only)

  * `ERP_DB_SERVER`: URL/IP of the read-only ERP database.
  * `ERP_DB_NAME`: Name of the ERP database.
  * `ERP_DB_USERNAME`: Read-only SQL user for the ERP DB.
  * `ERP_DB_PASSWORD`: Password for the ERP DB user.
  * `ERP_DB_PORT`: Port for ERP DB (e.g., `1433`).
  * `ERP_DB_DRIVER`: The *exact name* of the ODBC driver installed on the server (e.g., `ODBC Driver 17 for SQL Server`).
  * `ERP_DB_TIMEOUT`: Connection timeout in seconds (e.g., `30`).

### Email Server (Required)

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