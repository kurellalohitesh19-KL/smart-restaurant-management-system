"""
Unit tests for the Super Admin password reset utility (reset_admin_password.py).
Runs against an isolated in-memory SQLite database.
"""

import unittest
from app import create_app, db
from app.models.user import User
from reset_admin_password import reset_super_admin_password, validate_password, MIN_PASSWORD_LENGTH


class ResetAdminPasswordTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Seed test users
        self.admin = User(name='Admin', email='admin@test.com', role='super_admin', is_active=True)
        self.admin.set_password('initial_admin_pass')

        self.inactive_admin = User(name='InactiveAdmin', email='inactive_admin@test.com', role='super_admin', is_active=False)
        self.inactive_admin.set_password('initial_inactive_pass')

        self.owner = User(name='Owner', email='owner@test.com', role='restaurant_owner', is_active=True)
        self.owner.set_password('initial_owner_pass')

        self.customer = User(name='Customer', email='customer@test.com', role='customer', is_active=True)
        self.customer.set_password('initial_cust_pass')

        db.session.add_all([self.admin, self.inactive_admin, self.owner, self.customer])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_validate_password_helper(self):
        # Empty
        valid, err = validate_password("", "")
        self.assertFalse(valid)
        self.assertIn("cannot be empty", err)

        # Short
        valid, err = validate_password("short", "short")
        self.assertFalse(valid)
        self.assertIn(f"at least {MIN_PASSWORD_LENGTH} characters", err)

        # Mismatch
        valid, err = validate_password("valid_password_1", "valid_password_2")
        self.assertFalse(valid)
        self.assertIn("do not match", err)

        # Valid
        valid, err = validate_password("valid_password_123", "valid_password_123")
        self.assertTrue(valid)
        self.assertIsNone(err)

    def test_successful_super_admin_password_reset(self):
        success, msg = reset_super_admin_password(
            self.app, db, 'admin@test.com', 'new_super_secret_999', 'new_super_secret_999'
        )
        self.assertTrue(success)
        self.assertIn("successfully updated", msg)

        # Verify database record updated
        updated_admin = User.query.filter_by(email='admin@test.com').first()
        self.assertTrue(updated_admin.check_password('new_super_secret_999'))
        self.assertFalse(updated_admin.check_password('initial_admin_pass'))

        # Verify other users' passwords remain untouched
        owner = User.query.filter_by(email='owner@test.com').first()
        self.assertTrue(owner.check_password('initial_owner_pass'))
        customer = User.query.filter_by(email='customer@test.com').first()
        self.assertTrue(customer.check_password('initial_cust_pass'))

    def test_reset_nonexistent_email_fails(self):
        success, msg = reset_super_admin_password(
            self.app, db, 'nobody@test.com', 'new_super_secret_999', 'new_super_secret_999'
        )
        self.assertFalse(success)
        self.assertIn("does not exist", msg)

    def test_reset_inactive_super_admin_fails(self):
        success, msg = reset_super_admin_password(
            self.app, db, 'inactive_admin@test.com', 'new_super_secret_999', 'new_super_secret_999'
        )
        self.assertFalse(success)
        self.assertIn("inactive/disabled", msg)

        # Verify password did not change
        u = User.query.filter_by(email='inactive_admin@test.com').first()
        self.assertTrue(u.check_password('initial_inactive_pass'))

    def test_reset_non_super_admin_roles_rejected(self):
        # Owner rejected
        success, msg = reset_super_admin_password(
            self.app, db, 'owner@test.com', 'new_super_secret_999', 'new_super_secret_999'
        )
        self.assertFalse(success)
        self.assertIn("Access denied", msg)
        self.assertIn("restaurant_owner", msg)

        # Customer rejected
        success, msg = reset_super_admin_password(
            self.app, db, 'customer@test.com', 'new_super_secret_999', 'new_super_secret_999'
        )
        self.assertFalse(success)
        self.assertIn("Access denied", msg)
        self.assertIn("customer", msg)

        # Verify neither password changed
        owner = User.query.filter_by(email='owner@test.com').first()
        self.assertTrue(owner.check_password('initial_owner_pass'))
        cust = User.query.filter_by(email='customer@test.com').first()
        self.assertTrue(cust.check_password('initial_cust_pass'))

    def test_reset_invalid_password_rejected(self):
        # Mismatched passwords
        success, msg = reset_super_admin_password(
            self.app, db, 'admin@test.com', 'pass_abc_123', 'pass_xyz_456'
        )
        self.assertFalse(success)
        self.assertIn("do not match", msg)

        # Too short password
        success, msg = reset_super_admin_password(
            self.app, db, 'admin@test.com', 'short', 'short'
        )
        self.assertFalse(success)
        self.assertIn(f"at least {MIN_PASSWORD_LENGTH} characters", msg)

        # Empty password
        success, msg = reset_super_admin_password(
            self.app, db, 'admin@test.com', '', ''
        )
        self.assertFalse(success)
        self.assertIn("cannot be empty", msg)

        # Verify admin password remains untouched
        admin = User.query.filter_by(email='admin@test.com').first()
        self.assertTrue(admin.check_password('initial_admin_pass'))

    def test_invalid_email_input_rejected(self):
        success, msg = reset_super_admin_password(
            self.app, db, '', 'new_super_secret_999', 'new_super_secret_999'
        )
        self.assertFalse(success)
        self.assertIn("valid email address", msg)


if __name__ == '__main__':
    unittest.main()
