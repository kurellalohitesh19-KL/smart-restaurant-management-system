import unittest
import re
from datetime import date, time as dt_time
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant, RestaurantStaff
from app.models.table import Table
from app.models.menu import MenuCategory, MenuItem
from app.models.reservation import Reservation
from app.models.order import Order, OrderItem

class CSRFTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        # Explicitly enable CSRF for this test suite
        self.app.config['WTF_CSRF_ENABLED'] = True
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed basic users and restaurant
        self.admin = User(name='Admin', email='admin@test.com', role='super_admin')
        self.admin.set_password('pass')
        self.owner = User(name='Owner', email='owner@test.com', role='restaurant_owner')
        self.owner.set_password('pass')
        self.staff_user = User(name='Staff', email='staff@test.com', role='restaurant_staff')
        self.staff_user.set_password('pass')
        self.customer = User(name='Customer', email='customer@test.com', role='customer')
        self.customer.set_password('pass')

        db.session.add_all([self.admin, self.owner, self.staff_user, self.customer])
        db.session.commit()

        self.restaurant = Restaurant(owner_id=self.owner.id, name='CSRF Rest', city='Trichy', state='TN', is_active=True)
        db.session.add(self.restaurant)
        db.session.commit()

        self.staff_assignment = RestaurantStaff(restaurant_id=self.restaurant.id, user_id=self.staff_user.id)
        self.table = Table(restaurant_id=self.restaurant.id, table_number='1', capacity=4, status='available')
        self.cat = MenuCategory(restaurant_id=self.restaurant.id, name='Mains', is_active=True)
        db.session.add_all([self.staff_assignment, self.table, self.cat])
        db.session.commit()

        self.item = MenuItem(category_id=self.cat.id, restaurant_id=self.restaurant.id, name='Dosa', price=10.0, is_available=True)
        db.session.add(self.item)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def get_csrf_token(self, html):
        match = re.search(r'<input type="hidden" name="csrf_token" value="(.*?)"', html)
        if match:
            return match.group(1)
        return None

    def login_client(self, email, password='pass'):
        resp = self.client.get('/auth/login')
        token = self.get_csrf_token(resp.data.decode('utf-8'))
        return self.client.post('/auth/login', data={
            'email': email,
            'password': password,
            'csrf_token': token
        }, follow_redirects=True)

    def test_missing_csrf_token_rejected(self):
        # State-changing POST without CSRF token
        response = self.client.post('/auth/login', data={
            'email': 'customer@test.com',
            'password': 'pass'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'The CSRF token is missing', response.data)

    def test_invalid_csrf_token_rejected(self):
        # Establish session first so a CSRF session token exists
        self.client.get('/auth/login')
        # State-changing POST with invalid CSRF token
        response = self.client.post('/auth/login', data={
            'email': 'customer@test.com',
            'password': 'pass',
            'csrf_token': 'completely_invalid_csrf_token'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn(b'The CSRF token is invalid', response.data)

    def test_login_and_logout_with_valid_token(self):
        # Valid login
        response = self.login_client('customer@test.com')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Customer Dashboard', response.data)

        # Logout
        logout_resp = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(logout_resp.status_code, 200)
        self.assertIn(b'You have been logged out', logout_resp.data)

    def test_registration_with_valid_and_missing_token(self):
        # Missing token fails
        resp_missing = self.client.post('/auth/register', data={
            'name': 'New User',
            'email': 'new@test.com',
            'password': 'pass',
            'confirm_password': 'pass'
        })
        self.assertEqual(resp_missing.status_code, 400)

        # Valid token succeeds
        get_resp = self.client.get('/auth/register')
        token = self.get_csrf_token(get_resp.data.decode('utf-8'))
        self.assertIsNotNone(token)

        resp_valid = self.client.post('/auth/register', data={
            'name': 'New User',
            'email': 'new@test.com',
            'password': 'pass',
            'confirm_password': 'pass',
            'csrf_token': token
        }, follow_redirects=True)
        self.assertEqual(resp_valid.status_code, 200)
        self.assertIn(b'Registration successful', resp_valid.data)

    def test_reservation_creation_with_csrf(self):
        self.login_client('customer@test.com')
        # View reservation form
        form_page = self.client.get(f'/customer/restaurants/{self.restaurant.id}/reserve')
        token = self.get_csrf_token(form_page.data.decode('utf-8'))
        self.assertIsNotNone(token)

        # Submit valid reservation
        resp = self.client.post(f'/customer/restaurants/{self.restaurant.id}/reserve', data={
            'table_id': self.table.id,
            'reservation_date': '2030-01-01',
            'start_time': '12:00',
            'end_time': '13:00',
            'number_of_guests': 2,
            'csrf_token': token
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Reservation created successfully', resp.data)

    def test_cart_and_order_flow_with_csrf(self):
        self.login_client('customer@test.com')

        # Add to cart from menu
        menu_page = self.client.get(f'/customer/restaurants/{self.restaurant.id}/menu')
        token = self.get_csrf_token(menu_page.data.decode('utf-8'))
        self.assertIsNotNone(token)

        cart_add_resp = self.client.post('/customer/cart/add', data={
            'menu_item_id': self.item.id,
            'quantity': 1,
            'csrf_token': token
        }, follow_redirects=True)
        self.assertEqual(cart_add_resp.status_code, 200)
        self.assertIn(b'added to cart', cart_add_resp.data)

        # Place order
        cart_page = self.client.get('/customer/cart')
        cart_token = self.get_csrf_token(cart_page.data.decode('utf-8'))
        self.assertIsNotNone(cart_token)

        place_resp = self.client.post('/customer/order/place', data={
            'csrf_token': cart_token
        }, follow_redirects=True)
        self.assertEqual(place_resp.status_code, 200)
        self.assertIn(b'Order placed successfully', place_resp.data)

        # Confirm final order
        order = Order.query.filter_by(customer_id=self.customer.id).first()
        order_page = self.client.get(f'/customer/orders/{order.id}')
        order_token = self.get_csrf_token(order_page.data.decode('utf-8'))
        self.assertIsNotNone(order_token)

        confirm_resp = self.client.post(f'/customer/orders/{order.id}/confirm', data={
            'csrf_token': order_token
        }, follow_redirects=True)
        self.assertEqual(confirm_resp.status_code, 200)
        self.assertIn(b'Final order confirmed', confirm_resp.data)

    def test_staff_status_update_with_csrf(self):
        # Create an order with status 'placed'
        order = Order(customer_id=self.customer.id, restaurant_id=self.restaurant.id, status='placed', total_amount=10.0)
        db.session.add(order)
        db.session.commit()

        self.login_client('staff@test.com')
        detail_page = self.client.get(f'/staff/orders/{order.id}')
        token = self.get_csrf_token(detail_page.data.decode('utf-8'))
        self.assertIsNotNone(token)

        update_resp = self.client.post(f'/staff/orders/{order.id}/status', data={
            'status': 'confirmed',
            'csrf_token': token
        }, follow_redirects=True)
        self.assertEqual(update_resp.status_code, 200)
        self.assertIn(b'Order status updated to confirmed', update_resp.data)

    def test_admin_form_with_csrf(self):
        self.login_client('admin@test.com')
        admin_page = self.client.get('/admin/restaurants/create')
        token = self.get_csrf_token(admin_page.data.decode('utf-8'))
        self.assertIsNotNone(token)

        create_resp = self.client.post('/admin/restaurants/create', data={
            'name': 'New Admin Restaurant',
            'owner_id': self.owner.id,
            'phone': '9998887776',
            'email': 'adminrest@test.com',
            'address': 'Main Road',
            'city': 'Trichy',
            'state': 'TN',
            'latitude': 10.8,
            'longitude': 78.7,
            'is_active': 'y',
            'csrf_token': token
        }, follow_redirects=True)
        self.assertEqual(create_resp.status_code, 200)
        self.assertIn(b'Restaurant created successfully', create_resp.data)

if __name__ == '__main__':
    unittest.main()
