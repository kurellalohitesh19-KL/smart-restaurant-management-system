import unittest
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant, RestaurantStaff

class AdminStaffTestCase(unittest.TestCase):
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

        self.r1 = Restaurant(name="Rest 1", owner_id=self.owner1.id, city="City1", state="State1", address="Addr1", phone="123", email="1@1.com", is_active=True)
        db.session.add(self.r1)
        db.session.flush()

        # Create Owner 2 and Restaurant 2
        self.owner2 = User(name="Owner2", email="owner2@test.com", role="restaurant_owner")
        self.owner2.set_password("password")
        db.session.add(self.owner2)
        db.session.flush()

        self.r2 = Restaurant(name="Rest 2", owner_id=self.owner2.id, city="City2", state="State2", address="Addr2", phone="123", email="2@2.com", is_active=True)
        db.session.add(self.r2)
        db.session.flush()

        # Create Staff 1 for Restaurant 1
        self.staff_user1 = User(name="Staff1", email="staff1@test.com", role="restaurant_staff")
        self.staff_user1.set_password("password")
        db.session.add(self.staff_user1)
        db.session.flush()
        self.staff1 = RestaurantStaff(user_id=self.staff_user1.id, restaurant_id=self.r1.id, designation="Waiter", is_active=True)
        db.session.add(self.staff1)

        # Create Staff 2 for Restaurant 2
        self.staff_user2 = User(name="Staff2", email="staff2@test.com", role="restaurant_staff")
        self.staff_user2.set_password("password")
        db.session.add(self.staff_user2)
        db.session.flush()
        self.staff2 = RestaurantStaff(user_id=self.staff_user2.id, restaurant_id=self.r2.id, designation="Chef", is_active=True)
        db.session.add(self.staff2)

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

    def logout(self):
        return self.client.get('/auth/logout', follow_redirects=True)

    def test_super_admin_can_view_all_staff(self):
        self.login('admin@test.com', 'password')
        response = self.client.get('/admin/staff')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Staff1', response.data)
        self.assertIn(b'Staff2', response.data)
        self.assertIn(b'Rest 1', response.data)
        self.assertIn(b'Rest 2', response.data)

    def test_super_admin_cannot_see_password_hashes(self):
        self.login('admin@test.com', 'password')
        response = self.client.get('/admin/staff')
        # Check that the password hash is not rendered (assuming werkzeug default prefix pbkdf2)
        self.assertNotIn(b'pbkdf2:sha256', response.data)
        
        response2 = self.client.get(f'/admin/staff/{self.staff1.id}')
        self.assertNotIn(b'pbkdf2:sha256', response2.data)

    def test_super_admin_can_edit_staff(self):
        self.login('admin@test.com', 'password')
        response = self.client.post(f'/admin/staff/{self.staff1.id}/edit', data={
            'name': 'Staff1Updated',
            'email': 'staff1up@test.com',
            'designation': 'Manager',
            'restaurant_id': self.r2.id
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Staff account updated successfully', response.data)
        
        staff = RestaurantStaff.query.get(self.staff1.id)
        self.assertEqual(staff.restaurant_id, self.r2.id)
        self.assertEqual(staff.designation, 'Manager')
        self.assertEqual(staff.user.name, 'Staff1Updated')

    def test_super_admin_can_toggle_staff(self):
        self.login('admin@test.com', 'password')
        response = self.client.post(f'/admin/staff/{self.staff1.id}/toggle', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        staff = RestaurantStaff.query.get(self.staff1.id)
        self.assertFalse(staff.is_active)

    def test_owner_can_only_access_own_staff(self):
        self.login('owner1@test.com', 'password')
        response = self.client.get('/owner/staff')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Staff1', response.data)
        self.assertNotIn(b'Staff2', response.data)

    def test_owner_cannot_access_another_restaurant_staff(self):
        self.login('owner1@test.com', 'password')
        response = self.client.get(f'/owner/staff/{self.staff2.id}/edit')
        self.assertEqual(response.status_code, 404)
        
        response2 = self.client.post(f'/owner/staff/{self.staff2.id}/toggle')
        self.assertEqual(response2.status_code, 404)

    def test_owner_cannot_access_super_admin_staff(self):
        self.login('owner1@test.com', 'password')
        response = self.client.get('/admin/staff')
        self.assertEqual(response.status_code, 403)

    def test_staff_cannot_access_super_admin_staff(self):
        self.login('staff1@test.com', 'password')
        response = self.client.get('/admin/staff')
        self.assertEqual(response.status_code, 403)

    def test_customer_cannot_access_super_admin_staff(self):
        self.login('customer@test.com', 'password')
        response = self.client.get('/admin/staff')
        self.assertEqual(response.status_code, 403)

    def test_super_admin_can_create_staff(self):
        self.login('admin@test.com', 'password')
        # GET form
        resp_get = self.client.get('/admin/staff/create')
        self.assertEqual(resp_get.status_code, 200)
        self.assertIn(b'Add Staff', resp_get.data)

        # POST valid staff
        resp_post = self.client.post('/admin/staff/create', data={
            'name': 'New Admin Staff',
            'email': 'newstaff@test.com',
            'password': 'password123',
            'phone': '9876543210',
            'designation': 'Supervisor',
            'restaurant_id': self.r1.id
        }, follow_redirects=True)
        self.assertEqual(resp_post.status_code, 200)
        self.assertIn(b'Staff account created successfully', resp_post.data)

        new_user = User.query.filter_by(email='newstaff@test.com').first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.role, 'restaurant_staff')
        self.assertTrue(new_user.check_password('password123'))

        new_staff = RestaurantStaff.query.filter_by(user_id=new_user.id).first()
        self.assertIsNotNone(new_staff)
        self.assertEqual(new_staff.restaurant_id, self.r1.id)
        self.assertEqual(new_staff.designation, 'Supervisor')

    def test_super_admin_create_staff_validation(self):
        self.login('admin@test.com', 'password')
        # Duplicate email
        resp = self.client.post('/admin/staff/create', data={
            'name': 'Duplicate Staff',
            'email': 'staff1@test.com',
            'password': 'password123',
            'restaurant_id': self.r1.id
        }, follow_redirects=True)
        self.assertIn(b'Email is already registered.', resp.data)

        # Missing required fields
        resp2 = self.client.post('/admin/staff/create', data={
            'name': '',
            'email': '',
            'password': '',
            'restaurant_id': ''
        }, follow_redirects=True)
        self.assertIn(b'Name, email, password, and assigned restaurant are required.', resp2.data)

    def test_non_admin_cannot_access_create_staff(self):
        self.login('owner1@test.com', 'password')
        resp_owner = self.client.get('/admin/staff/create')
        self.assertEqual(resp_owner.status_code, 403)

        self.login('customer@test.com', 'password')
        resp_cust = self.client.get('/admin/staff/create')
        self.assertEqual(resp_cust.status_code, 403)

    def test_admin_staff_templates_responsive_and_no_literal_none(self):
        self.login('admin@test.com', 'password')
        resp = self.client.get('/admin/staff')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'table-responsive', resp.data)
        # Should not have unhandled None in designation or restaurant columns
        self.assertNotIn(b'<td>None</td>', resp.data)

if __name__ == '__main__':
    unittest.main()
