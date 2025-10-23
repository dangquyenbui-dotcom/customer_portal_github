# Customer Portal

## 🌟 Overview

The Customer Portal is a web application designed specifically for WePackItAll's customers. It provides a secure and convenient way for customers to view their current inventory levels held at WePackItAll facilities.

* **Customer Inventory View:** A filterable and sortable grid displaying real-time inventory data specific to the logged-in customer.
* **Admin Customer Management:** A separate, secure interface for WePackItAll administrators to manage customer accounts (creation, activation/deactivation, password resets).

The system connects directly to a **read-only ERP database** (Deacom Cloud via `pyodbc`) for live inventory data. Customer account information (credentials, linked ERP name) and potentially session/audit data are stored in a separate, local **SQL Server database** (`CustomerPortalDB`). Customer authentication uses email and password stored locally.

**Status:** Core customer login, inventory view, and admin customer management features are implemented. Password reset via email is planned but not yet implemented.

---

## 🚀 Getting Started

### Prerequisites

* Python 3.10+
* Microsoft SQL Server (for the local `CustomerPortalDB`)
* Read-only access to the target ERP SQL Server database (Deacom Cloud).
* Appropriate **ODBC Drivers** installed on the server running the application (e.g., "ODBC Driver 17 for SQL Server" or similar, as specified in `.env`).

### Installation & Setup

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url>
    cd customer_portal
    ```

2.  **Set Up Environment Variables (`.env`):**
    * Copy the `.env.template` file to a new file named `.env` in the project root.
    * **Update the variables within `.env`** with your specific configuration details:
        * `SECRET_KEY`: Generate a new, strong, random secret key.
        * `DB_SERVER`, `DB_NAME`, `DB_USERNAME`, `DB_PASSWORD` (or `DB_USE_WINDOWS_AUTH`) for the local `CustomerPortalDB`.
        * `ERP_DB_SERVER`, `ERP_DB_NAME`, `ERP_DB_USERNAME`, `ERP_DB_PASSWORD`, `ERP_DB_PORT`, `ERP_DB_DRIVER` for the read-only ERP connection.
        * `SMTP_*`, `EMAIL_FROM` if implementing password reset.
        * `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH` for the portal's admin access. Generate the hash using the provided Python command.

3.  **Create and Activate Virtual Environment:**
    ```bash
    # Navigate to the project root directory
    cd path/to/customer_portal

    # Create the virtual environment (named 'venv')
    python -m venv venv

    # Activate the environment
    # Windows PowerShell:
    .\venv\Scripts\Activate.ps1
    # Windows CMD:
    # .\venv\Scripts\activate.bat
    # macOS/Linux:
    # source venv/bin/activate
    ```

4.  **Install Dependencies:**
    With the virtual environment activated:
    ```bash
    pip install -r requirements.txt
    ```
   

5.  **Database Initialization (`CustomerPortalDB`):**
    * Ensure the `CustomerPortalDB` database and the `CustomerPortalUser` login/user exist on your `DB_SERVER` instance (using the provided SQL scripts or manually).
    * Verify the `CustomerPortalUser` has permissions (`db_datareader`, `db_datawriter`, `db_ddladmin`, `CONNECT`) within that database.
    * The application will attempt to create necessary tables (`Customers`, `PasswordResetTokens`, etc.) on its first run if they don't exist.

6.  **Run the Application (Production):**
    Use a production-ready WSGI server like Waitress (included in requirements). Ensure the virtual environment is active.
    ```bash
    waitress-serve --host=0.0.0.0 --port=5001 --call app:create_app
    ```
    *(Adjust host/port as needed. Ensure the server's firewall allows traffic on the specified port. Port 5001 is suggested to avoid conflict with Production Portal on 5000)*

7.  **Access in Browser:**
    * **Customers:** Navigate to `http://your_server_ip:5001`. They will be redirected to the login page (`/login`).
    * **Admin:** Navigate to `http://your_server_ip:5001/admin-login` to access the admin section.

---

## 🛠️ Core Features

### Customer View

* **Login:** Customers log in using their registered email address and password.
* **Inventory Dashboard (`/inventory`):**
    * Displays a grid of inventory items belonging *only* to the logged-in customer. Data is fetched live from the ERP.
    * Features filtering (by Part, Bin, text search) and sorting capabilities.
    * Allows exporting the currently visible data to an Excel (.xlsx) file.

### Admin View (`/admin`)

* **Login (`/admin-login`):** Separate login for administrators using credentials defined in `.env`.
* **Dashboard (`/admin`):** Central navigation for admin functions.
* **Customer Management (`/admin/customers`):**
    * View list of customers with filtering and search.
    * Add new customer accounts, linking them to their specific ERP Customer Name.
    * Edit customer details (name, email, ERP name) and optionally reset passwords.
    * Activate or deactivate customer accounts.

---

## 💻 Technology Stack

