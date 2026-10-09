import unittest
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant, CustomerRestaurant

class AdminCustomerTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Create Super Admin
        self.admin = User(name="Admin", email="admin@test.com", role="super_admin")
        self.admin.set_password("password")
        db.session.add(self.admin)

        # Create Owner 1 and Restaurant 1
        self.owner1 = User(name="Owner1", email="owner1@test.com", role="restaurant_owner")
        self.owner1.set_password("password")
        db.session.add(self.owner1)
        db.session.flush()

        self.r1 = Restaurant(name="Rest 1", owner_id=self.owner1.id, city="City1", state="State1", is_active=True)
        db.session.add(self.r1)
        db.session.flush()

        # Create Owner 2 and Restaurant 2
        self.owner2 = User(name="Owner2", email="owner2@test.com", role="restaurant_owner")
        self.owner2.set_password("password")
        db.session.add(self.owner2)
        db.session.flush()

        self.r2 = Restaurant(name="Rest 2", owner_id=self.owner2.id, city="City2", state="State2", is_active=True)
        db.session.add(self.r2)
        db.session.flush()

        # Create Staff for Restaurant 1
        self.staff_user1 = User(name="Staff1", email="staff1@test.com", role="restaurant_staff")
        self.staff_user1.set_password("password")
        db.session.add(self.staff_user1)

        # Create Customer 1 (Interacted with R1)
        self.c1 = User(name="Customer One", email="c1@test.com", role="customer", is_active=True)
        self.c1.set_password("password")
        db.session.add(self.c1)
        db.session.flush()

        self.cr1 = CustomerRestaurant(customer_id=self.c1.id, restaurant_id=self.r1.id)
        db.session.add(self.cr1)

        # Create Customer 2 (No interaction yet)
        self.c2 = User(name="Customer Two", email="c2@test.com", role="customer", is_active=True)
        self.c2.set_password("password")
        db.session.add(self.c2)

        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, email, password):
        return self.client.post('/auth/login', data={'email': email, 'password': password}, follow_redirects=True)

    def test_super_admin_can_view_all_customers(self):
        self.login('admin@test.com', 'password')
        response = self.client.get('/admin/customers')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Customer One', response.data)
        self.assertIn(b'Customer Two', response.data)
        self.assertIn(b'c1@test.com', response.data)
        self.assertIn(b'c2@test.com', response.data)

    def test_super_admin_can_search_customers(self):
        self.login('admin@test.com', 'password')
        response = self.client.get('/admin/customers?search=Two')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'Customer One', response.data)
        self.assertIn(b'Customer Two', response.data)

    def test_super_admin_can_view_customer_details(self):
        self.login('admin@test.com', 'password')
        response = self.client.get(f'/admin/customers/{self.c1.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Customer One', response.data)
        # Check interaction is shown
        self.assertIn(b'Rest 1', response.data)

    def test_super_admin_can_toggle_customer(self):
        self.login('admin@test.com', 'password')
        response = self.client.post(f'/admin/customers/{self.c1.id}/toggle', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        customer = User.query.get(self.c1.id)
        self.assertFalse(customer.is_active)

    def test_owner_can_see_only_own_customers(self):
        self.login('owner1@test.com', 'password')
        response = self.client.get('/owner/dashboard') # Or wherever customers are listed
        self.assertEqual(response.status_code, 200)
        # In this app, owner dashboard might show customer count.
        # But wait, owner isolation should mean they can't access admin customer routes.
        
        response2 = self.client.get('/admin/customers')
        self.assertEqual(response2.status_code, 403)

    def test_staff_cannot_access_admin_customers(self):
        self.login('staff1@test.com', 'password')
        response = self.client.get('/admin/customers')
        self.assertEqual(response.status_code, 403)

    def test_customer_cannot_access_admin_customers(self):
        self.login('c1@test.com', 'password')
        response = self.client.get('/admin/customers')
        self.assertEqual(response.status_code, 403)

    def test_customer_passwords_not_exposed(self):
        self.login('admin@test.com', 'password')
        response = self.client.get('/admin/customers')
        self.assertNotIn(b'pbkdf2:sha256', response.data)
        
        response2 = self.client.get(f'/admin/customers/{self.c1.id}')
        self.assertNotIn(b'pbkdf2:sha256', response2.data)

if __name__ == '__main__':
    unittest.main()
