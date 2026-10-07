# ARCHITECTURE
## Smart Restaurant Management and Ordering System

---

## 1. Roles & Data Access Scope

- **CUSTOMER** → own account, reservations and orders
- **RESTAURANT_OWNER** → only their own restaurant
- **RESTAURANT_STAFF** → only their assigned restaurant
- **SUPER_ADMIN** → entire platform

---

## 2. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT (Browser)                       │
│  ┌───────────┐  ┌───────────┐  ┌──────────────────────┐    │
│  │   HTML    │  │    CSS    │  │     JavaScript       │    │
│  │ (Jinja2) │  │ (Vanilla) │  │ (Vanilla / Fetch API)│    │
│  └───────────┘  └───────────┘  └──────────────────────┘    │
└────────────────────────┬────────────────────────────────────┘
                         │  HTTP Requests
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FLASK APPLICATION SERVER                  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   Flask Blueprints                    │   │
│  │  ┌──────┐ ┌──────────┐ ┌───────┐ ┌───────┐ ┌─────┐  │   │
│  │  │ auth │ │ customer │ │ owner │ │ staff │ │admin│  │   │
│  │  └──────┘ └──────────┘ └───────┘ └───────┘ └─────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              Service / Business Logic Layer           │   │
│  │  ┌──────────────┐ ┌────────────┐ ┌────────────────┐  │   │
│  │  │ AuthService  │ │ OrderSvc   │ │ ReservationSvc │  │   │
│  │  └──────────────┘ └────────────┘ └────────────────┘  │   │
│  │  ┌──────────────┐ ┌────────────┐ ┌────────────────┐  │   │
│  │  │RestaurantSvc │ │  MenuSvc   │ │  LocationSvc   │  │   │
│  │  └──────────────┘ └────────────┘ └────────────────┘  │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │            Data Access Layer (Models / ORM)           │   │
│  │          SQLAlchemy ORM / Raw SQL via PyMySQL         │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │  SQL Queries
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     MySQL 8.0 Database                      │
│                  smart_restaurant_db                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Frontend Architecture

### 2.1 Technology
- **Templating:** Jinja2 (rendered server-side by Flask)
- **Styling:** Vanilla CSS with a custom design system
- **Scripting:** Vanilla JavaScript (ES6+), Fetch API for AJAX calls
- **No frontend frameworks** (no React, Vue, Angular)

### 2.2 Template Hierarchy

```
templates/
├── base.html                     ← Master layout (navbar, footer, flash messages)
├── auth/
│   ├── login.html
│   ├── register.html             ← Customer + Owner registration
│   └── profile.html
├── customer/
│   ├── home.html                 ← Landing page with Trichy location
│   ├── restaurants.html          ← Restaurant listing
│   ├── restaurant_detail.html    ← Single restaurant view
│   ├── tables.html               ← Table availability & reservation
│   ├── menu.html                 ← Restaurant menu browsing
│   ├── cart.html                 ← Shopping cart
│   ├── order_confirm.html        ← Order confirmation
│   ├── order_track.html          ← Order status tracking
│   └── order_history.html        ← Past orders
├── owner/                        ← Restaurant Owner (own restaurant only)
│   ├── dashboard.html            ← Owner overview (orders, reservations, revenue)
│   ├── restaurant_profile.html   ← Edit own restaurant details
│   ├── staff_manage.html         ← Manage own restaurant staff
│   ├── customers.html            ← Customers who interacted with restaurant
│   ├── tables_manage.html        ← Table CRUD (own restaurant)
│   ├── reservations.html         ← Reservation management (own restaurant)
│   ├── menu_manage.html          ← Menu item CRUD (own restaurant)
│   ├── orders.html               ← All orders (own restaurant)
│   ├── order_detail.html         ← Single order + status update
│   └── reports.html              ← Restaurant-level reports
├── staff/                        ← Restaurant Staff (own restaurant only)
│   ├── dashboard.html            ← Staff operational overview
│   ├── tables.html               ← Table availability management
│   ├── reservations.html         ← View/update reservations
│   ├── orders.html               ← Incoming orders
│   └── order_detail.html         ← Single order + status update
└── admin/                        ← Super Admin (platform-wide)
    ├── dashboard.html            ← Platform-wide overview
    ├── restaurants.html          ← Manage all restaurants
    ├── owners.html               ← Manage restaurant owners
    ├── staff.html                ← Manage all staff
    ├── customers.html            ← Manage all customers
    ├── menus.html                ← Menu oversight (all restaurants)
    ├── tables.html               ← Table oversight (all restaurants)
    ├── reservations.html         ← Reservation monitoring (all restaurants)
    └── orders.html               ← Order monitoring (all restaurants)
```

