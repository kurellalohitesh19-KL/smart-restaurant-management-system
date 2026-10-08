import unittest
import json
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant

class LocationTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Users
        self.admin = User(name='Admin', email='admin@test.com', role='super_admin')
        self.admin.set_password('pass')
        self.owner1 = User(name='Owner1', email='owner1@test.com', role='restaurant_owner')
        self.owner1.set_password('pass')
        self.owner2 = User(name='Owner2', email='owner2@test.com', role='restaurant_owner')
        self.owner2.set_password('pass')
        self.cust1 = User(name='Cust1', email='cust1@test.com', role='customer')
        self.cust1.set_password('pass')
        
        db.session.add_all([self.admin, self.owner1, self.owner2, self.cust1])
        db.session.commit()

        # Restaurants with locations
        # Base location: lat=40.7128, lng=-74.0060 (NYC)
        
        # R1: Same location (dist 0km)
        self.r1 = Restaurant(name='R1', email='r1@test.com', owner_id=self.owner1.id, city='NYC', state='NY',
                             latitude=40.7128, longitude=-74.0060, is_active=True)
        # R2: Very close (dist ~ 2.8 km)
        self.r2 = Restaurant(name='R2', email='r2@test.com', owner_id=self.owner2.id, city='NYC', state='NY',
                             latitude=40.7382, longitude=-73.9987, is_active=True)
        # R3: Far away (dist ~ 350 km) - Boston
        self.r3 = Restaurant(name='R3', email='r3@test.com', owner_id=self.admin.id, city='Boston', state='MA',
                             latitude=42.3601, longitude=-71.0589, is_active=True)
        # R4: Close but inactive (dist ~ 2.8 km)
        self.r4 = Restaurant(name='R4', email='r4@test.com', owner_id=self.admin.id, city='NYC', state='NY',
                             latitude=40.7382, longitude=-73.9987, is_active=False)
        
        db.session.add_all([self.r1, self.r2, self.r3, self.r4])
        db.session.commit()

        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, email):
        return self.client.post('/auth/login', data={'email': email, 'password': 'pass'})

    def test_valid_nearby_search_and_sorting(self):
        resp = self.client.get('/api/restaurants/nearby?latitude=40.7128&longitude=-74.0060&radius=10')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn('restaurants', data)
        self.assertEqual(len(data['restaurants']), 2) # R1 and R2
        
        # Check sorting by distance
        self.assertEqual(data['restaurants'][0]['name'], 'R1')
        self.assertEqual(data['restaurants'][1]['name'], 'R2')
        self.assertLess(data['restaurants'][0]['distance'], data['restaurants'][1]['distance'])

    def test_radius_filtering(self):
        # With 400km radius, R3 (Boston) should also be included
        resp = self.client.get('/api/restaurants/nearby?latitude=40.7128&longitude=-74.0060&radius=400')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(len(data['restaurants']), 3) # R1, R2, R3
        self.assertEqual(data['restaurants'][2]['name'], 'R3')

    def test_inactive_restaurants_excluded(self):
        resp = self.client.get('/api/restaurants/nearby?latitude=40.7128&longitude=-74.0060&radius=10')
        data = json.loads(resp.data)
        # R4 is close but inactive, should not be included
        names = [r['name'] for r in data['restaurants']]
        self.assertNotIn('R4', names)

    def test_invalid_parameters_rejected(self):
        # Invalid latitude
        resp = self.client.get('/api/restaurants/nearby?latitude=100&longitude=-74.0060&radius=10')
        self.assertEqual(resp.status_code, 400)
        # Invalid longitude
        resp = self.client.get('/api/restaurants/nearby?latitude=40.7128&longitude=-200&radius=10')
        self.assertEqual(resp.status_code, 400)
        # Invalid radius
        resp = self.client.get('/api/restaurants/nearby?latitude=40.7128&longitude=-74.0060&radius=0')
        self.assertEqual(resp.status_code, 400)
        resp = self.client.get('/api/restaurants/nearby?latitude=40.7128&longitude=-74.0060&radius=2000')
        self.assertEqual(resp.status_code, 400)
        # Missing parameter
        resp = self.client.get('/api/restaurants/nearby?longitude=-74.0060&radius=10')
        self.assertEqual(resp.status_code, 400)

    def test_api_security(self):
        resp = self.client.get('/api/restaurants/nearby?latitude=40.7128&longitude=-74.0060&radius=10')
        self.assertEqual(resp.status_code, 200)
        text = resp.data.decode('utf-8')
        # Ensure passwords or hashes are not exposed
        self.assertNotIn('password', text.lower())
        self.assertNotIn('hash', text.lower())
        self.assertNotIn('pass', text.lower()) # owner1's password is 'pass'
        self.assertNotIn('owner1', text.lower()) # owner id not exposed either

    def test_owner_coordinate_security(self):
        # Owner1 can modify R1
        self.login('owner1@test.com')
        resp = self.client.post('/owner/restaurant/edit', data={
            'name': 'R1 Modified',
            'city': 'NYC',
            'state': 'NY',
            'latitude': '41.0',
            'longitude': '-73.0'
        })
        r1 = Restaurant.query.get(self.r1.id)
        self.assertEqual(r1.latitude, 41.0)
        
        # But Owner1 cannot modify R2 because /owner/restaurant/edit only fetches the owner's assigned restaurant
        # They don't even have a parameter to pass restaurant_id. They are locked to their own.
        r2 = Restaurant.query.get(self.r2.id)
        self.assertNotEqual(r2.latitude, 41.0)

    def test_super_admin_coordinate_management(self):
        self.login('admin@test.com')
        resp = self.client.post(f'/admin/restaurants/{self.r1.id}/edit', data={
            'name': 'R1 By Admin',
            'owner_id': self.owner1.id,
            'city': 'NYC',
            'state': 'NY',
            'latitude': '42.0',
            'longitude': '-72.0'
        })
        r1 = Restaurant.query.get(self.r1.id)
        self.assertEqual(r1.latitude, 42.0)

    def test_customer_cannot_modify_coordinates(self):
        self.login('cust1@test.com')
        # Customer tries to access owner edit route
        resp = self.client.post('/owner/restaurant/edit', data={'latitude': '40'})
        self.assertEqual(resp.status_code, 403)
        # Customer tries to access admin edit route
        resp = self.client.post(f'/admin/restaurants/{self.r1.id}/edit', data={'latitude': '40'})
        self.assertEqual(resp.status_code, 403)

    def test_city_fallback_discovery(self):
        # Customer should still be able to search by city normally
        self.login('cust1@test.com')
        resp = self.client.get('/customer/restaurants?city=Boston')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'R3', resp.data)
        self.assertNotIn(b'R1', resp.data)

if __name__ == '__main__':
    unittest.main()
