import unittest
from datetime import datetime, date, time
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant
from app.models.table import Table
from app.models.reservation import Reservation

class AdminReservationsTestCase(unittest.TestCase):
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
        self.t1 = Table(restaurant_id=self.r1.id, table_number="T1", capacity=4)
        self.t2 = Table(restaurant_id=self.r2.id, table_number="T2", capacity=4)
        db.session.add_all([self.t1, self.t2])
        db.session.flush()

        # Create Customer
        self.customer = User(name="Customer", email="customer@test.com", role="customer")
        self.customer.set_password("password")
        db.session.add(self.customer)
        db.session.flush()

        # Create Reservations
        self.res1 = Reservation(
            restaurant_id=self.r1.id,
            customer_id=self.customer.id,
            table_id=self.t1.id,
            reservation_date=date(2025, 1, 1),
            start_time=time(18, 0),
            end_time=time(20, 0),
            number_of_guests=2,
            status='pending'
        )
        self.res2 = Reservation(
            restaurant_id=self.r2.id,
            customer_id=self.customer.id,
            table_id=self.t2.id,
            reservation_date=date(2025, 1, 2),
            start_time=time(19, 0),
            end_time=time(21, 0),
            number_of_guests=4,
            status='confirmed'
        )
        db.session.add_all([self.res1, self.res2])

        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, email, password):
        return self.client.post('/auth/login', data={'email': email, 'password': password}, follow_redirects=True)

    def test_super_admin_can_view_all_reservations(self):
        self.login('admin@test.com', 'password')
        response = self.client.get('/admin/reservations')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<td>Rest 1</td>', response.data)
        self.assertIn(b'<td>Rest 2</td>', response.data)
        self.assertIn(b'pending', response.data.lower())
        self.assertIn(b'confirmed', response.data.lower())

    def test_super_admin_can_filter_by_restaurant(self):
        self.login('admin@test.com', 'password')
        response = self.client.get(f'/admin/reservations?restaurant_id={self.r1.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<td>Rest 1</td>', response.data)
        self.assertNotIn(b'<td>Rest 2</td>', response.data)

    def test_super_admin_can_filter_by_status(self):
        self.login('admin@test.com', 'password')
        response = self.client.get('/admin/reservations?status=confirmed')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'<td>Rest 1</td>', response.data)
        self.assertIn(b'<td>Rest 2</td>', response.data)

    def test_super_admin_can_filter_by_date(self):
        self.login('admin@test.com', 'password')
        response = self.client.get('/admin/reservations?date=2025-01-01')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<td>Rest 1</td>', response.data)
        self.assertNotIn(b'<td>Rest 2</td>', response.data)

    def test_super_admin_can_confirm_reservation(self):
        self.login('admin@test.com', 'password')
        response = self.client.post(f'/admin/reservations/{self.res1.id}/confirm', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        res = Reservation.query.get(self.res1.id)
        self.assertEqual(res.status, 'confirmed')

    def test_super_admin_can_cancel_reservation(self):
        self.login('admin@test.com', 'password')
        response = self.client.post(f'/admin/reservations/{self.res2.id}/cancel', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        res = Reservation.query.get(self.res2.id)
        self.assertEqual(res.status, 'cancelled')

    def test_owner_cannot_access_admin_reservations(self):
        self.login('owner1@test.com', 'password')
        response = self.client.get('/admin/reservations')
        self.assertEqual(response.status_code, 403)
        
        response2 = self.client.post(f'/admin/reservations/{self.res2.id}/cancel')
        self.assertEqual(response2.status_code, 403)

    def test_owner_cannot_modify_other_restaurant_reservations(self):
        self.login('owner1@test.com', 'password')
        response = self.client.post(f'/owner/reservations/{self.res2.id}/cancel')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