### 2.3 Static Assets Structure

```
static/
├── css/
│   ├── base.css                  ← Design system: variables, reset, typography
│   ├── components.css            ← Reusable component styles (cards, buttons, modals)
│   ├── layout.css                ← Grid, navbar, sidebar, footer
│   ├── auth.css
│   ├── customer.css
│   ├── owner.css
│   ├── staff.css
│   └── admin.css
├── js/
│   ├── main.js                   ← Global utilities, navbar toggle
│   ├── cart.js                   ← Cart interactions (add/remove/update)
│   ├── reservation.js            ← Date/time picker, availability check (AJAX)
│   ├── order_track.js            ← Polling/WebSocket for order status
│   ├── menu_manage.js            ← Staff menu CRUD interactions
│   ├── table_manage.js           ← Staff table CRUD interactions
│   └── location.js               ← Future: Geolocation API + Maps integration
└── img/
    ├── logo/
    ├── restaurants/              ← Restaurant images
    ├── menu_items/               ← Food item images
    └── icons/
```

---

## 3. Flask Backend Architecture

### 3.1 Project Structure

```
smart_restaurant/                 ← Root Python package
├── __init__.py                   ← App factory (create_app)
├── config.py                     ← Configuration classes (Dev, Prod, Test)
├── extensions.py                 ← Initialize extensions (db, login_manager, csrf)
│
├── models/                       ← SQLAlchemy / database models
│   ├── __init__.py
│   ├── user.py                   ← User, Role
│   ├── restaurant.py             ← Restaurant, RestaurantImage
│   ├── table.py                  ← Table, TableAvailability
│   ├── reservation.py            ← Reservation
│   ├── menu.py                   ← MenuCategory, MenuItem
│   ├── order.py                  ← Order, OrderItem
│   └── location.py               ← City, Area (Trichy-first)
│
├── blueprints/                   ← Flask Blueprints (route handlers)
│   ├── __init__.py
│   ├── auth.py                   ← /auth/*  (login, register, logout)
│   ├── customer.py               ← /        (home, restaurants, menu, cart, orders)
│   ├── owner.py                  ← /owner/* (manage own restaurant, staff, menu, orders)
│   ├── staff.py                  ← /staff/* (operational: tables, reservations, orders)
│   ├── admin.py                  ← /admin/* (super admin: platform-wide management)
│   └── api.py                    ← /api/*   (JSON endpoints for AJAX calls)
│
├── services/                     ← Business logic layer
│   ├── __init__.py
│   ├── auth_service.py
│   ├── restaurant_service.py
│   ├── staff_service.py          ← Owner manages staff for own restaurant
│   ├── table_service.py
│   ├── reservation_service.py
│   ├── menu_service.py
│   ├── order_service.py
│   └── location_service.py
│
├── utils/                        ← Utility functions
│   ├── __init__.py
│   ├── decorators.py             ← role_required, login_required wrappers
│   ├── validators.py             ← Input validation helpers
│   └── helpers.py                ← Date/time, formatting utilities
│
├── templates/                    ← Jinja2 templates (see Section 2.2)
├── static/                       ← CSS, JS, images (see Section 2.3)
│
├── seed/                         ← Database seed data
│   ├── trichy_restaurants.json   ← Controlled Trichy restaurant data
│   ├── menu_items.json           ← Sample menu items
│   └── seed_db.py                ← Script to populate the database
│
└── tests/                        ← Test suite
    ├── __init__.py
    ├── conftest.py               ← pytest fixtures
    ├── test_auth.py
    ├── test_restaurant.py
    ├── test_reservation.py
    ├── test_menu.py
    └── test_order.py

run.py                            ← Entry point: python run.py
requirements.txt                  ← pip dependencies
.env                              ← Environment variables (DB creds, secret key)
.gitignore                        ← Ignore __pycache__, .env, venv/, etc.
```

### 3.2 Flask Application Factory Pattern

