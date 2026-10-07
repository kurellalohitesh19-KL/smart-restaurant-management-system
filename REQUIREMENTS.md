# REQUIREMENTS
## Smart Restaurant Management and Ordering System

---

## 1. Functional Requirements

### 1.1 Authentication & User Management

| ID      | Requirement                                                                 | Priority |
|---------|-----------------------------------------------------------------------------|----------|
| FR-1.1  | System shall allow new users to register as **Customer**                    | High     |
| FR-1.2  | System shall allow new users to register as **Restaurant Owner**            | High     |
| FR-1.3  | System shall allow **Restaurant Owner** to create **Restaurant Staff** accounts scoped to their own restaurant | High |
| FR-1.4  | System shall authenticate users via username/email and password             | High     |
| FR-1.5  | System shall hash all passwords before storing in database                  | High     |
| FR-1.6  | System shall support four roles: `customer`, `restaurant_owner`, `restaurant_staff`, `super_admin` | High |
| FR-1.7  | System shall restrict access to routes based on user role                   | High     |
| FR-1.8  | System shall allow users to log out and destroy session                     | High     |
| FR-1.9  | System shall allow users to view and update their profile                   | Medium   |
| FR-1.10 | System shall prevent duplicate registrations (same email or username)       | High     |
| FR-1.11 | **Super Admin** account shall be pre-seeded; super admin registration shall not be publicly open | High |

### 1.2 Restaurant Discovery

| ID      | Requirement                                                                 | Priority |
|---------|-----------------------------------------------------------------------------|----------|
| FR-2.1  | System shall display Tiruchirappalli as the current/default location        | High     |
| FR-2.2  | System shall list all active restaurants in Trichy                          | High     |
| FR-2.3  | System shall allow filtering by cuisine type                                | Medium   |
| FR-2.4  | System shall allow filtering by vegetarian / non-vegetarian                 | Medium   |
| FR-2.5  | System shall allow filtering by rating                                      | Low      |
| FR-2.6  | System shall display restaurant cards with name, image, cuisine, rating     | High     |
| FR-2.7  | System shall show a detailed restaurant page (address, hours, description)  | High     |
| FR-2.8  | System shall show restaurant operating hours                                | Medium   |

### 1.3 Table Reservation

| ID      | Requirement                                                                 | Priority |
|---------|-----------------------------------------------------------------------------|----------|
| FR-3.1  | System shall display all tables for a selected restaurant                   | High     |
| FR-3.2  | System shall allow customer to select a reservation date                    | High     |
| FR-3.3  | System shall allow customer to select a reservation time slot               | High     |
| FR-3.4  | System shall allow customer to specify party size (number of people)        | High     |
| FR-3.5  | System shall show only tables matching the party size and available slot    | High     |
| FR-3.6  | System shall allow customer to reserve an available table                   | High     |
| FR-3.7  | System shall prevent double-booking of the same table at the same time     | High     |
| FR-3.8  | System shall allow customer to cancel a reservation                        | Medium   |
| FR-3.9  | System shall allow staff to view all reservations for their restaurant     | High     |
| FR-3.10 | System shall allow staff to manually mark a reservation as completed       | Medium   |

### 1.4 Menu Browsing

| ID      | Requirement                                                                 | Priority |
|---------|-----------------------------------------------------------------------------|----------|
| FR-4.1  | System shall display menu items grouped by category                        | High     |
| FR-4.2  | Each menu item shall show name, description, price, veg/non-veg indicator  | High     |
| FR-4.3  | System shall show item images where available                              | Medium   |
| FR-4.4  | System shall indicate if a menu item is currently unavailable              | Medium   |
| FR-4.5  | System shall show estimated preparation time per item                      | Low      |

### 1.5 Cart & Ordering

| ID      | Requirement                                                                 | Priority |
|---------|-----------------------------------------------------------------------------|----------|
| FR-5.1  | Customer shall be able to add menu items to a cart                          | High     |
| FR-5.2  | Customer shall be able to modify item quantity in the cart                  | High     |
| FR-5.3  | Customer shall be able to remove items from the cart                        | High     |
| FR-5.4  | System shall calculate and display cart total                               | High     |
| FR-5.5  | Customer shall be able to place an order from the cart                      | High     |
| FR-5.6  | System shall generate an order confirmation with order ID                   | High     |
| FR-5.7  | Customer shall be able to add special notes/instructions to the order       | Medium   |
| FR-5.8  | Cart shall be scoped to a single restaurant at a time                       | High     |

