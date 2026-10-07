# PROJECT PLAN
## Smart Restaurant Management and Ordering System

---

## 1. Project Objective

Build a centralized web application that connects **customers** with multiple
restaurants in **Tiruchirappalli (Trichy), Tamil Nadu**. The system enables:

- **Customers** to discover restaurants, reserve tables, browse menus, place
  food orders, and track order status.
- **Restaurant Owners** to manage their own restaurant — including profile,
  staff, customers, tables, reservations, menu, orders, and reports.
- **Restaurant Staff** to handle operational tasks (tables, reservations,
  orders) within the single restaurant they are assigned to.
- **Super Admin** to oversee the entire platform — managing all restaurants,
  owners, staff, customers, menus, tables, reservations, and orders.

The first version is scoped to Trichy with controlled seed data. The
architecture is designed so that browser Geolocation API and Maps API
integration can be added in future phases without refactoring.

---

## 2. Users / Roles

| Role                   | Description                                                                                                          |
|------------------------|----------------------------------------------------------------------------------------------------------------------|
| **Customer**           | End user who discovers restaurants, reserves tables, orders food, and tracks orders. Can access only their own data. |
| **Restaurant Owner**   | Owns and manages a single restaurant — profile, staff, customers, tables, reservations, menu, orders, and reports. Cannot access any other restaurant's data. |
| **Restaurant Staff**   | Assigned to one restaurant. Handles operational tasks: tables, reservations, and orders. Cannot access any other restaurant's data. |
| **Super Admin**        | Platform administrator with unrestricted access to all restaurants, owners, staff, customers, menus, tables, reservations & orders. |
| **Guest (future)**     | Unauthenticated visitor who can browse restaurants and menus but cannot order or reserve.                             |

### 2.1 Data Isolation Rules

| Rule | Enforcement |
|------|-------------|
| A **Restaurant Owner** must NEVER access another restaurant's data. | Server-side: every query filters by `owner.restaurant_id`. |
| A **Restaurant Staff** member must NEVER access another restaurant's data. | Server-side: every query filters by `staff.restaurant_id`. |
| A **Customer** can access only their own account, reservations, and orders. | Server-side: every query filters by `customer_id = current_user.id`. |
| Only **Super Admin** has cross-restaurant access. | Admin blueprint has no restaurant_id scoping. |

---

## 3. Major Modules

### 3.1 Authentication & Authorization Module
- User registration (Customer, Restaurant Owner)
- Login / Logout
- Four-role RBAC: `customer`, `restaurant_owner`, `restaurant_staff`, `super_admin`
- Session management via Flask sessions
- Restaurant Owner creates Staff accounts for their own restaurant

### 3.2 Location & Discovery Module
- Trichy as the default/hardcoded city (Phase 1)
- Restaurant listing with filters (cuisine, rating, availability)
- Restaurant detail page
- Future: Geolocation API integration, Google Maps embed

### 3.3 Table Reservation Module
- View restaurant tables and layout
- Check table availability by date, time, party size
- Reserve a table
- Cancel / modify reservation
- Owner / Staff: manage tables, mark availability (own restaurant only)

### 3.4 Menu & Cart Module
- Browse restaurant menu (categories, items, prices, images)
- Add items to cart
- Modify cart (quantity, remove)
- Owner: full CRUD on menu items (own restaurant only)
- Staff: toggle item availability (own restaurant only)

### 3.5 Order Management Module
- Place order from cart
- Order confirmation
- Real-time order status tracking (Placed → Preparing → Ready → Served/Delivered)
- Owner: view all orders, assign to staff, update status (own restaurant only)
- Staff: view incoming orders, update status (own restaurant only)
- Order history for customers

### 3.6 Restaurant Owner Module
- Restaurant profile (name, address, cuisine, hours, images) — own restaurant only
- Manage restaurant staff (create, edit, deactivate) — own restaurant only
- View customers who interacted with their restaurant
- Dashboard with daily orders, reservations overview
- Restaurant-level reports (popular items, revenue, peak hours)

