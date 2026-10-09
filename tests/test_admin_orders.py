import unittest
from datetime import datetime, timezone, timedelta
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant, RestaurantStaff
from app.models.menu import MenuCategory, MenuItem
from app.models.order import Order, OrderItem

class AdminOrdersTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Users
        self.admin = User(name="Admin", email="admin@test.com", role="super_admin")
        self.admin.set_password("password")
        
        self.owner1 = User(name="Owner1", email="owner1@test.com", role="restaurant_owner")
        self.owner1.set_password("password")
        
        self.owner2 = User(name="Owner2", email="owner2@test.com", role="restaurant_owner")
        self.owner2.set_password("password")
        
        self.staff_user = User(name="Staff1", email="staff1@test.com", role="restaurant_staff")
        self.staff_user.set_password("password")
        
        self.customer = User(name="Customer", email="customer@test.com", role="customer")
        self.customer.set_password("password")
        
        self.customer2 = User(name="Customer2", email="customer2@test.com", role="customer")
        self.customer2.set_password("password")
        
        db.session.add_all([self.admin, self.owner1, self.owner2, self.staff_user, self.customer, self.customer2])
        db.session.flush()

        # Restaurants
        self.r1 = Restaurant(name="Rest 1", owner_id=self.owner1.id, city="City1", state="State1", is_active=True)
        self.r2 = Restaurant(name="Rest 2", owner_id=self.owner2.id, city="City2", state="State2", is_active=True)
        db.session.add_all([self.r1, self.r2])
        db.session.flush()
        
        # Staff
        self.staff1 = RestaurantStaff(user_id=self.staff_user.id, restaurant_id=self.r1.id, designation="Waiter")
        db.session.add(self.staff1)

        # Menus
        self.cat1 = MenuCategory(restaurant_id=self.r1.id, name="Cat 1")
        self.cat2 = MenuCategory(restaurant_id=self.r2.id, name="Cat 2")
        db.session.add_all([self.cat1, self.cat2])
        db.session.flush()
        
        self.m1 = MenuItem(restaurant_id=self.r1.id, category_id=self.cat1.id, name="Item 1", price=10.0)
        self.m2 = MenuItem(restaurant_id=self.r2.id, category_id=self.cat2.id, name="Item 2", price=20.0)
        db.session.add_all([self.m1, self.m2])
        db.session.flush()

        # Orders
        self.order1 = Order(restaurant_id=self.r1.id, customer_id=self.customer.id, status='placed', total_amount=10.0)
        self.order2 = Order(restaurant_id=self.r2.id, customer_id=self.customer2.id, status='confirmed', total_amount=40.0)
        db.session.add_all([self.order1, self.order2])
        db.session.flush()
        
        self.oi1 = OrderItem(order_id=self.order1.id, menu_item_id=self.m1.id, quantity=1, unit_price=10.0, subtotal=10.0)
        self.oi2 = OrderItem(order_id=self.order2.id, menu_item_id=self.m2.id, quantity=2, unit_price=20.0, subtotal=40.0)
        db.session.add_all([self.oi1, self.oi2])

        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, email, password):
        return self.client.post('/auth/login', data={'email': email, 'password': password}, follow_redirects=True)

    def test_super_admin_can_view_all_orders(self):
        self.login('admin@test.com', 'password')
        response = self.client.get('/admin/orders')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<td>Rest 1</td>', response.data)
        self.assertIn(b'<td>Rest 2</td>', response.data)
        self.assertIn(b'Placed', response.data)
        self.assertIn(b'Confirmed', response.data)

    def test_super_admin_can_filter_orders_by_restaurant(self):
        self.login('admin@test.com', 'password')
        response = self.client.get(f'/admin/orders?restaurant_id={self.r1.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<td>Rest 1</td>', response.data)
        self.assertNotIn(b'<td>Rest 2</td>', response.data)

    def test_super_admin_can_filter_orders_by_status(self):
        self.login('admin@test.com', 'password')
        response = self.client.get('/admin/orders?status=confirmed')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'<td>Rest 1</td>', response.data)
        self.assertIn(b'<td>Rest 2</td>', response.data)

    def test_super_admin_can_view_order_details(self):
        self.login('admin@test.com', 'password')
        response = self.client.get(f'/admin/orders/{self.order1.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Order #1', response.data)
        self.assertIn(b'Item 1', response.data)

    def test_super_admin_can_update_order_status_valid(self):
        self.login('admin@test.com', 'password')
        response = self.client.post(f'/admin/orders/{self.order1.id}/status', data={'status': 'confirmed'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        o = Order.query.get(self.order1.id)
        self.assertEqual(o.status, 'confirmed')

    def test_super_admin_cannot_update_order_status_invalid(self):
        self.login('admin@test.com', 'password')
        response = self.client.post(f'/admin/orders/{self.order1.id}/status', data={'status': 'served'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        o = Order.query.get(self.order1.id)
        self.assertEqual(o.status, 'placed')  # Should not change

    def test_owner_cannot_access_admin_orders(self):
        self.login('owner1@test.com', 'password')
        response = self.client.get('/admin/orders')
        self.assertEqual(response.status_code, 403)
        
    def test_owner_cannot_view_other_restaurant_orders(self):
        self.login('owner1@test.com', 'password')
        response = self.client.get(f'/owner/orders/{self.order2.id}')
        self.assertEqual(response.status_code, 404)

    def test_staff_cannot_access_admin_orders(self):
        self.login('staff1@test.com', 'password')
        response = self.client.get('/admin/orders')
        self.assertEqual(response.status_code, 403)

    def test_customer_cannot_access_other_customer_orders(self):
        self.login('customer@test.com', 'password')
        response = self.client.get(f'/customer/orders/{self.order2.id}')
        self.assertEqual(response.status_code, 404)
        
    def test_customer_cannot_access_admin_orders(self):
        self.login('customer@test.com', 'password')
        response = self.client.get('/admin/orders')
        self.assertEqual(response.status_code, 403)

if __name__ == '__main__':
    unittest.main()