```python
# smart_restaurant/__init__.py  (conceptual — not implementation code)

def create_app(config_name='development'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register Blueprints (6 total)
    from .blueprints.auth import auth_bp
    from .blueprints.customer import customer_bp
    from .blueprints.owner import owner_bp
    from .blueprints.staff import staff_bp
    from .blueprints.admin import admin_bp
    from .blueprints.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(owner_bp, url_prefix='/owner')
    app.register_blueprint(staff_bp, url_prefix='/staff')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
```

### 3.3 Key Flask Extensions

| Extension             | Purpose                                       |
|-----------------------|-----------------------------------------------|
| Flask-SQLAlchemy      | ORM for MySQL database access                 |
| Flask-Login           | User session management                       |
| Flask-WTF             | Form handling with CSRF protection             |
| PyMySQL / mysqlclient | MySQL database driver                         |
| Flask-Migrate         | Database migrations via Alembic               |
| python-dotenv         | Load `.env` configuration                     |
| Werkzeug              | Password hashing (built into Flask)           |

### 3.4 API Routes Overview

| Blueprint   | Route Pattern                        | Methods     | Description                    | Access Scope       |
|-------------|--------------------------------------|-------------|--------------------------------|--------------------|
| auth        | `/auth/register`                     | GET, POST   | Customer / Owner registration  | Public             |
| auth        | `/auth/login`                        | GET, POST   | User login (all roles)         | Public             |
| auth        | `/auth/logout`                       | GET         | User logout                    | Authenticated      |
| customer    | `/`                                  | GET         | Home / landing page            | Public             |
| customer    | `/restaurants`                       | GET         | Restaurant listing             | Public             |
| customer    | `/restaurants/<id>`                  | GET         | Restaurant detail              | Public             |
| customer    | `/restaurants/<id>/tables`           | GET         | Table availability             | Customer           |
| customer    | `/restaurants/<id>/menu`             | GET         | Restaurant menu                | Public             |
| customer    | `/cart`                              | GET         | View cart                      | Customer           |
| customer    | `/orders`                            | GET         | Order history (own only)       | Customer           |
| customer    | `/orders/<id>`                       | GET         | Order tracking (own only)      | Customer           |
| api         | `/api/tables/availability`           | POST        | Check availability (AJAX)      | Customer           |
| api         | `/api/reservations`                  | POST        | Create reservation (AJAX)      | Customer           |
| api         | `/api/cart/add`                      | POST        | Add item to cart (AJAX)        | Customer           |
| api         | `/api/cart/update`                   | PUT         | Update cart item (AJAX)        | Customer           |
| api         | `/api/cart/remove`                   | DELETE      | Remove cart item (AJAX)        | Customer           |
| api         | `/api/orders`                        | POST        | Place order (AJAX)             | Customer           |
| api         | `/api/orders/<id>/status`            | GET         | Get order status (AJAX)        | Customer           |
| **owner**   | **`/owner/dashboard`**               | **GET**     | **Owner dashboard**            | **Own restaurant** |
| **owner**   | **`/owner/restaurant`**              | **GET, POST** | **Edit restaurant profile**  | **Own restaurant** |
| **owner**   | **`/owner/staff`**                   | **GET, POST** | **Manage restaurant staff**  | **Own restaurant** |
| **owner**   | **`/owner/customers`**               | **GET**     | **View restaurant customers**  | **Own restaurant** |
| **owner**   | **`/owner/tables`**                  | **GET, POST** | **Manage tables**            | **Own restaurant** |
| **owner**   | **`/owner/reservations`**            | **GET**     | **View reservations**          | **Own restaurant** |
| **owner**   | **`/owner/menu`**                    | **GET, POST** | **Manage menu items**        | **Own restaurant** |
| **owner**   | **`/owner/orders`**                  | **GET**     | **View all orders**            | **Own restaurant** |
| **owner**   | **`/owner/orders/<id>`**             | **GET, POST** | **Update order status**      | **Own restaurant** |
| **owner**   | **`/owner/reports`**                 | **GET**     | **Restaurant-level reports**   | **Own restaurant** |
| staff       | `/staff/dashboard`                   | GET         | Staff operational dashboard    | Own restaurant     |
| staff       | `/staff/tables`                      | GET, POST   | Manage table availability      | Own restaurant     |
| staff       | `/staff/reservations`                | GET, POST   | View/update reservations       | Own restaurant     |
| staff       | `/staff/orders`                      | GET         | View incoming orders           | Own restaurant     |
| staff       | `/staff/orders/<id>`                 | GET, POST   | Update order status            | Own restaurant     |
| admin       | `/admin/dashboard`                   | GET         | Super Admin dashboard          | Platform-wide      |
| admin       | `/admin/restaurants`                 | GET, POST   | Manage all restaurants         | Platform-wide      |
| admin       | `/admin/owners`                      | GET, POST   | Manage restaurant owners       | Platform-wide      |
| admin       | `/admin/staff`                       | GET, POST   | Manage all staff               | Platform-wide      |
| admin       | `/admin/customers`                   | GET, POST   | Manage all customers           | Platform-wide      |
| admin       | `/admin/menus`                       | GET         | Manage menus (all restaurants) | Platform-wide      |
| admin       | `/admin/tables`                      | GET         | Manage tables (all restaurants)| Platform-wide      |
| admin       | `/admin/reservations`                | GET         | Monitor all reservations       | Platform-wide      |
| admin       | `/admin/orders`                      | GET         | Monitor all orders             | Platform-wide      |

