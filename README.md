# Smart Restaurant Management and Ordering System

A centralized web application that connects customers with multiple restaurants in Tiruchirappalli (Trichy), Tamil Nadu.

## Roles

1. **Customer**: Discover restaurants, reserve tables, order food, and track orders.
2. **Restaurant Owner**: Manage their own restaurant (profile, staff, tables, menu, orders).
3. **Restaurant Staff**: Handle operational tasks (tables, reservations, orders) for their assigned restaurant.
4. **Super Admin**: Oversee the entire platform.

## Architecture

- **Backend**: Python + Flask
- **Frontend**: HTML + CSS + JavaScript (Jinja2 Templates)
- **Database**: MySQL 8.0

## Getting Started

1. Set up a Python virtual environment and install requirements:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
2. Create a `.env` file based on `.env.example`.
3. Run the Flask application:
   ```bash
   python app.py
   ```
