import unittest
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant

class RestaurantTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Setup users for testing
        self.admin = User(name='Admin', email='admin@test.com', role='super_admin')
        self.admin.set_password('pass')
        self.owner1 = User(name='Owner1', email='owner1@test.com', role='restaurant_owner')
        self.owner1.set_password('pass')
        self.owner2 = User(name='Owner2', email='owner2@test.com', role='restaurant_owner')
        self.owner2.set_password('pass')
        self.customer = User(name='Customer', email='customer@test.com', role='customer')
        self.customer.set_password('pass')
        self.staff = User(name='Staff', email='staff@test.com', role='restaurant_staff')
        self.staff.set_password('pass')
        
        db.session.add_all([self.admin, self.owner1, self.owner2, self.customer, self.staff])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _login(self, email):
        self.client.post('/auth/login', data={'email': email, 'password': 'pass'})

    def test_admin_can_create_restaurant(self):
        self._login('admin@test.com')
        resp = self.client.post('/admin/restaurants/create', data={
            'name': 'Admin Rest',
            'owner_id': self.owner1.id,
            'city': 'Trichy',
            'state': 'TN'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Restaurant created successfully', resp.data)
        r = Restaurant.query.filter_by(name='Admin Rest').first()
        self.assertIsNotNone(r)
        self.assertEqual(r.owner_id, self.owner1.id)

    def test_customer_cannot_create_restaurant(self):
        self._login('customer@test.com')
        resp = self.client.post('/admin/restaurants/create', data={
            'name': 'Cust Rest', 'owner_id': self.owner1.id, 'city': 'Trichy', 'state': 'TN'
        })
        self.assertEqual(resp.status_code, 403)

    def test_staff_cannot_create_restaurant(self):
        self._login('staff@test.com')
        resp = self.client.post('/admin/restaurants/create', data={
            'name': 'Staff Rest', 'owner_id': self.owner1.id, 'city': 'Trichy', 'state': 'TN'
        })
        self.assertEqual(resp.status_code, 403)

    def test_owner_can_view_own_restaurant(self):
        r = Restaurant(name='Owner1 Rest', owner_id=self.owner1.id, city='Trichy', state='TN')
        db.session.add(r)
        db.session.commit()
        
        self._login('owner1@test.com')
        resp = self.client.get('/owner/restaurant')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Owner1 Rest', resp.data)

    def test_owner_can_edit_own_restaurant(self):
        r = Restaurant(name='Owner1 Rest', owner_id=self.owner1.id, city='Trichy', state='TN')
        db.session.add(r)
        db.session.commit()
        
        self._login('owner1@test.com')
        resp = self.client.post('/owner/restaurant/edit', data={
            'name': 'Owner1 Updated',
            'city': 'Chennai',
            'state': 'TN'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        r = Restaurant.query.get(r.id)
        self.assertEqual(r.name, 'Owner1 Updated')

    def test_owner_cannot_access_another_owners_restaurant(self):
        r2 = Restaurant(name='Owner2 Rest', owner_id=self.owner2.id, city='Trichy', state='TN')
        db.session.add(r2)
        db.session.commit()
        
        self._login('owner1@test.com')
        # Attempt direct ID access
        resp = self.client.get(f'/owner/restaurants/{r2.id}')
        self.assertEqual(resp.status_code, 404)
        
        # Test editing via ID (which we also implemented with explicit isolation)
        resp2 = self.client.get(f'/owner/restaurants/{r2.id}/edit')
        self.assertEqual(resp2.status_code, 404)

    def test_owner_cannot_change_restaurant_ownership_or_deactivate(self):
        r = Restaurant(name='Rest', owner_id=self.owner1.id, city='Trichy', state='TN', is_active=True)
        db.session.add(r)
        db.session.commit()
        
        self._login('owner1@test.com')
        # Owner form doesn't even have owner_id or is_active, but simulating POST hacking
        resp = self.client.post('/owner/restaurant/edit', data={
            'name': 'Rest',
            'city': 'Trichy',
            'state': 'TN',
            'owner_id': self.owner2.id,
            'is_active': 'off' # unchecked
        }, follow_redirects=True)
        
        r_updated = Restaurant.query.get(r.id)
        # Should remain owner1 and active
        self.assertEqual(r_updated.owner_id, self.owner1.id)
        self.assertTrue(r_updated.is_active)

    def test_admin_can_view_edit_deactivate_all_restaurants(self):
        r = Restaurant(name='Rest', owner_id=self.owner1.id, city='Trichy', state='TN', is_active=True)
        db.session.add(r)
        db.session.commit()
        
        self._login('admin@test.com')
        # View
        resp1 = self.client.get(f'/admin/restaurants/{r.id}')
        self.assertEqual(resp1.status_code, 200)
        
        # Edit and Deactivate
        resp2 = self.client.post(f'/admin/restaurants/{r.id}/edit', data={
            'name': 'Admin Updated Rest',
            'owner_id': self.owner2.id,
            'city': 'Madurai',
            'state': 'TN'
        }, follow_redirects=True)
        self.assertEqual(resp2.status_code, 200)
        
        r_updated = Restaurant.query.get(r.id)
        self.assertEqual(r_updated.name, 'Admin Updated Rest')
        self.assertEqual(r_updated.owner_id, self.owner2.id)
        self.assertFalse(r_updated.is_active)

if __name__ == '__main__':
    unittest.main()
