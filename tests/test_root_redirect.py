"""
Unit tests for the Root URL ('/') redirect behavior.
Verifies anonymous redirect to login and authenticated redirects to role-appropriate dashboards.
"""
import unittest
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant, RestaurantStaff

class RootRedirectTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed sample users for each role
        self.customer = User(name='Test Customer', email='customer@test.com', role='customer')
        self.customer.set_password('pass123')

        self.owner = User(name='Test Owner', email='owner@test.com', role='restaurant_owner')
        self.owner.set_password('pass123')

        self.staff_user = User(name='Test Staff', email='staff@test.com', role='restaurant_staff')
        self.staff_user.set_password('pass123')

        self.admin = User(name='Test Admin', email='admin@test.com', role='super_admin')
        self.admin.set_password('pass123')

        db.session.add_all([self.customer, self.owner, self.staff_user, self.admin])
        db.session.commit()

        # Associated restaurant and staff record for full dashboard rendering
        self.restaurant = Restaurant(name='Test Bistro', owner_id=self.owner.id, city='Trichy', state='TN')
        db.session.add(self.restaurant)
        db.session.commit()

        self.staff_record = RestaurantStaff(user_id=self.staff_user.id, restaurant_id=self.restaurant.id, designation='Captain')
        db.session.add(self.staff_record)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _login(self, email, password='pass123'):
        return self.client.post('/auth/login', data={'email': email, 'password': password})

    def test_anonymous_root_redirect(self):
        """Anonymous access to '/' must redirect to '/auth/login'."""
        response = self.client.get('/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/auth/login'))

        # Follow redirect lands on login page
        follow_resp = self.client.get('/', follow_redirects=True)
        self.assertEqual(follow_resp.status_code, 200)
        self.assertIn(b'Login', follow_resp.data)

    def test_authenticated_customer_root_redirect(self):
        """Authenticated customer accessing '/' redirects to '/customer/dashboard'."""
        self._login('customer@test.com')
        response = self.client.get('/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/customer/dashboard'))

        follow_resp = self.client.get('/', follow_redirects=True)
        self.assertEqual(follow_resp.status_code, 200)
        self.assertIn(b'Customer Dashboard', follow_resp.data)

    def test_authenticated_owner_root_redirect(self):
        """Authenticated restaurant owner accessing '/' redirects to '/owner/dashboard'."""
        self._login('owner@test.com')
        response = self.client.get('/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/owner/dashboard'))

        follow_resp = self.client.get('/', follow_redirects=True)
        self.assertEqual(follow_resp.status_code, 200)
        self.assertIn(b'Owner Dashboard', follow_resp.data)

    def test_authenticated_staff_root_redirect(self):
        """Authenticated restaurant staff accessing '/' redirects to '/staff/dashboard'."""
        self._login('staff@test.com')
        response = self.client.get('/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/staff/dashboard'))

        follow_resp = self.client.get('/', follow_redirects=True)
        self.assertEqual(follow_resp.status_code, 200)
        self.assertIn(b'Staff Dashboard', follow_resp.data)

    def test_authenticated_super_admin_root_redirect(self):
        """Authenticated super admin accessing '/' redirects to '/admin/dashboard'."""
        self._login('admin@test.com')
        response = self.client.get('/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/admin/dashboard'))

        follow_resp = self.client.get('/', follow_redirects=True)
        self.assertEqual(follow_resp.status_code, 200)
        self.assertIn(b'Admin Dashboard', follow_resp.data)

    def test_authenticated_unknown_role_fallback_redirect(self):
        """Authenticated user with an unexpected role falls back to login redirect."""
        unknown_user = User(name='Unknown', email='unknown@test.com', role='unsupported_role')
        unknown_user.set_password('pass123')
        db.session.add(unknown_user)
        db.session.commit()

        self._login('unknown@test.com')
        response = self.client.get('/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith('/auth/login'))

if __name__ == '__main__':
    unittest.main()
