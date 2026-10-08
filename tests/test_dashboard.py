import unittest
from datetime import datetime, time
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant, RestaurantStaff, CustomerRestaurant
from app.models.table import Table
from app.models.menu import MenuCategory, MenuItem
from app.models.reservation import Reservation
from app.models.order import Order, OrderItem

class DashboardTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Users
        self.admin = User(name='Admin', email='admin@test.com', role='super_admin')
        self.admin.set_password('pass')
        self.owner1 = User(name='Owner1', email='owner1@test.com', role='restaurant_owner')
        self.owner1.set_password('pass')
        self.owner2 = User(name='Owner2', email='owner2@test.com', role='restaurant_owner')
        self.owner2.set_password('pass')
        self.staff1 = User(name='Staff1', email='staff1@test.com', role='restaurant_staff')
        self.staff1.set_password('pass')
        self.staff2 = User(name='Staff2', email='staff2@test.com', role='restaurant_staff')
        self.staff2.set_password('pass')
        self.cust1 = User(name='Cust1', email='cust1@test.com', role='customer')
        self.cust1.set_password('pass')
        self.cust2 = User(name='Cust2', email='cust2@test.com', role='customer')
        self.cust2.set_password('pass')
        
        db.session.add_all([self.admin, self.owner1, self.owner2, self.staff1, self.staff2, self.cust1, self.cust2])
        db.session.commit()

        # Restaurants
        self.r1 = Restaurant(name='R1', email='r1@test.com', phone='111', owner_id=self.owner1.id, address='A1', city='C1', state='S1')
        self.r2 = Restaurant(name='R2', email='r2@test.com', phone='222', owner_id=self.owner2.id, address='A2', city='C2', state='S2')
        db.session.add_all([self.r1, self.r2])
        db.session.commit()

        # Staff assignment
        self.s1 = RestaurantStaff(user_id=self.staff1.id, restaurant_id=self.r1.id, designation='Waiter')
        self.s2 = RestaurantStaff(user_id=self.staff2.id, restaurant_id=self.r2.id, designation='Chef')
        db.session.add_all([self.s1, self.s2])
        db.session.commit()

        # Tables
        self.t1 = Table(restaurant_id=self.r1.id, table_number='T1', capacity=2, status='available')
        self.t2 = Table(restaurant_id=self.r1.id, table_number='T2', capacity=4, status='occupied')
        self.t3 = Table(restaurant_id=self.r2.id, table_number='T3', capacity=2, status='available')
        db.session.add_all([self.t1, self.t2, self.t3])
        db.session.commit()

        # Reservations
        self.res1 = Reservation(customer_id=self.cust1.id, restaurant_id=self.r1.id, table_id=self.t1.id,
                                reservation_date=datetime.now().date(), start_time=time(18, 0), end_time=time(19, 0),
                                number_of_guests=2, status='confirmed')
        self.res2 = Reservation(customer_id=self.cust2.id, restaurant_id=self.r2.id, table_id=self.t3.id,
                                reservation_date=datetime.now().date(), start_time=time(19, 0), end_time=time(20, 0),
                                number_of_guests=2, status='pending')
        db.session.add_all([self.res1, self.res2])
        db.session.commit()

        # Customer Restaurant Tracking
        cr1 = CustomerRestaurant(customer_id=self.cust1.id, restaurant_id=self.r1.id)
        cr2 = CustomerRestaurant(customer_id=self.cust2.id, restaurant_id=self.r2.id)
        db.session.add_all([cr1, cr2])
        db.session.commit()

        # Orders
        self.o1 = Order(customer_id=self.cust1.id, restaurant_id=self.r1.id, total_amount=100.0, status='placed')
        self.o2 = Order(customer_id=self.cust2.id, restaurant_id=self.r2.id, total_amount=200.0, status='ready')
        db.session.add_all([self.o1, self.o2])
        db.session.commit()

        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, email):
        return self.client.post('/auth/login', data={'email': email, 'password': 'pass'})

    # Role Isolation Tests
    def test_unauthenticated_cannot_access(self):
        for route in ['/customer/dashboard', '/owner/dashboard', '/staff/dashboard', '/admin/dashboard']:
            resp = self.client.get(route)
            self.assertEqual(resp.status_code, 302)

    def test_customer_role_isolation(self):
        self.login('cust1@test.com')
        self.assertEqual(self.client.get('/owner/dashboard').status_code, 403)
        self.assertEqual(self.client.get('/staff/dashboard').status_code, 403)
        self.assertEqual(self.client.get('/admin/dashboard').status_code, 403)
        self.assertEqual(self.client.get('/customer/dashboard').status_code, 200)

    def test_owner_role_isolation(self):
        self.login('owner1@test.com')
        self.assertEqual(self.client.get('/customer/dashboard').status_code, 403)
        self.assertEqual(self.client.get('/staff/dashboard').status_code, 403)
        self.assertEqual(self.client.get('/admin/dashboard').status_code, 403)
        self.assertEqual(self.client.get('/owner/dashboard').status_code, 200)

    def test_staff_role_isolation(self):
        self.login('staff1@test.com')
        self.assertEqual(self.client.get('/customer/dashboard').status_code, 403)
        self.assertEqual(self.client.get('/owner/dashboard').status_code, 403)
        self.assertEqual(self.client.get('/admin/dashboard').status_code, 403)
        self.assertEqual(self.client.get('/staff/dashboard').status_code, 200)

    def test_admin_role_isolation(self):
        self.login('admin@test.com')
        self.assertEqual(self.client.get('/customer/dashboard').status_code, 403)
        self.assertEqual(self.client.get('/owner/dashboard').status_code, 403)
        self.assertEqual(self.client.get('/staff/dashboard').status_code, 403)
        self.assertEqual(self.client.get('/admin/dashboard').status_code, 200)

    # Data Isolation & Counting Tests
    def test_customer_dashboard_data(self):
        self.login('cust1@test.com')
        resp = self.client.get('/customer/dashboard')
        self.assertIn(b'R1', resp.data) # Has reservation and order at R1
        self.assertNotIn(b'R2', resp.data) # No reservation/order at R2

    def test_owner_dashboard_data(self):
        self.login('owner1@test.com')
        resp = self.client.get('/owner/dashboard')
        
        # Check if only own stats are shown. r1 has 2 tables, 1 res, 1 order, 1 staff, 1 customer.
        self.assertIn(b'Total Tables:</strong> 2', resp.data)
        self.assertIn(b"Today's Reservations:</strong> 1", resp.data)
        self.assertIn(b"Today's Orders:</strong> 1", resp.data)
        self.assertIn(b'Total Active Staff:</strong> 1', resp.data)
        self.assertIn(b'Interacted Customers:</strong> 1', resp.data)
        self.assertIn(b'R1', resp.data)
        self.assertNotIn(b'R2', resp.data)

    def test_staff_dashboard_data(self):
        self.login('staff1@test.com')
        resp = self.client.get('/staff/dashboard')
        
        # r1 stats: 1 available, 1 occupied, 1 res, 1 order
        self.assertIn(b'Available:</strong> <span class="badge bg-success">1', resp.data)
        self.assertIn(b'Occupied:</strong> <span class="badge bg-danger">1', resp.data)
        self.assertIn(b"Today's:</strong> 1", resp.data)
        self.assertIn(b'New (Placed):</strong> 1', resp.data)
        self.assertIn(b'R1', resp.data)
        self.assertNotIn(b'R2', resp.data)

    def test_admin_dashboard_data(self):
        self.login('admin@test.com')
        resp = self.client.get('/admin/dashboard')
        
        # Admin should see global stats
        self.assertIn(b'Customers:</strong> 2', resp.data)
        self.assertIn(b'Restaurant Owners:</strong> 2', resp.data)
        self.assertIn(b'Restaurant Staff:</strong> 2', resp.data)
        self.assertIn(b'Super Admins:</strong> 1', resp.data)
        
        self.assertIn(b'Total Restaurants:</strong> 2', resp.data)
        self.assertIn(b'Total:</strong> 3', resp.data) # Tables
        self.assertIn(b'Total:</strong> 2', resp.data) # Reservations
        self.assertIn(b'Total:</strong> 2', resp.data) # Orders
        
        self.assertNotIn(b'password_hash', resp.data)
        self.assertNotIn(b'SECRET_KEY', resp.data)

if __name__ == '__main__':
    unittest.main()
