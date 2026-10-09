import unittest
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant
from app.models.menu import MenuCategory, MenuItem

class AdminMenusTestCase(unittest.TestCase):
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

        # Create Menus
        self.cat1 = MenuCategory(restaurant_id=self.r1.id, name="Starters1")
        self.cat2 = MenuCategory(restaurant_id=self.r2.id, name="Starters2")
        db.session.add_all([self.cat1, self.cat2])
        db.session.flush()

        self.item1 = MenuItem(restaurant_id=self.r1.id, category_id=self.cat1.id, name="Soup", price=5.0)
        self.item2 = MenuItem(restaurant_id=self.r2.id, category_id=self.cat2.id, name="Salad", price=7.0)
        db.session.add_all([self.item1, self.item2])

        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def login(self, email, password):
        return self.client.post('/auth/login', data={'email': email, 'password': password}, follow_redirects=True)

    def test_super_admin_can_view_all_menus(self):
        self.login('admin@test.com', 'password')
        response = self.client.get('/admin/menus')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Starters1', response.data)
        self.assertIn(b'Starters2', response.data)
        self.assertIn(b'Soup', response.data)
        self.assertIn(b'Salad', response.data)

    def test_super_admin_can_filter_menus_by_restaurant(self):
        self.login('admin@test.com', 'password')
        response = self.client.get(f'/admin/menus?restaurant_id={self.r1.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Starters1', response.data)
        self.assertNotIn(b'Starters2', response.data)
        self.assertIn(b'Soup', response.data)
        self.assertNotIn(b'Salad', response.data)

    def test_super_admin_can_create_category(self):
        self.login('admin@test.com', 'password')
        response = self.client.post('/admin/menus/categories/create', data={
            'name': 'Mains',
            'restaurant_id': self.r1.id,
            'is_active': 'on'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        cat = MenuCategory.query.filter_by(name='Mains').first()
        self.assertIsNotNone(cat)
        self.assertEqual(cat.restaurant_id, self.r1.id)

    def test_super_admin_can_edit_menu_item(self):
        self.login('admin@test.com', 'password')
        response = self.client.post(f'/admin/menus/items/{self.item1.id}/edit', data={
            'name': 'Soup Deluxe',
            'category_id': self.cat1.id,
            'restaurant_id': self.r1.id,
            'price': '6.5',
            'is_available': 'on'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        item = MenuItem.query.get(self.item1.id)
        self.assertEqual(item.name, 'Soup Deluxe')
        self.assertEqual(item.price, 6.5)

    def test_owner_cannot_access_admin_menus(self):
        self.login('owner1@test.com', 'password')
        response = self.client.get('/admin/menus')
        self.assertEqual(response.status_code, 403)
        
        response2 = self.client.post(f'/admin/menus/items/{self.item2.id}/edit', data={
            'name': 'Hacked',
            'category_id': self.cat2.id,
            'restaurant_id': self.r2.id,
            'price': '1.0'
        })
        self.assertEqual(response2.status_code, 403)

    def test_owner_cannot_edit_other_restaurant_menus(self):
        self.login('owner1@test.com', 'password')
        # Owner trying to edit R2's item using owner route
        response = self.client.post(f'/owner/menu/items/{self.item2.id}/edit', data={
            'name': 'Hacked',
            'category_id': self.cat2.id,
            'price': '1.0'
        })
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main()