* **Backend**: Python 3, Flask
* **WSGI Server**: Waitress
* **Database ORM/Driver**: `pyodbc` for both local SQL Server and ERP SQL Server connections
* **Frontend**: Jinja2 Templating, HTML, CSS, Vanilla JavaScript
* **Excel Export**: `openpyxl`
* **Environment Variables**: `python-dotenv`
* **Password Hashing:** `Werkzeug`

---

## 🏗️ Architecture

* **Flask Application Factory:** Uses `create_app()` pattern in `app.py`.
* **Blueprints:** Modular structure using Flask Blueprints for different sections (main, inventory, admin).
* **Database Layer:**
    * Separate connection handlers for local `CustomerPortalDB` (`database/connection.py`) and read-only ERP (`database/erp_connection_base.py`).
    * Service layer (`database/erp_service.py`) acts as a facade for ERP queries.
    * Dedicated module (`database/customer_data.py`) for local `Customers` table operations.
* **Authentication:** Handled in the `auth` package, interacting with the local `Customers` table or checking admin credentials. Route protection via decorators (`@login_required`, `@admin_required`).
* **Frontend:** Server-side rendering with Jinja2; client-side interactions via Vanilla JavaScript for filtering, sorting, and exporting.

---

## 📁 Project Structure

````

/customer\_portal/
│
├── app.py                  \# Flask application factory & runner
├── config.py               \# Configuration loader (reads .env)
├── requirements.txt        \# Python dependencies
├── .env                    \# Local environment variables (GITIGNORED)
├── .env.template           \# Template for .env file
├── README.md               \# This file
│
├── /auth/                  \# Authentication & Authorization
│   ├── **init**.py
│   └── customer\_auth.py    \# Customer & Admin login/auth logic, decorators
│
├── /database/              \# Data access layer
│   ├── **init**.py         \# Exports DB instances & service getters
│   ├── connection.py       \# Local DB (CustomerPortalDB) connection
│   ├── erp\_connection\_base.py \# Base ERP DB connection (pyodbc)
│   ├── erp\_service.py      \# Facade for ERP queries
│   ├── customer\_data.py    \# Local Customer & Password Reset DB operations
│   ├── sessions.py         \# (Optional - Reuse from Prod Portal)
│   ├── audit.py            \# (Optional - Reuse from Prod Portal)
│   └── /erp\_queries/       \# Specific SQL queries for ERP
│       ├── **init**.py
│       └── inventory\_queries.py \# Customer-specific inventory query
│
├── /routes/                \# Flask blueprints (controllers)
│   ├── **init**.py
│   ├── main.py             \# Core routes (login, logout, admin-login)
│   ├── inventory.py        \# Customer inventory view routes
│   └── /admin/             \# Admin panel blueprints
│       ├── **init**.py
│       ├── panel.py        \# Admin dashboard route
│       └── customers.py      \# Customer CRUD routes
│
├── /static/                \# Frontend assets (CSS, JS, Images)
│   ├── /css/               \# base.css, admin.css, login.css
│   ├── /js/                \# theme.js, common.js, inventory.js
│   └── /img/               \# Logo images
│
├── /templates/             \# Jinja2 HTML templates
│   ├── base.html
│   ├── login.html
│   ├── admin\_login.html
│   ├── inventory\_view.html
│   ├── /admin/
│   │   ├── panel.html
│   │   └── customer\_management.html
│   └── /components/        \# (Empty for now - Reuse from Prod Portal if needed)
│
└── /utils/                 \# Helper utilities
├── **init**.py
├── helpers.py          \# General utilities (client info, formatting)
└── validators.py       \# Input validation (email, password)

````

---

## ⚙️ Configuration (`.env`)

Key settings managed via the `.env` file:

* `SECRET_KEY`: **Must be set to a unique, random string for security.**
* `SESSION_HOURS`: Duration for user sessions.
* `DB_*`: Connection details for the local `CustomerPortalDB` SQL Server.
* `ERP_*`: Connection details for the read-only ERP SQL Server.
* `SMTP_*`, `EMAIL_FROM`: Required for password reset functionality.
* `ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`: Credentials for the portal administrator.

---

## 🏭 Running for Production

* **WSGI Server:** Use Waitress (or Gunicorn/uWSGI). **Do not use `flask run` or `python app.py` with `debug=True`**.
    ```bash
    waitress-serve --host=0.0.0.0 --port=5001 --call app:create_app
    ```
* **Configuration:** Ensure a strong `SECRET_KEY` is set in `.env`. Verify all DB/ERP settings point to production resources.
* **HTTPS:** Strongly recommended. Set up a reverse proxy (Nginx, Apache, IIS) to handle SSL termination.
* **Logging:** Configure proper file-based logging for monitoring (Flask's built-in logging or a library like `logging`).
* **Virtual Environment:** Always run within the activated project virtual environment.

---

## 📄 License

(Specify your project's license here, e.g., MIT, GPL, Proprietary)

---

## 🙏 Acknowledgements

* Flask
* Waitress
* pyodbc
* Werkzeug
* openpyxl
* python-dotenv

---
````