import unittest
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant, RestaurantStaff
from app.models.table import Table
from app.models.menu import MenuCategory, MenuItem

class CustomerDiscoveryTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        self.owner = User(name='Owner', email='owner@test.com', role='restaurant_owner')
        self.owner.set_password('pass')
        self.customer = User(name='Customer', email='customer@test.com', role='customer')
        self.customer.set_password('pass')
        
        db.session.add_all([self.owner, self.customer])
        db.session.commit()
        
        self.r1 = Restaurant(name='Pizza Place', owner_id=self.owner.id, city='Trichy', state='TN', is_active=True)
        self.r2 = Restaurant(name='Burger Joint', owner_id=self.owner.id, city='Chennai', state='TN', is_active=True)
        self.r_inactive = Restaurant(name='Closed Shop', owner_id=self.owner.id, city='Trichy', state='TN', is_active=False)
        db.session.add_all([self.r1, self.r2, self.r_inactive])
        db.session.commit()
        
        self.t1 = Table(restaurant_id=self.r1.id, table_number='1', capacity=4, status='available')
        self.t2 = Table(restaurant_id=self.r1.id, table_number='2', capacity=2, status='occupied')
        db.session.add_all([self.t1, self.t2])
        db.session.commit()
        
        self.c1 = MenuCategory(restaurant_id=self.r1.id, name='Pizzas', is_active=True)
        self.c_inactive = MenuCategory(restaurant_id=self.r1.id, name='Secret Menu', is_active=False)
        db.session.add_all([self.c1, self.c_inactive])
        db.session.commit()
        
        self.m1 = MenuItem(restaurant_id=self.r1.id, category_id=self.c1.id, name='Margherita', price=10.0, is_available=True)
        self.m2 = MenuItem(restaurant_id=self.r1.id, category_id=self.c1.id, name='Pepperoni (Out)', price=12.0, is_available=False)
        db.session.add_all([self.m1, self.m2])
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _login(self, email):
        self.client.post('/auth/login', data={'email': email, 'password': 'pass'})

    def test_customer_can_view_active_restaurants(self):
        self._login('customer@test.com')
        resp = self.client.get('/customer/restaurants')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Pizza Place', resp.data)
        self.assertIn(b'Burger Joint', resp.data)
        self.assertNotIn(b'Closed Shop', resp.data) # Inactive restaurant

    def test_customer_can_search_and_filter(self):
        self._login('customer@test.com')
        resp = self.client.get('/customer/restaurants?name=Pizza')
        self.assertIn(b'Pizza Place', resp.data)
        self.assertNotIn(b'Burger Joint', resp.data)
        
        resp2 = self.client.get('/customer/restaurants?city=Chennai')
        self.assertNotIn(b'Pizza Place', resp2.data)
        self.assertIn(b'Burger Joint', resp2.data)

    def test_customer_can_view_restaurant_details(self):
        self._login('customer@test.com')
        resp = self.client.get(f'/customer/restaurants/{self.r1.id}')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Pizza Place', resp.data)

    def test_customer_can_view_available_tables_only(self):
        self._login('customer@test.com')
        resp = self.client.get(f'/customer/restaurants/{self.r1.id}/tables')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Table 1', resp.data) # available
        self.assertNotIn(b'Table 2', resp.data) # occupied

    def test_customer_can_view_available_menu_items_only(self):
        self._login('customer@test.com')
        resp = self.client.get(f'/customer/restaurants/{self.r1.id}/menu')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Pizzas', resp.data)
        self.assertIn(b'Margherita', resp.data)
        self.assertNotIn(b'Pepperoni (Out)', resp.data) # is_available = False
        # c_inactive is not tested explicitly here since relationship might load all categories, but my route filters `is_active=True`
        self.assertNotIn(b'Secret Menu', resp.data)
        self.assertIn(b'Add to Cart', resp.data)

    def test_inactive_restaurants_are_hidden(self):
        self._login('customer@test.com')
        resp = self.client.get(f'/customer/restaurants/{self.r_inactive.id}')
        self.assertEqual(resp.status_code, 404)

    def test_customer_cannot_modify_data(self):
        self._login('customer@test.com')
        resp = self.client.post('/owner/tables/create', data={})
        self.assertEqual(resp.status_code, 403)
        
        resp2 = self.client.post('/owner/menu/items/create', data={})
        self.assertEqual(resp2.status_code, 403)
        
        resp3 = self.client.post('/admin/restaurants/create', data={})
        self.assertEqual(resp3.status_code, 403)

    def test_unauthenticated_users_are_protected(self):
        resp = self.client.get('/customer/restaurants', follow_redirects=True)
        self.assertIn(b'Please log in', resp.data)

    def test_restaurants_page_does_not_render_map_while_listing_and_search_work(self):
        self._login('customer@test.com')
        resp = self.client.get('/customer/restaurants')
        self.assertEqual(resp.status_code, 200)

        # Verify Google Map container, API scripts, and initialization are completely absent
        self.assertNotIn(b'id="map"', resp.data)
        self.assertNotIn(b'maps.googleapis.com', resp.data)
        self.assertNotIn(b'initMap', resp.data)
        self.assertNotIn(b'google.maps', resp.data)

        # Verify restaurant listing and search work as expected
        self.assertIn(b'Pizza Place', resp.data)
        self.assertIn(b'Burger Joint', resp.data)
        self.assertIn(b'restaurant-list', resp.data)

        # Verify search filter continues to work
        resp_search = self.client.get('/customer/restaurants?name=Pizza')
        self.assertEqual(resp_search.status_code, 200)
        self.assertIn(b'Pizza Place', resp_search.data)
        self.assertNotIn(b'Burger Joint', resp_search.data)
        self.assertNotIn(b'id="map"', resp_search.data)

if __name__ == '__main__':
    unittest.main()