---

## 4. MySQL Database Architecture

### 4.1 Database Name
`smart_restaurant_db`

### 4.2 Entity Relationship Diagram (Conceptual)

```
┌──────────┐       ┌──────────────┐       ┌───────────────┐
│   User   │──1:N──│  Reservation │──N:1──│   Restaurant  │
│          │       └──────────────┘       │               │
│          │                              │               │
│          │       ┌──────────────┐       │               │
│          │──1:N──│    Order     │──N:1──│               │
│          │       │              │       │               │
└──────────┘       │              │       │               │
                   │              │       └───────┬───────┘
                   └──────┬───────┘               │
                          │                       ├──1:N──┌───────────┐
                   ┌──────┴───────┐               │       │   Table   │
                   │  OrderItem   │               │       └───────────┘
                   │              │               │
                   └──────┬───────┘               ├──1:N──┌────────────────┐
                          │                       │       │ MenuCategory   │
                          N:1                     │       └───────┬────────┘
                          │                       │               │
                   ┌──────┴───────┐               │        ┌──────┴───────┐
                   │   MenuItem   │──N:1──────────┘        │   MenuItem   │
                   └──────────────┘                        └──────────────┘

┌──────────┐       ┌──────────────┐
│   City   │──1:N──│    Area      │
└──────────┘       └──────────────┘
```

### 4.3 Major Database Entities

#### `users`
| Column         | Type                | Description                       |
|----------------|---------------------|-----------------------------------|
| id             | INT, PK, AUTO_INC   | Primary key                       |
| username       | VARCHAR(80), UNIQUE  | Login username                    |
| email          | VARCHAR(120), UNIQUE | Email address                     |
| password_hash  | VARCHAR(256)         | Bcrypt/werkzeug hashed password   |
| full_name      | VARCHAR(150)         | Display name                      |
| phone          | VARCHAR(15)          | Phone number                      |
| role           | ENUM('customer','restaurant_owner','restaurant_staff','super_admin') | User role |
| restaurant_id  | INT, FK, NULL        | Owner/Staff linked to restaurant (NULL for customer/admin) |
| is_active      | BOOLEAN, DEFAULT 1   | Account active status             |
| created_at     | DATETIME             | Registration timestamp            |
| updated_at     | DATETIME             | Last update timestamp             |

#### `restaurants`
| Column         | Type                | Description                       |
|----------------|---------------------|-----------------------------------|
| id             | INT, PK, AUTO_INC   | Primary key                       |
| owner_id       | INT, FK              | Owner user ID (role=restaurant_owner) |
| name           | VARCHAR(200)         | Restaurant name                   |
| description    | TEXT                 | About the restaurant              |
| address        | VARCHAR(300)         | Full street address               |
| area           | VARCHAR(100)         | Locality within Trichy            |
| city           | VARCHAR(100)         | City (default: Tiruchirappalli)   |
| state          | VARCHAR(100)         | State (default: Tamil Nadu)       |
| pincode        | VARCHAR(10)          | Postal code                       |
| latitude       | DECIMAL(10,8), NULL  | GPS latitude (future)             |
| longitude      | DECIMAL(11,8), NULL  | GPS longitude (future)            |
| phone          | VARCHAR(15)          | Contact phone                     |
| email          | VARCHAR(120)         | Contact email                     |
| cuisine_type   | VARCHAR(200)         | e.g., "South Indian, Chinese"     |
| is_veg         | BOOLEAN              | Pure vegetarian flag              |
| rating         | DECIMAL(2,1)         | Average rating (0.0 - 5.0)        |
| opening_time   | TIME                 | Daily opening time                |
| closing_time   | TIME                 | Daily closing time                |
| image_url      | VARCHAR(500)         | Main restaurant image             |
| is_active      | BOOLEAN, DEFAULT 1   | Restaurant active on platform     |
| created_at     | DATETIME             | Created timestamp                 |
| updated_at     | DATETIME             | Last update timestamp             |

