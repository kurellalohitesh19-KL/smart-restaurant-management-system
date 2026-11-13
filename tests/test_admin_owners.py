import unittest
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant

class AdminOwnersTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

        # Create Super Admin
        self.admin = User(name="Admin", username="admin", email="admin@test.com", role="super_admin")
        self.admin.set_password("password123")
        db.session.add(self.admin)

        # Create Existing Owner
        self.owner = User(name="Existing Owner", username="existing_owner", email="owner@test.com", phone="1234567890", role="restaurant_owner", is_active=True)
        self.owner.set_password("password123")
        db.session.add(self.owner)
        db.session.flush()

        # Create Restaurant for Existing Owner
        self.restaurant = Restaurant(name="Existing Cafe", owner_id=self.owner.id, city="Trichy", state="Tamil Nadu", address="123 Main St", phone="9876543210", email="cafe@test.com", is_active=True)
        db.session.add(self.restaurant)

        # Create Customer
        self.customer = User(name="Customer User", username="cust_user", email="customer@test.com", role="customer")
        self.customer.set_password("password123")
        db.session.add(self.customer)

        # Create Staff
        self.staff = User(name="Staff User", username="staff_user", email="staff@test.com", role="restaurant_staff")
        self.staff.set_password("password123")
        db.session.add(self.staff)

        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, email="admin@test.com", password="password123"):
        return self.client.post('/auth/login', data={
            'email': email,
            'password': password
        }, follow_redirects=True)

    def test_super_admin_can_access_manage_owners(self):
        """1. Super Admin can access Manage Owners page and view UI elements."""
        self.login("admin@test.com")
        response = self.client.get('/admin/owners')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Manage Restaurant Owners", response.data)
        self.assertIn(b"Add New Owner", response.data)
        self.assertIn(b"Existing Owner", response.data)
        self.assertIn(b"existing_owner", response.data)
        self.assertIn(b"owner@test.com", response.data)

    def test_unauthorized_users_cannot_access_owner_routes(self):
        """2. Anonymous, Customer, Staff, and Owner users cannot access admin owner routes."""
        # Anonymous
        res = self.client.get('/admin/owners')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/auth/login', res.headers['Location'])

        res = self.client.get('/admin/owners/create')
        self.assertEqual(res.status_code, 302)

        # Customer
        self.login("customer@test.com")
        res = self.client.get('/admin/owners')
        self.assertEqual(res.status_code, 403)
        res = self.client.post('/admin/owners/create', data={})
        self.assertEqual(res.status_code, 403)

        # Staff
        self.login("staff@test.com")
        res = self.client.get('/admin/owners')
        self.assertEqual(res.status_code, 403)

        # Restaurant Owner
        self.login("owner@test.com")
        res = self.client.get('/admin/owners')
        self.assertEqual(res.status_code, 403)

    def test_create_valid_owner(self):
        """3. Super Admin can successfully create a valid restaurant owner."""
        self.login("admin@test.com")
        response = self.client.post('/admin/owners/create', data={
            'name': 'Gourmet Master',
            'username': 'gourmet_master',
            'email': 'gourmet@bistro.com',
            'phone': '9988776655',
            'password': 'securepassword123',
            'confirm_password': 'securepassword123',
            'is_active': 'on'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"created successfully", response.data)

        # Check DB
        user = User.query.filter_by(username='gourmet_master').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.name, 'Gourmet Master')
        self.assertEqual(user.email, 'gourmet@bistro.com')
        self.assertEqual(user.phone, '9988776655')
        self.assertEqual(user.role, 'restaurant_owner')
        self.assertTrue(user.is_active)
        self.assertTrue(user.check_password('securepassword123'))

    def test_duplicate_username_rejected(self):
        """4. Duplicate usernames are rejected with an error message."""
        self.login("admin@test.com")
        initial_count = User.query.count()

        response = self.client.post('/admin/owners/create', data={
            'name': 'Duplicate Username Test',
            'username': 'existing_owner', # existing
            'email': 'different_email@test.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Username is already registered", response.data)
        self.assertEqual(User.query.count(), initial_count)

    def test_duplicate_email_rejected(self):
        """5. Duplicate emails are rejected with an error message."""
        self.login("admin@test.com")
        initial_count = User.query.count()

        response = self.client.post('/admin/owners/create', data={
            'name': 'Duplicate Email Test',
            'username': 'unique_user_99',
            'email': 'owner@test.com', # existing
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Email is already registered", response.data)
        self.assertEqual(User.query.count(), initial_count)

    def test_invalid_email_and_mismatched_password_rejected(self):
        """6. Invalid email formats and mismatched passwords are both rejected."""
        self.login("admin@test.com")

        # Invalid Email
        res = self.client.post('/admin/owners/create', data={
            'name': 'Bad Email',
            'username': 'bad_email_user',
            'email': 'invalid-email-format',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)
        self.assertIn(b"valid email address", res.data)

        # Mismatched Password
        res = self.client.post('/admin/owners/create', data={
            'name': 'Mismatch Pass',
            'username': 'mismatch_user',
            'email': 'mismatch@test.com',
            'password': 'password123',
            'confirm_password': 'different_password'
        }, follow_redirects=True)
        self.assertIn(b"Passwords do not match", res.data)

    def test_password_stored_as_hash(self):
        """7. Passwords must be at least 8 chars and are stored securely as cryptographic hashes."""
        self.login("admin@test.com")

        # Too short password (< 8 chars)
        res = self.client.post('/admin/owners/create', data={
            'name': 'Short Pass',
            'username': 'short_pass_user',
            'email': 'short@test.com',
            'password': 'short',
            'confirm_password': 'short'
        }, follow_redirects=True)
        self.assertIn(b"at least 8 characters long", res.data)

        # Valid password hashing
        self.client.post('/admin/owners/create', data={
            'name': 'Hash Check Owner',
            'username': 'hash_owner',
            'email': 'hash@test.com',
            'password': 'supersecretpass',
            'confirm_password': 'supersecretpass'
        }, follow_redirects=True)

        user = User.query.filter_by(username='hash_owner').first()
        self.assertIsNotNone(user)
        self.assertNotEqual(user.password_hash, 'supersecretpass')
        self.assertTrue(user.check_password('supersecretpass'))
        self.assertFalse(user.check_password('wrongpass'))

    def test_new_accounts_receive_correct_role(self):
        """8. New accounts created through /admin/owners receive 'restaurant_owner' role."""
        self.login("admin@test.com")
        self.client.post('/admin/owners/create', data={
            'name': 'Role Verification',
            'username': 'role_verifier',
            'email': 'role@test.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        user = User.query.filter_by(username='role_verifier').first()
        self.assertEqual(user.role, 'restaurant_owner')
        self.assertNotEqual(user.role, 'super_admin')

    def test_customers_and_staff_cannot_be_selected_as_owners(self):
        """9. Customers and Staff cannot be assigned as restaurant owners in Add Restaurant."""
        self.login("admin@test.com")

        # Try assigning Customer as Restaurant Owner
        res = self.client.post('/admin/restaurants/create', data={
            'name': 'Illegal Customer Restaurant',
            'owner_id': self.customer.id,
            'city': 'Trichy',
            'state': 'Tamil Nadu'
        }, follow_redirects=True)
        self.assertIn(b"Invalid owner selected", res.data)

        # Try assigning Staff as Restaurant Owner
        res = self.client.post('/admin/restaurants/create', data={
            'name': 'Illegal Staff Restaurant',
            'owner_id': self.staff.id,
            'city': 'Trichy',
            'state': 'Tamil Nadu'
        }, follow_redirects=True)
        self.assertIn(b"Invalid owner selected", res.data)

    def test_new_owner_appears_in_add_restaurant_dropdown(self):
        """10. Newly created owner appears in Add Restaurant dropdown."""
        self.login("admin@test.com")
        self.client.post('/admin/owners/create', data={
            'name': 'Chef Pierre',
            'username': 'chefpierre',
            'email': 'pierre@paris.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        res = self.client.get('/admin/restaurants/create')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Chef Pierre", res.data)
        self.assertIn(b"chefpierre", res.data)
        self.assertIn(b"pierre@paris.com", res.data)

    def test_restaurant_creation_with_selected_owner(self):
        """11. A restaurant can be successfully created with the newly created owner."""
        self.login("admin@test.com")
        self.client.post('/admin/owners/create', data={
            'name': 'Owner Bob',
            'username': 'owner_bob',
            'email': 'bob@bistro.com',
            'password': 'password123',
            'confirm_password': 'password123'
        }, follow_redirects=True)

        bob = User.query.filter_by(username='owner_bob').first()

        res = self.client.post('/admin/restaurants/create', data={
            'name': "Bob's Gourmet Grill",
            'owner_id': bob.id,
            'city': 'Trichy',
            'state': 'Tamil Nadu',
            'address': '77 Fort Station Road',
            'phone': '1122334455',
            'email': 'grill@bob.com',
            'is_active': 'on'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Restaurant created successfully", res.data)

        restaurant = Restaurant.query.filter_by(name="Bob's Gourmet Grill").first()
        self.assertIsNotNone(restaurant)
        self.assertEqual(restaurant.owner_id, bob.id)
        self.assertIn(restaurant, bob.owned_restaurants)

    def test_owner_detail_view_and_assigned_restaurants(self):
        """12. Super Admin can view owner details and their associated restaurants."""
        self.login("admin@test.com")
        res = self.client.get(f'/admin/owners/{self.owner.id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Existing Owner", res.data)
        self.assertIn(b"existing_owner", res.data)
        self.assertIn(b"Existing Cafe", res.data) # Assigned restaurant

    def test_edit_owner_profile(self):
        """13. Super Admin can edit an owner's details, username, email, and password."""
        self.login("admin@test.com")
        res = self.client.post(f'/admin/owners/{self.owner.id}/edit', data={
            'name': 'Updated Owner Name',
            'username': 'updated_owner_un',
            'email': 'updated_email@test.com',
            'phone': '9998887776',
            'password': 'newpassword123',
            'confirm_password': 'newpassword123',
            'is_active': 'on'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(b"updated successfully", res.data)

        updated = User.query.get(self.owner.id)
        self.assertEqual(updated.name, 'Updated Owner Name')
        self.assertEqual(updated.username, 'updated_owner_un')
        self.assertEqual(updated.email, 'updated_email@test.com')
        self.assertEqual(updated.phone, '9998887776')
        self.assertTrue(updated.check_password('newpassword123'))

    def test_toggle_owner_status(self):
        """14. Super Admin can activate and deactivate owner accounts."""
        self.login("admin@test.com")
        self.assertTrue(self.owner.is_active)

        # Deactivate
        res = self.client.post(f'/admin/owners/{self.owner.id}/toggle', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"deactivated successfully", res.data)
        self.assertFalse(User.query.get(self.owner.id).is_active)

        # Inactive owner should not appear in Add Restaurant eligible dropdown
        create_res_page = self.client.get('/admin/restaurants/create')
        self.assertNotIn(f'value="{self.owner.id}"'.encode(), create_res_page.data)

        # Reactivate
        res = self.client.post(f'/admin/owners/{self.owner.id}/toggle', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"activated successfully", res.data)
        self.assertTrue(User.query.get(self.owner.id).is_active)

    def test_prevent_self_deactivation(self):
        """15. Super Admin cannot deactivate their own account."""
        self.login("admin@test.com")
        res = self.client.post(f'/admin/owners/{self.admin.id}/toggle', follow_redirects=True)
        # Should be 404 because admin user does not have role='restaurant_owner'
        self.assertEqual(res.status_code, 404)

    def test_search_owners(self):
        """16. Search filter searches across name, username, and email."""
        self.login("admin@test.com")

        # Search by name
        res = self.client.get('/admin/owners?search=Existing')
        self.assertIn(b"Existing Owner", res.data)

        # Search by username
        res = self.client.get('/admin/owners?search=existing_owner')
        self.assertIn(b"Existing Owner", res.data)

        # Search by email
        res = self.client.get('/admin/owners?search=owner@test.com')
        self.assertIn(b"Existing Owner", res.data)

        # Non-matching search
        res = self.client.get('/admin/owners?search=NonExistentQueryXYZ')
        self.assertIn(b"No restaurant owners found", res.data)

if __name__ == '__main__':
    unittest.main()
