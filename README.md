# Smart Restaurant Management and Ordering System

A centralized web application connecting customers with multiple restaurants in **Tiruchirappalli (Trichy), Tamil Nadu**. Built with Flask, SQLAlchemy, MySQL, and modern responsive Bootstrap interfaces.

---

## 📋 Table of Contents

- [Overview & Key Features](#-overview--key-features)
- [User Roles & Permissions](#-user-roles--permissions)
- [Technology Stack](#-technology-stack)
- [Prerequisites & Compatibility](#-prerequisites--compatibility)
- [Project Directory Structure](#-project-directory-structure)
- [Setup & Installation](#-setup--installation)
- [Environment Configuration](#-environment-configuration)
- [Database Setup & Initialization](#-database-setup--initialization)
- [Running the Application](#-running-the-application)
- [Application URLs & Navigation](#-application-urls--navigation)
- [Running the Test Suites](#-running-the-test-suites)
- [Security & Version Control Rules](#-security--version-control-rules)
- [Troubleshooting](#-troubleshooting)

---

## 🍽️ Overview & Key Features

The **Smart Restaurant Management and Ordering System** streamlines table bookings, categorized menu exploration, food ordering, and kitchen workflows across multiple restaurants in Trichy.

### Key Features
- **Multi-Restaurant Discovery**: Filter restaurants by cuisine, veg/non-veg options, and Trichy localities.
- **Table Reservations**: Real-time table booking with party-size capacity checks and time-slot collision validation.
- **Interactive Menu & Cart**: Food browsing with categorized items, formatted currency (₹ Indian Rupees), and session-backed cart management.
- **Order Pipeline & Kitchen Tracking**: Structured order progression (`placed` → `confirmed` → `preparing` → `ready` → `served`).
- **Historical Price Integrity**: Recorded item prices remain immutable on past orders even when menu prices change.
- **Order Modification Lock**: Customers cannot cancel or edit orders once kitchen preparation has begun.
- **Responsive Multi-Viewport UI**: Custom dark-and-gold aesthetic styled with Bootstrap 5.3.3, with responsive table containers (`.table-responsive`) optimized for desktop (1280px), tablet (768px), and mobile (375px).
- **Enterprise Security**: Flask-WTF CSRF protection enabled across all forms, Werkzeug password hashing, role-based access control (RBAC), and SQLAlchemy parameterization against SQL injection.

---

## 👥 User Roles & Permissions

The application implements four distinct roles with strict data isolation:

| Role | Blueprint / Route Prefix | Primary Responsibilities | Data Access Scope |
| :--- | :--- | :--- | :--- |
| **Customer** (`customer`) | `/customer` | Discover restaurants, book tables, order food, track order status. | Private account, personal reservations, and personal orders only. |
| **Restaurant Owner** (`restaurant_owner`) | `/owner` | Manage restaurant profile, tables, menu categories, dishes, staff, view orders and reservations. | Assigned restaurant only. Cannot access other restaurants' data. |
| **Restaurant Staff** (`restaurant_staff`) | `/staff` | Operational tasks: update table status, accept/confirm reservations, update kitchen order progress. | Assigned restaurant operations only. |
| **Super Admin** (`super_admin`) | `/admin` | Platform governance: manage all restaurants, assign owners, register staff (`/admin/staff/create`), monitor platform-wide reservations and orders. | Platform-wide access. |

---

## 🛠️ Technology Stack

- **Backend**: Python (Flask 3.1.x, Flask-Login, Flask-SQLAlchemy 3.1.x, Flask-WTF 1.3.x, Werkzeug)
- **Database**: MySQL 8.0 (PyMySQL driver) via SQLAlchemy ORM 2.0
- **Frontend**: Jinja2 Templates, HTML5, Vanilla JavaScript, Bootstrap 5.3.3
- **Testing**: Python `unittest` (with in-memory SQLite isolation), Playwright for browser E2E workflows

---

## ⚙️ Prerequisites & Compatibility

- **Python**: Version `3.10`, `3.11`, `3.12`, `3.13`, or `3.14` (Verified on Python 3.14.7).
- **MySQL Server**: MySQL 8.0+ Community Server running on `127.0.0.1:3306`.
- **Git**: 2.20+ for source code management.
- **Web Browser**: Google Chrome, Microsoft Edge, or Mozilla Firefox.

---

## 📁 Project Directory Structure

```text
Smart-Restaurant-Management/
├── app/
│   ├── __init__.py           # Application Factory, Blueprint registration & Root route
│   ├── models/               # SQLAlchemy Models
│   │   ├── user.py           # User & password hashing
│   │   ├── restaurant.py     # Restaurant, RestaurantStaff, CustomerRestaurant
│   │   ├── table.py          # Dining tables
│   │   ├── menu.py           # Menu categories & items
│   │   ├── reservation.py    # Table reservations
│   │   └── order.py          # Orders & historical OrderItems
│   ├── routes/               # Flask Blueprints
│   │   ├── auth.py           # Authentication (/auth)
│   │   ├── customer.py       # Customer interface (/customer)
│   │   ├── owner.py          # Restaurant Owner interface (/owner)
│   │   ├── staff.py          # Restaurant Staff interface (/staff)
│   │   ├── admin.py          # Super Admin interface (/admin)
│   │   └── api.py            # JSON API (/api)
│   ├── static/               # CSS, JS, and vendor assets
│   ├── templates/            # Jinja2 HTML templates by role
│   └── utils.py              # RBAC decorators & helper functions
├── tests/                    # Automated Unit & Security Test Suites (165 tests)
├── scratch/                  # Temporary scripts, E2E tests, & audit artifacts (git-ignored)
├── config.py                 # Configuration classes (Development, Production, Testing)
├── app.py                    # Application entry point
├── requirements.txt          # Python package dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules for secrets, DBs, caches
└── README.md                 # Project documentation
```

---

## 🚀 Setup & Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Smart-Restaurant-Management
```

### 2. Create and Activate a Virtual Environment

**Windows (PowerShell / Command Prompt):**
```powershell
python -m venv venv
.\venv\Scripts\activate
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies
```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Configuration

1. Copy the example configuration to create your local `.env`:
   ```bash
   # Windows PowerShell
   Copy-Item .env.example .env

   # Linux / macOS / Bash
   cp .env.example .env
   ```

2. Open `.env` and set your configuration values:

```ini
# Flask
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your_secure_random_secret_key_here

# MySQL Database
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=smart_restaurant_db
DB_USER=smart_restaurant_app
DB_PASSWORD=your_secure_password_here

# Trichy Geographic Center (Default)
TRICHY_LAT=10.7905
TRICHY_LNG=78.7047

# External Integrations (Optional)
GOOGLE_MAPS_API_KEY=your_optional_maps_key
```

> **IMPORTANT**: Never commit the real `.env` file, database passwords, or secret keys to version control.

---

## 🗄️ Database Setup & Initialization

### 1. Create MySQL Database and Application User
Connect to MySQL as `root` (or an administrative user) and run:

```sql
-- Create application database with UTF-8 support
CREATE DATABASE IF NOT EXISTS smart_restaurant_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

-- Create dedicated non-root application user
CREATE USER IF NOT EXISTS 'smart_restaurant_app'@'127.0.0.1' IDENTIFIED BY 'your_secure_password_here';

-- Grant required permissions to the database
GRANT ALL PRIVILEGES ON smart_restaurant_db.* TO 'smart_restaurant_app'@'127.0.0.1';
FLUSH PRIVILEGES;
```

### 2. Initialize Database Tables
To create all database tables defined in the SQLAlchemy models without modifying or deleting existing data:

```bash
python -c "from app import create_app, db; import app.models; app = create_app('development'); app.app_context().push(); db.create_all()"
```

*(Note: `db.create_all()` safely creates any missing tables. It does not drop or overwrite tables that already exist.)*

---

## 💻 Running the Application

### Start the Development Server
```bash
python app.py
```
*Alternatively, using the Flask CLI:*
```bash
flask run --host=127.0.0.1 --port=5000
```

The application will be accessible at: **`http://127.0.0.1:5000`**

---

## 🌐 Application URLs & Navigation

### Homepage Redirect Behavior
- **`http://127.0.0.1:5000/`**:
  - **Anonymous / Unauthenticated**: Automatically redirects to `/auth/login` (HTTP 302).
  - **Authenticated Customer**: Redirects to `/customer/dashboard`.
  - **Authenticated Owner**: Redirects to `/owner/dashboard`.
  - **Authenticated Staff**: Redirects to `/staff/dashboard`.
  - **Authenticated Super Admin**: Redirects to `/admin/dashboard`.

### Key Role Endpoints

| Area | Route | Description |
| :--- | :--- | :--- |
| **Authentication** | `/auth/login` | User login (email & password) |
| | `/auth/register` | Customer self-registration |
| | `/auth/logout` | Session termination (POST/GET) |
| **Customer** | `/customer/restaurants` | Discover Trichy restaurants |
| | `/customer/restaurants/<id>` | Restaurant profile & table booking |
| | `/customer/restaurants/<id>/menu`| Restaurant menu & Add to Cart |
| | `/customer/cart` | View cart, adjust quantities, checkout |
| | `/customer/reservations` | Reservation history |
| | `/customer/orders` | Customer food orders & status |
| **Restaurant Owner** | `/owner/dashboard` | Owner management dashboard |
| | `/owner/restaurant` | View & edit restaurant profile |
| | `/owner/tables` | Manage dining tables |
| | `/owner/menu` | Manage menu categories & items |
| | `/owner/staff` | Assign and manage staff accounts |
| | `/owner/reservations` | Review incoming table bookings |
| | `/owner/orders` | Track and review restaurant orders |
| **Restaurant Staff** | `/staff/dashboard` | Staff operational dashboard |
| | `/staff/tables` | Update table status (available/occupied) |
| | `/staff/reservations` | View and confirm reservations |
| | `/staff/orders` | Update order preparation states |
| **Super Admin** | `/admin/dashboard` | Platform overview & metrics |
| | `/admin/restaurants` | Manage all registered restaurants |
| | `/admin/staff` | View staff registry across all restaurants |
| | `/admin/staff/create` | Register staff for any restaurant |
| | `/admin/tables` | View tables across all restaurants |
| | `/admin/menus` | View menus across all restaurants |
| | `/admin/reservations` | Filter platform reservations |
| | `/admin/orders` | Filter platform orders |
| | `/admin/customers` | Manage registered customers |
| **Health Check** | `/health` | Application status JSON (`{"status": "ok"}`) |

---

## 🧪 Running the Test Suites

All automated tests run against **isolated in-memory or SQLite databases**. The development MySQL database is **never accessed or modified during testing**.

### 1. Full Unit Test Suite (165 Tests)
Runs all unit, regression, RBAC, and boundary tests:
```bash
python -m unittest discover -s tests
```
*Expected Result:* `Ran 165 tests ... OK`

### 2. CSRF Security Protection Suite (8 Tests)
Verifies CSRF enforcement on state-modifying POST routes:
```bash
python -m unittest tests/test_csrf.py
```
*Expected Result:* `Ran 8 tests ... OK`

### 3. Root URL Redirect Suite (6 Tests)
Verifies anonymous login redirection and authenticated role routing:
```bash
python -m unittest tests/test_root_redirect.py
```
*Expected Result:* `Ran 6 tests ... OK`

### 4. End-to-End Customer Ordering Browser Test (Playwright)
Executes a complete customer reservation, menu browsing, cart checkout, and kitchen status transition workflow using an isolated SQLite database on an isolated test server port:
```bash
# Ensure playwright browser binaries are installed
pip install playwright
playwright install chromium

# Run the test
python scratch/e2e_order_test.py
```
*Expected Result:* `10/10 checks PASS` (including historical unit-price lock verification).

---

## 🔒 Security & Version Control Rules

1. **Never Commit Secrets**: The `.env` file containing local credentials, API keys, or secrets is git-ignored. Keep all configuration in `.env` local to your environment.
2. **Never Commit Backups or Synthetic Databases**: SQL dumps (`*.sql`, `*.bak`, `*.dump`) and local SQLite files (`*.db`, `*.sqlite`, `*.sqlite3`) are ignored in `.gitignore`.
3. **Dedicated MySQL User**: Always run the application with a dedicated MySQL user (e.g., `smart_restaurant_app`) with permissions scoped exclusively to `smart_restaurant_db`. Never configure `root` with blank or administrator passwords in production.
4. **CSRF Protection**: All POST/PUT/DELETE forms must include a CSRF token:
   ```html
   <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
   ```
5. **Database Isolation in Tests**: Testing configurations strictly enforce `SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'` or dedicated test SQLite files in `scratch/`.

---

## ❓ Troubleshooting

### 1. `ModuleNotFoundError: No module named 'flask'`
- **Cause**: Virtual environment is not activated or dependencies are missing.
- **Solution**: Activate your virtual environment (`.\venv\Scripts\activate` or `source venv/bin/activate`) and run `pip install -r requirements.txt`.

### 2. `OperationalError: (2003, "Can't connect to MySQL server")`
- **Cause**: MySQL server is stopped or unreachable at `127.0.0.1:3306`.
- **Solution**:
  - Check service status:
    - Windows: `Get-Service MySQL80` (or start via Services MMC / `net start MySQL80`).
    - Linux: `sudo systemctl status mysql`.
  - Verify `DB_HOST`, `DB_PORT`, `DB_USER`, and `DB_PASSWORD` in `.env`.

### 3. `OperationalError: (1045, "Access denied for user ...")`
- **Cause**: Incorrect username or password in `.env`, or missing privileges.
- **Solution**: Check credentials in `.env`. If your password contains special characters (`@`, `#`, etc.), `config.py` automatically encodes it using `urllib.parse.quote_plus`. Ensure the user has been granted privileges on `smart_restaurant_db.*`.

### 4. `HTTP 400 Bad Request — CSRF validation failed`
- **Cause**: A form was submitted without a valid CSRF token, or session cookies expired.
- **Solution**: Ensure your form includes `<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">`. If submitting via Fetch/AJAX, include the `X-CSRFToken` request header.

### 5. `HTTP 403 Forbidden`
- **Cause**: Accessing an endpoint restricted to a different role (e.g., customer attempting `/owner/...` or `/admin/...`).
- **Solution**: Log out and authenticate with the user account possessing the required role (`customer`, `restaurant_owner`, `restaurant_staff`, or `super_admin`).

### 6. `HTTP 404 Not Found` on `/`
- **Cause**: Root index route missing.
- **Solution**: Verified and implemented in `app/__init__.py`. Visiting `/` redirects anonymous visitors to `/auth/login` and authenticated users to their corresponding dashboard.