#### `tables`
| Column         | Type                | Description                       |
|----------------|---------------------|-----------------------------------|
| id             | INT, PK, AUTO_INC   | Primary key                       |
| restaurant_id  | INT, FK              | Belongs to restaurant             |
| table_number   | VARCHAR(10)          | Display number (e.g., "T1")       |
| capacity       | INT                  | Max seats                         |
| location       | ENUM('indoor','outdoor','balcony') | Table location     |
| is_active      | BOOLEAN, DEFAULT 1   | Table in service                  |

#### `reservations`
| Column           | Type                | Description                     |
|------------------|---------------------|---------------------------------|
| id               | INT, PK, AUTO_INC   | Primary key                     |
| customer_id      | INT, FK              | Customer user ID                |
| restaurant_id    | INT, FK              | Restaurant ID                   |
| table_id         | INT, FK              | Reserved table ID               |
| reservation_date | DATE                 | Date of reservation             |
| start_time       | TIME                 | Reservation start time          |
| end_time         | TIME                 | Reservation end time            |
| party_size       | INT                  | Number of guests                |
| status           | ENUM('pending','confirmed','cancelled','completed') | Status |
| special_requests | TEXT, NULL           | Customer notes                  |
| created_at       | DATETIME             | Booking timestamp               |

#### `menu_categories`
| Column         | Type                | Description                       |
|----------------|---------------------|-----------------------------------|
| id             | INT, PK, AUTO_INC   | Primary key                       |
| restaurant_id  | INT, FK              | Belongs to restaurant             |
| name           | VARCHAR(100)         | e.g., "Starters", "Main Course"   |
| display_order  | INT                  | Sorting order                     |

#### `menu_items`
| Column         | Type                | Description                       |
|----------------|---------------------|-----------------------------------|
| id             | INT, PK, AUTO_INC   | Primary key                       |
| category_id    | INT, FK              | Belongs to menu category          |
| restaurant_id  | INT, FK              | Belongs to restaurant             |
| name           | VARCHAR(200)         | Item name                         |
| description    | TEXT                 | Item description                  |
| price          | DECIMAL(8,2)         | Price in INR                      |
| image_url      | VARCHAR(500)         | Item image                        |
| is_veg         | BOOLEAN              | Vegetarian flag                   |
| is_available   | BOOLEAN, DEFAULT 1   | Currently available               |
| preparation_time | INT                | Estimated minutes                 |

#### `orders`
| Column         | Type                | Description                       |
|----------------|---------------------|-----------------------------------|
| id             | INT, PK, AUTO_INC   | Primary key                       |
| customer_id    | INT, FK              | Customer user ID                  |
| restaurant_id  | INT, FK              | Restaurant ID                     |
| reservation_id | INT, FK, NULL        | Linked reservation (optional)     |
| status         | ENUM('placed','confirmed','preparing','ready','served','cancelled') | Order status |
| total_amount   | DECIMAL(10,2)        | Total order amount                |
| special_notes  | TEXT, NULL           | Customer notes                    |
| placed_at      | DATETIME             | Order placed timestamp            |
| updated_at     | DATETIME             | Last status update                |

#### `order_items`
| Column         | Type                | Description                       |
|----------------|---------------------|-----------------------------------|
| id             | INT, PK, AUTO_INC   | Primary key                       |
| order_id       | INT, FK              | Belongs to order                  |
| menu_item_id   | INT, FK              | References menu item              |
| quantity       | INT                  | Item quantity                     |
| unit_price     | DECIMAL(8,2)         | Price at time of order            |
| subtotal       | DECIMAL(10,2)        | quantity × unit_price             |

