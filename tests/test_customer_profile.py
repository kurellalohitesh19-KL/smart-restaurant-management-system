import unittest
from app import create_app, db
from app.models.user import User
from app.models.order import Order
from app.models.reservation import Reservation

class CustomerProfileTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.cust = User(name='John Doe', email='john@test.com', phone='1234567890', role='customer')
        self.cust.set_password('pass123')

        self.other_cust = User(name='Jane Smith', email='jane@test.com', phone='0987654321', role='customer')
        self.other_cust.set_password('pass123')

        self.owner = User(name='Rest Owner', email='owner@test.com', role='restaurant_owner')
        self.owner.set_password('pass123')

        db.session.add_all([self.cust, self.other_cust, self.owner])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, email, password='pass123'):
        return self.client.post('/auth/login', data={'email': email, 'password': password})

    def test_unauthenticated_cannot_access_profile(self):
        resp = self.client.get('/customer/profile')
        self.assertEqual(resp.status_code, 302)

    def test_non_customer_role_cannot_access_customer_profile(self):
        self.login('owner@test.com')
        resp = self.client.get('/customer/profile')
        self.assertEqual(resp.status_code, 403)

    def test_customer_can_view_own_profile(self):
        self.login('john@test.com')
        resp = self.client.get('/customer/profile')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'John Doe', resp.data)
        self.assertIn(b'john@test.com', resp.data)
        self.assertIn(b'1234567890', resp.data)
        # Ensure other customer's private data is not present
        self.assertNotIn(b'jane@test.com', resp.data)

    def test_customer_can_update_profile(self):
        self.login('john@test.com')
        resp = self.client.post('/customer/profile', data={
            'name': 'John Updated',
            'phone': '9999999999'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Profile updated successfully', resp.data)
        self.assertIn(b'John Updated', resp.data)

        updated_user = User.query.filter_by(email='john@test.com').first()
        self.assertEqual(updated_user.name, 'John Updated')
        self.assertEqual(updated_user.phone, '9999999999')
        self.assertEqual(updated_user.role, 'customer') # Role remains customer

    def test_customer_cannot_set_empty_name(self):
        self.login('john@test.com')
        resp = self.client.post('/customer/profile', data={
            'name': '',
            'phone': '9999999999'
        }, follow_redirects=True)
        self.assertIn(b'Name cannot be empty', resp.data)

        user = User.query.filter_by(email='john@test.com').first()
        self.assertEqual(user.name, 'John Doe') # Unchanged

if __name__ == '__main__':
    unittest.main()