### 1.6 Order Tracking

| ID      | Requirement                                                                 | Priority |
|---------|-----------------------------------------------------------------------------|----------|
| FR-6.1  | Customer shall be able to view current order status                         | High     |
| FR-6.2  | Order status shall progress: Placed → Confirmed → Preparing → Ready → Served | High  |
| FR-6.3  | Customer shall see order status update without full page reload (AJAX)      | Medium   |
| FR-6.4  | Customer shall be able to view past order history                           | Medium   |
| FR-6.5  | System shall allow customer to cancel an order only if status is "Placed"   | Medium   |

### 1.7 Restaurant Owner Management (Own Restaurant Only)

| ID      | Requirement                                                                              | Priority |
|---------|------------------------------------------------------------------------------------------|----------|
| FR-7.1  | Owner shall be able to edit their own restaurant's profile                                | High     |
| FR-7.2  | Owner shall be able to create, edit, and deactivate staff accounts for their restaurant   | High     |
| FR-7.3  | Owner shall be able to view customers who interacted with their restaurant                | Medium   |
| FR-7.4  | Owner shall be able to add, edit, and remove tables for their restaurant                  | High     |
| FR-7.5  | Owner shall be able to view and manage reservations for their restaurant                  | High     |
| FR-7.6  | Owner shall be able to add, edit, and remove menu categories for their restaurant         | High     |
| FR-7.7  | Owner shall be able to add, edit, and remove menu items for their restaurant              | High     |
| FR-7.8  | Owner shall be able to toggle menu item availability                                     | High     |
| FR-7.9  | Owner shall receive and view all incoming customer orders for their restaurant            | High     |
| FR-7.10 | Owner shall be able to update order status                                                | High     |
| FR-7.11 | Owner shall see a dashboard with orders, reservations, and revenue for their restaurant   | High     |
| FR-7.12 | Owner shall be able to view restaurant-level reports (popular items, peak hours, revenue)  | Medium   |
| FR-7.13 | Owner shall NEVER access another restaurant's data                                        | High     |

### 1.8 Restaurant Staff Operations (Own Restaurant Only)

| ID      | Requirement                                                                              | Priority |
|---------|------------------------------------------------------------------------------------------|----------|
| FR-8.1  | Staff shall be able to view and update table availability for their assigned restaurant   | High     |
| FR-8.2  | Staff shall be able to view and update reservations for their assigned restaurant         | High     |
| FR-8.3  | Staff shall receive and view incoming customer orders for their assigned restaurant       | High     |
| FR-8.4  | Staff shall be able to update order status                                                | High     |
| FR-8.5  | Staff shall see an operational dashboard with today's orders and reservations             | Medium   |
| FR-8.6  | Staff shall NEVER access another restaurant's data                                        | High     |

### 1.9 Super Admin Management (Platform-Wide)

| ID      | Requirement                                                                              | Priority |
|---------|------------------------------------------------------------------------------------------|----------|
| FR-9.1  | Super Admin shall be able to view, add, edit, and deactivate restaurants                  | High     |
| FR-9.2  | Super Admin shall be able to view, activate, and deactivate restaurant owner accounts     | High     |
| FR-9.3  | Super Admin shall be able to view, activate, and deactivate restaurant staff accounts     | High     |
| FR-9.4  | Super Admin shall be able to view, activate, and deactivate customer accounts             | High     |
| FR-9.5  | Super Admin shall be able to view and manage menus across all restaurants                  | Medium   |
| FR-9.6  | Super Admin shall be able to view and manage tables across all restaurants                 | Medium   |
| FR-9.7  | Super Admin shall be able to monitor all reservations with filters                         | High     |
| FR-9.8  | Super Admin shall be able to monitor all orders with filters                               | High     |
| FR-9.9  | Super Admin dashboard shall show platform-wide statistics                                  | Medium   |

---

## 2. Non-Functional Requirements

