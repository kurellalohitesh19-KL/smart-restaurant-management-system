import unittest
from app import create_app, db
from app.models.user import User

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['TESTING'] = True
        # Use an in-memory SQLite database for testing authentication logic
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_hashing(self):
        u = User(name='Test', email='test@test.com', role='customer')
        u.set_password('password123')
        self.assertTrue(u.check_password('password123'))
        self.assertFalse(u.check_password('wrongpassword'))
        self.assertNotEqual(u.password_hash, 'password123')

    def test_customer_registration(self):
        response = self.client.post('/auth/register', data={
            'name': 'John Doe',
            'email': 'john@test.com',
            'phone': '1234567890',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful', response.data)
        
        user = User.query.filter_by(email='john@test.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.role, 'customer')

    def test_duplicate_email(self):
        u = User(name='Existing', email='exists@test.com', role='customer')
        u.set_password('pass')
        db.session.add(u)
        db.session.commit()

        response = self.client.post('/auth/register', data={
            'name': 'New',
            'email': 'exists@test.com',
            'phone': '0987654321',
            'password': 'pass',
            'confirm_password': 'pass'
        }, follow_redirects=True)
        self.assertIn(b'Email address already registered', response.data)

    def test_successful_login(self):
        u = User(name='Login User', email='login@test.com', role='customer')
        u.set_password('pass')
        db.session.add(u)
        db.session.commit()

        response = self.client.post('/auth/login', data={
            'email': 'login@test.com',
            'password': 'pass'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        # Assuming redirect_based_on_role for customer goes to home
        self.assertIn(b'Customer Dashboard', response.data)

    def test_failed_login(self):
        response = self.client.post('/auth/login', data={
            'email': 'fake@test.com',
            'password': 'pass'
        }, follow_redirects=True)
        self.assertIn(b'Invalid email or password', response.data)

    def test_logout(self):
        u = User(name='Logout User', email='logout@test.com', role='customer')
        u.set_password('pass')
        db.session.add(u)
        db.session.commit()

        self.client.post('/auth/login', data={'email': 'logout@test.com', 'password': 'pass'})
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertIn(b'You have been logged out', response.data)

    def test_unauthenticated_access_redirect(self):
        response = self.client.get('/customer/dashboard', follow_redirects=True)
        self.assertIn(b'Please log in to access this page', response.data)

    def _login_as(self, role):
        u = User(name=role, email=f'{role}@test.com', role=role)
        u.set_password('pass')
        db.session.add(u)
        db.session.commit()
        self.client.post('/auth/login', data={'email': f'{role}@test.com', 'password': 'pass'})
        return u

    def test_customer_role_protection(self):
        self._login_as('customer')
        response = self.client.get('/customer/dashboard')
        self.assertEqual(response.status_code, 200)
        
        # Ensure customer cannot access owner routes
        response = self.client.get('/owner/dashboard')
        self.assertEqual(response.status_code, 403)
        
        # Ensure customer cannot access staff routes
        response = self.client.get('/staff/dashboard')
        self.assertEqual(response.status_code, 403)
        
        # Ensure customer cannot access super-admin routes
        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 403)

    def test_owner_role_protection(self):
        self._login_as('restaurant_owner')
        response = self.client.get('/owner/dashboard')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 403)

    def test_staff_role_protection(self):
        self._login_as('restaurant_staff')
        response = self.client.get('/staff/dashboard')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/owner/dashboard')
        self.assertEqual(response.status_code, 403)

    def test_super_admin_role_protection(self):
        self._login_as('super_admin')
        response = self.client.get('/admin/dashboard')
        self.assertEqual(response.status_code, 200)
        response = self.client.get('/owner/dashboard')
        self.assertEqual(response.status_code, 403)

if __name__ == '__main__':
    unittest.main()
