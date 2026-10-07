import unittest
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant, RestaurantStaff

class StaffTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        self.owner1 = User(name='Owner1', email='owner1@test.com', role='restaurant_owner')
        self.owner1.set_password('pass')
        self.owner2 = User(name='Owner2', email='owner2@test.com', role='restaurant_owner')
        self.owner2.set_password('pass')
        self.customer = User(name='Customer', email='customer@test.com', role='customer')
        self.customer.set_password('pass')
        self.admin = User(name='Admin', email='admin@test.com', role='super_admin')
        self.admin.set_password('pass')
        
        db.session.add_all([self.owner1, self.owner2, self.customer, self.admin])
        db.session.commit()
        
        self.r1 = Restaurant(name='R1', owner_id=self.owner1.id, city='Trichy', state='TN')
        self.r2 = Restaurant(name='R2', owner_id=self.owner2.id, city='Trichy', state='TN')
        db.session.add_all([self.r1, self.r2])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _login(self, email):
        self.client.post('/auth/login', data={'email': email, 'password': 'pass'})

    def test_owner_can_create_staff_and_role_assigned(self):
        self._login('owner1@test.com')
        resp = self.client.post('/owner/staff/create', data={
            'name': 'Staff One',
            'email': 'staff1@test.com',
            'password': 'pass',
            'designation': 'Waiter'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Staff account created successfully', resp.data)
        
        user = User.query.filter_by(email='staff1@test.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.role, 'restaurant_staff')
        self.assertTrue(user.check_password('pass'))
        
        staff = RestaurantStaff.query.filter_by(user_id=user.id).first()
        self.assertIsNotNone(staff)
        self.assertEqual(staff.restaurant_id, self.r1.id)

    def test_duplicate_email_rejected(self):
        self._login('owner1@test.com')
        self.client.post('/owner/staff/create', data={
            'name': 'Staff One', 'email': 'staff1@test.com', 'password': 'pass', 'designation': 'Waiter'
        }, follow_redirects=True)
        resp = self.client.post('/owner/staff/create', data={
            'name': 'Staff Two', 'email': 'staff1@test.com', 'password': 'pass', 'designation': 'Chef'
        }, follow_redirects=True)
        self.assertIn(b'Email is already registered', resp.data)

    def test_owner_cannot_access_another_restaurant_staff(self):
        u = User(name='Staff2', email='staff2@test.com', role='restaurant_staff')
        u.set_password('pass')
        db.session.add(u)
        db.session.commit()
        s = RestaurantStaff(user_id=u.id, restaurant_id=self.r2.id, designation='Chef')
        db.session.add(s)
        db.session.commit()
        
        self._login('owner1@test.com')
        resp = self.client.get(f'/owner/staff/{s.id}/edit')
        self.assertEqual(resp.status_code, 404)
        
        resp_toggle = self.client.post(f'/owner/staff/{s.id}/toggle')
        self.assertEqual(resp_toggle.status_code, 404)

    def test_customer_and_staff_cannot_create_staff(self):
        self._login('customer@test.com')
        resp = self.client.get('/owner/staff/create')
        self.assertEqual(resp.status_code, 403)
        
        # Create a staff member to test staff restrictions
        u = User(name='S', email='s@test.com', role='restaurant_staff')
        u.set_password('pass')
        db.session.add(u)
        db.session.commit()
        
        self._login('s@test.com')
        resp2 = self.client.get('/owner/staff/create')
        self.assertEqual(resp2.status_code, 403)

    def test_staff_dashboard_access_and_isolation(self):
        u = User(name='My Staff', email='mystaff@test.com', role='restaurant_staff')
        u.set_password('pass')
        db.session.add(u)
        db.session.commit()
        s = RestaurantStaff(user_id=u.id, restaurant_id=self.r1.id, designation='Manager')
        db.session.add(s)
        db.session.commit()
        
        self._login('mystaff@test.com')
        resp = self.client.get('/staff/dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'My Staff', resp.data)
        self.assertIn(b'R1', resp.data)
        self.assertIn(b'Manager', resp.data)
        
        resp2 = self.client.get('/owner/dashboard')
        self.assertEqual(resp2.status_code, 403)
        resp3 = self.client.get('/admin/dashboard')
        self.assertEqual(resp3.status_code, 403)

if __name__ == '__main__':
    unittest.main()