| ID       | Category        | Requirement                                                           |
|----------|-----------------|-----------------------------------------------------------------------|
| NFR-1    | Performance     | Pages shall load within 3 seconds on a standard connection            |
| NFR-2    | Performance     | Database queries shall complete within 500ms for standard operations  |
| NFR-3    | Scalability     | Architecture shall support addition of new cities without refactoring |
| NFR-4    | Usability       | UI shall be responsive and functional on desktop and mobile browsers  |
| NFR-5    | Usability       | System shall provide clear error messages for invalid inputs          |
| NFR-6    | Usability       | System shall provide success feedback for completed actions           |
| NFR-7    | Availability    | Application shall handle database connection failures gracefully      |
| NFR-8    | Maintainability | Code shall follow modular architecture (Blueprints, Services)         |
| NFR-9    | Maintainability | Database changes shall be managed through migration scripts           |
| NFR-10   | Compatibility   | Application shall work on Chrome, Firefox, Edge (latest versions)     |
| NFR-11   | Accessibility   | Forms shall have proper labels and semantic HTML                      |
| NFR-12   | Data Integrity  | All foreign key relationships shall be enforced at database level     |
| NFR-13   | Logging         | Application shall log errors and critical operations                  |

---

## 3. Technology Requirements

### 3.1 Mandatory Stack

| Layer       | Technology                  | Version       | Status          |
|-------------|-----------------------------|---------------|-----------------|
| Language    | Python                      | 3.14.7        | ✅ Installed     |
| Backend     | Flask                       | Latest stable | ⬜ To install    |
| Database    | MySQL                       | 8.0.46        | ✅ Running       |
| Frontend    | HTML5 + CSS3 + JavaScript   | ES6+          | ✅ Native        |
| Templating  | Jinja2 (via Flask)          | Built-in      | ⬜ With Flask    |
| VCS         | Git                         | 2.55.0        | ✅ Installed     |
| OS          | Windows 11                  | Build 26200   | ✅ Current       |

### 3.2 Python Packages Required

| Package             | Purpose                              | Install Phase |
|---------------------|--------------------------------------|---------------|
| Flask               | Web framework                        | Phase 1       |
| Flask-SQLAlchemy    | ORM for MySQL                        | Phase 1       |
| Flask-Login         | User session management              | Phase 2       |
| Flask-WTF           | Forms + CSRF protection              | Phase 2       |
| Flask-Migrate       | Database migrations (Alembic)        | Phase 1       |
| PyMySQL             | MySQL database driver for Python     | Phase 1       |
| python-dotenv       | Environment variable management      | Phase 1       |
| Werkzeug            | Password hashing (bundled with Flask)| Phase 2       |
| pytest              | Testing framework                    | Phase 7       |

### 3.3 Prohibited Technologies

The following must **NOT** be used:

- ❌ React, Vue, Angular, Svelte (frontend frameworks)
- ❌ Node.js, Express (backend)
- ❌ Firebase, Supabase (BaaS)
- ❌ MongoDB (NoSQL database)
- ❌ TailwindCSS (CSS framework — unless explicitly requested)

---

## 4. Security Requirements

| ID      | Requirement                                                                       | Priority |
|---------|-----------------------------------------------------------------------------------|----------|
| SEC-1   | All passwords shall be hashed using Werkzeug or bcrypt before storage             | High     |
| SEC-2   | All forms shall include CSRF tokens (Flask-WTF)                                   | High     |
| SEC-3   | All user inputs shall be validated server-side before processing                  | High     |
| SEC-4   | All database queries shall use parameterized queries or ORM (no raw string SQL)   | High     |
| SEC-5   | Jinja2 auto-escaping shall remain enabled to prevent XSS attacks                  | High     |
| SEC-6   | Session cookies shall be set with `HttpOnly` and `SameSite` attributes            | High     |
| SEC-7   | Database credentials shall be stored in `.env` file, not in source code           | High     |
| SEC-8   | `.env` file shall be listed in `.gitignore`                                       | High     |
| SEC-9   | Role-based decorators shall protect all owner, staff, and admin routes            | High     |
| SEC-10  | Failed login attempts shall show generic error messages (no user enumeration)     | Medium   |
| SEC-11  | File uploads (images) shall validate file type and size                           | Medium   |
| SEC-12  | Super Admin account shall be pre-seeded; super admin registration shall not be publicly open | High |
| SEC-13  | Session timeout shall be enforced for inactive sessions                           | Medium   |
| SEC-14  | `SECRET_KEY` shall be a strong random string stored in `.env`                     | High     |
| SEC-15  | Owner routes shall filter ALL queries by `current_user.restaurant_id`             | High     |
| SEC-16  | Staff routes shall filter ALL queries by `current_user.restaurant_id`             | High     |
| SEC-17  | Customer routes shall filter ALL queries by `current_user.id`                     | High     |
| SEC-18  | Cross-restaurant data access shall be impossible for Owner, Staff, and Customer roles | High |