### 3.7 Restaurant Staff Module
- Operational dashboard (today's orders, reservations) — own restaurant only
- Manage tables and table availability — own restaurant only
- View and update reservations — own restaurant only
- View incoming orders, update order status — own restaurant only

### 3.8 Super Admin Dashboard Module
- Manage restaurants (approve, suspend, remove) — platform-wide
- Manage restaurant owners — platform-wide
- Manage restaurant staff — platform-wide
- Manage customers — platform-wide
- Manage menus and tables across all restaurants
- Monitor all reservations and orders
- Platform analytics (future)

---

## 4. Development Phases

### Phase 1 — Foundation & Setup
- Initialize Git repository
- Set up Flask project structure (Blueprints)
- Configure MySQL database connection
- Create database schema and seed Trichy restaurant data
- Build base HTML templates (Jinja2) and CSS design system
- **Deliverable:** Running Flask app with DB connection and base layout

### Phase 2 — Authentication & User Management
- User registration (Customer, Restaurant Owner)
- Login / Logout with Flask sessions
- Password hashing (werkzeug or bcrypt)
- Four-role route protection (decorators for customer, owner, staff, super_admin)
- Owner can create Staff accounts scoped to their restaurant
- **Deliverable:** Working auth flow with four roles and data isolation

### Phase 3 — Restaurant Discovery & Location
- Trichy restaurant listing page
- Filters: cuisine type, vegetarian/non-veg, rating
- Restaurant detail page
- Hardcoded Trichy location with architecture hook for Geolocation
- **Deliverable:** Customers can browse and view Trichy restaurants

### Phase 4 — Table Reservation System
- Table entity per restaurant (number, capacity, position)
- Availability calendar (date + time-slot based)
- Customer reservation flow (select date → time → party size → table → confirm)
- Owner table management dashboard (own restaurant only)
- Staff table operational view (own restaurant only)
- **Deliverable:** End-to-end table reservation flow with owner/staff separation

### Phase 5 — Menu, Cart & Ordering
- Menu management (Owner CRUD, own restaurant only)
- Menu browsing (Customer view with categories)
- Shopping cart (session-based)
- Order placement and confirmation
- Order status tracking (Customer + Owner + Staff views, scoped by restaurant)
- **Deliverable:** Complete ordering pipeline with role-based access

### Phase 6 — Owner Dashboard & Super Admin Dashboard
- Owner dashboard: restaurant profile, staff, customers, tables, menu, orders, reports (own restaurant only)
- Super Admin dashboard: platform-wide CRUD for restaurants, owners, staff, customers
- Super Admin reservation and order monitoring (all restaurants)
- Basic analytics (total orders, popular items, per-restaurant breakdown)
- **Deliverable:** Fully functional owner panel and super admin panel

### Phase 7 — Polish & Integration Testing
- UI/UX refinement, responsive design
- Cross-browser testing
- End-to-end integration tests
- Performance optimization
- **Deliverable:** Production-ready application

---

## 5. Testing Phases

| Phase         | Type                  | Description                                                    |
|---------------|-----------------------|----------------------------------------------------------------|
| Unit Testing  | Backend               | Test Flask routes, models, utility functions (pytest)          |
| Unit Testing  | Frontend              | Manual DOM/interaction testing per page                        |
| Integration   | API + DB              | Test full request lifecycle (route → service → DB → response)  |
| System        | End-to-End            | Complete user flows (register → discover → reserve → order)    |
| Security      | Auth & Input          | Test for SQL injection, XSS, CSRF, session hijacking           |
| Performance   | Load                  | Concurrent user simulation on key endpoints                    |
| UAT           | User Acceptance       | Peer review and demo with sample Trichy data                   |

---

## 6. Future Enhancements

| Enhancement                        | Description                                                          |
|------------------------------------|----------------------------------------------------------------------|
| **Geolocation API**                | Auto-detect user city; show nearby restaurants on a map              |
| **Google Maps Integration**        | Embed maps on restaurant detail pages; show directions               |
| **Online Payment Gateway**         | Razorpay / Stripe integration for pre-payment of orders              |
| **Real-time Notifications**        | WebSocket-based live order status updates                            |
| **Rating & Reviews**              | Customers can rate and review restaurants and dishes                   |
| **Multi-city Expansion**          | Extend beyond Trichy to Chennai, Madurai, etc.                        |
| **Mobile-responsive PWA**         | Progressive Web App for near-native mobile experience                 |
| **AI Recommendations**            | Suggest restaurants/dishes based on order history                     |
| **Email/SMS Notifications**       | Order confirmation, reservation reminders                             |
| **Restaurant Analytics Dashboard**| Revenue trends, peak hours, popular dishes for restaurant owners      |
| **Multi-language Support**        | Tamil and English language toggle                                     |

---

> **Status:** Phase 0 — Inspection & Planning ✅  
> **Next Step:** Phase 1 — Foundation & Setup (awaiting approval)
