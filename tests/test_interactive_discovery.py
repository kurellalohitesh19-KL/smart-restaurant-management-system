import unittest
from datetime import datetime, date, time
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant
from app.models.table import Table
from app.models.menu import MenuCategory, MenuItem
from app.models.reservation import Reservation

class InteractiveDiscoveryTestCase(unittest.TestCase):
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
        self.owner = User(name='Owner', email='owner@test.com', role='restaurant_owner')
        self.owner.set_password('pass')
        self.customer = User(name='Customer', email='customer@test.com', role='customer')
        self.customer.set_password('pass')
        db.session.add_all([self.owner, self.customer])
        db.session.commit()

        # Restaurant
        self.rest = Restaurant(
            name='Spice Garden',
            owner_id=self.owner.id,
            city='Tiruchirappalli',
            state='Tamil Nadu',
            address='123 Grand Trunk Road',
            phone='9876543210',
            email='spice@garden.com',
            is_active=True
        )
        db.session.add(self.rest)
        db.session.commit()

        # Tables
        self.t1 = Table(restaurant_id=self.rest.id, table_number='T1', capacity=2, status='available')
        self.t2 = Table(restaurant_id=self.rest.id, table_number='T2', capacity=4, status='available')
        self.t3 = Table(restaurant_id=self.rest.id, table_number='T3', capacity=6, status='available')
        db.session.add_all([self.t1, self.t2, self.t3])
        db.session.commit()

        # Categories & Items
        self.c1 = MenuCategory(restaurant_id=self.rest.id, name='Breakfast', is_active=True)
        self.c2 = MenuCategory(restaurant_id=self.rest.id, name='Lunch', is_active=True)
        db.session.add_all([self.c1, self.c2])
        db.session.commit()

        self.m1 = MenuItem(restaurant_id=self.rest.id, category_id=self.c1.id, name='Masala Dosa', price=120.0, is_available=True)
        self.m2 = MenuItem(restaurant_id=self.rest.id, category_id=self.c2.id, name='Special Biryani', price=250.0, is_available=True)
        db.session.add_all([self.m1, self.m2])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _login_customer(self):
        self.client.post('/auth/login', data={'email': 'customer@test.com', 'password': 'pass'})

    def test_api_slot_availability(self):
        """Verify GET /api/restaurants/<id>/slot-availability returns slots array."""
        resp = self.client.get(f'/api/restaurants/{self.rest.id}/slot-availability?date=2030-01-01&guests=2')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('slots', data)
        self.assertGreater(len(data['slots']), 0)
        self.assertTrue(data['slots'][0]['is_available'])
        self.assertGreaterEqual(data['slots'][0]['available_tables'], 1)

    def test_api_table_availability(self):
        """Verify GET /api/restaurants/<id>/table-availability returns tables list."""
        resp = self.client.get(
            f'/api/restaurants/{self.rest.id}/table-availability?date=2030-01-01&start_time=18:00&end_time=19:00&guests=2'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn('tables', data)
        self.assertEqual(len(data['tables']), 3)
        # All 3 tables are available for 2 guests
        self.assertTrue(all(t['is_available'] for t in data['tables']))

    def test_api_table_availability_guest_filtering(self):
        """Verify table availability accounts for party size (fits_capacity)."""
        resp = self.client.get(
            f'/api/restaurants/{self.rest.id}/table-availability?date=2030-01-01&start_time=18:00&end_time=19:00&guests=5'
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        # For 5 guests, t1 (cap 2) and t2 (cap 4) should NOT fit; t3 (cap 6) SHOULD fit
        t_map = {t['table_number']: t for t in data['tables']}
        self.assertFalse(t_map['T1']['fits_capacity'])
        self.assertFalse(t_map['T2']['fits_capacity'])
        self.assertTrue(t_map['T3']['fits_capacity'])

    def test_customer_dashboard_discovery_ui(self):
        """Verify customer dashboard renders discovery heading, search, and restaurant cards."""
        self._login_customer()
        resp = self.client.get('/customer/dashboard')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Discover Your Next', resp.data)
        self.assertIn(b'Spice Garden', resp.data)
        self.assertIn(b'Tiruchirappalli', resp.data)
        self.assertIn(b'Book Table', resp.data)

    def test_customer_restaurant_detail_ui(self):
        """Verify restaurant details page renders gallery, lightbox, and reservation actions."""
        self._login_customer()
        resp = self.client.get(f'/customer/restaurants/{self.rest.id}')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Spice Garden', resp.data)
        self.assertIn(b'gallery-lightbox', resp.data)
        self.assertIn(b'Reserve a Table', resp.data)
        self.assertIn(b'Masala Dosa', resp.data)
        self.assertIn(b'Special Biryani', resp.data)

    def test_interactive_reservation_form_get(self):
        """Verify multi-step reservation form renders step indicators and table cards."""
        self._login_customer()
        resp = self.client.get(f'/customer/restaurants/{self.rest.id}/reserve')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'wizard-header-steps', resp.data)
        self.assertIn(b'guest-stepper-btn', resp.data)
        self.assertIn(b'slots-grid', resp.data)
        self.assertIn(b'interactive-tables-grid', resp.data)
        self.assertIn(b'Table T1', resp.data)

    def test_interactive_reservation_booking_submission(self):
        """Verify reservation form submission creates confirmed booking and redirects."""
        self._login_customer()
        resp = self.client.post(f'/customer/restaurants/{self.rest.id}/reserve', data={
            'table_id': self.t1.id,
            'reservation_date': '2030-05-15',
            'start_time': '19:00',
            'end_time': '20:00',
            'number_of_guests': 2
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'booked successfully', resp.data)
        
        # Check DB reservation is confirmed
        res = Reservation.query.filter_by(restaurant_id=self.rest.id, table_id=self.t1.id).first()
        self.assertIsNotNone(res)
        self.assertEqual(res.status, 'confirmed')

    def test_customer_menu_ui(self):
        """Verify customer menu renders search input, category tabs, and dish cards with images."""
        self._login_customer()
        resp = self.client.get(f'/customer/restaurants/{self.rest.id}/menu')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'dish-search-input', resp.data)
        self.assertIn(b'category-pills-bar', resp.data)
        self.assertIn(b'Masala Dosa', resp.data)
        self.assertIn(b'Special Biryani', resp.data)
        self.assertIn(b'Add to Cart', resp.data)