---

## 5. Trichy Location Requirements

### 5.1 Phase 1 — Hardcoded Location (Current Scope)

| ID       | Requirement                                                                    | Priority |
|----------|--------------------------------------------------------------------------------|----------|
| LOC-1    | System shall display "Tiruchirappalli" as the default and only city            | High     |
| LOC-2    | All seed restaurants shall be real/realistic Trichy restaurants                 | High     |
| LOC-3    | Restaurant addresses shall use real Trichy localities and pincodes             | High     |
| LOC-4    | Seed data shall include at least 8–10 restaurants across different Trichy areas | High    |
| LOC-5    | Seed data shall cover diverse cuisines: South Indian, North Indian, Chinese, Multi-cuisine, Biryani | Medium |
| LOC-6    | Database schema shall include `latitude` and `longitude` columns (nullable)    | High     |
| LOC-7    | Database schema shall include `cities` and `areas` tables for future expansion | Medium   |
| LOC-8    | Location detection shall be abstracted into a `LocationService` class          | High     |

### 5.2 Trichy Seed Data Areas

The following Trichy areas/localities shall be represented in seed data:

| Area                  | Pincode   | Notes                                   |
|-----------------------|-----------|-----------------------------------------|
| Srirangam             | 620006    | Temple town, vegetarian restaurants      |
| Thillai Nagar         | 620018    | Commercial hub, diverse dining           |
| Cantonment (Contment) | 620001    | Central area, historic restaurants       |
| Woraiyur              | 620003    | Residential, local eateries              |
| K.K. Nagar            | 620021    | Residential, family restaurants          |
| Tennur                | 620017    | Central, popular food spots              |
| Thiruverumbur         | 620013    | Suburban, growing food scene             |
| Anna Nagar            | 620026    | Residential, biryani joints              |

### 5.3 Phase 2 — Geolocation Integration (Future Scope)

| ID       | Requirement                                                                    | Priority |
|----------|--------------------------------------------------------------------------------|----------|
| LOC-F1   | System shall request browser Geolocation permission                            | Future   |
| LOC-F2   | System shall reverse-geocode coordinates to identify user's city               | Future   |
| LOC-F3   | System shall fall back to manual city selection if geolocation is denied        | Future   |
| LOC-F4   | System shall embed Google Maps on restaurant detail pages                      | Future   |
| LOC-F5   | System shall show restaurant markers on a map view                             | Future   |
| LOC-F6   | System shall sort restaurants by distance from user's coordinates              | Future   |
| LOC-F7   | System shall support adding new cities (Chennai, Madurai, etc.)                | Future   |

---

## 6. Development Environment Checklist

| Item                              | Status | Details                              |
|-----------------------------------|--------|--------------------------------------|
| Operating System                  | ✅     | Windows 11 Home (x64, Build 26200)  |
| Python                            | ✅     | 3.14.7                               |
| pip                               | ✅     | 26.2.1                               |
| Git                               | ✅     | 2.55.0.windows.3                     |
| MySQL Server                      | ✅     | 8.0.46 (service running)             |
| MySQL Client CLI                  | ✅     | Available in PATH                    |
| Git Repository Initialized        | ⬜     | To do in Phase 1                     |
| Python Virtual Environment        | ⬜     | To create in Phase 1                 |
| Flask Installed                   | ⬜     | To install in Phase 1                |
| Database Created                  | ⬜     | To create in Phase 1                 |

---

## 7. Constraints

1. **No frontend frameworks** — all UI is HTML + CSS + JavaScript with Jinja2.
2. **No NoSQL databases** — MySQL only.
3. **No third-party BaaS** — Flask handles all backend logic.
4. **College project scope** — delivered in iterative phases.
5. **Single-city first** — Trichy only in v1; multi-city via architecture expansion.
6. **No payment integration** — v1 assumes dine-in ordering (payment at counter).

---

> **Document Version:** 1.0  
> **Last Updated:** 2026-10-07  
> **Status:** Approved for Phase 1 development
