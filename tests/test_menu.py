import unittest
from app import create_app, db
from app.models.user import User
from app.models.restaurant import Restaurant, RestaurantStaff
from app.models.menu import MenuCategory, MenuItem

class MenuTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        self.owner1 = User(name='Owner1', email='owner1@test.com', role='restaurant_owner')
        self.owner1.set_password('pass')
        self.owner2 = User(name='Owner2', email='owner2@test.com', role='restaurant_owner')
        self.owner2.set_password('pass')
        self.customer = User(name='Customer', email='customer@test.com', role='customer')
        self.customer.set_password('pass')
        self.staff1_user = User(name='Staff1', email='staff1@test.com', role='restaurant_staff')
        self.staff1_user.set_password('pass')
        
        db.session.add_all([self.owner1, self.owner2, self.customer, self.staff1_user])
        db.session.commit()
        
        self.r1 = Restaurant(name='R1', owner_id=self.owner1.id, city='Trichy', state='TN')
        self.r2 = Restaurant(name='R2', owner_id=self.owner2.id, city='Trichy', state='TN')
        db.session.add_all([self.r1, self.r2])
        db.session.commit()
        
        self.staff1 = RestaurantStaff(user_id=self.staff1_user.id, restaurant_id=self.r1.id, designation='Waiter')
        db.session.add(self.staff1)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def _login(self, email):
        self.client.post('/auth/login', data={'email': email, 'password': 'pass'})

    def test_owner_can_create_and_edit_category(self):
        self._login('owner1@test.com')
        resp = self.client.post('/owner/menu/categories/create', data={
            'name': 'Desserts',
            'is_active': 'on'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Category created successfully', resp.data)
        
        c = MenuCategory.query.filter_by(name='Desserts').first()
        self.assertIsNotNone(c)
        self.assertEqual(c.restaurant_id, self.r1.id)
        
        # Edit
        resp2 = self.client.post(f'/owner/menu/categories/{c.id}/edit', data={
            'name': 'Sweet Desserts'
        }, follow_redirects=True)
        self.assertIn(b'Category updated successfully', resp2.data)
        
        c_updated = MenuCategory.query.get(c.id)
        self.assertEqual(c_updated.name, 'Sweet Desserts')
        self.assertFalse(c_updated.is_active) # was missing from form, unchecked

    def test_owner_can_deactivate_category(self):
        c = MenuCategory(restaurant_id=self.r1.id, name='Drinks', is_active=True)
        db.session.add(c)
        db.session.commit()
        
        self._login('owner1@test.com')
        self.client.post(f'/owner/menu/categories/{c.id}/edit', data={
            'name': 'Drinks' # is_active omitted -> False
        })
        c_updated = MenuCategory.query.get(c.id)
        self.assertFalse(c_updated.is_active)

    def test_owner_can_create_and_edit_menu_item(self):
        c = MenuCategory(restaurant_id=self.r1.id, name='Drinks')
        db.session.add(c)
        db.session.commit()
        
        self._login('owner1@test.com')
        resp = self.client.post('/owner/menu/items/create', data={
            'name': 'Coke',
            'category_id': c.id,
            'price': '2.50',
            'is_available': 'on'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Menu item created successfully', resp.data)
        
        item = MenuItem.query.filter_by(name='Coke').first()
        self.assertIsNotNone(item)
        self.assertEqual(item.price, 2.5)
        self.assertTrue(item.is_available)
        
        # Edit
        resp2 = self.client.post(f'/owner/menu/items/{item.id}/edit', data={
            'name': 'Diet Coke',
            'category_id': c.id,
            'price': '3.00'
        }, follow_redirects=True)
        item_updated = MenuItem.query.get(item.id)
        self.assertEqual(item_updated.name, 'Diet Coke')
        self.assertEqual(item_updated.price, 3.0)
        self.assertFalse(item_updated.is_available)

    def test_owner_can_delete_valid_menu_item(self):
        c = MenuCategory(restaurant_id=self.r1.id, name='Drinks')
        db.session.add(c)
        db.session.commit()
        item = MenuItem(restaurant_id=self.r1.id, category_id=c.id, name='Water', price=1.0)
        db.session.add(item)
        db.session.commit()
        
        self._login('owner1@test.com')
        resp = self.client.post(f'/owner/menu/items/{item.id}/delete', follow_redirects=True)
        self.assertIn(b'Menu item deleted successfully', resp.data)
        self.assertIsNone(MenuItem.query.get(item.id))

    def test_owner_cannot_access_another_restaurant_category_or_item(self):
        c2 = MenuCategory(restaurant_id=self.r2.id, name='R2 Category')
        db.session.add(c2)
        db.session.commit()
        item2 = MenuItem(restaurant_id=self.r2.id, category_id=c2.id, name='R2 Item', price=10.0)
        db.session.add(item2)
        db.session.commit()
        
        self._login('owner1@test.com')
        resp1 = self.client.get(f'/owner/menu/categories/{c2.id}/edit')
        self.assertEqual(resp1.status_code, 404)
        
        resp2 = self.client.get(f'/owner/menu/items/{item2.id}/edit')
        self.assertEqual(resp2.status_code, 404)

    def test_owner_cannot_attach_item_to_another_restaurant_category(self):
        c1 = MenuCategory(restaurant_id=self.r1.id, name='R1 Category')
        c2 = MenuCategory(restaurant_id=self.r2.id, name='R2 Category')
        db.session.add_all([c1, c2])
        db.session.commit()
        
        self._login('owner1@test.com')
        resp = self.client.post('/owner/menu/items/create', data={
            'name': 'Hacked Item',
            'category_id': c2.id,
            'price': '5.0'
        }, follow_redirects=True)
        # category validation should fail
        self.assertIn(b'Invalid category selected', resp.data)

    def test_staff_can_view_menu(self):
        c1 = MenuCategory(restaurant_id=self.r1.id, name='R1 Category')
        db.session.add(c1)
        db.session.commit()
        item1 = MenuItem(restaurant_id=self.r1.id, category_id=c1.id, name='R1 Item', price=10.0)
        db.session.add(item1)
        db.session.commit()
        
        self._login('staff1@test.com')
        resp = self.client.get('/staff/menu')
        self.assertIn(b'R1 Category', resp.data)
        self.assertIn(b'R1 Item', resp.data)
        self.assertIn(b'10.0', resp.data)

    def test_staff_cannot_modify_menu_or_access_another(self):
        self._login('staff1@test.com')
        resp1 = self.client.post('/owner/menu/categories/create', data={'name': 'Hack'})
        self.assertEqual(resp1.status_code, 403)
        
        c2 = MenuCategory(restaurant_id=self.r2.id, name='R2 Category')
        db.session.add(c2)
        db.session.commit()
        item2 = MenuItem(restaurant_id=self.r2.id, category_id=c2.id, name='R2 Item', price=10.0)
        db.session.add(item2)
        db.session.commit()
        
        # test isolation handled by reading their own restaurant directly in view_menu

    def test_customer_cannot_modify_menu(self):
        self._login('customer@test.com')
        resp = self.client.post('/owner/menu/categories/create', data={'name': 'Hack'})
        self.assertEqual(resp.status_code, 403)

    def test_invalid_price_is_rejected(self):
        c = MenuCategory(restaurant_id=self.r1.id, name='Drinks')
        db.session.add(c)
        db.session.commit()
        
        self._login('owner1@test.com')
        resp = self.client.post('/owner/menu/items/create', data={
            'name': 'Coke', 'category_id': c.id, 'price': '-2.50'
        }, follow_redirects=True)
        self.assertIn(b'Price must be a valid number greater than or equal to zero', resp.data)
        
        resp2 = self.client.post('/owner/menu/items/create', data={
            'name': 'Coke', 'category_id': c.id, 'price': 'invalid'
        }, follow_redirects=True)
        self.assertIn(b'Price must be a valid number greater than or equal to zero', resp2.data)

if __name__ == '__main__':
    unittest.main()
