import unittest
from datetime import datetime, time, date, timedelta, timezone
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant, RestaurantStaff, CustomerRestaurant
from app.models.table import Table
from app.models.reservation import Reservation

class ReservationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Users
        self.admin = User(name='Admin', email='admin@test.com', role='super_admin')
        self.admin.set_password('pass')
        self.owner = User(name='Owner', email='owner@test.com', role='restaurant_owner')
        self.owner.set_password('pass')
        self.staff_user = User(name='Staff', email='staff@test.com', role='restaurant_staff')
        self.staff_user.set_password('pass')
        self.customer = User(name='Customer', email='customer@test.com', role='customer')
        self.customer.set_password('pass')
        self.customer2 = User(name='Customer2', email='customer2@test.com', role='customer')
        self.customer2.set_password('pass')

        db.session.add_all([self.admin, self.owner, self.staff_user, self.customer, self.customer2])
        db.session.commit()

        # Restaurant 1
        self.r1 = Restaurant(owner_id=self.owner.id, name='Test Rest 1', city='City A', state='State A', is_active=True)
        db.session.add(self.r1)
        db.session.commit()

        # Staff assignment
        self.rs1 = RestaurantStaff(user_id=self.staff_user.id, restaurant_id=self.r1.id)
        db.session.add(self.rs1)

        # Tables
        self.t1 = Table(restaurant_id=self.r1.id, table_number='1', capacity=4, status='available')
        self.t2 = Table(restaurant_id=self.r1.id, table_number='2', capacity=2, status='maintenance')
        db.session.add_all([self.t1, self.t2])
        
        # Restaurant 2
        self.owner2 = User(name='Owner 2', email='owner2@test.com', role='restaurant_owner')
        self.owner2.set_password('pass')
        db.session.add(self.owner2)
        db.session.commit()
        
        self.r2 = Restaurant(owner_id=self.owner2.id, name='Test Rest 2', city='City B', state='State B', is_active=False)
        db.session.add(self.r2)
        db.session.commit()
        
        self.t3 = Table(restaurant_id=self.r2.id, table_number='1', capacity=4, status='available')
        db.session.add(self.t3)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, email, password='pass'):
        self.client.post('/auth/login', data={'email': email, 'password': password})

    def logout(self):
        self.client.get('/auth/logout')

    def test_customer_create_reservation_and_customer_restaurant(self):
        self.login('customer@test.com')
        response = self.client.post(f'/customer/restaurants/{self.r1.id}/reserve', data={
            'table_id': self.t1.id,
            'reservation_date': '2030-01-01',
            'start_time': '12:00',
            'end_time': '13:00',
            'number_of_guests': 2
        }, follow_redirects=True)
        self.assertIn(b'booked successfully', response.data)
        
        res = Reservation.query.first()
        self.assertIsNotNone(res)
        self.assertEqual(res.customer_id, self.customer.id)
        self.assertEqual(res.table_id, self.t1.id)
        # Reservations are auto-confirmed, no owner approval needed
        self.assertEqual(res.status, 'confirmed')

        # Check CustomerRestaurant creation
        cr = CustomerRestaurant.query.filter_by(customer_id=self.customer.id, restaurant_id=self.r1.id).first()
        self.assertIsNotNone(cr)
        
        # Test Duplicate prevention
        self.client.post(f'/customer/restaurants/{self.r1.id}/reserve', data={
            'table_id': self.t1.id,
            'reservation_date': '2030-01-02',
            'start_time': '12:00',
            'end_time': '13:00',
            'number_of_guests': 2
        }, follow_redirects=True)
        
        crs = CustomerRestaurant.query.filter_by(customer_id=self.customer.id, restaurant_id=self.r1.id).all()
        self.assertEqual(len(crs), 1)

    def test_reservation_validations(self):
        self.login('customer@test.com')
        
        # Inactive restaurant
        response = self.client.post(f'/customer/restaurants/{self.r2.id}/reserve', data={}, follow_redirects=True)
        self.assertEqual(response.status_code, 404)
        
        # Table under maintenance
        response = self.client.post(f'/customer/restaurants/{self.r1.id}/reserve', data={
            'table_id': self.t2.id,
            'reservation_date': '2030-01-01',
            'start_time': '12:00',
            'end_time': '13:00',
            'number_of_guests': 2
        }, follow_redirects=True)
        self.assertIn(b'under maintenance', response.data)
        
        # Exceed capacity
        response = self.client.post(f'/customer/restaurants/{self.r1.id}/reserve', data={
            'table_id': self.t1.id,
            'reservation_date': '2030-01-01',
            'start_time': '12:00',
            'end_time': '13:00',
            'number_of_guests': 5
        }, follow_redirects=True)
        self.assertIn(b'exceeds table capacity', response.data)
        
        # Invalid date
        response = self.client.post(f'/customer/restaurants/{self.r1.id}/reserve', data={
            'table_id': self.t1.id,
            'reservation_date': 'invalid-date',
            'start_time': '12:00',
            'end_time': '13:00',
            'number_of_guests': 2
        }, follow_redirects=True)
        self.assertIn(b'Invalid date or time', response.data)
        
        # Start time after end time
        response = self.client.post(f'/customer/restaurants/{self.r1.id}/reserve', data={
            'table_id': self.t1.id,
            'reservation_date': '2030-01-01',
            'start_time': '14:00',
            'end_time': '13:00',
            'number_of_guests': 2
        }, follow_redirects=True)
        self.assertIn(b'Start time must be before end time', response.data)

    def test_overlapping_reservations(self):
        self.login('customer@test.com')
        # Create pending
        self.client.post(f'/customer/restaurants/{self.r1.id}/reserve', data={
            'table_id': self.t1.id,
            'reservation_date': '2030-01-01',
            'start_time': '12:00',
            'end_time': '13:00',
            'number_of_guests': 2
        })
        
        # Overlapping 
        response = self.client.post(f'/customer/restaurants/{self.r1.id}/reserve', data={
            'table_id': self.t1.id,
            'reservation_date': '2030-01-01',
            'start_time': '12:30',
            'end_time': '13:30',
            'number_of_guests': 2
        }, follow_redirects=True)
        self.assertIn(b'already reserved for the selected time', response.data)
        
        # Non-overlapping should succeed
        response = self.client.post(f'/customer/restaurants/{self.r1.id}/reserve', data={
            'table_id': self.t1.id,
            'reservation_date': '2030-01-01',
            'start_time': '13:00',
            'end_time': '14:00',
            'number_of_guests': 2
        }, follow_redirects=True)
        self.assertIn(b'booked successfully', response.data)

        # Cancel the first one and book overlapping
        res1 = Reservation.query.first()
        self.client.post(f'/customer/reservations/{res1.id}/cancel')
        
        response = self.client.post(f'/customer/restaurants/{self.r1.id}/reserve', data={
            'table_id': self.t1.id,
            'reservation_date': '2030-01-01',
            'start_time': '12:00',
            'end_time': '13:00',
            'number_of_guests': 2
        }, follow_redirects=True)
        self.assertIn(b'booked successfully', response.data)

    def test_customer_isolation_and_cancellation(self):
        # Create res for customer 1
        res = Reservation(customer_id=self.customer.id, restaurant_id=self.r1.id, table_id=self.t1.id,
                          reservation_date=date(2030, 1, 1), start_time=time(12, 0), end_time=time(13, 0), number_of_guests=2, status='pending')
        db.session.add(res)
        db.session.commit()
        
        self.login('customer2@test.com')
        # View another's res
        response = self.client.get(f'/customer/reservations/{res.id}')
        self.assertEqual(response.status_code, 404)
        
        # Cancel another's res
        response = self.client.post(f'/customer/reservations/{res.id}/cancel')
        self.assertEqual(response.status_code, 404)
        
        self.logout()
        self.login('customer@test.com')
        # View own
        response = self.client.get(f'/customer/reservations/{res.id}')
        self.assertEqual(response.status_code, 200)
        
        # Cancel own
        response = self.client.post(f'/customer/reservations/{res.id}/cancel', follow_redirects=True)
        self.assertIn(b'cancelled successfully', response.data)
        
        db.session.refresh(res)
        self.assertEqual(res.status, 'cancelled')

    def test_owner_reservation_management(self):
        res = Reservation(customer_id=self.customer.id, restaurant_id=self.r1.id, table_id=self.t1.id,
                          reservation_date=date(2030, 1, 1), start_time=time(12, 0), end_time=time(13, 0), number_of_guests=2, status='pending')
        db.session.add(res)
        db.session.commit()
        
        # Login as owner 2, shouldn't see it (will get 404 because reservation is not under their restaurant)
        self.login('owner2@test.com')
        response = self.client.post(f'/owner/reservations/{res.id}/confirm')
        self.assertEqual(response.status_code, 404)
        self.logout()
        
        # Login as owner
        self.login('owner@test.com')
        response = self.client.get('/owner/reservations')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'12:00', response.data)

        # Reservation is already confirmed (auto-confirmed on creation)
        # Directly set to pending to test owner-confirm path
        db.session.refresh(res)
        res.status = 'pending'
        res.table.status = 'available'
        db.session.commit()

        # Confirm via owner
        response = self.client.post(f'/owner/reservations/{res.id}/confirm', follow_redirects=True)
        db.session.refresh(res)
        self.assertEqual(res.status, 'confirmed')

        # Complete (checkout + release table)
        response = self.client.post(f'/owner/reservations/{res.id}/complete', follow_redirects=True)
        db.session.refresh(res)
        self.assertEqual(res.status, 'completed')

    def test_staff_reservation_management(self):
        res = Reservation(customer_id=self.customer.id, restaurant_id=self.r1.id, table_id=self.t1.id,
                          reservation_date=date(2030, 1, 1), start_time=time(12, 0), end_time=time(13, 0), number_of_guests=2, status='pending')
        db.session.add(res)
        db.session.commit()
        
        self.login('staff@test.com')
        response = self.client.get('/staff/reservations')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'12:00', response.data)
        
        # Confirm
        self.client.post(f'/staff/reservations/{res.id}/confirm')
        db.session.refresh(res)
        self.assertEqual(res.status, 'confirmed')
        
        # Cancel
        self.client.post(f'/staff/reservations/{res.id}/cancel')
        db.session.refresh(res)
        self.assertEqual(res.status, 'cancelled')

if __name__ == '__main__':
    unittest.main()