#### `cities` (Location — Future Expansion)
| Column         | Type                | Description                       |
|----------------|---------------------|-----------------------------------|
| id             | INT, PK, AUTO_INC   | Primary key                       |
| name           | VARCHAR(100)         | City name                         |
| state          | VARCHAR(100)         | State name                        |
| is_active      | BOOLEAN, DEFAULT 1   | City supported on platform        |

#### `areas`
| Column         | Type                | Description                       |
|----------------|---------------------|-----------------------------------|
| id             | INT, PK, AUTO_INC   | Primary key                       |
| city_id        | INT, FK              | Belongs to city                   |
| name           | VARCHAR(100)         | Area / locality name              |
| pincode        | VARCHAR(10)          | Postal code                       |

---

## 5. User Flow Diagrams

### 5.1 Customer Flow

```
Landing Page (Trichy selected)
    │
    ▼
Browse Restaurants ──► Filter (cuisine, veg, rating)
    │
    ▼
Restaurant Detail Page
    │
    ├──► View Tables ──► Select Date/Time/Party Size
    │         │
    │         ▼
    │    Check Availability ──► Reserve Table ──► Confirmation
    │
    ├──► View Menu ──► Add to Cart
    │                      │
    │                      ▼
    │                  View Cart ──► Modify Items
    │                      │
    │                      ▼
    │                 Place Order ──► Order Confirmation
    │                      │
    │                      ▼
    │                Track Order Status (Placed → Preparing → Ready → Served)
    │
    └──► Order History
```

### 5.2 Restaurant Owner Flow (Own Restaurant Only)

```
Owner Login
    │
    ▼
Owner Dashboard (Revenue, Orders, Reservations — own restaurant only)
    │
    ├──► Manage Restaurant Profile (edit name, hours, images)
    │
    ├──► Manage Restaurant Staff
    │       ├── Create Staff Account (auto-linked to own restaurant)
    │       ├── Edit Staff Details
    │       ├── Activate / Deactivate Staff
    │       └── View Staff Activity
    │
    ├──► View Restaurant Customers
    │       └── Customers who reserved/ordered at own restaurant
    │
    ├──► Manage Tables (add/edit/remove tables, set capacity)
    │
    ├──► Manage Reservations
    │       ├── View All Reservations (own restaurant)
    │       ├── Confirm / Cancel Reservations
    │       └── Mark as Completed
    │
    ├──► Manage Menu
    │       ├── Add / Edit / Remove Categories
    │       ├── Add / Edit / Remove Menu Items
    │       └── Toggle Item Availability
    │
    ├──► Manage Orders
    │       ├── View All Orders (own restaurant)
    │       ├── Accept / Reject Order
    │       └── Update Status (Confirmed → Preparing → Ready → Served)
    │
    └──► Restaurant Reports
            ├── Popular Items
            ├── Revenue Summary
            └── Peak Hours
```

> ⚠️ **Data Isolation:** Every query in the Owner blueprint is filtered by
> `WHERE restaurant_id = current_user.restaurant_id`. An owner can NEVER
> see or modify another restaurant's data.

### 5.3 Restaurant Staff Flow (Own Restaurant Only)

```
Staff Login
    │
    ▼
Staff Dashboard (Today's Orders, Reservations — own restaurant only)
    │
    ├──► Manage Tables
    │       ├── View Tables (own restaurant)
    │       └── Update Table Availability
    │
    ├──► Manage Reservations
    │       ├── View Reservations (own restaurant)
    │       └── Update Reservation Status
    │
    └──► Manage Orders
            ├── View Incoming Orders (own restaurant)
            └── Update Status (Confirmed → Preparing → Ready → Served)
```

> ⚠️ **Data Isolation:** Every query in the Staff blueprint is filtered by
> `WHERE restaurant_id = current_user.restaurant_id`. A staff member can
> NEVER see or modify another restaurant's data.

### 5.4 Super Admin Flow (Platform-Wide)

