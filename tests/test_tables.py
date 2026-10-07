import unittest
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant, RestaurantStaff
from app.models.table import Table

class TablesTestCase(unittest.TestCase):
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
        self.staff1_user = User(name='Staff1', email='staff1@test.com', role='restaurant_staff')
        self.staff1_user.set_password('pass')
        
        db.session.add_all([self.owner1, self.owner2, self.customer, self.staff1_user])
        db.session.commit()
        
        self.r1 = Restaurant(name='R1', owner_id=self.owner1.id, city='Trichy', state='TN')
        self.r2 = Restaurant(name='R2', owner_id=self.owner2.id, city='Trichy', state='TN')
        db.session.add_all([self.r1, self.r2])
        db.session.commit()
        
        self.staff1 = RestaurantStaff(user_id=self.staff1_user.id, restaurant_id=self.r1.id, designation='Waiter')
        db.session.add(self.staff1)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _login(self, email):
        self.client.post('/auth/login', data={'email': email, 'password': 'pass'})

    def test_owner_can_create_and_view_own_table(self):
        self._login('owner1@test.com')
        resp = self.client.post('/owner/tables/create', data={
            'table_number': 'T1',
            'capacity': 4,
            'status': 'available'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Table created successfully', resp.data)
        
        t = Table.query.filter_by(table_number='T1').first()
        self.assertIsNotNone(t)
        self.assertEqual(t.restaurant_id, self.r1.id)
        
        # View
        resp2 = self.client.get('/owner/tables')
        self.assertIn(b'T1', resp2.data)

    def test_owner_cannot_access_or_edit_another_restaurant_table(self):
        t2 = Table(restaurant_id=self.r2.id, table_number='T2', capacity=4, status='available')
        db.session.add(t2)
        db.session.commit()
        
        self._login('owner1@test.com')
        resp = self.client.get(f'/owner/tables/{t2.id}/edit')
        self.assertEqual(resp.status_code, 404)
        
        resp2 = self.client.post(f'/owner/tables/{t2.id}/edit', data={
            'table_number': 'T2 Updated', 'capacity': 5, 'status': 'reserved'
        })
        self.assertEqual(resp2.status_code, 404)

    def test_owner_cannot_create_table_for_another_restaurant(self):
        self._login('owner1@test.com')
        # Form doesn't have restaurant_id, it is derived from current owner.
        self.client.post('/owner/tables/create', data={
            'table_number': 'T1', 'capacity': 4, 'status': 'available'
        }, follow_redirects=True)
        
        t = Table.query.filter_by(table_number='T1').first()
        # Should be forced to r1.id
        self.assertEqual(t.restaurant_id, self.r1.id)

    def test_staff_can_view_and_update_status(self):
        t1 = Table(restaurant_id=self.r1.id, table_number='T1', capacity=4, status='available')
        db.session.add(t1)
        db.session.commit()
        
        self._login('staff1@test.com')
        resp = self.client.get('/staff/tables')
        self.assertIn(b'T1', resp.data)
        
        resp2 = self.client.post(f'/staff/tables/{t1.id}/status', data={
            'status': 'occupied'
        }, follow_redirects=True)
        self.assertIn(b'Table status updated', resp2.data)
        
        t_updated = Table.query.get(t1.id)
        self.assertEqual(t_updated.status, 'occupied')

    def test_staff_cannot_access_another_restaurant_tables(self):
        t2 = Table(restaurant_id=self.r2.id, table_number='T2', capacity=4, status='available')
        db.session.add(t2)
        db.session.commit()
        
        self._login('staff1@test.com')
        resp = self.client.post(f'/staff/tables/{t2.id}/status', data={'status': 'occupied'})
        self.assertEqual(resp.status_code, 404)

    def test_customer_cannot_modify_tables(self):
        t1 = Table(restaurant_id=self.r1.id, table_number='T1', capacity=4, status='available')
        db.session.add(t1)
        db.session.commit()
        
        self._login('customer@test.com')
        resp1 = self.client.post('/owner/tables/create', data={'table_number': 'T2', 'capacity': 2, 'status': 'available'})
        self.assertEqual(resp1.status_code, 403)
        
        resp2 = self.client.post(f'/staff/tables/{t1.id}/status', data={'status': 'occupied'})
        self.assertEqual(resp2.status_code, 403)

    def test_invalid_table_status_and_capacity_rejected(self):
        self._login('owner1@test.com')
        
        # Invalid status
        resp = self.client.post('/owner/tables/create', data={
            'table_number': 'T1', 'capacity': 4, 'status': 'fake_status'
        }, follow_redirects=True)
        self.assertIn(b'Invalid status selected', resp.data)
        
        # Invalid capacity
        resp2 = self.client.post('/owner/tables/create', data={
            'table_number': 'T2', 'capacity': -1, 'status': 'available'
        }, follow_redirects=True)
        self.assertIn(b'Capacity must be a positive integer', resp2.data)

    def test_duplicate_table_number_rejected_within_same_restaurant(self):
        t1 = Table(restaurant_id=self.r1.id, table_number='T1', capacity=4, status='available')
        db.session.add(t1)
        db.session.commit()
        
        self._login('owner1@test.com')
        resp = self.client.post('/owner/tables/create', data={
            'table_number': 'T1', 'capacity': 2, 'status': 'available'
        }, follow_redirects=True)
        self.assertIn(b'Table number already exists', resp.data)

    def test_table_number_reused_in_different_restaurant(self):
        t1 = Table(restaurant_id=self.r1.id, table_number='T1', capacity=4, status='available')
        db.session.add(t1)
        db.session.commit()
        
        self._login('owner2@test.com')
        resp = self.client.post('/owner/tables/create', data={
            'table_number': 'T1', 'capacity': 2, 'status': 'available'
        }, follow_redirects=True)
        self.assertIn(b'Table created successfully', resp.data)
        
        t2 = Table.query.filter_by(restaurant_id=self.r2.id, table_number='T1').first()
        self.assertIsNotNone(t2)

    def test_unauthorized_users_are_blocked(self):
        resp = self.client.get('/owner/tables', follow_redirects=True)
        self.assertIn(b'Please log in', resp.data)
        
        resp2 = self.client.get('/staff/tables', follow_redirects=True)
        self.assertIn(b'Please log in', resp2.data)

if __name__ == '__main__':
    unittest.main()
