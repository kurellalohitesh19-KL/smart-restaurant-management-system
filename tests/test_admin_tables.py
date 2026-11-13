import unittest
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant, RestaurantStaff
from app.models.table import Table

class AdminTablesTestCase(unittest.TestCase):
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

        # Create Tables
        self.t1 = Table(restaurant_id=self.r1.id, table_number="T1", capacity=4, status="available")
        db.session.add(self.t1)
        
        self.t2 = Table(restaurant_id=self.r2.id, table_number="T2", capacity=2, status="occupied")
        db.session.add(self.t2)
        
        # Create Staff 1 for Restaurant 1
        self.staff_user = User(name="Staff1", email="staff1@test.com", role="restaurant_staff")
        self.staff_user.set_password("password")
        db.session.add(self.staff_user)
        db.session.flush()
        self.staff1 = RestaurantStaff(user_id=self.staff_user.id, restaurant_id=self.r1.id, is_active=True)
        db.session.add(self.staff1)

        # Create Customer
        self.customer = User(name="Customer", email="customer@test.com", role="customer")
        self.customer.set_password("password")
        db.session.add(self.customer)

        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, email, password):
        return self.client.post('/auth/login', data={'email': email, 'password': password}, follow_redirects=True)

    def test_super_admin_can_view_all_tables(self):
        self.login('admin@test.com', 'password')
        response = self.client.get('/admin/tables')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'T1', response.data)
        self.assertIn(b'T2', response.data)
        self.assertIn(b'Rest 1', response.data)
        self.assertIn(b'Rest 2', response.data)

    def test_super_admin_can_filter_tables_by_restaurant(self):
        self.login('admin@test.com', 'password')
        response = self.client.get(f'/admin/tables?restaurant_id={self.r1.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'T1', response.data)
        self.assertNotIn(b'<td>T2</td>', response.data)

    def test_super_admin_can_search_tables(self):
        self.login('admin@test.com', 'password')
        response = self.client.get(f'/admin/tables?search=T2')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'<td>T1</td>', response.data)
        self.assertIn(b'T2', response.data)

    def test_super_admin_can_edit_table(self):
        self.login('admin@test.com', 'password')
        response = self.client.post(f'/admin/tables/{self.t1.id}/edit', data={
            'table_number': 'T1-Updated',
            'capacity': '6',
            'status': 'maintenance',
            'restaurant_id': self.r1.id
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        table = Table.query.get(self.t1.id)
        self.assertEqual(table.table_number, 'T1-Updated')
        self.assertEqual(table.capacity, 6)
        self.assertEqual(table.status, 'maintenance')

    def test_owner_cannot_access_admin_tables(self):
        self.login('owner1@test.com', 'password')
        response = self.client.get('/admin/tables')
        self.assertEqual(response.status_code, 403)
        
        response2 = self.client.post(f'/admin/tables/{self.t2.id}/edit', data={
            'table_number': 'Hacked',
            'capacity': '10',
            'status': 'available',
            'restaurant_id': self.r2.id
        })
        self.assertEqual(response2.status_code, 403)

    def test_owner_can_only_access_own_tables(self):
        self.login('owner1@test.com', 'password')
        response = self.client.get('/owner/tables')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'T1', response.data)
        self.assertNotIn(b'T2', response.data)

    def test_owner_cannot_edit_other_restaurant_tables(self):
        self.login('owner1@test.com', 'password')
        response = self.client.post(f'/owner/tables/{self.t2.id}/edit', data={
            'table_number': 'Hacked',
            'capacity': '10',
            'status': 'available'
        })
        self.assertEqual(response.status_code, 404)

    def test_staff_cannot_access_admin_tables(self):
        self.login('staff1@test.com', 'password')
        response = self.client.get('/admin/tables')
        self.assertEqual(response.status_code, 403)

    def test_customer_cannot_access_admin_tables(self):
        self.login('customer@test.com', 'password')
        response = self.client.get('/admin/tables')
        self.assertEqual(response.status_code, 403)

if __name__ == '__main__':
    unittest.main()