```
Super Admin Login
    │
    ▼
Super Admin Dashboard (Platform Stats, Recent Activity — all restaurants)
    │
    ├──► Manage Restaurants
    │       ├── View All Restaurants
    │       ├── Approve / Suspend / Remove
    │       └── View Restaurant Details
    │
    ├──► Manage Restaurant Owners
    │       ├── View All Owners
    │       ├── Activate / Deactivate Accounts
    │       └── View Owner's Restaurant
    │
    ├──► Manage Restaurant Staff
    │       ├── View All Staff (across all restaurants)
    │       ├── Activate / Deactivate Accounts
    │       └── Reassign Staff to Restaurants
    │
    ├──► Manage Customers
    │       ├── View All Customers
    │       └── Activate / Deactivate Accounts
    │
    ├──► Manage Menus (cross-restaurant oversight)
    │
    ├──► Manage Tables (cross-restaurant oversight)
    │
    ├──► Monitor Reservations
    │       ├── View All Reservations (all restaurants)
    │       ├── Filter by Date / Restaurant / Status
    │       └── Cancel Reservations (if needed)
    │
    └──► Monitor Orders
            ├── View All Orders (all restaurants)
            ├── Filter by Date / Restaurant / Status
            └── View Order Details
```

---

## 6. Future Location API Architecture

### Phase 1 (Current): Hardcoded Trichy

```python
# services/location_service.py

class LocationService:
    DEFAULT_CITY = "Tiruchirappalli"
    DEFAULT_STATE = "Tamil Nadu"

    @staticmethod
    def get_current_city():
        """Phase 1: Return hardcoded Trichy. Phase 2: Use geolocation."""
        return {
            "city": LocationService.DEFAULT_CITY,
            "state": LocationService.DEFAULT_STATE,
            "latitude": 10.7905,
            "longitude": 78.7047
        }

    @staticmethod
    def get_restaurants_by_city(city_name):
        """Fetch restaurants filtered by city."""
        # Query restaurants table WHERE city = city_name
        pass
```

### Phase 2 (Future): Browser Geolocation + Maps API

```
┌──────────────────────────────────────┐
│           Browser (Client)           │
│                                      │
│  navigator.geolocation.getCurrentPosition()
│         │                            │
│         ▼                            │
│  Lat/Lng obtained ──► Send to Flask  │
│         │                            │
│  Google Maps JS API                  │
│    - Render map                      │
│    - Show restaurant markers         │
│    - Directions to restaurant        │
└──────────┬───────────────────────────┘
           │  POST /api/location/detect
           ▼
┌──────────────────────────────────────┐
│         Flask Backend                │
│                                      │
│  Reverse geocode (Google Maps API)   │
│  Determine city from coordinates     │
│  Return restaurants near lat/lng     │
│                                      │
│  GET /api/restaurants?lat=X&lng=Y    │
│  → Sort by distance, return list     │
└──────────────────────────────────────┘
```

### Architecture Hooks Already in Place
- `restaurants` table has `latitude` and `longitude` columns (nullable)
- `cities` and `areas` tables for multi-city expansion
- `LocationService` class abstracts city detection (easy to swap implementation)
- `static/js/location.js` reserved for Geolocation API integration

---

## 7. Security Architecture

```
┌─────────────────────────────────────────────┐
│            Security Layers                   │
│                                              │
│  1. CSRF Protection      (Flask-WTF)        │
│  2. Password Hashing     (Werkzeug/bcrypt)  │
│  3. Session Management   (Flask-Login)       │
│  4. Role-Based Access    (Custom decorators) │
│  5. Restaurant Scoping   (owner/staff → own  │
│                           restaurant only)    │
│  6. Input Validation     (WTForms + custom)  │
│  7. SQL Injection Guard  (SQLAlchemy ORM)    │
│  8. XSS Prevention       (Jinja2 autoscape) │
│  9. Environment Secrets  (.env file)         │
└─────────────────────────────────────────────┘
```

---

## 8. Deployment Architecture (Future)

```
                     ┌───────────────────┐
                     │   Nginx (Proxy)   │
                     └─────────┬─────────┘
                               │
                     ┌─────────▼─────────┐
                     │   Gunicorn WSGI   │
                     │   (Flask App)     │
                     └─────────┬─────────┘
                               │
                     ┌─────────▼─────────┐
                     │   MySQL 8.0       │
                     └───────────────────┘
```

- **Development:** `flask run` (debug mode)
- **Production:** Gunicorn behind Nginx reverse proxy
- **Database:** MySQL 8.0 (same host or separate DB server)

---

> **This document defines the target architecture. No implementation code has
> been written yet. Development begins at Phase 1 upon approval.**
