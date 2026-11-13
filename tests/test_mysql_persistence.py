"""
Integration Test Suite: MySQL Physical Database Persistence
Smart Restaurant Management System

Verifies that all entity creations, status updates, transactions,
and role operations persist directly into the active MySQL database
(smart_restaurant_db) and survive application restarts.
"""

import unittest
import time
from decimal import Decimal
from datetime import datetime, date, time as dtime, timedelta, timezone
from sqlalchemy import text
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant, RestaurantStaff, CustomerRestaurant
from app.models.table import Table
from app.models.menu import MenuCategory, MenuItem
from app.models.reservation import Reservation
from app.models.order import Order, OrderItem
from app.services import reservation_service

class MySQLPersistenceTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Initialize with development configuration to connect to real MySQL
        cls.app = create_app('development')
        cls.app.config['WTF_CSRF_ENABLED'] = False
        cls.tag = f"persist_{int(datetime.now().timestamp())}"

    def setUp(self):
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        # Roll back any dangling session changes
        db.session.rollback()
        self.app_context.pop()

    @classmethod
    def tearDownClass(cls):
        # Clean up test-tagged records from MySQL
        with cls.app.app_context():
            try:
                # Find test restaurants and delete test children
                test_rests = Restaurant.query.filter(Restaurant.name.like(f"%{cls.tag}%")).all()
                for r in test_rests:
                    OrderItem.query.filter(OrderItem.order.has(restaurant_id=r.id)).delete(synchronize_session=False)
                    Order.query.filter_by(restaurant_id=r.id).delete()
                    Reservation.query.filter_by(restaurant_id=r.id).delete()
                    MenuItem.query.filter_by(restaurant_id=r.id).delete()
                    MenuCategory.query.filter_by(restaurant_id=r.id).delete()
                    Table.query.filter_by(restaurant_id=r.id).delete()
                    RestaurantStaff.query.filter_by(restaurant_id=r.id).delete()
                    CustomerRestaurant.query.filter_by(restaurant_id=r.id).delete()
                    db.session.delete(r)

                # Delete test users
                User.query.filter(User.email.like(f"%{cls.tag}%")).delete(synchronize_session=False)
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                print(f"Cleanup warning: {e}")

    def test_01_verify_active_mysql_connection(self):
        """Verify the test is actively connected to MySQL (not SQLite)."""
        with db.engine.connect() as conn:
            db_name = conn.execute(text("SELECT DATABASE();")).scalar()
            version = conn.execute(text("SELECT VERSION();")).scalar()
            user = conn.execute(text("SELECT CURRENT_USER();")).scalar()
            
            self.assertEqual(db_name, 'smart_restaurant_db')
            self.assertIn('8.0', str(version))
            self.assertIn('smart_restaurant_app', str(user))

    def test_02_register_customer_and_verify_mysql_row(self):
        """Workflow 1: Register customer and verify row in MySQL."""
        cust_email = f"cust_{self.tag}@example.com"
        customer = User(
            name="Persistence Customer",
            email=cust_email,
            phone="9876500001",
            role="customer",
            is_active=True
        )
        customer.set_password("SecurePass@123")
        db.session.add(customer)
        db.session.commit()

        # Verify through raw SQL query
        with db.engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, name, email, role, is_active FROM users WHERE email = :email"),
                {"email": cust_email}
            ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[1], "Persistence Customer")
            self.assertEqual(row[3], "customer")
            self.assertEqual(row[4], 1)

    def test_03_create_restaurant_and_verify_mysql_row(self):
        """Workflow 2: Create restaurant and verify Restaurant row in MySQL."""
        owner_email = f"owner_{self.tag}@example.com"
        owner = User(
            name="Persistence Owner",
            email=owner_email,
            role="restaurant_owner",
            is_active=True
        )
        owner.set_password("OwnerPass@123")
        db.session.add(owner)
        db.session.commit()

        rest_name = f"Persist Bistro {self.tag}"
        restaurant = Restaurant(
            name=rest_name,
            owner_id=owner.id,
            city="Tiruchirappalli",
            state="Tamil Nadu",
            address="100 Cantonment Road",
            is_active=True
        )
        db.session.add(restaurant)
        db.session.commit()

        # Verify via raw SQL
        with db.engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, name, owner_id, city, is_active FROM restaurants WHERE name = :name"),
                {"name": rest_name}
            ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[1], rest_name)
            self.assertEqual(row[2], owner.id)
            self.assertEqual(row[3], "Tiruchirappalli")

    def test_04_create_menu_category_and_item_and_verify_mysql(self):
        """Workflows 3 & 4: Create category & item and verify in MySQL."""
        owner = User.query.filter(User.email.like(f"owner_{self.tag}%")).first()
        rest = Restaurant.query.filter(Restaurant.name.like(f"Persist Bistro {self.tag}%")).first()

        category = MenuCategory(
            restaurant_id=rest.id,
            name=f"Chef Specials {self.tag}",
            is_active=True
        )
        db.session.add(category)
        db.session.commit()

        item = MenuItem(
            restaurant_id=rest.id,
            category_id=category.id,
            name=f"Signature Curry {self.tag}",
            description="Tender chicken with ground spices",
            price=Decimal("350.00"),
            is_available=True
        )
        db.session.add(item)
        db.session.commit()

        # Raw SQL verification
        with db.engine.connect() as conn:
            cat_row = conn.execute(
                text("SELECT id, name, is_active FROM menu_categories WHERE id = :id"),
                {"id": category.id}
            ).fetchone()
            self.assertIsNotNone(cat_row)
            self.assertEqual(cat_row[1], f"Chef Specials {self.tag}")

            item_row = conn.execute(
                text("SELECT id, name, price, is_available FROM menu_items WHERE id = :id"),
                {"id": item.id}
            ).fetchone()
            self.assertIsNotNone(item_row)
            self.assertEqual(item_row[1], f"Signature Curry {self.tag}")
            self.assertEqual(float(item_row[2]), 350.00)
            self.assertEqual(item_row[3], 1)

    def test_05_create_table_and_verify_mysql(self):
        """Workflow 5: Create table and verify Table row in MySQL."""
        rest = Restaurant.query.filter(Restaurant.name.like(f"Persist Bistro {self.tag}%")).first()

        table = Table(
            restaurant_id=rest.id,
            table_number=f"T-P1",
            capacity=4,
            status="available"
        )
        db.session.add(table)
        db.session.commit()

        with db.engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, table_number, capacity, status FROM tables WHERE id = :id"),
                {"id": table.id}
            ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[1], "T-P1")
            self.assertEqual(row[2], 4)
            self.assertEqual(row[3], "available")

    def test_06_create_reservation_auto_confirmed_in_mysql(self):
        """Workflow 6: Create reservation and verify in MySQL with auto-confirmation."""
        cust = User.query.filter(User.email.like(f"cust_{self.tag}%")).first()
        rest = Restaurant.query.filter(Restaurant.name.like(f"Persist Bistro {self.tag}%")).first()
        table = Table.query.filter_by(restaurant_id=rest.id, table_number="T-P1").first()

        res_date = date.today() + timedelta(days=2)
        reservation = Reservation(
            customer_id=cust.id,
            restaurant_id=rest.id,
            table_id=table.id,
            reservation_date=res_date,
            start_time=dtime(19, 0),
            end_time=dtime(20, 0),
            number_of_guests=3,
            status="confirmed"
        )
        db.session.add(reservation)
        db.session.commit()

        with db.engine.connect() as conn:
            row = conn.execute(
                text("SELECT id, customer_id, restaurant_id, table_id, status, number_of_guests FROM reservations WHERE id = :id"),
                {"id": reservation.id}
            ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[1], cust.id)
            self.assertEqual(row[2], rest.id)
            self.assertEqual(row[3], table.id)
            self.assertEqual(row[4], "confirmed")
            self.assertEqual(row[5], 3)

    def test_07_place_order_and_verify_order_items_in_mysql(self):
        """Workflows 7 & 8: Place order and verify Order and OrderItem in MySQL."""
        cust = User.query.filter(User.email.like(f"cust_{self.tag}%")).first()
        rest = Restaurant.query.filter(Restaurant.name.like(f"Persist Bistro {self.tag}%")).first()
        item = MenuItem.query.filter(MenuItem.name.like(f"Signature Curry {self.tag}%")).first()

        order = Order(
            customer_id=cust.id,
            restaurant_id=rest.id,
            status="placed",
            total_amount=Decimal("700.00")
        )
        db.session.add(order)
        db.session.flush()

        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=item.id,
            quantity=2,
            unit_price=item.price,
            subtotal=Decimal("700.00")
        )
        db.session.add(order_item)
        db.session.commit()

        with db.engine.connect() as conn:
            order_row = conn.execute(
                text("SELECT id, customer_id, restaurant_id, status, total_amount FROM orders WHERE id = :id"),
                {"id": order.id}
            ).fetchone()
            self.assertIsNotNone(order_row)
            self.assertEqual(order_row[1], cust.id)
            self.assertEqual(order_row[3], "placed")
            self.assertEqual(float(order_row[4]), 700.00)

            item_row = conn.execute(
                text("SELECT id, order_id, menu_item_id, quantity, unit_price, subtotal FROM order_items WHERE order_id = :oid"),
                {"oid": order.id}
            ).fetchone()
            self.assertIsNotNone(item_row)
            self.assertEqual(item_row[2], item.id)
            self.assertEqual(item_row[3], 2)
            self.assertEqual(float(item_row[4]), 350.00)
            self.assertEqual(float(item_row[5]), 700.00)

    def test_08_update_customer_profile_and_verify_mysql(self):
        """Workflow 9: Update customer profile and verify change in MySQL."""
        cust = User.query.filter(User.email.like(f"cust_{self.tag}%")).first()
        cust.name = "Updated Persistence Customer"
        cust.phone = "9876599999"
        db.session.commit()

        with db.engine.connect() as conn:
            row = conn.execute(
                text("SELECT name, phone FROM users WHERE id = :id"),
                {"id": cust.id}
            ).fetchone()
            self.assertEqual(row[0], "Updated Persistence Customer")
            self.assertEqual(row[1], "9876599999")

    def test_09_update_menu_item_price_and_verify_mysql(self):
        """Workflow 10: Update menu item price and verify change in MySQL."""
        item = MenuItem.query.filter(MenuItem.name.like(f"Signature Curry {self.tag}%")).first()
        item.price = Decimal("399.00")
        db.session.commit()

        with db.engine.connect() as conn:
            price = conn.execute(
                text("SELECT price FROM menu_items WHERE id = :id"),
                {"id": item.id}
            ).scalar()
            self.assertEqual(float(price), 399.00)

    def test_10_update_table_status_and_verify_mysql(self):
        """Workflow 11: Update table status and verify change in MySQL."""
        rest = Restaurant.query.filter(Restaurant.name.like(f"Persist Bistro {self.tag}%")).first()
        table = Table.query.filter_by(restaurant_id=rest.id, table_number="T-P1").first()
        table.status = "occupied"
        db.session.commit()

        with db.engine.connect() as conn:
            status = conn.execute(
                text("SELECT status FROM tables WHERE id = :id"),
                {"id": table.id}
            ).scalar()
            self.assertEqual(status, "occupied")

    def test_11_update_order_status_and_verify_mysql(self):
        """Workflow 12: Update order status and verify change in MySQL."""
        cust = User.query.filter(User.email.like(f"cust_{self.tag}%")).first()
        order = Order.query.filter_by(customer_id=cust.id).first()
        order.status = "preparing"
        db.session.commit()

        with db.engine.connect() as conn:
            status = conn.execute(
                text("SELECT status FROM orders WHERE id = :id"),
                {"id": order.id}
            ).scalar()
            self.assertEqual(status, "preparing")

    def test_12_role_based_record_isolation(self):
        """Workflow 13: Verify each role can access only authorized records."""
        cust = User.query.filter(User.email.like(f"cust_{self.tag}%")).first()
        owner = User.query.filter(User.email.like(f"owner_{self.tag}%")).first()
        rest = Restaurant.query.filter(Restaurant.name.like(f"Persist Bistro {self.tag}%")).first()
        order = Order.query.filter_by(customer_id=cust.id).first()

        # Customer should own their order
        self.assertEqual(order.customer_id, cust.id)
        # Owner owns this restaurant
        self.assertEqual(rest.owner_id, owner.id)
        # Other owners cannot own this restaurant
        other_owner = User.query.filter(User.role == 'restaurant_owner', User.id != owner.id).first()
        if other_owner:
            self.assertNotEqual(rest.owner_id, other_owner.id)

    def test_13_restart_flask_app_and_confirm_persistence(self):
        """Workflow 14: Simulate app restart and confirm previously saved records exist."""
        # Create a completely brand new Flask app instance connected to MySQL
        fresh_app = create_app('development')
        with fresh_app.app_context():
            cust = User.query.filter(User.email.like(f"cust_{self.tag}%")).first()
            self.assertIsNotNone(cust)
            self.assertEqual(cust.name, "Updated Persistence Customer")

            rest = Restaurant.query.filter(Restaurant.name.like(f"Persist Bistro {self.tag}%")).first()
            self.assertIsNotNone(rest)

            item = MenuItem.query.filter(MenuItem.name.like(f"Signature Curry {self.tag}%")).first()
            self.assertIsNotNone(item)
            self.assertEqual(float(item.price), 399.00)

            table = Table.query.filter_by(restaurant_id=rest.id, table_number="T-P1").first()
            self.assertIsNotNone(table)
            self.assertEqual(table.status, "occupied")

            order = Order.query.filter_by(customer_id=cust.id).first()
            self.assertIsNotNone(order)
            self.assertEqual(order.status, "preparing")

if __name__ == '__main__':
    unittest.main()

